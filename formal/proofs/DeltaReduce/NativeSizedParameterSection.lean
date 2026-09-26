import DeltaReduce.NativeParameterSection
import DeltaReduce.NativeContractSize

/-! Add the original native certificate JSON byte bound to every certificate
view in the checked parent/PARAMETER section. This is not full policy admission. -/
namespace DeltaReduce.NativeSizedParameterSection
open NativeReceiptBytes NativeContractSize NativePolicyBytes NativeStateBytes

def iscRow (c : NativeIscCertificate.Checked) : Row :=
  ⟨"ISC",c.source,NativeIscCertificate.domain,NativeIscCertificate.json c.certificate,some c.qcId⟩
def normRow (c : NativeNormEvidence.Checked) : Row :=
  ⟨"NORM",c.source,NativeNormEvidence.domain,NativeNormEvidence.json c.evidence,some c.id⟩
def seedRow (c : NativeSeedTranscript.Checked) : Row :=
  ⟨"SEED",c.source,NativeSeedTranscript.domain,NativeSeedTranscript.json c.transcript,some c.id⟩
def ecRow (finalized : Bool) (c : NativeEligibilityLineage.Edge) : Row :=
  ⟨if finalized then "EC_FINAL" else "EC_PROPOSED",c.source,NativeEligibility.domain,
    NativeEligibility.json c.certificate,if finalized then some c.id else none⟩
def planRow (finalized : Bool) (c : NativePlanLineage.Edge) : Row :=
  ⟨if finalized then "APC_FINAL" else "APC_PROPOSED",c.source,NativePlan.domain,
    NativePlan.json c.certificate,if finalized then some c.id else none⟩
def parameterRow (finalized : Bool) (c : NativeParameterLineage.Edge) : Row :=
  ⟨if finalized then "PARAMETER_FINAL" else "PARAMETER_PROPOSED",c.source,NativeParameter.domain,
    NativeParameter.json c.certificate,if finalized then some c.id else none⟩

def groups (b : NativeParameterSection.Bound) : List (List Row) :=
  [b.plans.eligibility.norms.isc.certificates.map iscRow,
   b.plans.eligibility.norms.norms.map normRow,
   b.plans.eligibility.seeds.map seedRow,
   b.plans.eligibility.bodies.map (ecRow false),
   b.plans.eligibility.certificates.map (ecRow true),
   b.plans.bodies.map (planRow false),b.plans.certificates.map (planRow true),
   b.bodies.map (parameterRow false),b.certificates.map (parameterRow true)]

def rows (b : NativeParameterSection.Bound) : List Row := (groups b).flatten

theorem groupsCount (b : NativeParameterSection.Bound) : (groups b).length = 9 := rfl

theorem groupLengths (b : NativeParameterSection.Bound) :
    (groups b).map List.length =
    [b.plans.eligibility.norms.isc.certificates.length,b.plans.eligibility.norms.norms.length,
     b.plans.eligibility.seeds.length,b.plans.eligibility.bodies.length,
     b.plans.eligibility.certificates.length,b.plans.bodies.length,b.plans.certificates.length,
     b.bodies.length,b.certificates.length] := by simp [groups]

structure Bound where
  prior : NativeParameterSection.Bound
  checked : List Checked

def bindSection (sha : Bytes → Bytes) (p : Policy) (s : State) : Option Bound := do
  let b ← NativeParameterSection.bindSection sha p s
  let checked ← checkAll sha (rows b)
  some ⟨b,checked⟩

theorem checkedSource {sha p s b} (h : bindSection sha p s = some b) :
    NativeParameterSection.bindSection sha p s = some b.prior ∧
    checkAll sha (rows b.prior) = some b.checked := by
  unfold bindSection at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨prior,hs,checked,hc,last⟩ := h
  cases Option.some.inj last
  exact ⟨hs,hc⟩

theorem fromComponents {sha p s prior checked}
    (hs : NativeParameterSection.bindSection sha p s = some prior)
    (hc : checkAll sha (rows prior) = some checked) :
    bindSection sha p s = some ⟨prior,checked⟩ := by
  simp only [bindSection,hs,hc,bind,Option.bind]

theorem originalSection {sha p s b} (h : bindSection sha p s = some b) :
    NativeParameterSection.Source sha p s b.prior :=
  NativeParameterSection.checkedSource (checkedSource h).1

theorem everyCertificateBound {sha p s b row} (h : bindSection sha p s = some b)
    (mem : row ∈ rows b.prior) : row.payload.length ≤ maxBytes :=
  allBounds (checkedSource h).2 row mem

theorem everyCheckedHash {sha p s b out} (h : bindSection sha p s = some b)
    (mem : out ∈ b.checked) :
    NativeStateBytes.contentId sha out.row.domain out.row.payload = some out.id ∧
    (out.row.expected = none ∨ out.row.expected = some out.id) :=
  (NativeContractSize.checkedSource (allChecked (checkedSource h).2 out mem)).2.2

theorem exactPayloads {sha p s b} (h : bindSection sha p s = some b) :
    b.checked.map Checked.row = rows b.prior := allSources (checkedSource h).2

theorem exactCount {sha p s b} (h : bindSection sha p s = some b) :
    b.checked.length = (rows b.prior).length := NativeContractSize.exactCount (checkedSource h).2

theorem exactPosition {sha p s b} {i : Nat} {out : Checked} (h : bindSection sha p s = some b)
    (atIndex : b.checked[i]? = some out) : (rows b.prior)[i]? = some out.row :=
  NativeContractSize.exactPosition (checkedSource h).2 atIndex

theorem allGroupBounds {sha p s b group row} (h : bindSection sha p s = some b)
    (hg : group ∈ groups b.prior) (hr : row ∈ group) : row.payload.length ≤ maxBytes :=
  everyCertificateBound h (List.mem_flatten.mpr ⟨group,hg,hr⟩)

theorem oversizedSectionRejected {sha p s prior row}
    (hs : NativeParameterSection.bindSection sha p s = some prior)
    (mem : row ∈ rows prior) (over : maxBytes < row.payload.length) :
    bindSection sha p s = none := by
  simp only [bindSection,hs,bind,Option.bind,oversizedListRejected mem over]

theorem oldFailureRejected {sha p s}
    (h : NativeParameterSection.bindSection sha p s = none) : bindSection sha p s = none := by
  simp only [bindSection,h,bind,Option.bind]

def prepare (sha : Bytes → Bytes) (policyRaw stateRaw : Bytes) : Option Bound := do
  let (_,p) ← NativePolicyBytes.decodePolicy policyRaw
  let s ← NativeStateBytes.decodeState stateRaw
  bindSection sha p s

theorem preparedSource {sha policyRaw stateRaw b} (h : prepare sha policyRaw stateRaw = some b) :
    ∃ tree p s, NativePolicyBytes.decodePolicy policyRaw = some (tree,p) ∧
    NativeStateBytes.decodeState stateRaw = some s ∧
    NativeParameterSection.Source sha p s b.prior ∧
    b.checked.map Checked.row = rows b.prior ∧
    ∀ row ∈ rows b.prior, row.payload.length ≤ maxBytes := by
  unfold prepare at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨tree,p⟩,hp,s,hs,hb⟩ := h
  exact ⟨tree,p,s,hp,hs,originalSection hb,exactPayloads hb,fun _ hm => everyCertificateBound hb hm⟩

end DeltaReduce.NativeSizedParameterSection
