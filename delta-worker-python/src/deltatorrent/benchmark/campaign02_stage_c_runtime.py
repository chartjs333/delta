"""Measured Python/Java/C++/OS execution boundary for Campaign 02 Stage C."""

from __future__ import annotations

import base64
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from deltatorrent.benchmark.fault_profiles import FaultProfile
from deltatorrent.benchmark.network_profiles import NetworkProfile
from deltatorrent.protocol.canonical import sha256_content_id

_CONTENT_ID: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_TOKEN: Final = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
_PROFILE_RECEIPT_DOMAIN: Final = b"deltareduce.010.stagec-java-transport-receipt.v1\0"
_NATIVE_TRACE_SET_DOMAIN: Final = b"deltareduce.010.stagec-native-fault-trace-set.v1\0"
_FORBIDDEN_MODES: Final = {"DRY", "FIXTURE", "SYNTHETIC", "CALLER_SUPPLIED", "SIMULATED_ONLY"}


class MeasuredStageCRuntimeError(ValueError):
    """Stable fail-closed measured Stage C rejection."""


def _fail(code: str) -> MeasuredStageCRuntimeError:
    return MeasuredStageCRuntimeError(code)


def _id(value: str, code: str) -> str:
    if _CONTENT_ID.fullmatch(value) is None:
        raise _fail(code)
    return value


def _nonnegative(value: str, code: str) -> int:
    if not value.isascii() or not value.isdecimal():
        raise _fail(code)
    parsed = int(value)
    if parsed < 0:
        raise _fail(code)
    return parsed


@dataclass(frozen=True, slots=True)
class MeasuredNetworkCounters:
    network_profile_id: str
    java_transport_receipt_id: str
    attempted_packets: int
    attempted_payload_bytes: int
    unique_delivered_packets: int
    unique_delivered_payload_bytes: int
    dropped_packets: int
    dropped_payload_bytes: int
    duplicate_packets: int
    duplicate_payload_bytes: int
    reordered_packets: int
    disconnect_count: int
    disconnect_duration_ms: int
    java_tx_payload_bytes: int
    java_rx_payload_bytes: int
    os_tx_bytes_before: int
    os_tx_bytes_after: int
    os_tx_bytes: int
    os_rx_bytes_before: int
    os_rx_bytes_after: int
    os_rx_bytes: int

    def __post_init__(self) -> None:
        _id(self.network_profile_id, "CAMPAIGN02_STAGE_C_NETWORK_PROFILE_ID_INVALID")
        _id(self.java_transport_receipt_id, "CAMPAIGN02_STAGE_C_JAVA_RECEIPT_ID_INVALID")
        counters = (
            self.attempted_packets,
            self.attempted_payload_bytes,
            self.unique_delivered_packets,
            self.unique_delivered_payload_bytes,
            self.dropped_packets,
            self.dropped_payload_bytes,
            self.duplicate_packets,
            self.duplicate_payload_bytes,
            self.reordered_packets,
            self.disconnect_count,
            self.disconnect_duration_ms,
            self.java_tx_payload_bytes,
            self.java_rx_payload_bytes,
            self.os_tx_bytes_before,
            self.os_tx_bytes_after,
            self.os_tx_bytes,
            self.os_rx_bytes_before,
            self.os_rx_bytes_after,
            self.os_rx_bytes,
        )
        if any(isinstance(value, bool) or value < 0 for value in counters):
            raise _fail("CAMPAIGN02_STAGE_C_COUNTER_INVALID")
        if (
            self.attempted_packets != self.unique_delivered_packets + self.dropped_packets
            or self.attempted_payload_bytes
            != self.unique_delivered_payload_bytes + self.dropped_payload_bytes
            or self.java_tx_payload_bytes
            != self.unique_delivered_payload_bytes + self.duplicate_payload_bytes
            or self.java_rx_payload_bytes
            != self.unique_delivered_payload_bytes + self.duplicate_payload_bytes
            or self.os_tx_bytes_after - self.os_tx_bytes_before != self.os_tx_bytes
            or self.os_rx_bytes_after - self.os_rx_bytes_before != self.os_rx_bytes
        ):
            raise _fail("CAMPAIGN02_STAGE_C_APPLICATION_COUNTERS_UNRECONCILED")
        if (
            self.attempted_packets <= 0
            or self.attempted_payload_bytes <= 0
            or self.unique_delivered_packets <= 0
            or self.java_tx_payload_bytes <= 0
            or self.os_tx_bytes < self.java_tx_payload_bytes
            or self.os_rx_bytes < self.java_rx_payload_bytes
        ):
            raise _fail("CAMPAIGN02_STAGE_C_OS_RUNTIME_MEASUREMENT_INVALID")

    @property
    def document(self) -> dict[str, object]:
        return {
            "attempted_packets": self.attempted_packets,
            "attempted_payload_bytes": self.attempted_payload_bytes,
            "disconnect_count": self.disconnect_count,
            "disconnect_duration_ms": self.disconnect_duration_ms,
            "dropped_packets": self.dropped_packets,
            "dropped_payload_bytes": self.dropped_payload_bytes,
            "duplicate_packets": self.duplicate_packets,
            "duplicate_payload_bytes": self.duplicate_payload_bytes,
            "java_rx_payload_bytes": self.java_rx_payload_bytes,
            "java_transport_receipt_id": self.java_transport_receipt_id,
            "java_tx_payload_bytes": self.java_tx_payload_bytes,
            "network_profile_id": self.network_profile_id,
            "os_rx_bytes_after": self.os_rx_bytes_after,
            "os_rx_bytes_before": self.os_rx_bytes_before,
            "os_rx_bytes": self.os_rx_bytes,
            "os_tx_bytes_after": self.os_tx_bytes_after,
            "os_tx_bytes_before": self.os_tx_bytes_before,
            "os_tx_bytes": self.os_tx_bytes,
            "reordered_packets": self.reordered_packets,
            "unique_delivered_packets": self.unique_delivered_packets,
            "unique_delivered_payload_bytes": self.unique_delivered_payload_bytes,
        }


@dataclass(frozen=True, slots=True)
class NativeFaultTransition:
    event_id: str
    at_step: int
    actor_class: str
    action: str
    expected_outcome: str
    observed_outcome: str
    observation_source: str
    native_trace_id: str
    native_state_root: str
    native_effect_root: str
    native_wal_sha256: str
    runtime_operation_count: int
    wal_replayed: bool
    view_change_observed: bool
    current_checkpoint_advanced: bool
    availability_success: bool
    native_trace: bytes

    def __post_init__(self) -> None:
        if (
            _TOKEN.fullmatch(self.event_id) is None
            or _TOKEN.fullmatch(self.actor_class) is None
            or _TOKEN.fullmatch(self.action) is None
            or self.at_step < 0
        ):
            raise _fail("CAMPAIGN02_STAGE_C_NATIVE_FAULT_EVENT_INVALID")
        for value in (
            self.native_trace_id,
            self.native_state_root,
            self.native_effect_root,
            self.native_wal_sha256,
        ):
            _id(value, "CAMPAIGN02_STAGE_C_NATIVE_TRACE_ID_INVALID")
        if (
            self.observation_source != "ACTUAL_RUNTIME_TRANSITION"
            or self.runtime_operation_count <= 0
            or not self.native_trace
            or sha256_content_id(self.native_trace) != self.native_trace_id
        ):
            raise _fail("CAMPAIGN02_STAGE_C_NATIVE_EXECUTION_PROOF_INVALID")
        if self.action == "RESTART" and not self.wal_replayed:
            raise _fail("CAMPAIGN02_STAGE_C_RESTART_WITHOUT_WAL_REPLAY")
        if (
            self.actor_class == "VALIDATOR"
            and self.action == "CRASH"
            and not self.view_change_observed
        ):
            raise _fail("CAMPAIGN02_STAGE_C_VALIDATOR_CRASH_WITHOUT_VIEW_CHANGE")
        if (
            self.actor_class == "REGION"
            and self.action == "PARTITION"
            and self.current_checkpoint_advanced
        ):
            raise _fail("CAMPAIGN02_STAGE_C_PARTITION_ADVANCED_CURRENT")
        if self.actor_class == "STORAGE" and self.action == "CRASH" and self.availability_success:
            raise _fail("CAMPAIGN02_STAGE_C_STORAGE_CRASH_FALSE_AVAILABILITY")

    @property
    def passed(self) -> bool:
        return self.observed_outcome == self.expected_outcome

    @property
    def document(self) -> dict[str, object]:
        return {
            "at_step": self.at_step,
            "action": self.action,
            "actor_class": self.actor_class,
            "availability_success": self.availability_success,
            "current_checkpoint_advanced": self.current_checkpoint_advanced,
            "event_id": self.event_id,
            "expected_outcome": self.expected_outcome,
            "native_effect_root": self.native_effect_root,
            "native_state_root": self.native_state_root,
            "native_trace_id": self.native_trace_id,
            "native_wal_sha256": self.native_wal_sha256,
            "native_trace_base64": base64.b64encode(self.native_trace).decode("ascii"),
            "observation_source": self.observation_source,
            "observed_outcome": self.observed_outcome,
            "passed": self.passed,
            "runtime_operation_count": self.runtime_operation_count,
            "view_change_observed": self.view_change_observed,
            "wal_replayed": self.wal_replayed,
        }


@dataclass(frozen=True, slots=True)
class MeasuredStageCReceipt:
    plan_id: str
    network_counters: tuple[MeasuredNetworkCounters, ...]
    fault_transitions: tuple[NativeFaultTransition, ...]
    native_fault_trace_id: str
    raw_java_receipt: bytes

    def __post_init__(self) -> None:
        _id(self.plan_id, "CAMPAIGN02_STAGE_C_PLAN_ID_INVALID")
        _id(self.native_fault_trace_id, "CAMPAIGN02_STAGE_C_NATIVE_TRACE_SET_ID_INVALID")
        if not self.network_counters or not self.fault_transitions:
            raise _fail("CAMPAIGN02_STAGE_C_MEASUREMENT_INCOMPLETE")
        if not all(item.passed for item in self.fault_transitions):
            raise _fail("CAMPAIGN02_STAGE_C_RUNTIME_TERMINAL_MISMATCH")
        if not self.raw_java_receipt:
            raise _fail("CAMPAIGN02_STAGE_C_RAW_JAVA_RECEIPT_MISSING")

    @property
    def raw_java_receipt_id(self) -> str:
        return sha256_content_id(self.raw_java_receipt)


@dataclass(frozen=True, slots=True)
class RuntimeArtifact:
    path: Path
    content_id: str

    def verify(self, code: str, *, executable: bool = False) -> None:
        _id(self.content_id, code)
        try:
            actual = sha256_content_id(self.path.read_bytes())
        except OSError as exc:
            raise _fail(code) from exc
        if actual != self.content_id or (executable and not os.access(self.path, os.X_OK)):
            raise _fail(code)


@dataclass(frozen=True, slots=True)
class MeasuredStageCRuntimeBoundary:
    """Immutable production process boundary; no caller-supplied measurement backend exists."""

    image_id: str
    java_executable: RuntimeArtifact
    native_executable: RuntimeArtifact
    transport_harness: RuntimeArtifact
    netty_artifacts: tuple[RuntimeArtifact, ...]
    os_interface_counter_root: Path
    working_root: Path
    measurement_mode: str = "MEASURED_RUNTIME_ONLY"
    timeout_seconds: int = 180

    def __post_init__(self) -> None:
        _id(self.image_id, "CAMPAIGN02_STAGE_C_IMAGE_ID_INVALID")
        if (
            self.measurement_mode != "MEASURED_RUNTIME_ONLY"
            or self.measurement_mode in _FORBIDDEN_MODES
        ):
            raise _fail("CAMPAIGN02_STAGE_C_MEASUREMENT_MODE_INVALID")
        if not self.netty_artifacts or self.timeout_seconds <= 0:
            raise _fail("CAMPAIGN02_STAGE_C_RUNTIME_BOUNDARY_INVALID")

    @property
    def java_executable_id(self) -> str:
        return self.java_executable.content_id

    @property
    def native_executable_id(self) -> str:
        return self.native_executable.content_id

    @property
    def transport_harness_id(self) -> str:
        return self.transport_harness.content_id

    @property
    def netty_artifact_ids(self) -> tuple[str, ...]:
        return tuple(item.content_id for item in self.netty_artifacts)

    def verify_artifacts(self) -> None:
        self.java_executable.verify("CAMPAIGN02_STAGE_C_JAVA_EXECUTABLE_MISMATCH", executable=True)
        self.native_executable.verify(
            "CAMPAIGN02_STAGE_C_NATIVE_EXECUTABLE_MISMATCH", executable=True
        )
        self.transport_harness.verify("CAMPAIGN02_STAGE_C_TRANSPORT_HARNESS_MISMATCH")
        for artifact in self.netty_artifacts:
            artifact.verify("CAMPAIGN02_STAGE_C_NETTY_ARTIFACT_MISMATCH")
        if not all(
            (self.os_interface_counter_root / name).is_file() for name in ("tx_bytes", "rx_bytes")
        ):
            raise _fail("CAMPAIGN02_STAGE_C_OS_COUNTER_SOURCE_MISSING")

    def execute(
        self,
        *,
        plan_id: str,
        packet_count: int,
        payload_bytes: int,
        network_profiles: tuple[tuple[str, NetworkProfile], ...],
        fault_profile: FaultProfile,
    ) -> MeasuredStageCReceipt:
        self.verify_artifacts()
        _id(plan_id, "CAMPAIGN02_STAGE_C_PLAN_ID_INVALID")
        if packet_count <= 0 or payload_bytes <= 0 or not network_profiles:
            raise _fail("CAMPAIGN02_STAGE_C_RUNTIME_REQUEST_INVALID")
        plan_root = self.working_root / plan_id[7:]
        try:
            plan_root.mkdir(parents=True, exist_ok=False)
            request_path = plan_root / "request.txt"
            journal_path = plan_root / "native-fault.wal"
            request_path.write_bytes(
                _request_bytes(
                    plan_id,
                    packet_count,
                    payload_bytes,
                    network_profiles,
                    fault_profile,
                )
            )
        except FileExistsError as exc:
            raise _fail("CAMPAIGN02_STAGE_C_RUNTIME_OUTPUT_ALREADY_EXISTS") from exc
        classpath = os.pathsep.join(
            [
                str(self.transport_harness.path),
                *(str(item.path) for item in self.netty_artifacts),
            ]
        )
        command = (
            str(self.java_executable.path),
            "-Dio.netty.noUnsafe=true",
            "-cp",
            classpath,
            "io.deltareduce.node.benchmark.MeasuredStageCTransport",
            str(request_path),
            str(self.native_executable.path),
            str(journal_path),
            str(self.os_interface_counter_root),
        )
        environment = dict(os.environ)
        environment.update(
            {
                "ALL_PROXY": "http://127.0.0.1:9",
                "HTTP_PROXY": "http://127.0.0.1:9",
                "HTTPS_PROXY": "http://127.0.0.1:9",
                "NO_PROXY": "localhost,127.0.0.1,::1",
            }
        )
        try:
            completed = subprocess.run(
                command,
                check=False,
                capture_output=True,
                env=environment,
                text=False,
                timeout=self.timeout_seconds,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise _fail("CAMPAIGN02_STAGE_C_RUNTIME_PROCESS_FAILED") from exc
        if completed.returncode != 0 or completed.stderr:
            raise _fail("CAMPAIGN02_STAGE_C_RUNTIME_PROCESS_FAILED")
        return _parse_receipt(
            completed.stdout,
            plan_id=plan_id,
            network_profiles=network_profiles,
            fault_profile=fault_profile,
        )


def _request_bytes(
    plan_id: str,
    packet_count: int,
    payload_bytes: int,
    network_profiles: tuple[tuple[str, NetworkProfile], ...],
    fault_profile: FaultProfile,
) -> bytes:
    fields: dict[str, str] = {
        "fault_count": str(len(fault_profile.events)),
        "packet_count": str(packet_count),
        "payload_bytes": str(payload_bytes),
        "plan_id": plan_id,
        "profile_count": str(len(network_profiles)),
    }
    for index, (_profile_id, profile) in enumerate(network_profiles):
        prefix = f"profile.{index}."
        fields.update(
            {
                prefix + "bandwidth_kbps": str(profile.bandwidth_kbps),
                prefix + "disconnect_ms": str(profile.disconnect_ms),
                prefix + "duplication_ppm": str(profile.duplication_ppm),
                prefix + "id": profile.profile_id,
                prefix + "jitter_ms": str(profile.jitter_ms),
                prefix + "loss_ppm": str(profile.loss_ppm),
                prefix + "reordering_ppm": str(profile.reordering_ppm),
                prefix + "rtt_ms": str(profile.rtt_ms),
                prefix + "seed": str(profile.seed),
            }
        )
    for index, event in enumerate(fault_profile.events):
        prefix = f"fault.{index}."
        fields.update(
            {
                prefix + "action": event.action,
                prefix + "actor": event.actor_class,
                prefix + "assumptions_hold": "1" if event.assumptions_hold else "0",
                prefix + "id": event.event_id,
                prefix + "step": str(event.at_step),
            }
        )
    return "".join(f"{key}={value}\n" for key, value in sorted(fields.items())).encode("ascii")


def _parse_receipt(
    raw: bytes,
    *,
    plan_id: str,
    network_profiles: tuple[tuple[str, NetworkProfile], ...],
    fault_profile: FaultProfile,
) -> MeasuredStageCReceipt:
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise _fail("CAMPAIGN02_STAGE_C_RUNTIME_RECEIPT_INVALID") from exc
    if lines[:1] != [f"STAGEC_V1 {plan_id}"] or lines[-1:] != ["END_STAGEC_V1"]:
        raise _fail("CAMPAIGN02_STAGE_C_RUNTIME_RECEIPT_INVALID")
    profile_ids = {profile.profile_id: content_id for content_id, profile in network_profiles}
    counters: list[MeasuredNetworkCounters] = []
    fault_rows: list[
        tuple[
            str,
            int,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            str,
            int,
            bool,
            bool,
            bool,
            bool,
            bytes,
        ]
    ] = []
    for line in lines[1:-1]:
        fields = line.split(" ")
        if fields[0] == "PROFILE":
            if len(fields) != 22 or fields[1] not in profile_ids:
                raise _fail("CAMPAIGN02_STAGE_C_JAVA_RECEIPT_INVALID")
            expected_receipt = sha256_content_id(
                _PROFILE_RECEIPT_DOMAIN + " ".join(fields[:-1]).encode("ascii")
            )
            if fields[-1] != expected_receipt:
                raise _fail("CAMPAIGN02_STAGE_C_JAVA_RECEIPT_INVALID")
            values = [
                _nonnegative(value, "CAMPAIGN02_STAGE_C_COUNTER_INVALID") for value in fields[2:-1]
            ]
            counters.append(
                MeasuredNetworkCounters(
                    network_profile_id=profile_ids[fields[1]],
                    java_transport_receipt_id=fields[-1],
                    attempted_packets=values[0],
                    attempted_payload_bytes=values[1],
                    unique_delivered_packets=values[2],
                    unique_delivered_payload_bytes=values[3],
                    dropped_packets=values[4],
                    dropped_payload_bytes=values[5],
                    duplicate_packets=values[6],
                    duplicate_payload_bytes=values[7],
                    reordered_packets=values[8],
                    disconnect_count=values[9],
                    disconnect_duration_ms=values[10],
                    java_tx_payload_bytes=values[11],
                    java_rx_payload_bytes=values[12],
                    os_tx_bytes_before=values[13],
                    os_tx_bytes_after=values[14],
                    os_tx_bytes=values[15],
                    os_rx_bytes_before=values[16],
                    os_rx_bytes_after=values[17],
                    os_rx_bytes=values[18],
                )
            )
        elif fields[0] == "FAULT":
            if len(fields) != 17:
                raise _fail("CAMPAIGN02_STAGE_C_NATIVE_TRACE_INVALID")
            try:
                native_trace = bytes.fromhex(fields[16])
            except ValueError as exc:
                raise _fail("CAMPAIGN02_STAGE_C_NATIVE_TRACE_INVALID") from exc
            flags = fields[12:16]
            if any(value not in {"0", "1"} for value in flags):
                raise _fail("CAMPAIGN02_STAGE_C_NATIVE_TRACE_INVALID")
            fault_rows.append(
                (
                    fields[1],
                    _nonnegative(fields[2], "CAMPAIGN02_STAGE_C_NATIVE_TRACE_INVALID"),
                    fields[3],
                    fields[4],
                    fields[5],
                    fields[6],
                    fields[7],
                    fields[8],
                    fields[9],
                    fields[10],
                    _nonnegative(fields[11], "CAMPAIGN02_STAGE_C_NATIVE_TRACE_INVALID"),
                    fields[12] == "1",
                    fields[13] == "1",
                    fields[14] == "1",
                    fields[15] == "1",
                    native_trace,
                )
            )
        else:
            raise _fail("CAMPAIGN02_STAGE_C_RUNTIME_RECEIPT_INVALID")
    if tuple(item.network_profile_id for item in counters) != tuple(
        item[0] for item in network_profiles
    ):
        raise _fail("CAMPAIGN02_STAGE_C_NETWORK_PROFILE_SET_MISMATCH")
    if tuple((item[0], item[1]) for item in fault_rows) != tuple(
        (item.event_id, item.at_step) for item in fault_profile.events
    ):
        raise _fail("CAMPAIGN02_STAGE_C_FAULT_PROFILE_SET_MISMATCH")
    expected_by_id = {item.event_id: item.expected_outcome for item in fault_profile.events}
    transitions = tuple(
        NativeFaultTransition(
            event_id=item[0],
            at_step=item[1],
            actor_class=item[2],
            action=item[3],
            expected_outcome=expected_by_id[item[0]],
            observed_outcome=item[4],
            observation_source=item[5],
            native_trace_id=item[6],
            native_state_root=item[7],
            native_effect_root=item[8],
            native_wal_sha256=item[9],
            runtime_operation_count=item[10],
            wal_replayed=item[11],
            view_change_observed=item[12],
            current_checkpoint_advanced=item[13],
            availability_success=item[14],
            native_trace=item[15],
        )
        for item in fault_rows
    )
    trace_set_id = sha256_content_id(
        _NATIVE_TRACE_SET_DOMAIN + "\n".join(item[6] for item in fault_rows).encode("ascii")
    )
    return MeasuredStageCReceipt(plan_id, tuple(counters), transitions, trace_set_id, raw)
