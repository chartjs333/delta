"""Verify the fail-closed Feature 010/011 reconciliation manifest and Git state."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

BASE_COMMIT = "7a9faf852e0ccae4d25fdc363fbf39ecf1719341"
BASE_TREE = "2ae9ad2ad0064cfb65c956464dc737c2ab03034a"
EXPECTED_BRANCH = "feature/overnight-010-011-requalification"
FORMAL_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
FORMAL_REPORT_SHA256 = "3e2e2344a038b2c902b06d275fb3e3820f95e5a780c2750e5c1a367dd82936d7"
FEATURE009_MERGE = "007eb08aa3aaee849128ba428274a9fbda561bf8"
FEATURE009_SOURCE = "f43e39fa1c60d256bab5d7e37e0756f28438d5e4"
FEATURE009_EVIDENCE = "a5e73b41feb2dad73aa11d810d0c700c548e11ba"
FEATURE009_REPORT_SHA256 = "95b312b45f3c2df4293ceaa0cbb16dd1e89c5d12a86c890211353a45798516ef"
ENVIRONMENT_EVIDENCE_SHA256 = "7e85058bd01a43e499c93a8db938798d07b76a04bbf752942ba20ac9385a4992"

PROTECTED_PREFIXES = (
    "formal/",
    "delta-core-cpp/",
    "delta-runtime-cpp/",
    "delta-ffi/",
    "delta-node-java/",
)
PROTECTED_PATTERNS = [f"{prefix}**" for prefix in PROTECTED_PREFIXES]
ALLOWED_CHANGE_PREFIXES = (
    "specs/010-wan-benchmark-and-quality/",
    "specs/011-multiregion-pilot/",
)
ALLOWED_CHANGE_FILES = {"specs/HYBRID-RUNTIME-MAP.md"}
CLAIM_KEYS = {
    "controller_governance_complete",
    "feature010_go",
    "feature011_go",
    "multiregion_qualified",
    "physical_cuda_campaign02_qualified",
    "real_wan_qualified",
}
MISSING_EXTERNAL_REQUIREMENTS = {
    "adopted_campaign02_governance_and_custody_policy",
    "four_independent_controller_authorities_and_fresh_ed25519_keys",
    "four_authenticated_owner_key_bindings_and_six_pairwise_independence_passes",
    "canonical_four_member_validator_set_with_three_mapping_and_three_registration_votes",
    "fresh_current_lineage_definition_attestation_and_separate_execution_authorization",
    "pinned_current_lineage_cuda_runtime_with_authorized_immutable_model_data_and_evaluators",
    "approved_real_wan_multiregion_endpoints_credentials_tls_identities_and_measurement",
    "pilot_pki_overlay_signed_images_and_20_to_50_worker_3_to_5_region_inventory",
    "pilot_definition_and_evaluator_quorums",
}
HISTORY = {
    11: ("881301d8443c667a478617cc663d1450aee9777a", "HISTORICAL_NO_GO"),
    19: ("b2af7b926f3525494bb5634dbedcca3fe97051e1", "GOVERNANCE_STOP"),
    28: ("84b337892cb70d0ce9823ef2d64fab572752b145", "UNSIGNED_ZERO_EXECUTION_REGISTRATION"),
    29: ("de3348fdcbd527046d5b66bc6d8c90df098d5aa8", "PROPOSED_CUSTODY_POLICY_NOT_ADOPTED"),
    30: ("670b58f4c400f5c8904ca40ba9cf3a2072e98d78", "NON_AUTHORITATIVE_DEMO"),
}
ENVIRONMENT_COMMAND_SHA256 = {
    "physical_gpu": "1a1c5793373c9add4e571d1858a098ea545eb0a32472ec51db5c7bb1fb5403fc",
    "host_cuda_toolkit": "dfa60777ada28406c275067422b3364a6698853d2c8a337d2cdfe347569d507c",
    "current_worktree_torch": "f0933332f854f607584e6fa918b073bf5156a26531456644eb20cfc1ef251498",
    "separate_untracked_torch": (
        "aae9f4528cb68a39c451b15c4c5b253f038aa65e89c12f047e98d3ddc042b5f5"
    ),
    "historical_memory_threshold": (
        "99a675fbbce0f78b45cc24587d12cf60b7838807a1d51bdacb0b18367c2d1089"
    ),
    "historical_campaign_image": (
        "0f89130790be353689177abc5a659bd4d892696d6f35497c3c0f67d3dcc15927"
    ),
    "model_cache_names": "07aade972b5d44fc728e3dbf2784c34acbd414d5f0d96b9203969846462ee5e5",
    "evaluation_dataset_cache_names": (
        "72d30ee34a095b019bbb5fbdfdceaef6a2902fc755e3e1841a39b45840c24e9b"
    ),
    "repository_actions_names": (
        "6694dba522614ae57d1cdbfc513c5b165dd01f538e7c1d0ff053feab688d808d"
    ),
    "local_controller_authority": (
        "be4a87bf0f9520b8f746c71ded5304aca6ccd268a6b81ac5bc33353d43c717a9"
    ),
    "remote_inventory_paths": ("7dfba209055aa5e2f0d1b4b1fd51f27b08ace7d3e5dbf9ed7a248e362799d711"),
}
ENVIRONMENT_OUTPUTS = {
    "physical_gpu": (
        0,
        "NVIDIA GeForce RTX 3070 Laptop GPU|8192 MiB|compute_capability=8.6",
    ),
    "host_cuda_toolkit": (0, "CUDA 12.8|V12.8.61"),
    "current_worktree_torch": (
        0,
        "torch=2.6.0+cpu|cuda_available=false|cuda_runtime=null",
    ),
    "separate_untracked_torch": (
        0,
        "torch=2.6.0+cu124|cuda_available=true|cuda_runtime=12.4|total_memory=8589410304",
    ),
    "historical_memory_threshold": (
        0,
        "visible=8589410304|threshold=8589934592|delta=-524288",
    ),
    "historical_campaign_image": (
        1,
        "image=sha256:0bb88834d973ca1b450fcc2a05333c6fe45510bee289912a5391274c351c4a4d|present=false",
    ),
    "model_cache_names": (0, "models--microsoft--Phi-3.5-mini-instruct"),
    "evaluation_dataset_cache_names": (
        0,
        "root=%USERPROFILE%/.cache/huggingface|wikitext=false|lambada=false|hellaswag=false",
    ),
    "repository_actions_names": (
        0,
        "actions_secret_names=[]|repository_variable_names=[]",
    ),
    "local_controller_authority": (
        0,
        "untracked_register_present=true|untracked_approval_present=true|"
        "register_approval_same_campaign=true|register_approval_same_reference_package=false|"
        "register_approval_same_governance_authority=false|"
        "adopted_policy_in_current_lineage=false|canonical_register_tracked=false",
    ),
    "remote_inventory_paths": (
        0,
        "candidate_paths=.github/workflows/campaign02-stage-a-bootstrap.yml|"
        "approved_inventory_paths=[]",
    ),
}
ENVIRONMENT_CONCLUSION = {
    "eligible_current_lineage_campaign02_gpu_environment": False,
    "controller_governance_complete": False,
    "approved_real_wan_inventory_found": False,
    "pilot_multiregion_inventory_found": False,
    "status": "STOPPED_BEFORE_PRIMARY_EXECUTION",
}
ENVIRONMENT_MANIFEST_OBSERVATION = {
    "observed_at_utc": "2026-09-20T14:08:03Z",
    "evidence_path": "specs/010-wan-benchmark-and-quality/evidence/environment-audit.json",
    "evidence_sha256": ENVIRONMENT_EVIDENCE_SHA256,
    "narrative_path": "specs/010-wan-benchmark-and-quality/evidence/environment-audit.md",
    "physical_gpu_present": True,
    "gpu_name": "NVIDIA GeForce RTX 3070 Laptop GPU",
    "gpu_memory_mib": 8192,
    "gpu_compute_capability": "8.6",
    "host_cuda_install_version": "12.8",
    "worker_torch_version": "2.6.0+cpu",
    "worker_cuda_available": False,
    "worker_cuda_runtime": None,
    "separate_untracked_cuda_environment_observed": True,
    "separate_untracked_torch_version": "2.6.0+cu124",
    "separate_untracked_torch_visible_gpu_bytes": 8589410304,
    "historical_literal_8gib_threshold_bytes": 8589934592,
    "required_container_image_present": False,
    "local_model_snapshot_present": True,
    "model_identity_bound_to_current_definition": False,
    "required_evaluation_datasets_present": False,
    "eligible_current_lineage_campaign02_gpu_environment": False,
    "repository_secret_names_found": [],
    "repository_variable_names_found": [],
    "untracked_controller_register_observed": True,
    "independent_controller_registry_verified": False,
    "matching_custodial_private_keys_verified": False,
    "bootstrap_signature_quorums_verified": False,
    "approved_real_wan_inventory_found": False,
    "pilot_tls_identity_inventory_found": False,
    "pilot_multiregion_inventory_found": False,
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(root: Path, *arguments: str) -> str:
    completed = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def git_is_ancestor(root: Path, ancestor: str, descendant: str) -> bool:
    completed = subprocess.run(
        ["git", "merge-base", "--is-ancestor", ancestor, descendant],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )
    require(completed.returncode in {0, 1}, "GIT_ANCESTRY_CHECK_FAILED")
    return completed.returncode == 0


def path_lines(value: str) -> set[str]:
    return {line.strip().replace("\\", "/") for line in value.splitlines() if line.strip()}


def numbered_ids(path: Path, pattern: str) -> list[int]:
    text = path.read_text(encoding="utf-8")
    return [int(value) for value in re.findall(pattern, text, flags=re.MULTILINE)]


def checklist_entries(path: Path, pattern: str) -> list[tuple[str, int]]:
    text = path.read_text(encoding="utf-8")
    return [(marker, int(value)) for marker, value in re.findall(pattern, text, flags=re.MULTILINE)]


def collect_git_state(root: Path) -> dict[str, Any]:
    head = git(root, "rev-parse", "HEAD")
    branch = git(root, "branch", "--show-current")
    changed = path_lines(git(root, "diff", "--name-only", BASE_COMMIT, "--"))
    untracked = path_lines(git(root, "ls-files", "--others", "--exclude-standard"))
    changed.update(untracked)
    worktree_status = git(root, "status", "--porcelain=v1", "--untracked-files=all")
    protected = sorted(
        path for path in changed if any(path.startswith(prefix) for prefix in PROTECTED_PREFIXES)
    )
    out_of_scope = sorted(
        path
        for path in changed
        if path not in ALLOWED_CHANGE_FILES
        and not any(path.startswith(prefix) for prefix in ALLOWED_CHANGE_PREFIXES)
    )
    return {
        "base_tree": git(root, "rev-parse", f"{BASE_COMMIT}^{{tree}}"),
        "branch": branch,
        "changed_paths": sorted(changed),
        "head": head,
        "head_tree": git(root, "rev-parse", "HEAD^{tree}"),
        "is_base_ancestor": git_is_ancestor(root, BASE_COMMIT, head),
        "is_feature009_ancestor": git_is_ancestor(root, FEATURE009_MERGE, head),
        "out_of_scope_paths": out_of_scope,
        "protected_paths": protected,
        "untracked_paths": sorted(untracked),
        "worktree_clean": not worktree_status,
    }


def validate_environment_payload(
    environment_record: dict[str, Any],
    observation: dict[str, Any],
    claims: dict[str, Any],
) -> None:
    require(type(environment_record) is dict, "ENVIRONMENT_NOT_OBJECT")
    require(type(observation) is dict, "ENVIRONMENT_MANIFEST_NOT_OBJECT")
    require(type(claims) is dict, "CLAIMS_NOT_OBJECT")
    require(
        set(environment_record)
        == {
            "schema_version",
            "type_name",
            "observed_at_utc",
            "scope",
            "command_working_directory",
            "authority",
            "observations",
            "conclusion",
        },
        "ENVIRONMENT_FIELD_SET_MISMATCH",
    )
    require(environment_record["schema_version"] == "1.0.0", "ENVIRONMENT_SCHEMA_MISMATCH")
    require(
        environment_record["type_name"] == "FEATURE010_ASSIGNMENT_ENVIRONMENT_AUDIT",
        "ENVIRONMENT_TYPE_MISMATCH",
    )
    require(
        environment_record["scope"] == "assignment_host_and_repository_visible_names_only",
        "ENVIRONMENT_SCOPE_MISMATCH",
    )
    require(
        environment_record["command_working_directory"] == "repository_root",
        "ENVIRONMENT_COMMAND_CWD_MISMATCH",
    )
    require(environment_record["authority"] is False, "ENVIRONMENT_AUTHORITY_FORBIDDEN")
    require(
        environment_record["observed_at_utc"]
        == ENVIRONMENT_MANIFEST_OBSERVATION["observed_at_utc"],
        "ENVIRONMENT_TIMESTAMP_MISMATCH",
    )

    require(
        set(observation) == set(ENVIRONMENT_MANIFEST_OBSERVATION),
        "ENVIRONMENT_MANIFEST_FIELD_SET_MISMATCH",
    )
    for field, expected in ENVIRONMENT_MANIFEST_OBSERVATION.items():
        actual = observation[field]
        require(
            type(actual) is type(expected) and actual == expected,
            f"ENVIRONMENT_MANIFEST_PROJECTION_MISMATCH_{field}",
        )

    items = environment_record["observations"]
    require(type(items) is list, "ENVIRONMENT_OBSERVATIONS_NOT_LIST")
    require(
        all(type(item) is dict and type(item.get("id")) is str for item in items),
        "ENVIRONMENT_OBSERVATION_SHAPE_MISMATCH",
    )
    identifiers = [item["id"] for item in items]
    require(
        len(identifiers) == len(set(identifiers)),
        "ENVIRONMENT_OBSERVATION_ID_DUPLICATE",
    )
    require(
        set(identifiers) == set(ENVIRONMENT_OUTPUTS),
        "ENVIRONMENT_OBSERVATION_SET_MISMATCH",
    )
    require(
        set(ENVIRONMENT_COMMAND_SHA256) == set(ENVIRONMENT_OUTPUTS),
        "ENVIRONMENT_EXPECTATION_SET_MISMATCH",
    )
    records = {item["id"]: item for item in items}
    for identifier, (exit_code, normalized_output) in ENVIRONMENT_OUTPUTS.items():
        record = records[identifier]
        require(
            set(record) == {"id", "command", "exit_code", "normalized_output", "output_sha256"},
            f"ENVIRONMENT_RECORD_FIELD_SET_MISMATCH_{identifier}",
        )
        command = record["command"]
        require(
            type(command) is list and all(type(argument) is str for argument in command),
            f"ENVIRONMENT_COMMAND_SHAPE_MISMATCH_{identifier}",
        )
        command_digest = hashlib.sha256(
            json.dumps(command, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        require(
            command_digest == ENVIRONMENT_COMMAND_SHA256[identifier],
            f"ENVIRONMENT_COMMAND_MISMATCH_{identifier}",
        )
        require(
            type(record["exit_code"]) is int and record["exit_code"] == exit_code,
            f"ENVIRONMENT_EXIT_MISMATCH_{identifier}",
        )
        require(
            type(record["normalized_output"]) is str
            and record["normalized_output"] == normalized_output,
            f"ENVIRONMENT_OUTPUT_MISMATCH_{identifier}",
        )
        require(
            record["output_sha256"]
            == hashlib.sha256(normalized_output.encode("utf-8")).hexdigest(),
            f"ENVIRONMENT_OUTPUT_HASH_MISMATCH_{identifier}",
        )

    conclusion = environment_record["conclusion"]
    require(type(conclusion) is dict, "ENVIRONMENT_CONCLUSION_SHAPE_MISMATCH")
    require(
        set(conclusion) == set(ENVIRONMENT_CONCLUSION),
        "ENVIRONMENT_CONCLUSION_FIELD_SET_MISMATCH",
    )
    for field, expected in ENVIRONMENT_CONCLUSION.items():
        actual = conclusion[field]
        require(
            type(actual) is type(expected) and actual == expected,
            f"ENVIRONMENT_CONCLUSION_MISMATCH_{field}",
        )
    require(
        conclusion["eligible_current_lineage_campaign02_gpu_environment"]
        is observation["eligible_current_lineage_campaign02_gpu_environment"],
        "ENVIRONMENT_GPU_CONCLUSION_DRIFT",
    )
    require(
        conclusion["approved_real_wan_inventory_found"]
        is observation["approved_real_wan_inventory_found"],
        "ENVIRONMENT_WAN_CONCLUSION_DRIFT",
    )
    require(
        conclusion["pilot_multiregion_inventory_found"]
        is observation["pilot_multiregion_inventory_found"],
        "ENVIRONMENT_PILOT_CONCLUSION_DRIFT",
    )
    require(
        conclusion["controller_governance_complete"] is claims["controller_governance_complete"],
        "ENVIRONMENT_CONTROLLER_CONCLUSION_DRIFT",
    )


def validate_document(
    document: dict[str, Any],
    root: Path,
    state: dict[str, Any],
    *,
    require_branch: bool,
    sealed: bool = False,
) -> dict[str, Any]:
    require(type(document) is dict, "DOCUMENT_NOT_OBJECT")
    require(document.get("schema_version") == "1.0.0", "SCHEMA_VERSION_MISMATCH")
    require(document.get("type_name") == "FEATURE010011_RECONCILIATION_STATUS", "TYPE_MISMATCH")
    require(document.get("status") == "WORKING_VERSION_READY", "STATUS_MUST_REMAIN_WVR")

    source = document["source"]
    require(source["branch"] == EXPECTED_BRANCH, "RECORDED_BRANCH_MISMATCH")
    require(source["base_commit"] == BASE_COMMIT, "BASE_COMMIT_MISMATCH")
    require(source["base_tree"] == BASE_TREE, "BASE_TREE_MISMATCH")
    require(
        source["candidate_commit_binding"] == "runtime_git_head_and_external_handoff",
        "CANDIDATE_BINDING_MISMATCH",
    )
    require(state["base_tree"] == BASE_TREE, "ACTUAL_BASE_TREE_MISMATCH")
    require(state["is_base_ancestor"], "BASE_NOT_ANCESTOR_OF_HEAD")
    if require_branch:
        require(state["branch"] == EXPECTED_BRANCH, "ACTUAL_BRANCH_MISMATCH")
    require(not state["out_of_scope_paths"], "OUT_OF_SCOPE_DIFF")
    require(not state["protected_paths"], "PROTECTED_GIT_DIFF_FORBIDDEN")
    if sealed:
        require(state["head"] != BASE_COMMIT, "CANDIDATE_HEAD_NOT_SEALED")
        require(state["changed_paths"], "SEALED_CANDIDATE_DIFF_MISSING")
        require(not state["untracked_paths"], "SEALED_CANDIDATE_HAS_UNTRACKED_PATHS")
        require(state["worktree_clean"], "SEALED_CANDIDATE_WORKTREE_DIRTY")

    formal = document["formal"]
    require(formal["status"] == "GO", "FORMAL_NOT_GO")
    require(formal["formal_semantics_id"] == FORMAL_ID, "FORMAL_ID_MISMATCH")
    require(formal["semantic_change"] is False, "SEMANTIC_CHANGE_FORBIDDEN")
    formal_report = root / formal["report_path"]
    report_digest = digest(formal_report)
    report_document = json.loads(formal_report.read_text(encoding="utf-8"))
    require(report_digest == FORMAL_REPORT_SHA256, "FORMAL_REPORT_HASH_MISMATCH")
    require(formal["report_sha256"] == report_digest, "RECORDED_REPORT_HASH_MISMATCH")
    require(report_document["decision"] == "GO", "FORMAL_REPORT_DECISION_NOT_GO")
    require(report_document["formal_semantics_id"] == FORMAL_ID, "FORMAL_REPORT_ID_MISMATCH")

    predecessor = document["predecessor_feature_009"]
    require(predecessor["merge_commit"] == FEATURE009_MERGE, "FEATURE009_MERGE_MISMATCH")
    require(predecessor["source_commit"] == FEATURE009_SOURCE, "FEATURE009_SOURCE_MISMATCH")
    require(predecessor["evidence_commit"] == FEATURE009_EVIDENCE, "FEATURE009_EVIDENCE_MISMATCH")
    require(state["is_feature009_ancestor"], "FEATURE009_NOT_ANCESTOR")
    predecessor_report = root / predecessor["report_path"]
    require(
        digest(predecessor_report) == FEATURE009_REPORT_SHA256, "FEATURE009_REPORT_HASH_MISMATCH"
    )
    require(
        predecessor["report_sha256"] == FEATURE009_REPORT_SHA256,
        "RECORDED_FEATURE009_HASH_MISMATCH",
    )
    predecessor_document = json.loads(predecessor_report.read_text(encoding="utf-8"))
    require(predecessor_document["status"] == "PASS", "FEATURE009_REPORT_NOT_PASS")
    require(
        predecessor_document["formal"]["formal_semantics_id"] == FORMAL_ID,
        "FEATURE009_FORMAL_ID_MISMATCH",
    )

    working = document["working_version"]
    require(working["status"] == "PASS", "WORKING_VERSION_NOT_PASS")
    require(working["scope"] == "single-host Step 5C only", "WORKING_VERSION_SCOPE_MISMATCH")
    require(working["ready_sha"] == BASE_COMMIT, "WORKING_VERSION_SHA_MISMATCH")

    history_items = document["historical_inputs"]
    require(len(history_items) == len(HISTORY), "HISTORY_COUNT_MISMATCH")
    history = {item["pull_request"]: item for item in history_items}
    require(set(history) == set(HISTORY), "HISTORY_PR_SET_MISMATCH")
    for number, (head, classification) in HISTORY.items():
        require(history[number]["head"] == head, f"HISTORY_HEAD_MISMATCH_{number}")
        require(
            history[number]["classification"] == classification, f"HISTORY_CLASS_MISMATCH_{number}"
        )
        require(
            history[number]["eligible_as_authority"] is False, f"DRAFT_AUTHORITY_FORBIDDEN_{number}"
        )

    claims = document["claims"]
    require(type(claims) is dict, "CLAIMS_NOT_OBJECT")
    require(set(claims) == CLAIM_KEYS, "CLAIM_SET_MISMATCH")
    require(all(value is False for value in claims.values()), "QUALIFICATION_CLAIM_FORBIDDEN")

    observation = document["environment_observation"]
    require(type(observation) is dict, "ENVIRONMENT_MANIFEST_NOT_OBJECT")
    require(
        observation.get("evidence_sha256") == ENVIRONMENT_EVIDENCE_SHA256,
        "RECORDED_ENVIRONMENT_EVIDENCE_HASH_MISMATCH",
    )
    evidence_path = root / ENVIRONMENT_MANIFEST_OBSERVATION["evidence_path"]
    require(evidence_path.is_file(), "ENVIRONMENT_EVIDENCE_MISSING")
    environment_digest = digest(evidence_path)
    require(environment_digest == ENVIRONMENT_EVIDENCE_SHA256, "ENVIRONMENT_EVIDENCE_HASH_MISMATCH")
    environment_record = json.loads(evidence_path.read_text(encoding="utf-8"))
    validate_environment_payload(environment_record, observation, claims)
    require((root / observation["narrative_path"]).is_file(), "ENVIRONMENT_NARRATIVE_MISSING")

    feature_010 = document["feature_010"]
    require(
        feature_010["status"] == "STOPPED_BEFORE_PRIMARY_EXECUTION",
        "FEATURE010_STATUS_MUST_BE_STOP",
    )
    require(feature_010["primary_observations"] == 0, "PRIMARY_OBSERVATION_FORBIDDEN")
    require(feature_010["simulated_wan_runs"] == 0, "SIMULATED_WAN_RUN_FORBIDDEN")
    require(feature_010["approved_real_wan_runs"] == 0, "REAL_WAN_CLAIM_FORBIDDEN")
    require(feature_010["benchmark_result_qc_id"] is None, "RESULT_QC_MUST_BE_ABSENT")
    require(feature_010["feature010_go_checkpoint_sha"] is None, "GO_CHECKPOINT_FORBIDDEN")

    feature_011 = document["feature_011"]
    require(feature_011["status"] == "BLOCKED_ON_FEATURE010_GO", "FEATURE011_NOT_BLOCKED")
    require(feature_011["remote_provisioning_runs"] == 0, "REMOTE_PROVISIONING_FORBIDDEN")
    require(feature_011["pilot_runs"] == 0, "PILOT_RUN_FORBIDDEN")
    require(feature_011["pilot_result_qc_id"] is None, "PILOT_QC_MUST_BE_ABSENT")

    require(
        set(document["missing_external_requirements"]) == MISSING_EXTERNAL_REQUIREMENTS,
        "EXTERNAL_REQUIREMENTS_MISMATCH",
    )

    guard = document["diff_guard"]
    require(guard["protected_paths"] == PROTECTED_PATTERNS, "PROTECTED_PATTERN_MISMATCH")
    require(
        guard["protected_spine_diff_count"] == len(state["protected_paths"]),
        "RECORDED_PROTECTED_DIFF_MISMATCH",
    )
    require(guard["protected_spine_diff_count"] == 0, "PROTECTED_DIFF_FORBIDDEN")

    completeness_checks = [
        (
            root / "specs" / "010-wan-benchmark-and-quality" / "tasks.md",
            r"^- \[[ x]\] T(\d{3})\b",
            list(range(55)),
            "FEATURE010_TASK_IDS_INCOMPLETE",
        ),
        (
            root / "specs" / "010-wan-benchmark-and-quality" / "runtime-tasks.md",
            r"^- \[[ x]\] \*\*HR010-(\d{3})\*\*",
            list(range(1, 19)),
            "FEATURE010_RUNTIME_TASK_IDS_INCOMPLETE",
        ),
        (
            root / "specs" / "010-wan-benchmark-and-quality" / "spec.md",
            r"^- \*\*FR-(\d{3})\*\*:",
            list(range(1, 44)),
            "FEATURE010_REQUIREMENTS_INCOMPLETE",
        ),
        (
            root / "specs" / "010-wan-benchmark-and-quality" / "spec.md",
            r"^- \*\*SC-(\d{3})\*\*:",
            list(range(1, 9)),
            "FEATURE010_SUCCESS_CRITERIA_INCOMPLETE",
        ),
        (
            root / "specs" / "011-multiregion-pilot" / "tasks.md",
            r"^- \[[ x]\] T(\d{3})\b",
            list(range(76)),
            "FEATURE011_TASK_IDS_INCOMPLETE",
        ),
        (
            root / "specs" / "011-multiregion-pilot" / "runtime-tasks.md",
            r"^- \[[ x]\] \*\*HR011-(\d{3})\*\*",
            list(range(1, 17)),
            "FEATURE011_RUNTIME_TASK_IDS_INCOMPLETE",
        ),
        (
            root / "specs" / "011-multiregion-pilot" / "spec.md",
            r"^- \*\*FR-(\d{3})\*\*:",
            list(range(1, 58)),
            "FEATURE011_REQUIREMENTS_INCOMPLETE",
        ),
        (
            root / "specs" / "011-multiregion-pilot" / "spec.md",
            r"^- \*\*SC-(\d{3})\*\*:",
            list(range(1, 11)),
            "FEATURE011_SUCCESS_CRITERIA_INCOMPLETE",
        ),
    ]
    for path, pattern, expected, error in completeness_checks:
        require(numbered_ids(path, pattern) == expected, error)

    feature_010_task_entries = checklist_entries(
        root / "specs" / "010-wan-benchmark-and-quality" / "tasks.md",
        r"^- \[([ x])\] T(\d{3})\b",
    )
    require(
        feature_010_task_entries == [("x", 0), *[(" ", value) for value in range(1, 55)]],
        "FEATURE010_TASK_STATE_MISMATCH",
    )
    feature_010_runtime_entries = checklist_entries(
        root / "specs" / "010-wan-benchmark-and-quality" / "runtime-tasks.md",
        r"^- \[([ x])\] \*\*HR010-(\d{3})\*\*",
    )
    require(
        feature_010_runtime_entries == [(" ", value) for value in range(1, 19)],
        "FEATURE010_RUNTIME_TASK_STATE_MISMATCH",
    )
    feature_011_task_entries = checklist_entries(
        root / "specs" / "011-multiregion-pilot" / "tasks.md",
        r"^- \[([ x])\] T(\d{3})\b",
    )
    require(
        feature_011_task_entries == [(" ", value) for value in range(76)],
        "FEATURE011_TASK_STATE_MISMATCH",
    )
    feature_011_runtime_entries = checklist_entries(
        root / "specs" / "011-multiregion-pilot" / "runtime-tasks.md",
        r"^- \[([ x])\] \*\*HR011-(\d{3})\*\*",
    )
    require(
        feature_011_runtime_entries == [(" ", value) for value in range(1, 17)],
        "FEATURE011_RUNTIME_TASK_STATE_MISMATCH",
    )

    return {
        "actual_branch": state["branch"],
        "base_commit": BASE_COMMIT,
        "changed_path_count": len(state["changed_paths"]),
        "feature_010": feature_010["status"],
        "feature_011": feature_011["status"],
        "formal_semantics_id": FORMAL_ID,
        "head_commit": state["head"],
        "head_tree": state["head_tree"],
        "protected_spine_diff_count": len(state["protected_paths"]),
        "sealed": sealed,
        "status": "PASS",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--require-branch", action="store_true")
    parser.add_argument("--sealed", action="store_true")
    arguments = parser.parse_args()
    root = Path(__file__).resolve().parents[3]
    default_manifest = (
        root / "specs" / "010-wan-benchmark-and-quality" / "evidence" / "reconciliation-status.json"
    )
    evidence_path = arguments.manifest.resolve() if arguments.manifest else default_manifest
    try:
        document = json.loads(evidence_path.read_text(encoding="utf-8"))
        result = validate_document(
            document,
            root,
            collect_git_state(root),
            require_branch=arguments.require_branch,
            sealed=arguments.sealed,
        )
    except (
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
        subprocess.SubprocessError,
    ) as error:
        print(
            json.dumps(
                {"error": f"{type(error).__name__}:{error}", "status": "FAIL"},
                sort_keys=True,
                separators=(",", ":"),
            ),
            file=sys.stderr,
        )
        return 1
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
