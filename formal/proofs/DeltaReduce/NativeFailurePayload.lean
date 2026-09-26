import DeltaReduce.NativeApplySection

/-! Exact original timeout/view/abort payloads and canonical binary hash preimages.
Hashing has no invented certificate-JSON size bound; policy wire guards remain. -/
namespace DeltaReduce.NativeFailurePayload
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativeIscCertificate (readTexts)
open NativeConfigAdmission (Label)
open NativeInputSetBody (text64)
structure Timeout where
  round : Bytes
  height : Nat
  view : Nat
  deriving DecidableEq, Repr
structure ViewBody where
  round : Bytes
  height : Nat
  fromView : Nat
  toView : Nat
  deadline : Nat
  deriving DecidableEq, Repr
structure Request where
  round : Bytes
  reason : Bytes
  deriving DecidableEq, Repr
structure AbortBody where
  round : Bytes
  epoch : Bytes
  height : Nat
  view : Nat
  deadline : Nat
  parent : Bytes
  reason : Bytes
  configs : List Bytes
  inputs : List Bytes
  eligibility : List Bytes
  plans : List Bytes
  parameters : List Bytes
  roots : List Bytes
  applies : List Bytes
  deriving DecidableEq, Repr
def timeoutValue (c : Timeout) : Value := .pair (.text c.round) (.pair (.number c.height) (.pair (.number c.view) (.end)))
def readTimeout : Value → Option Timeout
  | .pair (.text round) (.pair (.number height) (.pair (.number view) (.end))) => some ⟨round,height,view⟩
  | _ => none
theorem timeoutRead (c) : readTimeout (timeoutValue c) = some c := by cases c; rfl
theorem timeoutOriginal {v c} (h : readTimeout v = some c) : v = timeoutValue c := by
  unfold readTimeout at h; split at h <;> try contradiction
  cases Option.some.inj h; rfl

def viewValue (c : ViewBody) : Value := .pair (.text c.round) (.pair (.number c.height) (.pair (.number c.fromView) (.pair (.number c.toView) (.pair (.number c.deadline) (.end)))))
def readView : Value → Option ViewBody
  | .pair (.text round) (.pair (.number height) (.pair (.number fromView) (.pair (.number toView) (.pair (.number deadline) (.end))))) => some ⟨round,height,fromView,toView,deadline⟩
  | _ => none
theorem viewRead (c) : readView (viewValue c) = some c := by cases c; rfl
theorem viewOriginal {v c} (h : readView v = some c) : v = viewValue c := by
  unfold readView at h; split at h <;> try contradiction
  cases Option.some.inj h; rfl

def requestValue (c : Request) : Value := .pair (.text c.round) (.pair (.text c.reason) (.end))
def readRequest : Value → Option Request
  | .pair (.text round) (.pair (.text reason) (.end)) => some ⟨round,reason⟩
  | _ => none
theorem requestRead (c) : readRequest (requestValue c) = some c := by cases c; rfl
theorem requestOriginal {v c} (h : readRequest v = some c) : v = requestValue c := by
  unfold readRequest at h; split at h <;> try contradiction
  cases Option.some.inj h; rfl

def abortValue (c : AbortBody) : Value :=
  .pair (.text c.round) (.pair (.text c.epoch) (.pair (.number c.height) (.pair (.number c.view) (.pair (.number c.deadline) (.pair (.text c.parent) (.pair (.text c.reason) (.pair (.items (c.configs.map Value.text)) (.pair (.items (c.inputs.map Value.text)) (.pair (.items (c.eligibility.map Value.text)) (.pair (.items (c.plans.map Value.text)) (.pair (.items (c.parameters.map Value.text)) (.pair (.items (c.roots.map Value.text)) (.pair (.items (c.applies.map Value.text)) (.end))))))))))))))
def readAbort : Value → Option AbortBody
  | .pair (.text round) (.pair (.text epoch) (.pair (.number height) (.pair (.number view) (.pair (.number deadline) (.pair (.text parent) (.pair (.text reason) (.pair (.items configs) (.pair (.items inputs) (.pair (.items eligibility) (.pair (.items plans) (.pair (.items parameters) (.pair (.items roots) (.pair (.items applies) (.end)))))))))))))) => do
    let configsValue ← readTexts configs
    let inputsValue ← readTexts inputs
    let eligibilityValue ← readTexts eligibility
    let plansValue ← readTexts plans
    let parametersValue ← readTexts parameters
    let rootsValue ← readTexts roots
    let appliesValue ← readTexts applies
    some ⟨round,epoch,height,view,deadline,parent,reason,configsValue,inputsValue,eligibilityValue,plansValue,parametersValue,rootsValue,appliesValue⟩
  | _ => none

theorem abortRead (c) : readAbort (abortValue c) = some c := by
  cases c
  simp only [abortValue,readAbort,NativeIscCertificate.textsRead,bind,Option.bind]
theorem abortOriginal {v c} (h : readAbort v = some c) : v = abortValue c := by
  unfold readAbort at h; split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨a0,h0,a1,h1,a2,h2,a3,h3,a4,h4,a5,h5,a6,h6,last⟩ := h
  cases Option.some.inj last
  simp only [abortValue,← NativeIscCertificate.textsOriginal h0,← NativeIscCertificate.textsOriginal h1,← NativeIscCertificate.textsOriginal h2,← NativeIscCertificate.textsOriginal h3,← NativeIscCertificate.textsOriginal h4,← NativeIscCertificate.textsOriginal h5,← NativeIscCertificate.textsOriginal h6]

def readAll {α : Type} (read : Value → Option α) : List Value → Option (List α)
  | [] => some []
  | v::vs => do let a ← read v; let rest ← readAll read vs; some (a::rest)
theorem readAllOriginal {α : Type} {read : Value → Option α} {value : α → Value}
    (original : ∀ {v a}, read v = some a → v = value a) {vs as}
    (h : readAll read vs = some as) : vs = as.map value := by
  induction vs generalizing as with
  | nil => simp [readAll] at h; subst as; rfl
  | cons v vs ih =>
    simp only [readAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨a,ha,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,← original ha,← ih hr]
theorem readAllRoundTrip {α : Type} {read : Value → Option α} {value : α → Value}
    (roundTrip : ∀ a, read (value a) = some a) (as : List α) :
    readAll read (as.map value) = some as := by
  induction as with
  | nil => rfl
  | cons a as ih => simp only [List.map_cons,readAll,roundTrip,ih,bind,Option.bind]

def TimeoutValid (t : Timeout) : Prop := Label t.round ∧ t.height < 256^8 ∧ t.view < 256^8
instance (t) : Decidable (TimeoutValid t) := by unfold TimeoutValid; infer_instance
def RequestValid (r : Request) : Prop := Label r.round ∧
  (r.reason = NativeVoteBytes.ascii "INCOMPLETE_INPUT" ∨ r.reason = NativeVoteBytes.ascii "UNSAFE_COEFFICIENTS")
instance (r) : Decidable (RequestValid r) := by unfold RequestValid; infer_instance

def timeoutLT (a b : Timeout) : Bool :=
  if a.round ≠ b.round then NativePolicyBytes.bytesLT a.round b.round
  else if a.height ≠ b.height then a.height < b.height else a.view < b.view

def requestLT (a b : Request) : Bool :=
  if a.round ≠ b.round then NativePolicyBytes.bytesLT a.round b.round
  else NativePolicyBytes.bytesLT a.reason b.reason

def texts64 (xs : List Bytes) : Bytes := be 8 xs.length ++ (xs.map text64).flatten

def viewBytes (v : ViewBody) : Bytes := text64 v.round ++ be 8 v.height ++
  be 8 v.fromView ++ be 8 v.toView ++ be 8 v.deadline

def abortBytes (a : AbortBody) : Bytes := text64 a.round ++ text64 a.epoch ++
  be 8 a.height ++ be 8 a.view ++ be 8 a.deadline ++ text64 a.parent ++ text64 a.reason ++
  texts64 a.configs ++ texts64 a.inputs ++ texts64 a.eligibility ++ texts64 a.plans ++
  texts64 a.parameters ++ texts64 a.roots ++ texts64 a.applies

def viewDomain := NativeVoteBytes.ascii "deltareduce.vote.view-change-body.v1"
def abortDomain := NativeVoteBytes.ascii "deltareduce.vote.abort-body.v1"
def viewId (sha : Bytes → Bytes) (v : ViewBody) := NativeStateBytes.contentId sha viewDomain (viewBytes v)
def abortId (sha : Bytes → Bytes) (a : AbortBody) := NativeStateBytes.contentId sha abortDomain (abortBytes a)

structure Row (α : Type) where
  body : α
  source : Value
  wire : Bytes
  id : Bytes

def checkRow {α : Type} (fmt : Format) (read : Value → Option α) (hash : α → Option Bytes)
    (source : Value) : Option (Row α) := do
  let body ← read source
  let wire ← encode fmt source
  let id ← hash body
  some ⟨body,source,wire,id⟩
theorem rowSource {α : Type} {fmt read hash source} {r : Row α}
    (h : checkRow fmt read hash source = some r) :
    r.source = source ∧ read source = some r.body ∧ encode fmt source = some r.wire ∧ hash r.body = some r.id := by
  unfold checkRow at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨b,hb,w,hw,id,hi,last⟩ := h
  cases Option.some.inj last
  exact ⟨rfl,hb,hw,hi⟩
theorem rowFromComponents {α : Type} {fmt read hash source} {b : α} {w id}
    (hb : read source = some b) (hw : encode fmt source = some w) (hi : hash b = some id) :
    checkRow fmt read hash source = some ⟨b,source,w,id⟩ := by
  simp only [checkRow,hb,hw,hi,bind,Option.bind]
theorem rowDecoded {α : Type} {fmt read hash source} {r : Row α}
    (h : checkRow fmt read hash source = some r) : NativePolicyCodec.decode fmt r.wire = some source :=
  NativePolicyCodec.encoded (rowSource h).2.2.1

def checkRows {α : Type} (fmt : Format) (read : Value → Option α) (hash : α → Option Bytes) :
    List Value → Option (List (Row α))
  | [] => some []
  | v::vs => do let r ← checkRow fmt read hash v; let rs ← checkRows fmt read hash vs; some (r::rs)
theorem rowsOriginal {α : Type} {fmt read hash vs} {rs : List (Row α)}
    (h : checkRows fmt read hash vs = some rs) : rs.map Row.source = vs := by
  induction vs generalizing rs with
  | nil => simp [checkRows] at h; subst rs; rfl
  | cons v vs ih =>
    simp only [checkRows,bind,Option.bind_eq_some_iff] at h
    obtain ⟨r,hr,rest,ht,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,(rowSource hr).1,ih ht]
theorem rowsChecked {α : Type} {fmt read hash vs} {rs : List (Row α)}
    (h : checkRows fmt read hash vs = some rs) (r : Row α) (mem : r ∈ rs) :
    checkRow fmt read hash r.source = some r := by
  induction vs generalizing rs with
  | nil => simp [checkRows] at h; subst rs; simp at mem
  | cons v vs ih =>
    simp only [checkRows,bind,Option.bind_eq_some_iff] at h
    obtain ⟨x,hx,rest,hr,last⟩ := h
    cases Option.some.inj last
    rcases List.mem_cons.mp mem with rfl | mem
    · simpa only [(rowSource hx).1] using hx
    · exact ih hr mem

def checkViews (sha : Bytes → Bytes) := checkRows fmtViewChange readView (viewId sha)
def checkAborts (sha : Bytes → Bytes) := checkRows fmtAbortBody readAbort (abortId sha)
end DeltaReduce.NativeFailurePayload
