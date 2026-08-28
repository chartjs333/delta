"""Materialize deterministic feature-005 refinement evidence for one exact source commit."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "005-content-addressed-p2p-distribution"
SCRIPT_DIR: Final = FEATURE / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_refinement_traces import canonical_json_bytes  # noqa: E402
from verify_distribution_refinement import verify  # noqa: E402

OUTPUT: Final = FEATURE / "evidence/distribution-refinement.json"


def git_text(*arguments: str) -> str:
    return subprocess.run(
        ["git", *arguments], cwd=ROOT, check=True, capture_output=True, text=True
    ).stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    if not arguments.write:
        parser.error("--write is required")
    source_commit = git_text("rev-parse", arguments.source_commit)
    if source_commit != git_text("rev-parse", "HEAD"):
        parser.error("evidence must be materialized at the exact source HEAD")
    result = verify()
    if result.get("status") != "PASS":
        raise RuntimeError("distribution refinement gate did not pass")
    result["source"] = {
        "commit": source_commit,
        "tree": git_text("rev-parse", f"{source_commit}^{{tree}}"),
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_bytes(canonical_json_bytes(result) + b"\n")
    print(
        canonical_json_bytes(
            {"output": str(OUTPUT.relative_to(ROOT)), "source": result["source"], "status": "PASS"}
        ).decode()
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
