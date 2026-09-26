"""Small component proofs from original CONFIG bytes; finite SHA samples only."""

import hashlib
import json
from pathlib import Path

import native_policy_codec as codec
from check_native_config_admission import original
from generate_native_policy_schema import format_of, lean_value
from generate_native_state_vectors import envelope
from generate_native_vote_codec_vectors import text
from generate_native_wal_lean import lit

ROOT = Path(__file__).resolve().parents[2]


def generate():
    p, s, _ = original()
    raw = envelope(5, sorted(s.items()))
    out = [
        "import DeltaReduce.NativeConfigAdmission",
        "import DeltaReduce.NativeVoteCodecVectors",
        "",
        "/-! Exact original CONFIG components. Two finite SHA samples are not authentication. -/",
        "namespace DeltaReduce.NativeConfigAdmissionVectors",
        "open NativeReceiptBytes NativeConfigAdmission NativePolicyCodec NativePolicySchema",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 1000000",
        "",
    ]

    def add(s):
        out.append(s)

    add("def tree : Value := " + lean_value("policy", p))
    add("def snapshot : Value := " + lean_value("snapshot", p["snapshot"]))
    c = p["candidates"][0]
    add("def parents : Value := " + lean_value("parents", c["parents"]))

    def asc(x):
        return "NativeVoteBytes.ascii " + json.dumps(x)

    add(
        "def candidate : NativePolicyBytes.Candidate := ⟨1,"
        + ",".join(
            [
                asc(c["body_hash"]),
                asc(c["context_id"]),
                str(c["height"]),
                str(c["view"]),
                "parents",
                lean_value("candidate", c),
            ]
        )
        + "⟩"
    )
    args = [
        asc(p["local_validator_id"]),
        asc(p["validator_epoch_id"]),
        "[" + ",".join(asc(x) for x in p["validator_ids"]) + "]",
        "1",
        asc(p["round_id"]),
        asc(p["round_config_id"]),
        asc(p["configured_abort_reason"]),
        str(p["initial_logical_tick"]),
        str(p["soft_deadline_tick"]),
        str(p["hard_deadline_tick"]),
        "snapshot",
        "[candidate]",
        "tree",
    ]
    add("def policy : NativePolicyBytes.Policy := ⟨" + ",".join(args) + "⟩")
    add("theorem extracted : NativePolicyBytes.extract tree = some policy := by rfl")
    body = codec.encode_value("policy", p)
    add("def policyBody : Bytes := " + lit(body))
    cache = {}

    def encode_proof(kind, value):
        key = (kind, json.dumps(value, sort_keys=True))
        if key in cache:
            return cache[key]
        expr = lean_value(kind, value)
        raw = codec.encode_value(kind, value)
        vec = codec.vector_shape(kind)
        if kind in codec.SCHEMAS:
            tail = "(by rfl)"
            for k, t in reversed(codec.SCHEMAS[kind]):
                head = encode_proof(t, value[k])
                tail = f"(encodedField {head} {tail})"
            proof = "exact " + tail
        elif vec:
            tail = "(by rfl)"
            for v in reversed(value):
                head = encode_proof(vec[0], v)
                tail = f"(encodedCons {head} {tail})"
            proof = f"exact encodedVector (by decide) {tail}"
        else:
            proof = "decide"
        name = "encoding" + str(len(cache))
        cache[key] = name
        add(
            f"theorem {name} : NativePolicyCodec.encode ({format_of(kind)}) "
            f"({expr}) = some {lit(raw)} := by\n  {proof}"
        )
        return name

    whole = encode_proof("policy", p)
    add(
        "theorem policyEncoded : NativePolicyCodec.encode fmtPolicy tree = some policyBody := "
        + whole
    )
    add("theorem canonical : NativePolicyBytes.Canonical policy := by decide")
    add("def policyRaw : Bytes := NativePolicyBytes.header ++ policyBody")
    add(
        "theorem policyDecoded : NativePolicyBytes.decodePolicy policyRaw = "
        "some (tree,policy) :=\n  NativePolicyBytes.encoded policyEncoded "
        "extracted canonical (by decide)"
    )
    keys = [
        "available_ticket_count",
        "committed_ticket_count",
        "config_id",
        "durable_sequence",
        "height",
        "parent_checkpoint_id",
        "phase",
        "round_id",
        "state_root",
        "ticket_count",
        "view",
    ]
    args = [str(s[k]) if type(s[k]) is int else asc(s[k]) for k in keys]
    add("def wire : NativeStateBytes.WireState := ⟨" + ",".join(args) + "⟩")
    add("def state : NativeStateBytes.State := ⟨wire,0,1,0⟩")
    add("def stateRaw : Bytes := " + lit(raw))
    terms = []
    for i, x in enumerate(sorted({v for kv in s.items() for v in kv if type(v) is str})):
        add(f"theorem text{i} : NativeVoteBytes.textBytes ({asc(x)}) = {lit(text(x))} := by decide")
        terms.append(f"text{i}")
    add(
        "theorem statePayload : NativeStateBytes.payload (NativeStateBytes.stateFields wire) = "
        + lit(raw[12:])
        + (
            " := by\n  simp only "
            "[NativeStateBytes.payload,NativeStateBytes.stateFields,wire,NativeStateBytes.encodeFields,NativeStateBytes.scalarBytes,NativeVoteBytes.nativeSemantics,"
        )
        + ",".join(terms)
        + "]\n  rfl"
    )
    add(
        "theorem stateEncoded : NativeStateBytes.encodeState wire = stateRaw "
        ":= by\n  unfold NativeStateBytes.encodeState "
        "NativeStateBytes.encodeEnvelope; rw [statePayload]; rfl"
    )
    add(
        "theorem stateFrame : NativeStateBytes.EnvelopeValid 5 "
        "(NativeStateBytes.stateFields wire) := by\n  constructor; · decide\n "
        " change (NativeStateBytes.encodeState wire).length ≤ "
        "NativeVoteBytes.maxEnvelope\n  rw [stateEncoded]; decide"
    )
    add(
        "theorem stateValid : NativeStateBytes.StateValid state := ⟨stateFrame,"
        + ",".join(["by decide"] * 11)
        + "⟩"
    )
    add(
        "theorem stateDecoded : NativeStateBytes.decodeState stateRaw = some "
        "state := NativeStateBytes.stateFromBytes state stateRaw stateValid "
        "stateEncoded"
    )
    state_pre = b"deltareduce:003:round-state:v1\0" + raw
    ep = p["validator_epoch_id"].encode()
    context_pre = (
        b"deltareduce.vote-context.config.v1\0"
        + (1).to_bytes(8, "big")
        + len(ep).to_bytes(8, "big")
        + ep
    )
    add(
        "def sha (b : Bytes) : Bytes :=\n  if b = "
        "NativeStateBytes.contentPreimage NativeStateBytes.stateDomain "
        "stateRaw then "
        + lit(hashlib.sha256(state_pre).digest())
        + "\n  else if b = configPreimage 1 policy.epoch then "
        + lit(hashlib.sha256(context_pre).digest())
        + " else []"
    )
    add(
        "theorem snapshotHash : NativeStateBytes.contentId sha "
        "NativeStateBytes.stateDomain (NativeStateBytes.encodeState "
        "state.wire) = some ("
        + asc(p["snapshot"]["state_id"])
        + (
            ") := by\n  change NativeStateBytes.contentId sha "
            "NativeStateBytes.stateDomain (NativeStateBytes.encodeState wire) = "
            "_\n  rw [stateEncoded]\n  simp only "
            "[NativeStateBytes.contentId,sha,↓reduceIte]; rfl"
        )
    )
    add(
        "theorem contextHash : configContext sha 1 policy.epoch = some "
        "candidate.context := by\n  unfold configContext sha\n  have diff : "
        "configPreimage 1 policy.epoch ≠ NativeStateBytes.contentPreimage "
        "NativeStateBytes.stateDomain stateRaw := by decide\n  simp only "
        "[if_neg diff,↓reduceIte]; rfl"
    )
    vals = [
        "policy",
        "state",
        "candidate",
        asc(c["parents"]["parent_checkpoint_id"]),
        asc(p["snapshot"]["parameter_schema_id"]),
        asc(p["snapshot"]["arithmetic_profile_id"]),
        asc(p["snapshot"]["required_accumulator_proof_id"]),
        "[" + asc(p["round_config_id"]) + "]",
        "[]",
        asc(p["snapshot"]["state_id"]),
        "candidate.context",
    ]
    add("def bound : Bound := ⟨" + ",".join(vals) + "⟩")
    add("theorem boundChecks : Checks bound := by decide")
    add(
        "theorem originalBinding : bindConfig sha policy state = some bound := by\n"
        "  apply bindConfigComplete\n"
        "  exact ⟨rfl,rfl,rfl,by rfl,snapshotHash,by decide,by rfl,by rfl,"
        "by rfl,by rfl,by rfl,by rfl,contextHash,boundChecks⟩"
    )
    add(
        "theorem originalPrepare : prepare sha policyRaw stateRaw = some "
        "bound := by\n  simp only "
        "[prepare,policyDecoded,stateDecoded,bind,Option.bind,originalBinding]"
    )
    add("def facts : RuntimeFacts := ⟨10,true,false,false,1⟩")
    add(
        "theorem originalChecks : VoteChecks bound facts "
        "NativeVoteCodecVectors.vote1 := by\n  exact "
        "⟨NativeVoteCodecVectors.valid1," + ",".join(["by decide"] * 16) + "⟩"
    )
    add(
        "theorem originalAllBytes : fromBytes sha policyRaw stateRaw "
        "NativeReceiptVectors.frame1 facts = some "
        "(bound,NativeVoteCodecVectors.vote1) :=\n  fromComponents "
        "originalPrepare NativeVoteCodecVectors.parsed1 originalChecks"
    )
    tests = [
        ("liveNotReady", "{facts with ready := false}"),
        ("invalidated", "{facts with invalidated := true}"),
        ("expired", "{facts with tick := 100}"),
        ("wrongSequence", "{facts with expectedSequence := 2}"),
        ("invalidatedRecovery", "{facts with recovery := true,ready := false,invalidated := true}"),
        ("expiredRecovery", "{facts with recovery := true,ready := false,tick := 100}"),
    ]
    for name, r in tests:
        add(
            f"theorem {name} : (checkVote bound ({r}) "
            f"NativeVoteCodecVectors.vote1).isNone = true := by decide"
        )
    add(
        "theorem recoveryWithoutReady : (checkVote bound "
        "{facts with recovery := true,ready := false} "
        "NativeVoteCodecVectors.vote1).isSome = true := by decide"
    )
    add(
        "theorem beforeDeadline : (checkVote bound {facts with tick := 99} "
        "NativeVoteCodecVectors.vote1).isSome = true := by decide"
    )
    for i in range(2, 10):
        add(
            f"theorem otherAction{i} : (checkVote bound facts "
            f"NativeVoteCodecVectors.vote{i}).isNone = true := by decide"
        )
    add(
        "theorem differentCheckpoint : (checkVote "
        "{bound with checkpoint := []} facts "
        "NativeVoteCodecVectors.vote1).isNone = true := by decide"
    )
    add('theorem badLabel : ¬ Label (NativeConfigAdmission.ascii "bad round") := by decide')
    add("theorem zeroHeight : ¬ HeaderChecks policy {state with height := 0} := by decide")
    add(
        "theorem badCommittee : ¬ HeaderChecks "
        "{policy with validators := [policy.localValidator,[]]} state := by "
        "decide"
    )
    add("end DeltaReduce.NativeConfigAdmissionVectors\n")
    (ROOT / "formal/proofs/DeltaReduce/NativeConfigAdmissionVectors.lean").write_text(
        "\n\n".join(out), encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    generate()
