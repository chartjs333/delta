import Std

/-!
Amendment 0001 candidate lemmas. No production Formal GO is claimed.
The interval lemmas are parametric in integers. Hash injectivity and native
anchor authentication remain explicit premises, not cryptography proofs.
-/
namespace ArithmeticBinding

def roundParts (q r d : Int) : Int := if r < d - r then q else q + 1

def round (n d : Int) : Int := roundParts (n / d) (n % d) d

theorem noDoubleRemainderOverflow (r d : Int) :
    (r < d - r) = (2 * r < d) := by
  apply propext
  constructor <;> omega

theorem tieTowardPositive (q r d : Int) (tie : 2 * r = d) :
    roundParts q r d = q + 1 := by
  have h : ¬ r < d - r := by omega
  simp [roundParts, h]

theorem adjacentIntegers (q r d : Int) :
    q ≤ roundParts q r d ∧ roundParts q r d ≤ q + 1 := by
  unfold roundParts
  split <;> omega

theorem outputRange (q r d lo hi : Int)
    (lower : lo ≤ q) (upper : q + 1 ≤ hi) :
    lo ≤ roundParts q r d ∧ roundParts q r d ≤ hi := by
  have h := adjacentIntegers q r d
  omega

theorem exactMinimum (lo d : Int) (positive : 0 < d) :
    roundParts lo 0 d = lo := by
  simp [roundParts, positive]

theorem negativeHalf : round (-1) 2 = 0 := by decide
theorem positiveHalf : round 1 2 = 1 := by decide
theorem fullSignedMinimum : round (-9223372036854775808) 1 = -9223372036854775808 := by decide
theorem roundingCannotMoveAcrossMixture :
    round (round 1 2 + round (-1) 2) 2 ≠ round (1 - 1) 4 := by decide

def convert (n denominator u v x y : Int) : Int :=
  round ((n * u) * y) ((denominator * v) * x)

def step (theta momentum gradient muN muD lrN lrD wdN wdD : Int) : Int × Int :=
  let nextMomentum := round (momentum * muN) muD + gradient
  let direction := round (nextMomentum * muN) muD + gradient
  let decay := round (theta * wdN) wdD
  (theta - round ((direction + decay) * lrN) lrD, nextMomentum)

theorem convertedQuantum : convert 7 2 1 2 1 4 = 7 := by decide
theorem checkedFixtureStep : step 20 2 1 1 2 1 2 0 1 = (19, 2) := by decide

def admit {Bytes : Type} [DecidableEq Bytes]
    (expected candidate : Bytes) : Option Bytes :=
  if candidate = expected then some candidate else none

theorem acceptedEqualsRecomputed {Bytes : Type} [DecidableEq Bytes]
    (expected candidate accepted : Bytes)
    (h : admit expected candidate = some accepted) : accepted = expected := by
  unfold admit at h
  split at h
  · rename_i same
    simp only [Option.some.injEq] at h
    exact h.symm.trans same
  · contradiction

theorem substitutionRejected {Bytes : Type} [DecidableEq Bytes]
    (expected candidate : Bytes) (different : candidate ≠ expected) :
    admit expected candidate = none := by simp [admit, different]

theorem exactBytesFromBoundHash {Bytes Id : Type}
    (hash : Bytes → Id) (hashInjective : Function.Injective hash)
    (bound payload : Bytes) (sameId : hash payload = hash bound) : payload = bound :=
  hashInjective sameId

theorem deterministicRecovery {Anchor Bytes : Type}
    (compute : Anchor → Bytes) (before after : Anchor) (restored : after = before) :
    compute after = compute before := congrArg compute restored

end ArithmeticBinding

#print axioms ArithmeticBinding.noDoubleRemainderOverflow
#print axioms ArithmeticBinding.tieTowardPositive
#print axioms ArithmeticBinding.adjacentIntegers
#print axioms ArithmeticBinding.outputRange
#print axioms ArithmeticBinding.exactMinimum
#print axioms ArithmeticBinding.negativeHalf
#print axioms ArithmeticBinding.positiveHalf
#print axioms ArithmeticBinding.fullSignedMinimum
#print axioms ArithmeticBinding.roundingCannotMoveAcrossMixture
#print axioms ArithmeticBinding.convertedQuantum
#print axioms ArithmeticBinding.checkedFixtureStep
#print axioms ArithmeticBinding.acceptedEqualsRecomputed
#print axioms ArithmeticBinding.substitutionRejected
#print axioms ArithmeticBinding.exactBytesFromBoundHash
#print axioms ArithmeticBinding.deterministicRecovery
