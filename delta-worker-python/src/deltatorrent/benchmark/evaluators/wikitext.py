"""Preregistered token-weighted WikiText loss and perplexity evaluator."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, localcontext

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
    "bos_policy": "DO_NOT_ADD",
    "context_length": 2048,
    "document_boundary": "RESET",
    "domain_aggregation": "TOKEN_WEIGHTED",
    "eos_policy": "DO_NOT_ADD",
    "ignored_token_policy": "FIRST_TOKEN_PER_DOCUMENT_AND_OVERLAP_CONTEXT",
    "loss_denominator": "SCORED_TARGET_TOKENS",
    "numeric_precision": "DECIMAL50_ROUND_HALF_EVEN",
    "overlap_masking": "SCORE_EACH_NONINITIAL_TOKEN_ONCE",
    "perplexity_conversion": "EXP_MEAN_NLL_THEN_SCALE_1E6",
    "stride": 512,
    "text_field": "text",
    "tokenizer_add_special_tokens": False,
}


@dataclass(frozen=True, slots=True)
class WikiTextRecord:
    domain_id: str
    text: str


class WikiTextEvaluator:
    def __init__(self, profile: EvaluatorProfile) -> None:
        if profile.evaluator_id != "wikitext" or profile.method != _METHOD:
            raise fail("WIKITEXT_METHOD_PROFILE_INVALID")
        self.profile = profile

    def evaluate(
        self,
        context: EvaluationContext,
        backend: ScoringBackend,
        records: tuple[WikiTextRecord, ...],
    ) -> MeasuredEvaluation:
        validate_context(self.profile, context, backend)
        if not records:
            raise fail("WIKITEXT_DATASET_EMPTY")
        context_length = int(self.profile.method["context_length"])
        stride = int(self.profile.method["stride"])
        if stride < 1 or stride > context_length:
            raise fail("WIKITEXT_WINDOW_INVALID")
        item_evidence: list[dict[str, object]] = []
        domain_values: dict[str, list[tuple[Decimal, int]]] = {}
        for record in records:
            if not record.domain_id or not isinstance(record.text, str):
                raise fail("WIKITEXT_RECORD_INVALID")
            tokens = backend.encode(record.text, add_bos=False, add_eos=False)
            nll_values: list[Decimal] = []
            target_start = 1
            while target_start < len(tokens):
                target_end = min(target_start + stride, len(tokens))
                input_start = max(0, target_end - context_length)
                window = tokens[input_start:target_end]
                log_probs = backend.token_log_probabilities(window)
                if len(log_probs) != max(0, len(window) - 1):
                    raise fail("WIKITEXT_BACKEND_SCORE_COUNT_INVALID")
                first_scored_global = max(target_start, input_start + 1)
                for global_index in range(first_scored_global, target_end):
                    value = log_probs[global_index - input_start - 1]
                    if not value.is_finite() or value > 0:
                        raise fail("WIKITEXT_LOG_PROB_INVALID")
                    nll_values.append(-value)
                target_start = target_end
            nll = decimal_sum(tuple(nll_values))
            scored = len(nll_values)
            if scored:
                domain_values.setdefault(record.domain_id, []).append((nll, scored))
            item_evidence.append(
                {
                    "domain_id": record.domain_id,
                    "nll_nano": scaled_decimal(nll, 1_000_000_000),
                    "scored_tokens": scored,
                    "text_sha256": "sha256:"
                    + hashlib.sha256(record.text.encode("utf-8")).hexdigest(),
                    "token_count": len(tokens),
                }
            )
        if not domain_values:
            raise fail("WIKITEXT_NO_SCORABLE_TOKENS")
        domain_summaries: list[dict[str, object]] = []
        total_nll = Decimal(0)
        total_tokens = 0
        for domain_id in sorted(domain_values):
            values = domain_values[domain_id]
            domain_nll = decimal_sum(tuple(item[0] for item in values))
            domain_tokens = sum(item[1] for item in values)
            loss = domain_nll / Decimal(domain_tokens)
            domain_summaries.append(
                {
                    "domain_id": domain_id,
                    "loss_micro": scaled_decimal(loss, 1_000_000),
                    "scored_tokens": domain_tokens,
                }
            )
            total_nll += domain_nll
            total_tokens += domain_tokens
        mean_loss = total_nll / Decimal(total_tokens)
        with localcontext() as decimal_context:
            decimal_context.prec = 50
            decimal_context.rounding = ROUND_HALF_EVEN
            perplexity = mean_loss.exp()
        metrics = (
            MetricValue("validation_loss_micro", scaled_decimal(mean_loss, 1_000_000), "micro-nat"),
            MetricValue(
                "validation_perplexity_micro",
                scaled_decimal(perplexity, 1_000_000),
                "micro-perplexity",
            ),
            MetricValue(
                "per_domain_wikitext_loss_micro",
                scaled_decimal(mean_loss, 1_000_000),
                "micro-nat",
            ),
        )
        return MeasuredEvaluation(
            evaluator_id="wikitext",
            context=context,
            item_count=len(records),
            scored_token_count=total_tokens,
            metrics=metrics,
            item_evidence_root=evidence_root(item_evidence),
            method_observation={
                **self.profile.method,
                "domain_results": domain_summaries,
            },
        )
