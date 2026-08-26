#!/usr/bin/env python3
"""Fail-closed entrypoint for the formal Makefile targets."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TOOLCHAIN = ROOT / "formal" / "toolchain"
TLA_ROOT = ROOT / "formal" / "tla"
PROOFS = ROOT / "formal" / "proofs"
sys.path.insert(0, str(TOOLCHAIN))

from prepare_cache import artifacts, verify  # noqa: E402


GATES = ("parse", "safety", "liveness", "proofs", "mutants", "refinement", "report")


def fail(message: str) -> None:
    raise RuntimeError(message)


def run(
    command: list[str],
    *,
    cwd: Path,
    timeout: int,
    environment: dict[str, str] | None = None,
) -> None:
    rendered = " ".join(command)
    print(f"formal-gate: {rendered}", flush=True)
    subprocess.run(
        command,
        cwd=cwd,
        check=True,
        timeout=timeout,
        env=environment,
    )


def run_capture(
    command: list[str], *, cwd: Path, timeout: int, echo: bool = True
) -> str:
    rendered = " ".join(command)
    print(f"formal-gate: {rendered}", flush=True)
    result = subprocess.run(
        command,
        cwd=cwd,
        check=False,
        timeout=timeout,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if echo and result.stdout:
        print(result.stdout, end="")
    if echo and result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, command)
    return f"{result.stdout}\n{result.stderr}"


def verify_action_coverage(output: str, required_actions: list[str]) -> None:
    for action in required_actions:
        pattern = re.compile(
            rf"^<{re.escape(action)}\b[^>]*>:\s+"
            rf"([0-9][0-9,]*):([0-9][0-9,]*)",
            flags=re.MULTILINE,
        )
        match = pattern.search(output)
        if match is None:
            fail(f"TLC action coverage missing for {action}")
        invocation_count = int(match.group(2).replace(",", ""))
        if invocation_count <= 0:
            fail(f"TLC action coverage is zero for {action}")


def verify_sany_output(output: str) -> None:
    failure_markers = (
        "Semantic errors:",
        "Parse Error",
        "*** Errors:",
        "Unknown operator:",
    )
    detected = [marker for marker in failure_markers if marker in output]
    if detected:
        fail(f"SANY reported errors despite a zero exit code: {detected}")
    if "Semantic processing of module" not in output:
        fail("SANY output contains no semantic-processing evidence")


def tla_runtime() -> tuple[str, list[str], Path]:
    lock = json.loads((TOOLCHAIN / "tla.lock").read_text(encoding="utf-8"))
    artifact = artifacts("tla")[0]
    jar = Path(os.environ.get("TLA2TOOLS_JAR", TOOLCHAIN / "cache" / artifact["artifact"]))
    valid, reason = verify(jar, artifact)
    if not valid:
        fail(f"TLA2TOOLS_JAR is not the locked artifact: {reason}")
    native_java = (
        TOOLCHAIN
        / "windows"
        / "tla-runtime-17.0.20.1"
        / "java"
        / "bin"
        / "java.exe"
    )
    java = os.environ.get(
        "JAVA",
        str(native_java) if os.name == "nt" and native_java.is_file() else "java",
    )
    if shutil.which(java) is None and not Path(java).is_file():
        fail(f"Java executable not found: {java}")
    version = run_capture([java, "-version"], cwd=ROOT, timeout=30, echo=False)
    if str(lock["jvm"]["version"]).split("+")[0] not in version:
        fail(f"Java runtime differs from tla.lock: {version.splitlines()[0]}")
    return java, list(lock["runtime"]["java_options"]), jar


def parse_modules() -> None:
    if not TLA_ROOT.is_dir():
        fail("formal/tla does not exist; T013 has not started")
    modules = sorted(TLA_ROOT.rglob("*.tla"))
    if not modules:
        fail("no TLA+ modules found; parser success cannot be vacuous")
    java, options, jar = tla_runtime()
    for module in modules:
        output = run_capture(
            [java, *options, "-cp", str(jar), "tla2sany.SANY", str(module)],
            cwd=TLA_ROOT,
            timeout=120,
        )
        verify_sany_output(output)


def run_tlc(kind: str) -> None:
    manifest_path = TLA_ROOT / "cfg" / "config-manifest.json"
    if not manifest_path.is_file():
        fail("missing formal/tla/cfg/config-manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema_version") != "1.0.0":
        fail("unsupported TLA config manifest schema")
    all_configs = manifest.get("configs", [])
    if not isinstance(all_configs, list):
        fail("TLA config manifest configs must be an array")
    identifiers = [entry.get("id") for entry in all_configs if isinstance(entry, dict)]
    if len(identifiers) != len(all_configs) or len(identifiers) != len(set(identifiers)):
        fail("TLA config manifest has malformed or duplicate IDs")
    registry = json.loads(
        (ROOT / "formal" / "reports" / "formal-id-registry.json").read_text(
            encoding="utf-8"
        )
    )
    registered_configs = {entry["id"] for entry in registry["configs"]}
    unknown = set(identifiers) - registered_configs
    if unknown:
        fail(f"unregistered TLA configs: {sorted(unknown)}")
    configs = [entry for entry in manifest.get("configs", []) if entry.get("kind") == kind]
    if not configs:
        fail(f"no {kind} configs registered; gate success cannot be vacuous")
    java, options, jar = tla_runtime()
    for entry in configs:
        if not isinstance(entry.get("fingerprint_index"), int) or not (
            0 <= entry["fingerprint_index"] <= 63
        ):
            fail(f"invalid fingerprint index for {entry.get('id')}")
        if not isinstance(entry.get("seed"), int):
            fail(f"missing deterministic seed for {entry.get('id')}")
        required_coverage = entry.get("required_action_coverage", [])
        if not isinstance(required_coverage, list) or len(required_coverage) != len(
            set(required_coverage)
        ):
            fail(f"invalid action coverage list for {entry.get('id')}")
        config = TLA_ROOT / entry["config"]
        module = TLA_ROOT / entry["module"]
        if not config.is_file() or not module.is_file():
            fail(f"missing config/module for {entry.get('id')}")
        timeout = int(entry.get("timeout_seconds", 600))
        metadata = ROOT / "formal" / "build" / "tlc" / entry["id"]
        metadata.mkdir(parents=True, exist_ok=True)
        command = [
                java,
                *options,
                "-cp",
                str(jar),
                "tlc2.TLC",
                "-workers",
                str(entry.get("workers", 1)),
                "-fp",
                str(entry["fingerprint_index"]),
                "-seed",
                str(entry["seed"]),
                "-metadir",
                str(metadata),
            ]
        if required_coverage:
            command.extend(["-coverage", "1"])
        command.extend(["-config", str(config), str(module)])
        output = run_capture(
            command, cwd=TLA_ROOT, timeout=timeout, echo=not required_coverage
        )
        (metadata / "tlc.log").write_text(output, encoding="utf-8")
        verify_action_coverage(output, required_coverage)
        if required_coverage:
            summary_patterns = (
                "Model checking completed.",
                " states generated, ",
                "The depth of the complete state graph",
            )
            for line in output.splitlines():
                if any(pattern in line for pattern in summary_patterns) or any(
                    line.startswith(f"<{action} ") for action in required_coverage
                ):
                    print(line)


def run_proofs() -> None:
    manifest = PROOFS / "lake-manifest.json"
    if not manifest.is_file():
        fail(
            "missing pinned formal/proofs/lake-manifest.json; "
            "implicit dependency resolution is forbidden"
        )
    native_lake = (
        TOOLCHAIN
        / "windows"
        / "lean-4.32.1-windows"
        / "bin"
        / "lake.exe"
    )
    lake = os.environ.get(
        "LAKE",
        str(native_lake) if os.name == "nt" and native_lake.is_file() else "lake",
    )
    if shutil.which(lake) is None and not Path(lake).is_file():
        fail(f"Lake executable not found: {lake}")
    proof_environment = dict(os.environ)
    proof_environment["LAKE"] = lake
    run(
        [lake, "build", "DeltaReduce"],
        cwd=PROOFS,
        timeout=1200,
        environment=proof_environment,
    )
    run_script(
        "formal/scripts/check_lean_evidence.py",
        [],
        300,
        environment=proof_environment,
    )


def run_script(
    relative_path: str,
    arguments: list[str],
    timeout: int,
    *,
    environment: dict[str, str] | None = None,
) -> None:
    script = ROOT / relative_path
    if not script.is_file():
        fail(f"missing mandatory gate script: {relative_path}")
    run(
        [sys.executable, str(script), *arguments],
        cwd=ROOT,
        timeout=timeout,
        environment=environment,
    )


def dispatch(gate: str) -> None:
    if gate == "parse":
        parse_modules()
    elif gate in {"safety", "liveness"}:
        run_tlc(gate)
        if gate == "liveness":
            run_script("formal/scripts/run_liveness_counterchecks.py", [], 180)
    elif gate == "proofs":
        run_proofs()
    elif gate == "mutants":
        run_script("formal/scripts/run_mutants.py", [], 1200)
    elif gate == "refinement":
        run_script("formal/scripts/check-refinement.py", ["--all-fixtures"], 300)
    elif gate == "report":
        report = ROOT / "formal" / "reports" / "formal-verification-report.json"
        if not report.is_file():
            fail("missing FormalVerificationReport; report success cannot be vacuous")
        run_script("formal/scripts/verify_formal_report.py", [str(report), "--require-go"], 300)
    else:
        fail(f"unknown gate: {gate}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("gate", choices=GATES)
    arguments = parser.parse_args()
    try:
        dispatch(arguments.gate)
    except (RuntimeError, ValueError, OSError, subprocess.SubprocessError) as error:
        output: dict[str, Any] = {
            "schema_version": "1.0.0",
            "gate": arguments.gate,
            "status": "FAIL",
            "error": f"{type(error).__name__}:{error}",
        }
        print(json.dumps(output, sort_keys=True, separators=(",", ":")), file=sys.stderr)
        return 1
    print(
        json.dumps(
            {"schema_version": "1.0.0", "gate": arguments.gate, "status": "PASS"},
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
