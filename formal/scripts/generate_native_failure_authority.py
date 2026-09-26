"""Original native VIEW/ABORT candidate contexts and selected-vote components."""

import hashlib
import json
from pathlib import Path

import generate_native_failure as prior
import generate_native_vote_codec_vectors as votes
from formal_artifacts import canonical_json_bytes, load_json_strict
from generate_native_wal_lean import lit
from native_admission_snapshot import decode_flat

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "formal/proofs/DeltaReduce/NativeFailureAuthorityVectors.lean"
VOTE_PIN = "788374b6bc1ce788b30a847fbcf6def0fb3804b4f9926304c4456430dd604c44"
DOMAINS = ("deltareduce.vote-context.view.v1", "deltareduce.vote-context.abort.v1")


def source():
    policies = prior.source()
    observed = load_json_strict(votes.previous.FOLDER / "cpp-cross-check.json")
    if hashlib.sha256(canonical_json_bytes(observed)).hexdigest() != VOTE_PIN:
        raise ValueError("original native vote observation changed")
    frames = {row["action"]: row for row in votes.previous.validate(observed["observed"])}
    result = []
    for action, data, domain in zip([8, 9], policies, DOMAINS, strict=True):
        p, body, _, _ = data
        candidate = p["candidates"][0]
        payload = prior.text64(p["round_id"])
        if action == 8:
            payload += prior.u64(body["from_view"])
        pre = domain.encode() + b"\0" + payload
        identifier = "sha256:" + hashlib.sha256(pre).hexdigest()
        vote = decode_flat(bytes.fromhex(frames[action]["frame_hex"]), 3)
        if (
            candidate["context_id"] != identifier
            or vote["context_id"] != identifier
            or vote["body_hash"] != candidate["body_hash"]
        ):
            raise ValueError("original candidate and vote context/body differ")
        result.append((p, body, pre, identifier))
    return result


def generate():
    data = source()
    out = [
        "import DeltaReduce.NativeFailureVote",
        "import DeltaReduce.NativeFailureVectors",
        "",
        "/-! Original native candidate/vote components; four finite hash samples total.",
        "No complete policy admission, WAL effect, QC or new native execution. -/",
        "namespace DeltaReduce.NativeFailureAuthorityVectors",
        "open NativeReceiptBytes NativeFailurePayload NativeFailureAuthority NativeFailureVote",
        "open NativeFailureVectors",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 500000",
    ]

    def theorem(name, statement, proof="by decide"):
        if "\n" in proof and proof.startswith("by "):
            proof = "by\n  " + proof[3:]
        out.append(f"theorem {name} : {statement} := {proof}")

    for i, name in enumerate(["view", "abort"]):
        pre = data[i][2]
        out += [
            f"def {name}CtxPre : Bytes := " + lit(pre),
            f"def {name}CtxHash : Bytes := " + lit(hashlib.sha256(pre).digest()),
        ]
    out.append(
        "def hash (raw : Bytes) : Bytes := if raw = viewCtxPre then viewCtxHash "
        "else if raw = abortCtxPre then abortCtxHash else NativeFailureVectors.sha raw"
    )
    for i, name in enumerate(["view", "abort"]):
        steps = ", ".join(["if_neg (by decide)"] * i + ["if_pos rfl"])
        theorem(
            name + "CtxSHA", f"hash {name}CtxPre = {name}CtxHash", f"by unfold hash; rw [{steps}]"
        )
        args = "viewPolicy.round 0" if name == "view" else "abortPolicy.round"
        theorem(
            name + "ContextExact",
            f"{name}Context hash {args} = some {name}Candidate.context",
            f"by unfold {name}Context; rw [if_pos (by decide)]; "
            "unfold NativeStateBytes.contentId NativeStateBytes.contentPreimage; "
            f"change (if (hash {name}CtxPre).length = 32 then _ else _) = _; "
            f"rw [{name}CtxSHA]; rfl",
        )
        theorem(
            name + "HashRetained",
            f"hash {name}Preimage = {name}Hash",
            f"by unfold hash; rw [if_neg (by decide),if_neg (by decide)]; exact {name}SHA",
        )
        theorem(
            name + "BodyRetained",
            f"{name}Id hash {name} = some {name}ID",
            f"by simp only [{name}Id,NativeStateBytes.contentId,"
            f"NativeStateBytes.contentPreimage,{name}PreimageExact,{name}HashRetained]; rfl",
        )
        fmt = (
            "fmtViewChange readView (viewId hash)"
            if name == "view"
            else "fmtAbortBody readAbort (abortId hash)"
        )
        theorem(
            name + "RowRetained",
            f"checkRow NativePolicySchema.{fmt} {name}Tree = some {name}Row",
            f"rowFromComponents {name}ReadExact {name}Encoded {name}BodyRetained",
        )
        # Concrete successful original tail execution under the same extended SHA.
        facts = f"NativeFailureSection.checkedTail {name}TailChecked"
        theorem(
            name + "TailRetained",
            f"NativeFailureSection.checkTail hash {name}Policy "
            f"NativeConfigAdmissionVectors.state = some {name}Tail",
            "by apply NativeFailureSection.tailFromComponents; "
            f"have h := {facts}; "
            "refine ⟨h.lineage,h.timeoutTrees,h.timeouts,h.viewTrees,?_,h.requestTrees,"
            "h.requests,h.abortTrees,?_,h.valid⟩\n"
            + (
                (
                    "  · simp only [checkViews,checkRows,viewTail,viewRowRetained,"
                    "bind,Option.bind]\n  · rfl"
                )
                if name == "view"
                else (
                    "  · rfl\n  · simp only [checkAborts,checkRows,abortTail,"
                    "abortRowRetained,bind,Option.bind]"
                )
            ),
        )
        reason = "[]" if name == "view" else "abort.reason"
        out.append(f"def {name}Parents : Parents := ⟨{name}Policy.config,abort.parent,{reason}⟩")
        theorem(
            name + "ParentsRead",
            f"readParents {name}Candidate.parents = some {name}Parents",
            f"parentsRead {name}Parents",
        )
        typ = "ViewEntry" if name == "view" else "AbortEntry"
        extra = ",timeout" if name == "view" else ""
        out.append(
            f"def {name}Entry : {typ} := ⟨{name}Parents,{name}Candidate.context,{name}Row{extra}⟩"
        )
        theorem(
            name + "CandidateChecked",
            f"check{name.title()} hash {name}Policy "
            f"NativeConfigAdmissionVectors.state {name}Tail {name}Candidate = some {name}Entry",
            f"{name}FromComponents ⟨{name}ParentsRead,{name}ContextExact,"
            + ("rfl,rfl," if name == "view" else "rfl,")
            + "rfl,by decide,by decide,by decide⟩",
        )
    out += [
        "def state := NativeConfigAdmissionVectors.state",
        "def live : NativeConfigAdmission.RuntimeFacts := ⟨50,true,false,false,1⟩",
        "def late : NativeConfigAdmission.RuntimeFacts := ⟨100,true,false,false,1⟩",
    ]
    for name, num, runtime in [("view", 8, "live"), ("abort", 9, "late")]:
        params = f"{name}Policy state {name}Tail {name}Candidate (.{name} {name}Entry) {runtime}"
        theorem(
            name + "VoteChecks",
            f"VoteChecks {params} NativeVoteCodecVectors.vote{num}",
            f"by refine ⟨NativeVoteCodecVectors.valid{num},?_⟩; decide",
        )
        theorem(
            name + "VoteSelected",
            f"checkVote {params} NativeVoteCodecVectors.vote{num} = "
            f"some NativeVoteCodecVectors.vote{num}",
            f"voteFromComponents {name}VoteChecks",
        )
        theorem(
            name + "CandidateOriginal",
            f"{name}Policy.candidates.find? "
            f"(matching state NativeVoteCodecVectors.vote{num}) = some {name}Candidate",
            "rfl",
        )
    # Component scope and boundary rejections avoid evaluating large frame proofs repeatedly.
    for name, field, value in [
        ("Round", "round", 'NativeVoteBytes.ascii "foreign"'),
        ("Height", "height", "2"),
        ("From", "fromView", "1"),
        ("Next", "toView", "2"),
        ("Deadline", "deadline", "51"),
    ]:
        theorem(
            "wrongView" + name,
            "¬ ViewChecks viewPolicy state " + "{view with " + field + ":=" + value + "} timeout",
        )
    theorem(
        "uint64NoWrap",
        "¬ ViewChecks viewPolicy {state with view:=256^8-1} "
        "{view with fromView:=256^8-1,toView:=0} {timeout with view:=256^8-1}",
    )
    for name, field, val in [
        ("Round", "round", 'NativeVoteBytes.ascii "other"'),
        ("Height", "height", "2"),
        ("View", "view", "1"),
    ]:
        theorem(
            "wrongTimeout" + name,
            "¬ ViewChecks viewPolicy state view {timeout with " + field + ":=" + val + "}",
        )
    theorem(
        "missingTimeout",
        "checkView hash viewPolicy state {viewTail with timeouts:=[]} viewCandidate = none",
        "by simp only [checkView,viewParentsRead,viewTail,bind,Option.bind]; rfl",
    )
    theorem(
        "abortAfterApply",
        "¬ AbortChecks abortPolicy state "
        "{abortTail with lineage:={lineage with applies:=[abort.parent]}} abortParents "
        "{abort with applies:=[abort.parent]}",
    )
    theorem(
        "abortWrongReason",
        "¬ AbortChecks abortPolicy state abortTail "
        '{abortParents with reason:=NativeVoteBytes.ascii "INCOMPLETE_INPUT"} abort',
    )
    theorem(
        "abortWrongParent",
        "¬ AbortChecks abortPolicy state abortTail abortParents {abort with parent:=viewID}",
    )
    for name, expr in [
        ("viewTooEarly", "Enabled viewPolicy viewTail {live with tick:=49} (.view viewEntry)"),
        ("viewAtHard", "Enabled viewPolicy viewTail {live with tick:=100} (.view viewEntry)"),
        ("abortTooEarly", "Enabled abortPolicy abortTail {late with tick:=99} (.abort abortEntry)"),
    ]:
        theorem(name, "¬ " + expr)
    theorem("viewLastTick", "Enabled viewPolicy viewTail {live with tick:=99} (.view viewEntry)")
    theorem(
        "foreignRequestBlocksView",
        "¬ Enabled viewPolicy "
        '{viewTail with requests:=[⟨NativeVoteBytes.ascii "foreign",'
        'NativeVoteBytes.ascii "INCOMPLETE_INPUT"⟩]} live (.view viewEntry)',
    )
    theorem(
        "foreignRequestDoesNotEnableAbort",
        "¬ Enabled "
        '{abortPolicy with reason:=NativeVoteBytes.ascii "INCOMPLETE_INPUT"} '
        '{abortTail with requests:=[⟨NativeVoteBytes.ascii "foreign",'
        'NativeVoteBytes.ascii "INCOMPLETE_INPUT"⟩]} live '
        "(.abort {abortEntry with row:={abortRow with body:={abort with "
        'reason:=NativeVoteBytes.ascii "INCOMPLETE_INPUT"}}})',
    )
    theorem(
        "exactRequestEnablesEarly",
        "Enabled "
        '{abortPolicy with reason:=NativeVoteBytes.ascii "INCOMPLETE_INPUT"} '
        '{abortTail with requests:=[⟨abortPolicy.round,NativeVoteBytes.ascii "INCOMPLETE_INPUT"⟩]} '
        "live (.abort {abortEntry with row:={abortRow with body:={abort with "
        'reason:=NativeVoteBytes.ascii "INCOMPLETE_INPUT"}}})',
    )
    for name, runtime in [
        ("liveNotReady", "{live with ready:=false}"),
        ("invalidated", "{live with invalidated:=true}"),
        ("wrongSequence", "{live with expectedSequence:=2}"),
    ]:
        theorem(
            name,
            "¬ VoteChecks viewPolicy state viewTail viewCandidate (.view viewEntry) "
            + runtime
            + " NativeVoteCodecVectors.vote8",
            "by simp only [VoteChecks,NativeVoteCodecVectors.valid8,true_and]; decide",
        )
    theorem(
        "replayWithoutReady",
        "VoteChecks viewPolicy state viewTail viewCandidate "
        "(.view viewEntry) {live with recovery:=true,ready:=false} NativeVoteCodecVectors.vote8",
        "by refine ⟨NativeVoteCodecVectors.valid8,?_⟩; decide",
    )
    for phase in ["AGGREGATED", "ABORTED", "invented"]:
        theorem(
            "rejectPhase" + phase.title(),
            "¬ phaseAllowed (NativeVoteBytes.ascii " + json.dumps(phase) + ")",
        )
    theorem(
        "scopeViewParentNotYetCurrent",
        "Common viewPolicy state viewCandidate "
        "{viewParents with checkpoint:=viewID} viewCandidate.context",
    )
    theorem(
        "selectedParentMustBeCurrent",
        "¬ VoteChecks viewPolicy state viewTail viewCandidate "
        "(.view {viewEntry with parents:={viewParents with checkpoint:=viewID}}) "
        "live NativeVoteCodecVectors.vote8",
        "by simp only [VoteChecks,NativeVoteCodecVectors.valid8,true_and]; decide",
    )
    for name, txt in [
        ("space", "round with spaces"),
        ("punctuation", "round/@!?"),
        ("long", "a" * 129),
    ]:
        theorem("wireId" + name.title(), "WireId (NativeVoteBytes.ascii " + json.dumps(txt) + ")")
        theorem(
            "notCertificateLabel" + name.title(),
            "¬ NativeConfigAdmission.Label (NativeVoteBytes.ascii " + json.dumps(txt) + ")",
        )
        theorem(
            "timeoutId" + name.title(),
            "TimeoutValid {timeout with round:=NativeVoteBytes.ascii " + json.dumps(txt) + "}",
        )
    theorem("emptyWireId", "¬ WireId []")
    theorem("nonPrintableWireId", "¬ WireId [10]")
    theorem(
        "viewEpochNotInContext",
        "viewContext hash viewPolicy.round state.view = "
        "viewContext hash abortPolicy.round state.view",
        "rfl",
    )
    theorem(
        "noParameter",
        "checkCandidate hash viewPolicy state viewTail {viewCandidate with action:=5} = none",
        "rfl",
    )
    theorem(
        "noApply",
        "checkCandidate hash viewPolicy state viewTail {viewCandidate with action:=7} = none",
        "rfl",
    )
    # Every otherwise forbidden parent slot is tested from the exact original schema.
    import native_policy_codec as codec
    from generate_native_policy_schema import lean_value

    for field, _ in codec.SCHEMAS["parents"][2:-1]:
        p = dict(data[0][0]["candidates"][0]["parents"])
        p[field] = "forbidden"
        theorem(
            "forbidden_" + field, "readParents (" + lean_value("parents", p) + ") = none", "rfl"
        )
    theorem("emptyViewContext", "viewContext hash [] 0 = none", "by decide")
    theorem("emptyAbortContext", "abortContext hash [] = none", "by decide")
    out += ["end DeltaReduce.NativeFailureAuthorityVectors", ""]
    return "\n".join(out)


if __name__ == "__main__":
    TARGET.write_text(generate(), encoding="utf-8", newline="\n")
    print(TARGET.relative_to(ROOT))
