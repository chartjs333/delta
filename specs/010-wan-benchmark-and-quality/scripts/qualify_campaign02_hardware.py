"""Run non-primary exact-source GPU/QLoRA qualification for Campaign 02."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "delta-worker-python/src"))

from deltatorrent.benchmark.gpu_environment import (  # noqa: E402
    verify_gpu_environment_outputs,
)
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id  # noqa: E402
from deltatorrent.qlora.qualification import run_physical_qualification  # noqa: E402

FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
PROFILE: Final = ROOT / "configs/qlora/8gb-reference.json"
REQUIRED: Final = {
    "accelerate": "1.14.0",
    "bitsandbytes": "0.50.2",
    "huggingface_hub": "1.29.0",
    "peft": "0.20.0",
    "torch": "2.6.0+cu124",
    "transformers": "5.16.1",
}


class Campaign02HardwareError(RuntimeError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise Campaign02HardwareError(code)


def git(*arguments: str) -> str:
    return subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        check=True,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.strip()


def file_id(path: Path) -> str:
    return sha256_content_id(path.read_bytes())


def distribution_versions() -> dict[str, str]:
    actual = {
        name: importlib.metadata.version(name.replace("_", "-"))
        for name in ("accelerate", "bitsandbytes", "huggingface_hub", "peft", "transformers")
    }
    import torch

    actual["torch"] = str(torch.__version__)
    require(platform.python_version() == "3.12.1", "CAMPAIGN02_PYTHON_VERSION_MISMATCH")
    require(actual == REQUIRED, "CAMPAIGN02_GPU_PACKAGE_VERSION_MISMATCH")
    require(str(torch.version.cuda) == "12.4", "CAMPAIGN02_CUDA_RUNTIME_MISMATCH")
    return actual


def bitsandbytes_binary() -> Path:
    import bitsandbytes.cextension as extension

    library = getattr(getattr(extension, "lib", None), "_lib", None)
    name = getattr(library, "_name", None)
    if isinstance(name, str) and Path(name).is_file():
        return Path(name).resolve()
    package = Path(extension.__file__).resolve().parent
    matches = sorted(
        path
        for pattern in ("*cuda124*.dll", "*cuda124*.so", "*cuda124*.dylib")
        for path in package.rglob(pattern)
    )
    require(len(matches) == 1, "CAMPAIGN02_BITSANDBYTES_BINARY_AMBIGUOUS")
    return matches[0]


def torch_build() -> dict[str, object]:
    import torch

    binary = Path(torch._C.__file__).resolve()
    document: dict[str, object] = {
        "binary_id": file_id(binary),
        "cuda_runtime": str(torch.version.cuda),
        "debug": bool(torch.version.debug),
        "git_version": str(torch.version.git_version),
        "version": str(torch.__version__),
    }
    return {**document, "torch_build_id": sha256_content_id(canonical_json_bytes(document))}


def gpu_binary_smoke() -> dict[str, object]:
    import bitsandbytes.functional as bnb_functional
    import torch

    torch.manual_seed(2_026_083_101)
    torch.cuda.manual_seed_all(2_026_083_101)
    torch.use_deterministic_algorithms(True)
    values = torch.arange(256, dtype=torch.float32, device="cuda").reshape(16, 16) / 256
    quantized, state = bnb_functional.quantize_4bit(
        values, blocksize=64, compress_statistics=True, quant_type="nf4"
    )
    restored = bnb_functional.dequantize_4bit(quantized, state)
    torch.cuda.synchronize()
    require(bool(torch.isfinite(restored).all()), "CAMPAIGN02_BITSANDBYTES_SMOKE_NONFINITE")
    payload = restored.cpu().contiguous().numpy().tobytes()
    return {
        "input_elements": values.numel(),
        "output_sha256": sha256_content_id(payload),
        "quantization_type": "NF4",
        "status": "PASS",
    }


def build(source_commit: str, native_library: Path) -> dict[str, object]:
    head = git("rev-parse", "HEAD")
    require(source_commit == head, "CAMPAIGN02_HARDWARE_SOURCE_NOT_HEAD")
    require(not git("status", "--porcelain=v1"), "CAMPAIGN02_HARDWARE_SOURCE_DIRTY")
    source_tree = git("show", "-s", "--format=%T", source_commit)
    require(re.fullmatch(r"[0-9a-f]{40}", source_tree) is not None, "SOURCE_TREE_INVALID")
    lock = verify_gpu_environment_outputs(ROOT)
    versions = distribution_versions()
    bnb_binary = bitsandbytes_binary()
    physical = run_physical_qualification(PROFILE, native_library.resolve())
    require(physical.get("status") == "PASS", "CAMPAIGN02_PHYSICAL_QUALIFICATION_FAILED")
    require(
        physical.get("source")
        == {
            "commit": source_commit,
            "tree": source_tree,
            "worktree_clean": True,
        },
        "CAMPAIGN02_PHYSICAL_SOURCE_MISMATCH",
    )
    device = physical["device"]
    require(isinstance(device, dict), "CAMPAIGN02_DEVICE_EVIDENCE_INVALID")
    hardware_document = {
        "compute_capability": device["compute_capability"],
        "driver_version": device["driver_version"],
        "gpu_name": device["name"],
        "gpu_total_memory_bytes": device["total_memory_bytes"],
        "gpu_uuid": device["uuid"],
    }
    hardware_id = sha256_content_id(canonical_json_bytes(hardware_document))
    torch_identity = torch_build()
    bnb_id = file_id(bnb_binary)
    python_document = {
        "executable_id": file_id(Path(sys.executable)),
        "implementation": platform.python_implementation(),
        "version": platform.python_version(),
    }
    python_build_id = sha256_content_id(canonical_json_bytes(python_document))
    environment_document = {
        "bitsandbytes_binary_id": bnb_id,
        "cuda_runtime_id": lock.document["cuda_runtime_id"],
        "driver_version": device["driver_version"],
        "formal_semantics_id": FORMAL_ID,
        "gpu_environment_lock_id": lock.content_id,
        "oci_image_digest": lock.document["oci_image_digest"],
        "python_build_id": python_build_id,
        "runner_hardware_id": hardware_id,
        "sbom_id": lock.sbom_id,
        "torch_build_id": torch_identity["torch_build_id"],
    }
    environment_id = sha256_content_id(canonical_json_bytes(environment_document))
    physical_id = sha256_content_id(canonical_json_bytes(physical))
    return {
        "bitsandbytes": {
            "binary_id": bnb_id,
            "binary_name": bnb_binary.name,
            "version": versions["bitsandbytes"],
        },
        "environment": {**environment_document, "environment_id": environment_id},
        "fixture_class": "NON_PRIMARY_HARDWARE_QUALIFICATION",
        "formal_semantics_id": FORMAL_ID,
        "gpu_smoke": gpu_binary_smoke(),
        "primary_scientific_execution_count": 0,
        "python": {**python_document, "python_build_id": python_build_id},
        "qlora_physical_qualification_id": physical_id,
        "qlora_ticket": physical["ticket"],
        "schema_version": "1.0.0",
        "scientific_observations_created": False,
        "source": {"commit": source_commit, "tree": source_tree},
        "status": "PASS",
        "torch": torch_identity,
        "type_name": "CAMPAIGN02_HARDWARE_QUALIFICATION",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--native-library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    report = build(arguments.source_commit, arguments.native_library)
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_bytes(canonical_json_bytes(report) + b"\n")
    print(
        json.dumps(
            {
                "environment_id": report["environment"]["environment_id"],
                "source_commit": arguments.source_commit,
                "status": "PASS",
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
