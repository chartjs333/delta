#!/usr/bin/env python3
"""Run every registered weakening mutant and archive its intended TLC witness."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MUTANT_ROOT = ROOT / "formal" / "mutants"
FIXTURES = ROOT / "formal" / "fixtures" / "counterexamples"
TOOLCHAIN = ROOT / "formal" / "toolchain"
sys.path.insert(0, str(ROOT / "formal" / "scripts"))
sys.path.insert(0, str(TOOLCHAIN))

from formal_artifacts import canonical_json_bytes, sha256_file, write_canonical_json  # noqa: E402
from prepare_cache import artifacts, verify  # noqa: E402


MUTANTS = (
    ("MUT-MISSING-DURABLE-VOTE", "PersistBeforeSend", "INV-VOTE-UNIQUENESS", "formal/tla/DeltaReduceQuorums.tla", "PersistBeforeSend"),
    ("MUT-DUPLICATE-COMMITMENT", "CommitUniqueness", "INV-COMMIT-UNIQUENESS", "formal/tla/DeltaReduceTickets.tla", "CommitUniqueness"),
    ("MUT-MUTABLE-ISC", "ISCImmutability", "INV-ISC-IMMUTABILITY", "formal/tla/DeltaReduceCertificates.tla", "ISCImmutability"),
    ("MUT-EARLY-SEED", "SeedAfterInputFreeze", "INV-SEED-AFTER-FREEZE", "formal/tla/DeltaReduceCertificates.tla", "SeedAfterInputFreeze"),
    ("MUT-MISSING-APC-PARENT", "APCParentage", "INV-APC-PARENTAGE", "formal/tla/DeltaReduceCertificates.tla", "APCParentage"),
    ("MUT-MISSING-SHARD-PARENT", "ShardViewAtomicity", "INV-SHARD-VIEW-ATOMICITY", "formal/tla/DeltaReduceReduceApply.tla", "ShardViewAtomicity"),
    ("MUT-INCOMPLETE-AGGREGATE", "AggregateCompleteness", "INV-AGGREGATE-COMPLETENESS", "formal/tla/DeltaReduceReduceApply.tla", "AggregateCompleteness"),
    ("MUT-UNCHECKED-OVERFLOW", "NoOverflow", "INV-NO-OVERFLOW", "formal/tla/DeltaReduceReduceApply.tla", "NoOverflow"),
    ("MUT-CURRENT-WITHOUT-APPLYQC", "CurrentCertified", "INV-CURRENT-CERTIFIED", "formal/tla/DeltaReduceReduceApply.tla", "CurrentCertified"),
    ("MUT-PARTIAL-PUBLICATION", "PlaneSeparation", "INV-PLANE-SEPARATION", "formal/tla/DeltaReduceReduceApply.tla", "PlaneSeparation"),
)


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def main() -> int:
    artifact = artifacts("tla")[0]
    jar = Path(os.environ.get("TLA2TOOLS_JAR", TOOLCHAIN / "cache" / artifact["artifact"]))
    valid, reason = verify(jar, artifact)
    if not valid:
        raise RuntimeError(f"unverified tla2tools: {reason}")
    native_java = TOOLCHAIN / "windows" / "tla-runtime-17.0.20.1" / "java" / "bin" / "java.exe"
    java = os.environ.get(
        "JAVA", str(native_java) if os.name == "nt" and native_java.is_file() else "java"
    )
    if shutil.which(java) is None and not Path(java).is_file():
        raise RuntimeError("java executable is missing")

    module = MUTANT_ROOT / "DeltaReduceMutants.tla"
    module_hash = sha256_file(module)
    tool_hash = sha256_file(jar)
    FIXTURES.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, str]] = []

    for index, (mutant_id, invariant, property_id, source_path, anchor) in enumerate(MUTANTS):
        source = ROOT / source_path
        if anchor not in source.read_text(encoding="utf-8"):
            raise RuntimeError(f"{mutant_id}: source anchor is missing: {anchor}")
        config = "\n".join((
            "SPECIFICATION Spec",
            "CONSTANTS",
            f'    MutantId = "{mutant_id}"',
            "    RequiredKeyCount = 2",
            "    AccumulatorBound = 1",
            f"INVARIANT {invariant}",
            "CHECK_DEADLOCK FALSE",
            "",
        )).encode("utf-8")
        cfg = MUTANT_ROOT / ".generated-mutant.cfg"
        cfg.write_bytes(config)
        command = [
            java, "-XX:+UseParallelGC", "-Dfile.encoding=UTF-8",
            "-Duser.language=en", "-Duser.country=US", "-Duser.timezone=UTC",
            "-cp", str(jar), "tlc2.TLC", "-workers", "1",
            "-fp", str((index * 7 + 3) % 64), "-seed", str(2026082500 + index),
            "-config", cfg.name, module.name,
        ]
        result = subprocess.run(
            command, cwd=MUTANT_ROOT, check=False, capture_output=True,
            text=True, encoding="utf-8", errors="replace", timeout=120,
        )
        output = f"{result.stdout}\n{result.stderr}"
        expected_marker = f"Invariant {invariant} is violated."
        if result.returncode == 0:
            raise RuntimeError(f"{mutant_id}: unexpectedly passed")
        if expected_marker not in output:
            match = re.search(r"Invariant ([A-Za-z0-9_]+) is violated", output)
            actual = match.group(1) if match else "NO_INVARIANT"
            raise RuntimeError(
                f"{mutant_id}: intended {invariant}, observed {actual}; "
                f"output={output[-1000:]!r}"
            )
        fixture = {
            "schema_version": "1.0.0",
            "mutant_id": mutant_id,
            "expected_property_id": property_id,
            "expected_invariant": invariant,
            "outcome": "EXPECTED_COUNTEREXAMPLE",
            "source_anchor": {"path": source_path, "operator": anchor, "sha256": sha256_file(source)},
            "model": {"path": "formal/mutants/DeltaReduceMutants.tla", "sha256": module_hash},
            "config_sha256": hashlib.sha256(config).hexdigest(),
            "tool_sha256": tool_hash,
            "normalized_trace": ["Init", "MutantStep", f"VIOLATION:{invariant}"],
        }
        fixture_path = FIXTURES / f"{mutant_id.lower()}.json"
        write_bytes(fixture_path, canonical_json_bytes(fixture))
        summaries.append({"id": mutant_id, "property": property_id, "status": "PASS"})
        print(f"{mutant_id}: expected {invariant} counterexample observed")

    cfg.unlink(missing_ok=True)
    report = {"schema_version": "1.0.0", "status": "PASS", "mutants": summaries}
    write_canonical_json(ROOT / "formal" / "reports" / "mutant-evidence.json", report)
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
