import DeltaReduce.NativeApplyResultJoin
import DeltaReduce.NativeApplyCertificateVectors
import DeltaReduce.NativeGraphVectors

/-! Original graph computation reused by component proof. Constructed
candidate is SYNTHETIC, not an original native capture or authority. -/
namespace DeltaReduce.NativeApplyResultVectors
open NativeBinding NativeApplyResult
set_option maxRecDepth 12000
set_option maxHeartbeats 3000000
set_option Elab.async false
def pre0 : Bytes := [100,101,108,116,97,114,101,100,117,99,101,46,48,48,56,46,109,111,100,101,108,46,118,49,0,49,57,59,45,49,57,59]
def hash0 : Bytes := [214,198,17,198,195,26,33,192,77,190,212,83,242,249,14,206,193,142,61,181,148,129,84,102,223,63,221,57,87,237,97,186]
def pre1 : Bytes := [100,101,108,116,97,114,101,100,117,99,101,46,48,48,56,46,111,112,116,105,109,105,122,101,114,46,118,49,0,50,59,45,50,59]
def hash1 : Bytes := [29,32,175,74,152,236,138,225,190,142,37,79,219,85,10,129,98,68,105,204,117,225,161,95,171,189,104,183,25,48,241,24]
def pre2 : Bytes := [100,101,108,116,97,114,101,100,117,99,101,46,48,48,56,46,109,111,100,101,108,46,118,49,0,50,48,59,45,50,48,59]
def hash2 : Bytes := [107,44,40,97,209,59,100,171,13,144,252,195,221,212,29,186,101,15,38,160,109,240,239,102,45,107,160,175,23,204,65,221]
def sha (raw : Bytes) : Bytes :=
  if raw = pre0 then hash0 else
  if raw = pre1 then hash1 else
  if raw = pre2 then hash2 else
  []
theorem sample0 : sha pre0 = hash0 := by decide
theorem sample1 : sha pre1 = hash1 := by decide
theorem sample2 : sha pre2 = hash2 := by decide
def values : Values := ⟨[19,-19],[2,-2],[20,-20],[2,-2]⟩
def expectedHashes : Digests := ⟨hash0,hash1,hash2,hash1⟩
def candidate : NativeApplyCertificate.Candidate :=
  { NativeApplyCertificateVectors.candidate with
    modelValues := decimalValues values.model, optimizerValues := decimalValues values.optimizer,
    model := idBytes hash0, optimizer := idBytes hash1,
    parent := idBytes hash2, parentOptimizer := idBytes hash1 }
theorem computedDigests : digests sha values = expectedHashes := by decide
theorem accepted : checkValues sha values candidate = some expectedHashes := by decide
theorem exactPreimages :
    rawValueInput .model candidate.modelValues = pre0 ∧
    rawValueInput .optimizer candidate.optimizerValues = pre1 := by decide
theorem originalGraphResult (native : NativeApply NativeGraphVectors.fixtureBinding)
    (computed : deriveNativeApply NativeGraphVectors.fixtureBinding = some native) :
    checkValues sha (nativeValues NativeGraphVectors.fixtureBinding native) candidate =
      some expectedHashes := by
  have body : native.body = NativeGraphVectors.expectedApply := by
    have pinned := NativeGraphVectors.nativeApplyMatchesOracle
    rw [computed] at pinned
    exact Option.some.inj pinned
  change checkValues sha ⟨native.body.nextModel,native.body.nextOptimizer,_,_⟩ candidate = _
  rw [body]
  exact accepted
theorem missingCoordinate : checkValues sha values {candidate with modelValues := [[49,57]]} = none := by decide
theorem reordered : checkValues sha values {candidate with modelValues := candidate.modelValues.reverse} = none := by decide
theorem wrongNumber : checkValues sha values {candidate with modelValues := [[57,57,57],[45,49,57]]} = none := by decide
theorem extraCoordinate : checkValues sha values {candidate with modelValues := candidate.modelValues ++ [[48]]} = none := by decide
theorem wrongOptimizer : checkValues sha values {candidate with optimizerValues := candidate.modelValues} = none := by decide
theorem wrongModelHash : checkValues sha values {candidate with model := candidate.optimizer} = none := by decide
theorem wrongOptimizerHash : checkValues sha values {candidate with optimizer := candidate.model} = none := by decide
theorem wrongParentModel : checkValues sha values {candidate with parent := candidate.model} = none := by decide
theorem wrongParentOptimizer : checkValues sha values {candidate with parentOptimizer := candidate.parent} = none := by decide
theorem changedPreimageNotApproved : checkValues sha {values with model := [999,-19]} candidate = none := by decide
theorem unavailableHash : checkValues (fun _ => []) values candidate = none := by decide
theorem shortHash : checkValues (fun _ => [1]) values candidate = none := by decide
theorem originalLabelHashesNotRewritten : checkValues sha values NativeApplyCertificateVectors.candidate = none := by decide
theorem signedEndpoints : decimalValues [-9223372036854775808,9223372036854775807] =
  [[45,57,50,50,51,51,55,50,48,51,54,56,53,52,55,55,53,56,48,56],[57,50,50,51,51,55,50,48,51,54,56,53,52,55,55,53,56,48,55]] := by decide
theorem oldNegativeZeroStillAccepted : NativeCertificateDecimal.parse false [45,48,48] = some 0 := by decide
theorem oldNegativeAliasStillAccepted : NativeCertificateDecimal.parse false [45,48,49] = some (-1) := by decide
theorem negativeZeroNotComputed : [45,48,48] ≠ asciiBytes (toString (0 : Int)) := by decide
theorem negativeAliasNotComputed : [45,48,49] ≠ asciiBytes (toString (-1 : Int)) := by decide
def sourceProfile : NativeApplyProfile.Profile :=
  ⟨NativeApplyCertificateVectors.profile.accumulator,[⟨[100,49],⟨1,1⟩⟩],⟨1,2⟩,⟨1,2⟩,1,
    asciiBytes "HALF_TOWARD_POSITIVE",⟨0,1⟩⟩
theorem numericProfile : ProfileMatches sourceProfile NativeGraphVectors.fixtureBinding.profile := by decide
theorem wrongLearning : ¬ ProfileMatches {sourceProfile with learning := ⟨1,3⟩} NativeGraphVectors.fixtureBinding.profile := by decide
theorem wrongMomentum : ¬ ProfileMatches {sourceProfile with momentum := ⟨0,1⟩} NativeGraphVectors.fixtureBinding.profile := by decide
theorem wrongDecay : ¬ ProfileMatches {sourceProfile with decay := ⟨1,1⟩} NativeGraphVectors.fixtureBinding.profile := by decide
theorem wrongDomain : ¬ ProfileMatches {sourceProfile with weights := [⟨[120],⟨1,1⟩⟩]} NativeGraphVectors.fixtureBinding.profile := by decide
theorem missingWeight : ¬ ProfileMatches {sourceProfile with weights := []} NativeGraphVectors.fixtureBinding.profile := by decide
theorem duplicateWeight : ¬ ProfileMatches {sourceProfile with weights := sourceProfile.weights ++ sourceProfile.weights} NativeGraphVectors.fixtureBinding.profile := by decide
theorem wrongRounding : ¬ ProfileMatches {sourceProfile with rounding := []} NativeGraphVectors.fixtureBinding.profile := by decide
theorem wrongNesterov : ¬ ProfileMatches {sourceProfile with nesterov := 0} NativeGraphVectors.fixtureBinding.profile := by decide
theorem numericGateDoesNotAuthenticateMetadata : checkValues sha values
    {candidate with context := {candidate.context with schema := [],config := [],arithmetic := []}, root := [],profile := []}
      = some expectedHashes := by decide
theorem numericProfileDoesNotAuthenticateAccumulator :
    ProfileMatches {sourceProfile with accumulator := []} NativeGraphVectors.fixtureBinding.profile := by decide
theorem opaqueAnchorCheckpointNotValueIdentity :
    asciiBytes NativeGraphVectors.anchor.context.parentCheckpoint ≠ idBytes hash2 := by decide
def leaf (p : ParameterBody) : NativeParameterLineage.Edge :=
  { NativeParameterVectors.finalizedEdge with certificate :=
    { NativeParameterVectors.finalizedEdge.certificate with common :=
      { NativeParameterVectors.finalizedEdge.certificate.common with
        domain := asciiBytes p.domain,shard := asciiBytes p.shard,denominator := p.denominator.toNat,
        numerators := decimalValues p.numerators } } }
def leaves := NativeGraphVectors.expectedBodies.map leaf
theorem allLeafNumbers : LeafMatches leaves NativeGraphVectors.expectedBodies := by decide
theorem missingLeaf : ¬ LeafMatches leaves.tail NativeGraphVectors.expectedBodies := by decide
theorem extraLeaf : ¬ LeafMatches (leaves ++ leaves) NativeGraphVectors.expectedBodies := by decide
theorem reorderedLeaves : ¬ LeafMatches leaves.reverse NativeGraphVectors.expectedBodies := by decide
theorem wrongNumerator : ¬ LeafMatches leaves
    (NativeGraphVectors.expectedBodies.map (fun p => {p with numerators := [999]})) := by decide
theorem scaledFractionNotEqual : ¬ LeafMatches leaves
    (NativeGraphVectors.expectedBodies.map (fun p => {p with denominator := p.denominator * 2, numerators := p.numerators.map (· * 2)})) := by decide
theorem missingSourceLeavesStillNumeric : LeafMatches
    (leaves.map (fun e => {e with certificate := {e.certificate with common := {e.certificate.common with leaves := []}}}))
    NativeGraphVectors.expectedBodies := by decide
end DeltaReduce.NativeApplyResultVectors
