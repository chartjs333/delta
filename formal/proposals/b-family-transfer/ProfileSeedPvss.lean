import Mathlib.Tactic.Ring

/-! T047/T053. Algebra used by the isolated existing-key PVSS component.
These are scalar-field identities, not cryptographic soundness, a seed authority
predicate, or R2.3 closure. DDH, signature and Fiat–Shamir assumptions are NOT
declared as Lean axioms. No claim of a whole producer follows from these lemmas.
-/
namespace DeltaReduce.ProfileSeedPvss

variable {F : Type*} [CommRing F]

def polynomial (a b c z : F) : F := a + b*z + c*z^2

/-- Each reconstructed DLEQ commitment uses this scalar identity. -/
theorem responseCompleteness (w challenge witness : F) :
    (w - challenge*witness) + challenge*witness = w := by ring

theorem reconstruct123 (a b c : F) :
    3 * polynomial a b c 1 - 3 * polynomial a b c 2 + polynomial a b c 3 = a := by
  unfold polynomial
  ring

/-- Subset 1,2,4: denominator-cleared identity, valid in any commutative ring. -/
theorem reconstruct124Scaled (a b c : F) :
    8 * polynomial a b c 1 - 6 * polynomial a b c 2 + polynomial a b c 4 = 3*a := by
  unfold polynomial
  ring

theorem reconstruct134 (a b c : F) :
    2 * polynomial a b c 1 - 2 * polynomial a b c 3 + polynomial a b c 4 = a := by
  unfold polynomial
  ring

theorem reconstruct234 (a b c : F) :
    6 * polynomial a b c 2 - 8 * polynomial a b c 3 + 3 * polynomial a b c 4 = a := by
  unfold polynomial
  ring

theorem reconstruct1234 (a b c : F) :
    4 * polynomial a b c 1 - 6 * polynomial a b c 2 +
      4 * polynomial a b c 3 - polynomial a b c 4 = a := by
  unfold polynomial
  ring

/-- Explicit inverse premise, not a premise saying reconstruction succeeded. -/
theorem reconstruct124 (a b c inverseThree : F) (inverse : inverseThree * 3 = 1) :
    inverseThree * (8 * polynomial a b c 1 - 6 * polynomial a b c 2 +
      polynomial a b c 4) = a := by
  rw [reconstruct124Scaled, ← mul_assoc, inverse, one_mul]

/-- Applying any deterministic encoding to the reconstructed scalar keeps the
    same output. A concrete group implementation still requires qualification. -/
theorem allSubsetsSamePoint {Point : Type*} (encode : F → Point)
    (a b c inverseThree : F) (inverse : inverseThree * 3 = 1) :
    encode (3 * polynomial a b c 1 - 3 * polynomial a b c 2 + polynomial a b c 3) = encode a ∧
    encode (inverseThree * (8 * polynomial a b c 1 - 6 * polynomial a b c 2 +
      polynomial a b c 4)) = encode a ∧
    encode (2 * polynomial a b c 1 - 2 * polynomial a b c 3 + polynomial a b c 4) = encode a ∧
    encode (6 * polynomial a b c 2 - 8 * polynomial a b c 3 +
      3 * polynomial a b c 4) = encode a := by
  simp only [reconstruct123,reconstruct124 a b c inverseThree inverse,
    reconstruct134,reconstruct234,and_self]

#print axioms responseCompleteness
#print axioms reconstruct123
#print axioms reconstruct124Scaled
#print axioms reconstruct134
#print axioms reconstruct234
#print axioms reconstruct1234
#print axioms reconstruct124
#print axioms allSubsetsSamePoint

end DeltaReduce.ProfileSeedPvss
