import DeltaReduce.NativeIscCertificate
import DeltaReduce.NativeContractSize

/-! Original proposed ISC bodies expanded with the actual configured committee.
The binary body identity and bounded JSON certificate identity stay distinct.
This is shape/identity verification, not signature or ledger authentication. -/
namespace DeltaReduce.NativeProposedIsc
open NativeReceiptBytes NativePolicyCodec
open NativeInputSetBody (Body Context)
open NativeIscCertificate (Certificate)

def certificate (committee : List Bytes) (body : Body) : Certificate :=
  ⟨body,NativeIscCertificate.quorum committee,committee⟩

structure Checked where
  body : NativeInputSetBody.Checked
  qcId : Bytes

def check (sha : Bytes → Bytes) (expected : Context) (committee : List Bytes)
    (source : Value) : Option Checked := do
  let body ← NativeInputSetBody.check sha expected source
  let c := certificate committee body.body
  if NativeIscCertificate.Valid expected committee c then
    let qc ← NativeContractSize.contentId sha NativeIscCertificate.domain (NativeIscCertificate.json c)
    some ⟨body,qc⟩
  else none

structure Source (sha : Bytes → Bytes) (expected : Context) (committee : List Bytes)
    (source : Value) (out : Checked) : Prop where
  body : NativeInputSetBody.check sha expected source = some out.body
  valid : NativeIscCertificate.Valid expected committee (certificate committee out.body.body)
  bounded : NativeContractSize.contentId sha NativeIscCertificate.domain
    (NativeIscCertificate.json (certificate committee out.body.body)) = some out.qcId

theorem checkedSource {sha expected committee source out}
    (h : check sha expected committee source = some out) : Source sha expected committee source out := by
  unfold check at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨body,hb,last⟩ := h
  split at last <;> try contradiction
  rename_i valid
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨qc,hq,eq⟩ := last
  cases Option.some.inj eq
  exact ⟨hb,valid,hq⟩

theorem fromComponents {sha expected committee source out}
    (h : Source sha expected committee source out) : check sha expected committee source = some out := by
  simp only [check,h.body,bind,Option.bind,if_pos h.valid,h.bounded]

theorem originalBody {sha expected committee source out}
    (h : check sha expected committee source = some out) :
    NativeInputSetBody.CheckedSource sha expected source out.body :=
  NativeInputSetBody.checkSource (checkedSource h).body

theorem computedCertificate {sha expected committee source out}
    (h : check sha expected committee source = some out) :
    (NativeIscCertificate.json (certificate committee out.body.body)).length ≤ NativeContractSize.maxBytes ∧
    NativeIscCertificate.id sha (certificate committee out.body.body) = some out.qcId :=
  NativeContractSize.accepted (checkedSource h).bounded

theorem allConfiguredSigners {sha expected committee source out}
    (h : check sha expected committee source = some out) :
    ∀ signer ∈ committee, NativeConfigAdmission.Label signer := by
  intro signer member
  exact ((checkedSource h).valid.2.2.2.2.2.2.2.2 signer member).1

theorem originalContext {sha expected committee source out}
    (h : check sha expected committee source = some out) : out.body.body.context = expected :=
  (checkedSource h).valid.2.1.2.1

theorem originalTuples {sha expected committee source out}
    (h : check sha expected committee source = some out) :
    ∀ t ∈ out.body.body.tuples, NativeInputSetBody.TupleValid t :=
  (NativeInputSetBody.noTupleErasure (checkedSource h).body).2

theorem oversizedRejected {sha expected committee source body}
    (hb : NativeInputSetBody.check sha expected source = some body)
    (large : NativeContractSize.maxBytes <
      (NativeIscCertificate.json (certificate committee body.body)).length) :
    check sha expected committee source = none := by
  simp only [check,hb,bind,Option.bind]
  split <;> simp only [NativeContractSize.oversized large]

theorem nonLabelSignerRejected {sha expected committee source out signer}
    (mem : signer ∈ committee) (bad : ¬ NativeConfigAdmission.Label signer) :
    check sha expected committee source ≠ some out := by
  intro h; exact bad (allConfiguredSigners h signer mem)

def checkAll (sha : Bytes → Bytes) (expected : Context) (committee : List Bytes) :
    List Value → Option (List Checked)
  | [] => some []
  | source::sources => do
    let out ← check sha expected committee source
    let rest ← checkAll sha expected committee sources
    some (out::rest)

theorem listFromComponents {sha expected committee source sources out rest}
    (first : check sha expected committee source = some out)
    (tail : checkAll sha expected committee sources = some rest) :
    checkAll sha expected committee (source::sources) = some (out::rest) := by
  simp only [checkAll,first,tail,bind,Option.bind]

theorem allSources {sha expected committee sources outs}
    (h : checkAll sha expected committee sources = some outs) :
    outs.map (fun x => x.body.source) = sources := by
  induction sources generalizing outs with
  | nil => simp [checkAll] at h; subst outs; rfl
  | cons source sources ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨out,ho,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,(originalBody ho).1,ih hr]

theorem allChecked {sha expected committee sources outs}
    (h : checkAll sha expected committee sources = some outs) (out : Checked) (mem : out ∈ outs) :
    Source sha expected committee out.body.source out := by
  induction sources generalizing outs with
  | nil => simp [checkAll] at h; subst outs; simp at mem
  | cons source sources ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨first,hf,rest,hr,last⟩ := h
    cases Option.some.inj last
    rcases List.mem_cons.mp mem with rfl | mem
    · simpa only [(originalBody hf).1] using checkedSource hf
    · exact ih hr mem

theorem exactCount {sha expected committee sources outs}
    (h : checkAll sha expected committee sources = some outs) : outs.length = sources.length := by
  have eq := congrArg List.length (allSources h); simpa using eq

theorem exactPosition {sha expected committee sources outs} {i : Nat} {out : Checked}
    (h : checkAll sha expected committee sources = some outs) (atIndex : outs[i]? = some out) :
    sources[i]? = some out.body.source := by
  rw [← allSources h,List.getElem?_map,atIndex]; rfl

end DeltaReduce.NativeProposedIsc
