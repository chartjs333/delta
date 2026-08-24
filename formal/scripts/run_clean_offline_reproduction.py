#!/usr/bin/env python3
"""Reproduce mandatory machine gates in a clean network-none Linux container."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "formal" / "reports" / "clean-offline-reproduction.json"
sys.path.insert(0, str(ROOT / "formal" / "scripts"))

from formal_artifacts import write_canonical_json  # noqa: E402


COMMANDS = (
    ("phase0", [sys.executable, "formal/scripts/verify_phase0.py"], 60),
    (
        "contracts",
        [sys.executable, "-m", "unittest", "discover", "-s", "formal/tests", "-v"],
        120,
    ),
    (
        "toolchain",
        [sys.executable, "formal/toolchain/verify_locks.py", "--require-cache"],
        300,
    ),
    (
        "report-verifier",
        [
            sys.executable,
            "formal/scripts/verify_formal_report.py",
            "formal/reports/formal-verification-report.json",
        ],
        60,
    ),
    ("parse", [sys.executable, "formal/scripts/run_formal_gate.py", "parse"], 300),
    ("safety", [sys.executable, "formal/scripts/run_formal_gate.py", "safety"], 2400),
    ("liveness", [sys.executable, "formal/scripts/run_formal_gate.py", "liveness"], 900),
    ("proofs", [sys.executable, "formal/scripts/run_formal_gate.py", "proofs"], 1800),
    ("mutants", [sys.executable, "formal/scripts/run_formal_gate.py", "mutants"], 1200),
    (
        "refinement",
        [sys.executable, "formal/scripts/run_formal_gate.py", "refinement"],
        300,
    ),
    (
        "tlc-evidence",
        [sys.executable, "formal/scripts/collect_tlc_evidence.py"],
        120,
    ),
    (
        "cross-artifact",
        [sys.executable, "formal/scripts/analyze_formal_consistency.py"],
        120,
    ),
)


def digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    ).stdout.strip()


def main() -> int:
    errors: list[str] = []
    if os.name == "nt" or platform.system() != "Linux":
        errors.append("reproduction must execute in Linux")
    if not Path("/.dockerenv").is_file():
        errors.append("/.dockerenv is missing")
    interfaces = sorted(path.name for path in Path("/sys/class/net").glob("*"))
    if interfaces != ["lo"]:
        errors.append(f"network-none expected only lo, observed {interfaces}")
    source_status = git("status", "--porcelain=v1", "--untracked-files=all")
    if source_status:
        errors.append("source tree was not clean before reproduction")

    environment = dict(os.environ)
    environment.update(
        {
            "PYTHONHASHSEED": "0",
            "TZ": "UTC",
            "HTTP_PROXY": "http://127.0.0.1:9",
            "HTTPS_PROXY": "http://127.0.0.1:9",
            "ALL_PROXY": "http://127.0.0.1:9",
            "NO_PROXY": "",
        }
    )
    checks: list[dict[str, Any]] = []
    if not errors:
        for name, command, timeout in COMMANDS:
            result = subprocess.run(
                command,
                cwd=ROOT,
                env=environment,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
            combined = f"{result.stdout}\n{result.stderr}"
            checks.append(
                {
                    "id": name,
                    "command": command,
                    "exit_code": result.returncode,
                    "output_sha256": digest(combined),
                    "status": "PASS" if result.returncode == 0 else "FAIL",
                }
            )
            if result.returncode != 0:
                errors.append(f"{name} exited {result.returncode}")
                break

    report = {
        "schema_version": "1.0.0",
        "status": "PASS" if not errors else "FAIL",
        "environment": "linux/amd64 clean container with --network none",
        "source_commit": git("rev-parse", "HEAD"),
        "source_clean_at_start": source_status == "",
        "platform": platform.platform(),
        "machine": platform.machine(),
        "network_interfaces": interfaces,
        "network_proxies_forced_to_loopback": True,
        "checks": checks,
        "errors": errors,
    }
    write_canonical_json(REPORT, report)
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
