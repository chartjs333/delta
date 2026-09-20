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
REPRODUCTION_EVIDENCE = ROOT / "formal" / "reports" / "reproducibility-evidence.json"
FINAL_REPORT = ROOT / "formal" / "reports" / "formal-verification-report.json"
sys.path.insert(0, str(ROOT / "formal" / "scripts"))

from formal_artifacts import (  # noqa: E402
    REPRODUCTION_COMMANDS,
    CanonicalJsonError,
    canonical_json_bytes,
    derive_formal_semantics_id,
    discover_semantic_artifacts,
    git_output,
    git_revision,
    load_json_strict,
    reproduction_check_sha256,
    reproduction_matches_source,
    sha256_file,
    source_commit_from_history,
    write_canonical_json,
)
from tlc_results import successful_tlc_result  # noqa: E402

TIMEOUTS = {
    "phase0": 60,
    "contracts": 120,
    "parse": 300,
    "safety": 2400,
    "liveness": 900,
    "proofs": 1800,
    "toolchain": 300,
    "mutants": 1200,
    "refinement": 300,
    "tlc-evidence": 120,
    "cross-artifact": 120,
}
COMMANDS = tuple(
    (identifier, list(command), TIMEOUTS[identifier])
    for identifier, command in REPRODUCTION_COMMANDS
)
FINALIZATION_COMMANDS = (
    ("report-generation", ["python3", "formal/scripts/generate_formal_report.py"], 60),
    (
        "report-verifier",
        [
            "python3",
            "formal/scripts/verify_formal_report.py",
            "formal/reports/formal-verification-report.json",
        ],
        60,
    ),
)


RUNTIME_PREFIXES = (
    ".apalache/",
    ".git/",
    "formal/build/",
    "formal/mutants/states/",
    "formal/proofs/.lake/",
    "formal/proofs/build/",
    "formal/proofs/lake-packages/",
    "formal/reports/local/",
    "formal/toolchain/cache/",
    "formal/toolchain/windows/",
    "formal/tla/states/",
)


def is_runtime_path(relative: str) -> bool:
    return (
        "__pycache__/" in relative
        or relative.startswith(RUNTIME_PREFIXES)
        or relative.endswith((".class", ".log", ".pyc", ".pyo"))
    )


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


def git_safe_directory_environment(
    environment: dict[str, str], root: Path = ROOT
) -> dict[str, str]:
    """Allow Git to inspect only the exact bind-mounted proof checkouts.

    Git rejects repositories owned by the host runner when the container runs as
    root. Lake interprets that rejection as a changed dependency URL and tries to
    clone again. Command-scope config keeps the network-none build deterministic
    without granting the wildcard safe.directory exception.
    """

    dependencies = load_json_strict(root / "formal" / "proofs" / "dependencies.lock.json")
    package_names = [package["name"] for package in dependencies["packages"]]
    safe_directories = [
        root / "formal" / "proofs",
        *(root / "formal" / "proofs" / ".lake" / "packages" / name for name in package_names),
    ]
    configured = dict(environment)
    configured["GIT_CONFIG_COUNT"] = str(len(safe_directories))
    for index, directory in enumerate(safe_directories):
        configured[f"GIT_CONFIG_KEY_{index}"] = "safe.directory"
        configured[f"GIT_CONFIG_VALUE_{index}"] = str(directory.resolve())
    return configured


def verify_source_manifest(path: Path, root: Path = ROOT) -> dict[str, Any]:
    manifest = load_json_strict(path)
    if set(manifest) != {
        "schema_version",
        "checkout_commit",
        "checkout_tree",
        "source_commit",
        "source_tree",
        "source_clean",
        "files",
    }:
        raise ValueError("source manifest shape mismatch")
    if manifest["schema_version"] != "2.0.0" or manifest["source_clean"] is not True:
        raise ValueError("source manifest is not a clean v2 snapshot")
    for field in ("checkout_commit", "checkout_tree", "source_commit", "source_tree"):
        if not isinstance(manifest[field], str) or not re.fullmatch(
            r"[0-9a-f]{40}", manifest[field]
        ):
            raise ValueError(f"invalid {field}")
    if git_output(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("source checkout is not clean")
    if git_revision(root, "HEAD") != manifest["checkout_commit"]:
        raise ValueError("manifest checkout commit is not HEAD")
    if git_revision(root, "HEAD^{tree}") != manifest["checkout_tree"]:
        raise ValueError("manifest checkout tree does not belong to HEAD")
    expected_source_commit = source_commit_from_history(root)
    if manifest["source_commit"] != expected_source_commit:
        raise ValueError("manifest source commit is not the latest non-evidence commit")
    if git_revision(root, f"{manifest['source_commit']}^{{tree}}") != manifest["source_tree"]:
        raise ValueError("source manifest tree does not belong to its commit")

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
    missing = sorted(relative for relative in declared - observed if not is_runtime_path(relative))
    if extras or missing:
        raise ValueError(f"source file set mismatch: extras={extras}, missing={missing}")
    return manifest


def _canonical_result(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    result = {
        "schema_version": "1.0.0",
        "kind": kind,
        "status": "PASS",
        "payload": payload,
    }
    canonical_json_bytes(result)
    return result


def _last_json_object(output: str) -> dict[str, Any]:
    for line in reversed(output.splitlines()):
        if not line.startswith("{"):
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise ValueError("stage output contains no JSON result object")


def _artifact_payload(paths: list[Path], root: Path = ROOT) -> dict[str, Any]:
    artifacts: list[dict[str, str]] = []
    for path in sorted(paths):
        if not path.is_file():
            raise ValueError(f"missing stage artifact: {path.relative_to(root)}")
        artifacts.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": sha256_file(path),
            }
        )
    return {"artifacts": artifacts}


def _tla_module_payload(root: Path = ROOT) -> dict[str, Any]:
    modules = sorted((root / "formal" / "tla").rglob("*.tla"))
    if not modules:
        raise ValueError("SANY stage has no TLA+ modules")
    return _artifact_payload(modules, root)


def _tlc_stage_payload(kind: str, root: Path = ROOT) -> dict[str, Any]:
    manifest = load_json_strict(root / "formal" / "tla" / "cfg" / "config-manifest.json")
    lock = load_json_strict(root / "formal" / "toolchain" / "tla.lock")
    expected_version = lock["tla_tools"]["reported_tlc_version"]
    expected_revision = lock["tla_tools"]["release_commit"]
    models: list[dict[str, Any]] = []
    for entry in manifest["configs"]:
        if entry["kind"] != kind:
            continue
        log = root / "formal" / "build" / "tlc" / entry["id"] / "tlc.log"
        if not log.is_file():
            raise ValueError(f"missing TLC log for {entry['id']}")
        parsed = successful_tlc_result(
            log.read_text(encoding="utf-8", errors="replace"),
            expected_version=expected_version,
            expected_revision=expected_revision,
            fingerprint_index=entry["fingerprint_index"],
            seed=entry["seed"],
            workers=entry["workers"],
            required_actions=entry.get("required_action_coverage", []),
        )
        module = root / "formal" / "tla" / entry["module"]
        config = root / "formal" / "tla" / entry["config"]
        models.append(
            {
                "id": entry["id"],
                "module_sha256": sha256_file(module),
                "config_sha256": sha256_file(config),
                "tool_sha256": lock["tla_tools"]["sha256"],
                "result": parsed,
            }
        )
    if not models:
        raise ValueError(f"no {kind} TLC models in the manifest")
    payload: dict[str, Any] = {"models": models}
    if kind == "liveness":
        payload.update(
            _artifact_payload(
                [root / "formal" / "reports" / "liveness-countercheck.json"],
                root,
            )
        )
    return payload


def stage_result(identifier: str, output: str, root: Path = ROOT) -> dict[str, Any]:
    """Build a deterministic result projection after a successful stage."""

    if identifier == "phase0":
        result = _last_json_object(output)
        if result.get("status") != "PASS":
            raise ValueError("phase0 did not publish PASS")
        return _canonical_result("phase0-summary", result)
    if identifier == "contracts":
        matches = re.findall(r"^Ran ([0-9]+) tests? in .+$", output, re.MULTILINE)
        if len(matches) != 1 or re.search(r"^OK$", output, re.MULTILINE) is None:
            raise ValueError("unittest output lacks one successful test summary")
        return _canonical_result(
            "unittest-summary", {"framework": "unittest", "tests_run": int(matches[0])}
        )
    if identifier == "parse":
        return _canonical_result("sany-module-set", _tla_module_payload(root))
    if identifier in {"safety", "liveness"}:
        return _canonical_result("tlc-model-set", _tlc_stage_payload(identifier, root))

    artifact_paths = {
        "proofs": [root / "formal" / "reports" / "lean-proof-report.json"],
        "toolchain": [root / "formal" / "reports" / "toolchain-evidence.json"],
        "mutants": [
            root / "formal" / "reports" / "mutant-evidence.json",
            *sorted((root / "formal" / "fixtures" / "counterexamples").glob("*.json")),
        ],
        "refinement": [root / "formal" / "reports" / "refinement-evidence.json"],
        "tlc-evidence": [
            root / "formal" / "reports" / "tlc-evidence.json",
            root / "formal" / "reports" / "executed-coverage.md",
        ],
        "cross-artifact": [
            root / "formal" / "reports" / "cross-artifact-analysis.json",
            root / "formal" / "reports" / "final-constitution-check.md",
        ],
    }
    paths = artifact_paths.get(identifier)
    if paths is None:
        raise ValueError(f"no deterministic result profile for stage {identifier}")
    return _canonical_result("artifact-set", _artifact_payload(paths, root))


def _actual_command(canonical_command: list[str]) -> list[str]:
    if not canonical_command or canonical_command[0] != "python3":
        raise ValueError("only registered Python commands are allowed")
    return [sys.executable, *canonical_command[1:]]


def verify_complete_reproduction_receipt(
    report: dict[str, Any],
    source_manifest: dict[str, Any],
    formal_semantics_id: str,
    root: Path = ROOT,
) -> bool:
    """Publish provisional PASS only when its complete receipt validates."""

    report["status"] = "PASS"
    valid = reproduction_matches_source(
        report,
        source_manifest["source_commit"],
        formal_semantics_id,
        source_tree=source_manifest["source_tree"],
        root=root,
    )
    if not valid:
        report["status"] = "FAIL"
    return valid


def main() -> int:
    errors: list[str] = []
    if os.name == "nt" or platform.system() != "Linux":
        errors.append("reproduction must execute in Linux")
    observed_machine = platform.machine().lower()
    if observed_machine not in {"amd64", "x86_64"}:
        errors.append(f"reproduction requires amd64, observed {observed_machine}")
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

    for stale_output in (REPORT, REPRODUCTION_EVIDENCE, FINAL_REPORT):
        stale_output.unlink(missing_ok=True)

    semantic_artifacts = discover_semantic_artifacts(ROOT)
    formal_semantics_id = derive_formal_semantics_id("1.0.0", semantic_artifacts)

    environment = dict(os.environ)
    for inherited_override in (
        "FORMAL_VERIFIED_SOURCE_MANIFEST",
        "JAVA",
        "JAVA_TOOL_OPTIONS",
        "JDK_JAVA_OPTIONS",
        "LAKE",
        "MUTANT_FILTER",
        "TLA2TOOLS_JAR",
        "_JAVA_OPTIONS",
    ):
        environment.pop(inherited_override, None)
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
    if source_manifest is not None and not errors:
        environment["FORMAL_VERIFIED_SOURCE_MANIFEST"] = str(manifest_path)
    environment = git_safe_directory_environment(environment)
    checks: list[dict[str, Any]] = []
    report: dict[str, Any] = {
        "schema_version": "2.0.0",
        "status": "FAIL",
        "environment": "linux/amd64 clean container with --network none",
        "source_commit": source_manifest["source_commit"] if source_manifest else "0" * 40,
        "source_tree": source_manifest["source_tree"] if source_manifest else "0" * 40,
        "source_clean_at_start": source_manifest is not None,
        "source_manifest_sha256": sha256_file(manifest_path)
        if manifest_path.is_file()
        else "0" * 64,
        "formal_semantics_id": formal_semantics_id,
        "platform": "Linux-amd64",
        "machine": "amd64",
        "network_interfaces": interfaces,
        "network_proxies_forced_to_loopback": True,
        "checks": checks,
        "errors": errors,
    }
    if not errors:
        for name, canonical_command, timeout in COMMANDS:
            try:
                completed = subprocess.run(
                    _actual_command(canonical_command),
                    cwd=ROOT,
                    env=environment,
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout,
                )
                combined = f"{completed.stdout}\n{completed.stderr}"
            except subprocess.TimeoutExpired as error:
                combined = f"{error.stdout or ''}\n{error.stderr or ''}"
                completed = subprocess.CompletedProcess(
                    _actual_command(canonical_command), 124, error.stdout or "", error.stderr or ""
                )
            except (OSError, subprocess.SubprocessError) as error:
                combined = str(error)
                completed = subprocess.CompletedProcess(
                    _actual_command(canonical_command), 125, "", str(error)
                )
            if completed.returncode != 0:
                checks.append(
                    {
                        "id": name,
                        "command": canonical_command,
                        "exit_code": completed.returncode,
                        "output_sha256": hashlib.sha256(combined.encode("utf-8")).hexdigest(),
                        "status": "FAIL",
                        "failure_output_tail": combined[-8000:],
                    }
                )
                errors.append(f"{name} exited {completed.returncode}")
                break
            try:
                stable_result = stage_result(name, combined)
            except (OSError, ValueError, KeyError, TypeError) as error:
                checks.append(
                    {
                        "id": name,
                        "command": canonical_command,
                        "exit_code": 1,
                        "output_sha256": hashlib.sha256(combined.encode("utf-8")).hexdigest(),
                        "status": "FAIL",
                        "failure_output_tail": f"{error}\n{combined[-7600:]}",
                    }
                )
                errors.append(f"{name} result projection failed: {error}")
                break
            record: dict[str, Any] = {
                "id": name,
                "command": canonical_command,
                "exit_code": 0,
                "result": stable_result,
                "output_sha256": "",
                "status": "PASS",
            }
            record["output_sha256"] = reproduction_check_sha256(record, report)
            checks.append(record)

    if not errors and source_manifest is not None:
        if not verify_complete_reproduction_receipt(
            report,
            source_manifest,
            formal_semantics_id,
        ):
            errors.append("complete reproduction receipt failed strict self-verification")

    report["status"] = "PASS" if not errors else "FAIL"
    write_canonical_json(REPORT, report)
    finalization: list[dict[str, Any]] = []
    if not errors:
        write_canonical_json(REPRODUCTION_EVIDENCE, report)
        FINAL_REPORT.unlink(missing_ok=True)
        for name, canonical_command, timeout in FINALIZATION_COMMANDS:
            try:
                completed = subprocess.run(
                    _actual_command(canonical_command),
                    cwd=ROOT,
                    env=environment,
                    check=False,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=timeout,
                )
                combined = f"{completed.stdout}\n{completed.stderr}"
            except subprocess.TimeoutExpired as error:
                combined = f"{error.stdout or ''}\n{error.stderr or ''}"
                completed = subprocess.CompletedProcess(
                    _actual_command(canonical_command), 124, error.stdout or "", error.stderr or ""
                )
            except (OSError, subprocess.SubprocessError) as error:
                combined = str(error)
                completed = subprocess.CompletedProcess(
                    _actual_command(canonical_command), 125, "", str(error)
                )
            if completed.returncode == 0 and name == "report-verifier":
                try:
                    finalized_report = load_json_strict(FINAL_REPORT)
                    decision = finalized_report["decision"]
                    reasons = finalized_report["decision_reasons"]
                    expected_draft = decision == "NO_GO" and reasons == [
                        "INSUFFICIENT_INDEPENDENT_REVIEWS"
                    ]
                    expected_go = decision == "GO" and reasons == []
                    if not (expected_draft or expected_go):
                        raise ValueError(
                            f"unexpected formal decision after clean run: {decision} {reasons}"
                        )
                except (CanonicalJsonError, KeyError, OSError, TypeError, ValueError) as error:
                    combined = f"{combined}\nstrict final report postcondition failed: {error}"
                    completed = subprocess.CompletedProcess(
                        _actual_command(canonical_command), 1, completed.stdout, completed.stderr
                    )
            finalization.append(
                {
                    "id": name,
                    "status": "PASS" if completed.returncode == 0 else "FAIL",
                }
            )
            if completed.returncode != 0:
                errors.append(f"{name} exited {completed.returncode}: {combined[-4000:]}")
                report["status"] = "FAIL"
                write_canonical_json(REPORT, report)
                write_canonical_json(REPRODUCTION_EVIDENCE, report)
                FINAL_REPORT.unlink(missing_ok=True)
                break

    print(
        json.dumps(
            {"clean_reproduction": report, "finalization": finalization},
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
