"""Capture successful GitHub execution evidence for one exact feature-005 source commit."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "005-content-addressed-p2p-distribution"
OUTPUT: Final = FEATURE / "evidence/native-execution.json"
WORKFLOWS: Final = {
    "Feature 005 distribution verification",
    "Native core matrix",
    "Native sanitizer matrix",
    "Python worker quality",
}
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def run_json(*arguments: str) -> Any:
    process = subprocess.run(list(arguments), cwd=ROOT, check=True, capture_output=True, text=True)
    return json.loads(process.stdout)


def git_text(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    if not arguments.write:
        parser.error("--write is required")
    commit = git_text("rev-parse", arguments.source_commit)
    runs = run_json(
        "gh",
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
        workflow = run.get("workflowName")
        if (
            workflow in WORKFLOWS
            and run.get("headSha") == commit
            and run.get("status") == "completed"
            and run.get("conclusion") == "success"
            and workflow not in selected
        ):
            detail = run_json("gh", "run", "view", str(run["databaseId"]), "--json", "jobs")
            jobs = []
            for job in detail["jobs"]:
                jobs.append(
                    {
                        "conclusion": job["conclusion"],
                        "database_id": job["databaseId"],
                        "name": job["name"],
                        "url": job["url"],
                        "verified_steps": [
                            step["name"]
                            for step in job.get("steps", [])
                            if step.get("conclusion") == "success"
                        ],
                    }
                )
            selected[workflow] = {
                "conclusion": run["conclusion"],
                "database_id": run["databaseId"],
                "event": run["event"],
                "head_sha": run["headSha"],
                "jobs": sorted(jobs, key=lambda item: item["name"]),
                "url": run["url"],
                "workflow_name": workflow,
            }
    missing = sorted(WORKFLOWS - selected.keys())
    if missing:
        raise RuntimeError(f"successful workflow runs are missing: {missing}")
    workflow_paths = [
        ROOT / ".github/workflows/distribution.yml",
        ROOT / ".github/workflows/native.yml",
        ROOT / ".github/workflows/native-verification.yml",
        ROOT / ".github/workflows/ci.yml",
    ]
    result = {
        "architecture_coverage": {
            "aarch64": {"reason": "NO_EXACT_PINNED_RUNNER_AVAILABLE", "status": "NOT_RUN"},
            "x86_64": "PASS",
        },
        "formal_semantics_id": FORMAL_ID,
        "runs": {key: selected[key] for key in sorted(selected)},
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "commit": commit,
            "tree": git_text("rev-parse", f"{commit}^{{tree}}"),
        },
        "status": "PASS",
        "task_ids": ["T011", "T014", "T015", "T024", "T027", "T031"],
        "workflows": [
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
            }
            for path in workflow_paths
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(canonical_json_bytes(result) + b"\n")
    print(
        canonical_json_bytes({"output": str(OUTPUT.relative_to(ROOT)), "status": "PASS"}).decode()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
