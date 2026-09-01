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
    CampaignExecutionPlan,
    CertifiedRoundPolicy,
    ParameterShardKey,
    load_domain_manifest,
    load_ticket_plan,
    load_workload_contract,
)
from deltatorrent.benchmark.campaign02_binding import (
    Campaign02BindingError,
    CertifiedPlanBinding,
    QualifiedRuntimeLineage,
    compile_campaign02_execution_set,
    expected_round_id,
)
from deltatorrent.benchmark.definition import BenchmarkDefinition
from deltatorrent.benchmark.governance import (
    BenchmarkReviewValidatorSet,
    VerifiedDefinitionAttestation,
    create_definition_vote,
    finalize_definition_attestation,
)
from deltatorrent.benchmark.primary import PrimaryRunError, adapter_for
from deltatorrent.cli.main import main
from deltatorrent.protocol.canonical import canonical_json_bytes, sha256_content_id

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "configs/benchmark/campaign-02"
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


def _attestation(definition_id: str) -> VerifiedDefinitionAttestation:
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
    return finalize_definition_attestation(
        benchmark_definition_id=definition_id,
        validator_set=validator_set,
        votes=votes,
        verified_at=NOW,
    )


def _inputs() -> tuple[
    BenchmarkDefinition,
    VerifiedDefinitionAttestation,
    dict[str, object],
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
    attestation = _attestation(definition.content_id)
    authorization: dict[str, object] = {
        "benchmark_definition_id": definition.content_id,
        "campaign_id": "campaign-02",
        "definition_attestation_id": attestation.content_id,
        "domain_manifest_id": domain_manifest.content_id,
        "environment_id": runtime.environment_id,
        "evaluation_runner_id": runtime.evaluation_runner_id,
        "formal_semantics_id": value["formal_semantics_id"],
        "observation_writer_id": runtime.writer_id,
        "primary_execution_authorized": True,
        "qualified_runtime_lineage_id": runtime.content_id,
        "schema_version": "1.0.0",
        "scientific_runner_id": runtime.runner_id,
        "source_commit": runtime.source_commit,
        "source_tree": runtime.source_tree,
        "ticket_plan_id": ticket_plan.content_id,
        "type_name": "BENCHMARK_EXECUTION_AUTHORIZATION",
        "workload_contract_id": workload.content_id,
    }
    return (
        definition,
        attestation,
        authorization,
        workload,
        domain_manifest,
        ticket_plan,
        arms,
        runtime,
    )


def _compile(**updates: object):  # type: ignore[no-untyped-def]
    names = (
        "definition",
        "attestation",
        "authorization",
        "workload",
        "domain_manifest",
        "ticket_plan",
        "arms",
        "runtime_lineage",
    )
    values = dict(zip(names, _inputs(), strict=True))
    values.update(updates)
    return compile_campaign02_execution_set(**values)  # type: ignore[arg-type]


def test_campaign02_compiler_creates_exact_15_plan_matrix() -> None:
    execution = _compile()
    assert len(execution.plans) == 15
    assert len({item.content_id for item in execution.plans}) == 15
    assert all(item.ticket_count == 32 for item in execution.plans)
    assert all(item.tokens_per_ticket == 32_768 for item in execution.plans)
    assert all(item.optimizer_steps_per_ticket == 32 for item in execution.plans)
    assert all(item.processed_tokens == 1_048_576 for item in execution.plans)
    assert sum(item.result_class == "REFERENCE" for item in execution.plans) == 3
    assert sum(item.result_class == "CERTIFIED_DELTAREDUCE" for item in execution.plans) == 12
    assert all(
        (item.result_class == "CERTIFIED_DELTAREDUCE") == (item.certified_round_policy is not None)
        for item in execution.plans
    )


def test_campaign02_compiler_rejects_missing_authorization() -> None:
    with pytest.raises(Campaign02BindingError, match="CAMPAIGN02_EXECUTION_AUTHORIZATION_REQUIRED"):
        _compile(authorization=None)


def test_campaign02_compiler_rejects_wrong_definition_and_attestation() -> None:
    definition, attestation, *_ = _inputs()
    wrong_value = dict(definition.raw)
    wrong_value["workload_contract_id"] = _id("wrong-workload")
    wrong_definition = BenchmarkDefinition.from_dict(wrong_value)
    with pytest.raises(
        Campaign02BindingError, match="CAMPAIGN02_DEFINITION_EXECUTION_BINDING_MISMATCH"
    ):
        _compile(definition=wrong_definition)
    wrong_attestation = replace(attestation, benchmark_definition_id=_id("wrong-definition"))
    with pytest.raises(Campaign02BindingError, match="CAMPAIGN02_DEFINITION_ATTESTATION_MISMATCH"):
        _compile(attestation=wrong_attestation)


def test_campaign02_compiler_rejects_wrong_source_tree() -> None:
    *_, runtime = _inputs()
    with pytest.raises(
        Campaign02BindingError, match="CAMPAIGN02_DEFINITION_EXECUTION_BINDING_MISMATCH"
    ):
        _compile(runtime_lineage=replace(runtime, source_tree="c" * 40))


def test_campaign02_legacy_primary_adapter_is_forbidden() -> None:
    definition, _, _, _, _, _, arms, _ = _inputs()
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
    execution = _compile()
    assert (
        len(
            {
                execution.workload_contract_id,
                execution.domain_manifest_id,
                execution.ticket_plan_id,
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
