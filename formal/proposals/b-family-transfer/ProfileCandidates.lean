import ProfileCollections
import DeltaReduce.NativeCandidateShape
import DeltaReduce.NativeFailureAuthority

/-! T047/T053. All nine original candidate kinds over one successor snapshot.
Existing pure native guards are retained, including VIEW/ABORT. This is static
candidate authority only, not original vote/sign/barrier history or liveness. -/
namespace DeltaReduce.ProfileSource.Candidates
open NativeReceiptBytes NativePolicyCodec
open NativePolicyBytes (Policy Candidate)
open NativeCandidateShape (Parents)
open Collections (Bound stateView)

def parentContext (sha : Bytes → Bytes) (domain : String) (parent : Bytes) : Option Bytes :=
  if NativeVoteBytes.ContentId parent then
    NativeStateBytes.contentId sha (NativeVoteBytes.ascii domain) (NativeInputSetBody.text64 parent)
  else none

def Config (sha : Bytes → Bytes) (p : Policy) (s : NativeHeader.Coarse)
    (b : Bound) (c : Candidate) : Prop :=
  c.body ∈ b.proposedConfigs ∧
  NativeConfigAdmission.configContext sha s.height p.epoch = some c.context
instance (sha p s b c) : Decidable (Config sha p s b c) := by unfold Config; infer_instance

def Isc (sha : Bytes → Bytes) (p : Policy) (b : Bound) (c : Candidate) : Prop :=
  c.body ∈ b.eligibility.lineage.inputs.closed ∧
  (b.eligibility.lineage.inputs.bodies.find? (fun x => x.value.consensusId == c.body)).isSome = true ∧
  NativeIscAdmission.iscContext sha p.round = some c.context
instance (sha p b c) : Decidable (Isc sha p b c) := by unfold Isc; infer_instance

def Ec (sha : Bytes → Bytes) (b : Bound) (c : Candidate) (r : Parents)
    (e : Eligibility.Edge) : Prop :=
  e.certificate.common.isc ∈ b.eligibility.lineage.inputs.finalized ∧
  r.isc = e.certificate.common.isc ∧ r.seed = e.seedId ∧ r.norm = e.certificate.common.norm ∧
  parentContext sha "deltareduce.vote-context.ec.v1" e.certificate.common.isc = some c.context
instance (sha b c r e) : Decidable (Ec sha b c r e) := by unfold Ec; infer_instance

def PlanChecks (sha : Bytes → Bytes) (b : Bound) (c : Candidate) (r : Parents)
    (e : Plan.Edge) (ec : Eligibility.Edge) : Prop :=
  e.certificate.common.isc ∈ b.eligibility.lineage.inputs.finalized ∧
  e.certificate.common.ec ∈ b.eligibility.finalized ∧
  r.isc = e.certificate.common.isc ∧ r.seed = e.certificate.common.seed ∧
  r.ec = e.certificate.common.ec ∧ r.norm = ec.certificate.common.norm ∧
  parentContext sha "deltareduce.vote-context.apc.v1" e.certificate.common.ec = some c.context
instance (sha b c r e ec) : Decidable (PlanChecks sha b c r e ec) := by
  unfold PlanChecks; infer_instance

def ParameterChecks (b : Bound) (c : Candidate) (r : Parents)
    (e : Parameter.Edge) (plan : Plan.Edge) : Prop :=
  e.voteContext = c.context ∧ e.voteContext ≠ [] ∧
  e.certificate.common.plan ∈ b.plans.finalized ∧
  r.isc = e.certificate.common.isc ∧ r.ec = e.certificate.common.ec ∧
  r.plan = e.certificate.common.plan ∧ r.domain = e.certificate.common.domain ∧
  r.shard = e.certificate.common.shard ∧ r.seed = plan.certificate.common.seed
instance (b c r e plan) : Decidable (ParameterChecks b c r e plan) := by
  unfold ParameterChecks; infer_instance

def Root (sha : Bytes → Bytes) (b : Bound) (c : Candidate) (r : Parents)
    (e : Aggregate.Edge) (plan : Plan.Edge) : Prop :=
  e.certificate.common.plan ∈ b.plans.finalized ∧
  r.isc = e.certificate.common.isc ∧ r.ec = e.certificate.common.ec ∧
  r.plan = e.certificate.common.plan ∧ r.matrix = e.certificate.common.merkle ∧
  r.seed = plan.certificate.common.seed ∧
  parentContext sha "deltareduce.vote-context.root.v1" e.certificate.common.plan = some c.context
instance (sha b c r e plan) : Decidable (Root sha b c r e plan) := by unfold Root; infer_instance

def ApplyChecks (sha : Bytes → Bytes) (s : NativeHeader.Coarse) (b : Bound)
    (c : Candidate) (r : Parents) (e : Apply.Edge) : Prop :=
  e.decoded.candidate.root ∈ b.roots.finalized ∧
  r.root = e.decoded.candidate.root ∧ r.profile = e.decoded.candidate.profile ∧
  r.apply = e.decoded.candidateId ∧ e.decoded.candidate.parent = s.parent ∧
  parentContext sha "deltareduce.vote-context.apply.v1" e.decoded.candidate.root = some c.context
instance (sha s b c r e) : Decidable (ApplyChecks sha s b c r e) := by
  unfold ApplyChecks; infer_instance

def Authority (sha : Bytes → Bytes) (p : Policy) (s : NativeHeader.Coarse)
    (b : Bound) (c : Candidate) (r : Parents) : Prop :=
  match c.action with
  | 1 => Config sha p s b c
  | 2 => Isc sha p b c
  | 3 => match b.eligibility.bodies.find? (fun x => x.value.id == c.body) with
    | some e => Ec sha b c r e.value
    | none => False
  | 4 => match b.plans.bodies.find? (fun x => x.value.id == c.body) with
    | some e => match b.eligibility.certificates.find? (fun x => x.value.id == e.value.certificate.common.ec) with
      | some ec => PlanChecks sha b c r e.value ec.value
      | none => False
    | none => False
  | 5 => match b.parameters.bodies.find? (fun x => x.value.id == c.body) with
    | some e => match b.plans.certificates.find? (fun x => x.value.id == e.value.certificate.common.plan) with
      | some plan => ParameterChecks b c r e.value plan.value
      | none => False
    | none => False
  | 6 => match b.roots.bodies.find? (fun x => x.value.id == c.body) with
    | some e => match b.plans.certificates.find? (fun x => x.value.id == e.value.certificate.common.plan) with
      | some plan => Root sha b c r e.value plan.value
      | none => False
    | none => False
  | 7 => match b.applies.bodies.find? (fun x => x.value.id == c.body) with
    | some e => ApplyChecks sha s b c r e.value
    | none => False
  | 8 => (NativeFailureAuthority.checkView sha p (stateView s) b.tail c).isSome = true
  | 9 => (NativeFailureAuthority.checkAbort sha p (stateView s) b.tail c).isSome = true
  | _ => False
instance (sha p s b c r) : Decidable (Authority sha p s b c r) := by
  unfold Authority; split <;> first | infer_instance | (split <;> first | infer_instance | (split <;> infer_instance))

structure Entry where
  original : Candidate
  parents : Parents

def check (sha : Bytes → Bytes) (p : Policy) (s : NativeHeader.Coarse)
    (b : Bound) (c : Candidate) : Option Entry := do
  let r ← NativeCandidateShape.check p c
  if c.height = s.height ∧ c.view = s.view ∧ Authority sha p s b c r then some ⟨c,r⟩ else none

theorem checked {sha p s b c e} (ok : check sha p s b c = some e) :
    e.original = c ∧ NativeCandidateShape.check p c = some e.parents ∧
    c.height = s.height ∧ c.view = s.view ∧ Authority sha p s b c e.parents := by
  unfold check at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨r,hr,last⟩ := ok
  split at last <;> try contradiction
  rename_i valid
  cases Option.some.inj last
  exact ⟨rfl,hr,valid⟩

theorem fromComponents {sha p s b c r}
    (hr : NativeCandidateShape.check p c = some r)
    (hh : c.height = s.height) (hv : c.view = s.view) (ha : Authority sha p s b c r) :
    check sha p s b c = some ⟨c,r⟩ := by
  have valid : c.height = s.height ∧ c.view = s.view ∧ Authority sha p s b c r := ⟨hh,hv,ha⟩
  simp only [check,hr,Bind.bind,Option.bind,if_pos valid]

theorem allOriginalParents {sha p s b c e} (ok : check sha p s b c = some e) :
    c.parents = NativeCandidateShape.value e.parents := NativeCandidateShape.exactParents (checked ok).2.1

def checkAll (sha : Bytes → Bytes) (p : Policy) (s : NativeHeader.Coarse) (b : Bound) :
    List Candidate → Option (List Entry)
  | [] => some []
  | c::cs => do
    let e ← check sha p s b c
    let es ← checkAll sha p s b cs
    some (e::es)

theorem originals {sha p s b cs es} (ok : checkAll sha p s b cs = some es) :
    es.map Entry.original = cs := by
  induction cs generalizing es with
  | nil => cases Option.some.inj ok; rfl
  | cons c cs ih =>
    simp only [checkAll,Bind.bind,Option.bind_eq_some_iff] at ok
    obtain ⟨e,he,rest,hr,last⟩ := ok
    cases Option.some.inj last
    simp only [List.map_cons,(checked he).1,ih hr]

theorem everyEntry {sha p s b cs es} (ok : checkAll sha p s b cs = some es) :
    ∀ e ∈ es, check sha p s b e.original = some e := by
  induction cs generalizing es with
  | nil => cases Option.some.inj ok; simp
  | cons c cs ih =>
    simp only [checkAll,Bind.bind,Option.bind_eq_some_iff] at ok
    obtain ⟨e,he,rest,hr,last⟩ := ok
    cases Option.some.inj last
    intro out member
    rcases List.mem_cons.mp member with same | member
    · subst out; simpa only [(checked he).1] using he
    · exact ih hr out member

theorem allComplete {sha p s b es}
    (every : ∀ e ∈ es, check sha p s b e.original = some e) :
    checkAll sha p s b (es.map Entry.original) = some es := by
  induction es with
  | nil => rfl
  | cons e es ih =>
    simp only [List.map_cons,checkAll,every e (by simp),Bind.bind,Option.bind]
    rw [ih (fun x hx => every x (by simp [hx]))]

structure PolicyBinding where
  source : Policy.Bound
  collections : Bound
  entries : List Entry

def bindPolicy (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (actor configRaw stateRaw policyRaw : Bytes) (stateValue : Value)
    (raw : Collections.Originals) : Option PolicyBinding := do
  let source ← Policy.bind sha enrolled actor configRaw stateRaw policyRaw stateValue
  let b ← Collections.bind sha source.header.state source.policy raw
  let entries ← checkAll sha source.policy source.header.state b source.policy.candidates
  some ⟨source,b,entries⟩

theorem policySource {sha enrolled actor configRaw stateRaw policyRaw stateValue raw out}
    (ok : bindPolicy sha enrolled actor configRaw stateRaw policyRaw stateValue raw = some out) :
    Policy.bind sha enrolled actor configRaw stateRaw policyRaw stateValue = some out.source ∧
    Collections.bind sha out.source.header.state out.source.policy raw = some out.collections ∧
    checkAll sha out.source.policy out.source.header.state out.collections out.source.policy.candidates = some out.entries := by
  unfold bindPolicy at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨source,hs,b,hb,es,he,last⟩ := ok
  cases Option.some.inj last
  exact ⟨hs,hb,he⟩

theorem allOriginalCandidates {sha enrolled actor configRaw stateRaw policyRaw stateValue raw out}
    (ok : bindPolicy sha enrolled actor configRaw stateRaw policyRaw stateValue raw = some out) :
    out.entries.map Entry.original = out.source.policy.candidates := originals (policySource ok).2.2

end DeltaReduce.ProfileSource.Candidates
