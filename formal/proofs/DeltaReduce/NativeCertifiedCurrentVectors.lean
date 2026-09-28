import DeltaReduce.NativeCertifiedCurrent
import DeltaReduce.NativeCurrentPointerVectors
import DeltaReduce.NativeApplyCertificateVectors

/-! Reuse existing original 008 certificates and synthetic pointer-WAL bytes.
These are component checks, not an authenticated full source-graph execution. -/
namespace DeltaReduce.NativeCertifiedCurrentVectors
set_option maxRecDepth 4096
open NativeBinding NativeCertifiedCurrent
open NativeCurrentPointer NativePointerWal
open NativeCurrentPointerVectors (sha initial prepared lineBytes)

def root := NativeAggregateVectors.finalizedEdge
def finalized := NativeApplyCertificateVectors.finalEdge

theorem finalizedRoot : NativeAggregateBinding.ApplyLinks root finalized.profile.id finalized :=
  ⟨rfl,rfl,rfl⟩

theorem changedProfile : ¬ NativeAggregateBinding.ApplyLinks root [] finalized := by
  intro h
  have len := congrArg List.length h.2.2
  change 71 = 0 at len
  omega

theorem changedRootId : ¬ NativeAggregateBinding.ApplyLinks {root with id := []} finalized.profile.id finalized := by
  intro h
  have len := congrArg List.length h.1
  change 71 = 0 at len
  omega

theorem changedRootSigners : ¬ NativeAggregateBinding.ApplyLinks
    {root with certificate := {root.certificate with signers := []}} finalized.profile.id finalized := by
  intro h
  have len := congrArg (fun q : NativeAggregateRoot.Certificate => q.signers.length) h.2.1
  change 3 = 0 at len
  omega

theorem missingRootLeaves : ¬ NativeAggregateBinding.ApplyLinks
    {root with certificate := {root.certificate with common := {root.certificate.common with leaves := []}}}
      finalized.profile.id finalized := by
  intro h
  have len := congrArg (fun q : NativeAggregateRoot.Certificate => q.common.leaves.length) h.2.1
  change 1 = 0 at len
  omega

theorem originalPointerCommand : NativeCurrentPointer.prepare sha
    NativeCurrentPointerVectors.command NativeCurrentPointerVectors.certificate = some prepared :=
  NativeCurrentPointerVectors.preparedExact

theorem originalCurrentAdvances : choose initial prepared = some .advanced :=
  NativeCurrentPointerVectors.firstAdvance

theorem exactObserved : observe sha initial prepared (.bytes lineBytes) =
    some ⟨next prepared,[record prepared],[]⟩ :=
  observedFromComponents NativeCurrentPointerVectors.exactRecovery rfl

theorem observedStateExact : (⟨next prepared,[record prepared],[]⟩ : Recovered).state = next prepared :=
  observedState exactObserved

theorem tornSuffixRetained : observe sha initial prepared
    (.bytes (lineBytes ++ NativeVoteBytes.ascii "truncated")) =
    some ⟨next prepared,[record prepared],NativeVoteBytes.ascii "truncated"⟩ :=
  observedFromComponents NativeCurrentPointerVectors.tornRetained rfl

theorem unknownRejected : observe sha initial prepared .unknown = none := rfl

theorem emptyCannotClaimRecord : observe sha initial prepared (.bytes []) = none := by
  simp only [observe,NativeCurrentPointerVectors.emptyKnown,bind,Option.bind]
  rfl

theorem onlyTornCannotClaimRecord : observe sha initial prepared
    (.bytes (NativeVoteBytes.ascii "truncated")) = none := by
  simp only [observe,NativeCurrentPointerVectors.onlyTornNoAdvance,bind,Option.bind]
  rfl

theorem duplicateRecordsRejected : observe sha initial prepared (.bytes (lineBytes ++ lineBytes)) = none := by
  simp only [observe,NativeCurrentPointerVectors.doubleRecord,bind,Option.bind]

theorem corruptChecksumRejected : observe sha initial prepared
    (.bytes (NativeCurrentPointerVectors.pre2 ++ [124] ++ NativeVoteBytes.ascii "wrong\n")) = none := by
  simp only [observe,NativeCurrentPointerVectors.checksumSubstitution,bind,Option.bind]

theorem wrongInitialParentRejected : observe sha
    {initial with checkpoint := NativeCurrentPointerVectors.command.checkpoint} prepared (.bytes lineBytes) = none := by
  simp only [observe,NativeCurrentPointerVectors.parentMismatch,bind,Option.bind]

theorem staleHeightRejected : observe sha {initial with height := 8} prepared (.bytes lineBytes) = none := by
  simp only [observe,NativeCurrentPointerVectors.nonIncreasingHeight,bind,Option.bind]

theorem otherPreparedQcRejected : observe sha initial {prepared with qcId := []} (.bytes lineBytes) = none := by
  simp only [observe,NativeCurrentPointerVectors.exactRecovery,bind,Option.bind]
  apply if_neg
  intro h
  have eq := List.cons.inj h
  have len := congrArg (fun r : Record => r.qc.length) eq.1
  change 71 = 0 at len
  omega

theorem otherPreparedOptimizerRejected : observe sha initial
    {prepared with command := {prepared.command with optimizer := []}} (.bytes lineBytes) = none := by
  simp only [observe,NativeCurrentPointerVectors.exactRecovery,bind,Option.bind]
  apply if_neg
  intro h
  have len := congrArg (fun r : Record => r.optimizer.length) (List.cons.inj h).1
  change 71 = 0 at len
  omega

theorem originalRepair : step initial (record prepared) = some (next prepared) ∧
    choose (next prepared) prepared = some .replay :=
  durableReplayRepair originalPointerCommand originalCurrentAdvances

theorem replayNoSecondWrite : execute sha (next prepared) NativeCurrentPointerVectors.command
    NativeCurrentPointerVectors.certificate .duringAppend = some ⟨next prepared,[],some .replay⟩ :=
  NativeCurrentPointerVectors.replayHasNoWrite

theorem survivalWithoutResponse : execute sha initial NativeCurrentPointerVectors.command
    NativeCurrentPointerVectors.certificate .afterDurability = some ⟨initial,lineBytes,none⟩ :=
  NativeCurrentPointerVectors.afterDurabilityExact

theorem unknownCutNotSuccess : execute sha initial NativeCurrentPointerVectors.command
    NativeCurrentPointerVectors.certificate .unknown = none := NativeCurrentPointerVectors.unknownFresh

-- Explicitly retained counterexample: the old raw WAL scan alone does not
-- authenticate a QC. The new composition must recheck its original source.
theorem rawRecoveryStillUnauthenticated : (NativePointerWal.recover sha initial
    (.bytes NativeCurrentPointerVectors.fakeLine)).isSome = true :=
  NativeCurrentPointerVectors.rehashedUncertifiedRecovery

theorem rewrittenRawIdsRejected : observe sha initial prepared
    (.bytes NativeCurrentPointerVectors.fakeLine) = none := by decide

theorem tornCannotResume : completeObservation
    ⟨next prepared,[record prepared],NativeVoteBytes.ascii "truncated"⟩ = none := rfl

theorem completeReturnsOriginalTuple : completeObservation
    ⟨next prepared,[record prepared],[]⟩ = some (next prepared) := rfl

end DeltaReduce.NativeCertifiedCurrentVectors
