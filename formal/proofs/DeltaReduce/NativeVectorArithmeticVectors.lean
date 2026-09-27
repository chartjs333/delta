import DeltaReduce.NativeVectorArithmetic
import DeltaReduce.NativeManifestVectors
import DeltaReduce.NativeAccumulatorVectors
import DeltaReduce.NativePlanCoefficientVectors

/-! Original layout/components plus separately synthetic mathematical rows.
No combined whole-policy/Q source-load execution or authenticated source. -/
namespace DeltaReduce.NativeVectorArithmeticVectors
open NativeVectorContext NativeVectorArithmetic
open NativeVoteBytes (ascii)

def original := NativeManifestVectors.bound
theorem originalCompatible : Compatible original original := ⟨rfl,rfl,rfl⟩
theorem originalSlots : original.blocks.map (fun q => (shape q).entry) =
    original.plan.plan.entries := originalPlanSlots NativeManifestVectors.wholeManifest
theorem actualWidths : original.blocks.map (fun q => (shape q).entry.count) =
    [4,8,8,8,8] := by decide
theorem actualLocations : original.blocks.map (fun q => (shape q).entry.start) =
    [0,4,12,20,28] := by decide
theorem actualQuanta : original.blocks.map (fun q => (shape q).quantum) =
    [⟨1,4⟩,⟨1,16⟩,⟨1,16⟩,⟨1,16⟩,⟨1,16⟩] := by decide
theorem shapesKeepFullWidth : (original.blocks.map (fun q => q.block.frame.values.length)).sum
    = 36 := by decide
theorem changedSchema : ¬ Compatible original
    { original with manifest := { original.manifest with wire :=
      { original.manifest.wire with schema := ascii "changed" } } } := by
  intro h
  have bad := congrArg (fun xs => xs[0]?) h.1
  revert bad; decide
theorem changedProfile : ¬ Compatible original
    { original with manifest := { original.manifest with wire :=
      { original.manifest.wire with profile := ascii "changed" } } } := by
  intro h
  have bad := congrArg (fun xs => xs[1]?) h.1
  revert bad; decide
theorem changedProof : ¬ Compatible original
    { original with manifest := { original.manifest with wire :=
      { original.manifest.wire with proof := ascii "changed" } } } := by
  intro h
  have bad := congrArg (fun xs => xs[2]?) h.1
  revert bad; decide
theorem changedConfig : ¬ Compatible original
    { original with manifest := { original.manifest with wire :=
      { original.manifest.wire with config := ascii "changed" } } } := by
  intro h
  have bad := congrArg (fun xs => xs[3]?) h.1
  revert bad; decide
theorem changedScale : ¬ Compatible original
    { original with manifest := { original.manifest with wire :=
      { original.manifest.wire with scale := ascii "changed" } } } := by
  intro h
  have bad := congrArg (fun xs => xs[4]?) h.1
  revert bad; decide
theorem changedPlan : ¬ Compatible original
    { original with manifest := { original.manifest with wire :=
      { original.manifest.wire with plan := ascii "changed" } } } := by
  intro h
  have bad := congrArg (fun xs => xs[5]?) h.1
  revert bad; decide
theorem changedParent : ¬ Compatible original
    { original with manifest := { original.manifest with wire :=
      { original.manifest.wire with parent := ascii "changed" } } } := by
  intro h
  have bad := congrArg (fun xs => xs[6]?) h.1
  revert bad; decide
theorem missingBlock : ¬ Compatible original { original with blocks := original.blocks.drop 1 } := by
  intro h; have bad := congrArg (List.length) h.2.2
  revert bad; decide
theorem extraBlock : ¬ Compatible original { original with blocks := original.blocks ++ original.blocks.take 1 } := by
  intro h; have bad := congrArg (List.length) h.2.2
  revert bad; decide
theorem reorderedBlocks : ¬ Compatible original { original with blocks := original.blocks.reverse } := by
  intro h; have bad := congrArg (fun xs => xs[0]?) h.2.2
  revert bad; decide
theorem duplicatedBlock : ¬ Compatible original { original with blocks := original.blocks.take 1 ++ original.blocks.dropLast } := by
  intro h; have bad := congrArg (fun xs => xs[1]?) h.2.2
  revert bad; decide
def badQuantum := { NativeScaleVectors.bound0 with segment :=
  { NativeScaleVectors.bound0.segment with denominator := 5 } }
theorem changedQuantum : ¬ Compatible original
    { original with blocks := badQuantum :: original.blocks.tail } := by
  intro h; have bad := congrArg (fun xs => xs[0]?) h.2.2; revert bad; decide
def badOffset := { NativeScaleVectors.bound0 with block :=
  { NativeScaleVectors.bound0.block with header :=
    { NativeScaleVectors.bound0.block.header with offset := 1 } } }
theorem changedOffset : ¬ Compatible original
    { original with blocks := badOffset :: original.blocks.tail } := by
  intro h; have bad := congrArg (fun xs => xs[0]?) h.2.2; revert bad; decide
theorem changedDecodedPlan : ¬ Compatible original
    { original with plan := { original.plan with plan :=
      { original.plan.plan with target := 0 } } } := by
  intro h; have bad := congrArg (fun p => p.plan.target) h.2.1; revert bad; decide
theorem parentIsOnlyIdentity : context { original with manifest :=
    { original.manifest with wire := { original.manifest.wire with steps := ascii "9" } } }
    = context original := rfl

/-- Low-level mathematical fixture builder; does NOT authenticate changed rows. -/
def sample (a d : Nat) (q : NativeScaleBinding.Bound) : Slice :=
  let base := NativePlanCoefficientVectors.rows[0]
  let weight := { base.weight with numerator := a, denominator := d }
  let row := { base with weight := weight }
  ⟨⟨⟨row,a*(12/d)⟩,⟨original,NativeAccumulatorVectors.bound⟩⟩,q⟩
def withValues (q : NativeScaleBinding.Bound) (values : List Int) : NativeScaleBinding.Bound :=
  { q with block := { q.block with frame := { q.block.frame with values := values } } }
def numbers := { NativeAccumulatorVectors.numbers with denominator := 12 }
def slices0 : List Slice := [sample 1 3 (withValues NativeScaleVectors.bound0 [1,-2,0,4]),sample 1 2 (withValues NativeScaleVectors.bound0 [-1,2,0,-4])]
theorem vector0 : compute numbers 4 slices0 =
    some [-2,4,0,-8] := by decide
theorem count0 : slices0.length = 2 := rfl
def slices1 : List Slice := [sample 1 3 (withValues NativeScaleVectors.bound1 [-16,-15,-14,-13,-12,-11,-10,-9]),sample 1 2 (withValues NativeScaleVectors.bound1 [16,15,14,13,12,11,10,9])]
theorem vector1 : compute numbers 8 slices1 =
    some [32,30,28,26,24,22,20,18] := by decide
theorem count1 : slices1.length = 2 := rfl
def slices2 : List Slice := [sample 1 3 (withValues NativeScaleVectors.bound2 [-8,-7,-6,-5,-4,-3,-2,-1]),sample 1 2 (withValues NativeScaleVectors.bound2 [8,7,6,5,4,3,2,1])]
theorem vector2 : compute numbers 8 slices2 =
    some [16,14,12,10,8,6,4,2] := by decide
theorem count2 : slices2.length = 2 := rfl
def slices3 : List Slice := [sample 1 3 (withValues NativeScaleVectors.bound3 [0,1,2,3,4,5,6,7]),sample 1 2 (withValues NativeScaleVectors.bound3 [0,-1,-2,-3,-4,-5,-6,-7])]
theorem vector3 : compute numbers 8 slices3 =
    some [0,-2,-4,-6,-8,-10,-12,-14] := by decide
theorem count3 : slices3.length = 2 := rfl
def slices4 : List Slice := [sample 1 3 (withValues NativeScaleVectors.bound4 [8,9,10,11,12,13,14,15]),sample 1 2 (withValues NativeScaleVectors.bound4 [-8,-9,-10,-11,-12,-13,-14,-15])]
theorem vector4 : compute numbers 8 slices4 =
    some [-16,-18,-20,-22,-24,-26,-28,-30] := by decide
theorem count4 : slices4.length = 2 := rfl
def slices5 : List Slice := [sample 0 1 (withValues NativeScaleVectors.bound0 [1,-2,0,4])]
theorem vector5 : compute numbers 4 slices5 =
    some [0,0,0,0] := by decide
theorem count5 : slices5.length = 1 := rfl
def slices6 : List Slice := [sample 0 1 (withValues NativeScaleVectors.bound1 [-16,-15,-14,-13,-12,-11,-10,-9])]
theorem vector6 : compute numbers 8 slices6 =
    some [0,0,0,0,0,0,0,0] := by decide
theorem count6 : slices6.length = 1 := rfl
def slices7 : List Slice := [sample 0 1 (withValues NativeScaleVectors.bound2 [-8,-7,-6,-5,-4,-3,-2,-1])]
theorem vector7 : compute numbers 8 slices7 =
    some [0,0,0,0,0,0,0,0] := by decide
theorem count7 : slices7.length = 1 := rfl
def slices8 : List Slice := [sample 0 1 (withValues NativeScaleVectors.bound3 [0,1,2,3,4,5,6,7])]
theorem vector8 : compute numbers 8 slices8 =
    some [0,0,0,0,0,0,0,0] := by decide
theorem count8 : slices8.length = 1 := rfl
def slices9 : List Slice := [sample 0 1 (withValues NativeScaleVectors.bound4 [8,9,10,11,12,13,14,15])]
theorem vector9 : compute numbers 8 slices9 =
    some [0,0,0,0,0,0,0,0] := by decide
theorem count9 : slices9.length = 1 := rfl
theorem actualPayloadWithSyntheticWeight : compute numbers 4
    [sample 1 3 NativeScaleVectors.bound0] = some [4,-8,0,16] := by decide
theorem zeroWeightRetained : (slices5.map kernelRow).length = 1 ∧
    (slices5.map kernelRow)[0]?.map (·.numerator) = some 0 := by decide
theorem missingCoordinate : compute numbers 4
    [sample 1 3 (withValues NativeScaleVectors.bound0 [1,2,3])] = none := by decide
theorem extraCoordinate : compute numbers 4
    [sample 1 3 (withValues NativeScaleVectors.bound0 [1,2,3,4,5])] = none := by decide
theorem emptyMembers : compute numbers 4 [] = none := by decide
theorem wrongDenominator : compute { numbers with denominator := 5 } 4 slices0 = none := by decide
theorem substitutedMinimumLCM : compute { numbers with denominator := 6 } 4 slices0 =
    some [-1,2,0,-4] := by decide
theorem signedFractionLimit : compute numbers 4
    [sample (2^63) 1 NativeScaleVectors.bound0] = none := by decide
theorem unsafePrefixCancellation : compute numbers 1
    [sample 1 1 (withValues NativeScaleVectors.bound0 [9223372036854775807]),
     sample 1 1 (withValues NativeScaleVectors.bound0 [-9223372036854775807])] = none := by decide
theorem emptySlice {index} : sliceRows index [] = some [] := rfl
end DeltaReduce.NativeVectorArithmeticVectors
