import DeltaReduce.NativeStateArtifacts

/-! Source-derived state/profile artifacts. UnitSource is a named unresolved
primitive metadata boundary; it returns only quantum for a complete source key.
No native configuration/metadata authentication is inferred from its presence. -/
namespace DeltaReduce.NativeStateProjection
open NativeBinding
open NativeVectorArtifacts (Artifact pack)
open NativeIscProjection (Stored)
open NativeStateArtifacts
open NativeVectorContext (Bound)

structure UnitKey where
  context : NativeInputSetBody.Context
  apc : Bytes
  applyProfile : Bytes
  accumulator : Bytes
  current : NativeCurrentPointer.State
  deriving DecidableEq, Repr
abbrev UnitSource := UnitKey → Option Rational

def unitKey (b : Bound) (p : NativeApplyProfile.Checked) (c : NativeCurrentHistory.Current) : UnitKey :=
  ⟨(NativeVectorAuthority.plan b).certificate.common.context,(NativeVectorAuthority.plan b).id,
    p.id,p.profile.accumulator,c.recovery.wal.state⟩

def selectProfile (sha : Bytes → Bytes) (b : Bound) (pid : Bytes) : Option NativeApplyProfile.Checked := do
  let trees ← NativeParameterSection.trees (NativeVectorAuthority.policy b) "apply_profiles"
  let ps ← NativeApplyProfile.checkAll sha trees
  if NativePolicyBytes.strictly NativePolicyBytes.bytesLT (ps.map (·.id)) = true then
    match ps.filter (fun p => p.id == pid) with
    | [p] => some p
    | _ => none
  else none

theorem selectedSource {sha b pid p} (h : selectProfile sha b pid = some p) :
    ∃ trees ps, NativeParameterSection.trees (NativeVectorAuthority.policy b) "apply_profiles" = some trees ∧
      NativeApplyProfile.checkAll sha trees = some ps ∧ p ∈ ps ∧ p.id = pid ∧
      NativeApplyProfile.check sha p.source = some p := by
  simp only [selectProfile,bind,Option.bind_eq_some_iff] at h
  obtain ⟨trees,ht,ps,hp,last⟩ := h
  split at last <;> try contradiction
  split at last <;> try contradiction
  rename_i p' eq
  cases Option.some.inj last
  have member : p ∈ ps.filter (fun p => p.id == pid) := by rw [eq]; simp
  have mem := List.mem_filter.mp member
  exact ⟨trees,ps,ht,hp,mem.1,by simpa using mem.2,NativeApplyProfile.allChecked hp _ mem.1⟩

def Links (b : Bound) (p : NativeApplyProfile.Checked) (c : NativeCurrentHistory.Current) : Prop :=
  p.profile.accumulator = (NativeVectorAuthority.plan b).certificate.common.accumulator ∧
  c.recovery.wal.state.checkpoint = (NativeVectorAuthority.state b).wire.parent ∧
  c.recovery.wal.state.height < (NativeVectorAuthority.state b).height ∧
  c.last.edge.decoded.candidate.context.schema = (NativeVectorAuthority.plan b).certificate.common.context.schema
instance (b p c) : Decidable (Links b p c) := by unfold Links; infer_instance

def model (schema : Ref) (q : Rational) (c : NativeCurrentHistory.Current) : StateVector :=
  ⟨schema,q,c.last.values.model⟩
def optimizer (schema : Ref) (q : Rational) (c : NativeCurrentHistory.Current) : StateVector :=
  ⟨schema,q,c.last.values.optimizer⟩

structure Image where
  current : NativeCurrentHistory.Current
  originalProfile : NativeApplyProfile.Checked
  quantum : Rational
  profile : Profile
  profileArtifact : Artifact
  graph : NativePlanProjection.Image
  modelArtifact : Artifact
  optimizerArtifact : Artifact

def assemble (sha : Bytes → Bytes) (codec : Codec) (store : Store) (b : Bound)
    (c : NativeCurrentHistory.Current) (p : NativeApplyProfile.Checked) (q : Rational)
    (permission : NativeAvailableQ.Permission) (inputs : List NativeAvailableQ.Input) : Option Image := do
  let profile := profileValue b.source.plan.accumulator.numbers.accumulatorBits q p.profile
  if Links b p c ∧ ProfileChecks p.profile profile then
    let pa ← pack codec.hash (profileBytes profile) (.profile profile)
    let graph ← NativePlanProjection.check sha codec store b permission inputs pa.ref
    if c.last.values.model.length = graph.isc.layout.coordinates.length ∧
       c.last.values.optimizer.length = graph.isc.layout.coordinates.length then
      let m ← pack codec.hash (vectorBytes "MODEL" (model graph.isc.schema.ref q c)) (.model (model graph.isc.schema.ref q c))
      let o ← pack codec.hash (vectorBytes "OPTIMIZER" (optimizer graph.isc.schema.ref q c)) (.optimizer (optimizer graph.isc.schema.ref q c))
      if Stored codec store pa ∧ Stored codec store m ∧ Stored codec store o then
        some ⟨c,p,q,profile,pa,graph,m,o⟩
      else none
    else none
  else none

def construct (sha : Bytes → Bytes) (codec : Codec) (store : Store) (b : Bound)
    (units : UnitSource) (pid : Bytes) (initial : NativeCurrentPointer.State)
    (observation : NativePointerWal.Observation) (history : List NativeCurrentHistory.Input)
    (permission : NativeAvailableQ.Permission) (inputs : List NativeAvailableQ.Input) : Option Image := do
  let c ← NativeCurrentHistory.current sha initial observation history
  let p ← selectProfile sha b pid
  let q ← units (unitKey b p c)
  assemble sha codec store b c p q permission inputs

structure Source (sha : Bytes → Bytes) (codec : Codec) (store : Store) (b : Bound)
    (units : UnitSource) (pid : Bytes) (initial : NativeCurrentPointer.State)
    (observation : NativePointerWal.Observation) (history : List NativeCurrentHistory.Input)
    (permission : NativeAvailableQ.Permission) (inputs : List NativeAvailableQ.Input) (out : Image) : Prop where
  current : NativeCurrentHistory.current sha initial observation history = some out.current
  originalProfile : selectProfile sha b pid = some out.originalProfile
  quantum : units (unitKey b out.originalProfile out.current) = some out.quantum
  profile : out.profile = profileValue b.source.plan.accumulator.numbers.accumulatorBits out.quantum out.originalProfile.profile
  links : Links b out.originalProfile out.current
  checked : ProfileChecks out.originalProfile.profile out.profile
  profileArtifact : pack codec.hash (profileBytes out.profile) (.profile out.profile) = some out.profileArtifact
  graph : NativePlanProjection.check sha codec store b permission inputs out.profileArtifact.ref = some out.graph
  sizes : out.current.last.values.model.length = out.graph.isc.layout.coordinates.length ∧
    out.current.last.values.optimizer.length = out.graph.isc.layout.coordinates.length
  modelArtifact : pack codec.hash (vectorBytes "MODEL" (model out.graph.isc.schema.ref out.quantum out.current))
    (.model (model out.graph.isc.schema.ref out.quantum out.current)) = some out.modelArtifact
  optimizerArtifact : pack codec.hash (vectorBytes "OPTIMIZER" (optimizer out.graph.isc.schema.ref out.quantum out.current))
    (.optimizer (optimizer out.graph.isc.schema.ref out.quantum out.current)) = some out.optimizerArtifact
  stored : Stored codec store out.profileArtifact ∧ Stored codec store out.modelArtifact ∧ Stored codec store out.optimizerArtifact

structure AssemblySource (sha : Bytes → Bytes) (codec : Codec) (store : Store) (b : Bound)
    (c : NativeCurrentHistory.Current) (p : NativeApplyProfile.Checked) (q : Rational)
    (permission : NativeAvailableQ.Permission) (inputs : List NativeAvailableQ.Input) (out : Image) : Prop where
  currentSame : out.current = c
  originalSame : out.originalProfile = p
  quantumSame : out.quantum = q
  profile : out.profile = profileValue b.source.plan.accumulator.numbers.accumulatorBits out.quantum out.originalProfile.profile
  links : Links b out.originalProfile out.current
  checked : ProfileChecks out.originalProfile.profile out.profile
  profileArtifact : pack codec.hash (profileBytes out.profile) (.profile out.profile) = some out.profileArtifact
  graph : NativePlanProjection.check sha codec store b permission inputs out.profileArtifact.ref = some out.graph
  sizes : out.current.last.values.model.length = out.graph.isc.layout.coordinates.length ∧
    out.current.last.values.optimizer.length = out.graph.isc.layout.coordinates.length
  modelArtifact : pack codec.hash (vectorBytes "MODEL" (model out.graph.isc.schema.ref out.quantum out.current))
    (.model (model out.graph.isc.schema.ref out.quantum out.current)) = some out.modelArtifact
  optimizerArtifact : pack codec.hash (vectorBytes "OPTIMIZER" (optimizer out.graph.isc.schema.ref out.quantum out.current))
    (.optimizer (optimizer out.graph.isc.schema.ref out.quantum out.current)) = some out.optimizerArtifact
  stored : Stored codec store out.profileArtifact ∧ Stored codec store out.modelArtifact ∧ Stored codec store out.optimizerArtifact

attribute [local irreducible] Links ProfileChecks NativePlanProjection.check
  NativeVectorArtifacts.pack NativeIscProjection.Stored

theorem assembled {sha codec store b c p q permission inputs out}
    (h : assemble sha codec store b c p q permission inputs = some out) :
    AssemblySource sha codec store b c p q permission inputs out := by
  classical
  unfold assemble at h
  dsimp only at h
  by_cases checks : Links b p c ∧ ProfileChecks p.profile
      (profileValue b.source.plan.accumulator.numbers.accumulatorBits q p.profile)
  · rw [if_pos checks] at h
    simp only [bind,Option.bind_eq_some_iff] at h
    obtain ⟨pa,hpa,graph,hg,last⟩ := h
    split at last
    next sizes =>
      simp only [Option.bind_eq_some_iff] at last
      obtain ⟨m,hm,o,ho,last⟩ := last
      split at last
      next stored =>
        cases Option.some.inj last
        exact ⟨rfl,rfl,rfl,rfl,checks.1,checks.2,hpa,hg,sizes,hm,ho,stored⟩
      next _ => cases last
    next _ => cases last
  · rw [if_neg checks] at h
    contradiction

theorem constructed {sha codec store b units pid initial observation history permission inputs out}
    (h : construct sha codec store b units pid initial observation history permission inputs = some out) :
    Source sha codec store b units pid initial observation history permission inputs out := by
  simp only [construct,bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,hc,p,hp,q,hq,ha⟩ := h
  have a := assembled ha
  rw [← a.currentSame] at hc hq
  rw [← a.originalSame] at hp hq
  rw [← a.quantumSame] at hq
  exact ⟨hc,hp,hq,a.profile,a.links,a.checked,a.profileArtifact,a.graph,a.sizes,
    a.modelArtifact,a.optimizerArtifact,a.stored⟩

theorem exactSourceProfile {sha codec store b units pid initial observation history permission inputs out}
    (h : construct sha codec store b units pid initial observation history permission inputs = some out) :
    NativeApplyProfile.check sha out.originalProfile.source = some out.originalProfile :=
  (selectedSource (constructed h).originalProfile).choose_spec.choose_spec.2.2.2.2

theorem allArtifactsResolved {sha codec store b units pid initial observation history permission inputs out}
    (h : construct sha codec store b units pid initial observation history permission inputs = some out) :
    Resolves codec store out.profileArtifact.ref out.profileArtifact.raw (.profile out.profile) ∧
    Resolves codec store out.modelArtifact.ref out.modelArtifact.raw (.model (model out.graph.isc.schema.ref out.quantum out.current)) ∧
    Resolves codec store out.optimizerArtifact.ref out.optimizerArtifact.raw (.optimizer (optimizer out.graph.isc.schema.ref out.quantum out.current)) := by
  have src := constructed h
  have p := NativeIscProjection.storedResolves src.stored.1
  have m := NativeIscProjection.storedResolves src.stored.2.1
  have o := NativeIscProjection.storedResolves src.stored.2.2
  rw [(NativeVectorArtifacts.packed src.profileArtifact).2.1] at p
  rw [(NativeVectorArtifacts.packed src.modelArtifact).2.1] at m
  rw [(NativeVectorArtifacts.packed src.optimizerArtifact).2.1] at o
  exact ⟨p,m,o⟩

theorem sourceCurrentHashes {sha codec store b units pid initial raw history permission inputs out}
    (h : construct sha codec store b units pid initial (.bytes raw) history permission inputs = some out) :
    out.current.recovery.wal.state.checkpoint = idBytes (sha (valueHashInput .model out.current.last.values.model)) ∧
    out.current.recovery.wal.state.optimizer = idBytes (sha (valueHashInput .optimizer out.current.last.values.optimizer)) :=
  NativeCurrentHistory.currentValueHashes (constructed h).current

theorem adapterCurrentHashes {codec store b units pid initial raw history permission inputs out}
    (adapter : HashAdapter codec)
    (h : construct adapter.sha256 codec store b units pid initial (.bytes raw) history permission inputs = some out) :
    out.current.recovery.wal.state.checkpoint = idBytes (codec.valueHash .model out.current.last.values.model) ∧
    out.current.recovery.wal.state.optimizer = idBytes (codec.valueHash .optimizer out.current.last.values.optimizer) := by
  rw [adapter.model,adapter.optimizer]
  exact sourceCurrentHashes h

theorem exactArtifactBytes {sha codec store b units pid initial observation history permission inputs out}
    (h : construct sha codec store b units pid initial observation history permission inputs = some out) :
    out.profileArtifact.raw = profileBytes out.profile ∧
    out.modelArtifact.raw = vectorBytes "MODEL" (model out.graph.isc.schema.ref out.quantum out.current) ∧
    out.optimizerArtifact.raw = vectorBytes "OPTIMIZER" (optimizer out.graph.isc.schema.ref out.quantum out.current) :=
  ⟨(NativeVectorArtifacts.packed (constructed h).profileArtifact).1,
    (NativeVectorArtifacts.packed (constructed h).modelArtifact).1,
    (NativeVectorArtifacts.packed (constructed h).optimizerArtifact).1⟩

theorem boundedArtifacts {sha codec store b units pid initial observation history permission inputs out}
    (h : construct sha codec store b units pid initial observation history permission inputs = some out) :
    out.profileArtifact.raw.length ≤ 4194304 ∧ out.modelArtifact.raw.length ≤ 4194304 ∧
    out.optimizerArtifact.raw.length ≤ 4194304 := by
  rw [(exactArtifactBytes h).1,(exactArtifactBytes h).2.1,(exactArtifactBytes h).2.2]
  exact ⟨(NativeVectorArtifacts.packed (constructed h).profileArtifact).2.2.2.2.1,
    (NativeVectorArtifacts.packed (constructed h).modelArtifact).2.2.2.2.1,
    (NativeVectorArtifacts.packed (constructed h).optimizerArtifact).2.2.2.2.1⟩

theorem sameQuantumAndSchema {sha codec store b units pid initial observation history permission inputs out}
    (h : construct sha codec store b units pid initial observation history permission inputs = some out) :
    (model out.graph.isc.schema.ref out.quantum out.current).quantum = out.profile.applyQuantum ∧
    (optimizer out.graph.isc.schema.ref out.quantum out.current).quantum = out.profile.applyQuantum ∧
    (model out.graph.isc.schema.ref out.quantum out.current).schema = out.graph.isc.schema.ref ∧
    (optimizer out.graph.isc.schema.ref out.quantum out.current).schema = out.graph.isc.schema.ref := by
  rw [(constructed h).profile]; exact ⟨rfl,rfl,rfl,rfl⟩

theorem noUnitsRejected {sha codec store b pid initial observation history permission inputs} :
    construct sha codec store b (fun _ => none) pid initial observation history permission inputs = none := by
  simp [construct]

theorem unknownRejected {sha codec store b units pid initial history permission inputs} :
    construct sha codec store b units pid initial .unknown history permission inputs = none := rfl

structure Preparation where
  policy : Bytes
  state : Bytes
  apc : Bytes
  config : Bytes
  proof : Bytes
  workerProfile : Bytes
  eligible : List NativeAvailableQ.Input

def run (sha : Bytes → Bytes) (codec : Codec) (store : Store) (s : Preparation)
    (units : UnitSource) (pid : Bytes) (initial : NativeCurrentPointer.State)
    (observation : NativePointerWal.Observation) (history : List NativeCurrentHistory.Input)
    (permission : NativeAvailableQ.Permission) (inputs : List NativeAvailableQ.Input) : Option (Bound × Image) := do
  let b ← NativeVectorContext.bind sha s.policy s.state s.apc s.config s.proof s.workerProfile permission s.eligible
  let out ← construct sha codec store b units pid initial observation history permission inputs
  some (b,out)

theorem runSource {sha codec store s units pid initial observation history permission inputs b out}
    (h : run sha codec store s units pid initial observation history permission inputs = some (b,out)) :
    NativeVectorContext.bind sha s.policy s.state s.apc s.config s.proof s.workerProfile permission s.eligible = some b ∧
    construct sha codec store b units pid initial observation history permission inputs = some out := by
  simp only [run,bind,Option.bind_eq_some_iff] at h
  obtain ⟨b',hb,out',ho,last⟩ := h
  cases Option.some.inj last
  exact ⟨hb,ho⟩

end DeltaReduce.NativeStateProjection
