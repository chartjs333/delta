import DeltaReduce.PublicRootHistory
import DeltaReduce.NativeVoteCacheVectors
import DeltaReduce.PublicRootBodyVectors

/-! Existing original mixed ISC/command replay and separate public ROOT
components. No joined positive raw ROOT/corpus execution is claimed. -/
namespace DeltaReduce.PublicRootHistoryVectors
open NativeBinding NativeHistoryRow PublicState PublicRootEnvelope
open NativeMixedPolicyVectors (policyRaw)
open NativeMixedReplayVectors (initial)
open NativeWholeReplayVectors (first final sha)
open NativeArithmeticHistoryVectors (voteInput commandInput original)
open NativeVoteCacheVectors (firstRow)
variable {codec : Codec} {store : Store} {trust : Trust} (adapter : HashAdapter codec)

def firstLocated : Located (store := store) (trust := trust) adapter :=
  ⟨initial,voteInput adapter,⟨first,[firstRow adapter]⟩,firstRow adapter⟩

theorem absentPosition : locate (store := store) (trust := trust) adapter policyRaw none initial [] 0 = none := rfl

theorem pastOriginalLog : locate (store := store) (trust := trust) adapter policyRaw none initial (original adapter) 2 = none :=
  pastEnd adapter (by simp only [original,List.length_cons,List.length_nil]; omega)

theorem failedFullSuffixBlocks {index}
    (failed : NativeCacheHistory.recover (store := store) (trust := trust) adapter policyRaw initial.core.state none
      (original adapter) = none) : recoverAt (store := store) (trust := trust) adapter policyRaw initial.core.state none (original adapter) index = none :=
  incompleteRejects adapter failed

variable (sameSha : adapter.sha256 = sha)
include sameSha

theorem firstAtOriginalPosition : locate (store := store) (trust := trust) adapter policyRaw none initial
    (original adapter) 0 = some (firstLocated (store := store) (trust := trust) adapter) := by
  simp only [original,locate,NativeVoteCacheVectors.capturedVote adapter sameSha,bind,Option.bind,firstLocated]

theorem commandAtSecondPositionRejects : locate (store := store) (trust := trust) adapter policyRaw none initial
    (original adapter) 1 = none := by
  simp only [original,locate,NativeVoteCacheVectors.capturedVote adapter sameSha,
    NativeVoteCacheVectors.capturedCommand adapter sameSha,bind,Option.bind]

theorem computedRowRetained : (firstLocated (store := store) (trust := trust) adapter).row ∈
    ([firstRow adapter] : List (NativeVoteCache.Row adapter)) :=
  inCompleteCache adapter (NativeVoteCacheVectors.fullCapturedRun adapter sameSha) (firstAtOriginalPosition adapter sameSha)

theorem actualPriorAndOrdinals : (firstLocated (store := store) (trust := trust) adapter).row.entry =
    (firstLocated (store := store) (trust := trust) adapter).input.entry ∧ (firstLocated (store := store) (trust := trust) adapter).row.beforeState = (firstLocated (store := store) (trust := trust) adapter).prior.core.state ∧
    (firstLocated (store := store) (trust := trust) adapter).row.ordinal = (firstLocated (store := store) (trust := trust) adapter).prior.votes.length+1 :=
  positionOriginal adapter (firstAtOriginalPosition adapter sameSha)

omit sameSha in
theorem arithmeticOnlyCacheStillBlocks : NativeCacheProjection.all adapter
    [firstRow (store := store) (trust := trust) adapter] = none := rfl

omit sameSha in
theorem globalAndVoteSequenceDifferent : final.core.sequence = 2 ∧
    (firstLocated (store := store) (trust := trust) adapter).row.ordinal = 1 := ⟨rfl,rfl⟩

omit sameSha in
theorem unknownObservationStillRejects : NativeCacheHistory.recoverObserved (store := store) (trust := trust) adapter
    policyRaw initial.core.state none none [none,none] = none := rfl

end DeltaReduce.PublicRootHistoryVectors

namespace DeltaReduce.PublicRootHistoryVectors
open PublicState PublicRootEnvelope

def rootBody := PublicRootBodyVectors.body PublicApplyBodyVectors.leaves

def rootVote := envelope (.model "v1") PublicAuthorityVectors.apc rootBody

theorem exactActor : rootVote.actor = .model "v1" := rfl

theorem exactRootKind : rootVote.kind = .text "AGGREGATE_ROOT" := rfl

theorem entireApcContext : rootVote.context = PublicAuthorityVectors.apc := rfl

theorem contextField : readField rootVote.body "apc" = some rootVote.context := rfl

theorem arithmeticContextNotExtended : PublicState.expectedContext rootVote = none := rfl

theorem changedActor : {rootVote with actor := .model "v2"} ≠ rootVote := by decide

theorem changedKind : {rootVote with kind := .text "APPLY"} ≠ rootVote := by decide

theorem opaqueContextNotStructured : {rootVote with context := .model "native-apc-id"} ≠ rootVote := by decide

theorem missingLeaf : {rootVote with body := PublicRootBodyVectors.body []} ≠ rootVote := by decide +kernel

theorem fullEnvelopeCanonical : canonical ("v1" :: PublicAuthorityVectors.vocabulary.models)
    (.function (voteEntries rootVote)) = true := by decide +kernel

end DeltaReduce.PublicRootHistoryVectors
