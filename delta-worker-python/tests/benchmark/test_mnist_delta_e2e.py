from __future__ import annotations

import json
import os
import shutil
from dataclasses import dataclass
from itertools import pairwise
from pathlib import Path

import numpy as np
import pytest
from deltatorrent.benchmark import mnist_delta_nodes, mnist_demo
from deltatorrent.benchmark.campaign02_demo_controllers import (
    generate_demo_controller_bundle,
)
from deltatorrent.benchmark.mnist_delta_nodes import (
    DIGIT_COUNT,
    NODE_COUNT,
    PIXELS_PER_DIGIT,
    REQUIRED_VOTE_KINDS,
    VECTOR_WIDTH,
    DeltaToolchain,
    MnistDeltaError,
    run_delta_nodes,
    write_node_contribution,
)
from deltatorrent.benchmark.mnist_demo import MnistDataset, run_mnist_demo
from deltatorrent.benchmark.mnist_demo_workspace import _validate_workspace_report


@dataclass(frozen=True, slots=True)
class _Summary:
    node_id: str
    counts: np.ndarray
    sums: np.ndarray
    summary_id: str


def _node_local_summaries() -> tuple[_Summary, ...]:
    ownership = ((0, 1, 2), (3, 4, 5), (6, 7), (8, 9))
    summaries: list[_Summary] = []
    for node_index, digits in enumerate(ownership, start=1):
        counts = np.zeros(DIGIT_COUNT, dtype=np.int64)
        sums = np.zeros((DIGIT_COUNT, PIXELS_PER_DIGIT), dtype=np.int64)
        for digit in digits:
            counts[digit] = 3
            sums[digit] = (digit + 1) * 3
        summaries.append(
            _Summary(
                node_id=f"demo-mnist-worker-{node_index:02d}",
                counts=counts,
                sums=sums,
                summary_id=f"sha256:{node_index:064x}",
            )
        )
    return tuple(summaries)


def _node_contributions(tmp_path: Path):
    return tuple(
        write_node_contribution(
            summary,
            f"sha256:{index + 100:064x}",
            (tmp_path / f"local-worker-{index:02d}.bin").resolve(),
        )
        for index, summary in enumerate(_node_local_summaries(), start=1)
    )


def _synthetic_mnist() -> MnistDataset:
    train_labels = np.repeat(np.arange(DIGIT_COUNT, dtype=np.uint8), 6)
    test_labels = np.repeat(np.arange(DIGIT_COUNT, dtype=np.uint8), 2)

    def image(digit: int, variation: int) -> np.ndarray:
        value = np.zeros((28, 28), dtype=np.uint8)
        row = digit * 2 + 2
        column = 25 - digit * 2
        value[row : row + 2, 3:25] = 180 + variation
        value[3:25, column : column + 2] = 220 + variation
        return value

    return MnistDataset(
        source_id="sha256:" + "b" * 64,
        train_images=np.stack(
            [image(int(digit), index % 2) for index, digit in enumerate(train_labels)]
        ),
        train_labels=train_labels,
        test_images=np.stack(
            [image(int(digit), index % 2) for index, digit in enumerate(test_labels)]
        ),
        test_labels=test_labels,
    )


def _retain_delta_evidence(source: Path, label: str) -> Path | None:
    evidence_value = os.environ.get("DELTA_MNIST_E2E_EVIDENCE_DIR")
    if not evidence_value:
        return None
    evidence_root = Path(evidence_value).resolve()
    evidence_root.mkdir(parents=True, exist_ok=True)
    target = evidence_root / label
    shutil.copytree(source, target)
    assert not list(target.rglob("*.pem"))
    return target


@pytest.mark.skipif(
    os.environ.get("DELTA_MNIST_E2E") != "1",
    reason="requires the compiled native node and JDK 25 Netty relay",
)
def test_real_delta_path_reaches_applied_without_demo_aggregation(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[3]
    controllers = tmp_path / "controllers"
    generate_demo_controller_bundle(controllers)
    contributions = _node_contributions(tmp_path)

    result = run_delta_nodes(
        repository_root,
        tmp_path / "delta-execution",
        controllers,
        contributions,
        "sha256:" + "a" * 64,
    )

    expected = np.zeros(VECTOR_WIDTH, dtype=np.int16)
    for digit in range(DIGIT_COUNT):
        start = digit * PIXELS_PER_DIGIT
        expected[start : start + PIXELS_PER_DIGIT] = digit + 1
    expected[DIGIT_COUNT * PIXELS_PER_DIGIT :] = 1
    assert np.array_equal(result.applied_model.values, expected)

    trace = json.loads(result.execution_trace_path.read_text(encoding="utf-8"))
    assert trace["terminal_outcome"] == "APPLIED"
    assert trace["classification"] == "LOCAL_DEMO_ONLY"
    assert trace["authoritative"] is False
    assert trace["governance_eligible"] is False
    assert trace["execution_authorized"] is False
    assert trace["formal_refinement_claimed"] is False
    assert trace["semantic_completeness_claimed"] is False
    assert trace["trace_scope"] == "POST_CONFIG_POST_AVAILABILITY_DEMO_SUBTRACE"
    assert trace["python_cross_node_aggregation_performed"] is False
    assert trace["python_vote_quorum_assembly_performed"] is False
    assert trace["demo_owned_aggregation"] is False
    assert trace["aggregation_authority"] == "delta::robust::reduce_parameter_shard"
    assert trace["vote_quorum_component"] == "delta::core::consensus::validate_quorum"
    assert trace["typed_certificate_verifier"] == "delta::certificates::ChainVerifier"
    assert trace["phase_ordering_enforced"] is True
    phase_execution = trace["phase_execution"]
    assert [item["phase"] for item in phase_execution] == list(REQUIRED_VOTE_KINDS)
    assert [item["position"] for item in phase_execution] == list(
        range(1, len(REQUIRED_VOTE_KINDS) + 1)
    )
    assert phase_execution[0]["required_parent_typed_certificate_id"] is None
    assert phase_execution[0]["required_parent_vote_quorum_id"] is None
    assert all(
        current["required_parent_typed_certificate_id"] == previous["typed_certificate_id"]
        and current["required_parent_vote_quorum_id"] == previous["vote_quorum_id"]
        for previous, current in pairwise(phase_execution)
    )
    assert all(
        item["validated_parent_typed_certificate_ids"]
        == [parent["typed_certificate_id"] for parent in phase_execution[:index]]
        and item["validated_parent_vote_quorum_ids"]
        == [parent["vote_quorum_id"] for parent in phase_execution[:index]]
        for index, item in enumerate(phase_execution)
    )
    assert {item["typed_certificate_id"] for item in phase_execution}.isdisjoint(
        {item["vote_quorum_id"] for item in phase_execution}
    )
    assert all(item["certifying_nodes"] == NODE_COUNT for item in phase_execution)
    assert all(item["delivered_vote_count_per_receiver"] == NODE_COUNT for item in phase_execution)
    assert all(item["vote_frames_relayed_per_receiver"] == NODE_COUNT for item in phase_execution)
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
    assert len(trace["transport_receipts"]) == NODE_COUNT * (1 + len(REQUIRED_VOTE_KINDS))
    assert len(trace["native_results"]) == (NODE_COUNT * len(REQUIRED_VOTE_KINDS) * 2 + NODE_COUNT)
    assert sum(
        result["type_name"] == "MNIST_DELTA_VOTE_PHASE_RESULT" for result in trace["native_results"]
    ) == NODE_COUNT * len(REQUIRED_VOTE_KINDS)
    assert sum(
        result["type_name"] == "MNIST_DELTA_CERTIFY_PHASE_RESULT"
        for result in trace["native_results"]
    ) == NODE_COUNT * len(REQUIRED_VOTE_KINDS)
    assert [component["component"] for component in trace["components"]] == [
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
    contribution_ids = [item.content_id for item in result.node_contributions]
    assert trace["contribution_ids"] == contribution_ids
    assert all(
        native_result["contribution_ids"] == contribution_ids
        for native_result in trace["native_results"]
    )
    assert trace["toolchain"]["source_snapshot"]["no_hidden_aggregation_static_gate"] == "PASS"
    certificates = result.delta_execution["quorum_certificates"]
    assert [certificate["kind"] for certificate in certificates] == [
        "input_set",
        "eligibility",
        "aggregation_plan",
        "parameter_shard",
        "aggregate_root",
        "apply",
    ]
    assert all(certificate["signer_count"] == NODE_COUNT for certificate in certificates)
    assert all(certificate["threshold"] == 3 for certificate in certificates)
    assert [certificate["body_hash"] for certificate in certificates] == [
        item["typed_certificate_id"] for item in phase_execution
    ]
    assert [certificate["qc_id"] for certificate in certificates] == [
        item["vote_quorum_id"] for item in phase_execution
    ]
    assert trace["apply_qc_id"] == phase_execution[-1]["typed_certificate_id"]
    assert trace["current_pointer"]["apply_qc_id"] == phase_execution[-1]["typed_certificate_id"]
    assert result.failure_simulation["status"] == "RECOVERED_AND_APPLIED"
    assert result.failure_simulation["replay_observed"] is True
    assert result.failure_simulation["terminal_outcome"] == "APPLIED"
    diagram = result.execution_diagram_path.read_text(encoding="utf-8")
    assert "generic parent quorum plus typed parent certificate" in diagram
    assert "required before numeric reduction" in diagram
    assert "CertificateVoteRuntime: persist Apply vote" in diagram
    assert "consensus::validate_quorum: generic Apply quorum" in diagram
    assert "ChainVerifier: typed ApplyQC" in diagram
    assert "robust::build_plan" in diagram
    assert "robust::reduce_parameter_shard" in diagram

    result_root = tmp_path / "delta-execution"
    vote_paths = [
        result_root / f"results/validator-01-{phase}-vote.json" for phase in REQUIRED_VOTE_KINDS
    ]
    certify_paths = [
        result_root / f"results/validator-01-{phase}-certify.json" for phase in REQUIRED_VOTE_KINDS
    ]
    finalize_path = result_root / "results/validator-01-finalize.json"
    vote_results = [json.loads(path.read_text(encoding="utf-8")) for path in vote_paths]
    certify_results = [json.loads(path.read_text(encoding="utf-8")) for path in certify_paths]
    finalize_result = json.loads(finalize_path.read_text(encoding="utf-8"))
    forged_vote = dict(vote_results[0])
    forged_vote["result_id"] = "sha256:" + "0" * 64
    with pytest.raises(MnistDeltaError, match="NATIVE_RESULT_ID_INVALID"):
        mnist_delta_nodes._validate_vote_phase_result(
            forged_vote,
            "validator-01",
            trace["workload_id"],
            "sha256:" + "a" * 64,
            contribution_ids,
            result_root / "native-nodes/validator-01",
            vote_paths[0],
            0,
            (),
            crash=False,
        )

    native_trace_path = result_root / "native-nodes/validator-01/trace.jsonl"
    conflated_certify_results = json.loads(json.dumps(certify_results))
    conflated_certificate = conflated_certify_results[0]["quorum_certificate"]
    conflated_certificate["qc_id"] = conflated_certificate["body_hash"]
    with pytest.raises(MnistDeltaError, match="TYPED_CERTIFICATE_QUORUM_ID_CONFLATED"):
        mnist_delta_nodes._collect_native_trace(
            native_trace_path,
            "validator-01",
            vote_results,
            conflated_certify_results,
            finalize_result,
            expect_crash=False,
        )

    for rows in trace["native_trace"].values():
        current_vote_quorums = [
            (index, row)
            for index, row in enumerate(rows)
            if row["action_id"] == "OBS-CURRENT-VOTE-QUORUM-VALIDATED"
        ]
        assert len(current_vote_quorums) == len(REQUIRED_VOTE_KINDS)
        for quorum_index, quorum_row in current_vote_quorums:
            typed_index = next(
                index
                for index, row in enumerate(rows[quorum_index + 1 :], start=quorum_index + 1)
                if row["action_id"] == "OBS-TYPED-CERT-VERIFIED-AFTER-QC"
                and row["body_hash"] == quorum_row["body_hash"]
            )
            durable_qc_index = next(
                index
                for index, row in enumerate(rows[typed_index + 1 :], start=typed_index + 1)
                if row["action_id"] == "OBS-CURRENT-QC-DURABLY-FINALIZED"
                and row["body_hash"] == quorum_row["body_hash"]
            )
            assert quorum_index < typed_index < durable_qc_index

    reordered_rows = [
        json.loads(line) for line in native_trace_path.read_text(encoding="utf-8").splitlines()
    ]
    quorum_positions = [
        index for index, row in enumerate(reordered_rows) if row["event"] == "quorum_validated"
    ]
    first, second = quorum_positions[:2]
    reordered_rows[first], reordered_rows[second] = reordered_rows[second], reordered_rows[first]
    reordered_path = tmp_path / "reordered-native-trace.jsonl"
    reordered_path.write_text(
        "".join(
            json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n" for row in reordered_rows
        ),
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(MnistDeltaError, match="NATIVE_TRACE_INVALID"):
        mnist_delta_nodes._collect_native_trace(
            reordered_path,
            "validator-01",
            vote_results,
            certify_results,
            finalize_result,
            expect_crash=False,
        )

    _retain_delta_evidence(result_root, "direct-delta-path")


@pytest.mark.skipif(
    os.environ.get("DELTA_MNIST_E2E") != "1",
    reason="requires the compiled native node and JDK 25 Netty relay",
)
def test_full_demo_orchestration_uses_four_workers_and_real_delta(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset = _synthetic_mnist()
    monkeypatch.setattr(
        mnist_demo,
        "prepare_mnist_cache",
        lambda _cache, *, allow_download: {
            "download_was_allowed": allow_download,
            "source_id": dataset.source_id,
        },
    )
    monkeypatch.setattr(mnist_demo, "load_mnist", lambda _cache, _source_id: dataset)

    result = run_mnist_demo(
        Path(__file__).resolve().parents[3],
        tmp_path / "cache",
        tmp_path / "full-demo",
        allow_download=False,
    )
    report = json.loads(result.report_json.read_text(encoding="utf-8"))
    assert report["demo_status"] == "DEMO_PASS"
    assert report["dataset"]["train_samples"] == 60
    assert report["dataset"]["test_samples"] == 20
    assert report["distributed"]["parallel_processes_observed"] == NODE_COUNT
    assert report["distributed"]["worker_processes_required"] == NODE_COUNT
    assert report["execution_path"]["four_distinct_worker_processes_observed"] is True
    assert (
        report["execution_path"]["distributed_orchestrator_received_node_local_numeric_arrays"]
        is False
    )
    assert report["delta_execution"]["terminal_outcome"] == "APPLIED"
    assert report["delta_execution"]["python_cross_node_aggregation_performed"] is False
    assert report["distributed"]["exact_model_match_with_centralized"] is True
    assert _validate_workspace_report(report) is report

    retained = _retain_delta_evidence(result.output_dir / "delta-execution", "full-demo-path")
    if retained is not None:
        shutil.copyfile(result.report_json, retained / "mnist-demo-report.json")
        (retained / "evidence-scope.json").write_text(
            json.dumps(
                {
                    "authoritative": False,
                    "classification": "LOCAL_DEMO_ONLY",
                    "dataset_scope": "SYNTHETIC_MNIST_SHAPE_TEST_60_TRAIN_20_TEST",
                    "full_orchestration_path_exercised": True,
                    "governance_eligible": False,
                    "private_controller_keys_retained": False,
                    "raw_delta_execution_tree_retained": True,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )


@pytest.mark.skipif(
    os.environ.get("DELTA_MNIST_E2E") != "1",
    reason="requires the compiled native node and JDK 25 Netty relay",
)
def test_deleted_relayed_contribution_stops_before_delta_votes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    controllers = tmp_path / "controllers"
    generate_demo_controller_bundle(controllers)
    contributions = _node_contributions(tmp_path)
    original_run_process = mnist_delta_nodes._run_process
    mutated = False

    def delete_before_native(command: tuple[str, ...], *, expected_codes: frozenset[int]) -> object:
        nonlocal mutated
        if not mutated and len(command) > 1 and command[1] == "vote-phase":
            contribution_root = Path(command[command.index("--contributions-root") + 1])
            (contribution_root / "worker-01.bin").unlink()
            mutated = True
        return original_run_process(command, expected_codes=expected_codes)

    monkeypatch.setattr(mnist_delta_nodes, "_run_process", delete_before_native)
    with pytest.raises(MnistDeltaError, match="MNIST_DELTA_PROCESS_FAILED"):
        run_delta_nodes(
            Path(__file__).resolve().parents[3],
            tmp_path / "delta-execution",
            controllers,
            contributions,
            "sha256:" + "a" * 64,
        )
    assert mutated is True
    assert not (tmp_path / "delta-execution/native-nodes/validator-01/votes/runtime.wal").exists()


@pytest.mark.skipif(
    os.environ.get("DELTA_MNIST_E2E") != "1",
    reason="requires the compiled native node and JDK 25 Netty relay",
)
def test_missing_parent_qc_stops_next_phase_before_vote(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    controllers = tmp_path / "controllers"
    generate_demo_controller_bundle(controllers)
    contributions = _node_contributions(tmp_path)
    original_run_process = mnist_delta_nodes._run_process
    removed = False

    def remove_parent_qc(command: tuple[str, ...], *, expected_codes: frozenset[int]) -> object:
        nonlocal removed
        if (
            not removed
            and len(command) > 1
            and command[1] == "vote-phase"
            and command[command.index("--phase") + 1] == "eligibility"
        ):
            qcs_root = Path(command[command.index("--qcs-root") + 1])
            (qcs_root / "input_set.qc").unlink()
            removed = True
        return original_run_process(command, expected_codes=expected_codes)

    monkeypatch.setattr(mnist_delta_nodes, "_run_process", remove_parent_qc)
    with pytest.raises(MnistDeltaError, match="MNIST_DELTA_PROCESS_FAILED"):
        run_delta_nodes(
            Path(__file__).resolve().parents[3],
            tmp_path / "delta-execution",
            controllers,
            contributions,
            "sha256:" + "a" * 64,
        )
    assert removed is True
    assert not (
        tmp_path / "delta-execution/native-nodes/validator-01/vote-frames/eligibility.vote"
    ).exists()


@pytest.mark.skipif(
    os.environ.get("DELTA_MNIST_E2E") != "1",
    reason="requires the compiled native node and JDK 25 Netty relay",
)
def test_duplicate_production_class_is_rejected_as_classpath_shadow(tmp_path: Path) -> None:
    repository_root = Path(__file__).resolve().parents[3]
    toolchain = DeltaToolchain.from_environment(repository_root)
    class_directories = [
        Path(entry) for entry in toolchain.relay_classpath.split(os.pathsep) if Path(entry).is_dir()
    ]
    source = class_directories[0] / ("io/deltareduce/node/benchmark/BenchmarkTransport.class")
    duplicate = tmp_path / "duplicate-classes" / source.relative_to(class_directories[0])
    duplicate.parent.mkdir(parents=True)
    shutil.copyfile(source, duplicate)
    shadowed = DeltaToolchain(
        toolchain.native_executable,
        toolchain.java_executable,
        toolchain.relay_classpath + os.pathsep + str(tmp_path / "duplicate-classes"),
    )
    with pytest.raises(MnistDeltaError, match="CLASSPATH_SHADOWED"):
        shadowed.validate(repository_root)
