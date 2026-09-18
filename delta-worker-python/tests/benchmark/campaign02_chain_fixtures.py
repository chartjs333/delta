from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from deltatorrent.benchmark.campaign02 import (
    CampaignExecutionPlan,
    CertifiedRoundPolicy,
    ParameterShardKey,
    TicketAllocation,
    execution_authorization_id,
)
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.benchmark.feature008_admission import (
    CertificateArtifact,
    Feature008CertificateBundle,
    NativeChainAdmissionReceipt,
)
from deltatorrent.benchmark.measured_runner import (
    CertifiedRoundMeasurement,
    ComponentIdentity,
    RawArtifact,
    RunHandle,
    TicketContributionMeasurement,
)
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

ROOT = Path(__file__).resolve().parents[3]


def content_id(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode()).hexdigest()


class FixtureNativeChainVerifier:
    """Deterministic receipt issuer for non-primary Python preflight unit tests."""

    native_build_id = content_id("fixture-native-build")

    def verify(
        self,
        plan: CampaignExecutionPlan,
        result: CertifiedRoundMeasurement,
        canonical_bundle: bytes,
    ) -> NativeChainAdmissionReceipt:
        policy = plan.certified_round_policy
        assert policy is not None
        bundle = result.certificate_bundle
        native_identity = canonical_json_bytes(
            {
                "formal_semantics_id": FORMAL_SEMANTICS_ID,
                "native_build_id": self.native_build_id,
                "type_name": "DELTA_CERTIFICATE_CHAIN_VERIFIER",
            }
        )
        value = {
            "aggregate_root_qc_id": bundle.aggregate_root.content_id,
            "apply_qc_id": bundle.apply_qc.content_id,
            "certificate_bundle_id": sha256_content_id(
                b"deltareduce.010.native-chain-admission-bundle.v1\0" + canonical_bundle
            ),
            "certified_round_policy_id": policy.content_id,
            "checkpoint_wal_sha256": result.checkpoint_wal_sha256,
            "effect_set_id": result.effect_set_id,
            "execution_plan_id": plan.content_id,
            "final_checkpoint_id": result.final_checkpoint_id,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "input_set_certificate_id": bundle.input_set.content_id,
            "native_build_id": self.native_build_id,
            "native_chain_verifier_id": sha256_content_id(
                b"deltareduce.010.native-chain-verifier.v1\0" + native_identity
            ),
            "runtime_state_id": result.runtime_state_id,
            "runtime_wal_sha256": result.runtime_wal_sha256,
            "schema_version": "1.0.0",
            "status": "ACCEPT",
            "type_name": "CAMPAIGN02_NATIVE_CHAIN_ADMISSION_RECEIPT",
        }
        canonical = canonical_json_bytes(value)
        return NativeChainAdmissionReceipt(canonical, value)


def authorization() -> dict[str, object]:
    return json.loads(
        (
            ROOT / "reports/benchmark/campaigns/campaign-02/remediation-authorization.json"
        ).read_bytes()
    )


def component() -> ComponentIdentity:
    return ComponentIdentity(
        component="PRIMARY_SCIENTIFIC_RUNNER",
        source_commit="a" * 40,
        source_tree="b" * 40,
        executable_hashes=(("scientific.py", content_id("scientific.py")),),
        environment_id=content_id("environment"),
        image_id=content_id("image"),
        hardware_compatibility_class_id=content_id("hardware-class"),
        model_data_staging_policy_id=content_id("staging"),
        timeout_policy_id=content_id("timeout"),
        output_schema_ids=(content_id("observation-v2"),),
        create_only_store_policy_id=content_id("create-only"),
    )


def _apply_profile() -> CertificateArtifact:
    return CertificateArtifact.from_value(
        {
            "accumulator_proof_id": content_id("accumulator-proof"),
            "domain_weights": [{"domain_id": "domain", "pi": {"denominator": 1, "numerator": "1"}}],
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "learning_rate": {"denominator": 10, "numerator": "1"},
            "momentum": {"denominator": 10, "numerator": "9"},
            "nesterov": True,
            "rounding": "HALF_TOWARD_POSITIVE",
            "schema_version": "1.0.0",
            "type_name": "APPLY_ARITHMETIC_PROFILE",
            "weight_decay": {"denominator": 100, "numerator": "1"},
        }
    )


def certified_plan(ticket_count: int = 4) -> tuple[CampaignExecutionPlan, ComponentIdentity]:
    identity = component()
    apply_profile = _apply_profile()
    ticket_ids = sorted(content_id(f"ticket:{index}") for index in range(ticket_count))
    tickets = tuple(
        TicketAllocation(ticket_id, "domain", ordinal, 2, 2, 4)
        for ordinal, ticket_id in enumerate(ticket_ids)
    )
    policy = CertifiedRoundPolicy(
        round_id="campaign-02-certified-smoke",
        height=10,
        view=0,
        round_config_id=content_id("round-config"),
        validator_epoch_id=content_id("validator-epoch"),
        parameter_schema_id=content_id("parameter-schema"),
        arithmetic_profile_id=content_id("arithmetic-profile"),
        accumulator_proof_id=content_id("accumulator-proof"),
        apply_arithmetic_profile_id=apply_profile.content_id,
        validator_ids=("validator-0", "validator-1", "validator-2", "validator-3"),
        quorum_threshold=3,
        required_shards=(
            ParameterShardKey("domain", "shard-000"),
            ParameterShardKey("domain", "shard-001"),
        ),
    )
    return (
        CampaignExecutionPlan(
            execution_class="NON_PRIMARY_SMOKE",
            result_class="CERTIFIED_DELTAREDUCE",
            campaign_id="campaign-02",
            benchmark_definition_id=content_id("definition"),
            definition_attestation_id=content_id("attestation"),
            execution_authorization_id=execution_authorization_id(authorization()),
            arm_id=content_id("certified-arm"),
            round_id=policy.round_id,
            seed=17,
            repetition=1,
            source_commit="a" * 40,
            source_tree="b" * 40,
            environment_id=content_id("environment"),
            image_id=content_id("image"),
            hardware_id=content_id("hardware"),
            runner_id=identity.content_id,
            evaluation_runner_id=content_id("evaluation-runner"),
            writer_id=content_id("writer"),
            workload_id=content_id("workload"),
            tokens_per_optimizer_step=2,
            optimizer_steps_per_ticket=2,
            tokens_per_ticket=4,
            ticket_count=ticket_count,
            total_tokens_per_arm_run=4 * ticket_count,
            model_id=content_id("base-model"),
            parent_checkpoint_id=content_id("parent-checkpoint"),
            tokenizer_id=content_id("tokenizer"),
            dataset_ids=(content_id("dataset"),),
            evaluation_profile_ids=(content_id("evaluation-profile"),),
            evaluation_implementation_ids=(content_id("evaluation-implementation"),),
            tickets=tickets,
            certified_round_policy=policy,
        ),
        identity,
    )


def contributions(
    plan: CampaignExecutionPlan, *, duplicate_contribution: bool = False
) -> tuple[TicketContributionMeasurement, ...]:
    result = []
    for ticket in plan.tickets:
        ordinal = 0 if duplicate_contribution else ticket.ordinal
        result.append(
            TicketContributionMeasurement(
                ticket_id=ticket.ticket_id,
                domain_id=ticket.domain_id,
                processed_tokens=ticket.tokens_per_ticket,
                optimizer_steps=ticket.optimizer_steps,
                contribution_id=content_id(f"contribution:{ordinal}"),
                commitment_id=content_id(f"commitment:{ticket.ordinal}"),
                availability_certificate_id=content_id(f"availability:{ticket.ordinal}"),
                artifacts=(
                    RawArtifact(
                        f"ticket-{ticket.ordinal}.bin",
                        "application/octet-stream",
                        f"contribution:{ticket.ordinal}".encode(),
                    ),
                ),
            )
        )
    return tuple(result)


def _context(plan: CampaignExecutionPlan) -> dict[str, object]:
    policy = plan.certified_round_policy
    assert policy is not None
    return {
        "arithmetic_profile_id": policy.arithmetic_profile_id,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "height": policy.height,
        "parameter_schema_id": policy.parameter_schema_id,
        "round_config_id": policy.round_config_id,
        "round_id": policy.round_id,
        "schema_version": "1.0.0",
        "validator_epoch_id": policy.validator_epoch_id,
        "view": policy.view,
    }


def _qc(plan: CampaignExecutionPlan) -> dict[str, object]:
    policy = plan.certified_round_policy
    assert policy is not None
    return {
        "quorum_threshold": policy.quorum_threshold,
        "signer_ids": ["validator-0", "validator-1", "validator-2"],
    }


def _merkle_root(leaves: list[dict[str, object]]) -> str:
    level = [
        sha256_content_id(b"deltareduce.008.aggregate-leaf.v1\0" + canonical_json_bytes(leaf))
        for leaf in leaves
    ]
    while len(level) > 1:
        parent = []
        for index in range(0, len(level), 2):
            if index + 1 == len(level):
                parent.append(level[index])
            else:
                pair = bytes.fromhex(level[index][7:]) + bytes.fromhex(level[index + 1][7:])
                parent.append(sha256_content_id(b"deltareduce.008.aggregate-node.v1\0" + pair))
        level = parent
    return level[0]


def _artifact(type_name: str, value: dict[str, object]) -> CertificateArtifact:
    return CertificateArtifact.from_value({**value, "type_name": type_name})


def certified_result(
    plan: CampaignExecutionPlan,
    measured: tuple[TicketContributionMeasurement, ...],
    *,
    isc_members: tuple[Any, ...] | None = None,
    apc_isc_parent: str | None = None,
    shard_count: int | None = None,
    apply_root_parent: str | None = None,
    ordered_ticket_ids: tuple[str, ...] | None = None,
) -> CertifiedRoundMeasurement:
    policy = plan.certified_round_policy
    assert policy is not None
    members = measured if isc_members is None else isc_members
    tuples = sorted(
        (
            {
                "availability_certificate_id": item.availability_certificate_id,
                "commitment_id": item.commitment_id,
                "domain_id": item.domain_id,
                "ticket_id": item.ticket_id,
            }
            for item in members
        ),
        key=lambda item: (str(item["ticket_id"]), str(item["commitment_id"])),
    )
    context = _context(plan)
    qc = _qc(plan)
    input_set = _artifact(
        "INPUT_SET_CERTIFICATE",
        {
            **context,
            **qc,
            "input_root": content_id("input-root"),
            "tuples": tuples,
        },
    )
    seed = _artifact(
        "SEED_TRANSCRIPT",
        {
            **context,
            "input_set_certificate_id": input_set.content_id,
            "seed_id": content_id("seed"),
            "seed_profile_id": content_id("seed-profile"),
            "share_ids": sorted(content_id(f"share:{index}") for index in range(3)),
        },
    )
    norms = _artifact(
        "NORM_EVIDENCE",
        {
            **context,
            "entries": [
                {"scale_denominator": 1, "squared_norm": "1", "ticket_id": item["ticket_id"]}
                for item in tuples
            ],
            "input_set_certificate_id": input_set.content_id,
            "norm_root": content_id("norm-root"),
        },
    )
    eligibility = _artifact(
        "ELIGIBILITY_CERTIFICATE",
        {
            **context,
            **qc,
            "entries": [
                {
                    "accepted": True,
                    "domain_id": item["domain_id"],
                    "gamma": {"denominator": 1, "numerator": "1"},
                    "reason_code": "ACCEPTED",
                    "ticket_id": item["ticket_id"],
                }
                for item in tuples
            ],
            "input_set_certificate_id": input_set.content_id,
            "norm_evidence_id": norms.content_id,
            "robust_profile_id": content_id("robust-profile"),
        },
    )
    tickets = [str(item["ticket_id"]) for item in tuples]
    aggregation_plan = _artifact(
        "AGGREGATION_PLAN_CERTIFICATE",
        {
            **context,
            **qc,
            "accumulator_proof_id": policy.accumulator_proof_id,
            "bucket_assignments": [
                {"bucket_id": "bucket-0", "ticket_id": ticket_id} for ticket_id in tickets
            ],
            "eligibility_certificate_id": eligibility.content_id,
            "input_set_certificate_id": apc_isc_parent or input_set.content_id,
            "iteration_count": 1,
            "seed_transcript_id": seed.content_id,
            "transcript_root": content_id("transcript-root"),
            "weights": [
                {
                    "alpha": {"denominator": len(tickets), "numerator": "1"},
                    "ticket_id": ticket_id,
                }
                for ticket_id in tickets
            ],
        },
    )
    required = policy.required_shards
    selected = required if shard_count is None else required[:shard_count]
    shards = tuple(
        _artifact(
            "PARAMETER_SHARD_QC",
            {
                **context,
                **qc,
                "aggregation_plan_certificate_id": aggregation_plan.content_id,
                "denominator": 1,
                "domain_id": key.domain_id,
                "eligibility_certificate_id": eligibility.content_id,
                "input_leaf_ids": sorted(
                    content_id(f"leaf:{key.shard_id}:{index}") for index in range(2)
                ),
                "input_set_certificate_id": input_set.content_id,
                "result_numerators": ["1", "2"],
                "shard_id": key.shard_id,
            },
        )
        for key in selected
    )
    leaves = [
        {
            "domain_id": key.domain_id,
            "parameter_shard_qc_id": shard.content_id,
            "shard_id": key.shard_id,
        }
        for key, shard in zip(selected, shards, strict=True)
    ]
    root = _artifact(
        "AGGREGATE_ROOT_QC",
        {
            **context,
            **qc,
            "aggregation_plan_certificate_id": aggregation_plan.content_id,
            "eligibility_certificate_id": eligibility.content_id,
            "input_set_certificate_id": input_set.content_id,
            "leaves": leaves,
            "merkle_root": _merkle_root(leaves),
            "required_keys": [item.document for item in required],
        },
    )
    apply_profile = _apply_profile()
    final_checkpoint_id = content_id("final-checkpoint")
    next_optimizer_hash = content_id("next-optimizer")
    candidate = _artifact(
        "APPLY_CANDIDATE",
        {
            **context,
            "aggregate_root_qc_id": root.content_id,
            "apply_arithmetic_profile_id": apply_profile.content_id,
            "next_model_hash": final_checkpoint_id,
            "next_model_values": ["1", "2"],
            "next_optimizer_hash": next_optimizer_hash,
            "next_optimizer_values": ["0", "0"],
            "parent_checkpoint_id": plan.parent_checkpoint_id,
            "parent_optimizer_hash": content_id("parent-optimizer"),
        },
    )
    apply_qc = _artifact(
        "APPLY_QC",
        {
            **context,
            **qc,
            "aggregate_root_qc_id": apply_root_parent or root.content_id,
            "apply_arithmetic_profile_id": apply_profile.content_id,
            "apply_candidate_id": candidate.content_id,
            "next_model_hash": final_checkpoint_id,
            "next_optimizer_hash": next_optimizer_hash,
            "parent_checkpoint_id": plan.parent_checkpoint_id,
        },
    )
    pointer = _artifact(
        "CURRENT_POINTER_COMMAND",
        {
            **context,
            "apply_qc_id": apply_qc.content_id,
            "expected_parent_checkpoint_id": plan.parent_checkpoint_id,
            "next_checkpoint_id": final_checkpoint_id,
            "next_optimizer_hash": next_optimizer_hash,
        },
    )
    bundle = Feature008CertificateBundle(
        input_set,
        seed,
        norms,
        eligibility,
        aggregation_plan,
        shards,
        root,
        apply_profile,
        candidate,
        apply_qc,
        pointer,
    )
    common = {
        "apply_qc_id": apply_qc.content_id,
        "execution_plan_id": plan.content_id,
        "final_checkpoint_id": final_checkpoint_id,
        "parent_checkpoint_id": plan.parent_checkpoint_id,
        "round_id": plan.round_id,
        "schema_version": "1.0.0",
    }
    state = RawArtifact(
        "runtime-state.json",
        "application/json",
        canonical_json_bytes({**common, "type_name": "CERTIFIED_RUNTIME_STATE"}),
    )
    effects = RawArtifact(
        "effect-set.json",
        "application/json",
        canonical_json_bytes({**common, "type_name": "CERTIFIED_EFFECT_SET"}),
    )
    runtime_wal = RawArtifact("runtime.wal", "application/octet-stream", b"runtime-wal")
    checkpoint_wal = RawArtifact("checkpoint.wal", "application/octet-stream", b"checkpoint-wal")
    runtime_wal_sha256 = hashlib.sha256(runtime_wal.data).hexdigest()
    checkpoint_wal_sha256 = hashlib.sha256(checkpoint_wal.data).hexdigest()
    receipt = RawArtifact(
        "finalization-receipt.json",
        "application/json",
        canonical_json_bytes(
            {
                **common,
                "checkpoint_wal_sha256": checkpoint_wal_sha256,
                "effect_set_id": effects.content_id,
                "runtime_state_id": state.content_id,
                "runtime_wal_sha256": runtime_wal_sha256,
                "type_name": "CERTIFIED_FINALIZATION_RECEIPT",
            }
        ),
    )
    order = ordered_ticket_ids or tuple(item.ticket_id for item in measured)
    by_ticket = {item.ticket_id: item.contribution_id for item in measured}
    ordered_contributions = tuple(by_ticket[item] for item in order)
    return CertifiedRoundMeasurement(
        round_id=plan.round_id,
        parent_checkpoint_id=plan.parent_checkpoint_id,
        ordered_ticket_ids=order,
        ordered_contribution_ids=ordered_contributions,
        input_set_certificate_id=input_set.content_id,
        seed_transcript_id=seed.content_id,
        eligibility_certificate_id=eligibility.content_id,
        aggregation_plan_certificate_id=aggregation_plan.content_id,
        parameter_shard_qc_ids=tuple(item.content_id for item in shards),
        aggregate_root_qc_id=root.content_id,
        apply_qc_id=apply_qc.content_id,
        final_checkpoint_id=final_checkpoint_id,
        runtime_state_id=state.content_id,
        effect_set_id=effects.content_id,
        runtime_wal_sha256=runtime_wal_sha256,
        checkpoint_wal_sha256=checkpoint_wal_sha256,
        runtime_receipt_id=receipt.content_id,
        terminal_outcome="APPLIED",
        certificate_bundle=bundle,
        artifacts=(state, effects, runtime_wal, checkpoint_wal, receipt),
    )


@dataclass
class CertifiedBackend:
    plan: CampaignExecutionPlan
    measured: tuple[TicketContributionMeasurement, ...]
    finalized: Any
    source_class: str = "NON_PRIMARY_FIXTURE"
    result_class: str = "CERTIFIED_DELTAREDUCE"

    @property
    def environment_id(self) -> str:
        return self.plan.environment_id

    @property
    def model_id(self) -> str:
        return self.plan.model_id

    def begin_run(self, plan: CampaignExecutionPlan) -> RunHandle:
        return RunHandle(content_id("run-handle"), plan.content_id)

    def execute_ticket(
        self, _run: RunHandle, ticket: TicketAllocation
    ) -> TicketContributionMeasurement:
        return self.measured[ticket.ordinal]

    def finalize_run(
        self,
        _run: RunHandle,
        _contributions: tuple[TicketContributionMeasurement, ...],
    ) -> Any:
        return self.finalized


def extra_member() -> Any:
    return SimpleNamespace(
        ticket_id=content_id("unknown-ticket"),
        domain_id="domain",
        contribution_id=content_id("unknown-contribution"),
        commitment_id=content_id("unknown-commitment"),
        availability_certificate_id=content_id("unknown-availability"),
    )
