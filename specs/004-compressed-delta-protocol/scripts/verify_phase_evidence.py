"""Verify content-addressed feature-004 phase evidence against the exact source tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Final, NoReturn

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "004-compressed-delta-protocol"
OUTPUTS: Final = (
    "protocol-contracts-final.json",
    "native-architecture.json",
    "proof-instances.json",
    "direct-q-refinement.json",
)


class PhaseEvidenceError(RuntimeError):
    pass


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise PhaseEvidenceError(f"{code}: {detail}" if detail else code)


def git_text(*arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments], cwd=ROOT, check=False, capture_output=True, text=True
    )
    require(process.returncode == 0, "GIT_COMMAND_FAILED", process.stderr.strip())
    return process.stdout.strip()


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    require(
        process.returncode == 0,
        "GIT_COMMAND_FAILED",
        process.stderr.decode(errors="replace").strip(),
    )
    return process.stdout


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def verify() -> dict[str, object]:
    source: dict[str, str] | None = None
    evidence: list[dict[str, str]] = []
    documents: dict[str, dict[str, object]] = {}
    for name in OUTPUTS:
        path = FEATURE / "evidence" / name
        raw = path.read_bytes()
        document = json.loads(raw.decode("utf-8"))
        require(isinstance(document, dict), "EVIDENCE_ROOT_INVALID", name)
        require(raw == canonical_json_bytes(document) + b"\n", "EVIDENCE_NOT_CANONICAL", name)
        declared_source = document.get("source")
        require(isinstance(declared_source, dict), "EVIDENCE_SOURCE_INVALID", name)
        require(
            all(isinstance(declared_source.get(field), str) for field in ("commit", "tree")),
            "EVIDENCE_SOURCE_FIELDS_INVALID",
            name,
        )
        if source is None:
            source = {"commit": declared_source["commit"], "tree": declared_source["tree"]}
        require(declared_source == source, "EVIDENCE_SOURCE_DIVERGENCE", name)
        require(document.get("status") == "PASS", "EVIDENCE_STATUS_NOT_PASS", name)
        require(
            document.get("formal_semantics_id")
            == "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6",
            "EVIDENCE_FORMAL_ID_INVALID",
            name,
        )
        documents[name] = document
        evidence.append(
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": __import__("hashlib").sha256(raw).hexdigest(),
            }
        )
    require(source is not None, "EVIDENCE_SET_EMPTY")
    commit = source["commit"]
    require(git_text("rev-parse", f"{commit}^{{commit}}") == commit, "SOURCE_COMMIT_INVALID")
    require(git_text("rev-parse", f"{commit}^{{tree}}") == source["tree"], "SOURCE_TREE_INVALID")
    process = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT, check=False
    )
    require(process.returncode == 0, "SOURCE_NOT_ANCESTOR")
    for name, document in documents.items():
        artifacts = document.get("artifacts")
        require(isinstance(artifacts, list) and artifacts, "ARTIFACT_SET_INVALID", name)
        for artifact in artifacts:
            require(isinstance(artifact, dict), "ARTIFACT_INVALID", name)
            path = artifact.get("path")
            digest = artifact.get("sha256")
            require(isinstance(path, str) and isinstance(digest, str), "ARTIFACT_FIELDS_INVALID")
            raw = git_bytes("show", f"{commit}:{path}")
            require(hashlib.sha256(raw).hexdigest() == digest, "ARTIFACT_HASH_INVALID", path)
    contracts = documents["protocol-contracts-final.json"]
    require(contracts.get("golden", {}).get("shards") == 5, "GOLDEN_SHARD_COUNT_INVALID")  # type: ignore[union-attr]
    architecture = documents["native-architecture.json"]
    require(
        architecture.get("finding_count") == 0 and architecture.get("findings") == [],
        "ARCHITECTURE_FINDINGS_PRESENT",
    )
    proofs = documents["proof-instances.json"]
    require(
        proofs.get("first_unsafe_int64", {}).get("status") == "REJECT",  # type: ignore[union-attr]
        "FIRST_UNSAFE_NOT_REJECTED",
    )
    refinement = documents["direct-q-refinement.json"]
    require(
        refinement.get("legal_trace", {}).get("terminal_outcome") == "APPLIED"  # type: ignore[union-attr]
        and "UNCHECKED_ARITHMETIC_ACCEPTED" in str(refinement.get("unsafe_trace", {}).get("error")),  # type: ignore[union-attr]
        "REFINEMENT_EVIDENCE_INVALID",
    )
    return {
        "evidence": sorted(evidence, key=lambda item: item["path"]),
        "phase": "004-phase-evidence",
        "schema_version": "1.0.0",
        "source": source,
        "status": "PASS",
    }


def fail(error: Exception) -> NoReturn:
    print(
        canonical_json_bytes(
            {
                "error": str(error),
                "phase": "004-phase-evidence",
                "schema_version": "1.0.0",
                "status": "FAIL",
            }
        ).decode("utf-8")
    )
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.parse_args()
    try:
        result = verify()
    except (PhaseEvidenceError, OSError, ValueError, json.JSONDecodeError) as exc:
        fail(exc)
    print(canonical_json_bytes(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
