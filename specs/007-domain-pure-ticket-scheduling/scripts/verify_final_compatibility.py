"""Publish the final Constitution 2.1.0 compatibility decision for feature 007."""

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
FEATURE: Final = ROOT / "specs" / "007-domain-pure-ticket-scheduling"
OUTPUT: Final = FEATURE / "evidence" / "final-compatibility.json"
SOURCE_PREDECESSOR: Final = "b3475963cd98213c2161729364b973829bf52253"
MERGED_PREDECESSOR: Final = "827d3393acf347c9b45eabdb3d652bdc98bcfe75"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
SOURCE_ARTIFACTS: Final = (
    ".github/workflows/ci.yml",
    ".github/workflows/scheduling.yml",
    "Makefile",
    "delta-node-java/README.md",
    "docs/scheduling-operations.md",
    "specs/007-domain-pure-ticket-scheduling/checklists/hybrid-runtime.md",
    "specs/007-domain-pure-ticket-scheduling/checklists/requirements.md",
    "specs/007-domain-pure-ticket-scheduling/scripts/capture_scheduling_ci.py",
    "specs/007-domain-pure-ticket-scheduling/scripts/verify_final_compatibility.py",
)
EVIDENCE_NAMES: Final = (
    "preflight.json",
    "protocol-contracts.json",
    "native-planner.json",
    "native-admission.json",
    "native-lifecycle.json",
    "scheduling-boundary.json",
    "scheduling-refinement.json",
    "scheduling-ci.json",
)

sys.path.insert(0, str(FEATURE / "scripts"))
from capture_scheduling_ci import verify as verify_ci  # noqa: E402
from verify_scheduling_refinement import verify_evidence as verify_refinement  # noqa: E402


class CompatibilityError(RuntimeError):
    """Stable fail-closed feature-007 final compatibility error."""


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise CompatibilityError(f"{code}:{detail}" if detail else code)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    require(
        process.returncode == 0,
        "GIT_COMMAND_FAILED",
        process.stderr.decode(errors="replace").strip(),
    )
    return process.stdout.replace(b"\r\n", b"\n")


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode().strip()


def source_bytes(commit: str, path: str) -> bytes:
    return git_bytes("show", f"{commit}:{path}")


def checked_ids(path: Path, prefix: str) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return set(re.findall(rf"^- \[x\] (?:\*\*)?({re.escape(prefix)}\d{{3}})\b", text, re.MULTILINE))


def artifact(path: Path) -> dict[str, str]:
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def load_evidence(name: str) -> dict[str, Any]:
    path = FEATURE / "evidence" / name
    raw = path.read_bytes()
    document = json.loads(raw)
    require(isinstance(document, dict), "EVIDENCE_ROOT_INVALID", name)
    require(document.get("status") == "PASS", "EVIDENCE_STATUS_INVALID", name)
    require(document.get("formal_semantics_id") == FORMAL_ID, "EVIDENCE_FORMAL_ID_INVALID", name)
    require(
        document.get("semantic_completeness_claimed") is False,
        "EVIDENCE_SEMANTIC_CLAIM_INVALID",
        name,
    )
    return document


def validate_source(commit: str) -> list[dict[str, str]]:
    require(git_text("rev-parse", f"{commit}^{{commit}}") == commit, "SOURCE_COMMIT_INVALID")
    require(git_text("rev-parse", f"{commit}^") == SOURCE_PREDECESSOR, "SOURCE_PARENT_INVALID")
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT, check=False
        ).returncode
        == 0,
        "SOURCE_NOT_ANCESTOR",
    )
    changed = set(git_text("diff", "--name-only", SOURCE_PREDECESSOR, commit).splitlines())
    require(changed == set(SOURCE_ARTIFACTS), "SOURCE_SCOPE_INVALID", ",".join(sorted(changed)))
    formal_diff = git_text(
        "diff",
        "--name-only",
        MERGED_PREDECESSOR,
        commit,
        "--",
        "formal/tla",
        "formal/proofs",
        "formal/schemas",
    )
    require(not formal_diff, "FORMAL_SOURCE_DIFF_PRESENT", formal_diff)
    operations = source_bytes(commit, "docs/scheduling-operations.md").decode()
    for marker in (
        "## Startup and admission",
        "## Runtime signals",
        "## Failure and recovery",
        "## Rollback",
        "## Feature-008 boundary",
        "Do not restore legacy adaptive `H`",
    ):
        require(marker in operations, "OPERATIONS_DOCUMENTATION_INCOMPLETE", marker)
    java_readme = source_bytes(commit, "delta-node-java/README.md").decode()
    require("Feature 007 adds `NativeScheduling`" in java_readme, "JAVA_OPERATIONS_DOC_MISSING")
    return [
        {"path": path, "sha256": hashlib.sha256(source_bytes(commit, path)).hexdigest()}
        for path in SOURCE_ARTIFACTS
    ]


def build(source_commit: str, trace_root: Path) -> dict[str, Any]:
    commit = git_text("rev-parse", source_commit)
    source_artifacts = validate_source(commit)
    ci = verify_ci()
    refinement = verify_refinement(trace_root)
    require(
        ci.get("source") == {"commit": commit, "tree": git_text("rev-parse", f"{commit}^{{tree}}")},
        "CI_SOURCE_DIVERGENCE",
    )
    require(
        checked_ids(FEATURE / "tasks.md", "T") == {f"T{index:03d}" for index in range(34)},
        "TASKS_INCOMPLETE",
    )
    require(
        checked_ids(FEATURE / "runtime-tasks.md", "HR007-")
        == {f"HR007-{index:03d}" for index in range(1, 13)},
        "RUNTIME_TASKS_INCOMPLETE",
    )
    constitution = (ROOT / ".specify" / "memory" / "constitution.md").read_text(encoding="utf-8")
    require("**Version**: 2.1.0" in constitution, "CONSTITUTION_VERSION_INVALID")
    evidence = {name: load_evidence(name) for name in EVIDENCE_NAMES}
    preflight = evidence["preflight.json"]
    require(preflight.get("formal", {}).get("status") == "GO", "INHERITED_FORMAL_NOT_GO")
    require(preflight.get("feature006", {}).get("status") == "PASS", "FEATURE006_CHAIN_INVALID")
    require(
        preflight.get("formal_impact")
        == {
            "classification": "REFINEMENT_ONLY",
            "new_failure_terminals": [],
            "new_formal_action_ids": [],
            "new_protocol_visible_durability_outcomes": [],
            "status": "PASS",
        },
        "FORMAL_IMPACT_DRIFT",
    )
    require(
        refinement.get("source", {}).get("commit") == "ea73c126c38e33f91285dadabd20d4bdd695aca2",
        "REFINEMENT_SOURCE_DRIFT",
    )
    return {
        "checks": [
            "ALL_T000_T033_AND_HR007_001_HR007_012_COMPLETE",
            "EXACT_FEATURE006_AND_FORMAL_GO_REVERIFIED",
            "NO_FORMAL_SOURCE_DIFF",
            "FIXED_DOMAIN_PURE_TICKET_PLAN_AND_EXACT_INFEASIBILITY_PASS",
            "CAPABILITY_AFFECTS_ADMISSION_AND_OWNERSHIP_ONLY",
            "DURABLE_LEASE_TIMER_REASSIGN_COMMIT_RECOVERY_PASS",
            "PRODUCTION_MUTANTS_AND_ILLEGAL_REFINEMENT_TRACES_REJECTED",
            "FIFTY_WORKER_CPP20_CPP23_DETERMINISM_PASS",
            "BORROWED_COPY_C_ABI_AND_JDK25_JDK26_TRANSPORT_PASS",
            "GCC_CLANG_SANITIZER_FUZZ_AND_FULL_PYTHON_MATRIX_PASS",
            "OPERATIONS_ROLLBACK_OBSERVABILITY_AND_FEATURE008_BOUNDARY_DOCUMENTED",
            "CONSTITUTION_2_1_0_FINAL_CHECK_PASS",
        ],
        "classification": "REFINEMENT_ONLY",
        "evidence_artifacts": [artifact(FEATURE / "evidence" / name) for name in EVIDENCE_NAMES],
        "formal": {
            "formal_semantics_id": FORMAL_ID,
            "new_action_ids": [],
            "new_failure_terminals": [],
            "source_diff": [],
            "status": "GO",
        },
        "inherited_feature006": preflight["feature006"],
        "refinement": refinement,
        "scheduling_ci": ci,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": source_artifacts,
            "commit": commit,
            "tree": git_text("rev-parse", f"{commit}^{{tree}}"),
        },
        "status": "PASS",
        "task_ids": ["T030", "T031", "T032", "T033", "HR007-012"],
        "unsupported_claims": [
            "WAN_LATENCY_OR_BANDWIDTH_TARGET",
            "FEATURE008_CERTIFICATE_CHAIN_OR_SEED_COMPLETION",
            "APPLY_QC_OR_CURRENT_POINTER_COMPLETION",
            "DEVICE_PERFORMANCE_AS_MATHEMATICAL_WEIGHT",
            "SEMANTIC_COVERAGE_BEYOND_DECLARED_REFINEMENT",
        ],
    }


def fail(error: Exception) -> NoReturn:
    print(
        canonical_json_bytes(
            {"error": str(error), "phase": "007-final-compatibility", "status": "FAIL"}
        ).decode()
    )
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
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
            OUTPUT.write_bytes(canonical_json_bytes(result))
        else:
            require(arguments.check_only, "CHECK_ONLY_REQUIRED")
            raw = OUTPUT.read_bytes()
            result = json.loads(raw)
            require(isinstance(result, dict), "REPORT_ROOT_INVALID")
            source = result.get("source")
            require(isinstance(source, dict), "REPORT_SOURCE_INVALID")
            require(result == build(str(source.get("commit")), trace_root), "REPORT_DRIFT")
            require(raw == canonical_json_bytes(result), "REPORT_NOT_CANONICAL")
    except (
        CompatibilityError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ) as error:
        fail(error)
    print(canonical_json_bytes(result).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
