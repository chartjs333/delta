import FamilyGuards
import FamilyApply
import DeltaReduce.PublicDurablePrefix
import DeltaReduce.NativeVoteCache
import DeltaReduce.NativeRootSource
import DeltaReduce.PublicRootEnvelope
import DeltaReduce.PublicFailureBody

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
  tickets : List Ticket
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
  configured : authority.completion.configured = configuration.tickets
  widths : widthMatches binding.profile configuration

def loadInputs : Option (Inputs (binding := binding) vocabulary source configuration indices) := do
  if widths : widthMatches binding.profile configuration then
    let corpus ← FamilyInputs.loadCorpus binding
    match chosen : selectCoordinates corpus.frame indices with
    | none => none
    | some choice =>
      let input ← FamilyInputs.project corpus choice configuration.limit
      match original : FamilyAuthority.project input vocabulary source configuration.tickets with
      | none => none
      | some authority =>
        some ⟨corpus,choice,chosen,input,authority,FamilyAuthority.projectedConfiguration original,widths⟩
  else none

theorem inputsLoaderComplete
    (inputs : Inputs (binding := binding) vocabulary source configuration indices) :
    loadInputs vocabulary source configuration indices = some inputs := by
  cases inputs with
  | mk corpus choice chosen input authority configured widths =>
    simp only [loadInputs,dif_pos widths,FamilyInputs.corpusLoaderComplete corpus,bind,Option.bind]
    split
    · rename_i absent
      rw [chosen] at absent
      contradiction
    · rename_i selected found
      cases Option.some.inj (found.symm.trans chosen)
      simp only [FamilyInputs.projectFromComputed input]
      have complete := FamilyAuthority.projectFromComputed authority
      rw [configured] at complete
      split
      · rename_i absent
        rw [complete] at absent
        contradiction
      · rename_i result loaded
        cases Option.some.inj (loaded.symm.trans complete)
        rfl

theorem loadedCompleteInputsHaveNumericGuards
    (inputs : Inputs (binding := binding) vocabulary source configuration indices) :
    FamilyInputs.InputNumericGuards
      (FamilyInputs.completedImage (FamilyInputs.image inputs.input) configuration.tickets) := by
  rw [← inputs.configured]
  exact FamilyInputs.completedImageNumericGuards _ _ (FamilyInputs.allInputNumericGuards inputs.input)
    inputs.authority.completion.coverage.2.2.2.1

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

theorem parameterBodyConstructorTotal
    (inputs : Inputs (binding := binding) vocabulary source configuration indices)
    (authorityCanonical : canonical vocabulary.models inputs.authority.value = true)
    (names : ∀ n ∈ vocabulary.domains ++ vocabulary.shards, canonical vocabulary.models (.model n) = true)
    {domain shard} (native : DerivedParameter binding domain shard) :
    ∃ candidate body, loadParameterBody vocabulary source configuration indices native candidate = some body := by
  cases configuration with
  | mk limit resultBound expectedCheckpoint tickets =>
    have widths := inputs.widths
    change limit = accumulatorHi binding.profile ∧ resultBound = accumulatorHi binding.profile + 1 at widths
    rcases widths with ⟨rfl,rfl⟩
    obtain ⟨candidate,checked,accepted⟩ :=
      FamilyParameter.checkedParameterFromAuthority ⟨inputs.authority,authorityCanonical⟩ names native
    refine ⟨candidate,?_⟩
    unfold loadParameterBody
    rw [inputsLoaderComplete vocabulary source _ indices inputs]
    simp only [bind,Option.bind]
    split
    · rename_i absent
      rw [accepted] at absent
      contradiction
    · exact ⟨_,rfl⟩

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

/- The full configured image embedded in the body is the image used for the
APC member selection. Excluded ticket completion has no arithmetic effect. -/
theorem parameterCandidateUsesCompleteInputs {domain shard} {native : DerivedParameter binding domain shard}
    {candidate : Value} (body : ParameterBody vocabulary source configuration indices native candidate) :
    FamilyInputs.InputNumericGuards
      (FamilyInputs.completedImage (FamilyInputs.image body.inputs.input) configuration.tickets) ∧
    (readField candidate "authority" >>= fun a => readField a "inputs") =
      some body.inputs.authority.encoded.value ∧
    ∃ d ∈ body.inputs.input.domains, d.domain = native.assignment.domain ∧
      d.denominator = native.assignment.denominator ∧
      ((FamilyInputs.memberImageRows
          (FamilyInputs.completedImage (FamilyInputs.image body.inputs.input) configuration.tickets)
          (FamilyInputs.activeNames body.inputs.input.tickets) d.domain
          body.checked.projection.entry.block.slot.val).bind
        (ParameterKernel.checkedParameter (-configuration.limit-1) configuration.limit minInput maxInput d.denominator 1)) =
          some [body.checked.projection.value] := by
  refine ⟨loadedCompleteInputsHaveNumericGuards vocabulary source configuration indices body.inputs,
    (parameterCandidateUsesOwnInputs vocabulary source configuration indices body).2.1,?_⟩
  obtain ⟨d,member,domain,denominator,computed⟩ :=
    FamilyParameter.actualInputImageComputesBody configuration.resultBound native body.checked.projection
  refine ⟨d,member,domain,denominator,?_⟩
  have same := FamilyInputs.excludedCellsNeverEnterParameter body.inputs.authority.completion
    d.domain body.checked.projection.entry.block.slot.val
  change FamilyInputs.memberImageRows
    (FamilyInputs.completedImage (FamilyInputs.image body.inputs.input) body.inputs.authority.completion.configured)
    (FamilyInputs.activeNames body.inputs.input.tickets) d.domain body.checked.projection.entry.block.slot.val = _ at same
  rw [← body.inputs.configured,same]
  exact computed

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

theorem applyBodyFromConstructed
    (inputs : Inputs (binding := binding) vocabulary source configuration indices)
    (native : NativeApply binding)
    (projection : FamilyApply.Projection inputs.authority configuration.resultBound mapping
      configuration.expectedCheckpoint native)
    (constructed : FamilyApply.project inputs.authority configuration.resultBound mapping
      configuration.expectedCheckpoint native = some projection)
    (authorityCanonical : canonical vocabulary.models inputs.authority.value = true)
    (names : ∀ n ∈ vocabulary.domains ++ vocabulary.shards, canonical vocabulary.models (.model n) = true)
    (uniqueBytes : (projection.leaves.map PublicState.encode).Nodup)
    (checkpointCanonical : canonical vocabulary.models configuration.expectedCheckpoint = true) :
    ∃ body, loadApplyBody vocabulary source configuration mapping indices native projection.value = some body := by
  obtain ⟨checked,accepted,_⟩ := FamilyApply.checkedFromConstructed inputs.authority configuration.resultBound
    mapping configuration.expectedCheckpoint native projection constructed authorityCanonical names uniqueBytes checkpointCanonical
  unfold loadApplyBody
  rw [inputsLoaderComplete vocabulary source configuration indices inputs]
  simp only [bind,Option.bind]
  split
  · rename_i absent
    rw [accepted] at absent
    contradiction
  · exact ⟨_,rfl⟩

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

/- Direct original-source composition for obligation 3. These are static
observations: no journal mutation, recovery induction or response exposure is
inferred from decoding a WAL/receipt pair. The production arithmetic guard is
still rejected. All constructor inputs below share this single source. -/
namespace Direct

structure Artifacts where
  policy : Bytes
  state : Bytes
  apc : Bytes
  accumulator : Bytes
  proof : Bytes
  arithmetic : Bytes
  permission : NativeAvailableQ.Permission
  inputs : List NativeAvailableQ.Input
  applyProfile : Bytes

structure Source (sha : Bytes → Bytes) (mapping : IdentityMap) (actors : List Value)
    (artifacts : Artifacts) (units : NativeStateProjection.UnitSource)
    (current : FamilyInputs.CurrentBasis) where
  bound : NativeVectorContext.Bound
  prepared : FamilyInputs.prepareOriginalVector sha artifacts.policy artifacts.state artifacts.apc
    artifacts.accumulator artifacts.proof artifacts.arithmetic artifacts.permission artifacts.inputs = some bound
  numeric : FamilyInputs.OriginalNumericConfiguration sha bound units artifacts.applyProfile current
  committee : PolicyActors mapping actors artifacts.policy

def loadSource (sha : Bytes → Bytes) (mapping : IdentityMap) (actors : List Value)
    (artifacts : Artifacts) (units : NativeStateProjection.UnitSource)
    (current : FamilyInputs.CurrentBasis) : Option (Source sha mapping actors artifacts units current) := do
  match prepared : FamilyInputs.prepareOriginalVector sha artifacts.policy artifacts.state artifacts.apc
      artifacts.accumulator artifacts.proof artifacts.arithmetic artifacts.permission artifacts.inputs with
  | none => none
  | some bound =>
    let numeric ← FamilyInputs.loadOriginalNumericConfiguration sha bound units artifacts.applyProfile current
    let committee ← checkPolicyActors mapping actors artifacts.policy
    some ⟨bound,prepared,numeric,committee⟩

theorem originalRawSource {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs bound}
    (source : FamilyInputs.OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs bound) :
    ∃ tree, NativePolicyBytes.decodePolicy policyRaw = some (tree,NativeVectorAuthority.policy bound) ∧
      NativeStateBytes.decodeState stateRaw = some (NativeVectorAuthority.state bound) := by
  obtain ⟨tree,p,s,hp,hs,ps⟩ := NativePlanSection.preparedSource source.corpus.plan.members.plans
  have es := NativeEligibilitySection.checkedSource ps.eligibility
  have ns := NativeNormSection.checkedSource es.norms
  have src := NativeFinalizedIscSection.checkedSource ns.1
  exact ⟨tree,by simpa only [NativeVectorAuthority.policy,NativeVectorAuthority.base,src.1] using hp,
    by simpa only [NativeVectorAuthority.state,NativeVectorAuthority.base,src.2.1] using hs⟩

section Source
variable {sha mapping actors artifacts units current}
    (source : Source sha mapping actors artifacts units current)

theorem sourceRaw :
    ∃ tree, NativePolicyBytes.decodePolicy artifacts.policy = some (tree,NativeVectorAuthority.policy source.bound) ∧
      NativeStateBytes.decodeState artifacts.state = some (NativeVectorAuthority.state source.bound) :=
  originalRawSource (FamilyInputs.originalVectorPrepared source.prepared)

theorem sourceCommittee : source.committee.policy = NativeVectorAuthority.policy source.bound := by
  obtain ⟨_,decoded,_⟩ := sourceRaw source
  exact congrArg Prod.snd (Option.some.inj (source.committee.decoded.symm.trans decoded))

theorem sourceCommitteeCardinality : actors.length = (NativeVectorAuthority.policy source.bound).validators.length := by
  rw [← sourceCommittee source]
  exact actorsExactCount source.committee.names

structure NativeObservation (wal receipt : Bytes) (facts : NativeConfigAdmission.RuntimeFacts) where
  entry : NativeWalBytes.Entry
  record : NativeReceiptBytes.Receipt
  vote : NativeVoteBytes.Vote
  original : NativeWalBytes.bindReceipt sha artifacts.policy wal receipt = some (entry,record,vote)
  admitted : NativeSelectedVote.Admitted
  selected : NativeArithmeticVote.select sha source.bound facts vote = some admitted

def loadNativeObservation (wal receipt : Bytes) (facts : NativeConfigAdmission.RuntimeFacts) :
    Option (NativeObservation source wal receipt facts) := do
  match original : NativeWalBytes.bindReceipt sha artifacts.policy wal receipt with
  | none => none
  | some (entry,record,vote) =>
    match selected : NativeArithmeticVote.select sha source.bound facts vote with
    | none => none
    | some admitted => some ⟨entry,record,vote,original,admitted,selected⟩

variable {source} {wal receipt facts}
    (native : NativeObservation source wal receipt facts)

def NativeObservation.carrier : NativeSelectedVote.Checked :=
  ⟨NativeVectorAuthority.policy source.bound,NativeVectorAuthority.state source.bound,native.admitted,native.vote⟩

theorem originalBytes :
    NativeWalBytes.encode sha native.entry = wal ∧ NativeReceiptBytes.encode native.record = receipt ∧
    NativeVoteBytes.encodeFrame native.vote.wire = native.entry.command ∧
    native.entry.sequence = native.vote.sequence :=
  NativeWalBytes.boundOriginalBytes sha artifacts.policy wal receipt native.entry native.record native.vote native.original

theorem originalSequence : native.entry.sequence = facts.expectedSequence :=
  (originalBytes native).2.2.2.trans (NativeArithmeticVote.selectedSequence native.selected)

theorem originalPolicyCandidate :
    (NativeVectorAuthority.policy source.bound).candidates.find?
      (NativeSelectedVote.matching (NativeVectorAuthority.state source.bound) native.vote) = some native.admitted.selected.original ∧
    NativeCandidateAuthority.check sha (NativeVectorAuthority.policy source.bound) (NativeVectorAuthority.state source.bound)
      native.admitted.checked.snapshot native.admitted.selected.original = some native.admitted.selected :=
  NativeArithmeticVote.originalCandidate native.selected

theorem completeOriginalSnapshot :
    NativeSnapshotBase.bindSnapshot sha (NativeVectorAuthority.policy source.bound) (NativeVectorAuthority.state source.bound) =
      some native.admitted.checked.snapshot :=
  (NativeCandidateAuthority.policySource (NativeArithmeticVote.selected native.selected).1).1

theorem completeOriginalCandidateList :
    native.admitted.checked.entries.map NativeCandidateAuthority.Entry.original =
      (NativeVectorAuthority.policy source.bound).candidates :=
  NativeCandidateAuthority.completeCandidateList (NativeArithmeticVote.selected native.selected).1

theorem productionGuardStillClosed :
    NativeSelectedVote.checkVote (NativeVectorAuthority.policy source.bound) (NativeVectorAuthority.state source.bound)
      native.admitted.checked.snapshot.prior.tail native.admitted.selected facts native.vote = none :=
  NativeArithmeticVote.originalGuardStillRejects native.selected

end Source

/- A durable record can exist before any receipt is exposed. Reconstruct the
deterministic receipt from its original WAL command and selected candidate;
this does not assert that a response was returned, sent or delivered. -/
section WalObservation
variable {sha mapping actors artifacts units current}
    (source : Source sha mapping actors artifacts units current)

def receiptForWal (entry : NativeWalBytes.Entry) (vote : NativeVoteBytes.Vote)
    (admitted : NativeSelectedVote.Admitted) (id : Bytes) : NativeReceiptBytes.Receipt :=
  ⟨admitted.selected.original.action,entry.sequence,entry.command,id,vote.wire.context⟩

structure WalObservation (wal : Bytes) (facts : NativeConfigAdmission.RuntimeFacts) where
  entry : NativeWalBytes.Entry
  decoded : NativeWalBytes.decode sha wal = some entry
  vote : NativeVoteBytes.Vote
  frame : NativeVoteBytes.decodeFrame entry.command = some vote
  admitted : NativeSelectedVote.Admitted
  selected : NativeArithmeticVote.select sha source.bound facts vote = some admitted
  id : Bytes
  hashed : NativeVoteBytes.voteId sha entry.command = some id
  valid : NativeReceiptBytes.Valid (receiptForWal entry vote admitted id)
  link : NativeWalBytes.ReceiptLink sha artifacts.policy entry (receiptForWal entry vote admitted id)
  voteLink : NativeVoteBytes.ReceiptLinked sha (receiptForWal entry vote admitted id) vote

def loadWalObservation (wal : Bytes) (facts : NativeConfigAdmission.RuntimeFacts) :
    Option (WalObservation source wal facts) := do
  match decoded : NativeWalBytes.decode sha wal with
  | none => none
  | some entry =>
    match frame : NativeVoteBytes.decodeFrame entry.command with
    | none => none
    | some vote =>
      match selected : NativeArithmeticVote.select sha source.bound facts vote with
      | none => none
      | some admitted =>
        match hashed : NativeVoteBytes.voteId sha entry.command with
        | none => none
        | some id =>
          if h : NativeReceiptBytes.Valid (receiptForWal entry vote admitted id) ∧
              NativeWalBytes.ReceiptLink sha artifacts.policy entry (receiptForWal entry vote admitted id) ∧
              NativeVoteBytes.ReceiptLinked sha (receiptForWal entry vote admitted id) vote then
            some ⟨entry,decoded,vote,frame,admitted,selected,id,hashed,h.1,h.2.1,h.2.2⟩
          else none

variable {source wal facts} (observation : WalObservation source wal facts)

def WalObservation.receipt : NativeReceiptBytes.Receipt :=
  receiptForWal observation.entry observation.vote observation.admitted observation.id

def WalObservation.native : NativeObservation source wal (NativeReceiptBytes.encode observation.receipt) facts :=
  ⟨observation.entry,observation.receipt,observation.vote,
    NativeWalBytes.bindFromComponents sha artifacts.policy wal (NativeReceiptBytes.encode observation.receipt)
      observation.entry observation.receipt observation.vote observation.decoded
      (NativeVoteBytes.receiptFromComponents sha observation.receipt observation.vote observation.valid
        (NativeVoteBytes.bindingFromComponents sha observation.receipt observation.vote observation.frame observation.voteLink))
      observation.link,
    observation.admitted,observation.selected⟩

theorem walObservationLoaded : loadWalObservation source wal facts = some observation := by
  cases observation with
  | mk entry decoded vote frame admitted selected id hashed valid link voteLink =>
    unfold loadWalObservation
    split
    · rename_i absent; rw [decoded] at absent; contradiction
    · rename_i e he
      cases Option.some.inj (he.symm.trans decoded)
      split
      · rename_i absent; rw [frame] at absent; contradiction
      · rename_i v hv
        cases Option.some.inj (hv.symm.trans frame)
        split
        · rename_i absent; rw [selected] at absent; contradiction
        · rename_i a ha
          cases Option.some.inj (ha.symm.trans selected)
          split
          · rename_i absent; rw [hashed] at absent; contradiction
          · rename_i i hi
            cases Option.some.inj (hi.symm.trans hashed)
            rw [dif_pos ⟨valid,link,voteLink⟩]

theorem receiptComesFromWal :
    observation.receipt.action = observation.admitted.selected.original.action ∧
    observation.receipt.sequence = observation.entry.sequence ∧
    observation.receipt.frame = observation.entry.command ∧
    observation.receipt.context = observation.vote.wire.context ∧
    NativeVoteBytes.voteId sha observation.entry.command = some observation.receipt.voteId :=
  ⟨rfl,rfl,rfl,rfl,observation.hashed⟩

theorem walOnlyOriginalBytes :
    NativeWalBytes.encode sha observation.entry = wal ∧
    NativeVoteBytes.encodeFrame observation.vote.wire = observation.entry.command ∧
    observation.entry.sequence = facts.expectedSequence :=
  ⟨NativeWalBytes.decodedCanonical sha wal observation.entry observation.decoded,
    (NativeVoteBytes.decodedVoteSound observation.frame).2,originalSequence observation.native⟩

/- Decoding an additionally observed receipt can only confirm the derived
receipt. The receipt may not relabel its action while retaining the same vote. -/
theorem actionNameInjective {a b : Nat} (aLower : 1 ≤ a) (aUpper : a ≤ 9)
    (bLower : 1 ≤ b) (bUpper : b ≤ 9)
    (same : NativeVoteBytes.actionName a = NativeVoteBytes.actionName b) : a = b := by
  have as : a = 1 ∨ a = 2 ∨ a = 3 ∨ a = 4 ∨ a = 5 ∨ a = 6 ∨ a = 7 ∨ a = 8 ∨ a = 9 := by omega
  have bs : b = 1 ∨ b = 2 ∨ b = 3 ∨ b = 4 ∨ b = 5 ∨ b = 6 ∨ b = 7 ∨ b = 8 ∨ b = 9 := by omega
  rcases as with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl <;>
    rcases bs with rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl | rfl <;>
    simp_all [NativeVoteBytes.actionName,NativeVoteBytes.ascii]

theorem observedReceiptMatches {rawReceipt entry record vote}
    (observed : NativeWalBytes.bindReceipt sha artifacts.policy wal rawReceipt = some (entry,record,vote)) :
    entry = observation.entry ∧ vote = observation.vote ∧
    record = observation.receipt ∧ rawReceipt = NativeReceiptBytes.encode observation.receipt := by
  have bound := NativeWalBytes.bindingSound sha artifacts.policy wal rawReceipt entry record vote observed
  have entrySame := Option.some.inj (bound.1.symm.trans observation.decoded)
  subst entry
  have receipt := NativeVoteBytes.semanticReceiptSound bound.2.1
  have frameSame : record.frame = observation.entry.command := bound.2.2.2.2.1.symm
  have decoded : NativeVoteBytes.decodeFrame observation.entry.command = some vote := by rw [← frameSame]; exact receipt.2.1
  have voteSame := Option.some.inj (decoded.symm.trans observation.frame)
  subst vote
  have valid := receipt.2.2.1
  have linked := receipt.2.2.2.2.2.2
  have actionSame : record.action = observation.receipt.action :=
    actionNameInjective valid.1 valid.2.1 observation.valid.1 observation.valid.2.1
      (linked.2.2.1.trans observation.voteLink.2.2.1.symm)
  have sequenceSame : record.sequence = observation.receipt.sequence := bound.2.2.2.1.symm
  have idSame : record.voteId = observation.receipt.voteId := by
    have hash := linked.2.2.2
    rw [frameSame] at hash
    exact Option.some.inj (hash.symm.trans observation.hashed)
  have contextSame : record.context = observation.receipt.context := linked.2.1
  have same : record = observation.receipt := by
    cases record
    simp only [WalObservation.receipt,receiptForWal,NativeReceiptBytes.Receipt.mk.injEq]
    exact ⟨actionSame,sequenceSame,frameSame,idSame,contextSame⟩
  exact ⟨rfl,rfl,same,receipt.2.2.2.2.1.symm.trans (congrArg NativeReceiptBytes.encode same)⟩

end WalObservation

section Body
variable {sha mapping actors artifacts units current}
    {source : Source sha mapping actors artifacts units current} {wal receipt facts}
    (native : NativeObservation source wal receipt facts)
    {indices vocabulary configured names earlyTrust planningTrust}
    {metadata : PublicPlanningBody.Metadata earlyTrust planningTrust}
    (authority : FamilyAuthority.Original source.bound indices source.numeric.profile source.numeric.quantum
      current.values vocabulary configured names metadata native.carrier)
    (shardAliases : Bytes → Option String) (checkpointNames : Value → Option Bytes) (expected : Value)

/- The selected original candidate chooses its original canonical certificate
row. A public body is then computed by the full constructor, never assumed or
looked up in a table of previously approved whole-body translations. -/
inductive Body where
  | parameter (edge : NativeParameterLineage.Edge)
      (action : native.admitted.selected.original.action = 5)
      (selected : (NativeCandidateAuthority.parameterSection native.admitted.checked.snapshot).bodies.find?
        (fun e => e.id == native.admitted.selected.original.body) = some edge)
      (leaf : FamilyParameter.OriginalLeaf authority shardAliases edge)
  | apply (edge : NativeApplyLineage.Edge)
      (action : native.admitted.selected.original.action = 7)
      (selected : (NativeCandidateAuthority.applySection native.admitted.checked.snapshot).bodies.find?
        (fun e => e.id == native.admitted.selected.original.body) = some edge)
      (result : FamilyApply.OriginalApply authority shardAliases sha checkpointNames expected edge)

def loadBody : Option (Body native authority shardAliases checkpointNames expected) :=
  if action : native.admitted.selected.original.action = 5 then
    match selected : (NativeCandidateAuthority.parameterSection native.admitted.checked.snapshot).bodies.find?
        (fun e => e.id == native.admitted.selected.original.body) with
    | none => none
    | some edge => do
      let leaf ← FamilyParameter.loadOriginalLeaf authority shardAliases edge
      some (.parameter edge action selected leaf)
  else if action : native.admitted.selected.original.action = 7 then
    match selected : (NativeCandidateAuthority.applySection native.admitted.checked.snapshot).bodies.find?
        (fun e => e.id == native.admitted.selected.original.body) with
    | none => none
    | some edge => do
      let result ← FamilyApply.loadOriginalApply authority shardAliases sha checkpointNames expected edge
      some (.apply edge action selected result)
  else none

def Body.value : Body native authority shardAliases checkpointNames expected → Value
  | .parameter edge _ _ leaf => leaf.value authority shardAliases edge
  | .apply _ _ _ result => result.value authority shardAliases

def Body.kind : Body native authority shardAliases checkpointNames expected → Value
  | .parameter .. => .text "PARAMETER"
  | .apply .. => .text "APPLY"

def Body.originalId : Body native authority shardAliases checkpointNames expected → Bytes
  | .parameter edge .. => edge.id
  | .apply edge .. => edge.id

theorem bodyLoaded (body : Body native authority shardAliases checkpointNames expected) :
    loadBody native authority shardAliases checkpointNames expected = some body := by
  cases body with
  | parameter edge action selected leaf =>
    simp only [loadBody,dif_pos action]
    split
    · rename_i absent; simp [selected] at absent
    · rename_i found foundAt
      have same := Option.some.inj (foundAt.symm.trans selected)
      subst found
      simp only [FamilyParameter.originalLeafLoaded authority shardAliases edge leaf,bind,Option.bind]
  | apply edge action selected result =>
    have notParameter : native.admitted.selected.original.action ≠ 5 := by omega
    simp only [loadBody,dif_neg notParameter,dif_pos action]
    split
    · rename_i absent; simp [selected] at absent
    · rename_i found foundAt
      have same := Option.some.inj (foundAt.symm.trans selected)
      subst found
      simp only [FamilyApply.originalApplyLoaded authority shardAliases result,bind,Option.bind]

theorem bodyOriginalIdentity (body : Body native authority shardAliases checkpointNames expected) :
    body.originalId = native.admitted.selected.original.body ∧
      native.vote.wire.bodyHash = body.originalId := by
  have identity := NativeArithmeticVote.identity native.selected
  have vote : native.vote.wire.bodyHash = native.admitted.selected.original.body := identity.2.2.2.2.2.2.1
  cases body with
  | parameter edge action selected leaf =>
    have id : edge.id = native.admitted.selected.original.body := by simpa using List.find?_some selected
    exact ⟨id,vote.trans id.symm⟩
  | apply edge action selected result =>
    have id : edge.id = native.admitted.selected.original.body := by simpa using List.find?_some selected
    exact ⟨id,vote.trans id.symm⟩

theorem bodyOriginalKind (body : Body native authority shardAliases checkpointNames expected) :
    (match body.kind with | .text kind => some (asciiBytes kind) | _ => none) = some native.vote.wire.kind := by
  have kind := (NativeArithmeticVote.selected native.selected).2.2.2.2.1
  cases body with
  | parameter edge action selected leaf =>
    simpa only [Body.kind,action,NativeVoteBytes.actionName,
      show NativeVoteBytes.ascii "PARAMETER" = asciiBytes "PARAMETER" from by decide] using congrArg some kind
  | apply edge action selected result =>
    simpa only [Body.kind,action,NativeVoteBytes.actionName,
      show NativeVoteBytes.ascii "APPLY" = asciiBytes "APPLY" from by decide] using congrArg some kind

def bodyVote (body : Body native authority shardAliases checkpointNames expected) : Option Vote := do
  let context ← expectedContext ⟨authority.parents.ec.parent.header.actor.value,body.kind,.text "",body.value⟩
  some ⟨authority.parents.ec.parent.header.actor.value,body.kind,context,body.value⟩

/- These equalities join independent primitive namespaces on the same original
keys. They do not authenticate a function merely because it returns a name.
The existing metadata/source trust boundary remains explicit. -/
def AliasChecks : Prop :=
  actorBytes mapping authority.parents.ec.parent.header.actor.value = some native.vote.wire.validator ∧
  authority.parents.ec.parent.header.actor.value ∈ actors ∧
  mapping.height authority.parents.ec.parent.header.height.value = some (NativeVectorAuthority.state source.bound).height ∧
  (mapping.epoch authority.parents.ec.parent.header.epoch.value).map asciiBytes = some (NativeVectorAuthority.policy source.bound).epoch ∧
  names (NativeVectorAuthority.policy source.bound).config = some authority.parents.ec.parent.header.config.text ∧
  checkpointNames authority.header.parent.value = some (NativeVectorAuthority.state source.bound).wire.parent

instance : Decidable (AliasChecks native authority checkpointNames) := by unfold AliasChecks; infer_instance

/- The same primitive ticket name is used by the numeric image and by every
ISC/EC/APC parent row. All unavailable configured tickets remain in the numeric
image; only actual parent members are required to have an original row here. -/
def InputAliasChecks : Prop :=
  (∀ entry ∈ authority.parents.ec.parent.entries,
    vocabulary.ticket (NativeVectorLayout.text entry.original.ticket) = some entry.ticket.text) ∧
  (∀ member ∈ authority.parents.ec.members,
    vocabulary.ticket (NativeVectorLayout.text member.original) = some member.name.text) ∧
  (∀ member ∈ authority.parents.members,
    vocabulary.ticket (NativeVectorLayout.text member.original) = some member.name.text)

instance : Decidable (InputAliasChecks native authority) := by unfold InputAliasChecks; infer_instance

structure View where
  body : Body native authority shardAliases checkpointNames expected
  projectedVote : Vote
  computed : bodyVote native authority shardAliases checkpointNames expected body = some projectedVote
  aliases : AliasChecks native authority checkpointNames
  inputAliases : InputAliasChecks native authority
  canonical : PublicState.canonical vocabulary.models (.function (voteEntries projectedVote)) = true

def loadView : Option (View native authority shardAliases checkpointNames expected) := do
  if aliases : AliasChecks native authority checkpointNames then
    if inputAliases : InputAliasChecks native authority then
      let body ← loadBody native authority shardAliases checkpointNames expected
      match computed : bodyVote native authority shardAliases checkpointNames expected body with
      | none => none
      | some projectedVote =>
        if canonical : PublicState.canonical vocabulary.models (.function (voteEntries projectedVote)) = true then
          some ⟨body,projectedVote,computed,aliases,inputAliases,canonical⟩ else none
    else none
  else none

variable {native authority shardAliases checkpointNames expected}
    (view : View native authority shardAliases checkpointNames expected)

theorem viewLoaded : loadView native authority shardAliases checkpointNames expected = some view := by
  unfold loadView
  rw [dif_pos view.aliases,dif_pos view.inputAliases,bodyLoaded native authority shardAliases checkpointNames expected view.body]
  simp only [bind,Option.bind]
  split
  · rename_i absent; simp [view.computed] at absent
  · rename_i vote found
    have same := Option.some.inj (found.symm.trans view.computed)
    subst vote
    rw [dif_pos view.canonical]

def checkView (candidate : Vote) : Option (View native authority shardAliases checkpointNames expected) := do
  let computed ← loadView native authority shardAliases checkpointNames expected
  if candidate = computed.projectedVote then some computed else none

theorem viewChecksOwnValue : checkView (native := native) (authority := authority) (shardAliases := shardAliases)
    (checkpointNames := checkpointNames) (expected := expected) view.projectedVote = some view := by
  simp only [checkView,viewLoaded view,bind,Option.bind,ite_true]

theorem substitutedVoteRejected (candidate : Vote) (different : candidate ≠ view.projectedVote) :
    checkView (native := native) (authority := authority) (shardAliases := shardAliases)
      (checkpointNames := checkpointNames) (expected := expected) candidate = none := by
  simp only [checkView,viewLoaded view,bind,Option.bind,if_neg different]

theorem viewComputedBody : view.projectedVote.body = view.body.value ∧ view.projectedVote.kind = view.body.kind ∧
    view.projectedVote.actor = authority.parents.ec.parent.header.actor.value := by
  have computed := view.computed
  simp only [bodyVote,bind,Option.bind_eq_some_iff] at computed
  obtain ⟨_,_,eq⟩ := computed
  have same := (Option.some.inj eq).symm
  exact ⟨congrArg Vote.body same,congrArg Vote.kind same,congrArg Vote.actor same⟩

theorem viewComputedContext : expectedContext view.projectedVote = some view.projectedVote.context := by
  have computed := view.computed
  simp only [bodyVote,bind,Option.bind_eq_some_iff] at computed
  obtain ⟨context,derived,eq⟩ := computed
  have same := (Option.some.inj eq).symm
  rw [same]
  exact derived

theorem viewOriginalActor : actorBytes mapping view.projectedVote.actor = some native.vote.wire.validator := by
  rw [(viewComputedBody view).2.2]
  exact view.aliases.1

theorem inputTicketsFromOriginal :
    FamilyInputs.readOriginalTickets source.bound indices = some authority.input.image.tickets := by
  have computed := authority.input.computed
  simp only [FamilyInputs.readOriginalImage,bind,Option.bind_eq_some_iff] at computed
  obtain ⟨tickets,ht,model,_,optimizer,_,last⟩ := computed
  have same := congrArg PublicArithmeticInputs.Image.tickets (Option.some.inj last)
  rw [← same]
  exact ht

theorem inputApcOriginalOrder :
    authority.input.image.tickets.map (·.ticket) =
      authority.parents.members.map (fun m => NativeVectorLayout.text m.original) := by
  have bound := FamilyInputs.originalVectorPrepared source.prepared
  have ordered := congrArg (List.map Prod.fst)
    (FamilyInputs.originalTicketsFullOrderedSource bound (inputTicketsFromOriginal (authority := authority))).2
  have ids : authority.input.image.tickets.map (·.ticket) =
      source.bound.source.plan.members.rows.map (fun r => NativeVectorLayout.text r.member.input.ticket) := by
    simpa only [List.map_map,Function.comp_def] using ordered
  obtain ⟨_,all,_,_,_,weights,_,valid⟩ := FamilyInputs.originalPlanExactMembers bound.corpus.plan.members.rows
  have raw := PublicPlanningBody.membersOriginal authority.parents.computed
  have rawText := congrArg (List.map NativeVectorLayout.text) raw
  simp only [List.map_map,Function.comp_def] at rawText
  rw [ids,rawText,← weights]
  simp only [List.map_map,Function.comp_def]
  apply List.map_congr_left
  intro row member
  exact congrArg NativeVectorLayout.text (valid row member).2.2.1.symm

include view in
theorem inputApcNamesAgree :
    authority.input.image.tickets.map (fun t => vocabulary.ticket t.ticket) =
      authority.parents.members.map (fun m => some m.name.text) := by
  have same := congrArg (List.map vocabulary.ticket) (inputApcOriginalOrder (authority := authority))
  simp only [List.map_map,Function.comp_def] at same
  rw [same]
  apply List.map_congr_left
  intro member present
  exact view.inputAliases.2.2 member present

theorem viewNoSignerInflation {other : Value} (member : other ∈ actors)
    (same : actorBytes mapping other = some native.vote.wire.validator) : other = view.projectedVote.actor := by
  apply actorAliasesInjective source.committee.names member
  · rw [(viewComputedBody view).2.2]; exact view.aliases.2.1
  · exact same
  · exact viewOriginalActor view

theorem viewsKeepOneNativeObject {otherIndices}
    {otherAuthority : FamilyAuthority.Original source.bound otherIndices source.numeric.profile source.numeric.quantum
      current.values vocabulary configured names metadata native.carrier}
    (other : View native otherAuthority shardAliases checkpointNames expected) :
    view.body.originalId = other.body.originalId ∧ view.projectedVote.actor = other.projectedVote.actor ∧
      native.entry.sequence = facts.expectedSequence := by
  refine ⟨(bodyOriginalIdentity native authority shardAliases checkpointNames expected view.body).1.trans
    (bodyOriginalIdentity native otherAuthority shardAliases checkpointNames expected other.body).1.symm,?_,originalSequence native⟩
  apply viewNoSignerInflation other
  · rw [(viewComputedBody view).2.2]; exact view.aliases.2.1
  · exact viewOriginalActor view

end Body

/- Single executable entry point for the direct arithmetic observation. The
remaining complete-state join must use this computed result, not the draft
Binding path or a supplied public-body equality. This does not assert that
unobserved global state or unrelated certificate collections are empty. -/
section Projection
variable (sha : Bytes → Bytes) (mapping : IdentityMap) (actors : List Value)
    (artifacts : Artifacts) (units : NativeStateProjection.UnitSource) (current : FamilyInputs.CurrentBasis)
    (wal receipt : Bytes) (facts : NativeConfigAdmission.RuntimeFacts) (indices : List Nat)
    (vocabulary : Vocabulary) (configured : List Ticket) (names : Bytes → Option String)
    {earlyTrust planningTrust} (metadata : PublicPlanningBody.Metadata earlyTrust planningTrust)
    (shardAliases : Bytes → Option String) (checkpointNames : Value → Option Bytes) (expected : Value)

structure Projection where
  source : Source sha mapping actors artifacts units current
  native : NativeObservation source wal receipt facts
  authority : FamilyAuthority.Original source.bound indices source.numeric.profile source.numeric.quantum
    current.values vocabulary configured names metadata native.carrier
  view : View native authority shardAliases checkpointNames expected

def loadProjection : Option (Projection sha mapping actors artifacts units current wal receipt facts indices
    vocabulary configured names metadata shardAliases checkpointNames expected) := do
  let source ← loadSource sha mapping actors artifacts units current
  let native ← loadNativeObservation source wal receipt facts
  let authority ← FamilyAuthority.loadOriginal source.bound indices source.numeric.profile source.numeric.quantum
    current.values vocabulary configured names metadata native.carrier
  let view ← loadView native authority shardAliases checkpointNames expected
  some ⟨source,native,authority,view⟩

variable {sha mapping actors artifacts units current wal receipt facts indices vocabulary configured names metadata
    shardAliases checkpointNames expected}
    (projection : Projection sha mapping actors artifacts units current wal receipt facts indices
      vocabulary configured names (earlyTrust := earlyTrust) (planningTrust := planningTrust) metadata
      shardAliases checkpointNames expected)

theorem projectionOriginalArtifacts :
    FamilyInputs.prepareOriginalVector sha artifacts.policy artifacts.state artifacts.apc artifacts.accumulator
      artifacts.proof artifacts.arithmetic artifacts.permission artifacts.inputs = some projection.source.bound ∧
    NativeWalBytes.encode sha projection.native.entry = wal ∧
    NativeReceiptBytes.encode projection.native.record = receipt ∧
    NativeVoteBytes.encodeFrame projection.native.vote.wire = projection.native.entry.command :=
  ⟨projection.source.prepared,(originalBytes projection.native).1,(originalBytes projection.native).2.1,
    (originalBytes projection.native).2.2.1⟩

theorem projectionSameProfileAndUnits :
    NativeStateProjection.selectProfile sha projection.source.bound artifacts.applyProfile = some projection.source.numeric.profile ∧
    units (FamilyInputs.currentUnitKey projection.source.bound projection.source.numeric.profile current) =
      some projection.source.numeric.quantum ∧
    FamilyInputs.OriginalProfileNormalized projection.source.numeric.profile.profile :=
  ⟨projection.source.numeric.profileSource,projection.source.numeric.unitSource,projection.source.numeric.checked.2.1⟩

theorem projectionFullInputImage :
    FamilyInputs.readOriginalImage projection.source.bound indices projection.source.numeric.profile.profile
      projection.source.numeric.quantum current.values = some projection.authority.input.image ∧
    FamilyInputs.InputNumericGuards (FamilyInputs.completedImage projection.authority.input.image configured) :=
  ⟨projection.authority.input.computed,FamilyAuthority.originalInputFullNumeric projection.authority.input⟩

theorem projectionOriginalVoteIdentity :
    projection.native.vote.wire.bodyHash = projection.view.body.originalId ∧
    actorBytes mapping projection.view.projectedVote.actor = some projection.native.vote.wire.validator ∧
    projection.native.entry.sequence = facts.expectedSequence ∧
    expectedContext projection.view.projectedVote = some projection.view.projectedVote.context :=
  ⟨(bodyOriginalIdentity projection.native projection.authority shardAliases checkpointNames expected projection.view.body).2,
    viewOriginalActor projection.view,originalSequence projection.native,viewComputedContext projection.view⟩

end Projection

/- The same full arithmetic constructors also accept a WAL-only observation.
The receipt below is derived data, never evidence of exposure. -/
section StoredProjection
variable (sha : Bytes → Bytes) (mapping : IdentityMap) (actors : List Value)
    (artifacts : Artifacts) (units : NativeStateProjection.UnitSource) (current : FamilyInputs.CurrentBasis)
    (wal : Bytes) (facts : NativeConfigAdmission.RuntimeFacts) (indices : List Nat)
    (vocabulary : Vocabulary) (configured : List Ticket) (names : Bytes → Option String)
    {earlyTrust planningTrust} (metadata : PublicPlanningBody.Metadata earlyTrust planningTrust)
    (shardAliases : Bytes → Option String) (checkpointNames : Value → Option Bytes) (expected : Value)

structure StoredProjection where
  source : Source sha mapping actors artifacts units current
  observation : WalObservation source wal facts
  authority : FamilyAuthority.Original source.bound indices source.numeric.profile source.numeric.quantum
    current.values vocabulary configured names metadata observation.native.carrier
  view : View observation.native authority shardAliases checkpointNames expected

def loadStoredProjection : Option (StoredProjection sha mapping actors artifacts units current wal facts indices
    vocabulary configured names metadata shardAliases checkpointNames expected) := do
  let source ← loadSource sha mapping actors artifacts units current
  let observation ← loadWalObservation source wal facts
  let authority ← FamilyAuthority.loadOriginal source.bound indices source.numeric.profile source.numeric.quantum
    current.values vocabulary configured names metadata observation.native.carrier
  let view ← loadView observation.native authority shardAliases checkpointNames expected
  some ⟨source,observation,authority,view⟩

variable {sha mapping actors artifacts units current wal facts indices vocabulary configured names metadata
    shardAliases checkpointNames expected}
    (stored : StoredProjection sha mapping actors artifacts units current wal facts indices
      vocabulary configured names (earlyTrust := earlyTrust) (planningTrust := planningTrust) metadata
      shardAliases checkpointNames expected)

def StoredProjection.asProjection : Projection sha mapping actors artifacts units current wal
    (NativeReceiptBytes.encode stored.observation.receipt) facts indices vocabulary configured names
    metadata shardAliases checkpointNames expected :=
  ⟨stored.source,stored.observation.native,stored.authority,stored.view⟩

theorem storedOriginalVoteIdentity :
    stored.observation.vote.wire.bodyHash = stored.view.body.originalId ∧
    actorBytes mapping stored.view.projectedVote.actor = some stored.observation.vote.wire.validator ∧
    stored.observation.entry.sequence = facts.expectedSequence ∧
    expectedContext stored.view.projectedVote = some stored.view.projectedVote.context :=
  projectionOriginalVoteIdentity stored.asProjection

theorem storedObservedReceipt {rawReceipt entry record vote}
    (observed : NativeWalBytes.bindReceipt sha artifacts.policy wal rawReceipt = some (entry,record,vote)) :
    record = stored.observation.receipt ∧ rawReceipt = NativeReceiptBytes.encode stored.observation.receipt :=
  (observedReceiptMatches stored.observation observed).2.2

end StoredProjection

/- A separately authenticated current anchor can provide initial values without
inventing a previous APPLY. Only its value/context boundary is composed here;
the complete initial state and pointer-QC correspondence remain R2.3. -/
section AnchoredProjection
variable (sha : Bytes → Bytes) (mapping : IdentityMap) (actors : List Value)
    (artifacts : Artifacts) (units : NativeStateProjection.UnitSource)
    (trust : NativeBinding.Trust) (anchor : Anchor)
    (authenticated : trust.anchorAuthenticated anchor) (recovered : trust.recoveryAuthenticated anchor)
    (pointer : NativeCurrentPointer.State) (schema : Bytes) (modelRaw optimizerRaw : List Bytes)
    (wal : Bytes) (facts : NativeConfigAdmission.RuntimeFacts) (indices : List Nat)
    (vocabulary : Vocabulary) (configured : List Ticket) (names : Bytes → Option String)
    {earlyTrust planningTrust} (metadata : PublicPlanningBody.Metadata earlyTrust planningTrust)
    (shardAliases : Bytes → Option String) (checkpointNames : Value → Option Bytes) (expected : Value)

structure AnchoredProjection where
  values : FamilyInputs.AnchoredValues sha anchor modelRaw optimizerRaw
  anchorAuthenticated : trust.anchorAuthenticated anchor
  recoveryAuthenticated : trust.recoveryAuthenticated anchor
  stored : StoredProjection sha mapping actors artifacts units ⟨values.values,pointer,schema⟩ wal facts indices
    vocabulary configured names metadata shardAliases checkpointNames expected
  context : anchor.context = NativeVectorAuthority.context stored.source.bound
  pointerValid : NativeCurrentPointer.StateValid pointer
  optimizer : pointer.optimizer = idBytes anchor.currentOptimizerHash

def loadAnchoredProjection : Option (AnchoredProjection sha mapping actors artifacts units trust anchor pointer schema
    modelRaw optimizerRaw wal facts indices vocabulary configured names metadata shardAliases checkpointNames expected) := do
  let values ← FamilyInputs.loadAnchoredValues sha anchor modelRaw optimizerRaw
  let stored ← loadStoredProjection sha mapping actors artifacts units ⟨values.values,pointer,schema⟩ wal facts indices
    vocabulary configured names metadata shardAliases checkpointNames expected
  if checked : anchor.context = NativeVectorAuthority.context stored.source.bound ∧
      NativeCurrentPointer.StateValid pointer ∧ pointer.optimizer = idBytes anchor.currentOptimizerHash then
    some ⟨values,authenticated,recovered,stored,checked.1,checked.2.1,checked.2.2⟩
  else none

variable {sha mapping actors artifacts units trust anchor pointer schema modelRaw optimizerRaw wal facts indices
    vocabulary configured names metadata shardAliases checkpointNames expected}
    (anchored : AnchoredProjection sha mapping actors artifacts units trust anchor pointer schema modelRaw optimizerRaw
      wal facts indices vocabulary configured names (earlyTrust := earlyTrust) (planningTrust := planningTrust) metadata
      shardAliases checkpointNames expected)

theorem anchoredCurrentOriginalPreimages :
    modelRaw = NativeApplyResult.decimalValues anchored.values.values.model ∧
    optimizerRaw = NativeApplyResult.decimalValues anchored.values.values.optimizer ∧
    sha (NativeApplyResult.rawValueInput .model modelRaw) = anchor.currentModelHash ∧
    sha (NativeApplyResult.rawValueInput .optimizer optimizerRaw) = anchor.currentOptimizerHash :=
  FamilyInputs.anchoredValuesOriginal anchored.values

theorem anchoredCurrentContextAndSchema :
    asciiBytes anchor.context.parentCheckpoint = pointer.checkpoint ∧
    schema = (NativeVectorAuthority.plan anchored.stored.source.bound).certificate.common.context.schema ∧
    anchor.context = NativeVectorAuthority.context anchored.stored.source.bound := by
  refine ⟨?_,anchored.stored.source.numeric.checked.1.2.2.2,anchored.context⟩
  rw [anchored.context]
  change asciiBytes (NativeVectorLayout.text (NativeVectorAuthority.state anchored.stored.source.bound).wire.parent) = _
  rw [FamilyInputs.originalLabelRoundtrip]
  exact anchored.stored.source.numeric.checked.1.2.1.symm

theorem anchoredCurrentDoesNotInventApply :
    NativeWalBytes.encode sha anchored.stored.observation.entry = wal ∧
    anchored.stored.observation.vote.wire.bodyHash = anchored.stored.view.body.originalId ∧
    anchored.stored.observation.entry.sequence = facts.expectedSequence ∧
    FamilyInputs.readOriginalImage anchored.stored.source.bound indices anchored.stored.source.numeric.profile.profile
      anchored.stored.source.numeric.quantum anchored.values.values = some anchored.stored.authority.input.image :=
  ⟨(walOnlyOriginalBytes anchored.stored.observation).1,(storedOriginalVoteIdentity anchored.stored).1,
    (storedOriginalVoteIdentity anchored.stored).2.2.1,(projectionFullInputImage anchored.stored.asProjection).1⟩

end AnchoredProjection

/- Source provenance for an observed nonempty current-pointer history is checked
by the EXISTING native reader. This only reuses that reader at the static source
boundary; it adds no recovery transition theorem. Arbitrary initial snapshots
and unknown observations must not be represented by a fabricated last APPLY. -/
section ObservedProjection
variable (sha : Bytes → Bytes) (mapping : IdentityMap) (actors : List Value)
    (artifacts : Artifacts) (units : NativeStateProjection.UnitSource)
    (initial : NativeCurrentPointer.State) (pointer : NativePointerWal.Observation)
    (currentInputs : List NativeCurrentHistory.Input)
    (wal receipt : Bytes) (facts : NativeConfigAdmission.RuntimeFacts) (indices : List Nat)
    (vocabulary : Vocabulary) (configured : List Ticket) (names : Bytes → Option String)
    {earlyTrust planningTrust} (metadata : PublicPlanningBody.Metadata earlyTrust planningTrust)
    (shardAliases : Bytes → Option String) (checkpointNames : Value → Option Bytes) (expected : Value)

structure ObservedProjection where
  current : NativeCurrentHistory.Current
  currentSource : NativeCurrentHistory.current sha initial pointer currentInputs = some current
  projection : Projection sha mapping actors artifacts units current wal receipt facts indices
    vocabulary configured names metadata shardAliases checkpointNames expected

def loadObservedProjection : Option (ObservedProjection sha mapping actors artifacts units initial pointer currentInputs
    wal receipt facts indices vocabulary configured names metadata shardAliases checkpointNames expected) := do
  match currentSource : NativeCurrentHistory.current sha initial pointer currentInputs with
  | none => none
  | some current =>
    let projection ← loadProjection sha mapping actors artifacts units current wal receipt facts indices
      vocabulary configured names metadata shardAliases checkpointNames expected
    some ⟨current,currentSource,projection⟩

theorem unknownCurrentRejects :
    loadObservedProjection sha mapping actors artifacts units initial .unknown currentInputs wal receipt facts indices
      vocabulary configured names metadata shardAliases checkpointNames expected = none := rfl

variable {sha mapping actors artifacts units initial currentInputs wal receipt facts indices vocabulary configured names
    metadata shardAliases checkpointNames expected} {pointerRaw : Bytes}
    (observed : ObservedProjection sha mapping actors artifacts units initial (.bytes pointerRaw) currentInputs
      wal receipt facts indices vocabulary configured names (earlyTrust := earlyTrust) (planningTrust := planningTrust)
      metadata shardAliases checkpointNames expected)

theorem observedCurrentOriginalBytes :
    NativePointerWal.recover sha initial (.bytes pointerRaw) = some observed.current.recovery.wal ∧
    observed.current.last.edge.decoded.candidate.modelValues = NativeApplyResult.decimalValues observed.current.last.values.model ∧
    observed.current.last.edge.decoded.candidate.optimizerValues = NativeApplyResult.decimalValues observed.current.last.values.optimizer :=
  ⟨NativeCurrentHistory.retainedObservation observed.currentSource,
    NativeCurrentHistory.currentOriginalValues observed.currentSource⟩

theorem observedCurrentPreimages :
    (NativeVectorAuthority.state observed.projection.source.bound).wire.parent =
      idBytes (sha (valueHashInput .model observed.current.last.values.model)) ∧
    observed.current.recovery.wal.state.optimizer =
      idBytes (sha (valueHashInput .optimizer observed.current.last.values.optimizer)) := by
  have hashes := NativeCurrentHistory.currentValueHashes observed.currentSource
  exact ⟨observed.projection.source.numeric.checked.1.2.1.symm.trans hashes.1,hashes.2⟩

end ObservedProjection

/- Select by the original mixed-WAL position. State commands retain their
positions; no vote count or coordinate index is substituted for a sequence.
This is a static source join. Complete public collection correspondence is not
inferred merely because the complete native byte stream was checked. -/
section LocatedProjection
variable (sha : Bytes → Bytes) (mapping : IdentityMap) (actors : List Value)
    (artifacts : Artifacts) (units : NativeStateProjection.UnitSource)
    (initial : NativeCurrentPointer.State) (pointer : NativePointerWal.Observation)
    (currentInputs : List NativeCurrentHistory.Input)
    (observation : Option Bytes) (position : Nat) (facts : NativeConfigAdmission.RuntimeFacts)
    (indices : List Nat) (vocabulary : Vocabulary) (configured : List Ticket)
    (names : Bytes → Option String) {earlyTrust planningTrust}
    (metadata : PublicPlanningBody.Metadata earlyTrust planningTrust)
    (shardAliases : Bytes → Option String) (checkpointNames : Value → Option Bytes) (expected : Value)

structure LocatedProjection where
  raw : Bytes
  known : observation = some raw
  scan : NativeWalScan.Result
  scanned : NativeWalScan.check sha raw = some scan
  complete : scan.torn = false
  piece : NativeWalScan.Piece
  atPosition : scan.pieces[position]? = some piece
  current : NativeCurrentHistory.Current
  currentSource : NativeCurrentHistory.current sha initial pointer currentInputs = some current
  stored : StoredProjection sha mapping actors artifacts units current piece.bytes facts indices
    vocabulary configured names metadata shardAliases checkpointNames expected
  entry : stored.observation.entry = piece.entry

def loadLocatedProjection : Option (LocatedProjection sha mapping actors artifacts units initial pointer currentInputs
    observation position facts indices vocabulary configured names metadata shardAliases checkpointNames expected) := do
  match known : observation with
  | none => none
  | some raw =>
    match scanned : NativeWalScan.check sha raw with
    | none => none
    | some scan =>
      if complete : scan.torn = false then
        match atPosition : scan.pieces[position]? with
        | none => none
        | some piece =>
          match currentSource : NativeCurrentHistory.current sha initial pointer currentInputs with
          | none => none
          | some current =>
            let stored ← loadStoredProjection sha mapping actors artifacts units current piece.bytes facts indices
              vocabulary configured names metadata shardAliases checkpointNames expected
            if entry : stored.observation.entry = piece.entry then
              some ⟨raw,known,scan,scanned,complete,piece,atPosition,current,currentSource,stored,entry⟩
            else none
      else none

theorem unknownWalRejects :
    loadLocatedProjection sha mapping actors artifacts units initial pointer currentInputs none position facts indices
      vocabulary configured names metadata shardAliases checkpointNames expected = none := rfl

variable {sha mapping actors artifacts units initial pointer currentInputs observation position facts indices
    vocabulary configured names metadata shardAliases checkpointNames expected}
    (located : LocatedProjection sha mapping actors artifacts units initial pointer currentInputs observation
      position facts indices vocabulary configured names (earlyTrust := earlyTrust) (planningTrust := planningTrust)
      metadata shardAliases checkpointNames expected)

theorem locatedWholeOriginalBytes :
    located.raw = NativeWalScan.joined located.scan.pieces ∧
    ∀ piece ∈ located.scan.pieces, NativeWalBytes.decode sha piece.bytes = some piece.entry ∧
      NativeWalBytes.encode sha piece.entry = piece.bytes := by
  have tail := NativeWalScan.checkedTerminal sha located.raw located.scan located.scanned
  simp only [located.complete,Bool.false_eq_true,if_false] at tail
  have partition := NativeWalScan.checkedPartition sha located.raw located.scan located.scanned
  rw [tail,List.append_nil] at partition
  refine ⟨partition,?_⟩
  intro piece member
  have scanned := (NativeWalScan.checkedSound sha located.raw located.scan located.scanned).1
  exact ⟨(NativeWalScan.tracePieces sha located.raw located.scan
    ((NativeWalScan.scanExact sha located.raw located.scan).mp scanned) piece member).1,
    (NativeWalScan.scannedCanonical sha located.raw located.scan scanned piece member).2⟩

theorem locatedOriginalSequence :
    located.stored.observation.entry.sequence = position + 1 ∧ facts.expectedSequence = position + 1 := by
  have atEntry : (NativeWalScan.entries located.scan)[position]? = some located.piece.entry := by
    simp only [NativeWalScan.entries,List.getElem?_map,located.atPosition,Option.map_some]
  have sequence := NativeWalScan.checkedPosition sha located.raw located.scan located.scanned
    position located.piece.entry atEntry
  have original := (walOnlyOriginalBytes located.stored.observation).2.2
  rw [located.entry] at original
  constructor
  · rw [located.entry,sequence]; omega
  · omega

theorem locatedOriginalObject :
    located.stored.observation.vote.wire.bodyHash = located.stored.view.body.originalId ∧
    actorBytes mapping located.stored.view.projectedVote.actor = some located.stored.observation.vote.wire.validator ∧
    located.stored.observation.entry.sequence = position + 1 ∧
    expectedContext located.stored.view.projectedVote = some located.stored.view.projectedVote.context :=
  ⟨(storedOriginalVoteIdentity located.stored).1,(storedOriginalVoteIdentity located.stored).2.1,
    (locatedOriginalSequence located).1,(storedOriginalVoteIdentity located.stored).2.2.2⟩

theorem locatedCurrentPreimages :
    (NativeVectorAuthority.state located.stored.source.bound).wire.parent =
      idBytes (sha (valueHashInput .model located.current.last.values.model)) ∧
    located.current.recovery.wal.state.optimizer =
      idBytes (sha (valueHashInput .optimizer located.current.last.values.optimizer)) := by
  cases pointer with
  | unknown =>
    have source := located.currentSource
    simp only [NativeCurrentHistory.unknownNoCurrent] at source
    contradiction
  | bytes raw =>
    have hashes := NativeCurrentHistory.currentValueHashes located.currentSource
    exact ⟨located.stored.source.numeric.checked.1.2.1.symm.trans hashes.1,hashes.2⟩

include located in
theorem incompleteWalCannotHaveProjection {raw scan}
    (known : observation = some raw) (scanned : NativeWalScan.check sha raw = some scan)
    (torn : scan.torn = true) : False := by
  have rawSame := Option.some.inj (known.symm.trans located.known)
  subst raw
  have scanSame := Option.some.inj (scanned.symm.trans located.scanned)
  subst scan
  rw [located.complete] at torn
  contradiction

include located in
theorem corruptWalCannotHaveProjection {raw}
    (known : observation = some raw) (corrupt : NativeWalScan.check sha raw = none) : False := by
  have rawSame := Option.some.inj (known.symm.trans located.known)
  subst raw
  rw [located.scanned] at corrupt
  contradiction

theorem commandPositionCannotHaveProjection (command : located.piece.entry.kind = 1) : False := by
  have vote := located.stored.observation.link.1
  rw [located.entry,command] at vote
  contradiction

/- Running the executable source join at different coordinate selectors must
resolve the same original objects. No equality of translated bodies is assumed. -/
theorem locatedSelectorsShareOriginals {otherIndices}
    (other : LocatedProjection sha mapping actors artifacts units initial pointer currentInputs observation
      position facts otherIndices vocabulary configured names metadata shardAliases checkpointNames expected) :
    located.raw = other.raw ∧ located.scan = other.scan ∧ located.piece = other.piece ∧
    located.stored.observation.entry = other.stored.observation.entry ∧
    located.stored.observation.vote = other.stored.observation.vote ∧
    located.current = other.current ∧ located.stored.source.bound = other.stored.source.bound := by
  have raw := Option.some.inj (located.known.symm.trans other.known)
  have scan : located.scan = other.scan := Option.some.inj
    (located.scanned.symm.trans ((congrArg (NativeWalScan.check sha) raw).trans other.scanned))
  have piece : located.piece = other.piece := Option.some.inj
    (located.atPosition.symm.trans ((congrArg (fun s : NativeWalScan.Result => s.pieces[position]?) scan).trans other.atPosition))
  have entry : located.stored.observation.entry = other.stored.observation.entry :=
    located.entry.trans ((congrArg NativeWalScan.Piece.entry piece).trans other.entry.symm)
  have vote : located.stored.observation.vote = other.stored.observation.vote := Option.some.inj
    (located.stored.observation.frame.symm.trans
      ((congrArg (fun e : NativeWalBytes.Entry => NativeVoteBytes.decodeFrame e.command) entry).trans
        other.stored.observation.frame))
  exact ⟨raw,scan,piece,entry,vote,
    Option.some.inj (located.currentSource.symm.trans other.currentSource),
    Option.some.inj (located.stored.source.prepared.symm.trans other.stored.source.prepared)⟩

theorem locatedSelectorsPreserveIdentity {otherIndices}
    (other : LocatedProjection sha mapping actors artifacts units initial pointer currentInputs observation
      position facts otherIndices vocabulary configured names metadata shardAliases checkpointNames expected) :
    located.stored.view.body.originalId = other.stored.view.body.originalId ∧
    located.stored.view.projectedVote.actor = other.stored.view.projectedVote.actor ∧
    located.stored.observation.entry.sequence = other.stored.observation.entry.sequence ∧
    located.current.last.values.model = other.current.last.values.model ∧
    located.current.last.values.optimizer = other.current.last.values.optimizer := by
  have originals := locatedSelectorsShareOriginals located other
  have vote := originals.2.2.2.2.1
  have current := originals.2.2.2.2.2.1
  have left := storedOriginalVoteIdentity located.stored
  have right := storedOriginalVoteIdentity other.stored
  refine ⟨left.1.symm.trans ((congrArg (fun v : NativeVoteBytes.Vote => v.wire.bodyHash) vote).trans right.1),?_,
    congrArg NativeWalBytes.Entry.sequence originals.2.2.2.1,
    congrArg (fun c : NativeCurrentHistory.Current => c.last.values.model) current,
    congrArg (fun c : NativeCurrentHistory.Current => c.last.values.optimizer) current⟩
  apply viewNoSignerInflation other.stored.view
  · rw [(viewComputedBody located.stored.view).2.2]
    exact located.stored.view.aliases.2.1
  · exact left.2.1.trans (congrArg (fun v : NativeVoteBytes.Vote => some v.wire.validator) vote)

end LocatedProjection
/- The ROOT observation uses the existing ordinary native selector. Its
PARAMETER ancestors are finalized original objects; no future APPLY or
conversion result is a premise of constructing the aggregate body. -/
section RootObservation
variable {sha mapping actors artifacts units current}
    (source : Source sha mapping actors artifacts units current)

structure RootObservation (source : Source sha mapping actors artifacts units current)
    (wal : Bytes) (facts : NativeConfigAdmission.RuntimeFacts) where
  entry : NativeWalBytes.Entry
  decoded : NativeWalBytes.decode sha wal = some entry
  loaded : NativeEarlySource.Loaded sha artifacts.policy artifacts.state entry.command facts
  root : NativeRootSource.Root loaded.original
  id : Bytes
  hashed : NativeVoteBytes.voteId sha entry.command = some id
  valid : NativeReceiptBytes.Valid (receiptForWal entry loaded.original.vote loaded.original.admitted id)
  link : NativeWalBytes.ReceiptLink sha artifacts.policy entry
    (receiptForWal entry loaded.original.vote loaded.original.admitted id)
  voteLink : NativeVoteBytes.ReceiptLinked sha
    (receiptForWal entry loaded.original.vote loaded.original.admitted id) loaded.original.vote

def loadRootObservation (wal : Bytes) (facts : NativeConfigAdmission.RuntimeFacts) :
    Option (RootObservation source wal facts) := do
  match decoded : NativeWalBytes.decode sha wal with
  | none => none
  | some entry =>
    let loaded ← NativeEarlySource.load sha artifacts.policy artifacts.state entry.command facts
    let root ← NativeRootSource.loadRoot loaded.original
    match hashed : NativeVoteBytes.voteId sha entry.command with
    | none => none
    | some id =>
      if h : NativeReceiptBytes.Valid (receiptForWal entry loaded.original.vote loaded.original.admitted id) ∧
          NativeWalBytes.ReceiptLink sha artifacts.policy entry
            (receiptForWal entry loaded.original.vote loaded.original.admitted id) ∧
          NativeVoteBytes.ReceiptLinked sha
            (receiptForWal entry loaded.original.vote loaded.original.admitted id) loaded.original.vote then
        some ⟨entry,decoded,loaded,root,id,hashed,h.1,h.2.1,h.2.2⟩
      else none

variable {source wal facts} (observation : RootObservation source wal facts)

def RootObservation.receipt : NativeReceiptBytes.Receipt :=
  receiptForWal observation.entry observation.loaded.original.vote observation.loaded.original.admitted observation.id

theorem rootObservationLoaded : loadRootObservation source wal facts = some observation := by
  unfold loadRootObservation
  split
  · rename_i absent; rw [observation.decoded] at absent; contradiction
  · rename_i entry found
    cases Option.some.inj (found.symm.trans observation.decoded)
    have selected : NativeEarlySource.load sha artifacts.policy artifacts.state observation.entry.command facts =
        some observation.loaded := by
      unfold NativeEarlySource.load
      split
      · rename_i absent; rw [observation.loaded.computed] at absent; contradiction
      · rename_i original found
        cases Option.some.inj (found.symm.trans observation.loaded.computed)
        rfl
    rw [selected]
    simp only [bind,Option.bind,NativeRootSource.fromComponents observation.root]
    split
    · rename_i absent; rw [observation.hashed] at absent; contradiction
    · rename_i id found
      cases Option.some.inj (found.symm.trans observation.hashed)
      rw [dif_pos ⟨observation.valid,observation.link,observation.voteLink⟩]

theorem rootOriginalWalBinding :
    NativeWalBytes.bindReceipt sha artifacts.policy wal (NativeReceiptBytes.encode observation.receipt) =
      some (observation.entry,observation.receipt,observation.loaded.original.vote) :=
  NativeWalBytes.bindFromComponents sha artifacts.policy wal (NativeReceiptBytes.encode observation.receipt)
    observation.entry observation.receipt observation.loaded.original.vote observation.decoded
    (NativeVoteBytes.receiptFromComponents sha observation.receipt observation.loaded.original.vote observation.valid
      (NativeVoteBytes.bindingFromComponents sha observation.receipt observation.loaded.original.vote
        (NativeEarlySource.loadedOriginal observation.loaded).vote observation.voteLink)) observation.link

theorem rootOriginalBytes :
    NativeWalBytes.encode sha observation.entry = wal ∧
    NativeVoteBytes.encodeFrame observation.loaded.original.vote.wire = observation.entry.command ∧
    observation.entry.sequence = facts.expectedSequence := by
  have bytes := NativeWalBytes.boundOriginalBytes sha artifacts.policy wal (NativeReceiptBytes.encode observation.receipt)
    observation.entry observation.receipt observation.loaded.original.vote (rootOriginalWalBinding observation)
  exact ⟨bytes.1,bytes.2.2.1,bytes.2.2.2.trans
    (NativeEarlySource.loadedIdentity observation.loaded).2.2.2.2.2.2.2.2⟩

theorem rootSameOriginalPolicyState :
    observation.loaded.original.policy = NativeVectorAuthority.policy source.bound ∧
    observation.loaded.original.state = NativeVectorAuthority.state source.bound := by
  obtain ⟨_,policy,state⟩ := sourceRaw source
  obtain ⟨_,original⟩ := (NativeEarlySource.loadedOriginal observation.loaded).policy
  exact ⟨congrArg Prod.snd (Option.some.inj (original.symm.trans policy)),
    Option.some.inj ((NativeEarlySource.loadedOriginal observation.loaded).state.symm.trans state)⟩

theorem rootOriginalBodyAndContext :
    observation.loaded.original.vote.wire.bodyHash = observation.root.original.id ∧
    NativeAggregateRoot.bodyId sha observation.root.original.certificate.common =
      some observation.loaded.original.vote.wire.bodyHash ∧
    NativeCandidateAuthority.parentContext sha "deltareduce.vote-context.root.v1"
      observation.root.original.certificate.common.plan = some observation.loaded.original.vote.wire.context :=
  ⟨(NativeRootSource.identity observation.loaded observation.root).1,
    NativeRootSource.originalPreimage observation.loaded observation.root,
    (NativeRootSource.identity observation.loaded observation.root).2⟩

theorem rootNoFutureApplyPremise :
    observation.root.original.shards.map NativeAggregateLineage.shardLeaf =
      observation.root.original.certificate.common.leaves ∧
    ∀ shard ∈ observation.root.original.shards,
      shard.id ∈ (NativeRootSource.sectionOf observation.loaded.original).parameters.prior.finalized ∧
      NativeContractSize.contentId sha NativeParameter.domain (NativeParameter.json shard.certificate) = some shard.id :=
  ⟨NativeRootSource.completeLeaves observation.loaded observation.root,
    fun _ member => NativeRootSource.leafFinalizedAndHashed observation.loaded observation.root member⟩

end RootObservation

section RootView
variable {sha mapping actors artifacts units current source wal facts indices vocabulary configured names earlyTrust planningTrust metadata}
    (observation : RootObservation (sha := sha) (mapping := mapping) (actors := actors)
      (artifacts := artifacts) (units := units) (current := current) source wal facts)
    (authority : FamilyAuthority.Original source.bound indices source.numeric.profile source.numeric.quantum
      current.values vocabulary configured names (earlyTrust := earlyTrust) (planningTrust := planningTrust)
      metadata observation.loaded.original)
    (shardAliases : Bytes → Option String) (checkpointNames : Value → Option Bytes)

def rootBodyVote (root : FamilyApply.OriginalRoot authority shardAliases observation.root.original) : Option Vote := do
  some (PublicRootEnvelope.envelope authority.parents.ec.parent.header.actor.value authority.parents.value
    (FamilyApply.originalAggregate authority shardAliases root.entries))

theorem rootBodyVoteTotal (root : FamilyApply.OriginalRoot authority shardAliases observation.root.original) :
    rootBodyVote observation authority shardAliases root =
      some (PublicRootEnvelope.envelope authority.parents.ec.parent.header.actor.value authority.parents.value
        (FamilyApply.originalAggregate authority shardAliases root.entries)) := rfl

def RootAliasChecks : Prop :=
  actorBytes mapping authority.parents.ec.parent.header.actor.value = some observation.loaded.original.vote.wire.validator ∧
  authority.parents.ec.parent.header.actor.value ∈ actors ∧
  mapping.height authority.parents.ec.parent.header.height.value = some (NativeVectorAuthority.state source.bound).height ∧
  (mapping.epoch authority.parents.ec.parent.header.epoch.value).map asciiBytes = some (NativeVectorAuthority.policy source.bound).epoch ∧
  names (NativeVectorAuthority.policy source.bound).config = some authority.parents.ec.parent.header.config.text ∧
  checkpointNames authority.header.parent.value = some (NativeVectorAuthority.state source.bound).wire.parent ∧
  (∀ entry ∈ authority.parents.ec.parent.entries,
    vocabulary.ticket (NativeVectorLayout.text entry.original.ticket) = some entry.ticket.text) ∧
  (∀ member ∈ authority.parents.ec.members,
    vocabulary.ticket (NativeVectorLayout.text member.original) = some member.name.text) ∧
  (∀ member ∈ authority.parents.members,
    vocabulary.ticket (NativeVectorLayout.text member.original) = some member.name.text)

instance : Decidable (RootAliasChecks observation authority checkpointNames) := by
  unfold RootAliasChecks; infer_instance

structure RootView where
  root : FamilyApply.OriginalRoot authority shardAliases observation.root.original
  projectedVote : Vote
  computed : rootBodyVote observation authority shardAliases root = some projectedVote
  aliases : RootAliasChecks observation authority checkpointNames
  canonical : PublicState.canonical vocabulary.models (.function (voteEntries projectedVote)) = true

def loadRootView : Option (RootView observation authority shardAliases checkpointNames) := do
  if aliases : RootAliasChecks observation authority checkpointNames then
    let root ← FamilyApply.loadOriginalRoot authority shardAliases observation.root.original
    match computed : rootBodyVote observation authority shardAliases root with
    | none => none
    | some projectedVote =>
      if canonical : PublicState.canonical vocabulary.models (.function (voteEntries projectedVote)) = true then
        some ⟨root,projectedVote,computed,aliases,canonical⟩ else none
  else none

variable {observation authority shardAliases checkpointNames}
    (view : RootView observation authority shardAliases checkpointNames)

theorem rootViewLoaded : loadRootView observation authority shardAliases checkpointNames = some view := by
  unfold loadRootView
  rw [dif_pos view.aliases,FamilyApply.originalRootLoaded authority shardAliases view.root]
  simp only [bind,Option.bind]
  split
  · rename_i absent; rw [view.computed] at absent; contradiction
  · rename_i projected found
    cases Option.some.inj (found.symm.trans view.computed)
    rw [dif_pos view.canonical]

theorem rootViewComputed :
    view.projectedVote.body = FamilyApply.originalAggregate authority shardAliases view.root.entries ∧
    view.projectedVote.kind = .text "AGGREGATE_ROOT" ∧
    view.projectedVote.actor = authority.parents.ec.parent.header.actor.value ∧
    readField view.projectedVote.body "apc" = some view.projectedVote.context := by
  have computed := view.computed
  have same := (Option.some.inj computed).symm
  rw [same]
  exact ⟨rfl,rfl,rfl,rfl⟩

theorem rootUsesExistingApcContext : view.projectedVote.context = authority.parents.value ∧
    expectedContext view.projectedVote = none := by
  have same := (Option.some.inj view.computed).symm
  rw [same]
  exact ⟨rfl,rfl⟩

theorem rootViewKeepsWholeOriginals :
    view.root.entries.map FamilyApply.OriginalEntry.native = observation.root.original.shards ∧
    observation.loaded.original.vote.wire.bodyHash = observation.root.original.id ∧
    actorBytes mapping view.projectedVote.actor = some observation.loaded.original.vote.wire.validator ∧
    observation.entry.sequence = facts.expectedSequence := by
  refine ⟨FamilyApply.originalRootExact authority shardAliases view.root,
    (rootOriginalBodyAndContext observation).1,?_,(rootOriginalBytes observation).2.2⟩
  rw [(rootViewComputed view).2.2.1]
  exact view.aliases.1

theorem rootVoteNativeKind : observation.loaded.original.vote.wire.kind = NativeVoteBytes.ascii "AGGREGATE_ROOT" := by
  have checked := NativeSelectedVote.originalByteAuthority observation.loaded.computed
  have kind := checked.2.2.2.2.2.2.1
  simpa only [observation.root.kind,NativeVoteBytes.actionName] using kind.symm

theorem rootViewNoSignerInflation {other : Value} (member : other ∈ actors)
    (same : actorBytes mapping other = some observation.loaded.original.vote.wire.validator) :
    other = view.projectedVote.actor := by
  apply actorAliasesInjective source.committee.names member
  · rw [(rootViewComputed view).2.2.1]; exact view.aliases.2.1
  · exact same
  · exact (rootViewKeepsWholeOriginals view).2.2.1

theorem rootViewsKeepOneNativeObject {otherIndices}
    {otherAuthority : FamilyAuthority.Original source.bound otherIndices source.numeric.profile source.numeric.quantum
      current.values vocabulary configured names metadata observation.loaded.original}
    (other : RootView observation otherAuthority shardAliases checkpointNames) :
    view.root.entries.map FamilyApply.OriginalEntry.native = other.root.entries.map FamilyApply.OriginalEntry.native ∧
    view.projectedVote.actor = other.projectedVote.actor ∧ observation.entry.sequence = facts.expectedSequence := by
  refine ⟨(rootViewKeepsWholeOriginals view).1.trans (rootViewKeepsWholeOriginals other).1.symm,?_,
    (rootOriginalBytes observation).2.2⟩
  apply rootViewNoSignerInflation other
  · rw [(rootViewComputed view).2.2.1]; exact view.aliases.2.1
  · exact (rootViewKeepsWholeOriginals view).2.2.1

end RootView

section RootProjection
variable (sha : Bytes → Bytes) (mapping : IdentityMap) (actors : List Value)
    (artifacts : Artifacts) (units : NativeStateProjection.UnitSource) (current : FamilyInputs.CurrentBasis)
    (wal : Bytes) (facts : NativeConfigAdmission.RuntimeFacts) (indices : List Nat)
    (vocabulary : Vocabulary) (configured : List Ticket) (names : Bytes → Option String)
    {earlyTrust planningTrust} (metadata : PublicPlanningBody.Metadata earlyTrust planningTrust)
    (shardAliases : Bytes → Option String) (checkpointNames : Value → Option Bytes)

structure RootProjection where
  source : Source sha mapping actors artifacts units current
  observation : RootObservation source wal facts
  authority : FamilyAuthority.Original source.bound indices source.numeric.profile source.numeric.quantum
    current.values vocabulary configured names metadata observation.loaded.original
  view : RootView observation authority shardAliases checkpointNames

def loadRootProjection : Option (RootProjection sha mapping actors artifacts units current wal facts indices
    vocabulary configured names metadata shardAliases checkpointNames) := do
  let source ← loadSource sha mapping actors artifacts units current
  let observation ← loadRootObservation source wal facts
  let authority ← FamilyAuthority.loadOriginal source.bound indices source.numeric.profile source.numeric.quantum
    current.values vocabulary configured names metadata observation.loaded.original
  let view ← loadRootView observation authority shardAliases checkpointNames
  some ⟨source,observation,authority,view⟩

end RootProjection

/- Common parent values are derived from the same original certificate graph
and primitive metadata. Neither an equality of entire translated bodies nor a
coordinate approval table is supplied. Actor is deliberately absent from these
certificate values, so different original signers may share the same parents. -/
section CommonParents

theorem earlyHeaderControls {trust} {metadata : PublicEarlyBody.Metadata trust}
    {left right : NativeSelectedVote.Checked}
    (a : PublicEarlyBody.Header metadata left) (b : PublicEarlyBody.Header metadata right)
    (height : left.state.height = right.state.height)
    (epoch : left.policy.epoch = right.policy.epoch)
    (config : left.policy.config = right.policy.config) :
    a.round = b.round ∧ a.epoch.value = b.epoch.value ∧ a.config.value = b.config.value := by
  have heights : a.height.text = b.height.text := by
    apply Option.some.inj
    rw [← a.height.selected,← b.height.selected,height]
  have epochs : a.epoch.text = b.epoch.text := by
    apply Option.some.inj
    rw [← a.epoch.selected,← b.epoch.selected,epoch]
  have configs : a.config.text = b.config.text := by
    apply Option.some.inj
    rw [← a.config.selected,← b.config.selected,config]
  simp only [PublicEarlyBody.Header.round,PublicEarlyBody.Name.value,heights,epochs,configs,and_self]

theorem iscParentsFromSameOriginal {earlyTrust planningTrust}
    {metadata : PublicPlanningBody.Metadata earlyTrust planningTrust}
    {left right : NativeSelectedVote.Checked} {native : NativeIscCertificate.Checked}
    (a : PublicPlanningBody.IscBody metadata left native) (b : PublicPlanningBody.IscBody metadata right native)
    (height : left.state.height = right.state.height)
    (epoch : left.policy.epoch = right.policy.epoch)
    (config : left.policy.config = right.policy.config) :
    a.value = b.value ∧ a.header.epoch.value = b.header.epoch.value := by
  have headers := earlyHeaderControls a.header b.header height epoch config
  have policy := Option.some.inj (a.policySelected.symm.trans b.policySelected)
  have entries := Option.some.inj (a.computed.symm.trans b.computed)
  exact ⟨by simp only [PublicPlanningBody.IscBody.value,headers.1,headers.2.2,policy,entries],headers.2.1⟩

theorem ecParentsFromSameOriginal {earlyTrust planningTrust}
    {metadata : PublicPlanningBody.Metadata earlyTrust planningTrust}
    {left right : NativeSelectedVote.Checked} {native : NativeEligibilityLineage.Edge}
    (a : PublicPlanningBody.EcBody metadata left native) (b : PublicPlanningBody.EcBody metadata right native)
    (height : left.state.height = right.state.height)
    (epoch : left.policy.epoch = right.policy.epoch)
    (config : left.policy.config = right.policy.config) :
    a.parent.value = b.parent.value ∧ a.seedValue = b.seedValue ∧ a.value = b.value := by
  have parent := iscParentsFromSameOriginal a.parent b.parent height epoch config
  have seed := Option.some.inj (a.seed.selected.symm.trans b.seed.selected)
  have norm := Option.some.inj (a.norm.selected.symm.trans b.norm.selected)
  have members := Option.some.inj (a.computed.symm.trans b.computed)
  have seedValue : a.seedValue = b.seedValue := by
    simp only [PublicPlanningBody.EcBody.seedValue,parent.1,parent.2,PublicPlanningBody.Name.value,seed]
  exact ⟨parent.1,seedValue,by
    simp only [PublicPlanningBody.EcBody.value,parent.1,seedValue,members,PublicPlanningBody.Name.value,norm]⟩

theorem apcParentsFromSameOriginal {earlyTrust planningTrust}
    {metadata : PublicPlanningBody.Metadata earlyTrust planningTrust}
    {left right : NativeSelectedVote.Checked} {native : NativePlanLineage.Edge}
    (a : PublicPlanningBody.ApcBody metadata left native) (b : PublicPlanningBody.ApcBody metadata right native)
    (height : left.state.height = right.state.height)
    (epoch : left.policy.epoch = right.policy.epoch)
    (config : left.policy.config = right.policy.config) :
    a.ec.parent.value = b.ec.parent.value ∧ a.ec.seedValue = b.ec.seedValue ∧
    a.ec.value = b.ec.value ∧ a.value = b.value := by
  have parents := ecParentsFromSameOriginal a.ec b.ec height epoch config
  have coefficient := Option.some.inj (a.coefficient.selected.symm.trans b.coefficient.selected)
  have members := Option.some.inj (a.computed.symm.trans b.computed)
  exact ⟨parents.1,parents.2.1,parents.2.2,by
    simp only [PublicPlanningBody.ApcBody.value,parents.1,parents.2.1,parents.2.2,members,
      PublicPlanningBody.Name.value,coefficient]⟩

variable {sha mapping actors artifacts units current}
    {source : Source sha mapping actors artifacts units current}
    {wal receipt facts rootWal rootFacts indices rootIndices vocabulary configured names earlyTrust planningTrust metadata}
    (arithmetic : NativeObservation source wal receipt facts)
    (root : RootObservation source rootWal rootFacts)
    (arithmeticAuthority : FamilyAuthority.Original source.bound indices source.numeric.profile source.numeric.quantum
      current.values vocabulary configured names (earlyTrust := earlyTrust) (planningTrust := planningTrust)
      metadata arithmetic.carrier)
    (rootAuthority : FamilyAuthority.Original source.bound rootIndices source.numeric.profile source.numeric.quantum
      current.values vocabulary configured names metadata root.loaded.original)

theorem rootAndArithmeticHaveSameParents :
    arithmeticAuthority.parents.ec.parent.value = rootAuthority.parents.ec.parent.value ∧
    arithmeticAuthority.parents.ec.seedValue = rootAuthority.parents.ec.seedValue ∧
    arithmeticAuthority.parents.ec.value = rootAuthority.parents.ec.value ∧
    arithmeticAuthority.parents.value = rootAuthority.parents.value := by
  have same := rootSameOriginalPolicyState root
  apply apcParentsFromSameOriginal arithmeticAuthority.parents rootAuthority.parents
  · exact congrArg NativeStateBytes.State.height same.2.symm
  · exact congrArg NativePolicyBytes.Policy.epoch same.1.symm
  · exact congrArg NativePolicyBytes.Policy.config same.1.symm

theorem parameterApplySelectorsHaveSameParents {otherIndices}
    (other : FamilyAuthority.Original source.bound otherIndices source.numeric.profile source.numeric.quantum
      current.values vocabulary configured names metadata arithmetic.carrier) :
    arithmeticAuthority.parents.ec.parent.value = other.parents.ec.parent.value ∧
    arithmeticAuthority.parents.ec.seedValue = other.parents.ec.seedValue ∧
    arithmeticAuthority.parents.ec.value = other.parents.ec.value ∧
    arithmeticAuthority.parents.value = other.parents.value :=
  apcParentsFromSameOriginal arithmeticAuthority.parents other.parents rfl rfl rfl

end CommonParents

/- Static current source when the original finalized ApplyQC is present in a
snapshot but no preceding pointer-WAL history was supplied. This only resolves
existing bytes and checks the current pointer; it does not advance/recover it. -/
section CertifiedCurrent
variable (sha : Bytes → Bytes) (policyRaw stateRaw : Bytes) (pointer : NativeCurrentPointer.State)

structure CertifiedCurrent where
  tree : NativePolicyCodec.Value
  policy : NativePolicyBytes.Policy
  policySource : NativePolicyBytes.decodePolicy policyRaw = some (tree,policy)
  state : NativeStateBytes.State
  stateSource : NativeStateBytes.decodeState stateRaw = some state
  sectionBound : NativeApplySection.Bound
  sectionSource : NativeApplySection.bindSection sha policy state = some sectionBound
  edge : NativeApplyLineage.Edge
  selected : sectionBound.certificates.find? (fun e => e.id == pointer.qc) = some edge
  finalized : pointer.qc ∈ sectionBound.finalized
  values : NativeCurrentValues.Image
  valuesSource : NativeCurrentValues.load sha edge.decoded.candidate = some values
  pointerValid : NativeCurrentPointer.StateValid pointer
  checkpoint : pointer.checkpoint = edge.decoded.certificate.model
  optimizer : pointer.optimizer = edge.decoded.certificate.optimizer
  height : pointer.height = edge.decoded.certificate.context.height

def loadCertifiedCurrent : Option (CertifiedCurrent sha policyRaw stateRaw pointer) := do
  match policySource : NativePolicyBytes.decodePolicy policyRaw with
  | none => none
  | some (tree,policy) =>
    match stateSource : NativeStateBytes.decodeState stateRaw with
    | none => none
    | some state =>
      match sectionSource : NativeApplySection.bindSection sha policy state with
      | none => none
      | some sectionBound =>
        match selected : sectionBound.certificates.find? (fun e => e.id == pointer.qc) with
        | none => none
        | some edge =>
          if finalized : pointer.qc ∈ sectionBound.finalized then
            match valuesSource : NativeCurrentValues.load sha edge.decoded.candidate with
            | none => none
            | some values =>
              if checks : NativeCurrentPointer.StateValid pointer ∧
                  pointer.checkpoint = edge.decoded.certificate.model ∧
                  pointer.optimizer = edge.decoded.certificate.optimizer ∧
                  pointer.height = edge.decoded.certificate.context.height then
                some ⟨tree,policy,policySource,state,stateSource,sectionBound,sectionSource,edge,selected,
                  finalized,values,valuesSource,checks.1,checks.2.1,checks.2.2.1,checks.2.2.2⟩
              else none
          else none

variable {sha policyRaw stateRaw pointer} (current : CertifiedCurrent sha policyRaw stateRaw pointer)

def CertifiedCurrent.basis : FamilyInputs.CurrentBasis :=
  ⟨current.values,pointer,current.edge.decoded.candidate.context.schema⟩

theorem certifiedCurrentLoadFromComponents :
    loadCertifiedCurrent sha policyRaw stateRaw pointer = some current := by
  cases current with
  | mk tree policy policySource state stateSource sectionBound sectionSource edge selected finalized values valuesSource pointerValid checkpoint optimizer height =>
    unfold loadCertifiedCurrent
    split
    · rename_i absent; rw [policySource] at absent; contradiction
    · rename_i t p found
      cases Option.some.inj (found.symm.trans policySource)
      split
      · rename_i absent; rw [stateSource] at absent; contradiction
      · rename_i s found
        cases Option.some.inj (found.symm.trans stateSource)
        split
        · rename_i absent; rw [sectionSource] at absent; contradiction
        · rename_i sectionResult found
          cases Option.some.inj (found.symm.trans sectionSource)
          split
          · rename_i absent; rw [selected] at absent; contradiction
          · rename_i e found
            cases Option.some.inj (found.symm.trans selected)
            rw [dif_pos finalized]
            split
            · rename_i absent; rw [valuesSource] at absent; contradiction
            · rename_i v found
              cases Option.some.inj (found.symm.trans valuesSource)
              rw [dif_pos (And.intro pointerValid (And.intro checkpoint (And.intro optimizer height)))]

theorem certifiedCurrentOriginalId : current.edge.id = pointer.qc := by
  simpa using List.find?_some current.selected

theorem certifiedCurrentValuePreimages :
    current.edge.decoded.candidate.modelValues = NativeApplyResult.decimalValues current.values.model ∧
    current.edge.decoded.candidate.optimizerValues = NativeApplyResult.decimalValues current.values.optimizer :=
  NativeCurrentValues.originalPreimages current.valuesSource

theorem certifiedCurrentHashes :
    pointer.checkpoint = idBytes current.values.modelHash ∧
    pointer.optimizer = idBytes current.values.optimizerHash := by
  have checked := NativeApplySection.certificateChecked current.sectionSource (List.mem_of_find?_eq_some current.selected)
  have fields := NativeApplyLineage.certifiedFields checked
  have values := (NativeCurrentValues.loaded current.valuesSource).checked
  exact ⟨current.checkpoint.trans (fields.2.2.1.trans values.2.2.2.2.2.1),
    current.optimizer.trans (fields.2.2.2.trans values.2.2.2.2.2.2)⟩

theorem certifiedCurrentBounds : FamilyInputs.CurrentValues.Bounded current.basis.values :=
  FamilyInputs.currentValuesFromNative current.valuesSource

theorem certifiedCurrentOriginalPayload :
    current.edge.source = NativeApplyLineage.original .finalized current.edge.decoded ∧
    NativeApplyCertificate.candidateId sha current.edge.decoded.candidate = some current.edge.decoded.candidateId :=
  NativeApplyLineage.originalPayload
    (NativeApplySection.certificateChecked current.sectionSource (List.mem_of_find?_eq_some current.selected))

theorem certifiedCurrentEntireLists :
    current.sectionBound.profiles.map NativeApplyProfile.Checked.source = current.sectionBound.profileTrees ∧
    current.sectionBound.bodies.map NativeApplyLineage.Edge.source = current.sectionBound.bodyTrees ∧
    current.sectionBound.certificates.map NativeApplyLineage.Edge.source = current.sectionBound.certificateTrees :=
  NativeApplySection.originalLists current.sectionSource

theorem certifiedCurrentRejectsDifferentValues {otherModel otherOptimizer : List Int}
    (modelRead : NativeCurrentValues.readValues current.edge.decoded.candidate.modelValues = some otherModel)
    (optimizerRead : NativeCurrentValues.readValues current.edge.decoded.candidate.optimizerValues = some otherOptimizer) :
    otherModel = current.values.model ∧ otherOptimizer = current.values.optimizer := by
  have source := NativeCurrentValues.loaded current.valuesSource
  exact ⟨Option.some.inj (modelRead.symm.trans source.model),
    Option.some.inj (optimizerRead.symm.trans source.optimizer)⟩

theorem certifiedCurrentRejectsUnfinalized
    (missing : pointer.qc ∉ current.sectionBound.finalized) : False := missing current.finalized

theorem certifiedCurrentRejectsMissingQc
    (missing : current.sectionBound.certificates.find? (fun e => e.id == pointer.qc) = none) : False := by
  rw [current.selected] at missing
  contradiction

theorem certifiedCurrentSameActorPolicy {mapping actors}
    (actorNames : PolicyActors mapping actors policyRaw) : actorNames.policy = current.policy :=
  congrArg Prod.snd (Option.some.inj (actorNames.decoded.symm.trans current.policySource))

theorem certifiedCurrentSignerQuorum {mapping actors exposed}
    (actorNames : PolicyActors mapping actors policyRaw)
    (signers : SignerImage actorNames current.edge.decoded.certificate.signers exposed) :
    current.edge.decoded.certificate.threshold = 2*((actors.length-1)/3)+1 ∧
    current.edge.decoded.certificate.threshold ≤ exposed.length ∧
    exposed.Nodup ∧
    (∀ signer ∈ current.edge.decoded.certificate.signers,
      ∃ actor ∈ exposed, actorBytes mapping actor = some signer) := by
  have checked := NativeApplySection.certificateChecked current.sectionSource
    (List.mem_of_find?_eq_some current.selected)
  have valid := (NativeApplyLineage.checkedSource checked).certificateValid
  rcases valid with ⟨_,_,_,_,_,_,_,_,_,quorum⟩
  have samePolicy := certifiedCurrentSameActorPolicy current actorNames
  have count := actorsExactCount actorNames.names
  rw [samePolicy] at count
  have threshold : current.edge.decoded.certificate.threshold = NativeIscCertificate.quorum current.policy.validators :=
    quorum.2.2.1
  refine ⟨?_,?_,signers.names.publicUnique,?_⟩
  · rw [threshold,NativeIscCertificate.quorum,count]
  · rw [actorsExactCount signers.names]; exact quorum.2.2.2.1
  · intro signer member; exact originalHasActor signers.names member

end CertifiedCurrent

section SnapshotProjection
variable (sha : Bytes → Bytes) (mapping : IdentityMap) (actors : List Value)
    (artifacts : Artifacts) (units : NativeStateProjection.UnitSource)
    (currentPolicy currentState : Bytes) (pointer : NativeCurrentPointer.State)
    (wal : Bytes) (facts : NativeConfigAdmission.RuntimeFacts) (indices : List Nat)
    (vocabulary : Vocabulary) (configured : List Ticket) (names : Bytes → Option String)
    {earlyTrust planningTrust} (metadata : PublicPlanningBody.Metadata earlyTrust planningTrust)
    (shardAliases : Bytes → Option String) (checkpointNames : Value → Option Bytes) (expected : Value)

structure SnapshotProjection where
  current : CertifiedCurrent sha currentPolicy currentState pointer
  stored : StoredProjection sha mapping actors artifacts units current.basis wal facts indices
    vocabulary configured names metadata shardAliases checkpointNames expected

def loadSnapshotProjection : Option (SnapshotProjection sha mapping actors artifacts units currentPolicy currentState
    pointer wal facts indices vocabulary configured names metadata shardAliases checkpointNames expected) := do
  let current ← loadCertifiedCurrent sha currentPolicy currentState pointer
  let stored ← loadStoredProjection sha mapping actors artifacts units current.basis wal facts indices
    vocabulary configured names metadata shardAliases checkpointNames expected
  some ⟨current,stored⟩

variable {sha mapping actors artifacts units currentPolicy currentState pointer wal facts indices vocabulary configured
    names metadata shardAliases checkpointNames expected}
    (snapshot : SnapshotProjection sha mapping actors artifacts units currentPolicy currentState pointer wal facts indices
      vocabulary configured names (earlyTrust := earlyTrust) (planningTrust := planningTrust) metadata
      shardAliases checkpointNames expected)

theorem snapshotCurrentLinksOriginalQc :
    snapshot.current.edge.id = pointer.qc ∧ pointer.qc ∈ snapshot.current.sectionBound.finalized ∧
    pointer.checkpoint = idBytes snapshot.current.values.modelHash ∧
    pointer.optimizer = idBytes snapshot.current.values.optimizerHash ∧
    (NativeVectorAuthority.state snapshot.stored.source.bound).wire.parent = pointer.checkpoint :=
  ⟨certifiedCurrentOriginalId snapshot.current,snapshot.current.finalized,
    (certifiedCurrentHashes snapshot.current).1,(certifiedCurrentHashes snapshot.current).2,
    snapshot.stored.source.numeric.checked.1.2.1.symm⟩

theorem snapshotCurrentFeedsOwnInput :
    FamilyInputs.readOriginalImage snapshot.stored.source.bound indices snapshot.stored.source.numeric.profile.profile
      snapshot.stored.source.numeric.quantum snapshot.current.basis.values = some snapshot.stored.authority.input.image ∧
    pointer.height < (NativeVectorAuthority.state snapshot.stored.source.bound).height :=
  ⟨snapshot.stored.authority.input.computed,snapshot.stored.source.numeric.checked.1.2.2.1⟩

theorem snapshotSelectorsShareCurrent {otherIndices}
    (other : SnapshotProjection sha mapping actors artifacts units currentPolicy currentState pointer wal facts
      otherIndices vocabulary configured names metadata shardAliases checkpointNames expected) :
    snapshot.current = other.current ∧ snapshot.stored.source.bound = other.stored.source.bound := by
  have current := Option.some.inj ((certifiedCurrentLoadFromComponents snapshot.current).symm.trans
    (certifiedCurrentLoadFromComponents other.current))
  exact ⟨current,Option.some.inj (snapshot.stored.source.prepared.symm.trans other.stored.source.prepared)⟩

theorem snapshotOriginalVoteAndCurrent :
    snapshot.stored.observation.vote.wire.bodyHash = snapshot.stored.view.body.originalId ∧
    actorBytes mapping snapshot.stored.view.projectedVote.actor = some snapshot.stored.observation.vote.wire.validator ∧
    snapshot.stored.observation.entry.sequence = facts.expectedSequence ∧
    snapshot.current.edge.id = pointer.qc :=
  ⟨(storedOriginalVoteIdentity snapshot.stored).1,(storedOriginalVoteIdentity snapshot.stored).2.1,
    (storedOriginalVoteIdentity snapshot.stored).2.2.1,certifiedCurrentOriginalId snapshot.current⟩

end SnapshotProjection

/- Exact static collection correspondence for the migrated PARAMETER/ROOT/APPLY
constructors and the existing early/planning/failure projectors. Source packets
are original per-record artifacts, never supplied public bodies. Unsupported
payloads fail; they are not skipped or treated as empty collections. The existing
failure projector still only constructs empty-downstream ABORT bodies; it is
not promoted into a universal ABORT gate or a claim of complete R2 coverage. -/
structure FailureNames where
  trust : PublicFailureBody.Trust
  checkpoint : NativeFailurePayload.AbortBody → Option String
  authentic : ∀ body name, checkpoint body = some name → trust.checkpoint body name

def FailureNames.metadata {earlyTrust} (names : FailureNames) (early : PublicEarlyBody.Metadata earlyTrust) :
    PublicFailureBody.Metadata earlyTrust names.trust := ⟨early,names.checkpoint,names.authentic⟩

structure JournalInput where
  artifacts : Artifacts
  current : FamilyInputs.CurrentBasis
  facts : NativeConfigAdmission.RuntimeFacts
  failureNames : Option FailureNames
  failureLimits : PublicFailureBody.Limits

section OrdinaryStored
variable (sha : Bytes → Bytes) (input : JournalInput) (raw : Bytes)

structure OrdinaryObservation where
  entry : NativeWalBytes.Entry
  decoded : NativeWalBytes.decode sha raw = some entry
  loaded : NativeEarlySource.Loaded sha input.artifacts.policy input.artifacts.state entry.command input.facts
  id : Bytes
  hashed : NativeVoteBytes.voteId sha entry.command = some id
  valid : NativeReceiptBytes.Valid (receiptForWal entry loaded.original.vote loaded.original.admitted id)
  link : NativeWalBytes.ReceiptLink sha input.artifacts.policy entry
    (receiptForWal entry loaded.original.vote loaded.original.admitted id)
  voteLink : NativeVoteBytes.ReceiptLinked sha
    (receiptForWal entry loaded.original.vote loaded.original.admitted id) loaded.original.vote

def loadOrdinaryObservation : Option (OrdinaryObservation sha input raw) := do
  match decoded : NativeWalBytes.decode sha raw with
  | none => none
  | some entry =>
    let loaded ← NativeEarlySource.load sha input.artifacts.policy input.artifacts.state entry.command input.facts
    match hashed : NativeVoteBytes.voteId sha entry.command with
    | none => none
    | some id =>
      if checks : NativeReceiptBytes.Valid (receiptForWal entry loaded.original.vote loaded.original.admitted id) ∧
          NativeWalBytes.ReceiptLink sha input.artifacts.policy entry
            (receiptForWal entry loaded.original.vote loaded.original.admitted id) ∧
          NativeVoteBytes.ReceiptLinked sha
            (receiptForWal entry loaded.original.vote loaded.original.admitted id) loaded.original.vote then
        some ⟨entry,decoded,loaded,id,hashed,checks.1,checks.2.1,checks.2.2⟩
      else none

variable {sha input raw} (observation : OrdinaryObservation sha input raw)

def OrdinaryObservation.receipt : NativeReceiptBytes.Receipt :=
  receiptForWal observation.entry observation.loaded.original.vote observation.loaded.original.admitted observation.id

theorem ordinaryOriginalWalBinding :
    NativeWalBytes.bindReceipt sha input.artifacts.policy raw (NativeReceiptBytes.encode observation.receipt) =
      some (observation.entry,observation.receipt,observation.loaded.original.vote) :=
  NativeWalBytes.bindFromComponents sha input.artifacts.policy raw (NativeReceiptBytes.encode observation.receipt)
    observation.entry observation.receipt observation.loaded.original.vote observation.decoded
    (NativeVoteBytes.receiptFromComponents sha observation.receipt observation.loaded.original.vote observation.valid
      (NativeVoteBytes.bindingFromComponents sha observation.receipt observation.loaded.original.vote
        (NativeEarlySource.loadedOriginal observation.loaded).vote observation.voteLink)) observation.link

theorem ordinaryOriginalSequence : observation.entry.sequence = input.facts.expectedSequence := by
  have bytes := NativeWalBytes.boundOriginalBytes sha input.artifacts.policy raw (NativeReceiptBytes.encode observation.receipt)
    observation.entry observation.receipt observation.loaded.original.vote (ordinaryOriginalWalBinding observation)
  exact bytes.2.2.2.trans (NativeEarlySource.loadedIdentity observation.loaded).2.2.2.2.2.2.2.2

variable {earlyTrust planningTrust} (metadata : PublicPlanningBody.Metadata earlyTrust planningTrust)

inductive OrdinaryBody where
  | early (image : PublicEarlyBody.Image sha observation.loaded.original metadata.early)
      (computed : PublicEarlyBody.project sha observation.loaded.original metadata.early = some image)
      (separated : image.Separated)
  | planning (image : PublicPlanningBody.Image observation.loaded.original metadata)
      (computed : PublicPlanningBody.project observation.loaded.original metadata = some image)
      (separated : image.Separated)
  | failure (names : FailureNames) (originalNames : input.failureNames = some names)
      (image : PublicFailureBody.Image sha observation.loaded.original (names.metadata metadata.early) input.failureLimits)
      (computed : PublicFailureBody.project sha observation.loaded.original (names.metadata metadata.early)
        input.failureLimits = some image)
      (separated : image.Separated)
      (configured : PublicFailureBody.ConfigurationFits input.failureLimits observation.loaded.original)

def loadOrdinaryBody : Option (OrdinaryBody observation metadata) :=
  match computed : PublicEarlyBody.project sha observation.loaded.original metadata.early with
  | some image => if separated : image.Separated then some (.early image computed separated) else none
  | none =>
    match computed : PublicPlanningBody.project observation.loaded.original metadata with
    | some image => if separated : image.Separated then some (.planning image computed separated) else none
    | none =>
      match originalNames : input.failureNames with
      | none => none
      | some names =>
        match computed : PublicFailureBody.project sha observation.loaded.original (names.metadata metadata.early)
            input.failureLimits with
        | none => none
        | some image =>
          if checks : image.Separated ∧ PublicFailureBody.ConfigurationFits input.failureLimits observation.loaded.original then
            some (.failure names originalNames image computed checks.1 checks.2)
          else none

variable {observation metadata}

def OrdinaryBody.vote : OrdinaryBody observation metadata → Vote
  | .early image .. => image.vote
  | .planning image .. => image.vote
  | .failure _ _ image .. => image.vote

def OrdinaryBody.header : OrdinaryBody observation metadata → PublicEarlyBody.Header metadata.early observation.loaded.original
  | .early (.config _ header) .. => header
  | .early (.isc _ body) .. => body.header
  | .planning (.ec _ body) .. => body.parent.header
  | .planning (.apc _ body) .. => body.ec.parent.header
  | .failure _ _ (.view _ body) .. => body.header
  | .failure _ _ (.abort _ body) .. => body.header

theorem ordinaryBodyActor (body : OrdinaryBody observation metadata) : body.vote.actor = body.header.actor.value := by
  cases body with
  | early image _ _ => cases image <;> rfl
  | planning image _ _ => cases image <;> rfl
  | failure _ _ image _ _ _ => cases image <;> rfl

variable (mapping : IdentityMap) (actors : List Value) (names : Bytes → Option String)
    (vocabulary : Vocabulary) (metadata : PublicPlanningBody.Metadata earlyTrust planningTrust)
    (sha input raw)

def OrdinaryAliasChecks (observation : OrdinaryObservation sha input raw) (body : OrdinaryBody observation metadata) : Prop :=
  actorBytes mapping body.header.actor.value = some observation.loaded.original.vote.wire.validator ∧
  body.header.actor.value ∈ actors ∧
  mapping.height body.header.height.value = some observation.loaded.original.state.height ∧
  (mapping.epoch body.header.epoch.value).map asciiBytes = some observation.loaded.original.policy.epoch ∧
  names observation.loaded.original.policy.config = some body.header.config.text

instance (observation : OrdinaryObservation sha input raw) (body : OrdinaryBody observation metadata) :
    Decidable (OrdinaryAliasChecks (sha := sha) (input := input) (raw := raw) (mapping := mapping) (actors := actors) (names := names) (metadata := metadata) observation body) := by
  unfold OrdinaryAliasChecks; infer_instance

structure OrdinaryProjection where
  observation : OrdinaryObservation sha input raw
  committee : PolicyActors mapping actors input.artifacts.policy
  body : OrdinaryBody observation metadata
  aliases : OrdinaryAliasChecks (sha := sha) (input := input) (raw := raw) (mapping := mapping) (actors := actors) (names := names) (metadata := metadata) observation body
  canonical : PublicState.canonical vocabulary.models (.function (voteEntries body.vote)) = true

def loadOrdinaryProjection : Option (OrdinaryProjection (sha := sha) (input := input) (raw := raw) (mapping := mapping) (actors := actors) (names := names) (vocabulary := vocabulary) (metadata := metadata)) := do
  let observation ← loadOrdinaryObservation sha input raw
  let committee ← checkPolicyActors mapping actors input.artifacts.policy
  let body ← loadOrdinaryBody observation metadata
  if checked : OrdinaryAliasChecks (sha := sha) (input := input) (raw := raw) (mapping := mapping) (actors := actors) (names := names) (metadata := metadata) observation body ∧
      PublicState.canonical vocabulary.models (.function (voteEntries body.vote)) = true then
    some ⟨observation,committee,body,checked.1,checked.2⟩
  else none

variable {mapping actors names vocabulary metadata sha input raw}
    (ordinary : OrdinaryProjection (sha := sha) (input := input) (raw := raw) (mapping := mapping) (actors := actors) (names := names) (vocabulary := vocabulary) (metadata := metadata))

theorem ordinaryOriginalActor : actorBytes mapping ordinary.body.vote.actor =
    some ordinary.observation.loaded.original.vote.wire.validator := by
  rw [ordinaryBodyActor]; exact ordinary.aliases.1

theorem ordinaryNoSignerInflation {other : Value} (member : other ∈ actors)
    (same : actorBytes mapping other = some ordinary.observation.loaded.original.vote.wire.validator) :
    other = ordinary.body.vote.actor := by
  apply actorAliasesInjective ordinary.committee.names member
  · rw [ordinaryBodyActor]; exact ordinary.aliases.2.1
  · exact same
  · exact ordinaryOriginalActor ordinary

end OrdinaryStored

section MixedVoteRows
variable (sha : Bytes → Bytes) (mapping : IdentityMap) (actors : List Value)
    (units : NativeStateProjection.UnitSource) (indices : List Nat)
    (vocabulary : Vocabulary) (configured : List Ticket) (names : Bytes → Option String)
    {earlyTrust planningTrust} (metadata : PublicPlanningBody.Metadata earlyTrust planningTrust)
    (shardAliases : Bytes → Option String) (checkpointNames : Value → Option Bytes) (expected : Value)

inductive JournalProjection (input : JournalInput) (raw : Bytes) where
  | arithmetic (stored : StoredProjection sha mapping actors input.artifacts units input.current raw input.facts indices
      vocabulary configured names metadata shardAliases checkpointNames expected)
  | root (stored : RootProjection sha mapping actors input.artifacts units input.current raw input.facts indices
      vocabulary configured names metadata shardAliases checkpointNames)
  | ordinary (stored : OrdinaryProjection (sha := sha) (input := input) (raw := raw) (mapping := mapping) (actors := actors) (names := names) (vocabulary := vocabulary) (metadata := metadata))

def loadJournalProjection (input : JournalInput) (raw : Bytes) :
    Option (JournalProjection sha mapping actors units indices vocabulary configured names metadata
      shardAliases checkpointNames expected input raw) :=
  match loadStoredProjection sha mapping actors input.artifacts units input.current raw input.facts indices
      vocabulary configured names metadata shardAliases checkpointNames expected with
  | some stored => some (.arithmetic stored)
  | none => do
    match loadRootProjection sha mapping actors input.artifacts units input.current raw input.facts indices
        vocabulary configured names metadata shardAliases checkpointNames with
    | some stored => some (.root stored)
    | none => do
      let stored ← loadOrdinaryProjection (sha := sha) (input := input) (raw := raw) (mapping := mapping) (actors := actors) (names := names) (vocabulary := vocabulary) (metadata := metadata)
      some (.ordinary stored)

variable {sha mapping actors units indices vocabulary configured names metadata shardAliases checkpointNames expected}

def JournalProjection.entry {input raw} :
    JournalProjection sha mapping actors units indices vocabulary configured names metadata
      shardAliases checkpointNames expected input raw → NativeWalBytes.Entry
  | .arithmetic stored => stored.observation.entry
  | .root stored => stored.observation.entry
  | .ordinary stored => stored.observation.entry

def JournalProjection.vote {input raw} :
    JournalProjection sha mapping actors units indices vocabulary configured names metadata
      shardAliases checkpointNames expected input raw → Vote
  | .arithmetic stored => stored.view.projectedVote
  | .root stored => stored.view.projectedVote
  | .ordinary stored => stored.body.vote

def JournalProjection.nativeVote {input raw} :
    JournalProjection sha mapping actors units indices vocabulary configured names metadata
      shardAliases checkpointNames expected input raw → NativeVoteBytes.Vote
  | .arithmetic stored => stored.observation.vote
  | .root stored => stored.observation.loaded.original.vote
  | .ordinary stored => stored.observation.loaded.original.vote

def JournalProjection.configAlias {input raw} :
    JournalProjection sha mapping actors units indices vocabulary configured names metadata
      shardAliases checkpointNames expected input raw → Bytes × Value
  | .arithmetic stored => ((NativeVectorAuthority.policy stored.source.bound).config,
      stored.authority.parents.ec.parent.header.config.value)
  | .root stored => ((NativeVectorAuthority.policy stored.source.bound).config,
      stored.authority.parents.ec.parent.header.config.value)
  | .ordinary stored => (stored.observation.loaded.original.policy.config,stored.body.header.config.value)

theorem journalConfigFromOriginalName {input raw}
    (row : JournalProjection sha mapping actors units indices vocabulary configured names metadata
      shardAliases checkpointNames expected input raw) :
    ∃ name, names row.configAlias.1 = some name ∧ row.configAlias.2 = .model name := by
  cases row with
  | arithmetic stored => exact ⟨_,stored.view.aliases.2.2.2.2.1,rfl⟩
  | root stored => exact ⟨_,stored.view.aliases.2.2.2.2.1,rfl⟩
  | ordinary stored => exact ⟨_,stored.aliases.2.2.2.2,rfl⟩

theorem journalSameConfigHasSamePublicName {leftInput leftRaw rightInput rightRaw}
    (left : JournalProjection sha mapping actors units indices vocabulary configured names metadata
      shardAliases checkpointNames expected leftInput leftRaw)
    (right : JournalProjection sha mapping actors units indices vocabulary configured names metadata
      shardAliases checkpointNames expected rightInput rightRaw)
    (same : left.configAlias.1 = right.configAlias.1) : left.configAlias.2 = right.configAlias.2 := by
  obtain ⟨a,ha,va⟩ := journalConfigFromOriginalName left
  obtain ⟨b,hb,vb⟩ := journalConfigFromOriginalName right
  have namesEqual := Option.some.inj (ha.symm.trans ((congrArg names same).trans hb))
  exact va.trans ((congrArg Value.model namesEqual).trans vb.symm)

theorem journalProjectionActorAndCanonical {input raw}
    (row : JournalProjection sha mapping actors units indices vocabulary configured names metadata
      shardAliases checkpointNames expected input raw) :
    actorBytes mapping row.vote.actor = some row.nativeVote.wire.validator ∧
    PublicState.canonical vocabulary.models (.function (voteEntries row.vote)) = true := by
  cases row with
  | arithmetic stored => exact ⟨(storedOriginalVoteIdentity stored).2.1,stored.view.canonical⟩
  | root stored => exact ⟨(rootViewKeepsWholeOriginals stored.view).2.2.1,stored.view.canonical⟩
  | ordinary stored => exact ⟨ordinaryOriginalActor stored,stored.canonical⟩

theorem journalProjectionOriginal {input raw}
    (row : JournalProjection sha mapping actors units indices vocabulary configured names metadata
      shardAliases checkpointNames expected input raw) :
    NativeWalBytes.decode sha raw = some row.entry ∧ row.entry.kind = 2 ∧
    row.entry.sequence = input.facts.expectedSequence := by
  cases row with
  | arithmetic stored =>
    exact ⟨stored.observation.decoded,stored.observation.link.1,(storedOriginalVoteIdentity stored).2.2.1⟩
  | root stored =>
    exact ⟨stored.observation.decoded,stored.observation.link.1,(rootOriginalBytes stored.observation).2.2⟩
  | ordinary stored =>
    exact ⟨stored.observation.decoded,stored.observation.link.1,ordinaryOriginalSequence stored.observation⟩

structure JournalRow where
  piece : NativeWalScan.Piece
  input : JournalInput
  projection : JournalProjection sha mapping actors units indices vocabulary configured names metadata
    shardAliases checkpointNames expected input piece.bytes
  original : projection.entry = piece.entry

variable (sha mapping actors units indices vocabulary configured names metadata shardAliases checkpointNames expected)

def loadJournalRow (piece : NativeWalScan.Piece) (input : JournalInput) :
    Option (JournalRow (sha := sha) (mapping := mapping) (actors := actors) (units := units) (indices := indices)
      (vocabulary := vocabulary) (configured := configured) (names := names) (metadata := metadata)
      (shardAliases := shardAliases) (checkpointNames := checkpointNames) (expected := expected)) := do
  let projection ← loadJournalProjection sha mapping actors units indices vocabulary configured names metadata
    shardAliases checkpointNames expected input piece.bytes
  if original : projection.entry = piece.entry then some ⟨piece,input,projection,original⟩ else none

def loadJournalRows : List NativeWalScan.Piece → List JournalInput →
    Option (List (JournalRow (sha := sha) (mapping := mapping) (actors := actors) (units := units) (indices := indices)
      (vocabulary := vocabulary) (configured := configured) (names := names) (metadata := metadata)
      (shardAliases := shardAliases) (checkpointNames := checkpointNames) (expected := expected)))
  | [],[] => some []
  | [],_::_ => none
  | piece::pieces,inputs =>
    if piece.entry.kind = 1 then
      loadJournalRows pieces inputs
    else match inputs with
      | [] => none
      | input::inputs => do
        let row ← loadJournalRow sha mapping actors units indices vocabulary configured names metadata
          shardAliases checkpointNames expected piece input
        let rest ← loadJournalRows pieces inputs
        some (row::rest)

variable {sha mapping actors units indices vocabulary configured names metadata shardAliases checkpointNames expected}

theorem journalRowLoaded {piece input row}
    (loaded : loadJournalRow sha mapping actors units indices vocabulary configured names metadata
      shardAliases checkpointNames expected piece input = some row) : row.piece = piece ∧ row.input = input := by
  unfold loadJournalRow at loaded
  simp only [bind,Option.bind_eq_some_iff] at loaded
  obtain ⟨projection,_,last⟩ := loaded
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨rfl,rfl⟩

theorem journalRowsEntireOriginals {pieces inputs rows}
    (loaded : loadJournalRows sha mapping actors units indices vocabulary configured names metadata
      shardAliases checkpointNames expected pieces inputs = some rows) :
    rows.map JournalRow.piece = pieces.filter (fun piece => piece.entry.kind != 1) ∧
    rows.map JournalRow.input = inputs := by
  induction pieces generalizing inputs rows with
  | nil =>
    cases inputs <;> simp [loadJournalRows] at loaded
    subst rows; exact ⟨rfl,rfl⟩
  | cons piece pieces ih =>
    unfold loadJournalRows at loaded
    split at loaded
    · rename_i command
      have tail := ih loaded
      simpa only [List.filter_cons,command,bne_self_eq_false,Bool.false_eq_true,if_false] using tail
    · rename_i notCommand
      cases inputs with
      | nil => contradiction
      | cons input inputs =>
        simp only [bind,Option.bind_eq_some_iff] at loaded
        obtain ⟨row,hr,rest,ht,last⟩ := loaded
        cases Option.some.inj last
        have first := journalRowLoaded hr
        have tail := ih ht
        constructor
        · simp only [List.map_cons,first.1,tail.1,List.filter_cons,bne_iff_ne.mpr notCommand,if_true]
        · simp only [List.map_cons,first.2,tail.2]

theorem journalRowsNoExtraSource {pieces inputs rows}
    (loaded : loadJournalRows sha mapping actors units indices vocabulary configured names metadata
      shardAliases checkpointNames expected pieces inputs = some rows) :
    rows.length = inputs.length ∧ rows.length = (pieces.filter (fun piece => piece.entry.kind != 1)).length := by
  have exacts := journalRowsEntireOriginals loaded
  exact ⟨by simpa using congrArg List.length exacts.2,by simpa using congrArg List.length exacts.1⟩

theorem journalRowsEveryNativeVote {pieces inputs rows piece}
    (loaded : loadJournalRows sha mapping actors units indices vocabulary configured names metadata
      shardAliases checkpointNames expected pieces inputs = some rows)
    (member : piece ∈ pieces) (vote : piece.entry.kind = 2) :
    ∃ row ∈ rows, row.piece = piece := by
  apply List.mem_map.mp
  rw [(journalRowsEntireOriginals loaded).1]
  exact List.mem_filter.mpr ⟨member,by simp [vote]⟩

theorem journalRowsEveryPublicVote {pieces inputs rows row}
    (loaded : loadJournalRows sha mapping actors units indices vocabulary configured names metadata
      shardAliases checkpointNames expected pieces inputs = some rows) (member : row ∈ rows) :
    row.piece ∈ pieces ∧ row.piece.entry.sequence = row.input.facts.expectedSequence ∧
    NativeWalBytes.decode sha row.piece.bytes = some row.piece.entry := by
  have original := journalProjectionOriginal row.projection
  rw [row.original] at original
  refine ⟨?_,original.2.2,original.1⟩
  apply List.mem_of_mem_filter
  rw [← (journalRowsEntireOriginals loaded).1]
  exact List.mem_map.mpr ⟨row,member,rfl⟩

def journalVotes (rows : List (JournalRow (sha := sha) (mapping := mapping) (actors := actors) (units := units)
    (indices := indices) (vocabulary := vocabulary) (configured := configured) (names := names)
    (metadata := metadata) (shardAliases := shardAliases) (checkpointNames := checkpointNames) (expected := expected))) :
    List Vote := rows.map (fun row => row.projection.vote)

variable (sha mapping actors units indices vocabulary configured names metadata shardAliases checkpointNames expected)
    (observation : Option Bytes) (inputs : List JournalInput) (actor : Value) (candidate : List Vote)

structure VoteCollection where
  raw : Bytes
  known : observation = some raw
  scan : NativeWalScan.Result
  scanned : NativeWalScan.check sha raw = some scan
  complete : scan.torn = false
  rows : List (JournalRow (sha := sha) (mapping := mapping) (actors := actors) (units := units)
    (indices := indices) (vocabulary := vocabulary) (configured := configured) (names := names)
    (metadata := metadata) (shardAliases := shardAliases) (checkpointNames := checkpointNames) (expected := expected))
  loaded : loadJournalRows sha mapping actors units indices vocabulary configured names metadata shardAliases
    checkpointNames expected scan.pieces inputs = some rows
  unique : (journalVotes rows).Nodup
  sameActor : ∀ vote ∈ journalVotes rows, vote.actor = actor
  exactVotes : candidate.Perm (journalVotes rows)

def loadVoteCollection : Option (VoteCollection sha mapping actors units indices vocabulary configured names
    metadata shardAliases checkpointNames expected observation inputs actor candidate) :=
  match observation with
  | none => none
  | some raw =>
    match scanned : NativeWalScan.check sha raw with
    | none => none
    | some scan =>
      if complete : scan.torn = false then
        match loaded : loadJournalRows sha mapping actors units indices vocabulary configured names metadata shardAliases
            checkpointNames expected scan.pieces inputs with
        | none => none
        | some rows =>
          if checked : (journalVotes rows).Nodup ∧ (∀ vote ∈ journalVotes rows, vote.actor = actor) ∧
              candidate.Perm (journalVotes rows) then
            some ⟨raw,rfl,scan,scanned,complete,rows,loaded,checked.1,checked.2.1,checked.2.2⟩
          else none
      else none

theorem unknownVoteCollectionRejects :
    loadVoteCollection sha mapping actors units indices vocabulary configured names metadata shardAliases
      checkpointNames expected none inputs actor candidate = none := rfl

variable {sha mapping actors units indices vocabulary configured names metadata shardAliases checkpointNames expected
  observation inputs actor candidate}
    (collection : VoteCollection sha mapping actors units indices vocabulary configured names metadata shardAliases
      checkpointNames expected observation inputs actor candidate)

theorem collectionExactOriginalRows :
    collection.rows.map JournalRow.piece = collection.scan.pieces.filter (fun piece => piece.entry.kind != 1) ∧
    collection.rows.map JournalRow.input = inputs := journalRowsEntireOriginals collection.loaded

theorem collectionNoMissingPublicVote {piece} (member : piece ∈ collection.scan.pieces)
    (vote : piece.entry.kind = 2) :
    ∃ row ∈ collection.rows, row.piece = piece ∧ row.projection.vote ∈ candidate := by
  obtain ⟨row,present,exactPiece⟩ := journalRowsEveryNativeVote collection.loaded member vote
  refine ⟨row,present,exactPiece,collection.exactVotes.mem_iff.mpr ?_⟩
  exact List.mem_map.mpr ⟨row,present,rfl⟩

theorem collectionNoExtraPublicVote {vote} (member : vote ∈ candidate) :
    ∃ row ∈ collection.rows, row.projection.vote = vote ∧ row.piece ∈ collection.scan.pieces ∧
      NativeWalBytes.decode sha row.piece.bytes = some row.piece.entry := by
  obtain ⟨row,present,exactVote⟩ := List.mem_map.mp (collection.exactVotes.mem_iff.mp member)
  have original := journalRowsEveryPublicVote collection.loaded present
  exact ⟨row,present,exactVote,original.1,original.2.2⟩

include collection in
theorem collectionNoDuplicatePublicVote : candidate.Nodup :=
  collection.exactVotes.symm.nodup collection.unique

include collection in
theorem collectionActorFromOriginal {vote} (member : vote ∈ candidate) : vote.actor = actor :=
  collection.sameActor vote (collection.exactVotes.mem_iff.mp member)

theorem collectionPhysicalSequenceRetained {row} (member : row ∈ collection.rows) :
    ∃ position, collection.scan.pieces[position]? = some row.piece ∧
      row.piece.entry.sequence = position + 1 ∧ row.input.facts.expectedSequence = position + 1 := by
  have original := journalRowsEveryPublicVote collection.loaded member
  obtain ⟨position,atPosition⟩ := List.mem_iff_getElem?.mp original.1
  have entry : (NativeWalScan.entries collection.scan)[position]? = some row.piece.entry := by
    simp only [NativeWalScan.entries,List.getElem?_map,atPosition,Option.map_some]
  have sequence := NativeWalScan.checkedPosition sha collection.raw collection.scan collection.scanned
    position row.piece.entry entry
  exact ⟨position,atPosition,by omega,by omega⟩

theorem collectionLogicalCountKeepsPhysicalPositions :
    candidate.length = (collection.scan.pieces.filter (fun piece => piece.entry.kind != 1)).length := by
  have count := (journalRowsNoExtraSource collection.loaded).2
  exact collection.exactVotes.length_eq.trans ((List.length_map ..).trans count)

theorem collectionWholeOriginalBytes : collection.raw = NativeWalScan.joined collection.scan.pieces := by
  have terminal := NativeWalScan.checkedTerminal sha collection.raw collection.scan collection.scanned
  simp only [collection.complete,Bool.false_eq_true,if_false] at terminal
  simpa only [terminal,List.append_nil] using
    NativeWalScan.checkedPartition sha collection.raw collection.scan collection.scanned

include collection in
theorem collectionCandidateCanonical {vote} (member : vote ∈ candidate) :
    PublicState.canonical vocabulary.models (.function (voteEntries vote)) = true := by
  obtain ⟨row,_,same,_,_⟩ := collectionNoExtraPublicVote collection member
  rw [← same]
  exact (journalProjectionActorAndCanonical row.projection).2

theorem collectionsUseSameOriginalRows {otherCandidate}
    (other : VoteCollection sha mapping actors units indices vocabulary configured names metadata shardAliases
      checkpointNames expected observation inputs actor otherCandidate) :
    collection.raw = other.raw ∧ collection.scan = other.scan ∧ collection.rows = other.rows := by
  have raw := Option.some.inj (collection.known.symm.trans other.known)
  have scan := Option.some.inj (collection.scanned.symm.trans
    ((congrArg (NativeWalScan.check sha) raw).trans other.scanned))
  have rows := Option.some.inj (collection.loaded.symm.trans
    ((congrArg (fun s : NativeWalScan.Result => loadJournalRows sha mapping actors units indices vocabulary configured
      names metadata shardAliases checkpointNames expected s.pieces inputs) scan).trans other.loaded))
  exact ⟨raw,scan,rows⟩

include collection in
theorem collectionRejectsDroppedExtraOrSubstituted {otherCandidate}
    (different : ¬ candidate.Perm otherCandidate)
    (other : VoteCollection sha mapping actors units indices vocabulary configured names metadata shardAliases
      checkpointNames expected observation inputs actor otherCandidate) : False := by
  have rows := (collectionsUseSameOriginalRows collection other).2.2
  have same := collection.exactVotes
  rw [rows] at same
  exact different (same.trans other.exactVotes.symm)

/- One observed stream per original actor. This binds the ENTIRE durableVotes
field, without assigning command positions to the public logical vote count.
Authentication of complete actor observations and the other static fields stays
in the same remaining R2.3 source/state boundary. -/
structure ActorPacket where
  actor : Value
  observation : Option Bytes
  inputs : List JournalInput

def votesOf (actor : Value) (votes : List Vote) : List Vote := votes.filter (fun vote => vote.actor == actor)

structure ActorVotes (votes : List Vote) where
  packet : ActorPacket
  collection : VoteCollection sha mapping actors units indices vocabulary configured names metadata shardAliases
    checkpointNames expected packet.observation packet.inputs packet.actor (votesOf packet.actor votes)

def observedConfigs {votes} (images : List (ActorVotes (sha := sha) (mapping := mapping) (actors := actors)
    (units := units) (indices := indices) (vocabulary := vocabulary) (configured := configured) (names := names)
    (metadata := metadata) (shardAliases := shardAliases) (checkpointNames := checkpointNames) (expected := expected) votes)) :
    List (Bytes × Value) := images.flatMap (fun image => image.collection.rows.map (fun row => row.projection.configAlias))

/- Only configuration identities share this namespace. There is no imposed
global injectivity across unrelated primitive-key categories or coordinates. -/
def ConfigNamesSeparated (pairs : List (Bytes × Value)) : Prop :=
  ∀ left ∈ pairs, ∀ right ∈ pairs, left.2 = right.2 → left.1 = right.1

instance (pairs : List (Bytes × Value)) : Decidable (ConfigNamesSeparated pairs) := by
  unfold ConfigNamesSeparated; infer_instance

theorem distinctConfigurationsCannotCollapse {pairs left right}
    (checked : ConfigNamesSeparated pairs) (first : left ∈ pairs) (second : right ∈ pairs)
    (different : left.1 ≠ right.1) : left.2 ≠ right.2 := fun same => different (checked left first right second same)

variable (sha mapping actors units indices vocabulary configured names metadata shardAliases checkpointNames expected)

def loadActorVotes (votes : List Vote) : List ActorPacket →
    Option (List (ActorVotes (sha := sha) (mapping := mapping) (actors := actors) (units := units) (indices := indices)
      (vocabulary := vocabulary) (configured := configured) (names := names) (metadata := metadata)
      (shardAliases := shardAliases) (checkpointNames := checkpointNames) (expected := expected) votes))
  | [] => some []
  | packet::packets => do
    let collection ← loadVoteCollection sha mapping actors units indices vocabulary configured names metadata shardAliases
      checkpointNames expected packet.observation packet.inputs packet.actor (votesOf packet.actor votes)
    let rest ← loadActorVotes votes packets
    some (⟨packet,collection⟩::rest)

variable {sha mapping actors units indices vocabulary configured names metadata shardAliases checkpointNames expected}

theorem actorVotesEntirePackets {votes packets images}
    (loaded : loadActorVotes sha mapping actors units indices vocabulary configured names metadata shardAliases
      checkpointNames expected votes packets = some images) : images.map ActorVotes.packet = packets := by
  induction packets generalizing images with
  | nil => cases Option.some.inj loaded; rfl
  | cons packet packets ih =>
    simp only [loadActorVotes,bind,Option.bind_eq_some_iff] at loaded
    obtain ⟨collection,_,rest,tail,last⟩ := loaded
    cases Option.some.inj last
    simp only [List.map_cons,ih tail]

variable (sha mapping actors units indices vocabulary configured names metadata shardAliases checkpointNames expected)
    (state : PublicState.State) (packets : List ActorPacket)

structure DurableVoteState where
  votes : List Vote
  fromState : PublicState.readVotes state = some votes
  inventory : packets.map ActorPacket.actor = actors
  distinctActors : actors.Nodup
  knownActors : ∀ vote ∈ votes, vote.actor ∈ actors
  unique : votes.Nodup
  sequences : ∀ actor ∈ actors, (state.read "durableSequence" >>= fun f => readFunction f actor) =
    some (.integer (votesOf actor votes).length)
  images : List (ActorVotes (sha := sha) (mapping := mapping) (actors := actors) (units := units) (indices := indices)
    (vocabulary := vocabulary) (configured := configured) (names := names) (metadata := metadata)
    (shardAliases := shardAliases) (checkpointNames := checkpointNames) (expected := expected) votes)
  loaded : loadActorVotes sha mapping actors units indices vocabulary configured names metadata shardAliases
    checkpointNames expected votes packets = some images
  configNames : ConfigNamesSeparated (observedConfigs images)

def loadDurableVoteState : Option (DurableVoteState sha mapping actors units indices vocabulary configured names metadata
    shardAliases checkpointNames expected state packets) :=
  match fromState : PublicState.readVotes state with
  | none => none
  | some votes =>
    if checked : packets.map ActorPacket.actor = actors ∧ actors.Nodup ∧ (∀ vote ∈ votes, vote.actor ∈ actors) ∧ votes.Nodup ∧
        (∀ actor ∈ actors, (state.read "durableSequence" >>= fun f => readFunction f actor) =
          some (.integer (votesOf actor votes).length)) then
      match loaded : loadActorVotes sha mapping actors units indices vocabulary configured names metadata shardAliases
          checkpointNames expected votes packets with
      | none => none
      | some images =>
        if configNames : ConfigNamesSeparated (observedConfigs images) then
          some ⟨votes,fromState,checked.1,checked.2.1,checked.2.2.1,checked.2.2.2.1,checked.2.2.2.2,images,loaded,configNames⟩
        else none
    else none

variable {sha mapping actors units indices vocabulary configured names metadata shardAliases checkpointNames expected state packets}
    (durable : DurableVoteState sha mapping actors units indices vocabulary configured names metadata shardAliases
      checkpointNames expected state packets)

theorem durableEntireActorInventory : durable.images.map (fun image => image.packet.actor) = actors := by
  have same := congrArg (List.map ActorPacket.actor) (actorVotesEntirePackets durable.loaded)
  simpa only [List.map_map,Function.comp_def] using same.trans durable.inventory

theorem durableEveryActorHasOriginalStream {actor} (member : actor ∈ actors) :
    ∃ image ∈ durable.images, image.packet.actor = actor ∧ image.packet.observation = some image.collection.raw := by
  rw [← durableEntireActorInventory durable] at member
  obtain ⟨image,present,same⟩ := List.mem_map.mp member
  exact ⟨image,present,same,image.collection.known⟩

theorem durableEveryPublicVoteHasOriginal {vote} (member : vote ∈ durable.votes) :
    ∃ image ∈ durable.images, ∃ row ∈ image.collection.rows,
      row.projection.vote = vote ∧ row.piece ∈ image.collection.scan.pieces ∧
      NativeWalBytes.decode sha row.piece.bytes = some row.piece.entry := by
  obtain ⟨image,present,actor,_⟩ := durableEveryActorHasOriginalStream durable (durable.knownActors vote member)
  have selected : vote ∈ votesOf image.packet.actor durable.votes := by
    apply List.mem_filter.mpr
    exact ⟨member,by simp only [actor,beq_self_eq_true]⟩
  obtain ⟨row,rowPresent,same,original,decoded⟩ := collectionNoExtraPublicVote image.collection selected
  exact ⟨image,present,row,rowPresent,same,original,decoded⟩

theorem durableEveryNativeVoteHasPublic {image} (present : image ∈ durable.images) {piece}
    (member : piece ∈ image.collection.scan.pieces) (vote : piece.entry.kind = 2) :
    image.packet ∈ packets ∧ ∃ row ∈ image.collection.rows, row.piece = piece ∧ row.projection.vote ∈ durable.votes := by
  obtain ⟨row,rowPresent,same,exposed⟩ := collectionNoMissingPublicVote image.collection member vote
  refine ⟨?_,row,rowPresent,same,(List.mem_filter.mp exposed).1⟩
  have mapped : image.packet ∈ durable.images.map ActorVotes.packet := List.mem_map.mpr ⟨image,present,rfl⟩
  simpa only [actorVotesEntirePackets durable.loaded] using mapped

theorem durableLogicalSequenceFromOriginalVotes {image} (present : image ∈ durable.images) :
    (state.read "durableSequence" >>= fun f => readFunction f image.packet.actor) =
      some (.integer image.collection.rows.length) := by
  have member : image.packet.actor ∈ durable.images.map (fun i => i.packet.actor) :=
    List.mem_map.mpr ⟨image,present,rfl⟩
  have actor : image.packet.actor ∈ actors := by simpa only [durableEntireActorInventory durable] using member
  have sequence := durable.sequences image.packet.actor actor
  have count := image.collection.exactVotes.length_eq
  simp only [journalVotes,List.length_map] at count
  simpa only [count] using sequence

theorem durableOriginalSourcePackets : durable.images.map ActorVotes.packet = packets :=
  actorVotesEntirePackets durable.loaded

theorem durableConfigNameIsUnambiguous {leftImage rightImage}
    (firstImage : leftImage ∈ durable.images) (secondImage : rightImage ∈ durable.images)
    {left right} (first : left ∈ leftImage.collection.rows) (second : right ∈ rightImage.collection.rows)
    (same : left.projection.configAlias.2 = right.projection.configAlias.2) :
    left.projection.configAlias.1 = right.projection.configAlias.1 := by
  apply durable.configNames _ ?_ _ ?_ same
  · exact List.mem_flatMap.mpr ⟨leftImage,firstImage,List.mem_map.mpr ⟨left,first,rfl⟩⟩
  · exact List.mem_flatMap.mpr ⟨rightImage,secondImage,List.mem_map.mpr ⟨right,second,rfl⟩⟩

theorem durableWholeStateSource {field} (known : field ∈ PublicState.fieldNames) :
    ∃ value, state.read field = some value := by
  obtain ⟨value,read,_⟩ := PublicState.everyFieldRetained state known
  exact ⟨value,read⟩

end MixedVoteRows

/- Static current-field identity. The initial checkpoint may be a separately
authenticated identifier; only an actual finalized APPLY source proves it is
the model hash. No structured public vector is coerced to a native content ID. -/
section CurrentField
variable (mapping : IdentityMap) (checkpointNames : Value → Option Bytes)
    (state : PublicState.State) (pointer : NativeCurrentPointer.State)

structure CurrentField where
  symbol : Value
  original : state.read "currentCheckpoint" = some symbol
  valid : NativeCurrentPointer.StateValid pointer
  mapped : (mapping.checkpoint symbol).map asciiBytes = some pointer.checkpoint
  shared : checkpointNames symbol = some pointer.checkpoint

def loadCurrentField : Option (CurrentField mapping checkpointNames state pointer) :=
  match original : state.read "currentCheckpoint" with
  | none => none
  | some symbol =>
    if checked : NativeCurrentPointer.StateValid pointer ∧
        (mapping.checkpoint symbol).map asciiBytes = some pointer.checkpoint ∧
        checkpointNames symbol = some pointer.checkpoint then
      some ⟨symbol,original,checked.1,checked.2.1,checked.2.2⟩ else none

variable {mapping checkpointNames state pointer} (field : CurrentField mapping checkpointNames state pointer)

theorem currentFieldComputed : loadCurrentField mapping checkpointNames state pointer = some field := by
  unfold loadCurrentField
  split
  · rename_i absent; rw [field.original] at absent; contradiction
  · rename_i symbol found
    cases Option.some.inj (found.symm.trans field.original)
    rw [dif_pos ⟨field.valid,field.mapped,field.shared⟩]

include field in
theorem currentFieldCannotChangeCheckpoint {otherPointer}
    (other : CurrentField mapping checkpointNames state otherPointer) : pointer.checkpoint = otherPointer.checkpoint := by
  have symbol := Option.some.inj (field.original.symm.trans other.original)
  exact Option.some.inj (field.shared.symm.trans ((congrArg checkpointNames symbol).trans other.shared))

theorem currentFieldRejectsConflictingNamespaces {native}
    (different : native ≠ pointer.checkpoint) (observed : checkpointNames field.symbol = some native) : False :=
  different (Option.some.inj (observed.symm.trans field.shared))

end CurrentField

section CurrentSourceField
variable {sha mapping actors artifacts units currentPolicy currentState pointer wal facts indices vocabulary configured names
    earlyTrust planningTrust} {metadata : PublicPlanningBody.Metadata earlyTrust planningTrust}
    {shardAliases checkpointNames expected}
    (snapshot : SnapshotProjection sha mapping actors artifacts units currentPolicy currentState pointer wal facts indices
      vocabulary configured names metadata shardAliases checkpointNames expected)
    (state : PublicState.State) (field : CurrentField mapping checkpointNames state pointer)

theorem snapshotBindsPublicCurrentToOriginalQc :
    state.read "currentCheckpoint" = some field.symbol ∧
    checkpointNames field.symbol = some (idBytes snapshot.current.values.modelHash) ∧
    snapshot.current.edge.id = pointer.qc ∧ pointer.optimizer = idBytes snapshot.current.values.optimizerHash := by
  have hashes := certifiedCurrentHashes snapshot.current
  exact ⟨field.original,field.shared.trans (congrArg some hashes.1),
    certifiedCurrentOriginalId snapshot.current,hashes.2⟩

theorem snapshotParentUsesPublicCurrent :
    checkpointNames field.symbol = some (NativeVectorAuthority.state snapshot.stored.source.bound).wire.parent :=
  field.shared.trans (congrArg some snapshot.stored.source.numeric.checked.1.2.1)

end CurrentSourceField

/- The current QC can have arrived from another validator without a local vote.
Its original parent bodies therefore read controls from the actual ISC context,
not from a fabricated NativeSelectedVote. This is part of the same static join. -/
section CertificateParents
variable {earlyTrust planningTrust} (metadata : PublicPlanningBody.Metadata earlyTrust planningTrust)
    (native : NativePlanLineage.Edge)

structure CertificateParents where
  height : PublicEarlyBody.Name metadata.early (.height native.ec.parent.certificate.body.context.height)
  epoch : PublicEarlyBody.Name metadata.early (.epoch native.ec.parent.certificate.body.context.epoch)
  config : PublicEarlyBody.Name metadata.early (.config native.ec.parent.certificate.body.context.config)
  policy : PublicAuthority.ClosePolicy
  policySelected : metadata.early.policy native.ec.parent.bodyId native.ec.parent.certificate.body = some policy
  entries : List (PublicEarlyBody.Entry metadata.early native.ec.parent.bodyId native.ec.parent.certificate.body)
  entriesComputed : PublicEarlyBody.loadEntries metadata.early native.ec.parent.bodyId
    native.ec.parent.certificate.body native.ec.parent.certificate.body.tuples = some entries
  seed : PublicPlanningBody.Name metadata (.seed native.ec.seed.id native.ec.seed.transcript)
  norm : PublicPlanningBody.Name metadata (.norm native.ec.norm.id native.ec.norm.evidence native.ec.certificate.common)
  ecMembers : List (PublicPlanningBody.Member metadata.early native.ec.parent.certificate.body.context)
  ecComputed : PublicPlanningBody.loadMembers metadata.early native.ec.parent.certificate.body.context
    (NativePlan.acceptedTickets native.ec.certificate) = some ecMembers
  coefficient : PublicPlanningBody.Name metadata (.coefficient native.id native.certificate.common native.ec.certificate.common)
  planMembers : List (PublicPlanningBody.Member metadata.early native.ec.parent.certificate.body.context)
  planComputed : PublicPlanningBody.loadMembers metadata.early native.ec.parent.certificate.body.context
    (native.certificate.common.weights.map NativePlan.Weight.ticket) = some planMembers
  parents : PublicPlanningBody.SamePlanParents native
  members : planMembers.map PublicPlanningBody.Member.value = ecMembers.map PublicPlanningBody.Member.value

def loadCertificateParents : Option (CertificateParents metadata native) := do
  let height ← PublicEarlyBody.loadName metadata.early (.height native.ec.parent.certificate.body.context.height)
  let epoch ← PublicEarlyBody.loadName metadata.early (.epoch native.ec.parent.certificate.body.context.epoch)
  let config ← PublicEarlyBody.loadName metadata.early (.config native.ec.parent.certificate.body.context.config)
  match policySelected : metadata.early.policy native.ec.parent.bodyId native.ec.parent.certificate.body with
  | none => none
  | some policy =>
    match entriesComputed : PublicEarlyBody.loadEntries metadata.early native.ec.parent.bodyId
        native.ec.parent.certificate.body native.ec.parent.certificate.body.tuples with
    | none => none
    | some entries =>
      let seed ← PublicPlanningBody.loadName metadata (.seed native.ec.seed.id native.ec.seed.transcript)
      let norm ← PublicPlanningBody.loadName metadata (.norm native.ec.norm.id native.ec.norm.evidence native.ec.certificate.common)
      match ecComputed : PublicPlanningBody.loadMembers metadata.early native.ec.parent.certificate.body.context
          (NativePlan.acceptedTickets native.ec.certificate) with
      | none => none
      | some ecMembers =>
        let coefficient ← PublicPlanningBody.loadName metadata
          (.coefficient native.id native.certificate.common native.ec.certificate.common)
        match planComputed : PublicPlanningBody.loadMembers metadata.early native.ec.parent.certificate.body.context
            (native.certificate.common.weights.map NativePlan.Weight.ticket) with
        | none => none
        | some planMembers =>
          if checked : PublicPlanningBody.SamePlanParents native ∧
              planMembers.map PublicPlanningBody.Member.value = ecMembers.map PublicPlanningBody.Member.value then
            some ⟨height,epoch,config,policy,policySelected,entries,entriesComputed,seed,norm,ecMembers,ecComputed,
              coefficient,planMembers,planComputed,checked.1,checked.2⟩ else none

variable {metadata native} (p : CertificateParents metadata native)

theorem certificateParentsLoaded : loadCertificateParents metadata native = some p := by
  unfold loadCertificateParents
  rw [FamilyAuthority.originalEarlyNameLoaded p.height,FamilyAuthority.originalEarlyNameLoaded p.epoch,
    FamilyAuthority.originalEarlyNameLoaded p.config]
  simp only [bind,Option.bind]
  split
  · rename_i absent; rw [p.policySelected] at absent; contradiction
  · rename_i policy found
    cases Option.some.inj (found.symm.trans p.policySelected)
    split
    · rename_i absent; rw [p.entriesComputed] at absent; contradiction
    · rename_i entries found
      cases Option.some.inj (found.symm.trans p.entriesComputed)
      rw [FamilyAuthority.originalPlanningNameLoaded p.seed,FamilyAuthority.originalPlanningNameLoaded p.norm]
      dsimp only
      split
      · rename_i absent; rw [p.ecComputed] at absent; contradiction
      · rename_i members found
        cases Option.some.inj (found.symm.trans p.ecComputed)
        rw [FamilyAuthority.originalPlanningNameLoaded p.coefficient]
        dsimp only
        split
        · rename_i absent; rw [p.planComputed] at absent; contradiction
        · rename_i members found
          cases Option.some.inj (found.symm.trans p.planComputed)
          rw [dif_pos ⟨p.parents,p.members⟩]

def CertificateParents.isc : Value := PublicAuthority.iscValue
  (PublicAuthority.roundValue p.height.value p.epoch.value) p.config.value p.policy
  (PublicAuthority.setValue (p.entries.map PublicEarlyBody.Entry.value))
def CertificateParents.seedValue : Value := PublicAuthority.seedValue p.isc p.epoch.value p.seed.value
def CertificateParents.ec : Value := PublicAuthority.ecValue p.isc p.seedValue
  (PublicAuthority.setValue (p.ecMembers.map PublicPlanningBody.Member.value)) p.norm.value
def CertificateParents.apc : Value := PublicAuthority.apcValue p.isc p.seedValue p.ec
  (PublicAuthority.setValue (p.planMembers.map PublicPlanningBody.Member.value)) p.coefficient.value

theorem certificateParentsOriginalEntries :
    p.entries.map PublicEarlyBody.Entry.original = native.ec.parent.certificate.body.tuples :=
  PublicEarlyBody.entriesOriginal p.entriesComputed

theorem certificateParentsOriginalMembers :
    p.ecMembers.map PublicPlanningBody.Member.original = NativePlan.acceptedTickets native.ec.certificate ∧
    p.planMembers.map PublicPlanningBody.Member.original = native.certificate.common.weights.map NativePlan.Weight.ticket :=
  ⟨PublicPlanningBody.membersOriginal p.ecComputed,PublicPlanningBody.membersOriginal p.planComputed⟩

theorem certificateParentsNoLocalVotePremise {x : NativeSelectedVote.Checked}
    (old : PublicPlanningBody.ApcBody metadata x native)
    (height : x.state.height = native.ec.parent.certificate.body.context.height)
    (epoch : x.policy.epoch = native.ec.parent.certificate.body.context.epoch)
    (config : x.policy.config = native.ec.parent.certificate.body.context.config) :
    p.isc = old.ec.parent.value ∧ p.seedValue = old.ec.seedValue ∧ p.ec = old.ec.value ∧ p.apc = old.value := by
  have h : p.height.text = old.ec.parent.header.height.text := by
    apply Option.some.inj
    rw [← p.height.selected,← old.ec.parent.header.height.selected,height]
  have e : p.epoch.text = old.ec.parent.header.epoch.text := by
    apply Option.some.inj
    rw [← p.epoch.selected,← old.ec.parent.header.epoch.selected,epoch]
  have c : p.config.text = old.ec.parent.header.config.text := by
    apply Option.some.inj
    rw [← p.config.selected,← old.ec.parent.header.config.selected,config]
  have policy := Option.some.inj (p.policySelected.symm.trans old.ec.parent.policySelected)
  have entries := Option.some.inj (p.entriesComputed.symm.trans old.ec.parent.computed)
  have seed := Option.some.inj (p.seed.selected.symm.trans old.ec.seed.selected)
  have norm := Option.some.inj (p.norm.selected.symm.trans old.ec.norm.selected)
  have ecMembers := Option.some.inj (p.ecComputed.symm.trans old.ec.computed)
  have coefficient := Option.some.inj (p.coefficient.selected.symm.trans old.coefficient.selected)
  have planMembers := Option.some.inj (p.planComputed.symm.trans old.computed)
  have isc : p.isc = old.ec.parent.value := by
    simp only [CertificateParents.isc,PublicPlanningBody.IscBody.value,PublicEarlyBody.Header.round,
      PublicEarlyBody.Name.value,h,e,c,policy,entries]
  have seedValue : p.seedValue = old.ec.seedValue := by
    simp only [CertificateParents.seedValue,PublicPlanningBody.EcBody.seedValue,isc,
      PublicEarlyBody.Name.value,PublicPlanningBody.Name.value,e,seed]
  have ec : p.ec = old.ec.value := by
    simp only [CertificateParents.ec,PublicPlanningBody.EcBody.value,isc,seedValue,
      PublicPlanningBody.Name.value,ecMembers,norm]
  exact ⟨isc,seedValue,ec,by
    simp only [CertificateParents.apc,PublicPlanningBody.ApcBody.value,isc,seedValue,ec,
      PublicPlanningBody.Name.value,coefficient,planMembers]⟩

end CertificateParents

section CurrentCertificateParents
variable {sha policyRaw stateRaw pointer} (current : CertifiedCurrent sha policyRaw stateRaw pointer)
    {earlyTrust planningTrust} (metadata : PublicPlanningBody.Metadata earlyTrust planningTrust)

def loadCurrentCertificateParents : Option (CertificateParents metadata current.edge.root.plan) :=
  loadCertificateParents metadata current.edge.root.plan

variable {metadata} (parents : CertificateParents metadata current.edge.root.plan)

theorem currentCertificateParentIsOriginal :
    current.edge.root.plan ∈ current.sectionBound.roots.parameters.prior.plans.certificates := by
  have apply := NativeApplySection.certificateChecked current.sectionSource
    (List.mem_of_find?_eq_some current.selected)
  have root := NativeApplySection.selectedRoot current.sectionSource apply
  exact List.mem_of_find?_eq_some (NativeAggregateLineage.checkedSource root).plan

theorem currentCertificateParentControls :
    current.edge.root.plan.ec.parent.certificate.body.context.height = current.state.height ∧
    current.edge.root.plan.ec.parent.certificate.body.context.epoch = current.policy.epoch ∧
    current.edge.root.plan.ec.parent.certificate.body.context.config = current.policy.config := by
  have roots := (NativeApplySection.checkedSource current.sectionSource).roots
  have parameters := (NativeSizedParameterSection.checkedSource
    (NativeAggregateSection.checkedSource roots).parameters).1
  have plans := (NativeParameterSection.checkedSource parameters).plans
  have plan := NativePlanSection.certificateChecked plans (currentCertificateParentIsOriginal current)
  have ec := (NativePlanSection.checkedParents plans plan).2.1
  have isc := (NativeEligibilitySection.checkedParents (NativePlanSection.checkedSource plans).eligibility ec).1
  have context := isc.2.2.2.1.2.1.2.1
  exact ⟨congrArg NativeInputSetBody.Context.height context,congrArg NativeInputSetBody.Context.epoch context,
    congrArg NativeInputSetBody.Context.config context⟩

theorem currentCertificateParentsAgreeWithOriginalVote {vote facts}
    (loaded : NativeEarlySource.Loaded sha policyRaw stateRaw vote facts)
    (old : PublicPlanningBody.ApcBody metadata loaded.original current.edge.root.plan) :
    parents.isc = old.ec.parent.value ∧ parents.seedValue = old.ec.seedValue ∧
    parents.ec = old.ec.value ∧ parents.apc = old.value := by
  have original := NativeEarlySource.loadedOriginal loaded
  obtain ⟨_,policySource⟩ := original.policy
  have policy : loaded.original.policy = current.policy :=
    congrArg Prod.snd (Option.some.inj (policySource.symm.trans current.policySource))
  have state : loaded.original.state = current.state := Option.some.inj (original.state.symm.trans current.stateSource)
  have controls := currentCertificateParentControls current
  exact certificateParentsNoLocalVotePremise parents old
    ((congrArg NativeStateBytes.State.height state).trans controls.1.symm)
    ((congrArg NativePolicyBytes.Policy.epoch policy).trans controls.2.1.symm)
    ((congrArg NativePolicyBytes.Policy.config policy).trans controls.2.2.symm)

theorem currentCertificateRetainsRemoteParentSource :
    current.edge.id = pointer.qc ∧
    parents.entries.map PublicEarlyBody.Entry.original = current.edge.root.plan.ec.parent.certificate.body.tuples ∧
    parents.planMembers.map PublicPlanningBody.Member.original =
      current.edge.root.plan.certificate.common.weights.map NativePlan.Weight.ticket :=
  ⟨certifiedCurrentOriginalId current,certificateParentsOriginalEntries parents,
    (certificateParentsOriginalMembers parents).2⟩

theorem currentCertificateParentsComputed : loadCurrentCertificateParents current metadata = some parents :=
  certificateParentsLoaded parents

end CurrentCertificateParents

/- One checked static bundle for the fields already related above. The remaining
certificate/candidate/environment collections and initial applicability are not
inferred from this bundle. It adds no transition or recovery assertion. -/
section ObservedState
variable (sha : Bytes → Bytes) (mapping : IdentityMap) (actors : List Value)
    (units : NativeStateProjection.UnitSource) (indices : List Nat)
    (vocabulary : Vocabulary) (configured : List Ticket) (names : Bytes → Option String)
    {earlyTrust planningTrust} (metadata : PublicPlanningBody.Metadata earlyTrust planningTrust)
    (shardAliases : Bytes → Option String) (checkpointNames : Value → Option Bytes) (expected : Value)
    (state : PublicState.State) (packets : List ActorPacket)
    (policyRaw stateRaw : Bytes) (pointer : NativeCurrentPointer.State)

structure ObservedState where
  durable : DurableVoteState sha mapping actors units indices vocabulary configured names metadata
    shardAliases checkpointNames expected state packets
  current : CertifiedCurrent sha policyRaw stateRaw pointer
  actorPolicy : PolicyActors mapping actors policyRaw
  field : CurrentField mapping checkpointNames state pointer
  parents : CertificateParents metadata current.edge.root.plan
  configForward : names current.policy.config = some parents.config.text
  configInverse : ConfigNamesSeparated
    ((current.policy.config,parents.config.value)::observedConfigs durable.images)

def loadObservedState : Option (ObservedState sha mapping actors units indices vocabulary configured names metadata
    shardAliases checkpointNames expected state packets policyRaw stateRaw pointer) := do
  let durable ← loadDurableVoteState sha mapping actors units indices vocabulary configured names metadata
    shardAliases checkpointNames expected state packets
  let current ← loadCertifiedCurrent sha policyRaw stateRaw pointer
  let actorPolicy ← checkPolicyActors mapping actors policyRaw
  let field ← loadCurrentField mapping checkpointNames state pointer
  let parents ← loadCurrentCertificateParents current metadata
  if checked : names current.policy.config = some parents.config.text ∧
      ConfigNamesSeparated ((current.policy.config,parents.config.value)::observedConfigs durable.images) then
    some ⟨durable,current,actorPolicy,field,parents,checked.1,checked.2⟩
  else none

variable {sha mapping actors units indices vocabulary configured names metadata shardAliases checkpointNames expected
    state packets policyRaw stateRaw pointer}
    (joined : ObservedState sha mapping actors units indices vocabulary configured names metadata
      shardAliases checkpointNames expected state packets policyRaw stateRaw pointer)

theorem observedCurrentSameSource :
    state.read "currentCheckpoint" = some joined.field.symbol ∧
    checkpointNames joined.field.symbol = some (idBytes joined.current.values.modelHash) ∧
    joined.current.edge.id = pointer.qc ∧
    pointer.optimizer = idBytes joined.current.values.optimizerHash ∧
    joined.actorPolicy.policy = joined.current.policy := by
  have hashes := certifiedCurrentHashes joined.current
  exact ⟨joined.field.original,joined.field.shared.trans (congrArg some hashes.1),
    certifiedCurrentOriginalId joined.current,hashes.2,
    certifiedCurrentSameActorPolicy joined.current joined.actorPolicy⟩

theorem observedCurrentConfigCannotAliasJournal {image} (present : image ∈ joined.durable.images)
    {row} (member : row ∈ image.collection.rows)
    (same : joined.parents.config.value = row.projection.configAlias.2) :
    joined.current.policy.config = row.projection.configAlias.1 := by
  apply joined.configInverse _ (List.mem_cons_self ..) _ ?_ same
  apply List.mem_cons_of_mem
  exact List.mem_flatMap.mpr ⟨image,present,List.mem_map.mpr ⟨row,member,rfl⟩⟩

theorem observedCurrentConfigForwardFromJournal {image} (_present : image ∈ joined.durable.images)
    {row} (_member : row ∈ image.collection.rows)
    (same : joined.current.policy.config = row.projection.configAlias.1) :
    joined.parents.config.value = row.projection.configAlias.2 := by
  obtain ⟨name,selected,value⟩ := journalConfigFromOriginalName row.projection
  have forward := joined.configForward
  rw [same] at forward
  have text := Option.some.inj (forward.symm.trans selected)
  simpa only [PublicEarlyBody.Name.value,text] using value.symm

theorem observedCurrentQuorum {exposed}
    (signers : SignerImage joined.actorPolicy joined.current.edge.decoded.certificate.signers exposed) :
    joined.current.edge.decoded.certificate.threshold = 2*((actors.length-1)/3)+1 ∧
    joined.current.edge.decoded.certificate.threshold ≤ exposed.length ∧ exposed.Nodup ∧
    (∀ signer ∈ joined.current.edge.decoded.certificate.signers,
      ∃ actor ∈ exposed, actorBytes mapping actor = some signer) :=
  certifiedCurrentSignerQuorum joined.current joined.actorPolicy signers

end ObservedState

end Direct
end DeltaReduce.FamilyRelation
