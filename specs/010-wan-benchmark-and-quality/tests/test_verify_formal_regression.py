from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).parents[3]
SCRIPT = ROOT / "specs/010-wan-benchmark-and-quality/scripts/verify_formal_regression.py"


def load_script() -> ModuleType:
    specification = importlib.util.spec_from_file_location("verify_formal_regression", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def model(config_id: str, kind: str) -> dict[str, object]:
    return {
        "config_id": config_id,
        "depth": 1,
        "distinct_states": 1,
        "generated_states": 1,
        "kind": kind,
        "log_sha256": "sha256:" + "0" * 64,
        "status": "PASS",
    }


def execution() -> dict[str, object]:
    return {
        "models": [
            *[model(f"safety-{index}", "safety") for index in range(19)],
            *[model(f"liveness-{index}", "liveness") for index in range(6)],
        ],
        "status": "PASS",
    }


def test_recorded_execution_requires_all_model_families() -> None:
    module = load_script()

    assert module.validate_recorded_execution(execution())["status"] == "PASS"
    invalid = execution()
    models = invalid["models"]
    assert isinstance(models, list)
    models.pop()
    with pytest.raises(RuntimeError, match="FORMAL_EXECUTION_MODELS"):
        module.validate_recorded_execution(invalid)


def test_formal_source_and_semantic_identity_are_frozen() -> None:
    module = load_script()

    assert module.FORMAL_SOURCE == "1e6e0f6f70056161d95933e71494ec390c7c1151"
    assert module.FORMAL_GO == "7abd0f43f8f1b15ec9aa6c3d2c80b32bfb4a6eca"
    assert module.FORMAL_ID == (
        "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
    )
