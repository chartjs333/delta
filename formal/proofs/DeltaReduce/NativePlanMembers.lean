import DeltaReduce.NativePlanSection

/-! Complete original ISC/EC membership joined to original final APC alpha.
The public entry point decodes policy/state bytes itself. Hashes, signatures,
policy provenance and the EC-to-seed primitive are not authenticated here. -/
namespace DeltaReduce.NativePlanMembers
open NativeReceiptBytes (Bytes)
open NativeInputSetBody (Tuple)
open NativeEligibility (Entry)
open NativePlan (Weight Bucket)

structure Member where
  input : Tuple
  eligibility : Entry
  deriving DecidableEq, Repr
def SameMember (t : Tuple) (e : Entry) : Prop :=
  t.ticket = e.ticket ∧ t.domain = e.domain ∧ (e.accepted = 0 ∨ e.accepted = 1)
instance (t e) : Decidable (SameMember t e) := by unfold SameMember; infer_instance
def align : List Tuple → List Entry → Option (List Member)
  | [],[] => some []
  | t::ts,e::es => do
    if SameMember t e then
      let rest ← align ts es
      some (⟨t,e⟩::rest)
    else none
  | _,_ => none

theorem alignedSource {ts es ms} (h : align ts es = some ms) :
    ms.map Member.input = ts ∧ ms.map Member.eligibility = es ∧
    ∀ m ∈ ms, SameMember m.input m.eligibility := by
  induction ts generalizing es ms with
  | nil => cases es <;> simp [align] at h; subst ms; simp
  | cons t ts ih =>
    cases es with
    | nil => simp [align] at h
    | cons e es =>
      simp only [align] at h
      split at h <;> try contradiction
      rename_i valid
      simp only [bind,Option.bind_eq_some_iff] at h
      obtain ⟨rest,hr,last⟩ := h
      cases Option.some.inj last
      have src := ih hr
      exact ⟨by simp [src.1],by simp [src.2.1],by
        intro m hm; rcases List.mem_cons.mp hm with rfl | hm
        · exact valid
        · exact src.2.2 m hm⟩

def eligible (ms : List Member) := ms.filter (fun m => m.eligibility.accepted != 0)
structure Row where
  member : Member
  weight : Weight
  bucket : Bucket
  deriving DecidableEq, Repr
def RowValid (r : Row) : Prop :=
  SameMember r.member.input r.member.eligibility ∧ r.member.eligibility.accepted = 1 ∧
  r.weight.ticket = r.member.input.ticket ∧ r.bucket.ticket = r.member.input.ticket ∧
  NativePlan.WeightValid r.weight
instance (r) : Decidable (RowValid r) := by unfold RowValid; infer_instance
def attach : List Member → List Weight → List Bucket → Option (List Row)
  | [],[],[] => some []
  | m::ms,w::ws,b::bs => do
    let row := Row.mk m w b
    if RowValid row then
      let rest ← attach ms ws bs
      some (row::rest)
    else none
  | _,_,_ => none

theorem attachedSource {ms ws bs rs} (h : attach ms ws bs = some rs) :
    rs.map Row.member = ms ∧ rs.map Row.weight = ws ∧ rs.map Row.bucket = bs ∧
    ∀ r ∈ rs, RowValid r := by
  induction ms generalizing ws bs rs with
  | nil => cases ws <;> cases bs <;> simp [attach] at h; subst rs; simp
  | cons m ms ih =>
    cases ws with
    | nil => simp [attach] at h
    | cons w ws =>
      cases bs with
      | nil => simp [attach] at h
      | cons b bs =>
        simp only [attach] at h
        split at h <;> try contradiction
        rename_i valid
        simp only [bind,Option.bind_eq_some_iff] at h
        obtain ⟨rest,hr,last⟩ := h
        cases Option.some.inj last
        have src := ih hr
        exact ⟨by simp [src.1],by simp [src.2.1],by simp [src.2.2.1],by
          intro r hm; rcases List.mem_cons.mp hm with rfl | hm
          · exact valid
          · exact src.2.2.2 r hm⟩

/-- Additional projection checks, not a claim of equivalence to isolated native
verify_plan. In particular the complete rejected EC membership is retained. -/
def CrossParents (e : NativePlanLineage.Edge) : Prop :=
  e.parent.certificate.body.context = e.certificate.common.context ∧
  e.ec.certificate.common.context = e.certificate.common.context ∧
  e.seed.transcript.context = e.certificate.common.context ∧
  e.ec.norm.evidence.context = e.certificate.common.context ∧
  e.certificate.common.isc = e.parent.qcId ∧
  e.ec.certificate.common.isc = e.parent.qcId ∧
  e.seed.transcript.isc = e.parent.qcId ∧ e.ec.norm.evidence.isc = e.parent.qcId ∧
  e.certificate.common.ec = e.ec.id ∧ e.certificate.common.seed = e.seed.id ∧
  e.ec.seedId = e.seed.id ∧ e.ec.norm.id = e.ec.certificate.common.norm ∧
  (e.parent.certificate.body.tuples.map Tuple.ticket).Nodup ∧
  e.parent.certificate.body.tuples.length ≤ 4096 ∧
  e.ec.norm.evidence.entries.map NativeNormEvidence.Entry.ticket =
    e.parent.certificate.body.tuples.map Tuple.ticket
instance (e) : Decidable (CrossParents e) := by unfold CrossParents; infer_instance

def derive (e : NativePlanLineage.Edge) : Option (List Row) := do
  if CrossParents e then
    let all ← align e.parent.certificate.body.tuples e.ec.certificate.common.entries
    attach (eligible all) e.certificate.common.weights e.certificate.common.buckets
  else none
structure Derived (e : NativePlanLineage.Edge) (rs : List Row) : Prop where
  parents : CrossParents e
  members : ∃ all, align e.parent.certificate.body.tuples e.ec.certificate.common.entries = some all ∧
    attach (eligible all) e.certificate.common.weights e.certificate.common.buckets = some rs

theorem derivedSource {e rs} (h : derive e = some rs) : Derived e rs := by
  unfold derive at h; split at h <;> try contradiction
  rename_i parents
  simp only [bind,Option.bind_eq_some_iff] at h
  exact ⟨parents,h⟩

theorem fullOriginalCoverage {e rs} (h : derive e = some rs) :
    rs.map Row.weight = e.certificate.common.weights ∧
    rs.map Row.bucket = e.certificate.common.buckets ∧
    ∀ r ∈ rs, RowValid r := by
  obtain ⟨all,_,ha⟩ := (derivedSource h).members
  exact (attachedSource ha).2

theorem completeEligibility {e rs} (h : derive e = some rs) :
    ∃ all, all.map Member.input = e.parent.certificate.body.tuples ∧
      all.map Member.eligibility = e.ec.certificate.common.entries ∧
      rs.map Row.member = eligible all := by
  obtain ⟨all,hm,ha⟩ := (derivedSource h).members
  exact ⟨all,(alignedSource hm).1,(alignedSource hm).2.1,(attachedSource ha).1⟩

structure Bound where
  plans : NativePlanSection.Bound
  edge : NativePlanLineage.Edge
  rows : List Row

def prepare (sha : Bytes → Bytes) (policyRaw stateRaw apcId : Bytes) : Option Bound := do
  let s ← NativePlanSection.prepare sha policyRaw stateRaw
  let e ← s.certificates.find? (fun e => e.id == apcId)
  if apcId ∈ s.finalized then
    let rows ← derive e
    some ⟨s,e,rows⟩
  else none

structure Source (sha : Bytes → Bytes) (policyRaw stateRaw apcId : Bytes) (b : Bound) : Prop where
  plans : NativePlanSection.prepare sha policyRaw stateRaw = some b.plans
  edge : b.plans.certificates.find? (fun e => e.id == apcId) = some b.edge
  finalized : apcId ∈ b.plans.finalized
  rows : derive b.edge = some b.rows

theorem preparedSource {sha policyRaw stateRaw apcId b}
    (h : prepare sha policyRaw stateRaw apcId = some b) : Source sha policyRaw stateRaw apcId b := by
  simp only [prepare,bind,Option.bind_eq_some_iff] at h
  obtain ⟨s,hs,e,he,last⟩ := h
  split at last <;> try contradiction
  rename_i finalized
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨rows,hr,last⟩ := last
  cases Option.some.inj last
  exact ⟨hs,he,finalized,hr⟩

theorem prepareFromSource {sha policyRaw stateRaw apcId b}
    (h : Source sha policyRaw stateRaw apcId b) : prepare sha policyRaw stateRaw apcId = some b := by
  simp only [prepare,h.plans,h.edge,bind,Option.bind,if_pos h.finalized,h.rows]

theorem actualSourceSection {sha policyRaw stateRaw apcId b}
    (h : prepare sha policyRaw stateRaw apcId = some b) :
    ∃ tree p s, NativePolicyBytes.decodePolicy policyRaw = some (tree,p) ∧
      NativeStateBytes.decodeState stateRaw = some s ∧
      NativePlanSection.Source sha p s b.plans ∧
      b.edge ∈ b.plans.certificates ∧ b.edge.id = apcId := by
  have src := preparedSource h
  obtain ⟨tree,p,s,hp,hs,hsrc⟩ := NativePlanSection.preparedSource src.plans
  exact ⟨tree,p,s,hp,hs,hsrc,List.mem_of_find?_eq_some src.edge,
    by simpa using List.find?_some src.edge⟩
end DeltaReduce.NativePlanMembers
