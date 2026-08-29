"""Verify exact-source feature-009 protocol contracts and frozen QLoRA identities."""

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
FEATURE: Final = ROOT / "specs" / "009-qlora-8gb-mode"
OUTPUT: Final = FEATURE / "evidence" / "protocol-contracts.json"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
PREFLIGHT_OVERLAY: Final = "ed01d126aed3cbe981704a0dac6b27e0e9d0d32a"
RUNTIME_PREFIXES: Final = (
    "delta-core-cpp/",
    "delta-runtime-cpp/",
    "delta-ffi/",
    "delta-node-java/",
    "delta-worker-python/",
)

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class ProtocolContractError(RuntimeError):
    """Stable fail-closed feature-009 protocol-contract error."""


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise ProtocolContractError(f"{code}:{detail}" if detail else code)


def load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    require(spec is not None and spec.loader is not None, "MODULE_LOAD_FAILED", name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


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


def tracked_bytes(path: str, revision: str) -> bytes:
    relative = Path(path)
    require(not relative.is_absolute() and ".." not in relative.parts, "UNSAFE_PATH", path)
    return git_bytes("show", f"{revision}:{path}")


def artifact(path: str, revision: str) -> dict[str, str]:
    return {"path": path, "sha256": sha256_bytes(tracked_bytes(path, revision))}


def require_ancestor(ancestor: str, descendant: str, code: str) -> None:
    process = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    require(process.returncode == 0, code)


def verify_preflight(source_commit: str) -> dict[str, Any]:
    module = load_module(
        "feature009_preflight_contract_dependency",
        FEATURE / "scripts" / "verify_preflight.py",
    )
    raw = (FEATURE / "evidence" / "preflight.json").read_bytes()
    document = json.loads(raw)
    require(isinstance(document, dict), "PREFLIGHT_INVALID")
    preflight_source = document.get("source", {}).get("commit")
    require(isinstance(preflight_source, str), "PREFLIGHT_SOURCE_INVALID")
    require_ancestor(preflight_source, source_commit, "PREFLIGHT_SOURCE_NOT_ANCESTOR")
    expected = module.verify(preflight_source)
    require(raw == canonical_json_bytes(expected), "PREFLIGHT_EVIDENCE_STALE")
    require(document.get("status") == "PASS", "PREFLIGHT_NOT_PASS")
    require(
        document.get("hardware_readiness", {}).get("status") == "IDENTIFIED_PROFILE_FROZEN",
        "HARDWARE_PROFILE_NOT_FROZEN",
    )
    return {
        "artifact": {
            "path": "specs/009-qlora-8gb-mode/evidence/preflight.json",
            "sha256": sha256_bytes(raw),
        },
        "hardware_status": document["hardware_readiness"]["status"],
        "source_commit": preflight_source,
        "status": "PASS",
    }


def output_paths(module: Any) -> list[str]:
    paths = []
    for absolute in module.expected_outputs():
        paths.append(absolute.relative_to(ROOT).as_posix())
    return sorted(paths)


def verify_contracts(source_commit: str) -> dict[str, Any]:
    module = load_module(
        "feature009_contract_generator_dependency",
        FEATURE / "scripts" / "qlora_contracts.py",
    )
    expected = module.expected_outputs()
    for path, value in expected.items():
        relative = path.relative_to(ROOT).as_posix()
        require(tracked_bytes(relative, source_commit) == value, "CONTRACT_OUTPUT_DRIFT", relative)
    fixtures = module.fixture_documents()
    schemas = module.schema_documents()
    for name, wrapper in fixtures["valid"]["artifacts"].items():
        module.validate_identified(name, wrapper, schemas)
    chain = module.validate_chain(fixtures["valid"]["artifacts"])
    for case in fixtures["invalid"]["cases"]:
        module.validate_negative(case, fixtures["valid"]["artifacts"], schemas)
    return {
        "artifact_count": chain["artifact_count"],
        "invalid_case_count": len(fixtures["invalid"]["cases"]),
        "output_count": len(expected),
        "schema_count": len(schemas),
        "status": "PASS",
    }


def verify_source_boundary(source_commit: str) -> dict[str, Any]:
    changed = git_text("diff", "--name-only", PREFLIGHT_OVERLAY, source_commit).splitlines()
    runtime = [path for path in changed if path.startswith(RUNTIME_PREFIXES)]
    require(not runtime, "RUNTIME_SOURCE_BEFORE_CONTRACT_GATE", json.dumps(runtime))
    formal = git_text(
        "diff",
        "--name-only",
        PREFLIGHT_OVERLAY,
        source_commit,
        "--",
        "formal/tla",
        "formal/proofs",
        "formal/schemas",
    )
    require(not formal, "FORMAL_SOURCE_DIFF_PRESENT", formal)
    unexpected = [
        path
        for path in changed
        if not path.startswith("delta-protocol/")
        and not path.startswith("specs/009-qlora-8gb-mode/")
    ]
    require(not unexpected, "UNEXPECTED_CONTRACT_PATH", json.dumps(unexpected))
    return {
        "changed_path_count": len(changed),
        "formal_source_diff": [],
        "runtime_source_count": 0,
        "status": "PASS",
    }


def verify_source(source_commit: str, paths: list[str]) -> dict[str, Any]:
    require_ancestor(source_commit, "HEAD", "CONTRACT_SOURCE_NOT_ANCESTOR")
    extra = [
        "specs/009-qlora-8gb-mode/scripts/qlora_contracts.py",
        "specs/009-qlora-8gb-mode/scripts/verify_protocol_contracts.py",
        "specs/009-qlora-8gb-mode/tests/test_qlora_contracts.py",
        "specs/009-qlora-8gb-mode/tests/test_verify_protocol_contracts.py",
    ]
    return {
        "artifacts": [artifact(path, source_commit) for path in sorted(set(paths + extra))],
        "commit": source_commit,
        "tree": git_text("rev-parse", f"{source_commit}^{{tree}}"),
    }


def verify(source_commit: str) -> dict[str, Any]:
    module = load_module(
        "feature009_contract_paths_dependency",
        FEATURE / "scripts" / "qlora_contracts.py",
    )
    paths = output_paths(module)
    validation = verify_contracts(source_commit)
    return {
        "checks": [
            "EXACT_PREFLIGHT_PASS",
            "ELEVEN_CLOSED_RUNTIME_NEUTRAL_SCHEMAS",
            "EXPLICIT_ORDERED_TARGETS_AND_ADAPTER_PARAMETERS",
            "BASE_OMISSION_AND_EPHEMERAL_CACHE_POLICY_FROZEN",
            "VALID_INVALID_TINY_CROSS_LANGUAGE_FIXTURES_REPRODUCIBLE",
            "NO_PARALLEL_QLORA_CERTIFICATE_GRAPH",
            "NO_RUNTIME_SOURCE_BEFORE_CONTRACT_GATE",
            "NO_FORMAL_SOURCE_DIFF",
            "PROTOCOL_REGISTRY_CLOSED",
        ],
        "classification": "REFINEMENT_ONLY",
        "formal_semantics_id": FORMAL_ID,
        "preflight": verify_preflight(source_commit),
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": verify_source(source_commit, paths),
        "source_boundary": verify_source_boundary(source_commit),
        "status": "PASS",
        "task_ids": ["T001", "T002", "T005"],
        "validation": validation,
    }


def source_for_run(check_only: bool) -> str:
    if not check_only:
        require(
            not git_text("status", "--porcelain", "--untracked-files=all"),
            "SOURCE_TREE_NOT_CLEAN",
        )
        return git_text("rev-parse", "HEAD")
    require(OUTPUT.is_file(), "CONTRACT_EVIDENCE_MISSING")
    document = json.loads(OUTPUT.read_text(encoding="utf-8"))
    source = document.get("source", {}).get("commit")
    require(
        isinstance(source, str) and re.fullmatch(r"[0-9a-f]{40}", source) is not None,
        "CONTRACT_SOURCE_INVALID",
    )
    return source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    arguments = parser.parse_args()
    try:
        result = verify(source_for_run(arguments.check_only))
        encoded = canonical_json_bytes(result)
        if arguments.check_only:
            require(OUTPUT.read_bytes() == encoded, "CONTRACT_EVIDENCE_STALE")
        else:
            OUTPUT.write_bytes(encoded)
    except (
        ProtocolContractError,
        RuntimeError,
        OSError,
        UnicodeDecodeError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ) as error:
        print(
            canonical_json_bytes(
                {
                    "error_code": str(error),
                    "formal_semantics_id": FORMAL_ID,
                    "status": "FAIL",
                }
            ).decode()
        )
        return 2
    print(encoded.decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
