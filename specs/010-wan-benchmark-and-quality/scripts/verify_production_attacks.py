"""Execute and attest the mandatory attack corpus at native production boundaries."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "delta-worker-python/src"))

from deltatorrent.benchmark.attacks import production_rejection_corpus  # noqa: E402
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID  # noqa: E402

OUTPUT: Final = ROOT / "specs/010-wan-benchmark-and-quality/evidence/production-attacks.json"
TARGET: Final = "delta_certificates_test"
FILES: Final = (
    "CMakeLists.txt",
    "delta-core-cpp/include/delta/certificates/contracts.hpp",
    "delta-core-cpp/include/delta/certificates/verifier.hpp",
    "delta-core-cpp/include/delta/distribution/certification_policy.hpp",
    "delta-core-cpp/src/certificates/contracts.cpp",
    "delta-core-cpp/src/certificates/verifier.cpp",
    "delta-core-cpp/src/distribution/certification_policy.cpp",
    "delta-core-cpp/src/robust/plan.cpp",
    "delta-core-cpp/tests/certificates_test.cpp",
    "delta-runtime-cpp/src/certificate_runtime.cpp",
    "delta-runtime-cpp/src/runtime.cpp",
    "delta-runtime-cpp/src/wal.cpp",
    "delta-worker-python/src/deltatorrent/benchmark/attacks.py",
    "delta-worker-python/src/deltatorrent/benchmark/safety.py",
    "specs/010-wan-benchmark-and-quality/scripts/verify_production_attacks.py",
)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def execute(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )


def run(*args: str) -> str:
    return execute(*args).stdout.strip()


def source_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path}"), cwd=ROOT, check=True, capture_output=True
    ).stdout


def executable(preset: str) -> Path:
    suffix = ".exe" if os.name == "nt" else ""
    candidates = sorted((ROOT / "out/build" / preset).rglob(TARGET + suffix))
    require(len(candidates) == 1, f"ATTACK_BINARY_COUNT:{preset}:{len(candidates)}")
    return candidates[0]


def execute_native(preset: str) -> tuple[dict[str, object], dict[str, object]]:
    run("cmake", "--preset", preset)
    run("cmake", "--build", "--preset", preset, "--target", TARGET, "--parallel", "4")
    with tempfile.TemporaryDirectory(prefix=f"delta-attacks-010-{preset}-") as directory:
        report_path = Path(directory) / "production-attacks.json"
        run(str(executable(preset)), "--attack-report", str(report_path))
        raw = report_path.read_bytes()
    document = json.loads(raw)
    require(isinstance(document, dict), f"ATTACK_REPORT_NOT_OBJECT:{preset}")
    outcomes = production_rejection_corpus(document)
    require(
        all(
            item.rejected
            and item.current_unchanged
            and item.actual_outcome == item.expected_outcome
            for item in outcomes
        ),
        f"ATTACK_OUTCOME_FAILED:{preset}",
    )
    return document, {
        "attack_count": len(outcomes),
        "preset": preset,
        "report_sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
        "status": "PASS",
    }


def capture_environment() -> dict[str, str]:
    return {
        "cmake": run("cmake", "--version").splitlines()[0],
        "host": platform.platform(),
        "python": platform.python_version(),
    }


def validate_environment(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        raise RuntimeError("ATTACK_ENVIRONMENT_MISSING")
    require(set(value) == {"cmake", "host", "python"}, "ATTACK_ENVIRONMENT_FIELDS")
    require(all(isinstance(item, str) and item for item in value.values()), "ATTACK_ENVIRONMENT")
    return {str(key): str(item) for key, item in value.items()}


def build(commit: str, environment: dict[str, str] | None = None) -> dict[str, object]:
    require(re.fullmatch(r"[0-9a-f]{40}", commit) is not None, "SOURCE_COMMIT_INVALID")
    formal_diff = run(
        "git",
        "diff",
        "--name-only",
        "origin/main..." + commit,
        "--",
        "formal",
        "specs/000-formal-tla-spec",
    ).splitlines()
    require(not formal_diff, "FORMAL_SOURCE_DIFF")
    reports: list[dict[str, object]] = []
    runs: list[dict[str, object]] = []
    for preset in ("cpp20", "cpp23"):
        report, result = execute_native(preset)
        reports.append(report)
        runs.append(result)
    require(reports[0] == reports[1], "CXX20_CXX23_ATTACK_REPORT_MISMATCH")
    return {
        "attack_report": reports[0],
        "checks": [
            "CXX20_AND_CXX23_PRODUCTION_BOUNDARIES_EXECUTED",
            "CONFLICTING_CONFIG_COMMITMENT_AND_VOTE_REJECTED",
            "SEED_AC_EPOCH_AND_AGGREGATE_ATTACKS_REJECTED",
            "UNSAFE_ACCUMULATOR_REJECTED",
            "APPLY_CURRENT_AND_DISTRIBUTION_DOWNGRADES_REJECTED",
            "CURRENT_POINTER_UNCHANGED_FOR_ALL_ATTACKS",
            "NO_FORMAL_SOURCE_DIFF",
        ],
        "classification": "REGRESSION_ONLY",
        "environment": environment if environment is not None else capture_environment(),
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "native_runs": runs,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": [
                {"path": path, "sha256": hashlib.sha256(source_bytes(commit, path)).hexdigest()}
                for path in FILES
            ],
            "commit": commit,
            "tree": run("git", "show", "-s", "--format=%T", commit),
        },
        "status": "PASS",
        "task_ids": ["T021", "T030", "T031", "T032", "T033"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    arguments = parser.parse_args()
    if arguments.check_only:
        recorded = json.loads(OUTPUT.read_text(encoding="utf-8"))
        environment = validate_environment(recorded.get("environment"))
        expected = build(str(recorded["source"]["commit"]), environment)
        require(recorded == expected, "PRODUCTION_ATTACK_EVIDENCE_MISMATCH")
        report = recorded
    else:
        require(not run("git", "status", "--porcelain"), "SOURCE_TREE_NOT_CLEAN")
        report = build(run("git", "rev-parse", "HEAD"))
        OUTPUT.write_text(
            json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
