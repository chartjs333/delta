from __future__ import annotations

from pathlib import Path

import pytest
from deltatorrent.benchmark.contracts import CanonicalContract, ContractError
from deltatorrent.benchmark.decision import GateOutcome, build_foundation_result
from deltatorrent.benchmark.evidence import EvidenceGraph, EvidenceGraphBuilder
from deltatorrent.benchmark.receipts import verify_receipt_chain
from deltatorrent.benchmark.verifier import OfflineEvidenceVerifier

from .conftest import (
    arm,
    cid,
    completed_run,
    definition,
    environment,
    fault_profile,
    fixture_receipts,
    metrics,
    network_profile,
    reviewer_set,
    runtime_identity,
    scientific_profile,
)


def _artifacts(*, disconnect_dependency: bool = False) -> dict[str, object]:
    runtime = runtime_identity()
    scientific = scientific_profile(repetitions=1, seeds=[17])
    definition_reviewers = reviewer_set("DEFINITION_REVIEWERS")
    result_evaluators = reviewer_set("RESULT_EVALUATORS", key_offset=8)
    arms = (
        arm("reference", kind="REFERENCE", topology="FLAT", deployment_profile="EMBEDDED_FFM"),
        arm(
            "candidate",
            kind="DELTAREDUCE",
            topology="HIERARCHICAL",
            deployment_profile="EMBEDDED_FFM",
        ),
    )
    network = network_profile()
    fault = fault_profile()
    benchmark_definition = definition(
        runtime,
        scientific,
        arms,
        (network,),
        (fault,),
        definition_reviewer_set_id=definition_reviewers.content_id,
        result_evaluator_set_id=result_evaluators.content_id,
    )
    if disconnect_dependency:
        definition_document = benchmark_definition.to_dict()
        dependency = definition_document["dependencies"][0]
        dependency["content_id"] = cid("unlicensed-scientific-input")
        dependency["locator"] = "cas://sha256/" + dependency["content_id"].removeprefix("sha256:")
        benchmark_definition = CanonicalContract.from_dict(definition_document)
    env = environment(runtime)
    ticket_id = cid("ticket-1")
    runs: list[CanonicalContract] = []
    receipt_groups: list[tuple[CanonicalContract, ...]] = []
    run_metrics: list[CanonicalContract] = []
    for label, benchmark_arm in zip(("reference", "candidate"), arms, strict=True):
        run_id = f"foundation-fixture-{label}"
        receipts = fixture_receipts(
            benchmark_definition.content_id,
            benchmark_arm.content_id,
            runtime,
            ticket_id,
            run_id,
        )
        runs.append(
            completed_run(
                benchmark_definition.content_id,
                benchmark_arm.content_id,
                scientific,
                network,
                fault,
                env,
                ticket_id,
                receipts,
                run_id,
            )
        )
        receipt_groups.append(receipts)
        run_metrics.append(metrics(run_id))
    return {
        "runtime": runtime,
        "scientific": scientific,
        "definition_reviewers": definition_reviewers,
        "result_evaluators": result_evaluators,
        "arms": arms,
        "definition": benchmark_definition,
        "environment": env,
        "network": network,
        "fault": fault,
        "receipt_groups": tuple(receipt_groups),
        "runs": tuple(runs),
        "metrics": tuple(run_metrics),
    }


def _artifact_labels() -> tuple[str, ...]:
    labels = {
        "abi-header",
        "abi-schema",
        "adapter-candidate",
        "adapter-reference",
        "checkpoint",
        "compiler-lock",
        "cpp-core",
        "cuda-profile-unqualified",
        "dataset",
        "durability-evidence",
        "effect",
        "evaluator-a",
        "evaluator-b",
        "fixture-binary-build",
        "fixture-corpus",
        "fixture-gpu",
        "fixture-hardware",
        "fixture-image",
        "fixture-sbom",
        "formal-report",
        "java-binary",
        "java-dependencies",
        "jdk-25-toolchain",
        "license-dataset",
        "license-evaluator-000",
        "license-evaluator-001",
        "license-model",
        "license-optimizer",
        "license-ticket-000",
        "license-ticket-plan",
        "license-tokenizer",
        "model",
        "model-input",
        "native-runtime",
        "netty-profile",
        "normalized-update",
        "opaque-native-submit-receipt",
        "optimizer",
        "protocol-registry",
        "python-3.12-profile",
        "python-lock",
        "python-wheel",
        "state-root",
        "ticket-1",
        "ticket-plan",
        "tokenizer",
        "transport-envelope",
        "wal-record",
    }
    return tuple(sorted(labels))


def _graph(
    root: Path,
    *,
    disconnect_dependency: bool = False,
) -> tuple[EvidenceGraphBuilder, EvidenceGraph, dict[str, object]]:
    values = _artifacts(disconnect_dependency=disconnect_dependency)
    benchmark_definition = values["definition"]
    assert isinstance(benchmark_definition, CanonicalContract)
    builder = EvidenceGraphBuilder(root, definition_id=benchmark_definition.content_id)
    prior: tuple[str, ...] = ()
    ordinal = 0

    def add(kind: str, payload: object, run_id: str = "foundation-global") -> None:
        nonlocal ordinal, prior
        node = builder.add_node(
            kind=kind,
            payload=payload,
            run_id=run_id,
            ordinal=ordinal,
            dependencies=prior,
        )
        prior = (node.reference.content_id,)
        ordinal += 1

    add("DEFINITION_REVIEWER_SET", values["definition_reviewers"])
    add("RESULT_EVALUATOR_SET", values["result_evaluators"])
    add("DEFINITION", benchmark_definition)
    add("RUNTIME_IDENTITY", values["runtime"])
    add("SCIENTIFIC_PROFILE", values["scientific"])
    for benchmark_arm in values["arms"]:
        add("ARM", benchmark_arm)
    add("ENVIRONMENT", values["environment"])
    add("NETWORK_PROFILE", values["network"])
    add("FAULT_PROFILE", values["fault"])
    for label in _artifact_labels():
        node = builder.add_bound_artifact(
            name="artifact-" + str(ordinal),
            artifact_kind="FIXTURE_INPUT",
            value=label.encode("utf-8"),
            media_type="application/octet-stream",
            run_id="foundation-global",
            ordinal=ordinal,
            dependencies=prior,
        )
        prior = (node.reference.content_id,)
        ordinal += 1
    for run, receipts, run_metrics in zip(
        values["runs"], values["receipt_groups"], values["metrics"], strict=True
    ):
        run_id = run.to_dict()["run_id"]
        for receipt in receipts:
            add("STAGE_RECEIPT", receipt, str(run_id))
        add("RUN_MANIFEST", run, str(run_id))
        add("METRICS", run_metrics, str(run_id))
    run_ids = tuple(sorted(str(run.to_dict()["run_id"]) for run in values["runs"]))
    return builder, builder.seal(run_ids=run_ids), values


def _object_path(root: Path, object_id: str) -> Path:
    digest = object_id.removeprefix("sha256:")
    return root / "objects" / "sha256" / digest[:2] / digest


def _publish_contract(builder: EvidenceGraphBuilder, contract: CanonicalContract) -> str:
    reference = builder.store.publish_bytes(
        contract.canonical_bytes,
        media_type="application/json",
        schema_id="SCHEMA-BENCHMARK-TEST-MUTATION-010-V1",
    )
    return reference.content_id


def test_bound_artifact_rejects_media_schema_drift_before_publish(tmp_path: Path) -> None:
    builder = EvidenceGraphBuilder(tmp_path, definition_id=cid("definition"))
    with pytest.raises(ContractError, match="EVIDENCE_RAW_ARTIFACT_MEDIA_TYPE_INVALID"):
        builder.add_bound_artifact(
            name="artifact",
            artifact_kind="FIXTURE_INPUT",
            value=b"opaque",
            media_type="application/json",
            run_id="foundation-global",
            ordinal=0,
        )
    assert not list(tmp_path.rglob("*"))


def test_complete_content_addressed_graph_verifies_offline(tmp_path: Path) -> None:
    _, graph, _ = _graph(tmp_path)
    result = OfflineEvidenceVerifier(tmp_path).verify(graph.manifest.reference.content_id)
    assert result.status == "PASS"
    assert result.definition_id == graph.definition_id
    assert result.node_count == len(graph.nodes)
    assert result.run_count == 2
    assert result.bound_artifact_count == len(_artifact_labels())


def test_offline_graph_rejects_dependency_entries_disconnected_from_science(
    tmp_path: Path,
) -> None:
    _, graph, _ = _graph(tmp_path, disconnect_dependency=True)
    with pytest.raises(ContractError, match="SCIENTIFIC_DEPENDENCY_JOIN_MISMATCH"):
        OfflineEvidenceVerifier(tmp_path).verify(graph.manifest.reference.content_id)


def test_terminal_attestation_verifies_without_claiming_result_qc(tmp_path: Path) -> None:
    builder, graph, values = _graph(tmp_path)
    result_evaluators = values["result_evaluators"]
    result = build_foundation_result(
        definition_id=graph.definition_id,
        evidence_manifest_id=graph.manifest.reference.content_id,
        result_evaluator_set_id=result_evaluators.content_id,
        run_ids=tuple(sorted(str(run.to_dict()["run_id"]) for run in values["runs"])),
        gates=(GateOutcome("foundation-contracts", True, "PASS"),),
        limitations=("NO_PRIMARY_OBSERVATIONS",),
        commentary="Foundation fixture only; no qualifying gate is evaluated.",
    )
    attestation = builder.attest(graph=graph, result=result)
    verified = OfflineEvidenceVerifier(tmp_path).verify_attestation(
        attestation.manifest.reference.content_id
    )
    assert verified.decision == "NOT_EVALUATED"
    assert verified.result_qc_present is False


def test_builder_rejects_result_with_different_run_inventory(tmp_path: Path) -> None:
    builder, graph, values = _graph(tmp_path)
    result = build_foundation_result(
        definition_id=graph.definition_id,
        evidence_manifest_id=graph.manifest.reference.content_id,
        result_evaluator_set_id=values["result_evaluators"].content_id,
        run_ids=("unrelated-run",),
        gates=(GateOutcome("foundation-contracts", True, "PASS"),),
        limitations=("NO_PRIMARY_OBSERVATIONS",),
        commentary="Foundation fixture only; no qualifying gate is evaluated.",
    )
    with pytest.raises(ContractError, match="EVIDENCE_RESULT_RUN_INVENTORY_MISMATCH"):
        builder.attest(graph=graph, result=result)


@pytest.mark.parametrize(
    ("mutation", "expected_error"),
    [
        ("run_inventory", "ATTESTATION_RESULT_RUN_INVENTORY_MISMATCH"),
        ("evaluator_set", "ATTESTATION_RESULT_EVALUATOR_SET_MISMATCH"),
    ],
)
def test_terminal_attestation_rejects_unjoined_result_context(
    tmp_path: Path,
    mutation: str,
    expected_error: str,
) -> None:
    builder, graph, values = _graph(tmp_path)
    result_evaluators = values["result_evaluators"]
    result = build_foundation_result(
        definition_id=graph.definition_id,
        evidence_manifest_id=graph.manifest.reference.content_id,
        result_evaluator_set_id=result_evaluators.content_id,
        run_ids=tuple(sorted(str(run.to_dict()["run_id"]) for run in values["runs"])),
        gates=(GateOutcome("foundation-contracts", True, "PASS"),),
        limitations=("NO_PRIMARY_OBSERVATIONS",),
        commentary="Foundation fixture only; no qualifying gate is evaluated.",
    )
    valid_attestation = builder.attest(graph=graph, result=result)
    result_document = result.to_dict()
    attestation_document = valid_attestation.manifest.contract.to_dict()
    if mutation == "run_inventory":
        result_document["run_ids"] = ["unrelated-run"]
    else:
        unrelated_set_id = cid("unrelated-result-evaluator-set")
        result_document["result_evaluator_set_id"] = unrelated_set_id
        attestation_document["result_evaluator_set_id"] = unrelated_set_id
    mutated_result = CanonicalContract.from_dict(result_document)
    attestation_document["benchmark_result_id"] = _publish_contract(builder, mutated_result)
    mutated_attestation = CanonicalContract.from_dict(attestation_document)
    attestation_id = _publish_contract(builder, mutated_attestation)
    with pytest.raises(ContractError, match=expected_error):
        OfflineEvidenceVerifier(tmp_path).verify_attestation(attestation_id)


def test_receipt_chain_binds_all_three_stages_ticket_and_native_refs() -> None:
    values = _artifacts()
    receipts = values["receipt_groups"][0]
    run = values["runs"][0]
    verify_receipt_chain(
        run_manifest=run,
        receipts=receipts,
        runtime_identity=values["runtime"],
    )
    native = receipts[-1].to_dict()
    assert set(native["native_opaque_refs"]) == {
        "checkpoint_id",
        "durability_evidence_id",
        "effect_id",
        "state_root_id",
        "submit_receipt_id",
        "wal_record_id",
    }


@pytest.mark.parametrize(
    "mutation", ["missing", "reordered", "predecessor", "source", "component", "ticket"]
)
def test_receipt_chain_mutations_fail_closed(mutation: str) -> None:
    values = _artifacts()
    receipts = list(values["receipt_groups"][0])
    if mutation == "missing":
        receipts.pop(1)
    elif mutation == "reordered":
        receipts[0], receipts[1] = receipts[1], receipts[0]
    else:
        target = receipts[1].to_dict()
        if mutation == "predecessor":
            target["previous_receipt_id"] = cid("wrong-predecessor")
        elif mutation == "source":
            target["source_commit"] = "0" * 40
        elif mutation == "ticket":
            target["ticket_id"] = cid("wrong-ticket")
        else:
            target["component_identity_id"] = cid("wrong-component")
        receipts[1] = CanonicalContract.from_dict(target)
    with pytest.raises(ContractError, match="RECEIPT_CHAIN"):
        verify_receipt_chain(
            run_manifest=values["runs"][0],
            receipts=tuple(receipts),
            runtime_identity=values["runtime"],
        )


def test_planned_run_rejects_undeclared_actual_receipts() -> None:
    values = _artifacts()
    planned = values["runs"][0].to_dict()
    planned.update(
        {
            "evidence_class": "FOUNDATION_ONLY",
            "execution_mode": "PLAN_ONLY",
            "stage_receipt_ids": [],
            "status": "PLANNED",
        }
    )
    with pytest.raises(ContractError, match="PLANNED_RUN_RECEIPTS_FORBIDDEN"):
        verify_receipt_chain(
            run_manifest=CanonicalContract.from_dict(planned),
            receipts=values["receipt_groups"][0],
            runtime_identity=values["runtime"],
        )


def test_missing_and_mutated_objects_fail_hash_or_presence_checks(tmp_path: Path) -> None:
    _, graph, _ = _graph(tmp_path)
    verifier = OfflineEvidenceVerifier(tmp_path)
    node_id = graph.nodes[0].reference.content_id
    node_path = _object_path(tmp_path, node_id)
    original = node_path.read_bytes()
    node_path.unlink()
    with pytest.raises(ContractError, match="EVIDENCE_OBJECT_MISSING"):
        verifier.verify(graph.manifest.reference.content_id)
    node_path.write_bytes(original + b"\n")
    with pytest.raises(ContractError, match="EVIDENCE_OBJECT_HASH_MISMATCH"):
        verifier.verify(graph.manifest.reference.content_id)


def test_wrong_expected_root_is_not_discovered_or_substituted(tmp_path: Path) -> None:
    _graph(tmp_path)
    with pytest.raises(ContractError, match="EVIDENCE_OBJECT_MISSING"):
        OfflineEvidenceVerifier(tmp_path).verify(cid("another-root"))


def test_builder_refuses_incomplete_required_kind_set(tmp_path: Path) -> None:
    values = _artifacts()
    benchmark_definition = values["definition"]
    assert isinstance(benchmark_definition, CanonicalContract)
    builder = EvidenceGraphBuilder(tmp_path, definition_id=benchmark_definition.content_id)
    builder.add_node(
        kind="RUNTIME_IDENTITY",
        payload=values["runtime"],
        run_id="foundation-global",
        ordinal=0,
    )
    with pytest.raises(ContractError, match="EVIDENCE_REQUIRED_KIND_MISSING"):
        builder.seal(run_ids=("foundation-fixture-candidate",))


def test_fixture_run_cannot_claim_primary_or_execution_authority() -> None:
    values = _artifacts()
    run = values["runs"][0].to_dict()
    run["primary_eligible"] = True
    with pytest.raises(ContractError, match="PRIMARY_ELIGIBILITY_FORBIDDEN"):
        CanonicalContract.from_dict(run)
    run = values["runs"][0].to_dict()
    run["execution_authorization_id"] = cid("fake-authority")
    with pytest.raises(ContractError, match="FIXTURE_EXECUTION_AUTHORITY_FORBIDDEN"):
        CanonicalContract.from_dict(run)
