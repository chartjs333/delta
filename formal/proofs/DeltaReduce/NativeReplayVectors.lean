import DeltaReduce.NativeReplay
import DeltaReduce.NativeVoteVectors

/-! Native arithmetic is recomputed, not accepted by a record table.
Input/hash samples and metadata/QC/scan trust are finite and synthetic.
The three-vote journal renumbers only arithmetic votes: it is NOT the
full public trace, whose other five vote kinds need their own bridge. -/
namespace DeltaReduce.NativeReplayVectors
open NativeBinding NativeReplay NativeGraphVectors NativeVoteVectors RecoveryKernel
set_option maxRecDepth 1000000
set_option maxHeartbeats 0

def input0 : NativeReplay.Input codec syntheticTrust voteTrust :=
  ⟨parameterAnchor, store, some parameterBinding, metadata0, True.intro⟩
def input1 : NativeReplay.Input codec syntheticTrust voteTrust :=
  ⟨parameterAnchor, store, some parameterBinding, metadata1, True.intro⟩
def input2 : NativeReplay.Input codec syntheticTrust voteTrust :=
  ⟨anchor, store, some fixtureBinding, metadata2, True.intro⟩
def applyGraph : NativeReplay.Graph codec syntheticTrust := ⟨anchor, store, some fixtureBinding⟩
def certifiedBody : NativeBinding.Bytes := [123,34,97,103,103,114,101,103,97,116,101,95,105,100,34,58,34,115,104,97,50,53,54,58,52,101,99,100,53,49,57,56,100,55,49,57,57,52,99,97,57,99,50,97,51,50,56,55,50,53,99,50,100,57,102,99,56,57,55,55,53,55,49,53,55,99,101,54,51,102,52,52,102,48,56,49,52,52,57,101,51,100,52,57,99,99,48,98,34,44,34,97,117,116,104,111,114,105,116,121,95,105,100,34,58,34,115,104,97,50,53,54,58,102,97,51,55,50,98,54,97,57,100,102,53,56,49,48,100,57,51,50,56,102,57,102,48,57,101,98,100,48,50,102,102,49,51,57,97,56,49,52,55,53,49,53,99,54,99,49,55,57,51,99,52,52,55,49,57,54,97,99,102,100,52,98,51,34,44,34,107,105,110,100,34,58,34,65,80,80,76,89,95,69,88,80,69,67,84,69,68,34,44,34,110,101,120,116,95,109,111,100,101,108,34,58,91,49,57,44,45,49,57,93,44,34,110,101,120,116,95,109,111,100,101,108,95,104,97,115,104,34,58,34,115,104,97,50,53,54,58,100,54,99,54,49,49,99,54,99,51,49,97,50,49,99,48,52,100,98,101,100,52,53,51,102,50,102,57,48,101,99,101,99,49,56,101,51,100,98,53,57,52,56,49,53,52,54,54,100,102,51,102,100,100,51,57,53,55,101,100,54,49,98,97,34,44,34,110,101,120,116,95,111,112,116,105,109,105,122,101,114,34,58,91,50,44,45,50,93,44,34,110,101,120,116,95,111,112,116,105,109,105,122,101,114,95,104,97,115,104,34,58,34,115,104,97,50,53,54,58,49,100,50,48,97,102,52,97,57,56,101,99,56,97,101,49,98,101,56,101,50,53,52,102,100,98,53,53,48,97,56,49,54,50,52,52,54,57,99,99,55,53,101,49,97,49,53,102,97,98,98,100,54,56,98,55,49,57,51,48,102,49,49,56,34,44,34,112,97,114,97,109,101,116,101,114,95,98,111,100,121,95,105,100,115,34,58,91,34,115,104,97,50,53,54,58,98,57,101,97,101,49,55,98,100,51,101,54,97,55,51,97,56,49,97,102,51,55,54,100,55,100,99,56,50,53,51,48,97,98,54,52,98,99,48,48,100,98,50,97,99,49,99,101,97,101,49,97,48,55,97,100,97,48,49,57,48,56,101,51,34,44,34,115,104,97,50,53,54,58,100,56,51,49,51,57,99,57,54,56,97,55,53,101,50,57,97,56,53,54,54,97,48,55,55,55,55,56,54,101,55,101,98,54,48,51,100,101,50,53,48,55,102,50,49,99,102,49,98,51,49,54,48,52,102,54,97,98,97,57,57,98,102,54,34,93,125]
def env : Environment codec syntheticTrust voteTrust where
  input context := if context = RecoveryKernelVectors.data4.context then some input0
    else if context = RecoveryKernelVectors.data5.context then some input1
    else if context = RecoveryKernelVectors.data7.context then some input2 else none
  graph _ := some applyGraph
  applyAuthenticated _ body c := decide (body = certifiedBody ∧
    c.bytes = RecoveryKernelVectors.certificate.bytes ∧
    c.next.checkpoint = RecoveryKernelVectors.nextCurrent.checkpoint)
  scanAuthenticated _ _ _ _ := true -- Named synthetic exporter trust.
def nativeAdapter := NativeReplay.adapter env
def r0 : Record := { RecoveryKernelVectors.record4 with sequence := 1, receipt := [123,34,99,111,109,109,97,110,100,95,105,100,34,58,34,115,104,97,50,53,54,58,98,49,51,98,55,51,50,55,98,55,99,56,100,52,102,50,57,51,50,49,54,102,48,56,99,50,98,99,53,51,100,100,52,98,100,54,52,98,56,52,101,55,101,50,51,97,100,101,98,48,51,102,48,52,102,99,55,57,51,98,101,48,57,48,34,44,34,101,102,102,101,99,116,95,105,100,34,58,34,115,104,97,50,53,54,58,53,52,57,101,49,53,48,56,51,55,100,49,100,55,52,50,97,52,50,50,50,51,99,51,102,101,50,49,98,101,98,51,102,56,54,97,56,57,53,52,98,54,52,101,48,48,52,101,51,97,101,52,101,53,49,101,102,100,55,51,99,98,97,57,34,44,34,112,114,111,106,101,99,116,105,111,110,95,118,101,114,115,105,111,110,34,58,34,100,114,97,102,116,49,34,44,34,115,101,113,117,101,110,99,101,34,58,49,44,34,118,111,116,101,34,58,123,34,97,99,116,105,111,110,95,105,100,34,58,34,65,67,84,45,80,65,82,65,77,45,86,79,84,69,34,44,34,97,99,116,111,114,95,105,100,34,58,34,118,97,108,105,100,97,116,111,114,45,49,34,44,34,98,111,100,121,95,104,97,115,104,34,58,34,115,104,97,50,53,54,58,98,57,101,97,101,49,55,98,100,51,101,54,97,55,51,97,56,49,97,102,51,55,54,100,55,100,99,56,50,53,51,48,97,98,54,52,98,99,48,48,100,98,50,97,99,49,99,101,97,101,49,97,48,55,97,100,97,48,49,57,48,56,101,51,34,44,34,104,101,105,103,104,116,34,58,49,44,34,112,97,114,101,110,116,95,104,97,115,104,101,115,34,58,91,34,115,104,97,50,53,54,58,55,98,49,54,49,97,52,56,55,48,49,51,102,48,49,56,101,57,101,102,98,97,100,101,102,52,99,100,57,52,56,99,56,53,57,97,55,99,52,102,48,50,48,55,54,100,99,50,57,99,97,101,50,102,51,51,50,100,49,97,101,99,101,54,34,93,44,34,114,111,117,110,100,95,105,100,34,58,34,114,111,117,110,100,45,49,34,44,34,118,97,108,105,100,97,116,111,114,95,101,112,111,99,104,34,58,34,101,112,111,99,104,45,49,34,44,34,118,111,116,101,95,99,111,110,116,101,120,116,95,105,100,34,58,34,78,79,82,77,65,76,45,80,65,82,65,77,45,68,49,45,83,49,58,114,111,117,110,100,45,49,34,125,125] }
def r1 : Record := { RecoveryKernelVectors.record5 with sequence := 2, receipt := [123,34,99,111,109,109,97,110,100,95,105,100,34,58,34,115,104,97,50,53,54,58,48,56,99,56,100,99,102,97,52,57,101,57,99,102,57,102,49,48,102,56,99,51,50,102,100,55,49,52,101,98,49,102,102,49,54,101,97,98,54,51,51,51,56,53,101,54,98,48,54,51,57,97,53,100,101,99,51,98,52,97,50,101,97,53,34,44,34,101,102,102,101,99,116,95,105,100,34,58,34,115,104,97,50,53,54,58,57,102,98,98,99,57,51,97,50,98,97,55,99,100,50,97,100,97,54,99,48,52,50,97,99,97,54,48,100,56,48,51,97,102,97,102,98,49,56,102,101,52,57,101,57,54,48,54,98,53,98,50,99,101,99,51,102,56,51,51,98,52,99,99,34,44,34,112,114,111,106,101,99,116,105,111,110,95,118,101,114,115,105,111,110,34,58,34,100,114,97,102,116,49,34,44,34,115,101,113,117,101,110,99,101,34,58,50,44,34,118,111,116,101,34,58,123,34,97,99,116,105,111,110,95,105,100,34,58,34,65,67,84,45,80,65,82,65,77,45,86,79,84,69,34,44,34,97,99,116,111,114,95,105,100,34,58,34,118,97,108,105,100,97,116,111,114,45,49,34,44,34,98,111,100,121,95,104,97,115,104,34,58,34,115,104,97,50,53,54,58,100,56,51,49,51,57,99,57,54,56,97,55,53,101,50,57,97,56,53,54,54,97,48,55,55,55,55,56,54,101,55,101,98,54,48,51,100,101,50,53,48,55,102,50,49,99,102,49,98,51,49,54,48,52,102,54,97,98,97,57,57,98,102,54,34,44,34,104,101,105,103,104,116,34,58,49,44,34,112,97,114,101,110,116,95,104,97,115,104,101,115,34,58,91,34,115,104,97,50,53,54,58,55,98,49,54,49,97,52,56,55,48,49,51,102,48,49,56,101,57,101,102,98,97,100,101,102,52,99,100,57,52,56,99,56,53,57,97,55,99,52,102,48,50,48,55,54,100,99,50,57,99,97,101,50,102,51,51,50,100,49,97,101,99,101,54,34,93,44,34,114,111,117,110,100,95,105,100,34,58,34,114,111,117,110,100,45,49,34,44,34,118,97,108,105,100,97,116,111,114,95,101,112,111,99,104,34,58,34,101,112,111,99,104,45,49,34,44,34,118,111,116,101,95,99,111,110,116,101,120,116,95,105,100,34,58,34,78,79,82,77,65,76,45,80,65,82,65,77,45,68,49,45,83,50,58,114,111,117,110,100,45,49,34,125,125] }
def r2 : Record := { RecoveryKernelVectors.record7 with sequence := 3, receipt := [123,34,99,111,109,109,97,110,100,95,105,100,34,58,34,115,104,97,50,53,54,58,100,102,51,102,99,53,57,49,98,98,52,102,99,52,99,102,53,57,55,52,50,52,52,51,99,100,52,54,57,48,48,53,54,54,48,99,51,54,51,49,55,57,51,97,99,50,97,100,56,57,102,57,100,57,49,54,99,49,50,102,56,101,99,51,34,44,34,101,102,102,101,99,116,95,105,100,34,58,34,115,104,97,50,53,54,58,48,53,56,100,51,101,100,53,54,99,52,101,102,100,50,48,50,53,54,54,51,102,102,49,99,98,51,57,55,98,101,52,100,49,54,53,49,50,55,52,97,97,48,53,51,97,56,50,48,48,54,97,49,97,48,49,98,56,99,49,56,49,56,99,34,44,34,112,114,111,106,101,99,116,105,111,110,95,118,101,114,115,105,111,110,34,58,34,100,114,97,102,116,49,34,44,34,115,101,113,117,101,110,99,101,34,58,51,44,34,118,111,116,101,34,58,123,34,97,99,116,105,111,110,95,105,100,34,58,34,65,67,84,45,65,80,80,76,89,45,86,79,84,69,34,44,34,97,99,116,111,114,95,105,100,34,58,34,118,97,108,105,100,97,116,111,114,45,49,34,44,34,98,111,100,121,95,104,97,115,104,34,58,34,115,104,97,50,53,54,58,53,50,50,100,102,56,102,56,99,48,56,56,97,53,57,53,49,49,48,57,52,56,102,56,97,52,49,100,102,98,52,101,56,52,50,97,53,102,98,98,55,56,99,52,49,98,97,53,101,99,53,48,49,51,56,52,102,56,50,53,101,55,101,101,34,44,34,104,101,105,103,104,116,34,58,49,44,34,112,97,114,101,110,116,95,104,97,115,104,101,115,34,58,91,34,115,104,97,50,53,54,58,53,99,51,99,100,57,100,50,52,48,49,52,102,99,52,53,54,54,97,49,102,54,101,102,56,97,53,101,51,99,102,55,55,97,48,101,55,50,51,51,55,52,102,54,49,52,52,98,99,49,49,102,100,49,101,53,101,52,101,51,55,55,57,56,34,93,44,34,114,111,117,110,100,95,105,100,34,58,34,114,111,117,110,100,45,49,34,44,34,118,97,108,105,100,97,116,111,114,95,101,112,111,99,104,34,58,34,101,112,111,99,104,45,49,34,44,34,118,111,116,101,95,99,111,110,116,101,120,116,95,105,100,34,58,34,78,79,82,77,65,76,45,65,80,80,76,89,58,114,111,117,110,100,45,49,34,125,125] }
def start := initial (nativeCurrent anchor)
def prior : List Entry := [.vote r0, .vote r1]
def journal : List Entry := prior ++ [.vote r2, .advance RecoveryKernelVectors.certificate]
def completeState : State := ⟨[r0, r1, r2], RecoveryKernelVectors.nextCurrent⟩
def absentEnv : Environment codec syntheticTrust voteTrust := { env with input := fun _ => none }
def missingEnv := { env with input := fun _ => some { input0 with available := none } }
def unboundQC := { env with applyAuthenticated := fun _ _ _ => false }
def unboundScan := { env with scanAuthenticated := fun _ _ _ _ => false }
theorem pinnedNativeRecord0Admitted : step nativeAdapter state0 (.vote RecoveryKernelVectors.record4) = some ⟨RecoveryKernelVectors.records.take 5, nativeCurrent anchor⟩ := by decide
theorem pinnedNativeRecord1Admitted : step nativeAdapter state1 (.vote RecoveryKernelVectors.record5) = some ⟨RecoveryKernelVectors.records.take 6, nativeCurrent anchor⟩ := by decide
theorem pinnedNativeRecord2Admitted : step nativeAdapter state2 (.vote RecoveryKernelVectors.record7) = some ⟨RecoveryKernelVectors.records.take 8, nativeCurrent anchor⟩ := by decide
theorem nativeJournalReplays : replay nativeAdapter start journal = some completeState := by decide
theorem nativePrepareExact : prepare nativeAdapter .ready start r0.data = .pending r0 := by decide
theorem missingContextRejects : prepare (NativeReplay.adapter absentEnv) .ready start r0.data = .rejected := by decide
theorem missingGraphRejects : prepare (NativeReplay.adapter missingEnv) .ready start r0.data = .rejected := by decide
theorem missingGraphHasNoEffect : NativeReplay.effect missingEnv r0.data = none := by decide
theorem wrongAuthorityRejected : step nativeAdapter start (.vote { r0 with data.authority := [] }) = none := by decide
theorem wrongBodyRejected : step nativeAdapter start (.vote { r0 with data.body := [] }) = none := by decide
theorem wrongCanonicalCommandRejected : step nativeAdapter start (.vote { r0 with data.command := r0.data.command ++ [32] }) = none := by decide
theorem wrongSequenceRejected : step nativeAdapter start (.vote { r0 with sequence := 2 }) = none := by decide
theorem wrongReceiptRejected : step nativeAdapter start (.vote { r0 with receipt := [] }) = none := by decide
theorem wrongEffectRejected : step nativeAdapter start (.vote { r0 with effect := [] }) = none := by decide
theorem missingContextReceiptIsNone : NativeReplay.receipt absentEnv r0.data 1 r0.effect = none := by decide
theorem overflowReceiptIsNone : NativeReplay.receipt env r0.data 9223372036854775808 r0.effect = none := by decide
theorem zeroReceiptIsNone : NativeReplay.receipt env r0.data 0 r0.effect = none := by decide
theorem changedReceiptEffectIsNone : NativeReplay.receipt env r0.data 1 [] = none := by decide
theorem failedEffectStopsPreparation : prepare { nativeAdapter with effect := fun _ => none } .ready start r0.data = .rejected := by decide
theorem failedReceiptStopsPreparation : prepare { nativeAdapter with receipt := fun _ _ _ => none } .ready start r0.data = .rejected := by decide
theorem failedEffectCannotReplayEmpty : step { nativeAdapter with effect := fun _ => none } start (.vote { r0 with effect := [] }) = none := by decide
theorem failedReceiptCannotReplayEmpty : step { nativeAdapter with receipt := fun _ _ _ => none } start (.vote { r0 with receipt := [] }) = none := by decide
theorem wrongQCModelRejected : step nativeAdapter start (.advance { RecoveryKernelVectors.certificate with next.model := [0] }) = none := by decide
theorem wrongQCOptimizerRejected : step nativeAdapter start (.advance { RecoveryKernelVectors.certificate with next.optimizer := [0] }) = none := by decide
theorem wrongQCParentRejected : step nativeAdapter start (.advance { RecoveryKernelVectors.certificate with parent.model := [0] }) = none := by decide
theorem unauthenticatedQCRejected : step (NativeReplay.adapter unboundQC) start (.advance RecoveryKernelVectors.certificate) = none := by decide
theorem missingQCGraphRejected : step (NativeReplay.adapter { env with graph := fun _ => none }) start (.advance RecoveryKernelVectors.certificate) = none := by decide
theorem duplicateQCIsIdempotent : step nativeAdapter completeState (.advance RecoveryKernelVectors.certificate) = some completeState := by decide
theorem oldParentFirstRejected : prepare nativeAdapter .ready (initial RecoveryKernelVectors.nextCurrent) r0.data = .rejected := by decide
theorem historicalRetryAfterAdvance : prepare nativeAdapter .ready completeState r0.data = .retry r0 := by decide
theorem historicalConflictAfterAdvance : prepare nativeAdapter .ready completeState { r0.data with command := r0.data.command ++ [32] } = .conflict := by decide
theorem survivingUnexposedRecordRecovered : resolveUnknown nativeAdapter start prior r2 (.complete (prior ++ [.vote r2])) = .ready ⟨[r0,r1,r2], nativeCurrent anchor⟩ := by decide
theorem verifiedAbsentReplaysExactPrefix : resolveUnknown nativeAdapter start prior r2 (.verifiedAbsent prior) = .ready ⟨[r0,r1], nativeCurrent anchor⟩ := by decide
theorem plainPrefixNotAbsence : resolveUnknown nativeAdapter start prior r2 (.complete prior) = .blocked := by decide
theorem truncatedAbsentPrefixRejected : resolveUnknown nativeAdapter start prior r2 (.verifiedAbsent []) = .blocked := by decide
theorem untrustedScanRejected : resolveUnknown (NativeReplay.adapter unboundScan) start prior r2 (.complete (prior ++ [.vote r2])) = .blocked := by decide
theorem incompleteStaysUnknown : observedSequence (resolveUnknown nativeAdapter start prior r2 .incomplete) = none := by decide
theorem corruptStaysBlocked : resolveUnknown nativeAdapter start prior r2 .corrupt = .blocked := by decide
theorem ambiguousStaysBlocked : resolveUnknown nativeAdapter start prior r2 .ambiguous = .blocked := by decide
theorem blockedCannotResume : continueRecovery nativeAdapter start prior r2 .blocked (.verifiedAbsent prior) = .blocked := by decide
theorem unexposedCannotSend : exposePending .ready .durable ⟨[r0], nativeCurrent anchor⟩ r0 = none := by decide
theorem committedExactRecordCanSend : exposePending .ready .committed ⟨[r0], nativeCurrent anchor⟩ r0 = some r0 := by decide

end DeltaReduce.NativeReplayVectors
