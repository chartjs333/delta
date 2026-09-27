import DeltaReduce.NativeSelectedVote
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
def entry1 : NativeCandidateAuthority.Entry := ⟨candidate1,parents1⟩
theorem checks1 : Checks policy state emptyTail entry1 live
    vote1 := by
  refine ⟨valid1,?_⟩; decide
theorem accepted1 : checkVote policy state emptyTail entry1 live vote1 = some vote1 :=
  voteFromComponents checks1
theorem selected1 : select ⟨mixed,[entry1]⟩ state vote1 = some entry1 := by rfl
def entry2 : NativeCandidateAuthority.Entry := ⟨candidate2,parents2⟩
theorem checks2 : Checks policy available emptyTail entry2 live
    vote2 := by
  refine ⟨valid2,?_⟩; decide
theorem accepted2 : checkVote policy available emptyTail entry2 live vote2 = some vote2 :=
  voteFromComponents checks2
theorem selected2 : select ⟨mixed,[entry2]⟩ available vote2 = some entry2 := by rfl
def entry3 : NativeCandidateAuthority.Entry := ⟨candidate3,parents3⟩
theorem checks3 : Checks policy eligible emptyTail entry3 live
    vote3 := by
  refine ⟨valid3,?_⟩; decide
theorem accepted3 : checkVote policy eligible emptyTail entry3 live vote3 = some vote3 :=
  voteFromComponents checks3
theorem selected3 : select ⟨mixed,[entry3]⟩ eligible vote3 = some entry3 := by rfl
def entry4 : NativeCandidateAuthority.Entry := ⟨candidate4,parents4⟩
theorem checks4 : Checks policy eligible emptyTail entry4 live
    vote4 := by
  refine ⟨valid4,?_⟩; decide
theorem accepted4 : checkVote policy eligible emptyTail entry4 live vote4 = some vote4 :=
  voteFromComponents checks4
theorem selected4 : select ⟨mixed,[entry4]⟩ eligible vote4 = some entry4 := by rfl
def entry5 : NativeCandidateAuthority.Entry := ⟨candidate5,parents5⟩
theorem guarded5 :
    checkVote policy eligible emptyTail entry5 live vote5 = none :=
  arithmeticRejected (by decide)
theorem guardedRecovery5 :
    checkVote policy eligible emptyTail entry5 {live with recovery := true} vote5 = none :=
  arithmeticRejected (by decide)
def entry6 : NativeCandidateAuthority.Entry := ⟨candidate6,parents6⟩
theorem checks6 : Checks policy eligible emptyTail entry6 live
    vote6 := by
  refine ⟨valid6,?_⟩; decide
theorem accepted6 : checkVote policy eligible emptyTail entry6 live vote6 = some vote6 :=
  voteFromComponents checks6
theorem selected6 : select ⟨mixed,[entry6]⟩ eligible vote6 = some entry6 := by rfl
def entry7 : NativeCandidateAuthority.Entry := ⟨candidate7,parents7⟩
theorem guarded7 :
    checkVote policy eligible emptyTail entry7 live vote7 = none :=
  arithmeticRejected (by decide)
theorem guardedRecovery7 :
    checkVote policy eligible emptyTail entry7 {live with recovery := true} vote7 = none :=
  arithmeticRejected (by decide)
def entry8 : NativeCandidateAuthority.Entry := ⟨candidate8,parents8⟩
theorem checks8 : Checks policy state emptyTail entry8 viewTime
    vote8 := by
  refine ⟨valid8,?_⟩; decide
theorem accepted8 : checkVote policy state emptyTail entry8 viewTime vote8 = some vote8 :=
  voteFromComponents checks8
theorem selected8 : select ⟨mixed,[entry8]⟩ state vote8 = some entry8 := by rfl
def entry9 : NativeCandidateAuthority.Entry := ⟨candidate9,parents9⟩
theorem checks9 : Checks policy state abortTail entry9 abortTime
    vote9 := by
  refine ⟨valid9,?_⟩; decide
theorem accepted9 : checkVote policy state abortTail entry9 abortTime vote9 = some vote9 :=
  voteFromComponents checks9
theorem selected9 : select ⟨mixed,[entry9]⟩ state vote9 = some entry9 := by rfl
theorem exactPhaseTable :
    ([1,2,3,4,5,6,7,8,9].map (fun a => NativeStateBytes.phases.map
      (fun phase => decide (phaseAllows a phase)))) = [[true,false,false,false,false,false],[false,false,true,false,false,false],[false,false,false,true,false,false],[false,false,false,true,false,false],[false,false,false,true,false,false],[false,false,false,true,false,false],[false,false,false,true,false,false],[true,true,true,true,false,false],[true,true,true,true,false,false]] := by decide

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
    (checkAdmission NativeConfigAdmissionVectors.sha policy state live vote1).isSome = true := by decide
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
theorem identity_validator : ¬ Identity policy state entry1 live
    {vote1 with wire := {vote1.wire with validator := ascii "foreign"}} := by decide
theorem identity_epoch : ¬ Identity policy state entry1 live
    {vote1 with wire := {vote1.wire with epoch := vote1.wire.bodyHash}} := by decide
theorem identity_round : ¬ Identity policy state entry1 live
    {vote1 with wire := {vote1.wire with round := ascii "foreign"}} := by decide
theorem identity_context : ¬ Identity policy state entry1 live
    {vote1 with wire := {vote1.wire with context := vote2.wire.context}} := by decide
theorem identity_bodyHash : ¬ Identity policy state entry1 live
    {vote1 with wire := {vote1.wire with bodyHash := vote2.wire.bodyHash}} := by decide

theorem identityHeight : ¬ Identity policy state entry1 live {vote1 with height := 2} := by decide
theorem identityView : ¬ Identity policy state entry1 live {vote1 with view := 1} := by decide
theorem signatureIsOnlySyntactic : Checks policy state emptyTail entry1 live
    {vote1 with wire := {vote1.wire with signature := vote1.wire.epoch}} := by decide
-- This deliberate countercheck shows that no signature authenticity is proved.
end DeltaReduce.NativeSelectedVoteVectors
