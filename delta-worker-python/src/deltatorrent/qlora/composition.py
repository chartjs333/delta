"""Native-authorized QLoRA composition, resume and derived-export metadata."""

from __future__ import annotations

import re
from dataclasses import dataclass

_CONTENT_ID = re.compile(r"^sha256:[0-9a-f]{64}$")


class CompositionError(ValueError):
    """Stable rejection for incompatible composition or provenance."""


def _content_id(value: object, field: str) -> str:
    if not isinstance(value, str) or _CONTENT_ID.fullmatch(value) is None:
        raise CompositionError(f"{field.upper()}_INVALID")
    return value


@dataclass(frozen=True, slots=True)
class ModelComposition:
    base_model_manifest_id: str
    tokenizer_hash: str
    quantized_base_profile_id: str
    adapter_parameter_schema_id: str
    adapter_checkpoint_id: str
    apply_qc_id: str
    native_authorization: bytes


def compose(
    context: dict[str, object],
    checkpoint: dict[str, object],
    native_authorization: bytes,
) -> ModelComposition:
    if not native_authorization:
        raise CompositionError("NATIVE_AUTHORIZATION_REQUIRED")
    pairs = {
        "base_model_manifest_id": "base_model_manifest_id",
        "quantized_base_profile_id": "quantized_base_profile_id",
        "adapter_parameter_schema_id": "adapter_parameter_schema_id",
        "training_mode_id": "training_mode_id",
    }
    for checkpoint_field, context_field in pairs.items():
        if checkpoint.get(checkpoint_field) != context.get(context_field):
            raise CompositionError(f"COMPOSITION_{checkpoint_field.upper()}_MISMATCH")
    if checkpoint.get("parent_adapter_id") != context.get("parent_adapter_id"):
        raise CompositionError("COMPOSITION_PARENT_ADAPTER_MISMATCH")
    return ModelComposition(
        base_model_manifest_id=_content_id(
            context.get("base_model_manifest_id"), "base_model_manifest_id"
        ),
        tokenizer_hash=_content_id(context.get("tokenizer_hash"), "tokenizer_hash"),
        quantized_base_profile_id=_content_id(
            context.get("quantized_base_profile_id"), "quantized_base_profile_id"
        ),
        adapter_parameter_schema_id=_content_id(
            context.get("adapter_parameter_schema_id"), "adapter_parameter_schema_id"
        ),
        adapter_checkpoint_id=_content_id(
            checkpoint.get("next_adapter_id"), "adapter_checkpoint_id"
        ),
        apply_qc_id=_content_id(checkpoint.get("apply_qc_id"), "apply_qc_id"),
        native_authorization=bytes(native_authorization),
    )


def validate_resume(
    composition: ModelComposition,
    context: dict[str, object],
    requested_parent_adapter_id: str,
) -> None:
    expected = (
        composition.base_model_manifest_id,
        composition.tokenizer_hash,
        composition.quantized_base_profile_id,
        composition.adapter_parameter_schema_id,
        composition.adapter_checkpoint_id,
    )
    actual = (
        context.get("base_model_manifest_id"),
        context.get("tokenizer_hash"),
        context.get("quantized_base_profile_id"),
        context.get("adapter_parameter_schema_id"),
        requested_parent_adapter_id,
    )
    if actual != expected:
        raise CompositionError("INCOMPATIBLE_QLORA_RESUME")


def derived_export(
    composition: ModelComposition,
    *,
    merged_model_id: str,
    source_license: str,
    redistribution_allowed: bool,
    provenance_id: str,
) -> dict[str, object]:
    if not redistribution_allowed:
        raise CompositionError("DERIVED_EXPORT_REDISTRIBUTION_FORBIDDEN")
    if not source_license:
        raise CompositionError("DERIVED_EXPORT_LICENSE_REQUIRED")
    return {
        "adapter_checkpoint_id": composition.adapter_checkpoint_id,
        "apply_qc_id": composition.apply_qc_id,
        "base_model_manifest_id": composition.base_model_manifest_id,
        "merged_model_id": _content_id(merged_model_id, "merged_model_id"),
        "provenance_id": _content_id(provenance_id, "provenance_id"),
        "source_license": source_license,
    }
