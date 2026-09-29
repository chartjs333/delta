"""Reproduce one R2.3 representation obstruction; no runtime or protocol edits."""

# Existing source-bound repository loaders.
# ruff: noqa: E402
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
BUILD = ROOT / "formal/build/r2-qc-context-probe"
EVIDENCE = ROOT / "formal/proposals/evidence/r2-qc-context"
sys.path.insert(0, str(ROOT / "formal/scripts"))
import generate_native_admission_vectors as native
from formal_artifacts import sha256_file, write_canonical_json
from native_admission_snapshot import decode_flat


def require(value: bool, label: str) -> None:
    if not value:
        raise ValueError(label)


def run() -> None:
    require(native.SOURCE == "60c692f6e391f839829dfc64e93380db54cd507b", "PIN_CHANGED")
    blobs = native.sources()  # Original Git blobs; no conditional guard patch.
    BUILD.mkdir(parents=True, exist_ok=True)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    for path, raw in blobs.items():
        target = (
            BUILD / "include" / path.split("/include/")[1]
            if "/include/" in path
            else BUILD / Path(path).name
        )
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        require(target.read_bytes() == raw, "SOURCE_COPY")
    probe = HERE / "qc_context_probe.cpp"
    (BUILD / "probe.cpp").write_bytes(probe.read_bytes())
    command = (
        '@echo off\ncall "C:/Program Files (x86)/Microsoft Visual Studio/2019/BuildTools/'
        'VC/Auxiliary/Build/vcvars64.bat" >nul\nif errorlevel 1 exit /b 1\n'
        "cl /Bv /std:c++20 /EHsc /W4 /WX /Iinclude probe.cpp "
        + " ".join(Path(p).name for p in native.UNITS)
        + " /Fe:probe.exe\nexit /b %errorlevel%\n"
    )
    (BUILD / "compile.cmd").write_text(command, encoding="utf-8", newline="\r\n")
    process = subprocess.run(
        ["cmd", "/d", "/c", str(BUILD / "compile.cmd")], cwd=BUILD, capture_output=True
    )
    log = (process.stdout + process.stderr).decode("utf-8")
    (EVIDENCE / "compile.txt").write_text(
        "\n".join(line.rstrip() for line in log.splitlines()).rstrip() + "\n",
        encoding="utf-8",
        newline="\n",
    )
    require(process.returncode == 0, "COMPILER_FAILURE")
    compiler = re.search(r"Optimizing Compiler Version ([0-9.]+) for x64", log)
    require(compiler is not None, "COMPILER_IDENTITY")
    observed = json.loads(subprocess.check_output([str(BUILD / "probe.exe")], cwd=BUILD))
    require(observed["policy"] == observed["vote1"] == observed["vote2"] == "ACCEPT", "ADMISSION")
    require(observed["journal_size"] == 3 and observed["sequences"] == [2, 3], "JOURNAL")
    require(observed["isc_qc1"] != observed["isc_qc2"], "DISTINCT_QCS")
    require(observed["ec_context1"] != observed["ec_context2"], "DISTINCT_NATIVE_CONTEXTS")
    votes = [decode_flat(bytes.fromhex(raw), 3) for raw in observed["ec_vote_hex"]]
    prior = [decode_flat(bytes.fromhex(raw), 3) for raw in observed["prior_isc_vote_hex"]]
    require(len(prior) == 4 and len(votes) == 2, "ORIGINAL_VOTES")
    require({v["validator_id"] for v in prior} == {f"validator-{i}" for i in range(1, 5)}, "ACTORS")
    require(all(v["body_hash"] == observed["isc_body"] for v in prior), "PRIOR_COMMON_BODY")
    require(all(v["validator_id"] == "validator-1" for v in votes), "SAME_HONEST_ACTOR")
    for key in ("validator_epoch_id", "height", "view", "round_id"):
        require(votes[0][key] == votes[1][key] == prior[0][key], "SAME_ORIGINAL_CONTEXT")

    # Necessary public predicate fragments, source-pinned below. This is a
    # source-reviewed algebraic obstruction, NOT a new full-state/TLC checker.
    public_paths = [
        "formal/tla/DeltaReduceCertificates.tla",
        "formal/tla/DeltaReduceQuorums.tla",
        "formal/tla/DeltaReduceFailures.tla",
        "formal/tla/DeltaReduceTypes.tla",
        "formal/proofs/DeltaReduce/PublicPlanningBody.lean",
        "formal/proofs/DeltaReduce/PublicAuthority.lean",
        "specs/000-formal-tla-spec/candidate-contract.md",
        "specs/000-formal-tla-spec/accepted-residual-20260928.md",
    ]
    cert = (ROOT / public_paths[0]).read_text(encoding="utf-8")
    require('envelope == VoteEnvelope(validator, "EC", body.isc, body)' in cert, "PUBLIC_CONTEXT")
    require("/\\ vote.body.isc = body.isc" in cert, "PUBLIC_CONFLICT_CONTEXT")
    require("/\\ vote.body # body" in cert, "PUBLIC_CONFLICT_BODY")
    require("/\\ vote \\notin ecVotes" in cert, "PUBLIC_FRESHNESS")
    public_cases = [
        {
            "projection": "distinct_EC_bodies_with_same_ISC_body",
            "honest_actor_EC_body_count": 2,
            "CertificateVoteUniqueness": False,
            "second_VoteEC_enabled": False,
        },
        {
            "projection": "equal_EC_bodies_with_same_ISC_body",
            "original_local_journal_count": 3,
            "projected_local_durable_vote_set_count": 2,
            "DurableSequenceExact_if_original_count_retained": False,
            "second_VoteEC_enabled": False,
        },
    ]
    import hashlib

    source_hashes = {p: hashlib.sha256(raw).hexdigest() for p, raw in sorted(blobs.items())}
    local_paths = [HERE / "check_qc_context.py", probe, *[ROOT / p for p in public_paths]]
    result = {
        "status": "R2_OPEN_ARCHITECTURAL_CONTEXT_OBSTRUCTION",
        "completed_at_utc": datetime.now(UTC).isoformat(),
        "source_commit": native.SOURCE,
        "source_sha256": source_hashes,
        "local_sources": [
            {"path": p.relative_to(ROOT).as_posix(), "sha256": sha256_file(p)} for p in local_paths
        ],
        "compiler": compiler[1],
        "compiler_flags": "/Bv /std:c++20 /EHsc /W4 /WX",
        "unmodified_translation_units": native.UNITS,
        "native_observed": observed,
        "quorum_threshold": 3,
        "isc_signer_sets": [[1, 2, 3], [1, 2, 4]],
        "public_source_reviewed_case_split": public_cases,
        "native_admission_and_in_memory_vote_journal_executed": True,
        "native_runtime_wal_execution": False,
        "authenticated_export_or_reachable_native_snapshot_proved": False,
        "cryptographic_signatures_executed": False,
        "full_public_checker_or_TLC_executed": False,
        "necessary_missing_binding": (
            "Native parent-QC-dependent context separation must not permit multiple fresh "
            "votes for the same actor and computed public parent-body context. The existing "
            "native policy admits the witness; assuming its complete formal-state projection "
            "would assume the R2 obligation. No total preserving map covers this admitted "
            "snapshot and journal under the frozen public uniqueness and sequence predicates."
        ),
        "production_init_next_changed": False,
        "certificate_semantics_changed": False,
        "wal_identity_changed": False,
        "r2_1_and_r2_2_reopened": False,
        "r3_started": False,
        "formal_go": False,
    }
    write_canonical_json(EVIDENCE / "counterexample.json", result)
    print(json.dumps({"status": result["status"], "native_policy": "ACCEPT", "journal_size": 3}))


if __name__ == "__main__":
    run()
