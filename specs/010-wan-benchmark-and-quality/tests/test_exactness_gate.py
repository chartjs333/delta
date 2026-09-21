from __future__ import annotations

import copy
import hashlib
import json
import statistics
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "specs/010-wan-benchmark-and-quality/scripts"
sys.path.insert(0, str(SCRIPTS))
import capture_exactness_ci as capture  # noqa: E402
import exactness_gate as gate  # noqa: E402
import verify_exactness_status as status  # noqa: E402


def content_id(fill: str) -> str:
    return "sha256:" + fill * 64


def process_result() -> dict[str, object]:
    result: dict[str, object] = {
        "aggregate_root_qc_id": content_id("1"),
        "aggregator_effect_root": content_id("3"),
        "aggregator_state_root": content_id("1"),
        "apply_candidate_id": content_id("2"),
        "apply_effect_root": content_id("d"),
        "apply_qc_id": content_id("3"),
        "apply_state_root": content_id("e"),
        "benchmark_definition_id": gate.DEFINITION_ID,
        "current_wal_sha256": content_id("5"),
        "declared_B": 64,
        "declared_H": 16,
        "execution_class": "CONFORMANCE_SAFETY_FAULT_ONLY",
        "feature010_go": False,
        "flat_result_id": content_id("6"),
        "formal_semantics_id": gate.FORMAL_ID,
        "hierarchical_assembly_id": content_id("7"),
        "hierarchical_result_id": content_id("6"),
        "input_set_certificate_id": content_id("8"),
        "parameter_shard_qc_id": content_id("9"),
        "primary_observation_count": 0,
        "primary_parameter_shape_bound": False,
        "processed_q_value_count": 64,
        "protocol_result_id": content_id("a"),
        "qualifying_gate_c": False,
        "qualifying_gate_d": False,
        "reduction_vector_width": 4,
        "robust_plan_id": content_id("b"),
        "schema_version": "1.0.0",
        "status": "PASS",
        "synthetic_contribution_count": 16,
        "type_name": "FEATURE010_EXACTNESS_PROCESS_RESULT",
        "validator_effect_root": content_id("2"),
        "validator_process_count": 4,
        "validator_receipts_sha256": content_id("f"),
        "validator_state_root": content_id("1"),
        "work_ticket_budget_exercised": False,
    }
    assert set(result) == gate.PROCESS_FIELDS
    return result


def execution_document() -> dict[str, object]:
    source = gate.source_identity("HEAD")
    process = process_result()
    process_hash = gate.sha256_id(gate.canonical_bytes(process))
    corpus_hash = content_id("c")
    _risk, risk_raw = gate.canonical_document(gate.PROFILE_DECISION_PATH)
    lanes = []
    durations = []
    for index, (compiler, standard) in enumerate(sorted(gate.EXPECTED_LANES), start=1):
        duration = index * 10
        durations.append(duration)
        lanes.append(
            {
                "architecture": "x86_64",
                "compiler": compiler,
                "compiler_image": gate.EXPECTED_TOOLCHAINS[compiler]["image"],
                "compiler_version": gate.EXPECTED_TOOLCHAINS[compiler]["version_pattern"],
                "cpp_standard": standard,
                "diagnostic_elapsed_ns": duration,
                "formal_semantics_id": gate.FORMAL_ID,
                "process_output": copy.deepcopy(process),
                "process_output_sha256": process_hash,
                "process_receipts": [
                    {
                        "aggregator_sha256": content_id("1"),
                        "validator_receipts": [
                            {"path": f"validator-{validator}.json", "sha256": content_id("2")}
                            for validator in range(4)
                        ],
                    }
                    for _repetition in range(4)
                ],
                "process_repetitions": 4,
                "schema_version": "1.0.0",
                "shared_corpus_sha256": corpus_hash,
                "source": source,
                "status": "PASS",
                "type_name": "FEATURE010_NATIVE_EXACTNESS_LANE",
            }
        )
    profile = {
        "available_profile": "EMBEDDED_FFM",
        "comparison": {
            "embedded_ffm": {
                "crash_containment": "PROCESS_COFAILURE_RISK_ACCEPTED_NO_ISOLATION_CLAIM",
                "diagnostic_four_process_elapsed_ns": durations,
                "median_four_process_elapsed_ns": int(statistics.median(durations)),
                "restart_replay": "PASS",
                "status": "QUALIFIED_EXACTNESS_ONLY",
            },
            "isolated_sidecar": {
                "crash_containment": "NOT_EVALUATED",
                "latency_ns": None,
                "reason": "CURRENT_LINEAGE_SIDECAR_NOT_IMPLEMENTED",
                "restart_replay": "NOT_EVALUATED",
                "status": "OMITTED_BY_FORMAL_RISK_DECISION",
                "throughput": None,
            },
            "measurement_class": "NON_PRIMARY_CI_DIAGNOSTIC",
            "performance_superiority_claimed": False,
        },
        "pilot_execution_authorized": False,
        "risk_acceptance": {
            "accepted_risk": "NATIVE_CRASH_MAY_TERMINATE_JAVA_PROCESS",
            "crash_isolation_claimed": False,
            "formal_impact": "NO_SEMANTIC_CHANGE",
            "sidecar_omitted": True,
        },
        "risk_decision_sha256": gate.sha256_id(risk_raw),
        "selected_profile": None,
        "selection_basis": "NO_SELECTION_SIDECAR_NOT_EVALUATED",
        "selection_scope": "BLOCKED_PENDING_IMMUTABLE_COMPARATIVE_BENCHMARK_EVIDENCE",
    }
    return {
        "architecture_coverage": {
            "aarch64": {
                "reason": "NO_EXACT_PINNED_RUNNER_AVAILABLE",
                "status": "NOT_RUN",
            },
            "x86_64": "PASS",
        },
        "attack_coverage": copy.deepcopy(gate.ATTACK_COVERAGE),
        "authority": {
            "definition_execution_authorized": False,
            "feature010_go": False,
            "primary_observation_count": 0,
            "qualifying_gate_c": False,
            "qualifying_gate_d": False,
            "result_qc": None,
        },
        "cross_language_corpus_sha256": corpus_hash,
        "formal_semantics_id": gate.FORMAL_ID,
        "gates": copy.deepcopy(gate.EXPECTED_GATES),
        "native_lanes": lanes,
        "process_result": process,
        "profile_decision": profile,
        "qualification_blockers": copy.deepcopy(gate.QUALIFICATION_BLOCKERS),
        "refinement": [
            {"path": path, "sha256": content_id(str(index)), "status": "PASS"}
            for index, path in enumerate(sorted(gate.REFINEMENT_FILES), start=1)
        ],
        "safety_tests": sorted(gate.EXPECTED_TESTS),
        "safety_junit_sha256": content_id("0"),
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": source,
        "status": "FAIL",
        "type_name": "FEATURE010_EXACTNESS_EXECUTION",
    }


def write_document(path: Path, value: object) -> bytes:
    raw = gate.canonical_bytes(value) + b"\n"
    path.write_bytes(raw)
    return raw


def write_receipt_directory(path: Path, process: dict[str, object]) -> None:
    path.mkdir()
    transcript = b""
    for index in range(4):
        validator_id = f"validator-{index}"
        raw = write_document(
            path / f"{validator_id}.json",
            {
                "effect_root": process["validator_effect_root"],
                "state_root": process["validator_state_root"],
                "validator_id": validator_id,
            },
        )
        transcript += validator_id.encode() + b"\0" + raw
    process["validator_receipts_sha256"] = gate.sha256_id(transcript)
    write_document(
        path / "aggregator.json",
        {
            "aggregator_effect_root": process["aggregator_effect_root"],
            "aggregator_state_root": process["aggregator_state_root"],
            "validator_effect_root": process["validator_effect_root"],
            "validator_process_count": 4,
            "validator_receipts_sha256": process["validator_receipts_sha256"],
            "validator_state_root": process["validator_state_root"],
        },
    )


def ci_document(execution_raw: bytes) -> dict[str, object]:
    source = gate.source_identity("HEAD")
    runs: dict[str, object] = {}
    next_id = 100
    for workflow, jobs in sorted(capture.WORKFLOWS.items()):
        run_id = next_id
        next_id += 1
        normalized_jobs = []
        for name in sorted(jobs):
            normalized_jobs.append(
                {
                    "conclusion": "success",
                    "database_id": next_id,
                    "name": name,
                    "url": f"https://example.invalid/jobs/{next_id}",
                }
            )
            next_id += 1
        runs[workflow] = {
            "conclusion": "success",
            "database_id": run_id,
            "event": "pull_request",
            "head_sha": source["commit"],
            "jobs": normalized_jobs,
            "url": f"https://example.invalid/runs/{run_id}",
            "workflow_name": workflow,
        }
    exact_run = runs["Feature 010 exactness and safety verification"]
    run_id = exact_run["database_id"]
    artifact_names = sorted(
        {
            f"feature010-exactness-execution-{run_id}-{source['commit']}",
            f"feature010-java-jdk25-{source['commit']}",
            f"feature010-java-jdk26-{source['commit']}",
            f"feature010-native-clang-cpp20-{source['commit']}",
            f"feature010-native-clang-cpp23-{source['commit']}",
            f"feature010-native-gcc-cpp20-{source['commit']}",
            f"feature010-native-gcc-cpp23-{source['commit']}",
            f"feature010-safety-{source['commit']}",
        }
    )
    return {
        "artifacts": [
            {
                "archive_digest": content_id("d"),
                "artifact_id": 700 + index,
                "artifact_name": name,
                "created_at": "2026-09-21T00:00:00Z",
                "size_in_bytes": len(execution_raw),
            }
            for index, name in enumerate(artifact_names)
        ],
        "authority": {
            "feature010_go": False,
            "primary_observation_count": 0,
            "qualifying_gate_c": False,
            "qualifying_gate_d": False,
            "result_qc": None,
        },
        "execution_sha256": "sha256:" + hashlib.sha256(execution_raw).hexdigest(),
        "formal_semantics_id": gate.FORMAL_ID,
        "required_job_count": sum(len(value["jobs"]) for value in runs.values()),
        "runs": runs,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": source,
        "status": "PASS",
        "type_name": "FEATURE010_EXACT_HEAD_CI",
        "workflows": capture.workflow_hashes(source["commit"]),
    }


def test_process_rejects_flat_hierarchy_drift() -> None:
    document = process_result()
    document["hierarchical_result_id"] = content_id("f")

    with pytest.raises(gate.ExactnessError, match="HIERARCHY_DRIFT"):
        gate.validate_process(document)


def test_process_rejects_fixture_shape_drift() -> None:
    document = process_result()
    document["processed_q_value_count"] = 63

    with pytest.raises(gate.ExactnessError, match="PROCESS_FIXTURE_SHAPE"):
        gate.validate_process(document)


def test_process_rejects_unbound_primary_scale_claim() -> None:
    document = process_result()
    document["work_ticket_budget_exercised"] = True

    with pytest.raises(gate.ExactnessError, match="PROCESS_PRIMARY_SCALE_CLAIM_FORBIDDEN"):
        gate.validate_process(document)


def test_validator_aggregator_receipts_are_bound(tmp_path: Path) -> None:
    process = process_result()
    receipt_dir = tmp_path / "receipts"
    write_receipt_directory(receipt_dir, process)

    result = gate.validate_receipt_directory(receipt_dir, process)

    assert len(result["validator_receipts"]) == 4
    assert result["aggregator_sha256"].startswith("sha256:")


def test_validator_receipt_root_mutation_is_rejected(tmp_path: Path) -> None:
    process = process_result()
    receipt_dir = tmp_path / "receipts"
    write_receipt_directory(receipt_dir, process)
    write_document(
        receipt_dir / "validator-2.json",
        {
            "effect_root": process["validator_effect_root"],
            "state_root": content_id("9"),
            "validator_id": "validator-2",
        },
    )

    with pytest.raises(gate.ExactnessError, match="VALIDATOR_STATE"):
        gate.validate_receipt_directory(receipt_dir, process)


def test_corpus_rejects_promoted_primary_observation() -> None:
    document = json.loads(
        (ROOT / "delta-protocol/fixtures/010/cross-language/foundation-v1.json").read_text(
            encoding="utf-8"
        )
    )
    corpus = {
        "artifact_ids": [wrapper["content_id"] for wrapper in document["artifacts"].values()],
        "execution_class": "CONFORMANCE_SAFETY_ONLY",
        "formal_semantics_id": gate.FORMAL_ID,
        "negative_statuses": [
            {"case_id": "definition-leading-space", "status": "JSON_BYTES_NOT_CANONICAL"},
            {"case_id": "run-primary-promotion", "status": "PRIMARY_ELIGIBILITY_FORBIDDEN"},
        ],
        "primary_observation_count": 1,
        "schema_version": "1.0.0",
        "status": "PASS",
        "type_name": "FEATURE010_EXACTNESS_CORPUS",
    }

    with pytest.raises(gate.ExactnessError, match="CORPUS_PRIMARY_FORBIDDEN"):
        gate.validate_corpus(corpus)


def test_corpus_rejects_substituted_content_identity() -> None:
    document = {
        "artifact_ids": copy.deepcopy(gate.EXPECTED_CORPUS_IDS),
        "execution_class": "CONFORMANCE_SAFETY_ONLY",
        "formal_semantics_id": gate.FORMAL_ID,
        "negative_statuses": [
            {"case_id": "definition-leading-space", "status": "JSON_BYTES_NOT_CANONICAL"},
            {"case_id": "run-primary-promotion", "status": "PRIMARY_ELIGIBILITY_FORBIDDEN"},
        ],
        "primary_observation_count": 0,
        "schema_version": "1.0.0",
        "status": "PASS",
        "type_name": "FEATURE010_EXACTNESS_CORPUS",
    }
    document["artifact_ids"][0] = content_id("f")

    with pytest.raises(gate.ExactnessError, match="CORPUS_IDS"):
        gate.validate_corpus(document)


def test_execution_document_passes(tmp_path: Path) -> None:
    path = tmp_path / "execution.json"
    write_document(path, execution_document())

    assert gate.verify_execution(path)["status"] == "FAIL"


def test_execution_rejects_authority_promotion(tmp_path: Path) -> None:
    document = execution_document()
    document["authority"]["feature010_go"] = True
    path = tmp_path / "execution.json"
    write_document(path, document)

    with pytest.raises(gate.ExactnessError, match="AUTHORITY"):
        gate.verify_execution(path)


def test_execution_rejects_cross_compiler_hash_drift(tmp_path: Path) -> None:
    document = execution_document()
    document["native_lanes"][0]["process_output_sha256"] = content_id("f")
    path = tmp_path / "execution.json"
    write_document(path, document)

    with pytest.raises(gate.ExactnessError, match="LANE_PROCESS_HASH"):
        gate.verify_execution(path)


def test_execution_rejects_attack_coverage_mutation(tmp_path: Path) -> None:
    document = execution_document()
    document["attack_coverage"][0]["expected_terminal"] = "ACCEPT"
    path = tmp_path / "execution.json"
    write_document(path, document)

    with pytest.raises(gate.ExactnessError, match="ATTACK_COVERAGE"):
        gate.verify_execution(path)


def test_execution_rejects_crash_isolation_claim(tmp_path: Path) -> None:
    document = execution_document()
    document["profile_decision"]["risk_acceptance"]["crash_isolation_claimed"] = True
    path = tmp_path / "execution.json"
    write_document(path, document)

    with pytest.raises(gate.ExactnessError, match="PROFILE_RISK_DECISION"):
        gate.verify_execution(path)


def test_execution_rejects_unbenchmarked_profile_selection(tmp_path: Path) -> None:
    document = execution_document()
    document["profile_decision"]["selected_profile"] = "EMBEDDED_FFM"
    path = tmp_path / "execution.json"
    write_document(path, document)

    with pytest.raises(gate.ExactnessError, match="PROFILE_SELECTION_FORBIDDEN"):
        gate.verify_execution(path)


def test_execution_rejects_removed_qualification_blocker(tmp_path: Path) -> None:
    document = execution_document()
    document["qualification_blockers"] = []
    path = tmp_path / "execution.json"
    write_document(path, document)

    with pytest.raises(gate.ExactnessError, match="EXECUTION_QUALIFICATION_BLOCKERS"):
        gate.verify_execution(path)


def test_qualification_blockers_do_not_claim_a_formal_change() -> None:
    blockers = {item["blocker_id"]: item for item in gate.QUALIFICATION_BLOCKERS}

    assert all(item["requires_formal_change"] is False for item in blockers.values())
    assert blockers["PRIMARY_WORKLOAD_SCALE_UNBOUND"]["requires_formal_review"] is False
    sidecar = blockers["ISOLATED_SIDECAR_NOT_IMPLEMENTED"]
    assert sidecar["requires_formal_review"] is False
    assert sidecar["future_formal_review_required"] is True
    assert sidecar["formal_review_trigger"] == "BEFORE_ISOLATED_SIDECAR_IMPLEMENTATION"
    assert (
        sidecar["formal_escalation"]
        == "ONLY_IF_NEW_EXTERNALLY_VISIBLE_STATE_OR_OUTCOME_IS_REQUIRED"
    )


def test_status_overlay_generation_fails_closed_on_blocked_gates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    document = execution_document()
    monkeypatch.setattr(status, "validate_source", lambda _source: None)

    with pytest.raises(gate.ExactnessError, match="MANDATORY_EXACTNESS_GATES_BLOCKED"):
        status.expected_status(
            document,
            b"execution\n",
            {"source": document["source"]},
            b"ci\n",
        )


def test_ci_rejects_missing_required_job(monkeypatch: pytest.MonkeyPatch) -> None:
    workflow_hashes = [{"path": "fixture", "sha256": content_id("1"), "workflow": "fixture"}]
    monkeypatch.setattr(capture, "workflow_hashes", lambda _commit: workflow_hashes)
    execution_raw = b"{}\n"
    document = ci_document(execution_raw)
    workflow = "Native sanitizer matrix"
    document["runs"][workflow]["jobs"].pop()

    with pytest.raises(gate.ExactnessError, match="CI_JOB_SET"):
        capture.verify_ci(document, execution_raw)


def test_ci_rejects_cross_commit_run(monkeypatch: pytest.MonkeyPatch) -> None:
    workflow_hashes = [{"path": "fixture", "sha256": content_id("1"), "workflow": "fixture"}]
    monkeypatch.setattr(capture, "workflow_hashes", lambda _commit: workflow_hashes)
    execution_raw = b"{}\n"
    document = ci_document(execution_raw)
    workflow = "Python worker quality"
    document["runs"][workflow]["head_sha"] = "0" * 40

    with pytest.raises(gate.ExactnessError, match="CI_HEAD_DIVERGENCE"):
        capture.verify_ci(document, execution_raw)


def test_ci_document_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    workflow_hashes = [{"path": "fixture", "sha256": content_id("1"), "workflow": "fixture"}]
    monkeypatch.setattr(capture, "workflow_hashes", lambda _commit: workflow_hashes)
    execution_raw = b"{}\n"
    document = ci_document(execution_raw)

    assert capture.verify_ci(document, execution_raw)["status"] == "PASS"


def test_final_gate_promotion_is_limited_to_exact_head_ci() -> None:
    promoted = status.final_gates()
    by_id = {item["gate_id"]: item["status"] for item in promoted}

    assert by_id["XH-SANITIZERS"] == "PASS_EXACT_HEAD_CI"
    assert by_id["XH-NETTY"] == "PASS_EXACT_HEAD_CI"
    assert by_id["XH-ABI"] == "PASS_EXACT_HEAD_CI"
    assert by_id["XH-SIDECAR"] == "PASS_PREREGISTERED_OMISSION_RISK_DECISION"
    assert by_id["XH-PRIMARY-SCALE"].startswith("BLOCKED_")
    assert by_id["XH-PROFILES"].startswith("BLOCKED_")
    assert by_id["XH-PILOT"].startswith("BLOCKED_")
    assert all(item["status"] != "REQUIRES_EXACT_HEAD_CI" for item in promoted)
