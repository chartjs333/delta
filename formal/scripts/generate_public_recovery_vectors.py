"""Checked all-vote crash/recovery examples; synthetic scan trust, no physical WAL."""

import hashlib
from pathlib import Path

from generate_native_vote_vectors import byte_list, content_id, string
from generate_public_journal_vectors import refinement
from native_trace_witness import NativeEvidence, n

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "formal/proofs/DeltaReduce/PublicRecoveryVectors.lean"
EVIDENCE = ROOT / "formal/proposals/public-recovery-vectors.json"
NAMES = (
    ["normal-apply"]
    + [
        f"cut-{kind}-{cut}"
        for kind in ["parameter", "apply"]
        for cut in ["durable", "committed", "append-survived", "barrier-failed-survived"]
    ]
    + [
        "uncertain-parameter-append-absent",
        "uncertain-apply-barrier-absent",
        "uncertain-parameter-ambiguous",
        "uncertain-apply-torn",
        "uncertain-parameter-incomplete",
    ]
)


def observation(value):
    def tip(when):
        seq, root = value[f"sequence_{when}"], value[f"journal_{when}"]
        return (
            "⟨"
            + ("none" if seq is None else f"some {seq}")
            + ", "
            + ("none" if root is None else "some " + content_id(root))
            + "⟩"
        )

    def output(field):
        raw = value[field]
        return "none" if raw is None else "some " + byte_list(raw.encode("ascii"))

    return (
        "{ before := "
        + tip("before")
        + ", after := "
        + tip("after")
        + ", receipt := "
        + output("receipt_ascii")
        + ", effect := "
        + output("effect_ascii")
        + " }"
    )


def generate(fixture_root=ROOT / "formal/fixtures/traces", target=TARGET, evidence_path=EVIDENCE):
    loaded, sources = {}, []
    # Validate every complete source first; invalid non-arithmetic history or
    # rehashed observations must not produce a partial new vector artifact.
    for name in NAMES:
        trace_path, bundle_path = (
            fixture_root / "legal" / f"{name}.json",
            fixture_root / "native" / f"{name}.json",
        )
        native = NativeEvidence(bundle_path, hashlib.sha256(bundle_path.read_bytes()).hexdigest())
        checked = refinement.check_trace(trace_path, native)
        n.require(checked["status"] == "PASS", "PUBLIC_RECOVERY_SOURCE")
        loaded[name] = (n.decode(trace_path.read_bytes()), native)
        sources.append(
            {"name": name, "native_sha256": hashlib.sha256(bundle_path.read_bytes()).hexdigest()}
        )
    lines = [
        "import DeltaReduce.PublicRecovery",
        "import DeltaReduce.PublicJournalVectors",
        "namespace DeltaReduce.PublicRecoveryVectors",
        "open NativeBinding NativeGraphVectors NativeVoteVectors PublicJournal",
        "open PublicJournalVectors PublicRecovery",
        "set_option maxRecDepth 1000000",
        "set_option maxHeartbeats 0",
        "def env : PublicRecovery.Environment codec syntheticTrust voteTrust where",
        "  journal := PublicJournalVectors.env",
        "  scanAuthenticated _ _ _ _ := true -- synthetic, not physical authentication",
        'def boot : Machine := PublicRecovery.initial "validator-1" (nativeCurrent anchor)',
        "def machineAt (count : Nat) : Machine := { boot with",
        "  log := (slots.take count).map PublicJournal.Event.vote, journal := journalAt count }",
        (
            "def exposedStages : List String := "
            '["VALIDATED","APPENDED","DURABLE","COMMITTED","EXPOSED"]'
        ),
        "def noOutput (before after : Nat) : Observation :=",
        (
            "  ⟨knownTip env.journal (slots.take before), knownTip "
            "env.journal (slots.take after), none, none⟩"
        ),
        "def unknownOutput (before : Nat) : Observation :=",
        "  ⟨knownTip env.journal (slots.take before), ⟨none,none⟩, none, none⟩",
    ]
    cases = {}
    normal, native = loaded["normal-apply"]
    for e in normal["events"]:
        if e["actor_id"] == "validator-1" and e["action_id"] in {
            "ACT-PARAM-VOTE",
            "ACT-APPLY-VOTE",
        }:
            seq = e["durable_sequence"]
            lines.append(
                f"def observed{seq} : Observation := "
                + observation(native.operations[e["durability_witness"]])
            )
    lines += [
        "def submitSlot (m : Machine) (slot : Slot) : Option Machine :=",
        "  if slot.envelope.action.arithmetic then",
        (
            "    let o := if slot.sequence = 5 then observed5 else if "
            "slot.sequence = 6 then observed6 else observed8"
        ),
        "    persist env.journal m slot exposedStages o",
        "  else otherVote env.journal m slot",
        "def runPrefix (count : Nat) : Option Machine := (slots.take count).foldlM submitSlot boot",
        "def normalEight : Machine := { machineAt 8 with sent := [s4,s5,s7] }",
    ]
    cases["prefixFourFromEmpty"] = "runPrefix 4 = some (machineAt 4)"
    cases["allEightFromEmpty"] = "runPrefix 8 = some normalEight"
    cases["normalCurrentAdvance"] = (
        "advance env.journal normalEight RecoveryKernelVectors.certificate = some "
        "{ normalEight with journal := finalJournal, log := events }"
    )
    for i, name in enumerate(NAMES[1:9]):
        trace, native = loaded[name]
        e = next(
            e
            for e in trace["events"]
            if e["action_id"] in {"ACT-PARAM-VOTE", "ACT-APPLY-VOTE"}
            and e["actor_id"] == "validator-1"
            and "EXPOSED" not in native.operations[e["durability_witness"]]["stages"]
        )
        obs = native.operations[e["durability_witness"]]
        before, seq = obs["sequence_before"], obs["sequence_after"]
        stages = "[" + ",".join(string(s) for s in obs["stages"]) + "]"
        lines += [
            f"def stages{i} : List String := {stages}",
            f"def cutObservation{i} : Observation := {observation(obs)}",
        ]
        cases[f"cut{i}PreservesOriginalUnexposedRecord"] = (
            f"persist env.journal (machineAt {before}) s{seq - 1} stages{i} cutObservation{i} = "
            f"some {{ machineAt {seq} with mode := .mustCrash }}"
        )
    for i, name in enumerate(NAMES[9:]):
        trace, native = loaded[name]
        e = next(
            e
            for e in trace["events"]
            if e["action_id"] in {"ACT-PARAM-VOTE", "ACT-APPLY-VOTE"} and e["outcome"] == "FAULT"
        )
        obs = native.operations[e["durability_witness"]]
        before = obs["sequence_before"]
        stages = "[" + ",".join(string(s) for s in obs["stages"]) + "]"
        lines += [
            f"def uncertainStages{i} : List String := {stages}",
            f"def uncertainObservation{i} : Observation := {observation(obs)}",
        ]
        cases[f"unknown{i}KeepsOriginalKnownPrefix"] = (
            f"persist env.journal (machineAt {before}) s{before} "
            f"uncertainStages{i} uncertainObservation{i} = "
            f"some {{ machineAt {before} with mode := .mustCrash, pending := some s{before} }}"
        )
        recoveries = [
            native.operations[e["durability_witness"]]
            for e in trace["events"]
            if e["action_id"] == "ACT-JOURNAL-RECOVER" and e.get("durability_witness")
        ]
        if recoveries:
            scan = recoveries[-1]
            lines.append(f"def scanObservation{i} : Observation := {observation(scan)}")
            pending = (
                f"{{ machineAt {before} with mode := .recovering, pending := some s{before} }}"
            )
            if "VERIFIED_ABSENT" in scan["stages"]:
                cases[f"scan{i}VerifiedAbsenceRestoresExactPrefix"] = (
                    f"recover env {pending} (.verifiedAbsent (machineAt {before}).log) "
                    f"scanObservation{i} = "
                    f"some (machineAt {before})"
                )
            else:
                kind = "ambiguous" if "AMBIGUOUS" in scan["stages"] else "corrupt"
                cases[f"scan{i}BlocksWithoutClaimingAbsent"] = (
                    f"recover env {pending} .{kind} scanObservation{i} = "
                    f"some {{ machineAt {before} with mode := .blocked, "
                    f"pending := some s{before} }}"
                )
    lines += [
        "def unexposed : Machine := { machineAt 5 with mode := .mustCrash }",
        "def awaiting : Machine := { machineAt 4 with mode := .recovering, pending := some s4 }",
        "def restored : Machine := machineAt 5",
        "def advanced : Machine := { normalEight with journal := finalJournal, log := events }",
    ]
    cases.update(
        {
            "noVoteBeforeRequiredCrash": "otherVote env.journal unexposed s6 = none",
            "noCurrentAdvanceBeforeRecovery": (
                "advance env.journal unexposed RecoveryKernelVectors.certificate = none"
            ),
            "noRetryBeforeRecovery": (
                "exposeRetry unexposed s4.key RecoveryKernelVectors.record4.data.command = none"
            ),
            "restartBeforeCrashRejected": "restart unexposed = none",
            "crashThenRestart": (
                "(crash unexposed >>= restart) = some { unexposed with mode := .recovering }"
            ),
            "knownFullPrefixRecovered": (
                "recover env { unexposed with mode := .recovering } (.complete "
                "unexposed.log) (noOutput 5 5) = some restored"
            ),
            "unexposedReceiptReturnedOnlyByRetry": (
                "exposeRetry restored s4.key "
                "RecoveryKernelVectors.record4.data.command = some ({ restored "
                "with sent := [s4] }, RecoveryKernelVectors.record4)"
            ),
            "unknownPresenceReplaysAllVotes": (
                "recover env awaiting (.complete restored.log) (noOutput 4 5) = some restored"
            ),
            "ordinaryOldPrefixCannotResolveUnknown": (
                "recover env awaiting (.complete awaiting.log) (noOutput 4 4) = none"
            ),
            "incompleteScanRemainsUnresolved": (
                "recover env awaiting .incomplete (unknownOutput 4) = some awaiting"
            ),
            "incompleteCannotClaimKnownTip": (
                "recover env awaiting .incomplete (noOutput 4 4) = none"
            ),
            "corruptScanBlocks": (
                "recover env awaiting .corrupt (unknownOutput 4) = some { "
                "awaiting with mode := .blocked }"
            ),
            "ambiguousScanBlocks": (
                "recover env awaiting .ambiguous (unknownOutput 4) = some { "
                "awaiting with mode := .blocked }"
            ),
            "blockedCannotBeRepairedByAnotherScan": (
                "recover env { awaiting with mode := .blocked } (.verifiedAbsent "
                "awaiting.log) (noOutput 4 4) = none"
            ),
            "unauthenticatedScanRejected": (
                "recover { env with scanAuthenticated := fun _ _ _ _ => false } "
                "awaiting (.complete restored.log) (noOutput 4 5) = none"
            ),
            "truncatedVerifiedAbsenceRejected": (
                "recover env awaiting (.verifiedAbsent (machineAt 3).log) (noOutput 4 3) = none"
            ),
            "recoveryRejectsWrongRoot": (
                "recover env awaiting (.complete restored.log) { noOutput 4 5 "
                "with after := knownTip env.journal [] } = none"
            ),
            "recoveryNeverReturnsReceipt": (
                "recover env awaiting (.complete restored.log) { noOutput 4 5 "
                "with receipt := some RecoveryKernelVectors.record4.receipt } = "
                "none"
            ),
            "historicalRetryAfterCurrentAdvance": (
                "exposeRetry advanced s4.key "
                "RecoveryKernelVectors.record4.data.command = some (advanced, "
                "RecoveryKernelVectors.record4)"
            ),
            "historicalConflictBeforeAppend": (
                "retry advanced s4.key "
                "(RecoveryKernelVectors.record4.data.command ++ [32]) = .conflict"
            ),
            "exposureWithoutBarrierRejected": (
                "persist env.journal (machineAt 4) s4 "
                '["VALIDATED","APPENDED","COMMITTED","EXPOSED"] observed5 = none'
            ),
            "unexposedWithReturnedBytesRejected": (
                "persist env.journal (machineAt 4) s4 stages0 observed5 = none"
            ),
            "unknownWithReturnedBytesRejected": (
                "persist env.journal (machineAt 4) s4 uncertainStages0 observed5 = none"
            ),
            "nativeMissingGraphBeforeAppendRejected": (
                "persist { env.journal with native := "
                "NativeReplayVectors.missingEnv } (machineAt 4) s4 exposedStages "
                "observed5 = none"
            ),
        }
    )
    lines += [f"theorem {name} : {claim} := by decide" for name, claim in cases.items()]
    lines += ["end DeltaReduce.PublicRecoveryVectors", ""]
    doc = {
        "sources": sources,
        "kernel_decide_theorems": list(cases),
        "formal_go": False,
        "scope": "ALL_VOTE_JOURNAL_STAGE_AND_SCAN_LAYER_NOT_FULL_PUBLIC_NATIVE_REFINEMENT",
        "scan_authentication": "synthetic; no physical WAL or general exporter proof",
    }
    target.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    evidence_path.write_bytes(n.canonical(doc) + b"\n")
    print(f"public recovery: {len(cases)} kernel examples, {len(sources)} validated source traces")


if __name__ == "__main__":
    generate()
