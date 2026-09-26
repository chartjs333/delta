import DeltaReduce.NativeInputSetBody

/-! Complete native ISC certificate shape, computed canonical JSON and two
distinct identities. A configured signer set is not signature authentication.
Ledger/root provenance and the rest of the certificate graph remain separate. -/
namespace DeltaReduce.NativeIscCertificate
open NativeReceiptBytes NativePolicyCodec NativePolicySchema NativeInputSetBody
open NativeConfigAdmission (ascii Label)

structure Certificate where
  body : Body
  threshold : Nat
  signers : List Bytes
  deriving DecidableEq, Repr

def value (c : Certificate) : Value :=
  .pair (contextValue c.body.context) (.pair (.text c.body.root)
    (.pair (.number c.threshold) (.pair (.items (c.signers.map Value.text))
      (.pair (.items (c.body.tuples.map tupleValue)) .end))))

def readTexts : List Value → Option (List Bytes)
  | [] => some []
  | .text x::xs => do let rest ← readTexts xs; some (x::rest)
  | _ => none

def read : Value → Option Certificate
  | .pair ctx (.pair (.text root) (.pair (.number threshold)
      (.pair (.items signers) (.pair (.items tuples) .end)))) => do
    let c ← readContext ctx
    let ss ← readTexts signers
    let ts ← readTuples tuples
    some ⟨⟨c,root,ts⟩,threshold,ss⟩
  | _ => none

theorem textsRead (xs) : readTexts (xs.map Value.text) = some xs := by
  induction xs with
  | nil => rfl
  | cons x xs ih => simp only [List.map_cons,readTexts,ih,bind,Option.bind]

theorem textsOriginal {vs xs} (h : readTexts vs = some xs) : vs = xs.map Value.text := by
  induction vs generalizing xs with
  | nil => simp [readTexts] at h; subst xs; rfl
  | cons v vs ih =>
    cases v <;> try simp [readTexts] at h
    rename_i b
    simp only [Option.bind_eq_some_iff] at h
    obtain ⟨rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,← ih hr]

theorem valueRead (c) : read (value c) = some c := by
  cases c; simp only [value,read,contextRead,textsRead,tuplesRead,bind,Option.bind]

theorem readOriginal {v c} (h : read v = some c) : v = value c := by
  unfold read at h
  split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨ctx,hc,ss,hs,ts,ht,last⟩ := h
  cases Option.some.inj last
  simp only [value,← contextOriginal hc,← textsOriginal hs,← tuplesOriginal ht]

def quorum (committee : List Bytes) : Nat := 2 * ((committee.length - 1) / 3) + 1
def CommitteeValid (committee : List Bytes) : Prop :=
  committee ≠ [] ∧ committee.length ≤ 4096 ∧ committee.length % 3 = 1 ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT committee = true ∧
  ∀ id ∈ committee, Label id
instance (committee) : Decidable (CommitteeValid committee) := by
  unfold CommitteeValid; infer_instance

def SignersValid (committee : List Bytes) (c : Certificate) : Prop :=
  0 < c.threshold ∧ c.threshold < 256^4 ∧ c.threshold = quorum committee ∧
  c.threshold ≤ c.signers.length ∧ c.signers.length ≤ 100000 ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT c.signers = true ∧
  ∀ id ∈ c.signers, Label id ∧ id ∈ committee
instance (committee c) : Decidable (SignersValid committee c) := by
  unfold SignersValid; infer_instance

def Valid (expected : Context) (committee : List Bytes) (c : Certificate) : Prop :=
  CommitteeValid committee ∧ BodyValid expected c.body ∧ SignersValid committee c
instance (expected committee c) : Decidable (Valid expected committee c) := by
  unfold Valid; infer_instance

-- Pure serializers; only check/fromBytes establish the native shape guards.
def quoted (b : Bytes) : Bytes := [34] ++ b ++ [34]
def comma : List Bytes → Bytes
  | [] => []
  | [x] => x
  | x::y::xs => x ++ [44] ++ comma (y::xs)
def array (xs : List Bytes) : Bytes := [91] ++ comma xs ++ [93]
def object (fields : List (String × Bytes)) : Bytes :=
  [123] ++ comma (fields.map (fun (k,v) => quoted (ascii k) ++ [58] ++ v)) ++ [125]
def number (n : Nat) : Bytes := ascii (toString n)
def tupleJSON (t : Tuple) : Bytes := object
  [("availability_certificate_id",quoted t.availability),("commitment_id",quoted t.commitment),
   ("domain_id",quoted t.domain),("ticket_id",quoted t.ticket)]
def fields (c : Certificate) : List (String × Bytes) :=
  [("arithmetic_profile_id",quoted c.body.context.arithmetic),
   ("formal_semantics_id",quoted NativeVoteBytes.nativeSemantics),
   ("height",number c.body.context.height),("input_root",quoted c.body.root),
   ("parameter_schema_id",quoted c.body.context.schema),("quorum_threshold",number c.threshold),
   ("round_config_id",quoted c.body.context.config),("round_id",quoted c.body.context.round),
   ("schema_version",quoted (ascii "1.0.0")),("signer_ids",array (c.signers.map quoted)),
   ("tuples",array (c.body.tuples.map tupleJSON)),
   ("type_name",quoted (ascii "INPUT_SET_CERTIFICATE")),
   ("validator_epoch_id",quoted c.body.context.epoch),("view",number c.body.context.view)]
def json (c : Certificate) : Bytes := object (fields c)
def domain : Bytes := ascii "deltareduce.008.input-set-certificate.v1"
def id (sha : Bytes → Bytes) (c : Certificate) : Option Bytes :=
  NativeStateBytes.contentId sha domain (json c)

structure Checked where
  certificate : Certificate
  source : Value
  qcId : Bytes
  bodyId : Bytes

def check (sha : Bytes → Bytes) (expected : Context) (committee : List Bytes)
    (source : Value) : Option Checked := do
  let c ← read source
  if Valid expected committee c then
    let qc ← id sha c
    let body ← NativeInputSetBody.bodyId sha c.body
    some ⟨c,source,qc,body⟩
  else none

def Source (sha : Bytes → Bytes) (expected : Context) (committee : List Bytes)
    (source : Value) (c : Checked) : Prop :=
  c.source = source ∧ read source = some c.certificate ∧ source = value c.certificate ∧
  Valid expected committee c.certificate ∧ id sha c.certificate = some c.qcId ∧
  NativeInputSetBody.bodyId sha c.certificate.body = some c.bodyId

theorem checkedSource {sha expected committee source c}
    (h : check sha expected committee source = some c) : Source sha expected committee source c := by
  unfold check at h
  cases hr : read source with
  | none => simp [hr] at h
  | some cert =>
    simp only [hr,bind,Option.bind] at h
    split at h <;> try contradiction
    rename_i valid
    cases hq : id sha cert with
    | none => simp [hq] at h
    | some qc =>
      cases hb : NativeInputSetBody.bodyId sha cert.body with
      | none => simp [hq,hb] at h
      | some body =>
        simp only [hq,hb] at h
        cases Option.some.inj h
        exact ⟨rfl,hr,readOriginal hr,valid,hq,hb⟩

theorem fromComponents {sha expected committee source c qc body}
    (parsed : read source = some c) (valid : Valid expected committee c)
    (hq : id sha c = some qc) (hb : NativeInputSetBody.bodyId sha c.body = some body) :
    check sha expected committee source = some ⟨c,source,qc,body⟩ := by
  simp only [check,parsed,bind,Option.bind,if_pos valid,hq,hb]

theorem wrongShapeRejected {sha expected committee source c}
    (parsed : read source = some c) (bad : ¬ Valid expected committee c) :
    check sha expected committee source = none := by simp [check,parsed,bad]

theorem checkedQuorum {sha expected committee source c}
    (h : check sha expected committee source = some c) :
    c.certificate.threshold = quorum committee ∧
    c.certificate.threshold ≤ c.certificate.signers.length ∧
    ∀ signer ∈ c.certificate.signers, signer ∈ committee := by
  have v := (checkedSource h).2.2.2.1.2.2
  exact ⟨v.2.2.1,v.2.2.2.1,fun x hx => (v.2.2.2.2.2.2 x hx).2⟩

theorem checkedContext {sha expected committee source c}
    (h : check sha expected committee source = some c) : c.certificate.body.context = expected :=
  (checkedSource h).2.2.2.1.2.1.2.1

theorem checkedBody {sha expected committee source c}
    (h : check sha expected committee source = some c) :
    NativeInputSetBody.check sha expected (bodyValue c.certificate.body) =
      some ⟨c.certificate.body,c.bodyId,bodyValue c.certificate.body⟩ :=
  NativeInputSetBody.checkFromComponents (bodyRead _) (checkedSource h).2.2.2.2.2
    (checkedSource h).2.2.2.1.2.1

theorem bodyIgnoresSigners (c : Certificate) (signers threshold) :
    ({c with signers := signers, threshold := threshold} : Certificate).body = c.body := rfl

theorem missingHashRejected (expected committee source) :
    check (fun _ => []) expected committee source = none := by
  unfold check
  cases read source with
  | none => rfl
  | some c =>
    dsimp only [bind,Option.bind]
    split <;> simp [NativeIscCertificate.id,NativeStateBytes.contentId]

def checkAll (sha : Bytes → Bytes) (expected : Context) (committee : List Bytes) :
    List Value → Option (List Checked)
  | [] => some []
  | v::vs => do
    let c ← check sha expected committee v
    let cs ← checkAll sha expected committee vs
    some (c::cs)

theorem listFromComponents {sha expected committee v vs c cs}
    (first : check sha expected committee v = some c)
    (rest : checkAll sha expected committee vs = some cs) :
    checkAll sha expected committee (v::vs) = some (c::cs) := by
  simp only [checkAll,first,rest,bind,Option.bind]

theorem allSources {sha expected committee vs cs}
    (h : checkAll sha expected committee vs = some cs) : cs.map Checked.source = vs := by
  induction vs generalizing cs with
  | nil => simp [checkAll] at h; subst cs; rfl
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨c,hc,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,(checkedSource hc).1,ih hr]

theorem allChecked {sha expected committee vs cs}
    (h : checkAll sha expected committee vs = some cs) (c : Checked) (mem : c ∈ cs) :
    Source sha expected committee c.source c := by
  induction vs generalizing cs with
  | nil => simp [checkAll] at h; subst cs; simp at mem
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨x,hx,rest,hr,last⟩ := h
    cases Option.some.inj last
    rcases List.mem_cons.mp mem with rfl | mem
    · have s := checkedSource hx; simpa only [s.1] using s
    · exact ih hr mem

theorem allCount {sha expected committee vs cs}
    (h : checkAll sha expected committee vs = some cs) : cs.length = vs.length := by
  have eq := congrArg List.length (allSources h); simpa using eq

def fromBytes (sha : Bytes → Bytes) (expected : Context) (committee : List Bytes)
    (raw : Bytes) : Option Checked := do
  if raw.length ≤ 4*1024*1024 then
    let tree ← NativePolicyCodec.decode fmtInputSet raw
    check sha expected committee tree
  else none

theorem bytesSource {sha expected committee raw out}
    (h : fromBytes sha expected committee raw = some out) :
    raw.length ≤ 4*1024*1024 ∧ encode fmtInputSet out.source = some raw ∧
    Source sha expected committee out.source out := by
  unfold fromBytes at h
  split at h <;> try contradiction
  rename_i size
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨tree,parsed,checked⟩ := h
  have src := checkedSource checked
  exact ⟨size,src.1 ▸ (NativePolicyCodec.decoded parsed).2,by simpa only [src.1] using src⟩

theorem bytesFromComponents {sha expected committee raw tree out}
    (size : raw.length ≤ 4*1024*1024)
    (parsed : NativePolicyCodec.decode fmtInputSet raw = some tree)
    (checked : check sha expected committee tree = some out) :
    fromBytes sha expected committee raw = some out := by
  simp only [fromBytes,if_pos size,parsed,checked,bind,Option.bind]

end DeltaReduce.NativeIscCertificate
