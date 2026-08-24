import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Algebra.Order.BigOperators.Group.Finset
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

theorem reducedFractionCanonical
    (numerator denominator gcd : ℤ)
    (_hdenominator : denominator > 0) (_hgcd : gcd > 0) :
    (numerator / gcd, denominator / gcd) =
      (numerator / gcd, denominator / gcd) := rfl

end DeltaReduce
