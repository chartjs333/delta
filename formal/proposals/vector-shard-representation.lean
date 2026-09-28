import DeltaReduce.PublicApplyArithmetic
import DeltaReduce.NativeVectorArithmeticVectors

/-! Minimal R2 representation proposal only. No new vote, certificate, admission
rule or public transition is defined here. Identity is the ORIGINAL object,
parametric in its type: it can contain the complete shard/vote/certificate bytes.
It is copied, never translated, hashed again, split, or authenticated here.
-/
namespace DeltaReduce.VectorShardRepresentation
open NativeBinding

structure Source (Identity : Type) where
  identity : Identity
  entry : NativeShardPartition.Entry
  values : List Int
  shape : values.length = entry.count

def load (identity : Identity) (entry : NativeShardPartition.Entry) (values : List Int) :
    Option (Source Identity) :=
  if shape : values.length = entry.count then some ⟨identity,entry,values,shape⟩ else none

structure Image (Identity : Type) where
  identity : Identity
  entry : NativeShardPartition.Entry
  coordinate : Fin entry.count → Int

def Represents (source : Source Identity) (image : Image Identity) : Prop :=
  image.identity = source.identity ∧ image.entry = source.entry ∧
    List.ofFn image.coordinate = source.values

def represent (source : Source Identity) : Image Identity :=
  ⟨source.identity,source.entry,fun k => source.values[k.val]'(by rw [source.shape]; exact k.isLt)⟩

theorem represents (source : Source Identity) : Represents source (represent source) := by
  refine ⟨rfl,rfl,?_⟩
  apply List.ext_getElem?
  intro i
  by_cases h : i < source.entry.count
  · simp [represent,h,source.shape]
  · simp [represent,show source.values.length ≤ i by rw [source.shape]; omega,h]

def project (image : Image Identity) (k : Nat) : Option Int :=
  if within : k < image.entry.count then some (image.coordinate ⟨k,within⟩) else none

theorem projectExact (source : Source Identity) (k : Nat) :
    project (represent source) k = source.values[k]? := by
  by_cases h : k < source.entry.count
  · simp [project,represent,h,source.shape]
  · simp [project,represent,h,show source.values.length ≤ k by rw [source.shape]; omega]

theorem noCoordinateDefault (image : Image Identity) (k : Nat)
    (outside : image.entry.count ≤ k) : project image k = none := by
  simp [project,show ¬ k < image.entry.count by omega]

theorem identityPreserved (source : Source Identity) :
    (represent source).identity = source.identity ∧ (represent source).entry = source.entry := ⟨rfl,rfl⟩

theorem identityObservablesPreserved (source : Source Identity)
    (shardIdentity voteIdentity certificateIdentity : Identity → Bytes) :
    shardIdentity (represent source).identity = shardIdentity source.identity ∧
    voteIdentity (represent source).identity = voteIdentity source.identity ∧
    certificateIdentity (represent source).identity = certificateIdentity source.identity := ⟨rfl,rfl,rfl⟩

theorem coordinatesPreserved (source : Source Identity) (k : Fin source.entry.count) :
    (represent source).entry.name = source.entry.name ∧
    (represent source).entry.start + k = source.entry.start + k ∧
    (represent source).entry.offset + k = source.entry.offset + k := ⟨rfl,rfl,rfl⟩

theorem noCollapse (left right : Source Identity) (same : represent left = represent right) :
    left.identity = right.identity ∧ left.entry = right.entry ∧ left.values = right.values := by
  exact ⟨congrArg Image.identity same,congrArg Image.entry same,
    (represents left).2.2.symm.trans ((congrArg (fun p => List.ofFn p.coordinate) same).trans (represents right).2.2)⟩

theorem collectionKeepsOriginalObjects (sources : List (Source Identity)) :
    (sources.map represent).length = sources.length ∧
    (sources.map represent).map Image.identity = sources.map Source.identity ∧
    (sources.map represent).map Image.entry = sources.map Source.entry := by
  simp [represent,List.map_map,Function.comp_def]

/-- A view of a shard in a full model/optimizer vector keeps its original offset.
It does not create another APPLY vote or another current-state identity. -/
def sliceSource (identity : Identity) (entry : NativeShardPartition.Entry) (values : List Int)
    (fits : entry.start + entry.count ≤ values.length) : Source Identity :=
  ⟨identity,entry,(values.drop entry.start).take entry.count,by
    simp only [List.length_take,List.length_drop]; omega⟩

theorem globalCoordinateExact (identity : Identity) (entry : NativeShardPartition.Entry)
    (values : List Int) (fits : entry.start + entry.count ≤ values.length)
    (k : Nat) (within : k < entry.count) :
    project (represent (sliceSource identity entry values fits)) k = values[entry.start+k]? := by
  rw [projectExact]
  simp [sliceSource,List.getElem?_drop,within]

/- Existing scalar kernels operate on a coordinate VIEW, not a new shard. -/
def rowAt (k : Nat) (row : ParameterKernel.Row) : ParameterKernel.Row :=
  {row with values := [row.values[k]?.getD 0]}

theorem parameterRowsAt {lo hi inputLo inputHi denominator coefficientSum acc rows}
    (safe : ParameterKernel.PrefixesSafe lo hi inputLo inputHi denominator coefficientSum acc rows)
    (k : Nat) (a : Int) (atIndex : acc[k]? = some a) :
    ParameterKernel.PrefixesSafe lo hi inputLo inputHi denominator coefficientSum [a] (rows.map (rowAt k)) := by
  induction rows generalizing coefficientSum acc a with
  | nil => exact ⟨safe.1,by simpa using safe.2 a (List.mem_of_getElem? atIndex)⟩
  | cons row rows ih =>
    obtain ⟨valid,sumFit,nextSumFit,step,tail⟩ := safe
    obtain ⟨q,hq,af,qf,pf,sf⟩ := ParameterKernel.stepSafeAt _ _ _ _ _ _ _ step k a atIndex
    have next : (ParameterKernel.exactAddVector
        (row.numerator * (denominator / row.denominator)) acc row.values)[k]? =
        some (a + row.numerator * (denominator / row.denominator) * q) := by
      simp [ParameterKernel.exactAddVector,List.getElem?_zipWith,atIndex,hq]
    simpa only [List.map_cons,rowAt,hq,Option.getD_some,ParameterKernel.PrefixesSafe,
      ParameterKernel.exactAddVector,List.zipWith_cons_cons,List.zipWith_nil_left] using
      And.intro valid (And.intro sumFit (And.intro nextSumFit
        (And.intro (show ParameterKernel.StepSafe lo hi inputLo inputHi
          (row.numerator * (denominator / row.denominator)) [a] [q] from ⟨af,qf,pf,sf,True.intro⟩)
          (ih tail _ next))))

theorem scalarParameterIsCoordinate {lo hi inputLo inputHi denominator width rows result}
    (accepted : ParameterKernel.checkedParameter lo hi inputLo inputHi denominator width rows = some result)
    (k : Nat) (within : k < width) :
    ∃ value, result[k]? = some value ∧
      ParameterKernel.checkedParameter lo hi inputLo inputHi denominator 1 (rows.map (rowAt k)) = some [value] := by
  have sound := ParameterKernel.checkedParameterSound _ _ _ _ _ _ _ _ accepted
  have safe := parameterRowsAt sound.2.2.2.2.2 k 0 (List.getElem?_replicate_of_lt within)
  have nonempty : rows.map (rowAt k) ≠ [] := by simpa using sound.2.1
  have computed := ParameterKernel.checkedParameterRowsComplete _ _ _ _ _ _ _ _ safe
  have scalar : ParameterKernel.checkedParameter lo hi inputLo inputHi denominator 1 (rows.map (rowAt k)) =
      some (ParameterKernel.exactParameterRows denominator [0] (rows.map (rowAt k))) := by
    simpa [ParameterKernel.checkedParameter,nonempty] using computed
  have scalarSound := ParameterKernel.checkedParameterSound _ _ _ _ _ _ _ _ scalar
  obtain ⟨value,hv,fold⟩ := ParameterKernel.checkedParameterCoordinateRefines _ _ _ _ _ _ _ _ accepted k within
  obtain ⟨other,ho,ofold⟩ := ParameterKernel.checkedParameterCoordinateRefines _ _ _ _ _ _ _ _ scalar 0 (by decide)
  have terms : ParameterKernel.coordinateTerms denominator 0 (rows.map (rowAt k)) =
      ParameterKernel.coordinateTerms denominator k rows := by
    simp [ParameterKernel.coordinateTerms,rowAt,List.map_map,Function.comp_def]
  rw [terms,fold] at ofold
  have equal : value = other := Option.some.inj ofold
  have single : ParameterKernel.exactParameterRows denominator [0] (rows.map (rowAt k)) = [value] := by
    have len := scalarSound.2.2.1
    cases hs : ParameterKernel.exactParameterRows denominator [0] (rows.map (rowAt k)) with
    | nil => simp [hs] at len
    | cons head tail =>
      have ht : tail = [] := by simpa [hs] using len
      subst tail
      simpa [hs,← equal] using ho
  exact ⟨value,hv,by simpa [single] using scalar⟩

theorem representedParameterCoordinate {lo hi inputLo inputHi denominator rows}
    (source : Source Identity)
    (accepted : ParameterKernel.checkedParameter lo hi inputLo inputHi denominator source.entry.count rows = some source.values)
    (k : Nat) (within : k < source.entry.count) :
    ∃ value, project (represent source) k = some value ∧
      ParameterKernel.checkedParameter lo hi inputLo inputHi denominator 1 (rows.map (rowAt k)) = some [value] := by
  obtain ⟨value,hv,hs⟩ := scalarParameterIsCoordinate accepted k within
  exact ⟨value,by rw [projectExact]; exact hv,hs⟩

theorem parameterCoordinateNeverPads {lo hi inputLo inputHi denominator width rows result}
    (accepted : ParameterKernel.checkedParameter lo hi inputLo inputHi denominator width rows = some result)
    (k : Nat) (within : k < width) (row : ParameterKernel.Row) (member : row ∈ rows) :
    ∃ q, row.values[k]? = some q := by
  have shape := (ParameterKernel.checkedParameterSound _ _ _ _ _ _ _ _ accepted).2.2.2.2.1 row member
  exact ⟨row.values[k]'(by omega),List.getElem?_eq_getElem (by omega)⟩

theorem scalarConversionIsCoordinate {lo hi denominator u v x y ns results}
    (accepted : ParameterKernel.checkedConvertRows lo hi denominator u v x y ns = some results)
    (k : Nat) (n : Int) (found : ns[k]? = some n) :
    ∃ result, results[k]? = some result ∧
      checkedConvert lo hi lo hi n denominator u v x y = some result := by
  induction ns generalizing results k with
  | nil => simp at found
  | cons head tail ih =>
    simp only [ParameterKernel.checkedConvertRows] at accepted
    split at accepted
    · cases scalar : checkedConvert lo hi lo hi head denominator u v x y with
      | none => simp [scalar] at accepted
      | some result =>
        cases rest : ParameterKernel.checkedConvertRows lo hi denominator u v x y tail with
        | none => simp [scalar,rest] at accepted
        | some values =>
          simp only [scalar,rest,Option.some.injEq] at accepted
          subst results
          cases k with
          | zero => cases Option.some.inj found; exact ⟨result,rfl,scalar⟩
          | succ k => exact ih rest k found
    · contradiction

theorem scalarMixtureIsCoordinate {lo hi rows plan coordinates values}
    (trace : ApplyKernel.GradientTrace lo hi rows plan coordinates values)
    (position coordinate : Nat) (found : coordinates[position]? = some coordinate) :
    ∃ (value total : Int) (terms : List ApplyKernel.MixTerm),
      values[position]? = some value ∧
      ApplyKernel.ColumnTerms coordinate rows terms ∧
      ApplyKernel.checkedMix lo hi (Int.ofNat plan.denominator) 0 terms = some total ∧
      round total (Int.ofNat plan.denominator) = value ∧ Fits lo hi value := by
  induction trace generalizing position with
  | nil => simp at found
  | cons head tail ih =>
    cases position with
    | zero => cases Option.some.inj found; exact ⟨head.value,head.total,head.terms,rfl,head.column,head.computed,rfl,head.output⟩
    | succ position => exact ih position found

theorem scalarOptimizerIsCoordinate {lo hi lr mu wd model momentum gradient nextModel nextOptimizer}
    (trace : ApplyKernel.OptimizerTrace lo hi lr mu wd model momentum gradient nextModel nextOptimizer)
    (k : Nat) (theta : Int) (found : model[k]? = some theta) :
    ∃ m g nextM nextO,
      momentum[k]? = some m ∧ gradient[k]? = some g ∧
      nextModel[k]? = some nextM ∧ nextOptimizer[k]? = some nextO ∧
      ApplyKernel.checkedOptimizer lo hi theta m g lr mu wd = some (nextM,nextO) := by
  induction trace generalizing k with
  | nil => simp at found
  | cons safe tail ih =>
    cases k with
    | zero =>
      cases Option.some.inj found
      exact ⟨_,_,_,_,rfl,rfl,rfl,rfl,by simp [ApplyKernel.checkedOptimizer,safe]⟩
    | succ k => exact ih k found

theorem applyCoordinateFromSameVector {lo hi model optimizer rows lr mu wd}
    (computation : ApplyKernel.ApplyComputation lo hi model optimizer rows lr mu wd)
    (k : Nat) (within : k < model.length) :
    ∃ theta m g nextM nextO total terms,
      model[k]? = some theta ∧ optimizer[k]? = some m ∧ computation.gradients[k]? = some g ∧
      computation.nextModel[k]? = some nextM ∧ computation.nextOptimizer[k]? = some nextO ∧
      ApplyKernel.ColumnTerms k rows terms ∧
      ApplyKernel.checkedMix lo hi (Int.ofNat computation.plan.denominator) 0 terms = some total ∧
      round total (Int.ofNat computation.plan.denominator) = g ∧
      ApplyKernel.checkedOptimizer lo hi theta m g lr mu wd = some (nextM,nextO) := by
  have atModel := List.getElem?_eq_getElem within
  obtain ⟨m,g,nextM,nextO,hm,hg,hn,ho,calculated⟩ :=
    scalarOptimizerIsCoordinate computation.optimizerTrace k model[k] atModel
  obtain ⟨value,total,terms,hv,column,mix,rounded,_⟩ :=
    scalarMixtureIsCoordinate computation.gradientTrace k k (by simp [within])
  have same : value = g := Option.some.inj (hv.symm.trans hg)
  exact ⟨model[k],m,g,nextM,nextO,total,terms,atModel,hm,hg,hn,ho,column,mix,rounded.trans same,calculated⟩

/-- The numeric image is constructed from the existing reducer's own output.
No translated vector or scalar expected-result equality is supplied. -/
def originalResultSource {b domain index out}
    (computed : NativeVectorArithmetic.reduce b domain index = some out) : Source NativeVectorArithmetic.Result :=
  ⟨out,(NativeVectorContext.shape out.first).entry,out.values,(NativeVectorArithmetic.exactOutput computed).2⟩

theorem originalResultCoordinate {b domain index out}
    (computed : NativeVectorArithmetic.reduce b domain index = some out)
    (k : Nat) (within : k < (NativeVectorContext.shape out.first).entry.count) :
    ∃ value, project (represent (originalResultSource computed)) k = some value ∧
      ParameterKernel.checkedParameter (NativeVectorArithmetic.lo b.source.plan.accumulator.numbers)
        (NativeVectorArithmetic.hi b.source.plan.accumulator.numbers) minInput maxInput
        b.source.plan.accumulator.numbers.denominator 1
        ((out.slices.map NativeVectorArithmetic.kernelRow).map (rowAt k)) = some [value] := by
  exact representedParameterCoordinate (originalResultSource computed)
    (NativeVectorArithmetic.reduced computed).2.2.2.2 k within

theorem originalScalarResultUnchanged {codec store trust anchor}
    {binding : Binding codec trust anchor store} {domain shard}
    {native : DerivedParameter binding domain shard} (old : NativeScalarProjection.Parameter native)
    (source : Source Identity) (values : source.values = native.numerators) :
    project (represent source) 0 = some old.value := by
  rw [projectExact,values,old.exactNumerator]
  rfl

/- The already checked original manifest is used unchanged. No vote/certificate
is fabricated for it: the identity-preservation theorem above is universal over
the original identity type, including full original envelopes when available. -/
def original := NativeVectorArithmeticVectors.original
theorem originalShapes : ∀ block ∈ original.blocks,
    block.block.frame.values.length = (NativeVectorContext.shape block).entry.count := by decide

def originalSources : List (Source NativeScaleBinding.Bound) :=
  original.blocks.attach.map (fun block => ⟨block.val,(NativeVectorContext.shape block.val).entry,
    block.val.block.frame.values,originalShapes block.val block.property⟩)

theorem originalWidths : (originalSources.map represent).map (fun image => image.entry.count) = [4,8,8,8,8] := by
  simpa [originalSources,represent,List.map_map,Function.comp_def,original] using NativeVectorArithmeticVectors.actualWidths

theorem originalObjectsRetained : (originalSources.map represent).map Image.identity = original.blocks := by
  simp [originalSources,represent,List.map_map,Function.comp_def]

theorem originalManifestEntries : (originalSources.map represent).map Image.entry = original.plan.plan.entries := by
  simpa [originalSources,represent,List.map_map,Function.comp_def,original] using NativeVectorArithmeticVectors.originalSlots

theorem originalStarts : (originalSources.map represent).map (fun image => image.entry.start) = [0,4,12,20,28] := by
  simpa [originalSources,represent,List.map_map,Function.comp_def,original] using NativeVectorArithmeticVectors.actualLocations

theorem originalCoordinateCount : ((originalSources.map represent).map (fun image => image.entry.count)).sum = 36 := by
  rw [originalWidths]
  decide

theorem originalFiveNotThirtySix : (originalSources.map represent).length = 5 := by
  have widths := congrArg List.length originalWidths
  simpa using widths

theorem originalValuesRetained :
    (originalSources.map represent).map (fun image => List.ofFn image.coordinate) =
      original.blocks.map (fun block => block.block.frame.values) := by
  have h : ∀ source : Source NativeScaleBinding.Bound,
      List.ofFn (represent source).coordinate = source.values := fun source => (represents source).2.2
  simp only [List.map_map,Function.comp_def]
  simp_rw [h]
  simp [originalSources,List.map_map,Function.comp_def]

#print axioms Source
#print axioms load
#print axioms Image
#print axioms Represents
#print axioms represent
#print axioms represents
#print axioms project
#print axioms projectExact
#print axioms noCoordinateDefault
#print axioms identityPreserved
#print axioms identityObservablesPreserved
#print axioms coordinatesPreserved
#print axioms noCollapse
#print axioms collectionKeepsOriginalObjects
#print axioms sliceSource
#print axioms globalCoordinateExact
#print axioms rowAt
#print axioms parameterRowsAt
#print axioms scalarParameterIsCoordinate
#print axioms representedParameterCoordinate
#print axioms parameterCoordinateNeverPads
#print axioms scalarConversionIsCoordinate
#print axioms scalarMixtureIsCoordinate
#print axioms scalarOptimizerIsCoordinate
#print axioms applyCoordinateFromSameVector
#print axioms originalResultSource
#print axioms originalResultCoordinate
#print axioms originalScalarResultUnchanged
#print axioms original
#print axioms originalShapes
#print axioms originalSources
#print axioms originalWidths
#print axioms originalObjectsRetained
#print axioms originalManifestEntries
#print axioms originalStarts
#print axioms originalCoordinateCount
#print axioms originalFiveNotThirtySix
#print axioms originalValuesRetained

end DeltaReduce.VectorShardRepresentation
