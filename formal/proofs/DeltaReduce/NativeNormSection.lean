import DeltaReduce.NativeNormEvidence
import DeltaReduce.NativeFinalizedIscSection

/-! Whole original norm vector with computed finalized ISC parent witnesses.
This checks these two sections only, not the later graph or complete admission. -/
namespace DeltaReduce.NativeNormSection
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativePolicyBytes (Policy)
open NativeStateBytes (State)
open NativeNormEvidence (Checked)

structure Bound where
  isc : NativeFinalizedIscSection.Bound
  trees : List Value
  norms : List Checked

def Ordered (norms : List Checked) : Prop :=
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (norms.map Checked.id) = true
instance (norms) : Decidable (Ordered norms) := by unfold Ordered; infer_instance

def bindSection (sha : Bytes → Bytes) (p : Policy) (s : State) : Option Bound := do
  let isc ← NativeFinalizedIscSection.bindSection sha p s
  let trees ← lookup fmtSnapshot p.snapshot "norm_evidence" >>= NativePolicyBytes.items
  let norms ← NativeNormEvidence.checkAll sha
    (NativeIscAdmission.expected p s isc.schema isc.arithmetic) isc.finalized trees
  if Ordered norms then some ⟨isc,trees,norms⟩ else none

def Source (sha : Bytes → Bytes) (p : Policy) (s : State) (b : Bound) : Prop :=
  NativeFinalizedIscSection.bindSection sha p s = some b.isc ∧
  (lookup fmtSnapshot p.snapshot "norm_evidence" >>= NativePolicyBytes.items) = some b.trees ∧
  NativeNormEvidence.checkAll sha (NativeIscAdmission.expected p s b.isc.schema b.isc.arithmetic)
    b.isc.finalized b.trees = some b.norms ∧ Ordered b.norms

theorem checkedSource {sha p s b} (h : bindSection sha p s = some b) : Source sha p s b := by
  unfold bindSection at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨isc,hi,trees,ht,norms,hs,last⟩ := h
  split at last <;> try contradiction
  rename_i ordered
  cases Option.some.inj last
  exact ⟨hi,by simpa only [bind,Option.bind_eq_some_iff] using ht,hs,ordered⟩

theorem fromComponents {sha p s b} (h : Source sha p s b) : bindSection sha p s = some b := by
  rcases h with ⟨isc,trees,norms,ordered⟩
  unfold bindSection
  rw [isc,trees]
  dsimp only [bind,Option.bind]
  rw [norms]
  exact if_pos ordered

theorem originalNormList {sha p s b} (h : bindSection sha p s = some b) :
    b.norms.map Checked.source = b.trees := NativeNormEvidence.allSources (checkedSource h).2.2.1

theorem normCount {sha p s b} (h : bindSection sha p s = some b) :
    b.norms.length = b.trees.length := by
  have eq := congrArg List.length (originalNormList h); simpa using eq

theorem normSource {sha p s b norm} (h : bindSection sha p s = some b) (mem : norm ∈ b.norms) :
    NativeNormEvidence.Source sha (NativeIscAdmission.expected p s b.isc.schema b.isc.arithmetic)
      b.isc.finalized norm.source norm :=
  NativeNormEvidence.allChecked (checkedSource h).2.2.1 norm mem

theorem finalizedParent {sha p s b norm} (h : bindSection sha p s = some b) (mem : norm ∈ b.norms) :
    norm.evidence.isc ∈ b.isc.finalized ∧
    ∃ c ∈ b.isc.certificates, c.qcId = norm.evidence.isc ∧
      NativeIscCertificate.Source sha (NativeIscAdmission.expected p s b.isc.schema b.isc.arithmetic)
        p.validators c.source c := by
  have parent := (normSource h mem).2.2.2.2.1
  exact ⟨parent,NativeFinalizedIscSection.finalizedCertificate (checkedSource h).1 parent⟩

theorem noUnfinalizedParent {sha p s b norm} (h : bindSection sha p s = some b)
    (absent : norm.evidence.isc ∉ b.isc.finalized) : norm ∉ b.norms := by
  intro mem
  exact absent (finalizedParent h mem).1

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

end DeltaReduce.NativeNormSection
