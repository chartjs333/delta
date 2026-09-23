#!/usr/bin/env python3
"""Fail-closed contracts for the one-shot PR50 sidecar diagnostic campaign.

The diagnostic is deliberately outside the Feature 010 comparison assembler.  It
may explain a qualification-environment stall, but it cannot qualify a profile,
select a profile, or change a benchmark gate.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Final

SCHEMA_VERSION: Final = "1.1.0"
MANIFEST_TYPE: Final = "FEATURE010_SIDECAR_DIAGNOSTIC_MANIFEST"
EVIDENCE_TYPE: Final = "FEATURE010_SIDECAR_DIAGNOSTIC_EVIDENCE"
ALLOCATION_TYPE: Final = "FEATURE010_SIDECAR_DIAGNOSTIC_ALLOCATION"
BUILD_PROVENANCE_TYPE: Final = "FEATURE010_SIDECAR_DIAGNOSTIC_BUILD_PROVENANCE"
HOST_RECEIPT_TYPE: Final = "FEATURE010_SIDECAR_DIAGNOSTIC_HOST_RECEIPT"
HOST_TELEMETRY_TYPE: Final = "FEATURE010_SIDECAR_DIAGNOSTIC_HOST_TELEMETRY"
EXECUTION_CLASS: Final = "NON_QUALIFYING_DIAGNOSTIC_ONLY"
FROZEN_STATE: Final = "FROZEN_EXECUTABLE"
EXAMPLE_STATE: Final = "EXAMPLE_NOT_EXECUTABLE"
PROFILE_ORDER: Final = ["EMBEDDED_FFM", "ISOLATED_SIDECAR"]
OFFER_RATE: Final = 100
WARMUP_OPERATIONS: Final = 1_000
SOURCE_REPOSITORY: Final = "https://github.com/chartjs333/delta.git"
CONTENT_ID: Final = re.compile(r"sha256:[0-9a-f]{64}\Z")
GIT_OBJECT: Final = re.compile(r"[0-9a-f]{40}\Z")
CAMPAIGN_ID: Final = re.compile(r"[a-z0-9][a-z0-9._-]{7,127}\Z")

PER_MISS_CLASSIFICATIONS: Final = {
    "ENVIRONMENT_INVALID",
    "GENUINE_RUNTIME_DEMAND_INDICATOR",
    "HARNESS_OR_TIMER_DEFECT",
    "INCONCLUSIVE",
}
CAMPAIGN_CLASSIFICATIONS: Final = PER_MISS_CLASSIFICATIONS | {"NO_MISSED_SLOTS_OBSERVED"}

MANDATORY_COLLECTORS: Final = [
    "SCHEDULED_ACTUAL_AND_LATENESS_NS",
    "PROCESS_AND_THREAD_CPU_TIME_DELTAS",
    "CGROUP_CPU_STAT",
    "CPU_PSI",
    "IO_PSI",
    "SCHEDSTAT_OR_RUN_QUEUE",
    "WAL_AND_FSYNC_LATENCY",
    "CPUSET_QUOTA_PROCESSORS_MEMORY_CONTAINER_RUNTIME",
    "JAVA_JFR_GC_SAFEPOINT_COMPILER",
]
OPTIONAL_HOST_COLLECTORS: Final = [
    "DOCKER_DESKTOP_AND_WSL_PAUSE_RESTART_SUSPEND",
    "WINDOWS_WHEA_STORAGE_RESET_THERMAL_POWER",
]

AUTHORITY_FIELDS: Final = {
    "assembler_eligible",
    "benchmark_result_qc",
    "execution_class",
    "feature010_go",
    "gate_a_qualified",
    "gate_b_qualified",
    "gate_c_qualified",
    "gate_d_qualified",
    "official_comparison",
    "profile_selection_allowed",
    "selected_profile",
}
SOURCE_FIELDS: Final = {"commit", "repository", "tree"}
SCHEDULE_FIELDS: Final = {
    "duration_seconds_per_lane",
    "lane_order",
    "late_offer_policy",
    "offers_per_second",
    "overlap_policy",
    "warmup_operations",
}
FILE_FIELDS: Final = {"path", "sha256", "size_bytes"}
ENVIRONMENT_FIELDS: Final = {
    "allocation_manifest",
    "allocation_root",
    "campaign_ledger_directory",
    "container_image_digest",
    "container_runtime",
    "host_collector_sha256",
    "host_receipt_nonce",
    "host_receipt_path",
    "host_telemetry_path",
    "host_telemetry_wait_seconds",
    "mandatory_collectors",
    "optional_host_collectors",
    "sampling_interval_ms",
}
LANE_FIELDS: Final = {
    "argv",
    "environment",
    "java_involved",
    "jfr_events",
    "profile_id",
    "strace_fsync",
    "working_directory",
}
MANIFEST_FIELDS: Final = {
    "authority",
    "diagnostic_campaign_id",
    "environment",
    "evidence_directory",
    "lanes",
    "manifest_state",
    "schedule",
    "schema_version",
    "source",
    "type_name",
}
ALLOCATION_FIELDS: Final = {
    "artifacts",
    "container",
    "jdk_tree",
    "resources",
    "schema_version",
    "source",
    "type_name",
}
ALLOCATION_ARTIFACT_IDS: Final = [
    "BUILD_PROVENANCE_RECEIPT",
    "CANONICAL_CORPUS",
    "JAVA_CLASSES_JAR",
    "JAVA_EXECUTABLE",
    "JFR_EXECUTABLE",
    "NATIVE_LIBRARY",
    "SIDECAR_EXECUTABLE",
    "STRACE_EXECUTABLE",
]
BUILD_OUTPUT_IDS: Final = ["JAVA_CLASSES_JAR", "NATIVE_LIBRARY", "SIDECAR_EXECUTABLE"]
INVOCATION_FIELDS: Final = {"argv", "environment", "environment_mode", "working_directory"}
PROCESS_RECEIPT_FIELDS: Final = INVOCATION_FIELDS | {
    "exit_code",
    "stderr_sha256",
    "stdout_sha256",
}
LANE_ENVIRONMENT_TEMPLATE: Final = {
    "HOME": "/tmp",
    "JAVA_HOME": "{ALLOCATION_ROOT}/jdk",
    "LANG": "C.UTF-8",
    "LANGUAGE": "C",
    "LC_ALL": "C.UTF-8",
    "PATH": "{ALLOCATION_ROOT}/jdk/bin:/usr/bin:/bin",
    "TMPDIR": "/tmp",
    "TZ": "UTC",
}


class DiagnosticError(RuntimeError):
    """Stable fail-closed diagnostic contract error."""


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise DiagnosticError(f"{code}:{detail}" if detail else code)


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


def directory_inventory(root: Path) -> dict[str, object]:
    """Return a canonical content/type/mode inventory for an immutable tool tree."""

    resolved_root = root.resolve(strict=True)
    require(resolved_root.is_dir(), "TREE_INVENTORY_ROOT", str(root))
    entries: list[dict[str, object]] = []
    total_size = 0
    for path in sorted(
        resolved_root.rglob("*"), key=lambda item: item.relative_to(resolved_root).as_posix()
    ):
        relative = path.relative_to(resolved_root).as_posix()
        metadata = path.lstat()
        mode = stat.S_IMODE(metadata.st_mode)
        if path.is_symlink():
            target = os.readlink(path)
            entries.append({"kind": "SYMLINK", "mode": mode, "path": relative, "target": target})
        elif path.is_dir():
            entries.append({"kind": "DIRECTORY", "mode": mode, "path": relative})
        elif path.is_file():
            payload = path.read_bytes()
            total_size += len(payload)
            entries.append(
                {
                    "kind": "FILE",
                    "mode": mode,
                    "path": relative,
                    "sha256": sha256_id(payload),
                    "size_bytes": len(payload),
                }
            )
        else:
            raise DiagnosticError(f"TREE_INVENTORY_SPECIAL_FILE:{path}")
    require(entries, "TREE_INVENTORY_EMPTY", str(root))
    return {
        "algorithm": "CANONICAL_PATH_KIND_MODE_CONTENT_V1",
        "entry_count": len(entries),
        "sha256": sha256_id(canonical_bytes(entries)),
        "total_size_bytes": total_size,
    }


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
        raise DiagnosticError(f"JSON_INVALID:{path}") from error
    require(isinstance(value, dict), "JSON_OBJECT_REQUIRED", str(path))
    encoded = canonical_bytes(value)
    require(raw in {encoded, encoded + b"\n"}, "JSON_NOT_CANONICAL", str(path))
    return value, encoded


def exact_object(value: object, fields: set[str], code: str) -> dict[str, Any]:
    require(isinstance(value, dict) and set(value) == fields, code)
    return value


def strict_text(value: object, code: str, *, maximum: int = 4096) -> str:
    require(isinstance(value, str) and value != "", code)
    encoded = value.encode("utf-8")
    require(len(encoded) <= maximum and "\x00" not in value, code)
    return value


def strict_int(value: object, code: str, *, minimum: int = 0, maximum: int = 2**63 - 1) -> int:
    require(type(value) is int and minimum <= value <= maximum, code)
    return int(value)


def content_id(value: object, code: str) -> str:
    require(isinstance(value, str) and CONTENT_ID.fullmatch(value) is not None, code)
    return value


def absolute_contract_path(value: str) -> bool:
    return (
        Path(value).is_absolute()
        or PurePosixPath(value).is_absolute()
        or PureWindowsPath(value).is_absolute()
    )


def artifact_record(value: object, code: str) -> dict[str, Any]:
    record = exact_object(value, FILE_FIELDS, f"{code}_FIELDS")
    path = strict_text(record["path"], f"{code}_PATH")
    require(absolute_contract_path(path), f"{code}_PATH_ABSOLUTE")
    content_id(record["sha256"], f"{code}_SHA256")
    strict_int(record["size_bytes"], f"{code}_SIZE", minimum=1)
    return record


def expected_authority() -> dict[str, object]:
    return {
        "assembler_eligible": False,
        "benchmark_result_qc": None,
        "execution_class": EXECUTION_CLASS,
        "feature010_go": False,
        "gate_a_qualified": False,
        "gate_b_qualified": False,
        "gate_c_qualified": False,
        "gate_d_qualified": False,
        "official_comparison": False,
        "profile_selection_allowed": False,
        "selected_profile": None,
    }


def invocation_record(
    argv: list[str] | tuple[str, ...],
    *,
    environment: dict[str, str],
    working_directory: Path,
) -> dict[str, object]:
    """Describe one no-shell subprocess with a full replacement environment."""

    resolved_cwd = working_directory.resolve(strict=True)
    require(resolved_cwd.is_dir(), "INVOCATION_WORKING_DIRECTORY")
    arguments = [strict_text(item, "INVOCATION_ARGV_ITEM") for item in argv]
    require(arguments, "INVOCATION_ARGV")
    normalized_environment: dict[str, str] = {}
    for key, item in environment.items():
        normalized_key = strict_text(key, "INVOCATION_ENVIRONMENT_KEY", maximum=128)
        require(normalized_key not in normalized_environment, "INVOCATION_ENVIRONMENT_DUPLICATE")
        normalized_environment[normalized_key] = strict_text(
            item, "INVOCATION_ENVIRONMENT_VALUE", maximum=4096
        )
    return {
        "argv": arguments,
        "environment": normalized_environment,
        "environment_mode": "REPLACE",
        "working_directory": str(resolved_cwd),
    }


def validate_invocation_record(value: object, code: str) -> dict[str, Any]:
    record = exact_object(value, INVOCATION_FIELDS, f"{code}_FIELDS")
    argv = record["argv"]
    require(isinstance(argv, list) and argv, f"{code}_ARGV")
    for item in argv:
        strict_text(item, f"{code}_ARGV_ITEM")
    environment = record["environment"]
    require(isinstance(environment, dict), f"{code}_ENVIRONMENT")
    for key, item in environment.items():
        strict_text(key, f"{code}_ENVIRONMENT_KEY", maximum=128)
        strict_text(item, f"{code}_ENVIRONMENT_VALUE")
    require(record["environment_mode"] == "REPLACE", f"{code}_ENVIRONMENT_MODE")
    working_directory = strict_text(record["working_directory"], f"{code}_WORKING_DIRECTORY")
    require(absolute_contract_path(working_directory), f"{code}_WORKING_DIRECTORY_ABSOLUTE")
    return record


def validate_process_receipt(value: object, code: str) -> dict[str, Any]:
    receipt = exact_object(value, PROCESS_RECEIPT_FIELDS, f"{code}_FIELDS")
    validate_invocation_record(
        {name: receipt[name] for name in INVOCATION_FIELDS}, f"{code}_INVOCATION"
    )
    strict_int(receipt["exit_code"], f"{code}_EXIT_CODE", maximum=2**31 - 1)
    content_id(receipt["stderr_sha256"], f"{code}_STDERR")
    content_id(receipt["stdout_sha256"], f"{code}_STDOUT")
    return receipt


def validate_checkout_receipt(
    value: object, code: str, *, manifest: bool = False
) -> dict[str, Any]:
    fields = {"checkout_root", "commit", "git_invocations", "status_porcelain_sha256", "tree"}
    if manifest:
        fields |= {"manifest_blob", "manifest_relative_path"}
    receipt = exact_object(value, fields, f"{code}_FIELDS")
    checkout_root = strict_text(receipt["checkout_root"], f"{code}_ROOT")
    require(absolute_contract_path(checkout_root), f"{code}_ROOT_ABSOLUTE")
    for name in ("commit", "tree"):
        item = strict_text(receipt[name], f"{code}_{name.upper()}", maximum=40)
        require(GIT_OBJECT.fullmatch(item) is not None, f"{code}_{name.upper()}")
    content_id(receipt["status_porcelain_sha256"], f"{code}_STATUS")
    invocations = receipt["git_invocations"]
    require(isinstance(invocations, list) and invocations, f"{code}_GIT_INVOCATIONS")
    for index, invocation in enumerate(invocations):
        validate_process_receipt(invocation, f"{code}_GIT_{index}")
    if manifest:
        blob = strict_text(receipt["manifest_blob"], f"{code}_MANIFEST_BLOB", maximum=40)
        require(GIT_OBJECT.fullmatch(blob) is not None, f"{code}_MANIFEST_BLOB")
        strict_text(receipt["manifest_relative_path"], f"{code}_MANIFEST_RELATIVE")
    return receipt


def git_replacement_environment() -> dict[str, str]:
    """Return the small, recorded environment allowed to influence Git verification."""

    environment = {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "LANG": "C",
        "LC_ALL": "C",
        "TZ": "UTC",
    }
    if os.name == "nt":
        # CreateProcess and Git for Windows need these OS identities.  They are
        # the only inherited values, are recorded in the receipt, and cannot
        # inject Git/JVM/tool options.
        for canonical, candidates in {
            "COMSPEC": ("COMSPEC", "ComSpec"),
            "SYSTEMROOT": ("SYSTEMROOT", "SystemRoot"),
            "WINDIR": ("WINDIR", "windir"),
        }.items():
            value = next(
                (os.environ.get(name) for name in candidates if os.environ.get(name)), None
            )
            if value is not None:
                environment[canonical] = value
    return environment


def required_option_argument(argv: list[Any], name: str, code_prefix: str) -> str:
    positions = [position for position, item in enumerate(argv) if item == name]
    require(len(positions) == 1, f"{code_prefix}_OPTION_CARDINALITY", name)
    position = positions[0]
    require(position + 1 < len(argv), f"{code_prefix}_OPTION_VALUE", name)
    return str(argv[position + 1])


def validate_manifest(value: object, *, executable: bool = True) -> dict[str, Any]:
    manifest = exact_object(value, MANIFEST_FIELDS, "MANIFEST_FIELDS")
    require(manifest["schema_version"] == SCHEMA_VERSION, "MANIFEST_SCHEMA")
    require(manifest["type_name"] == MANIFEST_TYPE, "MANIFEST_TYPE")
    expected_state = FROZEN_STATE if executable else EXAMPLE_STATE
    require(manifest["manifest_state"] == expected_state, "MANIFEST_STATE")
    campaign_id = strict_text(manifest["diagnostic_campaign_id"], "CAMPAIGN_ID", maximum=128)
    require(CAMPAIGN_ID.fullmatch(campaign_id) is not None, "CAMPAIGN_ID")

    authority = exact_object(manifest["authority"], AUTHORITY_FIELDS, "AUTHORITY_FIELDS")
    require(authority == expected_authority(), "DIAGNOSTIC_AUTHORITY")

    source = exact_object(manifest["source"], SOURCE_FIELDS, "SOURCE_FIELDS")
    require(source["repository"] == SOURCE_REPOSITORY, "SOURCE_REPOSITORY")
    commit = strict_text(source["commit"], "SOURCE_COMMIT", maximum=40)
    tree = strict_text(source["tree"], "SOURCE_TREE", maximum=40)
    require(GIT_OBJECT.fullmatch(commit) is not None, "SOURCE_COMMIT")
    require(GIT_OBJECT.fullmatch(tree) is not None, "SOURCE_TREE")
    if executable:
        require(commit != "0" * 40 and tree != "0" * 40, "SOURCE_PLACEHOLDER_FORBIDDEN")

    schedule = exact_object(manifest["schedule"], SCHEDULE_FIELDS, "SCHEDULE_FIELDS")
    require(schedule["offers_per_second"] == OFFER_RATE, "SCHEDULE_RATE_MUST_REMAIN_100")
    require(schedule["warmup_operations"] == WARMUP_OPERATIONS, "SCHEDULE_WARMUP")
    strict_int(
        schedule["duration_seconds_per_lane"],
        "SCHEDULE_DURATION",
        minimum=1,
        maximum=3_600,
    )
    require(schedule["lane_order"] == PROFILE_ORDER, "SCHEDULE_LANE_ORDER")
    require(schedule["overlap_policy"] == "SEQUENTIAL_NO_OVERLAP", "SCHEDULE_OVERLAP")
    require(
        schedule["late_offer_policy"]
        == "ABSOLUTE_MONOTONIC_DEADLINES_NO_RATE_REDUCTION_NO_CATCHUP_REBASE",
        "SCHEDULE_LATE_OFFER_POLICY",
    )

    evidence_directory = strict_text(
        manifest["evidence_directory"], "EVIDENCE_DIRECTORY", maximum=4096
    )
    require(absolute_contract_path(evidence_directory), "EVIDENCE_DIRECTORY_ABSOLUTE")

    environment = exact_object(manifest["environment"], ENVIRONMENT_FIELDS, "ENVIRONMENT_FIELDS")
    artifact_record(environment["allocation_manifest"], "ALLOCATION_MANIFEST")
    allocation_root = strict_text(environment["allocation_root"], "ALLOCATION_ROOT")
    require(absolute_contract_path(allocation_root), "ALLOCATION_ROOT_ABSOLUTE")
    ledger_directory = strict_text(
        environment["campaign_ledger_directory"], "CAMPAIGN_LEDGER_DIRECTORY"
    )
    require(absolute_contract_path(ledger_directory), "CAMPAIGN_LEDGER_DIRECTORY_ABSOLUTE")
    content_id(environment["container_image_digest"], "CONTAINER_IMAGE_DIGEST")
    runtime = exact_object(
        environment["container_runtime"], {"name", "version"}, "CONTAINER_RUNTIME_FIELDS"
    )
    require(runtime["name"] in {"docker", "podman"}, "CONTAINER_RUNTIME_NAME")
    strict_text(runtime["version"], "CONTAINER_RUNTIME_VERSION", maximum=512)
    require(environment["mandatory_collectors"] == MANDATORY_COLLECTORS, "MANDATORY_COLLECTORS")
    require(
        environment["optional_host_collectors"] == OPTIONAL_HOST_COLLECTORS,
        "OPTIONAL_HOST_COLLECTORS",
    )
    strict_int(environment["sampling_interval_ms"], "SAMPLING_INTERVAL", minimum=1, maximum=100)
    content_id(environment["host_collector_sha256"], "HOST_COLLECTOR_SHA256")
    content_id(environment["host_receipt_nonce"], "HOST_RECEIPT_NONCE")
    for name in ("host_receipt_path", "host_telemetry_path"):
        path = strict_text(environment[name], name.upper())
        require(absolute_contract_path(path), f"{name.upper()}_ABSOLUTE")
    strict_int(
        environment["host_telemetry_wait_seconds"],
        "HOST_TELEMETRY_WAIT_SECONDS",
        minimum=1,
        maximum=600,
    )

    lanes = manifest["lanes"]
    require(isinstance(lanes, list) and len(lanes) == 2, "LANE_COUNT")
    profiles: list[str] = []
    for index, raw_lane in enumerate(lanes):
        lane = exact_object(raw_lane, LANE_FIELDS, f"LANE_{index}_FIELDS")
        profile = strict_text(lane["profile_id"], f"LANE_{index}_PROFILE", maximum=32)
        profiles.append(profile)
        require(lane["java_involved"] is True, f"LANE_{index}_JAVA_REQUIRED")
        argv = lane["argv"]
        require(isinstance(argv, list) and len(argv) >= 2, f"LANE_{index}_ARGV")
        for argument in argv:
            strict_text(argument, f"LANE_{index}_ARGV_ITEM", maximum=4096)
        require(
            any("{ALLOCATION_ROOT}" in argument for argument in argv),
            f"LANE_{index}_ALLOCATION_ROOT_PLACEHOLDER",
        )
        require("{PROFILE_ID}" in argv, f"LANE_{index}_PROFILE_PLACEHOLDER")
        require("{EVENT_LOG}" in argv, f"LANE_{index}_EVENT_LOG_PLACEHOLDER")
        require("{DURATION_SECONDS}" in argv, f"LANE_{index}_DURATION_PLACEHOLDER")
        require("{OFFERS_PER_SECOND}" in argv, f"LANE_{index}_RATE_PLACEHOLDER")
        require("{SOURCE_ROOT}" in argv, f"LANE_{index}_SOURCE_ROOT_PLACEHOLDER")
        require(
            any("{JFR_FILE}" in argument for argument in argv),
            f"LANE_{index}_JFR_FILE_PLACEHOLDER",
        )
        require(
            "io.deltareduce.node.sidecar.SidecarDiagnosticCapture" in argv,
            f"LANE_{index}_DIAGNOSTIC_ENTRYPOINT",
        )
        required_options = {
            "--corpus",
            "--durable-directory",
            "--duration-seconds",
            "--event-log",
            "--offers-per-second",
            "--profile",
            "--source-root",
        }
        require(required_options <= set(argv), f"LANE_{index}_REQUIRED_OPTIONS")

        require("{ALLOCATION_ROOT}" in str(argv[0]), f"LANE_{index}_JAVA_ALLOCATION_PATH")
        require(
            "{ALLOCATION_ROOT}" in required_option_argument(argv, "--corpus", f"LANE_{index}"),
            f"LANE_{index}_CORPUS_ALLOCATION_PATH",
        )
        classpath = required_option_argument(argv, "-cp", f"LANE_{index}")
        require("{ALLOCATION_ROOT}" in classpath, f"LANE_{index}_CLASSPATH_ALLOCATION_PATH")
        if profile == "EMBEDDED_FFM":
            require(
                "--native-library" in argv and "--sidecar-executable" not in argv,
                f"LANE_{index}_PROFILE_ARTIFACT_OPTION",
            )
            require(
                "{ALLOCATION_ROOT}"
                in required_option_argument(argv, "--native-library", f"LANE_{index}"),
                f"LANE_{index}_NATIVE_ALLOCATION_PATH",
            )
        else:
            require(
                "--sidecar-executable" in argv and "--native-library" not in argv,
                f"LANE_{index}_PROFILE_ARTIFACT_OPTION",
            )
            require(
                "{ALLOCATION_ROOT}"
                in required_option_argument(argv, "--sidecar-executable", f"LANE_{index}"),
                f"LANE_{index}_SIDECAR_ALLOCATION_PATH",
            )
        working_directory = strict_text(
            lane["working_directory"], f"LANE_{index}_WORKING_DIRECTORY"
        )
        require(working_directory == "{SOURCE_ROOT}", f"LANE_{index}_WORKING_DIRECTORY")
        lane_environment = lane["environment"]
        require(
            lane_environment == LANE_ENVIRONMENT_TEMPLATE,
            f"LANE_{index}_ENVIRONMENT_REPLACEMENT",
        )
        require(
            lane["jfr_events"]
            == [
                "jdk.GarbageCollection",
                "jdk.GCPhasePause",
                "jdk.SafepointBegin",
                "jdk.SafepointEnd",
                "jdk.Compilation",
                "jdk.CompilerPhase",
            ],
            f"LANE_{index}_JFR_EVENTS",
        )
        strace = exact_object(
            lane["strace_fsync"],
            {"argv_prefix", "unavailable_policy"},
            f"LANE_{index}_STRACE_FIELDS",
        )
        prefix = strace["argv_prefix"]
        require(isinstance(prefix, list) and len(prefix) >= 2, f"LANE_{index}_STRACE_ARGV")
        for argument in prefix:
            strict_text(argument, f"LANE_{index}_STRACE_ARGV_ITEM", maximum=4096)
        require(
            "{ALLOCATION_ROOT}" in str(prefix[0]),
            f"LANE_{index}_STRACE_ALLOCATION_PATH",
        )
        require(
            strace["unavailable_policy"] == "RECORD_NOT_AVAILABLE_NEVER_INFER",
            f"LANE_{index}_STRACE_POLICY",
        )
    require(profiles == PROFILE_ORDER, "LANE_ORDER")
    return manifest


def verify_artifact(record: dict[str, Any]) -> Path:
    path = Path(str(record["path"]))
    require(path.is_file(), "ARTIFACT_MISSING", str(path))
    require(path.stat().st_size == record["size_bytes"], "ARTIFACT_SIZE", str(path))
    require(sha256_id(path.read_bytes()) == record["sha256"], "ARTIFACT_SHA256", str(path))
    return path


def load_and_verify_allocation(record: dict[str, Any], manifest: dict[str, Any]) -> dict[str, Any]:
    path = verify_artifact(record)
    allocation, _ = canonical_document(path)
    exact_object(allocation, ALLOCATION_FIELDS, "ALLOCATION_FIELDS")
    require(allocation["schema_version"] == SCHEMA_VERSION, "ALLOCATION_SCHEMA")
    require(allocation["type_name"] == ALLOCATION_TYPE, "ALLOCATION_TYPE")
    require(allocation["source"] == manifest["source"], "ALLOCATION_SOURCE")
    container = exact_object(
        allocation["container"],
        {"image_digest", "runtime", "runtime_version"},
        "ALLOCATION_CONTAINER_FIELDS",
    )
    environment = manifest["environment"]
    require(container["image_digest"] == environment["container_image_digest"], "ALLOCATION_IMAGE")
    require(container["runtime"] == environment["container_runtime"]["name"], "ALLOCATION_RUNTIME")
    require(
        container["runtime_version"] == environment["container_runtime"]["version"],
        "ALLOCATION_RUNTIME_VERSION",
    )
    resources = exact_object(
        allocation["resources"],
        {
            "available_processors",
            "cgroup_mode",
            "cpu_max",
            "cpuset_cpus_effective",
            "memory_max",
        },
        "ALLOCATION_RESOURCE_FIELDS",
    )
    strict_int(resources["available_processors"], "ALLOCATION_PROCESSORS", minimum=1)
    require(resources["cgroup_mode"] in {"V1", "V2"}, "ALLOCATION_CGROUP_MODE")
    for name in ("cpu_max", "cpuset_cpus_effective", "memory_max"):
        strict_text(resources[name], f"ALLOCATION_{name.upper()}", maximum=512)
    jdk_tree = exact_object(
        allocation["jdk_tree"],
        {"algorithm", "entry_count", "root", "sha256", "total_size_bytes"},
        "ALLOCATION_JDK_TREE_FIELDS",
    )
    jdk_root = strict_text(jdk_tree["root"], "ALLOCATION_JDK_TREE_ROOT")
    require(absolute_contract_path(jdk_root), "ALLOCATION_JDK_TREE_ROOT_ABSOLUTE")
    require(
        jdk_tree["algorithm"] == "CANONICAL_PATH_KIND_MODE_CONTENT_V1",
        "ALLOCATION_JDK_TREE_ALGORITHM",
    )
    strict_int(jdk_tree["entry_count"], "ALLOCATION_JDK_TREE_ENTRY_COUNT", minimum=1)
    strict_int(jdk_tree["total_size_bytes"], "ALLOCATION_JDK_TREE_SIZE", minimum=1)
    content_id(jdk_tree["sha256"], "ALLOCATION_JDK_TREE_SHA256")
    artifacts = allocation["artifacts"]
    require(isinstance(artifacts, list), "ALLOCATION_ARTIFACTS")
    allocation_root = Path(str(environment["allocation_root"]))
    require(allocation_root.is_dir(), "ALLOCATION_ROOT_MISSING", str(allocation_root))
    resolved_root = allocation_root.resolve(strict=True)
    ids: list[str] = []
    indexed: dict[str, dict[str, Any]] = {}
    for raw in artifacts:
        item = exact_object(raw, FILE_FIELDS | {"artifact_id"}, "ALLOCATION_ARTIFACT_FIELDS")
        identifier = strict_text(item["artifact_id"], "ALLOCATION_ARTIFACT_ID", maximum=64)
        ids.append(identifier)
        artifact_path = verify_artifact({name: item[name] for name in FILE_FIELDS})
        try:
            artifact_path.resolve(strict=True).relative_to(resolved_root)
        except ValueError as error:
            raise DiagnosticError(f"ALLOCATION_ARTIFACT_OUTSIDE_ROOT:{artifact_path}") from error
        indexed[identifier] = item
    require(ids == ALLOCATION_ARTIFACT_IDS, "ALLOCATION_ARTIFACT_ORDER")
    java_path = Path(str(indexed["JAVA_EXECUTABLE"]["path"]))
    jfr_path = Path(str(indexed["JFR_EXECUTABLE"]["path"]))
    expected_jfr_name = "jfr.exe" if java_path.name.lower() == "java.exe" else "jfr"
    require(
        jfr_path == java_path.with_name(expected_jfr_name),
        "ALLOCATION_JFR_NOT_JAVA_SIBLING",
    )
    expected_jdk_root = java_path.parent.parent.resolve(strict=True)
    require(expected_jdk_root == Path(jdk_root).resolve(strict=True), "ALLOCATION_JDK_TREE_ROOT")
    observed_jdk = directory_inventory(expected_jdk_root)
    require(
        {name: jdk_tree[name] for name in observed_jdk} == observed_jdk,
        "ALLOCATION_JDK_TREE_MISMATCH",
    )

    provenance_path = Path(str(indexed["BUILD_PROVENANCE_RECEIPT"]["path"]))
    provenance, _ = canonical_document(provenance_path)
    exact_object(
        provenance,
        {
            "builder_container_image_digest",
            "execution",
            "invocation",
            "invocation_sha256",
            "outputs",
            "schema_version",
            "source",
            "source_checkout",
            "type_name",
        },
        "BUILD_PROVENANCE_FIELDS",
    )
    require(provenance["schema_version"] == SCHEMA_VERSION, "BUILD_PROVENANCE_SCHEMA")
    require(provenance["type_name"] == BUILD_PROVENANCE_TYPE, "BUILD_PROVENANCE_TYPE")
    require(provenance["source"] == allocation["source"], "BUILD_PROVENANCE_SOURCE")
    build_source_receipt = validate_checkout_receipt(
        provenance["source_checkout"], "BUILD_PROVENANCE_SOURCE_CHECKOUT"
    )
    require(
        build_source_receipt["commit"] == allocation["source"]["commit"]
        and build_source_receipt["tree"] == allocation["source"]["tree"],
        "BUILD_PROVENANCE_SOURCE_CHECKOUT_IDENTITY",
    )
    require(
        provenance["builder_container_image_digest"] == container["image_digest"],
        "BUILD_PROVENANCE_IMAGE",
    )
    invocation = exact_object(
        provenance["invocation"],
        {"argv", "environment", "environment_mode", "working_directory"},
        "BUILD_PROVENANCE_INVOCATION_FIELDS",
    )
    require(
        isinstance(invocation["argv"], list) and invocation["argv"],
        "BUILD_PROVENANCE_ARGV",
    )
    for argument in invocation["argv"]:
        strict_text(argument, "BUILD_PROVENANCE_ARGV_ITEM")
    require(isinstance(invocation["environment"], dict), "BUILD_PROVENANCE_ENVIRONMENT")
    for key, item in invocation["environment"].items():
        strict_text(key, "BUILD_PROVENANCE_ENVIRONMENT_KEY")
        strict_text(item, "BUILD_PROVENANCE_ENVIRONMENT_VALUE")
    require(
        invocation["environment_mode"] == "REPLACE",
        "BUILD_PROVENANCE_ENVIRONMENT_MODE",
    )
    working_directory = strict_text(
        invocation["working_directory"], "BUILD_PROVENANCE_WORKING_DIRECTORY"
    )
    require(
        absolute_contract_path(working_directory),
        "BUILD_PROVENANCE_WORKING_DIRECTORY_ABSOLUTE",
    )
    invocation_sha256 = content_id(provenance["invocation_sha256"], "BUILD_PROVENANCE_INVOCATION")
    require(
        invocation_sha256 == sha256_id(canonical_bytes(invocation)),
        "BUILD_PROVENANCE_INVOCATION_MISMATCH",
    )
    execution = exact_object(
        provenance["execution"],
        {"exit_code", "stderr", "stdout"},
        "BUILD_PROVENANCE_EXECUTION_FIELDS",
    )
    require(execution["exit_code"] == 0, "BUILD_PROVENANCE_EXECUTION_EXIT")
    for stream_name in ("stderr", "stdout"):
        stream = exact_object(
            execution[stream_name], FILE_FIELDS, "BUILD_PROVENANCE_EXECUTION_STREAM_FIELDS"
        )
        stream_path = strict_text(stream["path"], f"BUILD_PROVENANCE_{stream_name.upper()}_PATH")
        require(
            absolute_contract_path(stream_path),
            f"BUILD_PROVENANCE_{stream_name.upper()}_PATH_ABSOLUTE",
        )
        content_id(stream["sha256"], f"BUILD_PROVENANCE_{stream_name.upper()}_SHA256")
        strict_int(stream["size_bytes"], f"BUILD_PROVENANCE_{stream_name.upper()}_SIZE", minimum=0)
        verified_stream = verify_artifact(stream)
        try:
            verified_stream.resolve(strict=True).relative_to(resolved_root)
        except ValueError as error:
            raise DiagnosticError(
                f"BUILD_PROVENANCE_{stream_name.upper()}_OUTSIDE_ROOT:{verified_stream}"
            ) from error
    outputs = provenance["outputs"]
    require(isinstance(outputs, list) and len(outputs) == len(BUILD_OUTPUT_IDS), "BUILD_OUTPUTS")
    for identifier, raw_output in zip(BUILD_OUTPUT_IDS, outputs, strict=True):
        output = exact_object(raw_output, {"artifact_id", "sha256"}, "BUILD_OUTPUT_FIELDS")
        require(output["artifact_id"] == identifier, "BUILD_OUTPUT_ID", identifier)
        require(
            output["sha256"] == indexed[identifier]["sha256"], "BUILD_OUTPUT_SHA256", identifier
        )
    return allocation


def git_checkout_receipt(root: Path) -> tuple[dict[str, object], Any]:
    root = root.resolve(strict=True)
    environment = git_replacement_environment()
    executable_text = shutil.which("git")
    require(executable_text is not None, "SOURCE_GIT_EXECUTABLE_MISSING")
    executable = Path(executable_text).resolve(strict=True)
    invocations: list[dict[str, object]] = []

    def git(*arguments: str) -> str:
        invocation = invocation_record(
            [str(executable), "-C", str(root), *arguments],
            environment=environment,
            working_directory=root,
        )
        process = subprocess.run(
            invocation["argv"],
            check=False,
            capture_output=True,
            cwd=invocation["working_directory"],
            env=invocation["environment"],
            timeout=30,
        )
        invocations.append(
            {
                **invocation,
                "exit_code": process.returncode,
                "stderr_sha256": sha256_id(process.stderr),
                "stdout_sha256": sha256_id(process.stdout),
            }
        )
        require(process.returncode == 0, "SOURCE_GIT_FAILED", " ".join(arguments))
        try:
            return process.stdout.decode("utf-8", errors="strict").strip()
        except UnicodeDecodeError as error:
            raise DiagnosticError("SOURCE_GIT_OUTPUT_NOT_UTF8") from error

    require(
        Path(git("rev-parse", "--show-toplevel")).resolve(strict=True) == root,
        "GIT_ROOT_MISMATCH",
    )
    status = git("status", "--porcelain=v1", "--untracked-files=all", "--ignore-submodules=none")
    require(status == "", "GIT_CHECKOUT_DIRTY")
    return (
        {
            "checkout_root": str(root),
            "commit": git("rev-parse", "HEAD"),
            "git_invocations": invocations,
            "status_porcelain_sha256": sha256_id(status.encode("utf-8")),
            "tree": git("rev-parse", "HEAD^{tree}"),
        },
        git,
    )


def verify_source_checkout(source_root: Path, source: dict[str, Any]) -> dict[str, object]:
    receipt, _git = git_checkout_receipt(source_root)
    require(receipt["commit"] == source["commit"], "SOURCE_COMMIT_MISMATCH")
    require(receipt["tree"] == source["tree"], "SOURCE_TREE_MISMATCH")
    return receipt


def verify_manifest_checkout(manifest_path: Path, checkout_root: Path) -> dict[str, object]:
    root = checkout_root.resolve(strict=True)
    manifest = manifest_path.resolve(strict=True)
    try:
        relative = manifest.relative_to(root).as_posix()
    except ValueError as error:
        raise DiagnosticError("MANIFEST_OUTSIDE_CHECKOUT") from error
    receipt, git = git_checkout_receipt(root)
    tracked_blob = git("rev-parse", f"HEAD:{relative}")
    require(GIT_OBJECT.fullmatch(tracked_blob) is not None, "MANIFEST_GIT_BLOB")
    require(git("hash-object", relative) == tracked_blob, "MANIFEST_WORKTREE_BLOB_MISMATCH")
    return {
        **receipt,
        "manifest_blob": tracked_blob,
        "manifest_relative_path": relative,
    }


def availability(value: object) -> str:
    require(isinstance(value, dict), "TELEMETRY_AVAILABILITY_SHAPE")
    status = value.get("status")
    require(status in {"AVAILABLE", "NOT_AVAILABLE"}, "TELEMETRY_AVAILABILITY_STATUS")
    if status == "NOT_AVAILABLE":
        strict_text(value.get("reason"), "TELEMETRY_NOT_AVAILABLE_REASON", maximum=1024)
    return str(status)


def classify_missed_slot(slot: dict[str, Any], *, java_involved: bool) -> str:
    required = exact_object(
        slot.get("mandatory_telemetry"),
        set(MANDATORY_COLLECTORS),
        "MISSED_SLOT_MANDATORY_FIELDS",
    )
    all_mandatory = True
    for collector in MANDATORY_COLLECTORS:
        if collector == "JAVA_JFR_GC_SAFEPOINT_COMPILER" and not java_involved:
            continue
        all_mandatory = availability(required[collector]) == "AVAILABLE" and all_mandatory

    predicates = exact_object(
        slot.get("predicates"),
        {
            "cgroup_throttling_overlap",
            "cpu_or_io_psi_overlap",
            "harness_or_timer_defect_observed",
            "host_hardware_fault_overlap",
            "java_pause_or_compiler_overlap",
            "process_runnable_not_continuously_consuming_cpu",
            "run_queue_starvation_overlap",
            "sustained_target_runtime_cpu_demand",
            "wal_or_fsync_stall_overlap",
        },
        "MISSED_SLOT_PREDICATE_FIELDS",
    )
    for key, item in predicates.items():
        require(type(item) is bool, "MISSED_SLOT_PREDICATE", key)

    environment_signal = any(
        predicates[name]
        for name in (
            "cgroup_throttling_overlap",
            "cpu_or_io_psi_overlap",
            "host_hardware_fault_overlap",
            "run_queue_starvation_overlap",
            "wal_or_fsync_stall_overlap",
        )
    )
    if predicates["host_hardware_fault_overlap"] or (
        predicates["process_runnable_not_continuously_consuming_cpu"] and environment_signal
    ):
        return "ENVIRONMENT_INVALID"

    if predicates["harness_or_timer_defect_observed"]:
        return "HARNESS_OR_TIMER_DEFECT"

    no_invalidator = not environment_signal
    if (
        all_mandatory
        and no_invalidator
        and predicates["sustained_target_runtime_cpu_demand"]
        and not predicates["process_runnable_not_continuously_consuming_cpu"]
        and not predicates["java_pause_or_compiler_overlap"]
    ):
        return "GENUINE_RUNTIME_DEMAND_INDICATOR"
    return "INCONCLUSIVE"


def classify_campaign(lanes: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    require(len(lanes) == 2, "EVIDENCE_LANE_COUNT")
    require([lane.get("profile_id") for lane in lanes] == PROFILE_ORDER, "EVIDENCE_LANE_ORDER")
    classified: list[dict[str, Any]] = []
    for lane in lanes:
        missed = lane.get("missed_slots")
        require(isinstance(missed, list), "MISSED_SLOTS_SHAPE")
        for index, slot_value in enumerate(missed):
            require(isinstance(slot_value, dict), "MISSED_SLOT_SHAPE")
            scheduled = strict_int(
                slot_value.get("scheduled_offer_ns"), "MISSED_SLOT_SCHEDULED", minimum=1
            )
            actual = strict_int(slot_value.get("actual_offer_ns"), "MISSED_SLOT_ACTUAL", minimum=1)
            lateness = strict_int(
                slot_value.get("scheduler_lateness_ns"), "MISSED_SLOT_LATENESS", minimum=1
            )
            require(
                actual >= scheduled and actual - scheduled == lateness, "MISSED_SLOT_ARITHMETIC"
            )
            result = classify_missed_slot(slot_value, java_involved=bool(lane["java_involved"]))
            classified.append(
                {
                    "classification": result,
                    "miss_index": index,
                    "profile_id": lane["profile_id"],
                    "scheduler_lateness_ns": lateness,
                }
            )
    if not classified:
        return "NO_MISSED_SLOTS_OBSERVED", classified
    outcomes = {item["classification"] for item in classified}
    if "INCONCLUSIVE" in outcomes or len(outcomes) != 1:
        return "INCONCLUSIVE", classified
    result = outcomes.pop()
    require(result in CAMPAIGN_CLASSIFICATIONS, "CAMPAIGN_CLASSIFICATION")
    return result, classified
