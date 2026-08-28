"""Materialize deterministic feature-004 gate results for one exact source commit."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Final

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "004-compressed-delta-protocol"
SCRIPT_DIR: Final = FEATURE / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_refinement_fixtures import canonical_json_bytes  # noqa: E402
from verify_direct_q_refinement import verify as verify_refinement  # noqa: E402
from verify_native_architecture import verify as verify_architecture  # noqa: E402
from verify_proof_instances import verify as verify_proofs  # noqa: E402
from verify_protocol_contracts import verify_all as verify_contracts  # noqa: E402

OUTPUTS: Final = {
    "protocol-contracts-final.json": verify_contracts,
    "native-architecture.json": verify_architecture,
    "proof-instances.json": verify_proofs,
    "direct-q-refinement.json": verify_refinement,
}


def git_text(*arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments], cwd=ROOT, check=True, capture_output=True, text=True
    )
    return process.stdout.strip()


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
    source = {
        "commit": source_commit,
        "tree": git_text("rev-parse", f"{source_commit}^{{tree}}"),
    }
    for name, verifier in OUTPUTS.items():
        result = verifier()
        if result.get("status") != "PASS":
            raise RuntimeError(f"gate did not pass: {name}")
        result["source"] = source
        output = FEATURE / "evidence" / name
        output.write_bytes(canonical_json_bytes(result) + b"\n")
    print(
        canonical_json_bytes(
            {
                "outputs": sorted(OUTPUTS),
                "source": source,
                "status": "PASS",
            }
        ).decode("utf-8")
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
