"""Compile one Campaign 02 Definition into its only admissible execution matrix."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime
from typing import Final

from deltatorrent.benchmark.arms import ArmSpec
from deltatorrent.benchmark.campaign02 import (
    CAMPAIGN02_GATE_STAGES,
    CampaignDomainManifest,
    CampaignExecutionPlan,
    CampaignTicketPlan,
    CertifiedRoundPolicy,
    WorkloadContract,
)
from deltatorrent.benchmark.campaign02_execution_identities import (
    StageExecutionIdentityManifest,
)
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID, BenchmarkDefinition
from deltatorrent.benchmark.governance import (
    BenchmarkReviewValidatorSet,
    SignedDefinitionVote,
    verify_definition_attestation,
)
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
_SUPERSEDED_DEFINITION_IDS: Final = frozenset(
    {
        "sha256:b263e77766599426dbf13574b05f2104ace1acf2d866e6ca5d9a3abef66f5dd5",
    }
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
    gate_stage: str
    arm_id: str
    arm_name: str
    seed: int
    repetition: int
    policy: CertifiedRoundPolicy

    def __post_init__(self) -> None:
        if self.gate_stage not in CAMPAIGN02_GATE_STAGES:
            raise _fail("CAMPAIGN02_POLICY_GATE_STAGE_INVALID")
        _content_id(self.arm_id, "CAMPAIGN02_POLICY_ARM_ID_INVALID")
        if not self.arm_name or self.seed < 0 or self.repetition < 1:
            raise _fail("CAMPAIGN02_POLICY_COORDINATE_INVALID")
        if self.policy.round_id != expected_round_id(
            self.gate_stage, self.arm_name, self.seed, self.repetition
        ):
            raise _fail("CAMPAIGN02_POLICY_ROUND_ID_MISMATCH")

    @classmethod
    def from_dict(cls, value: object) -> CertifiedPlanBinding:
        fields = {"arm_id", "arm_name", "gate_stage", "policy", "repetition", "seed"}
        if not isinstance(value, dict) or set(value) != fields:
            raise _fail("CAMPAIGN02_POLICY_BINDING_FIELDS_INVALID")
        seed = value["seed"]
        repetition = value["repetition"]
        if (
            isinstance(seed, bool)
            or not isinstance(seed, int)
            or seed < 0
            or isinstance(repetition, bool)
            or not isinstance(repetition, int)
            or repetition < 1
        ):
            raise _fail("CAMPAIGN02_POLICY_COORDINATE_INVALID")
        result = cls(
            gate_stage=str(value["gate_stage"]),
            arm_id=str(value["arm_id"]),
            arm_name=str(value["arm_name"]),
            seed=seed,
            repetition=repetition,
            policy=CertifiedRoundPolicy.from_dict(value["policy"]),
        )
        if result.document != value:
            raise _fail("CAMPAIGN02_POLICY_BINDING_DOCUMENT_MISMATCH")
        return result

    @property
    def document(self) -> dict[str, object]:
        return {
            "arm_id": self.arm_id,
            "arm_name": self.arm_name,
            "gate_stage": self.gate_stage,
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
    runner_id: str | None
    evaluation_runner_id: str
    writer_id: str
    model_id: str
    parent_checkpoint_id: str
    tokenizer_id: str
    dataset_ids: tuple[str, ...]
    evaluation_profile_ids: tuple[str, ...]
    evaluation_implementation_ids: tuple[str, ...]
    certified_plan_bindings: tuple[CertifiedPlanBinding, ...]
    stage_execution_identities_id: str | None = None
    exactness_runner_id: str | None = None
    scientific_runner_id: str | None = None
    network_fault_runner_id: str | None = None

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
        legacy = self.runner_id is not None and all(
            value is None
            for value in (
                self.stage_execution_identities_id,
                self.exactness_runner_id,
                self.scientific_runner_id,
                self.network_fault_runner_id,
            )
        )
        stage_specific = self.runner_id is None and all(
            value is not None
            for value in (
                self.stage_execution_identities_id,
                self.exactness_runner_id,
                self.scientific_runner_id,
                self.network_fault_runner_id,
            )
        )
        if not (legacy or stage_specific):
            raise _fail("CAMPAIGN02_RUNTIME_LINEAGE_RUNNER_SCHEMA_INVALID")
        runner_ids = (
            (self.runner_id,)
            if legacy
            else (
                self.stage_execution_identities_id,
                self.exactness_runner_id,
                self.scientific_runner_id,
                self.network_fault_runner_id,
            )
        )
        if any(
            not isinstance(value, str) or _CONTENT_ID.fullmatch(value) is None
            for value in runner_ids
        ):
            raise _fail("CAMPAIGN02_RUNTIME_LINEAGE_IDENTITY_INVALID")
        if (
            stage_specific
            and len(
                {
                    self.exactness_runner_id,
                    self.scientific_runner_id,
                    self.network_fault_runner_id,
                }
            )
            != 3
        ):
            raise _fail("CAMPAIGN02_RUNTIME_LINEAGE_STAGE_RUNNER_ALIAS")
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
            (item.gate_stage, item.arm_id, item.seed, item.repetition)
            for item in self.certified_plan_bindings
        )
        if len(set(coordinates)) != len(coordinates):
            raise _fail("CAMPAIGN02_RUNTIME_LINEAGE_POLICY_DUPLICATE")
        if self.certified_plan_bindings != tuple(
            sorted(
                self.certified_plan_bindings,
                key=lambda item: (
                    item.gate_stage,
                    item.arm_name,
                    item.repetition,
                    item.seed,
                ),
            )
        ):
            raise _fail("CAMPAIGN02_RUNTIME_LINEAGE_POLICY_ORDER_INVALID")

    @classmethod
    def from_dict(cls, value: object) -> QualifiedRuntimeLineage:
        fields = {
            "campaign_id",
            "certified_plan_bindings",
            "dataset_ids",
            "environment_id",
            "evaluation_implementation_ids",
            "evaluation_profile_ids",
            "evaluation_runner_id",
            "exactness_runner_id",
            "formal_semantics_id",
            "hardware_id",
            "image_id",
            "model_id",
            "network_fault_runner_id",
            "parent_checkpoint_id",
            "schema_version",
            "scientific_runner_id",
            "source_commit",
            "source_tree",
            "stage_execution_identities_id",
            "stage_execution_model",
            "tokenizer_id",
            "type_name",
            "writer_id",
        }
        if (
            not isinstance(value, dict)
            or set(value) != fields
            or value["campaign_id"] != "campaign-02"
            or value["schema_version"] != "3.0.0"
            or value["type_name"] != "CAMPAIGN02_QUALIFIED_RUNTIME_LINEAGE"
            or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
            or value["stage_execution_model"] != "INDEPENDENT_BFT_RUNS"
        ):
            raise _fail("CAMPAIGN02_RUNTIME_LINEAGE_V3_FIELDS_INVALID")

        def strings(name: str) -> tuple[str, ...]:
            raw = value[name]
            if not isinstance(raw, list) or any(not isinstance(item, str) for item in raw):
                raise _fail("CAMPAIGN02_RUNTIME_LINEAGE_IDENTITY_INVALID")
            return tuple(raw)

        raw_bindings = value["certified_plan_bindings"]
        if not isinstance(raw_bindings, list):
            raise _fail("CAMPAIGN02_RUNTIME_LINEAGE_POLICY_INVALID")
        result = cls(
            source_commit=str(value["source_commit"]),
            source_tree=str(value["source_tree"]),
            environment_id=str(value["environment_id"]),
            image_id=str(value["image_id"]),
            hardware_id=str(value["hardware_id"]),
            runner_id=None,
            evaluation_runner_id=str(value["evaluation_runner_id"]),
            writer_id=str(value["writer_id"]),
            model_id=str(value["model_id"]),
            parent_checkpoint_id=str(value["parent_checkpoint_id"]),
            tokenizer_id=str(value["tokenizer_id"]),
            dataset_ids=strings("dataset_ids"),
            evaluation_profile_ids=strings("evaluation_profile_ids"),
            evaluation_implementation_ids=strings("evaluation_implementation_ids"),
            certified_plan_bindings=tuple(
                CertifiedPlanBinding.from_dict(item) for item in raw_bindings
            ),
            stage_execution_identities_id=str(value["stage_execution_identities_id"]),
            exactness_runner_id=str(value["exactness_runner_id"]),
            scientific_runner_id=str(value["scientific_runner_id"]),
            network_fault_runner_id=str(value["network_fault_runner_id"]),
        )
        if result.document != value:
            raise _fail("CAMPAIGN02_RUNTIME_LINEAGE_V3_DOCUMENT_MISMATCH")
        return result

    @property
    def document(self) -> dict[str, object]:
        document: dict[str, object] = {
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
            "stage_execution_model": "INDEPENDENT_BFT_RUNS",
            "source_commit": self.source_commit,
            "source_tree": self.source_tree,
            "tokenizer_id": self.tokenizer_id,
            "type_name": "CAMPAIGN02_QUALIFIED_RUNTIME_LINEAGE",
            "writer_id": self.writer_id,
        }
        if self.runner_id is not None:
            document.update({"runner_id": self.runner_id, "schema_version": "2.0.0"})
        else:
            document.update(
                {
                    "exactness_runner_id": self.exactness_runner_id,
                    "network_fault_runner_id": self.network_fault_runner_id,
                    "schema_version": "3.0.0",
                    "scientific_runner_id": self.scientific_runner_id,
                    "stage_execution_identities_id": self.stage_execution_identities_id,
                }
            )
        return document

    @property
    def content_id(self) -> str:
        version = b"v2" if self.runner_id is not None else b"v3"
        return sha256_content_id(
            b"deltareduce.010.campaign02-qualified-runtime-lineage."
            + version
            + b"\0"
            + canonical_json_bytes(self.document)
        )

    def runner_id_for_stage(self, gate_stage: str) -> str:
        if self.runner_id is not None:
            return self.runner_id
        mapping = {
            "STAGE_A_EXACTNESS": self.exactness_runner_id,
            "STAGE_B_SCIENTIFIC": self.scientific_runner_id,
            "STAGE_C_EMULATED_WAN": self.network_fault_runner_id,
        }
        value = mapping.get(gate_stage)
        if not isinstance(value, str):
            raise _fail("CAMPAIGN02_RUNTIME_LINEAGE_STAGE_RUNNER_MISSING")
        return value

    def policy_for(
        self, gate_stage: str, arm: ArmSpec, seed: int, repetition: int
    ) -> CertifiedRoundPolicy:
        matches = tuple(
            item
            for item in self.certified_plan_bindings
            if item.gate_stage == gate_stage
            and item.arm_id == arm.content_id
            and item.arm_name == arm.arm_id
            and item.seed == seed
            and item.repetition == repetition
        )
        if len(matches) != 1:
            raise _fail("CAMPAIGN02_CERTIFIED_POLICY_MISSING")
        return matches[0].policy


@dataclass(frozen=True, slots=True)
class Campaign02PlanCatalog:
    definition_id: str
    attestation_id: str
    workload_contract_id: str
    domain_manifest_id: str
    ticket_plan_id: str
    runtime_lineage_id: str
    stage_execution_identities_id: str
    gate_analyzer_id: str
    definition_attestation_verified_at: datetime
    plans: tuple[CampaignExecutionPlan, ...]

    def __post_init__(self) -> None:
        expected_count = 15 * len(CAMPAIGN02_GATE_STAGES)
        if (
            _CONTENT_ID.fullmatch(self.gate_analyzer_id) is None
            or _CONTENT_ID.fullmatch(self.stage_execution_identities_id) is None
            or _CONTENT_ID.fullmatch(self.runtime_lineage_id) is None
            or len(self.plans) != expected_count
            or len({item.content_id for item in self.plans}) != expected_count
            or any(len(self.plan_ids_for_stage(stage)) != 15 for stage in CAMPAIGN02_GATE_STAGES)
        ):
            raise _fail("CAMPAIGN02_PLAN_CATALOG_INCOMPLETE")
        certified_contexts = tuple(
            (
                item.round_id,
                item.certified_round_policy.height,
                item.certified_round_policy.view,
                item.certified_round_policy.validator_epoch_id,
            )
            for item in self.plans
            if item.certified_round_policy is not None
        )
        if len(certified_contexts) != 36 or len(set(certified_contexts)) != 36:
            raise _fail("CAMPAIGN02_DUPLICATE_BFT_ROUND_CONTEXT")

    def plan_ids_for_stage(self, stage: str) -> tuple[str, ...]:
        if stage not in CAMPAIGN02_GATE_STAGES:
            raise _fail("CAMPAIGN02_PLAN_GATE_STAGE_INVALID")
        return tuple(item.content_id for item in self.plans if item.gate_stage == stage)

    @property
    def document(self) -> dict[str, object]:
        return {
            "base_plan_count": 15,
            "benchmark_definition_id": self.definition_id,
            "campaign_id": "campaign-02",
            "definition_attestation_id": self.attestation_id,
            "definition_attestation_verified_at": (
                self.definition_attestation_verified_at.isoformat().replace("+00:00", "Z")
            ),
            "domain_manifest_id": self.domain_manifest_id,
            "execution_authorized": False,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "gate_analyzer_id": self.gate_analyzer_id,
            "plan_ids": [item.content_id for item in self.plans],
            "plan_ids_by_stage": {
                stage: list(self.plan_ids_for_stage(stage)) for stage in CAMPAIGN02_GATE_STAGES
            },
            "qualified_runtime_lineage_id": self.runtime_lineage_id,
            "schema_version": "3.0.0",
            "stage_execution_model": "INDEPENDENT_BFT_RUNS",
            "stage_execution_identities_id": self.stage_execution_identities_id,
            "status": "COMPILED_NOT_EXECUTABLE_REQUIRES_STAGE_AUTHORIZATION",
            "ticket_plan_id": self.ticket_plan_id,
            "ticket_identity_scope": "ROUND_ID_PLUS_TICKET_TEMPLATE_ID",
            "type_name": "CAMPAIGN02_PLAN_CATALOG",
            "workload_contract_id": self.workload_contract_id,
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            b"deltareduce.010.campaign02-plan-catalog.v3\0" + canonical_json_bytes(self.document)
        )


def expected_round_id(gate_stage: str, arm_name: str, seed: int, repetition: int) -> str:
    if gate_stage not in CAMPAIGN02_GATE_STAGES:
        raise _fail("CAMPAIGN02_PLAN_GATE_STAGE_INVALID")
    return f"campaign-02:{gate_stage}:{arm_name}:{repetition}:{seed}"


def _validate_definition_bindings(
    definition: BenchmarkDefinition,
    workload: WorkloadContract,
    domain_manifest: CampaignDomainManifest,
    ticket_plan: CampaignTicketPlan,
    runtime_lineage: QualifiedRuntimeLineage,
    stage_identities: StageExecutionIdentityManifest,
) -> None:
    if definition.content_id in _SUPERSEDED_DEFINITION_IDS:
        raise _fail("CAMPAIGN02_DEFINITION_SUPERSEDED_BEFORE_ATTESTATION")
    if (
        definition.raw.get("schema_version") != "3.0.0"
        or definition.campaign_id != "campaign-02"
        or not definition.primary
    ):
        raise _fail("CAMPAIGN02_DEFINITION_V3_REQUIRED")
    if runtime_lineage.runner_id is not None:
        raise _fail("CAMPAIGN02_STAGE_SPECIFIC_RUNTIME_LINEAGE_REQUIRED")
    if (
        stage_identities.content_id != runtime_lineage.stage_execution_identities_id
        or stage_identities.source_commit != runtime_lineage.source_commit
        or stage_identities.source_tree != runtime_lineage.source_tree
        or stage_identities.identity_id("exactness_runner") != runtime_lineage.exactness_runner_id
        or stage_identities.identity_id("scientific_runner") != runtime_lineage.scientific_runner_id
        or stage_identities.identity_id("network_fault_runner")
        != runtime_lineage.network_fault_runner_id
        or stage_identities.identity_id("evaluation_runner") != runtime_lineage.evaluation_runner_id
        or stage_identities.identity_id("observation_writer") != runtime_lineage.writer_id
    ):
        raise _fail("CAMPAIGN02_STAGE_EXECUTION_IDENTITY_MANIFEST_MISMATCH")
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
        or definition.stage_execution_identities_id != runtime_lineage.stage_execution_identities_id
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


def compile_campaign02_plan_catalog(
    *,
    definition: BenchmarkDefinition,
    attestation_document: dict[str, object],
    validator_set: BenchmarkReviewValidatorSet,
    votes: tuple[SignedDefinitionVote, ...],
    workload: WorkloadContract,
    domain_manifest: CampaignDomainManifest,
    ticket_plan: CampaignTicketPlan,
    arms: tuple[ArmSpec, ...],
    runtime_lineage: QualifiedRuntimeLineage,
    stage_identities: StageExecutionIdentityManifest,
) -> Campaign02PlanCatalog:
    """Compile deterministic stage templates without granting execution authority."""
    _validate_definition_bindings(
        definition,
        workload,
        domain_manifest,
        ticket_plan,
        runtime_lineage,
        stage_identities,
    )
    _validate_arms(definition, arms, workload)
    vote_map = {item.content_id: item for item in votes}
    if len(vote_map) != len(votes):
        raise _fail("CAMPAIGN02_DEFINITION_VOTE_DUPLICATE")
    attested_vote_ids = attestation_document.get("ordered_vote_ids")
    if (
        not isinstance(attested_vote_ids, list)
        or any(not isinstance(item, str) for item in attested_vote_ids)
        or set(attested_vote_ids) != set(vote_map)
        or len(attested_vote_ids) != len(vote_map)
    ):
        raise _fail("CAMPAIGN02_DEFINITION_VOTE_SET_MISMATCH")
    try:
        attestation = verify_definition_attestation(
            attestation_document,
            validator_set=validator_set,
            votes=vote_map,
        )
    except ValueError as exc:
        raise _fail(f"CAMPAIGN02_DEFINITION_ATTESTATION_INVALID:{exc}") from exc
    if attestation.benchmark_definition_id != definition.content_id:
        raise _fail("CAMPAIGN02_DEFINITION_ATTESTATION_MISMATCH")
    plans: list[CampaignExecutionPlan] = []
    for gate_stage in CAMPAIGN02_GATE_STAGES:
        for arm in arms:
            result_class = (
                "REFERENCE" if arm.arm_id == "scientific-reference" else "CERTIFIED_DELTAREDUCE"
            )
            for repetition, seed in enumerate(definition.seeds, start=1):
                policy = (
                    None
                    if result_class == "REFERENCE"
                    else runtime_lineage.policy_for(gate_stage, arm, seed, repetition)
                )
                plan = CampaignExecutionPlan(
                    execution_class="PRIMARY_MEASURED",
                    result_class=result_class,
                    campaign_id="campaign-02",
                    benchmark_definition_id=definition.content_id,
                    definition_attestation_id=attestation.content_id,
                    execution_authorization_id=None,
                    arm_id=arm.content_id,
                    round_id=expected_round_id(gate_stage, arm.arm_id, seed, repetition),
                    seed=seed,
                    repetition=repetition,
                    source_commit=runtime_lineage.source_commit,
                    source_tree=runtime_lineage.source_tree,
                    environment_id=runtime_lineage.environment_id,
                    image_id=runtime_lineage.image_id,
                    hardware_id=runtime_lineage.hardware_id,
                    runner_id=runtime_lineage.runner_id_for_stage(gate_stage),
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
                    gate_stage=gate_stage,
                )
                plans.append(plan)
    expected_policy_count = len(CAMPAIGN02_GATE_STAGES) * 4 * len(definition.seeds)
    if (
        len(plans) != 45
        or len({item.content_id for item in plans}) != 45
        or len(runtime_lineage.certified_plan_bindings) != expected_policy_count
    ):
        raise _fail("CAMPAIGN02_EXECUTION_MATRIX_INCOMPLETE")
    return Campaign02PlanCatalog(
        definition_id=definition.content_id,
        attestation_id=attestation.content_id,
        workload_contract_id=workload.content_id,
        domain_manifest_id=domain_manifest.content_id,
        ticket_plan_id=ticket_plan.content_id,
        runtime_lineage_id=runtime_lineage.content_id,
        stage_execution_identities_id=str(runtime_lineage.stage_execution_identities_id),
        gate_analyzer_id=stage_identities.identity_id("stage_gate_analyzer"),
        definition_attestation_verified_at=attestation.verified_at,
        plans=tuple(plans),
    )


def compile_campaign02_execution_set(**_values: object) -> Campaign02PlanCatalog:
    """Reject the superseded interface that trusted a caller-constructed attestation."""
    raise _fail("CAMPAIGN02_UNVERIFIED_ATTESTATION_INTERFACE_FORBIDDEN")
