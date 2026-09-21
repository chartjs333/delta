"""Append-only content-addressed Feature 010 evidence graph builder."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from deltatorrent.artifacts.filesystem import FilesystemArtifactStore
from deltatorrent.benchmark.contracts import (
    AUTHORITY_SCOPE,
    FORMAL_SEMANTICS_ID,
    SCHEMA_VERSION,
    CanonicalContract,
    ContractError,
)
from deltatorrent.benchmark.governance import GovernanceQC, ReviewerSet
from deltatorrent.domain.manifests import ArtifactRef

KIND_POLICY = {
    "ARM": (
        "BENCHMARK_ARM",
        "application/vnd.deltareduce.benchmark-arm+json;version=1",
        "SCHEMA-BENCHMARK-ARM-010-V1",
    ),
    "BOUND_ARTIFACT": (
        "BENCHMARK_BOUND_ARTIFACT",
        "application/vnd.deltareduce.benchmark-bound-artifact+json;version=1",
        "SCHEMA-BENCHMARK-BOUND-ARTIFACT-010-V1",
    ),
    "DEFINITION": (
        "BENCHMARK_DEFINITION",
        "application/vnd.deltareduce.benchmark-definition+json;version=1",
        "SCHEMA-BENCHMARK-DEFINITION-010-V1",
    ),
    "DEFINITION_REVIEWER_SET": (
        "BENCHMARK_REVIEWER_SET",
        "application/vnd.deltareduce.benchmark-reviewer-set+json;version=1",
        "SCHEMA-BENCHMARK-REVIEWER-SET-010-V1",
    ),
    "ENVIRONMENT": (
        "BENCHMARK_ENVIRONMENT_MANIFEST",
        "application/vnd.deltareduce.benchmark-environment+json;version=1",
        "SCHEMA-BENCHMARK-ENVIRONMENT-010-V1",
    ),
    "FAULT_PROFILE": (
        "BENCHMARK_FAULT_PROFILE",
        "application/vnd.deltareduce.benchmark-fault-profile+json;version=1",
        "SCHEMA-BENCHMARK-FAULT-PROFILE-010-V1",
    ),
    "METRICS": (
        "BENCHMARK_METRICS",
        "application/vnd.deltareduce.benchmark-metrics+json;version=1",
        "SCHEMA-BENCHMARK-METRICS-010-V1",
    ),
    "NETWORK_PROFILE": (
        "BENCHMARK_NETWORK_PROFILE",
        "application/vnd.deltareduce.benchmark-network-profile+json;version=1",
        "SCHEMA-BENCHMARK-NETWORK-PROFILE-010-V1",
    ),
    "RUN_MANIFEST": (
        "BENCHMARK_RUN_MANIFEST",
        "application/vnd.deltareduce.benchmark-run-manifest+json;version=1",
        "SCHEMA-BENCHMARK-RUN-MANIFEST-010-V1",
    ),
    "RUNTIME_IDENTITY": (
        "BENCHMARK_RUNTIME_IDENTITY",
        "application/vnd.deltareduce.benchmark-runtime-identity+json;version=1",
        "SCHEMA-BENCHMARK-RUNTIME-IDENTITY-010-V1",
    ),
    "RESULT_EVALUATOR_SET": (
        "BENCHMARK_REVIEWER_SET",
        "application/vnd.deltareduce.benchmark-reviewer-set+json;version=1",
        "SCHEMA-BENCHMARK-REVIEWER-SET-010-V1",
    ),
    "SCIENTIFIC_PROFILE": (
        "BENCHMARK_SCIENTIFIC_PROFILE",
        "application/vnd.deltareduce.benchmark-scientific-profile+json;version=1",
        "SCHEMA-BENCHMARK-SCIENTIFIC-PROFILE-010-V1",
    ),
    "STAGE_RECEIPT": (
        "BENCHMARK_STAGE_RECEIPT",
        "application/vnd.deltareduce.benchmark-stage-receipt+json;version=1",
        "SCHEMA-BENCHMARK-STAGE-RECEIPT-010-V1",
    ),
}
REQUIRED_FOUNDATION_KINDS = tuple(sorted(KIND_POLICY))
RAW_ARTIFACT_MEDIA_TYPE = "application/octet-stream"
RAW_ARTIFACT_SCHEMA_ID = "SCHEMA-BENCHMARK-RAW-ARTIFACT-010-V1"


@dataclass(frozen=True, slots=True)
class EvidenceObject:
    contract: CanonicalContract
    reference: ArtifactRef


@dataclass(frozen=True, slots=True)
class EvidenceGraph:
    definition_id: str
    manifest: EvidenceObject
    nodes: tuple[EvidenceObject, ...]


@dataclass(frozen=True, slots=True)
class EvidenceAttestation:
    result: EvidenceObject
    result_qc: ArtifactRef | None
    manifest: EvidenceObject


class EvidenceGraphBuilder:
    """Create-only builder. It cannot mark a benchmark gate complete."""

    def __init__(self, root: Path, *, definition_id: str) -> None:
        self.store = FilesystemArtifactStore(root)
        self.definition_id = definition_id
        self._nodes: list[EvidenceObject] = []
        self._ordinals: set[int] = set()
        self._governance_refs: dict[str, ArtifactRef] = {}

    def _publish_contract(
        self,
        contract: CanonicalContract | ReviewerSet,
        *,
        media_type: str,
        schema_id: str,
    ) -> ArtifactRef:
        return self.store.publish_bytes(
            contract.canonical_bytes,
            media_type=media_type,
            schema_id=schema_id,
        )

    def add_node(
        self,
        *,
        kind: str,
        payload: CanonicalContract | ReviewerSet,
        run_id: str,
        ordinal: int,
        dependencies: tuple[str, ...] = (),
    ) -> EvidenceObject:
        try:
            expected_type, media_type, schema_id = KIND_POLICY[kind]
        except KeyError as exc:
            raise ContractError("EVIDENCE_KIND_UNSUPPORTED") from exc
        if payload.type_name != expected_type:
            raise ContractError("EVIDENCE_PAYLOAD_TYPE_MISMATCH")
        if ordinal in self._ordinals or ordinal < 0:
            raise ContractError("EVIDENCE_ORDINAL_DUPLICATE_OR_INVALID")
        if tuple(sorted(set(dependencies))) != dependencies:
            raise ContractError("EVIDENCE_DEPENDENCIES_NOT_SORTED_UNIQUE")
        if kind == "DEFINITION" and payload.content_id != self.definition_id:
            raise ContractError("EVIDENCE_DEFINITION_PAYLOAD_MISMATCH")
        if kind == "DEFINITION_REVIEWER_SET":
            if not isinstance(payload, ReviewerSet) or payload.role != "DEFINITION_REVIEWERS":
                raise ContractError("EVIDENCE_DEFINITION_REVIEWER_SET_INVALID")
        if kind == "RESULT_EVALUATOR_SET":
            if not isinstance(payload, ReviewerSet) or payload.role != "RESULT_EVALUATORS":
                raise ContractError("EVIDENCE_RESULT_EVALUATOR_SET_INVALID")
        if kind in {"DEFINITION_REVIEWER_SET", "RESULT_EVALUATOR_SET"}:
            if kind in self._governance_refs:
                raise ContractError("EVIDENCE_GOVERNANCE_SET_DUPLICATE")
        run_scoped = {"METRICS", "RUN_MANIFEST", "STAGE_RECEIPT"}
        if kind in run_scoped:
            if not isinstance(payload, CanonicalContract) or payload.to_dict()["run_id"] != run_id:
                raise ContractError("EVIDENCE_NODE_RUN_MISMATCH")
        elif run_id != "foundation-global":
            raise ContractError("EVIDENCE_GLOBAL_NODE_RUN_INVALID")
        payload_ref = self._publish_contract(payload, media_type=media_type, schema_id=schema_id)
        node = CanonicalContract.from_dict(
            {
                "authority_scope": AUTHORITY_SCOPE,
                "benchmark_definition_id": self.definition_id,
                "dependencies": list(dependencies),
                "evidence_class": "TEST_FIXTURE",
                "formal_semantics_id": FORMAL_SEMANTICS_ID,
                "gate_eligible": False,
                "kind": kind,
                "media_type": media_type,
                "ordinal": ordinal,
                "payload_id": payload_ref.content_id,
                "primary_eligible": False,
                "run_id": run_id,
                "schema_id": schema_id,
                "schema_version": SCHEMA_VERSION,
                "type_name": "BENCHMARK_EVIDENCE_NODE",
            }
        )
        node_ref = self._publish_contract(
            node,
            media_type="application/vnd.deltareduce.benchmark-evidence-node+json;version=1",
            schema_id="SCHEMA-BENCHMARK-EVIDENCE-NODE-010-V1",
        )
        result = EvidenceObject(node, node_ref)
        self._nodes.append(result)
        self._ordinals.add(ordinal)
        if kind in {"DEFINITION_REVIEWER_SET", "RESULT_EVALUATOR_SET"}:
            self._governance_refs[kind] = payload_ref
        return result

    def add_bound_artifact(
        self,
        *,
        name: str,
        artifact_kind: str,
        value: bytes,
        media_type: str,
        run_id: str,
        ordinal: int,
        dependencies: tuple[str, ...] = (),
        license_id: str | None = None,
    ) -> EvidenceObject:
        if media_type != RAW_ARTIFACT_MEDIA_TYPE:
            raise ContractError("EVIDENCE_RAW_ARTIFACT_MEDIA_TYPE_INVALID")
        raw_ref = self.store.publish_bytes(
            value,
            media_type=RAW_ARTIFACT_MEDIA_TYPE,
            schema_id=RAW_ARTIFACT_SCHEMA_ID,
        )
        wrapper = CanonicalContract.from_dict(
            {
                "artifact_id": raw_ref.content_id,
                "artifact_kind": artifact_kind,
                "authority_scope": AUTHORITY_SCOPE,
                "byte_length": len(value),
                "evidence_class": "TEST_FIXTURE",
                "formal_semantics_id": FORMAL_SEMANTICS_ID,
                "gate_eligible": False,
                "license_id": license_id,
                "media_type": media_type,
                "name": name,
                "primary_eligible": False,
                "schema_version": SCHEMA_VERSION,
                "type_name": "BENCHMARK_BOUND_ARTIFACT",
            }
        )
        return self.add_node(
            kind="BOUND_ARTIFACT",
            payload=wrapper,
            run_id=run_id,
            ordinal=ordinal,
            dependencies=dependencies,
        )

    def seal(
        self,
        *,
        run_ids: tuple[str, ...],
        definition_qc: ArtifactRef | None = None,
    ) -> EvidenceGraph:
        if tuple(sorted(set(run_ids))) != run_ids or not run_ids:
            raise ContractError("EVIDENCE_RUN_IDS_NOT_SORTED_UNIQUE")
        actual_kinds = {node.contract.to_dict()["kind"] for node in self._nodes}
        if not set(REQUIRED_FOUNDATION_KINDS) <= actual_kinds:
            raise ContractError("EVIDENCE_REQUIRED_KIND_MISSING")
        definition_reviewer_set = self._governance_refs.get("DEFINITION_REVIEWER_SET")
        if definition_reviewer_set is None:
            raise ContractError("EVIDENCE_DEFINITION_REVIEWER_SET_MISSING")
        node_ids = tuple(sorted(node.reference.content_id for node in self._nodes))
        manifest = CanonicalContract.from_dict(
            {
                "authority_scope": AUTHORITY_SCOPE,
                "benchmark_definition_id": self.definition_id,
                "definition_reviewer_set_id": definition_reviewer_set.content_id,
                "definition_qc_id": definition_qc.content_id if definition_qc else None,
                "evidence_class": "TEST_FIXTURE",
                "formal_semantics_id": FORMAL_SEMANTICS_ID,
                "gate_eligible": False,
                "node_ids": list(node_ids),
                "primary_eligible": False,
                "required_kinds": list(REQUIRED_FOUNDATION_KINDS),
                "run_ids": list(run_ids),
                "schema_version": SCHEMA_VERSION,
                "type_name": "BENCHMARK_EVIDENCE_MANIFEST",
            }
        )
        manifest_ref = self._publish_contract(
            manifest,
            media_type="application/vnd.deltareduce.benchmark-evidence-manifest+json;version=1",
            schema_id="SCHEMA-BENCHMARK-EVIDENCE-MANIFEST-010-V1",
        )
        return EvidenceGraph(
            definition_id=self.definition_id,
            manifest=EvidenceObject(manifest, manifest_ref),
            nodes=tuple(sorted(self._nodes, key=lambda item: item.contract.to_dict()["ordinal"])),
        )

    def attest(
        self,
        *,
        graph: EvidenceGraph,
        result: CanonicalContract,
        result_qc: GovernanceQC | None = None,
    ) -> EvidenceAttestation:
        if result.type_name != "BENCHMARK_RESULT":
            raise ContractError("EVIDENCE_RESULT_TYPE_INVALID")
        result_document = result.to_dict()
        if result_document["benchmark_definition_id"] != graph.definition_id:
            raise ContractError("EVIDENCE_RESULT_DEFINITION_MISMATCH")
        if result_document["evidence_manifest_id"] != graph.manifest.reference.content_id:
            raise ContractError("EVIDENCE_RESULT_MANIFEST_MISMATCH")
        if tuple(result_document["run_ids"]) != tuple(graph.manifest.contract.to_dict()["run_ids"]):
            raise ContractError("EVIDENCE_RESULT_RUN_INVENTORY_MISMATCH")
        evaluator_set = self._governance_refs.get("RESULT_EVALUATOR_SET")
        definition_set = self._governance_refs.get("DEFINITION_REVIEWER_SET")
        if evaluator_set is None or definition_set is None:
            raise ContractError("EVIDENCE_GOVERNANCE_SET_MISSING")
        if result_document["result_evaluator_set_id"] != evaluator_set.content_id:
            raise ContractError("EVIDENCE_RESULT_EVALUATOR_SET_MISMATCH")
        result_ref = self._publish_contract(
            result,
            media_type="application/vnd.deltareduce.benchmark-result+json;version=1",
            schema_id="SCHEMA-BENCHMARK-RESULT-010-V1",
        )
        qc_ref: ArtifactRef | None = None
        if result_qc is not None:
            if result_qc.body_id != result.content_id:
                raise ContractError("EVIDENCE_RESULT_QC_BODY_MISMATCH")
            qc_ref = self.store.publish_bytes(
                result_qc.canonical_bytes,
                media_type="application/vnd.deltareduce.benchmark-governance-qc+json;version=1",
                schema_id="SCHEMA-BENCHMARK-GOVERNANCE-QC-010-V1",
            )
        attestation = CanonicalContract.from_dict(
            {
                "authority_scope": AUTHORITY_SCOPE,
                "benchmark_result_id": result_ref.content_id,
                "benchmark_result_qc_id": qc_ref.content_id if qc_ref else None,
                "definition_reviewer_set_id": definition_set.content_id,
                "evidence_class": "TEST_FIXTURE",
                "evidence_manifest_id": graph.manifest.reference.content_id,
                "formal_semantics_id": FORMAL_SEMANTICS_ID,
                "gate_eligible": False,
                "primary_eligible": False,
                "result_evaluator_set_id": evaluator_set.content_id,
                "schema_version": SCHEMA_VERSION,
                "type_name": "BENCHMARK_ATTESTATION_MANIFEST",
            }
        )
        attestation_ref = self._publish_contract(
            attestation,
            media_type="application/vnd.deltareduce.benchmark-attestation-manifest+json;version=1",
            schema_id="SCHEMA-BENCHMARK-ATTESTATION-MANIFEST-010-V1",
        )
        return EvidenceAttestation(
            result=EvidenceObject(result, result_ref),
            result_qc=qc_ref,
            manifest=EvidenceObject(attestation, attestation_ref),
        )
