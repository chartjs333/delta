from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest
from deltatorrent.artifacts.canonical_json import canonical_json_bytes, sha256_content_id
from deltatorrent.delta.builder import snapshot_fp32_parameters
from deltatorrent.delta.schema import derive_parameter_schema
from deltatorrent.domain.errors import DeltaError
from deltatorrent.domain.manifests import ArtifactRef
from deltatorrent.domain.parameters import ParameterSchema
from deltatorrent.domain.planes import WORKER_LOCAL_MEDIA_TYPES, require_distribution_eligible
from deltatorrent.domain.tickets import DomainPureWorkTicket
from deltatorrent.training.baseline import TrainingState
from deltatorrent.training.config import BaselineConfig
from deltatorrent.training.data import Tokenizer, load_samples
from deltatorrent.worker.validation import (
    LocalRoundLimits,
    arithmetic_profile_id,
    optimizer_profile_id,
)
from safetensors.torch import save as save_tensors

ROOT = Path(__file__).resolve().parents[3]
WORKER = ROOT / "delta-worker-python" / "src" / "deltatorrent"
PROTOCOL = ROOT / "delta-protocol"


def test_worker_local_media_is_rejected_at_distribution_boundary() -> None:
    for index, media_type in enumerate(sorted(WORKER_LOCAL_MEDIA_TYPES)):
        reference = ArtifactRef(
            content_id="sha256:" + str(index + 1) * 64,
            media_type=media_type,
            schema_id=(
                "SCHEMA-LOCAL-ROUND-COMPLETION-V1"
                if "completion" in media_type
                else "SCHEMA-NORMALIZED-CONTRIBUTION-CANDIDATE-V1"
            ),
            schema_version="1.0.0",
            byte_length=1,
            locator=f"local/{index}.json",
        )
        with pytest.raises(DeltaError, match="WORKER_LOCAL_ARTIFACT_FORBIDDEN"):
            require_distribution_eligible(reference)


def test_worker_execution_graph_has_no_native_jvm_validator_or_distribution_import() -> None:
    forbidden = ("delta_core_cpp", "delta_runtime_cpp", "delta_ffi", "delta_node_java", "netty")
    violations: list[str] = []
    for directory in ("delta", "training", "worker"):
        for path in (WORKER / directory).rglob("*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [item.name for item in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                else:
                    names = []
                if any(name.startswith(forbidden) for name in names):
                    violations.append(path.relative_to(ROOT).as_posix())
    assert violations == []


def test_smoke_ticket_and_feature004_inputs_are_content_bound_without_qbytes() -> None:
    ticket_value = json.loads(
        (ROOT / "configs/worker/smoke-ticket.json").read_text(encoding="utf-8")
    )
    schema_value = json.loads(
        (ROOT / "configs/worker/smoke-parameter-schema.json").read_text(encoding="utf-8")
    )
    ticket = DomainPureWorkTicket.from_dict(ticket_value)
    schema = ParameterSchema.from_dict(schema_value)
    assert ticket.parameter_schema_id == schema.fingerprint
    assert ticket.data_range.end - ticket.data_range.start == 16
    config = BaselineConfig.from_json_file(ROOT / "configs/baseline/cpu-smoke-v1.json")
    tokenizer_path = ROOT / config.tokenizer_path
    corpus_path = ROOT / config.corpus_path
    tokenizer = Tokenizer.from_json_file(tokenizer_path)
    samples = load_samples(corpus_path, tokenizer, config.sequence_length)
    state = TrainingState.create(config, len(samples))
    derived_schema = derive_parameter_schema(state.model)
    parent_bytes = save_tensors(snapshot_fp32_parameters(state.model, derived_schema))
    tokenizer_id = sha256_content_id(tokenizer_path.read_bytes())
    limits = LocalRoundLimits()
    assert ticket.data.content_id == sha256_content_id(corpus_path.read_bytes())
    assert ticket.parent_model.content_id == sha256_content_id(parent_bytes)
    assert ticket.parent_model.byte_length == len(parent_bytes)
    assert ticket.optimizer_profile_id == optimizer_profile_id(config)
    assert ticket.arithmetic_profile_id == arithmetic_profile_id(
        config,
        tokenizer_id=tokenizer_id,
        limits=limits,
    )

    fixture = json.loads(
        (PROTOCOL / "fixtures/local-round/feature004-encoder-inputs-v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert fixture["quantization_outputs_in_scope"] is False
    assert "qbytes" not in json.dumps(fixture).lower()
    tensor_source = fixture["normalized_fp32_reference"]
    assert (
        sha256_content_id(canonical_json_bytes(tensor_source))
        == fixture["normalized_source_content_id"]
    )
    for tensor in tensor_source["tensors"]:
        payload = bytes.fromhex(tensor["values_hex"])
        assert len(payload) == tensor["byte_length"]
        assert hashlib.sha256(payload).hexdigest() == tensor["sha256"]
    metadata = canonical_json_bytes(fixture["metadata"]["value"])
    assert metadata.hex() == fixture["metadata"]["expected_utf8_hex"]
    assert hashlib.sha256(metadata).hexdigest() == fixture["metadata"]["expected_sha256"]
