"""Machine and human reports derived from one immutable BenchmarkResult."""

from __future__ import annotations

import json

from deltatorrent.benchmark.decision import BenchmarkResult
from deltatorrent.protocol.canonical import canonical_json_bytes


def machine_report(result: BenchmarkResult) -> bytes:
    return canonical_json_bytes(result.document)


def human_report(result: BenchmarkResult) -> str:
    gates = result.document.get("gate_table")
    if not isinstance(gates, list):
        raise ValueError("RESULT_GATE_TABLE_INVALID")
    lines = [
        "# Feature 010 benchmark result",
        "",
        f"Decision: `{result.decision}`",
        "",
        "| Gate | Mandatory | Status | Reason |",
        "| --- | --- | --- | --- |",
    ]
    for gate in gates:
        if not isinstance(gate, dict):
            raise ValueError("RESULT_GATE_TABLE_INVALID")
        lines.append(
            f"| {gate['gate_id']} | {str(gate['mandatory']).lower()} | "
            f"{gate['status']} | {gate['reason']} |"
        )
    limitations = result.document.get("limitations")
    if not isinstance(limitations, list):
        raise ValueError("RESULT_LIMITATIONS_INVALID")
    lines.extend(["", "## Limitations", ""])
    lines.extend(f"- {item}" for item in limitations)
    return "\n".join(lines) + "\n"


def parse_machine_report(value: bytes) -> dict[str, object]:
    document = json.loads(value)
    if not isinstance(document, dict) or canonical_json_bytes(document) != value:
        raise ValueError("MACHINE_REPORT_NOT_CANONICAL")
    return document
