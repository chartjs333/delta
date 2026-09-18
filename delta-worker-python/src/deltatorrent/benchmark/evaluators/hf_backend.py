"""Exact Hugging Face causal-LM adapter used by Campaign 02 evaluators."""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from deltatorrent.benchmark.evaluators.common import EvaluatorContractError


class HuggingFaceCausalLMBackend:
    """Thin measured backend; imports GPU dependencies only when instantiated."""

    def __init__(
        self,
        model: Any,
        tokenizer: Any,
        *,
        model_id: str,
        tokenizer_id: str,
        device: str = "cuda",
    ) -> None:
        import torch

        self._torch = torch
        self._model = model
        self._tokenizer = tokenizer
        self._model_id = model_id
        self._tokenizer_id = tokenizer_id
        self._device = device
        self._model.eval()

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def tokenizer_id(self) -> str:
        return self._tokenizer_id

    def encode(self, text: str, *, add_bos: bool, add_eos: bool) -> tuple[int, ...]:
        values = list(self._tokenizer.encode(text, add_special_tokens=False))
        if add_bos:
            bos = self._tokenizer.bos_token_id
            if bos is None:
                raise EvaluatorContractError("EVALUATOR_BOS_TOKEN_UNAVAILABLE")
            values.insert(0, int(bos))
        if add_eos:
            eos = self._tokenizer.eos_token_id
            if eos is None:
                raise EvaluatorContractError("EVALUATOR_EOS_TOKEN_UNAVAILABLE")
            values.append(int(eos))
        return tuple(int(item) for item in values)

    def token_log_probabilities(self, input_ids: tuple[int, ...]) -> tuple[Decimal, ...]:
        if len(input_ids) < 2:
            return ()
        torch = self._torch
        tensor = torch.tensor((input_ids,), dtype=torch.long, device=self._device)
        with torch.inference_mode():
            logits = self._model(input_ids=tensor, use_cache=False).logits[0, :-1, :]
            targets = tensor[0, 1:]
            log_probs = torch.log_softmax(logits, dim=-1, dtype=torch.float64)
            selected = log_probs.gather(1, targets[:, None]).squeeze(1).cpu().tolist()
        return tuple(Decimal(format(float(value), ".17g")) for value in selected)

    def encode_continuation(
        self, prefix: str, continuation: str
    ) -> tuple[tuple[int, ...], tuple[int, ...]]:
        if not prefix or not continuation:
            raise EvaluatorContractError("EVALUATOR_CONTINUATION_INPUT_INVALID")
        try:
            encoded = self._tokenizer(
                prefix + continuation,
                add_special_tokens=False,
                return_offsets_mapping=True,
            )
            values = tuple(int(item) for item in encoded["input_ids"])
            offsets = tuple((int(start), int(end)) for start, end in encoded["offset_mapping"])
        except (KeyError, NotImplementedError, TypeError, ValueError) as exc:
            raise EvaluatorContractError("EVALUATOR_OFFSETS_UNAVAILABLE") from exc
        if len(values) != len(offsets) or not values:
            raise EvaluatorContractError("EVALUATOR_OFFSETS_INVALID")
        boundary = len(prefix)
        target_start = next(
            (index for index, (_, end) in enumerate(offsets) if end > boundary),
            len(values),
        )
        prefix_ids = values[:target_start]
        continuation_ids = values[target_start:]
        if not prefix_ids or not continuation_ids:
            raise EvaluatorContractError("EVALUATOR_CONTINUATION_TOKENIZATION_EMPTY")
        if any(end > boundary for _, end in offsets[:target_start]) or any(
            end <= boundary for _, end in offsets[target_start:]
        ):
            raise EvaluatorContractError("EVALUATOR_CONTINUATION_BOUNDARY_INVALID")
        return prefix_ids, continuation_ids

    def greedy_tokens(self, prefix_ids: tuple[int, ...], count: int) -> tuple[int, ...]:
        if not prefix_ids or count < 1:
            raise EvaluatorContractError("EVALUATOR_GREEDY_INPUT_INVALID")
        torch = self._torch
        values = list(prefix_ids)
        generated: list[int] = []
        with torch.inference_mode():
            for _ in range(count):
                tensor = torch.tensor((values,), dtype=torch.long, device=self._device)
                logits = self._model(input_ids=tensor, use_cache=False).logits[0, -1, :]
                token = int(torch.argmax(logits).item())
                values.append(token)
                generated.append(token)
        return tuple(generated)
