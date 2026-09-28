import VectorShardRepresentation
import DeltaReduce.RecoveryKernel

/-! Isolated feasibility experiment. A family has ONE original carrier and ONE
control state. Coordinates cannot supply identities, journals or certificates.
This file is not a native/public refinement theorem or mandatory GO artifact. -/
namespace DeltaReduce.BFeasibility
open RecoveryKernel

structure Whole (Original : Type) (width : Nat) (Value : Type := Int) where
  original : Original
  control : State
  values : List Value
  shape : values.length = width

structure Family (Original : Type) (width : Nat) (Value : Type := Int) where
  original : Original
  control : State
  coordinate : Fin width → Value

def project (s : Whole Original width Value) : Family Original width Value :=
  ⟨s.original, s.control, fun k => s.values[k.val]'(by rw [s.shape]; exact k.isLt)⟩

def reconstruct (f : Family Original width Value) : Whole Original width Value :=
  ⟨f.original, f.control, List.ofFn f.coordinate, List.length_ofFn⟩

theorem reconstruct_project (s : Whole Original width Value) : reconstruct (project s) = s := by
  have hv : List.ofFn (project s).coordinate = s.values := by
    apply List.ext_getElem?
    intro k
    by_cases hk : k < width
    · simp [project, hk, s.shape]
    · simp [project, hk, show s.values.length ≤ k by rw [s.shape]; omega]
  cases s
  simp_all [reconstruct, project]

theorem project_reconstruct (f : Family Original width Value) : project (reconstruct f) = f := by
  cases f
  simp [project, reconstruct]

theorem joint_injective {s t : Whole Original width Value} (equal : project s = project t) : s = t := by
  simpa only [reconstruct_project] using congrArg reconstruct equal

/-- Complete ordered serialization. No sort, omission, padding or set collapse. -/
def coordinates (f : Family Original width Value) : List (Nat × Value) :=
  List.ofFn (fun k : Fin width => (k.val, f.coordinate k))

def acceptsCoordinates [DecidableEq Value] (f : Family Original width Value) (rows : List (Nat × Value)) : Bool :=
  decide (rows = coordinates f)

theorem accepted_coordinates_exact [DecidableEq Value] {f : Family Original width Value} {rows}
    (accepted : acceptsCoordinates f rows = true) : rows = coordinates f := by
  simpa [acceptsCoordinates] using accepted

theorem complete_coordinate_domain (f : Family Original width Value) :
    (coordinates f).map Prod.fst = List.range width := by
  simp only [coordinates, List.map_ofFn, Function.comp_def]
  apply List.ext_getElem?
  intro k
  by_cases hk : k < width <;> simp [hk]

theorem ordered_values_exact (s : Whole Original width Value) :
    (coordinates (project s)).map Prod.snd = s.values := by
  have := congrArg Whole.values (reconstruct_project s)
  simpa [coordinates, reconstruct, List.map_ofFn, Function.comp_def] using this

/-- Views expose the same original carrier, not a coordinate-derived protocol ID. -/
def scalarView (f : Family Original width Value) (k : Fin width) : Original × State × Value :=
  (f.original, f.control, f.coordinate k)

theorem one_identity (f : Family Original width Value) (k j : Fin width)
    (observe : Original → α) :
    observe (scalarView f k).1 = observe (scalarView f j).1 := rfl

theorem one_control (f : Family Original width Value) (k j : Fin width) :
    (scalarView f k).2.1 = (scalarView f j).2.1 := rfl

/-- Unchanged existing journal step, executed ONCE on the original carrier.
Its admission, receipt/effect, authentication premises are not erased by views. -/
def wholeStep (a : Adapter) (s : Whole Original width Value) (e : Entry) :
    Option (Whole Original width Value) :=
  (step a s.control e).map (fun next => {s with control := next})

def familyStep (a : Adapter) (f : Family Original width Value) (e : Entry) :
    Option (Family Original width Value) :=
  (step a f.control e).map (fun next => {f with control := next})

theorem step_commutes (a : Adapter) (s : Whole Original width Value) (e : Entry) :
    familyStep a (project s) e = (wholeStep a s e).map project := by
  simp [familyStep, wholeStep, project, Option.map_map, Function.comp_def]

theorem rejection_is_atomic (a : Adapter) (f : Family Original width Value) (e : Entry)
    (rejected : step a f.control e = none) : familyStep a f e = none := by
  simp [familyStep, rejected]

theorem whole_result_of_family_step {a : Adapter} {s : Whole Original width Value} {e f}
    (accepted : familyStep a (project s) e = some f) :
    wholeStep a s e = some (reconstruct f) := by
  rw [step_commutes] at accepted
  cases hs : wholeStep a s e with
  | none => simp [hs] at accepted
  | some t =>
      have hf : project t = f := by simpa [hs] using accepted
      rw [← hf, reconstruct_project]

theorem one_original_record {a : Adapter} {f g : Family Original width Value} {r : Record}
    (accepted : familyStep a f (.vote r) = some g) :
    g.original = f.original ∧ g.coordinate = f.coordinate ∧
    g.control.votes = f.control.votes ++ [r] ∧
    g.control.votes.length = f.control.votes.length + 1 ∧
    g.control.current = f.control.current := by
  unfold familyStep at accepted
  cases hs : step a f.control (.vote r) with
  | none => simp [hs] at accepted
  | some next =>
      have hg : {f with control := next} = g := by simpa [hs] using accepted
      subst g
      cases stepSound hs with
      | vote admitted => simp

theorem original_record_checks_retained {a : Adapter} {f g : Family Original width Value} {r}
    (accepted : familyStep a f (.vote r) = some g) : validVote a f.control r := by
  unfold familyStep at accepted
  cases hs : step a f.control (.vote r) with
  | none => simp [hs] at accepted
  | some next => cases stepSound hs with | vote admitted => exact admitted

/-- A finite same-event history uses the original replay function once, not width times. -/
def familyReplay (a : Adapter) (f : Family Original width Value) (entries : List Entry) :
    Option (Family Original width Value) :=
  (replay a f.control entries).map (fun next => {f with control := next})

theorem history_keeps_exact_original_records {a : Adapter} {f g : Family Original width Value} {es}
    (accepted : familyReplay a f es = some g) :
    g.original = f.original ∧ g.coordinate = f.coordinate ∧
    g.control.votes = f.control.votes ++ voteRecords es := by
  unfold familyReplay at accepted
  cases hs : replay a f.control es with
  | none => simp [hs] at accepted
  | some next =>
      have hg : {f with control := next} = g := by simpa [hs] using accepted
      subst g
      exact ⟨rfl, rfl, replayExactRecords hs⟩

/-- Coordinate-free common control and action label, with the SAME index for every
view. ScalarStep is instantiated by unchanged production TLA actions in the
finite harness. This lemma is a lifting rule, not a proof of its premises. -/
def Synchronized (R : Original → State → State → Value → Value → Prop)
    (before after : Family Original width Value) : Prop :=
  after.original = before.original ∧
  ∀ k : Fin width, R before.original before.control after.control
    (before.coordinate k) (after.coordinate k)

theorem synchronized_reconstruct
    {R : Original → State → State → Value → Value → Prop}
    {before after : Family Original width Value}
    (sync : Synchronized R before after) :
    (reconstruct after).original = (reconstruct before).original ∧
    ∀ k : Fin width, R before.original before.control after.control
      ((reconstruct before).values[k.val]'(by simp [reconstruct]))
      ((reconstruct after).values[k.val]'(by simp [reconstruct])) := by
  simpa [Synchronized, reconstruct] using sync

/-- Existing checked scalar arithmetic is used at each coordinate with identical
width-independent guards and the original row order; no supplied result equality. -/
theorem checked_parameter_family {lo hi inputLo inputHi denominator width rows values}
    (native : ParameterKernel.checkedParameter lo hi inputLo inputHi denominator width rows = some values)
    (original : Original) (control : State) :
    ∃ s : Whole Original width, s.original = original ∧ s.control = control ∧
      s.values = values ∧ reconstruct (project s) = s ∧
      ∀ k : Fin width, ParameterKernel.checkedParameter lo hi inputLo inputHi denominator 1
        (rows.map (VectorShardRepresentation.rowAt k.val)) = some [(project s).coordinate k] := by
  have shape := (ParameterKernel.checkedParameterSound _ _ _ _ _ _ _ _ native).2.2.1
  let s : Whole Original width := ⟨original, control, values, shape⟩
  refine ⟨s, rfl, rfl, rfl, reconstruct_project s, ?_⟩
  intro k
  obtain ⟨value, atIndex, computed⟩ := VectorShardRepresentation.scalarParameterIsCoordinate native k.val k.isLt
  have hv : (project s).coordinate k = value := by
    simpa [project, s] using (List.getElem?_eq_some_iff.mp atIndex).2
  simpa [hv] using computed

def exampleControl : State := ⟨[], ⟨[], [], []⟩⟩
def exampleFamily : Family String 3 := project ⟨"original-s01", exampleControl, [3,-4,5], rfl⟩
theorem exampleRoundTrip : (reconstruct exampleFamily).values = [3,-4,5] := by decide
theorem exampleComplete : acceptsCoordinates exampleFamily [(0,3),(1,-4),(2,5)] = true := by decide
theorem exampleMissing : acceptsCoordinates exampleFamily [(0,3),(2,5)] = false := by decide
theorem exampleReordered : acceptsCoordinates exampleFamily [(2,5),(1,-4),(0,3)] = false := by decide
theorem exampleDuplicate : acceptsCoordinates exampleFamily [(0,3),(1,-4),(1,-4),(2,5)] = false := by decide
theorem exampleChanged : acceptsCoordinates exampleFamily [(0,3),(1,4),(2,5)] = false := by decide

end DeltaReduce.BFeasibility
