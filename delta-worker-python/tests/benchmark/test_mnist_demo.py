from __future__ import annotations

import hashlib
import json
import struct
import threading
from dataclasses import fields
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest
from deltatorrent.benchmark import mnist_demo
from deltatorrent.benchmark.mnist_delta_nodes import (
    MODEL_MAGIC,
    NODE_COUNT,
    REQUIRED_VOTE_KINDS,
    TRACE_SCOPE,
    TYPED_CERTIFICATE_VERIFIER,
    VECTOR_WIDTH,
    VOTE_QUORUM_COMPONENT,
    AppliedModel,
    DeltaExecutionResult,
    NodeContribution,
    expected_central_model,
)
from deltatorrent.benchmark.mnist_demo import (
    MNIST_FILES,
    MnistDataset,
    MnistDemoError,
    NodeSummary,
    compute_summary,
    materialize_node_shards,
    prepare_mnist_cache,
    run_mnist_demo,
    run_node_summaries,
)
from deltatorrent.benchmark.mnist_demo_workspace import (
    WORKSPACE_HTML,
    _validate_workspace_report,
    _workspace_catalog,
    serve_workspace,
)


def _repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _synthetic_dataset() -> MnistDataset:
    train_labels = np.repeat(np.arange(10, dtype=np.uint8), 6)
    test_labels = np.repeat(np.arange(10, dtype=np.uint8), 2)

    def image(digit: int, variation: int) -> np.ndarray:
        value = np.zeros((28, 28), dtype=np.uint8)
        row = digit * 2 + 2
        column = 25 - digit * 2
        value[row : row + 2, 3:25] = 180 + variation
        value[3:25, column : column + 2] = 220 + variation
        return value

    train_images = np.stack(
        [image(int(digit), index % 2) for index, digit in enumerate(train_labels)]
    )
    test_images = np.stack(
        [image(int(digit), index % 2) for index, digit in enumerate(test_labels)]
    )
    return MnistDataset(
        source_id="sha256:" + "1" * 64,
        train_images=np.asarray(train_images, dtype=np.uint8),
        train_labels=train_labels,
        test_images=np.asarray(test_images, dtype=np.uint8),
        test_labels=test_labels,
    )


def test_stage_c_counter_write_is_atomic_for_concurrent_reader(tmp_path: Path) -> None:
    counter = tmp_path / "tx_bytes"
    mnist_demo._write_stage_c_counter(counter, 0)
    stop = threading.Event()
    observed_invalid: list[str] = []

    def read_counter() -> None:
        while not stop.is_set():
            try:
                text = counter.read_text(encoding="ascii").strip()
            except OSError:
                continue
            if not text.isdigit():
                observed_invalid.append(text)
                stop.set()

    reader = threading.Thread(target=read_counter)
    reader.start()
    try:
        for value in range(1, 1_000):
            mnist_demo._write_stage_c_counter(counter, value)
    finally:
        stop.set()
        reader.join(timeout=5.0)

    assert observed_invalid == []
    assert counter.read_text(encoding="ascii").strip() == "999"


def _patch_dataset(monkeypatch: pytest.MonkeyPatch, dataset: MnistDataset) -> None:
    monkeypatch.setattr(
        mnist_demo,
        "prepare_mnist_cache",
        lambda _cache, *, allow_download: {
            "source_id": dataset.source_id,
            "download_was_allowed": allow_download,
        },
    )
    monkeypatch.setattr(mnist_demo, "load_mnist", lambda _cache, _source_id: dataset)


def _patch_delta_nodes(monkeypatch: pytest.MonkeyPatch, dataset: MnistDataset) -> None:
    central_sums, central_counts = compute_summary(dataset.train_images, dataset.train_labels)
    central_values = expected_central_model(central_sums, central_counts)

    def fake_delta_nodes(
        _root: Path,
        destination: Path,
        _controllers: Path,
        node_contributions: tuple[NodeContribution, ...],
        _source_id: str,
        *,
        toolchain: object = None,
    ) -> DeltaExecutionResult:
        del toolchain
        destination.mkdir(parents=True)
        trace_path = destination / "execution-trace.json"
        diagram_path = destination / "execution-path.mmd"
        trace_path.write_text('{"status":"PASS"}\n', encoding="utf-8")
        diagram_path.write_text("flowchart LR\n", encoding="utf-8")
        raw = MODEL_MAGIC + struct.pack(">I", VECTOR_WIDTH) + central_values.astype(">i2").tobytes()
        model = AppliedModel(
            raw_bytes=raw,
            content_id=f"sha256:{hashlib.sha256(raw).hexdigest()}",
            centroids=central_values[: 10 * 28 * 28].reshape(10, 28 * 28).astype(np.int64),
            presence=central_values[10 * 28 * 28 :].astype(np.int64),
            values=central_values,
        )
        proposal_components = (
            "delta::certificates::InputSetCertificate",
            "delta::robust::build_plan",
            "delta::robust::build_plan",
            "delta::robust::reduce_parameter_shard",
            "delta::certificates::aggregate_merkle_root",
            "delta::apply::compute_candidate",
        )
        vote_actions = (
            "ACT-ISC-VOTE",
            "ACT-EC-VOTE",
            "ACT-APC-VOTE",
            "ACT-PARAM-VOTE",
            "ACT-ROOT-VOTE",
            "ACT-APPLY-VOTE",
        )
        trace_kinds = (
            "ISC",
            "EC",
            "APC",
            "PARAMETER_SHARD_QC",
            "AGGREGATE_ROOT_QC",
            "APPLY_QC",
        )
        typed_ids = [f"sha256:{index + 10:064x}" for index in range(len(REQUIRED_VOTE_KINDS))]
        quorum_ids = [f"sha256:{index + 20:064x}" for index in range(len(REQUIRED_VOTE_KINDS))]
        phase_execution = [
            {
                "body_hash": typed_ids[index],
                "certifying_nodes": NODE_COUNT,
                "delivered_vote_count_per_receiver": NODE_COUNT,
                "execution_order": [
                    "typed_body_proposed",
                    "vote_persisted",
                    "four_netty_deliveries",
                    "generic_vote_quorum_validated",
                    "typed_certificate_verified",
                    "generic_qc_durably_finalized",
                ],
                "parent_gate_enforced": True,
                "phase": phase,
                "position": index + 1,
                "proposal_component": proposal_components[index],
                "qc_durable_finalize_action_id": "OBS-CURRENT-QC-DURABLY-FINALIZED",
                "required_parent_typed_certificate_id": (typed_ids[index - 1] if index else None),
                "required_parent_vote_quorum_id": quorum_ids[index - 1] if index else None,
                "transport_component": "io.deltareduce.demo.MnistDeltaNettyRelay",
                "typed_certificate_action_id": "OBS-TYPED-CERT-VERIFIED-AFTER-QC",
                "typed_certificate_id": typed_ids[index],
                "typed_certificate_verification_after_vote_quorum": True,
                "typed_certificate_verifier": TYPED_CERTIFICATE_VERIFIER,
                "validated_parent_typed_certificate_ids": typed_ids[:index],
                "validated_parent_vote_quorum_ids": quorum_ids[:index],
                "vote_action_id": vote_actions[index],
                "vote_frames_relayed_per_receiver": NODE_COUNT,
                "vote_persistence_component": "delta::runtime::CertificateVoteRuntime",
                "vote_quorum_action_id": "OBS-CURRENT-VOTE-QUORUM-VALIDATED",
                "vote_quorum_component": VOTE_QUORUM_COMPONENT,
                "vote_quorum_id": quorum_ids[index],
            }
            for index, phase in enumerate(REQUIRED_VOTE_KINDS)
        ]
        quorum_certificates = [
            {
                "body_hash": typed_ids[index],
                "context_id": f"{trace_kinds[index]}:demo:1:0",
                "kind": phase,
                "qc_id": quorum_ids[index],
                "signer_count": NODE_COUNT,
                "threshold": 3,
            }
            for index, phase in enumerate(REQUIRED_VOTE_KINDS)
        ]
        delta_execution: dict[str, object] = {
            "aggregation_authority": "delta::robust::reduce_parameter_shard",
            "apply_qc_id": typed_ids[-1],
            "applied_model_file_sha256": model.content_id,
            "authoritative": False,
            "certificate_signature_semantics": "CONTENT_ID_PLACEHOLDER_LOCAL_DEMO_ONLY",
            "classification": "LOCAL_DEMO_ONLY",
            "components": [
                {"component": name, "evidence": {}, "sequence": index, "status": "PASS"}
                for index, name in enumerate(
                    (
                        "deltatorrent.benchmark.mnist_demo",
                        "io.deltareduce.demo.MnistDeltaNettyRelay",
                        "delta::runtime::CertificateVoteRuntime",
                        VOTE_QUORUM_COMPONENT,
                        TYPED_CERTIFICATE_VERIFIER,
                        "delta::robust::build_plan",
                        "delta::robust::reduce_parameter_shard",
                        "delta::apply::compute_candidate",
                        "delta::runtime::CurrentPointerStore",
                    ),
                    start=1,
                )
            ],
            "contributions_bound_netty_to_native": True,
            "current_pointer": {
                "apply_qc_id": typed_ids[-1],
                "disposition": "ADVANCED",
                "height": 1,
            },
            "demo_owned_aggregation": False,
            "execution_authorized": False,
            "execution_path_id": "sha256:" + "2" * 64,
            "distributed_orchestrator_received_node_local_numeric_arrays": False,
            "formal_refinement_claimed": False,
            "governance_eligible": False,
            "native_cryptographic_signatures_verified": False,
            "phase_execution": phase_execution,
            "phase_ordering_enforced": True,
            "protocol_scope": "MNIST_WORKLOAD_TO_APPLIED_LOCAL_DELTA",
            "python_cross_node_aggregation_performed": False,
            "python_vote_quorum_assembly_performed": False,
            "quorum_certificates": quorum_certificates,
            "semantic_completeness_claimed": False,
            "status": "PASS",
            "terminal_outcome": "APPLIED",
            "trace_scope": TRACE_SCOPE,
            "toolchain": {
                "source_snapshot": {
                    "no_hidden_aggregation_static_gate": "PASS",
                    "semantic_completeness_claimed": False,
                }
            },
            "typed_certificate_verifier": TYPED_CERTIFICATE_VERIFIER,
            "vote_quorum_component": VOTE_QUORUM_COMPONENT,
        }
        return DeltaExecutionResult(
            applied_model=model,
            delta_execution=delta_execution,
            execution_trace_path=trace_path,
            execution_diagram_path=diagram_path,
            failure_simulation={
                "failed_node_id": "validator-04",
                "protocol_accepted_after_recovery": True,
                "replay_observed": True,
                "status": "RECOVERED_AND_APPLIED",
                "terminal_outcome": "APPLIED",
            },
            node_contributions=node_contributions,
        )

    monkeypatch.setattr(mnist_demo, "run_delta_nodes", fake_delta_nodes)


def _patch_stage_c(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_stage_c(
        _root: Path,
        destination: Path,
        node_contributions: tuple[NodeContribution, ...],
        _source_id: str,
        *,
        boundary: object,
    ) -> object:
        del boundary
        destination.mkdir(parents=True)
        evidence_path = destination / "stagec-real-drq1-evidence.json"
        evidence = {
            "python_cross_node_aggregation_performed": False,
            "single_shard_scope": True,
            "synthetic_contribution_fallback_allowed": False,
        }
        evidence_path.write_text(json.dumps(evidence), encoding="utf-8")
        causal = SimpleNamespace(
            current_pointer_after="sha256:" + "b" * 64,
            current_pointer_before="sha256:" + "a" * 64,
            isc_ticket_set=tuple(f"ticket-{index:03d}" for index in range(4)),
            missing_work_policy_result="FULL_QUORUM_DELIVERED_EXACT_ISC",
        )
        transition = SimpleNamespace(
            causal_evidence=causal,
            current_checkpoint_advanced=True,
            native_wal_sha256="sha256:" + "c" * 64,
            observed_outcome="APPLIED",
        )
        receipt = SimpleNamespace(
            fault_transitions=(transition,),
            native_fault_trace_id="sha256:" + "d" * 64,
            raw_java_receipt_id="sha256:" + "e" * 64,
        )
        return SimpleNamespace(
            evaluation_checkpoint_id="sha256:" + "b" * 64,
            evidence=evidence,
            evidence_path=evidence_path,
            final_checkpoint_id="sha256:" + "b" * 64,
            receipt=receipt,
            ticket_ids=tuple(f"ticket-{index:03d}" for index in range(4)),
            worker_shard_leaf_ids=tuple(
                (f"ticket-{index:03d}", f"sha256:{index + 40:064x}") for index in range(4)
            ),
        )

    monkeypatch.setattr(
        mnist_demo,
        "_resolve_stage_c_boundary_from_environment",
        lambda _destination: (object(), False),
    )
    monkeypatch.setattr(mnist_demo, "run_stage_c_real_drq1_nodes", fake_stage_c)


def test_mnist_sources_are_content_pinned() -> None:
    assert len(MNIST_FILES) == 4
    assert len({item.filename for item in MNIST_FILES}) == 4
    assert all(len(item.sha256) == 64 for item in MNIST_FILES)
    assert all(item.size_bytes > 0 for item in MNIST_FILES)
    assert all(item.url.startswith("https://storage.googleapis.com/") for item in MNIST_FILES)


def test_offline_cache_fails_closed_when_a_pinned_source_is_missing(tmp_path: Path) -> None:
    with pytest.raises(MnistDemoError, match="MNIST_SOURCE_MISSING_OFFLINE"):
        prepare_mnist_cache(tmp_path / "empty-cache", allow_download=False)


def test_four_label_skew_shards_are_disjoint_and_exact(tmp_path: Path) -> None:
    dataset = _synthetic_dataset()
    manifests = materialize_node_shards(
        dataset.train_images,
        dataset.train_labels,
        tmp_path / "nodes",
    )

    assert len(manifests) == 4
    observed_counts = np.sum(
        np.asarray([manifest["label_counts"] for manifest in manifests], dtype=np.int64),
        axis=0,
    )
    assert np.array_equal(observed_counts, np.bincount(dataset.train_labels, minlength=10))
    for manifest in manifests:
        allowed = set(cast(list[int], manifest["allowed_digits"]))
        counts = cast(list[int], manifest["label_counts"])
        assert all(count == 0 for digit, count in enumerate(counts) if digit not in allowed)


def test_workers_return_opaque_contributions_not_numeric_model_sums(tmp_path: Path) -> None:
    dataset = _synthetic_dataset()
    node_root = tmp_path / "nodes"
    manifests = materialize_node_shards(dataset.train_images, dataset.train_labels, node_root)
    node_dirs = tuple(node_root / f"demo-mnist-worker-{index:02d}" for index in range(1, 5))
    shard_ids = {
        cast(str, manifest["node_id"]): cast(str, manifest["shard_id"]) for manifest in manifests
    }
    summaries = run_node_summaries(node_dirs, shard_ids)
    assert len(summaries) == 4
    assert len({summary.process_id for summary in summaries}) == 4
    assert sum(summary.contribution.sample_count for summary in summaries) == int(
        dataset.train_labels.size
    )
    for summary in summaries:
        assert summary.contribution.record_path.is_file()
        assert summary.contribution.size_bytes == summary.contribution.record_path.stat().st_size
        assert not hasattr(summary, "counts")
        assert not hasattr(summary, "sums")


def test_production_demo_has_no_cross_node_python_aggregation() -> None:
    root = _repository_root()
    demo_source = (root / "delta-worker-python/src/deltatorrent/benchmark/mnist_demo.py").read_text(
        encoding="utf-8"
    )
    integration_source = (
        root / "delta-worker-python/src/deltatorrent/benchmark/mnist_delta_nodes.py"
    ).read_text(encoding="utf-8")
    native_source = (root / "integration/mnist-delta/native/mnist_delta_node.cpp").read_text(
        encoding="utf-8"
    )
    java_source = (
        root / "integration/mnist-delta/java/io/deltareduce/demo/MnistDeltaNettyRelay.java"
    ).read_text(encoding="utf-8")

    assert "def aggregate_summaries" not in demo_source
    assert "def aggregate_summaries" not in integration_source
    assert "node_contributions: Sequence[NodeContribution]" in integration_source
    assert "tuple(summary.contribution for summary in node_summaries)" in demo_source
    assert "sums" not in {field.name for field in fields(NodeSummary)}
    assert "run_delta_nodes(" in demo_source
    assert "delta::robust::reduce_parameter_shard" in native_source
    assert "consensus::validate_quorum" in native_source
    assert "certificates::ChainVerifier" in native_source
    assert "delta::apply::compute_candidate" in native_source
    assert "runtime::CurrentPointerStore" in native_source
    assert 'options.mode == "vote-phase"' in native_source
    assert 'options.mode == "certify-phase"' in native_source
    assert "build_chain(" not in native_source
    assert "BenchmarkTransport" in java_source
    assert "NioServerSocketChannel" in java_source


def test_checked_in_trace_excerpt_documents_observed_delta_execution_path() -> None:
    trace = json.loads(
        (_repository_root() / "integration/mnist-delta/example-execution-trace.json").read_text(
            encoding="utf-8"
        )
    )
    expected_components = [
        "deltatorrent.benchmark.mnist_demo",
        "io.deltareduce.demo.MnistDeltaNettyRelay",
        "delta::runtime::CertificateVoteRuntime",
        "delta::core::consensus::validate_quorum",
        "delta::certificates::ChainVerifier",
        "delta::robust::build_plan",
        "delta::robust::reduce_parameter_shard",
        "delta::apply::compute_candidate",
        "delta::runtime::CurrentPointerStore",
    ]

    assert trace["type_name"] == "MNIST_DELTA_VERIFIED_RUN_TRACE_EXCERPT"
    assert trace["actual_run"] is True
    assert trace["classification"] == "LOCAL_DEMO_ONLY"
    assert trace["authoritative"] is False
    assert trace["governance_eligible"] is False
    assert trace["execution_authorized"] is False
    assert trace["formal_refinement_claimed"] is False
    assert trace["semantic_completeness_claimed"] is False
    assert trace["trace_scope"] == TRACE_SCOPE
    assert trace["terminal_outcome"] == "APPLIED"
    assert trace["python_cross_node_aggregation_performed"] is False
    assert trace["python_vote_quorum_assembly_performed"] is False
    assert trace["demo_owned_aggregation"] is False
    assert trace["native_cryptographic_signatures_verified"] is False
    assert trace["certificate_signature_semantics"] == "CONTENT_ID_PLACEHOLDER_LOCAL_DEMO_ONLY"
    assert trace["vote_quorum_component"] == VOTE_QUORUM_COMPONENT
    assert trace["typed_certificate_verifier"] == TYPED_CERTIFICATE_VERIFIER
    assert trace["exact_model_match_with_centralized"] is True
    assert trace["centralized_accuracy_ppm"] == trace["distributed_accuracy_ppm"]
    assert trace["dataset"]["train_samples"] == 60_000
    assert trace["dataset"]["test_samples"] == 10_000
    assert trace["toolchain"]["java_feature"] == 25
    assert trace["network"]["ed25519_verified"] is True
    assert trace["network"]["native_receipts_bound_contribution_ids"] is True
    assert trace["network"]["netty_loopback_receipts"] == 28
    assert trace["network"]["vote_frames_per_phase_receiver"] == 4
    assert len(trace["contribution_ids"]) == 4
    assert trace["native_results"] == {
        "applied": 4,
        "qcs_finalized": 24,
        "votes_exposed": 24,
    }
    assert trace["phase_ordering_enforced"] is True
    assert [item["phase"] for item in trace["phase_execution"]] == [
        "input_set",
        "eligibility",
        "aggregation_plan",
        "parameter_shard",
        "aggregate_root",
        "apply",
    ]
    phase_execution = trace["phase_execution"]
    assert [item["position"] for item in phase_execution] == list(range(1, 7))
    assert all(
        "certificate_id" not in item
        and "certificate_component" not in item
        and "required_parent_qc_id" not in item
        for item in phase_execution
    )
    assert [item["proposal_component"] for item in phase_execution] == [
        "delta::certificates::InputSetCertificate",
        "delta::robust::build_plan",
        "delta::robust::build_plan",
        "delta::robust::reduce_parameter_shard",
        "delta::certificates::aggregate_merkle_root",
        "delta::apply::compute_candidate",
    ]
    assert phase_execution[0]["required_parent_typed_certificate_id"] is None
    assert phase_execution[0]["required_parent_vote_quorum_id"] is None
    assert all(
        phase_execution[index]["required_parent_typed_certificate_id"]
        == phase_execution[index - 1]["typed_certificate_id"]
        and phase_execution[index]["required_parent_vote_quorum_id"]
        == phase_execution[index - 1]["vote_quorum_id"]
        for index in range(1, len(phase_execution))
    )
    assert all(
        item["validated_parent_typed_certificate_ids"]
        == [parent["typed_certificate_id"] for parent in phase_execution[:index]]
        and item["validated_parent_vote_quorum_ids"]
        == [parent["vote_quorum_id"] for parent in phase_execution[:index]]
        for index, item in enumerate(phase_execution)
    )
    assert all(item["certifying_nodes"] == 4 for item in phase_execution)
    assert all(item["delivered_vote_count_per_receiver"] == 4 for item in phase_execution)
    assert all(item["vote_frames_relayed_per_receiver"] == 4 for item in phase_execution)
    assert all(
        item["vote_persistence_component"] == "delta::runtime::CertificateVoteRuntime"
        and item["transport_component"] == "io.deltareduce.demo.MnistDeltaNettyRelay"
        and item["vote_quorum_component"] == "delta::core::consensus::validate_quorum"
        and item["typed_certificate_verifier"] == "delta::certificates::ChainVerifier"
        and item["vote_quorum_action_id"] == "OBS-CURRENT-VOTE-QUORUM-VALIDATED"
        and item["typed_certificate_action_id"] == "OBS-TYPED-CERT-VERIFIED-AFTER-QC"
        and item["qc_durable_finalize_action_id"] == "OBS-CURRENT-QC-DURABLY-FINALIZED"
        and item["typed_certificate_verification_after_vote_quorum"] is True
        and item["parent_gate_enforced"] is True
        and item["typed_certificate_id"] == item["body_hash"]
        and item["vote_quorum_id"] != item["typed_certificate_id"]
        for item in phase_execution
    )
    assert {item["typed_certificate_id"] for item in phase_execution}.isdisjoint(
        {item["vote_quorum_id"] for item in phase_execution}
    )
    assert all(
        item["execution_order"]
        == [
            "typed_body_proposed",
            "vote_persisted",
            "four_netty_deliveries",
            "generic_vote_quorum_validated",
            "typed_certificate_verified",
            "generic_qc_durably_finalized",
        ]
        for item in phase_execution
    )
    assert [item["component"] for item in trace["components"]] == expected_components
    assert [item["sequence"] for item in trace["components"]] == list(range(1, 10))
    assert all(item["status"] == "PASS" for item in trace["components"])
    assert len(trace["quorum_certificates"]) == 6
    assert all(item["threshold"] == 3 for item in trace["quorum_certificates"])
    assert all(item["signer_count"] == 4 for item in trace["quorum_certificates"])
    assert [item["body_hash"] for item in trace["quorum_certificates"]] == [
        item["typed_certificate_id"] for item in phase_execution
    ]
    assert [item["qc_id"] for item in trace["quorum_certificates"]] == [
        item["vote_quorum_id"] for item in phase_execution
    ]
    assert trace["apply_qc_id"] == phase_execution[-1]["typed_certificate_id"]
    assert trace["current_pointer"]["apply_qc_id"] == phase_execution[-1]["typed_certificate_id"]
    assert trace["recovery"]["crash_point"] == ("AFTER_DURABLE_APPLY_VOTE_BEFORE_EXPOSE")
    assert trace["recovery"]["replay_observed"] is True
    assert trace["recovery"]["status"] == "RECOVERED_AND_APPLIED"
    assert trace["source_execution_trace_bytes"] > 500_000
    assert trace["source_execution_trace_sha256"].startswith("sha256:")


def test_run_uses_applied_delta_model_and_real_recovery_contract(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset = _synthetic_dataset()
    _patch_dataset(monkeypatch, dataset)
    _patch_delta_nodes(monkeypatch, dataset)
    _patch_stage_c(monkeypatch)

    result = run_mnist_demo(
        _repository_root(),
        tmp_path / "cache",
        tmp_path / "run",
        allow_download=False,
    )
    report = json.loads(result.report_json.read_text(encoding="utf-8"))

    assert report["demo_status"] == "DEMO_PASS"
    assert report["authoritative"] is False
    assert report["governance_eligible"] is False
    assert report["execution_authorized"] is False
    assert report["feature_010_go_claimed"] is False
    assert report["dataset"]["name"] == "MNIST"
    assert report["dataset"]["dataset_id"] == "mnist-v1"
    assert report["dataset"]["sample_kind"] == "image/grayscale-28x28"
    assert report["dataset"]["target_kind"] == "class-id/0-9"
    assert report["model"]["plugin_id"] == "mnist-centroid-v1"
    assert report["model"]["sample_kind"] == "image/grayscale-28x28"
    assert report["model"]["target_kind"] == "class-id/0-9"
    assert report["model_dataset_binding"] == {
        "contract_compatibility": "PASS",
        "dataset_id": "mnist-v1",
        "model_plugin_id": "mnist-centroid-v1",
        "runner_boundary": "ModelDatasetBinding",
        "sample_kind": "image/grayscale-28x28",
        "target_kind": "class-id/0-9",
        "type_name": "DELTAREDUCE_MODEL_DATASET_BINDING_EVIDENCE",
    }
    multi_domain = report["multi_domain"]
    assert multi_domain["type_name"] == "DELTAREDUCE_MULTI_DOMAIN_DEMO_STRUCTURE"
    assert multi_domain["model_dataset_runner"] == "MultiDomainBinding"
    assert multi_domain["domain_count"] == 3
    assert multi_domain["delta_stage_c_domain_count"] == 1
    assert multi_domain["active_stage_c_domain_id"] == "mnist-image"
    assert multi_domain["cross_domain_aggregation_performed"] is False
    assert multi_domain["registry_backed"] is True
    domains = {item["domain_id"]: item for item in multi_domain["domains"]}
    assert set(domains) == {"mnist-image", "qlora-adapter", "eeg-bandpower"}

    # MNIST: Live Stage C execution
    assert domains["mnist-image"]["requested_execution_scope"] == "STAGE_C_REAL_DRQ1"
    assert domains["mnist-image"]["verified_execution_evidence"] == "LIVE_STAGE_C_APPLIED_RECEIPT"
    assert domains["mnist-image"]["delta_stage_c_execution_claimed"] is True
    assert domains["mnist-image"]["live_consensus_claimed_in_this_run"] is True
    assert domains["mnist-image"]["checkpoint_accuracy_claimed_from_stage_c"] is False
    assert domains["mnist-image"]["python_cross_node_aggregation_performed"] is False
    assert domains["mnist-image"]["raw_samples_shared_outside_provider"] is False
    assert domains["mnist-image"]["stage_c_execution_mode"] == "REAL_DRQ1"
    assert domains["mnist-image"]["stage_c_outcome"] == "APPLIED"

    # QLoRA: Stage C capable, verified via historical trajectory anchor
    assert domains["qlora-adapter"]["requested_execution_scope"] == "STAGE_C_REAL_DRQ1"
    assert (
        domains["qlora-adapter"]["verified_execution_evidence"]
        == "NO_LIVE_EXECUTION_EVIDENCE_IN_CURRENT_WORKSPACE_RUN"
    )
    assert domains["qlora-adapter"]["reference_anchor_evidence"] == (
        "HISTORICAL_TRAJECTORY_ANCHOR_VERIFIED"
    )
    assert domains["qlora-adapter"]["reference_anchor_is_current_workspace_receipt"] is False
    assert domains["qlora-adapter"]["delta_stage_c_execution_claimed"] is False
    assert domains["qlora-adapter"]["live_consensus_claimed_in_this_run"] is False
    assert domains["qlora-adapter"]["reference_trajectory_anchor"] == (
        "437558d886d4fc7aac4d8a72f2e4d69696fab7f7"
    )
    assert domains["qlora-adapter"]["supports_stage_c_real_drq1"] is True
    assert domains["qlora-adapter"]["checkpoint_accuracy_claimed_from_stage_c"] is False
    assert domains["qlora-adapter"]["python_cross_node_aggregation_performed"] is False
    assert domains["qlora-adapter"]["raw_samples_shared_outside_provider"] is False
    assert domains["qlora-adapter"]["stage_c_execution_mode"] is None
    assert domains["qlora-adapter"]["stage_c_outcome"] is None
    assert domains["qlora-adapter"]["total_elements"] == 8

    # EEG: Model/dataset binding smoke, observation only
    assert domains["eeg-bandpower"]["requested_execution_scope"] == "MODEL_DATASET_BINDING_ONLY"
    assert domains["eeg-bandpower"]["verified_execution_evidence"] == "LOCAL_PLUGIN_WORKER_SMOKE"
    assert domains["eeg-bandpower"]["delta_stage_c_execution_claimed"] is False
    assert domains["eeg-bandpower"]["live_consensus_claimed_in_this_run"] is False
    assert domains["eeg-bandpower"]["supports_stage_c_real_drq1"] is False
    assert domains["eeg-bandpower"]["checkpoint_accuracy_claimed_from_stage_c"] is False
    assert domains["eeg-bandpower"]["python_cross_node_aggregation_performed"] is False
    assert domains["eeg-bandpower"]["raw_samples_shared_outside_provider"] is False
    assert domains["eeg-bandpower"]["stage_c_execution_mode"] is None
    assert domains["eeg-bandpower"]["total_elements"] == 34

    assert any(
        item["plugin_id"] == "qlora-tiny-adapter-v1" for item in report["registry"]["model_plugins"]
    )
    assert any(
        item["dataset_id"] == "tiny-qlora-regression-v1" for item in report["registry"]["datasets"]
    )
    assert any(
        item["plugin_id"] == "eeg-bandpower-centroid-v1"
        for item in report["registry"]["model_plugins"]
    )
    assert any(
        item["dataset_id"] == "eeg-synthetic-bci-v1" for item in report["registry"]["datasets"]
    )
    qlora_showcase = report["plugin_showcase"]["qlora_adapter"]
    assert qlora_showcase["type_name"] == "DELTAREDUCE_QLORA_PLUGIN_SHOWCASE"
    assert qlora_showcase["model_plugin_id"] == "qlora-tiny-adapter-v1"
    assert qlora_showcase["dataset_id"] == "tiny-qlora-regression-v1"
    assert qlora_showcase["runner_boundary"] == "ModelDatasetBinding"
    assert qlora_showcase["contract_compatibility"] == "PASS"
    assert qlora_showcase["sample_kind"] == "vector/tiny-qlora-2d"
    assert qlora_showcase["target_kind"] == "regression/vector-2d"
    assert qlora_showcase["worker_count"] == 4
    assert qlora_showcase["total_elements"] == 8
    assert qlora_showcase["delta_stage_c_execution_claimed"] is False
    assert qlora_showcase["live_consensus_claimed_in_this_run"] is False
    assert qlora_showcase["supports_stage_c_real_drq1"] is True
    assert qlora_showcase["trajectory_anchor_verified"] is True
    assert qlora_showcase["reference_trajectory_anchor"] == (
        "437558d886d4fc7aac4d8a72f2e4d69696fab7f7"
    )
    assert (
        qlora_showcase["verified_execution_evidence"]
        == "NO_LIVE_EXECUTION_EVIDENCE_IN_CURRENT_WORKSPACE_RUN"
    )
    assert qlora_showcase["reference_anchor_evidence"] == "HISTORICAL_TRAJECTORY_ANCHOR_VERIFIED"
    assert qlora_showcase["reference_anchor_is_current_workspace_receipt"] is False
    eeg_showcase = report["plugin_showcase"]["eeg_bandpower"]
    assert eeg_showcase["type_name"] == "DELTAREDUCE_EEG_PLUGIN_SHOWCASE"
    assert eeg_showcase["model_plugin_id"] == "eeg-bandpower-centroid-v1"
    assert eeg_showcase["dataset_id"] == "eeg-synthetic-bci-v1"
    assert eeg_showcase["runner_boundary"] == "ModelDatasetBinding"
    assert eeg_showcase["contract_compatibility"] == "PASS"
    assert eeg_showcase["sample_kind"] == "eeg/bandpower-4ch-4band"
    assert eeg_showcase["target_kind"] == "class-id/0-1"
    assert eeg_showcase["worker_count"] == 4
    assert eeg_showcase["total_elements"] == 34
    assert eeg_showcase["delta_stage_c_execution_claimed"] is False
    assert eeg_showcase["python_cross_node_aggregation_performed"] is False
    assert eeg_showcase["raw_eeg_shared_outside_provider"] is False
    first_eeg_worker = eeg_showcase["workers"][0]
    first_ticket_context = first_eeg_worker["first_ticket_context"]
    assert first_eeg_worker["ticket_context_count"] == 40
    assert first_eeg_worker["point_semantics_in_ticket_context"] is False
    assert set(first_ticket_context) == {
        "acquisition_profile_id",
        "binding_assertion_id",
        "binding_authority_id",
        "binding_decision_id",
        "binding_schema_version",
        "data_window_id",
        "intervention_event_id",
        "preprocessing_profile_id",
        "raw_data_hash",
        "resolved_binding_set_id",
        "session_id",
    }
    assert first_ticket_context["binding_schema_version"] == "1.0.0"
    assert first_ticket_context["binding_assertion_id"].startswith("sha256:")
    assert first_ticket_context["binding_decision_id"].startswith("sha256:")
    assert first_ticket_context["resolved_binding_set_id"].startswith("sha256:")
    assert first_ticket_context["intervention_event_id"].startswith("evt-demo-eeg-")
    assert first_ticket_context["data_window_id"].startswith("eegwin-demo-")
    assert first_ticket_context["raw_data_hash"].startswith("sha256:")
    temporal_binding = eeg_showcase["temporal_binding"]
    assert temporal_binding["type_name"] == "DELTAREDUCE_TEMPORAL_EVENT_BINDING_EVIDENCE"
    assert (
        temporal_binding["binding_layer"]
        == "deltatorrent.data.binding.BindingProvider/BindingAuthority/ResolvedBindingSet"
    )
    assert temporal_binding["assertion_schema_version"] == "1.0.0"
    assert temporal_binding["assertion_count"] == 160
    assert temporal_binding["accepted_count"] == 160
    assert temporal_binding["rejected_count"] == 0
    assert temporal_binding["review_count"] == 0
    assert temporal_binding["window_count"] == 160
    assert temporal_binding["event_count"] == 4
    assert temporal_binding["binding_provider_id"] == "eeg-window-rule-provider-v1"
    assert temporal_binding["binding_provider_type"] == "RULE"
    assert temporal_binding["binding_authority_id"] == "eeg-demo-binding-authority-v1"
    assert temporal_binding["resolved_binding_set_id"].startswith("sha256:")
    assert (
        temporal_binding["relation_contract"]
        == "EegWindow.intervention_event_id == InterventionEvent.intervention_event_id"
    )
    assert temporal_binding["point_id_exposed_to_ticket_context"] is False
    assert temporal_binding["model_plugin_creates_intervention_event"] is False
    assert temporal_binding["delta_spine_knows_medical_semantics"] is False
    assert temporal_binding["ticket_context_contains_ids_hashes_only"] is True
    assert len(temporal_binding["examples"]) == 4
    first_binding = temporal_binding["examples"][0]
    assert first_binding["binding_assertion_id"] == first_ticket_context["binding_assertion_id"]
    assert first_binding["binding_decision_id"] == first_ticket_context["binding_decision_id"]
    assert (
        first_binding["resolved_binding_set_id"] == first_ticket_context["resolved_binding_set_id"]
    )
    assert first_binding["intervention_event_id"] == first_ticket_context["intervention_event_id"]
    assert first_binding["data_window_id"] == first_ticket_context["data_window_id"]
    assert first_binding["session_id"] == first_ticket_context["session_id"]
    assert first_binding["raw_data_hash"] == first_ticket_context["raw_data_hash"]
    assert first_binding["binding_provider_id"] == "eeg-window-rule-provider-v1"
    assert first_binding["binding_provider_type"] == "RULE"
    assert first_binding["binding_status"] == "PROPOSED"
    assert first_binding["binding_authority_id"] == "eeg-demo-binding-authority-v1"
    assert first_binding["authority_decision"] == "ACCEPTED"
    assert first_binding["reason_code"] == "RULE_EVENT_WINDOW_CONTEXT_MATCH"
    assert first_binding["point_id"] == "TCM-ST36"
    assert first_binding["point_source"] == "InterventionEvent.point_id"
    assert first_binding["laterality"] == "left"
    assert first_binding["intervention_type"] == "acupuncture_injection"
    assert first_binding["protocol_id"] == "protocol-demo-eeg-st36-v1"
    assert "point_id" not in first_ticket_context
    assert "laterality" not in first_ticket_context
    assert "intervention_type" not in first_ticket_context
    assert "protocol_id" not in first_ticket_context
    assert "relation" not in first_ticket_context
    assert "start_offset_ms" not in first_ticket_context
    assert "end_offset_ms" not in first_ticket_context
    observation_demo = eeg_showcase["observation_demo"]
    assert observation_demo["type_name"] == "DELTAREDUCE_EEG_OBSERVATION_DEMO"
    assert observation_demo["event_id"] == "evt-demo-eeg-01"
    assert observation_demo["clinical_conclusion_claimed"] is False
    assert observation_demo["recommendation_claimed"] is False
    assert observation_demo["delta_spine_modified"] is False
    assert observation_demo["binding_semantics_in_delta"] is False
    response = observation_demo["response"]
    assert response["type_name"] == "DELTAREDUCE_EEG_RESPONSE_ANALYSIS_RESULT"
    assert response["intervention_event_id"] == "evt-demo-eeg-01"
    assert response["baseline_window_count"] > 0
    assert response["post_window_count"] > 0
    assert response["clinical_conclusion_claimed"] is False
    assert response["recommendation_claimed"] is False
    assert report["distributed"]["exact_model_match_with_centralized"] is True
    assert report["distributed"]["aggregation_owner"] == ("delta::robust::reduce_parameter_shard")
    assert report["distributed"]["native_runtime_terminal"] == "APPLIED"
    assert report["distributed"]["parallel_processes_observed"] == 4
    assert report["distributed"]["worker_processes_required"] == 4
    assert report["distributed"]["stage_c_execution_mode"] == "REAL_DRQ1"
    assert report["distributed"]["stage_c_checkpoint_advanced"] is True
    assert report["centralized"]["evaluation"] == report["distributed"]["evaluation"]
    assert report["delta_execution"]["python_cross_node_aggregation_performed"] is False
    assert report["delta_execution"]["terminal_outcome"] == "APPLIED"
    assert report["stage_c_execution"]["execution_mode"] == "REAL_DRQ1"
    assert report["stage_c_execution"]["worker_count"] == 4
    assert report["stage_c_execution"]["isc_ticket_count"] == 4
    assert report["stage_c_execution"]["outcome"] == "APPLIED"
    assert report["stage_c_execution"]["checkpoint_advanced"] is True
    assert report["stage_c_execution"]["synthetic_fallback"] is False
    assert report["stage_c_execution"]["stage_c_checkpoint_accuracy_claimed"] is False
    assert report["model"]["stage_c_checkpoint_accuracy_claimed"] is False
    assert report["execution_path"]["acceptance_status"] == "PASS"
    assert report["execution_path"]["demo_owned_aggregation"] is False
    assert report["execution_path"]["existing_delta_node_interfaces"] is True
    assert report["execution_path"]["mnist_is_workload_only"] is True
    assert report["execution_path"]["phase_ordering_enforced"] is True
    assert report["execution_path"]["centralized_baseline_isolated_from_delta_inputs"] is True
    assert (
        report["execution_path"]["distributed_orchestrator_received_node_local_numeric_arrays"]
        is False
    )
    assert report["execution_path"]["four_distinct_worker_processes_observed"] is True
    assert (result.output_dir / report["execution_path"]["diagram"]).is_file()
    assert (result.output_dir / report["execution_path"]["trace"]).is_file()
    assert report["failure_simulation"]["failed_node_id"] == "validator-04"
    assert report["failure_simulation"]["replay_observed"] is True
    assert report["failure_simulation"]["protocol_accepted_after_recovery"] is True
    assert report["failure_simulation"]["terminal_outcome"] == "APPLIED"
    assert report["failure_simulation"]["evaluation"] == report["distributed"]["evaluation"]
    assert all(node["raw_images_shared"] is False for node in report["distributed"]["nodes"])
    assert {node["shared_payload"] for node in report["distributed"]["nodes"]} == {
        "SIGNED_CANONICAL_INT16_MODEL_DELTA_ONLY"
    }
    assert report["controller_quorum"]["keys_cryptographically_valid"] is True
    assert report["controller_quorum"]["valid_for_campaign02_governance"] is False
    assert _validate_workspace_report(report) is report
    forged = json.loads(json.dumps(report))
    forged["delta_execution"]["phase_ordering_enforced"] = False
    with pytest.raises(MnistDemoError, match="MNIST_WORKSPACE_DELTA_EVIDENCE_INVALID"):
        _validate_workspace_report(forged)

    hidden_quorum_assembly = json.loads(json.dumps(report))
    hidden_quorum_assembly["delta_execution"]["python_vote_quorum_assembly_performed"] = True
    with pytest.raises(MnistDemoError, match="MNIST_WORKSPACE_DELTA_EVIDENCE_INVALID"):
        _validate_workspace_report(hidden_quorum_assembly)

    conflated_ids = json.loads(json.dumps(report))
    first_phase = conflated_ids["delta_execution"]["phase_execution"][0]
    first_phase["vote_quorum_id"] = first_phase["typed_certificate_id"]
    with pytest.raises(MnistDemoError, match="MNIST_WORKSPACE_DELTA_PHASE_INVALID"):
        _validate_workspace_report(conflated_ids)

    wrong_parent = json.loads(json.dumps(report))
    wrong_parent["delta_execution"]["phase_execution"][1][
        "required_parent_typed_certificate_id"
    ] = wrong_parent["delta_execution"]["phase_execution"][0]["vote_quorum_id"]
    with pytest.raises(MnistDemoError, match="MNIST_WORKSPACE_DELTA_PHASE_INVALID"):
        _validate_workspace_report(wrong_parent)

    wrong_binding = json.loads(json.dumps(report))
    wrong_binding["model_dataset_binding"]["dataset_id"] = "fashion-mnist-v1"
    with pytest.raises(MnistDemoError, match="MNIST_WORKSPACE_DELTA_EVIDENCE_INVALID"):
        _validate_workspace_report(wrong_binding)

    wrong_eeg_claim = json.loads(json.dumps(report))
    wrong_eeg_claim["plugin_showcase"]["eeg_bandpower"]["delta_stage_c_execution_claimed"] = True
    with pytest.raises(MnistDemoError, match="MNIST_WORKSPACE_DELTA_EVIDENCE_INVALID"):
        _validate_workspace_report(wrong_eeg_claim)

    wrong_temporal_binding = json.loads(json.dumps(report))
    wrong_temporal_binding["plugin_showcase"]["eeg_bandpower"]["temporal_binding"]["examples"][0][
        "binding_assertion_id"
    ] = "sha256:" + "0" * 64
    with pytest.raises(MnistDemoError, match="MNIST_WORKSPACE_DELTA_EVIDENCE_INVALID"):
        _validate_workspace_report(wrong_temporal_binding)

    wrong_multi_domain = json.loads(json.dumps(report))
    wrong_multi_domain["multi_domain"]["delta_stage_c_domain_count"] = 2
    wrong_multi_domain["multi_domain"]["domains"][1]["delta_stage_c_execution_claimed"] = True
    with pytest.raises(MnistDemoError, match="MNIST_WORKSPACE_DELTA_EVIDENCE_INVALID"):
        _validate_workspace_report(wrong_multi_domain)

    wrong_qlora_receipt_claim = json.loads(json.dumps(report))
    qlora_domain = wrong_qlora_receipt_claim["multi_domain"]["domains"][1]
    qlora_domain["verified_execution_evidence"] = "LIVE_STAGE_C_APPLIED_RECEIPT"
    qlora_domain["reference_anchor_is_current_workspace_receipt"] = True
    qlora_domain["stage_c_execution_mode"] = "REAL_DRQ1"
    qlora_domain["stage_c_outcome"] = "APPLIED"
    with pytest.raises(MnistDemoError, match="MNIST_WORKSPACE_DELTA_EVIDENCE_INVALID"):
        _validate_workspace_report(wrong_qlora_receipt_claim)

    wrong_qlora_showcase_receipt = json.loads(json.dumps(report))
    wrong_qlora_showcase_receipt["plugin_showcase"]["qlora_adapter"][
        "verified_execution_evidence"
    ] = "LIVE_STAGE_C_APPLIED_RECEIPT"
    with pytest.raises(MnistDemoError, match="MNIST_WORKSPACE_DELTA_EVIDENCE_INVALID"):
        _validate_workspace_report(wrong_qlora_showcase_receipt)


def test_reproducibility_identity_excludes_observational_timings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dataset = _synthetic_dataset()
    _patch_dataset(monkeypatch, dataset)
    _patch_delta_nodes(monkeypatch, dataset)
    _patch_stage_c(monkeypatch)
    first = run_mnist_demo(
        _repository_root(),
        tmp_path / "cache",
        tmp_path / "run-a",
        allow_download=False,
    )
    second = run_mnist_demo(
        _repository_root(),
        tmp_path / "cache",
        tmp_path / "run-b",
        allow_download=False,
    )
    assert first.reproducibility_id == second.reproducibility_id


def test_workspace_is_one_button_and_does_not_expose_raw_json_by_default() -> None:
    assert "Запустить демо" in WORKSPACE_HTML
    assert "Покажи различия по цифрам" in WORKSPACE_HTML
    assert "Отказ и восстановление" in WORKSPACE_HTML
    assert "LOCAL DEMO ONLY" in WORKSPACE_HTML
    assert "Feature 010 GO" in WORKSPACE_HTML
    assert "ModelPlugin ↔ DatasetProvider" in WORKSPACE_HTML
    assert "model-plugin-id" in WORKSPACE_HTML
    assert "dataset-provider-id" in WORKSPACE_HTML
    assert "Мульти-доменная структура" in WORKSPACE_HTML
    assert "multi-domain-grid" in WORKSPACE_HTML
    assert "EEG плагин подключён" in WORKSPACE_HTML
    assert "Intervention EEG Explorer" in WORKSPACE_HTML
    assert "Event metadata" in WORKSPACE_HTML
    assert "EEG Timeline" in WORKSPACE_HTML
    assert "Response" in WORKSPACE_HTML
    assert "observed association" in WORKSPACE_HTML
    assert "InterventionEvent" in WORKSPACE_HTML
    assert "Binding Provenance" in WORKSPACE_HTML
    assert "BindingProvider" in WORKSPACE_HTML
    assert "BindingAuthority" in WORKSPACE_HTML
    assert "ResolvedBindingSet" in WORKSPACE_HTML
    assert "temporal-binding-rows" in WORKSPACE_HTML
    assert "BindingAssertion" in WORKSPACE_HTML
    assert "eeg-plugin-id" in WORKSPACE_HTML
    assert "registry/worker smoke" in WORKSPACE_HTML
    assert "Requested scope" in WORKSPACE_HTML
    assert "historical reference" in WORKSPACE_HTML
    assert "<pre" not in WORKSPACE_HTML
    assert "mnist-demo-report.json" not in WORKSPACE_HTML


def test_workspace_catalog_is_read_only_and_reports_scope_capabilities() -> None:
    catalog = _workspace_catalog()
    assert catalog["type_name"] == "DELTAREDUCE_WORKSPACE_PLUGIN_DATASET_CATALOG"
    assert catalog["register_exposed"] is False
    assert any(item["plugin_id"] == "qlora-tiny-adapter-v1" for item in catalog["model_plugins"])
    assert any(item["dataset_id"] == "tiny-qlora-regression-v1" for item in catalog["datasets"])
    pairs = {
        (item["model_plugin_id"], item["dataset_id"]): item for item in catalog["compatibility"]
    }
    qlora_pair = pairs[("qlora-tiny-adapter-v1", "tiny-qlora-regression-v1")]
    assert qlora_pair["contract_compatible"] is True
    assert qlora_pair["requested_scope_allowed"]["STAGE_C_REAL_DRQ1"] is True
    eeg_pair = pairs[("eeg-bandpower-centroid-v1", "eeg-synthetic-bci-v1")]
    assert eeg_pair["contract_compatible"] is True
    assert eeg_pair["requested_scope_allowed"]["STAGE_C_REAL_DRQ1"] is False


def test_workspace_refuses_non_loopback_binding(tmp_path: Path) -> None:
    with pytest.raises(MnistDemoError, match="MUST_BIND_LOOPBACK"):
        serve_workspace(
            _repository_root(),
            tmp_path / "cache",
            tmp_path / "runs",
            allow_download=False,
            host="0.0.0.0",
        )


def test_run_refuses_to_overwrite_prior_output(tmp_path: Path) -> None:
    destination = tmp_path / "run"
    destination.mkdir()
    with pytest.raises(MnistDemoError, match="OUTPUT_ALREADY_EXISTS"):
        run_mnist_demo(
            _repository_root(),
            tmp_path / "cache",
            destination,
            allow_download=False,
        )
