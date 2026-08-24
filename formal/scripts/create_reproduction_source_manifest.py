#!/usr/bin/env python3
"""Create a complete clean-Git source manifest for an offline container."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal" / "scripts"))

from formal_artifacts import sha256_file, write_canonical_json  # noqa: E402


def git(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="strict",
        timeout=30,
    ).stdout.rstrip("\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()

    status = git("status", "--porcelain=v1", "--untracked-files=all")
    if status:
        raise RuntimeError("source tree must be clean before manifest creation")
    tracked = git("ls-files", "-z").split("\0")
    paths = sorted(path for path in tracked if path)
    files = []
    for relative in paths:
        source = ROOT / relative
        if not source.is_file():
            raise RuntimeError(f"tracked source is not a regular file: {relative}")
        files.append({"path": relative, "sha256": sha256_file(source)})

    write_canonical_json(
        arguments.output,
        {
            "schema_version": "1.0.0",
            "source_commit": git("rev-parse", "HEAD"),
            "source_tree": git("rev-parse", "HEAD^{tree}"),
            "source_clean": True,
            "files": files,
        },
    )
    print(arguments.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
