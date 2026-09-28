import DeltaReduce.NativeCertifiedCorpus
import DeltaReduce.NativeApplyResult
import DeltaReduce.NativeApplySection

/-! Computed aggregate bytes and an authenticated-anchor extension. All trust
premises are explicit; original QC identity is never a projected artifact hash. -/
namespace DeltaReduce.NativeAggregateBinding
open NativeBinding
open NativeVectorArtifacts (Artifact pack)
open NativeIscProjection (Stored)

def encode (authority : ContentId) (parameters : List Bytes) : Bytes :=
  asciiBytes "{\"kind\":\"AGGREGATE_PROJECTION\",\"payload\":{\"authority_id\":" ++
  quotedBytes (idBytes authority) ++ asciiBytes ",\"parameters\":" ++ arrayBytes parameters ++ [125,125]

def extended (a : Anchor) (r : Ref) : Anchor := { a with aggregate := some r }

/-- Separately authenticated original certificate and projection provenance.
Availability, arithmetic, and self-consistent hashing cannot provide this. -/
def CertificateAuthority := NativePolicyCodec.Value → Bytes → Artifact → Prop

section Extension
variable {codec store trust anchor} (binding : Binding codec trust anchor store)

def artifact (image : NativeCertifiedCorpus.Image binding) : Option Artifact := do
  let parameters ← encodeParameterBodies (image.corpus.entries.map BoundParameter.body)
  let root ← pack codec.hash (encode anchor.authority.id parameters)
    (.aggregate anchor.authority.id (image.corpus.entries.map BoundParameter.body))
  if Stored codec store root then some root else none

attribute [local irreducible] Stored NativeVectorArtifacts.pack

theorem artifactSource {image root} (h : artifact binding image = some root) :
    ∃ parameters, encodeParameterBodies (image.corpus.entries.map BoundParameter.body) = some parameters ∧
      pack codec.hash (encode anchor.authority.id parameters)
        (.aggregate anchor.authority.id (image.corpus.entries.map BoundParameter.body)) = some root ∧
      Stored codec store root := by
  simp only [artifact,bind,Option.bind_eq_some_iff] at h
  obtain ⟨ps,hps,r,hr,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨ps,hps,hr,by assumption⟩

theorem aggregateResolved {image root} (h : artifact binding image = some root) :
    Resolves codec store root.ref root.raw
      (.aggregate anchor.authority.id (image.corpus.entries.map BoundParameter.body)) := by
  obtain ⟨ps,_,packed,stored⟩ := artifactSource binding h
  have r := NativeIscProjection.storedResolves stored
  rw [(NativeVectorArtifacts.packed packed).2.1] at r
  exact r

theorem aggregateComplete {image root} (h : artifact binding image = some root) :
    Complete codec store root.ref :=
  .node (aggregateResolved binding h) (by intro i child bad; simp [Payload.refs,Payload.edges] at bad)

structure Premises (authority : CertificateAuthority) (image : NativeCertifiedCorpus.Image binding)
    (root : Artifact) : Prop where
  nativeAnchor : trust.anchorAuthenticated (extended anchor root.ref)
  nativeRecovery : trust.recoveryAuthenticated (extended anchor root.ref)
  originalCertificate : authority image.root.source image.root.id root
  projectedCertificate : trust.certificateAuthenticated root.ref

def extend {b id image root authority} (adapter : HashAdapter codec)
    (_source : NativeCertifiedCorpus.check binding adapter.sha256 b id = some image)
    (made : artifact binding image = some root) (auth : Premises binding authority image root) :
    Binding codec trust (extended anchor root.ref) store where
  authenticatedAnchor := auth.nativeAnchor
  authenticatedRecovery := auth.nativeRecovery
  complete := by
    intro r mem
    have choices : r = anchor.authority ∨ r = root.ref := by simpa [extended,Anchor.roots] using mem
    rcases choices with rfl | rfl
    · exact binding.complete anchor.authority (by simp [Anchor.roots])
    · exact aggregateComplete binding made
  authorityBytes := binding.authorityBytes
  authority := binding.authority
  authorityResolved := binding.authorityResolved
  contextMatches := binding.contextMatches
  iscAuthenticated := binding.iscAuthenticated
  ecAuthenticated := binding.ecAuthenticated
  apcAuthenticated := binding.apcAuthenticated
  modelBytes := binding.modelBytes
  model := binding.model
  modelWalk := binding.modelWalk
  modelSchema := binding.modelSchema
  modelCurrent := binding.modelCurrent
  optimizerBytes := binding.optimizerBytes
  optimizer := binding.optimizer
  optimizerWalk := binding.optimizerWalk
  optimizerSchema := binding.optimizerSchema
  optimizerCurrent := binding.optimizerCurrent
  profileBytes := binding.profileBytes
  profile := binding.profile
  profileWalk := binding.profileWalk
  modelQuantum := binding.modelQuantum
  optimizerQuantum := binding.optimizerQuantum
  aggregateBound := by
    intro r eq
    cases Option.some.inj eq
    exact ⟨auth.projectedCertificate,root.raw,image.corpus.entries.map BoundParameter.body,
      aggregateResolved binding made⟩

theorem unchangedAuthority {b id image root authority} (adapter : HashAdapter codec)
    (source : NativeCertifiedCorpus.check binding adapter.sha256 b id = some image)
    (made : artifact binding image = some root) (auth : Premises binding authority image root) :
    (extend binding adapter source made auth).authorityBytes = binding.authorityBytes ∧
    (extend binding adapter source made auth).authority = binding.authority ∧
    (extend binding adapter source made auth).model = binding.model ∧
    (extend binding adapter source made auth).optimizer = binding.optimizer ∧
    (extend binding adapter source made auth).profile = binding.profile := ⟨rfl,rfl,rfl,rfl,rfl⟩

theorem noInventedCertificate {authority image root}
    (absent : ¬ authority image.root.source image.root.id root) :
    ¬ Premises binding authority image root := fun p => absent p.originalCertificate

theorem hashPreimage {image root} (adapter : HashAdapter codec) (h : artifact binding image = some root) :
    ∃ parameters, encodeParameterBodies (image.corpus.entries.map BoundParameter.body) = some parameters ∧
      root.ref.id = adapter.sha256 (artifactHashInput (encode anchor.authority.id parameters)) := by
  obtain ⟨ps,encoded,packed,_⟩ := artifactSource binding h
  refine ⟨ps,encoded,?_⟩
  rw [(NativeVectorArtifacts.packed packed).2.2.1]
  exact adapter.artifact _

end Extension

section Apply
variable {codec store trust anchor} (binding : Binding codec trust anchor store)

def ApplyLinks (root : NativeAggregateLineage.Edge) (profileId : Bytes) (e : NativeApplyLineage.Edge) : Prop :=
  e.root.id = root.id ∧ e.root.certificate = root.certificate ∧ e.profile.id = profileId
instance (root profileId e) : Decidable (ApplyLinks root profileId e) := by unfold ApplyLinks; infer_instance

structure Applied where
  loaded : NativeApplySection.Bound
  original : NativeApplyLineage.Edge
  checked : NativeApplyResult.Checked binding

def checkApply (adapter : HashAdapter codec) (b : NativeVectorContext.Bound)
    (root : NativeAggregateLineage.Edge) (profileId candidateId : Bytes) : Option (Applied binding) := do
  let loaded ← NativeApplySection.bindSection adapter.sha256 (NativeVectorAuthority.policy b) (NativeVectorAuthority.state b)
  let original ← loaded.bodies.find? (fun e => e.id == candidateId)
  if ApplyLinks root profileId original then
    let checked ← NativeApplyResult.check binding adapter.sha256 original
    some ⟨loaded,original,checked⟩ else none

attribute [local irreducible] ApplyLinks

theorem applySource {adapter b root profileId candidateId out}
    (h : checkApply binding adapter b root profileId candidateId = some out) :
    NativeApplySection.bindSection adapter.sha256 (NativeVectorAuthority.policy b) (NativeVectorAuthority.state b) = some out.loaded ∧
    out.loaded.bodies.find? (fun e => e.id == candidateId) = some out.original ∧
    ApplyLinks root profileId out.original ∧
    NativeApplyResult.check binding adapter.sha256 out.original = some out.checked := by
  simp only [checkApply,bind,Option.bind_eq_some_iff] at h
  obtain ⟨s,hs,e,he,last⟩ := h
  split at last <;> try contradiction
  rename_i links
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨result,hr,last⟩ := last
  cases Option.some.inj last
  exact ⟨hs,he,links,hr⟩

theorem originalCandidate {adapter b root profileId candidateId out}
    (h : checkApply binding adapter b root profileId candidateId = some out) :
    NativeApplyLineage.check adapter.sha256 .proposed
      (NativeParameterSection.expected (NativeVectorAuthority.policy b) (NativeVectorAuthority.state b) out.loaded.roots.parameters.prior.plans)
      (NativeVectorAuthority.policy b).validators (NativeVectorAuthority.state b).wire.parent
      out.loaded.roots.finalized out.loaded.roots.certificates out.loaded.profiles out.original.source = some out.original :=
  NativeApplySection.proposedChecked (applySource binding h).1
    (List.mem_of_find?_eq_some (applySource binding h).2.1)

theorem exactOutput {adapter b root profileId candidateId out}
    (h : checkApply binding adapter b root profileId candidateId = some out) :
    out.original.decoded.candidate.modelValues = NativeApplyResult.decimalValues out.checked.result.body.nextModel ∧
    out.original.decoded.candidate.optimizerValues = NativeApplyResult.decimalValues out.checked.result.body.nextOptimizer :=
  NativeApplyResult.exactComputedValues binding (applySource binding h).2.2.2

theorem exactHashes {adapter b root profileId candidateId out}
    (h : checkApply binding adapter b root profileId candidateId = some out) :
    out.original.decoded.candidate.model = idBytes out.checked.result.body.nextModelHash ∧
    out.original.decoded.candidate.optimizer = idBytes out.checked.result.body.nextOptimizerHash ∧
    out.original.decoded.candidate.parent = idBytes anchor.currentModelHash ∧
    out.original.decoded.candidate.parentOptimizer = idBytes anchor.currentOptimizerHash :=
  NativeApplyResult.exactComputedHashes binding (applySource binding h).2.2.2

theorem originalRootBytes {oldAnchor} (base : Binding codec trust oldAnchor store)
    {adapter b id image profileId candidateId out}
    (source : NativeCertifiedCorpus.check base adapter.sha256 b id = some image)
    (h : checkApply binding adapter b image.root profileId candidateId = some out) :
    out.original.root.source = image.root.source := by
  have src := applySource binding h
  have candidate := originalCandidate binding h
  have newRoot := NativeApplySection.selectedRoot src.1 candidate
  have oldRoot := NativeCertifiedCorpus.originalRoot base source
  have left := NativeAggregateLineage.decodedOriginal (NativeAggregateLineage.checkedSource newRoot).decoded
  have right := NativeAggregateLineage.decodedOriginal (NativeAggregateLineage.checkedSource oldRoot).decoded
  have links := src.2.2.1
  unfold ApplyLinks at links
  exact left.trans ((congrArg (NativeAggregateLineage.original .finalized) links.2.1).trans right.symm)

end Apply

/-- Same raw source construction and selected original profile as the prior API.
Independent trust premises are not inferred by the wrapper. -/
def fromSource {codec store depth prep units pid initial observation history permission inputs b s root trust}
    (adapter : HashAdapter codec)
    (ran : NativeAuthorityProjection.run adapter.sha256 codec store depth prep units pid initial observation history permission inputs = some (b,s,root))
    (auth : NativeBindingConstruction.Premises trust codec b s root)
    {id image aggregate authority}
    (source : NativeCertifiedCorpus.check (NativeBindingConstruction.fromRun adapter ran auth) adapter.sha256 b id = some image)
    (made : artifact (NativeBindingConstruction.fromRun adapter ran auth) image = some aggregate)
    (aggregateAuth : Premises (NativeBindingConstruction.fromRun adapter ran auth) authority image aggregate)
    (candidateId : Bytes) :=
  checkApply (extend (NativeBindingConstruction.fromRun adapter ran auth) adapter source made aggregateAuth)
    adapter b image.root s.originalProfile.id candidateId

end DeltaReduce.NativeAggregateBinding
