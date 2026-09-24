import DeltaReduce.NativeGraphVectors
import DeltaReduce.RecoveryKernelVectors

/-! Exact pre-WAL records computed from the anchored graph. Finite input
codec/hash samples and synthetic metadata trust are not native execution. -/
namespace DeltaReduce.NativeVoteVectors
open NativeBinding NativeGraphVectors
set_option maxRecDepth 1000000
set_option maxHeartbeats 0
def voteTrust : NativeVoteTrust := ⟨fun _ _ => True⟩
-- First PARAMETER binding has no AggregateRootQC prerequisite.
def parameterAnchor : Anchor := { anchor with aggregate := none }
def parameterBinding : Binding codec syntheticTrust parameterAnchor store := {
  fixtureBinding with
  complete := by
    intro r member
    change r ∈ [anchor.authority] at member
    have eq : r = anchor.authority := by simpa using member
    subst r
    exact fixtureBinding.complete anchor.authority (by simp [Anchor.roots])
  aggregateBound := by intro r h; contradiction
}
def metadata0 : VoteMetadata := {
  actor := "validator-1", kind := .parameter "d1" "s1"
  voteContext := "NORMAL-PARAM-D1-S1:round-1"
  parentCertificate := [123,22,26,72,112,19,240,24,233,239,186,222,244,205,148,140,133,154,124,79,2,7,109,194,156,174,47,51,45,26,236,230]
  projection := fixtureBinding.authority.apc, logicalTime := 18
  recovered := true, validator := true }
def command0 : Bytes := [123,34,97,99,116,105,111,110,34,58,34,65,67,84,45,80,65,82,65,77,45,86,79,84,69,34,44,34,112,97,121,108,111,97,100,34,58,123,34,97,117,116,104,111,114,105,116,121,95,105,100,34,58,34,115,104,97,50,53,54,58,102,97,51,55,50,98,54,97,57,100,102,53,56,49,48,100,57,51,50,56,102,57,102,48,57,101,98,100,48,50,102,102,49,51,57,97,56,49,52,55,53,49,53,99,54,99,49,55,57,51,99,52,52,55,49,57,54,97,99,102,100,52,98,51,34,44,34,99,111,110,116,101,120,116,34,58,34,78,79,82,77,65,76,45,80,65,82,65,77,45,68,49,45,83,49,58,114,111,117,110,100,45,49,34,44,34,100,101,110,111,109,105,110,97,116,111,114,34,58,49,44,34,100,111,109,97,105,110,34,58,34,100,49,34,44,34,105,110,112,117,116,95,108,101,97,102,95,105,100,115,34,58,91,34,115,104,97,50,53,54,58,55,99,97,100,102,52,54,52,102,48,54,57,49,100,55,56,97,50,97,98,55,50,101,97,99,51,99,99,50,56,99,53,54,54,57,54,49,51,101,102,97,53,53,48,97,100,97,53,99,100,50,102,55,49,99,53,50,52,48,101,54,51,51,54,34,93,44,34,107,105,110,100,34,58,34,80,65,82,65,77,69,84,69,82,95,69,88,80,69,67,84,69,68,34,44,34,110,117,109,101,114,97,116,111,114,115,34,58,91,49,93,44,34,115,104,97,114,100,34,58,34,115,49,34,125,125]
def state0 : RecoveryKernel.State :=
  ⟨RecoveryKernelVectors.records.take 4, nativeCurrent anchor⟩
def prepared0 := prepareNativeFirst parameterBinding voteTrust metadata0
  True.intro .ready state0 command0
def metadata1 : VoteMetadata := {
  actor := "validator-1", kind := .parameter "d1" "s2"
  voteContext := "NORMAL-PARAM-D1-S2:round-1"
  parentCertificate := [123,22,26,72,112,19,240,24,233,239,186,222,244,205,148,140,133,154,124,79,2,7,109,194,156,174,47,51,45,26,236,230]
  projection := fixtureBinding.authority.apc, logicalTime := 22
  recovered := true, validator := true }
def command1 : Bytes := [123,34,97,99,116,105,111,110,34,58,34,65,67,84,45,80,65,82,65,77,45,86,79,84,69,34,44,34,112,97,121,108,111,97,100,34,58,123,34,97,117,116,104,111,114,105,116,121,95,105,100,34,58,34,115,104,97,50,53,54,58,102,97,51,55,50,98,54,97,57,100,102,53,56,49,48,100,57,51,50,56,102,57,102,48,57,101,98,100,48,50,102,102,49,51,57,97,56,49,52,55,53,49,53,99,54,99,49,55,57,51,99,52,52,55,49,57,54,97,99,102,100,52,98,51,34,44,34,99,111,110,116,101,120,116,34,58,34,78,79,82,77,65,76,45,80,65,82,65,77,45,68,49,45,83,50,58,114,111,117,110,100,45,49,34,44,34,100,101,110,111,109,105,110,97,116,111,114,34,58,49,44,34,100,111,109,97,105,110,34,58,34,100,49,34,44,34,105,110,112,117,116,95,108,101,97,102,95,105,100,115,34,58,91,34,115,104,97,50,53,54,58,53,52,51,53,49,100,55,56,50,55,99,102,56,49,98,52,99,53,56,102,56,97,98,57,50,54,48,50,101,54,55,49,56,51,102,51,53,49,101,101,48,48,101,52,48,54,100,101,53,52,101,57,56,48,49,53,55,56,53,54,101,54,54,54,34,93,44,34,107,105,110,100,34,58,34,80,65,82,65,77,69,84,69,82,95,69,88,80,69,67,84,69,68,34,44,34,110,117,109,101,114,97,116,111,114,115,34,58,91,45,50,93,44,34,115,104,97,114,100,34,58,34,115,50,34,125,125]
def state1 : RecoveryKernel.State :=
  ⟨RecoveryKernelVectors.records.take 5, nativeCurrent anchor⟩
def prepared1 := prepareNativeFirst parameterBinding voteTrust metadata1
  True.intro .ready state1 command1
def metadata2 : VoteMetadata := {
  actor := "validator-1", kind := .apply
  voteContext := "NORMAL-APPLY:round-1"
  parentCertificate := [92,60,217,210,64,20,252,69,102,161,246,239,138,94,60,247,122,14,114,51,116,246,20,75,193,31,209,229,228,227,119,152]
  projection := (anchor.aggregate.getD anchor.authority), logicalTime := 31
  recovered := true, validator := true }
def command2 : Bytes := [123,34,97,99,116,105,111,110,34,58,34,65,67,84,45,65,80,80,76,89,45,86,79,84,69,34,44,34,112,97,121,108,111,97,100,34,58,123,34,97,103,103,114,101,103,97,116,101,95,105,100,34,58,34,115,104,97,50,53,54,58,52,101,99,100,53,49,57,56,100,55,49,57,57,52,99,97,57,99,50,97,51,50,56,55,50,53,99,50,100,57,102,99,56,57,55,55,53,55,49,53,55,99,101,54,51,102,52,52,102,48,56,49,52,52,57,101,51,100,52,57,99,99,48,98,34,44,34,97,117,116,104,111,114,105,116,121,95,105,100,34,58,34,115,104,97,50,53,54,58,102,97,51,55,50,98,54,97,57,100,102,53,56,49,48,100,57,51,50,56,102,57,102,48,57,101,98,100,48,50,102,102,49,51,57,97,56,49,52,55,53,49,53,99,54,99,49,55,57,51,99,52,52,55,49,57,54,97,99,102,100,52,98,51,34,44,34,107,105,110,100,34,58,34,65,80,80,76,89,95,69,88,80,69,67,84,69,68,34,44,34,110,101,120,116,95,109,111,100,101,108,34,58,91,49,57,44,45,49,57,93,44,34,110,101,120,116,95,109,111,100,101,108,95,104,97,115,104,34,58,34,115,104,97,50,53,54,58,100,54,99,54,49,49,99,54,99,51,49,97,50,49,99,48,52,100,98,101,100,52,53,51,102,50,102,57,48,101,99,101,99,49,56,101,51,100,98,53,57,52,56,49,53,52,54,54,100,102,51,102,100,100,51,57,53,55,101,100,54,49,98,97,34,44,34,110,101,120,116,95,111,112,116,105,109,105,122,101,114,34,58,91,50,44,45,50,93,44,34,110,101,120,116,95,111,112,116,105,109,105,122,101,114,95,104,97,115,104,34,58,34,115,104,97,50,53,54,58,49,100,50,48,97,102,52,97,57,56,101,99,56,97,101,49,98,101,56,101,50,53,52,102,100,98,53,53,48,97,56,49,54,50,52,52,54,57,99,99,55,53,101,49,97,49,53,102,97,98,98,100,54,56,98,55,49,57,51,48,102,49,49,56,34,44,34,112,97,114,97,109,101,116,101,114,95,98,111,100,121,95,105,100,115,34,58,91,34,115,104,97,50,53,54,58,98,57,101,97,101,49,55,98,100,51,101,54,97,55,51,97,56,49,97,102,51,55,54,100,55,100,99,56,50,53,51,48,97,98,54,52,98,99,48,48,100,98,50,97,99,49,99,101,97,101,49,97,48,55,97,100,97,48,49,57,48,56,101,51,34,44,34,115,104,97,50,53,54,58,100,56,51,49,51,57,99,57,54,56,97,55,53,101,50,57,97,56,53,54,54,97,48,55,55,55,55,56,54,101,55,101,98,54,48,51,100,101,50,53,48,55,102,50,49,99,102,49,98,51,49,54,48,52,102,54,97,98,97,57,57,98,102,54,34,93,125,125]
def state2 : RecoveryKernel.State :=
  ⟨RecoveryKernelVectors.records.take 7, nativeCurrent anchor⟩
def prepared2 := prepareNativeFirst fixtureBinding voteTrust metadata2
  True.intro .ready state2 command2
def everyASCII : String := String.ofList ((List.range 128).map Char.ofNat)
def envelope0 : Bytes := [123,34,97,99,116,105,111,110,95,105,100,34,58,34,65,67,84,45,80,65,82,65,77,45,86,79,84,69,34,44,34,97,99,116,111,114,95,105,100,34,58,34,118,97,108,105,100,97,116,111,114,45,49,34,44,34,98,111,100,121,95,104,97,115,104,34,58,34,115,104,97,50,53,54,58,98,57,101,97,101,49,55,98,100,51,101,54,97,55,51,97,56,49,97,102,51,55,54,100,55,100,99,56,50,53,51,48,97,98,54,52,98,99,48,48,100,98,50,97,99,49,99,101,97,101,49,97,48,55,97,100,97,48,49,57,48,56,101,51,34,44,34,104,101,105,103,104,116,34,58,49,44,34,112,97,114,101,110,116,95,104,97,115,104,101,115,34,58,91,34,115,104,97,50,53,54,58,55,98,49,54,49,97,52,56,55,48,49,51,102,48,49,56,101,57,101,102,98,97,100,101,102,52,99,100,57,52,56,99,56,53,57,97,55,99,52,102,48,50,48,55,54,100,99,50,57,99,97,101,50,102,51,51,50,100,49,97,101,99,101,54,34,93,44,34,114,111,117,110,100,95,105,100,34,58,34,114,111,117,110,100,45,49,34,44,34,118,97,108,105,100,97,116,111,114,95,101,112,111,99,104,34,58,34,101,112,111,99,104,45,49,34,44,34,118,111,116,101,95,99,111,110,116,101,120,116,95,105,100,34,58,34,78,79,82,77,65,76,45,80,65,82,65,77,45,68,49,45,83,49,58,114,111,117,110,100,45,49,34,125]
def effect0 : Bytes := [123,34,112,114,111,106,101,99,116,105,111,110,95,118,101,114,115,105,111,110,34,58,34,100,114,97,102,116,49,34,44,34,118,111,116,101,34,58,123,34,97,99,116,105,111,110,95,105,100,34,58,34,65,67,84,45,80,65,82,65,77,45,86,79,84,69,34,44,34,97,99,116,111,114,95,105,100,34,58,34,118,97,108,105,100,97,116,111,114,45,49,34,44,34,98,111,100,121,95,104,97,115,104,34,58,34,115,104,97,50,53,54,58,98,57,101,97,101,49,55,98,100,51,101,54,97,55,51,97,56,49,97,102,51,55,54,100,55,100,99,56,50,53,51,48,97,98,54,52,98,99,48,48,100,98,50,97,99,49,99,101,97,101,49,97,48,55,97,100,97,48,49,57,48,56,101,51,34,44,34,104,101,105,103,104,116,34,58,49,44,34,112,97,114,101,110,116,95,104,97,115,104,101,115,34,58,91,34,115,104,97,50,53,54,58,55,98,49,54,49,97,52,56,55,48,49,51,102,48,49,56,101,57,101,102,98,97,100,101,102,52,99,100,57,52,56,99,56,53,57,97,55,99,52,102,48,50,48,55,54,100,99,50,57,99,97,101,50,102,51,51,50,100,49,97,101,99,101,54,34,93,44,34,114,111,117,110,100,95,105,100,34,58,34,114,111,117,110,100,45,49,34,44,34,118,97,108,105,100,97,116,111,114,95,101,112,111,99,104,34,58,34,101,112,111,99,104,45,49,34,44,34,118,111,116,101,95,99,111,110,116,101,120,116,95,105,100,34,58,34,78,79,82,77,65,76,45,80,65,82,65,77,45,68,49,45,83,49,58,114,111,117,110,100,45,49,34,125,125]
theorem nativeRecord0MatchesDiagnostic : prepared0.map NativePrepared.record = some RecoveryKernelVectors.record4 := by decide
theorem nativeRecord0Replays : (prepared0.bind (fun p => RecoveryKernel.step RecoveryKernelVectors.adapter state0 (.vote p.record))) = some ⟨RecoveryKernelVectors.records.take 5, nativeCurrent anchor⟩ := by decide
theorem nativeRecord0ChangedCommandRejected : (prepareNativeFirst parameterBinding voteTrust metadata0 True.intro .ready state0 (command0 ++ [32])).isNone = true := by decide
theorem nativeRecord0ChangedModelRejected : (prepareNativeFirst parameterBinding voteTrust metadata0 True.intro .ready { state0 with current := { state0.current with model := [] } } command0).isNone = true := by decide
theorem nativeRecord0ChangedOptimizerRejected : (prepareNativeFirst parameterBinding voteTrust metadata0 True.intro .ready { state0 with current := { state0.current with optimizer := [] } } command0).isNone = true := by decide
theorem nativeRecord0ChangedCheckpointRejected : (prepareNativeFirst parameterBinding voteTrust metadata0 True.intro .ready { state0 with current := { state0.current with checkpoint := [] } } command0).isNone = true := by decide
theorem nativeRecord0DeadlineRejected : (prepareNativeFirst parameterBinding voteTrust { metadata0 with logicalTime := anchor.context.hardDeadline } True.intro .ready state0 command0).isNone = true := by decide
theorem nativeRecord0RecoveryRequired : (prepareNativeFirst parameterBinding voteTrust { metadata0 with recovered := false } True.intro .ready state0 command0).isNone = true := by decide
theorem nativeRecord0WrongRoleRejected : (prepareNativeFirst parameterBinding voteTrust { metadata0 with validator := false } True.intro .ready state0 command0).isNone = true := by decide
theorem nativeRecord0DuplicateRejected : (prepareNativeFirst parameterBinding voteTrust metadata0 True.intro .ready { state0 with votes := state0.votes ++ [RecoveryKernelVectors.record4] } command0).isNone = true := by decide
theorem nativeRecord1MatchesDiagnostic : prepared1.map NativePrepared.record = some RecoveryKernelVectors.record5 := by decide
theorem nativeRecord1Replays : (prepared1.bind (fun p => RecoveryKernel.step RecoveryKernelVectors.adapter state1 (.vote p.record))) = some ⟨RecoveryKernelVectors.records.take 6, nativeCurrent anchor⟩ := by decide
theorem nativeRecord1ChangedCommandRejected : (prepareNativeFirst parameterBinding voteTrust metadata1 True.intro .ready state1 (command1 ++ [32])).isNone = true := by decide
theorem nativeRecord1ChangedModelRejected : (prepareNativeFirst parameterBinding voteTrust metadata1 True.intro .ready { state1 with current := { state1.current with model := [] } } command1).isNone = true := by decide
theorem nativeRecord1ChangedOptimizerRejected : (prepareNativeFirst parameterBinding voteTrust metadata1 True.intro .ready { state1 with current := { state1.current with optimizer := [] } } command1).isNone = true := by decide
theorem nativeRecord1ChangedCheckpointRejected : (prepareNativeFirst parameterBinding voteTrust metadata1 True.intro .ready { state1 with current := { state1.current with checkpoint := [] } } command1).isNone = true := by decide
theorem nativeRecord1DeadlineRejected : (prepareNativeFirst parameterBinding voteTrust { metadata1 with logicalTime := anchor.context.hardDeadline } True.intro .ready state1 command1).isNone = true := by decide
theorem nativeRecord1RecoveryRequired : (prepareNativeFirst parameterBinding voteTrust { metadata1 with recovered := false } True.intro .ready state1 command1).isNone = true := by decide
theorem nativeRecord1WrongRoleRejected : (prepareNativeFirst parameterBinding voteTrust { metadata1 with validator := false } True.intro .ready state1 command1).isNone = true := by decide
theorem nativeRecord1DuplicateRejected : (prepareNativeFirst parameterBinding voteTrust metadata1 True.intro .ready { state1 with votes := state1.votes ++ [RecoveryKernelVectors.record5] } command1).isNone = true := by decide
theorem nativeRecord2MatchesDiagnostic : prepared2.map NativePrepared.record = some RecoveryKernelVectors.record7 := by decide
theorem nativeRecord2Replays : (prepared2.bind (fun p => RecoveryKernel.step RecoveryKernelVectors.adapter state2 (.vote p.record))) = some ⟨RecoveryKernelVectors.records.take 8, nativeCurrent anchor⟩ := by decide
theorem nativeRecord2ChangedCommandRejected : (prepareNativeFirst fixtureBinding voteTrust metadata2 True.intro .ready state2 (command2 ++ [32])).isNone = true := by decide
theorem nativeRecord2ChangedModelRejected : (prepareNativeFirst fixtureBinding voteTrust metadata2 True.intro .ready { state2 with current := { state2.current with model := [] } } command2).isNone = true := by decide
theorem nativeRecord2ChangedOptimizerRejected : (prepareNativeFirst fixtureBinding voteTrust metadata2 True.intro .ready { state2 with current := { state2.current with optimizer := [] } } command2).isNone = true := by decide
theorem nativeRecord2ChangedCheckpointRejected : (prepareNativeFirst fixtureBinding voteTrust metadata2 True.intro .ready { state2 with current := { state2.current with checkpoint := [] } } command2).isNone = true := by decide
theorem nativeRecord2DeadlineRejected : (prepareNativeFirst fixtureBinding voteTrust { metadata2 with logicalTime := anchor.context.hardDeadline } True.intro .ready state2 command2).isNone = true := by decide
theorem nativeRecord2RecoveryRequired : (prepareNativeFirst fixtureBinding voteTrust { metadata2 with recovered := false } True.intro .ready state2 command2).isNone = true := by decide
theorem nativeRecord2WrongRoleRejected : (prepareNativeFirst fixtureBinding voteTrust { metadata2 with validator := false } True.intro .ready state2 command2).isNone = true := by decide
theorem nativeRecord2DuplicateRejected : (prepareNativeFirst fixtureBinding voteTrust metadata2 True.intro .ready { state2 with votes := state2.votes ++ [RecoveryKernelVectors.record7] } command2).isNone = true := by decide
theorem missingAuthorityCannotPrepare : prepareNativeAvailable (codec := codec) (store := store) (trust := syntheticTrust) (anchor := parameterAnchor) none voteTrust metadata0 True.intro .ready state0 command0 = none := by decide
theorem everyASCIIEscapeMatchesPython : jsonASCII everyASCII = some [34,92,117,48,48,48,48,92,117,48,48,48,49,92,117,48,48,48,50,92,117,48,48,48,51,92,117,48,48,48,52,92,117,48,48,48,53,92,117,48,48,48,54,92,117,48,48,48,55,92,98,92,116,92,110,92,117,48,48,48,98,92,102,92,114,92,117,48,48,48,101,92,117,48,48,48,102,92,117,48,48,49,48,92,117,48,48,49,49,92,117,48,48,49,50,92,117,48,48,49,51,92,117,48,48,49,52,92,117,48,48,49,53,92,117,48,48,49,54,92,117,48,48,49,55,92,117,48,48,49,56,92,117,48,48,49,57,92,117,48,48,49,97,92,117,48,48,49,98,92,117,48,48,49,99,92,117,48,48,49,100,92,117,48,48,49,101,92,117,48,48,49,102,32,33,92,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57,58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,92,93,94,95,96,97,98,99,100,101,102,103,104,105,106,107,108,109,110,111,112,113,114,115,116,117,118,119,120,121,122,123,124,125,126,92,117,48,48,55,102,34] := by decide
theorem unicodeMetadataRejected : jsonASCII "é" = none := by decide
theorem firstParameterNeedsNoAggregate : parameterAnchor.aggregate = none := by decide
theorem wrongParameterContextRejected : (deriveExpectedNativeVote parameterBinding { metadata0 with voteContext := "other" }).isNone = true := by decide
theorem wrongProjectionRejected : (deriveExpectedNativeVote parameterBinding { metadata0 with projection := fixtureBinding.authority.isc }).isNone = true := by decide
theorem shortCertificateIdRejected : (deriveExpectedNativeVote parameterBinding { metadata0 with parentCertificate := [] }).isNone = true := by decide
theorem unknownModeCannotPrepare : (prepareNativeFirst parameterBinding voteTrust metadata0 True.intro .unknown state0 command0).isNone = true := by decide
theorem emptyActorCannotPrepare : (prepareNativeFirst parameterBinding voteTrust { metadata0 with actor := "" } True.intro .ready state0 command0).isNone = true := by decide
theorem oversizedActorCannotPrepare : (prepareNativeFirst parameterBinding voteTrust { metadata0 with actor := String.ofList (List.replicate 257 'a') } True.intro .ready state0 command0).isNone = true := by decide
theorem shortReceiptHashRejected : (encodeDiagnosticReceipt { codec with hash := fun _ => [] } command0 [] [] 1).isNone = true := by decide
theorem malformedNativeModelIdentityRejected : ¬ NativeFresh { anchor with currentModelHash := [] } metadata0 .ready { state0 with current := nativeCurrent { anchor with currentModelHash := [] } } := by decide
theorem malformedNativeOptimizerIdentityRejected : ¬ NativeFresh { anchor with currentOptimizerHash := [] } metadata0 .ready { state0 with current := nativeCurrent { anchor with currentOptimizerHash := [] } } := by decide
theorem maximumReceiptSequenceMatchesPython : encodeDiagnosticReceipt codec command0 envelope0 effect0 9223372036854775807 = some [123,34,99,111,109,109,97,110,100,95,105,100,34,58,34,115,104,97,50,53,54,58,98,49,51,98,55,51,50,55,98,55,99,56,100,52,102,50,57,51,50,49,54,102,48,56,99,50,98,99,53,51,100,100,52,98,100,54,52,98,56,52,101,55,101,50,51,97,100,101,98,48,51,102,48,52,102,99,55,57,51,98,101,48,57,48,34,44,34,101,102,102,101,99,116,95,105,100,34,58,34,115,104,97,50,53,54,58,53,52,57,101,49,53,48,56,51,55,100,49,100,55,52,50,97,52,50,50,50,51,99,51,102,101,50,49,98,101,98,51,102,56,54,97,56,57,53,52,98,54,52,101,48,48,52,101,51,97,101,52,101,53,49,101,102,100,55,51,99,98,97,57,34,44,34,112,114,111,106,101,99,116,105,111,110,95,118,101,114,115,105,111,110,34,58,34,100,114,97,102,116,49,34,44,34,115,101,113,117,101,110,99,101,34,58,57,50,50,51,51,55,50,48,51,54,56,53,52,55,55,53,56,48,55,44,34,118,111,116,101,34,58,123,34,97,99,116,105,111,110,95,105,100,34,58,34,65,67,84,45,80,65,82,65,77,45,86,79,84,69,34,44,34,97,99,116,111,114,95,105,100,34,58,34,118,97,108,105,100,97,116,111,114,45,49,34,44,34,98,111,100,121,95,104,97,115,104,34,58,34,115,104,97,50,53,54,58,98,57,101,97,101,49,55,98,100,51,101,54,97,55,51,97,56,49,97,102,51,55,54,100,55,100,99,56,50,53,51,48,97,98,54,52,98,99,48,48,100,98,50,97,99,49,99,101,97,101,49,97,48,55,97,100,97,48,49,57,48,56,101,51,34,44,34,104,101,105,103,104,116,34,58,49,44,34,112,97,114,101,110,116,95,104,97,115,104,101,115,34,58,91,34,115,104,97,50,53,54,58,55,98,49,54,49,97,52,56,55,48,49,51,102,48,49,56,101,57,101,102,98,97,100,101,102,52,99,100,57,52,56,99,56,53,57,97,55,99,52,102,48,50,48,55,54,100,99,50,57,99,97,101,50,102,51,51,50,100,49,97,101,99,101,54,34,93,44,34,114,111,117,110,100,95,105,100,34,58,34,114,111,117,110,100,45,49,34,44,34,118,97,108,105,100,97,116,111,114,95,101,112,111,99,104,34,58,34,101,112,111,99,104,45,49,34,44,34,118,111,116,101,95,99,111,110,116,101,120,116,95,105,100,34,58,34,78,79,82,77,65,76,45,80,65,82,65,77,45,68,49,45,83,49,58,114,111,117,110,100,45,49,34,125,125] := by decide
theorem zeroReceiptSequenceRejected : (encodeDiagnosticReceipt codec command0 envelope0 effect0 0).isNone = true := by decide
theorem overflowReceiptSequenceRejected : (encodeDiagnosticReceipt codec command0 envelope0 effect0 9223372036854775808).isNone = true := by decide

end DeltaReduce.NativeVoteVectors
