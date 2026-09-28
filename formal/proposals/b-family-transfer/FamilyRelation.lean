import FamilyGuards
import DeltaReduce.PublicDurablePrefix
import DeltaReduce.NativeVoteCache

/-! R2 arithmetic subrelation at one family view. This composes complete body
construction, the existing primitive metadata boundary and original journal
record. It intentionally does not claim that the entire static R2 relation is
closed: unrelated state fields, all certificate collections and provenance of
the public configuration still need their existing source correspondence.
There is no persistence/replay/Next theorem here. -/
namespace DeltaReduce.FamilyRelation
open NativeBinding NativeInputProjection PublicState PublicArithmeticInputs

/- Constructor completeness over the already source-bound input corpus. This
does not assume a supplied aggregate/APPLY translation. The remaining checkpoint
premise is exactly the existing primitive identity boundary, not a new name. -/
theorem applyConstructorTotal {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : FamilyInputs.Corpus binding} {choice : FamilyInputs.Choice corpus.frame}
    {input : FamilyInputs.Projected corpus choice (accumulatorHi binding.profile)}
    {vocabulary : Vocabulary} {metadataTrust} {source : PublicAuthority.Metadata metadataTrust}
    (authority : FamilyAuthority.Projection input vocabulary source)
    (mapping : IdentityMap) (expected : Value) (native : NativeApply binding)
    (checkpoint : PublicApplyBody.Checkpoint mapping expected native) :
    ∃ projection, FamilyApply.project authority (accumulatorHi binding.profile+1) mapping expected native = some projection := by
  have frame : native.core.conversion.certified.corpus.frame = corpus.frame := by
    exact congrArg Subtype.val (Option.some.inj
      ((NativeVectorDerivation.frameComplete native.core.conversion.certified.corpus.origin).symm.trans
        (NativeVectorDerivation.frameComplete corpus.origin)))
  have modelShape : binding.model.values.length = corpus.frame.coordinates.length := by
    simpa only [StateFamily.nativeLayout,StateFamily.ofValidated,frame] using StateFamily.nativeModelShape native
  have bounds := nativeApplyOutputBounds native
  obtain ⟨modelCells,model,modelSource,modelEncoded⟩ :=
    FamilyAuthority.currentTableTotal authority native.body.nextModel (bounds.1.trans modelShape)
  obtain ⟨optimizerCells,optimizer,optimizerSource,optimizerEncoded⟩ :=
    FamilyAuthority.currentTableTotal authority native.body.nextOptimizer (bounds.2.1.trans modelShape)
  obtain ⟨leaves,leafSource⟩ := FamilyApply.allLeavesConstructible authority native.core.conversion.certified.corpus.entries
  have checkpointSource : PublicApplyBody.checkCheckpoint mapping expected native = some checkpoint := by
    cases checkpoint with
    | mk symbol configured identity =>
      subst expected
      simp only [PublicApplyBody.checkCheckpoint,dif_pos identity]
  unfold FamilyApply.project
  rw [dif_pos frame,leafSource,FamilyGuards.nativePublicArithmeticCheck native]
  simp only [bind,Option.bind]
  split
  · rename_i mc oc hm ho
    have em := Option.some.inj (hm.symm.trans modelSource)
    have eo := Option.some.inj (ho.symm.trans optimizerSource)
    subst mc; subst oc
    split
    · rename_i m o hem heo
      have em := Option.some.inj (hem.symm.trans modelEncoded)
      have eo := Option.some.inj (heo.symm.trans optimizerEncoded)
      subst m; subst o
      rw [checkpointSource]
      exact ⟨_,rfl⟩
    · simp_all
  · simp_all

def selectCoordinates (frame : ParameterFrame) (indices : List Nat) : Option (FamilyInputs.Choice frame) :=
  if shape : indices.length = frame.shards.length then
    if h : ∀ s : Fin frame.shards.length, indices[s.val]'(by rw [shape]; exact s.isLt) < frame.shards[s.val].length then
      some (fun s => ⟨indices[s.val]'(by rw [shape]; exact s.isLt),h s⟩)
    else none
  else none

/- Explicit relation to already configured arithmetic constants. No chosen
result, full translated body or truth-valued admission flag is supplied. -/
structure ArithmeticConfiguration where
  limit : Int
  resultBound : Int
  expectedCheckpoint : Value
  deriving DecidableEq, Repr

def widthMatches (p : Profile) (c : ArithmeticConfiguration) : Prop :=
  c.limit = accumulatorHi p ∧ c.resultBound = accumulatorHi p + 1
instance (p c) : Decidable (widthMatches p c) := by unfold widthMatches; infer_instance

section Body
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust)
    (configuration : ArithmeticConfiguration) (mapping : IdentityMap) (indices : List Nat)

structure Inputs where
  corpus : FamilyInputs.Corpus binding
  choice : FamilyInputs.Choice corpus.frame
  chosen : selectCoordinates corpus.frame indices = some choice
  input : FamilyInputs.Projected corpus choice configuration.limit
  authority : FamilyAuthority.Projection input vocabulary source
  widths : widthMatches binding.profile configuration

def loadInputs : Option (Inputs (binding := binding) vocabulary source configuration indices) := do
  if widths : widthMatches binding.profile configuration then
    let corpus ← FamilyInputs.loadCorpus binding
    match chosen : selectCoordinates corpus.frame indices with
    | none => none
    | some choice =>
      let input ← FamilyInputs.project corpus choice configuration.limit
      let authority ← FamilyAuthority.project input vocabulary source
      some ⟨corpus,choice,chosen,input,authority,widths⟩
  else none

theorem inputsLoaderComplete
    (inputs : Inputs (binding := binding) vocabulary source configuration indices) :
    loadInputs vocabulary source configuration indices = some inputs := by
  cases inputs with
  | mk corpus choice chosen input authority widths =>
    simp only [loadInputs,dif_pos widths,FamilyInputs.corpusLoaderComplete corpus,bind,Option.bind]
    split
    · rename_i absent
      rw [chosen] at absent
      contradiction
    · rename_i selected found
      cases Option.some.inj (found.symm.trans chosen)
      simp only [FamilyInputs.projectFromComputed input,FamilyAuthority.projectFromComputed authority]

theorem loadedInputsHaveNumericGuards
    (inputs : Inputs (binding := binding) vocabulary source configuration indices) :
    FamilyInputs.InputNumericGuards (FamilyInputs.image inputs.input) :=
  FamilyInputs.allInputNumericGuards inputs.input

structure ParameterBody {domain shard} (native : DerivedParameter binding domain shard) (candidate : Value) where
  inputs : Inputs (binding := binding) vocabulary source configuration indices
  checked : FamilyParameter.Checked inputs.authority configuration.resultBound native
  exactBody : candidate = checked.projection.body inputs.authority

def loadParameterBody {domain shard} (native : DerivedParameter binding domain shard) (candidate : Value) :
    Option (ParameterBody vocabulary source configuration indices native candidate) := do
  let inputs ← loadInputs vocabulary source configuration indices
  match accepted : FamilyParameter.check inputs.authority configuration.resultBound native candidate with
  | none => none
  | some checked => some ⟨inputs,checked,FamilyParameter.computedWholeBody inputs.authority configuration.resultBound native accepted⟩

theorem parameterCandidateUsesOwnInputs {domain shard} {native : DerivedParameter binding domain shard}
    {candidate : Value} (body : ParameterBody vocabulary source configuration indices native candidate) :
    FamilyInputs.InputNumericGuards (FamilyInputs.image body.inputs.input) ∧
    (readField candidate "authority" >>= fun a => readField a "inputs") =
      some body.inputs.authority.encoded.value ∧
    readField candidate "value" = some (.integer body.checked.projection.value) ∧
    ∃ d ∈ body.inputs.input.domains, d.domain = native.assignment.domain ∧
      d.denominator = native.assignment.denominator ∧
      ((FamilyInputs.imageRows (FamilyInputs.image body.inputs.input) d.domain
          body.checked.projection.entry.block.slot.val).bind
        (ParameterKernel.checkedParameter (-configuration.limit-1) configuration.limit minInput maxInput d.denominator 1)) =
          some [body.checked.projection.value] := by
  refine ⟨loadedInputsHaveNumericGuards vocabulary source configuration indices body.inputs,?_,?_,?_⟩
  · exact congrArg (fun v => readField v "authority" >>= fun a => readField a "inputs") body.exactBody
  · exact congrArg (fun v => readField v "value") body.exactBody
  · exact FamilyParameter.actualInputImageComputesBody configuration.resultBound native body.checked.projection

structure ApplyBody (native : NativeApply binding) (candidate : Value) where
  inputs : Inputs (binding := binding) vocabulary source configuration indices
  checked : FamilyApply.Checked inputs.authority configuration.resultBound mapping configuration.expectedCheckpoint native
  exactBody : candidate = checked.projection.value

def loadApplyBody (native : NativeApply binding) (candidate : Value) :
    Option (ApplyBody vocabulary source configuration mapping indices native candidate) := do
  let inputs ← loadInputs vocabulary source configuration indices
  match accepted : FamilyApply.check inputs.authority configuration.resultBound mapping configuration.expectedCheckpoint native candidate with
  | none => none
  | some checked => some ⟨inputs,checked,FamilyApply.computedWholeBody inputs.authority configuration.resultBound mapping
      configuration.expectedCheckpoint native accepted⟩

def SourceBody {kind} (native : VoteSource binding kind) (candidate : Value) : Type :=
  match native with
  | .parameter result => ParameterBody vocabulary source configuration indices result candidate
  | .apply result => ApplyBody vocabulary source configuration mapping indices result candidate

def loadSourceBody {kind} (native : VoteSource binding kind) (candidate : Value) :
    Option (SourceBody vocabulary source configuration mapping indices native candidate) :=
  match native with
  | .parameter result => loadParameterBody vocabulary source configuration indices result candidate
  | .apply result => loadApplyBody vocabulary source configuration mapping indices result candidate

end Body

/- Historical identity checks do not impose current first-vote freshness on
retries. Both actual slot and entire public envelope are checked. No opaque
non-arithmetic authorization can pass this arithmetic subrelation. -/
structure Historical {codec trust voteTrust} (env : PublicJournal.Environment codec trust voteTrust)
    (mapping : IdentityMap) (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust)
    (configuration : ArithmeticConfiguration) (indices : List Nat) (slot : PublicJournal.Slot) (vote : Vote) where
  supported : slot.envelope.action.arithmetic = true
  record : RecoveryKernel.Record
  stored : slot.native = some record
  resolved : NativeReplay.Resolved env.native record.data
  envelope : slot.envelope = PublicDurablePrefix.nativeEnvelope resolved.input.anchor resolved.input.metadata (codec.hash resolved.expected.body)
  canonicalEnvelope : slot.envelope.encode = some slot.bytes
  bytes : slot.bytes = resolved.expected.envelope
  key : slot.key = record.data.context
  encodedKey : slot.envelope.key = some slot.key
  sequence : record.sequence = slot.sequence
  effect : record.effect = resolved.expected.effect
  receipt : encodeDiagnosticReceipt codec record.data.command slot.bytes record.effect slot.sequence = some record.receipt
  identity : PublicDurablePrefix.identityMatches mapping vote resolved.input.anchor resolved.input.metadata
  body : SourceBody vocabulary source configuration mapping indices resolved.expected.source vote.body

def checkHistorical {codec trust voteTrust} (env : PublicJournal.Environment codec trust voteTrust)
    (mapping : IdentityMap) (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust)
    (configuration : ArithmeticConfiguration) (indices : List Nat) (slot : PublicJournal.Slot) (vote : Vote) :
    Option (Historical env mapping vocabulary source configuration indices slot vote) := do
  if supported : slot.envelope.action.arithmetic = true then
    match stored : slot.native with
    | none => none
    | some record =>
      let resolved ← NativeReplay.resolve env.native record.data
      if checks : slot.envelope = PublicDurablePrefix.nativeEnvelope resolved.input.anchor resolved.input.metadata (codec.hash resolved.expected.body) ∧
          slot.envelope.encode = some slot.bytes ∧ slot.bytes = resolved.expected.envelope ∧
          slot.key = record.data.context ∧ slot.envelope.key = some slot.key ∧
          record.sequence = slot.sequence ∧ record.effect = resolved.expected.effect ∧
          encodeDiagnosticReceipt codec record.data.command slot.bytes record.effect slot.sequence = some record.receipt ∧
          PublicDurablePrefix.identityMatches mapping vote resolved.input.anchor resolved.input.metadata then
        let body ← loadSourceBody vocabulary source configuration mapping indices resolved.expected.source vote.body
        some ⟨supported,record,stored,resolved,checks.1,checks.2.1,checks.2.2.1,checks.2.2.2.1,
          checks.2.2.2.2.1,checks.2.2.2.2.2.1,checks.2.2.2.2.2.2.1,checks.2.2.2.2.2.2.2.1,
          checks.2.2.2.2.2.2.2.2,body⟩
      else none
  else none

theorem historicalOriginalIdentity {codec trust voteTrust env mapping vocabulary metadataTrust source configuration indices slot vote}
    (h : Historical (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping vocabulary
      (metadataTrust := metadataTrust) source configuration indices slot vote) :
    slot.native = some h.record ∧ h.record.sequence = slot.sequence ∧
    slot.bytes = h.resolved.expected.envelope ∧ h.record.effect = h.resolved.expected.effect ∧
    mapping.actor vote.actor = some h.resolved.input.metadata.actor ∧
    expectedContext vote = some vote.context :=
  ⟨h.stored,h.sequence,h.bytes,h.effect,h.identity.1,h.identity.2.2.1⟩

theorem nonArithmeticRejected {codec trust voteTrust env mapping vocabulary metadataTrust source configuration indices slot vote}
    (notArithmetic : slot.envelope.action.arithmetic = false) :
    checkHistorical (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping vocabulary
      (metadataTrust := metadataTrust) source configuration indices slot vote = none := by
  simp [checkHistorical,notArithmetic]

/- Direct original-source entry point: the native candidate checker computes the
vote image. The historical reader above also remains useful for existing draft
records, but cannot by itself establish this original source correspondence. -/
/- One alias namespace belongs to the original decoded policy. Coordinate
indices do not occur in it. These checks preserve cardinality and cannot turn
one native signer into several exposed validators. Authentication of the exposed
configuration itself is still the named R2 source boundary. -/
def actorBytes (mapping : IdentityMap) (actor : Value) : Option Bytes :=
  (mapping.actor actor).map asciiBytes

structure ActorNamespace (mapping : IdentityMap) (actors : List Value) (committee : List Bytes) where
  mapped : List Bytes
  source : collect (actorBytes mapping) actors = some mapped
  exactMembers : mapped.Perm committee
  publicUnique : actors.Nodup
  nativeUnique : committee.Nodup

def checkActors (mapping : IdentityMap) (actors : List Value) (committee : List Bytes) :
    Option (ActorNamespace mapping actors committee) := do
  match source : collect (actorBytes mapping) actors with
  | none => none
  | some mapped =>
    if valid : mapped.Perm committee ∧ actors.Nodup ∧ committee.Nodup then
      some ⟨mapped,source,valid.1,valid.2.1,valid.2.2⟩ else none

theorem actorsExactCount {mapping actors committee} (a : ActorNamespace mapping actors committee) :
    actors.length = committee.length := (collectLength a.source).symm.trans a.exactMembers.length_eq

theorem actorHasOriginal {mapping actors committee} (a : ActorNamespace mapping actors committee)
    {v : Value} (member : v ∈ actors) : ∃ native ∈ committee, actorBytes mapping v = some native := by
  obtain ⟨i,atActor⟩ := List.mem_iff_getElem?.mp member
  have inside : i < a.mapped.length := by rw [collectLength a.source]; exact (List.getElem?_eq_some_iff.mp atActor).1
  obtain ⟨v',atV,selected⟩ := collectAt a.source i a.mapped[i] (List.getElem?_eq_getElem inside)
  have same := Option.some.inj (atV.symm.trans atActor)
  subst v'
  exact ⟨_,a.exactMembers.mem_iff.mp (List.getElem_mem inside),selected⟩

theorem originalHasActor {mapping actors committee} (a : ActorNamespace mapping actors committee)
    {native : Bytes} (member : native ∈ committee) : ∃ v ∈ actors, actorBytes mapping v = some native := by
  obtain ⟨i,atNative⟩ := List.mem_iff_getElem?.mp (a.exactMembers.mem_iff.mpr member)
  obtain ⟨v,atActor,selected⟩ := collectAt a.source i native atNative
  exact ⟨v,List.mem_of_getElem? atActor,selected⟩

theorem collectedSameAt {α β} {f : α → Option β} {xs ys} (loaded : collect f xs = some ys)
    {i : Nat} {x y} (atX : xs[i]? = some x) (selected : f x = some y) : ys[i]? = some y := by
  have inside : i < ys.length := by rw [collectLength loaded]; exact (List.getElem?_eq_some_iff.mp atX).1
  obtain ⟨x',atX',selected'⟩ := collectAt loaded i ys[i] (List.getElem?_eq_getElem inside)
  have sameX := Option.some.inj (atX'.symm.trans atX)
  subst x'
  have sameY := Option.some.inj (selected'.symm.trans selected)
  simpa only [sameY] using List.getElem?_eq_getElem inside

theorem actorAliasesInjective {mapping actors committee} (a : ActorNamespace mapping actors committee)
    {v w native} (first : v ∈ actors) (second : w ∈ actors)
    (av : actorBytes mapping v = some native) (aw : actorBytes mapping w = some native) : v = w := by
  obtain ⟨i,vi⟩ := List.mem_iff_getElem?.mp first
  obtain ⟨j,wj⟩ := List.mem_iff_getElem?.mp second
  have ni := collectedSameAt a.source vi av
  have nj := collectedSameAt a.source wj aw
  have unique : a.mapped.Nodup := a.exactMembers.nodup_iff.mpr a.nativeUnique
  have indices : i = j := (List.getElem?_inj (List.getElem?_eq_some_iff.mp ni).1 unique).mp (ni.trans nj.symm)
  subst j
  exact Option.some.inj (vi.symm.trans wj)

theorem repeatedActorAliasRejected {mapping actors committee a b native}
    (first : a ∈ actors) (second : b ∈ actors) (distinct : a ≠ b)
    (left : actorBytes mapping a = some native) (right : actorBytes mapping b = some native) :
    checkActors mapping actors committee = none := by
  cases checked : checkActors mapping actors committee with
  | none => rfl
  | some names => exact False.elim (distinct (actorAliasesInjective names first second left right))

structure PolicyActors (mapping : IdentityMap) (actors : List Value) (policyRaw : Bytes) where
  tree : NativePolicyCodec.Value
  policy : NativePolicyBytes.Policy
  decoded : NativePolicyBytes.decodePolicy policyRaw = some (tree,policy)
  names : ActorNamespace mapping actors policy.validators

def checkPolicyActors (mapping : IdentityMap) (actors : List Value) (policyRaw : Bytes) :
    Option (PolicyActors mapping actors policyRaw) := do
  match decoded : NativePolicyBytes.decodePolicy policyRaw with
  | none => none
  | some (tree,policy) =>
    let names ← checkActors mapping actors policy.validators
    some ⟨tree,policy,decoded,names⟩

structure SignerImage {mapping actors policyRaw} (a : PolicyActors mapping actors policyRaw)
    (original : List Bytes) (exposed : List Value) where
  names : ActorNamespace mapping exposed original
  members : ∀ v ∈ exposed, v ∈ actors

def checkSigners {mapping actors policyRaw} (a : PolicyActors mapping actors policyRaw)
    (original : List Bytes) (exposed : List Value) : Option (SignerImage a original exposed) := do
  let names ← checkActors mapping exposed original
  if members : ∀ v ∈ exposed, v ∈ actors then some ⟨names,members⟩ else none

theorem signerThresholdPreserved {mapping actors policyRaw} {a : PolicyActors mapping actors policyRaw}
    {original exposed threshold} (s : SignerImage a original exposed) :
    threshold ≤ exposed.length ↔ threshold ≤ original.length := by rw [actorsExactCount s.names]

theorem signerMembershipPreserved {mapping actors policyRaw} {a : PolicyActors mapping actors policyRaw}
    {original exposed} (s : SignerImage a original exposed) :
    ∀ native ∈ original, native ∈ a.policy.validators := by
  intro native member
  obtain ⟨v,hv,selected⟩ := originalHasActor s.names member
  obtain ⟨id,hid,selected'⟩ := actorHasOriginal a.names (s.members v hv)
  have same := Option.some.inj (selected.symm.trans selected')
  simpa only [same] using hid

theorem actualIscQuorumPreserved {mapping actors policyRaw} (a : PolicyActors mapping actors policyRaw)
    {sha context source certificate exposed}
    (checked : NativeIscCertificate.check sha context a.policy.validators source = some certificate)
    (s : SignerImage a certificate.certificate.signers exposed) :
    certificate.certificate.threshold = 2*((actors.length-1)/3)+1 ∧
    certificate.certificate.threshold ≤ exposed.length := by
  have length := actorsExactCount a.names
  constructor
  · rw [(NativeIscCertificate.checkedQuorum checked).1,NativeIscCertificate.quorum,length]
  · rw [actorsExactCount s.names]
    exact (NativeIscCertificate.checkedQuorum checked).2.1


section Original
variable {codec store trust} (adapter : HashAdapter codec)
    (mapping : IdentityMap) (vocabulary : Vocabulary) {metadataTrust}
    (metadata : PublicAuthority.Metadata metadataTrust) (configuration : ArithmeticConfiguration)
    (indices : List Nat) (policy : Bytes) (snapshot : Option NativeCommandReplay.Snapshot)
    (prior : NativeConfigReplay.Machine) (entry : NativeWalBytes.Entry)
    (source : NativeArithmeticJournal.Source codec store trust adapter.sha256) (vote : Vote)

structure CapturedArithmetic where
  original : NativeArithmeticJournal.Arithmetic adapter source
  computed : NativeArithmeticJournal.arithmetic adapter policy snapshot prior entry source = some original
  identity : PublicDurablePrefix.identityMatches mapping vote source.anchor original.image.metadata
  canonical : PublicState.canonical vocabulary.models (.function (voteEntries vote)) = true
  body : SourceBody vocabulary metadata configuration mapping indices original.image.expected.source vote.body

def checkOriginal : Option (CapturedArithmetic adapter mapping vocabulary metadata configuration indices
    policy snapshot prior entry source vote) := do
  match computed : NativeArithmeticJournal.arithmetic adapter policy snapshot prior entry source with
  | none => none
  | some original =>
    if checks : PublicDurablePrefix.identityMatches mapping vote source.anchor original.image.metadata ∧
        PublicState.canonical vocabulary.models (.function (voteEntries vote)) = true then
      let body ← loadSourceBody vocabulary metadata configuration mapping indices original.image.expected.source vote.body
      some ⟨original,computed,checks.1,checks.2,body⟩
    else none

variable {mapping vocabulary metadata configuration indices policy snapshot prior entry source vote}
    (h : CapturedArithmetic adapter mapping vocabulary (metadataTrust := metadataTrust) metadata configuration indices
      policy snapshot prior entry source vote)

theorem capturedOriginalBytes : NativeVoteBytes.encodeFrame h.original.vote.wire = entry.command ∧
    h.original.vote.sequence = entry.sequence ∧ h.original.image.original = h.original.vote := by
  have original := NativeArithmeticJournal.originalVote adapter (NativeArithmeticJournal.checked adapter h.computed)
  exact ⟨original.1,original.2.1,original.2.2.1⟩

theorem capturedOriginalPosition : entry.sequence = prior.core.sequence+1 ∧
    (NativeArithmeticJournal.stored adapter entry h.original).receipt.sequence = entry.sequence :=
  ⟨(NativeArithmeticJournal.checked adapter h.computed).position,rfl⟩

include h in
theorem capturedOriginalGraph : NativeVectorContext.bind adapter.sha256 policy prior.core.state
    source.apc source.config source.proof source.profile source.permission source.inputs = some source.bound :=
  NativeArithmeticJournal.actualPreparation adapter (NativeArithmeticJournal.checked adapter h.computed)

theorem capturedNoNewProtocolIdentity :
    NativeVoteBytes.voteId adapter.sha256 entry.command = some h.original.id ∧
    (NativeArithmeticJournal.stored adapter entry h.original).vote = h.original.vote ∧
    (NativeArithmeticJournal.stored adapter entry h.original).parents =
      (NativeArithmeticPrefix.admitted source.binding h.original.computation).selected.original.parents :=
  ⟨(NativeArithmeticJournal.checked adapter h.computed).id,rfl,rfl⟩

theorem originalGuardUnchanged :
    NativeSelectedVote.checkVote (NativeVectorAuthority.policy source.bound) (NativeVectorAuthority.state source.bound)
      (NativeArithmeticPrefix.admitted source.binding h.original.computation).checked.snapshot.prior.tail
      (NativeArithmeticPrefix.admitted source.binding h.original.computation).selected
      (NativeConfigReplay.facts prior entry) h.original.vote = none :=
  NativeArithmeticJournal.originalGuard adapter (NativeArithmeticJournal.checked adapter h.computed)

end Original

section Configured
variable {codec store trust} (adapter : HashAdapter codec)
    (mapping : IdentityMap) (vocabulary : Vocabulary) {metadataTrust}
    (metadata : PublicAuthority.Metadata metadataTrust) (configuration : ArithmeticConfiguration)
    (indices : List Nat) (actors : List Value) (policy : Bytes)
    (snapshot : Option NativeCommandReplay.Snapshot) (prior : NativeConfigReplay.Machine)
    (entry : NativeWalBytes.Entry) (source : NativeArithmeticJournal.Source codec store trust adapter.sha256)
    (vote : Vote)

structure ConfiguredArithmetic where
  captured : CapturedArithmetic adapter mapping vocabulary metadata configuration indices policy snapshot prior entry source vote
  actorNames : PolicyActors mapping actors policy
  actorConfigured : vote.actor ∈ actors

def checkConfiguredArithmetic : Option (ConfiguredArithmetic adapter mapping vocabulary metadata configuration indices
    actors policy snapshot prior entry source vote) := do
  let captured ← checkOriginal adapter mapping vocabulary metadata configuration indices policy snapshot prior entry source vote
  let actorNames ← checkPolicyActors mapping actors policy
  if member : vote.actor ∈ actors then some ⟨captured,actorNames,member⟩ else none

variable {mapping vocabulary metadata configuration indices actors policy snapshot prior entry source vote}
    (c : ConfiguredArithmetic adapter mapping vocabulary (metadataTrust := metadataTrust) metadata configuration indices
      actors policy snapshot prior entry source vote)

theorem configuredSameOriginalPolicy : c.actorNames.policy = NativeVectorAuthority.policy source.bound := by
  obtain ⟨tree,decoded,_⟩ := NativeVectorAuthority.rawSource source.loaded
  rw [(NativeArithmeticJournal.checked adapter c.captured.computed).samePolicy] at decoded
  exact congrArg Prod.snd (Option.some.inj (c.actorNames.decoded.symm.trans decoded))

theorem configuredActorIsOriginal : actorBytes mapping vote.actor = some c.captured.original.vote.wire.validator := by
  have computed := (NativeArithmeticJournal.checked adapter c.captured.computed).image
  have original : asciiBytes c.captured.original.image.metadata.actor = c.captured.original.vote.wire.validator := by
    unfold NativeArithmeticJournal.projected at computed
    split at computed
    all_goals exact (NativeVoteMetadata.originalMetadata source.binding computed).1
  simp only [actorBytes,c.captured.identity.1,Option.map_some,original]

theorem configuredNoActorDuplication {other : Value} (member : other ∈ actors)
    (same : actorBytes mapping other = some c.captured.original.vote.wire.validator) : other = vote.actor :=
  actorAliasesInjective c.actorNames.names member c.actorConfigured same (configuredActorIsOriginal adapter c)

include c in
theorem configuredOriginalCommitteeCount : actors.length = (NativeVectorAuthority.policy source.bound).validators.length := by
  rw [← configuredSameOriginalPolicy adapter c]
  exact actorsExactCount c.actorNames.names

end Configured
end DeltaReduce.FamilyRelation
