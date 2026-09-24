#!/usr/bin/env python3
"""Check candidate IO-stage guards; these are not production-action mutants."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from formal_artifacts import sha256_file, write_canonical_json
from run_formal_gate import ROOT, TLA_ROOT, tla_runtime
from run_mutants import Replacement, invariant_only_config, replace_exact
from tlc_results import mutant_tlc_result

HARNESS = "DeltaReducePersistenceHarness.tla"
CASES = (
    (
        "EXPOSE_BEFORE_COMMIT",
        "PersistenceRecordSound",
        (
            Replacement(
                '    /\\ ioStage = "COMMITTED" /\\ NotCut("COMMITTED")\n'
                "    /\\ ioCommitted /\\ CanVote(LateValidator)\n",
                '    /\\ ioStage = "DURABLE" /\\ NotCut("DURABLE")\n'
                "    /\\ CanVote(LateValidator)\n",
            ),
        ),
    ),
    (
        "CORRUPT_RECOVERY_READY",
        "PersistenceRecoverySound",
        (
            Replacement(
                '    /\\ HoldProtocol /\\ ioStage\' = "BLOCKED"\n',
                "    /\\ RecoverJournal(LateValidator) /\\ UNCHANGED bindingStep\n"
                '    /\\ ioStage\' = "BLOCKED"\n',
            ),
        ),
    ),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    write_canonical_json(args.output, {"status": "NOT_COMPLETED", "formal_go": False})
    java, options, jar = tla_runtime()
    lock = json.loads((ROOT / "formal/toolchain/tla.lock").read_text(encoding="utf-8"))
    source = TLA_ROOT / HARNESS
    config = TLA_ROOT / "cfg/persistence-parameter.cfg"
    results = []
    for index, (name, invariant, replacements) in enumerate(CASES):
        with tempfile.TemporaryDirectory(prefix="delta-io-guard-") as raw:
            work = Path(raw)
            for module in TLA_ROOT.glob("*.tla"):
                shutil.copyfile(module, work / module.name)
            text = source.read_text(encoding="utf-8")
            for replacement in replacements:
                text = replace_exact(text, replacement, name)
            (work / HARNESS).write_text(text, encoding="utf-8", newline="\n")
            (work / "check.cfg").write_text(
                invariant_only_config(config.read_text(encoding="utf-8"), invariant),
                encoding="utf-8",
                newline="\n",
            )
            fingerprint = 50 + index
            seed = 2026092420 + index
            result = subprocess.run(
                [
                    java,
                    *options,
                    "-Xss16m",
                    "-cp",
                    str(jar),
                    "tlc2.TLC",
                    "-workers",
                    "1",
                    "-fp",
                    str(fingerprint),
                    "-seed",
                    str(seed),
                    "-config",
                    "check.cfg",
                    HARNESS,
                ],
                cwd=work,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=120,
            )
            output = result.stdout + "\n" + result.stderr
            log = ROOT / "formal/build/persistence-validation" / (name.lower() + ".log")
            log.parent.mkdir(parents=True, exist_ok=True)
            log.write_text(output, encoding="utf-8", newline="\n")
            checked = mutant_tlc_result(
                output,
                return_code=result.returncode,
                expected_invariant=invariant,
                expected_version=lock["tla_tools"]["reported_tlc_version"],
                expected_revision=lock["tla_tools"]["release_commit"],
                fingerprint_index=fingerprint,
                seed=seed,
                workers=1,
            )
            results.append(
                {
                    "id": name,
                    "expected_invariant": invariant,
                    "mutated_harness_sha256": sha256_file(work / HARNESS),
                    "mutated_config_sha256": sha256_file(work / "check.cfg"),
                    "tlc_result": checked,
                }
            )
            print(name + ": EXPECTED_COUNTEREXAMPLE", flush=True)
    write_canonical_json(
        args.output,
        {
            "schema_version": "1.0.0",
            "status": "PASS",
            "formal_go": False,
            "mutation_scope": "CANDIDATE_PERSISTENCE_HARNESS",
            "harness_sha256": sha256_file(source),
            "config_sha256": sha256_file(config),
            "tool_sha256": sha256_file(jar),
            "counterchecks": results,
        },
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
