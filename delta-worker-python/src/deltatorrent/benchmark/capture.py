"""Deterministic, explicit-input environment and metric capture for fixtures."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from deltatorrent.benchmark.canonical import content_id
from deltatorrent.benchmark.contracts import (
    AUTHORITY_SCOPE,
    FORMAL_SEMANTICS_ID,
    SCHEMA_VERSION,
    CanonicalContract,
    ContractError,
)


@dataclass(frozen=True, slots=True)
class CapturedArtifact:
    name: str
    value: bytes
    content_id: str


@dataclass(frozen=True, slots=True)
class CapturedEnvironment:
    manifest: CanonicalContract
    artifacts: tuple[CapturedArtifact, ...]


def _capture_group(values: Mapping[str, bytes], code: str) -> tuple[CapturedArtifact, ...]:
    if not values or tuple(values) != tuple(sorted(values)):
        raise ContractError(code)
    artifacts: list[CapturedArtifact] = []
    for name, value in values.items():
        if not name or not isinstance(value, bytes):
            raise ContractError(code)
        artifacts.append(CapturedArtifact(name=name, value=value, content_id=content_id(value)))
    return tuple(artifacts)


def capture_environment(
    *,
    runtime_identity: CanonicalContract,
    binary_artifacts: Mapping[str, bytes],
    dependency_locks: Mapping[str, bytes],
    sbom: bytes,
    image_manifest: bytes,
    hardware_inventory: bytes,
    capture_epoch_ms: int,
    environment_variable_names: tuple[str, ...],
) -> CapturedEnvironment:
    """Build a manifest from supplied bytes without reading the host or secrets."""

    if runtime_identity.type_name != "BENCHMARK_RUNTIME_IDENTITY":
        raise ContractError("CAPTURE_RUNTIME_IDENTITY_TYPE_INVALID")
    binaries = _capture_group(binary_artifacts, "CAPTURE_BINARY_ARTIFACTS_INVALID")
    locks = _capture_group(dependency_locks, "CAPTURE_DEPENDENCY_LOCKS_INVALID")
    runtime = runtime_identity.to_dict()
    binary_ids = tuple(sorted(item.content_id for item in binaries))
    lock_ids = tuple(sorted(item.content_id for item in locks))
    if not {runtime["binary_build_id"], runtime["native_runtime_id"]} <= set(binary_ids):
        raise ContractError("CAPTURE_RUNTIME_BINARIES_MISSING")
    if not {
        runtime["compiler_lock_id"],
        runtime["java_dependency_lock_id"],
        runtime["python_lock_id"],
    } <= set(lock_ids):
        raise ContractError("CAPTURE_RUNTIME_LOCKS_MISSING")
    if content_id(sbom) != runtime["sbom_id"]:
        raise ContractError("CAPTURE_SBOM_MISMATCH")
    manifest = CanonicalContract.from_dict(
        {
            "authority_scope": AUTHORITY_SCOPE,
            "binary_ids": list(binary_ids),
            "capture_epoch_ms": capture_epoch_ms,
            "dependency_lock_ids": list(lock_ids),
            "environment_variable_names": list(environment_variable_names),
            "evidence_class": "TEST_FIXTURE",
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "gate_eligible": False,
            "hardware_inventory_id": content_id(hardware_inventory),
            "image_id": content_id(image_manifest),
            "primary_eligible": False,
            "runtime_identity_id": runtime_identity.content_id,
            "sbom_id": content_id(sbom),
            "schema_version": SCHEMA_VERSION,
            "source_commit": runtime["source_commit"],
            "source_tree": runtime["source_tree"],
            "type_name": "BENCHMARK_ENVIRONMENT_MANIFEST",
        }
    )
    extras = (
        CapturedArtifact("hardware-inventory", hardware_inventory, content_id(hardware_inventory)),
        CapturedArtifact("image-manifest", image_manifest, content_id(image_manifest)),
        CapturedArtifact("sbom", sbom, content_id(sbom)),
    )
    return CapturedEnvironment(
        manifest=manifest,
        artifacts=tuple(sorted((*binaries, *locks, *extras), key=lambda item: item.name)),
    )


def capture_fixture_metrics(
    *,
    run_manifest: CanonicalContract,
    phase_timings: tuple[tuple[str, int, int], ...],
    byte_counters: Mapping[str, int],
    gpu_device_id: str,
    gpu_memory_peak_bytes: int,
    gpu_sample_count: int,
    gpu_utilization_basis_points: int,
    cpu_time_ns: int,
    p2p_bytes: int,
    peak_rss_bytes: int,
) -> CanonicalContract:
    """Normalize already-observed fixture counters; it performs no live sampling."""

    if run_manifest.type_name != "BENCHMARK_RUN_MANIFEST":
        raise ContractError("METRICS_CAPTURE_RUN_TYPE_INVALID")
    run = run_manifest.to_dict()
    if run["status"] != "FIXTURE_COMPLETE":
        raise ContractError("METRICS_CAPTURE_FIXTURE_RUN_REQUIRED")
    return CanonicalContract.from_dict(
        {
            "authority_scope": AUTHORITY_SCOPE,
            "byte_counters": dict(byte_counters),
            "evidence_class": "TEST_FIXTURE",
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "gate_eligible": False,
            "gpu_metrics": {
                "device_id": gpu_device_id,
                "memory_peak_bytes": gpu_memory_peak_bytes,
                "sample_count": gpu_sample_count,
                "utilization_basis_points": gpu_utilization_basis_points,
            },
            "phase_timings": [
                {"end_ns": end, "phase": phase, "start_ns": start}
                for phase, start, end in phase_timings
            ],
            "primary_eligible": False,
            "resource_metrics": {
                "cpu_time_ns": cpu_time_ns,
                "p2p_bytes": p2p_bytes,
                "peak_rss_bytes": peak_rss_bytes,
            },
            "run_id": run["run_id"],
            "schema_version": SCHEMA_VERSION,
            "type_name": "BENCHMARK_METRICS",
        }
    )
