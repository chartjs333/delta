#!/usr/bin/env python3
"""Explicitly fetch, or verify offline, the locked Lean dependency sources.

Existing directories are never reset, removed or silently repaired. The build
gate calls only verify_packages; network access belongs to --download setup.
This verifies source identities, not precompiled .olean provenance or Formal GO.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROOFS = ROOT / "formal/proofs"


def git(path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-c", "core.autocrlf=false", "-C", str(path), *args],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    return result.stdout.strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def locked_packages(proofs: Path) -> tuple[dict, list[dict]]:
    lock = json.loads((proofs / "dependencies.lock.json").read_text(encoding="utf-8"))
    manifest = json.loads((proofs / "lake-manifest.json").read_text(encoding="utf-8"))
    packages = lock["packages"]
    if not packages or len({p["name"] for p in packages}) != len(packages):
        raise ValueError("Empty or duplicate dependency lock")
    for item in packages:
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_-]*", item["name"]):
            raise ValueError("Unsafe package name")
        if not re.fullmatch(r"[0-9a-f]{40}", item["rev"]):
            raise ValueError("Dependency revision must be an exact commit")
        if not re.fullmatch(r"https://github.com/[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+", item["url"]):
            raise ValueError("Dependency URL is outside the locked public GitHub form")
        if item["license_path"] != "LICENSE":
            raise ValueError("Unsupported license path")
    expected = sorted((p["name"], p["rev"], p["url"]) for p in packages)
    actual = sorted((p["name"], p["rev"], p["url"]) for p in manifest["packages"])
    if actual != expected or manifest["packagesDir"] != ".lake/packages":
        raise ValueError("Lake manifest differs from the locked package identities")
    for item in manifest["packages"]:
        if (
            item.get("type") != "git"
            or item.get("subDir") is not None
            or item.get("manifestFile") != "lake-manifest.json"
            or item.get("configFile") not in {"lakefile.lean", "lakefile.toml"}
        ):
            raise ValueError("Lake manifest redirects a locked package")
    return lock, packages


def package_path(proofs: Path, name: str) -> Path:
    directory = (proofs / ".lake/packages").resolve()
    if not directory.is_relative_to(proofs.resolve()):
        raise ValueError("Dependency cache escapes the proof workspace")
    path = directory / name
    if path.resolve().parent != directory:
        raise ValueError(f"Package path escapes the source cache: {name}")
    return path


def verify_package(proofs: Path, item: dict) -> dict:
    path = package_path(proofs, item["name"])
    if not (path / ".git").exists():
        raise ValueError(f"Missing materialized dependency: {item['name']}")
    if Path(git(path, "rev-parse", "--show-toplevel")).resolve() != path.resolve():
        raise ValueError(f"Dependency is not an isolated checkout: {item['name']}")
    if git(path, "remote", "get-url", "origin") != item["url"]:
        raise ValueError(f"Dependency URL mismatch: {item['name']}")
    if git(path, "rev-parse", "HEAD") != item["rev"]:
        raise ValueError(f"Dependency revision mismatch: {item['name']}")
    if git(path, "status", "--porcelain", "--untracked-files=all"):
        raise ValueError(f"Dependency has modified/untracked source: {item['name']}")
    if sha256(path / item["license_path"]) != item["license_sha256"]:
        raise ValueError(f"Dependency license mismatch: {item['name']}")
    return {
        "name": item["name"],
        "rev": item["rev"],
        "url": item["url"],
        "git_tree": git(path, "rev-parse", "HEAD^{tree}"),
        "license_sha256": item["license_sha256"],
        "status": "PASS",
    }


def verify_packages(proofs: Path = PROOFS) -> dict:
    lock, packages = locked_packages(proofs)
    records = [verify_package(proofs, item) for item in packages]
    mathlib = package_path(proofs, "mathlib")
    if sha256(mathlib / "lake-manifest.json") != lock["source"]["lake_manifest_sha256"]:
        raise ValueError("Pinned mathlib upstream manifest mismatch")
    if (mathlib / "lean-toolchain").read_text().strip() != (
        proofs / "lean-toolchain"
    ).read_text().strip():
        raise ValueError("Mathlib Lean toolchain mismatch")
    return {
        "schema_version": "1.0.0",
        "status": "PASS",
        "scope": "LOCKED_DEPENDENCY_SOURCES_ONLY",
        "dependency_lock_sha256": sha256(proofs / "dependencies.lock.json"),
        "packages": records,
        "compiled_cache_provenance_verified": False,
        "formal_go": False,
    }


def download_packages(proofs: Path = PROOFS) -> None:
    _, packages = locked_packages(proofs)
    for item in packages:
        path = package_path(proofs, item["name"])
        if path.exists():
            verify_package(proofs, item)
            continue
        path.mkdir(parents=True)
        git(path, "init", "--quiet")
        git(path, "config", "core.autocrlf", "false")
        git(path, "config", "core.eol", "lf")
        git(path, "remote", "add", "origin", item["url"])
        git(path, "fetch", "--depth", "1", "origin", item["rev"])
        git(path, "checkout", "--detach", item["rev"])
        verify_package(proofs, item)
        print(f"Prepared exact source: {item['name']} {item['rev']}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        if args.download:
            download_packages()
        result = verify_packages()
    except (ValueError, OSError, KeyError, subprocess.SubprocessError) as error:
        result = {"schema_version": "1.0.0", "status": "FAIL", "error": str(error)}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(result, sort_keys=True, separators=(",", ":")), encoding="utf-8"
        )
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
