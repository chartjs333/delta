import DeltaReduce.NativeEligibilityLineage

/-! Actual finalized ISC, norm and seed checks feed complete EC lists. Later
APC/admission/replay and authenticated finalization remain outside this section. -/
namespace DeltaReduce.NativeEligibilitySection
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativePolicyBytes (Policy)
open NativeStateBytes (State)
open NativeEligibilityLineage (Mode Edge)

structure Bound where
  norms : NativeNormSection.Bound
  seedTrees : List Value
  seeds : List NativeSeedTranscript.Checked
  bodyTrees : List Value
  bodies : List Edge
  certificateTrees : List Value
  certificates : List Edge
  finalized : List Bytes

def expected (p : Policy) (s : State) (b : NativeNormSection.Bound) : NativeInputSetBody.Context :=
  NativeIscAdmission.expected p s b.isc.schema b.isc.arithmetic
def trees (p : Policy) (key : String) : Option (List Value) :=
  lookup fmtSnapshot p.snapshot key >>= NativePolicyBytes.items
def edgeList (sha : Bytes → Bytes) (p : Policy) (s : State) (norms : NativeNormSection.Bound)
    (seeds : List NativeSeedTranscript.Checked) (mode : Mode) (vs : List Value) :=
  NativeEligibilityLineage.checkAll sha mode (expected p s norms) p.validators
    norms.isc.certificates norms.isc.finalized norms.norms seeds vs
def SetChecks (b : Bound) : Prop :=
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (b.seeds.map NativeSeedTranscript.Checked.id) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (b.bodies.map Edge.id) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (b.certificates.map Edge.id) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT b.finalized = true ∧
  ∀ id ∈ b.finalized, id ∈ b.certificates.map Edge.id
instance (b) : Decidable (SetChecks b) := by unfold SetChecks; infer_instance

def bindSection (sha : Bytes → Bytes) (p : Policy) (s : State) : Option Bound := do
  let norms ← NativeNormSection.bindSection sha p s
  let seedTrees ← trees p "seed_transcripts"
  let seeds ← NativeSeedTranscript.checkAll sha (expected p s norms) norms.isc.finalized seedTrees
  let bodyTrees ← trees p "eligibility_bodies"
  let bodies ← edgeList sha p s norms seeds .proposed bodyTrees
  let certificateTrees ← trees p "eligibility_certificates"
  let certificates ← edgeList sha p s norms seeds .finalized certificateTrees
  let finalized ← NativeConfigAdmission.getTexts fmtSnapshot p.snapshot "finalized_eligibility_ids"
  let b := Bound.mk norms seedTrees seeds bodyTrees bodies certificateTrees certificates finalized
  if SetChecks b then some b else none

structure Source (sha : Bytes → Bytes) (p : Policy) (s : State) (b : Bound) : Prop where
  norms : NativeNormSection.bindSection sha p s = some b.norms
  seedTrees : trees p "seed_transcripts" = some b.seedTrees
  seeds : NativeSeedTranscript.checkAll sha (expected p s b.norms) b.norms.isc.finalized
    b.seedTrees = some b.seeds
  bodyTrees : trees p "eligibility_bodies" = some b.bodyTrees
  bodies : edgeList sha p s b.norms b.seeds .proposed b.bodyTrees = some b.bodies
  certificateTrees : trees p "eligibility_certificates" = some b.certificateTrees
  certificates : edgeList sha p s b.norms b.seeds .finalized b.certificateTrees = some b.certificates
  finalized : NativeConfigAdmission.getTexts fmtSnapshot p.snapshot "finalized_eligibility_ids" =
    some b.finalized
  sets : SetChecks b

theorem checkedSource {sha p s b} (h : bindSection sha p s = some b) : Source sha p s b := by
  unfold bindSection at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨norms,hn,st,hst,seeds,hs,bt,hbt,bodies,hb,ct,hct,certificates,hc,finalized,hf,last⟩ := h
  split at last <;> try contradiction
  rename_i sets
  cases Option.some.inj last
  exact ⟨hn,hst,hs,hbt,hb,hct,hc,hf,sets⟩

theorem fromComponents {sha p s b} (h : Source sha p s b) : bindSection sha p s = some b := by
  unfold bindSection
  rw [h.norms,h.seedTrees]
  dsimp only [bind,Option.bind]
  rw [h.seeds,h.bodyTrees]
  dsimp only [bind,Option.bind]
  rw [h.bodies,h.certificateTrees]
  dsimp only [bind,Option.bind]
  rw [h.certificates,h.finalized]
  exact if_pos h.sets

theorem originalLists {sha p s b} (h : bindSection sha p s = some b) :
    b.seeds.map NativeSeedTranscript.Checked.source = b.seedTrees ∧
    b.bodies.map Edge.source = b.bodyTrees ∧ b.certificates.map Edge.source = b.certificateTrees := by
  have src := checkedSource h
  exact ⟨NativeSeedTranscript.allSources src.seeds,
    NativeEligibilityLineage.allSources src.bodies,NativeEligibilityLineage.allSources src.certificates⟩

theorem exactCounts {sha p s b} (h : bindSection sha p s = some b) :
    b.bodies.length = b.bodyTrees.length ∧ b.certificates.length = b.certificateTrees.length := by
  have hb := congrArg List.length (originalLists h).2.1
  have hc := congrArg List.length (originalLists h).2.2
  exact ⟨by simpa using hb,by simpa using hc⟩

theorem certificateChecked {sha p s b e} (h : bindSection sha p s = some b)
    (mem : e ∈ b.certificates) :
    NativeEligibilityLineage.check sha .finalized (expected p s b.norms) p.validators
      b.norms.isc.certificates b.norms.isc.finalized b.norms.norms b.seeds e.source = some e :=
  NativeEligibilityLineage.allChecked (checkedSource h).certificates e mem

theorem proposedChecked {sha p s b e} (h : bindSection sha p s = some b)
    (mem : e ∈ b.bodies) :
    NativeEligibilityLineage.check sha .proposed (expected p s b.norms) p.validators
      b.norms.isc.certificates b.norms.isc.finalized b.norms.norms b.seeds e.source = some e :=
  NativeEligibilityLineage.allChecked (checkedSource h).bodies e mem

theorem checkedParents {sha p s b mode source e} (h : bindSection sha p s = some b)
    (edge : NativeEligibilityLineage.check sha mode (expected p s b.norms) p.validators
      b.norms.isc.certificates b.norms.isc.finalized b.norms.norms b.seeds source = some e) :
    NativeIscCertificate.Source sha (expected p s b.norms) p.validators e.parent.source e.parent ∧
    NativeNormEvidence.Source sha (expected p s b.norms) b.norms.isc.finalized e.norm.source e.norm ∧
    NativeSeedTranscript.Source sha (expected p s b.norms) b.norms.isc.finalized e.seed.source e.seed := by
  have src := checkedSource h
  have witnesses := NativeEligibilityLineage.parentWitnesses edge
  have isc := NativeFinalizedIscSection.checkedSource (NativeNormSection.checkedSource src.norms).1
  exact ⟨NativeIscCertificate.allChecked isc.2.2.2.2.2.2.2.1 e.parent witnesses.1,
    NativeNormSection.normSource src.norms witnesses.2.2.1,
    NativeSeedTranscript.allChecked src.seeds e.seed witnesses.2.2.2.2.1⟩

theorem finalizedWitness {sha p s b id} (h : bindSection sha p s = some b)
    (mem : id ∈ b.finalized) :
    ∃ e ∈ b.certificates, e.id = id ∧
      NativeEligibilityLineage.check sha .finalized (expected p s b.norms) p.validators
        b.norms.isc.certificates b.norms.isc.finalized b.norms.norms b.seeds e.source = some e := by
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
end DeltaReduce.NativeEligibilitySection
