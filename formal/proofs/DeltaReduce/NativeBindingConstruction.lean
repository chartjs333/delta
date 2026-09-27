import DeltaReduce.NativeAuthorityProjection

/-! Construct a pre-aggregate Binding from executed source projections and full
store closure. Authentication remains named external premises, never inferred
from graph closure, successful hashing, or availability of UnitSource. -/
namespace DeltaReduce.NativeBindingConstruction
open NativeBinding
open NativeVectorContext (Bound)
open NativeVectorArtifacts (Artifact)
open NativeStateProjection (model optimizer)

def anchor (codec : Codec) (b : Bound) (s : NativeStateProjection.Image) (root : Artifact) : Anchor :=
  ⟨root.ref,NativeVectorAuthority.context b,
    codec.valueHash .model s.current.last.values.model,
    codec.valueHash .optimizer s.current.last.values.optimizer,none⟩

structure Premises (trust : Trust) (codec : Codec) (b : Bound)
    (s : NativeStateProjection.Image) (root : Artifact) : Prop where
  nativeAnchor : trust.anchorAuthenticated (anchor codec b s root)
  nativeRecovery : trust.recoveryAuthenticated (anchor codec b s root)
  isc : trust.certificateAuthenticated s.graph.isc.isc.ref
  ec : trust.certificateAuthenticated s.graph.isc.ec.ref
  apc : trust.certificateAuthenticated s.graph.apc.ref

def binding {codec store depth b units pid initial observation history permission inputs s root trust}
    (adapter : HashAdapter codec)
    (source : NativeStateProjection.construct adapter.sha256 codec store b units pid initial observation history permission inputs = some s)
    (closed : NativeAuthorityProjection.check codec store depth b s = some root)
    (auth : Premises trust codec b s root) : Binding codec trust (anchor codec b s root) store where
  authenticatedAnchor := auth.nativeAnchor
  authenticatedRecovery := auth.nativeRecovery
  complete := by
    intro ref mem
    have eq : ref = root.ref := by simpa [anchor,Anchor.roots] using mem
    subst ref
    exact NativeAuthorityProjection.rootComplete closed
  authorityBytes := root.raw
  authority := NativeAuthorityProjection.value b s
  authorityResolved := NativeAuthorityProjection.rootResolved closed
  contextMatches := rfl
  iscAuthenticated := auth.isc
  ecAuthenticated := auth.ec
  apcAuthenticated := auth.apc
  modelBytes := s.modelArtifact.raw
  model := model s.graph.isc.schema.ref s.quantum s.current
  modelWalk := .step (NativeAuthorityProjection.rootResolved closed) (by rfl)
    (.here (NativeStateProjection.allArtifactsResolved source).2.1)
  modelSchema := rfl
  modelCurrent := rfl
  optimizerBytes := s.optimizerArtifact.raw
  optimizer := optimizer s.graph.isc.schema.ref s.quantum s.current
  optimizerWalk := .step (NativeAuthorityProjection.rootResolved closed) (by rfl)
    (.here (NativeStateProjection.allArtifactsResolved source).2.2)
  optimizerSchema := rfl
  optimizerCurrent := rfl
  profileBytes := s.profileArtifact.raw
  profile := s.profile
  profileWalk := .step (NativeAuthorityProjection.rootResolved closed) (by rfl)
    (.here (NativeStateProjection.allArtifactsResolved source).1)
  modelQuantum := (NativeStateProjection.sameQuantumAndSchema source).1
  optimizerQuantum := (NativeStateProjection.sameQuantumAndSchema source).2.1
  aggregateBound := by intro ref impossible; cases impossible

theorem originalCurrentHashes {codec store b units pid initial raw history permission inputs s root}
    (adapter : HashAdapter codec)
    (source : NativeStateProjection.construct adapter.sha256 codec store b units pid initial (.bytes raw) history permission inputs = some s) :
    s.current.recovery.wal.state.checkpoint = idBytes (anchor codec b s root).currentModelHash ∧
    s.current.recovery.wal.state.optimizer = idBytes (anchor codec b s root).currentOptimizerHash :=
  NativeStateProjection.adapterCurrentHashes adapter source

theorem noAggregate (codec b s root) : (anchor codec b s root).aggregate = none := rfl

theorem noAuthenticationFromClosure {trust codec b s root}
    (absent : ¬ trust.anchorAuthenticated (anchor codec b s root)) :
    ¬ Premises trust codec b s root := fun p => absent p.nativeAnchor

def fromRun {codec store depth prep units pid initial observation history permission inputs b s root trust}
    (adapter : HashAdapter codec)
    (ran : NativeAuthorityProjection.run adapter.sha256 codec store depth prep units pid initial observation history permission inputs = some (b,s,root))
    (auth : Premises trust codec b s root) : Binding codec trust (anchor codec b s root) store :=
  binding adapter (NativeStateProjection.runSource (NativeAuthorityProjection.runSource ran).1).2
    (NativeAuthorityProjection.runSource ran).2 auth

theorem originalPreparation {sha codec store depth prep units pid initial observation history permission inputs b s root}
    (ran : NativeAuthorityProjection.run sha codec store depth prep units pid initial observation history permission inputs = some (b,s,root)) :
    NativeVectorContext.bind sha prep.policy prep.state prep.apc prep.config prep.proof prep.workerProfile permission prep.eligible = some b :=
  (NativeStateProjection.runSource (NativeAuthorityProjection.runSource ran).1).1

theorem retainedArtifacts {codec store depth prep units pid initial observation history permission inputs b s root trust}
    (adapter : HashAdapter codec)
    (ran : NativeAuthorityProjection.run adapter.sha256 codec store depth prep units pid initial observation history permission inputs = some (b,s,root))
    (auth : Premises trust codec b s root) :
    (fromRun adapter ran auth).authorityBytes = root.raw ∧
    (fromRun adapter ran auth).modelBytes = s.modelArtifact.raw ∧
    (fromRun adapter ran auth).optimizerBytes = s.optimizerArtifact.raw ∧
    (fromRun adapter ran auth).profileBytes = s.profileArtifact.raw ∧
    (fromRun adapter ran auth).model.values = s.current.last.values.model ∧
    (fromRun adapter ran auth).optimizer.values = s.current.last.values.optimizer := ⟨rfl,rfl,rfl,rfl,rfl,rfl⟩

def parameter {codec store depth prep units pid initial observation history permission inputs b s root trust}
    (adapter : HashAdapter codec)
    (ran : NativeAuthorityProjection.run adapter.sha256 codec store depth prep units pid initial observation history permission inputs = some (b,s,root))
    (auth : Premises trust codec b s root) (domain : Bytes) (index : Nat) :=
  NativeVectorAuthority.verify (fromRun adapter ran auth) adapter.sha256 b domain index

theorem parameterNumbers {codec store depth prep units pid initial observation history permission inputs b s root trust}
    (adapter : HashAdapter codec)
    (ran : NativeAuthorityProjection.run adapter.sha256 codec store depth prep units pid initial observation history permission inputs = some (b,s,root))
    (auth : Premises trust codec b s root) {domain index out}
    (verified : parameter adapter ran auth domain index = some out) :
    out.selected.original.certificate.common.numerators.map NativeCertificateDecimal.number = out.computation.out.values :=
  NativeVectorAuthority.verifiedNumbers verified

theorem parameterLeafCoverage {codec store depth prep units pid initial observation history permission inputs b s root trust}
    (adapter : HashAdapter codec)
    (ran : NativeAuthorityProjection.run adapter.sha256 codec store depth prep units pid initial observation history permission inputs = some (b,s,root))
    (auth : Premises trust codec b s root) {domain index out}
    (verified : parameter adapter ran auth domain index = some out) :
    out.selected.original.certificate.common.leaves.Perm out.leaves ∧
    out.leaves.length = out.computation.out.slices.length :=
  NativeVectorAuthority.verifiedLeaves verified

end DeltaReduce.NativeBindingConstruction
