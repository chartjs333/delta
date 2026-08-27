from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

import pytest
import torch
from deltatorrent.artifacts.canonical_json import canonical_json_bytes
from deltatorrent.artifacts.filesystem import FilesystemArtifactStore
from deltatorrent.cli.main import main
from deltatorrent.delta.builder import snapshot_fp32_parameters
from deltatorrent.delta.reconstruction import reconstruct_final
from deltatorrent.delta.schema import canonical_parameter_tensors, derive_parameter_schema
from deltatorrent.domain.manifests import ArtifactRef
from deltatorrent.domain.parameters import ParameterSchema
from deltatorrent.domain.tickets import DataRange, DomainPureWorkTicket
from deltatorrent.training.baseline import TrainingState, train_to_optimizer_step
from deltatorrent.training.config import BaselineConfig
from deltatorrent.training.data import DeterministicSampler, Tokenizer, TokenSample, load_samples
from deltatorrent.worker.engine import LocalRoundEngine
from deltatorrent.worker.update_writer import load_canonical_tensor_artifact
from deltatorrent.worker.validation import (
    LocalRoundLimits,
    ResolvedLocalRound,
    arithmetic_profile_id,
    optimizer_profile_id,
    resolve_local_round,
)
from safetensors.torch import save as save_tensors

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "configs" / "baseline" / "cpu-smoke-v1.json"


@dataclass(frozen=True, slots=True)
class PreparedRound:
    store: FilesystemArtifactStore
    config: BaselineConfig
    schema: ParameterSchema
    tokenizer_ref: ArtifactRef
    samples: tuple[TokenSample, ...]
    ticket: DomainPureWorkTicket
    resolved: ResolvedLocalRound


def prepare_round(tmp_path: Path, *, ticket_id: str) -> PreparedRound:
    base = BaselineConfig.from_json_file(CONFIG)
    config = replace(base, run_id=ticket_id, output_dir=str(tmp_path), optimizer_steps=2)
    store = FilesystemArtifactStore(tmp_path)
    tokenizer_path = ROOT / config.tokenizer_path
    corpus_path = ROOT / config.corpus_path
    tokenizer_ref = store.publish_bytes(
        tokenizer_path.read_bytes(),
        media_type="application/vnd.deltareduce.tokenizer+json;version=1",
        schema_id="SCHEMA-TOKENIZER-V1",
    )
    data_ref = store.publish_bytes(
        corpus_path.read_bytes(),
        media_type="text/plain;charset=utf-8",
        schema_id="SCHEMA-CORPUS-TEXT-V1",
    )
    tokenizer = Tokenizer.from_json_file(tokenizer_path)
    samples = load_samples(corpus_path, tokenizer, config.sequence_length)
    initial = TrainingState.create(config, len(samples))
    schema = derive_parameter_schema(initial.model)
    parent = snapshot_fp32_parameters(initial.model, schema)
    parent_ref = store.publish_bytes(
        save_tensors(parent),
        media_type="application/vnd.safetensors",
        schema_id="SCHEMA-SAFETENSORS-V1",
    )
    limits = LocalRoundLimits()
    draw_count = config.batch_size * config.gradient_accumulation_steps * config.optimizer_steps
    ticket = DomainPureWorkTicket(
        ticket_id=ticket_id,
        domain_id="domain-text-en",
        data=data_ref,
        data_range=DataRange(start=3, end=3 + draw_count),
        batch_budget=config.batch_size,
        step_budget=config.optimizer_steps,
        parent_model=parent_ref,
        parameter_schema_id=schema.fingerprint,
        optimizer_profile_id=optimizer_profile_id(config),
        arithmetic_profile_id=arithmetic_profile_id(
            config,
            tokenizer_id=tokenizer_ref.content_id,
            limits=limits,
        ),
        deterministic_seed=config.seed,
        logical_deadline_ms=60_000,
    )
    resolved = resolve_local_round(
        ticket=ticket,
        config=config,
        parameter_schema=schema,
        tokenizer_ref=tokenizer_ref,
        store=store,
        limits=limits,
    )
    return PreparedRound(store, config, schema, tokenizer_ref, samples, ticket, resolved)


def test_engine_matches_direct_reference_exact_range_and_a_equals_h(tmp_path: Path) -> None:
    prepared = prepare_round(tmp_path, ticket_id="engine-parity")
    clock = iter((1_000_000_000, 1_250_000_000))
    result = LocalRoundEngine(
        prepared.store,
        worker_id="worker-integration-1",
        clock_ns=lambda: next(clock),
    ).run(prepared.resolved)

    direct = TrainingState.create(prepared.config, len(prepared.samples))
    direct.sampler = DeterministicSampler(
        len(prepared.samples),
        prepared.ticket.deterministic_seed,
        cursor=prepared.ticket.data_range.start,
    )
    with torch.no_grad():
        for name, parameter in canonical_parameter_tensors(direct.model, prepared.schema).items():
            parameter.copy_(prepared.resolved.parent_parameters[name])
    train_to_optimizer_step(direct, prepared.config, prepared.samples, prepared.ticket.step_budget)
    direct_final = snapshot_fp32_parameters(direct.model, prepared.schema)

    local_delta = load_canonical_tensor_artifact(
        prepared.store,
        result.published.local_delta_ref,
        prepared.schema,
    )
    reconstructed = reconstruct_final(
        prepared.resolved.parent_parameters,
        local_delta,
        prepared.schema,
    )
    normalized = load_canonical_tensor_artifact(
        prepared.store,
        result.published.normalized_delta_ref,
        prepared.schema,
    )
    for name in direct_final:
        torch.testing.assert_close(reconstructed[name], direct_final[name], rtol=1e-6, atol=1e-7)
        torch.testing.assert_close(
            normalized[name],
            local_delta[name] / prepared.ticket.step_budget,
            rtol=0,
            atol=0,
        )

    completion = result.published.completion
    candidate = result.published.candidate
    assert completion.effective_steps == candidate.effective_steps == prepared.ticket.step_budget
    assert completion.cursor_start == prepared.ticket.data_range.start
    assert completion.cursor_end == prepared.ticket.data_range.end
    assert candidate.normalization_denominator == prepared.ticket.step_budget
    assert [event.state.value for event in result.telemetry.events] == [
        "RECEIVED",
        "ACCEPTED",
        "RUNNING",
        "COMPLETED",
    ]
    assert len(result.telemetry.metrics) == prepared.ticket.step_budget
    assert result.published.candidate_ref.locator.endswith("candidate.json")


def test_worker_run_ticket_cli_returns_machine_readable_result(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    prepared = prepare_round(tmp_path / "store", ticket_id="cli-ticket")
    input_dir = tmp_path / "inputs"
    input_dir.mkdir()
    ticket_path = input_dir / "ticket.json"
    config_path = input_dir / "config.json"
    schema_path = input_dir / "schema.json"
    tokenizer_ref_path = input_dir / "tokenizer-ref.json"
    ticket_path.write_bytes(canonical_json_bytes(prepared.ticket.to_dict()))
    config_path.write_bytes(canonical_json_bytes(prepared.config.to_dict()))
    schema_path.write_bytes(canonical_json_bytes(prepared.schema.to_dict()))
    tokenizer_ref_path.write_bytes(canonical_json_bytes(prepared.tokenizer_ref.to_dict()))

    assert (
        main(
            [
                "worker",
                "run-ticket",
                str(ticket_path),
                str(config_path),
                str(schema_path),
                str(tokenizer_ref_path),
                "--store-root",
                str(prepared.store.root),
                "--worker-id",
                "worker-cli-1",
            ]
        )
        == 0
    )
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "COMPLETED"
    assert output["ticket_id"] == "cli-ticket"
    assert output["telemetry"]["events"][-1]["state"] == "COMPLETED"
