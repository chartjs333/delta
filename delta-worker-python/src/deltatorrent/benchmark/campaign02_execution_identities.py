"""Strict recursive verification for Campaign 02 stage execution identities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

_CONTENT_ID: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_ID: Final = re.compile(r"^[0-9a-f]{40}$")
_MANIFEST_DOMAIN: Final = b"deltareduce.010.campaign02-stage-execution-identities.v2\0"
_IDENTITY_DOMAINS: Final = {
    "evaluation_runner": "deltareduce.010.primary-component.v1",
    "exactness_runner": "deltareduce.010.campaign02-stage-role-identity.v2",
    "multi_role_runner": "deltareduce.010.campaign02-multi-role-runner.v2",
    "native_feature008_verifier": "deltareduce.010.campaign02-native-feature008-verifier.v2",
    "network_fault_runner": "deltareduce.010.campaign02-stage-role-identity.v2",
    "observation_writer": "deltareduce.010.primary-component.v1",
    "scientific_runner": "deltareduce.010.primary-component.v1",
    "signed_stage_authorization_verifier": (
        "deltareduce.010.campaign02-signed-stage-authorization-verifier.v2"
    ),
    "stage_gate_analyzer": "deltareduce.010.campaign02-stage-gate-analyzer.v2",
    "typed_gate_receipt_verifier": (
        "deltareduce.010.campaign02-typed-stage-gate-receipt-verifier.v2"
    ),
}


class StageExecutionIdentityError(ValueError):
    """Stable fail-closed stage identity rejection."""


def _fail(code: str) -> StageExecutionIdentityError:
    return StageExecutionIdentityError(code)


def _verify_source_bound(value: object, source_commit: str, source_tree: str) -> None:
    if isinstance(value, dict):
        if "source_commit" in value and value["source_commit"] != source_commit:
            raise _fail("CAMPAIGN02_STAGE_IDENTITY_SOURCE_COMMIT_MISMATCH")
        if "source_tree" in value and value["source_tree"] != source_tree:
            raise _fail("CAMPAIGN02_STAGE_IDENTITY_SOURCE_TREE_MISMATCH")
        if "execution_authorized" in value and value["execution_authorized"] is not False:
            raise _fail("CAMPAIGN02_STAGE_IDENTITY_EXECUTION_FLAG_INVALID")
        for item in value.values():
            _verify_source_bound(item, source_commit, source_tree)
    elif isinstance(value, list):
        for item in value:
            _verify_source_bound(item, source_commit, source_tree)


@dataclass(frozen=True, slots=True)
class StageExecutionIdentity:
    name: str
    identity_domain: str
    content_id: str
    value: dict[str, object]


@dataclass(frozen=True, slots=True)
class StageExecutionIdentityManifest:
    source_commit: str
    source_tree: str
    identities: tuple[StageExecutionIdentity, ...]
    raw: dict[str, object]

    @classmethod
    def from_dict(cls, value: object) -> StageExecutionIdentityManifest:
        fields = {
            "campaign_id",
            "execution_authorized",
            "formal_semantics_id",
            "identities",
            "schema_version",
            "source_commit",
            "source_tree",
            "type_name",
        }
        if not isinstance(value, dict) or set(value) != fields:
            raise _fail("CAMPAIGN02_STAGE_IDENTITY_MANIFEST_FIELDS_INVALID")
        source_commit = value["source_commit"]
        source_tree = value["source_tree"]
        if (
            value["type_name"] != "CAMPAIGN02_STAGE_EXECUTION_IDENTITIES"
            or value["schema_version"] != "2.0.0"
            or value["campaign_id"] != "campaign-02"
            or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
            or value["execution_authorized"] is not False
            or not isinstance(source_commit, str)
            or not isinstance(source_tree, str)
            or _COMMIT_ID.fullmatch(source_commit) is None
            or _COMMIT_ID.fullmatch(source_tree) is None
        ):
            raise _fail("CAMPAIGN02_STAGE_IDENTITY_MANIFEST_HEADER_INVALID")
        raw_identities = value["identities"]
        if not isinstance(raw_identities, dict) or set(raw_identities) != set(_IDENTITY_DOMAINS):
            raise _fail("CAMPAIGN02_STAGE_IDENTITY_SET_INVALID")
        identities: list[StageExecutionIdentity] = []
        for name in sorted(_IDENTITY_DOMAINS):
            raw_identity = raw_identities[name]
            if not isinstance(raw_identity, dict) or set(raw_identity) != {
                "content_id",
                "identity_domain",
                "value",
            }:
                raise _fail("CAMPAIGN02_STAGE_IDENTITY_FIELDS_INVALID")
            identity_domain = raw_identity["identity_domain"]
            identity_value = raw_identity["value"]
            content_id = raw_identity["content_id"]
            if (
                identity_domain != _IDENTITY_DOMAINS[name]
                or not isinstance(identity_value, dict)
                or not isinstance(content_id, str)
                or _CONTENT_ID.fullmatch(content_id) is None
                or sha256_content_id(
                    str(identity_domain).encode() + b"\0" + canonical_json_bytes(identity_value)
                )
                != content_id
            ):
                raise _fail("CAMPAIGN02_STAGE_IDENTITY_CONTENT_ID_INVALID")
            _verify_source_bound(identity_value, source_commit, source_tree)
            identities.append(
                StageExecutionIdentity(name, str(identity_domain), content_id, identity_value)
            )
        result = cls(source_commit, source_tree, tuple(identities), dict(value))
        result._verify_roles()
        return result

    def _verify_roles(self) -> None:
        exactness = self.identity("exactness_runner").value
        scientific = self.identity("scientific_runner").value
        network = self.identity("network_fault_runner").value
        multi_role = self.identity("multi_role_runner").value
        exactness_entrypoints = exactness.get("entrypoints")
        network_entrypoints = network.get("entrypoints")
        if (
            exactness.get("allowed_role") != "EXACTNESS_RUNNER"
            or not isinstance(exactness_entrypoints, list)
            or "deltatorrent.benchmark.campaign02_exactness.run_stage_a"
            not in exactness_entrypoints
        ):
            raise _fail("CAMPAIGN02_EXACTNESS_EXECUTOR_IDENTITY_INVALID")
        if scientific.get("component") != "PRIMARY_SCIENTIFIC_RUNNER":
            raise _fail("CAMPAIGN02_SCIENTIFIC_EXECUTOR_IDENTITY_INVALID")
        if (
            network.get("allowed_role") != "NETWORK_FAULT_RUNNER"
            or not isinstance(network_entrypoints, list)
            or "deltatorrent.benchmark.campaign02_network_fault.run_stage_c"
            not in network_entrypoints
        ):
            raise _fail("CAMPAIGN02_NETWORK_FAULT_EXECUTOR_IDENTITY_INVALID")
        role_ids = multi_role.get("role_identity_ids")
        if not isinstance(role_ids, dict) or role_ids != {
            "EXACTNESS_RUNNER": self.identity_id("exactness_runner"),
            "NETWORK_FAULT_RUNNER": self.identity_id("network_fault_runner"),
            "SCIENTIFIC_RUNNER": self.identity_id("scientific_runner"),
        }:
            raise _fail("CAMPAIGN02_MULTI_ROLE_METADATA_INVALID")
        if "entrypoints" in multi_role:
            raise _fail("CAMPAIGN02_MULTI_ROLE_METADATA_MUST_NOT_BE_EXECUTABLE")

    def identity(self, name: str) -> StageExecutionIdentity:
        matches = tuple(item for item in self.identities if item.name == name)
        if len(matches) != 1:
            raise _fail("CAMPAIGN02_STAGE_IDENTITY_MISSING")
        return matches[0]

    def identity_id(self, name: str) -> str:
        return self.identity(name).content_id

    @property
    def content_id(self) -> str:
        return sha256_content_id(_MANIFEST_DOMAIN + canonical_json_bytes(self.raw))
