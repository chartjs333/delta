import DeltaReduce.PublicState

/-! Checked complete first-vote effects. This derives the four assigned fields
of VoteParameter/VoteApply and retains the other sixty. It does not establish
the arithmetic/certificate guards, TLA Next, exporter trust or native recovery. -/
namespace DeltaReduce.PublicVoteEffects
open PublicState

/-- Insert by canonical byte order. Structural equality removes an existing
member; a byte collision cannot certify canonicality (the observation loader
checks strict byte ordering separately). -/
def insert (value : Value) : Values → Values
  | .nil => .cons value .nil
  | .cons head tail =>
    if value = head then .cons head tail
    else if byteLess (encode value) (encode head) then .cons value (.cons head tail)
    else .cons head (insert value tail)

theorem insertBefore {value head tail} (different : value ≠ head)
    (less : byteLess (encode value) (encode head) = true) :
    insert value (.cons head tail) = .cons value (.cons head tail) := by
  simp only [insert, if_neg different, less, if_true]

theorem insertAfter {value head tail} (different : value ≠ head)
    (less : byteLess (encode value) (encode head) = false) :
    insert value (.cons head tail) = .cons head (insert value tail) := by
  simp only [insert, if_neg different, less, Bool.false_eq_true, if_false]

theorem byteLessReverse {a b : NativeBinding.Bytes} (less : byteLess a b = true) :
    byteLess b a = false := by
  apply Bool.eq_false_iff.mpr
  intro opposite
  exact List.lt_asymm ((byteLessCorrect a b).mp less) ((byteLessCorrect b a).mp opposite)

theorem insertMembership (value item : Value) (values : Values) :
    item ∈ valuesList (insert value values) ↔ item = value ∨ item ∈ valuesList values := by
  cases values with
  | nil => simp [insert, valuesList]
  | cons head tail =>
    simp only [insert]
    split
    · rename_i same
      subst head
      simp [valuesList]
    · split
      · simp [valuesList]
      · simp only [valuesList, List.mem_cons, insertMembership value item tail]
        simp only [or_left_comm]

theorem insertRetains (value item : Value) (values : Values)
    (old : item ∈ valuesList values) : item ∈ valuesList (insert value values) :=
  (insertMembership value item values).mpr (Or.inr old)

theorem insertAdds (value : Value) (values : Values) :
    value ∈ valuesList (insert value values) :=
  (insertMembership value value values).mpr (Or.inl rfl)

/-- Updating values retains all function domains and their order. All matching
keys are updated, so the lookup property also holds on a raw typed input;
loaded canonical functions additionally have unique ordered domains. -/
def update (key value : Value) : Entries → Entries
  | .nil => .nil
  | .cons k v tail => .cons k (if k = key then value else v) (update key value tail)

theorem updateKeys (key value : Value) (entries : Entries) :
    keys (update key value entries) = keys entries := by
  cases entries with
  | nil => rfl
  | cons k v tail => simp only [update, keys, updateKeys key value tail]

theorem updateLookup (key value query : Value) (entries : Entries) :
    functionLookup query (update key value entries) =
      (functionLookup query entries).map (fun old => if query = key then value else old) := by
  cases entries with
  | nil => rfl
  | cons k v tail =>
    by_cases same : k = query
    · subst k; simp [update, functionLookup]
    · simp [update, functionLookup, same, updateLookup key value query tail]

theorem updateSelected {key value old entries}
    (found : functionLookup key entries = some old) :
    functionLookup key (update key value entries) = some value := by
  rw [updateLookup, found]; simp

theorem updateOther {key value query entries} (other : query ≠ key) :
    functionLookup query (update key value entries) = functionLookup query entries := by
  rw [updateLookup]; simp [other]

def envelope (vote : Vote) : Value := .function (voteEntries vote)
def phaseVote (vote : Vote) : Value :=
  .function (.cons (.text "body") vote.body (.cons (.text "validator") vote.actor .nil))

def collection (vote : Vote) : Option String :=
  if vote.kind = .text "PARAMETER" then some "parameterVotes"
  else if vote.kind = .text "APPLY" then some "applyVotes" else none

theorem collectionKinds {vote name} (found : collection vote = some name) :
    (vote.kind = .text "PARAMETER" ∧ name = "parameterVotes") ∨
    (vote.kind = .text "APPLY" ∧ name = "applyVotes") := by
  unfold collection at found
  split at found
  · rename_i same; exact Or.inl ⟨same, (Option.some.inj found).symm⟩
  · split at found
    · rename_i same; exact Or.inr ⟨same, (Option.some.inj found).symm⟩
    · contradiction

/-- Independently read source fields; no expected after-state, sequence or
result is supplied to the reader. -/
structure Inputs (before : State) (vote : Vote) where
  name : String
  kind : collection vote = some name
  durable : Values
  volatile : Values
  phaseVotes : Values
  sequences : Entries
  oldSequence : Nat
  durableSource : before.read "durableVotes" = some (.set durable)
  volatileSource : before.read "volatileVotes" = some (.set volatile)
  phaseSource : before.read name = some (.set phaseVotes)
  sequenceSource : before.read "durableSequence" = some (.function sequences)
  actorSource : functionLookup vote.actor sequences = some (.integer oldSequence)

def readInputs (before : State) (vote : Vote) : Option (Inputs before vote) := do
  let name ← collection vote
  match hd : before.read "durableVotes", hv : before.read "volatileVotes",
      hp : before.read name, hs : before.read "durableSequence" with
  | some (.set durable), some (.set volatile), some (.set phaseVotes), some (.function sequences) =>
    match ha : functionLookup vote.actor sequences with
    | some (.integer n) =>
      if hn : 0 ≤ n then
        if hk : collection vote = some name then
          some ⟨name,hk,durable,volatile,phaseVotes,sequences,n.toNat,hd,hv,hp,hs,
            by simpa only [Int.toNat_of_nonneg hn] using ha⟩
        else none
      else none
    | _ => none
  | _, _, _, _ => none

def assigned (name : String) : List String :=
  ["durableVotes", "volatileVotes", "durableSequence", name]

def nextValue {before vote} (input : Inputs before vote) (name : String) (old : Value) : Value :=
  if name = "durableVotes" then .set (insert (envelope vote) input.durable)
  else if name = "volatileVotes" then .set (insert (envelope vote) input.volatile)
  else if name = "durableSequence" then
    .function (update vote.actor (.integer (input.oldSequence + 1)) input.sequences)
  else if name = input.name then .set (insert (phaseVote vote) input.phaseVotes)
  else old

def expected {before vote} (input : Inputs before vote) : State :=
  ⟨before.rows.map (fun (name,old) => (name,nextValue input name old)),
    by simpa only [List.map_map, Function.comp_def] using before.complete⟩

theorem lookupMapped (rows : List (String × Value)) (f : String → Value → Value) (name : String) :
    lookup name (rows.map (fun (k,v) => (k,f k v))) = (lookup name rows).map (f name) := by
  induction rows with
  | nil => rfl
  | cons head tail ih =>
    rcases head with ⟨key,value⟩
    by_cases same : key = name
    · subst key; simp [lookup]
    · simp [lookup, same, ih]

theorem expectedReads {before vote} (input : Inputs before vote) (name : String) :
    (expected input).read name = (before.read name).map (nextValue input name) :=
  lookupMapped before.rows (nextValue input) name

theorem expectedUnchanged {before vote} (input : Inputs before vote) {name}
    (unchanged : name ∉ assigned input.name) : (expected input).read name = before.read name := by
  have hd : name ≠ "durableVotes" := by intro h; apply unchanged; simp [assigned, h]
  have hv : name ≠ "volatileVotes" := by intro h; apply unchanged; simp [assigned, h]
  have hs : name ≠ "durableSequence" := by intro h; apply unchanged; simp [assigned, h]
  have hp : name ≠ input.name := by intro h; apply unchanged; simp [assigned, h]
  rw [expectedReads input name]
  have identity : nextValue input name = id := by
    funext old
    simp [nextValue, hd, hv, hs, hp]
  rw [identity]
  simp

theorem expectedDurable {before vote} (input : Inputs before vote) :
    (expected input).read "durableVotes" = some (.set (insert (envelope vote) input.durable)) := by
  rw [expectedReads, input.durableSource]; simp [nextValue]

theorem expectedVolatile {before vote} (input : Inputs before vote) :
    (expected input).read "volatileVotes" = some (.set (insert (envelope vote) input.volatile)) := by
  rw [expectedReads, input.volatileSource]; simp [nextValue]

theorem expectedSequences {before vote} (input : Inputs before vote) :
    (expected input).read "durableSequence" =
      some (.function (update vote.actor (.integer (input.oldSequence + 1)) input.sequences)) := by
  rw [expectedReads, input.sequenceSource]; simp [nextValue]

theorem expectedPhaseVotes {before vote} (input : Inputs before vote) :
    (expected input).read input.name = some (.set (insert (phaseVote vote) input.phaseVotes)) := by
  rw [expectedReads, input.phaseSource]
  rcases collectionKinds input.kind with h | h
  · simp [nextValue, h.2]
  · simp [nextValue, h.2]

theorem expectedActorSequence {before vote} (input : Inputs before vote) :
    ((expected input).read "durableSequence" >>= fun f => readFunction f vote.actor) =
      some (.integer (input.oldSequence + 1)) := by
  rw [expectedSequences]
  exact updateSelected input.actorSource

theorem expectedOtherSequence {before vote} (input : Inputs before vote) {actor}
    (other : actor ≠ vote.actor) :
    ((expected input).read "durableSequence" >>= fun f => readFunction f actor) =
      (before.read "durableSequence" >>= fun f => readFunction f actor) := by
  rw [expectedSequences, input.sequenceSource]
  exact updateOther other

theorem exactFourAssigned {before vote} (input : Inputs before vote) :
    (assigned input.name).Nodup ∧ (assigned input.name).length = 4 ∧
      ∀ name ∈ assigned input.name, name ∈ fieldNames := by
  rcases collectionKinds input.kind with h | h
  · rw [h.2]; decide
  · rw [h.2]; decide

structure Checked (before after : State) (actor : Value) where
  first : First before after actor
  inputs : Inputs before first.vote
  exactRows : after.rows = (expected inputs).rows

/-- Compare every one of the 64 fields against computed effects. The equality
is a checked output witness, never an argument supplied by the caller. -/
def check (before after : State) (actor : Value) : Option (Checked before after actor) := do
  let first ← extractFirst before after actor
  let inputs ← readInputs before first.vote
  if exactRows : after.rows = (expected inputs).rows then
    some ⟨first,inputs,exactRows⟩ else none

theorem checkFromComputed {before after actor} (first : First before after actor)
    (inputs : Inputs before first.vote)
    (extracted : extractFirst before after actor = some first)
    (read : readInputs before first.vote = some inputs)
    (rows : after.rows = (expected inputs).rows) : (check before after actor).isSome = true := by
  simp [check, extracted, read, rows, Bind.bind, Option.bind]

theorem checkedRead {before after actor} (checked : Checked before after actor) (name : String) :
    after.read name = (expected checked.inputs).read name :=
  congrArg (lookup name) checked.exactRows

theorem checkedUnchanged {before after actor} (checked : Checked before after actor) {name}
    (unchanged : name ∉ assigned checked.inputs.name) : after.read name = before.read name :=
  (checkedRead checked name).trans (expectedUnchanged checked.inputs unchanged)

theorem checkedNoMessageExposure {before after actor} (checked : Checked before after actor) :
    after.read "messages" = before.read "messages" ∧
    after.read "messageMultiplicity" = before.read "messageMultiplicity" ∧
    after.read "receivedVotes" = before.read "receivedVotes" := by
  have unchanged : ∀ name ∈ ["messages", "messageMultiplicity", "receivedVotes"],
      name ∉ assigned checked.inputs.name := by
    rcases collectionKinds checked.inputs.kind with h | h
    · rw [h.2]; decide
    · rw [h.2]; decide
  exact ⟨checkedUnchanged checked (unchanged _ (by simp)),
    checkedUnchanged checked (unchanged _ (by simp)),
    checkedUnchanged checked (unchanged _ (by simp))⟩

theorem checkedNoCurrentAdvance {before after actor} (checked : Checked before after actor) :
    after.read "currentCheckpoint" = before.read "currentCheckpoint" := by
  apply checkedUnchanged checked
  rcases collectionKinds checked.inputs.kind with h | h
  · rw [h.2]; decide
  · rw [h.2]; decide

theorem unassignedMutationRejected {before after actor name}
    (parameter : name ∉ assigned "parameterVotes")
    (applyVote : name ∉ assigned "applyVotes")
    (changed : after.read name ≠ before.read name) : check before after actor = none := by
  cases result : check before after actor with
  | none => rfl
  | some checked =>
    have unchanged : name ∉ assigned checked.inputs.name := by
      rcases collectionKinds checked.inputs.kind with h | h
      · simpa only [h.2] using parameter
      · simpa only [h.2] using applyVote
    exact False.elim (changed (checkedUnchanged checked unchanged))

theorem checkedSequenceAllocatedFromPrior {before after actor} (checked : Checked before after actor) :
    checked.inputs.oldSequence = checked.first.prior.data.sequence ∧
    checked.inputs.oldSequence + 1 = checked.first.next.data.sequence := by
  have prior := checked.first.prior.bound.2.2.2.1
  rw [checked.inputs.sequenceSource] at prior
  change functionLookup actor checked.inputs.sequences =
    some (.integer checked.first.prior.data.sequence) at prior
  have same := congrArg (fun a => functionLookup a checked.inputs.sequences) checked.first.checked.1
  have equal : checked.inputs.oldSequence = checked.first.prior.data.sequence := by
    have values := Option.some.inj (checked.inputs.actorSource.symm.trans (same.trans prior))
    exact Int.ofNat_inj.mp (Value.integer.inj values)
  exact ⟨equal, by rw [equal]; exact checked.first.sequence.symm⟩

theorem checkedOtherSequenceUnchanged {before after actor} (checked : Checked before after actor)
    {other} (different : other ≠ actor) :
    (after.read "durableSequence" >>= fun f => readFunction f other) =
      (before.read "durableSequence" >>= fun f => readFunction f other) := by
  rw [checkedRead checked "durableSequence"]
  exact expectedOtherSequence checked.inputs (by simpa only [checked.first.checked.1] using different)

theorem messageMutationRejected {before after actor}
    (changed : after.read "messages" ≠ before.read "messages") : check before after actor = none := by
  cases result : check before after actor with
  | none => rfl
  | some checked => exact False.elim (changed (checkedNoMessageExposure checked).1)

theorem checkedDurableMembership {before after actor} (checked : Checked before after actor) (item : Value) :
    (after.read "durableVotes" >>= readSet).any (fun xs => xs.contains item) = true ↔
      item = envelope checked.first.vote ∨ item ∈ valuesList checked.inputs.durable := by
  rw [checkedRead checked "durableVotes", expectedDurable checked.inputs]
  change (valuesList (insert (envelope checked.first.vote) checked.inputs.durable)).contains item = true ↔ _
  rw [List.contains_iff_mem]
  exact insertMembership (envelope checked.first.vote) item checked.inputs.durable

theorem checkedPhaseMembership {before after actor} (checked : Checked before after actor) (item : Value) :
    (after.read checked.inputs.name >>= readSet).any (fun xs => xs.contains item) = true ↔
      item = phaseVote checked.first.vote ∨ item ∈ valuesList checked.inputs.phaseVotes := by
  rw [checkedRead checked checked.inputs.name, expectedPhaseVotes checked.inputs]
  change (valuesList (insert (phaseVote checked.first.vote) checked.inputs.phaseVotes)).contains item = true ↔ _
  rw [List.contains_iff_mem]
  exact insertMembership (phaseVote checked.first.vote) item checked.inputs.phaseVotes

theorem emptyVolatileRejected {before after actor}
    (empty : after.read "volatileVotes" = some (.set .nil)) : check before after actor = none := by
  cases result : check before after actor with
  | none => rfl
  | some checked =>
    have h := (checkedRead checked "volatileVotes").trans (expectedVolatile checked.inputs)
    rw [empty] at h
    have shapes := Value.set.inj (Option.some.inj h)
    have member := insertAdds (envelope checked.first.vote) checked.inputs.volatile
    rw [← shapes] at member
    exact False.elim (List.not_mem_nil member)

theorem emptyPhaseRejected {before after actor}
    (parameter : after.read "parameterVotes" = some (.set .nil))
    (applyVote : after.read "applyVotes" = some (.set .nil)) : check before after actor = none := by
  cases result : check before after actor with
  | none => rfl
  | some checked =>
    have empty : after.read checked.inputs.name = some (.set .nil) := by
      rcases collectionKinds checked.inputs.kind with h | h
      · simpa only [h.2] using parameter
      · simpa only [h.2] using applyVote
    have h := (checkedRead checked checked.inputs.name).trans (expectedPhaseVotes checked.inputs)
    rw [empty] at h
    have shapes := Value.set.inj (Option.some.inj h)
    have member := insertAdds (phaseVote checked.first.vote) checked.inputs.phaseVotes
    rw [← shapes] at member
    exact False.elim (List.not_mem_nil member)

theorem otherSequenceMutationRejected {before after actor other}
    (different : other ≠ actor)
    (changed : (after.read "durableSequence" >>= fun f => readFunction f other) ≠
      (before.read "durableSequence" >>= fun f => readFunction f other)) :
    check before after actor = none := by
  cases result : check before after actor with
  | none => rfl
  | some checked => exact False.elim (changed (checkedOtherSequenceUnchanged checked different))

/-- Complete preimages are loaded by the previous layer, then the computed
footprint is checked; neither root equality nor authentication is assumed. -/
structure Projected (models : List String) (identity : Identity)
    (sha256 : NativeBinding.Bytes → NativeBinding.ContentId)
    (before after : Observation) (actor : Value) where
  prior : Loaded models identity sha256 before
  next : Loaded models identity sha256 after
  effects : Checked prior.state next.state actor

def project (models : List String) (identity : Identity)
    (sha256 : NativeBinding.Bytes → NativeBinding.ContentId)
    (before after : Observation) (actor : Value) :
    Option (Projected models identity sha256 before after actor) := do
  let prior ← load models identity sha256 before
  let next ← load models identity sha256 after
  let effects ← check prior.state next.state actor
  some ⟨prior,next,effects⟩

theorem projectFromLoaded {models identity sha256 before after actor}
    (prior : Loaded models identity sha256 before)
    (next : Loaded models identity sha256 after)
    (accepted : (check prior.state next.state actor).isSome = true) :
    (project models identity sha256 before after actor).isSome = true := by
  simp only [project, loadProvided prior, loadProvided next, Bind.bind, Option.bind]
  cases result : check prior.state next.state actor with
  | none => simp only [result, Option.isSome_none, Bool.false_eq_true] at accepted
  | some effects => rfl

theorem projectedCompletePreimages {models identity sha256 before after actor}
    (p : Projected models identity sha256 before after actor) :
    before.bytes = documentBytes identity p.prior.state ∧
    after.bytes = documentBytes identity p.next.state ∧
    sha256 (preimage identity p.prior.state) = before.root ∧
    sha256 (preimage identity p.next.state) = after.root :=
  ⟨(loadedCompletePreimage p.prior).1,(loadedCompletePreimage p.next).1,
    (loadedCompletePreimage p.prior).2,(loadedCompletePreimage p.next).2⟩

end DeltaReduce.PublicVoteEffects
