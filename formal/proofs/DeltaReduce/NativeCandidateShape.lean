import DeltaReduce.NativeSnapshotBase

/-! All fifteen original native parent slots; requiredness is action-specific.
Wire decoding bounds and actual authority/live guards are composed separately. -/
namespace DeltaReduce.NativeCandidateShape
open NativeReceiptBytes NativePolicyCodec
open NativePolicyBytes (Policy Candidate)
open NativeVoteBytes (ContentId)
structure Parents where
  config : Bytes
  checkpoint : Bytes
  isc : Bytes
  seed : Bytes
  norm : Bytes
  ec : Bytes
  plan : Bytes
  matrix : Bytes
  root : Bytes
  profile : Bytes
  apply : Bytes
  last : Bytes
  domain : Bytes
  shard : Bytes
  reason : Bytes
  deriving DecidableEq, Repr

def value (p : Parents) : Value := .pair (.text p.config) (.pair (.text p.checkpoint) (.pair (.text p.isc) (.pair (.text p.seed) (.pair (.text p.norm) (.pair (.text p.ec) (.pair (.text p.plan) (.pair (.text p.matrix) (.pair (.text p.root) (.pair (.text p.profile) (.pair (.text p.apply) (.pair (.text p.last) (.pair (.text p.domain) (.pair (.text p.shard) (.pair (.text p.reason) (.end)))))))))))))))
def read : Value → Option Parents
  | .pair (.text config) (.pair (.text checkpoint) (.pair (.text isc) (.pair (.text seed) (.pair (.text norm) (.pair (.text ec) (.pair (.text plan) (.pair (.text matrix) (.pair (.text root) (.pair (.text profile) (.pair (.text apply) (.pair (.text last) (.pair (.text domain) (.pair (.text shard) (.pair (.text reason) (.end))))))))))))))) => some ⟨config,checkpoint,isc,seed,norm,ec,plan,matrix,root,profile,apply,last,domain,shard,reason⟩
  | _ => none
theorem readValue (p) : read (value p) = some p := by cases p; rfl
theorem original {v p} (h : read v = some p) : v = value p := by
  unfold read at h; split at h <;> try contradiction
  cases Option.some.inj h; rfl

def Required (needed hash : Bool) (v : Bytes) : Prop :=
  if needed then if hash then ContentId v else v ≠ [] else v = []
instance (needed hash v) : Decidable (Required needed hash v) := by
  unfold Required; infer_instance

def Checks (p : Policy) (c : Candidate) (r : Parents) : Prop :=
  ContentId c.body ∧ c.context ≠ [] ∧ 1 ≤ c.action ∧ c.action ≤ 9 ∧
  ContentId r.config ∧ ContentId r.checkpoint ∧ r.config = p.config ∧
  Required (c.action ∈ [3,4,5,6]) true r.isc ∧
  Required (c.action ∈ [3,4,5,6]) true r.seed ∧
  Required (c.action ∈ [3,4]) true r.norm ∧
  Required (c.action ∈ [4,5,6]) true r.ec ∧
  Required (c.action ∈ [5,6]) true r.plan ∧
  Required (c.action == 6) true r.matrix ∧
  Required (c.action == 7) true r.root ∧
  Required (c.action == 7) true r.profile ∧
  Required (c.action == 7) true r.apply ∧
  r.last = [] ∧ Required (c.action == 5) false r.domain ∧
  Required (c.action == 5) false r.shard ∧ Required (c.action == 9) false r.reason ∧
  (c.action = 1 → c.body = r.config)
instance (p c r) : Decidable (Checks p c r) := by unfold Checks; infer_instance

def check (p : Policy) (c : Candidate) : Option Parents := do
  let r ← read c.parents
  if Checks p c r then some r else none

theorem checked {p c r} (h : check p c = some r) :
    read c.parents = some r ∧ Checks p c r := by
  unfold check at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨r,hr,last⟩ := h
  split at last <;> try contradiction
  rename_i valid
  cases Option.some.inj last
  exact ⟨hr,valid⟩
theorem fromComponents {p c r} (hr : read c.parents = some r) (hc : Checks p c r) :
    check p c = some r := by simp only [check,hr,bind,Option.bind,if_pos hc]
theorem exactParents {p c r} (h : check p c = some r) : c.parents = value r :=
  original (checked h).1
theorem noSyntheticLast {p c r} (h : check p c = some r) : r.last = [] :=
  (checked h).2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2.1
theorem configuredParent {p c r} (h : check p c = some r) : r.config = p.config :=
  (checked h).2.2.2.2.2.2.2.1
theorem checkpointIsContent {p c r} (h : check p c = some r) : ContentId r.checkpoint :=
  (checked h).2.2.2.2.2.2.1
end DeltaReduce.NativeCandidateShape
