import DeltaReduce.NativeVoteBytes

/-! Lexical model of the pinned certificate require_decimal/from_chars composition.
This intentionally retains accepted negative-zero/leading-zero strings. It is not
a proof of C++ std::from_chars or a repair of canonical protocol arithmetic. -/
namespace DeltaReduce.NativeCertificateDecimal
open NativeReceiptBytes

def negative (raw : Bytes) : Bool := raw.head? == some 45
def digits (raw : Bytes) : Bytes := if negative raw then raw.drop 1 else raw
def magnitude (raw : Bytes) : Nat := NativeVoteBytes.decimalValue (digits raw)
def number (raw : Bytes) : Int :=
  if negative raw then -(Int.ofNat (magnitude raw)) else Int.ofNat (magnitude raw)

def Lexical (raw : Bytes) : Prop :=
  raw ≠ [] ∧ (raw = [48] ∨ (raw.head? ≠ some 48 ∧ raw ≠ [45,48])) ∧
  digits raw ≠ [] ∧ (∀ b ∈ digits raw, NativeVoteBytes.digit b)
instance (raw) : Decidable (Lexical raw) := by unfold Lexical; infer_instance

def Valid (nonnegative : Bool) (raw : Bytes) : Prop :=
  Lexical raw ∧ -(2^63 : Int) ≤ number raw ∧ number raw < 2^63 ∧
  (nonnegative = true → 0 ≤ number raw)
instance (nonnegative raw) : Decidable (Valid nonnegative raw) := by unfold Valid; infer_instance

def parse (nonnegative : Bool) (raw : Bytes) : Option Int :=
  if Valid nonnegative raw then some (number raw) else none

theorem parsed {nonnegative raw n} (h : parse nonnegative raw = some n) :
    Valid nonnegative raw ∧ n = number raw := by
  unfold parse at h
  split at h
  · exact ⟨‹Valid nonnegative raw›,(Option.some.inj h).symm⟩
  · contradiction

theorem fromValid {nonnegative raw} (h : Valid nonnegative raw) :
    parse nonnegative raw = some (number raw) := if_pos h

theorem invalidRejected {nonnegative raw} (h : ¬ Valid nonnegative raw) :
    parse nonnegative raw = none := if_neg h

theorem range {nonnegative raw n} (h : parse nonnegative raw = some n) :
    -(2^63 : Int) ≤ n ∧ n < 2^63 := by
  obtain ⟨valid,rfl⟩ := parsed h
  exact ⟨valid.2.1,valid.2.2.1⟩

theorem nonnegativeResult {raw n} (h : parse true raw = some n) : 0 ≤ n := by
  obtain ⟨valid,rfl⟩ := parsed h
  exact valid.2.2.2 rfl

theorem originalDigits {nonnegative raw n} (h : parse nonnegative raw = some n) :
    digits raw ≠ [] ∧ ∀ b ∈ digits raw, NativeVoteBytes.digit b := (parsed h).1.1.2.2

theorem signedFromNonnegative {raw n} (h : parse true raw = some n) :
    parse false raw = some n := by
  obtain ⟨valid,rfl⟩ := parsed h
  exact fromValid ⟨valid.1,valid.2.1,valid.2.2.1,by simp⟩

theorem negativeNonnegativeIsZero {raw n} (h : parse true raw = some n)
    (sign : negative raw = true) : n = 0 := by
  have lower := nonnegativeResult h
  have eq := (parsed h).2
  simp only [number,sign,ite_true] at eq
  have positive : 0 ≤ Int.ofNat (magnitude raw) := Int.natCast_nonneg _
  omega

-- Canonical spelling is a separate predicate, not a conclusion of parse.
def Canonical (raw : Bytes) : Prop :=
  raw = [48] ∨ (digits raw ≠ [] ∧
    (∃ b ∈ (digits raw).head?, 49 ≤ b.toNat ∧ b.toNat ≤ 57) ∧
    ∀ b ∈ digits raw, NativeVoteBytes.digit b)
instance (raw) : Decidable (Canonical raw) := by unfold Canonical; infer_instance

structure Checked where
  original : Bytes
  value : Int
  deriving DecidableEq, Repr

def check (nonnegative : Bool) (raw : Bytes) : Option Checked := do
  let n ← parse nonnegative raw
  some ⟨raw,n⟩

theorem checkedOriginal {nonnegative raw out} (h : check nonnegative raw = some out) :
    out.original = raw ∧ parse nonnegative raw = some out.value := by
  unfold check at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨n,hn,last⟩ := h
  cases Option.some.inj last
  exact ⟨rfl,hn⟩

theorem checkedFromParse {nonnegative raw n} (h : parse nonnegative raw = some n) :
    check nonnegative raw = some ⟨raw,n⟩ := by simp only [check,h,bind,Option.bind]

theorem differentOriginals {nonnegative a b x y}
    (ha : check nonnegative a = some x) (hb : check nonnegative b = some y)
    (different : a ≠ b) : x ≠ y := by
  intro eq
  have h := congrArg Checked.original eq
  rw [(checkedOriginal ha).1,(checkedOriginal hb).1] at h
  exact different h

theorem emptyRejected (nonnegative) : parse nonnegative [] = none := by
  apply invalidRejected
  simp [Valid,Lexical]

theorem singleNegativeZeroRejected (nonnegative) : parse nonnegative [45,48] = none := by
  apply invalidRejected
  simp [Valid,Lexical]

end DeltaReduce.NativeCertificateDecimal
