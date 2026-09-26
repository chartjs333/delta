import DeltaReduce.NativeNormEvidence
import DeltaReduce.NativeSeedTranscript

/-! Complete native EC certificate and body. Gamma uses integer wire bits, not
decimal source spelling. This layer does not authenticate or derive decisions. -/
namespace DeltaReduce.NativeEligibility
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativeInputSetBody (Context contextValue readContext ContextValid contextBytes text64)
open NativeIscCertificate (quoted array object number readTexts)

structure Entry where
  accepted : Nat
  domain : Bytes
  numerator : Nat
  denominator : Nat
  reason : Bytes
  ticket : Bytes
  deriving DecidableEq, Repr
structure Common where
  context : Context
  entries : List Entry
  isc : Bytes
  norm : Bytes
  robust : Bytes
  deriving DecidableEq, Repr
structure Certificate where
  common : Common
  threshold : Nat
  signers : List Bytes
  deriving DecidableEq, Repr
structure Body where
  common : Common
  seed : Bytes
  deriving DecidableEq, Repr

def entryValue (e : Entry) : Value :=
  .pair (.number e.accepted) (.pair (.text e.domain)
    (.pair (.pair (.number e.numerator) (.pair (.number e.denominator) .end))
      (.pair (.text e.reason) (.pair (.text e.ticket) .end))))
def readEntry : Value → Option Entry
  | .pair (.number accepted) (.pair (.text domain)
    (.pair (.pair (.number numerator) (.pair (.number denominator) .end))
      (.pair (.text reason) (.pair (.text ticket) .end)))) =>
    some ⟨accepted,domain,numerator,denominator,reason,ticket⟩
  | _ => none
def readEntries : List Value → Option (List Entry)
  | [] => some []
  | v::vs => do let e ← readEntry v; let es ← readEntries vs; some (e::es)

def value (c : Certificate) : Value := .pair (contextValue c.common.context)
  (.pair (.items (c.common.entries.map entryValue)) (.pair (.text c.common.isc)
    (.pair (.text c.common.norm) (.pair (.number c.threshold) (.pair (.text c.common.robust)
      (.pair (.items (c.signers.map Value.text)) .end))))))
def read : Value → Option Certificate
  | .pair ctx (.pair (.items entries) (.pair (.text isc) (.pair (.text norm)
      (.pair (.number threshold) (.pair (.text robust) (.pair (.items signers) .end)))))) => do
    let c ← readContext ctx
    let es ← readEntries entries
    let ss ← readTexts signers
    some ⟨⟨c,es,isc,norm,robust⟩,threshold,ss⟩
  | _ => none
def bodyValue (b : Body) : Value := .pair (contextValue b.common.context)
  (.pair (.items (b.common.entries.map entryValue)) (.pair (.text b.common.isc)
    (.pair (.text b.common.norm) (.pair (.text b.common.robust) (.pair (.text b.seed) .end)))))
def readBody : Value → Option Body
  | .pair ctx (.pair (.items entries) (.pair (.text isc) (.pair (.text norm)
      (.pair (.text robust) (.pair (.text seed) .end))))) => do
    let c ← readContext ctx
    let es ← readEntries entries
    some ⟨⟨c,es,isc,norm,robust⟩,seed⟩
  | _ => none

theorem entryRead (e) : readEntry (entryValue e) = some e := by cases e; rfl
theorem entriesRead (es) : readEntries (es.map entryValue) = some es := by
  induction es with
  | nil => rfl
  | cons e es ih => simp only [List.map_cons,readEntries,entryRead,ih,bind,Option.bind]
theorem entryOriginal {v e} (h : readEntry v = some e) : v = entryValue e := by
  unfold readEntry at h; split at h <;> try contradiction
  cases Option.some.inj h; rfl
theorem entriesOriginal {vs es} (h : readEntries vs = some es) : vs = es.map entryValue := by
  induction vs generalizing es with
  | nil => simp [readEntries] at h; subst es; rfl
  | cons v vs ih =>
    simp only [readEntries,bind,Option.bind_eq_some_iff] at h
    obtain ⟨e,he,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,← entryOriginal he,← ih hr]
theorem valueRead (c) : read (value c) = some c := by
  cases c
  simp only [value,read,NativeInputSetBody.contextRead,entriesRead,
    NativeIscCertificate.textsRead,bind,Option.bind]
theorem readOriginal {v c} (h : read v = some c) : v = value c := by
  unfold read at h; split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,hc,es,hs,ss,hss,last⟩ := h
  cases Option.some.inj last
  simp only [value,← NativeInputSetBody.contextOriginal hc,← entriesOriginal hs,
    ← NativeIscCertificate.textsOriginal hss]
theorem bodyRead (b) : readBody (bodyValue b) = some b := by
  cases b
  simp only [bodyValue,readBody,NativeInputSetBody.contextRead,entriesRead,bind,Option.bind]
theorem bodyOriginal {v b} (h : readBody v = some b) : v = bodyValue b := by
  unfold readBody at h; split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,hc,es,hs,last⟩ := h
  cases Option.some.inj last
  simp only [bodyValue,← NativeInputSetBody.contextOriginal hc,← entriesOriginal hs]

-- The lower uint64 half represents nonnegative int64. Negative gamma is rejected.
def EntryValid (e : Entry) : Prop :=
  e.accepted ≤ 1 ∧ NativeConfigAdmission.Label e.domain ∧
  e.numerator < 2^63 ∧ 0 < e.denominator ∧ e.denominator < 256^8 ∧
  Nat.gcd e.numerator e.denominator = 1 ∧ NativeConfigAdmission.Label e.reason ∧
  NativeConfigAdmission.Label e.ticket
instance (e) : Decidable (EntryValid e) := by unfold EntryValid; infer_instance
def CommonValid (expected : Context) (c : Common) : Prop :=
  ContextValid c.context ∧ c.context = expected ∧ NativeVoteBytes.ContentId c.isc ∧
  NativeVoteBytes.ContentId c.norm ∧ NativeVoteBytes.ContentId c.robust ∧
  0 < c.entries.length ∧ c.entries.length ≤ 100000 ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (c.entries.map Entry.ticket) = true ∧
  ∀ e ∈ c.entries, EntryValid e
instance (expected c) : Decidable (CommonValid expected c) := by unfold CommonValid; infer_instance
-- Only the existing signer predicate consumes this view; its body is never hashed.
def signerView (c : Certificate) : NativeIscCertificate.Certificate :=
  ⟨⟨c.common.context,[],[]⟩,c.threshold,c.signers⟩
def Valid (expected : Context) (committee : List Bytes) (c : Certificate) : Prop :=
  CommonValid expected c.common ∧ NativeIscCertificate.CommitteeValid committee ∧
  NativeIscCertificate.SignersValid committee (signerView c)
instance (expected committee c) : Decidable (Valid expected committee c) := by
  unfold Valid; infer_instance
def Membership (c : Common) (parent : NativeIscCertificate.Checked) : Prop :=
  c.isc = parent.qcId ∧ c.entries.map (fun e => (e.ticket,e.domain)) =
    parent.certificate.body.tuples.map (fun t => (t.ticket,t.domain))
instance (c parent) : Decidable (Membership c parent) := by unfold Membership; infer_instance

def entryJSON (e : Entry) : Bytes := object
  [("accepted",NativeVoteBytes.ascii (if e.accepted = 0 then "false" else "true")),
   ("domain_id",quoted e.domain),("gamma",object [("denominator",number e.denominator),
   ("numerator",quoted (number e.numerator))]),("reason_code",quoted e.reason),
   ("ticket_id",quoted e.ticket)]
def fields (c : Certificate) : List (String × Bytes) :=
  [("arithmetic_profile_id",quoted c.common.context.arithmetic),
   ("entries",array (c.common.entries.map entryJSON)),
   ("formal_semantics_id",quoted NativeVoteBytes.nativeSemantics),
   ("height",number c.common.context.height),("input_set_certificate_id",quoted c.common.isc),
   ("norm_evidence_id",quoted c.common.norm),("parameter_schema_id",quoted c.common.context.schema),
   ("quorum_threshold",number c.threshold),("robust_profile_id",quoted c.common.robust),
   ("round_config_id",quoted c.common.context.config),("round_id",quoted c.common.context.round),
   ("schema_version",quoted (NativeVoteBytes.ascii "1.0.0")),
   ("signer_ids",array (c.signers.map quoted)),
   ("type_name",quoted (NativeVoteBytes.ascii "ELIGIBILITY_CERTIFICATE")),
   ("validator_epoch_id",quoted c.common.context.epoch),("view",number c.common.context.view)]
def json (c : Certificate) : Bytes := object (fields c)
def domain : Bytes := NativeVoteBytes.ascii "deltareduce.008.eligibility-certificate.v1"
def id (sha : Bytes → Bytes) (c : Certificate) : Option Bytes :=
  NativeStateBytes.contentId sha domain (json c)
def entryBytes (e : Entry) : Bytes := be 1 e.accepted ++ text64 e.domain ++
  be 8 e.numerator ++ be 8 e.denominator ++ text64 e.reason ++ text64 e.ticket
def bodyBytes (b : Body) : Bytes := contextBytes b.common.context ++
  be 8 b.common.entries.length ++ (b.common.entries.map entryBytes).flatten ++
  text64 b.common.isc ++ text64 b.common.norm ++ text64 b.common.robust ++ text64 b.seed
def bodyDomain : Bytes := NativeVoteBytes.ascii "deltareduce.vote.eligibility-body.v1"
def bodyId (sha : Bytes → Bytes) (b : Body) : Option Bytes :=
  NativeStateBytes.contentId sha bodyDomain (bodyBytes b)
def proposedCertificate (committee : List Bytes) (b : Body) : Certificate :=
  ⟨b.common,NativeIscCertificate.quorum committee,committee⟩

structure Checked where
  certificate : Certificate
  source : Value
  qcId : Bytes
def check (sha : Bytes → Bytes) (expected : Context) (committee : List Bytes)
    (parent : NativeIscCertificate.Checked) (normId : Bytes) (source : Value) : Option Checked := do
  let c ← read source
  if Valid expected committee c ∧ Membership c.common parent ∧ c.common.norm = normId then
    let qc ← id sha c
    some ⟨c,source,qc⟩
  else none
def Source (sha : Bytes → Bytes) (expected : Context) (committee : List Bytes)
    (parent : NativeIscCertificate.Checked) (normId : Bytes) (source : Value) (out : Checked) : Prop :=
  out.source = source ∧ read source = some out.certificate ∧ source = value out.certificate ∧
  Valid expected committee out.certificate ∧ Membership out.certificate.common parent ∧
  out.certificate.common.norm = normId ∧ id sha out.certificate = some out.qcId

theorem checkedSource {sha expected committee parent normId source out}
    (h : check sha expected committee parent normId source = some out) :
    Source sha expected committee parent normId source out := by
  unfold check at h
  cases hr : read source with
  | none => simp [hr] at h
  | some c =>
    simp only [hr,bind,Option.bind] at h
    split at h <;> try contradiction
    rename_i checks
    cases hi : id sha c with
    | none => simp [hi] at h
    | some qc =>
      simp only [hi] at h
      cases Option.some.inj h
      exact ⟨rfl,hr,readOriginal hr,checks.1,checks.2.1,checks.2.2,hi⟩
theorem fromComponents {sha expected committee parent normId source c qc}
    (parsed : read source = some c) (valid : Valid expected committee c)
    (membership : Membership c.common parent) (norm : c.common.norm = normId)
    (hashed : id sha c = some qc) :
    check sha expected committee parent normId source = some ⟨c,source,qc⟩ := by
  have checks := And.intro valid (And.intro membership norm)
  simp only [check,parsed,bind,Option.bind,if_pos checks,hashed]
theorem wrongMembershipRejected {sha expected committee parent normId source c}
    (parsed : read source = some c) (invalid : ¬ Membership c.common parent) :
    check sha expected committee parent normId source = none := by simp [check,parsed,invalid]
theorem wrongShapeRejected {sha expected committee parent normId source c}
    (parsed : read source = some c) (invalid : ¬ Valid expected committee c) :
    check sha expected committee parent normId source = none := by simp [check,parsed,invalid]
theorem exactMembers {sha expected committee parent normId source out}
    (h : check sha expected committee parent normId source = some out) :
    out.certificate.common.entries.map (fun e => (e.ticket,e.domain)) =
      parent.certificate.body.tuples.map (fun t => (t.ticket,t.domain)) :=
  (checkedSource h).2.2.2.2.1.2
theorem exactMemberCount {sha expected committee parent normId source out}
    (h : check sha expected committee parent normId source = some out) :
    out.certificate.common.entries.length = parent.certificate.body.tuples.length := by
  have eq := congrArg List.length (exactMembers h); simpa using eq
theorem exactMemberPosition {sha expected committee parent normId source out}
    (h : check sha expected committee parent normId source = some out) (i : Nat) :
    (out.certificate.common.entries.map (fun e => (e.ticket,e.domain)))[i]? =
      (parent.certificate.body.tuples.map (fun t => (t.ticket,t.domain)))[i]? :=
  congrArg (fun xs => xs[i]?) (exactMembers h)

def fromBytes (sha : Bytes → Bytes) (expected : Context) (committee : List Bytes)
    (parent : NativeIscCertificate.Checked) (normId raw : Bytes) : Option Checked := do
  if raw.length ≤ 4*1024*1024 then
    let tree ← NativePolicyCodec.decode fmtEligibility raw
    check sha expected committee parent normId tree
  else none
theorem bytesSource {sha expected committee parent normId raw out}
    (h : fromBytes sha expected committee parent normId raw = some out) :
    raw.length ≤ 4*1024*1024 ∧ encode fmtEligibility out.source = some raw ∧
    Source sha expected committee parent normId out.source out := by
  unfold fromBytes at h; split at h <;> try contradiction
  rename_i size
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨tree,parsed,checked⟩ := h
  have src := checkedSource checked
  exact ⟨size,src.1 ▸ (NativePolicyCodec.decoded parsed).2,by simpa only [src.1] using src⟩
end DeltaReduce.NativeEligibility
