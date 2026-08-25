#!/usr/bin/env python3
"""Confirm that removing declared fairness invalidates the positive claim."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOLCHAIN = ROOT / "formal" / "toolchain"
TLA = ROOT / "formal" / "tla"
sys.path.insert(0, str(TOOLCHAIN))
sys.path.insert(0, str(ROOT / "formal" / "scripts"))

from formal_artifacts import sha256_file, write_canonical_json  # noqa: E402
from prepare_cache import artifacts, verify  # noqa: E402


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
        raise RuntimeError("Java executable is missing")

    source_config = TLA / "cfg" / "liveness-eventual-synchrony.cfg"
    config_text = source_config.read_text(encoding="utf-8")
    config_text = config_text.replace(
        "SPECIFICATION LivenessSpec", "SPECIFICATION NoFairnessSpec", 1
    )
    property_marker = "\nPROPERTIES\n"
    if property_marker not in config_text:
        raise RuntimeError("positive liveness config has no PROPERTIES section")
    prefix = config_text.split(property_marker, 1)[0]
    countercheck_text = (
        prefix
        + "\nPROPERTY AppliedReached\n"
        + "CHECK_DEADLOCK FALSE\n"
    )
    config = TLA / "cfg" / ".generated-liveness-no-fairness.cfg"
    config.write_text(countercheck_text, encoding="utf-8")
    config_sha256 = sha256_file(config)
    command = [
        java,
        "-XX:+UseParallelGC",
        "-Dfile.encoding=UTF-8",
        "-Duser.language=en",
        "-Duser.country=US",
        "-Duser.timezone=UTC",
        "-cp",
        str(jar),
        "tlc2.TLC",
        "-workers",
        "1",
        "-fp",
        "17",
        "-seed",
        "2026082412",
        "-config",
        str(config),
        str(TLA / "DeltaReduceLivenessHarness.tla"),
    ]
    result = subprocess.run(
        command,
        cwd=TLA,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    output = f"{result.stdout}\n{result.stderr}"
    expected = "Temporal properties were violated"
    if result.returncode == 0 or expected not in output:
        raise RuntimeError(
            "no-fairness countercheck did not produce the intended temporal violation"
        )
    evidence = {
        "schema_version": "1.0.0",
        "status": "PASS",
        "countercheck_id": "COUNTERCHECK-NO-FAIRNESS",
        "removed_assumptions": ["weak fairness for protocol progress actions"],
        "expected_property_id": "LIVE-APPLIED-REACHED",
        "outcome": "EXPECTED_TEMPORAL_COUNTEREXAMPLE",
        "module": {
            "path": "formal/tla/DeltaReduceLivenessHarness.tla",
            "sha256": sha256_file(TLA / "DeltaReduceLivenessHarness.tla"),
        },
        "source_config": {
            "path": "formal/tla/cfg/liveness-eventual-synchrony.cfg",
            "sha256": sha256_file(source_config),
        },
        "generated_config_sha256": config_sha256,
        "tool_sha256": sha256_file(jar),
    }
    path = ROOT / "formal" / "reports" / "liveness-countercheck.json"
    write_canonical_json(path, evidence)
    config.unlink(missing_ok=True)
    print(json.dumps(evidence, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, RuntimeError, subprocess.SubprocessError) as error:
        print(
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "status": "FAIL",
                    "error": f"{type(error).__name__}:{error}",
                },
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        sys.exit(1)
