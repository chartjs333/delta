"""Full per-actor envelope-prefix examples; not full native trace refinement."""

import hashlib
import importlib.util
from pathlib import Path

from generate_native_vote_vectors import byte_list, content_id, string
from native_durability_witness import envelope, journal_root, n
from native_trace_witness import NativeEvidence

ROOT = Path(__file__).resolve().parents[2]
TRACE = ROOT / "formal/fixtures/traces/legal/normal-apply.json"
SOURCE = ROOT / "formal/fixtures/traces/native/normal-apply.json"
TARGET = ROOT / "formal/proofs/DeltaReduce/PublicJournalVectors.lean"
EVIDENCE = ROOT / "formal/proposals/public-journal-vectors.json"
spec = importlib.util.spec_from_file_location(
    "public_journal_refinement", ROOT / "formal/scripts/check-refinement.py"
)
assert spec and spec.loader
refinement = importlib.util.module_from_spec(spec)
spec.loader.exec_module(refinement)


def generate(trace_path=TRACE, source=SOURCE, target=TARGET, evidence_path=EVIDENCE):
    trace = n.decode(trace_path.read_bytes())
    native = NativeEvidence(source, hashlib.sha256(source.read_bytes()).hexdigest())
    # Validate the whole trace, not only the three arithmetic observations.
    checked = refinement.check_trace(trace_path, native)
    events = [
        e
        for e in trace["events"]
        if e["actor_id"] == "validator-1"
        and e["action_id"].endswith("-VOTE")
        and e["outcome"] == "ACCEPTED"
    ]
    n.require(
        len(events) == 8 and [e["durable_sequence"] for e in events] == list(range(1, 9)),
        "PUBLIC_JOURNAL_SEQUENCE_SCOPE",
    )
    kinds = {
        "ACT-CONFIG-VOTE": "config",
        "ACT-ISC-VOTE": "isc",
        "ACT-EC-VOTE": "ec",
        "ACT-APC-VOTE": "apc",
        "ACT-PARAM-VOTE": "parameter",
        "ACT-ROOT-VOTE": "root",
        "ACT-APPLY-VOTE": "apply",
        "ACT-VIEW-VOTE": "view",
        "ACT-ABORT-VOTE": "abort",
    }
    lines = [
        "import DeltaReduce.PublicJournal",
        "import DeltaReduce.NativeReplayVectors",
        "",
        "/-! All eight original validator-1 vote slots; arithmetic sequences 5/6/8.",
        "Other native receipts are unprojected (none), not fabricated empty bytes.",
        "Other-action/QC/metadata trust and SHA samples are finite/synthetic. -/",
        "namespace DeltaReduce.PublicJournalVectors",
        "open NativeBinding NativeGraphVectors NativeVoteVectors",
        "open PublicJournal",
        "set_option maxRecDepth 1000000",
        "set_option maxHeartbeats 0",
    ]
    hashes, ids, roots = {}, [], []
    other = []
    for i, event in enumerate(events):
        raw = n.canonical(envelope(event))
        preimage = b"deltareduce.000.arithmetic-binding.draft1\x00" + raw
        hashes[preimage] = hashlib.sha256(preimage).digest()
        ids.append(n.digest(raw))
        arithmetic = event["action_id"] in {"ACT-PARAM-VOTE", "ACT-APPLY-VOTE"}
        record = f"some RecoveryKernelVectors.record{i}" if arithmetic else "none"
        if not arithmetic:
            other.append(f"e{i}")
        parents = "[" + ",".join(content_id(v) for v in event["parent_hashes"]) + "]"
        lines += [
            f"def e{i} : Envelope := {{",
            f"  action := .{kinds[event['action_id']]},",
            f"  actor := {string(event['actor_id'])}, round := {string(event['round_id'])},",
            f"  height := {event['height']}, epoch := {string(event['validator_epoch'])},",
            f"  context := {string(event['vote_context_id'])}, parents := {parents},",
            f"  body := {content_id(event['body_hash'])} }}",
            f"def s{i} : Slot := ⟨e{i}, {i + 1}, {byte_list(raw)},",
            f"  {byte_list(n.canonical([event['actor_id'], event['vote_context_id']]))}, {record}⟩",
        ]
    for i in range(9):
        raw = b"deltareduce.vote-journal-projection.draft1\x00" + n.canonical(ids[:i])
        digest = hashlib.sha256(raw).digest()
        hashes[raw] = digest
        roots.append(journal_root(ids[:i]))
        lines += [f"def root{i} : ContentId := {byte_list(digest)}"]
    lines += [
        "def hashSamples : List (NativeBinding.Bytes × ContentId) := ["  # noqa: RUF001
        + ",".join(f"({byte_list(k)},{byte_list(v)})" for k, v in sorted(hashes.items()))
        + "]",
        "def env : PublicJournal.Environment codec syntheticTrust voteTrust where",
        "  native := NativeReplayVectors.env",
        "  otherAuthorized _ e := decide (e ∈ [" + ",".join(other) + "])",
        "  sha256 raw := ((hashSamples.find? (fun pair => pair.1 == raw)).map Prod.snd).getD []",
        "def slots : List Slot := [" + ",".join(f"s{i}" for i in range(8)) + "]",
        'def start : Journal := ⟨"validator-1", [], nativeCurrent anchor⟩',
        "def journalAt (count : Nat) : Journal := { start with slots := slots.take count }",
        "def events : List PublicJournal.Event := slots.map PublicJournal.Event.vote ++",
        "  [.advance RecoveryKernelVectors.certificate]",
        'def finalJournal : Journal := ⟨"validator-1", slots, RecoveryKernelVectors.nextCurrent⟩',
    ]
    cases = {f"envelope{i}MatchesPublicBytes": f"e{i}.encode = some s{i}.bytes" for i in range(8)}
    cases.update(
        {
            f"prefix{i}RootMatchesPublicWitness": f"journalRoot env (slots.take {i}) = root{i}"
            for i in range(9)
        }
    )
    cases["allOriginalVotesReplay"] = "PublicJournal.replay env start events = some finalJournal"
    cases["allOriginalSequencesRetained"] = "slots.map Slot.sequence = [1,2,3,4,5,6,7,8]"
    cases["nonArithmeticReceiptsRemainUnprojected"] = (
        "(slots.filter (fun s => !s.envelope.action.arithmetic)).map "
        "Slot.native = [none,none,none,none,none]"
    )
    cases["arithmeticReceiptsRemainExact"] = (
        "slots.filterMap Slot.native = [RecoveryKernelVectors.record4, "
        "RecoveryKernelVectors.record5, RecoveryKernelVectors.record7]"
    )
    for i in [4, 5, 7]:
        obs = native.operations[events[i]["durability_witness"]]
        lines += [
            f"def observation{i} : AppendObservation := {{",
            f"  before := ⟨some {obs['sequence_before']}, "
            f"some {content_id(obs['journal_before'])}⟩,",
            f"  after := ⟨some {obs['sequence_after']}, some {content_id(obs['journal_after'])}⟩,",
            f"  exposed := true, receipt := some {byte_list(obs['receipt_ascii'])},",
            f"  effect := some {byte_list(obs['effect_ascii'])} }}",
        ]
        cases[f"observedArithmetic{i}MatchesAllVotePrefix"] = (
            f"observedAppend env (journalAt {i}) s{i} observation{i} = some (journalAt {i + 1})"
        )
    cases.update(
        {
            "omittedNonArithmeticPrefixRejected": (
                "appendSlot env { start with slots := [s0,s1,s2] } s4 = none"
            ),
            "renumberedParameterRejected": (
                "appendSlot env (journalAt 4) { s4 with sequence := 1 } = none"
            ),
            "arithmeticCannotUseOtherAuthorization": (
                "appendSlot { env with otherAuthorized := fun _ _ => true } (journalAt "
                "4) { s4 with native := none } = none"
            ),
            "inventedOtherReceiptRejected": (
                "appendSlot env start { s0 with native := some "
                "RecoveryKernelVectors.record4 } = none"
            ),
            "missingNativeAuthorityRejected": (
                "appendSlot { env with native := NativeReplayVectors.missingEnv } "
                "(journalAt 4) s4 = none"
            ),
            "changedEnvelopeRejected": (
                "appendSlot env (journalAt 4) { s4 with bytes := s4.bytes ++ [32] } = none"
            ),
            "changedPublicBodyRejected": (
                "appendSlot env (journalAt 4) { s4 with envelope.body := [] } = none"
            ),
            "wrongActorRejected": 'appendSlot env { start with actor := "validator-2" } s0 = none',
            "duplicateContextRejected": (
                "appendSlot env (journalAt 5) { s4 with sequence := 6 } = none"
            ),
            "badBeforeRootRejected": (
                "observedAppend env (journalAt 4) s4 { observation4 with before.root "
                ":= some root0 } = none"
            ),
            "badAfterRootRejected": (
                "observedAppend env (journalAt 4) s4 { observation4 with after.root := "
                "some root4 } = none"
            ),
            "unknownAfterSequenceRejected": (
                "observedAppend env (journalAt 4) s4 { observation4 with "
                "after.sequence := none } = none"
            ),
            "unknownAfterRootRejected": (
                "observedAppend env (journalAt 4) s4 { observation4 with after.root := "
                "none } = none"
            ),
            "wrongExposedReceiptRejected": (
                "observedAppend env (journalAt 4) s4 { observation4 with receipt := none } = none"
            ),
            "unexposedHasNoOutput": (
                "observedAppend env (journalAt 4) s4 { observation4 with exposed := "
                "false, receipt := none, effect := none } = some (journalAt 5)"
            ),
            "unexposedCannotClaimOutput": (
                "observedAppend env (journalAt 4) s4 { observation4 with exposed := false } = none"
            ),
            "currentAdvanceDoesNotRewriteJournalRoot": "journalRoot env finalJournal.slots = root8",
        }
    )
    lines += [f"theorem {name} : {claim} := by decide" for name, claim in cases.items()]
    lines += ["", "end DeltaReduce.PublicJournalVectors", ""]
    document = {
        "scope": "FULL_EIGHT_VOTE_PUBLIC_PREFIX_NATIVE_ARITHMETIC_NOT_FULL_RUNTIME_REFINEMENT",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "trace_validation": checked["status"],
        "original_sequences": list(range(1, 9)),
        "arithmetic_sequences": [5, 6, 8],
        "public_prefix_roots": roots,
        "kernel_decide_theorems": list(cases),
        "sha256_samples": len(hashes),
        "other_receipts": "unprojected none, never invented empty native bytes",
        "other_admission": "finite checked-trace envelope set, not a Lean phase/QC proof",
        "metadata_qc_hash_scan_provenance": "synthetic examples; concrete adapters still open",
        "formal_go": False,
    }
    target.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    evidence_path.write_bytes(n.canonical(document) + b"\n")
    print(f"public journal vectors: {len(cases)} kernel examples; original 8-vote prefix")


if __name__ == "__main__":
    generate()
