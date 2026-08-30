from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/010-wan-benchmark-and-quality/scripts/verify_runtime_adapters.py"


def load_script() -> ModuleType:
    specification = importlib.util.spec_from_file_location("verify_runtime_adapters", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_golden_aggregate_is_exact_and_complete() -> None:
    count, aggregate = load_script().golden_hash_aggregate()
    assert count == 18
    assert aggregate == "sha256:34caa122b80bc044baaaed7a90b8b68ef82f379ccbabbee193a825044948302f"


def test_recorded_environment_is_fail_closed() -> None:
    module = load_script()
    valid = {"cmake": "c", "host": "h", "java_compiler": "j", "python": "p"}
    assert module.validate_recorded_environment(valid) == valid
    try:
        module.validate_recorded_environment({"host": "h"})
        raise AssertionError("incomplete environment accepted")
    except RuntimeError as error:
        assert str(error) == "RECORDED_ENVIRONMENT_FIELDS"
