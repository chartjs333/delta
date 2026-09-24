#!/usr/bin/env python3
"""Canonical JSON, schema, compatibility and report decision helpers.

This module deliberately depends only on the Python standard library and the
checked-in formal contracts.  Production DeltaReduce packages are not imported.
"""

from __future__ import annotations

import ast
import copy
import hashlib
import json
import re
import subprocess
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
    "MUT-ARITHMETIC-PREFIX-GUARD",
    "MUT-ARITHMETIC-PRODUCT-GUARD",
    "MUT-ARITHMETIC-CONVERSION-GUARD",
    "MUT-DOMAIN-MIXTURE-WEIGHTS",
    "MUT-DOMAIN-ROUNDING",
    "MUT-PARAMETER-STALE-CURRENT",
    "MUT-PARAMETER-STALE-CURRENT-RECOVERY",
    "MUT-APPLY-STALE-CURRENT",
    "MUT-APPLY-STALE-CURRENT-RECOVERY",
    "MUT-PARAMETER-ARITHMETIC-BINDING",
    "MUT-PARAMETER-MODEL-BINDING",
    "MUT-APPLY-OPTIMIZER-BINDING",
    "MUT-APPLY-ARITHMETIC-BINDING",
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
    "MUT-PARAMETER-PERSISTENCE-SEQUENCE",
    "MUT-APPLY-PERSISTENCE-SEQUENCE",
    "MUT-PARAMETER-PERSISTENCE-RECOVERY",
    "MUT-APPLY-PERSISTENCE-RECOVERY",
}
GENERATED_REPORT_OUTPUTS = {
    "formal/reports/clean-offline-reproduction.json",
    "formal/reports/cross-artifact-analysis.json",
    "formal/reports/executed-coverage.md",
    "formal/reports/final-constitution-check.md",
    "formal/reports/formal-verification-report.json",
    "formal/reports/formal-semantics.json",
    "formal/reports/lean-proof-report.json",
    "formal/reports/liveness-countercheck.json",
    "formal/reports/mutant-evidence.json",
    "formal/reports/refinement-evidence.json",
    "formal/reports/reproducibility-evidence.json",
    "formal/reports/source-tree-manifest.json",
    "formal/reports/tlc-evidence.json",
    "formal/reports/toolchain-evidence.json",
    *{f"formal/fixtures/counterexamples/{identifier.lower()}.json" for identifier in MUTANT_IDS},
}
GENERATED_REPORT_OUTPUT_GLOBS = ("formal/reports/reviews/*.json",)
REQUIREMENT_IDS = {f"FR-{number:03d}" for number in range(1, 47)}
REVIEW_SCOPE = {"MODEL", "LIVENESS", "PROOFS", "COVERAGE"}
REVIEW_ATTESTATION_KEYS = {
    "formal_semantics_id",
    "independent",
    "reviewed_commit",
    "reviewer_id",
    "scope",
    "status",
}
REPRODUCTION_COMMANDS = (
    ("phase0", ("python3", "formal/scripts/verify_phase0.py")),
    (
        "contracts",
        (
            "python3",
            "-m",
            "unittest",
            "discover",
            "-s",
            "formal/tests",
            "-v",
        ),
    ),
    ("parse", ("python3", "formal/scripts/run_formal_gate.py", "parse")),
    ("safety", ("python3", "formal/scripts/run_formal_gate.py", "safety")),
    ("liveness", ("python3", "formal/scripts/run_formal_gate.py", "liveness")),
    ("proofs", ("python3", "formal/scripts/run_formal_gate.py", "proofs")),
    (
        "toolchain",
        ("python3", "formal/scripts/collect_toolchain_evidence.py"),
    ),
    ("mutants", ("python3", "formal/scripts/run_formal_gate.py", "mutants")),
    (
        "refinement",
        ("python3", "formal/scripts/run_formal_gate.py", "refinement"),
    ),
    (
        "tlc-evidence",
        ("python3", "formal/scripts/collect_tlc_evidence.py"),
    ),
    (
        "cross-artifact",
        ("python3", "formal/scripts/analyze_formal_consistency.py"),
    ),
)
REPRODUCTION_CHECK_IDS = tuple(identifier for identifier, _ in REPRODUCTION_COMMANDS)
REPRODUCTION_RESULT_KINDS = {
    "phase0": "phase0-summary",
    "contracts": "unittest-summary",
    "parse": "sany-module-set",
    "safety": "tlc-model-set",
    "liveness": "tlc-model-set",
    "proofs": "artifact-set",
    "toolchain": "artifact-set",
    "mutants": "artifact-set",
    "refinement": "artifact-set",
    "tlc-evidence": "artifact-set",
    "cross-artifact": "artifact-set",
}
REPRODUCTION_RECEIPT_PROFILE = "deltareduce.clean-offline-check.v1"
REPRODUCTION_TLC_IDS = {
    "safety": (
        "CFG-HETEROGENEOUS-POSITIVE",
        "CFG-HETEROGENEOUS-PREFIX",
        "CFG-HETEROGENEOUS-PRODUCT",
        "CFG-HETEROGENEOUS-CONVERSION",
        "CFG-CONFIG-QC",
        "CFG-SAFETY-F1",
        "CFG-VOTE-CRASH-RECOVERY",
        "CFG-VOTE-LIFECYCLE-CONFIG",
        "CFG-VOTE-LIFECYCLE-ISC",
        "CFG-VOTE-LIFECYCLE-EC",
        "CFG-VOTE-LIFECYCLE-APC",
        "CFG-VOTE-LIFECYCLE-PARAMETER",
        "CFG-VOTE-LIFECYCLE-AGGREGATE",
        "CFG-VOTE-LIFECYCLE-APPLY",
        "CFG-VOTE-LIFECYCLE-VIEW",
        "CFG-VOTE-LIFECYCLE-ABORT",
        "CFG-TICKET-LEASE-AVAILABILITY",
        "CFG-AVAILABILITY-LOSS-REPAIR",
        "CFG-INPUT-FREEZE-SEED",
        "CFG-CERTIFICATE-FRANKENSTEIN",
        "CFG-SPLIT-BRAIN-PARTITION",
        "CFG-ARITHMETIC-BOUNDARY",
        "CFG-APPLY-RECOVERY",
        "CFG-NATIVE-ARITHMETIC-BINDING",
        "CFG-CURRENT-BINDING",
        "CFG-CURRENT-BINDING-RECOVERY",
        "CFG-PERSISTENCE-PARAMETER",
        "CFG-PERSISTENCE-APPLY",
    ),
    "liveness": (
        "CFG-LIVENESS-CONFIG-QC",
        "CFG-LIVENESS-ISC",
        "CFG-LIVENESS-PLAN",
        "CFG-LIVENESS-EVENTUAL-SYNCHRONY",
        "CFG-LIVENESS-VIEW-CHANGE",
        "CFG-LIVENESS-ABORT-QC",
        "CFG-NATIVE-ARITHMETIC-LIVENESS",
    ),
}
REPRODUCTION_ARTIFACT_PATHS = {
    "proofs": ("formal/reports/lean-proof-report.json",),
    "toolchain": ("formal/reports/toolchain-evidence.json",),
    "mutants": (
        "formal/reports/mutant-evidence.json",
        *tuple(
            f"formal/fixtures/counterexamples/{identifier.lower()}.json"
            for identifier in sorted(MUTANT_IDS)
        ),
    ),
    "refinement": ("formal/reports/refinement-evidence.json",),
    "tlc-evidence": (
        "formal/reports/executed-coverage.md",
        "formal/reports/tlc-evidence.json",
    ),
    "cross-artifact": (
        "formal/reports/cross-artifact-analysis.json",
        "formal/reports/final-constitution-check.md",
    ),
}


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


def git_output(root: Path, *arguments: str) -> str:
    """Run a read-only Git query against one exact checkout."""

    try:
        completed = subprocess.run(
            [
                "git",
                "-c",
                f"safe.directory={root.resolve()}",
                "-C",
                str(root.resolve()),
                *arguments,
            ],
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError(f"Git query failed: {error}") from error
    if completed.returncode != 0:
        raise ValueError(f"Git query failed: {completed.stderr.strip()}")
    return completed.stdout.rstrip("\n")


def git_revision(root: Path, revision: str) -> str:
    """Resolve an exact Git object without consulting the network."""

    value = git_output(root, "rev-parse", "--verify", revision).strip()
    if re.fullmatch(r"[0-9a-f]{40}", value) is None:
        raise ValueError(f"cannot resolve Git revision {revision}")
    return value


def is_generated_report_output(path: str) -> bool:
    normalized = path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    return normalized in GENERATED_REPORT_OUTPUTS or (
        pure.parent == PurePosixPath("formal/reports/reviews")
        and pure.suffix == ".json"
        and bool(pure.stem)
    )


def source_commit_from_history(root: Path) -> str:
    """Return the newest commit that changes bytes outside generated evidence."""

    if git_output(root, "rev-parse", "--is-shallow-repository").strip() != "false":
        raise ValueError("full Git history is required for source/evidence separation")
    exclusions = [f":(exclude){path}" for path in sorted(GENERATED_REPORT_OUTPUTS)]
    exclusions.extend(f":(exclude,glob){pattern}" for pattern in GENERATED_REPORT_OUTPUT_GLOBS)
    commit = git_output(root, "log", "-1", "--format=%H", "--", ".", *exclusions).strip()
    if re.fullmatch(r"[0-9a-f]{40}", commit) is None:
        raise ValueError("cannot identify the latest non-evidence source commit")
    return commit


def semantic_text_sha256(path: Path) -> str:
    """Hash a semantic text artifact using the repository's canonical LF bytes."""

    canonical = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    return sha256_bytes(canonical)


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


def review_attestation_matches(
    payload: Any,
    *,
    reviewed_commit: str,
    formal_semantics_id: str,
    projection: dict[str, Any] | None = None,
) -> bool:
    """Validate a review payload and, when supplied, its report projection."""

    if not isinstance(payload, dict) or set(payload) != REVIEW_ATTESTATION_KEYS:
        return False
    if (
        payload["reviewed_commit"] != reviewed_commit
        or payload["formal_semantics_id"] != formal_semantics_id
        or not isinstance(payload["reviewer_id"], str)
        or not payload["reviewer_id"]
        or type(payload["independent"]) is not bool
        or payload["status"] not in {"PASS", "FAIL"}
        or payload["scope"] != sorted(REVIEW_SCOPE)
    ):
        return False
    if projection is None:
        return True
    expected_projection = {
        "reviewer_id": payload["reviewer_id"],
        "independent": payload["independent"],
        "status": payload["status"],
        "scope": payload["scope"],
        "evidence_id": projection.get("evidence_id"),
    }
    return projection == expected_projection


def reproduction_check_sha256(check: dict[str, Any], reproduction: dict[str, Any]) -> str:
    """Hash a source-bound, independently recomputable clean-check receipt."""

    receipt = {
        "profile": REPRODUCTION_RECEIPT_PROFILE,
        "id": check["id"],
        "command": check["command"],
        "exit_code": check["exit_code"],
        "status": check["status"],
        "result": check["result"],
        "source_commit": reproduction["source_commit"],
        "source_tree": reproduction["source_tree"],
        "source_manifest_sha256": reproduction["source_manifest_sha256"],
        "formal_semantics_id": reproduction["formal_semantics_id"],
        "environment": reproduction["environment"],
    }
    return sha256_bytes(canonical_json_bytes(receipt))


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _declared_unittest_count(root: Path) -> int:
    """Count source-declared unittest methods without importing or executing tests."""

    count = 0
    tests_root = root / "formal" / "tests"
    for path in sorted(tests_root.rglob("test*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            is_test_case = any(
                (isinstance(base, ast.Name) and base.id == "TestCase")
                or (isinstance(base, ast.Attribute) and base.attr == "TestCase")
                for base in node.bases
            )
            if not is_test_case:
                continue
            count += sum(
                isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef))
                and member.name.startswith("test_")
                for member in node.body
            )
    return count


def _valid_artifact_payload(
    payload: Any,
    *,
    expected_paths: tuple[str, ...] | None = None,
    root: Path | None = None,
) -> bool:
    if not isinstance(payload, dict) or set(payload) != {"artifacts"}:
        return False
    artifacts = payload["artifacts"]
    if not isinstance(artifacts, list) or not artifacts:
        return False
    paths: list[str] = []
    for item in artifacts:
        if (
            not isinstance(item, dict)
            or set(item) != {"path", "sha256"}
            or not isinstance(item["path"], str)
            or not _is_sha256(item["sha256"])
        ):
            return False
        paths.append(item["path"])
        if root is not None:
            try:
                path = safe_repo_path(root, item["path"])
            except ValueError:
                return False
            if not path.is_file() or sha256_file(path) != item["sha256"]:
                return False
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        return False
    if expected_paths is not None and paths != sorted(expected_paths):
        return False
    return True


def _valid_tlc_projection(value: Any) -> bool:
    expected_keys = {
        "schema_version",
        "outcome",
        "tlc_version",
        "tlc_revision",
        "fingerprint_index",
        "seed",
        "workers",
        "states",
        "distinct_states",
        "diameter",
        "required_action_reached",
    }
    if not isinstance(value, dict) or set(value) != expected_keys:
        return False
    reached = value["required_action_reached"]
    return (
        value["schema_version"] == "1.0.0"
        and value["outcome"] == "NO_ERROR"
        and isinstance(value["tlc_version"], str)
        and bool(value["tlc_version"])
        and isinstance(value["tlc_revision"], str)
        and re.fullmatch(r"[0-9a-f]{7}", value["tlc_revision"]) is not None
        and isinstance(value["fingerprint_index"], int)
        and not isinstance(value["fingerprint_index"], bool)
        and 0 <= value["fingerprint_index"] <= 63
        and isinstance(value["seed"], int)
        and not isinstance(value["seed"], bool)
        and value["seed"] > 0
        and value["workers"] == 1
        and isinstance(value["states"], int)
        and isinstance(value["distinct_states"], int)
        and isinstance(value["diameter"], int)
        and value["states"] >= value["distinct_states"] > 0
        and value["diameter"] >= 0
        and isinstance(reached, dict)
        and all(isinstance(action, str) and action for action in reached)
        and all(flag is True for flag in reached.values())
    )


def _valid_tlc_payload(identifier: str, payload: Any, root: Path | None) -> bool:
    kind = identifier
    expected_keys = {"models"} | ({"artifacts"} if kind == "liveness" else set())
    if not isinstance(payload, dict) or set(payload) != expected_keys:
        return False
    models = payload["models"]
    if not isinstance(models, list) or [
        model.get("id") for model in models if isinstance(model, dict)
    ] != list(REPRODUCTION_TLC_IDS[kind]):
        return False

    source_entries: dict[str, Any] | None = None
    tool: dict[str, Any] | None = None
    evidence_models: dict[str, Any] | None = None
    if root is not None:
        try:
            manifest = load_json_strict(root / "formal" / "tla" / "cfg" / "config-manifest.json")
            lock = load_json_strict(root / "formal" / "toolchain" / "tla.lock")
            evidence = load_json_strict(root / "formal" / "reports" / "tlc-evidence.json")
            entries = [entry for entry in manifest["configs"] if entry.get("kind") == kind]
            if [entry.get("id") for entry in entries] != list(REPRODUCTION_TLC_IDS[kind]):
                return False
            source_entries = {entry["id"]: entry for entry in entries}
            tool = lock["tla_tools"]
            if (
                not _is_sha256(tool.get("sha256"))
                or not isinstance(tool.get("reported_tlc_version"), str)
                or not isinstance(tool.get("release_commit"), str)
                or re.fullmatch(r"[0-9a-f]{40}", tool["release_commit"]) is None
            ):
                return False
            all_evidence_models = evidence["models"]
            expected_evidence_ids = [
                *REPRODUCTION_TLC_IDS["safety"],
                *REPRODUCTION_TLC_IDS["liveness"],
            ]
            if (
                evidence.get("schema_version") != "2.0.0"
                or evidence.get("status") != "PASS"
                or not isinstance(all_evidence_models, list)
                or [record.get("id") for record in all_evidence_models] != expected_evidence_ids
            ):
                return False
            evidence_models = {record["id"]: record for record in all_evidence_models}
        except (AttributeError, CanonicalJsonError, KeyError, OSError, TypeError, ValueError):
            return False

    for model in models:
        if not isinstance(model, dict) or set(model) != {
            "id",
            "module_sha256",
            "config_sha256",
            "tool_sha256",
            "result",
        }:
            return False
        if not all(
            _is_sha256(model[field]) for field in ("module_sha256", "config_sha256", "tool_sha256")
        ) or not _valid_tlc_projection(model["result"]):
            return False
        if (
            root is not None
            and source_entries is not None
            and tool is not None
            and evidence_models is not None
        ):
            entry = source_entries[model["id"]]
            result = model["result"]
            try:
                required_actions = entry.get("required_action_coverage", [])
                if (
                    not isinstance(required_actions, list)
                    or len(required_actions) != len(set(required_actions))
                    or not all(isinstance(action, str) and action for action in required_actions)
                ):
                    return False
                module = safe_repo_path(root, f"formal/tla/{entry['module']}")
                config = safe_repo_path(root, f"formal/tla/{entry['config']}")
                evidence_model = evidence_models[model["id"]]
                evidence_without_hash = dict(evidence_model)
                evidence_hash = evidence_without_hash.pop("tlc_result_sha256")
                if (
                    not module.is_file()
                    or not config.is_file()
                    or model["module_sha256"] != sha256_file(module)
                    or model["config_sha256"] != sha256_file(config)
                    or model["tool_sha256"] != tool["sha256"]
                    or result["tlc_version"] != tool["reported_tlc_version"]
                    or result["tlc_revision"] != tool["release_commit"][:7]
                    or result["fingerprint_index"] != entry["fingerprint_index"]
                    or result["seed"] != entry["seed"]
                    or result["workers"] != entry["workers"]
                    or result["required_action_reached"]
                    != {action: True for action in sorted(required_actions)}
                    or evidence_hash != sha256_bytes(canonical_json_bytes(evidence_without_hash))
                    or evidence_model.get("status") != "PASS"
                    or evidence_model.get("kind") != kind
                    or evidence_model.get("module") != f"formal/tla/{entry['module']}"
                    or evidence_model.get("config") != f"formal/tla/{entry['config']}"
                    or evidence_model.get("module_sha256") != model["module_sha256"]
                    or evidence_model.get("config_sha256") != model["config_sha256"]
                    or evidence_model.get("tool_sha256") != model["tool_sha256"]
                    or evidence_model.get("fingerprint_index") != result["fingerprint_index"]
                    or evidence_model.get("seed") != result["seed"]
                    or evidence_model.get("workers") != result["workers"]
                    or evidence_model.get("states") != result["states"]
                    or evidence_model.get("distinct_states") != result["distinct_states"]
                    or evidence_model.get("diameter") != result["diameter"]
                    or evidence_model.get("required_action_reached")
                    != result["required_action_reached"]
                ):
                    return False
            except (KeyError, OSError, TypeError, ValueError):
                return False
    if kind == "liveness" and not _valid_artifact_payload(
        {"artifacts": payload["artifacts"]},
        expected_paths=("formal/reports/liveness-countercheck.json",),
        root=root,
    ):
        return False
    return True


def _valid_reproduction_result(identifier: str, result: Any, root: Path | None = None) -> bool:
    if not isinstance(result, dict) or set(result) != {
        "schema_version",
        "kind",
        "status",
        "payload",
    }:
        return False
    if (
        result["schema_version"] != "1.0.0"
        or result["kind"] != REPRODUCTION_RESULT_KINDS.get(identifier)
        or result["status"] != "PASS"
        or not isinstance(result["payload"], dict)
    ):
        return False
    payload = result["payload"]
    if identifier == "phase0":
        count_keys = {
            "actions",
            "configs",
            "faults",
            "invariants",
            "proof_obligations",
            "temporal_properties",
        }
        valid_payload = (
            set(payload)
            == {
                "schema_version",
                "phase",
                "status",
                "formal_semantics_version",
                "input_bundle_sha256",
                "counts",
                "errors",
            }
            and payload["schema_version"] == "1.0.0"
            and payload["phase"] == "T000-T003"
            and payload["status"] == "PASS"
            and isinstance(payload["formal_semantics_version"], str)
            and re.fullmatch(
                r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)",
                payload["formal_semantics_version"],
            )
            is not None
            and _is_sha256(payload["input_bundle_sha256"])
            and isinstance(payload["counts"], dict)
            and set(payload["counts"]) == count_keys
            and all(
                isinstance(count, int) and not isinstance(count, bool) and count > 0
                for count in payload["counts"].values()
            )
            and payload["errors"] == []
        )
        if valid_payload and root is not None:
            try:
                baseline = load_json_strict(root / "formal" / "reports" / "baseline-inputs.json")
                registry = load_json_strict(root / "formal" / "reports" / "formal-id-registry.json")
                expected_counts = {key: len(registry[key]) for key in count_keys}
                valid_payload = (
                    payload["formal_semantics_version"]
                    == registry["formal_semantics_version"]
                    == baseline["formal_semantics_version"]
                    and payload["input_bundle_sha256"] == baseline["input_bundle_sha256"]
                    and payload["counts"] == expected_counts
                )
            except (CanonicalJsonError, KeyError, OSError, TypeError, ValueError):
                valid_payload = False
    elif identifier == "contracts":
        valid_payload = (
            set(payload) == {"framework", "tests_run"}
            and payload["framework"] == "unittest"
            and isinstance(payload["tests_run"], int)
            and not isinstance(payload["tests_run"], bool)
            and payload["tests_run"] > 0
        )
        if valid_payload and root is not None:
            try:
                expected_test_count = _declared_unittest_count(root)
                valid_payload = (
                    expected_test_count > 0 and payload["tests_run"] == expected_test_count
                )
            except (OSError, SyntaxError, UnicodeError):
                valid_payload = False
    elif identifier == "parse":
        valid_payload = _valid_artifact_payload(payload, root=root)
        if valid_payload:
            paths = [item["path"] for item in payload["artifacts"]]
            valid_payload = all(
                path.startswith("formal/tla/") and path.endswith(".tla") for path in paths
            )
            if root is not None:
                expected = sorted(
                    path.relative_to(root).as_posix()
                    for path in (root / "formal" / "tla").rglob("*.tla")
                )
                valid_payload = paths == expected
    elif identifier in {"safety", "liveness"}:
        valid_payload = _valid_tlc_payload(identifier, payload, root)
    else:
        expected_paths = REPRODUCTION_ARTIFACT_PATHS.get(identifier)
        valid_payload = expected_paths is not None and _valid_artifact_payload(
            payload, expected_paths=expected_paths, root=root
        )
    if not valid_payload:
        return False
    try:
        canonical_json_bytes(result)
    except CanonicalJsonError:
        return False
    return True


def reproduction_matches_source(
    reproduction: Any,
    commit: str,
    formal_semantics_id: str,
    *,
    source_tree: str | None = None,
    root: Path | None = None,
) -> bool:
    """Validate clean-reproduction shape and its exact source binding."""

    expected_keys = {
        "schema_version",
        "status",
        "environment",
        "source_commit",
        "source_tree",
        "source_clean_at_start",
        "source_manifest_sha256",
        "formal_semantics_id",
        "platform",
        "machine",
        "network_interfaces",
        "network_proxies_forced_to_loopback",
        "checks",
        "errors",
    }
    if not isinstance(reproduction, dict) or set(reproduction) != expected_keys:
        return False
    checks = reproduction.get("checks")
    if not isinstance(checks, list):
        return False
    if [item.get("id") for item in checks if isinstance(item, dict)] != list(
        REPRODUCTION_CHECK_IDS
    ):
        return False
    expected_commands = {identifier: list(command) for identifier, command in REPRODUCTION_COMMANDS}
    checks_pass = True
    for item in checks:
        if not isinstance(item, dict) or set(item) != {
            "id",
            "command",
            "exit_code",
            "result",
            "output_sha256",
            "status",
        }:
            checks_pass = False
            break
        identifier = item["id"]
        if (
            item["status"] != "PASS"
            or item["exit_code"] != 0
            or item["command"] != expected_commands.get(identifier)
            or not _valid_reproduction_result(identifier, item["result"], root)
            or not isinstance(item["output_sha256"], str)
            or re.fullmatch(r"[0-9a-f]{64}", item["output_sha256"]) is None
        ):
            checks_pass = False
            break
        try:
            if item["output_sha256"] != reproduction_check_sha256(item, reproduction):
                checks_pass = False
                break
        except (CanonicalJsonError, KeyError, TypeError):
            checks_pass = False
            break
    recorded_tree = reproduction.get("source_tree")
    return (
        reproduction.get("schema_version") == "2.0.0"
        and reproduction.get("status") == "PASS"
        and reproduction.get("environment") == "linux/amd64 clean container with --network none"
        and reproduction.get("source_commit") == commit
        and reproduction.get("source_clean_at_start") is True
        and reproduction.get("formal_semantics_id") == formal_semantics_id
        and reproduction.get("network_interfaces") == ["lo"]
        and reproduction.get("network_proxies_forced_to_loopback") is True
        and reproduction.get("errors") == []
        and isinstance(recorded_tree, str)
        and re.fullmatch(r"[0-9a-f]{40}", recorded_tree) is not None
        and (source_tree is None or recorded_tree == source_tree)
        and isinstance(reproduction.get("source_manifest_sha256"), str)
        and re.fullmatch(r"[0-9a-f]{64}", reproduction["source_manifest_sha256"]) is not None
        and str(reproduction.get("machine", "")).lower() in {"amd64", "x86_64"}
        and reproduction.get("platform") == "Linux-amd64"
        and checks_pass
    )


def _artifact_entry(root: Path, path: Path, kind: str) -> dict[str, str]:
    return {
        "kind": kind,
        "path": path.relative_to(root).as_posix(),
        "sha256": semantic_text_sha256(path),
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
        if set(manifest) != {"schema_version", "commit", "git_tree", "files"}:
            raise ValueError("manifest shape mismatch")
        if (
            manifest["schema_version"] != "2.0.0"
            or manifest["commit"] != source["commit"]
            or not isinstance(manifest["git_tree"], str)
            or re.fullmatch(r"[0-9a-f]{40}", manifest["git_tree"]) is None
        ):
            raise ValueError("manifest version/commit mismatch")
        if git_revision(root, f"{manifest['commit']}^{{tree}}") != manifest["git_tree"]:
            raise ValueError("manifest Git tree does not belong to its source commit")
        files = manifest["files"]
        if not isinstance(files, list):
            raise ValueError("manifest files must be an array")
        paths = [item["path"] for item in files]
        if paths != sorted(paths) or len(paths) != len(set(paths)):
            raise ValueError("manifest paths must be sorted and unique")
        semantic_paths = {item["path"] for item in discovered}
        for item in files:
            if set(item) != {"path", "sha256"}:
                raise ValueError("manifest entry shape mismatch")
            path = safe_repo_path(root, item["path"])
            if not path.is_file():
                raise ValueError(f"manifest file missing: {item['path']}")
            actual_sha256 = (
                semantic_text_sha256(path) if item["path"] in semantic_paths else sha256_file(path)
            )
            if actual_sha256 != item["sha256"]:
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


def _check_reproduction_binding(
    report: dict[str, Any],
    root: Path,
    valid_evidence: set[str],
    reasons: set[str],
) -> None:
    evidence_id = "EVIDENCE-REPRODUCIBILITY"
    nodes = [node for node in report["evidence_graph"]["nodes"] if node["id"] == evidence_id]
    valid = False
    if len(nodes) == 1 and evidence_id in valid_evidence:
        node = nodes[0]
        try:
            if node["path"] != "formal/reports/reproducibility-evidence.json":
                raise ValueError("unexpected reproduction evidence path")
            path = safe_repo_path(root, node["path"])
            payload = load_json_strict(path)
            if path.read_bytes() != canonical_json_bytes(payload):
                raise ValueError("reproduction evidence is not canonical JSON")
            source_manifest_path = safe_repo_path(root, report["source_tree"]["manifest_path"])
            source_manifest = load_json_strict(source_manifest_path)
            valid = reproduction_matches_source(
                payload,
                report["source_tree"]["commit"],
                report["formal_semantics_id"],
                source_tree=source_manifest["git_tree"],
                root=root,
            )
        except (CanonicalJsonError, OSError, TypeError, ValueError):
            valid = False
    if not valid:
        _reason(reasons, "INVALID_REPRODUCTION_ATTESTATION")


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
    _check_reproduction_binding(report, root, valid_evidence, reasons)

    _check_expected_records(
        report["toolchains"], TOOLCHAIN_IDS, "TOOLCHAIN", valid_evidence, reasons
    )
    config_ids = {item["id"] for item in registry["configs"]}
    _check_expected_records(
        report["model_checks"], config_ids, "MODEL_CHECK", valid_evidence, reasons
    )
    property_ids = {item["id"] for item in registry["invariants"] + registry["temporal_properties"]}
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
                item["id"] not in property_ids or item["status"] != "PASS" for item in properties
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
    evidence_by_id = {node["id"]: node for node in report["evidence_graph"]["nodes"]}
    for review in report["review_attestations"]:
        evidence_id = review["evidence_id"]
        binding_valid = False
        node = evidence_by_id.get(evidence_id)
        if evidence_id in valid_evidence and node is not None:
            try:
                evidence_path = PurePosixPath(node["path"])
                if (
                    evidence_path.parts[:3] != ("formal", "reports", "reviews")
                    or len(evidence_path.parts) != 4
                    or evidence_path.suffix != ".json"
                ):
                    raise ValueError("review evidence path is outside the review directory")
                payload = load_json_strict(safe_repo_path(root, node["path"]))
                binding_valid = review_attestation_matches(
                    payload,
                    reviewed_commit=report["source_tree"]["commit"],
                    formal_semantics_id=report["formal_semantics_id"],
                    projection=review,
                )
            except (CanonicalJsonError, OSError, TypeError, ValueError):
                binding_valid = False
        if not binding_valid:
            _reason(reasons, "INVALID_REVIEW_ATTESTATION", evidence_id)
            continue
        if (
            review["independent"]
            and review["status"] == "PASS"
            and set(review["scope"]) == REVIEW_SCOPE
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
