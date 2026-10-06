"""T047/T053: immutable storage producer audit; not a new source verifier.

The diagnostic evaluates the cardinalities in the existing TLA guards. It is
neither a TLC run nor evidence of an end-to-end production-reachable attack.
No codec, producer rule, protocol predicate or admission behavior is added.
"""

import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
NATIVE = "60c692f6e391f839829dfc64e93380db54cd507b"
PROFILE = "26eb02d0632435c9aa0d8ef44eb496b6fa73dd13"
CONTRACT = "1438fa3d78ec99291475cf4660fd8c190ac01bb3"
REFERENCE = "e766ef98748504779a9a88d06ee3760594c4184d"
OUT = ROOT / "formal/proposals/evidence/storage-producer-boundary.json"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def main():
    records = []
    texts = {}
    sources = [
        (NATIVE, "formal/tla/DeltaReduceAvailability.tla"),
        (NATIVE, "delta-core-cpp/include/delta/core/consensus.hpp"),
        (NATIVE, "delta-core-cpp/include/delta/core/protocol.hpp"),
        (NATIVE, "delta-core-cpp/src/consensus.cpp"),
        (NATIVE, "delta-core-cpp/src/transition.cpp"),
        (NATIVE, "delta-core-cpp/tests/prepared_100_test.cpp"),
        (NATIVE, "delta-runtime-cpp/include/delta/runtime/runtime.hpp"),
        (NATIVE, "delta-runtime-cpp/include/delta/runtime/certificate_runtime.hpp"),
        (
            NATIVE,
            "delta-node-java/src/main/java/io/deltareduce/node/apply/ArtifactEffectAdapter.java",
        ),
        (
            NATIVE,
            "delta-node-java/src/main/java/io/deltareduce/node/certificates/"
            "AuthenticatedCertificateTransport.java",
        ),
        (
            NATIVE,
            "delta-worker-python/src/deltatorrent/artifacts/filesystem.py",
        ),
        (NATIVE, "specs/003-bft-round-state-machine/spec.md"),
        (NATIVE, "specs/003-bft-round-state-machine/formal-refinement.md"),
        (PROFILE, "docs/adr/0013-snapshot-provenance-profile-v1.md"),
        (CONTRACT, "docs/adr/0016-storage-availability-source-binding-v1.md"),
        (REFERENCE, "formal/reference/isc_source/README.md"),
    ]
    for commit, path in sources:
        raw = git("show", f"{commit}:{path}")
        records.append({"commit": commit, "path": path, "sha256": hashlib.sha256(raw).hexdigest()})
        texts[path] = raw.decode("utf8")

    tla = texts["formal/tla/DeltaReduceAvailability.tla"]
    for snippet in (
        "ArtifactLocation(storage, content, shard) \\in availableArtifacts",
        "Cardinality(AvailableAttestersFor(ticket, content, shard))",
        "location \\in availableArtifacts",
        "/\\ HasCompleteAvailability(ticket, content)",
        "availableArtifacts' = availableArtifacts \\ {location}",
    ):
        assert snippet in tla, snippet
    admission = (
        texts["delta-core-cpp/src/consensus.cpp"]
        .split("Disposition InputLedger::record_availability(", 1)[1]
        .split("const std::vector<FrozenInput>& InputLedger::freeze", 1)[0]
    )
    assert "proof.covered_leaf_ids == required_leaf_ids" in admission
    assert "proof.attester_ids.size() >= required_threshold" in admission
    assert "availabilities_.insert(found, std::move(proof))" in admission
    assert "availableArtifacts" not in admission
    transition = (
        texts["delta-core-cpp/src/transition.cpp"]
        .split('command.command_kind == "ACCEPT_AVAILABILITY"', 1)[1]
        .split('command.command_kind == "FINALIZE_INPUT_FREEZE"', 1)[0]
    )
    assert "state.available_ticket_count < state.committed_ticket_count" in transition
    assert "++state.available_ticket_count" in transition
    assert "InputLedger" not in transition
    assert "command.body_hash" not in transition

    # Inventory the exact source pin, including all call sites. A downstream
    # external producer is not disproved by grep; none is supplied by this pin.
    paths = git("ls-tree", "-r", "--name-only", NATIVE).decode().splitlines()
    roots = (
        "delta-core-cpp/",
        "delta-runtime-cpp/",
        "delta-ffi/",
        "delta-node-java/",
        "delta-worker-python/",
    )
    code = [
        p
        for p in paths
        if p.startswith(roots) and p.endswith((".cpp", ".hpp", ".h", ".java", ".py"))
    ]
    calls = git("grep", "-n", "record_availability", NATIVE, "--", *code).decode()
    call_lines = calls.splitlines()
    non_test_calls = [p for p in call_lines if "/tests/" not in p]
    assert len(non_test_calls) == 2, non_test_calls
    assert all("consensus.hpp:" in p or "consensus.cpp:" in p for p in non_test_calls)

    # One selected original leaf. Other leaves, if any, retain complete
    # coverage in both cuts. The original threshold is 3; storage-4 is unused.
    attesters = {"storage-1", "storage-2", "storage-3"}
    before = set(attesters)
    after = before - {"storage-3"}
    threshold = 3
    before_guard = len(attesters & before) >= threshold
    after_guard = len(attesters & after) >= threshold
    assert before_guard and not after_guard
    assert len(attesters) >= threshold  # Historical signatures did not vanish.

    report = {
        "task_ids": ["T047", "T053"],
        "assignment_id": "b52fcd71-2a71-456e-86a0-f5c1691f58c9",
        "effective_scope_revision": 7,
        "ack_id": "scope-ack-9946f552dad9e7696d4b29ea5d9d240f",
        "decision_id": "scope-decision-614a7db8512f59e36720131917827d4c",
        "result": "MISSING_STORAGE_PRODUCING_HISTORY_BINDING",
        "formal_status": "NO_GO",
        "r2_3": "OPEN",
        "source_hash_rule": "Exact immutable Git blob bytes; no normalization.",
        "sources": records,
        "native_call_inventory": {
            "searched_code_file_count": len(code),
            "record_availability_occurrences": call_lines,
            "non_test_occurrences_are_declaration_and_definition_only": True,
        },
        "guard_diagnostic": {
            "kind": "Existing-guard evaluation, not a TLC/native execution",
            "preconditions": (
                "Existing committed ticket/content, CertificateProgressOpen, "
                "availability actions/faults enabled, content not yet frozen; "
                "one selected original leaf, others fully covered in both cuts."
            ),
            "common_prefix": [
                "UploadArtifact and AttestAvailability for storage-1,2,3",
                "Retain the same original authentic attestation statements",
            ],
            "cut_a": {
                "available_attesters": sorted(before),
                "HasAttestationCoverage": True,
                "HasCompleteAvailability": before_guard,
                "FinalizeAvailability_enabled_given_other_guards": before_guard,
            },
            "cut_b": {
                "additional_original_action": "LoseArtifactPreFreeze(storage-3,content,leaf)",
                "available_attesters": sorted(after),
                "HasAttestationCoverage": True,
                "HasCompleteAvailability": after_guard,
                "FinalizeAvailability_enabled_given_other_guards": after_guard,
            },
            "unchanged": (
                "Original attestation bytes/IDs, signatures, signer identities, "
                "candidate D/ac and six AvailabilityProof fields can stay equal. "
                "No concrete SAG1 bytes or qualified AC are manufactured here."
            ),
            "negative_control": (
                "Finalize at cut_a THEN lose a shard: the existing finalized AC "
                "remains in lineage; this audit does not demand deletion or "
                "current availability forever after finalization."
            ),
        },
        "missing_link": (
            "An independently defined original native storage producer/observation "
            "and complete retained event binding sufficient to determine per-location "
            "availability at the original attestation/finalization cuts. The pinned "
            "coarse transition, six-field ledger, local artifact I/O and opaque "
            "transport do not supply that original event history."
        ),
        "limitations": [
            "No claim that a forbidden FinalizeAvailability is production reachable.",
            "No refutation of R2 totality for an independently valid full source bundle.",
            (
                "No claim that no external producer can exist; an immutable "
                "applicable contract/evidence is required."
            ),
            (
                "No weakened source domain, new producer/observer/authority "
                "assumption or changed Init/Next."
            ),
            "No storage implementation, production change, Lean proof or semantics ID assigned.",
            (
                "Scope7 approves authentication bytes; it expressly does not "
                "discharge this source-origin obligation."
            ),
            (
                "Bounds/full R2 composition remain unqualified; this audit "
                "stops at the first mandatory source gate."
            ),
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf8", newline="\n")
    print(report["result"])


if __name__ == "__main__":
    main()
