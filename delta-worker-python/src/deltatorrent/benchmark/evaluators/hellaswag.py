"""Preregistered HellaSwag length-normalized multiple-choice evaluator."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import Decimal, localcontext

from deltatorrent.benchmark.evaluators.common import (
    EvaluationContext,
    EvaluatorProfile,
    MeasuredEvaluation,
    MetricValue,
    ScoringBackend,
    decimal_sum,
    evidence_root,
    fail,
    scaled_decimal,
    validate_context,
)

_METHOD = {
    "accuracy_aggregation": "EXACT_MATCH_MEAN_PPM",
    "case_normalization": "NONE",
    "choice_formatting": "SINGLE_ASCII_SPACE_PLUS_STRIPPED_ENDING",
    "choice_score": "MEAN_TARGET_TOKEN_LOG_PROB",
    "context_construction": "CTX_A_RSTRIP_SPACE_CTX_B_LSTRIP",
    "dataset_fields": ["ctx_a", "ctx_b", "endings", "label"],
    "length_normalization": "DIVIDE_BY_CHOICE_TOKEN_COUNT",
    "tie_rule": "LOWEST_CHOICE_INDEX",
    "token_boundary_policy": "JOINED_TEXT_OFFSET_OVERLAP_TOKEN_BELONGS_TO_CHOICE",
    "tokenizer_add_special_tokens": False,
}


@dataclass(frozen=True, slots=True)
class HellaSwagRecord:
    ctx_a: str
    ctx_b: str
    endings: tuple[str, ...]
    label: int


class HellaSwagEvaluator:
    def __init__(self, profile: EvaluatorProfile) -> None:
        if profile.evaluator_id != "hellaswag" or profile.method != _METHOD:
            raise fail("HELLASWAG_METHOD_PROFILE_INVALID")
        self.profile = profile

    def evaluate(
        self,
        context: EvaluationContext,
        backend: ScoringBackend,
        records: tuple[HellaSwagRecord, ...],
    ) -> MeasuredEvaluation:
        validate_context(self.profile, context, backend)
        if not records:
            raise fail("HELLASWAG_DATASET_EMPTY")
        correct = 0
        scored_tokens = 0
        item_evidence: list[dict[str, object]] = []
        for record in records:
            if len(record.endings) < 2 or not 0 <= record.label < len(record.endings):
                raise fail("HELLASWAG_RECORD_INVALID")
            context_text = record.ctx_a.rstrip() + " " + record.ctx_b.lstrip()
            prompt_ids = backend.encode(context_text, add_bos=False, add_eos=False)
            if not prompt_ids:
                raise fail("HELLASWAG_CONTEXT_TOKENIZATION_EMPTY")
            scores: list[Decimal] = []
            score_nanos: list[int] = []
            choice_token_counts: list[int] = []
            for ending in record.endings:
                choice_text = " " + ending.strip()
                scored_prompt_ids, choice_ids = backend.encode_continuation(
                    context_text, choice_text
                )
                if not choice_ids:
                    raise fail("HELLASWAG_CHOICE_TOKENIZATION_EMPTY")
                if scored_prompt_ids != prompt_ids:
                    raise fail("HELLASWAG_CONTEXT_TOKENIZATION_DRIFT")
                combined = scored_prompt_ids + choice_ids
                log_probs = backend.token_log_probabilities(combined)
                if len(log_probs) != len(combined) - 1:
                    raise fail("HELLASWAG_BACKEND_SCORE_COUNT_INVALID")
                target_log_probs = log_probs[len(prompt_ids) - 1 :]
                if len(target_log_probs) != len(choice_ids) or any(
                    not item.is_finite() or item > 0 for item in target_log_probs
                ):
                    raise fail("HELLASWAG_LOG_PROB_INVALID")
                with localcontext() as decimal_context:
                    decimal_context.prec = 50
                    score = decimal_sum(target_log_probs) / Decimal(len(choice_ids))
                scores.append(score)
                score_nanos.append(scaled_decimal(-score, 1_000_000_000))
                choice_token_counts.append(len(choice_ids))
                scored_tokens += len(choice_ids)
            best = max(range(len(scores)), key=lambda index: (scores[index], -index))
            correct += int(best == record.label)
            item_evidence.append(
                {
                    "choice_mean_nll_nano": score_nanos,
                    "choice_token_counts": choice_token_counts,
                    "context_sha256": "sha256:"
                    + hashlib.sha256(context_text.encode("utf-8")).hexdigest(),
                    "gold_label": record.label,
                    "predicted_label": best,
                }
            )
        return MeasuredEvaluation(
            evaluator_id="hellaswag",
            context=context,
            item_count=len(records),
            scored_token_count=scored_tokens,
            metrics=(
                MetricValue(
                    "post_training_hellaswag_accuracy_ppm",
                    correct * 1_000_000 // len(records),
                    "ppm",
                ),
            ),
            item_evidence_root=evidence_root(item_evidence),
            method_observation=dict(self.profile.method),
        )
