#!/usr/bin/env python3
"""Normalize TLC logs into content-addressable model and coverage evidence."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TLA = ROOT / "formal" / "tla"
REPORTS = ROOT / "formal" / "reports"
sys.path.insert(0, str(ROOT / "formal" / "scripts"))

from formal_artifacts import load_json_strict, sha256_file, write_canonical_json  # noqa: E402
from tlc_results import (  # noqa: E402
    TlcResultError,
    result_sha256,
    successful_tlc_result,
    top_level_action_counts,
)


def config_properties(config: Path, registry: dict[str, Any]) -> list[str]:
    names = {
        item["name"]: item["id"]
        for item in registry["invariants"] + registry["temporal_properties"]
    }
    result: list[str] = []
    section: str | None = None
    for raw in config.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line in {"INVARIANTS", "PROPERTIES"}:
            section = line
            continue
        if line.startswith("PROPERTY "):
            section = "PROPERTIES"
            name = line.split(maxsplit=1)[1]
        elif not line or line.startswith(r"\*"):
            continue
        elif section is not None and (
            line.startswith("CHECK_")
            or line.startswith("CONSTRAINT")
            or line.startswith("SYMMETRY")
            or line in {"CONSTANTS"}
        ):
            section = None
            continue
        elif section is not None:
            name = line
        else:
            continue
        identifier = names.get(name)
        if identifier is None and name.endswith("TypeOK"):
            identifier = "INV-TYPE-OK"
        if identifier is not None and identifier not in result:
            result.append(identifier)
    return result


def observed_terminal_outcomes(properties: list[str], action_counts: dict[str, int]) -> list[str]:
    """Project terminal classes from validated non-zero TLC action coverage."""

    terminals: list[str] = []
    if action_counts.get("HardAbortAction", 0) > 0:
        terminals.append("ABORTED")
    if (
        action_counts.get("AdvanceCurrentCheckpointAction", 0) > 0
        or action_counts.get("HeteroAdvance", 0) > 0
    ):
        terminals.append("APPLIED")
    if (
        "LIVE-APPLIED-REACHED" in properties
        and action_counts.get("PositiveAdvanceCurrent", 0) > 0
        and "APPLIED" not in terminals
    ):
        terminals.append("APPLIED")
    if (
        "LIVE-ABORT-QC-REACHED" in properties
        and action_counts.get("PositiveFinalizeHardAbort", 0) > 0
        and "ABORTED" not in terminals
    ):
        terminals.append("ABORTED")
    return terminals


def main() -> int:
    manifest_path = TLA / "cfg" / "config-manifest.json"
    manifest = load_json_strict(manifest_path)
    registry = load_json_strict(REPORTS / "formal-id-registry.json")
    tla_lock = load_json_strict(ROOT / "formal" / "toolchain" / "tla.lock")
    expected_version = tla_lock["tla_tools"]["reported_tlc_version"]
    expected_revision = tla_lock["tla_tools"]["release_commit"]
    tool_sha256 = tla_lock["tla_tools"]["sha256"]
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    markdown = [
        "# Executed TLC coverage evidence",
        "",
        "All metrics below come from the checked-in deterministic config manifest and "
        "a validated TLC semantic-result projection. Raw PID, timing, host telemetry "
        "and coverage counters are diagnostic only and are not content-addressed. No "
        "TLC symmetry set or state constraint is used. Bounds reduce constants only; "
        "every required action is checked for non-zero reachability.",
        "",
        "| Config | Kind | States | Distinct | Diameter | "
        "Terminal outcome classes | Required actions |",
        "| --- | --- | ---: | ---: | ---: | --- | ---: |",
    ]

    for entry in manifest["configs"]:
        identifier = entry["id"]
        log = ROOT / "formal" / "build" / "tlc" / identifier / "tlc.log"
        if not log.is_file():
            errors.append(f"{identifier}: missing TLC log")
            continue
        output = log.read_text(encoding="utf-8", errors="replace")
        try:
            parsed = successful_tlc_result(
                output,
                expected_version=expected_version,
                expected_revision=expected_revision,
                fingerprint_index=entry["fingerprint_index"],
                seed=entry["seed"],
                workers=entry["workers"],
                required_actions=entry.get("required_action_coverage", []),
            )
            action_counts = top_level_action_counts(output)
        except TlcResultError as error:
            errors.append(f"{identifier}: invalid TLC evidence: {error}")
            continue
        required_reached = parsed["required_action_reached"]
        states = parsed["states"]
        distinct = parsed["distinct_states"]
        diameter = parsed["diameter"]
        properties = config_properties(TLA / entry["config"], registry)
        if not properties:
            errors.append(f"{identifier}: no registered property in config")
        terminals = observed_terminal_outcomes(properties, action_counts)
        module_path = TLA / entry["module"]
        config_path = TLA / entry["config"]
        record = {
            "id": identifier,
            "kind": entry["kind"],
            "module": f"formal/tla/{entry['module']}",
            "module_sha256": sha256_file(module_path),
            "config": f"formal/tla/{entry['config']}",
            "config_sha256": sha256_file(config_path),
            "tool_sha256": tool_sha256,
            "seed": entry["seed"],
            "fingerprint_index": entry["fingerprint_index"],
            "workers": entry["workers"],
            "states": states,
            "distinct_states": distinct,
            "diameter": diameter,
            "terminal_outcomes_observed": terminals,
            "terminal_outcome_class_count": len(terminals),
            "properties": properties,
            "required_action_reached": required_reached,
            "status": "PASS",
        }
        record["tlc_result_sha256"] = result_sha256(record)
        records.append(record)
        markdown.append(
            f"| {identifier} | {entry['kind']} | {states} | {distinct} | "
            f"{diameter} | {', '.join(terminals) if terminals else 'none'} | "
            f"{len(required_reached)} |"
        )

    evidence = {
        "schema_version": "2.0.0",
        "status": "PASS" if not errors else "FAIL",
        "manifest": {
            "path": "formal/tla/cfg/config-manifest.json",
            "sha256": sha256_file(manifest_path),
        },
        "symmetry_reduction": {
            "used": False,
            "justification": "No SYMMETRY declaration is present in a mandatory config.",
        },
        "state_constraints": {
            "used": False,
            "justification": "No CONSTRAINT declaration is present in a mandatory config.",
        },
        "bounds_rationale": (
            "Finite constants bound validator, ticket, domain, shard, time, "
            "rejection and retry populations; separate f=1 and parametric Lean "
            "proofs prevent those bounds from being generalized as theorem evidence."
        ),
        "liveness_assumptions": [
            "eventual synchrony after a finite disruption",
            "weak fairness for each phase-specific composed progress relation",
            "an honest responsive quorum remains available",
            "required certified artifact bytes remain available or repairable",
            "bounded deterministic local computation",
        ],
        "liveness_countercheck": "formal/reports/liveness-countercheck.json",
        "terminal_metric": (
            "terminal_outcome_class_count counts APPLIED/ABORTED outcome classes "
            "reached by a non-zero terminal-setting transition, with the matching "
            "registered eventual milestone required for liveness wrappers; it is "
            "not a count of concrete TLC states."
        ),
        "models": records,
        "errors": errors,
    }
    write_canonical_json(REPORTS / "tlc-evidence.json", evidence)
    (REPORTS / "executed-coverage.md").write_text("\n".join(markdown) + "\n", encoding="utf-8")
    print(json.dumps(evidence, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
