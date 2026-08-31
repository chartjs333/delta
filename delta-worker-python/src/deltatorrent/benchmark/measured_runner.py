"""Source-bound production scientific and evaluation runners for Campaign 02."""

from __future__ import annotations

import re
from dataclasses import dataclass
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
class TicketMeasurement:
    ticket_id: str
    domain_id: str
    processed_tokens: int
    optimizer_steps: int
    checkpoint_id: str
    contribution_id: str
    certificate_ids: tuple[str, ...]
    artifacts: tuple[RawArtifact, ...]

    def __post_init__(self) -> None:
        values = (self.ticket_id, self.checkpoint_id, self.contribution_id, *self.certificate_ids)
        if any(_CONTENT_ID.fullmatch(value) is None for value in values):
            raise _fail("TICKET_MEASUREMENT_IDENTITY_INVALID")
        if self.processed_tokens < 1 or self.optimizer_steps < 1 or not self.domain_id:
            raise _fail("TICKET_MEASUREMENT_ACCOUNTING_INVALID")
        if len({item.name for item in self.artifacts}) != len(self.artifacts):
            raise _fail("TICKET_MEASUREMENT_ARTIFACT_DUPLICATE")


class ScientificArmBackend(Protocol):
    @property
    def source_class(self) -> str: ...

    @property
    def environment_id(self) -> str: ...

    @property
    def model_id(self) -> str: ...

    @property
    def certified(self) -> bool: ...

    def execute_ticket(
        self, plan: CampaignExecutionPlan, ticket: TicketAllocation
    ) -> TicketMeasurement: ...


@dataclass(frozen=True, slots=True)
class ScientificRun:
    plan_id: str
    runner_id: str
    ticket_measurements: tuple[TicketMeasurement, ...]
    final_checkpoint_id: str
    raw_artifacts: tuple[RawArtifact, ...]

    @property
    def processed_tokens(self) -> int:
        return sum(item.processed_tokens for item in self.ticket_measurements)


class PrimaryScientificRunner:
    def __init__(self, identity: ComponentIdentity) -> None:
        if identity.component != "PRIMARY_SCIENTIFIC_RUNNER":
            raise _fail("SCIENTIFIC_RUNNER_IDENTITY_INVALID")
        self.identity = identity

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
        measurements: list[TicketMeasurement] = []
        artifacts: list[RawArtifact] = []
        for ticket in plan.tickets:
            measured = backend.execute_ticket(plan, ticket)
            if (
                measured.ticket_id != ticket.ticket_id
                or measured.domain_id != ticket.domain_id
                or measured.processed_tokens != ticket.tokens_per_ticket
                or measured.optimizer_steps != ticket.optimizer_steps
            ):
                raise _fail("SCIENTIFIC_RUNNER_TICKET_OUTPUT_MISMATCH")
            if backend.certified and len(measured.certificate_ids) < 6:
                raise _fail("SCIENTIFIC_RUNNER_CERTIFICATE_EVIDENCE_INCOMPLETE")
            if not backend.certified and measured.certificate_ids:
                raise _fail("SCIENTIFIC_RUNNER_REFERENCE_CERTIFICATE_INVALID")
            measurements.append(measured)
            artifacts.extend(measured.artifacts)
        run = ScientificRun(
            plan_id=plan.content_id,
            runner_id=self.identity.content_id,
            ticket_measurements=tuple(measurements),
            final_checkpoint_id=measurements[-1].checkpoint_id,
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
