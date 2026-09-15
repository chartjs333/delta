"""Unit and cross-language tests for the canonical DRQ1 producer."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from deltatorrent.domain.manifests import ArtifactRef
from deltatorrent.domain.updates import NormalizedContributionCandidate
from deltatorrent.worker.drq1_producer import (
    produce_drq1_shards,
)


def _load_golden_fixture() -> dict[str, object]:
    fixture_path = (
        Path(__file__).resolve().parents[3]
        / "delta-protocol"
        / "fixtures"
        / "004"
        / "cross-language"
        / "golden-v1.json"
    )
    return json.loads(fixture_path.read_text(encoding="utf-8"))


def test_drq1_producer_golden_cross_language_conformance() -> None:
    golden = _load_golden_fixture()
    manifest = golden["manifest"]["value"]
    shard_plan = golden["shard_plan"]["value"]
    scale_table = golden["scale_table"]["value"]

    # Reconstruct the source vector values
    source_records = golden["normalized_source"]
    source_values = [
        float(int(item["numerator"]) / int(item["denominator"])) for item in source_records
    ]

    # Partition source into decoder.bias (4) and embedding.weight (32)
    decoder_bias = np.array(source_values[:4], dtype=np.float32)
    embedding_weight = np.array(source_values[4:], dtype=np.float32)

    candidate = NormalizedContributionCandidate(
        ticket_id=str(manifest["ticket_id"]),
        domain_id=str(manifest["domain_id"]),
        ticket_fingerprint="sha256:" + "a" * 64,
        completion_id="sha256:" + "b" * 64,
        parent_model_id="sha256:" + "c" * 64,
        parameter_schema_id=str(manifest["parameter_schema_id"]),
        optimizer_profile_id="sha256:" + "d" * 64,
        arithmetic_profile_id="sha256:" + "e" * 64,
        effective_steps=1,
        step_budget=1,
        normalization_denominator=1,
        normalized_delta=ArtifactRef(
            content_id="sha256:" + "f" * 64,
            media_type="application/vnd.safetensors",
            schema_id="SCHEMA-SAFETENSORS-V1",
            schema_version="1.0.0",
            byte_length=100,
            locator="tensors/delta.safetensors",
        ),
        tensor_order=("decoder.bias", "embedding.weight"),
    )

    tensors = {
        "decoder.bias": decoder_bias,
        "embedding.weight": embedding_weight,
    }

    scale_table_wrapped = {
        "content_id": golden["scale_table"]["content_id"],
        **scale_table,
    }
    shard_plan_wrapped = {
        "content_id": golden["shard_plan"]["content_id"],
        **shard_plan,
    }

    produced = produce_drq1_shards(
        candidate=candidate,
        tensors=tensors,
        scale_table=scale_table_wrapped,
        shard_plan=shard_plan_wrapped,
        proof_instance_id=str(golden["proof_instance"]["content_id"]),
        round_config_id=str(golden["fixedpoint_config"]["content_id"]),
        profile_id=str(golden["profile"]["content_id"]),
        formal_semantics_id=str(golden["formal_semantics_id"]),
    )

    # 1. Verify commitment root matches golden manifest
    assert produced.commitment_root == manifest["commitment_root"]

    # 2. Verify all shards match golden envelope hex and leaf IDs exactly
    golden_shards = golden["shards"]
    assert len(produced.shards) == len(golden_shards)

    for prod_shard, exp_shard in zip(produced.shards, golden_shards, strict=True):
        assert prod_shard.ordinal == exp_shard["ordinal"]
        assert prod_shard.leaf_id == exp_shard["leaf_id"]
        assert prod_shard.envelope.hex() == exp_shard["envelope_hex"]
        assert prod_shard.payload.hex() == exp_shard["payload_hex"]
        assert prod_shard.header["payload_sha256"] == exp_shard["header"]["payload_sha256"]


def test_drq1_producer_single_shard_mnist() -> None:
    # 7850 elements: 7840 weights + 10 biases
    weight = np.full((10, 784), 0.05, dtype=np.float32)
    bias = np.zeros((10,), dtype=np.float32)

    candidate = NormalizedContributionCandidate(
        ticket_id="ticket-mnist-001",
        domain_id="text",
        ticket_fingerprint="sha256:" + "1" * 64,
        completion_id="sha256:" + "2" * 64,
        parent_model_id="sha256:" + "3" * 64,
        parameter_schema_id="sha256:" + "4" * 64,
        optimizer_profile_id="sha256:" + "5" * 64,
        arithmetic_profile_id="sha256:" + "6" * 64,
        effective_steps=1,
        step_budget=1,
        normalization_denominator=1,
        normalized_delta=ArtifactRef(
            content_id="sha256:" + "7" * 64,
            media_type="application/vnd.safetensors",
            schema_id="SCHEMA-SAFETENSORS-V1",
            schema_version="1.0.0",
            byte_length=15700,
            locator="tensors/delta.safetensors",
        ),
        tensor_order=("bias", "weight"),
    )

    scale_table = {
        "content_id": "sha256:" + "a" * 64,
        "segments": [
            {
                "segment_id": "mnist.linear",
                "segment_ordinal": 0,
                "element_start": 0,
                "element_count": 7850,
                "quantum": {"numerator": "1", "denominator": 10000},
            }
        ],
        "total_elements": 7850,
    }

    shard_plan = {
        "content_id": "sha256:" + "b" * 64,
        "entries": [
            {
                "ordinal": 0,
                "segment_id": "mnist.linear",
                "segment_offset": 0,
                "element_start": 0,
                "element_count": 7850,
                "payload_bytes": 15700,
            }
        ],
        "total_elements": 7850,
    }

    produced = produce_drq1_shards(
        candidate=candidate,
        tensors={"weight": weight, "bias": bias},
        scale_table=scale_table,
        shard_plan=shard_plan,
        proof_instance_id="sha256:" + "8" * 64,
        round_config_id="sha256:" + "9" * 64,
    )

    assert len(produced.shards) == 1
    # Critical invariant: For single shard, merkle_root(leaves) == leaf_id!
    assert produced.commitment_root == produced.shards[0].leaf_id
    assert produced.shards[0].envelope[:4] == b"DRQ1"
    assert len(produced.shards[0].payload) == 7850 * 2
