"""Verify frozen feature-008 protocol contracts and publish exact-source evidence."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs/008-certificates-and-consensus"
OUTPUT: Final = FEATURE / "evidence/protocol-contracts.json"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
FEATURE007_MERGE: Final = "2054f31ef0f6750645b924ef337a35d1737c619d"

sys.path.insert(0, str(ROOT / "formal/scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class ContractEvidenceError(RuntimeError):
    """Stable fail-closed feature-008 contract-evidence error."""


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise ContractEvidenceError(f"{code}:{detail}" if detail else code)


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    require(process.returncode == 0, "GIT_COMMAND_FAILED", process.stderr.decode().strip())
    return process.stdout.replace(b"\r\n", b"\n")


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode().strip()


def tracked_bytes(path: str, revision: str) -> bytes:
    return git_bytes("show", f"{revision}:{path}")


def artifact(path: str, revision: str) -> dict[str, str]:
    return {"path": path, "sha256": hashlib.sha256(tracked_bytes(path, revision)).hexdigest()}


def load_contracts() -> Any:
    path = FEATURE / "scripts/certificate_contracts.py"
    spec = importlib.util.spec_from_file_location("feature008_contracts_evidence", path)
    require(spec is not None and spec.loader is not None, "CONTRACT_HELPER_LOAD_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_preflight() -> dict[str, Any]:
    document = json.loads((FEATURE / "evidence/preflight.json").read_text(encoding="utf-8"))
    require(document.get("status") == "PASS", "PREFLIGHT_NOT_PASS")
    require(document.get("formal_semantics_id") == FORMAL_ID, "PREFLIGHT_FORMAL_ID_DRIFT")
    require(
        document.get("formal_impact", {}).get("classification") == "REFINEMENT_ONLY",
        "PREFLIGHT_CLASS_DRIFT",
    )
    require(document.get("architecture", {}).get("production_source_count") == 0, "PREFLIGHT_DIRTY")
    return {
        "commit": document["source"]["commit"],
        "sha256": hashlib.sha256((FEATURE / "evidence/preflight.json").read_bytes()).hexdigest(),
        "status": "PASS",
    }


def verify_source_boundary(source_commit: str, output_paths: set[str]) -> dict[str, Any]:
    changed = git_text("diff", "--name-only", FEATURE007_MERGE, source_commit).splitlines()
    production_prefixes = (
        "delta-core-cpp/",
        "delta-runtime-cpp/",
        "delta-ffi/",
        "delta-node-java/",
        "delta-worker-python/",
    )
    forbidden = [path for path in changed if path.startswith(production_prefixes)]
    require(not forbidden, "PRODUCTION_SOURCE_BEFORE_CONTRACT_GATE", json.dumps(forbidden))
    protocol = {path for path in changed if path.startswith("delta-protocol/")}
    expected_protocol = {f"delta-protocol/{path}" for path in output_paths}
    require(protocol == expected_protocol, "PROTOCOL_OUTPUT_SET_DRIFT")
    formal = git_text(
        "diff",
        "--name-only",
        FEATURE007_MERGE,
        source_commit,
        "--",
        "formal/tla",
        "formal/proofs",
        "formal/schemas",
    )
    require(not formal, "FORMAL_SOURCE_DIFF_PRESENT", formal)
    return {
        "changed_path_count": len(changed),
        "formal_source_diff": [],
        "production_source_count": 0,
        "protocol_output_count": len(protocol),
        "status": "PASS",
    }


def verify(source_commit: str) -> dict[str, Any]:
    contracts = load_contracts()
    outputs = contracts.build_outputs()
    contracts.check_outputs(outputs)
    validation = contracts.validate_outputs(outputs)
    require(validation.get("status") == "PASS", "CONTRACT_VALIDATION_FAILED")
    paths = sorted(f"delta-protocol/{path}" for path in outputs)
    source_paths = [
        *paths,
        "specs/008-certificates-and-consensus/scripts/certificate_contracts.py",
        "specs/008-certificates-and-consensus/scripts/verify_protocol_contracts.py",
        "specs/008-certificates-and-consensus/tests/test_certificate_contracts.py",
        "specs/008-certificates-and-consensus/tests/test_verify_protocol_contracts.py",
    ]
    return {
        "checks": [
            "EXACT_PREFLIGHT_PASS",
            "ELEVEN_CLOSED_SCHEMAS_FROZEN",
            "ONE_PARENT_GRAPH_AND_REQUIRED_MATRIX_FROZEN",
            "VALID_INVALID_CROSS_LANGUAGE_FIXTURES_REPRODUCIBLE",
            "EARLY_SEED_MIXED_VIEW_INCOMPLETE_UNSAFE_CONFLICTING_CURRENT_NEGATIVES_BOUND",
            "NO_PRODUCTION_SOURCE_BEFORE_CONTRACT_GATE",
            "NO_FORMAL_SOURCE_DIFF",
            "PROTOCOL_REGISTRY_CLOSED",
        ],
        "classification": "REFINEMENT_ONLY",
        "formal_semantics_id": FORMAL_ID,
        "preflight": verify_preflight(),
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": [artifact(path, source_commit) for path in source_paths],
            "commit": source_commit,
            "tree": git_text("rev-parse", f"{source_commit}^{{tree}}"),
        },
        "source_boundary": verify_source_boundary(source_commit, set(outputs)),
        "status": "PASS",
        "task_ids": [f"T{index:03d}" for index in range(6, 13)],
        "validation": validation,
    }


def source_for_run(check_only: bool, source_commit: str | None) -> str:
    if not check_only:
        if source_commit is None:
            require(
                not git_text("status", "--porcelain", "--untracked-files=all"),
                "SOURCE_TREE_NOT_CLEAN",
            )
            source_commit = "HEAD"
        return git_text("rev-parse", f"{source_commit}^{{commit}}")
    require(OUTPUT.is_file(), "CONTRACT_EVIDENCE_MISSING")
    document = json.loads(OUTPUT.read_text(encoding="utf-8"))
    source = document.get("source", {}).get("commit")
    require(isinstance(source, str) and re.fullmatch(r"[0-9a-f]{40}", source), "SOURCE_INVALID")
    return source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--source-commit")
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    try:
        require(arguments.check_only != arguments.write, "EXACT_MODE_REQUIRED")
        result = verify(source_for_run(arguments.check_only, arguments.source_commit))
        encoded = canonical_json_bytes(result)
        if arguments.check_only:
            require(OUTPUT.read_bytes() == encoded, "CONTRACT_EVIDENCE_STALE")
        else:
            OUTPUT.write_bytes(encoded)
    except (ContractEvidenceError, OSError, ValueError, json.JSONDecodeError) as error:
        print(canonical_json_bytes({"error_code": str(error), "status": "FAIL"}).decode())
        return 2
    print(encoded.decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
