import DeltaReduce.ArithmeticKernel

/-!
PO-AB1 arithmetic sublayer, not the complete nativeParameterConversionSound
obligation. Inputs here are ordered mathematical rows, not decoded artifacts.
The native graph/eligibility/commitment/schema binding must instantiate this
layer separately. No caller-provided coefficient or expected result is trusted.
-/
namespace DeltaReduce.ParameterKernel
open DeltaReduce

structure Row where
  numerator : Int
  denominator : Int
  values : List Int
  deriving DecidableEq, Repr

def ReducedNonnegative (inputLo inputHi a b : Int) : Prop :=
  Fits inputLo inputHi a ∧ 0 ≤ a ∧ 0 < b ∧ b ≤ inputHi ∧ Int.gcd a b = 1

instance (inputLo inputHi a b : Int) : Decidable (ReducedNonnegative inputLo inputHi a b) :=
  inferInstanceAs (Decidable (Fits inputLo inputHi a ∧ 0 ≤ a ∧ 0 < b ∧
    b ≤ inputHi ∧ Int.gcd a b = 1))

def CoefficientValid (lo hi inputLo inputHi denominator a b : Int) : Prop :=
  ReducedNonnegative inputLo inputHi a b ∧ 0 < denominator ∧
    Fits lo hi denominator ∧ denominator % b = 0 ∧ Fits lo hi (a * (denominator / b))

instance (lo hi inputLo inputHi denominator a b : Int) :
    Decidable (CoefficientValid lo hi inputLo inputHi denominator a b) :=
  inferInstanceAs (Decidable (ReducedNonnegative inputLo inputHi a b ∧ 0 < denominator ∧
    Fits lo hi denominator ∧ denominator % b = 0 ∧ Fits lo hi (a * (denominator / b))))

def checkedCoefficient (lo hi inputLo inputHi denominator a b : Int) : Option Int :=
  if CoefficientValid lo hi inputLo inputHi denominator a b then
    some (a * (denominator / b)) else none

theorem checkedCoefficientSound (lo hi inputLo inputHi denominator a b coefficient : Int)
    (accepted : checkedCoefficient lo hi inputLo inputHi denominator a b = some coefficient) :
    CoefficientValid lo hi inputLo inputHi denominator a b ∧
    coefficient = a * (denominator / b) ∧ coefficient * b = a * denominator := by
  unfold checkedCoefficient at accepted
  split at accepted
  · rename_i valid
    cases Option.some.inj accepted
    refine ⟨valid, rfl, ?_⟩
    rw [Int.mul_assoc, Int.ediv_mul_cancel_of_emod_eq_zero valid.2.2.2.1]
  · contradiction

def exactAddVector (coefficient : Int) (acc values : List Int) : List Int :=
  List.zipWith (fun a q => a + coefficient * q) acc values

def StepSafe (lo hi inputLo inputHi coefficient : Int) : List Int → List Int → Prop
  | [], [] => True
  | a :: acc, q :: values =>
      Fits lo hi a ∧ Fits inputLo inputHi q ∧ Fits lo hi (coefficient * q) ∧
        Fits lo hi (a + coefficient * q) ∧ StepSafe lo hi inputLo inputHi coefficient acc values
  | _, _ => False

def checkedAddVector (lo hi inputLo inputHi coefficient : Int) :
    List Int → List Int → Option (List Int)
  | [], [] => some []
  | a :: acc, q :: values =>
      if Fits lo hi a ∧ Fits inputLo inputHi q ∧ Fits lo hi (coefficient * q) ∧
          Fits lo hi (a + coefficient * q) then
        match checkedAddVector lo hi inputLo inputHi coefficient acc values with
        | some tail => some ((a + coefficient * q) :: tail)
        | none => none
      else none
  | _, _ => none

theorem checkedAddVectorSound (lo hi inputLo inputHi coefficient : Int)
    (acc values result : List Int)
    (accepted : checkedAddVector lo hi inputLo inputHi coefficient acc values = some result) :
    result = exactAddVector coefficient acc values ∧ acc.length = values.length ∧
      result.length = acc.length ∧ StepSafe lo hi inputLo inputHi coefficient acc values := by
  induction acc generalizing values result with
  | nil =>
      cases values with
      | nil =>
          simp only [checkedAddVector] at accepted
          cases Option.some.inj accepted
          exact ⟨rfl, rfl, rfl, True.intro⟩
      | cons q values => simp [checkedAddVector] at accepted
  | cons a acc ih =>
      cases values with
      | nil => simp [checkedAddVector] at accepted
      | cons q values =>
          simp only [checkedAddVector] at accepted
          split at accepted
          · rename_i bounds
            cases rest : checkedAddVector lo hi inputLo inputHi coefficient acc values with
            | none => simp [rest] at accepted
            | some tail =>
                simp only [rest] at accepted
                cases Option.some.inj accepted
                obtain ⟨same, shape, length, safe⟩ := ih values tail rest
                refine ⟨?_, by simp [shape], by simp [length],
                  bounds.1, bounds.2.1, bounds.2.2.1, bounds.2.2.2, safe⟩
                simp only [exactAddVector, List.zipWith_cons_cons, same]
          · contradiction

def exactParameterRows (denominator : Int) (acc : List Int) : List Row → List Int
  | [] => acc
  | row :: rows => exactParameterRows denominator
      (exactAddVector (row.numerator * (denominator / row.denominator)) acc row.values) rows

def PrefixesSafe (lo hi inputLo inputHi denominator coefficientSum : Int)
    (acc : List Int) : List Row → Prop
  | [] => Fits lo hi coefficientSum ∧ ∀ value ∈ acc, Fits lo hi value
  | row :: rows =>
      let coefficient := row.numerator * (denominator / row.denominator)
      CoefficientValid lo hi inputLo inputHi denominator row.numerator row.denominator ∧
      Fits lo hi coefficientSum ∧ Fits lo hi (coefficientSum + coefficient) ∧
      StepSafe lo hi inputLo inputHi coefficient acc row.values ∧
      PrefixesSafe lo hi inputLo inputHi denominator (coefficientSum + coefficient)
        (exactAddVector coefficient acc row.values) rows

def checkedParameterRows (lo hi inputLo inputHi denominator coefficientSum : Int)
    (acc : List Int) : List Row → Option (List Int)
  | [] => if Fits lo hi coefficientSum ∧ (∀ value ∈ acc, Fits lo hi value)
      then some acc else none
  | row :: rows =>
      match checkedCoefficient lo hi inputLo inputHi denominator row.numerator row.denominator with
      | none => none
      | some coefficient =>
          if Fits lo hi coefficientSum ∧ Fits lo hi (coefficientSum + coefficient) then
            match checkedAddVector lo hi inputLo inputHi coefficient acc row.values with
            | none => none
            | some next => checkedParameterRows lo hi inputLo inputHi denominator
                (coefficientSum + coefficient) next rows
          else none

theorem checkedParameterRowsSound (lo hi inputLo inputHi denominator : Int)
    (rows : List Row) (coefficientSum : Int) (acc result : List Int)
    (accepted : checkedParameterRows lo hi inputLo inputHi denominator coefficientSum
      acc rows = some result) :
    result = exactParameterRows denominator acc rows ∧ result.length = acc.length ∧
      (∀ row ∈ rows, row.values.length = acc.length) ∧
      PrefixesSafe lo hi inputLo inputHi denominator coefficientSum acc rows := by
  induction rows generalizing coefficientSum acc result with
  | nil =>
      simp only [checkedParameterRows] at accepted
      split at accepted
      · rename_i bounds
        cases Option.some.inj accepted
        exact ⟨rfl, rfl, by simp, bounds⟩
      · contradiction
  | cons row rows ih =>
      simp only [checkedParameterRows] at accepted
      cases coeff : checkedCoefficient lo hi inputLo inputHi denominator
          row.numerator row.denominator with
      | none => simp [coeff] at accepted
      | some coefficient =>
          simp only [coeff] at accepted
          split at accepted
          · rename_i sums
            cases next : checkedAddVector lo hi inputLo inputHi coefficient acc row.values with
            | none => simp [next] at accepted
            | some nextAcc =>
                simp only [next] at accepted
                obtain ⟨valid, coefficientEq, _⟩ := checkedCoefficientSound
                  lo hi inputLo inputHi denominator row.numerator row.denominator coefficient coeff
                obtain ⟨stepEq, shape, stepLength, stepSafe⟩ := checkedAddVectorSound
                  lo hi inputLo inputHi coefficient acc row.values nextAcc next
                obtain ⟨resultEq, resultLength, shapes, safeTail⟩ :=
                  ih (coefficientSum + coefficient) nextAcc result accepted
                subst coefficientEq
                subst stepEq
                refine ⟨resultEq, resultLength.trans stepLength, ?_,
                  valid, sums.1, sums.2, stepSafe, safeTail⟩
                intro item member
                rcases List.mem_cons.mp member with equal | member
                · subst item; exact shape.symm
                · exact (shapes item member).trans stepLength
          · contradiction

def checkedParameter (lo hi inputLo inputHi denominator : Int) (width : Nat)
    (rows : List Row) : Option (List Int) :=
  if 0 < width ∧ rows ≠ [] then
    checkedParameterRows lo hi inputLo inputHi denominator 0 (List.replicate width 0) rows
  else none

theorem checkedParameterSound (lo hi inputLo inputHi denominator : Int) (width : Nat)
    (rows : List Row) (result : List Int)
    (accepted : checkedParameter lo hi inputLo inputHi denominator width rows = some result) :
    0 < width ∧ rows ≠ [] ∧ result.length = width ∧
      result = exactParameterRows denominator (List.replicate width 0) rows ∧
      (∀ row ∈ rows, row.values.length = width) ∧
      PrefixesSafe lo hi inputLo inputHi denominator 0 (List.replicate width 0) rows := by
  unfold checkedParameter at accepted
  split at accepted
  · rename_i nonempty
    obtain ⟨same, length, shapes, safe⟩ := checkedParameterRowsSound
      lo hi inputLo inputHi denominator rows 0 (List.replicate width 0) result accepted
    exact ⟨nonempty.1, nonempty.2, by simpa using length, same,
      fun row member => by simpa using shapes row member, safe⟩
  · contradiction

theorem checkedAddVectorComplete (lo hi inputLo inputHi coefficient : Int)
    (acc values : List Int) (safe : StepSafe lo hi inputLo inputHi coefficient acc values) :
    checkedAddVector lo hi inputLo inputHi coefficient acc values =
      some (exactAddVector coefficient acc values) := by
  induction acc generalizing values with
  | nil =>
      cases values with
      | nil => rfl
      | cons _ _ => exact False.elim safe
  | cons a acc ih =>
      cases values with
      | nil => exact False.elim safe
      | cons q values =>
          obtain ⟨aFit, qFit, productFit, sumFit, tailSafe⟩ := safe
          simp only [checkedAddVector, aFit, qFit, productFit, sumFit,
            and_self, ↓reduceIte, ih values tailSafe]
          rfl

theorem checkedParameterRowsComplete (lo hi inputLo inputHi denominator coefficientSum : Int)
    (acc : List Int) (rows : List Row)
    (safe : PrefixesSafe lo hi inputLo inputHi denominator coefficientSum acc rows) :
    checkedParameterRows lo hi inputLo inputHi denominator coefficientSum acc rows =
      some (exactParameterRows denominator acc rows) := by
  induction rows generalizing coefficientSum acc with
  | nil =>
      change Fits lo hi coefficientSum ∧ (∀ value ∈ acc, Fits lo hi value) at safe
      exact if_pos safe
  | cons row rows ih =>
      obtain ⟨valid, sumFit, nextSumFit, stepSafe, tailSafe⟩ := safe
      simp only [checkedParameterRows, checkedCoefficient, valid, ↓reduceIte,
        sumFit, nextSumFit, and_self]
      rw [checkedAddVectorComplete _ _ _ _ _ _ _ stepSafe]
      exact ih _ _ tailSafe

theorem checkedParameterRowsRejectsExactly (lo hi inputLo inputHi denominator coefficientSum : Int)
    (acc : List Int) (rows : List Row) :
    checkedParameterRows lo hi inputLo inputHi denominator coefficientSum acc rows = none ↔
      ¬ PrefixesSafe lo hi inputLo inputHi denominator coefficientSum acc rows := by
  constructor
  · intro rejected safe
    have accepted := checkedParameterRowsComplete lo hi inputLo inputHi denominator
      coefficientSum acc rows safe
    rw [rejected] at accepted
    contradiction
  · intro invalidBounds
    cases outcome : checkedParameterRows lo hi inputLo inputHi denominator coefficientSum acc rows with
    | none => rfl
    | some result =>
        have sound := checkedParameterRowsSound lo hi inputLo inputHi denominator
          rows coefficientSum acc result outcome
        exact False.elim (invalidBounds sound.2.2.2)

theorem stepSafeAt (lo hi inputLo inputHi coefficient : Int) (acc values : List Int)
    (safe : StepSafe lo hi inputLo inputHi coefficient acc values)
    (index : Nat) (a : Int) (atIndex : acc[index]? = some a) :
    ∃ q, values[index]? = some q ∧ Fits lo hi a ∧ Fits inputLo inputHi q ∧
      Fits lo hi (coefficient * q) ∧ Fits lo hi (a + coefficient * q) := by
  induction acc generalizing values index a with
  | nil => simp at atIndex
  | cons head acc ih =>
      cases values with
      | nil => exact False.elim safe
      | cons q values =>
          obtain ⟨headFit, qFit, productFit, sumFit, tailSafe⟩ := safe
          cases index with
          | zero =>
              simp only [List.getElem?_cons_zero] at atIndex
              cases Option.some.inj atIndex
              exact ⟨q, rfl, headFit, qFit, productFit, sumFit⟩
          | succ index =>
              exact ih values tailSafe index a atIndex

def coordinateTerms (denominator : Int) (index : Nat) (rows : List Row) : List (Int × Int) :=
  rows.map (fun row =>
    (row.numerator * (denominator / row.denominator), row.values[index]?.getD 0))

/-- The vector recurrence refines the previously proved ordered scalar kernel
at every present coordinate. The getD fallback is never used on an accepted row. -/
theorem parameterRowsCoordinateRefines (lo hi inputLo inputHi denominator coefficientSum : Int)
    (acc : List Int) (rows : List Row)
    (safe : PrefixesSafe lo hi inputLo inputHi denominator coefficientSum acc rows)
    (index : Nat) (a : Int) (atIndex : acc[index]? = some a) :
    ∃ value, (exactParameterRows denominator acc rows)[index]? = some value ∧
      checkedAccumulate lo hi lo hi a (coordinateTerms denominator index rows) = some value := by
  induction rows generalizing coefficientSum acc a with
  | nil =>
      obtain ⟨_, fits⟩ := safe
      have aFit := fits a (List.mem_of_getElem? atIndex)
      exact ⟨a, atIndex, by simp [coordinateTerms, checkedAccumulate, aFit]⟩
  | cons row rows ih =>
      obtain ⟨_, _, _, stepSafe, tailSafe⟩ := safe
      obtain ⟨q, qAt, aFit, _, productFit, _⟩ :=
        stepSafeAt lo hi inputLo inputHi _ acc row.values stepSafe index a atIndex
      have nextAt :
          (exactAddVector (row.numerator * (denominator / row.denominator))
            acc row.values)[index]? =
            some (a + (row.numerator * (denominator / row.denominator)) * q) := by
        simp [exactAddVector, List.getElem?_zipWith, atIndex, qAt]
      obtain ⟨value, resultAt, projected⟩ := ih _ _ tailSafe _ nextAt
      refine ⟨value, resultAt, ?_⟩
      simpa only [coordinateTerms, List.map_cons, qAt, Option.getD_some,
        checkedAccumulate, aFit, productFit, and_self, ↓reduceIte] using projected

theorem checkedParameterCoordinateRefines (lo hi inputLo inputHi denominator : Int) (width : Nat)
    (rows : List Row) (result : List Int)
    (accepted : checkedParameter lo hi inputLo inputHi denominator width rows = some result)
    (index : Nat) (within : index < width) :
    ∃ value, result[index]? = some value ∧
      checkedAccumulate lo hi lo hi 0 (coordinateTerms denominator index rows) = some value := by
  obtain ⟨_, _, _, same, _, safe⟩ := checkedParameterSound
    lo hi inputLo inputHi denominator width rows result accepted
  rw [same]
  exact parameterRowsCoordinateRefines lo hi inputLo inputHi denominator 0
    (List.replicate width 0) rows safe index 0 (List.getElem?_replicate_of_lt within)

def ConversionSafe (lo hi denominator u v x y n result : Int) : Prop :=
  Fits lo hi n ∧ Fits lo hi (n * u) ∧ Fits lo hi ((n * u) * y) ∧
    Fits lo hi (denominator * v) ∧ Fits lo hi ((denominator * v) * x) ∧
    Fits lo hi result ∧ result = round ((n * u) * y) ((denominator * v) * x)

inductive ConversionTrace (lo hi denominator u v x y : Int) : List Int → List Int → Prop where
  | nil : ConversionTrace lo hi denominator u v x y [] []
  | cons {n result ns results}
      (head : ConversionSafe lo hi denominator u v x y n result)
      (tail : ConversionTrace lo hi denominator u v x y ns results) :
      ConversionTrace lo hi denominator u v x y (n :: ns) (result :: results)

def checkedConvertRows (lo hi denominator u v x y : Int) : List Int → Option (List Int)
  | [] => some []
  | n :: ns =>
      if Fits lo hi n then
        match checkedConvert lo hi lo hi n denominator u v x y with
        | none => none
        | some value =>
            match checkedConvertRows lo hi denominator u v x y ns with
            | none => none
            | some values => some (value :: values)
      else none

theorem checkedConvertRowsSound (lo hi denominator u v x y : Int)
    (numerators result : List Int)
    (accepted : checkedConvertRows lo hi denominator u v x y numerators = some result) :
    result.length = numerators.length ∧
      ConversionTrace lo hi denominator u v x y numerators result ∧
      result = numerators.map (fun n => round ((n * u) * y) ((denominator * v) * x)) := by
  induction numerators generalizing result with
  | nil =>
      simp only [checkedConvertRows] at accepted
      cases Option.some.inj accepted
      exact ⟨rfl, .nil, rfl⟩
  | cons n ns ih =>
      simp only [checkedConvertRows] at accepted
      split at accepted
      · rename_i nFit
        cases conversion : checkedConvert lo hi lo hi n denominator u v x y with
        | none => simp [conversion] at accepted
        | some value =>
            simp only [conversion] at accepted
            cases rest : checkedConvertRows lo hi denominator u v x y ns with
            | none => simp [rest] at accepted
            | some values =>
                simp only [rest] at accepted
                cases Option.some.inj accepted
                obtain ⟨length, tailSafe, tailEq⟩ := ih values rest
                obtain ⟨_, _, _, _, _, p1, p2, d1, d2, output, valueEq⟩ :=
                  checkedConvertSound lo hi lo hi n denominator u v x y value conversion
                exact ⟨by simp [length],
                  .cons ⟨nFit, p1, p2, d1, d2, output, valueEq⟩ tailSafe,
                  by simp [valueEq, tailEq]⟩
      · contradiction

def DomainConditions (lo hi inputLo inputHi denominator u v x y : Int)
    (numerators : List Int) : Prop :=
  0 < denominator ∧ Fits lo hi denominator ∧
    ReducedNonnegative inputLo inputHi u v ∧ 0 < u ∧
    ReducedNonnegative inputLo inputHi x y ∧ 0 < x ∧ numerators ≠ []

instance (lo hi inputLo inputHi denominator u v x y : Int) (numerators : List Int) :
    Decidable (DomainConditions lo hi inputLo inputHi denominator u v x y numerators) :=
  inferInstanceAs (Decidable (0 < denominator ∧ Fits lo hi denominator ∧
    ReducedNonnegative inputLo inputHi u v ∧ 0 < u ∧
    ReducedNonnegative inputLo inputHi x y ∧ 0 < x ∧ numerators ≠ []))

def checkedDomainVector (lo hi inputLo inputHi denominator u v x y : Int)
    (numerators : List Int) : Option (List Int) :=
  if DomainConditions lo hi inputLo inputHi denominator u v x y numerators then
    checkedConvertRows lo hi denominator u v x y numerators else none

theorem checkedDomainVectorSound (lo hi inputLo inputHi denominator u v x y : Int)
    (numerators result : List Int)
    (accepted : checkedDomainVector lo hi inputLo inputHi denominator u v x y numerators =
      some result) :
    DomainConditions lo hi inputLo inputHi denominator u v x y numerators ∧
    result.length = numerators.length ∧
    ConversionTrace lo hi denominator u v x y numerators result ∧
    result = numerators.map (fun n => round ((n * u) * y) ((denominator * v) * x)) := by
  unfold checkedDomainVector at accepted
  split at accepted
  · rename_i conditions
    exact ⟨conditions, checkedConvertRowsSound lo hi denominator u v x y numerators result accepted⟩
  · contradiction

end DeltaReduce.ParameterKernel
