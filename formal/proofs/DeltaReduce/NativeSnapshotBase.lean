import DeltaReduce.NativeProposedIsc
import DeltaReduce.NativeFailureSection

/-! Shared original snapshot base composed with all existing typed sections.
No candidate list or certificate graph is replaced with an empty proxy. Full
candidate admission, native arithmetic and runtime recovery remain separate. -/
namespace DeltaReduce.NativeSnapshotBase
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativePolicyBytes (Policy)
open NativeStateBytes (State)
open NativeConfigAdmission (getText getTexts HeaderChecks ConfigIds)
open NativeParameterSection (trees)

structure Base where
  schema : Bytes
  arithmetic : Bytes
  accumulator : Bytes
  proposedConfigs : List Bytes
  finalizedConfigs : List Bytes
  inputTrees : List Value
  inputs : List NativeProposedIsc.Checked
  closed : List Bytes

def Checks (p : Policy) (s : State) (b : Base) : Prop :=
  HeaderChecks p s ∧ NativeIscCertificate.CommitteeValid p.validators ∧
  NativeInputSetBody.ContextValid (NativeIscAdmission.expected p s b.schema b.arithmetic) ∧
  (b.accumulator = [] ∨ NativeVoteBytes.ContentId b.accumulator) ∧
  ConfigIds p b.proposedConfigs ∧ ConfigIds p b.finalizedConfigs ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (b.inputs.map (fun c => c.body.id)) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT b.closed = true ∧
  (∀ id ∈ b.closed, NativeVoteBytes.ContentId id) ∧
  ∀ id ∈ b.closed, id ∈ b.inputs.map (fun c => c.body.id)
instance (p s b) : Decidable (Checks p s b) := by unfold Checks; infer_instance

def checkBase (sha : Bytes → Bytes) (p : Policy) (s : State) : Option Base := do
  let schema ← getText fmtSnapshot p.snapshot "parameter_schema_id"
  let arithmetic ← getText fmtSnapshot p.snapshot "arithmetic_profile_id"
  let accumulator ← getText fmtSnapshot p.snapshot "required_accumulator_proof_id"
  let proposedConfigs ← getTexts fmtSnapshot p.snapshot "proposed_round_config_ids"
  let finalizedConfigs ← getTexts fmtSnapshot p.snapshot "finalized_round_config_ids"
  let inputTrees ← trees p "input_set_bodies"
  let inputs ← NativeProposedIsc.checkAll sha
    (NativeIscAdmission.expected p s schema arithmetic) p.validators inputTrees
  let closed ← getTexts fmtSnapshot p.snapshot "closed_input_set_ids"
  let b := Base.mk schema arithmetic accumulator proposedConfigs finalizedConfigs inputTrees inputs closed
  if Checks p s b then some b else none

structure BaseSource (sha : Bytes → Bytes) (p : Policy) (s : State) (b : Base) : Prop where
  schema : getText fmtSnapshot p.snapshot "parameter_schema_id" = some b.schema
  arithmetic : getText fmtSnapshot p.snapshot "arithmetic_profile_id" = some b.arithmetic
  accumulator : getText fmtSnapshot p.snapshot "required_accumulator_proof_id" = some b.accumulator
  proposed : getTexts fmtSnapshot p.snapshot "proposed_round_config_ids" = some b.proposedConfigs
  finalized : getTexts fmtSnapshot p.snapshot "finalized_round_config_ids" = some b.finalizedConfigs
  inputTrees : trees p "input_set_bodies" = some b.inputTrees
  inputs : NativeProposedIsc.checkAll sha (NativeIscAdmission.expected p s b.schema b.arithmetic)
    p.validators b.inputTrees = some b.inputs
  closed : getTexts fmtSnapshot p.snapshot "closed_input_set_ids" = some b.closed
  valid : Checks p s b

theorem checkedBase {sha p s b} (h : checkBase sha p s = some b) : BaseSource sha p s b := by
  unfold checkBase at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨schema,hs,arithmetic,ha,accumulator,hu,proposed,hp,finalized,hf,ts,ht,inputs,hi,closed,hc,last⟩ := h
  split at last <;> try contradiction
  rename_i valid
  cases Option.some.inj last
  exact ⟨hs,ha,hu,hp,hf,ht,hi,hc,valid⟩

theorem baseFromComponents {sha p s b} (h : BaseSource sha p s b) : checkBase sha p s = some b := by
  unfold checkBase
  rw [h.schema,h.arithmetic,h.accumulator,h.proposed,h.finalized,h.inputTrees]
  dsimp only [bind,Option.bind]
  rw [h.inputs,h.closed]
  exact if_pos h.valid

theorem originalInputList {sha p s b} (h : checkBase sha p s = some b) :
    b.inputs.map (fun c => c.body.source) = b.inputTrees :=
  NativeProposedIsc.allSources (checkedBase h).inputs

theorem everyInput {sha p s b out} (h : checkBase sha p s = some b) (mem : out ∈ b.inputs) :
    NativeProposedIsc.Source sha (NativeIscAdmission.expected p s b.schema b.arithmetic)
      p.validators out.body.source out := NativeProposedIsc.allChecked (checkedBase h).inputs out mem

theorem everyInputBounded {sha p s b out} (h : checkBase sha p s = some b) (mem : out ∈ b.inputs) :
    (NativeIscCertificate.json (NativeProposedIsc.certificate p.validators out.body.body)).length ≤
      NativeContractSize.maxBytes := (NativeContractSize.accepted (everyInput h mem).bounded).1

theorem closedHasOriginalBody {sha p s b id} (h : checkBase sha p s = some b) (mem : id ∈ b.closed) :
    ∃ out ∈ b.inputs, out.body.id = id ∧
      NativeProposedIsc.Source sha (NativeIscAdmission.expected p s b.schema b.arithmetic)
        p.validators out.body.source out := by
  obtain ⟨out,member,eq⟩ := List.mem_map.mp ((checkedBase h).valid.2.2.2.2.2.2.2.2.2 id mem)
  exact ⟨out,member,eq,everyInput h member⟩

theorem noInventedClosed {sha p s b id} (h : checkBase sha p s = some b)
    (absent : ∀ out ∈ b.inputs, out.body.id ≠ id) : id ∉ b.closed := by
  intro mem
  obtain ⟨out,member,eq,_⟩ := closedHasOriginalBody h mem
  exact absent out member eq

theorem configurationsExact {sha p s b} (h : checkBase sha p s = some b) :
    (∀ id ∈ b.proposedConfigs, id = p.config) ∧ (∀ id ∈ b.finalizedConfigs, id = p.config) :=
  ⟨(checkedBase h).valid.2.2.2.2.1.2,(checkedBase h).valid.2.2.2.2.2.1.2⟩

theorem constructorContext {sha p s b} (h : checkBase sha p s = some b) :
    NativeInputSetBody.ContextValid (NativeIscAdmission.expected p s b.schema b.arithmetic) :=
  (checkedBase h).valid.2.2.1

structure Bound where
  prior : NativeFailureSection.Bound
  base : Base

def bindSnapshot (sha : Bytes → Bytes) (p : Policy) (s : State) : Option Bound := do
  let prior ← NativeFailureSection.bindSection sha p s
  let base ← checkBase sha p s
  some ⟨prior,base⟩

theorem checkedSnapshot {sha p s b} (h : bindSnapshot sha p s = some b) :
    NativeFailureSection.bindSection sha p s = some b.prior ∧ checkBase sha p s = some b.base := by
  unfold bindSnapshot at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨prior,hp,base,hb,last⟩ := h
  cases Option.some.inj last
  exact ⟨hp,hb⟩

theorem snapshotFromComponents {sha p s b}
    (hp : NativeFailureSection.bindSection sha p s = some b.prior)
    (hb : checkBase sha p s = some b.base) : bindSnapshot sha p s = some b := by
  simp only [bindSnapshot,hp,hb,bind,Option.bind]

theorem rejectInvalidBase {sha p s} (h : checkBase sha p s = none) :
    bindSnapshot sha p s = none := by
  unfold bindSnapshot
  cases NativeFailureSection.bindSection sha p s <;> simp only [h,bind,Option.bind]

def prepare (sha : Bytes → Bytes) (policyRaw stateRaw : Bytes) : Option Bound := do
  let (_,p) ← NativePolicyBytes.decodePolicy policyRaw
  let s ← NativeStateBytes.decodeState stateRaw
  bindSnapshot sha p s

theorem preparedSource {sha policyRaw stateRaw b} (h : prepare sha policyRaw stateRaw = some b) :
    ∃ tree p s, NativePolicyBytes.decodePolicy policyRaw = some (tree,p) ∧
      NativeStateBytes.decodeState stateRaw = some s ∧ NativePolicyBytes.Canonical p ∧
      NativeFailureSection.bindSection sha p s = some b.prior ∧ BaseSource sha p s b.base := by
  unfold prepare at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨tree,p⟩,hp,s,hs,hb⟩ := h
  have result := checkedSnapshot hb
  exact ⟨tree,p,s,hp,hs,NativePolicyBytes.acceptedCanonical hp,result.1,checkedBase result.2⟩

end DeltaReduce.NativeSnapshotBase
