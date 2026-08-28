from __future__ import annotations

import sys
from pathlib import Path

FEATURE = Path(__file__).resolve().parents[1]
SCRIPTS = FEATURE / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from generate_refinement_traces import TRACE_DIR, canonical_json_bytes, traces  # noqa: E402
from verify_distribution_refinement import verify  # noqa: E402


def test_traces_are_deterministic_and_refine_expected_outcomes() -> None:
    for relative, expected in traces().items():
        assert (TRACE_DIR / relative).read_bytes().replace(b"\r\n", b"\n") == (
            canonical_json_bytes(expected) + b"\n"
        )
    result = verify()
    assert result["status"] == "PASS"
    assert len(result["legal_traces"]) == 3
    assert len(result["illegal_traces"]) == 2
    assert result["semantic_completeness_claimed"] is False
