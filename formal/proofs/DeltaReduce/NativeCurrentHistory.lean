import DeltaReduce.NativeCurrentValues

/-! Every observed pointer-WAL record is joined to an original full finalized
APPLY snapshot and its exact candidate value preimages. No history or vector is
invented for an empty/unknown observation. Physical provenance remains open. -/
namespace DeltaReduce.NativeCurrentHistory
open NativeReceiptBytes
open NativeCurrentPointer (State Prepared)
open NativePointerWal (Record result)

structure Input where
  policy : Bytes
  state : Bytes
  deriving DecidableEq, Repr

def command (r : Record) (e : NativeApplyLineage.Edge) : NativeCurrentPointer.Command :=
  ⟨e.decoded.certificate.context,r.qc,e.decoded.certificate.parent,
    e.decoded.certificate.model,e.decoded.certificate.optimizer⟩

structure Row where
  input : Input
  before : State
  record : Record
  policy : NativePolicyBytes.Policy
  state : NativeStateBytes.State
  sectionBound : NativeApplySection.Bound
  edge : NativeApplyLineage.Edge
  prepared : Prepared
  values : NativeCurrentValues.Image
  after : State

def checkRow (sha : Bytes → Bytes) (before : State) (r : Record) (input : Input) : Option Row := do
  let (_,policy) ← NativePolicyBytes.decodePolicy input.policy
  let state ← NativeStateBytes.decodeState input.state
  let sec ← NativeApplySection.bindSection sha policy state
  let edge ← sec.certificates.find? (fun e => e.id == r.qc)
  if r.qc ∈ sec.finalized then
    let prepared ← NativeCurrentPointer.prepare sha (command r edge) edge.decoded.certificate
    if NativePointerWal.record prepared = r ∧ edge.decoded.candidate.parentOptimizer = before.optimizer then
      let values ← NativeCurrentValues.load sha edge.decoded.candidate
      let after ← NativePointerWal.step before r
      some ⟨input,before,r,policy,state,sec,edge,prepared,values,after⟩
    else none
  else none

structure RowSource (sha : Bytes → Bytes) (before : State) (r : Record) (input : Input) (out : Row) : Prop where
  originalInput : out.input = input
  originalBefore : out.before = before
  originalRecord : out.record = r
  policy : ∃ tree, NativePolicyBytes.decodePolicy input.policy = some (tree,out.policy)
  state : NativeStateBytes.decodeState input.state = some out.state
  sectionBound : NativeApplySection.bindSection sha out.policy out.state = some out.sectionBound
  selected : out.sectionBound.certificates.find? (fun e => e.id == r.qc) = some out.edge
  finalized : r.qc ∈ out.sectionBound.finalized
  prepared : NativeCurrentPointer.prepare sha (command r out.edge) out.edge.decoded.certificate = some out.prepared
  recordMatches : NativePointerWal.record out.prepared = r
  parentOptimizer : out.edge.decoded.candidate.parentOptimizer = before.optimizer
  values : NativeCurrentValues.load sha out.edge.decoded.candidate = some out.values
  step : NativePointerWal.step before r = some out.after

theorem rowSource {sha before r input out} (h : checkRow sha before r input = some out) :
    RowSource sha before r input out := by
  simp only [checkRow,Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨tree,policy⟩,hp,state,hs,sec,hsec,edge,he,last⟩ := h
  split at last <;> try contradiction
  rename_i finalized
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨prepared,hp',last⟩ := last
  split at last <;> try contradiction
  rename_i links
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨values,hv,after,ha,last⟩ := last
  cases Option.some.inj last
  exact ⟨rfl,rfl,rfl,⟨tree,hp⟩,hs,hsec,he,finalized,hp',links.1,links.2,hv,ha⟩

theorem rowFromSource {sha before r input out} (h : RowSource sha before r input out) :
    checkRow sha before r input = some out := by
  obtain ⟨tree,hp⟩ := h.policy
  cases out
  cases h.originalInput
  cases h.originalBefore
  cases h.originalRecord
  simp only [checkRow,hp,h.state,h.sectionBound,h.selected,Bind.bind,Option.bind,
    if_pos h.finalized,h.prepared,if_pos (And.intro h.recordMatches h.parentOptimizer),h.values,h.step]

theorem originalCandidate {sha before r input out} (h : checkRow sha before r input = some out) :
    out.edge.source = NativeApplyLineage.original .finalized out.edge.decoded ∧
    NativeApplyCertificate.candidateId sha out.edge.decoded.candidate = some out.edge.decoded.candidateId :=
  NativeApplyLineage.originalPayload (NativeApplySection.certificateChecked (rowSource h).sectionBound
    (List.mem_of_find?_eq_some (rowSource h).selected))

theorem candidateBounds {sha before r input out} (h : checkRow sha before r input = some out) :
    (NativeApplyCertificate.candidateJSON out.edge.decoded.candidate).length ≤ NativeContractSize.maxBytes ∧
    (NativeApplyCertificate.certificateJSON out.edge.decoded.certificate).length ≤ NativeContractSize.maxBytes :=
  NativeApplyLineage.bothPayloadBounds (NativeApplySection.certificateChecked (rowSource h).sectionBound
    (List.mem_of_find?_eq_some (rowSource h).selected))

theorem afterComputed {sha before r input out} (h : checkRow sha before r input = some out) :
    out.after = result r := (NativePointerWal.stepExact (rowSource h).step).2

theorem valueHashes {sha before r input out} (h : checkRow sha before r input = some out) :
    out.after.checkpoint = NativeBinding.idBytes out.values.modelHash ∧
    out.after.optimizer = NativeBinding.idBytes out.values.optimizerHash := by
  have src := rowSource h
  have checked := NativeApplySection.certificateChecked src.sectionBound (List.mem_of_find?_eq_some src.selected)
  have fields := NativeApplyLineage.certifiedFields checked
  have p := NativeCurrentPointer.preparedSource src.prepared
  have model := congrArg NativePointerWal.Record.checkpoint src.recordMatches
  have optimizer := congrArg NativePointerWal.Record.optimizer src.recordMatches
  simp only [NativePointerWal.record,p.command,command] at model optimizer
  have values := (NativeCurrentValues.loaded src.values).checked
  rw [afterComputed h]
  exact ⟨model.symm.trans (fields.2.2.1.trans values.2.2.2.2.2.1),
    optimizer.symm.trans (fields.2.2.2.trans values.2.2.2.2.2.2)⟩

theorem originalValueBytes {sha before r input out} (h : checkRow sha before r input = some out) :
    out.edge.decoded.candidate.modelValues = NativeApplyResult.decimalValues out.values.model ∧
    out.edge.decoded.candidate.optimizerValues = NativeApplyResult.decimalValues out.values.optimizer :=
  NativeCurrentValues.originalPreimages (rowSource h).values

theorem parentsFromPrevious {sha before r input out} (h : checkRow sha before r input = some out) :
    out.edge.decoded.candidate.parent = before.checkpoint ∧
    out.edge.decoded.candidate.parentOptimizer = before.optimizer := by
  have src := rowSource h
  have fields := NativeApplyLineage.certifiedFields
    (NativeApplySection.certificateChecked src.sectionBound (List.mem_of_find?_eq_some src.selected))
  have p := NativeCurrentPointer.preparedSource src.prepared
  have parent := congrArg NativePointerWal.Record.parent src.recordMatches
  simp only [NativePointerWal.record,p.command,command] at parent
  exact ⟨fields.2.1.symm.trans (parent.trans (NativePointerWal.stepExact src.step).1.2.1),
    src.parentOptimizer⟩

theorem heightStrictlyIncreases {sha before r input out} (h : checkRow sha before r input = some out) :
    before.height < out.after.height := NativePointerWal.heightIncreases (rowSource h).step

def finalState : State → List Record → State
  | s,[] => s
  | _,r::rs => finalState (result r) rs

theorem walFinalState {sha s lines out} (h : NativePointerWal.History sha s lines out) :
    finalState s out.records = out.state := by
  induction h with
  | done => rfl
  | more parsed step later ih =>
    simpa only [finalState,(NativePointerWal.stepExact step).2] using ih

structure Chain where
  rows : List Row
  state : State

def loadRows (sha : Bytes → Bytes) (before : State) : List Record → List Input → Option Chain
  | [],[] => some ⟨[],before⟩
  | r::rs,input::inputs => do
    let row ← checkRow sha before r input
    let rest ← loadRows sha row.after rs inputs
    some ⟨row::rest.rows,rest.state⟩
  | _,_ => none

def Linked : State → List Row → Prop
  | _,[] => True
  | before,row::rows => row.before = before ∧ Linked row.after rows

theorem chainLinked {sha before records inputs out} (h : loadRows sha before records inputs = some out) :
    Linked before out.rows := by
  induction records generalizing before inputs out with
  | nil => cases inputs <;> simp [loadRows] at h; subst out; trivial
  | cons r rs ih =>
    cases inputs with
    | nil => simp [loadRows] at h
    | cons input inputs =>
      simp only [loadRows,Bind.bind,Option.bind_eq_some_iff] at h
      obtain ⟨row,hr,rest,ht,last⟩ := h
      cases Option.some.inj last
      exact ⟨(rowSource hr).originalBefore,ih ht⟩

theorem chainSource {sha before records inputs out} (h : loadRows sha before records inputs = some out) :
    out.rows.map Row.record = records ∧ out.rows.map Row.input = inputs ∧
    out.state = finalState before records ∧
    ∀ row ∈ out.rows, checkRow sha row.before row.record row.input = some row := by
  induction records generalizing before inputs out with
  | nil =>
    cases inputs <;> simp [loadRows] at h
    subst out
    exact ⟨rfl,rfl,rfl,by simp⟩
  | cons r rs ih =>
    cases inputs with
    | nil => simp [loadRows] at h
    | cons input inputs =>
      simp only [loadRows,Bind.bind,Option.bind_eq_some_iff] at h
      obtain ⟨row,hr,rest,ht,last⟩ := h
      cases Option.some.inj last
      have src := rowSource hr
      have tail := ih ht
      refine ⟨by simp [src.originalRecord,tail.1],by simp [src.originalInput,tail.2.1],?_,?_⟩
      · rw [tail.2.2.1,afterComputed hr]; rfl
      · intro item mem
        rcases List.mem_cons.mp mem with rfl | mem
        · simpa only [src.originalBefore,src.originalRecord,src.originalInput] using hr
        · exact tail.2.2.2 item mem

theorem chainFinalRow {sha before records inputs out row}
    (h : loadRows sha before records inputs = some out) (last : out.rows.getLast? = some row) :
    out.state = row.after := by
  induction records generalizing before inputs out with
  | nil => cases inputs <;> simp [loadRows] at h; subst out; simp at last
  | cons r rs ih =>
    cases inputs with
    | nil => simp [loadRows] at h
    | cons input inputs =>
      simp only [loadRows,Bind.bind,Option.bind_eq_some_iff] at h
      obtain ⟨first,hf,rest,ht,eq⟩ := h
      cases Option.some.inj eq
      cases tail : rest.rows with
      | nil =>
        have empty : rs = [] := by simpa [tail] using (chainSource ht).1.symm
        subst rs
        cases inputs <;> simp [loadRows] at ht
        subst rest
        exact congrArg Row.after (by simpa using last)
      | cons head more =>
        apply ih ht
        simpa [tail] using last

structure Recovered where
  wal : NativePointerWal.Recovered
  chain : Chain

def recover (sha : Bytes → Bytes) (initial : State) (observation : NativePointerWal.Observation)
    (inputs : List Input) : Option Recovered := do
  let wal ← NativePointerWal.recover sha initial observation
  let chain ← loadRows sha initial wal.records inputs
  some ⟨wal,chain⟩

theorem recoveredSource {sha initial observation inputs out}
    (h : recover sha initial observation inputs = some out) :
    NativePointerWal.recover sha initial observation = some out.wal ∧
    loadRows sha initial out.wal.records inputs = some out.chain := by
  simp only [recover,Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨wal,hw,chain,hc,last⟩ := h
  cases Option.some.inj last
  exact ⟨hw,hc⟩

theorem computedFinalState {sha initial raw inputs out}
    (h : recover sha initial (.bytes raw) inputs = some out) : out.chain.state = out.wal.state :=
  (chainSource (recoveredSource h).2).2.2.1.trans
    (walFinalState (NativePointerWal.recoveredHistory (recoveredSource h).1).2)

theorem completeOrderedEvidence {sha initial observation inputs out}
    (h : recover sha initial observation inputs = some out) :
    out.chain.rows.map Row.record = out.wal.records ∧ out.chain.rows.map Row.input = inputs :=
  ⟨(chainSource (recoveredSource h).2).1,(chainSource (recoveredSource h).2).2.1⟩

theorem unknownRejected (sha initial inputs) : recover sha initial .unknown inputs = none := rfl

theorem noEvidenceRejected (sha before r rs) : loadRows sha before (r::rs) [] = none := rfl
theorem extraEvidenceRejected (sha before input inputs) : loadRows sha before [] (input::inputs) = none := rfl

structure Current where
  recovery : Recovered
  last : Row

def current (sha : Bytes → Bytes) (initial : State) (observation : NativePointerWal.Observation)
    (inputs : List Input) : Option Current := do
  let recovered ← recover sha initial observation inputs
  let last ← recovered.chain.rows.getLast?
  some ⟨recovered,last⟩

theorem currentSource {sha initial observation inputs out}
    (h : current sha initial observation inputs = some out) :
    recover sha initial observation inputs = some out.recovery ∧
    out.recovery.chain.rows.getLast? = some out.last := by
  simp only [current,Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨recovered,hr,last,hl,eq⟩ := h
  cases Option.some.inj eq
  exact ⟨hr,hl⟩

theorem currentRowChecked {sha initial observation inputs out}
    (h : current sha initial observation inputs = some out) :
    checkRow sha out.last.before out.last.record out.last.input = some out.last :=
  (chainSource (recoveredSource (currentSource h).1).2).2.2.2 _
    (List.mem_of_getLast? (currentSource h).2)

theorem currentStateDerived {sha initial raw inputs out}
    (h : current sha initial (.bytes raw) inputs = some out) :
    out.recovery.wal.state = out.last.after :=
  (computedFinalState (currentSource h).1).symm.trans
    (chainFinalRow (recoveredSource (currentSource h).1).2 (currentSource h).2)

theorem currentValueHashes {sha initial raw inputs out}
    (h : current sha initial (.bytes raw) inputs = some out) :
    out.recovery.wal.state.checkpoint =
      NativeBinding.idBytes (sha (NativeBinding.valueHashInput .model out.last.values.model)) ∧
    out.recovery.wal.state.optimizer =
      NativeBinding.idBytes (sha (NativeBinding.valueHashInput .optimizer out.last.values.optimizer)) := by
  have row := currentRowChecked h
  have src := NativeCurrentValues.loaded (rowSource row).values
  rw [currentStateDerived h,← src.modelHash,← src.optimizerHash]
  exact valueHashes row

theorem currentOriginalValues {sha initial observation inputs out}
    (h : current sha initial observation inputs = some out) :
    out.last.edge.decoded.candidate.modelValues = NativeApplyResult.decimalValues out.last.values.model ∧
    out.last.edge.decoded.candidate.optimizerValues = NativeApplyResult.decimalValues out.last.values.optimizer :=
  originalValueBytes (currentRowChecked h)

theorem emptyHistoryNoCurrent {sha initial observation inputs out}
    (h : recover sha initial observation inputs = some out) (empty : out.chain.rows = []) :
    current sha initial observation inputs = none := by
  simp only [current,h,Bind.bind,Option.bind,empty,List.getLast?_nil]

theorem unknownNoCurrent (sha initial inputs) : current sha initial .unknown inputs = none := rfl

theorem badObservationRejected {sha initial observation inputs}
    (bad : NativePointerWal.recover sha initial observation = none) :
    current sha initial observation inputs = none := by
  simp only [current,recover,bad,Bind.bind,Option.bind]

theorem retainedObservation {sha initial raw inputs out}
    (h : current sha initial (.bytes raw) inputs = some out) :
    NativePointerWal.recover sha initial (.bytes raw) = some out.recovery.wal :=
  (recoveredSource (currentSource h).1).1

end DeltaReduce.NativeCurrentHistory
