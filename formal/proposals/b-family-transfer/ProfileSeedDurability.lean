import Std

/-! T047/T053 two-barrier seed transaction under the existing T primitive.
This is the durability kernel, NOT a whole-source or cryptographic theorem.
`intent` and `signed` are exact computed/checked companion frames. Full journal
replay applies the separate no-double-intent and evidence guards. A recovery
case compares ORIGINAL attempted bytes, not just an imported durable flag.
-/
namespace DeltaReduce.ProfileSeedDurability

abbrev Bytes := List UInt8
structure Transaction where
  prior : Bytes
  intent : Bytes
  signed : Bytes
  artifact : Bytes
  deriving DecidableEq, Repr
def intentTip (t : Transaction) := t.prior ++ t.intent
def signedTip (t : Transaction) := intentTip t ++ t.signed

inductive Phase where
  | prepared | intentAppended | intentRecovered | intentDurable | intentCommitted
  | produced | signedAppended | signedRecovered | signedDurable | signedCommitted
  | crashed | blocked
  deriving DecidableEq, Repr
structure State where
  nativeWal : Bytes
  volatile : Bytes
  stable : Bytes
  phase : Phase
  exposed : List Bytes
  deriving DecidableEq, Repr
def initial (t : Transaction) (wal : Bytes) : State :=
  ⟨wal,t.prior,t.prior,.prepared,[]⟩

inductive Action where
  | appendIntent | barrierIntent | commitIntent | sign | appendSigned
  | barrierSigned | commitSigned | expose | recover
  | crash (surviving : Bytes)
  deriving DecidableEq, Repr

def step (t : Transaction) (s : State) : Action → Option State
  | .appendIntent => if s.phase = .prepared ∧ s.volatile = t.prior then
      some {s with volatile := intentTip t, phase := .intentAppended} else none
  | .barrierIntent => if (s.phase = .intentAppended ∨ s.phase = .intentRecovered) ∧
      s.volatile = intentTip t then
      some {s with stable := s.volatile, phase := .intentDurable} else none
  | .commitIntent => if s.phase = .intentDurable ∧ s.stable = intentTip t then
      some {s with phase := .intentCommitted} else none
  | .sign => if s.phase = .intentCommitted ∧ s.stable = intentTip t then
      some {s with phase := .produced} else none
  | .appendSigned => if s.phase = .produced ∧ s.volatile = intentTip t then
      some {s with volatile := signedTip t, phase := .signedAppended} else none
  | .barrierSigned => if (s.phase = .signedAppended ∨ s.phase = .signedRecovered) ∧
      s.volatile = signedTip t then
      some {s with stable := s.volatile, phase := .signedDurable} else none
  | .commitSigned => if s.phase = .signedDurable ∧ s.stable = signedTip t then
      some {s with phase := .signedCommitted} else none
  | .expose => if s.phase = .signedCommitted ∧ s.stable = signedTip t then
      some {s with exposed := s.exposed ++ [t.artifact]} else none
  | .crash surviving => if s.stable.IsPrefix surviving ∧ surviving.length ≤ s.volatile.length then
      some {s with volatile := surviving, stable := surviving, phase := .crashed} else none
  | .recover => if s.phase = .crashed then
      some {s with phase := if s.volatile = signedTip t then .signedRecovered
        else if s.volatile = intentTip t then .intentRecovered
        else if s.volatile = t.prior then .prepared else .blocked} else none

inductive Run (t : Transaction) (wal : Bytes) : List Action → State → Prop where
  | start : Run t wal [] (initial t wal)
  | next {trace before after act} : Run t wal trace before →
      step t before act = some after → Run t wal (act::trace) after

def intentBarrierSinceCrash : List Action → Bool
  | [] => false
  | .barrierIntent::_ => true
  | .crash _::_ => false
  | _::xs => intentBarrierSinceCrash xs
def artifactBarrierSinceCrash : List Action → Bool
  | [] => false
  | .barrierSigned::_ => true
  | .crash _::_ => false
  | _::xs => artifactBarrierSinceCrash xs

def IntentArmed (s : State) : Prop :=
  s.phase = .intentDurable ∨ s.phase = .intentCommitted ∨ s.phase = .produced ∨
  s.phase = .signedAppended
def ArtifactArmed (s : State) : Prop :=
  s.phase = .signedDurable ∨ s.phase = .signedCommitted

theorem stepWal {t s act out} (ok : step t s act = some out) :
    out.nativeWal = s.nativeWal := by
  cases act <;> simp only [step] at ok <;> split at ok <;> try contradiction
  all_goals cases Option.some.inj ok; rfl

theorem stepHistory {t s act out} (ok : step t s act = some out) :
    s.exposed.IsPrefix out.exposed := by
  cases act <;> simp only [step] at ok <;> split at ok <;> try contradiction
  all_goals cases Option.some.inj ok; simp

theorem stepArmed {t s act out trace} (ok : step t s act = some out)
    (hi : IntentArmed s → intentBarrierSinceCrash trace = true)
    (ha : ArtifactArmed s → artifactBarrierSinceCrash trace = true) :
    (IntentArmed out → intentBarrierSinceCrash (act::trace) = true) ∧
    (ArtifactArmed out → artifactBarrierSinceCrash (act::trace) = true) := by
  cases act <;> simp only [step] at ok <;> split at ok <;> try contradiction
  all_goals cases Option.some.inj ok; simp_all [IntentArmed,ArtifactArmed,
    intentBarrierSinceCrash,artifactBarrierSinceCrash]
  all_goals repeat' first | split | constructor
  all_goals simp_all

theorem runArmed {t wal trace s} (run : Run t wal trace s) :
    s.nativeWal = wal ∧
    (IntentArmed s → intentBarrierSinceCrash trace = true) ∧
    (ArtifactArmed s → artifactBarrierSinceCrash trace = true) := by
  induction run with
  | start => simp [initial,IntentArmed,ArtifactArmed]
  | next before ok ih =>
    exact ⟨(stepWal ok).trans ih.1,stepArmed ok ih.2.1 ih.2.2⟩

theorem signingRequiresIntentBarrier {t wal trace s out}
    (run : Run t wal trace s) (signed : step t s .sign = some out) :
    intentBarrierSinceCrash trace = true ∧ s.stable = intentTip t := by
  simp only [step] at signed
  split at signed <;> try contradiction
  rename_i guard
  exact ⟨(runArmed run).2.1 (Or.inr (Or.inl guard.1)),guard.2⟩

theorem exposureRequiresArtifactBarrier {t wal trace s out}
    (run : Run t wal trace s) (exposed : step t s .expose = some out) :
    artifactBarrierSinceCrash trace = true ∧ s.stable = signedTip t ∧
    out.exposed = s.exposed ++ [t.artifact] ∧ out.nativeWal = wal := by
  simp only [step] at exposed
  split at exposed <;> try contradiction
  rename_i guard
  cases Option.some.inj exposed
  exact ⟨(runArmed run).2.2 (Or.inr guard.1),guard.2,rfl,(runArmed run).1⟩

theorem retryExposureKeepsJournal {t s out} (ok : step t s .expose = some out) :
    out.stable = s.stable ∧ out.volatile = s.volatile := by
  simp only [step] at ok
  split at ok <;> try contradiction
  cases Option.some.inj ok
  exact ⟨rfl,rfl⟩

theorem tornRecoveryBlocked {t s out} (crashed : s.phase = .crashed)
    (notSigned : s.volatile ≠ signedTip t) (notIntent : s.volatile ≠ intentTip t)
    (notPrior : s.volatile ≠ t.prior) (ok : step t s .recover = some out) :
    out.phase = .blocked ∧ out.volatile = s.volatile ∧ out.stable = s.stable := by
  simp [step,crashed,notSigned,notIntent,notPrior] at ok
  cases ok
  exact ⟨rfl,rfl,rfl⟩

/-- Exact origin state corresponding to durability.py's recovery_active/base/
target. First capture is from original pre-crash state; subsequent crashes
cannot replace it. Only successful replay/barrier/commit releases this origin. -/
structure RecoveryOrigin where
  active : Bool
  base : Bytes
  attempted : Bytes
  deriving DecidableEq, Repr

def capture (o : RecoveryOrigin) (stable volatile : Bytes) : RecoveryOrigin :=
  if o.active then o else ⟨true,stable,volatile⟩
def recognized (o : RecoveryOrigin) (surviving : Bytes) : Bool :=
  o.active && (surviving == o.base || surviving == o.attempted)
def captureMany (o : RecoveryOrigin) : List (Bytes × Bytes) → RecoveryOrigin
  | [] => o
  | (stable,volatile)::rest => captureMany (capture o stable volatile) rest

theorem captureFirst (o : RecoveryOrigin) (inactive : o.active = false) (stable volatile) :
    capture o stable volatile = ⟨true,stable,volatile⟩ := by simp [capture,inactive]
theorem captureActive (o : RecoveryOrigin) (active : o.active = true) (stable volatile) :
    capture o stable volatile = o := by simp [capture,active]
theorem repeatedCrashOrigin (o : RecoveryOrigin) (active : o.active = true) (buffers) :
    captureMany o buffers = o := by
  induction buffers with
  | nil => rfl
  | cons head rest ih => simpa [captureMany,captureActive o active] using ih
theorem unknownRemainsRejected (o : RecoveryOrigin) (active : o.active = true)
    (surviving : Bytes) (unknown : surviving ≠ o.base ∧ surviving ≠ o.attempted) (buffers) :
    recognized (captureMany o buffers) surviving = false := by
  rw [repeatedCrashOrigin o active]
  simp [recognized,unknown.1,unknown.2]

#print axioms stepWal
#print axioms stepHistory
#print axioms stepArmed
#print axioms runArmed
#print axioms signingRequiresIntentBarrier
#print axioms exposureRequiresArtifactBarrier
#print axioms retryExposureKeepsJournal
#print axioms tornRecoveryBlocked
#print axioms captureFirst
#print axioms captureActive
#print axioms repeatedCrashOrigin
#print axioms unknownRemainsRejected
end DeltaReduce.ProfileSeedDurability
