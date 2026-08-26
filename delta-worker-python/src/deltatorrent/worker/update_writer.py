"""Safe tensor publication and manifest-last local candidate commit."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import torch
from safetensors.torch import load as load_tensors
from safetensors.torch import save as save_tensors
from torch import Tensor

from deltatorrent import __version__
from deltatorrent.artifacts.canonical_json import canonical_json_bytes
from deltatorrent.artifacts.filesystem import FilesystemArtifactStore
from deltatorrent.delta.normalization import normalize_local_delta
from deltatorrent.delta.schema import included_tensor_names
from deltatorrent.delta.validation import validate_fp32_tensor_bundle
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.manifests import ArtifactRef
from deltatorrent.domain.parameters import ParameterSchema
from deltatorrent.domain.tickets import DomainPureWorkTicket
from deltatorrent.domain.updates import (
    CompletionReason,
    CompletionStatus,
    LocalDelta,
    LocalRoundCompletion,
    NormalizedContributionCandidate,
    NumericalSummary,
    ResourceSummary,
)
from deltatorrent.training.token_accounting import TokenAccountingRecord
from deltatorrent.worker.validation import LocalRoundLimits

_SAFETENSORS_MEDIA_TYPE = "application/vnd.safetensors"


def load_canonical_tensor_artifact(
    store: FilesystemArtifactStore,
    reference: ArtifactRef,
    parameter_schema: ParameterSchema,
) -> dict[str, Tensor]:
    if (
        reference.schema_id != "SCHEMA-SAFETENSORS-V1"
        or reference.media_type != _SAFETENSORS_MEDIA_TYPE
    ):
        raise DeltaError(ErrorCode.INVALID_DELTA_TENSOR, "TENSOR_ARTIFACT_TYPE_INVALID")
    try:
        loaded = load_tensors(store.read(reference))
    except Exception as exc:
        raise DeltaError(ErrorCode.INVALID_DELTA_TENSOR, "TENSOR_ARTIFACT_INVALID") from exc
    tensor_order = included_tensor_names(parameter_schema)
    if set(loaded) != set(tensor_order):
        raise DeltaError(ErrorCode.INVALID_DELTA_TENSOR, "TENSOR_ARTIFACT_SET_INVALID")
    canonical = {name: loaded[name] for name in tensor_order}
    validate_fp32_tensor_bundle(canonical, parameter_schema)
    return canonical


@dataclass(frozen=True, slots=True)
class PublishedLocalRound:
    parameter_schema_ref: ArtifactRef
    local_delta_ref: ArtifactRef
    completion_ref: ArtifactRef
    normalized_delta_ref: ArtifactRef
    candidate_ref: ArtifactRef
    completion: LocalRoundCompletion
    candidate: NormalizedContributionCandidate

    def to_dict(self) -> dict[str, object]:
        return {
            "candidate": self.candidate_ref.to_dict(),
            "completion": self.completion_ref.to_dict(),
            "local_delta": self.local_delta_ref.to_dict(),
            "normalized_delta": self.normalized_delta_ref.to_dict(),
            "parameter_schema": self.parameter_schema_ref.to_dict(),
            "schema_version": "1.0.0",
            "status": "COMPLETED",
            "ticket_id": self.candidate.ticket_id,
        }


class LocalUpdateWriter:
    def __init__(self, store: FilesystemArtifactStore) -> None:
        self.store = store

    def publish_success(
        self,
        *,
        ticket: DomainPureWorkTicket,
        worker_id: str,
        parameter_schema: ParameterSchema,
        accounting: TokenAccountingRecord,
        local_delta: Mapping[str, Tensor],
        normalized_delta: Mapping[str, Tensor],
        limits: LocalRoundLimits,
        wall_time_ms: int,
        peak_memory_bytes: int,
    ) -> PublishedLocalRound:
        if accounting.effective_steps != ticket.step_budget or accounting.pending_micro_steps:
            raise DeltaError(
                ErrorCode.INVALID_CONTRIBUTION_CANDIDATE,
                "CANDIDATE_REQUIRES_COMMITTED_A_EQUALS_H",
            )
        validate_fp32_tensor_bundle(local_delta, parameter_schema)
        summary = validate_fp32_tensor_bundle(
            normalized_delta,
            parameter_schema,
            per_tensor_norm_ceiling=limits.per_tensor_norm_ceiling,
            global_norm_ceiling=limits.global_norm_ceiling,
        )
        schema_ref = self.store.publish_json(
            parameter_schema.to_dict(),
            media_type="application/vnd.deltareduce.parameter-schema+json;version=1",
            schema_id="SCHEMA-PARAMETER-SCHEMA-V1",
        )
        if schema_ref.content_id != ticket.parameter_schema_id:
            raise DeltaError(ErrorCode.INVALID_WORK_TICKET, "PUBLISHED_SCHEMA_ID_MISMATCH")
        local_ref = self._publish_tensors(local_delta)
        normalized_ref = self._publish_tensors(normalized_delta)
        tensor_order = included_tensor_names(parameter_schema)
        local_contract = LocalDelta(
            ticket_id=ticket.ticket_id,
            ticket_fingerprint=ticket.fingerprint,
            parent_model_id=ticket.parent_model.content_id,
            parameter_schema_id=ticket.parameter_schema_id,
            artifact=local_ref,
            tensor_order=tensor_order,
        )
        completion = LocalRoundCompletion(
            arithmetic_profile_id=ticket.arithmetic_profile_id,
            batch_budget=ticket.batch_budget,
            candidate_eligible=True,
            cursor_end=accounting.cursor_end,
            cursor_start=accounting.cursor_start,
            data_id=ticket.data.content_id,
            data_range_end=ticket.data_range.end,
            data_range_start=ticket.data_range.start,
            deterministic_seed=ticket.deterministic_seed,
            domain_id=ticket.domain_id,
            effective_steps=accounting.effective_steps,
            failure_code=None,
            local_delta=local_contract,
            logical_deadline_ms=ticket.logical_deadline_ms,
            micro_steps=accounting.observed_micro_steps,
            numerical_summary=NumericalSummary(
                all_finite=True,
                global_l2_norm_fp64_bits=summary.global_l2_norm_fp64_bits,
                max_abs_fp32_bits=summary.max_abs_fp32_bits,
            ),
            optimizer_profile_id=ticket.optimizer_profile_id,
            parameter_schema_id=ticket.parameter_schema_id,
            parent_model_id=ticket.parent_model.content_id,
            processed_tokens=accounting.processed_tokens,
            producer_version=f"deltatorrent-worker-{__version__}",
            reason=CompletionReason.EXACT_H,
            resource_summary=ResourceSummary(
                peak_memory_bytes=peak_memory_bytes,
                wall_time_ms=wall_time_ms,
            ),
            status=CompletionStatus.COMPLETED,
            step_budget=ticket.step_budget,
            ticket_fingerprint=ticket.fingerprint,
            ticket_id=ticket.ticket_id,
            worker_id=worker_id,
        )
        completion_ref = self.store.publish_named(
            f"local-round/{ticket.ticket_id}/completion.json",
            canonical_json_bytes(completion.to_dict()),
            media_type="application/vnd.deltareduce.local-round-completion+json;version=1",
            schema_id="SCHEMA-LOCAL-ROUND-COMPLETION-V1",
        )
        if completion_ref.content_id != completion.fingerprint:
            raise DeltaError(ErrorCode.INVALID_LOCAL_COMPLETION, "COMPLETION_ID_MISMATCH")
        candidate = NormalizedContributionCandidate(
            arithmetic_profile_id=ticket.arithmetic_profile_id,
            completion_id=completion.fingerprint,
            domain_id=ticket.domain_id,
            effective_steps=accounting.effective_steps,
            normalization_denominator=accounting.effective_steps,
            normalized_delta=normalized_ref,
            optimizer_profile_id=ticket.optimizer_profile_id,
            parameter_schema_id=ticket.parameter_schema_id,
            parent_model_id=ticket.parent_model.content_id,
            step_budget=ticket.step_budget,
            tensor_order=tensor_order,
            ticket_fingerprint=ticket.fingerprint,
            ticket_id=ticket.ticket_id,
        )
        candidate_ref = self.store.publish_named(
            f"local-round/{ticket.ticket_id}/candidate.json",
            canonical_json_bytes(candidate.to_dict()),
            media_type=(
                "application/vnd.deltareduce.normalized-contribution-candidate+json;version=1"
            ),
            schema_id="SCHEMA-NORMALIZED-CONTRIBUTION-CANDIDATE-V1",
        )
        return PublishedLocalRound(
            parameter_schema_ref=schema_ref,
            local_delta_ref=local_ref,
            completion_ref=completion_ref,
            normalized_delta_ref=normalized_ref,
            candidate_ref=candidate_ref,
            completion=completion,
            candidate=candidate,
        )

    def verify_success(
        self,
        published: PublishedLocalRound,
        *,
        ticket: DomainPureWorkTicket,
        parameter_schema: ParameterSchema,
        limits: LocalRoundLimits,
    ) -> None:
        completion = published.completion
        candidate = published.candidate
        if (
            published.parameter_schema_ref.content_id != ticket.parameter_schema_id
            or completion.ticket_id != ticket.ticket_id
            or completion.domain_id != ticket.domain_id
            or completion.ticket_fingerprint != ticket.fingerprint
            or completion.data_id != ticket.data.content_id
            or completion.parent_model_id != ticket.parent_model.content_id
            or completion.parameter_schema_id != ticket.parameter_schema_id
            or completion.optimizer_profile_id != ticket.optimizer_profile_id
            or completion.arithmetic_profile_id != ticket.arithmetic_profile_id
            or completion.local_delta is None
            or completion.local_delta.artifact != published.local_delta_ref
            or candidate.ticket_id != ticket.ticket_id
            or candidate.domain_id != ticket.domain_id
            or candidate.ticket_fingerprint != ticket.fingerprint
            or candidate.completion_id != completion.fingerprint
            or candidate.parent_model_id != ticket.parent_model.content_id
            or candidate.parameter_schema_id != ticket.parameter_schema_id
            or candidate.optimizer_profile_id != ticket.optimizer_profile_id
            or candidate.arithmetic_profile_id != ticket.arithmetic_profile_id
            or candidate.normalized_delta != published.normalized_delta_ref
        ):
            raise DeltaError(
                ErrorCode.INVALID_CONTRIBUTION_CANDIDATE,
                "CANDIDATE_LINEAGE_MISMATCH",
            )
        schema_bytes = self.store.read(published.parameter_schema_ref)
        if schema_bytes != canonical_json_bytes(parameter_schema.to_dict()):
            raise DeltaError(ErrorCode.INVALID_PARAMETER_SCHEMA, "PUBLISHED_SCHEMA_BYTES_INVALID")
        completion_bytes = self.store.read(published.completion_ref)
        candidate_bytes = self.store.read(published.candidate_ref)
        if completion_bytes != canonical_json_bytes(published.completion.to_dict()):
            raise DeltaError(ErrorCode.INVALID_LOCAL_COMPLETION, "COMPLETION_BYTES_INVALID")
        if candidate_bytes != canonical_json_bytes(published.candidate.to_dict()):
            raise DeltaError(
                ErrorCode.INVALID_CONTRIBUTION_CANDIDATE,
                "CANDIDATE_BYTES_INVALID",
            )
        local = load_canonical_tensor_artifact(
            self.store,
            published.local_delta_ref,
            parameter_schema,
        )
        normalized = load_canonical_tensor_artifact(
            self.store,
            published.normalized_delta_ref,
            parameter_schema,
        )
        validate_fp32_tensor_bundle(
            normalized,
            parameter_schema,
            per_tensor_norm_ceiling=limits.per_tensor_norm_ceiling,
            global_norm_ceiling=limits.global_norm_ceiling,
        )
        expected = normalize_local_delta(
            local,
            parameter_schema,
            effective_steps=published.candidate.effective_steps,
            step_budget=published.candidate.step_budget,
            per_tensor_norm_ceiling=limits.per_tensor_norm_ceiling,
            global_norm_ceiling=limits.global_norm_ceiling,
        )
        if any(not torch.equal(normalized[name], expected[name]) for name in expected):
            raise DeltaError(
                ErrorCode.INVALID_CONTRIBUTION_CANDIDATE,
                "CANDIDATE_NORMALIZATION_MISMATCH",
            )

    def _publish_tensors(self, tensors: Mapping[str, Tensor]) -> ArtifactRef:
        encoded = save_tensors({name: tensor for name, tensor in tensors.items()})
        return self.store.publish_bytes(
            encoded,
            media_type=_SAFETENSORS_MEDIA_TYPE,
            schema_id="SCHEMA-SAFETENSORS-V1",
        )
