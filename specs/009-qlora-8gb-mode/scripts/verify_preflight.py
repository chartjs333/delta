"""Verify the exact feature-008, Formal and physical-profile boundary for feature 009."""

from __future__ import annotations

import argparse
import copy
import csv
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "009-qlora-8gb-mode"
OUTPUT: Final = FEATURE / "evidence" / "preflight.json"
PROFILE_PATH: Final = "configs/qlora/8gb-reference.json"

FEATURE008_MERGE: Final = "62124e58062d876dc4c2fd903b57cfc7d89872d7"
FEATURE008_PARENTS: Final = (
    "2054f31ef0f6750645b924ef337a35d1737c619d",
    "d86473a3f864b4e61d2312584afa080c8fd4fbab",
)
FEATURE008_SOURCE: Final = "4ef4daead4e3fcdf19d6947cf8120c4974af09fe"
FEATURE008_OVERLAY: Final = FEATURE008_PARENTS[1]
FEATURE008_REPORT_SHA256: Final = "fb7b9f572923e3d8a8e24195f630474ed836ff0a7ef6454b7d31d3f930a4cc9c"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
MODEL_REVISION: Final = "2fe192450127e6a83f7441aef6e3ca586c338b77"
GPU_UUID: Final = "GPU-4f9cec9a-c8e8-3f95-4706-c70e0b11df5d"
GPU_NAME: Final = "NVIDIA GeForce RTX 3070 Laptop GPU"
GPU_TOTAL_BYTES: Final = 8 * 1024**3

SOURCE_ARTIFACTS: Final = (
    ".specify/memory/constitution.md",
    "configs/qlora/8gb-reference.json",
    "docs/adr/0000-formal-verification-gate.md",
    "docs/adr/0001-deltareduce-v1.md",
    "specs/ROADMAP.md",
    "specs/000-formal-tla-spec/failure-semantics.md",
    "specs/000-formal-tla-spec/proof-obligations.md",
    "specs/000-formal-tla-spec/refinement-contract.md",
    "specs/008-certificates-and-consensus/evidence/final-compatibility.json",
    "specs/009-qlora-8gb-mode/checklists/hybrid-runtime.md",
    "specs/009-qlora-8gb-mode/checklists/requirements.md",
    "specs/009-qlora-8gb-mode/formal-refinement.md",
    "specs/009-qlora-8gb-mode/plan.md",
    "specs/009-qlora-8gb-mode/runtime-profile.md",
    "specs/009-qlora-8gb-mode/runtime-tasks.md",
    "specs/009-qlora-8gb-mode/scripts/verify_preflight.py",
    "specs/009-qlora-8gb-mode/spec.md",
    "specs/009-qlora-8gb-mode/task-map.md",
    "specs/009-qlora-8gb-mode/tasks.md",
    "specs/009-qlora-8gb-mode/tests/test_verify_preflight.py",
)
PRODUCTION_PREFIXES: Final = (
    "delta-core-cpp/",
    "delta-runtime-cpp/",
    "delta-ffi/",
    "delta-node-java/",
    "delta-worker-python/",
    "delta-protocol/",
)
ALLOWED_NON_FEATURE_PATHS: Final = {PROFILE_PATH, "specs/ROADMAP.md"}

sys.path.insert(0, str(ROOT / "formal" / "scripts"))
from formal_artifacts import canonical_json_bytes  # noqa: E402


class PreflightError(RuntimeError):
    """Stable fail-closed feature-009 preflight error."""


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise PreflightError(f"{code}:{detail}" if detail else code)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    require(
        process.returncode == 0,
        "GIT_COMMAND_FAILED",
        process.stderr.decode(errors="replace").strip(),
    )
    return process.stdout.replace(b"\r\n", b"\n")


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode().strip()


def tracked_bytes(path: str, revision: str) -> bytes:
    relative = Path(path)
    require(not relative.is_absolute() and ".." not in relative.parts, "UNSAFE_PATH", path)
    return git_bytes("show", f"{revision}:{path}")


def tracked_text(path: str, revision: str) -> str:
    return tracked_bytes(path, revision).decode()


def artifact(path: str, revision: str) -> dict[str, str]:
    return {"path": path, "sha256": sha256_bytes(tracked_bytes(path, revision))}


def require_ancestor(ancestor: str, descendant: str, code: str) -> None:
    process = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=ROOT,
        check=False,
        capture_output=True,
    )
    require(process.returncode == 0, code)


def verify_manifest(
    entries: object,
    revision: str,
    code: str,
    *,
    prefix: str = "",
) -> int:
    require(isinstance(entries, list) and entries, code)
    for entry in entries:
        require(isinstance(entry, dict), code)
        path = entry.get("path")
        expected = entry.get("sha256")
        require(isinstance(path, str) and isinstance(expected, str), code)
        full_path = f"{prefix}{path}"
        require(sha256_bytes(tracked_bytes(full_path, revision)) == expected, code, full_path)
    return len(entries)


def validate_feature008_document(document: dict[str, Any]) -> None:
    require(document.get("status") == "PASS", "FEATURE008_STATUS_INVALID")
    require(document.get("classification") == "REFINEMENT_ONLY", "FEATURE008_CLASS_INVALID")
    require(document.get("semantic_completeness_claimed") is False, "FEATURE008_CLAIM_INVALID")
    require(
        document.get("formal")
        == {
            "formal_semantics_id": FORMAL_ID,
            "new_action_ids": [],
            "new_failure_terminals": [],
            "source_diff": [],
            "status": "GO",
        },
        "FEATURE008_FORMAL_DRIFT",
    )
    require(
        document.get("source", {}).get("commit") == FEATURE008_SOURCE,
        "FEATURE008_SOURCE_DRIFT",
    )
    require(
        "FEATURE009_QLORA_8GB_COMPLETION" in document.get("unsupported_claims", []),
        "FEATURE008_QLORA_BOUNDARY_MISSING",
    )


def verify_feature008(source_commit: str) -> dict[str, Any]:
    parents = tuple(git_text("show", "-s", "--format=%P", FEATURE008_MERGE).split())
    require(parents == FEATURE008_PARENTS, "FEATURE008_MERGE_PARENTS_INVALID")
    require_ancestor(FEATURE008_SOURCE, FEATURE008_OVERLAY, "FEATURE008_SOURCE_CHAIN_INVALID")
    require_ancestor(FEATURE008_OVERLAY, FEATURE008_MERGE, "FEATURE008_OVERLAY_CHAIN_INVALID")
    require_ancestor(FEATURE008_MERGE, source_commit, "FEATURE008_MERGE_NOT_ANCESTOR")

    report_path = "specs/008-certificates-and-consensus/evidence/final-compatibility.json"
    raw = tracked_bytes(report_path, FEATURE008_MERGE)
    require(sha256_bytes(raw) == FEATURE008_REPORT_SHA256, "FEATURE008_REPORT_HASH_DRIFT")
    document = json.loads(raw)
    require(isinstance(document, dict), "FEATURE008_REPORT_INVALID")
    validate_feature008_document(document)
    evidence_count = verify_manifest(
        document.get("evidence_artifacts"),
        FEATURE008_MERGE,
        "FEATURE008_EVIDENCE_MANIFEST_DRIFT",
        prefix="specs/008-certificates-and-consensus/",
    )

    native_path = "specs/008-certificates-and-consensus/evidence/native-execution.json"
    native = json.loads(tracked_bytes(native_path, FEATURE008_MERGE))
    require(isinstance(native, dict), "FEATURE008_NATIVE_REPORT_INVALID")
    require(native.get("status") == "PASS", "FEATURE008_NATIVE_NOT_PASS")
    require(native.get("source", {}).get("commit") == FEATURE008_SOURCE, "FEATURE008_NATIVE_DRIFT")
    source_count = verify_manifest(
        native.get("source", {}).get("artifacts"),
        FEATURE008_SOURCE,
        "FEATURE008_SOURCE_MANIFEST_DRIFT",
    )
    for path in (
        "specs/008-certificates-and-consensus/tasks.md",
        "specs/008-certificates-and-consensus/runtime-tasks.md",
    ):
        require(
            not re.search(r"^- \[ \] ", tracked_text(path, FEATURE008_MERGE), re.MULTILINE),
            "FEATURE008_TASK_OPEN",
            path,
        )
    return {
        "evidence_artifact_count": evidence_count,
        "evidence_overlay": FEATURE008_OVERLAY,
        "merge_commit": FEATURE008_MERGE,
        "merge_parents": list(FEATURE008_PARENTS),
        "report": {"path": report_path, "sha256": FEATURE008_REPORT_SHA256},
        "source_artifact_count": source_count,
        "source_commit": FEATURE008_SOURCE,
        "status": "PASS",
    }


def load_feature008_preflight() -> Any:
    path = ROOT / "specs/008-certificates-and-consensus/scripts/verify_preflight.py"
    spec = importlib.util.spec_from_file_location("feature008_preflight_dependency", path)
    require(spec is not None and spec.loader is not None, "FORMAL_HELPER_LOAD_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_formal(source_commit: str) -> dict[str, Any]:
    result = load_feature008_preflight().verify_formal(source_commit)
    require(result.get("status") == "GO", "FORMAL_NOT_GO")
    refinement = tracked_text("formal/tla/DeltaReduceRefinement.tla", source_commit)
    required = {
        "ACT-APC-FINALIZE",
        "ACT-APPLY-FINALIZE",
        "ACT-COMMIT",
        "ACT-CURRENT-ADVANCE",
        "ACT-EC-FINALIZE",
        "ACT-ISC-FINALIZE",
        "ACT-PARAM-FINALIZE",
        "ACT-ROOT-FINALIZE",
        "ACT-SEED-GENERATE",
    }
    missing = sorted(action for action in required if f'"{action}"' not in refinement)
    require(not missing, "FORMAL_ACTION_MISSING", ",".join(missing))
    return {**result, "required_action_ids": sorted(required)}


def expected_target_modules() -> list[str]:
    suffixes = (
        "self_attn.qkv_proj",
        "self_attn.o_proj",
        "mlp.gate_up_proj",
        "mlp.down_proj",
    )
    return [f"model.layers.{layer}.{suffix}" for layer in range(32) for suffix in suffixes]


def validate_profile(document: dict[str, Any]) -> dict[str, Any]:
    require(document.get("schema_version") == "1.0.0", "PROFILE_SCHEMA_INVALID")
    claim = document.get("claim")
    require(
        claim
        == {
            "generalized": False,
            "scope": "ONE_EXACT_PHYSICAL_RUNNER_AND_PROFILE",
            "status": "PENDING_EXECUTION",
        },
        "PROFILE_CLAIM_INVALID",
    )

    runner = document.get("runner")
    require(isinstance(runner, dict), "RUNNER_INVALID")
    gpu = runner.get("gpu")
    require(isinstance(gpu, dict), "GPU_INVALID")
    require(gpu.get("uuid") == GPU_UUID, "GPU_UUID_DRIFT")
    require(gpu.get("name") == GPU_NAME, "GPU_NAME_DRIFT")
    require(gpu.get("total_memory_bytes") == GPU_TOTAL_BYTES, "GPU_MEMORY_NOT_8_GIB")
    require(gpu.get("compute_capability") == "8.6", "GPU_CAPABILITY_DRIFT")
    require(gpu.get("driver_model") == "WDDM", "GPU_DRIVER_MODEL_DRIFT")
    require(runner.get("kind") == "LOCAL_PHYSICAL_WINDOWS", "RUNNER_KIND_INVALID")
    require(runner.get("registered_github_runner") is False, "RUNNER_REGISTRY_DRIFT")

    model = document.get("model")
    require(isinstance(model, dict), "MODEL_PROFILE_INVALID")
    require(model.get("repository") == "microsoft/Phi-3.5-mini-instruct", "MODEL_DRIFT")
    require(model.get("revision") == MODEL_REVISION, "MODEL_REVISION_DRIFT")
    require(model.get("license") == "MIT", "MODEL_LICENSE_INVALID")
    require(model.get("gated") is False, "MODEL_MUST_BE_PUBLIC")
    require(model.get("access_token_required") is False, "MODEL_TOKEN_FORBIDDEN")
    require(model.get("trust_remote_code") is False, "REMOTE_CODE_FORBIDDEN")
    require(MODEL_REVISION in str(model.get("license_url")), "MODEL_LICENSE_UNPINNED")

    adapter = document.get("adapter")
    require(isinstance(adapter, dict), "ADAPTER_PROFILE_INVALID")
    targets = adapter.get("ordered_target_modules")
    require(targets == expected_target_modules(), "ADAPTER_TARGET_SET_DRIFT")
    require(len(targets) == len(set(targets)) == 128, "ADAPTER_TARGET_DUPLICATE")
    require(
        not any(re.search(r"[*?\[\]()]", target) for target in targets), "TARGET_REGEX_FORBIDDEN"
    )
    require(adapter.get("rank") == 8 and adapter.get("alpha") == 16, "ADAPTER_RANK_DRIFT")
    require(adapter.get("dropout_ppm") == 0, "ADAPTER_DROPOUT_DRIFT")

    ticket = document.get("ticket")
    require(isinstance(ticket, dict), "TICKET_PROFILE_INVALID")
    tokens_per_step = (
        ticket.get("sequence_length")
        * ticket.get("microbatch_size")
        * ticket.get("gradient_accumulation_steps")
    )
    require(ticket.get("tokens_per_optimizer_step") == tokens_per_step, "TICKET_STEP_MISMATCH")
    require(ticket.get("B") == tokens_per_step * ticket.get("H"), "TICKET_B_H_MISMATCH")
    require(ticket.get("B") == 2048 and ticket.get("H") == 2, "TICKET_FIXED_WORK_DRIFT")

    memory = document.get("memory")
    require(isinstance(memory, dict), "MEMORY_PROFILE_INVALID")
    hard_limit = memory.get("hard_max_reserved_bytes")
    headroom = memory.get("required_headroom_bytes")
    minimum_available = memory.get("required_minimum_available_at_start_bytes")
    require(
        all(isinstance(value, int) for value in (hard_limit, headroom, minimum_available)),
        "MEMORY_BOUND_INVALID",
    )
    require(
        hard_limit + headroom <= minimum_available <= GPU_TOTAL_BYTES, "MEMORY_HEADROOM_INVALID"
    )
    require(memory.get("offload_policy") == "NONE", "OFFLOAD_POLICY_INVALID")
    require(memory.get("host_offload_limit_bytes") == 0, "HOST_OFFLOAD_FORBIDDEN")

    quantization = document.get("quantization")
    require(
        quantization
        == {
            "backend": "BITSANDBYTES",
            "compute_dtype": "FLOAT16",
            "double_quantization": True,
            "quantization_type": "NF4",
            "storage_bits": 4,
        },
        "QUANTIZATION_PROFILE_INVALID",
    )
    software = document.get("software")
    require(isinstance(software, dict), "SOFTWARE_PROFILE_INVALID")
    require(software.get("pytorch") == "2.6.0+cu124", "PYTORCH_PROFILE_DRIFT")
    require(software.get("bitsandbytes") == "0.50.2", "BITSANDBYTES_PROFILE_DRIFT")

    return {
        "claim_status": claim["status"],
        "gpu_name": gpu["name"],
        "gpu_total_memory_bytes": gpu["total_memory_bytes"],
        "gpu_uuid": gpu["uuid"],
        "model_license": model["license"],
        "model_repository": model["repository"],
        "model_revision": model["revision"],
        "ordered_target_module_count": len(targets),
        "runner_id": runner["runner_id"],
        "status": "IDENTIFIED_PROFILE_FROZEN",
    }


def verify_profile(source_commit: str) -> dict[str, Any]:
    raw = tracked_bytes(PROFILE_PATH, source_commit)
    document = json.loads(raw)
    require(isinstance(document, dict), "PROFILE_INVALID")
    return {
        **validate_profile(document),
        "profile": {
            "content_id": f"sha256:{sha256_bytes(raw)}",
            **artifact(PROFILE_PATH, source_commit),
        },
    }


def verify_local_hardware(profile: dict[str, Any]) -> None:
    process = subprocess.run(
        [
            "nvidia-smi",
            "--query-gpu=name,uuid,memory.total,driver_version,compute_cap",
            "--format=csv,noheader,nounits",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    require(process.returncode == 0, "LOCAL_GPU_PROBE_FAILED", process.stderr.strip())
    rows = list(csv.reader(process.stdout.splitlines()))
    require(len(rows) == 1 and len(rows[0]) == 5, "LOCAL_GPU_PROBE_INVALID")
    name, uuid, memory_mib, driver, capability = (value.strip() for value in rows[0])
    gpu = profile["runner"]["gpu"]
    require(name == gpu["name"], "LOCAL_GPU_NAME_DRIFT")
    require(uuid == gpu["uuid"], "LOCAL_GPU_UUID_DRIFT")
    require(int(memory_mib) * 1024**2 == gpu["total_memory_bytes"], "LOCAL_GPU_MEMORY_DRIFT")
    require(driver == gpu["driver_version"], "LOCAL_GPU_DRIVER_DRIFT")
    require(capability == gpu["compute_capability"], "LOCAL_GPU_CAPABILITY_DRIFT")


def verify_architecture(source_commit: str) -> dict[str, Any]:
    changed = git_text("diff", "--name-only", FEATURE008_MERGE, source_commit).splitlines()
    production = [path for path in changed if path.startswith(PRODUCTION_PREFIXES)]
    require(not production, "PRODUCTION_SOURCE_BEFORE_PREFLIGHT", json.dumps(production))
    unexpected = [
        path
        for path in changed
        if not path.startswith("specs/009-qlora-8gb-mode/")
        and path not in ALLOWED_NON_FEATURE_PATHS
    ]
    require(not unexpected, "UNEXPECTED_PREFLIGHT_PATH", json.dumps(unexpected))
    paths = (
        "specs/009-qlora-8gb-mode/formal-refinement.md",
        "specs/009-qlora-8gb-mode/plan.md",
        "specs/009-qlora-8gb-mode/runtime-profile.md",
        "specs/009-qlora-8gb-mode/spec.md",
        "specs/009-qlora-8gb-mode/task-map.md",
        "specs/009-qlora-8gb-mode/tasks.md",
    )
    combined = "\n".join(tracked_text(path, source_commit) for path in paths)
    for marker in (
        "C++ alone",
        "Python alone",
        "Java owns",
        "BLOCKED_HARDWARE",
        "parallel",
        "REFINEMENT_ONLY",
        "semantic_completeness_claimed=false",
        FORMAL_ID,
    ):
        require(marker in combined, "ARCHITECTURE_RULE_UNBOUND", marker)
    for legacy in (
        "src/deltatorrent/apply/adapter_engine.py",
        "tests/integration/",
        "Constitution 2.0.0",
    ):
        require(legacy not in combined, "LEGACY_PATH_OR_CONSTITUTION", legacy)
    formal_diff = git_text(
        "diff",
        "--name-only",
        FEATURE008_MERGE,
        source_commit,
        "--",
        "formal/tla",
        "formal/proofs",
        "formal/schemas",
    )
    require(not formal_diff, "FORMAL_SOURCE_DIFF_PRESENT", formal_diff)
    return {
        "changed_path_count": len(changed),
        "finding_count": 0,
        "production_source_count": 0,
        "status": "PASS",
    }


def verify_source(source_commit: str) -> dict[str, Any]:
    require_ancestor(source_commit, "HEAD", "PREFLIGHT_SOURCE_NOT_ANCESTOR")
    require(
        "**Version**: 2.1.0" in tracked_text(".specify/memory/constitution.md", source_commit),
        "CONSTITUTION_VERSION_INVALID",
    )
    return {
        "artifacts": [artifact(path, source_commit) for path in SOURCE_ARTIFACTS],
        "commit": source_commit,
        "constitution_version": "2.1.0",
        "tree": git_text("rev-parse", f"{source_commit}^{{tree}}"),
    }


def verify(source_commit: str) -> dict[str, Any]:
    return {
        "architecture": verify_architecture(source_commit),
        "checks": [
            "FEATURE008_MERGE_SOURCE_EVIDENCE_REPORT_EXACT",
            "FEATURE008_TASKS_AND_NATIVE_MANIFEST_EXACT",
            "FORMAL_GO_REDERIVED_AND_NO_FORMAL_SOURCE_DIFF",
            "REFINEMENT_ONLY_CLOSED_CERTIFICATE_GRAPH",
            "NO_BASE_MUTATION_ADAPTIVE_H_PARTIAL_OR_FP_REDUCE_AUTHORITY",
            "PHYSICAL_8_GIB_RUNNER_IDENTIFIED",
            "MODEL_REVISION_LICENSE_AND_NO_TOKEN_POLICY_FROZEN",
            "EXACT_128_MODULE_ADAPTER_TARGET_LIST_FROZEN",
            "FIXED_B_H_MEMORY_HEADROOM_AND_NO_OFFLOAD_PROFILE_FROZEN",
            "PREFLIGHT_SOURCE_TREE_BOUND",
        ],
        "errors": [],
        "feature008": verify_feature008(source_commit),
        "formal": verify_formal(source_commit),
        "formal_impact": {
            "classification": "REFINEMENT_ONLY",
            "new_failure_terminals": [],
            "new_formal_action_ids": [],
            "new_protocol_visible_durability_outcomes": [],
            "status": "PASS",
        },
        "formal_semantics_id": FORMAL_ID,
        "hardware_readiness": verify_profile(source_commit),
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": verify_source(source_commit),
        "status": "PASS",
        "task_ids": ["T000", "T037", "T038"],
    }


def source_for_run(check_only: bool) -> str:
    if not check_only:
        require(
            not git_text("status", "--porcelain", "--untracked-files=all"),
            "SOURCE_TREE_NOT_CLEAN",
        )
        return git_text("rev-parse", "HEAD")
    require(OUTPUT.is_file(), "PREFLIGHT_EVIDENCE_MISSING")
    document = json.loads(OUTPUT.read_text(encoding="utf-8"))
    source = document.get("source", {}).get("commit")
    require(
        isinstance(source, str) and re.fullmatch(r"[0-9a-f]{40}", source) is not None,
        "PREFLIGHT_SOURCE_INVALID",
    )
    return source


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--verify-local-hardware", action="store_true")
    arguments = parser.parse_args()
    try:
        source_commit = source_for_run(arguments.check_only)
        if arguments.verify_local_hardware:
            profile = json.loads(tracked_bytes(PROFILE_PATH, source_commit))
            require(isinstance(profile, dict), "PROFILE_INVALID")
            validate_profile(copy.deepcopy(profile))
            verify_local_hardware(profile)
        result = verify(source_commit)
        encoded = canonical_json_bytes(result)
        if arguments.check_only:
            require(OUTPUT.read_bytes() == encoded, "PREFLIGHT_EVIDENCE_STALE")
        else:
            OUTPUT.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT.write_bytes(encoded)
    except (
        PreflightError,
        RuntimeError,
        OSError,
        UnicodeDecodeError,
        ValueError,
        TypeError,
        json.JSONDecodeError,
    ) as error:
        print(
            canonical_json_bytes(
                {
                    "error_code": str(error),
                    "formal_semantics_id": FORMAL_ID,
                    "schema_version": "1.0.0",
                    "status": "FAIL",
                }
            ).decode()
        )
        return 2
    print(encoded.decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
