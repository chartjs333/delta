import ShardFamily
import DeltaReduce.NativeIscCertificate

/-! R2 source/body transfer, not public admission or recovery refinement.
Native INT64/INT128 checks are reused at their ACTUAL bounds. No limit127
recheck, width-one restriction, synthetic body or coordinate identity is added.
-/
namespace DeltaReduce.NativeFamily
open NativeBinding

def single (width : Nat) (positive : 0 < width) : ShardFamily.Layout :=
  ⟨1,fun _ => width,fun _ => positive⟩

section Parameter
variable {codec store trust anchor} {binding : Binding codec trust anchor store} {domain shard}
variable (native : DerivedParameter binding domain shard)

def parameterLayout : ShardFamily.Layout := single native.partition.length
  (ParameterKernel.checkedParameterSound _ _ _ _ _ _ _ _ native.computed).1

def parameterSlot : Fin (parameterLayout native).count := ⟨0,by change 0 < 1; decide⟩

def parameterWhole (control : Control) : ShardFamily.Whole (parameterLayout native)
    (DerivedParameter binding domain shard × Control) Int :=
  ⟨(native,control),fun _ => native.numerators,fun _ =>
    (ParameterKernel.checkedParameterSound _ _ _ _ _ _ _ _ native.computed).2.2.1⟩

def parameterFamily (control : Control) := ShardFamily.project (parameterWhole native control)

theorem parameterRoundtrip (control : Control) :
    ShardFamily.reconstruct (parameterFamily native control) = parameterWhole native control :=
  ShardFamily.reconstruct_project _

/-- Every scalar result is recomputed by the original kernel from the original
ordered rows. There is no premise giving a translated body or expected result. -/
theorem parameterCoordinate (control : Control) (a : ShardFamily.Selector (parameterLayout native)) :
    ParameterKernel.checkedParameter (accumulatorLo binding.profile) (accumulatorHi binding.profile)
      minInput maxInput native.assignment.denominator 1
      (native.rows.map (VectorShardRepresentation.rowAt (a (parameterSlot native)).val)) =
        some [(parameterFamily native control).view a (parameterSlot native)] := by
  obtain ⟨value,atValue,computed⟩ := VectorShardRepresentation.scalarParameterIsCoordinate
    native.computed (a (parameterSlot native)).val (a (parameterSlot native)).isLt
  have bound : (a (parameterSlot native)).val < native.numerators.length := by
    rw [(ParameterKernel.checkedParameterSound _ _ _ _ _ _ _ _ native.computed).2.2.1]
    exact (a (parameterSlot native)).isLt
  have equal : value = native.numerators[(a (parameterSlot native)).val] := by
    simpa only [List.getElem?_eq_getElem bound,Option.some.injEq] using atValue.symm
  simpa only [parameterFamily,parameterWhole,ShardFamily.project,equal] using computed

theorem parameterOriginalRows (k : Fin native.partition.length) (i : Nat)
    (row : ParameterKernel.Row) (atRow : native.rows[i]? = some row) :
    ∃ contribution, native.assignment.contributions[i]? = some contribution ∧
      ∃ loaded : LoadedRow codec store binding.authority.schema native.frame native.assignment
        native.partition.length contribution,
        row = loaded.row ∧ ∃ value, loaded.q.values[k.val]? = some value := by
  obtain ⟨contribution,atContribution,loaded,equal⟩ := rowsBoundAt native.boundRows i row atRow
  refine ⟨contribution,atContribution,loaded,equal,?_⟩
  have bound : k.val < loaded.q.values.length := by rw [loaded.shape]; exact k.isLt
  exact ⟨loaded.q.values[k.val],List.getElem?_eq_getElem bound⟩

def reconstructedBody (control : Control) : ParameterBody :=
  {native.body with numerators := (ShardFamily.reconstruct (parameterFamily native control)).values (parameterSlot native)}

theorem completeBodyRecovered (control : Control) : reconstructedBody native control = native.body := by
  simp only [reconstructedBody,parameterRoundtrip,parameterWhole,DerivedParameter.body]

theorem originalBodyBytes (control : Control) :
    encodeParameterBody (reconstructedBody native control) = encodeParameterBody native.body := by
  rw [completeBodyRecovered]

theorem oldScalarResult (control : Control) (old : NativeScalarProjection.Parameter native) :
    (ShardFamily.reconstruct (parameterFamily native control)).values (parameterSlot native) = [old.value] := by
  rw [parameterRoundtrip]; exact old.exactNumerator

end Parameter

section Prepared
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
variable {voteTrust mode state request domain shard} {metadata : VoteMetadata}

def parameterFromVote (vote : ExpectedNativeVote binding {metadata with kind := .parameter domain shard}) :
    DerivedParameter binding domain shard := match vote.source with
  | .parameter native => native

theorem parameterFromVoteEncoded (vote : ExpectedNativeVote binding {metadata with kind := .parameter domain shard}) :
    encodeParameterBody (parameterFromVote vote).body = some vote.body := by
  have h := vote.bodyEncoded
  cases hs : vote.source with
  | parameter native => simpa [parameterFromVote,hs,VoteSource.bodyBytes] using h

variable (prepared : NativePrepared binding voteTrust {metadata with kind := .parameter domain shard}
    mode state request)

/-- Derives the vector from the actual original vote source. The caller cannot
attach an unrelated vector, or supply a whole-body translation as a premise. -/
def preparedFamily := parameterFamily (parameterFromVote prepared.expected) prepared

theorem preparedRecordIdentity (a : ShardFamily.Selector (parameterLayout (parameterFromVote prepared.expected))) :
    ((ShardFamily.scalarView (preparedFamily prepared) a).1.2).record = prepared.record ∧
    ((ShardFamily.scalarView (preparedFamily prepared) a).1.2).record.sequence = state.votes.length + 1 ∧
    ((ShardFamily.scalarView (preparedFamily prepared) a).1.2).expected.envelope = prepared.expected.envelope :=
  ⟨rfl,rfl,rfl⟩

theorem preparedWholeBodyRecovered :
    encodeParameterBody (reconstructedBody (parameterFromVote prepared.expected) prepared) =
      some prepared.expected.body := by
  rw [completeBodyRecovered]
  exact parameterFromVoteEncoded prepared.expected

theorem preparedOriginalCommand :
    request = encodeNativeCommand (.parameter domain shard) prepared.expected.body :=
  prepared.requestMatches

end Prepared

section Apply
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
variable (native : NativeApply binding)

/-- Model and optimizer belong to one vector state and use the same global
coordinate, before being restricted to each original shard's offset. -/
structure ApplyCell where
  model : Int
  optimizer : Int
  gradient : Int
  nextModel : Int
  nextOptimizer : Int
  deriving DecidableEq, Repr

def applyCell (k : Fin binding.model.values.length) : ApplyCell :=
  let shapes := ApplyKernel.applyComputationShapeAndBounds native.core.computation
  ⟨binding.model.values[k.val],
    binding.optimizer.values[k.val]'(by rw [native.core.computation.optimizerShape]; exact k.isLt),
    native.core.computation.gradients[k.val]'(by rw [shapes.1]; exact k.isLt),
    native.core.computation.nextModel[k.val]'(by rw [shapes.2.1]; exact k.isLt),
    native.core.computation.nextOptimizer[k.val]'(by rw [shapes.2.2.1]; exact k.isLt)⟩

def applyLayout : ShardFamily.Layout := single binding.model.values.length
  (by
    have h := native.core.computation.nonempty
    cases hv : binding.model.values with
    | nil => exact False.elim (h hv)
    | cons _ _ => simp)

def applySlot : Fin (applyLayout native).count := ⟨0,by change 0 < 1; decide⟩

def applyWhole (control : Control) : ShardFamily.Whole (applyLayout native)
    (NativeApply binding × Control) ApplyCell :=
  ⟨(native,control),fun _ => List.ofFn (applyCell native),fun _ => List.length_ofFn⟩

def applyFamily (control : Control) := ShardFamily.project (applyWhole native control)

theorem applyModelReconstructed (control : Control) :
    (((ShardFamily.reconstruct (applyFamily native control)).values (applySlot native)).map ApplyCell.nextModel) = native.body.nextModel ∧
    (((ShardFamily.reconstruct (applyFamily native control)).values (applySlot native)).map ApplyCell.nextOptimizer) = native.body.nextOptimizer := by
  have shape := nativeApplyOutputBounds native
  simp only [applyFamily,ShardFamily.reconstruct_project,applyWhole]
  constructor <;> simp only [List.map_ofFn,Function.comp_def,applyCell]
    <;> apply List.ext_getElem? <;> intro k <;> by_cases hk : k < binding.model.values.length
  · simp [hk,NativeApply.body,NativeApplyCore.body]
  · simp [hk,show native.body.nextModel.length ≤ k by rw [shape.1]; omega]
  · simp [hk,NativeApply.body,NativeApplyCore.body]
  · simp [hk,show native.body.nextOptimizer.length ≤ k by rw [shape.2.1]; omega]

theorem applyOriginalHashPreimages (control : Control) :
    codec.valueHash .model (((ShardFamily.reconstruct (applyFamily native control)).values (applySlot native)).map ApplyCell.nextModel) =
      native.body.nextModelHash ∧
    codec.valueHash .optimizer (((ShardFamily.reconstruct (applyFamily native control)).values (applySlot native)).map ApplyCell.nextOptimizer) =
      native.body.nextOptimizerHash := by
  rw [(applyModelReconstructed native control).1,(applyModelReconstructed native control).2]
  exact ⟨rfl,rfl⟩

theorem applyArithmeticCoordinate (k : Fin binding.model.values.length) :
    ∃ total terms,
      ApplyKernel.ColumnTerms k.val native.core.rows terms ∧
      ApplyKernel.checkedMix minInput maxInput (Int.ofNat native.core.computation.plan.denominator) 0 terms = some total ∧
      round total (Int.ofNat native.core.computation.plan.denominator) = (applyCell native k).gradient ∧
      ApplyKernel.checkedOptimizer minInput maxInput (applyCell native k).model (applyCell native k).optimizer
        (applyCell native k).gradient binding.profile.learningRate.kernelWeight
        binding.profile.momentum.kernelWeight binding.profile.weightDecay.kernelWeight =
          some ((applyCell native k).nextModel,(applyCell native k).nextOptimizer) := by
  obtain ⟨theta,m,g,n,o,total,terms,ht,hm,hg,hn,ho,column,mix,rounded,optimized⟩ :=
    VectorShardRepresentation.applyCoordinateFromSameVector native.core.computation k.val k.isLt
  have shapes := ApplyKernel.applyComputationShapeAndBounds native.core.computation
  simp only [List.getElem?_eq_getElem k.isLt,Option.some.injEq] at ht
  have bm : k.val < binding.optimizer.values.length := by rw [native.core.computation.optimizerShape]; exact k.isLt
  have bg : k.val < native.core.computation.gradients.length := by rw [shapes.1]; exact k.isLt
  have bn : k.val < native.core.computation.nextModel.length := by rw [shapes.2.1]; exact k.isLt
  have bo : k.val < native.core.computation.nextOptimizer.length := by rw [shapes.2.2.1]; exact k.isLt
  simp only [List.getElem?_eq_getElem bm,Option.some.injEq] at hm
  simp only [List.getElem?_eq_getElem bg,Option.some.injEq] at hg
  simp only [List.getElem?_eq_getElem bn,Option.some.injEq] at hn
  simp only [List.getElem?_eq_getElem bo,Option.some.injEq] at ho
  refine ⟨total,terms,column,mix,?_,?_⟩
  · simpa only [applyCell,← hg] using rounded
  · simpa only [applyCell,ht,hm,hg,hn,ho] using optimized

end Apply

/- Original certificate/record checks are properties of the shared carrier.
These specialize to real existing definitions; no coordinate changes a signer,
threshold, command, receipt, sequence, or QC body. No authentication is inferred. -/
theorem certificateSignersUnchanged (whole : ShardFamily.Whole l Common Cell)
    (certificate : Common → NativeIscCertificate.Certificate) (committee) (a : ShardFamily.Selector l) :
    NativeIscCertificate.SignersValid committee (certificate (ShardFamily.scalarView (ShardFamily.project whole) a).1) ↔
      NativeIscCertificate.SignersValid committee (certificate whole.common) := Iff.rfl

theorem originalRecordUnchanged (whole : ShardFamily.Whole l Common Cell)
    (record : Common → RecoveryKernel.Record) (a : ShardFamily.Selector l) :
    record (ShardFamily.scalarView (ShardFamily.project whole) a).1 = record whole.common := rfl

end DeltaReduce.NativeFamily
