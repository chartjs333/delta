"""Guard examples reuse original vote bytes; only CONFIG is a whole policy example."""

from pathlib import Path

from generate_native_candidate_authority import sources

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "formal/proofs/DeltaReduce/NativeSelectedVoteVectors.lean"


def generate():
    sources()  # Independently pinned original nine candidate policies, not a new run.
    out = [
        r"""import DeltaReduce.NativeSelectedVote
import DeltaReduce.NativeCandidateAuthorityVectors

/-! Original nine VOTE records; separately checked selected guards and synthetic
component states/tails. Only CONFIG below executes the whole original policy.
No full original nonempty mixed-policy wrapper, new native execution or recovery. -/
namespace DeltaReduce.NativeSelectedVoteVectors
open NativeReceiptBytes
open NativeSelectedVote
open NativeVoteBytes (ascii)
open NativeCandidateAuthorityVectors (policy state candidate1 candidate2 candidate3 candidate4
  candidate5 candidate6 candidate7 candidate8 candidate9 parents1 parents2 parents3 parents4
  parents5 parents6 parents7 parents8 parents9 mixed abortMixed)
open NativeVoteCodecVectors
set_option maxRecDepth 16384
set_option maxHeartbeats 1000000

def live := NativeConfigAdmissionVectors.facts
def eligible := {state with wire := {state.wire with phase := ascii "ELIGIBLE"}}
def available := {state with wire := {state.wire with phase := ascii "AVAILABLE"}}
def emptyTail := {mixed.prior.tail with requests := []}
def abortTail := abortMixed.prior.tail
def viewTime := {live with tick := 50}
def abortTime := {live with tick := 100}
"""
    ]
    for i in range(1, 10):
        out.append(f"def entry{i} : NativeCandidateAuthority.Entry := ⟨candidate{i},parents{i}⟩\n")
        if i in [5, 7]:
            out.append(f"""theorem guarded{i} :
    checkVote policy eligible emptyTail entry{i} live vote{i} = none :=
  arithmeticRejected (by decide)
theorem guardedRecovery{i} :
    checkVote policy eligible emptyTail entry{i} {{live with recovery := true}} vote{i} = none :=
  arithmeticRejected (by decide)
""")
            continue
        state = "available" if i == 2 else "eligible" if i in [3, 4, 6] else "state"
        tail = "abortTail" if i == 9 else "emptyTail"
        facts = "viewTime" if i == 8 else "abortTime" if i == 9 else "live"
        out.append(f"""theorem checks{i} : Checks policy {state} {tail} entry{i} {facts}
    vote{i} := by
  refine ⟨valid{i},?_⟩; decide
theorem accepted{i} : checkVote policy {state} {tail} entry{i} {facts} vote{i} = some vote{i} :=
  voteFromComponents checks{i}
theorem selected{i} : select ⟨mixed,[entry{i}]⟩ {state} vote{i} = some entry{i} := by rfl
""")
    expected = [
        [True, False, False, False, False, False],
        [False, False, True, False, False, False],
        *[[False, False, False, True, False, False]] * 5,
        *[[True, True, True, True, False, False]] * 2,
    ]
    bools = (
        "[" + ",".join("[" + ",".join(str(x).lower() for x in row) + "]" for row in expected) + "]"
    )
    out.append(f"""theorem exactPhaseTable :
    ([1,2,3,4,5,6,7,8,9].map (fun a => NativeStateBytes.phases.map
      (fun phase => decide (phaseAllows a phase)))) = {bools} := by decide
""")
    out.append(
        r"""
theorem inventedPhase : ¬ phaseAllows 8 (ascii "invented") := by decide
theorem unknownKind : select
    ⟨mixed,[entry1,entry2,entry3,entry4,entry5,entry6,entry7,entry8,entry9]⟩
    state {vote1 with wire := {vote1.wire with kind := ascii "UNKNOWN"}} = none := by decide
theorem firstOriginal : select ⟨mixed,[entry1,entry2]⟩ state vote2 = some entry2 := by rfl
theorem neverSkipFirstMatching : select ⟨mixed,[entry1,{entry1 with parents := parents2}]⟩
    state vote1 = some entry1 := by rfl
theorem exactContext : select ⟨mixed,[entry1]⟩ state
    {vote1 with wire := {vote1.wire with context := vote2.wire.context}} = none := by decide
theorem exactCandidateHeight : select ⟨mixed,[{entry1 with original := {candidate1 with
    height := 2}}]⟩
    state vote1 = none := by decide
theorem exactCandidateView : select ⟨mixed,[{entry1 with original := {candidate1 with view := 1}}]⟩
    state vote1 = none := by decide
theorem noncurrentParent : ¬ Checks policy state emptyTail
    {entry1 with parents := {parents1 with checkpoint := NativeSnapshotBaseVectors.base.schema}}
    live vote1 := by decide
theorem notReady : ¬ Checks policy state emptyTail entry1 {live with ready := false} vote1 :=
    by decide
theorem recoveryNotReady : checkVote policy state emptyTail entry1
    {live with recovery := true,ready := false} vote1 = some vote1 := recoveryOnlyReadiness
    accepted1
theorem invalidatedLive : ¬ Checks policy state emptyTail entry1 {live with invalidated :=
    true} vote1 := by decide
theorem invalidatedRecovery : ¬ Checks policy state emptyTail entry1
    {live with invalidated := true,recovery := true} vote1 := by decide
theorem expiredLive : ¬ Checks policy state emptyTail entry1 {live with tick := 100} vote1 :=
    by decide
theorem expiredRecovery : ¬ Checks policy state emptyTail entry1
    {live with tick := 100,recovery := true} vote1 := by decide
theorem wrongSequence : ¬ Checks policy state emptyTail entry1 {live with expectedSequence :=
    2} vote1 := by decide
theorem uint64Tick : ¬ Checks policy state abortTail entry9 {abortTime with tick := 256^8}
    vote9 := by decide
theorem uint64Sequence : ¬ Checks policy state emptyTail entry1 {live with expectedSequence
    := 256^8} vote1 := by decide
theorem ordinaryLastTick : Environment policy state emptyTail entry1 {live with tick := 99}
    := by decide
theorem viewTooEarly : ¬ Environment policy state emptyTail entry8 {live with tick := 49} :=
    by decide
theorem viewFirstTick : Environment policy state emptyTail entry8 viewTime := by decide
theorem viewLastTick : Environment policy state emptyTail entry8 {live with tick := 99} := by decide
theorem viewAtHard : ¬ Environment policy state emptyTail entry8 abortTime := by decide
theorem abortTooEarly : ¬ Environment policy state abortTail entry9 {live with tick := 99} :=
    by decide
theorem abortAtHard : Environment policy state abortTail entry9 abortTime := by decide
theorem foreignRequestBlocksOrdinary : ¬ Environment policy state
    {emptyTail with requests := [⟨ascii "foreign",ascii "INCOMPLETE_INPUT"⟩]} entry1 live :=
    by decide
theorem foreignRequestBlocksView : ¬ Environment policy state
    {emptyTail with requests := [⟨ascii "foreign",ascii "INCOMPLETE_INPUT"⟩]} entry8 viewTime
    := by decide
theorem missingAbortBody : ¬ enabled policy {abortTail with aborts := []} 9 candidate9.body
    abortTime := by decide
theorem abortWrongConfiguredReason : ¬ enabled {policy with reason := ascii "INCOMPLETE_INPUT"}
    abortTail 9 candidate9.body abortTime := by decide
def requestPolicy := {policy with reason := ascii "INCOMPLETE_INPUT"}
def requestTail := {abortTail with
  aborts := [{NativeFailureVectors.abortRow with body :=
    {NativeFailureVectors.abort with reason := ascii "INCOMPLETE_INPUT"}}],
  requests := [⟨policy.round,ascii "INCOMPLETE_INPUT"⟩]}
theorem exactRequestEarly : enabled requestPolicy requestTail 9 candidate9.body live := by decide
theorem foreignRequestNotEnough : ¬ enabled requestPolicy
    {requestTail with requests := [⟨ascii "foreign",ascii "INCOMPLETE_INPUT"⟩]}
    9 candidate9.body live := by decide
theorem otherReasonNotEnough : ¬ enabled requestPolicy
    {requestTail with requests := [⟨policy.round,ascii "UNSAFE_COEFFICIENTS"⟩]}
    9 candidate9.body live := by decide
-- The three request cases check only the enabling predicate; mutated body IDs
-- are NOT a successfully checked source snapshot or cryptographic authority.

theorem wholeOriginalConfigSelected :
    (checkAdmission NativeConfigAdmissionVectors.sha policy state live vote1).isSome ="""
        r""" true := by decide
theorem wholeOriginalConfigBytes :
    (fromBytes NativeConfigAdmissionVectors.sha NativeConfigAdmissionVectors.policyRaw
      NativeConfigAdmissionVectors.stateRaw NativeReceiptVectors.frame1 live).isSome = true := by
  unfold fromBytes
  rw [NativeConfigAdmissionVectors.policyDecoded,NativeConfigAdmissionVectors.stateDecoded,
    NativeVoteCodecVectors.parsed1]
  simp only [bind,Option.bind]
  change ((checkAdmission NativeConfigAdmissionVectors.sha policy state live vote1).bind
    (fun a => some (Checked.mk policy state a vote1))).isSome = true
  cases h : checkAdmission NativeConfigAdmissionVectors.sha policy state live vote1 with
  | none => have good := wholeOriginalConfigSelected; rw [h] at good; contradiction
  | some out => rfl
"""
    )
    for field, replacement in [
        ("validator", 'ascii "foreign"'),
        ("epoch", "vote1.wire.bodyHash"),
        ("round", 'ascii "foreign"'),
        ("context", "vote2.wire.context"),
        ("bodyHash", "vote2.wire.bodyHash"),
    ]:
        out.append(f"""theorem identity_{field} : ¬ Identity policy state entry1 live
    {{vote1 with wire := {{vote1.wire with {field} := {replacement}}}}} := by decide
""")
    out.append(r"""
theorem identityHeight : ¬ Identity policy state entry1 live {vote1 with height := 2} := by decide
theorem identityView : ¬ Identity policy state entry1 live {vote1 with view := 1} := by decide
theorem signatureIsOnlySyntactic : Checks policy state emptyTail entry1 live
    {vote1 with wire := {vote1.wire with signature := vote1.wire.epoch}} := by decide
-- This deliberate countercheck shows that no signature authenticity is proved.
end DeltaReduce.NativeSelectedVoteVectors
""")
    return "".join(out)


if __name__ == "__main__":
    TARGET.write_text(generate(), encoding="utf-8", newline="\n")
