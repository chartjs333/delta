import Std

/-!
Amendment 0001: checked arithmetic over arbitrary ordered input lists.

These kernel lemmas cover the integer operation graph, not artifact decoding,
certificate authentication, native authority or WAL recovery. PO-AB1 stays open.
Bounds are asymmetric so FULL_SIGNED_INT64's minimum is representable. Products
and every prefix are checked separately: a safe final sum is insufficient.
-/
namespace DeltaReduce

def Fits (lo hi value : Int) : Prop := lo ≤ value ∧ value ≤ hi

instance (lo hi value : Int) : Decidable (Fits lo hi value) :=
  inferInstanceAs (Decidable (lo ≤ value ∧ value ≤ hi))

def exactAccumulate (acc : Int) : List (Int × Int) → Int
  | [] => acc
  | (coefficient, value) :: rest =>
      exactAccumulate (acc + coefficient * value) rest

def checkedAccumulate (lo hi productLo productHi acc : Int) : List (Int × Int) → Option Int
  | [] => if Fits lo hi acc then some acc else none
  | (coefficient, value) :: rest =>
      if Fits lo hi acc ∧ Fits productLo productHi (coefficient * value) then
        checkedAccumulate lo hi productLo productHi (acc + coefficient * value) rest
      else none

def AllPrefixesFit (lo hi productLo productHi acc : Int) : List (Int × Int) → Prop
  | [] => Fits lo hi acc
  | (coefficient, value) :: rest =>
      Fits lo hi acc ∧ Fits productLo productHi (coefficient * value) ∧
        AllPrefixesFit lo hi productLo productHi (acc + coefficient * value) rest

theorem checkedAccumulateSound (lo hi productLo productHi acc result : Int)
    (terms : List (Int × Int))
    (accepted : checkedAccumulate lo hi productLo productHi acc terms = some result) :
    result = exactAccumulate acc terms ∧
      AllPrefixesFit lo hi productLo productHi acc terms ∧ Fits lo hi result := by
  induction terms generalizing acc with
  | nil =>
      simp only [checkedAccumulate] at accepted
      split at accepted
      · rename_i bound
        cases Option.some.inj accepted
        exact ⟨rfl, bound, bound⟩
      · contradiction
  | cons term rest ih =>
      rcases term with ⟨coefficient, value⟩
      simp only [checkedAccumulate] at accepted
      split at accepted
      · rename_i bounds
        obtain ⟨same, prefixes, finalBound⟩ := ih _ accepted
        exact ⟨same, ⟨bounds.1, bounds.2, prefixes⟩, finalBound⟩
      · contradiction

theorem checkedAccumulateComplete (lo hi productLo productHi acc : Int)
    (terms : List (Int × Int)) (bounds : AllPrefixesFit lo hi productLo productHi acc terms) :
    checkedAccumulate lo hi productLo productHi acc terms = some (exactAccumulate acc terms) := by
  induction terms generalizing acc with
  | nil => simp only [AllPrefixesFit] at bounds; simp [checkedAccumulate, exactAccumulate, bounds]
  | cons term rest ih =>
      rcases term with ⟨coefficient, value⟩
      obtain ⟨initial, product, prefixes⟩ := bounds
      simp only [checkedAccumulate, initial, product, and_self, ↓reduceIte]
      exact ih _ prefixes

theorem checkedAccumulateRejectsExactly (lo hi productLo productHi acc : Int)
    (terms : List (Int × Int)) :
    checkedAccumulate lo hi productLo productHi acc terms = none ↔
      ¬ AllPrefixesFit lo hi productLo productHi acc terms := by
  constructor
  · intro rejected bounds
    have accepted := checkedAccumulateComplete lo hi productLo productHi acc terms bounds
    rw [rejected] at accepted
    contradiction
  · intro invalidBounds
    cases outcome : checkedAccumulate lo hi productLo productHi acc terms with
    | none => rfl
    | some result =>
        have safe := checkedAccumulateSound lo hi productLo productHi acc result terms outcome
        exact False.elim (invalidBounds safe.2.1)

def roundParts (quotient remainder denominator : Int) : Int :=
  if remainder < denominator - remainder then quotient else quotient + 1

def round (numerator denominator : Int) : Int :=
  roundParts (numerator / denominator) (numerator % denominator) denominator

theorem roundWithoutDoubledRemainder (numerator denominator : Int) :
    round numerator denominator =
      if 2 * (numerator % denominator) < denominator then numerator / denominator
      else numerator / denominator + 1 := by
  have equivalent : (numerator % denominator < denominator - numerator % denominator) ↔
      (2 * (numerator % denominator) < denominator) := by omega
  simp only [round, roundParts, equivalent]

/- Every multiplication is checked in the specified order, before rounding.
   In particular cancellation is not permission to skip an overflowing product. -/
def checkedConvert (lo hi outputLo outputHi n denominator u v x y : Int) : Option Int :=
  let p₁ := n * u
  let p₂ := p₁ * y
  let d₁ := denominator * v
  let d₂ := d₁ * x
  let result := round p₂ d₂
  if 0 < denominator ∧ 0 < u ∧ 0 < v ∧ 0 < x ∧ 0 < y ∧
      Fits lo hi p₁ ∧ Fits lo hi p₂ ∧ Fits lo hi d₁ ∧ Fits lo hi d₂ ∧
      Fits outputLo outputHi result then some result else none

theorem checkedConvertSound (lo hi outputLo outputHi n denominator u v x y result : Int)
    (accepted : checkedConvert lo hi outputLo outputHi n denominator u v x y = some result) :
    0 < denominator ∧ 0 < u ∧ 0 < v ∧ 0 < x ∧ 0 < y ∧
      Fits lo hi (n * u) ∧ Fits lo hi ((n * u) * y) ∧
      Fits lo hi (denominator * v) ∧ Fits lo hi ((denominator * v) * x) ∧
      Fits outputLo outputHi result ∧
      result = round ((n * u) * y) ((denominator * v) * x) := by
  dsimp only [checkedConvert] at accepted
  split at accepted
  · rename_i bounds
    cases Option.some.inj accepted
    exact ⟨bounds.1, bounds.2.1, bounds.2.2.1, bounds.2.2.2.1,
      bounds.2.2.2.2.1, bounds.2.2.2.2.2.1, bounds.2.2.2.2.2.2.1,
      bounds.2.2.2.2.2.2.2.1, bounds.2.2.2.2.2.2.2.2.1,
      bounds.2.2.2.2.2.2.2.2.2, rfl⟩
  · contradiction

theorem fullSignedMinimumAccepted :
    checkedConvert (-9223372036854775808) 9223372036854775807
      (-9223372036854775808) 9223372036854775807
      (-9223372036854775808) 1 1 1 1 1 = some (-9223372036854775808) := by decide

theorem conversionCancellationDoesNotPermitOverflow :
    checkedConvert (-8) 7 (-8) 7 7 2 2 1 1 1 = none ∧ round (7 * 2) 2 = 7 := by decide

theorem conversionOutputWidthIndependent :
    checkedConvert (-128) 127 (-8) 7 8 1 1 1 1 1 = none ∧
      checkedConvert (-128) 127 (-8) 7 8 2 1 1 1 1 = some 4 := by decide

theorem positiveAndNegativeHalf : round 1 2 = 1 ∧ round (-1) 2 = 0 := by decide

theorem unsafeProductRejectedDespiteSafeSum :
    checkedAccumulate (-8) 7 (-8) 7 (-7) [(2, 7)] = none ∧
      exactAccumulate (-7) [(2, 7)] = 7 := by decide

theorem unsafePrefixRejectedDespiteSafeFinal :
    checkedAccumulate (-8) 7 (-8) 7 0 [(1, 7), (1, 7), (1, -7), (1, -7)] = none ∧
      exactAccumulate 0 [(1, 7), (1, 7), (1, -7), (1, -7)] = 0 := by decide

theorem productAndAccumulatorWidthsIndependent :
    checkedAccumulate (-8) 7 (-128) 127 (-7) [(2, 7)] = some 7 ∧
      checkedAccumulate (-128) 127 (-8) 7 (-7) [(2, 7)] = none := by decide

theorem perDomainRoundingCannotMoveAcrossMixture :
    round (round 1 2 + round (-1) 2) 2 = 1 ∧ round (1 - 1) 4 = 0 := by decide

end DeltaReduce
