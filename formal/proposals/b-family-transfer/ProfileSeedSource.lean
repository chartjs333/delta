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

/- Finite source-family composition. The concrete decoder supplies the original
instance key and full event (including inputs/cut); the local step includes its
accepted/rejected/unresolved outcome. Projection never filters source positions.
This algebra does not authenticate the catalog or discharge a missing key. -/
namespace InstanceDispatch
variable {State Payload : Type}

structure Event (Payload : Type) where
  instanceKey : Bytes
  original : Payload

def step (advance : State → Payload → State) (states : Bytes → Option State)
    (event : Event Payload) : Bytes → Option State :=
  match states event.instanceKey with
  | none => states
  | some before => fun key =>
      if key = event.instanceKey then some (advance before event.original) else states key

def facet (advance : State → Payload → State) (key : Bytes) (state : Option State)
    (event : Event Payload) : Option State :=
  if key = event.instanceKey then state.map (fun before => advance before event.original) else state

theorem stepProjection (advance : State → Payload → State) (states : Bytes → Option State)
    (event : Event Payload) (key : Bytes) :
    step advance states event key = facet advance key (states key) event := by
  by_cases same : key = event.instanceKey
  · subst key
    cases h : states event.instanceKey <;> simp [step,facet,h]
  · cases h : states event.instanceKey <;> simp [step,facet,h,same]

theorem otherInstanceUnchanged (advance : State → Payload → State)
    (states : Bytes → Option State) (event : Event Payload) (key : Bytes)
    (other : key ≠ event.instanceKey) : step advance states event key = states key := by
  rw [stepProjection]
  simp [facet,other]

theorem completePrefixProjection (advance : State → Payload → State)
    (states : Bytes → Option State) (events : List (Event Payload)) (key : Bytes) :
    (events.foldl (step advance) states) key =
      events.foldl (facet advance key) (states key) := by
  induction events generalizing states with
  | nil => rfl
  | cons event rest ih =>
    simp only [List.foldl_cons]
    rw [ih,stepProjection]

def covered (states : Bytes → Option State) (events : List (Event Payload)) : Bool :=
  events.all (fun event => (states event.instanceKey).isSome)

theorem coverageRequiresEveryOriginal (states : Bytes → Option State)
    (events : List (Event Payload)) (ok : covered states events = true)
    (event : Event Payload) (member : event ∈ events) :
    ∃ state, states event.instanceKey = some state := by
  have present := (List.all_eq_true.mp ok) event member
  cases h : states event.instanceKey with
  | none => simp [h] at present
  | some state => exact ⟨state,rfl⟩

end InstanceDispatch

#print axioms originalPrepareBodyUnique
#print axioms prepareValueUnique
#print axioms originalCommitStatusFloor
#print axioms completeOriginals
#print axioms completeLength
#print axioms completePosition
#print axioms unresolvedSuffixCannotRepair
#print axioms InstanceDispatch.stepProjection
#print axioms InstanceDispatch.otherInstanceUnchanged
#print axioms InstanceDispatch.completePrefixProjection
#print axioms InstanceDispatch.coverageRequiresEveryOriginal
end DeltaReduce.ProfileSeedSource
