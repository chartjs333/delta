import ProfileSeedIntent
import ProfileSeedKnowledge

/-! T047/T053 source membership composition for the existing local kernels.
`decodePrepare` is the deterministic body/reference decoder, not a safety oracle.
This theorem does not authenticate signatures or prove the Python extractor.
It replaces no-double-prepare/status-floor assumptions by explicit original
intent and knowledge trace membership. The complete byte/source join must supply
those traces; no public-state/refinement result is a premise.
-/
namespace DeltaReduce.ProfileSeedSource
open ProfileSeedIntent (Bytes)
variable {Value : Type} [DecidableEq Value]

structure LocalHistory (Value : Type) [DecidableEq Value] where
  originalIntents : List ProfileSeedIntent.Intent
  intentState : ProfileSeedIntent.State
  knowledgeState : ProfileSeedKnowledge.State Value
  intentRun : ProfileSeedIntent.Run originalIntents intentState
  knowledgeRun : ProfileSeedKnowledge.Run knowledgeState

def Prepared (decodePrepare : Bytes → Option Value) (h : LocalHistory Value)
    (view : Nat) (value : Value) : Prop :=
  ∃ i ∈ h.originalIntents, i.key = ⟨.prepare,view⟩ ∧ decodePrepare i.body = some value

def Committed (h : LocalHistory Value) (view : Nat) (value : Value) : Prop :=
  (view,value) ∈ h.knowledgeState.commits

def Reported (h : LocalHistory Value) (target : Nat)
    (report : Option (Nat × Value)) : Prop :=
  (target,report) ∈ h.knowledgeState.reports

theorem originalPrepareBodyUnique (h : LocalHistory Value)
    {left right : ProfileSeedIntent.Intent}
    (hl : left ∈ h.originalIntents) (hr : right ∈ h.originalIntents)
    (sameKey : left.key = right.key) : left.body = right.body :=
  ProfileSeedIntent.noConflictingAcceptedBodies h.intentRun hl hr sameKey

theorem prepareValueUnique (decodePrepare : Bytes → Option Value)
    (h : LocalHistory Value) {view left right}
    (hl : Prepared decodePrepare h view left) (hr : Prepared decodePrepare h view right) :
    left = right := by
  obtain ⟨il,hil,kl,dl⟩ := hl
  obtain ⟨ir,hir,kr,dr⟩ := hr
  have bytes := originalPrepareBodyUnique h hil hir (kl.trans kr.symm)
  rw [bytes] at dl
  exact Option.some.inj (dl.symm.trans dr)

theorem originalCommitStatusFloor (h : LocalHistory Value)
    {view value target report} (hc : Committed h view value)
    (hr : Reported h target report) (later : view < target) :
    ∃ w y, report = some (w,y) ∧ view ≤ w :=
  ProfileSeedKnowledge.commitStatusFloor h.knowledgeRun hc hr later

/- Whole source order/multiplicity is independent of accepting a protocol step.
The concrete extractor supplies one outcome per original event, including other
handlers, rejected calls and unresolved physical/output assertions. Matching
prefixes does not manufacture success for any of those cases. -/
inductive Disposition where
  | accepted | rejected | other | unresolved
  deriving DecidableEq, Repr

structure OriginalEvent where
  descriptor : Bytes
  original : Bytes
  inputs : List Bytes
  dependencies : List Nat
  deriving DecidableEq, Repr

structure Outcome where
  original : OriginalEvent
  disposition : Disposition
  deriving DecidableEq, Repr

def complete (originals : List OriginalEvent) (outcomes : List Outcome) : Bool :=
  decide (outcomes.map Outcome.original = originals)

theorem completeOriginals {originals outcomes} (ok : complete originals outcomes = true) :
    outcomes.map Outcome.original = originals := by
  simpa [complete] using ok

theorem completeLength {originals outcomes} (ok : complete originals outcomes = true) :
    outcomes.length = originals.length := by
  have same := congrArg List.length (completeOriginals ok)
  simpa using same

theorem completePosition {originals outcomes} (ok : complete originals outcomes = true)
    {index : Nat} {event : OriginalEvent} (found : originals[index]? = some event) :
    ∃ result : Outcome, outcomes[index]? = some result ∧ result.original = event := by
  rw [← completeOriginals ok] at found
  rw [List.getElem?_map] at found
  cases h : outcomes[index]? with
  | none => simp [h] at found
  | some value =>
    exact ⟨value,rfl,by simpa [h] using found⟩

def resolved (outcomes : List Outcome) : Bool :=
  outcomes.all (fun o => o.disposition != .unresolved)

theorem unresolvedSuffixCannotRepair {before after : List Outcome}
    (bad : resolved before = false) : resolved (before ++ after) = false := by
  rw [resolved,List.all_append]
  change (resolved before && resolved after) = false
  rw [bad]
  rfl

#print axioms originalPrepareBodyUnique
#print axioms prepareValueUnique
#print axioms originalCommitStatusFloor
#print axioms completeOriginals
#print axioms completeLength
#print axioms completePosition
#print axioms unresolvedSuffixCannotRepair
end DeltaReduce.ProfileSeedSource
