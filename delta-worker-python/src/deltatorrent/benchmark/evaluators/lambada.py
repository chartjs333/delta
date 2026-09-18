"""Preregistered LAMBADA exact-match and target log-likelihood evaluator."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from decimal import Decimal

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

_FINAL_TOKEN = re.compile(r"^(.*\s)(\S+)$", re.DOTALL)
_METHOD = {
    "case_normalization": "NONE",
    "dataset_field": "text",
    "exact_match_rule": "GREEDY_TOKEN_ID_SEQUENCE_EQUALS_TARGET",
    "log_likelihood_aggregation": "SUM_TARGET_TOKEN_LOG_PROB",
    "multi_token_target": "SCORE_AND_GENERATE_ALL_TARGET_TOKENS",
    "prompt_construction": "PREFIX_THROUGH_FINAL_WHITESPACE",
    "target_extraction": "FINAL_NON_WHITESPACE_SPAN",
    "text_normalization": "UNICODE_NFC",
    "token_boundary_policy": "JOINED_TEXT_OFFSET_OVERLAP_TOKEN_BELONGS_TO_TARGET",
    "tokenizer_add_special_tokens": False,
    "whitespace_normalization": "NONE",
}


@dataclass(frozen=True, slots=True)
class LambadaRecord:
    text: str


class LambadaEvaluator:
    def __init__(self, profile: EvaluatorProfile) -> None:
        if profile.evaluator_id != "lambada" or profile.method != _METHOD:
            raise fail("LAMBADA_METHOD_PROFILE_INVALID")
        self.profile = profile

    def evaluate(
        self,
        context: EvaluationContext,
        backend: ScoringBackend,
        records: tuple[LambadaRecord, ...],
    ) -> MeasuredEvaluation:
        validate_context(self.profile, context, backend)
        if not records:
            raise fail("LAMBADA_DATASET_EMPTY")
        correct = 0
        target_token_count = 0
        negative_log_likelihoods: list[Decimal] = []
        item_evidence: list[dict[str, object]] = []
        for record in records:
            normalized = unicodedata.normalize("NFC", record.text)
            match = _FINAL_TOKEN.fullmatch(normalized)
            if match is None:
                raise fail("LAMBADA_TARGET_EXTRACTION_INVALID")
            prompt, target = match.groups()
            prompt_ids, target_ids = backend.encode_continuation(prompt, target)
            if not prompt_ids or not target_ids:
                raise fail("LAMBADA_TOKENIZATION_EMPTY")
            combined = prompt_ids + target_ids
            log_probs = backend.token_log_probabilities(combined)
            if len(log_probs) != len(combined) - 1:
                raise fail("LAMBADA_BACKEND_SCORE_COUNT_INVALID")
            target_log_probs = log_probs[len(prompt_ids) - 1 :]
            if len(target_log_probs) != len(target_ids) or any(
                not item.is_finite() or item > 0 for item in target_log_probs
            ):
                raise fail("LAMBADA_LOG_PROB_INVALID")
            nll = -decimal_sum(target_log_probs)
            predicted = backend.greedy_tokens(prompt_ids, len(target_ids))
            exact = predicted == target_ids
            correct += int(exact)
            target_token_count += len(target_ids)
            negative_log_likelihoods.append(nll)
            item_evidence.append(
                {
                    "exact_match": exact,
                    "nll_nano": scaled_decimal(nll, 1_000_000_000),
                    "prompt_sha256": "sha256:" + hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                    "target_sha256": "sha256:" + hashlib.sha256(target.encode("utf-8")).hexdigest(),
                    "target_token_count": len(target_ids),
                }
            )
        mean_nll = decimal_sum(tuple(negative_log_likelihoods)) / Decimal(len(records))
        return MeasuredEvaluation(
            evaluator_id="lambada",
            context=context,
            item_count=len(records),
            scored_token_count=target_token_count,
            metrics=(
                MetricValue(
                    "downstream_lambada_accuracy_ppm",
                    correct * 1_000_000 // len(records),
                    "ppm",
                ),
                MetricValue(
                    "downstream_lambada_mean_nll_nano",
                    scaled_decimal(mean_nll, 1_000_000_000),
                    "nano-nat",
                ),
            ),
            item_evidence_root=evidence_root(item_evidence),
            method_observation=dict(self.profile.method),
        )
