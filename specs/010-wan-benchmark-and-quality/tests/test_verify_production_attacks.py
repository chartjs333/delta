from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).parents[3]
SCRIPT = ROOT / "specs/010-wan-benchmark-and-quality/scripts/verify_production_attacks.py"


def load_script() -> ModuleType:
    specification = importlib.util.spec_from_file_location("verify_production_attacks", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_recorded_attack_environment_is_fail_closed() -> None:
    module = load_script()
    valid = {"cmake": "c", "host": "h", "python": "p"}

    assert module.validate_environment(valid) == valid
    with pytest.raises(RuntimeError, match="ATTACK_ENVIRONMENT_FIELDS"):
        module.validate_environment({"host": "h"})


def test_attack_source_set_binds_production_boundaries() -> None:
    module = load_script()

    assert "delta-core-cpp/src/certificates/verifier.cpp" in module.FILES
    assert "delta-runtime-cpp/src/certificate_runtime.cpp" in module.FILES
    assert "delta-core-cpp/src/distribution/certification_policy.cpp" in module.FILES
    assert "delta-core-cpp/tests/certificates_test.cpp" in module.FILES
