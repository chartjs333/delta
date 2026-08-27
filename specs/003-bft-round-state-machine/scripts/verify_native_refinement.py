"""Validate runtime-derived traces and real production-mutant counterexamples."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
FEATURE = ROOT / "specs" / "003-bft-round-state-machine"
TRACE_ROOT = FEATURE / "evidence" / "traces"
MUTANT_ROOT = FEATURE / "evidence" / "mutants"
EXPECTED_FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
EXPECTED_LEGAL = {
    "native-certified-abort.json": ("TRACE-NATIVE-003-CERTIFIED-ABORT", "ABORTED"),
    "native-crash-recovery.json": ("TRACE-NATIVE-003-CRASH-RECOVERY", "IN_PROGRESS"),
    "native-normal.json": ("TRACE-NATIVE-003-NORMAL", "IN_PROGRESS"),
    "native-view-change.json": ("TRACE-NATIVE-003-VIEW-CHANGE", "IN_PROGRESS"),
}
EXPECTED_MUTANTS = {
    "native-effect-before-durability.json": "PARTIAL_OR_UNCERTIFIED_PUBLICATION",
    "native-view-without-qc.json": "QC_QUORUM_MISSING",
}

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class NativeRefinementError(RuntimeError):
    """Stable fail-closed native refinement error."""


def reject(code: str, detail: str = "") -> None:
    raise NativeRefinementError(f"{code}:{detail}" if detail else code)


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        reject(code, detail)


def git_archive() -> bytes:
    completed = subprocess.run(
        ["git", "archive", "--format=tar", "HEAD", "formal", "specs/000-formal-tla-spec"],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    require(completed.returncode == 0, "FORMAL_ARCHIVE_FAILED")
    return completed.stdout


def materialize_formal_tree(destination: Path) -> None:
    with tarfile.open(fileobj=io.BytesIO(git_archive()), mode="r:") as archive:
        for member in archive.getmembers():
            target = (destination / member.name).resolve()
            require(target.is_relative_to(destination.resolve()), "FORMAL_ARCHIVE_PATH_INVALID")
        archive.extractall(destination, filter="data")


def load_canonical(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    value = json.loads(raw.decode())
    require(isinstance(value, dict), "TRACE_ROOT_INVALID", path.name)
    require(
        raw in {canonical_json_bytes(value), canonical_json_bytes(value) + b"\n"},
        "TRACE_NOT_CANONICAL",
        path.name,
    )
    require(
        value.get("formal_semantics_id") == EXPECTED_FORMAL_ID,
        "TRACE_FORMAL_ID_INVALID",
        path.name,
    )
    return value


def run_accepted_checker(checker: Path, trace: Path) -> tuple[int, dict[str, Any]]:
    completed = subprocess.run(
        [sys.executable, str(checker), str(trace)],
        cwd=checker.parents[2],
        check=False,
        capture_output=True,
        text=True,
    )
    output = completed.stdout.strip().splitlines()
    require(bool(output), "REFINEMENT_CHECKER_OUTPUT_MISSING", trace.name)
    try:
        result = json.loads(output[-1])
    except json.JSONDecodeError as error:
        reject("REFINEMENT_CHECKER_OUTPUT_INVALID", f"{trace.name}:{error}")
    require(isinstance(result, dict), "REFINEMENT_CHECKER_ROOT_INVALID", trace.name)
    return completed.returncode, result


def verify_all() -> dict[str, Any]:
    require_fragments = {
        ROOT / "delta-core-cpp/src/transition.cpp": (
            "DELTA_NATIVE_MUTANT_ALLOW_VIEW_JUMP",
            "command.view == state.view + 1U",
        ),
        ROOT / "delta-runtime-cpp/src/runtime.cpp": (
            "DELTA_NATIVE_MUTANT_EXPOSE_BEFORE_DURABILITY",
            "wal_.append_and_sync(entry, false)",
        ),
        ROOT / "delta-runtime-cpp/tests/trace_exporter.cpp": (
            "export_normal",
            "export_view_change",
            "export_abort",
            "export_crash_recovery",
        ),
        ROOT / "delta-runtime-cpp/tests/native_mutant_test.cpp": (
            "QC_QUORUM_MISSING",
            "PARTIAL_OR_UNCERTIFIED_PUBLICATION",
        ),
    }
    for path, fragments in require_fragments.items():
        text = path.read_text(encoding="utf-8")
        for fragment in fragments:
            require(fragment in text, "NATIVE_REFINEMENT_SOURCE_INCOMPLETE", fragment)

    for name in EXPECTED_LEGAL:
        load_canonical(TRACE_ROOT / name)
    for name in EXPECTED_MUTANTS:
        load_canonical(MUTANT_ROOT / name)
    with tempfile.TemporaryDirectory(prefix="delta-native-refinement-") as temporary:
        materialized = Path(temporary)
        materialize_formal_tree(materialized)
        input_root = materialized / "implementation-traces"
        input_root.mkdir()
        checker = materialized / "formal/scripts/check-refinement.py"
        legal_results = []
        mutant_results = []
        for name, (trace_id, outcome) in EXPECTED_LEGAL.items():
            target = input_root / name
            target.write_bytes((TRACE_ROOT / name).read_bytes())
            return_code, result = run_accepted_checker(checker, target)
            require(
                return_code == 0 and result.get("status") == "PASS",
                "LEGAL_TRACE_REJECTED",
                name,
            )
            require(result.get("trace_id") == trace_id, "LEGAL_TRACE_ID_INVALID", name)
            require(result.get("terminal_outcome") == outcome, "LEGAL_TRACE_OUTCOME_INVALID", name)
            legal_results.append({"fixture": name, "result": result, "status": "PASS"})
        for name, reason in EXPECTED_MUTANTS.items():
            target = input_root / name
            target.write_bytes((MUTANT_ROOT / name).read_bytes())
            return_code, result = run_accepted_checker(checker, target)
            error = result.get("error", "")
            require(return_code != 0 and reason in error, "MUTANT_COUNTEREXAMPLE_INVALID", name)
            mutant_results.append({"expected_reason": reason, "fixture": name, "status": "PASS"})

    artifacts = []
    for path in [
        *(TRACE_ROOT / name for name in EXPECTED_LEGAL),
        *(MUTANT_ROOT / name for name in EXPECTED_MUTANTS),
    ]:
        artifacts.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return {
        "artifacts": artifacts,
        "checks": [
            "RUNTIME_DERIVED_NORMAL_VIEW_ABORT_CRASH_RECOVERY_TRACES",
            "EXACT_ACCEPTED_FEATURE000_REFINEMENT_CHECKER",
            "REAL_TRANSITION_VIEW_GUARD_MUTANT_REJECTED",
            "REAL_RUNTIME_DURABILITY_BARRIER_MUTANT_REJECTED",
            "TRACE_BYTES_CANONICAL_AND_CONTENT_ADDRESSED",
        ],
        "formal_impact": "REFINEMENT_ONLY",
        "formal_semantics_id": EXPECTED_FORMAL_ID,
        "legal": legal_results,
        "mutants": mutant_results,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "status": "PASS",
        "task_ids": ["T040", "T041", "T042", "HR003-022", "HR003-023"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    arguments = parser.parse_args()
    try:
        require(arguments.check_only, "CHECK_ONLY_REQUIRED")
        result = verify_all()
    except (NativeRefinementError, OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        result = {
            "error_code": str(error),
            "formal_semantics_id": EXPECTED_FORMAL_ID,
            "schema_version": "1.0.0",
            "status": "FAIL",
        }
        print(canonical_json_bytes(result).decode())
        return 2
    print(canonical_json_bytes(result).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
