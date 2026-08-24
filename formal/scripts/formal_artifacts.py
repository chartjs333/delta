#!/usr/bin/env python3
"""Canonical JSON, schema, compatibility and report decision helpers.

This module deliberately depends only on the Python standard library and the
checked-in formal contracts.  Production DeltaReduce packages are not imported.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[2]
TRACE_SCHEMA = Path("formal/schemas/formal-trace.schema.json")
REPORT_SCHEMA = Path("formal/schemas/formal-verification-report.schema.json")
ID_REGISTRY = Path("formal/reports/formal-id-registry.json")
SEMANTICS_DOMAIN = "deltareduce.formal-semantics.v1"

TOOLCHAIN_IDS = {
    "TOOLCHAIN-CONTAINER",
    "TOOLCHAIN-JRE",
    "TOOLCHAIN-LEAN",
    "TOOLCHAIN-TLA",
}
MUTANT_IDS = {
    "MUT-CURRENT-WITHOUT-APPLYQC",
    "MUT-DUPLICATE-COMMITMENT",
    "MUT-EARLY-SEED",
    "MUT-INCOMPLETE-AGGREGATE",
    "MUT-MISSING-APC-PARENT",
    "MUT-MISSING-DURABLE-VOTE",
    "MUT-MISSING-SHARD-PARENT",
    "MUT-MUTABLE-ISC",
    "MUT-PARTIAL-PUBLICATION",
    "MUT-UNCHECKED-OVERFLOW",
}
REQUIREMENT_IDS = {f"FR-{number:03d}" for number in range(1, 47)}
REVIEW_SCOPE = {"MODEL", "LIVENESS", "PROOFS", "COVERAGE"}


class CanonicalJsonError(ValueError):
    """Input cannot be represented by the DeltaReduce canonical JSON profile."""


class SchemaValidationError(ValueError):
    """JSON instance does not satisfy a checked-in schema."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


def _reject_float(value: str) -> NoReturn:
    raise CanonicalJsonError(f"floating-point JSON number is forbidden: {value}")


def _reject_constant(value: str) -> NoReturn:
    raise CanonicalJsonError(f"non-finite JSON number is forbidden: {value}")


def _object_without_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise CanonicalJsonError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def load_json_strict(path: Path) -> Any:
    """Load UTF-8 JSON while rejecting duplicates, floats and non-finite values."""

    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise CanonicalJsonError(f"cannot read UTF-8 JSON {path}: {error}") from error
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_without_duplicates,
            parse_float=_reject_float,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as error:
        raise CanonicalJsonError(f"invalid JSON {path}: {error}") from error
    _validate_canonical_value(value, "$")
    return value


def _validate_canonical_value(value: Any, location: str) -> None:
    if value is None or isinstance(value, (bool, int)):
        return
    if isinstance(value, float):
        raise CanonicalJsonError(f"{location}: floating-point values are forbidden")
    if isinstance(value, str):
        if unicodedata.normalize("NFC", value) != value:
            raise CanonicalJsonError(f"{location}: strings must be NFC-normalized")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_canonical_value(item, f"{location}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalJsonError(f"{location}: object keys must be strings")
            _validate_canonical_value(key, f"{location}.<key>")
            _validate_canonical_value(item, f"{location}.{key}")
        return
    raise CanonicalJsonError(f"{location}: unsupported value type {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    """Encode the project JSON profile: NFC strings, integers, sorted keys, no space."""

    _validate_canonical_value(value, "$")
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def write_canonical_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json_bytes(value))


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_equal(left: Any, right: Any) -> bool:
    return type(left) is type(right) and left == right


def _schema_type_matches(value: Any, expected: str) -> bool:
    if expected == "null":
        return value is None
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "string":
        return isinstance(value, str)
    if expected == "array":
        return isinstance(value, list)
    if expected == "object":
        return isinstance(value, dict)
    raise ValueError(f"unsupported schema type: {expected}")


def _resolve_local_ref(root_schema: dict[str, Any], reference: str) -> dict[str, Any]:
    if not reference.startswith("#/"):
        raise ValueError(f"only local schema references are supported: {reference}")
    current: Any = root_schema
    for encoded in reference[2:].split("/"):
        token = encoded.replace("~1", "/").replace("~0", "~")
        if not isinstance(current, dict) or token not in current:
            raise ValueError(f"unresolved schema reference: {reference}")
        current = current[token]
    if not isinstance(current, dict):
        raise ValueError(f"schema reference does not name an object: {reference}")
    return current


def validate_json_schema(instance: Any, schema: dict[str, Any]) -> None:
    """Validate the deliberately small JSON Schema subset used by formal contracts."""

    errors: list[str] = []

    def check(value: Any, rule: dict[str, Any], location: str) -> None:
        if "$ref" in rule:
            check(value, _resolve_local_ref(schema, rule["$ref"]), location)
            return

        expected_type = rule.get("type")
        if expected_type is not None:
            expected_types = [expected_type] if isinstance(expected_type, str) else expected_type
            if not any(_schema_type_matches(value, item) for item in expected_types):
                errors.append(
                    f"{location}: expected type {expected_types}, got {type(value).__name__}"
                )
                return

        if "const" in rule and not _json_equal(value, rule["const"]):
            errors.append(f"{location}: value does not equal const {rule['const']!r}")
        if "enum" in rule and not any(_json_equal(value, item) for item in rule["enum"]):
            errors.append(f"{location}: value is not in the allowed enum")

        if isinstance(value, str):
            if len(value) < int(rule.get("minLength", 0)):
                errors.append(f"{location}: string is shorter than minLength")
            if "maxLength" in rule and len(value) > int(rule["maxLength"]):
                errors.append(f"{location}: string is longer than maxLength")
            if "pattern" in rule and re.search(rule["pattern"], value) is None:
                errors.append(f"{location}: string does not match {rule['pattern']}")

        if isinstance(value, int) and not isinstance(value, bool):
            if "minimum" in rule and value < int(rule["minimum"]):
                errors.append(f"{location}: integer is below minimum {rule['minimum']}")

        if isinstance(value, list):
            if len(value) < int(rule.get("minItems", 0)):
                errors.append(f"{location}: array is shorter than minItems")
            if "maxItems" in rule and len(value) > int(rule["maxItems"]):
                errors.append(f"{location}: array is longer than maxItems")
            if rule.get("uniqueItems"):
                encoded = [canonical_json_bytes(item) for item in value]
                if len(encoded) != len(set(encoded)):
                    errors.append(f"{location}: array items are not unique")
            if "items" in rule:
                for index, item in enumerate(value):
                    check(item, rule["items"], f"{location}[{index}]")

        if isinstance(value, dict):
            required = rule.get("required", [])
            for key in required:
                if key not in value:
                    errors.append(f"{location}: missing required property {key}")
            properties = rule.get("properties", {})
            if rule.get("additionalProperties") is False:
                for key in value:
                    if key not in properties:
                        errors.append(f"{location}: unexpected property {key}")
            for key, property_rule in properties.items():
                if key in value:
                    check(value[key], property_rule, f"{location}.{key}")

    check(instance, schema, "$")
    if errors:
        raise SchemaValidationError(errors)


def safe_repo_path(root: Path, relative: str) -> Path:
    if "\\" in relative:
        raise ValueError(f"repository path contains a backslash: {relative}")
    pure = PurePosixPath(relative)
    if pure.is_absolute() or not pure.parts or ".." in pure.parts:
        raise ValueError(f"unsafe repository-relative path: {relative}")
    resolved_root = root.resolve()
    resolved = (resolved_root / Path(*pure.parts)).resolve()
    if not resolved.is_relative_to(resolved_root):
        raise ValueError(f"path escapes repository root: {relative}")
    return resolved


def _artifact_entry(root: Path, path: Path, kind: str) -> dict[str, str]:
    return {
        "kind": kind,
        "path": path.relative_to(root).as_posix(),
        "sha256": sha256_file(path),
    }


def discover_semantic_artifacts(root: Path) -> list[dict[str, str]]:
    """Discover only protocol modules/proofs and the public trace contract."""

    entries: list[dict[str, str]] = []
    tla_root = root / "formal" / "tla"
    if tla_root.is_dir():
        for path in tla_root.rglob("*.tla"):
            relative_parts = path.relative_to(tla_root).parts
            if "mutants" not in relative_parts:
                entries.append(_artifact_entry(root, path, "tla_module"))

    proof_root = root / "formal" / "proofs"
    proof_entry = proof_root / "DeltaReduce.lean"
    if proof_entry.is_file():
        entries.append(_artifact_entry(root, proof_entry, "lean_theorem"))
    theorem_root = proof_root / "DeltaReduce"
    if theorem_root.is_dir():
        for path in theorem_root.rglob("*.lean"):
            entries.append(_artifact_entry(root, path, "lean_theorem"))

    trace_schema = root / TRACE_SCHEMA
    if trace_schema.is_file():
        entries.append(_artifact_entry(root, trace_schema, "trace_schema"))
    return sorted(entries, key=lambda item: (item["path"], item["kind"]))


def derive_formal_semantics_id(version: str, artifacts: list[dict[str, str]]) -> str:
    normalized = sorted(copy.deepcopy(artifacts), key=lambda item: (item["path"], item["kind"]))
    paths = [item["path"] for item in normalized]
    if len(paths) != len(set(paths)):
        raise ValueError("semantic artifact paths must be unique")
    payload = {
        "artifacts": normalized,
        "domain": SEMANTICS_DOMAIN,
        "formal_semantics_version": version,
    }
    return f"sha256:{sha256_bytes(canonical_json_bytes(payload))}"


def validate_contract_registry(root: Path) -> None:
    trace_schema = load_json_strict(root / TRACE_SCHEMA)
    report_schema = load_json_strict(root / REPORT_SCHEMA)
    registry = load_json_strict(root / ID_REGISTRY)

    action_enum = set(trace_schema["$defs"]["event"]["properties"]["action_id"]["enum"])
    registered_actions = {item["id"] for item in registry["actions"]}
    if action_enum != registered_actions:
        raise ValueError("trace schema action enum differs from formal ID registry")

    report_required = set(report_schema["required"])
    registered_fields = set(registry["report_fields"])
    if report_required != registered_fields:
        raise ValueError("report schema required fields differ from formal ID registry")


def validate_trace_document(trace: dict[str, Any], root: Path) -> None:
    """Validate trace shape plus the state-root adjacency required by refinement."""

    schema = load_json_strict(root / TRACE_SCHEMA)
    validate_json_schema(trace, schema)
    validate_contract_registry(root)
    events = trace["events"]
    expected_prior = trace["initial_state_root"]
    for index, event in enumerate(events):
        if event["prior_state_root"] != expected_prior:
            raise ValueError(f"trace event {index} does not continue the prior state root")
        expected_prior = event["next_state_root"]
    if expected_prior != trace["terminal_state_root"]:
        raise ValueError("terminal_state_root differs from the last projected state")


def _reason(reasons: set[str], prefix: str, identifier: str | None = None) -> None:
    reasons.add(prefix if identifier is None else f"{prefix}:{identifier}")


def _verified_evidence(report: dict[str, Any], root: Path, reasons: set[str]) -> set[str]:
    graph = report["evidence_graph"]
    nodes: dict[str, dict[str, Any]] = {}
    for node in graph["nodes"]:
        identifier = node["id"]
        if identifier in nodes:
            _reason(reasons, "DUPLICATE_EVIDENCE_ID", identifier)
            continue
        nodes[identifier] = node
        try:
            path = safe_repo_path(root, node["path"])
            if not path.is_file() or sha256_file(path) != node["sha256"]:
                _reason(reasons, "INVALID_EVIDENCE", identifier)
        except (OSError, ValueError):
            _reason(reasons, "INVALID_EVIDENCE", identifier)

    for edge in graph["edges"]:
        if edge["from"] not in nodes or edge["to"] not in nodes:
            _reason(reasons, "INVALID_EVIDENCE_EDGE", f"{edge['from']}->{edge['to']}")
    return {
        identifier
        for identifier in nodes
        if f"INVALID_EVIDENCE:{identifier}" not in reasons
        and f"DUPLICATE_EVIDENCE_ID:{identifier}" not in reasons
    }


def _check_source_tree(report: dict[str, Any], root: Path, reasons: set[str]) -> None:
    source = report["source_tree"]
    if not source["clean"]:
        _reason(reasons, "SOURCE_TREE_NOT_CLEAN")

    declared = source["semantic_artifacts"]
    discovered = discover_semantic_artifacts(root)
    if declared != sorted(declared, key=lambda item: (item["path"], item["kind"])):
        _reason(reasons, "SEMANTIC_ARTIFACTS_NOT_SORTED")
    if declared != discovered:
        _reason(reasons, "SEMANTIC_ARTIFACT_SET_MISMATCH")
    kinds = {item["kind"] for item in declared}
    if kinds != {"tla_module", "lean_theorem", "trace_schema"}:
        _reason(reasons, "SEMANTIC_ARTIFACT_SET_INCOMPLETE")
    try:
        expected_id = derive_formal_semantics_id(report["formal_semantics_version"], declared)
    except (CanonicalJsonError, KeyError, TypeError, ValueError):
        _reason(reasons, "SEMANTIC_ID_UNDERIVABLE")
    else:
        if report["formal_semantics_id"] != expected_id:
            _reason(reasons, "SEMANTIC_ID_MISMATCH")

    try:
        manifest_path = safe_repo_path(root, source["manifest_path"])
        if not manifest_path.is_file() or sha256_file(manifest_path) != source["tree_sha256"]:
            raise ValueError("manifest content ID mismatch")
        manifest = load_json_strict(manifest_path)
        if set(manifest) != {"schema_version", "commit", "files"}:
            raise ValueError("manifest shape mismatch")
        if manifest["schema_version"] != "1.0.0" or manifest["commit"] != source["commit"]:
            raise ValueError("manifest version/commit mismatch")
        files = manifest["files"]
        if not isinstance(files, list):
            raise ValueError("manifest files must be an array")
        paths = [item["path"] for item in files]
        if paths != sorted(paths) or len(paths) != len(set(paths)):
            raise ValueError("manifest paths must be sorted and unique")
        for item in files:
            if set(item) != {"path", "sha256"}:
                raise ValueError("manifest entry shape mismatch")
            path = safe_repo_path(root, item["path"])
            if not path.is_file() or sha256_file(path) != item["sha256"]:
                raise ValueError(f"manifest file mismatch: {item['path']}")
        mandatory_paths = {item["path"] for item in declared} | {report["baseline_inputs"]["path"]}
        if not mandatory_paths.issubset(set(paths)):
            raise ValueError("manifest omits a mandatory semantic/baseline input")
    except (CanonicalJsonError, KeyError, OSError, TypeError, ValueError):
        _reason(reasons, "SOURCE_TREE_MANIFEST_INVALID")


def _check_baseline(report: dict[str, Any], root: Path, reasons: set[str]) -> None:
    baseline = report["baseline_inputs"]
    if not baseline["verified"]:
        _reason(reasons, "BASELINE_INPUTS_UNVERIFIED")
    try:
        path = safe_repo_path(root, baseline["path"])
        if not path.is_file() or sha256_file(path) != baseline["sha256"]:
            raise ValueError("baseline content ID mismatch")
        payload = load_json_strict(path)
        if payload.get("input_bundle_sha256") != baseline["input_bundle_sha256"]:
            raise ValueError("baseline bundle ID mismatch")
    except (CanonicalJsonError, OSError, ValueError):
        _reason(reasons, "BASELINE_INPUTS_INVALID")


def _check_expected_records(
    records: list[dict[str, Any]],
    expected_ids: set[str],
    category: str,
    valid_evidence: set[str],
    reasons: set[str],
) -> None:
    by_id: dict[str, dict[str, Any]] = {}
    for record in records:
        identifier = record["id"]
        if identifier in by_id:
            _reason(reasons, f"DUPLICATE_{category}", identifier)
        else:
            by_id[identifier] = record
        if record["mandatory"] and identifier not in expected_ids:
            _reason(reasons, f"UNREGISTERED_{category}", identifier)

    for identifier in expected_ids:
        record = by_id.get(identifier)
        if record is None:
            _reason(reasons, f"MISSING_{category}", identifier)
            continue
        evidence_id = record["evidence_id"]
        if (
            not record["mandatory"]
            or record["status"] != "PASS"
            or not record["verified"]
            or evidence_id not in valid_evidence
        ):
            _reason(reasons, f"FAILED_{category}", identifier)


def determine_report_decision(
    report: dict[str, Any], root: Path, registry: dict[str, Any]
) -> tuple[str, list[str]]:
    """Compute GO/NO_GO exclusively from checked evidence and frozen registries."""

    reasons: set[str] = set()
    _check_source_tree(report, root, reasons)
    _check_baseline(report, root, reasons)
    valid_evidence = _verified_evidence(report, root, reasons)

    _check_expected_records(
        report["toolchains"], TOOLCHAIN_IDS, "TOOLCHAIN", valid_evidence, reasons
    )
    config_ids = {item["id"] for item in registry["configs"]}
    _check_expected_records(
        report["model_checks"], config_ids, "MODEL_CHECK", valid_evidence, reasons
    )
    property_ids = {
        item["id"] for item in registry["invariants"] + registry["temporal_properties"]
    }
    for record in report["model_checks"]:
        properties = record["properties"]
        numeric_results = (
            record["states"],
            record["distinct_states"],
            record["diameter"],
            record["terminal_states"],
        )
        if (
            not properties
            or any(
                item["id"] not in property_ids or item["status"] != "PASS"
                for item in properties
            )
            or any(value is None for value in numeric_results)
            or (
                record["states"] is not None
                and record["distinct_states"] is not None
                and record["distinct_states"] > record["states"]
            )
        ):
            _reason(reasons, "INVALID_MODEL_RESULT", record["id"])
    theorem_ids = {item["id"] for item in registry["proof_obligations"]}
    _check_expected_records(
        report["theorem_checks"], theorem_ids, "THEOREM_CHECK", valid_evidence, reasons
    )
    declared_proof_sources = {
        item["path"]
        for item in report["source_tree"]["semantic_artifacts"]
        if item["kind"] == "lean_theorem"
    }
    for record in report["theorem_checks"]:
        if record["source"] not in declared_proof_sources:
            _reason(reasons, "INVALID_THEOREM_SOURCE", record["id"])
    _check_expected_records(
        report["mutant_checks"], MUTANT_IDS, "MUTANT_CHECK", valid_evidence, reasons
    )
    for record in report["mutant_checks"]:
        if record["expected_property_id"] not in property_ids:
            _reason(reasons, "INVALID_MUTANT_PROPERTY", record["id"])
    _check_expected_records(
        report["refinement_checks"],
        {"REFINEMENT-SUITE"},
        "REFINEMENT_CHECK",
        valid_evidence,
        reasons,
    )
    for record in report["refinement_checks"]:
        if record["id"] == "REFINEMENT-SUITE" and (
            record["legal_fixture_count"] < 5 or record["illegal_fixture_count"] < 14
        ):
            _reason(reasons, "INSUFFICIENT_REFINEMENT_FIXTURES")

    coverage_records = report["coverage"]["requirements"]
    coverage_by_id: dict[str, dict[str, Any]] = {}
    for record in coverage_records:
        identifier = record["id"]
        if identifier in coverage_by_id:
            _reason(reasons, "DUPLICATE_COVERAGE", identifier)
        coverage_by_id[identifier] = record
        if identifier not in REQUIREMENT_IDS:
            _reason(reasons, "UNREGISTERED_COVERAGE", identifier)
    for identifier in REQUIREMENT_IDS:
        record = coverage_by_id.get(identifier)
        if record is None:
            _reason(reasons, "MISSING_COVERAGE", identifier)
        elif record["status"] != "PASS" or record["evidence_id"] not in valid_evidence:
            _reason(reasons, "FAILED_COVERAGE", identifier)
    if report["coverage"]["unresolved"]:
        _reason(reasons, "UNRESOLVED_COVERAGE")

    passing_reviewers: set[str] = set()
    for review in report["review_attestations"]:
        if (
            review["independent"]
            and review["status"] == "PASS"
            and set(review["scope"]) == REVIEW_SCOPE
            and review["evidence_id"] in valid_evidence
        ):
            passing_reviewers.add(review["reviewer_id"])
    if len(passing_reviewers) < 2:
        _reason(reasons, "INSUFFICIENT_INDEPENDENT_REVIEWS")

    if not report["assumptions"]:
        _reason(reasons, "ASSUMPTIONS_MISSING")
    if not report["abstractions"]:
        _reason(reasons, "ABSTRACTIONS_MISSING")
    if not report["limitations"]:
        _reason(reasons, "LIMITATIONS_MISSING")

    ordered = sorted(reasons)
    return ("GO" if not ordered else "NO_GO", ordered)


def finalize_report(report: dict[str, Any], root: Path, registry: dict[str, Any]) -> dict[str, Any]:
    """Populate compatibility and deterministic decision fields in a report draft."""

    finalized = copy.deepcopy(report)
    artifacts = discover_semantic_artifacts(root)
    finalized["source_tree"]["semantic_artifacts"] = artifacts
    finalized["formal_semantics_id"] = derive_formal_semantics_id(
        finalized["formal_semantics_version"], artifacts
    )
    decision, reasons = determine_report_decision(finalized, root, registry)
    finalized["decision"] = decision
    finalized["decision_reasons"] = reasons
    return finalized


def verify_report_document(
    report_path: Path, root: Path, *, require_go: bool = False
) -> dict[str, Any]:
    """Verify schema, canonical bytes, evidence graph, compatibility and decision."""

    errors: list[str] = []
    report = load_json_strict(report_path)
    schema = load_json_strict(root / REPORT_SCHEMA)
    registry = load_json_strict(root / ID_REGISTRY)
    validate_json_schema(report, schema)
    validate_contract_registry(root)

    raw = report_path.read_bytes()
    canonical = canonical_json_bytes(report)
    if raw != canonical:
        errors.append("report bytes are not canonical JSON")

    computed_decision, computed_reasons = determine_report_decision(report, root, registry)
    if report["decision"] != computed_decision:
        errors.append(
            f"reported decision {report['decision']} differs from computed {computed_decision}"
        )
    if report["decision_reasons"] != computed_reasons:
        errors.append("decision_reasons differ from deterministic reasons")
    if require_go and computed_decision != "GO":
        errors.append("Formal GO required but deterministic decision is NO_GO")

    return {
        "schema_version": "1.0.0",
        "status": "PASS" if not errors else "FAIL",
        "decision": computed_decision,
        "formal_semantics_id": report["formal_semantics_id"],
        "report_sha256": sha256_bytes(canonical),
        "errors": errors,
    }
