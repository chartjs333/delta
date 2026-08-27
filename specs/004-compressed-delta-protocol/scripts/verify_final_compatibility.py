"""Verify and publish the final feature-004 compatibility decision."""

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
FEATURE: Final = ROOT / "specs" / "004-compressed-delta-protocol"
OUTPUT: Final = FEATURE / "evidence" / "final-compatibility.json"
SCRIPT_DIR: Final = FEATURE / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_refinement_fixtures import canonical_json_bytes  # noqa: E402
from verify_native_execution import EVIDENCE as NATIVE_EVIDENCE  # noqa: E402
from verify_native_execution import verify as verify_native_execution  # noqa: E402
from verify_phase_evidence import verify as verify_phase_evidence  # noqa: E402

PREDECESSOR: Final = "53da4d3c0b236726566fb242fdcae84032b42679"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
PROFILE_ID: Final = "sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61"
CONFIG_ID: Final = "sha256:34bc08c316dfe22efe155ed11b866bcc0daf7ef8c3c7389c56b2f2c707443629"
PROOF_ID: Final = "sha256:993b4d5104810dd26a3159b60cf8fe9afe6154cdcca90d22b577ae1b6d1ac076"
ROOT_ID: Final = "sha256:e80916a8ec7d634b4c3524d873c13144b7760c7552e6788132a75fce5456296d"


class FinalCompatibilityError(RuntimeError):
    pass


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise FinalCompatibilityError(f"{code}: {detail}" if detail else code)


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


def tracked_text(commit: str, path: str) -> str:
    return git_bytes("show", f"{commit}:{path}").decode("utf-8")


def task_ids(text: str, prefix: str) -> set[str]:
    return set(re.findall(rf"^- \[x\] (?:\*\*)?({prefix}\d{{3}})\b", text, flags=re.MULTILINE))


def current_task_ids(path: Path, prefix: str) -> set[str]:
    return task_ids(path.read_text(encoding="utf-8"), prefix)


def source_artifacts(commit: str) -> list[dict[str, str]]:
    changed = git_text("diff", "--name-only", PREDECESSOR, commit).splitlines()
    artifacts = []
    for path in sorted(item for item in changed if item):
        process = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}:{path}"], cwd=ROOT, check=False
        )
        if process.returncode == 0:
            artifacts.append(
                {
                    "path": path,
                    "sha256": hashlib.sha256(git_bytes("show", f"{commit}:{path}")).hexdigest(),
                }
            )
    return artifacts


def evidence_artifact(path: Path) -> dict[str, str]:
    return {
        "path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def build(source_commit: str) -> dict[str, object]:
    phase = verify_phase_evidence()
    native_raw = NATIVE_EVIDENCE.read_bytes()
    native_document = json.loads(native_raw.decode("utf-8"))
    require(isinstance(native_document, dict), "NATIVE_EVIDENCE_INVALID")
    native = verify_native_execution(native_document)
    source = phase["source"]
    require(isinstance(source, dict), "PHASE_SOURCE_INVALID")
    commit = git_text("rev-parse", source_commit)
    require(source.get("commit") == commit, "SOURCE_COMMIT_DIVERGENCE")
    require(native.get("source") == source, "NATIVE_SOURCE_DIVERGENCE")
    require(
        source.get("tree") == git_text("rev-parse", f"{commit}^{{tree}}"), "SOURCE_TREE_INVALID"
    )
    formal_diff = git_text(
        "diff",
        "--name-only",
        PREDECESSOR,
        commit,
        "--",
        "formal/tla",
        "formal/proofs",
        "formal/schemas",
    )
    require(not formal_diff, "FORMAL_SOURCE_DIFF_PRESENT", formal_diff)
    required_source_tasks = {f"T{index:03d}" for index in range(46)}
    source_tasks = task_ids(
        tracked_text(commit, "specs/004-compressed-delta-protocol/tasks.md"), "T"
    )
    require(required_source_tasks.issubset(source_tasks), "SOURCE_TASKS_INCOMPLETE")
    current_tasks = current_task_ids(FEATURE / "tasks.md", "T")
    require(current_tasks == {f"T{index:03d}" for index in range(48)}, "FINAL_TASKS_INCOMPLETE")
    current_runtime = current_task_ids(FEATURE / "runtime-tasks.md", "HR004-")
    require(
        current_runtime == {f"HR004-{index:03d}" for index in range(1, 13)},
        "RUNTIME_TASKS_INCOMPLETE",
    )
    golden = json.loads(
        (ROOT / "delta-protocol/fixtures/004/cross-language/golden-v1.json").read_text(
            encoding="utf-8"
        )
    )
    require(golden["profile"]["content_id"] == PROFILE_ID, "PROFILE_ID_DRIFT")
    require(golden["fixedpoint_config"]["content_id"] == CONFIG_ID, "CONFIG_ID_DRIFT")
    require(golden["proof_instance"]["content_id"] == PROOF_ID, "PROOF_ID_DRIFT")
    require(golden["commitment_root"] == ROOT_ID, "COMMITMENT_ROOT_DRIFT")
    direct = json.loads(
        (ROOT / "delta-protocol/fixtures/004/cross-language/direct-q-100-v1.json").read_text(
            encoding="utf-8"
        )
    )
    evidence_paths = [
        FEATURE / "evidence" / name
        for name in (
            "preflight.json",
            "protocol-contracts.json",
            "protocol-contracts-final.json",
            "native-architecture.json",
            "proof-instances.json",
            "direct-q-refinement.json",
            "native-execution.json",
        )
    ]
    return {
        "checks": [
            "ALL_T000_T047_AND_HR004_001_HR004_012_COMPLETE",
            "EXACT_FEATURE003_AND_FORMAL_GO_REVERIFIED",
            "NO_FORMAL_SOURCE_DIFF",
            "TWO_INDEPENDENT_ENCODERS_BYTE_IDENTICAL",
            "BOUNDED_NATIVE_PARSER_AND_PRODUCTION_MUTANTS_PASS",
            "CONCRETE_INT64_INT128_PROOF_INSTANCES_PASS",
            "DIRECT_Q_100_STATE_EFFECT_WAL_VERSIONED",
            "LEGAL_APPLIED_AND_UNSAFE_REFINEMENT_TRACES_PASS",
            "GCC_CLANG_CPP20_CPP23_JDK25_JDK26_PASS",
            "ASAN_UBSAN_LIBFUZZER_AND_TSAN_PASS",
            "CONSTITUTION_2_1_0_FINAL_CHECK_PASS",
        ],
        "classification": "REFINEMENT_ONLY",
        "constitution": {
            "sha256": hashlib.sha256(
                git_bytes("show", f"{commit}:.specify/memory/constitution.md")
            ).hexdigest(),
            "version": "2.1.0",
        },
        "direct_q_100": direct,
        "evidence_artifacts": [evidence_artifact(path) for path in evidence_paths],
        "formal": {
            "formal_semantics_id": FORMAL_ID,
            "new_action_ids": [],
            "new_failure_terminals": [],
            "source_diff": [],
            "status": "GO",
        },
        "identities": {
            "commitment_root": ROOT_ID,
            "fixedpoint_config_id": CONFIG_ID,
            "profile_id": PROFILE_ID,
            "proof_instance_id": PROOF_ID,
        },
        "native_execution": native,
        "phase_evidence": phase,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": source_artifacts(commit),
            "commit": commit,
            "tree": source["tree"],
        },
        "status": "PASS",
        "task_ids": ["T046", "T047", "HR004-012"],
        "unsupported_claims": [
            "AARCH64_WITHOUT_PINNED_RUNNER",
            "MODEL_QUALITY_BOUND",
            "RESIDUAL_ERROR_FEEDBACK",
            "WAN_OR_TRANSPORT",
            "HIERARCHY_OR_ROBUST_CERTIFICATES",
            "AGGREGATE_ROOT_OR_APPLY_COMPLETION",
        ],
    }


def fail(error: Exception) -> NoReturn:
    print(
        canonical_json_bytes(
            {
                "error": str(error),
                "phase": "004-final-compatibility",
                "status": "FAIL",
            }
        ).decode("utf-8")
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
            result = json.loads(raw.decode("utf-8"))
            require(isinstance(result, dict), "REPORT_ROOT_INVALID")
            source = result.get("source")
            require(isinstance(source, dict), "REPORT_SOURCE_INVALID")
            expected = build(str(source.get("commit")))
            require(result == expected, "FINAL_REPORT_DRIFT")
            require(raw == canonical_json_bytes(result) + b"\n", "REPORT_NOT_CANONICAL")
    except (FinalCompatibilityError, OSError, ValueError, json.JSONDecodeError) as exc:
        fail(exc)
    print(canonical_json_bytes(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
