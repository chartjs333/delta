import ProfileInstalledState
import ProfileGenesis

/-! T047/T053. The selected unit-bearing source generation joined to complete
original policy/collections. Old entry points remain unchanged. A typed profile
is a core-field view; its whole original P bytes and quantum are retained.
This static source join is not producer authority or complete R2.3 refinement. -/
namespace DeltaReduce.ProfileSource.UnitState
open NativeReceiptBytes (Bytes consume)
open NativeVoteBytes (ascii ContentId)
open NativePolicyCodec (Value)
open InputSection (Located)

structure Header where
  config : ConfigurationUnits.Bound
  state : NativeHeader.Coarse
  policy : NativePolicyBytes.Policy

def bindHeader (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (parent : ConfigurationUnits.Parent) (actor configRaw stateRaw policyRaw : Bytes)
    (stateValue : Value) : Option Header := do
  let config ← ConfigurationUnits.admit enrolled parent configRaw
  let (value,policy) ← Policy.decode policyRaw
  if NativeHeader.stateBytes stateValue = some stateRaw then
    let state ← NativeHeader.readCoarse stateValue
    if NativeHeader.matchFields sha configRaw stateRaw actor config.body state value then
      some ⟨config,state,policy⟩ else none
  else none

structure HeaderSource (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (parent : ConfigurationUnits.Parent) (actor configRaw stateRaw policyRaw : Bytes)
    (stateValue : Value) (out : Header) : Prop where
  configuration : ConfigurationUnits.admit enrolled parent configRaw = some out.config
  policy : Policy.decode policyRaw = some (out.policy.source,out.policy)
  originalState : NativeHeader.stateBytes stateValue = some stateRaw
  state : NativeHeader.readCoarse stateValue = some out.state
  fields : NativeHeader.Matches sha configRaw stateRaw actor out.config.body out.state out.policy.source

theorem headerSource {sha enrolled parent actor configRaw stateRaw policyRaw stateValue out}
    (ok : bindHeader sha enrolled parent actor configRaw stateRaw policyRaw stateValue = some out) :
    HeaderSource sha enrolled parent actor configRaw stateRaw policyRaw stateValue out := by
  simp only [bindHeader,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨c,hc,⟨v,p⟩,hp,last⟩ := ok
  split at last <;> try contradiction
  rename_i original
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨s,hs,last⟩ := last
  split at last <;> try contradiction
  rename_i fields
  cases Option.some.inj last
  have source := Policy.extractionOriginal (Policy.sound hp).extraction
  exact ⟨hc,by simpa only [source] using hp,original,hs,
    by simpa only [source] using NativeHeader.matchFieldsCorrect.mp fields⟩

theorem headerComplete {sha enrolled parent actor configRaw stateRaw policyRaw stateValue out}
    (h : HeaderSource sha enrolled parent actor configRaw stateRaw policyRaw stateValue out) :
    bindHeader sha enrolled parent actor configRaw stateRaw policyRaw stateValue = some out := by
  simp only [bindHeader,h.configuration,h.policy,Bind.bind,Option.bind,h.originalState,
    ↓reduceIte,h.state,NativeHeader.matchFieldsCorrect.mpr h.fields]

theorem headerOriginals {sha enrolled parent actor configRaw stateRaw policyRaw stateValue out}
    (ok : bindHeader sha enrolled parent actor configRaw stateRaw policyRaw stateValue = some out) :
    ConfigurationUnits.encodeFrame out.config.body.originalValue = some configRaw ∧
    NativeHeader.stateBytes out.state.original = some stateRaw ∧
    NativeHeader.policyBytes out.policy.source = some policyRaw ∧
    ConfigurationUnits.ParentMatches parent out.config := by
  have h := headerSource ok
  have config := ConfigurationUnits.admitted h.configuration
  exact ⟨(ConfigurationUnits.entireOriginalConfiguration config.1).1,
    by simpa only [(NativeHeader.coarseSource h.state).1] using h.originalState,
    (Policy.sound h.policy).bytes,config.2.2⟩

structure Profile where
  core : NativeApplyProfile.Checked
  numeric : ArithmeticUnits.Numeric

def numeric (q : NativeApplyProfile.Fraction) (p : NativeApplyProfile.Profile) : ArithmeticUnits.Numeric :=
  ⟨q,p.weights,p.learning,p.momentum,p.decay⟩

def quantumPrefix (proof : Bytes) : Bytes :=
  ascii "{\"accumulator_proof_id\":" ++ NativeIscCertificate.quoted proof ++ ascii ",\"apply_quantum\":"

def readQuantum (proof raw : Bytes) : Option NativeApplyProfile.Fraction := do
  let rest ← consume (quantumPrefix proof) raw
  let (q,_) ← ArithmeticUnits.readFraction rest
  some q

def bindProfile (sha : Bytes → Bytes) (sigma : Bytes) (tree : Value) (raw : Bytes) : Option Profile := do
  let p ← NativeApplyProfile.readProfile tree
  let q ← readQuantum p.accumulator raw
  let n := numeric q p
  if ContentId sigma ∧ sigma ≠ NativeVoteBytes.nativeSemantics ∧ NativeApplyProfile.Valid p ∧
      ArithmeticUnits.Valid n ∧ raw = ArithmeticUnits.profileJSON sigma p.accumulator n then
    let id ← NativeContractSize.contentId sha NativeApplyProfile.domain raw
    some ⟨⟨p,tree,id⟩,n⟩
  else none

structure ProfileSource (sha : Bytes → Bytes) (sigma : Bytes) (tree : Value) (raw : Bytes)
    (out : Profile) : Prop where
  core : NativeApplyProfile.readProfile tree = some out.core.profile
  quantum : readQuantum out.core.profile.accumulator raw = some out.numeric.quantum
  numeric : out.numeric = numeric out.numeric.quantum out.core.profile
  tree : out.core.source = tree
  semantic : ContentId sigma
  future : sigma ≠ NativeVoteBytes.nativeSemantics
  native : NativeApplyProfile.Valid out.core.profile
  units : ArithmeticUnits.Valid out.numeric
  bytes : raw = ArithmeticUnits.profileJSON sigma out.core.profile.accumulator out.numeric
  id : NativeContractSize.contentId sha NativeApplyProfile.domain raw = some out.core.id

theorem profileSource {sha sigma tree raw out}
    (ok : bindProfile sha sigma tree raw = some out) : ProfileSource sha sigma tree raw out := by
  simp only [bindProfile,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨p,hp,q,hq,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨id,hi,last⟩ := last
  cases Option.some.inj last
  exact ⟨hp,hq,rfl,rfl,checks.1,checks.2.1,checks.2.2.1,checks.2.2.2.1,checks.2.2.2.2,hi⟩

theorem profileComplete {sha sigma tree raw out} (h : ProfileSource sha sigma tree raw out) :
    bindProfile sha sigma tree raw = some out := by
  unfold bindProfile
  rw [h.core]
  simp only [Bind.bind,Option.bind,h.quantum]
  rw [← h.numeric]
  rw [if_pos ⟨h.semantic,h.future,h.native,h.units,h.bytes⟩,h.id]
  dsimp only [Bind.bind,Option.bind]
  rw [← h.tree]

theorem profileOriginals {sha sigma tree raw out}
    (ok : bindProfile sha sigma tree raw = some out) :
    tree = NativeApplyProfile.profileValue out.core.profile ∧
    raw = ArithmeticUnits.profileJSON sigma out.core.profile.accumulator out.numeric ∧
    raw.length ≤ NativeContractSize.maxBytes :=
  ⟨NativeApplyProfile.profileOriginal (profileSource ok).core,(profileSource ok).bytes,
    (NativeContractSize.accepted (profileSource ok).id).1⟩

def coreRow (row : Located Profile) : Located NativeApplyProfile.Checked :=
  ⟨row.tree,row.raw,row.value.core⟩

structure Applies where
  originalProfiles : List (Located Profile)
  core : Apply.Bound

def bindApplies (sha : Bytes → Bytes) (sigma : Bytes) (expected : NativeInputSetBody.Context)
    (parent : Bytes) (p : NativePolicyBytes.Policy) (roots : Aggregate.Bound)
    (profileRaws bodyRaws certificateRaws : List Bytes) : Option Applies := do
  let pt ← InputSection.trees p "apply_profiles"
  let originalProfiles ← InputSection.collect (bindProfile sha sigma) pt profileRaws
  let profiles := originalProfiles.map coreRow
  let bt ← InputSection.trees p "apply_candidates"
  let bodies ← InputSection.collect (Apply.bind sha sigma .proposed expected p.validators parent roots profiles) bt bodyRaws
  let ct ← InputSection.trees p "apply_qcs"
  let certificates ← InputSection.collect (Apply.bind sha sigma .finalized expected p.validators parent roots profiles) ct certificateRaws
  let finalized ← InputSection.ids p "finalized_apply_ids"
  let out := Apply.Bound.mk profiles bodies certificates finalized
  if Apply.Sets out then some ⟨originalProfiles,out⟩ else none

structure ApplySource (sha : Bytes → Bytes) (sigma : Bytes) (expected : NativeInputSetBody.Context)
    (parent : Bytes) (p : NativePolicyBytes.Policy) (roots : Aggregate.Bound)
    (profileRaws bodyRaws certificateRaws : List Bytes) (out : Applies) : Prop where
  profileTrees : InputSection.trees p "apply_profiles" = some (out.originalProfiles.map Located.tree)
  profileBytes : out.originalProfiles.map Located.raw = profileRaws
  profiles : ∀ row ∈ out.originalProfiles, bindProfile sha sigma row.tree row.raw = some row.value
  core : out.core.profiles = out.originalProfiles.map coreRow
  bodyTrees : InputSection.trees p "apply_candidates" = some (out.core.bodies.map Located.tree)
  bodyBytes : out.core.bodies.map Located.raw = bodyRaws
  bodies : ∀ row ∈ out.core.bodies, Apply.bind sha sigma .proposed expected p.validators parent roots out.core.profiles row.tree row.raw = some row.value
  certificateTrees : InputSection.trees p "apply_qcs" = some (out.core.certificates.map Located.tree)
  certificateBytes : out.core.certificates.map Located.raw = certificateRaws
  certificates : ∀ row ∈ out.core.certificates, Apply.bind sha sigma .finalized expected p.validators parent roots out.core.profiles row.tree row.raw = some row.value
  finalized : InputSection.ids p "finalized_apply_ids" = some out.core.finalized
  sets : Apply.Sets out.core

theorem appliesSource {sha sigma expected parent p roots profileRaws bodyRaws certificateRaws out}
    (ok : bindApplies sha sigma expected parent p roots profileRaws bodyRaws certificateRaws = some out) :
    ApplySource sha sigma expected parent p roots profileRaws bodyRaws certificateRaws out := by
  simp only [bindApplies,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨pt,hpt,profiles,hp,bt,hbt,bodies,hb,ct,hct,certificates,hc,finalized,hf,last⟩ := ok
  split at last <;> try contradiction
  rename_i sets
  cases Option.some.inj last
  have ps := InputSection.collectedOriginals hp
  have bs := InputSection.collectedOriginals hb
  have cs := InputSection.collectedOriginals hc
  exact ⟨by simpa only [ps.1] using hpt,ps.2,InputSection.collectedEach hp,rfl,
    by simpa only [bs.1] using hbt,bs.2,InputSection.collectedEach hb,
    by simpa only [cs.1] using hct,cs.2,InputSection.collectedEach hc,hf,sets⟩

theorem appliesComplete {sha sigma expected parent p roots profileRaws bodyRaws certificateRaws out}
    (h : ApplySource sha sigma expected parent p roots profileRaws bodyRaws certificateRaws out) :
    bindApplies sha sigma expected parent p roots profileRaws bodyRaws certificateRaws = some out := by
  unfold bindApplies
  rw [h.profileTrees,← h.profileBytes]
  simp only [InputSection.collectComplete out.originalProfiles h.profiles,Bind.bind,Option.bind]
  rw [← h.core,h.bodyTrees,← h.bodyBytes]
  simp only [InputSection.collectComplete out.core.bodies h.bodies]
  rw [h.certificateTrees,← h.certificateBytes]
  simp only [InputSection.collectComplete out.core.certificates h.certificates,h.finalized]
  have same : Apply.Bound.mk out.core.profiles out.core.bodies out.core.certificates out.core.finalized = out.core := rfl
  rw [same,if_pos h.sets]

theorem completeProfileInventory {sha sigma expected parent p roots prs bs cs out}
    (ok : bindApplies sha sigma expected parent p roots prs bs cs = some out) :
    out.originalProfiles.map Located.raw = prs ∧
    out.core.profiles.map Located.raw = prs ∧
    out.originalProfiles.length = prs.length ∧
    out.core.profiles.length = prs.length := by
  have h := appliesSource ok
  refine ⟨h.profileBytes,?_,?_,?_⟩
  · rw [h.core,List.map_map]; exact h.profileBytes
  · simpa only [List.length_map] using congrArg List.length h.profileBytes
  · rw [h.core,List.length_map]; simpa only [List.length_map] using congrArg List.length h.profileBytes

structure Collection where
  core : Collections.Bound
  applies : Applies

def bindCollections (sha : Bytes → Bytes) (s : NativeHeader.Coarse) (p : NativePolicyBytes.Policy)
    (raw : Collections.Originals) : Option Collection := do
  let schema ← Collections.text p "parameter_schema_id"
  let arithmetic ← Collections.text p "arithmetic_profile_id"
  let accumulator ← Collections.text p "required_accumulator_proof_id"
  let proposed ← InputSection.ids p "proposed_round_config_ids"
  let finalized ← InputSection.ids p "finalized_round_config_ids"
  let ctx := NativeIscAdmission.expected p (Collections.stateView s) schema arithmetic
  let ec ← Eligibility.bindSection sha s.semantics ctx s.parent p raw.inputBodies
    raw.inputCertificates raw.norms raw.seeds raw.eligibilityBodies raw.eligibilityCertificates
  let plans ← Plan.bindCollections sha s.semantics ctx p ec raw.planBodies raw.planCertificates
  let parameters ← Parameter.bindCollections sha s.semantics ctx p ec plans
    raw.parameterBodies raw.parameterCertificates
  let roots ← Aggregate.bindCollections sha s.semantics ctx p ec plans parameters
    raw.rootBodies raw.rootCertificates
  let applies ← bindApplies sha s.semantics ctx s.parent p roots
    raw.profiles raw.applyBodies raw.applyCertificates
  let tail ← NativeFailureSection.checkTail sha p (Collections.stateView s)
  let sizes ← NativeContractSize.checkAll sha
    (ec.lineage.inputs.bodies.map (Collections.proposedSizeRow s.semantics p.validators))
  let out := Collections.Bound.mk schema arithmetic accumulator ctx proposed finalized ec plans
    parameters roots applies.core tail sizes
  if Collections.BaseChecks p s out then some ⟨out,applies⟩ else none

structure CollectionSource (sha : Bytes → Bytes) (s : NativeHeader.Coarse) (p : NativePolicyBytes.Policy)
    (raw : Collections.Originals) (out : Collection) : Prop where
  schema : Collections.text p "parameter_schema_id" = some out.core.schema
  arithmetic : Collections.text p "arithmetic_profile_id" = some out.core.arithmetic
  accumulator : Collections.text p "required_accumulator_proof_id" = some out.core.accumulator
  proposed : InputSection.ids p "proposed_round_config_ids" = some out.core.proposedConfigs
  finalized : InputSection.ids p "finalized_round_config_ids" = some out.core.finalizedConfigs
  context : out.core.context = NativeIscAdmission.expected p (Collections.stateView s) out.core.schema out.core.arithmetic
  eligibility : Eligibility.bindSection sha s.semantics out.core.context s.parent p raw.inputBodies
    raw.inputCertificates raw.norms raw.seeds raw.eligibilityBodies raw.eligibilityCertificates = some out.core.eligibility
  plans : Plan.bindCollections sha s.semantics out.core.context p out.core.eligibility raw.planBodies raw.planCertificates = some out.core.plans
  parameters : Parameter.bindCollections sha s.semantics out.core.context p out.core.eligibility out.core.plans
    raw.parameterBodies raw.parameterCertificates = some out.core.parameters
  roots : Aggregate.bindCollections sha s.semantics out.core.context p out.core.eligibility out.core.plans out.core.parameters
    raw.rootBodies raw.rootCertificates = some out.core.roots
  applies : bindApplies sha s.semantics out.core.context s.parent p out.core.roots
    raw.profiles raw.applyBodies raw.applyCertificates = some out.applies
  core : out.core.applies = out.applies.core
  tail : NativeFailureSection.checkTail sha p (Collections.stateView s) = some out.core.tail
  sizes : NativeContractSize.checkAll sha
    (out.core.eligibility.lineage.inputs.bodies.map (Collections.proposedSizeRow s.semantics p.validators)) = some out.core.proposedInputSizes
  base : Collections.BaseChecks p s out.core

theorem collectionsSource {sha s p raw out} (ok : bindCollections sha s p raw = some out) :
    CollectionSource sha s p raw out := by
  simp only [bindCollections,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨schema,hs,arithmetic,ha,accumulator,hu,proposed,hp,finalized,hf,
    ec,he,plans,hl,parameters,hps,roots,hr,applies,has,tail,ht,sizes,hz,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  exact ⟨hs,ha,hu,hp,hf,rfl,he,hl,hps,hr,has,rfl,ht,hz,checks⟩

theorem collectionsComplete {sha s p raw out} (h : CollectionSource sha s p raw out) :
    bindCollections sha s p raw = some out := by
  unfold bindCollections
  rw [h.schema,h.arithmetic,h.accumulator,h.proposed,h.finalized]
  simp only [Bind.bind,Option.bind]
  rw [← h.context,h.eligibility]
  dsimp only
  rw [h.plans]
  dsimp only
  rw [h.parameters]
  dsimp only
  rw [h.roots]
  dsimp only
  rw [h.applies]
  dsimp only
  rw [h.tail]
  dsimp only
  rw [h.sizes]
  dsimp only
  rw [← h.core]
  have same : Collections.Bound.mk out.core.schema out.core.arithmetic out.core.accumulator
      out.core.context out.core.proposedConfigs out.core.finalizedConfigs out.core.eligibility
      out.core.plans out.core.parameters out.core.roots out.core.applies out.core.tail
      out.core.proposedInputSizes = out.core := rfl
  rw [same,if_pos h.base]

structure Bound where
  header : Header
  collections : Collection
  candidates : List Candidates.Entry

def bind (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment) (parent : ConfigurationUnits.Parent)
    (actor configRaw stateRaw policyRaw : Bytes) (stateValue : Value)
    (originals : Collections.Originals) : Option Bound := do
  let h ← bindHeader sha enrolled parent actor configRaw stateRaw policyRaw stateValue
  let c ← bindCollections sha h.state h.policy originals
  let candidates ← Candidates.checkAll sha h.policy h.state c.core h.policy.candidates
  some ⟨h,c,candidates⟩

structure Source (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment) (parent : ConfigurationUnits.Parent)
    (actor configRaw stateRaw policyRaw : Bytes) (stateValue : Value)
    (originals : Collections.Originals) (out : Bound) : Prop where
  header : bindHeader sha enrolled parent actor configRaw stateRaw policyRaw stateValue = some out.header
  collections : bindCollections sha out.header.state out.header.policy originals = some out.collections
  candidates : Candidates.checkAll sha out.header.policy out.header.state out.collections.core
    out.header.policy.candidates = some out.candidates

theorem boundSource {sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals out}
    (ok : bind sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals = some out) :
    Source sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals out := by
  simp only [bind,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨h,hh,c,hc,candidates,hcs,last⟩ := ok
  cases Option.some.inj last
  exact ⟨hh,hc,hcs⟩

theorem complete {sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals out}
    (h : Source sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals out) :
    bind sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals = some out := by
  simp only [bind,h.header,h.collections,h.candidates,Bind.bind,Option.bind]

theorem allOriginalHeaders {sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals out}
    (ok : bind sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals = some out) :
    ConfigurationUnits.encodeFrame out.header.config.body.originalValue = some configRaw ∧
    NativeHeader.stateBytes out.header.state.original = some stateRaw ∧
    NativeHeader.policyBytes out.header.policy.source = some policyRaw ∧
    out.candidates.map Candidates.Entry.original = out.header.policy.candidates := by
  have h := boundSource ok
  have original := headerOriginals h.header
  exact ⟨original.1,original.2.1,original.2.2.1,Candidates.originals h.candidates⟩

theorem originalParentUnits {sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals out}
    (ok : bind sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals = some out) :
    ConfigurationUnits.ParentMatches parent out.header.config :=
  (headerOriginals (boundSource ok).header).2.2.2

theorem abortPreservesDownstream {sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals out row}
    (ok : bind sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals = some out)
    (member : row ∈ out.collections.core.tail.aborts) :
    NativeFailureSection.LineageSource out.header.policy
      ⟨row.body.configs,row.body.inputs,row.body.eligibility,row.body.plans,
       row.body.parameters,row.body.roots,row.body.applies⟩ :=
  NativeFailureSection.completeAbortLists (collectionsSource (boundSource ok).collections).tail member

theorem everyOriginalProfile {sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals out row}
    (ok : bind sha enrolled parent actor configRaw stateRaw policyRaw stateValue originals = some out)
    (member : row ∈ out.collections.applies.originalProfiles) :
    ProfileSource sha out.header.state.semantics row.tree row.raw row.value :=
  profileSource ((appliesSource (collectionsSource (boundSource ok).collections).applies).profiles row member)

end DeltaReduce.ProfileSource.UnitState
