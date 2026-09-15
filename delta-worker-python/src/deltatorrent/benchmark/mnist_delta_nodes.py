"""Fail-closed orchestration for the isolated MNIST-over-Delta demonstration.

This module packages node-local MNIST model deltas and invokes the demo-only
process adapters around the unchanged Java transport and native Delta libraries.
It deliberately contains no cross-node numerical aggregation implementation.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import os
import re
import shutil
import struct
import subprocess
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Protocol, cast

import numpy as np
import numpy.typing as npt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from safetensors.numpy import save_file as save_safetensors_np

from deltatorrent.benchmark.campaign02_stage_c_runtime import (
    MeasuredStageCReceipt,
    MeasuredStageCRuntimeBoundary,
)
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.benchmark.fault_profiles import FaultProfile
from deltatorrent.benchmark.network_profiles import NetworkProfile
from deltatorrent.domain.manifests import ArtifactRef
from deltatorrent.domain.updates import NormalizedContributionCandidate
from deltatorrent.worker.drq1_producer import (
    DEFAULT_PROFILE_ID,
    ProducedShardSet,
    produce_drq1_shards,
)

Int64Array = npt.NDArray[np.int64]
Int16Array = npt.NDArray[np.int16]

WORKLOAD_MAGIC = b"DMNIST2\0"
MODEL_MAGIC = b"DMODEL1\0"
WORKLOAD_VERSION = 2
MODEL_FORMAT = "DMODEL1_INT16_BE_V1"
NODE_COUNT = 4
DIGIT_COUNT = 10
PIXELS_PER_DIGIT = 28 * 28
VECTOR_WIDTH = DIGIT_COUNT * PIXELS_PER_DIGIT + DIGIT_COUNT
STAGE_C_MNIST_EVENT_ID = "mnist-4-workers"
STAGE_C_MNIST_SEGMENT_ID = "mnist.linear"
STAGE_C_MNIST_PARAMETER_SCHEMA_ID = (
    "sha256:f43c0259749b15ae0d0154a6e9094774c7ea65e55adefbaea400a6201acb6239"
)
STAGE_C_MNIST_PROOF_INSTANCE_ID = (
    "sha256:993b4d5104810dd26a3159b60cf8fe9afe6154cdcca90d22b577ae1b6d1ac076"
)
STAGE_C_MNIST_ROUND_CONFIG_ID = (
    "sha256:34bc08c316dfe22efe155ed11b866bcc0daf7ef8c3c7389c56b2f2c707443629"
)
STAGE_C_MNIST_SCALE_TABLE_ID = (
    "sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205"
)
STAGE_C_MNIST_SHARD_PLAN_ID = (
    "sha256:4c644a3254edb3d7bff009bbe91ee99df6051516362fa1a1eac6f0a803a9c7a1"
)
STAGE_C_MNIST_ARITHMETIC_PROFILE_ID = DEFAULT_PROFILE_ID
CONTENT_ID_TEXT_BYTES = 71
CONTRIBUTION_RECORD_BYTES = 4 + 8 + CONTENT_ID_TEXT_BYTES * 2 + VECTOR_WIDTH * 2
EXACT_WORKLOAD_BYTES = 8 + 16 + CONTENT_ID_TEXT_BYTES + NODE_COUNT * CONTRIBUTION_RECORD_BYTES
TRANSPORT_SIGNATURE_DOMAIN = b"deltareduce.mnist-demo.transport.v1\0"
RELAY_MAIN_CLASS = "io.deltareduce.demo.MnistDeltaNettyRelay"
REQUIRED_RELAY_CLASS_FILES = (
    "io/deltareduce/demo/MnistDeltaNettyRelay.class",
    "io/deltareduce/node/benchmark/BenchmarkContracts.class",
    "io/deltareduce/node/benchmark/BenchmarkTransport.class",
    "io/deltareduce/node/benchmark/NettyMetricsCollector.class",
)
SOURCE_SNAPSHOT_FILES = (
    "delta-worker-python/src/deltatorrent/benchmark/mnist_demo.py",
    "delta-worker-python/src/deltatorrent/benchmark/mnist_delta_nodes.py",
    "delta-worker-python/src/deltatorrent/benchmark/mnist_demo_workspace.py",
    "integration/mnist-delta/CMakeLists.txt",
    "integration/mnist-delta/native/mnist_delta_node.cpp",
    "integration/mnist-delta/java/io/deltareduce/demo/MnistDeltaNettyRelay.java",
    "integration/mnist-delta/windows-toolchain.lock.json",
    "delta-node-java/distribution-dependencies.lock.json",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/BenchmarkContracts.java",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/BenchmarkTransport.java",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/NettyMetricsCollector.java",
    "delta-core-cpp/src/consensus.cpp",
    "delta-core-cpp/src/certificates/verifier.cpp",
    "delta-core-cpp/src/robust/plan.cpp",
    "delta-core-cpp/src/apply/engine.cpp",
    "delta-runtime-cpp/src/certificate_runtime.cpp",
)
REQUIRED_VOTE_KINDS = (
    "input_set",
    "eligibility",
    "aggregation_plan",
    "parameter_shard",
    "aggregate_root",
    "apply",
)
TRACE_SCOPE = "POST_CONFIG_POST_AVAILABILITY_DEMO_SUBTRACE"
VOTE_QUORUM_COMPONENT = "delta::core::consensus::validate_quorum"
TYPED_CERTIFICATE_VERIFIER = "delta::certificates::ChainVerifier"
TRACE_PHASES = (
    ("input_set", "ISC", "ACT-ISC-VOTE"),
    ("eligibility", "EC", "ACT-EC-VOTE"),
    ("aggregation_plan", "APC", "ACT-APC-VOTE"),
    (
        "parameter_shard",
        "PARAMETER_SHARD_QC",
        "ACT-PARAM-VOTE",
    ),
    (
        "aggregate_root",
        "AGGREGATE_ROOT_QC",
        "ACT-ROOT-VOTE",
    ),
    ("apply", "APPLY_QC", "ACT-APPLY-VOTE"),
)
NATIVE_TRACE_FIELDS = frozenset(
    {
        "action_id",
        "authoritative",
        "body_hash",
        "classification",
        "durable_sequence",
        "error_code",
        "event",
        "formal_semantics_id",
        "governance_eligible",
        "height",
        "mode",
        "outcome",
        "replay",
        "result_hash",
        "round_id",
        "schema_version",
        "type_name",
        "validator_id",
        "view",
        "vote_context_id",
        "vote_kind",
    }
)
COMMON_NATIVE_RESULT_FIELDS = frozenset(
    {
        "authoritative",
        "classification",
        "contribution_ids",
        "cryptographic_signatures_verified",
        "formal_semantics_id",
        "governance_eligible",
        "height",
        "mode",
        "node_count",
        "result_id",
        "round_id",
        "schema_version",
        "signature_semantics",
        "source_id",
        "status",
        "type_name",
        "validator_id",
        "vector_width",
        "view",
        "workload_id",
    }
)
VOTE_PHASE_RESULT_FIELDS = COMMON_NATIVE_RESULT_FIELDS | {
    "phase",
    "recovered_vote_count",
    "recovery_required",
    "runtime_wal",
    "validated_parent_qc_ids",
    "vote_wal",
}
CERTIFY_PHASE_RESULT_FIELDS = COMMON_NATIVE_RESULT_FIELDS | {
    "phase",
    "qc_artifact",
    "quorum_certificate",
    "validated_parent_qc_ids",
}
FINALIZE_RESULT_FIELDS = COMMON_NATIVE_RESULT_FIELDS | {
    "aggregate_root_qc_id",
    "apply_candidate_id",
    "apply_qc_id",
    "body_ids",
    "current_pointer",
    "current_pointer_wal",
    "model_artifact",
    "model_hash",
    "optimizer_hash",
    "quorum_certificates",
    "runtime_wal",
    "vote_wal",
}
MAXIMUM_RELAY_ENTRIES = 128
MAXIMUM_MANIFEST_BYTES = 1 << 20
MAXIMUM_MANIFEST_LINE_CHARS = 16 << 10
MAXIMUM_MESSAGE_BYTES = 64 << 20
MAXIMUM_TOTAL_BYTES = 256 << 20
DESTINATION_SEGMENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
JVM_OPTION_ENVIRONMENT = ("JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "_JAVA_OPTIONS")


class MnistDeltaError(ValueError):
    """Stable fail-closed error raised by the demo integration boundary."""


class NodeSummaryLike(Protocol):
    """Only the node-local fields consumed by the workload adapter."""

    @property
    def node_id(self) -> str: ...

    @property
    def counts(self) -> Int64Array: ...

    @property
    def sums(self) -> Int64Array: ...

    @property
    def summary_id(self) -> str: ...


@dataclass(frozen=True, slots=True)
class DeltaToolchain:
    """Exact executables used by one local demo run."""

    native_executable: Path
    java_executable: Path
    relay_classpath: str

    @classmethod
    def from_environment(cls, repository_root: Path) -> DeltaToolchain:
        """Resolve a built toolchain; never substitute an in-process fallback."""
        native_override = os.environ.get("DELTA_MNIST_NATIVE_NODE")
        native_name = (
            "delta_mnist_native_node.exe" if os.name == "nt" else "delta_mnist_native_node"
        )
        native_candidates = (
            Path(native_override) if native_override else None,
            repository_root / "out/build/mnist-delta/Release" / native_name,
            repository_root / "out/build/mnist-delta/Debug" / native_name,
            repository_root / "out/build/mnist-delta" / native_name,
        )
        native = next(
            (
                candidate.resolve(strict=True)
                for candidate in native_candidates
                if candidate is not None and candidate.is_file() and not candidate.is_symlink()
            ),
            None,
        )
        if native is None:
            raise MnistDeltaError("MNIST_DELTA_NATIVE_EXECUTABLE_MISSING")

        java_override = os.environ.get("DELTA_MNIST_JAVA")
        java_home = os.environ.get("DELTA_MNIST_JAVA_HOME") or os.environ.get("JAVA_HOME")
        java_name = "java.exe" if os.name == "nt" else "java"
        java_candidates = (
            Path(java_override) if java_override else None,
            Path(java_home) / "bin" / java_name if java_home else None,
            Path(found) if (found := shutil.which("java")) else None,
        )
        java = next(
            (
                candidate.resolve(strict=True)
                for candidate in java_candidates
                if candidate is not None and candidate.is_file() and not candidate.is_symlink()
            ),
            None,
        )
        if java is None:
            raise MnistDeltaError("MNIST_DELTA_JAVA_EXECUTABLE_MISSING")
        classpath = os.environ.get("DELTA_MNIST_RELAY_CLASSPATH", "")
        if not classpath or any(ord(character) < 32 for character in classpath):
            raise MnistDeltaError("MNIST_DELTA_RELAY_CLASSPATH_MISSING")
        return cls(native, java, classpath)

    def validate(self, repository_root: Path) -> dict[str, object]:
        """Bind executable and classpath bytes, including the four pinned Netty jars."""
        return _validate_toolchain(self, repository_root)


@dataclass(frozen=True, slots=True)
class NodeContribution:
    """Opaque file emitted by one worker; never a cross-node aggregate."""

    node_index: int
    node_id: str
    sample_count: int
    shard_id: str
    summary_id: str
    record_path: Path
    size_bytes: int
    content_id: str

    def document(self) -> dict[str, object]:
        return {
            "content_id": self.content_id,
            "node_id": self.node_id,
            "node_index": self.node_index,
            "sample_count": self.sample_count,
            "shard_id": self.shard_id,
            "summary_id": self.summary_id,
            "size_bytes": self.size_bytes,
            "vector_width": VECTOR_WIDTH,
        }


@dataclass(frozen=True, slots=True)
class AppliedModel:
    """Model bytes emitted by native Apply and decoded without aggregation."""

    raw_bytes: bytes
    content_id: str
    centroids: Int64Array
    presence: Int64Array
    values: Int16Array


@dataclass(frozen=True, slots=True)
class DeltaExecutionResult:
    """Verified APPLIED result returned to the MNIST workload/UI layer."""

    applied_model: AppliedModel
    delta_execution: dict[str, object]
    execution_trace_path: Path
    execution_diagram_path: Path
    failure_simulation: dict[str, object]
    node_contributions: tuple[NodeContribution, ...]


@dataclass(frozen=True, slots=True)
class StageCMnistDrq1Result:
    """Stage C receipt proving worker DRQ1 artifacts entered Feature008."""

    receipt: MeasuredStageCReceipt
    evidence_path: Path
    evidence: dict[str, object]
    final_checkpoint_id: str
    evaluation_checkpoint_id: str
    ticket_ids: tuple[str, ...]
    worker_shard_leaf_ids: tuple[tuple[str, str], ...]


def _content_id(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _derived_content_id(domain: str, components: Sequence[str]) -> str:
    value = bytearray(domain.encode("ascii"))
    value.append(0)
    for component in components:
        encoded = component.encode("utf-8")
        value.extend(struct.pack(">Q", len(encoded)))
        value.extend(encoded)
    return _content_id(bytes(value))


def _regular_file_bytes(path: Path, code: str, *, maximum: int = MAXIMUM_MESSAGE_BYTES) -> bytes:
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise MnistDeltaError(code)
    try:
        size = path.stat().st_size
        if size <= 0 or size > maximum:
            raise MnistDeltaError(code)
        value = path.read_bytes()
    except OSError as exc:
        raise MnistDeltaError(code) from exc
    if len(value) != size:
        raise MnistDeltaError(code)
    return value


def _classpath_directory_document(path: Path) -> dict[str, object]:
    class_groups = (
        "io/deltareduce/demo/MnistDeltaNettyRelay",
        "io/deltareduce/node/benchmark/BenchmarkContracts",
        "io/deltareduce/node/benchmark/BenchmarkTransport",
        "io/deltareduce/node/benchmark/NettyMetricsCollector",
    )
    files: list[tuple[str, bytes]] = []
    for candidate in sorted(path.rglob("*.class")):
        if candidate.is_symlink() or not candidate.is_file():
            raise MnistDeltaError("MNIST_DELTA_CLASSPATH_INVALID")
        relative = candidate.relative_to(path).as_posix()
        if any(relative.startswith(group) for group in class_groups):
            files.append(
                (relative, _regular_file_bytes(candidate, "MNIST_DELTA_CLASSPATH_INVALID"))
            )
    digest_input = bytearray()
    for relative, value in files:
        encoded = relative.encode("utf-8")
        digest_input.extend(struct.pack(">I", len(encoded)))
        digest_input.extend(encoded)
        digest_input.extend(bytes.fromhex(_content_id(value)[7:]))
    return {
        "class_files": [
            {"content_id": _content_id(value), "path": relative} for relative, value in files
        ],
        "content_id": _content_id(bytes(digest_input)),
        "kind": "CLASS_DIRECTORY",
    }


def _source_snapshot(repository_root: Path) -> dict[str, object]:
    required_markers = {
        "integration/mnist-delta/CMakeLists.txt": (
            "delta::runtime",
            "delta::certificates",
            "delta::robust",
            "delta::apply",
        ),
        "integration/mnist-delta/native/mnist_delta_node.cpp": (
            "runtime::CertificateVoteRuntime",
            "consensus::validate_quorum",
            "certificates::ChainVerifier",
            "delta::robust::build_plan",
            "delta::robust::reduce_parameter_shard",
            "delta::apply::compute_candidate",
            "runtime::CurrentPointerStore",
            "verify_relayed_contributions",
        ),
        "integration/mnist-delta/java/io/deltareduce/demo/MnistDeltaNettyRelay.java": (
            "new BenchmarkTransport",
            "new NettyMetricsCollector",
            "Ed25519",
        ),
    }
    forbidden_orchestrator_marker_parts = (
        ("aggregate_", "summaries"),
        ("np.", "concatenate("),
        ("np.", "mean("),
        ("np.", "stack("),
        ("np.", "sum("),
    )
    files: list[dict[str, object]] = []
    for relative in SOURCE_SNAPSHOT_FILES:
        candidate = repository_root / relative
        if candidate.is_symlink():
            raise MnistDeltaError("MNIST_DELTA_SOURCE_SNAPSHOT_INVALID")
        path = candidate.resolve(strict=True)
        if not path.is_relative_to(repository_root):
            raise MnistDeltaError("MNIST_DELTA_SOURCE_SNAPSHOT_INVALID")
        raw = _regular_file_bytes(path, "MNIST_DELTA_SOURCE_SNAPSHOT_INVALID", maximum=4 << 20)
        try:
            text = raw.decode("utf-8")
        except UnicodeError as exc:
            raise MnistDeltaError("MNIST_DELTA_SOURCE_SNAPSHOT_INVALID") from exc
        if any(marker not in text for marker in required_markers.get(relative, ())):
            raise MnistDeltaError("MNIST_DELTA_SOURCE_MARKER_MISSING")
        if relative.endswith("/mnist_delta_nodes.py") and any(
            "".join(parts) in text for parts in forbidden_orchestrator_marker_parts
        ):
            raise MnistDeltaError("MNIST_DELTA_HIDDEN_AGGREGATION_SOURCE_REJECTED")
        files.append(
            {
                "bytes": len(raw),
                "content_id": _content_id(raw),
                "path": relative,
            }
        )
    document: dict[str, object] = {
        "binary_source_build_attestation_claimed": False,
        "files": files,
        "no_hidden_aggregation_static_gate": "PASS",
        "review_scope": "LOCAL_DEMO_EXECUTION_PATH",
        "semantic_completeness_claimed": False,
    }
    document["content_id"] = _content_id(_canonical_bytes(document))
    return document


def _validate_toolchain(toolchain: DeltaToolchain, repository_root: Path) -> dict[str, object]:
    for option in JVM_OPTION_ENVIRONMENT:
        if os.environ.get(option):
            raise MnistDeltaError("MNIST_DELTA_JVM_OPTION_INJECTION_REJECTED")
    native = toolchain.native_executable.resolve(strict=True)
    java = toolchain.java_executable.resolve(strict=True)
    native_bytes = _regular_file_bytes(native, "MNIST_DELTA_NATIVE_EXECUTABLE_INVALID")
    java_bytes = _regular_file_bytes(java, "MNIST_DELTA_JAVA_EXECUTABLE_INVALID")

    try:
        version = subprocess.run(
            (str(java), "-version"),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MnistDeltaError("MNIST_DELTA_JAVA_VERSION_INVALID") from exc
    version_text = version.stdout + version.stderr
    if (
        version.returncode != 0
        or re.search(r'(?:version\s+")?25(?:[.\s"]|$)', version_text) is None
    ):
        raise MnistDeltaError("MNIST_DELTA_REQUIRES_JDK25")

    try:
        described = subprocess.run(
            (str(native), "--describe"),
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        native_descriptor = json.loads(described.stdout)
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        raise MnistDeltaError("MNIST_DELTA_NATIVE_DESCRIPTOR_INVALID") from exc
    expected_descriptor: dict[str, object] = {
        "applied_model_format": MODEL_FORMAT,
        "authoritative": False,
        "classification": "LOCAL_DEMO_ONLY",
        "crash_exit_code": 75,
        "executable": "delta_mnist_native_node",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "governance_eligible": False,
        "modes": ["vote-phase", "certify-phase", "finalize"],
        "node_count": NODE_COUNT,
        "schema_version": "1.0.0",
        "type_name": "MNIST_DELTA_NATIVE_NODE_DESCRIPTOR",
        "vector_width": VECTOR_WIDTH,
        "workload_bytes": EXACT_WORKLOAD_BYTES,
        "workload_format": "DMNIST2_NODE_SUMMARY_INT16_BE_V1",
    }
    if (
        described.returncode != 0
        or described.stderr
        or native_descriptor != expected_descriptor
        or described.stdout.encode("utf-8") != _canonical_bytes(expected_descriptor) + b"\n"
    ):
        raise MnistDeltaError("MNIST_DELTA_NATIVE_DESCRIPTOR_INVALID")

    raw_entries = toolchain.relay_classpath.split(os.pathsep)
    if not raw_entries or len(raw_entries) > 16 or any(not entry for entry in raw_entries):
        raise MnistDeltaError("MNIST_DELTA_RELAY_CLASSPATH_INVALID")
    entries: list[Path] = []
    for raw_entry in raw_entries:
        candidate = Path(raw_entry)
        if not candidate.is_absolute() or candidate.is_symlink():
            raise MnistDeltaError("MNIST_DELTA_RELAY_CLASSPATH_INVALID")
        resolved = candidate.resolve(strict=True)
        if resolved in entries or (not resolved.is_dir() and not resolved.is_file()):
            raise MnistDeltaError("MNIST_DELTA_RELAY_CLASSPATH_INVALID")
        entries.append(resolved)

    lock = _load_json(
        repository_root / "delta-node-java/distribution-dependencies.lock.json",
        "MNIST_DELTA_DEPENDENCY_LOCK_INVALID",
    )
    artifacts = lock.get("maven_artifacts")
    if lock.get("type_name") != "DISTRIBUTION_DEPENDENCY_LOCK" or not isinstance(artifacts, list):
        raise MnistDeltaError("MNIST_DELTA_DEPENDENCY_LOCK_INVALID")
    expected_jars: dict[str, int] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            raise MnistDeltaError("MNIST_DELTA_DEPENDENCY_LOCK_INVALID")
        coordinate = artifact.get("coordinate")
        digest = artifact.get("sha256")
        length = artifact.get("length")
        if (
            not isinstance(coordinate, str)
            or not coordinate.startswith("io.netty:")
            or not isinstance(digest, str)
            or not isinstance(length, int)
        ):
            raise MnistDeltaError("MNIST_DELTA_DEPENDENCY_LOCK_INVALID")
        expected_jars[f"sha256:{digest}"] = length
    if len(expected_jars) != 4:
        raise MnistDeltaError("MNIST_DELTA_DEPENDENCY_LOCK_INVALID")

    class_documents: list[dict[str, object]] = []
    jar_documents: list[dict[str, object]] = []
    observed_jars: set[str] = set()
    observed_classes: set[str] = set()
    for entry in entries:
        if entry.is_dir():
            document = _classpath_directory_document(entry)
            class_documents.append(document)
            class_files = document.get("class_files")
            if not isinstance(class_files, list):
                raise MnistDeltaError("MNIST_DELTA_RELAY_CLASSPATH_INVALID")
            for class_file in class_files:
                if not isinstance(class_file, dict) or set(class_file) != {
                    "content_id",
                    "path",
                }:
                    raise MnistDeltaError("MNIST_DELTA_RELAY_CLASSPATH_INVALID")
                filename = class_file.get("path")
                if not isinstance(filename, str) or filename in observed_classes:
                    raise MnistDeltaError("MNIST_DELTA_RELAY_CLASSPATH_SHADOWED")
                _require_content_id(
                    class_file.get("content_id"), "MNIST_DELTA_RELAY_CLASSPATH_INVALID"
                )
                observed_classes.add(filename)
            continue
        value = _regular_file_bytes(entry, "MNIST_DELTA_CLASSPATH_JAR_INVALID")
        content_id = _content_id(value)
        if entry.suffix.lower() != ".jar" or content_id not in expected_jars:
            raise MnistDeltaError("MNIST_DELTA_CLASSPATH_JAR_UNPINNED")
        if len(value) != expected_jars[content_id] or content_id in observed_jars:
            raise MnistDeltaError("MNIST_DELTA_CLASSPATH_JAR_INVALID")
        observed_jars.add(content_id)
        jar_documents.append(
            {"bytes": len(value), "content_id": content_id, "kind": "PINNED_NETTY_JAR"}
        )
    if observed_jars != set(expected_jars) or any(
        required not in observed_classes for required in REQUIRED_RELAY_CLASS_FILES
    ):
        raise MnistDeltaError("MNIST_DELTA_RELAY_CLASSPATH_INCOMPLETE")
    classpath_document: dict[str, object] = {
        "class_directories": class_documents,
        "pinned_jars": jar_documents,
    }
    classpath_document["content_id"] = _content_id(_canonical_bytes(classpath_document))
    return {
        "classpath": classpath_document,
        "java_executable_sha256": _content_id(java_bytes),
        "java_feature": 25,
        "native_executable_sha256": _content_id(native_bytes),
        "native_descriptor": native_descriptor,
        "source_snapshot": _source_snapshot(repository_root),
    }


def _require_content_id(value: object, code: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != CONTENT_ID_TEXT_BYTES
        or not value.startswith("sha256:")
    ):
        raise MnistDeltaError(code)
    try:
        bytes.fromhex(value[7:])
    except ValueError as exc:
        raise MnistDeltaError(code) from exc
    if value != value.lower():
        raise MnistDeltaError(code)
    return value


def _write_new(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _write_json_new(path: Path, value: object) -> None:
    _write_new(path, _canonical_bytes(value) + b"\n")


def _node_index(node_id: str) -> int:
    try:
        suffix = int(node_id.rsplit("-", 1)[1])
    except (IndexError, ValueError) as exc:
        raise MnistDeltaError("MNIST_DELTA_NODE_ID_INVALID") from exc
    if suffix not in range(1, NODE_COUNT + 1):
        raise MnistDeltaError("MNIST_DELTA_NODE_ID_INVALID")
    return suffix


def _round_nonnegative_half_toward_positive(values: Int64Array, count: int) -> Int64Array:
    if count <= 0 or bool(np.any(values < 0)):
        raise MnistDeltaError("MNIST_DELTA_LOCAL_SUM_INVALID")
    quotient, remainder = np.divmod(values, count)
    rounded = quotient + (remainder * 2 >= count)
    return np.ascontiguousarray(rounded, dtype=np.int64)


def write_node_contribution(
    summary: NodeSummaryLike, shard_id: str, destination: Path
) -> NodeContribution:
    """Quantize and seal exactly one worker summary inside that worker process."""
    node_index = _node_index(summary.node_id)
    shard = _require_content_id(shard_id, "MNIST_DELTA_SHARD_ID_INVALID")
    _require_content_id(summary.summary_id, "MNIST_DELTA_SUMMARY_ID_INVALID")
    counts = np.asarray(summary.counts, dtype=np.int64)
    sums = np.asarray(summary.sums, dtype=np.int64)
    if counts.shape != (DIGIT_COUNT,) or sums.shape != (DIGIT_COUNT, PIXELS_PER_DIGIT):
        raise MnistDeltaError("MNIST_DELTA_LOCAL_SUMMARY_SHAPE_INVALID")
    if bool(np.any(counts < 0)) or bool(np.any(sums < 0)):
        raise MnistDeltaError("MNIST_DELTA_LOCAL_SUMMARY_NEGATIVE")

    values = np.zeros(VECTOR_WIDTH, dtype=np.int16)
    for digit in range(DIGIT_COUNT):
        count = int(counts[digit])
        row = sums[digit]
        if count == 0:
            if bool(np.any(row != 0)):
                raise MnistDeltaError("MNIST_DELTA_EMPTY_CLASS_HAS_SUM")
            continue
        rounded = _round_nonnegative_half_toward_positive(row, count)
        if bool(np.any(rounded > 255)):
            raise MnistDeltaError("MNIST_DELTA_CENTROID_OUT_OF_RANGE")
        start = digit * PIXELS_PER_DIGIT
        # The frozen robust profile assigns every one of the four tickets weight 1/4.
        # Scale this node-local delta by four so its disjoint class survives that
        # production coefficient exactly; no other node's values are inspected here.
        values[start : start + PIXELS_PER_DIGIT] = -(rounded * NODE_COUNT).astype(np.int16)
        values[DIGIT_COUNT * PIXELS_PER_DIGIT + digit] = -NODE_COUNT

    sample_count = int(np.add.reduce(counts, dtype=np.int64))
    if sample_count <= 0:
        raise MnistDeltaError("MNIST_DELTA_LOCAL_SUMMARY_EMPTY")
    record = bytearray()
    record.extend(struct.pack(">IQ", node_index, sample_count))
    record.extend(shard.encode("ascii"))
    record.extend(summary.summary_id.encode("ascii"))
    record.extend(values.astype(">i2", copy=False).tobytes(order="C"))
    record_bytes = bytes(record)
    if len(record_bytes) != CONTRIBUTION_RECORD_BYTES:
        raise MnistDeltaError("MNIST_DELTA_CONTRIBUTION_SIZE_INVALID")
    if not destination.is_absolute() or destination.is_symlink() or destination.exists():
        raise MnistDeltaError("MNIST_DELTA_CONTRIBUTION_DESTINATION_INVALID")
    _write_new(destination, record_bytes)
    return NodeContribution(
        node_index=node_index,
        node_id=summary.node_id,
        sample_count=sample_count,
        shard_id=shard,
        summary_id=summary.summary_id,
        record_path=destination.resolve(strict=True),
        size_bytes=len(record_bytes),
        content_id=_content_id(record_bytes),
    )


def write_workload(
    contributions: Sequence[NodeContribution],
    source_id: str,
    destination: Path,
) -> tuple[tuple[NodeContribution, ...], str]:
    """Concatenate four opaque worker records; perform no numeric operation on them."""
    source = _require_content_id(source_id, "MNIST_DELTA_SOURCE_ID_INVALID")
    if len(contributions) != NODE_COUNT:
        raise MnistDeltaError("MNIST_DELTA_NODE_COUNT_INVALID")
    ordered = tuple(sorted(contributions, key=lambda item: item.node_index))
    if tuple(item.node_index for item in ordered) != tuple(range(1, NODE_COUNT + 1)):
        raise MnistDeltaError("MNIST_DELTA_NODE_SET_INVALID")
    if (
        len({item.node_id for item in ordered}) != NODE_COUNT
        or len({item.shard_id for item in ordered}) != NODE_COUNT
        or len({item.summary_id for item in ordered}) != NODE_COUNT
        or len({item.record_path for item in ordered}) != NODE_COUNT
    ):
        raise MnistDeltaError("MNIST_DELTA_NODE_SET_DUPLICATE")

    opaque_records: list[bytes] = []
    for item in ordered:
        _require_content_id(item.shard_id, "MNIST_DELTA_SHARD_ID_INVALID")
        _require_content_id(item.summary_id, "MNIST_DELTA_SUMMARY_ID_INVALID")
        raw = _regular_file_bytes(
            item.record_path,
            "MNIST_DELTA_CONTRIBUTION_FILE_INVALID",
            maximum=CONTRIBUTION_RECORD_BYTES,
        )
        expected_prefix = (
            struct.pack(">IQ", item.node_index, item.sample_count)
            + item.shard_id.encode("ascii")
            + item.summary_id.encode("ascii")
        )
        if (
            item.node_id != f"demo-mnist-worker-{item.node_index:02d}"
            or item.sample_count <= 0
            or item.sample_count > 60_000
            or item.size_bytes != CONTRIBUTION_RECORD_BYTES
            or len(raw) != CONTRIBUTION_RECORD_BYTES
            or not raw.startswith(expected_prefix)
            or _content_id(raw) != item.content_id
        ):
            raise MnistDeltaError("MNIST_DELTA_CONTRIBUTION_FILE_INVALID")
        opaque_records.append(raw)

    header = bytearray(WORKLOAD_MAGIC)
    header.extend(struct.pack(">IIII", WORKLOAD_VERSION, NODE_COUNT, VECTOR_WIDTH, NODE_COUNT))
    header.extend(source.encode("ascii"))
    payload = bytes(header) + b"".join(opaque_records)
    if len(payload) != EXACT_WORKLOAD_BYTES:
        raise MnistDeltaError("MNIST_DELTA_WORKLOAD_SIZE_INVALID")
    _write_new(destination, payload)
    for contribution, record in zip(ordered, opaque_records, strict=True):
        _write_new(
            destination.parent / f"contribution-{contribution.node_index:02d}.bin",
            record,
        )
    return ordered, _content_id(payload)


def _stage_c_mnist_network_profiles() -> tuple[tuple[str, NetworkProfile], ...]:
    value: dict[str, object] = {
        "bandwidth_kbps": 1_000_000,
        "disconnect_ms": 0,
        "duplication_ppm": 0,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "jitter_ms": 0,
        "loss_ppm": 0,
        "profile_id": "lan-control",
        "reordering_ppm": 0,
        "rtt_ms": 1,
        "schema_version": "1.0.0",
        "seed": 10001,
        "type_name": "NETWORK_PROFILE",
    }
    return ((_content_id(_canonical_bytes(value)), NetworkProfile.from_dict(value)),)


def _stage_c_mnist_fault_profile() -> FaultProfile:
    return FaultProfile.from_dict(
        {
            "events": [
                {
                    "action": "CRASH",
                    "actor_class": "WORKER",
                    "assumptions_hold": True,
                    "at_step": 100,
                    "event_id": STAGE_C_MNIST_EVENT_ID,
                    "expected_outcome": "APPLIED",
                }
            ],
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "profile_id": "mnist-real-drq1-stagec-v1",
            "schema_version": "1.0.0",
            "type_name": "FAULT_PROFILE",
        }
    )


def _stage_c_mnist_scale_table() -> dict[str, object]:
    return {
        "content_id": STAGE_C_MNIST_SCALE_TABLE_ID,
        "segments": [
            {
                "element_count": VECTOR_WIDTH,
                "element_start": 0,
                "quantum": {"denominator": 1, "numerator": "1"},
                "segment_id": STAGE_C_MNIST_SEGMENT_ID,
                "segment_ordinal": 0,
            }
        ],
        "total_elements": VECTOR_WIDTH,
    }


def _stage_c_mnist_shard_plan() -> dict[str, object]:
    return {
        "content_id": STAGE_C_MNIST_SHARD_PLAN_ID,
        "entries": [
            {
                "element_count": VECTOR_WIDTH,
                "element_start": 0,
                "ordinal": 0,
                "payload_bytes": VECTOR_WIDTH * 2,
                "segment_id": STAGE_C_MNIST_SEGMENT_ID,
                "segment_offset": 0,
            }
        ],
        "total_elements": VECTOR_WIDTH,
    }


def _stage_c_mnist_shards_manifest() -> dict[str, object]:
    return {
        "element_count": VECTOR_WIDTH,
        "element_start": 0,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "ordinal": 0,
        "parameter_schema_id": STAGE_C_MNIST_PARAMETER_SCHEMA_ID,
        "profile_id": STAGE_C_MNIST_ARITHMETIC_PROFILE_ID,
        "proof_instance_id": STAGE_C_MNIST_PROOF_INSTANCE_ID,
        "round_config_id": STAGE_C_MNIST_ROUND_CONFIG_ID,
        "scale_table_id": STAGE_C_MNIST_SCALE_TABLE_ID,
        "segment_id": STAGE_C_MNIST_SEGMENT_ID,
        "segment_offset": 0,
        "shard_plan_id": STAGE_C_MNIST_SHARD_PLAN_ID,
    }


def _read_verified_node_q_values(contribution: NodeContribution) -> Int16Array:
    _require_content_id(contribution.shard_id, "MNIST_DELTA_SHARD_ID_INVALID")
    _require_content_id(contribution.summary_id, "MNIST_DELTA_SUMMARY_ID_INVALID")
    raw = _regular_file_bytes(
        contribution.record_path,
        "MNIST_DELTA_CONTRIBUTION_FILE_INVALID",
        maximum=CONTRIBUTION_RECORD_BYTES,
    )
    expected_prefix = (
        struct.pack(">IQ", contribution.node_index, contribution.sample_count)
        + contribution.shard_id.encode("ascii")
        + contribution.summary_id.encode("ascii")
    )
    if (
        contribution.node_id != f"demo-mnist-worker-{contribution.node_index:02d}"
        or contribution.sample_count <= 0
        or contribution.sample_count > 60_000
        or contribution.size_bytes != CONTRIBUTION_RECORD_BYTES
        or len(raw) != CONTRIBUTION_RECORD_BYTES
        or not raw.startswith(expected_prefix)
        or _content_id(raw) != contribution.content_id
    ):
        raise MnistDeltaError("MNIST_DELTA_CONTRIBUTION_FILE_INVALID")
    offset = 4 + 8 + CONTENT_ID_TEXT_BYTES * 2
    values = np.frombuffer(raw, dtype=">i2", offset=offset).astype(np.int16)
    if values.shape != (VECTOR_WIDTH,):
        raise MnistDeltaError("MNIST_DELTA_CONTRIBUTION_FILE_INVALID")
    return np.ascontiguousarray(values, dtype=np.int16)


def _stage_c_ticket_id(contribution: NodeContribution) -> str:
    if contribution.node_index not in range(1, NODE_COUNT + 1):
        raise MnistDeltaError("MNIST_DELTA_NODE_SET_INVALID")
    return f"ticket-{contribution.node_index - 1:03d}"


def _stage_c_domain_id(contribution: NodeContribution) -> str:
    if contribution.node_index not in range(1, NODE_COUNT + 1):
        raise MnistDeltaError("MNIST_DELTA_NODE_SET_INVALID")
    return "code" if contribution.node_index <= NODE_COUNT // 2 else "text"


def _write_stage_c_candidate_artifact(q_values: Int16Array, destination: Path) -> ArtifactRef:
    tensor = np.ascontiguousarray(q_values.astype(np.float32), dtype=np.float32)
    if destination.exists() or destination.is_symlink():
        raise MnistDeltaError("MNIST_DELTA_STAGEC_ARTIFACT_DESTINATION_INVALID")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        save_safetensors_np({STAGE_C_MNIST_SEGMENT_ID: tensor}, str(destination))
    except Exception as exc:
        raise MnistDeltaError("MNIST_DELTA_STAGEC_SAFETENSORS_WRITE_FAILED") from exc
    raw = _regular_file_bytes(
        destination.resolve(strict=True),
        "MNIST_DELTA_STAGEC_SAFETENSORS_WRITE_FAILED",
        maximum=1 << 20,
    )
    return ArtifactRef(
        byte_length=len(raw),
        content_id=_content_id(raw),
        locator=f"stagec-normalized/{destination.name}",
        media_type="application/vnd.safetensors",
        schema_id="SCHEMA-SAFETENSORS-V1",
        schema_version="1.0.0",
    )


def _produce_stage_c_mnist_shard_set(
    contribution: NodeContribution,
    destination: Path,
) -> ProducedShardSet:
    q_values = _read_verified_node_q_values(contribution)
    ticket_id = _stage_c_ticket_id(contribution)
    artifact = _write_stage_c_candidate_artifact(
        q_values,
        destination / "stagec-normalized" / f"{ticket_id}.safetensors",
    )
    candidate = NormalizedContributionCandidate(
        arithmetic_profile_id=STAGE_C_MNIST_ARITHMETIC_PROFILE_ID,
        completion_id=contribution.content_id,
        domain_id=_stage_c_domain_id(contribution),
        effective_steps=1,
        normalized_delta=artifact,
        normalization_denominator=1,
        optimizer_profile_id=_derived_content_id(
            "deltareduce.demo.mnist.optimizer-profile.v1",
            [STAGE_C_MNIST_EVENT_ID],
        ),
        parameter_schema_id=STAGE_C_MNIST_PARAMETER_SCHEMA_ID,
        parent_model_id=_derived_content_id(
            "deltareduce.demo.mnist.parent-model.v1",
            [STAGE_C_MNIST_EVENT_ID],
        ),
        step_budget=1,
        tensor_order=(STAGE_C_MNIST_SEGMENT_ID,),
        ticket_fingerprint=contribution.shard_id,
        ticket_id=ticket_id,
    )
    produced = produce_drq1_shards(
        candidate=candidate,
        safetensors_path=destination / "stagec-normalized" / f"{ticket_id}.safetensors",
        scale_table=_stage_c_mnist_scale_table(),
        shard_plan=_stage_c_mnist_shard_plan(),
        proof_instance_id=STAGE_C_MNIST_PROOF_INSTANCE_ID,
        round_config_id=STAGE_C_MNIST_ROUND_CONFIG_ID,
        profile_id=STAGE_C_MNIST_ARITHMETIC_PROFILE_ID,
        formal_semantics_id=FORMAL_SEMANTICS_ID,
    )
    if len(produced.shards) != 1 or produced.shards[0].ordinal != 0:
        raise MnistDeltaError("MNIST_DELTA_STAGEC_REQUIRES_SINGLE_SHARD")
    if produced.commitment_root != produced.shards[0].leaf_id:
        raise MnistDeltaError("MNIST_DELTA_STAGEC_SINGLE_SHARD_ROOT_INVALID")
    return produced


def _assert_stage_c_mnist_receipt(receipt: MeasuredStageCReceipt) -> tuple[str, str]:
    if len(receipt.fault_transitions) != 1:
        raise MnistDeltaError("MNIST_DELTA_STAGEC_RECEIPT_INVALID")
    transition = receipt.fault_transitions[0]
    evidence = transition.causal_evidence
    final_checkpoint_id = evidence.next_checkpoint_id
    evaluation_checkpoint_id = evidence.current_pointer_after
    if (
        transition.event_id != STAGE_C_MNIST_EVENT_ID
        or transition.observed_outcome != "APPLIED"
        or not transition.current_checkpoint_advanced
        or final_checkpoint_id is None
        or evaluation_checkpoint_id is None
        or final_checkpoint_id != evaluation_checkpoint_id
        or evidence.current_pointer_before == evidence.current_pointer_after
        or evidence.missing_work_policy_result != "FULL_QUORUM_DELIVERED_EXACT_ISC"
        or evidence.isc_ticket_set != tuple(f"ticket-{index:03d}" for index in range(NODE_COUNT))
        or evidence.worker_count_before != NODE_COUNT
        or evidence.worker_count_lost != 0
    ):
        raise MnistDeltaError("MNIST_DELTA_STAGEC_RECEIPT_INVALID")
    return final_checkpoint_id, evaluation_checkpoint_id


def run_stage_c_real_drq1_nodes(
    repository_root: Path,
    destination: Path,
    node_contributions: Sequence[NodeContribution],
    source_id: str,
    *,
    boundary: MeasuredStageCRuntimeBoundary,
    network_profiles: tuple[tuple[str, NetworkProfile], ...] | None = None,
    fault_profile: FaultProfile | None = None,
    packet_count: int = 10,
    payload_bytes: int = 1000,
) -> StageCMnistDrq1Result:
    """Run the four MNIST worker DRQ1 shards through existing Stage C Feature008."""
    repository_root.resolve(strict=True)
    source = _require_content_id(source_id, "MNIST_DELTA_SOURCE_ID_INVALID")
    output = destination.resolve(strict=False)
    if output.exists():
        raise MnistDeltaError("MNIST_DELTA_STAGEC_OUTPUT_ALREADY_EXISTS")
    output.mkdir(parents=True)
    if len(node_contributions) != NODE_COUNT:
        raise MnistDeltaError("MNIST_DELTA_NODE_COUNT_INVALID")
    ordered = tuple(sorted(node_contributions, key=lambda item: item.node_index))
    if tuple(item.node_index for item in ordered) != tuple(range(1, NODE_COUNT + 1)):
        raise MnistDeltaError("MNIST_DELTA_NODE_SET_INVALID")

    worker_shards: dict[str, bytes] = {}
    leaf_ids: list[tuple[str, str]] = []
    for contribution in ordered:
        produced = _produce_stage_c_mnist_shard_set(contribution, output)
        ticket_id = _stage_c_ticket_id(contribution)
        shard = produced.shards[0]
        worker_shards[ticket_id] = shard.envelope
        leaf_ids.append((ticket_id, shard.leaf_id))

    plan_document = {
        "event_id": STAGE_C_MNIST_EVENT_ID,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "profile": "REAL_DRQ1_SINGLE_SHARD_MNIST_DEMO",
        "source_id": source,
        "ticket_ids": sorted(worker_shards),
        "worker_contribution_ids": [item.content_id for item in ordered],
    }
    plan_id = _content_id(_canonical_bytes(plan_document))
    receipt = boundary.execute(
        plan_id=plan_id,
        packet_count=packet_count,
        payload_bytes=payload_bytes,
        network_profiles=network_profiles or _stage_c_mnist_network_profiles(),
        fault_profile=fault_profile or _stage_c_mnist_fault_profile(),
        worker_shards=worker_shards,
        shards_manifest=_stage_c_mnist_shards_manifest(),
    )
    final_checkpoint_id, evaluation_checkpoint_id = _assert_stage_c_mnist_receipt(receipt)
    evidence: dict[str, object] = {
        "commitment_scope": "SINGLE_DRQ1_SHARD_PER_WORKER_LEAF_ID",
        "event_id": STAGE_C_MNIST_EVENT_ID,
        "final_checkpoint_id": final_checkpoint_id,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "mnist_source_id": source,
        "native_fault_trace_id": receipt.native_fault_trace_id,
        "python_cross_node_aggregation_performed": False,
        "real_drq1_required": True,
        "receipt_id": receipt.raw_java_receipt_id,
        "schema_version": "1.0.0",
        "single_shard_scope": True,
        "synthetic_contribution_fallback_allowed": False,
        "ticket_ids": sorted(worker_shards),
        "type_name": "MNIST_STAGEC_REAL_DRQ1_ACCEPTANCE",
        "worker_shard_leaf_ids": [
            {"leaf_id": leaf_id, "ticket_id": ticket_id} for ticket_id, leaf_id in leaf_ids
        ],
    }
    evidence_path = output / "stagec-real-drq1-evidence.json"
    _write_json_new(evidence_path, evidence)
    return StageCMnistDrq1Result(
        receipt=receipt,
        evidence_path=evidence_path,
        evidence=evidence,
        final_checkpoint_id=final_checkpoint_id,
        evaluation_checkpoint_id=evaluation_checkpoint_id,
        ticket_ids=tuple(sorted(worker_shards)),
        worker_shard_leaf_ids=tuple(leaf_ids),
    )


def decode_applied_model(path: Path) -> AppliedModel:
    """Decode only the model artifact emitted by the native APPLIED transition."""
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise MnistDeltaError("MNIST_DELTA_APPLIED_MODEL_MISSING") from exc
    if len(raw) != len(MODEL_MAGIC) + 4 + VECTOR_WIDTH * 2 or not raw.startswith(MODEL_MAGIC):
        raise MnistDeltaError("MNIST_DELTA_APPLIED_MODEL_FORMAT_INVALID")
    (width,) = struct.unpack_from(">I", raw, len(MODEL_MAGIC))
    if width != VECTOR_WIDTH:
        raise MnistDeltaError("MNIST_DELTA_APPLIED_MODEL_WIDTH_INVALID")
    values = np.frombuffer(raw, dtype=">i2", offset=len(MODEL_MAGIC) + 4).astype(np.int16)
    centroid_values = values[: DIGIT_COUNT * PIXELS_PER_DIGIT].astype(np.int64)
    presence_values = values[DIGIT_COUNT * PIXELS_PER_DIGIT :].astype(np.int64)
    if bool(np.any(centroid_values < 0)) or bool(np.any(centroid_values > 255)):
        raise MnistDeltaError("MNIST_DELTA_APPLIED_CENTROID_INVALID")
    if bool(np.any((presence_values != 0) & (presence_values != 1))):
        raise MnistDeltaError("MNIST_DELTA_APPLIED_PRESENCE_INVALID")
    return AppliedModel(
        raw_bytes=raw,
        content_id=_content_id(raw),
        centroids=np.ascontiguousarray(
            centroid_values.reshape(DIGIT_COUNT, PIXELS_PER_DIGIT), dtype=np.int64
        ),
        presence=np.ascontiguousarray(presence_values, dtype=np.int64),
        values=np.ascontiguousarray(values, dtype=np.int16),
    )


def expected_central_model(sums: Int64Array, counts: Int64Array) -> Int16Array:
    """Build the independent centralized baseline under the same integer profile."""
    if sums.shape != (DIGIT_COUNT, PIXELS_PER_DIGIT) or counts.shape != (DIGIT_COUNT,):
        raise MnistDeltaError("MNIST_DELTA_CENTRAL_MODEL_SHAPE_INVALID")
    values = np.zeros(VECTOR_WIDTH, dtype=np.int16)
    for digit in range(DIGIT_COUNT):
        count = int(counts[digit])
        if count <= 0:
            continue
        rounded = _round_nonnegative_half_toward_positive(sums[digit], count)
        if bool(np.any(rounded > 255)):
            raise MnistDeltaError("MNIST_DELTA_CENTRAL_CENTROID_INVALID")
        start = digit * PIXELS_PER_DIGIT
        values[start : start + PIXELS_PER_DIGIT] = rounded.astype(np.int16)
        values[DIGIT_COUNT * PIXELS_PER_DIGIT + digit] = 1
    return values


def _load_json(path: Path, code: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MnistDeltaError(code) from exc
    if not isinstance(value, dict):
        raise MnistDeltaError(code)
    return cast(dict[str, object], value)


def _run_process(
    command: Sequence[str], *, expected_codes: frozenset[int]
) -> subprocess.CompletedProcess[str]:
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
            tuple(command),
            check=False,
            capture_output=True,
            env=environment,
            text=True,
            timeout=300,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise MnistDeltaError("MNIST_DELTA_PROCESS_FAILED") from exc
    if completed.returncode not in expected_codes or completed.stderr:
        raise MnistDeltaError("MNIST_DELTA_PROCESS_FAILED")
    return completed


def _load_demo_signers(controllers_dir: Path) -> tuple[tuple[str, Ed25519PrivateKey], ...]:
    manifest_path = controllers_dir / "demo-controller-manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        raise MnistDeltaError("MNIST_DELTA_CONTROLLER_MANIFEST_INVALID")
    manifest = _load_json(
        manifest_path,
        "MNIST_DELTA_CONTROLLER_MANIFEST_INVALID",
    )
    records = manifest.get("controllers")
    if (
        manifest.get("environment") != "LOCAL_DEMO_ONLY"
        or manifest.get("type_name") != "CAMPAIGN02_DEMO_CONTROLLER_BUNDLE"
        or manifest.get("authoritative") is not False
        or manifest.get("governance_eligible") is not False
        or manifest.get("execution_authorized") is not False
        or manifest.get("valid_for_campaign02_governance") is not False
        or manifest.get("valid_for_demo_testing") is not True
        or manifest.get("formal_semantics_id") != FORMAL_SEMANTICS_ID
        or not isinstance(records, list)
        or len(records) != NODE_COUNT
    ):
        raise MnistDeltaError("MNIST_DELTA_CONTROLLER_MANIFEST_INVALID")
    signers: list[tuple[str, Ed25519PrivateKey]] = []
    controller_ids: set[str] = set()
    signer_ids: set[str] = set()
    public_keys: set[bytes] = set()
    for index, raw_record in enumerate(records, start=1):
        if not isinstance(raw_record, dict):
            raise MnistDeltaError("MNIST_DELTA_CONTROLLER_MANIFEST_INVALID")
        public_key = raw_record.get("public_key_base64")
        public_key_fingerprint = raw_record.get("public_key_raw_sha256")
        controller_id = raw_record.get("controller_id")
        signer_id = raw_record.get("signer_id")
        private_relative = raw_record.get("private_key_file")
        if (
            not isinstance(public_key, str)
            or not isinstance(public_key_fingerprint, str)
            or controller_id != f"demo-campaign02-controller-{index:02d}"
            or signer_id != f"demo-campaign02-signer-{index:02d}"
            or not isinstance(private_relative, str)
            or not isinstance(controller_id, str)
            or not isinstance(signer_id, str)
            or controller_id in controller_ids
            or signer_id in signer_ids
        ):
            raise MnistDeltaError("MNIST_DELTA_CONTROLLER_MANIFEST_INVALID")
        controller_ids.add(controller_id)
        signer_ids.add(signer_id)
        relative = PurePosixPath(private_relative)
        if relative.is_absolute() or ".." in relative.parts or "." in relative.parts:
            raise MnistDeltaError("MNIST_DELTA_CONTROLLER_PRIVATE_PATH_INVALID")
        private_candidate = controllers_dir.joinpath(*relative.parts)
        current = controllers_dir
        for part in relative.parts:
            current /= part
            if current.is_symlink():
                raise MnistDeltaError("MNIST_DELTA_CONTROLLER_PRIVATE_PATH_INVALID")
        private_path = private_candidate.resolve(strict=True)
        if not private_path.is_relative_to(controllers_dir) or not private_path.is_file():
            raise MnistDeltaError("MNIST_DELTA_CONTROLLER_PRIVATE_PATH_INVALID")
        try:
            key = serialization.load_pem_private_key(private_path.read_bytes(), password=None)
            expected_public = base64.b64decode(public_key, validate=True)
        except (OSError, ValueError, TypeError, binascii.Error) as exc:
            raise MnistDeltaError("MNIST_DELTA_CONTROLLER_PRIVATE_KEY_INVALID") from exc
        if not isinstance(key, Ed25519PrivateKey):
            raise MnistDeltaError("MNIST_DELTA_CONTROLLER_PRIVATE_KEY_INVALID")
        if (
            len(expected_public) != 32
            or base64.b64encode(expected_public).decode("ascii") != public_key
            or _content_id(expected_public) != public_key_fingerprint
            or expected_public in public_keys
        ):
            raise MnistDeltaError("MNIST_DELTA_CONTROLLER_PUBLIC_KEY_INVALID")
        public_keys.add(expected_public)
        actual_public = key.public_key().public_bytes(
            serialization.Encoding.Raw,
            serialization.PublicFormat.Raw,
        )
        if actual_public != expected_public:
            raise MnistDeltaError("MNIST_DELTA_CONTROLLER_KEY_MISMATCH")
        signers.append((public_key, key))
    return tuple(signers)


@dataclass(frozen=True, slots=True)
class _RelayEntry:
    source: Path
    destination: PurePosixPath
    signer_index: int


def _run_relay(
    toolchain: DeltaToolchain,
    signers: Sequence[tuple[str, Ed25519PrivateKey]],
    entries: Sequence[_RelayEntry],
    destination_root: Path,
    evidence_root: Path,
    label: str,
) -> dict[str, object]:
    if not entries or len(entries) > MAXIMUM_RELAY_ENTRIES:
        raise MnistDeltaError("MNIST_DELTA_RELAY_EMPTY")
    if not destination_root.is_absolute() or destination_root.is_symlink():
        raise MnistDeltaError("MNIST_DELTA_RELAY_OUTPUT_ROOT_INVALID")
    evidence_root.mkdir(parents=True, exist_ok=True)
    manifest_path = evidence_root / f"{label}.manifest.tsv"
    receipt_relative = PurePosixPath("relay-evidence/receipt.json")
    trace_relative = PurePosixPath("relay-evidence/trace.jsonl")
    receipt_path = destination_root.joinpath(*receipt_relative.parts)
    trace_path = destination_root.joinpath(*trace_relative.parts)
    rows: list[str] = []
    expected: list[dict[str, object]] = []
    sources: set[Path] = set()
    content_ids: set[str] = set()
    destinations: set[PurePosixPath] = set()
    total_bytes = 0
    for entry in entries:
        if entry.signer_index not in range(NODE_COUNT):
            raise MnistDeltaError("MNIST_DELTA_RELAY_SIGNER_INVALID")
        if (
            not entry.source.is_absolute()
            or entry.source.is_symlink()
            or not entry.source.is_file()
        ):
            raise MnistDeltaError("MNIST_DELTA_RELAY_SOURCE_INVALID")
        source = entry.source.resolve(strict=True)
        if source in sources:
            raise MnistDeltaError("MNIST_DELTA_RELAY_SOURCE_DUPLICATE")
        sources.add(source)
        raw = _regular_file_bytes(source, "MNIST_DELTA_RELAY_SOURCE_INVALID")
        total_bytes += len(raw)
        if total_bytes > MAXIMUM_TOTAL_BYTES:
            raise MnistDeltaError("MNIST_DELTA_RELAY_TOTAL_SIZE_INVALID")
        content_id = _content_id(raw)
        if content_id in content_ids:
            raise MnistDeltaError("MNIST_DELTA_RELAY_CONTENT_ID_DUPLICATE")
        content_ids.add(content_id)
        public_key, private_key = signers[entry.signer_index]
        signature = base64.b64encode(private_key.sign(TRANSPORT_SIGNATURE_DOMAIN + raw)).decode(
            "ascii"
        )
        destination_text = entry.destination.as_posix()
        if (
            entry.destination.is_absolute()
            or len(destination_text) > 512
            or not entry.destination.parts
            or any(
                DESTINATION_SEGMENT.fullmatch(part) is None or part in (".", "..")
                for part in entry.destination.parts
            )
            or entry.destination in destinations
        ):
            raise MnistDeltaError("MNIST_DELTA_RELAY_DESTINATION_INVALID")
        destinations.add(entry.destination)
        expected.append(
            {
                "content_id": content_id,
                "destination": destination_text,
                "size_bytes": len(raw),
            }
        )
        line = "\t".join((str(source), destination_text, content_id, public_key, signature))
        if len(line) > MAXIMUM_MANIFEST_LINE_CHARS:
            raise MnistDeltaError("MNIST_DELTA_RELAY_MANIFEST_LINE_INVALID")
        rows.append(line)
    all_targets = (*destinations, receipt_relative, trace_relative)
    if len(set(all_targets)) != len(all_targets) or any(
        left != right
        and (
            left.parts == right.parts[: len(left.parts)]
            or right.parts == left.parts[: len(right.parts)]
        )
        for left in all_targets
        for right in all_targets
    ):
        raise MnistDeltaError("MNIST_DELTA_RELAY_TARGET_COLLISION")
    manifest_bytes = ("\n".join(rows) + "\n").encode("utf-8")
    if len(manifest_bytes) > MAXIMUM_MANIFEST_BYTES:
        raise MnistDeltaError("MNIST_DELTA_RELAY_MANIFEST_SIZE_INVALID")
    _write_new(manifest_path, manifest_bytes)
    completed = _run_process(
        (
            str(toolchain.java_executable),
            "-Dio.netty.noUnsafe=true",
            "-cp",
            toolchain.relay_classpath,
            RELAY_MAIN_CLASS,
            str(manifest_path),
            str(destination_root),
            receipt_relative.as_posix(),
            trace_relative.as_posix(),
        ),
        expected_codes=frozenset({0}),
    )
    receipt_bytes = receipt_path.read_bytes()
    receipt = _load_json(receipt_path, "MNIST_DELTA_RELAY_RECEIPT_INVALID")
    outputs = receipt.get("outputs")
    input_ids = [item["content_id"] for item in expected]
    metrics = receipt.get("metrics")
    pid = receipt.get("pid")
    expected_metrics = {
        "atomic_files_written": len(entries),
        "netty_rx_messages": len(entries),
        "netty_rx_payload_bytes": total_bytes,
        "netty_tx_messages": len(entries),
        "netty_tx_payload_bytes": total_bytes,
    }
    if (
        receipt_bytes != _canonical_bytes(receipt) + b"\n"
        or completed.stdout.encode("utf-8") != receipt_bytes
        or receipt.get("component") != "delta-node-java/netty"
        or receipt.get("type_name") != "MNIST_DELTA_NETTY_RELAY_RECEIPT"
        or receipt.get("schema_version") != "1.0.0"
        or receipt.get("status") != "PASS"
        or receipt.get("transport") != "NETTY_LOOPBACK_TCP"
        or receipt.get("entry_count") != len(entries)
        or not isinstance(pid, int)
        or pid <= 0
        or receipt.get("input_content_ids") != input_ids
        or receipt.get("output_content_ids") != input_ids
        or metrics != expected_metrics
        or not isinstance(outputs, list)
        or len(outputs) != len(entries)
    ):
        raise MnistDeltaError("MNIST_DELTA_RELAY_RECEIPT_INVALID")
    for expected_output, raw_output in zip(expected, outputs, strict=True):
        if not isinstance(raw_output, dict):
            raise MnistDeltaError("MNIST_DELTA_RELAY_RECEIPT_INVALID")
        destination = raw_output.get("destination")
        sha256 = raw_output.get("sha256")
        size_bytes = raw_output.get("size_bytes")
        if (
            not isinstance(destination, str)
            or not isinstance(sha256, str)
            or not isinstance(size_bytes, int)
        ):
            raise MnistDeltaError("MNIST_DELTA_RELAY_RECEIPT_INVALID")
        if raw_output != {
            "destination": expected_output["destination"],
            "sha256": expected_output["content_id"],
            "size_bytes": expected_output["size_bytes"],
        }:
            raise MnistDeltaError("MNIST_DELTA_RELAY_RECEIPT_INVALID")
        persisted = destination_root.joinpath(*PurePosixPath(destination).parts)
        persisted_bytes = _regular_file_bytes(persisted, "MNIST_DELTA_RELAY_PERSISTED_FILE_INVALID")
        if _content_id(persisted_bytes) != sha256 or len(persisted_bytes) != size_bytes:
            raise MnistDeltaError("MNIST_DELTA_RELAY_BYTES_CHANGED")
    _validate_relay_trace(trace_path, expected, pid)
    return receipt


def _validate_relay_trace(path: Path, expected: Sequence[Mapping[str, object]], pid: int) -> None:
    try:
        raw = path.read_bytes()
        text_value = raw.decode("utf-8")
        if not raw.endswith(b"\n") or b"\r" in raw:
            raise MnistDeltaError("MNIST_DELTA_RELAY_TRACE_INVALID")
        lines = text_value.splitlines()
        rows = [json.loads(line) for line in lines]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MnistDeltaError("MNIST_DELTA_RELAY_TRACE_INVALID") from exc
    entry_count = len(expected)
    if len(rows) != entry_count * 4:
        raise MnistDeltaError("MNIST_DELTA_RELAY_TRACE_INVALID")
    expected_rows: list[dict[str, object]] = []
    for item in expected:
        expected_rows.append({"action": "SOURCE_VERIFIED", **item})
    for item in expected:
        for action in ("NETTY_TRANSMITTED", "NETTY_RECEIVED", "ATOMIC_WRITE_VERIFIED"):
            expected_rows.append({"action": action, **item})
    for sequence, (line, row, expected_row) in enumerate(
        zip(lines, rows, expected_rows, strict=True), start=1
    ):
        full_expected = {
            "action": expected_row["action"],
            "component": "delta-node-java/netty",
            "destination": expected_row["destination"],
            "input_content_id": expected_row["content_id"],
            "output_content_id": expected_row["content_id"],
            "pid": pid,
            "sequence": sequence,
            "size_bytes": expected_row["size_bytes"],
            "status": "PASS",
        }
        if row != full_expected or line.encode("utf-8") != _canonical_bytes(full_expected):
            raise MnistDeltaError("MNIST_DELTA_RELAY_TRACE_INVALID")


def _native_command(
    toolchain: DeltaToolchain,
    mode: str,
    *,
    workload: Path,
    contributions_root: Path,
    node_dir: Path,
    validator_id: str,
    result_path: Path,
    phase: str | None = None,
    votes_root: Path | None = None,
    qcs_root: Path | None = None,
    qc_output: Path | None = None,
    applied_model: Path | None = None,
    crash: bool = False,
) -> tuple[str, ...]:
    command = [
        str(toolchain.native_executable),
        mode,
        "--workload",
        str(workload),
        "--contributions-root",
        str(contributions_root),
        "--node-dir",
        str(node_dir),
        "--validator-id",
        validator_id,
        "--result",
        str(result_path),
    ]
    if phase is not None:
        command.extend(("--phase", phase))
    if votes_root is not None:
        command.extend(("--votes-root", str(votes_root)))
    if qcs_root is not None:
        command.extend(("--qcs-root", str(qcs_root)))
    if qc_output is not None:
        command.extend(("--qc-output", str(qc_output)))
    if applied_model is not None:
        command.extend(("--applied-model", str(applied_model)))
    if crash:
        command.extend(("--crash-after-durable-vote", "apply"))
    return tuple(command)


def _validate_common_native_result(
    value: Mapping[str, object],
    validator_id: str,
    workload_id: str,
    source_id: str,
    contribution_ids: Sequence[str],
) -> None:
    expected_round_id = f"mnist-demo-{workload_id[7:27]}"
    if (
        value.get("schema_version") != "1.0.0"
        or value.get("classification") != "LOCAL_DEMO_ONLY"
        or value.get("authoritative") is not False
        or value.get("governance_eligible") is not False
        or value.get("formal_semantics_id") != FORMAL_SEMANTICS_ID
        or value.get("validator_id") != validator_id
        or value.get("workload_id") != workload_id
        or value.get("node_count") != NODE_COUNT
        or value.get("vector_width") != VECTOR_WIDTH
        or value.get("cryptographic_signatures_verified") is not False
        or value.get("signature_semantics") != "CONTENT_ID_PLACEHOLDER_LOCAL_DEMO_ONLY"
        or value.get("height") != 1
        or value.get("view") != 0
        or value.get("round_id") != expected_round_id
        or value.get("source_id") != source_id
        or value.get("contribution_ids") != list(contribution_ids)
    ):
        raise MnistDeltaError("MNIST_DELTA_NATIVE_RESULT_INVALID")
    result_id = _require_content_id(value.get("result_id"), "MNIST_DELTA_NATIVE_RESULT_ID_INVALID")
    body = {key: item for key, item in value.items() if key != "result_id"}
    if result_id != _derived_content_id(
        "deltareduce.demo.mnist.result.v1",
        (_canonical_bytes(body).decode("utf-8"),),
    ):
        raise MnistDeltaError("MNIST_DELTA_NATIVE_RESULT_ID_INVALID")


def _validate_body_ids(value: Mapping[str, object]) -> dict[str, object]:
    body_ids = value.get("body_ids")
    if not isinstance(body_ids, dict) or tuple(sorted(body_ids)) != tuple(
        sorted(REQUIRED_VOTE_KINDS)
    ):
        raise MnistDeltaError("MNIST_DELTA_NATIVE_BODY_IDS_INVALID")
    checked_body_ids = [
        _require_content_id(body_id, "MNIST_DELTA_NATIVE_BODY_ID_INVALID")
        for body_id in body_ids.values()
    ]
    if len(set(checked_body_ids)) != len(REQUIRED_VOTE_KINDS):
        raise MnistDeltaError("MNIST_DELTA_NATIVE_BODY_ID_INVALID")
    return cast(dict[str, object], body_ids)


def _validate_native_result_file(path: Path, value: Mapping[str, object], code: str) -> None:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise MnistDeltaError(code) from exc
    if raw != _canonical_bytes(value) + b"\n":
        raise MnistDeltaError(code)


def _validate_native_file_reference(
    value: object, node_dir: Path, expected_file: str, code: str
) -> None:
    if not isinstance(value, dict) or set(value) != {"file", "sha256"}:
        raise MnistDeltaError(code)
    filename = value.get("file")
    digest = value.get("sha256")
    if filename != expected_file or not isinstance(digest, str):
        raise MnistDeltaError(code)
    relative = PurePosixPath(filename)
    if (
        relative.is_absolute()
        or not relative.parts
        or any(part in (".", "..") for part in relative.parts)
    ):
        raise MnistDeltaError(code)
    path = node_dir.joinpath(*relative.parts)
    try:
        resolved_node = node_dir.resolve(strict=True)
        resolved_path = path.resolve(strict=True)
    except OSError as exc:
        raise MnistDeltaError(code) from exc
    if not resolved_path.is_relative_to(resolved_node):
        raise MnistDeltaError(code)
    raw = _regular_file_bytes(resolved_path, code, maximum=16 << 20)
    if _content_id(raw) != digest:
        raise MnistDeltaError(code)


def _validate_vote_phase_result(
    value: Mapping[str, object],
    validator_id: str,
    workload_id: str,
    source_id: str,
    contribution_ids: Sequence[str],
    node_dir: Path,
    result_path: Path,
    phase_index: int,
    expected_parent_qc_ids: Sequence[str],
    *,
    crash: bool,
) -> None:
    phase, trace_kind, _vote_action = TRACE_PHASES[phase_index]
    expected_fields = VOTE_PHASE_RESULT_FIELDS | ({"crashed_vote"} if crash else {"vote_frame"})
    if set(value) != expected_fields:
        raise MnistDeltaError("MNIST_DELTA_VOTE_PHASE_RESULT_INVALID")
    _validate_common_native_result(value, validator_id, workload_id, source_id, contribution_ids)
    _validate_native_result_file(result_path, value, "MNIST_DELTA_VOTE_PHASE_RESULT_INVALID")
    expected_status = "SIMULATED_CRASH" if crash else "VOTE_EXPOSED"
    if (
        value.get("type_name") != "MNIST_DELTA_VOTE_PHASE_RESULT"
        or value.get("status") != expected_status
        or value.get("mode") != "vote-phase"
        or value.get("phase") != phase
    ):
        raise MnistDeltaError("MNIST_DELTA_VOTE_PHASE_RESULT_INVALID")
    parent_ids = value.get("validated_parent_qc_ids")
    if (
        not isinstance(parent_ids, list)
        or parent_ids != list(expected_parent_qc_ids)
        or len(parent_ids) != phase_index
    ):
        raise MnistDeltaError("MNIST_DELTA_VOTE_PHASE_RESULT_INVALID")
    for parent_id in parent_ids:
        _require_content_id(parent_id, "MNIST_DELTA_VOTE_PHASE_RESULT_INVALID")
    _validate_native_file_reference(
        value.get("runtime_wal"),
        node_dir,
        "runtime/runtime.wal",
        "MNIST_DELTA_RUNTIME_WAL_INVALID",
    )
    _validate_native_file_reference(
        value.get("vote_wal"),
        node_dir,
        "votes/runtime.wal",
        "MNIST_DELTA_VOTE_WAL_INVALID",
    )
    if crash:
        crashed_vote = value.get("crashed_vote")
        if (
            value.get("recovery_required") is not True
            or value.get("recovered_vote_count") != phase_index + 1
            or not isinstance(crashed_vote, dict)
            or set(crashed_vote) != {"body_hash", "context_id", "durable_sequence", "kind"}
            or crashed_vote.get("kind") != phase
            or crashed_vote.get("context_id") != f"{trace_kind}:{value['round_id']}:1:0"
            or crashed_vote.get("durable_sequence") != phase_index + 1
        ):
            raise MnistDeltaError("MNIST_DELTA_CRASH_NOT_DURABLE")
        _require_content_id(crashed_vote.get("body_hash"), "MNIST_DELTA_CRASH_NOT_DURABLE")
        return
    expected_replay = validator_id == "validator-04" and phase == "apply"
    expected_recovered = phase_index + 1 if expected_replay else phase_index
    frame = value.get("vote_frame")
    if (
        value.get("recovery_required") is not False
        or value.get("recovered_vote_count") != expected_recovered
        or not isinstance(frame, dict)
        or set(frame)
        != {"body_hash", "context_id", "durable_sequence", "file", "kind", "replay", "sha256"}
        or frame.get("kind") != phase
        or frame.get("durable_sequence") != phase_index + 1
        or frame.get("context_id") != f"{trace_kind}:{value['round_id']}:1:0"
        or frame.get("file") != f"vote-frames/{phase}.vote"
        or frame.get("replay") is not expected_replay
    ):
        raise MnistDeltaError("MNIST_DELTA_VOTE_PHASE_RESULT_INVALID")
    _require_content_id(frame.get("body_hash"), "MNIST_DELTA_VOTE_PHASE_RESULT_INVALID")
    _validate_native_file_reference(
        {"file": frame["file"], "sha256": frame.get("sha256")},
        node_dir,
        f"vote-frames/{phase}.vote",
        "MNIST_DELTA_VOTE_FRAME_INVALID",
    )


def _validate_certify_phase_result(
    value: Mapping[str, object],
    validator_id: str,
    workload_id: str,
    source_id: str,
    contribution_ids: Sequence[str],
    qcs_root: Path,
    result_path: Path,
    phase_index: int,
    expected_parent_qc_ids: Sequence[str],
) -> None:
    phase, trace_kind, _vote_action = TRACE_PHASES[phase_index]
    if set(value) != CERTIFY_PHASE_RESULT_FIELDS:
        raise MnistDeltaError("MNIST_DELTA_CERTIFY_PHASE_RESULT_INVALID")
    _validate_common_native_result(value, validator_id, workload_id, source_id, contribution_ids)
    _validate_native_result_file(result_path, value, "MNIST_DELTA_CERTIFY_PHASE_RESULT_INVALID")
    parent_ids = value.get("validated_parent_qc_ids")
    certificate = value.get("quorum_certificate")
    if (
        value.get("type_name") != "MNIST_DELTA_CERTIFY_PHASE_RESULT"
        or value.get("status") != "QC_FINALIZED"
        or value.get("mode") != "certify-phase"
        or value.get("phase") != phase
        or not isinstance(parent_ids, list)
        or parent_ids != list(expected_parent_qc_ids)
        or len(parent_ids) != phase_index
        or not isinstance(certificate, dict)
        or set(certificate)
        != {"body_hash", "context_id", "kind", "qc_id", "signer_count", "threshold"}
        or certificate.get("kind") != phase
        or certificate.get("context_id") != f"{trace_kind}:{value['round_id']}:1:0"
        or certificate.get("signer_count") != NODE_COUNT
        or certificate.get("threshold") != 3
    ):
        raise MnistDeltaError("MNIST_DELTA_CERTIFY_PHASE_RESULT_INVALID")
    for parent_id in parent_ids:
        _require_content_id(parent_id, "MNIST_DELTA_CERTIFY_PHASE_RESULT_INVALID")
    typed_certificate_id = _require_content_id(
        certificate.get("body_hash"), "MNIST_DELTA_CERTIFY_PHASE_RESULT_INVALID"
    )
    vote_quorum_id = _require_content_id(
        certificate.get("qc_id"), "MNIST_DELTA_CERTIFY_PHASE_RESULT_INVALID"
    )
    if typed_certificate_id == vote_quorum_id:
        raise MnistDeltaError("MNIST_DELTA_TYPED_CERTIFICATE_QUORUM_ID_CONFLATED")
    _validate_native_file_reference(
        value.get("qc_artifact"),
        qcs_root,
        f"{phase}.qc",
        "MNIST_DELTA_QC_ARTIFACT_INVALID",
    )


def _validate_finalize_result(
    value: Mapping[str, object],
    validator_id: str,
    workload_id: str,
    source_id: str,
    contribution_ids: Sequence[str],
    model: AppliedModel,
    node_dir: Path,
    result_path: Path,
) -> None:
    if set(value) != FINALIZE_RESULT_FIELDS:
        raise MnistDeltaError("MNIST_DELTA_FINALIZE_RESULT_INVALID")
    _validate_common_native_result(value, validator_id, workload_id, source_id, contribution_ids)
    body_ids = _validate_body_ids(value)
    _validate_native_result_file(result_path, value, "MNIST_DELTA_FINALIZE_RESULT_INVALID")
    model_artifact = value.get("model_artifact")
    pointer = value.get("current_pointer")
    certificates = value.get("quorum_certificates")
    if (
        value.get("type_name") != "MNIST_DELTA_FINALIZE_RESULT"
        or value.get("status") != "APPLIED"
        or value.get("mode") != "finalize"
        or not isinstance(model_artifact, dict)
        or model_artifact.get("format") != MODEL_FORMAT
        or model_artifact.get("sha256") != model.content_id
        or model_artifact.get("bytes") != len(model.raw_bytes)
        or model_artifact.get("width") != VECTOR_WIDTH
        or model_artifact.get("file") != "applied-model.bin"
        or not isinstance(pointer, dict)
        or pointer.get("disposition") != "ADVANCED"
        or not isinstance(certificates, list)
        or len(certificates) != len(REQUIRED_VOTE_KINDS)
    ):
        raise MnistDeltaError("MNIST_DELTA_FINALIZE_RESULT_INVALID")
    kinds = tuple(item.get("kind") for item in certificates if isinstance(item, dict))
    if kinds != REQUIRED_VOTE_KINDS:
        raise MnistDeltaError("MNIST_DELTA_FINALIZE_RESULT_INVALID")
    if (
        value.get("aggregate_root_qc_id") != body_ids["aggregate_root"]
        or value.get("apply_qc_id") != body_ids["apply"]
        or set(model_artifact) != {"bytes", "file", "format", "sha256", "width"}
    ):
        raise MnistDeltaError("MNIST_DELTA_FINALIZE_RESULT_INVALID")
    qc_ids: list[str] = []
    for kind, certificate in zip(REQUIRED_VOTE_KINDS, certificates, strict=True):
        trace_kind = TRACE_PHASES[REQUIRED_VOTE_KINDS.index(kind)][1]
        if (
            not isinstance(certificate, dict)
            or set(certificate)
            != {"body_hash", "context_id", "kind", "qc_id", "signer_count", "threshold"}
            or certificate.get("kind") != kind
            or certificate.get("body_hash") != body_ids[kind]
            or certificate.get("signer_count") != NODE_COUNT
            or certificate.get("threshold") != 3
            or certificate.get("context_id") != f"{trace_kind}:{value['round_id']}:1:0"
        ):
            raise MnistDeltaError("MNIST_DELTA_FINALIZE_RESULT_INVALID")
        typed_certificate_id = _require_content_id(
            certificate.get("body_hash"), "MNIST_DELTA_FINALIZE_TYPED_CERTIFICATE_ID_INVALID"
        )
        vote_quorum_id = _require_content_id(
            certificate.get("qc_id"), "MNIST_DELTA_FINALIZE_QC_ID_INVALID"
        )
        if typed_certificate_id == vote_quorum_id:
            raise MnistDeltaError("MNIST_DELTA_TYPED_CERTIFICATE_QUORUM_ID_CONFLATED")
        qc_ids.append(vote_quorum_id)
    if len(set(qc_ids)) != len(REQUIRED_VOTE_KINDS):
        raise MnistDeltaError("MNIST_DELTA_FINALIZE_QC_ID_INVALID")
    for field in (
        "aggregate_root_qc_id",
        "apply_candidate_id",
        "apply_qc_id",
        "model_hash",
        "optimizer_hash",
    ):
        _require_content_id(value.get(field), "MNIST_DELTA_FINALIZE_ID_INVALID")
    for field, expected_file, code in (
        ("runtime_wal", "runtime/runtime.wal", "MNIST_DELTA_RUNTIME_WAL_INVALID"),
        ("vote_wal", "votes/runtime.wal", "MNIST_DELTA_VOTE_WAL_INVALID"),
        (
            "current_pointer_wal",
            "current/current-pointer.wal",
            "MNIST_DELTA_POINTER_WAL_INVALID",
        ),
    ):
        _validate_native_file_reference(value.get(field), node_dir, expected_file, code)
    if not isinstance(pointer, dict) or set(pointer) != {
        "apply_qc_id",
        "checkpoint_id",
        "disposition",
        "height",
        "optimizer_id",
    }:
        raise MnistDeltaError("MNIST_DELTA_FINALIZE_RESULT_INVALID")
    if (
        pointer.get("apply_qc_id") != value.get("apply_qc_id")
        or pointer.get("checkpoint_id") != value.get("model_hash")
        or pointer.get("optimizer_id") != value.get("optimizer_hash")
        or pointer.get("height") != 1
    ):
        raise MnistDeltaError("MNIST_DELTA_FINALIZE_RESULT_INVALID")


def _collect_native_trace(
    path: Path,
    validator_id: str,
    vote_results: Sequence[Mapping[str, object]],
    certify_results: Sequence[Mapping[str, object]],
    finalize_result: Mapping[str, object],
    *,
    expect_crash: bool,
) -> list[dict[str, object]]:
    """Validate the exact compute/vote, transport-fed QC, and successor order."""
    if len(vote_results) != len(TRACE_PHASES) or len(certify_results) != len(TRACE_PHASES):
        raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
    body_ids = _validate_body_ids(finalize_result)
    qc_ids: list[str] = []
    for index, (vote_result, certify_result) in enumerate(
        zip(vote_results, certify_results, strict=True)
    ):
        phase = TRACE_PHASES[index][0]
        frame = vote_result.get("vote_frame")
        certificate = certify_result.get("quorum_certificate")
        if (
            not isinstance(frame, dict)
            or not isinstance(certificate, dict)
            or frame.get("body_hash") != body_ids[phase]
            or certificate.get("body_hash") != body_ids[phase]
            or vote_result.get("validated_parent_qc_ids") != qc_ids
            or certify_result.get("validated_parent_qc_ids") != qc_ids
        ):
            raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
        vote_quorum_id = _require_content_id(
            certificate.get("qc_id"), "MNIST_DELTA_NATIVE_TRACE_INVALID"
        )
        if vote_quorum_id == body_ids[phase]:
            raise MnistDeltaError("MNIST_DELTA_TYPED_CERTIFICATE_QUORUM_ID_CONFLATED")
        qc_ids.append(vote_quorum_id)
    final_certificates = finalize_result.get("quorum_certificates")
    if (
        not isinstance(final_certificates, list)
        or [item.get("qc_id") for item in final_certificates if isinstance(item, dict)] != qc_ids
    ):
        raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")

    try:
        raw = path.read_bytes()
        if not raw.endswith(b"\n") or b"\r" in raw:
            raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
        lines = raw.decode("utf-8").splitlines()
        parsed = [json.loads(line) for line in lines]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID") from exc
    rows: list[dict[str, object]] = []
    round_id = str(finalize_result.get("round_id"))
    for line, value in zip(lines, parsed, strict=True):
        if (
            not isinstance(value, dict)
            or set(value) != NATIVE_TRACE_FIELDS
            or line.encode("utf-8") != _canonical_bytes(value)
            or value.get("type_name") != "MNIST_DELTA_DEMO_TRACE"
            or value.get("schema_version") != "1.0.0"
            or value.get("classification") != "LOCAL_DEMO_ONLY"
            or value.get("authoritative") is not False
            or value.get("governance_eligible") is not False
            or value.get("formal_semantics_id") != FORMAL_SEMANTICS_ID
            or value.get("validator_id") != validator_id
            or value.get("round_id") != round_id
            or value.get("height") != 1
            or value.get("view") != 0
            or value.get("mode") not in ("vote-phase", "certify-phase", "finalize")
            or not isinstance(value.get("action_id"), str)
            or not isinstance(value.get("event"), str)
            or not isinstance(value.get("outcome"), str)
            or not isinstance(value.get("durable_sequence"), int)
            or not isinstance(value.get("replay"), bool)
        ):
            raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
        for content_field in ("body_hash", "result_hash"):
            content_value = value.get(content_field)
            if content_value is not None:
                _require_content_id(content_value, "MNIST_DELTA_NATIVE_TRACE_INVALID")
        if value.get("error_code") is not None and value.get("event") != "simulated_crash":
            raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
        rows.append(cast(dict[str, object], value))
    if not rows:
        raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")

    starts = [index for index, row in enumerate(rows) if row.get("event") == "mode_started"]
    segments = [
        rows[start : starts[index + 1] if index + 1 < len(starts) else len(rows)]
        for index, start in enumerate(starts)
    ]
    expected_calls: list[tuple[str, int, bool]] = []
    for phase_index in range(len(TRACE_PHASES)):
        if expect_crash and phase_index == len(TRACE_PHASES) - 1:
            expected_calls.append(("vote-phase", phase_index, True))
        expected_calls.append(("vote-phase", phase_index, False))
        expected_calls.append(("certify-phase", phase_index, False))
    expected_calls.append(("finalize", len(TRACE_PHASES), False))
    if len(segments) != len(expected_calls):
        raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")

    durable_vote_ids: list[str] = []
    crashed_apply_vote_id: str | None = None
    proposal_event_names = frozenset(
        {
            "aggregate_root_assembled",
            "apply_computed",
            "input_set_closed",
            "parameter_shard_reduced",
            "seed_generated",
            "typed_certificate_materialized",
        }
    )
    for segment, (mode, phase_index, crash_segment) in zip(segments, expected_calls, strict=True):
        started = segment[0]
        if (
            started.get("mode") != mode
            or started.get("action_id") != "OBS-POST-CONFIG-SUBTRACE-START"
            or started.get("outcome") != "ACCEPTED"
            or any(row.get("mode") != mode for row in segment)
        ):
            raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
        completions = [row for row in segment if row.get("event") == "mode_complete"]
        parent_count = len(TRACE_PHASES) if mode == "finalize" else phase_index
        expected_quorum_ids = qc_ids[:parent_count]
        if mode == "certify-phase":
            expected_quorum_ids = [*expected_quorum_ids, qc_ids[phase_index]]
        quorum_rows = [row for row in segment if row.get("event") == "quorum_validated"]
        vote_quorum_rows = [row for row in segment if row.get("event") == "vote_quorum_validated"]
        verifier_rows = [row for row in segment if row.get("event") == "chain_verifier_verified"]
        if [row.get("result_hash") for row in quorum_rows] != expected_quorum_ids or len(
            verifier_rows
        ) != len(expected_quorum_ids):
            raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
        for parent_index in range(parent_count):
            quorum_row = quorum_rows[parent_index]
            verifier_row = verifier_rows[parent_index]
            parent_phase, parent_kind, _vote_action = TRACE_PHASES[parent_index]
            if (
                quorum_row.get("action_id") != "OBS-PARENT-QC-VALIDATED"
                or quorum_row.get("vote_kind") != parent_kind
                or quorum_row.get("body_hash") != body_ids[parent_phase]
                or quorum_row.get("result_hash") != qc_ids[parent_index]
                or quorum_row.get("outcome") != "VALIDATED_PARENT"
                or quorum_row.get("replay") is not False
                or verifier_row.get("action_id") != "OBS-TYPED-CERT-VERIFIED-AFTER-QC"
                or verifier_row.get("vote_kind") != parent_kind
                or verifier_row.get("body_hash") != body_ids[parent_phase]
                or verifier_row.get("result_hash") != body_ids[parent_phase]
                or verifier_row.get("outcome") != "ACCEPTED"
                or verifier_row.get("replay") is not False
                or segment.index(quorum_row) >= segment.index(verifier_row)
            ):
                raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")

        if mode == "finalize":
            pointer_rows = [row for row in segment if row.get("event") == "current_pointer_applied"]
            if (
                vote_quorum_rows
                or len(completions) != 1
                or completions[0] is not segment[-1]
                or completions[0].get("action_id") != "OBS-POST-CONFIG-SUBTRACE-COMPLETE"
                or completions[0].get("outcome") != "APPLIED"
                or completions[0].get("result_hash") != finalize_result.get("model_hash")
                or len(pointer_rows) != 1
                or pointer_rows[0].get("action_id") != "ACT-CURRENT-ADVANCE"
                or pointer_rows[0].get("body_hash") != finalize_result.get("apply_qc_id")
                or pointer_rows[0].get("result_hash") != finalize_result.get("model_hash")
            ):
                raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
            continue

        phase, trace_kind, vote_action = TRACE_PHASES[phase_index]
        if started.get("vote_kind") != trace_kind:
            raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
        proposal_rows = [row for row in segment if row.get("event") in proposal_event_names]
        if mode == "vote-phase":
            replayed_current_vote = expect_crash and phase == "apply" and not crash_segment
            expected_proposals = {
                "input_set": (("input_set_closed", "ACT-INPUT-CLOSE"),),
                "eligibility": (
                    ("seed_generated", "ACT-SEED-GENERATE"),
                    ("typed_certificate_materialized", "OBS-EC-BODY-MATERIALIZED"),
                ),
                "aggregation_plan": (
                    (
                        "typed_certificate_materialized",
                        "OBS-AGGREGATION-PLAN-COMPUTED",
                    ),
                ),
                "parameter_shard": (("parameter_shard_reduced", "ACT-PARAM-PROPOSE"),),
                "aggregate_root": (("aggregate_root_assembled", "ACT-ROOT-ASSEMBLE"),),
                "apply": (
                    (
                        "apply_computed",
                        (
                            "OBS-APPLY-CANDIDATE-RECONSTRUCTED"
                            if replayed_current_vote
                            else "ACT-APPLY-COMPUTE"
                        ),
                    ),
                    (
                        "typed_certificate_materialized",
                        (
                            "OBS-APPLY-BODY-RECONSTRUCTED"
                            if replayed_current_vote
                            else "OBS-APPLY-BODY-MATERIALIZED"
                        ),
                    ),
                ),
            }[phase]
            if (
                vote_quorum_rows
                or tuple((row.get("event"), row.get("action_id")) for row in proposal_rows)
                != expected_proposals
                or any(row.get("replay") is not replayed_current_vote for row in proposal_rows)
                or any(
                    row.get("outcome") != ("NO_OP" if replayed_current_vote else "ACCEPTED")
                    for row in proposal_rows
                )
            ):
                raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
            if proposal_rows[-1].get("result_hash") != body_ids[phase]:
                raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
            if phase == "apply" and (
                proposal_rows[0].get("result_hash") != finalize_result.get("apply_candidate_id")
                or proposal_rows[1].get("body_hash") != finalize_result.get("apply_candidate_id")
            ):
                raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
            if quorum_rows and segment.index(quorum_rows[-1]) >= segment.index(proposal_rows[0]):
                raise MnistDeltaError("MNIST_DELTA_PHASE_ORDER_INVALID")

            replay_rows = [
                row for row in segment if row.get("event") == "predecessor_vote_replay_verified"
            ]
            journal_rows = [row for row in segment if row.get("event") == "journal_recovered"]
            durable_rows = [
                row for row in segment if row.get("event") == "vote_durable_and_exposed"
            ]
            if crash_segment:
                crash_rows = [row for row in segment if row.get("event") == "simulated_crash"]
                restart_rows = [row for row in segment if row.get("event") == "runtime_restarted"]
                recovery_rows = [
                    row for row in segment if row.get("event") == "journal_recovery_verified"
                ]
                if (
                    completions
                    or durable_rows
                    or len(journal_rows) != 1
                    or len(replay_rows) != phase_index * 2 + 1
                    or [row.get("result_hash") for row in replay_rows[:phase_index]]
                    != durable_vote_ids
                    or [row.get("result_hash") for row in replay_rows[phase_index:-1]]
                    != durable_vote_ids
                    or len(crash_rows) != 1
                    or len(restart_rows) != 1
                    or len(recovery_rows) != 1
                    or crash_rows[0].get("body_hash") != body_ids[phase]
                    or crash_rows[0].get("error_code") != "SIMULATED_CRASH_AFTER_DURABILITY"
                    or crash_rows[0].get("outcome") != "DURABLE_NOT_EXPOSED"
                    or recovery_rows[0].get("replay") is not True
                    or not (
                        segment.index(proposal_rows[-1])
                        < segment.index(crash_rows[0])
                        < segment.index(restart_rows[0])
                        < segment.index(recovery_rows[0])
                    )
                ):
                    raise MnistDeltaError("MNIST_DELTA_CRASH_RECOVERY_TRACE_INVALID")
                crashed_apply_vote_id = _require_content_id(
                    replay_rows[-1].get("result_hash"),
                    "MNIST_DELTA_CRASH_RECOVERY_TRACE_INVALID",
                )
                continue
            expected_replay = replayed_current_vote
            if (
                len(completions) != 1
                or completions[0] is not segment[-1]
                or completions[0].get("action_id") != "OBS-POST-CONFIG-SUBTRACE-COMPLETE"
                or completions[0].get("outcome") != "VOTE_EXPOSED"
                or completions[0].get("replay") is not expected_replay
                or len(replay_rows) != phase_index
                or [row.get("result_hash") for row in replay_rows] != durable_vote_ids
                or len(journal_rows) != (1 if phase_index > 0 else 0)
                or len(durable_rows) != 1
                or durable_rows[0].get("action_id") != vote_action
                or durable_rows[0].get("body_hash") != body_ids[phase]
                or durable_rows[0].get("durable_sequence") != phase_index + 1
                or durable_rows[0].get("replay") is not expected_replay
                or durable_rows[0].get("outcome") != ("NO_OP" if expected_replay else "ACCEPTED")
                or segment.index(proposal_rows[-1]) >= segment.index(durable_rows[0])
            ):
                raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
            current_vote_id = _require_content_id(
                durable_rows[0].get("result_hash"), "MNIST_DELTA_NATIVE_TRACE_INVALID"
            )
            if expected_replay and current_vote_id != crashed_apply_vote_id:
                raise MnistDeltaError("MNIST_DELTA_CRASH_RECOVERY_TRACE_INVALID")
            durable_vote_ids.append(current_vote_id)
        else:
            current_verifier = verifier_rows[-1]
            current_quorum = quorum_rows[-1]
            current_vote_quorum = vote_quorum_rows[0] if vote_quorum_rows else None
            if (
                proposal_rows
                or len(completions) != 1
                or completions[0] is not segment[-1]
                or completions[0].get("action_id") != "OBS-POST-CONFIG-SUBTRACE-COMPLETE"
                or completions[0].get("outcome") != "QC_FINALIZED"
                or not isinstance(current_vote_quorum, dict)
                or current_verifier.get("action_id") != "OBS-TYPED-CERT-VERIFIED-AFTER-QC"
                or current_verifier.get("vote_kind") != trace_kind
                or current_verifier.get("body_hash") != body_ids[phase]
                or current_verifier.get("result_hash") != body_ids[phase]
                or len(vote_quorum_rows) != 1
                or current_vote_quorum.get("action_id") != "OBS-CURRENT-VOTE-QUORUM-VALIDATED"
                or current_vote_quorum.get("vote_kind") != trace_kind
                or current_vote_quorum.get("body_hash") != body_ids[phase]
                or current_vote_quorum.get("result_hash") != qc_ids[phase_index]
                or current_vote_quorum.get("outcome") != "VALIDATED"
                or current_quorum.get("action_id") != "OBS-CURRENT-QC-DURABLY-FINALIZED"
                or current_quorum.get("body_hash") != body_ids[phase]
                or current_quorum.get("result_hash") != qc_ids[phase_index]
                or current_quorum.get("outcome") not in ("FINALIZED", "NO_OP")
                or current_quorum.get("replay") is not (current_quorum.get("outcome") == "NO_OP")
                or not (
                    segment.index(current_vote_quorum)
                    < segment.index(current_verifier)
                    < segment.index(current_quorum)
                )
            ):
                raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")

    expected_event_counts = {
        "aggregate_root_assembled": 1,
        "apply_computed": 2 if expect_crash else 1,
        "chain_verifier_verified": 47 if expect_crash else 42,
        "current_pointer_applied": 1,
        "input_set_closed": 1,
        "journal_recovered": 6 if expect_crash else 5,
        "mode_complete": 13,
        "mode_started": 14 if expect_crash else 13,
        "parameter_shard_reduced": 1,
        "predecessor_vote_replay_verified": 26 if expect_crash else 15,
        "quorum_validated": 47 if expect_crash else 42,
        "runtime_transition": 10,
        "seed_generated": 1,
        "typed_certificate_materialized": 4 if expect_crash else 3,
        "vote_quorum_validated": len(TRACE_PHASES),
        "vote_durable_and_exposed": len(TRACE_PHASES),
    }
    if expect_crash:
        expected_event_counts.update(
            {
                "journal_recovery_verified": 1,
                "runtime_restarted": 1,
                "simulated_crash": 1,
            }
        )
    if Counter(str(row["event"]) for row in rows) != expected_event_counts:
        raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
    return rows


def _logical_result(value: Mapping[str, object]) -> dict[str, object]:
    """Drop observations that must not enter a deterministic execution identity."""
    excluded = {"pid", "duration_ms"}
    return {key: item for key, item in value.items() if key not in excluded}


def _write_execution_evidence(
    destination: Path,
    workload_id: str,
    contributions: Sequence[NodeContribution],
    transport_receipts: Sequence[Mapping[str, object]],
    vote_results: Sequence[Mapping[str, object]],
    certify_results: Sequence[Mapping[str, object]],
    finalize_results: Sequence[Mapping[str, object]],
    native_traces: Mapping[str, Sequence[Mapping[str, object]]],
    toolchain_document: Mapping[str, object],
    model: AppliedModel,
) -> tuple[dict[str, object], Path, Path]:
    source_snapshot = toolchain_document.get("source_snapshot")
    if not isinstance(source_snapshot, dict):
        raise MnistDeltaError("MNIST_DELTA_SOURCE_SNAPSHOT_INVALID")
    raw_source_files = source_snapshot.get("files")
    if not isinstance(raw_source_files, list):
        raise MnistDeltaError("MNIST_DELTA_SOURCE_SNAPSHOT_INVALID")
    source_ids: dict[str, str] = {}
    for item in raw_source_files:
        if not isinstance(item, dict):
            raise MnistDeltaError("MNIST_DELTA_SOURCE_SNAPSHOT_INVALID")
        path = item.get("path")
        content_id = item.get("content_id")
        if not isinstance(path, str) or not isinstance(content_id, str):
            raise MnistDeltaError("MNIST_DELTA_SOURCE_SNAPSHOT_INVALID")
        source_ids[path] = _require_content_id(content_id, "MNIST_DELTA_SOURCE_SNAPSHOT_INVALID")
    if set(source_ids) != set(SOURCE_SNAPSHOT_FILES):
        raise MnistDeltaError("MNIST_DELTA_SOURCE_SNAPSHOT_INVALID")

    transport_receipt_ids = [
        _content_id(_canonical_bytes(_logical_result(receipt))) for receipt in transport_receipts
    ]
    native_trace_ids = {
        validator_id: _content_id(b"".join(_canonical_bytes(row) + b"\n" for row in rows))
        for validator_id, rows in native_traces.items()
    }
    observed_vote_events = sum(
        row.get("event") == "vote_durable_and_exposed"
        for rows in native_traces.values()
        for row in rows
    )
    observed_quorum_events = sum(
        row.get("event") == "quorum_validated" for rows in native_traces.values() for row in rows
    )
    observed_vote_quorum_events = sum(
        row.get("event") == "vote_quorum_validated"
        for rows in native_traces.values()
        for row in rows
    )
    observed_typed_certificate_events = sum(
        row.get("event") == "chain_verifier_verified"
        for rows in native_traces.values()
        for row in rows
    )
    observed_certified_phases = sum(
        row.get("event") == "mode_complete"
        and row.get("mode") == "certify-phase"
        and row.get("outcome") == "QC_FINALIZED"
        for rows in native_traces.values()
        for row in rows
    )

    def component_validators(event: str, vote_kind: str | None = None) -> set[str]:
        return {
            validator_id
            for validator_id, rows in native_traces.items()
            if any(
                row.get("mode") == "vote-phase"
                and row.get("event") == event
                and (vote_kind is None or row.get("vote_kind") == vote_kind)
                for row in rows
            )
        }

    def source(path: str) -> str:
        return source_ids[path]

    def observed(condition: bool, code: str) -> str:
        if not condition:
            raise MnistDeltaError(code)
        return "PASS"

    def nested(item: Mapping[str, object], field: str, nested_field: str) -> object:
        value = item.get(field)
        return value.get(nested_field) if isinstance(value, dict) else None

    components: list[dict[str, object]] = [
        {
            "component": "deltatorrent.benchmark.mnist_demo",
            "evidence": {
                "contribution_ids": [item.content_id for item in contributions],
                "source_ids": [
                    source("delta-worker-python/src/deltatorrent/benchmark/mnist_demo.py"),
                    source("delta-worker-python/src/deltatorrent/benchmark/mnist_delta_nodes.py"),
                ],
            },
            "implementation_class": "DEMO_WORKLOAD_ADAPTER",
            "sequence": 1,
            "status": observed(
                len(contributions) == NODE_COUNT,
                "MNIST_DELTA_WORKLOAD_COMPONENT_NOT_OBSERVED",
            ),
        },
        {
            "component": "io.deltareduce.demo.MnistDeltaNettyRelay",
            "evidence": {
                "vote_delivery_count": NODE_COUNT * NODE_COUNT * len(REQUIRED_VOTE_KINDS),
                "vote_relay_receipt_count": NODE_COUNT * len(REQUIRED_VOTE_KINDS),
                "votes_delivered_per_phase_receiver": NODE_COUNT,
                "receipt_ids": transport_receipt_ids,
                "source_ids": [
                    source(
                        "integration/mnist-delta/java/io/deltareduce/demo/MnistDeltaNettyRelay.java"
                    ),
                    source(
                        "delta-node-java/src/main/java/io/deltareduce/node/benchmark/"
                        "BenchmarkTransport.java"
                    ),
                    source(
                        "delta-node-java/src/main/java/io/deltareduce/node/benchmark/"
                        "NettyMetricsCollector.java"
                    ),
                ],
            },
            "implementation_class": "DEMO_ADAPTER_USING_PRODUCTION_NETTY_TRANSPORT",
            "sequence": 2,
            "status": observed(
                len(transport_receipts) == NODE_COUNT * (1 + len(REQUIRED_VOTE_KINDS))
                and all(receipt.get("status") == "PASS" for receipt in transport_receipts)
                and all(
                    receipt.get("entry_count") == NODE_COUNT + 1
                    for receipt in transport_receipts[:NODE_COUNT]
                )
                and all(
                    receipt.get("entry_count") == NODE_COUNT
                    for receipt in transport_receipts[NODE_COUNT:]
                ),
                "MNIST_DELTA_NETTY_COMPONENT_NOT_OBSERVED",
            ),
        },
        {
            "component": "delta::runtime::CertificateVoteRuntime",
            "evidence": {
                "durable_vote_events": observed_vote_events,
                "native_trace_ids": native_trace_ids,
                "source_id": source("delta-runtime-cpp/src/certificate_runtime.cpp"),
            },
            "implementation_class": "PRODUCTION_DELTA",
            "sequence": 3,
            "status": observed(
                len(vote_results) == NODE_COUNT * len(REQUIRED_VOTE_KINDS)
                and observed_vote_events == NODE_COUNT * len(REQUIRED_VOTE_KINDS),
                "MNIST_DELTA_VOTE_RUNTIME_NOT_OBSERVED",
            ),
        },
        {
            "component": VOTE_QUORUM_COMPONENT,
            "evidence": {
                "delivered_votes_per_receiver": NODE_COUNT,
                "validated_vote_quorum_count": observed_vote_quorum_events,
                "source_id": source("delta-core-cpp/src/consensus.cpp"),
            },
            "implementation_class": "PRODUCTION_DELTA",
            "sequence": 4,
            "status": observed(
                observed_vote_quorum_events == NODE_COUNT * len(REQUIRED_VOTE_KINDS),
                "MNIST_DELTA_VOTE_QUORUM_VALIDATOR_NOT_OBSERVED",
            ),
        },
        {
            "component": TYPED_CERTIFICATE_VERIFIER,
            "evidence": {
                "certified_phase_count": observed_certified_phases,
                "parent_and_current_typed_verification_events": (observed_typed_certificate_events),
                "post_quorum_only": True,
                "source_id": source("delta-core-cpp/src/certificates/verifier.cpp"),
            },
            "implementation_class": "PRODUCTION_DELTA",
            "sequence": 5,
            "status": observed(
                len(certify_results) == NODE_COUNT * len(REQUIRED_VOTE_KINDS)
                and observed_certified_phases == NODE_COUNT * len(REQUIRED_VOTE_KINDS)
                and observed_typed_certificate_events == observed_quorum_events,
                "MNIST_DELTA_CHAIN_VERIFIER_NOT_OBSERVED",
            ),
        },
        {
            "component": "delta::robust::build_plan",
            "evidence": {
                "aggregate_root_ids": [item["aggregate_root_qc_id"] for item in finalize_results],
                "observed_validator_count": len(
                    component_validators("typed_certificate_materialized", "APC")
                ),
                "source_id": source("delta-core-cpp/src/robust/plan.cpp"),
            },
            "implementation_class": "PRODUCTION_DELTA",
            "sequence": 6,
            "status": observed(
                len({item["aggregate_root_qc_id"] for item in finalize_results}) == 1
                and len(component_validators("typed_certificate_materialized", "APC"))
                == NODE_COUNT,
                "MNIST_DELTA_ROBUST_PLAN_NOT_OBSERVED",
            ),
        },
        {
            "component": "delta::robust::reduce_parameter_shard",
            "evidence": {
                "applied_model_file_sha256": model.content_id,
                "observed_validator_count": len(component_validators("parameter_shard_reduced")),
                "source_id": source("delta-core-cpp/src/robust/plan.cpp"),
            },
            "implementation_class": "PRODUCTION_DELTA_AGGREGATION_AUTHORITY",
            "sequence": 7,
            "status": observed(
                all(
                    nested(item, "model_artifact", "sha256") == model.content_id
                    for item in finalize_results
                )
                and len(component_validators("parameter_shard_reduced")) == NODE_COUNT,
                "MNIST_DELTA_ROBUST_REDUCE_NOT_OBSERVED",
            ),
        },
        {
            "component": "delta::apply::compute_candidate",
            "evidence": {
                "candidate_ids": [item["apply_candidate_id"] for item in finalize_results],
                "observed_validator_count": len(component_validators("apply_computed")),
                "source_id": source("delta-core-cpp/src/apply/engine.cpp"),
            },
            "implementation_class": "PRODUCTION_DELTA",
            "sequence": 8,
            "status": observed(
                len({item["apply_candidate_id"] for item in finalize_results}) == 1
                and len(component_validators("apply_computed")) == NODE_COUNT,
                "MNIST_DELTA_APPLY_NOT_OBSERVED",
            ),
        },
        {
            "component": "delta::runtime::CurrentPointerStore",
            "evidence": {
                "model_state_hash": finalize_results[0]["model_hash"],
                "pointer_count": len(finalize_results),
                "source_id": source("delta-runtime-cpp/src/certificate_runtime.cpp"),
            },
            "implementation_class": "PRODUCTION_DELTA",
            "sequence": 9,
            "status": observed(
                len(finalize_results) == NODE_COUNT
                and all(
                    nested(item, "current_pointer", "disposition") == "ADVANCED"
                    for item in finalize_results
                ),
                "MNIST_DELTA_CURRENT_POINTER_NOT_OBSERVED",
            ),
        },
    ]
    proposal_components = (
        "delta::certificates::InputSetCertificate",
        "delta::robust::build_plan",
        "delta::robust::build_plan",
        "delta::robust::reduce_parameter_shard",
        "delta::certificates::aggregate_merkle_root",
        "delta::apply::compute_candidate",
    )
    final_certificates = finalize_results[0].get("quorum_certificates")
    if not isinstance(final_certificates, list) or len(final_certificates) != len(TRACE_PHASES):
        raise MnistDeltaError("MNIST_DELTA_PHASE_EXECUTION_INVALID")
    phase_execution: list[dict[str, object]] = []
    for index, (phase, _trace_kind, vote_action) in enumerate(TRACE_PHASES):
        phase_votes = [item for item in vote_results if item.get("phase") == phase]
        phase_certificates = [item for item in certify_results if item.get("phase") == phase]
        certificate = final_certificates[index]
        if (
            len(phase_votes) != NODE_COUNT
            or len(phase_certificates) != NODE_COUNT
            or not isinstance(certificate, dict)
            or any(item.get("mode") != "vote-phase" for item in phase_votes)
            or any(item.get("mode") != "certify-phase" for item in phase_certificates)
        ):
            raise MnistDeltaError("MNIST_DELTA_PHASE_EXECUTION_INVALID")
        typed_certificate_id = _require_content_id(
            certificate.get("body_hash"), "MNIST_DELTA_PHASE_EXECUTION_INVALID"
        )
        vote_quorum_id = _require_content_id(
            certificate.get("qc_id"), "MNIST_DELTA_PHASE_EXECUTION_INVALID"
        )
        preceding_certificates = final_certificates[:index]
        if not all(isinstance(item, dict) for item in preceding_certificates):
            raise MnistDeltaError("MNIST_DELTA_PHASE_EXECUTION_INVALID")
        parent_vote_quorum_ids = [
            _require_content_id(
                cast(Mapping[str, object], item).get("qc_id"),
                "MNIST_DELTA_PHASE_EXECUTION_INVALID",
            )
            for item in preceding_certificates
        ]
        if (
            typed_certificate_id == vote_quorum_id
            or any(
                item.get("validated_parent_qc_ids") != parent_vote_quorum_ids
                for item in (*phase_votes, *phase_certificates)
            )
            or any(
                cast(Mapping[str, object], item.get("vote_frame")).get("body_hash")
                != typed_certificate_id
                for item in phase_votes
            )
            or any(item.get("quorum_certificate") != certificate for item in phase_certificates)
        ):
            raise MnistDeltaError("MNIST_DELTA_PHASE_EXECUTION_INVALID")
        parent_typed_certificate_id = (
            None
            if index == 0
            else _require_content_id(
                cast(Mapping[str, object], final_certificates[index - 1]).get("body_hash"),
                "MNIST_DELTA_PHASE_EXECUTION_INVALID",
            )
        )
        parent_vote_quorum_id = parent_vote_quorum_ids[-1] if parent_vote_quorum_ids else None
        phase_execution.append(
            {
                "body_hash": typed_certificate_id,
                "certifying_nodes": len(phase_certificates),
                "delivered_vote_count_per_receiver": len(phase_votes),
                "execution_order": [
                    "typed_body_proposed",
                    "vote_persisted",
                    "four_netty_deliveries",
                    "generic_vote_quorum_validated",
                    "typed_certificate_verified",
                    "generic_qc_durably_finalized",
                ],
                "qc_durable_finalize_action_id": "OBS-CURRENT-QC-DURABLY-FINALIZED",
                "parent_gate_enforced": True,
                "phase": phase,
                "position": index + 1,
                "proposal_component": proposal_components[index],
                "required_parent_typed_certificate_id": parent_typed_certificate_id,
                "required_parent_vote_quorum_id": parent_vote_quorum_id,
                "transport_component": "io.deltareduce.demo.MnistDeltaNettyRelay",
                "typed_certificate_id": typed_certificate_id,
                "typed_certificate_action_id": "OBS-TYPED-CERT-VERIFIED-AFTER-QC",
                "typed_certificate_verification_after_vote_quorum": True,
                "typed_certificate_verifier": TYPED_CERTIFICATE_VERIFIER,
                "validated_parent_typed_certificate_ids": [
                    _require_content_id(
                        cast(Mapping[str, object], item).get("body_hash"),
                        "MNIST_DELTA_PHASE_EXECUTION_INVALID",
                    )
                    for item in preceding_certificates
                ],
                "validated_parent_vote_quorum_ids": parent_vote_quorum_ids,
                "vote_action_id": vote_action,
                "vote_frames_relayed_per_receiver": len(phase_votes),
                "vote_persistence_component": "delta::runtime::CertificateVoteRuntime",
                "vote_quorum_action_id": "OBS-CURRENT-VOTE-QUORUM-VALIDATED",
                "vote_quorum_component": VOTE_QUORUM_COMPONENT,
                "vote_quorum_id": vote_quorum_id,
            }
        )
    deterministic_trace: dict[str, object] = {
        "aggregation_authority": "delta::robust::reduce_parameter_shard",
        "apply_qc_id": finalize_results[0].get("apply_qc_id"),
        "authoritative": False,
        "certificate_signature_semantics": "CONTENT_ID_PLACEHOLDER_LOCAL_DEMO_ONLY",
        "classification": "LOCAL_DEMO_ONLY",
        "components": components,
        "contribution_ids": [item.content_id for item in contributions],
        "contributions_bound_netty_to_native": True,
        "current_pointer": finalize_results[0].get("current_pointer"),
        "demo_owned_aggregation": False,
        "execution_authorized": False,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "formal_refinement_claimed": False,
        "governance_eligible": False,
        "applied_model_file_sha256": model.content_id,
        "native_results": [
            _logical_result(item) for item in (*vote_results, *certify_results, *finalize_results)
        ],
        "native_cryptographic_signatures_verified": False,
        "native_trace_ids": native_trace_ids,
        "phase_execution": phase_execution,
        "phase_ordering_enforced": True,
        "distributed_orchestrator_received_node_local_numeric_arrays": False,
        "protocol_scope": "MNIST_WORKLOAD_TO_APPLIED_LOCAL_DELTA",
        "python_cross_node_aggregation_performed": False,
        "python_vote_quorum_assembly_performed": False,
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "terminal_outcome": "APPLIED",
        "trace_scope": TRACE_SCOPE,
        "transport_receipts": [_logical_result(item) for item in transport_receipts],
        "transport_receipt_ids": transport_receipt_ids,
        "toolchain": dict(toolchain_document),
        "type_name": "DELTAREDUCE_MNIST_EXECUTION_TRACE",
        "typed_certificate_verifier": TYPED_CERTIFICATE_VERIFIER,
        "vote_quorum_component": VOTE_QUORUM_COMPONENT,
        "workload_id": workload_id,
    }
    execution_path_id = _content_id(_canonical_bytes(deterministic_trace))
    trace_document = dict(deterministic_trace)
    trace_document.update(
        {
            "execution_path_id": execution_path_id,
            "native_trace": native_traces,
        }
    )
    trace_path = destination / "execution-trace.json"
    _write_json_new(trace_path, trace_document)
    diagram_path = destination / "execution-path.mmd"
    diagram = """flowchart TB
    A[4 Python MNIST workers] -->|node-local compute only| W[seal 4 opaque contribution files]
    W -->|Ed25519 verified bytes| B[Java Netty workload relay]
    B --> N[4 native Delta nodes]
    N --> I[InputSetCertificate typed body]
    I --> IV[CertificateVoteRuntime: persist ISC vote]
    IV --> IN[Java Netty: 4 ISC deliveries per receiver]
    IN --> IQ[consensus::validate_quorum: generic ISC quorum]
    IQ --> IT[ChainVerifier: typed ISC certificate]
    IT -->|parent quorum plus typed certificate| E[Eligibility via robust::build_plan]
    E --> EV[CertificateVoteRuntime: persist EC vote]
    EV --> EN[Java Netty: 4 EC deliveries per receiver]
    EN --> EQ[consensus::validate_quorum: generic EC quorum]
    EQ --> ET[ChainVerifier: typed EC certificate]
    ET -->|parent quorum plus typed certificate| P[Aggregation plan via robust::build_plan]
    P --> PV[CertificateVoteRuntime: persist APC vote]
    PV --> PN[Java Netty: 4 APC deliveries per receiver]
    PN --> PQ[consensus::validate_quorum: generic APC quorum]
    PQ --> PT[ChainVerifier: typed APC certificate]
    PT -->|required before numeric reduction| R[robust::reduce_parameter_shard]
    R --> RV[CertificateVoteRuntime: persist ParameterShard vote]
    RV --> RN[Java Netty: 4 ParameterShard deliveries per receiver]
    RN --> RQ[consensus::validate_quorum: generic ParameterShard quorum]
    RQ --> RT[ChainVerifier: typed ParameterShardQC]
    RT -->|generic parent quorum plus typed parent certificate| G[aggregate_merkle_root]
    G --> GV[CertificateVoteRuntime: persist AggregateRoot vote]
    GV --> GN[Java Netty: 4 AggregateRoot deliveries per receiver]
    GN --> GQ[consensus::validate_quorum: generic AggregateRoot quorum]
    GQ --> GT[ChainVerifier: typed AggregateRootQC]
    GT -->|generic parent quorum plus typed parent certificate| AC[apply::compute_candidate]
    AC --> AV[CertificateVoteRuntime: persist Apply vote]
    AV --> AN[Java Netty: 4 Apply deliveries per receiver]
    AN --> AQ[consensus::validate_quorum: generic Apply quorum]
    AQ --> AT[ChainVerifier: typed ApplyQC]
    AT -->|pointer apply_qc_id equals typed ApplyQC ID| C[CurrentPointerStore: APPLIED]
    C -->|native model bytes| UI[Python evaluation plus UI]
    Z[centralized baseline] -. comparison only; never a Delta input .-> UI
"""
    _write_new(diagram_path, diagram.encode("utf-8"))
    delta_execution: dict[str, object] = {
        "aggregation_authority": "delta::robust::reduce_parameter_shard",
        "apply_qc_id": finalize_results[0].get("apply_qc_id"),
        "applied_model_file_sha256": model.content_id,
        "authoritative": False,
        "certificate_signature_semantics": "CONTENT_ID_PLACEHOLDER_LOCAL_DEMO_ONLY",
        "classification": "LOCAL_DEMO_ONLY",
        "components": components,
        "contributions_bound_netty_to_native": True,
        "current_pointer": finalize_results[0].get("current_pointer"),
        "demo_owned_aggregation": False,
        "execution_authorized": False,
        "execution_path_id": execution_path_id,
        "execution_trace_sha256": _content_id(trace_path.read_bytes()),
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "formal_refinement_claimed": False,
        "governance_eligible": False,
        "model_state_hash": finalize_results[0].get("model_hash"),
        "native_cryptographic_signatures_verified": False,
        "node_count": NODE_COUNT,
        "phase_execution": phase_execution,
        "phase_ordering_enforced": True,
        "distributed_orchestrator_received_node_local_numeric_arrays": False,
        "protocol_scope": "MNIST_WORKLOAD_TO_APPLIED_LOCAL_DELTA",
        "python_cross_node_aggregation_performed": False,
        "python_vote_quorum_assembly_performed": False,
        "quorum_certificates": finalize_results[0].get("quorum_certificates"),
        "semantic_completeness_claimed": False,
        "status": "PASS",
        "terminal_outcome": "APPLIED",
        "trace_scope": TRACE_SCOPE,
        "transport_ed25519_verified": True,
        "typed_certificate_verifier": TYPED_CERTIFICATE_VERIFIER,
        "vote_quorum_component": VOTE_QUORUM_COMPONENT,
        "toolchain": dict(toolchain_document),
        "workload_id": workload_id,
    }
    return delta_execution, trace_path, diagram_path


def run_delta_nodes(
    repository_root: Path,
    destination: Path,
    controllers_dir: Path,
    node_contributions: Sequence[NodeContribution],
    source_id: str,
    *,
    toolchain: DeltaToolchain | None = None,
) -> DeltaExecutionResult:
    """Run four local Delta nodes through six interleaved vote/QC phases."""
    root = repository_root.resolve(strict=True)
    output = destination.resolve(strict=False)
    if output.exists():
        raise MnistDeltaError("MNIST_DELTA_OUTPUT_ALREADY_EXISTS")
    output.mkdir(parents=True)
    selected_toolchain = toolchain or DeltaToolchain.from_environment(root)
    toolchain_document = selected_toolchain.validate(root)
    signers = _load_demo_signers(controllers_dir.resolve(strict=True))

    workload_root = output / "workload"
    workload_root.mkdir()
    workload_path = workload_root / "mnist-workload.bin"
    contributions, workload_id = write_workload(node_contributions, source_id, workload_path)
    contribution_ids = tuple(item.content_id for item in contributions)
    validator_ids = tuple(f"validator-{index:02d}" for index in range(1, NODE_COUNT + 1))

    transport_receipts: list[dict[str, object]] = []
    relayed_workloads: dict[str, Path] = {}
    relayed_contribution_roots: dict[str, Path] = {}
    for validator_index, validator_id in enumerate(validator_ids):
        destination_root = output / "network" / "workloads" / validator_id
        entries = [
            _RelayEntry(workload_path, PurePosixPath("workload.bin"), validator_index),
            *(
                _RelayEntry(
                    workload_root / f"contribution-{item.node_index:02d}.bin",
                    PurePosixPath(f"contributions/worker-{item.node_index:02d}.bin"),
                    item.node_index - 1,
                )
                for item in contributions
            ),
        ]
        receipt = _run_relay(
            selected_toolchain,
            signers,
            entries,
            destination_root,
            output / "transport-evidence",
            f"workload-to-{validator_id}",
        )
        transport_receipts.append(receipt)
        relayed_workloads[validator_id] = destination_root / "workload.bin"
        relayed_contribution_roots[validator_id] = destination_root / "contributions"
    expected_workload_transport_ids = [workload_id, *contribution_ids]
    if any(
        receipt.get("input_content_ids") != expected_workload_transport_ids
        or receipt.get("output_content_ids") != expected_workload_transport_ids
        for receipt in transport_receipts
    ):
        raise MnistDeltaError("MNIST_DELTA_CONTRIBUTION_TRANSPORT_BINDING_INVALID")

    runtime_root = output / "native-nodes"
    results_root = output / "results"
    results_root.mkdir()
    qcs_roots = {validator_id: output / "qcs" / validator_id for validator_id in validator_ids}
    for qcs_root in qcs_roots.values():
        qcs_root.mkdir(parents=True)
    vote_results_by_validator: dict[str, list[dict[str, object]]] = {
        validator_id: [] for validator_id in validator_ids
    }
    certify_results_by_validator: dict[str, list[dict[str, object]]] = {
        validator_id: [] for validator_id in validator_ids
    }
    crash_result_path = results_root / "validator-04-apply-crash.json"
    crash_result: dict[str, object] | None = None

    for phase_index, phase in enumerate(REQUIRED_VOTE_KINDS):
        phase_body_ids: list[str] = []
        for validator_id in validator_ids:
            node_dir = runtime_root / validator_id
            qcs_argument = qcs_roots[validator_id] if phase_index > 0 else None
            expected_parent_qc_ids = [
                _require_content_id(
                    cast(Mapping[str, object], item.get("quorum_certificate")).get("qc_id"),
                    "MNIST_DELTA_PARENT_QCS_INVALID",
                )
                for item in certify_results_by_validator[validator_id]
            ]
            if validator_id == "validator-04" and phase == "apply":
                _run_process(
                    _native_command(
                        selected_toolchain,
                        "vote-phase",
                        workload=relayed_workloads[validator_id],
                        contributions_root=relayed_contribution_roots[validator_id],
                        node_dir=node_dir,
                        validator_id=validator_id,
                        result_path=crash_result_path,
                        phase=phase,
                        qcs_root=qcs_argument,
                        crash=True,
                    ),
                    expected_codes=frozenset({75}),
                )
                crash_result = _load_json(crash_result_path, "MNIST_DELTA_CRASH_RESULT_INVALID")
                _validate_vote_phase_result(
                    crash_result,
                    validator_id,
                    workload_id,
                    source_id,
                    contribution_ids,
                    node_dir,
                    crash_result_path,
                    phase_index,
                    expected_parent_qc_ids,
                    crash=True,
                )
            result_path = results_root / f"{validator_id}-{phase}-vote.json"
            _run_process(
                _native_command(
                    selected_toolchain,
                    "vote-phase",
                    workload=relayed_workloads[validator_id],
                    contributions_root=relayed_contribution_roots[validator_id],
                    node_dir=node_dir,
                    validator_id=validator_id,
                    result_path=result_path,
                    phase=phase,
                    qcs_root=qcs_argument,
                ),
                expected_codes=frozenset({0}),
            )
            result = _load_json(result_path, "MNIST_DELTA_VOTE_PHASE_RESULT_INVALID")
            _validate_vote_phase_result(
                result,
                validator_id,
                workload_id,
                source_id,
                contribution_ids,
                node_dir,
                result_path,
                phase_index,
                expected_parent_qc_ids,
                crash=False,
            )
            frame = result.get("vote_frame")
            if not isinstance(frame, dict):
                raise MnistDeltaError("MNIST_DELTA_VOTE_PHASE_RESULT_INVALID")
            phase_body_ids.append(
                _require_content_id(frame.get("body_hash"), "MNIST_DELTA_VOTE_BODY_ID_INVALID")
            )
            vote_results_by_validator[validator_id].append(result)
        if len(set(phase_body_ids)) != 1:
            raise MnistDeltaError("MNIST_DELTA_NODE_PHASE_BODIES_DIVERGED")

        vote_sources = [
            _RelayEntry(
                runtime_root / sender_id / "vote-frames" / f"{phase}.vote",
                PurePosixPath(f"{sender_id}/vote-frames/{phase}.vote"),
                sender_index,
            )
            for sender_index, sender_id in enumerate(validator_ids)
        ]
        phase_qc_documents: list[bytes] = []
        for receiver_id in validator_ids:
            expected_parent_qc_ids = [
                _require_content_id(
                    cast(Mapping[str, object], item.get("quorum_certificate")).get("qc_id"),
                    "MNIST_DELTA_PARENT_QCS_INVALID",
                )
                for item in certify_results_by_validator[receiver_id]
            ]
            votes_root = output / "network" / "votes" / phase / receiver_id
            receipt = _run_relay(
                selected_toolchain,
                signers,
                vote_sources,
                votes_root,
                output / "transport-evidence",
                f"votes-{phase}-to-{receiver_id}",
            )
            transport_receipts.append(receipt)
            qc_output = qcs_roots[receiver_id] / f"{phase}.qc"
            result_path = results_root / f"{receiver_id}-{phase}-certify.json"
            _run_process(
                _native_command(
                    selected_toolchain,
                    "certify-phase",
                    workload=relayed_workloads[receiver_id],
                    contributions_root=relayed_contribution_roots[receiver_id],
                    node_dir=runtime_root / receiver_id,
                    validator_id=receiver_id,
                    result_path=result_path,
                    phase=phase,
                    votes_root=votes_root,
                    qcs_root=qcs_roots[receiver_id] if phase_index > 0 else None,
                    qc_output=qc_output,
                ),
                expected_codes=frozenset({0}),
            )
            result = _load_json(result_path, "MNIST_DELTA_CERTIFY_PHASE_RESULT_INVALID")
            _validate_certify_phase_result(
                result,
                receiver_id,
                workload_id,
                source_id,
                contribution_ids,
                qcs_roots[receiver_id],
                result_path,
                phase_index,
                expected_parent_qc_ids,
            )
            certificate = result.get("quorum_certificate")
            if (
                not isinstance(certificate, dict)
                or certificate.get("body_hash") != phase_body_ids[0]
            ):
                raise MnistDeltaError("MNIST_DELTA_CERTIFY_PHASE_RESULT_INVALID")
            certify_results_by_validator[receiver_id].append(result)
            phase_qc_documents.append(qc_output.read_bytes())
        if len(set(phase_qc_documents)) != 1:
            raise MnistDeltaError("MNIST_DELTA_NODE_QCS_DIVERGED")

    finalize_results: list[dict[str, object]] = []
    models: list[AppliedModel] = []
    for validator_id in validator_ids:
        model_path = output / "models" / validator_id / "applied-model.bin"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        result_path = results_root / f"{validator_id}-finalize.json"
        _run_process(
            _native_command(
                selected_toolchain,
                "finalize",
                workload=relayed_workloads[validator_id],
                contributions_root=relayed_contribution_roots[validator_id],
                node_dir=runtime_root / validator_id,
                validator_id=validator_id,
                result_path=result_path,
                qcs_root=qcs_roots[validator_id],
                applied_model=model_path,
            ),
            expected_codes=frozenset({0}),
        )
        model = decode_applied_model(model_path)
        result = _load_json(result_path, "MNIST_DELTA_FINALIZE_RESULT_INVALID")
        _validate_finalize_result(
            result,
            validator_id,
            workload_id,
            source_id,
            contribution_ids,
            model,
            runtime_root / validator_id,
            result_path,
        )
        body_ids = _validate_body_ids(result)
        vote_body_ids = [
            cast(Mapping[str, object], vote.get("vote_frame"))["body_hash"]
            for vote in vote_results_by_validator[validator_id]
        ]
        qc_ids = [
            cast(Mapping[str, object], certificate.get("quorum_certificate"))["qc_id"]
            for certificate in certify_results_by_validator[validator_id]
        ]
        final_qcs = result.get("quorum_certificates")
        if (
            vote_body_ids != [body_ids[kind] for kind in REQUIRED_VOTE_KINDS]
            or not isinstance(final_qcs, list)
            or qc_ids
            != [cast(Mapping[str, object], certificate)["qc_id"] for certificate in final_qcs]
        ):
            raise MnistDeltaError("MNIST_DELTA_PHASE_CHAIN_BINDING_INVALID")
        models.append(model)
        finalize_results.append(result)

    if len({model.raw_bytes for model in models}) != 1:
        raise MnistDeltaError("MNIST_DELTA_NODE_MODELS_DIVERGED")
    semantic_keys = (
        "aggregate_root_qc_id",
        "apply_candidate_id",
        "apply_qc_id",
        "body_ids",
        "current_pointer",
        "model_hash",
        "quorum_certificates",
        "optimizer_hash",
    )
    if any(
        len({_canonical_bytes(result.get(key)) for result in finalize_results}) != 1
        for key in semantic_keys
    ):
        raise MnistDeltaError("MNIST_DELTA_NODE_RECEIPTS_DIVERGED")

    native_traces = {
        validator_id: _collect_native_trace(
            runtime_root / validator_id / "trace.jsonl",
            validator_id,
            vote_results_by_validator[validator_id],
            certify_results_by_validator[validator_id],
            finalize_results[index],
            expect_crash=validator_id == "validator-04",
        )
        for index, validator_id in enumerate(validator_ids)
    }
    validator_four_events = [row.get("event") for row in native_traces["validator-04"]]
    if "simulated_crash" not in validator_four_events or not any(
        row.get("replay") is True for row in native_traces["validator-04"]
    ):
        raise MnistDeltaError("MNIST_DELTA_CRASH_RECOVERY_TRACE_INVALID")

    vote_results = [
        item for validator_id in validator_ids for item in vote_results_by_validator[validator_id]
    ]
    certify_results = [
        item
        for validator_id in validator_ids
        for item in certify_results_by_validator[validator_id]
    ]
    delta_execution, trace_path, diagram_path = _write_execution_evidence(
        output,
        workload_id,
        contributions,
        transport_receipts,
        vote_results,
        certify_results,
        finalize_results,
        native_traces,
        toolchain_document,
        models[0],
    )
    if crash_result is None:
        raise MnistDeltaError("MNIST_DELTA_CRASH_RESULT_INVALID")
    failure_simulation: dict[str, object] = {
        "available_nodes_after_restart": NODE_COUNT,
        "crash_exit_code": 75,
        "crash_point": "AFTER_DURABLE_APPLY_VOTE_BEFORE_EXPOSE",
        "failed_node_id": "validator-04",
        "model_hash_after_recovery": models[0].content_id,
        "protocol_accepted_after_recovery": True,
        "recovered_vote_count": vote_results_by_validator["validator-04"][-1].get(
            "recovered_vote_count"
        ),
        "replay_observed": True,
        "status": "RECOVERED_AND_APPLIED",
        "terminal_outcome": "APPLIED",
        "vote_wal_after_crash": crash_result.get("vote_wal"),
    }
    return DeltaExecutionResult(
        applied_model=models[0],
        delta_execution=delta_execution,
        execution_trace_path=trace_path,
        execution_diagram_path=diagram_path,
        failure_simulation=failure_simulation,
        node_contributions=contributions,
    )
