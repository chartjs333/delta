import DeltaReduce.NativeAggregateMerkle
import DeltaReduce.NativeSizedParameterSection

/-! Entire original ROOT body/QC representation, computed Merkle and bounded JSON.
Source quorum checks are structural; no cryptographic signer authentication. -/
namespace DeltaReduce.NativeAggregateRoot
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativeInputSetBody (Context contextValue readContext ContextValid contextBytes text64)
open NativeIscCertificate (quoted array object number readTexts)
open NativeAggregateMerkle (Leaf leafJSON key)
open NativeParameter (Key keyValue readKeys keysRead keysOriginal keyLT)

structure Common where
  context : Context
  plan : Bytes
  ec : Bytes
  isc : Bytes
  leaves : List Leaf
  merkle : Bytes
  keys : List Key
  deriving DecidableEq, Repr
structure Certificate where
  common : Common
  threshold : Nat
  signers : List Bytes
  deriving DecidableEq, Repr

def leafValue (l : Leaf) : Value := .pair (.text l.domain) (.pair (.text l.qc) (.pair (.text l.shard) .end))
def readLeaf : Value → Option Leaf
  | .pair (.text domain) (.pair (.text qc) (.pair (.text shard) .end)) => some ⟨domain,qc,shard⟩
  | _ => none
def readLeaves : List Value → Option (List Leaf)
  | [] => some []
  | v::vs => do let l ← readLeaf v; let ls ← readLeaves vs; some (l::ls)
theorem leafRead (l) : readLeaf (leafValue l) = some l := by cases l; rfl
theorem leavesRead (ls) : readLeaves (ls.map leafValue) = some ls := by
  induction ls with
  | nil => rfl
  | cons l ls ih => simp only [List.map_cons,readLeaves,leafRead,ih,bind,Option.bind]
theorem leafOriginal {v l} (h : readLeaf v = some l) : v = leafValue l := by
  unfold readLeaf at h; split at h <;> try contradiction
  cases Option.some.inj h; rfl
theorem leavesOriginal {vs ls} (h : readLeaves vs = some ls) : vs = ls.map leafValue := by
  induction vs generalizing ls with
  | nil => simp [readLeaves] at h; subst ls; rfl
  | cons v vs ih =>
    simp only [readLeaves,bind,Option.bind_eq_some_iff] at h
    obtain ⟨l,hl,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,← leafOriginal hl,← ih hr]

def bodyValue (c : Common) : Value :=
  (.pair (contextValue c.context) (.pair (.text c.plan) (.pair (.text c.ec) (.pair (.text c.isc) (.pair (.items (c.leaves.map leafValue)) (.pair (.text c.merkle) (.pair (.items (c.keys.map keyValue)) .end)))))))
def readBody : Value → Option Common
  | (.pair ctx (.pair (.text plan) (.pair (.text ec) (.pair (.text isc) (.pair (.items leaves) (.pair (.text merkle) (.pair (.items keys) .end))))))) => do
    let context ← readContext ctx
    let ls ← readLeaves leaves
    let ks ← readKeys keys
    some ⟨context,plan,ec,isc,ls,merkle,ks⟩
  | _ => none
theorem bodyRead (c) : readBody (bodyValue c) = some c := by
  cases c
  simp only [bodyValue,readBody,NativeInputSetBody.contextRead,leavesRead,keysRead,bind,Option.bind]
theorem bodyOriginal {v c} (h : readBody v = some c) : v = bodyValue c := by
  unfold readBody at h; split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨context,hctx,ls,hl,ks,hk,last⟩ := h
  cases Option.some.inj last
  simp only [bodyValue,← NativeInputSetBody.contextOriginal hctx,← leavesOriginal hl,← keysOriginal hk]

def value (b : Certificate) : Value :=
  let c := b.common
  (.pair (contextValue c.context) (.pair (.text c.plan) (.pair (.text c.ec) (.pair (.text c.isc) (.pair (.items (c.leaves.map leafValue)) (.pair (.text c.merkle) (.pair (.number b.threshold) (.pair (.items (c.keys.map keyValue)) (.pair (.items (b.signers.map Value.text)) .end)))))))))
def read : Value → Option Certificate
  | (.pair ctx (.pair (.text plan) (.pair (.text ec) (.pair (.text isc) (.pair (.items leaves) (.pair (.text merkle) (.pair (.number threshold) (.pair (.items keys) (.pair (.items signers) .end))))))))) => do
    let context ← readContext ctx
    let ls ← readLeaves leaves
    let ks ← readKeys keys
    let ss ← readTexts signers
    some ⟨⟨context,plan,ec,isc,ls,merkle,ks⟩,threshold,ss⟩
  | _ => none
theorem certRead (c) : read (value c) = some c := by
  cases c
  simp only [value,read,NativeInputSetBody.contextRead,leavesRead,keysRead,NativeIscCertificate.textsRead,bind,Option.bind]
theorem certOriginal {v c} (h : read v = some c) : v = value c := by
  unfold read at h; split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨context,hctx,ls,hl,ks,hk,ss,hss,last⟩ := h
  cases Option.some.inj last
  simp only [value,← NativeInputSetBody.contextOriginal hctx,← leavesOriginal hl,← keysOriginal hk,← NativeIscCertificate.textsOriginal hss]

def CommonValid (expected : Context) (c : Common) : Prop :=
  ContextValid c.context ∧ c.context = expected ∧
  NativeVoteBytes.ContentId c.plan ∧ NativeVoteBytes.ContentId c.ec ∧
  NativeVoteBytes.ContentId c.isc ∧ NativeVoteBytes.ContentId c.merkle ∧
  0 < c.leaves.length ∧ c.leaves.length ≤ 100000 ∧
  0 < c.keys.length ∧ c.keys.length ≤ 100000 ∧
  NativePolicyBytes.strictly keyLT (c.leaves.map key) = true ∧
  NativePolicyBytes.strictly keyLT c.keys = true ∧
  (∀ l ∈ c.leaves, NativeAggregateMerkle.LeafValid l) ∧
  ∀ k ∈ c.keys, NativeConfigAdmission.Label k.domain ∧ NativeConfigAdmission.Label k.shard
instance (expected c) : Decidable (CommonValid expected c) := by unfold CommonValid; infer_instance

def signerView (c : Certificate) : NativeIscCertificate.Certificate :=
  ⟨⟨c.common.context,[],[]⟩,c.threshold,c.signers⟩

def Valid (expected : Context) (committee : List Bytes) (c : Certificate) : Prop :=
  CommonValid expected c.common ∧ NativeIscCertificate.CommitteeValid committee ∧
  NativeIscCertificate.SignersValid committee (signerView c)
instance (expected committee c) : Decidable (Valid expected committee c) := by unfold Valid; infer_instance

def proposedCertificate (committee : List Bytes) (b : Common) : Certificate :=
  ⟨b,NativeIscCertificate.quorum committee,committee⟩
def keyJSON (k : Key) : Bytes := object [("domain_id",quoted k.domain),("shard_id",quoted k.shard)]
def fields (c : Certificate) : List (String × Bytes) :=
  [("aggregation_plan_certificate_id",quoted c.common.plan),
   ("arithmetic_profile_id",quoted c.common.context.arithmetic),
   ("eligibility_certificate_id",quoted c.common.ec),
   ("formal_semantics_id",quoted NativeVoteBytes.nativeSemantics),("height",number c.common.context.height),
   ("input_set_certificate_id",quoted c.common.isc),("leaves",array (c.common.leaves.map leafJSON)),
   ("merkle_root",quoted c.common.merkle),("parameter_schema_id",quoted c.common.context.schema),
   ("quorum_threshold",number c.threshold),("required_keys",array (c.common.keys.map keyJSON)),
   ("round_config_id",quoted c.common.context.config),("round_id",quoted c.common.context.round),
   ("schema_version",quoted (NativeVoteBytes.ascii "1.0.0")),("signer_ids",array (c.signers.map quoted)),
   ("type_name",quoted (NativeVoteBytes.ascii "AGGREGATE_ROOT_QC")),
   ("validator_epoch_id",quoted c.common.context.epoch),("view",number c.common.context.view)]
def json (c : Certificate) : Bytes := object (fields c)
def domain : Bytes := NativeVoteBytes.ascii "deltareduce.008.aggregate-root-qc.v1"
def id (sha : Bytes → Bytes) (c : Certificate) : Option Bytes := do
  let merkle ← NativeAggregateMerkle.root sha c.common.leaves
  if merkle = c.common.merkle then NativeContractSize.contentId sha domain (json c) else none

def leafBytes (l : Leaf) : Bytes := text64 l.domain ++ text64 l.qc ++ text64 l.shard
def keyBytes (k : Key) : Bytes := text64 k.domain ++ text64 k.shard
def bodyBytes (c : Common) : Bytes :=
  contextBytes c.context ++ text64 c.plan ++ text64 c.ec ++ text64 c.isc ++
  be 8 c.leaves.length ++ (c.leaves.map leafBytes).flatten ++ text64 c.merkle ++
  be 8 c.keys.length ++ (c.keys.map keyBytes).flatten
def bodyDomain : Bytes := NativeVoteBytes.ascii "deltareduce.vote.aggregate-root-body.v1"
def bodyId (sha : Bytes → Bytes) (c : Common) : Option Bytes :=
  NativeStateBytes.contentId sha bodyDomain (bodyBytes c)

theorem checkedIdentity {sha c cid} (h : id sha c = some cid) :
    NativeAggregateMerkle.root sha c.common.leaves = some c.common.merkle ∧
    (json c).length ≤ NativeContractSize.maxBytes ∧
    NativeStateBytes.contentId sha domain (json c) = some cid := by
  unfold id at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨merkle,hm,last⟩ := h
  split at last <;> try contradiction
  rename_i equal
  subst merkle
  exact ⟨hm,NativeContractSize.accepted last⟩

theorem identityFromComponents {sha c cid}
    (hm : NativeAggregateMerkle.root sha c.common.leaves = some c.common.merkle)
    (hb : (json c).length ≤ NativeContractSize.maxBytes)
    (hh : NativeStateBytes.contentId sha domain (json c) = some cid) : id sha c = some cid := by
  simp only [id,hm,bind,Option.bind,ite_true,NativeContractSize.fromComponents hb hh]

theorem wrongMerkle {sha c computed} (hm : NativeAggregateMerkle.root sha c.common.leaves = some computed)
    (ne : computed ≠ c.common.merkle) : id sha c = none := by simp only [id,hm,bind,Option.bind,if_neg ne]

end DeltaReduce.NativeAggregateRoot
