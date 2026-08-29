"""Publish or verify feature-008 certificate-chain refinement evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs/008-certificates-and-consensus"
OUTPUT: Final = FEATURE / "evidence/certificate-refinement.json"
TRACE_ROOT: Final = FEATURE / "evidence/traces"
PREDECESSOR: Final = "2054f31ef0f6750645b924ef337a35d1737c619d"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
LEGAL_FIXTURES: Final = ("normal-apply.json", "applyqc-pointer-recovery.json")
ILLEGAL_FIXTURES: Final = (
    "seed-without-isc.json",
    "ec-non-isc-member.json",
    "parameter-wrong-parent.json",
    "incomplete-aggregate.json",
    "duplicate-aggregate.json",
    "conflicting-durable-vote.json",
    "current-without-applyqc.json",
)
EXPECTED_ACTIONS: Final = [
    "ACT-ISC-FINALIZE",
    "ACT-SEED-GENERATE",
    "ACT-EC-FINALIZE",
    "ACT-APC-FINALIZE",
    *(["ACT-PARAM-FINALIZE"] * 4),
    "ACT-ROOT-FINALIZE",
    "ACT-APPLY-FINALIZE",
    "ACT-CURRENT-ADVANCE",
]


class RefinementError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise RefinementError(code)


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, capture_output=True, check=False)
    require(process.returncode == 0, "GIT_FAILED:" + process.stderr.decode(errors="replace"))
    return process.stdout.replace(b"\r\n", b"\n")


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode().strip()


def load_generator() -> Any:
    path = FEATURE / "scripts/generate_refinement_traces.py"
    spec = importlib.util.spec_from_file_location("feature008_traces", path)
    require(spec is not None and spec.loader is not None, "TRACE_GENERATOR_LOAD_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_traces() -> list[dict[str, str]]:
    expected = load_generator().build()
    require(
        set(path.name for path in TRACE_ROOT.glob("*.json")) == set(expected), "TRACE_SET_DRIFT"
    )
    artifacts = []
    for name, document in sorted(expected.items()):
        raw = TRACE_ROOT.joinpath(name).read_bytes()
        require(raw == canonical(document) + b"\n", "TRACE_DRIFT:" + name)
        artifacts.append(
            {"path": f"evidence/traces/{name}", "sha256": hashlib.sha256(raw).hexdigest()}
        )
    legal = expected["legal-full-chain.json"]
    require(legal["terminal_outcome"] == "APPLIED", "LEGAL_TRACE_NOT_APPLIED")
    require(
        [event["action_id"] for event in legal["events"]] == EXPECTED_ACTIONS, "ACTION_ORDER_DRIFT"
    )
    require(
        all(document["formal_semantics_id"] == FORMAL_ID for document in expected.values()),
        "FORMAL_ID_DRIFT",
    )
    return artifacts


def materialize_formal(commit: str, target: Path) -> Path:
    archive = subprocess.run(
        ["git", "archive", "--format=tar", commit, "formal", "specs/000-formal-tla-spec"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    require(archive.returncode == 0, "FORMAL_ARCHIVE_FAILED")
    with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as bundle:
        for member in bundle.getmembers():
            require(
                (target / member.name).resolve().is_relative_to(target.resolve()),
                "ARCHIVE_PATH_INVALID",
            )
        bundle.extractall(target, filter="data")
    return target / "formal/scripts/check-refinement.py"


def checker_result(checker: Path, fixture: Path, cwd: Path) -> tuple[int, dict[str, Any]]:
    process = subprocess.run(
        [sys.executable, str(checker), str(fixture)],
        cwd=cwd,
        capture_output=True,
        check=False,
        text=True,
    )
    lines = process.stdout.strip().splitlines()
    require(bool(lines), "FORMAL_CHECKER_OUTPUT_MISSING:" + fixture.name)
    return process.returncode, json.loads(lines[-1])


def verify_formal(commit: str) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="delta-008-refinement-") as temporary:
        root = Path(temporary)
        checker = materialize_formal(commit, root)
        legal = []
        for name in LEGAL_FIXTURES:
            code, result = checker_result(
                checker, root / "formal/fixtures/traces/legal" / name, root
            )
            require(
                code == 0 and result.get("status") == "PASS", "LEGAL_FORMAL_TRACE_REJECTED:" + name
            )
            legal.append({"fixture": name, "status": "PASS"})
        illegal = []
        for name in ILLEGAL_FIXTURES:
            code, result = checker_result(
                checker, root / "formal/fixtures/traces/illegal" / name, root
            )
            require(
                code != 0 and result.get("status") == "FAIL",
                "ILLEGAL_FORMAL_TRACE_ACCEPTED:" + name,
            )
            illegal.append({"error": result.get("error"), "fixture": name, "status": "PASS"})
    return {"illegal": illegal, "legal": legal, "status": "PASS"}


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
    return {
        "checks": [
            "FULL_ISC_SEED_EC_APC_SHARD_ROOT_APPLY_CURRENT_TRACE_APPLIED",
            "VOTE_ARTIFACT_POINTER_CRASH_RECOVERY_REPLAY_TRACE",
            "EXACT_FEATURE000_LEGAL_FIXTURES_ACCEPTED",
            "SEVEN_FEATURE000_ILLEGAL_FIXTURES_REJECTED",
            "NO_FORMAL_SOURCE_DIFF",
        ],
        "classification": "REFINEMENT_ONLY",
        "formal": verify_formal(commit),
        "formal_semantics_id": FORMAL_ID,
        "phase": "008-certificate-refinement",
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {"commit": commit, "tree": git_text("rev-parse", f"{commit}^{{tree}}")},
        "status": "PASS",
        "task_ids": ["T045", "T046", "T047", "T048", "HR008-018"],
        "trace_artifacts": verify_traces(),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--source-commit")
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    require(arguments.check_only != arguments.write, "EXACT_MODE_REQUIRED")
    if arguments.check_only:
        existing = json.loads(OUTPUT.read_text())
        source_commit = existing["source"]["commit"]
    else:
        require(arguments.source_commit is not None, "SOURCE_COMMIT_REQUIRED")
        source_commit = arguments.source_commit
    result = build(source_commit)
    encoded = canonical(result)
    if arguments.check_only:
        require(OUTPUT.read_bytes() == encoded, "REFINEMENT_EVIDENCE_DRIFT")
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_bytes(encoded)
    print(encoded.decode())
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (
        RefinementError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        json.JSONDecodeError,
    ) as error:
        print(canonical({"error": str(error), "status": "FAIL"}).decode())
        raise SystemExit(2) from error
