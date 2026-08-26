#!/usr/bin/env python3
"""Collect offline, content-addressable evidence for every pinned formal tool."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TOOLCHAIN = ROOT / "formal" / "toolchain"
PROOFS = ROOT / "formal" / "proofs"
sys.path.insert(0, str(TOOLCHAIN))
sys.path.insert(0, str(ROOT / "formal" / "scripts"))

from formal_artifacts import load_json_strict, sha256_file, write_canonical_json  # noqa: E402
from prepare_cache import artifacts, verify  # noqa: E402


def capture(command: list[str], cwd: Path = ROOT) -> tuple[int, str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    return result.returncode, f"{result.stdout}\n{result.stderr}".strip()


def record(identifier: str, status: str, details: dict[str, Any]) -> dict[str, Any]:
    return {"id": identifier, "status": status, **details}


def main() -> int:
    errors: list[str] = []
    selected = artifacts()
    artifact_results: dict[str, dict[str, Any]] = {}
    for artifact in selected:
        path = TOOLCHAIN / "cache" / artifact["artifact"]
        valid, reason = verify(path, artifact)
        artifact_results[artifact["component"] + ":" + artifact["project"]] = {
            "artifact": artifact["artifact"],
            "bytes": artifact["bytes"],
            "sha256": artifact["sha256"],
            "status": "PASS" if valid else "FAIL",
            "reason": reason,
        }
        if not valid:
            errors.append(f"{artifact['artifact']}:{reason}")

    tla_lock = load_json_strict(TOOLCHAIN / "tla.lock")
    lean_lock = load_json_strict(TOOLCHAIN / "lean.lock")
    container_lock = load_json_strict(TOOLCHAIN / "container.lock")
    native_java = (
        TOOLCHAIN
        / "windows"
        / "tla-runtime-17.0.20.1"
        / "java"
        / "bin"
        / "java.exe"
    )
    java = os.environ.get(
        "JAVA", str(native_java) if os.name == "nt" and native_java.is_file() else "java"
    )
    java_code, java_version = capture([java, "-version"])
    expected_java = str(tla_lock["jvm"]["version"]).split("+")[0]
    jre_pass = java_code == 0 and expected_java in java_version

    native_lean = (
        TOOLCHAIN
        / "windows"
        / "lean-4.32.1-windows"
        / "bin"
        / "lean.exe"
    )
    lean = str(native_lean) if os.name == "nt" and native_lean.is_file() else "lean"
    lean_code, lean_version = capture([lean, "--version"])
    proof_report_path = ROOT / "formal" / "reports" / "lean-proof-report.json"
    proof_report = load_json_strict(proof_report_path) if proof_report_path.is_file() else {}
    lean_pass = (
        lean_code == 0
        and "4.32.1" in lean_version
        and proof_report.get("status") == "PASS"
    )

    verify_code, verify_output = capture(
        [sys.executable, str(TOOLCHAIN / "verify_locks.py"), "--require-cache"]
    )
    dockerfile = (TOOLCHAIN / "Dockerfile").read_text(encoding="utf-8")
    base_reference = (
        f"{container_lock['base_image']}@{container_lock['base_manifest_digest']}"
    )
    container_pass = (
        verify_code == 0
        and f"FROM {base_reference}" in dockerfile
        and "apt-get" not in dockerfile
        and "curl " not in dockerfile
    )

    tla_artifact = next(item for item in selected if item["project"] == "tlaplus/tlaplus")
    jre_artifact = next(item for item in selected if item["project"].startswith("adoptium/"))
    lean_artifact = next(item for item in selected if item["project"] == "leanprover/lean4")
    checks = [
        record(
            "TOOLCHAIN-TLA",
            "PASS" if verify(TOOLCHAIN / "cache" / tla_artifact["artifact"], tla_artifact)[0] else "FAIL",
            {"artifact": tla_artifact["artifact"], "sha256": tla_artifact["sha256"]},
        ),
        record(
            "TOOLCHAIN-JRE",
            "PASS" if jre_pass and verify(TOOLCHAIN / "cache" / jre_artifact["artifact"], jre_artifact)[0] else "FAIL",
            {"artifact": jre_artifact["artifact"], "sha256": jre_artifact["sha256"], "version_output": java_version},
        ),
        record(
            "TOOLCHAIN-LEAN",
            "PASS" if lean_pass and verify(TOOLCHAIN / "cache" / lean_artifact["artifact"], lean_artifact)[0] else "FAIL",
            {"artifact": lean_artifact["artifact"], "sha256": lean_artifact["sha256"], "version_output": lean_version},
        ),
        record(
            "TOOLCHAIN-CONTAINER",
            "PASS" if container_pass else "FAIL",
            {
                "base_reference": base_reference,
                "definition_verified": container_pass,
                "clean_offline_reproduction_is_separate": True,
            },
        ),
    ]
    failed = [item["id"] for item in checks if item["status"] != "PASS"]
    errors.extend(failed)
    evidence = {
        "schema_version": "1.0.0",
        "status": "PASS" if not errors else "FAIL",
        "platform": "windows-amd64" if os.name == "nt" else "linux-amd64",
        "checks": checks,
        "selected_artifacts": artifact_results,
        "lock_verifier": {
            "status": "PASS" if verify_code == 0 else "FAIL",
            "output": verify_output,
        },
        "locks": {
            "tla": sha256_file(TOOLCHAIN / "tla.lock"),
            "lean": sha256_file(TOOLCHAIN / "lean.lock"),
            "container": sha256_file(TOOLCHAIN / "container.lock"),
            "dependencies": sha256_file(PROOFS / "dependencies.lock.json"),
        },
        "errors": errors,
    }
    write_canonical_json(
        ROOT / "formal" / "reports" / "toolchain-evidence.json", evidence
    )
    print(json.dumps(evidence, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
