"""Publish the final Constitution 2.1.0 compatibility decision for feature 006."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Final, NoReturn

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "006-regional-hierarchical-reduce"
OUTPUT: Final = FEATURE / "evidence" / "final-compatibility.json"
PREDECESSOR: Final = "5e887bd"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"

sys.path.insert(0, str(FEATURE / "scripts"))
from capture_hierarchy_ci import verify as verify_ci  # noqa: E402
from verify_native_hierarchy import verify_evidence as verify_native  # noqa: E402


class CompatibilityError(RuntimeError):
    pass


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise CompatibilityError(f"{code}:{detail}" if detail else code)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def git_text(*arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments], cwd=ROOT, check=False, capture_output=True, text=True
    )
    require(process.returncode == 0, "GIT_COMMAND_FAILED", process.stderr.strip())
    return process.stdout.strip()


def checked_ids(path: Path, prefix: str) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return set(re.findall(rf"^- \[x\] (?:\*\*)?({re.escape(prefix)}\d{{3}})\b", text, re.MULTILINE))


def artifact(path: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def build(source_commit: str, trace_root: Path) -> dict[str, Any]:
    native = verify_native(trace_root)
    ci = verify_ci()
    source = native.get("source")
    require(isinstance(source, dict), "NATIVE_SOURCE_INVALID")
    commit = git_text("rev-parse", source_commit)
    require(source.get("commit") == commit, "SOURCE_COMMIT_DIVERGENCE")
    require(
        ci.get("source") == {"commit": commit, "tree": source.get("tree")}, "CI_SOURCE_DIVERGENCE"
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
    require(
        checked_ids(FEATURE / "tasks.md", "T") == {f"T{index:03d}" for index in range(31)},
        "TASKS_INCOMPLETE",
    )
    require(
        checked_ids(FEATURE / "runtime-tasks.md", "HR006-")
        == {f"HR006-{index:03d}" for index in range(1, 12)},
        "RUNTIME_TASKS_INCOMPLETE",
    )
    constitution = (ROOT / ".specify" / "memory" / "constitution.md").read_text(encoding="utf-8")
    require("**Version**: 2.1.0" in constitution, "CONSTITUTION_VERSION_INVALID")
    evidence_paths = [
        FEATURE / "evidence" / "preflight.json",
        FEATURE / "evidence" / "protocol-contracts.json",
        FEATURE / "evidence" / "native-topology.json",
        FEATURE / "evidence" / "native-hierarchy.json",
        FEATURE / "evidence" / "hierarchy-ci.json",
    ]
    return {
        "checks": [
            "ALL_T000_T030_AND_HR006_001_HR006_011_COMPLETE",
            "EXACT_FEATURE005_AND_FORMAL_GO_REVERIFIED",
            "NO_FORMAL_SOURCE_DIFF",
            "PO_H1_H2_A1_A2_A3_INSTANCE_BOUND",
            "THREE_UNEQUAL_REGIONS_TWO_DOMAINS_TWO_SHARDS_FLAT_EQUIVALENT",
            "REGIONAL_GLOBAL_QC_DURABILITY_AND_RECOVERY_PASS",
            "PRODUCTION_MUTANTS_AND_ILLEGAL_REFINEMENT_TRACES_REJECTED",
            "BORROWED_COPY_FFI_AND_JAVA_ROUTING_CONFORMANCE_PASS",
            "GCC_CPP20_CPP23_CLANG_SANITIZER_JDK25_JDK26_PASS",
            "PARTIAL_MEDIA_DENYLIST_AND_FEATURE008_BOUNDARY_PASS",
            "CONSTITUTION_2_1_0_FINAL_CHECK_PASS",
        ],
        "classification": "REFINEMENT_ONLY",
        "evidence_artifacts": [artifact(path) for path in evidence_paths],
        "formal": {
            "formal_semantics_id": FORMAL_ID,
            "new_action_ids": [],
            "new_failure_terminals": [],
            "source_diff": [],
            "status": "GO",
        },
        "hierarchy_ci": ci,
        "native_hierarchy": native,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": source,
        "status": "PASS",
        "task_ids": ["T030", "HR006-011"],
        "unsupported_claims": [
            "WAN_LATENCY_OR_BANDWIDTH_REDUCTION",
            "FEATURE008_CERTIFICATE_CHAIN_COMPLETION",
            "APPLY_QC_OR_CURRENT_POINTER_COMPLETION",
            "CRASH_ISOLATION_IN_EMBEDDED_FFM_MODE",
            "SEMANTIC_COVERAGE_BEYOND_DECLARED_REFINEMENT",
        ],
    }


def fail(error: Exception) -> NoReturn:
    print(
        canonical_json_bytes(
            {"error": str(error), "phase": "006-final-compatibility", "status": "FAIL"}
        ).decode()
    )
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--source-commit")
    parser.add_argument("--trace-dir", type=Path, required=True)
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    try:
        trace_root = arguments.trace_dir.resolve()
        if arguments.write:
            require(arguments.source_commit is not None, "SOURCE_COMMIT_REQUIRED")
            result = build(arguments.source_commit, trace_root)
            OUTPUT.write_bytes(canonical_json_bytes(result) + b"\n")
        else:
            require(arguments.check_only, "CHECK_ONLY_REQUIRED")
            raw = OUTPUT.read_bytes()
            result = json.loads(raw.decode())
            require(isinstance(result, dict), "REPORT_ROOT_INVALID")
            source = result.get("source")
            require(isinstance(source, dict), "REPORT_SOURCE_INVALID")
            require(result == build(str(source.get("commit")), trace_root), "REPORT_DRIFT")
            require(raw == canonical_json_bytes(result) + b"\n", "REPORT_NOT_CANONICAL")
    except (CompatibilityError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        fail(error)
    print(canonical_json_bytes(result).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
