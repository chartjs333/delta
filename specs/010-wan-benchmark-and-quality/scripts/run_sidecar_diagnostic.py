#!/usr/bin/env python3
"""Run exactly one sealed, non-qualifying PR50 sidecar diagnostic campaign."""

from __future__ import annotations

import argparse
import copy
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import ROUND_FLOOR, Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from typing import Any

import sidecar_diagnostic_common as contract

ATTEMPT_SEAL_TYPE = "FEATURE010_SIDECAR_DIAGNOSTIC_ATTEMPT_SEAL"
EXECUTION_STARTED_SEAL_TYPE = "FEATURE010_SIDECAR_DIAGNOSTIC_EXECUTION_STARTED_SEAL"
COMPLETION_SEAL_TYPE = "FEATURE010_SIDECAR_DIAGNOSTIC_COMPLETION_SEAL"
FAILURE_SEAL_TYPE = "FEATURE010_SIDECAR_DIAGNOSTIC_FAILURE_SEAL"
TERMINAL_SEAL_TYPE = "FEATURE010_SIDECAR_DIAGNOSTIC_TERMINAL_SEAL"
LANES_COMPLETE_TYPE = "FEATURE010_SIDECAR_DIAGNOSTIC_LANES_COMPLETE"
PREFLIGHT_RECEIPT_TYPE = "FEATURE010_SIDECAR_DIAGNOSTIC_PREFLIGHT_RECEIPT"
PREFLIGHT_RECEIPT_STATE = "PREFLIGHT_PASSED_NON_CONSUMING"
ATTEMPT_SEAL_STATE = "ARMED_ONE_SHOT_NO_RERUN"
EXECUTION_STARTED_SEAL_STATE = "EXECUTION_STARTED_ONE_SHOT_NO_RERUN"
PREFLIGHT_RECEIPT_FIELDS = {
    "allocation_manifest_sha256",
    "allocation_preflight",
    "consumes_campaign",
    "created_at_utc",
    "diagnostic_campaign_id",
    "live_allocation",
    "manifest_checkout",
    "manifest_sha256",
    "schema_version",
    "source",
    "source_checkout",
    "state",
    "type_name",
}
ATTEMPT_SEAL_FIELDS = {
    "allocation_manifest_sha256",
    "authority",
    "diagnostic_campaign_id",
    "manifest_checkout",
    "manifest_sha256",
    "preflight_receipt_sha256",
    "schema_version",
    "source",
    "source_checkout",
    "started_at_utc",
    "state",
    "type_name",
}
FAILURE_SEAL_FIELDS = {
    "attempt_record_sha256",
    "diagnostic_campaign_id",
    "error_type",
    "execution_started_record_sha256",
    "failed_at_utc",
    "manifest_sha256",
    "message",
    "schema_version",
    "state",
    "type_name",
}
COMPLETION_SEAL_FIELDS = {
    "attempt_record_sha256",
    "completed_at_utc",
    "diagnostic_campaign_id",
    "evidence_sha256",
    "execution_started_record_sha256",
    "manifest_sha256",
    "schema_version",
    "state",
    "type_name",
}
EXECUTION_STARTED_SEAL_FIELDS = {
    "attempt_record_sha256",
    "diagnostic_campaign_id",
    "manifest_sha256",
    "schema_version",
    "started_at_utc",
    "state",
    "type_name",
}
TERMINAL_SEAL_FIELDS = {
    "attempt_record_sha256",
    "diagnostic_campaign_id",
    "execution_started_record_sha256",
    "manifest_sha256",
    "outcome",
    "outcome_record",
    "outcome_record_sha256",
    "schema_version",
    "sealed_at_utc",
    "state",
    "type_name",
}
JFR_DRY_RUN_CLASS = "io.deltareduce.node.sidecar.SidecarDiagnosticCaptureDryRun"
STRACE_CHILD_PROBE = (
    "import os,tempfile;"
    "p=tempfile.NamedTemporaryFile(delete=False);"
    "p.write(b'x');p.flush();os.fsync(p.fileno());p.close();os.unlink(p.name)"
)

EVIDENCE_FIELDS = {
    "artifacts",
    "assembler_eligible",
    "authority",
    "benchmark_result_qc",
    "campaign_classification",
    "classified_missed_slots",
    "diagnostic_campaign_id",
    "ended_at_utc",
    "execution_class",
    "external_ledger",
    "feature010_go",
    "gate_a_qualified",
    "gate_b_qualified",
    "gate_c_qualified",
    "gate_d_qualified",
    "lanes",
    "manifest_checkout",
    "manifest_sha256",
    "official_comparison",
    "profile_selection_allowed",
    "schema_version",
    "selected_profile",
    "source",
    "source_checkout",
    "status",
    "type_name",
}

LANE_EVIDENCE_FIELDS = {
    "artifacts",
    "ended_at_utc",
    "event_count",
    "executed_argv",
    "executed_environment",
    "environment_mode",
    "exit_code",
    "java_involved",
    "jfr",
    "missed_slots",
    "monotonic_duration_ns",
    "profile_id",
    "started_at_utc",
    "strace_fsync",
    "timed_out",
    "working_directory",
}


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")


def canonical_write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    payload = contract.canonical_bytes(value) + b"\n"
    with temporary.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)
    if os.name == "posix":
        descriptor = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def durable_exclusive_write(path: Path, value: object) -> None:
    """Durably publish one complete append-only ledger record without replacement."""

    contract.require(path.parent.is_dir(), "LEDGER_DIRECTORY_MISSING", str(path.parent))
    payload = contract.canonical_bytes(value) + b"\n"
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        stream = os.fdopen(descriptor, "wb")
        descriptor = -1
        with stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.link(temporary, path)
        if os.name == "posix":
            directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def available(value: object) -> dict[str, object]:
    return {"status": "AVAILABLE", "value": value}


def unavailable(reason: str) -> dict[str, object]:
    return {"reason": reason, "status": "NOT_AVAILABLE"}


def read_text(path: Path, label: str) -> dict[str, object]:
    try:
        return available(path.read_text(encoding="utf-8", errors="strict").strip())
    except (OSError, UnicodeError) as error:
        return unavailable(f"{label}: {type(error).__name__}")


def parse_key_values(record: dict[str, object]) -> dict[str, object]:
    if record["status"] != "AVAILABLE":
        return record
    output: dict[str, int | str] = {}
    for line in str(record["value"]).splitlines():
        pieces = line.split()
        if len(pieces) != 2:
            continue
        try:
            output[pieces[0]] = int(pieces[1])
        except ValueError:
            output[pieces[0]] = pieces[1]
    return available(output)


@dataclass(frozen=True)
class CgroupMembership:
    controller: str
    process_path: str
    mount_root: str
    mount_point: Path
    resolved_path: Path

    def as_evidence(self) -> dict[str, str]:
        return {
            "controller": self.controller,
            "mount_point": str(self.mount_point),
            "mount_root": self.mount_root,
            "process_path": self.process_path,
            "resolved_path": str(self.resolved_path),
        }


@dataclass(frozen=True)
class CgroupLayout:
    mode: str
    cpu: Path
    cpuset: Path
    memory: Path
    memberships: tuple[CgroupMembership, ...]


@dataclass(frozen=True)
class CgroupMount:
    filesystem: str
    root: str
    mount_point: Path
    controllers: frozenset[str]


def mountinfo_text(value: str) -> str:
    for encoded, decoded in (("\\040", " "), ("\\011", "\t"), ("\\134", "\\")):
        value = value.replace(encoded, decoded)
    return value


def cgroup_relative(process_path: str, mount_root: str) -> tuple[str, ...] | None:
    process = PurePosixPath(process_path)
    root = PurePosixPath(mount_root)
    if not process.is_absolute() or not root.is_absolute():
        return None
    if process == root:
        return ()
    try:
        relative = process.relative_to(root)
    except ValueError:
        return None
    return relative.parts


def read_cgroup_mounts(mountinfo: Path) -> list[CgroupMount]:
    mounts: list[CgroupMount] = []
    for line in mountinfo.read_text(encoding="utf-8", errors="strict").splitlines():
        fields = line.split()
        if "-" not in fields:
            continue
        separator = fields.index("-")
        if separator < 6 or len(fields) <= separator + 3:
            continue
        filesystem = fields[separator + 1]
        if filesystem not in {"cgroup", "cgroup2"}:
            continue
        super_options = frozenset(fields[separator + 3].split(","))
        mounts.append(
            CgroupMount(
                filesystem=filesystem,
                root=mountinfo_text(fields[3]),
                mount_point=Path(mountinfo_text(fields[4])).resolve(),
                controllers=super_options,
            )
        )
    return mounts


def resolve_cgroup_membership(
    controller: str,
    process_path: str,
    mounts: list[CgroupMount],
    *,
    filesystem: str,
) -> CgroupMembership | None:
    candidates: list[tuple[int, CgroupMembership]] = []
    for mount in mounts:
        if mount.filesystem != filesystem:
            continue
        if filesystem == "cgroup" and controller not in mount.controllers:
            continue
        relative = cgroup_relative(process_path, mount.root)
        if relative is None:
            continue
        resolved = mount.mount_point.joinpath(*relative).resolve()
        if not resolved.is_dir():
            continue
        membership = CgroupMembership(
            controller=controller,
            process_path=process_path,
            mount_root=mount.root,
            mount_point=mount.mount_point,
            resolved_path=resolved,
        )
        candidates.append((len(PurePosixPath(mount.root).parts), membership))
    if not candidates:
        return None
    return max(candidates, key=lambda item: item[0])[1]


def cgroup_layout(
    proc_cgroup: Path = Path("/proc/self/cgroup"),
    mountinfo: Path = Path("/proc/self/mountinfo"),
) -> CgroupLayout | None:
    """Resolve the current process' cgroup v2 or legacy controller paths.

    Docker Desktop may expose the same frozen CPU/cpuset/memory controls through
    cgroup v1.  The diagnostic records that fact and normalizes only the three
    allocation identities plus cpu.stat; it never treats one mode as evidence
    for the other.
    """

    try:
        entries: list[tuple[str, tuple[str, ...], str]] = []
        for line in proc_cgroup.read_text(encoding="ascii").splitlines():
            hierarchy, controllers, relative = line.split(":", 2)
            entries.append(
                (hierarchy, tuple(controllers.split(",")) if controllers else (), relative)
            )
        mounts = read_cgroup_mounts(mountinfo)
        unified = next(
            (
                relative
                for hierarchy, controllers, relative in entries
                if hierarchy == "0" and not controllers
            ),
            None,
        )
        if unified is not None:
            membership = resolve_cgroup_membership("unified", unified, mounts, filesystem="cgroup2")
            if membership is not None and (membership.resolved_path / "cpu.max").is_file():
                path = membership.resolved_path
                return CgroupLayout("V2", path, path, path, (membership,))

        process_paths: dict[str, str] = {}
        for _hierarchy, controllers, relative in entries:
            for controller in controllers:
                process_paths[controller] = relative
        memberships = {
            controller: resolve_cgroup_membership(
                controller,
                process_paths[controller],
                mounts,
                filesystem="cgroup",
            )
            for controller in ("cpu", "cpuset", "memory")
            if controller in process_paths
        }
        if all(memberships.get(name) is not None for name in ("cpu", "cpuset", "memory")):
            exact = tuple(memberships[name] for name in ("cpu", "cpuset", "memory"))
            return CgroupLayout(
                "V1",
                exact[0].resolved_path,
                exact[1].resolved_path,
                exact[2].resolved_path,
                exact,
            )
    except (OSError, ValueError):
        return None
    return None


def normalized_cgroup_values(layout: CgroupLayout | None) -> dict[str, object]:
    names = (
        "cpu.max",
        "cpu.stat",
        "cpuset.cpus.effective",
        "memory.current",
        "memory.max",
    )
    if layout is None:
        return {name: unavailable("cgroup allocation path not available") for name in names}
    if layout.mode == "V2":
        return {
            "cpu.max": read_text(layout.cpu / "cpu.max", "cgroup cpu.max"),
            "cpu.stat": parse_key_values(read_text(layout.cpu / "cpu.stat", "cgroup cpu.stat")),
            "cpuset.cpus.effective": read_text(
                layout.cpuset / "cpuset.cpus.effective", "cgroup cpuset.cpus.effective"
            ),
            "memory.current": read_text(layout.memory / "memory.current", "cgroup memory.current"),
            "memory.max": read_text(layout.memory / "memory.max", "cgroup memory.max"),
        }

    quota = read_text(layout.cpu / "cpu.cfs_quota_us", "cgroup v1 cpu quota")
    period = read_text(layout.cpu / "cpu.cfs_period_us", "cgroup v1 cpu period")
    if quota["status"] == "AVAILABLE" and period["status"] == "AVAILABLE":
        try:
            quota_value = int(str(quota["value"]))
            period_value = int(str(period["value"]))
            cpu_max = available(f"{'max' if quota_value < 0 else quota_value} {period_value}")
        except ValueError as error:
            cpu_max = unavailable(f"cgroup v1 cpu limit: {type(error).__name__}")
    else:
        cpu_max = unavailable("cgroup v1 cpu quota/period unavailable")
    cpuset_path = layout.cpuset / "cpuset.effective_cpus"
    if not cpuset_path.is_file():
        cpuset_path = layout.cpuset / "cpuset.cpus"
    return {
        "cpu.max": cpu_max,
        "cpu.stat": parse_key_values(read_text(layout.cpu / "cpu.stat", "cgroup v1 cpu.stat")),
        "cpuset.cpus.effective": read_text(cpuset_path, "cgroup v1 cpuset CPUs"),
        "memory.current": read_text(
            layout.memory / "memory.usage_in_bytes", "cgroup v1 memory usage"
        ),
        "memory.max": read_text(layout.memory / "memory.limit_in_bytes", "cgroup v1 memory limit"),
    }


def proc_stat() -> dict[str, object]:
    try:
        result: dict[str, int] = {}
        for line in Path("/proc/stat").read_text(encoding="ascii").splitlines():
            pieces = line.split()
            if len(pieces) == 2 and pieces[0] in {"ctxt", "procs_running", "procs_blocked"}:
                result[pieces[0]] = int(pieces[1])
        if set(result) != {"ctxt", "procs_running", "procs_blocked"}:
            return unavailable("/proc/stat lacks required scheduler counters")
        return available(result)
    except (OSError, UnicodeError, ValueError) as error:
        return unavailable(f"/proc/stat: {type(error).__name__}")


def affinity() -> dict[str, object]:
    getter = getattr(os, "sched_getaffinity", None)
    if getter is None:
        return unavailable("os.sched_getaffinity is unavailable")
    try:
        cpus = sorted(getter(0))
    except OSError as error:
        return unavailable(f"sched_getaffinity: {type(error).__name__}")
    return available(cpus)


def load_host_receipt(
    path: Path, manifest: dict[str, Any], allocation: dict[str, Any]
) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    try:
        receipt = json.loads(raw, object_pairs_hook=contract.reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise contract.DiagnosticError("HOST_RECEIPT_INVALID_JSON") from error
    contract.exact_object(
        receipt,
        {
            "collected_at_utc",
            "collector_sha256",
            "container",
            "diagnostic_campaign_id",
            "host",
            "receipt_nonce",
            "resources",
            "schema_version",
            "type_name",
        },
        "HOST_RECEIPT_FIELDS",
    )
    contract.require(receipt["schema_version"] == contract.SCHEMA_VERSION, "HOST_RECEIPT_SCHEMA")
    contract.require(receipt["type_name"] == contract.HOST_RECEIPT_TYPE, "HOST_RECEIPT_TYPE")
    contract.require(
        receipt["diagnostic_campaign_id"] == manifest["diagnostic_campaign_id"],
        "HOST_RECEIPT_CAMPAIGN",
    )
    environment = manifest["environment"]
    contract.require(
        receipt["receipt_nonce"] == environment["host_receipt_nonce"], "HOST_RECEIPT_NONCE"
    )
    contract.require(
        receipt["collector_sha256"] == environment["host_collector_sha256"],
        "HOST_RECEIPT_COLLECTOR",
    )
    contract.strict_text(receipt["collected_at_utc"], "HOST_RECEIPT_TIME")
    try:
        instant_ns(receipt["collected_at_utc"])
    except (ValueError, OverflowError) as error:
        raise contract.DiagnosticError("HOST_RECEIPT_TIME_INVALID") from error
    container = contract.exact_object(
        receipt["container"],
        {"container_id", "image_digest", "runtime", "runtime_version"},
        "HOST_RECEIPT_CONTAINER_FIELDS",
    )
    contract.require(
        isinstance(container["container_id"], str)
        and re.fullmatch(r"[0-9a-f]{12,64}", container["container_id"]) is not None,
        "HOST_RECEIPT_CONTAINER_ID",
    )
    expected_container = allocation["container"]
    contract.require(
        container["image_digest"] == expected_container["image_digest"], "HOST_RECEIPT_IMAGE"
    )
    contract.require(container["runtime"] == expected_container["runtime"], "HOST_RECEIPT_RUNTIME")
    contract.require(
        container["runtime_version"] == expected_container["runtime_version"],
        "HOST_RECEIPT_RUNTIME_VERSION",
    )
    resources = contract.exact_object(
        receipt["resources"],
        {"cgroup_mode", "cpu_max", "cpuset_cpus_effective", "memory_max"},
        "HOST_RECEIPT_RESOURCE_FIELDS",
    )
    for name in resources:
        contract.require(
            resources[name] == allocation["resources"][name], "HOST_RECEIPT_RESOURCE", name
        )
    host = contract.exact_object(
        receipt["host"], {"machine_id_sha256", "operating_system"}, "HOST_RECEIPT_HOST_FIELDS"
    )
    contract.content_id(host["machine_id_sha256"], "HOST_RECEIPT_MACHINE")
    contract.strict_text(host["operating_system"], "HOST_RECEIPT_OPERATING_SYSTEM")
    return receipt, raw


def environment_snapshot(
    manifest: dict[str, Any], allocation: dict[str, Any], host_receipt: dict[str, Any]
) -> dict[str, object]:
    layout = cgroup_layout()
    cgroup_values = normalized_cgroup_values(layout)
    environment = manifest["environment"]
    container_identity = available(host_receipt["container"])
    return {
        # The measured runtime is Java, whose exact cgroup-aware value was
        # already exercised by the allocation dry-run.  Python's os.cpu_count
        # can report the Docker VM host count under cgroup v1, so retain it
        # separately instead of mislabelling it as the lane's allocation.
        "available_processors": allocation["resources"]["available_processors"],
        "cgroup_mode": layout.mode if layout is not None else "NOT_AVAILABLE",
        "cgroup_paths": (
            {
                "cpu": str(layout.cpu),
                "cpuset": str(layout.cpuset),
                "memory": str(layout.memory),
            }
            if layout is not None
            else "NOT_AVAILABLE"
        ),
        "cgroup_membership": (
            [membership.as_evidence() for membership in layout.memberships]
            if layout is not None
            else "NOT_AVAILABLE"
        ),
        "cgroup_values": cgroup_values,
        "container_image_digest": environment["container_image_digest"],
        "container_identity": container_identity,
        "container_runtime": environment["container_runtime"],
        "cpu_affinity": affinity(),
        "kernel_release": platform.release(),
        "machine": platform.machine(),
        "memory_host": read_text(Path("/proc/meminfo"), "/proc/meminfo"),
        "operating_system": platform.system(),
        "platform": platform.platform(),
        "python_os_cpu_count": os.cpu_count(),
        "python": platform.python_version(),
        "wsl_interop": (
            available(os.environ["WSL_INTEROP"])
            if "WSL_INTEROP" in os.environ
            else unavailable("WSL_INTEROP not present in the qualification container")
        ),
        "host_receipt": host_receipt,
        "host_telemetry_state": "AWAITING_LANES_COMPLETE_HANDSHAKE",
    }


def validate_host_events(
    value: object, code: str, *, capture_start_ns: int, capture_end_ns: int
) -> dict[str, object]:
    status = contract.availability(value)
    contract.require(isinstance(value, dict), f"{code}_SHAPE")
    if status == "NOT_AVAILABLE":
        contract.exact_object(value, {"reason", "status"}, f"{code}_FIELDS")
        return value
    record = contract.exact_object(value, {"status", "value"}, f"{code}_FIELDS")
    events = record["value"]
    contract.require(isinstance(events, list), f"{code}_EVENTS")
    for index, raw_event in enumerate(events):
        event = contract.exact_object(
            raw_event,
            {
                "category",
                "detail_sha256",
                "end_wall_time_ns",
                "event_id",
                "provider",
                "start_wall_time_ns",
            },
            f"{code}_EVENT_FIELDS",
        )
        contract.strict_text(event["category"], f"{code}_CATEGORY")
        contract.content_id(event["detail_sha256"], f"{code}_DETAIL")
        contract.require(
            (isinstance(event["event_id"], str) and event["event_id"] != "")
            or (type(event["event_id"]) is int and event["event_id"] >= 0),
            f"{code}_EVENT_ID",
        )
        contract.strict_text(event["provider"], f"{code}_PROVIDER")
        start = contract.strict_int(event["start_wall_time_ns"], f"{code}_START", minimum=1)
        end = contract.strict_int(event["end_wall_time_ns"], f"{code}_END", minimum=1)
        contract.require(end >= start, f"{code}_INTERVAL", str(index))
        contract.require(
            capture_start_ns <= start <= end <= capture_end_ns,
            f"{code}_CAPTURE_INTERVAL",
            str(index),
        )
    return record


def load_host_telemetry(
    path: Path,
    manifest: dict[str, Any],
    *,
    lanes_complete_sha256: str,
    wait_seconds: int,
) -> tuple[dict[str, Any], bytes]:
    deadline = time.monotonic() + wait_seconds
    while not path.is_file() and time.monotonic() < deadline:
        time.sleep(0.1)
    contract.require(path.is_file(), "HOST_TELEMETRY_TIMEOUT", str(path))
    raw = path.read_bytes()
    try:
        telemetry = json.loads(raw, object_pairs_hook=contract.reject_duplicate_keys)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise contract.DiagnosticError("HOST_TELEMETRY_INVALID_JSON") from error
    contract.exact_object(
        telemetry,
        {
            "capture_ended_at_utc",
            "capture_started_at_utc",
            "collector_sha256",
            "diagnostic_campaign_id",
            "docker_wsl_events",
            "lanes_complete_sha256",
            "receipt_nonce",
            "schema_version",
            "type_name",
            "windows_hardware_events",
        },
        "HOST_TELEMETRY_FIELDS",
    )
    contract.require(
        telemetry["schema_version"] == contract.SCHEMA_VERSION, "HOST_TELEMETRY_SCHEMA"
    )
    contract.require(telemetry["type_name"] == contract.HOST_TELEMETRY_TYPE, "HOST_TELEMETRY_TYPE")
    contract.require(
        telemetry["collector_sha256"] == manifest["environment"]["host_collector_sha256"],
        "HOST_TELEMETRY_COLLECTOR",
    )
    contract.require(
        telemetry["diagnostic_campaign_id"] == manifest["diagnostic_campaign_id"],
        "HOST_TELEMETRY_CAMPAIGN",
    )
    contract.require(
        telemetry["receipt_nonce"] == manifest["environment"]["host_receipt_nonce"],
        "HOST_TELEMETRY_NONCE",
    )
    contract.require(
        telemetry["lanes_complete_sha256"] == lanes_complete_sha256,
        "HOST_TELEMETRY_LANES_COMPLETE",
    )
    start_text = contract.strict_text(telemetry["capture_started_at_utc"], "HOST_TELEMETRY_START")
    end_text = contract.strict_text(telemetry["capture_ended_at_utc"], "HOST_TELEMETRY_END")
    try:
        capture_start_ns = instant_ns(start_text)
        capture_end_ns = instant_ns(end_text)
    except (ValueError, OverflowError) as error:
        raise contract.DiagnosticError("HOST_TELEMETRY_TIME_INVALID") from error
    contract.require(capture_end_ns >= capture_start_ns, "HOST_TELEMETRY_TIME_ORDER")
    validate_host_events(
        telemetry["docker_wsl_events"],
        "HOST_DOCKER_WSL",
        capture_start_ns=capture_start_ns,
        capture_end_ns=capture_end_ns,
    )
    validate_host_events(
        telemetry["windows_hardware_events"],
        "HOST_WINDOWS_HARDWARE",
        capture_start_ns=capture_start_ns,
        capture_end_ns=capture_end_ns,
    )
    return telemetry, raw


def host_fault_overlap(
    telemetry: dict[str, Any], scheduled_wall_ns: int, actual_wall_ns: int
) -> bool:
    for name in ("docker_wsl_events", "windows_hardware_events"):
        value = availability_value(telemetry.get(name))
        if not isinstance(value, list):
            continue
        if any(
            isinstance(event, dict)
            and type(event.get("start_wall_time_ns")) is int
            and type(event.get("end_wall_time_ns")) is int
            and int(event["start_wall_time_ns"]) <= actual_wall_ns
            and int(event["end_wall_time_ns"]) >= scheduled_wall_ns
            for event in value
        ):
            return True
    return False


def verify_live_allocation(allocation: dict[str, Any], snapshot: dict[str, object]) -> None:
    resources = allocation["resources"]
    cgroup = snapshot["cgroup_values"]
    contract.require(isinstance(cgroup, dict), "LIVE_CGROUP_VALUES")

    def observed(name: str) -> object:
        value = availability_value(cgroup.get(name))
        contract.require(value is not None, "LIVE_ALLOCATION_NOT_AVAILABLE", name)
        return value

    contract.require(snapshot.get("cgroup_mode") == resources["cgroup_mode"], "LIVE_CGROUP_MODE")
    contract.require(observed("cpu.max") == resources["cpu_max"], "LIVE_CPU_MAX_MISMATCH")
    contract.require(
        observed("cpuset.cpus.effective") == resources["cpuset_cpus_effective"],
        "LIVE_CPUSET_MISMATCH",
    )
    contract.require(observed("memory.max") == resources["memory_max"], "LIVE_MEMORY_MISMATCH")
    affinity_value = availability_value(snapshot["cpu_affinity"])
    contract.require(isinstance(affinity_value, list), "LIVE_AFFINITY_NOT_AVAILABLE")
    contract.require(
        affinity_value == parse_cpuset(str(resources["cpuset_cpus_effective"])),
        "LIVE_AFFINITY_CPUSET_MISMATCH",
    )
    contract.require(
        availability_status(snapshot["container_identity"]),
        "LIVE_CONTAINER_IDENTITY_MISMATCH",
    )


def parse_cpuset(value: str) -> list[int]:
    contract.require(
        re.fullmatch(r"\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*", value) is not None, "CPUSET_SYNTAX"
    )
    result: list[int] = []
    for item in value.split(","):
        bounds = item.split("-", 1)
        first = int(bounds[0])
        last = int(bounds[-1])
        contract.require(first <= last, "CPUSET_RANGE")
        result.extend(range(first, last + 1))
    contract.require(result == sorted(set(result)), "CPUSET_ORDER_OR_OVERLAP")
    return result


def process_tree_topology(
    root_pid: int, proc_root: Path = Path("/proc")
) -> dict[int, dict[int, tuple[int, ...]]]:
    pending = [root_pid]
    result: dict[int, dict[int, tuple[int, ...]]] = {}
    seen: set[int] = set()
    while pending:
        pid = pending.pop()
        if pid in seen:
            continue
        seen.add(pid)
        process_root = proc_root / str(pid)
        if not process_root.is_dir():
            raise FileNotFoundError(f"process disappeared during snapshot: {process_root}")
        task_entries = list((process_root / "task").iterdir())
        task_directories: list[Path] = []
        for item in task_entries:
            if not item.name.isdecimal():
                continue
            if not item.is_dir():
                raise FileNotFoundError(f"task disappeared during snapshot: {item}")
            task_directories.append(item)
        task_directories.sort(key=lambda item: int(item.name))
        if not task_directories:
            raise FileNotFoundError(
                f"process has no readable tasks during snapshot: {process_root}"
            )
        task_children: dict[int, tuple[int, ...]] = {}
        for task_directory in task_directories:
            children = (task_directory / "children").read_text(encoding="ascii")
            child_pids = tuple(sorted(int(item) for item in children.split()))
            if any(child_pid <= 0 for child_pid in child_pids):
                raise ValueError(f"invalid child pid in task snapshot: {task_directory}")
            task_children[int(task_directory.name)] = child_pids
            pending.extend(child_pids)
        result[pid] = task_children
    return result


def process_tree_pids(root_pid: int, proc_root: Path = Path("/proc")) -> list[int]:
    return sorted(process_tree_topology(root_pid, proc_root))


def process_reaches_root(records: dict[int, dict[str, object]], pid: int, root_pid: int) -> bool:
    ancestors: set[int] = set()
    current = pid
    while current in records and current not in ancestors:
        if current == root_pid:
            return True
        ancestors.add(current)
        current = int(records[current]["parent_pid"])
    return False


def derive_process_roles(
    records: dict[int, dict[str, object]],
    *,
    root_pid: int,
    target_executable: str,
    tracer_wrapped: bool,
) -> dict[int, tuple[str, bool]]:
    reachable = {pid for pid in records if process_reaches_root(records, pid, root_pid)}
    target_roots = {
        pid
        for pid, record in records.items()
        if pid in reachable and record["executable"] == target_executable
    }

    def belongs_to_target(pid: int) -> bool:
        ancestors: set[int] = set()
        current = pid
        while current in records and current not in ancestors:
            if current in target_roots:
                return True
            ancestors.add(current)
            current = int(records[current]["parent_pid"])
        return False

    result: dict[int, tuple[str, bool]] = {}
    for pid in records:
        if pid not in reachable:
            role = "EXCLUDED_NON_TARGET_DESCENDANT"
        elif tracer_wrapped and pid == root_pid:
            role = "TRACER"
        elif pid in target_roots:
            role = "TARGET_JAVA"
        elif belongs_to_target(pid):
            role = "TARGET_RUNTIME_DESCENDANT"
        else:
            role = "EXCLUDED_NON_TARGET_DESCENDANT"
        result[pid] = (role, role in {"TARGET_JAVA", "TARGET_RUNTIME_DESCENDANT"})
    return result


def process_tree_sample(
    root_pid: int | None,
    target_executable: str | None,
    tracer_wrapped: bool | None,
    proc_root: Path = Path("/proc"),
) -> dict[str, object]:
    if root_pid is None or target_executable is None or tracer_wrapped is None:
        return unavailable("lane process has not started")
    clock_ticks = os.sysconf("SC_CLK_TCK") if hasattr(os, "sysconf") else None
    if not isinstance(clock_ticks, int) or clock_ticks <= 0:
        return unavailable("SC_CLK_TCK is unavailable")
    raw_records: dict[int, dict[str, object]] = {}
    try:
        sampled_topology = process_tree_topology(root_pid, proc_root)
        sampled_pids = sorted(sampled_topology)
        for pid in sampled_pids:
            process_root = proc_root / str(pid)
            raw = (process_root / "stat").read_text(encoding="ascii")
            close = raw.rfind(")")
            contract.require(close >= 0, "PROC_STAT_COMM")
            fields = raw[close + 2 :].split()
            contract.require(len(fields) >= 20, "PROC_STAT_FIELDS")
            schedstat = read_text(process_root / "schedstat", f"schedstat pid {pid}")
            raw_records[pid] = {
                "cpu_ticks": int(fields[11]) + int(fields[12]),
                "executable": str((process_root / "exe").resolve(strict=True)),
                "parent_pid": int(fields[1]),
                "pid": pid,
                "schedstat": schedstat,
                "start_time_ticks": int(fields[19]),
                "state": fields[0],
            }
        contract.require(
            process_tree_topology(root_pid, proc_root) == sampled_topology,
            "PROC_TREE_CHANGED_DURING_SAMPLE",
        )
    except (OSError, UnicodeError, ValueError, contract.DiagnosticError) as error:
        return unavailable(f"process tree sample: {type(error).__name__}")

    roles = derive_process_roles(
        raw_records,
        root_pid=root_pid,
        target_executable=target_executable,
        tracer_wrapped=tracer_wrapped,
    )
    records: list[dict[str, object]] = []
    for pid, raw_record in sorted(raw_records.items()):
        record = dict(raw_record)
        role, target_cpu = roles[pid]
        record["role"] = role
        record["target_cpu"] = target_cpu
        records.append(record)
    return available(
        {
            "clock_ticks_per_second": clock_ticks,
            "processes": records,
            "root_pid": root_pid,
            "target_executable": target_executable,
            "tracer_wrapped": tracer_wrapped,
        }
    )


def sample_host(
    root_pid: int | None,
    target_executable: str | None,
    tracer_wrapped: bool | None,
) -> dict[str, object]:
    sample_begin = time.monotonic_ns()
    wall_begin = time.time_ns()
    layout = cgroup_layout()
    values = normalized_cgroup_values(layout)
    result = {
        "cgroup_cpu_stat": values["cpu.stat"],
        "cgroup_mode": layout.mode if layout is not None else "NOT_AVAILABLE",
        "cpu_pressure": read_text(Path("/proc/pressure/cpu"), "CPU PSI"),
        "io_pressure": read_text(Path("/proc/pressure/io"), "IO PSI"),
        "load_average": read_text(Path("/proc/loadavg"), "/proc/loadavg"),
        "proc_stat": proc_stat(),
        "sample_begin_monotonic_ns": sample_begin,
        "sample_begin_wall_time_ns": wall_begin,
        "target_process_tree": process_tree_sample(root_pid, target_executable, tracer_wrapped),
    }
    result["sample_end_monotonic_ns"] = time.monotonic_ns()
    result["sample_end_wall_time_ns"] = time.time_ns()
    return result


class HostSampler:
    def __init__(self, output: Path, interval_ms: int) -> None:
        self._output = output
        self._interval = interval_ms / 1_000
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._root_pid: int | None = None
        self._target_executable: str | None = None
        self._tracer_wrapped: bool | None = None
        self._lock = threading.Lock()
        self._failure: BaseException | None = None

    def set_process_identity(
        self, pid: int, *, target_executable: Path, tracer_wrapped: bool
    ) -> None:
        contract.require(pid > 0, "HOST_SAMPLER_PID")
        resolved_target = target_executable.resolve(strict=True)
        contract.require(resolved_target.is_file(), "HOST_SAMPLER_TARGET_EXECUTABLE")
        with self._lock:
            contract.require(self._root_pid is None, "HOST_SAMPLER_PID_SET_TWICE")
            self._root_pid = pid
            self._target_executable = str(resolved_target)
            self._tracer_wrapped = tracer_wrapped

    def start(self) -> None:
        contract.require(self._thread is None, "HOST_SAMPLER_STARTED_TWICE")
        self._thread = threading.Thread(target=self._run, name="sidecar-diagnostic-host-sampler")
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        contract.require(self._thread is not None, "HOST_SAMPLER_NOT_STARTED")
        self._thread.join(timeout=10)
        contract.require(not self._thread.is_alive(), "HOST_SAMPLER_DID_NOT_STOP")
        with self._lock:
            failure = self._failure
        if failure is not None:
            raise contract.DiagnosticError(
                f"HOST_SAMPLER_FAILED:{type(failure).__name__}"
            ) from failure

    def _run(self) -> None:
        try:
            with self._output.open("xb", buffering=0) as stream:
                deadline = time.monotonic()
                while not self._stop.is_set():
                    with self._lock:
                        root_pid = self._root_pid
                        target_executable = self._target_executable
                        tracer_wrapped = self._tracer_wrapped
                    stream.write(
                        contract.canonical_bytes(
                            sample_host(root_pid, target_executable, tracer_wrapped)
                        )
                        + b"\n"
                    )
                    deadline += self._interval
                    self._stop.wait(max(0.0, deadline - time.monotonic()))
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException as error:
            with self._lock:
                self._failure = error
            self._stop.set()


def expand_argument(
    argument: str,
    *,
    profile: str,
    source_root: Path,
    allocation_root: str,
    lane_directory: Path,
    duration: int,
) -> str:
    replacements = {
        "{ALLOCATION_ROOT}": allocation_root,
        "{DURATION_SECONDS}": str(duration),
        "{EVENT_LOG}": str(lane_directory / "operations.jsonl"),
        "{EVIDENCE_ROOT}": str(lane_directory.parent),
        "{JFR_FILE}": str(lane_directory / "java.jfr"),
        "{LANE_DIRECTORY}": str(lane_directory),
        "{OFFERS_PER_SECOND}": str(contract.OFFER_RATE),
        "{PROFILE_ID}": profile,
        "{SOURCE_ROOT}": str(source_root),
    }
    result = argument
    for marker, value in replacements.items():
        result = result.replace(marker, value)
    contract.require("{" not in result and "}" not in result, "UNKNOWN_ARGV_PLACEHOLDER", result)
    return result


@dataclass(frozen=True)
class PreparedLane:
    lane: dict[str, Any]
    profile: str
    lane_directory: Path
    argv: tuple[str, ...]
    environment: dict[str, str]
    working_directory: Path
    trace_prefix: tuple[str, ...]
    jfr_tool: Path


def allocation_artifacts(allocation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    artifacts = allocation["artifacts"]
    contract.require(isinstance(artifacts, list), "ALLOCATION_ARTIFACTS")
    result = {str(item["artifact_id"]): item for item in artifacts if isinstance(item, dict)}
    contract.require(
        list(result) == contract.ALLOCATION_ARTIFACT_IDS,
        "ALLOCATION_ARTIFACT_INDEX",
    )
    return result


def option_value(argv: tuple[str, ...], option: str, profile: str) -> str:
    positions = [index for index, item in enumerate(argv) if item == option]
    contract.require(len(positions) == 1, "LANE_OPTION_CARDINALITY", f"{profile}:{option}")
    position = positions[0]
    contract.require(position + 1 < len(argv), "LANE_OPTION_VALUE", f"{profile}:{option}")
    return argv[position + 1]


def prepare_lanes(
    manifest: dict[str, Any],
    allocation: dict[str, Any],
    *,
    source_root: Path,
    evidence_root: Path,
) -> list[PreparedLane]:
    records = allocation_artifacts(allocation)
    expected = {identifier: str(record["path"]) for identifier, record in records.items()}
    allocation_root = str(manifest["environment"]["allocation_root"])
    duration = int(manifest["schedule"]["duration_seconds_per_lane"])
    prepared: list[PreparedLane] = []
    for lane in manifest["lanes"]:
        profile = str(lane["profile_id"])
        lane_directory = evidence_root / profile.lower()
        argv = tuple(
            expand_argument(
                item,
                profile=profile,
                source_root=source_root,
                allocation_root=allocation_root,
                lane_directory=lane_directory,
                duration=duration,
            )
            for item in lane["argv"]
        )
        trace_prefix = tuple(
            expand_argument(
                item,
                profile=profile,
                source_root=source_root,
                allocation_root=allocation_root,
                lane_directory=lane_directory,
                duration=duration,
            )
            for item in lane["strace_fsync"]["argv_prefix"]
        )
        lane_environment = {
            str(key): expand_argument(
                str(item),
                profile=profile,
                source_root=source_root,
                allocation_root=allocation_root,
                lane_directory=lane_directory,
                duration=duration,
            )
            for key, item in lane["environment"].items()
        }
        lane_environment.update(
            {
                "DELTA_DIAGNOSTIC_AUTHORITY": "DIAGNOSTIC_ONLY",
                "DELTA_DIAGNOSTIC_EVENT_LOG": str(lane_directory / "operations.jsonl"),
                "DELTA_DIAGNOSTIC_OFFERS_PER_SECOND": str(contract.OFFER_RATE),
                "DELTA_DIAGNOSTIC_PROFILE": profile,
            }
        )
        working_directory = Path(
            expand_argument(
                str(lane["working_directory"]),
                profile=profile,
                source_root=source_root,
                allocation_root=allocation_root,
                lane_directory=lane_directory,
                duration=duration,
            )
        ).resolve(strict=True)
        contract.require(
            working_directory == source_root.resolve(strict=True), "LANE_WORKING_DIRECTORY"
        )
        contract.require(argv[0] == expected["JAVA_EXECUTABLE"], "LANE_JAVA_ARTIFACT_MISMATCH")
        contract.require(
            option_value(argv, "-cp", profile) == expected["JAVA_CLASSES_JAR"],
            "LANE_CLASSPATH_ARTIFACT_MISMATCH",
        )
        contract.require(
            option_value(argv, "--corpus", profile) == expected["CANONICAL_CORPUS"],
            "LANE_CORPUS_ARTIFACT_MISMATCH",
        )
        if profile == "EMBEDDED_FFM":
            contract.require(
                option_value(argv, "--native-library", profile) == expected["NATIVE_LIBRARY"],
                "LANE_NATIVE_ARTIFACT_MISMATCH",
            )
        else:
            contract.require(
                option_value(argv, "--sidecar-executable", profile)
                == expected["SIDECAR_EXECUTABLE"],
                "LANE_SIDECAR_ARTIFACT_MISMATCH",
            )
        contract.require(
            trace_prefix[0] == expected["STRACE_EXECUTABLE"],
            "LANE_STRACE_ARTIFACT_MISMATCH",
        )
        jfr_tool = Path(expected["JFR_EXECUTABLE"])
        java_tool = Path(expected["JAVA_EXECUTABLE"])
        expected_jfr_name = "jfr.exe" if java_tool.name.lower() == "java.exe" else "jfr"
        contract.require(
            jfr_tool == java_tool.with_name(expected_jfr_name),
            "LANE_JFR_ARTIFACT_MISMATCH",
        )
        prepared.append(
            PreparedLane(
                lane=lane,
                profile=profile,
                lane_directory=lane_directory,
                argv=argv,
                environment=lane_environment,
                working_directory=working_directory,
                trace_prefix=trace_prefix,
                jfr_tool=jfr_tool,
            )
        )
    return prepared


def exact_subprocess(
    argv: list[str],
    *,
    environment: dict[str, str],
    working_directory: Path,
    timeout: int,
) -> tuple[subprocess.CompletedProcess[bytes], dict[str, object]]:
    invocation = contract.invocation_record(
        argv,
        environment=environment,
        working_directory=working_directory,
    )
    result = subprocess.run(
        invocation["argv"],
        check=False,
        capture_output=True,
        cwd=invocation["working_directory"],
        env=invocation["environment"],
        timeout=timeout,
    )
    receipt = {
        **invocation,
        "exit_code": result.returncode,
        "stderr_sha256": contract.sha256_id(result.stderr),
        "stdout_sha256": contract.sha256_id(result.stdout),
    }
    return result, receipt


def invocation_probe(
    argv: list[str],
    *,
    environment: dict[str, str],
    working_directory: Path,
    expected_exit_codes: set[int],
    label: str,
) -> tuple[dict[str, object], bytes, bytes]:
    try:
        result, receipt = exact_subprocess(
            argv,
            environment=environment,
            working_directory=working_directory,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        detail = f"PREFLIGHT_{label}_INVOCATION:{type(error).__name__}"
        raise contract.DiagnosticError(detail) from error
    contract.require(
        result.returncode in expected_exit_codes,
        f"PREFLIGHT_{label}_EXIT",
        str(result.returncode),
    )
    return receipt, result.stdout, result.stderr


def mount_is_read_only(path: Path) -> bool:
    if os.name != "posix":
        return False
    try:
        root = path.resolve(strict=True)
        candidates: list[tuple[int, set[str]]] = []
        for line in Path("/proc/self/mountinfo").read_text(encoding="utf-8").splitlines():
            fields = line.split()
            if len(fields) < 6:
                continue
            mount_text = fields[4]
            for encoded, decoded in (("\\040", " "), ("\\011", "\t"), ("\\134", "\\")):
                mount_text = mount_text.replace(encoded, decoded)
            mount = Path(mount_text).resolve(strict=True)
            if mount == root or mount in root.parents:
                candidates.append((len(mount.parts), set(fields[5].split(","))))
        return bool(candidates) and "ro" in max(candidates, key=lambda item: item[0])[1]
    except (OSError, UnicodeError):
        return False


def jfr_profile_enabled_events(java: Path, selected_events: list[str]) -> list[str]:
    profile = java.parent.parent / "lib" / "jfr" / "profile.jfc"
    contract.require(profile.is_file(), "PREFLIGHT_JFR_PROFILE_MISSING", str(profile))
    try:
        root = ET.parse(profile).getroot()
    except (ET.ParseError, OSError) as error:
        raise contract.DiagnosticError("PREFLIGHT_JFR_PROFILE_INVALID") from error
    settings: dict[str, bool] = {}
    for event in root.iter():
        if event.tag.rsplit("}", 1)[-1] != "event" or "name" not in event.attrib:
            continue
        enabled = None
        for setting in event:
            if (
                setting.tag.rsplit("}", 1)[-1] == "setting"
                and setting.attrib.get("name") == "enabled"
            ):
                enabled = (setting.text or "").strip().lower() == "true"
        if enabled is not None:
            settings[event.attrib["name"]] = enabled
    missing = [name for name in selected_events if settings.get(name) is not True]
    contract.require(not missing, "PREFLIGHT_JFR_EVENTS_NOT_ENABLED", ",".join(missing))
    return list(selected_events)


def psi_capability() -> dict[str, object]:
    values = {
        "cpu": read_text(Path("/proc/pressure/cpu"), "CPU PSI"),
        "io": read_text(Path("/proc/pressure/io"), "IO PSI"),
    }
    status = (
        "AVAILABLE"
        if all(pressure_total(value) is not None for value in values.values())
        else "NOT_AVAILABLE"
    )
    return {
        "miss_policy": "ANY_MISS_IS_INCONCLUSIVE_WHEN_PSI_NOT_AVAILABLE",
        "status": status,
        "values": values,
    }


def probe_strace_child(
    prefix: tuple[str, ...], *, environment: dict[str, str], working_directory: Path
) -> dict[str, object]:
    with tempfile.TemporaryDirectory(prefix="delta-diagnostic-strace-") as temporary:
        root = Path(temporary)
        trace = root / "probe.strace"
        argv = [*prefix, "-o", str(trace), sys.executable, "-c", STRACE_CHILD_PROBE]
        result, invocation = exact_subprocess(
            argv,
            environment=environment,
            working_directory=working_directory,
            timeout=30,
        )
        contract.require(
            result.returncode == 0, "PREFLIGHT_STRACE_CHILD_EXIT", str(result.returncode)
        )
        files = sorted(root.glob("probe.strace*"))
        parsed = parse_strace_files(files, artifact_root=root)
        contract.require(availability_status(parsed), "PREFLIGHT_STRACE_CHILD_PARSE")
        value = availability_value(parsed)
        contract.require(
            isinstance(value, dict) and len(value.get("fsync_events", [])) >= 1,
            "PREFLIGHT_STRACE_CHILD_FSYNC_MISSING",
        )
        return {
            "event_count": len(value["fsync_events"]),
            "invocation": invocation,
            "stderr_sha256": contract.sha256_id(result.stderr),
            "stdout_sha256": contract.sha256_id(result.stdout),
        }


def probe_jfr_recording(
    java: Path,
    jfr: Path,
    jar: Path,
    selected_events: list[str],
    *,
    environment: dict[str, str],
    working_directory: Path,
) -> dict[str, object]:
    enabled = jfr_profile_enabled_events(java, selected_events)
    with tempfile.TemporaryDirectory(prefix="delta-diagnostic-jfr-") as temporary:
        recording = Path(temporary) / "probe.jfr"
        java_argv = [
            str(java),
            f"-XX:StartFlightRecording=filename={recording},settings=profile,dumponexit=true",
            "--enable-native-access=ALL-UNNAMED",
            "-cp",
            str(jar),
            JFR_DRY_RUN_CLASS,
        ]
        result, java_invocation = exact_subprocess(
            java_argv,
            environment=environment,
            working_directory=working_directory,
            timeout=60,
        )
        contract.require(
            result.returncode == 0, "PREFLIGHT_JFR_RECORDING_EXIT", str(result.returncode)
        )
        contract.require(
            recording.is_file() and recording.stat().st_size > 0, "PREFLIGHT_JFR_RECORDING"
        )
        jfr_argv = [
            str(jfr),
            "print",
            "--json",
            "--events",
            ",".join(selected_events),
            str(recording),
        ]
        printed, jfr_invocation = exact_subprocess(
            jfr_argv,
            environment=environment,
            working_directory=working_directory,
            timeout=60,
        )
        contract.require(
            printed.returncode == 0, "PREFLIGHT_JFR_PRINT_EXIT", str(printed.returncode)
        )
        try:
            document = json.loads(printed.stdout)
            validate_jfr_document(document, set(selected_events))
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError, OverflowError) as error:
            raise contract.DiagnosticError("PREFLIGHT_JFR_PRINT_INVALID") from error
        events = document["recording"]["events"]
        return {
            "enabled_events": enabled,
            "extracted_event_count": len(events),
            "java_invocation": java_invocation,
            "jfr_invocation": jfr_invocation,
            "recording_sha256": contract.sha256_id(recording.read_bytes()),
            "stderr_sha256": contract.sha256_id(result.stderr),
            "stdout_sha256": contract.sha256_id(result.stdout),
        }


def preflight_allocation(
    allocation: dict[str, Any],
    *,
    allocation_root: Path,
    prepared_lanes: list[PreparedLane] | None = None,
) -> dict[str, object]:
    """Prove exact frozen tools can be invoked before the one-shot seal exists."""

    records = allocation_artifacts(allocation)
    paths = {identifier: Path(str(record["path"])) for identifier, record in records.items()}
    for identifier, path in paths.items():
        contract.require(os.access(path, os.R_OK), "PREFLIGHT_ARTIFACT_NOT_READABLE", identifier)
    for identifier in (
        "JAVA_EXECUTABLE",
        "JFR_EXECUTABLE",
        "SIDECAR_EXECUTABLE",
        "STRACE_EXECUTABLE",
    ):
        contract.require(
            os.access(paths[identifier], os.X_OK),
            "PREFLIGHT_ARTIFACT_NOT_EXECUTABLE",
            identifier,
        )
    contract.require(
        mount_is_read_only(allocation_root),
        "PREFLIGHT_ALLOCATION_ROOT_NOT_READ_ONLY",
        str(allocation_root),
    )

    receipts: dict[str, object] = {}
    contract.require(prepared_lanes is not None and prepared_lanes, "PREFLIGHT_LANES_REQUIRED")
    probe_environment = dict(prepared_lanes[0].environment)
    probe_environment["DELTA_DIAGNOSTIC_PROFILE"] = "PREFLIGHT"
    probe_working_directory = prepared_lanes[0].working_directory
    dry_run, stdout, _ = invocation_probe(
        [
            str(paths["JAVA_EXECUTABLE"]),
            "--enable-native-access=ALL-UNNAMED",
            "-cp",
            str(paths["JAVA_CLASSES_JAR"]),
            JFR_DRY_RUN_CLASS,
        ],
        environment=probe_environment,
        working_directory=probe_working_directory,
        expected_exit_codes={0},
        label="JAVA_DRY_RUN",
    )
    try:
        dry_run_document = json.loads(stdout)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise contract.DiagnosticError("PREFLIGHT_JAVA_DRY_RUN_OUTPUT") from error
    contract.require(
        isinstance(dry_run_document, dict)
        and set(dry_run_document)
        == {
            "authority",
            "available_processors",
            "offers_per_second",
            "status",
            "type_name",
        }
        and dry_run_document["authority"] == "DIAGNOSTIC_ONLY"
        and type(dry_run_document["available_processors"]) is int
        and dry_run_document["available_processors"]
        == allocation["resources"]["available_processors"]
        and dry_run_document["offers_per_second"] == contract.OFFER_RATE
        and dry_run_document["status"] == "PASS"
        and dry_run_document["type_name"] == "FEATURE010_SIDECAR_DIAGNOSTIC_DRY_RUN",
        "PREFLIGHT_JAVA_DRY_RUN_OUTPUT",
    )
    receipts["java_dry_run"] = dry_run
    receipts["jfr"], _, _ = invocation_probe(
        [str(paths["JFR_EXECUTABLE"]), "version"],
        environment=probe_environment,
        working_directory=probe_working_directory,
        expected_exit_codes={0},
        label="JFR",
    )
    receipts["strace"], _, _ = invocation_probe(
        [str(paths["STRACE_EXECUTABLE"]), "--version"],
        environment=probe_environment,
        working_directory=probe_working_directory,
        expected_exit_codes={0},
        label="STRACE",
    )
    sidecar, _, sidecar_stderr = invocation_probe(
        [str(paths["SIDECAR_EXECUTABLE"])],
        environment=probe_environment,
        working_directory=probe_working_directory,
        expected_exit_codes={2},
        label="SIDECAR",
    )
    contract.require(
        b"session and generation are required" in sidecar_stderr,
        "PREFLIGHT_SIDECAR_OUTPUT",
    )
    receipts["sidecar"] = sidecar
    native, _, _ = invocation_probe(
        [
            sys.executable,
            "-c",
            "import ctypes,sys; ctypes.CDLL(sys.argv[1])",
            str(paths["NATIVE_LIBRARY"]),
        ],
        environment=probe_environment,
        working_directory=probe_working_directory,
        expected_exit_codes={0},
        label="NATIVE_LIBRARY",
    )
    receipts["native_library_load"] = native
    receipts["allocation_root_read_only"] = True
    selected_events = list(prepared_lanes[0].lane["jfr_events"])
    contract.require(
        all(list(item.lane["jfr_events"]) == selected_events for item in prepared_lanes),
        "PREFLIGHT_JFR_EVENT_SELECTION_MISMATCH",
    )
    receipts["jfr_recording"] = probe_jfr_recording(
        paths["JAVA_EXECUTABLE"],
        paths["JFR_EXECUTABLE"],
        paths["JAVA_CLASSES_JAR"],
        selected_events,
        environment=probe_environment,
        working_directory=probe_working_directory,
    )
    receipts["strace_child_fsync"] = probe_strace_child(
        prepared_lanes[0].trace_prefix,
        environment=probe_environment,
        working_directory=probe_working_directory,
    )
    receipts["psi"] = psi_capability()
    return receipts


def run_process(
    argv: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    stdout: Path,
    stderr: Path,
    timeout_seconds: int,
    sampler: HostSampler,
    target_executable: Path,
    tracer_wrapped: bool,
) -> tuple[int, bool]:
    timed_out = False
    with stdout.open("xb") as out, stderr.open("xb") as err:
        process = subprocess.Popen(argv, cwd=cwd, env=environment, stdout=out, stderr=err)
        sampler.set_process_identity(
            process.pid,
            target_executable=target_executable,
            tracer_wrapped=tracer_wrapped,
        )
        try:
            exit_code = process.wait(timeout=timeout_seconds)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.terminate()
            try:
                exit_code = process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                exit_code = process.wait(timeout=10)
        out.flush()
        err.flush()
        os.fsync(out.fileno())
        os.fsync(err.fileno())
    return exit_code, timed_out


def jfr_evidence(
    tool: Path,
    java_tool: Path,
    lane: dict[str, Any],
    lane_directory: Path,
    evidence_root: Path,
    *,
    environment: dict[str, str],
    working_directory: Path,
) -> dict[str, object]:
    recording = lane_directory / "java.jfr"
    if not recording.is_file() or recording.stat().st_size == 0:
        return unavailable("JFR recording was not produced")
    if not tool.is_file():
        return unavailable("the exact JDK has no jfr tool")
    summary = lane_directory / "jfr-summary.txt"
    summary_stderr = lane_directory / "jfr-summary.stderr.txt"
    events = lane_directory / "jfr-events.json"
    events_stderr = lane_directory / "jfr-events.stderr.txt"
    try:
        summary_result, summary_invocation = exact_subprocess(
            [str(tool), "summary", str(recording)],
            environment=environment,
            working_directory=working_directory,
            timeout=60,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return unavailable(f"JFR summary invocation failed: {type(error).__name__}")
    summary.write_bytes(summary_result.stdout)
    summary_stderr.write_bytes(summary_result.stderr)
    selected = ",".join(lane["jfr_events"])
    try:
        events_result, events_invocation = exact_subprocess(
            [str(tool), "print", "--json", "--events", selected, str(recording)],
            environment=environment,
            working_directory=working_directory,
            timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return unavailable(f"JFR event extraction failed: {type(error).__name__}")
    events.write_bytes(events_result.stdout)
    events_stderr.write_bytes(events_result.stderr)
    if summary_result.returncode != 0 or events_result.returncode != 0:
        return unavailable("JFR summary or event extraction failed")
    try:
        summary_text = summary_result.stdout.decode("utf-8", errors="strict")
        summary_fields = ("Version:", "Chunks:", "Start:", "Duration:")
        if not all(marker in summary_text for marker in summary_fields):
            raise ValueError("JFR summary lacks required completeness fields")
        event_document = json.loads(events_result.stdout)
        validate_jfr_document(event_document, set(lane["jfr_events"]))
        intervals = jfr_intervals(event_document)
        enabled_events = jfr_profile_enabled_events(java_tool, list(lane["jfr_events"]))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, OverflowError) as error:
        return unavailable(f"JFR JSON event parsing failed: {type(error).__name__}")
    return available(
        {
            "artifacts": {
                "events": artifact(events, evidence_root),
                "events_stderr": artifact(events_stderr, evidence_root),
                "recording": artifact(recording, evidence_root),
                "summary": artifact(summary, evidence_root),
                "summary_stderr": artifact(summary_stderr, evidence_root),
            },
            "enabled_events": enabled_events,
            "event_intervals": intervals,
            "invocations": {
                "events": events_invocation,
                "summary": summary_invocation,
            },
        }
    )


def validate_jfr_document(value: object, selected_events: set[str]) -> None:
    if not isinstance(value, dict):
        raise ValueError("JFR JSON root is not an object")
    recording = value.get("recording")
    if not isinstance(recording, dict):
        raise ValueError("JFR JSON recording is not an object")
    events = recording.get("events")
    if not isinstance(events, list):
        raise ValueError("JFR JSON events is not an array")
    for event in events:
        if not isinstance(event, dict):
            raise ValueError("JFR event is not an object")
        event_type = event.get("type")
        values = event.get("values")
        if not isinstance(event_type, str) or event_type not in selected_events:
            raise ValueError("JFR event type is outside the frozen selection")
        if not isinstance(values, dict):
            raise ValueError("JFR event values is not an object")
        instant_ns(values.get("startTime"))
        duration_ns(values.get("duration"))


def duration_ns(value: object) -> int:
    if type(value) is int:
        return int(value)
    if isinstance(value, str):
        match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(\d+)(?:\.(\d{1,9}))?S", value)
        if match is not None:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3))
            fraction = (match.group(4) or "").ljust(9, "0")
            return ((hours * 60 + minutes) * 60 + seconds) * 1_000_000_000 + int(fraction or "0")
    raise ValueError("unsupported JFR duration")


def instant_ns(value: object) -> int:
    if not isinstance(value, str):
        raise ValueError("unsupported JFR instant")
    match = re.fullmatch(
        r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})(?:\.(\d{1,9}))?(Z|[+-]\d{2}:\d{2})",
        value,
    )
    if match is None:
        raise ValueError("unsupported JFR instant")
    zone = "+00:00" if match.group(3) == "Z" else match.group(3)
    parsed = datetime.fromisoformat(match.group(1) + zone)
    if parsed.tzinfo is None:  # pragma: no cover - guarded by the grammar
        raise ValueError("JFR instant has no timezone")
    delta = parsed.astimezone(UTC) - datetime(1970, 1, 1, tzinfo=UTC)
    whole_seconds = (delta.days * 86_400) + delta.seconds
    fraction = int((match.group(2) or "").ljust(9, "0") or "0")
    return whole_seconds * 1_000_000_000 + fraction


def decimal_seconds_ns(value: str) -> int:
    """Convert decimal seconds to ns using an explicit floor at sub-ns precision."""

    try:
        seconds = Decimal(value)
    except InvalidOperation as error:
        raise ValueError("invalid decimal seconds") from error
    if not seconds.is_finite() or seconds < 0:
        raise ValueError("decimal seconds must be finite and non-negative")
    return int((seconds * Decimal(1_000_000_000)).to_integral_value(rounding=ROUND_FLOOR))


def jfr_intervals(value: object) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []

    def visit(item: object) -> None:
        if isinstance(item, list):
            for child in item:
                visit(child)
            return
        if not isinstance(item, dict):
            return
        event_type = item.get("type")
        values = item.get("values")
        if isinstance(event_type, str) and isinstance(values, dict):
            start_value = values.get("startTime")
            duration_value = values.get("duration")
            if start_value is not None and duration_value is not None:
                try:
                    start = instant_ns(start_value)
                    elapsed = duration_ns(duration_value)
                    result.append(
                        {
                            "end_wall_time_ns": start + elapsed,
                            "event_type": event_type,
                            "start_wall_time_ns": start,
                        }
                    )
                except (ValueError, OverflowError):
                    pass
        for child in item.values():
            visit(child)

    visit(value)
    return result


def jfr_overlap(jfr: dict[str, object], scheduled_wall_ns: int, actual_wall_ns: int) -> bool:
    value = availability_value(jfr)
    if not isinstance(value, dict):
        return False
    intervals = value.get("event_intervals")
    if not isinstance(intervals, list):
        return False
    relevant = {
        "jdk.Compilation",
        "jdk.CompilerPhase",
        "jdk.GarbageCollection",
        "jdk.GCPhasePause",
        "jdk.SafepointBegin",
        "jdk.SafepointEnd",
    }
    return any(
        isinstance(item, dict)
        and item.get("event_type") in relevant
        and type(item.get("start_wall_time_ns")) is int
        and type(item.get("end_wall_time_ns")) is int
        and int(item["start_wall_time_ns"]) <= actual_wall_ns
        and int(item["end_wall_time_ns"]) >= scheduled_wall_ns
        for item in intervals
    )


def read_json_lines(path: Path, code: str) -> list[dict[str, Any]]:
    contract.require(path.is_file(), f"{code}_MISSING", str(path))
    result: list[dict[str, Any]] = []
    with path.open("rb") as stream:
        for line_number, raw in enumerate(stream, start=1):
            raw = raw.rstrip(b"\n")
            contract.require(raw != b"", f"{code}_EMPTY_LINE", str(line_number))
            try:
                value = json.loads(raw, object_pairs_hook=contract.reject_duplicate_keys)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise contract.DiagnosticError(f"{code}_INVALID:{line_number}") from error
            contract.require(isinstance(value, dict), f"{code}_OBJECT", str(line_number))
            contract.require(contract.canonical_bytes(value) == raw, f"{code}_NOT_CANONICAL")
            result.append(value)
    return result


def read_lane_observations(path: Path) -> list[dict[str, Any]]:
    contract.require(path.is_file(), "LANE_EVENT_LOG_MISSING", str(path))
    return read_json_lines(path, "LANE_EVENT")


def validate_availability_integer(value: object, code: str) -> None:
    status = contract.availability(value)
    record = value
    contract.require(isinstance(record, dict), code)
    if status == "AVAILABLE":
        contract.exact_object(record, {"status", "value"}, f"{code}_FIELDS")
        contract.strict_int(record["value"], f"{code}_VALUE")
    else:
        contract.exact_object(record, {"reason", "status"}, f"{code}_FIELDS")


def validate_schedstat_delta(value: object) -> None:
    status = contract.availability(value)
    contract.require(isinstance(value, dict), "LANE_SCHEDSTAT")
    if status == "NOT_AVAILABLE":
        contract.exact_object(value, {"reason", "status"}, "LANE_SCHEDSTAT_FIELDS")
        return
    contract.exact_object(value, {"status", "value"}, "LANE_SCHEDSTAT_FIELDS")
    fields = contract.exact_object(
        value["value"], {"running_ns", "timeslices", "waiting_ns"}, "LANE_SCHEDSTAT_VALUE_FIELDS"
    )
    for name in fields:
        contract.strict_int(fields[name], f"LANE_SCHEDSTAT_{name.upper()}")


def validate_wal_observation(value: object, code: str) -> dict[str, Any]:
    record = contract.exact_object(
        value,
        {"modified_time_millis", "observed_at_ns", "present", "size_bytes"},
        f"{code}_FIELDS",
    )
    contract.require(type(record["present"]) is bool, f"{code}_PRESENT")
    contract.strict_int(record["modified_time_millis"], f"{code}_MODIFIED")
    contract.strict_int(record["observed_at_ns"], f"{code}_OBSERVED", minimum=1)
    contract.strict_int(record["size_bytes"], f"{code}_SIZE")
    if record["present"] is False:
        contract.require(record["size_bytes"] == 0, f"{code}_ABSENT_SIZE")
    else:
        contract.require(record["size_bytes"] > 0, f"{code}_PRESENT_SIZE")
    return record


def validate_lane_execution(
    events: list[dict[str, Any]],
    *,
    profile: str,
    duration: int,
    expected_processors: int,
    exit_code: int,
    timed_out: bool,
) -> None:
    """Reject every partial lane before it can become a zero-miss classification."""

    contract.require(not timed_out, "LANE_TIMED_OUT", profile)
    contract.require(exit_code == 0, "LANE_EXIT_NONZERO", f"{profile}:{exit_code}")
    operation_count = duration * contract.OFFER_RATE
    expected_event_count = 2 + (2 * operation_count)
    contract.require(len(events) == expected_event_count, "LANE_EVENT_COUNT", profile)
    start = events[0]
    end = events[-1]
    contract.exact_object(
        start,
        {
            "available_processors",
            "duration_seconds",
            "event_type",
            "initial_durable_sequence",
            "initial_state_root",
            "monotonic_anchor_ns",
            "offers_per_second",
            "process_id",
            "profile_id",
            "source_root",
            "wall_anchor_ns",
            "warmup_completed_operations",
        },
        "LANE_START_FIELDS",
    )
    contract.exact_object(
        end,
        {
            "completed_operations",
            "event_type",
            "final_durable_sequence",
            "final_state_root",
            "monotonic_ns",
            "profile_id",
            "terminal_state_validated",
            "wall_time_ns",
        },
        "LANE_END_FIELDS",
    )
    contract.require(start.get("event_type") == "LANE_START", "LANE_START_MISSING", profile)
    contract.require(end.get("event_type") == "LANE_END", "LANE_END_MISSING", profile)
    contract.require(start.get("profile_id") == profile, "LANE_START_PROFILE", profile)
    contract.require(end.get("profile_id") == profile, "LANE_END_PROFILE", profile)
    contract.require(start.get("offers_per_second") == contract.OFFER_RATE, "LANE_START_RATE")
    contract.require(start.get("duration_seconds") == duration, "LANE_START_DURATION")
    contract.require(
        start.get("warmup_completed_operations") == contract.WARMUP_OPERATIONS,
        "LANE_START_WARMUP",
    )
    contract.require(
        start.get("available_processors") == expected_processors,
        "LANE_START_PROCESSORS",
    )
    contract.strict_int(start.get("process_id"), "LANE_START_PROCESS_ID", minimum=1)
    monotonic_anchor = contract.strict_int(
        start.get("monotonic_anchor_ns"), "LANE_MONOTONIC_ANCHOR", minimum=1
    )
    wall_anchor = contract.strict_int(start.get("wall_anchor_ns"), "LANE_WALL_ANCHOR", minimum=1)
    monotonic_end = contract.strict_int(
        end.get("monotonic_ns"), "LANE_MONOTONIC_END", minimum=monotonic_anchor
    )
    wall_end = contract.strict_int(end.get("wall_time_ns"), "LANE_WALL_END", minimum=wall_anchor)
    contract.require(end.get("completed_operations") == operation_count, "LANE_END_COUNT")
    contract.require(end.get("terminal_state_validated") is True, "LANE_TERMINAL_STATE")
    initial_root = contract.content_id(start.get("initial_state_root"), "LANE_INITIAL_STATE_ROOT")
    initial_sequence = contract.strict_int(
        start.get("initial_durable_sequence"), "LANE_INITIAL_DURABLE_SEQUENCE"
    )
    final_root = contract.content_id(end.get("final_state_root"), "LANE_FINAL_STATE_ROOT")
    final_sequence = contract.strict_int(
        end.get("final_durable_sequence"), "LANE_FINAL_DURABLE_SEQUENCE", minimum=1
    )

    offers = events[1 : 1 + operation_count]
    completions = events[1 + operation_count : -1]
    contract.require(
        all(event.get("event_type") == "OFFER" for event in offers),
        "LANE_OFFER_SEQUENCE",
        profile,
    )
    contract.require(
        all(event.get("event_type") == "COMPLETION" for event in completions),
        "LANE_COMPLETION_SEQUENCE",
        profile,
    )
    interval = 1_000_000_000 // contract.OFFER_RATE
    first_scheduled: int | None = None
    previous_actual = monotonic_anchor
    previous_actual_wall = wall_anchor
    previous_completion = monotonic_anchor
    previous_completion_wall = wall_anchor
    previous_sequence = initial_sequence
    previous_root = initial_root
    for ordinal, (offer, completion) in enumerate(zip(offers, completions, strict=True)):
        contract.exact_object(
            offer,
            {
                "actual_offer_ns",
                "actual_wall_time_ns",
                "admission_accepted",
                "event_type",
                "harness_preparation_overran_slot",
                "missed_slot",
                "offer_ordinal",
                "preparation_latency_ns",
                "process_cpu_delta_ns",
                "profile_id",
                "request_id",
                "scheduled_offer_ns",
                "scheduler_lateness_ns",
                "scheduler_thread_cpu_delta_ns",
                "schedstat_delta",
                "wal_before",
                "wakeup_lateness_ns",
                "wakeup_ns",
            },
            "LANE_OFFER_FIELDS",
        )
        contract.exact_object(
            completion,
            {
                "completed_at_ns",
                "completed_wall_time_ns",
                "durable_sequence",
                "event_type",
                "native_phase_latency_ns",
                "next_state_root",
                "offer_ordinal",
                "operation_latency_ns",
                "prior_state_root",
                "profile_id",
                "request_id",
                "wal_after",
            },
            "LANE_COMPLETION_FIELDS",
        )
        offer_ordinal = contract.strict_int(offer.get("offer_ordinal"), "LANE_OFFER_ORDINAL")
        completion_ordinal = contract.strict_int(
            completion.get("offer_ordinal"), "LANE_COMPLETION_ORDINAL"
        )
        contract.require(offer_ordinal == ordinal, "LANE_OFFER_ORDINAL_SEQUENCE", profile)
        contract.require(
            completion_ordinal == ordinal,
            "LANE_COMPLETION_ORDINAL_SEQUENCE",
            profile,
        )
        contract.require(offer.get("profile_id") == profile, "LANE_OFFER_PROFILE", profile)
        contract.require(
            completion.get("profile_id") == profile,
            "LANE_COMPLETION_PROFILE",
            profile,
        )
        request_id = contract.strict_text(offer.get("request_id"), "LANE_OFFER_REQUEST_ID")
        contract.require(
            completion.get("request_id") == request_id,
            "LANE_REQUEST_JOIN",
            str(ordinal),
        )
        contract.require(offer.get("admission_accepted") is True, "LANE_OFFER_REJECTED")
        scheduled = contract.strict_int(
            offer.get("scheduled_offer_ns"), "LANE_SCHEDULED_OFFER", minimum=1
        )
        actual = contract.strict_int(offer.get("actual_offer_ns"), "LANE_ACTUAL_OFFER", minimum=1)
        wakeup = contract.strict_int(offer.get("wakeup_ns"), "LANE_WAKEUP", minimum=1)
        wakeup_lateness = contract.strict_int(
            offer.get("wakeup_lateness_ns"), "LANE_WAKEUP_LATENESS"
        )
        preparation = contract.strict_int(
            offer.get("preparation_latency_ns"), "LANE_PREPARATION_LATENCY"
        )
        lateness = contract.strict_int(offer.get("scheduler_lateness_ns"), "LANE_LATENESS")
        contract.require(actual >= wakeup >= scheduled, "LANE_CLOCK_REGRESSION", str(ordinal))
        contract.require(
            monotonic_anchor <= scheduled <= actual <= monotonic_end,
            "LANE_MONOTONIC_INTERVAL",
            str(ordinal),
        )
        contract.require(actual >= previous_actual, "LANE_OFFER_MONOTONIC_ORDER", str(ordinal))
        previous_actual = actual
        contract.require(wakeup_lateness == wakeup - scheduled, "LANE_WAKEUP_ARITHMETIC")
        contract.require(preparation == actual - wakeup, "LANE_PREPARATION_ARITHMETIC")
        contract.require(lateness == actual - scheduled, "LANE_LATENESS_ARITHMETIC", str(ordinal))
        if first_scheduled is None:
            first_scheduled = scheduled
        contract.require(
            scheduled == first_scheduled + (ordinal * interval),
            "LANE_ABSOLUTE_GRID",
            str(ordinal),
        )
        contract.require(
            offer.get("missed_slot") is (lateness >= interval),
            "LANE_MISSED_SLOT_FLAG",
            str(ordinal),
        )
        contract.require(
            offer.get("harness_preparation_overran_slot")
            is (lateness >= interval and wakeup_lateness < interval),
            "LANE_HARNESS_PREPARATION_PREDICATE",
            str(ordinal),
        )
        actual_wall = contract.strict_int(
            offer.get("actual_wall_time_ns"), "LANE_ACTUAL_WALL", minimum=wall_anchor
        )
        contract.require(actual_wall <= wall_end, "LANE_WALL_INTERVAL", str(ordinal))
        contract.require(actual_wall >= previous_actual_wall, "LANE_OFFER_WALL_ORDER", str(ordinal))
        previous_actual_wall = actual_wall
        validate_availability_integer(offer.get("process_cpu_delta_ns"), "LANE_PROCESS_CPU")
        validate_availability_integer(
            offer.get("scheduler_thread_cpu_delta_ns"), "LANE_SCHEDULER_THREAD_CPU"
        )
        validate_schedstat_delta(offer.get("schedstat_delta"))
        contract.require(
            availability_status(offer.get("process_cpu_delta_ns")),
            "LANE_PROCESS_CPU_REQUIRED",
            str(ordinal),
        )
        contract.require(
            availability_status(offer.get("scheduler_thread_cpu_delta_ns")),
            "LANE_SCHEDULER_THREAD_CPU_REQUIRED",
            str(ordinal),
        )
        contract.require(
            availability_status(offer.get("schedstat_delta")),
            "LANE_SCHEDSTAT_REQUIRED",
            str(ordinal),
        )
        wal_before = validate_wal_observation(offer.get("wal_before"), "LANE_WAL_BEFORE")
        contract.require(
            wakeup <= wal_before["observed_at_ns"] <= actual,
            "LANE_WAL_BEFORE_ORDER",
        )
        contract.require(wal_before["present"] is True, "LANE_WAL_BEFORE_REQUIRED")

        completed_at = contract.strict_int(
            completion.get("completed_at_ns"), "LANE_COMPLETED_AT", minimum=actual
        )
        contract.require(completed_at <= monotonic_end, "LANE_COMPLETION_MONOTONIC_INTERVAL")
        contract.require(
            completed_at >= previous_completion,
            "LANE_COMPLETION_MONOTONIC_ORDER",
        )
        previous_completion = completed_at
        completed_wall = contract.strict_int(
            completion.get("completed_wall_time_ns"),
            "LANE_COMPLETED_WALL",
            minimum=actual_wall,
        )
        contract.require(completed_wall <= wall_end, "LANE_COMPLETION_WALL_INTERVAL")
        contract.require(completed_wall >= previous_completion_wall, "LANE_COMPLETION_WALL_ORDER")
        previous_completion_wall = completed_wall
        operation_latency = contract.strict_int(
            completion.get("operation_latency_ns"), "LANE_OPERATION_LATENCY"
        )
        native_latency = contract.strict_int(
            completion.get("native_phase_latency_ns"), "LANE_NATIVE_PHASE_LATENCY"
        )
        contract.require(
            operation_latency == completed_at - actual,
            "LANE_OPERATION_LATENCY_ARITHMETIC",
        )
        contract.require(native_latency <= operation_latency, "LANE_NATIVE_LATENCY_BOUND")
        wal_after = validate_wal_observation(completion.get("wal_after"), "LANE_WAL_AFTER")
        contract.require(wal_after["observed_at_ns"] >= completed_at, "LANE_WAL_AFTER_ORDER")
        contract.require(wal_after["present"] is True, "LANE_WAL_AFTER_REQUIRED")
        prior_root = contract.content_id(
            completion.get("prior_state_root"), "LANE_COMPLETION_PRIOR_ROOT"
        )
        next_root = contract.content_id(
            completion.get("next_state_root"), "LANE_COMPLETION_NEXT_ROOT"
        )
        contract.require(prior_root == previous_root, "LANE_STATE_ROOT_CONTINUITY")
        previous_root = next_root
        durable_sequence = contract.strict_int(
            completion.get("durable_sequence"), "LANE_COMPLETION_DURABLE_SEQUENCE", minimum=1
        )
        contract.require(
            durable_sequence == previous_sequence + 1,
            "LANE_DURABLE_SEQUENCE_CONTINUITY",
        )
        previous_sequence = durable_sequence
    contract.require(previous_root == final_root, "LANE_TERMINAL_ROOT_MISMATCH")
    contract.require(previous_sequence == final_sequence, "LANE_TERMINAL_SEQUENCE_MISMATCH")


def availability_status(value: object) -> bool:
    return isinstance(value, dict) and value.get("status") == "AVAILABLE"


def availability_value(value: object) -> object | None:
    return value.get("value") if availability_status(value) else None  # type: ignore[union-attr]


def bracketing_samples(
    samples: list[dict[str, Any]], scheduled: int, actual: int
) -> tuple[dict[str, Any], dict[str, Any]] | None:
    # A sample spans several /proc and cgroup reads.  Use only samples wholly outside the
    # interval so a nominal timestamp cannot smuggle pre-actual or post-scheduled values into a
    # causal predicate.
    before = [
        item
        for item in samples
        if type(item.get("sample_end_monotonic_ns")) is int
        and int(item["sample_end_monotonic_ns"]) <= scheduled
    ]
    after = [
        item
        for item in samples
        if type(item.get("sample_begin_monotonic_ns")) is int
        and int(item["sample_begin_monotonic_ns"]) >= actual
    ]
    if not before or not after:
        return None
    return (
        max(before, key=lambda item: int(item["sample_end_monotonic_ns"])),
        min(after, key=lambda item: int(item["sample_begin_monotonic_ns"])),
    )


def integer_map(value: object) -> dict[str, int] | None:
    raw = availability_value(value)
    if not isinstance(raw, dict):
        return None
    if not all(isinstance(key, str) and type(item) is int for key, item in raw.items()):
        return None
    return {str(key): int(item) for key, item in raw.items()}


def pressure_total(value: object) -> int | None:
    raw = availability_value(value)
    if not isinstance(raw, str):
        return None
    totals = [int(item) for item in re.findall(r"\btotal=(\d+)\b", raw)]
    return sum(totals) if totals else None


def process_tree_cpu(
    before: dict[str, Any], after: dict[str, Any]
) -> tuple[int, bool, bool, list[dict[str, object]]] | None:
    left = availability_value(before.get("target_process_tree"))
    right = availability_value(after.get("target_process_tree"))
    if not isinstance(left, dict) or not isinstance(right, dict):
        return None
    ticks = left.get("clock_ticks_per_second")
    if type(ticks) is not int or ticks <= 0 or right.get("clock_ticks_per_second") != ticks:
        return None
    for field in ("root_pid", "target_executable", "tracer_wrapped"):
        if left.get(field) != right.get(field):
            return None

    def records(value: object) -> dict[int, dict[str, Any]]:
        if not isinstance(value, list):
            return {}
        return {
            int(item["pid"]): item
            for item in value
            if isinstance(item, dict)
            and type(item.get("pid")) is int
            and type(item.get("cpu_ticks")) is int
            and item.get("target_cpu") is True
        }

    left_records = records(left.get("processes"))
    right_records = records(right.get("processes"))
    common = set(left_records) & set(right_records)
    if not common:
        return None
    identity_fields = ("executable", "role", "start_time_ticks")
    if any(
        any(
            left_records[pid].get(field) != right_records[pid].get(field)
            for field in identity_fields
        )
        for pid in common
    ):
        return None
    target_executable = left.get("target_executable")
    if not any(
        left_records[pid].get("role") == "TARGET_JAVA"
        and left_records[pid].get("executable") == target_executable
        for pid in common
    ):
        return None
    deltas = [
        int(right_records[pid]["cpu_ticks"]) - int(left_records[pid]["cpu_ticks"]) for pid in common
    ]
    if any(delta < 0 for delta in deltas):
        return None
    tick_delta = sum(deltas)
    cpu_delta_ns = tick_delta * 1_000_000_000 // ticks
    runnable = any(str(right_records[pid].get("state")) == "R" for pid in common)
    waiting = False
    for pid in common:
        left_sched = availability_value(left_records[pid].get("schedstat"))
        right_sched = availability_value(right_records[pid].get("schedstat"))
        if isinstance(left_sched, str) and isinstance(right_sched, str):
            try:
                left_wait = int(left_sched.split()[1])
                right_wait = int(right_sched.split()[1])
                waiting = waiting or right_wait > left_wait
            except (IndexError, ValueError):
                continue
    identities = [
        {
            "executable": left_records[pid]["executable"],
            "pid": pid,
            "role": left_records[pid]["role"],
            "start_time_ticks": left_records[pid]["start_time_ticks"],
        }
        for pid in sorted(common)
    ]
    return cpu_delta_ns, runnable, waiting, identities


def causal_target_cpu_lower_bound(
    cpu_delta_ns: int,
    before: dict[str, Any],
    after: dict[str, Any],
    *,
    scheduled_ns: int,
    actual_ns: int,
    processor_count: int,
) -> tuple[int, int] | None:
    """Bound target CPU inside one missed interval, excluding the sampler overhang."""

    if cpu_delta_ns < 0 or processor_count <= 0 or scheduled_ns >= actual_ns:
        return None
    bounds = (
        before.get("sample_begin_monotonic_ns"),
        before.get("sample_end_monotonic_ns"),
        after.get("sample_begin_monotonic_ns"),
        after.get("sample_end_monotonic_ns"),
    )
    if not all(type(value) is int for value in bounds):
        return None
    before_begin, before_end, after_begin, after_end = (int(value) for value in bounds)
    if not (before_begin <= before_end <= scheduled_ns < actual_ns <= after_begin <= after_end):
        return None
    outside_interval_upper_bound_ns = (
        scheduled_ns - before_begin + after_end - actual_ns
    ) * processor_count
    causal_lower_bound_ns = max(0, cpu_delta_ns - outside_interval_upper_bound_ns)
    return causal_lower_bound_ns, outside_interval_upper_bound_ns


def strace_files(lane_directory: Path) -> list[Path]:
    return sorted(path for path in lane_directory.glob("fsync.strace*") if path.is_file())


def parse_strace_files(
    files: list[Path], *, artifact_root: Path | None = None
) -> dict[str, object]:
    if not files:
        return unavailable("strace produced no per-process trace files")
    syscall_pattern = re.compile(
        r"^(\d+\.\d+)\s+(?:f?datasync|fsync)\(.*\)\s+=\s+.*\s+<([0-9]+(?:\.[0-9]+)?)>$"
    )
    control_pattern = re.compile(r"^\d+\.\d+\s+(?:\+\+\+ .+ \+\+\+|--- .+ ---)$")
    parsed: list[dict[str, int]] = []
    for path in files:
        try:
            lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
        except (OSError, UnicodeError) as error:
            return unavailable(f"strace file read failed: {type(error).__name__}")
        if not lines:
            return unavailable("strace emitted an empty per-process trace")
        for line in lines:
            match = syscall_pattern.fullmatch(line)
            if match is not None:
                try:
                    ended_ns = decimal_seconds_ns(match.group(1))
                    duration = decimal_seconds_ns(match.group(2))
                except ValueError:
                    return unavailable("strace timestamp or duration is invalid")
                parsed.append(
                    {
                        "duration_ns": duration,
                        "ended_wall_time_ns": ended_ns,
                        "started_wall_time_ns": ended_ns - duration,
                    }
                )
                continue
            if control_pattern.fullmatch(line) is None:
                return unavailable("strace contains an incomplete or unparseable line")
    return available(
        {
            "artifacts": [artifact(path, artifact_root) for path in files],
            "fsync_events": parsed,
        }
    )


def fsync_overlap(
    trace: dict[str, object], scheduled_wall_ns: int, actual_wall_ns: int, lateness: int
) -> bool:
    value = availability_value(trace)
    if not isinstance(value, dict) or not isinstance(value.get("fsync_events"), list):
        return False
    return any(
        isinstance(event, dict)
        and type(event.get("duration_ns")) is int
        and type(event.get("started_wall_time_ns")) is int
        and type(event.get("ended_wall_time_ns")) is int
        and int(event["started_wall_time_ns"]) <= actual_wall_ns
        and int(event["ended_wall_time_ns"]) >= scheduled_wall_ns
        for event in value["fsync_events"]
    )


def build_missed_slots(
    events: list[dict[str, Any]],
    host_samples: list[dict[str, Any]],
    *,
    environment: dict[str, object],
    host_telemetry: dict[str, Any],
    jfr: dict[str, object],
    trace_files: list[Path],
    strace: dict[str, object] | None = None,
) -> list[dict[str, Any]]:
    completions = {
        int(item["offer_ordinal"]): item
        for item in events
        if item.get("event_type") == "COMPLETION" and type(item.get("offer_ordinal")) is int
    }
    result: list[dict[str, Any]] = []
    effective_processors = availability_value(environment.get("cpu_affinity"))
    processor_count = len(effective_processors) if isinstance(effective_processors, list) else 0
    allocation_preflight = environment.get("allocation_preflight")
    psi_preflight_available = (
        isinstance(allocation_preflight, dict)
        and isinstance(allocation_preflight.get("psi"), dict)
        and allocation_preflight["psi"].get("status") == "AVAILABLE"
    )
    environment_identity_available = (
        availability_status(environment.get("container_identity"))
        and availability_status(environment.get("cpu_affinity"))
        and all(
            availability_status(environment.get("cgroup_values", {}).get(name))
            for name in ("cpu.max", "cpuset.cpus.effective", "memory.current", "memory.max")
        )
    )
    for offer in events:
        if offer.get("event_type") != "OFFER" or offer.get("missed_slot") is not True:
            continue
        scheduled = contract.strict_int(
            offer.get("scheduled_offer_ns"), "OFFER_SCHEDULED", minimum=1
        )
        actual = contract.strict_int(offer.get("actual_offer_ns"), "OFFER_ACTUAL", minimum=1)
        lateness = contract.strict_int(
            offer.get("scheduler_lateness_ns"), "OFFER_LATENESS", minimum=1
        )
        ordinal = contract.strict_int(offer.get("offer_ordinal"), "OFFER_ORDINAL")
        pair = bracketing_samples(host_samples, scheduled, actual)
        cgroup_available = False
        cpu_psi_available = False
        io_psi_available = False
        run_queue_available = False
        process_tree_available = False
        cgroup_throttled = False
        pressure_stall = False
        run_queue_stall = False
        sustained_cpu = False
        not_continuous = False
        association: dict[str, object] = {
            "causal_target_cpu_lower_bound_ns": None,
            "host_sample_after_begin_monotonic_ns": None,
            "host_sample_before_end_monotonic_ns": None,
            "outside_interval_cpu_upper_bound_ns": None,
            "target_cpu_delta_ns": None,
            "target_process_identities": None,
        }
        if pair is not None:
            before, after = pair
            association = {
                "causal_target_cpu_lower_bound_ns": None,
                "host_sample_after_begin_monotonic_ns": after["sample_begin_monotonic_ns"],
                "host_sample_before_end_monotonic_ns": before["sample_end_monotonic_ns"],
                "outside_interval_cpu_upper_bound_ns": None,
                "target_cpu_delta_ns": None,
                "target_process_identities": None,
            }
            left_cpu = integer_map(before.get("cgroup_cpu_stat"))
            right_cpu = integer_map(after.get("cgroup_cpu_stat"))
            if left_cpu is not None and right_cpu is not None:
                required_keys = {"nr_periods", "nr_throttled"}
                throttle_key = (
                    "throttled_usec" if "throttled_usec" in right_cpu else "throttled_time"
                )
                cgroup_available = required_keys <= set(left_cpu) and required_keys <= set(
                    right_cpu
                )
                cgroup_available = (
                    cgroup_available and throttle_key in left_cpu and throttle_key in right_cpu
                )
                if cgroup_available:
                    cgroup_throttled = (
                        right_cpu["nr_throttled"] > left_cpu["nr_throttled"]
                        or right_cpu[throttle_key] > left_cpu[throttle_key]
                    )
            left_cpu_pressure = pressure_total(before.get("cpu_pressure"))
            right_cpu_pressure = pressure_total(after.get("cpu_pressure"))
            cpu_psi_available = (
                psi_preflight_available
                and left_cpu_pressure is not None
                and right_cpu_pressure is not None
            )
            left_io_pressure = pressure_total(before.get("io_pressure"))
            right_io_pressure = pressure_total(after.get("io_pressure"))
            io_psi_available = (
                psi_preflight_available
                and left_io_pressure is not None
                and right_io_pressure is not None
            )
            pressure_stall = (
                cpu_psi_available and right_cpu_pressure > left_cpu_pressure  # type: ignore[operator]
            ) or (
                io_psi_available and right_io_pressure > left_io_pressure  # type: ignore[operator]
            )
            left_proc = integer_map(before.get("proc_stat"))
            right_proc = integer_map(after.get("proc_stat"))
            run_queue_available = (
                left_proc is not None
                and right_proc is not None
                and processor_count > 0
                and "procs_running" in left_proc
                and "procs_running" in right_proc
            )
            if run_queue_available:
                run_queue_stall = (
                    max(left_proc["procs_running"], right_proc["procs_running"]) > processor_count
                )  # type: ignore[index]
            process = process_tree_cpu(before, after)
            if process is not None:
                cpu_delta, runnable, waiting, target_identities = process
                causal_cpu = causal_target_cpu_lower_bound(
                    cpu_delta,
                    before,
                    after,
                    scheduled_ns=scheduled,
                    actual_ns=actual,
                    processor_count=processor_count,
                )
                if causal_cpu is not None:
                    process_tree_available = True
                    causal_lower_bound, outside_upper_bound = causal_cpu
                    association.update(
                        {
                            "causal_target_cpu_lower_bound_ns": causal_lower_bound,
                            "outside_interval_cpu_upper_bound_ns": outside_upper_bound,
                            "target_cpu_delta_ns": cpu_delta,
                            "target_process_identities": target_identities,
                        }
                    )
                    sustained_cpu = causal_lower_bound * 100 >= lateness * 80
                    not_continuous = runnable and waiting

        completion = completions.get(ordinal)
        trace_evidence = strace if strace is not None else parse_strace_files(trace_files)
        wal_available = availability_status(trace_evidence) and completion is not None
        actual_wall = contract.strict_int(offer.get("actual_wall_time_ns"), "OFFER_WALL", minimum=1)
        scheduled_wall = actual_wall - lateness
        wal_stall = fsync_overlap(trace_evidence, scheduled_wall, actual_wall, lateness)
        java_overlap = jfr_overlap(jfr, scheduled_wall, actual_wall)
        host_fault = host_fault_overlap(host_telemetry, scheduled_wall, actual_wall)
        cpu_fields_available = (
            availability_status(offer.get("process_cpu_delta_ns"))
            and availability_status(offer.get("scheduler_thread_cpu_delta_ns"))
            and process_tree_available
        )
        schedstat_available = availability_status(offer.get("schedstat_delta"))
        offer_schedstat = availability_value(offer.get("schedstat_delta"))
        if isinstance(offer_schedstat, dict) and type(offer_schedstat.get("waiting_ns")) is int:
            run_queue_stall = run_queue_stall or int(offer_schedstat["waiting_ns"]) > 0
        mandatory = {
            "CGROUP_CPU_STAT": (
                available(association)
                if cgroup_available
                else unavailable("cgroup cpu.stat bracket missing")
            ),
            "CPUSET_QUOTA_PROCESSORS_MEMORY_CONTAINER_RUNTIME": (
                available(environment)
                if environment_identity_available
                else unavailable("exact allocation identity incomplete")
            ),
            "CPU_PSI": (
                available(association)
                if cpu_psi_available
                else unavailable("CPU PSI bracket missing")
            ),
            "IO_PSI": (
                available(association)
                if io_psi_available
                else unavailable("IO PSI bracket missing")
            ),
            "JAVA_JFR_GC_SAFEPOINT_COMPILER": jfr,
            "PROCESS_AND_THREAD_CPU_TIME_DELTAS": (
                available(
                    {
                        "process_cpu_delta_ns": offer["process_cpu_delta_ns"],
                        "scheduler_thread_cpu_delta_ns": offer["scheduler_thread_cpu_delta_ns"],
                        "target_process_tree": association,
                    }
                )
                if cpu_fields_available
                else unavailable("process/thread/process-tree CPU bracket missing")
            ),
            "SCHEDULED_ACTUAL_AND_LATENESS_NS": available(
                {
                    "actual_offer_ns": actual,
                    "harness_preparation_overran_slot": offer["harness_preparation_overran_slot"],
                    "preparation_latency_ns": offer["preparation_latency_ns"],
                    "scheduled_offer_ns": scheduled,
                    "scheduler_lateness_ns": lateness,
                    "wakeup_lateness_ns": offer["wakeup_lateness_ns"],
                    "wakeup_ns": offer["wakeup_ns"],
                }
            ),
            "SCHEDSTAT_OR_RUN_QUEUE": (
                available(
                    {
                        "host_sample_association": association,
                        "offer_schedstat_delta": offer["schedstat_delta"],
                    }
                )
                if schedstat_available or run_queue_available
                else unavailable("schedstat and run-queue bracket missing")
            ),
            "WAL_AND_FSYNC_LATENCY": (
                available(
                    {
                        "completed_at_ns": completion["completed_at_ns"],
                        "native_phase_latency_ns": completion["native_phase_latency_ns"],
                        "operation_latency_ns": completion["operation_latency_ns"],
                        "strace": availability_value(trace_evidence),
                        "wal_after": completion["wal_after"],
                        "wal_before": offer["wal_before"],
                    }
                )
                if wal_available
                else unavailable("WAL completion or fsync syscall trace missing")
            ),
        }
        result.append(
            {
                "actual_offer_ns": actual,
                "event_type": "MISSED_SLOT",
                "mandatory_telemetry": mandatory,
                "offer_ordinal": ordinal,
                "predicates": {
                    "cgroup_throttling_overlap": cgroup_throttled,
                    "cpu_or_io_psi_overlap": pressure_stall,
                    "harness_or_timer_defect_observed": offer["harness_preparation_overran_slot"],
                    "host_hardware_fault_overlap": host_fault,
                    "java_pause_or_compiler_overlap": java_overlap,
                    "process_runnable_not_continuously_consuming_cpu": not_continuous,
                    "run_queue_starvation_overlap": run_queue_stall,
                    "sustained_target_runtime_cpu_demand": sustained_cpu,
                    "wal_or_fsync_stall_overlap": wal_stall,
                },
                "scheduled_offer_ns": scheduled,
                "scheduler_lateness_ns": lateness,
            }
        )
    return result


def artifact(path: Path, root: Path | None = None) -> dict[str, object]:
    resolved = path.resolve(strict=True)
    if root is None:
        recorded_path = str(resolved)
    else:
        try:
            recorded_path = resolved.relative_to(root.resolve(strict=True)).as_posix()
        except ValueError as error:
            raise contract.DiagnosticError(f"ARTIFACT_OUTSIDE_EVIDENCE_ROOT:{path}") from error
    return {
        "path": recorded_path,
        "sha256": contract.sha256_id(resolved.read_bytes()),
        "size_bytes": resolved.stat().st_size,
    }


def verified_artifact_path(root: Path, record: object, code: str) -> Path:
    value = contract.exact_object(record, contract.FILE_FIELDS, f"{code}_FIELDS")
    relative = contract.strict_text(value["path"], f"{code}_PATH")
    contract.require(not contract.absolute_contract_path(relative), f"{code}_PATH_NOT_PORTABLE")
    expected_sha256 = contract.content_id(value["sha256"], f"{code}_SHA256")
    expected_size = contract.strict_int(value["size_bytes"], f"{code}_SIZE")
    candidate = (root / relative).resolve(strict=True)
    try:
        candidate.relative_to(root.resolve(strict=True))
    except ValueError as error:
        raise contract.DiagnosticError(f"{code}_PATH_ESCAPE") from error
    contract.require(candidate.is_file(), f"{code}_MISSING")
    contract.require(candidate.stat().st_size == expected_size, f"{code}_SIZE")
    contract.require(
        contract.sha256_id(candidate.read_bytes()) == expected_sha256, f"{code}_SHA256"
    )
    return candidate


def execute_lane(
    prepared: PreparedLane,
    *,
    source_root: Path,
    duration: int,
    sampling_interval_ms: int,
    environment_snapshot_value: dict[str, object],
    expected_processors: int,
    evidence_root: Path,
    host_telemetry: dict[str, Any],
) -> dict[str, Any]:
    lane = prepared.lane
    profile = prepared.profile
    lane_directory = prepared.lane_directory
    lane_directory.mkdir(parents=False, exist_ok=False)
    argv = list(prepared.argv)
    environment = dict(prepared.environment)
    trace_prefix = list(prepared.trace_prefix)
    trace_tool = Path(trace_prefix[0])
    trace_available = trace_tool.is_file() or shutil.which(trace_prefix[0]) is not None
    trace_path = lane_directory / "fsync.strace"
    executed_argv = argv
    if trace_available:
        executed_argv = [*trace_prefix, "-o", str(trace_path), *argv]
    sampler = HostSampler(lane_directory / "host-telemetry.jsonl", sampling_interval_ms)
    started_at = utc_now()
    started_ns = time.monotonic_ns()
    sampler.start()
    try:
        exit_code, timed_out = run_process(
            executed_argv,
            cwd=prepared.working_directory,
            environment=environment,
            stdout=lane_directory / "stdout.txt",
            stderr=lane_directory / "stderr.txt",
            timeout_seconds=duration + 180,
            sampler=sampler,
            target_executable=Path(argv[0]),
            tracer_wrapped=trace_available,
        )
    finally:
        sampler.stop()
    ended_ns = time.monotonic_ns()
    ended_at = utc_now()
    events = read_lane_observations(lane_directory / "operations.jsonl")
    validate_lane_execution(
        events,
        profile=profile,
        duration=duration,
        expected_processors=expected_processors,
        exit_code=exit_code,
        timed_out=timed_out,
    )
    host_samples = read_json_lines(lane_directory / "host-telemetry.jsonl", "HOST_TELEMETRY")
    validate_lane_process_identity(
        events,
        host_samples,
        target_executable=str(Path(argv[0]).resolve(strict=True)),
    )
    jfr = jfr_evidence(
        prepared.jfr_tool,
        Path(prepared.argv[0]),
        lane,
        lane_directory,
        evidence_root,
        environment=environment,
        working_directory=prepared.working_directory,
    )
    traces = strace_files(lane_directory)
    syscall = (
        parse_strace_files(traces, artifact_root=evidence_root)
        if trace_available
        else unavailable("strace is unavailable in the pinned allocation")
    )
    contract.require(availability_status(jfr), "LANE_JFR_REQUIRED", profile)
    contract.require(availability_status(syscall), "LANE_STRACE_REQUIRED", profile)
    syscall_value = availability_value(syscall)
    contract.require(
        isinstance(syscall_value, dict)
        and isinstance(syscall_value.get("fsync_events"), list)
        and len(syscall_value["fsync_events"]) > 0,
        "LANE_STRACE_FSYNC_REQUIRED",
        profile,
    )
    missed = build_missed_slots(
        events,
        host_samples,
        environment=environment_snapshot_value,
        host_telemetry=host_telemetry,
        jfr=jfr,
        trace_files=traces,
        strace=syscall,
    )
    return {
        "artifacts": {
            "event_log": artifact(lane_directory / "operations.jsonl", evidence_root),
            "host_telemetry": artifact(lane_directory / "host-telemetry.jsonl", evidence_root),
            "stderr": artifact(lane_directory / "stderr.txt", evidence_root),
            "stdout": artifact(lane_directory / "stdout.txt", evidence_root),
        },
        "ended_at_utc": ended_at,
        "event_count": len(events),
        "executed_argv": executed_argv,
        "executed_environment": environment,
        "environment_mode": "REPLACE",
        "exit_code": exit_code,
        "java_involved": lane["java_involved"],
        "jfr": jfr,
        "missed_slots": missed,
        "monotonic_duration_ns": ended_ns - started_ns,
        "profile_id": profile,
        "started_at_utc": started_at,
        "strace_fsync": syscall,
        "timed_out": timed_out,
        "working_directory": str(prepared.working_directory),
    }


def pending_host_telemetry() -> dict[str, Any]:
    return {
        "docker_wsl_events": unavailable("host collection awaits lanes-complete handshake"),
        "windows_hardware_events": unavailable("host collection awaits lanes-complete handshake"),
    }


def recompute_lane_missed_slots(
    lane: dict[str, Any],
    *,
    evidence_root: Path,
    environment: dict[str, object],
    host_telemetry: dict[str, Any],
    target_executable: str,
) -> None:
    artifacts = lane["artifacts"]
    events = read_lane_observations(
        verified_artifact_path(evidence_root, artifacts["event_log"], "VERIFY_EVENT_LOG")
    )
    host_samples = read_json_lines(
        verified_artifact_path(evidence_root, artifacts["host_telemetry"], "VERIFY_HOST_TELEMETRY"),
        "VERIFY_HOST_TELEMETRY",
    )
    validate_lane_process_identity(
        events,
        host_samples,
        target_executable=target_executable,
    )
    lane["missed_slots"] = build_missed_slots(
        events,
        host_samples,
        environment=environment,
        host_telemetry=host_telemetry,
        jfr=lane["jfr"],
        trace_files=[],
        strace=lane["strace_fsync"],
    )


def durable_copy_bytes(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    if os.name == "posix":
        descriptor = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)


def ledger_paths(directory: Path, campaign_id: str) -> dict[str, Path]:
    return {
        "attempt": directory / f"{campaign_id}.attempt.json",
        "started": directory / f"{campaign_id}.started.json",
        "terminal": directory / f"{campaign_id}.terminal.json",
        "completed": directory / f"{campaign_id}.completed.json",
        "failed": directory / f"{campaign_id}.failed.json",
    }


def validate_execution_started_seal(
    value: object,
    *,
    manifest: dict[str, Any],
    manifest_canonical: bytes,
    attempt_raw: bytes,
) -> dict[str, Any]:
    started = contract.exact_object(
        value, EXECUTION_STARTED_SEAL_FIELDS, "EXECUTION_STARTED_SEAL_FIELDS"
    )
    contract.require(
        started["schema_version"] == contract.SCHEMA_VERSION, "EXECUTION_STARTED_SCHEMA"
    )
    contract.require(started["type_name"] == EXECUTION_STARTED_SEAL_TYPE, "EXECUTION_STARTED_TYPE")
    contract.require(started["state"] == EXECUTION_STARTED_SEAL_STATE, "EXECUTION_STARTED_STATE")
    contract.require(
        started["diagnostic_campaign_id"] == manifest["diagnostic_campaign_id"],
        "EXECUTION_STARTED_CAMPAIGN",
    )
    contract.require(
        started["manifest_sha256"] == contract.sha256_id(manifest_canonical),
        "EXECUTION_STARTED_MANIFEST",
    )
    contract.require(
        started["attempt_record_sha256"] == contract.sha256_id(attempt_raw),
        "EXECUTION_STARTED_ATTEMPT",
    )
    instant_ns(contract.strict_text(started["started_at_utc"], "EXECUTION_STARTED_TIME"))
    return started


def claim_execution(
    seals: dict[str, Path],
    *,
    manifest: dict[str, Any],
    manifest_canonical: bytes,
    attempt_raw: bytes,
) -> dict[str, Any]:
    """Irreversibly claim the sole campaign execution before any capture side effect."""

    contract.require(
        not any(seals[name].exists() for name in ("terminal", "completed", "failed")),
        "CAMPAIGN_ALREADY_TERMINAL",
    )
    started = {
        "attempt_record_sha256": contract.sha256_id(attempt_raw),
        "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
        "manifest_sha256": contract.sha256_id(manifest_canonical),
        "schema_version": contract.SCHEMA_VERSION,
        "started_at_utc": utc_now(),
        "state": EXECUTION_STARTED_SEAL_STATE,
        "type_name": EXECUTION_STARTED_SEAL_TYPE,
    }
    validate_execution_started_seal(
        started,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_raw,
    )
    try:
        durable_exclusive_write(seals["started"], started)
    except FileExistsError as error:
        raise contract.DiagnosticError("CAMPAIGN_EXECUTION_ALREADY_STARTED") from error
    return started


def validate_completion_seal(
    value: object,
    *,
    manifest: dict[str, Any],
    manifest_canonical: bytes,
    attempt_raw: bytes,
    started_raw: bytes,
) -> dict[str, Any]:
    completion = contract.exact_object(value, COMPLETION_SEAL_FIELDS, "COMPLETION_SEAL_FIELDS")
    contract.require(completion["schema_version"] == contract.SCHEMA_VERSION, "COMPLETION_SCHEMA")
    contract.require(completion["type_name"] == COMPLETION_SEAL_TYPE, "COMPLETION_TYPE")
    contract.require(completion["state"] == "COMPLETED_ONE_SHOT_NO_RERUN", "COMPLETION_STATE")
    contract.require(
        completion["diagnostic_campaign_id"] == manifest["diagnostic_campaign_id"],
        "COMPLETION_CAMPAIGN",
    )
    manifest_sha256 = contract.content_id(completion["manifest_sha256"], "COMPLETION_MANIFEST_ID")
    attempt_sha256 = contract.content_id(
        completion["attempt_record_sha256"], "COMPLETION_ATTEMPT_ID"
    )
    started_sha256 = contract.content_id(
        completion["execution_started_record_sha256"], "COMPLETION_EXECUTION_STARTED_ID"
    )
    contract.content_id(completion["evidence_sha256"], "COMPLETION_EVIDENCE_ID")
    contract.require(
        manifest_sha256 == contract.sha256_id(manifest_canonical), "COMPLETION_MANIFEST"
    )
    contract.require(attempt_sha256 == contract.sha256_id(attempt_raw), "COMPLETION_ATTEMPT")
    contract.require(
        started_sha256 == contract.sha256_id(started_raw), "COMPLETION_EXECUTION_STARTED"
    )
    instant_ns(contract.strict_text(completion["completed_at_utc"], "COMPLETION_TIME"))
    return completion


def validate_terminal_seal(
    value: object,
    *,
    manifest: dict[str, Any],
    manifest_canonical: bytes,
    attempt_raw: bytes,
    started_raw: bytes,
) -> dict[str, Any]:
    terminal = contract.exact_object(value, TERMINAL_SEAL_FIELDS, "TERMINAL_SEAL_FIELDS")
    contract.require(terminal["schema_version"] == contract.SCHEMA_VERSION, "TERMINAL_SCHEMA")
    contract.require(terminal["type_name"] == TERMINAL_SEAL_TYPE, "TERMINAL_TYPE")
    contract.require(terminal["state"] == "TERMINAL_ONE_SHOT_NO_RERUN", "TERMINAL_STATE")
    contract.require(terminal["outcome"] in {"COMPLETED", "FAILED"}, "TERMINAL_OUTCOME")
    contract.require(
        terminal["diagnostic_campaign_id"] == manifest["diagnostic_campaign_id"],
        "TERMINAL_CAMPAIGN",
    )
    contract.content_id(terminal["manifest_sha256"], "TERMINAL_MANIFEST_ID")
    contract.content_id(terminal["attempt_record_sha256"], "TERMINAL_ATTEMPT_ID")
    contract.content_id(
        terminal["execution_started_record_sha256"], "TERMINAL_EXECUTION_STARTED_ID"
    )
    contract.require(
        terminal["manifest_sha256"] == contract.sha256_id(manifest_canonical),
        "TERMINAL_MANIFEST",
    )
    contract.require(
        terminal["attempt_record_sha256"] == contract.sha256_id(attempt_raw),
        "TERMINAL_ATTEMPT",
    )
    contract.require(
        terminal["execution_started_record_sha256"] == contract.sha256_id(started_raw),
        "TERMINAL_EXECUTION_STARTED",
    )
    outcome_record = terminal["outcome_record"]
    contract.require(isinstance(outcome_record, dict), "TERMINAL_OUTCOME_RECORD")
    contract.content_id(terminal["outcome_record_sha256"], "TERMINAL_OUTCOME_RECORD_SHA256")
    contract.require(
        terminal["outcome_record_sha256"]
        == contract.sha256_id(contract.canonical_bytes(outcome_record) + b"\n"),
        "TERMINAL_OUTCOME_RECORD_HASH",
    )
    if terminal["outcome"] == "COMPLETED":
        validate_completion_seal(
            outcome_record,
            manifest=manifest,
            manifest_canonical=manifest_canonical,
            attempt_raw=attempt_raw,
            started_raw=started_raw,
        )
    else:
        validate_failure_seal(
            outcome_record,
            manifest=manifest,
            manifest_canonical=manifest_canonical,
            attempt_raw=attempt_raw,
            started_raw=started_raw,
        )
    instant_ns(contract.strict_text(terminal["sealed_at_utc"], "TERMINAL_TIME"))
    return terminal


def recover_terminal_outcome(
    seals: dict[str, Path],
    *,
    manifest: dict[str, Any],
    manifest_canonical: bytes,
    attempt_raw: bytes,
    started_raw: bytes,
) -> dict[str, Any]:
    """Idempotently materialize the outcome embedded in the terminal arbitration record."""

    terminal_value, _ = contract.canonical_document(seals["terminal"])
    terminal = validate_terminal_seal(
        terminal_value,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_raw,
        started_raw=started_raw,
    )
    outcome = str(terminal["outcome"]).lower()
    other = "failed" if outcome == "completed" else "completed"
    contract.require(not seals[other].exists(), "CONFLICTING_TERMINAL_SEAL")
    outcome_record = terminal["outcome_record"]
    target = seals[outcome]
    if target.exists():
        existing, _ = contract.canonical_document(target)
        contract.require(existing == outcome_record, "TERMINAL_OUTCOME_RECORD_MISMATCH")
        return terminal
    try:
        durable_exclusive_write(target, outcome_record)
    except FileExistsError:
        existing, _ = contract.canonical_document(target)
        contract.require(existing == outcome_record, "TERMINAL_OUTCOME_RECORD_MISMATCH")
    return terminal


def durable_terminal_transition(
    seals: dict[str, Path],
    outcome: str,
    record: dict[str, Any],
    *,
    manifest: dict[str, Any],
    manifest_canonical: bytes,
    attempt_raw: bytes,
    started_raw: bytes,
) -> dict[str, Any]:
    """Seal one outcome and recover its derived record after any publication cut."""

    contract.require(outcome in {"completed", "failed"}, "TERMINAL_OUTCOME")
    contract.require(isinstance(record, dict), "TERMINAL_OUTCOME_RECORD")
    contract.require(
        seals["terminal"].exists()
        or (not seals["completed"].exists() and not seals["failed"].exists()),
        "CAMPAIGN_OUTCOME_WITHOUT_TERMINAL",
    )
    outcome_record = copy.deepcopy(record)
    terminal = {
        "attempt_record_sha256": contract.sha256_id(attempt_raw),
        "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
        "execution_started_record_sha256": contract.sha256_id(started_raw),
        "manifest_sha256": contract.sha256_id(manifest_canonical),
        "outcome": outcome.upper(),
        "outcome_record": outcome_record,
        "outcome_record_sha256": contract.sha256_id(
            contract.canonical_bytes(outcome_record) + b"\n"
        ),
        "schema_version": contract.SCHEMA_VERSION,
        "sealed_at_utc": utc_now(),
        "state": "TERMINAL_ONE_SHOT_NO_RERUN",
        "type_name": TERMINAL_SEAL_TYPE,
    }
    validate_terminal_seal(
        terminal,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_raw,
        started_raw=started_raw,
    )
    try:
        durable_exclusive_write(seals["terminal"], terminal)
    except FileExistsError:
        existing_value, _ = contract.canonical_document(seals["terminal"])
        existing = validate_terminal_seal(
            existing_value,
            manifest=manifest,
            manifest_canonical=manifest_canonical,
            attempt_raw=attempt_raw,
            started_raw=started_raw,
        )
        contract.require(existing["outcome"] == outcome.upper(), "CONFLICTING_TERMINAL_SEAL")
        contract.require(existing["outcome_record"] == outcome_record, "DUPLICATE_TERMINAL_SEAL")
    return recover_terminal_outcome(
        seals,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_raw,
        started_raw=started_raw,
    )


def lane_capture_binding(lanes: list[dict[str, Any]]) -> list[dict[str, object]]:
    return [
        {
            "artifacts": lane["artifacts"],
            "environment_mode": lane["environment_mode"],
            "executed_argv": lane["executed_argv"],
            "executed_environment": lane["executed_environment"],
            "jfr": lane["jfr"],
            "profile_id": lane["profile_id"],
            "strace_fsync": lane["strace_fsync"],
            "working_directory": lane["working_directory"],
        }
        for lane in lanes
    ]


def portable_input_record(path: Path, evidence_root: Path) -> dict[str, object]:
    return artifact(path, evidence_root)


def validate_host_sample(sample: object, index: int) -> dict[str, Any]:
    value = contract.exact_object(
        sample,
        {
            "cgroup_cpu_stat",
            "cgroup_mode",
            "cpu_pressure",
            "io_pressure",
            "load_average",
            "proc_stat",
            "sample_begin_monotonic_ns",
            "sample_begin_wall_time_ns",
            "sample_end_monotonic_ns",
            "sample_end_wall_time_ns",
            "target_process_tree",
        },
        "VERIFY_HOST_SAMPLE_FIELDS",
    )
    begin = contract.strict_int(
        value["sample_begin_monotonic_ns"], "VERIFY_HOST_SAMPLE_BEGIN", minimum=1
    )
    end = contract.strict_int(
        value["sample_end_monotonic_ns"], "VERIFY_HOST_SAMPLE_END", minimum=begin
    )
    wall_begin = contract.strict_int(
        value["sample_begin_wall_time_ns"], "VERIFY_HOST_SAMPLE_WALL_BEGIN", minimum=1
    )
    contract.strict_int(
        value["sample_end_wall_time_ns"],
        "VERIFY_HOST_SAMPLE_WALL_END",
        minimum=wall_begin,
    )
    contract.require(value["cgroup_mode"] in {"V1", "V2", "NOT_AVAILABLE"}, "VERIFY_CGROUP_MODE")
    for name in (
        "cgroup_cpu_stat",
        "cpu_pressure",
        "io_pressure",
        "load_average",
        "proc_stat",
        "target_process_tree",
    ):
        status = contract.availability(value[name])
        if status == "AVAILABLE":
            contract.exact_object(
                value[name], {"status", "value"}, "VERIFY_HOST_SAMPLE_AVAILABLE_FIELDS"
            )
        else:
            contract.exact_object(
                value[name], {"reason", "status"}, "VERIFY_HOST_SAMPLE_UNAVAILABLE_FIELDS"
            )
    process_tree = availability_value(value["target_process_tree"])
    if process_tree is not None:
        tree = contract.exact_object(
            process_tree,
            {
                "clock_ticks_per_second",
                "processes",
                "root_pid",
                "target_executable",
                "tracer_wrapped",
            },
            "VERIFY_PROCESS_TREE_FIELDS",
        )
        contract.strict_int(
            tree["clock_ticks_per_second"], "VERIFY_PROCESS_TREE_CLOCK_TICKS", minimum=1
        )
        root_pid = contract.strict_int(tree["root_pid"], "VERIFY_PROCESS_TREE_ROOT", minimum=1)
        target_executable = contract.strict_text(
            tree["target_executable"], "VERIFY_PROCESS_TREE_TARGET_EXECUTABLE"
        )
        contract.require(
            contract.absolute_contract_path(target_executable),
            "VERIFY_PROCESS_TREE_TARGET_EXECUTABLE_ABSOLUTE",
        )
        contract.require(type(tree["tracer_wrapped"]) is bool, "VERIFY_PROCESS_TREE_TRACER_WRAPPED")
        contract.require(isinstance(tree["processes"], list), "VERIFY_PROCESS_TREE_RECORDS")
        seen_pids: set[int] = set()
        validated_records: dict[int, dict[str, object]] = {}
        roles = {
            "EXCLUDED_NON_TARGET_DESCENDANT",
            "TARGET_JAVA",
            "TARGET_RUNTIME_DESCENDANT",
            "TRACER",
        }
        for process in tree["processes"]:
            record = contract.exact_object(
                process,
                {
                    "cpu_ticks",
                    "executable",
                    "parent_pid",
                    "pid",
                    "role",
                    "schedstat",
                    "start_time_ticks",
                    "state",
                    "target_cpu",
                },
                "VERIFY_PROCESS_TREE_RECORD_FIELDS",
            )
            pid = contract.strict_int(record["pid"], "VERIFY_PROCESS_TREE_PID", minimum=1)
            contract.require(pid not in seen_pids, "VERIFY_PROCESS_TREE_DUPLICATE_PID")
            seen_pids.add(pid)
            contract.strict_int(record["parent_pid"], "VERIFY_PROCESS_TREE_PARENT_PID", minimum=0)
            contract.strict_int(
                record["start_time_ticks"], "VERIFY_PROCESS_TREE_START_TIME", minimum=1
            )
            contract.strict_int(record["cpu_ticks"], "VERIFY_PROCESS_TREE_CPU_TICKS")
            executable = contract.strict_text(
                record["executable"], "VERIFY_PROCESS_TREE_EXECUTABLE"
            )
            contract.require(
                contract.absolute_contract_path(executable),
                "VERIFY_PROCESS_TREE_EXECUTABLE_ABSOLUTE",
            )
            role = contract.strict_text(record["role"], "VERIFY_PROCESS_TREE_ROLE")
            contract.require(role in roles, "VERIFY_PROCESS_TREE_ROLE")
            contract.require(type(record["target_cpu"]) is bool, "VERIFY_PROCESS_TREE_TARGET_CPU")
            expected_target_cpu = role in {"TARGET_JAVA", "TARGET_RUNTIME_DESCENDANT"}
            contract.require(
                record["target_cpu"] is expected_target_cpu,
                "VERIFY_PROCESS_TREE_TARGET_CPU_DERIVATION",
            )
            if role == "TARGET_JAVA":
                contract.require(
                    executable == target_executable,
                    "VERIFY_PROCESS_TREE_TARGET_EXECUTABLE_BINDING",
                )
            if role == "TRACER":
                contract.require(
                    tree["tracer_wrapped"] is True and pid == root_pid,
                    "VERIFY_PROCESS_TREE_TRACER_IDENTITY",
                )
            contract.strict_text(record["state"], "VERIFY_PROCESS_TREE_STATE", maximum=1)
            schedstat_status = contract.availability(record["schedstat"])
            expected_schedstat_fields = (
                {"status", "value"} if schedstat_status == "AVAILABLE" else {"reason", "status"}
            )
            contract.exact_object(
                record["schedstat"],
                expected_schedstat_fields,
                "VERIFY_PROCESS_TREE_SCHEDSTAT_FIELDS",
            )
            schedstat_value = availability_value(record["schedstat"])
            if schedstat_value is not None:
                contract.strict_text(schedstat_value, "VERIFY_PROCESS_TREE_SCHEDSTAT")
            validated_records[pid] = record
        if validated_records:
            contract.require(root_pid in validated_records, "VERIFY_PROCESS_TREE_ROOT_MISSING")
            contract.require(
                all(
                    process_reaches_root(validated_records, pid, root_pid)
                    for pid in validated_records
                ),
                "VERIFY_PROCESS_TREE_REACHABILITY",
            )
            derived_roles = derive_process_roles(
                validated_records,
                root_pid=root_pid,
                target_executable=target_executable,
                tracer_wrapped=tree["tracer_wrapped"],
            )
            for pid, record in validated_records.items():
                expected_role, expected_target_cpu = derived_roles[pid]
                contract.require(
                    record["role"] == expected_role and record["target_cpu"] is expected_target_cpu,
                    "VERIFY_PROCESS_TREE_ROLE_DERIVATION",
                )
            if tree["tracer_wrapped"] is False:
                contract.require(
                    derived_roles[root_pid] == ("TARGET_JAVA", True),
                    "VERIFY_PROCESS_TREE_UNWRAPPED_ROOT",
                )
    contract.require(end >= begin, "VERIFY_HOST_SAMPLE_ORDER", str(index))
    return value


def validate_lane_process_identity(
    events: list[dict[str, Any]],
    host_samples: list[dict[str, Any]],
    *,
    target_executable: str,
) -> dict[str, object]:
    """Bind the Java-emitted PID to one stable sampled /proc identity."""

    contract.require(events, "LANE_PROCESS_IDENTITY_EVENTS_EMPTY")
    start = events[0]
    end = events[-1]
    lane_pid = contract.strict_int(start.get("process_id"), "LANE_START_PROCESS_ID", minimum=1)
    lane_begin = contract.strict_int(
        start.get("monotonic_anchor_ns"), "LANE_MONOTONIC_ANCHOR", minimum=1
    )
    lane_end = contract.strict_int(
        end.get("monotonic_ns"), "LANE_MONOTONIC_END", minimum=lane_begin
    )
    lane_wall_begin = contract.strict_int(
        start.get("wall_anchor_ns"), "LANE_WALL_ANCHOR", minimum=1
    )
    lane_wall_end = contract.strict_int(
        end.get("wall_time_ns"), "LANE_WALL_END", minimum=lane_wall_begin
    )
    expected_executable = contract.strict_text(
        target_executable, "LANE_PROCESS_IDENTITY_EXPECTED_EXECUTABLE"
    )
    bound_identity: dict[str, object] | None = None
    previous_sample_end = 0
    previous_sample_wall_end = 0
    for sample_index, sample in enumerate(host_samples):
        validated_sample = validate_host_sample(sample, sample_index)
        contract.require(
            validated_sample["sample_begin_monotonic_ns"] >= previous_sample_end,
            "VERIFY_HOST_SAMPLE_SEQUENCE",
        )
        previous_sample_end = validated_sample["sample_end_monotonic_ns"]
        contract.require(
            validated_sample["sample_begin_wall_time_ns"] >= previous_sample_wall_end,
            "VERIFY_HOST_SAMPLE_WALL_SEQUENCE",
        )
        previous_sample_wall_end = validated_sample["sample_end_wall_time_ns"]
        overlaps_lane = (
            validated_sample["sample_end_monotonic_ns"] >= lane_begin
            and validated_sample["sample_begin_monotonic_ns"] <= lane_end
            and validated_sample["sample_end_wall_time_ns"] >= lane_wall_begin
            and validated_sample["sample_begin_wall_time_ns"] <= lane_wall_end
        )
        if not overlaps_lane:
            continue
        tree = availability_value(validated_sample["target_process_tree"])
        if not isinstance(tree, dict):
            continue
        contract.require(
            tree["target_executable"] == expected_executable,
            "LANE_PROCESS_IDENTITY_TARGET_EXECUTABLE",
        )
        target_records = [record for record in tree["processes"] if record["role"] == "TARGET_JAVA"]
        if not target_records:
            continue
        contract.require(len(target_records) == 1, "LANE_PROCESS_IDENTITY_MULTIPLE_TARGETS")
        target = target_records[0]
        identity = {
            "executable": target["executable"],
            "pid": target["pid"],
            "start_time_ticks": target["start_time_ticks"],
        }
        contract.require(identity["pid"] == lane_pid, "LANE_PROCESS_IDENTITY_PID")
        contract.require(
            identity["executable"] == expected_executable,
            "LANE_PROCESS_IDENTITY_EXECUTABLE",
        )
        root_pid = tree["root_pid"]
        if tree["tracer_wrapped"] is True:
            contract.require(identity["pid"] != root_pid, "LANE_PROCESS_IDENTITY_TRACER_ROOT")
        else:
            contract.require(identity["pid"] == root_pid, "LANE_PROCESS_IDENTITY_UNWRAPPED_ROOT")
        if bound_identity is None:
            bound_identity = identity
        else:
            contract.require(identity == bound_identity, "LANE_PROCESS_IDENTITY_CHANGED")
    contract.require(bound_identity is not None, "LANE_PROCESS_IDENTITY_MISSING")
    return bound_identity


def verify_jfr_evidence(
    value: object,
    *,
    evidence_root: Path,
    java_tool: Path,
    jfr_tool: Path,
    selected_events: list[str],
    environment: dict[str, str],
    working_directory: Path,
) -> dict[str, object]:
    record = contract.exact_object(value, {"status", "value"}, "VERIFY_JFR_FIELDS")
    contract.require(record["status"] == "AVAILABLE", "VERIFY_JFR_REQUIRED")
    details = contract.exact_object(
        record["value"],
        {"artifacts", "enabled_events", "event_intervals", "invocations"},
        "VERIFY_JFR_VALUE_FIELDS",
    )
    artifacts = contract.exact_object(
        details["artifacts"],
        {"events", "events_stderr", "recording", "summary", "summary_stderr"},
        "VERIFY_JFR_ARTIFACT_FIELDS",
    )
    paths = {
        name: verified_artifact_path(evidence_root, item, f"VERIFY_JFR_{name.upper()}")
        for name, item in artifacts.items()
    }
    contract.require(paths["recording"].stat().st_size > 0, "VERIFY_JFR_RECORDING_EMPTY")
    summary = paths["summary"].read_text(encoding="utf-8", errors="strict")
    contract.require(
        all(marker in summary for marker in ("Version:", "Chunks:", "Start:", "Duration:")),
        "VERIFY_JFR_SUMMARY_INCOMPLETE",
    )
    document = json.loads(
        paths["events"].read_bytes(), object_pairs_hook=contract.reject_duplicate_keys
    )
    validate_jfr_document(document, set(selected_events))
    invocations = contract.exact_object(
        details["invocations"], {"events", "summary"}, "VERIFY_JFR_INVOCATIONS"
    )
    summary_replay, summary_receipt = exact_subprocess(
        [str(jfr_tool), "summary", str(paths["recording"])],
        environment=environment,
        working_directory=working_directory,
        timeout=60,
    )
    contract.require(summary_replay.returncode == 0, "VERIFY_JFR_SUMMARY_REPLAY_EXIT")
    contract.require(
        summary_replay.stdout == paths["summary"].read_bytes(), "VERIFY_JFR_SUMMARY_REPLAY"
    )
    contract.require(
        summary_replay.stderr == paths["summary_stderr"].read_bytes(),
        "VERIFY_JFR_SUMMARY_STDERR_REPLAY",
    )
    contract.require(invocations["summary"] == summary_receipt, "VERIFY_JFR_SUMMARY_INVOCATION")
    replay, events_receipt = exact_subprocess(
        [
            str(jfr_tool),
            "print",
            "--json",
            "--events",
            ",".join(selected_events),
            str(paths["recording"]),
        ],
        environment=environment,
        working_directory=working_directory,
        timeout=120,
    )
    contract.require(replay.returncode == 0, "VERIFY_JFR_REPLAY_EXIT")
    contract.require(replay.stdout == paths["events"].read_bytes(), "VERIFY_JFR_EVENTS_REPLAY")
    contract.require(
        replay.stderr == paths["events_stderr"].read_bytes(), "VERIFY_JFR_EVENTS_STDERR_REPLAY"
    )
    contract.require(invocations["events"] == events_receipt, "VERIFY_JFR_EVENTS_INVOCATION")
    replay_document = json.loads(replay.stdout, object_pairs_hook=contract.reject_duplicate_keys)
    validate_jfr_document(replay_document, set(selected_events))
    contract.require(replay_document == document, "VERIFY_JFR_REPLAY_DOCUMENT")
    contract.require(
        details["event_intervals"] == jfr_intervals(document),
        "VERIFY_JFR_INTERVALS",
    )
    enabled = jfr_profile_enabled_events(java_tool, selected_events)
    contract.require(details["enabled_events"] == enabled, "VERIFY_JFR_ENABLED_EVENTS")
    return record


def verify_strace_evidence(value: object, *, evidence_root: Path) -> dict[str, object]:
    record = contract.exact_object(value, {"status", "value"}, "VERIFY_STRACE_FIELDS")
    contract.require(record["status"] == "AVAILABLE", "VERIFY_STRACE_REQUIRED")
    details = contract.exact_object(
        record["value"], {"artifacts", "fsync_events"}, "VERIFY_STRACE_VALUE_FIELDS"
    )
    raw_artifacts = details["artifacts"]
    contract.require(isinstance(raw_artifacts, list) and raw_artifacts, "VERIFY_STRACE_ARTIFACTS")
    paths = [
        verified_artifact_path(evidence_root, item, "VERIFY_STRACE_FILE") for item in raw_artifacts
    ]
    reparsed = parse_strace_files(paths, artifact_root=evidence_root)
    contract.require(reparsed == record, "VERIFY_STRACE_REPARSE")
    contract.require(
        isinstance(details["fsync_events"], list) and details["fsync_events"],
        "VERIFY_STRACE_FSYNC_REQUIRED",
    )
    return record


def validate_environment_evidence(
    value: object,
    allocation: dict[str, Any],
    host_receipt: dict[str, Any],
    prepared_lanes: list[PreparedLane],
) -> dict[str, Any]:
    environment = contract.exact_object(
        value,
        {
            "allocation_preflight",
            "available_processors",
            "cgroup_membership",
            "cgroup_mode",
            "cgroup_paths",
            "cgroup_values",
            "container_identity",
            "container_image_digest",
            "container_runtime",
            "cpu_affinity",
            "host_receipt",
            "host_telemetry_state",
            "kernel_release",
            "machine",
            "memory_host",
            "operating_system",
            "platform",
            "python",
            "python_os_cpu_count",
            "wsl_interop",
        },
        "VERIFY_ENVIRONMENT_FIELDS",
    )
    contract.require(
        environment["available_processors"] == allocation["resources"]["available_processors"],
        "VERIFY_ENVIRONMENT_PROCESSORS",
    )
    contract.require(environment["host_receipt"] == host_receipt, "VERIFY_ENVIRONMENT_HOST_RECEIPT")
    contract.require(
        availability_value(environment["container_identity"]) == host_receipt["container"],
        "VERIFY_ENVIRONMENT_CONTAINER_IDENTITY",
    )
    contract.require(
        environment["host_telemetry_state"] == "AWAITING_LANES_COMPLETE_HANDSHAKE",
        "VERIFY_ENVIRONMENT_HOST_STATE",
    )
    cgroup_values = contract.exact_object(
        environment["cgroup_values"],
        {"cpu.max", "cpu.stat", "cpuset.cpus.effective", "memory.current", "memory.max"},
        "VERIFY_ENVIRONMENT_CGROUP_FIELDS",
    )
    for name, item in cgroup_values.items():
        status = contract.availability(item)
        expected_fields = {"status", "value"} if status == "AVAILABLE" else {"reason", "status"}
        contract.exact_object(item, expected_fields, f"VERIFY_ENVIRONMENT_{name}_FIELDS")
    contract.require(
        environment["cgroup_mode"] == allocation["resources"]["cgroup_mode"],
        "VERIFY_ENVIRONMENT_CGROUP_MODE",
    )
    cgroup_paths = contract.exact_object(
        environment["cgroup_paths"], {"cpu", "cpuset", "memory"}, "VERIFY_CGROUP_PATH_FIELDS"
    )
    for item in cgroup_paths.values():
        contract.strict_text(item, "VERIFY_CGROUP_PATH")
    memberships = environment["cgroup_membership"]
    contract.require(
        isinstance(memberships, list)
        and len(memberships) == (1 if environment["cgroup_mode"] == "V2" else 3),
        "VERIFY_CGROUP_MEMBERSHIP_COUNT",
    )
    for item in memberships:
        membership = contract.exact_object(
            item,
            {"controller", "mount_point", "mount_root", "process_path", "resolved_path"},
            "VERIFY_CGROUP_MEMBERSHIP_FIELDS",
        )
        for member_value in membership.values():
            contract.strict_text(member_value, "VERIFY_CGROUP_MEMBERSHIP_VALUE")
    preflight = contract.exact_object(
        environment["allocation_preflight"],
        {
            "allocation_root_read_only",
            "java_dry_run",
            "jfr",
            "jfr_recording",
            "native_library_load",
            "psi",
            "sidecar",
            "strace",
            "strace_child_fsync",
        },
        "VERIFY_PREFLIGHT_FIELDS",
    )
    contract.require(preflight["allocation_root_read_only"] is True, "VERIFY_PREFLIGHT_READ_ONLY")
    allocation_paths = {
        identifier: str(item["path"])
        for identifier, item in allocation_artifacts(allocation).items()
    }
    contract.require(prepared_lanes, "VERIFY_PREFLIGHT_LANES")
    probe_environment = dict(prepared_lanes[0].environment)
    probe_environment["DELTA_DIAGNOSTIC_PROFILE"] = "PREFLIGHT"
    probe_working_directory = prepared_lanes[0].working_directory
    expected_invocations = {
        "java_dry_run": (
            [
                allocation_paths["JAVA_EXECUTABLE"],
                "--enable-native-access=ALL-UNNAMED",
                "-cp",
                allocation_paths["JAVA_CLASSES_JAR"],
                JFR_DRY_RUN_CLASS,
            ],
            0,
        ),
        "jfr": ([allocation_paths["JFR_EXECUTABLE"], "version"], 0),
        "native_library_load": (
            [
                sys.executable,
                "-c",
                "import ctypes,sys; ctypes.CDLL(sys.argv[1])",
                allocation_paths["NATIVE_LIBRARY"],
            ],
            0,
        ),
        "sidecar": ([allocation_paths["SIDECAR_EXECUTABLE"]], 2),
        "strace": ([allocation_paths["STRACE_EXECUTABLE"], "--version"], 0),
    }
    for name in ("java_dry_run", "jfr", "native_library_load", "sidecar", "strace"):
        invocation = contract.validate_process_receipt(
            preflight[name], "VERIFY_PREFLIGHT_INVOCATION"
        )
        expected_argv, expected_exit = expected_invocations[name]
        contract.require(invocation["argv"] == expected_argv, "VERIFY_PREFLIGHT_INVOCATION_BINDING")
        contract.require(
            invocation["exit_code"] == expected_exit, "VERIFY_PREFLIGHT_INVOCATION_EXIT_BINDING"
        )
        expected_contract = contract.invocation_record(
            expected_argv,
            environment=probe_environment,
            working_directory=probe_working_directory,
        )
        contract.require(
            {field: invocation[field] for field in contract.INVOCATION_FIELDS} == expected_contract,
            "VERIFY_PREFLIGHT_INVOCATION_CONTRACT",
            name,
        )
    jfr_probe = contract.exact_object(
        preflight["jfr_recording"],
        {
            "enabled_events",
            "extracted_event_count",
            "java_invocation",
            "jfr_invocation",
            "recording_sha256",
            "stderr_sha256",
            "stdout_sha256",
        },
        "VERIFY_PREFLIGHT_JFR_FIELDS",
    )
    contract.require(
        jfr_probe["enabled_events"]
        == [
            "jdk.GarbageCollection",
            "jdk.GCPhasePause",
            "jdk.SafepointBegin",
            "jdk.SafepointEnd",
            "jdk.Compilation",
            "jdk.CompilerPhase",
        ],
        "VERIFY_PREFLIGHT_JFR_EVENTS",
    )
    contract.strict_int(jfr_probe["extracted_event_count"], "VERIFY_PREFLIGHT_JFR_COUNT")
    jfr_invocations = {
        name: contract.validate_process_receipt(
            jfr_probe[name], f"VERIFY_PREFLIGHT_JFR_{name.upper()}"
        )
        for name in ("java_invocation", "jfr_invocation")
    }
    for name, invocation in jfr_invocations.items():
        contract.require(
            invocation["environment"] == probe_environment
            and invocation["environment_mode"] == "REPLACE"
            and invocation["working_directory"] == str(probe_working_directory),
            "VERIFY_PREFLIGHT_JFR_INVOCATION_CONTRACT",
            name,
        )
        contract.require(invocation["exit_code"] == 0, "VERIFY_PREFLIGHT_JFR_INVOCATION_EXIT")
    java_argv = jfr_invocations["java_invocation"]["argv"]
    contract.require(
        isinstance(java_argv, list) and len(java_argv) == 6, "VERIFY_PREFLIGHT_JAVA_ARGV"
    )
    recording_argument = java_argv[1]
    recording_prefix = "-XX:StartFlightRecording=filename="
    recording_suffix = ",settings=profile,dumponexit=true"
    contract.require(
        isinstance(recording_argument, str)
        and recording_argument.startswith(recording_prefix)
        and recording_argument.endswith(recording_suffix),
        "VERIFY_PREFLIGHT_JAVA_RECORDING_ARGUMENT",
    )
    recording_path = recording_argument[
        len(recording_prefix) : len(recording_argument) - len(recording_suffix)
    ]
    contract.require(
        contract.absolute_contract_path(recording_path)
        and Path(recording_path).name == "probe.jfr",
        "VERIFY_PREFLIGHT_JAVA_RECORDING_PATH",
    )
    contract.require(
        java_argv
        == [
            allocation_paths["JAVA_EXECUTABLE"],
            recording_argument,
            "--enable-native-access=ALL-UNNAMED",
            "-cp",
            allocation_paths["JAVA_CLASSES_JAR"],
            JFR_DRY_RUN_CLASS,
        ],
        "VERIFY_PREFLIGHT_JAVA_RECORDING_ARGV",
    )
    contract.require(
        jfr_invocations["jfr_invocation"]["argv"]
        == [
            allocation_paths["JFR_EXECUTABLE"],
            "print",
            "--json",
            "--events",
            ",".join(jfr_probe["enabled_events"]),
            recording_path,
        ],
        "VERIFY_PREFLIGHT_JFR_PRINT_ARGV",
    )
    for name in ("recording_sha256", "stderr_sha256", "stdout_sha256"):
        contract.content_id(jfr_probe[name], f"VERIFY_PREFLIGHT_JFR_{name.upper()}")
    strace_probe = contract.exact_object(
        preflight["strace_child_fsync"],
        {"event_count", "invocation", "stderr_sha256", "stdout_sha256"},
        "VERIFY_PREFLIGHT_STRACE_FIELDS",
    )
    contract.strict_int(strace_probe["event_count"], "VERIFY_PREFLIGHT_STRACE_COUNT", minimum=1)
    strace_invocation = contract.validate_process_receipt(
        strace_probe["invocation"], "VERIFY_PREFLIGHT_STRACE_INVOCATION"
    )
    contract.require(
        strace_invocation["environment"] == probe_environment
        and strace_invocation["environment_mode"] == "REPLACE"
        and strace_invocation["working_directory"] == str(probe_working_directory),
        "VERIFY_PREFLIGHT_STRACE_INVOCATION_CONTRACT",
    )
    expected_trace_prefix = list(prepared_lanes[0].trace_prefix)
    strace_argv = strace_invocation["argv"]
    contract.require(
        isinstance(strace_argv, list) and len(strace_argv) == len(expected_trace_prefix) + 5,
        "VERIFY_PREFLIGHT_STRACE_ARGV",
    )
    trace_output = strace_argv[len(expected_trace_prefix) + 1]
    contract.require(
        strace_argv[: len(expected_trace_prefix)] == expected_trace_prefix
        and strace_argv[len(expected_trace_prefix)] == "-o"
        and contract.absolute_contract_path(trace_output)
        and Path(trace_output).name == "probe.strace"
        and strace_argv[len(expected_trace_prefix) + 2 :]
        == [sys.executable, "-c", STRACE_CHILD_PROBE],
        "VERIFY_PREFLIGHT_STRACE_ARGV_BINDING",
    )
    contract.require(strace_invocation["exit_code"] == 0, "VERIFY_PREFLIGHT_STRACE_EXIT")
    psi = contract.exact_object(
        preflight["psi"], {"miss_policy", "status", "values"}, "VERIFY_PREFLIGHT_PSI_FIELDS"
    )
    contract.require(
        psi["miss_policy"] == "ANY_MISS_IS_INCONCLUSIVE_WHEN_PSI_NOT_AVAILABLE",
        "VERIFY_PREFLIGHT_PSI_POLICY",
    )
    contract.require(psi["status"] in {"AVAILABLE", "NOT_AVAILABLE"}, "VERIFY_PREFLIGHT_PSI_STATUS")
    psi_values = contract.exact_object(
        psi["values"], {"cpu", "io"}, "VERIFY_PREFLIGHT_PSI_VALUE_FIELDS"
    )
    for item in psi_values.values():
        contract.availability(item)
    expected_psi_status = (
        "AVAILABLE"
        if all(pressure_total(item) is not None for item in psi_values.values())
        else "NOT_AVAILABLE"
    )
    contract.require(psi["status"] == expected_psi_status, "VERIFY_PREFLIGHT_PSI_DERIVATION")
    for name in ("container_identity", "cpu_affinity", "memory_host", "wsl_interop"):
        contract.availability(environment[name])
    verify_live_allocation(allocation, environment)
    return environment


def verify_evidence_directory(evidence_root: Path) -> dict[str, Any]:
    """Independently rederive every seal, artifact join, miss, and classification."""

    root = evidence_root.resolve(strict=True)
    evidence_path = root / "diagnostic-evidence.json"
    evidence, evidence_canonical = contract.canonical_document(evidence_path)
    contract.exact_object(evidence, EVIDENCE_FIELDS, "EVIDENCE_FIELDS")
    contract.require(evidence["schema_version"] == contract.SCHEMA_VERSION, "EVIDENCE_SCHEMA")
    contract.require(evidence["type_name"] == contract.EVIDENCE_TYPE, "EVIDENCE_TYPE")
    contract.require(evidence["status"] == "SEALED", "EVIDENCE_STATUS")
    contract.require(evidence["authority"] == "DIAGNOSTIC_ONLY", "EVIDENCE_AUTHORITY")
    for field, expected in contract.expected_authority().items():
        contract.require(evidence[field] == expected, "EVIDENCE_AUTHORITY_FIELD", field)

    artifacts = contract.exact_object(
        evidence["artifacts"],
        {
            "allocation_manifest",
            "attempt_seal",
            "environment",
            "execution_started_seal",
            "frozen_manifest",
            "host_receipt",
            "host_telemetry",
            "lanes_complete",
            "preflight_receipt",
        },
        "EVIDENCE_ARTIFACT_FIELDS",
    )
    paths = {
        name: verified_artifact_path(root, item, f"VERIFY_{name.upper()}")
        for name, item in artifacts.items()
    }

    manifest, manifest_canonical = contract.canonical_document(paths["frozen_manifest"])
    contract.validate_manifest(manifest, executable=True)
    manifest_sha256 = contract.sha256_id(manifest_canonical)
    contract.require(evidence["manifest_sha256"] == manifest_sha256, "VERIFY_MANIFEST_SHA256")
    contract.require(
        evidence["diagnostic_campaign_id"] == manifest["diagnostic_campaign_id"],
        "VERIFY_CAMPAIGN_ID",
    )
    contract.require(evidence["source"] == manifest["source"], "VERIFY_SOURCE")

    recorded_source_receipt = contract.validate_checkout_receipt(
        evidence["source_checkout"], "VERIFY_SOURCE_RECEIPT"
    )
    recorded_manifest_receipt = contract.validate_checkout_receipt(
        evidence["manifest_checkout"], "VERIFY_MANIFEST_RECEIPT", manifest=True
    )
    source_receipt = contract.verify_source_checkout(
        Path(contract.strict_text(recorded_source_receipt["checkout_root"], "VERIFY_SOURCE_ROOT")),
        manifest["source"],
    )
    contract.require(source_receipt == evidence["source_checkout"], "VERIFY_SOURCE_RECEIPT")
    manifest_receipt = contract.verify_manifest_checkout(
        Path(
            contract.strict_text(recorded_manifest_receipt["checkout_root"], "VERIFY_MANIFEST_ROOT")
        )
        / contract.strict_text(
            recorded_manifest_receipt["manifest_relative_path"], "VERIFY_MANIFEST_RELATIVE"
        ),
        Path(
            contract.strict_text(recorded_manifest_receipt["checkout_root"], "VERIFY_MANIFEST_ROOT")
        ),
    )
    contract.require(manifest_receipt == evidence["manifest_checkout"], "VERIFY_MANIFEST_RECEIPT")

    copied_allocation_record = dict(manifest["environment"]["allocation_manifest"])
    copied_allocation_record["path"] = str(paths["allocation_manifest"])
    manifest_for_allocation = copy.deepcopy(manifest)
    manifest_for_allocation["environment"]["allocation_manifest"] = copied_allocation_record
    allocation = contract.load_and_verify_allocation(
        copied_allocation_record, manifest_for_allocation
    )
    expected_prepared = prepare_lanes(
        manifest,
        allocation,
        source_root=Path(str(source_receipt["checkout_root"])),
        evidence_root=Path(str(manifest["evidence_directory"])),
    )
    preflight_value, _ = contract.canonical_document(paths["preflight_receipt"])
    preflight_raw = paths["preflight_receipt"].read_bytes()
    preflight = validate_preflight_receipt(
        preflight_value,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        source_root=Path(str(source_receipt["checkout_root"])),
        manifest_checkout=Path(str(manifest_receipt["checkout_root"])),
        allocation=allocation,
    )
    contract.require(preflight["source_checkout"] == source_receipt, "VERIFY_PREFLIGHT_SOURCE")
    contract.require(
        preflight["manifest_checkout"] == manifest_receipt, "VERIFY_PREFLIGHT_MANIFEST"
    )

    host_receipt, _ = load_host_receipt(paths["host_receipt"], manifest, allocation)
    environment, _ = contract.canonical_document(paths["environment"])
    environment = validate_environment_evidence(
        environment, allocation, host_receipt, expected_prepared
    )
    contract.require(
        environment["allocation_preflight"] == preflight["allocation_preflight"],
        "VERIFY_PREFLIGHT_CAPABILITY_COPY",
    )
    current_environment = environment_snapshot(manifest, allocation, host_receipt)
    verify_live_allocation(allocation, current_environment)

    handshake, handshake_canonical = contract.canonical_document(paths["lanes_complete"])
    contract.exact_object(
        handshake,
        {
            "capture_sha256",
            "completed_at_utc",
            "diagnostic_campaign_id",
            "profile_order",
            "receipt_nonce",
            "schema_version",
            "type_name",
        },
        "VERIFY_LANES_COMPLETE_FIELDS",
    )
    contract.require(handshake["schema_version"] == contract.SCHEMA_VERSION, "VERIFY_LANES_SCHEMA")
    contract.require(handshake["type_name"] == LANES_COMPLETE_TYPE, "VERIFY_LANES_TYPE")
    contract.require(handshake["profile_order"] == contract.PROFILE_ORDER, "VERIFY_LANES_ORDER")
    contract.require(
        handshake["diagnostic_campaign_id"] == manifest["diagnostic_campaign_id"],
        "VERIFY_LANES_CAMPAIGN",
    )
    contract.require(
        handshake["receipt_nonce"] == manifest["environment"]["host_receipt_nonce"],
        "VERIFY_LANES_NONCE",
    )
    handshake_completed_ns = instant_ns(
        contract.strict_text(handshake["completed_at_utc"], "VERIFY_LANES_COMPLETED")
    )
    host_telemetry, _ = load_host_telemetry(
        paths["host_telemetry"],
        manifest,
        lanes_complete_sha256=contract.sha256_id(handshake_canonical + b"\n"),
        wait_seconds=0,
    )
    receipt_ns = instant_ns(host_receipt["collected_at_utc"])
    capture_start_ns = instant_ns(host_telemetry["capture_started_at_utc"])
    capture_end_ns = instant_ns(host_telemetry["capture_ended_at_utc"])
    contract.require(
        capture_start_ns <= receipt_ns <= capture_end_ns,
        "VERIFY_HOST_RECEIPT_CAPTURE_INTERVAL",
    )
    contract.require(
        capture_start_ns <= handshake_completed_ns <= capture_end_ns,
        "VERIFY_HANDSHAKE_CAPTURE_INTERVAL",
    )
    evidence_ended_ns = instant_ns(
        contract.strict_text(evidence["ended_at_utc"], "VERIFY_EVIDENCE_ENDED")
    )
    contract.require(evidence_ended_ns >= capture_end_ns, "VERIFY_EVIDENCE_TIME_ORDER")

    lanes = evidence["lanes"]
    contract.require(isinstance(lanes, list) and len(lanes) == 2, "VERIFY_LANE_COUNT")
    records = allocation_artifacts(allocation)
    java_tool = Path(str(records["JAVA_EXECUTABLE"]["path"]))
    jfr_tool = Path(str(records["JFR_EXECUTABLE"]["path"]))
    schedule = manifest["schedule"]
    recomputed_lanes = copy.deepcopy(lanes)
    prior_lane_ended_ns = capture_start_ns
    first_lane_started_ns: int | None = None
    for index, lane in enumerate(recomputed_lanes):
        contract.exact_object(lane, LANE_EVIDENCE_FIELDS, "VERIFY_LANE_FIELDS")
        expected_manifest_lane = manifest["lanes"][index]
        profile = contract.PROFILE_ORDER[index]
        contract.require(lane["profile_id"] == profile, "VERIFY_LANE_PROFILE")
        contract.require(lane["java_involved"] is True, "VERIFY_LANE_JAVA")
        contract.require(lane["exit_code"] == 0 and lane["timed_out"] is False, "VERIFY_LANE_EXIT")
        expected_executed_argv = [
            *expected_prepared[index].trace_prefix,
            "-o",
            str(expected_prepared[index].lane_directory / "fsync.strace"),
            *expected_prepared[index].argv,
        ]
        contract.require(
            lane["executed_argv"] == expected_executed_argv,
            "VERIFY_LANE_ARGV",
            profile,
        )
        contract.require(
            lane["executed_environment"] == expected_prepared[index].environment,
            "VERIFY_LANE_ENVIRONMENT",
            profile,
        )
        contract.require(lane["environment_mode"] == "REPLACE", "VERIFY_LANE_ENVIRONMENT_MODE")
        contract.require(
            lane["working_directory"] == str(expected_prepared[index].working_directory),
            "VERIFY_LANE_WORKING_DIRECTORY",
            profile,
        )
        contract.strict_int(lane["monotonic_duration_ns"], "VERIFY_LANE_DURATION", minimum=1)
        lane_started_ns = instant_ns(
            contract.strict_text(lane["started_at_utc"], "VERIFY_LANE_STARTED")
        )
        if first_lane_started_ns is None:
            first_lane_started_ns = lane_started_ns
        lane_ended_ns = instant_ns(contract.strict_text(lane["ended_at_utc"], "VERIFY_LANE_ENDED"))
        contract.require(
            prior_lane_ended_ns <= lane_started_ns <= lane_ended_ns <= handshake_completed_ns,
            "VERIFY_LANE_TIME_ORDER",
            profile,
        )
        prior_lane_ended_ns = lane_ended_ns
        lane_artifacts = contract.exact_object(
            lane["artifacts"],
            {"event_log", "host_telemetry", "stderr", "stdout"},
            "VERIFY_LANE_ARTIFACT_FIELDS",
        )
        lane_paths = {
            name: verified_artifact_path(root, item, f"VERIFY_LANE_{name.upper()}")
            for name, item in lane_artifacts.items()
        }
        events = read_lane_observations(lane_paths["event_log"])
        contract.require(lane["event_count"] == len(events), "VERIFY_LANE_EVENT_COUNT")
        validate_lane_execution(
            events,
            profile=profile,
            duration=schedule["duration_seconds_per_lane"],
            expected_processors=allocation["resources"]["available_processors"],
            exit_code=lane["exit_code"],
            timed_out=lane["timed_out"],
        )
        host_samples = read_json_lines(lane_paths["host_telemetry"], "VERIFY_HOST_SAMPLE")
        contract.require(host_samples, "VERIFY_HOST_SAMPLES_EMPTY")
        validate_lane_process_identity(
            events,
            host_samples,
            target_executable=str(java_tool.resolve(strict=True)),
        )
        lane["jfr"] = verify_jfr_evidence(
            lane["jfr"],
            evidence_root=root,
            java_tool=java_tool,
            jfr_tool=jfr_tool,
            selected_events=list(expected_manifest_lane["jfr_events"]),
            environment=expected_prepared[index].environment,
            working_directory=expected_prepared[index].working_directory,
        )
        lane["strace_fsync"] = verify_strace_evidence(lane["strace_fsync"], evidence_root=root)
        lane["missed_slots"] = build_missed_slots(
            events,
            host_samples,
            environment=environment,
            host_telemetry=host_telemetry,
            jfr=lane["jfr"],
            trace_files=[],
            strace=lane["strace_fsync"],
        )
        contract.require(
            lane["missed_slots"] == lanes[index]["missed_slots"],
            "VERIFY_MISSED_SLOTS",
            profile,
        )

    capture_sha256 = contract.sha256_id(contract.canonical_bytes(lane_capture_binding(lanes)))
    contract.require(handshake["capture_sha256"] == capture_sha256, "VERIFY_CAPTURE_BINDING")
    classification, classified_slots = contract.classify_campaign(recomputed_lanes)
    contract.require(
        evidence["campaign_classification"] == classification,
        "VERIFY_CLASSIFICATION",
    )
    contract.require(
        evidence["classified_missed_slots"] == classified_slots,
        "VERIFY_CLASSIFIED_SLOTS",
    )

    ledger = ledger_paths(
        Path(str(manifest["environment"]["campaign_ledger_directory"])),
        str(manifest["diagnostic_campaign_id"]),
    )
    attempt, attempt_canonical = contract.canonical_document(ledger["attempt"])
    copied_attempt, _ = contract.canonical_document(paths["attempt_seal"])
    contract.require(attempt == copied_attempt, "VERIFY_ATTEMPT_COPY")
    validate_attempt_seal(
        attempt,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        preflight=preflight,
        preflight_raw=preflight_raw,
    )
    attempt_started_ns = instant_ns(
        contract.strict_text(attempt["started_at_utc"], "VERIFY_ATTEMPT_STARTED")
    )
    started, started_canonical = contract.canonical_document(ledger["started"])
    copied_started, _ = contract.canonical_document(paths["execution_started_seal"])
    contract.require(started == copied_started, "VERIFY_EXECUTION_STARTED_COPY")
    validate_execution_started_seal(
        started,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_canonical + b"\n",
    )
    execution_started_ns = instant_ns(
        contract.strict_text(started["started_at_utc"], "VERIFY_EXECUTION_STARTED_TIME")
    )
    contract.require(execution_started_ns >= attempt_started_ns, "VERIFY_EXECUTION_BEFORE_ATTEMPT")
    contract.require(
        first_lane_started_ns is not None and execution_started_ns <= first_lane_started_ns,
        "VERIFY_EXECUTION_STARTED_AFTER_LANE",
    )
    contract.require(
        attempt_started_ns <= receipt_ns <= handshake_completed_ns,
        "VERIFY_ATTEMPT_TIME_ORDER",
    )
    contract.require(attempt["source_checkout"] == source_receipt, "VERIFY_ATTEMPT_SOURCE_RECEIPT")
    contract.require(
        attempt["manifest_checkout"] == manifest_receipt, "VERIFY_ATTEMPT_MANIFEST_RECEIPT"
    )
    external = contract.exact_object(
        evidence["external_ledger"],
        {
            "attempt_record_sha256",
            "completion_record_required",
            "execution_started_record_sha256",
            "terminal_record_required",
        },
        "VERIFY_EXTERNAL_LEDGER_FIELDS",
    )
    attempt_raw_sha = contract.sha256_id(attempt_canonical + b"\n")
    contract.require(external["attempt_record_sha256"] == attempt_raw_sha, "VERIFY_LEDGER_ATTEMPT")
    started_raw_sha = contract.sha256_id(started_canonical + b"\n")
    contract.require(
        external["execution_started_record_sha256"] == started_raw_sha,
        "VERIFY_LEDGER_EXECUTION_STARTED",
    )
    contract.require(
        external["completion_record_required"] is True, "VERIFY_LEDGER_COMPLETION_FLAG"
    )
    contract.require(external["terminal_record_required"] is True, "VERIFY_LEDGER_TERMINAL_FLAG")
    completion_value, _ = contract.canonical_document(ledger["completed"])
    completion = validate_completion_seal(
        completion_value,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_canonical + b"\n",
        started_raw=started_canonical + b"\n",
    )
    completion_ns = instant_ns(
        contract.strict_text(completion["completed_at_utc"], "VERIFY_COMPLETION_TIME")
    )
    contract.require(completion_ns >= evidence_ended_ns, "VERIFY_COMPLETION_TIME_ORDER")
    contract.require(
        completion["evidence_sha256"] == contract.sha256_id(evidence_canonical + b"\n"),
        "VERIFY_COMPLETION_EVIDENCE",
    )
    terminal_value, _ = contract.canonical_document(ledger["terminal"])
    terminal = validate_terminal_seal(
        terminal_value,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_canonical + b"\n",
        started_raw=started_canonical + b"\n",
    )
    contract.require(terminal["outcome"] == "COMPLETED", "VERIFY_TERMINAL_STATE")
    contract.require(terminal["outcome_record"] == completion, "VERIFY_TERMINAL_OUTCOME")
    contract.require(
        terminal["outcome_record_sha256"]
        == contract.sha256_id(contract.canonical_bytes(completion) + b"\n"),
        "VERIFY_TERMINAL_OUTCOME",
    )
    terminal_ns = instant_ns(
        contract.strict_text(terminal["sealed_at_utc"], "VERIFY_TERMINAL_TIME")
    )
    contract.require(terminal_ns >= evidence_ended_ns, "VERIFY_TERMINAL_TIME_ORDER")
    contract.require(not ledger["failed"].exists(), "VERIFY_CONFLICTING_FAILURE_SEAL")
    contract.require(not (root / "failure.json").exists(), "VERIFY_CONFLICTING_FAILURE_ARTIFACT")
    return evidence


def live_allocation_identity(allocation: dict[str, Any]) -> dict[str, object]:
    layout = cgroup_layout()
    values = normalized_cgroup_values(layout)
    snapshot = {
        "cgroup_mode": layout.mode if layout is not None else "NOT_AVAILABLE",
        "cgroup_values": values,
        "container_identity": available("PREFLIGHT_PINNED_CONTAINER"),
        "cpu_affinity": affinity(),
    }
    verify_live_allocation(allocation, snapshot)
    return {
        "available_processors": allocation["resources"]["available_processors"],
        "cgroup_mode": snapshot["cgroup_mode"],
        "cpu_affinity": availability_value(snapshot["cpu_affinity"]),
        "cpu_max": availability_value(values["cpu.max"]),
        "cpuset_cpus_effective": availability_value(values["cpuset.cpus.effective"]),
        "memory_max": availability_value(values["memory.max"]),
    }


def validate_preflight_receipt_location(path: Path, manifest: dict[str, Any]) -> Path:
    """Keep the non-consuming receipt in container-temporary, non-ledger storage."""

    resolved = path.resolve()
    temporary_root = Path(tempfile.gettempdir()).resolve(strict=True)
    try:
        relative = resolved.relative_to(temporary_root)
    except ValueError as error:
        raise contract.DiagnosticError("PREFLIGHT_RECEIPT_NOT_EPHEMERAL") from error
    contract.require(relative.parts, "PREFLIGHT_RECEIPT_NOT_EPHEMERAL")
    environment = manifest["environment"]
    persistent_roots = {
        "EVIDENCE": Path(str(manifest["evidence_directory"])).resolve(),
        "HOST_EXCHANGE": Path(str(environment["host_receipt_path"])).resolve().parent,
        "LEDGER": Path(str(environment["campaign_ledger_directory"])).resolve(),
    }
    for label, root in persistent_roots.items():
        try:
            resolved.relative_to(root)
        except ValueError:
            continue
        raise contract.DiagnosticError(f"PREFLIGHT_RECEIPT_PERSISTENT_LOCATION:{label}")
    return resolved


def validate_preflight_receipt(
    value: object,
    *,
    manifest: dict[str, Any],
    manifest_canonical: bytes,
    source_root: Path,
    manifest_checkout: Path,
    allocation: dict[str, Any],
) -> dict[str, Any]:
    receipt = contract.exact_object(value, PREFLIGHT_RECEIPT_FIELDS, "PREFLIGHT_RECEIPT_FIELDS")
    contract.require(receipt["schema_version"] == contract.SCHEMA_VERSION, "PREFLIGHT_SCHEMA")
    contract.require(receipt["type_name"] == PREFLIGHT_RECEIPT_TYPE, "PREFLIGHT_TYPE")
    contract.require(receipt["state"] == PREFLIGHT_RECEIPT_STATE, "PREFLIGHT_NON_CONSUMING_STATE")
    contract.require(receipt["consumes_campaign"] is False, "PREFLIGHT_CONSUMPTION")
    contract.require(
        receipt["diagnostic_campaign_id"] == manifest["diagnostic_campaign_id"],
        "PREFLIGHT_CAMPAIGN",
    )
    contract.require(receipt["source"] == manifest["source"], "PREFLIGHT_SOURCE")
    contract.require(
        receipt["manifest_sha256"] == contract.sha256_id(manifest_canonical),
        "PREFLIGHT_MANIFEST",
    )
    contract.require(
        receipt["allocation_manifest_sha256"]
        == manifest["environment"]["allocation_manifest"]["sha256"],
        "PREFLIGHT_ALLOCATION",
    )
    source_receipt = contract.validate_checkout_receipt(
        receipt["source_checkout"], "PREFLIGHT_SOURCE_CHECKOUT"
    )
    manifest_receipt = contract.validate_checkout_receipt(
        receipt["manifest_checkout"], "PREFLIGHT_MANIFEST_CHECKOUT", manifest=True
    )
    contract.require(
        Path(str(source_receipt["checkout_root"])).resolve(strict=True)
        == source_root.resolve(strict=True),
        "PREFLIGHT_SOURCE_ROOT",
    )
    contract.require(
        Path(str(manifest_receipt["checkout_root"])).resolve(strict=True)
        == manifest_checkout.resolve(strict=True),
        "PREFLIGHT_MANIFEST_ROOT",
    )
    contract.require(source_receipt["commit"] == manifest["source"]["commit"], "PREFLIGHT_COMMIT")
    contract.require(source_receipt["tree"] == manifest["source"]["tree"], "PREFLIGHT_TREE")
    contract.require(
        mount_is_read_only(Path(str(manifest["environment"]["allocation_root"]))),
        "PREFLIGHT_ALLOCATION_ROOT_NOT_READ_ONLY",
    )
    live = contract.exact_object(
        receipt["live_allocation"],
        {
            "available_processors",
            "cgroup_mode",
            "cpu_affinity",
            "cpu_max",
            "cpuset_cpus_effective",
            "memory_max",
        },
        "PREFLIGHT_LIVE_ALLOCATION_FIELDS",
    )
    contract.require(live == live_allocation_identity(allocation), "PREFLIGHT_LIVE_ALLOCATION")
    contract.strict_text(receipt["created_at_utc"], "PREFLIGHT_CREATED_AT")
    contract.require(isinstance(receipt["allocation_preflight"], dict), "PREFLIGHT_CAPABILITIES")
    return receipt


def preflight_campaign(
    manifest_path: Path,
    manifest_checkout: Path,
    source_root: Path,
    preflight_receipt_path: Path,
) -> dict[str, Any]:
    """Run every fallible capability/Git probe without starting the campaign."""

    manifest, manifest_canonical = contract.canonical_document(manifest_path)
    contract.validate_manifest(manifest, executable=True)
    expected_output = Path(str(manifest["evidence_directory"])).resolve()
    contract.require(not expected_output.exists(), "OUTPUT_DIRECTORY_MUST_BE_FRESH")
    contract.require(expected_output.parent.is_dir(), "OUTPUT_PARENT_MISSING")
    preflight_receipt_path = validate_preflight_receipt_location(preflight_receipt_path, manifest)
    contract.require(not preflight_receipt_path.exists(), "PREFLIGHT_RECEIPT_MUST_BE_FRESH")
    contract.require(preflight_receipt_path.is_absolute(), "PREFLIGHT_RECEIPT_ABSOLUTE")
    contract.require(preflight_receipt_path.parent.is_dir(), "PREFLIGHT_RECEIPT_PARENT")
    source_receipt = contract.verify_source_checkout(source_root, manifest["source"])
    manifest_receipt = contract.verify_manifest_checkout(manifest_path, manifest_checkout)
    contract.require(mount_is_read_only(source_root), "PREFLIGHT_SOURCE_NOT_READ_ONLY")
    contract.require(mount_is_read_only(manifest_checkout), "PREFLIGHT_MANIFEST_NOT_READ_ONLY")
    allocation = contract.load_and_verify_allocation(
        manifest["environment"]["allocation_manifest"], manifest
    )
    prepared_lanes = prepare_lanes(
        manifest,
        allocation,
        source_root=source_root.resolve(),
        evidence_root=expected_output,
    )
    allocation_preflight = preflight_allocation(
        allocation,
        allocation_root=Path(str(manifest["environment"]["allocation_root"])),
        prepared_lanes=prepared_lanes,
    )
    live_identity = live_allocation_identity(allocation)
    environment = manifest["environment"]
    for name in ("host_receipt_path", "host_telemetry_path"):
        contract.require(
            not Path(str(environment[name])).exists(), f"PREFLIGHT_{name.upper()}_FRESH"
        )
    ledger = ledger_paths(
        Path(str(environment["campaign_ledger_directory"])), str(manifest["diagnostic_campaign_id"])
    )
    contract.require(
        not any(path.exists() for path in ledger.values()), "CAMPAIGN_LEDGER_ALREADY_EXISTS"
    )
    receipt = {
        "allocation_manifest_sha256": environment["allocation_manifest"]["sha256"],
        "allocation_preflight": allocation_preflight,
        "consumes_campaign": False,
        "created_at_utc": utc_now(),
        "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
        "live_allocation": live_identity,
        "manifest_checkout": manifest_receipt,
        "manifest_sha256": contract.sha256_id(manifest_canonical),
        "schema_version": contract.SCHEMA_VERSION,
        "source": manifest["source"],
        "source_checkout": source_receipt,
        "state": PREFLIGHT_RECEIPT_STATE,
        "type_name": PREFLIGHT_RECEIPT_TYPE,
    }
    durable_exclusive_write(preflight_receipt_path, receipt)
    return receipt


def validate_attempt_identity(
    value: object,
    *,
    manifest: dict[str, Any],
    manifest_canonical: bytes,
) -> dict[str, Any]:
    """Validate the immutable identity of a durable consuming arm record."""

    attempt = contract.exact_object(value, ATTEMPT_SEAL_FIELDS, "ATTEMPT_SEAL_FIELDS")
    contract.require(attempt["schema_version"] == contract.SCHEMA_VERSION, "ATTEMPT_SCHEMA")
    contract.require(attempt["type_name"] == ATTEMPT_SEAL_TYPE, "ATTEMPT_TYPE")
    contract.require(attempt["state"] == ATTEMPT_SEAL_STATE, "ATTEMPT_STATE")
    contract.require(attempt["authority"] == "DIAGNOSTIC_ONLY", "ATTEMPT_AUTHORITY")
    contract.require(
        attempt["diagnostic_campaign_id"] == manifest["diagnostic_campaign_id"],
        "ATTEMPT_CAMPAIGN",
    )
    contract.require(attempt["source"] == manifest["source"], "ATTEMPT_SOURCE")
    contract.require(
        attempt["manifest_sha256"] == contract.sha256_id(manifest_canonical),
        "ATTEMPT_MANIFEST",
    )
    return attempt


def validate_attempt_seal(
    value: object,
    *,
    manifest: dict[str, Any],
    manifest_canonical: bytes,
    preflight: dict[str, Any],
    preflight_raw: bytes,
) -> dict[str, Any]:
    """Validate the consuming arm record written before host receipt publication."""

    attempt = validate_attempt_identity(
        value,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
    )
    contract.require(
        attempt["source_checkout"] == preflight["source_checkout"],
        "ATTEMPT_SOURCE_CHECKOUT",
    )
    contract.require(
        attempt["manifest_checkout"] == preflight["manifest_checkout"],
        "ATTEMPT_MANIFEST_CHECKOUT",
    )
    contract.require(
        attempt["allocation_manifest_sha256"]
        == manifest["environment"]["allocation_manifest"]["sha256"],
        "ATTEMPT_ALLOCATION",
    )
    contract.require(
        attempt["preflight_receipt_sha256"] == contract.sha256_id(preflight_raw),
        "ATTEMPT_PREFLIGHT_RECEIPT",
    )
    started_ns = instant_ns(contract.strict_text(attempt["started_at_utc"], "ATTEMPT_STARTED"))
    preflight_ns = instant_ns(
        contract.strict_text(preflight["created_at_utc"], "ATTEMPT_PREFLIGHT_CREATED")
    )
    contract.require(started_ns >= preflight_ns, "ATTEMPT_BEFORE_PREFLIGHT")
    return attempt


def arm_campaign(
    manifest_path: Path,
    manifest_checkout: Path,
    source_root: Path,
    preflight_receipt_path: Path,
) -> dict[str, Any]:
    """Consume the one-shot identity only after non-consuming preflight passes."""

    manifest, manifest_canonical = contract.canonical_document(manifest_path)
    contract.validate_manifest(manifest, executable=True)
    output_directory = Path(str(manifest["evidence_directory"])).resolve()
    contract.require(not output_directory.exists(), "OUTPUT_DIRECTORY_MUST_BE_FRESH")
    contract.require(output_directory.parent.is_dir(), "OUTPUT_PARENT_MISSING")
    preflight_receipt_path = validate_preflight_receipt_location(preflight_receipt_path, manifest)
    contract.require(mount_is_read_only(source_root), "PREFLIGHT_SOURCE_NOT_READ_ONLY")
    contract.require(mount_is_read_only(manifest_checkout), "PREFLIGHT_MANIFEST_NOT_READ_ONLY")
    allocation = contract.load_and_verify_allocation(
        manifest["environment"]["allocation_manifest"], manifest
    )
    prepare_lanes(
        manifest,
        allocation,
        source_root=source_root.resolve(),
        evidence_root=output_directory,
    )
    preflight_value, _ = contract.canonical_document(preflight_receipt_path)
    preflight = validate_preflight_receipt(
        preflight_value,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        source_root=source_root,
        manifest_checkout=manifest_checkout,
        allocation=allocation,
    )
    preflight_raw = preflight_receipt_path.read_bytes()
    contract.require(
        contract.verify_source_checkout(source_root, manifest["source"])
        == preflight["source_checkout"],
        "ARM_SOURCE_CHANGED_AFTER_PREFLIGHT",
    )
    contract.require(
        contract.verify_manifest_checkout(manifest_path, manifest_checkout)
        == preflight["manifest_checkout"],
        "ARM_MANIFEST_CHANGED_AFTER_PREFLIGHT",
    )
    environment = manifest["environment"]
    for name in ("host_receipt_path", "host_telemetry_path"):
        contract.require(not Path(str(environment[name])).exists(), f"ARM_{name.upper()}_FRESH")
    ledger_directory = Path(str(environment["campaign_ledger_directory"])).resolve()
    contract.require(ledger_directory.is_dir(), "LEDGER_DIRECTORY_MISSING")
    contract.require(os.access(ledger_directory, os.W_OK), "LEDGER_DIRECTORY_NOT_WRITABLE")
    try:
        ledger_directory.relative_to(output_directory)
    except ValueError:
        pass
    else:
        raise contract.DiagnosticError("LEDGER_INSIDE_EVIDENCE_DIRECTORY")
    try:
        output_directory.relative_to(ledger_directory)
    except ValueError:
        pass
    else:
        raise contract.DiagnosticError("EVIDENCE_INSIDE_LEDGER_DIRECTORY")
    seals = ledger_paths(ledger_directory, str(manifest["diagnostic_campaign_id"]))
    contract.require(
        not any(path.exists() for path in seals.values()), "CAMPAIGN_LEDGER_ALREADY_EXISTS"
    )
    attempt = {
        "allocation_manifest_sha256": environment["allocation_manifest"]["sha256"],
        "authority": "DIAGNOSTIC_ONLY",
        "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
        "manifest_checkout": preflight["manifest_checkout"],
        "manifest_sha256": contract.sha256_id(manifest_canonical),
        "preflight_receipt_sha256": contract.sha256_id(preflight_raw),
        "schema_version": contract.SCHEMA_VERSION,
        "source": manifest["source"],
        "source_checkout": preflight["source_checkout"],
        "started_at_utc": utc_now(),
        "state": ATTEMPT_SEAL_STATE,
        "type_name": ATTEMPT_SEAL_TYPE,
    }
    validate_attempt_seal(
        attempt,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        preflight=preflight,
        preflight_raw=preflight_raw,
    )
    durable_exclusive_write(seals["attempt"], attempt)
    return attempt


def validate_failure_seal(
    value: object,
    *,
    manifest: dict[str, Any],
    manifest_canonical: bytes,
    attempt_raw: bytes,
    started_raw: bytes,
) -> dict[str, Any]:
    failure = contract.exact_object(value, FAILURE_SEAL_FIELDS, "FAILURE_SEAL_FIELDS")
    contract.require(failure["schema_version"] == contract.SCHEMA_VERSION, "FAILURE_SCHEMA")
    contract.require(failure["type_name"] == FAILURE_SEAL_TYPE, "FAILURE_TYPE")
    contract.require(failure["state"] == "FAILED_NO_RERUN", "FAILURE_STATE")
    contract.require(
        failure["diagnostic_campaign_id"] == manifest["diagnostic_campaign_id"],
        "FAILURE_CAMPAIGN",
    )
    contract.content_id(failure["manifest_sha256"], "FAILURE_MANIFEST_ID")
    contract.content_id(failure["attempt_record_sha256"], "FAILURE_ATTEMPT_ID")
    contract.content_id(failure["execution_started_record_sha256"], "FAILURE_EXECUTION_STARTED_ID")
    contract.require(
        failure["manifest_sha256"] == contract.sha256_id(manifest_canonical),
        "FAILURE_MANIFEST",
    )
    contract.require(
        failure["attempt_record_sha256"] == contract.sha256_id(attempt_raw),
        "FAILURE_ATTEMPT",
    )
    contract.require(
        failure["execution_started_record_sha256"] == contract.sha256_id(started_raw),
        "FAILURE_EXECUTION_STARTED",
    )
    contract.strict_text(failure["error_type"], "FAILURE_ERROR_TYPE", maximum=256)
    contract.require(
        isinstance(failure["message"], str)
        and len(failure["message"].encode("utf-8")) <= 4096
        and "\x00" not in failure["message"],
        "FAILURE_MESSAGE",
    )
    instant_ns(contract.strict_text(failure["failed_at_utc"], "FAILURE_TIME"))
    return failure


def persist_failure_seal(
    *,
    seals: dict[str, Path],
    manifest: dict[str, Any],
    manifest_canonical: bytes,
    attempt_raw: bytes,
    error_type: str,
    message: str,
    output_directory: Path | None,
) -> dict[str, Any] | None:
    """Durably terminalize an armed campaign without replacing an existing terminal."""

    contract.require(
        not (seals["completed"].exists() and seals["failed"].exists()),
        "CAMPAIGN_CONFLICTING_TERMINALS",
    )
    if seals["started"].exists():
        started_value, _ = contract.canonical_document(seals["started"])
        validate_execution_started_seal(
            started_value,
            manifest=manifest,
            manifest_canonical=manifest_canonical,
            attempt_raw=attempt_raw,
        )
    else:
        claim_execution(
            seals,
            manifest=manifest,
            manifest_canonical=manifest_canonical,
            attempt_raw=attempt_raw,
        )
    started_raw = seals["started"].read_bytes()
    if seals["terminal"].exists():
        terminal = recover_terminal_outcome(
            seals,
            manifest=manifest,
            manifest_canonical=manifest_canonical,
            attempt_raw=attempt_raw,
            started_raw=started_raw,
        )
        if terminal["outcome"] == "COMPLETED":
            return None
        existing, _ = contract.canonical_document(seals["failed"])
        return validate_failure_seal(
            existing,
            manifest=manifest,
            manifest_canonical=manifest_canonical,
            attempt_raw=attempt_raw,
            started_raw=started_raw,
        )
    contract.require(
        not seals["completed"].exists() and not seals["failed"].exists(),
        "CAMPAIGN_OUTCOME_WITHOUT_TERMINAL",
    )
    failure = {
        "attempt_record_sha256": contract.sha256_id(attempt_raw),
        "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
        "error_type": str(error_type)[:256] or "UnknownFailure",
        "execution_started_record_sha256": contract.sha256_id(started_raw),
        "failed_at_utc": utc_now(),
        "manifest_sha256": contract.sha256_id(manifest_canonical),
        "message": str(message)[:4096],
        "schema_version": contract.SCHEMA_VERSION,
        "state": "FAILED_NO_RERUN",
        "type_name": FAILURE_SEAL_TYPE,
    }
    validate_failure_seal(
        failure,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_raw,
        started_raw=started_raw,
    )
    durable_terminal_transition(
        seals,
        "failed",
        failure,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_raw,
        started_raw=started_raw,
    )
    if output_directory is not None and output_directory.is_dir():
        failure_artifact = output_directory / "failure.json"
        if not failure_artifact.exists():
            canonical_write(failure_artifact, failure)
    return failure


def record_armed_failure(
    manifest_path: Path,
    *,
    error_type: str,
    message: str,
) -> dict[str, Any] | None:
    """Terminalize wrapper-side failures that occur after the durable arm transition."""

    manifest, manifest_canonical = contract.canonical_document(manifest_path)
    contract.validate_manifest(manifest, executable=True)
    environment = manifest["environment"]
    ledger_directory = Path(str(environment["campaign_ledger_directory"])).resolve()
    contract.require(ledger_directory.is_dir(), "LEDGER_DIRECTORY_MISSING")
    seals = ledger_paths(ledger_directory, str(manifest["diagnostic_campaign_id"]))
    contract.require(seals["attempt"].is_file(), "CAMPAIGN_NOT_ARMED")
    attempt_value, _ = contract.canonical_document(seals["attempt"])
    validate_attempt_identity(
        attempt_value,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
    )
    attempt_raw = seals["attempt"].read_bytes()
    return persist_failure_seal(
        seals=seals,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_raw,
        error_type=error_type,
        message=message,
        output_directory=Path(str(manifest["evidence_directory"])).resolve(),
    )


def recover_terminal_campaign(manifest_path: Path) -> dict[str, Any]:
    """Repair only the derived terminal outcome file; never arm or execute a lane."""

    manifest, manifest_canonical = contract.canonical_document(manifest_path)
    contract.validate_manifest(manifest, executable=True)
    ledger_directory = Path(str(manifest["environment"]["campaign_ledger_directory"])).resolve()
    contract.require(ledger_directory.is_dir(), "LEDGER_DIRECTORY_MISSING")
    contract.require(os.access(ledger_directory, os.W_OK), "LEDGER_DIRECTORY_NOT_WRITABLE")
    seals = ledger_paths(ledger_directory, str(manifest["diagnostic_campaign_id"]))
    contract.require(seals["attempt"].is_file(), "CAMPAIGN_NOT_ARMED")
    contract.require(seals["started"].is_file(), "CAMPAIGN_EXECUTION_NOT_STARTED")
    contract.require(seals["terminal"].is_file(), "CAMPAIGN_TERMINAL_MISSING")
    attempt_value, _ = contract.canonical_document(seals["attempt"])
    validate_attempt_identity(
        attempt_value,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
    )
    attempt_raw = seals["attempt"].read_bytes()
    started_value, _ = contract.canonical_document(seals["started"])
    validate_execution_started_seal(
        started_value,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_raw,
    )
    return recover_terminal_outcome(
        seals,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_raw,
        started_raw=seals["started"].read_bytes(),
    )


def write_success_evidence(
    *,
    output_directory: Path,
    manifest: dict[str, Any],
    manifest_canonical: bytes,
    manifest_receipt: dict[str, object],
    source_receipt: dict[str, object],
    attempt_raw: bytes,
    started_raw: bytes,
    lanes: list[dict[str, Any]],
    classification: str,
    classified_slots: list[dict[str, Any]],
    seals: dict[str, Path],
) -> dict[str, Any]:
    evidence_artifacts = {
        "allocation_manifest": portable_input_record(
            output_directory / "inputs" / "allocation-manifest.json", output_directory
        ),
        "attempt_seal": portable_input_record(
            output_directory / "attempt-seal.json", output_directory
        ),
        "execution_started_seal": portable_input_record(
            output_directory / "execution-started-seal.json", output_directory
        ),
        "environment": portable_input_record(
            output_directory / "environment.json", output_directory
        ),
        "frozen_manifest": portable_input_record(
            output_directory / "inputs" / "frozen-manifest.json", output_directory
        ),
        "host_receipt": portable_input_record(
            output_directory / "host" / "host-receipt.json", output_directory
        ),
        "host_telemetry": portable_input_record(
            output_directory / "host" / "host-telemetry.json", output_directory
        ),
        "lanes_complete": portable_input_record(
            output_directory / "lanes-complete.json", output_directory
        ),
        "preflight_receipt": portable_input_record(
            output_directory / "inputs" / "preflight-receipt.json", output_directory
        ),
    }
    evidence = {
        "artifacts": evidence_artifacts,
        "assembler_eligible": False,
        "authority": "DIAGNOSTIC_ONLY",
        "benchmark_result_qc": None,
        "campaign_classification": classification,
        "classified_missed_slots": classified_slots,
        "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
        "ended_at_utc": utc_now(),
        "execution_class": contract.EXECUTION_CLASS,
        "external_ledger": {
            "attempt_record_sha256": contract.sha256_id(attempt_raw),
            "completion_record_required": True,
            "execution_started_record_sha256": contract.sha256_id(started_raw),
            "terminal_record_required": True,
        },
        "feature010_go": False,
        "gate_a_qualified": False,
        "gate_b_qualified": False,
        "gate_c_qualified": False,
        "gate_d_qualified": False,
        "lanes": lanes,
        "manifest_checkout": manifest_receipt,
        "manifest_sha256": contract.sha256_id(manifest_canonical),
        "official_comparison": False,
        "profile_selection_allowed": False,
        "schema_version": contract.SCHEMA_VERSION,
        "selected_profile": None,
        "source": manifest["source"],
        "source_checkout": source_receipt,
        "status": "SEALED",
        "type_name": contract.EVIDENCE_TYPE,
    }
    canonical_write(output_directory / "diagnostic-evidence.json", evidence)
    evidence_raw = (output_directory / "diagnostic-evidence.json").read_bytes()
    completion = {
        "attempt_record_sha256": contract.sha256_id(attempt_raw),
        "completed_at_utc": utc_now(),
        "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
        "evidence_sha256": contract.sha256_id(evidence_raw),
        "execution_started_record_sha256": contract.sha256_id(started_raw),
        "manifest_sha256": contract.sha256_id(manifest_canonical),
        "schema_version": contract.SCHEMA_VERSION,
        "state": "COMPLETED_ONE_SHOT_NO_RERUN",
        "type_name": COMPLETION_SEAL_TYPE,
    }
    durable_terminal_transition(
        seals,
        "completed",
        completion,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_raw,
        started_raw=started_raw,
    )
    return evidence


def _run_campaign(
    manifest_path: Path,
    manifest_checkout: Path,
    source_root: Path,
    output_directory: Path,
    preflight_receipt_path: Path,
) -> dict[str, Any]:
    manifest, manifest_canonical = contract.canonical_document(manifest_path)
    contract.validate_manifest(manifest, executable=True)
    expected_output = Path(str(manifest["evidence_directory"])).resolve()
    contract.require(output_directory.resolve() == expected_output, "OUTPUT_DIRECTORY_MISMATCH")
    contract.require(not output_directory.exists(), "OUTPUT_DIRECTORY_MUST_BE_FRESH")
    contract.require(output_directory.parent.is_dir(), "OUTPUT_PARENT_MISSING")
    preflight_receipt_path = validate_preflight_receipt_location(preflight_receipt_path, manifest)
    preflight_value, _ = contract.canonical_document(preflight_receipt_path)
    preflight_identity = contract.exact_object(
        preflight_value, PREFLIGHT_RECEIPT_FIELDS, "PREFLIGHT_RECEIPT_FIELDS"
    )
    preflight_raw = preflight_receipt_path.read_bytes()
    ledger_directory = Path(str(manifest["environment"]["campaign_ledger_directory"])).resolve()
    contract.require(ledger_directory.is_dir(), "LEDGER_DIRECTORY_MISSING")
    contract.require(os.access(ledger_directory, os.W_OK), "LEDGER_DIRECTORY_NOT_WRITABLE")
    try:
        ledger_directory.relative_to(output_directory.resolve())
    except ValueError:
        pass
    else:
        raise contract.DiagnosticError("LEDGER_INSIDE_EVIDENCE_DIRECTORY")
    try:
        output_directory.resolve().relative_to(ledger_directory)
    except ValueError:
        pass
    else:
        raise contract.DiagnosticError("EVIDENCE_INSIDE_LEDGER_DIRECTORY")
    seals = ledger_paths(ledger_directory, str(manifest["diagnostic_campaign_id"]))
    contract.require(seals["attempt"].is_file(), "CAMPAIGN_NOT_ARMED")
    attempt_value, _ = contract.canonical_document(seals["attempt"])
    validate_attempt_seal(
        attempt_value,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        preflight=preflight_identity,
        preflight_raw=preflight_raw,
    )
    attempt_raw = seals["attempt"].read_bytes()
    if seals["terminal"].exists():
        contract.require(seals["started"].is_file(), "CAMPAIGN_TERMINAL_WITHOUT_EXECUTION_START")
        started_value, _ = contract.canonical_document(seals["started"])
        validate_execution_started_seal(
            started_value,
            manifest=manifest,
            manifest_canonical=manifest_canonical,
            attempt_raw=attempt_raw,
        )
        recover_terminal_outcome(
            seals,
            manifest=manifest,
            manifest_canonical=manifest_canonical,
            attempt_raw=attempt_raw,
            started_raw=seals["started"].read_bytes(),
        )
        raise contract.DiagnosticError("CAMPAIGN_ALREADY_TERMINAL")
    contract.require(
        not seals["completed"].exists() and not seals["failed"].exists(),
        "CAMPAIGN_OUTCOME_WITHOUT_TERMINAL",
    )
    claim_execution(
        seals,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_raw,
    )
    started_raw = seals["started"].read_bytes()

    try:
        contract.require(os.access(output_directory.parent, os.W_OK), "OUTPUT_PARENT_NOT_WRITABLE")
        contract.require(mount_is_read_only(source_root), "PREFLIGHT_SOURCE_NOT_READ_ONLY")
        contract.require(mount_is_read_only(manifest_checkout), "PREFLIGHT_MANIFEST_NOT_READ_ONLY")
        allocation = contract.load_and_verify_allocation(
            manifest["environment"]["allocation_manifest"], manifest
        )
        prepared_lanes = prepare_lanes(
            manifest,
            allocation,
            source_root=source_root.resolve(),
            evidence_root=output_directory.resolve(),
        )
        preflight = validate_preflight_receipt(
            preflight_value,
            manifest=manifest,
            manifest_canonical=manifest_canonical,
            source_root=source_root,
            manifest_checkout=manifest_checkout,
            allocation=allocation,
        )
        source_receipt = preflight["source_checkout"]
        manifest_receipt = preflight["manifest_checkout"]
        host_receipt_path = Path(str(manifest["environment"]["host_receipt_path"]))
        host_receipt, host_receipt_raw = load_host_receipt(host_receipt_path, manifest, allocation)
        host_telemetry_path = Path(str(manifest["environment"]["host_telemetry_path"]))
        contract.require(not host_telemetry_path.exists(), "HOST_TELEMETRY_MUST_BE_FRESH")
        contract.require(host_telemetry_path.parent.is_dir(), "HOST_TELEMETRY_PARENT_MISSING")
        captured_environment = environment_snapshot(manifest, allocation, host_receipt)
        captured_environment["allocation_preflight"] = preflight["allocation_preflight"]
        verify_live_allocation(allocation, captured_environment)

        schedule = manifest["schedule"]
        lanes: list[dict[str, Any]] = []
        output_directory.mkdir(parents=False, exist_ok=False)
        durable_copy_bytes(output_directory / "attempt-seal.json", attempt_raw)
        durable_copy_bytes(output_directory / "execution-started-seal.json", started_raw)
        canonical_write(output_directory / "environment.json", captured_environment)
        durable_copy_bytes(
            output_directory / "inputs" / "frozen-manifest.json", manifest_canonical + b"\n"
        )
        durable_copy_bytes(output_directory / "inputs" / "preflight-receipt.json", preflight_raw)
        allocation_raw = Path(
            str(manifest["environment"]["allocation_manifest"]["path"])
        ).read_bytes()
        durable_copy_bytes(output_directory / "inputs" / "allocation-manifest.json", allocation_raw)
        durable_copy_bytes(output_directory / "host" / "host-receipt.json", host_receipt_raw)
        for prepared in prepared_lanes:
            lanes.append(
                execute_lane(
                    prepared,
                    source_root=source_root.resolve(),
                    duration=schedule["duration_seconds_per_lane"],
                    sampling_interval_ms=manifest["environment"]["sampling_interval_ms"],
                    environment_snapshot_value=captured_environment,
                    expected_processors=allocation["resources"]["available_processors"],
                    evidence_root=output_directory,
                    host_telemetry=pending_host_telemetry(),
                )
            )
        handshake = {
            "capture_sha256": contract.sha256_id(
                contract.canonical_bytes(lane_capture_binding(lanes))
            ),
            "completed_at_utc": utc_now(),
            "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
            "profile_order": contract.PROFILE_ORDER,
            "receipt_nonce": manifest["environment"]["host_receipt_nonce"],
            "schema_version": contract.SCHEMA_VERSION,
            "type_name": LANES_COMPLETE_TYPE,
        }
        canonical_write(output_directory / "lanes-complete.json", handshake)
        handshake_raw = (output_directory / "lanes-complete.json").read_bytes()
        host_telemetry, host_telemetry_raw = load_host_telemetry(
            host_telemetry_path,
            manifest,
            lanes_complete_sha256=contract.sha256_id(handshake_raw),
            wait_seconds=manifest["environment"]["host_telemetry_wait_seconds"],
        )
        contract.require(
            instant_ns(host_telemetry["capture_started_at_utc"])
            <= instant_ns(host_receipt["collected_at_utc"])
            <= instant_ns(host_telemetry["capture_ended_at_utc"]),
            "HOST_RECEIPT_CAPTURE_INTERVAL",
        )
        durable_copy_bytes(output_directory / "host" / "host-telemetry.json", host_telemetry_raw)
        for lane, prepared in zip(lanes, prepared_lanes, strict=True):
            recompute_lane_missed_slots(
                lane,
                evidence_root=output_directory,
                environment=captured_environment,
                host_telemetry=host_telemetry,
                target_executable=str(Path(prepared.argv[0]).resolve(strict=True)),
            )
        classification, classified_slots = contract.classify_campaign(lanes)
        return write_success_evidence(
            output_directory=output_directory,
            manifest=manifest,
            manifest_canonical=manifest_canonical,
            manifest_receipt=manifest_receipt,
            source_receipt=source_receipt,
            attempt_raw=attempt_raw,
            started_raw=started_raw,
            lanes=lanes,
            classification=classification,
            classified_slots=classified_slots,
            seals=seals,
        )
    except BaseException as error:
        failure = {
            "attempt_record_sha256": contract.sha256_id(attempt_raw),
            "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
            "error_type": type(error).__name__,
            "execution_started_record_sha256": contract.sha256_id(started_raw),
            "failed_at_utc": utc_now(),
            "manifest_sha256": contract.sha256_id(manifest_canonical),
            "message": str(error)[:4096],
            "schema_version": contract.SCHEMA_VERSION,
            "state": "FAILED_NO_RERUN",
            "type_name": FAILURE_SEAL_TYPE,
        }
        if not seals["terminal"].exists():
            try:
                durable_terminal_transition(
                    seals,
                    "failed",
                    failure,
                    manifest=manifest,
                    manifest_canonical=manifest_canonical,
                    attempt_raw=attempt_raw,
                    started_raw=started_raw,
                )
            except BaseException as seal_error:
                error.add_note(f"terminal failure seal could not be written: {seal_error}")
        if (
            seals["failed"].is_file()
            and output_directory.is_dir()
            and not (output_directory / "failure.json").exists()
        ):
            canonical_write(output_directory / "failure.json", failure)
        raise


def run_campaign(
    manifest_path: Path,
    manifest_checkout: Path,
    source_root: Path,
    output_directory: Path,
    preflight_receipt_path: Path,
) -> dict[str, Any]:
    """Run an armed campaign and terminalize every post-arm failure."""

    try:
        return _run_campaign(
            manifest_path,
            manifest_checkout,
            source_root,
            output_directory,
            preflight_receipt_path,
        )
    except BaseException as error:
        if isinstance(error, contract.DiagnosticError) and str(error) in {
            "CAMPAIGN_ALREADY_TERMINAL",
            "CAMPAIGN_EXECUTION_ALREADY_STARTED",
        }:
            raise
        try:
            record_armed_failure(
                manifest_path,
                error_type=type(error).__name__,
                message=str(error),
            )
        except BaseException as seal_error:
            error.add_note(f"post-arm terminal failure seal could not be written: {seal_error}")
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--manifest-checkout", type=Path)
    parser.add_argument("--source-checkout", type=Path)
    parser.add_argument("--preflight-receipt", type=Path)
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--arm-only", action="store_true")
    parser.add_argument("--fail-armed", action="store_true")
    parser.add_argument("--recover-terminal", action="store_true")
    parser.add_argument("--failure-message")
    parser.add_argument("--output-directory", type=Path)
    arguments = parser.parse_args()
    try:
        mode_count = sum(
            int(value)
            for value in (
                arguments.preflight_only,
                arguments.arm_only,
                arguments.fail_armed,
                arguments.recover_terminal,
            )
        )
        contract.require(mode_count <= 1, "RUNNER_MODE_CONFLICT")
        if arguments.recover_terminal:
            contract.require(arguments.output_directory is None, "RECOVERY_OUTPUT_FORBIDDEN")
            contract.require(
                arguments.failure_message is None, "RECOVERY_FAILURE_MESSAGE_FORBIDDEN"
            )
            terminal = recover_terminal_campaign(arguments.manifest.resolve())
            print(f"sidecar diagnostic terminal recovered: outcome={terminal['outcome']}")
            return 0
        contract.require(arguments.manifest_checkout is not None, "MANIFEST_CHECKOUT_REQUIRED")
        contract.require(arguments.source_checkout is not None, "SOURCE_CHECKOUT_REQUIRED")
        contract.require(arguments.preflight_receipt is not None, "PREFLIGHT_RECEIPT_REQUIRED")
        manifest_checkout = arguments.manifest_checkout.resolve()
        source_checkout = arguments.source_checkout.resolve()
        preflight_receipt = arguments.preflight_receipt.resolve()
        if arguments.preflight_only:
            contract.require(arguments.output_directory is None, "PREFLIGHT_OUTPUT_FORBIDDEN")
            preflight_campaign(
                arguments.manifest.resolve(),
                manifest_checkout,
                source_checkout,
                preflight_receipt,
            )
            print("sidecar diagnostic preflight passed without starting a campaign")
            return 0
        if arguments.arm_only:
            contract.require(arguments.output_directory is None, "ARM_OUTPUT_FORBIDDEN")
            arm_campaign(
                arguments.manifest.resolve(),
                manifest_checkout,
                source_checkout,
                preflight_receipt.resolve(strict=True),
            )
            print("sidecar diagnostic campaign armed; the one-shot identity is now consumed")
            return 0
        if arguments.fail_armed:
            contract.require(arguments.output_directory is None, "FAIL_ARMED_OUTPUT_FORBIDDEN")
            failure_message = contract.strict_text(
                arguments.failure_message, "FAIL_ARMED_MESSAGE", maximum=4096
            )
            record_armed_failure(
                arguments.manifest.resolve(),
                error_type="HostWrapperFailure",
                message=failure_message,
            )
            print("sidecar diagnostic campaign sealed failed; the one-shot identity cannot rerun")
            return 0
        contract.require(arguments.failure_message is None, "FAILURE_MESSAGE_WITHOUT_FAIL_ARMED")
        contract.require(arguments.output_directory is not None, "OUTPUT_DIRECTORY_REQUIRED")
        evidence = run_campaign(
            arguments.manifest.resolve(),
            manifest_checkout,
            source_checkout,
            arguments.output_directory.resolve(),
            preflight_receipt.resolve(strict=True),
        )
    except (
        OSError,
        UnicodeError,
        ValueError,
        subprocess.SubprocessError,
        contract.DiagnosticError,
    ) as error:
        print(f"sidecar diagnostic failed: {error}")
        return 1
    print(
        "sealed non-qualifying diagnostic: "
        f"classification={evidence['campaign_classification']} selected_profile=null"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
