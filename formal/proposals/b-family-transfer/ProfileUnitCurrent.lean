import ProfileUnitState
import ProfileCurrentJournal

/-! T047/T053. Original unit-bearing configuration/P selection along the complete
pointer journal. Static source association only: producing authority, arithmetic
and imported certified-floor checks remain required by the enclosing relation.
No pointer byte, QC identity, physical sequence or production recovery changes. -/
namespace DeltaReduce.ProfileSource.UnitCurrent
open NativeReceiptBytes (Bytes)
open ConfigurationUnits (Parent)
open Current (Input)

structure Row where
  originalLine : Bytes
  input : Input
  before : Parent
  bound : UnitState.Bound
  edge : InputSection.Located Apply.Edge
  selected : ArithmeticUnits.Selected
  record : NativePointerWal.Record
  values : NativeCurrentValues.Image
  after : Parent

def bind (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment) (actor : Bytes)
    (before : Parent) (line : Bytes) (input : Input) : Option Row := do
  let bound ← UnitState.bind sha enrolled before actor input.config input.state input.policy
    input.stateValue input.originals
  let record ← NativePointerWal.readLine sha line
  let edge ← bound.collections.core.applies.certificates.find? (fun e => e.value.id == record.qc)
  if record.qc ∈ bound.collections.core.applies.finalized ∧ record = Current.originalRecord edge ∧
      edge.value.decoded.candidate.parentOptimizer = before.current.optimizer then
    let selected ← ArithmeticUnits.select sha bound.header.config.body.semantics
      edge.value.root.value.plan.value.certificate.common.accumulator
      bound.header.config.source edge.value.profile.raw
    if selected.id = edge.value.profile.value.id ∧ selected.profile = edge.value.profile.value.profile then
      let values ← NativeCurrentValues.load sha edge.value.decoded.candidate
      let after ← NativePointerWal.step before.current record
      some ⟨line,input,before,bound,edge,selected,record,values,{before with current := after}⟩
    else none
  else none

structure Source (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment) (actor : Bytes)
    (before : Parent) (line : Bytes) (input : Input) (out : Row) : Prop where
  originalLine : out.originalLine = line
  originalInput : out.input = input
  originalBefore : out.before = before
  installed : UnitState.bind sha enrolled before actor input.config input.state input.policy
    input.stateValue input.originals = some out.bound
  parsed : NativePointerWal.readLine sha line = some out.record
  selectedEdge : out.bound.collections.core.applies.certificates.find?
    (fun e => e.value.id == out.record.qc) = some out.edge
  finalized : out.record.qc ∈ out.bound.collections.core.applies.finalized
  record : out.record = Current.originalRecord out.edge
  optimizer : out.edge.value.decoded.candidate.parentOptimizer = before.current.optimizer
  profile : ArithmeticUnits.select sha out.bound.header.config.body.semantics
    out.edge.value.root.value.plan.value.certificate.common.accumulator
    out.bound.header.config.source out.edge.value.profile.raw = some out.selected
  profileId : out.selected.id = out.edge.value.profile.value.id
  profileCore : out.selected.profile = out.edge.value.profile.value.profile
  values : NativeCurrentValues.load sha out.edge.value.decoded.candidate = some out.values
  step : NativePointerWal.step before.current out.record = some out.after.current
  units : out.after = {before with current := out.after.current}

theorem boundSource {sha enrolled actor before line input out}
    (ok : bind sha enrolled actor before line input = some out) :
    Source sha enrolled actor before line input out := by
  simp only [bind,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨b,hb,r,hr,e,he,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨p,hp,last⟩ := last
  split at last <;> try contradiction
  rename_i profile
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨v,hv,n,hn,last⟩ := last
  cases Option.some.inj last
  exact ⟨rfl,rfl,rfl,hb,hr,he,checks.1,checks.2.1,checks.2.2,hp,profile.1,profile.2,hv,hn,rfl⟩

theorem boundComplete {sha enrolled actor before line input out}
    (h : Source sha enrolled actor before line input out) :
    bind sha enrolled actor before line input = some out := by
  simp only [bind,h.installed,h.parsed,h.selectedEdge,Bind.bind,Option.bind]
  rw [if_pos ⟨h.finalized,h.record,h.optimizer⟩,h.profile]
  dsimp only
  rw [if_pos ⟨h.profileId,h.profileCore⟩,h.values,h.step]
  dsimp only
  rw [← h.units,← h.originalLine,← h.originalInput,← h.originalBefore]

theorem exactOriginalWitness {sha enrolled actor before line input out}
    (ok : bind sha enrolled actor before line input = some out) :
    out.edge ∈ out.bound.collections.core.applies.certificates ∧
    out.record.qc = out.edge.value.id ∧
    out.record.qc ∈ out.bound.collections.core.applies.finalized := by
  have h := boundSource ok
  have same : out.edge.value.id = out.record.qc := by simpa using List.find?_some h.selectedEdge
  exact ⟨List.mem_of_find?_eq_some h.selectedEdge,same.symm,h.finalized⟩

theorem candidateSource {sha enrolled actor before line input out}
    (ok : bind sha enrolled actor before line input = some out) :
    Apply.bind sha out.bound.header.state.semantics .finalized out.bound.collections.core.context
      out.bound.header.policy.validators out.bound.header.state.parent out.bound.collections.core.roots
      out.bound.collections.core.applies.profiles out.edge.tree out.edge.raw = some out.edge.value := by
  have h := UnitState.collectionsSource (UnitState.boundSource (boundSource ok).installed).collections
  have applies := UnitState.appliesSource h.applies
  have member := (exactOriginalWitness ok).1
  rw [h.core] at member ⊢
  exact applies.certificates _ member

theorem selectedFromOriginalConfiguration {sha enrolled actor before line input out}
    (ok : bind sha enrolled actor before line input = some out) :
    out.selected.numeric = out.bound.header.config.numeric ∧
    out.selected.profile.accumulator = out.edge.value.root.value.plan.value.certificate.common.accumulator ∧
    out.edge.value.profile.raw = ArithmeticUnits.profileJSON out.bound.header.config.body.semantics
      out.edge.value.root.value.plan.value.certificate.common.accumulator out.bound.header.config.numeric := by
  have h := boundSource ok
  have config := ConfigurationUnits.checked
    (ConfigurationUnits.admitted (UnitState.headerSource (UnitState.boundSource h.installed).header).configuration).1
  have selected := ArithmeticUnits.selectedSource h.profile
  have same := ArithmeticUnits.sourceNumbersUnique selected.decoded config.numeric
  exact ⟨same,ArithmeticUnits.selectedProof h.profile,by simpa only [same] using selected.bytes⟩

theorem unchangedOriginalUnits {sha enrolled actor before line input out}
    (ok : bind sha enrolled actor before line input = some out) :
    out.selected.numeric.quantum = before.modelQuantum ∧
    before.modelQuantum = before.optimizerQuantum ∧
    out.after.schema = before.schema ∧ out.after.modelQuantum = before.modelQuantum ∧
    out.after.optimizerQuantum = before.optimizerQuantum := by
  have h := boundSource ok
  have units := UnitState.originalParentUnits h.installed
  refine ⟨?_,units.2.2.2.2.1.symm.trans units.2.2.2.2.2,?_,?_,?_⟩
  · rw [(selectedFromOriginalConfiguration ok).1]; exact units.2.2.2.2.1
  all_goals rw [h.units]

theorem parentAndValues {sha enrolled actor before line input out}
    (ok : bind sha enrolled actor before line input = some out) :
    out.edge.value.decoded.candidate.parent = before.current.checkpoint ∧
    out.edge.value.decoded.candidate.parentOptimizer = before.current.optimizer ∧
    out.edge.value.decoded.candidate.modelValues = NativeApplyResult.decimalValues out.values.model ∧
    out.edge.value.decoded.candidate.optimizerValues = NativeApplyResult.decimalValues out.values.optimizer := by
  have h := boundSource ok
  have fields := Apply.exactCurrentFields (candidateSource ok)
  have parent := (NativePointerWal.stepExact h.step).1.2.1
  rw [h.record] at parent
  exact ⟨fields.2.2.1.symm.trans parent,h.optimizer,NativeCurrentValues.originalPreimages h.values⟩

theorem computedCurrent {sha enrolled actor before line input out}
    (ok : bind sha enrolled actor before line input = some out) :
    out.after.current = NativePointerWal.result out.record ∧
    before.current.height < out.after.current.height ∧ out.after.current.qc = out.edge.value.id := by
  have h := boundSource ok
  have same := (NativePointerWal.stepExact h.step).2
  exact ⟨same,NativePointerWal.heightIncreases h.step,by rw [same]; exact (exactOriginalWitness ok).2.1⟩

theorem actualCurrentHashes {sha enrolled actor before line input out}
    (ok : bind sha enrolled actor before line input = some out) :
    out.after.current.checkpoint = NativeBinding.idBytes out.values.modelHash ∧
    out.after.current.optimizer = NativeBinding.idBytes out.values.optimizerHash := by
  have h := boundSource ok
  have fields := Apply.exactCurrentFields (candidateSource ok)
  have values := (NativeCurrentValues.loaded h.values).checked
  rw [(computedCurrent ok).1,h.record]
  exact ⟨fields.2.2.2.1.trans values.2.2.2.2.2.1,fields.2.2.2.2.trans values.2.2.2.2.2.2⟩

structure Chain where
  rows : List Row
  current : Parent

def run (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment) (actor : Bytes) :
    Parent → List (Bytes × Input) → Option Chain
  | before,[] => some ⟨[],before⟩
  | before,(line,input)::rest => do
    let row ← bind sha enrolled actor before line input
    let tail ← run sha enrolled actor row.after rest
    some ⟨row::tail.rows,tail.current⟩

inductive History (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment) (actor : Bytes) :
    Parent → List (Bytes × Input) → Chain → Prop where
  | nil (s) : History sha enrolled actor s [] ⟨[],s⟩
  | cons {s line input row rest tail} : bind sha enrolled actor s line input = some row →
      History sha enrolled actor row.after rest tail →
      History sha enrolled actor s ((line,input)::rest) ⟨row::tail.rows,tail.current⟩

theorem runSound {sha enrolled actor before inputs out}
    (ok : run sha enrolled actor before inputs = some out) : History sha enrolled actor before inputs out := by
  induction inputs generalizing before out with
  | nil => cases Option.some.inj ok; exact .nil _
  | cons head rest ih =>
    simp only [run,Bind.bind,Option.bind_eq_some_iff] at ok
    obtain ⟨row,hr,tail,ht,last⟩ := ok
    cases Option.some.inj last
    exact .cons hr (ih ht)

theorem historyComplete {sha enrolled actor before inputs out}
    (h : History sha enrolled actor before inputs out) : run sha enrolled actor before inputs = some out := by
  induction h with
  | nil => rfl
  | cons one _ ih => simp only [run,one,ih,Bind.bind,Option.bind]

theorem everyOriginal {sha enrolled actor before inputs out}
    (ok : run sha enrolled actor before inputs = some out) :
    out.rows.map (fun r => (r.originalLine,r.input)) = inputs := by
  have h := runSound ok
  clear ok
  induction h with
  | nil => rfl
  | cons one _ ih => simp only [List.map_cons,(boundSource one).originalLine,(boundSource one).originalInput,ih]

theorem unitsAlongCompleteHistory {sha enrolled actor before inputs out}
    (ok : run sha enrolled actor before inputs = some out) :
    out.current.schema = before.schema ∧ out.current.modelQuantum = before.modelQuantum ∧
    out.current.optimizerQuantum = before.optimizerQuantum := by
  have h := runSound ok
  clear ok
  induction h with
  | nil => exact ⟨rfl,rfl,rfl⟩
  | cons one _ ih =>
    have same := (unchangedOriginalUnits one).2.2
    exact ⟨ih.1.trans same.1,ih.2.1.trans same.2.1,ih.2.2.trans same.2.2⟩

theorem exactPointerScan {sha enrolled actor before pairs chain}
    (history : History sha enrolled actor before pairs chain) :
    NativePointerWal.replay sha before.current (pairs.map Prod.fst ++ [[]]) =
      some ⟨chain.current.current,chain.rows.map Row.record,[]⟩ := by
  induction history with
  | nil => rfl
  | @cons s line input row rest tail one later ih =>
    have h := boundSource one
    have expand : NativePointerWal.replay sha s.current (line::(rest.map Prod.fst ++ [[]])) =
        (do
          let r ← NativePointerWal.readLine sha line
          let n ← NativePointerWal.step s.current r
          let out ← NativePointerWal.replay sha n (rest.map Prod.fst ++ [[]])
          some ⟨out.state,r::out.records,out.tail⟩) := by cases rest <;> rfl
    simp only [List.map_cons,List.cons_append]
    rw [expand,h.parsed]
    dsimp only [Bind.bind,Option.bind]
    rw [h.step]
    dsimp only [Bind.bind,Option.bind]
    rw [ih]

structure Journal where
  original : Bytes
  inputs : List Input
  pairs : List (Bytes × Input)
  chain : Chain

def bindJournal (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment) (actor : Bytes)
    (initial : Parent) (observation : NativePointerWal.Observation) (inputs : List Input) : Option Journal := do
  match observation with
  | .unknown => none
  | .bytes original =>
    if NativeCurrentPointer.StateValid initial.current then
      let pairs ← CurrentJournal.align (NativePointerWal.split 10 original) inputs
      let chain ← run sha enrolled actor initial pairs
      some ⟨original,inputs,pairs,chain⟩
    else none

theorem journalSource {sha enrolled actor initial original inputs out}
    (ok : bindJournal sha enrolled actor initial (.bytes original) inputs = some out) :
    NativeCurrentPointer.StateValid initial.current ∧ out.original = original ∧ out.inputs = inputs ∧
    CurrentJournal.align (NativePointerWal.split 10 original) inputs = some out.pairs ∧
    run sha enrolled actor initial out.pairs = some out.chain := by
  simp only [bindJournal] at ok
  split at ok <;> try contradiction
  rename_i valid
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨pairs,hp,chain,hc,last⟩ := ok
  cases Option.some.inj last
  exact ⟨valid,rfl,rfl,hp,hc⟩

theorem fullOriginalInventory {sha enrolled actor initial original inputs out}
    (ok : bindJournal sha enrolled actor initial (.bytes original) inputs = some out) :
    out.chain.rows.map Row.originalLine ++ [[]] = NativePointerWal.split 10 original ∧
    out.chain.rows.map Row.input = inputs := by
  have h := journalSource ok
  have inv := CurrentJournal.aligned h.2.2.2.1
  have rows := everyOriginal h.2.2.2.2
  have first := congrArg (List.map Prod.fst) rows
  have second := congrArg (List.map Prod.snd) rows
  simp only [List.map_map] at first second
  change out.chain.rows.map Row.originalLine = out.pairs.map Prod.fst at first
  change out.chain.rows.map Row.input = out.pairs.map Prod.snd at second
  exact ⟨by rw [first]; exact inv.1,second.trans inv.2⟩

theorem journalComplete {sha enrolled actor initial original pairs chain}
    (valid : NativeCurrentPointer.StateValid initial.current)
    (inventory : pairs.map Prod.fst ++ [[]] = NativePointerWal.split 10 original)
    (history : History sha enrolled actor initial pairs chain) :
    bindJournal sha enrolled actor initial (.bytes original) (pairs.map Prod.snd) =
      some ⟨original,pairs.map Prod.snd,pairs,chain⟩ := by
  simp only [bindJournal,if_pos valid]
  rw [← inventory,CurrentJournal.alignComplete]
  dsimp only [Bind.bind,Option.bind]
  rw [historyComplete history]

theorem noRecordOrInputErasure {sha enrolled actor initial original inputs out}
    (ok : bindJournal sha enrolled actor initial (.bytes original) inputs = some out) :
    out.chain.rows.length = inputs.length ∧
    out.chain.rows.length+1 = (NativePointerWal.split 10 original).length := by
  have h := fullOriginalInventory ok
  have first := congrArg List.length h.1
  have second := congrArg List.length h.2
  simp only [List.length_append,List.length_map,List.length_cons,List.length_nil] at first second
  exact ⟨second,first⟩

theorem nativeScanAgrees {sha enrolled actor initial original inputs out}
    (ok : bindJournal sha enrolled actor initial (.bytes original) inputs = some out) :
    NativePointerWal.recover sha initial.current (.bytes original) =
      some ⟨out.chain.current.current,out.chain.rows.map Row.record,[]⟩ := by
  have h := journalSource ok
  have scan := exactPointerScan (runSound h.2.2.2.2)
  rw [(CurrentJournal.aligned h.2.2.2.1).1] at scan
  exact (if_pos h.1).trans scan

theorem incompleteRejected {sha enrolled actor initial original inputs recovered}
    (observed : NativePointerWal.recover sha initial.current (.bytes original) = some recovered)
    (incomplete : recovered.tail ≠ []) :
    bindJournal sha enrolled actor initial (.bytes original) inputs = none := by
  cases result : bindJournal sha enrolled actor initial (.bytes original) inputs with
  | none => rfl
  | some out =>
    have same := Option.some.inj (observed.symm.trans (nativeScanAgrees result))
    exact False.elim (incomplete (congrArg NativePointerWal.Recovered.tail same))

structure FromOrigin where
  origin : Origin.Bound
  genesis : Genesis.Bound
  journal : Journal

def OriginContext (known : Origin.Independent) (origin : Origin.Bound)
    (initialConfiguration : Control.Fields) (enrolled : Configuration.Enrollment) (actor : Bytes) : Prop :=
  actor = origin.bootstrap.origin.actor ∧ enrolled.semantics = known.pins.semantics ∧
  enrolled.epoch = origin.bootstrap.origin.epoch ∧
  enrolled.validators = origin.bootstrap.members.map Origin.Member.validator ∧
  (Index.field initialConfiguration "storage_authority" >>= Index.object >>=
    fun fields => Index.text (Index.field fields "storage_epoch_id")) = some enrolled.storageEpoch ∧
  (Index.field initialConfiguration "storage_authority" >>= Index.object >>=
    fun fields => Index.text (Index.field fields "storage_registry_id")) = some enrolled.storageRegistry
instance (known origin initialConfiguration enrolled actor) :
    Decidable (OriginContext known origin initialConfiguration enrolled actor) := by
  unfold OriginContext; infer_instance

def bindFromOrigin (sha : Bytes → Bytes) (known : Origin.Independent)
    (bootstrap index : Control.Fields) (bootstrapRaw indexRaw : Bytes) (store : List Bytes)
    (g : Genesis.Descriptor) (initialConfiguration : Control.Fields)
    (enrolled : Configuration.Enrollment) (actor : Bytes) (journal : NativePointerWal.Observation)
    (inputs : List Input) : Option FromOrigin := do
  let origin ← Origin.bind sha known bootstrap index bootstrapRaw indexRaw store
  let base ← Genesis.bind sha origin g initialConfiguration
  if OriginContext known origin initialConfiguration enrolled actor then
    let rows ← bindJournal sha enrolled actor (Genesis.parent base) journal inputs
    some ⟨origin,base,rows⟩
  else none

theorem originSource {sha known bootstrap index bootstrapRaw indexRaw store g initialConfiguration enrolled actor journal inputs out}
    (ok : bindFromOrigin sha known bootstrap index bootstrapRaw indexRaw store g initialConfiguration
      enrolled actor journal inputs = some out) :
    Origin.bind sha known bootstrap index bootstrapRaw indexRaw store = some out.origin ∧
    Genesis.bind sha out.origin g initialConfiguration = some out.genesis ∧
    bindJournal sha enrolled actor (Genesis.parent out.genesis) journal inputs = some out.journal ∧
    OriginContext known out.origin initialConfiguration enrolled actor := by
  simp only [bindFromOrigin,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨o,ho,b,hb,last⟩ := ok
  split at last <;> try contradiction
  rename_i same
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨j,hj,last⟩ := last
  cases Option.some.inj last
  exact ⟨ho,hb,hj,same⟩

theorem originalGenesisToCurrentUnits {sha known bootstrap index bootstrapRaw indexRaw store g initialConfiguration enrolled actor original inputs out}
    (ok : bindFromOrigin sha known bootstrap index bootstrapRaw indexRaw store g initialConfiguration
      enrolled actor (.bytes original) inputs = some out) :
    out.genesis.original = out.origin.source.genesis ∧
    out.genesis.initialConfiguration = out.origin.initialConfiguration ∧
    out.journal.chain.current.schema = out.genesis.units.schema ∧
    out.journal.chain.current.modelQuantum = out.genesis.units.quantum ∧
    out.journal.chain.current.optimizerQuantum = out.genesis.units.quantum := by
  have h := originSource ok
  have g := Genesis.boundSource h.2.1
  have j := unitsAlongCompleteHistory (journalSource h.2.2.1).2.2.2.2
  exact ⟨g.original,g.configuration,j⟩

end DeltaReduce.ProfileSource.UnitCurrent
