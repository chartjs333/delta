#!/usr/bin/env python3
"""Install already verified formal artifacts without network access."""

from __future__ import annotations

import argparse
import json
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from pathlib import Path

from prepare_cache import TOOLCHAIN_DIR, artifacts, verify


def move_single_root(extracted: Path, destination: Path) -> None:
    entries = list(extracted.iterdir())
    source = entries[0] if len(entries) == 1 and entries[0].is_dir() else extracted
    destination.mkdir(parents=True, exist_ok=False)
    for entry in source.iterdir():
        shutil.move(str(entry), destination / entry.name)


def extract_tar(archive: Path, destination: Path) -> None:
    with tempfile.TemporaryDirectory(
        prefix="formal-jre-", dir=destination.parent
    ) as temporary_name:
        temporary = Path(temporary_name)
        with tarfile.open(archive, mode="r:gz") as source:
            source.extractall(temporary, filter="data")
        move_single_root(temporary, destination)


def extract_zip(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    root = destination.resolve()
    with zipfile.ZipFile(archive) as source:
        members = [member for member in source.infolist() if member.filename]
        first_parts = {
            Path(member.filename.replace("\\", "/")).parts[0]
            for member in members
        }
        strip_root = next(iter(first_parts)) if len(first_parts) == 1 else None
        for member in members:
            parts = Path(member.filename.replace("\\", "/")).parts
            if strip_root is not None and parts and parts[0] == strip_root:
                parts = parts[1:]
            if not parts:
                continue
            target = destination.joinpath(*parts).resolve()
            if root not in target.parents and target != root:
                raise ValueError(f"unsafe zip path: {member.filename}")
            unix_mode = member.external_attr >> 16
            if stat.S_ISLNK(unix_mode):
                raise ValueError(f"zip symlink is forbidden: {member.filename}")
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with source.open(member) as input_stream, target.open("wb") as output_stream:
                shutil.copyfileobj(input_stream, output_stream)
            permission_bits = stat.S_IMODE(unix_mode)
            if permission_bits and sys.platform != "win32":
                target.chmod(permission_bits)


def command_output(command: list[str]) -> str:
    result = subprocess.run(
        command,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=30,
    )
    return result.stdout.strip().splitlines()[0]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache-dir", type=Path, required=True)
    parser.add_argument("--destination", type=Path, required=True)
    parser.add_argument("--component", choices=("all", "tla", "lean"), default="all")
    arguments = parser.parse_args()

    selected = artifacts(arguments.component)
    locked = {artifact["artifact"]: artifact for artifact in selected}
    for artifact_name, artifact in locked.items():
        valid, reason = verify(arguments.cache_dir / artifact_name, artifact)
        if not valid:
            raise ValueError(f"{artifact_name} failed verification: {reason}")

    if arguments.destination.exists():
        raise ValueError(f"destination already exists: {arguments.destination}")
    arguments.destination.mkdir(parents=True)

    executable_suffix = ".exe" if sys.platform == "win32" else ""
    versions: dict[str, str] = {}
    if arguments.component in {"all", "tla"}:
        java_dir = arguments.destination / "java"
        tla_dir = arguments.destination / "tla"
        jvm = next(artifact for artifact in selected if artifact["project"].startswith("adoptium/"))
        jvm_archive = arguments.cache_dir / jvm["artifact"]
        if jvm_archive.name.endswith(".tar.gz"):
            extract_tar(jvm_archive, java_dir)
        else:
            extract_zip(jvm_archive, java_dir)
        tla_dir.mkdir()
        shutil.copy2(arguments.cache_dir / "tla2tools.jar", tla_dir / "tla2tools.jar")
        versions["java"] = command_output(
            [str(java_dir / "bin" / f"java{executable_suffix}"), "-version"]
        )
    if arguments.component in {"all", "lean"}:
        lean_dir = arguments.destination / "lean"
        lean = next(artifact for artifact in selected if artifact["component"] == "lean")
        extract_zip(arguments.cache_dir / lean["artifact"], lean_dir)
        versions["lean"] = command_output(
            [str(lean_dir / "bin" / f"lean{executable_suffix}"), "--version"]
        )
        versions["lake"] = command_output(
            [str(lean_dir / "bin" / f"lake{executable_suffix}"), "--version"]
        )
    print(
        json.dumps(
            {"schema_version": "1.0.0", "status": "PASS", "versions": versions},
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
