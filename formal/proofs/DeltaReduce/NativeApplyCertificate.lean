import DeltaReduce.NativeApplyProfile

/-! Candidate and QC retain original values and decimal spellings. Structural
acceptance does not derive the arithmetic or authorize a current transition. -/
namespace DeltaReduce.NativeApplyCertificate
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativeInputSetBody (Context contextValue readContext ContextValid)
open NativeIscCertificate (quoted array object number readTexts)
structure Candidate where
  context : Context
  root : Bytes
  profile : Bytes
  model : Bytes
  modelValues : List Bytes
  optimizer : Bytes
  optimizerValues : List Bytes
  parent : Bytes
  parentOptimizer : Bytes
  deriving DecidableEq, Repr
structure Certificate where
  context : Context
  root : Bytes
  profile : Bytes
  candidate : Bytes
  model : Bytes
  optimizer : Bytes
  parent : Bytes
  threshold : Nat
  signers : List Bytes
  deriving DecidableEq, Repr
def candidateValue (c : Candidate) : Value :=
  .pair (contextValue c.context) (.pair (.text c.root) (.pair (.text c.profile) (.pair (.text c.model) (.pair (.items (c.modelValues.map Value.text)) (.pair (.text c.optimizer) (.pair (.items (c.optimizerValues.map Value.text)) (.pair (.text c.parent) (.pair (.text c.parentOptimizer) (.end)))))))))
def readCandidate : Value → Option Candidate
  | .pair (context) (.pair (.text root) (.pair (.text profile) (.pair (.text model) (.pair (.items modelValues) (.pair (.text optimizer) (.pair (.items optimizerValues) (.pair (.text parent) (.pair (.text parentOptimizer) (.end))))))))) => do
    let contextValue ← readContext context
    let modelValuesValue ← readTexts modelValues
    let optimizerValuesValue ← readTexts optimizerValues
    some ⟨contextValue,root,profile,model,modelValuesValue,optimizer,optimizerValuesValue,parent,parentOptimizer⟩
  | _ => none

theorem candidateRead (c) : readCandidate (candidateValue c) = some c := by
  cases c
  simp only [candidateValue,readCandidate,NativeInputSetBody.contextRead,NativeIscCertificate.textsRead,bind,Option.bind]
theorem candidateOriginal {v c} (h : readCandidate v = some c) : v = candidateValue c := by
  unfold readCandidate at h; split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨a0,h0,a1,h1,a2,h2,last⟩ := h
  cases Option.some.inj last
  simp only [candidateValue,← NativeInputSetBody.contextOriginal h0,← NativeIscCertificate.textsOriginal h1,← NativeIscCertificate.textsOriginal h2]

def certificateValue (c : Certificate) : Value :=
  .pair (contextValue c.context) (.pair (.text c.root) (.pair (.text c.profile) (.pair (.text c.candidate) (.pair (.text c.model) (.pair (.text c.optimizer) (.pair (.text c.parent) (.pair (.number c.threshold) (.pair (.items (c.signers.map Value.text)) (.end)))))))))
def readCertificate : Value → Option Certificate
  | .pair (context) (.pair (.text root) (.pair (.text profile) (.pair (.text candidate) (.pair (.text model) (.pair (.text optimizer) (.pair (.text parent) (.pair (.number threshold) (.pair (.items signers) (.end))))))))) => do
    let contextValue ← readContext context
    let signersValue ← readTexts signers
    some ⟨contextValue,root,profile,candidate,model,optimizer,parent,threshold,signersValue⟩
  | _ => none

theorem certificateRead (c) : readCertificate (certificateValue c) = some c := by
  cases c
  simp only [certificateValue,readCertificate,NativeInputSetBody.contextRead,NativeIscCertificate.textsRead,bind,Option.bind]
theorem certificateOriginal {v c} (h : readCertificate v = some c) : v = certificateValue c := by
  unfold readCertificate at h; split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨a0,h0,a1,h1,last⟩ := h
  cases Option.some.inj last
  simp only [certificateValue,← NativeInputSetBody.contextOriginal h0,← NativeIscCertificate.textsOriginal h1]

structure Finalized where
  certificate : Certificate
  candidate : Candidate
  deriving DecidableEq, Repr
def finalizedValue (c : Finalized) : Value :=
  .pair (certificateValue c.certificate) (.pair (candidateValue c.candidate) (.end))
def readFinalized : Value → Option Finalized
  | .pair (certificate) (.pair (candidate) (.end)) => do
    let certificateValue ← readCertificate certificate
    let candidateValue ← readCandidate candidate
    some ⟨certificateValue,candidateValue⟩
  | _ => none

theorem finalizedRead (c) : readFinalized (finalizedValue c) = some c := by
  cases c
  simp only [finalizedValue,readFinalized,certificateRead,candidateRead,bind,Option.bind]
theorem finalizedOriginal {v c} (h : readFinalized v = some c) : v = finalizedValue c := by
  unfold readFinalized at h; split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨a0,h0,a1,h1,last⟩ := h
  cases Option.some.inj last
  simp only [finalizedValue,← certificateOriginal h0,← candidateOriginal h1]

def CandidateValid (expected : Context) (c : Candidate) : Prop :=
  ContextValid c.context ∧ c.context = expected ∧
  NativeVoteBytes.ContentId c.root ∧ NativeVoteBytes.ContentId c.profile ∧
  NativeVoteBytes.ContentId c.model ∧ NativeVoteBytes.ContentId c.optimizer ∧
  NativeVoteBytes.ContentId c.parent ∧ NativeVoteBytes.ContentId c.parentOptimizer ∧
  0 < c.modelValues.length ∧ c.modelValues.length ≤ 100000 ∧
  c.optimizerValues.length = c.modelValues.length ∧
  (∀ x ∈ c.modelValues, NativeCertificateDecimal.Valid false x) ∧
  ∀ x ∈ c.optimizerValues, NativeCertificateDecimal.Valid false x
instance (expected c) : Decidable (CandidateValid expected c) := by unfold CandidateValid; infer_instance
def signerView (c : Certificate) : NativeIscCertificate.Certificate := ⟨⟨c.context,[],[]⟩,c.threshold,c.signers⟩
def CertificateValid (expected : Context) (committee : List Bytes) (c : Certificate) : Prop :=
  ContextValid c.context ∧ c.context = expected ∧
  NativeVoteBytes.ContentId c.root ∧ NativeVoteBytes.ContentId c.profile ∧
  NativeVoteBytes.ContentId c.candidate ∧ NativeVoteBytes.ContentId c.model ∧
  NativeVoteBytes.ContentId c.optimizer ∧ NativeVoteBytes.ContentId c.parent ∧
  NativeIscCertificate.CommitteeValid committee ∧ NativeIscCertificate.SignersValid committee (signerView c)
instance (expected committee c) : Decidable (CertificateValid expected committee c) := by unfold CertificateValid; infer_instance
def candidateFields (c : Candidate) : List (String × Bytes) :=
 [("aggregate_root_qc_id",quoted c.root),("apply_arithmetic_profile_id",quoted c.profile),
  ("arithmetic_profile_id",quoted c.context.arithmetic),("formal_semantics_id",quoted NativeVoteBytes.nativeSemantics),
  ("height",number c.context.height),("next_model_hash",quoted c.model),
  ("next_model_values",array (c.modelValues.map quoted)),("next_optimizer_hash",quoted c.optimizer),
  ("next_optimizer_values",array (c.optimizerValues.map quoted)),("parameter_schema_id",quoted c.context.schema),
  ("parent_checkpoint_id",quoted c.parent),("parent_optimizer_hash",quoted c.parentOptimizer),
  ("round_config_id",quoted c.context.config),("round_id",quoted c.context.round),
  ("schema_version",quoted (NativeVoteBytes.ascii "1.0.0")),("type_name",quoted (NativeVoteBytes.ascii "APPLY_CANDIDATE")),
  ("validator_epoch_id",quoted c.context.epoch),("view",number c.context.view)]
def candidateJSON (c : Candidate) := object (candidateFields c)
def candidateDomain := NativeVoteBytes.ascii "deltareduce.008.apply-candidate.v1"
def candidateId (sha : Bytes → Bytes) (c : Candidate) := NativeContractSize.contentId sha candidateDomain (candidateJSON c)
def certificateFields (c : Certificate) : List (String × Bytes) :=
 [("aggregate_root_qc_id",quoted c.root),("apply_arithmetic_profile_id",quoted c.profile),
  ("apply_candidate_id",quoted c.candidate),("arithmetic_profile_id",quoted c.context.arithmetic),
  ("formal_semantics_id",quoted NativeVoteBytes.nativeSemantics),("height",number c.context.height),
  ("next_model_hash",quoted c.model),("next_optimizer_hash",quoted c.optimizer),
  ("parameter_schema_id",quoted c.context.schema),("parent_checkpoint_id",quoted c.parent),
  ("quorum_threshold",number c.threshold),("round_config_id",quoted c.context.config),("round_id",quoted c.context.round),
  ("schema_version",quoted (NativeVoteBytes.ascii "1.0.0")),("signer_ids",array (c.signers.map quoted)),
  ("type_name",quoted (NativeVoteBytes.ascii "APPLY_QC")),("validator_epoch_id",quoted c.context.epoch),("view",number c.context.view)]
def certificateJSON (c : Certificate) := object (certificateFields c)
def certificateDomain := NativeVoteBytes.ascii "deltareduce.008.apply-qc.v1"
def certificateId (sha : Bytes → Bytes) (c : Certificate) := NativeContractSize.contentId sha certificateDomain (certificateJSON c)
def proposedCertificate (committee : List Bytes) (b : Candidate) (bid : Bytes) : Certificate :=
  ⟨b.context,b.root,b.profile,bid,b.model,b.optimizer,b.parent,NativeIscCertificate.quorum committee,committee⟩
theorem retainedValues {expected c} (h : CandidateValid expected c) :
    c.optimizerValues.length = c.modelValues.length ∧
    (∀ x ∈ c.modelValues, NativeCertificateDecimal.Valid false x) ∧
    ∀ x ∈ c.optimizerValues, NativeCertificateDecimal.Valid false x := h.2.2.2.2.2.2.2.2.2.2
theorem candidateBound {sha c cid} (h : candidateId sha c = some cid) :
    (candidateJSON c).length ≤ NativeContractSize.maxBytes ∧
    NativeStateBytes.contentId sha candidateDomain (candidateJSON c) = some cid := NativeContractSize.accepted h
theorem certificateBound {sha c cid} (h : certificateId sha c = some cid) :
    (certificateJSON c).length ≤ NativeContractSize.maxBytes ∧
    NativeStateBytes.contentId sha certificateDomain (certificateJSON c) = some cid := NativeContractSize.accepted h
end DeltaReduce.NativeApplyCertificate
