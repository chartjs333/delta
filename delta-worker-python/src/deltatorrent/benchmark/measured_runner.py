"""Source-bound production scientific and evaluation runners for Campaign 02."""

from __future__ import annotations

import re
from dataclasses import dataclass, replace
from typing import Any, Protocol

from deltatorrent.benchmark.campaign02 import (
    CampaignExecutionPlan,
    TicketAllocation,
    authorize_execution_class,
)
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.benchmark.evaluators.common import (
    EvaluatorProfile,
    MeasuredEvaluation,
    ScoringBackend,
)
from deltatorrent.benchmark.feature008_admission import (
    Feature008CertificateBundle,
    Feature008ChainVerifier,
)
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

_CONTENT_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
_SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


class MeasuredRunnerError(ValueError):
    """Stable runner identity or measured-output rejection."""


def _fail(code: str) -> MeasuredRunnerError:
    return MeasuredRunnerError(code)


def _id(value: str, code: str) -> str:
    if _CONTENT_ID.fullmatch(value) is None:
        raise _fail(code)
    return value


@dataclass(frozen=True, slots=True)
class ComponentIdentity:
    component: str
    source_commit: str
    source_tree: str
    executable_hashes: tuple[tuple[str, str], ...]
    environment_id: str
    image_id: str
    hardware_compatibility_class_id: str
    model_data_staging_policy_id: str
    timeout_policy_id: str
    output_schema_ids: tuple[str, ...]
    create_only_store_policy_id: str

    def __post_init__(self) -> None:
        if self.component not in {
            "PRIMARY_SCIENTIFIC_RUNNER",
            "PRIMARY_EVALUATION_RUNNER",
            "PRIMARY_OBSERVATION_WRITER",
        }:
            raise _fail("COMPONENT_IDENTITY_KIND_INVALID")
        if not re.fullmatch(r"[0-9a-f]{40}", self.source_commit) or not re.fullmatch(
            r"[0-9a-f]{40}", self.source_tree
        ):
            raise _fail("COMPONENT_SOURCE_IDENTITY_INVALID")
        if not self.executable_hashes or tuple(sorted(self.executable_hashes)) != (
            self.executable_hashes
        ):
            raise _fail("COMPONENT_EXECUTABLE_SET_INVALID")
        if len({path for path, _ in self.executable_hashes}) != len(self.executable_hashes):
            raise _fail("COMPONENT_EXECUTABLE_SET_INVALID")
        identities = (
            self.environment_id,
            self.image_id,
            self.hardware_compatibility_class_id,
            self.model_data_staging_policy_id,
            self.timeout_policy_id,
            self.create_only_store_policy_id,
            *self.output_schema_ids,
            *(content_id for _, content_id in self.executable_hashes),
        )
        if any(_CONTENT_ID.fullmatch(value) is None for value in identities):
            raise _fail("COMPONENT_BOUND_IDENTITY_INVALID")

    @property
    def document(self) -> dict[str, object]:
        return {
            "component": self.component,
            "create_only_store_policy_id": self.create_only_store_policy_id,
            "environment_id": self.environment_id,
            "executable_hashes": [
                {"content_id": content_id, "path": path}
                for path, content_id in self.executable_hashes
            ],
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "hardware_compatibility_class_id": self.hardware_compatibility_class_id,
            "image_id": self.image_id,
            "model_data_staging_policy_id": self.model_data_staging_policy_id,
            "output_schema_ids": list(self.output_schema_ids),
            "schema_version": "1.0.0",
            "source_commit": self.source_commit,
            "source_tree": self.source_tree,
            "timeout_policy_id": self.timeout_policy_id,
            "type_name": "PRIMARY_COMPONENT_IDENTITY",
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            b"deltareduce.010.primary-component.v1\0" + canonical_json_bytes(self.document)
        )


@dataclass(frozen=True, slots=True)
class RawArtifact:
    name: str
    media_type: str
    data: bytes

    def __post_init__(self) -> None:
        if _SAFE_NAME.fullmatch(self.name) is None or not self.media_type or not self.data:
            raise _fail("MEASURED_RAW_ARTIFACT_INVALID")

    @property
    def content_id(self) -> str:
        return sha256_content_id(self.data)


@dataclass(frozen=True, slots=True)
class RunHandle:
    run_id: str
    execution_plan_id: str

    def __post_init__(self) -> None:
        _id(self.run_id, "SCIENTIFIC_RUN_HANDLE_ID_INVALID")
        _id(self.execution_plan_id, "SCIENTIFIC_RUN_HANDLE_PLAN_ID_INVALID")


@dataclass(frozen=True, slots=True)
class TicketContributionMeasurement:
    ticket_id: str
    domain_id: str
    processed_tokens: int
    optimizer_steps: int
    contribution_id: str
    commitment_id: str
    availability_certificate_id: str
    artifacts: tuple[RawArtifact, ...]

    def __post_init__(self) -> None:
        values = (
            self.ticket_id,
            self.contribution_id,
            self.commitment_id,
            self.availability_certificate_id,
        )
        if any(_CONTENT_ID.fullmatch(value) is None for value in values):
            raise _fail("TICKET_CONTRIBUTION_IDENTITY_INVALID")
        if self.processed_tokens < 1 or self.optimizer_steps < 1 or not self.domain_id:
            raise _fail("TICKET_CONTRIBUTION_ACCOUNTING_INVALID")
        if not self.artifacts:
            raise _fail("TICKET_CONTRIBUTION_ARTIFACT_MISSING")
        if len({item.name for item in self.artifacts}) != len(self.artifacts):
            raise _fail("TICKET_CONTRIBUTION_ARTIFACT_DUPLICATE")

    @property
    def document(self) -> dict[str, object]:
        return {
            "availability_certificate_id": self.availability_certificate_id,
            "commitment_id": self.commitment_id,
            "contribution_id": self.contribution_id,
            "domain_id": self.domain_id,
            "local_artifact_ids": sorted(item.content_id for item in self.artifacts),
            "optimizer_steps": self.optimizer_steps,
            "processed_tokens": self.processed_tokens,
            "ticket_id": self.ticket_id,
        }


@dataclass(frozen=True, slots=True)
class ReferenceRoundMeasurement:
    round_id: str
    parent_checkpoint_id: str
    ordered_ticket_ids: tuple[str, ...]
    ordered_data_exposure_ids: tuple[str, ...]
    processed_tokens: int
    final_checkpoint_id: str
    training_artifacts: tuple[RawArtifact, ...]
    terminal_outcome: str = "COMPLETED"
    result_class: str = "REFERENCE"

    def __post_init__(self) -> None:
        if self.result_class != "REFERENCE" or self.terminal_outcome != "COMPLETED":
            raise _fail("REFERENCE_ROUND_CLASS_OR_OUTCOME_INVALID")
        if not self.round_id or self.processed_tokens < 1 or not self.training_artifacts:
            raise _fail("REFERENCE_ROUND_ACCOUNTING_INVALID")
        values = (
            self.parent_checkpoint_id,
            self.final_checkpoint_id,
            *self.ordered_ticket_ids,
            *self.ordered_data_exposure_ids,
        )
        if any(_CONTENT_ID.fullmatch(value) is None for value in values):
            raise _fail("REFERENCE_ROUND_IDENTITY_INVALID")
        if len(self.ordered_ticket_ids) != len(self.ordered_data_exposure_ids):
            raise _fail("REFERENCE_ROUND_EXPOSURE_COUNT_MISMATCH")

    @property
    def artifacts(self) -> tuple[RawArtifact, ...]:
        return self.training_artifacts

    @property
    def document(self) -> dict[str, object]:
        return {
            "final_checkpoint_id": self.final_checkpoint_id,
            "ordered_data_exposure_ids": list(self.ordered_data_exposure_ids),
            "ordered_ticket_ids": list(self.ordered_ticket_ids),
            "parent_checkpoint_id": self.parent_checkpoint_id,
            "processed_tokens": self.processed_tokens,
            "result_class": self.result_class,
            "round_id": self.round_id,
            "terminal_outcome": self.terminal_outcome,
            "training_artifact_ids": sorted(item.content_id for item in self.training_artifacts),
        }


@dataclass(frozen=True, slots=True)
class CertifiedRoundMeasurement:
    round_id: str
    parent_checkpoint_id: str
    ordered_ticket_ids: tuple[str, ...]
    ordered_contribution_ids: tuple[str, ...]
    input_set_certificate_id: str
    seed_transcript_id: str
    eligibility_certificate_id: str
    aggregation_plan_certificate_id: str
    parameter_shard_qc_ids: tuple[str, ...]
    aggregate_root_qc_id: str
    apply_qc_id: str
    final_checkpoint_id: str
    runtime_state_id: str
    effect_set_id: str
    runtime_wal_sha256: str
    checkpoint_wal_sha256: str
    runtime_receipt_id: str
    terminal_outcome: str
    certificate_bundle: Feature008CertificateBundle
    artifacts: tuple[RawArtifact, ...]
    native_chain_admission_receipt_id: str | None = None
    native_chain_verifier_id: str | None = None
    result_class: str = "CERTIFIED_DELTAREDUCE"

    def __post_init__(self) -> None:
        if self.result_class != "CERTIFIED_DELTAREDUCE":
            raise _fail("CERTIFIED_ROUND_CLASS_INVALID")
        if not self.round_id or not self.parameter_shard_qc_ids or not self.artifacts:
            raise _fail("CERTIFIED_ROUND_EVIDENCE_INCOMPLETE")
        identities = (
            self.parent_checkpoint_id,
            *self.ordered_ticket_ids,
            *self.ordered_contribution_ids,
            self.input_set_certificate_id,
            self.seed_transcript_id,
            self.eligibility_certificate_id,
            self.aggregation_plan_certificate_id,
            *self.parameter_shard_qc_ids,
            self.aggregate_root_qc_id,
            self.apply_qc_id,
            self.final_checkpoint_id,
            self.runtime_state_id,
            self.effect_set_id,
            self.runtime_receipt_id,
        )
        if any(_CONTENT_ID.fullmatch(value) is None for value in identities):
            raise _fail("CERTIFIED_ROUND_IDENTITY_INVALID")
        if not re.fullmatch(r"[0-9a-f]{64}", self.runtime_wal_sha256) or not re.fullmatch(
            r"[0-9a-f]{64}", self.checkpoint_wal_sha256
        ):
            raise _fail("CERTIFIED_ROUND_WAL_IDENTITY_INVALID")
        native_identities = (
            self.native_chain_admission_receipt_id,
            self.native_chain_verifier_id,
        )
        if any(value is not None for value in native_identities) and any(
            value is None or _CONTENT_ID.fullmatch(value) is None for value in native_identities
        ):
            raise _fail("CERTIFIED_ROUND_NATIVE_ADMISSION_IDENTITY_INVALID")

    @property
    def document(self) -> dict[str, object]:
        if self.native_chain_admission_receipt_id is None or self.native_chain_verifier_id is None:
            raise _fail("CERTIFIED_ROUND_NATIVE_ADMISSION_RECEIPT_MISSING")
        return {
            "aggregate_root_qc_id": self.aggregate_root_qc_id,
            "aggregation_plan_certificate_id": self.aggregation_plan_certificate_id,
            "apply_qc_id": self.apply_qc_id,
            "checkpoint_wal_sha256": self.checkpoint_wal_sha256,
            "effect_set_id": self.effect_set_id,
            "eligibility_certificate_id": self.eligibility_certificate_id,
            "final_checkpoint_id": self.final_checkpoint_id,
            "input_set_certificate_id": self.input_set_certificate_id,
            "native_chain_admission_receipt_id": self.native_chain_admission_receipt_id,
            "native_chain_verifier_id": self.native_chain_verifier_id,
            "ordered_contribution_ids": list(self.ordered_contribution_ids),
            "ordered_ticket_ids": list(self.ordered_ticket_ids),
            "parameter_shard_qc_ids": list(self.parameter_shard_qc_ids),
            "parent_checkpoint_id": self.parent_checkpoint_id,
            "result_class": self.result_class,
            "round_id": self.round_id,
            "runtime_receipt_id": self.runtime_receipt_id,
            "runtime_state_id": self.runtime_state_id,
            "runtime_wal_sha256": self.runtime_wal_sha256,
            "seed_transcript_id": self.seed_transcript_id,
            "terminal_outcome": self.terminal_outcome,
        }


RoundMeasurement = ReferenceRoundMeasurement | CertifiedRoundMeasurement


class ScientificArmBackend(Protocol):
    @property
    def source_class(self) -> str: ...

    @property
    def environment_id(self) -> str: ...

    @property
    def model_id(self) -> str: ...

    @property
    def result_class(self) -> str: ...

    def begin_run(self, plan: CampaignExecutionPlan) -> RunHandle: ...

    def execute_ticket(
        self, run: RunHandle, ticket: TicketAllocation
    ) -> TicketContributionMeasurement: ...

    def finalize_run(
        self,
        run: RunHandle,
        contributions: tuple[TicketContributionMeasurement, ...],
    ) -> RoundMeasurement: ...


@dataclass(frozen=True, slots=True)
class ScientificRun:
    plan_id: str
    runner_id: str
    ticket_measurements: tuple[TicketContributionMeasurement, ...]
    round_result: RoundMeasurement
    raw_artifacts: tuple[RawArtifact, ...]

    @property
    def processed_tokens(self) -> int:
        return sum(item.processed_tokens for item in self.ticket_measurements)

    @property
    def final_checkpoint_id(self) -> str:
        return self.round_result.final_checkpoint_id

    @property
    def result_class(self) -> str:
        return self.round_result.result_class

    @property
    def content_id(self) -> str:
        value = {
            "execution_plan_id": self.plan_id,
            "result_class": self.result_class,
            "round_result": self.round_result.document,
            "runner_id": self.runner_id,
            "ticket_results": [item.document for item in self.ticket_measurements],
        }
        return sha256_content_id(
            b"deltareduce.010.scientific-run.v2\0" + canonical_json_bytes(value)
        )


class PrimaryScientificRunner:
    def __init__(
        self,
        identity: ComponentIdentity,
        certificate_verifier: Feature008ChainVerifier | None = None,
    ) -> None:
        if identity.component != "PRIMARY_SCIENTIFIC_RUNNER":
            raise _fail("SCIENTIFIC_RUNNER_IDENTITY_INVALID")
        self.identity = identity
        self.certificate_verifier = certificate_verifier

    def run(
        self,
        plan: CampaignExecutionPlan,
        authorization: dict[str, Any],
        backend: ScientificArmBackend,
    ) -> ScientificRun:
        authorize_execution_class(authorization, plan)
        if (
            plan.runner_id != self.identity.content_id
            or plan.source_commit != self.identity.source_commit
            or plan.source_tree != self.identity.source_tree
            or plan.environment_id != self.identity.environment_id
            or plan.image_id != self.identity.image_id
            or backend.environment_id != plan.environment_id
            or backend.model_id != plan.model_id
            or backend.result_class != plan.result_class
        ):
            raise _fail("SCIENTIFIC_RUNNER_PLAN_IDENTITY_MISMATCH")
        if plan.execution_class == "PRIMARY_MEASURED" and backend.source_class != (
            "MEASURED_HARDWARE"
        ):
            raise _fail("SCIENTIFIC_RUNNER_SYNTHETIC_PRIMARY_FORBIDDEN")
        if plan.execution_class == "NON_PRIMARY_SMOKE" and backend.source_class not in {
            "NON_PRIMARY_FIXTURE",
            "MEASURED_HARDWARE",
        }:
            raise _fail("SCIENTIFIC_RUNNER_SOURCE_CLASS_INVALID")
        run_handle = backend.begin_run(plan)
        if run_handle.execution_plan_id != plan.content_id:
            raise _fail("SCIENTIFIC_RUNNER_HANDLE_PLAN_MISMATCH")
        measurements: list[TicketContributionMeasurement] = []
        artifacts: list[RawArtifact] = []
        for ticket in plan.tickets:
            measured = backend.execute_ticket(run_handle, ticket)
            if (
                measured.ticket_id != ticket.ticket_id
                or measured.domain_id != ticket.domain_id
                or measured.processed_tokens != ticket.tokens_per_ticket
                or measured.optimizer_steps != ticket.optimizer_steps
            ):
                raise _fail("SCIENTIFIC_RUNNER_TICKET_OUTPUT_MISMATCH")
            measurements.append(measured)
            artifacts.extend(measured.artifacts)
        finalized = backend.finalize_run(run_handle, tuple(measurements))
        if not isinstance(finalized, (ReferenceRoundMeasurement, CertifiedRoundMeasurement)):
            raise _fail("SCIENTIFIC_RUNNER_FINALIZATION_TYPE_INVALID")
        if finalized.result_class != plan.result_class:
            raise _fail("SCIENTIFIC_RUNNER_RESULT_CLASS_MISMATCH")
        if isinstance(finalized, ReferenceRoundMeasurement):
            if (
                plan.result_class != "REFERENCE"
                or finalized.round_id != plan.round_id
                or finalized.parent_checkpoint_id != plan.parent_checkpoint_id
                or finalized.processed_tokens != plan.processed_tokens
                or set(finalized.ordered_ticket_ids) != {item.ticket_id for item in plan.tickets}
                or len(finalized.ordered_ticket_ids) != len(plan.tickets)
            ):
                raise _fail("SCIENTIFIC_RUNNER_REFERENCE_FINALIZATION_INVALID")
            exposures = dict(
                zip(
                    finalized.ordered_ticket_ids,
                    finalized.ordered_data_exposure_ids,
                    strict=True,
                )
            )
            canonical_tickets = tuple(item.ticket_id for item in plan.tickets)
            finalized = replace(
                finalized,
                ordered_ticket_ids=canonical_tickets,
                ordered_data_exposure_ids=tuple(exposures[item] for item in canonical_tickets),
            )
        elif isinstance(finalized, CertifiedRoundMeasurement):
            if plan.result_class != "CERTIFIED_DELTAREDUCE" or self.certificate_verifier is None:
                raise _fail("SCIENTIFIC_RUNNER_CERTIFIED_VERIFIER_MISSING")
            receipt = self.certificate_verifier.verify(
                plan,
                tuple(measurements),
                finalized,
                require_native=plan.execution_class == "PRIMARY_MEASURED",
            )
            finalized = replace(
                finalized,
                ordered_ticket_ids=receipt.canonical_ticket_ids,
                ordered_contribution_ids=receipt.canonical_contribution_ids,
                native_chain_admission_receipt_id=receipt.native_receipt.content_id,
                native_chain_verifier_id=str(
                    receipt.native_receipt.value["native_chain_verifier_id"]
                ),
            )
            artifacts.append(
                RawArtifact(
                    "native-chain-admission-receipt.json",
                    "application/vnd.deltareduce.campaign-02.native-chain-admission-receipt+json;version=1",
                    receipt.native_receipt.canonical_bytes,
                )
            )
            for certificate in finalized.certificate_bundle.artifacts:
                artifacts.append(
                    RawArtifact(
                        certificate.name, certificate.media_type, certificate.canonical_bytes
                    )
                )
        artifacts.extend(finalized.artifacts)
        if len({item.name for item in artifacts}) != len(artifacts):
            raise _fail("SCIENTIFIC_RUNNER_ARTIFACT_NAME_DUPLICATE")
        run = ScientificRun(
            plan_id=plan.content_id,
            runner_id=self.identity.content_id,
            ticket_measurements=tuple(measurements),
            round_result=finalized,
            raw_artifacts=tuple(artifacts),
        )
        if run.processed_tokens != plan.processed_tokens:
            raise _fail("SCIENTIFIC_RUNNER_PROCESSED_TOKENS_MISMATCH")
        return run


class MeasuredEvaluator(Protocol):
    profile: EvaluatorProfile

    def evaluate(
        self,
        context: Any,
        backend: ScoringBackend,
        records: Any,
    ) -> MeasuredEvaluation: ...


@dataclass(frozen=True, slots=True)
class EvaluatorBinding:
    profile: EvaluatorProfile
    implementation_id: str
    evaluator: MeasuredEvaluator

    def __post_init__(self) -> None:
        _id(self.implementation_id, "EVALUATOR_IMPLEMENTATION_ID_INVALID")
        if self.evaluator.profile.content_id != self.profile.content_id:
            raise _fail("EVALUATOR_BINDING_PROFILE_MISMATCH")


class PrimaryEvaluationRunner:
    def __init__(self, identity: ComponentIdentity, bindings: tuple[EvaluatorBinding, ...]) -> None:
        if identity.component != "PRIMARY_EVALUATION_RUNNER" or not bindings:
            raise _fail("EVALUATION_RUNNER_IDENTITY_INVALID")
        if len({item.profile.content_id for item in bindings}) != len(bindings):
            raise _fail("EVALUATION_RUNNER_BINDING_DUPLICATE")
        self.identity = identity
        self.bindings = bindings

    def run(
        self,
        plan: CampaignExecutionPlan,
        authorization: dict[str, Any],
        scientific_run: ScientificRun,
        backends: dict[str, ScoringBackend],
        datasets: dict[str, object],
    ) -> tuple[MeasuredEvaluation, ...]:
        from deltatorrent.benchmark.evaluators.common import EvaluationContext

        authorize_execution_class(authorization, plan)
        if (
            plan.evaluation_runner_id != self.identity.content_id
            or plan.environment_id != self.identity.environment_id
            or plan.source_commit != self.identity.source_commit
            or plan.source_tree != self.identity.source_tree
            or scientific_run.plan_id != plan.content_id
            or tuple(item.profile.content_id for item in self.bindings)
            != plan.evaluation_profile_ids
            or tuple(item.implementation_id for item in self.bindings)
            != plan.evaluation_implementation_ids
        ):
            raise _fail("EVALUATION_RUNNER_PLAN_IDENTITY_MISMATCH")
        results: list[MeasuredEvaluation] = []
        for binding in self.bindings:
            evaluator_id = binding.profile.evaluator_id
            try:
                backend = backends[evaluator_id]
                dataset = datasets[evaluator_id]
            except KeyError as exc:
                raise _fail("EVALUATION_RUNNER_INPUT_MISSING") from exc
            context = EvaluationContext(
                execution_plan_id=plan.content_id,
                checkpoint_id=scientific_run.final_checkpoint_id,
                model_id=scientific_run.final_checkpoint_id,
                tokenizer_id=plan.tokenizer_id,
                dataset_id=binding.profile.dataset_id,
                environment_id=plan.environment_id,
                evaluator_profile_id=binding.profile.content_id,
                evaluator_implementation_id=binding.implementation_id,
            )
            result = binding.evaluator.evaluate(context, backend, dataset)
            if result.context != context:
                raise _fail("EVALUATION_RUNNER_OUTPUT_CONTEXT_MISMATCH")
            results.append(result)
        return tuple(results)
