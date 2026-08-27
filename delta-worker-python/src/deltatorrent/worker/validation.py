"""Fail-closed ticket binding and immutable input resolution."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from safetensors.torch import load as load_tensors
from torch import Tensor

from deltatorrent.artifacts.canonical_json import canonical_json_bytes, sha256_content_id
from deltatorrent.artifacts.filesystem import FilesystemArtifactStore
from deltatorrent.delta.schema import included_tensor_names
from deltatorrent.delta.validation import validate_fp32_tensor_bundle
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.manifests import ArtifactRef
from deltatorrent.domain.parameters import ParameterSchema
from deltatorrent.domain.tickets import DomainPureWorkTicket
from deltatorrent.training.config import BaselineConfig
from deltatorrent.training.data import Tokenizer, TokenSample, load_samples_from_text


def _invalid(message: str, **details: object) -> DeltaError:
    return DeltaError(ErrorCode.INVALID_WORK_TICKET, message, details)


@dataclass(frozen=True, slots=True)
class LocalRoundLimits:
    per_tensor_norm_ceiling_microunits: int = 1_000_000_000_000
    global_norm_ceiling_microunits: int = 1_000_000_000_000

    def __post_init__(self) -> None:
        for field in self.__dataclass_fields__:
            value = getattr(self, field)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise _invalid("WORK_TICKET_NORM_LIMIT_INVALID", field=field)

    @property
    def per_tensor_norm_ceiling(self) -> float:
        return self.per_tensor_norm_ceiling_microunits / 1_000_000

    @property
    def global_norm_ceiling(self) -> float:
        return self.global_norm_ceiling_microunits / 1_000_000


def optimizer_profile_payload(config: BaselineConfig) -> dict[str, object]:
    return {
        "beta1_ppm": config.beta1_ppm,
        "beta2_ppm": config.beta2_ppm,
        "epsilon_nanos": config.epsilon_nanos,
        "kind": "CANONICAL_ADAMW_V1",
        "learning_rate_nanos": config.learning_rate_nanos,
        "schema_version": "1.0.0",
        "weight_decay_ppm": config.weight_decay_ppm,
    }


def optimizer_profile_id(config: BaselineConfig) -> str:
    return sha256_content_id(canonical_json_bytes(optimizer_profile_payload(config)))


def arithmetic_profile_payload(
    config: BaselineConfig,
    *,
    tokenizer_id: str,
    limits: LocalRoundLimits,
) -> dict[str, object]:
    return {
        "device": config.device,
        "dtype": config.dtype,
        "global_norm_ceiling_microunits": limits.global_norm_ceiling_microunits,
        "gradient_accumulation_steps": config.gradient_accumulation_steps,
        "hidden_size": config.hidden_size,
        "per_tensor_norm_ceiling_microunits": limits.per_tensor_norm_ceiling_microunits,
        "schema_version": "1.0.0",
        "sequence_length": config.sequence_length,
        "tokenizer_id": tokenizer_id,
        "vocab_size": config.vocab_size,
    }


def arithmetic_profile_id(
    config: BaselineConfig,
    *,
    tokenizer_id: str,
    limits: LocalRoundLimits,
) -> str:
    return sha256_content_id(
        canonical_json_bytes(
            arithmetic_profile_payload(config, tokenizer_id=tokenizer_id, limits=limits)
        )
    )


@dataclass(frozen=True, slots=True)
class ResolvedLocalRound:
    ticket: DomainPureWorkTicket
    config: BaselineConfig
    parameter_schema: ParameterSchema
    tokenizer_ref: ArtifactRef
    tokenizer: Tokenizer
    samples: tuple[TokenSample, ...]
    parent_parameters: Mapping[str, Tensor]
    limits: LocalRoundLimits


def resolve_local_round(
    *,
    ticket: DomainPureWorkTicket,
    config: BaselineConfig,
    parameter_schema: ParameterSchema,
    tokenizer_ref: ArtifactRef,
    store: FilesystemArtifactStore,
    limits: LocalRoundLimits | None = None,
) -> ResolvedLocalRound:
    resolved_limits = limits or LocalRoundLimits()
    if ticket.parameter_schema_id != parameter_schema.fingerprint:
        raise _invalid("WORK_TICKET_PARAMETER_SCHEMA_MISMATCH")
    if ticket.batch_budget != config.batch_size or ticket.step_budget != config.optimizer_steps:
        raise _invalid("WORK_TICKET_BUDGET_MISMATCH")
    if ticket.deterministic_seed != config.seed:
        raise _invalid("WORK_TICKET_SEED_MISMATCH")
    if ticket.optimizer_profile_id != optimizer_profile_id(config):
        raise _invalid("WORK_TICKET_OPTIMIZER_PROFILE_MISMATCH")
    if (
        tokenizer_ref.schema_id != "SCHEMA-TOKENIZER-V1"
        or tokenizer_ref.media_type != "application/vnd.deltareduce.tokenizer+json;version=1"
    ):
        raise _invalid("WORK_TICKET_TOKENIZER_REF_INVALID")
    tokenizer_bytes = store.read(tokenizer_ref)
    tokenizer = Tokenizer.from_json_bytes(tokenizer_bytes)
    if len(tokenizer.vocabulary) != config.vocab_size or tokenizer.pad_id != 0:
        raise _invalid("WORK_TICKET_TOKENIZER_PROFILE_MISMATCH")
    if ticket.arithmetic_profile_id != arithmetic_profile_id(
        config,
        tokenizer_id=tokenizer_ref.content_id,
        limits=resolved_limits,
    ):
        raise _invalid("WORK_TICKET_ARITHMETIC_PROFILE_MISMATCH")
    if (
        ticket.data.schema_id != "SCHEMA-CORPUS-TEXT-V1"
        or ticket.data.media_type != "text/plain;charset=utf-8"
    ):
        raise _invalid("WORK_TICKET_DATA_REF_INVALID")
    try:
        corpus_text = store.read(ticket.data).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise _invalid("WORK_TICKET_DATA_UTF8_INVALID") from exc
    samples = load_samples_from_text(corpus_text, tokenizer, config.sequence_length)
    required_draws = ticket.batch_budget * config.gradient_accumulation_steps * ticket.step_budget
    if ticket.data_range.end - ticket.data_range.start != required_draws:
        raise _invalid(
            "WORK_TICKET_DATA_RANGE_BUDGET_MISMATCH",
            actual=ticket.data_range.end - ticket.data_range.start,
            expected=required_draws,
        )
    if (
        ticket.parent_model.schema_id != "SCHEMA-SAFETENSORS-V1"
        or ticket.parent_model.media_type != "application/vnd.safetensors"
    ):
        raise _invalid("WORK_TICKET_PARENT_REF_INVALID")
    try:
        parent = load_tensors(store.read(ticket.parent_model))
    except Exception as exc:
        raise _invalid("WORK_TICKET_PARENT_TENSOR_INVALID") from exc
    canonical_parent = {
        name: parent[name].detach().cpu().contiguous().clone()
        for name in included_tensor_names(parameter_schema)
        if name in parent
    }
    try:
        validate_fp32_tensor_bundle(canonical_parent, parameter_schema)
    except DeltaError as exc:
        raise _invalid("WORK_TICKET_PARENT_TENSOR_INVALID") from exc
    if set(parent) != set(canonical_parent):
        raise _invalid("WORK_TICKET_PARENT_TENSOR_SET_INVALID")
    return ResolvedLocalRound(
        ticket=ticket,
        config=config,
        parameter_schema=parameter_schema,
        tokenizer_ref=tokenizer_ref,
        tokenizer=tokenizer,
        samples=samples,
        parent_parameters=MappingProxyType(canonical_parent),
        limits=resolved_limits,
    )
