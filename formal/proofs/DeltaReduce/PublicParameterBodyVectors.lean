import DeltaReduce.PublicParameterJoin
import DeltaReduce.PublicAuthorityVectors

namespace DeltaReduce.PublicParameterBodyVectors
open NativeBinding NativeInputProjection PublicState PublicAuthority PublicParameterBody NativeGraphVectors
set_option Elab.async false
set_option maxRecDepth 16000
set_option maxHeartbeats 4000000

def limit127 : ModelLimit := ⟨127,by decide,by decide⟩
def bounded (denominator : Int) (rows : List ParameterKernel.Row) : Option (List Int) :=
  ParameterKernel.checkedParameter (-128) 127 minInput maxInput denominator 1 rows
def wide (denominator : Int) (rows : List ParameterKernel.Row) : Option (List Int) :=
  ParameterKernel.checkedParameter minInput maxInput minInput maxInput denominator 1 rows

theorem originalNativeFirstNarrow : ((deriveParameter fixtureBinding "d1" "s1").bind
    (fun n => (narrow n limit127).map (fun x => x.scalar.value))) = some 1 := by decide +kernel
theorem originalNativeSecondNarrow : ((deriveParameter fixtureBinding "d1" "s2").bind
    (fun n => (narrow n limit127).map (fun x => x.scalar.value))) = some (-2) := by decide +kernel
theorem originalUnplannedStillRejects : ((deriveParameter fixtureBinding "d2" "s1").bind
    (fun n => (narrow n limit127).map (fun x => x.scalar.value))) = none := by decide +kernel

theorem minimumNarrowAccepted : bounded 1 [⟨1,1,[-128]⟩] = some [-128] := by decide +kernel
theorem minimumArithmeticFailsSeparateResultGuard : resultFits limit127 (-128) = false := by decide +kernel
theorem minimumPublicResultAccepted : resultFits limit127 (-127) = true := by decide +kernel
theorem maximumNarrowAccepted : bounded 1 [⟨1,1,[127]⟩] = some [127] := by decide +kernel
theorem firstPositiveOutsideRejected : bounded 1 [⟨1,1,[128]⟩] = none := by decide +kernel
theorem firstNegativeOutsideRejected : bounded 1 [⟨1,1,[-129]⟩] = none := by decide +kernel
theorem samePositiveAcceptedNativeWidth : wide 1 [⟨1,1,[128]⟩] = some [128] := by decide +kernel
theorem coefficientOverflowAtZeroOutput : bounded 1 [⟨128,1,[0]⟩] = none := by decide +kernel
theorem coefficientOverflowFitsNativeWidth : wide 1 [⟨128,1,[0]⟩] = some [0] := by decide +kernel
theorem coefficientPrefixOverflowAtZeroOutput : bounded 1 [⟨70,1,[0]⟩,⟨70,1,[0]⟩] = none := by decide +kernel
theorem productCancellationCannotHideOverflow : bounded 1 [⟨2,1,[64]⟩,⟨2,1,[-64]⟩] = none := by decide +kernel
theorem productCancellationAcceptedNativeWidth : wide 1 [⟨2,1,[64]⟩,⟨2,1,[-64]⟩] = some [0] := by decide +kernel
theorem prefixCancellationCannotHideOverflow : bounded 1 [⟨1,1,[70]⟩,⟨1,1,[70]⟩,⟨1,1,[-70]⟩] = none := by decide +kernel
theorem prefixCancellationAcceptedNativeWidth : wide 1 [⟨1,1,[70]⟩,⟨1,1,[70]⟩,⟨1,1,[-70]⟩] = some [70] := by decide +kernel
theorem unequalFractions : bounded 6 [⟨1,2,[3]⟩,⟨1,3,[-4]⟩] = some [1] := by decide +kernel
theorem nondividingRejected : bounded 2 [⟨1,3,[1]⟩] = none := by decide +kernel
theorem negativeWeightRejected : bounded 1 [⟨-1,1,[0]⟩] = none := by decide +kernel
theorem vectorNotSilentlyScalarized : bounded 1 [⟨1,1,[1,2]⟩] = none := by decide +kernel
theorem emptyNotPadded : bounded 1 [] = none := by decide +kernel
theorem zeroWeightRetainsNativeInput : bounded 1 [⟨0,1,[maxInput]⟩] = some [0] := by decide +kernel
-- Input Q range is separately checked by NativeInputProjection.Projected.
-- This low-level row calculation alone cannot admit the preceding example.
theorem denominatorBoundIsExtraRepresentationRestriction : bounded 128 [⟨1,128,[1]⟩] = none := by decide +kernel

def fixtureFields (number : Int) : List (String × Value) :=
  PublicParameterBody.fields PublicAuthorityVectors.apc (.model "profile1") PublicAuthorityVectors.authority
    (.model "coeff1") (.model "configA") (.model "d1") PublicAuthorityVectors.ec PublicAuthorityVectors.isc
    (.model "parent1") PublicAuthorityVectors.round (.model "schema1") PublicAuthorityVectors.seed (.model "shard1") number
def fixtureBody : Value := record (fixtureFields 1)

theorem fifteenFieldsPresent : (fixtureFields 1).map Prod.fst = parameterFieldNames := rfl
theorem completeBodyCanonical : canonical PublicAuthorityVectors.vocabulary.models fixtureBody = true := by decide +kernel
theorem bodyHasFullAuthority : readField fixtureBody "authority" = some PublicAuthorityVectors.authority := rfl
theorem bodyHasActualNumber : readField fixtureBody "value" = some (.integer 1) := rfl
theorem metadataAndNumberAreDifferentFields : readField fixtureBody "domain" = some (.model "d1") ∧
    readField fixtureBody "shard" = some (.model "shard1") := ⟨rfl,rfl⟩
theorem fullBodyRetainsAllParents : readField fixtureBody "apc" = some PublicAuthorityVectors.apc ∧
    readField fixtureBody "ec" = some PublicAuthorityVectors.ec ∧
    readField fixtureBody "isc" = some PublicAuthorityVectors.isc := ⟨rfl,rfl,rfl⟩
theorem wrongNumberChangesWholeBody : record (fixtureFields (-2)) ≠ fixtureBody := by decide +kernel
theorem numericOnlyCounterexampleLacksAuthority : readField (record [("value",.integer 1)]) "authority" = none := rfl

-- The general rejection theorem applies without expanding the native graph,
-- full states, or dependent row proofs into one giant reduction.
theorem previousNumericOnlyBodyRejected {codec store trust anchor binding corpus limit input vocabulary metadataTrust source}
    (authority : PublicAuthority.Projection (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (corpus := corpus) (limit := limit) input vocabulary (metadataTrust := metadataTrust) source)
    {domain shard} (native : DerivedParameter binding domain shard) :
    PublicParameterBody.check authority native (record [("value",.integer 1)]) = none :=
  missingAuthorityRejected authority native _ numericOnlyCounterexampleLacksAuthority

end DeltaReduce.PublicParameterBodyVectors
