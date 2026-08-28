"""Verify direct-q integration against feature 003 and the accepted formal checker."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Final, NoReturn

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "004-compressed-delta-protocol"
SCRIPT_DIR: Final = FEATURE / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from generate_refinement_fixtures import (  # noqa: E402
    LEGAL_PATH,
    UNSAFE_PATH,
    canonical_json_bytes,
    direct_q_trace,
    unchecked_bound_trace,
)
from verify_native_architecture import verify as verify_architecture  # noqa: E402
from verify_proof_instances import verify as verify_proofs  # noqa: E402

CHECKER: Final = ROOT / "formal" / "scripts" / "check-refinement.py"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"


class RefinementGateError(RuntimeError):
    pass


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise RefinementGateError(f"{code}: {detail}" if detail else code)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def run_checker(path: Path) -> tuple[int, dict[str, object]]:
    with tempfile.TemporaryDirectory(prefix="delta-004-refinement-") as temporary:
        materialized = Path(temporary)
        formal = materialized / "formal"
        for relative in (
            Path("scripts/check-refinement.py"),
            Path("scripts/formal_artifacts.py"),
            Path("schemas/formal-trace.schema.json"),
            Path("schemas/formal-verification-report.schema.json"),
            Path("reports/formal-id-registry.json"),
            Path("proofs/DeltaReduce.lean"),
        ):
            target = formal / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / "formal" / relative, target)
        shutil.copytree(
            ROOT / "formal/tla", formal / "tla", ignore=shutil.ignore_patterns("states")
        )
        shutil.copytree(ROOT / "formal/proofs/DeltaReduce", formal / "proofs/DeltaReduce")
        for source in (materialized / "formal").rglob("*"):
            if source.is_file():
                raw = source.read_bytes()
                if b"\x00" not in raw:
                    source.write_bytes(raw.replace(b"\r\n", b"\n"))
        trace = materialized / "feature004" / path.name
        trace.parent.mkdir(parents=True)
        trace.write_bytes(path.read_bytes().replace(b"\r\n", b"\n"))
        process = subprocess.run(
            [sys.executable, str(materialized / "formal/scripts/check-refinement.py"), str(trace)],
            cwd=materialized,
            check=False,
            capture_output=True,
            text=True,
        )
    output = process.stdout.strip().splitlines()
    require(bool(output), "REFINEMENT_OUTPUT_MISSING", path.name)
    value = json.loads(output[-1])
    require(isinstance(value, dict), "REFINEMENT_OUTPUT_INVALID", path.name)
    return process.returncode, value


def verify() -> dict[str, object]:
    require(
        LEGAL_PATH.read_bytes() == canonical_json_bytes(direct_q_trace()) + b"\n",
        "DIRECT_Q_TRACE_NOT_DETERMINISTIC",
    )
    require(
        UNSAFE_PATH.read_bytes() == canonical_json_bytes(unchecked_bound_trace()) + b"\n",
        "UNSAFE_TRACE_NOT_DETERMINISTIC",
    )
    legal_code, legal = run_checker(LEGAL_PATH)
    require(legal_code == 0 and legal.get("status") == "PASS", "DIRECT_Q_TRACE_REJECTED")
    require(legal.get("terminal_outcome") == "APPLIED", "DIRECT_Q_TRACE_NOT_APPLIED")
    unsafe_code, unsafe = run_checker(UNSAFE_PATH)
    require(unsafe_code != 0 and unsafe.get("status") == "FAIL", "UNSAFE_TRACE_ACCEPTED")
    require(
        "UNCHECKED_ARITHMETIC_ACCEPTED" in str(unsafe.get("error")),
        "UNSAFE_TRACE_WRONG_COUNTEREXAMPLE",
    )
    architecture = verify_architecture()
    proofs = verify_proofs()
    require(architecture["status"] == proofs["status"] == "PASS", "PRIOR_NATIVE_GATE_NOT_PASS")
    direct_fixture = json.loads(
        (ROOT / "delta-protocol/fixtures/004/cross-language/direct-q-100-v1.json").read_text(
            encoding="utf-8"
        )
    )
    require(direct_fixture["eligible_state_id"].startswith("sha256:"), "DIRECT_Q_STATE_ID_INVALID")
    source = (ROOT / "delta-core-cpp/src/fixedpoint/direct_q.cpp").read_text(encoding="utf-8")
    test = (ROOT / "delta-core-cpp/tests/direct_q_test.cpp").read_text(encoding="utf-8")
    require("DELTA_FIXEDPOINT_MUTANT_UNCHECKED_COUNT" in source, "DIRECT_Q_MUTANT_MISSING")
    require("encoded_worker_q_shard" in test, "DISTRIBUTION_DENYLIST_TEST_MISSING")
    paths = [
        CHECKER,
        LEGAL_PATH,
        UNSAFE_PATH,
        ROOT / "CMakeLists.txt",
        ROOT / "delta-core-cpp/src/fixedpoint/direct_q.cpp",
        ROOT / "delta-core-cpp/tests/direct_q_test.cpp",
        ROOT / "delta-core-cpp/tests/prepared_100_test.cpp",
        ROOT / "delta-core-cpp/tests/shards_test.cpp",
        ROOT / "delta-protocol/fixtures/004/cross-language/direct-q-100-v1.json",
        ROOT / "delta-protocol/fixtures/004/cross-language/golden-v1.json",
        ROOT / "delta-worker-python/src/deltatorrent/reference/fixedpoint_encoder.py",
    ]
    return {
        "artifacts": [
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256_file(path),
            }
            for path in sorted(paths)
        ],
        "classification": "REFINEMENT_ONLY",
        "direct_q_100": direct_fixture,
        "formal_semantics_id": FORMAL_ID,
        "legal_trace": legal,
        "phase": "004-direct-q-refinement",
        "production_mutants": [
            "DELTA_FIXEDPOINT_MUTANT_UNCHECKED_COUNT",
            "DELTA_FIXEDPOINT_MUTANT_UNBOUNDED_HEADER",
            "DELTA_FIXEDPOINT_MUTANT_SKIP_CONTEXT",
        ],
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "status": "PASS",
        "tasks": ["T036", "T037", "T038", "T039", "T040"],
        "unsafe_trace": unsafe,
    }


def fail(error: Exception) -> NoReturn:
    print(
        canonical_json_bytes(
            {
                "error": str(error),
                "phase": "004-direct-q-refinement",
                "schema_version": "1.0.0",
                "status": "FAIL",
            }
        ).decode("utf-8")
    )
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.parse_args()
    try:
        result = verify()
    except (
        RefinementGateError,
        KeyError,
        OSError,
        TypeError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        fail(exc)
    print(canonical_json_bytes(result).decode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
