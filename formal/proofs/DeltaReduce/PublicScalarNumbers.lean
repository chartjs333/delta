import DeltaReduce.NativeScalarProjection
import DeltaReduce.PublicVoteEffects

/-! A checked numeric subrelation between an actual native vote derivation and
the complete public-state vote. Symbol aliases describe only model vocabulary;
they never supply arithmetic outputs. This deliberately does not check the whole
authority/parent/body, authenticate aliases or establish a production action. -/
namespace DeltaReduce.PublicScalarNumbers
open NativeBinding PublicState

def entriesList : Entries → List (Value × Value)
  | .nil => []
  | .cons key value tail => (key,value) :: entriesList tail

/-- Every alias is read by its native shard name; missing aliases fail closed. -/
inductive Renamed (symbols : String → Option Value) :
    List (String × Int) → List (Value × Value) → Prop where
  | nil : Renamed symbols [] []
  | cons {name value rest symbol tail} (selected : symbols name = some symbol)
      (next : Renamed symbols rest tail) :
      Renamed symbols ((name,value) :: rest) ((symbol,.integer value) :: tail)

def renameCells (symbols : String → Option Value) : (cells : List (String × Int)) →
    Option {rows : List (Value × Value) // Renamed symbols cells rows}
  | [] => some ⟨[], .nil⟩
  | (name,value) :: rest =>
      match selected : symbols name with
      | none => none
      | some symbol => do
          let tail ← renameCells symbols rest
          some ⟨(symbol,.integer value) :: tail.val, .cons selected tail.property⟩

theorem renamedLength {symbols cells rows} (h : Renamed symbols cells rows) :
    rows.length = cells.length := by
  induction h with
  | nil => rfl
  | cons _ _ ih => simp [ih]

theorem renamedOrigin {symbols cells rows} (h : Renamed symbols cells rows) {symbol value}
    (member : (symbol,value) ∈ rows) :
    ∃ name number, (name,number) ∈ cells ∧ symbols name = some symbol ∧ value = .integer number := by
  induction h with
  | nil => simp at member
  | @cons name number rest sym tail selected next ih =>
      rcases List.mem_cons.mp member with same | member
      · cases same; exact ⟨name,number,List.mem_cons_self,selected,rfl⟩
      · obtain ⟨name,number,hm,hs,hv⟩ := ih member
        exact ⟨name,number,List.mem_cons_of_mem _ hm,hs,hv⟩

theorem renamedRetains {symbols cells rows} (h : Renamed symbols cells rows) {name number}
    (member : (name,number) ∈ cells) :
    ∃ symbol, symbols name = some symbol ∧ (symbol,.integer number) ∈ rows := by
  induction h with
  | nil => simp at member
  | cons selected next ih =>
      rcases List.mem_cons.mp member with same | member
      · cases same; exact ⟨_,selected,List.mem_cons_self⟩
      · obtain ⟨symbol,hs,hm⟩ := ih member
        exact ⟨symbol,hs,List.mem_cons_of_mem _ hm⟩

structure Table (symbols : String → Option Value) (cells : List (String × Int)) (value : Value) where
  entries : Entries
  decoded : value = .function entries
  rows : List (Value × Value)
  renamed : Renamed symbols cells rows
  unique : (rows.map Prod.fst).Nodup
  exactRows : (entriesList entries).Perm rows

def checkTable (symbols : String → Option Value) (cells : List (String × Int)) (value : Value) :
    Option (Table symbols cells value) := do
  let renamed ← renameCells symbols cells
  match decoded : value with
  | .function entries =>
      if checked : (renamed.val.map Prod.fst).Nodup ∧ (entriesList entries).Perm renamed.val then
        some ⟨entries,decoded,renamed.val,renamed.property,checked.1,checked.2⟩
      else none
  | _ => none

theorem checkedTableSize {symbols cells value} (t : Table symbols cells value) :
    (entriesList t.entries).length = cells.length :=
  t.exactRows.length_eq.trans (renamedLength t.renamed)

theorem checkedTableNoInventedNumbers {symbols cells value} (t : Table symbols cells value)
    {symbol number} (member : (symbol,number) ∈ entriesList t.entries) :
    ∃ name n, (name,n) ∈ cells ∧ symbols name = some symbol ∧ number = .integer n :=
  renamedOrigin t.renamed (t.exactRows.mem_iff.mp member)

theorem checkedTableNoLostNumbers {symbols cells value} (t : Table symbols cells value)
    {name number} (member : (name,number) ∈ cells) :
    ∃ symbol, symbols name = some symbol ∧ (symbol,.integer number) ∈ entriesList t.entries := by
  obtain ⟨symbol, hs, hm⟩ := renamedRetains t.renamed member
  exact ⟨symbol,hs,t.exactRows.mem_iff.mpr hm⟩

/-- The abstract MODEL/OPTIMIZER record is distinct from its native hash bytes.
All three fields and the complete numeric table must match. -/
structure VectorValue (symbols : String → Option Value) (kind : String) (schema : Value)
    (cells : List (String × Int)) (value : Value) where
  table : Value
  fields : value = .function (.cons (.text "kind") (.text kind)
    (.cons (.text "schema") schema (.cons (.text "values") table .nil)))
  checkedTable : Table symbols cells table

def checkVectorValue (symbols : String → Option Value) (kind : String) (schema : Value)
    (cells : List (String × Int)) (value : Value) : Option (VectorValue symbols kind schema cells value) := do
  let table ← readField value "values"
  if fields : value = .function (.cons (.text "kind") (.text kind)
      (.cons (.text "schema") schema (.cons (.text "values") table .nil))) then
    let checkedTable ← checkTable symbols cells table
    some ⟨table,fields,checkedTable⟩
  else none

structure ApplyNumbers {codec store trust anchor} {binding : Binding codec trust anchor store}
    (symbols : String → Option Value) (schema : Value) (native : NativeApply binding) (body : Value) where
  projection : NativeScalarProjection.Apply native
  modelValue : Value
  optimizerValue : Value
  modelField : readField body "nextModelHash" = some modelValue
  optimizerField : readField body "nextOptimizerHash" = some optimizerValue
  model : VectorValue symbols "MODEL" schema projection.model.cells modelValue
  optimizer : VectorValue symbols "OPTIMIZER" schema projection.optimizer.cells optimizerValue

def checkApplyNumbers {codec store trust anchor} {binding : Binding codec trust anchor store}
    (symbols : String → Option Value) (schema : Value) (native : NativeApply binding) (body : Value) :
    Option (ApplyNumbers symbols schema native body) := do
  let projection ← NativeScalarProjection.applyResult native
  match hm : readField body "nextModelHash", ho : readField body "nextOptimizerHash" with
  | some mv, some ov =>
      let model ← checkVectorValue symbols "MODEL" schema projection.model.cells mv
      let optimizer ← checkVectorValue symbols "OPTIMIZER" schema projection.optimizer.cells ov
      some ⟨projection,mv,ov,hm,ho,model,optimizer⟩
  | _, _ => none

theorem checkedApplyAllNativeCoordinates {codec store trust anchor}
    {binding : Binding codec trust anchor store} {symbols schema native body}
    (checked : ApplyNumbers (binding := binding) symbols schema native body)
    (i : Nat) (within : i < checked.projection.scalarLayout.width) :
    ∃ shard ∈ checked.projection.scalarLayout.shards, shard.offset = i ∧
      ∃ number symbol, native.body.nextModel[i]? = some number ∧ symbols shard.id = some symbol ∧
        (symbol,.integer number) ∈ entriesList checked.model.checkedTable.entries := by
  obtain ⟨shard, hs, ho, number, hn, hc⟩ :=
    NativeScalarProjection.projectionRetainsEveryCoordinate checked.projection.model i within
  obtain ⟨symbol, ha, hv⟩ := checkedTableNoLostNumbers checked.model.checkedTable hc
  exact ⟨shard,hs,ho,number,symbol,hn,ha,hv⟩

theorem checkedOptimizerAllNativeCoordinates {codec store trust anchor}
    {binding : Binding codec trust anchor store} {symbols schema native body}
    (checked : ApplyNumbers (binding := binding) symbols schema native body)
    (i : Nat) (within : i < checked.projection.scalarLayout.width) :
    ∃ shard ∈ checked.projection.scalarLayout.shards, shard.offset = i ∧
      ∃ number symbol, native.body.nextOptimizer[i]? = some number ∧ symbols shard.id = some symbol ∧
        (symbol,.integer number) ∈ entriesList checked.optimizer.checkedTable.entries := by
  obtain ⟨shard, hs, ho, number, hn, hc⟩ :=
    NativeScalarProjection.projectionRetainsEveryCoordinate checked.projection.optimizer i within
  obtain ⟨symbol, ha, hv⟩ := checkedTableNoLostNumbers checked.optimizer.checkedTable hc
  exact ⟨shard,hs,ho,number,symbol,hn,ha,hv⟩

structure ParameterNumber {codec store trust anchor} {binding : Binding codec trust anchor store}
    {domain shard} (native : DerivedParameter binding domain shard) (body : Value) where
  projection : NativeScalarProjection.Parameter native
  exactValue : readField body "value" = some (.integer projection.value)

def checkParameterNumber {codec store trust anchor} {binding : Binding codec trust anchor store}
    {domain shard} (native : DerivedParameter binding domain shard) (body : Value) :
    Option (ParameterNumber native body) := do
  let projection ← NativeScalarProjection.parameter native
  if exactValue : readField body "value" = some (.integer projection.value) then
    some ⟨projection,exactValue⟩ else none

theorem checkedParameterNativeComputation {codec store trust anchor}
    {binding : Binding codec trust anchor store} {domain shard native body}
    (checked : ParameterNumber (binding := binding) (domain := domain) (shard := shard) native body) :
    ∃ number, readField body "value" = some (.integer number) ∧
      native.body.numerators = [number] ∧
      checkedAccumulate (accumulatorLo binding.profile) (accumulatorHi binding.profile)
        (accumulatorLo binding.profile) (accumulatorHi binding.profile) 0
        (ParameterKernel.coordinateTerms native.assignment.denominator 0 native.rows) = some number :=
  ⟨checked.projection.value,checked.exactValue,checked.projection.exactNumerator,
    NativeScalarProjection.parameterScalarComputedFromNativeRows checked.projection⟩

def kindName : VoteKind → Value
  | .parameter _ _ => .text "PARAMETER"
  | .apply => .text "APPLY"

def SourceNumbers {codec store trust anchor} {binding : Binding codec trust anchor store}
    (symbols : String → Option Value) (schema : Value) {kind}
    (source : VoteSource binding kind) (body : Value) : Type :=
  match source with
  | .parameter native => ParameterNumber native body
  | .apply native => ApplyNumbers symbols schema native body

def checkSourceNumbers {codec store trust anchor} {binding : Binding codec trust anchor store}
    (symbols : String → Option Value) (schema : Value) {kind}
    (source : VoteSource binding kind) (body : Value) : Option (SourceNumbers symbols schema source body) :=
  match source with
  | .parameter native => checkParameterNumber native body
  | .apply native => checkApplyNumbers symbols schema native body

/-- This explicitly partial join checks numeric results, event frame, complete
effects and actual native preparation. It is NOT full body/authority/phase
correspondence. Its name and result type must not be used as a formal GO gate. -/
structure VoteNumbers {codec trust voteTrust} (env : PublicJournal.Environment codec trust voteTrust)
    (mapping : IdentityMap) (symbols : String → Option Value) (schema : Value)
    (journal : PublicJournal.Journal) (slot : PublicJournal.Slot)
    (before after : PublicState.State) (actor : Value) where
  effects : PublicVoteEffects.Checked before after actor
  checkedSlot : PublicJournal.CheckedSlot env journal slot
  native : PublicJournal.NativeSlot env journal slot
  frame : NativeFrame mapping effects.first native.resolved.input.anchor native.resolved.input.metadata
  kind : effects.first.vote.kind = kindName native.resolved.input.metadata.kind
  priorSequence : effects.first.prior.data.sequence = journal.slots.length
  nextSequence : effects.first.next.data.sequence = native.record.sequence
  numbers : SourceNumbers symbols schema native.resolved.expected.source effects.first.vote.body

def bindCheckedNumbers {codec trust voteTrust} (env : PublicJournal.Environment codec trust voteTrust)
    (mapping : IdentityMap) (symbols : String → Option Value) (schema : Value)
    (journal : PublicJournal.Journal) (slot : PublicJournal.Slot)
    {before after : PublicState.State} {actor : Value}
    (effects : PublicVoteEffects.Checked before after actor) :
    Option (VoteNumbers env mapping symbols schema journal slot before after actor) := do
  let checkedSlot ← PublicJournal.checkSlot env journal slot
  let native ← PublicJournal.checkNativeSlot env journal slot
  let frame ← bindNativeFrame mapping effects.first native.resolved.input.anchor native.resolved.input.metadata
  if h : effects.first.vote.kind = kindName native.resolved.input.metadata.kind ∧
      effects.first.prior.data.sequence = journal.slots.length ∧
      effects.first.next.data.sequence = native.record.sequence then
    let numbers ← checkSourceNumbers symbols schema native.resolved.expected.source effects.first.vote.body
    some ⟨effects,checkedSlot,native,frame,h.1,h.2.1,h.2.2,numbers⟩
  else none

def bindVoteNumbers {codec trust voteTrust} (env : PublicJournal.Environment codec trust voteTrust)
    (mapping : IdentityMap) (symbols : String → Option Value) (schema : Value)
    (journal : PublicJournal.Journal) (slot : PublicJournal.Slot)
    (before after : PublicState.State) (actor : Value) :
    Option (VoteNumbers env mapping symbols schema journal slot before after actor) := do
  let effects ← PublicVoteEffects.check before after actor
  bindCheckedNumbers env mapping symbols schema journal slot effects

theorem checkEqualsComputed {before after actor} (first : First before after actor)
    (inputs : PublicVoteEffects.Inputs before first.vote)
    (extracted : extractFirst before after actor = some first)
    (read : PublicVoteEffects.readInputs before first.vote = some inputs)
    (rows : after.rows = (PublicVoteEffects.expected inputs).rows) :
    PublicVoteEffects.check before after actor = some ⟨first,inputs,rows⟩ := by
  simp [PublicVoteEffects.check, extracted, read, rows, Bind.bind, Option.bind]

theorem bindFromComputed {codec trust voteTrust env mapping symbols schema journal slot before after actor}
    (effects : PublicVoteEffects.Checked before after actor)
    (checked : PublicVoteEffects.check before after actor = some effects)
    (joined : (bindCheckedNumbers (codec := codec) (trust := trust) (voteTrust := voteTrust)
      env mapping symbols schema journal slot effects).isSome = true) :
    (bindVoteNumbers env mapping symbols schema journal slot before after actor).isSome = true := by
  simpa only [bindVoteNumbers, checked, Bind.bind, Option.bind] using joined

theorem boundNumbersHaveOriginalPreparation {codec trust voteTrust env mapping symbols schema journal slot before after actor}
    (bound : VoteNumbers (codec := codec) (trust := trust) (voteTrust := voteTrust)
      env mapping symbols schema journal slot before after actor) :
    ∃ resolved : NativeReplay.Resolved env.native bound.native.record.data,
      ∃ prepared : NativePrepared resolved.binding voteTrust resolved.input.metadata .ready
        journal.admissionState bound.native.record.data.command,
        bound.native.record = prepared.record := by
  obtain ⟨resolved,_,prepared,same⟩ := NativeReplay.acceptedVoteHasPreparation bound.native.admitted
  exact ⟨resolved,prepared,same⟩

theorem boundNumbersPreserveCompleteFootprint {codec trust voteTrust env mapping symbols schema journal slot before after actor}
    (bound : VoteNumbers (codec := codec) (trust := trust) (voteTrust := voteTrust)
      env mapping symbols schema journal slot before after actor) :
    after.rows = (PublicVoteEffects.expected bound.effects.inputs).rows ∧
    after.read "messages" = before.read "messages" ∧
    after.read "currentCheckpoint" = before.read "currentCheckpoint" :=
  ⟨bound.effects.exactRows,(PublicVoteEffects.checkedNoMessageExposure bound.effects).1,
    PublicVoteEffects.checkedNoCurrentAdvance bound.effects⟩

theorem boundNumbersRetainAllVoteSequence {codec trust voteTrust env mapping symbols schema journal slot before after actor}
    (bound : VoteNumbers (codec := codec) (trust := trust) (voteTrust := voteTrust)
      env mapping symbols schema journal slot before after actor) :
    bound.effects.first.next.data.sequence = journal.slots.length + 1 ∧
    bound.native.record.sequence = slot.sequence ∧
    slot.native = some bound.native.record :=
  ⟨bound.effects.first.sequence.trans (congrArg (· + 1) bound.priorSequence),
    bound.native.sequence,bound.native.projected⟩

structure ExecutedNumbers {codec trust voteTrust} (env : PublicRecovery.Environment codec trust voteTrust)
    (mapping : IdentityMap) (symbols : String → Option Value) (schema : Value)
    (machine : PublicRecovery.Machine) (slot : PublicJournal.Slot)
    (before after : PublicState.State) (actor : Value)
    (stages : List String) (observation : PublicRecovery.Observation) where
  binding : VoteNumbers env.journal mapping symbols schema machine.journal slot before after actor
  knownCut : PublicRecovery.classify stages ≠ some .unknown
  final : PublicRecovery.Machine
  executed : PublicRecovery.persist env.journal machine slot stages observation = some final

/-- Only a known surviving record may accompany complete after-state evidence.
An unknown append has no total-state fallback through this API. -/
def executeKnownNumbers {codec trust voteTrust} (env : PublicRecovery.Environment codec trust voteTrust)
    (mapping : IdentityMap) (symbols : String → Option Value) (schema : Value)
    (machine : PublicRecovery.Machine) (slot : PublicJournal.Slot)
    (before after : PublicState.State) (actor : Value)
    (stages : List String) (observation : PublicRecovery.Observation) :
    Option (ExecutedNumbers env mapping symbols schema machine slot before after actor stages observation) := do
  if knownCut : PublicRecovery.classify stages ≠ some .unknown then
    let binding ← bindVoteNumbers env.journal mapping symbols schema machine.journal slot before after actor
    match executed : PublicRecovery.persist env.journal machine slot stages observation with
    | none => none
    | some final => some ⟨binding,knownCut,final,executed⟩
  else none

theorem numericExecutionPreservesReachability {codec trust voteTrust env mapping symbols schema machine slot before after actor stages observation}
    (executed : ExecutedNumbers (codec := codec) (trust := trust) (voteTrust := voteTrust)
      env mapping symbols schema machine slot before after actor stages observation)
    {nativeActor current} (prior : PublicReachability.Reachable env nativeActor current machine) :
    PublicReachability.Reachable env nativeActor current executed.final :=
  .next prior (.persist executed.executed)

theorem unknownCannotSupplyCompleteState {codec trust voteTrust env mapping symbols schema machine slot before after actor stages observation}
    (unknown : PublicRecovery.classify stages = some .unknown) :
    executeKnownNumbers (codec := codec) (trust := trust) (voteTrust := voteTrust)
      env mapping symbols schema machine slot before after actor stages observation = none := by
  simp [executeKnownNumbers, unknown]

end DeltaReduce.PublicScalarNumbers
