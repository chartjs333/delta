"""Tiny deterministic end-to-end slice used to qualify the benchmark control plane."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from deltatorrent.benchmark.arms import ArmSpec
from deltatorrent.benchmark.attacks import synthetic_rejection_corpus
from deltatorrent.benchmark.decision import BenchmarkResult, GateResult, decide
from deltatorrent.benchmark.definition import BenchmarkDefinition
from deltatorrent.benchmark.efficiency import analyze_efficiency
from deltatorrent.benchmark.evidence import EvidenceBundle, EvidenceCollector
from deltatorrent.benchmark.orchestrator import ExperimentOrchestrator
from deltatorrent.benchmark.preregistration import (
    PreregisteredDefinition,
    PreregistrationStore,
)
from deltatorrent.benchmark.quality import analyze_quality
from deltatorrent.benchmark.reconciliation import reconcile
from deltatorrent.benchmark.resilience import analyze_resilience, synthetic_scenarios
from deltatorrent.benchmark.review import GovernanceAttestation, GovernanceVote
from deltatorrent.benchmark.safety import analyze_safety
from deltatorrent.benchmark.verifier import OfflineVerifier, VerificationResult


class SyntheticSliceError(ValueError):
    """Stable fixture or vertical-slice construction error."""


@dataclass(frozen=True, slots=True)
class SyntheticSliceResult:
    benchmark_result: BenchmarkResult
    definition_attestation: GovernanceAttestation
    result_attestation: GovernanceAttestation
    evidence_bundle: EvidenceBundle
    verification: VerificationResult
    run_count: int
    fixture_class: str = "SYNTHETIC_NOT_PRIMARY_EVIDENCE"


def _load_artifacts(path: Path) -> dict[str, dict[str, Any]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SyntheticSliceError("SYNTHETIC_FIXTURE_INVALID") from exc
    artifacts = value.get("artifacts") if isinstance(value, dict) else None
    if not isinstance(artifacts, dict) or any(
        not isinstance(item, dict) for item in artifacts.values()
    ):
        raise SyntheticSliceError("SYNTHETIC_FIXTURE_INVALID")
    return artifacts


def _attest(
    body_id: str,
    purpose: str,
    member_prefix: str,
) -> GovernanceAttestation:
    if purpose not in {"DEFINITION", "RESULT"}:
        raise SyntheticSliceError("ATTESTATION_PURPOSE_INVALID")
    validator_ids = tuple(f"{member_prefix}-{index}" for index in range(4))
    validator_set_id = "sha256:" + ("4" if purpose == "DEFINITION" else "5") * 64
    typed_purpose: Literal["DEFINITION", "RESULT"] = (
        "DEFINITION" if purpose == "DEFINITION" else "RESULT"
    )
    votes = tuple(
        GovernanceVote(signer, validator_set_id, body_id, typed_purpose)
        for signer in validator_ids[:3]
    )
    return GovernanceAttestation.finalize(
        body_id=body_id,
        validator_set_id=validator_set_id,
        purpose=typed_purpose,
        validator_ids=validator_ids,
        f_b=1,
        votes=votes,
    )


def execute_synthetic_fixture(fixture_path: Path, output_root: Path) -> SyntheticSliceResult:
    artifacts = _load_artifacts(fixture_path)
    definition = BenchmarkDefinition.from_dict(artifacts["definition"]["value"])
    if definition.primary:
        raise SyntheticSliceError("PRIMARY_DEFINITION_NOT_ALLOWED_IN_SYNTHETIC_SLICE")
    arms = tuple(
        ArmSpec.from_wrapper(artifacts[key])
        for key in ("arm_reference", "arm_embedded", "arm_sidecar")
    )
    definition_attestation = _attest(definition.content_id, "DEFINITION", "reviewer")
    preregistration = PreregisteredDefinition(definition, definition_attestation)
    PreregistrationStore(output_root / "definitions").seal(preregistration)
    environment_id = artifacts["environment"].get("content_id")
    if not isinstance(environment_id, str):
        raise SyntheticSliceError("ENVIRONMENT_FIXTURE_ID_INVALID")
    orchestration = ExperimentOrchestrator().execute(
        preregistration,
        arms,
        environment_manifest_id=environment_id,
    )
    reconciliation = reconcile(definition, orchestration.runs)
    quality = analyze_quality(definition, definition.content_id, orchestration.runs, reconciliation)
    safety = analyze_safety(
        definition.content_id,
        orchestration.runs,
        synthetic_rejection_corpus(),
        formal_regression_passed=True,
    )
    efficiency = analyze_efficiency(definition, definition.content_id, orchestration.runs)
    resilience = analyze_resilience(definition.content_id, synthetic_scenarios())
    formal = {
        "benchmark_definition_id": definition.content_id,
        "classification": "REGRESSION_ONLY",
        "formal_go_overlay_commit": "7abd0f43f8f1b15ec9aa6c3d2c80b32bfb4a6eca",
        "formal_report_id": definition.raw["formal_report_id"],
        "formal_semantics_id": definition.raw["formal_semantics_id"],
        "formal_source_commit": "1e6e0f6f70056161d95933e71494ec390c7c1151",
        "regression_report_id": "sha256:" + "6" * 64,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "status": "PASS",
        "type_name": "FORMAL_EVIDENCE",
    }
    collector = EvidenceCollector(output_root / "objects")
    bundle = collector.collect(
        definition_id=definition.content_id,
        runs=orchestration.runs,
        quality=quality.document,
        safety=safety.document,
        efficiency=efficiency.document,
        resilience=resilience.document,
        formal=formal,
    )
    verification = OfflineVerifier(output_root / "objects").verify(bundle)
    profiles = {item.deployment_profile for item in arms}
    gates = (
        GateResult("EVIDENCE", True, verification.status, "OFFLINE_VERIFIED"),
        GateResult("FORMAL_REGRESSION", True, "PASS", "INHERITED_GO_EXACT"),
        GateResult(
            "PROCESS_ISOLATION",
            True,
            "PASS" if {"EMBEDDED_FFM", "ISOLATED_SIDECAR"} <= profiles else "FAIL",
            "BOTH_PROFILES_EXECUTED",
        ),
        GateResult("PROTOCOL_EXACTNESS", True, safety.status, "HASH_AND_ATTACK_GATE"),
        GateResult("QUALITY", True, quality.status, "TOKEN_DOMAIN_MATCHED"),
        GateResult("RESILIENCE", True, resilience.status, "COMPLETE_OR_SAFE_ABORT"),
        GateResult("WAN_P2P", True, efficiency.status, "SYNTHETIC_ACCOUNTING"),
    )
    result = decide(
        definition_id=definition.content_id,
        evidence_manifest_id=bundle.manifest_ref.content_id,
        run_ids=bundle.run_ids,
        gates=gates,
        limitations=("SYNTHETIC_FIXTURE_NOT_PRIMARY_EVIDENCE",),
    )
    result_attestation = _attest(result.content_id, "RESULT", "evaluator")
    return SyntheticSliceResult(
        benchmark_result=result,
        definition_attestation=definition_attestation,
        result_attestation=result_attestation,
        evidence_bundle=bundle,
        verification=verification,
        run_count=len(orchestration.runs),
    )
