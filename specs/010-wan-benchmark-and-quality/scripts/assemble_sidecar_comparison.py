#!/usr/bin/env python3
"""Assemble compact sidecar-comparison evidence from canonical raw observations."""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Final

import sidecar_comparison_gate as gate

EXECUTION_CLASS: Final = "NON_PRIMARY_RUNTIME_PROFILE_QUALIFICATION"
RUN_TYPE: Final = "FEATURE010_SIDECAR_PROFILE_RUN_RAW"
MANIFEST_TYPE: Final = "FEATURE010_SIDECAR_GATE_CRASH_MANIFEST"
SATURATION_OFFERS_PER_BLOCK: Final = 10_000_000
GIT_OBJECT = re.compile(r"[0-9a-f]{40}\Z")
EMPTY_SHA256: Final = gate.sha256_id(b"")

RUN_FIELDS: Final = {
    "aggregation_rules",
    "bounds",
    "canonical_input_trace_sha256",
    "copy_accounting",
    "design_canonical_id",
    "design_sha256",
    "execution_class",
    "fault_trace_sha256",
    "fixed_load_blocks",
    "formal_semantics_id",
    "hardware_allocation_sha256",
    "initial_artifacts",
    "input_graph_nodes",
    "input_provenance",
    "input_provenance_sha256",
    "java_process_survival",
    "measurements",
    "native_core_sha256",
    "operation_copy_samples",
    "output_transcripts",
    "profile_id",
    "request_order",
    "restart_to_ready",
    "runtime_ids",
    "runtime_stats",
    "saturation_blocks",
    "saturation_request_schedule",
    "schema_version",
    "source",
    "timer_order",
    "toolchains_sha256",
    "type_name",
    "wal_artifacts",
    "warmup_completed_operations",
}
SOURCE_FIELDS: Final = {"commit", "tree"}
PROVENANCE_FIELDS: Final = {
    "capture_plan",
    "hardware_identity",
    "input_artifacts",
    "preparation_ended_at_utc",
    "preparation_started_at_utc",
    "runner_logs",
    "schema_version",
    "source",
    "tools",
    "type_name",
}
PROVENANCE_SOURCE_FIELDS: Final = {"commit", "tracked_clean", "tree"}
CAPTURE_PLAN_FIELDS: Final = {"argv", "output_path", "profile_id"}
HARDWARE_IDENTITY_FIELDS: Final = {
    "allocation_artifact_sha256",
    "available_processors",
    "os_arch",
    "os_name",
    "os_version",
}
INPUT_ARTIFACT_FIELDS: Final = {"artifact_id", "path", "sha256", "size_bytes"}
TOOL_IDENTITY_FIELDS: Final = {"path", "sha256", "size_bytes", "tool_id", "version"}
RUNNER_LOG_FIELDS: Final = {
    "argv",
    "ended_at_utc",
    "path",
    "runner_id",
    "sha256",
    "size_bytes",
    "started_at_utc",
    "tool_id",
}
INPUT_GRAPH_NODE_FIELDS: Final = {
    "artifact_sha256",
    "node_id",
    "provenance_sha256",
    "size_bytes",
}
RUNTIME_STATS_FIELDS: Final = {
    "duplicate_response_count",
    "rejected_frame_count",
    "retry_count",
    "stale_response_count",
}
WAL_ARTIFACTS_FIELDS: Final = {"record_vote", "runtime"}
WAL_ARTIFACT_FIELDS: Final = {"sha256", "size_bytes"}
CAPTURE_OPTION_NAMES: Final = {
    "--crash-observations",
    "--corpus",
    "--design",
    "--durable-directory",
    "--fault-trace",
    "--hardware-allocation",
    "--input-provenance",
    "--native-core",
    "--output",
    "--profile",
    "--projected-formal-trace",
    "--source-commit",
    "--source-tree",
    "--toolchains",
    "--vote-fixture",
}
RUNTIME_ID_FIELDS: Final = {
    "abi_sha256",
    "build_id",
    "formal_semantics_id",
    "protocol_sha256",
    "schema_set_id",
    "schema_sha256",
}
INITIAL_ARTIFACT_FIELDS: Final = {
    "initial_state_sha256",
    "snapshot_sha256",
    "wal_sha256",
}
REQUEST_FIELDS: Final = {"canonical_request_sha256", "ordinal", "request_id"}
TIMER_FIELDS: Final = {"ordinal", "timer_token_sha256"}
FIXED_RAW_FIELDS: Final = gate.FIXED_BLOCK_FIELDS | {
    "latency_ns",
    "offer_offset_ns",
    "phase_latency_ns",
}
SATURATION_RAW_FIELDS: Final = gate.SATURATION_BLOCK_FIELDS | {
    "admitted_operations",
    "cutoff_outcome",
    "offered_operations",
    "unadmitted_at_cutoff",
}
SATURATION_SCHEDULE_FIELDS: Final = {
    "block_count",
    "cycle_length",
    "evidence",
    "evidence_sha256",
    "max_in_flight",
    "offers_per_block",
    "replay_rule",
    "schema_version",
    "target_request_ids",
    "total_logical_offers",
    "type_name",
}
EVIDENCE_FIELDS: Final = {"artifact_sha256", "checks", "observations"}
MEASUREMENT_FIELDS: Final = {"evidence", "evidence_sha256", "measurement_id"}
COPY_COUNTER_FIELDS: Final = {"counter_id", "evidence", "evidence_sha256", "value"}
RESTART_FIELDS: Final = {"crash_point", "duration_ns", "evidence", "evidence_sha256"}
SURVIVAL_FIELDS: Final = {"evidence", "evidence_sha256", "survived_all_native_deaths"}
TRANSCRIPT_FIELDS: Final = {
    "equality_id",
    "evidence",
    "evidence_sha256",
    "transcript_sha256",
}
MANIFEST_FIELDS: Final = {
    "common_hard_gates",
    "crash_coverage",
    "design_canonical_id",
    "design_sha256",
    "execution_class",
    "formal_semantics_id",
    "schema_version",
    "sidecar_hard_gates",
    "type_name",
}
MANIFEST_GATE_FIELDS: Final = {"evidence", "evidence_sha256", "gate_id"}
CONFORMANCE_RECEIPT_TYPE: Final = "FEATURE010_SIDECAR_CONFORMANCE_RECEIPT"
CONFORMANCE_RECEIPT_FIELDS: Final = {
    "binary_sha256",
    "exit_code",
    "gate_id",
    "raw_log_sha256",
    "receipt_type",
    "source_commit",
    "source_tree",
    "test_id",
}
CONFORMANCE_TEST_IDS: Final = {
    "DESCRIPTOR_VERSION_AND_IDENTITY_MISMATCH_FAIL_CLOSED": (
        "io.deltareduce.node.sidecar.SidecarIpcConformance#descriptorIdentityMismatch"
    ),
    "FRAME_LENGTH_OFFSET_DIGEST_AND_RESERVED_BYTE_BOUNDS": (
        "io.deltareduce.node.sidecar.SidecarIpcConformance#frameMutationBounds"
    ),
    "BACKPRESSURE_REJECTS_ONLY_BEFORE_NATIVE_ADMISSION": (
        "io.deltareduce.node.sidecar.SidecarSupervisorConformance#boundedIngressBackpressure"
    ),
    "SHARED_MEMORY_OWNERSHIP_GENERATION_DIGEST_AND_COPY_EQUIVALENCE": (
        "io.deltareduce.node.sidecar.SidecarIpcConformance#sharedMemoryDisabledCopyEquivalence"
    ),
    "STALE_RESPONSE_FENCING": (
        "io.deltareduce.node.sidecar.SidecarSupervisorConformance#staleResponseFencing"
    ),
    "NETTY_EVENT_LOOP_NONBLOCKING": (
        "io.deltareduce.node.sidecar.SidecarSupervisorConformance#eventLoopNonblocking"
    ),
}
MANIFEST_CRASH_FIELDS: Final = {"paired", "sidecar_supplemental"}
PAIRED_CRASH_FIELDS: Final = {
    "crash_point",
    "embedded_evidence",
    "embedded_evidence_sha256",
    "sidecar_evidence",
    "sidecar_evidence_sha256",
}
SUPPLEMENTAL_CRASH_FIELDS: Final = {"crash_point", "evidence", "evidence_sha256"}
CRASH_OBSERVATION_FIELDS: Final = {
    "java_process_survived",
    "journal_recovered_before_admission",
    "partial_response_exposed",
    "persist_before_expose",
    "replay_identity_exact",
}
SHM_PUBLICATION_OBSERVATION_FIELDS: Final = {
    "atomic_abi_probe_result",
    "atomic_abi_probe_scope",
    "atomic_abi_supported",
    "bounded_copy_equivalence",
    "crash_process_exit_code",
    "duration_ns",
    "fallback_transport",
    "failed_generation_stdout_bytes_after_submit",
    "shared_memory_admission_state",
    "shared_memory_admitted_sequence",
    "shared_memory_admitted_sequence_derivation",
    "shared_memory_control_frame_exposed",
    "shared_memory_enabled",
    "shared_memory_ingress_bytes",
    "shared_memory_egress_bytes",
    "shared_memory_failed_generation_egress_control_bytes",
    "shared_memory_failed_generation_operation_response_wire_bytes",
    "shared_memory_failed_generation_response_carrier_count",
    "shared_memory_failed_generation_response_frame_count",
    "shared_memory_ingress_ack_frame_count",
    "shared_memory_native_call_count",
    "shared_memory_native_status",
    "shared_memory_notification_ack_inline_only",
    "shared_memory_operation_response_frame_exposed",
    "shared_memory_open_admitted_sequence",
    "shared_memory_publication_completed",
    "shared_memory_publication_started",
    "shared_memory_region_id",
    "shared_memory_slot_state_at_native_death",
    "shared_memory_status",
    "shared_memory_telemetry_scope",
    "validated_response_count_before_recovery",
    "zero_copy_eligible_count",
    "zero_copy_hit_count",
}
SHM_PUBLICATION_CHECKS: Final = {
    "FIRST_GENERATION_EXIT_CONFIRMED",
    "JAVA_PROCESS_SURVIVED_NATIVE_DEATH",
    "NO_VALIDATED_PARTIAL_RESPONSE_EXPOSED",
    "RECOVERY_READY_PRECEDED_RETRY",
    "RETRY_DURABLE_RESULT_MATCHED_REFERENCE",
    "SHARED_MEMORY_ATOMIC_ABI_PROBED",
    "SHARED_MEMORY_ADMISSION_SEQUENCE_DERIVED",
    "SHARED_MEMORY_NOTIFICATION_ACK_ONLY",
    "SHARED_MEMORY_OPERATION_RESPONSE_NOT_EXPOSED",
    "SHARED_MEMORY_PUBLICATION_NOT_EXPOSED",
    "SHARED_MEMORY_PUBLICATION_STARTED",
}


def require(condition: bool, code: str, detail: str = "") -> None:
    gate.require(condition, code, detail)


def exact_object(value: object, fields: set[str], code: str) -> dict[str, Any]:
    return gate.exact_object(value, fields, code)


def nonempty_text(value: object, code: str, *, maximum_utf8: int = 256) -> str:
    require(isinstance(value, str) and bool(value), code)
    encoded = value.encode("utf-8")
    require(len(encoded) <= maximum_utf8 and b"\x00" not in encoded, code)
    return value


def checked_multiply_u64(left: object, right: object, code: str) -> int:
    left_value = gate.strict_u64(left, code)
    right_value = gate.strict_u64(right, code)
    result = left_value * right_value
    require(result <= gate.U64_MAX, code)
    return result


def validate_json_value(value: object, code: str) -> None:
    if value is None or type(value) in {bool, str}:
        return
    if type(value) is int:
        gate.strict_u64(value, code)
        return
    if isinstance(value, list):
        for item in value:
            validate_json_value(item, code)
        return
    require(isinstance(value, dict), code)
    for key, item in value.items():
        nonempty_text(key, code)
        validate_json_value(item, code)


def validate_evidence_object(
    value: object,
    declared_sha256: object,
    code: str,
) -> tuple[dict[str, Any], bool, str]:
    evidence = exact_object(value, EVIDENCE_FIELDS, code)
    gate.content_id(evidence["artifact_sha256"], code)
    checks = evidence["checks"]
    require(isinstance(checks, dict) and bool(checks), code)
    for check_id, passed in checks.items():
        nonempty_text(check_id, code)
        require(type(passed) is bool, code)
    observations = evidence["observations"]
    require(isinstance(observations, dict) and bool(observations), code)
    validate_json_value(observations, code)
    actual_sha256 = gate.sha256_id(gate.canonical_bytes(evidence))
    require(gate.content_id(declared_sha256, code) == actual_sha256, f"{code}_SHA256")
    return evidence, all(checks.values()), actual_sha256


def require_observations(
    evidence: dict[str, Any],
    expected: dict[str, object],
    code: str,
) -> None:
    observations = evidence["observations"]
    for field, expected_value in expected.items():
        require(observations.get(field) == expected_value, code, field)


def validate_headers(document: dict[str, Any], expected_type: str, code: str) -> None:
    require(document["type_name"] == expected_type, f"{code}_TYPE")
    require(document["schema_version"] == "1.0.0", f"{code}_SCHEMA")
    require(document["execution_class"] == EXECUTION_CLASS, f"{code}_EXECUTION_CLASS")
    require(document["formal_semantics_id"] == gate.FORMAL_ID, f"{code}_FORMAL_ID")
    require(document["design_sha256"] == gate.EXPECTED_DESIGN_SHA256, f"{code}_DESIGN_SHA256")
    require(
        document["design_canonical_id"] == gate.EXPECTED_DESIGN_CANONICAL_ID,
        f"{code}_DESIGN_CANONICAL_ID",
    )


def utc_instant(value: object, code: str) -> datetime:
    timestamp = nonempty_text(value, code)
    require(timestamp.endswith("Z"), code)
    try:
        parsed = datetime.fromisoformat(timestamp[:-1] + "+00:00")
    except ValueError as error:
        raise gate.ComparisonError(code) from error
    require(parsed.utcoffset() is not None and parsed.utcoffset().total_seconds() == 0, code)
    return parsed


def text_array(value: object, code: str, *, nonempty: bool = False) -> list[str]:
    require(isinstance(value, list) and (bool(value) or not nonempty), code)
    return [nonempty_text(item, code, maximum_utf8=4096) for item in value]


def provenance_file_record(
    value: object,
    fields: set[str],
    id_field: str,
    expected_id: str,
    code: str,
) -> dict[str, Any]:
    record = exact_object(value, fields, code)
    require(record[id_field] == expected_id, code)
    nonempty_text(record["path"], code, maximum_utf8=4096)
    gate.content_id(record["sha256"], code)
    gate.strict_u64(record["size_bytes"], code)
    return record


def validate_input_provenance(
    run: dict[str, Any],
    *,
    crash_artifact_sha256: str,
) -> str:
    provenance = exact_object(run["input_provenance"], PROVENANCE_FIELDS, "INPUT_PROVENANCE_FIELDS")
    require(
        provenance["type_name"] == "FEATURE010_CAPTURE_INPUT_PROVENANCE",
        "INPUT_PROVENANCE_TYPE",
    )
    require(provenance["schema_version"] == "1.0.0", "INPUT_PROVENANCE_SCHEMA")
    provenance_sha256 = gate.sha256_id(gate.canonical_bytes(provenance))
    require(
        gate.content_id(run["input_provenance_sha256"], "INPUT_PROVENANCE_SHA256")
        == provenance_sha256,
        "INPUT_PROVENANCE_SHA256",
    )

    source = exact_object(provenance["source"], PROVENANCE_SOURCE_FIELDS, "INPUT_PROVENANCE_SOURCE")
    require(source["commit"] == run["source"]["commit"], "INPUT_PROVENANCE_COMMIT")
    require(source["tree"] == run["source"]["tree"], "INPUT_PROVENANCE_TREE")
    require(source["tracked_clean"] is True, "INPUT_PROVENANCE_TRACKED_CLEAN")

    plan = exact_object(provenance["capture_plan"], CAPTURE_PLAN_FIELDS, "CAPTURE_PLAN_FIELDS")
    require(plan["profile_id"] == run["profile_id"], "CAPTURE_PLAN_PROFILE")
    output_path = nonempty_text(plan["output_path"], "CAPTURE_PLAN_OUTPUT", maximum_utf8=4096)
    argv = text_array(plan["argv"], "CAPTURE_PLAN_ARGV", nonempty=True)
    require(len(argv) % 2 == 0, "CAPTURE_PLAN_ARGV")
    arguments: dict[str, str] = {}
    for index in range(0, len(argv), 2):
        name = argv[index]
        require(name.startswith("--") and name not in arguments, "CAPTURE_PLAN_ARGV")
        arguments[name] = argv[index + 1]
    native_option = (
        "--native-library" if run["profile_id"] == "EMBEDDED_FFM" else "--sidecar-executable"
    )
    require(set(arguments) == CAPTURE_OPTION_NAMES | {native_option}, "CAPTURE_PLAN_ARGV_OPTIONS")
    require(arguments["--profile"] == run["profile_id"], "CAPTURE_PLAN_ARGV_PROFILE")
    require(arguments["--output"] == output_path, "CAPTURE_PLAN_ARGV_OUTPUT")
    require(arguments["--source-commit"] == source["commit"], "CAPTURE_PLAN_ARGV_COMMIT")
    require(arguments["--source-tree"] == source["tree"], "CAPTURE_PLAN_ARGV_TREE")

    expected_artifact_ids = [
        "CORPUS",
        "CRASH_OBSERVATIONS",
        "FROZEN_DESIGN",
        "HARDWARE_ALLOCATION",
        "NATIVE_CORE",
        "PAIRED_CORE_FAULT_TRACE",
        "PROJECTED_FORMAL_TRACE",
        "TOOLCHAINS",
        "VOTE_FIXTURE",
        "NATIVE_LIBRARY" if run["profile_id"] == "EMBEDDED_FFM" else "SIDECAR_EXECUTABLE",
    ]
    input_artifacts = provenance["input_artifacts"]
    require(
        isinstance(input_artifacts, list) and len(input_artifacts) == len(expected_artifact_ids),
        "INPUT_ARTIFACT_COUNT",
    )
    artifacts: dict[str, dict[str, Any]] = {}
    for index, artifact_id in enumerate(expected_artifact_ids):
        artifacts[artifact_id] = provenance_file_record(
            input_artifacts[index],
            INPUT_ARTIFACT_FIELDS,
            "artifact_id",
            artifact_id,
            "INPUT_ARTIFACT_FIELDS",
        )
    require(
        artifacts["VOTE_FIXTURE"]["size_bytes"] > 0
        and artifacts["VOTE_FIXTURE"]["sha256"] != EMPTY_SHA256,
        "VOTE_FIXTURE_EMPTY",
    )

    artifact_bindings = {
        "CORPUS": ("--corpus", run["canonical_input_trace_sha256"]),
        "CRASH_OBSERVATIONS": ("--crash-observations", crash_artifact_sha256),
        "FROZEN_DESIGN": ("--design", run["design_sha256"]),
        "HARDWARE_ALLOCATION": ("--hardware-allocation", run["hardware_allocation_sha256"]),
        "NATIVE_CORE": ("--native-core", run["native_core_sha256"]),
        "PAIRED_CORE_FAULT_TRACE": ("--fault-trace", run["fault_trace_sha256"]),
        "PROJECTED_FORMAL_TRACE": ("--projected-formal-trace", None),
        "TOOLCHAINS": ("--toolchains", run["toolchains_sha256"]),
        "VOTE_FIXTURE": ("--vote-fixture", None),
        expected_artifact_ids[-1]: (native_option, None),
    }
    for artifact_id, (option, expected_sha256) in artifact_bindings.items():
        record = artifacts[artifact_id]
        require(arguments[option] == record["path"], "INPUT_ARTIFACT_ARGV_PATH", artifact_id)
        if expected_sha256 is not None:
            require(record["sha256"] == expected_sha256, "INPUT_ARTIFACT_BINDING", artifact_id)

    hardware = exact_object(
        provenance["hardware_identity"], HARDWARE_IDENTITY_FIELDS, "HARDWARE_IDENTITY_FIELDS"
    )
    require(
        hardware["allocation_artifact_sha256"] == artifacts["HARDWARE_ALLOCATION"]["sha256"],
        "HARDWARE_ALLOCATION_BINDING",
    )
    gate.strict_u64(
        hardware["available_processors"],
        "HARDWARE_AVAILABLE_PROCESSORS",
        positive=True,
    )
    for field in ("os_arch", "os_name", "os_version"):
        nonempty_text(hardware[field], "HARDWARE_IDENTITY", maximum_utf8=256)

    tools_value = provenance["tools"]
    expected_tool_ids = ["GIT", "JAVA_RUNTIME", "NATIVE_RUNTIME"]
    require(
        isinstance(tools_value, list) and len(tools_value) == len(expected_tool_ids),
        "TOOL_IDENTITY_COUNT",
    )
    tools: dict[str, dict[str, Any]] = {}
    for index, tool_id in enumerate(expected_tool_ids):
        tool = provenance_file_record(
            tools_value[index], TOOL_IDENTITY_FIELDS, "tool_id", tool_id, "TOOL_IDENTITY_FIELDS"
        )
        nonempty_text(tool["version"], "TOOL_VERSION", maximum_utf8=256)
        tools[tool_id] = tool
    native_artifact = artifacts[expected_artifact_ids[-1]]
    require(
        {
            "path": tools["NATIVE_RUNTIME"]["path"],
            "sha256": tools["NATIVE_RUNTIME"]["sha256"],
            "size_bytes": tools["NATIVE_RUNTIME"]["size_bytes"],
        }
        == {
            "path": native_artifact["path"],
            "sha256": native_artifact["sha256"],
            "size_bytes": native_artifact["size_bytes"],
        },
        "NATIVE_TOOL_ARTIFACT_BINDING",
    )

    preparation_started = utc_instant(
        provenance["preparation_started_at_utc"], "PREPARATION_STARTED_AT"
    )
    preparation_ended = utc_instant(provenance["preparation_ended_at_utc"], "PREPARATION_ENDED_AT")
    require(preparation_started <= preparation_ended, "PREPARATION_INTERVAL")
    runner_values = provenance["runner_logs"]
    require(isinstance(runner_values, list) and bool(runner_values), "RUNNER_LOG_COUNT")
    runners: list[dict[str, Any]] = []
    runner_ids: set[str] = set()
    for value in runner_values:
        runner = exact_object(value, RUNNER_LOG_FIELDS, "RUNNER_LOG_FIELDS")
        runner_id = nonempty_text(runner["runner_id"], "RUNNER_ID")
        require(runner_id not in runner_ids, "RUNNER_ID_DUPLICATE")
        runner_ids.add(runner_id)
        tool_id = nonempty_text(runner["tool_id"], "RUNNER_TOOL_ID")
        require(tool_id in tools, "RUNNER_TOOL_ID")
        nonempty_text(runner["path"], "RUNNER_LOG_PATH", maximum_utf8=4096)
        gate.content_id(runner["sha256"], "RUNNER_LOG_SHA256")
        gate.strict_u64(runner["size_bytes"], "RUNNER_LOG_SIZE")
        text_array(runner["argv"], "RUNNER_ARGV", nonempty=True)
        started = utc_instant(runner["started_at_utc"], "RUNNER_STARTED_AT")
        ended = utc_instant(runner["ended_at_utc"], "RUNNER_ENDED_AT")
        require(
            preparation_started <= started <= ended <= preparation_ended,
            "RUNNER_INTERVAL",
        )
        runners.append(runner)

    expected_nodes: list[dict[str, object]] = []
    for artifact_id in expected_artifact_ids:
        record = artifacts[artifact_id]
        expected_nodes.append(
            {
                "artifact_sha256": record["sha256"],
                "node_id": f"INPUT:{artifact_id}",
                "provenance_sha256": provenance_sha256,
                "size_bytes": record["size_bytes"],
            }
        )
    for tool_id in expected_tool_ids:
        record = tools[tool_id]
        expected_nodes.append(
            {
                "artifact_sha256": record["sha256"],
                "node_id": f"TOOL:{tool_id}",
                "provenance_sha256": provenance_sha256,
                "size_bytes": record["size_bytes"],
            }
        )
    for runner in runners:
        expected_nodes.append(
            {
                "artifact_sha256": runner["sha256"],
                "node_id": f"RUNNER_LOG:{runner['runner_id']}",
                "provenance_sha256": provenance_sha256,
                "size_bytes": runner["size_bytes"],
            }
        )
    graph_nodes = run["input_graph_nodes"]
    require(
        isinstance(graph_nodes, list) and len(graph_nodes) == len(expected_nodes),
        "INPUT_GRAPH_NODE_COUNT",
    )
    for index, expected in enumerate(expected_nodes):
        node = exact_object(graph_nodes[index], INPUT_GRAPH_NODE_FIELDS, "INPUT_GRAPH_NODE_FIELDS")
        gate.content_id(node["artifact_sha256"], "INPUT_GRAPH_NODE_SHA256")
        gate.content_id(node["provenance_sha256"], "INPUT_GRAPH_PROVENANCE_SHA256")
        gate.strict_u64(node["size_bytes"], "INPUT_GRAPH_NODE_SIZE")
        require(node == expected, "INPUT_GRAPH_NODE_BINDING")
    return provenance_sha256


def ordered_unique_strings(value: object, code: str) -> list[str]:
    require(isinstance(value, list), code)
    result: list[str] = []
    for item in value:
        result.append(nonempty_text(item, code))
    require(len(result) == len(set(result)), code)
    return result


def validate_design_shape(design: dict[str, Any], *, production: bool) -> None:
    comparison = design.get("comparison_plan")
    require(isinstance(comparison, dict), "DESIGN_COMPARISON_PLAN")
    require(comparison.get("profiles") == ["EMBEDDED_FFM", "ISOLATED_SIDECAR"], "DESIGN_PROFILES")
    for field in (
        "copy_accounting",
        "exact_cross_profile_equalities",
        "hard_gates_common",
        "hard_gates_sidecar",
        "identical_pair_fields",
        "paired_crash_points",
        "required_measurements",
        "sidecar_supplemental_crash_points",
    ):
        ordered_unique_strings(comparison.get(field), f"DESIGN_{field.upper()}")
    aggregation = comparison.get("aggregation")
    require(isinstance(aggregation, dict), "DESIGN_AGGREGATION")
    require(aggregation.get("latency_percentiles") == [50, 95, 99], "DESIGN_PERCENTILES")
    if production:
        fixed_total = checked_multiply_u64(
            aggregation.get("measured_blocks"),
            aggregation.get("fixed_load_offered_operations_per_block"),
            "DESIGN_FIXED_TOTAL",
        )
        require(fixed_total == 60_000, "FROZEN_FIXED_SAMPLE_COUNT")


def validate_order_records(value: object, *, timer: bool) -> list[dict[str, Any]]:
    code = "TIMER_ORDER" if timer else "REQUEST_ORDER"
    fields = TIMER_FIELDS if timer else REQUEST_FIELDS
    require(isinstance(value, list), code)
    result: list[dict[str, Any]] = []
    request_bindings: dict[str, str] = {}
    for index, item in enumerate(value):
        record = exact_object(item, fields, code)
        require(gate.strict_u64(record["ordinal"], code) == index, code)
        if timer:
            gate.content_id(record["timer_token_sha256"], code)
        else:
            request_id = nonempty_text(record["request_id"], code)
            request_sha256 = gate.content_id(record["canonical_request_sha256"], code)
            previous = request_bindings.setdefault(request_id, request_sha256)
            require(previous == request_sha256, "REQUEST_ID_BODY_CONFLICT")
        result.append(record)
    return result


def validate_saturation_schedule(
    value: object,
    request_order: list[dict[str, Any]],
    aggregation: dict[str, Any],
) -> dict[str, Any]:
    schedule = exact_object(value, SATURATION_SCHEDULE_FIELDS, "SATURATION_SCHEDULE_FIELDS")
    require(
        schedule["type_name"] == "FEATURE010_SATURATION_REPLAY_SCHEDULE",
        "SATURATION_SCHEDULE_TYPE",
    )
    require(schedule["schema_version"] == "1.0.0", "SATURATION_SCHEDULE_SCHEMA")
    fixed_blocks = gate.strict_u64(
        aggregation["measured_blocks"], "SATURATION_SCHEDULE_BLOCKS", positive=True
    )
    fixed_per_block = gate.strict_u64(
        aggregation["fixed_load_offered_operations_per_block"],
        "SATURATION_SCHEDULE_FIXED_OPERATIONS",
        positive=True,
    )
    warmup = gate.strict_u64(
        aggregation["warmup_operations"], "SATURATION_SCHEDULE_WARMUP", positive=True
    )
    saturation_blocks = gate.strict_u64(
        aggregation["saturation_blocks"], "SATURATION_SCHEDULE_BLOCKS", positive=True
    )
    require(
        gate.strict_u64(schedule["block_count"], "SATURATION_SCHEDULE_BLOCKS") == saturation_blocks,
        "SATURATION_SCHEDULE_BLOCKS",
    )
    require(
        gate.strict_u64(schedule["offers_per_block"], "SATURATION_SCHEDULE_OFFERS")
        == SATURATION_OFFERS_PER_BLOCK,
        "SATURATION_SCHEDULE_OFFERS",
    )
    require(
        gate.strict_u64(schedule["max_in_flight"], "SATURATION_SCHEDULE_IN_FLIGHT") == 64,
        "SATURATION_SCHEDULE_IN_FLIGHT",
    )
    expected_total = checked_multiply_u64(
        saturation_blocks, SATURATION_OFFERS_PER_BLOCK, "SATURATION_SCHEDULE_TOTAL"
    )
    require(
        gate.strict_u64(schedule["total_logical_offers"], "SATURATION_SCHEDULE_TOTAL")
        == expected_total,
        "SATURATION_SCHEDULE_TOTAL",
    )
    expected_rule = (
        "FINITE_RLE_CYCLE_FIXED_BLOCK_TERMINAL_REQUESTS_THEN_HARNESS_CUTOFF_PRE_ADMISSION"
    )
    require(schedule["replay_rule"] == expected_rule, "SATURATION_SCHEDULE_RULE")
    targets = ordered_unique_strings(schedule["target_request_ids"], "SATURATION_SCHEDULE_TARGETS")
    require(len(targets) == fixed_blocks, "SATURATION_SCHEDULE_TARGET_COUNT")
    require(
        gate.strict_u64(schedule["cycle_length"], "SATURATION_SCHEDULE_CYCLE") == len(targets),
        "SATURATION_SCHEDULE_CYCLE",
    )
    expected_targets: list[str] = []
    for block in range(fixed_blocks):
        ordinal = warmup + ((block + 1) * fixed_per_block) - 1
        require(ordinal < len(request_order), "SATURATION_SCHEDULE_TARGET_RANGE")
        expected_targets.append(request_order[ordinal]["request_id"])
    require(targets == expected_targets, "SATURATION_SCHEDULE_TARGET_ORDER")

    core = {
        key: item for key, item in schedule.items() if key not in {"evidence", "evidence_sha256"}
    }
    artifact_sha256 = gate.sha256_id(gate.canonical_bytes(core))
    evidence, passed, _ = validate_evidence_object(
        schedule["evidence"], schedule["evidence_sha256"], "SATURATION_SCHEDULE_EVIDENCE"
    )
    require(passed, "SATURATION_SCHEDULE_CHECK_FAILED")
    require(
        evidence["checks"] == {"PREDECLARED_IDENTICAL_REPLAY_STREAM": True},
        "SATURATION_SCHEDULE_CHECK",
    )
    require(evidence["artifact_sha256"] == artifact_sha256, "SATURATION_SCHEDULE_ARTIFACT")
    require_observations(
        evidence,
        {
            "cycle_length": len(targets),
            "max_in_flight": 64,
            "offers_per_block": SATURATION_OFFERS_PER_BLOCK,
            "replay_rule": expected_rule,
            "target_request_ids_sha256": gate.sha256_id(gate.canonical_bytes(targets)),
        },
        "SATURATION_SCHEDULE_OBSERVATION",
    )
    return schedule


def validate_measurements(
    value: object,
    expected_ids: list[str],
    profile: str,
    expectations: dict[str, tuple[str, str, dict[str, object]]],
) -> list[dict[str, Any]]:
    require(isinstance(value, list) and len(value) == len(expected_ids), "RAW_MEASUREMENTS")
    require(list(expectations) == expected_ids, "RAW_MEASUREMENT_EXPECTATIONS")
    compact: list[dict[str, Any]] = []
    for index, measurement_id in enumerate(expected_ids):
        record = exact_object(value[index], MEASUREMENT_FIELDS, "RAW_MEASUREMENT_FIELDS")
        require(record["measurement_id"] == measurement_id, "RAW_MEASUREMENT_ORDER", profile)
        evidence, passed, evidence_sha256 = validate_evidence_object(
            record["evidence"], record["evidence_sha256"], "RAW_MEASUREMENT_EVIDENCE"
        )
        artifact_sha256, check_id, observations = expectations[measurement_id]
        require(
            evidence["artifact_sha256"] == artifact_sha256,
            "RAW_MEASUREMENT_ARTIFACT",
            measurement_id,
        )
        require(
            set(evidence["checks"]) == {check_id},
            "RAW_MEASUREMENT_CHECK",
            measurement_id,
        )
        require(
            evidence["observations"] == observations,
            "RAW_MEASUREMENT_OBSERVATION",
            measurement_id,
        )
        compact.append(
            {
                "evidence_sha256": evidence_sha256,
                "measurement_id": measurement_id,
                "status": "PRESENT" if passed else "MISSING",
            }
        )
    return compact


def nearest_rank(values: list[int], percentile: int) -> int:
    require(bool(values), "LATENCY_POPULATION_EMPTY")
    require(1 <= percentile <= 100, "LATENCY_PERCENTILE")
    ordered = sorted(values)
    rank = (percentile * len(ordered) + 99) // 100
    return ordered[rank - 1]


def validate_blocks(
    run: dict[str, Any],
    aggregation: dict[str, Any],
    *,
    production: bool,
) -> tuple[
    list[dict[str, int]],
    list[dict[str, int]],
    dict[str, int],
    dict[str, int],
    int,
    dict[str, Any],
]:
    fixed_count = gate.strict_u64(
        aggregation["measured_blocks"], "DESIGN_FIXED_BLOCKS", positive=True
    )
    offered = gate.strict_u64(
        aggregation["fixed_load_offered_operations_per_block"],
        "DESIGN_FIXED_OFFERED",
        positive=True,
    )
    rate = gate.strict_u64(
        aggregation["fixed_offered_load_ops_per_second"], "DESIGN_FIXED_RATE", positive=True
    )
    window = gate.strict_u64(
        aggregation["throughput_window_seconds"], "DESIGN_WINDOW", positive=True
    )
    require(
        checked_multiply_u64(rate, window, "FIXED_SCHEDULE_PRODUCT") == offered, "FIXED_SCHEDULE"
    )
    require(1_000_000_000 % rate == 0, "FIXED_RATE_NANOSECOND_INTERVAL")
    offer_interval_ns = 1_000_000_000 // rate
    window_ns = checked_multiply_u64(window, 1_000_000_000, "FIXED_WINDOW_NS")
    fixed = run["fixed_load_blocks"]
    require(isinstance(fixed, list) and len(fixed) == fixed_count, "RAW_FIXED_BLOCK_COUNT")
    compact_fixed: list[dict[str, int]] = []
    latencies: list[int] = []
    phase_latencies: list[int] = []
    schedule_fixed: list[dict[str, int]] = []
    for index, item in enumerate(fixed):
        block = exact_object(item, FIXED_RAW_FIELDS, "RAW_FIXED_BLOCK_FIELDS")
        require(
            gate.strict_u64(block["block_index"], "RAW_FIXED_BLOCK_INDEX") == index,
            "RAW_FIXED_BLOCK_ORDER",
        )
        require(
            gate.strict_u64(block["offered_operations"], "RAW_FIXED_OFFERED") == offered,
            "RAW_FIXED_OFFERED",
        )
        require(
            gate.strict_u64(block["completed_operations"], "RAW_FIXED_COMPLETED") == offered,
            "RAW_FIXED_INCOMPLETE",
        )
        require(
            gate.strict_u64(block["offered_ops_per_second"], "RAW_FIXED_RATE") == rate,
            "RAW_FIXED_RATE",
        )
        require(
            gate.strict_u64(block["window_seconds"], "RAW_FIXED_WINDOW") == window,
            "RAW_FIXED_WINDOW",
        )
        block_latencies = block["latency_ns"]
        block_offer_offsets = block["offer_offset_ns"]
        block_phases = block["phase_latency_ns"]
        require(
            isinstance(block_latencies, list) and len(block_latencies) == offered,
            "RAW_LATENCY_BLOCK_COUNT",
        )
        require(
            isinstance(block_phases, list) and len(block_phases) == offered, "RAW_PHASE_BLOCK_COUNT"
        )
        require(
            isinstance(block_offer_offsets, list) and len(block_offer_offsets) == offered,
            "RAW_OFFER_BLOCK_COUNT",
        )
        for operation_index, offset_value in enumerate(block_offer_offsets):
            offset = gate.strict_u64(offset_value, "RAW_OFFER_OFFSET")
            require(offset < window_ns, "RAW_OFFER_OUTSIDE_WINDOW")
            target = operation_index * offer_interval_ns
            require(offset >= target, "RAW_OFFER_PRECEDES_SLOT")
            require(offset - target < offer_interval_ns, "RAW_OFFER_MISSED_SLOT")
        latencies.extend(
            gate.strict_u64(value, "RAW_LATENCY_SAMPLE", positive=True) for value in block_latencies
        )
        phase_latencies.extend(
            gate.strict_u64(value, "RAW_PHASE_SAMPLE", positive=True) for value in block_phases
        )
        compact_fixed.append(
            {
                "block_index": index,
                "completed_operations": offered,
                "offered_operations": offered,
                "offered_ops_per_second": rate,
                "window_seconds": window,
            }
        )
        schedule_fixed.append(
            {
                "block_index": index,
                "offered_operations": offered,
                "offered_ops_per_second": rate,
                "window_seconds": window,
            }
        )

    expected_fixed_total = checked_multiply_u64(fixed_count, offered, "FIXED_TOTAL_OVERFLOW")
    require(len(latencies) == expected_fixed_total, "RAW_LATENCY_TOTAL")
    require(len(phase_latencies) == expected_fixed_total, "RAW_PHASE_TOTAL")
    if production:
        require(expected_fixed_total == 60_000, "FROZEN_FIXED_SAMPLE_COUNT")

    percentiles = {
        f"p{percentile}": nearest_rank(latencies, percentile)
        for percentile in aggregation["latency_percentiles"]
    }
    percentiles["sample_count"] = len(latencies)
    phase_percentiles = {
        f"p{percentile}": nearest_rank(phase_latencies, percentile)
        for percentile in aggregation["latency_percentiles"]
    }
    phase_percentiles["sample_count"] = len(phase_latencies)

    saturation_count = gate.strict_u64(
        aggregation["saturation_blocks"], "DESIGN_SATURATION_BLOCKS", positive=True
    )
    saturation = run["saturation_blocks"]
    require(
        isinstance(saturation, list) and len(saturation) == saturation_count,
        "RAW_SATURATION_BLOCK_COUNT",
    )
    compact_saturation: list[dict[str, int]] = []
    schedule_saturation: list[dict[str, int]] = []
    saturation_total = 0
    for index, item in enumerate(saturation):
        block = exact_object(item, SATURATION_RAW_FIELDS, "RAW_SATURATION_BLOCK_FIELDS")
        require(
            gate.strict_u64(block["block_index"], "RAW_SATURATION_BLOCK_INDEX") == index,
            "RAW_SATURATION_BLOCK_ORDER",
        )
        completed = gate.strict_u64(
            block["completed_operations"], "RAW_SATURATION_COMPLETED", positive=True
        )
        admitted = gate.strict_u64(
            block["admitted_operations"], "RAW_SATURATION_ADMITTED", positive=True
        )
        offered = gate.strict_u64(
            block["offered_operations"], "RAW_SATURATION_OFFERED", positive=True
        )
        unadmitted = gate.strict_u64(
            block["unadmitted_at_cutoff"], "RAW_SATURATION_UNADMITTED", positive=True
        )
        require(offered == SATURATION_OFFERS_PER_BLOCK, "RAW_SATURATION_OFFERED")
        require(admitted <= offered, "RAW_SATURATION_ADMITTED")
        require(completed <= admitted, "RAW_SATURATION_COMPLETED")
        require(admitted - completed <= 64, "RAW_SATURATION_BOUNDED_COMPLETION")
        require(unadmitted == offered - admitted, "RAW_SATURATION_CUTOFF_ACCOUNTING")
        require(
            block["cutoff_outcome"] == "HARNESS_CUTOFF_PRE_ADMISSION",
            "RAW_SATURATION_CUTOFF_OUTCOME",
        )
        require(
            gate.strict_u64(block["window_seconds"], "RAW_SATURATION_WINDOW") == window,
            "RAW_SATURATION_WINDOW",
        )
        saturation_total = gate.checked_add_u64(
            saturation_total, completed, "SATURATION_TOTAL_OVERFLOW"
        )
        compact_saturation.append(
            {"block_index": index, "completed_operations": completed, "window_seconds": window}
        )
        schedule_saturation.append({"block_index": index, "window_seconds": window})

    schedule = {"fixed_load": schedule_fixed, "saturation": schedule_saturation}
    return (
        compact_fixed,
        compact_saturation,
        percentiles,
        phase_percentiles,
        saturation_total,
        schedule,
    )


def validate_copy_ledger(
    run: dict[str, Any],
    copy_ids: list[str],
    measured_operations: int,
) -> tuple[list[dict[str, int | str]], dict[str, int | str]]:
    samples = run["operation_copy_samples"]
    require(isinstance(samples, list) and len(samples) == measured_operations, "COPY_SAMPLE_COUNT")
    totals = {counter_id: 0 for counter_id in copy_ids}
    operation_ids: set[str] = set()
    maximum = -1
    maximum_ingress = 0
    maximum_egress = 0
    maximum_operation = ""
    sample_fields = {"operation_id", *copy_ids}
    for sample in samples:
        record = exact_object(sample, sample_fields, "COPY_SAMPLE_FIELDS")
        operation_id = nonempty_text(record["operation_id"], "COPY_OPERATION_ID")
        require(operation_id not in operation_ids, "COPY_OPERATION_ID_DUPLICATE")
        operation_ids.add(operation_id)
        for counter_id in copy_ids:
            value = gate.strict_u64(record[counter_id], "COPY_SAMPLE_VALUE")
            if counter_id in {"ZERO_COPY_ELIGIBLE_COUNT", "ZERO_COPY_HIT_COUNT"}:
                require(value in {0, 1}, "COPY_SAMPLE_BOOLEAN_COUNTER")
            totals[counter_id] = gate.checked_add_u64(
                totals[counter_id], value, "COPY_COUNTER_OVERFLOW"
            )
        require(
            record["ZERO_COPY_HIT_COUNT"] <= record["ZERO_COPY_ELIGIBLE_COUNT"],
            "COPY_SAMPLE_ZERO_COPY_RELATION",
        )
        require(
            record["ZERO_COPY_HIT_COUNT"] == 0,
            "COPY_SAMPLE_ZERO_COPY_HIT_FORBIDDEN",
        )
        ingress = record["STAGING_FALLBACK_INGRESS_BYTES"]
        egress = record["STAGING_FALLBACK_EGRESS_BYTES"]
        combined = gate.checked_add_u64(ingress, egress, "COPY_SAMPLE_FALLBACK_OVERFLOW")
        if combined > maximum:
            maximum = combined
            maximum_ingress = ingress
            maximum_egress = egress
            maximum_operation = operation_id

    counters = run["copy_accounting"]
    require(isinstance(counters, list) and len(counters) == len(copy_ids), "RAW_COPY_COUNTERS")
    totals_artifact = gate.sha256_id(gate.canonical_bytes(totals))
    compact: list[dict[str, int | str]] = []
    for index, counter_id in enumerate(copy_ids):
        record = exact_object(counters[index], COPY_COUNTER_FIELDS, "RAW_COPY_COUNTER_FIELDS")
        require(record["counter_id"] == counter_id, "RAW_COPY_COUNTER_ORDER")
        value = gate.strict_u64(record["value"], "RAW_COPY_COUNTER_VALUE")
        require(value == totals[counter_id], "RAW_COPY_COUNTER_SUM", counter_id)
        evidence, passed, _ = validate_evidence_object(
            record["evidence"], record["evidence_sha256"], "RAW_COPY_COUNTER_EVIDENCE"
        )
        require(passed, "RAW_COPY_COUNTER_CHECK_FAILED", counter_id)
        require(evidence["artifact_sha256"] == totals_artifact, "RAW_COPY_COUNTER_ARTIFACT")
        require(
            evidence["checks"] == {"COUNTER_SUM_MATCHES_OPERATION_SAMPLES": True},
            "RAW_COPY_COUNTER_CHECK",
        )
        require(
            evidence["observations"]
            == {
                "counter_id": counter_id,
                "profile_id": run["profile_id"],
                "value": value,
            },
            "RAW_COPY_COUNTER_OBSERVATION",
        )
        compact.append({"counter_id": counter_id, "value": value})

    require(maximum >= 0, "COPY_SAMPLE_COUNT")
    fallback: dict[str, int | str] = {
        "egress_bytes": maximum_egress,
        "ingress_bytes": maximum_ingress,
        "operation_count_scanned": measured_operations,
        "operation_id": maximum_operation,
        "total_bytes": maximum,
    }
    return compact, fallback


def validate_restarts(
    value: object,
    expected_points: list[str],
    profile: str,
) -> list[int]:
    require(isinstance(value, list) and len(value) == len(expected_points), "RAW_RESTART_COUNT")
    result: list[int] = []
    for index, crash_point in enumerate(expected_points):
        record = exact_object(value[index], RESTART_FIELDS, "RAW_RESTART_FIELDS")
        require(record["crash_point"] == crash_point, "RAW_RESTART_ORDER", profile)
        duration = gate.strict_u64(record["duration_ns"], "RAW_RESTART_DURATION", positive=True)
        evidence, passed, _ = validate_evidence_object(
            record["evidence"], record["evidence_sha256"], "RAW_RESTART_EVIDENCE"
        )
        require(passed, "RAW_RESTART_CHECK_FAILED", crash_point)
        require_observations(
            evidence,
            {"crash_point": crash_point, "duration_ns": duration, "profile_id": profile},
            "RAW_RESTART_OBSERVATION",
        )
        result.append(duration)
    return result


def validate_transcripts(
    value: object,
    expected_ids: list[str],
    profile: str,
) -> dict[str, dict[str, str]]:
    require(isinstance(value, list) and len(value) == len(expected_ids), "RAW_TRANSCRIPTS")
    result: dict[str, dict[str, str]] = {}
    for index, equality_id in enumerate(expected_ids):
        record = exact_object(value[index], TRANSCRIPT_FIELDS, "RAW_TRANSCRIPT_FIELDS")
        require(record["equality_id"] == equality_id, "RAW_TRANSCRIPT_ORDER", profile)
        transcript_sha256 = gate.content_id(record["transcript_sha256"], "RAW_TRANSCRIPT_SHA256")
        if equality_id == "CANONICAL_VOTE_RECEIPT_BYTES":
            require(
                transcript_sha256 != EMPTY_SHA256,
                "RAW_VOTE_RECEIPT_TRANSCRIPT_EMPTY",
                profile,
            )
        evidence, passed, evidence_sha256 = validate_evidence_object(
            record["evidence"], record["evidence_sha256"], "RAW_TRANSCRIPT_EVIDENCE"
        )
        require(passed, "RAW_TRANSCRIPT_CHECK_FAILED", equality_id)
        require(
            evidence["artifact_sha256"] == transcript_sha256,
            "RAW_TRANSCRIPT_ARTIFACT",
            equality_id,
        )
        require(
            evidence["checks"] == {"CONCRETE_TRANSCRIPT_HASHED": True},
            "RAW_TRANSCRIPT_CHECK",
            equality_id,
        )
        require(
            evidence["observations"]
            == {
                "equality_id": equality_id,
                "profile_id": profile,
                "transcript_sha256": transcript_sha256,
            },
            "RAW_TRANSCRIPT_OBSERVATION",
        )
        result[equality_id] = {
            "evidence_sha256": evidence_sha256,
            "transcript_sha256": transcript_sha256,
        }
    return result


def validate_run(
    value: object,
    expected_profile: str,
    design: dict[str, Any],
    *,
    production: bool,
) -> dict[str, Any]:
    run = exact_object(value, RUN_FIELDS, "RAW_RUN_FIELDS")
    validate_headers(run, RUN_TYPE, "RAW_RUN")
    require(run["profile_id"] == expected_profile, "RAW_PROFILE_ID", expected_profile)
    comparison = design["comparison_plan"]
    aggregation = comparison["aggregation"]
    require(run["aggregation_rules"] == aggregation, "RAW_AGGREGATION_RULES")
    require(run["bounds"] == design["ipc_contract"]["bounds"], "RAW_FROZEN_BOUNDS")

    source = exact_object(run["source"], SOURCE_FIELDS, "RAW_SOURCE")
    require(
        isinstance(source["commit"], str) and GIT_OBJECT.fullmatch(source["commit"]) is not None,
        "RAW_SOURCE_COMMIT",
    )
    require(
        isinstance(source["tree"], str) and GIT_OBJECT.fullmatch(source["tree"]) is not None,
        "RAW_SOURCE_TREE",
    )
    runtime_ids = exact_object(run["runtime_ids"], RUNTIME_ID_FIELDS, "RAW_RUNTIME_IDS")
    require(runtime_ids["formal_semantics_id"] == gate.FORMAL_ID, "RAW_RUNTIME_FORMAL_ID")
    for field in RUNTIME_ID_FIELDS - {"formal_semantics_id"}:
        gate.content_id(runtime_ids[field], "RAW_RUNTIME_ID")
    for field in (
        "canonical_input_trace_sha256",
        "fault_trace_sha256",
        "hardware_allocation_sha256",
        "native_core_sha256",
        "toolchains_sha256",
    ):
        gate.content_id(run[field], f"RAW_{field.upper()}")
    initial_artifacts = exact_object(
        run["initial_artifacts"], INITIAL_ARTIFACT_FIELDS, "RAW_INITIAL_ARTIFACTS"
    )
    for value_id in initial_artifacts.values():
        gate.content_id(value_id, "RAW_INITIAL_ARTIFACT_ID")
    request_order = validate_order_records(run["request_order"], timer=False)
    timer_order = validate_order_records(run["timer_order"], timer=True)
    saturation_request_schedule = validate_saturation_schedule(
        run["saturation_request_schedule"], request_order, aggregation
    )

    warmup = gate.strict_u64(run["warmup_completed_operations"], "RAW_WARMUP")
    require(warmup == aggregation["warmup_operations"], "RAW_WARMUP")
    (
        compact_fixed,
        compact_saturation,
        percentiles,
        phase_percentiles,
        saturation_total,
        schedule,
    ) = validate_blocks(run, aggregation, production=production)
    measured_operations = gate.checked_add_u64(
        percentiles["sample_count"], saturation_total, "RAW_MEASURED_OPERATION_OVERFLOW"
    )
    compact_copy, fallback = validate_copy_ledger(
        run, comparison["copy_accounting"], measured_operations
    )

    expected_restart_points = list(comparison["paired_crash_points"])
    if expected_profile == "ISOLATED_SIDECAR":
        expected_restart_points += comparison["sidecar_supplemental_crash_points"]
    restart = validate_restarts(run["restart_to_ready"], expected_restart_points, expected_profile)

    survival = exact_object(run["java_process_survival"], SURVIVAL_FIELDS, "RAW_SURVIVAL_FIELDS")
    survived = survival["survived_all_native_deaths"]
    require(type(survived) is bool, "RAW_SURVIVAL_TYPE")
    survival_evidence, survival_passed, _ = validate_evidence_object(
        survival["evidence"], survival["evidence_sha256"], "RAW_SURVIVAL_EVIDENCE"
    )
    require(survival_passed, "RAW_SURVIVAL_CHECK_FAILED")
    require_observations(
        survival_evidence,
        {
            "native_death_injection_count": len(expected_restart_points),
            "profile_id": expected_profile,
            "qualification_case_count": len(expected_restart_points),
            "survived_all_native_deaths": survived,
        },
        "RAW_SURVIVAL_OBSERVATION",
    )
    if expected_profile == "EMBEDDED_FFM":
        require(survived is False, "RAW_EMBEDDED_COFAILURE_REQUIRED")

    transcripts = validate_transcripts(
        run["output_transcripts"], comparison["exact_cross_profile_equalities"], expected_profile
    )
    wal_artifacts = exact_object(
        run["wal_artifacts"], WAL_ARTIFACTS_FIELDS, "RAW_WAL_ARTIFACTS_FIELDS"
    )
    compact_wal_artifacts: dict[str, dict[str, int | str]] = {}
    for artifact_id in ("record_vote", "runtime"):
        record = exact_object(
            wal_artifacts[artifact_id], WAL_ARTIFACT_FIELDS, "RAW_WAL_ARTIFACT_FIELDS"
        )
        compact_wal_artifacts[artifact_id] = {
            "sha256": gate.content_id(record["sha256"], "RAW_WAL_ARTIFACT_SHA256"),
            "size_bytes": gate.strict_u64(
                record["size_bytes"], "RAW_WAL_ARTIFACT_SIZE", positive=True
            ),
        }
    require(
        transcripts["WAL_RECEIPTS_AND_DURABLE_SEQUENCES"]["transcript_sha256"]
        == gate.sha256_id(gate.canonical_bytes(compact_wal_artifacts)),
        "RAW_WAL_TRANSCRIPT_BINDING",
    )
    crash_document = {
        "java_process_survival": survival,
        "profile_id": expected_profile,
        "restart_to_ready": run["restart_to_ready"],
        "schema_version": "1.0.0",
        "type_name": "FEATURE010_SIDECAR_CRASH_OBSERVATIONS",
    }
    crash_artifact = gate.sha256_id(gate.canonical_bytes(crash_document))
    provenance_sha256 = validate_input_provenance(run, crash_artifact_sha256=crash_artifact)
    vote_fixture_node = next(
        node for node in run["input_graph_nodes"] if node["node_id"] == "INPUT:VOTE_FIXTURE"
    )
    vote_fixture = {
        "sha256": gate.content_id(vote_fixture_node["artifact_sha256"], "VOTE_FIXTURE_SHA256"),
        "size_bytes": gate.strict_u64(
            vote_fixture_node["size_bytes"], "VOTE_FIXTURE_SIZE", positive=True
        ),
    }
    runtime_stats = exact_object(run["runtime_stats"], RUNTIME_STATS_FIELDS, "RUNTIME_STATS")
    for field in RUNTIME_STATS_FIELDS:
        gate.strict_u64(runtime_stats[field], "RUNTIME_STATS_VALUE")
    expected_retry_count = len(saturation_request_schedule["target_request_ids"])
    for block in run["saturation_blocks"]:
        expected_retry_count = gate.checked_add_u64(
            expected_retry_count,
            block["admitted_operations"],
            "RUNTIME_RETRY_COUNT_OVERFLOW",
        )
    require(runtime_stats["retry_count"] == expected_retry_count, "RUNTIME_RETRY_COUNT")
    fixed_artifact = gate.sha256_id(gate.canonical_bytes(run["fixed_load_blocks"]))
    saturation_artifact = gate.sha256_id(gate.canonical_bytes(run["saturation_blocks"]))
    transcript_artifact = gate.sha256_id(
        gate.canonical_bytes(
            {
                equality_id: transcripts[equality_id]["transcript_sha256"]
                for equality_id in comparison["exact_cross_profile_equalities"]
            }
        )
    )
    runtime_stats_artifact = gate.sha256_id(gate.canonical_bytes(runtime_stats))
    base_observation = {"profile_id": expected_profile}
    measurement_expectations: dict[str, tuple[str, str, dict[str, object]]] = {
        "END_TO_END_LATENCY_NS": (
            fixed_artifact,
            "ALL_FIXED_LOAD_SAMPLES_PRESENT",
            {"measurement_id": "END_TO_END_LATENCY_NS", **base_observation},
        ),
        "PHASE_LATENCY_NS": (
            fixed_artifact,
            "ALL_FIXED_LOAD_SAMPLES_PRESENT",
            {"measurement_id": "PHASE_LATENCY_NS", **base_observation},
        ),
        "FIXED_LOAD_THROUGHPUT_OPS_PER_WINDOW": (
            fixed_artifact,
            "ALL_FIXED_LOAD_SAMPLES_PRESENT",
            {
                "measurement_id": "FIXED_LOAD_THROUGHPUT_OPS_PER_WINDOW",
                **base_observation,
            },
        ),
        "SATURATION_THROUGHPUT_OPS_PER_WINDOW": (
            saturation_artifact,
            "ALL_SATURATION_WINDOWS_PRESENT",
            {
                "executed_corpus_prefix_operations": warmup + percentiles["sample_count"],
                "measurement_id": "SATURATION_THROUGHPUT_OPS_PER_WINDOW",
                **base_observation,
                "request_order_scope": "FULL_DLTSTRC1_ORDERED_INPUT_CORPUS",
            },
        ),
        "RESTART_TO_READY_NS": (
            crash_artifact,
            "INDEPENDENT_CRASH_RECEIPTS_IMPORTED",
            {"measurement_id": "RESTART_TO_READY_NS", **base_observation},
        ),
        "JAVA_PROCESS_SURVIVAL": (
            crash_artifact,
            "PROFILE_BOUNDARY_SURVIVAL_REPORTED",
            {"measurement_id": "JAVA_PROCESS_SURVIVAL", **base_observation},
        ),
        "STATE_EFFECT_WAL_REPLAY_IDENTITY": (
            transcript_artifact,
            "CONCRETE_TRANSCRIPTS_CAPTURED",
            {"measurement_id": "STATE_EFFECT_WAL_REPLAY_IDENTITY", **base_observation},
        ),
        "RETRY_COUNT": (
            runtime_stats_artifact,
            "EXACT_REPLAYS_COMPLETED",
            {
                "measurement_id": "RETRY_COUNT",
                **base_observation,
                "value": runtime_stats["retry_count"],
            },
        ),
        "DUPLICATE_RESPONSE_COUNT": (
            runtime_stats_artifact,
            "CLIENT_COUNTER_CAPTURED",
            {
                "measurement_id": "DUPLICATE_RESPONSE_COUNT",
                **base_observation,
                "value": runtime_stats["duplicate_response_count"],
            },
        ),
        "STALE_RESPONSE_COUNT": (
            runtime_stats_artifact,
            "CLIENT_COUNTER_CAPTURED",
            {
                "measurement_id": "STALE_RESPONSE_COUNT",
                **base_observation,
                "value": runtime_stats["stale_response_count"],
            },
        ),
        "REJECTED_FRAME_COUNT": (
            runtime_stats_artifact,
            "CLIENT_COUNTER_CAPTURED",
            {
                "measurement_id": "REJECTED_FRAME_COUNT",
                **base_observation,
                "value": runtime_stats["rejected_frame_count"],
            },
        ),
    }
    measurements = validate_measurements(
        run["measurements"],
        comparison["required_measurements"],
        expected_profile,
        measurement_expectations,
    )
    pair_values = {
        "SOURCE_COMMIT_AND_TREE": source,
        "FORMAL_ABI_SCHEMA_PROTOCOL_BUILD_SCHEMA_SET_IDS": runtime_ids,
        "NATIVE_CORE": run["native_core_sha256"],
        "HARDWARE_ALLOCATION": run["hardware_allocation_sha256"],
        "TOOLCHAINS": run["toolchains_sha256"],
        "INITIAL_WAL_AND_SNAPSHOT_HASHES": initial_artifacts,
        "CANONICAL_INPUT_BYTES": {
            "corpus_sha256": run["canonical_input_trace_sha256"],
            "vote_fixture": vote_fixture,
        },
        "REQUEST_IDS_AND_ORDER": {
            "new_transition_order": request_order,
            "saturation_replay_schedule": saturation_request_schedule,
        },
        "TIMER_TOKENS_AND_ORDER": timer_order,
        "QUEUE_AND_INFLIGHT_BOUNDS": run["bounds"],
        "WARMUP_AND_REPETITION_COUNTS": {
            "fixed_load_blocks": len(compact_fixed),
            "saturation_blocks": len(compact_saturation),
            "warmup_completed_operations": warmup,
        },
        "OFFERED_LOAD_SCHEDULE": schedule,
        "PAIRED_CORE_FAULT_TRACE": run["fault_trace_sha256"],
        "AGGREGATION_RULES": run["aggregation_rules"],
    }
    require(
        list(pair_values) == comparison["identical_pair_fields"],
        "RAW_PAIR_FIELD_MAPPING",
    )
    compact_profile = {
        "copy_accounting": compact_copy,
        "fixed_load_blocks": compact_fixed,
        "fixed_load_latency_ns": percentiles,
        "input_provenance_sha256": provenance_sha256,
        "java_survived_all_native_deaths": survived,
        "max_staging_fallback": fallback,
        "measurement_coverage": measurements,
        "phase_latency_ns": phase_percentiles,
        "phase_latency_sample_count": phase_percentiles["sample_count"],
        "profile_id": expected_profile,
        "raw_capture_sha256": gate.sha256_id(gate.canonical_bytes(run)),
        "restart_to_ready_ns": restart,
        "saturation_blocks": compact_saturation,
        "wal_artifacts": compact_wal_artifacts,
        "warmup_completed_operations": warmup,
    }
    native_node_id = (
        "INPUT:NATIVE_LIBRARY" if expected_profile == "EMBEDDED_FFM" else "INPUT:SIDECAR_EXECUTABLE"
    )
    native_artifact_sha256 = next(
        node["artifact_sha256"]
        for node in run["input_graph_nodes"]
        if node["node_id"] == native_node_id
    )
    runner_log_sha256s = frozenset(
        node["artifact_sha256"]
        for node in run["input_graph_nodes"]
        if node["node_id"].startswith("RUNNER_LOG:")
    )
    require(bool(runner_log_sha256s), "RUNNER_LOG_COUNT")
    return {
        "compact_profile": compact_profile,
        "native_artifact_sha256": native_artifact_sha256,
        "pair_values": pair_values,
        "runner_log_sha256s": runner_log_sha256s,
        "source": source,
        "survived": survived,
        "transcripts": transcripts,
    }


def crash_evidence_passes(
    value: object,
    declared_sha256: object,
    crash_point: str,
    *,
    expected_profile: str,
    expected_java_survival: bool,
    special_shared_memory: bool = False,
) -> tuple[bool, str]:
    evidence, checks_pass, evidence_sha256 = validate_evidence_object(
        value, declared_sha256, "CRASH_EVIDENCE"
    )
    observations = evidence["observations"]
    require(CRASH_OBSERVATION_FIELDS <= set(observations), "CRASH_OBSERVATIONS", crash_point)
    require(observations.get("crash_point") == crash_point, "CRASH_OBSERVATIONS", "crash_point")
    require(
        observations.get("profile_id") == expected_profile,
        "CRASH_OBSERVATIONS",
        "profile_id",
    )
    derived = (
        observations["java_process_survived"] is expected_java_survival
        and observations["journal_recovered_before_admission"] is True
        and observations["partial_response_exposed"] is False
        and observations["persist_before_expose"] is True
        and observations["replay_identity_exact"] is True
    )
    for field in CRASH_OBSERVATION_FIELDS:
        require(type(observations[field]) is bool, "CRASH_OBSERVATION_TYPE", field)
    if special_shared_memory:
        require(
            SHM_PUBLICATION_OBSERVATION_FIELDS <= set(observations),
            "SHM_PUBLICATION_OBSERVATIONS",
        )
        checks = evidence["checks"]
        require(
            set(checks) == SHM_PUBLICATION_CHECKS and all(checks.values()),
            "SHM_PUBLICATION_CHECKS",
        )
        require(
            observations["atomic_abi_probe_result"]
            == "LOCK_FREE_JAVA_NATIVE_MAP_SHARED_U32_BIG_ENDIAN"
            and observations["atomic_abi_probe_scope"] == "EXACT_PATH_DEVICE_INODE_GENERATION_SLOT",
            "SHM_ATOMIC_ABI",
        )
        require(observations["atomic_abi_supported"] is True, "SHM_ATOMIC_ABI")
        require(observations["shared_memory_enabled"] is True, "SHM_MUST_BE_ENABLED")
        gate.strict_u64(observations["duration_ns"], "SHM_DURATION", positive=True)
        open_admitted_sequence = gate.strict_u64(
            observations["shared_memory_open_admitted_sequence"],
            "SHM_OPEN_ADMITTED_SEQUENCE",
            positive=True,
        )
        admitted_sequence = gate.strict_u64(
            observations["shared_memory_admitted_sequence"],
            "SHM_ADMITTED_SEQUENCE",
            positive=True,
        )
        require(
            observations["shared_memory_admission_state"] == "ADMITTED_OUTCOME_AVAILABLE"
            and open_admitted_sequence == 1
            and admitted_sequence == 2
            and admitted_sequence == open_admitted_sequence + 1
            and observations["shared_memory_admitted_sequence_derivation"]
            == "OBSERVED_OPEN_ADMISSION_PLUS_FIRST_POST_OPEN_OPERATION"
            and gate.strict_u64(
                observations["shared_memory_native_call_count"], "SHM_NATIVE_CALL_COUNT"
            )
            == 1
            and gate.strict_u64(observations["shared_memory_native_status"], "SHM_NATIVE_STATUS")
            == 0,
            "SHM_ADMITTED_OUTCOME",
        )
        require(
            observations["shared_memory_telemetry_scope"] == "SUPERVISOR_ALL_GENERATIONS",
            "SHM_TELEMETRY_SCOPE",
        )
        require(
            observations["shared_memory_publication_started"] is True
            and observations["shared_memory_publication_completed"] is False
            and observations["shared_memory_control_frame_exposed"] is True
            and observations["shared_memory_operation_response_frame_exposed"] is False,
            "SHM_PUBLICATION_CUT",
        )
        require(
            gate.strict_u64(
                observations["shared_memory_ingress_ack_frame_count"],
                "SHM_INGRESS_ACK_FRAME_COUNT",
            )
            == 1
            and observations["shared_memory_notification_ack_inline_only"] is True
            and gate.strict_u64(
                observations["shared_memory_failed_generation_response_frame_count"],
                "SHM_FAILED_RESPONSE_FRAME_COUNT",
            )
            == 0
            and gate.strict_u64(
                observations["shared_memory_failed_generation_response_carrier_count"],
                "SHM_FAILED_RESPONSE_CARRIER_COUNT",
            )
            == 0
            and gate.strict_u64(
                observations["shared_memory_failed_generation_egress_control_bytes"],
                "SHM_FAILED_EGRESS_CONTROL_BYTES",
            )
            == gate.strict_u64(
                observations["failed_generation_stdout_bytes_after_submit"],
                "SHM_FAILED_STDOUT_BYTES",
                positive=True,
            )
            and gate.strict_u64(
                observations["shared_memory_failed_generation_operation_response_wire_bytes"],
                "SHM_FAILED_OPERATION_RESPONSE_WIRE_BYTES",
            )
            == 0
            and gate.strict_u64(
                observations["validated_response_count_before_recovery"],
                "SHM_VALIDATED_RESPONSE_COUNT",
            )
            == 0,
            "SHM_NOTIFICATION_ONLY_ACK",
        )
        require(
            observations["shared_memory_region_id"] == "NATIVE_TO_JAVA"
            and observations["shared_memory_slot_state_at_native_death"] == "WRITING"
            and observations["shared_memory_status"] == "ENABLED_LOCK_FREE_U32_BIG_ENDIAN",
            "SHM_PUBLICATION_STATE",
        )
        require(observations["crash_process_exit_code"] == 88, "SHM_CRASH_EXIT_CODE")
        require(observations["fallback_transport"] == "NOT_USED", "SHM_FALLBACK_TRANSPORT")
        require(observations["bounded_copy_equivalence"] == "EXACT", "SHM_COPY_EQUIVALENCE")
        ingress = gate.strict_u64(
            observations["shared_memory_ingress_bytes"], "SHM_INGRESS_BYTES", positive=True
        )
        egress = gate.strict_u64(
            observations["shared_memory_egress_bytes"], "SHM_EGRESS_BYTES", positive=True
        )
        eligible = gate.strict_u64(
            observations["zero_copy_eligible_count"], "SHM_ZERO_COPY_ELIGIBLE", positive=True
        )
        hits = gate.strict_u64(observations["zero_copy_hit_count"], "SHM_ZERO_COPY_HITS")
        require(ingress > 0 and egress > 0, "SHM_TRAFFIC")
        require(hits <= eligible, "SHM_ZERO_COPY_COUNTER_ORDER")
        require(hits == 0, "SHM_ZERO_COPY_HIT_FORBIDDEN")
    return checks_pass and derived, evidence_sha256


def conformance_receipt_passes(
    evidence: dict[str, Any],
    gate_id: str,
    runs: dict[str, dict[str, Any]],
) -> bool:
    """Derive a conformance gate from a source- and provenance-bound process receipt."""
    expected_test_id = CONFORMANCE_TEST_IDS.get(gate_id)
    if expected_test_id is None:
        return False
    observations = evidence["observations"]
    if set(observations) != CONFORMANCE_RECEIPT_FIELDS:
        return False
    embedded_source = runs["EMBEDDED_FFM"]["source"]
    sidecar_source = runs["ISOLATED_SIDECAR"]["source"]
    raw_log_sha256 = observations["raw_log_sha256"]
    return (
        observations["receipt_type"] == CONFORMANCE_RECEIPT_TYPE
        and observations["gate_id"] == gate_id
        and observations["test_id"] == expected_test_id
        and type(observations["exit_code"]) is int
        and observations["exit_code"] == 0
        and observations["source_commit"] == embedded_source["commit"]
        and observations["source_commit"] == sidecar_source["commit"]
        and observations["source_tree"] == embedded_source["tree"]
        and observations["source_tree"] == sidecar_source["tree"]
        and observations["binary_sha256"] == runs["ISOLATED_SIDECAR"]["native_artifact_sha256"]
        and raw_log_sha256 in runs["ISOLATED_SIDECAR"]["runner_log_sha256s"]
        and evidence["artifact_sha256"] == raw_log_sha256
    )


def validate_manifest(
    value: object,
    design: dict[str, Any],
    runs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    manifest = exact_object(value, MANIFEST_FIELDS, "MANIFEST_FIELDS")
    validate_headers(manifest, MANIFEST_TYPE, "MANIFEST")
    comparison = design["comparison_plan"]

    def gate_records(
        raw: object,
        expected_ids: list[str],
        *,
        sidecar: bool,
    ) -> list[dict[str, object]]:
        require(isinstance(raw, list) and len(raw) == len(expected_ids), "MANIFEST_GATE_COUNT")
        result: list[dict[str, object]] = []
        for index, gate_id in enumerate(expected_ids):
            record = exact_object(raw[index], MANIFEST_GATE_FIELDS, "MANIFEST_GATE_FIELDS")
            require(record["gate_id"] == gate_id, "MANIFEST_GATE_ORDER")
            evidence, _, evidence_sha256 = validate_evidence_object(
                record["evidence"], record["evidence_sha256"], "MANIFEST_GATE_EVIDENCE"
            )
            conformance_passed: bool | None = None
            if not sidecar and gate_id in CONFORMANCE_TEST_IDS:
                conformance_passed = conformance_receipt_passes(evidence, gate_id, runs)
            else:
                require(
                    evidence["observations"] == {"gate_id": gate_id},
                    "MANIFEST_GATE_OBSERVATION",
                    gate_id,
                )
            result.append(
                {
                    "conformance_passed": conformance_passed,
                    "evidence_sha256": evidence_sha256,
                    "gate_id": gate_id,
                }
            )
        return result

    common_records = gate_records(
        manifest["common_hard_gates"], comparison["hard_gates_common"], sidecar=False
    )
    sidecar_records = gate_records(
        manifest["sidecar_hard_gates"], comparison["hard_gates_sidecar"], sidecar=True
    )

    crash = exact_object(manifest["crash_coverage"], MANIFEST_CRASH_FIELDS, "MANIFEST_CRASH_FIELDS")
    paired_ids = comparison["paired_crash_points"]
    paired = crash["paired"]
    require(
        isinstance(paired, list) and len(paired) == len(paired_ids), "MANIFEST_PAIRED_CRASH_COUNT"
    )
    compact_paired: list[dict[str, str]] = []
    embedded_survival: list[bool] = []
    sidecar_survival: list[bool] = []
    paired_observations: list[dict[str, Any]] = []
    for index, crash_point in enumerate(paired_ids):
        record = exact_object(paired[index], PAIRED_CRASH_FIELDS, "MANIFEST_PAIRED_CRASH_FIELDS")
        require(record["crash_point"] == crash_point, "MANIFEST_PAIRED_CRASH_ORDER")
        embedded_pass, embedded_sha256 = crash_evidence_passes(
            record["embedded_evidence"],
            record["embedded_evidence_sha256"],
            crash_point,
            expected_profile="EMBEDDED_FFM",
            expected_java_survival=False,
        )
        sidecar_pass, sidecar_sha256 = crash_evidence_passes(
            record["sidecar_evidence"],
            record["sidecar_evidence_sha256"],
            crash_point,
            expected_profile="ISOLATED_SIDECAR",
            expected_java_survival=True,
        )
        embedded_survival.append(
            record["embedded_evidence"]["observations"]["java_process_survived"]
        )
        sidecar_survival.append(record["sidecar_evidence"]["observations"]["java_process_survived"])
        paired_observations.extend(
            [
                record["embedded_evidence"]["observations"],
                record["sidecar_evidence"]["observations"],
            ]
        )
        compact_paired.append(
            {
                "crash_point": crash_point,
                "embedded_evidence_sha256": embedded_sha256,
                "sidecar_evidence_sha256": sidecar_sha256,
                "status": "PASS" if embedded_pass and sidecar_pass else "FAIL",
            }
        )

    supplemental_ids = comparison["sidecar_supplemental_crash_points"]
    supplemental = crash["sidecar_supplemental"]
    require(
        isinstance(supplemental, list) and len(supplemental) == len(supplemental_ids),
        "MANIFEST_SUPPLEMENTAL_CRASH_COUNT",
    )
    compact_supplemental: list[dict[str, str]] = []
    for index, crash_point in enumerate(supplemental_ids):
        record = exact_object(
            supplemental[index], SUPPLEMENTAL_CRASH_FIELDS, "MANIFEST_SUPPLEMENTAL_CRASH_FIELDS"
        )
        require(record["crash_point"] == crash_point, "MANIFEST_SUPPLEMENTAL_CRASH_ORDER")
        passed, evidence_sha256 = crash_evidence_passes(
            record["evidence"],
            record["evidence_sha256"],
            crash_point,
            expected_profile="ISOLATED_SIDECAR",
            expected_java_survival=True,
            special_shared_memory=crash_point == "DURING_SHARED_MEMORY_PUBLICATION",
        )
        sidecar_survival.append(record["evidence"]["observations"]["java_process_survived"])
        compact_supplemental.append(
            {
                "crash_point": crash_point,
                "evidence_sha256": evidence_sha256,
                "status": "PASS" if passed else "FAIL",
            }
        )

    require(
        runs["EMBEDDED_FFM"]["survived"] is all(embedded_survival),
        "EMBEDDED_SURVIVAL_AGGREGATE",
    )
    require(
        runs["ISOLATED_SIDECAR"]["survived"] is all(sidecar_survival),
        "SIDECAR_SURVIVAL_AGGREGATE",
    )

    def semantic_equal(*equality_ids: str) -> bool:
        return all(
            runs["EMBEDDED_FFM"]["transcripts"][equality_id]["transcript_sha256"]
            == runs["ISOLATED_SIDECAR"]["transcripts"][equality_id]["transcript_sha256"]
            for equality_id in equality_ids
        )

    all_measurements_present = all(
        measurement["status"] == "PRESENT"
        for profile in ("EMBEDDED_FFM", "ISOLATED_SIDECAR")
        for measurement in runs[profile]["compact_profile"]["measurement_coverage"]
    )
    common_derived = {
        "EXACT_CANONICAL_STATUS_EFFECT_STATE_AND_WAL_BYTES": semantic_equal(
            "CANONICAL_STATUS_BYTES",
            "CANONICAL_EFFECT_BYTES",
            "STATE_ROOTS",
            "WAL_RECEIPTS_AND_DURABLE_SEQUENCES",
        ),
        "EXACT_PROJECTED_FORMAL_TRACE": semantic_equal(
            "PROJECTED_FORMAL_TRACE_BYTES_AFTER_STUTTER_ERASURE"
        ),
        "PERSIST_BEFORE_EXPOSE_AT_ALL_PAIRED_CRASH_POINTS": all(
            observation["persist_before_expose"] is True
            and observation["partial_response_exposed"] is False
            for observation in paired_observations
        ),
        "RESTART_AND_JOURNAL_RECOVERY_BEFORE_ADMISSION": all(
            observation["journal_recovered_before_admission"] is True
            for observation in paired_observations
        ),
        "EXACT_REPLAY_EFFECT_IDENTITY_AND_DURABLE_SEQUENCE": semantic_equal(
            "WAL_RECEIPTS_AND_DURABLE_SEQUENCES", "REPLAY_EFFECT_IDENTITIES"
        )
        and all(
            observation["replay_identity_exact"] is True for observation in paired_observations
        ),
        "NO_MISSING_BLOCK_OPERATION_OR_METRIC": all_measurements_present,
    }
    for record in common_records:
        gate_id = str(record["gate_id"])
        conformance_passed = record["conformance_passed"]
        if conformance_passed is not None:
            common_derived[gate_id] = bool(conformance_passed)
    require(
        set(common_derived) == set(comparison["hard_gates_common"]),
        "MANIFEST_GATE_DERIVATION",
    )
    common_gates = [
        {
            "evidence_sha256": record["evidence_sha256"],
            "gate_id": record["gate_id"],
            "status": "PASS" if common_derived[str(record["gate_id"])] else "FAIL",
        }
        for record in common_records
    ]

    supplemental_pass = all(item["status"] == "PASS" for item in compact_supplemental)
    sidecar_derived = {
        "JAVA_SURVIVES_EVERY_SIDECAR_NATIVE_DEATH_INJECTION": (
            runs["ISOLATED_SIDECAR"]["survived"] and all(sidecar_survival)
        ),
        "SIDECAR_SUPPLEMENTAL_CRASH_RECOVERY_AND_NO_PARTIAL_RESPONSE": supplemental_pass,
    }
    require(
        set(sidecar_derived) == set(comparison["hard_gates_sidecar"]),
        "MANIFEST_GATE_DERIVATION",
    )
    sidecar_gates = [
        {
            "evidence_sha256": record["evidence_sha256"],
            "gate_id": record["gate_id"],
            "status": "PASS" if sidecar_derived[str(record["gate_id"])] else "FAIL",
        }
        for record in sidecar_records
    ]
    return {
        "common_hard_gates": common_gates,
        "crash_coverage": {"paired": compact_paired, "sidecar_supplemental": compact_supplemental},
        "sidecar_hard_gates": sidecar_gates,
    }


def pair_markers(
    runs: dict[str, dict[str, Any]],
    expected_ids: list[str],
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for field_id in expected_ids:
        embedded = gate.sha256_id(
            gate.canonical_bytes(runs["EMBEDDED_FFM"]["pair_values"][field_id])
        )
        sidecar = gate.sha256_id(
            gate.canonical_bytes(runs["ISOLATED_SIDECAR"]["pair_values"][field_id])
        )
        exact = embedded == sidecar
        comparison = {
            "embedded_sha256": embedded,
            "exact": exact,
            "field_id": field_id,
            "sidecar_sha256": sidecar,
        }
        result.append(
            {
                "embedded_sha256": embedded,
                "evidence_sha256": gate.sha256_id(gate.canonical_bytes(comparison)),
                "field_id": field_id,
                "sidecar_sha256": sidecar,
                "status": "EXACT" if exact else "MISMATCH",
            }
        )
    return result


def semantic_markers(
    runs: dict[str, dict[str, Any]],
    expected_ids: list[str],
) -> list[dict[str, str]]:
    result: list[dict[str, str]] = []
    for equality_id in expected_ids:
        embedded_record = runs["EMBEDDED_FFM"]["transcripts"][equality_id]
        sidecar_record = runs["ISOLATED_SIDECAR"]["transcripts"][equality_id]
        embedded = embedded_record["transcript_sha256"]
        sidecar = sidecar_record["transcript_sha256"]
        exact = embedded == sidecar
        comparison = {
            "embedded_evidence_sha256": embedded_record["evidence_sha256"],
            "embedded_sha256": embedded,
            "equality_id": equality_id,
            "exact": exact,
            "sidecar_evidence_sha256": sidecar_record["evidence_sha256"],
            "sidecar_sha256": sidecar,
        }
        result.append(
            {
                "embedded_sha256": embedded,
                "equality_id": equality_id,
                "evidence_sha256": gate.sha256_id(gate.canonical_bytes(comparison)),
                "sidecar_sha256": sidecar,
                "status": "EXACT" if exact else "MISMATCH",
            }
        )
    return result


def assemble_comparison(
    embedded_run: object,
    sidecar_run: object,
    gate_crash_manifest: object,
    *,
    _design_override: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    production = _design_override is None
    design = gate.load_frozen_design() if production else _design_override
    require(isinstance(design, dict), "DESIGN_OBJECT")
    validate_design_shape(design, production=production)
    runs = {
        "EMBEDDED_FFM": validate_run(embedded_run, "EMBEDDED_FFM", design, production=production),
        "ISOLATED_SIDECAR": validate_run(
            sidecar_run, "ISOLATED_SIDECAR", design, production=production
        ),
    }
    manifest = validate_manifest(gate_crash_manifest, design, runs)
    comparison = design["comparison_plan"]
    compact = {
        "authority": gate.expected_authority(design),
        "common_hard_gates": manifest["common_hard_gates"],
        "crash_coverage": manifest["crash_coverage"],
        "design_canonical_id": gate.EXPECTED_DESIGN_CANONICAL_ID,
        "design_sha256": gate.EXPECTED_DESIGN_SHA256,
        "execution_class": EXECUTION_CLASS,
        "formal_semantics_id": gate.FORMAL_ID,
        "pair_fields": pair_markers(runs, comparison["identical_pair_fields"]),
        "profiles": [
            runs["EMBEDDED_FFM"]["compact_profile"],
            runs["ISOLATED_SIDECAR"]["compact_profile"],
        ],
        "risk_acceptance": None,
        "schema_version": "1.0.0",
        "semantic_equalities": semantic_markers(runs, comparison["exact_cross_profile_equalities"]),
        "sidecar_hard_gates": manifest["sidecar_hard_gates"],
        "status": "COMPLETE",
        "type_name": "FEATURE010_SIDECAR_COMPARISON_EVIDENCE",
    }
    selection = gate.validate_evidence(compact, design)
    return compact, selection


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("embedded_run", type=Path)
    parser.add_argument("sidecar_run", type=Path)
    parser.add_argument("gate_crash_manifest", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--result-output", type=Path)
    arguments = parser.parse_args()
    try:
        embedded, _ = gate.canonical_document(arguments.embedded_run)
        sidecar, _ = gate.canonical_document(arguments.sidecar_run)
        manifest, _ = gate.canonical_document(arguments.gate_crash_manifest)
        compact, result = assemble_comparison(embedded, sidecar, manifest)
        arguments.output.parent.mkdir(parents=True, exist_ok=True)
        arguments.output.write_bytes(gate.canonical_bytes(compact) + b"\n")
        if arguments.result_output is not None:
            arguments.result_output.parent.mkdir(parents=True, exist_ok=True)
            arguments.result_output.write_bytes(gate.canonical_bytes(result) + b"\n")
    except (gate.ComparisonError, OSError, ValueError, KeyError, TypeError) as error:
        print(gate.canonical_bytes({"error": str(error), "status": "FAIL"}).decode("utf-8"))
        return 2
    print(gate.canonical_bytes(result).decode("utf-8"))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
