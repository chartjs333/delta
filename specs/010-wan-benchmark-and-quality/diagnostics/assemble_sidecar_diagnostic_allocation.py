#!/usr/bin/env python3
"""Build and exclusively seal a Feature 010 diagnostic allocation."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import sidecar_diagnostic_common as contract  # noqa: E402

PLAN_TYPE = "FEATURE010_SIDECAR_DIAGNOSTIC_ALLOCATION_PLAN"
PLAN_FIELDS = {
    "allocation_manifest_path",
    "allocation_root",
    "container",
    "invocation",
    "resources",
    "schema_version",
    "source",
    "type_name",
}
INVOCATION_FIELDS = {"argv", "environment", "environment_mode", "working_directory"}
FIXED_ARTIFACT_PATHS = {
    "BUILD_PROVENANCE_RECEIPT": "build-provenance.json",
    "CANONICAL_CORPUS": "corpus.bin",
    "JAVA_CLASSES_JAR": "sidecar-diagnostic-tests.jar",
    "JAVA_EXECUTABLE": "jdk/bin/java",
    "JFR_EXECUTABLE": "jdk/bin/jfr",
    "NATIVE_LIBRARY": "libdelta_ffi.so",
    "SIDECAR_EXECUTABLE": "delta_runtime_sidecar",
    "STRACE_EXECUTABLE": "bin/strace",
}
EXECUTABLE_ARTIFACT_IDS = {
    "JAVA_EXECUTABLE",
    "JFR_EXECUTABLE",
    "SIDECAR_EXECUTABLE",
    "STRACE_EXECUTABLE",
}


def exclusive_write(path: Path, payload: bytes) -> None:
    contract.require(path.is_absolute(), "ASSEMBLER_OUTPUT_NOT_ABSOLUTE", str(path))
    contract.require(path.parent.is_dir(), "ASSEMBLER_OUTPUT_PARENT_MISSING", str(path.parent))
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=False) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(descriptor)
    if os.name == "posix":
        directory = os.open(path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        try:
            os.fsync(directory)
        finally:
            os.close(directory)


def exclusive_document(path: Path, value: object) -> None:
    exclusive_write(path, contract.canonical_bytes(value) + b"\n")


def absolute_path(value: object, code: str) -> Path:
    text = contract.strict_text(value, code)
    contract.require(contract.absolute_contract_path(text), f"{code}_ABSOLUTE")
    return Path(text)


def validate_source(value: object) -> dict[str, Any]:
    source = contract.exact_object(value, contract.SOURCE_FIELDS, "PLAN_SOURCE_FIELDS")
    contract.require(source["repository"] == contract.SOURCE_REPOSITORY, "PLAN_REPOSITORY")
    for name in ("commit", "tree"):
        item = contract.strict_text(source[name], f"PLAN_SOURCE_{name.upper()}", maximum=40)
        contract.require(
            contract.GIT_OBJECT.fullmatch(item) is not None, f"PLAN_SOURCE_{name.upper()}"
        )
        contract.require(item != "0" * 40, f"PLAN_SOURCE_{name.upper()}_PLACEHOLDER")
    return source


def validate_invocation(value: object) -> dict[str, Any]:
    invocation = contract.exact_object(value, INVOCATION_FIELDS, "PLAN_INVOCATION_FIELDS")
    argv = invocation["argv"]
    contract.require(isinstance(argv, list) and argv, "PLAN_INVOCATION_ARGV")
    for item in argv:
        contract.strict_text(item, "PLAN_INVOCATION_ARGV_ITEM")
    executable = absolute_path(argv[0], "PLAN_INVOCATION_EXECUTABLE")
    contract.require(executable.is_file(), "PLAN_INVOCATION_EXECUTABLE_MISSING", str(executable))
    contract.require(os.access(executable, os.X_OK), "PLAN_INVOCATION_EXECUTABLE_NOT_EXECUTABLE")
    environment = invocation["environment"]
    contract.require(isinstance(environment, dict), "PLAN_INVOCATION_ENVIRONMENT")
    for key, item in environment.items():
        contract.strict_text(key, "PLAN_INVOCATION_ENVIRONMENT_KEY")
        contract.strict_text(item, "PLAN_INVOCATION_ENVIRONMENT_VALUE")
    contract.require(invocation["environment_mode"] == "REPLACE", "PLAN_ENVIRONMENT_MODE")
    working_directory = absolute_path(
        invocation["working_directory"], "PLAN_INVOCATION_WORKING_DIRECTORY"
    )
    contract.require(working_directory.is_dir(), "PLAN_WORKING_DIRECTORY_MISSING")
    return invocation


def validate_plan(value: object, source_root: Path) -> dict[str, Any]:
    plan = contract.exact_object(value, PLAN_FIELDS, "PLAN_FIELDS")
    contract.require(plan["schema_version"] == contract.SCHEMA_VERSION, "PLAN_SCHEMA")
    contract.require(plan["type_name"] == PLAN_TYPE, "PLAN_TYPE")
    validate_source(plan["source"])
    invocation = validate_invocation(plan["invocation"])
    checkout = source_root.resolve(strict=True)
    working_directory = Path(str(invocation["working_directory"])).resolve(strict=True)
    contract.require(working_directory == checkout, "PLAN_WORKING_DIRECTORY_NOT_SOURCE_ROOT")

    allocation_root = absolute_path(plan["allocation_root"], "PLAN_ALLOCATION_ROOT")
    allocation_manifest = absolute_path(
        plan["allocation_manifest_path"], "PLAN_ALLOCATION_MANIFEST"
    )
    contract.require(
        allocation_manifest.resolve(strict=False) != allocation_root.resolve(strict=False)
        and allocation_root.resolve(strict=False)
        not in allocation_manifest.resolve(strict=False).parents,
        "PLAN_MANIFEST_INSIDE_ALLOCATION",
    )
    container = contract.exact_object(
        plan["container"], {"image_digest", "runtime", "runtime_version"}, "PLAN_CONTAINER_FIELDS"
    )
    contract.content_id(container["image_digest"], "PLAN_IMAGE_DIGEST")
    contract.require(container["runtime"] in {"docker", "podman"}, "PLAN_RUNTIME")
    contract.strict_text(container["runtime_version"], "PLAN_RUNTIME_VERSION", maximum=512)
    resources = contract.exact_object(
        plan["resources"],
        {"available_processors", "cgroup_mode", "cpu_max", "cpuset_cpus_effective", "memory_max"},
        "PLAN_RESOURCE_FIELDS",
    )
    contract.strict_int(resources["available_processors"], "PLAN_PROCESSORS", minimum=1)
    contract.require(resources["cgroup_mode"] in {"V1", "V2"}, "PLAN_CGROUP_MODE")
    for name in ("cpu_max", "cpuset_cpus_effective", "memory_max"):
        contract.strict_text(resources[name], f"PLAN_{name.upper()}", maximum=512)
    return plan


def load_plan(path: Path, source_root: Path) -> tuple[dict[str, Any], bytes]:
    plan, canonical = contract.canonical_document(path)
    return validate_plan(plan, source_root), canonical


def file_record(path: Path) -> dict[str, object]:
    resolved = path.resolve(strict=True)
    contract.require(resolved.is_file(), "ASSEMBLER_ARTIFACT_MISSING", str(path))
    payload = resolved.read_bytes()
    contract.require(payload, "ASSEMBLER_ARTIFACT_EMPTY", str(path))
    return {
        "path": str(resolved),
        "sha256": contract.sha256_id(payload),
        "size_bytes": len(payload),
    }


def execution_record(path: Path) -> dict[str, object]:
    resolved = path.resolve(strict=True)
    payload = resolved.read_bytes()
    return {
        "path": str(resolved),
        "sha256": contract.sha256_id(payload),
        "size_bytes": len(payload),
    }


def source_receipt(plan: dict[str, Any], source_root: Path) -> dict[str, object]:
    receipt = contract.verify_source_checkout(source_root, plan["source"])
    contract.require(
        receipt["checkout_root"] == str(source_root.resolve(strict=True)), "PLAN_SOURCE_ROOT"
    )
    return receipt


def artifact_paths(plan: dict[str, Any]) -> dict[str, Path]:
    root = Path(str(plan["allocation_root"])).resolve(strict=True)
    return {identifier: root / relative for identifier, relative in FIXED_ARTIFACT_PATHS.items()}


def manifest_stub(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "environment": {
            "allocation_root": plan["allocation_root"],
            "container_image_digest": plan["container"]["image_digest"],
            "container_runtime": {
                "name": plan["container"]["runtime"],
                "version": plan["container"]["runtime_version"],
            },
        },
        "source": plan["source"],
    }


def verify_generated_allocation(
    plan: dict[str, Any], source_root: Path, allocation_manifest: Path
) -> dict[str, Any]:
    validate_plan(plan, source_root)
    observed_source = source_receipt(plan, source_root)
    record = file_record(allocation_manifest)
    allocation = contract.load_and_verify_allocation(record, manifest_stub(plan))
    contract.require(allocation["container"] == plan["container"], "ASSEMBLER_VERIFY_CONTAINER")
    contract.require(allocation["resources"] == plan["resources"], "ASSEMBLER_VERIFY_RESOURCES")
    contract.require(allocation["source"] == plan["source"], "ASSEMBLER_VERIFY_SOURCE")
    expected_paths = artifact_paths(plan)
    indexed = {item["artifact_id"]: item for item in allocation["artifacts"]}
    for identifier in contract.ALLOCATION_ARTIFACT_IDS:
        contract.require(
            Path(str(indexed[identifier]["path"])).resolve(strict=True)
            == expected_paths[identifier].resolve(strict=True),
            "ASSEMBLER_VERIFY_ARTIFACT_PATH",
            identifier,
        )
    provenance, _ = contract.canonical_document(expected_paths["BUILD_PROVENANCE_RECEIPT"])
    contract.require(provenance["invocation"] == plan["invocation"], "ASSEMBLER_VERIFY_INVOCATION")
    contract.require(
        provenance["source_checkout"] == observed_source, "ASSEMBLER_VERIFY_SOURCE_CHECKOUT"
    )
    return allocation


def build_and_assemble(plan: dict[str, Any], source_root: Path) -> dict[str, Any]:
    validate_plan(plan, source_root)
    observed_source = source_receipt(plan, source_root)
    allocation_root = Path(str(plan["allocation_root"]))
    allocation_manifest = Path(str(plan["allocation_manifest_path"]))
    contract.require(not allocation_root.exists(), "ASSEMBLER_ALLOCATION_ROOT_MUST_BE_FRESH")
    contract.require(allocation_root.parent.is_dir(), "ASSEMBLER_ALLOCATION_PARENT_MISSING")
    contract.require(not allocation_manifest.exists(), "ASSEMBLER_MANIFEST_MUST_BE_FRESH")
    contract.require(allocation_manifest.parent.is_dir(), "ASSEMBLER_MANIFEST_PARENT_MISSING")

    invocation = plan["invocation"]
    completed = subprocess.run(
        list(invocation["argv"]),
        cwd=invocation["working_directory"],
        env={str(key): str(value) for key, value in invocation["environment"].items()},
        check=False,
        capture_output=True,
    )
    contract.require(completed.returncode == 0, "ASSEMBLER_BUILD_EXIT", str(completed.returncode))
    contract.require(allocation_root.is_dir(), "ASSEMBLER_BUILD_DID_NOT_CREATE_ROOT")
    stdout_path = allocation_root / "build.stdout"
    stderr_path = allocation_root / "build.stderr"
    exclusive_write(stdout_path, completed.stdout)
    exclusive_write(stderr_path, completed.stderr)

    paths = artifact_paths(plan)
    contract.require(
        not paths["BUILD_PROVENANCE_RECEIPT"].exists(), "ASSEMBLER_PROVENANCE_MUST_BE_FRESH"
    )
    indexed: dict[str, dict[str, object]] = {}
    for identifier in contract.ALLOCATION_ARTIFACT_IDS[1:]:
        indexed[identifier] = {"artifact_id": identifier, **file_record(paths[identifier])}
        if identifier in EXECUTABLE_ARTIFACT_IDS:
            contract.require(
                os.access(paths[identifier], os.X_OK),
                "ASSEMBLER_ARTIFACT_NOT_EXECUTABLE",
                identifier,
            )
    provenance = {
        "builder_container_image_digest": plan["container"]["image_digest"],
        "execution": {
            "exit_code": completed.returncode,
            "stderr": execution_record(stderr_path),
            "stdout": execution_record(stdout_path),
        },
        "invocation": invocation,
        "invocation_sha256": contract.sha256_id(contract.canonical_bytes(invocation)),
        "outputs": [
            {"artifact_id": identifier, "sha256": indexed[identifier]["sha256"]}
            for identifier in contract.BUILD_OUTPUT_IDS
        ],
        "schema_version": contract.SCHEMA_VERSION,
        "source": plan["source"],
        "source_checkout": observed_source,
        "type_name": contract.BUILD_PROVENANCE_TYPE,
    }
    exclusive_document(paths["BUILD_PROVENANCE_RECEIPT"], provenance)
    indexed["BUILD_PROVENANCE_RECEIPT"] = {
        "artifact_id": "BUILD_PROVENANCE_RECEIPT",
        **file_record(paths["BUILD_PROVENANCE_RECEIPT"]),
    }
    jdk_root = paths["JAVA_EXECUTABLE"].parent.parent
    allocation = {
        "artifacts": [indexed[identifier] for identifier in contract.ALLOCATION_ARTIFACT_IDS],
        "container": plan["container"],
        "jdk_tree": {**contract.directory_inventory(jdk_root), "root": str(jdk_root.resolve())},
        "resources": plan["resources"],
        "schema_version": contract.SCHEMA_VERSION,
        "source": plan["source"],
        "type_name": contract.ALLOCATION_TYPE,
    }
    exclusive_document(allocation_manifest, allocation)
    verified = verify_generated_allocation(plan, source_root, allocation_manifest)
    contract.require(verified == allocation, "ASSEMBLER_ROUND_TRIP_MISMATCH")
    return allocation


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build-and-assemble")
    build.add_argument("--plan", type=Path, required=True)
    build.add_argument("--source-checkout", type=Path, required=True)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--plan", type=Path, required=True)
    verify.add_argument("--source-checkout", type=Path, required=True)
    verify.add_argument("--allocation-manifest", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        plan, _ = load_plan(args.plan, args.source_checkout)
        if args.command == "build-and-assemble":
            build_and_assemble(plan, args.source_checkout)
        else:
            expected = Path(str(plan["allocation_manifest_path"])).resolve(strict=True)
            supplied = args.allocation_manifest.resolve(strict=True)
            contract.require(supplied == expected, "ASSEMBLER_VERIFY_MANIFEST_PATH")
            verify_generated_allocation(plan, args.source_checkout, supplied)
    except (OSError, subprocess.SubprocessError, contract.DiagnosticError) as error:
        print(f"sidecar diagnostic allocation assembly failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
