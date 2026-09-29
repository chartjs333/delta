import FamilyApplyArithmetic
import DeltaReduce.NativeApplyResult

/-! R2 numeric domain compatibility. These are implications from the existing
native checked operation graph, not new native preconditions. Public arithmetic
and the separate symmetric PARAMETER result guard have distinct bounds. -/
namespace DeltaReduce.FamilyGuards
open NativeBinding ParameterKernel ApplyKernel

theorem fitsWiden {lo hi wideLo wideHi value : Int} (lower : wideLo ≤ lo) (upper : hi ≤ wideHi)
    (h : Fits lo hi value) : Fits wideLo wideHi value := ⟨lower.trans h.1,h.2.trans upper⟩

theorem fractionWiden {lo hi wideLo wideHi a b : Int} (lower : wideLo ≤ lo) (upper : hi ≤ wideHi)
    (h : ReducedNonnegative lo hi a b) : ReducedNonnegative wideLo wideHi a b :=
  ⟨fitsWiden lower upper h.1,h.2.1,h.2.2.1,h.2.2.2.1.trans upper,h.2.2.2.2⟩

theorem addWiden {lo hi wideLo wideHi inputLo inputHi coefficient : Int}
    (lower : wideLo ≤ lo) (upper : hi ≤ wideHi) {acc values}
    (h : StepSafe lo hi inputLo inputHi coefficient acc values) :
    StepSafe wideLo wideHi inputLo inputHi coefficient acc values := by
  induction acc generalizing values with
  | nil => cases values <;> exact h
  | cons a acc ih =>
    cases values with
    | nil => exact h
    | cons q values => exact ⟨fitsWiden lower upper h.1,h.2.1,
        fitsWiden lower upper h.2.2.1,fitsWiden lower upper h.2.2.2.1,ih h.2.2.2.2⟩

theorem parameterPrefixesWiden {lo hi wideLo wideHi inputLo inputHi denominator : Int}
    (lower : wideLo ≤ lo) (upper : hi ≤ wideHi) {rows coefficientSum acc}
    (h : PrefixesSafe lo hi inputLo inputHi denominator coefficientSum acc rows) :
    PrefixesSafe wideLo wideHi inputLo inputHi denominator coefficientSum acc rows := by
  induction rows generalizing coefficientSum acc with
  | nil => exact ⟨fitsWiden lower upper h.1,fun v hv => fitsWiden lower upper (h.2 v hv)⟩
  | cons row rows ih =>
    refine ⟨?_,fitsWiden lower upper h.2.1,fitsWiden lower upper h.2.2.1,
      addWiden lower upper h.2.2.2.1,ih h.2.2.2.2⟩
    exact ⟨h.1.1,h.1.2.1,fitsWiden lower upper h.1.2.2.1,h.1.2.2.2.1,
      fitsWiden lower upper h.1.2.2.2.2⟩

theorem parameterWiden {lo hi wideLo wideHi inputLo inputHi denominator : Int}
    (lower : wideLo ≤ lo) (upper : hi ≤ wideHi) {width rows values}
    (h : checkedParameter lo hi inputLo inputHi denominator width rows = some values) :
    checkedParameter wideLo wideHi inputLo inputHi denominator width rows = some values := by
  have sound := checkedParameterSound _ _ _ _ _ _ _ _ h
  unfold checkedParameter
  rw [if_pos ⟨sound.1,sound.2.1⟩,
    checkedParameterRowsComplete _ _ _ _ _ _ _ _ (parameterPrefixesWiden lower upper sound.2.2.2.2.2),
    ← sound.2.2.2.1]

theorem lcmWiden {lo hi wideLo wideHi : Int} (lower : wideLo ≤ lo) (upper : hi ≤ wideHi)
    {weights initial denominator} (h : checkedLcm lo hi initial weights = some denominator) :
    checkedLcm wideLo wideHi initial weights = some denominator := by
  induction weights generalizing initial with
  | nil =>
    simp only [checkedLcm] at h ⊢
    split at h <;> try contradiction
    rename_i safe
    rw [if_pos ⟨safe.1,fitsWiden lower upper safe.2⟩]
    exact h
  | cons w ws ih =>
    simp only [checkedLcm] at h ⊢
    split at h <;> try contradiction
    rename_i safe
    rw [if_pos ⟨safe.1,fitsWiden lower upper safe.2.1,fractionWiden lower upper safe.2.2⟩]
    exact ih h

def widenPlan {lo hi wideLo wideHi : Int} (lower : wideLo ≤ lo) (upper : hi ≤ wideHi)
    {weights} (p : WeightPlan lo hi weights) : WeightPlan wideLo wideHi weights :=
  ⟨p.denominator,lcmWiden lower upper p.computed,p.nonempty,p.normalized⟩

theorem mixStepWiden {lo hi wideLo wideHi : Int} (lower : wideLo ≤ lo) (upper : hi ≤ wideHi)
    {denominator acc term} (h : MixStepSafe lo hi denominator acc term) :
    MixStepSafe wideLo wideHi denominator acc term :=
  ⟨fractionWiden lower upper h.1,h.2.1,fitsWiden lower upper h.2.2.1,h.2.2.2.1,
    fitsWiden lower upper h.2.2.2.2.1,fitsWiden lower upper h.2.2.2.2.2.1,
    fitsWiden lower upper h.2.2.2.2.2.2.1,fitsWiden lower upper h.2.2.2.2.2.2.2.1,
    fitsWiden lower upper h.2.2.2.2.2.2.2.2⟩
theorem mixPrefixesWiden {lo hi wideLo wideHi : Int} (lower : wideLo ≤ lo) (upper : hi ≤ wideHi)
    {denominator acc terms} (h : MixPrefixesSafe lo hi denominator acc terms) :
    MixPrefixesSafe wideLo wideHi denominator acc terms := by
  induction terms generalizing acc with
  | nil => exact fitsWiden lower upper h
  | cons t ts ih => exact ⟨mixStepWiden lower upper h.1,ih h.2⟩
theorem mixWiden {lo hi wideLo wideHi : Int} (lower : wideLo ≤ lo) (upper : hi ≤ wideHi)
    {denominator acc terms total} (h : checkedMix lo hi denominator acc terms = some total) :
    checkedMix wideLo wideHi denominator acc terms = some total := by
  have sound := checkedMixSound _ _ _ _ _ _ h
  rw [checkedMixComplete _ _ _ _ _ (mixPrefixesWiden lower upper sound.2.1),← sound.1]

def widenGradient {lo hi wideLo wideHi : Int} (lower : wideLo ≤ lo) (upper : hi ≤ wideHi)
    {rows plan coordinate} (g : DerivedGradient lo hi rows plan coordinate) :
    DerivedGradient wideLo wideHi rows (widenPlan lower upper plan) coordinate :=
  ⟨g.terms,g.column,g.total,mixWiden lower upper g.computed,fitsWiden lower upper g.output⟩
theorem gradientTraceWiden {lo hi wideLo wideHi : Int} (lower : wideLo ≤ lo) (upper : hi ≤ wideHi)
    {rows plan coordinates values} (h : GradientTrace lo hi rows plan coordinates values) :
    GradientTrace wideLo wideHi rows (widenPlan lower upper plan) coordinates values := by
  induction h with
  | nil => exact .nil
  | cons head tail ih => exact .cons (widenGradient lower upper head) ih

theorem optimizerWiden {lo hi wideLo wideHi : Int} (lower : wideLo ≤ lo) (upper : hi ≤ wideHi)
    {theta momentum gradient lr mu wd} (h : OptimizerSafe lo hi theta momentum gradient lr mu wd) :
    OptimizerSafe wideLo wideHi theta momentum gradient lr mu wd :=
  ⟨fun c hc => fractionWiden lower upper (h.1 c hc),
    fun v hv => fitsWiden lower upper (h.2.1 v hv),fun v hv => fitsWiden lower upper (h.2.2 v hv)⟩
theorem optimizerTraceWiden {lo hi wideLo wideHi : Int} (lower : wideLo ≤ lo) (upper : hi ≤ wideHi)
    {lr mu wd model optimizer gradients nextModel nextOptimizer}
    (h : OptimizerTrace lo hi lr mu wd model optimizer gradients nextModel nextOptimizer) :
    OptimizerTrace wideLo wideHi lr mu wd model optimizer gradients nextModel nextOptimizer := by
  induction h with
  | nil => exact .nil
  | cons safe tail ih => exact .cons (optimizerWiden lower upper safe) ih

def widenApply {lo hi wideLo wideHi : Int} (lower : wideLo ≤ lo) (upper : hi ≤ wideHi)
    {model optimizer rows lr mu wd} (a : ApplyComputation lo hi model optimizer rows lr mu wd) :
    ApplyComputation wideLo wideHi model optimizer rows lr mu wd :=
  ⟨a.nonempty,a.optimizerShape,a.rowShapes,widenPlan lower upper a.plan,a.gradients,
    gradientTraceWiden lower upper a.gradientTrace,a.nextModel,a.nextOptimizer,
    optimizerTraceWiden lower upper a.optimizerTrace⟩

theorem accumulatorAsymmetric (p : Profile) : accumulatorLo p = -(accumulatorHi p)-1 := by
  simp only [accumulatorLo,accumulatorHi]; omega
theorem nativeBoundsContained (p : Profile) (bits : p.accumulatorBits = 64 ∨ p.accumulatorBits = 128) :
    accumulatorLo p ≤ minInput ∧ maxInput ≤ accumulatorHi p := by
  rcases bits with h | h <;> simp only [accumulatorLo,accumulatorHi,h] <;> decide
theorem symmetricResultIncludesMinimum {p : Profile} {v : Int}
    (h : Fits (accumulatorLo p) (accumulatorHi p) v) :
    Fits (-(accumulatorHi p+1)) (accumulatorHi p+1) v := by
  rw [accumulatorAsymmetric] at h
  unfold Fits at h ⊢; omega

theorem nativeParameterAtPublicWidth {codec store trust anchor} {binding : Binding codec trust anchor store}
    {domain shard} (native : DerivedParameter binding domain shard) :
    checkedParameter (-(accumulatorHi binding.profile)-1) (accumulatorHi binding.profile) minInput maxInput
      native.assignment.denominator native.partition.length native.rows = some native.numerators := by
  simpa only [accumulatorAsymmetric] using native.computed

def nativeApplyAtPublicWidth {codec store trust anchor} {binding : Binding codec trust anchor store}
    (native : NativeApply binding) : ApplyComputation (accumulatorLo binding.profile) (accumulatorHi binding.profile)
      binding.model.values binding.optimizer.values native.core.rows binding.profile.learningRate.kernelWeight
      binding.profile.momentum.kernelWeight binding.profile.weightDecay.kernelWeight :=
  let bounds := nativeBoundsContained binding.profile native.core.conversion.certified.corpus.validated.2.2.2.2.2.2.1
  widenApply bounds.1 bounds.2 native.core.computation

theorem nativeApplyOutputsPreserved {codec store trust anchor} {binding : Binding codec trust anchor store}
    (native : NativeApply binding) :
    (nativeApplyAtPublicWidth native).nextModel = native.body.nextModel ∧
    (nativeApplyAtPublicWidth native).nextOptimizer = native.body.nextOptimizer := ⟨rfl,rfl⟩

/- Ordered-sequence formulation of production ABCheckedSequence: every item,
every prefix including the empty prefix. No final-sum-only shortcut. -/
def SequenceSafe (lo hi acc : Int) : List Int → Prop
  | [] => Fits lo hi acc
  | v :: vs => Fits lo hi acc ∧ Fits lo hi v ∧ SequenceSafe lo hi (acc+v) vs
def PublicSequence (limit : Int) (values : List Int) : Prop :=
  (∀ v ∈ values, Fits (-limit-1) limit v) ∧
  ∀ n ≤ values.length, Fits (-limit-1) limit ((values.take n).sum)

theorem sequenceItems {lo hi acc values} (h : SequenceSafe lo hi acc values) :
    ∀ v ∈ values, Fits lo hi v := by
  induction values generalizing acc with
  | nil => simp
  | cons v vs ih =>
    intro x hx
    rcases List.mem_cons.mp hx with eq | hx
    · subst x; exact h.2.1
    · exact ih h.2.2 x hx
theorem sequencePrefixes {lo hi acc values} (h : SequenceSafe lo hi acc values) :
    ∀ n ≤ values.length, Fits lo hi (acc + (values.take n).sum) := by
  induction values generalizing acc with
  | nil => intro n hn; have : n = 0 := by simpa using hn
           subst n; simpa [SequenceSafe] using h
  | cons v vs ih =>
    intro n hn
    cases n with
    | zero => simpa using h.1
    | succ n =>
      have bound : n ≤ vs.length := by simpa using hn
      simpa only [List.take_succ_cons,List.sum_cons,Int.add_assoc] using ih h.2.2 n bound
theorem publicSequenceFromRecurrence {limit values} (h : SequenceSafe (-limit-1) limit 0 values) :
    PublicSequence limit values := ⟨sequenceItems h,by simpa using sequencePrefixes h⟩

theorem coefficientSequence {lo hi inputLo inputHi denominator acc rows coefficientSum}
    (h : PrefixesSafe lo hi inputLo inputHi denominator coefficientSum acc rows) :
    SequenceSafe lo hi coefficientSum (rows.map (fun r => r.numerator*(denominator/r.denominator))) := by
  induction rows generalizing acc coefficientSum with
  | nil => exact h.1
  | cons r rs ih => exact ⟨h.2.1,h.1.2.2.2.2,ih h.2.2.2.2⟩
theorem productSequence {lo hi acc terms} (h : AllPrefixesFit lo hi lo hi acc terms) :
    SequenceSafe lo hi acc (terms.map (fun t => t.1*t.2)) := by
  induction terms generalizing acc with
  | nil => exact h
  | cons t ts ih => exact ⟨h.1,h.2.1,ih h.2.2⟩

theorem nativeParameterPublicSequences {codec store trust anchor} {binding : Binding codec trust anchor store}
    {domain shard} (native : DerivedParameter binding domain shard) (k : Fin native.partition.length) :
    PublicSequence (accumulatorHi binding.profile)
      (native.rows.map (fun r => r.numerator*(native.assignment.denominator/r.denominator))) ∧
    PublicSequence (accumulatorHi binding.profile)
      ((coordinateTerms native.assignment.denominator k.val native.rows).map (fun t => t.1*t.2)) := by
  have checked := nativeParameterAtPublicWidth native
  have full := checkedParameterSound _ _ _ _ _ _ _ _ checked
  obtain ⟨v,_,fold⟩ := checkedParameterCoordinateRefines _ _ _ _ _ _ _ _ checked k.val k.isLt
  exact ⟨publicSequenceFromRecurrence (coefficientSequence full.2.2.2.2.2),
    publicSequenceFromRecurrence (productSequence (checkedAccumulateSound _ _ _ _ _ _ _ fold).2.1)⟩

def PublicConversion (limit n denominator u v x y result : Int) : Prop :=
  Fits (-limit-1) limit (n*u) ∧ Fits (-limit-1) limit ((n*u)*y) ∧
  Fits (-limit-1) limit (denominator*v) ∧ Fits (-limit-1) limit ((denominator*v)*x) ∧
  Fits (-limit-1) limit result ∧ result = round ((n*u)*y) ((denominator*v)*x)
theorem conversionIsPublicGuard {p : Profile} {n denominator u v x y result}
    (h : ConversionSafe (accumulatorLo p) (accumulatorHi p) denominator u v x y n result) :
    PublicConversion (accumulatorHi p) n denominator u v x y result := by
  rw [accumulatorAsymmetric] at h
  exact h.2

def PublicOptimizerValues (theta momentum gradient : Int) (lr mu wd : Weight) : List Int :=
  let v := optimizerValues theta momentum gradient lr mu wd
  [v.momentumProduct,v.nextOptimizer,v.nextMomentumProduct,v.direction,v.decayProduct,v.decay,
   v.directionWithDecay,v.stepProduct,v.step,v.nextModel]
theorem publicOptimizerSubsequence (theta momentum gradient : Int) (lr mu wd : Weight) :
    (PublicOptimizerValues theta momentum gradient lr mu wd).Sublist
      (optimizerValues theta momentum gradient lr mu wd).intermediates := by
  simp only [PublicOptimizerValues,OptimizerValues.intermediates]
  repeat first | apply List.Sublist.cons_cons | apply List.Sublist.cons
  exact List.Sublist.slnil
theorem optimizerIsPublicGuard {lo hi theta momentum gradient lr mu wd}
    (h : OptimizerSafe lo hi theta momentum gradient lr mu wd) :
    Fits lo hi gradient ∧ ∀ v ∈ PublicOptimizerValues theta momentum gradient lr mu wd, Fits lo hi v :=
  ⟨h.2.1 gradient (by simp),fun v hv => h.2.2 v
    ((publicOptimizerSubsequence theta momentum gradient lr mu wd).subset hv)⟩

def mixtureProducts (denominator : Int) (terms : List MixTerm) : List Int :=
  terms.map (fun t => (t.value*t.weight.numerator)*(denominator/t.weight.denominator))
theorem mixtureSequence {lo hi denominator acc terms} (h : MixPrefixesSafe lo hi denominator acc terms) :
    SequenceSafe lo hi acc (mixtureProducts denominator terms) ∧
    ∀ t ∈ terms, Fits lo hi (t.value*t.weight.numerator) := by
  induction terms generalizing acc with
  | nil => exact ⟨h,by simp⟩
  | cons t ts ih =>
    have tail := ih h.2
    refine ⟨⟨h.1.2.2.2.2.1,h.1.2.2.2.2.2.2.2.1,tail.1⟩,?_⟩
    intro term member
    rcases List.mem_cons.mp member with eq | member
    · subst term; exact h.1.2.2.2.2.2.2.1
    · exact tail.2 term member

theorem nativeApplyPublicGuards {codec store trust anchor} {binding : Binding codec trust anchor store}
    (native : NativeApply binding) (k : Fin binding.model.values.length) :
    ∃ total terms,
      ColumnTerms k.val native.core.rows terms ∧
      PublicSequence (accumulatorHi binding.profile)
        (mixtureProducts (Int.ofNat native.core.computation.plan.denominator) terms) ∧
      (∀ t ∈ terms, Fits (-(accumulatorHi binding.profile)-1) (accumulatorHi binding.profile)
        (t.value*t.weight.numerator)) ∧
      Fits (-(accumulatorHi binding.profile)-1) (accumulatorHi binding.profile)
        (Int.ofNat native.core.computation.plan.denominator) ∧
      Fits (-(accumulatorHi binding.profile)-1) (accumulatorHi binding.profile)
        (NativeFamily.applyCell native k).gradient ∧
      (∀ v ∈ PublicOptimizerValues (NativeFamily.applyCell native k).model (NativeFamily.applyCell native k).optimizer
        (NativeFamily.applyCell native k).gradient binding.profile.learningRate.kernelWeight binding.profile.momentum.kernelWeight
        binding.profile.weightDecay.kernelWeight,
        Fits (-(accumulatorHi binding.profile)-1) (accumulatorHi binding.profile) v) ∧
      round total (Int.ofNat native.core.computation.plan.denominator) = (NativeFamily.applyCell native k).gradient := by
  obtain ⟨total,terms,column,mix,rounded,optimized⟩ := NativeFamily.applyArithmeticCoordinate native k
  have bounds := nativeBoundsContained binding.profile native.core.conversion.certified.corpus.validated.2.2.2.2.2.2.1
  rw [accumulatorAsymmetric] at bounds
  have wide := checkedMixSound _ _ _ _ _ _ (mixWiden bounds.1 bounds.2 mix)
  have seq := mixtureSequence wide.2.1
  have opt := optimizerIsPublicGuard (optimizerWiden bounds.1 bounds.2
    (checkedOptimizerSound _ _ _ _ _ _ _ _ _ optimized).1)
  refine ⟨total,terms,column,publicSequenceFromRecurrence seq.1,seq.2,?_,opt.1,opt.2,rounded⟩
  exact fitsWiden bounds.1 bounds.2 (weightPlanLeast _ _ _ native.core.computation.plan).2.1

theorem conversionCoordinate {lo hi denominator u v x y ns values}
    (trace : ConversionTrace lo hi denominator u v x y ns values)
    {k : Nat} {n : Int} (atN : ns[k]? = some n) :
    ∃ value, values[k]? = some value ∧ ConversionSafe lo hi denominator u v x y n value := by
  induction trace generalizing k with
  | nil => simp at atN
  | cons head tail ih =>
    cases k with
    | zero => simp only [List.getElem?_cons_zero,Option.some.injEq] at atN
              subst n; exact ⟨_,rfl,head⟩
    | succ k => exact ih atN

theorem nativeConversionPublicGuard {codec store trust anchor} {binding : Binding codec trust anchor store}
    (entry : ConvertedParameter binding) (k : Fin entry.source.result.partition.length) :
    ∃ n value, entry.source.result.numerators[k.val]? = some n ∧ entry.values[k.val]? = some value ∧
      PublicConversion (accumulatorHi binding.profile) n entry.source.result.assignment.denominator
        entry.source.result.assignment.quantum.numerator entry.source.result.assignment.quantum.denominator
        binding.profile.applyQuantum.numerator binding.profile.applyQuantum.denominator value ∧
      Fits minInput maxInput value := by
  have shape := (checkedParameterSound _ _ _ _ _ _ _ _ entry.source.result.computed).2.2.1
  have inside : k.val < entry.source.result.numerators.length := by rw [shape]; exact k.isLt
  have atN := List.getElem?_eq_getElem inside
  obtain ⟨value,atValue,safe⟩ := conversionCoordinate (convertedParameterSound entry).2.1 atN
  exact ⟨_,value,atN,atValue,conversionIsPublicGuard safe,
    entry.outputBounds value (List.mem_of_getElem? atValue)⟩

theorem exactAccumulateIsSum (acc : Int) (terms : List (Int × Int)) :
    exactAccumulate acc terms = acc + (terms.map (fun t => t.1*t.2)).sum := by
  induction terms generalizing acc with
  | nil => simp [exactAccumulate]
  | cons t ts ih => simp only [exactAccumulate,ih,List.map_cons,List.sum_cons,Int.add_assoc]

theorem nativeParameterResultGuard {codec store trust anchor} {binding : Binding codec trust anchor store}
    {domain shard} (native : DerivedParameter binding domain shard) (k : Fin native.partition.length) :
    ∃ value, native.numerators[k.val]? = some value ∧
      value = ((coordinateTerms native.assignment.denominator k.val native.rows).map (fun t => t.1*t.2)).sum ∧
      Fits (-(accumulatorHi binding.profile+1)) (accumulatorHi binding.profile+1) value := by
  obtain ⟨value,atValue,computed⟩ := checkedParameterCoordinateRefines _ _ _ _ _ _ _ _ native.computed k.val k.isLt
  have sound := checkedAccumulateSound _ _ _ _ _ _ _ computed
  exact ⟨value,atValue,by simpa only [exactAccumulateIsSum,Int.zero_add] using sound.1,
    symmetricResultIncludesMinimum sound.2.2⟩

theorem derivePlanComplete {lo hi weights} (p : WeightPlan lo hi weights) :
    deriveWeightPlan lo hi weights = some p := by
  unfold deriveWeightPlan
  split
  · rename_i absent; simp [p.computed] at absent
  · rename_i d hd
    have equal := Option.some.inj (hd.symm.trans p.computed)
    subst d
    rw [dif_pos ⟨p.nonempty,p.normalized⟩]

theorem extractColumnComplete {coordinate rows terms} (h : ColumnTerms coordinate rows terms) :
    extractColumn rows coordinate = some ⟨terms,h⟩ := by
  induction h with
  | nil => rfl
  | cons present tail ih =>
    simp only [extractColumn,ih,bind,Option.bind]
    split
    · rename_i absent; rw [present] at absent; contradiction
    · rename_i value found
      have equal := Option.some.inj (found.symm.trans present)
      subst value; rfl

theorem deriveGradientComplete {lo hi rows plan coordinate} (g : DerivedGradient lo hi rows plan coordinate) :
    deriveGradient lo hi rows plan coordinate = some g := by
  unfold deriveGradient
  rw [extractColumnComplete g.column]
  simp only [bind,Option.bind]
  split
  · rename_i absent
    have impossible : none = some g.total := absent.symm.trans g.computed
    contradiction
  · rename_i total ht
    have equal := Option.some.inj (ht.symm.trans g.computed)
    subst total
    rw [dif_pos g.output]

theorem deriveGradientsComplete {lo hi rows plan coordinates values}
    (h : GradientTrace lo hi rows plan coordinates values) :
    deriveGradients lo hi rows plan coordinates = some ⟨values,h⟩ := by
  induction h with
  | nil => rfl
  | cons head tail ih => simp only [deriveGradients,deriveGradientComplete head,ih,bind,Option.bind]

theorem optimizerVectorsComplete {lo hi lr mu wd model optimizer gradient nextModel nextOptimizer}
    (h : OptimizerTrace lo hi lr mu wd model optimizer gradient nextModel nextOptimizer) :
    checkedOptimizerVectors lo hi lr mu wd model optimizer gradient = some (nextModel,nextOptimizer) := by
  induction h with
  | nil => rfl
  | cons head tail ih => simp only [checkedOptimizerVectors,checkedOptimizer,if_pos head,ih,bind,Option.bind]

theorem deriveApplyComplete {lo hi model optimizer rows lr mu wd}
    (a : ApplyComputation lo hi model optimizer rows lr mu wd) :
    deriveApply lo hi model optimizer rows lr mu wd = some a := by
  unfold deriveApply
  rw [dif_pos ⟨a.nonempty,a.optimizerShape,a.rowShapes⟩,derivePlanComplete a.plan]
  simp only [bind,Option.bind]
  rw [deriveGradientsComplete a.gradientTrace]
  dsimp only [bind,Option.bind]
  split
  · rename_i absent; simp [optimizerVectorsComplete a.optimizerTrace] at absent
  · rename_i m o computed
    have equal := Option.some.inj (computed.symm.trans (optimizerVectorsComplete a.optimizerTrace))
    obtain ⟨em,eo⟩ := Prod.mk.inj equal
    subst m; subst o
    rfl

def nativeConversions {codec store trust anchor} {binding : Binding codec trust anchor store} :
    (entries : List (ConvertedParameter binding)) → FamilyApplyArithmetic.Conversions (accumulatorHi binding.profile) entries
  | [] => .nil
  | entry :: entries => .cons ⟨by simpa only [FamilyApplyArithmetic.conversion,accumulatorAsymmetric] using entry.computed⟩
      (nativeConversions entries)

theorem checkConversionsComplete {codec store trust anchor} {binding : Binding codec trust anchor store}
    {limit entries} (h : FamilyApplyArithmetic.Conversions (binding := binding) limit entries) :
    FamilyApplyArithmetic.checkConversions limit entries = some h := by
  induction h with
  | nil => rfl
  | cons head tail ih =>
    have checked : FamilyApplyArithmetic.checkConversion _ limit = some head := by
      unfold FamilyApplyArithmetic.checkConversion
      split
      · rename_i absent; simp [head.computed] at absent
      · rfl
    simp only [FamilyApplyArithmetic.checkConversions,checked,ih,bind,Option.bind]

def nativePublicArithmetic {codec store trust anchor} {binding : Binding codec trust anchor store}
    (native : NativeApply binding) : FamilyApplyArithmetic.Checked native (accumulatorHi binding.profile) :=
  ⟨nativeConversions _,by simpa only [accumulatorAsymmetric] using nativeApplyAtPublicWidth native⟩

theorem nativePublicArithmeticCheck {codec store trust anchor} {binding : Binding codec trust anchor store}
    (native : NativeApply binding) :
    FamilyApplyArithmetic.check native (accumulatorHi binding.profile) = some (nativePublicArithmetic native) := by
  unfold FamilyApplyArithmetic.check
  rw [checkConversionsComplete (nativePublicArithmetic native).conversions]
  simp only [bind,Option.bind]
  rw [deriveApplyComplete (nativePublicArithmetic native).arithmetic]

/- The original C++ Apply engine rounds an int64 product with a uint64
denominator. In particular that denominator need not fit signed int64. The
mathematical translation below retains its magnitude/negative tie branch. -/
def magnitudeRound (n d : Int) : Int :=
  if 0 ≤ n then
    if n % d < d - n % d then n / d else n / d + 1
  else
    if (-n) % d ≤ d - (-n) % d then -((-n) / d) else -((-n) / d) - 1

theorem magnitudeRoundExact (n d : Int) (positive : 0 < d) : magnitudeRound n d = round n d := by
  by_cases nonnegative : 0 ≤ n
  · simp only [magnitudeRound,if_pos nonnegative,round,roundParts]
  · have negative : n < 0 := by omega
    have quotient := Int.neg_ediv (a := -n) (b := d)
    have remainder := Int.neg_emod (a := -n) (b := d)
    have sign : d.sign = 1 := Int.sign_eq_one_of_pos positive
    have abs : (d.natAbs : Int) = d := Int.natAbs_of_nonneg (by omega)
    simp only [Int.neg_neg,sign,abs] at quotient remainder
    by_cases divides : d ∣ -n
    · have zero : (-n) % d = 0 := Int.emod_eq_zero_of_dvd divides
      simp only [if_pos divides,sub_zero] at quotient remainder
      simp only [magnitudeRound,if_neg nonnegative,zero,round,roundParts,quotient,remainder]
      simp [positive,show (0 : Int) ≤ d by omega]
    · simp only [if_neg divides] at quotient remainder
      simp only [magnitudeRound,if_neg nonnegative,round,roundParts,quotient,remainder]
      split <;> split <;> omega

def NativeRoundValid (n d : Int) : Prop :=
  Fits minInput maxInput n ∧ 0 < d ∧ d < 2^64 ∧
    (if 0 ≤ n then n else -n) / d ≤ maxInput ∧ Fits minInput maxInput (magnitudeRound n d)
instance (n d) : Decidable (NativeRoundValid n d) := by unfold NativeRoundValid; infer_instance

def checkedNativeRound (n d : Int) : Option Int :=
  if NativeRoundValid n d then
    some (magnitudeRound n d)
  else none

theorem nativeRoundSound {n d value : Int} (h : checkedNativeRound n d = some value) :
    value = round n d ∧ Fits minInput maxInput value ∧ 0 < d ∧ d < 2^64 := by
  unfold checkedNativeRound at h
  split at h <;> try contradiction
  rename_i checked
  cases Option.some.inj h
  exact ⟨magnitudeRoundExact n d checked.2.1,checked.2.2.2.2,checked.2.1,checked.2.2.1⟩

def WireWeight (w : Weight) : Prop :=
  0 ≤ w.numerator ∧ w.numerator ≤ maxInput ∧ 0 < w.denominator ∧ w.denominator < 2^64 ∧
    Int.gcd w.numerator w.denominator = 1
instance (w) : Decidable (WireWeight w) := by unfold WireWeight; infer_instance

theorem originalFractionFits {f : NativeApplyProfile.Fraction} (valid : NativeApplyProfile.FractionValid f) :
    WireWeight (NativeApplyResult.fraction f).kernelWeight := by
  obtain ⟨numerator,positive,bounded,reduced⟩ := valid
  simp only [WireWeight,NativeApplyResult.fraction,Rational.kernelWeight]
  refine ⟨by omega,?_,by omega,?_,by simpa only [Int.gcd_natCast_natCast] using reduced⟩
  · unfold maxInput; norm_num at numerator ⊢; omega
  · norm_num at bounded ⊢; omega

def checkedI64 (value : Int) : Option Int :=
  if Fits minInput maxInput value then some value else none

theorem i64Sound {value result} (h : checkedI64 value = some result) :
    result = value ∧ Fits minInput maxInput result := by
  unfold checkedI64 at h
  split at h <;> try contradiction
  cases Option.some.inj h
  exact ⟨rfl,by assumption⟩

/- This is the operation graph in delta-core-cpp/src/apply/engine.cpp, including
the checked negation of step before checked addition to the parent model. It
does not execute C++ or authenticate the decoded profile/state. -/
def nativeOptimizer (theta momentum gradient : Int) (lr mu wd : Weight) : Option OptimizerValues := do
  if (∀ w ∈ [lr,mu,wd], WireWeight w) ∧ (∀ v ∈ [theta,momentum,gradient], Fits minInput maxInput v) then
    let mp ← checkedI64 (momentum*mu.numerator)
    let ms ← checkedNativeRound mp mu.denominator
    let next ← checkedI64 (ms+gradient)
    let np ← checkedI64 (next*mu.numerator)
    let ns ← checkedNativeRound np mu.denominator
    let direction ← checkedI64 (ns+gradient)
    let dp ← checkedI64 (theta*wd.numerator)
    let decay ← checkedNativeRound dp wd.denominator
    let stepInput ← checkedI64 (direction+decay)
    let sp ← checkedI64 (stepInput*lr.numerator)
    let step ← checkedNativeRound sp lr.denominator
    let negative ← checkedI64 (step*(-1))
    let model ← checkedI64 (theta+negative)
    some ⟨mp,ms,next,np,ns,direction,dp,decay,stepInput,sp,step,model⟩
  else none

theorem nativeOptimizerSound {theta momentum gradient lr mu wd values}
    (h : nativeOptimizer theta momentum gradient lr mu wd = some values) :
    values = optimizerValues theta momentum gradient lr mu wd ∧
    (∀ w ∈ [lr,mu,wd], WireWeight w) ∧
    (∀ v ∈ [theta,momentum,gradient], Fits minInput maxInput v) ∧
    ∀ v ∈ values.intermediates, Fits minInput maxInput v := by
  unfold nativeOptimizer at h
  split at h <;> try contradiction
  rename_i checked
  obtain ⟨mp,hmp,h⟩ := Option.bind_eq_some_iff.mp h
  obtain ⟨ms,hms,h⟩ := Option.bind_eq_some_iff.mp h
  obtain ⟨next,hn,h⟩ := Option.bind_eq_some_iff.mp h
  obtain ⟨np,hnp,h⟩ := Option.bind_eq_some_iff.mp h
  obtain ⟨ns,hns,h⟩ := Option.bind_eq_some_iff.mp h
  obtain ⟨direction,hd,h⟩ := Option.bind_eq_some_iff.mp h
  obtain ⟨dp,hdp,h⟩ := Option.bind_eq_some_iff.mp h
  obtain ⟨decay,hdec,h⟩ := Option.bind_eq_some_iff.mp h
  obtain ⟨stepInput,hsi,h⟩ := Option.bind_eq_some_iff.mp h
  obtain ⟨sp,hsp,h⟩ := Option.bind_eq_some_iff.mp h
  obtain ⟨step,hst,h⟩ := Option.bind_eq_some_iff.mp h
  obtain ⟨negative,hneg,h⟩ := Option.bind_eq_some_iff.mp h
  obtain ⟨model,hm,last⟩ := Option.bind_eq_some_iff.mp h
  obtain ⟨rfl,bmp⟩ := i64Sound hmp
  obtain ⟨rfl,bms,_,_⟩ := nativeRoundSound hms
  obtain ⟨rfl,bn⟩ := i64Sound hn
  obtain ⟨rfl,bnp⟩ := i64Sound hnp
  obtain ⟨rfl,bns,_,_⟩ := nativeRoundSound hns
  obtain ⟨rfl,bd⟩ := i64Sound hd
  obtain ⟨rfl,bdp⟩ := i64Sound hdp
  obtain ⟨rfl,bdec,_,_⟩ := nativeRoundSound hdec
  obtain ⟨rfl,bsi⟩ := i64Sound hsi
  obtain ⟨rfl,bsp⟩ := i64Sound hsp
  obtain ⟨rfl,bst,_,_⟩ := nativeRoundSound hst
  obtain ⟨rfl,_⟩ := i64Sound hneg
  obtain ⟨rfl,bm⟩ := i64Sound hm
  cases Option.some.inj last
  refine ⟨by simp [optimizerValues,Int.sub_eq_add_neg],checked.1,checked.2,?_⟩
  intro v member
  simp only [OptimizerValues.intermediates,List.mem_cons,List.not_mem_nil,or_false] at member
  rcases member with rfl|rfl|rfl|rfl|rfl|rfl|rfl|rfl|rfl|rfl|rfl|rfl <;> assumption

theorem nativeOptimizerPublicGuard {theta momentum gradient lr mu wd values}
    (h : nativeOptimizer theta momentum gradient lr mu wd = some values) (limit : Int)
    (lower : -limit-1 ≤ minInput) (upper : maxInput ≤ limit) :
    Fits (-limit-1) limit gradient ∧
    (∀ v ∈ PublicOptimizerValues theta momentum gradient lr mu wd, Fits (-limit-1) limit v) ∧
    values.nextModel = (optimizerValues theta momentum gradient lr mu wd).nextModel ∧
    values.nextOptimizer = (optimizerValues theta momentum gradient lr mu wd).nextOptimizer := by
  have sound := nativeOptimizerSound h
  refine ⟨fitsWiden lower upper (sound.2.2.1 gradient (by simp)),?_,
    congrArg OptimizerValues.nextModel sound.1,congrArg OptimizerValues.nextOptimizer sound.1⟩
  intro v hv
  have bounded := sound.2.2.2 v
  rw [sound.1] at bounded
  exact fitsWiden lower upper (bounded ((publicOptimizerSubsequence theta momentum gradient lr mu wd).subset hv))

/- Full ordered traversal of the original model/optimizer vectors. Mismatched
shapes reject before producing a partial vector; no coordinate identity exists.
The original decoded profile is retained, including its unsigned denominators. -/
def nativeOptimizerVector (p : NativeApplyProfile.Profile) :
    List Int → List Int → List Int → Option (List OptimizerValues)
  | [],[],[] => some []
  | theta::model,momentum::optimizer,g::gradients => do
    let head ← nativeOptimizer theta momentum g (NativeApplyResult.fraction p.learning).kernelWeight
      (NativeApplyResult.fraction p.momentum).kernelWeight (NativeApplyResult.fraction p.decay).kernelWeight
    let tail ← nativeOptimizerVector p model optimizer gradients
    some (head::tail)
  | _,_,_ => none

theorem nativeVectorShape {p model optimizer gradients values}
    (h : nativeOptimizerVector p model optimizer gradients = some values) :
    model.length = values.length ∧ optimizer.length = values.length ∧ gradients.length = values.length := by
  induction model generalizing optimizer gradients values with
  | nil => cases optimizer <;> cases gradients <;> simp [nativeOptimizerVector] at h
           subst values; exact ⟨rfl,rfl,rfl⟩
  | cons theta model ih =>
    cases optimizer with
    | nil => simp [nativeOptimizerVector] at h
    | cons momentum optimizer =>
      cases gradients with
      | nil => simp [nativeOptimizerVector] at h
      | cons g gradients =>
        simp only [nativeOptimizerVector,bind,Option.bind_eq_some_iff] at h
        obtain ⟨head,_,tail,ht,last⟩ := h
        cases Option.some.inj last
        obtain ⟨hm,ho,hg⟩ := ih ht
        exact ⟨by simp [hm],by simp [ho],by simp [hg]⟩

theorem nativeVectorAt {p model optimizer gradients values}
    (h : nativeOptimizerVector p model optimizer gradients = some values)
    {index : Nat} {value} (atValue : values[index]? = some value) :
    ∃ theta momentum g, model[index]? = some theta ∧ optimizer[index]? = some momentum ∧
      gradients[index]? = some g ∧ nativeOptimizer theta momentum g
        (NativeApplyResult.fraction p.learning).kernelWeight
        (NativeApplyResult.fraction p.momentum).kernelWeight
        (NativeApplyResult.fraction p.decay).kernelWeight = some value := by
  induction model generalizing optimizer gradients values index with
  | nil => cases optimizer <;> cases gradients <;> simp [nativeOptimizerVector] at h
           subst values; simp at atValue
  | cons theta model ih =>
    cases optimizer with
    | nil => simp [nativeOptimizerVector] at h
    | cons momentum optimizer =>
      cases gradients with
      | nil => simp [nativeOptimizerVector] at h
      | cons g gradients =>
        simp only [nativeOptimizerVector,bind,Option.bind_eq_some_iff] at h
        obtain ⟨head,hh,tail,ht,last⟩ := h
        cases Option.some.inj last
        cases index with
        | zero => simp only [List.getElem?_cons_zero,Option.some.injEq] at atValue
                  subst value; exact ⟨theta,momentum,g,rfl,rfl,rfl,hh⟩
        | succ index => exact ih ht atValue

structure OriginalOptimizer where
  profile : NativeApplyProfile.Checked
  values : List OptimizerValues

def checkOriginalOptimizer (sha : NativeBinding.Bytes → NativeBinding.Bytes)
    (source : NativePolicyCodec.Value) (model optimizer gradients : List Int) : Option OriginalOptimizer := do
  let profile ← NativeApplyProfile.check sha source
  let values ← nativeOptimizerVector profile.profile model optimizer gradients
  some ⟨profile,values⟩

theorem originalOptimizerSource {sha source model optimizer gradients out}
    (h : checkOriginalOptimizer sha source model optimizer gradients = some out) :
    NativeApplyProfile.check sha source = some out.profile ∧
    source = NativeApplyProfile.profileValue out.profile.profile ∧
    NativeApplyProfile.id sha out.profile.profile = some out.profile.id ∧
    nativeOptimizerVector out.profile.profile model optimizer gradients = some out.values := by
  simp only [checkOriginalOptimizer,bind,Option.bind_eq_some_iff] at h
  obtain ⟨profile,hp,values,hv,last⟩ := h
  cases Option.some.inj last
  exact ⟨hp,(NativeApplyProfile.checkedSource hp).2.1,(NativeApplyProfile.checkedSource hp).2.2.2,hv⟩

theorem originalOptimizerEveryCoordinate {sha source model optimizer gradients out}
    (h : checkOriginalOptimizer sha source model optimizer gradients = some out)
    {index : Nat} {value} (atValue : out.values[index]? = some value)
    (limit : Int) (lower : -limit-1 ≤ minInput) (upper : maxInput ≤ limit) :
    ∃ theta momentum g, model[index]? = some theta ∧ optimizer[index]? = some momentum ∧
      gradients[index]? = some g ∧ Fits (-limit-1) limit g ∧
      (∀ v ∈ PublicOptimizerValues theta momentum g
        (NativeApplyResult.fraction out.profile.profile.learning).kernelWeight
        (NativeApplyResult.fraction out.profile.profile.momentum).kernelWeight
        (NativeApplyResult.fraction out.profile.profile.decay).kernelWeight, Fits (-limit-1) limit v) ∧
      value = optimizerValues theta momentum g
        (NativeApplyResult.fraction out.profile.profile.learning).kernelWeight
        (NativeApplyResult.fraction out.profile.profile.momentum).kernelWeight
        (NativeApplyResult.fraction out.profile.profile.decay).kernelWeight := by
  obtain ⟨theta,momentum,g,hm,ho,hg,computed⟩ := nativeVectorAt (originalOptimizerSource h).2.2.2 atValue
  have guard := nativeOptimizerPublicGuard computed limit lower upper
  exact ⟨theta,momentum,g,hm,ho,hg,guard.1,guard.2.1,(nativeOptimizerSound computed).1⟩

/- The original mixture engine folds initial*(denominator/gcd) in uint64,
then checks the final LCM <= INT64_MAX. That existing guard entails the old
signed denominator and prefix restrictions for domain weights. It does NOT
entail normalization; sum(weights)=1 belongs to the frozen configuration
contract and still needs its source/configuration binding. The same bound
argument does not apply to optimizer learning/momentum/decay denominators. -/
theorem nativeLcmScale (initial denominator : Nat) :
    initial * (denominator / Nat.gcd initial denominator) = Nat.lcm initial denominator := by
  rw [Nat.lcm_eq_mul_div, Nat.mul_div_assoc initial (Nat.gcd_dvd_right initial denominator)]

theorem wireMixtureWeightFits {weights : List Weight}
    (wire : ∀ w ∈ weights, WireWeight w)
    (bound : (foldLcm 1 (weights.map (fun w => w.denominator.toNat)) : Int) ≤ maxInput)
    {w : Weight} (member : w ∈ weights) : ReducedNonnegative minInput maxInput w.numerator w.denominator := by
  have positive : ∀ d ∈ weights.map (fun w => w.denominator.toNat), 0 < d := by
    intro d hd
    obtain ⟨v,hv,rfl⟩ := List.mem_map.mp hd
    have h : 0 < v.denominator := (wire v hv).2.2.1
    omega
  have lcm := foldLcmSpec 1 (weights.map (fun w => w.denominator.toNat)) (by decide) positive
  have divides := lcm.2.2.1 w.denominator.toNat (List.mem_map.mpr ⟨w,member,rfl⟩)
  have le := Nat.le_of_dvd lcm.1 divides
  obtain ⟨wn,wbound,wp,_,wred⟩ := wire w member
  have cast : (w.denominator.toNat : Int) = w.denominator := Int.toNat_of_nonneg (by omega)
  have denominator : w.denominator ≤ maxInput := by
    have castLe : (w.denominator.toNat : Int) ≤ (foldLcm 1 (weights.map (fun w => w.denominator.toNat)) : Int) := by exact_mod_cast le
    omega
  exact ⟨⟨by unfold minInput; omega,wbound⟩,wn,wp,denominator,wred⟩

theorem lcmPrefixesFromFinalBound {weights : List Weight} {initial : Nat}
    (positive : 0 < initial)
    (valid : ∀ w ∈ weights, ReducedNonnegative minInput maxInput w.numerator w.denominator)
    (bound : (foldLcm initial (weights.map (fun w => w.denominator.toNat)) : Int) ≤ maxInput) :
    LcmPrefixesSafe minInput maxInput initial weights := by
  induction weights generalizing initial with
  | nil => exact ⟨positive,⟨by change minInput ≤ (initial : Int); unfold minInput; omega,bound⟩⟩
  | cons w ws ih =>
    have wp := valid w List.mem_cons_self
    have allPositive : ∀ d ∈ (w::ws).map (fun w => w.denominator.toNat), 0 < d := by
      intro d hd
      obtain ⟨v,hv,rfl⟩ := List.mem_map.mp hd
      have h : 0 < v.denominator := (valid v hv).2.2.1
      omega
    have all := foldLcmSpec initial ((w::ws).map (fun w => w.denominator.toNat)) positive allPositive
    have prior := Nat.le_of_dvd all.1 all.2.1
    have priorCast : (initial : Int) ≤ (foldLcm initial ((w::ws).map (fun w => w.denominator.toNat)) : Int) := by exact_mod_cast prior
    refine ⟨positive,⟨by change minInput ≤ (initial : Int); unfold minInput; omega,priorCast.trans bound⟩,wp,?_⟩
    have pos : 0 < w.denominator.toNat := by have := wp.2.2.1; omega
    exact ih (Nat.lcm_pos positive pos)
      (fun v hv => valid v (List.mem_cons_of_mem _ hv)) bound

theorem lcmComputedFromPrefixes {initial : Nat} {weights : List Weight}
    (safe : LcmPrefixesSafe minInput maxInput initial weights) :
    checkedLcm minInput maxInput initial weights =
      some (foldLcm initial (weights.map (fun w => w.denominator.toNat))) := by
  induction weights generalizing initial with
  | nil =>
    change 0 < initial ∧ Fits minInput maxInput (Int.ofNat initial) at safe
    simp only [checkedLcm,foldLcm,List.map_nil,if_pos safe]
  | cons w ws ih =>
    simp only [checkedLcm,List.map_cons,foldLcm]
    rw [if_pos ⟨safe.1,safe.2.1,safe.2.2.1⟩]
    exact ih safe.2.2.2

theorem originalMixtureLcmCompletes {weights : List Weight}
    (wire : ∀ w ∈ weights, WireWeight w)
    (bound : (foldLcm 1 (weights.map (fun w => w.denominator.toNat)) : Int) ≤ maxInput) :
    checkedLcm minInput maxInput 1 weights =
      some (foldLcm 1 (weights.map (fun w => w.denominator.toNat))) :=
  lcmComputedFromPrefixes (lcmPrefixesFromFinalBound (by decide)
    (fun _ hw => wireMixtureWeightFits wire bound hw) bound)

theorem checkedOriginalProfileMixtureLcm {sha source checked}
    (accepted : NativeApplyProfile.check sha source = some checked)
    (bound : (foldLcm 1 (checked.profile.weights.map (fun w =>
      (NativeApplyResult.fraction w.fraction).denominator.toNat)) : Int) ≤ maxInput) :
    checkedLcm minInput maxInput 1
      (checked.profile.weights.map (fun w => (NativeApplyResult.fraction w.fraction).kernelWeight)) =
      some (foldLcm 1 (checked.profile.weights.map (fun w =>
        (NativeApplyResult.fraction w.fraction).denominator.toNat))) := by
  have valid := (NativeApplyProfile.checkedSource accepted).2.2.1
  have wire : ∀ w ∈ checked.profile.weights.map (fun w =>
      (NativeApplyResult.fraction w.fraction).kernelWeight), WireWeight w := by
    intro w hw
    obtain ⟨original,member,rfl⟩ := List.mem_map.mp hw
    exact originalFractionFits (valid.2.2.2.2.1 original member).2
  simpa only [List.map_map,Function.comp_def,Rational.kernelWeight] using
    originalMixtureLcmCompletes wire (by
      simpa only [List.map_map,Function.comp_def,Rational.kernelWeight] using bound)

/- Direct original numeric-domain implication. No draft signed denominator,
identifier grammar, coordinate label or artifact-size premise is introduced. -/
theorem absoluteListSumBound {values : List Int} {bound : Int}
    (items : ∀ value ∈ values, |value| ≤ bound) :
    |values.sum| ≤ (values.length : Int)*bound := by
  induction values with
  | nil => simp
  | cons value values ih =>
    have head := items value (by simp)
    have tail := ih (fun v hv => items v (List.mem_cons_of_mem _ hv))
    have triangle := abs_add_le value values.sum
    simp only [List.sum_cons,List.length_cons,Nat.cast_add,Nat.cast_one]
    exact triangle.trans ((add_le_add head tail).trans_eq (by rw [add_mul,one_mul,add_comm]))

theorem publicSequenceFromItemBounds {limit bound : Int} {values : List Int}
    (positive : 0 ≤ bound) (single : bound ≤ limit)
    (total : (values.length : Int)*bound ≤ limit)
    (items : ∀ value ∈ values, |value| ≤ bound) : PublicSequence limit values := by
  have fits (value : Int) (safe : |value| ≤ bound) : Fits (-limit-1) limit value := by
    have signed := abs_le.mp safe
    constructor <;> omega
  refine ⟨fun value member => fits value (items value member),?_⟩
  intro count _
  have subtotal := absoluteListSumBound (values := values.take count)
    (fun value member => items value (List.mem_of_mem_take member))
  have length : ((values.take count).length : Int) ≤ (values.length : Int) := by
    simp only [List.length_take]
    exact_mod_cast Nat.min_le_right count values.length
  have product := mul_le_mul_of_nonneg_right length positive
  have signed := abs_le.mp (subtotal.trans (product.trans total))
  constructor <;> omega

theorem originalParameterSequences {n : NativeAccumulatorBinding.Numbers} {pairs : List (Int × Int)}
    (native : NativeAccumulatorBinding.NumericValid n)
    (count : pairs.length ≤ n.count)
    (coefficients : ∀ p ∈ pairs, |p.1| ≤ (n.coefficient : Int))
    (quantized : ∀ p ∈ pairs, |p.2| ≤ 32767) :
    PublicSequence (NativeAccumulatorBinding.limit n.accumulatorBits : Int) (pairs.map Prod.fst) ∧
    PublicSequence (NativeAccumulatorBinding.limit n.accumulatorBits : Int) (pairs.map (fun p => p.1*p.2)) := by
  have b := NativeAccumulatorBinding.computedBounds native
  have positiveCount : 0 < n.count := native.2.2.1
  have productNative : n.coefficient*32767 ≤ NativeAccumulatorBinding.limit n.accumulatorBits := by
    have productPositive : n.coefficient*32767 ≤ n.coefficient*32767*n.count := by
      exact Nat.le_mul_of_pos_right _ positiveCount
    have full : n.coefficient*32767*n.count ≤ NativeAccumulatorBinding.limit n.accumulatorBits := by
      simpa only [b.2.1,Nat.mul_comm n.coefficient 32767] using b.2.2.2
    exact productPositive.trans full
  have totalNative : pairs.length*(n.coefficient*32767) ≤ NativeAccumulatorBinding.limit n.accumulatorBits := by
    have full : n.count*(n.coefficient*32767) ≤ NativeAccumulatorBinding.limit n.accumulatorBits := by
      simpa [b.2.1,Nat.mul_assoc,Nat.mul_comm,Nat.mul_left_comm] using b.2.2.2
    exact (Nat.mul_le_mul_right _ count).trans full
  have product : (n.coefficient : Int)*32767 ≤ (NativeAccumulatorBinding.limit n.accumulatorBits : Int) := by
    exact_mod_cast productNative
  have total : (pairs.length : Int)*((n.coefficient : Int)*32767) ≤
      (NativeAccumulatorBinding.limit n.accumulatorBits : Int) := by exact_mod_cast totalNative
  have coefficientNonnegative : (0 : Int) ≤ n.coefficient := Int.natCast_nonneg _
  have coefficientBelow : (n.coefficient : Int) ≤ (n.coefficient : Int)*32767 := by omega
  constructor
  · apply publicSequenceFromItemBounds coefficientNonnegative (coefficientBelow.trans product)
    · simp only [List.length_map]
      exact (mul_le_mul_of_nonneg_left coefficientBelow (Int.natCast_nonneg _)).trans total
    · intro value member
      obtain ⟨p,hp,rfl⟩ := List.mem_map.mp member
      exact coefficients p hp
  · apply publicSequenceFromItemBounds (by positivity) product
    · simpa only [List.length_map] using total
    · intro value member
      obtain ⟨p,hp,rfl⟩ := List.mem_map.mp member
      rw [abs_mul]
      exact mul_le_mul (coefficients p hp) (quantized p hp) (abs_nonneg _) coefficientNonnegative

def originalParameterTerms (source : NativePlanQCorpus.Bound) (domain : NativeReceiptBytes.Bytes)
    (block coordinate : Nat) : Option (List (Int × Int)) :=
  NativeInputProjection.collect (fun row =>
    (NativeAvailableQ.coordinate row.corpus.manifest block coordinate).map
      (fun value => ((row.term.coefficient : Int),value))) (NativePlanQCorpus.inDomain domain source.rows)

theorem originalSourceParameterGuards
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source domain block coordinate pairs}
    (loaded : FamilyInputs.OriginalRowsSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (computed : originalParameterTerms source domain block coordinate = some pairs) :
    PublicSequence (NativeAccumulatorBinding.limit source.plan.accumulator.numbers.accumulatorBits : Int)
      (pairs.map Prod.fst) ∧
    PublicSequence (NativeAccumulatorBinding.limit source.plan.accumulator.numbers.accumulatorBits : Int)
      (pairs.map (fun p => p.1*p.2)) := by
  have sources := FamilyInputs.originalRowsSourceParts loaded
  have coefficients := NativePlanCoefficients.checked sources.1.coefficients
  have countRows : source.rows.length ≤ source.plan.accumulator.numbers.count := by
    have same := congrArg List.length (NativePlanQCorpus.completeRows sources.2).1
    simp only [List.length_map] at same
    rw [same,coefficients.2,NativePlanCoefficients.exactCount]
    exact coefficients.1.2.1
  apply originalParameterSequences coefficients.1.1
  · exact (NativeInputProjection.collectLength computed).le.trans
      ((List.length_filter_le _ _).trans countRows)
  · intro pair member
    obtain ⟨row,selected,read⟩ := FamilyAuthority.collectedValueSource computed member
    have original := List.mem_of_mem_filter selected
    obtain ⟨value,_,same⟩ := Option.map_eq_some_iff.mp read
    cases same
    have coefficientMember : row.term ∈ source.plan.coefficients := by
      rw [← (NativePlanQCorpus.completeRows sources.2).1]
      exact List.mem_map.mpr ⟨row,original,rfl⟩
    rw [coefficients.2] at coefficientMember
    have bounded := NativePlanCoefficients.coefficientBound coefficients.1 coefficientMember
    simpa only [abs_of_nonneg (Int.natCast_nonneg _)] using
      (show (row.term.coefficient : Int) ≤ source.plan.accumulator.numbers.coefficient by exact_mod_cast bounded)
  · intro pair member
    obtain ⟨row,selected,read⟩ := FamilyAuthority.collectedValueSource computed member
    obtain ⟨value,lookup,same⟩ := Option.map_eq_some_iff.mp read
    cases same
    exact FamilyInputs.originalCoordinateRange loaded row (List.mem_of_mem_filter selected) lookup

theorem originalSourceCoefficientsArePublicFormula
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source domain block coordinate pairs}
    (loaded : FamilyInputs.OriginalRowsSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (computed : originalParameterTerms source domain block coordinate = some pairs) :
    pairs.map Prod.fst = (NativePlanQCorpus.inDomain domain source.rows).map (fun row =>
      (row.term.source.weight.numerator : Int) *
        ((source.plan.accumulator.numbers.denominator : Int)/row.term.source.weight.denominator)) := by
  have sources := FamilyInputs.originalRowsSourceParts loaded
  have keys := FamilyInputs.collectedKeys computed (left := fun row : NativePlanQCorpus.Row =>
      (row.term.coefficient : Int)) (right := Prod.fst)
    (fun row pair accepted => by
      obtain ⟨_,_,same⟩ := Option.map_eq_some_iff.mp accepted
      cases same; rfl)
  rw [keys]
  apply List.map_congr_left
  intro row selected
  have original := List.mem_of_mem_filter selected
  have coefficientMember : row.term ∈ source.plan.coefficients := by
    rw [← (NativePlanQCorpus.completeRows sources.2).1]
    exact List.mem_map.mpr ⟨row,original,rfl⟩
  have same := (FamilyInputs.originalCoefficientIdentity sources.1 coefficientMember).2
  exact_mod_cast same

theorem sequenceSafeFromPrefixes {lo hi acc : Int} {values : List Int}
    (items : ∀ v ∈ values, Fits lo hi v)
    (prefixes : ∀ n ≤ values.length, Fits lo hi (acc+(values.take n).sum)) :
    SequenceSafe lo hi acc values := by
  induction values generalizing acc with
  | nil => simpa only [SequenceSafe,List.take_nil,List.sum_nil,add_zero] using prefixes 0 (by simp)
  | cons v vs ih =>
    refine ⟨by simpa using prefixes 0 (by simp),items v List.mem_cons_self,?_⟩
    apply ih (fun x hx => items x (List.mem_cons_of_mem _ hx))
    intro n hn
    simpa only [List.take_succ_cons,List.sum_cons,Int.add_assoc] using prefixes (n+1) (by simpa using hn)

theorem checkedTermsFromPublicSequence {limit : Int} {terms : List (Int × Int)}
    (safe : PublicSequence limit (terms.map (fun p => p.1*p.2))) :
    checkedAccumulate (-limit-1) limit (-limit-1) limit 0 terms = some (exactAccumulate 0 terms) := by
  have recurrence := sequenceSafeFromPrefixes (acc := 0) safe.1 (by simpa only [zero_add] using safe.2)
  apply checkedAccumulateComplete
  have transfer {acc : Int} (h : SequenceSafe (-limit-1) limit acc (terms.map (fun p => p.1*p.2))) :
      AllPrefixesFit (-limit-1) limit (-limit-1) limit acc terms := by
    clear safe recurrence
    induction terms generalizing acc with
    | nil => exact h
    | cons p ps ih => exact ⟨h.1,h.2.1,ih h.2.2⟩
  exact transfer recurrence

theorem originalScalarTerms {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source domain block coordinate rows}
    (loaded : FamilyInputs.OriginalRowsSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (computed : FamilyInputs.originalScalarRows source domain block coordinate = some rows) :
    originalParameterTerms source domain block coordinate = some
      (ParameterKernel.coordinateTerms source.plan.accumulator.numbers.denominator 0 rows) := by
  have sources := FamilyInputs.originalRowsSourceParts loaded
  unfold originalParameterTerms
  apply FamilyAuthority.collectProjection computed
  intro row member scalar selected
  obtain ⟨value,atValue,same⟩ := Option.map_eq_some_iff.mp selected
  cases same
  have coefficientMember : row.term ∈ source.plan.coefficients := by
    rw [← (NativePlanQCorpus.completeRows sources.2).1]
    exact List.mem_map.mpr ⟨row,List.mem_of_mem_filter member,rfl⟩
  have coefficient := (FamilyInputs.originalCoefficientIdentity sources.1 coefficientMember).2
  have formula : (row.term.coefficient : Int) =
      (row.term.source.weight.numerator : Int) * ((source.plan.accumulator.numbers.denominator : Int)/row.term.source.weight.denominator) := by
    exact_mod_cast coefficient
  simp only [atValue,Option.map_some,formula]
  rfl

theorem originalScalarShapes {source domain block coordinate rows}
    (computed : FamilyInputs.originalScalarRows source domain block coordinate = some rows) :
    ∀ row ∈ rows, row.values.length = 1 := by
  intro row member
  obtain ⟨_,_,accepted⟩ := FamilyAuthority.collectedValueSource computed member
  obtain ⟨_,_,same⟩ := Option.map_eq_some_iff.mp accepted
  cases same; rfl

theorem originalScalarParameterAccepts {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source domain block coordinate rows}
    (loaded : FamilyInputs.OriginalRowsSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (computed : FamilyInputs.originalScalarRows source domain block coordinate = some rows) :
    FamilyParameter.publicParameterRows (NativeAccumulatorBinding.limit source.plan.accumulator.numbers.accumulatorBits : Int)
      source.plan.accumulator.numbers.denominator rows =
      some (exactAccumulate 0 (ParameterKernel.coordinateTerms source.plan.accumulator.numbers.denominator 0 rows)) := by
  have terms := originalScalarTerms loaded computed
  have safe := originalSourceParameterGuards loaded terms
  have coefficients := checkedTermsFromPublicSequence (terms :=
    (ParameterKernel.coordinateTerms source.plan.accumulator.numbers.denominator 0 rows).map (fun p => (p.1,1)))
    (by simpa only [List.map_map,Function.comp_def,mul_one] using safe.1)
  have products := checkedTermsFromPublicSequence safe.2
  simp only [FamilyParameter.publicParameterRows,if_pos (originalScalarShapes computed),coefficients,
    bind,Option.bind_some,products]

theorem originalImageParameterAccepts
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source indices
      profile quantum current image domain block coordinate rows}
    (loaded : FamilyInputs.OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (computed : FamilyInputs.readOriginalImage source indices profile quantum current = some image)
    (atIndex : indices[block]? = some coordinate)
    (selected : FamilyInputs.imageRows image (NativeVectorLayout.text domain) block = some rows) :
    FamilyParameter.publicParameterRows (NativeAccumulatorBinding.limit source.source.plan.accumulator.numbers.accumulatorBits : Int)
      source.source.plan.accumulator.numbers.denominator rows =
      some (exactAccumulate 0 (ParameterKernel.coordinateTerms source.source.plan.accumulator.numbers.denominator 0 rows)) := by
  rw [FamilyInputs.originalInputRowsAreSourceRows loaded computed domain atIndex] at selected
  exact originalScalarParameterAccepts (FamilyInputs.originalVectorSourceParts loaded).1 selected

theorem originalImageLimit {source indices profile quantum current image}
    (computed : FamilyInputs.readOriginalImage source indices profile quantum current = some image) :
    image.limit = (NativeAccumulatorBinding.limit source.source.plan.accumulator.numbers.accumulatorBits : Int) := by
  simp only [FamilyInputs.readOriginalImage,bind,Option.bind_eq_some_iff] at computed
  obtain ⟨_,_,_,_,_,_,last⟩ := computed
  cases Option.some.inj last; rfl

section OriginalParameterTotal
variable {source indices profile quantum current vocabulary configured names earlyTrust planningTrust metadata selected}
    (authority : FamilyAuthority.Original source indices profile quantum current vocabulary configured names
      (earlyTrust := earlyTrust) (planningTrust := planningTrust) metadata selected)
    (native : NativeParameterLineage.Edge) (block : Nat) (nativeShardAlias : NativeBinding.Bytes → Option String)

theorem originalParameterProjectionTotal
    {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs vector coordinate dn sn}
    (loaded : FamilyInputs.OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    (computed : FamilyParameter.originalVector source native.certificate.common.domain block = some vector)
    (atCoordinate : indices[block]? = some coordinate)
    (inside : coordinate < vector.first.block.frame.values.length)
    (exactNative : native.certificate.common.leaves = vector.leaves.mergeSort NativePolicyBytes.bytesLT ∧
      native.certificate.common.numerators = vector.values.map (asciiBytes ∘ toString))
    (parents : native.certificate.common.context = source.source.plan.members.edge.certificate.common.context ∧
      native.certificate.common.plan = source.source.plan.members.edge.id ∧
      native.certificate.common.isc = source.source.plan.members.edge.parent.qcId ∧
      native.certificate.common.ec = source.source.plan.members.edge.ec.id ∧
      native.certificate.common.denominator = source.source.plan.accumulator.numbers.denominator)
    (domainAlias : vocabulary.domain (NativeVectorLayout.text native.certificate.common.domain) = some dn)
    (domainConfigured : dn ∈ vocabulary.domains)
    (shardAlias : vocabulary.shard (NativeVectorLayout.shardName vector.first.block.header.ordinal) = some sn)
    (nativeAlias : nativeShardAlias native.certificate.common.shard = some sn)
    (shardConfigured : sn ∈ vocabulary.shards) :
    ∃ p, FamilyParameter.projectOriginal authority native block nativeShardAlias = some p := by
  let rows := vector.slices.map (fun s => VectorShardRepresentation.rowAt coordinate (NativeVectorArithmetic.kernelRow s))
  have imageRows : FamilyInputs.imageRows authority.input.image
      (NativeVectorLayout.text native.certificate.common.domain) block = some rows := by
    rw [FamilyInputs.originalInputRowsAreSourceRows loaded authority.input.computed _ atCoordinate]
    exact FamilyParameter.scalarRowsFromSlices computed inside
  let value := exactAccumulate 0 (ParameterKernel.coordinateTerms source.source.plan.accumulator.numbers.denominator 0 rows)
  have terms : ParameterKernel.coordinateTerms source.source.plan.accumulator.numbers.denominator 0 rows =
      ParameterKernel.coordinateTerms source.source.plan.accumulator.numbers.denominator coordinate
        (vector.slices.map NativeVectorArithmetic.kernelRow) := by
    simp [rows,ParameterKernel.coordinateTerms,VectorShardRepresentation.rowAt,List.map_map,Function.comp_def]
  have nativeValue : vector.values[coordinate]? = some value := by
    dsimp only [value]
    rw [terms]
    exact FamilyParameter.originalVectorCoordinate computed inside
  have arithmetic : FamilyParameter.publicParameterRows authority.input.image.limit native.certificate.common.denominator rows = some value := by
    rw [originalImageLimit authority.input.computed,parents.2.2.2.2]
    exact originalImageParameterAccepts loaded authority.input.computed atCoordinate imageRows
  let p : FamilyParameter.OriginalProjection authority native block nativeShardAlias :=
    ⟨vector,computed,coordinate,atCoordinate,value,nativeValue,exactNative,parents,rows,imageRows,arithmetic,
      dn,domainAlias,domainConfigured,sn,shardAlias,nativeAlias,shardConfigured⟩
  exact ⟨p,FamilyParameter.originalProjectionLoaded authority native block nativeShardAlias p⟩

end OriginalParameterTotal

/- CheckedParameterValue uses a symmetric result bound, while the arithmetic
domain is the asymmetric signed interval. The extra endpoint is required to
represent the native minimum; it is a configuration value, not a new guard. -/
theorem originalParameterResultGuard {source indices profile quantum current vocabulary configured names
    earlyTrust planningTrust metadata selected}
    (authority : FamilyAuthority.Original source indices profile quantum current vocabulary configured names
      (earlyTrust := earlyTrust) (planningTrust := planningTrust) metadata selected)
    {native block nativeShardAlias}
    (p : FamilyParameter.OriginalProjection authority native block nativeShardAlias) :
    p.value = ((ParameterKernel.coordinateTerms native.certificate.common.denominator 0 p.rows).map
      (fun t => t.1*t.2)).sum ∧
      Fits (-(authority.input.image.limit+1)) (authority.input.image.limit+1) p.value := by
  have checked := p.arithmetic
  unfold FamilyParameter.publicParameterRows at checked
  split at checked <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at checked
  obtain ⟨_,_,computed⟩ := checked
  have sound := checkedAccumulateSound _ _ _ _ _ _ _ computed
  constructor
  · simpa only [exactAccumulateIsSum,Int.zero_add] using sound.1
  · have bounds := sound.2.2
    unfold Fits at bounds ⊢
    omega

/- Full APPLY numeric traversal using the original unsigned-denominator
optimizer. The existing mixture kernel is valid because native mixture requires
its final LCM to fit int64. This replaces only the restrictive optimizer adapter. -/
structure OriginalApplyMath (profile : NativeApplyProfile.Profile) (model optimizer : List Int)
    (rows : List ApplyKernel.DomainRow) where
  nonempty : model ≠ []
  optimizerShape : optimizer.length = model.length
  rowShapes : ∀ row ∈ rows, row.values.length = model.length
  weights : rows.map (·.weight) = profile.weights.map (fun w => (NativeApplyResult.fraction w.fraction).kernelWeight)
  plan : ApplyKernel.WeightPlan minInput maxInput (rows.map (·.weight))
  gradients : List Int
  trace : ApplyKernel.GradientTrace minInput maxInput rows plan (List.range model.length) gradients
  values : List ApplyKernel.OptimizerValues
  computed : nativeOptimizerVector profile model optimizer gradients = some values

def checkOriginalApplyMath (profile : NativeApplyProfile.Profile) (model optimizer : List Int)
    (rows : List ApplyKernel.DomainRow) : Option (OriginalApplyMath profile model optimizer rows) := do
  if shape : model ≠ [] ∧ optimizer.length = model.length ∧
      (∀ row ∈ rows, row.values.length = model.length) ∧
      rows.map (·.weight) = profile.weights.map (fun w => (NativeApplyResult.fraction w.fraction).kernelWeight) then
    let plan ← ApplyKernel.deriveWeightPlan minInput maxInput (rows.map (·.weight))
    let gradients ← ApplyKernel.deriveGradients minInput maxInput rows plan (List.range model.length)
    match computed : nativeOptimizerVector profile model optimizer gradients.val with
    | none => none
    | some values => some ⟨shape.1,shape.2.1,shape.2.2.1,shape.2.2.2,plan,gradients.val,gradients.property,values,computed⟩
  else none

def OriginalApplyMath.nextModel {profile model optimizer rows} (p : OriginalApplyMath profile model optimizer rows) : List Int :=
  p.values.map ApplyKernel.OptimizerValues.nextModel

def OriginalApplyMath.nextOptimizer {profile model optimizer rows} (p : OriginalApplyMath profile model optimizer rows) : List Int :=
  p.values.map ApplyKernel.OptimizerValues.nextOptimizer

theorem originalApplyMathTotal {profile model optimizer rows} (p : OriginalApplyMath profile model optimizer rows) :
    checkOriginalApplyMath profile model optimizer rows = some p := by
  unfold checkOriginalApplyMath
  rw [dif_pos ⟨p.nonempty,p.optimizerShape,p.rowShapes,p.weights⟩,derivePlanComplete p.plan]
  simp only [bind,Option.bind,deriveGradientsComplete p.trace]
  split
  · rename_i absent; simp [p.computed] at absent
  · rename_i values computed
    have same := Option.some.inj (computed.symm.trans p.computed)
    subst values; rfl

theorem originalApplyMathShape {profile model optimizer rows} (p : OriginalApplyMath profile model optimizer rows) :
    p.nextModel.length = model.length ∧ p.nextOptimizer.length = model.length := by
  have shape := nativeVectorShape p.computed
  simpa only [OriginalApplyMath.nextModel,OriginalApplyMath.nextOptimizer,List.length_map] using
    And.intro shape.1.symm shape.1.symm

theorem originalApplyMathCoordinate {profile model optimizer rows} (p : OriginalApplyMath profile model optimizer rows)
    {index : Nat} {value} (atValue : p.values[index]? = some value) :
    ∃ theta momentum gradient total terms,
      model[index]? = some theta ∧ optimizer[index]? = some momentum ∧ p.gradients[index]? = some gradient ∧
      ApplyKernel.ColumnTerms index rows terms ∧
      ApplyKernel.checkedMix minInput maxInput p.plan.denominator 0 terms = some total ∧
      gradient = round total p.plan.denominator ∧
      value = ApplyKernel.optimizerValues theta momentum gradient
        (NativeApplyResult.fraction profile.learning).kernelWeight
        (NativeApplyResult.fraction profile.momentum).kernelWeight
        (NativeApplyResult.fraction profile.decay).kernelWeight := by
  obtain ⟨theta,momentum,gradient,hm,ho,hg,computed⟩ := nativeVectorAt p.computed atValue
  have inside : index < model.length := by
    rw [(nativeVectorShape p.computed).1]
    exact (List.getElem?_eq_some_iff.mp atValue).1
  obtain ⟨g,total,terms,atHead,column,mix,rounded,_⟩ :=
    VectorShardRepresentation.scalarMixtureIsCoordinate p.trace index index (by simp [inside])
  have equal := Option.some.inj (atHead.symm.trans hg)
  exact ⟨theta,momentum,gradient,total,terms,hm,ho,hg,column,mix,
    (rounded.trans equal).symm,(nativeOptimizerSound computed).1⟩

theorem originalApplyCoordinatePublicGuards {profile model optimizer rows}
    (p : OriginalApplyMath profile model optimizer rows) {index : Nat} {value}
    (atValue : p.values[index]? = some value) (limit : Int)
    (lower : -limit-1 ≤ minInput) (upper : maxInput ≤ limit) :
    ∃ theta momentum gradient total terms,
      model[index]? = some theta ∧ optimizer[index]? = some momentum ∧ p.gradients[index]? = some gradient ∧
      ColumnTerms index rows terms ∧
      PublicSequence limit (mixtureProducts p.plan.denominator terms) ∧
      (∀ term ∈ terms, Fits (-limit-1) limit (term.value*term.weight.numerator)) ∧
      Fits (-limit-1) limit p.plan.denominator ∧
      gradient = round total p.plan.denominator ∧ Fits (-limit-1) limit gradient ∧
      (∀ v ∈ PublicOptimizerValues theta momentum gradient
        (NativeApplyResult.fraction profile.learning).kernelWeight
        (NativeApplyResult.fraction profile.momentum).kernelWeight
        (NativeApplyResult.fraction profile.decay).kernelWeight, Fits (-limit-1) limit v) ∧
      value = optimizerValues theta momentum gradient
        (NativeApplyResult.fraction profile.learning).kernelWeight
        (NativeApplyResult.fraction profile.momentum).kernelWeight
        (NativeApplyResult.fraction profile.decay).kernelWeight := by
  obtain ⟨theta,momentum,g,hm,ho,hg,computed⟩ := nativeVectorAt p.computed atValue
  obtain ⟨theta',momentum',g',total,terms,hm',ho',hg',column,mix,rounded,result⟩ := originalApplyMathCoordinate p atValue
  have tm := Option.some.inj (hm'.symm.trans hm)
  have om := Option.some.inj (ho'.symm.trans ho)
  have gg := Option.some.inj (hg'.symm.trans hg)
  have checked := checkedMixSound _ _ _ _ _ _ (mixWiden lower upper mix)
  have sequence := mixtureSequence checked.2.1
  have optimizer := nativeOptimizerPublicGuard computed limit lower upper
  exact ⟨theta,momentum,g,total,terms,hm,ho,hg,column,publicSequenceFromRecurrence sequence.1,sequence.2,
    fitsWiden lower upper (weightPlanLeast _ _ _ p.plan).2.1,by simpa only [gg] using rounded,
    optimizer.1,optimizer.2.1,by simpa only [tm,om,gg] using result⟩

end DeltaReduce.FamilyGuards
