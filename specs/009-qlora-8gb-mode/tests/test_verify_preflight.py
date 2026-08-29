from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs" / "009-qlora-8gb-mode" / "scripts" / "verify_preflight.py"
PROFILE = ROOT / "configs" / "qlora" / "8gb-reference.json"

SPEC = importlib.util.spec_from_file_location("feature009_preflight", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def profile() -> dict[str, Any]:
    document = json.loads(PROFILE.read_text(encoding="utf-8"))
    assert isinstance(document, dict)
    return document


def test_frozen_physical_profile_is_exact() -> None:
    result = MODULE.validate_profile(profile())

    assert result["status"] == "IDENTIFIED_PROFILE_FROZEN"
    assert result["gpu_total_memory_bytes"] == 8 * 1024**3
    assert result["ordered_target_module_count"] == 128
    assert result["claim_status"] == "PENDING_EXECUTION"


@pytest.mark.parametrize(
    ("path", "value", "code"),
    [
        (("runner", "gpu", "uuid"), "GPU-wrong", "GPU_UUID_DRIFT"),
        (("model", "access_token_required"), True, "MODEL_TOKEN_FORBIDDEN"),
        (("memory", "offload_policy"), "CPU", "OFFLOAD_POLICY_INVALID"),
        (("adapter", "rank"), 16, "ADAPTER_RANK_DRIFT"),
        (("ticket", "B"), 1024, "TICKET_B_H_MISMATCH"),
    ],
)
def test_profile_mutations_fail_closed(
    path: tuple[str, ...],
    value: object,
    code: str,
) -> None:
    document = copy.deepcopy(profile())
    cursor: dict[str, Any] = document
    for key in path[:-1]:
        nested = cursor[key]
        assert isinstance(nested, dict)
        cursor = nested
    cursor[path[-1]] = value

    with pytest.raises(MODULE.PreflightError, match=code):
        MODULE.validate_profile(document)


def test_target_order_and_explicitness_are_closed() -> None:
    document = copy.deepcopy(profile())
    targets = document["adapter"]["ordered_target_modules"]
    targets[0], targets[1] = targets[1], targets[0]

    with pytest.raises(MODULE.PreflightError, match="ADAPTER_TARGET_SET_DRIFT"):
        MODULE.validate_profile(document)


def test_exact_feature008_chain_is_still_valid() -> None:
    result = MODULE.verify_feature008("HEAD")

    assert result["status"] == "PASS"
    assert result["merge_commit"] == MODULE.FEATURE008_MERGE
    assert result["source_commit"] == MODULE.FEATURE008_SOURCE
