"""Immutable CPU/GPU lock separation and Campaign 02 environment identity."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

_PACKAGE = re.compile(r"^([A-Za-z0-9_.-]+)==([^ \\\r\n]+)", re.MULTILINE)
_CONTENT_ID = re.compile(r"^sha256:[0-9a-f]{64}$")
_REQUIRED: Final = {
    "accelerate": "1.14.0",
    "bitsandbytes": "0.50.2",
    "huggingface-hub": "1.29.0",
    "peft": "0.20.0",
    "torch": "2.6.0+cu124",
    "transformers": "5.16.1",
}


class GpuEnvironmentError(ValueError):
    """Stable immutable-environment rejection."""


def _fail(code: str) -> GpuEnvironmentError:
    return GpuEnvironmentError(code)


def _file_id(path: Path) -> str:
    try:
        return sha256_content_id(path.read_bytes())
    except OSError as exc:
        raise _fail("GPU_ENVIRONMENT_FILE_UNREADABLE") from exc


def _canonical_file(path: Path, code: str) -> tuple[dict[str, Any], bytes]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise _fail(code) from exc
    if not isinstance(value, dict) or canonical_json_bytes(value) + b"\n" != raw:
        raise _fail(code)
    return value, raw


def verify_hashed_lock(path: Path, *, python_platform: str) -> dict[str, str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise _fail("GPU_DEPENDENCY_LOCK_UNREADABLE") from exc
    matches = list(_PACKAGE.finditer(text))
    if not matches:
        raise _fail("GPU_DEPENDENCY_LOCK_EMPTY")
    header = text[: matches[0].start()]
    if (
        "--python-version 3.12.1" not in header
        or f"--python-platform {python_platform}" not in header
        or "--generate-hashes" not in header
        or "--no-emit-index-url" not in header
    ):
        raise _fail("GPU_DEPENDENCY_LOCK_METADATA_INVALID")
    versions: dict[str, str] = {}
    for index, match in enumerate(matches):
        name = match.group(1).lower().replace("_", "-")
        if name in versions:
            raise _fail("GPU_DEPENDENCY_LOCK_PACKAGE_DUPLICATE")
        versions[name] = match.group(2)
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        block = text[match.start() : end]
        if "--hash=sha256:" not in block:
            raise _fail("GPU_DEPENDENCY_LOCK_HASH_MISSING")
    for name, expected in _REQUIRED.items():
        if versions.get(name) != expected:
            raise _fail(f"GPU_DEPENDENCY_VERSION_MISMATCH:{name}")
    return versions


@dataclass(frozen=True, slots=True)
class GpuEnvironmentLock:
    document: dict[str, object]
    sbom: dict[str, object]

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.document)

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            b"deltareduce.010.gpu-environment-lock.v1\0" + self.canonical_bytes
        )

    @property
    def sbom_id(self) -> str:
        return sha256_content_id(b"deltareduce.010.gpu-sbom.v1\0" + canonical_json_bytes(self.sbom))


def build_gpu_environment_lock(root: Path) -> GpuEnvironmentLock:
    config = root / "configs/benchmark/campaign-02"
    policy, _ = _canonical_file(
        config / "gpu-environment-policy-v1.json", "GPU_ENVIRONMENT_POLICY_INVALID"
    )
    if (
        policy.get("type_name") != "GPU_ENVIRONMENT_POLICY"
        or policy.get("schema_version") != "1.0.0"
        or policy.get("formal_semantics_id") != FORMAL_SEMANTICS_ID
        or policy.get("python") != "3.12.1"
        or policy.get("cuda_runtime_id") != "CUDA_12.4"
        or policy.get("required_packages")
        != {
            "accelerate": "1.14.0",
            "bitsandbytes": "0.50.2",
            "huggingface_hub": "1.29.0",
            "peft": "0.20.0",
            "torch": "2.6.0+cu124",
            "transformers": "5.16.1",
        }
    ):
        raise _fail("GPU_ENVIRONMENT_POLICY_INVALID")
    image = policy.get("oci_base_image")
    if (
        not isinstance(image, dict)
        or image.get("platform") != "linux/amd64"
        or not isinstance(image.get("digest"), str)
        or _CONTENT_ID.fullmatch(str(image["digest"])) is None
    ):
        raise _fail("GPU_ENVIRONMENT_IMAGE_INVALID")
    locks = (
        (
            "configs/benchmark/campaign-02/gpu-linux-x86_64.lock",
            "linux/amd64-manylinux_2_28",
            "x86_64-manylinux_2_28",
        ),
        (
            "configs/benchmark/campaign-02/gpu-windows-x86_64.lock",
            "windows/amd64",
            "windows",
        ),
    )
    resolved_versions: dict[str, dict[str, str]] = {}
    lock_refs: list[dict[str, object]] = []
    for relative, target, python_platform in locks:
        path = root / relative
        resolved_versions[target] = verify_hashed_lock(path, python_platform=python_platform)
        lock_refs.append({"path": relative, "sha256": _file_id(path), "target": target})
    if any(
        versions.get(name) != expected
        for versions in resolved_versions.values()
        for name, expected in _REQUIRED.items()
    ):
        raise _fail("GPU_DEPENDENCY_PLATFORM_DRIFT")
    material_paths = (
        "configs/benchmark/campaign-02/gpu-requirements.in",
        "configs/benchmark/campaign-02/gpu-environment-policy-v1.json",
        "configs/benchmark/campaign-02/gpu-linux-x86_64.lock",
        "configs/benchmark/campaign-02/gpu-windows-x86_64.lock",
        "uv.lock",
    )
    sbom: dict[str, object] = {
        "files": [
            {"path": relative, "sha256": _file_id(root / relative)} for relative in material_paths
        ],
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "packages": [
            {
                "components": [
                    {"name": name, "version": version}
                    for name, version in sorted(resolved_versions[target].items())
                ],
                "target": target,
            }
            for target in sorted(resolved_versions)
        ],
        "portable_cpu_lock_scientific_use": False,
        "schema_version": "1.0.0",
        "type_name": "CAMPAIGN02_GPU_SBOM",
    }
    sbom_id = sha256_content_id(b"deltareduce.010.gpu-sbom.v1\0" + canonical_json_bytes(sbom))
    document: dict[str, object] = {
        "cpu_portable_lock_id": _file_id(root / "uv.lock"),
        "cuda_runtime_id": "CUDA_12.4",
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "image_scope": "PINNED_CUDA_BASE_PLUS_HASH_LOCKED_PYTHON_ENVIRONMENT",
        "immutable_resolution": True,
        "oci_image_digest": str(image["digest"]),
        "platform_locks": lock_refs,
        "policy_id": _file_id(config / "gpu-environment-policy-v1.json"),
        "python": "3.12.1",
        "required_packages": dict(policy["required_packages"]),
        "requirements_input_id": _file_id(config / "gpu-requirements.in"),
        "sbom_id": sbom_id,
        "schema_version": "1.0.0",
        "scientific_use": True,
        "type_name": "GPU_ENVIRONMENT_LOCK",
    }
    return GpuEnvironmentLock(document, sbom)


def write_gpu_environment_lock(root: Path) -> GpuEnvironmentLock:
    value = build_gpu_environment_lock(root)
    config = root / "configs/benchmark/campaign-02"
    (config / "gpu-sbom-v1.json").write_bytes(canonical_json_bytes(value.sbom) + b"\n")
    (config / "gpu-environment-lock-v1.json").write_bytes(value.canonical_bytes + b"\n")
    return value


def verify_gpu_environment_outputs(root: Path) -> GpuEnvironmentLock:
    expected = build_gpu_environment_lock(root)
    config = root / "configs/benchmark/campaign-02"
    if (config / "gpu-sbom-v1.json").read_bytes() != canonical_json_bytes(expected.sbom) + b"\n":
        raise _fail("GPU_SBOM_OUTPUT_DRIFT")
    if (config / "gpu-environment-lock-v1.json").read_bytes() != expected.canonical_bytes + b"\n":
        raise _fail("GPU_ENVIRONMENT_LOCK_OUTPUT_DRIFT")
    return expected
