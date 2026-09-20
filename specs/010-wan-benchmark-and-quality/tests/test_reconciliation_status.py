from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

FEATURE_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = FEATURE_ROOT / "scripts" / "verify_reconciliation_status.py"
MANIFEST = FEATURE_ROOT / "evidence" / "reconciliation-status.json"
ENVIRONMENT_AUDIT = FEATURE_ROOT / "evidence" / "environment-audit.json"
ENVIRONMENT_FIELDS = tuple(
    json.loads(MANIFEST.read_text(encoding="utf-8"))["environment_observation"]
)
ENVIRONMENT_CONCLUSION_BOOLEAN_FIELDS = (
    "eligible_current_lineage_campaign02_gpu_environment",
    "controller_governance_complete",
    "approved_real_wan_inventory_found",
    "pilot_multiregion_inventory_found",
)


def load_verifier() -> ModuleType:
    spec = importlib.util.spec_from_file_location("feature010_reconciliation_verifier", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_manifest(path: Path, *, require_branch: bool = False) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPT), "--manifest", str(path)]
    if require_branch:
        command.append("--require-branch")
    return subprocess.run(command, check=False, capture_output=True, text=True)


def write_manifest(tmp_path: Path, document: dict[str, object]) -> Path:
    path = tmp_path / "reconciliation-status.json"
    path.write_text(json.dumps(document), encoding="utf-8")
    return path


def environment_inputs() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    audit = json.loads(ENVIRONMENT_AUDIT.read_text(encoding="utf-8"))
    return audit, manifest["environment_observation"], manifest["claims"]


def changed_value(value: object) -> object:
    if value is None:
        return "tampered"
    if type(value) is bool:
        return not value
    if type(value) is int:
        return value + 1
    if type(value) is str:
        return f"{value}.tampered"
    if type(value) is list:
        return ["tampered"]
    raise AssertionError(f"unsupported environment field type: {type(value)}")


def test_reconciliation_status_is_fail_closed_and_git_bound() -> None:
    completed = run_manifest(MANIFEST)
    assert completed.returncode == 0, completed.stderr
    result = json.loads(completed.stdout)
    assert result["status"] == "PASS"
    assert result["feature_010"] == "STOPPED_BEFORE_PRIMARY_EXECUTION"
    assert result["feature_011"] == "BLOCKED_ON_FEATURE010_GO"
    assert result["protected_spine_diff_count"] == 0


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("drop_claim", "CLAIM_SET_MISMATCH"),
        ("fake_simulated_run", "SIMULATED_WAN_RUN_FORBIDDEN"),
        ("drop_external_requirement", "EXTERNAL_REQUIREMENTS_MISMATCH"),
        ("fake_protected_count", "RECORDED_PROTECTED_DIFF_MISMATCH"),
        ("wrong_predecessor", "FEATURE009_MERGE_MISMATCH"),
        ("wrong_environment_hash", "RECORDED_ENVIRONMENT_EVIDENCE_HASH_MISMATCH"),
    ],
)
def test_manifest_tampering_is_rejected(
    tmp_path: Path,
    mutation: str,
    expected_error: str,
) -> None:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if mutation == "drop_claim":
        document["claims"].pop("feature010_go")
    elif mutation == "fake_simulated_run":
        document["feature_010"]["simulated_wan_runs"] = 1
    elif mutation == "drop_external_requirement":
        document["missing_external_requirements"].pop()
    elif mutation == "fake_protected_count":
        document["diff_guard"]["protected_spine_diff_count"] = 1
    elif mutation == "wrong_predecessor":
        document["predecessor_feature_009"]["merge_commit"] = "0" * 40
    elif mutation == "wrong_environment_hash":
        document["environment_observation"]["evidence_sha256"] = "0" * 64
    else:  # pragma: no cover - keeps the parameter table exhaustive
        raise AssertionError(mutation)

    completed = run_manifest(write_manifest(tmp_path, document))
    assert completed.returncode == 1
    assert expected_error in completed.stderr


def test_actual_protected_git_diff_is_rejected() -> None:
    verifier = load_verifier()
    root = SCRIPT.resolve().parents[3]
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    state = copy.deepcopy(verifier.collect_git_state(root))
    state["protected_paths"] = ["formal/example.tla"]
    with pytest.raises(ValueError, match="PROTECTED_GIT_DIFF_FORBIDDEN"):
        verifier.validate_document(document, root, state, require_branch=True)


def test_actual_out_of_scope_git_diff_is_rejected() -> None:
    verifier = load_verifier()
    root = SCRIPT.resolve().parents[3]
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    state = copy.deepcopy(verifier.collect_git_state(root))
    state["out_of_scope_paths"] = ["unexpected.txt"]
    with pytest.raises(ValueError, match="OUT_OF_SCOPE_DIFF"):
        verifier.validate_document(document, root, state, require_branch=True)


def test_duplicate_environment_observation_id_is_rejected() -> None:
    verifier = load_verifier()
    audit, observation, claims = environment_inputs()
    audit["observations"][-1] = copy.deepcopy(audit["observations"][0])
    with pytest.raises(ValueError, match="ENVIRONMENT_OBSERVATION_ID_DUPLICATE"):
        verifier.validate_environment_payload(audit, observation, claims)


def test_environment_command_tampering_is_rejected() -> None:
    verifier = load_verifier()
    audit, observation, claims = environment_inputs()
    audit["observations"][0]["command"].append("--tampered")
    with pytest.raises(ValueError, match="ENVIRONMENT_COMMAND_MISMATCH_physical_gpu"):
        verifier.validate_environment_payload(audit, observation, claims)


@pytest.mark.parametrize("field", ENVIRONMENT_CONCLUSION_BOOLEAN_FIELDS)
def test_environment_conclusion_overclaim_is_rejected(field: str) -> None:
    verifier = load_verifier()
    audit, observation, claims = environment_inputs()
    audit["conclusion"][field] = True
    with pytest.raises(ValueError, match=f"ENVIRONMENT_CONCLUSION_MISMATCH_{field}"):
        verifier.validate_environment_payload(audit, observation, claims)


def test_environment_conclusion_boolean_type_confusion_is_rejected() -> None:
    verifier = load_verifier()
    audit, observation, claims = environment_inputs()
    field = "controller_governance_complete"
    audit["conclusion"][field] = 0
    with pytest.raises(ValueError, match=f"ENVIRONMENT_CONCLUSION_MISMATCH_{field}"):
        verifier.validate_environment_payload(audit, observation, claims)


@pytest.mark.parametrize("field", ENVIRONMENT_FIELDS)
def test_environment_manifest_projection_tampering_is_rejected(field: str) -> None:
    verifier = load_verifier()
    audit, observation, claims = environment_inputs()
    observation[field] = changed_value(observation[field])
    with pytest.raises(ValueError, match=f"ENVIRONMENT_MANIFEST_PROJECTION_MISMATCH_{field}"):
        verifier.validate_environment_payload(audit, observation, claims)


def test_environment_manifest_extra_field_is_rejected() -> None:
    verifier = load_verifier()
    audit, observation, claims = environment_inputs()
    observation["unreviewed_extra"] = False
    with pytest.raises(ValueError, match="ENVIRONMENT_MANIFEST_FIELD_SET_MISMATCH"):
        verifier.validate_environment_payload(audit, observation, claims)


def test_environment_audit_extra_field_is_rejected() -> None:
    verifier = load_verifier()
    audit, observation, claims = environment_inputs()
    audit["unreviewed_extra"] = False
    with pytest.raises(ValueError, match="ENVIRONMENT_FIELD_SET_MISMATCH"):
        verifier.validate_environment_payload(audit, observation, claims)


def test_required_assignment_branch_is_checked() -> None:
    verifier = load_verifier()
    root = SCRIPT.resolve().parents[3]
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    state = copy.deepcopy(verifier.collect_git_state(root))
    state["branch"] = "wrong/branch"
    with pytest.raises(ValueError, match="ACTUAL_BRANCH_MISMATCH"):
        verifier.validate_document(document, root, state, require_branch=True)


def test_uncommitted_candidate_cannot_pass_sealed_mode() -> None:
    verifier = load_verifier()
    root = SCRIPT.resolve().parents[3]
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    state = copy.deepcopy(verifier.collect_git_state(root))
    state["head"] = verifier.BASE_COMMIT
    state["untracked_paths"] = ["specs/010-wan-benchmark-and-quality/spec.md"]
    state["worktree_clean"] = False
    with pytest.raises(ValueError, match="CANDIDATE_HEAD_NOT_SEALED"):
        verifier.validate_document(
            document,
            root,
            state,
            require_branch=True,
            sealed=True,
        )


def test_feature011_completion_checkbox_cannot_be_forged(monkeypatch: pytest.MonkeyPatch) -> None:
    verifier = load_verifier()
    root = SCRIPT.resolve().parents[3]
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    original = verifier.checklist_entries

    def forged_entries(path: Path, pattern: str) -> list[tuple[str, int]]:
        entries = original(path, pattern)
        if path == root / "specs" / "011-multiregion-pilot" / "tasks.md":
            entries[-1] = ("x", 75)
        return entries

    monkeypatch.setattr(verifier, "checklist_entries", forged_entries)
    with pytest.raises(ValueError, match="FEATURE011_TASK_STATE_MISMATCH"):
        verifier.validate_document(
            document,
            root,
            verifier.collect_git_state(root),
            require_branch=True,
        )
