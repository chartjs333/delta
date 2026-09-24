#!/usr/bin/env python3
"""Compare exact finite transition graphs before/after arithmetic evaluation changes.

This checks Init/Next and invariants only. It does not replace mandatory liveness
or prove equivalence outside these two finite configurations.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

from formal_artifacts import semantic_text_sha256, write_canonical_json
from run_formal_gate import ROOT, run_capture, tla_runtime
from tlc_results import successful_tlc_result

IDS = {"CFG-LIVENESS-EVENTUAL-SYNCHRONY", "CFG-NATIVE-ARITHMETIC-LIVENESS"}


def git_bytes(*args: str) -> bytes:
    return subprocess.check_output(["git", *args], cwd=ROOT, timeout=30)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-source", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    write_canonical_json(args.output, {"status": "NOT_COMPLETED", "formal_go": False})
    base = git_bytes("rev-parse", "--verify", args.base_source + "^{commit}").decode().strip()
    if not re.fullmatch(r"[0-9a-f]{40}", base):
        raise ValueError("base source must resolve to one commit")
    paths = sorted((ROOT / "formal/tla").glob("*.tla"))
    snapshots: dict[str, dict[str, bytes]] = {
        "before": {
            p.name: git_bytes("show", base + ":" + p.relative_to(ROOT).as_posix()) for p in paths
        },
        "after": {p.name: p.read_bytes() for p in paths},
    }
    snapshot_ids = {
        arm: digest(json.dumps({n: digest(b) for n, b in files.items()}, sort_keys=True).encode())
        for arm, files in snapshots.items()
    }
    work = ROOT / "formal/build" / ("evaluation-" + base[:12] + "-" + snapshot_ids["after"][:12])
    java, options, jar = tla_runtime()
    lock = json.loads((ROOT / "formal/toolchain/tla.lock").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "formal/tla/cfg/config-manifest.json").read_text())
    entries = [entry for entry in manifest["configs"] if entry["id"] in IDS]
    if {entry["id"] for entry in entries} != IDS:
        raise ValueError("missing required finite comparison config")
    comparisons = []
    for entry in entries:
        source_config = ROOT / "formal/tla" / entry["config"]
        config_text = source_config.read_text(encoding="utf-8")
        old_config = git_bytes("show", base + ":" + source_config.relative_to(ROOT).as_posix())
        if old_config.decode().replace("\r\n", "\n") != config_text:
            raise ValueError("comparison requires identical before/after config: " + entry["id"])
        if (
            config_text.count("SPECIFICATION LivenessSpec") != 1
            or "\nPROPERTIES\n" not in config_text
        ):
            raise ValueError("unexpected liveness specification shape")
        diagnostic = config_text.replace(
            "SPECIFICATION LivenessSpec", "INIT Init\nNEXT AppliedLivenessNext"
        )
        diagnostic = diagnostic.split("\nPROPERTIES\n", 1)[0] + "\nCHECK_DEADLOCK FALSE\n"
        graphs = {}
        results = {}
        for arm, files in snapshots.items():
            directory = work / entry["id"] / arm
            directory.mkdir(parents=True, exist_ok=True)
            for name, contents in files.items():
                (directory / name).write_bytes(contents)
            config = directory / "diagnostic.cfg"
            config.write_text(diagnostic, encoding="utf-8", newline="\n")
            graph = directory / "states.dot"
            output = run_capture(
                [
                    java,
                    *options,
                    "-cp",
                    str(jar),
                    "tlc2.TLC",
                    "-workers",
                    str(entry["workers"]),
                    "-fp",
                    str(entry["fingerprint_index"]),
                    "-seed",
                    str(entry["seed"]),
                    "-metadir",
                    str(directory / "states"),
                    "-dump",
                    "dot",
                    str(graph),
                    "-config",
                    str(config),
                    str(directory / entry["module"]),
                ],
                cwd=directory,
                timeout=120,
                echo=False,
                output_path=directory / "tlc.log",
            )
            results[arm] = successful_tlc_result(
                output,
                expected_version=lock["tla_tools"]["reported_tlc_version"],
                expected_revision=lock["tla_tools"]["release_commit"],
                fingerprint_index=entry["fingerprint_index"],
                seed=entry["seed"],
                workers=entry["workers"],
                required_actions=[],
            )
            graphs[arm] = graph.read_bytes()
        equal = graphs["before"] == graphs["after"]
        if not equal or results["before"] != results["after"]:
            raise ValueError("finite graph changed: " + entry["id"])
        comparisons.append(
            {
                "id": entry["id"],
                "exact_graph_bytes_equal": equal,
                "graph_sha256": digest(graphs["after"]),
                "graph_bytes": len(graphs["after"]),
                "config_sha256": digest(diagnostic.encode()),
                "result": results["after"],
            }
        )
    report = {
        "schema_version": "1.0.0",
        "status": "PASS",
        "formal_go": False,
        "scope": "FINITE_FULL_STATE_AND_TRANSITION_GRAPH_EQUALITY_ONLY",
        "temporal_qualification_claimed": False,
        "mandatory_liveness_still_required": True,
        "base_source": base,
        "snapshot_ids": snapshot_ids,
        "comparisons": comparisons,
        "changed_modules": [
            name
            for name in snapshots["before"]
            if snapshots["before"][name] != snapshots["after"][name]
        ],
        "current_modules": [
            {"path": p.relative_to(ROOT).as_posix(), "sha256": semantic_text_sha256(p)}
            for p in paths
        ],
        "tool_sha256": digest(jar.read_bytes()),
    }
    write_canonical_json(args.output, report)
    print(
        json.dumps(
            {
                "status": "PASS",
                "comparisons": len(comparisons),
                "changed_modules": report["changed_modules"],
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
