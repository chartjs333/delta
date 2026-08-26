#!/usr/bin/env python3
"""Statically verify pinned formal toolchain and dependency contracts."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

from prepare_cache import TOOLCHAIN_DIR, artifacts, verify


ROOT = TOOLCHAIN_DIR.parents[1]
PROOFS = ROOT / "formal" / "proofs"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must be a JSON object")
    return value


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--require-cache", action="store_true")
    parser.add_argument("--cache-dir", type=Path, default=TOOLCHAIN_DIR / "cache")
    arguments = parser.parse_args()
    errors: list[str] = []

    tla = read_json(TOOLCHAIN_DIR / "tla.lock")
    lean = read_json(TOOLCHAIN_DIR / "lean.lock")
    container = read_json(TOOLCHAIN_DIR / "container.lock")
    dependencies = read_json(PROOFS / "dependencies.lock.json")
    lake_manifest = read_json(PROOFS / "lake-manifest.json")
    dockerfile = (TOOLCHAIN_DIR / "Dockerfile").read_text(encoding="utf-8")
    toolchain_name = (PROOFS / "lean-toolchain").read_text(encoding="utf-8").strip()
    with (PROOFS / "lakefile.toml").open("rb") as stream:
        lakefile = tomllib.load(stream)

    require(tla.get("schema_version") == "1.0.0", "unexpected TLA lock schema", errors)
    require(lean.get("schema_version") == "1.0.0", "unexpected Lean lock schema", errors)
    require(
        container.get("schema_version") == "1.0.0",
        "unexpected container lock schema",
        errors,
    )
    require(
        toolchain_name == lean["lean"]["toolchain_name"],
        "lean-toolchain differs from lean.lock",
        errors,
    )
    require(
        lean["mathlib"]["commit"] == dependencies["source"]["commit"],
        "mathlib source commit differs across locks",
        errors,
    )
    require(
        lean["mathlib"]["upstream_lake_manifest_sha256"]
        == dependencies["source"]["lake_manifest_sha256"],
        "mathlib source-manifest hash differs across locks",
        errors,
    )

    lake_requirements = lakefile.get("require", [])
    require(len(lake_requirements) == 1, "Lake must have one direct dependency", errors)
    if len(lake_requirements) == 1:
        mathlib_requirement = lake_requirements[0]
        require(mathlib_requirement.get("name") == "mathlib", "Lake dependency is not mathlib", errors)
        require(
            mathlib_requirement.get("rev") == lean["mathlib"]["commit"],
            "Lake mathlib revision is not the locked full commit",
            errors,
        )

    packages = dependencies.get("packages", [])
    require(isinstance(packages, list) and len(packages) == 9, "dependency lock must contain 9 packages", errors)
    if isinstance(packages, list):
        names = [package.get("name") for package in packages if isinstance(package, dict)]
        require(len(names) == len(set(names)), "duplicate dependency name", errors)
        require(sum(bool(package.get("direct")) for package in packages) == 1, "exactly one dependency must be direct", errors)
        for package in packages:
            if not isinstance(package, dict):
                errors.append("dependency entry is not an object")
                continue
            require(bool(HEX40.fullmatch(str(package.get("rev", "")))), f"dependency {package.get('name')} has non-full revision", errors)
            require(bool(HEX64.fullmatch(str(package.get("license_sha256", "")))), f"dependency {package.get('name')} has invalid license hash", errors)
            require(package.get("license") in {"Apache-2.0", "MIT"}, f"dependency {package.get('name')} has unreviewed license", errors)

    manifest_packages = lake_manifest.get("packages", [])
    require(
        isinstance(manifest_packages, list) and len(manifest_packages) == len(packages),
        "Lake manifest package count differs from dependency lock",
        errors,
    )
    if isinstance(manifest_packages, list) and isinstance(packages, list):
        locked_revisions = {package["name"]: package["rev"] for package in packages}
        manifest_revisions = {
            package.get("name"): package.get("rev")
            for package in manifest_packages
            if isinstance(package, dict)
        }
        require(
            manifest_revisions == locked_revisions,
            "Lake manifest revisions differ from audited dependency lock",
            errors,
        )

    for artifact in artifacts():
        require(bool(HEX64.fullmatch(str(artifact.get("sha256", "")))), f"{artifact.get('artifact')} has invalid SHA-256", errors)
        require(isinstance(artifact.get("bytes"), int) and artifact["bytes"] > 0, f"{artifact.get('artifact')} has invalid byte length", errors)
        cached = arguments.cache_dir / artifact["artifact"]
        if arguments.require_cache or cached.exists():
            valid, reason = verify(cached, artifact)
            require(valid, f"cache verification failed for {artifact['artifact']}: {reason}", errors)

    base_reference = f"{container['base_image']}@{container['base_manifest_digest']}"
    require(f"FROM {base_reference}" in dockerfile, "Dockerfile base differs from container.lock", errors)
    require("apt-get" not in dockerfile and "curl " not in dockerfile, "Dockerfile contains a network package/download command", errors)
    require("prepare_cache.py" in dockerfile, "Dockerfile does not verify cached artifacts", errors)

    forbidden_floating = ("/latest/", "/nightly/", "refs/heads/main", "refs/heads/master")
    effective_references = [
        str(artifact.get("url", "")) for artifact in artifacts()
    ] + [str(package.get("rev", "")) for package in packages if isinstance(package, dict)]
    effective_references.append(toolchain_name)
    for reference in effective_references:
        require(
            not any(token in reference for token in forbidden_floating),
            f"floating effective reference: {reference}",
            errors,
        )

    result = {
        "schema_version": "1.0.0",
        "status": "PASS" if not errors else "FAIL",
        "require_cache": arguments.require_cache,
        "artifacts": len(artifacts()),
        "dependencies": len(packages) if isinstance(packages, list) else 0,
        "errors": errors,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
