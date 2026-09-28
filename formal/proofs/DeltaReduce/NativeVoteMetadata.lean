import DeltaReduce.NativeArithmeticPrefix

/-! Lossless candidate metadata projection. The complete original VOTE and all
parent slots accompany the distinct draft envelope. Recovery scanning does not
establish readiness, authenticated metadata, physical persistence or exposure. -/
namespace DeltaReduce.NativeVoteMetadata
open NativeBinding
open NativeVectorAuthority (policy state)
open NativeVectorLayout (text shardName)
open NativeVoteBytes (Vote)
open NativeConfigAdmission (RuntimeFacts)

def readText (raw : Bytes) : Option String :=
  if asciiBytes (text raw) = raw ∧ (∀ byte ∈ raw, byte.toNat ≤ 127) then some (text raw) else none

theorem textRetained {raw value} (h : readText raw = some value) :
    asciiBytes value = raw := by
  unfold readText at h; split at h <;> try contradiction
  cases Option.some.inj h
  exact (by assumption : asciiBytes (text raw) = raw ∧ (∀ byte ∈ raw, byte.toNat ≤ 127)).1

def readDigest (original : Bytes) : Option Bytes := do
  let digest ← NativeAggregateMerkle.digestBytes original
  if digest.length = 32 ∧ idBytes digest = original then some digest else none

theorem digestRetained {original digest} (h : readDigest original = some digest) :
    NativeAggregateMerkle.digestBytes original = some digest ∧
    digest.length = 32 ∧ idBytes digest = original := by
  simp only [readDigest,bind,Option.bind_eq_some_iff] at h
  obtain ⟨d,hd,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨hd,by assumption⟩

def Header (anchor : Anchor) (b : NativeVectorContext.Bound) (v : Vote) : Prop :=
  anchor.context = NativeVectorAuthority.context b ∧
  asciiBytes anchor.context.round = v.wire.round ∧
  asciiBytes anchor.context.epoch = v.wire.epoch ∧
  asciiBytes anchor.context.parentCheckpoint = (state b).wire.parent ∧
  anchor.context.height = v.height ∧ anchor.context.view = v.view
instance (anchor b v) : Decidable (Header anchor b v) := by unfold Header; infer_instance

structure Fields where
  actor : String
  context : String
  parent : Bytes
  deriving DecidableEq, Repr

def fields (actor context parent : Bytes) : Option Fields := do
  let a ← readText actor
  let c ← readText context
  let p ← readDigest parent
  some ⟨a,c,p⟩

theorem fieldsRetained {actor context parent out} (h : fields actor context parent = some out) :
    asciiBytes out.actor = actor ∧ asciiBytes out.context = context ∧
    NativeAggregateMerkle.digestBytes parent = some out.parent ∧
    out.parent.length = 32 ∧ idBytes out.parent = parent := by
  simp only [fields,bind,Option.bind_eq_some_iff] at h
  obtain ⟨a,ha,c,hc,p,hp,last⟩ := h
  cases Option.some.inj last
  exact ⟨textRetained ha,textRetained hc,digestRetained hp⟩

/-- Conservative candidate interpretation of a completed live readiness flag.
Recovery mode itself never sets the draft recovered field. Authentication of
the supplied flags is a separate event/export premise. -/
def completed (r : RuntimeFacts) : Bool := r.ready && !r.recovery && !r.invalidated

def metadata (kind : VoteKind) (projection : Ref) (p : NativePolicyBytes.Policy)
    (r : RuntimeFacts) (v : Vote) (f : Fields) : VoteMetadata :=
  ⟨f.actor,kind,f.context,f.parent,projection,r.tick,completed r,
    decide (v.wire.validator = p.localValidator ∧ v.wire.validator ∈ p.validators)⟩

theorem metadataFields (kind projection p r v f) :
    (metadata kind projection p r v f).kind = kind ∧
    (metadata kind projection p r v f).projection = projection ∧
    (metadata kind projection p r v f).logicalTime = r.tick ∧
    (metadata kind projection p r v f).recovered = completed r := ⟨rfl,rfl,rfl,rfl⟩

theorem scanningNotCompleted {r : RuntimeFacts} (scan : r.recovery = true) : completed r = false := by
  simp [completed,scan]

theorem validatorMembership {kind projection p r v f}
    (h : (metadata kind projection p r v f).validator = true) :
    v.wire.validator = p.localValidator ∧ v.wire.validator ∈ p.validators := by
  simpa [metadata] using h

section Projection
variable {codec store trust anchor} (binding : Binding codec trust anchor store)

structure Image where
  original : Vote
  parents : NativeCandidateShape.Parents
  metadata : VoteMetadata
  expected : ExpectedNativeVote binding metadata

/-- This low-level encoder needs an actual VoteSource. The public parameter and
apply functions below obtain that source by executing original candidate checks.
This encoder alone is not a vote admission gate. -/
def encode {kind} (source : VoteSource binding kind) (b : NativeVectorContext.Bound)
    (r : RuntimeFacts) (v : Vote) (parents : NativeCandidateShape.Parents) (parent : Bytes) :
    Option (Image binding) := do
  let f ← fields v.wire.validator v.wire.context parent
  if Header anchor b v then
    let m := metadata kind source.projection (policy b) r v f
    if ctx : source.contextMatches m.voteContext = true then
      match hb : source.bodyBytes with
      | none => none
      | some body =>
        match hc : encodeVoteContext m with
        | none => none
        | some context =>
          match he : encodeVoteEnvelope anchor m (codec.hash body) with
          | none => none
          | some envelope =>
            some ⟨v,parents,m,⟨source,body,hb,rfl,ctx,context,hc,envelope,he⟩⟩
    else none
  else none

theorem encoded {kind source b r v parents parent out}
    (h : @encode _ _ _ _ binding kind source b r v parents parent = some out) :
    ∃ f, fields v.wire.validator v.wire.context parent = some f ∧
      Header anchor b v ∧ out.original = v ∧ out.parents = parents ∧
      out.metadata = metadata kind source.projection (policy b) r v f ∧
      source.bodyBytes = some out.expected.body := by
  simp only [encode,bind,Option.bind_eq_some_iff] at h
  obtain ⟨f,hf,last⟩ := h
  split at last <;> try contradiction
  rename_i header
  split at last <;> try contradiction
  split at last <;> try contradiction
  rename_i body hb
  split at last <;> try contradiction
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨f,hf,header,rfl,rfl,rfl,hb⟩

theorem originalMetadata {kind source b r v parents parent out}
    (h : @encode _ _ _ _ binding kind source b r v parents parent = some out) :
    asciiBytes out.metadata.actor = v.wire.validator ∧
    asciiBytes out.metadata.voteContext = v.wire.context ∧
    idBytes out.metadata.parentCertificate = parent ∧
    out.metadata.parentCertificate.length = 32 ∧
    out.metadata.kind = kind ∧ out.metadata.projection = source.projection ∧
    out.metadata.logicalTime = r.tick ∧ out.metadata.recovered = completed r := by
  obtain ⟨f,hf,_,_,_,hm,_⟩ := encoded binding h
  have kept := fieldsRetained hf
  rw [hm]
  exact ⟨kept.1,kept.2.1,kept.2.2.2.2,kept.2.2.2.1,rfl,rfl,rfl,rfl⟩

theorem originalHeader {kind source b r v parents parent out}
    (h : @encode _ _ _ _ binding kind source b r v parents parent = some out) :
    Header anchor b v := by obtain ⟨_,_,header,_⟩ := encoded binding h; exact header

theorem completeOriginal {kind source b r v parents parent out}
    (h : @encode _ _ _ _ binding kind source b r v parents parent = some out) :
    NativeVoteBytes.encodeFrame out.original.wire = NativeVoteBytes.encodeFrame v.wire ∧
    out.original.sequence = v.sequence ∧ out.original.view = v.view ∧
    out.original.wire.signature = v.wire.signature ∧ out.parents = parents := by
  obtain ⟨_,_,_,hv,hp,_⟩ := encoded binding h
  rw [hv]; exact ⟨rfl,rfl,rfl,rfl,hp⟩

theorem projectedHashPreimage {kind source b r v parents parent out}
    (adapter : HashAdapter codec)
    (h : @encode _ _ _ _ binding kind source b r v parents parent = some out) :
    source.bodyBytes = some out.expected.body ∧
    codec.hash out.expected.body = adapter.sha256 (artifactHashInput out.expected.body) := by
  obtain ⟨_,_,_,_,_,_,hb⟩ := encoded binding h
  exact ⟨hb,adapter.artifact _⟩

theorem wrongHeaderRejects {kind source b r v parents parent}
    (bad : ¬ Header anchor b v) :
    @encode _ _ _ _ binding kind source b r v parents parent = none := by
  cases h : encode binding source b r v parents parent with
  | none => rfl
  | some out => exact False.elim (bad (originalHeader binding h))

theorem scanCannotPrepare {kind source b r v parents parent out}
    (h : @encode _ _ _ _ binding kind source b r v parents parent = some out)
    (scan : r.recovery = true) (voteTrust : NativeVoteTrust)
    (auth : voteTrust.authenticated anchor out.metadata) (mode durable request) :
    prepareNativeFirst binding voteTrust out.metadata auth mode durable request = none := by
  have retained := (originalMetadata binding h).2.2.2.2.2.2.2
  have bad : out.metadata.recovered = false := retained.trans (scanningNotCompleted scan)
  apply nativeFirstRejectsUnready auth
  intro fresh
  have good := fresh.2.1
  simp [bad] at good

structure Parameter (b : NativeVectorContext.Bound) where
  checked : NativeArithmeticVote.Parameter binding b
  image : Image binding

def parameter (adapter : HashAdapter codec) (b : NativeVectorContext.Bound)
    (r : RuntimeFacts) (v : Vote) : Option (Parameter binding b) := do
  let checked ← NativeArithmeticVote.parameter binding adapter b r v
  let image ← encode binding (.parameter checked.computed.computation.native) b r v
    checked.admitted.selected.parents checked.body.certificate.common.plan
  some ⟨checked,image⟩

theorem parameterSource {adapter b r v out} (h : parameter binding adapter b r v = some out) :
    NativeArithmeticVote.parameter binding adapter b r v = some out.checked ∧
    encode binding (.parameter out.checked.computed.computation.native) b r v
      out.checked.admitted.selected.parents out.checked.body.certificate.common.plan = some out.image := by
  simp only [parameter,bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,hc,i,hi,last⟩ := h
  cases Option.some.inj last
  exact ⟨hc,hi⟩

theorem parameterBodies {b r v out} (adapter : HashAdapter codec)
    (h : parameter binding adapter b r v = some out) :
    NativeParameter.bodyId adapter.sha256 (NativeParameterLineage.asBody out.checked.body) = some v.wire.bodyHash ∧
    encodeParameterBody out.checked.computed.computation.native.body = some out.image.expected.body ∧
    codec.hash out.image.expected.body = adapter.sha256 (artifactHashInput out.image.expected.body) := by
  have src := parameterSource binding h
  exact ⟨NativeArithmeticVote.parameterPreimage binding src.1,
    projectedHashPreimage binding adapter src.2⟩

theorem parameterMetadata {adapter b r v out} (h : parameter binding adapter b r v = some out) :
    out.image.metadata.kind = .parameter (text out.checked.body.certificate.common.domain) (shardName out.checked.index) ∧
    out.image.metadata.projection = binding.authority.apc ∧
    idBytes out.image.metadata.parentCertificate = out.checked.body.certificate.common.plan ∧
    asciiBytes out.image.metadata.voteContext = v.wire.context := by
  have kept :=  originalMetadata binding (parameterSource binding h).2
  exact ⟨kept.2.2.2.2.1,kept.2.2.2.2.2.1,kept.2.2.1,kept.2.1⟩

structure Applied where
  checked : NativeArithmeticVote.Applied binding
  image : Image binding

def applyVote (adapter : HashAdapter codec) (b : NativeVectorContext.Bound)
    (root : NativeAggregateLineage.Edge) (profileId : Bytes) (r : RuntimeFacts) (v : Vote) :
    Option (Applied binding) := do
  let checked ← NativeArithmeticVote.applyVote binding adapter b root profileId r v
  let image ← encode binding (.apply checked.computed.checked.result) b r v
    checked.admitted.selected.parents checked.computed.original.decoded.candidate.root
  some ⟨checked,image⟩

theorem applySource {adapter b root profileId r v out}
    (h : applyVote binding adapter b root profileId r v = some out) :
    NativeArithmeticVote.applyVote binding adapter b root profileId r v = some out.checked ∧
    encode binding (.apply out.checked.computed.checked.result) b r v
      out.checked.admitted.selected.parents out.checked.computed.original.decoded.candidate.root = some out.image := by
  simp only [applyVote,bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,hc,i,hi,last⟩ := h
  cases Option.some.inj last
  exact ⟨hc,hi⟩

theorem applyBodies {b root profileId r v out} (adapter : HashAdapter codec)
    (h : applyVote binding adapter b root profileId r v = some out) :
    NativeApplyCertificate.candidateId adapter.sha256 out.checked.computed.original.decoded.candidate = some v.wire.bodyHash ∧
    out.image.expected.body = out.checked.computed.checked.result.bytes ∧
    codec.hash out.image.expected.body = adapter.sha256 (artifactHashInput out.image.expected.body) := by
  have src := applySource binding h
  have projected := projectedHashPreimage binding adapter src.2
  exact ⟨NativeArithmeticVote.applyPreimage binding src.1,(Option.some.inj projected.1).symm,projected.2⟩

theorem applyMetadata {adapter b root profileId r v out}
    (h : applyVote binding adapter b root profileId r v = some out) :
    out.image.metadata.kind = .apply ∧
    out.image.metadata.projection = out.checked.computed.checked.result.core.conversion.certified.aggregate ∧
    idBytes out.image.metadata.parentCertificate = out.checked.computed.original.decoded.candidate.root ∧
    NativeCandidateAuthority.parentContext adapter.sha256 "deltareduce.vote-context.apply.v1"
      out.checked.computed.original.decoded.candidate.root = some (asciiBytes out.image.metadata.voteContext) := by
  have src := applySource binding h
  have kept :=  originalMetadata binding src.2
  exact ⟨kept.2.2.2.2.1,kept.2.2.2.2.2.1,kept.2.2.1,
    kept.2.1 ▸ (NativeArithmeticVote.applyIdentity binding src.1).2⟩

def nextImage {b} (n : NativeArithmeticPrefix.Next binding b) : Option (Image binding) :=
  match n.computation with
  | .parameter p => encode binding (.parameter p.computed.computation.native) b
      (NativeArithmeticPrefix.facts n.before) n.vote p.admitted.selected.parents p.body.certificate.common.plan
  | .apply p => encode binding (.apply p.computed.checked.result) b
      (NativeArithmeticPrefix.facts n.before) n.vote p.admitted.selected.parents p.computed.original.decoded.candidate.root

theorem nextRetained {b n out} (h : @nextImage _ _ _ _ binding b n = some out) :
    out.original = n.vote ∧ out.metadata.recovered = false ∧
    out.metadata.logicalTime = n.before.prior.core.tick := by
  unfold nextImage at h
  split at h
  all_goals
    obtain ⟨f,hf,header,hv,hp,hm,hb⟩ := encoded binding h
    rw [hm]
    exact ⟨hv,rfl,rfl⟩

structure Next (b : NativeVectorContext.Bound) where
  original : NativeArithmeticPrefix.Next binding b
  image : Image binding

/-- Actual original mixed-prefix execution is mandatory. All original entry,
vote, receipt and arithmetic objects remain in the result alongside the draft. -/
def checkNext (adapter : HashAdapter codec) {b policyRaw stateRaw apc config proof profile permission inputs}
    (loaded : NativeVectorContext.bind adapter.sha256 policyRaw stateRaw apc config proof profile permission inputs = some b)
    (initial : Bytes) (snapshot : Option NativeCommandReplay.Snapshot)
    (observation : Option Bytes) (nextRaw : Bytes)
    (application : Option (NativeAggregateLineage.Edge × Bytes)) : Option (Next binding b) := do
  let original ← NativeArithmeticPrefix.check binding adapter loaded initial snapshot observation nextRaw application
  let image ← nextImage binding original
  some ⟨original,image⟩

theorem checkedNext {adapter b policyRaw stateRaw apc config proof profile permission inputs
    loaded initial snapshot observation nextRaw application out}
    (h : @checkNext _ _ _ _ binding adapter b policyRaw stateRaw apc config proof profile permission inputs
      loaded initial snapshot observation nextRaw application = some out) :
    NativeArithmeticPrefix.check binding adapter loaded initial snapshot observation nextRaw application = some out.original ∧
    nextImage binding out.original = some out.image := by
  simp only [checkNext,bind,Option.bind_eq_some_iff] at h
  obtain ⟨n,hn,i,hi,last⟩ := h
  cases Option.some.inj last
  exact ⟨hn,hi⟩

theorem nextCannotPrepare {b n out} (h : @nextImage _ _ _ _ binding b n = some out)
    (voteTrust : NativeVoteTrust) (auth : voteTrust.authenticated anchor out.metadata) (mode durable request) :
    prepareNativeFirst binding voteTrust out.metadata auth mode durable request = none := by
  apply nativeFirstRejectsUnready auth
  intro fresh
  have good := fresh.2.1
  simp [(nextRetained binding h).2.1] at good

theorem nextOriginalBytes {adapter b policyRaw stateRaw apc config proof profile permission inputs
    loaded initial snapshot observation nextRaw application out}
    (h : @checkNext _ _ _ _ binding adapter b policyRaw stateRaw apc config proof profile permission inputs
      loaded initial snapshot observation nextRaw application = some out) :
    NativeVoteBytes.encodeFrame out.image.original.wire = out.original.entry.command ∧
    NativeWalBytes.encode adapter.sha256 out.original.entry = nextRaw ∧
    out.image.original.sequence = out.original.before.prior.core.requests.length +
      out.original.before.prior.votes.length + 1 := by
  have src := checkedNext binding h
  have original := NativeArithmeticPrefix.checked binding src.1
  rw [(nextRetained binding src.2).1]
  exact ⟨(NativeArithmeticPrefix.originalBytes binding original).1,
    (NativeArithmeticPrefix.originalBytes binding original).2,
    (NativeArithmeticPrefix.globalSequence binding original).2.2⟩

end Projection
end DeltaReduce.NativeVoteMetadata
