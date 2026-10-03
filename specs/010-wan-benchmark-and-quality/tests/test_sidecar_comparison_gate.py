from __future__ import annotations

import copy
import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "specs/010-wan-benchmark-and-quality/scripts"
sys.path.insert(0, str(SCRIPTS))
import sidecar_comparison_gate as gate  # noqa: E402


def content_id(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def marker(
    item_id: str,
    id_field: str,
    *,
    status: str = "PASS",
    paired: bool = False,
) -> dict[str, object]:
    result: dict[str, object] = {
        id_field: item_id,
        "evidence_sha256": content_id("evidence:" + item_id),
        "status": status,
    }
    if paired:
        digest = content_id("pair:" + item_id)
        result["embedded_sha256"] = digest
        result["sidecar_sha256"] = digest
    return result


def profile_document(profile_id: str, design: dict[str, object]) -> dict[str, object]:
    comparison = design["comparison_plan"]
    aggregation = comparison["aggregation"]
    saturation_completed = 1_000 if profile_id == "EMBEDDED_FFM" else 950
    copy_ids = comparison["copy_accounting"]
    copy_values = {item: 0 for item in copy_ids}
    copy_values["STAGING_FALLBACK_INGRESS_BYTES"] = 100
    copy_values["STAGING_FALLBACK_EGRESS_BYTES"] = 100
    copy_values["ZERO_COPY_ELIGIBLE_COUNT"] = 100
    copy_values["ZERO_COPY_HIT_COUNT"] = 0
    restart_count = len(comparison["paired_crash_points"])
    if profile_id == "ISOLATED_SIDECAR":
        restart_count += len(comparison["sidecar_supplemental_crash_points"])
    measured_operations = 60_000 + 10 * saturation_completed
    return {
        "copy_accounting": [{"counter_id": item, "value": copy_values[item]} for item in copy_ids],
        "fixed_load_blocks": [
            {
                "block_index": index,
                "completed_operations": 6_000,
                "offered_operations": 6_000,
                "offered_ops_per_second": 100,
                "window_seconds": 60,
            }
            for index in range(10)
        ],
        "fixed_load_latency_ns": {
            "p50": 500,
            "p95": 800,
            "p99": 1_000 if profile_id == "EMBEDDED_FFM" else 1_200,
            "sample_count": 60_000,
        },
        "input_provenance_sha256": content_id(f"{profile_id}:input-provenance"),
        "java_survived_all_native_deaths": profile_id == "ISOLATED_SIDECAR",
        "max_staging_fallback": {
            "egress_bytes": 50,
            "ingress_bytes": 50,
            "operation_count_scanned": measured_operations,
            "operation_id": "fixed-0-operation-0",
            "total_bytes": 100,
        },
        "measurement_coverage": [
            {
                "evidence_sha256": content_id(f"{profile_id}:{item}"),
                "measurement_id": item,
                "status": "PRESENT",
            }
            for item in comparison["required_measurements"]
        ],
        "phase_latency_ns": {
            "p50": 300,
            "p95": 600,
            "p99": 900 if profile_id == "EMBEDDED_FFM" else 1_000,
            "sample_count": 60_000,
        },
        "phase_latency_sample_count": 60_000,
        "profile_id": profile_id,
        "raw_capture_sha256": content_id(f"{profile_id}:raw-capture"),
        "restart_to_ready_ns": [1_000_000 + index for index in range(restart_count)],
        "saturation_blocks": [
            {
                "block_index": index,
                "completed_operations": saturation_completed,
                "window_seconds": 60,
            }
            for index in range(10)
        ],
        "wal_artifacts": {
            "record_vote": {
                "sha256": content_id("record-vote-wal"),
                "size_bytes": 101,
            },
            "runtime": {
                "sha256": content_id("runtime-wal"),
                "size_bytes": 202,
            },
        },
        "warmup_completed_operations": aggregation["warmup_operations"],
    }


def evidence_document() -> dict[str, object]:
    design = gate.load_frozen_design()
    comparison = design["comparison_plan"]
    profiles = [
        profile_document("EMBEDDED_FFM", design),
        profile_document("ISOLATED_SIDECAR", design),
    ]
    semantic_equalities = [
        marker(item, "equality_id", status="EXACT", paired=True)
        for item in comparison["exact_cross_profile_equalities"]
    ]
    wal_equality = next(
        item
        for item in semantic_equalities
        if item["equality_id"] == "WAL_RECEIPTS_AND_DURABLE_SEQUENCES"
    )
    for field, profile in zip(("embedded_sha256", "sidecar_sha256"), profiles, strict=True):
        wal_equality[field] = gate.sha256_id(gate.canonical_bytes(profile["wal_artifacts"]))
    return {
        "authority": gate.expected_authority(design),
        "common_hard_gates": [marker(item, "gate_id") for item in comparison["hard_gates_common"]],
        "crash_coverage": {
            "paired": [
                {
                    "crash_point": item,
                    "embedded_evidence_sha256": content_id("embedded:" + item),
                    "sidecar_evidence_sha256": content_id("sidecar:" + item),
                    "status": "PASS",
                }
                for item in comparison["paired_crash_points"]
            ],
            "sidecar_supplemental": [
                {
                    "crash_point": item,
                    "evidence_sha256": content_id("supplemental:" + item),
                    "status": "PASS",
                }
                for item in comparison["sidecar_supplemental_crash_points"]
            ],
        },
        "design_canonical_id": gate.EXPECTED_DESIGN_CANONICAL_ID,
        "design_sha256": gate.EXPECTED_DESIGN_SHA256,
        "execution_class": "NON_PRIMARY_RUNTIME_PROFILE_QUALIFICATION",
        "formal_semantics_id": gate.FORMAL_ID,
        "pair_fields": [
            marker(item, "field_id", status="EXACT", paired=True)
            for item in comparison["identical_pair_fields"]
        ],
        "profiles": profiles,
        "risk_acceptance": None,
        "schema_version": "1.0.0",
        "semantic_equalities": semantic_equalities,
        "sidecar_hard_gates": [
            marker(item, "gate_id") for item in comparison["hard_gates_sidecar"]
        ],
        "status": "COMPLETE",
        "type_name": "FEATURE010_SIDECAR_COMPARISON_EVIDENCE",
    }


def copy_counter(profile: dict[str, object], counter_id: str) -> dict[str, object]:
    return next(item for item in profile["copy_accounting"] if item["counter_id"] == counter_id)


def set_saturation(profile: dict[str, object], value: int) -> None:
    for block in profile["saturation_blocks"]:
        block["completed_operations"] = value
    scanned = 60_000 + 10 * value
    profile["max_staging_fallback"]["operation_count_scanned"] = scanned


def test_valid_evidence_selects_sidecar_without_promoting_authority() -> None:
    result = gate.validate_evidence(evidence_document())

    assert result["status"] == "PASS"
    assert result["selected_profile"] == "ISOLATED_SIDECAR"
    assert result["metrics"] == {
        "fallback_copy_bytes_per_operation": 100,
        "p99_fixed_load_latency_ratio_bps": 12_000,
        "saturation_throughput_ratio_bps": 9_500,
    }
    assert result["authority"]["selected_profile"] == "ISOLATED_SIDECAR"
    assert result["authority"]["feature010_go"] is False
    assert result["authority"]["gate_a_qualified"] is False
    assert result["authority"]["gate_b_qualified"] is False
    assert result["authority"]["gate_c_qualified"] is False
    assert result["authority"]["gate_d_qualified"] is False
    assert result["authority"]["pilot_execution_authorized"] is False
    assert result["authority"]["benchmark_result_qc"] is None
    assert result["authority"]["primary_observation_count"] == 0


def test_latency_threshold_is_inclusive_and_next_basis_point_fails() -> None:
    evidence = evidence_document()
    evidence["profiles"][0]["fixed_load_latency_ns"]["p99"] = 10_000
    evidence["profiles"][1]["fixed_load_latency_ns"]["p99"] = 12_500

    assert gate.validate_evidence(evidence)["selected_profile"] == "ISOLATED_SIDECAR"

    evidence["profiles"][1]["fixed_load_latency_ns"]["p99"] = 12_501
    result = gate.validate_evidence(evidence)
    assert result["metrics"]["p99_fixed_load_latency_ratio_bps"] == 12_501
    assert result["selected_profile"] is None
    assert result["status"] == "NO_SELECTION"


def test_throughput_threshold_is_inclusive_and_one_basis_point_below_fails() -> None:
    evidence = evidence_document()
    set_saturation(evidence["profiles"][0], 10_000)
    set_saturation(evidence["profiles"][1], 9_000)

    assert gate.validate_evidence(evidence)["selected_profile"] == "ISOLATED_SIDECAR"

    set_saturation(evidence["profiles"][1], 8_999)
    result = gate.validate_evidence(evidence)
    assert result["metrics"]["saturation_throughput_ratio_bps"] == 8_999
    assert result["selected_profile"] is None


def test_fallback_threshold_uses_checked_per_operation_sum() -> None:
    evidence = evidence_document()
    sidecar = evidence["profiles"][1]
    threshold = 33_570_816
    sidecar["max_staging_fallback"].update(
        {"egress_bytes": threshold // 2, "ingress_bytes": threshold // 2, "total_bytes": threshold}
    )
    copy_counter(sidecar, "STAGING_FALLBACK_INGRESS_BYTES")["value"] = threshold // 2
    copy_counter(sidecar, "STAGING_FALLBACK_EGRESS_BYTES")["value"] = threshold // 2

    assert gate.validate_evidence(evidence)["selected_profile"] == "ISOLATED_SIDECAR"

    sidecar["max_staging_fallback"]["egress_bytes"] += 1
    sidecar["max_staging_fallback"]["total_bytes"] += 1
    copy_counter(sidecar, "STAGING_FALLBACK_EGRESS_BYTES")["value"] += 1
    result = gate.validate_evidence(evidence)
    assert result["metrics"]["fallback_copy_bytes_per_operation"] == threshold + 1
    assert result["selected_profile"] is None


def test_self_asserted_risk_acceptance_is_rejected_and_cannot_select_embedded() -> None:
    evidence = evidence_document()
    evidence["profiles"][1]["fixed_load_latency_ns"]["p99"] = 2_000
    evidence["risk_acceptance"] = {
        "accepts_process_cofailure": True,
        "disclaims_crash_isolation": True,
        "evidence_sha256": content_id("self-asserted-risk-acceptance"),
        "frozen_before_measurement": True,
        "status": "PASS",
    }

    with pytest.raises(gate.ComparisonError, match="RISK_ACCEPTANCE_UNAVAILABLE_IN_SCHEMA_V1"):
        gate.validate_evidence(evidence)


def test_failed_gate_or_equality_selects_null() -> None:
    evidence = evidence_document()
    evidence["common_hard_gates"][0]["status"] = "FAIL"
    assert gate.validate_evidence(evidence)["selected_profile"] is None

    evidence = evidence_document()
    equality = evidence["semantic_equalities"][0]
    equality["status"] = "MISMATCH"
    equality["sidecar_sha256"] = content_id("different")
    assert gate.validate_evidence(evidence)["selected_profile"] is None


def test_missing_duplicate_or_ambiguous_gate_is_rejected() -> None:
    evidence = evidence_document()
    evidence["common_hard_gates"].pop()
    with pytest.raises(gate.ComparisonError, match="COMMON_HARD_GATES"):
        gate.validate_evidence(evidence)

    evidence = evidence_document()
    evidence["common_hard_gates"][1]["gate_id"] = evidence["common_hard_gates"][0]["gate_id"]
    with pytest.raises(gate.ComparisonError, match="COMMON_HARD_GATES"):
        gate.validate_evidence(evidence)

    evidence = evidence_document()
    evidence["common_hard_gates"][0]["status"] = "UNKNOWN"
    with pytest.raises(gate.ComparisonError, match="COMMON_HARD_GATES"):
        gate.validate_evidence(evidence)


def test_authority_promotion_is_rejected() -> None:
    evidence = evidence_document()
    evidence["authority"]["feature010_go"] = True

    with pytest.raises(gate.ComparisonError, match="EVIDENCE_AUTHORITY"):
        gate.validate_evidence(evidence)


def test_incomplete_or_misordered_schedule_is_rejected() -> None:
    evidence = evidence_document()
    evidence["profiles"][0]["fixed_load_blocks"][0]["completed_operations"] = 5_999
    with pytest.raises(gate.ComparisonError, match="FIXED_INCOMPLETE"):
        gate.validate_evidence(evidence)

    evidence = evidence_document()
    evidence["profiles"][1]["saturation_blocks"][1]["block_index"] = 0
    with pytest.raises(gate.ComparisonError, match="SATURATION_BLOCK_ORDER"):
        gate.validate_evidence(evidence)


def test_compact_aggregate_counts_must_cover_exact_60000_samples() -> None:
    evidence = evidence_document()
    evidence["profiles"][1]["fixed_load_latency_ns"]["sample_count"] = 59_999

    with pytest.raises(gate.ComparisonError, match="LATENCY_SAMPLE_COUNT"):
        gate.validate_evidence(evidence)


def test_boolean_and_u64_overflow_are_not_accepted_as_counts() -> None:
    evidence = evidence_document()
    evidence["profiles"][0]["warmup_completed_operations"] = True
    with pytest.raises(gate.ComparisonError, match="WARMUP_COUNT"):
        gate.validate_evidence(evidence)

    evidence = evidence_document()
    fallback = evidence["profiles"][1]["max_staging_fallback"]
    fallback["ingress_bytes"] = gate.U64_MAX
    fallback["egress_bytes"] = 1
    fallback["total_bytes"] = gate.U64_MAX
    with pytest.raises(gate.ComparisonError, match="FALLBACK_SUM_OVERFLOW"):
        gate.validate_evidence(evidence)


def test_fallback_sum_scan_count_and_zero_copy_relations_are_checked() -> None:
    evidence = evidence_document()
    evidence["profiles"][1]["max_staging_fallback"]["total_bytes"] = 99
    with pytest.raises(gate.ComparisonError, match="FALLBACK_SUM"):
        gate.validate_evidence(evidence)

    evidence = evidence_document()
    evidence["profiles"][1]["max_staging_fallback"]["operation_count_scanned"] -= 1
    with pytest.raises(gate.ComparisonError, match="FALLBACK_SCAN_COUNT"):
        gate.validate_evidence(evidence)

    evidence = evidence_document()
    sidecar = evidence["profiles"][1]
    copy_counter(sidecar, "ZERO_COPY_HIT_COUNT")["value"] = 101
    with pytest.raises(gate.ComparisonError, match="ZERO_COPY_COUNTS"):
        gate.validate_evidence(evidence)

    evidence = evidence_document()
    sidecar = evidence["profiles"][1]
    copy_counter(sidecar, "ZERO_COPY_HIT_COUNT")["value"] = 1
    with pytest.raises(gate.ComparisonError, match="ZERO_COPY_HIT_FORBIDDEN"):
        gate.validate_evidence(evidence)


def test_wal_artifact_digest_and_size_are_validated() -> None:
    evidence = evidence_document()
    evidence["profiles"][1]["wal_artifacts"]["record_vote"]["size_bytes"] = 0
    with pytest.raises(gate.ComparisonError, match="WAL_ARTIFACT_SIZE"):
        gate.validate_evidence(evidence)

    evidence = evidence_document()
    evidence["profiles"][1]["wal_artifacts"]["runtime"]["sha256"] = "not-a-content-id"
    with pytest.raises(gate.ComparisonError, match="WAL_ARTIFACT_SHA256"):
        gate.validate_evidence(evidence)

    evidence = evidence_document()
    evidence["profiles"][1]["wal_artifacts"]["record_vote"]["sha256"] = content_id(
        "different-record-vote-wal"
    )
    with pytest.raises(gate.ComparisonError, match="WAL_EQUALITY_BINDING"):
        gate.validate_evidence(evidence)


def test_compact_gate_rejects_empty_vote_receipt_transcript() -> None:
    evidence = evidence_document()
    equality = next(
        item
        for item in evidence["semantic_equalities"]
        if item["equality_id"] == "CANONICAL_VOTE_RECEIPT_BYTES"
    )
    equality["embedded_sha256"] = gate.EMPTY_SHA256
    equality["sidecar_sha256"] = gate.EMPTY_SHA256

    with pytest.raises(gate.ComparisonError, match="VOTE_RECEIPT_TRANSCRIPT_EMPTY"):
        gate.validate_evidence(evidence)


def test_missing_crash_or_measurement_evidence_selects_or_fails_closed() -> None:
    evidence = evidence_document()
    evidence["crash_coverage"]["paired"].pop()
    with pytest.raises(gate.ComparisonError, match="PAIRED_CRASH_COUNT"):
        gate.validate_evidence(evidence)

    evidence = evidence_document()
    evidence["profiles"][1]["measurement_coverage"][0]["status"] = "MISSING"
    assert gate.validate_evidence(evidence)["selected_profile"] is None


def test_performance_failure_requires_future_versioned_risk_contract() -> None:
    evidence = evidence_document()
    evidence["profiles"][1]["fixed_load_latency_ns"]["p99"] = 2_000

    result = gate.validate_evidence(evidence)

    assert result["selected_profile"] is None
    assert result["selection_reason"] == (
        "SIDECAR_PERFORMANCE_FAILED_FUTURE_VERSIONED_RISK_ACCEPTANCE_REQUIRED"
    )
    assert result["embedded_fallback_policy"] == (
        "UNAVAILABLE_IN_SCHEMA_V1_REQUIRES_FUTURE_SEPARATELY_FROZEN_CONTRACT_VERSION"
    )


def test_design_binding_and_exact_marker_hashes_are_enforced() -> None:
    evidence = evidence_document()
    evidence["design_sha256"] = content_id("substituted-design")
    with pytest.raises(gate.ComparisonError, match="EVIDENCE_DESIGN_SHA256"):
        gate.validate_evidence(evidence)

    evidence = evidence_document()
    evidence["pair_fields"][0]["sidecar_sha256"] = content_id("different")
    with pytest.raises(gate.ComparisonError, match="PAIR_FIELDS"):
        gate.validate_evidence(evidence)


def test_checked_ratio_formulas_are_integer_and_fail_closed() -> None:
    assert gate.checked_ratio_bps(5, 4, ceiling=True) == 12_500
    assert gate.checked_ratio_bps(5, 4, ceiling=False) == 12_500
    assert gate.checked_ratio_bps(1, 3, ceiling=True) == 3_334
    assert gate.checked_ratio_bps(1, 3, ceiling=False) == 3_333
    with pytest.raises(gate.ComparisonError, match="RATIO_DENOMINATOR"):
        gate.checked_ratio_bps(1, 0, ceiling=True)
    with pytest.raises(gate.ComparisonError, match="RATIO_NUMERATOR"):
        gate.checked_ratio_bps(True, 1, ceiling=True)


def test_canonical_loader_rejects_duplicate_keys(tmp_path: Path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_bytes(b'{"schema_version":"1.0.0","schema_version":"2.0.0"}')

    with pytest.raises(gate.ComparisonError, match="JSON_DUPLICATE_KEY"):
        gate.canonical_document(path)


def test_result_hash_is_stable_for_canonical_evidence() -> None:
    evidence = evidence_document()
    expected = gate.sha256_id(gate.canonical_bytes(evidence))

    assert gate.validate_evidence(copy.deepcopy(evidence))["comparison_evidence_sha256"] == expected
    assert json.loads(gate.canonical_bytes(evidence)) == evidence
