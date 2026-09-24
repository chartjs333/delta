"""Pin diagnostic receipt bytes to a finite Lean replay example, not native I/O.

Arithmetic admission is checked by the proposal oracle before generation. Lean
uses a finite table adapter, NOT a proof of NativeBinding/exporter refinement.
Non-arithmetic prefix records have no receipt projection in the public witness;
their empty receipt/effect and envelope-as-command are explicit synthetic slots.
"""

import hashlib
from pathlib import Path

from native_durability_witness import check_durability_trace, envelope, n
from native_trace_witness import NativeEvidence, check_native_trace

ROOT = Path(__file__).resolve().parents[2]
TRACE = ROOT / "formal/fixtures/traces/legal/durability-after-current.json"
SOURCE = ROOT / "formal/fixtures/traces/native/durability-after-current.json"
TARGET = ROOT / "formal/proofs/DeltaReduce/RecoveryKernelVectors.lean"
EVIDENCE = ROOT / "formal/proposals/recovery-kernel-vectors.json"


def byte_list(value):
    if isinstance(value, str):
        value = value.encode("ascii")
    return "[" + ",".join(map(str, value)) + "]"


def generate(trace_path=TRACE, source=SOURCE, target=TARGET, evidence_path=EVIDENCE):
    trace = n.decode(trace_path.read_bytes())
    evidence = NativeEvidence(source, hashlib.sha256(source.read_bytes()).hexdigest())
    native_count = check_native_trace(trace, evidence)
    counts = check_durability_trace(trace, evidence)
    events = [
        e
        for e in trace["events"]
        if e["actor_id"] == "validator-1"
        and e["action_id"].endswith("-VOTE")
        and e["outcome"] == "ACCEPTED"
    ]
    n.require(len(events) == 8, "RECOVERY_VECTOR_SCOPE")
    lines = [
        "import DeltaReduce.RecoveryKernel",
        "",
        "/-! Generated finite diagnostic example. Receipt bytes are pinned for",
        "PARAMETER/APPLY only. Other votes use synthetic empty byte slots.",
        "Table admission/authentication is not NativeBinding or native execution. -/",
        "namespace DeltaReduce.RecoveryKernelVectors",
        "open RecoveryKernel",
        "set_option maxRecDepth 1000000",
        "set_option maxHeartbeats 0",
        "",
    ]
    parameter = apply = None
    old = new = None
    pinned = []
    for index, event in enumerate(events):
        n.require(event["durable_sequence"] == index + 1, "RECOVERY_VECTOR_SEQUENCE")
        context = n.canonical([event["actor_id"], event["vote_context_id"]])
        proof = event["arithmetic_witness"]
        if proof:
            snapshot = evidence.snapshots[proof["snapshot_id"]]
            obs = evidence.operations[event["durability_witness"]]
            command = proof["command_ascii"]
            body = n.canonical(n.decode(command.encode("ascii"))["payload"])
            authority = snapshot["anchor"]["authority_id"]
            receipt, effect = obs["receipt_ascii"], obs["effect_ascii"]
            anchor = snapshot["anchor"]
            old = [
                anchor["parent_checkpoint"],
                anchor["current_model_hash"],
                anchor["current_optimizer_hash"],
            ]
            if event["action_id"] == "ACT-PARAM-VOTE" and parameter is None:
                parameter = index
            if event["action_id"] == "ACT-APPLY-VOTE":
                apply = index
                payload = n.decode(body)
                advance = next(
                    e for e in trace["events"] if e["action_id"] == "ACT-CURRENT-ADVANCE"
                )
                new = [
                    advance["result_hash"],
                    payload["next_model_hash"],
                    payload["next_optimizer_hash"],
                ]
            pinned.append(
                {
                    "record": index,
                    "sequence": index + 1,
                    "command_sha256": hashlib.sha256(command.encode("ascii")).hexdigest(),
                    "receipt_sha256": hashlib.sha256(receipt.encode("ascii")).hexdigest(),
                    "effect_sha256": hashlib.sha256(effect.encode("ascii")).hexdigest(),
                }
            )
        else:
            command = n.canonical(envelope(event))
            body, authority, receipt, effect = event["body_hash"], b"", b"", b""
        lines += [
            f"def data{index} : VoteData := ⟨{byte_list(context)}, {byte_list(command)}, "
            f"{byte_list(authority)}, {byte_list(body)}⟩",
            f"def record{index} : Record := ⟨data{index}, {index + 1}, "
            f"{byte_list(receipt)}, {byte_list(effect)}⟩",
        ]
    assert parameter is not None and apply is not None and old and new
    assert (parameter, apply) == (4, 7)
    lines += [
        "def oldCurrent : Current := ⟨" + ", ".join(map(byte_list, old)) + "⟩",
        "def nextCurrent : Current := ⟨" + ", ".join(map(byte_list, new)) + "⟩",
        "def certificate : Certificate := ⟨oldCurrent, nextCurrent, "
        + byte_list(n.canonical(advance))
        + "⟩",
        "def records : List Record := [" + ", ".join(f"record{i}" for i in range(8)) + "]",
        "def prior : List Entry := (records.take 4).map Entry.vote",
        "def journal : List Entry := records.map Entry.vote ++ [.advance certificate]",
        "def before : State := ⟨records.take 4, oldCurrent⟩",
        "def persisted : State := ⟨records.take 5, oldCurrent⟩",
        "def finalState : State := ⟨records, nextCurrent⟩",
        "def adapter : Adapter where",
        "  admitted current data := decide (current = oldCurrent ∧ data ∈ records.map Record.data)",
        "  effect data := match lookup records data.context with",
        "    | some r => some r.effect",
        "    | none => none",
        "  receipt data sequence effect := match lookup records data.context with",
        (
            "    | some r => if sequence = r.sequence ∧ effect = r.effect then "
            "some r.receipt else none"
        ),
        "    | none => none",
        "  authenticated c := decide (c = certificate)",
        "  scanAuthenticated _ _ _ _ := true -- Synthetic trust, not exporter authentication.",
    ]
    cases = {
        "unauthenticatedScanRejected": (
            "resolveUnknown { adapter with scanAuthenticated := fun _ _ _ _ => false } "
            "(initial oldCurrent) prior record4 (.verifiedAbsent prior) = .blocked"
        ),
        "fullJournalReplayed": "replay adapter (initial oldCurrent) journal = some finalState",
        "priorReplayed": "replay adapter (initial oldCurrent) prior = some before",
        "parameterOriginalReceipt": (
            "retry .ready finalState data4.context data4.command = .retry record4"
        ),
        "applyOriginalReceipt": (
            "retry .ready finalState data7.context data7.command = .retry record7"
        ),
        "sameContextChangedBytesConflict": (
            "retry .ready finalState data4.context (data4.command ++ [32]) = .conflict"
        ),
        "retryAfterCurrentNotReadmitted": (
            "prepare adapter .ready finalState data4 = .retry record4"
        ),
        "newAdmissionStaleParentRejected": (
            "prepare adapter .ready ⟨[], nextCurrent⟩ data4 = .rejected"
        ),
        "firstMismatchRejected": (
            "prepare adapter .ready before { data4 with command := [0] } = .rejected"
        ),
        "missingAuthorityRejected": (
            "prepare adapter .ready before { data4 with authority := [] } = .rejected"
        ),
        "preparedRecordExact": "prepare adapter .ready before data4 = .pending record4",
        "duplicateAppendRejected": "step adapter persisted (.vote record4) = none",
        "wrongSequenceRejected": (
            "step adapter before (.vote { record4 with sequence := 6 }) = none"
        ),
        "wrongReceiptRejected": (
            "step adapter before (.vote { record4 with receipt := record4.receipt ++ [32] }) = none"
        ),
        "wrongEffectRejected": (
            "step adapter before (.vote { record4 with effect := record4.effect ++ [32] }) = none"
        ),
        "unauthenticatedAdvanceRejected": (
            "step adapter persisted (.advance { certificate with bytes := [] }) = none"
        ),
        "staleAdvanceParentRejected": (
            "step adapter ⟨records, ⟨[0], [0], [0]⟩⟩ (.advance certificate) = none"
        ),
        "advanceReplayIdempotent": (
            "step adapter finalState (.advance certificate) = some finalState"
        ),
        "voteKeepsAllPointers": "step adapter before (.vote record4) = some persisted",
        "validatedCannotExpose": "exposePending .ready .validated persisted record4 = none",
        "appendedCannotExpose": "exposePending .ready .appended persisted record4 = none",
        "durableCannotExpose": "exposePending .ready .durable persisted record4 = none",
        "committedRecordExposes": (
            "exposePending .ready .committed persisted record4 = some record4"
        ),
        "absentRecordCannotExpose": "exposePending .ready .committed before record4 = none",
        "crashedCannotRetry": (
            "retry .crashed finalState data4.context data4.command = .unavailable"
        ),
        "recoveringCannotRetry": (
            "retry .recovering finalState data4.context data4.command = .unavailable"
        ),
        "unknownCannotRetry": (
            "retry .unknown finalState data4.context data4.command = .unavailable"
        ),
        "blockedCannotRetry": (
            "retry .blocked finalState data4.context data4.command = .unavailable"
        ),
        "unacknowledgedPresentRecovered": (
            "resolveUnknown adapter (initial oldCurrent) prior record4 (.complete "
            "(prior ++ [.vote record4])) = .ready persisted"
        ),
        "verifiedAbsenceRecovered": (
            "resolveUnknown adapter (initial oldCurrent) prior record4 (.verifiedAbsent "
            "prior) = .ready before"
        ),
        "ordinaryPrefixNotAbsence": (
            "resolveUnknown adapter (initial oldCurrent) prior record4 (.complete prior) = .blocked"
        ),
        "truncatedAbsenceBlocked": (
            "resolveUnknown adapter (initial oldCurrent) prior record4 (.verifiedAbsent "
            "[]) = .blocked"
        ),
        "changedSurvivingBytesBlocked": (
            "resolveUnknown adapter (initial oldCurrent) prior record4 (.complete "
            "(prior ++ [.vote { record4 with receipt := [] }])) = .blocked"
        ),
        "incompleteDoesNotInferSequence": (
            "observedSequence (resolveUnknown adapter (initial oldCurrent) prior "
            "record4 .incomplete) = none"
        ),
        "corruptScanBlocked": (
            "resolveUnknown adapter (initial oldCurrent) prior record4 .corrupt = .blocked"
        ),
        "ambiguousScanBlocked": (
            "resolveUnknown adapter (initial oldCurrent) prior record4 .ambiguous = .blocked"
        ),
        "blockedScanCannotBecomeReady": (
            "continueRecovery adapter (initial oldCurrent) prior record4 .blocked "
            "(.verifiedAbsent prior) = .blocked"
        ),
    }
    lines += [f"theorem {name} : {claim} := by decide" for name, claim in cases.items()]
    lines += ["", "end DeltaReduce.RecoveryKernelVectors", ""]
    evidence_document = {
        "scope": "FINITE_DIAGNOSTIC_REPLAY_NOT_NATIVE_REFINEMENT",
        "native_runtime_executed": False,
        "arithmetic_admission": "proposal oracle then finite Lean lookup table",
        "non_arithmetic_records": "synthetic empty receipt/effect slots; envelope-as-command",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "pinned_arithmetic_records": pinned,
        "checked_native_first_votes": native_count,
        "checked_durability": counts,
        "kernel_decide_theorems": list(cases),
    }
    target.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    evidence_path.write_bytes(n.canonical(evidence_document) + b"\n")
    print(
        f"recovery vectors: {len(cases)} kernel examples, {len(pinned)} pinned arithmetic records"
    )


if __name__ == "__main__":
    generate()
