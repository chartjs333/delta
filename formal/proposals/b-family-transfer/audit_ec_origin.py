"""T047/T053: source evidence for the first-EC producing-history dependency.

This is a bounded source audit, not a reachable counterexample or a proof that
no other contract could exist. It neither supplies nor authorizes a producer.
"""

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "formal/proposals/evidence/ec-origin-boundary"
NATIVE = "60c692f6e391f839829dfc64e93380db54cd507b"
AUTHORITY = "bb9fce957dae329701a8cd473a7148e198e1ca12"
BASE = "4dea988bae971c6b05f004319764a220cd9e4717"


def blob(ref, path):
    return subprocess.check_output(["git", "cat-file", "blob", ref + ":" + path], cwd=ROOT)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", NATIVE], cwd=ROOT, text=True, encoding="utf8"
    ).splitlines()
    sources, mentions = {}, []
    for path in files:
        if (
            not path.startswith(("delta-core-cpp/", "delta-runtime-cpp/", "delta-ffi/"))
            or not any(part in {"src", "include"} for part in Path(path).parts)
            or Path(path).suffix not in {".cpp", ".hpp", ".h"}
        ):
            continue
        raw = blob(NATIVE, path)
        sources[NATIVE + ":" + path] = sha(raw)
        for number, line in enumerate(raw.decode("utf8").splitlines(), 1):
            if re.search(r"\b(eligibility_certificates|finalized_eligibility_ids)\b", line):
                mentions.append({"path": path, "line": number, "text": line.strip()})

    # Check every source occurrence's reviewed owner category, rather than
    # interpreting a failed grep for one function name as absence evidence.
    categories = {
        "delta-core-cpp/include/delta/core/consensus.hpp": "typed carrier declarations",
        "delta-core-cpp/src/certificates/vote_admission.cpp": "read-only validation and lookup",
        "delta-runtime-cpp/src/vote_codec.cpp": "serialization or decoding supplied snapshot",
    }
    unexpected = sorted({m["path"] for m in mentions} - set(categories))
    if unexpected:
        raise RuntimeError("EC source owner classification needs review: " + repr(unexpected))

    spans = [
        (NATIVE, "delta-runtime-cpp/include/delta/runtime/runtime.hpp", 67, 83),
        (NATIVE, "delta-runtime-cpp/include/delta/runtime/runtime.hpp", 105, 143),
        (NATIVE, "delta-runtime-cpp/src/runtime.cpp", 108, 136),
        (NATIVE, "delta-core-cpp/src/consensus.cpp", 543, 588),
        (NATIVE, "delta-core-cpp/src/certificates/vote_admission.cpp", 530, 558),
        (NATIVE, "delta-runtime-cpp/src/vote_codec.cpp", 883, 892),
        (AUTHORITY, "docs/adr/0015-non-isc-authority-binding-v1.md", 13, 29),
        (AUTHORITY, "docs/adr/0015-non-isc-authority-binding-v1.md", 216, 235),
        (AUTHORITY, "docs/adr/0015-non-isc-authority-binding-v1.md", 289, 306),
        (BASE, "docs/adr/0013-snapshot-provenance-profile-v1.md", 163, 192),
        (BASE, "docs/adr/0014-isc-finalization-wal-capsule-v1.md", 342, 347),
        (BASE, "formal/tla/DeltaReduceCertificates.tla", 359, 374),
        (BASE, "formal/proposals/b-family-transfer/ProfileIscFinalization.lean", 153, 200),
        (BASE, "formal/proposals/b-family-transfer/ProfileCertificateVotes.lean", 1, 35),
    ]
    excerpts = []
    for ref, path, start, end in spans:
        raw = blob(ref, path)
        sources[ref + ":" + path] = sha(raw)
        excerpts.append(
            {
                "commit": ref,
                "path": path,
                "start": start,
                "end": end,
                "lines": raw.decode("utf8").splitlines()[start - 1 : end],
            }
        )

    result = {
        "task_ids": ["T047", "T053", "ISC-S16-D01"],
        "assignment_id": "13069d7e-a148-475a-bd49-9885bf2f283d",
        "scope_revision": 15,
        "audit_script_sha256": sha(Path(__file__).read_bytes()),
        "status": "UNRESOLVED_NATIVE_PRODUCER_SELECTION",
        "r2_3": "OPEN",
        "formal_go": False,
        "native_source_files_reviewed": sum(k.startswith(NATIVE + ":") for k in sources),
        "sources": sources,
        "ec_inventory_occurrences": mentions,
        "owner_classification": categories,
        "excerpts": excerpts,
        "required_edge": {
            "before": "Verified prior native policy; first EC not finalized for its original ISC",
            "inputs": (
                "Original EC body, ISC/seed/norm dependencies, authenticated original "
                "received votes at the exact cut"
            ),
            "after": (
                "Computed exact original EC witness and eligibility_certificates/"
                "finalized_eligibility_ids delta, with all other fields retained"
            ),
            "obligations": (
                "Original context, first-finalization/retry behavior, witness/ID selection "
                "and original journal/source association"
            ),
        },
        "finding": (
            "N supplies EC carrier/codec/validator and an immutable startup vote policy, "
            "not the requested prior-state/received-cut producer. Selected W1 changes only ISC "
            "witness/finalized fields. SIG-NON-ISC authenticates original votes/certificates "
            "and explicitly adds no producer. Scope15 selects U/R/P units, not an EC producer."
        ),
        "excluded_substitutes": [
            "Treating a supplied valid EC or a prefilled policy as a producing event",
            "Using public FinalizeEC/Next success as native origin",
            "Assuming the final source/public relation or rejecting all nonempty EC histories",
            "Extending ISC W1 to other kinds without a selected native contract",
        ],
        "limits": [
            "No production-reachable forged history or complete Profile-v1 counterexample claimed",
            "No impossibility claim for all potential external native contracts",
            "Other unfinished source and totality obligations remain; "
            "this does not certify their sufficiency",
            "Source inspection is not kernel proof or independent attestation",
        ],
    }
    (OUT / "source-audit.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf8", newline="\n"
    )
    print(json.dumps({k: result[k] for k in ("status", "native_source_files_reviewed")}))


if __name__ == "__main__":
    main()
