"""Generate exact-source evidence for the feature-009 Python runtime layer."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
OUTPUT: Final = ROOT / "specs/009-qlora-8gb-mode/evidence/python-runtime.json"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
FILES: Final = (
    "delta-worker-python/src/deltatorrent/qlora/adapter_schema.py",
    "delta-worker-python/src/deltatorrent/qlora/backend.py",
    "delta-worker-python/src/deltatorrent/qlora/contribution.py",
    "delta-worker-python/src/deltatorrent/qlora/model_loader.py",
    "delta-worker-python/src/deltatorrent/qlora/preflight.py",
    "delta-worker-python/src/deltatorrent/qlora/trainer.py",
    "delta-worker-python/tests/qlora/test_backend_schema.py",
    "delta-worker-python/tests/qlora/test_fixed_ticket.py",
    "delta-worker-python/tests/qlora/test_preflight.py",
    "specs/009-qlora-8gb-mode/scripts/verify_python_runtime.py",
)


def run(*args: str) -> str:
    result = subprocess.run(
        args, cwd=ROOT, check=True, capture_output=True, encoding="utf-8", errors="replace"
    )
    return result.stdout.strip()


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def source_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path}"), cwd=ROOT, check=True, capture_output=True
    ).stdout


def build(commit: str) -> dict[str, object]:
    artifacts = [{"path": path, "sha256": sha256(source_bytes(commit, path))} for path in FILES]
    formal_diff = run(
        "git",
        "diff",
        "--name-only",
        "origin/main..." + commit,
        "--",
        "formal",
        "specs/000-formal-tla-spec",
    ).splitlines()
    if formal_diff:
        raise RuntimeError("FORMAL_SOURCE_DIFF")
    pytest_result = subprocess.run(
        (sys.executable, "-m", "pytest", "delta-worker-python/tests/qlora", "-q"),
        cwd=ROOT,
        check=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    summary = next(
        line for line in reversed(pytest_result.stdout.splitlines()) if "passed" in line
    )
    return {
        "checks": [
            "BACKEND_NEUTRAL_LOADER_AND_PINNED_PRODUCTION_ADAPTER",
            "EXACT_ORDERED_ADAPTER_SCHEMA",
            "LOGICAL_BASE_AND_PROTOCOL_BUFFERS_IMMUTABLE",
            "ADAPTER_ONLY_OPTIMIZER_GRADIENT_AND_PAYLOAD",
            "EXACT_COMPATIBILITY_AND_HARD_MEMORY_BUDGET",
            "FEATURE007_FIXED_TICKET_B_H_PRESERVED",
            "A_J_EQUALS_H_BEFORE_COMMITMENT",
            "FEATURE004_CANONICAL_INT16_ADAPTER_SHARDS",
            "TERMINAL_FAILURES_PUBLISH_NOTHING",
            "NO_FORMAL_SOURCE_DIFF",
        ],
        "classification": "REFINEMENT_ONLY",
        "formal_semantics_id": FORMAL_ID,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": artifacts,
            "commit": commit,
            "tree": run("git", "show", "-s", "--format=%T", commit),
        },
        "status": "PASS",
        "task_ids": [
            *[f"T{index:03d}" for index in range(6, 21)],
            "HR009-002",
            "HR009-003",
            "HR009-004",
        ],
        "tests": {
            "command": "python -m pytest delta-worker-python/tests/qlora -q",
            "summary": summary,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()
    if args.check_only:
        report = json.loads(OUTPUT.read_text(encoding="utf-8"))
        expected = build(str(report["source"]["commit"]))
        if report != expected:
            raise RuntimeError("PYTHON_RUNTIME_EVIDENCE_MISMATCH")
    else:
        if run("git", "status", "--porcelain"):
            raise RuntimeError("SOURCE_TREE_NOT_CLEAN")
        report = build(run("git", "rev-parse", "HEAD"))
        OUTPUT.write_text(
            json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
