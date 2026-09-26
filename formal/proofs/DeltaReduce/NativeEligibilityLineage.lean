import DeltaReduce.NativeEligibility
import DeltaReduce.NativeNormSection

/-! Proposed versus finalized native EC edges remain distinct. Finalized EC
does not repeat the proposed-only norm/ISC equality. Every norm is still
validated against its own finalized ISC by the enclosing section. -/
namespace DeltaReduce.NativeEligibilityLineage
open NativeReceiptBytes NativePolicyCodec NativePolicySchema NativeEligibility
open NativeInputSetBody (Context)

inductive Mode where | proposed | finalized deriving DecidableEq, Repr
def decode (mode : Mode) (committee : List Bytes) (source : Value) :
    Option (Certificate × Bytes) :=
  match mode,source with
  | .proposed,_ => do
    let b ← readBody source
    some (proposedCertificate committee b,b.seed)
  | .finalized,.pair cert (.pair (.text seed) .end) => do
    let c ← read cert
    some (c,seed)
  | _,_ => none
def original (mode : Mode) (c : Certificate) (seed : Bytes) : Value :=
  match mode with
  | .proposed => bodyValue ⟨c.common,seed⟩
  | .finalized => .pair (value c) (.pair (.text seed) .end)

theorem decodedOriginal {mode committee source c seed}
    (h : decode mode committee source = some (c,seed)) : source = original mode c seed := by
  cases mode with
  | proposed =>
    simp only [decode,bind,Option.bind_eq_some_iff] at h
    obtain ⟨b,hb,last⟩ := h
    cases Option.some.inj last
    exact bodyOriginal hb
  | finalized =>
    unfold decode at h
    split at h <;> try contradiction
    simp only [bind,Option.bind_eq_some_iff] at h
    obtain ⟨cert,hc,last⟩ := h
    cases Option.some.inj last
    simp only [original,← readOriginal hc]

def NativeParentChecks (mode : Mode) (finalized : List Bytes)
    (c : Certificate) (parent : NativeIscCertificate.Checked)
    (norm : NativeNormEvidence.Checked) (seed : NativeSeedTranscript.Checked) : Prop :=
  parent.qcId ∈ finalized ∧ seed.transcript.isc = parent.qcId ∧
  (mode = .proposed → norm.evidence.isc = parent.qcId) ∧ Membership c.common parent
instance (mode finalized c parent norm seed) :
    Decidable (NativeParentChecks mode finalized c parent norm seed) := by
  unfold NativeParentChecks; infer_instance

def resultId (sha : Bytes → Bytes) (mode : Mode) (c : Certificate) (seed : Bytes) :
    Option Bytes :=
  match mode with
  | .proposed => bodyId sha ⟨c.common,seed⟩
  | .finalized => id sha c

structure Edge where
  certificate : Certificate
  seedId : Bytes
  source : Value
  id : Bytes
  parent : NativeIscCertificate.Checked
  norm : NativeNormEvidence.Checked
  seed : NativeSeedTranscript.Checked

def check (sha : Bytes → Bytes) (mode : Mode) (expected : Context) (committee : List Bytes)
    (parents : List NativeIscCertificate.Checked) (finalized : List Bytes)
    (norms : List NativeNormEvidence.Checked) (seeds : List NativeSeedTranscript.Checked)
    (source : Value) : Option Edge := do
  let (c,seedId) ← decode mode committee source
  let parent ← parents.find? (fun p => p.qcId == c.common.isc)
  let norm ← norms.find? (fun n => n.id == c.common.norm)
  let seed ← seeds.find? (fun s => s.id == seedId)
  if Valid expected committee c ∧ NativeParentChecks mode finalized c parent norm seed then
    let hash ← resultId sha mode c seedId
    some ⟨c,seedId,source,hash,parent,norm,seed⟩
  else none

def Source (sha : Bytes → Bytes) (mode : Mode) (expected : Context) (committee : List Bytes)
    (parents : List NativeIscCertificate.Checked) (finalized : List Bytes)
    (norms : List NativeNormEvidence.Checked) (seeds : List NativeSeedTranscript.Checked)
    (source : Value) (e : Edge) : Prop :=
  e.source = source ∧ decode mode committee source = some (e.certificate,e.seedId) ∧
  parents.find? (fun p => p.qcId == e.certificate.common.isc) = some e.parent ∧
  norms.find? (fun n => n.id == e.certificate.common.norm) = some e.norm ∧
  seeds.find? (fun s => s.id == e.seedId) = some e.seed ∧
  Valid expected committee e.certificate ∧
  NativeParentChecks mode finalized e.certificate e.parent e.norm e.seed ∧
  resultId sha mode e.certificate e.seedId = some e.id

theorem checkedSource {sha mode expected committee parents finalized norms seeds source e}
    (h : check sha mode expected committee parents finalized norms seeds source = some e) :
    Source sha mode expected committee parents finalized norms seeds source e := by
  unfold check at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨c,seedId⟩,hd,parent,hp,norm,hn,seed,hs,last⟩ := h
  split at last <;> try contradiction
  rename_i valid
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨hash,hh,last⟩ := last
  cases Option.some.inj last
  exact ⟨rfl,hd,hp,hn,hs,valid.1,valid.2,hh⟩

theorem fromComponents {sha mode expected committee parents finalized norms seeds source e}
    (h : Source sha mode expected committee parents finalized norms seeds source e) :
    check sha mode expected committee parents finalized norms seeds source = some e := by
  rcases h with ⟨rfl,hd,hp,hn,hs,hv,hparents,hh⟩
  unfold check
  rw [hd]
  dsimp only [bind,Option.bind]
  rw [hp,hn,hs]
  dsimp only [bind,Option.bind]
  rw [if_pos ⟨hv,hparents⟩,hh]

theorem originalRetained {sha mode expected committee parents finalized norms seeds source e}
    (h : check sha mode expected committee parents finalized norms seeds source = some e) :
    source = original mode e.certificate e.seedId := decodedOriginal (checkedSource h).2.1

theorem parentWitnesses {sha mode expected committee parents finalized norms seeds source e}
    (h : check sha mode expected committee parents finalized norms seeds source = some e) :
    e.parent ∈ parents ∧ e.parent.qcId = e.certificate.common.isc ∧
    e.norm ∈ norms ∧ e.norm.id = e.certificate.common.norm ∧
    e.seed ∈ seeds ∧ e.seed.id = e.seedId := by
  have src := checkedSource h
  exact ⟨List.mem_of_find?_eq_some src.2.2.1,by simpa using List.find?_some src.2.2.1,
    List.mem_of_find?_eq_some src.2.2.2.1,by simpa using List.find?_some src.2.2.2.1,
    List.mem_of_find?_eq_some src.2.2.2.2.1,by simpa using List.find?_some src.2.2.2.2.1⟩

theorem proposedSameNormIsc {sha expected committee parents finalized norms seeds source e}
    (h : check sha .proposed expected committee parents finalized norms seeds source = some e) :
    e.norm.evidence.isc = e.parent.qcId :=
  (checkedSource h).2.2.2.2.2.2.1.2.2.1 rfl

def checkAll (sha : Bytes → Bytes) (mode : Mode) (expected : Context) (committee : List Bytes)
    (parents : List NativeIscCertificate.Checked) (finalized : List Bytes)
    (norms : List NativeNormEvidence.Checked) (seeds : List NativeSeedTranscript.Checked) :
    List Value → Option (List Edge)
  | [] => some []
  | v::vs => do
    let e ← check sha mode expected committee parents finalized norms seeds v
    let rest ← checkAll sha mode expected committee parents finalized norms seeds vs
    some (e::rest)

theorem allSources {sha mode expected committee parents finalized norms seeds vs es}
    (h : checkAll sha mode expected committee parents finalized norms seeds vs = some es) :
    es.map Edge.source = vs := by
  induction vs generalizing es with
  | nil => simp [checkAll] at h; subst es; rfl
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨e,he,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,(checkedSource he).1,ih hr]

theorem allChecked {sha mode expected committee parents finalized norms seeds vs es}
    (h : checkAll sha mode expected committee parents finalized norms seeds vs = some es)
    (e : Edge) (mem : e ∈ es) :
    check sha mode expected committee parents finalized norms seeds e.source = some e := by
  induction vs generalizing es with
  | nil => simp [checkAll] at h; subst es; simp at mem
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨x,hx,rest,hr,last⟩ := h
    cases Option.some.inj last
    rcases List.mem_cons.mp mem with rfl | mem
    · simpa only [(checkedSource hx).1] using hx
    · exact ih hr mem
end DeltaReduce.NativeEligibilityLineage
