import DeltaReduce.NativeIscCertificate
import DeltaReduce.NativeIscAdmission

/-! Checked complete finalized-ISC section from original policy/state bytes.
This section does not validate other graph sections or authorize fresh votes. -/
namespace DeltaReduce.NativeFinalizedIscSection
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativeConfigAdmission (getText getTexts HeaderChecks)
open NativePolicyBytes (Policy)
open NativeStateBytes (State)
open NativeIscCertificate (Checked)

structure Bound where
  policy : Policy
  state : State
  schema : Bytes
  arithmetic : Bytes
  snapshotId : Bytes
  trees : List Value
  certificates : List Checked
  finalized : List Bytes

def SetChecks (b : Bound) : Prop :=
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (b.certificates.map Checked.qcId) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT b.finalized = true ∧
  ∀ id ∈ b.finalized, id ∈ b.certificates.map Checked.qcId
instance (b) : Decidable (SetChecks b) := by unfold SetChecks; infer_instance

def bindSection (sha : Bytes → Bytes) (p : Policy) (s : State) : Option Bound := do
  let snapshotId ← getText fmtSnapshot p.snapshot "state_id"
  let computed ← NativeStateBytes.contentId sha NativeStateBytes.stateDomain
    (NativeStateBytes.encodeState s.wire)
  let schema ← getText fmtSnapshot p.snapshot "parameter_schema_id"
  let arithmetic ← getText fmtSnapshot p.snapshot "arithmetic_profile_id"
  let trees ← lookup fmtSnapshot p.snapshot "input_set_certificates" >>= NativePolicyBytes.items
  let certificates ← NativeIscCertificate.checkAll sha
    (NativeIscAdmission.expected p s schema arithmetic) p.validators trees
  let finalized ← getTexts fmtSnapshot p.snapshot "finalized_input_set_ids"
  let b := Bound.mk p s schema arithmetic snapshotId trees certificates finalized
  if snapshotId = computed ∧ HeaderChecks p s ∧ NativeIscCertificate.CommitteeValid p.validators ∧
      NativeVoteBytes.ContentId schema ∧ NativeVoteBytes.ContentId arithmetic ∧ SetChecks b then
    some b
  else none

def Source (sha : Bytes → Bytes) (p : Policy) (s : State) (b : Bound) : Prop :=
  b.policy = p ∧ b.state = s ∧
  getText fmtSnapshot p.snapshot "state_id" = some b.snapshotId ∧
  NativeStateBytes.contentId sha NativeStateBytes.stateDomain
    (NativeStateBytes.encodeState s.wire) = some b.snapshotId ∧
  getText fmtSnapshot p.snapshot "parameter_schema_id" = some b.schema ∧
  getText fmtSnapshot p.snapshot "arithmetic_profile_id" = some b.arithmetic ∧
  (lookup fmtSnapshot p.snapshot "input_set_certificates" >>= NativePolicyBytes.items) = some b.trees ∧
  NativeIscCertificate.checkAll sha (NativeIscAdmission.expected p s b.schema b.arithmetic)
    p.validators b.trees = some b.certificates ∧
  getTexts fmtSnapshot p.snapshot "finalized_input_set_ids" = some b.finalized ∧
  HeaderChecks p s ∧ NativeIscCertificate.CommitteeValid p.validators ∧
  NativeVoteBytes.ContentId b.schema ∧ NativeVoteBytes.ContentId b.arithmetic ∧ SetChecks b

theorem checkedSource {sha p s b} (h : bindSection sha p s = some b) : Source sha p s b := by
  unfold bindSection at h
  simp only [Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨snapshot,hs,computed,hc,schema,hk,arithmetic,ha,trees,ht,certs,hq,finalized,hf,last⟩ := h
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  rcases checks with ⟨rfl,checks⟩
  exact ⟨rfl,rfl,hs,hc,hk,ha,
    by simpa only [Bind.bind,Option.bind_eq_some_iff] using ht,hq,hf,checks⟩

theorem fromComponents {sha p s b} (h : Source sha p s b) : bindSection sha p s = some b := by
  rcases h with ⟨rfl,rfl,snapshot,hash,schema,arithmetic,trees,certs,finalized,checks⟩
  unfold bindSection
  rw [snapshot,hash,schema,arithmetic,trees]
  dsimp only [Bind.bind,Option.bind]
  rw [certs,finalized]
  dsimp only [Bind.bind,Option.bind]
  exact if_pos ⟨rfl,checks⟩

theorem originalCertificateList {sha p s b} (h : bindSection sha p s = some b) :
    b.certificates.map Checked.source = b.trees :=
  NativeIscCertificate.allSources (checkedSource h).2.2.2.2.2.2.2.1

theorem certificateCount {sha p s b} (h : bindSection sha p s = some b) :
    b.certificates.length = b.trees.length := by
  have eq := congrArg List.length (originalCertificateList h); simpa using eq

theorem finalizedCertificate {sha p s b id} (h : bindSection sha p s = some b)
    (member : id ∈ b.finalized) :
    ∃ c ∈ b.certificates, c.qcId = id ∧ NativeIscCertificate.Source sha
      (NativeIscAdmission.expected p s b.schema b.arithmetic) p.validators c.source c := by
  have source := checkedSource h
  have sets := source.2.2.2.2.2.2.2.2.2.2.2.2.2
  obtain ⟨c,mem,eq⟩ := List.mem_map.mp (sets.2.2 id member)
  exact ⟨c,mem,eq,NativeIscCertificate.allChecked source.2.2.2.2.2.2.2.1 c mem⟩

def prepare (sha : Bytes → Bytes) (policyRaw stateRaw : Bytes) : Option Bound := do
  let (_,p) ← NativePolicyBytes.decodePolicy policyRaw
  let s ← NativeStateBytes.decodeState stateRaw
  bindSection sha p s

theorem preparedSource {sha policyRaw stateRaw b} (h : prepare sha policyRaw stateRaw = some b) :
    ∃ tree, NativePolicyBytes.decodePolicy policyRaw = some (tree,b.policy) ∧
    NativeStateBytes.decodeState stateRaw = some b.state ∧ Source sha b.policy b.state b := by
  unfold prepare at h
  simp only [Bind.bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨tree,p⟩,hp,s,hs,hb⟩ := h
  have checked := checkedSource hb
  exact ⟨tree,checked.1 ▸ hp,checked.2.1 ▸ hs,by simpa only [checked.1,checked.2.1] using checked⟩

theorem noInventedFinalized {sha p s b id} (h : bindSection sha p s = some b)
    (absent : ∀ c ∈ b.certificates, c.qcId ≠ id) : id ∉ b.finalized := by
  intro member
  obtain ⟨c,mem,eq,_⟩ := finalizedCertificate h member
  exact absent c mem eq

end DeltaReduce.NativeFinalizedIscSection
