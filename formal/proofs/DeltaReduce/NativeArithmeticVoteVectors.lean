import DeltaReduce.NativeArithmeticPrefix
import DeltaReduce.NativeSelectedVoteVectors
import DeltaReduce.NativeWholeReplayVectors
import DeltaReduce.NativeWalScanVectors

/-! Small original-wire and separately constructed admission components.
No joined authenticated arithmetic source graph or new native run is claimed. -/
namespace DeltaReduce.NativeArithmeticVoteVectors
open NativeArithmeticVote
open NativeSelectedVoteVectors (entry1 entry5 entry7 eligible emptyTail live)
open NativeCandidateAuthorityVectors (policy state)
open NativeVoteCodecVectors (vote1 vote5 vote7)
open NativeVoteBytes (ascii)
set_option maxRecDepth 4096

theorem parameterChecks : Checks policy eligible emptyTail entry5 live vote5 := by
  refine ⟨NativeVoteCodecVectors.valid5,?_⟩; decide
theorem applyChecks : Checks policy eligible emptyTail entry7 live vote7 := by
  refine ⟨NativeVoteCodecVectors.valid7,?_⟩; decide
theorem originalParameterGuard :
    NativeSelectedVote.checkVote policy eligible emptyTail entry5 live vote5 = none :=
  NativeSelectedVoteVectors.guarded5
theorem originalApplyGuard :
    NativeSelectedVote.checkVote policy eligible emptyTail entry7 live vote7 = none :=
  NativeSelectedVoteVectors.guarded7
theorem configNotArithmetic : ¬ Checks policy state emptyTail entry1 live vote1 := by
  intro h; have wrong := h.2.1; cases wrong <;> contradiction
theorem wrongPhase : ¬ Checks policy state emptyTail entry5 live vote5 := by
  intro h; have phase := h.2.2.2.2.2.2.1; exact (by decide : ¬ _) phase
theorem atDeadline : ¬ Checks policy eligible emptyTail entry5 {live with tick := 100} vote5 := by
  intro h; have time := h.2.2.2.2.2.2.2.1; exact (by decide : ¬ _) time
theorem invalidated : ¬ Checks policy eligible emptyTail entry5 {live with invalidated := true} vote5 := by
  intro h; have invalid := h.2.2.2.2.2.1; contradiction
theorem liveNotReady : ¬ Checks policy eligible emptyTail entry5 {live with ready := false} vote5 := by
  intro h; have ready := h.2.2.2.2.1; exact (by decide : ¬ _) ready
theorem recoveredStillInvalid : ¬ Checks policy eligible emptyTail entry5
    {live with recovery := true,invalidated := true} vote5 := by
  intro h; have invalid := h.2.2.2.2.2.1; contradiction
theorem wrongSequence : ¬ Checks policy eligible emptyTail entry5 {live with expectedSequence := 5} vote5 := by
  intro h; have seq := h.2.2.2.1.2.2.2.2.2.2.2.2; contradiction
theorem wrongBody : ¬ Checks policy eligible emptyTail entry5 live
    {vote5 with wire := {vote5.wire with bodyHash := vote7.wire.bodyHash}} := by
  intro h; have body := h.2.2.2.1.2.2.2.2.2.2.1; exact (by decide : ¬ _) body
theorem wrongValidator : ¬ Checks policy eligible emptyTail entry5 live
    {vote5 with wire := {vote5.wire with validator := ascii "other"}} := by
  intro h; have actor := h.2.2.2.1.1; exact (by decide : ¬ _) actor
theorem wrongEpoch : ¬ Checks policy eligible emptyTail entry5 live
    {vote5 with wire := {vote5.wire with epoch := ascii "other"}} := by
  intro h; have epoch := h.2.2.2.1.2.1; exact (by decide : ¬ _) epoch
theorem wrongView : ¬ Checks policy eligible emptyTail entry5 live {vote5 with view := 1} := by
  intro h; have view := h.2.2.2.1.2.2.2.2.1; contradiction
theorem wrongContext : ¬ Checks policy eligible emptyTail entry5 live
    {vote5 with wire := {vote5.wire with context := vote7.wire.context}} := by
  intro h; have ctx := h.2.2.2.1.2.2.2.2.2.1; exact (by decide : ¬ _) ctx
theorem wrongParent : ¬ Checks policy eligible emptyTail
    {entry5 with parents := {entry5.parents with checkpoint := []}} live vote5 := by
  intro h; have parent := h.2.2.2.1.2.2.2.2.2.2.2.1; exact (by decide : ¬ _) parent
theorem fullOriginalParameterBytes : NativeVoteBytes.encodeFrame vote5.wire = NativeReceiptVectors.frame5 :=
  (NativeVoteBytes.decodedVoteSound NativeVoteCodecVectors.parsed5).2
theorem fullOriginalApplyBytes : NativeVoteBytes.encodeFrame vote7.wire = NativeReceiptVectors.frame7 :=
  (NativeVoteBytes.decodedVoteSound NativeVoteCodecVectors.parsed7).2
theorem originalSemantics : (NativeVoteBytes.fields vote7.wire)[3]? =
    some (ascii "formal_semantics_id",NativeVoteBytes.nativeSemantics) := rfl
theorem originalSignature : (NativeVoteBytes.fields vote5.wire)[8]? =
    some (ascii "signature_id",vote5.wire.signature) := rfl

def actualPrefix : NativeArithmeticPrefix.Prefix :=
  ⟨NativeWalScanVectors.fullResult,NativeWholeReplayVectors.final⟩
theorem mixedCounts : actualPrefix.prior.core.sequence = 2 ∧
    actualPrefix.prior.core.requests.length = 1 ∧ actualPrefix.prior.votes.length = 1 := ⟨rfl,rfl,rfl⟩
theorem mixedGlobalNext : (NativeArithmeticPrefix.facts actualPrefix).expectedSequence = 3 := rfl
theorem voteCountIsNotGlobal : actualPrefix.prior.votes.length+1 ≠
    (NativeArithmeticPrefix.facts actualPrefix).expectedSequence := by decide
theorem actualInvalidation : (NativeArithmeticPrefix.facts actualPrefix).invalidated = true ∧
    (NativeArithmeticPrefix.facts actualPrefix).tick = 11 := ⟨rfl,rfl⟩
theorem mixedGuardRetained : ¬ Checks policy eligible emptyTail entry5
    (NativeArithmeticPrefix.facts actualPrefix) vote5 := by
  intro h; have invalid := h.2.2.2.2.2.1; contradiction
theorem unknownPrefix : NativeArithmeticPrefix.loadPrefix NativeWholeReplayVectors.sha [] [] [] none none = none := rfl
theorem tornPrefix : NativeArithmeticPrefix.loadPrefix NativeWalVectors.tinySHA [] [] [] none (some [68]) = none := by decide
theorem corruptPrefix : NativeArithmeticPrefix.loadPrefix NativeWalVectors.tinySHA [] [] [] none
    (some (List.replicate 64 0)) = none := by decide

end DeltaReduce.NativeArithmeticVoteVectors
