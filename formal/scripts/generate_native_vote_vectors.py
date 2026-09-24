"""Native-derived pre-WAL records versus pinned diagnostic receipts (not C++)."""

import hashlib
import json
from pathlib import Path

from native_durability_witness import check_durability_trace, n
from native_trace_witness import NativeEvidence, check_native_trace

ROOT = Path(__file__).resolve().parents[2]
TRACE = ROOT / "formal/fixtures/traces/legal/normal-apply.json"
SOURCE = ROOT / "formal/fixtures/traces/native/normal-apply.json"
TARGET = ROOT / "formal/proofs/DeltaReduce/NativeVoteVectors.lean"
EVIDENCE = ROOT / "formal/proposals/native-vote-vectors.json"


def string(value):
    return json.dumps(value, ensure_ascii=True)


def byte_list(value):
    if isinstance(value, str):
        value = value.encode("ascii")
    return "[" + ",".join(map(str, value)) + "]"


def content_id(value):
    return byte_list(bytes.fromhex(value[7:]))


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
    n.require(len(events) == 3, "NATIVE_VOTE_VECTOR_SCOPE")
    lines = [
        "import DeltaReduce.NativeGraphVectors",
        "import DeltaReduce.RecoveryKernelVectors",
        "",
        "/-! Exact pre-WAL records computed from the anchored graph. Finite input",
        "codec/hash samples and synthetic metadata trust are not native execution. -/",
        "namespace DeltaReduce.NativeVoteVectors",
        "open NativeBinding NativeGraphVectors",
        "set_option maxRecDepth 1000000",
        "set_option maxHeartbeats 0",
        "def voteTrust : NativeVoteTrust := ⟨fun _ _ => True⟩",
        "-- First PARAMETER binding has no AggregateRootQC prerequisite.",
        "def parameterAnchor : Anchor := { anchor with aggregate := none }",
        "def parameterBinding : Binding codec syntheticTrust parameterAnchor store := {",
        "  fixtureBinding with",
        "  complete := by",
        "    intro r member",
        "    change r ∈ [anchor.authority] at member",
        "    have eq : r = anchor.authority := by simpa using member",
        "    subst r",
        "    exact fixtureBinding.complete anchor.authority (by simp [Anchor.roots])",
        "  aggregateBound := by intro r h; contradiction",
        "}",
    ]
    cases = {}
    pinned = []
    for index, event in enumerate(events):
        proof = event["arithmetic_witness"]
        snapshot = evidence.snapshots[proof["snapshot_id"]]
        payload = n.decode(proof["command_ascii"].encode("ascii"))["payload"]
        is_parameter = event["action_id"] == "ACT-PARAM-VOTE"
        role = (
            f".parameter {string(payload['domain'])} {string(payload['shard'])}"
            if is_parameter
            else ".apply"
        )
        binding = "parameterBinding" if is_parameter else "fixtureBinding"
        record = event["durable_sequence"] - 1
        n.require(record == [4, 5, 7][index], "NATIVE_VOTE_VECTOR_SEQUENCE")
        projection = (
            "fixtureBinding.authority.apc"
            if is_parameter
            else "(anchor.aggregate.getD anchor.authority)"
        )
        lines += [
            f"def metadata{index} : VoteMetadata := {{",
            f"  actor := {string(event['actor_id'])}, kind := {role}",
            f"  voteContext := {string(event['vote_context_id'])}",
            f"  parentCertificate := {content_id(snapshot['parent_certificate'])}",
            f"  projection := {projection}, logicalTime := {snapshot['anchor']['logical_time']}",
            "  recovered := true, validator := true }",
            f"def command{index} : Bytes := {byte_list(proof['command_ascii'])}",
            f"def state{index} : RecoveryKernel.State :=",
            f"  ⟨RecoveryKernelVectors.records.take {record}, nativeCurrent anchor⟩",
            f"def prepared{index} := prepareNativeFirst {binding} voteTrust metadata{index}",
            f"  True.intro .ready state{index} command{index}",
        ]
        cases[f"nativeRecord{index}MatchesDiagnostic"] = (
            f"prepared{index}.map NativePrepared.record = some RecoveryKernelVectors.record{record}"
        )
        cases[f"nativeRecord{index}Replays"] = (
            f"(prepared{index}.bind (fun p => RecoveryKernel.step RecoveryKernelVectors.adapter "
            f"state{index} (.vote p.record))) = some "
            f"⟨RecoveryKernelVectors.records.take {record + 1}, nativeCurrent anchor⟩"
        )
        call = f"prepareNativeFirst {binding} voteTrust"
        original = f"{call} metadata{index} True.intro"
        cases[f"nativeRecord{index}ChangedCommandRejected"] = (
            f"({original} .ready state{index} (command{index} ++ [32])).isNone = true"
        )
        cases[f"nativeRecord{index}ChangedModelRejected"] = (
            f"({original} .ready {{ state{index} with current := "
            f"{{ state{index}.current with model := [] }} }} command{index}).isNone = true"
        )
        cases[f"nativeRecord{index}ChangedOptimizerRejected"] = (
            f"({original} .ready {{ state{index} with current := "
            f"{{ state{index}.current with optimizer := [] }} }} command{index}).isNone = true"
        )
        cases[f"nativeRecord{index}ChangedCheckpointRejected"] = (
            f"({original} .ready {{ state{index} with current := "
            f"{{ state{index}.current with checkpoint := [] }} }} command{index}).isNone = true"
        )
        cases[f"nativeRecord{index}DeadlineRejected"] = (
            f"({call} {{ metadata{index} with logicalTime := anchor.context.hardDeadline }} "
            f"True.intro .ready state{index} command{index}).isNone = true"
        )
        cases[f"nativeRecord{index}RecoveryRequired"] = (
            f"({call} {{ metadata{index} with recovered := false }} True.intro "
            f".ready state{index} command{index}).isNone = true"
        )
        cases[f"nativeRecord{index}WrongRoleRejected"] = (
            f"({call} {{ metadata{index} with validator := false }} True.intro "
            f".ready state{index} command{index}).isNone = true"
        )
        cases[f"nativeRecord{index}DuplicateRejected"] = (
            f"({original} .ready {{ state{index} with votes := "
            f"state{index}.votes ++ [RecoveryKernelVectors.record{record}] }} "
            f"command{index}).isNone = true"
        )
        pinned.append(
            {
                "sequence": record + 1,
                "command_sha256": hashlib.sha256(
                    proof["command_ascii"].encode("ascii")
                ).hexdigest(),
                "snapshot_id": proof["snapshot_id"],
            }
        )
    ascii_string = "".join(map(chr, range(128)))
    lines += ["def everyASCII : String := String.ofList ((List.range 128).map Char.ofNat)"]
    cases.update(
        {
            "missingAuthorityCannotPrepare": (
                "prepareNativeAvailable (codec := codec) (store := store) "
                "(trust := syntheticTrust) "
                "(anchor := parameterAnchor) none voteTrust metadata0 True.intro "
                ".ready state0 command0 = none"
            ),
            "everyASCIIEscapeMatchesPython": (
                f"jsonASCII everyASCII = some {byte_list(n.canonical(ascii_string))}"
            ),
            "unicodeMetadataRejected": 'jsonASCII "\u00e9" = none',
            "firstParameterNeedsNoAggregate": "parameterAnchor.aggregate = none",
            "wrongParameterContextRejected": (
                "(deriveExpectedNativeVote parameterBinding { metadata0 with "
                'voteContext := "other" })'
                ".isNone = true"
            ),
            "wrongProjectionRejected": (
                "(deriveExpectedNativeVote parameterBinding { metadata0 with projection := "
                "fixtureBinding.authority.isc }).isNone = true"
            ),
            "shortCertificateIdRejected": (
                "(deriveExpectedNativeVote parameterBinding { metadata0 with "
                "parentCertificate := [] })"
                ".isNone = true"
            ),
            "unknownModeCannotPrepare": (
                "(prepareNativeFirst parameterBinding voteTrust metadata0 True.intro "
                ".unknown state0 command0).isNone = true"
            ),
            "emptyActorCannotPrepare": (
                '(prepareNativeFirst parameterBinding voteTrust { metadata0 with actor := "" } '
                "True.intro .ready state0 command0).isNone = true"
            ),
            "oversizedActorCannotPrepare": (
                "(prepareNativeFirst parameterBinding voteTrust { metadata0 with actor := "
                "String.ofList (List.replicate 257 'a') } True.intro .ready state0 command0)"
                ".isNone = true"
            ),
            "shortReceiptHashRejected": (
                "(encodeDiagnosticReceipt { codec with hash := fun _ => [] } "
                "command0 [] [] 1).isNone = true"
            ),
            "malformedNativeModelIdentityRejected": (
                "¬ NativeFresh { anchor with currentModelHash := [] } metadata0 .ready "
                "{ state0 with current := nativeCurrent { anchor with currentModelHash := [] } }"
            ),
            "malformedNativeOptimizerIdentityRejected": (
                "¬ NativeFresh { anchor with currentOptimizerHash := [] } metadata0 .ready "
                "{ state0 with current := nativeCurrent "
                "{ anchor with currentOptimizerHash := [] } }"
            ),
        }
    )
    envelope = evidence.operations[events[0]["durability_witness"]]["effect_ascii"]
    envelope_value = n.decode(envelope.encode("ascii"))["vote"]
    receipt = n.decode(
        evidence.operations[events[0]["durability_witness"]]["receipt_ascii"].encode("ascii")
    )
    receipt["sequence"] = (1 << 63) - 1
    lines += [
        f"def envelope0 : Bytes := {byte_list(n.canonical(envelope_value))}",
        f"def effect0 : Bytes := {byte_list(envelope)}",
    ]
    cases["maximumReceiptSequenceMatchesPython"] = (
        "encodeDiagnosticReceipt codec command0 envelope0 effect0 9223372036854775807 = "
        f"some {byte_list(n.canonical(receipt))}"
    )
    cases["zeroReceiptSequenceRejected"] = (
        "(encodeDiagnosticReceipt codec command0 envelope0 effect0 0).isNone = true"
    )
    cases["overflowReceiptSequenceRejected"] = (
        "(encodeDiagnosticReceipt codec command0 envelope0 effect0 "
        "9223372036854775808).isNone = true"
    )
    lines += [f"theorem {name} : {claim} := by decide" for name, claim in cases.items()]
    lines += ["", "end DeltaReduce.NativeVoteVectors", ""]
    document = {
        "scope": "NATIVE_GRAPH_DERIVED_PRE_WAL_DIAGNOSTIC_RECORDS_NOT_NATIVE_EXECUTION",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "pinned_arithmetic_records": pinned,
        "kernel_decide_theorems": list(cases),
        "input_codec": "twelve pinned artifact strings",
        "hashes": "finite output samples; SHA256 implementation not proved",
        "metadata_trust": "synthetic, no exporter authentication",
        "replay_adapter": "finite RecoveryKernelVectors table, not general native refinement",
        "formal_go": False,
    }
    target.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    evidence_path.write_bytes(n.canonical(document) + b"\n")
    print(f"native vote vectors: {len(cases)} kernel examples, three computed pre-WAL records")


if __name__ == "__main__":
    generate()
