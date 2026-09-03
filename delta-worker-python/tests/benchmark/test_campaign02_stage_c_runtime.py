from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from deltatorrent.benchmark.campaign02_stage_c_runtime import (
    MeasuredNetworkCounters,
    MeasuredStageCRuntimeBoundary,
    MeasuredStageCRuntimeError,
    RuntimeArtifact,
    _parse_receipt,
    _request_bytes,
)
from deltatorrent.benchmark.fault_profiles import FaultProfile
from deltatorrent.benchmark.network_profiles import NetworkProfile
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

ROOT = Path(__file__).resolve().parents[3]
PROFILE_DOMAIN = b"deltareduce.010.stagec-java-transport-receipt.v1\0"


def _inputs() -> tuple[tuple[tuple[str, NetworkProfile], ...], FaultProfile]:
    networks = json.loads((ROOT / "configs/benchmark/networks-v1.json").read_bytes())
    faults = json.loads((ROOT / "configs/benchmark/faults-v1.json").read_bytes())
    profiles = tuple(
        (sha256_content_id(canonical_json_bytes(value)), NetworkProfile.from_dict(value))
        for value in networks["profiles"]
    )
    return profiles, FaultProfile.from_dict(faults["trace_profile"])


def _causal(event, observed: str, current_advanced: bool) -> bytes:
    applied = observed == "APPLIED"
    partition = event.actor_class == "REGION" and event.action == "PARTITION"
    worker = event.actor_class == "WORKER" and event.action == "CRASH"
    concentrated = event.event_id == "worker-loss-concentrated"
    profile = (
        "wan-regional"
        if event.actor_class == "REGION" and event.action == "DELAY"
        else "wan-intercontinental"
        if partition
        else "lan-control"
    )
    none = "NONE"
    parent = "sha256:" + "c" * 64
    next_checkpoint = "sha256:" + "d" * 64
    hard_deadline = event.at_step + 60
    if concentrated:
        deliveries = [
            *(f"worker-ticket-{index:03d}:{event.at_step + index}" for index in range(2, 10)),
            *(f"abort-vote-{index}:{hard_deadline}" for index in range(3)),
        ]
    elif worker:
        deliveries = [
            *(f"worker-ticket-{index:03d}:{event.at_step + index}" for index in range(9)),
            *(f"aggregate-vote-{index}:{event.at_step + 20 + index}" for index in range(3)),
            *(f"apply-vote-{index}:{event.at_step + 30 + index}" for index in range(3)),
        ]
    elif event.actor_class == "REGION" and event.action == "DELAY":
        deliveries = [
            *(f"worker-ticket-{index:03d}:{event.at_step + 1 + index}" for index in range(4)),
            *(f"aggregate-vote-{index}:{event.at_step + 20 + index}" for index in range(3)),
            *(f"apply-vote-{index}:{event.at_step + 30 + index}" for index in range(3)),
        ]
    elif partition:
        deliveries = [
            *(f"worker-ticket-{index:03d}:{event.at_step + index}" for index in range(4)),
            *(f"partition-aggregate-{index}:{event.at_step + 10 + index}" for index in range(2)),
            *(f"abort-vote-{index}:{hard_deadline}" for index in range(3)),
        ]
    else:
        deliveries = [f"message-0:{event.at_step + 1}"]
    fields = {
        "abort_qc_id": "sha256:" + "a" * 64 if partition or concentrated else none,
        "aggregate_root_qc_id": "sha256:" + "1" * 64 if applied else none,
        "aggregate_root_qc_tick": str(event.at_step + 22 if applied else 0),
        "apply_qc_id": "sha256:" + "3" * 64 if applied else none,
        "apply_qc_tick": str(event.at_step + 32 if applied else 0),
        "apply_quorum_threshold": "3" if applied else "0",
        "apply_validator_set_id": "sha256:" + "4" * 64 if applied else none,
        "apply_work_item_id": "sha256:" + "2" * 64 if applied else none,
        "causal_transport_receipt_id": "sha256:" + "5" * 64,
        "certified_abort_tick": str(hard_deadline if partition or concentrated else 0),
        "current_checkpoint_advanced": "true" if current_advanced else "false",
        "current_pointer_after": (
            next_checkpoint if applied else parent if partition or concentrated else none
        ),
        "current_pointer_before": parent if applied or partition or concentrated else none,
        "dropped_message_ids": (
            "partition-aggregate-2,partition-aggregate-3"
            if partition
            else "worker-ticket-000,worker-ticket-001"
            if concentrated
            else "worker-ticket-009"
            if worker
            else none
        ),
        "event_id": event.event_id,
        "failed_quorum_reason": (
            "AGGREGATE_ROOT_QC_2_OF_3_AT_HARD_DEADLINE"
            if partition
            else "MANDATORY_DOMAIN_CODE_3_OF_4_AT_HARD_DEADLINE"
            if concentrated
            else none
        ),
        "gst_tick": str(event.at_step),
        "hard_deadline_tick": str(hard_deadline),
        "isc_ticket_set": (
            ",".join(f"ticket-{index:03d}" for index in range(9))
            if worker and not concentrated
            else ",".join(f"ticket-{index:03d}" for index in range(4))
            if applied
            else none
        ),
        "loss_fraction": "2/10" if concentrated else "1/10" if worker else "0/1",
        "lost_ticket_ids": (
            "ticket-000,ticket-001" if concentrated else "ticket-009" if worker else none
        ),
        "lost_worker_ids": (
            "worker-000,worker-001" if concentrated else "worker-009" if worker else none
        ),
        "message_delivery_ticks": ",".join(deliveries),
        "missing_work_policy_result": (
            "MANDATORY_DOMAIN_CAPACITY_UNSATISFIED_ABORT"
            if concentrated
            else "OMIT_PRE_FREEZE_LOST_TICKET_EXACT_ISC"
            if worker
            else "NOT_APPLICABLE"
        ),
        "network_profile_id": profile,
        "next_checkpoint_id": next_checkpoint if applied else none,
        "next_optimizer_state_id": "sha256:" + "f" * 64 if applied else none,
        "parent_checkpoint_id": parent if applied or partition or concentrated else none,
        "parent_optimizer_state_id": "sha256:" + "e" * 64 if applied else none,
        "partition_start_tick": str(event.at_step if partition else 0),
        "per_domain_remaining_tickets": (
            "code:3,text:5" if concentrated else "code:5,text:4" if worker else none
        ),
        "per_domain_required_tickets": "code:4,text:4" if worker else none,
        "pi_d_renormalized": "false",
        "quorum_capacity_after": (
            "8" if concentrated else "9" if worker else "2" if partition else "0"
        ),
        "quorum_capacity_before": "10" if worker else "4" if partition else "0",
        "quorum_formation_tick": str(event.at_step + 22 if applied else 0),
        "schema_version": "1.0.0",
        "unavailable_ids": (
            "validator-2,validator-3"
            if partition
            else "worker-000,worker-001"
            if concentrated
            else none
        ),
        "worker_count_before": "10" if worker else "0",
        "worker_count_lost": "2" if concentrated else "1" if worker else "0",
    }
    return "".join(f"{key}={value}\n" for key, value in sorted(fields.items())).encode("ascii")


def _receipt(
    *,
    observed_override: str | None = None,
    observed_override_event_id: str | None = None,
    source_override: str | None = None,
    operation_count_override: int | None = None,
    wal_replayed_override: bool | None = None,
    view_change_override: bool | None = None,
    current_advanced_override: bool | None = None,
    availability_override: bool | None = None,
) -> bytes:
    profiles, faults = _inputs()
    plan_id = "sha256:" + "a" * 64
    lines = [f"STAGEC_V1 {plan_id}"]
    for _profile_id, profile in profiles:
        line = " ".join(
            (
                "PROFILE",
                profile.profile_id,
                "4",
                "256",
                "3",
                "192",
                "1",
                "64",
                "1",
                "64",
                "1",
                "1",
                "10",
                "256",
                "256",
                "1000",
                "1300",
                "300",
                "2000",
                "2300",
                "300",
            )
        )
        lines.append(line + " " + sha256_content_id(PROFILE_DOMAIN + line.encode("ascii")))
    for index, fault in enumerate(faults.events):
        override_observed = observed_override is not None and (
            fault.event_id == observed_override_event_id
            if observed_override_event_id is not None
            else index == 0
        )
        observed = observed_override if override_observed else fault.expected_outcome
        assert observed is not None
        native_trace = f"1|ACT-{fault.event_id}|state|effect|{observed}\n".encode("ascii")
        ids = [
            sha256_content_id(native_trace),
            *["sha256:" + character * 64 for character in ("c", "d", "e")],
        ]
        wal_replayed = fault.action == "RESTART"
        view_change = fault.actor_class == "VALIDATOR" and fault.action == "CRASH"
        current_advanced = observed == "APPLIED"
        availability = not (
            (fault.actor_class == "STORAGE" and fault.action == "CRASH")
            or fault.event_id == "worker-loss-concentrated"
        )
        if index == 0:
            wal_replayed = wal_replayed if wal_replayed_override is None else wal_replayed_override
            view_change = view_change if view_change_override is None else view_change_override
            current_advanced = (
                current_advanced if current_advanced_override is None else current_advanced_override
            )
            availability = availability if availability_override is None else availability_override
        lines.append(
            " ".join(
                (
                    "FAULT",
                    fault.event_id,
                    str(fault.at_step),
                    fault.actor_class,
                    fault.action,
                    observed,
                    source_override or "ACTUAL_RUNTIME_TRANSITION",
                    *ids,
                    str(
                        operation_count_override
                        if index == 0 and operation_count_override is not None
                        else 1
                    ),
                    "1" if wal_replayed else "0",
                    "1" if view_change else "0",
                    "1" if current_advanced else "0",
                    "1" if availability else "0",
                    native_trace.hex(),
                    _causal(fault, observed, current_advanced).hex(),
                )
            )
        )
    lines.append("END_STAGEC_V1")
    return ("\n".join(lines) + "\n").encode("ascii")


def _parse(raw: bytes):
    profiles, faults = _inputs()
    return _parse_receipt(
        raw,
        plan_id="sha256:" + "a" * 64,
        network_profiles=profiles,
        fault_profile=faults,
    )


def _rewrite_causal(
    raw: bytes,
    event_id: str,
    updates: dict[str, str],
    *,
    current_advanced: bool | None = None,
) -> bytes:
    lines = raw.decode("ascii").splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith(f"FAULT {event_id} "))
    outer = lines[index].split(" ")
    fields: dict[str, str] = {}
    for line in bytes.fromhex(outer[17]).decode("ascii").splitlines():
        name, separator, value = line.partition("=")
        assert separator
        fields[name] = value
    fields.update(updates)
    if current_advanced is not None:
        outer[14] = "1" if current_advanced else "0"
        fields["current_checkpoint_advanced"] = "true" if current_advanced else "false"
    outer[17] = (
        "".join(f"{name}={value}\n" for name, value in sorted(fields.items())).encode("ascii").hex()
    )
    lines[index] = " ".join(outer)
    return ("\n".join(lines) + "\n").encode("ascii")


def test_measured_receipt_reconciles_java_native_and_os_layers() -> None:
    receipt = _parse(_receipt())
    assert len(receipt.network_counters) == 3
    assert len(receipt.fault_transitions) == 8
    assert all(item.passed for item in receipt.fault_transitions)


def test_executable_profile_binds_concentrated_loss_to_cross_language_request() -> None:
    profiles, faults = _inputs()
    concentrated = next(
        item for item in faults.events if item.event_id == "worker-loss-concentrated"
    )
    request = _request_bytes("sha256:" + "a" * 64, 40, 64, profiles, faults).decode("ascii")

    assert faults.profile_id == "primary-crash-restart-partition-v2"
    assert len(faults.events) == 8
    assert concentrated.actor_class == "WORKER"
    assert concentrated.action == "CRASH"
    assert concentrated.expected_outcome == "ABORTED"
    assert "fault_count=8\n" in request
    assert "fault.1.id=worker-loss-concentrated\n" in request


def test_expected_outcome_is_only_an_assertion() -> None:
    with pytest.raises(MeasuredStageCRuntimeError, match="RUNTIME_TERMINAL_MISMATCH"):
        _parse(
            _receipt(
                observed_override="SAFE_ABORT",
                observed_override_event_id="validator-restart",
            )
        )


def test_applied_without_apply_qc_is_rejected() -> None:
    with pytest.raises(MeasuredStageCRuntimeError, match="APPLIED_WITHOUT_EXACT_APPLY_QC"):
        _parse(_rewrite_causal(_receipt(), "worker-loss-10pct", {"apply_qc_id": "NONE"}))


def test_aggregated_only_state_reported_as_applied_is_rejected() -> None:
    with pytest.raises(MeasuredStageCRuntimeError, match="APPLIED_WITHOUT_EXACT_APPLY_QC"):
        _parse(
            _rewrite_causal(
                _receipt(),
                "worker-loss-10pct",
                {
                    "apply_qc_id": "NONE",
                    "apply_work_item_id": "NONE",
                    "next_checkpoint_id": "NONE",
                    "next_optimizer_state_id": "NONE",
                },
                current_advanced=False,
            )
        )


def test_applied_with_unchanged_current_pointer_is_rejected() -> None:
    with pytest.raises(MeasuredStageCRuntimeError, match="APPLIED_WITHOUT_EXACT_APPLY_QC"):
        _parse(_rewrite_causal(_receipt(), "worker-loss-10pct", {}, current_advanced=False))


def test_silent_domain_weight_renormalization_is_rejected() -> None:
    with pytest.raises(MeasuredStageCRuntimeError, match="CAUSAL_SCHEDULE_INVALID"):
        _parse(_rewrite_causal(_receipt(), "worker-loss-10pct", {"pi_d_renormalized": "true"}))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("lost_worker_ids", "NONE"),
        ("lost_ticket_ids", "NONE"),
        ("per_domain_required_tickets", "NONE"),
        ("per_domain_remaining_tickets", "NONE"),
    ],
)
def test_worker_loss_requires_exact_identity_and_domain_capacity_evidence(
    field: str, value: str
) -> None:
    with pytest.raises(MeasuredStageCRuntimeError, match="WORKER_LOSS_CAUSAL_EVIDENCE_INVALID"):
        _parse(_rewrite_causal(_receipt(), "worker-loss-10pct", {field: value}))


def test_regional_delay_without_delayed_runtime_messages_is_rejected() -> None:
    with pytest.raises(MeasuredStageCRuntimeError, match="REGIONAL_DELAY_CAUSAL_EVIDENCE_INVALID"):
        _parse(
            _rewrite_causal(
                _receipt(),
                "regional-delay",
                {
                    "message_delivery_ticks": ",".join(
                        [
                            *(f"aggregate-vote-{index}:{220 + index}" for index in range(3)),
                            *(f"apply-vote-{index}:{230 + index}" for index in range(3)),
                        ]
                    )
                },
            )
        )


def test_regional_delay_reaching_aggregate_only_is_rejected() -> None:
    with pytest.raises(MeasuredStageCRuntimeError, match="APPLIED_WITHOUT_EXACT_APPLY_QC"):
        _parse(
            _rewrite_causal(
                _receipt(),
                "regional-delay",
                {"apply_qc_id": "NONE", "apply_work_item_id": "NONE"},
                current_advanced=False,
            )
        )


def test_concentrated_mandatory_domain_loss_has_certified_abort_semantics() -> None:
    worker = next(
        item
        for item in _parse(_receipt()).fault_transitions
        if item.event_id == "worker-loss-concentrated"
    )
    parent = worker.causal_evidence.parent_checkpoint_id
    assert parent is not None
    assert worker.passed and worker.observed_outcome == "ABORTED"
    assert worker.causal_evidence.lost_worker_ids == ("worker-000", "worker-001")
    assert worker.causal_evidence.lost_ticket_ids == ("ticket-000", "ticket-001")
    assert dict(worker.causal_evidence.per_domain_remaining_tickets) == {"code": 3, "text": 5}
    assert worker.causal_evidence.aggregate_root_qc_id is None
    assert worker.causal_evidence.apply_qc_id is None
    assert worker.causal_evidence.abort_qc_id is not None
    assert worker.causal_evidence.certified_abort_tick == worker.causal_evidence.hard_deadline_tick
    assert worker.causal_evidence.current_pointer_before == parent
    assert worker.causal_evidence.current_pointer_after == parent
    assert not worker.current_checkpoint_advanced


def test_hardcoded_outcome_without_actual_runtime_source_is_rejected() -> None:
    with pytest.raises(MeasuredStageCRuntimeError, match="NATIVE_EXECUTION_PROOF_INVALID"):
        _parse(_receipt(source_override="HARDCODED_OUTCOME_TABLE"))


def test_state_and_effect_roots_without_actual_operation_are_rejected() -> None:
    with pytest.raises(MeasuredStageCRuntimeError, match="NATIVE_EXECUTION_PROOF_INVALID"):
        _parse(_receipt(operation_count_override=0))


def test_restart_without_wal_replay_is_rejected() -> None:
    raw = _receipt()
    lines = raw.decode("ascii").splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith("FAULT validator-restart "))
    fields = lines[index].split(" ")
    fields[12] = "0"
    lines[index] = " ".join(fields)
    with pytest.raises(MeasuredStageCRuntimeError, match="RESTART_WITHOUT_WAL_REPLAY"):
        _parse(("\n".join(lines) + "\n").encode("ascii"))


def test_validator_crash_without_view_change_is_rejected() -> None:
    raw = _receipt()
    lines = raw.decode("ascii").splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith("FAULT validator-crash "))
    fields = lines[index].split(" ")
    fields[13] = "0"
    lines[index] = " ".join(fields)
    with pytest.raises(MeasuredStageCRuntimeError, match="CRASH_WITHOUT_VIEW_CHANGE"):
        _parse(("\n".join(lines) + "\n").encode("ascii"))


def test_partition_with_current_advance_is_rejected() -> None:
    raw = _receipt()
    lines = raw.decode("ascii").splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith("FAULT regional-partition "))
    fields = lines[index].split(" ")
    fields[14] = "1"
    causal = bytes.fromhex(fields[17]).decode("ascii")
    fields[17] = (
        causal.replace("current_checkpoint_advanced=false\n", "current_checkpoint_advanced=true\n")
        .encode("ascii")
        .hex()
    )
    lines[index] = " ".join(fields)
    with pytest.raises(MeasuredStageCRuntimeError, match="PARTITION_ADVANCED_CURRENT"):
        _parse(("\n".join(lines) + "\n").encode("ascii"))


def test_partition_abort_before_exact_deadline_is_rejected() -> None:
    _profiles, faults = _inputs()
    partition = next(event for event in faults.events if event.event_id == "regional-partition")
    with pytest.raises(MeasuredStageCRuntimeError, match="PARTITION_CAUSAL_EVIDENCE_INVALID"):
        _parse(
            _rewrite_causal(
                _receipt(),
                "regional-partition",
                {"certified_abort_tick": str(partition.at_step + 59)},
            )
        )


def test_storage_crash_with_false_availability_success_is_rejected() -> None:
    raw = _receipt()
    lines = raw.decode("ascii").splitlines()
    index = next(i for i, line in enumerate(lines) if line.startswith("FAULT storage-crash "))
    fields = lines[index].split(" ")
    fields[15] = "1"
    lines[index] = " ".join(fields)
    with pytest.raises(MeasuredStageCRuntimeError, match="STORAGE_CRASH_FALSE_AVAILABILITY"):
        _parse(("\n".join(lines) + "\n").encode("ascii"))


def test_missing_java_transport_receipt_is_rejected() -> None:
    lines = _receipt().splitlines()
    with pytest.raises(MeasuredStageCRuntimeError, match="NETWORK_PROFILE_SET_MISMATCH"):
        _parse(b"\n".join([lines[0], *lines[2:]]) + b"\n")


def test_missing_native_fault_trace_is_rejected() -> None:
    lines = _receipt().splitlines()
    first_fault = next(index for index, line in enumerate(lines) if line.startswith(b"FAULT "))
    with pytest.raises(MeasuredStageCRuntimeError, match="FAULT_PROFILE_SET_MISMATCH"):
        _parse(b"\n".join([*lines[:first_fault], *lines[first_fault + 1 :]]) + b"\n")


def test_missing_os_measurement_is_rejected() -> None:
    with pytest.raises(MeasuredStageCRuntimeError, match="OS_RUNTIME_MEASUREMENT_INVALID"):
        MeasuredNetworkCounters(
            network_profile_id="sha256:" + "1" * 64,
            java_transport_receipt_id="sha256:" + "2" * 64,
            attempted_packets=1,
            attempted_payload_bytes=64,
            unique_delivered_packets=1,
            unique_delivered_payload_bytes=64,
            dropped_packets=0,
            dropped_payload_bytes=0,
            duplicate_packets=0,
            duplicate_payload_bytes=0,
            reordered_packets=0,
            disconnect_count=0,
            disconnect_duration_ms=0,
            java_tx_payload_bytes=64,
            java_rx_payload_bytes=64,
            os_tx_bytes_before=100,
            os_tx_bytes_after=100,
            os_tx_bytes=0,
            os_rx_bytes_before=200,
            os_rx_bytes_after=200,
            os_rx_bytes=0,
        )


def test_unreconciled_totals_are_rejected() -> None:
    receipt = _parse(_receipt())
    with pytest.raises(MeasuredStageCRuntimeError, match="APPLICATION_COUNTERS_UNRECONCILED"):
        replace(receipt.network_counters[0], dropped_packets=2)


@pytest.mark.parametrize(
    "mode", ["DRY", "FIXTURE", "SYNTHETIC", "CALLER_SUPPLIED", "SIMULATED_ONLY"]
)
def test_non_measured_runtime_modes_are_rejected(tmp_path: Path, mode: str) -> None:
    artifact = RuntimeArtifact(tmp_path / "missing", "sha256:" + "1" * 64)
    with pytest.raises(MeasuredStageCRuntimeError, match="MEASUREMENT_MODE_INVALID"):
        MeasuredStageCRuntimeBoundary(
            image_id="sha256:" + "2" * 64,
            java_executable=artifact,
            native_executable=artifact,
            transport_harness=artifact,
            netty_artifacts=(artifact,),
            os_interface_counter_root=tmp_path,
            working_root=tmp_path,
            measurement_mode=mode,
        )


def test_wrong_java_or_native_binary_hash_is_rejected(tmp_path: Path) -> None:
    executable = tmp_path / "runtime"
    executable.write_bytes(b"actual runtime")
    executable.chmod(0o755)
    valid = RuntimeArtifact(executable, sha256_content_id(executable.read_bytes()))
    wrong = RuntimeArtifact(executable, "sha256:" + "f" * 64)
    counter_root = tmp_path / "counters"
    counter_root.mkdir()
    for name in ("tx_bytes", "rx_bytes"):
        (counter_root / name).write_text("0\n", encoding="ascii")
    boundary = MeasuredStageCRuntimeBoundary(
        image_id="sha256:" + "2" * 64,
        java_executable=wrong,
        native_executable=valid,
        transport_harness=valid,
        netty_artifacts=(valid,),
        os_interface_counter_root=counter_root,
        working_root=tmp_path / "work",
    )
    with pytest.raises(MeasuredStageCRuntimeError, match="JAVA_EXECUTABLE_MISMATCH"):
        boundary.verify_artifacts()
    with pytest.raises(MeasuredStageCRuntimeError, match="NATIVE_EXECUTABLE_MISMATCH"):
        replace(boundary, java_executable=valid, native_executable=wrong).verify_artifacts()


def test_primary_runner_source_has_no_simulation_or_expected_outcome_assignment() -> None:
    source = (
        ROOT / "delta-worker-python/src/deltatorrent/benchmark/campaign02_network_fault.py"
    ).read_text(encoding="utf-8")
    assert "simulate(" not in source
    assert "apply_profile(" not in source
    assert "observed_outcome = event.expected_outcome" not in source
    sidecar = (ROOT / "delta-runtime-cpp/src/benchmark/sidecar_main.cpp").read_text(
        encoding="utf-8"
    )
    java = (
        ROOT
        / "delta-node-java/src/main/java/io/deltareduce/node/benchmark/MeasuredStageCTransport.java"
    ).read_text(encoding="utf-8")
    assert "fault_outcome(" not in sidecar
    assert "expected_outcome" not in sidecar
    assert 'fault.id().equals("worker-loss-concentrated")' in java
    assert '"ABORT_VOTE", hardDeadlineTick, true' in java
