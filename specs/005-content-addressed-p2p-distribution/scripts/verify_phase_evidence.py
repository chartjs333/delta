"""Verify feature-005 evidence against its exact source commit and successful CI matrix."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Final, NoReturn

ROOT: Final = Path(__file__).resolve().parents[3]
FEATURE: Final = ROOT / "specs" / "005-content-addressed-p2p-distribution"
REFINEMENT: Final = FEATURE / "evidence/distribution-refinement.json"
NATIVE: Final = FEATURE / "evidence/native-execution.json"
FORMAL_ID: Final = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"


class EvidenceError(RuntimeError):
    pass


def require(condition: bool, code: str, detail: str = "") -> None:
    if not condition:
        raise EvidenceError(f"{code}: {detail}" if detail else code)


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()


def git_bytes(*arguments: str) -> bytes:
    process = subprocess.run(["git", *arguments], cwd=ROOT, check=False, capture_output=True)
    require(process.returncode == 0, "GIT_COMMAND_FAILED", process.stderr.decode(errors="replace"))
    return process.stdout


def git_text(*arguments: str) -> str:
    return git_bytes(*arguments).decode().strip()


def load_canonical(path: Path) -> dict[str, object]:
    raw = path.read_bytes()
    value = json.loads(raw.decode())
    require(isinstance(value, dict), "EVIDENCE_ROOT_INVALID", path.name)
    require(raw == canonical_json_bytes(value) + b"\n", "EVIDENCE_NOT_CANONICAL", path.name)
    return value


def verify() -> dict[str, object]:
    refinement = load_canonical(REFINEMENT)
    native = load_canonical(NATIVE)
    require(refinement.get("status") == native.get("status") == "PASS", "EVIDENCE_NOT_PASS")
    require(
        refinement.get("formal_semantics_id") == native.get("formal_semantics_id") == FORMAL_ID,
        "FORMAL_ID_DIVERGENCE",
    )
    source = refinement.get("source")
    require(isinstance(source, dict) and native.get("source") == source, "SOURCE_DIVERGENCE")
    commit = str(source.get("commit"))
    tree = str(source.get("tree"))
    require(git_text("rev-parse", f"{commit}^{{commit}}") == commit, "SOURCE_COMMIT_INVALID")
    require(git_text("rev-parse", f"{commit}^{{tree}}") == tree, "SOURCE_TREE_INVALID")
    require(
        subprocess.run(["git", "merge-base", "--is-ancestor", commit, "HEAD"], cwd=ROOT).returncode
        == 0,
        "SOURCE_NOT_ANCESTOR",
    )
    formal_diff = git_text(
        "diff",
        "--name-only",
        "bd31efaa6d521bbfc3362ad9aac39455bd29a098",
        commit,
        "--",
        "formal/tla",
        "formal/proofs",
        "formal/schemas",
    )
    require(not formal_diff, "FORMAL_SOURCE_DIFF_PRESENT", formal_diff)
    artifacts = refinement.get("artifacts")
    require(isinstance(artifacts, list) and artifacts, "ARTIFACT_SET_INVALID")
    for item in artifacts:
        require(isinstance(item, dict), "ARTIFACT_INVALID")
        path = str(item.get("path"))
        raw = git_bytes("show", f"{commit}:{path}").replace(b"\r\n", b"\n")
        require(
            hashlib.sha256(raw).hexdigest() == item.get("sha256"), "ARTIFACT_HASH_INVALID", path
        )

    runs = native.get("runs")
    require(isinstance(runs, dict) and len(runs) == 4, "CI_RUN_SET_INVALID")
    jobs = {
        str(job.get("name")): str(job.get("conclusion"))
        for run in runs.values()
        if isinstance(run, dict)
        for job in run.get("jobs", [])
        if isinstance(job, dict)
    }
    required_jobs = {
        "JDK 25 Netty/FFM data plane",
        "JDK 26 Netty/FFM data plane",
        "gcc-14.2.0 native policy C++20/C++23",
        "clang-20.1.8 native policy C++20/C++23",
        "gcc-14.2.0 C++20/C++23",
        "clang-20.1.8 C++20/C++23",
        "JDK 25 runtime descriptor",
        "JDK 26 runtime descriptor",
        "Clang ASan UBSan core runtime ABI fuzz",
        "GCC TSan reactor recovery",
        "python-foundation",
    }
    require(all(jobs.get(name) == "success" for name in required_jobs), "CI_JOB_MATRIX_INCOMPLETE")
    evidence = []
    for path in (REFINEMENT, NATIVE):
        evidence.append(
            {
                "path": str(path.relative_to(ROOT)).replace("\\", "/"),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    return {
        "classification": "REFINEMENT_ONLY",
        "evidence": evidence,
        "formal_semantics_id": FORMAL_ID,
        "phase": "005-phase-evidence",
        "schema_version": "1.0.0",
        "semantic_completeness_claimed": False,
        "source": source,
        "status": "PASS",
    }


def fail(error: Exception) -> NoReturn:
    print(
        canonical_json_bytes(
            {"error": str(error), "phase": "005-phase-evidence", "status": "FAIL"}
        ).decode()
    )
    raise SystemExit(1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check-only", action="store_true")
    parser.parse_args()
    try:
        result = verify()
    except (EvidenceError, OSError, ValueError, json.JSONDecodeError) as error:
        fail(error)
    print(canonical_json_bytes(result).decode())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
