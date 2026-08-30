from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/010-wan-benchmark-and-quality/scripts/verify_architecture_guard.py"
SPEC = importlib.util.spec_from_file_location("verify_architecture_guard", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_path_boundary_allows_benchmark_and_rejects_protocol_authority() -> None:
    assert MODULE.allowed_path("delta-runtime-cpp/src/benchmark/metrics.cpp")
    assert MODULE.allowed_path("delta-protocol/schemas/010/run-manifest-v1.json")
    assert not MODULE.allowed_path("delta-runtime-cpp/src/runtime.cpp")
    assert not MODULE.allowed_path("formal/tla/DeltaReduce.tla")


def test_text_guard_rejects_semantic_waivers() -> None:
    assert MODULE.scan_text("manual GO override") == ("MANUAL_GO_OVERRIDE",)
    assert MODULE.scan_text('"protocol_current_transition": true') == ("PROTOCOL_CURRENT_TRUE",)
    assert MODULE.scan_text("ordinary benchmark accounting") == ()


def test_registry_projection_ignores_only_feature_010_extensions() -> None:
    registry = {
        "action_registry": {"sha256": "same"},
        "fixtures": [
            {"id": "OLD", "path": "fixtures/009/x.json"},
            {"id": "BENCHMARK010-X", "path": "fixtures/010/x.json"},
        ],
        "formal_semantics_id": MODULE.FORMAL_ID,
        "media_types": [
            {"id": "MEDIA-OLD", "path": "schemas/009/x.json"},
            {"id": "MEDIA-BENCHMARK-X", "path": "schemas/010/x.json"},
        ],
        "schemas": [
            {"id": "OLD", "path": "schemas/009/x.json"},
            {"id": "NEW", "path": "schemas/010/x.json"},
        ],
    }

    projected = MODULE.registry_projection(registry)

    assert projected["fixtures"] == [{"id": "OLD", "path": "fixtures/009/x.json"}]
    assert projected["schemas"] == [{"id": "OLD", "path": "schemas/009/x.json"}]
