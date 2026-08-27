"""Regression tests for the feature-003 preflight gate."""

from __future__ import annotations

import importlib.util
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "verify_preflight.py"
SPEC = importlib.util.spec_from_file_location("verify_feature003_preflight", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_preflight_rederives_exact_prerequisites_from_head() -> None:
    result = MODULE.verify("HEAD")

    assert result["status"] == "PASS"
    assert result["formal"]["artifact_count"] == 24
    assert result["formal"]["formal_semantics_id"] == MODULE.EXPECTED_FORMAL_ID
    assert result["feature002"]["merged_tree"] == MODULE.EXPECTED_FEATURE002_TREE
    assert result["architecture"]["findings"] == []


def test_legacy_implementation_patterns_cover_detached_plan() -> None:
    forbidden_examples = {
        "LEGACY_PYTHON_PACKAGE_PATH": "src/deltatorrent/consensus/transition.py",
        "LEGACY_PYTHON_REFERENCE_RUNTIME": "Python 3.12 reference implementation",
        "PRODUCTION_QUANTIZER_PATH": "fixedpoint/quantize.py",
        "PROTOBUF_IMPLEMENTATION_PATH": "proto/deltareduce/consensus.proto",
        "GRPC_IMPLEMENTATION_PATH": "adapters/grpc/consensus_server.py",
    }

    for identifier, example in forbidden_examples.items():
        assert MODULE.LEGACY_IMPLEMENTATION_PATTERNS[identifier].search(example)
