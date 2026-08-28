"""Verify and publish the final feature-005 compatibility decision."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Final, NoReturn

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "005-content-addressed-p2p-distribution"
OUTPUT: Final = FEATURE / "evidence/final-compatibility.json"
SCRIPT_DIR: Final = FEATURE / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_refinement_traces import canonical_json_bytes  # noqa: E402
from verify_phase_evidence import verify as verify_phase_evidence  # noqa: E402

PREDECESSOR: Final = "bd31efaa6d521bbfc3362ad9aac39455bd29a098"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
MANIFEST_ID: Final = "sha256:d48ff2208becabd6b380503c2de6746dbbe4ec0c450fe67308a9a17d726fc254"
PROFILE_ID: Final = "sha256:de9ca7f1a4e2630f729227e34d51c0c03c565062cc9ba924e465a884acc7987d"
POLICY_REGISTRY_ID: Final = (
    "sha256:c0d1e26526a772498041c34a5c0c5735a4aec3d133e190635f01eb251203d64b"
)


class FinalCompatibilityError(RuntimeError):
    pass


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise FinalCompatibilityError(f"{code}: {detail}" if detail else code)


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    require(process.returncode == 0, "GIT_COMMAND_FAILED", process.stderr.decode(errors="replace"))
    return process.stdout


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode().strip()


def task_ids(text: str, prefix: str) -> set[str]:
    return set(re.findall(rf"^- \[x\] (?:\*\*)?({prefix}\d{{3}})\b", text, flags=re.MULTILINE))


def evidence_artifact(path: Path) -> dict[str, str]:
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def source_artifacts(commit: str) -> list[dict[str, str]]:
    changed = git_text("diff", "--name-only", PREDECESSOR, commit).splitlines()
    result = []
    for path in sorted(item for item in changed if item):
        if subprocess.run(["git", "cat-file", "-e", f"{commit}:{path}"], cwd=ROOT).returncode == 0:
            result.append(
                {
                    "path": path,
                    "sha256": hashlib.sha256(git_bytes("show", f"{commit}:{path}")).hexdigest(),
                }
            )
    return result


def build(source_commit: str) -> dict[str, object]:
    phase = verify_phase_evidence()
    source = phase.get("source")
    require(isinstance(source, dict), "PHASE_SOURCE_INVALID")
    commit = git_text("rev-parse", source_commit)
    require(source.get("commit") == commit, "SOURCE_COMMIT_DIVERGENCE")
    require(
        source.get("tree") == git_text("rev-parse", f"{commit}^{{tree}}"), "SOURCE_TREE_INVALID"
    )
    require(
        not git_text(
            "diff",
            "--name-only",
            PREDECESSOR,
            commit,
            "--",
            "formal/tla",
            "formal/proofs",
            "formal/schemas",
        ),
        "FORMAL_SOURCE_DIFF_PRESENT",
    )
    source_tasks = task_ids(
        git_bytes(
            "show", f"{commit}:specs/005-content-addressed-p2p-distribution/tasks.md"
        ).decode(),
        "T",
    )
    require(
        {f"T{index:03d}" for index in range(31)}.issubset(source_tasks), "SOURCE_TASKS_INCOMPLETE"
    )
    current_tasks = task_ids((FEATURE / "tasks.md").read_text(encoding="utf-8"), "T")
    require(current_tasks == {f"T{index:03d}" for index in range(33)}, "FINAL_TASKS_INCOMPLETE")
    current_runtime = task_ids((FEATURE / "runtime-tasks.md").read_text(encoding="utf-8"), "HR005-")
    require(
        current_runtime == {f"HR005-{index:03d}" for index in range(1, 14)},
        "RUNTIME_TASKS_INCOMPLETE",
    )
    constitution = (ROOT / ".specify/memory/constitution.md").read_text(encoding="utf-8")
    require("**Version**: 2.1.0" in constitution, "CONSTITUTION_VERSION_INVALID")
    golden = json.loads(
        (ROOT / "delta-protocol/fixtures/005/cross-language/golden-v1.json").read_text(
            encoding="utf-8"
        )
    )
    require(golden["manifest"]["content_id"] == MANIFEST_ID, "MANIFEST_ID_DRIFT")
    require(golden["piece_profile"]["content_id"] == PROFILE_ID, "PROFILE_ID_DRIFT")
    require(golden["policy_registry"]["content_id"] == POLICY_REGISTRY_ID, "POLICY_ID_DRIFT")
    evidence_paths = [
        FEATURE / "evidence/preflight.json",
        FEATURE / "evidence/protocol-contracts.json",
        FEATURE / "evidence/distribution-refinement.json",
        FEATURE / "evidence/native-execution.json",
    ]
    return {
        "checks": [
            "ALL_T000_T032_AND_HR005_001_HR005_013_COMPLETE",
            "EXACT_FEATURE004_AND_FORMAL_GO_REVERIFIED",
            "NO_FORMAL_SOURCE_DIFF",
            "CANONICAL_MANIFEST_PIECE_TREE_AND_POLICY_IDS_STABLE",
            "NATIVE_POLICY_IS_SOLE_AUTHORITY",
            "BORROWED_DIRECT_AND_BOUNDED_COPY_EFFECTS_IDENTICAL",
            "PRODUCTION_POLICY_AND_PARSER_MUTANTS_KILLED",
            "ATOMIC_CAS_JOURNAL_RESTART_AND_BIT_ROT_PASS",
            "CORRUPT_SLOW_TRUNCATED_SEED_LOSS_AND_INCOMPLETE_UNION_PASS",
            "GCC_CLANG_CPP20_CPP23_JDK25_JDK26_PASS",
            "LEGAL_AND_ILLEGAL_FORMAL_REFINEMENT_TRACES_PASS",
            "CONSTITUTION_2_1_0_FINAL_CHECK_PASS",
        ],
        "classification": "REFINEMENT_ONLY",
        "evidence_artifacts": [evidence_artifact(path) for path in evidence_paths],
        "formal": {
            "formal_semantics_id": FORMAL_ID,
            "new_action_ids": [],
            "new_failure_terminals": [],
            "source_diff": [],
            "status": "GO",
        },
        "identities": {
            "manifest_id": MANIFEST_ID,
            "piece_profile_id": PROFILE_ID,
            "policy_registry_id": POLICY_REGISTRY_ID,
        },
        "phase_evidence": phase,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": source_artifacts(commit),
            "commit": commit,
            "tree": source["tree"],
        },
        "status": "PASS",
        "task_ledger": [
            evidence_artifact(FEATURE / "tasks.md"),
            evidence_artifact(FEATURE / "runtime-tasks.md"),
        ],
        "task_ids": ["T030", "T031", "T032", "HR005-013"],
        "unsupported_claims": [
            "AARCH64_WITHOUT_PINNED_RUNNER",
            "ANONYMOUS_OR_PUBLIC_DHT",
            "WAN_PERFORMANCE_OR_BANDWIDTH_REDUCTION",
            "ERASURE_CODING_OR_CDN",
            "HIERARCHICAL_CERTIFICATE_COMPLETION",
            "APPLY_QC_OR_CURRENT_POINTER_COMPLETION",
            "SEMANTIC_COVERAGE_BEYOND_DECLARED_REFINEMENT",
        ],
    }


def fail(error: Exception) -> NoReturn:
    print(
        canonical_json_bytes(
            {"error": str(error), "phase": "005-final-compatibility", "status": "FAIL"}
        ).decode()
    )
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--source-commit")
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    try:
        if arguments.write:
            require(arguments.source_commit is not None, "SOURCE_COMMIT_REQUIRED")
            result = build(arguments.source_commit)
            OUTPUT.write_bytes(canonical_json_bytes(result) + b"\n")
        else:
            require(arguments.check_only, "CHECK_ONLY_REQUIRED")
            raw = OUTPUT.read_bytes()
            result = json.loads(raw.decode())
            require(isinstance(result, dict), "REPORT_ROOT_INVALID")
            source = result.get("source")
            require(isinstance(source, dict), "REPORT_SOURCE_INVALID")
            require(result == build(str(source.get("commit"))), "FINAL_REPORT_DRIFT")
            require(raw == canonical_json_bytes(result) + b"\n", "REPORT_NOT_CANONICAL")
    except (FinalCompatibilityError, OSError, ValueError, json.JSONDecodeError) as error:
        fail(error)
    print(canonical_json_bytes(result).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
