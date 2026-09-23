from __future__ import annotations

import copy
import hashlib
import re
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "specs/010-wan-benchmark-and-quality/scripts"
JAVA_CRASH_QUALIFICATION = (
    ROOT
    / "delta-node-java/src/test/java/io/deltareduce/node/sidecar/SidecarCrashQualification.java"
)
sys.path.insert(0, str(SCRIPTS))
import assemble_sidecar_comparison as assembler  # noqa: E402
import sidecar_comparison_gate as gate  # noqa: E402


def content_id(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode("utf-8")).hexdigest()


def evidence_record(
    label: str,
    observations: dict[str, object],
    checks: dict[str, bool] | None = None,
    artifact_sha256: str | None = None,
) -> dict[str, object]:
    evidence = {
        "artifact_sha256": artifact_sha256 or content_id("artifact:" + label),
        "checks": {"OBSERVATION_VERIFIED": True} if checks is None else checks,
        "observations": observations,
    }
    return {
        "evidence": evidence,
        "evidence_sha256": gate.sha256_id(gate.canonical_bytes(evidence)),
    }


def rehash(record: dict[str, object], prefix: str = "") -> None:
    evidence_field = f"{prefix}evidence"
    digest_field = f"{prefix}evidence_sha256"
    record[digest_field] = gate.sha256_id(gate.canonical_bytes(record[evidence_field]))


def small_design() -> dict[str, Any]:
    design = copy.deepcopy(gate.load_frozen_design())
    aggregation = design["comparison_plan"]["aggregation"]
    aggregation.update(
        {
            "fixed_load_offered_operations_per_block": 3,
            "fixed_offered_load_ops_per_second": 1,
            "latency_population": "TEST_ONLY_ALL_6_FIXED_LOAD_OPERATIONS",
            "measured_blocks": 2,
            "saturation_blocks": 2,
            "throughput_window_seconds": 3,
            "warmup_operations": 2,
        }
    )
    return design


def copy_sample(operation_id: str, first: bool, hit: bool) -> dict[str, object]:
    return {
        "INLINE_INGRESS_BYTES": 1,
        "INLINE_EGRESS_BYTES": 2,
        "SHARED_MEMORY_INGRESS_BYTES": 0,
        "SHARED_MEMORY_EGRESS_BYTES": 0,
        "STAGING_FALLBACK_INGRESS_BYTES": 4 if first else 0,
        "STAGING_FALLBACK_EGRESS_BYTES": 6 if first else 0,
        "ZERO_COPY_ELIGIBLE_COUNT": 1 if first else 0,
        "ZERO_COPY_HIT_COUNT": 1 if first and hit else 0,
        "operation_id": operation_id,
    }


def raw_run(profile: str, design: dict[str, Any]) -> dict[str, object]:
    comparison = design["comparison_plan"]
    aggregation = comparison["aggregation"]
    embedded = profile == "EMBEDDED_FFM"
    latencies = [[10, 20, 30], [40, 50, 100]] if embedded else [[12, 24, 36], [48, 60, 120]]
    saturation_completed = 5
    measured_operations = 6 + 2 * saturation_completed
    samples = [
        copy_sample(f"{profile}-operation-{index}", index == 0, False)
        for index in range(measured_operations)
    ]
    totals = {
        counter_id: sum(int(sample[counter_id]) for sample in samples)
        for counter_id in comparison["copy_accounting"]
    }
    copy_accounting = []
    totals_artifact = gate.sha256_id(gate.canonical_bytes(totals))
    for counter_id in comparison["copy_accounting"]:
        record = {
            "counter_id": counter_id,
            "value": totals[counter_id],
            **evidence_record(
                f"{profile}:copy:{counter_id}",
                {"counter_id": counter_id, "profile_id": profile, "value": totals[counter_id]},
                checks={"COUNTER_SUM_MATCHES_OPERATION_SAMPLES": True},
                artifact_sha256=totals_artifact,
            ),
        }
        copy_accounting.append(record)

    measurements: list[dict[str, object]] = []
    restart_points = list(comparison["paired_crash_points"])
    if not embedded:
        restart_points += comparison["sidecar_supplemental_crash_points"]
    restart = []
    for index, crash_point in enumerate(restart_points):
        duration = 1_000 + index
        restart.append(
            {
                "crash_point": crash_point,
                "duration_ns": duration,
                **evidence_record(
                    f"{profile}:restart:{crash_point}",
                    {"crash_point": crash_point, "duration_ns": duration, "profile_id": profile},
                ),
            }
        )

    survived = not embedded
    survival = {
        "survived_all_native_deaths": survived,
        **evidence_record(
            f"{profile}:survival",
            {
                "native_death_injection_count": len(restart_points),
                "profile_id": profile,
                "qualification_case_count": len(restart_points),
                "survived_all_native_deaths": survived,
            },
        ),
    }
    wal_artifacts = {
        "record_vote": {
            "sha256": content_id("record-vote-wal"),
            "size_bytes": 101,
        },
        "runtime": {
            "sha256": content_id("runtime-wal"),
            "size_bytes": 202,
        },
    }
    transcripts = []
    for equality_id in comparison["exact_cross_profile_equalities"]:
        transcript_sha256 = (
            gate.sha256_id(gate.canonical_bytes(wal_artifacts))
            if equality_id == "WAL_RECEIPTS_AND_DURABLE_SEQUENCES"
            else content_id("transcript:" + equality_id)
        )
        transcripts.append(
            {
                "equality_id": equality_id,
                "transcript_sha256": transcript_sha256,
                **evidence_record(
                    f"{profile}:transcript:{equality_id}",
                    {
                        "equality_id": equality_id,
                        "profile_id": profile,
                        "transcript_sha256": transcript_sha256,
                    },
                    checks={"CONCRETE_TRANSCRIPT_HASHED": True},
                    artifact_sha256=transcript_sha256,
                ),
            }
        )

    deterministic_count = aggregation["warmup_operations"] + (
        aggregation["measured_blocks"] * aggregation["fixed_load_offered_operations_per_block"]
    )
    request_order = [
        {
            "canonical_request_sha256": content_id(f"request:{index}"),
            "ordinal": index,
            "request_id": f"request-{index}",
        }
        for index in range(deterministic_count)
    ]
    target_request_ids = [
        request_order[
            aggregation["warmup_operations"]
            + ((block + 1) * aggregation["fixed_load_offered_operations_per_block"])
            - 1
        ]["request_id"]
        for block in range(aggregation["measured_blocks"])
    ]
    schedule_core = {
        "block_count": aggregation["saturation_blocks"],
        "cycle_length": len(target_request_ids),
        "max_in_flight": 64,
        "offers_per_block": assembler.SATURATION_OFFERS_PER_BLOCK,
        "replay_rule": (
            "FINITE_RLE_CYCLE_FIXED_BLOCK_TERMINAL_REQUESTS_THEN_HARNESS_CUTOFF_PRE_ADMISSION"
        ),
        "schema_version": "1.0.0",
        "target_request_ids": target_request_ids,
        "total_logical_offers": (
            aggregation["saturation_blocks"] * assembler.SATURATION_OFFERS_PER_BLOCK
        ),
        "type_name": "FEATURE010_SATURATION_REPLAY_SCHEDULE",
    }
    schedule_evidence = {
        "artifact_sha256": gate.sha256_id(gate.canonical_bytes(schedule_core)),
        "checks": {"PREDECLARED_IDENTICAL_REPLAY_STREAM": True},
        "observations": {
            "cycle_length": len(target_request_ids),
            "max_in_flight": 64,
            "offers_per_block": assembler.SATURATION_OFFERS_PER_BLOCK,
            "replay_rule": schedule_core["replay_rule"],
            "target_request_ids_sha256": gate.sha256_id(gate.canonical_bytes(target_request_ids)),
        },
    }
    saturation_request_schedule = {
        **schedule_core,
        "evidence": schedule_evidence,
        "evidence_sha256": gate.sha256_id(gate.canonical_bytes(schedule_evidence)),
    }

    run: dict[str, object] = {
        "aggregation_rules": copy.deepcopy(aggregation),
        "bounds": copy.deepcopy(design["ipc_contract"]["bounds"]),
        "canonical_input_trace_sha256": content_id("canonical-input-trace"),
        "copy_accounting": copy_accounting,
        "design_canonical_id": gate.EXPECTED_DESIGN_CANONICAL_ID,
        "design_sha256": gate.EXPECTED_DESIGN_SHA256,
        "execution_class": assembler.EXECUTION_CLASS,
        "fault_trace_sha256": content_id("paired-fault-trace"),
        "fixed_load_blocks": [
            {
                "block_index": index,
                "completed_operations": 3,
                "latency_ns": block_latencies,
                "offer_offset_ns": [0, 1_000_000_000, 2_000_000_000],
                "offered_operations": 3,
                "offered_ops_per_second": 1,
                "phase_latency_ns": [1, 2, 3],
                "window_seconds": 3,
            }
            for index, block_latencies in enumerate(latencies)
        ],
        "formal_semantics_id": gate.FORMAL_ID,
        "hardware_allocation_sha256": content_id("hardware-allocation"),
        "initial_artifacts": {
            "initial_state_sha256": content_id("initial-state"),
            "snapshot_sha256": content_id("initial-snapshot"),
            "wal_sha256": content_id("initial-wal"),
        },
        "java_process_survival": survival,
        "measurements": measurements,
        "native_core_sha256": content_id("native-core"),
        "operation_copy_samples": samples,
        "output_transcripts": transcripts,
        "profile_id": profile,
        "request_order": request_order,
        "restart_to_ready": restart,
        "runtime_ids": {
            "abi_sha256": content_id("abi"),
            "build_id": content_id("build"),
            "formal_semantics_id": gate.FORMAL_ID,
            "protocol_sha256": content_id("protocol"),
            "schema_set_id": content_id("schema-set"),
            "schema_sha256": content_id("schema"),
        },
        "runtime_stats": {},
        "saturation_blocks": [
            {
                "admitted_operations": saturation_completed,
                "block_index": index,
                "completed_operations": saturation_completed,
                "cutoff_outcome": "HARNESS_CUTOFF_PRE_ADMISSION",
                "offered_operations": assembler.SATURATION_OFFERS_PER_BLOCK,
                "unadmitted_at_cutoff": (
                    assembler.SATURATION_OFFERS_PER_BLOCK - saturation_completed
                ),
                "window_seconds": 3,
            }
            for index in range(2)
        ],
        "saturation_request_schedule": saturation_request_schedule,
        "schema_version": "1.0.0",
        "source": {"commit": "1" * 40, "tree": "2" * 40},
        "timer_order": [{"ordinal": 0, "timer_token_sha256": content_id("timer:0")}],
        "toolchains_sha256": content_id("toolchains"),
        "type_name": assembler.RUN_TYPE,
        "wal_artifacts": wal_artifacts,
        "warmup_completed_operations": aggregation["warmup_operations"],
    }
    runtime_stats = {
        "duplicate_response_count": 0,
        "rejected_frame_count": 0,
        "retry_count": len(target_request_ids) + (2 * saturation_completed),
        "stale_response_count": 0,
    }
    run["runtime_stats"] = runtime_stats
    fixed_artifact = gate.sha256_id(gate.canonical_bytes(run["fixed_load_blocks"]))
    saturation_artifact = gate.sha256_id(gate.canonical_bytes(run["saturation_blocks"]))
    crash_document = {
        "java_process_survival": survival,
        "profile_id": profile,
        "restart_to_ready": restart,
        "schema_version": "1.0.0",
        "type_name": "FEATURE010_SIDECAR_CRASH_OBSERVATIONS",
    }
    crash_artifact = gate.sha256_id(gate.canonical_bytes(crash_document))
    transcript_artifact = gate.sha256_id(
        gate.canonical_bytes(
            {record["equality_id"]: record["transcript_sha256"] for record in transcripts}
        )
    )
    runtime_stats_artifact = gate.sha256_id(gate.canonical_bytes(runtime_stats))
    measurement_specs = {
        "END_TO_END_LATENCY_NS": (fixed_artifact, "ALL_FIXED_LOAD_SAMPLES_PRESENT", {}),
        "PHASE_LATENCY_NS": (fixed_artifact, "ALL_FIXED_LOAD_SAMPLES_PRESENT", {}),
        "FIXED_LOAD_THROUGHPUT_OPS_PER_WINDOW": (
            fixed_artifact,
            "ALL_FIXED_LOAD_SAMPLES_PRESENT",
            {},
        ),
        "SATURATION_THROUGHPUT_OPS_PER_WINDOW": (
            saturation_artifact,
            "ALL_SATURATION_WINDOWS_PRESENT",
            {
                "executed_corpus_prefix_operations": deterministic_count,
                "request_order_scope": "FULL_DLTSTRC1_ORDERED_INPUT_CORPUS",
            },
        ),
        "RESTART_TO_READY_NS": (crash_artifact, "INDEPENDENT_CRASH_RECEIPTS_IMPORTED", {}),
        "JAVA_PROCESS_SURVIVAL": (crash_artifact, "PROFILE_BOUNDARY_SURVIVAL_REPORTED", {}),
        "STATE_EFFECT_WAL_REPLAY_IDENTITY": (
            transcript_artifact,
            "CONCRETE_TRANSCRIPTS_CAPTURED",
            {},
        ),
        "RETRY_COUNT": (
            runtime_stats_artifact,
            "EXACT_REPLAYS_COMPLETED",
            {"value": runtime_stats["retry_count"]},
        ),
        "DUPLICATE_RESPONSE_COUNT": (
            runtime_stats_artifact,
            "CLIENT_COUNTER_CAPTURED",
            {"value": 0},
        ),
        "STALE_RESPONSE_COUNT": (
            runtime_stats_artifact,
            "CLIENT_COUNTER_CAPTURED",
            {"value": 0},
        ),
        "REJECTED_FRAME_COUNT": (
            runtime_stats_artifact,
            "CLIENT_COUNTER_CAPTURED",
            {"value": 0},
        ),
    }
    for measurement_id in comparison["required_measurements"]:
        artifact, check, extra = measurement_specs[measurement_id]
        observations = {"measurement_id": measurement_id, "profile_id": profile, **extra}
        measurements.append(
            {
                "measurement_id": measurement_id,
                **evidence_record(
                    f"{profile}:measurement:{measurement_id}",
                    observations,
                    checks={check: True},
                    artifact_sha256=artifact,
                ),
            }
        )

    native_artifact_id = "NATIVE_LIBRARY" if embedded else "SIDECAR_EXECUTABLE"
    option_paths = {
        "CORPUS": ("--corpus", f"C:/capture/{profile}/corpus.bin"),
        "CRASH_OBSERVATIONS": ("--crash-observations", f"C:/capture/{profile}/crash.json"),
        "FROZEN_DESIGN": ("--design", "C:/capture/design.json"),
        "HARDWARE_ALLOCATION": ("--hardware-allocation", "C:/capture/hardware.json"),
        "NATIVE_CORE": ("--native-core", "C:/capture/native-core.json"),
        "PAIRED_CORE_FAULT_TRACE": ("--fault-trace", "C:/capture/fault-trace.json"),
        "PROJECTED_FORMAL_TRACE": (
            "--projected-formal-trace",
            f"C:/capture/{profile}/formal.json",
        ),
        "TOOLCHAINS": ("--toolchains", "C:/capture/toolchains.json"),
        "VOTE_FIXTURE": ("--vote-fixture", "C:/capture/vote-fixture.bin"),
        native_artifact_id: (
            "--native-library" if embedded else "--sidecar-executable",
            f"C:/capture/{profile}/native.bin",
        ),
    }
    artifact_hashes = {
        "CORPUS": run["canonical_input_trace_sha256"],
        "CRASH_OBSERVATIONS": crash_artifact,
        "FROZEN_DESIGN": run["design_sha256"],
        "HARDWARE_ALLOCATION": run["hardware_allocation_sha256"],
        "NATIVE_CORE": run["native_core_sha256"],
        "PAIRED_CORE_FAULT_TRACE": run["fault_trace_sha256"],
        "PROJECTED_FORMAL_TRACE": content_id(f"{profile}:formal-receipt"),
        "TOOLCHAINS": run["toolchains_sha256"],
        "VOTE_FIXTURE": content_id("canonical-vote-fixture"),
        native_artifact_id: content_id(f"{profile}:native-runtime"),
    }
    artifacts = [
        {
            "artifact_id": artifact_id,
            "path": option_paths[artifact_id][1],
            "sha256": artifact_hashes[artifact_id],
            "size_bytes": index + 1,
        }
        for index, artifact_id in enumerate(option_paths)
    ]
    native_artifact = artifacts[-1]
    tools = [
        {
            "path": "C:/tools/git.exe",
            "sha256": content_id("git-tool"),
            "size_bytes": 101,
            "tool_id": "GIT",
            "version": "git version 2.test",
        },
        {
            "path": "C:/tools/java.exe",
            "sha256": content_id("java-tool"),
            "size_bytes": 102,
            "tool_id": "JAVA_RUNTIME",
            "version": "25-test",
        },
        {
            "path": native_artifact["path"],
            "sha256": native_artifact["sha256"],
            "size_bytes": native_artifact["size_bytes"],
            "tool_id": "NATIVE_RUNTIME",
            "version": content_id("native-build"),
        },
    ]
    runner = {
        "argv": ["prepare", profile],
        "ended_at_utc": "2026-01-01T00:01:00Z",
        "path": f"C:/capture/{profile}/prepare.log",
        "runner_id": "PREPARE",
        "sha256": content_id(f"{profile}:prepare-log"),
        "size_bytes": 103,
        "started_at_utc": "2026-01-01T00:00:00Z",
        "tool_id": "JAVA_RUNTIME",
    }
    argv: list[str] = []
    option_values = {
        "--profile": profile,
        "--corpus": option_paths["CORPUS"][1],
        "--design": option_paths["FROZEN_DESIGN"][1],
        "--output": f"C:/capture/{profile}/raw.json",
        "--durable-directory": f"C:/capture/{profile}/durable",
        "--source-commit": run["source"]["commit"],
        "--source-tree": run["source"]["tree"],
        "--hardware-allocation": option_paths["HARDWARE_ALLOCATION"][1],
        "--toolchains": option_paths["TOOLCHAINS"][1],
        "--vote-fixture": option_paths["VOTE_FIXTURE"][1],
        "--native-core": option_paths["NATIVE_CORE"][1],
        "--fault-trace": option_paths["PAIRED_CORE_FAULT_TRACE"][1],
        "--projected-formal-trace": option_paths["PROJECTED_FORMAL_TRACE"][1],
        "--crash-observations": option_paths["CRASH_OBSERVATIONS"][1],
        "--input-provenance": f"C:/capture/{profile}/provenance.json",
        option_paths[native_artifact_id][0]: option_paths[native_artifact_id][1],
    }
    for option, option_value in option_values.items():
        argv.extend([option, option_value])
    provenance = {
        "capture_plan": {
            "argv": argv,
            "output_path": option_values["--output"],
            "profile_id": profile,
        },
        "hardware_identity": {
            "allocation_artifact_sha256": run["hardware_allocation_sha256"],
            "available_processors": 8,
            "os_arch": "test-arch",
            "os_name": "test-os",
            "os_version": "test-version",
        },
        "input_artifacts": artifacts,
        "preparation_ended_at_utc": "2026-01-01T00:01:00Z",
        "preparation_started_at_utc": "2026-01-01T00:00:00Z",
        "runner_logs": [runner],
        "schema_version": "1.0.0",
        "source": {**run["source"], "tracked_clean": True},
        "tools": tools,
        "type_name": "FEATURE010_CAPTURE_INPUT_PROVENANCE",
    }
    provenance_sha256 = gate.sha256_id(gate.canonical_bytes(provenance))
    graph_nodes = [
        {
            "artifact_sha256": record["sha256"],
            "node_id": f"INPUT:{record['artifact_id']}",
            "provenance_sha256": provenance_sha256,
            "size_bytes": record["size_bytes"],
        }
        for record in artifacts
    ]
    graph_nodes.extend(
        {
            "artifact_sha256": record["sha256"],
            "node_id": f"TOOL:{record['tool_id']}",
            "provenance_sha256": provenance_sha256,
            "size_bytes": record["size_bytes"],
        }
        for record in tools
    )
    graph_nodes.append(
        {
            "artifact_sha256": runner["sha256"],
            "node_id": f"RUNNER_LOG:{runner['runner_id']}",
            "provenance_sha256": provenance_sha256,
            "size_bytes": runner["size_bytes"],
        }
    )
    run["input_graph_nodes"] = graph_nodes
    run["input_provenance"] = provenance
    run["input_provenance_sha256"] = provenance_sha256
    return run


def rebind_input_artifact(
    run: dict[str, object],
    artifact_id: str,
    artifact_sha256: str,
    *,
    size_bytes: int | None = None,
) -> None:
    provenance = run["input_provenance"]
    assert isinstance(provenance, dict)
    artifacts = provenance["input_artifacts"]
    assert isinstance(artifacts, list)
    artifact = next(item for item in artifacts if item["artifact_id"] == artifact_id)
    artifact["sha256"] = artifact_sha256
    if size_bytes is not None:
        artifact["size_bytes"] = size_bytes
    if artifact_id == "HARDWARE_ALLOCATION":
        provenance["hardware_identity"]["allocation_artifact_sha256"] = artifact_sha256

    provenance_sha256 = gate.sha256_id(gate.canonical_bytes(provenance))
    run["input_provenance_sha256"] = provenance_sha256
    graph_nodes = run["input_graph_nodes"]
    assert isinstance(graph_nodes, list)
    for node in graph_nodes:
        node["provenance_sha256"] = provenance_sha256
        if node["node_id"] == f"INPUT:{artifact_id}":
            node["artifact_sha256"] = artifact_sha256
            if size_bytes is not None:
                node["size_bytes"] = size_bytes


def rebind_crash_artifact(run: dict[str, object]) -> None:
    crash_document = {
        "java_process_survival": run["java_process_survival"],
        "profile_id": run["profile_id"],
        "restart_to_ready": run["restart_to_ready"],
        "schema_version": "1.0.0",
        "type_name": "FEATURE010_SIDECAR_CRASH_OBSERVATIONS",
    }
    crash_sha256 = gate.sha256_id(gate.canonical_bytes(crash_document))
    for measurement in run["measurements"]:
        if measurement["measurement_id"] in {"RESTART_TO_READY_NS", "JAVA_PROCESS_SURVIVAL"}:
            measurement["evidence"]["artifact_sha256"] = crash_sha256
            rehash(measurement)
    rebind_input_artifact(run, "CRASH_OBSERVATIONS", crash_sha256)


def rebind_transcript_artifact(run: dict[str, object]) -> None:
    transcripts = run["output_transcripts"]
    artifact_sha256 = gate.sha256_id(
        gate.canonical_bytes(
            {record["equality_id"]: record["transcript_sha256"] for record in transcripts}
        )
    )
    measurement = next(
        item
        for item in run["measurements"]
        if item["measurement_id"] == "STATE_EFFECT_WAL_REPLAY_IDENTITY"
    )
    measurement["evidence"]["artifact_sha256"] = artifact_sha256
    rehash(measurement)


def rebind_wal_transcript(run: dict[str, object]) -> None:
    transcript = next(
        item
        for item in run["output_transcripts"]
        if item["equality_id"] == "WAL_RECEIPTS_AND_DURABLE_SEQUENCES"
    )
    transcript_sha256 = gate.sha256_id(gate.canonical_bytes(run["wal_artifacts"]))
    transcript["transcript_sha256"] = transcript_sha256
    transcript["evidence"]["artifact_sha256"] = transcript_sha256
    transcript["evidence"]["observations"]["transcript_sha256"] = transcript_sha256
    rehash(transcript)
    rebind_transcript_artifact(run)


def rebind_copy_accounting(run: dict[str, object]) -> None:
    samples = run["operation_copy_samples"]
    counters = run["copy_accounting"]
    totals = {
        record["counter_id"]: sum(int(sample[record["counter_id"]]) for sample in samples)
        for record in counters
    }
    totals_artifact = gate.sha256_id(gate.canonical_bytes(totals))
    for record in counters:
        counter_id = record["counter_id"]
        value = totals[counter_id]
        record["value"] = value
        record["evidence"]["artifact_sha256"] = totals_artifact
        record["evidence"]["observations"]["value"] = value
        rehash(record)


def crash_evidence(profile: str, crash_point: str, survived: bool) -> dict[str, object]:
    observations: dict[str, object] = {
        "crash_point": crash_point,
        "java_process_survived": survived,
        "journal_recovered_before_admission": True,
        "partial_response_exposed": False,
        "persist_before_expose": True,
        "profile_id": profile,
        "replay_identity_exact": True,
    }
    checks = None
    if crash_point == "DURING_SHARED_MEMORY_PUBLICATION":
        observations["failed_generation_stdout_bytes_after_submit"] = 256
        observations.update(
            {
                "atomic_abi_probe_result": "LOCK_FREE_JAVA_NATIVE_MAP_SHARED_U32_BIG_ENDIAN",
                "atomic_abi_probe_scope": "EXACT_PATH_DEVICE_INODE_GENERATION_SLOT",
                "atomic_abi_supported": True,
                "bounded_copy_equivalence": "EXACT",
                "crash_process_exit_code": 88,
                "duration_ns": 1_000,
                "fallback_transport": "NOT_USED",
                "shared_memory_admission_state": "ADMITTED_OUTCOME_AVAILABLE",
                "shared_memory_admitted_sequence": 2,
                "shared_memory_admitted_sequence_derivation": (
                    "OBSERVED_OPEN_ADMISSION_PLUS_FIRST_POST_OPEN_OPERATION"
                ),
                "shared_memory_control_frame_exposed": True,
                "shared_memory_egress_bytes": 4096,
                "shared_memory_enabled": True,
                "shared_memory_failed_generation_egress_control_bytes": 256,
                "shared_memory_failed_generation_operation_response_wire_bytes": 0,
                "shared_memory_failed_generation_response_carrier_count": 0,
                "shared_memory_failed_generation_response_frame_count": 0,
                "shared_memory_ingress_bytes": 4096,
                "shared_memory_ingress_ack_frame_count": 1,
                "shared_memory_native_call_count": 1,
                "shared_memory_native_status": 0,
                "shared_memory_notification_ack_inline_only": True,
                "shared_memory_operation_response_frame_exposed": False,
                "shared_memory_open_admitted_sequence": 1,
                "shared_memory_publication_completed": False,
                "shared_memory_publication_started": True,
                "shared_memory_region_id": "NATIVE_TO_JAVA",
                "shared_memory_slot_state_at_native_death": "WRITING",
                "shared_memory_status": "ENABLED_LOCK_FREE_U32_BIG_ENDIAN",
                "shared_memory_telemetry_scope": "SUPERVISOR_ALL_GENERATIONS",
                "validated_response_count_before_recovery": 0,
                "zero_copy_eligible_count": 2,
                "zero_copy_hit_count": 0,
            }
        )
        checks = {check_id: True for check_id in assembler.SHM_PUBLICATION_CHECKS}
    return evidence_record(f"{profile}:crash:{crash_point}", observations, checks)


def manifest(
    design: dict[str, Any],
    embedded_run: dict[str, object],
    sidecar_run: dict[str, object],
) -> dict[str, object]:
    comparison = design["comparison_plan"]
    paired = []
    for crash_point in comparison["paired_crash_points"]:
        embedded = crash_evidence("EMBEDDED_FFM", crash_point, False)
        sidecar = crash_evidence("ISOLATED_SIDECAR", crash_point, True)
        paired.append(
            {
                "crash_point": crash_point,
                "embedded_evidence": embedded["evidence"],
                "embedded_evidence_sha256": embedded["evidence_sha256"],
                "sidecar_evidence": sidecar["evidence"],
                "sidecar_evidence_sha256": sidecar["evidence_sha256"],
            }
        )
    supplemental = []
    for crash_point in comparison["sidecar_supplemental_crash_points"]:
        supplemental.append(
            {
                "crash_point": crash_point,
                **crash_evidence("ISOLATED_SIDECAR", crash_point, True),
            }
        )

    sidecar_nodes = sidecar_run["input_graph_nodes"]
    sidecar_binary = next(
        node["artifact_sha256"]
        for node in sidecar_nodes
        if node["node_id"] == "INPUT:SIDECAR_EXECUTABLE"
    )
    conformance_log = next(
        node["artifact_sha256"]
        for node in sidecar_nodes
        if node["node_id"].startswith("RUNNER_LOG:")
    )

    def gate_records(ids: list[str]) -> list[dict[str, object]]:
        records = []
        for gate_id in ids:
            observations: dict[str, object] = {"gate_id": gate_id}
            artifact_sha256 = None
            if gate_id in assembler.CONFORMANCE_TEST_IDS:
                observations = {
                    "binary_sha256": sidecar_binary,
                    "exit_code": 0,
                    "gate_id": gate_id,
                    "raw_log_sha256": conformance_log,
                    "receipt_type": assembler.CONFORMANCE_RECEIPT_TYPE,
                    "source_commit": embedded_run["source"]["commit"],
                    "source_tree": embedded_run["source"]["tree"],
                    "test_id": assembler.CONFORMANCE_TEST_IDS[gate_id],
                }
                artifact_sha256 = conformance_log
            records.append(
                {
                    "gate_id": gate_id,
                    **evidence_record(
                        f"gate:{gate_id}", observations, artifact_sha256=artifact_sha256
                    ),
                }
            )
        return records

    return {
        "common_hard_gates": gate_records(comparison["hard_gates_common"]),
        "crash_coverage": {"paired": paired, "sidecar_supplemental": supplemental},
        "design_canonical_id": gate.EXPECTED_DESIGN_CANONICAL_ID,
        "design_sha256": gate.EXPECTED_DESIGN_SHA256,
        "execution_class": assembler.EXECUTION_CLASS,
        "formal_semantics_id": gate.FORMAL_ID,
        "schema_version": "1.0.0",
        "sidecar_hard_gates": gate_records(comparison["hard_gates_sidecar"]),
        "type_name": assembler.MANIFEST_TYPE,
    }


def install_compact_validator(monkeypatch: pytest.MonkeyPatch) -> list[dict[str, object]]:
    calls: list[dict[str, object]] = []

    def validate(document: dict[str, object], design: dict[str, object]) -> dict[str, object]:
        calls.append({"design": design, "document": document})
        return {"selected_profile": "ISOLATED_SIDECAR", "status": "PASS"}

    monkeypatch.setattr(assembler.gate, "validate_evidence", validate)
    return calls


def assembled_fixture(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[
    dict[str, Any], dict[str, object], dict[str, object], dict[str, object], list[dict[str, object]]
]:
    design = small_design()
    embedded = raw_run("EMBEDDED_FFM", design)
    sidecar = raw_run("ISOLATED_SIDECAR", design)
    gates = manifest(design, embedded, sidecar)
    calls = install_compact_validator(monkeypatch)
    return design, embedded, sidecar, gates, calls


def test_assembler_derives_nearest_rank_and_calls_compact_gate_last(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)

    compact, result = assembler.assemble_comparison(
        embedded, sidecar, gates, _design_override=design
    )

    assert result == {"selected_profile": "ISOLATED_SIDECAR", "status": "PASS"}
    assert len(calls) == 1
    assert calls[0]["document"] is compact
    assert compact["profiles"][0]["fixed_load_latency_ns"] == {
        "p50": 30,
        "p95": 100,
        "p99": 100,
        "sample_count": 6,
    }
    assert compact["profiles"][1]["fixed_load_latency_ns"] == {
        "p50": 36,
        "p95": 120,
        "p99": 120,
        "sample_count": 6,
    }
    assert compact["profiles"][1]["max_staging_fallback"] == {
        "egress_bytes": 6,
        "ingress_bytes": 4,
        "operation_count_scanned": 16,
        "operation_id": "ISOLATED_SIDECAR-operation-0",
        "total_bytes": 10,
    }
    assert all(item["status"] == "EXACT" for item in compact["pair_fields"])
    assert all(item["status"] == "EXACT" for item in compact["semantic_equalities"])
    assert "latency_ns" not in compact["profiles"][0]["fixed_load_blocks"][0]
    for run in (embedded, sidecar):
        artifacts = run["input_provenance"]["input_artifacts"]
        artifact_ids = [item["artifact_id"] for item in artifacts]
        assert artifact_ids[-3:-1] == ["TOOLCHAINS", "VOTE_FIXTURE"]
        argv = run["input_provenance"]["capture_plan"]["argv"]
        vote_option = argv.index("--vote-fixture")
        assert argv[vote_option + 1] == next(
            item["path"] for item in artifacts if item["artifact_id"] == "VOTE_FIXTURE"
        )


def test_vote_fixture_is_a_required_provenance_artifact(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)
    provenance = sidecar["input_provenance"]
    provenance["input_artifacts"] = [
        item for item in provenance["input_artifacts"] if item["artifact_id"] != "VOTE_FIXTURE"
    ]
    provenance_sha256 = gate.sha256_id(gate.canonical_bytes(provenance))
    sidecar["input_provenance_sha256"] = provenance_sha256
    for node in sidecar["input_graph_nodes"]:
        node["provenance_sha256"] = provenance_sha256

    with pytest.raises(gate.ComparisonError, match="INPUT_ARTIFACT_COUNT"):
        assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert calls == []


def test_vote_fixture_provenance_cannot_describe_empty_bytes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)
    provenance = sidecar["input_provenance"]
    fixture = next(
        item for item in provenance["input_artifacts"] if item["artifact_id"] == "VOTE_FIXTURE"
    )
    fixture["sha256"] = assembler.EMPTY_SHA256
    fixture["size_bytes"] = 0
    provenance_sha256 = gate.sha256_id(gate.canonical_bytes(provenance))
    sidecar["input_provenance_sha256"] = provenance_sha256
    for node in sidecar["input_graph_nodes"]:
        node["provenance_sha256"] = provenance_sha256
        if node["node_id"] == "INPUT:VOTE_FIXTURE":
            node["artifact_sha256"] = assembler.EMPTY_SHA256
            node["size_bytes"] = 0

    with pytest.raises(gate.ComparisonError, match="VOTE_FIXTURE_EMPTY"):
        assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert calls == []


@pytest.mark.parametrize("field", ["sha256", "size_bytes"])
def test_vote_fixture_sha_and_size_are_exact_pair_inputs(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
) -> None:
    design, embedded, sidecar, gates, _ = assembled_fixture(monkeypatch)
    fixture = next(
        item
        for item in sidecar["input_provenance"]["input_artifacts"]
        if item["artifact_id"] == "VOTE_FIXTURE"
    )
    if field == "sha256":
        rebind_input_artifact(
            sidecar,
            "VOTE_FIXTURE",
            content_id("different-vote-fixture"),
        )
    else:
        rebind_input_artifact(
            sidecar,
            "VOTE_FIXTURE",
            fixture["sha256"],
            size_bytes=fixture["size_bytes"] + 1,
        )

    compact, _ = assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    canonical_input = next(
        item for item in compact["pair_fields"] if item["field_id"] == "CANONICAL_INPUT_BYTES"
    )
    assert canonical_input["status"] == "MISMATCH"
    assert canonical_input["embedded_sha256"] != canonical_input["sidecar_sha256"]


def test_vote_receipt_transcript_cannot_be_sha256_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)
    for run in (embedded, sidecar):
        transcript = next(
            item
            for item in run["output_transcripts"]
            if item["equality_id"] == "CANONICAL_VOTE_RECEIPT_BYTES"
        )
        transcript["transcript_sha256"] = assembler.EMPTY_SHA256
        transcript["evidence"]["artifact_sha256"] = assembler.EMPTY_SHA256
        transcript["evidence"]["observations"]["transcript_sha256"] = assembler.EMPTY_SHA256
        rehash(transcript)
        rebind_transcript_artifact(run)

    with pytest.raises(gate.ComparisonError, match="RAW_VOTE_RECEIPT_TRANSCRIPT_EMPTY"):
        assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert calls == []


def test_vote_wal_record_is_bound_to_wal_transcript(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)
    sidecar["wal_artifacts"]["record_vote"]["sha256"] = content_id("mutated-vote-wal")

    with pytest.raises(gate.ComparisonError, match="RAW_WAL_TRANSCRIPT_BINDING"):
        assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert calls == []


def test_vote_wal_sha_and_size_participate_in_cross_profile_equality(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, _ = assembled_fixture(monkeypatch)
    record_vote = sidecar["wal_artifacts"]["record_vote"]
    record_vote["sha256"] = content_id("different-vote-wal")
    record_vote["size_bytes"] += 1
    rebind_wal_transcript(sidecar)

    compact, _ = assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    equality = next(
        item
        for item in compact["semantic_equalities"]
        if item["equality_id"] == "WAL_RECEIPTS_AND_DURABLE_SEQUENCES"
    )
    assert equality["status"] == "MISMATCH"
    assert equality["embedded_sha256"] != equality["sidecar_sha256"]
    assert compact["profiles"][1]["wal_artifacts"]["record_vote"] == record_vote


def test_raw_latency_count_fails_before_compact_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)
    sidecar["fixed_load_blocks"][0]["latency_ns"].pop()

    with pytest.raises(gate.ComparisonError, match="RAW_LATENCY_BLOCK_COUNT"):
        assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert calls == []


def test_pair_and_transcript_mismatches_are_derived(monkeypatch: pytest.MonkeyPatch) -> None:
    design, embedded, sidecar, gates, _ = assembled_fixture(monkeypatch)
    sidecar["hardware_allocation_sha256"] = content_id("different-hardware")
    rebind_input_artifact(sidecar, "HARDWARE_ALLOCATION", sidecar["hardware_allocation_sha256"])
    transcript = sidecar["output_transcripts"][0]
    transcript["transcript_sha256"] = content_id("different-transcript")
    transcript["evidence"]["artifact_sha256"] = transcript["transcript_sha256"]
    transcript["evidence"]["observations"]["transcript_sha256"] = transcript["transcript_sha256"]
    rehash(transcript)
    rebind_transcript_artifact(sidecar)

    compact, _ = assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    hardware = next(
        item for item in compact["pair_fields"] if item["field_id"] == "HARDWARE_ALLOCATION"
    )
    equality = compact["semantic_equalities"][0]
    assert hardware["status"] == "MISMATCH"
    assert hardware["embedded_sha256"] != hardware["sidecar_sha256"]
    assert equality["status"] == "MISMATCH"
    assert equality["embedded_sha256"] != equality["sidecar_sha256"]


def test_exact_request_retry_is_ordered_but_conflicting_reuse_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, _ = assembled_fixture(monkeypatch)
    retry_ordinal = len(embedded["request_order"])
    exact_retry = {
        "canonical_request_sha256": content_id("request:0"),
        "ordinal": retry_ordinal,
        "request_id": "request-0",
    }
    embedded["request_order"].append(copy.deepcopy(exact_retry))
    sidecar["request_order"].append(copy.deepcopy(exact_retry))

    compact, _ = assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)
    request_pair = next(
        item for item in compact["pair_fields"] if item["field_id"] == "REQUEST_IDS_AND_ORDER"
    )
    assert request_pair["status"] == "EXACT"

    sidecar["request_order"][retry_ordinal]["canonical_request_sha256"] = content_id(
        "conflicting-body"
    )
    with pytest.raises(gate.ComparisonError, match="REQUEST_ID_BODY_CONFLICT"):
        assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)


def test_declared_evidence_hash_is_recomputed(monkeypatch: pytest.MonkeyPatch) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)
    sidecar["measurements"][0]["evidence"]["observations"]["profile_id"] = "MUTATED"

    with pytest.raises(gate.ComparisonError, match="RAW_MEASUREMENT_EVIDENCE_SHA256"):
        assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert calls == []


def test_manifest_cannot_assert_status_and_run_gate_ignores_manifest_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, _ = assembled_fixture(monkeypatch)
    gates["common_hard_gates"][0]["status"] = "PASS"
    with pytest.raises(gate.ComparisonError, match="MANIFEST_GATE_FIELDS"):
        assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    gates = manifest(design, embedded, sidecar)
    first = gates["common_hard_gates"][0]
    first["evidence"]["checks"]["OBSERVATION_VERIFIED"] = False
    rehash(first)
    compact, _ = assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)
    assert compact["common_hard_gates"][0]["status"] == "PASS"


def test_hand_authored_true_check_cannot_promote_run_derived_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, _ = assembled_fixture(monkeypatch)
    transcript = sidecar["output_transcripts"][0]
    transcript["transcript_sha256"] = content_id("different-status-transcript")
    transcript["evidence"]["artifact_sha256"] = transcript["transcript_sha256"]
    transcript["evidence"]["observations"]["transcript_sha256"] = transcript["transcript_sha256"]
    rehash(transcript)
    rebind_transcript_artifact(sidecar)
    asserted = gates["common_hard_gates"][0]
    assert all(asserted["evidence"]["checks"].values())

    compact, _ = assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert compact["common_hard_gates"][0]["status"] == "FAIL"


@pytest.mark.parametrize(
    "mutation",
    [
        "legacy",
        "unknown_test",
        "nonzero_exit",
        "wrong_source",
        "unrooted_binary",
        "unrooted_log",
    ],
)
def test_hand_authored_true_check_cannot_promote_conformance_gate(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    design, embedded, sidecar, gates, _ = assembled_fixture(monkeypatch)
    gate_id = "DESCRIPTOR_VERSION_AND_IDENTITY_MISMATCH_FAIL_CLOSED"
    record = next(item for item in gates["common_hard_gates"] if item["gate_id"] == gate_id)
    evidence = record["evidence"]
    if mutation == "legacy":
        evidence["observations"] = {"gate_id": gate_id}
    elif mutation == "unknown_test":
        evidence["observations"]["test_id"] = "hand-authored-all-green"
    elif mutation == "nonzero_exit":
        evidence["observations"]["exit_code"] = 1
    elif mutation == "wrong_source":
        evidence["observations"]["source_commit"] = "3" * 40
    elif mutation == "unrooted_binary":
        evidence["observations"]["binary_sha256"] = content_id("unrooted-conformance-binary")
    else:
        unrooted = content_id("unrooted-conformance-log")
        evidence["observations"]["raw_log_sha256"] = unrooted
        evidence["artifact_sha256"] = unrooted
    evidence["checks"] = {"HAND_AUTHORED_ALL_GREEN": True}
    rehash(record)

    compact, _ = assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    result = next(item for item in compact["common_hard_gates"] if item["gate_id"] == gate_id)
    assert result["status"] == "FAIL"


def test_measurement_and_crash_statuses_are_derived_from_evidence_checks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, _ = assembled_fixture(monkeypatch)
    measurement = sidecar["measurements"][0]
    check_id = next(iter(measurement["evidence"]["checks"]))
    measurement["evidence"]["checks"][check_id] = False
    rehash(measurement)
    crash = gates["crash_coverage"]["paired"][0]
    crash["sidecar_evidence"]["checks"]["OBSERVATION_VERIFIED"] = False
    rehash(crash, "sidecar_")

    compact, _ = assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert compact["profiles"][1]["measurement_coverage"][0]["status"] == "MISSING"
    assert compact["crash_coverage"]["paired"][0]["status"] == "FAIL"


def test_shared_memory_publication_requires_real_lock_free_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)
    special = gates["crash_coverage"]["sidecar_supplemental"][1]
    special["evidence"]["observations"]["atomic_abi_supported"] = False
    rehash(special)

    with pytest.raises(gate.ComparisonError, match="SHM_ATOMIC_ABI"):
        assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert calls == []


def test_shared_memory_publication_accepts_mapped_copy_without_zero_copy_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)
    special = gates["crash_coverage"]["sidecar_supplemental"][1]
    assert special["evidence"]["observations"]["zero_copy_hit_count"] == 0

    compact, _ = assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert compact["crash_coverage"]["sidecar_supplemental"][1]["status"] == "PASS"
    assert len(calls) == 1


def test_shared_memory_publication_rejects_zero_copy_hit_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)
    special = gates["crash_coverage"]["sidecar_supplemental"][1]
    special["evidence"]["observations"]["zero_copy_hit_count"] = 1
    rehash(special)

    with pytest.raises(gate.ComparisonError, match="SHM_ZERO_COPY_HIT_FORBIDDEN"):
        assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert calls == []


def test_shared_memory_publication_accepts_production_admission_sequence_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)
    special = gates["crash_coverage"]["sidecar_supplemental"][1]
    observations = special["evidence"]["observations"]
    assert observations["shared_memory_open_admitted_sequence"] == 1
    assert observations["shared_memory_admitted_sequence"] == 2
    assert (
        observations["shared_memory_admitted_sequence_derivation"]
        == "OBSERVED_OPEN_ADMISSION_PLUS_FIRST_POST_OPEN_OPERATION"
    )
    assert observations["shared_memory_telemetry_scope"] == "SUPERVISOR_ALL_GENERATIONS"

    compact, _ = assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert compact["crash_coverage"]["sidecar_supplemental"][1]["status"] == "PASS"
    assert len(calls) == 1


def test_shared_memory_assembler_contract_matches_production_capture_source() -> None:
    source = JAVA_CRASH_QUALIFICATION.read_text(encoding="utf-8")
    production_observations = set(re.findall(r'observations\.put\(\s*"([A-Za-z0-9_]+)"', source))
    production_checks = set(re.findall(r'checks\.put\("([A-Z0-9_]+)"', source))

    assert assembler.SHM_PUBLICATION_OBSERVATION_FIELDS <= production_observations
    assert assembler.SHM_PUBLICATION_CHECKS <= production_checks
    assert "failedGenerationOpenAdmissionSequence == 1L" in source
    assert "failedGenerationSubmitAdmissionSequence == 2L" in source
    assert "OBSERVED_OPEN_ADMISSION_PLUS_FIRST_POST_OPEN_OPERATION" in source
    assert (
        'observations.put("shared_memory_telemetry_scope", "SUPERVISOR_ALL_GENERATIONS")' in source
    )


def test_shared_memory_publication_requires_production_derivation_check(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)
    special = gates["crash_coverage"]["sidecar_supplemental"][1]
    special["evidence"]["checks"].pop("SHARED_MEMORY_ADMISSION_SEQUENCE_DERIVED")
    rehash(special)

    with pytest.raises(gate.ComparisonError, match="SHM_PUBLICATION_CHECKS"):
        assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert calls == []


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("shared_memory_admitted_sequence", 1, "SHM_ADMITTED_OUTCOME"),
        ("shared_memory_open_admitted_sequence", 2, "SHM_ADMITTED_OUTCOME"),
        ("shared_memory_admitted_sequence_derivation", "ASSUMED", "SHM_ADMITTED_OUTCOME"),
        ("shared_memory_telemetry_scope", "FAILED_GENERATION_ONLY", "SHM_TELEMETRY_SCOPE"),
    ],
)
def test_shared_memory_publication_rejects_nonproduction_sequence_evidence(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    value: object,
    error: str,
) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)
    special = gates["crash_coverage"]["sidecar_supplemental"][1]
    special["evidence"]["observations"][field] = value
    rehash(special)

    with pytest.raises(gate.ComparisonError, match=error):
        assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert calls == []


@pytest.mark.parametrize(
    ("field", "error"),
    [
        ("shared_memory_ingress_bytes", "SHM_INGRESS_BYTES"),
        ("shared_memory_egress_bytes", "SHM_EGRESS_BYTES"),
    ],
)
def test_shared_memory_publication_still_requires_positive_mapped_traffic(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    error: str,
) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)
    special = gates["crash_coverage"]["sidecar_supplemental"][1]
    special["evidence"]["observations"][field] = 0
    rehash(special)

    with pytest.raises(gate.ComparisonError, match=error):
        assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert calls == []


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        ("copy_sum", "RAW_COPY_COUNTER_SUM"),
        ("copy_order", "RAW_COPY_COUNTER_ORDER"),
        ("restart_count", "RAW_RESTART_COUNT"),
    ],
)
def test_copy_counter_order_sums_and_restart_count_are_exact(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
    error: str,
) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)
    if mutation == "copy_sum":
        sidecar["copy_accounting"][0]["value"] += 1
    elif mutation == "copy_order":
        sidecar["copy_accounting"][0], sidecar["copy_accounting"][1] = (
            sidecar["copy_accounting"][1],
            sidecar["copy_accounting"][0],
        )
    else:
        sidecar["restart_to_ready"].pop()

    with pytest.raises(gate.ComparisonError, match=error):
        assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert calls == []


def test_operation_copy_ledger_rejects_zero_copy_hit_claim(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)
    sidecar["operation_copy_samples"][0]["ZERO_COPY_HIT_COUNT"] = 1
    rebind_copy_accounting(sidecar)

    with pytest.raises(gate.ComparisonError, match="COPY_SAMPLE_ZERO_COPY_HIT_FORBIDDEN"):
        assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert calls == []


def test_survival_summary_must_equal_concrete_crash_observations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)
    survival = sidecar["java_process_survival"]
    survival["survived_all_native_deaths"] = False
    survival["evidence"]["observations"]["survived_all_native_deaths"] = False
    rehash(survival)
    rebind_crash_artifact(sidecar)

    with pytest.raises(gate.ComparisonError, match="SIDECAR_SURVIVAL_AGGREGATE"):
        assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert calls == []


def test_shared_memory_publication_is_counted_as_a_native_death(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)
    survival = sidecar["java_process_survival"]
    survival["evidence"]["observations"]["native_death_injection_count"] += 1
    rehash(survival)

    with pytest.raises(gate.ComparisonError, match="RAW_SURVIVAL_OBSERVATION"):
        assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert calls == []


def test_shared_memory_publication_manifest_retains_measured_duration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    design, embedded, sidecar, gates, calls = assembled_fixture(monkeypatch)
    special = gates["crash_coverage"]["sidecar_supplemental"][1]
    special["evidence"]["observations"].pop("duration_ns")
    rehash(special)

    with pytest.raises(gate.ComparisonError, match="SHM_PUBLICATION_OBSERVATIONS"):
        assembler.assemble_comparison(embedded, sidecar, gates, _design_override=design)

    assert calls == []


def test_production_design_still_requires_exact_60000_population() -> None:
    design = gate.load_frozen_design()

    assembler.validate_design_shape(design, production=True)

    aggregation = design["comparison_plan"]["aggregation"]
    assert aggregation["measured_blocks"] == 10
    assert aggregation["fixed_load_offered_operations_per_block"] == 6_000
    assert (
        aggregation["measured_blocks"] * aggregation["fixed_load_offered_operations_per_block"]
        == 60_000
    )
