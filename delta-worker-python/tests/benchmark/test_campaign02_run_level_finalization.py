from __future__ import annotations

from dataclasses import replace

import pytest
from campaign02_chain_fixtures import (
    CertifiedBackend,
    FixtureNativeChainVerifier,
    authorization,
    certified_plan,
    certified_result,
    content_id,
    contributions,
    extra_member,
)
from deltatorrent.benchmark.feature008_admission import (
    Feature008AdmissionError,
    Feature008ChainVerifier,
)
from deltatorrent.benchmark.measured_runner import (
    MeasuredRunnerError,
    PrimaryScientificRunner,
)
from deltatorrent.benchmark.observation_writer import (
    ObservationWriterError,
    PrimaryObservationWriter,
)


def _run(plan, identity, measured, result):  # type: ignore[no-untyped-def]
    return PrimaryScientificRunner(
        identity, Feature008ChainVerifier(FixtureNativeChainVerifier())
    ).run(
        plan,
        authorization(),
        CertifiedBackend(plan, measured, result),
    )


def test_complete_certified_round_is_admitted_once() -> None:
    plan, identity = certified_plan()
    measured = contributions(plan)
    result = certified_result(plan, measured)
    run = _run(plan, identity, measured, result)
    assert run.final_checkpoint_id == result.certificate_bundle.apply_qc.value["next_model_hash"]
    assert run.result_class == "CERTIFIED_DELTAREDUCE"
    assert run.round_result.native_chain_admission_receipt_id is not None
    assert run.round_result.native_chain_verifier_id is not None
    PrimaryObservationWriter._verify_native_chain_receipt(plan, run)


def test_writer_rejects_a_native_receipt_binding_substitution() -> None:
    plan, identity = certified_plan()
    measured = contributions(plan)
    run = _run(plan, identity, measured, certified_result(plan, measured))
    tampered_result = replace(
        run.round_result,
        native_chain_verifier_id=content_id("substituted-native-verifier"),
    )
    with pytest.raises(
        ObservationWriterError,
        match="OBSERVATION_NATIVE_CHAIN_RECEIPT_BINDING_MISMATCH",
    ):
        PrimaryObservationWriter._verify_native_chain_receipt(
            plan, replace(run, round_result=tampered_result)
        )


def test_last_ticket_local_identity_cannot_be_substituted_as_final() -> None:
    plan, identity = certified_plan()
    measured = contributions(plan)
    result = replace(
        certified_result(plan, measured), final_checkpoint_id=measured[-1].contribution_id
    )
    with pytest.raises(Feature008AdmissionError, match="FEATURE008_APPLY_QC_BINDING_INVALID"):
        _run(plan, identity, measured, result)


def test_unrelated_per_ticket_certificate_sets_are_not_a_run_finalization() -> None:
    plan, identity = certified_plan(32)
    measured = contributions(plan)
    legacy_sets = tuple(
        (item.ticket_id, tuple(content_id(f"cert:{index}:{n}") for n in range(6)))
        for index, item in enumerate(measured)
    )
    with pytest.raises(MeasuredRunnerError, match="SCIENTIFIC_RUNNER_FINALIZATION_TYPE_INVALID"):
        _run(plan, identity, measured, legacy_sets)


@pytest.mark.parametrize("membership", ["missing", "extra"])
def test_isc_requires_every_planned_ticket_exactly_once(membership: str) -> None:
    plan, identity = certified_plan()
    measured = contributions(plan)
    members = measured[:-1] if membership == "missing" else (*measured, extra_member())
    result = certified_result(plan, measured, isc_members=tuple(members))
    with pytest.raises(Feature008AdmissionError, match="FEATURE008_ISC_MEMBERSHIP_MISMATCH"):
        _run(plan, identity, measured, result)


def test_duplicate_contribution_is_rejected() -> None:
    plan, identity = certified_plan()
    measured = contributions(plan, duplicate_contribution=True)
    result = certified_result(plan, measured)
    with pytest.raises(Feature008AdmissionError, match="FEATURE008_CONTRIBUTION_DUPLICATE"):
        _run(plan, identity, measured, result)


def test_declared_ticket_contribution_pairs_must_match_the_run() -> None:
    plan, identity = certified_plan()
    measured = contributions(plan)
    result = certified_result(plan, measured)
    mismatched = replace(
        result,
        ordered_contribution_ids=tuple(reversed(result.ordered_contribution_ids)),
    )
    with pytest.raises(
        Feature008AdmissionError,
        match="FEATURE008_ORDERED_CONTRIBUTION_SET_MISMATCH",
    ):
        _run(plan, identity, measured, mismatched)


def test_mixed_apc_parent_is_rejected() -> None:
    plan, identity = certified_plan()
    measured = contributions(plan)
    result = certified_result(plan, measured, apc_isc_parent=content_id("another-isc"))
    with pytest.raises(
        Feature008AdmissionError, match="FEATURE008_APC_PARENT_OR_MEMBERSHIP_MISMATCH"
    ):
        _run(plan, identity, measured, result)


def test_incomplete_parameter_shard_set_is_rejected() -> None:
    plan, identity = certified_plan()
    measured = contributions(plan)
    result = certified_result(plan, measured, shard_count=1)
    with pytest.raises(
        Feature008AdmissionError, match="FEATURE008_PARAMETER_SHARD_COVERAGE_INCOMPLETE"
    ):
        _run(plan, identity, measured, result)


def test_aggregate_root_must_be_bound_to_apply_qc() -> None:
    plan, identity = certified_plan()
    measured = contributions(plan)
    result = certified_result(plan, measured, apply_root_parent=content_id("another-root"))
    with pytest.raises(Feature008AdmissionError, match="FEATURE008_APPLY_QC_BINDING_INVALID"):
        _run(plan, identity, measured, result)


def test_apply_qc_checkpoint_must_equal_final_checkpoint() -> None:
    plan, identity = certified_plan()
    measured = contributions(plan)
    result = replace(
        certified_result(plan, measured), final_checkpoint_id=content_id("other-final")
    )
    with pytest.raises(Feature008AdmissionError, match="FEATURE008_APPLY_QC_BINDING_INVALID"):
        _run(plan, identity, measured, result)


def test_parent_checkpoint_must_match_execution_plan() -> None:
    plan, identity = certified_plan()
    measured = contributions(plan)
    result = replace(
        certified_result(plan, measured), parent_checkpoint_id=content_id("other-parent")
    )
    with pytest.raises(Feature008AdmissionError, match="FEATURE008_ROUND_PARENT_MISMATCH"):
        _run(plan, identity, measured, result)


def test_reference_and_certified_result_classes_cannot_be_crossed() -> None:
    plan, identity = certified_plan()
    measured = contributions(plan)
    result = certified_result(plan, measured)
    reference_plan = replace(plan, result_class="REFERENCE", certified_round_policy=None)
    backend = CertifiedBackend(reference_plan, measured, result, result_class="REFERENCE")
    with pytest.raises(MeasuredRunnerError, match="SCIENTIFIC_RUNNER_RESULT_CLASS_MISMATCH"):
        PrimaryScientificRunner(
            identity, Feature008ChainVerifier(FixtureNativeChainVerifier())
        ).run(reference_plan, authorization(), backend)
    backend.finalized = object()
    with pytest.raises(MeasuredRunnerError, match="SCIENTIFIC_RUNNER_FINALIZATION_TYPE_INVALID"):
        _run(plan, identity, measured, backend.finalized)


def test_ticket_permutation_has_one_canonical_run_identity() -> None:
    plan, identity = certified_plan()
    measured = contributions(plan)
    forward = certified_result(plan, measured)
    reverse = certified_result(
        plan,
        measured,
        ordered_ticket_ids=tuple(reversed(tuple(item.ticket_id for item in measured))),
    )
    assert (
        _run(plan, identity, measured, forward).content_id
        == _run(plan, identity, measured, reverse).content_id
    )


def test_certified_runtime_artifacts_and_wals_share_the_run() -> None:
    plan, identity = certified_plan()
    measured = contributions(plan)
    result = certified_result(plan, measured)
    tampered = replace(result, runtime_wal_sha256="0" * 64)
    with pytest.raises(Feature008AdmissionError, match="FEATURE008_RUNTIME_RECEIPT_MISMATCH"):
        _run(plan, identity, measured, tampered)
