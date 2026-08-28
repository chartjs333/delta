"""Capture or verify immutable GitHub execution evidence for feature 004."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Final, NoReturn

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "004-compressed-delta-protocol"
EVIDENCE: Final = FEATURE / "evidence" / "native-execution.json"
REPOSITORY: Final = "chartjs333/delta"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
WORKFLOWS: Final = {
    "native": ("Native core matrix", ".github/workflows/native.yml"),
    "python": ("Python worker quality", ".github/workflows/ci.yml"),
    "sanitizers": ("Native sanitizer matrix", ".github/workflows/native-verification.yml"),
}
EXPECTED_JOBS: Final = {
    "native": {
        "clang-20.1.8 C++20/C++23": ["Compile and test both language modes offline"],
        "gcc-14.2.0 C++20/C++23": ["Compile and test both language modes offline"],
        "JDK 25 runtime descriptor": [
            "Build native FFM library offline",
            "Compile and verify descriptor with offline execution policy",
        ],
        "JDK 26 runtime descriptor": [
            "Build native FFM library offline",
            "Compile and verify descriptor with offline execution policy",
        ],
    },
    "python": {
        "python-foundation": [
            "Run offline Python and protocol gates",
            "Verify feature 004 preflight and fixed-point contracts",
        ]
    },
    "sanitizers": {
        "Clang ASan UBSan core runtime ABI fuzz": [
            "Run ASan and UBSan offline",
            "Run feature-004 parser and FFI sanitizers offline",
        ],
        "GCC TSan reactor recovery": ["Run TSan offline"],
    },
}


class NativeExecutionError(RuntimeError):
    pass


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise NativeExecutionError(f"{code}: {detail}" if detail else code)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def command_json(command: list[str]) -> object:
    process = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    require(process.returncode == 0, "COMMAND_FAILED", process.stderr.strip())
    return json.loads(process.stdout)


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    require(
        process.returncode == 0,
        "GIT_COMMAND_FAILED",
        process.stderr.decode(errors="replace").strip(),
    )
    return process.stdout


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode("utf-8").strip()


def workflow_records(commit: str) -> list[dict[str, str]]:
    return [
        {
            "path": path,
            "sha256": hashlib.sha256(git_bytes("show", f"{commit}:{path}")).hexdigest(),
            "workflow_name": workflow,
        }
        for _, (workflow, path) in sorted(WORKFLOWS.items())
    ]


def capture(source_commit: str) -> dict[str, object]:
    commit = git_text("rev-parse", source_commit)
    require(commit == git_text("rev-parse", "HEAD"), "CAPTURE_SOURCE_NOT_HEAD")
    listed = command_json(
        [
            "gh",
            "run",
            "list",
            "--commit",
            commit,
            "--event",
            "push",
            "--limit",
            "20",
            "--json",
            "databaseId,workflowName,event,headSha,status,conclusion,url",
        ]
    )
    require(isinstance(listed, list), "RUN_LIST_INVALID")
    runs: dict[str, object] = {}
    for key, (workflow_name, _) in WORKFLOWS.items():
        matches = [
            item
            for item in listed
            if isinstance(item, dict)
            and item.get("workflowName") == workflow_name
            and item.get("headSha") == commit
            and item.get("event") == "push"
        ]
        require(len(matches) == 1, "RUN_NOT_UNIQUE", workflow_name)
        listed_run = matches[0]
        require(
            listed_run.get("status") == "completed" and listed_run.get("conclusion") == "success",
            "RUN_NOT_SUCCESS",
            workflow_name,
        )
        run_id = listed_run.get("databaseId")
        require(isinstance(run_id, int) and run_id > 0, "RUN_ID_INVALID", workflow_name)
        detail = command_json(
            [
                "gh",
                "run",
                "view",
                str(run_id),
                "--json",
                "databaseId,workflowName,event,headSha,conclusion,url,jobs",
            ]
        )
        require(isinstance(detail, dict), "RUN_DETAIL_INVALID", workflow_name)
        jobs = detail.get("jobs")
        require(isinstance(jobs, list), "RUN_JOBS_INVALID", workflow_name)
        expected = EXPECTED_JOBS[key]
        by_name = {job.get("name"): job for job in jobs if isinstance(job, dict)}
        require(set(by_name) == set(expected), "RUN_JOB_SET_INVALID", workflow_name)
        normalized_jobs = []
        for name, required_steps in sorted(expected.items()):
            job = by_name[name]
            require(job.get("conclusion") == "success", "JOB_NOT_SUCCESS", name)
            steps = job.get("steps")
            require(isinstance(steps, list), "JOB_STEPS_INVALID", name)
            steps_by_name = {step.get("name"): step for step in steps if isinstance(step, dict)}
            for step in required_steps:
                require(
                    step in steps_by_name and steps_by_name[step].get("conclusion") == "success",
                    "REQUIRED_STEP_NOT_SUCCESS",
                    f"{name}:{step}",
                )
            normalized_jobs.append(
                {
                    "conclusion": "success",
                    "database_id": job["databaseId"],
                    "name": name,
                    "url": job["url"],
                    "verified_steps": required_steps,
                }
            )
        runs[key] = {
            "conclusion": "success",
            "database_id": detail["databaseId"],
            "event": "push",
            "head_sha": commit,
            "jobs": normalized_jobs,
            "repository": REPOSITORY,
            "url": detail["url"],
            "workflow_name": workflow_name,
        }
    return {
        "architecture_coverage": {
            "aarch64": {
                "reason": "NO_EXACT_PINNED_RUNNER_AVAILABLE",
                "status": "NOT_RUN",
            },
            "x86_64": "PASS",
        },
        "formal_semantics_id": FORMAL_ID,
        "runs": runs,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "commit": commit,
            "tree": git_text("rev-parse", f"{commit}^{{tree}}"),
        },
        "status": "PASS",
        "task_ids": ["T041", "T042", "T043", "T044"],
        "workflows": workflow_records(commit),
    }


def verify(document: dict[str, object]) -> dict[str, object]:
    require(document.get("schema_version") == "1.0.0", "SCHEMA_VERSION_INVALID")
    require(document.get("status") == "PASS", "STATUS_NOT_PASS")
    require(document.get("formal_semantics_id") == FORMAL_ID, "FORMAL_ID_INVALID")
    require(document.get("semantic_completeness_claimed") is False, "SEMANTIC_CLAIM_INVALID")
    require(document.get("task_ids") == ["T041", "T042", "T043", "T044"], "TASK_IDS_INVALID")
    source = document.get("source")
    require(isinstance(source, dict), "SOURCE_INVALID")
    commit = source.get("commit")
    require(
        isinstance(commit, str) and re.fullmatch(r"[0-9a-f]{40}", commit) is not None,
        "SOURCE_COMMIT_INVALID",
    )
    require(
        source.get("tree") == git_text("rev-parse", f"{commit}^{{tree}}"), "SOURCE_TREE_INVALID"
    )
    ancestry = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT, check=False
    )
    require(ancestry.returncode == 0, "SOURCE_NOT_ANCESTOR")
    require(document.get("workflows") == workflow_records(commit), "WORKFLOW_RECORDS_INVALID")
    architecture = document.get("architecture_coverage")
    require(
        architecture
        == {
            "aarch64": {
                "reason": "NO_EXACT_PINNED_RUNNER_AVAILABLE",
                "status": "NOT_RUN",
            },
            "x86_64": "PASS",
        },
        "ARCHITECTURE_COVERAGE_INVALID",
    )
    runs = document.get("runs")
    require(isinstance(runs, dict) and set(runs) == set(WORKFLOWS), "RUN_SET_INVALID")
    run_ids: set[int] = set()
    job_ids: set[int] = set()
    for key, (workflow_name, _) in WORKFLOWS.items():
        run = runs[key]
        require(isinstance(run, dict), "RUN_INVALID", key)
        run_id = run.get("database_id")
        require(isinstance(run_id, int) and run_id > 0 and run_id not in run_ids, "RUN_ID_INVALID")
        run_ids.add(run_id)
        expected_url = f"https://github.com/{REPOSITORY}/actions/runs/{run_id}"
        require(
            run.get("conclusion") == "success"
            and run.get("event") == "push"
            and run.get("head_sha") == commit
            and run.get("repository") == REPOSITORY
            and run.get("url") == expected_url
            and run.get("workflow_name") == workflow_name,
            "RUN_METADATA_INVALID",
            key,
        )
        jobs = run.get("jobs")
        require(isinstance(jobs, list), "JOB_SET_INVALID", key)
        by_name = {job.get("name"): job for job in jobs if isinstance(job, dict)}
        require(set(by_name) == set(EXPECTED_JOBS[key]), "JOB_NAMES_INVALID", key)
        for name, steps in EXPECTED_JOBS[key].items():
            job = by_name[name]
            job_id = job.get("database_id")
            require(
                isinstance(job_id, int) and job_id > 0 and job_id not in job_ids,
                "JOB_ID_INVALID",
                name,
            )
            job_ids.add(job_id)
            require(
                job.get("conclusion") == "success"
                and job.get("url") == f"{expected_url}/job/{job_id}"
                and job.get("verified_steps") == steps,
                "JOB_METADATA_INVALID",
                name,
            )
    return document


def fail(error: Exception) -> NoReturn:
    print(canonical_json_bytes({"error": str(error), "status": "FAIL"}).decode("utf-8"))
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--source-commit")
    arguments = parser.parse_args()
    try:
        if arguments.capture:
            require(arguments.source_commit is not None, "SOURCE_COMMIT_REQUIRED")
            result = capture(arguments.source_commit)
            EVIDENCE.write_bytes(canonical_json_bytes(result) + b"\n")
        else:
            require(arguments.check_only, "CHECK_ONLY_REQUIRED")
            raw = EVIDENCE.read_bytes()
            result = json.loads(raw.decode("utf-8"))
            require(isinstance(result, dict), "EVIDENCE_ROOT_INVALID")
            require(raw == canonical_json_bytes(result) + b"\n", "EVIDENCE_NOT_CANONICAL")
            verify(result)
    except (NativeExecutionError, OSError, ValueError, json.JSONDecodeError) as exc:
        fail(exc)
    print(canonical_json_bytes(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
