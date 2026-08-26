"""Formal compatibility loader without TLA+, Lean, transport or native imports."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

FORMAL_SEMANTICS_ID = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
ARTIFACT_ACTION_IDS = frozenset(
    {
        "ACT-ARTIFACT-CORRUPT",
        "ACT-ARTIFACT-LOSE",
        "ACT-ARTIFACT-REPAIR",
        "ACT-PUBLISH",
    }
)
FORMAL_OUTCOMES = frozenset(
    {"ACCEPTED", "BLOCKED", "FAULT", "FINALIZED", "NO_OP", "REJECTED", "STUTTER"}
)


@dataclass(frozen=True, slots=True)
class FormalCompatibility:
    schema_version: str
    formal_semantics_id: str
    action_ids: frozenset[str]
    outcomes: frozenset[str]
    error_codes: frozenset[str]

    @classmethod
    def from_mapping(cls, value: dict[str, Any]) -> FormalCompatibility:
        expected_keys = {
            "actions",
            "error_codes",
            "formal_semantics_id",
            "outcomes",
            "schema_version",
        }
        if set(value) != expected_keys:
            raise ValueError("FORMAL_REGISTRY_SHAPE_INVALID")
        if value["schema_version"] != "1.0.0":
            raise ValueError("FORMAL_REGISTRY_VERSION_UNSUPPORTED")
        if value["formal_semantics_id"] != FORMAL_SEMANTICS_ID:
            raise ValueError("FORMAL_SEMANTICS_MISMATCH")
        action_ids = _string_set(value["actions"], "FORMAL_ACTION_IDS_INVALID")
        outcomes = _string_set(value["outcomes"], "FORMAL_OUTCOMES_INVALID")
        error_codes = _string_set(value["error_codes"], "FORMAL_ERROR_CODES_INVALID")
        if action_ids != ARTIFACT_ACTION_IDS:
            raise ValueError("FORMAL_ACTION_IDS_MISMATCH")
        if outcomes != FORMAL_OUTCOMES:
            raise ValueError("FORMAL_OUTCOMES_MISMATCH")
        return cls(
            schema_version="1.0.0",
            formal_semantics_id=FORMAL_SEMANTICS_ID,
            action_ids=action_ids,
            outcomes=outcomes,
            error_codes=error_codes,
        )


def _string_set(value: object, error_code: str) -> frozenset[str]:
    if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
        raise ValueError(error_code)
    result = frozenset(value)
    if len(result) != len(value):
        raise ValueError(error_code)
    return result


def load_formal_compatibility(path: Path) -> FormalCompatibility:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("FORMAL_REGISTRY_INVALID") from exc
    if not isinstance(value, dict):
        raise ValueError("FORMAL_REGISTRY_SHAPE_INVALID")
    return FormalCompatibility.from_mapping(value)
