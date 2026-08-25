import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Algebra.BigOperators.Group.Finset.Piecewise
import Mathlib.Algebra.Order.BigOperators.Group.Finset
import Mathlib.Algebra.Order.BigOperators.GroupWithZero.Finset
import Mathlib.Algebra.Order.Ring.Abs
import Mathlib.Data.Int.Basic
import Mathlib.Tactic.NormNum
import Lean.Elab.Tactic.Omega

/-! PO-A1--PO-A3 checked fixed-point arithmetic bounds. -/

namespace DeltaReduce

open scoped BigOperators

theorem signedProductBound (a q A Q : ℤ)
    (hA : 0 ≤ A) (_hQ : 0 ≤ Q)
    (ha : |a| ≤ A) (hq : |q| ≤ Q) :
    |a * q| ≤ A * Q := by
  rw [abs_mul]
  exact mul_le_mul ha hq (abs_nonneg q) hA

theorem flatAccumulatorBound {ι : Type*} [DecidableEq ι]
    (tickets : Finset ι) (a q : ι → ℤ) (Nmax : ℕ) (A Q : ℤ)
    (hN : tickets.card ≤ Nmax) (hA : 0 ≤ A) (hQ : 0 ≤ Q)
    (ha : ∀ j ∈ tickets, |a j| ≤ A)
    (hq : ∀ j ∈ tickets, |q j| ≤ Q) :
    |∑ j ∈ tickets, a j * q j| ≤ (Nmax : ℤ) * A * Q := by
  calc
    |∑ j ∈ tickets, a j * q j|
        ≤ ∑ j ∈ tickets, |a j * q j| := by
          exact Finset.abs_sum_le_sum_abs _ _
    _ ≤ ∑ _j ∈ tickets, A * Q := by
          exact Finset.sum_le_sum fun j hj =>
            signedProductBound (a j) (q j) A Q hA hQ (ha j hj) (hq j hj)
    _ = (tickets.card : ℤ) * A * Q := by simp [mul_assoc]
    _ ≤ (Nmax : ℤ) * A * Q := by
          have hcast : (tickets.card : ℤ) ≤ (Nmax : ℤ) := by exact_mod_cast hN
          exact mul_le_mul_of_nonneg_right
            (mul_le_mul_of_nonneg_right hcast hA) hQ

theorem everyCanonicalPrefixFits {ι : Type*} [DecidableEq ι]
    (tickets : Finset ι) (a q : ι → ℤ) (Nmax : ℕ) (A Q M : ℤ)
    (hN : tickets.card ≤ Nmax) (hA : 0 ≤ A) (hQ : 0 ≤ Q)
    (ha : ∀ j ∈ tickets, |a j| ≤ A)
    (hq : ∀ j ∈ tickets, |q j| ≤ Q)
    (hwidth : (Nmax : ℤ) * A * Q ≤ M) :
    ∀ (subset : Finset ι), subset ⊆ tickets →
      |∑ j ∈ subset, a j * q j| ≤ M := by
  intro subset hsubset
  have hpN : subset.card ≤ Nmax :=
    le_trans (Finset.card_le_card hsubset) hN
  have hp := flatAccumulatorBound subset a q Nmax A Q hpN hA hQ
    (fun j hj => ha j (hsubset hj)) (fun j hj => hq j (hsubset hj))
  exact le_trans hp hwidth

theorem intermediateProductFits (a q A Q productWidth : ℤ)
    (hA : 0 ≤ A) (hQ : 0 ≤ Q)
    (ha : |a| ≤ A) (hq : |q| ≤ Q)
    (hwidth : A * Q ≤ productWidth) :
    |a * q| ≤ productWidth :=
  le_trans (signedProductBound a q A Q hA hQ ha hq) hwidth

theorem commonDenominatorNumeratorSafe {ι : Type*} [DecidableEq ι]
    (tickets : Finset ι) (numerator quantized : ι → ℤ)
    (Nmax : ℕ) (NumeratorBound QuantizedBound accumulatorWidth : ℤ)
    (hN : tickets.card ≤ Nmax)
    (hNumerator : 0 ≤ NumeratorBound) (hQuantized : 0 ≤ QuantizedBound)
    (hn : ∀ j ∈ tickets, |numerator j| ≤ NumeratorBound)
    (hq : ∀ j ∈ tickets, |quantized j| ≤ QuantizedBound)
    (hwidth : (Nmax : ℤ) * NumeratorBound * QuantizedBound ≤ accumulatorWidth) :
    |∑ j ∈ tickets, numerator j * quantized j| ≤ accumulatorWidth := by
  exact le_trans
    (flatAccumulatorBound tickets numerator quantized Nmax NumeratorBound
      QuantizedBound hN hNumerator hQuantized hn hq)
    hwidth

theorem commonDenominatorDivisionDeterministic
    (numerator₁ numerator₂ denominator : ℤ)
    (_hdenominator : denominator ≠ 0)
    (hnumerator : numerator₁ = numerator₂) :
    numerator₁.ediv denominator = numerator₂.ediv denominator := by
  subst numerator₂
  rfl

/-! A reduced rational is canonical by construction: zero/negative
denominators and a common numerator/denominator factor are unrepresentable. -/

structure ReducedRational where
  numerator : ℤ
  denominator : ℕ
  denominatorPositive : 0 < denominator
  reduced : Nat.Coprime numerator.natAbs denominator

theorem reducedRationalDenominatorPositive (weight : ReducedRational) :
    0 < weight.denominator :=
  weight.denominatorPositive

theorem reducedRationalIsCoprime (weight : ReducedRational) :
    Nat.Coprime weight.numerator.natAbs weight.denominator :=
  weight.reduced

def commonDenominator {ι : Type*} [DecidableEq ι]
    (tickets : Finset ι) (weight : ι → ReducedRational) : ℕ :=
  ∏ ticket ∈ tickets, (weight ticket).denominator

theorem commonDenominatorPositive {ι : Type*} [DecidableEq ι]
    (tickets : Finset ι) (weight : ι → ReducedRational) :
    0 < commonDenominator tickets weight := by
  unfold commonDenominator
  exact Finset.prod_pos fun ticket _ => (weight ticket).denominatorPositive

theorem eachDenominatorDividesCommon {ι : Type*} [DecidableEq ι]
    (tickets : Finset ι) (weight : ι → ReducedRational)
    (ticket : ι) (hticket : ticket ∈ tickets) :
    (weight ticket).denominator ∣ commonDenominator tickets weight := by
  unfold commonDenominator
  exact Finset.dvd_prod_of_mem (fun item => (weight item).denominator) hticket

/-! Canonical rounding is nearest-integer rounding over Euclidean quotient and
remainder, with exact half ties resolved toward positive infinity. -/

def canonicalRound (numerator denominator : ℤ) : ℤ :=
  if 2 * numerator.emod denominator < denominator then
    numerator.ediv denominator
  else
    numerator.ediv denominator + 1

theorem canonicalRoundBelowHalf (numerator denominator : ℤ)
    (_hdenominator : 0 < denominator)
    (hbelow : 2 * numerator.emod denominator < denominator) :
    canonicalRound numerator denominator = numerator.ediv denominator := by
  simp [canonicalRound, hbelow]

theorem canonicalRoundAtOrAboveHalf (numerator denominator : ℤ)
    (_hdenominator : 0 < denominator)
    (habove : denominator ≤ 2 * numerator.emod denominator) :
    canonicalRound numerator denominator = numerator.ediv denominator + 1 := by
  simp [canonicalRound, Int.not_lt.mpr habove]

theorem canonicalRoundTieTowardPositive (numerator denominator : ℤ)
    (_hdenominator : 0 < denominator)
    (htie : 2 * numerator.emod denominator = denominator) :
    canonicalRound numerator denominator = numerator.ediv denominator + 1 := by
  apply canonicalRoundAtOrAboveHalf numerator denominator _hdenominator
  omega

theorem canonicalRoundDeterministic
    (numerator₁ numerator₂ denominator₁ denominator₂ : ℤ)
    (hnumerator : numerator₁ = numerator₂)
    (hdenominator : denominator₁ = denominator₂) :
    canonicalRound numerator₁ denominator₁ =
      canonicalRound numerator₂ denominator₂ := by
  subst numerator₂
  subst denominator₂
  rfl

end DeltaReduce
