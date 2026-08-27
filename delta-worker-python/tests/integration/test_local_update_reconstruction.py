from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest
import torch
from deltatorrent.artifacts.canonical_json import canonical_json_bytes
from deltatorrent.delta.reconstruction import reconstruct_final
from deltatorrent.delta.validation import validate_fp32_tensor_bundle
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.parameters import ParameterSchema, ParameterSpec
from deltatorrent.worker.engine import LocalRoundEngine
from deltatorrent.worker.update_writer import load_canonical_tensor_artifact
from deltatorrent.worker.validation import resolve_local_round
from safetensors.torch import load as load_tensors
from safetensors.torch import save as save_tensors

from tests.integration.test_local_round_engine import prepare_round


def test_published_metadata_is_canonical_and_recursively_self_consistent(
    tmp_path: Path,
) -> None:
    prepared = prepare_round(tmp_path, ticket_id="metadata-round")
    clock = iter((0, 5_000_000))
    result = LocalRoundEngine(
        prepared.store,
        worker_id="worker-metadata-1",
        clock_ns=lambda: next(clock),
    ).run(prepared.resolved)
    published = result.published

    assert prepared.store.read(published.completion_ref) == canonical_json_bytes(
        published.completion.to_dict()
    )
    assert prepared.store.read(published.candidate_ref) == canonical_json_bytes(
        published.candidate.to_dict()
    )
    assert published.completion_ref.content_id == published.completion.fingerprint
    assert published.candidate.completion_id == published.completion.fingerprint
    assert published.candidate.normalized_delta == published.normalized_delta_ref

    local_delta = load_canonical_tensor_artifact(
        prepared.store,
        published.local_delta_ref,
        prepared.schema,
    )
    reconstructed = reconstruct_final(
        prepared.resolved.parent_parameters,
        local_delta,
        prepared.schema,
    )
    assert all(torch.isfinite(tensor).all() for tensor in reconstructed.values())


def test_wrong_parameter_schema_is_rejected_before_training(tmp_path: Path) -> None:
    prepared = prepare_round(tmp_path, ticket_id="wrong-schema")
    first = prepared.schema.parameters[0]
    wrong_spec = ParameterSpec(
        name=first.name,
        shape=(*first.shape, 1),
        logical_dtype=first.logical_dtype,
        trainable=first.trainable,
    )
    wrong_schema = ParameterSchema(
        parameters=(wrong_spec, *prepared.schema.parameters[1:]),
        tied_aliases=prepared.schema.tied_aliases,
        frozen_omission_policy=prepared.schema.frozen_omission_policy,
    )
    with pytest.raises(DeltaError) as raised:
        resolve_local_round(
            ticket=prepared.ticket,
            config=prepared.config,
            parameter_schema=wrong_schema,
            tokenizer_ref=prepared.tokenizer_ref,
            store=prepared.store,
        )
    assert raised.value.code is ErrorCode.INVALID_WORK_TICKET


def test_malformed_safe_tensor_update_fails_exact_set_validation(tmp_path: Path) -> None:
    prepared = prepare_round(tmp_path, ticket_id="malformed-update")
    malformed_ref = prepared.store.publish_bytes(
        save_tensors({"unexpected.weight": torch.zeros(1, dtype=torch.float32)}),
        media_type="application/vnd.safetensors",
        schema_id="SCHEMA-SAFETENSORS-V1",
    )
    malformed = load_tensors(prepared.store.read(malformed_ref))
    with pytest.raises(DeltaError) as raised:
        validate_fp32_tensor_bundle(malformed, prepared.schema)
    assert raised.value.code is ErrorCode.INVALID_DELTA_TENSOR


def test_profile_or_parent_mutation_changes_ticket_fingerprint(tmp_path: Path) -> None:
    prepared = prepare_round(tmp_path, ticket_id="fingerprint-mutation")
    changed_profile = replace(
        prepared.ticket,
        optimizer_profile_id="sha256:" + "9" * 64,
    )
    changed_parent = replace(
        prepared.ticket,
        parent_model=replace(
            prepared.ticket.parent_model,
            content_id="sha256:" + "8" * 64,
        ),
    )
    assert changed_profile.fingerprint != prepared.ticket.fingerprint
    assert changed_parent.fingerprint != prepared.ticket.fingerprint
