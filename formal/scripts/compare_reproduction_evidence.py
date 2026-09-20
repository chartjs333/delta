#!/usr/bin/env python3
"""Compare two complete generated formal evidence bundles byte for byte."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from formal_artifacts import (
    GENERATED_REPORT_OUTPUTS,
    canonical_json_bytes,
    sha256_bytes,
    sha256_file,
)


def _bundle_files(root: Path) -> set[str]:
    return {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file()}


def compare_generated_evidence(left: Path, right: Path) -> dict[str, str]:
    """Require two exact evidence path sets with identical file bytes."""

    expected = set(GENERATED_REPORT_OUTPUTS)
    for label, root in (("left", left), ("right", right)):
        actual = _bundle_files(root)
        if actual != expected:
            missing = sorted(expected - actual)
            unexpected = sorted(actual - expected)
            raise RuntimeError(
                f"{label} evidence path set mismatch: missing={missing}, unexpected={unexpected}"
            )

    hashes = {relative: sha256_file(left / relative) for relative in sorted(expected)}
    mismatches = [
        relative for relative, digest in hashes.items() if sha256_file(right / relative) != digest
    ]
    if mismatches:
        raise RuntimeError(f"evidence bytes differ: {mismatches}")
    return hashes


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--left", type=Path, required=True)
    parser.add_argument("--right", type=Path, required=True)
    arguments = parser.parse_args()
    hashes = compare_generated_evidence(arguments.left.resolve(), arguments.right.resolve())
    bundle_sha256 = sha256_bytes(canonical_json_bytes(hashes))
    print(
        json.dumps(
            {"bundle_sha256": bundle_sha256, "files": len(hashes), "status": "PASS"},
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
