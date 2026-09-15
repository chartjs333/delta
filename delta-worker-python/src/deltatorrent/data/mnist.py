"""MNIST dataset provider: Content-pinned sourcing, caching, and ticket partitioning."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import struct
import tempfile
import urllib.error
import urllib.request
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import numpy as np
from numpy.typing import NDArray

from deltatorrent.data.base import (
    DataPartition,
    DatasetDescriptor,
    DatasetProviderError,
)

UInt8Array = NDArray[np.uint8]

DIGIT_COUNT: Final[int] = 10
PIXELS_PER_IMAGE: Final[int] = 28 * 28
DEMO_SEED: Final[int] = 20260914
PARTITION_RULE_ID: Final[str] = "label-skew-disjoint-v1"

NODE_LABELS: Final[tuple[tuple[int, ...], ...]] = (
    (0, 1, 2),
    (3, 4, 5),
    (6, 7),
    (8, 9),
)

PARTITION_NODE_MAP: Final[dict[str, int]] = {
    "demo-mnist-worker-01": 1,
    "demo-mnist-worker-02": 2,
    "demo-mnist-worker-03": 3,
    "demo-mnist-worker-04": 4,
    "worker-01": 1,
    "worker-02": 2,
    "worker-03": 3,
    "worker-04": 4,
    "ticket-000": 1,
    "ticket-001": 2,
    "ticket-002": 3,
    "ticket-003": 4,
}


@dataclass(frozen=True, slots=True)
class MnistFile:
    filename: str
    sha256: str
    size_bytes: int
    url: str


MNIST_FILES: Final[tuple[MnistFile, ...]] = (
    MnistFile(
        filename="train-images-idx3-ubyte.gz",
        sha256="440fcabf73cc546fa21475e81ea370265605f56be210a4024d2ca8f203523609",
        size_bytes=9_912_422,
        url="https://storage.googleapis.com/cvdf-datasets/mnist/train-images-idx3-ubyte.gz",
    ),
    MnistFile(
        filename="train-labels-idx1-ubyte.gz",
        sha256="3552534a0a558bbed6aed32b30c495cca23d567ec52cac8be1a0730e8010255c",
        size_bytes=28_881,
        url="https://storage.googleapis.com/cvdf-datasets/mnist/train-labels-idx1-ubyte.gz",
    ),
    MnistFile(
        filename="t10k-images-idx3-ubyte.gz",
        sha256="8d422c7b0a1c1c79245a5bcf07fe86e33eeafee792b84584aec276f5a2dbc4e6",
        size_bytes=1_648_877,
        url="https://storage.googleapis.com/cvdf-datasets/mnist/t10k-images-idx3-ubyte.gz",
    ),
    MnistFile(
        filename="t10k-labels-idx1-ubyte.gz",
        sha256="f7ae60f92e00ec6debd23a6088c31dbd2371eca3ffa0defaefb259924204aec6",
        size_bytes=4_542,
        url="https://storage.googleapis.com/cvdf-datasets/mnist/t10k-labels-idx1-ubyte.gz",
    ),
)

MNIST_DESCRIPTOR: Final[DatasetDescriptor] = DatasetDescriptor(
    dataset_id="mnist-v1",
    display_name="MNIST Handwritten Digits",
    sample_kind="image/grayscale-28x28",
    target_kind="class-id/0-9",
    deterministic=True,
    supports_offline_cache=True,
    description="Standard 28x28 grayscale handwritten digit classification dataset.",
    version="1.0.0",
)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def _source_manifest(sources: Sequence[MnistFile]) -> dict[str, object]:
    entries = [
        {
            "filename": source.filename,
            "sha256": f"sha256:{source.sha256}",
            "size_bytes": source.size_bytes,
            "url": source.url,
        }
        for source in sources
    ]
    manifest: dict[str, object] = {
        "attribution": "LeCun, Cortes and Burges - MNIST handwritten digit database",
        "authoritative": False,
        "environment": "LOCAL_DEMO_ONLY",
        "files": entries,
        "schema_version": "1.0.0",
        "source_page": "https://yann.lecun.org/exdb/mnist/index.html",
        "type_name": "DELTAREDUCE_LOCAL_DEMO_MNIST_SOURCE",
    }
    manifest["source_id"] = _content_id(manifest)
    return manifest


def _array_source_id(
    train_images: UInt8Array,
    train_labels: UInt8Array,
    test_images: UInt8Array,
    test_labels: UInt8Array,
) -> str:
    digest = hashlib.sha256()
    for array in (train_images, train_labels, test_images, test_labels):
        contiguous = np.ascontiguousarray(array)
        digest.update(str(contiguous.shape).encode("ascii"))
        digest.update(contiguous.dtype.str.encode("ascii"))
        digest.update(contiguous.tobytes(order="C"))
    return f"sha256:{digest.hexdigest()}"


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
                        raise DatasetProviderError(
                            f"MNIST_DOWNLOAD_SIZE_LIMIT_EXCEEDED:{source.filename}"
                        )
                    temporary.write(chunk)
                temporary.flush()
                os.fsync(temporary.fileno())
        if temporary_path is None:
            raise DatasetProviderError(f"MNIST_DOWNLOAD_EMPTY:{source.filename}")
        _validate_source_file(temporary_path, source)
        if destination.exists():
            _validate_source_file(destination, source)
            temporary_path.unlink()
        else:
            temporary_path.replace(destination)
        temporary_path = None
    except (OSError, urllib.error.URLError) as exc:
        raise DatasetProviderError(f"MNIST_DOWNLOAD_FAILED:{source.filename}") from exc
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _validate_source_file(path: Path, source: MnistFile) -> None:
    if path.is_symlink() or not path.is_file():
        raise DatasetProviderError(f"MNIST_SOURCE_NOT_REGULAR:{source.filename}")
    if path.stat().st_size != source.size_bytes:
        raise DatasetProviderError(f"MNIST_SOURCE_SIZE_MISMATCH:{source.filename}")
    if _file_sha256(path) != source.sha256:
        raise DatasetProviderError(f"MNIST_SOURCE_SHA256_MISMATCH:{source.filename}")


def _read_gzip(path: Path, expected_size: int) -> bytes:
    try:
        payload = gzip.decompress(path.read_bytes())
    except (OSError, EOFError) as exc:
        raise DatasetProviderError(f"MNIST_GZIP_INVALID:{path.name}") from exc
    if len(payload) != expected_size:
        raise DatasetProviderError(f"MNIST_IDX_SIZE_MISMATCH:{path.name}")
    return payload


def _read_images(path: Path, *, expected_count: int) -> UInt8Array:
    expected_size = 16 + expected_count * PIXELS_PER_IMAGE
    payload = _read_gzip(path, expected_size)
    magic, count, rows, columns = struct.unpack(">IIII", payload[:16])
    if (magic, count, rows, columns) != (2051, expected_count, 28, 28):
        raise DatasetProviderError(f"MNIST_IMAGE_HEADER_INVALID:{path.name}")
    return np.frombuffer(payload, dtype=np.uint8, offset=16).reshape(count, rows, columns).copy()


def _read_labels(path: Path, *, expected_count: int) -> UInt8Array:
    expected_size = 8 + expected_count
    payload = _read_gzip(path, expected_size)
    magic, count = struct.unpack(">II", payload[:8])
    if (magic, count) != (2049, expected_count):
        raise DatasetProviderError(f"MNIST_LABEL_HEADER_INVALID:{path.name}")
    labels = np.frombuffer(payload, dtype=np.uint8, offset=8).copy()
    if labels.size != expected_count or np.any(labels > 9):
        raise DatasetProviderError(f"MNIST_LABEL_VALUE_INVALID:{path.name}")
    return labels


class MnistDatasetProvider:
    """DatasetProvider implementation for the standard MNIST handwritten digits dataset."""

    def __init__(
        self,
        *,
        source_files: Sequence[MnistFile] = MNIST_FILES,
        train_count: int = 60_000,
        test_count: int = 10_000,
        train_images: UInt8Array | None = None,
        train_labels: UInt8Array | None = None,
        test_images: UInt8Array | None = None,
        test_labels: UInt8Array | None = None,
        seed: int = DEMO_SEED,
    ) -> None:
        self._source_files = tuple(source_files)
        if len(self._source_files) != 4:
            raise DatasetProviderError("MNIST_SOURCE_FILE_SET_INVALID")
        self._train_count = train_count
        self._test_count = test_count
        self._train_images = train_images
        self._train_labels = train_labels
        self._test_images = test_images
        self._test_labels = test_labels
        self._seed = seed
        provided = (
            train_images is not None,
            train_labels is not None,
            test_images is not None,
            test_labels is not None,
        )
        if any(provided) and not all(provided):
            raise DatasetProviderError("MNIST_IN_MEMORY_DATASET_INCOMPLETE")
        self._materialized = all(provided)
        self._source_id: str | None = None
        if self._materialized:
            assert (
                train_images is not None
                and train_labels is not None
                and test_images is not None
                and test_labels is not None
            )
            self._validate_arrays(train_images, train_labels, test_images, test_labels)
            self._source_id = _array_source_id(train_images, train_labels, test_images, test_labels)

    @property
    def dataset_id(self) -> str:
        return "mnist-v1"

    def descriptor(self) -> DatasetDescriptor:
        return MNIST_DESCRIPTOR

    def materialize(self, cache_dir: Path, *, allow_download: bool = True) -> Mapping[str, object]:
        """Validate local cache or download raw sources fail-closed."""
        if self._materialized:
            return {
                "authoritative": False,
                "schema_version": "1.0.0",
                "source_id": self._source_id,
                "type_name": "DELTAREDUCE_LOCAL_DEMO_MNIST_IN_MEMORY_SOURCE",
            }
        cache = cache_dir.resolve(strict=False)
        cache.mkdir(parents=True, exist_ok=True)
        if cache.is_symlink() or not cache.is_dir():
            raise DatasetProviderError("MNIST_CACHE_NOT_REGULAR_DIRECTORY")

        for source in self._source_files:
            destination = cache / source.filename
            if not destination.exists():
                if not allow_download:
                    raise DatasetProviderError(f"MNIST_SOURCE_MISSING_OFFLINE:{source.filename}")
                _download_source(source, destination)
            _validate_source_file(destination, source)

        self._train_images = _read_images(
            cache / self._source_files[0].filename,
            expected_count=self._train_count,
        )
        self._train_labels = _read_labels(
            cache / self._source_files[1].filename,
            expected_count=self._train_count,
        )
        self._test_images = _read_images(
            cache / self._source_files[2].filename,
            expected_count=self._test_count,
        )
        self._test_labels = _read_labels(
            cache / self._source_files[3].filename,
            expected_count=self._test_count,
        )
        self._validate_arrays(
            self._train_images,
            self._train_labels,
            self._test_images,
            self._test_labels,
        )
        manifest = _source_manifest(self._source_files)
        self._source_id = str(manifest["source_id"])
        (cache / "mnist-source-manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        self._materialized = True
        return manifest

    def _validate_arrays(
        self,
        train_images: UInt8Array,
        train_labels: UInt8Array,
        test_images: UInt8Array,
        test_labels: UInt8Array,
    ) -> None:
        if train_images.ndim != 3 or train_images.shape[1:] != (28, 28):
            raise DatasetProviderError("MNIST_TRAIN_IMAGE_SHAPE_INVALID")
        if test_images.ndim != 3 or test_images.shape[1:] != (28, 28):
            raise DatasetProviderError("MNIST_TEST_IMAGE_SHAPE_INVALID")
        if train_labels.shape != (train_images.shape[0],):
            raise DatasetProviderError("MNIST_TRAIN_LABEL_SHAPE_INVALID")
        if test_labels.shape != (test_images.shape[0],):
            raise DatasetProviderError("MNIST_TEST_LABEL_SHAPE_INVALID")
        if train_images.dtype != np.uint8 or test_images.dtype != np.uint8:
            raise DatasetProviderError("MNIST_IMAGE_DTYPE_INVALID")
        if train_labels.dtype != np.uint8 or test_labels.dtype != np.uint8:
            raise DatasetProviderError("MNIST_LABEL_DTYPE_INVALID")
        if bool(np.any(train_labels > 9)) or bool(np.any(test_labels > 9)):
            raise DatasetProviderError("MNIST_LABEL_VALUE_INVALID")

    def _require_materialized(self) -> None:
        if (
            not self._materialized
            or self._train_images is None
            or self._train_labels is None
            or self._test_images is None
            or self._test_labels is None
        ):
            raise DatasetProviderError("DATASET_NOT_MATERIALIZED: call materialize() first")

    def training_partition(self, partition_id: str) -> DataPartition:
        """Return the label-skew training shard assigned to the specified ticket or worker."""
        self._require_materialized()
        train_images = self._train_images
        train_labels = self._train_labels
        assert train_images is not None and train_labels is not None

        node_index = PARTITION_NODE_MAP.get(partition_id)
        if node_index is None or not (1 <= node_index <= 4):
            raise DatasetProviderError(f"UNKNOWN_PARTITION_ID: {partition_id}")

        digit_group = NODE_LABELS[node_index - 1]
        indices = np.flatnonzero(np.isin(train_labels, np.asarray(digit_group, dtype=np.uint8)))
        rng = np.random.Generator(np.random.PCG64(self._seed + node_index))
        indices = rng.permutation(indices)

        node_images = np.ascontiguousarray(train_images[indices], dtype=np.uint8)
        node_labels = np.ascontiguousarray(train_labels[indices], dtype=np.uint8)
        counts = np.bincount(node_labels, minlength=10).astype(np.int64)

        metadata: dict[str, object] = {
            "allowed_digits": list(digit_group),
            "label_counts": [int(value) for value in counts],
            "node_index": node_index,
            "partition_id": partition_id,
            "partition_rule_id": PARTITION_RULE_ID,
            "sample_count": int(node_labels.size),
            "seed": self._seed + node_index,
            "source_id": self._source_id,
        }
        return DataPartition(
            partition_id=partition_id,
            samples=node_images,
            targets=node_labels,
            metadata=metadata,
        )

    def evaluation_data(self) -> tuple[np.ndarray, np.ndarray]:
        """Return test images and test labels."""
        self._require_materialized()
        if self._test_images is None or self._test_labels is None:
            raise DatasetProviderError("TEST_DATA_NOT_AVAILABLE")
        return self._test_images, self._test_labels
