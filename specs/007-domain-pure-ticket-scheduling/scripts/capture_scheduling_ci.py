"""Capture the successful feature-007 exact-source GitHub Actions matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Final, NoReturn

ROOT: Final = Path(__file__).resolve().parents[3]
OUTPUT: Final = (
    ROOT / "specs" / "007-domain-pure-ticket-scheduling" / "evidence" / "scheduling-ci.json"
)
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
REQUIRED_WORKFLOWS: Final = {
    "Feature 007 scheduling verification": {
        "Clang ASan UBSan scheduling planner",
        "JDK 25 scheduling FFM adapter",
        "JDK 26 scheduling FFM adapter",
        "Native C++20 scheduling planner",
        "Native C++23 scheduling planner",
        "Scheduling ABI and Java boundary evidence",
    },
    "Python worker quality": {"python-foundation"},
}
WORKFLOW_PATHS: Final = {
    "Feature 007 scheduling verification": ".github/workflows/scheduling.yml",
    "Python worker quality": ".github/workflows/ci.yml",
}


class CaptureError(RuntimeError):
    """Stable fail-closed exact-source CI capture error."""


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise CaptureError(f"{code}:{detail}" if detail else code)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def run_json(*arguments: str) -> Any:
    process = subprocess.run(
        ["gh", *arguments], cwd=ROOT, check=False, capture_output=True, text=True
    )
    require(process.returncode == 0, "GH_COMMAND_FAILED", process.stderr.strip())
    return json.loads(process.stdout)


def git_text(*arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments], cwd=ROOT, check=False, capture_output=True, text=True
    )
    require(process.returncode == 0, "GIT_COMMAND_FAILED", process.stderr.strip())
    return process.stdout.strip()


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    require(
        process.returncode == 0,
        "GIT_COMMAND_FAILED",
        process.stderr.decode(errors="replace").strip(),
    )
    return process.stdout.replace(b"\r\n", b"\n")


def workflow_hashes(commit: str) -> list[dict[str, str]]:
    return [
        {
            "path": path,
            "sha256": hashlib.sha256(git_bytes("show", f"{commit}:{path}")).hexdigest(),
        }
        for path in sorted(WORKFLOW_PATHS.values())
    ]


def capture(source_commit: str) -> dict[str, Any]:
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
    selected: dict[str, dict[str, Any]] = {}
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
        details = run_json("run", "view", str(run["databaseId"]), "--json", "conclusion,jobs,url")
        jobs = [
            {
                "conclusion": job.get("conclusion"),
                "name": job.get("name"),
                "url": job.get("url"),
            }
            for job in details.get("jobs", [])
        ]
        conclusions = {str(job["name"]): str(job["conclusion"]) for job in jobs}
        if not all(conclusions.get(name) == "success" for name in REQUIRED_WORKFLOWS[workflow]):
            continue
        selected[workflow] = {
            "database_id": run["databaseId"],
            "event": run["event"],
            "head_sha": run["headSha"],
            "jobs": sorted(jobs, key=lambda item: str(item["name"])),
            "url": run["url"],
            "workflow_name": workflow,
        }
    missing = sorted(set(REQUIRED_WORKFLOWS) - set(selected))
    require(not missing, "SUCCESSFUL_SOURCE_WORKFLOWS_MISSING", ",".join(missing))
    return {
        "checks": [
            "GCC_CPP20_CPP23_PLANNER_LIFECYCLE_MUTANTS_FUZZ_ABI_PASS",
            "CLANG_ASAN_UBSAN_SCHEDULING_PASS",
            "JDK25_REFERENCE_FFM_TRANSPORT_PASS",
            "JDK26_COMPATIBILITY_FFM_TRANSPORT_PASS",
            "PYTHON_RUFF_FORMAT_MYPY_AND_TESTS_PASS",
            "REFINEMENT_AND_BOUNDARY_EVIDENCE_REPRODUCED",
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
    require(isinstance(evidence, dict), "EVIDENCE_ROOT_INVALID")
    require(raw == canonical_json_bytes(evidence), "EVIDENCE_NOT_CANONICAL")
    require(evidence.get("status") == "PASS", "CI_STATUS_INVALID")
    require(evidence.get("formal_semantics_id") == FORMAL_ID, "FORMAL_ID_INVALID")
    require(
        evidence.get("semantic_completeness_claimed") is False,
        "SEMANTIC_COMPLETENESS_CLAIM_INVALID",
    )
    source = evidence.get("source")
    require(isinstance(source, dict), "EVIDENCE_SOURCE_INVALID")
    commit = str(source.get("commit"))
    require(git_text("rev-parse", f"{commit}^{{commit}}") == commit, "SOURCE_COMMIT_INVALID")
    require(
        source.get("tree") == git_text("rev-parse", f"{commit}^{{tree}}"), "SOURCE_TREE_INVALID"
    )
    runs = evidence.get("runs")
    require(isinstance(runs, dict) and set(runs) == set(REQUIRED_WORKFLOWS), "CI_RUNS_INVALID")
    for workflow, required_jobs in REQUIRED_WORKFLOWS.items():
        run = runs.get(workflow)
        require(isinstance(run, dict) and run.get("head_sha") == commit, "CI_SOURCE_DIVERGENCE")
        jobs = run.get("jobs")
        require(isinstance(jobs, list), "CI_JOBS_INVALID")
        conclusions = {str(job.get("name")): str(job.get("conclusion")) for job in jobs}
        require(
            all(conclusions.get(name) == "success" for name in required_jobs),
            "CI_JOB_MATRIX_INCOMPLETE",
            workflow,
        )
    require(evidence.get("workflows") == workflow_hashes(commit), "WORKFLOW_HASHES_INVALID")
    return evidence


def fail(error: Exception) -> NoReturn:
    print(
        canonical_json_bytes(
            {"error": str(error), "phase": "007-scheduling-ci", "status": "FAIL"}
        ).decode()
    )
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    arguments = parser.parse_args()
    try:
        if arguments.write:
            require(arguments.source_commit is not None, "SOURCE_COMMIT_REQUIRED")
            result = capture(arguments.source_commit)
            OUTPUT.write_bytes(canonical_json_bytes(result))
        else:
            require(arguments.check_only, "CHECK_ONLY_REQUIRED")
            result = verify()
    except (CaptureError, OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        fail(error)
    print(canonical_json_bytes(result).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
