"""Generate source-sealed Campaign 02 domain/ticket identities and supersession record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Final

from deltatorrent.benchmark.campaign02 import (
    CampaignDomainManifest,
    build_ticket_plan,
    load_workload_contract,
)
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.protocol.canonical import canonical_json_bytes

ROOT: Final = Path(__file__).resolve().parents[3]
CONFIG: Final = ROOT / "configs/benchmark/campaign-02"
REPORTS: Final = ROOT / "reports/benchmark/campaigns/campaign-02"
DOMAIN_PATH: Final = CONFIG / "domain-manifest-v1.json"
TICKET_PLAN_PATH: Final = CONFIG / "ticket-plan-v1.json"
SUPERSESSION_PATH: Final = REPORTS / "definition-supersession-execution-binding.json"
QUALIFICATION_SUPERSESSION_PATH: Final = (
    REPORTS / "qualification-supersession-execution-binding.json"
)
STAGE_AUTHORIZATION_QUALIFICATION_SUPERSESSION_PATH: Final = (
    REPORTS / "qualification-supersession-stage-authorization.json"
)
SIGNED_STAGE_GOVERNANCE_QUALIFICATION_SUPERSESSION_PATH: Final = (
    REPORTS / "qualification-supersession-signed-stage-governance.json"
)
TSAN_EXCEPTION_LIFETIME_QUALIFICATION_SUPERSESSION_PATH: Final = (
    REPORTS / "qualification-supersession-tsan-exception-lifetime.json"
)
READINESS_PATH: Final = REPORTS / "execution-binding-remediation-readiness.json"
SUPERSEDED_DEFINITION_ID: Final = (
    "sha256:a4160af58ba310135bd86d03b2427c5034ae231f481e6229314e0e61d12b97af"
)
SUPERSEDED_ATTESTATION_ID: Final = (
    "sha256:6c59421bb773e4fe12a0df3414507682b93ae008ab04e75191292ab7a64b83f7"
)


class Campaign02BindingArtifactError(RuntimeError):
    """Stable generator/check rejection."""


def _load(path: Path) -> dict[str, object]:
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise Campaign02BindingArtifactError(f"CAMPAIGN02_OBJECT_INVALID:{path.name}")
    return value


def expected_outputs() -> dict[Path, bytes]:
    workload = load_workload_contract(CONFIG / "workload-v2.json")
    wikitext = _load(CONFIG / "evaluators/wikitext-v1.json")
    domain_value = {
        "campaign_id": "campaign-02",
        "domains": [
            {
                "dataset_id": wikitext["dataset_id"],
                "denominator": 1,
                "domain_id": "wikitext-en",
                "numerator": 1,
                "ticket_count": 32,
            }
        ],
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "schema_version": "1.0.0",
        "type_name": "CAMPAIGN_DOMAIN_MANIFEST",
    }
    domain_manifest = CampaignDomainManifest.from_dict(domain_value)
    ticket_plan = build_ticket_plan(workload, domain_manifest)
    supersession = {
        "authorization": {
            "benchmark_result_qc_authorized": False,
            "feature_011_authorized": False,
            "primary_execution_authorized": False,
            "real_wan_authorized": False,
            "stage_a_authorized": False,
            "stage_b_authorized": False,
            "stage_c_authorized": False,
        },
        "benchmark_result_qc": "ABSENT",
        "execution_authorization": "ABSENT",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "observation_counts": {
            "primary_observations": 0,
            "scientific_observations": 0,
            "stage_a_receipts": 0,
        },
        "reason_codes": [
            "QUALIFIED_PRIMARY_EXECUTION_PATH_NOT_BOUND_TO_CAMPAIGN02_WORKLOAD",
            "SYNTHETIC_SIGNER_LABELS_WITHOUT_SIGNATURE_EVIDENCE",
        ],
        "replacement_definition_required": True,
        "schema_version": "1.0.0",
        "status": "SUPERSEDED_BEFORE_EXECUTION",
        "superseded_attestation_id": SUPERSEDED_ATTESTATION_ID,
        "superseded_definition_id": SUPERSEDED_DEFINITION_ID,
        "type_name": "CAMPAIGN02_DEFINITION_SUPERSESSION",
    }
    qualification_supersession = {
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "primary_observations_created": 0,
        "reason": "QUALIFIED_PRIMARY_EXECUTION_PATH_NOT_BOUND_TO_CAMPAIGN02_WORKLOAD",
        "replacement_qualification_required": True,
        "schema_version": "1.0.0",
        "status": "SUPERSEDED_BEFORE_EXECUTION",
        "superseded_source": {
            "commit": "660710818a7a45708231ae03da78bac9bbc0abc9",
            "tree": "553f63928e13cf785798e8b1adfb53176e01629d",
        },
        "type_name": "CAMPAIGN02_SOURCE_QUALIFICATION_SUPERSESSION",
    }
    stage_authorization_qualification_supersession = {
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "primary_observations_created": 0,
        "reason_codes": [
            "SUPERSEDED_DEFINITION_V1_LEGACY_ROUTE_NOT_CENTRALLY_BLOCKED",
            "PLAN_CATALOG_AND_STAGE_EXECUTION_AUTHORIZATION_NOT_SEPARATED",
            "BINDER_TRUSTED_CALLER_CONSTRUCTED_ATTESTATION",
            "VOTE_SUBMITTED_AT_NOT_SIGNED",
        ],
        "replacement_qualification_required": True,
        "schema_version": "1.0.0",
        "status": "SUPERSEDED_AFTER_GOVERNANCE_REVIEW_BEFORE_EXECUTION",
        "superseded_evidence": {
            "ci_receipt_head": "0d5dcc8af0e2f8563a64a85346671e64dfeb94eb",
            "evidence_overlay": "2aaf2931d8c808354d69488f1da7171a0b9576a6",
            "source_commit": "d9b8230d373e484c8fbcdd0a0444ea0ee465e8c3",
            "source_tree": "c5591557d2ef6617a08f99c91a79e570c391d306",
        },
        "type_name": "CAMPAIGN02_SOURCE_QUALIFICATION_SUPERSESSION",
    }
    signed_stage_governance_qualification_supersession = {
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "primary_observations_created": 0,
        "reason_codes": [
            "STAGE_AUTHORIZATION_NOT_CRYPTOGRAPHICALLY_AUTHENTICATED",
            "PREDECESSOR_GATE_RECEIPTS_NOT_TYPED_OR_LINEAGE_VERIFIED",
            "RUNNER_ROLE_OPTIONAL",
            "STAGE_SPECIFIC_PLANS_REUSED_BFT_ROUND_CONTEXT",
        ],
        "replacement_qualification_required": True,
        "schema_version": "1.0.0",
        "status": "SUPERSEDED_AFTER_GOVERNANCE_REVIEW_BEFORE_EXECUTION",
        "superseded_evidence": {
            "ci_receipt_head": "04aad0c530aa8c83a76315f737e5caa36fe9b14e",
            "evidence_overlay": "68d2ddfed472e76197e0fcdfd29ee2a9ad601584",
            "source_commit": "b870c8a83ab89c694d1f3467804bafe5e08aac59",
            "source_tree": "1651bc3fd810ba7f47b32e1058f9c0e5d4e4cf92",
        },
        "type_name": "CAMPAIGN02_SOURCE_QUALIFICATION_SUPERSESSION",
    }
    tsan_exception_lifetime_qualification_supersession = {
        "failed_gate": {
            "check_name": "GCC TSan WAL and sidecar replay",
            "job_id": 100208818052,
            "summary": "RUNTIME_ERROR_FUTURE_SHARED_STATE_RELEASE_DATA_RACE",
            "workflow_run_id": 33618187137,
        },
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "primary_observations_created": 0,
        "reason_codes": [
            "RUNTIME_ERROR_EXCEPTION_LIFETIME_NOT_RETAINED_ACROSS_SYNCHRONOUS_FUTURE_GET",
            "REQUIRED_TSAN_GATE_FAILED",
        ],
        "replacement_qualification_required": True,
        "schema_version": "1.0.0",
        "status": "SUPERSEDED_AFTER_TSAN_FAILURE_BEFORE_EXECUTION",
        "superseded_evidence": {
            "ci_receipt_head": "1620d6b8e66abab338cd4c056b17d3a5662bd544",
            "ci_receipt_tree": "e9fe4f3a209b8898d96528255d6b90e7be3d415d",
            "evidence_overlay": "67d038375c172e0a14d7271d2bc0f82ea22e0458",
            "evidence_overlay_tree": "fbfdebe500d00bed39f9881614ea0d990e53fa8e",
            "source_commit": "90f4b46a81f6a9ba05e0e5f3c757d008b4bdfcd9",
            "source_tree": "e188e339ec6073dc9b431658fca95627e526a7bd",
        },
        "type_name": "CAMPAIGN02_SOURCE_QUALIFICATION_SUPERSESSION",
    }
    readiness = {
        "authorization": {
            "feature_011_authorized": False,
            "primary_execution_authorized": False,
            "real_wan_authorized": False,
            "result_qc_authorized": False,
            "stage_a_authorized": False,
            "stage_b_authorized": False,
            "stage_c_authorized": False,
        },
        "cryptographic_governance": {
            "definition_verifier_implemented": True,
            "independent_votes_present": 0,
            "private_keys_committed": False,
            "stage_authorization_verifier_implemented": True,
            "status": "IMPLEMENTED_AWAITING_EXTERNAL_VALIDATOR_ACTIONS",
        },
        "definition_created": False,
        "execution_authorization": "ABSENT",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "identity_bindings": {
            "all_distinct": len(
                {workload.content_id, domain_manifest.content_id, ticket_plan.content_id}
            )
            == 3,
            "domain_manifest_id": domain_manifest.content_id,
            "ticket_plan_id": ticket_plan.content_id,
            "workload_contract_id": workload.content_id,
        },
        "legacy_primary_path": "FORBIDDEN_BY_CAMPAIGN_AND_DEFINITION_ID_REGISTRY",
        "next_required_gate": "C2_021_TSAN_EXCEPTION_LIFETIME_REQUALIFICATION",
        "schema_version": "1.0.0",
        "status": "SOURCE_REMEDIATION_IN_PROGRESS_NO_EXECUTION",
        "type_name": "CAMPAIGN02_EXECUTION_BINDING_REMEDIATION_READINESS",
    }
    return {
        DOMAIN_PATH: canonical_json_bytes(domain_manifest.raw) + b"\n",
        TICKET_PLAN_PATH: canonical_json_bytes(ticket_plan.raw) + b"\n",
        SUPERSESSION_PATH: canonical_json_bytes(supersession) + b"\n",
        QUALIFICATION_SUPERSESSION_PATH: canonical_json_bytes(qualification_supersession) + b"\n",
        STAGE_AUTHORIZATION_QUALIFICATION_SUPERSESSION_PATH: canonical_json_bytes(
            stage_authorization_qualification_supersession
        )
        + b"\n",
        SIGNED_STAGE_GOVERNANCE_QUALIFICATION_SUPERSESSION_PATH: canonical_json_bytes(
            signed_stage_governance_qualification_supersession
        )
        + b"\n",
        TSAN_EXCEPTION_LIFETIME_QUALIFICATION_SUPERSESSION_PATH: canonical_json_bytes(
            tsan_exception_lifetime_qualification_supersession
        )
        + b"\n",
        READINESS_PATH: canonical_json_bytes(readiness) + b"\n",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    outputs = expected_outputs()
    if arguments.write:
        for path, value in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(value)
    else:
        for path, expected in outputs.items():
            if not path.is_file() or path.read_bytes() != expected:
                raise Campaign02BindingArtifactError(
                    f"CAMPAIGN02_EXECUTION_BINDING_OUTPUT_DRIFT:{path.name}"
                )
    print(
        canonical_json_bytes(
            {
                "output_count": len(outputs),
                "primary_execution_authorized": False,
                "status": "PASS",
            }
        ).decode()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
