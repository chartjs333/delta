"""Immutable default-branch bootstrap binding for Campaign 02 Stage A.

The mapping is registration metadata, never execution authority.  Its detached
signatures prove only that an exact default-branch workflow may dispatch an
exact qualified source.  Stage execution still requires the independent
C2-024 authorization proof.
"""

from __future__ import annotations

import base64
import binascii
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
_MAPPING_DOMAIN: Final = b"deltareduce.010.campaign02-workflow-bootstrap-mapping.v1\0"
_VALIDATOR_SET_DOMAIN: Final = b"deltareduce.010.campaign02-workflow-bootstrap-validator-set.v1\0"
_SIGNATURE_DOMAIN: Final = b"deltareduce.010.campaign02-workflow-bootstrap-signature.v1\0"
_ATTESTATION_DOMAIN: Final = b"deltareduce.010.campaign02-workflow-bootstrap-attestation.v1\0"


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
    definition_id: str

    @classmethod
    def from_dict(cls, value: object) -> WorkflowBootstrapMapping:
        fields = {
            "bootstrap_commit",
            "bootstrap_workflow_blob_id",
            "bootstrap_workflow_content_id",
            "bootstrap_workflow_path",
            "definition_id",
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
            definition_id=_content_id(
                value["definition_id"], "CAMPAIGN02_BOOTSTRAP_DEFINITION_ID_INVALID"
            ),
        )

    @property
    def document(self) -> dict[str, object]:
        return {
            "bootstrap_commit": self.bootstrap_commit,
            "bootstrap_workflow_blob_id": self.bootstrap_workflow_blob_id,
            "bootstrap_workflow_content_id": self.bootstrap_workflow_content_id,
            "bootstrap_workflow_path": self.bootstrap_workflow_path,
            "definition_id": self.definition_id,
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
    quorum_threshold: int

    @classmethod
    def from_dict(cls, value: object) -> BootstrapValidatorSet:
        fields = {
            "execution_authorized",
            "formal_semantics_id",
            "quorum_threshold",
            "schema_version",
            "type_name",
            "validators",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise _fail("CAMPAIGN02_BOOTSTRAP_VALIDATOR_SET_FIELDS_INVALID")
        raw_validators = value["validators"]
        threshold = value["quorum_threshold"]
        if (
            value["type_name"] != "CAMPAIGN02_WORKFLOW_BOOTSTRAP_VALIDATOR_SET"
            or value["schema_version"] != "1.0.0"
            or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
            or value["execution_authorized"] is not False
            or not isinstance(raw_validators, list)
            or not raw_validators
            or isinstance(threshold, bool)
            or not isinstance(threshold, int)
            or threshold <= 0
            or threshold > len(raw_validators)
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
        return cls(tuple(sorted(validators, key=lambda item: item.signer_id)), threshold)

    @property
    def document(self) -> dict[str, object]:
        return {
            "execution_authorized": False,
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


@dataclass(frozen=True, slots=True)
class VerifiedBootstrapMapping:
    mapping: WorkflowBootstrapMapping
    validator_set_id: str
    signer_ids: tuple[str, ...]

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
        mapping=mapping,
        validator_set_id=validator_set.content_id,
        signer_ids=tuple(sorted(signer_ids)),
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
