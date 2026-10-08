import ProfileInstalledState
import DeltaReduce.NativeCurrentValues

/-! T047/T053. Bind every original pointer-WAL row to a complete successor
installed snapshot, its finalized ApplyQC and the original model/optimizer
preimages. The pointer line grammar and parent/height decision are unchanged.
This is a static source join, not production recovery or origin authority:
the enclosing profile supplies the independently anchored initial pointer,
the original complete record inventory and each snapshot's producing cut. -/
namespace DeltaReduce.ProfileSource.Current
open NativeReceiptBytes (Bytes)
open NativePolicyCodec (Value)
open NativeCurrentPointer (State)
open NativePointerWal (Record)

structure Input where
  config : Bytes
  state : Bytes
  policy : Bytes
  stateValue : Value
  originals : Collections.Originals

structure Row where
  originalLine : Bytes
  input : Input
  before : State
  bound : InstalledState.Bound
  edge : InputSection.Located Apply.Edge
  record : Record
  values : NativeCurrentValues.Image
  after : State

def originalRecord (edge : InputSection.Located Apply.Edge) : Record :=
  let q := edge.value.decoded.certificate
  ⟨q.context.height,q.parent,q.model,q.optimizer,edge.value.id⟩

def bind (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment) (actor : Bytes)
    (before : State) (line : Bytes) (input : Input) : Option Row := do
  let bound ← InstalledState.bind sha enrolled actor input.config input.state input.policy
    input.stateValue input.originals
  let record ← NativePointerWal.readLine sha line
  let edge ← bound.collections.applies.certificates.find? (fun e => e.value.id == record.qc)
  if record.qc ∈ bound.collections.applies.finalized ∧ record = originalRecord edge ∧
      edge.value.decoded.candidate.parentOptimizer = before.optimizer then
    let values ← NativeCurrentValues.load sha edge.value.decoded.candidate
    let after ← NativePointerWal.step before record
    some ⟨line,input,before,bound,edge,record,values,after⟩
  else none

structure Source (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment) (actor : Bytes)
    (before : State) (line : Bytes) (input : Input) (out : Row) : Prop where
  originalLine : out.originalLine = line
  originalInput : out.input = input
  originalBefore : out.before = before
  installed : InstalledState.bind sha enrolled actor input.config input.state input.policy
    input.stateValue input.originals = some out.bound
  parsed : NativePointerWal.readLine sha line = some out.record
  selected : out.bound.collections.applies.certificates.find?
    (fun e => e.value.id == out.record.qc) = some out.edge
  finalized : out.record.qc ∈ out.bound.collections.applies.finalized
  record : out.record = originalRecord out.edge
  optimizer : out.edge.value.decoded.candidate.parentOptimizer = before.optimizer
  values : NativeCurrentValues.load sha out.edge.value.decoded.candidate = some out.values
  step : NativePointerWal.step before out.record = some out.after

theorem boundSource {sha enrolled actor before line input out}
    (ok : bind sha enrolled actor before line input = some out) :
    Source sha enrolled actor before line input out := by
  unfold bind at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨b,hb,r,hr,e,he,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨v,hv,n,hn,last⟩ := last
  cases Option.some.inj last
  exact ⟨rfl,rfl,rfl,hb,hr,he,checks.1,checks.2.1,checks.2.2,hv,hn⟩

theorem boundComplete {sha enrolled actor before line input out}
    (h : Source sha enrolled actor before line input out) :
    bind sha enrolled actor before line input = some out := by
  cases out
  cases h.originalLine
  cases h.originalInput
  cases h.originalBefore
  simp only [bind,h.installed,h.parsed,h.selected,Bind.bind,Option.bind,
    if_pos (And.intro h.finalized (And.intro h.record h.optimizer)),h.values,h.step]

theorem exactOriginalWitness {sha enrolled actor before line input out}
    (ok : bind sha enrolled actor before line input = some out) :
    out.edge ∈ out.bound.collections.applies.certificates ∧
    out.record.qc = out.edge.value.id ∧
    out.record.qc ∈ out.bound.collections.applies.finalized := by
  have h := boundSource ok
  have same : out.edge.value.id = out.record.qc := by simpa using List.find?_some h.selected
  exact ⟨List.mem_of_find?_eq_some h.selected,same.symm,h.finalized⟩

theorem candidateSource {sha enrolled actor before line input out}
    (ok : bind sha enrolled actor before line input = some out) :
    Apply.bind sha out.bound.installed.header.state.semantics .finalized out.bound.collections.context
      out.bound.installed.policy.validators out.bound.installed.header.state.parent
      out.bound.collections.roots out.bound.collections.applies.profiles out.edge.tree out.edge.raw =
        some out.edge.value := by
  have collections := (InstalledState.boundSource (boundSource ok).installed).collections
  have applies := (Collections.boundSource collections).applies
  exact (Apply.collectionsSource applies).certificates _ (exactOriginalWitness ok).1

theorem parentAndValues {sha enrolled actor before line input out}
    (ok : bind sha enrolled actor before line input = some out) :
    out.edge.value.decoded.candidate.parent = before.checkpoint ∧
    out.edge.value.decoded.candidate.parentOptimizer = before.optimizer ∧
    out.edge.value.decoded.candidate.modelValues = NativeApplyResult.decimalValues out.values.model ∧
    out.edge.value.decoded.candidate.optimizerValues = NativeApplyResult.decimalValues out.values.optimizer := by
  have h := boundSource ok
  have fields := Apply.exactCurrentFields (candidateSource ok)
  have parent := (NativePointerWal.stepExact h.step).1.2.1
  rw [h.record] at parent
  exact ⟨fields.2.2.1.symm.trans parent,h.optimizer,NativeCurrentValues.originalPreimages h.values⟩

theorem computedCurrent {sha enrolled actor before line input out}
    (ok : bind sha enrolled actor before line input = some out) :
    out.after = NativePointerWal.result out.record ∧ before.height < out.after.height ∧
    out.after.qc = out.edge.value.id := by
  have h := boundSource ok
  have same := (NativePointerWal.stepExact h.step).2
  exact ⟨same,NativePointerWal.heightIncreases h.step,by rw [same]; exact (exactOriginalWitness ok).2.1⟩

theorem actualCurrentHashes {sha enrolled actor before line input out}
    (ok : bind sha enrolled actor before line input = some out) :
    out.after.checkpoint = NativeBinding.idBytes out.values.modelHash ∧
    out.after.optimizer = NativeBinding.idBytes out.values.optimizerHash := by
  have h := boundSource ok
  have fields := Apply.exactCurrentFields (candidateSource ok)
  have values := (NativeCurrentValues.loaded h.values).checked
  rw [(computedCurrent ok).1,h.record]
  exact ⟨fields.2.2.2.1.trans values.2.2.2.2.2.1,
    fields.2.2.2.2.trans values.2.2.2.2.2.2⟩

theorem originalCandidateBytes {sha enrolled actor before line input out}
    (ok : bind sha enrolled actor before line input = some out) :
    Apply.candidateId sha out.bound.installed.header.state.semantics
      out.edge.value.decoded.candidate = some out.edge.value.decoded.candidateId ∧
    out.edge.raw = Apply.certificateJSON out.bound.installed.header.state.semantics
      out.edge.value.decoded.certificate :=
  ⟨(Apply.originalCandidate (candidateSource ok)).2,
    (Apply.boundSource (candidateSource ok)).originalBytes⟩

structure Chain where
  rows : List Row
  current : State

def run (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment) (actor : Bytes) :
    State → List (Bytes × Input) → Option Chain
  | before,[] => some ⟨[],before⟩
  | before,(line,input)::rest => do
    let row ← bind sha enrolled actor before line input
    let tail ← run sha enrolled actor row.after rest
    some ⟨row::tail.rows,tail.current⟩

inductive History (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment) (actor : Bytes) :
    State → List (Bytes × Input) → Chain → Prop where
  | nil (s) : History sha enrolled actor s [] ⟨[],s⟩
  | cons {s line input row rest tail} : bind sha enrolled actor s line input = some row →
      History sha enrolled actor row.after rest tail →
      History sha enrolled actor s ((line,input)::rest) ⟨row::tail.rows,tail.current⟩

theorem runSound {sha enrolled actor before inputs out}
    (ok : run sha enrolled actor before inputs = some out) :
    History sha enrolled actor before inputs out := by
  induction inputs generalizing before out with
  | nil => cases Option.some.inj ok; exact .nil _
  | cons head rest ih =>
    simp only [run,Bind.bind,Option.bind_eq_some_iff] at ok
    obtain ⟨row,hr,tail,ht,last⟩ := ok
    cases Option.some.inj last
    exact .cons hr (ih ht)

theorem historyComplete {sha enrolled actor before inputs out}
    (h : History sha enrolled actor before inputs out) :
    run sha enrolled actor before inputs = some out := by
  induction h with
  | nil => rfl
  | cons one _ ih => simp only [run,one,ih,Bind.bind,Option.bind]

theorem everyOriginal {sha enrolled actor before inputs out}
    (ok : run sha enrolled actor before inputs = some out) :
    out.rows.map (fun r => (r.originalLine,r.input)) = inputs := by
  have history := runSound ok
  clear ok
  induction history with
  | nil => rfl
  | cons one _ ih =>
    have h := boundSource one
    simp only [List.map_cons,h.originalLine,h.originalInput,ih]

theorem noRecordErasure {sha enrolled actor before inputs out}
    (ok : run sha enrolled actor before inputs = some out) : out.rows.length = inputs.length := by
  have h := congrArg List.length (everyOriginal ok)
  simpa only [List.length_map] using h

theorem monotonicHeight {sha enrolled actor before inputs out}
    (ok : run sha enrolled actor before inputs = some out) : before.height ≤ out.current.height := by
  have history := runSound ok
  clear ok
  induction history with
  | nil => exact Nat.le_refl _
  | cons one _ ih => exact Nat.le_trans (Nat.le_of_lt (computedCurrent one).2.1) ih

end DeltaReduce.ProfileSource.Current
