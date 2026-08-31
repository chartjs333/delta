"""Fail closed before Stage B when frozen scientific execution inputs are inconsistent."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tomllib
from pathlib import Path
from typing import Any, Final

ROOT: Final = Path(__file__).resolve().parents[3]
AUTHORIZATION: Final = ROOT / "reports/benchmark/primary-execution-authorization.json"
DEFINITION: Final = ROOT / "configs/benchmark/primary.yaml"
WORKLOAD: Final = ROOT / "configs/benchmark/workload-v1.json"
DEPENDENCIES: Final = ROOT / "configs/benchmark/dependencies-v1.json"
PHYSICAL_PROFILE: Final = ROOT / "configs/qlora/8gb-reference.json"
STAGE_A: Final = ROOT / "specs/010-wan-benchmark-and-quality/evidence/primary-exactness.json"
OUTPUT: Final = ROOT / "specs/010-wan-benchmark-and-quality/evidence/primary-scientific-prerun.json"

DEFINITION_ID: Final = "sha256:dd607651128bca0b8edfa861093945b0bac2355c93d9d45b4c8b08457fba4244"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
SOURCE_COMMIT: Final = "c460f3003277bb81db86f9afc1d7211e27870001"
SOURCE_TREE: Final = "d34d6b5b434bd5a81b7b202380ac500435c9b75d"
STAGE_B_TASK_IDS: Final = ("T035", "T036", "T039", "HR010-016")


class StageBPrerunError(RuntimeError):
    """Stable verification error for the recorded Stage B STOP artifact."""


def require(condition: bool, code: str) -> None:
    if not condition:
        raise StageBPrerunError(code)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def sha256_id(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def load_canonical(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw)
    require(isinstance(value, dict), f"JSON_OBJECT_REQUIRED:{path.name}")
    require(
        raw in {canonical_bytes(value), canonical_bytes(value) + b"\n"}, f"NONCANONICAL:{path.name}"
    )
    return value, raw


def load_json_object(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = path.read_bytes()
    value = json.loads(raw)
    require(isinstance(value, dict), f"JSON_OBJECT_REQUIRED:{path.name}")
    return value, raw


def git_bytes(*arguments: str, allow_not_found: bool = False) -> bytes:
    process = subprocess.run(
        ("git", *arguments),
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if allow_not_found and process.returncode == 1:
        return b""
    require(process.returncode == 0, "GIT_COMMAND_FAILED")
    return process.stdout


def source_bytes(path: str) -> bytes:
    return git_bytes("show", f"{SOURCE_COMMIT}:{path}")


def workload_check(
    definition: dict[str, Any], workload: dict[str, Any], stage_a: dict[str, Any]
) -> dict[str, object]:
    result = stage_a["primary_exactness_result"]
    ticket_budget = int(definition["B"])
    ticket_count = int(workload["ticket_count"])
    optimizer_steps = int(definition["H"])
    tokens_per_optimizer_step = int(workload["tokens_per_optimizer_step"])
    required_total = ticket_budget * ticket_count
    executor_total = ticket_budget
    stage_a_total = int(result["primary_token_budget"])
    stage_a_per_ticket = int(result["primary_tokens_per_ticket"])
    checks = {
        "B_equals_H_times_tokens_per_optimizer_step": (
            ticket_budget == optimizer_steps * tokens_per_optimizer_step
        ),
        "executor_total_equals_ticket_contract_total": executor_total == required_total,
        "stage_a_per_ticket_equals_B": stage_a_per_ticket == ticket_budget,
        "stage_a_total_equals_ticket_contract_total": stage_a_total == required_total,
    }
    return {
        "B": ticket_budget,
        "H": optimizer_steps,
        "checks": checks,
        "executor_processed_tokens_per_arm_run": executor_total,
        "stage_a_primary_token_budget": stage_a_total,
        "stage_a_primary_tokens_per_ticket": stage_a_per_ticket,
        "status": "PASS" if all(checks.values()) else "FAIL",
        "ticket_contract_total_tokens": required_total,
        "ticket_count": ticket_count,
        "tokens_per_optimizer_step": tokens_per_optimizer_step,
    }


def software_check(profile: dict[str, Any]) -> dict[str, object]:
    lock = tomllib.loads(source_bytes("uv.lock").decode("utf-8"))
    packages = lock.get("package", [])
    require(isinstance(packages, list), "UV_LOCK_PACKAGE_SET_INVALID")
    versions: dict[str, set[str]] = {}
    sources: dict[str, set[str]] = {}
    for package in packages:
        require(isinstance(package, dict), "UV_LOCK_PACKAGE_INVALID")
        name = str(package.get("name", ""))
        versions.setdefault(name, set()).add(str(package.get("version", "")))
        source = package.get("source")
        if isinstance(source, dict):
            sources.setdefault(name, set()).add(str(source.get("registry", "")))
    required = profile["software"]
    package_names = {
        "accelerate": "accelerate",
        "bitsandbytes": "bitsandbytes",
        "huggingface_hub": "huggingface-hub",
        "peft": "peft",
        "pytorch": "torch",
        "transformers": "transformers",
    }
    missing = sorted(
        profile_name
        for profile_name, package_name in package_names.items()
        if str(required[profile_name]) not in versions.get(package_name, set())
    )
    torch_versions = sorted(versions.get("torch", set()))
    torch_sources = sorted(sources.get("torch", set()))
    cuda_torch_bound = str(required["pytorch"]) in torch_versions and all(
        "/cpu" not in source for source in torch_sources
    )
    return {
        "cuda_torch_bound_by_uv_lock": cuda_torch_bound,
        "missing_or_mismatched_profile_packages": missing,
        "physical_profile_required": required,
        "python_profile_id": sha256_id(source_bytes("uv.lock")),
        "status": "PASS" if cuda_torch_bound and not missing else "FAIL",
        "uv_lock_torch_sources": torch_sources,
        "uv_lock_torch_versions": torch_versions,
    }


def evaluation_check(definition: dict[str, Any], dependencies: dict[str, Any]) -> dict[str, object]:
    artifacts = [
        item
        for item in dependencies["artifacts"]
        if str(item["role"]).startswith(("VALIDATION", "DOWNSTREAM", "POST_TRAINING"))
    ]
    method_fields = {
        "batching",
        "context_window",
        "fewshot",
        "implementation_id",
        "normalization",
        "prompt_template",
        "scoring_method",
        "tokenization",
        "version",
    }
    quality_metrics = [
        item
        for item in definition["metric_definitions"]
        if str(item["metric_id"]).startswith(
            ("validation_", "downstream_", "post_training_", "per_domain_")
        )
    ]
    implementation_ids = sorted({str(item["implementation_id"]) for item in quality_metrics})
    quality_analyzer_id = sha256_id(
        source_bytes("delta-worker-python/src/deltatorrent/benchmark/quality.py")
    )
    bindings = sorted(method_fields.intersection(*(set(item) for item in artifacts)))
    checks = {
        "dataset_artifacts_are_immutable": len(artifacts) == len(definition["evaluation_ids"]),
        "evaluation_method_fields_are_bound": bool(bindings),
        "metric_implementation_is_more_than_posthoc_analyzer": implementation_ids
        != [quality_analyzer_id],
    }
    return {
        "checks": checks,
        "evaluation_artifact_roles": [str(item["role"]) for item in artifacts],
        "evaluation_method_fields_present_in_all_artifacts": bindings,
        "quality_analyzer_id": quality_analyzer_id,
        "quality_metric_implementation_ids": implementation_ids,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def runner_check(definition: dict[str, Any], authorization: dict[str, Any]) -> dict[str, object]:
    callers = (
        git_bytes(
            "grep",
            "-l",
            "write_observation(",
            SOURCE_COMMIT,
            "--",
            "delta-worker-python/src",
            allow_not_found=True,
        )
        .decode("utf-8")
        .splitlines()
    )
    production_callers = sorted(
        path.split(":", 1)[-1] for path in callers if not path.endswith("primary_executor.py")
    )
    runner_fields = {"approved_runner_id", "measured_runner_id", "runner_id"}
    checks = {
        "approved_runner_bound_by_authorization": bool(runner_fields.intersection(authorization)),
        "measured_runner_bound_by_definition": bool(runner_fields.intersection(definition)),
        "production_observation_writer_present": bool(production_callers),
    }
    return {
        "checks": checks,
        "production_observation_writer_paths": production_callers,
        "status": "PASS" if all(checks.values()) else "FAIL",
    }


def build() -> dict[str, object]:
    authorization, authorization_raw = load_canonical(AUTHORIZATION)
    definition, _ = load_canonical(DEFINITION)
    workload, _ = load_canonical(WORKLOAD)
    dependencies, _ = load_canonical(DEPENDENCIES)
    physical_profile, _ = load_json_object(PHYSICAL_PROFILE)
    stage_a, stage_a_raw = load_canonical(STAGE_A)

    require(definition.get("formal_semantics_id") == FORMAL_ID, "DEFINITION_FORMAL_ID")
    require(definition.get("source_commit") == SOURCE_COMMIT, "DEFINITION_SOURCE_COMMIT")
    require(definition.get("source_tree") == SOURCE_TREE, "DEFINITION_SOURCE_TREE")
    require(stage_a.get("status") == "PASS", "STAGE_A_STATUS")
    require(stage_a.get("stage_b_entry_condition_satisfied") is True, "STAGE_A_ENTRY")
    require(stage_a.get("primary_scientific_execution_count") == 0, "SCIENTIFIC_RUN_ALREADY_EXISTS")
    require(authorization.get("status") == "APPROVED_STAGED", "AUTHORIZATION_STATUS")
    require(
        set(STAGE_B_TASK_IDS[:-1]).issubset(set(authorization["authorized_task_ids"])),
        "STAGE_B_TASK_AUTHORIZATION",
    )
    require(
        git_bytes("show", "-s", "--format=%T", SOURCE_COMMIT).decode().strip() == SOURCE_TREE,
        "SOURCE_TREE_MISMATCH",
    )

    checks = {
        "approved_measured_runner": runner_check(definition, authorization),
        "pinned_gpu_scientific_software": software_check(physical_profile),
        "preregistered_evaluation_methods": evaluation_check(definition, dependencies),
        "workload_ticket_token_reconciliation": workload_check(definition, workload, stage_a),
    }
    stop_codes = sorted(name.upper() for name, value in checks.items() if value["status"] != "PASS")
    require(stop_codes, "EXPECTED_STAGE_B_STOP_NOT_REPRODUCED")
    return {
        "affected_task_ids": list(STAGE_B_TASK_IDS),
        "authorization_id": sha256_id(authorization_raw),
        "benchmark_definition_id": DEFINITION_ID,
        "checks": checks,
        "decision_on_failure": authorization["decision_on_failure"],
        "feature_010_decision": "NO_GO",
        "feature_011_authorized": False,
        "formal_semantics_id": FORMAL_ID,
        "primary_scientific_execution_count": 0,
        "real_wan_authorized": False,
        "result_qc_authorized": False,
        "schema_version": "1.0.0",
        "source_commit": SOURCE_COMMIT,
        "source_tree": SOURCE_TREE,
        "stage_a_evidence_id": sha256_id(stage_a_raw),
        "status": "STOP_BEFORE_PRIMARY_SCIENTIFIC_EXECUTION",
        "stop_codes": stop_codes,
        "tasks_completed": [],
        "type_name": "PRIMARY_SCIENTIFIC_PRERUN_EVIDENCE",
    }


def verify_recorded(report: dict[str, object]) -> None:
    recorded, raw = load_canonical(OUTPUT)
    require(recorded == report, "STAGE_B_PRERUN_EVIDENCE_STALE")
    require(raw == canonical_bytes(recorded) + b"\n", "STAGE_B_PRERUN_ENCODING")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-only", action="store_true")
    arguments = parser.parse_args()
    try:
        report = build()
        if arguments.check_only:
            verify_recorded(report)
        print(json.dumps(report, ensure_ascii=False, separators=(",", ":"), sort_keys=True))
        return 0
    except (OSError, ValueError, json.JSONDecodeError, StageBPrerunError) as error:
        print(json.dumps({"error_code": str(error), "status": "FAIL"}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
