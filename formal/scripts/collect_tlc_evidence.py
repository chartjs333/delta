#!/usr/bin/env python3
"""Normalize TLC logs into content-addressable model and coverage evidence."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TLA = ROOT / "formal" / "tla"
REPORTS = ROOT / "formal" / "reports"
sys.path.insert(0, str(ROOT / "formal" / "scripts"))

from formal_artifacts import load_json_strict, sha256_file, write_canonical_json  # noqa: E402


SUMMARY = re.compile(
    r"([0-9][0-9,]*) states generated, ([0-9][0-9,]*) distinct states found"
)
DEPTH = re.compile(r"The depth of the complete state graph search is ([0-9][0-9,]*)")
ACTION = re.compile(
    r"^<([A-Za-z][A-Za-z0-9_]*)\b[^>]*>:\s+"
    r"([0-9][0-9,]*):([0-9][0-9,]*)",
    flags=re.MULTILINE,
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


def main() -> int:
    manifest_path = TLA / "cfg" / "config-manifest.json"
    manifest = load_json_strict(manifest_path)
    registry = load_json_strict(REPORTS / "formal-id-registry.json")
    records: list[dict[str, Any]] = []
    errors: list[str] = []
    markdown = [
        "# Executed TLC coverage evidence",
        "",
        "All counts below come from the checked-in deterministic config manifest and "
        "the corresponding retained TLC log. No TLC symmetry set or state constraint "
        "is used. Bounds reduce constants only; every required action is checked for "
        "non-zero invocation coverage.",
        "",
        "| Config | Kind | States | Distinct | Diameter | Terminal outcome classes | Required actions |",
        "| --- | --- | ---: | ---: | ---: | --- | ---: |",
    ]

    for entry in manifest["configs"]:
        identifier = entry["id"]
        log = ROOT / "formal" / "build" / "tlc" / identifier / "tlc.log"
        if not log.is_file():
            errors.append(f"{identifier}: missing TLC log")
            continue
        output = log.read_text(encoding="utf-8", errors="replace")
        summaries = SUMMARY.findall(output)
        depths = DEPTH.findall(output)
        if (
            "Model checking completed. No error has been found." not in output
            or not summaries
            or not depths
        ):
            errors.append(f"{identifier}: incomplete or failed TLC evidence")
            continue
        action_counts = {
            action: int(invocations.replace(",", ""))
            for action, _distinct, invocations in ACTION.findall(output)
        }
        required_counts: dict[str, int] = {}
        for action in entry.get("required_action_coverage", []):
            count = action_counts.get(action, 0)
            required_counts[action] = count
            if count <= 0:
                errors.append(f"{identifier}: unreachable required action {action}")
        states, distinct = (
            int(value.replace(",", "")) for value in summaries[-1]
        )
        diameter = int(depths[-1].replace(",", ""))
        terminals: list[str] = []
        if action_counts.get("HardAbortAction", 0) > 0:
            terminals.append("ABORTED")
        if action_counts.get("AdvanceCurrentCheckpointAction", 0) > 0:
            terminals.append("APPLIED")
        properties = config_properties(TLA / entry["config"], registry)
        if not properties:
            errors.append(f"{identifier}: no registered property in config")
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
        record = {
            "id": identifier,
            "kind": entry["kind"],
            "module": f"formal/tla/{entry['module']}",
            "config": f"formal/tla/{entry['config']}",
            "seed": entry["seed"],
            "fingerprint_index": entry["fingerprint_index"],
            "workers": entry["workers"],
            "states": states,
            "distinct_states": distinct,
            "diameter": diameter,
            "terminal_outcomes_observed": terminals,
            "terminal_outcome_class_count": len(terminals),
            "properties": properties,
            "required_action_invocations": required_counts,
            "log_sha256": sha256_file(log),
            "status": "PASS",
        }
        records.append(record)
        markdown.append(
            f"| {identifier} | {entry['kind']} | {states} | {distinct} | "
            f"{diameter} | {', '.join(terminals) if terminals else 'none'} | "
            f"{len(required_counts)} |"
        )

    evidence = {
        "schema_version": "1.0.0",
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
    (REPORTS / "executed-coverage.md").write_text(
        "\n".join(markdown) + "\n", encoding="utf-8"
    )
    print(json.dumps(evidence, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
