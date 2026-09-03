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


def _receipt(
    *,
    observed_override: str | None = None,
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
        observed = observed_override if index == 0 and observed_override else fault.expected_outcome
        native_trace = f"1|ACT-{fault.event_id}|state|effect|{observed}\n".encode("ascii")
        ids = [
            sha256_content_id(native_trace),
            *["sha256:" + character * 64 for character in ("c", "d", "e")],
        ]
        wal_replayed = fault.action == "RESTART"
        view_change = fault.actor_class == "VALIDATOR" and fault.action == "CRASH"
        current_advanced = False
        availability = not (fault.actor_class == "STORAGE" and fault.action == "CRASH")
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


def test_measured_receipt_reconciles_java_native_and_os_layers() -> None:
    receipt = _parse(_receipt())
    assert len(receipt.network_counters) == 3
    assert len(receipt.fault_transitions) == 7
    assert all(item.passed for item in receipt.fault_transitions)


def test_expected_outcome_is_only_an_assertion() -> None:
    with pytest.raises(MeasuredStageCRuntimeError, match="RUNTIME_TERMINAL_MISMATCH"):
        _parse(_receipt(observed_override="SAFE_ABORT"))


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
    lines[index] = " ".join(fields)
    with pytest.raises(MeasuredStageCRuntimeError, match="PARTITION_ADVANCED_CURRENT"):
        _parse(("\n".join(lines) + "\n").encode("ascii"))


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
