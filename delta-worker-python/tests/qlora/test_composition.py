from __future__ import annotations

import pytest
from deltatorrent.qlora.composition import (
    CompositionError,
    compose,
    derived_export,
    validate_resume,
)


def _id(digit: str) -> str:
    return "sha256:" + digit * 64


def _context() -> dict[str, object]:
    return {
        "adapter_parameter_schema_id": _id("1"),
        "base_model_manifest_id": _id("2"),
        "parent_adapter_id": _id("3"),
        "quantized_base_profile_id": _id("4"),
        "tokenizer_hash": _id("5"),
        "training_mode_id": _id("6"),
    }


def _checkpoint() -> dict[str, object]:
    return {
        **_context(),
        "apply_qc_id": _id("7"),
        "next_adapter_id": _id("8"),
    }


def test_native_authorized_composition_resume_and_export() -> None:
    composition = compose(_context(), _checkpoint(), b"native-verified")
    validate_resume(composition, _context(), _id("8"))
    exported = derived_export(
        composition,
        merged_model_id=_id("9"),
        source_license="MIT",
        redistribution_allowed=True,
        provenance_id=_id("a"),
    )
    assert exported["apply_qc_id"] == _id("7")
    assert exported["base_model_manifest_id"] == _id("2")


def test_incompatible_resume_and_unlicensed_export_are_rejected() -> None:
    composition = compose(_context(), _checkpoint(), b"native-verified")
    wrong = {**_context(), "base_model_manifest_id": _id("f")}
    with pytest.raises(CompositionError, match="INCOMPATIBLE_QLORA_RESUME"):
        validate_resume(composition, wrong, _id("8"))
    with pytest.raises(CompositionError, match="INCOMPATIBLE_QLORA_RESUME"):
        validate_resume(composition, _context(), _id("f"))
    with pytest.raises(CompositionError, match="DERIVED_EXPORT_REDISTRIBUTION_FORBIDDEN"):
        derived_export(
            composition,
            merged_model_id=_id("9"),
            source_license="restricted",
            redistribution_allowed=False,
            provenance_id=_id("a"),
        )


def test_composition_requires_exact_context_and_native_authorization() -> None:
    wrong = {**_checkpoint(), "quantized_base_profile_id": _id("f")}
    with pytest.raises(CompositionError, match="COMPOSITION_QUANTIZED_BASE_PROFILE_ID_MISMATCH"):
        compose(_context(), wrong, b"native-verified")
    with pytest.raises(CompositionError, match="NATIVE_AUTHORIZATION_REQUIRED"):
        compose(_context(), _checkpoint(), b"")
