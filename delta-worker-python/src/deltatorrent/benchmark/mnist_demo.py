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
import math
import os
import shutil
import struct
import sys
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from deltatorrent.benchmark.campaign02_demo_controllers import (
    DemoControllerError,
    generate_demo_controller_bundle,
    run_demo_quorum_smoke,
)
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.benchmark.mnist_delta_nodes import (
    DIGIT_COUNT,
    PIXELS_PER_DIGIT,
    DeltaToolchain,
    MnistDeltaError,
    expected_central_model,
    run_delta_nodes,
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
    """Sufficient statistics emitted by one isolated demo worker."""

    counts: Int64Array
    duration_ms: float
    node_id: str
    process_id: int
    raw_data_bytes: int
    shared_summary_bytes: int
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
    if images.ndim != 3 or images.shape[1:] != (28, 28) or labels.shape != (images.shape[0],):
        raise MnistDemoError("MNIST_SUMMARY_ARRAY_SHAPE_INVALID")
    flat = images.reshape(images.shape[0], 28 * 28)
    counts = np.bincount(labels, minlength=10).astype(np.int64)
    sums = np.stack(
        [flat[labels == digit].sum(axis=0, dtype=np.int64) for digit in range(10)],
        axis=0,
    )
    return np.asarray(sums, dtype=np.int64), counts


def _node_summary_worker(node_dir_text: str) -> NodeSummary:
    node_dir = Path(node_dir_text)
    started = time.perf_counter_ns()
    images = np.load(node_dir / "train-images.npy", mmap_mode="r", allow_pickle=False)
    labels = np.load(node_dir / "train-labels.npy", mmap_mode="r", allow_pickle=False)
    sums, counts = compute_summary(images, labels)
    duration_ms = (time.perf_counter_ns() - started) / 1_000_000
    raw_data_bytes = (node_dir / "train-images.npy").stat().st_size + (
        node_dir / "train-labels.npy"
    ).stat().st_size
    return NodeSummary(
        counts=counts,
        duration_ms=duration_ms,
        node_id=node_dir.name,
        process_id=os.getpid(),
        raw_data_bytes=raw_data_bytes,
        shared_summary_bytes=sums.nbytes + counts.nbytes,
        summary_id=_summary_id(sums, counts),
        sums=sums,
    )


def run_node_summaries(node_dirs: Sequence[Path], *, parallel: bool) -> tuple[NodeSummary, ...]:
    """Run each shard consumer separately; use four OS processes in presentation mode."""
    if len(node_dirs) != 4:
        raise MnistDemoError("MNIST_DEMO_REQUIRES_EXACTLY_FOUR_NODES")
    if parallel:
        with ProcessPoolExecutor(max_workers=4) as executor:
            summaries = tuple(executor.map(_node_summary_worker, map(str, node_dirs)))
    else:
        summaries = tuple(_node_summary_worker(str(path)) for path in node_dirs)
    if tuple(summary.node_id for summary in summaries) != tuple(path.name for path in node_dirs):
        raise MnistDemoError("MNIST_NODE_RESULT_ORDER_MISMATCH")
    return summaries


def evaluate_centroid_model(
    sums: Int64Array,
    counts: Int64Array,
    images: UInt8Array,
    labels: UInt8Array,
) -> Evaluation:
    """Measure a nearest-centroid classifier against the shared test set."""
    if sums.shape != (10, 28 * 28) or counts.shape != (10,):
        raise MnistDemoError("MNIST_MODEL_SHAPE_INVALID")
    if images.ndim != 3 or images.shape[1:] != (28, 28) or labels.shape != (images.shape[0],):
        raise MnistDemoError("MNIST_TEST_ARRAY_SHAPE_INVALID")
    valid_classes = counts > 0
    if not bool(np.any(valid_classes)):
        raise MnistDemoError("MNIST_MODEL_HAS_NO_CLASSES")
    centroids = np.divide(
        sums,
        counts[:, None],
        out=np.zeros_like(sums, dtype=np.float64),
        where=counts[:, None] != 0,
    )
    centroid_norm = np.square(centroids).sum(axis=1)
    predictions: list[UInt8Array] = []
    flat_images = images.reshape(images.shape[0], 28 * 28)
    for start in range(0, flat_images.shape[0], 512):
        batch = flat_images[start : start + 512].astype(np.float64)
        distances = (
            np.square(batch).sum(axis=1)[:, None]
            - 2.0 * batch @ centroids.T
            + centroid_norm[None, :]
        )
        distances[:, ~valid_classes] = math.inf
        predictions.append(distances.argmin(axis=1).astype(np.uint8))
    predicted = np.concatenate(predictions)
    correct = int(np.count_nonzero(predicted == labels))
    total = int(labels.size)
    confusion = np.zeros((10, 10), dtype=np.int64)
    np.add.at(confusion, (labels, predicted), 1)
    per_digit: list[dict[str, int]] = []
    for digit in range(10):
        mask = labels == digit
        digit_total = int(np.count_nonzero(mask))
        digit_correct = int(np.count_nonzero(predicted[mask] == digit))
        per_digit.append(
            {
                "accuracy_ppm": digit_correct * 1_000_000 // digit_total,
                "correct": digit_correct,
                "digit": digit,
                "total": digit_total,
            }
        )
    return Evaluation(
        accuracy_ppm=correct * 1_000_000 // total,
        confusion_matrix=[[int(value) for value in row] for row in confusion],
        correct=correct,
        per_digit=per_digit,
        predictions=predicted,
        total=total,
    )


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
        "label_counts": [int(value) for value in summary.counts],
        "node_id": summary.node_id,
        "process_id": summary.process_id,
        "raw_data_bytes": summary.raw_data_bytes,
        "raw_images_shared": False,
        "shared_payload": "SIGNED_CANONICAL_INT16_MODEL_DELTA_ONLY",
        "shared_summary_bytes": summary.shared_summary_bytes,
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


def run_mnist_demo(
    repository_root: Path,
    cache_dir: Path,
    output_dir: Path,
    *,
    allow_download: bool,
    parallel: bool = True,
    progress: ProgressCallback | None = None,
    toolchain: DeltaToolchain | None = None,
) -> MnistDemoResult:
    """Execute the isolated MNIST comparison and persist measured local evidence."""
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
        node_summaries = run_node_summaries(node_dirs, parallel=parallel)
        shard_ids: dict[str, str] = {}
        for manifest in shard_manifests:
            node_id = manifest.get("node_id")
            shard_id = manifest.get("shard_id")
            if not isinstance(node_id, str) or not isinstance(shard_id, str):
                raise MnistDemoError("MNIST_SHARD_MANIFEST_BINDING_INVALID")
            shard_ids[node_id] = shard_id
        update(
            "delta-path",
            61,
            "Netty передаёт вклады: Delta пишет WAL, собирает QC, выполняет reduce и Apply",
        )
        delta_result = run_delta_nodes(
            root,
            destination / "delta-execution",
            controllers_dir,
            node_summaries,
            shard_ids,
            dataset.source_id,
            toolchain=toolchain,
        )
        applied_model = delta_result.applied_model
        distributed_training_ms = (time.perf_counter_ns() - distributed_started) / 1_000_000
        if not np.array_equal(applied_model.values, central_values):
            raise MnistDemoError("MNIST_CENTRAL_DISTRIBUTED_MODEL_MISMATCH")

        update("evaluation", 82, "Оцениваем только модель из native APPLIED artifact")
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

        update("recovery", 89, "Проверяем crash/restart validator-04 и replay durable Apply vote")
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
                "implementation_version": IMPLEMENTATION_VERSION,
            }
        )
        deterministic_result: dict[str, object] = {
            "applied_model_file_sha256": applied_model.content_id,
            "central_accuracy_ppm": central_evaluation.accuracy_ppm,
            "contribution_ids": [
                contribution.content_id for contribution in delta_result.node_contributions
            ],
            "dataset_source_id": dataset.source_id,
            "distributed_accuracy_ppm": distributed_evaluation.accuracy_ppm,
            "execution_path_id": delta_result.delta_execution["execution_path_id"],
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "implementation_id": implementation_id,
            "implementation_version": IMPLEMENTATION_VERSION,
            "model_id": model_id,
            "model_type": MODEL_ID,
            "partition_rule_id": PARTITION_RULE_ID,
            "recovery_status": delta_result.failure_simulation["status"],
            "seed": DEMO_SEED,
            "shard_ids": [manifest["shard_id"] for manifest in shard_manifests],
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
                "image_shape": [28, 28],
                "name": "MNIST",
                "source_id": dataset.source_id,
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
                        "shared_contribution_bytes": len(contribution.record_bytes),
                    }
                    for summary, manifest, contribution in zip(
                        node_summaries,
                        shard_manifests,
                        delta_result.node_contributions,
                        strict=True,
                    )
                ],
                "parallel_processes_observed": len(
                    {summary.process_id for summary in node_summaries}
                ),
                "samples_seen": int(dataset.train_labels.size),
                "training_ms": round(distributed_training_ms, 3),
            },
            "environment": "LOCAL_DEMO_ONLY",
            "examples": examples,
            "execution_path": {
                "acceptance_status": "PASS",
                "aggregation_owner": "delta::robust::reduce_parameter_shard",
                "demo_owned_aggregation": False,
                "diagram": delta_result.execution_diagram_path.relative_to(destination).as_posix(),
                "existing_delta_node_interfaces": True,
                "mnist_is_workload_only": True,
                "protocol_scope": "MNIST_WORKLOAD_TO_APPLIED_LOCAL_DELTA",
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
                "NO_BENCHMARK_DEFINITION_QC_OR_BENCHMARK_RESULT_QC_CREATED",
                "NO_EXECUTE_STAGE_A_OR_FEATURE_010_GO_AUTHORITY_CREATED",
            ],
            "model": {
                "applied_artifact_sha256": applied_model.content_id,
                "arithmetic": "UINT8_LOCAL_INT64_SUM_DELTA_INT16_APPLY_FLOAT64_EVALUATION",
                "model_id": model_id,
                "type": MODEL_ID,
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
            "schema_version": "2.0.0",
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
    run.add_argument("--sequential", action="store_true", help="disable worker processes")

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
            parallel=not args.sequential,
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
