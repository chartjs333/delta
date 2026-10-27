import Std

/-! T047/T053: pure no-double-intent/view kernel for seed agreement.
This deliberately overapproximates the concrete signature/proposal/highest-
prepared guards: every concrete accepted intent must additionally pass those.
It is NOT a durable-storage, agreement safety/liveness or source-closure proof.
The empty start and all transitions are explicit; no prevalidated initial map.
-/
namespace DeltaReduce.ProfileSeedIntent

abbrev Bytes := List UInt8
inductive Kind | propose | prepare | commit | status deriving DecidableEq, Repr
structure Key where
  kind : Kind
  view : Nat
  deriving DecidableEq, Repr
structure Intent where
  key : Key
  body : Bytes
  deriving DecidableEq, Repr
structure State where
  view : Nat
  stored : Key → Option Bytes

def initial : State := ⟨0,fun _ => none⟩

def allowed (s : State) (i : Intent) : Prop :=
  if i.key.kind = .status then s.view < i.key.view else s.view = i.key.view
instance (s i) : Decidable (allowed s i) := by unfold allowed; infer_instance

def step (s : State) (i : Intent) : Option State :=
  match s.stored i.key with
  | some prior => if prior = i.body then some s else none
  | none => if allowed s i then
      some ⟨if i.key.kind = .status then i.key.view else s.view,
        fun key => if key = i.key then some i.body else s.stored key⟩
    else none

theorem exactRetry (s i) (prior : s.stored i.key = some i.body) :
    step s i = some s := by simp [step,prior]

theorem conflictingIntentRejected (s i prior)
    (stored : s.stored i.key = some prior) (different : prior ≠ i.body) :
    step s i = none := by simp [step,stored,different]

theorem acceptedStored {s i out} (ok : step s i = some out) :
    out.stored i.key = some i.body := by
  unfold step at ok
  cases h : s.stored i.key with
  | some prior =>
    simp only [h] at ok
    split at ok <;> try contradiction
    rename_i same
    cases Option.some.inj ok
    simpa [same] using h
  | none =>
    simp only [h] at ok
    split at ok <;> try contradiction
    cases Option.some.inj ok
    simp

theorem preservesStored {s i out key value} (ok : step s i = some out)
    (old : s.stored key = some value) : out.stored key = some value := by
  unfold step at ok
  cases h : s.stored i.key with
  | some prior =>
    simp only [h] at ok
    split at ok <;> try contradiction
    cases Option.some.inj ok
    exact old
  | none =>
    simp only [h] at ok
    split at ok <;> try contradiction
    cases Option.some.inj ok
    have different : key ≠ i.key := by
      intro same
      subst key
      simp [h] at old
    simpa [different] using old

theorem viewMonotone {s i out} (ok : step s i = some out) : s.view ≤ out.view := by
  unfold step at ok
  cases h : s.stored i.key with
  | some prior =>
    simp only [h] at ok
    split at ok <;> try contradiction
    cases Option.some.inj ok
    exact Nat.le_refl _
  | none =>
    simp only [h] at ok
    split at ok <;> try contradiction
    rename_i permit
    cases Option.some.inj ok
    simp only [allowed] at permit
    split <;> simp_all <;> omega

theorem newOldViewRejected (s i) (absent : s.stored i.key = none)
    (old : i.key.view < s.view) : step s i = none := by
  have no : ¬allowed s i := by
    unfold allowed
    split <;> omega
  simp [step,absent,no]

inductive Run : List Intent → State → Prop
  | start : Run [] initial
  | next {trace s i out} : Run trace s → step s i = some out → Run (trace ++ [i]) out

theorem allAcceptedRetained {trace out} (run : Run trace out) :
    ∀ i ∈ trace, out.stored i.key = some i.body := by
  induction run with
  | start => simp
  | @next trace s i out before ok ih =>
    intro x member
    simp only [List.mem_append,List.mem_singleton] at member
    rcases member with old | same
    · exact preservesStored ok (ih x old)
    · subst x; exact acceptedStored ok

theorem noConflictingAcceptedBodies {trace out} (run : Run trace out)
    {left right} (l : left ∈ trace) (r : right ∈ trace) (key : left.key = right.key) :
    left.body = right.body := by
  have hl := allAcceptedRetained run left l
  have hr := allAcceptedRetained run right r
  rw [key] at hl
  exact Option.some.inj (hl.symm.trans hr)

#print axioms exactRetry
#print axioms conflictingIntentRejected
#print axioms acceptedStored
#print axioms preservesStored
#print axioms viewMonotone
#print axioms newOldViewRejected
#print axioms allAcceptedRetained
#print axioms noConflictingAcceptedBodies

end DeltaReduce.ProfileSeedIntent
