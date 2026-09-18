"""Deterministic all-mandatory GO/NO_GO decision with no override path."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from deltatorrent.benchmark.definition import FORMAL_SEMANTICS_ID
from deltatorrent.protocol.canonical import canonical_json_bytes


class DecisionError(ValueError):
    """Stable gate-table or result decision error."""


@dataclass(frozen=True, slots=True)
class GateResult:
    gate_id: str
    mandatory: bool
    status: str
    reason: str

    def __post_init__(self) -> None:
        if not self.gate_id or self.status not in {"PASS", "FAIL"} or not self.reason:
            raise DecisionError("GATE_RESULT_INVALID")

    def to_dict(self) -> dict[str, object]:
        return {
            "gate_id": self.gate_id,
            "mandatory": self.mandatory,
            "reason": self.reason,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    document: dict[str, object]

    @property
    def decision(self) -> str:
        value = self.document["decision"]
        if not isinstance(value, str):
            raise DecisionError("RESULT_DECISION_INVALID")
        return value

    @property
    def content_id(self) -> str:
        domain = b"deltareduce.010.benchmark-result.v1\0"
        return "sha256:" + hashlib.sha256(domain + canonical_json_bytes(self.document)).hexdigest()


def decide(
    *,
    definition_id: str,
    evidence_manifest_id: str,
    run_ids: tuple[str, ...],
    gates: tuple[GateResult, ...],
    limitations: tuple[str, ...],
    measured_values: tuple[dict[str, object], ...] = (),
) -> BenchmarkResult:
    if not gates or len({item.gate_id for item in gates}) != len(gates):
        raise DecisionError("GATE_TABLE_INVALID")
    failed = tuple(
        sorted(item.gate_id for item in gates if item.mandatory and item.status != "PASS")
    )
    decision = "NO_GO" if failed else "GO"
    document: dict[str, object] = {
        "benchmark_definition_id": definition_id,
        "decision": decision,
        "evidence_manifest_id": evidence_manifest_id,
        "failed_or_missing": list(failed),
        "formal_semantics_id": FORMAL_SEMANTICS_ID,
        "gate_table": [item.to_dict() for item in sorted(gates, key=lambda item: item.gate_id)],
        "limitations": list(limitations),
        "measured_values": list(measured_values),
        "run_ids": list(run_ids),
        "schema_version": "1.0.0",
        "type_name": "BENCHMARK_RESULT",
    }
    return BenchmarkResult(document)
