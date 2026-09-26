import DeltaReduce.NativePlan

/-! Native APC parent resolution retains the exact observed guards. The native
APC verifier does not repeat EC/ISC cross-parent equality; no additional equality
is silently inserted here. Enclosing sections validate each original parent. -/
namespace DeltaReduce.NativePlanLineage
open NativeReceiptBytes NativePolicyCodec NativePolicySchema NativePlan
open NativeInputSetBody (Context)

inductive Mode where | proposed | finalized deriving DecidableEq, Repr
def decode (mode : Mode) (committee : List Bytes) (source : Value) : Option Certificate :=
  match mode with
  | .proposed => do let b ← readBody source; some (proposedCertificate committee b)
  | .finalized => read source
def original (mode : Mode) (c : Certificate) : Value :=
  match mode with
  | .proposed => bodyValue c.common
  | .finalized => value c
theorem decodedOriginal {mode committee source c}
    (h : decode mode committee source = some c) : source = original mode c := by
  cases mode with
  | proposed =>
    simp only [decode,bind,Option.bind_eq_some_iff] at h
    obtain ⟨b,hb,last⟩ := h
    cases Option.some.inj last
    exact bodyOriginal hb
  | finalized => exact readOriginal h

def NativeParentChecks (finalizedIsc finalizedEc : List Bytes) (required : Bytes)
    (c : Certificate) (parent : NativeIscCertificate.Checked)
    (ec : NativeEligibilityLineage.Edge) (seed : NativeSeedTranscript.Checked) : Prop :=
  parent.qcId ∈ finalizedIsc ∧ ec.id ∈ finalizedEc ∧ ec.seedId = seed.id ∧
  c.common.isc = parent.qcId ∧ c.common.ec = ec.id ∧ c.common.seed = seed.id ∧
  c.common.accumulator = required ∧ Coverage c.common ec.certificate
instance (finalizedIsc finalizedEc required c parent ec seed) :
    Decidable (NativeParentChecks finalizedIsc finalizedEc required c parent ec seed) := by
  unfold NativeParentChecks; infer_instance
def resultId (sha : Bytes → Bytes) (mode : Mode) (c : Certificate) : Option Bytes :=
  match mode with
  | .proposed => bodyId sha c.common
  | .finalized => id sha c

structure Edge where
  certificate : Certificate
  source : Value
  id : Bytes
  parent : NativeIscCertificate.Checked
  ec : NativeEligibilityLineage.Edge
  seed : NativeSeedTranscript.Checked

def check (sha : Bytes → Bytes) (mode : Mode) (expected : Context) (committee : List Bytes)
    (parents : List NativeIscCertificate.Checked) (finalizedIsc finalizedEc : List Bytes) (required : Bytes)
    (ecs : List NativeEligibilityLineage.Edge) (seeds : List NativeSeedTranscript.Checked)
    (source : Value) : Option Edge := do
  let c ← decode mode committee source
  let parent ← parents.find? (fun p => p.qcId == c.common.isc)
  let ec ← ecs.find? (fun n => n.id == c.common.ec)
  let seed ← seeds.find? (fun s => s.id == c.common.seed)
  if Valid expected committee c ∧ NativeParentChecks finalizedIsc finalizedEc required c parent ec seed then
    let hash ← resultId sha mode c
    some ⟨c,source,hash,parent,ec,seed⟩
  else none

def Source (sha : Bytes → Bytes) (mode : Mode) (expected : Context) (committee : List Bytes)
    (parents : List NativeIscCertificate.Checked) (finalizedIsc finalizedEc : List Bytes) (required : Bytes)
    (ecs : List NativeEligibilityLineage.Edge) (seeds : List NativeSeedTranscript.Checked)
    (source : Value) (e : Edge) : Prop :=
  e.source = source ∧ decode mode committee source = some e.certificate ∧
  parents.find? (fun p => p.qcId == e.certificate.common.isc) = some e.parent ∧
  ecs.find? (fun n => n.id == e.certificate.common.ec) = some e.ec ∧
  seeds.find? (fun s => s.id == e.certificate.common.seed) = some e.seed ∧
  Valid expected committee e.certificate ∧
  NativeParentChecks finalizedIsc finalizedEc required e.certificate e.parent e.ec e.seed ∧
  resultId sha mode e.certificate = some e.id

theorem checkedSource {sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds source e}
    (h : check sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds source = some e) :
    Source sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds source e := by
  unfold check at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨c,hd,parent,hp,ec,hn,seed,hs,last⟩ := h
  split at last <;> try contradiction
  rename_i valid
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨hash,hh,last⟩ := last
  cases Option.some.inj last
  exact ⟨rfl,hd,hp,hn,hs,valid.1,valid.2,hh⟩

theorem fromComponents {sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds source e}
    (h : Source sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds source e) :
    check sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds source = some e := by
  rcases h with ⟨rfl,hd,hp,hn,hs,hv,hparents,hh⟩
  unfold check
  rw [hd]
  dsimp only [bind,Option.bind]
  rw [hp,hn,hs]
  dsimp only [bind,Option.bind]
  rw [if_pos ⟨hv,hparents⟩,hh]

theorem originalRetained {sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds source e}
    (h : check sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds source = some e) :
    source = original mode e.certificate := decodedOriginal (checkedSource h).2.1

theorem parentWitnesses {sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds source e}
    (h : check sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds source = some e) :
    e.parent ∈ parents ∧ e.parent.qcId = e.certificate.common.isc ∧
    e.ec ∈ ecs ∧ e.ec.id = e.certificate.common.ec ∧
    e.seed ∈ seeds ∧ e.seed.id = e.certificate.common.seed := by
  have src := checkedSource h
  exact ⟨List.mem_of_find?_eq_some src.2.2.1,by simpa using List.find?_some src.2.2.1,
    List.mem_of_find?_eq_some src.2.2.2.1,by simpa using List.find?_some src.2.2.2.1,
    List.mem_of_find?_eq_some src.2.2.2.2.1,by simpa using List.find?_some src.2.2.2.2.1⟩

theorem exactCoverage {sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds source e}
    (h : check sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds source = some e) :
    Coverage e.certificate.common e.ec.certificate :=
  (checkedSource h).2.2.2.2.2.2.1.2.2.2.2.2.2.2

def checkAll (sha : Bytes → Bytes) (mode : Mode) (expected : Context) (committee : List Bytes)
    (parents : List NativeIscCertificate.Checked) (finalizedIsc finalizedEc : List Bytes) (required : Bytes)
    (ecs : List NativeEligibilityLineage.Edge) (seeds : List NativeSeedTranscript.Checked) :
    List Value → Option (List Edge)
  | [] => some []
  | v::vs => do
    let e ← check sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds v
    let rest ← checkAll sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds vs
    some (e::rest)

theorem allSources {sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds vs es}
    (h : checkAll sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds vs = some es) :
    es.map Edge.source = vs := by
  induction vs generalizing es with
  | nil => simp [checkAll] at h; subst es; rfl
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨e,he,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,(checkedSource he).1,ih hr]

theorem allChecked {sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds vs es}
    (h : checkAll sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds vs = some es)
    (e : Edge) (mem : e ∈ es) :
    check sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds e.source = some e := by
  induction vs generalizing es with
  | nil => simp [checkAll] at h; subst es; simp at mem
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨x,hx,rest,hr,last⟩ := h
    cases Option.some.inj last
    rcases List.mem_cons.mp mem with rfl | mem
    · simpa only [(checkedSource hx).1] using hx
    · exact ih hr mem
def format (mode : Mode) : Format := match mode with
  | .proposed => fmtPlanBody
  | .finalized => fmtPlan
def fromBytes (sha : Bytes → Bytes) (mode : Mode) (expected : Context) (committee : List Bytes)
    (parents : List NativeIscCertificate.Checked) (finalizedIsc finalizedEc : List Bytes) (required : Bytes)
    (ecs : List NativeEligibilityLineage.Edge) (seeds : List NativeSeedTranscript.Checked)
    (raw : Bytes) : Option Edge := do
  if raw.length ≤ 4*1024*1024 then
    let source ← NativePolicyCodec.decode (format mode) raw
    check sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds source
  else none
theorem bytesSource {sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds raw e}
    (h : fromBytes sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds raw = some e) :
    raw.length ≤ 4*1024*1024 ∧ encode (format mode) e.source = some raw ∧
    Source sha mode expected committee parents finalizedIsc finalizedEc required ecs seeds e.source e := by
  unfold fromBytes at h; split at h <;> try contradiction
  rename_i size
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨source,parsed,checked⟩ := h
  have src := checkedSource checked
  exact ⟨size,src.1 ▸ (NativePolicyCodec.decoded parsed).2,by simpa only [src.1] using src⟩
end DeltaReduce.NativePlanLineage
