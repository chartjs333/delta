import DeltaReduce.NativeAggregateLineage

/-! Complete ROOT proposal/QC/finalized lists, executing the actual bounded
preceding section. APPLY/current and full snapshot admission remain separate. -/
namespace DeltaReduce.NativeAggregateSection
open NativeReceiptBytes NativePolicyCodec NativePolicySchema NativeAggregateLineage
open NativePolicyBytes (Policy)
open NativeStateBytes (State)
open NativeParameterLineage (Mode)
open NativeParameterSection (trees expected)

structure Bound where
  parameters : NativeSizedParameterSection.Bound
  bodyTrees : List Value
  bodies : List Edge
  certificateTrees : List Value
  certificates : List Edge
  finalized : List Bytes

def edgeList (sha : Bytes → Bytes) (p : Policy) (s : State) (b : NativeParameterSection.Bound)
    (mode : Mode) (vs : List Value) :=
  checkAll sha mode (expected p s b.plans) p.validators
    b.plans.eligibility.norms.isc.certificates b.plans.eligibility.norms.isc.finalized
    b.plans.eligibility.finalized b.plans.finalized b.finalized b.keys
    b.plans.eligibility.certificates b.plans.certificates b.certificates vs

def SetChecks (b : Bound) : Prop :=
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (b.bodies.map Edge.id) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (b.certificates.map Edge.id) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT b.finalized = true ∧
  ∀ id ∈ b.finalized, id ∈ b.certificates.map Edge.id
instance (b) : Decidable (SetChecks b) := by unfold SetChecks; infer_instance

def bindSection (sha : Bytes → Bytes) (p : Policy) (s : State) : Option Bound := do
  let parameters ← NativeSizedParameterSection.bindSection sha p s
  let bt ← trees p "aggregate_root_bodies"
  let bodies ← edgeList sha p s parameters.prior .proposed bt
  let ct ← trees p "aggregate_root_qcs"
  let certificates ← edgeList sha p s parameters.prior .finalized ct
  let finalized ← NativeConfigAdmission.getTexts fmtSnapshot p.snapshot "finalized_aggregate_root_ids"
  let b := Bound.mk parameters bt bodies ct certificates finalized
  if SetChecks b then some b else none

structure Source (sha : Bytes → Bytes) (p : Policy) (s : State) (b : Bound) : Prop where
  parameters : NativeSizedParameterSection.bindSection sha p s = some b.parameters
  bodyTrees : trees p "aggregate_root_bodies" = some b.bodyTrees
  bodies : edgeList sha p s b.parameters.prior .proposed b.bodyTrees = some b.bodies
  certificateTrees : trees p "aggregate_root_qcs" = some b.certificateTrees
  certificates : edgeList sha p s b.parameters.prior .finalized b.certificateTrees = some b.certificates
  finalized : NativeConfigAdmission.getTexts fmtSnapshot p.snapshot "finalized_aggregate_root_ids" = some b.finalized
  sets : SetChecks b

theorem checkedSource {sha p s b} (h : bindSection sha p s = some b) : Source sha p s b := by
  unfold bindSection at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨parameters,hp,bt,hbt,bodies,hb,ct,hct,certificates,hc,finalized,hf,last⟩ := h
  split at last <;> try contradiction
  rename_i sets
  cases Option.some.inj last
  exact ⟨hp,hbt,hb,hct,hc,hf,sets⟩

theorem fromComponents {sha p s b} (h : Source sha p s b) : bindSection sha p s = some b := by
  unfold bindSection
  rw [h.parameters,h.bodyTrees]
  dsimp only [bind,Option.bind]
  rw [h.bodies,h.certificateTrees]
  dsimp only [bind,Option.bind]
  rw [h.certificates,h.finalized]
  exact if_pos h.sets

theorem originalLists {sha p s b} (h : bindSection sha p s = some b) :
    b.bodies.map Edge.source = b.bodyTrees ∧ b.certificates.map Edge.source = b.certificateTrees :=
  ⟨allSources (checkedSource h).bodies,allSources (checkedSource h).certificates⟩

theorem exactCounts {sha p s b} (h : bindSection sha p s = some b) :
    b.bodies.length = b.bodyTrees.length ∧ b.certificates.length = b.certificateTrees.length := by
  have hb := congrArg List.length (originalLists h).1
  have hc := congrArg List.length (originalLists h).2
  exact ⟨by simpa using hb,by simpa using hc⟩

theorem certificateChecked {sha p s b e} (h : bindSection sha p s = some b)
    (mem : e ∈ b.certificates) : check sha .finalized (expected p s b.parameters.prior.plans) p.validators
      b.parameters.prior.plans.eligibility.norms.isc.certificates b.parameters.prior.plans.eligibility.norms.isc.finalized
      b.parameters.prior.plans.eligibility.finalized b.parameters.prior.plans.finalized b.parameters.prior.finalized
      b.parameters.prior.keys b.parameters.prior.plans.eligibility.certificates b.parameters.prior.plans.certificates
      b.parameters.prior.certificates e.source = some e :=
  allChecked (checkedSource h).certificates e mem

theorem proposedChecked {sha p s b e} (h : bindSection sha p s = some b)
    (mem : e ∈ b.bodies) : check sha .proposed (expected p s b.parameters.prior.plans) p.validators
      b.parameters.prior.plans.eligibility.norms.isc.certificates b.parameters.prior.plans.eligibility.norms.isc.finalized
      b.parameters.prior.plans.eligibility.finalized b.parameters.prior.plans.finalized b.parameters.prior.finalized
      b.parameters.prior.keys b.parameters.prior.plans.eligibility.certificates b.parameters.prior.plans.certificates
      b.parameters.prior.certificates e.source = some e :=
  allChecked (checkedSource h).bodies e mem

theorem finalizedWitness {sha p s b id} (h : bindSection sha p s = some b)
    (mem : id ∈ b.finalized) : ∃ e ∈ b.certificates, e.id = id :=
  List.mem_map.mp ((checkedSource h).sets.2.2.2 id mem)

theorem priorBounds {sha p s b row} (h : bindSection sha p s = some b)
    (mem : row ∈ NativeSizedParameterSection.rows b.parameters.prior) :
    row.payload.length ≤ NativeContractSize.maxBytes :=
  NativeSizedParameterSection.everyCertificateBound (checkedSource h).parameters mem

theorem checkedShard {sha p s b mode source e shard} (h : bindSection sha p s = some b)
    (edge : check sha mode (expected p s b.parameters.prior.plans) p.validators
      b.parameters.prior.plans.eligibility.norms.isc.certificates b.parameters.prior.plans.eligibility.norms.isc.finalized
      b.parameters.prior.plans.eligibility.finalized b.parameters.prior.plans.finalized b.parameters.prior.finalized
      b.parameters.prior.keys b.parameters.prior.plans.eligibility.certificates b.parameters.prior.plans.certificates
      b.parameters.prior.certificates source = some e) (mem : shard ∈ e.shards) :
    NativeParameterLineage.check sha .finalized (expected p s b.parameters.prior.plans) p.validators
      b.parameters.prior.plans.eligibility.norms.isc.certificates b.parameters.prior.plans.eligibility.norms.isc.finalized
      b.parameters.prior.plans.eligibility.finalized b.parameters.prior.plans.finalized b.parameters.prior.keys
      b.parameters.prior.plans.eligibility.certificates b.parameters.prior.plans.certificates shard.source = some shard :=
  NativeParameterSection.certificateChecked
    (NativeSizedParameterSection.checkedSource (checkedSource h).parameters).1 (everyShard edge mem).1

def prepare (sha : Bytes → Bytes) (policyRaw stateRaw : Bytes) : Option Bound := do
  let (_,p) ← NativePolicyBytes.decodePolicy policyRaw
  let s ← NativeStateBytes.decodeState stateRaw
  bindSection sha p s

theorem preparedSource {sha policyRaw stateRaw b} (h : prepare sha policyRaw stateRaw = some b) :
    ∃ tree p s, NativePolicyBytes.decodePolicy policyRaw = some (tree,p) ∧
    NativeStateBytes.decodeState stateRaw = some s ∧ Source sha p s b := by
  unfold prepare at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨tree,p⟩,hp,s,hs,hb⟩ := h
  exact ⟨tree,p,s,hp,hs,checkedSource hb⟩

end DeltaReduce.NativeAggregateSection
