"""Deterministic all-mandatory benchmark decision functions."""

from __future__ import annotations

from dataclasses import dataclass

from deltatorrent.benchmark.contracts import (
    AUTHORITY_SCOPE,
    FORMAL_SEMANTICS_ID,
    SCHEMA_VERSION,
    CanonicalContract,
    ContractError,
)


@dataclass(frozen=True, slots=True)
class GateOutcome:
    gate_id: str
    mandatory: bool
    status: str

    def __post_init__(self) -> None:
        if (
            type(self.gate_id) is not str
            or not self.gate_id
            or type(self.mandatory) is not bool
            or type(self.status) is not str
            or self.status not in {"PASS", "FAIL", "MISSING"}
        ):
            raise ContractError("GATE_OUTCOME_INVALID")

    def to_dict(self) -> dict[str, object]:
        return {"gate_id": self.gate_id, "mandatory": self.mandatory, "status": self.status}


def all_mandatory_decision(
    gates: tuple[GateOutcome, ...],
    *,
    result_eligible: bool,
) -> str:
    """Return GO only for an eligible, complete all-pass gate table."""

    if type(result_eligible) is not bool:
        raise ContractError("RESULT_ELIGIBILITY_INVALID")
    if not gates or tuple(gate.gate_id for gate in gates) != tuple(
        sorted(gate.gate_id for gate in gates)
    ):
        raise ContractError("GATE_TABLE_NOT_SORTED")
    if len({gate.gate_id for gate in gates}) != len(gates):
        raise ContractError("GATE_TABLE_DUPLICATE")
    if any(gate.mandatory and gate.status != "PASS" for gate in gates):
        return "NO_GO"
    return "GO" if result_eligible else "NOT_EVALUATED"


def build_foundation_result(
    *,
    definition_id: str,
    evidence_manifest_id: str,
    result_evaluator_set_id: str,
    run_ids: tuple[str, ...],
    gates: tuple[GateOutcome, ...],
    limitations: tuple[str, ...],
    commentary: str,
) -> CanonicalContract:
    """Build a non-promotable report; commentary never influences decision."""

    decision = all_mandatory_decision(gates, result_eligible=False)
    failed = tuple(sorted(gate.gate_id for gate in gates if gate.status == "FAIL"))
    missing = tuple(sorted(gate.gate_id for gate in gates if gate.status == "MISSING"))
    return CanonicalContract.from_dict(
        {
            "authority_scope": AUTHORITY_SCOPE,
            "benchmark_definition_id": definition_id,
            "commentary": commentary,
            "decision": decision,
            "evidence_class": "TEST_FIXTURE",
            "evidence_manifest_id": evidence_manifest_id,
            "failed_gates": list(failed),
            "formal_semantics_id": FORMAL_SEMANTICS_ID,
            "gate_eligible": False,
            "gate_table": [gate.to_dict() for gate in gates],
            "limitations": list(sorted(limitations)),
            "missing_evidence": list(missing),
            "primary_eligible": False,
            "result_evaluator_set_id": result_evaluator_set_id,
            "run_ids": list(sorted(run_ids)),
            "schema_version": SCHEMA_VERSION,
            "type_name": "BENCHMARK_RESULT",
        }
    )
