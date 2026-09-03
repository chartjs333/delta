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
class NativeFaultCausalEvidence:
    causal_transport_receipt_id: str
    network_profile_id: str
    message_delivery_ticks: tuple[tuple[str, int], ...]
    dropped_message_ids: tuple[str, ...]
    aggregate_root_qc_id: str | None
    apply_work_item_id: str | None
    apply_qc_id: str | None
    abort_qc_id: str | None
    parent_checkpoint_id: str | None
    next_checkpoint_id: str | None
    parent_optimizer_state_id: str | None
    next_optimizer_state_id: str | None
    current_pointer_before: str | None
    current_pointer_after: str | None
    apply_validator_set_id: str | None
    apply_quorum_threshold: int
    worker_count_before: int
    worker_count_lost: int
    loss_fraction: tuple[int, int]
    lost_worker_ids: tuple[str, ...]
    lost_ticket_ids: tuple[str, ...]
    per_domain_required_tickets: tuple[tuple[str, int], ...]
    per_domain_remaining_tickets: tuple[tuple[str, int], ...]
    isc_ticket_set: tuple[str, ...]
    quorum_capacity_before: int
    quorum_capacity_after: int
    missing_work_policy_result: str
    pi_d_renormalized: bool
    gst_tick: int
    hard_deadline_tick: int
    quorum_formation_tick: int
    aggregate_root_qc_tick: int
    apply_qc_tick: int
    partition_start_tick: int
    unavailable_ids: tuple[str, ...]
    failed_quorum_reason: str | None
    certified_abort_tick: int

    def validate_for(self, transition: NativeFaultTransition) -> None:
        _id(
            self.causal_transport_receipt_id,
            "CAMPAIGN02_STAGE_C_CAUSAL_TRANSPORT_RECEIPT_INVALID",
        )
        if self.network_profile_id not in {
            "lan-control",
            "wan-regional",
            "wan-intercontinental",
        }:
            raise _fail("CAMPAIGN02_STAGE_C_CAUSAL_NETWORK_PROFILE_INVALID")
        optional_ids = (
            self.aggregate_root_qc_id,
            self.apply_work_item_id,
            self.apply_qc_id,
            self.abort_qc_id,
            self.parent_checkpoint_id,
            self.next_checkpoint_id,
            self.parent_optimizer_state_id,
            self.next_optimizer_state_id,
            self.current_pointer_before,
            self.current_pointer_after,
            self.apply_validator_set_id,
        )
        for value in optional_ids:
            if value is not None:
                _id(value, "CAMPAIGN02_STAGE_C_CAUSAL_CONTENT_ID_INVALID")
        integers = (
            self.apply_quorum_threshold,
            self.worker_count_before,
            self.worker_count_lost,
            *self.loss_fraction,
            self.quorum_capacity_before,
            self.quorum_capacity_after,
            self.gst_tick,
            self.hard_deadline_tick,
            self.quorum_formation_tick,
            self.aggregate_root_qc_tick,
            self.apply_qc_tick,
            self.partition_start_tick,
            self.certified_abort_tick,
        )
        if any(isinstance(value, bool) or value < 0 for value in integers):
            raise _fail("CAMPAIGN02_STAGE_C_CAUSAL_INTEGER_INVALID")
        if (
            self.loss_fraction[1] <= 0
            or self.gst_tick != transition.at_step
            or self.hard_deadline_tick < self.gst_tick
            or any(
                tick < self.gst_tick or tick > self.hard_deadline_tick
                for _, tick in self.message_delivery_ticks
            )
            or len({name for name, _ in self.message_delivery_ticks})
            != len(self.message_delivery_ticks)
            or self.pi_d_renormalized
        ):
            raise _fail("CAMPAIGN02_STAGE_C_CAUSAL_SCHEDULE_INVALID")
        if transition.observed_outcome == "APPLIED":
            deliveries = dict(self.message_delivery_ticks)
            aggregate_ticks = [
                tick
                for message_id, tick in deliveries.items()
                if message_id.startswith("aggregate-vote-")
            ]
            apply_ticks = [
                tick
                for message_id, tick in deliveries.items()
                if message_id.startswith("apply-vote-")
            ]
            if (
                any(
                    value is None
                    for value in (
                        self.aggregate_root_qc_id,
                        self.apply_work_item_id,
                        self.apply_qc_id,
                        self.parent_checkpoint_id,
                        self.next_checkpoint_id,
                        self.parent_optimizer_state_id,
                        self.next_optimizer_state_id,
                        self.current_pointer_before,
                        self.current_pointer_after,
                        self.apply_validator_set_id,
                    )
                )
                or self.abort_qc_id is not None
                or self.apply_quorum_threshold != 3
                or not transition.current_checkpoint_advanced
                or self.current_pointer_before != self.parent_checkpoint_id
                or self.current_pointer_after != self.next_checkpoint_id
                or self.current_pointer_before == self.current_pointer_after
                or len(aggregate_ticks) != 3
                or len(apply_ticks) != 3
                or max(aggregate_ticks, default=0) != self.aggregate_root_qc_tick
                or max(apply_ticks, default=0) != self.apply_qc_tick
                or self.quorum_formation_tick != self.aggregate_root_qc_tick
                or not (
                    self.gst_tick
                    < self.aggregate_root_qc_tick
                    < self.apply_qc_tick
                    < self.hard_deadline_tick
                )
            ):
                raise _fail("CAMPAIGN02_STAGE_C_APPLIED_WITHOUT_EXACT_APPLY_QC")
        elif transition.current_checkpoint_advanced:
            raise _fail("CAMPAIGN02_STAGE_C_NON_APPLIED_POINTER_ADVANCE")
        if transition.actor_class == "WORKER" and transition.action == "CRASH":
            required = dict(self.per_domain_required_tickets)
            remaining = dict(self.per_domain_remaining_tickets)
            common_invalid = (
                self.worker_count_before != 10
                or required != {"code": 4, "text": 4}
                or self.quorum_capacity_before != 10
                or len(self.lost_worker_ids) != self.worker_count_lost
                or len(self.lost_ticket_ids) != self.worker_count_lost
            )
            successful_loss_invalid = transition.observed_outcome == "APPLIED" and (
                self.worker_count_lost != 1
                or self.loss_fraction != (1, 10)
                or len(self.isc_ticket_set) != 9
                or any(remaining.get(domain, 0) < count for domain, count in required.items())
                or self.quorum_capacity_after != 9
                or self.missing_work_policy_result != "OMIT_PRE_FREEZE_LOST_TICKET_EXACT_ISC"
                or {
                    message_id
                    for message_id, _ in self.message_delivery_ticks
                    if message_id.startswith("worker-ticket-")
                }
                != {f"worker-ticket-{index:03d}" for index in range(9)}
                or set(self.dropped_message_ids) != {"worker-ticket-009"}
            )
            concentrated_abort_invalid = transition.observed_outcome == "ABORTED" and (
                self.worker_count_lost != 2
                or self.loss_fraction != (2, 10)
                or self.isc_ticket_set
                or remaining != {"code": 3, "text": 5}
                or self.quorum_capacity_after != 8
                or self.missing_work_policy_result != "MANDATORY_DOMAIN_CAPACITY_UNSATISFIED_ABORT"
                or self.abort_qc_id is None
                or self.certified_abort_tick != self.hard_deadline_tick
                or self.failed_quorum_reason != "MANDATORY_DOMAIN_CODE_3_OF_4_AT_HARD_DEADLINE"
                or self.current_pointer_before != self.parent_checkpoint_id
                or self.current_pointer_after != self.parent_checkpoint_id
            )
            if common_invalid or successful_loss_invalid or concentrated_abort_invalid:
                raise _fail("CAMPAIGN02_STAGE_C_WORKER_LOSS_CAUSAL_EVIDENCE_INVALID")
        if transition.actor_class == "REGION" and transition.action == "DELAY":
            delivery_ids = {message_id for message_id, _ in self.message_delivery_ticks}
            if (
                self.network_profile_id != "wan-regional"
                or {name for name in delivery_ids if name.startswith("worker-ticket-")}
                != {f"worker-ticket-{index:03d}" for index in range(4)}
                or {name for name in delivery_ids if name.startswith("aggregate-vote-")}
                != {f"aggregate-vote-{index}" for index in range(3)}
                or {name for name in delivery_ids if name.startswith("apply-vote-")}
                != {f"apply-vote-{index}" for index in range(3)}
            ):
                raise _fail("CAMPAIGN02_STAGE_C_REGIONAL_DELAY_CAUSAL_EVIDENCE_INVALID")
        if transition.actor_class == "REGION" and transition.action == "PARTITION":
            if (
                self.network_profile_id != "wan-intercontinental"
                or self.abort_qc_id is None
                or self.certified_abort_tick != self.hard_deadline_tick
                or self.partition_start_tick != transition.at_step
                or not self.unavailable_ids
                or {
                    message_id
                    for message_id, tick in self.message_delivery_ticks
                    if message_id.startswith("abort-vote-") and tick == self.hard_deadline_tick
                }
                != {f"abort-vote-{index}" for index in range(3)}
                or self.failed_quorum_reason != "AGGREGATE_ROOT_QC_2_OF_3_AT_HARD_DEADLINE"
                or self.current_pointer_before != self.current_pointer_after
                or self.current_pointer_before != self.parent_checkpoint_id
            ):
                raise _fail("CAMPAIGN02_STAGE_C_PARTITION_CAUSAL_EVIDENCE_INVALID")

    @property
    def document(self) -> dict[str, object]:
        return {
            "abort_qc_id": self.abort_qc_id,
            "aggregate_root_qc_id": self.aggregate_root_qc_id,
            "aggregate_root_qc_tick": self.aggregate_root_qc_tick,
            "apply_qc_id": self.apply_qc_id,
            "apply_qc_tick": self.apply_qc_tick,
            "apply_quorum_threshold": self.apply_quorum_threshold,
            "apply_validator_set_id": self.apply_validator_set_id,
            "apply_work_item_id": self.apply_work_item_id,
            "causal_transport_receipt_id": self.causal_transport_receipt_id,
            "certified_abort_tick": self.certified_abort_tick,
            "current_pointer_after": self.current_pointer_after,
            "current_pointer_before": self.current_pointer_before,
            "dropped_message_ids": list(self.dropped_message_ids),
            "failed_quorum_reason": self.failed_quorum_reason,
            "gst_tick": self.gst_tick,
            "hard_deadline_tick": self.hard_deadline_tick,
            "isc_ticket_set": list(self.isc_ticket_set),
            "loss_fraction": {
                "denominator": self.loss_fraction[1],
                "numerator": self.loss_fraction[0],
            },
            "lost_ticket_ids": list(self.lost_ticket_ids),
            "lost_worker_ids": list(self.lost_worker_ids),
            "message_delivery_ticks": [
                {"logical_tick": tick, "message_id": message_id}
                for message_id, tick in self.message_delivery_ticks
            ],
            "missing_work_policy_result": self.missing_work_policy_result,
            "network_profile_id": self.network_profile_id,
            "next_checkpoint_id": self.next_checkpoint_id,
            "next_optimizer_state_id": self.next_optimizer_state_id,
            "parent_checkpoint_id": self.parent_checkpoint_id,
            "parent_optimizer_state_id": self.parent_optimizer_state_id,
            "partition_start_tick": self.partition_start_tick,
            "per_domain_remaining_tickets": dict(self.per_domain_remaining_tickets),
            "per_domain_required_tickets": dict(self.per_domain_required_tickets),
            "pi_d_renormalized": self.pi_d_renormalized,
            "quorum_capacity_after": self.quorum_capacity_after,
            "quorum_capacity_before": self.quorum_capacity_before,
            "quorum_formation_tick": self.quorum_formation_tick,
            "unavailable_ids": list(self.unavailable_ids),
            "worker_count_before": self.worker_count_before,
            "worker_count_lost": self.worker_count_lost,
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
    causal_evidence: NativeFaultCausalEvidence

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
        self.causal_evidence.validate_for(self)

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
            **self.causal_evidence.document,
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


_CAUSAL_FIELDS: Final = {
    "abort_qc_id",
    "aggregate_root_qc_id",
    "aggregate_root_qc_tick",
    "apply_qc_id",
    "apply_qc_tick",
    "apply_quorum_threshold",
    "apply_validator_set_id",
    "apply_work_item_id",
    "causal_transport_receipt_id",
    "certified_abort_tick",
    "current_checkpoint_advanced",
    "current_pointer_after",
    "current_pointer_before",
    "dropped_message_ids",
    "event_id",
    "failed_quorum_reason",
    "gst_tick",
    "hard_deadline_tick",
    "isc_ticket_set",
    "loss_fraction",
    "lost_ticket_ids",
    "lost_worker_ids",
    "message_delivery_ticks",
    "missing_work_policy_result",
    "network_profile_id",
    "next_checkpoint_id",
    "next_optimizer_state_id",
    "parent_checkpoint_id",
    "parent_optimizer_state_id",
    "partition_start_tick",
    "per_domain_remaining_tickets",
    "per_domain_required_tickets",
    "pi_d_renormalized",
    "quorum_capacity_after",
    "quorum_capacity_before",
    "quorum_formation_tick",
    "schema_version",
    "unavailable_ids",
    "worker_count_before",
    "worker_count_lost",
}


def _parse_causal_evidence(
    raw: bytes,
    *,
    event_id: str,
    current_checkpoint_advanced: bool,
) -> NativeFaultCausalEvidence:
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        raise _fail("CAMPAIGN02_STAGE_C_CAUSAL_EVIDENCE_INVALID") from exc
    if not text.endswith("\n"):
        raise _fail("CAMPAIGN02_STAGE_C_CAUSAL_EVIDENCE_INVALID")
    fields: dict[str, str] = {}
    for line in text.splitlines():
        name, separator, value = line.partition("=")
        if not separator or not name or not value or name in fields:
            raise _fail("CAMPAIGN02_STAGE_C_CAUSAL_EVIDENCE_INVALID")
        fields[name] = value
    if (
        set(fields) != _CAUSAL_FIELDS
        or fields["schema_version"] != "1.0.0"
        or fields["event_id"] != event_id
        or fields["current_checkpoint_advanced"]
        != ("true" if current_checkpoint_advanced else "false")
        or text != "".join(f"{name}={value}\n" for name, value in sorted(fields.items()))
    ):
        raise _fail("CAMPAIGN02_STAGE_C_CAUSAL_EVIDENCE_INVALID")

    def optional(name: str) -> str | None:
        value = fields[name]
        if value == "NONE":
            return None
        return _id(value, "CAMPAIGN02_STAGE_C_CAUSAL_CONTENT_ID_INVALID")

    def tokens(name: str) -> tuple[str, ...]:
        value = fields[name]
        if value == "NONE":
            return ()
        items = tuple(value.split(","))
        if len(set(items)) != len(items) or any(_TOKEN.fullmatch(item) is None for item in items):
            raise _fail("CAMPAIGN02_STAGE_C_CAUSAL_TOKEN_SET_INVALID")
        return items

    def pairs(name: str) -> tuple[tuple[str, int], ...]:
        value = fields[name]
        if value == "NONE":
            return ()
        result: list[tuple[str, int]] = []
        for item in value.split(","):
            key, separator, raw_value = item.partition(":")
            if not separator or _TOKEN.fullmatch(key) is None:
                raise _fail("CAMPAIGN02_STAGE_C_CAUSAL_PAIR_SET_INVALID")
            result.append(
                (key, _nonnegative(raw_value, "CAMPAIGN02_STAGE_C_CAUSAL_PAIR_SET_INVALID"))
            )
        if len({key for key, _ in result}) != len(result):
            raise _fail("CAMPAIGN02_STAGE_C_CAUSAL_PAIR_SET_INVALID")
        return tuple(result)

    numerator, separator, denominator = fields["loss_fraction"].partition("/")
    if not separator:
        raise _fail("CAMPAIGN02_STAGE_C_CAUSAL_LOSS_FRACTION_INVALID")
    fraction = (
        _nonnegative(numerator, "CAMPAIGN02_STAGE_C_CAUSAL_LOSS_FRACTION_INVALID"),
        _nonnegative(denominator, "CAMPAIGN02_STAGE_C_CAUSAL_LOSS_FRACTION_INVALID"),
    )
    if fields["pi_d_renormalized"] not in {"true", "false"}:
        raise _fail("CAMPAIGN02_STAGE_C_CAUSAL_PI_D_INVALID")
    return NativeFaultCausalEvidence(
        causal_transport_receipt_id=_id(
            fields["causal_transport_receipt_id"],
            "CAMPAIGN02_STAGE_C_CAUSAL_TRANSPORT_RECEIPT_INVALID",
        ),
        network_profile_id=fields["network_profile_id"],
        message_delivery_ticks=pairs("message_delivery_ticks"),
        dropped_message_ids=tokens("dropped_message_ids"),
        aggregate_root_qc_id=optional("aggregate_root_qc_id"),
        apply_work_item_id=optional("apply_work_item_id"),
        apply_qc_id=optional("apply_qc_id"),
        abort_qc_id=optional("abort_qc_id"),
        parent_checkpoint_id=optional("parent_checkpoint_id"),
        next_checkpoint_id=optional("next_checkpoint_id"),
        parent_optimizer_state_id=optional("parent_optimizer_state_id"),
        next_optimizer_state_id=optional("next_optimizer_state_id"),
        current_pointer_before=optional("current_pointer_before"),
        current_pointer_after=optional("current_pointer_after"),
        apply_validator_set_id=optional("apply_validator_set_id"),
        apply_quorum_threshold=_nonnegative(
            fields["apply_quorum_threshold"], "CAMPAIGN02_STAGE_C_CAUSAL_INTEGER_INVALID"
        ),
        worker_count_before=_nonnegative(
            fields["worker_count_before"], "CAMPAIGN02_STAGE_C_CAUSAL_INTEGER_INVALID"
        ),
        worker_count_lost=_nonnegative(
            fields["worker_count_lost"], "CAMPAIGN02_STAGE_C_CAUSAL_INTEGER_INVALID"
        ),
        loss_fraction=fraction,
        lost_worker_ids=tokens("lost_worker_ids"),
        lost_ticket_ids=tokens("lost_ticket_ids"),
        per_domain_required_tickets=pairs("per_domain_required_tickets"),
        per_domain_remaining_tickets=pairs("per_domain_remaining_tickets"),
        isc_ticket_set=tokens("isc_ticket_set"),
        quorum_capacity_before=_nonnegative(
            fields["quorum_capacity_before"], "CAMPAIGN02_STAGE_C_CAUSAL_INTEGER_INVALID"
        ),
        quorum_capacity_after=_nonnegative(
            fields["quorum_capacity_after"], "CAMPAIGN02_STAGE_C_CAUSAL_INTEGER_INVALID"
        ),
        missing_work_policy_result=fields["missing_work_policy_result"],
        pi_d_renormalized=fields["pi_d_renormalized"] == "true",
        gst_tick=_nonnegative(fields["gst_tick"], "CAMPAIGN02_STAGE_C_CAUSAL_INTEGER_INVALID"),
        hard_deadline_tick=_nonnegative(
            fields["hard_deadline_tick"], "CAMPAIGN02_STAGE_C_CAUSAL_INTEGER_INVALID"
        ),
        quorum_formation_tick=_nonnegative(
            fields["quorum_formation_tick"], "CAMPAIGN02_STAGE_C_CAUSAL_INTEGER_INVALID"
        ),
        aggregate_root_qc_tick=_nonnegative(
            fields["aggregate_root_qc_tick"], "CAMPAIGN02_STAGE_C_CAUSAL_INTEGER_INVALID"
        ),
        apply_qc_tick=_nonnegative(
            fields["apply_qc_tick"], "CAMPAIGN02_STAGE_C_CAUSAL_INTEGER_INVALID"
        ),
        partition_start_tick=_nonnegative(
            fields["partition_start_tick"], "CAMPAIGN02_STAGE_C_CAUSAL_INTEGER_INVALID"
        ),
        unavailable_ids=tokens("unavailable_ids"),
        failed_quorum_reason=(
            None if fields["failed_quorum_reason"] == "NONE" else fields["failed_quorum_reason"]
        ),
        certified_abort_tick=_nonnegative(
            fields["certified_abort_tick"], "CAMPAIGN02_STAGE_C_CAUSAL_INTEGER_INVALID"
        ),
    )


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
            if len(fields) != 18:
                raise _fail("CAMPAIGN02_STAGE_C_NATIVE_TRACE_INVALID")
            try:
                native_trace = bytes.fromhex(fields[16])
                causal_evidence = bytes.fromhex(fields[17])
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
                    causal_evidence,
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
            causal_evidence=_parse_causal_evidence(
                item[16], event_id=item[0], current_checkpoint_advanced=item[13]
            ),
        )
        for item in fault_rows
    )
    trace_set_id = sha256_content_id(
        _NATIVE_TRACE_SET_DOMAIN + "\n".join(item[6] for item in fault_rows).encode("ascii")
    )
    return MeasuredStageCReceipt(plan_id, tuple(counters), transitions, trace_set_id, raw)
