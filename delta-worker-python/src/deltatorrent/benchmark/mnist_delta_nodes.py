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

from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID

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
TRACE_PHASES = (
    ("input_set", "ISC", "ACT-ISC-VOTE", "ACT-ISC-FINALIZE"),
    ("eligibility", "EC", "ACT-EC-VOTE", "ACT-EC-FINALIZE"),
    ("aggregation_plan", "APC", "ACT-APC-VOTE", "ACT-APC-FINALIZE"),
    (
        "parameter_shard",
        "PARAMETER_SHARD_QC",
        "ACT-PARAM-VOTE",
        "ACT-PARAM-FINALIZE",
    ),
    (
        "aggregate_root",
        "AGGREGATE_ROOT_QC",
        "ACT-ROOT-VOTE",
        "ACT-ROOT-FINALIZE",
    ),
    ("apply", "APPLY_QC", "ACT-APPLY-VOTE", "ACT-APPLY-FINALIZE"),
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
        "body_ids",
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
PREPARE_RESULT_FIELDS = COMMON_NATIVE_RESULT_FIELDS | {
    "recovered_vote_count",
    "recovery_required",
    "runtime_wal",
    "vote_frames",
    "vote_wal",
}
FINALIZE_RESULT_FIELDS = COMMON_NATIVE_RESULT_FIELDS | {
    "aggregate_root_qc_id",
    "apply_candidate_id",
    "apply_qc_id",
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
        "modes": ["prepare-votes", "finalize"],
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
    votes_root: Path | None = None,
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
    if votes_root is not None:
        command.extend(("--votes-root", str(votes_root)))
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


def _validate_prepare_result(
    value: Mapping[str, object],
    validator_id: str,
    workload_id: str,
    source_id: str,
    contribution_ids: Sequence[str],
    node_dir: Path,
    result_path: Path,
    *,
    crash: bool,
) -> None:
    expected_fields = PREPARE_RESULT_FIELDS | ({"crashed_vote"} if crash else set())
    if set(value) != expected_fields:
        raise MnistDeltaError("MNIST_DELTA_PREPARE_RESULT_INVALID")
    _validate_common_native_result(value, validator_id, workload_id, source_id, contribution_ids)
    _validate_native_result_file(result_path, value, "MNIST_DELTA_PREPARE_RESULT_INVALID")
    expected_status = "SIMULATED_CRASH" if crash else "VOTES_EXPOSED"
    if (
        value.get("type_name") != "MNIST_DELTA_PREPARE_RESULT"
        or value.get("status") != expected_status
        or value.get("mode") != "prepare-votes"
    ):
        raise MnistDeltaError("MNIST_DELTA_PREPARE_RESULT_INVALID")
    frames = value.get("vote_frames")
    if not isinstance(frames, list):
        raise MnistDeltaError("MNIST_DELTA_PREPARE_RESULT_INVALID")
    expected_frame_count = len(REQUIRED_VOTE_KINDS) - 1 if crash else len(REQUIRED_VOTE_KINDS)
    if len(frames) != expected_frame_count:
        raise MnistDeltaError("MNIST_DELTA_PREPARE_RESULT_INVALID")
    body_ids = cast(dict[str, object], value["body_ids"])
    expected_replay = validator_id == "validator-04" and not crash
    for expected_sequence, (kind, frame) in enumerate(
        zip(REQUIRED_VOTE_KINDS, frames, strict=False), start=1
    ):
        trace_kind = TRACE_PHASES[expected_sequence - 1][1]
        expected_context = f"{trace_kind}:{value['round_id']}:1:0"
        if (
            not isinstance(frame, dict)
            or set(frame)
            != {"body_hash", "context_id", "durable_sequence", "file", "kind", "replay", "sha256"}
            or frame.get("kind") != kind
            or frame.get("body_hash") != body_ids[kind]
            or frame.get("durable_sequence") != expected_sequence
            or frame.get("context_id") != expected_context
            or frame.get("file") != f"vote-frames/{kind}.vote"
            or frame.get("replay") is not expected_replay
        ):
            raise MnistDeltaError("MNIST_DELTA_PREPARE_RESULT_INVALID")
        _validate_native_file_reference(
            {"file": frame["file"], "sha256": frame.get("sha256")},
            node_dir,
            f"vote-frames/{kind}.vote",
            "MNIST_DELTA_VOTE_FRAME_INVALID",
        )
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
            or value.get("recovered_vote_count") != len(REQUIRED_VOTE_KINDS)
            or not isinstance(crashed_vote, dict)
            or set(crashed_vote) != {"body_hash", "context_id", "durable_sequence", "kind"}
            or crashed_vote.get("kind") != "apply"
            or crashed_vote.get("body_hash") != body_ids["apply"]
            or crashed_vote.get("context_id") != f"APPLY_QC:{value['round_id']}:1:0"
            or crashed_vote.get("durable_sequence") != len(REQUIRED_VOTE_KINDS)
        ):
            raise MnistDeltaError("MNIST_DELTA_CRASH_NOT_DURABLE")
        return
    if value.get("recovery_required") is not False or value.get("recovered_vote_count") != (
        len(REQUIRED_VOTE_KINDS) if validator_id == "validator-04" else 0
    ):
        raise MnistDeltaError("MNIST_DELTA_PREPARE_RESULT_INVALID")


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
    body_ids = cast(dict[str, object], value["body_ids"])
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
        qc_ids.append(
            _require_content_id(certificate.get("qc_id"), "MNIST_DELTA_FINALIZE_QC_ID_INVALID")
        )
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
    prepare_result: Mapping[str, object],
    finalize_result: Mapping[str, object],
    *,
    expect_crash: bool,
) -> list[dict[str, object]]:
    try:
        raw = path.read_bytes()
        if not raw.endswith(b"\n") or b"\r" in raw:
            raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
        lines = raw.decode("utf-8").splitlines()
        values = [json.loads(line) for line in lines]
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID") from exc
    rows: list[dict[str, object]] = []
    workload_id = str(prepare_result.get("workload_id"))
    round_id = str(prepare_result.get("round_id"))
    for line, value in zip(lines, values, strict=True):
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
            or value.get("mode") not in ("prepare-votes", "finalize")
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
        rows.append(cast(dict[str, object], value))
    if not rows:
        raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")

    expected_event_counts = {
        "apply_computed": 1,
        "current_pointer_applied": 1,
        "mode_complete": 2,
        "mode_started": 3 if expect_crash else 2,
        "quorum_validated": len(REQUIRED_VOTE_KINDS),
        "runtime_transition": 10,
        "vote_durable_and_exposed": 11 if expect_crash else len(REQUIRED_VOTE_KINDS),
    }
    if expect_crash:
        expected_event_counts.update(
            {
                "journal_recovered": 1,
                "journal_recovery_verified": 1,
                "simulated_crash": 1,
            }
        )
    if Counter(str(row["event"]) for row in rows) != expected_event_counts:
        raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
    if any(
        row.get("error_code") is not None and row.get("event") != "simulated_crash" for row in rows
    ):
        raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")

    started_rows = [row for row in rows if row.get("event") == "mode_started"]
    prepare_complete_rows = [
        row
        for row in rows
        if row.get("event") == "mode_complete" and row.get("mode") == "prepare-votes"
    ]
    if (
        [row.get("mode") for row in started_rows]
        != (
            ["prepare-votes", "prepare-votes", "finalize"]
            if expect_crash
            else ["prepare-votes", "finalize"]
        )
        or any(row.get("outcome") != "ACCEPTED" for row in started_rows)
        or len(prepare_complete_rows) != 1
        or prepare_complete_rows[0].get("outcome") != "VOTES_EXPOSED"
        or prepare_complete_rows[0].get("replay") is not expect_crash
        or prepare_complete_rows[0].get("body_hash")
        != cast(Mapping[str, object], prepare_result["body_ids"])["apply"]
    ):
        raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
    runtime_rows = [row for row in rows if row.get("event") == "runtime_transition"]
    if any(
        row.get("mode") not in ("prepare-votes", "finalize")
        or row.get("outcome") != "ACCEPTED"
        or row.get("replay") is not False
        for row in runtime_rows
    ):
        raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")

    body_ids = cast(Mapping[str, object], prepare_result["body_ids"])
    certificates = finalize_result.get("quorum_certificates")
    if not isinstance(certificates, list):
        raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
    certificate_by_kind = {
        str(item.get("kind")): item for item in certificates if isinstance(item, dict)
    }
    for phase, trace_kind, vote_action, finalize_action in TRACE_PHASES:
        vote_rows = [
            row
            for row in rows
            if row.get("event") == "vote_durable_and_exposed" and row.get("vote_kind") == trace_kind
        ]
        expected_vote_count = 2 if expect_crash and phase != "apply" else 1
        if len(vote_rows) != expected_vote_count:
            raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
        final_vote = vote_rows[-1]
        expected_sequence = REQUIRED_VOTE_KINDS.index(phase) + 1
        if (
            final_vote.get("action_id") != vote_action
            or final_vote.get("body_hash") != body_ids[phase]
            or final_vote.get("durable_sequence") != expected_sequence
            or final_vote.get("replay") is not expect_crash
            or final_vote.get("outcome") != ("NO_OP" if expect_crash else "ACCEPTED")
        ):
            raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
        if expect_crash and phase != "apply":
            first_vote = vote_rows[0]
            if (
                first_vote.get("action_id") != vote_action
                or first_vote.get("body_hash") != body_ids[phase]
                or first_vote.get("durable_sequence") != expected_sequence
                or first_vote.get("replay") is not False
                or first_vote.get("outcome") != "ACCEPTED"
            ):
                raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
        certificate = certificate_by_kind.get(phase)
        quorum_rows = [
            row
            for row in rows
            if row.get("event") == "quorum_validated" and row.get("vote_kind") == trace_kind
        ]
        if (
            not isinstance(certificate, dict)
            or len(quorum_rows) != 1
            or quorum_rows[0].get("action_id") != finalize_action
            or quorum_rows[0].get("body_hash") != certificate.get("body_hash")
            or quorum_rows[0].get("result_hash") != certificate.get("qc_id")
            or quorum_rows[0].get("vote_context_id") != certificate.get("context_id")
            or quorum_rows[0].get("outcome") != "FINALIZED"
        ):
            raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")

    apply_rows = [row for row in rows if row.get("event") == "apply_computed"]
    pointer_rows = [row for row in rows if row.get("event") == "current_pointer_applied"]
    terminal_rows = [
        row
        for row in rows
        if row.get("event") == "mode_complete"
        and row.get("mode") == "finalize"
        and row.get("outcome") == "APPLIED"
    ]
    if (
        len(apply_rows) != 1
        or apply_rows[0].get("action_id") != "ACT-APPLY-COMPUTE"
        or apply_rows[0].get("body_hash") != finalize_result.get("aggregate_root_qc_id")
        or apply_rows[0].get("result_hash") != finalize_result.get("apply_candidate_id")
        or len(pointer_rows) != 1
        or pointer_rows[0].get("action_id") != "ACT-CURRENT-ADVANCE"
        or pointer_rows[0].get("body_hash") != finalize_result.get("apply_qc_id")
        or pointer_rows[0].get("result_hash") != finalize_result.get("model_hash")
        or len(terminal_rows) != 1
        or terminal_rows[0] is not rows[-1]
        or terminal_rows[0].get("result_hash") != finalize_result.get("model_hash")
    ):
        raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")

    row_positions = {id(row): index for index, row in enumerate(rows)}
    final_vote_rows = [
        next(
            row
            for row in reversed(rows)
            if row.get("event") == "vote_durable_and_exposed" and row.get("vote_kind") == trace_kind
        )
        for _phase, trace_kind, _vote_action, _finalize_action in TRACE_PHASES
    ]
    quorum_rows_in_phase_order = [
        next(
            row
            for row in rows
            if row.get("event") == "quorum_validated" and row.get("vote_kind") == trace_kind
        )
        for _phase, trace_kind, _vote_action, _finalize_action in TRACE_PHASES
    ]
    critical_positions = [
        *(row_positions[id(row)] for row in final_vote_rows),
        row_positions[id(prepare_complete_rows[0])],
        row_positions[id(started_rows[-1])],
        *(row_positions[id(row)] for row in quorum_rows_in_phase_order),
        row_positions[id(apply_rows[0])],
        row_positions[id(pointer_rows[0])],
        row_positions[id(terminal_rows[0])],
    ]
    if critical_positions != sorted(critical_positions) or len(set(critical_positions)) != len(
        critical_positions
    ):
        raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")

    crash_rows = [row for row in rows if row.get("event") == "simulated_crash"]
    recovery_rows = [row for row in rows if row.get("event") == "journal_recovery_verified"]
    journal_rows = [row for row in rows if row.get("event") == "journal_recovered"]
    if expect_crash:
        if (
            len(crash_rows) != 1
            or crash_rows[0].get("action_id") != "ACT-CRASH"
            or crash_rows[0].get("body_hash") != body_ids["apply"]
            or crash_rows[0].get("error_code") != "SIMULATED_CRASH_AFTER_DURABILITY"
            or crash_rows[0].get("outcome") != "DURABLE_NOT_EXPOSED"
            or len(recovery_rows) != 1
            or recovery_rows[0].get("replay") is not True
            or len(journal_rows) != 1
            or journal_rows[0].get("replay") is not True
        ):
            raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
        crash_positions = [
            row_positions[id(crash_rows[0])],
            row_positions[id(recovery_rows[0])],
            row_positions[id(started_rows[1])],
            row_positions[id(journal_rows[0])],
            row_positions[id(final_vote_rows[0])],
        ]
        if crash_positions != sorted(crash_positions) or len(set(crash_positions)) != len(
            crash_positions
        ):
            raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")
    elif crash_rows or recovery_rows or journal_rows:
        raise MnistDeltaError("MNIST_DELTA_NATIVE_TRACE_INVALID")

    if workload_id != str(finalize_result.get("workload_id")):
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
    prepare_results: Sequence[Mapping[str, object]],
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
                len(transport_receipts) == NODE_COUNT * 2
                and all(receipt.get("status") == "PASS" for receipt in transport_receipts),
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
                observed_vote_events == NODE_COUNT * len(REQUIRED_VOTE_KINDS) + 5,
                "MNIST_DELTA_VOTE_RUNTIME_NOT_OBSERVED",
            ),
        },
        {
            "component": "delta::certificates::ChainVerifier",
            "evidence": {
                "quorum_validation_events": observed_quorum_events,
                "source_id": source("delta-core-cpp/src/certificates/verifier.cpp"),
            },
            "implementation_class": "PRODUCTION_DELTA",
            "sequence": 4,
            "status": observed(
                observed_quorum_events == NODE_COUNT * len(REQUIRED_VOTE_KINDS),
                "MNIST_DELTA_CHAIN_VERIFIER_NOT_OBSERVED",
            ),
        },
        {
            "component": "delta::robust::build_plan",
            "evidence": {
                "aggregate_root_ids": [item["aggregate_root_qc_id"] for item in finalize_results],
                "source_id": source("delta-core-cpp/src/robust/plan.cpp"),
            },
            "implementation_class": "PRODUCTION_DELTA",
            "sequence": 5,
            "status": observed(
                len({item["aggregate_root_qc_id"] for item in finalize_results}) == 1,
                "MNIST_DELTA_ROBUST_PLAN_NOT_OBSERVED",
            ),
        },
        {
            "component": "delta::robust::reduce_parameter_shard",
            "evidence": {
                "applied_model_file_sha256": model.content_id,
                "source_id": source("delta-core-cpp/src/robust/plan.cpp"),
            },
            "implementation_class": "PRODUCTION_DELTA_AGGREGATION_AUTHORITY",
            "sequence": 6,
            "status": observed(
                all(
                    nested(item, "model_artifact", "sha256") == model.content_id
                    for item in finalize_results
                ),
                "MNIST_DELTA_ROBUST_REDUCE_NOT_OBSERVED",
            ),
        },
        {
            "component": "delta::apply::compute_candidate",
            "evidence": {
                "candidate_ids": [item["apply_candidate_id"] for item in finalize_results],
                "source_id": source("delta-core-cpp/src/apply/engine.cpp"),
            },
            "implementation_class": "PRODUCTION_DELTA",
            "sequence": 7,
            "status": observed(
                len({item["apply_candidate_id"] for item in finalize_results}) == 1,
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
            "sequence": 8,
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
    deterministic_trace: dict[str, object] = {
        "aggregation_authority": "delta::robust::reduce_parameter_shard",
        "authoritative": False,
        "classification": "LOCAL_DEMO_ONLY",
        "components": components,
        "contribution_ids": [item.content_id for item in contributions],
        "contributions_bound_netty_to_native": True,
        "execution_authorized": False,
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "governance_eligible": False,
        "applied_model_file_sha256": model.content_id,
        "native_results": [_logical_result(item) for item in (*prepare_results, *finalize_results)],
        "native_trace_ids": native_trace_ids,
        "distributed_orchestrator_received_node_local_numeric_arrays": False,
        "protocol_scope": "MNIST_WORKLOAD_TO_APPLIED_LOCAL_DELTA",
        "python_cross_node_aggregation_performed": False,
        "schema_version": "1.0.0",
        "terminal_outcome": "APPLIED",
        "transport_receipts": [_logical_result(item) for item in transport_receipts],
        "transport_receipt_ids": transport_receipt_ids,
        "toolchain": dict(toolchain_document),
        "type_name": "DELTAREDUCE_MNIST_EXECUTION_TRACE",
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
    diagram = """flowchart LR
    A[4 Python MNIST workers] -->|worker-local computation| W[seal 4 opaque contribution files]
    W -->|Ed25519-verified exact bytes| B[Java Netty loopback]
    B --> C[demo-only native process adapter: bind all 4 records]
    C --> D[CertificateVoteRuntime + durable WAL]
    D --> E[ChainVerifier: ISC / EC / APC / ParameterShardQC / AggregateRootQC / ApplyQC]
    E --> F[robust::reduce_parameter_shard]
    F --> G[apply::compute_candidate]
    G --> H[CurrentPointerStore: APPLIED]
    H -->|native model bytes| I[Python evaluation + UI]
    Z[centralized baseline] -. comparison only; never a Delta input .-> I
"""
    _write_new(diagram_path, diagram.encode("utf-8"))
    delta_execution: dict[str, object] = {
        "aggregation_authority": "delta::robust::reduce_parameter_shard",
        "applied_model_file_sha256": model.content_id,
        "authoritative": False,
        "certificate_signature_semantics": "CONTENT_ID_PLACEHOLDER_LOCAL_DEMO_ONLY",
        "components": components,
        "contributions_bound_netty_to_native": True,
        "current_pointer": finalize_results[0].get("current_pointer"),
        "execution_path_id": execution_path_id,
        "execution_trace_sha256": _content_id(trace_path.read_bytes()),
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "governance_eligible": False,
        "model_state_hash": finalize_results[0].get("model_hash"),
        "native_cryptographic_signatures_verified": False,
        "node_count": NODE_COUNT,
        "distributed_orchestrator_received_node_local_numeric_arrays": False,
        "protocol_scope": "MNIST_WORKLOAD_TO_APPLIED_LOCAL_DELTA",
        "python_cross_node_aggregation_performed": False,
        "quorum_certificates": finalize_results[0].get("quorum_certificates"),
        "status": "PASS",
        "terminal_outcome": "APPLIED",
        "transport_ed25519_verified": True,
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
    """Run four local Delta node processes through Netty to terminal APPLIED."""
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

    transport_receipts: list[dict[str, object]] = []
    relayed_workloads: dict[str, Path] = {}
    relayed_contribution_roots: dict[str, Path] = {}
    for validator_index in range(1, NODE_COUNT + 1):
        validator_id = f"validator-{validator_index:02d}"
        destination_root = output / "network" / "workloads" / validator_id
        entries = [
            _RelayEntry(workload_path, PurePosixPath("workload.bin"), validator_index - 1),
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
    prepare_results: list[dict[str, object]] = []
    crash_result_path = output / "results" / "validator-04-crash.json"
    for validator_index in range(1, NODE_COUNT + 1):
        validator_id = f"validator-{validator_index:02d}"
        node_dir = runtime_root / validator_id
        result_path = output / "results" / f"{validator_id}-prepare.json"
        result_path.parent.mkdir(parents=True, exist_ok=True)
        if validator_index == NODE_COUNT:
            _run_process(
                _native_command(
                    selected_toolchain,
                    "prepare-votes",
                    workload=relayed_workloads[validator_id],
                    contributions_root=relayed_contribution_roots[validator_id],
                    node_dir=node_dir,
                    validator_id=validator_id,
                    result_path=crash_result_path,
                    crash=True,
                ),
                expected_codes=frozenset({75}),
            )
            crash_result = _load_json(crash_result_path, "MNIST_DELTA_CRASH_RESULT_INVALID")
            _validate_prepare_result(
                crash_result,
                validator_id,
                workload_id,
                source_id,
                contribution_ids,
                node_dir,
                crash_result_path,
                crash=True,
            )
        _run_process(
            _native_command(
                selected_toolchain,
                "prepare-votes",
                workload=relayed_workloads[validator_id],
                contributions_root=relayed_contribution_roots[validator_id],
                node_dir=node_dir,
                validator_id=validator_id,
                result_path=result_path,
            ),
            expected_codes=frozenset({0}),
        )
        result = _load_json(result_path, "MNIST_DELTA_PREPARE_RESULT_INVALID")
        _validate_prepare_result(
            result,
            validator_id,
            workload_id,
            source_id,
            contribution_ids,
            node_dir,
            result_path,
            crash=False,
        )
        if validator_index == NODE_COUNT:
            frames = result.get("vote_frames")
            apply_frame = frames[-1] if isinstance(frames, list) and frames else None
            if not isinstance(apply_frame, dict) or apply_frame.get("replay") is not True:
                raise MnistDeltaError("MNIST_DELTA_APPLY_VOTE_NOT_REPLAYED")
        prepare_results.append(result)

    vote_sources: list[_RelayEntry] = []
    for sender_index in range(1, NODE_COUNT + 1):
        for kind in REQUIRED_VOTE_KINDS:
            vote_sources.append(
                _RelayEntry(
                    runtime_root / f"validator-{sender_index:02d}" / "vote-frames" / f"{kind}.vote",
                    PurePosixPath(f"validator-{sender_index:02d}/vote-frames/{kind}.vote"),
                    sender_index - 1,
                )
            )

    finalize_results: list[dict[str, object]] = []
    models: list[AppliedModel] = []
    for receiver_index in range(1, NODE_COUNT + 1):
        validator_id = f"validator-{receiver_index:02d}"
        votes_root = output / "network" / "votes" / validator_id
        receipt = _run_relay(
            selected_toolchain,
            signers,
            vote_sources,
            votes_root,
            output / "transport-evidence",
            f"votes-to-{validator_id}",
        )
        transport_receipts.append(receipt)
        model_path = output / "models" / validator_id / "applied-model.bin"
        model_path.parent.mkdir(parents=True, exist_ok=True)
        result_path = output / "results" / f"{validator_id}-finalize.json"
        _run_process(
            _native_command(
                selected_toolchain,
                "finalize",
                workload=relayed_workloads[validator_id],
                contributions_root=relayed_contribution_roots[validator_id],
                node_dir=runtime_root / validator_id,
                validator_id=validator_id,
                result_path=result_path,
                votes_root=votes_root,
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
    if len({_canonical_bytes(result.get("body_ids")) for result in prepare_results}) != 1:
        raise MnistDeltaError("MNIST_DELTA_NODE_RECEIPTS_DIVERGED")

    native_traces = {
        f"validator-{index:02d}": _collect_native_trace(
            runtime_root / f"validator-{index:02d}" / "trace.jsonl",
            f"validator-{index:02d}",
            prepare_results[index - 1],
            finalize_results[index - 1],
            expect_crash=index == NODE_COUNT,
        )
        for index in range(1, NODE_COUNT + 1)
    }
    validator_four_events = [row.get("event") for row in native_traces["validator-04"]]
    if "simulated_crash" not in validator_four_events or not any(
        row.get("replay") is True for row in native_traces["validator-04"]
    ):
        raise MnistDeltaError("MNIST_DELTA_CRASH_RECOVERY_TRACE_INVALID")

    delta_execution, trace_path, diagram_path = _write_execution_evidence(
        output,
        workload_id,
        contributions,
        transport_receipts,
        prepare_results,
        finalize_results,
        native_traces,
        toolchain_document,
        models[0],
    )
    crash_result = _load_json(crash_result_path, "MNIST_DELTA_CRASH_RESULT_INVALID")
    failure_simulation: dict[str, object] = {
        "available_nodes_after_restart": NODE_COUNT,
        "crash_exit_code": 75,
        "crash_point": "AFTER_DURABLE_APPLY_VOTE_BEFORE_EXPOSE",
        "failed_node_id": "validator-04",
        "model_hash_after_recovery": models[0].content_id,
        "protocol_accepted_after_recovery": True,
        "recovered_vote_count": prepare_results[-1].get("recovered_vote_count"),
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
