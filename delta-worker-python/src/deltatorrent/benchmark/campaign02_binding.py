"""Compile one Campaign 02 Definition into its only admissible execution matrix."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Final

from deltatorrent.benchmark.arms import ArmSpec
from deltatorrent.benchmark.campaign02 import (
    CampaignDomainManifest,
    CampaignExecutionPlan,
    CampaignTicketPlan,
    CertifiedRoundPolicy,
    WorkloadContract,
    authorize_execution_class,
    execution_authorization_id,
)
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID, BenchmarkDefinition
from deltatorrent.benchmark.governance import VerifiedDefinitionAttestation
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

_CONTENT_ID: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_ID: Final = re.compile(r"^[0-9a-f]{40}$")
_EXPECTED_ARMS: Final = (
    ("scientific-reference", "SCIENTIFIC_REFERENCE", "PYTHON", "SINGLE_NODE_REFERENCE"),
    ("flat-embedded", "CERTIFIED_QLORA", "EMBEDDED_FFM", "FLAT_BFT"),
    (
        "hierarchy-embedded",
        "CERTIFIED_QLORA",
        "EMBEDDED_FFM",
        "HIERARCHICAL_BFT",
    ),
    ("flat-sidecar", "CERTIFIED_QLORA", "ISOLATED_SIDECAR", "FLAT_BFT"),
    (
        "hierarchy-sidecar",
        "CERTIFIED_QLORA",
        "ISOLATED_SIDECAR",
        "HIERARCHICAL_BFT",
    ),
)


class Campaign02BindingError(ValueError):
    """Stable fail-closed execution-binding rejection."""


def _fail(code: str) -> Campaign02BindingError:
    return Campaign02BindingError(code)


def _content_id(value: str, code: str) -> str:
    if _CONTENT_ID.fullmatch(value) is None:
        raise _fail(code)
    return value


@dataclass(frozen=True, slots=True)
class CertifiedPlanBinding:
    arm_id: str
    arm_name: str
    seed: int
    repetition: int
    policy: CertifiedRoundPolicy

    def __post_init__(self) -> None:
        _content_id(self.arm_id, "CAMPAIGN02_POLICY_ARM_ID_INVALID")
        if not self.arm_name or self.seed < 0 or self.repetition < 1:
            raise _fail("CAMPAIGN02_POLICY_COORDINATE_INVALID")
        if self.policy.round_id != expected_round_id(self.arm_name, self.seed, self.repetition):
            raise _fail("CAMPAIGN02_POLICY_ROUND_ID_MISMATCH")

    @property
    def document(self) -> dict[str, object]:
        return {
            "arm_id": self.arm_id,
            "arm_name": self.arm_name,
            "policy": self.policy.document,
            "repetition": self.repetition,
            "seed": self.seed,
        }


@dataclass(frozen=True, slots=True)
class QualifiedRuntimeLineage:
    source_commit: str
    source_tree: str
    environment_id: str
    image_id: str
    hardware_id: str
    runner_id: str
    evaluation_runner_id: str
    writer_id: str
    model_id: str
    parent_checkpoint_id: str
    tokenizer_id: str
    dataset_ids: tuple[str, ...]
    evaluation_profile_ids: tuple[str, ...]
    evaluation_implementation_ids: tuple[str, ...]
    certified_plan_bindings: tuple[CertifiedPlanBinding, ...]

    def __post_init__(self) -> None:
        if (
            _COMMIT_ID.fullmatch(self.source_commit) is None
            or _COMMIT_ID.fullmatch(self.source_tree) is None
        ):
            raise _fail("CAMPAIGN02_RUNTIME_LINEAGE_SOURCE_INVALID")
        identities = (
            self.environment_id,
            self.image_id,
            self.hardware_id,
            self.runner_id,
            self.evaluation_runner_id,
            self.writer_id,
            self.model_id,
            self.parent_checkpoint_id,
            self.tokenizer_id,
            *self.dataset_ids,
            *self.evaluation_profile_ids,
            *self.evaluation_implementation_ids,
        )
        if any(_CONTENT_ID.fullmatch(value) is None for value in identities):
            raise _fail("CAMPAIGN02_RUNTIME_LINEAGE_IDENTITY_INVALID")
        if not (
            len(self.dataset_ids)
            == len(self.evaluation_profile_ids)
            == len(self.evaluation_implementation_ids)
        ):
            raise _fail("CAMPAIGN02_RUNTIME_LINEAGE_EVALUATOR_COUNT_MISMATCH")
        if any(
            len(set(values)) != len(values)
            for values in (
                self.dataset_ids,
                self.evaluation_profile_ids,
                self.evaluation_implementation_ids,
            )
        ):
            raise _fail("CAMPAIGN02_RUNTIME_LINEAGE_IDENTITY_DUPLICATE")
        coordinates = tuple(
            (item.arm_id, item.seed, item.repetition) for item in self.certified_plan_bindings
        )
        if len(set(coordinates)) != len(coordinates):
            raise _fail("CAMPAIGN02_RUNTIME_LINEAGE_POLICY_DUPLICATE")
        if self.certified_plan_bindings != tuple(
            sorted(
                self.certified_plan_bindings,
                key=lambda item: (item.arm_name, item.repetition, item.seed),
            )
        ):
            raise _fail("CAMPAIGN02_RUNTIME_LINEAGE_POLICY_ORDER_INVALID")

    @property
    def document(self) -> dict[str, object]:
        return {
            "campaign_id": "campaign-02",
            "certified_plan_bindings": [item.document for item in self.certified_plan_bindings],
            "dataset_ids": list(self.dataset_ids),
            "environment_id": self.environment_id,
            "evaluation_implementation_ids": list(self.evaluation_implementation_ids),
            "evaluation_profile_ids": list(self.evaluation_profile_ids),
            "evaluation_runner_id": self.evaluation_runner_id,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "hardware_id": self.hardware_id,
            "image_id": self.image_id,
            "model_id": self.model_id,
            "parent_checkpoint_id": self.parent_checkpoint_id,
            "runner_id": self.runner_id,
            "schema_version": "1.0.0",
            "source_commit": self.source_commit,
            "source_tree": self.source_tree,
            "tokenizer_id": self.tokenizer_id,
            "type_name": "CAMPAIGN02_QUALIFIED_RUNTIME_LINEAGE",
            "writer_id": self.writer_id,
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            b"deltareduce.010.campaign02-qualified-runtime-lineage.v1\0"
            + canonical_json_bytes(self.document)
        )

    def policy_for(self, arm: ArmSpec, seed: int, repetition: int) -> CertifiedRoundPolicy:
        matches = tuple(
            item
            for item in self.certified_plan_bindings
            if item.arm_id == arm.content_id
            and item.arm_name == arm.arm_id
            and item.seed == seed
            and item.repetition == repetition
        )
        if len(matches) != 1:
            raise _fail("CAMPAIGN02_CERTIFIED_POLICY_MISSING")
        return matches[0].policy


@dataclass(frozen=True, slots=True)
class Campaign02ExecutionSet:
    definition_id: str
    attestation_id: str
    authorization_id: str
    workload_contract_id: str
    domain_manifest_id: str
    ticket_plan_id: str
    runtime_lineage_id: str
    plans: tuple[CampaignExecutionPlan, ...]

    @property
    def document(self) -> dict[str, object]:
        return {
            "authorization_id": self.authorization_id,
            "benchmark_definition_id": self.definition_id,
            "campaign_id": "campaign-02",
            "definition_attestation_id": self.attestation_id,
            "domain_manifest_id": self.domain_manifest_id,
            "execution_allowed": False,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "plan_ids": [item.content_id for item in self.plans],
            "qualified_runtime_lineage_id": self.runtime_lineage_id,
            "schema_version": "1.0.0",
            "status": "COMPILED_REQUIRES_SEPARATE_EXECUTION_INVOCATION",
            "ticket_plan_id": self.ticket_plan_id,
            "type_name": "CAMPAIGN02_EXECUTION_SET",
            "workload_contract_id": self.workload_contract_id,
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            b"deltareduce.010.campaign02-execution-set.v1\0" + canonical_json_bytes(self.document)
        )


def expected_round_id(arm_name: str, seed: int, repetition: int) -> str:
    return f"campaign-02:{arm_name}:{repetition}:{seed}"


def _validate_definition_bindings(
    definition: BenchmarkDefinition,
    workload: WorkloadContract,
    domain_manifest: CampaignDomainManifest,
    ticket_plan: CampaignTicketPlan,
    runtime_lineage: QualifiedRuntimeLineage,
) -> None:
    if (
        definition.raw.get("schema_version") != "2.0.0"
        or definition.campaign_id != "campaign-02"
        or not definition.primary
    ):
        raise _fail("CAMPAIGN02_DEFINITION_V2_REQUIRED")
    if (
        definition.B != workload.tokens_per_ticket
        or definition.H != workload.optimizer_steps_per_ticket
    ):
        raise _fail("CAMPAIGN02_DEFINITION_WORKLOAD_ARITHMETIC_MISMATCH")
    if (
        definition.workload_contract_id != workload.content_id
        or definition.raw["domain_manifest_id"] != domain_manifest.content_id
        or definition.ticket_plan_id != ticket_plan.content_id
        or definition.qualified_runtime_lineage_id != runtime_lineage.content_id
    ):
        raise _fail("CAMPAIGN02_DEFINITION_EXECUTION_BINDING_MISMATCH")
    if len({workload.content_id, domain_manifest.content_id, ticket_plan.content_id}) != 3:
        raise _fail("CAMPAIGN02_DEFINITION_EXECUTION_BINDING_ALIAS")
    if (
        definition.source_commit != runtime_lineage.source_commit
        or definition.source_tree != runtime_lineage.source_tree
        or definition.raw["image_id"] != runtime_lineage.image_id
        or definition.base_model_id != runtime_lineage.parent_checkpoint_id
        or definition.raw["tokenizer_id"] != runtime_lineage.tokenizer_id
        or definition.evaluation_ids != runtime_lineage.evaluation_implementation_ids
    ):
        raise _fail("CAMPAIGN02_DEFINITION_RUNTIME_LINEAGE_MISMATCH")
    manifest_datasets = tuple(item.dataset_id for item in domain_manifest.domains)
    if not set(manifest_datasets) <= set(runtime_lineage.dataset_ids):
        raise _fail("CAMPAIGN02_DEFINITION_DATASET_LINEAGE_MISMATCH")


def _validate_arms(
    definition: BenchmarkDefinition, arms: tuple[ArmSpec, ...], workload: WorkloadContract
) -> None:
    if len(arms) != 5 or tuple(item.content_id for item in arms) != definition.arm_ids:
        raise _fail("CAMPAIGN02_ARM_MATRIX_MISMATCH")
    observed = tuple(
        (item.arm_id, item.kind, item.deployment_profile, item.topology) for item in arms
    )
    if observed != _EXPECTED_ARMS or any(
        not item.mandatory or item.workload_identity != workload.content_id for item in arms
    ):
        raise _fail("CAMPAIGN02_ARM_MATRIX_MISMATCH")


def _validate_authorization(
    authorization: dict[str, Any] | None,
    definition: BenchmarkDefinition,
    attestation: VerifiedDefinitionAttestation,
    workload: WorkloadContract,
    domain_manifest: CampaignDomainManifest,
    ticket_plan: CampaignTicketPlan,
    runtime_lineage: QualifiedRuntimeLineage,
) -> dict[str, Any]:
    if authorization is None:
        raise _fail("CAMPAIGN02_EXECUTION_AUTHORIZATION_REQUIRED")
    expected = {
        "benchmark_definition_id": definition.content_id,
        "campaign_id": "campaign-02",
        "definition_attestation_id": attestation.content_id,
        "domain_manifest_id": domain_manifest.content_id,
        "environment_id": runtime_lineage.environment_id,
        "evaluation_runner_id": runtime_lineage.evaluation_runner_id,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "observation_writer_id": runtime_lineage.writer_id,
        "primary_execution_authorized": True,
        "qualified_runtime_lineage_id": runtime_lineage.content_id,
        "scientific_runner_id": runtime_lineage.runner_id,
        "source_commit": runtime_lineage.source_commit,
        "source_tree": runtime_lineage.source_tree,
        "ticket_plan_id": ticket_plan.content_id,
        "type_name": "BENCHMARK_EXECUTION_AUTHORIZATION",
        "workload_contract_id": workload.content_id,
    }
    if any(authorization.get(key) != value for key, value in expected.items()):
        raise _fail("CAMPAIGN02_EXECUTION_AUTHORIZATION_BINDING_MISMATCH")
    return authorization


def compile_campaign02_execution_set(
    *,
    definition: BenchmarkDefinition,
    attestation: VerifiedDefinitionAttestation,
    authorization: dict[str, Any] | None,
    workload: WorkloadContract,
    domain_manifest: CampaignDomainManifest,
    ticket_plan: CampaignTicketPlan,
    arms: tuple[ArmSpec, ...],
    runtime_lineage: QualifiedRuntimeLineage,
) -> Campaign02ExecutionSet:
    """Create the exact 5-arm x 3-seed matrix after every identity is verified."""
    _validate_definition_bindings(
        definition, workload, domain_manifest, ticket_plan, runtime_lineage
    )
    _validate_arms(definition, arms, workload)
    if (
        attestation.benchmark_definition_id != definition.content_id
        or len(attestation.ordered_vote_ids) != attestation.quorum_threshold
    ):
        raise _fail("CAMPAIGN02_DEFINITION_ATTESTATION_MISMATCH")
    authorization_value = _validate_authorization(
        authorization,
        definition,
        attestation,
        workload,
        domain_manifest,
        ticket_plan,
        runtime_lineage,
    )
    authorization_id = execution_authorization_id(authorization_value)
    plans: list[CampaignExecutionPlan] = []
    for arm in arms:
        result_class = (
            "REFERENCE" if arm.arm_id == "scientific-reference" else "CERTIFIED_DELTAREDUCE"
        )
        for repetition, seed in enumerate(definition.seeds, start=1):
            policy = (
                None
                if result_class == "REFERENCE"
                else runtime_lineage.policy_for(arm, seed, repetition)
            )
            plan = CampaignExecutionPlan(
                execution_class="PRIMARY_MEASURED",
                result_class=result_class,
                campaign_id="campaign-02",
                benchmark_definition_id=definition.content_id,
                definition_attestation_id=attestation.content_id,
                execution_authorization_id=authorization_id,
                arm_id=arm.content_id,
                round_id=expected_round_id(arm.arm_id, seed, repetition),
                seed=seed,
                repetition=repetition,
                source_commit=runtime_lineage.source_commit,
                source_tree=runtime_lineage.source_tree,
                environment_id=runtime_lineage.environment_id,
                image_id=runtime_lineage.image_id,
                hardware_id=runtime_lineage.hardware_id,
                runner_id=runtime_lineage.runner_id,
                evaluation_runner_id=runtime_lineage.evaluation_runner_id,
                writer_id=runtime_lineage.writer_id,
                workload_id=workload.content_id,
                tokens_per_optimizer_step=workload.tokens_per_optimizer_step,
                optimizer_steps_per_ticket=workload.optimizer_steps_per_ticket,
                tokens_per_ticket=workload.tokens_per_ticket,
                ticket_count=workload.ticket_count,
                total_tokens_per_arm_run=workload.total_tokens_per_arm_run,
                model_id=runtime_lineage.model_id,
                parent_checkpoint_id=runtime_lineage.parent_checkpoint_id,
                tokenizer_id=runtime_lineage.tokenizer_id,
                dataset_ids=runtime_lineage.dataset_ids,
                evaluation_profile_ids=runtime_lineage.evaluation_profile_ids,
                evaluation_implementation_ids=runtime_lineage.evaluation_implementation_ids,
                tickets=ticket_plan.tickets,
                certified_round_policy=policy,
                domain_manifest_id=domain_manifest.content_id,
                ticket_plan_id=ticket_plan.content_id,
                qualified_runtime_lineage_id=runtime_lineage.content_id,
            )
            authorize_execution_class(authorization_value, plan)
            plans.append(plan)
    expected_policy_count = 4 * len(definition.seeds)
    if (
        len(plans) != 15
        or len({item.content_id for item in plans}) != 15
        or len(runtime_lineage.certified_plan_bindings) != expected_policy_count
    ):
        raise _fail("CAMPAIGN02_EXECUTION_MATRIX_INCOMPLETE")
    return Campaign02ExecutionSet(
        definition_id=definition.content_id,
        attestation_id=attestation.content_id,
        authorization_id=authorization_id,
        workload_contract_id=workload.content_id,
        domain_manifest_id=domain_manifest.content_id,
        ticket_plan_id=ticket_plan.content_id,
        runtime_lineage_id=runtime_lineage.content_id,
        plans=tuple(plans),
    )
