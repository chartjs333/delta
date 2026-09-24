import DeltaReduce.ParameterKernel

/-! Checked APPLY arithmetic sublayer. This is not nativeApplyResultUnique:
canonical domain/model/optimizer extraction and cross-store result binding are
separate obligations. Every intermediate is checked at the caller's fixed width.
The native amendment instantiates INT64, even when PARAMETER uses INT128. -/
namespace DeltaReduce.ApplyKernel
open DeltaReduce

structure Weight where
  numerator : Int
  denominator : Int
  deriving DecidableEq, Repr

def foldLcm (initial : Nat) : List Nat → Nat
  | [] => initial
  | value :: values => foldLcm (Nat.lcm initial value) values

theorem foldLcmSpec (initial : Nat) (values : List Nat)
    (positive : 0 < initial) (allPositive : ∀ value ∈ values, 0 < value) :
    0 < foldLcm initial values ∧ initial ∣ foldLcm initial values ∧
    (∀ value ∈ values, value ∣ foldLcm initial values) ∧
    (∀ multiple, initial ∣ multiple → (∀ value ∈ values, value ∣ multiple) →
      foldLcm initial values ∣ multiple) := by
  induction values generalizing initial with
  | nil => exact ⟨positive, Nat.dvd_refl initial, by simp, fun _ h _ => h⟩
  | cons value values ih =>
      have headPositive := allPositive value (by simp)
      have tailPositive : ∀ value ∈ values, 0 < value := fun v h => allPositive v (by simp [h])
      obtain ⟨pos, factor, factors, least⟩ := ih (Nat.lcm initial value)
        (Nat.lcm_pos positive headPositive) tailPositive
      refine ⟨pos, Nat.dvd_trans (Nat.dvd_lcm_left initial value) factor, ?_, ?_⟩
      · intro v member
        rcases List.mem_cons.mp member with equal | member
        · subst v; exact Nat.dvd_trans (Nat.dvd_lcm_right initial value) factor
        · exact factors v member
      · intro multiple start rest
        exact least multiple (Nat.lcm_dvd start (rest value (by simp)))
          (fun v member => rest v (by simp [member]))

def LcmPrefixesSafe (lo hi : Int) (initial : Nat) : List Weight → Prop
  | [] => 0 < initial ∧ Fits lo hi (Int.ofNat initial)
  | weight :: weights =>
      0 < initial ∧ Fits lo hi (Int.ofNat initial) ∧
      ParameterKernel.ReducedNonnegative lo hi weight.numerator weight.denominator ∧
      LcmPrefixesSafe lo hi (Nat.lcm initial weight.denominator.toNat) weights

def checkedLcm (lo hi : Int) (initial : Nat) : List Weight → Option Nat
  | [] => if 0 < initial ∧ Fits lo hi (Int.ofNat initial) then some initial else none
  | weight :: weights =>
      if 0 < initial ∧ Fits lo hi (Int.ofNat initial) ∧
          ParameterKernel.ReducedNonnegative lo hi weight.numerator weight.denominator then
        checkedLcm lo hi (Nat.lcm initial weight.denominator.toNat) weights
      else none

theorem checkedLcmSound (lo hi : Int) (initial result : Nat) (weights : List Weight)
    (accepted : checkedLcm lo hi initial weights = some result) :
    result = foldLcm initial (weights.map (fun w => w.denominator.toNat)) ∧
      LcmPrefixesSafe lo hi initial weights ∧ 0 < result ∧ Fits lo hi (Int.ofNat result) := by
  induction weights generalizing initial with
  | nil =>
      simp only [checkedLcm] at accepted
      split at accepted
      · rename_i bounds; cases Option.some.inj accepted
        exact ⟨rfl, bounds, bounds⟩
      · contradiction
  | cons weight weights ih =>
      simp only [checkedLcm] at accepted
      split at accepted
      · rename_i bounds
        obtain ⟨same, tail, pos, range⟩ := ih _ accepted
        exact ⟨same, ⟨bounds.1, bounds.2.1, bounds.2.2, tail⟩, pos, range⟩
      · contradiction

theorem lcmPrefixesWeights (lo hi : Int) (initial : Nat) (weights : List Weight)
    (safe : LcmPrefixesSafe lo hi initial weights) :
    ∀ weight ∈ weights,
      ParameterKernel.ReducedNonnegative lo hi weight.numerator weight.denominator := by
  induction weights generalizing initial with
  | nil => simp
  | cons weight weights ih =>
      intro w member
      rcases List.mem_cons.mp member with equal | member
      · subst w; exact safe.2.2.1
      · exact ih _ safe.2.2.2 w member

structure WeightPlan (lo hi : Int) (weights : List Weight) where
  denominator : Nat
  computed : checkedLcm lo hi 1 weights = some denominator
  nonempty : weights ≠ []
  normalized : (weights.map (fun w => w.numerator * (Int.ofNat denominator / w.denominator))).sum =
    Int.ofNat denominator

def deriveWeightPlan (lo hi : Int) (weights : List Weight) : Option (WeightPlan lo hi weights) := do
  match computed : checkedLcm lo hi 1 weights with
  | none => none
  | some denominator =>
      if valid : weights ≠ [] ∧
          (weights.map (fun w => w.numerator * (Int.ofNat denominator / w.denominator))).sum =
            Int.ofNat denominator then
        some ⟨denominator, computed, valid.1, valid.2⟩
      else none

theorem weightPlanLeast (lo hi : Int) (weights : List Weight) (plan : WeightPlan lo hi weights) :
    0 < plan.denominator ∧ Fits lo hi (Int.ofNat plan.denominator) ∧
    (∀ weight ∈ weights, weight.denominator.toNat ∣ plan.denominator) ∧
    (∀ multiple, (∀ weight ∈ weights, weight.denominator.toNat ∣ multiple) →
      plan.denominator ∣ multiple) := by
  obtain ⟨same, safe, positive, bounded⟩ := checkedLcmSound lo hi 1 plan.denominator weights plan.computed
  have weightSafe := lcmPrefixesWeights lo hi 1 weights safe
  have pos : ∀ value ∈ weights.map (fun w => w.denominator.toNat), 0 < value := by
    intro value member
    obtain ⟨weight, weightMember, rfl⟩ := List.mem_map.mp member
    have h := (weightSafe weight weightMember).2.2.1
    omega
  have spec := foldLcmSpec 1 (weights.map (fun w => w.denominator.toNat)) (by decide) pos
  refine ⟨positive, bounded, ?_, ?_⟩
  · intro weight member; rw [same]
    exact spec.2.2.1 _ (List.mem_map.mpr ⟨weight, member, rfl⟩)
  · intro multiple factors; rw [same]
    exact spec.2.2.2 multiple (Nat.one_dvd _) (by
      intro value member; obtain ⟨weight, weightMember, rfl⟩ := List.mem_map.mp member
      exact factors weight weightMember)

structure MixTerm where
  weight : Weight
  value : Int
  deriving DecidableEq, Repr

def exactMix (denominator acc : Int) : List MixTerm → Int
  | [] => acc
  | term :: terms => exactMix denominator
      (acc + (term.value * term.weight.numerator) * (denominator / term.weight.denominator)) terms

def MixStepSafe (lo hi denominator acc : Int) (term : MixTerm) : Prop :=
  ParameterKernel.ReducedNonnegative lo hi term.weight.numerator term.weight.denominator ∧
  0 < denominator ∧ Fits lo hi denominator ∧ denominator % term.weight.denominator = 0 ∧
  Fits lo hi acc ∧ Fits lo hi term.value ∧ Fits lo hi (term.value * term.weight.numerator) ∧
  Fits lo hi ((term.value * term.weight.numerator) * (denominator / term.weight.denominator)) ∧
  Fits lo hi (acc + (term.value * term.weight.numerator) * (denominator / term.weight.denominator))

instance (lo hi denominator acc : Int) (term : MixTerm) :
    Decidable (MixStepSafe lo hi denominator acc term) := by unfold MixStepSafe; infer_instance

def MixPrefixesSafe (lo hi denominator acc : Int) : List MixTerm → Prop
  | [] => Fits lo hi acc
  | term :: terms => MixStepSafe lo hi denominator acc term ∧
      MixPrefixesSafe lo hi denominator
        (acc + (term.value * term.weight.numerator) * (denominator / term.weight.denominator)) terms

def checkedMix (lo hi denominator acc : Int) : List MixTerm → Option Int
  | [] => if Fits lo hi acc then some acc else none
  | term :: terms =>
      if MixStepSafe lo hi denominator acc term then
        checkedMix lo hi denominator
          (acc + (term.value * term.weight.numerator) * (denominator / term.weight.denominator)) terms
      else none

theorem checkedMixSound (lo hi denominator acc result : Int) (terms : List MixTerm)
    (accepted : checkedMix lo hi denominator acc terms = some result) :
    result = exactMix denominator acc terms ∧ MixPrefixesSafe lo hi denominator acc terms ∧
      Fits lo hi result := by
  induction terms generalizing acc with
  | nil =>
      simp only [checkedMix] at accepted
      split at accepted
      · rename_i bound; cases Option.some.inj accepted; exact ⟨rfl, bound, bound⟩
      · contradiction
  | cons term terms ih =>
      simp only [checkedMix] at accepted
      split at accepted
      · rename_i safe
        obtain ⟨same, tail, bounded⟩ := ih _ accepted
        exact ⟨same, ⟨safe, tail⟩, bounded⟩
      · contradiction

theorem checkedMixComplete (lo hi denominator acc : Int) (terms : List MixTerm)
    (safe : MixPrefixesSafe lo hi denominator acc terms) :
    checkedMix lo hi denominator acc terms = some (exactMix denominator acc terms) := by
  induction terms generalizing acc with
  | nil =>
      change Fits lo hi acc at safe
      simp only [checkedMix, if_pos safe, exactMix]
  | cons term terms ih =>
      simp only [checkedMix, if_pos safe.1, exactMix]
      exact ih _ safe.2

theorem checkedMixRejectsExactly (lo hi denominator acc : Int) (terms : List MixTerm) :
    checkedMix lo hi denominator acc terms = none ↔ ¬ MixPrefixesSafe lo hi denominator acc terms := by
  constructor
  · intro rejected safe
    have accepted := checkedMixComplete lo hi denominator acc terms safe
    simp [rejected] at accepted
  · intro notSafe
    cases outcome : checkedMix lo hi denominator acc terms with
    | none => rfl
    | some result => exact False.elim (notSafe (checkedMixSound lo hi denominator acc result terms outcome).2.1)

structure OptimizerValues where
  momentumProduct : Int
  oldMomentumScaled : Int
  nextOptimizer : Int
  nextMomentumProduct : Int
  nextMomentumScaled : Int
  direction : Int
  decayProduct : Int
  decay : Int
  directionWithDecay : Int
  stepProduct : Int
  step : Int
  nextModel : Int
  deriving DecidableEq, Repr

def optimizerValues (theta momentum gradient : Int) (lr mu wd : Weight) : OptimizerValues :=
  let mp := momentum * mu.numerator
  let ms := round mp mu.denominator
  let next := ms + gradient
  let np := next * mu.numerator
  let ns := round np mu.denominator
  let dir := ns + gradient
  let dp := theta * wd.numerator
  let decay := round dp wd.denominator
  let dirDecay := dir + decay
  let sp := dirDecay * lr.numerator
  let step := round sp lr.denominator
  ⟨mp, ms, next, np, ns, dir, dp, decay, dirDecay, sp, step, theta - step⟩

def OptimizerValues.intermediates (v : OptimizerValues) : List Int :=
  [v.momentumProduct, v.oldMomentumScaled, v.nextOptimizer, v.nextMomentumProduct,
    v.nextMomentumScaled, v.direction, v.decayProduct, v.decay, v.directionWithDecay,
    v.stepProduct, v.step, v.nextModel]

def OptimizerSafe (lo hi theta momentum gradient : Int) (lr mu wd : Weight) : Prop :=
  (∀ coefficient ∈ [lr, mu, wd],
    ParameterKernel.ReducedNonnegative lo hi coefficient.numerator coefficient.denominator) ∧
  (∀ value ∈ [theta, momentum, gradient], Fits lo hi value) ∧
  (∀ value ∈ (optimizerValues theta momentum gradient lr mu wd).intermediates, Fits lo hi value)

instance (lo hi theta momentum gradient : Int) (lr mu wd : Weight) :
    Decidable (OptimizerSafe lo hi theta momentum gradient lr mu wd) := by unfold OptimizerSafe; infer_instance

def checkedOptimizer (lo hi theta momentum gradient : Int) (lr mu wd : Weight) :
    Option (Int × Int) :=
  if OptimizerSafe lo hi theta momentum gradient lr mu wd then
    let v := optimizerValues theta momentum gradient lr mu wd
    some (v.nextModel, v.nextOptimizer)
  else none

theorem checkedOptimizerSound (lo hi theta momentum gradient : Int) (lr mu wd : Weight)
    (result : Int × Int)
    (accepted : checkedOptimizer lo hi theta momentum gradient lr mu wd = some result) :
    OptimizerSafe lo hi theta momentum gradient lr mu wd ∧
    result = ((optimizerValues theta momentum gradient lr mu wd).nextModel,
      (optimizerValues theta momentum gradient lr mu wd).nextOptimizer) := by
  unfold checkedOptimizer at accepted
  split at accepted
  · rename_i safe; exact ⟨safe, (Option.some.inj accepted).symm⟩
  · contradiction

theorem checkedOptimizerRejectsExactly (lo hi theta momentum gradient : Int) (lr mu wd : Weight) :
    checkedOptimizer lo hi theta momentum gradient lr mu wd = none ↔
      ¬ OptimizerSafe lo hi theta momentum gradient lr mu wd := by
  simp only [checkedOptimizer]
  split <;> simp_all

inductive OptimizerTrace (lo hi : Int) (lr mu wd : Weight) :
    List Int → List Int → List Int → List Int → List Int → Prop where
  | nil : OptimizerTrace lo hi lr mu wd [] [] [] [] []
  | cons {theta momentum gradient thetas momenta gradients nextModels nextOptimizers}
      (safe : OptimizerSafe lo hi theta momentum gradient lr mu wd)
      (tail : OptimizerTrace lo hi lr mu wd thetas momenta gradients nextModels nextOptimizers) :
      OptimizerTrace lo hi lr mu wd (theta :: thetas) (momentum :: momenta) (gradient :: gradients)
        ((optimizerValues theta momentum gradient lr mu wd).nextModel :: nextModels)
        ((optimizerValues theta momentum gradient lr mu wd).nextOptimizer :: nextOptimizers)

def checkedOptimizerVectors (lo hi : Int) (lr mu wd : Weight) :
    List Int → List Int → List Int → Option (List Int × List Int)
  | [], [], [] => some ([], [])
  | theta :: thetas, momentum :: momenta, gradient :: gradients => do
      let value ← checkedOptimizer lo hi theta momentum gradient lr mu wd
      let tail ← checkedOptimizerVectors lo hi lr mu wd thetas momenta gradients
      some (value.1 :: tail.1, value.2 :: tail.2)
  | _, _, _ => none

theorem checkedOptimizerVectorsSound (lo hi : Int) (lr mu wd : Weight)
    (model momentum gradient nextModel nextOptimizer : List Int)
    (accepted : checkedOptimizerVectors lo hi lr mu wd model momentum gradient =
      some (nextModel, nextOptimizer)) :
    OptimizerTrace lo hi lr mu wd model momentum gradient nextModel nextOptimizer := by
  induction model generalizing momentum gradient nextModel nextOptimizer with
  | nil =>
      cases momentum with
      | nil =>
          cases gradient with
          | nil =>
              simp only [checkedOptimizerVectors] at accepted
              cases Option.some.inj accepted
              exact .nil
          | cons g gs => simp [checkedOptimizerVectors] at accepted
      | cons m ms => cases gradient <;> simp [checkedOptimizerVectors] at accepted
  | cons theta thetas ih =>
      cases momentum with
      | nil => simp [checkedOptimizerVectors] at accepted
      | cons m ms =>
          cases gradient with
          | nil => simp [checkedOptimizerVectors] at accepted
          | cons g gs =>
              simp only [checkedOptimizerVectors] at accepted
              cases step : checkedOptimizer lo hi theta m g lr mu wd with
              | none => simp [step] at accepted
              | some value =>
                  cases tail : checkedOptimizerVectors lo hi lr mu wd thetas ms gs with
                  | none => simp [step, tail] at accepted
                  | some values =>
                      simp only [step, tail] at accepted
                      have eq := Option.some.inj accepted
                      obtain ⟨safe, exactValue⟩ := checkedOptimizerSound lo hi theta m g lr mu wd value step
                      cases values with
                      | mk models optimizers =>
                          cases eq
                          rw [exactValue]
                          exact .cons safe (ih ms gs models optimizers tail)

theorem optimizerTraceShape {lo hi lr mu wd model momentum gradient nextModel nextOptimizer}
    (trace : OptimizerTrace lo hi lr mu wd model momentum gradient nextModel nextOptimizer) :
    momentum.length = model.length ∧ gradient.length = model.length ∧
      nextModel.length = model.length ∧ nextOptimizer.length = model.length := by
  induction trace with
  | nil => exact ⟨rfl, rfl, rfl, rfl⟩
  | cons safe tail ih =>
      exact ⟨congrArg (· + 1) ih.1, congrArg (· + 1) ih.2.1,
        congrArg (· + 1) ih.2.2.1, congrArg (· + 1) ih.2.2.2⟩

theorem optimizerTraceBounds {lo hi lr mu wd model momentum gradient nextModel nextOptimizer}
    (trace : OptimizerTrace lo hi lr mu wd model momentum gradient nextModel nextOptimizer) :
    (∀ value ∈ nextModel, Fits lo hi value) ∧
      (∀ value ∈ nextOptimizer, Fits lo hi value) := by
  induction trace with
  | nil => exact ⟨by simp, by simp⟩
  | cons safe tail ih =>
      constructor
      · intro value member
        rcases List.mem_cons.mp member with equal | member
        · subst value; exact safe.2.2 _ (by simp [OptimizerValues.intermediates])
        · exact ih.1 value member
      · intro value member
        rcases List.mem_cons.mp member with equal | member
        · subst value; exact safe.2.2 _ (by simp [OptimizerValues.intermediates])
        · exact ih.2 value member

end DeltaReduce.ApplyKernel

namespace DeltaReduce.ApplyKernel
open DeltaReduce

structure DomainRow where
  weight : Weight
  values : List Int
  deriving DecidableEq, Repr

inductive ColumnTerms (coordinate : Nat) : List DomainRow → List MixTerm → Prop where
  | nil : ColumnTerms coordinate [] []
  | cons {row rows value terms} (present : row.values[coordinate]? = some value)
      (tail : ColumnTerms coordinate rows terms) :
      ColumnTerms coordinate (row :: rows) (⟨row.weight, value⟩ :: terms)

def extractColumn (rows : List DomainRow) (coordinate : Nat) :
    Option {terms : List MixTerm // ColumnTerms coordinate rows terms} :=
  match rows with
  | [] => some ⟨[], .nil⟩
  | row :: rows =>
      match found : row.values[coordinate]? with
      | none => none
      | some value => do
          let tail ← extractColumn rows coordinate
          some ⟨⟨row.weight, value⟩ :: tail.val, .cons found tail.property⟩

def mathematicalColumn (rows : List DomainRow) (coordinate : Nat) : List MixTerm :=
  rows.map (fun row => ⟨row.weight, row.values[coordinate]?.getD 0⟩)

theorem columnTermsExact {coordinate rows terms} (bound : ColumnTerms coordinate rows terms) :
    terms = mathematicalColumn rows coordinate ∧ terms.map (·.weight) = rows.map (·.weight) := by
  induction bound with
  | nil => exact ⟨rfl, rfl⟩
  | @cons row rows value terms present tail ih =>
      exact ⟨by simp [mathematicalColumn, present, ih.1], by simp [ih.2]⟩

theorem columnTermsPresent {coordinate rows terms} (bound : ColumnTerms coordinate rows terms) :
    ∀ row ∈ rows, ∃ value, row.values[coordinate]? = some value := by
  induction bound with
  | nil => simp
  | cons present tail ih =>
      intro row member
      rcases List.mem_cons.mp member with equal | member
      · subst row; exact ⟨_, present⟩
      · exact ih row member

structure DerivedGradient (lo hi : Int) (rows : List DomainRow)
    (plan : WeightPlan lo hi (rows.map (·.weight))) (coordinate : Nat) where
  terms : List MixTerm
  column : ColumnTerms coordinate rows terms
  total : Int
  computed : checkedMix lo hi (Int.ofNat plan.denominator) 0 terms = some total
  output : Fits lo hi (round total (Int.ofNat plan.denominator))

def DerivedGradient.value {lo hi rows plan coordinate}
    (result : DerivedGradient lo hi rows plan coordinate) : Int :=
  round result.total (Int.ofNat plan.denominator)

def deriveGradient (lo hi : Int) (rows : List DomainRow)
    (plan : WeightPlan lo hi (rows.map (·.weight))) (coordinate : Nat) :
    Option (DerivedGradient lo hi rows plan coordinate) := do
  let column ← extractColumn rows coordinate
  match computed : checkedMix lo hi (Int.ofNat plan.denominator) 0 column.val with
  | none => none
  | some total =>
      if output : Fits lo hi (round total (Int.ofNat plan.denominator)) then
        some ⟨column.val, column.property, total, computed, output⟩
      else none

theorem derivedGradientSound {lo hi rows plan coordinate}
    (result : DerivedGradient lo hi rows plan coordinate) :
    result.value = round (exactMix (Int.ofNat plan.denominator) 0 (mathematicalColumn rows coordinate))
      (Int.ofNat plan.denominator) ∧
    MixPrefixesSafe lo hi (Int.ofNat plan.denominator) 0 result.terms ∧
    Fits lo hi result.value ∧
    (∀ row ∈ rows, ∃ value, row.values[coordinate]? = some value) := by
  obtain ⟨same, safe, _⟩ := checkedMixSound lo hi (Int.ofNat plan.denominator)
    0 result.total result.terms result.computed
  obtain ⟨column, _⟩ := columnTermsExact result.column
  refine ⟨?_, safe, result.output, columnTermsPresent result.column⟩
  simp only [DerivedGradient.value, same, column]

inductive GradientTrace (lo hi : Int) (rows : List DomainRow)
    (plan : WeightPlan lo hi (rows.map (·.weight))) : List Nat → List Int → Prop where
  | nil : GradientTrace lo hi rows plan [] []
  | cons {coordinate coordinates values} (head : DerivedGradient lo hi rows plan coordinate)
      (tail : GradientTrace lo hi rows plan coordinates values) :
      GradientTrace lo hi rows plan (coordinate :: coordinates) (head.value :: values)

def deriveGradients (lo hi : Int) (rows : List DomainRow)
    (plan : WeightPlan lo hi (rows.map (·.weight))) (coordinates : List Nat) :
    Option {values : List Int // GradientTrace lo hi rows plan coordinates values} :=
  match coordinates with
  | [] => some ⟨[], .nil⟩
  | coordinate :: coordinates => do
      let value ← deriveGradient lo hi rows plan coordinate
      let tail ← deriveGradients lo hi rows plan coordinates
      some ⟨value.value :: tail.val, .cons value tail.property⟩

def mathematicalGradients (denominator : Nat) (rows : List DomainRow) (coordinates : List Nat) : List Int :=
  coordinates.map (fun coordinate => round
    (exactMix (Int.ofNat denominator) 0 (mathematicalColumn rows coordinate)) (Int.ofNat denominator))

theorem gradientTraceExact {lo hi rows plan coordinates values}
    (trace : GradientTrace lo hi rows plan coordinates values) :
    values = mathematicalGradients plan.denominator rows coordinates ∧
      values.length = coordinates.length ∧ (∀ value ∈ values, Fits lo hi value) := by
  induction trace with
  | nil => exact ⟨rfl, rfl, by simp⟩
  | cons head tail ih =>
      have sound := derivedGradientSound head
      refine ⟨by simp only [mathematicalGradients, List.map_cons, sound.1, ih.1],
        congrArg (· + 1) ih.2.1, ?_⟩
      intro value member
      rcases List.mem_cons.mp member with equal | member
      · subst value; exact sound.2.2.1
      · exact ih.2.2 value member

structure ApplyComputation (lo hi : Int) (model optimizer : List Int)
    (rows : List DomainRow) (lr mu wd : Weight) where
  nonempty : model ≠ []
  optimizerShape : optimizer.length = model.length
  rowShapes : ∀ row ∈ rows, row.values.length = model.length
  plan : WeightPlan lo hi (rows.map (·.weight))
  gradients : List Int
  gradientTrace : GradientTrace lo hi rows plan (List.range model.length) gradients
  nextModel : List Int
  nextOptimizer : List Int
  optimizerTrace : OptimizerTrace lo hi lr mu wd model optimizer gradients nextModel nextOptimizer

def deriveApply (lo hi : Int) (model optimizer : List Int) (rows : List DomainRow)
    (lr mu wd : Weight) : Option (ApplyComputation lo hi model optimizer rows lr mu wd) := do
  if shapes : model ≠ [] ∧ optimizer.length = model.length ∧
      ∀ row ∈ rows, row.values.length = model.length then
    let plan ← deriveWeightPlan lo hi (rows.map (·.weight))
    let gradients ← deriveGradients lo hi rows plan (List.range model.length)
    match computed : checkedOptimizerVectors lo hi lr mu wd model optimizer gradients.val with
    | none => none
    | some (nextModel, nextOptimizer) =>
        some ⟨shapes.1, shapes.2.1, shapes.2.2, plan, gradients.val, gradients.property,
          nextModel, nextOptimizer, checkedOptimizerVectorsSound lo hi lr mu wd
            model optimizer gradients.val nextModel nextOptimizer computed⟩
  else none

theorem optimizerTraceUnique {lo hi lr mu wd model optimizer gradients leftModel leftOptimizer
    rightModel rightOptimizer}
    (left : OptimizerTrace lo hi lr mu wd model optimizer gradients leftModel leftOptimizer)
    (right : OptimizerTrace lo hi lr mu wd model optimizer gradients rightModel rightOptimizer) :
    leftModel = rightModel ∧ leftOptimizer = rightOptimizer := by
  induction left generalizing rightModel rightOptimizer with
  | nil => cases right; exact ⟨rfl, rfl⟩
  | cons safe tail ih =>
      cases right with
      | cons otherSafe otherTail =>
          obtain ⟨modelEq, optimizerEq⟩ := ih otherTail
          exact ⟨congrArg (_ :: ·) modelEq, congrArg (_ :: ·) optimizerEq⟩

/-- Independent checked derivations from the same mathematical inputs agree;
native authority/graph-to-row identity must still be proved separately. -/
theorem applyComputationUnique {lo hi model optimizer rows lr mu wd}
    (left right : ApplyComputation lo hi model optimizer rows lr mu wd) :
    left.plan.denominator = right.plan.denominator ∧ left.gradients = right.gradients ∧
    left.nextModel = right.nextModel ∧ left.nextOptimizer = right.nextOptimizer := by
  have leftDen := (checkedLcmSound lo hi 1 _ _ left.plan.computed).1
  have rightDen := (checkedLcmSound lo hi 1 _ _ right.plan.computed).1
  have denom := leftDen.trans rightDen.symm
  have leftGrad := (gradientTraceExact left.gradientTrace).1
  have rightGrad := (gradientTraceExact right.gradientTrace).1
  have gradients : left.gradients = right.gradients := by rw [leftGrad, rightGrad, denom]
  have rightTrace := right.optimizerTrace
  rw [← gradients] at rightTrace
  exact ⟨denom, gradients, optimizerTraceUnique left.optimizerTrace rightTrace⟩

theorem applyComputationShapeAndBounds {lo hi model optimizer rows lr mu wd}
    (result : ApplyComputation lo hi model optimizer rows lr mu wd) :
    result.gradients.length = model.length ∧
    result.nextModel.length = model.length ∧ result.nextOptimizer.length = model.length ∧
    (∀ value ∈ result.gradients, Fits lo hi value) ∧
    (∀ value ∈ result.nextModel, Fits lo hi value) ∧
    (∀ value ∈ result.nextOptimizer, Fits lo hi value) := by
  have gradient := gradientTraceExact result.gradientTrace
  have shape := optimizerTraceShape result.optimizerTrace
  exact ⟨by simpa using gradient.2.1, shape.2.2.1, shape.2.2.2,
    gradient.2.2, optimizerTraceBounds result.optimizerTrace⟩

end DeltaReduce.ApplyKernel
