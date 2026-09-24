"""Native arithmetic replay bridge examples; finite input codec and synthetic trust."""

import hashlib
from pathlib import Path

from generate_native_vote_vectors import byte_list
from native_durability_witness import check_durability_trace, n
from native_trace_witness import NativeEvidence, check_native_trace

ROOT = Path(__file__).resolve().parents[2]
TRACE = ROOT / "formal/fixtures/traces/legal/normal-apply.json"
SOURCE = ROOT / "formal/fixtures/traces/native/normal-apply.json"
TARGET = ROOT / "formal/proofs/DeltaReduce/NativeReplayVectors.lean"
EVIDENCE = ROOT / "formal/proposals/native-replay-vectors.json"


def generate(trace_path=TRACE, source=SOURCE, target=TARGET, evidence_path=EVIDENCE):
    trace = n.decode(trace_path.read_bytes())
    evidence = NativeEvidence(source, hashlib.sha256(source.read_bytes()).hexdigest())
    check_native_trace(trace, evidence)
    check_durability_trace(trace, evidence)
    events = [
        e
        for e in trace["events"]
        if e["actor_id"] == "validator-1"
        and e["action_id"] in {"ACT-PARAM-VOTE", "ACT-APPLY-VOTE"}
        and e["outcome"] == "ACCEPTED"
    ]
    n.require([e["durable_sequence"] for e in events] == [5, 6, 8], "NATIVE_REPLAY_SCOPE")
    body = n.canonical(
        n.decode(events[-1]["arithmetic_witness"]["command_ascii"].encode())["payload"]
    )
    lines = [
        "import DeltaReduce.NativeReplay",
        "import DeltaReduce.NativeVoteVectors",
        "",
        "/-! Native arithmetic is recomputed, not accepted by a record table.",
        "Input/hash samples and metadata/QC/scan trust are finite and synthetic.",
        "The three-vote journal renumbers only arithmetic votes: it is NOT the",
        "full public trace, whose other five vote kinds need their own bridge. -/",
        "namespace DeltaReduce.NativeReplayVectors",
        "open NativeBinding NativeReplay NativeGraphVectors NativeVoteVectors RecoveryKernel",
        "set_option maxRecDepth 1000000",
        "set_option maxHeartbeats 0",
        "",
    ]
    for i in range(3):
        anchor = "parameterAnchor" if i < 2 else "anchor"
        binding = "parameterBinding" if i < 2 else "fixtureBinding"
        lines += [
            f"def input{i} : NativeReplay.Input codec syntheticTrust voteTrust :=",
            f"  ⟨{anchor}, store, some {binding}, metadata{i}, True.intro⟩",
        ]
    lines += [
        (
            "def applyGraph : NativeReplay.Graph codec syntheticTrust := ⟨anchor, "
            "store, some fixtureBinding⟩"
        ),
        f"def certifiedBody : NativeBinding.Bytes := {byte_list(body)}",
        "def env : Environment codec syntheticTrust voteTrust where",
        "  input context := if context = RecoveryKernelVectors.data4.context then some input0",
        "    else if context = RecoveryKernelVectors.data5.context then some input1",
        "    else if context = RecoveryKernelVectors.data7.context then some input2 else none",
        "  graph _ := some applyGraph",
        "  applyAuthenticated _ body c := decide (body = certifiedBody ∧",
        "    c.bytes = RecoveryKernelVectors.certificate.bytes ∧",
        "    c.next.checkpoint = RecoveryKernelVectors.nextCurrent.checkpoint)",
        "  scanAuthenticated _ _ _ _ := true -- Named synthetic exporter trust.",
        "def nativeAdapter := NativeReplay.adapter env",
    ]
    cases = {}
    for i, old in enumerate([4, 5, 7]):
        obs = evidence.operations[events[i]["durability_witness"]]
        receipt = n.decode(obs["receipt_ascii"].encode("ascii"))
        receipt["sequence"] = i + 1
        lines += [
            f"def r{i} : Record := {{ RecoveryKernelVectors.record{old} with sequence := {i + 1}, "
            f"receipt := {byte_list(n.canonical(receipt))} }}",
        ]
        cases[f"pinnedNativeRecord{i}Admitted"] = (
            f"step nativeAdapter state{i} (.vote RecoveryKernelVectors.record{old}) = "
            f"some ⟨RecoveryKernelVectors.records.take {old + 1}, nativeCurrent anchor⟩"
        )
    lines += [
        "def start := initial (nativeCurrent anchor)",
        "def prior : List Entry := [.vote r0, .vote r1]",
        (
            "def journal : List Entry := prior ++ [.vote r2, .advance "
            "RecoveryKernelVectors.certificate]"
        ),
        "def completeState : State := ⟨[r0, r1, r2], RecoveryKernelVectors.nextCurrent⟩",
        "def absentEnv : Environment codec syntheticTrust voteTrust := "
        "{ env with input := fun _ => none }",
        "def missingEnv := { env with input := fun _ => some { input0 with available := none } }",
        "def unboundQC := { env with applyAuthenticated := fun _ _ _ => false }",
        "def unboundScan := { env with scanAuthenticated := fun _ _ _ _ => false }",
    ]
    cases.update(
        {
            "nativeJournalReplays": "replay nativeAdapter start journal = some completeState",
            "nativePrepareExact": "prepare nativeAdapter .ready start r0.data = .pending r0",
            "missingContextRejects": (
                "prepare (NativeReplay.adapter absentEnv) .ready start r0.data = .rejected"
            ),
            "missingGraphRejects": (
                "prepare (NativeReplay.adapter missingEnv) .ready start r0.data = .rejected"
            ),
            "missingGraphHasNoEffect": "NativeReplay.effect missingEnv r0.data = none",
            "wrongAuthorityRejected": (
                "step nativeAdapter start (.vote { r0 with data.authority := [] }) = none"
            ),
            "wrongBodyRejected": (
                "step nativeAdapter start (.vote { r0 with data.body := [] }) = none"
            ),
            "wrongCanonicalCommandRejected": (
                "step nativeAdapter start (.vote { r0 with data.command := "
                "r0.data.command ++ [32] }) = none"
            ),
            "wrongSequenceRejected": (
                "step nativeAdapter start (.vote { r0 with sequence := 2 }) = none"
            ),
            "wrongReceiptRejected": (
                "step nativeAdapter start (.vote { r0 with receipt := [] }) = none"
            ),
            "wrongEffectRejected": (
                "step nativeAdapter start (.vote { r0 with effect := [] }) = none"
            ),
            "missingContextReceiptIsNone": (
                "NativeReplay.receipt absentEnv r0.data 1 r0.effect = none"
            ),
            "overflowReceiptIsNone": (
                "NativeReplay.receipt env r0.data 9223372036854775808 r0.effect = none"
            ),
            "zeroReceiptIsNone": "NativeReplay.receipt env r0.data 0 r0.effect = none",
            "changedReceiptEffectIsNone": "NativeReplay.receipt env r0.data 1 [] = none",
            "failedEffectStopsPreparation": (
                "prepare { nativeAdapter with effect := fun _ => none } .ready start "
                "r0.data = .rejected"
            ),
            "failedReceiptStopsPreparation": (
                "prepare { nativeAdapter with receipt := fun _ _ _ => none } .ready "
                "start r0.data = .rejected"
            ),
            "failedEffectCannotReplayEmpty": (
                "step { nativeAdapter with effect := fun _ => none } start (.vote { r0 "
                "with effect := [] }) = none"
            ),
            "failedReceiptCannotReplayEmpty": (
                "step { nativeAdapter with receipt := fun _ _ _ => none } start (.vote "
                "{ r0 with receipt := [] }) = none"
            ),
            "wrongQCModelRejected": (
                "step nativeAdapter start (.advance { "
                "RecoveryKernelVectors.certificate with next.model := [0] }) = none"
            ),
            "wrongQCOptimizerRejected": (
                "step nativeAdapter start (.advance { "
                "RecoveryKernelVectors.certificate with next.optimizer := [0] }) = none"
            ),
            "wrongQCParentRejected": (
                "step nativeAdapter start (.advance { "
                "RecoveryKernelVectors.certificate with parent.model := [0] }) = none"
            ),
            "unauthenticatedQCRejected": (
                "step (NativeReplay.adapter unboundQC) start (.advance "
                "RecoveryKernelVectors.certificate) = none"
            ),
            "missingQCGraphRejected": (
                "step (NativeReplay.adapter { env with graph := fun _ => none }) start "
                "(.advance RecoveryKernelVectors.certificate) = none"
            ),
            "duplicateQCIsIdempotent": (
                "step nativeAdapter completeState (.advance "
                "RecoveryKernelVectors.certificate) = some completeState"
            ),
            "oldParentFirstRejected": (
                "prepare nativeAdapter .ready (initial "
                "RecoveryKernelVectors.nextCurrent) r0.data = .rejected"
            ),
            "historicalRetryAfterAdvance": (
                "prepare nativeAdapter .ready completeState r0.data = .retry r0"
            ),
            "historicalConflictAfterAdvance": (
                "prepare nativeAdapter .ready completeState { r0.data with command := "
                "r0.data.command ++ [32] } = .conflict"
            ),
            "survivingUnexposedRecordRecovered": (
                "resolveUnknown nativeAdapter start prior r2 (.complete (prior ++ "
                "[.vote r2])) = .ready ⟨[r0,r1,r2], nativeCurrent anchor⟩"
            ),
            "verifiedAbsentReplaysExactPrefix": (
                "resolveUnknown nativeAdapter start prior r2 (.verifiedAbsent prior) = "
                ".ready ⟨[r0,r1], nativeCurrent anchor⟩"
            ),
            "plainPrefixNotAbsence": (
                "resolveUnknown nativeAdapter start prior r2 (.complete prior) = .blocked"
            ),
            "truncatedAbsentPrefixRejected": (
                "resolveUnknown nativeAdapter start prior r2 (.verifiedAbsent []) = .blocked"
            ),
            "untrustedScanRejected": (
                "resolveUnknown (NativeReplay.adapter unboundScan) start prior r2 "
                "(.complete (prior ++ [.vote r2])) = .blocked"
            ),
            "incompleteStaysUnknown": (
                "observedSequence (resolveUnknown nativeAdapter start prior r2 .incomplete) = none"
            ),
            "corruptStaysBlocked": (
                "resolveUnknown nativeAdapter start prior r2 .corrupt = .blocked"
            ),
            "ambiguousStaysBlocked": (
                "resolveUnknown nativeAdapter start prior r2 .ambiguous = .blocked"
            ),
            "blockedCannotResume": (
                "continueRecovery nativeAdapter start prior r2 .blocked "
                "(.verifiedAbsent prior) = .blocked"
            ),
            "unexposedCannotSend": (
                "exposePending .ready .durable ⟨[r0], nativeCurrent anchor⟩ r0 = none"
            ),
            "committedExactRecordCanSend": (
                "exposePending .ready .committed ⟨[r0], nativeCurrent anchor⟩ r0 = some r0"
            ),
        }
    )
    lines += [f"theorem {name} : {claim} := by decide" for name, claim in cases.items()]
    lines += ["", "end DeltaReduce.NativeReplayVectors", ""]
    document = {
        "scope": "NATIVE_ARITHMETIC_REPLAY_BRIDGE_NOT_FULL_PUBLIC_TRACE_OR_NATIVE_EXECUTION",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "kernel_decide_theorems": list(cases),
        "original_pinned_sequences": [5, 6, 8],
        "arithmetic_only_journal_sequences": [1, 2, 3],
        "arithmetic_admission": "recomputed with NativeBinding and exact encoders",
        "remaining_trust": (
            "finite input codec/hash samples and synthetic metadata/QC/scan provenance"
        ),
        "formal_go": False,
    }
    target.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    evidence_path.write_bytes(n.canonical(document) + b"\n")
    print(f"native replay vectors: {len(cases)} kernel examples")


if __name__ == "__main__":
    generate()
