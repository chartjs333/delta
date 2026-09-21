#!/usr/bin/env python3
"""Capture or verify exact-head CI evidence for Feature 010 Gate A."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Final

from exactness_gate import (
    BASE_COMMIT,
    FORMAL_ID,
    canonical_bytes,
    canonical_document,
    require,
    source_identity,
    verify_execution,
)

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs/010-wan-benchmark-and-quality"
CI_OUTPUT: Final = FEATURE / "evidence/exactness-ci.json"
EXECUTION_OUTPUT: Final = FEATURE / "evidence/exactness-execution.json"
REPOSITORY: Final = "chartjs333/delta"
WORKFLOWS: Final = {
    "Feature 010 exactness and safety verification": {
        "clang C++20 exact process corpus",
        "clang C++23 exact process corpus",
        "Deterministic fail-closed exactness analyzer",
        "gcc C++20 exact process corpus",
        "gcc C++23 exact process corpus",
        "JDK 25 exact canonical status corpus",
        "JDK 26 exact canonical status corpus",
        "Native attacks crash refinement and fuzz corpus",
    },
    "Feature 005 distribution verification": {
        "clang-20.1.8 native policy C++20/C++23",
        "gcc-14.2.0 native policy C++20/C++23",
        "JDK 25 Netty/FFM data plane",
        "JDK 26 Netty/FFM data plane",
    },
    "Feature 006 hierarchy verification": {
        "Clang ASan UBSan hierarchy",
        "Feature 006 final evidence",
        "JDK 25 hierarchy FFM routing",
        "JDK 26 hierarchy FFM routing",
        "Native C++20 hierarchy",
        "Native C++23 hierarchy",
    },
    "Feature 007 scheduling verification": {
        "Clang ASan UBSan scheduling planner",
        "JDK 25 scheduling FFM adapter",
        "JDK 26 scheduling FFM adapter",
        "Native C++20 scheduling planner",
        "Native C++23 scheduling planner",
        "Scheduling ABI and Java boundary evidence",
    },
    "Feature 008 certificate and Apply verification": {
        "Certificate refinement and evidence gate",
        "Clang ASan UBSan certificate chain",
        "Clang TSan certificate durability",
        "JDK 25 certificate FFM adapter",
        "JDK 26 certificate FFM adapter",
        "Native C++20 certificate chain",
        "Native C++23 certificate chain",
    },
    "Feature 009 certified QLoRA verification": {
        "Clang ASan UBSan QLoRA boundary",
        "Java 25 base-cache and adapter transport",
        "Java 26 base-cache and adapter transport",
        "Native C++20 QLoRA authority",
        "Native C++23 QLoRA authority",
        "QLoRA native and transport boundary gate",
    },
    "Native core matrix": {
        "clang-20.1.8 C++20/C++23",
        "gcc-14.2.0 C++20/C++23",
        "JDK 25 runtime descriptor",
        "JDK 26 runtime descriptor",
    },
    "Native sanitizer matrix": {
        "Clang ASan UBSan core runtime ABI fuzz",
        "GCC TSan reactor recovery",
    },
    "Python worker quality": {"python-foundation"},
}
WORKFLOW_PATHS: Final = {
    "Feature 010 exactness and safety verification": ".github/workflows/feature010-exactness.yml",
    "Feature 005 distribution verification": ".github/workflows/distribution.yml",
    "Feature 006 hierarchy verification": ".github/workflows/hierarchy.yml",
    "Feature 007 scheduling verification": ".github/workflows/scheduling.yml",
    "Feature 008 certificate and Apply verification": ".github/workflows/certificates.yml",
    "Feature 009 certified QLoRA verification": ".github/workflows/qlora.yml",
    "Native core matrix": ".github/workflows/native.yml",
    "Native sanitizer matrix": ".github/workflows/native-verification.yml",
    "Python worker quality": ".github/workflows/ci.yml",
}


def command_json(command: list[str]) -> Any:
    process = subprocess.run(command, cwd=ROOT, check=False, capture_output=True, text=True)
    require(process.returncode == 0, "COMMAND_FAILED", process.stderr.strip())
    return json.loads(process.stdout)


def workflow_hashes(commit: str) -> list[dict[str, str]]:
    result = []
    for workflow, path in sorted(WORKFLOW_PATHS.items()):
        raw = subprocess.run(
            ["git", "show", f"{commit}:{path}"], cwd=ROOT, check=True, capture_output=True
        ).stdout
        result.append(
            {
                "path": path,
                "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
                "workflow": workflow,
            }
        )
    return result


def runs_for_commit(commit: str) -> list[dict[str, Any]]:
    result = command_json(
        [
            "gh",
            "run",
            "list",
            "--commit",
            commit,
            "--limit",
            "100",
            "--json",
            "databaseId,workflowName,event,headSha,status,conclusion,url",
        ]
    )
    require(isinstance(result, list), "RUN_LIST_INVALID")
    return result


def select_runs(commit: str) -> dict[str, dict[str, Any]]:
    listed = runs_for_commit(commit)
    selected: dict[str, dict[str, Any]] = {}
    for workflow, expected_jobs in WORKFLOWS.items():
        candidates = [
            item
            for item in listed
            if isinstance(item, dict)
            and item.get("workflowName") == workflow
            and item.get("headSha") == commit
            and item.get("status") == "completed"
            and item.get("conclusion") == "success"
        ]
        require(bool(candidates), "SUCCESSFUL_WORKFLOW_MISSING", workflow)
        chosen = max(candidates, key=lambda item: int(item["databaseId"]))
        details = command_json(
            [
                "gh",
                "run",
                "view",
                str(chosen["databaseId"]),
                "--json",
                "databaseId,workflowName,event,headSha,conclusion,url,jobs",
            ]
        )
        require(isinstance(details, dict), "RUN_DETAIL_INVALID", workflow)
        jobs = details.get("jobs")
        require(isinstance(jobs, list), "RUN_JOBS_INVALID", workflow)
        by_name = {job.get("name"): job for job in jobs if isinstance(job, dict)}
        require(expected_jobs <= set(by_name), "RUN_JOB_SET_INVALID", workflow)
        normalized = []
        for name in sorted(expected_jobs):
            job = by_name[name]
            require(job.get("conclusion") == "success", "JOB_NOT_SUCCESS", name)
            steps = job.get("steps")
            require(isinstance(steps, list), "JOB_STEPS_INVALID", name)
            failed_steps = [
                str(step.get("name"))
                for step in steps
                if isinstance(step, dict) and step.get("conclusion") not in {"success", "skipped"}
            ]
            require(not failed_steps, "JOB_STEP_FAILED", f"{name}:{','.join(failed_steps)}")
            normalized.append(
                {
                    "conclusion": "success",
                    "database_id": job["databaseId"],
                    "name": name,
                    "url": job["url"],
                }
            )
        selected[workflow] = {
            "conclusion": "success",
            "database_id": details["databaseId"],
            "event": details["event"],
            "head_sha": details["headSha"],
            "jobs": normalized,
            "url": details["url"],
            "workflow_name": workflow,
        }
    return selected


def exactness_artifact(run_id: int, commit: str) -> tuple[list[dict[str, Any]], bytes]:
    artifact_name = f"feature010-exactness-execution-{run_id}-{commit}"
    response = command_json(
        ["gh", "api", f"repos/{REPOSITORY}/actions/runs/{run_id}/artifacts", "--paginate"]
    )
    require(isinstance(response, dict), "ARTIFACT_RESPONSE_INVALID")
    artifacts = response.get("artifacts")
    require(isinstance(artifacts, list), "ARTIFACT_LIST_INVALID")
    expected_names = {
        artifact_name,
        f"feature010-java-jdk25-{commit}",
        f"feature010-java-jdk26-{commit}",
        f"feature010-native-clang-cpp20-{commit}",
        f"feature010-native-clang-cpp23-{commit}",
        f"feature010-native-gcc-cpp20-{commit}",
        f"feature010-native-gcc-cpp23-{commit}",
        f"feature010-safety-{commit}",
    }
    by_name = {item.get("name"): item for item in artifacts if isinstance(item, dict)}
    require(set(by_name) == expected_names, "EXACTNESS_ARTIFACT_SET")
    with tempfile.TemporaryDirectory(prefix="delta-feature010-exactness-") as temporary:
        target = Path(temporary)
        process = subprocess.run(
            ["gh", "run", "download", str(run_id), "--name", artifact_name, "--dir", str(target)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        require(process.returncode == 0, "ARTIFACT_DOWNLOAD_FAILED", process.stderr.strip())
        path = target / "exactness-execution.json"
        require(path.is_file(), "EXECUTION_ARTIFACT_FILE_MISSING")
        value = verify_execution(path)
        raw = path.read_bytes()
    require(value["source"]["commit"] == commit, "EXECUTION_SOURCE_DIVERGENCE")
    normalized = []
    for name in sorted(expected_names):
        item = by_name[name]
        require(item.get("expired") is False, "EXACTNESS_ARTIFACT_EXPIRED", name)
        record = {
            "archive_digest": item.get("digest"),
            "artifact_id": item.get("id"),
            "artifact_name": name,
            "created_at": item.get("created_at"),
            "size_in_bytes": item.get("size_in_bytes"),
        }
        require(isinstance(record["artifact_id"], int), "ARTIFACT_ID_INVALID", name)
        normalized.append(record)
    return normalized, raw


def build(source_commit: str) -> tuple[dict[str, Any], bytes]:
    source = source_identity(source_commit)
    commit = source["commit"]
    selected = select_runs(commit)
    exactness_run = selected["Feature 010 exactness and safety verification"]
    artifacts, execution_raw = exactness_artifact(int(exactness_run["database_id"]), commit)
    execution = json.loads(execution_raw)
    require(execution.get("source") == source, "EXECUTION_SOURCE_INVALID")
    total_jobs = sum(len(run["jobs"]) for run in selected.values())
    result = {
        "artifacts": artifacts,
        "authority": {
            "feature010_go": False,
            "primary_observation_count": 0,
            "qualifying_gate_c": False,
            "qualifying_gate_d": False,
            "result_qc": None,
        },
        "formal_semantics_id": FORMAL_ID,
        "execution_sha256": "sha256:" + hashlib.sha256(execution_raw).hexdigest(),
        "required_job_count": total_jobs,
        "runs": {name: selected[name] for name in sorted(selected)},
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": source,
        "status": "PASS",
        "type_name": "FEATURE010_EXACT_HEAD_CI",
        "workflows": workflow_hashes(commit),
    }
    return result, execution_raw


def verify_ci(value: dict[str, Any], execution_raw: bytes | None = None) -> dict[str, Any]:
    require(
        set(value)
        == {
            "artifacts",
            "authority",
            "execution_sha256",
            "formal_semantics_id",
            "required_job_count",
            "runs",
            "schema_version",
            "semantic_completeness_claimed",
            "source",
            "status",
            "type_name",
            "workflows",
        },
        "CI_FIELDS",
    )
    require(value.get("type_name") == "FEATURE010_EXACT_HEAD_CI", "CI_TYPE")
    require(value.get("schema_version") == "1.0.0", "CI_SCHEMA")
    require(value.get("status") == "PASS", "CI_STATUS")
    require(value.get("formal_semantics_id") == FORMAL_ID, "CI_FORMAL_ID")
    require(value.get("semantic_completeness_claimed") is False, "CI_SEMANTIC_CLAIM")
    source = value.get("source")
    require(isinstance(source, dict), "CI_SOURCE")
    commit = source.get("commit")
    require(isinstance(commit, str), "CI_SOURCE_COMMIT")
    require(source == source_identity(commit), "CI_SOURCE_IDENTITY")
    require(value.get("workflows") == workflow_hashes(commit), "CI_WORKFLOW_HASHES")
    execution_sha256 = value.get("execution_sha256")
    require(
        isinstance(execution_sha256, str)
        and execution_sha256.startswith("sha256:")
        and len(execution_sha256) == 71,
        "CI_EXECUTION_HASH",
    )
    if execution_raw is not None:
        require(
            execution_sha256 == "sha256:" + hashlib.sha256(execution_raw).hexdigest(),
            "CI_EXECUTION_HASH_MISMATCH",
        )
    runs = value.get("runs")
    require(isinstance(runs, dict) and set(runs) == set(WORKFLOWS), "CI_RUN_SET")
    job_count = 0
    run_ids: set[int] = set()
    job_ids: set[int] = set()
    for workflow, expected_jobs in WORKFLOWS.items():
        run = runs[workflow]
        require(isinstance(run, dict), "CI_RUN_INVALID", workflow)
        require(
            set(run)
            == {
                "conclusion",
                "database_id",
                "event",
                "head_sha",
                "jobs",
                "url",
                "workflow_name",
            },
            "CI_RUN_FIELDS",
            workflow,
        )
        run_id = run.get("database_id")
        require(isinstance(run_id, int) and run_id not in run_ids, "CI_RUN_ID", workflow)
        run_ids.add(run_id)
        require(run.get("head_sha") == commit, "CI_HEAD_DIVERGENCE", workflow)
        require(run.get("conclusion") == "success", "CI_RUN_NOT_SUCCESS", workflow)
        require(run.get("event") in {"pull_request", "workflow_dispatch"}, "CI_RUN_EVENT")
        require(isinstance(run.get("url"), str) and run["url"], "CI_RUN_URL")
        require(run.get("workflow_name") == workflow, "CI_WORKFLOW_NAME", workflow)
        jobs = run.get("jobs")
        require(isinstance(jobs, list), "CI_JOBS_INVALID", workflow)
        require({job.get("name") for job in jobs} == expected_jobs, "CI_JOB_SET", workflow)
        for job in jobs:
            require(
                set(job) == {"conclusion", "database_id", "name", "url"},
                "CI_JOB_FIELDS",
            )
            job_id = job.get("database_id")
            require(isinstance(job_id, int) and job_id not in job_ids, "CI_JOB_ID")
            job_ids.add(job_id)
            require(job.get("conclusion") == "success", "CI_JOB_NOT_SUCCESS")
            require(isinstance(job.get("url"), str) and job["url"], "CI_JOB_URL")
        job_count += len(jobs)
    require(value.get("required_job_count") == job_count, "CI_JOB_COUNT")
    require(
        value.get("authority")
        == {
            "feature010_go": False,
            "primary_observation_count": 0,
            "qualifying_gate_c": False,
            "qualifying_gate_d": False,
            "result_qc": None,
        },
        "CI_AUTHORITY",
    )
    artifacts = value.get("artifacts")
    require(
        isinstance(artifacts, list) and len(artifacts) == 8,
        "CI_ARTIFACT_COUNT",
    )
    expected_run_id = runs["Feature 010 exactness and safety verification"]["database_id"]
    expected_artifact_names = {
        f"feature010-exactness-execution-{expected_run_id}-{commit}",
        f"feature010-java-jdk25-{commit}",
        f"feature010-java-jdk26-{commit}",
        f"feature010-native-clang-cpp20-{commit}",
        f"feature010-native-clang-cpp23-{commit}",
        f"feature010-native-gcc-cpp20-{commit}",
        f"feature010-native-gcc-cpp23-{commit}",
        f"feature010-safety-{commit}",
    }
    require(
        {artifact.get("artifact_name") for artifact in artifacts} == expected_artifact_names,
        "CI_ARTIFACT_NAMES",
    )
    artifact_ids: set[int] = set()
    for artifact in artifacts:
        require(
            set(artifact)
            == {
                "archive_digest",
                "artifact_id",
                "artifact_name",
                "created_at",
                "size_in_bytes",
            },
            "CI_ARTIFACT_FIELDS",
        )
        artifact_id = artifact["artifact_id"]
        require(
            isinstance(artifact_id, int) and artifact_id not in artifact_ids,
            "CI_ARTIFACT_ID",
        )
        artifact_ids.add(artifact_id)
        require(
            isinstance(artifact["size_in_bytes"], int) and artifact["size_in_bytes"] > 0,
            "CI_ARTIFACT_SIZE",
        )
        require(
            isinstance(artifact["archive_digest"], str)
            and artifact["archive_digest"].startswith("sha256:")
            and len(artifact["archive_digest"]) == 71,
            "CI_ARTIFACT_DIGEST",
        )
        require(
            isinstance(artifact["created_at"], str) and artifact["created_at"],
            "CI_ARTIFACT_TIME",
        )
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", BASE_COMMIT, commit], cwd=ROOT, check=False
        ).returncode
        == 0,
        "CI_BASE_NOT_ANCESTOR",
    )
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    arguments = parser.parse_args()
    try:
        require(arguments.write != arguments.check_only, "EXACT_MODE_REQUIRED")
        if arguments.write:
            require(arguments.source_commit is not None, "SOURCE_COMMIT_REQUIRED")
            result, execution_raw = build(arguments.source_commit)
            EXECUTION_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            EXECUTION_OUTPUT.write_bytes(execution_raw)
            CI_OUTPUT.write_bytes(canonical_bytes(result) + b"\n")
        else:
            result, _ = canonical_document(CI_OUTPUT)
            canonical_document(EXECUTION_OUTPUT)
            verify_ci(result, EXECUTION_OUTPUT.read_bytes())
            verify_execution(EXECUTION_OUTPUT)
    except (OSError, ValueError, KeyError, json.JSONDecodeError, RuntimeError) as error:
        print(canonical_bytes({"error": str(error), "status": "FAIL"}).decode("utf-8"))
        return 2
    print(canonical_bytes(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
