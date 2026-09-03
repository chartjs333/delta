"""Immutable default-branch bootstrap binding for Campaign 02 Stage A.

The mapping is registration metadata, never execution authority.  Its detached
signatures prove only that an exact default-branch workflow may dispatch an
exact qualified source.  Stage execution still requires the independent
C2-024 authorization proof.
"""

from __future__ import annotations

import base64
import binascii
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Final

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

_CONTENT_ID: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_GIT_ID: Final = re.compile(r"^[0-9a-f]{40}$")
_REPOSITORY: Final = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_WORKFLOW_PATH: Final = re.compile(r"^\.github/workflows/[A-Za-z0-9_.-]+\.ya?ml$")
_ARTIFACT_NAME: Final = re.compile(r"^.+-attempt-[1-9][0-9]*$")
_MAPPING_DOMAIN: Final = b"deltareduce.010.campaign02-workflow-bootstrap-mapping.v1\0"
_VALIDATOR_SET_DOMAIN: Final = b"deltareduce.010.campaign02-workflow-bootstrap-validator-set.v1\0"
_SIGNATURE_DOMAIN: Final = b"deltareduce.010.campaign02-workflow-bootstrap-signature.v1\0"
_ATTESTATION_DOMAIN: Final = b"deltareduce.010.campaign02-workflow-bootstrap-attestation.v1\0"
_REGISTRATION_DOMAIN: Final = b"deltareduce.010.campaign02-workflow-registration-receipt.v3\0"
_API_SNAPSHOT_DOMAIN: Final = b"deltareduce.010.campaign02-github-api-snapshot.v1\0"
_API_EVIDENCE_DOMAIN: Final = b"deltareduce.010.campaign02-registration-api-evidence.v1\0"
_REGISTRATION_SIGNATURE_DOMAIN: Final = (
    b"deltareduce.010.campaign02-workflow-registration-signature.v2\0"
)
_REGISTRATION_ATTESTATION_DOMAIN: Final = (
    b"deltareduce.010.campaign02-workflow-registration-attestation.v1\0"
)
_VERIFIED_MAPPING_TOKEN: Final = object()
_VERIFIED_REGISTRATION_TOKEN: Final = object()


class Campaign02BootstrapError(ValueError):
    """Stable fail-closed bootstrap provenance rejection."""


def _fail(code: str) -> Campaign02BootstrapError:
    return Campaign02BootstrapError(code)


def _content_id(value: object, code: str) -> str:
    if not isinstance(value, str) or _CONTENT_ID.fullmatch(value) is None:
        raise _fail(code)
    return value


def _git_id(value: object, code: str) -> str:
    if not isinstance(value, str) or _GIT_ID.fullmatch(value) is None:
        raise _fail(code)
    return value


def _canonical_base64(value: object, code: str) -> bytes:
    if not isinstance(value, str):
        raise _fail(code)
    try:
        decoded = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise _fail(code) from exc
    if base64.b64encode(decoded).decode("ascii") != value:
        raise _fail(code)
    return decoded


def _positive_int(value: object, code: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise _fail(code)
    return value


def _timestamp(value: object, code: str) -> datetime:
    try:
        result = datetime.fromisoformat(str(value))
    except ValueError as exc:
        raise _fail(code) from exc
    if result.tzinfo is None or result.utcoffset() is None:
        raise _fail(code)
    return result


@dataclass(frozen=True, slots=True)
class WorkflowBootstrapMapping:
    repository: str
    bootstrap_workflow_path: str
    bootstrap_commit: str
    bootstrap_workflow_blob_id: str
    bootstrap_workflow_content_id: str
    qualified_source_commit: str
    qualified_source_tree: str
    source_stage_a_workflow_path: str
    source_stage_a_workflow_content_id: str

    @classmethod
    def from_dict(cls, value: object) -> WorkflowBootstrapMapping:
        fields = {
            "bootstrap_commit",
            "bootstrap_workflow_blob_id",
            "bootstrap_workflow_content_id",
            "bootstrap_workflow_path",
            "execution_authorized",
            "formal_semantics_id",
            "qualified_source_commit",
            "qualified_source_tree",
            "repository",
            "schema_version",
            "source_stage_a_workflow_content_id",
            "source_stage_a_workflow_path",
            "type_name",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise _fail("CAMPAIGN02_BOOTSTRAP_MAPPING_FIELDS_INVALID")
        repository = value["repository"]
        bootstrap_path = value["bootstrap_workflow_path"]
        source_path = value["source_stage_a_workflow_path"]
        if (
            value["type_name"] != "CAMPAIGN02_WORKFLOW_BOOTSTRAP_MAPPING"
            or value["schema_version"] != "1.0.0"
            or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
            or value["execution_authorized"] is not False
            or not isinstance(repository, str)
            or _REPOSITORY.fullmatch(repository) is None
            or not isinstance(bootstrap_path, str)
            or _WORKFLOW_PATH.fullmatch(bootstrap_path) is None
            or bootstrap_path != ".github/workflows/campaign02-stage-a-bootstrap.yml"
            or not isinstance(source_path, str)
            or _WORKFLOW_PATH.fullmatch(source_path) is None
            or source_path != ".github/workflows/benchmark-campaign02-stage-a.yml"
        ):
            raise _fail("CAMPAIGN02_BOOTSTRAP_MAPPING_HEADER_INVALID")
        return cls(
            repository=repository,
            bootstrap_workflow_path=bootstrap_path,
            bootstrap_commit=_git_id(
                value["bootstrap_commit"], "CAMPAIGN02_BOOTSTRAP_COMMIT_INVALID"
            ),
            bootstrap_workflow_blob_id=_git_id(
                value["bootstrap_workflow_blob_id"], "CAMPAIGN02_BOOTSTRAP_BLOB_INVALID"
            ),
            bootstrap_workflow_content_id=_content_id(
                value["bootstrap_workflow_content_id"],
                "CAMPAIGN02_BOOTSTRAP_CONTENT_ID_INVALID",
            ),
            qualified_source_commit=_git_id(
                value["qualified_source_commit"], "CAMPAIGN02_BOOTSTRAP_SOURCE_COMMIT_INVALID"
            ),
            qualified_source_tree=_git_id(
                value["qualified_source_tree"], "CAMPAIGN02_BOOTSTRAP_SOURCE_TREE_INVALID"
            ),
            source_stage_a_workflow_path=source_path,
            source_stage_a_workflow_content_id=_content_id(
                value["source_stage_a_workflow_content_id"],
                "CAMPAIGN02_BOOTSTRAP_SOURCE_WORKFLOW_ID_INVALID",
            ),
        )

    @property
    def document(self) -> dict[str, object]:
        return {
            "bootstrap_commit": self.bootstrap_commit,
            "bootstrap_workflow_blob_id": self.bootstrap_workflow_blob_id,
            "bootstrap_workflow_content_id": self.bootstrap_workflow_content_id,
            "bootstrap_workflow_path": self.bootstrap_workflow_path,
            "execution_authorized": False,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "qualified_source_commit": self.qualified_source_commit,
            "qualified_source_tree": self.qualified_source_tree,
            "repository": self.repository,
            "schema_version": "1.0.0",
            "source_stage_a_workflow_content_id": self.source_stage_a_workflow_content_id,
            "source_stage_a_workflow_path": self.source_stage_a_workflow_path,
            "type_name": "CAMPAIGN02_WORKFLOW_BOOTSTRAP_MAPPING",
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(_MAPPING_DOMAIN + canonical_json_bytes(self.document))


@dataclass(frozen=True, slots=True)
class BootstrapValidator:
    signer_id: str
    controller_id: str
    public_key: bytes


@dataclass(frozen=True, slots=True)
class BootstrapValidatorSet:
    validators: tuple[BootstrapValidator, ...]
    f_b: int
    quorum_threshold: int

    @classmethod
    def from_dict(cls, value: object) -> BootstrapValidatorSet:
        fields = {
            "execution_authorized",
            "f_b",
            "formal_semantics_id",
            "quorum_threshold",
            "schema_version",
            "type_name",
            "validators",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise _fail("CAMPAIGN02_BOOTSTRAP_VALIDATOR_SET_FIELDS_INVALID")
        raw_validators = value["validators"]
        f_b = value["f_b"]
        threshold = value["quorum_threshold"]
        if (
            value["type_name"] != "CAMPAIGN02_WORKFLOW_BOOTSTRAP_VALIDATOR_SET"
            or value["schema_version"] != "1.0.0"
            or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
            or value["execution_authorized"] is not False
            or not isinstance(raw_validators, list)
            or not raw_validators
            or isinstance(f_b, bool)
            or not isinstance(f_b, int)
            or f_b < 1
            or isinstance(threshold, bool)
            or not isinstance(threshold, int)
            or threshold <= 0
            or threshold > len(raw_validators)
            or len(raw_validators) != 3 * f_b + 1
            or threshold != 2 * f_b + 1
        ):
            raise _fail("CAMPAIGN02_BOOTSTRAP_VALIDATOR_SET_HEADER_INVALID")
        validators: list[BootstrapValidator] = []
        for item in raw_validators:
            if not isinstance(item, dict) or set(item) != {
                "controller_id",
                "public_key_base64",
                "signer_id",
            }:
                raise _fail("CAMPAIGN02_BOOTSTRAP_VALIDATOR_FIELDS_INVALID")
            signer_id = item["signer_id"]
            controller_id = item["controller_id"]
            public_key = _canonical_base64(
                item["public_key_base64"], "CAMPAIGN02_BOOTSTRAP_PUBLIC_KEY_INVALID"
            )
            if (
                not isinstance(signer_id, str)
                or not signer_id
                or not isinstance(controller_id, str)
                or not controller_id
                or len(public_key) != 32
            ):
                raise _fail("CAMPAIGN02_BOOTSTRAP_VALIDATOR_INVALID")
            validators.append(BootstrapValidator(signer_id, controller_id, public_key))
        if (
            len({item.signer_id for item in validators}) != len(validators)
            or len({item.public_key for item in validators}) != len(validators)
            or len({item.controller_id for item in validators}) != len(validators)
        ):
            raise _fail("CAMPAIGN02_BOOTSTRAP_VALIDATOR_SET_DUPLICATE")
        return cls(tuple(sorted(validators, key=lambda item: item.signer_id)), f_b, threshold)

    @property
    def document(self) -> dict[str, object]:
        return {
            "execution_authorized": False,
            "f_b": self.f_b,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "quorum_threshold": self.quorum_threshold,
            "schema_version": "1.0.0",
            "type_name": "CAMPAIGN02_WORKFLOW_BOOTSTRAP_VALIDATOR_SET",
            "validators": [
                {
                    "controller_id": item.controller_id,
                    "public_key_base64": base64.b64encode(item.public_key).decode("ascii"),
                    "signer_id": item.signer_id,
                }
                for item in self.validators
            ],
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(_VALIDATOR_SET_DOMAIN + canonical_json_bytes(self.document))

    def validator(self, signer_id: str) -> BootstrapValidator:
        matches = tuple(item for item in self.validators if item.signer_id == signer_id)
        if len(matches) != 1:
            raise _fail("CAMPAIGN02_BOOTSTRAP_SIGNER_UNKNOWN")
        return matches[0]


@dataclass(frozen=True, slots=True)
class SignedBootstrapMappingVote:
    mapping_id: str
    validator_set_id: str
    signer_id: str
    submitted_at: datetime
    signature: bytes

    @classmethod
    def from_dict(cls, value: object) -> SignedBootstrapMappingVote:
        fields = {
            "formal_semantics_id",
            "mapping_id",
            "schema_version",
            "signature_base64",
            "signer_id",
            "submitted_at",
            "type_name",
            "validator_set_id",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise _fail("CAMPAIGN02_BOOTSTRAP_SIGNATURE_FIELDS_INVALID")
        signer_id = value["signer_id"]
        try:
            submitted_at = datetime.fromisoformat(str(value["submitted_at"]))
        except ValueError as exc:
            raise _fail("CAMPAIGN02_BOOTSTRAP_SIGNATURE_TIME_INVALID") from exc
        if (
            value["type_name"] != "CAMPAIGN02_WORKFLOW_BOOTSTRAP_SIGNATURE"
            or value["schema_version"] != "1.0.0"
            or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
            or not isinstance(signer_id, str)
            or not signer_id
            or submitted_at.tzinfo is None
        ):
            raise _fail("CAMPAIGN02_BOOTSTRAP_SIGNATURE_HEADER_INVALID")
        signature = _canonical_base64(
            value["signature_base64"], "CAMPAIGN02_BOOTSTRAP_SIGNATURE_INVALID"
        )
        if len(signature) != 64:
            raise _fail("CAMPAIGN02_BOOTSTRAP_SIGNATURE_INVALID")
        return cls(
            mapping_id=_content_id(value["mapping_id"], "CAMPAIGN02_BOOTSTRAP_MAPPING_ID_INVALID"),
            validator_set_id=_content_id(
                value["validator_set_id"],
                "CAMPAIGN02_BOOTSTRAP_VALIDATOR_SET_ID_INVALID",
            ),
            signer_id=signer_id,
            submitted_at=submitted_at,
            signature=signature,
        )

    @property
    def message(self) -> bytes:
        return _SIGNATURE_DOMAIN + canonical_json_bytes(
            {
                "mapping_id": self.mapping_id,
                "signer_id": self.signer_id,
                "submitted_at": self.submitted_at.isoformat(),
                "validator_set_id": self.validator_set_id,
            }
        )


@dataclass(frozen=True, slots=True, init=False)
class VerifiedBootstrapMapping:
    mapping: WorkflowBootstrapMapping
    validator_set_id: str
    signer_ids: tuple[str, ...]

    def __init__(
        self,
        token: object,
        mapping: WorkflowBootstrapMapping,
        validator_set_id: str,
        signer_ids: tuple[str, ...],
    ) -> None:
        if token is not _VERIFIED_MAPPING_TOKEN:
            raise _fail("CAMPAIGN02_BOOTSTRAP_VERIFIED_MAPPING_CONSTRUCTION_FORBIDDEN")
        object.__setattr__(self, "mapping", mapping)
        object.__setattr__(self, "validator_set_id", validator_set_id)
        object.__setattr__(self, "signer_ids", signer_ids)

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            _ATTESTATION_DOMAIN
            + canonical_json_bytes(
                {
                    "execution_authorized": False,
                    "mapping_id": self.mapping.content_id,
                    "signer_ids": list(self.signer_ids),
                    "validator_set_id": self.validator_set_id,
                }
            )
        )


def verify_bootstrap_mapping(
    mapping: WorkflowBootstrapMapping,
    *,
    validator_set: BootstrapValidatorSet,
    votes: tuple[SignedBootstrapMappingVote, ...],
) -> VerifiedBootstrapMapping:
    """Verify an exact quorum without converting mapping metadata into authority."""
    if len(votes) != validator_set.quorum_threshold:
        raise _fail("CAMPAIGN02_BOOTSTRAP_SIGNATURE_QUORUM_INVALID")
    signer_ids: list[str] = []
    controllers: list[str] = []
    for vote in votes:
        if (
            vote.mapping_id != mapping.content_id
            or vote.validator_set_id != validator_set.content_id
        ):
            raise _fail("CAMPAIGN02_BOOTSTRAP_SIGNATURE_BINDING_MISMATCH")
        validator = validator_set.validator(vote.signer_id)
        try:
            Ed25519PublicKey.from_public_bytes(validator.public_key).verify(
                vote.signature, vote.message
            )
        except InvalidSignature as exc:
            raise _fail("CAMPAIGN02_BOOTSTRAP_SIGNATURE_INVALID") from exc
        signer_ids.append(vote.signer_id)
        controllers.append(validator.controller_id)
    if len(set(signer_ids)) != len(signer_ids) or len(set(controllers)) != len(controllers):
        raise _fail("CAMPAIGN02_BOOTSTRAP_SIGNATURE_DUPLICATE")
    return VerifiedBootstrapMapping(
        _VERIFIED_MAPPING_TOKEN,
        mapping,
        validator_set.content_id,
        tuple(sorted(signer_ids)),
    )


@dataclass(frozen=True, slots=True)
class BootstrapRuntimeProvenance:
    repository: str
    workflow_id: int
    workflow_path: str
    workflow_ref: str
    workflow_sha: str
    workflow_blob_id: str
    workflow_content_id: str
    run_id: int
    run_attempt: int
    event_name: str
    dispatch_ref: str
    github_sha: str
    qualified_source_commit: str
    qualified_source_tree: str
    source_stage_a_workflow_content_id: str


def verify_bootstrap_runtime(
    verified: VerifiedBootstrapMapping,
    provenance: BootstrapRuntimeProvenance,
) -> None:
    """Bind actual GitHub and checked-out source objects without equating their SHAs."""
    mapping = verified.mapping
    expected_ref = f"{mapping.repository}/{mapping.bootstrap_workflow_path}@refs/heads/main"
    valid = (
        provenance.repository == mapping.repository
        and provenance.workflow_id > 0
        and provenance.workflow_path == mapping.bootstrap_workflow_path
        and provenance.workflow_ref == expected_ref
        and provenance.workflow_sha == mapping.bootstrap_commit
        and provenance.workflow_blob_id == mapping.bootstrap_workflow_blob_id
        and provenance.workflow_content_id == mapping.bootstrap_workflow_content_id
        and provenance.run_id > 0
        and provenance.run_attempt > 0
        and provenance.event_name == "workflow_dispatch"
        and provenance.dispatch_ref == "refs/heads/main"
        and _GIT_ID.fullmatch(provenance.github_sha) is not None
        and provenance.qualified_source_commit == mapping.qualified_source_commit
        and provenance.qualified_source_tree == mapping.qualified_source_tree
        and provenance.source_stage_a_workflow_content_id
        == mapping.source_stage_a_workflow_content_id
    )
    if not valid:
        raise _fail("CAMPAIGN02_BOOTSTRAP_RUNTIME_PROVENANCE_INVALID")


@dataclass(frozen=True, slots=True)
class RawGitHubApiSnapshot:
    endpoint: str
    status_code: int
    response_bytes: bytes
    response_sha256: str

    @classmethod
    def from_dict(cls, value: object) -> RawGitHubApiSnapshot:
        fields = {"endpoint", "response_base64", "response_sha256", "status_code"}
        if not isinstance(value, dict) or set(value) != fields:
            raise _fail("CAMPAIGN02_REGISTRATION_API_SNAPSHOT_FIELDS_INVALID")
        endpoint = value["endpoint"]
        status_code = value["status_code"]
        if (
            not isinstance(endpoint, str)
            or not endpoint.startswith("https://api.github.com/repos/")
            or status_code != 200
        ):
            raise _fail("CAMPAIGN02_REGISTRATION_API_SNAPSHOT_HEADER_INVALID")
        response = _canonical_base64(
            value["response_base64"], "CAMPAIGN02_REGISTRATION_API_SNAPSHOT_BYTES_INVALID"
        )
        response_sha256 = _content_id(
            value["response_sha256"], "CAMPAIGN02_REGISTRATION_API_SNAPSHOT_DIGEST_INVALID"
        )
        if not response or sha256_content_id(response) != response_sha256:
            raise _fail("CAMPAIGN02_REGISTRATION_API_SNAPSHOT_DIGEST_MISMATCH")
        return cls(endpoint, 200, response, response_sha256)

    @property
    def document(self) -> dict[str, object]:
        return {
            "endpoint": self.endpoint,
            "response_base64": base64.b64encode(self.response_bytes).decode("ascii"),
            "response_sha256": self.response_sha256,
            "status_code": self.status_code,
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(_API_SNAPSHOT_DOMAIN + canonical_json_bytes(self.document))

    def json_object(self) -> dict[str, object]:
        try:
            value = json.loads(self.response_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise _fail("CAMPAIGN02_REGISTRATION_API_RESPONSE_INVALID") from exc
        if not isinstance(value, dict):
            raise _fail("CAMPAIGN02_REGISTRATION_API_RESPONSE_INVALID")
        return value


@dataclass(frozen=True, slots=True)
class WorkflowRegistrationApiEvidence:
    repository: str
    collected_at: datetime
    workflow_metadata: RawGitHubApiSnapshot
    default_branch_ref: RawGitHubApiSnapshot
    bootstrap_workflow_file: RawGitHubApiSnapshot
    registration_workflow_run: RawGitHubApiSnapshot
    registration_artifact_metadata: RawGitHubApiSnapshot

    @classmethod
    def from_dict(cls, value: object) -> WorkflowRegistrationApiEvidence:
        fields = {
            "collected_at",
            "execution_authorized",
            "formal_semantics_id",
            "repository",
            "schema_version",
            "snapshots",
            "type_name",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise _fail("CAMPAIGN02_REGISTRATION_API_EVIDENCE_FIELDS_INVALID")
        repository = value["repository"]
        try:
            collected_at = datetime.fromisoformat(str(value["collected_at"]))
        except ValueError as exc:
            raise _fail("CAMPAIGN02_REGISTRATION_API_EVIDENCE_TIME_INVALID") from exc
        snapshots = value["snapshots"]
        names = {
            "bootstrap_workflow_file",
            "default_branch_ref",
            "registration_artifact_metadata",
            "registration_workflow_run",
            "workflow_metadata",
        }
        if (
            value["type_name"] != "CAMPAIGN02_WORKFLOW_REGISTRATION_API_EVIDENCE"
            or value["schema_version"] != "1.0.0"
            or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
            or value["execution_authorized"] is not False
            or not isinstance(repository, str)
            or _REPOSITORY.fullmatch(repository) is None
            or collected_at.tzinfo is None
            or not isinstance(snapshots, dict)
            or set(snapshots) != names
        ):
            raise _fail("CAMPAIGN02_REGISTRATION_API_EVIDENCE_HEADER_INVALID")
        return cls(
            repository=repository,
            collected_at=collected_at,
            workflow_metadata=RawGitHubApiSnapshot.from_dict(snapshots["workflow_metadata"]),
            default_branch_ref=RawGitHubApiSnapshot.from_dict(snapshots["default_branch_ref"]),
            bootstrap_workflow_file=RawGitHubApiSnapshot.from_dict(
                snapshots["bootstrap_workflow_file"]
            ),
            registration_workflow_run=RawGitHubApiSnapshot.from_dict(
                snapshots["registration_workflow_run"]
            ),
            registration_artifact_metadata=RawGitHubApiSnapshot.from_dict(
                snapshots["registration_artifact_metadata"]
            ),
        )

    @property
    def document(self) -> dict[str, object]:
        return {
            "collected_at": self.collected_at.isoformat(),
            "execution_authorized": False,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "repository": self.repository,
            "schema_version": "1.0.0",
            "snapshots": {
                "bootstrap_workflow_file": self.bootstrap_workflow_file.document,
                "default_branch_ref": self.default_branch_ref.document,
                "registration_artifact_metadata": self.registration_artifact_metadata.document,
                "registration_workflow_run": self.registration_workflow_run.document,
                "workflow_metadata": self.workflow_metadata.document,
            },
            "type_name": "CAMPAIGN02_WORKFLOW_REGISTRATION_API_EVIDENCE",
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(_API_EVIDENCE_DOMAIN + canonical_json_bytes(self.document))


@dataclass(frozen=True, slots=True)
class WorkflowRegistrationReceipt:
    repository: str
    workflow_id: int
    workflow_path: str
    workflow_state: str
    default_branch_ref: str
    bootstrap_mapping_id: str
    bootstrap_commit: str
    bootstrap_workflow_blob_id: str
    bootstrap_workflow_content_id: str
    qualified_source_commit: str
    qualified_source_tree: str
    api_evidence_root: str
    registration_workflow_id: int
    registration_run_id: int
    registration_run_attempt: int
    registration_run_event: str
    registration_run_head_sha: str
    registration_run_ref: str
    registration_run_status: str
    registration_run_conclusion: str
    registration_run_created_at: datetime
    registration_run_updated_at: datetime
    registration_run_completed_at: datetime
    registration_artifact_id: int
    registration_artifact_name: str
    registration_artifact_archive_digest: str
    registration_artifact_created_at: datetime
    registration_artifact_expires_at: datetime
    checked_at: datetime

    @classmethod
    def from_dict(cls, value: object) -> WorkflowRegistrationReceipt:
        fields = {
            "authority_bundle_supplied",
            "api_evidence_root",
            "bootstrap_commit",
            "bootstrap_commit_on_default_branch",
            "bootstrap_mapping_id",
            "bootstrap_workflow_blob_id",
            "bootstrap_workflow_content_id",
            "checked_at",
            "default_branch_ref",
            "formal_semantics_id",
            "execution_artifact_count",
            "execution_count",
            "observation_count",
            "qualified_source_commit",
            "qualified_source_exists",
            "qualified_source_tree",
            "repository",
            "registration_artifact_archive_digest",
            "registration_artifact_created_at",
            "registration_artifact_expires_at",
            "registration_artifact_id",
            "registration_artifact_name",
            "registration_run_attempt",
            "registration_run_completed_at",
            "registration_run_conclusion",
            "registration_run_created_at",
            "registration_run_event",
            "registration_run_head_sha",
            "registration_run_id",
            "registration_run_ref",
            "registration_run_status",
            "registration_run_updated_at",
            "registration_workflow_id",
            "schema_version",
            "stage_a_plans_executed",
            "stage_gate_receipt_emitted",
            "type_name",
            "workflow_id",
            "workflow_path",
            "workflow_state",
            "workflow_visible_on_default_branch",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise _fail("CAMPAIGN02_WORKFLOW_REGISTRATION_FIELDS_INVALID")
        checked_at = _timestamp(
            value["checked_at"], "CAMPAIGN02_WORKFLOW_REGISTRATION_TIME_INVALID"
        )
        run_created_at = _timestamp(
            value["registration_run_created_at"],
            "CAMPAIGN02_WORKFLOW_REGISTRATION_RUN_TIME_INVALID",
        )
        run_updated_at = _timestamp(
            value["registration_run_updated_at"],
            "CAMPAIGN02_WORKFLOW_REGISTRATION_RUN_TIME_INVALID",
        )
        run_completed_at = _timestamp(
            value["registration_run_completed_at"],
            "CAMPAIGN02_WORKFLOW_REGISTRATION_RUN_TIME_INVALID",
        )
        artifact_created_at = _timestamp(
            value["registration_artifact_created_at"],
            "CAMPAIGN02_WORKFLOW_REGISTRATION_ARTIFACT_TIME_INVALID",
        )
        artifact_expires_at = _timestamp(
            value["registration_artifact_expires_at"],
            "CAMPAIGN02_WORKFLOW_REGISTRATION_ARTIFACT_TIME_INVALID",
        )
        workflow_id = value["workflow_id"]
        registration_run_attempt = _positive_int(
            value["registration_run_attempt"],
            "CAMPAIGN02_WORKFLOW_REGISTRATION_RUN_ATTEMPT_INVALID",
        )
        registration_artifact_name = value["registration_artifact_name"]
        stop_counts = (
            value["execution_artifact_count"],
            value["execution_count"],
            value["observation_count"],
            value["stage_a_plans_executed"],
        )
        if (
            value["type_name"] != "CAMPAIGN02_WORKFLOW_REGISTRATION_RECEIPT"
            or value["schema_version"] != "3.0.0"
            or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
            or value["workflow_visible_on_default_branch"] is not True
            or value["bootstrap_commit_on_default_branch"] is not True
            or value["qualified_source_exists"] is not True
            or value["authority_bundle_supplied"] is not False
            or value["stage_gate_receipt_emitted"] is not False
            or any(
                isinstance(item, bool) or not isinstance(item, int) or item != 0
                for item in stop_counts
            )
            or value["workflow_state"] != "active"
            or value["default_branch_ref"] != "refs/heads/main"
            or isinstance(workflow_id, bool)
            or not isinstance(workflow_id, int)
            or workflow_id <= 0
            or value["registration_run_status"] != "completed"
            or value["registration_run_conclusion"] != "success"
            or not isinstance(registration_artifact_name, str)
            or _ARTIFACT_NAME.fullmatch(registration_artifact_name) is None
            or not registration_artifact_name.endswith(f"-attempt-{registration_run_attempt}")
            or not (run_created_at <= run_updated_at <= run_completed_at <= checked_at)
            or artifact_created_at > checked_at
            or artifact_expires_at <= checked_at
        ):
            raise _fail("CAMPAIGN02_WORKFLOW_REGISTRATION_STOP_INVALID")
        repository = value["repository"]
        workflow_path = value["workflow_path"]
        if (
            not isinstance(repository, str)
            or _REPOSITORY.fullmatch(repository) is None
            or not isinstance(workflow_path, str)
            or _WORKFLOW_PATH.fullmatch(workflow_path) is None
            or value["registration_run_event"] != "workflow_dispatch"
            or value["registration_run_ref"] != "refs/heads/main"
        ):
            raise _fail("CAMPAIGN02_WORKFLOW_REGISTRATION_HEADER_INVALID")
        return cls(
            repository=repository,
            workflow_id=workflow_id,
            workflow_path=workflow_path,
            workflow_state="active",
            default_branch_ref="refs/heads/main",
            bootstrap_mapping_id=_content_id(
                value["bootstrap_mapping_id"],
                "CAMPAIGN02_WORKFLOW_REGISTRATION_MAPPING_ID_INVALID",
            ),
            bootstrap_commit=_git_id(
                value["bootstrap_commit"],
                "CAMPAIGN02_WORKFLOW_REGISTRATION_COMMIT_INVALID",
            ),
            bootstrap_workflow_blob_id=_git_id(
                value["bootstrap_workflow_blob_id"],
                "CAMPAIGN02_WORKFLOW_REGISTRATION_BLOB_INVALID",
            ),
            bootstrap_workflow_content_id=_content_id(
                value["bootstrap_workflow_content_id"],
                "CAMPAIGN02_WORKFLOW_REGISTRATION_WORKFLOW_ID_INVALID",
            ),
            qualified_source_commit=_git_id(
                value["qualified_source_commit"],
                "CAMPAIGN02_WORKFLOW_REGISTRATION_SOURCE_COMMIT_INVALID",
            ),
            qualified_source_tree=_git_id(
                value["qualified_source_tree"],
                "CAMPAIGN02_WORKFLOW_REGISTRATION_SOURCE_TREE_INVALID",
            ),
            api_evidence_root=_content_id(
                value["api_evidence_root"],
                "CAMPAIGN02_WORKFLOW_REGISTRATION_API_ROOT_INVALID",
            ),
            registration_workflow_id=_positive_int(
                value["registration_workflow_id"],
                "CAMPAIGN02_WORKFLOW_REGISTRATION_RUN_WORKFLOW_INVALID",
            ),
            registration_run_id=_positive_int(
                value["registration_run_id"],
                "CAMPAIGN02_WORKFLOW_REGISTRATION_RUN_ID_INVALID",
            ),
            registration_run_attempt=registration_run_attempt,
            registration_run_event=str(value["registration_run_event"]),
            registration_run_head_sha=_git_id(
                value["registration_run_head_sha"],
                "CAMPAIGN02_WORKFLOW_REGISTRATION_RUN_HEAD_INVALID",
            ),
            registration_run_ref=str(value["registration_run_ref"]),
            registration_run_status="completed",
            registration_run_conclusion="success",
            registration_run_created_at=run_created_at,
            registration_run_updated_at=run_updated_at,
            registration_run_completed_at=run_completed_at,
            registration_artifact_id=_positive_int(
                value["registration_artifact_id"],
                "CAMPAIGN02_WORKFLOW_REGISTRATION_ARTIFACT_ID_INVALID",
            ),
            registration_artifact_name=registration_artifact_name,
            registration_artifact_archive_digest=_content_id(
                value["registration_artifact_archive_digest"],
                "CAMPAIGN02_WORKFLOW_REGISTRATION_ARTIFACT_DIGEST_INVALID",
            ),
            registration_artifact_created_at=artifact_created_at,
            registration_artifact_expires_at=artifact_expires_at,
            checked_at=checked_at,
        )

    @property
    def document(self) -> dict[str, object]:
        return {
            "authority_bundle_supplied": False,
            "api_evidence_root": self.api_evidence_root,
            "bootstrap_commit": self.bootstrap_commit,
            "bootstrap_commit_on_default_branch": True,
            "bootstrap_mapping_id": self.bootstrap_mapping_id,
            "bootstrap_workflow_blob_id": self.bootstrap_workflow_blob_id,
            "bootstrap_workflow_content_id": self.bootstrap_workflow_content_id,
            "checked_at": self.checked_at.isoformat(),
            "default_branch_ref": self.default_branch_ref,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "execution_artifact_count": 0,
            "execution_count": 0,
            "observation_count": 0,
            "qualified_source_commit": self.qualified_source_commit,
            "qualified_source_exists": True,
            "qualified_source_tree": self.qualified_source_tree,
            "repository": self.repository,
            "registration_artifact_archive_digest": self.registration_artifact_archive_digest,
            "registration_artifact_created_at": self.registration_artifact_created_at.isoformat(),
            "registration_artifact_expires_at": self.registration_artifact_expires_at.isoformat(),
            "registration_artifact_id": self.registration_artifact_id,
            "registration_artifact_name": self.registration_artifact_name,
            "registration_run_attempt": self.registration_run_attempt,
            "registration_run_completed_at": self.registration_run_completed_at.isoformat(),
            "registration_run_conclusion": self.registration_run_conclusion,
            "registration_run_created_at": self.registration_run_created_at.isoformat(),
            "registration_run_event": self.registration_run_event,
            "registration_run_head_sha": self.registration_run_head_sha,
            "registration_run_id": self.registration_run_id,
            "registration_run_ref": self.registration_run_ref,
            "registration_run_status": self.registration_run_status,
            "registration_run_updated_at": self.registration_run_updated_at.isoformat(),
            "registration_workflow_id": self.registration_workflow_id,
            "schema_version": "3.0.0",
            "stage_a_plans_executed": 0,
            "stage_gate_receipt_emitted": False,
            "type_name": "CAMPAIGN02_WORKFLOW_REGISTRATION_RECEIPT",
            "workflow_id": self.workflow_id,
            "workflow_path": self.workflow_path,
            "workflow_state": self.workflow_state,
            "workflow_visible_on_default_branch": True,
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(_REGISTRATION_DOMAIN + canonical_json_bytes(self.document))


@dataclass(frozen=True, slots=True)
class SignedWorkflowRegistrationVote:
    registration_receipt_id: str
    api_evidence_root: str
    mapping_id: str
    validator_set_id: str
    registration_run_status: str
    registration_run_conclusion: str
    registration_run_created_at: datetime
    registration_run_updated_at: datetime
    registration_run_completed_at: datetime
    registration_artifact_name: str
    registration_artifact_created_at: datetime
    registration_artifact_expires_at: datetime
    signer_id: str
    submitted_at: datetime
    signature: bytes

    @classmethod
    def from_dict(cls, value: object) -> SignedWorkflowRegistrationVote:
        fields = {
            "api_evidence_root",
            "formal_semantics_id",
            "mapping_id",
            "registration_receipt_id",
            "registration_run_completed_at",
            "registration_run_conclusion",
            "registration_run_created_at",
            "registration_run_status",
            "registration_run_updated_at",
            "registration_artifact_name",
            "registration_artifact_created_at",
            "registration_artifact_expires_at",
            "schema_version",
            "signature_base64",
            "signer_id",
            "submitted_at",
            "type_name",
            "validator_set_id",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise _fail("CAMPAIGN02_WORKFLOW_REGISTRATION_SIGNATURE_FIELDS_INVALID")
        signer_id = value["signer_id"]
        submitted_at = _timestamp(
            value["submitted_at"],
            "CAMPAIGN02_WORKFLOW_REGISTRATION_SIGNATURE_TIME_INVALID",
        )
        run_created_at = _timestamp(
            value["registration_run_created_at"],
            "CAMPAIGN02_WORKFLOW_REGISTRATION_SIGNATURE_TIME_INVALID",
        )
        run_updated_at = _timestamp(
            value["registration_run_updated_at"],
            "CAMPAIGN02_WORKFLOW_REGISTRATION_SIGNATURE_TIME_INVALID",
        )
        run_completed_at = _timestamp(
            value["registration_run_completed_at"],
            "CAMPAIGN02_WORKFLOW_REGISTRATION_SIGNATURE_TIME_INVALID",
        )
        artifact_created_at = _timestamp(
            value["registration_artifact_created_at"],
            "CAMPAIGN02_WORKFLOW_REGISTRATION_SIGNATURE_TIME_INVALID",
        )
        artifact_expires_at = _timestamp(
            value["registration_artifact_expires_at"],
            "CAMPAIGN02_WORKFLOW_REGISTRATION_SIGNATURE_TIME_INVALID",
        )
        if (
            value["type_name"] != "CAMPAIGN02_WORKFLOW_REGISTRATION_SIGNATURE"
            or value["schema_version"] != "2.0.0"
            or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
            or not isinstance(signer_id, str)
            or not signer_id
            or value["registration_run_status"] != "completed"
            or value["registration_run_conclusion"] != "success"
            or not isinstance(value["registration_artifact_name"], str)
            or _ARTIFACT_NAME.fullmatch(value["registration_artifact_name"]) is None
            or not (run_created_at <= run_updated_at <= run_completed_at <= submitted_at)
            or artifact_created_at > submitted_at
            or artifact_expires_at <= submitted_at
        ):
            raise _fail("CAMPAIGN02_WORKFLOW_REGISTRATION_SIGNATURE_HEADER_INVALID")
        signature = _canonical_base64(
            value["signature_base64"],
            "CAMPAIGN02_WORKFLOW_REGISTRATION_SIGNATURE_INVALID",
        )
        if len(signature) != 64:
            raise _fail("CAMPAIGN02_WORKFLOW_REGISTRATION_SIGNATURE_INVALID")
        return cls(
            registration_receipt_id=_content_id(
                value["registration_receipt_id"],
                "CAMPAIGN02_WORKFLOW_REGISTRATION_RECEIPT_ID_INVALID",
            ),
            api_evidence_root=_content_id(
                value["api_evidence_root"],
                "CAMPAIGN02_WORKFLOW_REGISTRATION_API_ROOT_INVALID",
            ),
            mapping_id=_content_id(
                value["mapping_id"], "CAMPAIGN02_WORKFLOW_REGISTRATION_MAPPING_ID_INVALID"
            ),
            validator_set_id=_content_id(
                value["validator_set_id"],
                "CAMPAIGN02_WORKFLOW_REGISTRATION_VALIDATOR_SET_ID_INVALID",
            ),
            registration_run_status="completed",
            registration_run_conclusion="success",
            registration_run_created_at=run_created_at,
            registration_run_updated_at=run_updated_at,
            registration_run_completed_at=run_completed_at,
            registration_artifact_name=value["registration_artifact_name"],
            registration_artifact_created_at=artifact_created_at,
            registration_artifact_expires_at=artifact_expires_at,
            signer_id=signer_id,
            submitted_at=submitted_at,
            signature=signature,
        )

    @property
    def message(self) -> bytes:
        artifact_created_at = self.registration_artifact_created_at.isoformat()
        artifact_expires_at = self.registration_artifact_expires_at.isoformat()
        return _REGISTRATION_SIGNATURE_DOMAIN + canonical_json_bytes(
            {
                "api_evidence_root": self.api_evidence_root,
                "mapping_id": self.mapping_id,
                "registration_receipt_id": self.registration_receipt_id,
                "registration_run_status": self.registration_run_status,
                "registration_run_conclusion": self.registration_run_conclusion,
                "registration_run_created_at": self.registration_run_created_at.isoformat(),
                "registration_run_updated_at": self.registration_run_updated_at.isoformat(),
                "registration_run_completed_at": self.registration_run_completed_at.isoformat(),
                "registration_artifact_name": self.registration_artifact_name,
                "registration_artifact_created_at": artifact_created_at,
                "registration_artifact_expires_at": artifact_expires_at,
                "signer_id": self.signer_id,
                "submitted_at": self.submitted_at.isoformat(),
                "validator_set_id": self.validator_set_id,
            }
        )

    @property
    def document(self) -> dict[str, object]:
        return {
            "api_evidence_root": self.api_evidence_root,
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "mapping_id": self.mapping_id,
            "registration_receipt_id": self.registration_receipt_id,
            "registration_run_status": self.registration_run_status,
            "registration_run_conclusion": self.registration_run_conclusion,
            "registration_run_created_at": self.registration_run_created_at.isoformat(),
            "registration_run_updated_at": self.registration_run_updated_at.isoformat(),
            "registration_run_completed_at": self.registration_run_completed_at.isoformat(),
            "registration_artifact_name": self.registration_artifact_name,
            "registration_artifact_created_at": self.registration_artifact_created_at.isoformat(),
            "registration_artifact_expires_at": self.registration_artifact_expires_at.isoformat(),
            "schema_version": "2.0.0",
            "signature_base64": base64.b64encode(self.signature).decode("ascii"),
            "signer_id": self.signer_id,
            "submitted_at": self.submitted_at.isoformat(),
            "type_name": "CAMPAIGN02_WORKFLOW_REGISTRATION_SIGNATURE",
            "validator_set_id": self.validator_set_id,
        }

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            _REGISTRATION_SIGNATURE_DOMAIN + canonical_json_bytes(self.document)
        )


@dataclass(frozen=True, slots=True, init=False)
class VerifiedWorkflowRegistration:
    receipt: WorkflowRegistrationReceipt
    api_evidence: WorkflowRegistrationApiEvidence
    validator_set_id: str
    signer_ids: tuple[str, ...]

    def __init__(
        self,
        token: object,
        receipt: WorkflowRegistrationReceipt,
        api_evidence: WorkflowRegistrationApiEvidence,
        validator_set_id: str,
        signer_ids: tuple[str, ...],
    ) -> None:
        if token is not _VERIFIED_REGISTRATION_TOKEN:
            raise _fail("CAMPAIGN02_VERIFIED_REGISTRATION_CONSTRUCTION_FORBIDDEN")
        object.__setattr__(self, "receipt", receipt)
        object.__setattr__(self, "api_evidence", api_evidence)
        object.__setattr__(self, "validator_set_id", validator_set_id)
        object.__setattr__(self, "signer_ids", signer_ids)

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            _REGISTRATION_ATTESTATION_DOMAIN
            + canonical_json_bytes(
                {
                    "api_evidence_root": self.api_evidence.content_id,
                    "execution_authorized": False,
                    "mapping_id": self.receipt.bootstrap_mapping_id,
                    "observation_count": 0,
                    "registration_receipt_id": self.receipt.content_id,
                    "signer_ids": list(self.signer_ids),
                    "validator_set_id": self.validator_set_id,
                }
            )
        )


def _api_file_bytes(value: object) -> bytes:
    if not isinstance(value, str):
        raise _fail("CAMPAIGN02_REGISTRATION_API_WORKFLOW_CONTENT_INVALID")
    normalized = "".join(value.split())
    try:
        return base64.b64decode(normalized, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise _fail("CAMPAIGN02_REGISTRATION_API_WORKFLOW_CONTENT_INVALID") from exc


def _git_blob_id(value: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(value)).encode("ascii") + b"\0" + value).hexdigest()


def _nested_dict(value: object, code: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise _fail(code)
    return value


def _verify_registration_api_evidence(
    mapping: WorkflowBootstrapMapping,
    receipt: WorkflowRegistrationReceipt,
    evidence: WorkflowRegistrationApiEvidence,
) -> None:
    if (
        evidence.repository != mapping.repository
        or receipt.api_evidence_root != evidence.content_id
        or evidence.collected_at > receipt.checked_at
    ):
        raise _fail("CAMPAIGN02_WORKFLOW_REGISTRATION_API_BINDING_MISMATCH")
    prefix = f"https://api.github.com/repos/{mapping.repository}"
    expected_endpoints = {
        evidence.workflow_metadata: f"{prefix}/actions/workflows/{receipt.workflow_id}",
        evidence.default_branch_ref: f"{prefix}/git/ref/heads/main",
        evidence.bootstrap_workflow_file: (
            f"{prefix}/contents/{mapping.bootstrap_workflow_path}?ref={mapping.bootstrap_commit}"
        ),
        evidence.registration_workflow_run: f"{prefix}/actions/runs/{receipt.registration_run_id}",
        evidence.registration_artifact_metadata: (
            f"{prefix}/actions/artifacts/{receipt.registration_artifact_id}"
        ),
    }
    if any(snapshot.endpoint != endpoint for snapshot, endpoint in expected_endpoints.items()):
        raise _fail("CAMPAIGN02_WORKFLOW_REGISTRATION_API_ENDPOINT_MISMATCH")

    workflow = evidence.workflow_metadata.json_object()
    default_ref = evidence.default_branch_ref.json_object()
    workflow_file = evidence.bootstrap_workflow_file.json_object()
    run = evidence.registration_workflow_run.json_object()
    artifact = evidence.registration_artifact_metadata.json_object()
    ref_object = _nested_dict(
        default_ref.get("object"), "CAMPAIGN02_WORKFLOW_REGISTRATION_API_DEFAULT_REF_INVALID"
    )
    run_repository = _nested_dict(
        run.get("repository"), "CAMPAIGN02_WORKFLOW_REGISTRATION_API_RUN_INVALID"
    )
    artifact_run = _nested_dict(
        artifact.get("workflow_run"), "CAMPAIGN02_WORKFLOW_REGISTRATION_API_ARTIFACT_INVALID"
    )
    workflow_bytes = _api_file_bytes(workflow_file.get("content"))
    run_created_at = _timestamp(
        run.get("created_at"), "CAMPAIGN02_WORKFLOW_REGISTRATION_API_RUN_TIME_INVALID"
    )
    run_updated_at = _timestamp(
        run.get("updated_at"), "CAMPAIGN02_WORKFLOW_REGISTRATION_API_RUN_TIME_INVALID"
    )
    # GitHub's workflow-run response exposes the terminal transition through
    # ``updated_at`` today.  Preserve an explicit completed-at security field,
    # and bind a future native ``completed_at`` field when the API supplies it.
    run_completed_at = _timestamp(
        run.get("completed_at", run.get("updated_at")),
        "CAMPAIGN02_WORKFLOW_REGISTRATION_API_RUN_TIME_INVALID",
    )
    artifact_created_at = _timestamp(
        artifact.get("created_at"),
        "CAMPAIGN02_WORKFLOW_REGISTRATION_API_ARTIFACT_TIME_INVALID",
    )
    artifact_expires_at = _timestamp(
        artifact.get("expires_at"),
        "CAMPAIGN02_WORKFLOW_REGISTRATION_API_ARTIFACT_TIME_INVALID",
    )
    valid = (
        workflow.get("id") == receipt.workflow_id
        and workflow.get("path") == mapping.bootstrap_workflow_path
        and workflow.get("state") == "active"
        and default_ref.get("ref") == "refs/heads/main"
        and ref_object.get("sha") == mapping.bootstrap_commit
        and workflow_file.get("path") == mapping.bootstrap_workflow_path
        and workflow_file.get("sha") == mapping.bootstrap_workflow_blob_id
        and workflow_file.get("encoding") == "base64"
        and _git_blob_id(workflow_bytes) == mapping.bootstrap_workflow_blob_id
        and sha256_content_id(workflow_bytes) == mapping.bootstrap_workflow_content_id
        and run.get("id") == receipt.registration_run_id
        and run.get("run_attempt") == receipt.registration_run_attempt
        and run.get("workflow_id") == receipt.registration_workflow_id
        and run.get("workflow_id") == receipt.workflow_id
        and run.get("event") == "workflow_dispatch"
        and run.get("status") == "completed"
        and run.get("conclusion") == "success"
        and run.get("head_sha") == mapping.bootstrap_commit
        and run.get("head_branch") == "main"
        and run.get("path") == mapping.bootstrap_workflow_path
        and run_repository.get("full_name") == mapping.repository
        and artifact.get("id") == receipt.registration_artifact_id
        and artifact.get("name") == receipt.registration_artifact_name
        and artifact.get("expired") is False
        and artifact.get("digest") == receipt.registration_artifact_archive_digest
        and artifact_run.get("id") == receipt.registration_run_id
        and artifact_run.get("head_sha") == mapping.bootstrap_commit
        and artifact_run.get("head_branch") == "main"
        and receipt.registration_run_event == "workflow_dispatch"
        and receipt.registration_run_head_sha == mapping.bootstrap_commit
        and receipt.registration_run_ref == "refs/heads/main"
        and receipt.registration_run_status == "completed"
        and receipt.registration_run_conclusion == "success"
        and receipt.registration_run_created_at == run_created_at
        and receipt.registration_run_updated_at == run_updated_at
        and receipt.registration_run_completed_at == run_completed_at
        and receipt.registration_artifact_created_at == artifact_created_at
        and receipt.registration_artifact_expires_at == artifact_expires_at
        and run_completed_at <= receipt.checked_at
        and artifact_created_at <= receipt.checked_at
        and receipt.checked_at < artifact_expires_at
    )
    if not valid:
        raise _fail("CAMPAIGN02_WORKFLOW_REGISTRATION_API_SEMANTICS_INVALID")


def verify_registration_receipt(
    verified: VerifiedBootstrapMapping,
    receipt: WorkflowRegistrationReceipt,
    *,
    api_evidence: WorkflowRegistrationApiEvidence,
    validator_set: BootstrapValidatorSet,
    votes: tuple[SignedWorkflowRegistrationVote, ...],
) -> VerifiedWorkflowRegistration:
    if (
        WorkflowRegistrationReceipt.from_dict(receipt.document) != receipt
        or WorkflowRegistrationApiEvidence.from_dict(api_evidence.document) != api_evidence
        or any(SignedWorkflowRegistrationVote.from_dict(vote.document) != vote for vote in votes)
    ):
        raise _fail("CAMPAIGN02_WORKFLOW_REGISTRATION_CANONICAL_OBJECT_INVALID")
    mapping = verified.mapping
    if (
        receipt.bootstrap_mapping_id != mapping.content_id
        or receipt.repository != mapping.repository
        or receipt.workflow_path != mapping.bootstrap_workflow_path
        or receipt.bootstrap_commit != mapping.bootstrap_commit
        or receipt.bootstrap_workflow_blob_id != mapping.bootstrap_workflow_blob_id
        or receipt.bootstrap_workflow_content_id != mapping.bootstrap_workflow_content_id
        or receipt.qualified_source_commit != mapping.qualified_source_commit
        or receipt.qualified_source_tree != mapping.qualified_source_tree
    ):
        raise _fail("CAMPAIGN02_WORKFLOW_REGISTRATION_BINDING_MISMATCH")
    _verify_registration_api_evidence(mapping, receipt, api_evidence)
    if validator_set.content_id != verified.validator_set_id:
        raise _fail("CAMPAIGN02_WORKFLOW_REGISTRATION_VALIDATOR_SET_MISMATCH")
    if len(votes) != validator_set.quorum_threshold:
        raise _fail("CAMPAIGN02_WORKFLOW_REGISTRATION_SIGNATURE_QUORUM_INVALID")
    signer_ids: list[str] = []
    controllers: list[str] = []
    for vote in votes:
        if (
            vote.registration_receipt_id != receipt.content_id
            or vote.api_evidence_root != api_evidence.content_id
            or vote.mapping_id != mapping.content_id
            or vote.validator_set_id != validator_set.content_id
            or vote.registration_run_status != receipt.registration_run_status
            or vote.registration_run_conclusion != receipt.registration_run_conclusion
            or vote.registration_run_created_at != receipt.registration_run_created_at
            or vote.registration_run_updated_at != receipt.registration_run_updated_at
            or vote.registration_run_completed_at != receipt.registration_run_completed_at
            or vote.registration_artifact_name != receipt.registration_artifact_name
            or vote.registration_artifact_created_at != receipt.registration_artifact_created_at
            or vote.registration_artifact_expires_at != receipt.registration_artifact_expires_at
            or vote.submitted_at < receipt.checked_at
        ):
            raise _fail("CAMPAIGN02_WORKFLOW_REGISTRATION_SIGNATURE_BINDING_MISMATCH")
        validator = validator_set.validator(vote.signer_id)
        try:
            Ed25519PublicKey.from_public_bytes(validator.public_key).verify(
                vote.signature, vote.message
            )
        except InvalidSignature as exc:
            raise _fail("CAMPAIGN02_WORKFLOW_REGISTRATION_SIGNATURE_INVALID") from exc
        signer_ids.append(vote.signer_id)
        controllers.append(validator.controller_id)
    if len(set(signer_ids)) != len(signer_ids) or len(set(controllers)) != len(controllers):
        raise _fail("CAMPAIGN02_WORKFLOW_REGISTRATION_SIGNATURE_DUPLICATE")
    return VerifiedWorkflowRegistration(
        _VERIFIED_REGISTRATION_TOKEN,
        receipt,
        api_evidence,
        validator_set.content_id,
        tuple(sorted(signer_ids)),
    )
