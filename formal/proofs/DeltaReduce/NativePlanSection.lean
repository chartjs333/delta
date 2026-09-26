import DeltaReduce.NativePlanLineage

/-! Whole original APC lists compose actual earlier checked EC/ISC/seed sections.
Required accumulator syntax is checked only when a plan list is nonempty. -/
namespace DeltaReduce.NativePlanSection
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativePolicyBytes (Policy)
open NativeStateBytes (State)
open NativePlanLineage (Mode Edge)

structure Bound where
  eligibility : NativeEligibilitySection.Bound
  required : Bytes
  bodyTrees : List Value
  bodies : List Edge
  certificateTrees : List Value
  certificates : List Edge
  finalized : List Bytes

def expected (p : Policy) (s : State) (b : NativeEligibilitySection.Bound) : NativeInputSetBody.Context :=
  NativeEligibilitySection.expected p s b.norms
def trees (p : Policy) (key : String) : Option (List Value) :=
  lookup fmtSnapshot p.snapshot key >>= NativePolicyBytes.items
def edgeList (sha : Bytes → Bytes) (p : Policy) (s : State) (ec : NativeEligibilitySection.Bound)
    (required : Bytes) (mode : Mode) (vs : List Value) :=
  NativePlanLineage.checkAll sha mode (expected p s ec) p.validators
    ec.norms.isc.certificates ec.norms.isc.finalized ec.finalized required ec.certificates ec.seeds vs
def SetChecks (b : Bound) : Prop :=
  ((b.bodyTrees ≠ [] ∨ b.certificateTrees ≠ []) → NativeVoteBytes.ContentId b.required) ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (b.bodies.map Edge.id) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (b.certificates.map Edge.id) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT b.finalized = true ∧
  ∀ id ∈ b.finalized, id ∈ b.certificates.map Edge.id
instance (b) : Decidable (SetChecks b) := by unfold SetChecks; infer_instance

def bindSection (sha : Bytes → Bytes) (p : Policy) (s : State) : Option Bound := do
  let eligibility ← NativeEligibilitySection.bindSection sha p s
  let required ← NativeConfigAdmission.getText fmtSnapshot p.snapshot "required_accumulator_proof_id"
  let bodyTrees ← trees p "aggregation_plan_bodies"
  let bodies ← edgeList sha p s eligibility required .proposed bodyTrees
  let certificateTrees ← trees p "aggregation_plan_certificates"
  let certificates ← edgeList sha p s eligibility required .finalized certificateTrees
  let finalized ← NativeConfigAdmission.getTexts fmtSnapshot p.snapshot "finalized_aggregation_plan_ids"
  let b := Bound.mk eligibility required bodyTrees bodies certificateTrees certificates finalized
  if SetChecks b then some b else none

structure Source (sha : Bytes → Bytes) (p : Policy) (s : State) (b : Bound) : Prop where
  eligibility : NativeEligibilitySection.bindSection sha p s = some b.eligibility
  required : NativeConfigAdmission.getText fmtSnapshot p.snapshot "required_accumulator_proof_id" = some b.required
  bodyTrees : trees p "aggregation_plan_bodies" = some b.bodyTrees
  bodies : edgeList sha p s b.eligibility b.required .proposed b.bodyTrees = some b.bodies
  certificateTrees : trees p "aggregation_plan_certificates" = some b.certificateTrees
  certificates : edgeList sha p s b.eligibility b.required .finalized b.certificateTrees = some b.certificates
  finalized : NativeConfigAdmission.getTexts fmtSnapshot p.snapshot "finalized_aggregation_plan_ids" = some b.finalized
  sets : SetChecks b
theorem checkedSource {sha p s b} (h : bindSection sha p s = some b) : Source sha p s b := by
  unfold bindSection at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨ec,he,required,hr,bt,hbt,bodies,hb,ct,hct,certificates,hc,finalized,hf,last⟩ := h
  split at last <;> try contradiction
  rename_i sets
  cases Option.some.inj last
  exact ⟨he,hr,hbt,hb,hct,hc,hf,sets⟩
theorem fromComponents {sha p s b} (h : Source sha p s b) : bindSection sha p s = some b := by
  unfold bindSection
  rw [h.eligibility,h.required]
  dsimp only [bind,Option.bind]
  rw [h.bodyTrees]
  dsimp only [bind,Option.bind]
  rw [h.bodies,h.certificateTrees]
  dsimp only [bind,Option.bind]
  rw [h.certificates,h.finalized]
  exact if_pos h.sets

theorem originalLists {sha p s b} (h : bindSection sha p s = some b) :
    b.bodies.map Edge.source = b.bodyTrees ∧ b.certificates.map Edge.source = b.certificateTrees := by
  have src := checkedSource h
  exact ⟨NativePlanLineage.allSources src.bodies,NativePlanLineage.allSources src.certificates⟩

theorem exactCounts {sha p s b} (h : bindSection sha p s = some b) :
    b.bodies.length = b.bodyTrees.length ∧ b.certificates.length = b.certificateTrees.length := by
  have hb := congrArg List.length (originalLists h).1
  have hc := congrArg List.length (originalLists h).2
  exact ⟨by simpa using hb,by simpa using hc⟩

theorem certificateChecked {sha p s b e} (h : bindSection sha p s = some b)
    (mem : e ∈ b.certificates) :
    NativePlanLineage.check sha .finalized (expected p s b.eligibility) p.validators
      b.eligibility.norms.isc.certificates b.eligibility.norms.isc.finalized b.eligibility.finalized
      b.required b.eligibility.certificates b.eligibility.seeds e.source = some e :=
  NativePlanLineage.allChecked (checkedSource h).certificates e mem

theorem proposedChecked {sha p s b e} (h : bindSection sha p s = some b)
    (mem : e ∈ b.bodies) :
    NativePlanLineage.check sha .proposed (expected p s b.eligibility) p.validators
      b.eligibility.norms.isc.certificates b.eligibility.norms.isc.finalized b.eligibility.finalized
      b.required b.eligibility.certificates b.eligibility.seeds e.source = some e :=
  NativePlanLineage.allChecked (checkedSource h).bodies e mem

theorem checkedParents {sha p s b mode source e} (h : bindSection sha p s = some b)
    (edge : NativePlanLineage.check sha mode (expected p s b.eligibility) p.validators
      b.eligibility.norms.isc.certificates b.eligibility.norms.isc.finalized b.eligibility.finalized
      b.required b.eligibility.certificates b.eligibility.seeds source = some e) :
    NativeIscCertificate.Source sha (expected p s b.eligibility) p.validators e.parent.source e.parent ∧
    NativeEligibilityLineage.check sha .finalized (expected p s b.eligibility) p.validators
      b.eligibility.norms.isc.certificates b.eligibility.norms.isc.finalized b.eligibility.norms.norms
      b.eligibility.seeds e.ec.source = some e.ec ∧
    NativeSeedTranscript.Source sha (expected p s b.eligibility) b.eligibility.norms.isc.finalized e.seed.source e.seed := by
  have he := (checkedSource h).eligibility
  have src := NativeEligibilitySection.checkedSource he
  have witnesses := NativePlanLineage.parentWitnesses edge
  have isc := NativeFinalizedIscSection.checkedSource (NativeNormSection.checkedSource src.norms).1
  exact ⟨NativeIscCertificate.allChecked isc.2.2.2.2.2.2.2.1 e.parent witnesses.1,
    NativeEligibilitySection.certificateChecked he witnesses.2.2.1,
    NativeSeedTranscript.allChecked src.seeds e.seed witnesses.2.2.2.2.1⟩

theorem finalizedWitness {sha p s b id} (h : bindSection sha p s = some b)
    (mem : id ∈ b.finalized) :
    ∃ e ∈ b.certificates, e.id = id ∧
      NativePlanLineage.check sha .finalized (expected p s b.eligibility) p.validators
        b.eligibility.norms.isc.certificates b.eligibility.norms.isc.finalized b.eligibility.finalized
      b.required b.eligibility.certificates b.eligibility.seeds e.source = some e := by
  obtain ⟨e,he,eq⟩ := List.mem_map.mp ((checkedSource h).sets.2.2.2.2 id mem)
  exact ⟨e,he,eq,certificateChecked h he⟩

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
end DeltaReduce.NativePlanSection
