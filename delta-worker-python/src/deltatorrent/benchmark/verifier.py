"""Network-independent recursive verifier for Feature 010 evidence graphs."""

from __future__ import annotations

import hashlib
import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from deltatorrent.benchmark.canonical import load_json_bytes
from deltatorrent.benchmark.contracts import (
    CanonicalContract,
    ContractError,
    validate_scientific_dependencies,
)
from deltatorrent.benchmark.evidence import KIND_POLICY, REQUIRED_FOUNDATION_KINDS
from deltatorrent.benchmark.governance import ReviewerSet, qc_from_bytes
from deltatorrent.benchmark.receipts import verify_receipt_chain


@dataclass(frozen=True, slots=True)
class VerifiedEvidenceGraph:
    manifest_id: str
    definition_id: str
    node_count: int
    payload_count: int
    run_count: int
    bound_artifact_count: int
    status: str = "PASS"


@dataclass(frozen=True, slots=True)
class VerifiedAttestation:
    attestation_id: str
    result_id: str
    evidence_manifest_id: str
    result_qc_present: bool
    decision: str
    status: str = "PASS"


class OfflineEvidenceVerifier:
    def __init__(self, store_root: Path) -> None:
        self.root = store_root.resolve()

    def _read(self, object_id: str) -> bytes:
        if (
            len(object_id) != 71
            or not object_id.startswith("sha256:")
            or any(character not in "0123456789abcdef" for character in object_id[7:])
        ):
            raise ContractError("EVIDENCE_OBJECT_ID_INVALID")
        digest = object_id[7:]
        path = self.root / "objects" / "sha256" / digest[:2] / digest
        parent_symlink = any(
            parent.is_symlink() for parent in path.parents if parent != self.root.parent
        )
        if path.is_symlink() or parent_symlink:
            raise ContractError("EVIDENCE_SYMLINK_FORBIDDEN")
        try:
            resolved = path.resolve(strict=True)
            value = resolved.read_bytes()
        except FileNotFoundError as exc:
            raise ContractError("EVIDENCE_OBJECT_MISSING") from exc
        if not resolved.is_relative_to(self.root):
            raise ContractError("EVIDENCE_PATH_ESCAPE")
        if hashlib.sha256(value).hexdigest() != digest:
            raise ContractError("EVIDENCE_OBJECT_HASH_MISMATCH")
        return value

    def _contract(self, object_id: str) -> CanonicalContract:
        return CanonicalContract.from_bytes(self._read(object_id))

    def _reviewer_set(self, object_id: str) -> ReviewerSet:
        reviewer_set = ReviewerSet.from_dict(load_json_bytes(self._read(object_id)))
        if reviewer_set.content_id != object_id:
            raise ContractError("EVIDENCE_REVIEWER_SET_ID_MISMATCH")
        return reviewer_set

    @staticmethod
    def _verify_dag(nodes: dict[str, CanonicalContract]) -> None:
        ordinals: set[int] = set()
        dependencies: set[str] = set()
        for node in nodes.values():
            value = node.to_dict()
            ordinal = int(value["ordinal"])
            if ordinal in ordinals:
                raise ContractError("EVIDENCE_ORDINAL_DUPLICATE")
            ordinals.add(ordinal)
            for dependency in value["dependencies"]:
                if dependency not in nodes:
                    raise ContractError("EVIDENCE_DEPENDENCY_MISSING")
                if int(nodes[dependency].to_dict()["ordinal"]) >= ordinal:
                    raise ContractError("EVIDENCE_DEPENDENCY_ORDER_INVALID")
                dependencies.add(dependency)
            if ordinal > 0 and not value["dependencies"]:
                raise ContractError("EVIDENCE_NONROOT_WITHOUT_DEPENDENCY")
        terminals = set(nodes) - dependencies
        if len(terminals) != 1:
            raise ContractError("EVIDENCE_TERMINAL_CARDINALITY_INVALID")
        visited: set[str] = set()

        def walk(node_id: str) -> None:
            if node_id in visited:
                return
            visited.add(node_id)
            for dependency in nodes[node_id].to_dict()["dependencies"]:
                walk(str(dependency))

        walk(terminals.pop())
        if visited != set(nodes):
            raise ContractError("EVIDENCE_GRAPH_ORPHAN")

    @staticmethod
    def _only(values: list[Any], code: str) -> Any:
        if len(values) != 1:
            raise ContractError(code)
        return values[0]

    @staticmethod
    def _external_artifact_ids(
        *,
        definition: CanonicalContract,
        runtime: CanonicalContract,
        scientific: CanonicalContract,
        environment: CanonicalContract,
        arms: list[CanonicalContract],
        receipts: list[CanonicalContract],
        metrics: list[CanonicalContract],
    ) -> set[str]:
        expected: set[str] = set()
        runtime_document = runtime.to_dict()
        for field in (
            "abi_header_id",
            "abi_schema_id",
            "binary_build_id",
            "compiler_lock_id",
            "cpp_core_id",
            "cuda_profile_id",
            "fixture_corpus_id",
            "formal_report_id",
            "java_dependency_lock_id",
            "java_toolchain_id",
            "native_runtime_id",
            "netty_profile_id",
            "protocol_registry_id",
            "python_lock_id",
            "python_profile_id",
            "sbom_id",
        ):
            expected.add(str(runtime_document[field]))
        scientific_document = scientific.to_dict()
        for field in (
            "dataset_id",
            "model_id",
            "optimizer_id",
            "ticket_plan_id",
            "tokenizer_id",
        ):
            expected.add(str(scientific_document[field]))
        expected.update(str(item) for item in scientific_document["evaluator_ids"])
        expected.update(str(item) for item in scientific_document["ticket_ids"])
        environment_document = environment.to_dict()
        expected.update(str(item) for item in environment_document["binary_ids"])
        expected.update(str(item) for item in environment_document["dependency_lock_ids"])
        for field in ("hardware_inventory_id", "image_id", "sbom_id"):
            expected.add(str(environment_document[field]))
        definition_document = definition.to_dict()
        for dependency in definition_document["dependencies"]:
            expected.add(str(dependency["content_id"]))
            expected.add(str(dependency["license_id"]))
        expected.update(str(arm.to_dict()["adapter_id"]) for arm in arms)
        for receipt in receipts:
            document = receipt.to_dict()
            expected.update(str(item) for item in document["input_ids"])
            expected.update(str(item) for item in document["output_ids"])
            expected.update(str(item) for item in document["native_opaque_refs"].values())
        expected.update(str(item.to_dict()["gpu_metrics"]["device_id"]) for item in metrics)
        return expected

    def _verify_definition_qc(
        self,
        *,
        manifest: dict[str, object],
        definition: CanonicalContract,
        reviewer_set: ReviewerSet,
    ) -> None:
        definition_qc_id = manifest["definition_qc_id"]
        if definition_qc_id is None:
            return
        qc = qc_from_bytes(self._read(str(definition_qc_id)), reviewer_set, definition)
        if qc.purpose != "BENCHMARK_DEFINITION_VOTE" or qc.decision != "APPROVE":
            raise ContractError("EVIDENCE_DEFINITION_QC_MISMATCH")

    def verify(self, expected_manifest_id: str) -> VerifiedEvidenceGraph:
        manifest_contract = self._contract(expected_manifest_id)
        if manifest_contract.type_name != "BENCHMARK_EVIDENCE_MANIFEST":
            raise ContractError("EVIDENCE_ROOT_TYPE_INVALID")
        manifest = manifest_contract.to_dict()
        definition_id = str(manifest["benchmark_definition_id"])
        node_ids = tuple(str(item) for item in manifest["node_ids"])
        nodes = {node_id: self._contract(node_id) for node_id in node_ids}
        if len(nodes) != len(node_ids):
            raise ContractError("EVIDENCE_NODE_ID_DUPLICATE")
        if any(node.type_name != "BENCHMARK_EVIDENCE_NODE" for node in nodes.values()):
            raise ContractError("EVIDENCE_NODE_TYPE_INVALID")
        self._verify_dag(nodes)

        by_kind: dict[str, list[tuple[CanonicalContract, object]]] = {}
        payload_ids: set[str] = set()
        for node in nodes.values():
            node_document = node.to_dict()
            if node_document["benchmark_definition_id"] != definition_id:
                raise ContractError("EVIDENCE_NODE_DEFINITION_MISMATCH")
            kind = str(node_document["kind"])
            try:
                expected_type, expected_media, expected_schema = KIND_POLICY[kind]
            except KeyError as exc:
                raise ContractError("EVIDENCE_KIND_UNSUPPORTED") from exc
            if (
                node_document["media_type"] != expected_media
                or node_document["schema_id"] != expected_schema
            ):
                raise ContractError("EVIDENCE_KIND_POLICY_MISMATCH")
            payload_id = str(node_document["payload_id"])
            if payload_id in payload_ids:
                raise ContractError("EVIDENCE_PAYLOAD_DUPLICATE")
            payload_ids.add(payload_id)
            if expected_type == "BENCHMARK_REVIEWER_SET":
                reviewer_payload = self._reviewer_set(payload_id)
                payload: object = reviewer_payload
                payload_type = reviewer_payload.type_name
            else:
                payload = self._contract(payload_id)
                payload_type = payload.type_name
            if payload_type != expected_type:
                raise ContractError("EVIDENCE_PAYLOAD_TYPE_MISMATCH")
            run_id = str(node_document["run_id"])
            if kind in {"METRICS", "RUN_MANIFEST", "STAGE_RECEIPT"}:
                if (
                    not isinstance(payload, CanonicalContract)
                    or payload.to_dict()["run_id"] != run_id
                ):
                    raise ContractError("EVIDENCE_NODE_RUN_MISMATCH")
            elif run_id != "foundation-global":
                raise ContractError("EVIDENCE_GLOBAL_NODE_RUN_INVALID")
            by_kind.setdefault(kind, []).append((node, payload))

        kind_set = tuple(sorted(by_kind))
        if kind_set != REQUIRED_FOUNDATION_KINDS:
            raise ContractError("EVIDENCE_REQUIRED_KIND_SET_MISMATCH")
        if kind_set != tuple(manifest["required_kinds"]):
            raise ContractError("EVIDENCE_MANIFEST_KIND_SET_MISMATCH")

        definition = self._only(
            [payload for _, payload in by_kind["DEFINITION"]],
            "EVIDENCE_DEFINITION_CARDINALITY_INVALID",
        )
        runtime = self._only(
            [payload for _, payload in by_kind["RUNTIME_IDENTITY"]],
            "EVIDENCE_RUNTIME_IDENTITY_CARDINALITY_INVALID",
        )
        scientific = self._only(
            [payload for _, payload in by_kind["SCIENTIFIC_PROFILE"]],
            "EVIDENCE_SCIENTIFIC_PROFILE_CARDINALITY_INVALID",
        )
        environment = self._only(
            [payload for _, payload in by_kind["ENVIRONMENT"]],
            "EVIDENCE_ENVIRONMENT_CARDINALITY_INVALID",
        )
        definition_reviewers = self._only(
            [payload for _, payload in by_kind["DEFINITION_REVIEWER_SET"]],
            "EVIDENCE_DEFINITION_REVIEWER_SET_CARDINALITY_INVALID",
        )
        result_evaluators = self._only(
            [payload for _, payload in by_kind["RESULT_EVALUATOR_SET"]],
            "EVIDENCE_RESULT_EVALUATOR_SET_CARDINALITY_INVALID",
        )
        assert isinstance(definition, CanonicalContract)
        assert isinstance(runtime, CanonicalContract)
        assert isinstance(scientific, CanonicalContract)
        assert isinstance(environment, CanonicalContract)
        assert isinstance(definition_reviewers, ReviewerSet)
        assert isinstance(result_evaluators, ReviewerSet)
        if definition_reviewers.role != "DEFINITION_REVIEWERS":
            raise ContractError("EVIDENCE_DEFINITION_REVIEWER_SET_ROLE_MISMATCH")
        if result_evaluators.role != "RESULT_EVALUATORS":
            raise ContractError("EVIDENCE_RESULT_EVALUATOR_SET_ROLE_MISMATCH")
        if definition.content_id != definition_id:
            raise ContractError("EVIDENCE_DEFINITION_ID_MISMATCH")
        definition_document = definition.to_dict()
        if definition_document["runtime_identity_id"] != runtime.content_id:
            raise ContractError("EVIDENCE_DEFINITION_RUNTIME_MISMATCH")
        if definition_document["scientific_profile_id"] != scientific.content_id:
            raise ContractError("EVIDENCE_DEFINITION_SCIENCE_MISMATCH")
        validate_scientific_dependencies(definition, scientific)
        if definition_document["definition_reviewer_set_id"] != definition_reviewers.content_id:
            raise ContractError("EVIDENCE_DEFINITION_REVIEWER_SET_MISMATCH")
        if definition_document["result_evaluator_set_id"] != result_evaluators.content_id:
            raise ContractError("EVIDENCE_RESULT_EVALUATOR_SET_MISMATCH")
        if manifest["definition_reviewer_set_id"] != definition_reviewers.content_id:
            raise ContractError("EVIDENCE_MANIFEST_REVIEWER_SET_MISMATCH")

        runtime_document = runtime.to_dict()
        environment_document = environment.to_dict()
        if environment_document["runtime_identity_id"] != runtime.content_id:
            raise ContractError("EVIDENCE_ENVIRONMENT_RUNTIME_MISMATCH")
        for field in ("source_commit", "source_tree", "sbom_id"):
            if environment_document[field] != runtime_document[field]:
                raise ContractError(f"EVIDENCE_ENVIRONMENT_{field.upper()}_MISMATCH")
        required_locks = {
            runtime_document["compiler_lock_id"],
            runtime_document["java_dependency_lock_id"],
            runtime_document["python_lock_id"],
        }
        if not required_locks <= set(environment_document["dependency_lock_ids"]):
            raise ContractError("EVIDENCE_ENVIRONMENT_LOCK_SET_INCOMPLETE")
        required_binaries = {
            runtime_document["binary_build_id"],
            runtime_document["native_runtime_id"],
        }
        if not required_binaries <= set(environment_document["binary_ids"]):
            raise ContractError("EVIDENCE_ENVIRONMENT_BINARY_SET_INCOMPLETE")

        arms = [payload for _, payload in by_kind["ARM"]]
        networks = [payload for _, payload in by_kind["NETWORK_PROFILE"]]
        faults = [payload for _, payload in by_kind["FAULT_PROFILE"]]
        receipts = [payload for _, payload in by_kind["STAGE_RECEIPT"]]
        metrics = [payload for _, payload in by_kind["METRICS"]]
        runs = [payload for _, payload in by_kind["RUN_MANIFEST"]]
        if not all(
            isinstance(item, CanonicalContract)
            for item in (*arms, *networks, *faults, *receipts, *metrics, *runs)
        ):
            raise ContractError("EVIDENCE_CONTRACT_PAYLOAD_INVALID")
        arm_contracts = [item for item in arms if isinstance(item, CanonicalContract)]
        network_contracts = [item for item in networks if isinstance(item, CanonicalContract)]
        fault_contracts = [item for item in faults if isinstance(item, CanonicalContract)]
        receipt_contracts = [item for item in receipts if isinstance(item, CanonicalContract)]
        metric_contracts = [item for item in metrics if isinstance(item, CanonicalContract)]
        run_contracts = [item for item in runs if isinstance(item, CanonicalContract)]
        if tuple(sorted(item.content_id for item in arm_contracts)) != tuple(
            definition_document["arm_ids"]
        ):
            raise ContractError("EVIDENCE_ARM_SET_MISMATCH")
        if {str(item.to_dict()["arm_kind"]) for item in arm_contracts} != {
            "REFERENCE",
            "DELTAREDUCE",
        }:
            raise ContractError("EVIDENCE_ARM_KIND_SET_INVALID")
        if tuple(sorted(item.content_id for item in network_contracts)) != tuple(
            definition_document["network_profile_ids"]
        ):
            raise ContractError("EVIDENCE_NETWORK_SET_MISMATCH")
        if tuple(sorted(item.content_id for item in fault_contracts)) != tuple(
            definition_document["fault_profile_ids"]
        ):
            raise ContractError("EVIDENCE_FAULT_SET_MISMATCH")

        scientific_document = scientific.to_dict()
        arm_by_id = {item.content_id: item for item in arm_contracts}
        run_by_id: dict[str, CanonicalContract] = {}
        receipt_groups: dict[str, list[CanonicalContract]] = {}
        metrics_by_run: dict[str, list[CanonicalContract]] = {}
        for receipt in receipt_contracts:
            receipt_groups.setdefault(str(receipt.to_dict()["run_id"]), []).append(receipt)
        for item in metric_contracts:
            metrics_by_run.setdefault(str(item.to_dict()["run_id"]), []).append(item)
        actual_matrix: set[tuple[object, ...]] = set()
        for run_manifest in run_contracts:
            run = run_manifest.to_dict()
            run_id = str(run["run_id"])
            if run_id in run_by_id:
                raise ContractError("EVIDENCE_RUN_MANIFEST_DUPLICATE")
            run_by_id[run_id] = run_manifest
            if run["benchmark_definition_id"] != definition_id:
                raise ContractError("EVIDENCE_RUN_DEFINITION_MISMATCH")
            if run["environment_manifest_id"] != environment.content_id:
                raise ContractError("EVIDENCE_RUN_ENVIRONMENT_MISMATCH")
            if run["scientific_profile_id"] != scientific.content_id:
                raise ContractError("EVIDENCE_RUN_SCIENCE_MISMATCH")
            if run["arm_id"] not in arm_by_id:
                raise ContractError("EVIDENCE_RUN_ARM_MISMATCH")
            if run["network_profile_id"] not in definition_document["network_profile_ids"]:
                raise ContractError("EVIDENCE_RUN_NETWORK_MISMATCH")
            if run["fault_profile_id"] not in definition_document["fault_profile_ids"]:
                raise ContractError("EVIDENCE_RUN_FAULT_MISMATCH")
            repetition = int(run["repetition"])
            if repetition > len(scientific_document["seeds"]):
                raise ContractError("EVIDENCE_RUN_REPETITION_MISMATCH")
            if run["seed"] != scientific_document["seeds"][repetition - 1]:
                raise ContractError("EVIDENCE_RUN_SEED_MISMATCH")
            if tuple(run["ticket_ids"]) != tuple(scientific_document["ticket_ids"]):
                raise ContractError("EVIDENCE_RUN_TICKET_SET_MISMATCH")
            arm_document = arm_by_id[str(run["arm_id"])].to_dict()
            if arm_document["model_mode"] != scientific_document["model_mode"]:
                raise ContractError("EVIDENCE_ARM_MODEL_MODE_MISMATCH")
            if arm_document["deployment_profile"] != runtime_document["deployment_profile"]:
                raise ContractError("EVIDENCE_ARM_DEPLOYMENT_MISMATCH")
            run_receipts = tuple(
                sorted(receipt_groups.get(run_id, []), key=lambda item: item.to_dict()["sequence"])
            )
            verify_receipt_chain(
                run_manifest=run_manifest,
                receipts=run_receipts,
                runtime_identity=runtime,
            )
            if len(metrics_by_run.get(run_id, [])) != 1:
                raise ContractError("EVIDENCE_RUN_METRICS_CARDINALITY_INVALID")
            matrix_key = (
                run["arm_id"],
                run["network_profile_id"],
                run["fault_profile_id"],
                repetition,
                run["seed"],
            )
            if matrix_key in actual_matrix:
                raise ContractError("EVIDENCE_RUN_MATRIX_DUPLICATE")
            actual_matrix.add(matrix_key)
        if tuple(sorted(run_by_id)) != tuple(manifest["run_ids"]):
            raise ContractError("EVIDENCE_RUN_INVENTORY_MISMATCH")
        expected_matrix = {
            (arm_id, network_id, fault_id, repetition, seed)
            for arm_id, network_id, fault_id, (repetition, seed) in itertools.product(
                definition_document["arm_ids"],
                definition_document["network_profile_ids"],
                definition_document["fault_profile_ids"],
                enumerate(scientific_document["seeds"], start=1),
            )
        }
        if actual_matrix != expected_matrix:
            raise ContractError("EVIDENCE_RUN_MATRIX_INCOMPLETE")
        if set(receipt_groups) != set(run_by_id) or set(metrics_by_run) != set(run_by_id):
            raise ContractError("EVIDENCE_RUN_PAYLOAD_ORPHAN")

        bound_artifact_ids: set[str] = set()
        for _, payload in by_kind["BOUND_ARTIFACT"]:
            assert isinstance(payload, CanonicalContract)
            wrapper = payload.to_dict()
            artifact_id = str(wrapper["artifact_id"])
            raw = self._read(artifact_id)
            if len(raw) != wrapper["byte_length"]:
                raise ContractError("EVIDENCE_BOUND_ARTIFACT_LENGTH_MISMATCH")
            if artifact_id in bound_artifact_ids:
                raise ContractError("EVIDENCE_BOUND_ARTIFACT_DUPLICATE")
            bound_artifact_ids.add(artifact_id)
        expected_artifact_ids = self._external_artifact_ids(
            definition=definition,
            runtime=runtime,
            scientific=scientific,
            environment=environment,
            arms=arm_contracts,
            receipts=receipt_contracts,
            metrics=metric_contracts,
        )
        if bound_artifact_ids != expected_artifact_ids:
            raise ContractError("EVIDENCE_BOUND_ARTIFACT_SET_MISMATCH")

        self._verify_definition_qc(
            manifest=manifest,
            definition=definition,
            reviewer_set=definition_reviewers,
        )
        return VerifiedEvidenceGraph(
            manifest_id=expected_manifest_id,
            definition_id=definition_id,
            node_count=len(nodes),
            payload_count=len(payload_ids),
            run_count=len(run_by_id),
            bound_artifact_count=len(bound_artifact_ids),
        )

    def verify_attestation(self, expected_attestation_id: str) -> VerifiedAttestation:
        attestation = self._contract(expected_attestation_id)
        if attestation.type_name != "BENCHMARK_ATTESTATION_MANIFEST":
            raise ContractError("ATTESTATION_ROOT_TYPE_INVALID")
        document = attestation.to_dict()
        graph = self.verify(str(document["evidence_manifest_id"]))
        result_id = str(document["benchmark_result_id"])
        result = self._contract(result_id)
        if result.type_name != "BENCHMARK_RESULT":
            raise ContractError("ATTESTATION_RESULT_TYPE_INVALID")
        result_document = result.to_dict()
        if result_document["benchmark_definition_id"] != graph.definition_id:
            raise ContractError("ATTESTATION_RESULT_DEFINITION_MISMATCH")
        if result_document["evidence_manifest_id"] != graph.manifest_id:
            raise ContractError("ATTESTATION_RESULT_MANIFEST_MISMATCH")
        if document["result_evaluator_set_id"] != result_document["result_evaluator_set_id"]:
            raise ContractError("ATTESTATION_RESULT_EVALUATOR_SET_MISMATCH")

        manifest = self._contract(graph.manifest_id).to_dict()
        if tuple(result_document["run_ids"]) != tuple(manifest["run_ids"]):
            raise ContractError("ATTESTATION_RESULT_RUN_INVENTORY_MISMATCH")
        definition = self._contract(graph.definition_id)
        if (
            document["definition_reviewer_set_id"]
            != definition.to_dict()["definition_reviewer_set_id"]
        ):
            raise ContractError("ATTESTATION_DEFINITION_REVIEWER_SET_MISMATCH")
        result_evaluator_set: ReviewerSet | None = None
        for node_id in manifest["node_ids"]:
            node = self._contract(str(node_id)).to_dict()
            if node["kind"] == "RESULT_EVALUATOR_SET":
                result_evaluator_set = self._reviewer_set(str(node["payload_id"]))
                break
        if result_evaluator_set is None:
            raise ContractError("ATTESTATION_RESULT_EVALUATOR_SET_MISSING")
        if (
            result_evaluator_set.role != "RESULT_EVALUATORS"
            or result_document["result_evaluator_set_id"] != result_evaluator_set.content_id
            or document["result_evaluator_set_id"] != result_evaluator_set.content_id
            or definition.to_dict()["result_evaluator_set_id"] != result_evaluator_set.content_id
        ):
            raise ContractError("ATTESTATION_RESULT_EVALUATOR_SET_MISMATCH")
        result_qc_id = document["benchmark_result_qc_id"]
        if result_qc_id is not None:
            qc = qc_from_bytes(self._read(str(result_qc_id)), result_evaluator_set, result)
            if qc.purpose != "BENCHMARK_RESULT_VOTE":
                raise ContractError("ATTESTATION_RESULT_QC_MISMATCH")
        return VerifiedAttestation(
            attestation_id=expected_attestation_id,
            result_id=result_id,
            evidence_manifest_id=graph.manifest_id,
            result_qc_present=result_qc_id is not None,
            decision=str(result_document["decision"]),
        )
