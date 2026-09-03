"""Strict recursive verification for Campaign 02 stage execution identities."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

_CONTENT_ID: Final = re.compile(r"^sha256:[0-9a-f]{64}$")
_COMMIT_ID: Final = re.compile(r"^[0-9a-f]{40}$")
_MANIFEST_DOMAINS: Final = {
    "2.0.0": b"deltareduce.010.campaign02-stage-execution-identities.v2\0",
    "3.0.0": b"deltareduce.010.campaign02-stage-execution-identities.v3\0",
    "4.0.0": b"deltareduce.010.campaign02-stage-execution-identities.v4\0",
}
_IDENTITY_DOMAINS_V2: Final = {
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
_IDENTITY_DOMAINS_V3: Final = {
    **_IDENTITY_DOMAINS_V2,
    "exactness_runner": "deltareduce.010.campaign02-stage-role-identity.v3",
    "multi_role_runner": "deltareduce.010.campaign02-multi-role-runner.v3",
    "network_fault_runner": "deltareduce.010.campaign02-stage-role-identity.v3",
    "stage_gate_analyzer": "deltareduce.010.campaign02-stage-gate-analyzer.v3",
}
_IDENTITY_DOMAINS_V4: Final = {
    **_IDENTITY_DOMAINS_V3,
    "exactness_runner": "deltareduce.010.campaign02-stage-role-identity.v4",
    "multi_role_runner": "deltareduce.010.campaign02-multi-role-runner.v4",
    "network_fault_runner": "deltareduce.010.campaign02-stage-role-identity.v4",
    "stage_gate_analyzer": "deltareduce.010.campaign02-stage-gate-analyzer.v4",
}
_STAGE_C_REQUIRED_PATHS: Final = {
    ".github/workflows/benchmark-campaign02-stage-c-measured.yml",
    "CMakeLists.txt",
    "configs/benchmark/faults-v1.json",
    "configs/benchmark/networks-v1.json",
    "delta-node-java/distribution-dependencies.lock.json",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/BenchmarkContracts.java",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/MeasuredStageCTransport.java",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/NettyMetricsCollector.java",
    "delta-node-java/src/main/java/io/deltareduce/node/benchmark/NetworkFaultController.java",
    "delta-protocol/schemas/010/campaign-02/benchmark-definition-v5.json",
    "delta-protocol/schemas/010/campaign-02/network-fault-plan-evidence-v3.json",
    "delta-protocol/schemas/010/campaign-02/execution-plan-v6.json",
    "delta-protocol/schemas/010/campaign-02/qualified-runtime-lineage-v5.json",
    "delta-protocol/schemas/010/campaign-02/stage-c-candidate-run-v1.json",
    "delta-protocol/schemas/010/campaign-02/stage-c-candidate-summary-v1.json",
    "delta-protocol/schemas/010/campaign-02/stage-execution-identities-v4.json",
    "delta-protocol/schemas/010/fault-profile-v1.json",
    "delta-protocol/schemas/010/network-profile-v1.json",
    "delta-runtime-cpp/include/delta/runtime/benchmark.hpp",
    "delta-runtime-cpp/src/benchmark/fault_control.cpp",
    "delta-runtime-cpp/src/benchmark/fault_execution.cpp",
    "delta-runtime-cpp/src/benchmark/sidecar_main.cpp",
    "delta-runtime-cpp/src/benchmark/trace_export.cpp",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_binding.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_execution_identities.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_network_fault.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_c_candidate.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_c_runtime.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_execution.py",
    "delta-worker-python/src/deltatorrent/benchmark/definition.py",
    "delta-worker-python/src/deltatorrent/benchmark/fault_profiles.py",
    "delta-worker-python/src/deltatorrent/benchmark/network_profiles.py",
    "specs/010-wan-benchmark-and-quality/scripts/campaign02_contracts.py",
    "specs/010-wan-benchmark-and-quality/scripts/run_campaign02_stage_c_conformance.py",
}
_BOOTSTRAP_REQUIRED_PATHS: Final = {
    ".github/workflows/benchmark-campaign02-stage-a.yml",
    "delta-protocol/schemas/010/campaign-02/benchmark-definition-v5.json",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_bootstrap.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_execution_identities.py",
    "delta-worker-python/src/deltatorrent/benchmark/campaign02_stage_execution.py",
    "delta-worker-python/src/deltatorrent/benchmark/definition.py",
    "delta-protocol/schemas/010/campaign-02/stage-workflow-gate-qc-v4.json",
    "delta-protocol/schemas/010/campaign-02/workflow-bootstrap-mapping-v1.json",
    "delta-protocol/schemas/010/campaign-02/workflow-bootstrap-signature-v1.json",
    "delta-protocol/schemas/010/campaign-02/workflow-bootstrap-validator-set-v1.json",
    "delta-protocol/schemas/010/campaign-02/workflow-registration-api-evidence-v1.json",
    "delta-protocol/schemas/010/campaign-02/workflow-registration-receipt-v2.json",
    "delta-protocol/schemas/010/campaign-02/workflow-registration-signature-v1.json",
    "specs/010-wan-benchmark-and-quality/scripts/campaign02_bootstrap_control.py",
    "specs/010-wan-benchmark-and-quality/scripts/campaign02_contracts.py",
    "specs/010-wan-benchmark-and-quality/scripts/campaign02_stage_a_control.py",
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
    schema_version: str
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
            or value["schema_version"] not in _MANIFEST_DOMAINS
            or value["campaign_id"] != "campaign-02"
            or value["formal_semantics_id"] != FORMAL_SEMANTICS_ID
            or value["execution_authorized"] is not False
            or not isinstance(source_commit, str)
            or not isinstance(source_tree, str)
            or _COMMIT_ID.fullmatch(source_commit) is None
            or _COMMIT_ID.fullmatch(source_tree) is None
        ):
            raise _fail("CAMPAIGN02_STAGE_IDENTITY_MANIFEST_HEADER_INVALID")
        schema_version = str(value["schema_version"])
        identity_domains = {
            "2.0.0": _IDENTITY_DOMAINS_V2,
            "3.0.0": _IDENTITY_DOMAINS_V3,
            "4.0.0": _IDENTITY_DOMAINS_V4,
        }[schema_version]
        raw_identities = value["identities"]
        if not isinstance(raw_identities, dict) or set(raw_identities) != set(identity_domains):
            raise _fail("CAMPAIGN02_STAGE_IDENTITY_SET_INVALID")
        identities: list[StageExecutionIdentity] = []
        for name in sorted(identity_domains):
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
                identity_domain != identity_domains[name]
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
        result = cls(schema_version, source_commit, source_tree, tuple(identities), dict(value))
        result._verify_roles()
        return result

    def _verify_roles(self) -> None:
        exactness = self.identity("exactness_runner").value
        scientific = self.identity("scientific_runner").value
        network = self.identity("network_fault_runner").value
        analyzer = self.identity("stage_gate_analyzer").value
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
        if (
            analyzer.get("component") != "CAMPAIGN02_STAGE_GATE_ANALYZER"
            or analyzer.get("entrypoint")
            != "deltatorrent.benchmark.campaign02_stage_execution.execute_stage"
            or analyzer.get("execution_authorized") is not False
        ):
            raise _fail("CAMPAIGN02_STAGE_GATE_ANALYZER_IDENTITY_INVALID")
        role_ids = multi_role.get("role_identity_ids")
        if not isinstance(role_ids, dict) or role_ids != {
            "EXACTNESS_RUNNER": self.identity_id("exactness_runner"),
            "NETWORK_FAULT_RUNNER": self.identity_id("network_fault_runner"),
            "SCIENTIFIC_RUNNER": self.identity_id("scientific_runner"),
        }:
            raise _fail("CAMPAIGN02_MULTI_ROLE_METADATA_INVALID")
        if "entrypoints" in multi_role:
            raise _fail("CAMPAIGN02_MULTI_ROLE_METADATA_MUST_NOT_BE_EXECUTABLE")
        if self.schema_version in {"3.0.0", "4.0.0"}:
            self._verify_production_identity(
                exactness, "EXACTNESS_RUNNER", source_class="MEASURED_CI_WORKFLOW"
            )
            self._verify_production_identity(
                network,
                "NETWORK_FAULT_RUNNER",
                source_class=(
                    "MEASURED_RUNTIME" if self.schema_version == "4.0.0" else "MEASURED_HARDWARE"
                ),
            )
            self._verify_gate_analyzer_identity(analyzer)
            if (
                exactness.get("workflow_repository") != "chartjs333/delta"
                or exactness.get("workflow_path")
                != ".github/workflows/benchmark-campaign02-stage-a.yml"
                or exactness.get("workflow_default_ref") != "refs/heads/main"
            ):
                raise _fail("CAMPAIGN02_EXACTNESS_WORKFLOW_PROVENANCE_POLICY_INVALID")
        if self.schema_version == "4.0.0":
            boundary_ids = (
                network.get("image_id"),
                network.get("java_executable_id"),
                network.get("native_executable_id"),
                network.get("transport_harness_id"),
            )
            netty_ids = network.get("netty_artifact_ids")
            if (
                any(
                    not isinstance(item, str) or _CONTENT_ID.fullmatch(item) is None
                    for item in boundary_ids
                )
                or not isinstance(netty_ids, list)
                or not netty_ids
                or any(
                    not isinstance(item, str) or _CONTENT_ID.fullmatch(item) is None
                    for item in netty_ids
                )
                or len(set(netty_ids)) != len(netty_ids)
            ):
                raise _fail("CAMPAIGN02_STAGE_C_RUNTIME_BOUNDARY_IDENTITY_INVALID")
            if not _STAGE_C_REQUIRED_PATHS <= self._identity_paths(network):
                raise _fail("CAMPAIGN02_STAGE_C_RECURSIVE_IDENTITY_INCOMPLETE")
            if not _BOOTSTRAP_REQUIRED_PATHS <= self._identity_paths(analyzer):
                raise _fail("CAMPAIGN02_BOOTSTRAP_RECURSIVE_IDENTITY_INCOMPLETE")

    @staticmethod
    def _identity_paths(value: dict[str, object]) -> set[str]:
        result: set[str] = set()
        for field in ("executable_hashes", "workflow_hashes"):
            entries = value.get(field)
            if isinstance(entries, list):
                result.update(
                    str(item["path"])
                    for item in entries
                    if isinstance(item, dict) and isinstance(item.get("path"), str)
                )
        return result

    @staticmethod
    def _verify_production_identity(
        value: dict[str, object], role: str, *, source_class: str
    ) -> None:
        implementation = {
            "entrypoints": value.get("entrypoints"),
            "executable_hashes": value.get("executable_hashes"),
            "workflow_hashes": value.get("workflow_hashes"),
        }
        expected_implementation_id = sha256_content_id(
            b"deltareduce.010.campaign02-stage-implementation.v1\0"
            + canonical_json_bytes(implementation)
        )
        if (
            value.get("role") != role
            or value.get("allowed_role") != role
            or value.get("source_class") != source_class
            or value.get("implementation_id") != expected_implementation_id
        ):
            raise _fail("CAMPAIGN02_STAGE_PRODUCTION_IDENTITY_INVALID")

    @staticmethod
    def _verify_gate_analyzer_identity(value: dict[str, object]) -> None:
        implementation = {
            "entrypoints": value.get("entrypoints"),
            "executable_hashes": value.get("executable_hashes"),
            "workflow_hashes": value.get("workflow_hashes"),
        }
        expected_implementation_id = sha256_content_id(
            b"deltareduce.010.campaign02-stage-implementation.v1\0"
            + canonical_json_bytes(implementation)
        )
        if (
            value.get("source_class") != "MEASURED_CONTROL_PLANE"
            or value.get("implementation_id") != expected_implementation_id
            or value.get("implementation_class")
            != ("deltatorrent.benchmark.campaign02_stage_execution.Campaign02StageGateFinalizer")
        ):
            raise _fail("CAMPAIGN02_STAGE_GATE_ANALYZER_PRODUCTION_IDENTITY_INVALID")

    def identity(self, name: str) -> StageExecutionIdentity:
        matches = tuple(item for item in self.identities if item.name == name)
        if len(matches) != 1:
            raise _fail("CAMPAIGN02_STAGE_IDENTITY_MISSING")
        return matches[0]

    def identity_id(self, name: str) -> str:
        return self.identity(name).content_id

    def verify_files(self, name: str, source_root: Path) -> None:
        """Verify all executable and workflow bytes named by an identity."""
        identity = self.identity(name)
        root = source_root.resolve()
        entries: list[object] = []
        for field in ("executable_hashes", "workflow_hashes"):
            value = identity.value.get(field, [])
            if not isinstance(value, list):
                raise _fail("CAMPAIGN02_STAGE_IDENTITY_HASH_SET_INVALID")
            entries.extend(value)
        if not entries:
            raise _fail("CAMPAIGN02_STAGE_IDENTITY_HASH_SET_INVALID")
        for item in entries:
            if not isinstance(item, dict) or set(item) != {"content_id", "path"}:
                raise _fail("CAMPAIGN02_STAGE_IDENTITY_HASH_ENTRY_INVALID")
            relative = item["path"]
            expected = item["content_id"]
            if not isinstance(relative, str) or not isinstance(expected, str):
                raise _fail("CAMPAIGN02_STAGE_IDENTITY_HASH_ENTRY_INVALID")
            path = (root / relative).resolve()
            try:
                path.relative_to(root)
                actual = sha256_content_id(path.read_bytes())
            except (OSError, ValueError) as exc:
                raise _fail("CAMPAIGN02_STAGE_IDENTITY_FILE_INVALID") from exc
            if actual != expected:
                raise _fail("CAMPAIGN02_STAGE_IDENTITY_FILE_HASH_MISMATCH")

    @property
    def content_id(self) -> str:
        return sha256_content_id(
            _MANIFEST_DOMAINS[self.schema_version] + canonical_json_bytes(self.raw)
        )
