"""Transactional optimizer-boundary token and cursor accounting."""

from __future__ import annotations

from dataclasses import dataclass

from deltatorrent.domain.errors import DeltaError, ErrorCode


def _invalid(message: str, **details: object) -> DeltaError:
    return DeltaError(ErrorCode.INVALID_TOKEN_ACCOUNTING, message, details)


def _non_negative(value: object, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise _invalid("ACCOUNTING_NON_NEGATIVE_INTEGER_REQUIRED", field=field)
    return value


@dataclass(frozen=True, slots=True)
class TokenAccountingRecord:
    effective_steps: int
    observed_micro_steps: int
    committed_micro_steps: int
    processed_tokens: int
    cursor_start: int
    cursor_end: int
    pending_micro_steps: int

    def __post_init__(self) -> None:
        for field in self.__dataclass_fields__:
            _non_negative(getattr(self, field), field)
        if self.cursor_end < self.cursor_start:
            raise _invalid("ACCOUNTING_CURSOR_INVALID")
        if self.committed_micro_steps > self.observed_micro_steps:
            raise _invalid("ACCOUNTING_MICRO_STEP_RELATION_INVALID")


@dataclass(slots=True)
class OptimizerBoundaryLedger:
    range_start: int
    range_end: int
    effective_steps: int = 0
    observed_micro_steps: int = 0
    committed_micro_steps: int = 0
    processed_tokens: int = 0
    cursor_end: int | None = None
    _pending_tokens: int = 0
    _pending_cursor_end: int | None = None
    _pending_micro_steps: int = 0

    def __post_init__(self) -> None:
        _non_negative(self.range_start, "range_start")
        _non_negative(self.range_end, "range_end")
        if self.range_end <= self.range_start:
            raise _invalid("ACCOUNTING_RANGE_INVALID")
        if self.cursor_end is None:
            self.cursor_end = self.range_start
        if not self.range_start <= self.cursor_end <= self.range_end:
            raise _invalid("ACCOUNTING_CURSOR_INVALID")
        for field in (
            "effective_steps",
            "observed_micro_steps",
            "committed_micro_steps",
            "processed_tokens",
            "_pending_tokens",
            "_pending_micro_steps",
        ):
            _non_negative(getattr(self, field), field)

    @property
    def pending_micro_steps(self) -> int:
        return self._pending_micro_steps

    def stage_microbatch(
        self, *, cursor_start: int, cursor_end: int, non_padding_tokens: int
    ) -> None:
        _non_negative(cursor_start, "cursor_start")
        _non_negative(cursor_end, "cursor_end")
        _non_negative(non_padding_tokens, "non_padding_tokens")
        expected_start = (
            self._pending_cursor_end if self._pending_cursor_end is not None else self.cursor_end
        )
        if (
            cursor_start != expected_start
            or cursor_end <= cursor_start
            or cursor_end > self.range_end
        ):
            raise _invalid(
                "ACCOUNTING_STAGE_RANGE_INVALID",
                actual_start=cursor_start,
                expected_start=expected_start,
            )
        self.observed_micro_steps += 1
        self._pending_micro_steps += 1
        self._pending_tokens += non_padding_tokens
        self._pending_cursor_end = cursor_end

    def commit_optimizer_step(self, *, expected_micro_steps: int) -> TokenAccountingRecord:
        if (
            isinstance(expected_micro_steps, bool)
            or not isinstance(expected_micro_steps, int)
            or expected_micro_steps <= 0
            or self._pending_micro_steps != expected_micro_steps
            or self._pending_cursor_end is None
        ):
            raise _invalid(
                "ACCOUNTING_BOUNDARY_INCOMPLETE",
                actual_micro_steps=self._pending_micro_steps,
                expected_micro_steps=expected_micro_steps,
            )
        self.effective_steps += 1
        self.committed_micro_steps += self._pending_micro_steps
        self.processed_tokens += self._pending_tokens
        self.cursor_end = self._pending_cursor_end
        self._pending_tokens = 0
        self._pending_cursor_end = None
        self._pending_micro_steps = 0
        return self.snapshot()

    def discard_partial_accumulation(self) -> TokenAccountingRecord:
        self._pending_tokens = 0
        self._pending_cursor_end = None
        self._pending_micro_steps = 0
        return self.snapshot()

    def snapshot(self) -> TokenAccountingRecord:
        assert self.cursor_end is not None
        return TokenAccountingRecord(
            effective_steps=self.effective_steps,
            observed_micro_steps=self.observed_micro_steps,
            committed_micro_steps=self.committed_micro_steps,
            processed_tokens=self.processed_tokens,
            cursor_start=self.range_start,
            cursor_end=self.cursor_end,
            pending_micro_steps=self._pending_micro_steps,
        )
