import DeltaReduce.PublicFailureHistory
import DeltaReduce.PublicEarlyBodyVectors
import DeltaReduce.NativeFailureAuthorityVectors

/-! Original failure component checks and synthetic public metadata. These are
not new complete selected failure snapshots or joined native recovery runs. -/
namespace DeltaReduce.PublicFailureBodyVectors
open NativeBinding PublicState PublicFailureBody
open NativeWholeReplayVectors (selected)
set_option maxRecDepth 16384

def syntheticTrust : PublicFailureBody.Trust := ⟨fun _ _ => True⟩
def names : Metadata PublicEarlyBodyVectors.syntheticTrust syntheticTrust :=
  ⟨PublicEarlyBodyVectors.names,fun _ => some "checkpoint1",(by intros; trivial)⟩
def limits : Limits := ⟨3,100,50,100⟩
def view : ViewImage names limits selected NativeFailureVectors.view :=
  ⟨PublicEarlyBodyVectors.header,(by decide)⟩
def config : Config names.early := ⟨NativeFailureVectors.abort.configs.head!,⟨"cfg1",rfl⟩⟩
def abort : AbortImage names limits selected NativeFailureVectors.abort :=
  ⟨PublicEarlyBodyVectors.header,(by decide),(by decide),"checkpoint1",rfl,"HARD_DEADLINE",rfl,[config],rfl⟩
def models := PublicEarlyBodyVectors.models ++ ["checkpoint1"]
def round : Value := PublicAuthority.roundValue (.model "h1") (.model "e1")
def viewBody : Value := PublicAuthority.record
  [("fromView",.integer 0),("round",round),("softDeadline",.integer 50),("toView",.integer 1)]
def viewVote : Vote := ⟨.model "v1",.text "VIEW_CHANGE",PublicAuthority.record [("fromView",.integer 0),("round",round)],viewBody⟩
def abortBody : Value := PublicAuthority.record
  [("configs",PublicAuthority.setValue [.model "cfg1"]),("hardDeadline",.integer 100),
   ("lineage",emptyLineageValue),("parentCheckpoint",.model "checkpoint1"),("reason",.text "HARD_DEADLINE"),
   ("round",round),("validatorEpoch",.model "e1"),("view",.integer 0)]
def abortVote : Vote := ⟨.model "v1",.text "ABORT",round,abortBody⟩

theorem originalViewSource : NativeFailureAuthority.checkView NativeFailureAuthorityVectors.hash
    NativeFailureVectors.viewPolicy NativeConfigAdmissionVectors.state NativeFailureVectors.viewTail
    NativeFailureVectors.viewCandidate = some NativeFailureAuthorityVectors.viewEntry :=
  NativeFailureAuthorityVectors.viewCandidateChecked
theorem originalAbortSource : NativeFailureAuthority.checkAbort NativeFailureAuthorityVectors.hash
    NativeFailureVectors.abortPolicy NativeConfigAdmissionVectors.state NativeFailureVectors.abortTail
    NativeFailureVectors.abortCandidate = some NativeFailureAuthorityVectors.abortEntry :=
  NativeFailureAuthorityVectors.abortCandidateChecked
theorem originalSevenLists : NativeFailureSection.LineageSource NativeFailureVectors.abortPolicy
    ⟨NativeFailureVectors.abort.configs,NativeFailureVectors.abort.inputs,NativeFailureVectors.abort.eligibility,
     NativeFailureVectors.abort.plans,NativeFailureVectors.abort.parameters,NativeFailureVectors.abort.roots,
     NativeFailureVectors.abort.applies⟩ := NativeFailureVectors.allAbortSources
theorem loadedView : loadViewBody names limits selected NativeFailureVectors.view = some view := rfl
theorem loadedAbort : loadAbortBody names limits selected NativeFailureVectors.abort = some abort := rfl
theorem completeViewValue : view.vote = viewVote := rfl
theorem completeAbortValue : abort.vote = abortVote := rfl
theorem viewCanonical : canonical models (.function (voteEntries viewVote)) = true := by decide
theorem abortCanonical : canonical models (.function (voteEntries abortVote)) = true := by decide
theorem completeConfigList : abort.configs.map Config.original = NativeFailureVectors.abort.configs := abortAllConfigs abort
theorem allEmptyLists : EmptyLineage NativeFailureVectors.abort := abort.empty
theorem originalTimeoutProjection : view.observation = PublicAuthority.record
    [("round",round),("view",.integer NativeFailureAuthorityVectors.viewEntry.observation.view)] := rfl

theorem inputPresenceRejects : loadAbortBody names limits selected
    {NativeFailureVectors.abort with inputs := [NativeFailureVectors.abort.parent]} = none :=
  nonemptyLineageRejects (by decide)
theorem ecPresenceRejects : loadAbortBody names limits selected
    {NativeFailureVectors.abort with eligibility := [NativeFailureVectors.abort.parent]} = none :=
  nonemptyLineageRejects (by decide)
theorem planPresenceRejects : loadAbortBody names limits selected
    {NativeFailureVectors.abort with plans := [NativeFailureVectors.abort.parent]} = none :=
  nonemptyLineageRejects (by decide)
theorem parameterPresenceRejects : loadAbortBody names limits selected
    {NativeFailureVectors.abort with parameters := [NativeFailureVectors.abort.parent]} = none :=
  nonemptyLineageRejects (by decide)
theorem rootPresenceRejects : loadAbortBody names limits selected
    {NativeFailureVectors.abort with roots := [NativeFailureVectors.abort.parent]} = none :=
  nonemptyLineageRejects (by decide)
theorem applyPresenceRejects : loadAbortBody names limits selected
    {NativeFailureVectors.abort with applies := [NativeFailureVectors.abort.parent]} = none :=
  nonemptyLineageRejects (by decide)
theorem wrongSoftDeadlineRejects : loadViewBody names {limits with softDeadline := 49} selected NativeFailureVectors.view = none :=
  outsideViewLimitsRejects (by decide)
theorem viewRangeRejects : loadViewBody names {limits with maxView := 0} selected NativeFailureVectors.view = none :=
  outsideViewLimitsRejects (by decide)
theorem timeRangeRejects : loadViewBody names {limits with maxTime := 99} selected NativeFailureVectors.view = none :=
  outsideViewLimitsRejects (by decide)
theorem unknownReasonRejects : reason (NativeVoteBytes.ascii "invented") = none := by decide
theorem noAbortReasonRejects : reason (NativeVoteBytes.ascii "NO_ABORT") = none := by decide
theorem allPublicReasons : (["HARD_DEADLINE","INCOMPLETE_INPUT","UNSAFE_COEFFICIENTS",
    "IRRECOVERABLE_AVAILABILITY","PARAMETER_FAILURE","APPLY_FAILURE"].map
    (fun s => reason (NativeVoteBytes.ascii s))) =
    [some "HARD_DEADLINE",some "INCOMPLETE_INPUT",some "UNSAFE_COEFFICIENTS",
     some "IRRECOVERABLE_AVAILABILITY",some "PARAMETER_FAILURE",some "APPLY_FAILURE"] := by decide
def noCheckpoint : Metadata PublicEarlyBodyVectors.syntheticTrust syntheticTrust :=
  ⟨PublicEarlyBodyVectors.names,fun _ => none,(by intros; trivial)⟩
theorem missingCheckpointRejects : loadAbortBody noCheckpoint limits selected NativeFailureVectors.abort = none := rfl
theorem duplicatedConfigsPreserved : loadConfigs names.early [config.original,config.original] = some [config,config] := rfl
theorem collapsedConfigsReject : ¬ [config.value,config.value].Nodup := by simp
theorem opaqueViewContextRejected : {viewVote with context := .model "opaque"} ≠ view.vote := by decide
theorem changedAbortCurrentRejected : {abortVote with body := .model "opaque"} ≠ abort.vote := by decide
theorem changedViewDeadlineRejected : {viewVote with body := PublicAuthority.record [("fromView",.integer 0),("round",round),("softDeadline",.integer 49),("toView",.integer 1)]} ≠ view.vote := by decide
theorem iscHasNoViewSource : NativeFailureSource.loadView NativeWholeReplayVectors.sha selected = none :=
  NativeFailureSource.wrongViewKind (by decide)
theorem iscHasNoAbortSource : NativeFailureSource.loadAbort NativeWholeReplayVectors.sha selected = none :=
  NativeFailureSource.wrongAbortKind (by decide)
theorem differentPolicyDeadlineRejects : check PublicEarlyBodyVectors.loaded names
    {limits with hardDeadline := selected.policy.hardDeadline + 1} models viewVote = none :=
  wrongConfigurationRejects (fun h => Nat.succ_ne_self _ h.2)

end DeltaReduce.PublicFailureBodyVectors
