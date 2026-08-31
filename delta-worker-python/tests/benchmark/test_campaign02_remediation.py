from __future__ import annotations

import hashlib
import json
import re
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest
from deltatorrent.benchmark.campaign02 import (
    Campaign02ContractError,
    CampaignExecutionPlan,
    TicketAllocation,
    allocate_tickets,
    authorize_execution_class,
    execution_authorization_id,
    load_workload_contract,
)
from deltatorrent.benchmark.evaluators.common import (
    EvaluationContext,
    EvaluatorContractError,
    load_evaluator_profile,
)
from deltatorrent.benchmark.evaluators.hellaswag import HellaSwagEvaluator, HellaSwagRecord
from deltatorrent.benchmark.evaluators.hf_backend import HuggingFaceCausalLMBackend
from deltatorrent.benchmark.evaluators.lambada import LambadaEvaluator, LambadaRecord
from deltatorrent.benchmark.evaluators.wikitext import WikiTextEvaluator, WikiTextRecord
from deltatorrent.benchmark.measured_runner import (
    ComponentIdentity,
    EvaluatorBinding,
    PrimaryEvaluationRunner,
    PrimaryScientificRunner,
    RawArtifact,
    TicketMeasurement,
)
from deltatorrent.benchmark.observation_writer import (
    ObservationWriterError,
    PrimaryObservationWriter,
)
from deltatorrent.benchmark.quality import QualityError, verify_measured_outputs

ROOT = Path(__file__).resolve().parents[3]
CONFIG = ROOT / "configs/benchmark/campaign-02"
FIXTURES = ROOT / "delta-protocol/fixtures/010/campaign-02/evaluators"


def _id(label: str) -> str:
    return "sha256:" + hashlib.sha256(label.encode()).hexdigest()


class _FixtureScoringBackend:
    def __init__(self, *, model_id: str, tokenizer_id: str) -> None:
        self._model_id = model_id
        self._tokenizer_id = tokenizer_id
        self._vocabulary: dict[str, int] = {}

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def tokenizer_id(self) -> str:
        return self._tokenizer_id

    def encode(self, text: str, *, add_bos: bool, add_eos: bool) -> tuple[int, ...]:
        assert not add_bos and not add_eos
        result: list[int] = []
        for token in re.findall(r"\S+", text):
            if token not in self._vocabulary:
                self._vocabulary[token] = len(self._vocabulary) + 1
            result.append(self._vocabulary[token])
        return tuple(result)

    def token_log_probabilities(self, input_ids: tuple[int, ...]) -> tuple[Decimal, ...]:
        return tuple(Decimal("-1") for _ in input_ids[1:])

    def encode_continuation(
        self, prefix: str, continuation: str
    ) -> tuple[tuple[int, ...], tuple[int, ...]]:
        return (
            self.encode(prefix, add_bos=False, add_eos=False),
            self.encode(continuation, add_bos=False, add_eos=False),
        )

    def greedy_tokens(self, prefix_ids: tuple[int, ...], count: int) -> tuple[int, ...]:
        assert prefix_ids and count > 0
        blue = self._vocabulary.setdefault("blue", len(self._vocabulary) + 1)
        return tuple(blue for _ in range(count))


class _FixtureScientificBackend:
    source_class = "NON_PRIMARY_FIXTURE"
    certified = False

    def __init__(self, environment_id: str, model_id: str) -> None:
        self.environment_id = environment_id
        self.model_id = model_id

    def execute_ticket(
        self, plan: CampaignExecutionPlan, ticket: TicketAllocation
    ) -> TicketMeasurement:
        return TicketMeasurement(
            ticket_id=ticket.ticket_id,
            domain_id=ticket.domain_id,
            processed_tokens=ticket.tokens_per_ticket,
            optimizer_steps=ticket.optimizer_steps,
            checkpoint_id=_id(f"checkpoint:{ticket.ordinal}"),
            contribution_id=_id(f"contribution:{ticket.ordinal}"),
            certificate_ids=(),
            artifacts=(
                RawArtifact(
                    f"ticket-{ticket.ordinal}.bin",
                    "application/octet-stream",
                    f"measured:{ticket.ticket_id}".encode(),
                ),
            ),
        )


def _component(kind: str, path: str) -> ComponentIdentity:
    return ComponentIdentity(
        component=kind,
        source_commit="a" * 40,
        source_tree="b" * 40,
        executable_hashes=((path, _id(path)),),
        environment_id=_id("environment"),
        image_id=_id("image"),
        hardware_compatibility_class_id=_id("hardware-class"),
        model_data_staging_policy_id=_id("staging"),
        timeout_policy_id=_id("timeout"),
        output_schema_ids=(_id(f"schema:{kind}"),),
        create_only_store_policy_id=_id("create-only"),
    )


def _profiles() -> tuple[object, ...]:
    return tuple(
        load_evaluator_profile(CONFIG / "evaluators" / f"{name}-v1.json")
        for name in ("wikitext", "lambada", "hellaswag")
    )


def _remediation_authorization() -> dict[str, object]:
    return json.loads(
        (
            ROOT / "reports/benchmark/campaigns/campaign-02/remediation-authorization.json"
        ).read_bytes()
    )


def _smoke_plan(
    scientific: ComponentIdentity,
    evaluation: ComponentIdentity,
    writer: ComponentIdentity,
) -> CampaignExecutionPlan:
    tickets = tuple(
        TicketAllocation(
            ticket_id=_id(f"ticket:{index}"),
            domain_id="wikitext-en",
            ordinal=index,
            tokens_per_optimizer_step=2,
            optimizer_steps=2,
            tokens_per_ticket=4,
        )
        for index in range(2)
    )
    profiles = _profiles()
    return CampaignExecutionPlan(
        execution_class="NON_PRIMARY_SMOKE",
        campaign_id="campaign-02",
        benchmark_definition_id=_id("non-primary-definition"),
        definition_attestation_id=_id("non-primary-attestation"),
        execution_authorization_id=execution_authorization_id(_remediation_authorization()),
        arm_id=_id("fixture-arm"),
        seed=7,
        repetition=1,
        source_commit="a" * 40,
        source_tree="b" * 40,
        environment_id=_id("environment"),
        image_id=_id("image"),
        hardware_id=_id("hardware"),
        runner_id=scientific.content_id,
        evaluation_runner_id=evaluation.content_id,
        writer_id=writer.content_id,
        workload_id=_id("smoke-workload"),
        tokens_per_optimizer_step=2,
        optimizer_steps_per_ticket=2,
        tokens_per_ticket=4,
        ticket_count=2,
        total_tokens_per_arm_run=8,
        model_id=_id("base-model"),
        tokenizer_id=profiles[0].tokenizer_id,
        dataset_ids=tuple(item.dataset_id for item in profiles),
        evaluation_profile_ids=tuple(item.content_id for item in profiles),
        evaluation_implementation_ids=tuple(
            _id(f"implementation:{item.evaluator_id}") for item in profiles
        ),
        tickets=tickets,
    )


def _fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES / name).read_bytes())


def _context(profile: object, model_id: str = _id("model")) -> EvaluationContext:
    return EvaluationContext(
        execution_plan_id=_id("plan"),
        checkpoint_id=model_id,
        model_id=model_id,
        tokenizer_id=profile.tokenizer_id,
        dataset_id=profile.dataset_id,
        environment_id=_id("environment"),
        evaluator_profile_id=profile.content_id,
        evaluator_implementation_id=_id(f"implementation:{profile.evaluator_id}"),
    )


def test_campaign02_workload_reconciles_ticket_and_arm_totals() -> None:
    workload = load_workload_contract(CONFIG / "workload-v2.json")
    tickets = allocate_tickets(workload)
    assert workload.tokens_per_ticket == 32_768
    assert workload.total_tokens_per_arm_run == 1_048_576
    assert len(tickets) == 32
    assert sum(item.tokens_per_ticket for item in tickets) == 1_048_576


def test_campaign02_workload_rejects_per_run_b_reinterpretation() -> None:
    value = json.loads((CONFIG / "workload-v2.json").read_bytes())
    value["total_tokens_per_arm_run"] = 32_768
    with pytest.raises(Campaign02ContractError, match="CAMPAIGN02_ARM_TOKEN_RECONCILIATION"):
        type(load_workload_contract(CONFIG / "workload-v2.json")).from_dict(value)


def test_execution_plan_derives_processed_tokens_and_rejects_drift() -> None:
    scientific = _component("PRIMARY_SCIENTIFIC_RUNNER", "scientific.py")
    evaluation = _component("PRIMARY_EVALUATION_RUNNER", "evaluation.py")
    writer = _component("PRIMARY_OBSERVATION_WRITER", "writer.py")
    plan = _smoke_plan(scientific, evaluation, writer)
    assert plan.processed_tokens == 8
    with pytest.raises(Campaign02ContractError, match="CAMPAIGN02_PLAN_TOKEN_RECONCILIATION"):
        replace(plan, total_tokens_per_arm_run=7)


def test_remediation_authorization_cannot_start_primary_execution() -> None:
    scientific = _component("PRIMARY_SCIENTIFIC_RUNNER", "scientific.py")
    evaluation = _component("PRIMARY_EVALUATION_RUNNER", "evaluation.py")
    writer = _component("PRIMARY_OBSERVATION_WRITER", "writer.py")
    primary = replace(
        _smoke_plan(scientific, evaluation, writer), execution_class="PRIMARY_MEASURED"
    )
    authorization = _remediation_authorization()
    with pytest.raises(
        Campaign02ContractError, match="CAMPAIGN02_PRIMARY_EXECUTION_NOT_AUTHORIZED"
    ):
        authorize_execution_class(authorization, primary)


def test_non_primary_execution_rejects_unbound_authorization() -> None:
    scientific = _component("PRIMARY_SCIENTIFIC_RUNNER", "scientific.py")
    evaluation = _component("PRIMARY_EVALUATION_RUNNER", "evaluation.py")
    writer = _component("PRIMARY_OBSERVATION_WRITER", "writer.py")
    plan = _smoke_plan(scientific, evaluation, writer)
    authorization = {**_remediation_authorization(), "status": "TAMPERED"}
    with pytest.raises(
        Campaign02ContractError, match="CAMPAIGN02_EXECUTION_AUTHORIZATION_ID_MISMATCH"
    ):
        authorize_execution_class(authorization, plan)


def test_wikitext_positive_negative_and_overlap_golden() -> None:
    profile = _profiles()[0]
    evaluator = WikiTextEvaluator(profile)
    backend = _FixtureScoringBackend(model_id=_id("model"), tokenizer_id=profile.tokenizer_id)
    positive = _fixture("wikitext-positive-v1.json")
    result = evaluator.evaluate(
        _context(profile),
        backend,
        tuple(WikiTextRecord(**item) for item in positive["records"]),
    )
    assert result.item_count == positive["expected"]["item_count"]
    assert result.scored_token_count == positive["expected"]["scored_token_count"]
    assert {item.metric_id: item.value for item in result.metrics} == positive["expected"][
        "metrics"
    ]
    long_result = evaluator.evaluate(
        _context(profile),
        backend,
        (WikiTextRecord("wikitext-en", " ".join(["token"] * 2600)),),
    )
    assert long_result.scored_token_count == 2599
    negative = _fixture("wikitext-negative-v1.json")
    with pytest.raises(EvaluatorContractError, match=negative["expected_error"]):
        evaluator.evaluate(
            _context(profile),
            backend,
            tuple(WikiTextRecord(**item) for item in negative["records"]),
        )


def test_lambada_positive_and_negative_golden() -> None:
    profile = _profiles()[1]
    evaluator = LambadaEvaluator(profile)
    backend = _FixtureScoringBackend(model_id=_id("model"), tokenizer_id=profile.tokenizer_id)
    positive = _fixture("lambada-positive-v1.json")
    result = evaluator.evaluate(
        _context(profile),
        backend,
        tuple(LambadaRecord(**item) for item in positive["records"]),
    )
    assert result.scored_token_count == positive["expected"]["scored_token_count"]
    assert {item.metric_id: item.value for item in result.metrics} == positive["expected"][
        "metrics"
    ]
    negative = _fixture("lambada-negative-v1.json")
    with pytest.raises(EvaluatorContractError, match=negative["expected_error"]):
        evaluator.evaluate(
            _context(profile),
            backend,
            tuple(LambadaRecord(**item) for item in negative["records"]),
        )


def test_huggingface_continuation_assigns_boundary_token_to_target() -> None:
    class _Model:
        def eval(self) -> None:
            return None

    class _Tokenizer:
        bos_token_id = None
        eos_token_id = None

        def __call__(self, _text: str, **_options: object) -> dict[str, object]:
            return {
                "input_ids": [10, 20, 30],
                "offset_mapping": [(0, 4), (4, 8), (8, 11)],
            }

    backend = HuggingFaceCausalLMBackend(
        _Model(),
        _Tokenizer(),
        model_id=_id("model"),
        tokenizer_id=_id("tokenizer"),
        device="cpu",
    )
    prefix_ids, target_ids = backend.encode_continuation("alpha ", "beta")
    assert prefix_ids == (10,)
    assert target_ids == (20, 30)


def test_hellaswag_positive_and_negative_golden() -> None:
    profile = _profiles()[2]
    evaluator = HellaSwagEvaluator(profile)
    backend = _FixtureScoringBackend(model_id=_id("model"), tokenizer_id=profile.tokenizer_id)
    positive = _fixture("hellaswag-positive-v1.json")
    result = evaluator.evaluate(
        _context(profile),
        backend,
        tuple(
            HellaSwagRecord(item["ctx_a"], item["ctx_b"], tuple(item["endings"]), item["label"])
            for item in positive["records"]
        ),
    )
    assert result.scored_token_count == positive["expected"]["scored_token_count"]
    assert {item.metric_id: item.value for item in result.metrics} == positive["expected"][
        "metrics"
    ]
    negative = _fixture("hellaswag-negative-v1.json")
    with pytest.raises(EvaluatorContractError, match=negative["expected_error"]):
        evaluator.evaluate(
            _context(profile),
            backend,
            tuple(
                HellaSwagRecord(item["ctx_a"], item["ctx_b"], tuple(item["endings"]), item["label"])
                for item in negative["records"]
            ),
        )


def test_production_runners_and_writer_publish_only_typed_smoke(tmp_path: Path) -> None:
    scientific_identity = _component("PRIMARY_SCIENTIFIC_RUNNER", "scientific.py")
    evaluation_identity = _component("PRIMARY_EVALUATION_RUNNER", "evaluation.py")
    writer_identity = _component("PRIMARY_OBSERVATION_WRITER", "writer.py")
    plan = _smoke_plan(scientific_identity, evaluation_identity, writer_identity)
    profiles = _profiles()
    bindings = (
        EvaluatorBinding(
            profiles[0], _id("implementation:wikitext"), WikiTextEvaluator(profiles[0])
        ),
        EvaluatorBinding(profiles[1], _id("implementation:lambada"), LambadaEvaluator(profiles[1])),
        EvaluatorBinding(
            profiles[2], _id("implementation:hellaswag"), HellaSwagEvaluator(profiles[2])
        ),
    )
    scientific_run = PrimaryScientificRunner(scientific_identity).run(
        plan,
        _remediation_authorization(),
        _FixtureScientificBackend(plan.environment_id, plan.model_id),
    )
    backends = {
        item.profile.evaluator_id: _FixtureScoringBackend(
            model_id=scientific_run.final_checkpoint_id,
            tokenizer_id=plan.tokenizer_id,
        )
        for item in bindings
    }
    datasets = {
        "wikitext": (WikiTextRecord("wikitext-en", "alpha beta gamma"),),
        "lambada": (LambadaRecord("the sky blue"),),
        "hellaswag": (HellaSwagRecord("A person", "moves", ("left", "right"), 0),),
    }
    evaluations = PrimaryEvaluationRunner(evaluation_identity, bindings).run(
        plan, _remediation_authorization(), scientific_run, backends, datasets
    )
    verified = verify_measured_outputs(plan, evaluations)
    assert verified.execution_plan_id == plan.content_id
    tampered_context = replace(
        evaluations[0].context,
        evaluator_implementation_id=_id("tampered-implementation"),
    )
    tampered = (replace(evaluations[0], context=tampered_context), *evaluations[1:])
    with pytest.raises(QualityError, match="QUALITY_MEASURED_EVALUATION_IDENTITY_INVALID"):
        verify_measured_outputs(plan, tampered)
    writer = PrimaryObservationWriter(writer_identity, tmp_path / "store")
    receipt = writer.publish(plan, _remediation_authorization(), scientific_run, evaluations)
    repeated = writer.publish(plan, _remediation_authorization(), scientific_run, evaluations)
    assert repeated.receipt_id == receipt.receipt_id
    assert receipt.observation_path.is_file()
    assert receipt.receipt_path.is_file()
    with pytest.raises(ObservationWriterError, match="OBSERVATION_MANUAL_JSON_FORBIDDEN"):
        writer.publish_json({"metric": "manually-edited"})


def test_quality_rejects_incomplete_evaluator_set() -> None:
    scientific_identity = _component("PRIMARY_SCIENTIFIC_RUNNER", "scientific.py")
    evaluation_identity = _component("PRIMARY_EVALUATION_RUNNER", "evaluation.py")
    writer_identity = _component("PRIMARY_OBSERVATION_WRITER", "writer.py")
    plan = _smoke_plan(scientific_identity, evaluation_identity, writer_identity)
    profile = _profiles()[0]
    backend = _FixtureScoringBackend(model_id=_id("checkpoint"), tokenizer_id=plan.tokenizer_id)
    measured = WikiTextEvaluator(profile).evaluate(
        EvaluationContext(
            execution_plan_id=plan.content_id,
            checkpoint_id=_id("checkpoint"),
            model_id=_id("checkpoint"),
            tokenizer_id=plan.tokenizer_id,
            dataset_id=profile.dataset_id,
            environment_id=plan.environment_id,
            evaluator_profile_id=profile.content_id,
            evaluator_implementation_id=_id("wrong-implementation"),
        ),
        backend,
        (WikiTextRecord("wikitext-en", "alpha beta"),),
    )
    with pytest.raises(QualityError, match="QUALITY_MEASURED_EVALUATION_SET_INCOMPLETE"):
        verify_measured_outputs(plan, (measured,))
