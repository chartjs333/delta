"""Generate isolated, non-authoritative Campaign 02 controller test material.

The generated validator set is accepted by the production bootstrap parser so it
can exercise signature verification in local tests.  It is deliberately marked
and named as demo-only material and never persists governance evidence, votes,
attestations, execution authorization, or benchmark results.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import stat
import sys
import tempfile
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from deltatorrent.benchmark.campaign02_bootstrap import (
    BootstrapValidatorSet,
    Campaign02BootstrapError,
    SignedBootstrapMappingVote,
    WorkflowBootstrapMapping,
    verify_bootstrap_mapping,
)
from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.protocol.canonical import sha256_content_id

_CONTROLLER_COUNT: Final = 4
_DEMO_TYPE: Final = "CAMPAIGN02_DEMO_CONTROLLER_BUNDLE"
_DEMO_VERSION: Final = "1.0.0"
_MANIFEST_NAME: Final = "demo-controller-manifest.json"
_VALIDATOR_SET_NAME: Final = "bootstrap-validator-set.demo.json"
_ADMIN_UI_REGISTER_NAME: Final = "controller-register.demo.json"
_NOTICE_NAME: Final = "DEMO-ONLY.txt"
_PRIVATE_DIR_NAME: Final = "private"
_PROHIBITED_USES: Final = (
    "governance_evidence",
    "controller_appointment",
    "bootstrap_registration",
    "execute_stage_a",
    "benchmark_definition_qc",
    "benchmark_result_qc",
    "production_or_pilot",
)
_DEMO_WORKFLOW: Final = b"name: local synthetic Campaign 02 bootstrap demo\n"


class DemoControllerError(ValueError):
    """Stable fail-closed demo-controller tooling rejection."""


@dataclass(frozen=True, slots=True)
class DemoControllerBundle:
    """Public summary of a generated and locally verified demo bundle."""

    output_dir: Path
    validator_set_id: str
    signer_ids: tuple[str, ...]

    @property
    def document(self) -> dict[str, object]:
        return {
            "controller_count": len(self.signer_ids),
            "execution_authorized": False,
            "governance_eligible": False,
            "output_dir": str(self.output_dir),
            "signer_ids": list(self.signer_ids),
            "valid_for_campaign02_governance": False,
            "valid_for_demo_testing": True,
            "validator_set_id": self.validator_set_id,
        }


@dataclass(frozen=True, slots=True)
class DemoSmokeResult:
    """Non-authoritative presentation result from production verifier calls."""

    validator_set_id: str
    mapping_id: str
    signer_ids: tuple[str, ...]

    @property
    def document(self) -> dict[str, object]:
        return {
            "authoritative": False,
            "checks": {
                "forged_signature_rejected": "PASS",
                "production_parser_compatibility": "PASS",
                "three_of_four_quorum_verified": "PASS",
                "two_of_four_quorum_rejected": "PASS",
            },
            "demo_status": "DEMO_PASS",
            "environment": "LOCAL_DEMO_ONLY",
            "execution_authorized": False,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "governance_eligible": False,
            "keys_cryptographically_valid": True,
            "mapping_id": self.mapping_id,
            "note": (
                "Synthetic local smoke result only; it is not governance evidence or "
                "Campaign 02 authorization."
            ),
            "schema_version": _DEMO_VERSION,
            "signer_ids": list(self.signer_ids),
            "type_name": "CAMPAIGN02_DEMO_QUORUM_SMOKE_RESULT",
            "valid_for_campaign02_governance": False,
            "valid_for_demo_testing": True,
            "validator_set_id": self.validator_set_id,
        }

    @property
    def presentation(self) -> str:
        """Human-readable commission display with the authority boundary in view."""
        return "\n".join(
            (
                "DeltaReduce Campaign 02 — cryptographic controller demo",
                "=========================================================",
                "Mode:                         LOCAL_DEMO_ONLY",
                "Four Ed25519 key bindings:   PASS (4/4)",
                "Production parser:           PASS",
                "Valid quorum:                PASS (3/4)",
                "Insufficient quorum:         REJECTED (2/4)",
                "Forged signature:            REJECTED",
                f"Demo validator set:          {self.validator_set_id}",
                "Governance eligibility:       NO",
                "Execution authorization:      NO",
                "Overall demo result:          DEMO_PASS",
            )
        )


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _write_new(path: Path, value: bytes, mode: int) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    descriptor = os.open(path, flags, mode)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            descriptor = -1
            stream.write(value)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    path.chmod(mode)


def _private_key_bytes(key: Ed25519PrivateKey) -> bytes:
    return key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )


def _public_key_bytes(key: Ed25519PrivateKey) -> bytes:
    return key.public_key().public_bytes(
        serialization.Encoding.Raw,
        serialization.PublicFormat.Raw,
    )


def _private_key_filename(index: int) -> str:
    return f"demo-campaign02-signer-{index:02d}.demo-controller-private.pem"


def _git_blob_id(value: bytes) -> str:
    header = b"blob " + str(len(value)).encode("ascii") + b"\0"
    return hashlib.sha1(header + value).hexdigest()


def _demo_mapping() -> WorkflowBootstrapMapping:
    return WorkflowBootstrapMapping.from_dict(
        {
            "bootstrap_commit": "d" * 40,
            "bootstrap_workflow_blob_id": _git_blob_id(_DEMO_WORKFLOW),
            "bootstrap_workflow_content_id": sha256_content_id(_DEMO_WORKFLOW),
            "bootstrap_workflow_path": ".github/workflows/campaign02-stage-a-bootstrap.yml",
            "execution_authorized": False,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "qualified_source_commit": "e" * 40,
            "qualified_source_tree": "f" * 40,
            "repository": "example/local-demo",
            "schema_version": "1.0.0",
            "source_stage_a_workflow_content_id": "sha256:" + "0" * 64,
            "source_stage_a_workflow_path": (".github/workflows/benchmark-campaign02-stage-a.yml"),
            "type_name": "CAMPAIGN02_WORKFLOW_BOOTSTRAP_MAPPING",
        }
    )


def _load_demo_private_key(path: Path) -> Ed25519PrivateKey:
    try:
        value = serialization.load_pem_private_key(path.read_bytes(), password=None)
    except (OSError, ValueError, TypeError) as exc:
        raise DemoControllerError("DEMO_CONTROLLER_PRIVATE_KEY_INVALID") from exc
    if not isinstance(value, Ed25519PrivateKey):
        raise DemoControllerError("DEMO_CONTROLLER_PRIVATE_KEY_TYPE_INVALID")
    return value


def _require_demo_manifest(value: object) -> dict[str, object]:
    expected = {
        "authoritative",
        "admin_ui_register_file",
        "admin_ui_register_file_sha256",
        "controllers",
        "created_at",
        "cryptographic_validity_scope",
        "environment",
        "execution_authorized",
        "formal_semantics_id",
        "governance_eligible",
        "private_key_storage",
        "prohibited_uses",
        "schema_version",
        "type_name",
        "valid_for_campaign02_governance",
        "valid_for_demo_testing",
        "validator_set_file",
        "validator_set_file_sha256",
        "validator_set_id",
    }
    if not isinstance(value, dict) or set(value) != expected:
        raise DemoControllerError("DEMO_CONTROLLER_MANIFEST_FIELDS_INVALID")
    if (
        value["type_name"] != _DEMO_TYPE
        or value["schema_version"] != _DEMO_VERSION
        or value["environment"] != "LOCAL_DEMO_ONLY"
        or value["cryptographic_validity_scope"] != "LOCAL_DEMO_ONLY"
        or value["authoritative"] is not False
        or value["governance_eligible"] is not False
        or value["execution_authorized"] is not False
        or value["valid_for_demo_testing"] is not True
        or value["valid_for_campaign02_governance"] is not False
        or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
        or value["admin_ui_register_file"] != _ADMIN_UI_REGISTER_NAME
        or value["validator_set_file"] != _VALIDATOR_SET_NAME
        or value["prohibited_uses"] != list(_PROHIBITED_USES)
    ):
        raise DemoControllerError("DEMO_CONTROLLER_MANIFEST_BOUNDARY_INVALID")
    controllers = value["controllers"]
    if not isinstance(controllers, list) or len(controllers) != _CONTROLLER_COUNT:
        raise DemoControllerError("DEMO_CONTROLLER_MANIFEST_CONTROLLERS_INVALID")
    storage = value["private_key_storage"]
    if not isinstance(storage, dict) or storage != {
        "directory": _PRIVATE_DIR_NAME,
        "format": "UNENCRYPTED_PKCS8_PEM",
        "kind": "DEMO_SOFTWARE_FILE",
        "repository_commit_prohibited": True,
        "windows_acl_must_be_checked_by_operator": True,
    }:
        raise DemoControllerError("DEMO_CONTROLLER_PRIVATE_STORAGE_INVALID")
    return value


def _load_json(path: Path, code: str) -> object:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DemoControllerError(code) from exc


def generate_demo_controller_bundle(output_dir: Path) -> DemoControllerBundle:
    """Create one fresh demo bundle without overwriting any existing path."""
    destination = output_dir.expanduser().resolve(strict=False)
    if destination.exists():
        raise DemoControllerError("DEMO_CONTROLLER_OUTPUT_ALREADY_EXISTS")
    destination.parent.mkdir(parents=True, exist_ok=True)

    temporary = Path(tempfile.mkdtemp(prefix=f".{destination.name}.tmp-", dir=destination.parent))
    try:
        temporary.chmod(stat.S_IRWXU)
        private_dir = temporary / _PRIVATE_DIR_NAME
        private_dir.mkdir(mode=stat.S_IRWXU)
        private_dir.chmod(stat.S_IRWXU)

        validators: list[dict[str, str]] = []
        controller_records: list[dict[str, object]] = []
        for index in range(1, _CONTROLLER_COUNT + 1):
            controller_id = f"demo-campaign02-controller-{index:02d}"
            signer_id = f"demo-campaign02-signer-{index:02d}"
            key = Ed25519PrivateKey.generate()
            public_key = _public_key_bytes(key)
            public_key_base64 = base64.b64encode(public_key).decode("ascii")
            public_key_fingerprint = sha256_content_id(public_key)
            filename = _private_key_filename(index)

            _write_new(private_dir / filename, _private_key_bytes(key), stat.S_IRUSR | stat.S_IWUSR)
            validators.append(
                {
                    "controller_id": controller_id,
                    "public_key_base64": public_key_base64,
                    "signer_id": signer_id,
                }
            )
            controller_records.append(
                {
                    "accountable_owner_id": "LOCAL_DEMO_OPERATOR",
                    "administrative_domain_id": f"demo-simulated-domain-{index:02d}",
                    "controller_id": controller_id,
                    "custody_kind": "DEMO_SOFTWARE_FILE",
                    "governance_status": "NOT_APPOINTED",
                    "independence_claimed": False,
                    "private_key_file": f"{_PRIVATE_DIR_NAME}/{filename}",
                    "public_key_base64": public_key_base64,
                    "public_key_raw_sha256": public_key_fingerprint,
                    "signer_id": signer_id,
                }
            )

        validator_set = BootstrapValidatorSet.from_dict(
            {
                "execution_authorized": False,
                "f_b": 1,
                "formal_semantics_id": FORMAL_SEMANTICS_ID,
                "quorum_threshold": 3,
                "schema_version": "1.0.0",
                "type_name": "CAMPAIGN02_WORKFLOW_BOOTSTRAP_VALIDATOR_SET",
                "validators": validators,
            }
        )
        validator_set_bytes = _json_bytes(validator_set.document)
        _write_new(
            temporary / _VALIDATOR_SET_NAME, validator_set_bytes, stat.S_IRUSR | stat.S_IWUSR
        )

        admin_ui_register = {
            "authority_class": "LOCAL_FIXTURE",
            "authoritative": False,
            "controllers": [
                {
                    "accountable_owner_id": record["accountable_owner_id"],
                    "administrative_domain_id": record["administrative_domain_id"],
                    "controller_id": record["controller_id"],
                    "cryptographic_key_status": "VALID_FOR_DEMO_TESTING",
                    "custody_boundary_id": f"demo-local-boundary-{index:02d}",
                    "custody_kind": record["custody_kind"],
                    "identity_type": "SYNTHETIC_DEMO",
                    "public_key_base64": record["public_key_base64"],
                    "public_key_raw_sha256": record["public_key_raw_sha256"],
                    "signer_id": record["signer_id"],
                    "slot": index,
                    "status": "DEMO_VALID_FOR_TESTING",
                }
                for index, record in enumerate(controller_records, start=1)
            ],
            "demo_mode": True,
            "document_type": "CONTROLLER_GOVERNANCE_REGISTER",
            "document_version": "demo-1.0.0",
            "execution_authorized": False,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "governance_eligible": False,
            "note": (
                "Synthetic LOCAL_FIXTURE for product demonstrations; not governance evidence."
            ),
            "status": "DEMO_VALID_FOR_TESTING",
            "validator_set_id": validator_set.content_id,
        }
        admin_ui_register_bytes = _json_bytes(admin_ui_register)
        _write_new(
            temporary / _ADMIN_UI_REGISTER_NAME,
            admin_ui_register_bytes,
            stat.S_IRUSR | stat.S_IWUSR,
        )

        manifest = {
            "admin_ui_register_file": _ADMIN_UI_REGISTER_NAME,
            "admin_ui_register_file_sha256": sha256_content_id(admin_ui_register_bytes),
            "authoritative": False,
            "controllers": controller_records,
            "created_at": datetime.now(UTC).isoformat(),
            "cryptographic_validity_scope": "LOCAL_DEMO_ONLY",
            "environment": "LOCAL_DEMO_ONLY",
            "execution_authorized": False,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "governance_eligible": False,
            "private_key_storage": {
                "directory": _PRIVATE_DIR_NAME,
                "format": "UNENCRYPTED_PKCS8_PEM",
                "kind": "DEMO_SOFTWARE_FILE",
                "repository_commit_prohibited": True,
                "windows_acl_must_be_checked_by_operator": True,
            },
            "prohibited_uses": list(_PROHIBITED_USES),
            "schema_version": _DEMO_VERSION,
            "type_name": _DEMO_TYPE,
            "valid_for_campaign02_governance": False,
            "valid_for_demo_testing": True,
            "validator_set_file": _VALIDATOR_SET_NAME,
            "validator_set_file_sha256": sha256_content_id(validator_set_bytes),
            "validator_set_id": validator_set.content_id,
        }
        _write_new(
            temporary / _MANIFEST_NAME,
            _json_bytes(manifest),
            stat.S_IRUSR | stat.S_IWUSR,
        )
        _write_new(
            temporary / _NOTICE_NAME,
            (
                b"LOCAL DEMO MATERIAL ONLY\n"
                b"\n"
                b"These identities and unencrypted private keys are synthetic test data.\n"
                b"They are NOT governance evidence, controller appointments, execution\n"
                b"authorization, BenchmarkDefinitionQC, or BenchmarkResultQC.\n"
                b"Never commit this directory or use it for production or pilot runs.\n"
            ),
            stat.S_IRUSR | stat.S_IWUSR,
        )
        temporary.rename(destination)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        raise

    return verify_demo_controller_bundle(destination)


def verify_demo_controller_bundle(output_dir: Path) -> DemoControllerBundle:
    """Verify markers, production parser compatibility, and every private/public pair."""
    requested = output_dir.expanduser()
    if requested.is_symlink():
        raise DemoControllerError("DEMO_CONTROLLER_OUTPUT_INVALID")
    root = requested.resolve(strict=True)
    if not root.is_dir():
        raise DemoControllerError("DEMO_CONTROLLER_OUTPUT_INVALID")
    expected_top_level = {
        _ADMIN_UI_REGISTER_NAME,
        _NOTICE_NAME,
        _MANIFEST_NAME,
        _PRIVATE_DIR_NAME,
        _VALIDATOR_SET_NAME,
    }
    top_level = tuple(root.iterdir())
    if {item.name for item in top_level} != expected_top_level or any(
        item.is_symlink() for item in top_level
    ):
        raise DemoControllerError("DEMO_CONTROLLER_OUTPUT_CONTENTS_INVALID")

    manifest = _require_demo_manifest(
        _load_json(root / _MANIFEST_NAME, "DEMO_CONTROLLER_MANIFEST_INVALID")
    )
    admin_ui_register_path = root / _ADMIN_UI_REGISTER_NAME
    admin_ui_register_bytes = admin_ui_register_path.read_bytes()
    if manifest["admin_ui_register_file_sha256"] != sha256_content_id(admin_ui_register_bytes):
        raise DemoControllerError("DEMO_CONTROLLER_ADMIN_UI_REGISTER_DIGEST_MISMATCH")
    admin_ui_register = _load_json(
        admin_ui_register_path,
        "DEMO_CONTROLLER_ADMIN_UI_REGISTER_INVALID",
    )
    if not isinstance(admin_ui_register, dict):
        raise DemoControllerError("DEMO_CONTROLLER_ADMIN_UI_REGISTER_INVALID")
    if (
        admin_ui_register.get("authority_class") != "LOCAL_FIXTURE"
        or admin_ui_register.get("authoritative") is not False
        or admin_ui_register.get("demo_mode") is not True
        or admin_ui_register.get("document_type") != "CONTROLLER_GOVERNANCE_REGISTER"
        or admin_ui_register.get("execution_authorized") is not False
        or admin_ui_register.get("governance_eligible") is not False
        or admin_ui_register.get("status") != "DEMO_VALID_FOR_TESTING"
    ):
        raise DemoControllerError("DEMO_CONTROLLER_ADMIN_UI_REGISTER_BOUNDARY_INVALID")
    validator_set_path = root / _VALIDATOR_SET_NAME
    validator_set_bytes = validator_set_path.read_bytes()
    if manifest["validator_set_file_sha256"] != sha256_content_id(validator_set_bytes):
        raise DemoControllerError("DEMO_CONTROLLER_VALIDATOR_SET_FILE_DIGEST_MISMATCH")
    validator_set = BootstrapValidatorSet.from_dict(
        _load_json(validator_set_path, "DEMO_CONTROLLER_VALIDATOR_SET_INVALID")
    )
    if manifest["validator_set_id"] != validator_set.content_id:
        raise DemoControllerError("DEMO_CONTROLLER_VALIDATOR_SET_ID_MISMATCH")

    private_dir = root / _PRIVATE_DIR_NAME
    if not private_dir.is_dir() or private_dir.is_symlink():
        raise DemoControllerError("DEMO_CONTROLLER_PRIVATE_DIRECTORY_INVALID")

    controllers = manifest["controllers"]
    assert isinstance(controllers, list)
    admin_ui_controllers = admin_ui_register.get("controllers")
    if not isinstance(admin_ui_controllers, list) or len(admin_ui_controllers) != _CONTROLLER_COUNT:
        raise DemoControllerError("DEMO_CONTROLLER_ADMIN_UI_CONTROLLERS_INVALID")
    expected_private_names: set[str] = set()
    signer_ids: list[str] = []
    for index, record in enumerate(controllers, start=1):
        if not isinstance(record, dict):
            raise DemoControllerError("DEMO_CONTROLLER_RECORD_INVALID")
        expected_record_fields = {
            "accountable_owner_id",
            "administrative_domain_id",
            "controller_id",
            "custody_kind",
            "governance_status",
            "independence_claimed",
            "private_key_file",
            "public_key_base64",
            "public_key_raw_sha256",
            "signer_id",
        }
        if set(record) != expected_record_fields:
            raise DemoControllerError("DEMO_CONTROLLER_RECORD_FIELDS_INVALID")
        expected_controller_id = f"demo-campaign02-controller-{index:02d}"
        expected_signer_id = f"demo-campaign02-signer-{index:02d}"
        expected_filename = _private_key_filename(index)
        if (
            record["controller_id"] != expected_controller_id
            or record["signer_id"] != expected_signer_id
            or record["accountable_owner_id"] != "LOCAL_DEMO_OPERATOR"
            or record["administrative_domain_id"] != f"demo-simulated-domain-{index:02d}"
            or record["custody_kind"] != "DEMO_SOFTWARE_FILE"
            or record["governance_status"] != "NOT_APPOINTED"
            or record["independence_claimed"] is not False
            or record["private_key_file"] != f"{_PRIVATE_DIR_NAME}/{expected_filename}"
        ):
            raise DemoControllerError("DEMO_CONTROLLER_RECORD_BOUNDARY_INVALID")

        validator = validator_set.validator(expected_signer_id)
        public_key = base64.b64decode(str(record["public_key_base64"]), validate=True)
        if (
            validator.controller_id != expected_controller_id
            or validator.public_key != public_key
            or record["public_key_raw_sha256"] != sha256_content_id(public_key)
        ):
            raise DemoControllerError("DEMO_CONTROLLER_PUBLIC_KEY_BINDING_INVALID")
        admin_ui_record = admin_ui_controllers[index - 1]
        if (
            not isinstance(admin_ui_record, dict)
            or admin_ui_record.get("controller_id") != expected_controller_id
            or admin_ui_record.get("signer_id") != expected_signer_id
            or admin_ui_record.get("public_key_base64") != record["public_key_base64"]
            or admin_ui_record.get("public_key_raw_sha256") != record["public_key_raw_sha256"]
            or admin_ui_record.get("cryptographic_key_status") != "VALID_FOR_DEMO_TESTING"
            or admin_ui_record.get("identity_type") != "SYNTHETIC_DEMO"
            or admin_ui_record.get("status") != "DEMO_VALID_FOR_TESTING"
        ):
            raise DemoControllerError("DEMO_CONTROLLER_ADMIN_UI_BINDING_INVALID")

        private_path = root / _PRIVATE_DIR_NAME / expected_filename
        if not private_path.is_file() or private_path.is_symlink():
            raise DemoControllerError("DEMO_CONTROLLER_PRIVATE_KEY_PATH_INVALID")
        private_value = _load_demo_private_key(private_path)
        if _public_key_bytes(private_value) != public_key:
            raise DemoControllerError("DEMO_CONTROLLER_PRIVATE_KEY_BINDING_INVALID")
        expected_private_names.add(expected_filename)
        signer_ids.append(expected_signer_id)

    if {item.name for item in private_dir.iterdir()} != expected_private_names:
        raise DemoControllerError("DEMO_CONTROLLER_PRIVATE_CONTENTS_INVALID")
    return DemoControllerBundle(root, validator_set.content_id, tuple(signer_ids))


def run_demo_quorum_smoke(output_dir: Path) -> DemoSmokeResult:
    """Exercise a real 3-of-4 verifier path and two mandatory negative paths."""
    bundle = verify_demo_controller_bundle(output_dir)
    validator_set = BootstrapValidatorSet.from_dict(
        _load_json(
            bundle.output_dir / _VALIDATOR_SET_NAME,
            "DEMO_CONTROLLER_VALIDATOR_SET_INVALID",
        )
    )
    mapping = _demo_mapping()
    submitted_at = datetime.now(UTC)
    votes: list[SignedBootstrapMappingVote] = []
    for index, signer_id in enumerate(bundle.signer_ids[:3], start=1):
        private_key = _load_demo_private_key(
            bundle.output_dir / _PRIVATE_DIR_NAME / _private_key_filename(index)
        )
        unsigned = SignedBootstrapMappingVote(
            mapping_id=mapping.content_id,
            validator_set_id=validator_set.content_id,
            signer_id=signer_id,
            submitted_at=submitted_at,
            signature=b"\0" * 64,
        )
        votes.append(replace(unsigned, signature=private_key.sign(unsigned.message)))

    verified = verify_bootstrap_mapping(
        mapping,
        validator_set=validator_set,
        votes=tuple(votes),
    )
    try:
        verify_bootstrap_mapping(
            mapping,
            validator_set=validator_set,
            votes=tuple(votes[:2]),
        )
    except Campaign02BootstrapError as exc:
        if str(exc) != "CAMPAIGN02_BOOTSTRAP_SIGNATURE_QUORUM_INVALID":
            raise DemoControllerError("DEMO_CONTROLLER_TWO_VOTE_NEGATIVE_UNEXPECTED") from exc
    else:
        raise DemoControllerError("DEMO_CONTROLLER_TWO_VOTE_NEGATIVE_ACCEPTED")

    forged_votes = (*votes[:-1], replace(votes[-1], signature=b"\0" * 64))
    try:
        verify_bootstrap_mapping(
            mapping,
            validator_set=validator_set,
            votes=forged_votes,
        )
    except Campaign02BootstrapError as exc:
        if str(exc) != "CAMPAIGN02_BOOTSTRAP_SIGNATURE_INVALID":
            raise DemoControllerError("DEMO_CONTROLLER_FORGED_VOTE_NEGATIVE_UNEXPECTED") from exc
    else:
        raise DemoControllerError("DEMO_CONTROLLER_FORGED_VOTE_NEGATIVE_ACCEPTED")

    return DemoSmokeResult(
        validator_set_id=validator_set.content_id,
        mapping_id=mapping.content_id,
        signer_ids=verified.signer_ids,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate or verify four non-authoritative Campaign 02 demo controllers."
    )
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("generate", "verify", "smoke", "demo"):
        subparser = commands.add_parser(command)
        subparser.add_argument(
            "--output-dir",
            type=Path,
            required=True,
            help="Local output directory; generation refuses to overwrite an existing path.",
        )
        subparser.add_argument(
            "--pretty",
            action="store_true",
            help="Print a human-readable presentation; JSON remains the default.",
        )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the demo-controller command-line interface."""
    args = _parser().parse_args(argv)
    try:
        if args.command == "generate":
            result: DemoControllerBundle | DemoSmokeResult = generate_demo_controller_bundle(
                args.output_dir
            )
        elif args.command == "verify":
            result = verify_demo_controller_bundle(args.output_dir)
        elif args.command == "smoke":
            result = run_demo_quorum_smoke(args.output_dir)
        else:
            generate_demo_controller_bundle(args.output_dir)
            result = run_demo_quorum_smoke(args.output_dir)
    except (DemoControllerError, OSError, ValueError) as exc:
        print(f"demo-controller error: {exc}", file=sys.stderr)
        return 2
    if args.pretty and isinstance(result, DemoSmokeResult):
        print(result.presentation)
    else:
        print(json.dumps(result.document, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
