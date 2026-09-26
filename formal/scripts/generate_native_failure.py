"""Exact original native VIEW/ABORT snapshot components; no live admission claim."""

import hashlib
import json
from pathlib import Path

import native_policy_codec as codec
from formal_artifacts import canonical_json_bytes, load_json_strict
from generate_native_policy_schema import format_of, lean_value
from generate_native_wal_lean import lit

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "formal/proofs/DeltaReduce/NativeFailureVectors.lean"
PIN = "d82c14dda8356bfebc1cc1febe3c2fd09c3393b467cc99bacd565b506a91d2ea"
KINDS = ("timeout", "view_change", "abort_request", "abort_body")
LIST_FIELDS = (
    "round_config_ids",
    "input_set_ids",
    "eligibility_ids",
    "aggregation_plan_ids",
    "parameter_ids",
    "aggregate_root_ids",
    "apply_ids",
)
DOMAINS = ("deltareduce.vote.view-change-body.v1", "deltareduce.vote.abort-body.v1")


def u64(n):
    return n.to_bytes(8, "big")


def text64(s):
    raw = s.encode("ascii")
    return u64(len(raw)) + raw


def body_bytes(kind, obj):
    if kind == "view_change":
        return text64(obj["round_id"]) + b"".join(
            u64(obj[k]) for k in ("height", "from_view", "to_view", "soft_deadline_tick")
        )
    if kind != "abort_body":
        raise ValueError("unsupported binary body")
    return (
        text64(obj["round_id"])
        + text64(obj["validator_epoch_id"])
        + b"".join(u64(obj[k]) for k in ("height", "view", "hard_deadline_tick"))
        + text64(obj["parent_checkpoint_id"])
        + text64(obj["reason_code"])
        + b"".join(u64(len(obj[k])) + b"".join(text64(s) for s in obj[k]) for k in LIST_FIELDS)
    )


def source():
    observed = load_json_strict(
        ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
    )
    if hashlib.sha256(canonical_json_bytes(observed)).hexdigest() != PIN:
        raise ValueError("original native failure policy observation changed")
    result = []
    for name, kind, field, domain in zip(
        ("codec-VIEW_CHANGE", "codec-ABORT"),
        ("view_change", "abort_body"),
        ("view_change_bodies", "abort_bodies"),
        DOMAINS,
        strict=True,
    ):
        row = next(r for r in observed["observed"] if r["name"] == name)
        raw = bytes.fromhex(row["policy_hex"])
        policy = codec.decode(raw)
        if codec.HEADER + codec.encode_value("policy", policy) != raw:
            raise ValueError("original policy bytes changed")
        body = policy["snapshot"][field][0]
        pre = domain.encode() + b"\0" + body_bytes(kind, body)
        ident = "sha256:" + hashlib.sha256(pre).hexdigest()
        if policy["candidates"][0]["body_hash"] != ident:
            raise ValueError("original body hash does not match binary preimage")
        result.append((policy, body, pre, ident))
    return result


def generate():
    data = source()
    asc = lambda x: "(NativeVoteBytes.ascii " + json.dumps(x) + ")"  # noqa: E731
    seq = lambda xs: "[" + ",".join(map(asc, xs)) + "]"  # noqa: E731
    view, abort = data[0][1], data[1][1]
    out = [
        "import DeltaReduce.NativeFailureSection",
        "import DeltaReduce.NativeConfigAdmissionVectors",
        "",
        "/-! Pinned original native wire components and two finite SHA samples.",
        "Snapshot checks do not prove candidate authority, deadlines or QC outcomes. -/",
        "namespace DeltaReduce.NativeFailureVectors",
        (
            "open NativeReceiptBytes NativePolicyCodec NativePolicySchema "
            "NativeFailurePayload NativeFailureSection"
        ),
        "open NativeConfigAdmission (encodedField encodedCons encodedVector)",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 400000",
        "def timeout : Timeout := ⟨" + asc(view["round_id"]) + ",1,0⟩",
        "def view : ViewBody := ⟨" + asc(view["round_id"]) + ",1,0,1,50⟩",
        "def abort : AbortBody := ⟨"
        + asc(abort["round_id"])
        + ","
        + asc(abort["validator_epoch_id"])
        + ",1,0,100,"
        + asc(abort["parent_checkpoint_id"])
        + ","
        + asc(abort["reason_code"])
        + ","
        + ",".join(seq(abort[k]) for k in LIST_FIELDS)
        + "⟩",
    ]
    objects = [
        ("timeout", "timeout", data[0][0]["snapshot"]["timeout_observations"][0], "fmtTimeout"),
        ("view", "view_change", view, "fmtViewChange"),
        ("abort", "abort_body", abort, "fmtAbortBody"),
    ]
    cache = {}

    def encode(kind, value):
        key = (kind, json.dumps(value, sort_keys=True))
        if key in cache:
            return cache[key]
        vector = codec.vector_shape(kind)
        proof = "(by rfl)"
        if kind in codec.SCHEMAS:
            for field, typ in reversed(codec.SCHEMAS[kind]):
                proof = f"(encodedField {encode(typ, value[field])} {proof})"
        elif vector:
            for item in reversed(value):
                proof = f"(encodedCons {encode(vector[0], item)} {proof})"
            proof = f"(encodedVector (by decide) {proof})"
        else:
            proof = "(by decide)"
        name = f"encoding{len(cache)}"
        cache[key] = name
        out.append(
            f"theorem {name} : encode ({format_of(kind)}) ({lean_value(kind, value)}) = some "
            + lit(codec.encode_value(kind, value))
            + " := "
            + proof
        )
        return name

    for name, kind, obj, fmt in objects:
        out.extend(
            [
                f"def {name}Tree : Value := " + lean_value(kind, obj),
                f"def {name}Raw : Bytes := " + lit(codec.encode_value(kind, obj)),
                (
                    f"theorem {name}ReadExact : read{name.title()} {name}Tree = some {name} "
                    f":= {name}Read {name}"
                ),
            ]
        )
        proof = encode(kind, obj)
        out.extend(
            [
                f"theorem {name}Encoded : encode {fmt} {name}Tree = some {name}Raw := {proof}",
                (
                    f"theorem {name}Decoded : NativePolicyCodec.decode {fmt} {name}Raw = some "
                    f"{name}Tree := NativePolicyCodec.encoded {name}Encoded"
                ),
            ]
        )
    # Four original source lists and all policy fields, not a caller-supplied approval.
    for (name, _kind, _, _), (policy, _body, pre, ident) in zip(objects[1:], data, strict=True):
        out.extend(
            [
                f"def {name}Snapshot : Value := " + lean_value("snapshot", policy["snapshot"]),
                f"def {name}PolicyTree : Value := " + lean_value("policy", policy),
            ]
        )
        cand = policy["candidates"][0]
        out.append(
            f"def {name}Candidate : NativePolicyBytes.Candidate := ⟨"
            + str(cand["action"])
            + ","
            + asc(cand["body_hash"])
            + ","
            + asc(cand["context_id"])
            + ","
            + str(cand["height"])
            + ","
            + str(cand["view"])
            + ","
            + lean_value("parents", cand["parents"])
            + ","
            + lean_value("candidate", cand)
            + "⟩"
        )
        out.append(
            f"def {name}Policy : NativePolicyBytes.Policy := ⟨"
            + ",".join(
                [
                    asc(policy["local_validator_id"]),
                    asc(policy["validator_epoch_id"]),
                    seq(policy["validator_ids"]),
                    str(policy["role"]),
                    asc(policy["round_id"]),
                    asc(policy["round_config_id"]),
                    asc(policy["configured_abort_reason"]),
                    str(policy["initial_logical_tick"]),
                    str(policy["soft_deadline_tick"]),
                    str(policy["hard_deadline_tick"]),
                    name + "Snapshot",
                    "[" + name + "Candidate]",
                    name + "PolicyTree",
                ]
            )
            + "⟩"
        )
        out.extend(
            [
                (
                    f"theorem {name}PolicySource : NativePolicyBytes.extract {name}PolicyTree "
                    f"= some {name}Policy := by rfl"
                ),
                f"def {name}Preimage : Bytes := " + lit(pre),
                f"def {name}Hash : Bytes := " + lit(hashlib.sha256(pre).digest()),
                f"def {name}ID : Bytes := " + asc(ident),
                (
                    f"theorem {name}PreimageExact : {name}Domain ++ [0] ++ {name}Bytes {name} "
                    f"= {name}Preimage := by rfl"
                ),
            ]
        )
    out.append(
        "def sha (raw : Bytes) : Bytes := if raw = viewPreimage then viewHash "
        "else if raw = abortPreimage then abortHash else []"
    )
    for name, steps in [("view", "if_pos rfl"), ("abort", "if_neg (by decide),if_pos rfl")]:
        out.extend(
            [
                (
                    f"theorem {name}SHA : sha {name}Preimage = {name}Hash := by unfold sha; "
                    f"rw [{steps}]"
                ),
                f"theorem {name}Computed : {name}Id sha {name} = some {name}ID := by\n"
                + f"  simp only [{name}Id,NativeStateBytes.contentId,"
                + f"NativeStateBytes.contentPreimage,{name}PreimageExact,{name}SHA]\n  rfl",
                f"def {name}Row : Row "
                + ("ViewBody" if name == "view" else "AbortBody")
                + f" := ⟨{name},{name}Tree,{name}Raw,{name}ID⟩",
                f"theorem {name}Checked : checkRow "
                + (
                    "fmtViewChange readView (viewId sha)"
                    if name == "view"
                    else "fmtAbortBody readAbort (abortId sha)"
                )
                + f" {name}Tree = some {name}Row := rowFromComponents "
                + f"{name}ReadExact {name}Encoded {name}Computed",
            ]
        )
    out.extend(
        [
            "def lineage : Lineage := ⟨abort.configs,[],[],[],[],[],[]⟩",
            (
                "def viewTail : Tail := "
                "⟨lineage,[timeoutTree],[timeout],[viewTree],[viewRow],[],[],[],[]⟩"
            ),
            "def abortTail : Tail := ⟨lineage,[],[],[],[],[],[],[abortTree],[abortRow]⟩",
        ]
    )
    for name in ["view", "abort"]:
        proof = (
            f"theorem {name}TailChecked : checkTail sha {name}Policy "
            f"""NativeConfigAdmissionVectors.state = some {name}Tail := by
  apply tailFromComponents
  constructor
  · rfl
  · rfl
  · rfl
  · rfl
  · """
            + (
                "simp only [checkViews,viewTail,checkRows,viewChecked,bind,Option.bind]"
                if name == "view"
                else "rfl"
            )
            + """
  · rfl
  · rfl
  · rfl
  · """
            + (
                "rfl"
                if name == "view"
                else "simp only [checkAborts,abortTail,checkRows,abortChecked,bind,Option.bind]"
            )
            + """
  · decide"""
        )
        out.append(proof)
    out.extend(
        [
            (
                "theorem allAbortSources : LineageSource abortPolicy "
                "⟨abort.configs,abort.inputs,abort.eligibility,abort.plans,"
                "abort.parameters,abort.roots,abort.applies⟩ := "
                "completeAbortLists (row:=abortRow) abortTailChecked (by simp [abortTail])"
            ),
            (
                "theorem exactAbort : AbortExact abortPolicy "
                "NativeConfigAdmissionVectors.state lineage abort := by decide"
            ),
        ]
    )
    # Every native abort field is checked; empty original lists still cannot be substituted.
    for field in [
        "round",
        "epoch",
        "height",
        "view",
        "deadline",
        "parent",
        "reason",
        "configs",
        "inputs",
        "eligibility",
        "plans",
        "parameters",
        "roots",
        "applies",
    ]:
        value = (
            "2"
            if field in ["height", "view", "deadline"]
            else '[NativeVoteBytes.ascii "changed"]'
            if field
            in ["configs", "inputs", "eligibility", "plans", "parameters", "roots", "applies"]
            else 'NativeVoteBytes.ascii "changed"'
        )
        out.append(
            f"theorem changed{field.title()} : ¬ AbortExact abortPolicy "
            f"NativeConfigAdmissionVectors.state lineage {{abort with {field} := "
            f"{value}}} := by decide"
        )
    out.extend(
        [
            (
                "theorem timeoutDuplicate : NativePolicyBytes.strictly timeoutLT "
                "[timeout,timeout] = false := by decide"
            ),
            (
                "theorem timeoutReverse : NativePolicyBytes.strictly timeoutLT [{timeout "
                "with view:=1},timeout] = false := by decide"
            ),
            (
                "theorem timeoutLexicographic : NativePolicyBytes.strictly timeoutLT "
                "[timeout,{timeout with view:=1},{timeout with height:=2}] = true := by "
                "decide"
            ),
            "theorem timeoutOverflow : ¬ TimeoutValid {timeout with height:=256^8} := by decide",
            (
                "theorem timeoutOtherRound : TimeoutValid {timeout with "
                'round:=NativeVoteBytes.ascii "another"} := by decide'
            ),
            'def request : Request := ⟨timeout.round,NativeVoteBytes.ascii "INCOMPLETE_INPUT"⟩',
            "theorem requestAllowed : RequestValid request := by decide",
            (
                "theorem requestUnsafe : RequestValid {request with "
                'reason:=NativeVoteBytes.ascii "UNSAFE_COEFFICIENTS"} := by decide'
            ),
            (
                "theorem requestHardDeadline : ¬ RequestValid {request with "
                'reason:=NativeVoteBytes.ascii "HARD_DEADLINE"} := by decide'
            ),
            (
                "theorem requestDuplicate : NativePolicyBytes.strictly requestLT "
                "[request,request] = false := by decide"
            ),
            (
                "theorem requestReverse : NativePolicyBytes.strictly requestLT [{request "
                'with reason:=NativeVoteBytes.ascii "UNSAFE_COEFFICIENTS"},request] = '
                "false := by decide"
            ),
            (
                "theorem viewDuplicate : ¬ TailChecks viewPolicy "
                "NativeConfigAdmissionVectors.state {viewTail with "
                "views:=[viewRow,viewRow]} := by decide"
            ),
            (
                "theorem abortDuplicate : ¬ TailChecks abortPolicy "
                "NativeConfigAdmissionVectors.state {abortTail with "
                "aborts:=[abortRow,abortRow]} := by decide"
            ),
            (
                "theorem uncheckedViewEnable : TailChecks viewPolicy "
                "NativeConfigAdmissionVectors.state {viewTail with views:=[{viewRow with "
                "body:={view with toView:=99}}]} := by decide"
            ),
            (
                "theorem matchingFinalApplyIsSnapshotOnly : AbortExact abortPolicy "
                "NativeConfigAdmissionVectors.state {lineage with "
                "applies:=[abort.parent]} {abort with applies:=[abort.parent]} := by "
                "decide"
            ),
            "theorem malformedAbort : readAbort (.pair (.text []) .end) = none := by rfl",
            "theorem malformedView : readView (.pair (.text []) .end) = none := by rfl",
            "theorem absentHashReject : viewId (fun _ => []) view = none := by rfl",
            (
                "theorem viewWireOverflow : encode fmtViewChange (viewValue {view with "
                "toView:=256^8}) = none := by decide"
            ),
            "end DeltaReduce.NativeFailureVectors",
            "",
        ]
    )
    return "\n".join(out)


if __name__ == "__main__":
    TARGET.write_text(generate(), encoding="utf-8", newline="\n")
    print(TARGET.relative_to(ROOT))
