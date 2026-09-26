import DeltaReduce.NativeCandidateShape
import DeltaReduce.NativeFailureAuthority

/-! All original candidate authorities on one computed shared native snapshot.
This executes source parent/body/context checks, not live vote enabling,
arithmetic input validation, authenticated export or journal recovery. -/
namespace DeltaReduce.NativeCandidateAuthority
open NativeReceiptBytes NativePolicyCodec
open NativePolicyBytes (Policy Candidate)
open NativeStateBytes (State)
open NativeCandidateShape (Parents)
open NativeSnapshotBase (Bound)
open NativeVoteBytes (ContentId ascii)

def applySection (b : Bound) := b.prior.prior
def rootSection (b : Bound) := (applySection b).roots
def parameterSection (b : Bound) := (rootSection b).parameters.prior
def planSection (b : Bound) := (parameterSection b).plans
def ecSection (b : Bound) := (planSection b).eligibility

def parentContext (sha : Bytes → Bytes) (domain : String) (parent : Bytes) : Option Bytes :=
  if ContentId parent then
    NativeStateBytes.contentId sha (ascii domain) (NativeInputSetBody.text64 parent)
  else none

def Config (sha : Bytes → Bytes) (p : Policy) (s : State) (b : Bound) (c : Candidate) : Prop :=
  c.body ∈ b.base.proposedConfigs ∧
  NativeConfigAdmission.configContext sha s.height p.epoch = some c.context
instance (sha p s b c) : Decidable (Config sha p s b c) := by unfold Config; infer_instance

def Isc (sha : Bytes → Bytes) (p : Policy) (b : Bound) (c : Candidate) : Prop :=
  c.body ∈ b.base.closed ∧
  (b.base.inputs.find? (fun e => e.body.id == c.body)).isSome = true ∧
  NativeIscAdmission.iscContext sha p.round = some c.context
instance (sha p b c) : Decidable (Isc sha p b c) := by unfold Isc; infer_instance

def Ec (sha : Bytes → Bytes) (b : Bound) (c : Candidate) (r : Parents)
    (e : NativeEligibilityLineage.Edge) : Prop :=
  e.certificate.common.isc ∈ (ecSection b).norms.isc.finalized ∧
  r.isc = e.certificate.common.isc ∧ r.seed = e.seedId ∧ r.norm = e.certificate.common.norm ∧
  parentContext sha "deltareduce.vote-context.ec.v1" e.certificate.common.isc = some c.context
instance (sha b c r e) : Decidable (Ec sha b c r e) := by unfold Ec; infer_instance

def Plan (sha : Bytes → Bytes) (b : Bound) (c : Candidate) (r : Parents)
    (e : NativePlanLineage.Edge) (ec : NativeEligibilityLineage.Edge) : Prop :=
  e.certificate.common.isc ∈ (ecSection b).norms.isc.finalized ∧
  e.certificate.common.ec ∈ (ecSection b).finalized ∧
  r.isc = e.certificate.common.isc ∧ r.seed = e.certificate.common.seed ∧
  r.ec = e.certificate.common.ec ∧ r.norm = ec.certificate.common.norm ∧
  parentContext sha "deltareduce.vote-context.apc.v1" e.certificate.common.ec = some c.context
instance (sha b c r e ec) : Decidable (Plan sha b c r e ec) := by unfold Plan; infer_instance

def Parameter (b : Bound) (c : Candidate) (r : Parents)
    (e : NativeParameterLineage.Edge) (plan : NativePlanLineage.Edge) : Prop :=
  e.voteContext = c.context ∧ e.voteContext ≠ [] ∧
  e.certificate.common.plan ∈ (planSection b).finalized ∧
  r.isc = e.certificate.common.isc ∧ r.ec = e.certificate.common.ec ∧
  r.plan = e.certificate.common.plan ∧ r.domain = e.certificate.common.domain ∧
  r.shard = e.certificate.common.shard ∧ r.seed = plan.certificate.common.seed
instance (b c r e plan) : Decidable (Parameter b c r e plan) := by unfold Parameter; infer_instance

def Root (sha : Bytes → Bytes) (b : Bound) (c : Candidate) (r : Parents)
    (e : NativeAggregateLineage.Edge) (plan : NativePlanLineage.Edge) : Prop :=
  e.certificate.common.plan ∈ (planSection b).finalized ∧
  r.isc = e.certificate.common.isc ∧ r.ec = e.certificate.common.ec ∧
  r.plan = e.certificate.common.plan ∧ r.matrix = e.certificate.common.merkle ∧
  r.seed = plan.certificate.common.seed ∧
  parentContext sha "deltareduce.vote-context.root.v1" e.certificate.common.plan = some c.context
instance (sha b c r e plan) : Decidable (Root sha b c r e plan) := by unfold Root; infer_instance

def Apply (sha : Bytes → Bytes) (s : State) (b : Bound) (c : Candidate) (r : Parents)
    (e : NativeApplyLineage.Edge) : Prop :=
  e.decoded.candidate.root ∈ (rootSection b).finalized ∧
  r.root = e.decoded.candidate.root ∧ r.profile = e.decoded.candidate.profile ∧
  r.apply = e.decoded.candidateId ∧ e.decoded.candidate.parent = s.wire.parent ∧
  parentContext sha "deltareduce.vote-context.apply.v1" e.decoded.candidate.root = some c.context
instance (sha s b c r e) : Decidable (Apply sha s b c r e) := by unfold Apply; infer_instance

def Authority (sha : Bytes → Bytes) (p : Policy) (s : State) (b : Bound)
    (c : Candidate) (r : Parents) : Prop :=
  match c.action with
  | 1 => Config sha p s b c
  | 2 => Isc sha p b c
  | 3 => match (ecSection b).bodies.find? (fun e => e.id == c.body) with
    | some e => Ec sha b c r e
    | none => False
  | 4 => match (planSection b).bodies.find? (fun e => e.id == c.body) with
    | some e => match (ecSection b).certificates.find? (fun ec => ec.id == e.certificate.common.ec) with
      | some ec => Plan sha b c r e ec
      | none => False
    | none => False
  | 5 => match (parameterSection b).bodies.find? (fun e => e.id == c.body) with
    | some e => match (planSection b).certificates.find? (fun plan => plan.id == e.certificate.common.plan) with
      | some plan => Parameter b c r e plan
      | none => False
    | none => False
  | 6 => match (rootSection b).bodies.find? (fun e => e.id == c.body) with
    | some e => match (planSection b).certificates.find? (fun plan => plan.id == e.certificate.common.plan) with
      | some plan => Root sha b c r e plan
      | none => False
    | none => False
  | 7 => match (applySection b).bodies.find? (fun e => e.id == c.body) with
    | some e => Apply sha s b c r e
    | none => False
  | 8 => (NativeFailureAuthority.checkView sha p s b.prior.tail c).isSome = true
  | 9 => (NativeFailureAuthority.checkAbort sha p s b.prior.tail c).isSome = true
  | _ => False
instance (sha p s b c r) : Decidable (Authority sha p s b c r) := by
  unfold Authority; split <;> first | infer_instance | (split <;> first | infer_instance | (split <;> infer_instance))

structure Entry where
  original : Candidate
  parents : Parents

def check (sha : Bytes → Bytes) (p : Policy) (s : State) (b : Bound) (c : Candidate) :
    Option Entry := do
  let r ← NativeCandidateShape.check p c
  if c.height = s.height ∧ c.view = s.view ∧ Authority sha p s b c r then some ⟨c,r⟩ else none

theorem checked {sha p s b c e} (h : check sha p s b c = some e) :
    e.original = c ∧ NativeCandidateShape.check p c = some e.parents ∧
    c.height = s.height ∧ c.view = s.view ∧ Authority sha p s b c e.parents := by
  unfold check at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨r,hr,last⟩ := h
  split at last <;> try contradiction
  rename_i valid
  cases Option.some.inj last
  exact ⟨rfl,hr,valid⟩

theorem fromComponents {sha p s b c r}
    (hr : NativeCandidateShape.check p c = some r)
    (hh : c.height = s.height) (hv : c.view = s.view) (ha : Authority sha p s b c r) :
    check sha p s b c = some ⟨c,r⟩ := by
  have valid : c.height = s.height ∧ c.view = s.view ∧ Authority sha p s b c r := ⟨hh,hv,ha⟩
  simp only [check,hr,bind,Option.bind,if_pos valid]

theorem allOriginalParents {sha p s b c e} (h : check sha p s b c = some e) :
    c.parents = NativeCandidateShape.value e.parents :=
  NativeCandidateShape.exactParents (checked h).2.1

theorem rejectAuthority {sha p s b c} (h : ∀ r, ¬ Authority sha p s b c r) :
    check sha p s b c = none := by
  unfold check
  cases hr : NativeCandidateShape.check p c with
  | none => rfl
  | some r => simp only [bind,Option.bind]; split <;> first | rfl | exact False.elim (h r ‹_ ∧ _ ∧ _›.2.2)

def checkAll (sha : Bytes → Bytes) (p : Policy) (s : State) (b : Bound) :
    List Candidate → Option (List Entry)
  | [] => some []
  | c::cs => do let e ← check sha p s b c; let es ← checkAll sha p s b cs; some (e::es)

theorem originals {sha p s b cs es} (h : checkAll sha p s b cs = some es) :
    es.map Entry.original = cs := by
  induction cs generalizing es with
  | nil => cases Option.some.inj h; rfl
  | cons c cs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨e,he,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,(checked he).1,ih hr]

theorem everyEntry {sha p s b cs es} (h : checkAll sha p s b cs = some es) :
    ∀ e ∈ es, check sha p s b e.original = some e := by
  induction cs generalizing es with
  | nil => cases Option.some.inj h; simp
  | cons c cs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨e,he,rest,hr,last⟩ := h
    cases Option.some.inj last
    intro out mem
    rcases List.mem_cons.mp mem with eq | hm
    · subst out; simpa only [(checked he).1] using he
    · exact ih hr out hm

theorem exactCount {sha p s b cs es} (h : checkAll sha p s b cs = some es) :
    es.length = cs.length := by simpa using congrArg List.length (originals h)
theorem exactPosition {sha p s b cs es} (h : checkAll sha p s b cs = some es) (i : Nat) :
    (es.map Entry.original)[i]? = cs[i]? := by rw [originals h]

structure CheckedPolicy where
  snapshot : Bound
  entries : List Entry

def bindPolicy (sha : Bytes → Bytes) (p : Policy) (s : State) : Option CheckedPolicy := do
  let b ← NativeSnapshotBase.bindSnapshot sha p s
  let entries ← checkAll sha p s b p.candidates
  some ⟨b,entries⟩

theorem policySource {sha p s out} (h : bindPolicy sha p s = some out) :
    NativeSnapshotBase.bindSnapshot sha p s = some out.snapshot ∧
    checkAll sha p s out.snapshot p.candidates = some out.entries := by
  unfold bindPolicy at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨b,hb,es,he,last⟩ := h
  cases Option.some.inj last
  exact ⟨hb,he⟩

theorem policyFromComponents {sha p s out}
    (hb : NativeSnapshotBase.bindSnapshot sha p s = some out.snapshot)
    (he : checkAll sha p s out.snapshot p.candidates = some out.entries) :
    bindPolicy sha p s = some out := by simp only [bindPolicy,hb,he,bind,Option.bind]

theorem completeCandidateList {sha p s out} (h : bindPolicy sha p s = some out) :
    out.entries.map Entry.original = p.candidates := originals (policySource h).2
theorem everyCandidate {sha p s out} (h : bindPolicy sha p s = some out) :
    ∀ e ∈ out.entries, check sha p s out.snapshot e.original = some e :=
  everyEntry (policySource h).2
theorem originalSharedSnapshot {sha p s out} (h : bindPolicy sha p s = some out) :
    NativeFailureSection.bindSection sha p s = some out.snapshot.prior ∧
    NativeSnapshotBase.BaseSource sha p s out.snapshot.base := by
  have src := NativeSnapshotBase.checkedSnapshot (policySource h).1
  exact ⟨src.1,NativeSnapshotBase.checkedBase src.2⟩

def prepare (sha : Bytes → Bytes) (policyRaw stateRaw : Bytes) : Option CheckedPolicy := do
  let (_,p) ← NativePolicyBytes.decodePolicy policyRaw
  let s ← NativeStateBytes.decodeState stateRaw
  bindPolicy sha p s

theorem preparedSource {sha policyRaw stateRaw out} (h : prepare sha policyRaw stateRaw = some out) :
    ∃ tree p s, NativePolicyBytes.decodePolicy policyRaw = some (tree,p) ∧
      NativeStateBytes.decodeState stateRaw = some s ∧ NativePolicyBytes.Canonical p ∧
      NativeSnapshotBase.bindSnapshot sha p s = some out.snapshot ∧
      out.entries.map Entry.original = p.candidates ∧
      ∀ e ∈ out.entries, check sha p s out.snapshot e.original = some e := by
  unfold prepare at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨tree,p⟩,hp,s,hs,hb⟩ := h
  exact ⟨tree,p,s,hp,hs,NativePolicyBytes.acceptedCanonical hp,
    (policySource hb).1,completeCandidateList hb,everyCandidate hb⟩


theorem configWitness {sha p s b c out} (h : check sha p s b c = some out) (ha : c.action = 1) :
    Config sha p s b c := by simpa only [Authority,ha] using (checked h).2.2.2.2
theorem iscWitness {sha p s b c out} (h : check sha p s b c = some out) (ha : c.action = 2) :
    Isc sha p b c := by simpa only [Authority,ha] using (checked h).2.2.2.2

theorem ecWitness {sha p s b c out} (h : check sha p s b c = some out) (ha : c.action = 3) :
    ∃ e, (ecSection b).bodies.find? (fun e => e.id == c.body) = some e ∧
      Ec sha b c out.parents e := by
  have valid := (checked h).2.2.2.2
  simp only [Authority,ha] at valid
  cases he : (ecSection b).bodies.find? (fun e => e.id == c.body) with
  | none => simp only [he] at valid
  | some e => exact ⟨e,rfl,by simpa only [he] using valid⟩

theorem applyWitness {sha p s b c out} (h : check sha p s b c = some out) (ha : c.action = 7) :
    ∃ e, (applySection b).bodies.find? (fun e => e.id == c.body) = some e ∧
      Apply sha s b c out.parents e := by
  have valid := (checked h).2.2.2.2
  simp only [Authority,ha] at valid
  cases he : (applySection b).bodies.find? (fun e => e.id == c.body) with
  | none => simp only [he] at valid
  | some e => exact ⟨e,rfl,by simpa only [he] using valid⟩

theorem planWitness {sha p s b c out} (h : check sha p s b c = some out) (ha : c.action = 4) :
    ∃ e parent, (planSection b).bodies.find? (fun e => e.id == c.body) = some e ∧
      (ecSection b).certificates.find? (fun parent => parent.id == e.certificate.common.ec) = some parent ∧
      Plan sha b c out.parents e parent := by
  have valid := (checked h).2.2.2.2
  simp only [Authority,ha] at valid
  cases he : (planSection b).bodies.find? (fun e => e.id == c.body) with
  | none => simp only [he] at valid
  | some e =>
    simp only [he] at valid
    cases hp : (ecSection b).certificates.find? (fun parent => parent.id == e.certificate.common.ec) with
    | none => simp only [hp] at valid
    | some parent => exact ⟨e,parent,rfl,hp,by simpa only [hp] using valid⟩

theorem parameterWitness {sha p s b c out} (h : check sha p s b c = some out) (ha : c.action = 5) :
    ∃ e parent, (parameterSection b).bodies.find? (fun e => e.id == c.body) = some e ∧
      (planSection b).certificates.find? (fun parent => parent.id == e.certificate.common.plan) = some parent ∧
      Parameter b c out.parents e parent := by
  have valid := (checked h).2.2.2.2
  simp only [Authority,ha] at valid
  cases he : (parameterSection b).bodies.find? (fun e => e.id == c.body) with
  | none => simp only [he] at valid
  | some e =>
    simp only [he] at valid
    cases hp : (planSection b).certificates.find? (fun parent => parent.id == e.certificate.common.plan) with
    | none => simp only [hp] at valid
    | some parent => exact ⟨e,parent,rfl,hp,by simpa only [hp] using valid⟩

theorem rootWitness {sha p s b c out} (h : check sha p s b c = some out) (ha : c.action = 6) :
    ∃ e parent, (rootSection b).bodies.find? (fun e => e.id == c.body) = some e ∧
      (planSection b).certificates.find? (fun parent => parent.id == e.certificate.common.plan) = some parent ∧
      Root sha b c out.parents e parent := by
  have valid := (checked h).2.2.2.2
  simp only [Authority,ha] at valid
  cases he : (rootSection b).bodies.find? (fun e => e.id == c.body) with
  | none => simp only [he] at valid
  | some e =>
    simp only [he] at valid
    cases hp : (planSection b).certificates.find? (fun parent => parent.id == e.certificate.common.plan) with
    | none => simp only [hp] at valid
    | some parent => exact ⟨e,parent,rfl,hp,by simpa only [hp] using valid⟩

theorem viewWitness {sha p s b c out} (h : check sha p s b c = some out) (ha : c.action = 8) :
    (NativeFailureAuthority.checkView sha p s b.prior.tail c).isSome = true := by
  simpa only [Authority,ha] using (checked h).2.2.2.2
theorem abortWitness {sha p s b c out} (h : check sha p s b c = some out) (ha : c.action = 9) :
    (NativeFailureAuthority.checkAbort sha p s b.prior.tail c).isSome = true := by
  simpa only [Authority,ha] using (checked h).2.2.2.2

theorem sourceSections {sha p s b} (h : NativeSnapshotBase.bindSnapshot sha p s = some b) :
    NativeApplySection.bindSection sha p s = some (applySection b) ∧
    NativeAggregateSection.bindSection sha p s = some (rootSection b) ∧
    NativeParameterSection.bindSection sha p s = some (parameterSection b) ∧
    NativePlanSection.bindSection sha p s = some (planSection b) ∧
    NativeEligibilitySection.bindSection sha p s = some (ecSection b) := by
  have hf := (NativeSnapshotBase.checkedSnapshot h).1
  have ha := (NativeFailureSection.checkedSource hf).1
  have hr := (NativeApplySection.checkedSource ha).roots
  have hp := (NativeSizedParameterSection.checkedSource (NativeAggregateSection.checkedSource hr).parameters).1
  have hl := (NativeParameterSection.checkedSource hp).plans
  have he := (NativePlanSection.checkedSource hl).eligibility
  exact ⟨ha,hr,hp,hl,he⟩


theorem iscOriginalBody {sha p s out e} (h : bindPolicy sha p s = some out)
    (mem : e ∈ out.entries) (act : e.original.action = 2) :
    ∃ body ∈ out.snapshot.base.inputs, body.body.id = e.original.body ∧
      NativeProposedIsc.Source sha
        (NativeIscAdmission.expected p s out.snapshot.base.schema out.snapshot.base.arithmetic)
        p.validators body.body.source body := by
  have base := (NativeSnapshotBase.checkedSnapshot (policySource h).1).2
  exact NativeSnapshotBase.closedHasOriginalBody base (iscWitness (everyCandidate h e mem) act).1

theorem ecOriginalBody {sha p s out e} (h : bindPolicy sha p s = some out)
    (mem : e ∈ out.entries) (act : e.original.action = 3) :
    ∃ row, (ecSection out.snapshot).bodies.find? (fun r => r.id == e.original.body) = some row ∧
      NativeEligibilityLineage.check sha .proposed
        (NativeEligibilitySection.expected p s (ecSection out.snapshot).norms) p.validators
        (ecSection out.snapshot).norms.isc.certificates (ecSection out.snapshot).norms.isc.finalized
        (ecSection out.snapshot).norms.norms (ecSection out.snapshot).seeds row.source = some row ∧
      Ec sha out.snapshot e.original e.parents row := by
  obtain ⟨row,hr,hc⟩ := ecWitness (everyCandidate h e mem) act
  exact ⟨row,hr,NativeEligibilitySection.proposedChecked
    (sourceSections (policySource h).1).2.2.2.2 (List.mem_of_find?_eq_some hr),hc⟩

theorem failureTailOriginal {sha p s out} (h : bindPolicy sha p s = some out) :
    NativeFailureSection.checkTail sha p s = some out.snapshot.prior.tail :=
  (NativeFailureSection.checkedSource (originalSharedSnapshot h).1).2

theorem emptyListCannotQualify {sha p s out} (h : bindPolicy sha p s = some out) :
    out.entries ≠ [] := by
  have canonical := (NativeSnapshotBase.checkedBase
    (NativeSnapshotBase.checkedSnapshot (policySource h).1).2).valid.1.1
  intro empty
  have original := completeCandidateList h
  rw [empty] at original
  -- A decoded/header-checked policy always contains at least one candidate.
  have hc : p.candidates = [] := original.symm
  unfold NativePolicyBytes.Canonical at canonical
  simp only [hc,List.length_nil] at canonical
  omega

end DeltaReduce.NativeCandidateAuthority
