from __future__ import annotations

import copy

import pytest
from deltatorrent.benchmark.compatibility import (
    CompatibilityAdmission,
    admit_plan,
    compare_runtime_identities,
)
from deltatorrent.benchmark.contracts import CanonicalContract, ContractError
from deltatorrent.benchmark.decision import (
    GateOutcome,
    all_mandatory_decision,
    build_foundation_result,
)
from deltatorrent.benchmark.orchestrator import plan_benchmark, reconcile_exposure
from deltatorrent.benchmark.profiles import (
    ATTACK_CORPUS,
    plan_tc_netem,
    replay_attack_corpus,
    replay_fault_profile,
    validate_attack_corpus,
)

from .conftest import (
    arm,
    cid,
    definition,
    environment,
    fault_profile,
    network_profile,
    runtime_identity,
    scientific_profile,
)


def _inputs() -> dict[str, object]:
    runtime = runtime_identity()
    scientific = scientific_profile()
    arms = (
        arm("reference", kind="REFERENCE", topology="FLAT", deployment_profile="EMBEDDED_FFM"),
        arm(
            "candidate",
            kind="DELTAREDUCE",
            topology="HIERARCHICAL",
            deployment_profile="EMBEDDED_FFM",
        ),
    )
    networks = (network_profile(),)
    faults = (fault_profile(),)
    benchmark_definition = definition(runtime, scientific, arms, networks, faults)
    env = environment(runtime)
    admission = admit_plan(
        definition=benchmark_definition,
        expected_runtime=runtime,
        actual_runtime=runtime,
        environment=env,
    )
    return {
        "runtime": runtime,
        "scientific": scientific,
        "arms": arms,
        "networks": networks,
        "faults": faults,
        "definition": benchmark_definition,
        "environment": env,
        "admission": admission,
    }


def test_deterministic_planner_expands_exact_matrix_without_execution_authority() -> None:
    values = _inputs()
    kwargs = {
        "definition": values["definition"],
        "runtime_identity": values["runtime"],
        "scientific_profile": values["scientific"],
        "environment": values["environment"],
        "arms": values["arms"],
        "network_profiles": values["networks"],
        "fault_profiles": values["faults"],
        "ticket_ids": (cid("ticket-1"),),
        "compatibility": values["admission"],
    }
    first = plan_benchmark(**kwargs)
    second = plan_benchmark(**kwargs)
    assert first == second
    assert len(first.runs) == 4
    assert first.execution_authorized is False
    assert all(run.manifest.to_dict()["status"] == "PLANNED" for run in first.runs)
    assert all(run.manifest.to_dict()["execution_authorization_id"] is None for run in first.runs)


def test_primary_admission_is_impossible_in_foundation() -> None:
    values = _inputs()
    with pytest.raises(ContractError, match="FOUNDATION_PRIMARY_ADMISSION_FORBIDDEN"):
        admit_plan(
            definition=values["definition"],
            expected_runtime=values["runtime"],
            actual_runtime=values["runtime"],
            environment=values["environment"],
            admission_class="PRIMARY",
        )


def test_planner_rejects_forged_cross_identity_compatibility() -> None:
    values = _inputs()
    alternate = runtime_identity(source_commit="1" * 40, source_tree="2" * 40)
    alternate_environment = environment(
        alternate,
        source_commit="1" * 40,
        source_tree="2" * 40,
    )
    forged = CompatibilityAdmission(
        expected_identity_id=values["runtime"].content_id,
        actual_identity_id=alternate.content_id,
        mismatch_codes=(),
        admitted=True,
        deployment_profile="EMBEDDED_FFM",
    )
    with pytest.raises(ContractError, match="COMPATIBILITY_BINDING_INVALID"):
        plan_benchmark(
            definition=values["definition"],
            runtime_identity=alternate,
            scientific_profile=values["scientific"],
            environment=alternate_environment,
            arms=values["arms"],
            network_profiles=values["networks"],
            fault_profiles=values["faults"],
            ticket_ids=(cid("ticket-1"),),
            compatibility=forged,
        )


@pytest.mark.parametrize(
    "field",
    [
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
    ],
)
def test_every_runtime_identity_mismatch_rejects_exact_admission(field: str) -> None:
    expected = runtime_identity()
    actual = runtime_identity(**{field: cid(f"changed-{field}")})
    admission = compare_runtime_identities(expected, actual)
    assert admission.admitted is False
    assert admission.mismatch_codes == (f"{field.upper()}_MISMATCH",)


def test_evidence_class_and_environment_identity_joins_are_exact() -> None:
    expected = runtime_identity()
    actual = runtime_identity(evidence_class="FOUNDATION_ONLY")
    admission = compare_runtime_identities(expected, actual)
    assert admission.admitted is False
    assert admission.mismatch_codes == ("EVIDENCE_CLASS_MISMATCH",)
    values = _inputs()
    drifted_environment = environment(values["runtime"], source_tree="0" * 40)
    with pytest.raises(ContractError, match="ENVIRONMENT_SOURCE_TREE_MISMATCH"):
        admit_plan(
            definition=values["definition"],
            expected_runtime=values["runtime"],
            actual_runtime=values["runtime"],
            environment=drifted_environment,
        )


@pytest.mark.parametrize(
    ("field", "replacement", "error"),
    [
        ("source_commit", "0" * 40, "ENVIRONMENT_SOURCE_COMMIT_MISMATCH"),
        ("source_tree", "0" * 40, "ENVIRONMENT_SOURCE_TREE_MISMATCH"),
        ("sbom_id", cid("wrong-sbom"), "ENVIRONMENT_SBOM_ID_MISMATCH"),
        (
            "dependency_lock_ids",
            [cid("unrelated-lock")],
            "ENVIRONMENT_DEPENDENCY_LOCK_SET_INCOMPLETE",
        ),
        ("binary_ids", [cid("unrelated-binary")], "ENVIRONMENT_BINARY_SET_INCOMPLETE"),
    ],
)
def test_planner_revalidates_environment_instead_of_trusting_admission(
    field: str,
    replacement: str | list[str],
    error: str,
) -> None:
    values = _inputs()
    document = values["environment"].to_dict()
    document[field] = replacement
    forged_environment = CanonicalContract.from_dict(document)
    with pytest.raises(ContractError, match=error):
        plan_benchmark(
            definition=values["definition"],
            runtime_identity=values["runtime"],
            scientific_profile=values["scientific"],
            environment=forged_environment,
            arms=values["arms"],
            network_profiles=values["networks"],
            fault_profiles=values["faults"],
            ticket_ids=(cid("ticket-1"),),
            compatibility=values["admission"],
        )


def test_planner_rejects_arm_runtime_and_frozen_ticket_mismatch() -> None:
    values = _inputs()
    arms = list(values["arms"])
    wrong_arm = arm(
        "candidate",
        kind="DELTAREDUCE",
        topology="HIERARCHICAL",
        deployment_profile="ISOLATED_SIDECAR",
    )
    definition_with_wrong_arm = definition(
        values["runtime"],
        values["scientific"],
        (arms[0], wrong_arm),
        values["networks"],
        values["faults"],
    )
    admission = admit_plan(
        definition=definition_with_wrong_arm,
        expected_runtime=values["runtime"],
        actual_runtime=values["runtime"],
        environment=values["environment"],
    )
    with pytest.raises(ContractError, match="ARM_DEPLOYMENT_MISMATCH"):
        plan_benchmark(
            definition=definition_with_wrong_arm,
            runtime_identity=values["runtime"],
            scientific_profile=values["scientific"],
            environment=values["environment"],
            arms=(arms[0], wrong_arm),
            network_profiles=values["networks"],
            fault_profiles=values["faults"],
            ticket_ids=(cid("ticket-1"),),
            compatibility=admission,
        )
    with pytest.raises(ContractError, match="TICKET_PLAN_MISMATCH"):
        plan_benchmark(
            definition=values["definition"],
            runtime_identity=values["runtime"],
            scientific_profile=values["scientific"],
            environment=values["environment"],
            arms=values["arms"],
            network_profiles=values["networks"],
            fault_profiles=values["faults"],
            ticket_ids=(cid("different-ticket"),),
            compatibility=values["admission"],
        )


def test_token_domain_and_scientific_reconciliation_is_exact() -> None:
    reference = scientific_profile()
    reconcile_exposure(reference, scientific_profile())
    candidate_doc = reference.to_dict()
    candidate_doc["domain_tokens"] = {"clinical": 3999, "general": 6001}
    candidate = CanonicalContract.from_dict(candidate_doc)
    with pytest.raises(ContractError, match="domain_tokens"):
        reconcile_exposure(reference, candidate)
    candidate_doc = reference.to_dict()
    candidate_doc["ticket_ids"] = [cid("different-ticket")]
    with pytest.raises(ContractError, match="ticket_ids"):
        reconcile_exposure(reference, CanonicalContract.from_dict(candidate_doc))


def test_planner_rejects_dependency_entries_disconnected_from_science() -> None:
    values = _inputs()
    definition_document = values["definition"].to_dict()
    dependency = definition_document["dependencies"][0]
    dependency["content_id"] = cid("unlicensed-scientific-input")
    dependency["locator"] = "cas://sha256/" + dependency["content_id"].removeprefix("sha256:")
    disconnected = CanonicalContract.from_dict(definition_document)
    with pytest.raises(ContractError, match="SCIENTIFIC_DEPENDENCY_JOIN_MISMATCH"):
        plan_benchmark(
            definition=disconnected,
            runtime_identity=values["runtime"],
            scientific_profile=values["scientific"],
            environment=values["environment"],
            arms=values["arms"],
            network_profiles=values["networks"],
            fault_profiles=values["faults"],
            ticket_ids=(cid("ticket-1"),),
            compatibility=values["admission"],
        )


def test_network_and_fault_plans_remain_deterministic_and_simulated() -> None:
    network = network_profile()
    first = plan_tc_netem(network, interface="eth0")
    second = plan_tc_netem(network, interface="eth0")
    assert first == second
    assert first.label == "SIMULATED"
    assert first.apply_argv[0:3] == ("tc", "qdisc", "replace")
    assert "0.1000%" in first.apply_argv
    assert "0.0100%" in first.apply_argv
    assert first.duration_ms == 60_000
    assert first.seed == 101
    assert first.partition_after_ms == 30_000
    trace = replay_fault_profile(fault_profile())
    assert trace == replay_fault_profile(fault_profile())
    assert trace.label == "SIMULATED"
    assert trace.expected_terminals == ("CONTINUE", "RECOVER", "SAFE_ABORT")


def test_real_wan_and_reordered_fault_events_are_rejected() -> None:
    network = network_profile().to_dict()
    network["label"] = "REAL_WAN"
    with pytest.raises(ContractError, match="SIMULATED"):
        CanonicalContract.from_dict(network)
    fault = fault_profile().to_dict()
    events = copy.deepcopy(fault["events"])
    assert isinstance(events, list)
    fault["events"] = list(reversed(events))
    with pytest.raises(ContractError, match="NOT_SORTED"):
        CanonicalContract.from_dict(fault)
    fault = fault_profile().to_dict()
    fault["events"][0]["expected_terminal"] = "RECOVER"
    with pytest.raises(ContractError, match="TERMINAL_MISMATCH"):
        CanonicalContract.from_dict(fault)


def test_attack_corpus_is_frozen_and_complete() -> None:
    validate_attack_corpus(ATTACK_CORPUS)
    trace = replay_attack_corpus()
    assert trace == replay_attack_corpus()
    assert trace.expected_terminals == ("REJECT",) * len(ATTACK_CORPUS)
    with pytest.raises(ContractError, match="ATTACK_CORPUS_MISMATCH"):
        validate_attack_corpus(ATTACK_CORPUS[:-1])


def test_all_mandatory_decision_is_fail_closed_and_non_overridable() -> None:
    passed = (
        GateOutcome("exactness", True, "PASS"),
        GateOutcome("science", True, "PASS"),
    )
    assert all_mandatory_decision(passed, result_eligible=True) == "GO"
    assert all_mandatory_decision(passed, result_eligible=False) == "NOT_EVALUATED"
    failed = (
        GateOutcome("exactness", True, "PASS"),
        GateOutcome("science", True, "MISSING"),
    )
    assert all_mandatory_decision(failed, result_eligible=True) == "NO_GO"


def test_decision_rejects_truthy_non_boolean_policy_inputs() -> None:
    with pytest.raises(ContractError, match="GATE_OUTCOME_INVALID"):
        GateOutcome("science", 0, "MISSING")  # type: ignore[arg-type]
    passed = (GateOutcome("science", True, "PASS"),)
    with pytest.raises(ContractError, match="RESULT_ELIGIBILITY_INVALID"):
        all_mandatory_decision(passed, result_eligible="false")  # type: ignore[arg-type]


def test_foundation_result_rejects_decision_and_gate_list_forgery() -> None:
    result = build_foundation_result(
        definition_id=cid("definition"),
        evidence_manifest_id=cid("manifest"),
        result_evaluator_set_id=cid("evaluators"),
        run_ids=("fixture-run",),
        gates=(GateOutcome("science", True, "PASS"),),
        limitations=("NO_PRIMARY_OBSERVATIONS",),
        commentary="fixture",
    )
    forged = result.to_dict()
    forged["decision"] = "NO_GO"
    with pytest.raises(ContractError, match="RESULT_DECISION_MISMATCH"):
        CanonicalContract.from_dict(forged)
    failed = build_foundation_result(
        definition_id=cid("definition"),
        evidence_manifest_id=cid("manifest"),
        result_evaluator_set_id=cid("evaluators"),
        run_ids=("fixture-run",),
        gates=(GateOutcome("science", True, "FAIL"),),
        limitations=("NO_PRIMARY_OBSERVATIONS",),
        commentary="fixture",
    )
    forged = failed.to_dict()
    forged["failed_gates"] = []
    with pytest.raises(ContractError, match="RESULT_FAILED_GATES_MISMATCH"):
        CanonicalContract.from_dict(forged)
