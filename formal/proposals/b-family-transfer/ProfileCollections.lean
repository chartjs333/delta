import ProfileApply
import DeltaReduce.NativeFailureSection

/-! T047/T053. One complete installed-policy collection join at its original
context. The typed summary is a field view only: it is never encoded through
the legacy native byte serializer. Full producer origin and public-state
refinement remain outer obligations, including the no-installed-policy case. -/
namespace DeltaReduce.ProfileSource.Collections
open NativeReceiptBytes NativePolicyCodec
open InputSection (Located)

/-- Reuse pure native guards on the same decoded fields, not legacy wire bytes. -/
def stateView (s : NativeHeader.Coarse) : NativeStateBytes.State :=
  ⟨⟨s.available,s.committed,s.config,NativeIscCertificate.number s.sequence,
    NativeIscCertificate.number s.height,s.parent,s.phase,s.round,s.root,s.total,
    NativeIscCertificate.number s.view⟩,s.sequence,s.height,s.view⟩

theorem stateFields (s : NativeHeader.Coarse) :
    (stateView s).height = s.height ∧ (stateView s).view = s.view ∧
    (stateView s).sequence = s.sequence ∧ (stateView s).wire.parent = s.parent ∧
    (stateView s).wire.round = s.round ∧ (stateView s).wire.phase = s.phase ∧
    (stateView s).wire.config = s.config ∧ (stateView s).wire.root = s.root := by
  exact ⟨rfl,rfl,rfl,rfl,rfl,rfl,rfl,rfl⟩

structure Originals where
  inputBodies : List Bytes
  inputCertificates : List Bytes
  norms : List Bytes
  seeds : List Bytes
  eligibilityBodies : List Bytes
  eligibilityCertificates : List Bytes
  planBodies : List Bytes
  planCertificates : List Bytes
  parameterBodies : List Bytes
  parameterCertificates : List Bytes
  rootBodies : List Bytes
  rootCertificates : List Bytes
  profiles : List Bytes
  applyBodies : List Bytes
  applyCertificates : List Bytes

def proposedSizeRow (sigma : Bytes) (committee : List Bytes)
    (row : Located InputSection.BodyRow) : NativeContractSize.Row :=
  ⟨"ISC_PROPOSED",row.tree,NativeVoteBytes.ascii "deltareduce.008.input-set-certificate.v2",
    ISCSourceV2.certificateJSON sigma
      ⟨row.value.body,NativeIscCertificate.quorum committee,committee⟩,none⟩

structure Bound where
  schema : Bytes
  arithmetic : Bytes
  accumulator : Bytes
  context : NativeInputSetBody.Context
  proposedConfigs : List Bytes
  finalizedConfigs : List Bytes
  eligibility : Eligibility.Bound
  plans : Plan.Bound
  parameters : Parameter.Bound
  roots : Aggregate.Bound
  applies : Apply.Bound
  tail : NativeFailureSection.Tail
  proposedInputSizes : List NativeContractSize.Checked

def text (p : NativePolicyBytes.Policy) (key : String) : Option Bytes :=
  lookup NativeHeader.snapshotFormat p.snapshot key >>= NativePolicyBytes.text

def BaseChecks (p : NativePolicyBytes.Policy) (s : NativeHeader.Coarse) (b : Bound) : Prop :=
  NativeConfigAdmission.HeaderChecks p (stateView s) ∧
  NativeIscCertificate.CommitteeValid p.validators ∧ NativeInputSetBody.ContextValid b.context ∧
  (b.accumulator = [] ∨ NativeVoteBytes.ContentId b.accumulator) ∧
  NativeConfigAdmission.ConfigIds p b.proposedConfigs ∧
  NativeConfigAdmission.ConfigIds p b.finalizedConfigs
instance (p s b) : Decidable (BaseChecks p s b) := by unfold BaseChecks; infer_instance

def bind (sha : Bytes → Bytes) (s : NativeHeader.Coarse) (p : NativePolicyBytes.Policy)
    (raw : Originals) : Option Bound := do
  let schema ← text p "parameter_schema_id"
  let arithmetic ← text p "arithmetic_profile_id"
  let accumulator ← text p "required_accumulator_proof_id"
  let proposed ← InputSection.ids p "proposed_round_config_ids"
  let finalized ← InputSection.ids p "finalized_round_config_ids"
  let ctx := NativeIscAdmission.expected p (stateView s) schema arithmetic
  let ec ← Eligibility.bindSection sha s.semantics ctx s.parent p raw.inputBodies
    raw.inputCertificates raw.norms raw.seeds raw.eligibilityBodies raw.eligibilityCertificates
  let plans ← Plan.bindCollections sha s.semantics ctx p ec raw.planBodies raw.planCertificates
  let parameters ← Parameter.bindCollections sha s.semantics ctx p ec plans
    raw.parameterBodies raw.parameterCertificates
  let roots ← Aggregate.bindCollections sha s.semantics ctx p ec plans parameters
    raw.rootBodies raw.rootCertificates
  let applies ← Apply.bindCollections sha s.semantics ctx s.parent p roots
    raw.profiles raw.applyBodies raw.applyCertificates
  let tail ← NativeFailureSection.checkTail sha p (stateView s)
  let sizes ← NativeContractSize.checkAll sha
    (ec.lineage.inputs.bodies.map (proposedSizeRow s.semantics p.validators))
  let out := Bound.mk schema arithmetic accumulator ctx proposed finalized ec plans
    parameters roots applies tail sizes
  if BaseChecks p s out then some out else none

structure Source (sha : Bytes → Bytes) (s : NativeHeader.Coarse) (p : NativePolicyBytes.Policy)
    (raw : Originals) (out : Bound) : Prop where
  schema : text p "parameter_schema_id" = some out.schema
  arithmetic : text p "arithmetic_profile_id" = some out.arithmetic
  accumulator : text p "required_accumulator_proof_id" = some out.accumulator
  proposed : InputSection.ids p "proposed_round_config_ids" = some out.proposedConfigs
  finalized : InputSection.ids p "finalized_round_config_ids" = some out.finalizedConfigs
  context : out.context = NativeIscAdmission.expected p (stateView s) out.schema out.arithmetic
  eligibility : Eligibility.bindSection sha s.semantics out.context s.parent p raw.inputBodies
    raw.inputCertificates raw.norms raw.seeds raw.eligibilityBodies raw.eligibilityCertificates = some out.eligibility
  plans : Plan.bindCollections sha s.semantics out.context p out.eligibility raw.planBodies raw.planCertificates = some out.plans
  parameters : Parameter.bindCollections sha s.semantics out.context p out.eligibility out.plans
    raw.parameterBodies raw.parameterCertificates = some out.parameters
  roots : Aggregate.bindCollections sha s.semantics out.context p out.eligibility out.plans out.parameters
    raw.rootBodies raw.rootCertificates = some out.roots
  applies : Apply.bindCollections sha s.semantics out.context s.parent p out.roots
    raw.profiles raw.applyBodies raw.applyCertificates = some out.applies
  tail : NativeFailureSection.checkTail sha p (stateView s) = some out.tail
  sizes : NativeContractSize.checkAll sha
    (out.eligibility.lineage.inputs.bodies.map (proposedSizeRow s.semantics p.validators)) = some out.proposedInputSizes
  base : BaseChecks p s out

theorem boundSource {sha s p raw out} (ok : bind sha s p raw = some out) :
    Source sha s p raw out := by
  unfold bind at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨schema,hs,arithmetic,ha,accumulator,hu,proposed,hp,finalized,hf,
    ec,he,plans,hl,parameters,hps,roots,hr,applies,has,tail,ht,sizes,hz,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  exact ⟨hs,ha,hu,hp,hf,rfl,he,hl,hps,hr,has,ht,hz,checks⟩

theorem boundComplete {sha s p raw out} (h : Source sha s p raw out) :
    bind sha s p raw = some out := by
  unfold bind
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
  exact if_pos h.base

theorem abortLineageNotErased {sha s p raw out row}
    (ok : bind sha s p raw = some out) (member : row ∈ out.tail.aborts) :
    NativeFailureSection.LineageSource p
      ⟨row.body.configs,row.body.inputs,row.body.eligibility,row.body.plans,
       row.body.parameters,row.body.roots,row.body.applies⟩ :=
  NativeFailureSection.completeAbortLists (boundSource ok).tail member

theorem proposedIscBound {sha s p raw out row}
    (ok : bind sha s p raw = some out) (member : row ∈ out.eligibility.lineage.inputs.bodies) :
    (ISCSourceV2.certificateJSON s.semantics
      ⟨row.value.body,NativeIscCertificate.quorum p.validators,p.validators⟩).length ≤ NativeContractSize.maxBytes :=
  NativeContractSize.allBounds (boundSource ok).sizes _ (List.mem_map.mpr ⟨row,member,rfl⟩)

theorem originalConfigurations {sha s p raw out} (ok : bind sha s p raw = some out) :
    (∀ id ∈ out.proposedConfigs, id = p.config) ∧ (∀ id ∈ out.finalizedConfigs, id = p.config) :=
  ⟨(boundSource ok).base.2.2.2.2.1.2,(boundSource ok).base.2.2.2.2.2.2⟩

end DeltaReduce.ProfileSource.Collections
