import DeltaReduce.NativeCacheProjection
import DeltaReduce.NativeArithmeticHistoryVectors

/-! Original ISC1/freeze2 components, strict lookup negatives and whole-list
ordinary rejection. No new joined positive arithmetic execution is claimed. -/
namespace DeltaReduce.NativeVoteCacheVectors
open NativeBinding NativeVoteCache
open NativeMixedPolicyVectors (policyRaw)
open NativeMixedReplayVectors (initial)
open NativeWholeReplayVectors (first final sha selected)
open NativeArithmeticHistoryVectors (voteInput commandInput original)
set_option maxRecDepth 4096
variable {codec : Codec} {store : Store} {trust : Trust} (adapter : HashAdapter codec)

def firstRow : Row (store := store) (trust := trust) adapter :=
  ordinaryRow adapter initial NativeWalVectors.entry2 selected NativeReceiptVectors.receipt2.voteId

theorem exactOriginalCache : native adapter (firstRow (store := store) (trust := trust) adapter) =
    NativeMixedReplayVectors.stored := rfl

theorem originalReceipt : (native adapter (firstRow (store := store) (trust := trust) adapter)).receipt =
    NativeReceiptVectors.receipt2 := rfl

theorem originalParents : (native adapter (firstRow (store := store) (trust := trust) adapter)).parents =
    NativeWholeReplayVectors.iscEntry.original.parents := rfl

theorem originalPosition : (firstRow (store := store) (trust := trust) adapter).entry.sequence = 1 ∧
    (firstRow (store := store) (trust := trust) adapter).ordinal = 1 := ⟨rfl,rfl⟩

theorem originalState : (firstRow (store := store) (trust := trust) adapter).beforeState = initial.core.state := rfl

theorem uniqueLookup : lookup adapter (NativeConfigReplay.key (native adapter (firstRow (store := store) (trust := trust) adapter)).vote)
    [firstRow (store := store) (trust := trust) adapter] = some (firstRow (store := store) (trust := trust) adapter) := by
  simp [lookup]

theorem duplicateLookup : lookup adapter (NativeConfigReplay.key (native adapter (firstRow (store := store) (trust := trust) adapter)).vote)
    [firstRow (store := store) (trust := trust) adapter,firstRow (store := store) (trust := trust) adapter] = none := by
  simp [lookup]

theorem alteredOrdinalStillAmbiguous : lookup adapter (NativeConfigReplay.key (native adapter (firstRow (store := store) (trust := trust) adapter)).vote)
    [firstRow (store := store) (trust := trust) adapter,{firstRow (store := store) (trust := trust) adapter with ordinal := 99}] = none := by
  simp [lookup,native,firstRow,ordinaryRow]

theorem absentLookup : lookup (store := store) (trust := trust) adapter ([],[],[]) [] = none := rfl

theorem ordinaryProjectRejects : NativeCacheProjection.project adapter
    (firstRow (store := store) (trust := trust) adapter) = none := rfl

theorem ordinaryListRejects : NativeCacheProjection.all adapter
    [firstRow (store := store) (trust := trust) adapter] = none := rfl

theorem ordinaryBlocksTail (tail : List (Row (store := store) (trust := trust) adapter)) :
    NativeCacheProjection.all adapter (firstRow (store := store) (trust := trust) adapter::tail) = none := by
  exact NativeCacheProjection.ordinaryBlocksAll adapter List.mem_cons_self rfl

theorem ordinaryBlocksPrefix (pre : List (Row (store := store) (trust := trust) adapter)) :
    NativeCacheProjection.all adapter (pre ++ [firstRow (store := store) (trust := trust) adapter]) = none :=
  NativeCacheProjection.ordinaryBlocksAll adapter (row := firstRow (store := store) (trust := trust) adapter) (by simp) rfl

theorem emptyDiagnosticProjection : NativeCacheProjection.all (store := store) (trust := trust) adapter [] = some [] := rfl

theorem unknownCache : NativeCacheHistory.recoverObserved (store := store) (trust := trust) adapter
    policyRaw initial.core.state none none [] = none := rfl

theorem unknownProjection : NativeCacheProjection.recoverObserved (store := store) (trust := trust) adapter
    policyRaw initial.core.state none none [none,none] = none := rfl

variable (sameSha : adapter.sha256 = sha)
include sameSha

theorem capturedVote : capture (store := store) (trust := trust) adapter policyRaw none initial (voteInput adapter) =
    some ⟨first,[firstRow (store := store) (trust := trust) adapter]⟩ := by
  apply ordinaryCapture adapter rfl
  rw [sameSha]
  exact NativeWholeReplayVectors.entryChecked

theorem capturedCommand : capture (store := store) (trust := trust) adapter policyRaw none first (commandInput adapter) =
    some ⟨final,[]⟩ := by
  have step := NativeArithmeticHistoryVectors.originalCommand (store := store) (trust := trust) adapter sameSha
  obtain ⟨out,ho,eq,cache,source,len⟩ := stepCapture adapter step
  have noRows : out.rows = [] := by
    have same := cache
    rw [eq] at same
    change first.votes = first.votes ++ out.rows.map (native adapter) at same
    have size := congrArg List.length same
    simp only [List.length_append,List.length_map] at size
    have empty : out.rows.length = 0 := by omega
    exact List.length_eq_zero_iff.mp empty
  have sameOut : out = ⟨final,[]⟩ := by cases out; simp_all
  exact sameOut ▸ ho

theorem fullCapturedRun : NativeCacheHistory.run (store := store) (trust := trust) adapter policyRaw none initial
    (original adapter) = some ⟨final,[firstRow (store := store) (trust := trust) adapter]⟩ := by
  simp only [original,NativeCacheHistory.run,capturedVote adapter sameSha,capturedCommand adapter sameSha,bind,Option.bind,List.append_nil]

omit sameSha in
theorem completeOriginalRows : final.votes = [native adapter (firstRow (store := store) (trust := trust) adapter)] := rfl

omit sameSha in
theorem finalGlobalDifferentFromVoteOrdinal : final.core.sequence = 2 ∧
    (firstRow (store := store) (trust := trust) adapter).ordinal = 1 ∧ final.core.requests.length = 1 := ⟨rfl,rfl,rfl⟩

theorem capturedSource : RowSource (store := store) (trust := trust) adapter policyRaw none initial
    (voteInput adapter) (firstRow (store := store) (trust := trust) adapter) := by
  refine ⟨rfl,rfl,rfl,rfl,?_⟩
  rw [sameSha]
  exact NativeWholeReplayVectors.entryChecked

theorem originalAuthority : NativeSelectedVote.Source adapter.sha256 policyRaw
    (firstRow (store := store) (trust := trust) adapter).beforeState (firstRow (store := store) (trust := trust) adapter).entry.command
    (NativeConfigReplay.facts initial (firstRow (store := store) (trust := trust) adapter).entry) selected :=
  (ordinaryOriginalAuthority adapter (capturedSource adapter sameSha) rfl).1

end DeltaReduce.NativeVoteCacheVectors
