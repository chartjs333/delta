import DeltaReduce.NativeProposalAdmission
import DeltaReduce.NativeIscAdmissionVectors
import DeltaReduce.NativeConfigAdmissionVectors

/-! Small component cases reuse the original CONFIG/ISC candidates and the
checked ISC graph. This is not a new complete-policy byte or mixed WAL proof. -/
set_option maxRecDepth 8192
set_option maxHeartbeats 2000000
namespace DeltaReduce.NativeProposalAdmissionVectors
open NativeReceiptBytes NativeProposalAdmission

def config := NativeConfigAdmissionVectors.candidate
def isc := NativeIscAdmissionVectors.candidate
def policy := {NativeIscAdmissionVectors.policy with candidates := [config,isc]}
def graph : Graph :=
  let b := NativeIscAdmissionVectors.bound
  ⟨policy,b.state,b.schema,b.arithmetic,b.accumulator,b.proposed,b.finalized,
    b.snapshotId,b.bodyTrees,b.bodies,b.closed⟩
def sha (raw : Bytes) : Bytes :=
  if raw = NativeConfigAdmission.configPreimage graph.state.height policy.epoch then
    NativeConfigAdmissionVectors.sha raw
  else NativeIscAdmissionVectors.sha raw
def configPrepared : Prepared := ⟨config,NativeIscAdmissionVectors.bound.checkpoint,config.context⟩
def iscPrepared : Prepared := ⟨isc,NativeIscAdmissionVectors.bound.checkpoint,isc.context⟩
def bound : Bound := ⟨graph,[configPrepared,iscPrepared]⟩

theorem entirePolicyCanonical : NativePolicyBytes.Canonical policy := by decide
theorem completeGraphChecks : GraphChecks graph := by decide
theorem configChecked : checkCandidate sha graph config = some configPrepared := by rfl
theorem iscChecked : checkCandidate sha graph isc = some iscPrepared := by rfl
theorem entireListChecked : checkCandidates sha graph policy.candidates = some bound.candidates := by
  change (checkCandidate sha graph config >>= fun a =>
    (checkCandidate sha graph isc >>= fun b => some [a,b])) = _
  rw [configChecked,iscChecked]; rfl
theorem bothOriginalCandidates : bound.candidates.map Prepared.candidate = [config,isc] := rfl
theorem originalIscVoteChecks : VoteChecks graph iscPrepared NativeIscAdmissionVectors.facts
    NativeVoteCodecVectors.vote2 := by decide
theorem selectedSecond : select bound NativeIscAdmissionVectors.facts
    NativeVoteCodecVectors.vote2 = some iscPrepared := by rfl
theorem readyFalseLive : select bound {NativeIscAdmissionVectors.facts with ready := false}
    NativeVoteCodecVectors.vote2 = none := by rfl
theorem recoveryNotReady : select bound {NativeIscAdmissionVectors.facts with ready := false,recovery := true}
    NativeVoteCodecVectors.vote2 = some iscPrepared := by rfl
theorem invalidated : select bound {NativeIscAdmissionVectors.facts with invalidated := true}
    NativeVoteCodecVectors.vote2 = none := by rfl
theorem wrongSequence : select bound {NativeIscAdmissionVectors.facts with expectedSequence := 2}
    NativeVoteCodecVectors.vote2 = none := by rfl
theorem atDeadline : select bound {NativeIscAdmissionVectors.facts with tick := 100}
    NativeVoteCodecVectors.vote2 = none := by rfl
theorem changedUnselectedConfig : checkCandidates sha graph [{config with body := isc.body},isc] = none := by rfl
theorem changedIsc : checkCandidates sha graph [config,{isc with body := config.body}] = none := by rfl
theorem wrongContext : checkCandidate sha graph {isc with context := config.context} = none := by rfl
theorem wrongHeight : checkCandidate sha graph {isc with height := 2} = none := by rfl
theorem unsupportedAction : checkCandidate sha graph {isc with action := 3} = none := by rfl
theorem reversedPolicy : ¬ NativePolicyBytes.Canonical {policy with candidates := [isc,config]} := by decide
theorem repeatedPolicy : ¬ NativePolicyBytes.Canonical {policy with candidates := [config,isc,isc]} := by decide
theorem emptyPolicy : ¬ NativePolicyBytes.Canonical {policy with candidates := []} := by decide

end DeltaReduce.NativeProposalAdmissionVectors
