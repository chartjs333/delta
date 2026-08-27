"""Verify the complete feature-003 exit contract and emit canonical evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "specs" / "003-bft-round-state-machine"
DEFAULT_OUTPUT = FEATURE / "evidence" / "final-compatibility.json"

EXPECTED_FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
EXPECTED_FORMAL_SOURCE = "1e6e0f6f70056161d95933e71494ec390c7c1151"
EXPECTED_FORMAL_REPORT_SHA256 = "b31c54c3372e36baf1f049b2e45326222b8834362d8fdfbac1e323532986dcab"
EXPECTED_PREDECESSOR = "a48d2af86fc7a976cb20b6be28058d22b09cec54"

EVIDENCE_GATES = (
    ("preflight.json", "verify_preflight.py"),
    ("toolchain-locks.json", "verify_native_toolchains.py"),
    ("protocol-contracts.json", "verify_protocol_contracts.py"),
    ("core-architecture.json", "verify_core_architecture.py"),
    ("native-supply-chain.json", "verify_native_supply_chain.py"),
    ("toolchain-execution.json", "verify_toolchain_execution.py"),
    ("core-protocol-execution.json", "verify_core_protocol_execution.py"),
    ("core-arithmetic-execution.json", "verify_core_arithmetic_execution.py"),
    ("core-transition-execution.json", "verify_core_transition_execution.py"),
    ("core-consensus-execution.json", "verify_core_consensus_execution.py"),
    ("core-portability-execution.json", "verify_core_portability_execution.py"),
    ("prepared-100-execution.json", "verify_prepared_100_execution.py"),
    ("runtime-durability-execution.json", "verify_runtime_durability_execution.py"),
    ("abi-ffm-execution.json", "verify_abi_ffm_execution.py"),
    ("native-phase6-execution.json", "verify_native_phase6_execution.py"),
)

NESTED_ONLY_GATES = ("verify_native_refinement.py",)

SOURCE_ARTIFACTS = (
    ".github/workflows/ci.yml",
    ".github/workflows/native-verification.yml",
    ".github/workflows/native.yml",
    ".specify/memory/constitution.md",
    "CMakeLists.txt",
    "Makefile",
    "delta-core-cpp/README.md",
    "delta-ffi/README.md",
    "delta-ffi/include/delta_abi.h",
    "delta-node-java/README.md",
    "delta-node-java/src/test/java/io/deltareduce/node/NativeRuntimeFfmConformance.java",
    "delta-node-java/src/test/java/io/deltareduce/node/RuntimeDescriptorCompatibility.java",
    "delta-protocol/README.md",
    "delta-protocol/fixtures/003/cross-language/core-portability-v1.json",
    "delta-protocol/fixtures/003/cross-language/golden-v1.json",
    "delta-protocol/fixtures/003/cross-language/prepared-100-v1.json",
    "delta-protocol/fixtures/003/invalid/canonical-binary-negative-v1.json",
    "delta-protocol/fixtures/003/valid/protocol-inputs-v1.json",
    "delta-protocol/registry.json",
    "delta-protocol/schemas/003/canonical-binary-v1.md",
    "delta-protocol/schemas/003/delta-abi-v1.json",
    "delta-protocol/schemas/003/hash-domains-v1.json",
    "delta-protocol/schemas/003/protocol-types-v1.json",
    "delta-protocol/schemas/003/registry-v1.json",
    "delta-runtime-cpp/README.md",
    "docs/adr/0000-formal-verification-gate.md",
    "docs/adr/0001-deltareduce-v1.md",
    "docs/adr/0010-hybrid-runtime-boundary.md",
    "specs/003-bft-round-state-machine/README.md",
    "specs/003-bft-round-state-machine/formal-refinement.md",
    "specs/003-bft-round-state-machine/plan.md",
    "specs/003-bft-round-state-machine/runtime-profile.md",
    "specs/003-bft-round-state-machine/runtime-tasks.md",
    "specs/003-bft-round-state-machine/scripts/verify_final_compatibility.py",
    "specs/003-bft-round-state-machine/spec.md",
    "specs/003-bft-round-state-machine/task-map.md",
    "specs/003-bft-round-state-machine/tasks.md",
)

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class FinalCompatibilityError(RuntimeError):
    """Stable fail-closed final compatibility error."""


def reject(code: str, detail: str = "") -> None:
    raise FinalCompatibilityError(f"{code}:{detail}" if detail else code)


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        reject(code, detail)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_bytes(*arguments: str) -> bytes:
    completed = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    if completed.returncode != 0:
        reject("GIT_COMMAND_FAILED", completed.stderr.decode(errors="replace").strip())
    return completed.stdout


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode("utf-8").strip()


def tracked_bytes(path: str, revision: str) -> bytes:
    relative = Path(path)
    require(not relative.is_absolute() and ".." not in relative.parts, "UNSAFE_PATH", path)
    return git_bytes("show", f"{revision}:{path}")


def tracked_text(path: str, revision: str) -> str:
    return tracked_bytes(path, revision).decode("utf-8")


def tracked_json(path: str, revision: str) -> dict[str, Any]:
    try:
        value = json.loads(tracked_text(path, revision))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        reject("JSON_INVALID", f"{path}:{exc}")
    require(isinstance(value, dict), "JSON_ROOT_INVALID", path)
    return value


def artifact(path: str, revision: str) -> dict[str, str]:
    return {"path": path, "sha256": sha256_bytes(tracked_bytes(path, revision))}


def require_ancestor(ancestor: str, descendant: str, code: str) -> None:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    require(completed.returncode == 0, code)


def verify_formal_binding(source_commit: str) -> dict[str, Any]:
    report_path = "formal/reports/formal-verification-report.json"
    report_raw = tracked_bytes(report_path, source_commit)
    require(sha256_bytes(report_raw) == EXPECTED_FORMAL_REPORT_SHA256, "FORMAL_REPORT_HASH_DRIFT")
    report = json.loads(report_raw.decode("utf-8"))
    require(
        report.get("decision") == "GO"
        and report.get("decision_reasons") == []
        and report.get("formal_semantics_id") == EXPECTED_FORMAL_ID
        and report.get("source_tree", {}).get("commit") == EXPECTED_FORMAL_SOURCE,
        "FORMAL_REPORT_NOT_EXACT_GO",
    )
    semantics = tracked_json("formal/reports/formal-semantics.json", source_commit)
    declared = semantics.get("semantic_artifacts")
    require(isinstance(declared, list) and len(declared) == 24, "FORMAL_ARTIFACT_SET_INVALID")
    require(
        semantics.get("formal_semantics_id") == EXPECTED_FORMAL_ID,
        "FORMAL_SEMANTICS_REPORT_DRIFT",
    )
    diff = git_text(
        "diff",
        "--name-only",
        EXPECTED_PREDECESSOR,
        source_commit,
        "--",
        "formal/tla",
        "formal/proofs",
        "formal/schemas",
    )
    require(not diff, "FORMAL_SOURCE_DIFF_PRESENT", diff)
    return {
        "artifact_count": 24,
        "decision": "GO",
        "report_sha256": EXPECTED_FORMAL_REPORT_SHA256,
        "source_commit": EXPECTED_FORMAL_SOURCE,
    }


def verify_registered_record(record: object, revision: str) -> None:
    require(isinstance(record, dict), "REGISTRY_RECORD_INVALID")
    require(set(record) == {"id", "path", "sha256"}, "REGISTRY_RECORD_FIELDS_INVALID")
    path = record.get("path")
    digest = record.get("sha256")
    require(isinstance(path, str) and isinstance(digest, str), "REGISTRY_RECORD_TYPES_INVALID")
    require(
        sha256_bytes(tracked_bytes(f"delta-protocol/{path}", revision)) == digest,
        "REGISTRY_HASH_MISMATCH",
        path,
    )


def verify_protocol_and_abi(revision: str) -> dict[str, Any]:
    registry = tracked_json("delta-protocol/registry.json", revision)
    require(registry.get("formal_semantics_id") == EXPECTED_FORMAL_ID, "REGISTRY_FORMAL_ID_DRIFT")
    for group in ("extensions", "fixtures", "schemas"):
        records = registry.get(group)
        require(isinstance(records, list) and records, "REGISTRY_GROUP_INVALID", group)
        for record in records:
            verify_registered_record(record, revision)
    verify_registered_record(registry.get("action_registry"), revision)

    feature_registry = tracked_json("delta-protocol/schemas/003/registry-v1.json", revision)
    require(
        feature_registry.get("registry_version") == "003.1.0"
        and feature_registry.get("encoding_id") == "delta-canonical-binary-v1"
        and feature_registry.get("formal_semantics_id") == EXPECTED_FORMAL_ID,
        "FEATURE003_REGISTRY_DRIFT",
    )
    records = feature_registry.get("artifacts")
    require(isinstance(records, list) and len(records) == 3, "FEATURE003_ARTIFACT_SET_INVALID")
    for record in records:
        verify_registered_record(record, revision)

    abi = tracked_json("delta-protocol/schemas/003/delta-abi-v1.json", revision)
    header = tracked_text("delta-ffi/include/delta_abi.h", revision)
    require(
        abi.get("abi_major") == 1
        and abi.get("abi_minor") == 0
        and abi.get("protocol_version") == "003.1.0"
        and abi.get("schema_version") == "1.0.0"
        and abi.get("runtime_profile") == "embedded-ffm"
        and abi.get("formal_semantics_id") == EXPECTED_FORMAL_ID
        and abi.get("semantic_completeness_claimed") is False,
        "ABI_DESCRIPTOR_DRIFT",
    )
    for fragment in (
        "#define DELTA_ABI_MAJOR UINT16_C(1)",
        "#define DELTA_ABI_MINOR UINT16_C(0)",
        '#define DELTA_PROTOCOL_VERSION "003.1.0"',
        '#define DELTA_SCHEMA_VERSION "1.0.0"',
        '#define DELTA_RUNTIME_PROFILE "embedded-ffm"',
        EXPECTED_FORMAL_ID,
        "delta_runtime_submit_borrowed",
        "delta_runtime_submit_copy",
        "delta_runtime_release",
    ):
        require(fragment in header, "ABI_HEADER_DESCRIPTOR_MISMATCH", fragment)
    java = tracked_text(
        "delta-node-java/src/test/java/io/deltareduce/node/NativeRuntimeFfmConformance.java",
        revision,
    )
    for fragment in (
        "delta_runtime_descriptor",
        "delta_runtime_submit_borrowed",
        "delta_runtime_submit_copy",
        "delta_runtime_snapshot",
        "delta_runtime_release",
    ):
        require(fragment in java, "JAVA_FFM_DESCRIPTOR_DRIFT", fragment)
    return {
        "feature003_fixture_count": len(
            [item for item in registry["fixtures"] if str(item.get("id", "")).startswith("BFT003-")]
        ),
        "feature003_registry_sha256": sha256_bytes(
            tracked_bytes("delta-protocol/schemas/003/registry-v1.json", revision)
        ),
        "root_registry_sha256": sha256_bytes(
            tracked_bytes("delta-protocol/registry.json", revision)
        ),
    }


def verify_documentation(revision: str) -> None:
    guide = tracked_text("specs/003-bft-round-state-machine/README.md", revision)
    component_docs = "\n".join(
        tracked_text(path, revision)
        for path in (
            "delta-core-cpp/README.md",
            "delta-runtime-cpp/README.md",
            "delta-ffi/README.md",
            "delta-node-java/README.md",
            "delta-protocol/README.md",
        )
    )
    for fragment in (
        "WAL append -> durability barrier -> state commit -> effect",
        "Borrowed ABI inputs",
        "semantic completeness",
        "production quantization",
        "protobuf/gRPC/Netty/TLS",
        "full certificate hierarchy",
        EXPECTED_FORMAL_ID,
    ):
        require(fragment in guide, "FINAL_DOCUMENTATION_INCOMPLETE", fragment)
    for fragment in (
        "persist-before-expose",
        "delta_runtime_submit_borrowed",
        "JDK 25",
        "prepared-100-v1.json",
    ):
        require(fragment in component_docs, "COMPONENT_DOCUMENTATION_INCOMPLETE", fragment)


def verify_completed_scope(revision: str) -> dict[str, int]:
    tasks = tracked_text("specs/003-bft-round-state-machine/tasks.md", revision)
    expected_tasks = [f"T{index:03d}" for index in range(53)]
    completed_tasks = re.findall(r"^- \[x\] (T\d{3})\b", tasks, re.MULTILINE)
    require(completed_tasks == expected_tasks, "SEMANTIC_TASK_SET_INCOMPLETE")

    runtime_tasks = tracked_text("specs/003-bft-round-state-machine/runtime-tasks.md", revision)
    expected_runtime = [f"HR003-{index:03d}" for index in range(1, 25)]
    completed_runtime = re.findall(r"^- \[x\] \*\*(HR003-\d{3})\*\*", runtime_tasks, re.MULTILINE)
    require(completed_runtime == expected_runtime, "RUNTIME_TASK_SET_INCOMPLETE")

    task_map = tracked_text("specs/003-bft-round-state-machine/task-map.md", revision)
    require(
        "T048" in task_map
        and "T052 | HR003-003, HR003-024" in task_map
        and "Python fixture/evidence helper cannot substitute" in task_map,
        "NORMATIVE_TASK_MAP_DRIFT",
    )
    return {"HR003": len(completed_runtime), "T": len(completed_tasks)}


def verify_constitution(revision: str) -> list[str]:
    constitution = tracked_text(".specify/memory/constitution.md", revision)
    require("**Version**: 2.1.0" in constitution, "CONSTITUTION_VERSION_DRIFT")
    plan = tracked_text("specs/003-bft-round-state-machine/plan.md", revision)
    require("**Constitution**: 2.1.0" in plan, "PLAN_CONSTITUTION_BINDING_DRIFT")
    return [
        "I_IV_FIXED_DOMAIN_TICKET_AND_PREPARED_INPUT_BINDING",
        "II_EXACT_FORMAL_GO_AND_NO_FORMAL_SOURCE_DIFF",
        "III_QUORUM_REPLICATED_DETERMINISTIC_STATE",
        "V_CHECKED_INTEGER_ONLY_PREPARED_REDUCE",
        "VI_INPUT_FREEZE_BEFORE_SEED_AND_PARENT_BINDING",
        "VII_APPLY_REMAINS_FORMAL_AND_LATER_FEATURE_SCOPE",
        "VIII_NO_LOCAL_OR_PARTIAL_DISTRIBUTION_PATH",
        "IX_CANONICAL_BOUNDED_UNTRUSTED_BYTE_PARSING",
        "X_DURABLE_RECOVERY_VIEW_CHANGE_AND_ABORT",
        "XI_DETERMINISTIC_EXIT_EVIDENCE_AND_ROLLBACK_PATH",
        "XII_CANONICAL_REPLACEABLE_NATIVE_ABI",
    ]


def verify_evidence(revision: str, run_nested: bool) -> tuple[list[dict[str, str]], set[str]]:
    artifacts: list[dict[str, str]] = []
    covered: set[str] = set()
    for evidence_name, script_name in EVIDENCE_GATES:
        evidence_path = f"specs/003-bft-round-state-machine/evidence/{evidence_name}"
        document = tracked_json(evidence_path, revision)
        require(document.get("status") == "PASS", "EVIDENCE_NOT_PASS", evidence_name)
        require(
            document.get("formal_semantics_id") == EXPECTED_FORMAL_ID,
            "EVIDENCE_FORMAL_ID_DRIFT",
            evidence_name,
        )
        require(
            document.get("semantic_completeness_claimed") is False,
            "EVIDENCE_SEMANTIC_CLAIM_INVALID",
            evidence_name,
        )
        task_ids = document.get("task_ids")
        require(isinstance(task_ids, list), "EVIDENCE_TASK_IDS_INVALID", evidence_name)
        covered.update(item for item in task_ids if isinstance(item, str))
        source = document.get("source") or document.get("source_tree")
        require(isinstance(source, dict), "EVIDENCE_SOURCE_INVALID", evidence_name)
        source_commit = source.get("commit")
        require(
            isinstance(source_commit, str)
            and re.fullmatch(r"[0-9a-f]{40}", source_commit) is not None,
            "EVIDENCE_SOURCE_COMMIT_INVALID",
            evidence_name,
        )
        require_ancestor(source_commit, revision, "EVIDENCE_SOURCE_NOT_ANCESTOR")
        artifacts.append(artifact(evidence_path, revision))

        if run_nested:
            script = FEATURE / "scripts" / script_name
            completed = subprocess.run(
                [sys.executable, str(script), "--check-only"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            require(completed.returncode == 0, "NESTED_EVIDENCE_GATE_FAILED", script_name)

    expected_tasks = {f"T{index:03d}" for index in range(49)}
    expected_runtime = {f"HR003-{index:03d}" for index in range(1, 24)}
    require(expected_tasks <= covered, "EVIDENCE_SEMANTIC_COVERAGE_INCOMPLETE")
    require(expected_runtime <= covered, "EVIDENCE_RUNTIME_COVERAGE_INCOMPLETE")
    if run_nested:
        for script_name in NESTED_ONLY_GATES:
            completed = subprocess.run(
                [sys.executable, str(FEATURE / "scripts" / script_name), "--check-only"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
            require(completed.returncode == 0, "NESTED_EVIDENCE_GATE_FAILED", script_name)
    return artifacts, covered


def verify(source_commit: str, *, run_nested: bool = True) -> dict[str, Any]:
    require_ancestor(EXPECTED_PREDECESSOR, source_commit, "PREDECESSOR_NOT_ANCESTOR")
    require_ancestor(source_commit, "HEAD", "FINAL_SOURCE_NOT_ANCESTOR")
    evidence, covered = verify_evidence(source_commit, run_nested)
    native = tracked_json(
        "specs/003-bft-round-state-machine/evidence/native-phase6-execution.json",
        source_commit,
    )
    abi = tracked_json(
        "specs/003-bft-round-state-machine/evidence/abi-ffm-execution.json",
        source_commit,
    )
    verify_documentation(source_commit)
    return {
        "analysis_kind": "FINAL_CONSTITUTION_COMPATIBILITY_AND_CROSS_ARTIFACT",
        "checks": [
            "ALL_T000_T052_AND_HR003_001_HR003_024_COMPLETE",
            "ALL_PHASE_EVIDENCE_REPRODUCED_FAIL_CLOSED",
            "FORMAL_GO_REVERIFIED_AND_NO_FORMAL_SOURCE_DIFF",
            "SCHEMA_REGISTRY_FIXTURE_HASHES_EXACT",
            "ABI_SCHEMA_HEADER_AND_JAVA_DESCRIPTOR_CONSISTENT",
            "GCC_CLANG_CPP20_CPP23_AND_JDK25_JDK26_EVIDENCE_EXACT",
            "ASAN_UBSAN_SEPARATE_TSAN_AND_FUZZ_EVIDENCE_EXACT",
            "FOUR_RUNTIME_NATIVE_EXIT_AND_RESTART_IDENTITY_EXACT",
            "LEGAL_REFINEMENT_AND_PRODUCTION_MUTANT_RESULTS_EXACT",
            "DOCUMENTED_LATER_FEATURE_BOUNDARIES_EXPLICIT",
            "CONSTITUTION_2_1_0_FINAL_CHECK_PASS",
        ],
        "classification": "REFINEMENT_ONLY",
        "constitution": {
            "checks": verify_constitution(source_commit),
            "sha256": sha256_bytes(tracked_bytes(".specify/memory/constitution.md", source_commit)),
            "version": "2.1.0",
        },
        "covered_prerequisite_task_ids": sorted(covered),
        "errors": [],
        "evidence_artifacts": evidence,
        "execution_runs": {
            "abi_ffm": abi["run"],
            "native_compiler": native["runs"]["compiler"],
            "native_sanitizer": native["runs"]["sanitizer"],
        },
        "formal": verify_formal_binding(source_commit),
        "formal_semantics_id": EXPECTED_FORMAL_ID,
        "native_exit": native["exit_result"],
        "new_failure_terminals": [],
        "new_formal_action_ids": [],
        "new_protocol_visible_durability_outcomes": [],
        "protocol": verify_protocol_and_abi(source_commit),
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": [artifact(path, source_commit) for path in SOURCE_ARTIFACTS],
            "commit": source_commit,
            "tree": git_text("rev-parse", f"{source_commit}^{{tree}}"),
        },
        "status": "PASS",
        "task_counts": verify_completed_scope(source_commit),
        "task_ids": ["T049", "T050", "T051", "T052", "HR003-024"],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args()


def source_for_run(output: Path, check_only: bool) -> str:
    if not check_only:
        require(
            not git_text("status", "--porcelain", "--untracked-files=all"), "SOURCE_TREE_NOT_CLEAN"
        )
        return git_text("rev-parse", "HEAD")
    require(output.is_file(), "FINAL_COMPATIBILITY_EVIDENCE_MISSING")
    try:
        document = json.loads(output.read_text(encoding="utf-8"))
        source = document["source"]["commit"]
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError) as exc:
        reject("FINAL_COMPATIBILITY_EVIDENCE_INVALID", str(exc))
    require(
        isinstance(source, str) and re.fullmatch(r"[0-9a-f]{40}", source) is not None,
        "FINAL_SOURCE_INVALID",
    )
    return source


def main() -> int:
    args = parse_args()
    output = args.output.resolve()
    try:
        source_commit = source_for_run(output, args.check_only)
        result = verify(source_commit)
        encoded = canonical_json_bytes(result)
        if args.check_only:
            require(output.read_bytes() == encoded, "FINAL_COMPATIBILITY_EVIDENCE_STALE")
        else:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_bytes(encoded)
    except (
        FinalCompatibilityError,
        OSError,
        UnicodeDecodeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        failure = {
            "error_code": str(exc),
            "formal_semantics_id": EXPECTED_FORMAL_ID,
            "schema_version": "1.0.0",
            "status": "FAIL",
        }
        print(canonical_json_bytes(failure).decode("utf-8"))
        return 2
    print(encoded.decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
