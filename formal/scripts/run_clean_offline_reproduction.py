#!/usr/bin/env python3
"""Reproduce mandatory machine gates in a clean network-none Linux container."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "formal" / "reports" / "clean-offline-reproduction.json"
sys.path.insert(0, str(ROOT / "formal" / "scripts"))

from formal_artifacts import (  # noqa: E402
    derive_formal_semantics_id,
    discover_semantic_artifacts,
    load_json_strict,
    sha256_file,
    write_canonical_json,
)


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


RUNTIME_PREFIXES = (
    ".apalache/",
    ".git/",
    "formal/build/",
    "formal/proofs/.lake/",
    "formal/proofs/build/",
    "formal/proofs/lake-packages/",
    "formal/reports/local/",
    "formal/toolchain/cache/",
    "formal/toolchain/windows/",
)


def is_runtime_path(relative: str) -> bool:
    return "__pycache__/" in relative or relative.startswith(RUNTIME_PREFIXES)


def observed_source_files(root: Path) -> set[str]:
    observed: set[str] = set()
    for directory, directory_names, file_names in os.walk(root):
        relative_directory = Path(directory).relative_to(root).as_posix()
        prefix = "" if relative_directory == "." else f"{relative_directory}/"
        directory_names[:] = [
            name
            for name in directory_names
            if name != "__pycache__" and not is_runtime_path(f"{prefix}{name}/")
        ]
        for name in file_names:
            relative = f"{prefix}{name}"
            if not is_runtime_path(relative):
                observed.add(relative)
    return observed


def verify_source_manifest(path: Path, root: Path = ROOT) -> dict[str, Any]:
    manifest = load_json_strict(path)
    if set(manifest) != {
        "schema_version",
        "source_commit",
        "source_tree",
        "source_clean",
        "files",
    }:
        raise ValueError("source manifest shape mismatch")
    if manifest["schema_version"] != "1.0.0" or manifest["source_clean"] is not True:
        raise ValueError("source manifest is not a clean v1 snapshot")
    for field in ("source_commit", "source_tree"):
        if not isinstance(manifest[field], str) or not re.fullmatch(
            r"[0-9a-f]{40}", manifest[field]
        ):
            raise ValueError(f"invalid {field}")

    files = manifest["files"]
    if not isinstance(files, list):
        raise ValueError("source manifest files must be an array")
    declared: set[str] = set()
    previous = ""
    root_resolved = root.resolve()
    for item in files:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            raise ValueError("invalid source manifest entry")
        relative = item["path"]
        if (
            not isinstance(relative, str)
            or not relative
            or relative <= previous
            or relative.startswith(("/", "\\"))
        ):
            raise ValueError("source manifest paths must be sorted relative paths")
        previous = relative
        candidate = (root / relative).resolve()
        if root_resolved not in candidate.parents or not candidate.is_file():
            raise ValueError(f"unsafe or missing source path: {relative}")
        if sha256_file(candidate) != item["sha256"]:
            raise ValueError(f"source hash mismatch: {relative}")
        declared.add(relative.replace("\\", "/"))

    observed = observed_source_files(root)
    extras = sorted(observed - declared)
    missing = sorted(declared - observed)
    if extras or missing:
        raise ValueError(f"source file set mismatch: extras={extras}, missing={missing}")
    return manifest


def main() -> int:
    errors: list[str] = []
    if os.name == "nt" or platform.system() != "Linux":
        errors.append("reproduction must execute in Linux")
    if not Path("/.dockerenv").is_file():
        errors.append("/.dockerenv is missing")
    interfaces = sorted(path.name for path in Path("/sys/class/net").glob("*"))
    if interfaces != ["lo"]:
        errors.append(f"network-none expected only lo, observed {interfaces}")
    manifest_path = Path(os.environ.get("FORMAL_SOURCE_MANIFEST", ""))
    source_manifest: dict[str, Any] | None = None
    if not manifest_path.is_file():
        errors.append("FORMAL_SOURCE_MANIFEST must name a mounted manifest file")
    else:
        try:
            source_manifest = verify_source_manifest(manifest_path)
        except (OSError, ValueError) as error:
            errors.append(f"source manifest verification failed: {error}")

    semantic_artifacts = discover_semantic_artifacts(ROOT)
    formal_semantics_id = derive_formal_semantics_id("1.0.0", semantic_artifacts)

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
        "source_commit": source_manifest["source_commit"] if source_manifest else "0" * 40,
        "source_tree": source_manifest["source_tree"] if source_manifest else "0" * 40,
        "source_clean_at_start": source_manifest is not None,
        "source_manifest_sha256": sha256_file(manifest_path)
        if manifest_path.is_file()
        else "0" * 64,
        "formal_semantics_id": formal_semantics_id,
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
