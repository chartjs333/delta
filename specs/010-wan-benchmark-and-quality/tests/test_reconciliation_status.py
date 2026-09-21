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


def expected_branch_state(verifier: ModuleType, root: Path) -> dict[str, object]:
    state = copy.deepcopy(verifier.collect_git_state(root))
    state["branch"] = verifier.EXPECTED_BRANCH
    return state


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


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("top_level_go", "DOCUMENT_FIELD_SET_MISMATCH"),
        ("source_execution_authorized", "SOURCE_FIELD_SET_MISMATCH"),
        ("feature010_all_gates_passed", "FEATURE010_FIELD_SET_MISMATCH"),
        ("duplicate_external_requirement", "EXTERNAL_REQUIREMENTS_DUPLICATE"),
        ("bool_primary_observations", "PRIMARY_OBSERVATION_FORBIDDEN"),
        ("bool_pilot_runs", "PILOT_RUN_FORBIDDEN"),
    ],
)
def test_required_reviewer_mutations_are_rejected(
    tmp_path: Path,
    mutation: str,
    expected_error: str,
) -> None:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if mutation == "top_level_go":
        document["qualification_decision"] = "GO"
    elif mutation == "source_execution_authorized":
        document["source"]["execution_authorized"] = True
    elif mutation == "feature010_all_gates_passed":
        document["feature_010"]["all_gates_passed"] = True
    elif mutation == "duplicate_external_requirement":
        document["missing_external_requirements"].append(
            document["missing_external_requirements"][0]
        )
    elif mutation == "bool_primary_observations":
        document["feature_010"]["primary_observations"] = False
    elif mutation == "bool_pilot_runs":
        document["feature_011"]["pilot_runs"] = False
    else:  # pragma: no cover - keeps the parameter table exhaustive
        raise AssertionError(mutation)

    completed = run_manifest(write_manifest(tmp_path, document))
    assert completed.returncode == 1
    assert expected_error in completed.stderr


@pytest.mark.parametrize(
    ("path", "expected_error"),
    [
        ((), "DOCUMENT_FIELD_SET_MISMATCH"),
        (("source",), "SOURCE_FIELD_SET_MISMATCH"),
        (("formal",), "FORMAL_FIELD_SET_MISMATCH"),
        (("working_version",), "WORKING_VERSION_FIELD_SET_MISMATCH"),
        (("predecessor_feature_009",), "FEATURE009_PREDECESSOR_FIELD_SET_MISMATCH"),
        (("historical_inputs", 0), "HISTORY_RECORD_FIELD_SET_MISMATCH"),
        (("feature_010",), "FEATURE010_FIELD_SET_MISMATCH"),
        (("feature_011",), "FEATURE011_FIELD_SET_MISMATCH"),
        (("claims",), "CLAIM_SET_MISMATCH"),
        (("diff_guard",), "DIFF_GUARD_FIELD_SET_MISMATCH"),
    ],
)
def test_authoritative_objects_reject_extra_fields(
    tmp_path: Path,
    path: tuple[str | int, ...],
    expected_error: str,
) -> None:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    target = document
    for component in path:
        target = target[component]
    target["unreviewed_extra"] = False

    completed = run_manifest(write_manifest(tmp_path, document))
    assert completed.returncode == 1
    assert expected_error in completed.stderr


@pytest.mark.parametrize(
    ("section", "field", "expected_error"),
    [
        ("feature_010", "primary_observations", "PRIMARY_OBSERVATION_FORBIDDEN"),
        ("feature_010", "simulated_wan_runs", "SIMULATED_WAN_RUN_FORBIDDEN"),
        ("feature_010", "approved_real_wan_runs", "REAL_WAN_CLAIM_FORBIDDEN"),
        ("feature_011", "remote_provisioning_runs", "REMOTE_PROVISIONING_FORBIDDEN"),
        ("feature_011", "pilot_runs", "PILOT_RUN_FORBIDDEN"),
        ("diff_guard", "protected_spine_diff_count", "RECORDED_PROTECTED_DIFF_MISMATCH"),
    ],
)
@pytest.mark.parametrize("invalid_zero", [False, 0.0])
def test_numeric_fields_reject_bool_and_float_zero(
    tmp_path: Path,
    section: str,
    field: str,
    expected_error: str,
    invalid_zero: object,
) -> None:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    document[section][field] = invalid_zero
    completed = run_manifest(write_manifest(tmp_path, document))
    assert completed.returncode == 1
    assert expected_error in completed.stderr


def test_duplicate_historical_pull_request_is_rejected(tmp_path: Path) -> None:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    document["historical_inputs"][-1] = copy.deepcopy(document["historical_inputs"][0])
    completed = run_manifest(write_manifest(tmp_path, document))
    assert completed.returncode == 1
    assert "HISTORY_PR_DUPLICATE" in completed.stderr


def test_historical_pull_request_type_confusion_is_rejected(tmp_path: Path) -> None:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    document["historical_inputs"][0]["pull_request"] = 11.0
    completed = run_manifest(write_manifest(tmp_path, document))
    assert completed.returncode == 1
    assert "HISTORY_PR_TYPE_MISMATCH" in completed.stderr


def test_external_requirements_must_be_a_list(tmp_path: Path) -> None:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    requirements = document["missing_external_requirements"]
    document["missing_external_requirements"] = dict.fromkeys(requirements, True)
    completed = run_manifest(write_manifest(tmp_path, document))
    assert completed.returncode == 1
    assert "EXTERNAL_REQUIREMENTS_NOT_LIST" in completed.stderr


def test_external_requirement_elements_must_be_strings(tmp_path: Path) -> None:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    document["missing_external_requirements"][0] = False
    completed = run_manifest(write_manifest(tmp_path, document))
    assert completed.returncode == 1
    assert "EXTERNAL_REQUIREMENT_TYPE_MISMATCH" in completed.stderr


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("recorded_date", "RECORDED_DATE_MISMATCH"),
        ("predecessor_status", "FEATURE009_STATUS_NOT_PASS"),
        ("formal_report_path", "FORMAL_REPORT_PATH_MISMATCH"),
        ("predecessor_report_path", "FEATURE009_REPORT_PATH_MISMATCH"),
        ("claim_type", "QUALIFICATION_CLAIM_FORBIDDEN"),
    ],
)
def test_authoritative_value_and_boolean_types_are_rejected(
    tmp_path: Path,
    mutation: str,
    expected_error: str,
) -> None:
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if mutation == "recorded_date":
        document["recorded_date"] = "1970-01-01"
    elif mutation == "predecessor_status":
        document["predecessor_feature_009"]["status"] = "FAIL"
    elif mutation == "formal_report_path":
        document["formal"]["report_path"] = document["predecessor_feature_009"]["report_path"]
    elif mutation == "predecessor_report_path":
        document["predecessor_feature_009"]["report_path"] = document["formal"]["report_path"]
    elif mutation == "claim_type":
        document["claims"]["feature010_go"] = 0
    else:  # pragma: no cover - keeps the parameter table exhaustive
        raise AssertionError(mutation)
    completed = run_manifest(write_manifest(tmp_path, document))
    assert completed.returncode == 1
    assert expected_error in completed.stderr


@pytest.mark.parametrize("location", ["root", "nested"])
def test_duplicate_json_keys_are_rejected(tmp_path: Path, location: str) -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    if location == "root":
        text = text.replace(
            '  "status": "WORKING_VERSION_READY",',
            '  "status": "QUALIFIED",\n  "status": "WORKING_VERSION_READY",',
            1,
        )
    elif location == "nested":
        text = text.replace(
            '    "branch": "feature/overnight-010-011-requalification",',
            '    "branch": "wrong/branch",\n'
            '    "branch": "feature/overnight-010-011-requalification",',
            1,
        )
    else:  # pragma: no cover - keeps the parameter table exhaustive
        raise AssertionError(location)
    path = tmp_path / "reconciliation-status.json"
    path.write_text(text, encoding="utf-8")
    completed = run_manifest(path)
    assert completed.returncode == 1
    assert "DUPLICATE_JSON_KEY_" in completed.stderr


def test_actual_protected_git_diff_is_rejected() -> None:
    verifier = load_verifier()
    root = SCRIPT.resolve().parents[3]
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    state = expected_branch_state(verifier, root)
    state["protected_paths"] = ["formal/example.tla"]
    with pytest.raises(ValueError, match="PROTECTED_GIT_DIFF_FORBIDDEN"):
        verifier.validate_document(document, root, state, require_branch=True)


def test_actual_out_of_scope_git_diff_is_rejected() -> None:
    verifier = load_verifier()
    root = SCRIPT.resolve().parents[3]
    document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    state = expected_branch_state(verifier, root)
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
    state = expected_branch_state(verifier, root)
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
            expected_branch_state(verifier, root),
            require_branch=True,
        )
