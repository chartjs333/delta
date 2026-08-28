"""Publish and verify exact feature-007 scheduling contract evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "007-domain-pure-ticket-scheduling"
OUTPUT: Final = FEATURE / "evidence" / "protocol-contracts.json"
PREDECESSOR: Final = "bd9080392b7710441c76b834c539881139472b52"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
SCHEMA_NAMES: Final = (
    "capability-profile",
    "domain-ticket-policy",
    "eligibility-decision",
    "infeasibility-report",
    "lease-timer-token",
    "round-ticket-plan",
    "ticket-lease",
    "work-ticket",
)
SOURCE_ARTIFACTS: Final = (
    ".github/workflows/ci.yml",
    "Makefile",
    "delta-protocol/fixtures/007/cross-language/golden-v1.json",
    "delta-protocol/fixtures/007/invalid/scheduling-negative-v1.json",
    "delta-protocol/fixtures/007/valid/scheduling-contract-v1.json",
    "delta-protocol/registry.json",
    "delta-protocol/schemas/007/capability-profile-v1.json",
    "delta-protocol/schemas/007/domain-ticket-policy-v1.json",
    "delta-protocol/schemas/007/eligibility-decision-v1.json",
    "delta-protocol/schemas/007/infeasibility-report-v1.json",
    "delta-protocol/schemas/007/lease-timer-token-v1.json",
    "delta-protocol/schemas/007/registry-v1.json",
    "delta-protocol/schemas/007/round-ticket-plan-v1.json",
    "delta-protocol/schemas/007/ticket-lease-v1.json",
    "delta-protocol/schemas/007/work-ticket-v1.json",
    "specs/007-domain-pure-ticket-scheduling/scripts/scheduling_contracts.py",
    "specs/007-domain-pure-ticket-scheduling/scripts/verify_protocol_contracts.py",
    "specs/007-domain-pure-ticket-scheduling/tests/test_scheduling_contracts.py",
)

sys.path.insert(0, str(FEATURE / "scripts"))
import scheduling_contracts as contracts  # noqa: E402

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class EvidenceError(RuntimeError):
    """Stable fail-closed contract evidence error."""


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise EvidenceError(f"{code}:{detail}" if detail else code)


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


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def validate_source(commit: str) -> list[dict[str, str]]:
    require(git_text("rev-parse", f"{commit}^{{commit}}") == commit, "SOURCE_COMMIT_INVALID")
    process = subprocess.run(
        ["git", "merge-base", "--is-ancestor", PREDECESSOR, commit],
        cwd=ROOT,
        check=False,
    )
    require(process.returncode == 0, "SOURCE_PREDECESSOR_INVALID")
    process = subprocess.run(
        ["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT, check=False
    )
    require(process.returncode == 0, "SOURCE_NOT_ANCESTOR")
    changed = set(git_text("diff", "--name-only", PREDECESSOR, commit).splitlines())
    require(changed == set(SOURCE_ARTIFACTS), "SOURCE_SCOPE_INVALID", ",".join(sorted(changed)))
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
    return [
        {"path": path, "sha256": sha256_bytes(source_bytes(commit, path))}
        for path in SOURCE_ARTIFACTS
    ]


def validate_preflight(commit: str) -> dict[str, Any]:
    raw = source_bytes(commit, "specs/007-domain-pure-ticket-scheduling/evidence/preflight.json")
    document = json.loads(raw)
    require(isinstance(document, dict), "PREFLIGHT_INVALID")
    require(document.get("status") == "PASS", "PREFLIGHT_NOT_PASS")
    require(document.get("formal_semantics_id") == FORMAL_ID, "PREFLIGHT_FORMAL_ID_DRIFT")
    require(
        document.get("formal_impact", {}).get("classification") == "REFINEMENT_ONLY",
        "PREFLIGHT_CLASS_DRIFT",
    )
    require(
        document.get("formal_impact", {}).get("new_formal_action_ids") == [],
        "PREFLIGHT_ACTION_EXTENSION",
    )
    return {
        "sha256": sha256_bytes(raw),
        "source_commit": document["source"]["commit"],
        "status": "PASS",
    }


def validate_schema_contracts(outputs: dict[str, bytes]) -> list[dict[str, str]]:
    records = []
    for name in SCHEMA_NAMES:
        path = f"schemas/007/{name}-v1.json"
        schema = json.loads(outputs[path])
        require(
            schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
            "SCHEMA_DIALECT_INVALID",
            name,
        )
        require(schema.get("additionalProperties") is False, "SCHEMA_OPEN", name)
        properties = schema.get("properties")
        require(isinstance(properties, dict), "SCHEMA_PROPERTIES_INVALID", name)
        require(schema.get("required") == sorted(properties), "SCHEMA_REQUIRED_INVALID", name)
        forbidden = {
            "adaptive_h",
            "adaptive_b",
            "coefficient",
            "device_speed_weight",
            "pi_d",
            "staleness_weight",
        }
        require(not (forbidden & set(properties)), "SCHEMA_FORBIDDEN_MATH_FIELD", name)
        records.append({"name": name, "sha256": sha256_bytes(outputs[path])})
    return records


def build(commit: str) -> dict[str, Any]:
    commit = git_text("rev-parse", commit)
    outputs = contracts.build_outputs()
    contracts.check_outputs(outputs)
    validation = contracts.validate_outputs(outputs)
    golden = json.loads(outputs["fixtures/007/cross-language/golden-v1.json"])
    local_registry = json.loads(outputs["schemas/007/registry-v1.json"])
    return {
        "checks": [
            "EIGHT_STRICT_SCHEMAS_FROZEN",
            "CANONICAL_BYTES_AND_DOMAIN_IDS_EXACT",
            "EXACT_DOMAIN_QUOTA_DATA_B_H_CONTEXT",
            "CAPABILITY_HAS_ZERO_MATHEMATICAL_WEIGHT_AUTHORITY",
            "OPAQUE_TIMER_BINDS_EXACT_LEASE_CONTEXT",
            "INFEASIBILITY_PRESERVES_IMMUTABLE_POLICY",
            "ADAPTIVE_DEVICE_JAVA_REASSIGN_FIXTURES_REJECTED",
            "GLOBAL_REGISTRY_CLOSED_WITH_STABLE_IDS",
            "NO_FORMAL_SOURCE_DIFF",
        ],
        "classification": "REFINEMENT_ONLY",
        "formal_semantics_id": FORMAL_ID,
        "identities": {
            "plan_id": golden["plan"]["content_id"],
            "registry_sha256": sha256_bytes(outputs["schemas/007/registry-v1.json"]),
            "schema_ids": [item["id"] for item in local_registry["artifacts"]],
        },
        "preflight": validate_preflight(commit),
        "schema_version": "1.0.0",
        "schemas": validate_schema_contracts(outputs),
        "semantic_completeness_claimed": False,
        "source": {
            "artifacts": validate_source(commit),
            "commit": commit,
            "tree": git_text("rev-parse", f"{commit}^{{tree}}"),
        },
        "status": "PASS",
        "task_ids": [f"T{index:03d}" for index in range(5, 11)],
        "validation": validation,
    }


def source_for_run(check_only: bool) -> str:
    if not check_only:
        require(
            not git_text("status", "--porcelain", "--untracked-files=all"), "SOURCE_TREE_NOT_CLEAN"
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
        result = build(source_for_run(arguments.check_only))
        encoded = canonical_json_bytes(result)
        if arguments.check_only:
            require(OUTPUT.read_bytes() == encoded, "CONTRACT_EVIDENCE_STALE")
        else:
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT.write_bytes(encoded)
    except (
        EvidenceError,
        contracts.ContractError,
        OSError,
        ValueError,
        json.JSONDecodeError,
    ) as error:
        print(contracts.canonical_json_bytes({"error": str(error), "status": "FAIL"}).decode())
        return 2
    print(encoded.decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
