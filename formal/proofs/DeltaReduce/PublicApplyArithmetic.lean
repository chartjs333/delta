import DeltaReduce.PublicParameterBody

/-! Rechecked model-width conversion and APPLY from actual native computations.
This is a projection restriction, not a new native admission rule. -/
namespace DeltaReduce.PublicApplyArithmetic
open NativeBinding NativeInputProjection PublicParameterBody ApplyKernel

theorem optimizerWidthsAgree {lo hi otherLo otherHi lr mu wd model optimizer gradients
    leftModel leftOptimizer rightModel rightOptimizer}
    (left : OptimizerTrace lo hi lr mu wd model optimizer gradients leftModel leftOptimizer)
    (right : OptimizerTrace otherLo otherHi lr mu wd model optimizer gradients rightModel rightOptimizer) :
    leftModel = rightModel ∧ leftOptimizer = rightOptimizer := by
  induction left generalizing rightModel rightOptimizer with
  | nil => cases right; exact ⟨rfl,rfl⟩
  | cons safe tail ih =>
      cases right with
      | cons otherSafe otherTail =>
          obtain ⟨m,o⟩ := ih otherTail
          exact ⟨congrArg (_ :: ·) m,congrArg (_ :: ·) o⟩

theorem applyWidthsAgree {lo hi otherLo otherHi model optimizer rows lr mu wd}
    (left : ApplyComputation lo hi model optimizer rows lr mu wd)
    (right : ApplyComputation otherLo otherHi model optimizer rows lr mu wd) :
    left.plan.denominator = right.plan.denominator ∧ left.gradients = right.gradients ∧
    left.nextModel = right.nextModel ∧ left.nextOptimizer = right.nextOptimizer := by
  have ld := (checkedLcmSound lo hi 1 _ _ left.plan.computed).1
  have rd := (checkedLcmSound otherLo otherHi 1 _ _ right.plan.computed).1
  have denominator := ld.trans rd.symm
  have lg := (gradientTraceExact left.gradientTrace).1
  have rg := (gradientTraceExact right.gradientTrace).1
  have gradients : left.gradients = right.gradients := by rw [lg,rg,denominator]
  have trace := right.optimizerTrace
  rw [← gradients] at trace
  exact ⟨denominator,gradients,optimizerWidthsAgree left.optimizerTrace trace⟩

section Conversion
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    (entry : ConvertedParameter binding) (limit : ModelLimit)

def conversion := ParameterKernel.checkedDomainVector (modelLo limit) limit.value minInput maxInput
    entry.source.result.assignment.denominator entry.source.result.assignment.quantum.numerator
    entry.source.result.assignment.quantum.denominator binding.profile.applyQuantum.numerator
    binding.profile.applyQuantum.denominator entry.source.result.numerators

theorem conversionWidthsAgree {values} (accepted : conversion entry limit = some values) :
    values = entry.values := by
  have narrow := ParameterKernel.checkedDomainVectorSound (modelLo limit) limit.value minInput maxInput
    entry.source.result.assignment.denominator entry.source.result.assignment.quantum.numerator
    entry.source.result.assignment.quantum.denominator binding.profile.applyQuantum.numerator
    binding.profile.applyQuantum.denominator entry.source.result.numerators values accepted
  exact narrow.2.2.2.trans (convertedParameterSound entry).2.2.symm

structure Converted : Type where
  computed : conversion entry limit = some entry.values

def checkConversion : Option (Converted entry limit) :=
  match computed : conversion entry limit with
  | none => none
  | some values => some ⟨by simpa only [conversionWidthsAgree entry limit computed] using computed⟩

theorem conversionChecksAllProducts (checked : Converted entry limit) :
    ParameterKernel.ConversionTrace (modelLo limit) limit.value entry.source.result.assignment.denominator
      entry.source.result.assignment.quantum.numerator entry.source.result.assignment.quantum.denominator
      binding.profile.applyQuantum.numerator binding.profile.applyQuantum.denominator
      entry.source.result.numerators entry.values :=
  (ParameterKernel.checkedDomainVectorSound _ _ _ _ _ _ _ _ _ _ _ checked.computed).2.2.1

end Conversion

inductive Conversions {codec store trust anchor} {binding : Binding codec trust anchor store}
    (limit : ModelLimit) : List (ConvertedParameter binding) → Type where
  | nil : Conversions limit []
  | cons {entry entries} (head : Converted entry limit) (tail : Conversions limit entries) :
      Conversions limit (entry :: entries)

def checkConversions {codec store trust anchor} {binding : Binding codec trust anchor store}
    (limit : ModelLimit) : (entries : List (ConvertedParameter binding)) → Option (Conversions limit entries)
  | [] => some .nil
  | entry :: entries => do
      let head ← checkConversion entry limit
      let tail ← checkConversions limit entries
      some (.cons head tail)

theorem everyConversionChecked {codec store trust anchor} {binding : Binding codec trust anchor store}
    {limit entries} (checked : Conversions (binding := binding) limit entries) :
    ∀ entry ∈ entries, conversion entry limit = some entry.values := by
  induction checked with
  | nil => simp
  | @cons entry entries head tail ih =>
      intro e member
      rcases List.mem_cons.mp member with same | member
      · subst e; exact head.computed
      · exact ih e member

section Apply
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    (native : NativeApply binding) (limit : ModelLimit)

structure Checked where
  conversions : Conversions limit native.core.conversion.converted
  arithmetic : ApplyComputation (modelLo limit) limit.value binding.model.values binding.optimizer.values
    native.core.rows binding.profile.learningRate.kernelWeight binding.profile.momentum.kernelWeight
    binding.profile.weightDecay.kernelWeight

def check : Option (Checked native limit) := do
  let conversions ← checkConversions limit native.core.conversion.converted
  let arithmetic ← deriveApply (modelLo limit) limit.value binding.model.values binding.optimizer.values
    native.core.rows binding.profile.learningRate.kernelWeight binding.profile.momentum.kernelWeight
    binding.profile.weightDecay.kernelWeight
  some ⟨conversions,arithmetic⟩

theorem outputIdentity (checked : Checked native limit) :
    checked.arithmetic.nextModel = native.body.nextModel ∧
    checked.arithmetic.nextOptimizer = native.body.nextOptimizer :=
  (applyWidthsAgree checked.arithmetic native.core.computation).2.2

theorem originalRowsFromPlacedConvertedValues :
    native.core.rows.map (·.values) = (domainValues native.core.conversion.vectors).map Prod.snd ∧
    native.core.rows.map (·.weight) = binding.profile.domainWeights.map (fun w => w.weight.kernelWeight) :=
  ⟨(applyRowsExact native.core.aligned).2.1,(applyRowsExact native.core.aligned).1⟩

theorem noCertifiedConversionOmitted (checked : Checked native limit) :
    native.core.conversion.converted.map (·.source) = native.core.conversion.certified.corpus.entries ∧
    ∀ entry ∈ native.core.conversion.converted, conversion entry limit = some entry.values :=
  ⟨native.core.conversion.convertedSources,everyConversionChecked checked.conversions⟩

theorem originalOutputsMeetModelRange (checked : Checked native limit) :
    (∀ value ∈ native.body.nextModel, Fits (modelLo limit) limit.value value) ∧
    (∀ value ∈ native.body.nextOptimizer, Fits (modelLo limit) limit.value value) := by
  have bounds := (applyComputationShapeAndBounds checked.arithmetic).2.2.2.2
  simpa only [(outputIdentity native limit checked).1,(outputIdentity native limit checked).2] using bounds

end Apply
end DeltaReduce.PublicApplyArithmetic
