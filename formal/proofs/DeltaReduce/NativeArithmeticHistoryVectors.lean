import DeltaReduce.NativeArithmeticHistory
import DeltaReduce.NativeWholeReplayVectors

/-! Existing two-entry original ISC/freeze execution lifted componentwise to
the candidate. The adapter SHA equality is explicit. No new raw arithmetic
source capture or successful multi-arithmetic fixture is invented here. -/
namespace DeltaReduce.NativeArithmeticHistoryVectors
open NativeBinding NativeArithmeticJournal NativeArithmeticHistory
open NativeMixedPolicyVectors (policyRaw)
open NativeMixedReplayVectors (initial)
open NativeWholeReplayVectors (first final sha)
set_option maxRecDepth 4096

variable {codec : Codec} {store : Store} {trust : Trust} (adapter : HashAdapter codec)

def voteInput : Input (store := store) (trust := trust) adapter := ⟨NativeWalVectors.entry2,none⟩
def commandInput : Input (store := store) (trust := trust) adapter := ⟨NativeWalVectors.entry3,none⟩
def original : List (Input (store := store) (trust := trust) adapter) := [voteInput adapter,commandInput adapter]

theorem exactAlignment : align (store := store) (trust := trust) adapter
    [NativeWalVectors.entry2,NativeWalVectors.entry3] [none,none] = some (original adapter) := rfl

theorem missingSourcePosition : align (store := store) (trust := trust) adapter
    [NativeWalVectors.entry2,NativeWalVectors.entry3] [none] = none := rfl

theorem extraSourcePosition : align (store := store) (trust := trust) adapter
    [NativeWalVectors.entry2] [none,none] = none := rfl

theorem missingWalSuffix : align (store := store) (trust := trust) adapter [] [none] = none := rfl

theorem exactEmpty : align (store := store) (trust := trust) adapter [] [] = some [] := rfl

theorem reorderedRetained : align (store := store) (trust := trust) adapter
    [NativeWalVectors.entry3,NativeWalVectors.entry2] [none,none] =
      some [commandInput adapter,voteInput adapter] := rfl

theorem unknownEmptyStillRejects : recoverObserved (store := store) (trust := trust) adapter
    policyRaw initial.core.state none none [] = none := rfl

theorem unknownNonemptyRejects : recoverObserved (store := store) (trust := trust) adapter
    policyRaw initial.core.state none none [none,none] = none := rfl

theorem zeroStateRetained : zeroSnapshot initial.core.state (some ⟨0,initial.core.state⟩) := by
  simp [zeroSnapshot]

theorem zeroStateSubstitution : ¬ zeroSnapshot initial.core.state (some ⟨0,[]⟩) := by decide

theorem zeroStateRejects : recover (store := store) (trust := trust) adapter policyRaw initial.core.state
    (some ⟨0,[]⟩) (original adapter) = none := zeroSnapshotRejects adapter zeroStateSubstitution

theorem noSnapshotRestriction : zeroSnapshot initial.core.state none := by simp [zeroSnapshot]

theorem wrongPolicySource (s : Source codec store trust adapter.sha256)
    (bad : s.policyRaw ≠ policyRaw) :
    arithmetic adapter policyRaw none initial NativeWalVectors.entry2 s = none := by
  simp [arithmetic,bad]

theorem wrongStateSource (s : Source codec store trust adapter.sha256)
    (bad : s.stateRaw ≠ initial.core.state) :
    arithmetic adapter policyRaw none initial NativeWalVectors.entry2 s = none := by
  simp [arithmetic,bad]

theorem commandSourceRejected (s : Source codec store trust adapter.sha256) :
    arithmetic adapter policyRaw none first NativeWalVectors.entry3 s = none := by
  simp only [arithmetic]
  exact if_neg (by intro h; have kind := h.2.2.1; contradiction)

theorem invalidationCannotRefresh (s : Source codec store trust adapter.sha256) :
    arithmetic adapter policyRaw none final NativeWalVectors.entry2 s = none :=
  invalidatedRejects adapter rfl

variable (sameSha : adapter.sha256 = sha)
include sameSha

theorem originalVote : step (store := store) (trust := trust) adapter policyRaw none initial (voteInput adapter) =
    some ⟨first,none⟩ := by
  simp only [step,voteInput,sameSha,NativeWholeReplayVectors.voteStep,Option.map_some]

theorem originalCommand : step (store := store) (trust := trust) adapter policyRaw none first (commandInput adapter) =
    some ⟨final,none⟩ := by
  simp only [step,commandInput,sameSha,NativeWholeReplayVectors.freezeStep,Option.map_some]

theorem originalFold : run (store := store) (trust := trust) adapter policyRaw none initial (original adapter) = some final := by
  simp only [original,run,originalVote adapter sameSha,originalCommand adapter sameSha,bind,Option.bind]

theorem originalRecovery : recover (store := store) (trust := trust) adapter policyRaw initial.core.state none
    (original adapter) = some final := by
  apply recoveryFromComponents adapter noSnapshotRestriction
    (sameSha ▸ NativeWholeReplayVectors.actualStartup) NativeMixedReplayVectors.initialCore
    (originalFold adapter sameSha) ⟨rfl,by simp⟩

theorem originalCount : final.core.sequence = (original (store := store) (trust := trust) adapter).length ∧
    final.core.requests.length + final.votes.length = (original (store := store) (trust := trust) adapter).length :=
  recoveryCounts adapter (originalRecovery adapter sameSha)

theorem reorderedRejected : run (store := store) (trust := trust) adapter policyRaw none initial
    [commandInput adapter,voteInput adapter] = none := by
  simp only [run,step,commandInput,sameSha,NativeWholeReplayVectors.missingVoteCannotStart,Option.map_none,bind,Option.bind]

theorem duplicatedRejected : run (store := store) (trust := trust) adapter policyRaw none initial
    [voteInput adapter,voteInput adapter] = none := by
  simp only [run,originalVote adapter sameSha,bind,Option.bind]
  simp only [step,voteInput,sameSha,NativeWholeReplayVectors.repeatedPositionRejected,Option.map_none]

theorem exactHistoricalRetry : NativeConfigReplay.retryVote adapter.sha256 final NativeReceiptVectors.frame2 =
    some NativeMixedReplayVectors.stored := sameSha ▸ NativeWholeReplayVectors.exactRetry

omit sameSha in
theorem originalGuardWithoutSource {m e v}
    (kind : e.kind = 2) (frame : NativeVoteBytes.decodeFrame e.command = some v)
    (arith : v.wire.kind = NativeVoteBytes.actionName 5 ∨ v.wire.kind = NativeVoteBytes.actionName 7) :
    step (store := store) (trust := trust) adapter policyRaw none m ⟨e,none⟩ = none := by
  simp only [step,NativeWholeReplay.arithmeticScanRejected kind frame arith,Option.map_none]

end DeltaReduce.NativeArithmeticHistoryVectors
