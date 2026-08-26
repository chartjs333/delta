"""Complete-only LocalDelta/A_j normalization."""

from __future__ import annotations

from collections.abc import Mapping

from torch import Tensor

from deltatorrent.delta.schema import included_tensor_names
from deltatorrent.delta.validation import validate_fp32_tensor_bundle
from deltatorrent.domain.errors import DeltaError, ErrorCode
from deltatorrent.domain.parameters import ParameterSchema


def require_complete_steps(*, effective_steps: object, step_budget: object) -> int:
    if (
        isinstance(effective_steps, bool)
        or not isinstance(effective_steps, int)
        or isinstance(step_budget, bool)
        or not isinstance(step_budget, int)
        or effective_steps <= 0
        or effective_steps != step_budget
    ):
        raise DeltaError(
            ErrorCode.INVALID_CONTRIBUTION_CANDIDATE,
            "CANDIDATE_REQUIRES_A_EQUALS_H",
            {"effective_steps": effective_steps, "step_budget": step_budget},
        )
    return effective_steps


def normalize_local_delta(
    local_delta: Mapping[str, Tensor],
    schema: ParameterSchema,
    *,
    effective_steps: object,
    step_budget: object,
    per_tensor_norm_ceiling: float | None = None,
    global_norm_ceiling: float | None = None,
) -> dict[str, Tensor]:
    denominator = require_complete_steps(
        effective_steps=effective_steps,
        step_budget=step_budget,
    )
    validate_fp32_tensor_bundle(local_delta, schema)
    normalized = {
        name: local_delta[name].div(denominator).contiguous()
        for name in included_tensor_names(schema)
    }
    validate_fp32_tensor_bundle(
        normalized,
        schema,
        per_tensor_norm_ceiling=per_tensor_norm_ceiling,
        global_norm_ceiling=global_norm_ceiling,
    )
    return normalized
