"""Reproduce the concrete non-ISC authority boundary; not a reachability proof."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from formal.reference.isc_crypto.codec import CodecError, decode_vote  # noqa: E402

PIN = "60c692f6e391f839829dfc64e93380db54cd507b"
APPROVED = "26eb02d0632435c9aa0d8ef44eb496b6fa73dd13"


def main():
    sources = []
    for commit, path in (
        (PIN, "delta-core-cpp/include/delta/certificates/verifier.hpp"),
        (PIN, "delta-core-cpp/src/certificates/verifier.cpp"),
        (PIN, "delta-core-cpp/src/certificates/vote_admission.cpp"),
        (PIN, "delta-runtime-cpp/src/certificate_runtime.cpp"),
        (APPROVED, "docs/adr/0013-snapshot-provenance-profile-v1.md"),
        (APPROVED, "docs/adr/0014-isc-production-contract-amendment-v1.md"),
        (APPROVED, "specs/008-certificates-and-consensus/spec.md"),
    ):
        raw = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)
        sources.append({"commit": commit, "path": path, "sha256": hashlib.sha256(raw).hexdigest()})
    # A well-framed 12-field diagnostic probe, deliberately NOT a proposed
    # authoritative APPLY encoding. Rejection must be dispatch, not bad framing.
    fields = {
        "body_hash": "sha256:" + "1" * 64,
        "context_id": "sha256:" + "2" * 64,
        "durable_sequence": "2",
        "formal_semantics_id": "sha256:" + "3" * 64,
        "height": "1",
        "kind": "APPLY",
        "round_id": "diagnostic-round",
        "schema_version": "2.0.0",
        "type_name": "VOTE",
        "validator_epoch_id": "sha256:" + "4" * 64,
        "validator_id": "validator-1",
        "view": "0",
    }

    def text(value):
        raw = value.encode("ascii")
        return b"\x21" + len(raw).to_bytes(4, "big") + raw

    payload = b"\x31" + len(fields).to_bytes(4, "big")
    payload += b"".join(text(key) + text(fields[key]) for key in sorted(fields))
    raw = b"DRC1\x01\x00\x00\x03" + len(payload).to_bytes(4, "big") + payload
    try:
        decode_vote(raw)
    except CodecError as error:
        outcome = str(error)
        assert outcome == "vote profile dispatch mismatch", outcome
    else:
        raise AssertionError("ISC decoder unexpectedly accepted APPLY")
    report = {
        "task_id": "ISC-S16-D01",
        "scope_revision": 3,
        "status": "MISSING_NON_ISC_SIGNATURE_BINDING",
        "formal_status": "NO_GO",
        "r2_3": "OPEN",
        "sources": sources,
        "dispatch_probe": {
            "sha256": hashlib.sha256(raw).hexdigest(),
            "bytes": len(raw),
            "outcome": outcome,
            "is_normative_apply_encoding": False,
        },
        "argument": (
            "Pinned verify_apply takes typed objects and IDs, not signature evidence/keys; "
            "equal arguments cannot distinguish missing from genuine signatures. "
            "Approved ISC codec rejects non-ISC kinds."
        ),
        "limits": [
            "Source/API insufficiency, not a production-reachable forged snapshot.",
            "No new non-ISC signed bytes or authentication assumptions selected.",
            "No runtime, legacy identity, profile trust or production model change.",
        ],
        "audit_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    path = ROOT / "formal/proposals/evidence/isc-source-v2/authority-boundary.json"
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(report["status"])


if __name__ == "__main__":
    main()
