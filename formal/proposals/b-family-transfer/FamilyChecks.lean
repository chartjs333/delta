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

end DeltaReduce.FamilyChecks
