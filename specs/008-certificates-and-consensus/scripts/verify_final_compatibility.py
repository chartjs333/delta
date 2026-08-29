"""Publish or verify the final Constitution 2.1.0 feature-008 decision."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs/008-certificates-and-consensus"
OUTPUT: Final = FEATURE / "evidence/final-compatibility.json"
PREDECESSOR: Final = "2054f31ef0f6750645b924ef337a35d1737c619d"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
EVIDENCE_NAMES: Final = (
    "preflight.json",
    "protocol-contracts.json",
    "native-execution.json",
    "certificate-refinement.json",
    "certificate-ci.json",
)


class CompatibilityError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise CompatibilityError(code)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, check=False)
    require(process.returncode == 0, "GIT_FAILED:" + process.stderr.decode(errors="replace"))
    return process.stdout.replace(b"\r\n", b"\n")


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode().strip()


def checked_ids(document: str, prefix: str, digits: int) -> set[str]:
    return set(
        re.findall(
            rf"^- \[x\] (?:\*\*)?({re.escape(prefix)}\d{{{digits}}})\b", document, re.MULTILINE
        )
    )


def load_evidence(name: str) -> dict[str, Any]:
    path = FEATURE / "evidence" / name
    document = json.loads(path.read_bytes())
    require(document.get("status") == "PASS", "EVIDENCE_NOT_PASS:" + name)
    require(document.get("formal_semantics_id") == FORMAL_ID, "EVIDENCE_FORMAL_ID_DRIFT:" + name)
    require(
        document.get("semantic_completeness_claimed") is False, "SEMANTIC_CLAIM_INVALID:" + name
    )
    return document


def artifact(name: str) -> dict[str, str]:
    path = FEATURE / "evidence" / name
    return {"path": f"evidence/{name}", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def build(source_commit: str) -> dict[str, Any]:
    commit = git_text("rev-parse", f"{source_commit}^{{commit}}")
    require(
        subprocess.run(
            ["git", "merge-base", "--is-ancestor", PREDECESSOR, commit], cwd=ROOT
        ).returncode
        == 0,
        "PREDECESSOR_NOT_ANCESTOR",
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
    tasks = (FEATURE / "tasks.md").read_text(encoding="utf-8")
    runtime_tasks = (FEATURE / "runtime-tasks.md").read_text(encoding="utf-8")
    require(
        checked_ids(tasks, "T", 3) == {f"T{index:03d}" for index in range(54)}, "TASKS_INCOMPLETE"
    )
    require(
        checked_ids(runtime_tasks, "HR008-", 3) == {f"HR008-{index:03d}" for index in range(1, 20)},
        "RUNTIME_TASKS_INCOMPLETE",
    )
    constitution = git_bytes("show", f"{commit}:.specify/memory/constitution.md").decode()
    require("**Version**: 2.1.0" in constitution, "CONSTITUTION_VERSION_INVALID")
    evidence = {name: load_evidence(name) for name in EVIDENCE_NAMES}
    preflight = evidence["preflight.json"]
    require(preflight["formal"]["status"] == "GO", "INHERITED_FORMAL_NOT_GO")
    require(preflight["feature007"]["status"] == "PASS", "FEATURE007_NOT_PASS")
    require(
        preflight["formal_impact"]
        == {
            "classification": "REFINEMENT_ONLY",
            "new_failure_terminals": [],
            "new_formal_action_ids": [],
            "new_protocol_visible_durability_outcomes": [],
            "status": "PASS",
        },
        "FORMAL_IMPACT_DRIFT",
    )
    expected_source = {"commit": commit, "tree": git_text("rev-parse", f"{commit}^{{tree}}")}
    for name in ("native-execution.json", "certificate-refinement.json", "certificate-ci.json"):
        source = evidence[name].get("source")
        require(
            isinstance(source, dict)
            and source.get("commit") == expected_source["commit"]
            and source.get("tree") == expected_source["tree"],
            "EXACT_SOURCE_DIVERGENCE:" + name,
        )
    return {
        "checks": [
            "ALL_T000_T053_AND_HR008_001_HR008_019_COMPLETE",
            "EXACT_FEATURE007_AND_FORMAL_GO_REVERIFIED",
            "NO_FORMAL_SOURCE_DIFF",
            "FULL_NATIVE_CERTIFICATE_CHAIN_AND_DURABLE_VOTES_PASS",
            "EXACT_ROBUST_REDUCE_AND_AGGREGATE_COVERAGE_PASS",
            "DETERMINISTIC_APPLY_APPLYQC_CURRENT_CAS_RECOVERY_PASS",
            "JAVA_TRANSPORT_TIMER_ARTIFACT_ONLY_BOUNDARY_PASS",
            "PRODUCTION_MUTANTS_AND_REFINEMENT_NEGATIVES_PASS",
            "CPP20_CPP23_SANITIZERS_FUZZ_C_ABI_JDK25_JDK26_PASS",
            "OPERATIONS_RECOVERY_ROLLBACK_AND_FEATURE009_BOUNDARY_DOCUMENTED",
            "CONSTITUTION_2_1_0_FINAL_CHECK_PASS",
        ],
        "classification": "REFINEMENT_ONLY",
        "evidence_artifacts": [artifact(name) for name in EVIDENCE_NAMES],
        "formal": {
            "formal_semantics_id": FORMAL_ID,
            "new_action_ids": [],
            "new_failure_terminals": [],
            "source_diff": [],
            "status": "GO",
        },
        "formal_semantics_id": FORMAL_ID,
        "inherited_feature007": preflight["feature007"],
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": expected_source,
        "status": "PASS",
        "task_ids": ["T050", "T051", "T052", "T053", "HR008-019"],
        "unsupported_claims": [
            "FEATURE009_QLORA_8GB_COMPLETION",
            "WAN_LATENCY_OR_BANDWIDTH_TARGET",
            "MODEL_QUALITY_OR_CONVERGENCE",
            "SEMANTIC_COMPLETENESS_BEYOND_DECLARED_REFINEMENT",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--source-commit")
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    require(arguments.check_only != arguments.write, "EXACT_MODE_REQUIRED")
    if arguments.check_only:
        existing = json.loads(OUTPUT.read_bytes())
        source_commit = existing["source"]["commit"]
    else:
        require(arguments.source_commit is not None, "SOURCE_COMMIT_REQUIRED")
        source_commit = arguments.source_commit
    result = build(source_commit)
    encoded = canonical(result)
    if arguments.check_only:
        require(OUTPUT.read_bytes() == encoded, "FINAL_REPORT_DRIFT")
    else:
        OUTPUT.write_bytes(encoded)
    print(encoded.decode())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        CompatibilityError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ) as error:
        print(canonical({"error": str(error), "status": "FAIL"}).decode())
        raise SystemExit(2) from error
