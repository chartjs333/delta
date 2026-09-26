"""Small component proofs from original ISC bytes; finite SHA samples only."""

import hashlib
import json
from pathlib import Path

import native_policy_codec as codec
from check_native_isc_admission import original
from generate_native_policy_schema import format_of, lean_value
from generate_native_state_vectors import envelope
from generate_native_vote_codec_vectors import text
from generate_native_wal_lean import lit

ROOT = Path(__file__).resolve().parents[2]


def generate():
    p, s, _ = original()
    raw = envelope(5, sorted(s.items()))
    out = [
        "import DeltaReduce.NativeIscAdmission",
        "import DeltaReduce.NativeVoteCodecVectors",
        "",
        "/-! Exact original ISC components. Three finite SHA samples are not authentication. -/",
        "namespace DeltaReduce.NativeIscAdmissionVectors",
        "open NativeReceiptBytes NativeIscAdmission NativePolicyCodec NativePolicySchema",
        (
            "open NativeConfigAdmission (encodedField encodedCons encodedVect"
            "or Label HeaderChecks RuntimeFacts)"
        ),
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 1000000",
        "",
    ]

    def add(s):
        out.append(s)

    def add_template(template, **values):
        add(template.format(**values))

    add("def tree : Value := " + lean_value("policy", p))
    add("def snapshot : Value := " + lean_value("snapshot", p["snapshot"]))
    c = p["candidates"][0]
    add("def parents : Value := " + lean_value("parents", c["parents"]))

    def asc(x):
        return "(NativeVoteBytes.ascii " + json.dumps(x) + ")"

    add(
        "def candidate : NativePolicyBytes.Candidate := ⟨2,"
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
        "theorem policyEncoded : NativePolicyCodec.encode fmtPolicy "
        "tree = some policyBody := " + whole
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
    add(
        "def state : NativeStateBytes.State := ⟨wire,"
        + ",".join(s[k] for k in ["durable_sequence", "height", "view"])
        + "⟩"
    )
    add("def stateRaw : Bytes := " + lit(raw))
    terms = []
    for i, x in enumerate(sorted({v for kv in s.items() for v in kv if type(v) is str})):
        add(f"theorem text{i} : NativeVoteBytes.textBytes ({asc(x)}) = {lit(text(x))} := by decide")
        terms.append(f"text{i}")
    add(
        "theorem statePayload : NativeStateBytes.payload (NativeStateBytes.stateFields "
        "wire) = "
        + lit(raw[12:])
        + (
            " := by\n  simp only "
            + (
                "[NativeStateBytes.payload,NativeStateBytes.stateFields,wire,Nati"
                "veStateBytes.encodeFields,NativeStateBytes.scalarBytes,NativeVot"
                "eBytes.nativeSemantics,"
            )
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
    import native_isc_body as isc

    native_body = isc.from_fields(p["snapshot"]["input_set_bodies"][0])
    ctx = native_body.context
    add(
        "def inputContext : NativeInputSetBody.Context := ⟨"
        + ",".join(
            str(getattr(ctx, k)) if k in ["height", "view"] else asc(getattr(ctx, k))
            for k in ctx.__annotations__
        )
        + "⟩"
    )
    tuples = []
    for i, t in enumerate(native_body.tuples):
        add(
            f"def tuple{i} : NativeInputSetBody.Tuple := ⟨"
            + ",".join(asc(getattr(t, k)) for k in t.__annotations__)
            + "⟩"
        )
        tuples.append(f"tuple{i}")
    add(
        "def inputBody : NativeInputSetBody.Body := ⟨inputContext,"
        + asc(native_body.input_root)
        + ",["
        + ",".join(tuples)
        + "]⟩"
    )
    add(
        "def inputTree : Value := "
        + lean_value("input_set_body", p["snapshot"]["input_set_bodies"][0])
    )
    add("theorem bodyTree : NativeInputSetBody.bodyValue inputBody = inputTree := by rfl")
    add(
        "theorem bodyRead : NativeInputSetBody.readBody inputTree = some "
        "inputBody := by rw [← bodyTree]; exact NativeInputSetBody.bodyRe"
        "ad _"
    )
    terms = []
    strs = set(x for x in vars(ctx).values() if isinstance(x, str)) | {native_body.input_root}
    for t in native_body.tuples:
        strs.update(vars(t).values())
    for i, x in enumerate(sorted(strs)):
        add(
            f"theorem hashText{i} : NativeInputSetBody.text64 ({asc(x)}) = "
            f"{lit(isc.text(x))} := by decide"
        )
        terms.append(f"hashText{i}")
    add("def inputRaw : Bytes := " + lit(native_body.encode()))
    add(
        (
            "theorem inputEncoded : NativeInputSetBody.bodyBytes inputBody = "
            "inputRaw := by\n  simp only [NativeInputSetBody.bodyBytes,NativeI"
            "nputSetBody.contextBytes,NativeInputSetBody.tupleBytes,inputBody"
            ",inputContext,"
        )
        + ",".join(tuples)
        + ",List.map_cons,List.map_nil,List.flatten_cons,List.flatten_nil,"
        + ",".join(terms)
        + "]\n  rfl"
    )
    state_pre = b"deltareduce:003:round-state:v1\0" + raw
    rr = p["round_id"].encode()
    context_pre = b"deltareduce.vote-context.isc.v1\0" + len(rr).to_bytes(8, "big") + rr
    add(
        (
            "def sha (b : Bytes) : Bytes :=\n  if b = NativeStateBytes.content"
            "Preimage NativeStateBytes.stateDomain stateRaw then "
        )
        + lit(hashlib.sha256(state_pre).digest())
        + "\n  else if b = iscPreimage policy.round then "
        + lit(hashlib.sha256(context_pre).digest())
        + (
            "\n  else if b = NativeStateBytes.contentPreimage NativeInputSetBo"
            "dy.bodyDomain inputRaw then "
        )
        + lit(hashlib.sha256(isc.DOMAIN + native_body.encode()).digest())
        + " else []"
    )
    add(
        (
            "theorem snapshotHash : NativeStateBytes.contentId sha NativeStat"
            "eBytes.stateDomain (NativeStateBytes.encodeState state.wire) = s"
            "ome ("
        )
        + asc(p["snapshot"]["state_id"])
        + (
            ") := by\n  change NativeStateBytes.contentId sha NativeStateBytes"
            ".stateDomain (NativeStateBytes.encodeState wire) = _\n  rw [state"
            "Encoded]\n  simp only [NativeStateBytes.contentId,sha,↓reduceIte]"
            "; rfl"
        )
    )
    add(
        "theorem contextHash : iscContext sha policy.round = some candida"
        "te.context := by\n  unfold iscContext sha\n  have diff : iscPreima"
        "ge policy.round ≠ NativeStateBytes.contentPreimage NativeStateBy"
        "tes.stateDomain stateRaw := by decide\n  simp only [if_neg diff,↓"
        "reduceIte]; rfl"
    )
    add(
        "theorem inputHash : NativeInputSetBody.bodyId sha inputBody = so"
        "me candidate.body := by\n  unfold NativeInputSetBody.bodyId\n  rw "
        "[inputEncoded]\n  unfold NativeStateBytes.contentId sha\n  have a "
        ": NativeStateBytes.contentPreimage NativeInputSetBody.bodyDomain"
        " inputRaw ≠ NativeStateBytes.contentPreimage NativeStateBytes.st"
        "ateDomain stateRaw := by decide\n  have b : NativeStateBytes.cont"
        "entPreimage NativeInputSetBody.bodyDomain inputRaw ≠ iscPreimage"
        " policy.round := by decide\n  simp only [if_neg a,if_neg b,↓reduc"
        "eIte]; rfl"
    )
    add(
        "theorem inputValid : NativeInputSetBody.BodyValid (expected policy state "
        + asc(p["snapshot"]["parameter_schema_id"])
        + " "
        + asc(p["snapshot"]["arithmetic_profile_id"])
        + ") inputBody := by decide"
    )
    add("def checked : NativeInputSetBody.Checked := ⟨inputBody,candidate.body,inputTree⟩")
    add(
        "theorem inputChecked : NativeInputSetBody.check sha (expected policy state "
        + asc(p["snapshot"]["parameter_schema_id"])
        + " "
        + asc(p["snapshot"]["arithmetic_profile_id"])
        + (
            ") inputTree = some checked := NativeInputSetBody.checkFromCompon"
            "ents bodyRead inputHash inputValid"
        )
    )
    vals = [
        "policy",
        "state",
        "candidate",
        asc(c["parents"]["parent_checkpoint_id"]),
        asc(p["snapshot"]["parameter_schema_id"]),
        asc(p["snapshot"]["arithmetic_profile_id"]),
        asc(p["snapshot"]["required_accumulator_proof_id"]),
    ]
    vals += [
        "[" + ",".join(asc(x) for x in p["snapshot"][k]) + "]"
        for k in ["proposed_round_config_ids", "finalized_round_config_ids"]
    ]
    vals += [
        asc(p["snapshot"]["state_id"]),
        "candidate.context",
        "[inputTree]",
        "[checked]",
        "[candidate.body]",
    ]
    add("def bound : Bound := ⟨" + ",".join(vals) + "⟩")
    add("theorem boundChecks : Checks bound := by decide")
    add(
        (
            "theorem originalBinding : bindIsc sha policy state = some bound "
            ":= by\n  apply bindFromComponents\n  refine ⟨rfl,rfl,rfl,rfl,snaps"
            "hotHash,by decide,rfl,rfl,rfl,rfl,rfl,rfl,rfl,?_,rfl,contextHash"
            ",boundChecks⟩\n  change NativeInputSetBody.checkAll sha (expected"
            " policy state ("
        )
        + asc(p["snapshot"]["parameter_schema_id"])
        + ") ("
        + asc(p["snapshot"]["arithmetic_profile_id"])
        + (
            ")) [inputTree] = some [checked]\n  simp only [NativeInputSetBody."
            "checkAll,inputChecked,bind,Option.bind]"
        )
    )
    add(
        "theorem originalPrepare : prepare sha policyRaw stateRaw = some "
        "bound := by\n  simp only [prepare,policyDecoded,stateDecoded,bind"
        ",Option.bind,originalBinding]"
    )
    add("def facts : RuntimeFacts := ⟨10,true,false,false,1⟩")
    add(
        (
            "theorem originalChecks : VoteChecks bound facts NativeVoteCodecV"
            "ectors.vote2 := ⟨NativeVoteCodecVectors.valid2,"
        )
        + ",".join(["by decide"] * 16)
        + "⟩"
    )
    add(
        "theorem originalAllBytes : fromBytes sha policyRaw stateRaw "
        "NativeReceiptVectors.frame2 facts = some (bound,NativeVoteCodecVectors.vote2) "
        ":= fromComponents originalPrepare NativeVoteCodecVectors.parsed2 "
        "originalChecks"
    )

    tests = [
        ("liveNotReady", "ready := false"),
        ("invalidated", "invalidated := true"),
        ("expired", "tick := 100"),
        ("wrongSequence", "expectedSequence := 2"),
        ("recoveryInvalidated", "ready := false,recovery := true,invalidated := true"),
    ]
    for name, update in tests:
        close = "simp_all [facts]"
        if name == "expired":
            close = "exact (by decide : ¬ (100 < bound.policy.hardDeadline)) deadline"
        if name == "wrongSequence":
            close = "exact (by decide : NativeVoteCodecVectors.vote2.sequence ≠ 2) sequence"
        add_template(
            "theorem {name} : (checkVote bound {{facts with {update}}} Na"
            "tiveVoteCodecVectors.vote2).isNone = true := by\n  unfold che"
            "ckVote\n  have bad : ¬ VoteChecks bound {{facts with {update}"
            "}} NativeVoteCodecVectors.vote2 := by\n    intro h\n    rcases"
            " h with ⟨_,_,_,_,_,_,_,_,_,_,sequence,ready,invalid,_,deadli"
            "ne,_⟩\n    {close}\n  rw [if_neg bad]; rfl",
            name=name,
            update=update,
            close=close,
        )
    add(
        (
            "theorem recoveryNotReady : (checkVote bound {facts with ready :="
            " false,recovery := true} NativeVoteCodecVectors.vote2).isSome = "
            "true := by\n  have valid : VoteChecks bound {facts with ready := "
            "false,recovery := true} NativeVoteCodecVectors.vote2 := ⟨NativeV"
            "oteCodecVectors.valid2,"
        )
        + ",".join(["by decide"] * 16)
        + "⟩\n  rw [checkVote,if_pos valid]; rfl"
    )
    for i in [1, 3, 4, 5, 6, 7, 8, 9]:
        add_template(
            "theorem otherAction{i} : (checkVote bound facts NativeVoteCo"
            "decVectors.vote{i}).isNone = true := by\n  unfold checkVote\n "
            " have bad : ¬ VoteChecks bound facts NativeVoteCodecVectors."
            "vote{i} := by\n    intro h; have wrong : NativeVoteCodecVecto"
            'rs.vote{i}.wire.kind ≠ NativeConfigAdmission.ascii "ISC" := '
            "by decide\n    exact wrong h.2.1\n  rw [if_neg bad]; rfl",
            i=i,
        )
    add("theorem missingClosed : ¬ Checks {bound with closed := []} := by decide")
    add("theorem missingBody : ¬ Checks {bound with bodies := []} := by decide")
    add(
        "theorem wrongSchema : ¬ NativeInputSetBody.BodyValid {inputConte"
        "xt with schema := []} inputBody := by decide"
    )
    add(
        "theorem emptyTuples : ¬ NativeInputSetBody.BodyValid inputContex"
        "t {inputBody with tuples := []} := by decide"
    )
    add(
        "theorem duplicateTuples : ¬ NativeInputSetBody.BodyValid inputCo"
        "ntext {inputBody with tuples := inputBody.tuples ++ inputBody.tu"
        "ples} := by decide"
    )
    add(
        "theorem sameTicketDifferentCommitmentAllowed : NativeInputSetBod"
        "y.BodyValid inputContext {inputBody with tuples := [tuple0,{tupl"
        'e0 with commitment := NativeVoteBytes.ascii "sha256:eeeeeeeeeeee'
        'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"}]} := by d'
        "ecide"
    )
    add("end DeltaReduce.NativeIscAdmissionVectors\n")
    (ROOT / "formal/proofs/DeltaReduce/NativeIscAdmissionVectors.lean").write_text(
        "\n\n".join(out), encoding="utf-8", newline="\n"
    )


if __name__ == "__main__":
    generate()
