"""Cross-language canonical protocol fixture regression tests."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_protocol_contracts.py"
SPEC = importlib.util.spec_from_file_location("verify_feature003_protocol", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_all_registered_types_have_exact_roundtrip_vectors() -> None:
    golden = MODULE.golden_document(None)

    assert len(golden["vectors"]) == 10
    assert [item["type_code"] for item in golden["vectors"]] == list(range(1, 11))
    assert golden["vectors"][0]["content_id"] == (
        "sha256:20a8dfa998f1681faa180ecf2d81aadf29c9503bf4129a45263779d37da245f0"
    )
    assert golden["vectors"][-1]["content_id"] == (
        "sha256:df81464647a0cc9fcfdca29c5a989ffd3adb29b81755296507faa17907052725"
    )


def test_negative_corpus_is_rejected_with_exact_codes() -> None:
    assert MODULE.verify_negative(None) == 9


def test_float_and_malformed_envelope_fail_closed() -> None:
    with pytest.raises(MODULE.ContractError, match=r"^FLOAT_NOT_ALLOWED$"):
        MODULE.encode_value(0.5)

    malformed = bytes.fromhex("44524331010000010000000f310000000121000000017a0200")
    with pytest.raises(MODULE.ContractError):
        MODULE.decode_envelope(malformed)


def test_root_registry_binds_every_feature003_contract() -> None:
    result = MODULE.verify_registry(None)

    assert result["artifact_count"] == 3
    assert result["registered_feature003_ids"] == 7
    assert result["registry_version"] == "003.1.0"
