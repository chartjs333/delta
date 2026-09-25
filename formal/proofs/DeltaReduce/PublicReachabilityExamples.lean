import DeltaReduce.PublicReachability
import DeltaReduce.PublicRecoveryVectors

/-! Composition of actual operations from empty initialization. All fixture
codec/hash/metadata/scan and non-arithmetic trust keeps its previous finite,
synthetic scope. These are not additional native or public trace executions. -/
namespace DeltaReduce.PublicReachabilityExamples
open NativeBinding PublicJournal PublicRecovery PublicReachability
open NativeGraphVectors NativeVoteVectors PublicJournalVectors PublicRecoveryVectors
set_option maxRecDepth 1000000
set_option maxHeartbeats 0

abbrev Live (m : Machine) := Reachable PublicRecoveryVectors.env "validator-1" (nativeCurrent anchor) m

theorem submitSlotReachable {m slot final} (prior : Live m)
    (accepted : submitSlot m slot = some final) : Live final := by
  unfold submitSlot at accepted
  split at accepted
  · exact .next prior (.persist accepted)
  · exact .next prior (.otherVote accepted)

theorem foldSlotsReachable {m final} (list : List Slot) (prior : Live m)
    (accepted : list.foldlM submitSlot m = some final) : Live final := by
  induction list generalizing m with
  | nil => cases Option.some.inj accepted; exact prior
  | cons slot rest ih =>
    cases h : submitSlot m slot with
    | none => simp [List.foldlM, h] at accepted
    | some next =>
      apply ih (submitSlotReachable prior h)
      simpa [List.foldlM, h] using accepted

theorem fourReachable : Live (machineAt 4) :=
  foldSlotsReachable _ .initial prefixFourFromEmpty

theorem eightReachable : Live normalEight :=
  foldSlotsReachable _ .initial allEightFromEmpty

theorem advancedReachable : Live advanced :=
  .next eightReachable (.advance normalCurrentAdvance)

theorem unexposedReachable : Live unexposed :=
  .next fourReachable (.persist cut0PreservesOriginalUnexposedRecord)

theorem crashUnexposed : crash unexposed = some { unexposed with mode := .crashed } := by decide
theorem restartUnexposed : restart { unexposed with mode := .crashed } =
    some { unexposed with mode := .recovering } := by decide

theorem unexposedRecoveringReachable : Live { unexposed with mode := .recovering } :=
  .next (.next unexposedReachable (.crash crashUnexposed)) (.restart restartUnexposed)

theorem restoredReachable : Live restored :=
  .next unexposedRecoveringReachable (.recover knownFullPrefixRecovered)

theorem recoveredReceiptReachable : Live { restored with sent := [s4] } :=
  .next restoredReachable (.retry unexposedReceiptReturnedOnlyByRetry)

theorem unknownReachable : Live { machineAt 4 with mode := .mustCrash, pending := some s4 } :=
  .next fourReachable (.persist unknown0KeepsOriginalKnownPrefix)

theorem crashUnknown : crash { machineAt 4 with mode := .mustCrash, pending := some s4 } =
    some { machineAt 4 with mode := .crashed, pending := some s4 } := by decide
theorem restartUnknown : restart { machineAt 4 with mode := .crashed, pending := some s4 } =
    some awaiting := by decide

theorem awaitingReachable : Live awaiting :=
  .next (.next unknownReachable (.crash crashUnknown)) (.restart restartUnknown)

/-- Separate mathematical presence case, not a new public UNKNOWN fixture. -/
theorem unknownPresenceReachable : Live restored :=
  .next awaitingReachable (.recover unknownPresenceReplaysAllVotes)

theorem verifiedAbsenceReachable : Live (machineAt 4) :=
  .next awaitingReachable (.recover scan0VerifiedAbsenceRestoresExactPrefix)

theorem incompleteReachable : Live awaiting :=
  .next awaitingReachable (.recover incompleteScanRemainsUnresolved)

theorem blockedReachable : Live { awaiting with mode := .blocked } :=
  .next awaitingReachable (.recover corruptScanBlocks)

theorem historicalRetryReachable : Live advanced :=
  .next advancedReachable (.retry historicalRetryAfterCurrentAdvance)

theorem composedAllVoteReplay :
    PublicJournal.replay PublicRecoveryVectors.env.journal advanced.initial advanced.log =
      some advanced.journal := (reachableInvariant advancedReachable).replayed

theorem composedUncertainReplay :
    PublicJournal.replay PublicRecoveryVectors.env.journal awaiting.initial awaiting.log =
      some awaiting.journal := (reachableInvariant awaitingReachable).replayed

theorem originalInitialRetained : advanced.initial = boot.initial :=
  reachableInitialUnchanged advancedReachable

theorem unresolvedAdmissionRetainsCheckedCandidate :
    Nonempty (CheckedSlot PublicRecoveryVectors.env.journal awaiting.journal s4) ∧
      awaiting.mode ≠ .ready := reachablePendingCannotBeReady awaitingReachable rfl

theorem restoredReceiptHasLogSlot : s4 ∈ voteSlots restored.log ∧ s4.native.isSome = true := by
  have derived := reachableSentIsStored (slot := s4) recoveredReceiptReachable (by simp)
  exact derived

theorem forgedReadyPendingUnreachable : ¬ Live { awaiting with mode := .ready } := by
  intro reachable
  exact (reachablePendingCannotBeReady reachable rfl).2 rfl

theorem earlyReceiptUnreachable : ¬ Live { boot with sent := [s4] } := by
  intro reachable
  have stored := (reachableInvariant reachable).sentStored s4 (by simp)
  exact List.not_mem_nil stored.1

theorem inventedOtherReceiptUnreachable : ¬ Live { machineAt 4 with sent := [s0] } := by
  intro reachable
  have stored := (reachableInvariant reachable).sentStored s0 (by simp)
  have absent : s0.native.isSome = false := rfl
  rw [absent] at stored
  exact Bool.noConfusion stored.2

theorem missingJournalUnreachable : ¬ Live { machineAt 4 with log := [] } := by
  intro reachable
  have slots := (reachableJournalHistory reachable).2
  have impossible : (machineAt 4).journal.slots ≠ [] := by decide
  exact impossible slots

theorem rewrittenInitialUnreachable : ¬ Live { boot with initial := (machineAt 4).journal } := by
  intro reachable
  have empty := (reachableInvariant reachable).emptyInitial
  have impossible : (machineAt 4).journal.slots ≠ [] := by decide
  exact impossible empty

end DeltaReduce.PublicReachabilityExamples
