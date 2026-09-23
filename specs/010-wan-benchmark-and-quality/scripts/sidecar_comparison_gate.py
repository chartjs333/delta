#!/usr/bin/env python3
"""Verify compact Feature 010 embedded-versus-sidecar comparison evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
DESIGN_PATH: Final = ROOT / "specs/010-wan-benchmark-and-quality/sidecar-refinement-design.json"
EXPECTED_DESIGN_SHA256: Final = (
    "sha256:dc031e7fb413d9ef1ed33b2d4fe1fedb170100e2782f636e7162b40cabbeb4c8"
)
EXPECTED_DESIGN_CANONICAL_ID: Final = (
    "sha256:080074ff7de58d7ba025b8156ceafb0085937bb6ed74485d217af664d0ecf6ef"
)
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
EMPTY_SHA256: Final = "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
U64_MAX: Final = (1 << 64) - 1
U128_MAX: Final = (1 << 128) - 1
CONTENT_ID = re.compile(r"sha256:[0-9a-f]{64}\Z")

EVIDENCE_FIELDS: Final = {
    "authority",
    "common_hard_gates",
    "crash_coverage",
    "design_canonical_id",
    "design_sha256",
    "execution_class",
    "formal_semantics_id",
    "pair_fields",
    "profiles",
    "risk_acceptance",
    "schema_version",
    "semantic_equalities",
    "sidecar_hard_gates",
    "status",
    "type_name",
}
PROFILE_FIELDS: Final = {
    "copy_accounting",
    "fixed_load_blocks",
    "fixed_load_latency_ns",
    "input_provenance_sha256",
    "java_survived_all_native_deaths",
    "max_staging_fallback",
    "measurement_coverage",
    "phase_latency_ns",
    "phase_latency_sample_count",
    "profile_id",
    "raw_capture_sha256",
    "restart_to_ready_ns",
    "saturation_blocks",
    "wal_artifacts",
    "warmup_completed_operations",
}
FIXED_BLOCK_FIELDS: Final = {
    "block_index",
    "completed_operations",
    "offered_operations",
    "offered_ops_per_second",
    "window_seconds",
}
SATURATION_BLOCK_FIELDS: Final = {
    "block_index",
    "completed_operations",
    "window_seconds",
}
LATENCY_FIELDS: Final = {"p50", "p95", "p99", "sample_count"}
FALLBACK_FIELDS: Final = {
    "egress_bytes",
    "ingress_bytes",
    "operation_count_scanned",
    "operation_id",
    "total_bytes",
}
WAL_ARTIFACTS_FIELDS: Final = {"record_vote", "runtime"}
WAL_ARTIFACT_FIELDS: Final = {"sha256", "size_bytes"}


class ComparisonError(RuntimeError):
    """Stable fail-closed comparison evidence error."""


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise ComparisonError(f"{code}:{detail}" if detail else code)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def sha256_id(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        require(key not in result, "JSON_DUPLICATE_KEY", key)
        result[key] = value
    return result


def canonical_document(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        value = json.loads(raw, object_pairs_hook=reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ComparisonError(f"JSON_INVALID:{path.name}") from error
    require(isinstance(value, dict), "JSON_OBJECT_REQUIRED", path.name)
    encoded = canonical_bytes(value)
    require(raw in {encoded, encoded + b"\n"}, "JSON_NOT_CANONICAL", path.name)
    return value, encoded


def exact_object(value: object, fields: set[str], code: str) -> dict[str, Any]:
    require(isinstance(value, dict) and set(value) == fields, code)
    return value


def strict_u64(value: object, code: str, *, positive: bool = False) -> int:
    require(type(value) is int, code)
    result = int(value)
    require(0 <= result <= U64_MAX, code)
    if positive:
        require(result > 0, code)
    return result


def content_id(value: object, code: str) -> str:
    require(isinstance(value, str) and CONTENT_ID.fullmatch(value) is not None, code)
    return value


def checked_add_u64(left: object, right: object, code: str) -> int:
    left_value = strict_u64(left, code)
    right_value = strict_u64(right, code)
    total = left_value + right_value
    require(total <= U64_MAX, code)
    return total


def checked_sum_u64(values: list[int], code: str) -> int:
    result = 0
    for value in values:
        result = checked_add_u64(result, value, code)
    return result


def checked_ratio_bps(numerator: object, denominator: object, *, ceiling: bool) -> int:
    numerator_value = strict_u64(numerator, "RATIO_NUMERATOR")
    denominator_value = strict_u64(denominator, "RATIO_DENOMINATOR", positive=True)
    product = numerator_value * 10_000
    require(product <= U128_MAX, "RATIO_MULTIPLICATION_OVERFLOW")
    quotient, remainder = divmod(product, denominator_value)
    if ceiling and remainder:
        quotient += 1
    require(quotient <= U64_MAX, "RATIO_RESULT_OVERFLOW")
    return quotient


def load_frozen_design() -> dict[str, Any]:
    document, canonical = canonical_document(DESIGN_PATH)
    raw = DESIGN_PATH.read_bytes()
    require(sha256_id(raw) == EXPECTED_DESIGN_SHA256, "DESIGN_RAW_SHA256")
    require(sha256_id(canonical) == EXPECTED_DESIGN_CANONICAL_ID, "DESIGN_CANONICAL_ID")
    require(document.get("status") == "DESIGN_ONLY_NOT_IMPLEMENTED", "DESIGN_STATUS")
    require(document.get("measurement_status") == "NOT_RUN", "DESIGN_MEASUREMENT_STATUS")
    require(
        document.get("formal_impact", {}).get("formal_semantics_id") == FORMAL_ID,
        "DESIGN_FORMAL_ID",
    )
    return document


def expected_authority(design: dict[str, Any]) -> dict[str, Any]:
    authority = design.get("authority")
    require(isinstance(authority, dict), "DESIGN_AUTHORITY")
    expected = dict(authority)
    require(expected.pop("selected_profile", None) is None, "DESIGN_PROFILE_ALREADY_SELECTED")
    return expected


def validate_marker_list(
    value: object,
    expected_ids: list[str],
    *,
    id_field: str,
    allowed_statuses: set[str],
    code: str,
    paired_hashes: bool,
) -> bool:
    require(isinstance(value, list) and len(value) == len(expected_ids), code)
    all_pass = True
    for index, expected_id in enumerate(expected_ids):
        item = value[index]
        fields = {id_field, "evidence_sha256", "status"}
        if paired_hashes:
            fields |= {"embedded_sha256", "sidecar_sha256"}
        record = exact_object(item, fields, code)
        require(record[id_field] == expected_id, code, expected_id)
        content_id(record["evidence_sha256"], code)
        status = record["status"]
        require(status in allowed_statuses, code, expected_id)
        if paired_hashes:
            embedded = content_id(record["embedded_sha256"], code)
            sidecar = content_id(record["sidecar_sha256"], code)
            exact = status == "EXACT"
            require((embedded == sidecar) is exact, code, expected_id)
            all_pass = all_pass and exact
        else:
            all_pass = all_pass and status == "PASS"
    return all_pass


def validate_measurement_coverage(value: object, expected_ids: list[str], profile: str) -> bool:
    require(isinstance(value, list) and len(value) == len(expected_ids), "MEASUREMENT_COVERAGE")
    complete = True
    for index, measurement_id in enumerate(expected_ids):
        record = exact_object(
            value[index],
            {"evidence_sha256", "measurement_id", "status"},
            "MEASUREMENT_COVERAGE",
        )
        require(record["measurement_id"] == measurement_id, "MEASUREMENT_ORDER", profile)
        content_id(record["evidence_sha256"], "MEASUREMENT_EVIDENCE")
        require(record["status"] in {"PRESENT", "MISSING"}, "MEASUREMENT_STATUS")
        complete = complete and record["status"] == "PRESENT"
    return complete


def validate_blocks(profile: dict[str, Any], aggregation: dict[str, Any]) -> tuple[int, int]:
    fixed = profile["fixed_load_blocks"]
    fixed_count = strict_u64(aggregation["measured_blocks"], "DESIGN_FIXED_BLOCKS", positive=True)
    require(isinstance(fixed, list) and len(fixed) == fixed_count, "FIXED_BLOCK_COUNT")
    fixed_total = 0
    for index, item in enumerate(fixed):
        block = exact_object(item, FIXED_BLOCK_FIELDS, "FIXED_BLOCK_FIELDS")
        require(strict_u64(block["block_index"], "FIXED_BLOCK_INDEX") == index, "FIXED_BLOCK_ORDER")
        require(
            strict_u64(block["offered_operations"], "FIXED_OFFERED")
            == aggregation["fixed_load_offered_operations_per_block"],
            "FIXED_OFFERED",
        )
        completed = strict_u64(block["completed_operations"], "FIXED_COMPLETED")
        require(completed == block["offered_operations"], "FIXED_INCOMPLETE")
        require(
            strict_u64(block["offered_ops_per_second"], "FIXED_RATE")
            == aggregation["fixed_offered_load_ops_per_second"],
            "FIXED_RATE",
        )
        require(
            strict_u64(block["window_seconds"], "FIXED_WINDOW")
            == aggregation["throughput_window_seconds"],
            "FIXED_WINDOW",
        )
        fixed_total = checked_add_u64(fixed_total, completed, "FIXED_TOTAL_OVERFLOW")

    saturation = profile["saturation_blocks"]
    saturation_count = strict_u64(
        aggregation["saturation_blocks"], "DESIGN_SATURATION_BLOCKS", positive=True
    )
    require(
        isinstance(saturation, list) and len(saturation) == saturation_count,
        "SATURATION_BLOCK_COUNT",
    )
    saturation_values: list[int] = []
    for index, item in enumerate(saturation):
        block = exact_object(item, SATURATION_BLOCK_FIELDS, "SATURATION_BLOCK_FIELDS")
        require(
            strict_u64(block["block_index"], "SATURATION_BLOCK_INDEX") == index,
            "SATURATION_BLOCK_ORDER",
        )
        completed = strict_u64(block["completed_operations"], "SATURATION_COMPLETED", positive=True)
        require(
            strict_u64(block["window_seconds"], "SATURATION_WINDOW")
            == aggregation["throughput_window_seconds"],
            "SATURATION_WINDOW",
        )
        saturation_values.append(completed)
    return fixed_total, min(saturation_values)


def validate_profile(
    value: object,
    expected_profile: str,
    design: dict[str, Any],
) -> dict[str, Any]:
    profile = exact_object(value, PROFILE_FIELDS, "PROFILE_FIELDS")
    require(profile["profile_id"] == expected_profile, "PROFILE_ID", expected_profile)
    content_id(profile["input_provenance_sha256"], "INPUT_PROVENANCE_SHA256")
    content_id(profile["raw_capture_sha256"], "RAW_CAPTURE_SHA256")
    wal_artifacts = exact_object(
        profile["wal_artifacts"], WAL_ARTIFACTS_FIELDS, "WAL_ARTIFACTS_FIELDS"
    )
    for artifact_id in ("record_vote", "runtime"):
        artifact = exact_object(
            wal_artifacts[artifact_id], WAL_ARTIFACT_FIELDS, "WAL_ARTIFACT_FIELDS"
        )
        content_id(artifact["sha256"], "WAL_ARTIFACT_SHA256")
        strict_u64(artifact["size_bytes"], "WAL_ARTIFACT_SIZE", positive=True)
    comparison = design["comparison_plan"]
    aggregation = comparison["aggregation"]
    require(
        strict_u64(profile["warmup_completed_operations"], "WARMUP_COUNT")
        == aggregation["warmup_operations"],
        "WARMUP_COUNT",
    )
    fixed_total, saturation_min = validate_blocks(profile, aggregation)

    latency = exact_object(profile["fixed_load_latency_ns"], LATENCY_FIELDS, "LATENCY_FIELDS")
    sample_count = strict_u64(latency["sample_count"], "LATENCY_SAMPLE_COUNT")
    require(sample_count == fixed_total == 60_000, "LATENCY_SAMPLE_COUNT")
    p50 = strict_u64(latency["p50"], "LATENCY_P50", positive=True)
    p95 = strict_u64(latency["p95"], "LATENCY_P95", positive=True)
    p99 = strict_u64(latency["p99"], "LATENCY_P99", positive=True)
    require(p50 <= p95 <= p99, "LATENCY_PERCENTILE_ORDER")
    require(
        strict_u64(profile["phase_latency_sample_count"], "PHASE_SAMPLE_COUNT") == fixed_total,
        "PHASE_SAMPLE_COUNT",
    )
    phase_latency = exact_object(
        profile["phase_latency_ns"], LATENCY_FIELDS, "PHASE_LATENCY_FIELDS"
    )
    require(
        strict_u64(phase_latency["sample_count"], "PHASE_LATENCY_SAMPLE_COUNT") == fixed_total,
        "PHASE_LATENCY_SAMPLE_COUNT",
    )
    phase_p50 = strict_u64(phase_latency["p50"], "PHASE_LATENCY_P50", positive=True)
    phase_p95 = strict_u64(phase_latency["p95"], "PHASE_LATENCY_P95", positive=True)
    phase_p99 = strict_u64(phase_latency["p99"], "PHASE_LATENCY_P99", positive=True)
    require(phase_p50 <= phase_p95 <= phase_p99, "PHASE_LATENCY_PERCENTILE_ORDER")

    restart = profile["restart_to_ready_ns"]
    expected_restarts = len(comparison["paired_crash_points"])
    if expected_profile == "ISOLATED_SIDECAR":
        expected_restarts += len(comparison["sidecar_supplemental_crash_points"])
    require(isinstance(restart, list) and len(restart) == expected_restarts, "RESTART_SAMPLE_COUNT")
    for item in restart:
        strict_u64(item, "RESTART_SAMPLE", positive=True)

    copy_values = profile["copy_accounting"]
    copy_ids = comparison["copy_accounting"]
    require(isinstance(copy_values, list) and len(copy_values) == len(copy_ids), "COPY_COVERAGE")
    copy: dict[str, int] = {}
    for index, counter_id in enumerate(copy_ids):
        record = exact_object(copy_values[index], {"counter_id", "value"}, "COPY_FIELDS")
        require(record["counter_id"] == counter_id, "COPY_ORDER", counter_id)
        copy[counter_id] = strict_u64(record["value"], "COPY_VALUE")

    measured_operations = checked_add_u64(
        fixed_total,
        checked_sum_u64(
            [
                strict_u64(item["completed_operations"], "SATURATION_COMPLETED")
                for item in profile["saturation_blocks"]
            ],
            "SATURATION_TOTAL_OVERFLOW",
        ),
        "MEASURED_OPERATION_OVERFLOW",
    )
    require(copy["ZERO_COPY_HIT_COUNT"] <= copy["ZERO_COPY_ELIGIBLE_COUNT"], "ZERO_COPY_COUNTS")
    require(copy["ZERO_COPY_ELIGIBLE_COUNT"] <= measured_operations, "ZERO_COPY_COUNTS")
    require(copy["ZERO_COPY_HIT_COUNT"] == 0, "ZERO_COPY_HIT_FORBIDDEN")

    fallback = exact_object(profile["max_staging_fallback"], FALLBACK_FIELDS, "FALLBACK_FIELDS")
    require(
        isinstance(fallback["operation_id"], str) and bool(fallback["operation_id"]),
        "FALLBACK_OPERATION_ID",
    )
    ingress = strict_u64(fallback["ingress_bytes"], "FALLBACK_INGRESS")
    egress = strict_u64(fallback["egress_bytes"], "FALLBACK_EGRESS")
    total = strict_u64(fallback["total_bytes"], "FALLBACK_TOTAL")
    require(total == checked_add_u64(ingress, egress, "FALLBACK_SUM_OVERFLOW"), "FALLBACK_SUM")
    require(
        strict_u64(fallback["operation_count_scanned"], "FALLBACK_SCAN_COUNT")
        == measured_operations,
        "FALLBACK_SCAN_COUNT",
    )
    require(ingress <= copy["STAGING_FALLBACK_INGRESS_BYTES"], "FALLBACK_INGRESS_TOTAL")
    require(egress <= copy["STAGING_FALLBACK_EGRESS_BYTES"], "FALLBACK_EGRESS_TOTAL")

    measurements_complete = validate_measurement_coverage(
        profile["measurement_coverage"], comparison["required_measurements"], expected_profile
    )
    survived = profile["java_survived_all_native_deaths"]
    require(type(survived) is bool, "JAVA_SURVIVAL_TYPE")
    if expected_profile == "EMBEDDED_FFM":
        require(survived is False, "EMBEDDED_CRASH_ISOLATION_CLAIM")

    return {
        "fallback_max": total,
        "fixed_p99": p99,
        "measurements_complete": measurements_complete,
        "saturation_min": saturation_min,
        "sidecar_java_survived": survived,
        "wal_transcript_sha256": sha256_id(canonical_bytes(wal_artifacts)),
    }


def validate_crash_coverage(value: object, design: dict[str, Any]) -> bool:
    crash = exact_object(value, {"paired", "sidecar_supplemental"}, "CRASH_FIELDS")
    paired_ids = design["comparison_plan"]["paired_crash_points"]
    paired = crash["paired"]
    require(isinstance(paired, list) and len(paired) == len(paired_ids), "PAIRED_CRASH_COUNT")
    complete = True
    for index, crash_id in enumerate(paired_ids):
        record = exact_object(
            paired[index],
            {"crash_point", "embedded_evidence_sha256", "sidecar_evidence_sha256", "status"},
            "PAIRED_CRASH_FIELDS",
        )
        require(record["crash_point"] == crash_id, "PAIRED_CRASH_ORDER")
        content_id(record["embedded_evidence_sha256"], "PAIRED_CRASH_EVIDENCE")
        content_id(record["sidecar_evidence_sha256"], "PAIRED_CRASH_EVIDENCE")
        require(record["status"] in {"PASS", "FAIL"}, "PAIRED_CRASH_STATUS")
        complete = complete and record["status"] == "PASS"

    supplemental_ids = design["comparison_plan"]["sidecar_supplemental_crash_points"]
    supplemental = crash["sidecar_supplemental"]
    require(
        isinstance(supplemental, list) and len(supplemental) == len(supplemental_ids),
        "SUPPLEMENTAL_CRASH_COUNT",
    )
    for index, crash_id in enumerate(supplemental_ids):
        record = exact_object(
            supplemental[index],
            {"crash_point", "evidence_sha256", "status"},
            "SUPPLEMENTAL_CRASH_FIELDS",
        )
        require(record["crash_point"] == crash_id, "SUPPLEMENTAL_CRASH_ORDER")
        content_id(record["evidence_sha256"], "SUPPLEMENTAL_CRASH_EVIDENCE")
        require(record["status"] in {"PASS", "FAIL"}, "SUPPLEMENTAL_CRASH_STATUS")
        complete = complete and record["status"] == "PASS"
    return complete


def validate_evidence(
    document: dict[str, Any], design: dict[str, Any] | None = None
) -> dict[str, Any]:
    frozen = load_frozen_design() if design is None else design
    require(set(document) == EVIDENCE_FIELDS, "EVIDENCE_FIELDS")
    require(
        document["type_name"] == "FEATURE010_SIDECAR_COMPARISON_EVIDENCE",
        "EVIDENCE_TYPE",
    )
    require(document["schema_version"] == "1.0.0", "EVIDENCE_SCHEMA")
    require(document["status"] == "COMPLETE", "EVIDENCE_STATUS")
    require(
        document["execution_class"] == "NON_PRIMARY_RUNTIME_PROFILE_QUALIFICATION",
        "EVIDENCE_EXECUTION_CLASS",
    )
    require(document["formal_semantics_id"] == FORMAL_ID, "EVIDENCE_FORMAL_ID")
    require(document["design_sha256"] == EXPECTED_DESIGN_SHA256, "EVIDENCE_DESIGN_SHA256")
    require(
        document["design_canonical_id"] == EXPECTED_DESIGN_CANONICAL_ID,
        "EVIDENCE_DESIGN_CANONICAL_ID",
    )
    require(document["authority"] == expected_authority(frozen), "EVIDENCE_AUTHORITY")
    require(
        document["risk_acceptance"] is None,
        "RISK_ACCEPTANCE_UNAVAILABLE_IN_SCHEMA_V1",
    )

    comparison = frozen["comparison_plan"]
    pair_exact = validate_marker_list(
        document["pair_fields"],
        comparison["identical_pair_fields"],
        id_field="field_id",
        allowed_statuses={"EXACT", "MISMATCH"},
        code="PAIR_FIELDS",
        paired_hashes=True,
    )
    equalities_exact = validate_marker_list(
        document["semantic_equalities"],
        comparison["exact_cross_profile_equalities"],
        id_field="equality_id",
        allowed_statuses={"EXACT", "MISMATCH"},
        code="SEMANTIC_EQUALITIES",
        paired_hashes=True,
    )
    vote_receipt_index = comparison["exact_cross_profile_equalities"].index(
        "CANONICAL_VOTE_RECEIPT_BYTES"
    )
    vote_receipt_equality = document["semantic_equalities"][vote_receipt_index]
    require(
        vote_receipt_equality["embedded_sha256"] != EMPTY_SHA256
        and vote_receipt_equality["sidecar_sha256"] != EMPTY_SHA256,
        "VOTE_RECEIPT_TRANSCRIPT_EMPTY",
    )
    common_pass = validate_marker_list(
        document["common_hard_gates"],
        comparison["hard_gates_common"],
        id_field="gate_id",
        allowed_statuses={"PASS", "FAIL"},
        code="COMMON_HARD_GATES",
        paired_hashes=False,
    )
    sidecar_pass = validate_marker_list(
        document["sidecar_hard_gates"],
        comparison["hard_gates_sidecar"],
        id_field="gate_id",
        allowed_statuses={"PASS", "FAIL"},
        code="SIDECAR_HARD_GATES",
        paired_hashes=False,
    )
    crash_pass = validate_crash_coverage(document["crash_coverage"], frozen)

    profiles = document["profiles"]
    expected_profiles = comparison["profiles"]
    require(isinstance(profiles, list) and len(profiles) == len(expected_profiles), "PROFILES")
    profile_results = {
        profile_id: validate_profile(profiles[index], profile_id, frozen)
        for index, profile_id in enumerate(expected_profiles)
    }
    embedded = profile_results["EMBEDDED_FFM"]
    sidecar = profile_results["ISOLATED_SIDECAR"]
    wal_equality_index = comparison["exact_cross_profile_equalities"].index(
        "WAL_RECEIPTS_AND_DURABLE_SEQUENCES"
    )
    wal_equality = document["semantic_equalities"][wal_equality_index]
    require(
        wal_equality["embedded_sha256"] == embedded["wal_transcript_sha256"]
        and wal_equality["sidecar_sha256"] == sidecar["wal_transcript_sha256"],
        "WAL_EQUALITY_BINDING",
    )

    p99_ratio = checked_ratio_bps(sidecar["fixed_p99"], embedded["fixed_p99"], ceiling=True)
    throughput_ratio = checked_ratio_bps(
        sidecar["saturation_min"], embedded["saturation_min"], ceiling=False
    )
    selection_rule = frozen["profile_selection_rule"]
    hard_complete = (
        pair_exact
        and equalities_exact
        and common_pass
        and sidecar_pass
        and crash_pass
        and embedded["measurements_complete"]
        and sidecar["measurements_complete"]
        and sidecar["sidecar_java_survived"]
    )
    performance_pass = (
        p99_ratio <= selection_rule["sidecar_p99_fixed_load_latency_ratio_bps_max"]
        and throughput_ratio >= selection_rule["sidecar_saturation_throughput_ratio_bps_min"]
        and sidecar["fallback_max"] <= selection_rule["fallback_copy_bytes_per_operation_max"]
    )
    selected_profile: str | None = None
    reason = "HARD_GATE_OR_EVIDENCE_FAILED"
    if hard_complete and performance_pass:
        selected_profile = "ISOLATED_SIDECAR"
        reason = "ISOLATED_SIDECAR_QUALIFIED"
    elif hard_complete:
        reason = "SIDECAR_PERFORMANCE_FAILED_FUTURE_VERSIONED_RISK_ACCEPTANCE_REQUIRED"

    authority = dict(expected_authority(frozen))
    authority["selected_profile"] = selected_profile
    return {
        "authority": authority,
        "comparison_evidence_sha256": sha256_id(canonical_bytes(document)),
        "embedded_fallback_policy": (
            "UNAVAILABLE_IN_SCHEMA_V1_REQUIRES_FUTURE_SEPARATELY_FROZEN_CONTRACT_VERSION"
        ),
        "formal_semantics_id": FORMAL_ID,
        "metrics": {
            "fallback_copy_bytes_per_operation": sidecar["fallback_max"],
            "p99_fixed_load_latency_ratio_bps": p99_ratio,
            "saturation_throughput_ratio_bps": throughput_ratio,
        },
        "schema_version": "1.0.0",
        "selected_profile": selected_profile,
        "selection_reason": reason,
        "status": "PASS" if selected_profile is not None else "NO_SELECTION",
        "thresholds": {
            "fallback_copy_bytes_per_operation_max": selection_rule[
                "fallback_copy_bytes_per_operation_max"
            ],
            "sidecar_p99_fixed_load_latency_ratio_bps_max": selection_rule[
                "sidecar_p99_fixed_load_latency_ratio_bps_max"
            ],
            "sidecar_saturation_throughput_ratio_bps_min": selection_rule[
                "sidecar_saturation_throughput_ratio_bps_min"
            ],
            "tie_break": selection_rule["tie_break"],
        },
        "type_name": "FEATURE010_SIDECAR_PROFILE_SELECTION_RESULT",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("evidence", type=Path)
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    try:
        evidence, _ = canonical_document(arguments.evidence)
        result = validate_evidence(evidence)
        if arguments.output is not None:
            arguments.output.parent.mkdir(parents=True, exist_ok=True)
            arguments.output.write_bytes(canonical_bytes(result) + b"\n")
    except (ComparisonError, OSError, ValueError, KeyError, TypeError) as error:
        print(
            canonical_bytes(
                {"error": str(error), "selected_profile": None, "status": "FAIL"}
            ).decode()
        )
        return 2
    print(canonical_bytes(result).decode("utf-8"))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
