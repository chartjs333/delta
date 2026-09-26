import DeltaReduce.NativePlanSection
import DeltaReduce.NativeCertificateDecimal

/-! Exact original PARAMETER payload. Original signed decimal strings are retained;
these source guards do not derive numerators, denominator or Q leaf coverage. -/
namespace DeltaReduce.NativeParameter
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativeInputSetBody (Context contextValue readContext ContextValid contextBytes text64)
open NativeIscCertificate (quoted array object number readTexts)

structure Common where
  context : Context
  plan : Bytes
  denominator : Nat
  domain : Bytes
  ec : Bytes
  leaves : List Bytes
  isc : Bytes
  numerators : List Bytes
  shard : Bytes
  deriving DecidableEq, Repr
structure Certificate where
  common : Common
  threshold : Nat
  signers : List Bytes
  deriving DecidableEq, Repr
structure Body where
  common : Common
  voteContext : Bytes
  deriving DecidableEq, Repr
structure Key where
  domain : Bytes
  shard : Bytes
  deriving DecidableEq, Repr

def keyValue (k : Key) : Value := .pair (.text k.domain) (.pair (.text k.shard) .end)
def readKey : Value → Option Key
  | .pair (.text domain) (.pair (.text shard) .end) => some ⟨domain,shard⟩
  | _ => none
def keyLT (a b : Key) : Bool := NativePolicyBytes.bytesLT a.domain b.domain ||
  (a.domain == b.domain && NativePolicyBytes.bytesLT a.shard b.shard)
def readKeys : List Value → Option (List Key)
  | [] => some []
  | v::vs => do let k ← readKey v; let ks ← readKeys vs; some (k::ks)
theorem keyRead (k) : readKey (keyValue k) = some k := by cases k; rfl
theorem keysRead (ks) : readKeys (ks.map keyValue) = some ks := by
  induction ks with
  | nil => rfl
  | cons k ks ih => simp only [List.map_cons,readKeys,keyRead,ih,bind,Option.bind]
theorem keyOriginal {v k} (h : readKey v = some k) : v = keyValue k := by
  unfold readKey at h; split at h <;> try contradiction
  cases Option.some.inj h; rfl
theorem keysOriginal {vs ks} (h : readKeys vs = some ks) : vs = ks.map keyValue := by
  induction vs generalizing ks with
  | nil => simp [readKeys] at h; subst ks; rfl
  | cons v vs ih =>
    simp only [readKeys,bind,Option.bind_eq_some_iff] at h
    obtain ⟨k,hk,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,← keyOriginal hk,← ih hr]

def value (b : Certificate) : Value :=
  let c := b.common
  (.pair (contextValue c.context) (.pair (.text c.plan) (.pair (.number c.denominator) (.pair (.text c.domain) (.pair (.text c.ec) (.pair (.items (c.leaves.map Value.text)) (.pair (.text c.isc) (.pair (.number b.threshold) (.pair (.items (c.numerators.map Value.text)) (.pair (.text c.shard) (.pair (.items (b.signers.map Value.text)) .end)))))))))))
def read : Value → Option Certificate
  | (.pair ctx (.pair (.text plan) (.pair (.number denominator) (.pair (.text domain) (.pair (.text ec) (.pair (.items leaves) (.pair (.text isc) (.pair (.number threshold) (.pair (.items numerators) (.pair (.text shard) (.pair (.items signers) .end))))))))))) => do
    let context ← readContext ctx
    let ls ← readTexts leaves
    let ns ← readTexts numerators
    let ss ← readTexts signers
    some ⟨⟨context,plan,denominator,domain,ec,ls,isc,ns,shard⟩,threshold,ss⟩
  | _ => none

theorem valueRead (c) : read (value c) = some c := by
  cases c
  simp only [value,read,NativeInputSetBody.contextRead,NativeIscCertificate.textsRead,bind,Option.bind]
theorem readOriginal {v c} (h : read v = some c) : v = value c := by
  unfold read at h; split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨context,hcontext,ls,hls,ns,hns,ss,hss,last⟩ := h
  cases Option.some.inj last
  simp only [value,← NativeInputSetBody.contextOriginal hcontext,← NativeIscCertificate.textsOriginal hls,← NativeIscCertificate.textsOriginal hns,← NativeIscCertificate.textsOriginal hss]

def bodyValue (b : Body) : Value :=
  let c := b.common
  (.pair (contextValue c.context) (.pair (.text c.plan) (.pair (.number c.denominator) (.pair (.text c.domain) (.pair (.text c.ec) (.pair (.items (c.leaves.map Value.text)) (.pair (.text c.isc) (.pair (.items (c.numerators.map Value.text)) (.pair (.text c.shard) (.pair (.text b.voteContext) .end))))))))))
def readBody : Value → Option Body
  | (.pair ctx (.pair (.text plan) (.pair (.number denominator) (.pair (.text domain) (.pair (.text ec) (.pair (.items leaves) (.pair (.text isc) (.pair (.items numerators) (.pair (.text shard) (.pair (.text voteContext) .end)))))))))) => do
    let context ← readContext ctx
    let ls ← readTexts leaves
    let ns ← readTexts numerators
    some ⟨⟨context,plan,denominator,domain,ec,ls,isc,ns,shard⟩,voteContext⟩
  | _ => none

theorem bodyRead (c) : readBody (bodyValue c) = some c := by
  cases c
  simp only [bodyValue,readBody,NativeInputSetBody.contextRead,NativeIscCertificate.textsRead,bind,Option.bind]
theorem bodyOriginal {v c} (h : readBody v = some c) : v = bodyValue c := by
  unfold readBody at h; split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨context,hcontext,ls,hls,ns,hns,last⟩ := h
  cases Option.some.inj last
  simp only [bodyValue,← NativeInputSetBody.contextOriginal hcontext,← NativeIscCertificate.textsOriginal hls,← NativeIscCertificate.textsOriginal hns]

def CommonValid (expected : Context) (c : Common) : Prop :=
  ContextValid c.context ∧ c.context = expected ∧
  NativeVoteBytes.ContentId c.plan ∧ NativeVoteBytes.ContentId c.ec ∧ NativeVoteBytes.ContentId c.isc ∧
  0 < c.denominator ∧ c.denominator < 256^8 ∧
  NativeConfigAdmission.Label c.domain ∧ NativeConfigAdmission.Label c.shard ∧
  0 < c.leaves.length ∧ c.leaves.length ≤ 100000 ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT c.leaves = true ∧
  (∀ x ∈ c.leaves, NativeVoteBytes.ContentId x) ∧
  0 < c.numerators.length ∧ c.numerators.length ≤ 100000 ∧
  ∀ x ∈ c.numerators, NativeCertificateDecimal.Valid false x
instance (expected c) : Decidable (CommonValid expected c) := by unfold CommonValid; infer_instance
theorem denominatorPositive {expected c} (h : CommonValid expected c) : 0 < c.denominator := h.2.2.2.2.2.1
theorem denominatorBound {expected c} (h : CommonValid expected c) : c.denominator < 256^8 := h.2.2.2.2.2.2.1
theorem leavesNonempty {expected c} (h : CommonValid expected c) : 0 < c.leaves.length := h.2.2.2.2.2.2.2.2.2.1
theorem leavesOrdered {expected c} (h : CommonValid expected c) : NativePolicyBytes.strictly NativePolicyBytes.bytesLT c.leaves = true := h.2.2.2.2.2.2.2.2.2.2.2.1
theorem resultsNonempty {expected c} (h : CommonValid expected c) : 0 < c.numerators.length := h.2.2.2.2.2.2.2.2.2.2.2.2.2.1
theorem resultsChecked {expected c} (h : CommonValid expected c) (x) (mem : x ∈ c.numerators) :
    NativeCertificateDecimal.parse false x = some (NativeCertificateDecimal.number x) :=
  NativeCertificateDecimal.fromValid (h.2.2.2.2.2.2.2.2.2.2.2.2.2.2.2 x mem)
def signerView (c : Certificate) : NativeIscCertificate.Certificate :=
  ⟨⟨c.common.context,[],[]⟩,c.threshold,c.signers⟩
def Valid (expected : Context) (committee : List Bytes) (c : Certificate) : Prop :=
  CommonValid expected c.common ∧ NativeIscCertificate.CommitteeValid committee ∧
  NativeIscCertificate.SignersValid committee (signerView c)
instance (expected committee c) : Decidable (Valid expected committee c) := by unfold Valid; infer_instance
def proposedCertificate (committee : List Bytes) (b : Body) : Certificate :=
  ⟨b.common,NativeIscCertificate.quorum committee,committee⟩
def fields (c : Certificate) : List (String × Bytes) :=
  [("aggregation_plan_certificate_id",quoted c.common.plan),
   ("arithmetic_profile_id",quoted c.common.context.arithmetic),
   ("denominator",number c.common.denominator),("domain_id",quoted c.common.domain),
   ("eligibility_certificate_id",quoted c.common.ec),
   ("formal_semantics_id",quoted NativeVoteBytes.nativeSemantics),
   ("height",number c.common.context.height),("input_leaf_ids",array (c.common.leaves.map quoted)),
   ("input_set_certificate_id",quoted c.common.isc),("parameter_schema_id",quoted c.common.context.schema),
   ("quorum_threshold",number c.threshold),("result_numerators",array (c.common.numerators.map quoted)),
   ("round_config_id",quoted c.common.context.config),("round_id",quoted c.common.context.round),
   ("schema_version",quoted (NativeVoteBytes.ascii "1.0.0")),("shard_id",quoted c.common.shard),
   ("signer_ids",array (c.signers.map quoted)),("type_name",quoted (NativeVoteBytes.ascii "PARAMETER_SHARD_QC")),
   ("validator_epoch_id",quoted c.common.context.epoch),("view",number c.common.context.view)]
def json (c : Certificate) : Bytes := object (fields c)
def domain : Bytes := NativeVoteBytes.ascii "deltareduce.008.parameter-shard-qc.v1"
def id (sha : Bytes → Bytes) (c : Certificate) : Option Bytes := NativeStateBytes.contentId sha domain (json c)
def texts64 (xs : List Bytes) : Bytes := be 8 xs.length ++ (xs.map text64).flatten
def bodyBytes (b : Body) : Bytes :=
  let c := b.common
  contextBytes c.context ++ text64 c.plan ++ be 8 c.denominator ++ text64 c.domain ++
  text64 c.ec ++ texts64 c.leaves ++ text64 c.isc ++ texts64 c.numerators ++ text64 c.shard
def bodyDomain : Bytes := NativeVoteBytes.ascii "deltareduce.vote.parameter-body.v1"
def bodyId (sha : Bytes → Bytes) (b : Body) : Option Bytes := NativeStateBytes.contentId sha bodyDomain (bodyBytes b)
theorem contextNotInBodyHash (sha b ctx) : bodyId sha {b with voteContext := ctx} = bodyId sha b := rfl
theorem contextRetained (c a b) (ne : a ≠ b) : bodyValue ⟨c,a⟩ ≠ bodyValue ⟨c,b⟩ := by
  intro eq
  have h := congrArg readBody eq
  rw [bodyRead,bodyRead] at h
  exact ne (congrArg Body.voteContext (Option.some.inj h))
def assignmentKey (b : Body) : Bytes × Key := (b.common.plan,⟨b.common.domain,b.common.shard⟩)
-- Original map/set guards, evaluated for each incoming body against prior bodies.
def AssignmentStep (prior : List Body) (b : Body) : Prop :=
  b.voteContext ≠ [] ∧
  (∀ old ∈ prior, assignmentKey old = assignmentKey b → old.voteContext = b.voteContext) ∧
  ∀ old ∈ prior, old.voteContext ≠ b.voteContext
instance (prior b) : Decidable (AssignmentStep prior b) := by unfold AssignmentStep; infer_instance
def assignments (prior : List Body) : List Body → Bool
  | [] => true
  | b::bs => decide (AssignmentStep prior b) && assignments (b::prior) bs
theorem distinctAssignment {prior b} (h : AssignmentStep prior b) (old) (mem : old ∈ prior) :
    assignmentKey old ≠ assignmentKey b := by
  intro same
  exact h.2.2 old mem (h.2.1 old mem same)
theorem assignmentHead {prior b bs} (h : assignments prior (b::bs) = true) :
    AssignmentStep prior b ∧ assignments (b::prior) bs = true := by
  simpa only [assignments,Bool.and_eq_true,decide_eq_true_eq] using h
theorem assignmentFuture {prior bs} (h : assignments prior bs = true) (b) (mem : b ∈ bs) :
    AssignmentStep prior b := by
  induction bs generalizing prior with
  | nil => simp at mem
  | cons x xs ih =>
    have step := assignmentHead h
    rcases List.mem_cons.mp mem with rfl | mem
    · exact step.1
    · have next := ih step.2 mem
      exact ⟨next.1,fun old hm => next.2.1 old (List.mem_cons_of_mem x hm),
        fun old hm => next.2.2 old (List.mem_cons_of_mem x hm)⟩
theorem assignmentsDistinct {prior bs} (h : assignments prior bs = true) :
    bs.Pairwise (fun a b => assignmentKey a ≠ assignmentKey b ∧ a.voteContext ≠ b.voteContext) := by
  induction bs generalizing prior with
  | nil => exact List.Pairwise.nil
  | cons x xs ih =>
    have step := assignmentHead h
    apply List.Pairwise.cons
    · intro b mem
      have later := assignmentFuture step.2 b mem
      exact ⟨distinctAssignment later x (List.mem_cons_self ..),later.2.2 x (List.mem_cons_self ..)⟩
    · exact ih step.2
end DeltaReduce.NativeParameter
