"""T040: deterministic Step 5C evidence-finalization consistency checks."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Iterator
from pathlib import Path
from typing import Any

ROOT_DIR = Path(__file__).resolve().parents[4]
EVIDENCE_DIR = Path(__file__).resolve().parents[1] / "evidence"

QUALIFICATION_BASE_SHA = "94721c271307e48aae1e1f09133660d169387ed0"
QUALIFIED_CODE_TEST_HEAD_SHA = "f5a6f37d9720b620bdd871ccbc7b0e4b6b60dc87"
PR39_REVIEWED_SHA = "614355b36aac8d00dca3043b732ae50f7023e3a5"
PR39_MERGE_SHA = "1a4d1a17c5e8f75941b1efb6e915b7405446d9b8"

TASK_EVIDENCE_FILES = {
    "step5c:T035": "t035-transport-profile.json",
    "step5c:T036": "t036-worker-dispatch-integration.json",
    "step5c:T037": "t037-admin-ui-integration.json",
    "step5c:T038": "t038-end-to-end-lineage.json",
    "step5c:T039": "t039-recovery-terminal-semantics.json",
}

PROTECTED_SPINE_PATHS = (
    "delta-core-cpp",
    "delta-runtime-cpp",
    "delta-ffi",
    "delta-node-java",
    "formal",
    "specs/000-formal-tla-spec",
)

T036_PRODUCTION_ARTIFACTS = {
    "delta-controller-python/src/deltacontroller/dispatch.py": (
        "b0d03f4c740cae10be28450949ebbf577e3d6945d3565f9f423208c2d60ecc6c"
    ),
    "delta-controller-python/src/deltacontroller/gate.py": (
        "e4b8193ee653dec029d70129ceb3675b09d6b99abf9bd6a7464b63c8a29218bc"
    ),
    "delta-worker-python/src/deltatorrent/live_execution/preflight.py": (
        "3f8cf0b9219b4499dad034846a78b466bb4e5ebc0d172207c493aabd887d0f76"
    ),
    "delta-worker-python/tests/live_execution/test_dispatch.py": (
        "ebf10004bd9d224087afb6dcad2fd715b3492a1b0492103210aff9e613b64863"
    ),
}

PENDING_VALUE = re.compile(r"\bPENDING_[A-Z0-9_]*\b")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _git_blob_bytes(revision: str, artifact_path: str) -> bytes:
    completed = subprocess.run(
        ["git", "cat-file", "blob", f"{revision}:{artifact_path}"],
        cwd=ROOT_DIR,
        check=True,
        capture_output=True,
    )
    return completed.stdout


def _git_text(*arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=ROOT_DIR,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _sha256(raw_bytes: bytes) -> str:
    return hashlib.sha256(raw_bytes).hexdigest()


def _walk_strings(value: Any, path: str = "$") -> Iterator[tuple[str, str]]:
    if isinstance(value, str):
        yield path, value
    elif isinstance(value, dict):
        for key, nested in value.items():
            yield from _walk_strings(nested, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            yield from _walk_strings(nested, f"{path}[{index}]")


def test_t040_artifact_bindings_match_raw_pr39_git_blobs() -> None:
    failures: list[str] = []
    for evidence_file in TASK_EVIDENCE_FILES.values():
        evidence = _load_json(EVIDENCE_DIR / evidence_file)
        for artifact_path, declared_sha256 in evidence["artifact_sha256"].items():
            qualified_bytes = _git_blob_bytes(QUALIFIED_CODE_TEST_HEAD_SHA, artifact_path)
            reviewed_bytes = _git_blob_bytes(PR39_REVIEWED_SHA, artifact_path)
            merge_bytes = _git_blob_bytes(PR39_MERGE_SHA, artifact_path)
            qualified_sha256 = _sha256(qualified_bytes)
            reviewed_sha256 = _sha256(reviewed_bytes)
            merge_sha256 = _sha256(merge_bytes)
            if qualified_bytes != reviewed_bytes or reviewed_bytes != merge_bytes:
                failures.append(f"{artifact_path}: qualified, reviewed, and merge blobs differ")
            if declared_sha256 != qualified_sha256:
                failures.append(
                    f"{artifact_path}: declared {declared_sha256}, "
                    f"qualified blob {qualified_sha256}"
                )
            if declared_sha256 != reviewed_sha256:
                failures.append(
                    f"{artifact_path}: declared {declared_sha256}, reviewed blob {reviewed_sha256}"
                )
            if declared_sha256 != merge_sha256:
                failures.append(
                    f"{artifact_path}: declared {declared_sha256}, merge blob {merge_sha256}"
                )
    assert not failures, "\n".join(failures)


def test_t040_t036_production_artifact_hashes_remain_exact() -> None:
    t036 = _load_json(EVIDENCE_DIR / TASK_EVIDENCE_FILES["step5c:T036"])
    declared = t036["artifact_sha256"]
    for artifact_path, expected_sha256 in T036_PRODUCTION_ARTIFACTS.items():
        assert declared[artifact_path] == expected_sha256
        assert _sha256(_git_blob_bytes(PR39_REVIEWED_SHA, artifact_path)) == expected_sha256
        assert _sha256(_git_blob_bytes(PR39_MERGE_SHA, artifact_path)) == expected_sha256


def test_t040_representative_artifact_map_matches_task_evidence() -> None:
    qualification = _load_json(EVIDENCE_DIR / "t040_t044_qualification.json")
    for task_id, evidence_file in TASK_EVIDENCE_FILES.items():
        task_evidence = _load_json(EVIDENCE_DIR / evidence_file)
        representative = qualification["task_evidence_map"][task_id]
        artifact_path = representative["artifact"]
        assert representative["commit"] == QUALIFIED_CODE_TEST_HEAD_SHA
        assert representative["artifact_sha256"] == task_evidence["artifact_sha256"][artifact_path]


def test_t040_pr39_preserves_protected_spine() -> None:
    changed_paths = _git_text(
        "diff",
        "--name-only",
        QUALIFICATION_BASE_SHA,
        PR39_REVIEWED_SHA,
        "--",
        *PROTECTED_SPINE_PATHS,
    )
    assert changed_paths == ""


def test_t040_qualification_preserves_distinct_provenance() -> None:
    qualification = _load_json(EVIDENCE_DIR / "t040_t044_qualification.json")
    provenance = qualification["pr39_provenance"]
    assert qualification["final_base_main_sha"] == QUALIFICATION_BASE_SHA
    assert qualification["integration_merge_sha"] == QUALIFIED_CODE_TEST_HEAD_SHA
    assert qualification["tested_head_sha"] == QUALIFIED_CODE_TEST_HEAD_SHA
    assert provenance["qualification_base_sha"] == QUALIFICATION_BASE_SHA
    assert provenance["qualified_code_test_head_sha"] == QUALIFIED_CODE_TEST_HEAD_SHA
    assert provenance["reviewed_sha"] == PR39_REVIEWED_SHA
    assert provenance["merge_sha"] == PR39_MERGE_SHA
    assert (
        len(
            {
                QUALIFICATION_BASE_SHA,
                QUALIFIED_CODE_TEST_HEAD_SHA,
                PR39_REVIEWED_SHA,
                PR39_MERGE_SHA,
            }
        )
        == 4
    )
    assert _git_text("rev-parse", f"{PR39_MERGE_SHA}^1") == QUALIFICATION_BASE_SHA
    assert _git_text("rev-parse", f"{PR39_MERGE_SHA}^2") == PR39_REVIEWED_SHA
    assert _git_text("rev-parse", f"{PR39_REVIEWED_SHA}^") == (QUALIFIED_CODE_TEST_HEAD_SHA)
    assert _git_text("rev-parse", f"{QUALIFIED_CODE_TEST_HEAD_SHA}^2") == (QUALIFICATION_BASE_SHA)
    assert _git_text("rev-parse", f"{PR39_MERGE_SHA}^{{tree}}") == _git_text(
        "rev-parse", f"{PR39_REVIEWED_SHA}^{{tree}}"
    )
    assert _git_text("show", "-s", "--format=%s", PR39_MERGE_SHA) == (
        "Merge pull request #39 from chartjs333/feature/step5c-e2e"
    )


def test_t040_qualification_has_final_pr39_facts_and_no_pending_values() -> None:
    qualification = _load_json(EVIDENCE_DIR / "t040_t044_qualification.json")
    provenance = qualification["pr39_provenance"]
    ci = provenance["exact_head_github_ci"]
    assert provenance["number"] == 39
    assert provenance["state"] == "MERGED"
    assert provenance["url"] == "https://github.com/chartjs333/delta/pull/39"
    assert provenance["merged_at"] == "2026-09-19T11:35:21Z"
    assert provenance["unresolved_review_threads"] == 0
    assert ci == {
        "head_sha": PR39_REVIEWED_SHA,
        "conclusion": "SUCCESS",
        "successful_checks": 36,
        "total_checks": 36,
        "failed_checks": 0,
        "pending_checks": 0,
        "source_url": "https://github.com/chartjs333/delta/pull/39/checks",
    }
    assert qualification["quality_gates"]["github_ci_exact_head"] == (
        "PASS: 36/36 SUCCESS on exact PR head " + PR39_REVIEWED_SHA
    )
    assert qualification["quality_gates"]["step5c_tests"]["tested_head_sha"] == (
        QUALIFIED_CODE_TEST_HEAD_SHA
    )
    release = qualification["release_decision"]
    assert release["reviewed_sha"] == PR39_REVIEWED_SHA
    assert release["unresolved_threads"] == 0
    assert release["pr39_state"] == "MERGED"
    assert release["pr39_merge_sha"] == PR39_MERGE_SHA
    assert release["state"] == "PR39_MERGED"
    assert release["step5c_final_status_claimed"] is False
    assert release["required_closure_authority"] == ("step5c-final-closure-v2 graph node")
    pending: list[str] = []
    for evidence_file in [*TASK_EVIDENCE_FILES.values(), "t040_t044_qualification.json"]:
        evidence = _load_json(EVIDENCE_DIR / evidence_file)
        pending.extend(
            f"{evidence_file}:{path}={value}"
            for path, value in _walk_strings(evidence)
            if PENDING_VALUE.search(value)
        )
    assert not pending, "\n".join(pending)
