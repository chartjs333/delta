import DeltaReduce.NativeApplyLineage

/-! Complete original APPLY lists joined to the actual bounded ROOT section.
This remains a snapshot subrelation, not complete native vote admission. -/
namespace DeltaReduce.NativeApplySection
open NativeReceiptBytes NativePolicyCodec NativePolicySchema NativeApplyLineage
open NativePolicyBytes (Policy)
open NativeStateBytes (State)
open NativeParameterLineage (Mode)
open NativeParameterSection (trees expected)
structure Bound where
  roots : NativeAggregateSection.Bound
  profileTrees : List Value
  profiles : List NativeApplyProfile.Checked
  bodyTrees : List Value
  bodies : List Edge
  certificateTrees : List Value
  certificates : List Edge
  finalized : List Bytes

def edgeList (sha : Bytes → Bytes) (p : Policy) (s : State) (r : NativeAggregateSection.Bound)
    (profiles : List NativeApplyProfile.Checked) (mode : Mode) (vs : List Value) :=
  checkAll sha mode (expected p s r.parameters.prior.plans) p.validators s.wire.parent
    r.finalized r.certificates profiles vs

def SetChecks (b : Bound) : Prop :=
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (b.profiles.map NativeApplyProfile.Checked.id) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (b.bodies.map Edge.id) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (b.certificates.map Edge.id) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT b.finalized = true ∧
  ∀ id ∈ b.finalized, id ∈ b.certificates.map Edge.id
instance (b) : Decidable (SetChecks b) := by unfold SetChecks; infer_instance

def bindSection (sha : Bytes → Bytes) (p : Policy) (s : State) : Option Bound := do
  let roots ← NativeAggregateSection.bindSection sha p s
  let pt ← trees p "apply_profiles"
  let profiles ← NativeApplyProfile.checkAll sha pt
  let bt ← trees p "apply_candidates"
  let bodies ← edgeList sha p s roots profiles .proposed bt
  let ct ← trees p "apply_qcs"
  let certificates ← edgeList sha p s roots profiles .finalized ct
  let finalized ← NativeConfigAdmission.getTexts fmtSnapshot p.snapshot "finalized_apply_ids"
  let b := Bound.mk roots pt profiles bt bodies ct certificates finalized
  if SetChecks b then some b else none
structure Source (sha : Bytes → Bytes) (p : Policy) (s : State) (b : Bound) : Prop where
  roots : NativeAggregateSection.bindSection sha p s = some b.roots
  profileTrees : trees p "apply_profiles" = some b.profileTrees
  profiles : NativeApplyProfile.checkAll sha b.profileTrees = some b.profiles
  bodyTrees : trees p "apply_candidates" = some b.bodyTrees
  bodies : edgeList sha p s b.roots b.profiles .proposed b.bodyTrees = some b.bodies
  certificateTrees : trees p "apply_qcs" = some b.certificateTrees
  certificates : edgeList sha p s b.roots b.profiles .finalized b.certificateTrees = some b.certificates
  finalized : NativeConfigAdmission.getTexts fmtSnapshot p.snapshot "finalized_apply_ids" = some b.finalized
  sets : SetChecks b

theorem checkedSource {sha p s b} (h : bindSection sha p s = some b) : Source sha p s b := by
  unfold bindSection at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨roots,hr,pt,hpt,profiles,hp,bt,hbt,bodies,hb,ct,hct,certificates,hc,finalized,hf,last⟩ := h
  split at last <;> try contradiction
  rename_i sets
  cases Option.some.inj last
  exact ⟨hr,hpt,hp,hbt,hb,hct,hc,hf,sets⟩
theorem fromComponents {sha p s b} (h : Source sha p s b) : bindSection sha p s = some b := by
  unfold bindSection
  rw [h.roots,h.profileTrees]
  dsimp only [bind,Option.bind]
  rw [h.profiles,h.bodyTrees]
  dsimp only [bind,Option.bind]
  rw [h.bodies,h.certificateTrees]
  dsimp only [bind,Option.bind]
  rw [h.certificates,h.finalized]
  exact if_pos h.sets

theorem originalLists {sha p s b} (h : bindSection sha p s = some b) :
    b.profiles.map NativeApplyProfile.Checked.source = b.profileTrees ∧
    b.bodies.map Edge.source = b.bodyTrees ∧ b.certificates.map Edge.source = b.certificateTrees :=
  ⟨NativeApplyProfile.allSources (checkedSource h).profiles,
   allSources (checkedSource h).bodies,allSources (checkedSource h).certificates⟩
theorem exactCounts {sha p s b} (h : bindSection sha p s = some b) :
    b.profiles.length = b.profileTrees.length ∧ b.bodies.length = b.bodyTrees.length ∧
    b.certificates.length = b.certificateTrees.length := by
  exact ⟨by simpa using congrArg List.length (originalLists h).1,
    by simpa using congrArg List.length (originalLists h).2.1,
    by simpa using congrArg List.length (originalLists h).2.2⟩
theorem certificateChecked {sha p s b e} (h : bindSection sha p s = some b) (mem : e ∈ b.certificates) :
    check sha .finalized (expected p s b.roots.parameters.prior.plans) p.validators s.wire.parent
      b.roots.finalized b.roots.certificates b.profiles e.source = some e :=
  allChecked (checkedSource h).certificates e mem
theorem proposedChecked {sha p s b e} (h : bindSection sha p s = some b) (mem : e ∈ b.bodies) :
    check sha .proposed (expected p s b.roots.parameters.prior.plans) p.validators s.wire.parent
      b.roots.finalized b.roots.certificates b.profiles e.source = some e :=
  allChecked (checkedSource h).bodies e mem
theorem finalizedWitness {sha p s b id} (h : bindSection sha p s = some b) (mem : id ∈ b.finalized) :
    ∃ e ∈ b.certificates, e.id = id := List.mem_map.mp ((checkedSource h).sets.2.2.2.2 id mem)

theorem selectedProfile {sha p s b mode source e} (h : bindSection sha p s = some b)
    (he : check sha mode (expected p s b.roots.parameters.prior.plans) p.validators s.wire.parent
      b.roots.finalized b.roots.certificates b.profiles source = some e) :
    NativeApplyProfile.check sha e.profile.source = some e.profile :=
  NativeApplyProfile.allChecked (checkedSource h).profiles e.profile (actualParents he).2.1

theorem selectedRoot {sha p s b mode source e} (h : bindSection sha p s = some b)
    (he : check sha mode (expected p s b.roots.parameters.prior.plans) p.validators s.wire.parent
      b.roots.finalized b.roots.certificates b.profiles source = some e) :
    NativeAggregateLineage.check sha .finalized (expected p s b.roots.parameters.prior.plans) p.validators
      b.roots.parameters.prior.plans.eligibility.norms.isc.certificates b.roots.parameters.prior.plans.eligibility.norms.isc.finalized
      b.roots.parameters.prior.plans.eligibility.finalized b.roots.parameters.prior.plans.finalized b.roots.parameters.prior.finalized
      b.roots.parameters.prior.keys b.roots.parameters.prior.plans.eligibility.certificates b.roots.parameters.prior.plans.certificates
      b.roots.parameters.prior.certificates e.root.source = some e.root :=
  NativeAggregateSection.certificateChecked (checkedSource h).roots (actualParents he).1

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
end DeltaReduce.NativeApplySection
