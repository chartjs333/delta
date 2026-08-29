"""Validate the one-run physical QLoRA claim without rerunning the GPU workload."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
PHYSICAL: Final = ROOT / "specs/009-qlora-8gb-mode/evidence/physical-qualification.json"
NATIVE: Final = ROOT / "specs/009-qlora-8gb-mode/evidence/native-runtime.json"
OUTPUT: Final = ROOT / "specs/009-qlora-8gb-mode/evidence/physical-gate.json"
PROFILE: Final = ROOT / "configs/qlora/8gb-reference.json"
PROFILE_SHA256: Final = "c7319d0c14ebc9af4667b91d92faba207b6ab0ae0cd6aa8a9e5d127d5f7ccb0d"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise RuntimeError(reason)


def run(*args: str) -> str:
    return subprocess.run(
        args, cwd=ROOT, check=True, capture_output=True, encoding="utf-8", errors="replace"
    ).stdout.strip()


def source_bytes(commit: str, path: str) -> bytes:
    return subprocess.run(
        ("git", "show", f"{commit}:{path}"), cwd=ROOT, check=True, capture_output=True
    ).stdout


def content_id(value: object) -> bool:
    return isinstance(value, str) and len(value) == 71 and value.startswith("sha256:")


def load_canonical(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_bytes()
    value = json.loads(raw)
    require(isinstance(value, dict), f"{path.name}:NOT_OBJECT")
    canonical = (
        json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
        + b"\n"
    )
    require(
        raw in {canonical, canonical.replace(b"\n", b"\r\n")},
        f"{path.name}:NOT_CANONICAL_JSON",
    )
    return value, hashlib.sha256(canonical).hexdigest()


def verify_native_ancestry(native: dict[str, Any], physical_commit: str) -> str:
    require(native.get("status") == "PASS", "NATIVE_RUNTIME_NOT_PASS")
    require(native.get("formal_semantics_id") == FORMAL_ID, "NATIVE_FORMAL_ID_MISMATCH")
    tests = native.get("tests")
    require(
        isinstance(tests, list)
        and [item.get("preset") for item in tests] == ["cpp20", "cpp23"]
        and all(item.get("summary") == "3/3 passed" for item in tests),
        "NATIVE_STRICT_MATRIX_INCOMPLETE",
    )
    source = native.get("source")
    require(isinstance(source, dict), "NATIVE_SOURCE_MISSING")
    artifacts = source.get("artifacts")
    require(isinstance(artifacts, list) and artifacts, "NATIVE_ARTIFACTS_MISSING")
    for artifact in artifacts:
        path = str(artifact["path"])
        actual = hashlib.sha256(source_bytes(physical_commit, path)).hexdigest()
        require(actual == artifact.get("sha256"), f"NATIVE_ARTIFACT_DRIFT:{path}")
    return str(source["commit"])


def build() -> dict[str, object]:
    physical, physical_sha256 = load_canonical(PHYSICAL)
    native, native_sha256 = load_canonical(NATIVE)
    profile = json.loads(PROFILE.read_text(encoding="utf-8"))
    require(hashlib.sha256(PROFILE.read_bytes()).hexdigest() == PROFILE_SHA256, "PROFILE_DRIFT")

    source = physical.get("source")
    require(isinstance(source, dict), "PHYSICAL_SOURCE_MISSING")
    commit = str(source.get("commit"))
    tree = str(source.get("tree"))
    require(source.get("worktree_clean") is True, "PHYSICAL_SOURCE_WAS_DIRTY")
    require(run("git", "show", "-s", "--format=%T", commit) == tree, "SOURCE_TREE_MISMATCH")
    require(
        not run(
            "git",
            "diff",
            "--name-only",
            "origin/main..." + commit,
            "--",
            "formal",
            "specs/000-formal-tla-spec",
        ),
        "FORMAL_SOURCE_DIFF",
    )
    require(
        hashlib.sha256(source_bytes(commit, "configs/qlora/8gb-reference.json")).hexdigest()
        == PROFILE_SHA256,
        "SOURCE_PROFILE_MISMATCH",
    )
    require(physical.get("status") == "PASS", "PHYSICAL_STATUS_NOT_PASS")
    require(physical.get("formal_semantics_id") == FORMAL_ID, "PHYSICAL_FORMAL_ID_MISMATCH")

    expected_gpu = profile["runner"]["gpu"]
    device = physical["device"]
    for field in ("name", "uuid", "driver_version", "compute_capability", "total_memory_bytes"):
        require(device[field] == expected_gpu[field], f"PHYSICAL_GPU_MISMATCH:{field}")
    require(
        device["free_memory_at_start_bytes"]
        >= profile["memory"]["required_minimum_available_at_start_bytes"],
        "PHYSICAL_START_MEMORY_INSUFFICIENT",
    )
    require(physical.get("software") == profile["software"], "PHYSICAL_SOFTWARE_DRIFT")
    require(
        physical.get("execution")
        == {"cublas_workspace_config": ":4096:8", "deterministic_algorithms": True},
        "PHYSICAL_DETERMINISM_MISSING",
    )

    ticket = physical["ticket"]
    frozen_ticket = profile["ticket"]
    require(ticket["fixed_B"] == frozen_ticket["B"], "PHYSICAL_B_MISMATCH")
    require(ticket["fixed_H"] == frozen_ticket["H"], "PHYSICAL_H_MISMATCH")
    require(ticket["processed_tokens"] == frozen_ticket["B"], "PHYSICAL_TICKET_INCOMPLETE")
    require(ticket["actual_optimizer_steps"] == frozen_ticket["H"], "PHYSICAL_STEPS_INCOMPLETE")
    losses = ticket.get("losses")
    expected_losses = frozen_ticket["H"] * frozen_ticket["gradient_accumulation_steps"]
    require(isinstance(losses, list) and len(losses) == expected_losses, "PHYSICAL_LOSS_COUNT")
    require(all(math.isfinite(float(loss)) for loss in losses), "PHYSICAL_LOSS_NONFINITE")

    base = physical["base"]
    require(base["hash_before"] == base["hash_after"], "PHYSICAL_BASE_MUTATED")
    require(content_id(base["hash_before"]), "PHYSICAL_BASE_HASH_INVALID")
    adapter = physical["adapter"]
    require(adapter["parameter_count"] > 0, "PHYSICAL_ADAPTER_EMPTY")
    require(adapter["bytes"] == adapter["parameter_count"] * 2, "PHYSICAL_ADAPTER_DTYPE")
    require(adapter["shard_count"] == 256, "PHYSICAL_SHARD_COUNT")
    require(content_id(adapter["commitment_root"]), "PHYSICAL_COMMITMENT_ROOT_INVALID")
    require(content_id(adapter["parameter_schema_id"]), "PHYSICAL_SCHEMA_ID_INVALID")
    total_parameters = base["parameter_count"] + adapter["parameter_count"]
    require(
        adapter["trainable_ratio_ppm"]
        == adapter["parameter_count"] * 1_000_000 // total_parameters,
        "PHYSICAL_ADAPTER_RATIO_MISMATCH",
    )

    optimizer = physical["optimizer"]
    require(
        optimizer
        == {
            "adapter_only": True,
            "learning_rate": "0.0001",
            "state_bytes": adapter["parameter_count"] * 8,
            "state_dtype": "FLOAT32",
            "type": "ADAMW",
        },
        "PHYSICAL_OPTIMIZER_MISMATCH",
    )
    memory = physical["memory"]
    require(
        0
        < memory["peak_allocated_bytes"]
        <= memory["peak_reserved_bytes"]
        <= memory["hard_max_reserved_bytes"]
        == profile["memory"]["hard_max_reserved_bytes"],
        "PHYSICAL_MEMORY_BUDGET_FAILED",
    )
    require(
        memory["headroom_bytes"]
        == device["total_memory_bytes"] - memory["peak_reserved_bytes"]
        >= memory["required_headroom_bytes"]
        == profile["memory"]["required_headroom_bytes"],
        "PHYSICAL_HEADROOM_FAILED",
    )
    require(memory["host_offload_peak_bytes"] == 0, "PHYSICAL_HOST_OFFLOAD")
    require(
        physical.get("claim")
        == {
            "eligible": True,
            "generalized": False,
            "scope": "ONE_EXACT_PHYSICAL_RUNNER_AND_PROFILE",
        },
        "PHYSICAL_CLAIM_OVERSTATED",
    )
    require(content_id(physical["native"]["context_id"]), "PHYSICAL_NATIVE_CONTEXT_INVALID")
    native_source_commit = verify_native_ancestry(native, commit)

    return {
        "checks": [
            "EXACT_FROZEN_PROFILE_AND_SOURCE",
            "DESIGNATED_PHYSICAL_8GIB_GPU",
            "PINNED_PYTHON_CUDA_SOFTWARE",
            "DETERMINISTIC_CUBLAS_EXECUTION",
            "FULL_FIXED_B_H_TICKET",
            "IMMUTABLE_QUANTIZED_BASE",
            "ADAPTER_ONLY_FP32_OPTIMIZER_STATE",
            "CANONICAL_ADAPTER_Q_COMMITMENT",
            "MEASURED_VRAM_BUDGET_AND_HEADROOM",
            "ZERO_HOST_OFFLOAD",
            "NATIVE_CERTIFICATE_APPLY_AND_ABI_ANCESTRY",
            "NON_GENERALIZED_PHYSICAL_CLAIM",
        ],
        "classification": "ONE_EXACT_PHYSICAL_RUNNER_AND_PROFILE",
        "formal_semantics_id": FORMAL_ID,
        "inputs": {
            "native_runtime_canonical_sha256": native_sha256,
            "physical_qualification_canonical_sha256": physical_sha256,
            "profile_sha256": PROFILE_SHA256,
        },
        "measurements": {
            "adapter_parameter_count": adapter["parameter_count"],
            "headroom_bytes": memory["headroom_bytes"],
            "peak_reserved_bytes": memory["peak_reserved_bytes"],
            "processed_tokens": ticket["processed_tokens"],
        },
        "native_source_commit": native_source_commit,
        "schema_version": "1.0.0",
        "source": {"commit": commit, "tree": tree},
        "status": "PASS",
        "task_ids": ["T039", "T040", "T041", "HR009-011"],
    }


def main() -> int:
    report = build()
    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
