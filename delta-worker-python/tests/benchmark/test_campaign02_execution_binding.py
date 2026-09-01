from __future__ import annotations

import base64
import json
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from deltatorrent.benchmark.arms import ArmSpec
from deltatorrent.benchmark.campaign02 import (
    CAMPAIGN02_GATE_STAGES,
    CAMPAIGN02_STAGE_TASK_IDS,
    CampaignExecutionPlan,
    CertifiedRoundPolicy,
    ParameterShardKey,
    authorize_execution_class,
    load_domain_manifest,
    load_ticket_plan,
    load_workload_contract,
)
from deltatorrent.benchmark.campaign02_binding import (
    Campaign02BindingError,
    Campaign02PlanCatalog,
    CertifiedPlanBinding,
    QualifiedRuntimeLineage,
    compile_campaign02_execution_set,
    compile_campaign02_plan_catalog,
    expected_round_id,
)
from deltatorrent.benchmark.definition import BenchmarkDefinition, load_definition
from deltatorrent.benchmark.governance import (
    BenchmarkReviewValidatorSet,
    SignedDefinitionVote,
    VerifiedDefinitionAttestation,
    create_definition_vote,
    finalize_definition_attestation,
)
from deltatorrent.benchmark.primary import ExecutionPlan, PrimaryRunError, adapter_for
from deltatorrent.cli.main import main
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "configs/benchmark/campaign-02"
FIXTURES = ROOT / "delta-worker-python/tests/fixtures/benchmark"
NOW = datetime(2026, 9, 1, 12, 0, tzinfo=UTC)


def _id(label: str) -> str:
    return sha256_content_id(label.encode())


def _arms(workload_id: str) -> tuple[ArmSpec, ...]:
    values = (
        ("scientific-reference", "SCIENTIFIC_REFERENCE", "PYTHON", "SINGLE_NODE_REFERENCE"),
        ("flat-embedded", "CERTIFIED_QLORA", "EMBEDDED_FFM", "FLAT_BFT"),
        (
            "hierarchy-embedded",
            "CERTIFIED_QLORA",
            "EMBEDDED_FFM",
            "HIERARCHICAL_BFT",
        ),
        ("flat-sidecar", "CERTIFIED_QLORA", "ISOLATED_SIDECAR", "FLAT_BFT"),
        (
            "hierarchy-sidecar",
            "CERTIFIED_QLORA",
            "ISOLATED_SIDECAR",
            "HIERARCHICAL_BFT",
        ),
    )
    result: list[ArmSpec] = []
    for arm_name, kind, deployment, topology in values:
        document = {
            "allowed_differences": ["arithmetic", "deployment_profile", "topology"],
            "arm_id": arm_name,
            "deployment_profile": deployment,
            "kind": kind,
            "mandatory": True,
            "topology": topology,
            "workload_identity": workload_id,
        }
        result.append(
            ArmSpec(
                content_id=sha256_content_id(canonical_json_bytes(document)),
                arm_id=arm_name,
                kind=kind,
                deployment_profile=deployment,
                mandatory=True,
                workload_identity=workload_id,
                runtime_profile_id=_id(f"runtime:{deployment}:{topology}"),
                topology=topology,
            )
        )
    return tuple(result)


def _policy(arm: ArmSpec, seed: int, repetition: int) -> CertifiedRoundPolicy:
    return CertifiedRoundPolicy(
        round_id=expected_round_id(arm.arm_id, seed, repetition),
        height=1,
        view=0,
        round_config_id=_id(f"round-config:{arm.arm_id}:{seed}"),
        validator_epoch_id=_id("validator-epoch"),
        parameter_schema_id=_id("parameter-schema"),
        arithmetic_profile_id=_id("arithmetic-profile"),
        accumulator_proof_id=_id("accumulator-proof"),
        apply_arithmetic_profile_id=_id("apply-profile"),
        validator_ids=("validator-0", "validator-1", "validator-2", "validator-3"),
        quorum_threshold=3,
        required_shards=(ParameterShardKey("wikitext-en", "adapter-shard-0"),),
    )


def _validator_set() -> tuple[BenchmarkReviewValidatorSet, tuple[Ed25519PrivateKey, ...]]:
    private_keys = tuple(Ed25519PrivateKey.generate() for _ in range(4))
    validators = []
    for index, private_key in enumerate(private_keys):
        public_key = private_key.public_key().public_bytes(
            serialization.Encoding.Raw, serialization.PublicFormat.Raw
        )
        validators.append(
            {
                "controller_id": f"independent-controller-{index}",
                "key_custody_statement_id": _id(f"custody:{index}"),
                "public_key": base64.b64encode(public_key).decode("ascii"),
                "public_key_id": sha256_content_id(
                    b"deltareduce.010.benchmark-review-key.v1\0" + public_key
                ),
                "signature_algorithm": "ED25519",
                "valid_from": "2026-08-01T00:00:00Z",
                "valid_until": None,
                "validator_id": f"benchmark-validator-{index}",
            }
        )
    return (
        BenchmarkReviewValidatorSet.from_dict(
            {
                "campaign_id": "campaign-02",
                "f_b": 1,
                "formal_semantics_id": (
                    "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
                ),
                "purpose": "BENCHMARK_DEFINITION_REVIEW",
                "schema_version": "1.0.0",
                "type_name": "BENCHMARK_REVIEW_VALIDATOR_SET",
                "validators": validators,
            }
        ),
        private_keys,
    )


def _attestation(
    definition_id: str,
) -> tuple[
    VerifiedDefinitionAttestation,
    BenchmarkReviewValidatorSet,
    tuple[SignedDefinitionVote, ...],
]:
    validator_set, private_keys = _validator_set()
    votes = tuple(
        create_definition_vote(
            benchmark_definition_id=definition_id,
            validator_set=validator_set,
            signer_id=f"benchmark-validator-{index}",
            submitted_at=NOW,
            private_key=private_keys[index],
        )
        for index in range(3)
    )
    attestation = finalize_definition_attestation(
        benchmark_definition_id=definition_id,
        validator_set=validator_set,
        votes=votes,
        verified_at=NOW,
    )
    return attestation, validator_set, votes


def _inputs() -> tuple[
    BenchmarkDefinition,
    dict[str, object],
    BenchmarkReviewValidatorSet,
    tuple[SignedDefinitionVote, ...],
    object,
    object,
    object,
    tuple[ArmSpec, ...],
    QualifiedRuntimeLineage,
]:
    workload = load_workload_contract(CONFIG / "workload-v2.json")
    domain_manifest = load_domain_manifest(CONFIG / "domain-manifest-v1.json")
    ticket_plan = load_ticket_plan(CONFIG / "ticket-plan-v1.json", workload, domain_manifest)
    arms = _arms(workload.content_id)
    seeds = (2026090101, 2026090102, 2026090103)
    bindings = tuple(
        sorted(
            (
                CertifiedPlanBinding(
                    arm.content_id,
                    arm.arm_id,
                    seed,
                    repetition,
                    _policy(arm, seed, repetition),
                )
                for arm in arms
                if arm.kind == "CERTIFIED_QLORA"
                for repetition, seed in enumerate(seeds, start=1)
            ),
            key=lambda item: (item.arm_name, item.repetition, item.seed),
        )
    )
    evaluator_profiles = tuple(
        json.loads((CONFIG / "evaluators" / f"{name}-v1.json").read_bytes())
        for name in ("wikitext", "lambada", "hellaswag")
    )
    runtime = QualifiedRuntimeLineage(
        source_commit="a" * 40,
        source_tree="b" * 40,
        environment_id=_id("environment"),
        image_id=_id("image"),
        hardware_id=_id("hardware"),
        runner_id=_id("scientific-runner"),
        evaluation_runner_id=_id("evaluation-runner"),
        writer_id=_id("observation-writer"),
        model_id=_id("base-model"),
        parent_checkpoint_id=_id("base-model"),
        tokenizer_id=str(evaluator_profiles[0]["tokenizer_id"]),
        dataset_ids=tuple(str(item["dataset_id"]) for item in evaluator_profiles),
        evaluation_profile_ids=tuple(_id(f"profile:{index}") for index in range(3)),
        evaluation_implementation_ids=tuple(
            _id(f"implementation:{name}") for name in ("wikitext", "lambada", "hellaswag")
        ),
        certified_plan_bindings=bindings,
    )
    value = json.loads((ROOT / "configs/benchmark/primary.yaml").read_bytes())
    value.update(
        {
            "B": workload.tokens_per_ticket,
            "H": workload.optimizer_steps_per_ticket,
            "arm_ids": [item.content_id for item in arms],
            "base_model_id": runtime.parent_checkpoint_id,
            "campaign_id": "campaign-02",
            "dataset_manifest_id": _id("campaign02-dataset-manifest"),
            "domain_manifest_id": domain_manifest.content_id,
            "evaluation_ids": list(runtime.evaluation_implementation_ids),
            "image_id": runtime.image_id,
            "native_build_id": _id("native-build"),
            "primary": True,
            "qualified_runtime_lineage_id": runtime.content_id,
            "repetitions": 3,
            "schema_version": "2.0.0",
            "seeds": list(seeds),
            "source_commit": runtime.source_commit,
            "source_tree": runtime.source_tree,
            "ticket_plan_id": ticket_plan.content_id,
            "tokenizer_id": runtime.tokenizer_id,
            "workload_contract_id": workload.content_id,
        }
    )
    for metric in value["metric_definitions"]:
        metric["repetitions"] = 3
    definition = BenchmarkDefinition.from_dict(value)
    attestation, validator_set, votes = _attestation(definition.content_id)
    return (
        definition,
        attestation.document,
        validator_set,
        votes,
        workload,
        domain_manifest,
        ticket_plan,
        arms,
        runtime,
    )


def _compile(**updates: object):  # type: ignore[no-untyped-def]
    names = (
        "definition",
        "attestation_document",
        "validator_set",
        "votes",
        "workload",
        "domain_manifest",
        "ticket_plan",
        "arms",
        "runtime_lineage",
    )
    values = dict(zip(names, _inputs(), strict=True))
    values.update(updates)
    return compile_campaign02_plan_catalog(**values)  # type: ignore[arg-type]


def _stage_authorization(
    catalog: Campaign02PlanCatalog,
    stage: str,
    predecessors: tuple[str, ...] = (),
) -> dict[str, object]:
    return {
        "allowed_plan_ids": list(catalog.plan_ids_for_stage(stage)),
        "authorized_stage": stage,
        "authorized_task_ids": list(CAMPAIGN02_STAGE_TASK_IDS[stage]),
        "benchmark_definition_id": catalog.definition_id,
        "campaign_id": "campaign-02",
        "definition_attestation_id": catalog.attestation_id,
        "formal_semantics_id": (
            "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
        ),
        "plan_catalog_id": catalog.content_id,
        "real_wan_authorized": False,
        "required_predecessor_receipt_ids": list(predecessors),
        "result_qc_authorized": False,
        "schema_version": "1.0.0",
        "stage_a_authorized": stage == "STAGE_A_EXACTNESS",
        "stage_b_authorized": stage == "STAGE_B_SCIENTIFIC",
        "stage_c_authorized": stage == "STAGE_C_EMULATED_WAN",
        "type_name": "BENCHMARK_STAGE_EXECUTION_AUTHORIZATION",
    }


def test_campaign02_compiler_creates_exact_15_plan_matrix_per_stage() -> None:
    catalog = _compile()
    assert isinstance(catalog, Campaign02PlanCatalog)
    assert catalog.document["base_plan_count"] == 15
    assert catalog.document["execution_authorized"] is False
    assert len(catalog.plans) == 45
    assert len({item.content_id for item in catalog.plans}) == 45
    assert all(len(catalog.plan_ids_for_stage(stage)) == 15 for stage in CAMPAIGN02_GATE_STAGES)
    assert all(item.ticket_count == 32 for item in catalog.plans)
    assert all(item.tokens_per_ticket == 32_768 for item in catalog.plans)
    assert all(item.optimizer_steps_per_ticket == 32 for item in catalog.plans)
    assert all(item.processed_tokens == 1_048_576 for item in catalog.plans)
    assert sum(item.result_class == "REFERENCE" for item in catalog.plans) == 9
    assert sum(item.result_class == "CERTIFIED_DELTAREDUCE" for item in catalog.plans) == 36
    assert all(
        (item.result_class == "CERTIFIED_DELTAREDUCE") == (item.certified_round_policy is not None)
        for item in catalog.plans
    )


def test_campaign02_plan_catalog_requires_no_execution_authorization() -> None:
    catalog = _compile()
    assert catalog.document["status"] == "COMPILED_NOT_EXECUTABLE_REQUIRES_STAGE_AUTHORIZATION"
    assert all(item.execution_authorization_id is None for item in catalog.plans)


def test_campaign02_compiler_rejects_wrong_definition_and_attestation() -> None:
    definition, attestation_document, validator_set, votes, *_ = _inputs()
    wrong_value = dict(definition.raw)
    wrong_value["workload_contract_id"] = _id("wrong-workload")
    wrong_definition = BenchmarkDefinition.from_dict(wrong_value)
    with pytest.raises(
        Campaign02BindingError, match="CAMPAIGN02_DEFINITION_EXECUTION_BINDING_MISMATCH"
    ):
        _compile(definition=wrong_definition)
    wrong_attestation = dict(attestation_document)
    wrong_attestation["benchmark_definition_id"] = _id("wrong-definition")
    with pytest.raises(Campaign02BindingError, match="CAMPAIGN02_DEFINITION_ATTESTATION_INVALID"):
        _compile(
            attestation_document=wrong_attestation,
            validator_set=validator_set,
            votes=votes,
        )


def test_campaign02_compiler_rejects_wrong_source_tree() -> None:
    *_, runtime = _inputs()
    with pytest.raises(
        Campaign02BindingError, match="CAMPAIGN02_DEFINITION_EXECUTION_BINDING_MISMATCH"
    ):
        _compile(runtime_lineage=replace(runtime, source_tree="c" * 40))


def test_campaign02_legacy_primary_adapter_is_forbidden() -> None:
    definition, *_, arms, _ = _inputs()
    with pytest.raises(PrimaryRunError, match="LEGACY_PRIMARY_PATH_FORBIDDEN"):
        adapter_for(arms[0]).plan(
            definition,
            arms[0],
            environment_manifest_id=_id("environment"),
            network_profile_id=definition.network_profile_ids[0],
            fault_profile_id=definition.fault_profile_ids[0],
            seed=definition.seeds[0],
            repetition=1,
        )


def test_exact_superseded_a4160_is_parseable_but_all_adapter_execution_is_forbidden() -> None:
    definition = load_definition(FIXTURES / "campaign-02-superseded-definition-a4160.json")
    assert definition.content_id == (
        "sha256:a4160af58ba310135bd86d03b2427c5034ae231f481e6229314e0e61d12b97af"
    )
    assert definition.campaign_id is None
    arm = ArmSpec(
        definition.arm_ids[0],
        "historical-reference",
        "SCIENTIFIC_REFERENCE",
        "PYTHON",
        True,
        _id("historical-workload"),
        _id("historical-runtime"),
        "SINGLE_NODE_REFERENCE",
    )
    adapter = adapter_for(arm)
    with pytest.raises(PrimaryRunError, match="LEGACY_PRIMARY_PATH_FORBIDDEN"):
        adapter.plan(
            definition,
            arm,
            environment_manifest_id=_id("environment"),
            network_profile_id=definition.network_profile_ids[0],
            fault_profile_id=definition.fault_profile_ids[0],
            seed=definition.seeds[0],
            repetition=1,
        )
    legacy_plan = ExecutionPlan(
        definition_id=definition.content_id,
        arm=arm,
        environment_manifest_id=_id("environment"),
        network_profile_id=definition.network_profile_ids[0],
        fault_profile_id=definition.fault_profile_ids[0],
        seed=definition.seeds[0],
        repetition=1,
        processed_tokens=definition.B,
        domains=tuple(item.domain_id for item in definition.domain_weights),
        ticket_plan_id=definition.ticket_plan_id,
        parent_checkpoint_id=definition.base_model_id,
        evaluation_ids=definition.evaluation_ids,
    )
    with pytest.raises(PrimaryRunError, match="LEGACY_PRIMARY_PATH_FORBIDDEN"):
        adapter.admit(legacy_plan, object())  # type: ignore[arg-type]


def test_historical_campaign01_definition_remains_audit_parseable_not_executable() -> None:
    definition = load_definition(FIXTURES / "historical-campaign-01-definition-dd607.json")
    assert definition.content_id == (
        "sha256:dd607651128bca0b8edfa861093945b0bac2355c93d9d45b4c8b08457fba4244"
    )
    assert definition.campaign_id is None
    arm = ArmSpec(
        definition.arm_ids[0],
        "historical-reference",
        "SCIENTIFIC_REFERENCE",
        "PYTHON",
        True,
        _id("historical-workload"),
        _id("historical-runtime"),
        "SINGLE_NODE_REFERENCE",
    )
    with pytest.raises(PrimaryRunError, match="LEGACY_PRIMARY_PATH_FORBIDDEN"):
        adapter_for(arm).plan(
            definition,
            arm,
            environment_manifest_id=_id("environment"),
            network_profile_id=definition.network_profile_ids[0],
            fault_profile_id=definition.fault_profile_ids[0],
            seed=definition.seeds[0],
            repetition=1,
        )


def test_campaign02_reference_and_certified_classes_cannot_cross() -> None:
    *_, arms, _ = _inputs()
    wrong_reference = replace(arms[0], kind="CERTIFIED_QLORA")
    with pytest.raises(Campaign02BindingError, match="CAMPAIGN02_ARM_MATRIX_MISMATCH"):
        _compile(arms=(wrong_reference, *arms[1:]))
    certified = next(
        item for item in _compile().plans if item.result_class == "CERTIFIED_DELTAREDUCE"
    )
    with pytest.raises(ValueError, match="CAMPAIGN02_RESULT_CLASS_POLICY_MISMATCH"):
        replace(certified, certified_round_policy=None)


def test_campaign02_distinct_workload_domain_and_ticket_plan_ids() -> None:
    catalog = _compile()
    assert (
        len(
            {
                catalog.workload_contract_id,
                catalog.domain_manifest_id,
                catalog.ticket_plan_id,
            }
        )
        == 3
    )


def test_campaign02_plan_total_cannot_fall_back_to_per_ticket_b() -> None:
    plan = _compile().plans[0]
    assert plan.tokens_per_ticket == 32_768
    assert plan.processed_tokens != plan.tokens_per_ticket
    with pytest.raises(ValueError, match="CAMPAIGN02_PLAN_TOKEN_RECONCILIATION"):
        replace(plan, total_tokens_per_arm_run=plan.tokens_per_ticket)


def test_campaign02_plan_requires_exact_ticket_table() -> None:
    plan = _compile().plans[0]
    with pytest.raises(ValueError, match="CAMPAIGN02_PLAN_TOKEN_RECONCILIATION"):
        replace(plan, tickets=plan.tickets[:-1])
    with pytest.raises(ValueError, match="CAMPAIGN02_PLAN_TICKET_ORDER_INVALID"):
        replace(
            plan,
            tickets=(replace(plan.tickets[0], ordinal=1), *plan.tickets[1:]),
        )


def test_campaign02_execution_plan_type_is_strict_runner_contract() -> None:
    assert all(isinstance(item, CampaignExecutionPlan) for item in _compile().plans)


def test_caller_constructed_verified_attestation_cannot_enter_binder() -> None:
    fake = VerifiedDefinitionAttestation(
        benchmark_definition_id=_id("definition"),
        validator_set_id=_id("validator-set"),
        f_b=1,
        ordered_signers=("a", "b", "c"),
        ordered_vote_ids=(_id("vote-a"), _id("vote-b"), _id("vote-c")),
        signature_set_root=_id("signature-root"),
        verified_at=NOW,
    )
    with pytest.raises(
        Campaign02BindingError,
        match="CAMPAIGN02_UNVERIFIED_ATTESTATION_INTERFACE_FORBIDDEN",
    ):
        compile_campaign02_execution_set(attestation=fake)


def test_campaign02_catalog_compiler_reverifies_every_detached_signature() -> None:
    _, attestation_document, validator_set, votes, *_ = _inputs()
    forged = replace(
        votes[0],
        signature=bytes([votes[0].signature[0] ^ 1]) + votes[0].signature[1:],
    )
    forged_attestation = dict(attestation_document)
    vote_ids = list(forged_attestation["ordered_vote_ids"])
    vote_ids[vote_ids.index(votes[0].content_id)] = forged.content_id
    forged_attestation["ordered_vote_ids"] = vote_ids
    with pytest.raises(Campaign02BindingError, match="BENCHMARK_DEFINITION_SIGNATURE_INVALID"):
        _compile(
            attestation_document=forged_attestation,
            validator_set=validator_set,
            votes=(forged, *votes[1:]),
        )


def test_stage_a_authorizes_only_exact_stage_a_catalog_plans() -> None:
    catalog = _compile()
    stage_a = next(item for item in catalog.plans if item.gate_stage == "STAGE_A_EXACTNESS")
    authorization = _stage_authorization(catalog, "STAGE_A_EXACTNESS")
    authorize_execution_class(authorization, stage_a, plan_catalog=catalog)

    stage_b = next(item for item in catalog.plans if item.gate_stage == "STAGE_B_SCIENTIFIC")
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_EXECUTION_NOT_AUTHORIZED"):
        authorize_execution_class(authorization, stage_b, plan_catalog=catalog)
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_RUNNER_ROLE_NOT_AUTHORIZED"):
        authorize_execution_class(
            authorization,
            stage_a,
            plan_catalog=catalog,
            runner_role="EVALUATION_RUNNER",
        )
    stage_c = next(item for item in catalog.plans if item.gate_stage == "STAGE_C_EMULATED_WAN")
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_EXECUTION_NOT_AUTHORIZED"):
        authorize_execution_class(authorization, stage_c, plan_catalog=catalog)


def test_stage_authorization_rejects_generic_extra_and_inexact_plan_sets() -> None:
    catalog = _compile()
    plan = next(item for item in catalog.plans if item.gate_stage == "STAGE_A_EXACTNESS")
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_AUTHORIZATION_FIELDS_INVALID"):
        authorize_execution_class(
            {"primary_execution_authorized": True},
            plan,
            plan_catalog=catalog,
        )
    authorization = _stage_authorization(catalog, "STAGE_A_EXACTNESS")
    authorization["extra"] = True
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_AUTHORIZATION_FIELDS_INVALID"):
        authorize_execution_class(authorization, plan, plan_catalog=catalog)
    authorization = _stage_authorization(catalog, "STAGE_A_EXACTNESS")
    authorization["allowed_plan_ids"] = authorization["allowed_plan_ids"][:-1]  # type: ignore[index]
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_EXECUTION_NOT_AUTHORIZED"):
        authorize_execution_class(authorization, plan, plan_catalog=catalog)
    authorization = _stage_authorization(catalog, "STAGE_A_EXACTNESS")
    authorization["benchmark_definition_id"] = _id("wrong-definition")
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_EXECUTION_NOT_AUTHORIZED"):
        authorize_execution_class(authorization, plan, plan_catalog=catalog)


def test_stage_b_and_c_require_exact_predecessor_gate_receipts() -> None:
    catalog = _compile()
    stage_a_receipt = _id("accepted-stage-a-gate-receipt")
    stage_b_receipt = _id("accepted-stage-b-gate-receipt")
    stage_b = next(item for item in catalog.plans if item.gate_stage == "STAGE_B_SCIENTIFIC")
    authorization_b = _stage_authorization(
        catalog,
        "STAGE_B_SCIENTIFIC",
        (stage_a_receipt,),
    )
    authorize_execution_class(
        authorization_b,
        stage_b,
        plan_catalog=catalog,
        predecessor_gate_receipt_ids=(stage_a_receipt,),
        runner_role="SCIENTIFIC_RUNNER",
    )
    with pytest.raises(ValueError, match="CAMPAIGN02_STAGE_PREDECESSOR_INVALID"):
        authorize_execution_class(
            authorization_b,
            stage_b,
            plan_catalog=catalog,
            predecessor_gate_receipt_ids=(_id("wrong-stage-a-receipt"),),
        )

    stage_c = next(item for item in catalog.plans if item.gate_stage == "STAGE_C_EMULATED_WAN")
    authorization_c = _stage_authorization(
        catalog,
        "STAGE_C_EMULATED_WAN",
        tuple(sorted((stage_a_receipt, stage_b_receipt))),
    )
    authorize_execution_class(
        authorization_c,
        stage_c,
        plan_catalog=catalog,
        predecessor_gate_receipt_ids=tuple(sorted((stage_a_receipt, stage_b_receipt))),
        runner_role="NETWORK_FAULT_RUNNER",
    )


@pytest.mark.parametrize(
    ("command", "suffix"),
    (
        ("plan-primary", ()),
        ("execute-primary", ("--", "runner")),
        ("collect-primary", ("observation.json",)),
        ("verify-primary-runs", ()),
    ),
)
def test_all_legacy_primary_cli_routes_reject_campaign02(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    command: str,
    suffix: tuple[str, ...],
) -> None:
    definition, *_ = _inputs()
    definition_path = tmp_path / "definition-v2.json"
    definition_path.write_bytes(canonical_json_bytes(definition.raw))
    common = (
        str(definition_path),
        str(tmp_path / "attestation.json"),
        str(tmp_path / "arms.json"),
        str(tmp_path / "environment.json"),
        str(tmp_path / "output"),
    )
    options: tuple[str, ...] = ()
    if command == "execute-primary":
        options = ("--runner-id", _id("runner"))
    assert main(("benchmark", command, *options, *common, *suffix)) == 2
    assert "LEGACY_PRIMARY_PATH_FORBIDDEN" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("command", "suffix"),
    (
        ("plan-primary", ()),
        ("execute-primary", ("--", "runner")),
        ("collect-primary", ("observation.json",)),
        ("verify-primary-runs", ()),
    ),
)
def test_exact_a4160_and_unsigned_6c594_are_rejected_by_every_legacy_cli_route(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    command: str,
    suffix: tuple[str, ...],
) -> None:
    common = (
        str(FIXTURES / "campaign-02-superseded-definition-a4160.json"),
        str(FIXTURES / "campaign-02-superseded-attestation-6c594.json"),
        str(tmp_path / "arms.json"),
        str(tmp_path / "environment.json"),
        str(tmp_path / "output"),
    )
    options: tuple[str, ...] = ()
    if command == "execute-primary":
        options = ("--runner-id", _id("runner"))
    assert main(("benchmark", command, *options, *common, *suffix)) == 2
    assert "LEGACY_PRIMARY_PATH_FORBIDDEN" in capsys.readouterr().err


def test_exact_a4160_cannot_be_preregistered_for_executable_primary_use(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert (
        main(
            (
                "benchmark",
                "preregister",
                str(FIXTURES / "campaign-02-superseded-definition-a4160.json"),
                str(FIXTURES / "campaign-02-superseded-attestation-6c594.json"),
                str(tmp_path / "store"),
            )
        )
        == 2
    )
    assert "LEGACY_PRIMARY_PATH_FORBIDDEN" in capsys.readouterr().err
