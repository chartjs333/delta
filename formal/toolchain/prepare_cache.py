#!/usr/bin/env python3
"""Download explicitly or verify the pinned formal binary cache."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any


TOOLCHAIN_DIR = Path(__file__).resolve().parent


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def artifacts(component: str = "all") -> list[dict[str, Any]]:
    tla_lock = load_json(TOOLCHAIN_DIR / "tla.lock")
    lean_lock = load_json(TOOLCHAIN_DIR / "lean.lock")
    selected = [
        {**tla_lock["tla_tools"], "component": "tla"},
        {
            **tla_lock["jvm_windows" if os.name == "nt" else "jvm"],
            "component": "tla",
        },
        {
            **lean_lock["lean_windows" if os.name == "nt" else "lean"],
            "component": "lean",
        },
    ]
    return [item for item in selected if component == "all" or item["component"] == component]


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def verify(path: Path, artifact: dict[str, Any]) -> tuple[bool, str]:
    if not path.is_file():
        return False, "missing"
    actual_size = path.stat().st_size
    expected_size = artifact["bytes"]
    if actual_size != expected_size:
        return False, f"size:{actual_size}!={expected_size}"
    actual_hash = digest_file(path)
    expected_hash = artifact["sha256"]
    if actual_hash != expected_hash:
        return False, f"sha256:{actual_hash}!={expected_hash}"
    return True, "verified"


def download(artifact: dict[str, Any], destination: Path) -> None:
    temporary = destination.with_suffix(destination.suffix + ".part")
    if temporary.exists():
        temporary.unlink()
    request = urllib.request.Request(
        artifact["url"], headers={"User-Agent": "DeltaReduce-formal-toolchain/1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response, temporary.open("wb") as output:
            while block := response.read(1024 * 1024):
                output.write(block)
        valid, reason = verify(temporary, artifact)
        if not valid:
            raise ValueError(f"downloaded {artifact['artifact']} failed verification: {reason}")
        os.replace(temporary, destination)
    finally:
        if temporary.exists():
            temporary.unlink()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cache-dir", type=Path, default=TOOLCHAIN_DIR / "cache"
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help="allow network downloads; without this flag verification is offline-only",
    )
    parser.add_argument("--component", choices=("all", "tla", "lean"), default="all")
    arguments = parser.parse_args()
    arguments.cache_dir.mkdir(parents=True, exist_ok=True)

    results: list[dict[str, Any]] = []
    errors: list[str] = []
    for artifact in artifacts(arguments.component):
        destination = arguments.cache_dir / artifact["artifact"]
        valid, reason = verify(destination, artifact)
        if not valid and arguments.download:
            try:
                download(artifact, destination)
                valid, reason = verify(destination, artifact)
            except Exception as error:  # noqa: BLE001 - emitted as deterministic gate failure
                reason = f"download_error:{type(error).__name__}:{error}"
        if not valid:
            errors.append(f"{artifact['artifact']}:{reason}")
        results.append(
            {
                "artifact": artifact["artifact"],
                "sha256": artifact["sha256"],
                "status": "PASS" if valid else "FAIL",
                "reason": reason,
            }
        )

    output = {
        "schema_version": "1.0.0",
        "network_allowed": arguments.download,
        "status": "PASS" if not errors else "FAIL",
        "artifacts": results,
        "errors": errors,
    }
    print(json.dumps(output, sort_keys=True, separators=(",", ":")))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
