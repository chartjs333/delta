import DeltaReduce.NativeWalBytes

/-! T047/T053. Static Profile-v1 source components, independent of public state.
Original bytes/positions are retained. This is not the full native producing
history verifier, R2 closure, a signature oracle or a recovery theorem. The
SHA byte function is an explicit primitive, as in the existing native codecs.
No successful public check occurs in any source premise. -/
namespace DeltaReduce.ProfileSource
open NativeReceiptBytes (Bytes)

structure Reference where
  length : Nat
  digest : Bytes
  deriving DecidableEq, Repr

structure Artifact where
  reference : Reference
  original : Bytes
  deriving DecidableEq, Repr

def ArtifactMatches (sha : Bytes → Bytes) (a : Artifact) : Prop :=
  a.reference.length = a.original.length ∧ a.reference.digest = sha a.original ∧
  a.reference.digest.length = 32
instance (sha a) : Decidable (ArtifactMatches sha a) := by
  unfold ArtifactMatches; infer_instance

def resolve (sha : Bytes → Bytes) (inventory : List Artifact) (r : Reference) : Option Bytes := do
  let a ← inventory.find? (fun a => a.reference == r)
  if ArtifactMatches sha a then some a.original else none

theorem resolvedOriginal {sha inventory r raw} (ok : resolve sha inventory r = some raw) :
    ∃ a ∈ inventory, a.reference = r ∧ a.original = raw ∧ ArtifactMatches sha a := by
  unfold resolve at ok
  cases hf : inventory.find? (fun a => a.reference == r) with
  | none => simp [hf] at ok
  | some a =>
    simp only [hf, bind, Option.bind] at ok
    split at ok <;> try contradiction
    rename_i good
    cases Option.some.inj ok
    exact ⟨a, List.mem_of_find?_eq_some hf, by simpa using List.find?_some hf, rfl, good⟩

theorem resolvedDigest {sha inventory r raw} (ok : resolve sha inventory r = some raw) :
    r.length = raw.length ∧ r.digest = sha raw ∧ r.digest.length = 32 := by
  obtain ⟨a, _, hr, hb, hm⟩ := resolvedOriginal ok
  simpa only [ArtifactMatches, hr, hb] using hm

theorem substitutionRequiresDigestCollision {sha inventory other r a b}
    (left : resolve sha inventory r = some a) (right : resolve sha other r = some b)
    (different : a ≠ b) : a ≠ b ∧ sha a = sha b := by
  exact ⟨different, (resolvedDigest left).2.1.symm.trans (resolvedDigest right).2.1⟩

def resolveAll (sha : Bytes → Bytes) (inventory : List Artifact) : List Reference → Option (List Bytes)
  | [] => some []
  | r :: rest => do
    let raw ← resolve sha inventory r
    let tail ← resolveAll sha inventory rest
    some (raw :: tail)

theorem resolveAllLength {sha inventory refs raw}
    (ok : resolveAll sha inventory refs = some raw) : raw.length = refs.length := by
  induction refs generalizing raw with
  | nil => simpa [resolveAll] using ok.symm
  | cons r rest ih =>
    simp only [resolveAll, bind, Option.bind_eq_some_iff] at ok
    obtain ⟨head, _, tail, ht, last⟩ := ok
    cases Option.some.inj last
    simpa using congrArg Nat.succ (ih ht)

theorem resolveAllPosition {sha inventory refs raw}
    (ok : resolveAll sha inventory refs = some raw) {n : Nat} {r : Reference} (found : refs[n]? = some r) :
    ∃ original, raw[n]? = some original ∧ resolve sha inventory r = some original := by
  induction refs generalizing raw n with
  | nil => simp at found
  | cons head rest ih =>
    simp only [resolveAll, bind, Option.bind_eq_some_iff] at ok
    obtain ⟨value, hv, tail, ht, last⟩ := ok
    cases Option.some.inj last
    cases n with
    | zero =>
      have same : head = r := by simpa using found
      subst r
      exact ⟨value, rfl, hv⟩
    | succ n =>
      obtain ⟨original, ha, hr⟩ := ih ht (by simpa using found)
      exact ⟨original, by simpa using ha, hr⟩

/- Neither storage equality nor a content hash licenses conversion of an event
list to a set. Position is part of the source input, also for repeated bytes. -/
theorem repeatedOccurrenceKept {sha inventory r raw}
    (ok : resolve sha inventory r = some raw) :
    resolveAll sha inventory [r, r] = some [raw, raw] := by
  simp [resolveAll, ok]

structure PrimitiveOrigin where
  bootstrap : Bytes
  sourceIndex : Bytes
  ownJournals : List Bytes
  deriving DecidableEq, Repr

def exactOrigin (original supplied : PrimitiveOrigin) : Bool := decide (original = supplied)

theorem checkedOrigin {original supplied} (ok : exactOrigin original supplied = true) :
    original.bootstrap = supplied.bootstrap ∧ original.sourceIndex = supplied.sourceIndex ∧
    original.ownJournals = supplied.ownJournals := by
  have h : original = supplied := by simpa only [exactOrigin, decide_eq_true_eq] using ok
  cases h
  exact ⟨rfl, rfl, rfl⟩

namespace Wal
open NativeWalBytes (Entry)

def increment (e : Entry) : Nat := if e.kind = 2 then 1 else 0

def voteCount (xs : List Entry) : Nat := (xs.map increment).sum

/- The complete ordered source list is the carrier. The ordinal annotates an
entry; it never replaces the original physical slot or creates a new vote. -/
def annotate (before : Nat) : List Entry → List (Entry × Nat)
  | [] => []
  | e :: rest => (e, before + increment e) :: annotate (before + increment e) rest

theorem annotationRetainsOriginals (before : Nat) (xs : List Entry) :
    (annotate before xs).map Prod.fst = xs := by
  induction xs generalizing before with
  | nil => rfl
  | cons e rest ih => simp [annotate, ih]

theorem annotationLength (before : Nat) (xs : List Entry) :
    (annotate before xs).length = xs.length := by
  have h := congrArg List.length (annotationRetainsOriginals before xs)
  simpa only [List.length_map] using h

theorem countAppend (xs ys : List Entry) : voteCount (xs ++ ys) = voteCount xs + voteCount ys := by
  simp [voteCount]

theorem annotationAppend (before : Nat) (xs ys : List Entry) :
    annotate before (xs ++ ys) = annotate before xs ++ annotate (before + voteCount xs) ys := by
  induction xs generalizing before with
  | nil => simp [annotate, voteCount]
  | cons e rest ih =>
    simp only [List.cons_append, annotate, ih, voteCount, List.map_cons, List.sum_cons]
    simp [Nat.add_assoc]

theorem position (before : Nat) (pre : List Entry) (e : Entry) (post : List Entry) :
    (annotate before (pre ++ e :: post))[pre.length]? =
      some (e, before + voteCount pre + increment e) := by
  rw [annotationAppend]
  have length := annotationLength before pre
  rw [← length, List.getElem?_append_right (Nat.le_refl _)]
  simp [annotate]

theorem commandNoVote (before : Nat) (e : Entry) (one : e.kind = 1) :
    (annotate before [e]).map Prod.snd = [before] := by
  simp [annotate, increment, one]

theorem finalizationNoVote (before : Nat) (e : Entry) (three : e.kind = 3) :
    (annotate before [e]).map Prod.snd = [before] := by
  simp [annotate, increment, three]

theorem voteIncrements (before : Nat) (e : Entry) (two : e.kind = 2) :
    (annotate before [e]).map Prod.snd = [before + 1] := by
  simp [annotate, increment, two]

theorem mixed1232 (before : Nat) (a b c d : Entry)
    (ha : a.kind = 1) (hb : b.kind = 2) (hc : c.kind = 3) (hd : d.kind = 2) :
    (annotate before [a, b, c, d]).map Prod.snd =
      [before, before + 1, before + 1, before + 2] := by
  simp [annotate, increment, ha, hb, hc, hd, Nat.add_assoc]

def Continuous (first : Nat) (xs : List Entry) : Prop :=
  ∀ n e, xs[n]? = some e → e.sequence = first + n

theorem physicalPosition {first xs} (continuous : Continuous first xs) (before : Nat)
    {n : Nat} {entry : Entry} {ordinal : Nat} (found : (annotate before xs)[n]? = some (entry, ordinal)) :
    entry.sequence = first + n := by
  have mapped := congrArg (Option.map Prod.fst) found
  rw [← List.getElem?_map, annotationRetainsOriginals] at mapped
  exact continuous n entry (by simpa using mapped)

theorem distinctPhysicalPositions {first xs} (continuous : Continuous first xs) (before : Nat)
    {n m : Nat} {a b : Entry} {va vb : Nat} (ha : (annotate before xs)[n]? = some (a, va))
    (hb : (annotate before xs)[m]? = some (b, vb)) (different : n ≠ m) :
    a.sequence ≠ b.sequence := by
  have left := physicalPosition continuous before ha
  have right := physicalPosition continuous before hb
  omega

theorem noEntryCollapse (before : Nat) {left right : List Entry}
    (equal : annotate before left = annotate before right) : left = right := by
  have h := congrArg (List.map Prod.fst) equal
  simpa only [annotationRetainsOriginals] using h

end Wal

/- Static ticket projection of the existing native lease producer. This
abstracts deadline/request-byte details, which the source decoder must still
check. It does not assert forward simulation of ReassignTicket: native allows
the same worker at the next epoch. That state remains representable here. -/
namespace Ticket

structure Commit where
  worker : Bytes
  epoch : Nat
  content : Bytes
  original : Bytes
  deriving DecidableEq, Repr

structure State where
  ticket : Bytes
  worker : Bytes
  epoch : Nat
  active : Bool
  committed : Option Commit
  history : List Bytes
  deriving DecidableEq, Repr

inductive Action where
  | renew
  | expire
  | reassign (worker : Bytes)
  | commit (content : Bytes)
  | observe
  deriving DecidableEq, Repr

def step (s : State) (action : Action) (original : Bytes) : State :=
  let base := {s with history := s.history ++ [original]}
  match action with
  | .observe => base
  | .renew => base
  | .expire => if s.committed.isNone then {base with active := false} else base
  | .reassign worker =>
      if s.committed.isNone && !s.active then
        {base with worker := worker, epoch := s.epoch + 1, active := true}
      else base
  | .commit content =>
      if s.committed.isNone && s.active then
        {base with committed := some ⟨s.worker, s.epoch, content, original⟩}
      else base

def Consistent (s : State) : Prop :=
  ∀ c, s.committed = some c → c.worker = s.worker ∧ c.epoch = s.epoch ∧
    c.original ∈ s.history

def publicActive (s : State) : Bool := s.active && s.committed.isNone

def initial (ticket worker : Bytes) (original : List Bytes) : State :=
  ⟨ticket,worker,0,true,none,original⟩

theorem initialConsistent (ticket worker original) : Consistent (initial ticket worker original) := by
  intro c h
  contradiction

theorem stepTicket (s action original) : (step s action original).ticket = s.ticket := by
  cases action <;> simp only [step] <;> split <;> rfl

theorem stepHistory (s action original) :
    (step s action original).history = s.history ++ [original] := by
  cases action <;> simp only [step] <;> split <;> rfl

theorem afterCommitStable {s c} (committed : s.committed = some c) (action original) :
    (step s action original).committed = some c ∧
    (step s action original).worker = s.worker ∧
    (step s action original).epoch = s.epoch := by
  cases action <;> simp [step, committed]

theorem stepConsistent {s} (valid : Consistent s) (action original) :
    Consistent (step s action original) := by
  intro c found
  cases h : s.committed with
  | some old =>
      have stable := afterCommitStable h action original
      have same : old = c := Option.some.inj (stable.1.symm.trans found)
      subst c
      obtain ⟨worker, epoch, present⟩ := valid old h
      exact ⟨worker.trans stable.2.1.symm, epoch.trans stable.2.2.symm,
        by rw [stepHistory]; exact List.mem_append_left _ present⟩
  | none =>
      cases action <;> simp [step, h] at found
      case reassign worker =>
        split at found <;> contradiction
      case commit content =>
        split at found
        · cases Option.some.inj found
          simp [step, *]
        · contradiction

def run (s : State) (events : List (Action × Bytes)) : State :=
  events.foldl (fun state event => step state event.1 event.2) s

theorem runConsistent {s} (valid : Consistent s) (events : List (Action × Bytes)) :
    Consistent (run s events) := by
  induction events generalizing s with
  | nil => exact valid
  | cons event rest ih => exact ih (stepConsistent valid event.1 event.2)

theorem runTicket (s events) : (run s events).ticket = s.ticket := by
  induction events generalizing s with
  | nil => rfl
  | cons event rest ih => exact (ih _).trans (stepTicket s event.1 event.2)

theorem runHistory (s events) : (run s events).history = s.history ++ events.map Prod.snd := by
  induction events generalizing s with
  | nil => simp [run]
  | cons event rest ih =>
      change (run (step s event.1 event.2) rest).history = _
      rw [ih, stepHistory]
      simp [List.append_assoc]

theorem runStaticCommitSafety {s} (valid : Consistent s) (events) {c}
    (committed : (run s events).committed = some c) :
    c.worker = (run s events).worker ∧ c.epoch = (run s events).epoch ∧
    c.original ∈ (run s events).history ∧ publicActive (run s events) = false := by
  obtain ⟨worker,epoch,original⟩ := runConsistent valid events c committed
  exact ⟨worker,epoch,original,by simp [publicActive,committed]⟩

theorem sameWorkerRepresentable {s} (empty : s.committed = none) (expired : s.active = false)
    (original) :
    (step s (.reassign s.worker) original).worker = s.worker ∧
    (step s (.reassign s.worker) original).epoch = s.epoch + 1 ∧
    publicActive (step s (.reassign s.worker) original) = true ∧
    (step s (.reassign s.worker) original).ticket = s.ticket := by
  simp [step,empty,expired,publicActive]

end Ticket
end DeltaReduce.ProfileSource
