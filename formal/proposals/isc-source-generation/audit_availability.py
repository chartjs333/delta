"""T047/T053: reproduce a source API boundary, not a production attack trace.

This reads immutable original sources. It neither chooses a storage signature
protocol nor defines a replacement availability admission predicate.
"""

import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NATIVE = "60c692f6e391f839829dfc64e93380db54cd507b"
PROFILE = "26eb02d0632435c9aa0d8ef44eb496b6fa73dd13"
CONTRACT = "bb9fce957dae329701a8cd473a7148e198e1ca12"
OUT = ROOT / "formal/proposals/evidence/non-isc-source-v1"


def read(commit, path):
    raw = subprocess.check_output(["git", "show", f"{commit}:{path}"], cwd=ROOT)
    return raw, {
        "commit": commit,
        "path": path,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }


def main():
    sources = {}
    evidence = []
    for commit, path in (
        (NATIVE, "delta-core-cpp/include/delta/core/consensus.hpp"),
        (NATIVE, "delta-core-cpp/src/consensus.cpp"),
        (NATIVE, "delta-core-cpp/tests/consensus_test.cpp"),
        (NATIVE, "specs/003-bft-round-state-machine/spec.md"),
        (NATIVE, "delta-protocol/registry.json"),
        (NATIVE, "delta-protocol/schemas/003/protocol-types-v1.json"),
        (
            NATIVE,
            "delta-node-java/src/main/java/io/deltareduce/node/certificates/"
            "AuthenticatedCertificateTransport.java",
        ),
        (PROFILE, "formal/tla/DeltaReduceAvailability.tla"),
        (PROFILE, "docs/adr/0013-snapshot-provenance-profile-v1.md"),
        (CONTRACT, "docs/adr/0015-non-isc-authority-binding-v1.md"),
    ):
        raw, record = read(commit, path)
        sources[path] = raw.decode("utf8")
        evidence.append(record)
    header = sources["delta-core-cpp/include/delta/core/consensus.hpp"]
    struct = header.split("struct AvailabilityProof {", 1)[1].split("};", 1)[0]
    fields = re.findall(r"std::(?:string|vector<std::string>|uint32_t)\s+(\w+);", struct)
    expected = [
        "ticket_id",
        "commitment_id",
        "certificate_id",
        "covered_leaf_ids",
        "attester_ids",
        "threshold",
    ]
    assert fields == expected, fields
    native = sources["delta-core-cpp/src/consensus.cpp"]
    admission = native.split("Disposition InputLedger::record_availability(", 1)[1]
    admission = admission.split("const std::vector<FrozenInput>& InputLedger::freeze", 1)[0]
    assert "proof.covered_leaf_ids == required_leaf_ids" in admission
    assert "proof.threshold == required_threshold" in admission
    assert "require_content_id(proof.certificate_id)" in admission
    assert "proof.attester_ids.size() >= required_threshold" in admission
    assert "commitment->commitment_id == proof.commitment_id" in admission
    assert not re.search(r"signature|public_key|retention_epoch|byte_length", admission)
    tla = sources["formal/tla/DeltaReduceAvailability.tla"]
    assert "location \\in availableArtifacts" in tla
    assert "Cardinality(AvailableAttestersFor(ticket, content, shard))" in tla
    spec = sources["specs/003-bft-round-state-machine/spec.md"]
    assert "exact shard content IDs, lengths and retention epoch" in spec
    transport = sources[
        "delta-node-java/src/main/java/io/deltareduce/node/certificates/"
        "AuthenticatedCertificateTransport.java"
    ]
    assert "boolean authenticate(String peerId, byte[] opaqueBytes" in transport

    # An indistinguishability witness at the actual six-field API, not a new
    # source wire type. The absent information is deliberately NOT supplied to
    # the function or made an assumed 'valid' bit in an R2 theorem.
    proof = {
        "ticket_id": "diagnostic-ticket",
        "commitment_id": "sha256:" + "1" * 64,
        "certificate_id": "sha256:" + "2" * 64,
        "covered_leaf_ids": ["sha256:" + "3" * 64],
        "attester_ids": ["storage-1", "storage-2", "storage-3"],
        "threshold": 3,
    }
    canonical = json.dumps(proof, sort_keys=True, separators=(",", ":")).encode()
    report = {
        "task_id": "ISC-S16-D01",
        "scope_revision": 5,
        "result": "MISSING_STORAGE_ATTESTATION_SOURCE_BINDING",
        "formal_status": "NO_GO",
        "r2_3": "OPEN",
        "sources": evidence,
        "original_api_fields": fields,
        "minimal_api_witness": {
            "proof": proof,
            "same_api_arguments_sha256": hashlib.sha256(canonical).hexdigest(),
            "world_a": (
                "Original authorized storage attestations exist for the exact leaves, "
                "lengths and retention epoch."
            ),
            "world_b": (
                "Those original attestations are absent or refer to another retention epoch; "
                "the six API fields are identical."
            ),
            "observation": (
                "record_availability receives identical arguments and cannot distinguish "
                "these worlds. certificate_id is checked for syntax, not recomputed "
                "from authenticated AC bytes."
            ),
        },
        "not_claimed": [
            "No production-reachable forged snapshot or exploit is established.",
            "No native executable was changed or newly invoked by this audit.",
            "The two external worlds are an API insufficiency argument, not normative AC vectors.",
            "Faithful retained bytes do not alone establish the missing storage authority binding.",
            "Validator SIG-ISC/NSG1 and transport authentication do not authorize storage peers.",
        ],
        "required_decision": (
            "Resolve the original storage AvailabilityAttestation/AC exact source-authority/"
            "codec binding; do not invent it or transfer validator keys/roles."
        ),
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "availability-boundary.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf8", newline="\n"
    )
    print(report["result"])


if __name__ == "__main__":
    main()
