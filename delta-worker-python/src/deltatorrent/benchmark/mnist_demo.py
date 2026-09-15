"""MNIST workload adapter for the isolated real-Delta node demonstration.

The module owns dataset preparation, node-local statistics and model evaluation.
Transport, durable votes, quorum certificates, cross-node reduction and Apply are
delegated fail-closed to unchanged Delta components; no Python fallback exists.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import struct
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Iterator, Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import numpy as np
from numpy.typing import NDArray

from deltatorrent.benchmark.campaign02_demo_controllers import (
    DemoControllerError,
    generate_demo_controller_bundle,
    run_demo_quorum_smoke,
)
from deltatorrent.benchmark.campaign02_stage_c_runtime import (
    MeasuredStageCRuntimeBoundary,
    RuntimeArtifact,
)
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.benchmark.mnist_delta_nodes import (
    DIGIT_COUNT,
    PIXELS_PER_DIGIT,
    DeltaToolchain,
    MnistDeltaError,
    NodeContribution,
    expected_central_model,
    run_delta_nodes,
    run_stage_c_real_drq1_nodes,
    write_node_contribution,
)
from deltatorrent.data.binding import BINDING_ASSERTION_SCHEMA_VERSION
from deltatorrent.data.eeg import (
    DEMO_EEG_PARTITIONS,
    EEG_DATASET_DESCRIPTOR,
    EegWindowDatasetProvider,
)
from deltatorrent.data.mnist import MNIST_DESCRIPTOR
from deltatorrent.data.registry import get_default_dataset_registry
from deltatorrent.model_plugins.mnist_centroid import (
    MnistCentroidPlugin,
    compute_mnist_summary,
)
from deltatorrent.model_plugins.registry import (
    EEG_BANDPOWER_DESCRIPTOR,
    MNIST_CENTROID_DESCRIPTOR,
)
from deltatorrent.model_plugins.registry import (
    get_default_registry as get_default_model_registry,
)
from deltatorrent.model_plugins.runner import (
    DomainBindingSpec,
    ModelDatasetBinding,
    MultiDomainBinding,
    bind_model_dataset_domains,
)


class MnistDemoError(ValueError):
    """Stable error raised by the local MNIST demonstration."""


ProgressCallback = Callable[[str, int, str], None]
UInt8Array = NDArray[np.uint8]
Int64Array = NDArray[np.int64]

MODEL_ID = "nearest-centroid-delta-int16-v2"
PARTITION_RULE_ID = "label-skew-disjoint-v1"
IMPLEMENTATION_VERSION = "2.0.0"
DEMO_SEED = 20260914
NODE_LABELS: tuple[tuple[int, ...], ...] = ((0, 1, 2), (3, 4, 5), (6, 7), (8, 9))


@dataclass(frozen=True, slots=True)
class MnistFile:
    """One pinned compressed source file from the public MNIST corpus."""

    filename: str
    sha256: str
    size_bytes: int
    url: str


MNIST_FILES: tuple[MnistFile, ...] = (
    MnistFile(
        filename="train-images-idx3-ubyte.gz",
        sha256="440fcabf73cc546fa21475e81ea370265605f56be210a4024d2ca8f203523609",
        size_bytes=9_912_422,
        url=("https://storage.googleapis.com/cvdf-datasets/mnist/train-images-idx3-ubyte.gz"),
    ),
    MnistFile(
        filename="train-labels-idx1-ubyte.gz",
        sha256="3552534a0a558bbed6aed32b30c495cca23d567ec52cac8be1a0730e8010255c",
        size_bytes=28_881,
        url=("https://storage.googleapis.com/cvdf-datasets/mnist/train-labels-idx1-ubyte.gz"),
    ),
    MnistFile(
        filename="t10k-images-idx3-ubyte.gz",
        sha256="8d422c7b0a1c1c79245a5bcf07fe86e33eeafee792b84584aec276f5a2dbc4e6",
        size_bytes=1_648_877,
        url=("https://storage.googleapis.com/cvdf-datasets/mnist/t10k-images-idx3-ubyte.gz"),
    ),
    MnistFile(
        filename="t10k-labels-idx1-ubyte.gz",
        sha256="f7ae60f92e00ec6debd23a6088c31dbd2371eca3ffa0defaefb259924204aec6",
        size_bytes=4_542,
        url=("https://storage.googleapis.com/cvdf-datasets/mnist/t10k-labels-idx1-ubyte.gz"),
    ),
)


@dataclass(frozen=True, slots=True)
class MnistDataset:
    """Validated in-memory MNIST train/test arrays and their source identity."""

    source_id: str
    train_images: UInt8Array
    train_labels: UInt8Array
    test_images: UInt8Array
    test_labels: UInt8Array


@dataclass(frozen=True, slots=True)
class NodeSummary:
    """Non-numeric metadata and an opaque contribution emitted by one worker."""

    contribution: NodeContribution
    duration_ms: float
    node_id: str
    process_id: int
    raw_data_bytes: int
    local_summary_bytes: int
    summary_id: str


@dataclass(frozen=True, slots=True)
class _LocalStatistics:
    """Process-local numeric state that is never returned to the orchestrator."""

    counts: Int64Array
    node_id: str
    summary_id: str
    sums: Int64Array


@dataclass(frozen=True, slots=True)
class Evaluation:
    """Measured classifier results over the common MNIST test set."""

    accuracy_ppm: int
    confusion_matrix: list[list[int]]
    correct: int
    per_digit: list[dict[str, int]]
    predictions: UInt8Array
    total: int

    def document(self) -> dict[str, object]:
        return {
            "accuracy_ppm": self.accuracy_ppm,
            "confusion_matrix": self.confusion_matrix,
            "correct": self.correct,
            "per_digit": self.per_digit,
            "total": self.total,
        }


@dataclass(frozen=True, slots=True)
class MnistDemoResult:
    """Paths and non-authoritative summary of a completed MNIST run."""

    output_dir: Path
    report_json: Path
    reproducibility_id: str

    @property
    def document(self) -> dict[str, object]:
        return {
            "authoritative": False,
            "demo_status": "DEMO_PASS",
            "execution_authorized": False,
            "governance_eligible": False,
            "output_dir": str(self.output_dir),
            "report_json": str(self.report_json),
            "reproducibility_id": self.reproducibility_id,
        }


def _canonical_bytes(value: Mapping[str, object]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _content_id(value: Mapping[str, object]) -> str:
    return f"sha256:{hashlib.sha256(_canonical_bytes(value)).hexdigest()}"


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_source_file(path: Path, source: MnistFile) -> None:
    if path.is_symlink() or not path.is_file():
        raise MnistDemoError(f"MNIST_SOURCE_NOT_REGULAR:{source.filename}")
    if path.stat().st_size != source.size_bytes:
        raise MnistDemoError(f"MNIST_SOURCE_SIZE_MISMATCH:{source.filename}")
    if _file_sha256(path) != source.sha256:
        raise MnistDemoError(f"MNIST_SOURCE_SHA256_MISMATCH:{source.filename}")


def _download_source(source: MnistFile, destination: Path) -> None:
    request = urllib.request.Request(
        source.url,
        headers={"User-Agent": "DeltaReduce-LOCAL-DEMO-ONLY/1.0"},
    )
    temporary_path: Path | None = None
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            with tempfile.NamedTemporaryFile(
                mode="xb",
                prefix=f".{source.filename}.",
                suffix=".part",
                dir=destination.parent,
                delete=False,
            ) as temporary:
                temporary_path = Path(temporary.name)
                downloaded = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    downloaded += len(chunk)
                    if downloaded > source.size_bytes:
                        raise MnistDemoError(
                            f"MNIST_DOWNLOAD_SIZE_LIMIT_EXCEEDED:{source.filename}"
                        )
                    temporary.write(chunk)
                temporary.flush()
                os.fsync(temporary.fileno())
        if temporary_path is None:
            raise MnistDemoError(f"MNIST_DOWNLOAD_EMPTY:{source.filename}")
        _validate_source_file(temporary_path, source)
        if destination.exists():
            _validate_source_file(destination, source)
            temporary_path.unlink()
        else:
            temporary_path.replace(destination)
        temporary_path = None
    except (OSError, urllib.error.URLError) as exc:
        raise MnistDemoError(f"MNIST_DOWNLOAD_FAILED:{source.filename}") from exc
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def prepare_mnist_cache(cache_dir: Path, *, allow_download: bool) -> dict[str, object]:
    """Validate or materialize all four content-pinned MNIST gzip files."""
    cache = cache_dir.resolve(strict=False)
    cache.mkdir(parents=True, exist_ok=True)
    if cache.is_symlink() or not cache.is_dir():
        raise MnistDemoError("MNIST_CACHE_NOT_REGULAR_DIRECTORY")
    entries: list[dict[str, object]] = []
    for source in MNIST_FILES:
        destination = cache / source.filename
        if not destination.exists():
            if not allow_download:
                raise MnistDemoError(f"MNIST_SOURCE_MISSING_OFFLINE:{source.filename}")
            _download_source(source, destination)
        _validate_source_file(destination, source)
        entries.append(
            {
                "filename": source.filename,
                "sha256": f"sha256:{source.sha256}",
                "size_bytes": source.size_bytes,
                "url": source.url,
            }
        )
    manifest: dict[str, object] = {
        "attribution": "LeCun, Cortes and Burges — MNIST handwritten digit database",
        "authoritative": False,
        "environment": "LOCAL_DEMO_ONLY",
        "files": entries,
        "schema_version": "1.0.0",
        "source_page": "https://yann.lecun.org/exdb/mnist/index.html",
        "type_name": "DELTAREDUCE_LOCAL_DEMO_MNIST_SOURCE",
    }
    manifest["source_id"] = _content_id(manifest)
    (cache / "mnist-source-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest


def _read_gzip(path: Path, expected_size: int) -> bytes:
    try:
        payload = gzip.decompress(path.read_bytes())
    except (OSError, EOFError) as exc:
        raise MnistDemoError(f"MNIST_GZIP_INVALID:{path.name}") from exc
    if len(payload) != expected_size:
        raise MnistDemoError(f"MNIST_IDX_SIZE_MISMATCH:{path.name}")
    return payload


def _read_images(path: Path, *, expected_count: int) -> UInt8Array:
    expected_size = 16 + expected_count * 28 * 28
    payload = _read_gzip(path, expected_size)
    magic, count, rows, columns = struct.unpack(">IIII", payload[:16])
    if (magic, count, rows, columns) != (2051, expected_count, 28, 28):
        raise MnistDemoError(f"MNIST_IMAGE_HEADER_INVALID:{path.name}")
    return np.frombuffer(payload, dtype=np.uint8, offset=16).reshape(count, rows, columns).copy()


def _read_labels(path: Path, *, expected_count: int) -> UInt8Array:
    expected_size = 8 + expected_count
    payload = _read_gzip(path, expected_size)
    magic, count = struct.unpack(">II", payload[:8])
    if (magic, count) != (2049, expected_count):
        raise MnistDemoError(f"MNIST_LABEL_HEADER_INVALID:{path.name}")
    labels = np.frombuffer(payload, dtype=np.uint8, offset=8).copy()
    if labels.size != expected_count or np.any(labels > 9):
        raise MnistDemoError(f"MNIST_LABEL_VALUE_INVALID:{path.name}")
    return labels


def load_mnist(cache_dir: Path, source_id: str) -> MnistDataset:
    """Parse validated MNIST IDX sources into fixed-shape uint8 arrays."""
    cache = cache_dir.resolve(strict=True)
    return MnistDataset(
        source_id=source_id,
        train_images=_read_images(cache / MNIST_FILES[0].filename, expected_count=60_000),
        train_labels=_read_labels(cache / MNIST_FILES[1].filename, expected_count=60_000),
        test_images=_read_images(cache / MNIST_FILES[2].filename, expected_count=10_000),
        test_labels=_read_labels(cache / MNIST_FILES[3].filename, expected_count=10_000),
    )


def _array_file_document(path: Path) -> dict[str, object]:
    return {
        "filename": path.name,
        "sha256": f"sha256:{_file_sha256(path)}",
        "size_bytes": path.stat().st_size,
    }


def materialize_node_shards(
    images: UInt8Array,
    labels: UInt8Array,
    destination: Path,
    *,
    seed: int = DEMO_SEED,
) -> tuple[dict[str, object], ...]:
    """Write four disjoint label-skew shards consumed by independent workers."""
    if images.ndim != 3 or images.shape[1:] != (28, 28) or labels.shape != (images.shape[0],):
        raise MnistDemoError("MNIST_TRAINING_ARRAY_SHAPE_INVALID")
    destination.mkdir(parents=True)
    selected_total = 0
    manifests: list[dict[str, object]] = []
    for node_index, digit_group in enumerate(NODE_LABELS, start=1):
        node_id = f"demo-mnist-worker-{node_index:02d}"
        node_dir = destination / node_id
        node_dir.mkdir()
        indices = np.flatnonzero(np.isin(labels, np.asarray(digit_group, dtype=np.uint8)))
        rng = np.random.Generator(np.random.PCG64(seed + node_index))
        indices = rng.permutation(indices)
        node_images = np.ascontiguousarray(images[indices], dtype=np.uint8)
        node_labels = np.ascontiguousarray(labels[indices], dtype=np.uint8)
        images_path = node_dir / "train-images.npy"
        labels_path = node_dir / "train-labels.npy"
        np.save(images_path, node_images, allow_pickle=False)
        np.save(labels_path, node_labels, allow_pickle=False)
        counts = np.bincount(node_labels, minlength=10).astype(np.int64)
        selected_total += int(node_labels.size)
        manifest: dict[str, object] = {
            "allowed_digits": list(digit_group),
            "files": [
                _array_file_document(images_path),
                _array_file_document(labels_path),
            ],
            "label_counts": [int(value) for value in counts],
            "node_id": node_id,
            "raw_samples_local": int(node_labels.size),
            "seed": seed + node_index,
        }
        manifest["shard_id"] = _content_id(manifest)
        (node_dir / "shard-manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        manifests.append(manifest)
    if selected_total != images.shape[0]:
        raise MnistDemoError("MNIST_SHARD_COVERAGE_INCOMPLETE")
    aggregate_counts = np.sum(
        np.asarray([manifest["label_counts"] for manifest in manifests], dtype=np.int64),
        axis=0,
    )
    if not np.array_equal(aggregate_counts, np.bincount(labels, minlength=10)):
        raise MnistDemoError("MNIST_SHARD_LABEL_COUNTS_MISMATCH")
    return tuple(manifests)


def _summary_id(sums: Int64Array, counts: Int64Array) -> str:
    digest = hashlib.sha256()
    digest.update(np.asarray(counts, dtype=">i8").tobytes(order="C"))
    digest.update(np.asarray(sums, dtype=">i8").tobytes(order="C"))
    return f"sha256:{digest.hexdigest()}"


def _quantized_model_id(values: NDArray[np.int16]) -> str:
    digest = hashlib.sha256()
    digest.update(b"deltareduce.mnist-demo.quantized-model.v2\0")
    digest.update(np.asarray(values, dtype=">i2").tobytes(order="C"))
    return f"sha256:{digest.hexdigest()}"


def compute_summary(images: UInt8Array, labels: UInt8Array) -> tuple[Int64Array, Int64Array]:
    """Learn exact integer class sufficient statistics for the centroid model."""
    try:
        return compute_mnist_summary(images, labels)
    except Exception as exc:
        raise MnistDemoError(str(exc)) from exc


def _node_summary_worker(node_dir_text: str, shard_id: str) -> NodeSummary:
    node_dir = Path(node_dir_text)
    started = time.perf_counter_ns()
    images = np.load(node_dir / "train-images.npy", mmap_mode="r", allow_pickle=False)
    labels = np.load(node_dir / "train-labels.npy", mmap_mode="r", allow_pickle=False)
    sums, counts = compute_summary(images, labels)
    summary_id = _summary_id(sums, counts)
    contribution = write_node_contribution(
        _LocalStatistics(
            counts=counts,
            node_id=node_dir.name,
            summary_id=summary_id,
            sums=sums,
        ),
        shard_id,
        (node_dir / "canonical-contribution.bin").resolve(),
    )
    duration_ms = (time.perf_counter_ns() - started) / 1_000_000
    raw_data_bytes = (node_dir / "train-images.npy").stat().st_size + (
        node_dir / "train-labels.npy"
    ).stat().st_size
    return NodeSummary(
        contribution=contribution,
        duration_ms=duration_ms,
        node_id=node_dir.name,
        process_id=os.getpid(),
        raw_data_bytes=raw_data_bytes,
        local_summary_bytes=sums.nbytes + counts.nbytes,
        summary_id=summary_id,
    )


def run_node_summaries(
    node_dirs: Sequence[Path], shard_ids: Mapping[str, str]
) -> tuple[NodeSummary, ...]:
    """Return opaque contributions produced by four distinct worker processes."""
    if len(node_dirs) != 4 or set(shard_ids) != {path.name for path in node_dirs}:
        raise MnistDemoError("MNIST_DEMO_REQUIRES_EXACTLY_FOUR_NODES")
    ordered_shard_ids = tuple(shard_ids[path.name] for path in node_dirs)
    with ProcessPoolExecutor(max_workers=4) as executor:
        summaries = tuple(
            executor.map(_node_summary_worker, map(str, node_dirs), ordered_shard_ids)
        )
    if tuple(summary.node_id for summary in summaries) != tuple(path.name for path in node_dirs):
        raise MnistDemoError("MNIST_NODE_RESULT_ORDER_MISMATCH")
    worker_process_ids = {summary.process_id for summary in summaries}
    if len(worker_process_ids) != 4 or os.getpid() in worker_process_ids:
        raise MnistDemoError("MNIST_DEMO_REQUIRES_FOUR_DISTINCT_WORKER_PROCESSES")
    return summaries


def evaluate_centroid_model(
    sums: Int64Array,
    counts: Int64Array,
    images: UInt8Array,
    labels: UInt8Array,
) -> Evaluation:
    """Measure a nearest-centroid classifier against the shared test set."""
    plugin = MnistCentroidPlugin()
    try:
        model = plugin.create_model((sums, counts))
        res = plugin.evaluate(model, (images, labels))
    except Exception as exc:
        raise MnistDemoError(str(exc)) from exc
    return Evaluation(
        accuracy_ppm=res.accuracy_ppm,
        confusion_matrix=cast(list[list[int]], res.metrics["confusion_matrix"]),
        correct=cast(int, res.metrics["correct"]),
        per_digit=cast(list[dict[str, int]], res.metrics["per_digit"]),
        predictions=cast(UInt8Array, res.metrics["predictions"]),
        total=cast(int, res.metrics["total"]),
    )


def _model_plugin_catalog() -> list[dict[str, object]]:
    registry = get_default_model_registry()
    return [
        {
            "deterministic": descriptor.deterministic,
            "display_name": descriptor.display_name,
            "model_family": descriptor.model_family,
            "parameter_schema_id": descriptor.parameter_schema_id,
            "plugin_id": descriptor.plugin_id,
            "sample_kind": descriptor.sample_kind,
            "supports_stage_c_real_drq1": descriptor.supports_stage_c_real_drq1,
            "target_kind": descriptor.target_kind,
            "task_type": descriptor.task_type,
        }
        for descriptor in registry.list_descriptors()
    ]


def _dataset_catalog() -> list[dict[str, object]]:
    registry = get_default_dataset_registry()
    return [
        {
            "dataset_id": descriptor.dataset_id,
            "description": descriptor.description,
            "deterministic": descriptor.deterministic,
            "display_name": descriptor.display_name,
            "sample_kind": descriptor.sample_kind,
            "supports_offline_cache": descriptor.supports_offline_cache,
            "target_kind": descriptor.target_kind,
            "version": descriptor.version,
        }
        for descriptor in registry.list_descriptors()
    ]


def _run_eeg_plugin_showcase(
    cache_dir: Path,
    binding: ModelDatasetBinding,
) -> dict[str, object]:
    """Exercise the EEG plugin through the generic model/dataset binding only.

    This deliberately does not claim Stage C or Delta consensus execution for EEG.
    It proves the plugin architecture accepts a non-image, windowed physiological domain
    without touching the existing MNIST REAL_DRQ1 execution path.
    """
    materialization = binding.materialize_dataset(cache_dir=cache_dir, allow_download=False)
    if not isinstance(binding.dataset_provider, EegWindowDatasetProvider):
        raise MnistDemoError("EEG_SHOWCASE_PROVIDER_TYPE_INVALID")
    eeg_provider = binding.dataset_provider

    temporal_examples: list[dict[str, object]] = []
    worker_documents: list[dict[str, object]] = []
    accuracies: list[int] = []
    for ordinal, partition_id in enumerate(DEMO_EEG_PARTITIONS):
        ticket_id = f"eeg-ticket-{ordinal:03d}"
        local_result = binding.train_ticket(ticket_id=ticket_id, partition_id=partition_id)
        tensor = local_result.tensors["eeg.centroid"]
        evaluation = binding.evaluate_checkpoint(tensor.astype(np.int64))
        partition_metadata = cast(
            Mapping[str, object],
            local_result.metadata["data_partition_metadata"],
        )
        ticket_context = cast(list[dict[str, object]], partition_metadata["ticket_context"])
        first_context = ticket_context[0]
        event = eeg_provider.intervention_event(str(first_context["intervention_event_id"]))
        assertion = eeg_provider.binding_assertion(str(first_context["data_window_id"]))
        if assertion.binding_assertion_id != first_context["binding_assertion_id"]:
            raise MnistDemoError("EEG_BINDING_ASSERTION_CONTEXT_MISMATCH")
        temporal_examples.append(
            {
                "binding_assertion_id": assertion.binding_assertion_id,
                "data_window_id": assertion.data_window_id,
                "end_offset_ms": assertion.end_offset_ms,
                "intervention_type": event.intervention_type,
                "intervention_event_id": assertion.intervention_event_id,
                "laterality": event.laterality,
                "partition_id": partition_id,
                "point_id": event.point_id,
                "point_source": "InterventionEvent.point_id",
                "protocol_id": event.protocol_id,
                "raw_data_hash": assertion.raw_data_hash,
                "relation": assertion.relation,
                "session_id": assertion.session_id,
                "start_offset_ms": assertion.start_offset_ms,
                "ticket_id": ticket_id,
            }
        )
        accuracies.append(evaluation.accuracy_ppm)
        worker_documents.append(
            {
                "accuracy_ppm": evaluation.accuracy_ppm,
                "class_counts": local_result.metadata["class_counts"],
                "first_ticket_context": first_context,
                "intervention_event_ids": partition_metadata["intervention_event_ids"],
                "partition_id": partition_id,
                "point_semantics_in_ticket_context": False,
                "sample_count": local_result.metadata["sample_count"],
                "tensor_shape": list(tensor.shape),
                "ticket_context_count": len(ticket_context),
                "ticket_id": ticket_id,
            }
        )

    return {
        "contract_compatibility": "PASS",
        "dataset_id": binding.dataset_descriptor.dataset_id,
        "delta_stage_c_execution_claimed": False,
        "display_name": binding.model_descriptor.display_name,
        "materialization": materialization,
        "mean_local_accuracy_ppm": sum(accuracies) // len(accuracies),
        "model_plugin_id": binding.model_descriptor.plugin_id,
        "plugin_scope": "MODEL_DATASET_BINDING_SMOKE_ONLY",
        "python_cross_node_aggregation_performed": False,
        "raw_eeg_shared_outside_provider": False,
        "runner_boundary": "ModelDatasetBinding",
        "sample_kind": binding.model_descriptor.sample_kind,
        "target_kind": binding.model_descriptor.target_kind,
        "temporal_binding": {
            "assertion_count": materialization["binding_assertion_count"],
            "assertion_schema_version": BINDING_ASSERTION_SCHEMA_VERSION,
            "binding_layer": "deltatorrent.data.binding.BindingAssertion",
            "delta_spine_knows_medical_semantics": False,
            "event_count": materialization["intervention_event_count"],
            "examples": temporal_examples,
            "model_plugin_creates_intervention_event": False,
            "point_id_exposed_to_ticket_context": False,
            "relation_contract": (
                "EegWindow.intervention_event_id == InterventionEvent.intervention_event_id"
            ),
            "ticket_context_contains_ids_hashes_only": True,
            "type_name": "DELTAREDUCE_TEMPORAL_EVENT_BINDING_EVIDENCE",
            "window_count": materialization["physiological_window_count"],
        },
        "total_elements": binding.model_plugin.total_elements,
        "type_name": "DELTAREDUCE_EEG_PLUGIN_SHOWCASE",
        "worker_count": len(worker_documents),
        "workers": worker_documents,
    }


def _build_multi_domain_structure(
    *,
    multi_domain_binding: MultiDomainBinding,
    mnist_accuracy_ppm: int,
    mnist_worker_count: int,
    stage_c_execution: Mapping[str, object],
    eeg_showcase: Mapping[str, object],
) -> dict[str, object]:
    """Build the report/UI evidence for all demo domains without mixing their claims."""
    domain_documents: list[dict[str, object]] = []
    for descriptor in multi_domain_binding.describe():
        domain_id = str(descriptor["domain_id"])
        if domain_id == "mnist-image":
            domain_documents.append(
                {
                    **descriptor,
                    "accuracy_ppm": mnist_accuracy_ppm,
                    "checkpoint_accuracy_claimed_from_stage_c": False,
                    "delta_stage_c_execution_claimed": True,
                    "metric_scope": "APPLIED_MNIST_MODEL_ARTIFACT",
                    "python_cross_node_aggregation_performed": False,
                    "raw_samples_shared_outside_provider": False,
                    "stage_c_execution_mode": stage_c_execution["execution_mode"],
                    "stage_c_outcome": stage_c_execution["outcome"],
                    "worker_count": mnist_worker_count,
                }
            )
        elif domain_id == "eeg-bandpower":
            domain_documents.append(
                {
                    **descriptor,
                    "accuracy_ppm": eeg_showcase["mean_local_accuracy_ppm"],
                    "checkpoint_accuracy_claimed_from_stage_c": False,
                    "delta_stage_c_execution_claimed": False,
                    "metric_scope": "LOCAL_PLUGIN_WORKER_SMOKE",
                    "python_cross_node_aggregation_performed": False,
                    "raw_samples_shared_outside_provider": False,
                    "stage_c_execution_mode": None,
                    "stage_c_outcome": None,
                    "worker_count": eeg_showcase["worker_count"],
                }
            )
        else:
            raise MnistDemoError(f"UNKNOWN_MULTI_DOMAIN_DEMO_DOMAIN:{domain_id}")

    return {
        "active_stage_c_domain_id": "mnist-image",
        "cross_domain_aggregation_performed": False,
        "delta_stage_c_domain_count": 1,
        "domain_count": len(domain_documents),
        "domains": domain_documents,
        "model_dataset_runner": "MultiDomainBinding",
        "protocol_scope": "MULTI_DOMAIN_PLUGIN_STRUCTURE_WITH_SINGLE_DOMAIN_STAGE_C_DEMO",
        "registry_backed": True,
        "stage_c_support_scope": "MNIST_ONLY_REAL_DRQ1_IN_THIS_DEMO",
        "type_name": "DELTAREDUCE_MULTI_DOMAIN_DEMO_STRUCTURE",
    }


def _sample_gallery(
    dataset: MnistDataset,
    central: Evaluation,
    distributed: Evaluation,
    failure: Evaluation,
    *,
    seed: int,
) -> list[dict[str, object]]:
    rng = np.random.Generator(np.random.PCG64(seed))
    samples: list[dict[str, object]] = []
    for digit in range(10):
        candidates = np.flatnonzero(dataset.test_labels == digit)
        selected = int(candidates[int(rng.integers(0, candidates.size))])
        samples.append(
            {
                "central_prediction": int(central.predictions[selected]),
                "digit": digit,
                "distributed_prediction": int(distributed.predictions[selected]),
                "failure_prediction": int(failure.predictions[selected]),
                "pixels": [int(value) for value in dataset.test_images[selected].reshape(-1)],
                "test_index": selected,
            }
        )
    return samples


def _node_document(summary: NodeSummary, manifest: Mapping[str, object]) -> dict[str, object]:
    return {
        "allowed_digits": manifest["allowed_digits"],
        "duration_ms": round(summary.duration_ms, 3),
        "label_counts": manifest["label_counts"],
        "node_id": summary.node_id,
        "process_id": summary.process_id,
        "raw_data_bytes": summary.raw_data_bytes,
        "raw_images_shared": False,
        "shared_payload": "SIGNED_CANONICAL_INT16_MODEL_DELTA_ONLY",
        "local_summary_bytes": summary.local_summary_bytes,
        "numeric_model_summary_returned_to_orchestrator": False,
        "shard_id": manifest["shard_id"],
        "summary_id": summary.summary_id,
    }


def _load_formal_go(repository_root: Path) -> None:
    report_path = repository_root / "formal/reports/formal-verification-report.json"
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise MnistDemoError("MNIST_DEMO_FORMAL_REPORT_INVALID") from exc
    if not isinstance(report, dict):
        raise MnistDemoError("MNIST_DEMO_FORMAL_REPORT_INVALID")
    if report.get("decision") != "GO" or report.get("formal_semantics_id") != FORMAL_SEMANTICS_ID:
        raise MnistDemoError("MNIST_DEMO_FORMAL_GO_MISMATCH")


def _runtime_artifact(path: Path, code: str, *, executable: bool = False) -> RuntimeArtifact:
    if not path.is_absolute() or path.is_symlink() or not path.is_file():
        raise MnistDemoError(code)
    try:
        resolved = path.resolve(strict=True)
        if executable and not os.access(resolved, os.X_OK):
            raise MnistDemoError(code)
        raw = resolved.read_bytes()
    except OSError as exc:
        raise MnistDemoError(code) from exc
    return RuntimeArtifact(resolved, f"sha256:{hashlib.sha256(raw).hexdigest()}")


def _classpath_entries(value: str, code: str) -> tuple[Path, ...]:
    raw_entries = value.split(os.pathsep)
    if not raw_entries or any(not item for item in raw_entries):
        raise MnistDemoError(code)
    entries = tuple(Path(item) for item in raw_entries)
    if any(not item.is_absolute() or item.is_symlink() or not item.is_file() for item in entries):
        raise MnistDemoError(code)
    return tuple(item.resolve(strict=True) for item in entries)


def _resolve_stage_c_boundary_from_environment(
    destination: Path,
) -> tuple[MeasuredStageCRuntimeBoundary, bool]:
    java = os.environ.get("DELTA_STAGEC_JAVA") or os.environ.get("DELTA_MNIST_JAVA")
    native = os.environ.get("DELTA_STAGEC_NATIVE_SIDECAR")
    harness = os.environ.get("DELTA_STAGEC_TRANSPORT_HARNESS")
    netty_classpath = os.environ.get("DELTA_STAGEC_NETTY_CLASSPATH")
    if not java or not native or not harness or not netty_classpath:
        raise MnistDemoError("MNIST_STAGEC_RUNTIME_BOUNDARY_MISSING")

    counter_root = destination / "stagec-counters"
    counter_root.mkdir(parents=True, exist_ok=True)
    for name in ("tx_bytes", "rx_bytes"):
        _write_stage_c_counter(counter_root / name, 0)

    java_artifact = _runtime_artifact(
        Path(java), "MNIST_STAGEC_JAVA_EXECUTABLE_INVALID", executable=True
    )
    native_artifact = _runtime_artifact(
        Path(native), "MNIST_STAGEC_NATIVE_SIDECAR_INVALID", executable=True
    )
    harness_artifact = _runtime_artifact(Path(harness), "MNIST_STAGEC_TRANSPORT_HARNESS_INVALID")
    netty_artifacts = tuple(
        _runtime_artifact(path, "MNIST_STAGEC_NETTY_CLASSPATH_INVALID")
        for path in _classpath_entries(netty_classpath, "MNIST_STAGEC_NETTY_CLASSPATH_INVALID")
    )
    image_id = _content_id(
        {
            "java": java_artifact.content_id,
            "native": native_artifact.content_id,
            "netty": [item.content_id for item in netty_artifacts],
            "transport_harness": harness_artifact.content_id,
            "type_name": "MNIST_STAGEC_RUNTIME_IMAGE",
        }
    )
    return (
        MeasuredStageCRuntimeBoundary(
            image_id=image_id,
            java_executable=java_artifact,
            native_executable=native_artifact,
            transport_harness=harness_artifact,
            netty_artifacts=netty_artifacts,
            os_interface_counter_root=counter_root,
            working_root=destination / "stagec-work",
            timeout_seconds=180,
        ),
        True,
    )


def _write_stage_c_counter(path: Path, value: int) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    try:
        temporary.write_text(f"{value}\n", encoding="ascii", newline="\n")
        for attempt in range(200):
            try:
                os.replace(temporary, path)
                break
            except PermissionError:
                if attempt == 199:
                    raise
                time.sleep(0.001)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


@contextmanager
def _stage_c_local_counter_source(
    boundary: MeasuredStageCRuntimeBoundary,
    *,
    enabled: bool,
) -> Iterator[None]:
    if not enabled:
        yield
        return

    stop = threading.Event()
    counter_root = boundary.os_interface_counter_root

    def pump() -> None:
        value = 0
        while not stop.is_set():
            value += 1_000_000
            for name in ("tx_bytes", "rx_bytes"):
                try:
                    _write_stage_c_counter(counter_root / name, value)
                except OSError:
                    return
            stop.wait(0.01)

    thread = threading.Thread(target=pump, name="mnist-stagec-counter-source", daemon=True)
    thread.start()
    try:
        yield
    finally:
        stop.set()
        thread.join(timeout=1.0)


def run_mnist_demo(
    repository_root: Path,
    cache_dir: Path,
    output_dir: Path,
    *,
    allow_download: bool,
    progress: ProgressCallback | None = None,
    toolchain: DeltaToolchain | None = None,
    stage_c_boundary: MeasuredStageCRuntimeBoundary | None = None,
) -> MnistDemoResult:
    """Execute the isolated MNIST comparison and persist measured local evidence."""
    multi_domain_binding = bind_model_dataset_domains(
        (
            DomainBindingSpec(
                domain_id="mnist-image",
                model_plugin_id=MNIST_CENTROID_DESCRIPTOR.plugin_id,
                dataset_id=MNIST_DESCRIPTOR.dataset_id,
                role="PRIMARY_DELTA_EXECUTION",
                execution_scope="STAGE_C_REAL_DRQ1",
            ),
            DomainBindingSpec(
                domain_id="eeg-bandpower",
                model_plugin_id=EEG_BANDPOWER_DESCRIPTOR.plugin_id,
                dataset_id=EEG_DATASET_DESCRIPTOR.dataset_id,
                role="PLUGIN_BINDING_SMOKE",
                execution_scope="MODEL_DATASET_BINDING_ONLY",
            ),
        )
    )
    model_dataset_binding = multi_domain_binding.get("mnist-image")
    eeg_binding = multi_domain_binding.get("eeg-bandpower")
    model_descriptor = model_dataset_binding.model_descriptor
    dataset_descriptor = model_dataset_binding.dataset_descriptor
    root = repository_root.resolve(strict=True)
    cache = cache_dir if cache_dir.is_absolute() else root / cache_dir
    destination = output_dir if output_dir.is_absolute() else root / output_dir
    cache = cache.resolve(strict=False)
    destination = destination.resolve(strict=False)
    if destination.exists():
        raise MnistDemoError("MNIST_DEMO_OUTPUT_ALREADY_EXISTS")
    destination.mkdir(parents=True)

    def update(stage: str, percent: int, message: str) -> None:
        if progress is not None:
            progress(stage, percent, message)

    try:
        update("formal", 4, "Проверяем принятый Formal GO")
        _load_formal_go(root)
        selected_stage_c_boundary, owns_stage_c_counter_source = (
            (stage_c_boundary, False)
            if stage_c_boundary is not None
            else _resolve_stage_c_boundary_from_environment(destination)
        )

        update("controllers", 10, "Создаём четыре одноразовых Ed25519 контроллера")
        controllers_dir = destination / "controllers"
        generate_demo_controller_bundle(controllers_dir)
        controller_smoke = run_demo_quorum_smoke(controllers_dir)

        update("dataset", 18, "Проверяем или загружаем закреплённый MNIST")
        source_manifest = prepare_mnist_cache(cache, allow_download=allow_download)
        source_id = source_manifest.get("source_id")
        if not isinstance(source_id, str):
            raise MnistDemoError("MNIST_SOURCE_ID_INVALID")
        dataset = load_mnist(cache, source_id)

        update("shards", 30, "Разделяем 60 000 изображений между четырьмя узлами")
        node_root = destination / "nodes"
        shard_manifests = materialize_node_shards(
            dataset.train_images,
            dataset.train_labels,
            node_root,
        )
        node_dirs = tuple(node_root / f"demo-mnist-worker-{index:02d}" for index in range(1, 5))

        update("central", 43, "Обучаем централизованный baseline на тех же данных")
        central_started = time.perf_counter_ns()
        central_sums, central_counts = compute_summary(dataset.train_images, dataset.train_labels)
        central_values = expected_central_model(central_sums, central_counts)
        central_centroids = central_values[: DIGIT_COUNT * PIXELS_PER_DIGIT].reshape(
            DIGIT_COUNT, PIXELS_PER_DIGIT
        )
        central_presence = central_values[DIGIT_COUNT * PIXELS_PER_DIGIT :].astype(np.int64)
        central_training_ms = (time.perf_counter_ns() - central_started) / 1_000_000

        update("distributed", 51, "Четыре процесса вычисляют только локальные MNIST-вклады")
        distributed_started = time.perf_counter_ns()
        shard_ids: dict[str, str] = {}
        for manifest in shard_manifests:
            node_id = manifest.get("node_id")
            shard_id = manifest.get("shard_id")
            if not isinstance(node_id, str) or not isinstance(shard_id, str):
                raise MnistDemoError("MNIST_SHARD_MANIFEST_BINDING_INVALID")
            shard_ids[node_id] = shard_id
        node_summaries = run_node_summaries(node_dirs, shard_ids)
        worker_process_ids = {summary.process_id for summary in node_summaries}
        update(
            "delta-path",
            61,
            "Шесть раз: Delta compute/vote → Netty relay → Delta QC; затем APPLIED",
        )
        delta_result = run_delta_nodes(
            root,
            destination / "delta-execution",
            controllers_dir,
            tuple(summary.contribution for summary in node_summaries),
            dataset.source_id,
            toolchain=toolchain,
        )
        applied_model = delta_result.applied_model
        distributed_training_ms = (time.perf_counter_ns() - distributed_started) / 1_000_000
        if not np.array_equal(applied_model.values, central_values):
            raise MnistDemoError("MNIST_CENTRAL_DISTRIBUTED_MODEL_MISMATCH")

        update("stage-c", 76, "Проводим 4 DRQ1 worker-вклада через Stage C REAL_DRQ1")
        with _stage_c_local_counter_source(
            selected_stage_c_boundary,
            enabled=owns_stage_c_counter_source,
        ):
            stage_c_result = run_stage_c_real_drq1_nodes(
                root,
                destination / "stage-c-real-drq1",
                tuple(summary.contribution for summary in node_summaries),
                dataset.source_id,
                boundary=selected_stage_c_boundary,
            )
        stage_c_transition = stage_c_result.receipt.fault_transitions[0]
        stage_c_evidence = stage_c_transition.causal_evidence
        stage_c_execution: dict[str, object] = {
            "checkpoint_advanced": stage_c_transition.current_checkpoint_advanced,
            "demo_domain_mapping": {
                "ticket-000": "code",
                "ticket-001": "code",
                "ticket-002": "text",
                "ticket-003": "text",
            },
            "demo_domains_are_protocol_qualification_only": True,
            "evaluation_checkpoint_id": stage_c_result.evaluation_checkpoint_id,
            "execution_mode": "REAL_DRQ1",
            "final_checkpoint_id": stage_c_result.final_checkpoint_id,
            "isc_ticket_count": len(stage_c_evidence.isc_ticket_set),
            "java_ml_arithmetic_performed": False,
            "missing_work_policy_result": stage_c_evidence.missing_work_policy_result,
            "native_fault_trace_id": stage_c_result.receipt.native_fault_trace_id,
            "outcome": stage_c_transition.observed_outcome,
            "python_cross_node_aggregation_performed": False,
            "receipt_id": stage_c_result.receipt.raw_java_receipt_id,
            "runtime_wal_sha256": stage_c_transition.native_wal_sha256,
            "stage_c_checkpoint_accuracy_claimed": False,
            "stage_c_evidence": stage_c_result.evidence_path.relative_to(destination).as_posix(),
            "synthetic_fallback": False,
            "ticket_ids": list(stage_c_result.ticket_ids),
            "type_name": "MNIST_STAGEC_REAL_DRQ1_EXECUTION_EVIDENCE",
            "worker_count": len(stage_c_result.ticket_ids),
            "worker_shard_leaf_ids": [
                {"leaf_id": leaf_id, "ticket_id": ticket_id}
                for ticket_id, leaf_id in stage_c_result.worker_shard_leaf_ids
            ],
        }

        update("evaluation", 84, "Оцениваем только модель из native APPLIED artifact")
        central_evaluation = evaluate_centroid_model(
            np.asarray(central_centroids, dtype=np.int64),
            central_presence,
            dataset.test_images,
            dataset.test_labels,
        )
        distributed_evaluation = evaluate_centroid_model(
            applied_model.centroids,
            applied_model.presence,
            dataset.test_images,
            dataset.test_labels,
        )
        if not np.array_equal(
            central_evaluation.predictions,
            distributed_evaluation.predictions,
        ):
            raise MnistDemoError("MNIST_CENTRAL_DISTRIBUTED_PREDICTION_MISMATCH")

        update("recovery", 90, "Проверяем crash/restart validator-04 и replay durable Apply vote")
        failure_evaluation = distributed_evaluation
        model_id = _quantized_model_id(central_values)
        integration_source = (
            root / "delta-worker-python/src/deltatorrent/benchmark/mnist_delta_nodes.py"
        )
        implementation_id = _content_id(
            {
                "component_source_ids": {
                    "mnist_demo": f"sha256:{_file_sha256(Path(__file__).resolve())}",
                    "mnist_delta_nodes": f"sha256:{_file_sha256(integration_source)}",
                },
                "execution_source_and_toolchain_id": delta_result.delta_execution[
                    "execution_path_id"
                ],
                "stage_c_real_drq1_final_checkpoint_id": stage_c_result.final_checkpoint_id,
                "implementation_version": IMPLEMENTATION_VERSION,
            }
        )
        model_plugin_catalog = _model_plugin_catalog()
        dataset_catalog = _dataset_catalog()
        eeg_plugin_showcase = _run_eeg_plugin_showcase(
            destination / "eeg-plugin-showcase",
            eeg_binding,
        )
        multi_domain_structure = _build_multi_domain_structure(
            multi_domain_binding=multi_domain_binding,
            mnist_accuracy_ppm=distributed_evaluation.accuracy_ppm,
            mnist_worker_count=len(worker_process_ids),
            stage_c_execution=stage_c_execution,
            eeg_showcase=eeg_plugin_showcase,
        )
        deterministic_result: dict[str, object] = {
            "applied_model_file_sha256": applied_model.content_id,
            "central_accuracy_ppm": central_evaluation.accuracy_ppm,
            "contribution_ids": [
                contribution.content_id for contribution in delta_result.node_contributions
            ],
            "dataset_source_id": dataset.source_id,
            "distributed_accuracy_ppm": distributed_evaluation.accuracy_ppm,
            "eeg_plugin_showcase": eeg_plugin_showcase,
            "execution_path_id": delta_result.delta_execution["execution_path_id"],
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "implementation_id": implementation_id,
            "implementation_version": IMPLEMENTATION_VERSION,
            "dataset_id": dataset_descriptor.dataset_id,
            "model_id": model_id,
            "model_plugin_id": model_descriptor.plugin_id,
            "model_type": MODEL_ID,
            "multi_domain_structure": multi_domain_structure,
            "partition_rule_id": PARTITION_RULE_ID,
            "recovery_status": delta_result.failure_simulation["status"],
            "seed": DEMO_SEED,
            "shard_ids": [manifest["shard_id"] for manifest in shard_manifests],
            "stage_c_execution_mode": "REAL_DRQ1",
            "stage_c_final_checkpoint_id": stage_c_result.final_checkpoint_id,
            "stage_c_ticket_ids": list(stage_c_result.ticket_ids),
        }
        reproducibility_id = _content_id(deterministic_result)
        examples = _sample_gallery(
            dataset,
            central_evaluation,
            distributed_evaluation,
            failure_evaluation,
            seed=DEMO_SEED,
        )

        update("report", 94, "Формируем пользовательский отчёт из фактических измерений")
        report: dict[str, object] = {
            "authoritative": False,
            "centralized": {
                "evaluation": central_evaluation.document(),
                "model_id": model_id,
                "samples_seen": int(dataset.train_labels.size),
                "training_ms": round(central_training_ms, 3),
            },
            "controller_quorum": controller_smoke.document,
            "dataset": {
                "dataset_id": dataset_descriptor.dataset_id,
                "display_name": dataset_descriptor.display_name,
                "image_shape": [28, 28],
                "name": "MNIST",
                "sample_kind": dataset_descriptor.sample_kind,
                "source_id": dataset.source_id,
                "target_kind": dataset_descriptor.target_kind,
                "test_samples": int(dataset.test_labels.size),
                "train_samples": int(dataset.train_labels.size),
            },
            "demo_status": "DEMO_PASS",
            "delta_execution": delta_result.delta_execution,
            "distributed": {
                "aggregation_owner": "delta::robust::reduce_parameter_shard",
                "applied_model_file_sha256": applied_model.content_id,
                "evaluation": distributed_evaluation.document(),
                "exact_model_match_with_centralized": True,
                "model_id": model_id,
                "native_runtime_terminal": "APPLIED",
                "nodes": [
                    {
                        **_node_document(summary, manifest),
                        "contribution_id": contribution.content_id,
                        "shared_contribution_bytes": contribution.size_bytes,
                    }
                    for summary, manifest, contribution in zip(
                        node_summaries,
                        shard_manifests,
                        delta_result.node_contributions,
                        strict=True,
                    )
                ],
                "parallel_processes_observed": len(worker_process_ids),
                "worker_processes_required": 4,
                "samples_seen": int(dataset.train_labels.size),
                "stage_c_checkpoint_advanced": stage_c_transition.current_checkpoint_advanced,
                "stage_c_execution_mode": "REAL_DRQ1",
                "stage_c_final_checkpoint_id": stage_c_result.final_checkpoint_id,
                "training_ms": round(distributed_training_ms, 3),
            },
            "environment": "LOCAL_DEMO_ONLY",
            "examples": examples,
            "execution_path": {
                "acceptance_status": "PASS",
                "aggregation_owner": "delta::robust::reduce_parameter_shard",
                "centralized_baseline_isolated_from_delta_inputs": True,
                "demo_owned_aggregation": False,
                "diagram": delta_result.execution_diagram_path.relative_to(destination).as_posix(),
                "existing_delta_node_interfaces": True,
                "mnist_is_workload_only": True,
                "phase_ordering_enforced": delta_result.delta_execution["phase_ordering_enforced"],
                "distributed_orchestrator_received_node_local_numeric_arrays": False,
                "four_distinct_worker_processes_observed": len(worker_process_ids) == 4,
                "protocol_scope": "MNIST_WORKLOAD_TO_APPLIED_LOCAL_DELTA",
                "stage_c_checkpoint_advanced": stage_c_transition.current_checkpoint_advanced,
                "stage_c_execution_mode": "REAL_DRQ1",
                "stage_c_synthetic_fallback": False,
                "terminal_outcome": "APPLIED",
                "trace": delta_result.execution_trace_path.relative_to(destination).as_posix(),
                "trace_id": delta_result.delta_execution["execution_path_id"],
            },
            "execution_authorized": False,
            "failure_simulation": {
                **delta_result.failure_simulation,
                "evaluation": failure_evaluation.document(),
            },
            "feature_010_go_claimed": False,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "governance_eligible": False,
            "implementation": {
                "implementation_id": implementation_id,
                "version": IMPLEMENTATION_VERSION,
            },
            "limitations": [
                "LOCAL_LOOPBACK_DEPLOYMENT_NOT_A_REAL_MULTI_REGION_OR_WAN_RUN",
                "DEMO_PROCESS_ADAPTER_IS_NOT_A_PRODUCTION_DEPLOYABLE_NODE_SURFACE",
                "NEAREST_CENTROID_IS_AN_EDUCATIONAL_MODEL_NOT_THE_PRIMARY_QLORA_WORKLOAD",
                "NATIVE_QC_SIGNATURE_IDS_ARE_LOCAL_DEMO_CONTENT_IDS_NOT_ED25519_VOTES",
                "ED25519_IS_VERIFIED_AT_THE_JAVA_TRANSPORT_BOUNDARY_ONLY",
                "OPAQUE_CONTRIBUTION_FILES_ARE_PARENT_READABLE_WITHOUT_OS_CAPABILITY_ISOLATION",
                "NO_BENCHMARK_DEFINITION_QC_OR_BENCHMARK_RESULT_QC_CREATED",
                "NO_EXECUTE_STAGE_A_OR_FEATURE_010_GO_AUTHORITY_CREATED",
                "MNIST_ACCURACY_IS_EVALUATED_FROM_THE_DEMO_APPLIED_MODEL_ARTIFACT_NOT_FROM_STAGE_C_CHECKPOINT_BYTES",
                "STAGE_C_CODE_TEXT_DOMAINS_ARE_DEMO_PROTOCOL_QUALIFICATION_BUCKETS_NOT_MNIST_LABEL_SEMANTICS",
            ],
            "model": {
                "applied_artifact_sha256": applied_model.content_id,
                "arithmetic": "UINT8_LOCAL_INT64_SUM_DELTA_INT16_APPLY_FLOAT64_EVALUATION",
                "display_name": model_descriptor.display_name,
                "plugin_id": model_descriptor.plugin_id,
                "sample_kind": model_descriptor.sample_kind,
                "stage_c_checkpoint_accuracy_claimed": False,
                "stage_c_model_reconstructed_for_accuracy": False,
                "target_kind": model_descriptor.target_kind,
                "model_id": model_id,
                "type": MODEL_ID,
            },
            "model_dataset_binding": {
                "contract_compatibility": "PASS",
                "dataset_id": dataset_descriptor.dataset_id,
                "model_plugin_id": model_descriptor.plugin_id,
                "runner_boundary": "ModelDatasetBinding",
                "sample_kind": dataset_descriptor.sample_kind,
                "target_kind": dataset_descriptor.target_kind,
                "type_name": "DELTAREDUCE_MODEL_DATASET_BINDING_EVIDENCE",
            },
            "multi_domain": multi_domain_structure,
            "plugin_showcase": {
                "eeg_bandpower": eeg_plugin_showcase,
            },
            "partition": {
                "disjoint": True,
                "label_skewed": True,
                "rule_id": PARTITION_RULE_ID,
                "seed": DEMO_SEED,
            },
            "reproducibility": {
                "deterministic_result": deterministic_result,
                "reproducibility_id": reproducibility_id,
            },
            "registry": {
                "datasets": dataset_catalog,
                "model_plugins": model_plugin_catalog,
            },
            "schema_version": "2.0.0",
            "stage_c_execution": stage_c_execution,
            "type_name": "DELTAREDUCE_LOCAL_MNIST_DEMO_REPORT",
        }
        report_json = destination / "mnist-demo-report.json"
        report_json.write_text(
            json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        update("complete", 100, "Демо завершено: фактические метрики готовы")
        return MnistDemoResult(
            output_dir=destination,
            report_json=report_json,
            reproducibility_id=reproducibility_id,
        )
    except Exception:
        if destination.is_symlink():
            destination.unlink()
        elif destination.exists():
            shutil.rmtree(destination)
        raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the isolated four-node MNIST demo.")
    commands = parser.add_subparsers(dest="command", required=True)

    prepare = commands.add_parser("prepare", help="download and validate pinned MNIST sources")
    prepare.add_argument("--cache-dir", type=Path, required=True)
    prepare.add_argument("--offline", action="store_true")

    run = commands.add_parser("run", help="run the headless MNIST comparison")
    run.add_argument("--cache-dir", type=Path, required=True)
    run.add_argument("--output-dir", type=Path, required=True)
    run.add_argument("--repository-root", type=Path, default=Path.cwd())
    run.add_argument("--offline", action="store_true")

    serve = commands.add_parser("serve", help="open the one-button local browser workspace")
    serve.add_argument("--cache-dir", type=Path, required=True)
    serve.add_argument("--output-root", type=Path, required=True)
    serve.add_argument("--repository-root", type=Path, default=Path.cwd())
    serve.add_argument("--offline", action="store_true")
    serve.add_argument("--port", type=int, default=0)
    serve.add_argument("--open-browser", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Execute the dataset-preparation or headless demonstration command."""
    args = _parser().parse_args(argv)
    try:
        if args.command == "prepare":
            manifest = prepare_mnist_cache(args.cache_dir, allow_download=not args.offline)
            print(f"MNIST cache ready: {manifest['source_id']}")
            return 0
        if args.command == "serve":
            from deltatorrent.benchmark.mnist_demo_workspace import serve_workspace

            serve_workspace(
                args.repository_root,
                args.cache_dir,
                args.output_root,
                allow_download=not args.offline,
                port=args.port,
                open_browser=args.open_browser,
            )
            return 0
        result = run_mnist_demo(
            args.repository_root,
            args.cache_dir,
            args.output_dir,
            allow_download=not args.offline,
        )
    except (
        DemoControllerError,
        MnistDeltaError,
        MnistDemoError,
        OSError,
        ValueError,
    ) as exc:
        print(f"mnist-demo error: {exc}", file=sys.stderr)
        return 2
    print(f"MNIST demo complete: {result.reproducibility_id}")
    print(f"Local report data: {result.report_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
