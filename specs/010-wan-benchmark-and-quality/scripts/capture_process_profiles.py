"""Build immutable process-profile evidence from exact GitHub Actions artifacts."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "delta-worker-python/src"))

from deltatorrent.benchmark.process_profiles import analyze_process_profiles  # noqa: E402
from deltatorrent.protocol.canonical import canonical_json_bytes  # noqa: E402

DEFAULT_OUTPUT: Final = ROOT / "specs/010-wan-benchmark-and-quality/evidence/process-profiles.json"


def build_evidence(
    *,
    jdk25: bytes,
    jdk26: bytes,
    source_commit: str,
    execution_commit: str,
    workflow_run_id: int,
    jdk25_job_id: int,
    jdk26_job_id: int,
    jdk25_artifact_id: int,
    jdk26_artifact_id: int,
) -> dict[str, object]:
    if (
        re.fullmatch(r"[0-9a-f]{40}", source_commit) is None
        or re.fullmatch(r"[0-9a-f]{40}", execution_commit) is None
        or workflow_run_id <= 0
        or jdk25_job_id <= 0
        or jdk26_job_id <= 0
        or jdk25_job_id == jdk26_job_id
        or jdk25_artifact_id <= 0
        or jdk26_artifact_id <= 0
        or jdk25_artifact_id == jdk26_artifact_id
    ):
        raise RuntimeError("PROCESS_PROFILE_GITHUB_IDENTITY_INVALID")
    evidence = analyze_process_profiles(
        {25: jdk25, 26: jdk26}, source_commit=source_commit, repetitions=5
    )
    evidence["github"] = {
        "execution_commit": execution_commit,
        "head_source_commit": source_commit,
        "jobs": [
            {
                "artifact_name": f"benchmark-process-profile-jdk25-{execution_commit}",
                "artifact_id": jdk25_artifact_id,
                "jdk_feature": 25,
                "job_id": jdk25_job_id,
            },
            {
                "artifact_name": f"benchmark-process-profile-jdk26-{execution_commit}",
                "artifact_id": jdk26_artifact_id,
                "jdk_feature": 26,
                "job_id": jdk26_job_id,
            },
        ],
        "workflow": "Feature 010 benchmark runtime qualification",
        "workflow_run_id": workflow_run_id,
    }
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jdk25", type=Path, required=True)
    parser.add_argument("--jdk26", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--execution-commit", required=True)
    parser.add_argument("--workflow-run-id", required=True, type=int)
    parser.add_argument("--jdk25-job-id", required=True, type=int)
    parser.add_argument("--jdk26-job-id", required=True, type=int)
    parser.add_argument("--jdk25-artifact-id", required=True, type=int)
    parser.add_argument("--jdk26-artifact-id", required=True, type=int)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    evidence = build_evidence(
        jdk25=arguments.jdk25.read_bytes(),
        jdk26=arguments.jdk26.read_bytes(),
        source_commit=arguments.source_commit,
        execution_commit=arguments.execution_commit,
        workflow_run_id=arguments.workflow_run_id,
        jdk25_job_id=arguments.jdk25_job_id,
        jdk26_job_id=arguments.jdk26_job_id,
        jdk25_artifact_id=arguments.jdk25_artifact_id,
        jdk26_artifact_id=arguments.jdk26_artifact_id,
    )
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_bytes(canonical_json_bytes(evidence))
    print(
        json.dumps(
            {
                "output": str(arguments.output),
                "selected_profile": evidence["selected_profile"],
                "source_commit": evidence["source_commit"],
                "status": evidence["status"],
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
