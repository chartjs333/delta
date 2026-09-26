import DeltaReduce.NativeParameterLineage

/-! Complete original PARAMETER lists, assignment map/set checks and matrix.
The actual preceding plan section is executed; later ROOT/APPLY remain open. -/
namespace DeltaReduce.NativeParameterSection
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativePolicyBytes (Policy)
open NativeStateBytes (State)
open NativeParameterLineage (Mode Edge)
structure Bound where
  plans : NativePlanSection.Bound
  keyTrees : List Value
  keys : List NativeParameter.Key
  bodyTrees : List Value
  bodies : List Edge
  certificateTrees : List Value
  certificates : List Edge
  finalized : List Bytes
def expected (p : Policy) (s : State) (b : NativePlanSection.Bound) : NativeInputSetBody.Context :=
  NativePlanSection.expected p s b.eligibility
def trees (p : Policy) (key : String) : Option (List Value) :=
  lookup fmtSnapshot p.snapshot key >>= NativePolicyBytes.items
def edgeList (sha : Bytes → Bytes) (p : Policy) (s : State) (b : NativePlanSection.Bound)
    (keys : List NativeParameter.Key) (mode : Mode) (vs : List Value) :=
  NativeParameterLineage.checkAll sha mode (expected p s b) p.validators
    b.eligibility.norms.isc.certificates b.eligibility.norms.isc.finalized b.eligibility.finalized
    b.finalized keys b.eligibility.certificates b.certificates vs
def SetChecks (b : Bound) : Prop :=
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (b.bodies.map Edge.id) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (b.certificates.map Edge.id) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT b.finalized = true ∧
  (∀ id ∈ b.finalized, id ∈ b.certificates.map Edge.id) ∧
  NativePolicyBytes.strictly NativeParameter.keyLT b.keys = true ∧
  NativeParameter.assignments [] (b.bodies.map NativeParameterLineage.asBody) = true
instance (b) : Decidable (SetChecks b) := by unfold SetChecks; infer_instance
def bindSection (sha : Bytes → Bytes) (p : Policy) (s : State) : Option Bound := do
  let plans ← NativePlanSection.bindSection sha p s
  let keyTrees ← trees p "required_parameter_keys"
  let keys ← NativeParameter.readKeys keyTrees
  let bodyTrees ← trees p "parameter_bodies"
  let bodies ← edgeList sha p s plans keys .proposed bodyTrees
  let certificateTrees ← trees p "parameter_qcs"
  let certificates ← edgeList sha p s plans keys .finalized certificateTrees
  let finalized ← NativeConfigAdmission.getTexts fmtSnapshot p.snapshot "finalized_parameter_ids"
  let b := Bound.mk plans keyTrees keys bodyTrees bodies certificateTrees certificates finalized
  if SetChecks b then some b else none
structure Source (sha : Bytes → Bytes) (p : Policy) (s : State) (b : Bound) : Prop where
  plans : NativePlanSection.bindSection sha p s = some b.plans
  keyTrees : trees p "required_parameter_keys" = some b.keyTrees
  keys : NativeParameter.readKeys b.keyTrees = some b.keys
  bodyTrees : trees p "parameter_bodies" = some b.bodyTrees
  bodies : edgeList sha p s b.plans b.keys .proposed b.bodyTrees = some b.bodies
  certificateTrees : trees p "parameter_qcs" = some b.certificateTrees
  certificates : edgeList sha p s b.plans b.keys .finalized b.certificateTrees = some b.certificates
  finalized : NativeConfigAdmission.getTexts fmtSnapshot p.snapshot "finalized_parameter_ids" = some b.finalized
  sets : SetChecks b
theorem checkedSource {sha p s b} (h : bindSection sha p s = some b) : Source sha p s b := by
  unfold bindSection at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨plans,hp,kt,hkt,keys,hk,bt,hbt,bodies,hb,ct,hct,certificates,hc,finalized,hf,last⟩ := h
  split at last <;> try contradiction
  rename_i sets
  cases Option.some.inj last
  exact ⟨hp,hkt,hk,hbt,hb,hct,hc,hf,sets⟩
theorem fromComponents {sha p s b} (h : Source sha p s b) : bindSection sha p s = some b := by
  unfold bindSection
  rw [h.plans,h.keyTrees]
  dsimp only [bind,Option.bind]
  rw [h.keys,h.bodyTrees]
  dsimp only [bind,Option.bind]
  rw [h.bodies,h.certificateTrees]
  dsimp only [bind,Option.bind]
  rw [h.certificates,h.finalized]
  exact if_pos h.sets
theorem originalLists {sha p s b} (h : bindSection sha p s = some b) :
    b.bodies.map Edge.source = b.bodyTrees ∧ b.certificates.map Edge.source = b.certificateTrees ∧
    b.keyTrees = b.keys.map NativeParameter.keyValue := by
  have src := checkedSource h
  exact ⟨NativeParameterLineage.allSources src.bodies,NativeParameterLineage.allSources src.certificates,
    NativeParameter.keysOriginal src.keys⟩
theorem exactCounts {sha p s b} (h : bindSection sha p s = some b) :
    b.bodies.length = b.bodyTrees.length ∧ b.certificates.length = b.certificateTrees.length := by
  have hb := congrArg List.length (originalLists h).1
  have hc := congrArg List.length (originalLists h).2.1
  exact ⟨by simpa using hb,by simpa using hc⟩
theorem distinctAssignments {sha p s b} (h : bindSection sha p s = some b) :
    (b.bodies.map NativeParameterLineage.asBody).Pairwise (fun a b =>
      NativeParameter.assignmentKey a ≠ NativeParameter.assignmentKey b ∧ a.voteContext ≠ b.voteContext) :=
  NativeParameter.assignmentsDistinct (checkedSource h).sets.2.2.2.2.2

theorem certificateChecked {sha p s b e} (h : bindSection sha p s = some b)
    (mem : e ∈ b.certificates) : NativeParameterLineage.check sha .finalized (expected p s b.plans) p.validators
      b.plans.eligibility.norms.isc.certificates b.plans.eligibility.norms.isc.finalized b.plans.eligibility.finalized
      b.plans.finalized b.keys b.plans.eligibility.certificates b.plans.certificates e.source = some e :=
  NativeParameterLineage.allChecked (checkedSource h).certificates e mem

theorem proposedChecked {sha p s b e} (h : bindSection sha p s = some b)
    (mem : e ∈ b.bodies) : NativeParameterLineage.check sha .proposed (expected p s b.plans) p.validators
      b.plans.eligibility.norms.isc.certificates b.plans.eligibility.norms.isc.finalized b.plans.eligibility.finalized
      b.plans.finalized b.keys b.plans.eligibility.certificates b.plans.certificates e.source = some e :=
  NativeParameterLineage.allChecked (checkedSource h).bodies e mem

theorem finalizedWitness {sha p s b id} (h : bindSection sha p s = some b)
    (mem : id ∈ b.finalized) : ∃ e ∈ b.certificates, e.id = id ∧
    NativeParameterLineage.check sha .finalized (expected p s b.plans) p.validators
      b.plans.eligibility.norms.isc.certificates b.plans.eligibility.norms.isc.finalized b.plans.eligibility.finalized
      b.plans.finalized b.keys b.plans.eligibility.certificates b.plans.certificates e.source = some e := by
  obtain ⟨e,he,eq⟩ := List.mem_map.mp ((checkedSource h).sets.2.2.2.1 id mem)
  exact ⟨e,he,eq,certificateChecked h he⟩
theorem checkedPlan {sha p s b mode source e} (h : bindSection sha p s = some b)
    (edge : NativeParameterLineage.check sha mode (expected p s b.plans) p.validators
      b.plans.eligibility.norms.isc.certificates b.plans.eligibility.norms.isc.finalized b.plans.eligibility.finalized
      b.plans.finalized b.keys b.plans.eligibility.certificates b.plans.certificates source = some e) :
    NativePlanLineage.check sha .finalized (NativePlanSection.expected p s b.plans.eligibility) p.validators
      b.plans.eligibility.norms.isc.certificates b.plans.eligibility.norms.isc.finalized b.plans.eligibility.finalized
      b.plans.required b.plans.eligibility.certificates b.plans.eligibility.seeds e.plan.source = some e.plan :=
  NativePlanSection.certificateChecked (checkedSource h).plans (NativeParameterLineage.parentWitnesses edge).2.2.2.2.1
theorem checkedEc {sha p s b mode source e} (h : bindSection sha p s = some b)
    (edge : NativeParameterLineage.check sha mode (expected p s b.plans) p.validators
      b.plans.eligibility.norms.isc.certificates b.plans.eligibility.norms.isc.finalized b.plans.eligibility.finalized
      b.plans.finalized b.keys b.plans.eligibility.certificates b.plans.certificates source = some e) :
    NativeEligibilityLineage.check sha .finalized (expected p s b.plans) p.validators
      b.plans.eligibility.norms.isc.certificates b.plans.eligibility.norms.isc.finalized b.plans.eligibility.norms.norms
      b.plans.eligibility.seeds e.ec.source = some e.ec :=
  NativeEligibilitySection.certificateChecked (NativePlanSection.checkedSource (checkedSource h).plans).eligibility
    (NativeParameterLineage.parentWitnesses edge).2.2.1
theorem checkedIsc {sha p s b mode source e} (h : bindSection sha p s = some b)
    (edge : NativeParameterLineage.check sha mode (expected p s b.plans) p.validators
      b.plans.eligibility.norms.isc.certificates b.plans.eligibility.norms.isc.finalized b.plans.eligibility.finalized
      b.plans.finalized b.keys b.plans.eligibility.certificates b.plans.certificates source = some e) :
    NativeIscCertificate.Source sha (expected p s b.plans) p.validators e.parent.source e.parent := by
  have hp := NativePlanSection.checkedSource (checkedSource h).plans
  have he := NativeEligibilitySection.checkedSource hp.eligibility
  have hi := NativeFinalizedIscSection.checkedSource (NativeNormSection.checkedSource he.norms).1
  exact NativeIscCertificate.allChecked hi.2.2.2.2.2.2.2.1 e.parent (NativeParameterLineage.parentWitnesses edge).1
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
end DeltaReduce.NativeParameterSection
