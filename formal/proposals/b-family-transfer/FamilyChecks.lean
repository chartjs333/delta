import FamilyRelation
import FamilyRoot
import ManifestFamily

/- Small numeric regression checks and original-source instantiations. No new
vote, certificate, WAL record, authenticated configuration or trace is created. -/
namespace DeltaReduce.FamilyChecks
open NativeBinding ApplyKernel FamilyGuards

def wideProfile : NativeApplyProfile.Profile := {
  accumulator := asciiBytes ("sha256:" ++ String.ofList (List.replicate 64 '0'))
  weights := [⟨asciiBytes "domain",⟨1,1⟩⟩]
  learning := ⟨1,9223372036854775808⟩
  momentum := ⟨0,1⟩
  nesterov := 1
  rounding := asciiBytes "HALF_TOWARD_POSITIVE"
  decay := ⟨0,1⟩ }

theorem unsignedDenominatorIsOriginalDomain : NativeApplyProfile.Valid wideProfile := by decide +kernel

theorem unsignedOptimizerComputes :
    (nativeOptimizerVector wideProfile [10,-10] [2,-2] [1,-1]).map
      (fun values => (values.map OptimizerValues.nextModel,values.map OptimizerValues.nextOptimizer)) =
        some ([10,-10],[1,-1]) := by decide +kernel

theorem oldProfileAdapterExcludesThisDomain :
    ¬ ParameterKernel.ReducedNonnegative minInput maxInput
      (NativeApplyResult.fraction wideProfile.learning).numerator
      (NativeApplyResult.fraction wideProfile.learning).denominator := by decide +kernel

theorem roundingBothNegativeBranches :
    checkedNativeRound (-3) 2 = some (-1) ∧ checkedNativeRound (-4) 3 = some (-1) ∧
    checkedNativeRound (-5) 3 = some (-2) := by decide +kernel

theorem nativeMinimumDivisionGuardRetained :
    checkedNativeRound minInput 1 = none ∧ checkedNativeRound minInput 2 = some (-4611686018427387904) := by decide +kernel

theorem zeroLearningDoesNotHideEarlierOverflow :
    nativeOptimizer 0 maxInput 1 ⟨0,1⟩ ⟨1,1⟩ ⟨0,1⟩ = none := by decide +kernel

theorem vectorShapeIsExact :
    nativeOptimizerVector wideProfile [1,2] [0] [1,2] = none ∧
    nativeOptimizerVector wideProfile [1] [0] [1,2] = none := by decide +kernel

theorem originalWidthsStillPreserved :
    List.ofFn (ManifestFamily.layout NativeManifestVectors.wholeManifest).width = [4,8,8,8,8] :=
  ManifestFamily.originalWidths

theorem originalCompleteValuesStillReconstruct :
    ShardFamily.ordered (ShardFamily.reconstruct ManifestFamily.original) =
      NativeManifestVectors.bound.blocks.map (fun q => q.block.frame.values) :=
  ManifestFamily.originalFullValues

/- A small regression for the already frozen OMIT_UNAVAILABLE and unsigned
denominator boundaries. These are diagnostic values, not new native objects. -/
def omittedInput : PublicArithmeticInputs.Image := {
  tickets := [⟨"kept","domain",⟨1,1⟩,[3,-4]⟩]
  domains := [⟨"domain",1,[⟨1,1⟩,⟨1,1⟩]⟩]
  shards := ["left","right"]
  profile := NativeStateArtifacts.profileValue 64 ⟨1,1⟩ wideProfile
  mixtureDenominator := 1
  model := [("left",10),("right",-10)]
  optimizer := [("left",0),("right",0)]
  limit := maxInput }

def omittedConfigured : List Ticket := [⟨"kept","domain"⟩,⟨"omitted","domain"⟩]

theorem omittedCompletionCoversConfigured :
    FamilyInputs.CompletionCoverage omittedInput omittedConfigured := by decide +kernel

theorem omittedSelectionRecoversOriginalRows :
    FamilyInputs.memberTickets ["kept"]
      (FamilyInputs.completedImage omittedInput omittedConfigured).tickets = omittedInput.tickets := by
  exact FamilyInputs.completionSelectedRowsExact _ _ _ omittedCompletionCoversConfigured.2.1
    omittedCompletionCoversConfigured.2.2.1

theorem omittedCannotAlterActiveDomain :
    FamilyInputs.complete omittedInput [⟨"kept","other"⟩,⟨"omitted","domain"⟩] = none := by decide +kernel

theorem missingOrDuplicatedConfiguredReject :
    FamilyInputs.complete omittedInput [⟨"omitted","domain"⟩] = none ∧
    FamilyInputs.complete omittedInput [⟨"kept","domain"⟩,⟨"kept","domain"⟩] = none := by decide +kernel

theorem completedUnsignedImageNumericallyValid :
    FamilyInputs.InputNumericGuards (FamilyInputs.completedImage omittedInput omittedConfigured) := by
  apply FamilyInputs.completedImageNumericGuards
  · decide +kernel
  · exact omittedCompletionCoversConfigured.2.2.2.1

def omittedVocabulary : PublicArithmeticInputs.Vocabulary := {
  ticket := fun name => if name = "kept" then some "T\"1" else if name = "omitted" then some "T\\2" else none
  domain := fun name => if name = "domain" then some "D" else none
  shard := fun name => if name = "left" then some "S1" else if name = "right" then some "S2" else none
  tickets := ["T\"1","T\\2"]
  domains := ["D"]
  shards := ["S1","S2"]
  models := ["T\"1","T\\2","D","S1","S2"] }

theorem omittedInputPrimitiveNamespaces :
    FamilyAuthority.InputEncodingPrimitives omittedVocabulary (FamilyInputs.completedImage omittedInput omittedConfigured) := by
  constructor <;> decide +kernel

theorem completeUnsignedInputEncodes :
    ∃ encoded, PublicArithmeticInputs.encodeImage omittedVocabulary
      (FamilyInputs.completedImage omittedInput omittedConfigured) = some encoded :=
  FamilyAuthority.inputEncoderTotal completedUnsignedImageNumericallyValid omittedInputPrimitiveNamespaces

theorem unsignedCommonDenominatorParameterAccepted :
    FamilyParameter.publicParameterRows maxInput 9223372036854775808
      [⟨1,9223372036854775808,[3]⟩] = some 3 := by decide +kernel

theorem unsignedCommonDenominatorStillChecksEachProduct :
    FamilyParameter.publicParameterRows maxInput 9223372036854775808
      [⟨1,1,[2]⟩] = none := by decide +kernel

theorem directApplyUsesUnsignedProfile :
    (checkOriginalApplyMath wideProfile [10,-10] [2,-2] [⟨⟨1,1⟩,[1,-1]⟩]).map
      (fun p => (p.nextModel,p.nextOptimizer)) = some ([10,-10],[1,-1]) := by decide +kernel

theorem directApplyRejectsUnnormalizedWeights :
    checkOriginalApplyMath { wideProfile with weights := [⟨asciiBytes "domain",⟨1,2⟩⟩] }
      [10] [0] [⟨⟨1,2⟩,[1]⟩] = none := by decide +kernel

theorem nativeLabelsRemainInjective (a b : Bytes)
    (same : NativeVectorLayout.text a = NativeVectorLayout.text b) : a = b :=
  FamilyInputs.originalLabelInjective same

end DeltaReduce.FamilyChecks
