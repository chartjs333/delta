import DeltaReduce.NativeApplySection

/-! Exact typed current-pointer command and original low-level store decision.
Structural content-ID checks are not certificate authentication. The finalized
snapshot bridge is separate and retains its source/crypto premises. -/
namespace DeltaReduce.NativeCurrentPointer
open NativeReceiptBytes NativeInputSetBody NativeApplyCertificate
open NativeIscCertificate (quoted number object)
open NativeVoteBytes (ContentId)

structure Command where
  context : Context
  qc : Bytes
  parent : Bytes
  checkpoint : Bytes
  optimizer : Bytes
  deriving DecidableEq, Repr
structure State where
  checkpoint : Bytes
  optimizer : Bytes
  qc : Bytes
  height : Nat
  deriving DecidableEq, Repr

def StateValid (s : State) : Prop :=
  ContentId s.checkpoint ∧ ContentId s.optimizer ∧
  (s.qc = [] ∨ ContentId s.qc) ∧ s.height < 256^8
instance (s) : Decidable (StateValid s) := by unfold StateValid; infer_instance
def CommandValid (c : Command) : Prop :=
  ContextValid c.context ∧ ContentId c.qc ∧ ContentId c.parent ∧
  ContentId c.checkpoint ∧ ContentId c.optimizer
instance (c) : Decidable (CommandValid c) := by unfold CommandValid; infer_instance

-- canonical_json(ApplyQc) checks signer shape, not the configured committee.
def QcShape (q : Certificate) : Prop :=
  ContextValid q.context ∧ ContentId q.root ∧ ContentId q.profile ∧
  ContentId q.candidate ∧ ContentId q.model ∧ ContentId q.optimizer ∧ ContentId q.parent ∧
  0 < q.threshold ∧ q.threshold < 256^4 ∧ q.threshold ≤ q.signers.length ∧
  q.signers.length ≤ 100000 ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT q.signers = true ∧
  ∀ signer ∈ q.signers, NativeConfigAdmission.Label signer
instance (q) : Decidable (QcShape q) := by unfold QcShape; infer_instance

def fields (c : Command) : List (String × Bytes) :=
 [("apply_qc_id",quoted c.qc),("arithmetic_profile_id",quoted c.context.arithmetic),
  ("expected_parent_checkpoint_id",quoted c.parent),
  ("formal_semantics_id",quoted NativeVoteBytes.nativeSemantics),
  ("height",number c.context.height),("next_checkpoint_id",quoted c.checkpoint),
  ("next_optimizer_hash",quoted c.optimizer),("parameter_schema_id",quoted c.context.schema),
  ("round_config_id",quoted c.context.config),("round_id",quoted c.context.round),
  ("schema_version",quoted (NativeVoteBytes.ascii "1.0.0")),
  ("type_name",quoted (NativeVoteBytes.ascii "CURRENT_POINTER_COMMAND")),
  ("validator_epoch_id",quoted c.context.epoch),("view",number c.context.view)]
def json (c : Command) : Bytes := object (fields c)
def domain : Bytes := NativeVoteBytes.ascii "deltareduce.008.current-pointer-command.v1"
def commandId (sha : Bytes → Bytes) (c : Command) : Option Bytes :=
  if CommandValid c then NativeContractSize.contentId sha domain (json c) else none
def qcId (sha : Bytes → Bytes) (q : Certificate) : Option Bytes :=
  if QcShape q then certificateId sha q else none
def Links (c : Command) (q : Certificate) (qid : Bytes) : Prop :=
  c.qc = qid ∧ c.context = q.context ∧ c.parent = q.parent ∧
  c.checkpoint = q.model ∧ c.optimizer = q.optimizer
instance (c q qid) : Decidable (Links c q qid) := by unfold Links; infer_instance
structure Prepared where
  command : Command
  certificate : Certificate
  commandId : Bytes
  qcId : Bytes
  deriving DecidableEq, Repr
def prepare (sha : Bytes → Bytes) (c : Command) (q : Certificate) : Option Prepared := do
  let cid ← commandId sha c
  let qid ← qcId sha q
  if Links c q qid then some ⟨c,q,cid,qid⟩ else none
structure Source (sha : Bytes → Bytes) (c : Command) (q : Certificate) (p : Prepared) : Prop where
  command : p.command = c
  certificate : p.certificate = q
  commandHash : commandId sha c = some p.commandId
  certificateHash : qcId sha q = some p.qcId
  links : Links c q p.qcId
theorem preparedSource {sha c q p} (h : prepare sha c q = some p) : Source sha c q p := by
  unfold prepare at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨cid,hc,qid,hq,last⟩ := h
  split at last <;> try contradiction
  rename_i hl
  cases Option.some.inj last
  exact ⟨rfl,rfl,hc,hq,hl⟩
theorem fromComponents {sha c q p} (h : Source sha c q p) : prepare sha c q = some p := by
  unfold prepare
  rw [h.commandHash]
  dsimp only [bind,Option.bind]
  rw [h.certificateHash]
  dsimp only [bind,Option.bind]
  rw [if_pos h.links,← h.command,← h.certificate]
theorem commandChecked {sha c id} (h : commandId sha c = some id) :
    CommandValid c ∧ (json c).length ≤ NativeContractSize.maxBytes ∧
    NativeStateBytes.contentId sha domain (json c) = some id := by
  unfold commandId at h
  split at h <;> try contradiction
  exact ⟨by assumption,NativeContractSize.accepted h⟩
theorem qcChecked {sha q id} (h : qcId sha q = some id) :
    QcShape q ∧ certificateId sha q = some id := by
  unfold qcId at h
  split at h <;> try contradiction
  exact ⟨by assumption,h⟩
theorem certificateImpliesShape {expected committee q} (h : CertificateValid expected committee q) : QcShape q := by
  rcases h with ⟨ctx,_,root,profile,candidate,model,optimizer,parent,_,signers⟩
  rcases signers with ⟨positive,bound,_,count,maxCount,ordered,members⟩
  exact ⟨ctx,root,profile,candidate,model,optimizer,parent,positive,bound,count,maxCount,ordered,
    fun signer mem => (members signer mem).1⟩

def next (p : Prepared) : State :=
  ⟨p.command.checkpoint,p.command.optimizer,p.qcId,p.command.context.height⟩
def ReplayMatches (s : State) (p : Prepared) : Prop :=
  s.checkpoint = p.command.checkpoint ∧ s.optimizer = p.command.optimizer ∧
  s.height = p.command.context.height
instance (s p) : Decidable (ReplayMatches s p) := by unfold ReplayMatches; infer_instance
def Extends (s : State) (p : Prepared) : Prop :=
  p.command.parent = s.checkpoint ∧ s.height < p.command.context.height
instance (s p) : Decidable (Extends s p) := by unfold Extends; infer_instance
inductive Disposition where | advanced | replay deriving DecidableEq, Repr
def choose (s : State) (p : Prepared) : Option Disposition :=
  if s.qc = p.qcId then
    if ReplayMatches s p then some .replay else none
  else if Extends s p then some .advanced else none
theorem replayBeforeCas {s p} (same : s.qc = p.qcId) (hm : ReplayMatches s p) :
    choose s p = some .replay := by simp only [choose,if_pos same,if_pos hm]
theorem replayExact {s p} (h : choose s p = some .replay) :
    s.qc = p.qcId ∧ ReplayMatches s p ∧ s = next p := by
  unfold choose at h
  split at h
  · rename_i same
    split at h
    · rename_i hm
      refine ⟨same,hm,?_⟩
      cases s
      simp only [ReplayMatches] at hm
      rcases hm with ⟨rfl,rfl,rfl⟩
      simp_all [next]
    · contradiction
  · split at h <;> contradiction
theorem freshExact {s p} (h : choose s p = some .advanced) :
    s.qc ≠ p.qcId ∧ Extends s p := by
  unfold choose at h
  split at h
  · split at h <;> contradiction
  · rename_i different
    split at h <;> try contradiction
    exact ⟨different,by assumption⟩
theorem freshFromComponents {s p} (different : s.qc ≠ p.qcId) (hext : Extends s p) :
    choose s p = some .advanced := by simp only [choose,if_neg different,if_pos hext]
theorem replayAfterAdvance (p) : choose (next p) p = some .replay := replayBeforeCas rfl ⟨rfl,rfl,rfl⟩
theorem nextValid {sha c q p} (h : prepare sha c q = some p) : StateValid (next p) := by
  have src := preparedSource h
  have valid := (commandChecked src.commandHash).1
  unfold StateValid next
  rw [src.command]
  exact ⟨valid.2.2.2.1,valid.2.2.2.2,Or.inr (src.links.1 ▸ valid.2.1),valid.1.2.2.1⟩

-- Original complete APPLY bound and finalized membership, not crypto authority.
structure Finalized where
  bound : NativeApplySection.Bound
  edge : NativeApplyLineage.Edge
  prepared : Prepared
def fromFinalized (sha : Bytes → Bytes) (policy : NativePolicyBytes.Policy)
    (state : NativeStateBytes.State) (c : Command) : Option Finalized := do
  let bound ← NativeApplySection.bindSection sha policy state
  let edge ← bound.certificates.find? (fun e => e.id == c.qc)
  if c.qc ∈ bound.finalized then
    let p ← prepare sha c edge.decoded.certificate
    some ⟨bound,edge,p⟩
  else none
theorem finalizedSource {sha policy state c out} (h : fromFinalized sha policy state c = some out) :
    NativeApplySection.bindSection sha policy state = some out.bound ∧
    out.edge ∈ out.bound.certificates ∧ c.qc ∈ out.bound.finalized ∧
    prepare sha c out.edge.decoded.certificate = some out.prepared := by
  unfold fromFinalized at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨bound,hs,edge,he,last⟩ := h
  split at last <;> try contradiction
  rename_i finalized
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨p,hp,last⟩ := last
  cases Option.some.inj last
  exact ⟨hs,List.mem_of_find?_eq_some he,finalized,hp⟩
theorem finalizedCandidate {sha policy state c out} (h : fromFinalized sha policy state c = some out) :
    out.edge.decoded.certificate.candidate = out.edge.decoded.candidateId ∧
    c.checkpoint = out.edge.decoded.candidate.model ∧
    c.optimizer = out.edge.decoded.candidate.optimizer ∧ c.parent = state.wire.parent := by
  have src := finalizedSource h
  have checked := NativeApplySection.certificateChecked src.1 src.2.1
  have fields := NativeApplyLineage.certifiedFields checked
  have links := (preparedSource src.2.2.2).links
  exact ⟨fields.1,links.2.2.2.1.trans fields.2.2.1,
    links.2.2.2.2.trans fields.2.2.2,
    links.2.2.1.trans (fields.2.1.trans (NativeApplyLineage.exactCurrent checked))⟩
end DeltaReduce.NativeCurrentPointer
