import DeltaReduce.NativeApplyCertificate

/-! Actual proposed/finalized APPLY source joins. The bounded preceding ROOT
section is composed separately; here no arithmetic approval callback is used. -/
namespace DeltaReduce.NativeApplyLineage
open NativeReceiptBytes NativePolicyCodec NativePolicySchema NativeApplyCertificate
open NativeInputSetBody (Context)
open NativeParameterLineage (Mode)
structure Decoded where
  candidate : Candidate
  certificate : Certificate
  candidateId : Bytes

def decode (sha : Bytes → Bytes) (mode : Mode) (committee : List Bytes) (source : Value) : Option Decoded :=
  match mode with
  | .proposed => do
    let b ← readCandidate source
    let bid ← NativeApplyCertificate.candidateId sha b
    some ⟨b,proposedCertificate committee b bid,bid⟩
  | .finalized => do
    let f ← readFinalized source
    let bid ← NativeApplyCertificate.candidateId sha f.candidate
    some ⟨f.candidate,f.certificate,bid⟩
def original (mode : Mode) (d : Decoded) : Value :=
  match mode with
  | .proposed => candidateValue d.candidate
  | .finalized => finalizedValue ⟨d.certificate,d.candidate⟩
theorem decodedOriginal {sha mode committee source d} (h : decode sha mode committee source = some d) :
    source = original mode d ∧ NativeApplyCertificate.candidateId sha d.candidate = some d.candidateId := by
  cases mode with
  | proposed =>
    simp only [decode,bind,Option.bind_eq_some_iff] at h
    obtain ⟨b,hb,bid,hi,last⟩ := h
    cases Option.some.inj last
    exact ⟨candidateOriginal hb,hi⟩
  | finalized =>
    simp only [decode,bind,Option.bind_eq_some_iff] at h
    obtain ⟨f,hf,bid,hi,last⟩ := h
    cases Option.some.inj last
    exact ⟨finalizedOriginal hf,hi⟩

def Links (parent : Bytes) (finalized : List Bytes) (d : Decoded)
    (root : NativeAggregateLineage.Edge) (profile : NativeApplyProfile.Checked) : Prop :=
  root.id ∈ finalized ∧ d.candidate.parent = parent ∧
  d.candidate.root = root.id ∧ d.certificate.root = root.id ∧
  d.candidate.profile = profile.id ∧ d.certificate.profile = profile.id ∧
  d.certificate.candidate = d.candidateId ∧
  d.certificate.parent = d.candidate.parent ∧ d.certificate.model = d.candidate.model ∧
  d.certificate.optimizer = d.candidate.optimizer
instance (parent finalized d root profile) : Decidable (Links parent finalized d root profile) := by unfold Links; infer_instance

def resultId (mode : Mode) (d : Decoded) (qc : Bytes) : Bytes :=
  match mode with | .proposed => d.candidateId | .finalized => qc
structure Edge where
  decoded : Decoded
  source : Value
  root : NativeAggregateLineage.Edge
  profile : NativeApplyProfile.Checked
  qc : Bytes
  id : Bytes

def check (sha : Bytes → Bytes) (mode : Mode) (expected : Context) (committee : List Bytes)
    (parent : Bytes) (finalized : List Bytes) (roots : List NativeAggregateLineage.Edge)
    (profiles : List NativeApplyProfile.Checked) (source : Value) : Option Edge := do
  let d ← decode sha mode committee source
  let root ← roots.find? (fun r => r.id == d.certificate.root)
  let profile ← profiles.find? (fun p => p.id == d.certificate.profile)
  if CandidateValid expected d.candidate ∧ CertificateValid expected committee d.certificate ∧
      Links parent finalized d root profile then
    let qc ← certificateId sha d.certificate
    some ⟨d,source,root,profile,qc,resultId mode d qc⟩
  else none

structure Source (sha : Bytes → Bytes) (mode : Mode) (expected : Context) (committee : List Bytes)
    (parent : Bytes) (finalized : List Bytes) (roots : List NativeAggregateLineage.Edge)
    (profiles : List NativeApplyProfile.Checked) (source : Value) (e : Edge) : Prop where
  originalSource : e.source = source
  decoded : decode sha mode committee source = some e.decoded
  root : roots.find? (fun r => r.id == e.decoded.certificate.root) = some e.root
  profile : profiles.find? (fun p => p.id == e.decoded.certificate.profile) = some e.profile
  candidateValid : CandidateValid expected e.decoded.candidate
  certificateValid : CertificateValid expected committee e.decoded.certificate
  links : Links parent finalized e.decoded e.root e.profile
  qc : certificateId sha e.decoded.certificate = some e.qc
  identity : e.id = resultId mode e.decoded e.qc

theorem checkedSource {sha mode expected committee parent finalized roots profiles source e}
    (h : check sha mode expected committee parent finalized roots profiles source = some e) :
    Source sha mode expected committee parent finalized roots profiles source e := by
  unfold check at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨d,hd,root,hr,profile,hp,last⟩ := h
  split at last <;> try contradiction
  rename_i valid
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨qc,hq,last⟩ := last
  cases Option.some.inj last
  exact ⟨rfl,hd,hr,hp,valid.1,valid.2.1,valid.2.2,hq,rfl⟩

theorem fromComponents {sha mode expected committee parent finalized roots profiles source e}
    (h : Source sha mode expected committee parent finalized roots profiles source e) :
    check sha mode expected committee parent finalized roots profiles source = some e := by
  unfold check
  rw [h.decoded]
  dsimp only [bind,Option.bind]
  rw [h.root,h.profile]
  dsimp only [bind,Option.bind]
  rw [if_pos ⟨h.candidateValid,h.certificateValid,h.links⟩,h.qc]
  dsimp only [bind,Option.bind]
  rw [← h.originalSource,← h.identity]

theorem originalPayload {sha mode expected committee parent finalized roots profiles source e}
    (h : check sha mode expected committee parent finalized roots profiles source = some e) :
    source = original mode e.decoded ∧
    NativeApplyCertificate.candidateId sha e.decoded.candidate = some e.decoded.candidateId :=
  decodedOriginal (checkedSource h).decoded

theorem actualParents {sha mode expected committee parent finalized roots profiles source e}
    (h : check sha mode expected committee parent finalized roots profiles source = some e) :
    e.root ∈ roots ∧ e.profile ∈ profiles ∧ Links parent finalized e.decoded e.root e.profile :=
  ⟨List.mem_of_find?_eq_some (checkedSource h).root,
   List.mem_of_find?_eq_some (checkedSource h).profile,(checkedSource h).links⟩

theorem bothPayloadBounds {sha mode expected committee parent finalized roots profiles source e}
    (h : check sha mode expected committee parent finalized roots profiles source = some e) :
    (candidateJSON e.decoded.candidate).length ≤ NativeContractSize.maxBytes ∧
    (certificateJSON e.decoded.certificate).length ≤ NativeContractSize.maxBytes :=
  ⟨(candidateBound (originalPayload h).2).1,(certificateBound (checkedSource h).qc).1⟩

theorem exactCurrent {sha mode expected committee parent finalized roots profiles source e}
    (h : check sha mode expected committee parent finalized roots profiles source = some e) :
    e.decoded.candidate.parent = parent := (checkedSource h).links.2.1

theorem certifiedFields {sha mode expected committee parent finalized roots profiles source e}
    (h : check sha mode expected committee parent finalized roots profiles source = some e) :
    e.decoded.certificate.candidate = e.decoded.candidateId ∧
    e.decoded.certificate.parent = e.decoded.candidate.parent ∧
    e.decoded.certificate.model = e.decoded.candidate.model ∧
    e.decoded.certificate.optimizer = e.decoded.candidate.optimizer :=
  (checkedSource h).links.2.2.2.2.2.2

def checkAll (sha : Bytes → Bytes) (mode : Mode) (expected : Context) (committee : List Bytes)
    (parent : Bytes) (finalized : List Bytes) (roots : List NativeAggregateLineage.Edge)
    (profiles : List NativeApplyProfile.Checked) : List Value → Option (List Edge)
  | [] => some []
  | v::vs => do
    let e ← check sha mode expected committee parent finalized roots profiles v
    let es ← checkAll sha mode expected committee parent finalized roots profiles vs
    some (e::es)
theorem allSources {sha mode expected committee parent finalized roots profiles vs es}
    (h : checkAll sha mode expected committee parent finalized roots profiles vs = some es) : es.map Edge.source = vs := by
  induction vs generalizing es with
  | nil => simp [checkAll] at h; subst es; rfl
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨e,he,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,(checkedSource he).originalSource,ih hr]
theorem allChecked {sha mode expected committee parent finalized roots profiles vs es}
    (h : checkAll sha mode expected committee parent finalized roots profiles vs = some es) (e : Edge) (mem : e ∈ es) :
    check sha mode expected committee parent finalized roots profiles e.source = some e := by
  induction vs generalizing es with
  | nil => simp [checkAll] at h; subst es; simp at mem
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨x,hx,rest,hr,last⟩ := h
    cases Option.some.inj last
    rcases List.mem_cons.mp mem with rfl | mem
    · simpa only [(checkedSource hx).originalSource] using hx
    · exact ih hr mem
end DeltaReduce.NativeApplyLineage
