import DeltaReduce.NativeAggregateBinding
import DeltaReduce.NativeApplyResultJoin
import DeltaReduce.NativeCurrentHistory

/-! Complete original ROOT/profile linkage for finalized APPLY and current-pointer
preparation. This is a conditional formal composition, not a runtime change.
Authentication of the source Binding/QC, physical WAL presence and historical
reachability remain independent obligations. The fresh API is not a retry API. -/
namespace DeltaReduce.NativeCertifiedCurrent
open NativeBinding
open NativeCurrentPointer (Command State Prepared)
open NativeVectorAuthority (policy state)

variable {codec store trust anchor} (binding : Binding codec trust anchor store)

/-- Compare the entire original ROOT certificate, not just numerical leaf values
or an opaque ROOT name. The selected profile comes from the source construction. -/
def check (adapter : HashAdapter codec) (b : NativeVectorContext.Bound)
    (root : NativeAggregateLineage.Edge) (profileId : Bytes) (command : Command) :
    Option (NativeApplyResultJoin.Pointer binding) := do
  let out ← NativeApplyResultJoin.pointer binding adapter.sha256 (policy b) (state b) command
  if NativeAggregateBinding.ApplyLinks root profileId out.original.edge then some out else none

theorem checkedSource {adapter b root profileId command out}
    (h : check binding adapter b root profileId command = some out) :
    NativeApplyResultJoin.pointer binding adapter.sha256 (policy b) (state b) command = some out ∧
    NativeAggregateBinding.ApplyLinks root profileId out.original.edge := by
  simp only [check,bind,Option.bind_eq_some_iff] at h
  obtain ⟨x,hx,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨hx,by assumption⟩

theorem fromComponents {adapter b root profileId command out}
    (hp : NativeApplyResultJoin.pointer binding adapter.sha256 (policy b) (state b) command = some out)
    (hl : NativeAggregateBinding.ApplyLinks root profileId out.original.edge) :
    check binding adapter b root profileId command = some out := by
  simp only [check,hp,bind,Option.bind,if_pos hl]

theorem finalizedSource {adapter b root profileId command out}
    (h : check binding adapter b root profileId command = some out) :
    NativeCurrentPointer.fromFinalized adapter.sha256 (policy b) (state b) command = some out.original ∧
    NativeApplyResult.check binding adapter.sha256 out.original.edge = some out.arithmetic :=
  NativeApplyResultJoin.pointerSource binding (checkedSource binding h).1

theorem actualFinalized {adapter b root profileId command out}
    (h : check binding adapter b root profileId command = some out) :
    NativeApplySection.bindSection adapter.sha256 (policy b) (state b) = some out.original.bound ∧
    out.original.edge ∈ out.original.bound.certificates ∧ command.qc ∈ out.original.bound.finalized ∧
    NativeCurrentPointer.prepare adapter.sha256 command out.original.edge.decoded.certificate = some out.original.prepared :=
  NativeCurrentPointer.finalizedSource (finalizedSource binding h).1

theorem finalizedLineage {adapter b root profileId command out}
    (h : check binding adapter b root profileId command = some out) :
    NativeApplyLineage.check adapter.sha256 .finalized
      (NativeParameterSection.expected (policy b) (state b) out.original.bound.roots.parameters.prior.plans)
      (policy b).validators (state b).wire.parent out.original.bound.roots.finalized
      out.original.bound.roots.certificates out.original.bound.profiles out.original.edge.source = some out.original.edge :=
  NativeApplySection.certificateChecked (actualFinalized binding h).1 (actualFinalized binding h).2.1

theorem fullOriginalRoot {oldAnchor} (base : Binding codec trust oldAnchor store)
    {adapter b id image profileId command out}
    (source : NativeCertifiedCorpus.check base adapter.sha256 b id = some image)
    (h : check binding adapter b image.root profileId command = some out) :
    out.original.edge.root.source = image.root.source := by
  have original := NativeApplySection.selectedRoot (actualFinalized binding h).1 (finalizedLineage binding h)
  have left := NativeAggregateLineage.decodedOriginal (NativeAggregateLineage.checkedSource original).decoded
  have right := NativeAggregateLineage.decodedOriginal
    (NativeAggregateLineage.checkedSource (NativeCertifiedCorpus.originalRoot base source)).decoded
  have links := (checkedSource binding h).2
  unfold NativeAggregateBinding.ApplyLinks at links
  exact left.trans ((congrArg (NativeAggregateLineage.original .finalized) links.2.1).trans right.symm)

theorem exactCurrentTuple {adapter b root profileId command out}
    (h : check binding adapter b root profileId command = some out) :
    command.checkpoint = idBytes out.arithmetic.result.body.nextModelHash ∧
    command.optimizer = idBytes out.arithmetic.result.body.nextOptimizerHash ∧
    command.parent = idBytes anchor.currentModelHash :=
  NativeApplyResultJoin.exactCommandOutput binding (checkedSource binding h).1

theorem completeCandidateValues {adapter b root profileId command out}
    (h : check binding adapter b root profileId command = some out) :
    out.original.edge.decoded.candidate.modelValues = NativeApplyResult.decimalValues out.arithmetic.result.body.nextModel ∧
    out.original.edge.decoded.candidate.optimizerValues = NativeApplyResult.decimalValues out.arithmetic.result.body.nextOptimizer :=
  NativeApplyResult.exactComputedValues binding (finalizedSource binding h).2

theorem originalBodyAndQc {adapter b root profileId command out}
    (h : check binding adapter b root profileId command = some out) :
    out.original.edge.source = NativeApplyLineage.original .finalized out.original.edge.decoded ∧
    NativeApplyCertificate.candidateId adapter.sha256 out.original.edge.decoded.candidate = some out.original.edge.decoded.candidateId ∧
    NativeApplyCertificate.certificateId adapter.sha256 out.original.edge.decoded.certificate = some out.original.edge.qc :=
  ⟨(NativeApplyLineage.originalPayload (finalizedLineage binding h)).1,
    (NativeApplyLineage.originalPayload (finalizedLineage binding h)).2,
    (NativeApplyLineage.checkedSource (finalizedLineage binding h)).qc⟩

/-- These are the ORIGINAL command and QC hashes; draft artifact IDs are not
substituted for either. No hash function injectivity is assumed here. -/
theorem originalPrepared {adapter b root profileId command out}
    (h : check binding adapter b root profileId command = some out) :
    NativeCurrentPointer.Source adapter.sha256 command out.original.edge.decoded.certificate out.original.prepared :=
  NativeCurrentPointer.preparedSource (actualFinalized binding h).2.2.2

theorem exactSelectedQc {adapter b root profileId command out}
    (h : check binding adapter b root profileId command = some out) :
    command.qc = out.original.edge.id := by
  have prepared := originalPrepared binding h
  have qc := (NativeCurrentPointer.qcChecked prepared.certificateHash).2
  have original := NativeApplyLineage.checkedSource (finalizedLineage binding h)
  have same := Option.some.inj (qc.symm.trans original.qc)
  exact prepared.links.1.trans (same.trans original.identity.symm)

theorem wrongGraphRejected {adapter b root profileId command out}
    (hp : NativeApplyResultJoin.pointer binding adapter.sha256 (policy b) (state b) command = some out)
    (bad : ¬ NativeAggregateBinding.ApplyLinks root profileId out.original.edge) :
    check binding adapter b root profileId command = none := by
  simp only [check,hp,bind,Option.bind,if_neg bad]

def fresh (adapter : HashAdapter codec) (b : NativeVectorContext.Bound)
    (root : NativeAggregateLineage.Edge) (profileId : Bytes) (command : Command) (current : State) :
    Option (NativeApplyResultJoin.Pointer binding) := do
  let out ← check binding adapter b root profileId command
  if NativeApplyResultJoin.FreshAnchor (anchor := anchor) current ∧
      NativeCurrentPointer.choose current out.original.prepared = some .advanced then some out else none

theorem freshSource {adapter b root profileId command current out}
    (h : fresh binding adapter b root profileId command current = some out) :
    check binding adapter b root profileId command = some out ∧
    NativeApplyResultJoin.FreshAnchor (anchor := anchor) current ∧
    NativeCurrentPointer.choose current out.original.prepared = some .advanced := by
  simp only [fresh,bind,Option.bind_eq_some_iff] at h
  obtain ⟨out,ho,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨ho,by assumption⟩

theorem freshFromComponents {adapter b root profileId command current out}
    (hc : check binding adapter b root profileId command = some out)
    (ha : NativeApplyResultJoin.FreshAnchor (anchor := anchor) current)
    (hf : NativeCurrentPointer.choose current out.original.prepared = some .advanced) :
    fresh binding adapter b root profileId command current = some out := by
  simp only [fresh,hc,bind,Option.bind,if_pos (And.intro ha hf)]

theorem bothParents {adapter b root profileId command current out}
    (h : fresh binding adapter b root profileId command current = some out) :
    command.parent = current.checkpoint ∧
    out.original.edge.decoded.candidate.parentOptimizer = current.optimizer := by
  have src := freshSource binding h
  have hashes := NativeApplyResult.exactComputedHashes binding (finalizedSource binding src.1).2
  exact ⟨(exactCurrentTuple binding src.1).2.2.trans src.2.1.1.symm,
    hashes.2.2.2.trans src.2.1.2.symm⟩

theorem originalRecordFields {adapter b root profileId command out}
    (h : check binding adapter b root profileId command = some out) :
    NativePointerWal.record out.original.prepared =
      ⟨command.context.height,command.parent,command.checkpoint,command.optimizer,command.qc⟩ := by
  have src := originalPrepared binding h
  simp only [NativePointerWal.record,src.command,src.links.1]

theorem recordComputed {adapter b root profileId command out}
    (h : check binding adapter b root profileId command = some out) :
    (NativePointerWal.record out.original.prepared).checkpoint = idBytes out.arithmetic.result.body.nextModelHash ∧
    (NativePointerWal.record out.original.prepared).optimizer = idBytes out.arithmetic.result.body.nextOptimizerHash := by
  rw [originalRecordFields binding h]
  exact ⟨(exactCurrentTuple binding h).1,(exactCurrentTuple binding h).2.1⟩

theorem durableRepair {adapter b root profileId command current out}
    (h : fresh binding adapter b root profileId command current = some out) :
    NativePointerWal.step current (NativePointerWal.record out.original.prepared) =
      some (NativeCurrentPointer.next out.original.prepared) ∧
    NativeCurrentPointer.choose (NativeCurrentPointer.next out.original.prepared) out.original.prepared = some .replay :=
  NativePointerWal.durableReplayRepair (actualFinalized binding (freshSource binding h).1).2.2.2
    (freshSource binding h).2.2

theorem replayWithoutSecondAppend {adapter b root profileId command out cut}
    (h : check binding adapter b root profileId command = some out) :
    NativePointerWal.execute adapter.sha256 (NativeCurrentPointer.next out.original.prepared)
      command out.original.edge.decoded.certificate cut =
      some ⟨NativeCurrentPointer.next out.original.prepared,[],some .replay⟩ :=
  NativePointerWal.exactReplayNoAppend (actualFinalized binding h).2.2.2
    (NativeCurrentPointer.replayAfterAdvance out.original.prepared)

/-- Deliberately independent of first-vote freshness: replay uses the original
certified preparation and exact tuple, even after current has advanced. -/
theorem freshCannotReplay {adapter b root profileId command out}
    (hc : check binding adapter b root profileId command = some out) :
    fresh binding adapter b root profileId command (NativeCurrentPointer.next out.original.prepared) = none := by
  simp only [fresh,hc,bind,Option.bind,NativeCurrentPointer.replayAfterAdvance]
  simp

/-- Retain actual complete/torn observations without assigning a success outcome
to UNKNOWN. This only checks one next record against its original prepared tuple;
the starting current state and observed bytes still need physical provenance. -/
def observe (sha : Bytes → Bytes) (current : State) (prepared : Prepared)
    (observation : NativePointerWal.Observation) : Option NativePointerWal.Recovered := do
  let recovered ← NativePointerWal.recover sha current observation
  if recovered.records = [NativePointerWal.record prepared] then some recovered else none

theorem observedSource {sha current prepared observation recovered}
    (h : observe sha current prepared observation = some recovered) :
    NativePointerWal.recover sha current observation = some recovered ∧
    recovered.records = [NativePointerWal.record prepared] := by
  simp only [observe,bind,Option.bind_eq_some_iff] at h
  obtain ⟨out,ho,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨ho,by assumption⟩

theorem unknownIncomplete (sha current prepared) : observe sha current prepared .unknown = none := rfl

theorem observedState {sha current prepared raw recovered}
    (h : observe sha current prepared (.bytes raw) = some recovered) :
    recovered.state = NativeCurrentPointer.next prepared := by
  have src := observedSource h
  have final := NativeCurrentHistory.walFinalState (NativePointerWal.recoveredHistory src.1).2
  rw [src.2] at final
  exact final.symm

theorem observedFromComponents {sha current prepared observation recovered}
    (hr : NativePointerWal.recover sha current observation = some recovered)
    (hs : recovered.records = [NativePointerWal.record prepared]) :
    observe sha current prepared observation = some recovered := by
  simp only [observe,hr,bind,Option.bind,if_pos hs]

theorem observedOriginalRecord {sha current prepared raw recovered}
    (h : observe sha current prepared (.bytes raw) = some recovered) :
    ∃ line ∈ NativePointerWal.split 10 raw,
      NativePointerWal.readLine sha line = some (NativePointerWal.record prepared) := by
  have src := observedSource h
  obtain ⟨line,mem,parsed,_⟩ := NativePointerWal.historyRecord
    (NativePointerWal.recoveredHistory src.1).2 (NativePointerWal.record prepared)
    (by rw [src.2]; simp)
  exact ⟨line,mem,parsed⟩

theorem observedComputed {adapter b root profileId command current out raw recovered}
    (hc : check binding adapter b root profileId command = some out)
    (ho : observe adapter.sha256 current out.original.prepared (.bytes raw) = some recovered) :
    ∃ line ∈ NativePointerWal.split 10 raw,
      NativePointerWal.readLine adapter.sha256 line = some
        ⟨command.context.height,command.parent,idBytes out.arithmetic.result.body.nextModelHash,
          idBytes out.arithmetic.result.body.nextOptimizerHash,command.qc⟩ := by
  obtain ⟨line,mem,parsed⟩ := observedOriginalRecord ho
  refine ⟨line,mem,?_⟩
  rw [originalRecordFields binding hc] at parsed
  rw [(exactCurrentTuple binding hc).1,(exactCurrentTuple binding hc).2.1] at parsed
  exact parsed

/-- Recovery of a known single next record uses the same complete arithmetic/QC
check and pre-advance current anchor. A torn suffix is retained, not truncated
or declared safe for subsequent writes. Empty/unknown cannot claim the record. -/
def recover (adapter : HashAdapter codec) (b : NativeVectorContext.Bound)
    (root : NativeAggregateLineage.Edge) (profileId : Bytes) (command : Command)
    (current : State) (observation : NativePointerWal.Observation) :
    Option (NativeApplyResultJoin.Pointer binding × NativePointerWal.Recovered) := do
  let out ← fresh binding adapter b root profileId command current
  let wal ← observe adapter.sha256 current out.original.prepared observation
  some (out,wal)

theorem recoveredSource {adapter b root profileId command current observation out wal}
    (h : recover binding adapter b root profileId command current observation = some (out,wal)) :
    fresh binding adapter b root profileId command current = some out ∧
    observe adapter.sha256 current out.original.prepared observation = some wal := by
  simp only [recover,bind,Option.bind_eq_some_iff] at h
  obtain ⟨x,hx,w,hw,last⟩ := h
  cases Option.some.inj last
  exact ⟨hx,hw⟩

theorem recoveredComputedCurrent {adapter b root profileId command current raw out wal}
    (h : recover binding adapter b root profileId command current (.bytes raw) = some (out,wal)) :
    wal.state.checkpoint = idBytes out.arithmetic.result.body.nextModelHash ∧
    wal.state.optimizer = idBytes out.arithmetic.result.body.nextOptimizerHash ∧
    NativeCurrentPointer.choose wal.state out.original.prepared = some .replay := by
  have src := recoveredSource binding h
  have checked := (freshSource binding src.1).1
  rw [observedState src.2]
  exact ⟨(NativeApplyResultJoin.nextComputed binding (checkedSource binding checked).1).1,
    (NativeApplyResultJoin.nextComputed binding (checkedSource binding checked).1).2,
    NativeCurrentPointer.replayAfterAdvance out.original.prepared⟩

theorem unknownRecoveryRejected (adapter b root profileId command current) :
    recover binding adapter b root profileId command current .unknown = none := by
  unfold recover
  cases fresh binding adapter b root profileId command current <;> rfl

/-- Complete-byte gate only; even a successful result needs independent physical
observation and authority. A retained suffix cannot qualify as a writable state. -/
def completeObservation (wal : NativePointerWal.Recovered) : Option State :=
  if wal.tail = [] then some wal.state else none

theorem completeObservationExact {wal current}
    (h : completeObservation wal = some current) : wal.tail = [] ∧ current = wal.state := by
  unfold completeObservation at h
  split at h <;> try contradiction
  exact ⟨by assumption,(Option.some.inj h).symm⟩

theorem tornObservationBlocked {wal} (torn : wal.tail ≠ []) : completeObservation wal = none := if_neg torn

def resumable (adapter : HashAdapter codec) (b : NativeVectorContext.Bound)
    (root : NativeAggregateLineage.Edge) (profileId : Bytes) (command : Command)
    (current : State) (observation : NativePointerWal.Observation) : Option State := do
  let (_,wal) ← recover binding adapter b root profileId command current observation
  completeObservation wal

theorem resumableSource {adapter b root profileId command current observation nextState}
    (h : resumable binding adapter b root profileId command current observation = some nextState) :
    ∃ out wal, recover binding adapter b root profileId command current observation = some (out,wal) ∧
      wal.tail = [] ∧ nextState = wal.state := by
  simp only [resumable,bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨out,wal⟩,hr,hc⟩ := h
  exact ⟨out,wal,hr,completeObservationExact hc⟩

/-- Refuse a new advance if the original history still has a torn suffix. -/
def freshFromHistory (adapter : HashAdapter codec) (b : NativeVectorContext.Bound)
    (root : NativeAggregateLineage.Edge) (profileId : Bytes) (command : Command)
    (history : NativePointerWal.Recovered) : Option (NativeApplyResultJoin.Pointer binding) := do
  let current ← completeObservation history
  fresh binding adapter b root profileId command current

theorem historyFreshSource {adapter b root profileId command history out}
    (h : freshFromHistory binding adapter b root profileId command history = some out) :
    history.tail = [] ∧ fresh binding adapter b root profileId command history.state = some out := by
  simp only [freshFromHistory,bind,Option.bind_eq_some_iff] at h
  obtain ⟨current,hc,hf⟩ := h
  have complete := completeObservationExact hc
  exact ⟨complete.1,complete.2 ▸ hf⟩

theorem tornHistoryBlocked {adapter b root profileId command history}
    (torn : history.tail ≠ []) :
    freshFromHistory binding adapter b root profileId command history = none := by
  simp only [freshFromHistory,tornObservationBlocked torn,bind,Option.bind]

/-- Constructed source graph, exact corpus, aggregate and source-selected profile.
All authentication hypotheses remain visible; no caller-supplied body mapping. -/
def fromSource {codec store depth prep units pid initial observation history permission inputs b s root trust}
    (adapter : HashAdapter codec)
    (ran : NativeAuthorityProjection.run adapter.sha256 codec store depth prep units pid initial observation history permission inputs = some (b,s,root))
    (auth : NativeBindingConstruction.Premises trust codec b s root)
    {id image aggregate authority}
    (source : NativeCertifiedCorpus.check (NativeBindingConstruction.fromRun adapter ran auth) adapter.sha256 b id = some image)
    (made : NativeAggregateBinding.artifact (NativeBindingConstruction.fromRun adapter ran auth) image = some aggregate)
    (aggregateAuth : NativeAggregateBinding.Premises (NativeBindingConstruction.fromRun adapter ran auth) authority image aggregate)
    (command : Command) :=
  freshFromHistory (NativeAggregateBinding.extend (NativeBindingConstruction.fromRun adapter ran auth) adapter source made aggregateAuth)
    adapter b image.root s.originalProfile.id command s.current.recovery.wal

/-- The pre-advance tuple is computed from the original checked history, not
supplied independently. The next-record observation is still unauthenticated. -/
def recoverFromSource {codec store depth prep units pid initial observation history permission inputs b s root trust}
    (adapter : HashAdapter codec)
    (ran : NativeAuthorityProjection.run adapter.sha256 codec store depth prep units pid initial observation history permission inputs = some (b,s,root))
    (auth : NativeBindingConstruction.Premises trust codec b s root)
    {id image aggregate authority}
    (source : NativeCertifiedCorpus.check (NativeBindingConstruction.fromRun adapter ran auth) adapter.sha256 b id = some image)
    (made : NativeAggregateBinding.artifact (NativeBindingConstruction.fromRun adapter ran auth) image = some aggregate)
    (aggregateAuth : NativeAggregateBinding.Premises (NativeBindingConstruction.fromRun adapter ran auth) authority image aggregate)
    (command : Command) (nextObservation : NativePointerWal.Observation) : Option State := do
  let current ← completeObservation s.current.recovery.wal
  resumable (NativeAggregateBinding.extend (NativeBindingConstruction.fromRun adapter ran auth) adapter source made aggregateAuth)
    adapter b image.root s.originalProfile.id command current nextObservation

end DeltaReduce.NativeCertifiedCurrent
