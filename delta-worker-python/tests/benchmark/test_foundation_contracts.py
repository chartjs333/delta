from __future__ import annotations

import copy
import json
import subprocess
from pathlib import Path

import pytest
from deltatorrent.benchmark.canonical import (
    ContractEncodingError,
    canonical_bytes,
    content_id,
    load_json_bytes,
    signing_message,
)
from deltatorrent.benchmark.config import load_foundation_config, validate_foundation_config
from deltatorrent.benchmark.contracts import CanonicalContract, ContractError
from deltatorrent.benchmark.preflight import scan_git_tree, validate_definition_preflight
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from .conftest import (
    arm,
    definition,
    fault_profile,
    metrics,
    network_profile,
    runtime_identity,
    scientific_profile,
)


def _foundation() -> tuple[CanonicalContract, CanonicalContract]:
    runtime = runtime_identity()
    scientific = scientific_profile()
    arms = (
        arm("reference", kind="REFERENCE", topology="FLAT", deployment_profile="EMBEDDED_FFM"),
        arm(
            "candidate",
            kind="DELTAREDUCE",
            topology="HIERARCHICAL",
            deployment_profile="EMBEDDED_FFM",
        ),
    )
    contract = definition(
        runtime,
        scientific,
        arms,
        (network_profile(),),
        (fault_profile(),),
    )
    return runtime, contract


def test_canonical_json_is_utf8_sorted_integer_only_and_locale_independent() -> None:
    left = {"z": 7, "é": "Δ", "a": [True, None, 3]}
    right = {"a": [True, None, 3], "é": "Δ", "z": 7}
    expected = '{"a":[true,null,3],"z":7,"é":"Δ"}'.encode()
    assert canonical_bytes(left) == expected
    assert canonical_bytes(right) == expected
    with pytest.raises(ContractEncodingError, match="JSON_NOT_CANONICALIZABLE"):
        canonical_bytes({"metric": 0.1})


@pytest.mark.parametrize(
    ("value", "code"),
    [
        (b'{"a":1,"a":2}', "DUPLICATE_JSON_KEY"),
        (b"\xef\xbb\xbf{}", "JSON_BOM_FORBIDDEN"),
        (b'{"a":NaN}', "NON_FINITE_NUMBER"),
        (b'{ "a": 1 }', "JSON_BYTES_NOT_CANONICAL"),
        (b"[]", "JSON_ROOT_NOT_OBJECT"),
    ],
)
def test_strict_json_loader_rejects_alternate_or_ambiguous_bytes(value: bytes, code: str) -> None:
    with pytest.raises(ContractEncodingError, match=code):
        load_json_bytes(value)


def test_lone_surrogates_use_the_stable_encoding_error_surface() -> None:
    with pytest.raises(ContractEncodingError, match="JSON_NOT_CANONICALIZABLE"):
        load_json_bytes(b'{"x":"\\ud800"}', require_canonical=False)
    with pytest.raises(ContractEncodingError, match="JSON_NOT_CANONICALIZABLE"):
        canonical_bytes({"x": "\ud800"})


def test_definition_round_trip_identity_and_context_are_stable() -> None:
    _, contract = _foundation()
    assert CanonicalContract.from_bytes(contract.canonical_bytes) == contract
    assert contract.content_id.startswith("sha256:")
    assert signing_message("BENCHMARK_DEFINITION_VOTE", contract.content_id).startswith(
        b"deltareduce.feature010.definition-vote.v1\x00"
    )
    with pytest.raises(ContractEncodingError, match="SIGNING_PURPOSE_INVALID"):
        signing_message("CALLER_SELECTED", contract.content_id)


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (lambda value: value["policy"].__setitem__("adaptive_h", True), "ZERO_TOLERANCE"),
        (lambda value: value["policy"].__setitem__("accept_stale", True), "ZERO_TOLERANCE"),
        (
            lambda value: value["policy"].__setitem__("consensus_arithmetic", "FLOAT"),
            "ZERO_TOLERANCE",
        ),
        (
            lambda value: value["policy"].__setitem__("threshold_override", True),
            "ZERO_TOLERANCE",
        ),
        (
            lambda value: value["policy"].__setitem__("current_authority", "PYTHON"),
            "ZERO_TOLERANCE",
        ),
        (lambda value: value["metrics"][0].pop("threshold"), "METRIC_FIELDS_INVALID"),
        (lambda value: value["metrics"][0].pop("direction"), "METRIC_FIELDS_INVALID"),
        (
            lambda value: value["dependencies"][0].__setitem__(
                "locator", "https://mutable.example/latest"
            ),
            "MUTABLE_DEPENDENCY_FORBIDDEN",
        ),
        (
            lambda value: value["dependencies"][0].__setitem__("license_id", "sha256:" + "f" * 64),
            "DEPENDENCY_LICENSE_NOT_APPROVED",
        ),
        (lambda value: value.__setitem__("H", 1 << 63), "H_INVALID"),
        (lambda value: value.__setitem__("missing_run_policy", "IGNORE"), "MISSING_RUN_POLICY"),
        (lambda value: value.__setitem__("unexpected", 1), "FIELDS_INVALID"),
    ],
)
def test_definition_mutations_fail_closed(mutation: object, code: str) -> None:
    _, contract = _foundation()
    value = copy.deepcopy(contract.to_dict())
    assert callable(mutation)
    mutation(value)
    with pytest.raises(ContractError, match=code):
        CanonicalContract.from_dict(value)


def test_post_attestation_material_change_changes_definition_identity() -> None:
    _, contract = _foundation()
    value = contract.to_dict()
    value["H"] = 17
    changed = CanonicalContract.from_dict(value)
    assert changed.content_id != contract.content_id


def _git(repo: Path, *arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments], cwd=repo, check=True, capture_output=True, text=True
    )
    return process.stdout.strip()


def _preflight_repo(
    tmp_path: Path,
    value: str,
    relative_path: str = "configs/benchmark/foundation.json",
) -> tuple[Path, str, str]:
    repo = tmp_path / "repo"
    config = repo / relative_path
    config.parent.mkdir(parents=True)
    _git(repo.parent, "init", str(repo))
    _git(repo, "config", "user.email", "fixture@example.invalid")
    _git(repo, "config", "user.name", "Fixture")
    config.write_text(value, encoding="utf-8", newline="\n")
    _git(repo, "add", "--", relative_path)
    _git(repo, "commit", "-m", "fixture")
    commit = _git(repo, "rev-parse", "HEAD")
    tree = _git(repo, "rev-parse", "HEAD^{tree}")
    return repo, commit, tree


def test_zero_tolerance_preflight_is_bound_to_exact_source_and_ignores_worktree(
    tmp_path: Path,
) -> None:
    _, contract = _foundation()
    validate_definition_preflight(contract)
    repo, commit, tree = _preflight_repo(tmp_path, contract.canonical_bytes.decode())
    report = scan_git_tree(
        repo,
        source_commit=commit,
        expected_tree=tree,
        include_paths=("configs/benchmark/",),
        required_prefixes=("configs/benchmark/",),
    )
    assert report.status == "PASS"
    assert report.scanned_paths == ("configs/benchmark/foundation.json",)
    (repo / "configs" / "benchmark" / "foundation.json").write_text(
        '{"adaptive_h":true}', encoding="utf-8"
    )
    (repo / "untracked.json").write_text('{"label":"REAL_WAN"}', encoding="utf-8")
    assert (
        scan_git_tree(
            repo,
            source_commit=commit,
            expected_tree=tree,
            include_paths=("configs/benchmark/",),
            required_prefixes=("configs/benchmark/",),
        )
        == report
    )


@pytest.mark.parametrize(
    "fragment",
    [
        '"adaptive_h":true',
        '"accept_stale":true',
        '"consensus_arithmetic":"FLOAT"',
        '"threshold_override":true',
        '"current_authority":"CENTRAL_COORDINATOR"',
        '"label":"REAL_WAN"',
        '"evidence_class":"PRIMARY"',
    ],
)
def test_preflight_detects_every_forbidden_behavior(fragment: str, tmp_path: Path) -> None:
    repo, commit, tree = _preflight_repo(tmp_path, "{" + fragment + "}")
    report = scan_git_tree(
        repo,
        source_commit=commit,
        expected_tree=tree,
        include_paths=("configs/benchmark/",),
        required_prefixes=("configs/benchmark/",),
    )
    assert report.status == "FAIL"
    assert len(report.findings) == 1


def test_preflight_detects_quoted_python_mapping_keys(tmp_path: Path) -> None:
    source = "\n".join(
        (
            "policy = {",
            "    'adaptive_h': True,",
            "    'accept_stale': True,",
            "    'consensus_arithmetic': 'FLOAT',",
            "    'threshold_override': True,",
            "    'current_authority': 'JAVA',",
            "    'label': 'REAL_WAN',",
            "    'evidence_class': 'PRIMARY',",
            "}",
        )
    )
    repo, commit, tree = _preflight_repo(
        tmp_path,
        source,
        "configs/benchmark/foundation.py",
    )
    report = scan_git_tree(
        repo,
        source_commit=commit,
        expected_tree=tree,
        include_paths=("configs/benchmark/",),
        required_prefixes=("configs/benchmark/",),
    )
    assert report.status == "FAIL"
    assert {finding.code for finding in report.findings} == {
        "ADAPTIVE_H_ENABLED",
        "CENTRAL_CURRENT_AUTHORITY",
        "FLOAT_CONSENSUS_FALLBACK",
        "PRIMARY_FIXTURE_PROMOTION",
        "REAL_WAN_RELABEL",
        "STALE_ACCEPTANCE_ENABLED",
        "THRESHOLD_OVERRIDE_ENABLED",
    }


def test_preflight_rejects_unknown_python_policy_literals(tmp_path: Path) -> None:
    source = (
        "policy = {'current_authority': 'CENTRAL_COORDINATOR', 'consensus_arithmetic': 'DOUBLE'}"
    )
    repo, commit, tree = _preflight_repo(
        tmp_path,
        source,
        "configs/benchmark/foundation.py",
    )
    report = scan_git_tree(
        repo,
        source_commit=commit,
        expected_tree=tree,
        include_paths=("configs/benchmark/",),
        required_prefixes=("configs/benchmark/",),
    )
    assert {finding.code for finding in report.findings} == {
        "CENTRAL_CURRENT_AUTHORITY",
        "FLOAT_CONSENSUS_FALLBACK",
    }


def test_preflight_rejects_unknown_python_assignments(tmp_path: Path) -> None:
    source = "current_authority = 'CENTRAL_COORDINATOR'\nconsensus_arithmetic = 'DOUBLE'\n"
    repo, commit, tree = _preflight_repo(
        tmp_path,
        source,
        "configs/benchmark/foundation.py",
    )
    report = scan_git_tree(
        repo,
        source_commit=commit,
        expected_tree=tree,
        include_paths=("configs/benchmark/",),
        required_prefixes=("configs/benchmark/",),
    )
    assert {finding.code for finding in report.findings} == {
        "CENTRAL_CURRENT_AUTHORITY",
        "FLOAT_CONSENSUS_FALLBACK",
    }


def test_all_feature010_schemas_are_valid_json() -> None:
    schema_root = Path(__file__).parents[3] / "delta-protocol" / "schemas" / "010"
    documents = [
        json.loads(path.read_text(encoding="utf-8")) for path in schema_root.glob("*.json")
    ]
    assert len(documents) >= 18
    assert all(
        document.get("$schema") == "https://json-schema.org/draft/2020-12/schema"
        for document in documents
    )
    for document in documents:
        Draft202012Validator.check_schema(document)


def test_raw_artifact_registry_binding_is_explicitly_opaque() -> None:
    root = Path(__file__).parents[3]
    registry = json.loads((root / "delta-protocol" / "registry.json").read_text(encoding="utf-8"))
    media = next(
        item
        for item in registry["media_types"]
        if item["schema_id"] == "SCHEMA-BENCHMARK-RAW-ARTIFACT-010-V1"
    )
    assert media["value"] == "application/octet-stream"
    schema = json.loads(
        (root / "delta-protocol" / "schemas" / "010" / "raw-artifact-v1.json").read_text(
            encoding="utf-8"
        )
    )
    assert schema["not"] == {}
    assert schema["x-deltareduce-payload-kind"] == "opaque-bytes"
    assert schema["x-deltareduce-media-type"] == media["value"]


def _schema_catalog() -> tuple[Path, Registry]:
    schema_root = Path(__file__).parents[3] / "delta-protocol" / "schemas" / "010"
    registry = Registry()
    for path in sorted(schema_root.glob("*.json")):
        document = json.loads(path.read_text(encoding="utf-8"))
        registry = registry.with_resource(document["$id"], Resource.from_contents(document))
    return schema_root, registry


def test_registered_wrapper_schemas_resolve_from_offline_catalog() -> None:
    schema_root, registry = _schema_catalog()
    runtime, benchmark_definition = _foundation()
    samples = (
        ("benchmark-definition-v1.json", benchmark_definition),
        ("metrics-v1.json", metrics()),
        ("runtime-identity-v1.json", runtime),
        ("scientific-profile-v1.json", scientific_profile()),
    )
    for filename, contract in samples:
        wrapper = json.loads((schema_root / filename).read_text(encoding="utf-8"))
        validator = Draft202012Validator(wrapper, registry=registry)
        assert not list(validator.iter_errors(contract.to_dict()))
        invalid = contract.to_dict()
        invalid.pop("authority_scope")
        assert list(validator.iter_errors(invalid))


def test_frozen_foundation_config_is_canonical_joined_and_schema_valid() -> None:
    root = Path(__file__).parents[3]
    path = root / "configs" / "benchmark" / "foundation-v1.json"
    frozen = load_foundation_config(path)
    assert frozen.definition.to_dict()["runtime_identity_id"] == frozen.runtime_identity.content_id
    assert frozen.document["primary_observation_count"] == 0
    assert frozen.document["feature010_go"] is False
    mutable_view = frozen.document
    mutable_view["feature010_go"] = True
    assert frozen.document["feature010_go"] is False
    assert frozen.content_id == content_id(canonical_bytes(frozen.document))
    schema_root, registry = _schema_catalog()
    schema = json.loads((schema_root / "foundation-config-v1.json").read_text(encoding="utf-8"))
    assert not list(Draft202012Validator(schema, registry=registry).iter_errors(frozen.document))

    mutated = copy.deepcopy(frozen.document)
    mutated["runtime_constraints"]["fast_math"] = True
    with pytest.raises(ContractError, match="RUNTIME_CONSTRAINTS_INVALID"):
        validate_foundation_config(mutated, raw_bytes=canonical_bytes(mutated))
    with pytest.raises(ContractError, match="FOUNDATION_CONFIG_BYTES_MISMATCH"):
        validate_foundation_config(frozen.document, raw_bytes=b"{}")


def test_metrics_schema_and_contract_reject_incomplete_or_duplicate_phases() -> None:
    schema_root, registry = _schema_catalog()
    wrapper = json.loads((schema_root / "metrics-v1.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(wrapper, registry=registry)
    for mutation in ("empty_gpu", "duplicate_phases"):
        document = metrics().to_dict()
        if mutation == "empty_gpu":
            document["gpu_metrics"] = {}
        else:
            for phase in document["phase_timings"]:
                phase["phase"] = "compute"
        assert list(validator.iter_errors(document))
        with pytest.raises(ContractError):
            CanonicalContract.from_dict(document)
    contradictory = metrics().to_dict()
    contradictory["resource_metrics"]["p2p_bytes"] = 999
    with pytest.raises(ContractError, match="METRICS_P2P_BYTES_MISMATCH"):
        CanonicalContract.from_dict(contradictory)


def test_python_definition_and_science_instances_match_json_schema() -> None:
    schema_path = (
        Path(__file__).parents[3]
        / "delta-protocol"
        / "schemas"
        / "010"
        / "foundation-contracts-v1.json"
    )
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    runtime, benchmark_definition = _foundation()
    science = scientific_profile()
    for definition_name, contract in (
        ("RuntimeIdentity", runtime),
        ("ScientificProfile", science),
        ("BenchmarkDefinition", benchmark_definition),
    ):
        validator = Draft202012Validator(
            {
                "$schema": "https://json-schema.org/draft/2020-12/schema",
                "$defs": schema["$defs"],
                "$ref": f"#/$defs/{definition_name}",
            }
        )
        assert not list(validator.iter_errors(contract.to_dict()))
