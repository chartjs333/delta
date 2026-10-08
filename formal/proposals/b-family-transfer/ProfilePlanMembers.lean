import ProfilePlan
import DeltaReduce.NativePlanMembers

/-! T047/T053. Reuse the original numeric membership/weight rules with the
approved consensus-b parent reference. No old Checked.qcId is relabeled as b,
and no legacy byte decoder is made to accept successor bytes. The source
producer must establish the same existing cross-parent coherence; this is
not an assumption of the required public refinement or a new source cap. -/
namespace DeltaReduce.ProfileSource.PlanMembers
open NativeReceiptBytes (Bytes)
open InputSection (Located)
open NativePlanMembers (Member Row)

def Parents (e : Plan.Edge) : Prop :=
  e.parent.value.certificate.body.context = e.certificate.common.context ∧
  e.ec.value.certificate.common.context = e.certificate.common.context ∧
  e.seed.value.transcript.context = e.certificate.common.context ∧
  e.ec.value.norm.value.evidence.context = e.certificate.common.context ∧
  e.certificate.common.isc = e.parent.value.consensusId ∧
  e.ec.value.certificate.common.isc = e.parent.value.consensusId ∧
  e.seed.value.transcript.isc = e.parent.value.consensusId ∧
  e.ec.value.norm.value.evidence.isc = e.parent.value.consensusId ∧
  e.certificate.common.ec = e.ec.value.id ∧ e.certificate.common.seed = e.seed.value.id ∧
  e.ec.value.seedId = e.seed.value.id ∧
  e.ec.value.norm.value.id = e.ec.value.certificate.common.norm ∧
  (e.parent.value.certificate.body.tuples.map NativeInputSetBody.Tuple.ticket).Nodup ∧
  e.ec.value.norm.value.evidence.entries.map NativeNormEvidence.Entry.ticket =
    e.parent.value.certificate.body.tuples.map NativeInputSetBody.Tuple.ticket
instance (e) : Decidable (Parents e) := by unfold Parents; infer_instance

/-- Only the shared four tuple fields are viewed by numeric membership code.
The full future body, explicit parent, original witness and bytes remain in e. -/
def tuple (t : NativeInputSetBody.Tuple) : NativeInputSetBody.Tuple :=
  ⟨t.availability,t.commitment,t.domain,t.ticket⟩

structure Bound where
  original : Located Plan.Edge
  members : List Member
  rows : List Row

def derive (original : Located Plan.Edge) : Option Bound := do
  let e := original.value
  if Parents e then
    let members ← NativePlanMembers.align
      (e.parent.value.certificate.body.tuples.map tuple) e.ec.value.certificate.common.entries
    let rows ← NativePlanMembers.attach (NativePlanMembers.eligible members)
      e.certificate.common.weights e.certificate.common.buckets
    some ⟨original,members,rows⟩
  else none

theorem derived {original out} (ok : derive original = some out) :
    out.original = original ∧ Parents original.value ∧
    NativePlanMembers.align (original.value.parent.value.certificate.body.tuples.map tuple)
      original.value.ec.value.certificate.common.entries = some out.members ∧
    NativePlanMembers.attach (NativePlanMembers.eligible out.members)
      original.value.certificate.common.weights original.value.certificate.common.buckets =
        some out.rows := by
  unfold derive at ok
  dsimp only at ok
  split at ok <;> try contradiction
  rename_i parents
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨members,hm,rows,hr,last⟩ := ok
  cases Option.some.inj last
  exact ⟨rfl,parents,hm,hr⟩

theorem complete {original members rows}
    (parents : Parents original.value)
    (hm : NativePlanMembers.align (original.value.parent.value.certificate.body.tuples.map tuple)
      original.value.ec.value.certificate.common.entries = some members)
    (hr : NativePlanMembers.attach (NativePlanMembers.eligible members)
      original.value.certificate.common.weights original.value.certificate.common.buckets = some rows) :
    derive original = some ⟨original,members,rows⟩ := by
  simp only [derive,if_pos parents,hm,hr,Bind.bind,Option.bind]

theorem allOriginalMembers {original out} (ok : derive original = some out) :
    out.members.map Member.input = original.value.parent.value.certificate.body.tuples.map tuple ∧
    out.members.map Member.eligibility = original.value.ec.value.certificate.common.entries ∧
    out.rows.map Row.member = NativePlanMembers.eligible out.members ∧
    out.rows.map Row.weight = original.value.certificate.common.weights ∧
    out.rows.map Row.bucket = original.value.certificate.common.buckets ∧
    ∀ row ∈ out.rows, NativePlanMembers.RowValid row := by
  have h := derived ok
  have a := NativePlanMembers.alignedSource h.2.2.1
  have b := NativePlanMembers.attachedSource h.2.2.2
  exact ⟨a.1,a.2.1,b⟩

theorem originalWitness {original out} (ok : derive original = some out) :
    out.original.raw = original.raw ∧ out.original.value.id = original.value.id ∧
    out.original.value.certificate.signers = original.value.certificate.signers ∧
    out.original.value.parent.raw = original.value.parent.raw ∧
    out.original.value.parent.value.consensusId = original.value.parent.value.consensusId ∧
    out.original.value.parent.value.witnessId = original.value.parent.value.witnessId := by
  rw [(derived ok).1]
  exact ⟨rfl,rfl,rfl,rfl,rfl,rfl⟩

/-- Equal consensus bodies permit different retained certificate witnesses.
Numeric membership is witness-independent, but the carrier is never merged. -/
theorem witnessIndependentRows (original : Located Plan.Edge)
    (other : Located ISCSourceV2.BoundCertificate)
    (body : other.value.certificate.body = original.value.parent.value.certificate.body)
    (consensus : other.value.consensusId = original.value.parent.value.consensusId) :
    (derive { original with value := { original.value with parent := other } }).map Bound.rows =
      (derive original).map Bound.rows := by
  unfold derive
  dsimp only
  simp only [Parents,body,consensus]
  split <;> simp only [Option.map_none,Bind.bind,Option.bind]
  · cases NativePlanMembers.align
        (original.value.parent.value.certificate.body.tuples.map tuple)
        original.value.ec.value.certificate.common.entries with
    | none => rfl
    | some members =>
      dsimp only
      cases NativePlanMembers.attach (NativePlanMembers.eligible members)
        original.value.certificate.common.weights original.value.certificate.common.buckets <;> rfl

end DeltaReduce.ProfileSource.PlanMembers
