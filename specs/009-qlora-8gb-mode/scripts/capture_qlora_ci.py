"""Capture successful exact-source CI for feature 009."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
OUTPUT: Final = ROOT / "specs/009-qlora-8gb-mode/evidence/qlora-ci.json"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
REQUIRED_WORKFLOWS: Final = {
    "Feature 009 certified QLoRA verification": {
        "Native C++20 QLoRA authority",
        "Native C++23 QLoRA authority",
        "Clang ASan UBSan QLoRA boundary",
        "Java 25 base-cache and adapter transport",
        "Java 26 base-cache and adapter transport",
        "QLoRA native and transport boundary gate",
    },
    "Python worker quality": {"python-foundation"},
}
WORKFLOW_PATHS: Final = (
    ".github/workflows/ci.yml",
    ".github/workflows/qlora.yml",
)


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def run_json(*args: str) -> Any:
    process = subprocess.run(["gh", *args], cwd=ROOT, capture_output=True, text=True)
    require(process.returncode == 0, f"GH_COMMAND_FAILED:{process.stderr.strip()}")
    return json.loads(process.stdout)


def git_text(*args: str) -> str:
    process = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    require(process.returncode == 0, f"GIT_COMMAND_FAILED:{process.stderr.strip()}")
    return process.stdout.strip()


def git_bytes(*args: str) -> bytes:
    process = subprocess.run(["git", *args], cwd=ROOT, capture_output=True)
    require(
        process.returncode == 0,
        f"GIT_COMMAND_FAILED:{process.stderr.decode(errors='replace').strip()}",
    )
    return process.stdout.replace(b"\r\n", b"\n")


def workflow_hashes(commit: str) -> list[dict[str, str]]:
    return [
        {
            "path": path,
            "sha256": hashlib.sha256(git_bytes("show", f"{commit}:{path}")).hexdigest(),
        }
        for path in WORKFLOW_PATHS
    ]


def capture(source_commit: str) -> dict[str, object]:
    commit = git_text("rev-parse", source_commit)
    runs = run_json(
        "run",
        "list",
        "--commit",
        commit,
        "--limit",
        "50",
        "--json",
        "databaseId,conclusion,event,headSha,status,url,workflowName",
    )
    selected: dict[str, dict[str, object]] = {}
    for run in sorted(runs, key=lambda item: int(item["databaseId"]), reverse=True):
        workflow = str(run.get("workflowName"))
        if (
            workflow not in REQUIRED_WORKFLOWS
            or workflow in selected
            or run.get("headSha") != commit
            or run.get("status") != "completed"
            or run.get("conclusion") != "success"
        ):
            continue
        details = run_json("run", "view", str(run["databaseId"]), "--json", "jobs,url")
        jobs = [
            {
                "conclusion": job.get("conclusion"),
                "name": job.get("name"),
                "url": job.get("url"),
            }
            for job in details.get("jobs", [])
        ]
        conclusions = {str(job["name"]): str(job["conclusion"]) for job in jobs}
        required = REQUIRED_WORKFLOWS[workflow]
        if not all(conclusions.get(name) == "success" for name in required):
            continue
        selected[workflow] = {
            "database_id": run["databaseId"],
            "event": run["event"],
            "head_sha": commit,
            "jobs": sorted(jobs, key=lambda item: str(item["name"])),
            "url": details["url"],
            "workflow_name": workflow,
        }
    missing = sorted(set(REQUIRED_WORKFLOWS) - set(selected))
    require(not missing, "SUCCESSFUL_SOURCE_WORKFLOWS_MISSING:" + ",".join(missing))
    return {
        "checks": [
            "STRICT_CPP20_CPP23_QLORA_PASS",
            "CLANG_ASAN_UBSAN_QLORA_PASS",
            "PINNED_JDK25_JDK26_TRANSPORT_PASS",
            "PHYSICAL_EVIDENCE_BOUNDARY_GATE_PASS",
            "PYTHON_RUFF_FORMAT_MYPY_TESTS_PASS",
        ],
        "formal_semantics_id": FORMAL_ID,
        "runs": {key: selected[key] for key in sorted(selected)},
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "commit": commit,
            "tree": git_text("rev-parse", f"{commit}^{{tree}}"),
        },
        "status": "PASS",
        "workflows": workflow_hashes(commit),
    }


def verify() -> dict[str, Any]:
    raw = OUTPUT.read_bytes()
    evidence = json.loads(raw)
    require(isinstance(evidence, dict), "CI_EVIDENCE_NOT_OBJECT")
    require(
        raw
        == json.dumps(evidence, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(),
        "CI_EVIDENCE_NOT_CANONICAL",
    )
    source = evidence.get("source")
    require(isinstance(source, dict), "CI_SOURCE_MISSING")
    expected = capture(str(source.get("commit")))
    require(evidence == expected, "CI_EVIDENCE_MISMATCH")
    return evidence


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    arguments = parser.parse_args()
    if arguments.write:
        require(arguments.source_commit is not None, "SOURCE_COMMIT_REQUIRED")
        report = capture(arguments.source_commit)
        OUTPUT.write_bytes(
            json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        )
    else:
        require(arguments.check_only, "CHECK_ONLY_REQUIRED")
        report = verify()
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
