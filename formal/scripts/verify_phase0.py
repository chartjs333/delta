#!/usr/bin/env python3
"""Verify the frozen authority/scope artifacts for tasks T000-T003."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from formal_artifacts import (
    derive_formal_semantics_id,
    discover_semantic_artifacts,
    load_json_strict,
    semantic_text_sha256,
    validate_contract_registry,
)

ROOT = Path(__file__).resolve().parents[2]
CANDIDATE_VERSION = "1.1.0"
HISTORICAL_GO = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
ACCEPTED_RESIDUAL_SHA256 = "51b1a92b724f6021eb4a534e6f86c92905c8fecd6f55fb5173c7eaf253d8a2e6"
REQUIRED_INPUTS = {
    "AGENTS.md",
    ".specify/memory/constitution.md",
    "docs/adr/0000-formal-verification-gate.md",
    "docs/adr/0001-deltareduce-v1.md",
    "docs/adr/0002-canonical-rational-rounding.md",
    "docs/adr/0010-hybrid-runtime-boundary.md",
    "specs/ROADMAP.md",
    "specs/HYBRID-RUNTIME-MAP.md",
    "specs/000-formal-tla-spec/failure-semantics.md",
    "specs/000-formal-tla-spec/proof-obligations.md",
    "specs/000-formal-tla-spec/refinement-contract.md",
    "specs/000-formal-tla-spec/spec.md",
    "specs/000-formal-tla-spec/plan.md",
    "specs/000-formal-tla-spec/tasks.md",
    "specs/000-formal-tla-spec/amendments/0001-arithmetic-input-binding.md",
    "specs/000-formal-tla-spec/candidate-contract.md",
    "specs/000-formal-tla-spec/accepted-residual-20260928.md",
    "formal/reports/formal-id-registry.json",
    "formal/reports/coverage-matrix.md",
}


def read_json(path: Path) -> dict[str, Any]:
    value = load_json_strict(path)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def verify_unique_ids(registry: dict[str, Any], collection: str, errors: list[str]) -> int:
    values = registry.get(collection)
    require(isinstance(values, list) and bool(values), f"{collection} is empty", errors)
    if not isinstance(values, list):
        return 0
    ids = [value.get("id") for value in values if isinstance(value, dict)]
    require(len(ids) == len(values), f"{collection} contains a non-object entry", errors)
    require(
        all(isinstance(item, str) and item for item in ids),
        f"{collection} has an invalid id",
        errors,
    )
    require(len(ids) == len(set(ids)), f"{collection} contains duplicate ids", errors)
    return len(values)


def verify(root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    reports = root / "formal" / "reports"
    baseline = read_json(reports / "baseline-inputs.json")
    registry = read_json(reports / "formal-id-registry.json")
    coverage = (reports / "coverage-matrix.md").read_text(encoding="utf-8")
    failure_semantics = (root / "specs" / "000-formal-tla-spec" / "failure-semantics.md").read_text(
        encoding="utf-8"
    )
    feature_spec = (root / "specs" / "000-formal-tla-spec" / "spec.md").read_text(encoding="utf-8")

    require(
        baseline.get("formal_semantics_version")
        == registry.get("formal_semantics_version")
        == CANDIDATE_VERSION,
        "formal semantics version mismatch",
        errors,
    )

    scope = baseline.get("scope_freeze", {})
    require(
        isinstance(scope, dict)
        and scope.get("residual_ids") == [f"R{i}" for i in range(1, 8)]
        and scope.get("accepted_residual_sha256") == ACCEPTED_RESIDUAL_SHA256
        and scope.get("historical_merged_formal_semantics_id") == HISTORICAL_GO,
        "accepted residual or historical authority mismatch",
        errors,
    )
    residual_path = root / "specs/000-formal-tla-spec/accepted-residual-20260928.md"
    require(
        residual_path.is_file() and semantic_text_sha256(residual_path) == ACCEPTED_RESIDUAL_SHA256,
        "accepted residual document changed",
        errors,
    )
    require(
        baseline.get("formal_semantics_id_status") == "candidate_frozen_T000_T003"
        and baseline.get("authority_status") == "CANDIDATE_NOT_FORMAL_GO",
        "candidate freeze must not claim merged Formal GO",
        errors,
    )
    compatibility = registry.get("compatibility", {})
    semantics = read_json(reports / "formal-semantics.json")
    current_artifacts = discover_semantic_artifacts(root)
    derived_id = derive_formal_semantics_id(CANDIDATE_VERSION, current_artifacts)
    require(
        baseline.get("formal_semantics_id")
        == compatibility.get("formal_semantics_id")
        == semantics.get("formal_semantics_id")
        == derived_id,
        "candidate compatibility identity mismatch",
        errors,
    )
    require(
        compatibility.get("id_derivation_status") == "candidate_pending_formal_go"
        and semantics.get("formal_semantics_version") == CANDIDATE_VERSION
        and semantics.get("status") == "candidate_pending_formal_go"
        and semantics.get("compatibility") == compatibility
        and semantics.get("semantic_artifacts") == current_artifacts,
        "candidate compatibility manifest is stale or claims publication",
        errors,
    )
    try:
        validate_contract_registry(root)
    except (KeyError, TypeError, ValueError) as error:
        errors.append(f"contract registry mismatch: {error}")

    hash_records: list[tuple[str, str]] = []
    inputs = baseline.get("inputs")
    require(isinstance(inputs, list) and bool(inputs), "baseline inputs are empty", errors)
    if isinstance(inputs, list):
        seen_paths: set[str] = set()
        for entry in inputs:
            if not isinstance(entry, dict):
                errors.append("baseline input entry is not an object")
                continue
            relative_path = entry.get("path")
            expected_hash = entry.get("sha256")
            if not isinstance(relative_path, str) or not isinstance(expected_hash, str):
                errors.append("baseline input path/hash is invalid")
                continue
            require(
                relative_path not in seen_paths, f"duplicate input path: {relative_path}", errors
            )
            seen_paths.add(relative_path)
            source_path = root / relative_path
            require(source_path.is_file(), f"missing input: {relative_path}", errors)
            if source_path.is_file():
                actual_hash = semantic_text_sha256(source_path)
                require(
                    actual_hash == expected_hash,
                    f"hash mismatch for {relative_path}: {actual_hash} != {expected_hash}",
                    errors,
                )
                hash_records.append((relative_path, actual_hash))
        require(
            seen_paths == REQUIRED_INPUTS,
            "baseline normative input inventory mismatch",
            errors,
        )

    canonical_bundle = "".join(
        f"{path}\t{digest}\n" for path, digest in sorted(hash_records)
    ).encode("utf-8")
    actual_bundle_hash = hashlib.sha256(canonical_bundle).hexdigest()
    require(
        actual_bundle_hash == baseline.get("input_bundle_sha256"),
        "input bundle hash mismatch",
        errors,
    )

    counts = {
        collection: verify_unique_ids(registry, collection, errors)
        for collection in (
            "actions",
            "invariants",
            "temporal_properties",
            "proof_obligations",
            "faults",
            "configs",
        )
    }

    required_action_names = {
        "ProposeRoundConfig",
        "VoteRoundConfig",
        "FinalizeRoundConfig",
        "IssueTicket",
        "LeaseTicket",
        "ExpireLease",
        "ReassignTicket",
        "CommitTicket",
        "AttestAvailability",
        "FinalizeAvailability",
        "CloseInput",
        "VoteISC",
        "FinalizeISC",
        "GenerateSeed",
        "VoteEC",
        "FinalizeEC",
        "VoteAPC",
        "FinalizeAPC",
        "ProposeParameterResult",
        "VoteParameter",
        "FinalizeParameterQC",
        "AssembleAggregateRoot",
        "VoteAggregateRoot",
        "FinalizeAggregateRootQC",
        "ComputeApplyCandidate",
        "VoteApply",
        "FinalizeApplyQC",
        "AdvanceCurrentCheckpoint",
        "SoftTimeout",
        "VoteViewChange",
        "ViewChange",
        "VoteHardAbort",
        "HardAbort",
        "Crash",
        "Restart",
        "RecoverJournal",
        "CorruptArtifact",
        "LoseArtifact",
        "RepairArtifact",
        "PublishCertifiedObject",
        "ReplayMessage",
    }
    registered_action_names = {
        entry.get("name") for entry in registry.get("actions", []) if isinstance(entry, dict)
    }
    require(
        required_action_names <= registered_action_names,
        f"missing action names: {sorted(required_action_names - registered_action_names)}",
        errors,
    )

    required_invariants = {
        "TypeOK",
        "ConfigUniqueness",
        "TicketImmutability",
        "LeaseCommitSafety",
        "CommitUniqueness",
        "VoteUniqueness",
        "QCUniqueness",
        "AvailabilityBeforeISC",
        "ISCImmutability",
        "SeedAfterInputFreeze",
        "ECSubsetISC",
        "APCParentage",
        "ConsensusIntegerOnly",
        "ArithmeticBindingSound",
        # Existing amendment harness checks, each limited to its registered scope.
        "NoStaleArithmeticVotes",
        "HeterogeneousExpected",
        "PersistenceRecordSound",
        "PersistenceRecoverySound",
        "NoOverflow",
        "ShardViewAtomicity",
        "AggregateCompleteness",
        "ApplyUniqueness",
        "CurrentCertified",
        "AbortPreservesParent",
        "RecoveryIdempotence",
        "ViewChangeCertified",
        "AbortCertified",
        "PlaneSeparation",
        "CertifiedPublishOnly",
        "AllQCVotesPersisted",
    }
    registered_invariants = {
        entry.get("name") for entry in registry.get("invariants", []) if isinstance(entry, dict)
    }
    require(
        required_invariants == registered_invariants,
        "registered invariant set differs from the normative invariant set",
        errors,
    )

    required_temporal = {
        "ConfigQCReached",
        "ISCReached",
        "PlanQCReached",
        "AppliedReached",
        "ViewQCReached",
        "AbortQCReached",
        "NeverUsesAbortAsProgress",
        "ConfigEventuallyFinalizesOrAborts",
        "CommittedEventuallyAvailableOrRejectedBeforeISC",
        "FrozenRoundEventuallyGetsPlanOrAborts",
        "PlannedShardEventuallyGetsQCOrRoundAborts",
        "AggregateEventuallyAppliesOrAborts",
        "ExistingApplyQCEventuallyRepairsCurrentPointer",
        "SoftTimeoutEventuallyChangesView",
        "HardDeadlineEventuallyTerminatesNonfinalizedRound",
    }
    registered_temporal = {
        entry.get("name")
        for entry in registry.get("temporal_properties", [])
        if isinstance(entry, dict)
    }
    require(
        required_temporal == registered_temporal,
        "registered temporal-property set differs from the normative set",
        errors,
    )

    required_proofs = {
        "PO-AB1",
        "PO-Q1",
        "PO-Q2",
        "PO-A1",
        "PO-A2",
        "PO-A3",
        "PO-A4",
        "PO-H1",
        "PO-H2",
        "PO-C1",
        "PO-AP1",
        "PO-AP2",
        "PO-D1",
        "PO-R1",
        "PO-R2",
    }
    registered_proofs = {
        entry.get("id")
        for entry in registry.get("proof_obligations", [])
        if isinstance(entry, dict)
    }
    require(required_proofs == registered_proofs, "proof obligation set mismatch", errors)

    required_report_fields = {
        "report_schema_version",
        "formal_semantics_version",
        "formal_semantics_id",
        "source_tree",
        "baseline_inputs",
        "toolchains",
        "model_checks",
        "theorem_checks",
        "mutant_checks",
        "refinement_checks",
        "coverage",
        "assumptions",
        "abstractions",
        "limitations",
        "review_attestations",
        "evidence_graph",
        "decision",
        "decision_reasons",
    }
    report_fields = registry.get("report_fields", [])
    require(isinstance(report_fields, list), "report_fields is not an array", errors)
    if isinstance(report_fields, list):
        require(len(report_fields) == len(set(report_fields)), "duplicate report field", errors)
        require(
            set(report_fields) == required_report_fields,
            "report field set differs from the frozen set",
            errors,
        )

    for requirement_number in range(1, 47):
        requirement_id = f"FR-{requirement_number:03d}"
        require(requirement_id in coverage, f"coverage missing {requirement_id}", errors)

    for collection in (
        "invariants",
        "temporal_properties",
        "proof_obligations",
        "configs",
    ):
        for entry in registry.get(collection, []):
            if isinstance(entry, dict) and isinstance(entry.get("id"), str):
                require(
                    entry["id"] in coverage,
                    f"coverage missing {entry['id']}",
                    errors,
                )

    required_semantic_phrases = (
        "ViewChangeQC",
        "AbortQC",
        "OMIT_UNAVAILABLE",
        "ABORT_ON_INCOMPLETE",
        "remains BLOCKED",
    )
    for phrase in required_semantic_phrases:
        require(phrase in failure_semantics, f"failure semantics missing {phrase}", errors)
    require("ViewChangeCertified" in feature_spec, "spec missing ViewChangeCertified", errors)
    require("AbortCertified" in feature_spec, "spec missing AbortCertified", errors)

    status = "PASS" if not errors else "FAIL"
    result = {
        "schema_version": "1.0.0",
        "phase": "T000-T003",
        "status": status,
        "formal_semantics_version": registry.get("formal_semantics_version"),
        "input_bundle_sha256": actual_bundle_hash,
        "counts": counts,
        "errors": errors,
    }
    return result


def main() -> int:
    result = verify()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
