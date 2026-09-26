import DeltaReduce.NativeIscCertificate
import DeltaReduce.NativeCertificateDecimal

/-! Original native norm fields, including accepted noncanonical decimal bytes.
Norm values/root remain primitives; no norm recomputation or membership theorem. -/
namespace DeltaReduce.NativeNormEvidence
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativeInputSetBody (Context contextValue readContext ContextValid)
open NativeIscCertificate (quoted array object number)

structure Entry where
  scale : Nat
  squared : Bytes
  ticket : Bytes
  deriving DecidableEq, Repr
structure Evidence where
  context : Context
  entries : List Entry
  isc : Bytes
  root : Bytes
  deriving DecidableEq, Repr

def entryValue (e : Entry) : Value :=
  .pair (.number e.scale) (.pair (.text e.squared) (.pair (.text e.ticket) .end))
def readEntry : Value → Option Entry
  | .pair (.number scale) (.pair (.text squared) (.pair (.text ticket) .end)) =>
    some ⟨scale,squared,ticket⟩
  | _ => none
def readEntries : List Value → Option (List Entry)
  | [] => some []
  | v::vs => do let e ← readEntry v; let es ← readEntries vs; some (e::es)
def value (t : Evidence) : Value := .pair (contextValue t.context)
  (.pair (.items (t.entries.map entryValue)) (.pair (.text t.isc) (.pair (.text t.root) .end)))
def read : Value → Option Evidence
  | .pair ctx (.pair (.items entries) (.pair (.text isc) (.pair (.text root) .end))) => do
    let c ← readContext ctx
    let es ← readEntries entries
    some ⟨c,es,isc,root⟩
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
theorem valueRead (t) : read (value t) = some t := by
  cases t
  simp only [value,read,NativeInputSetBody.contextRead,entriesRead,bind,Option.bind]
theorem readOriginal {v t} (h : read v = some t) : v = value t := by
  unfold read at h
  split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,hc,es,hs,last⟩ := h
  cases Option.some.inj last
  simp only [value,← NativeInputSetBody.contextOriginal hc,← entriesOriginal hs]

def EntryValid (e : Entry) : Prop :=
  0 < e.scale ∧ e.scale < 256^8 ∧ NativeConfigAdmission.Label e.ticket ∧
  NativeCertificateDecimal.Valid true e.squared
instance (e) : Decidable (EntryValid e) := by unfold EntryValid; infer_instance
def Valid (expected : Context) (t : Evidence) : Prop :=
  ContextValid t.context ∧ t.context = expected ∧ NativeVoteBytes.ContentId t.isc ∧
  NativeVoteBytes.ContentId t.root ∧ 0 < t.entries.length ∧ t.entries.length ≤ 100000 ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (t.entries.map Entry.ticket) = true ∧
  ∀ e ∈ t.entries, EntryValid e
instance (expected t) : Decidable (Valid expected t) := by unfold Valid; infer_instance

-- Keep squared_norm's original bytes; Int.repr would erase native accepted spelling.
def entryJSON (e : Entry) : Bytes := object
  [("scale_denominator",number e.scale),("squared_norm",quoted e.squared),
   ("ticket_id",quoted e.ticket)]
def fields (t : Evidence) : List (String × Bytes) :=
  [("arithmetic_profile_id",quoted t.context.arithmetic),("entries",array (t.entries.map entryJSON)),
   ("formal_semantics_id",quoted NativeVoteBytes.nativeSemantics),
   ("height",number t.context.height),("input_set_certificate_id",quoted t.isc),
   ("norm_root",quoted t.root),("parameter_schema_id",quoted t.context.schema),
   ("round_config_id",quoted t.context.config),("round_id",quoted t.context.round),
   ("schema_version",quoted (NativeVoteBytes.ascii "1.0.0")),
   ("type_name",quoted (NativeVoteBytes.ascii "NORM_EVIDENCE")),
   ("validator_epoch_id",quoted t.context.epoch),("view",number t.context.view)]
def json (t : Evidence) : Bytes := object (fields t)
def domain : Bytes := NativeVoteBytes.ascii "deltareduce.008.norm-evidence.v1"
def id (sha : Bytes → Bytes) (t : Evidence) : Option Bytes :=
  NativeStateBytes.contentId sha domain (json t)

structure Checked where
  evidence : Evidence
  source : Value
  id : Bytes

def check (sha : Bytes → Bytes) (expected : Context) (finalized : List Bytes)
    (source : Value) : Option Checked := do
  let t ← read source
  if Valid expected t ∧ t.isc ∈ finalized then
    let tid ← id sha t
    some ⟨t,source,tid⟩
  else none

def Source (sha : Bytes → Bytes) (expected : Context) (finalized : List Bytes)
    (source : Value) (out : Checked) : Prop :=
  out.source = source ∧ read source = some out.evidence ∧ source = value out.evidence ∧
  Valid expected out.evidence ∧ out.evidence.isc ∈ finalized ∧
  id sha out.evidence = some out.id

theorem checkedSource {sha expected finalized source out}
    (h : check sha expected finalized source = some out) : Source sha expected finalized source out := by
  unfold check at h
  cases hr : read source with
  | none => simp [hr] at h
  | some t =>
    simp only [hr,bind,Option.bind] at h
    split at h <;> try contradiction
    rename_i checks
    cases hi : id sha t with
    | none => simp [hi] at h
    | some tid =>
      simp only [hi] at h
      cases Option.some.inj h
      exact ⟨rfl,hr,readOriginal hr,checks.1,checks.2,hi⟩

theorem fromComponents {sha expected finalized source t tid}
    (parsed : read source = some t) (valid : Valid expected t)
    (parent : t.isc ∈ finalized) (hashed : id sha t = some tid) :
    check sha expected finalized source = some ⟨t,source,tid⟩ := by
  have checks : Valid expected t ∧ t.isc ∈ finalized := ⟨valid,parent⟩
  simp only [check,parsed,bind,Option.bind,if_pos checks,hashed]

theorem wrongParentRejected {sha expected finalized source t}
    (parsed : read source = some t) (absent : t.isc ∉ finalized) :
    check sha expected finalized source = none := by simp [check,parsed,absent]

theorem wrongShapeRejected {sha expected finalized source t}
    (parsed : read source = some t) (invalid : ¬ Valid expected t) :
    check sha expected finalized source = none := by simp [check,parsed,invalid]

theorem missingHashRejected (expected finalized source) :
    check (fun _ => []) expected finalized source = none := by
  unfold check
  cases read source with
  | none => rfl
  | some t =>
    dsimp only [bind,Option.bind]
    split <;> simp [NativeNormEvidence.id,NativeStateBytes.contentId]

def checkAll (sha : Bytes → Bytes) (expected : Context) (finalized : List Bytes) :
    List Value → Option (List Checked)
  | [] => some []
  | v::vs => do
    let t ← check sha expected finalized v
    let ts ← checkAll sha expected finalized vs
    some (t::ts)

theorem listFromComponents {sha expected finalized v vs t ts}
    (first : check sha expected finalized v = some t)
    (rest : checkAll sha expected finalized vs = some ts) :
    checkAll sha expected finalized (v::vs) = some (t::ts) := by
  simp only [checkAll,first,rest,bind,Option.bind]

theorem allSources {sha expected finalized vs ts}
    (h : checkAll sha expected finalized vs = some ts) : ts.map Checked.source = vs := by
  induction vs generalizing ts with
  | nil => simp [checkAll] at h; subst ts; rfl
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨t,ht,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,(checkedSource ht).1,ih hr]

theorem allChecked {sha expected finalized vs ts}
    (h : checkAll sha expected finalized vs = some ts) (t : Checked) (mem : t ∈ ts) :
    Source sha expected finalized t.source t := by
  induction vs generalizing ts with
  | nil => simp [checkAll] at h; subst ts; simp at mem
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨x,hx,rest,hr,last⟩ := h
    cases Option.some.inj last
    rcases List.mem_cons.mp mem with rfl | mem
    · have s := checkedSource hx; simpa only [s.1] using s
    · exact ih hr mem

def fromBytes (sha : Bytes → Bytes) (expected : Context) (finalized : List Bytes)
    (raw : Bytes) : Option Checked := do
  if raw.length ≤ 4*1024*1024 then
    let tree ← NativePolicyCodec.decode fmtNorm raw
    check sha expected finalized tree
  else none

theorem bytesSource {sha expected finalized raw out}
    (h : fromBytes sha expected finalized raw = some out) :
    raw.length ≤ 4*1024*1024 ∧ encode fmtNorm out.source = some raw ∧
    Source sha expected finalized out.source out := by
  unfold fromBytes at h
  split at h <;> try contradiction
  rename_i size
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨tree,parsed,checked⟩ := h
  have src := checkedSource checked
  exact ⟨size,src.1 ▸ (NativePolicyCodec.decoded parsed).2,by simpa only [src.1] using src⟩

theorem bytesFromComponents {sha expected finalized raw tree out}
    (size : raw.length ≤ 4*1024*1024) (parsed : NativePolicyCodec.decode fmtNorm raw = some tree)
    (checked : check sha expected finalized tree = some out) :
    fromBytes sha expected finalized raw = some out := by
  simp only [fromBytes,if_pos size,parsed,checked,bind,Option.bind]

-- This component computes both sides of the certificate edge, not finalization provenance.
def linked (sha : Bytes → Bytes) (expected : Context) (committee : List Bytes)
    (certificate source : Value) : Option (NativeIscCertificate.Checked × Checked) := do
  let parent ← NativeIscCertificate.check sha expected committee certificate
  let norm ← check sha expected [parent.qcId] source
  some (parent,norm)

theorem linkedFromComponents {sha expected committee certificate source parent norm}
    (cert : NativeIscCertificate.check sha expected committee certificate = some parent)
    (edge : check sha expected [parent.qcId] source = some norm) :
    linked sha expected committee certificate source = some (parent,norm) := by
  simp only [linked,cert,edge,bind,Option.bind]

theorem linkedSources {sha expected committee certificate source parent norm}
    (h : linked sha expected committee certificate source = some (parent,norm)) :
    NativeIscCertificate.Source sha expected committee certificate parent ∧
    Source sha expected [parent.qcId] source norm ∧ norm.evidence.isc = parent.qcId := by
  unfold linked at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨p,hp,s,hs,last⟩ := h
  cases Option.some.inj last
  have src := checkedSource hs
  exact ⟨NativeIscCertificate.checkedSource hp,src,by simpa using src.2.2.2.2.1⟩

theorem originalEntries {sha expected finalized source out}
    (h : check sha expected finalized source = some out) :
    ∀ e ∈ out.evidence.entries, EntryValid e := (checkedSource h).2.2.2.1.2.2.2.2.2.2.2

theorem entryNumbers {sha expected finalized source out}
    (h : check sha expected finalized source = some out) (e : Entry)
    (mem : e ∈ out.evidence.entries) :
    NativeCertificateDecimal.check true e.squared =
      some ⟨e.squared,NativeCertificateDecimal.number e.squared⟩ ∧
    0 ≤ NativeCertificateDecimal.number e.squared := by
  have v := (originalEntries h e mem).2.2.2
  exact ⟨NativeCertificateDecimal.checkedFromParse (NativeCertificateDecimal.fromValid v),v.2.2.2 rfl⟩

end DeltaReduce.NativeNormEvidence
