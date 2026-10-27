import Std

/-! T047/T053 local causal STATUS floor, derived from a concrete empty-start
knowledge/commit/view machine. Received prepared certificates are annotations
whose byte authentication is checked separately. They are NOT a global safety
premise. The model overapproximates learn; it never discards earlier knowledge.
-/
namespace DeltaReduce.ProfileSeedKnowledge
variable {Value : Type} [DecidableEq Value]
abbrev Entry (Value : Type) := Nat × Value

def highest : List (Entry Value) → Option (Entry Value)
  | [] => none
  | x::xs => match highest xs with
    | none => some x
    | some y => some (if x.1 < y.1 then y else x)

def Covers (report : Option (Entry Value)) (v : Nat) : Prop :=
  ∃ w y, report = some (w,y) ∧ v ≤ w

omit [DecidableEq Value] in
theorem highestCovers {xs : List (Entry Value)} {x} (member : x ∈ xs) :
    Covers (highest xs) x.1 := by
  induction xs with
  | nil => simp at member
  | cons h tail ih =>
    simp only [List.mem_cons] at member
    cases eq : highest tail with
    | none =>
      rcases member with same | old
      · subst x; exact ⟨h.1,h.2,by simp [highest,eq],Nat.le_refl _⟩
      · obtain ⟨w,y,found,_⟩ := ih old
        simp [eq] at found
    | some best =>
      by_cases better : h.1 < best.1
      · rcases member with same | old
        · subst x; exact ⟨best.1,best.2,by simp [highest,eq,better],by omega⟩
        · obtain ⟨w,y,found,bound⟩ := ih old
          have same : best = (w,y) := Option.some.inj (eq.symm.trans found)
          exact ⟨best.1,best.2,by simp [highest,eq,better],by simpa [same] using bound⟩
      · rcases member with same | old
        · subst x; exact ⟨h.1,h.2,by simp [highest,eq,better],Nat.le_refl _⟩
        · obtain ⟨w,y,found,bound⟩ := ih old
          have same : best = (w,y) := Option.some.inj (eq.symm.trans found)
          have le : x.1 ≤ best.1 := by simpa [same] using bound
          exact ⟨h.1,h.2,by simp [highest,eq,better],by omega⟩

structure State (Value : Type) where
  view : Nat
  known : List (Entry Value)
  commits : List (Entry Value)
  reports : List (Nat × Option (Entry Value))
  deriving DecidableEq, Repr
def initial : State Value := ⟨0,[],[],[]⟩
inductive Action (Value : Type) where
  | learn (entry : Entry Value)
  | commit (entry : Entry Value)
  | status (target : Nat)
  deriving DecidableEq, Repr
def summary (s : State Value) := highest (s.known.filter (fun e => decide (e.1 ≤ s.view)))
def step (s : State Value) : Action Value → Option (State Value)
  | .learn entry => some {s with known := s.known ++ [entry]}
  | .commit entry => if entry.1 = s.view ∧ entry ∈ s.known then
      some {s with commits := s.commits ++ [entry]} else none
  | .status target => if s.view < target then
      some {s with view := target, reports := s.reports ++ [(target,summary s)]} else none

def Good (s : State Value) : Prop :=
  (∀ e ∈ s.commits, e.1 ≤ s.view ∧ e ∈ s.known) ∧
  (∀ r ∈ s.reports, r.1 ≤ s.view) ∧
  (∀ r ∈ s.reports, ∀ e ∈ s.commits, e.1 < r.1 → Covers r.2 e.1)

theorem stepGood {s : State Value} {action out}
    (before : Good s) (ok : step s action = some out) : Good out := by
  obtain ⟨commits,reports,floor⟩ := before
  cases action with
  | learn entry =>
    cases Option.some.inj ok
    exact ⟨fun e he => ⟨(commits e he).1,List.mem_append_left _ (commits e he).2⟩,
      reports,floor⟩
  | commit entry =>
    simp only [step] at ok
    split at ok <;> try contradiction
    rename_i guard
    cases Option.some.inj ok
    refine ⟨?_,reports,?_⟩
    · intro e he
      simp only [List.mem_append,List.mem_singleton] at he
      rcases he with old | same
      · exact commits e old
      · subst e; exact ⟨Nat.le_of_eq guard.1,guard.2⟩
    · intro r hr e he later
      simp only [List.mem_append,List.mem_singleton] at he
      rcases he with old | same
      · exact floor r hr e old later
      · subst e; have bound := reports r hr; have eq := guard.1; omega
  | status target =>
    simp only [step] at ok
    split at ok <;> try contradiction
    rename_i advance
    cases Option.some.inj ok
    refine ⟨?_,?_,?_⟩
    · intro e he
      have old := commits e he
      change e.1 ≤ target ∧ e ∈ s.known
      exact ⟨by omega,old.2⟩
    · intro r hr
      simp only [List.mem_append,List.mem_singleton] at hr
      rcases hr with old | same
      · change r.1 ≤ target
        have bound := reports r old; exact by omega
      · subst r; exact Nat.le_refl _
    · intro r hr e he later
      simp only [List.mem_append,List.mem_singleton] at hr
      rcases hr with old | same
      · exact floor r old e he later
      · subst r
        have known := commits e he
        exact highestCovers (by simp [List.mem_filter,known.1,known.2])

inductive Run : State Value → Prop
  | start : Run initial
  | next {s out action} : Run s → step s action = some out → Run out
theorem runGood {s : State Value} (run : Run s) : Good s := by
  induction run with
  | start => simp [Good,initial]
  | next prior ok ih => exact stepGood ih ok

theorem commitStatusFloor {s : State Value} (run : Run s)
    {e r} (commit : e ∈ s.commits) (status : r ∈ s.reports) (later : e.1 < r.1) :
    ∃ w y, r.2 = some (w,y) ∧ e.1 ≤ w :=
  (runGood run).2.2 r status e commit later

#print axioms highestCovers
#print axioms stepGood
#print axioms runGood
#print axioms commitStatusFloor
end DeltaReduce.ProfileSeedKnowledge
