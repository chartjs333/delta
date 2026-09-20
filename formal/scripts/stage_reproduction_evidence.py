#!/usr/bin/env python3
"""Stage the exact generated formal evidence set for artifact transport."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from formal_artifacts import GENERATED_REPORT_OUTPUTS, ROOT


def stage_generated_evidence(root: Path, output: Path) -> list[str]:
    """Copy every fixed generated output, rejecting stale reviews or partial sets."""

    if output.exists():
        raise RuntimeError(f"staging output already exists: {output}")

    review_directory = root / "formal" / "reports" / "reviews"
    stale_reviews = sorted(
        path.relative_to(root).as_posix()
        for path in review_directory.glob("*.json")
        if path.is_file()
    )
    if stale_reviews:
        raise RuntimeError(f"stale review attestations remain: {stale_reviews}")

    relative_paths = sorted(GENERATED_REPORT_OUTPUTS)
    missing = [relative for relative in relative_paths if not (root / relative).is_file()]
    if missing:
        raise RuntimeError(f"generated evidence set is incomplete: {missing}")

    output.mkdir(parents=True)
    for relative in relative_paths:
        destination = output / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / relative, destination)
    return relative_paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    staged = stage_generated_evidence(ROOT, arguments.output.resolve())
    print(json.dumps({"files": staged, "status": "PASS"}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
