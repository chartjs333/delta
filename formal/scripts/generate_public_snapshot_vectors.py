"""Exact v1 snapshot encoding and native first-event binding; synthetic exporter trust."""

import hashlib
from pathlib import Path

from generate_native_vote_vectors import byte_list, content_id
from generate_public_journal_vectors import refinement
from native_trace_witness import NativeEvidence, n

ROOT = Path(__file__).resolve().parents[2]
TRACE = ROOT / "formal/fixtures/traces/legal/normal-apply.json"
SOURCE = ROOT / "formal/fixtures/traces/native/normal-apply.json"
TARGET = ROOT / "formal/proofs/DeltaReduce/PublicSnapshotVectors.lean"
EVIDENCE = ROOT / "formal/proposals/public-snapshot-vectors.json"


def generate(trace_path=TRACE, source=SOURCE, target=TARGET, evidence_path=EVIDENCE):
    native = NativeEvidence(source, hashlib.sha256(source.read_bytes()).hexdigest())
    refinement.check_trace(trace_path, native)
    trace = n.decode(trace_path.read_bytes())
    events = [
        e
        for e in trace["events"]
        if e["actor_id"] == "validator-1"
        and e["action_id"] in {"ACT-PARAM-VOTE", "ACT-APPLY-VOTE"}
        and e["outcome"] == "ACCEPTED"
    ]
    n.require([e["durable_sequence"] for e in events] == [5, 6, 8], "SNAPSHOT_VECTOR_SCOPE")
    lines = [
        "import DeltaReduce.PublicSnapshot",
        "import DeltaReduce.PublicReachabilityExamples",
        "namespace DeltaReduce.PublicSnapshotVectors",
        (
            "open NativeBinding NativeGraphVectors NativeVoteVectors "
            "PublicJournal PublicJournalVectors"
        ),
        "open PublicRecovery PublicRecoveryVectors PublicSnapshot",
        "abbrev Bytes := NativeBinding.Bytes",
        "set_option maxRecDepth 1000000",
        "set_option maxHeartbeats 0",
        "def exportTrust : ExportTrust := ⟨fun _ _ _ _ => True⟩ -- synthetic, not authentication",
        f"def contract : ContentId := {content_id(trace['round_contract']['contract_id'])}",
    ]
    sources, cases = [], {}
    for i, event in enumerate(events):
        snap_id = event["arithmetic_witness"]["snapshot_id"]
        snapshot = native.snapshots[snap_id]
        raw = n.canonical(snapshot)
        anchor = "parameterAnchor" if i < 2 else "anchor"
        slot = event["durable_sequence"] - 1
        lines += [
            f"def id{i} : ContentId := {content_id(snap_id)}",
            f"def bytes{i} : Bytes := {byte_list(raw)}",
            (
                f"def hashInput{i} : Bytes := "
                f"{byte_list(b'deltareduce.native-snapshot-witness.v1' + bytes([0]) + raw)}"
            ),
            f"def source{i} : Exported exportTrust := {{",
            (
                f"  anchor := {anchor}, metadata := metadata{i}, header := "
                f"⟨{content_id(snapshot['prior_state_root'])}, contract, "
                f"{event['durable_sequence']}⟩"
            ),
            f"  bytes := bytes{i}, provenance := True.intro }}",
            f"def event{i} : PublicSnapshot.Event := {{",
            (
                f"  envelope := s{slot}.envelope, validator := true, view := "
                f"{event['view']}, logicalTime := {event['logical_time']}"
            ),
            (
                f"  priorRoot := {content_id(event['prior_state_root'])}, "
                f"nextRoot := {content_id(event['next_state_root'])}"
            ),
            (
                f"  sequence := some {event['durable_sequence']}, outcome := "
                f".accepted, snapshotId := id{i}, command := command{i} }}"
            ),
        ]
        sources.append({"snapshot_id": snap_id, "sequence": event["durable_sequence"]})
        cases[f"snapshot{i}ExactBytes"] = (
            f"encode {anchor} metadata{i} source{i}.header = some bytes{i}"
        )
        cases[f"snapshot{i}ExactHashPreimage"] = f"preimage bytes{i} = hashInput{i}"
    lines += [
        "def env : PublicSnapshot.Environment codec syntheticTrust voteTrust exportTrust where",
        "  recovery := PublicRecoveryVectors.env",
        (
            "  snapshots id := if id = id0 then some source0 else if id = "
            "id1 then some source1 else if id = id2 then some source2 "
            "else none"
        ),
        (
            "  sha256 bytes := if bytes = hashInput0 then id0 else if "
            "bytes = hashInput1 then id1 else if bytes = hashInput2 then "
            "id2 else []"
        ),
        "-- Rehashed mutant source is still synthetic; genuine producer provenance is a premise.",
        (
            "def rehashedEnv (source : Exported exportTrust) : "
            "PublicSnapshot.Environment codec syntheticTrust voteTrust "
            "exportTrust := { env with"
        ),
        "  snapshots := fun id => if id = id0 then some source else none",
        "  sha256 := fun bytes => if bytes = preimage source.bytes then id0 else [] }",
        "def recode (source : Exported exportTrust) : Exported exportTrust := { source with",
        (
            "  bytes := (encode source.anchor source.metadata "
            "source.header).getD [], provenance := True.intro }"
        ),
    ]
    for i, slot in enumerate([4, 5, 7]):
        call = f"bindFirst env (machineAt {slot}) contract [metadata{i}.parentCertificate] s{slot}"
        lines += [f"def bound{i} := {call} event{i} exposedStages"]
        cases[f"snapshot{i}Loads"] = f"(load env id{i}).isSome = true"
        cases[f"event{i}BindsNativeInputs"] = f"bound{i}.isSome = true"
        for name, mutation in [
            ("WrongPrior", "priorRoot := List.replicate 32 0"),
            ("WrongView", f"view := event{i}.view + 1"),
            ("WrongTime", f"logicalTime := event{i}.logicalTime + 1"),
            ("WrongSequence", f"sequence := some {slot + 2}"),
            ("WrongCommand", f"command := command{i} ++ [32]"),
            ("NonValidator", "validator := false"),
            ("MissingSnapshot", "snapshotId := List.replicate 32 0"),
        ]:
            cases[f"event{i}{name}Rejected"] = (
                f"({call} {{ event{i} with {mutation} }} exposedStages).isNone = true"
            )
        cases[f"event{i}MissingParentRejected"] = (
            f"(bindFirst env (machineAt {slot}) contract [] s{slot} "
            f"event{i} exposedStages).isNone = true"
        )
        cases[f"event{i}WrongContractRejected"] = (
            f"(bindFirst env (machineAt {slot}) (List.replicate 32 0) "
            f"[metadata{i}.parentCertificate] s{slot} event{i} "
            f"exposedStages).isNone = true"
        )
    lines += [
        (
            "def executed0 := executeFirst env (machineAt 4) contract "
            "[metadata0.parentCertificate] s4 event0 exposedStages "
            "observed5"
        ),
        (
            "def unknownEvent : PublicSnapshot.Event := { event0 with "
            "outcome := .fault, sequence := none, nextRoot := "
            "event0.priorRoot }"
        ),
        'def unknownStages := ["VALIDATED", "APPENDED", "UNKNOWN"]',
        (
            "def unknownExecution := executeFirst env (machineAt 4) "
            "contract [metadata0.parentCertificate] s4 unknownEvent "
            "unknownStages (unknownOutput 4)"
        ),
    ]
    cases.update(
        {
            "firstExecutionPreservesOriginalSlot": (
                "executed0.map (fun r => r.final) = some { machineAt 5 with sent := [s4] }"
            ),
            "unknownExecutionPreservesUnresolvedPrefix": (
                "unknownExecution.map (fun r => r.final) = some { machineAt 4 "
                "with mode := .mustCrash, pending := some s4 }"
            ),
            "unknownCannotReportKnownSequence": (
                "(bindFirst env (machineAt 4) contract "
                "[metadata0.parentCertificate] s4 { unknownEvent with "
                "sequence := some 4 } unknownStages).isNone = true"
            ),
            "unknownCannotChangePublicRoot": (
                "(bindFirst env (machineAt 4) contract "
                "[metadata0.parentCertificate] s4 { unknownEvent with "
                "nextRoot := event0.nextRoot } unknownStages).isNone = true"
            ),
            "rawByteSubstitutionRejected": (
                "(load (rehashedEnv { source0 with bytes := bytes0 ++ [32], "
                "provenance := True.intro }) id0).isNone = true"
            ),
        }
    )
    for name, change in [
        ("Sequence", "header := { source0.header with sequence := 6 }"),
        ("Current", "anchor := { parameterAnchor with currentModelHash := List.replicate 32 0 }"),
        ("Metadata", "metadata := { metadata0 with logicalTime := metadata0.logicalTime + 1 }"),
        ("Projection", "metadata := { metadata0 with projection := anchor.authority }"),
    ]:
        lines += [
            f"def changed{name} := recode {{ source0 with {change}, provenance := True.intro }}"
        ]
        cases[f"rehashed{name}StillLoads"] = f"(load (rehashedEnv changed{name}) id0).isSome = true"
        cases[f"rehashed{name}NativeBindingRejected"] = (
            f"(bindFirst (rehashedEnv changed{name}) (machineAt 4) "
            f"contract [metadata0.parentCertificate] s4 event0 "
            f"exposedStages).isNone = true"
        )
    lines += [f"theorem {name} : {statement} := by decide" for name, statement in cases.items()]
    lines += [
        (
            "theorem firstExecutionReachable (result : Executed env "
            "(machineAt 4) contract [metadata0.parentCertificate] s4 "
            "event0 exposedStages observed5) :"
        ),
        (
            '    PublicReachability.Reachable env.recovery "validator-1" '
            "(nativeCurrent anchor) result.final :="
        ),
        "  executionPreservesReachability PublicReachabilityExamples.fourReachable result",
        "end DeltaReduce.PublicSnapshotVectors",
        "",
    ]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8", newline="\n")
    evidence_path.write_bytes(
        n.canonical(
            {
                "schema_version": "1.0.0",
                "native_sha256": native.sha256,
                "sources": sources,
                "kernel_examples": list(cases),
                "scope": (
                    "Existing snapshot v1 exact bytes/preimages and first-event "
                    "binding; finite SHA/codec and synthetic exporter trust; "
                    "state roots remain opaque fixture labels, not derived state "
                    "hashes."
                ),
            }
        )
        + b"\n"
    )
    print(f"generated {len(cases)} snapshot kernel examples")


if __name__ == "__main__":
    generate()
