"""Capture successful exact-source feature-008 GitHub Actions evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
OUTPUT: Final = ROOT / "specs/008-certificates-and-consensus/evidence/certificate-ci.json"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
REQUIRED_WORKFLOWS: Final = {
    "Feature 008 certificate and Apply verification": {
        "Native C++20 certificate chain",
        "Native C++23 certificate chain",
        "Clang ASan UBSan certificate chain",
        "Clang TSan certificate durability",
        "JDK 25 certificate FFM adapter",
        "JDK 26 certificate FFM adapter",
        "Certificate refinement and evidence gate",
    },
    "Python worker quality": {"python-foundation"},
}
WORKFLOW_PATHS: Final = (
    ".github/workflows/certificates.yml",
    ".github/workflows/ci.yml",
)


class CaptureError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise CaptureError(code)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, check=False)
    require(process.returncode == 0, "GIT_FAILED:" + process.stderr.decode(errors="replace"))
    return process.stdout.replace(b"\r\n", b"\n")


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode().strip()


def gh_json(*arguments: str) -> Any:
    process = subprocess.run(
        ["gh", *arguments], cwd=ROOT, capture_output=True, check=False, text=True
    )
    require(process.returncode == 0, "GH_FAILED:" + process.stderr.strip())
    return json.loads(process.stdout)


def workflow_hashes(commit: str) -> list[dict[str, str]]:
    return [
        {"path": path, "sha256": hashlib.sha256(git_bytes("show", f"{commit}:{path}")).hexdigest()}
        for path in WORKFLOW_PATHS
    ]


def capture(source_commit: str) -> dict[str, Any]:
    commit = git_text("rev-parse", f"{source_commit}^{{commit}}")
    runs = gh_json(
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
    for run in sorted(runs, key=lambda value: int(value["databaseId"]), reverse=True):
        workflow = str(run.get("workflowName"))
        if (
            workflow not in REQUIRED_WORKFLOWS
            or workflow in selected
            or run.get("headSha") != commit
            or run.get("status") != "completed"
            or run.get("conclusion") != "success"
        ):
            continue
        details = gh_json("run", "view", str(run["databaseId"]), "--json", "conclusion,jobs,url")
        jobs = [
            {"conclusion": job.get("conclusion"), "name": job.get("name"), "url": job.get("url")}
            for job in details.get("jobs", [])
        ]
        conclusions = {str(job["name"]): str(job["conclusion"]) for job in jobs}
        if not all(conclusions.get(name) == "success" for name in REQUIRED_WORKFLOWS[workflow]):
            continue
        selected[workflow] = {
            "database_id": run["databaseId"],
            "event": run["event"],
            "head_sha": run["headSha"],
            "jobs": sorted(jobs, key=lambda value: str(value["name"])),
            "url": run["url"],
            "workflow_name": workflow,
        }
    require(set(selected) == set(REQUIRED_WORKFLOWS), "SUCCESSFUL_SOURCE_WORKFLOWS_MISSING")
    return {
        "checks": [
            "GCC_CPP20_CPP23_CHAIN_MUTANTS_FUZZ_ABI_PASS",
            "CLANG_ASAN_UBSAN_TSAN_PASS",
            "JDK25_JDK26_NATIVE_FFM_PASS",
            "PYTHON_QUALITY_MATRIX_PASS",
            "EXACT_SOURCE_REFINEMENT_GATE_PASS",
        ],
        "formal_semantics_id": FORMAL_ID,
        "runs": {name: selected[name] for name in sorted(selected)},
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {"commit": commit, "tree": git_text("rev-parse", f"{commit}^{{tree}}")},
        "status": "PASS",
        "workflows": workflow_hashes(commit),
    }


def verify() -> dict[str, Any]:
    raw = OUTPUT.read_bytes()
    result = json.loads(raw)
    require(raw == canonical(result), "CI_EVIDENCE_NOT_CANONICAL")
    require(result.get("status") == "PASS", "CI_STATUS_INVALID")
    require(result.get("formal_semantics_id") == FORMAL_ID, "FORMAL_ID_INVALID")
    require(result.get("semantic_completeness_claimed") is False, "SEMANTIC_CLAIM_INVALID")
    commit = result["source"]["commit"]
    require(result["source"]["tree"] == git_text("rev-parse", f"{commit}^{{tree}}"), "TREE_DRIFT")
    require(result.get("workflows") == workflow_hashes(commit), "WORKFLOW_HASH_DRIFT")
    require(set(result.get("runs", {})) == set(REQUIRED_WORKFLOWS), "CI_RUN_SET_INVALID")
    for workflow, required in REQUIRED_WORKFLOWS.items():
        run = result["runs"][workflow]
        require(run.get("head_sha") == commit, "CI_SOURCE_DIVERGENCE")
        conclusions = {str(job["name"]): str(job["conclusion"]) for job in run["jobs"]}
        require(
            all(conclusions.get(name) == "success" for name in required), "CI_JOB_MATRIX_INCOMPLETE"
        )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--source-commit")
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    require(arguments.check_only != arguments.write, "EXACT_MODE_REQUIRED")
    if arguments.write:
        require(arguments.source_commit is not None, "SOURCE_COMMIT_REQUIRED")
        result = capture(arguments.source_commit)
        OUTPUT.write_bytes(canonical(result))
    else:
        result = verify()
    print(canonical(result).decode())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CaptureError, OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(canonical({"error": str(error), "status": "FAIL"}).decode())
        raise SystemExit(2) from error
