from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "specs/010-wan-benchmark-and-quality/scripts/capture_process_profiles.py"


def load_script() -> ModuleType:
    specification = importlib.util.spec_from_file_location("capture_process_profiles", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def raw_profile() -> bytes:
    lines = []
    for repetition in range(5):
        lines.extend(
            (
                f"PROCESS_PROFILE EMBEDDED_FFM 19 19 {10 + repetition} {11 + repetition} 0",
                f"PROCESS_PROFILE ISOLATED_SIDECAR 16 16 {100 + repetition} "
                f"{110 + repetition} {500 + repetition}",
            )
        )
    return ("\n".join(lines) + "\n").encode()


def test_process_profile_evidence_binds_exact_github_jobs() -> None:
    evidence = load_script().build_evidence(
        jdk25=raw_profile(),
        jdk26=raw_profile(),
        source_commit="a" * 40,
        workflow_run_id=11,
        jdk25_job_id=12,
        jdk26_job_id=13,
    )

    assert evidence["selected_profile"] == "ISOLATED_SIDECAR"
    assert evidence["github"]["workflow_run_id"] == 11
    assert [item["jdk_feature"] for item in evidence["github"]["jobs"]] == [25, 26]


def test_process_profile_evidence_rejects_ambiguous_job_identity() -> None:
    with pytest.raises(RuntimeError, match="PROCESS_PROFILE_GITHUB_IDENTITY_INVALID"):
        load_script().build_evidence(
            jdk25=raw_profile(),
            jdk26=raw_profile(),
            source_commit="a" * 40,
            workflow_run_id=11,
            jdk25_job_id=12,
            jdk26_job_id=12,
        )
