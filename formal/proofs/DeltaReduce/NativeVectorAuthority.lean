import DeltaReduce.NativeVectorDerivation
import DeltaReduce.NativeParameterSection

/-! Executable original policy/context/membership checks on the draft vector
join. Original certificate IDs and draft artifact IDs remain different domains.
This does not authenticate those mappings, current vectors or APPLY profiles. -/
namespace DeltaReduce.NativeVectorAuthority
open NativeBinding
open NativeVectorContext (Bound)
open NativeVectorLayout (text)

def base (b : Bound) := b.source.plan.members.plans.eligibility.norms.isc
def policy (b : Bound) := (base b).policy
def state (b : Bound) := (base b).state
def plan (b : Bound) := b.source.plan.members.edge

def context (b : Bound) : Context :=
  ⟨text (policy b).round,(state b).height,(state b).view,text (policy b).epoch,
    (policy b).hardDeadline,text (state b).wire.parent⟩

def members (b : Bound) : List String :=
  (plan b).parent.certificate.body.tuples.map (fun t => text t.ticket)
def eligible (b : Bound) : List String :=
  b.source.plan.members.rows.map (fun r => text r.member.input.ticket)
def tickets (b : Bound) : List Ticket :=
  b.source.plan.members.rows.map (fun r => ⟨text r.member.input.ticket,text r.member.input.domain⟩)

theorem rawSource {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs b}
    (h : NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw
      permission inputs = some b) :
    ∃ tree, NativePolicyBytes.decodePolicy policyRaw = some (tree,policy b) ∧
      NativeStateBytes.decodeState stateRaw = some (state b) := by
  have rows := NativePlanQCorpus.boundSource (NativeVectorContext.boundSource h).1
  have coeff := NativePlanCoefficients.boundSource rows.1
  obtain ⟨tree,p,s,hp,hs,ps,_,_⟩ := NativePlanMembers.actualSourceSection coeff.members
  have es := NativeEligibilitySection.checkedSource ps.eligibility
  have ns := NativeNormSection.checkedSource es.norms
  have src := NativeFinalizedIscSection.checkedSource ns.1
  exact ⟨tree,by simpa only [policy,base,src.1] using hp,
    by simpa only [state,base,src.2.1] using hs⟩

theorem originalContext (b : Bound) :
    (context b).round = text (policy b).round ∧
    (context b).height = (state b).height ∧ (context b).view = (state b).view ∧
    (context b).epoch = text (policy b).epoch ∧
    (context b).hardDeadline = (policy b).hardDeadline ∧
    (context b).parentCheckpoint = text (state b).wire.parent := ⟨rfl,rfl,rfl,rfl,rfl,rfl⟩

theorem completeMembers (b : Bound) :
    (members b).length = (plan b).parent.certificate.body.tuples.length ∧
    (eligible b).length = b.source.plan.members.rows.length ∧
    (tickets b).length = b.source.plan.members.rows.length := by
  simp [members,eligible,tickets]

theorem ticketAt (b : Bound) {position : Nat} {r : NativePlanMembers.Row}
    (h : b.source.plan.members.rows[position]? = some r) :
    (tickets b)[position]? = some ⟨text r.member.input.ticket,text r.member.input.domain⟩ := by
  simp [tickets,List.getElem?_map,h]

def FrameChecks (authority : Authority) (b : Bound) (f : ParameterFrame) : Prop :=
  authority.context = context b ∧ f.members = members b ∧
  f.eligible = eligible b ∧ f.plan.tickets = tickets b
instance (authority b f) : Decidable (FrameChecks authority b f) := by
  unfold FrameChecks; infer_instance

def assignmentKey (a : Assignment) : NativeParameter.Key :=
  ⟨asciiBytes a.domain,asciiBytes a.shard⟩
def selectedBodies (b : Bound) (s : NativeParameterSection.Bound) :=
  s.bodies.filter (fun e => e.certificate.common.plan == (plan b).id)
def findBody (b : Bound) (s : NativeParameterSection.Bound) (a : Assignment) :=
  (selectedBodies b s).find? (fun e =>
    e.certificate.common.domain == asciiBytes a.domain &&
    e.certificate.common.shard == asciiBytes a.shard)

/-- Native shard labels must equal the configured draft labels at this boundary.
This is an explicit representability restriction, not a new native admission rule. -/
def AssignmentChecks (b : Bound) (a : Assignment) (e : NativeParameterLineage.Edge) : Prop :=
  e.voteContext = asciiBytes a.context ∧ e.voteContext ≠ [] ∧
  e.certificate.common.context = (plan b).certificate.common.context ∧
  e.certificate.common.plan = (plan b).id ∧
  e.certificate.common.isc = (plan b).parent.qcId ∧
  e.certificate.common.ec = (plan b).ec.id ∧
  (e.certificate.common.denominator : Int) = a.denominator
instance (b a e) : Decidable (AssignmentChecks b a e) := by
  unfold AssignmentChecks; infer_instance

structure Link where
  assignment : Assignment
  original : NativeParameterLineage.Edge

def link (b : Bound) (s : NativeParameterSection.Bound) (a : Assignment) : Option Link := do
  let e ← findBody b s a
  if AssignmentChecks b a e then some ⟨a,e⟩ else none

theorem linked {b s a l} (h : link b s a = some l) :
    l.assignment = a ∧ findBody b s a = some l.original ∧
    AssignmentChecks b a l.original := by
  simp only [link,bind,Option.bind_eq_some_iff] at h
  obtain ⟨e,he,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨rfl,he,by assumption⟩

theorem bodyMembership {b s a e} (h : findBody b s a = some e) :
    e ∈ s.bodies ∧ e.certificate.common.plan = (plan b).id ∧
    e.certificate.common.domain = asciiBytes a.domain ∧
    e.certificate.common.shard = asciiBytes a.shard := by
  have mem := List.mem_of_find?_eq_some h
  have selected := List.mem_filter.mp mem
  have key := List.find?_some h
  exact ⟨selected.1,by simpa using selected.2,by simpa using key⟩

def links (b : Bound) (s : NativeParameterSection.Bound) : List Assignment → Option (List Link)
  | [] => some []
  | a::as => do
    let l ← link b s a
    let rest ← links b s as
    some (l::rest)

theorem allAssignments {b s as ls} (h : links b s as = some ls) :
    ls.map Link.assignment = as := by
  induction as generalizing ls with
  | nil => simp [links] at h; subst ls; rfl
  | cons a as ih =>
    simp only [links,bind,Option.bind_eq_some_iff] at h
    obtain ⟨l,hl,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,(linked hl).1,ih hr]

theorem allLinked {b s as ls} (h : links b s as = some ls) {l} (mem : l ∈ ls) :
    link b s l.assignment = some l := by
  induction as generalizing ls with
  | nil => simp [links] at h; subst ls; simp at mem
  | cons a as ih =>
    simp only [links,bind,Option.bind_eq_some_iff] at h
    obtain ⟨x,hx,rest,hr,last⟩ := h
    cases Option.some.inj last
    rcases List.mem_cons.mp mem with rfl | mem
    · simpa only [(linked hx).1] using hx
    · exact ih hr mem

theorem linkAt {b s as ls} (h : links b s as = some ls) {n : Nat} {a : Assignment} (positioned : as[n]? = some a) :
    ∃ l, ls[n]? = some l ∧ l.assignment = a ∧ link b s a = some l := by
  induction as generalizing ls n with
  | nil => simp at positioned
  | cons x xs ih =>
    simp only [links,bind,Option.bind_eq_some_iff] at h
    obtain ⟨l,hl,rest,hr,last⟩ := h
    cases Option.some.inj last
    cases n with
    | zero => simp at positioned; subst a; exact ⟨l,rfl,(linked hl).1,hl⟩
    | succ n => simpa using ih hr (by simpa using positioned)

def Coverage (b : Bound) (f : ParameterFrame) (s : NativeParameterSection.Bound) : Prop :=
  f.plan.assignments.map assignmentKey = s.keys ∧
  (selectedBodies b s).length = f.plan.assignments.length
instance (b f s) : Decidable (Coverage b f s) := by unfold Coverage; infer_instance

def OriginalCoverage (b : Bound) (s : NativeParameterSection.Bound) (ls : List Link) : Prop :=
  (ls.map (fun l => NativeParameterLineage.asBody l.original)).Perm
    ((selectedBodies b s).map NativeParameterLineage.asBody)
instance (b s ls) : Decidable (OriginalCoverage b s ls) := by
  unfold OriginalCoverage; infer_instance

structure Checked where
  native : NativeParameterSection.Bound
  bindings : List Link

def check (sha : Bytes → Bytes) (authority : Authority) (b : Bound)
    (f : ParameterFrame) : Option Checked := do
  let native ← NativeParameterSection.bindSection sha (policy b) (state b)
  if FrameChecks authority b f ∧ Coverage b f native then
    let bindings ← links b native f.plan.assignments
    if OriginalCoverage b native bindings then some ⟨native,bindings⟩ else none
  else none

structure Source (sha : Bytes → Bytes) (authority : Authority) (b : Bound)
    (f : ParameterFrame) (out : Checked) : Prop where
  native : NativeParameterSection.bindSection sha (policy b) (state b) = some out.native
  frame : FrameChecks authority b f
  coverage : Coverage b f out.native
  assignments : links b out.native f.plan.assignments = some out.bindings
  originals : OriginalCoverage b out.native out.bindings

theorem checked {sha authority b f out} (h : check sha authority b f = some out) :
    Source sha authority b f out := by
  simp only [check,bind,Option.bind_eq_some_iff] at h
  obtain ⟨s,hs,last⟩ := h
  split at last <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨ls,hl,last⟩ := last
  split at last <;> try contradiction
  rename_i all
  cases Option.some.inj last
  exact ⟨hs,checks.1,checks.2,hl,all⟩

theorem fromSource {sha authority b f out} (h : Source sha authority b f out) :
    check sha authority b f = some out := by
  simp only [check,h.native,bind,Option.bind,if_pos (show FrameChecks authority b f ∧ Coverage b f out.native from ⟨h.frame,h.coverage⟩),h.assignments,if_pos h.originals]

theorem originalAssignment {sha authority b f out} (h : check sha authority b f = some out)
    {l} (mem : l ∈ out.bindings) :
    AssignmentChecks b l.assignment l.original ∧
    NativeParameterLineage.check sha .proposed
      (NativeParameterSection.expected (policy b) (state b) out.native.plans)
      (policy b).validators out.native.plans.eligibility.norms.isc.certificates
      out.native.plans.eligibility.norms.isc.finalized out.native.plans.eligibility.finalized
      out.native.plans.finalized out.native.keys out.native.plans.eligibility.certificates
      out.native.plans.certificates l.original.source = some l.original := by
  have src := checked h
  have row := linked (allLinked src.assignments mem)
  exact ⟨row.2.2,NativeParameterSection.proposedChecked src.native (bodyMembership row.2.1).1⟩

theorem originalPayload {sha authority b f out} (h : check sha authority b f = some out)
    {l} (mem : l ∈ out.bindings) :
    l.original.source = NativeParameter.bodyValue (NativeParameterLineage.asBody l.original) :=
  NativeParameterLineage.originalRetained (originalAssignment h mem).2

theorem exactVoteContext {sha authority b f out} (h : check sha authority b f = some out)
    {l} (mem : l ∈ out.bindings) :
    l.original.voteContext = asciiBytes l.assignment.context ∧ l.original.voteContext ≠ [] :=
  ⟨(originalAssignment h mem).1.1,(originalAssignment h mem).1.2.1⟩

theorem completeMatrix {sha authority b f out} (h : check sha authority b f = some out) :
    out.bindings.map Link.assignment = f.plan.assignments ∧
    f.plan.assignments.map assignmentKey = out.native.keys ∧
    out.bindings.length = (selectedBodies b out.native).length := by
  have src := checked h
  have all := allAssignments src.assignments
  have count := congrArg List.length all
  simp only [List.length_map] at count
  exact ⟨all,src.coverage.1,count.trans src.coverage.2.symm⟩

theorem completeOriginalBodies {sha authority b f out} (h : check sha authority b f = some out) :
    (out.bindings.map (fun l => NativeParameterLineage.asBody l.original)).Perm
      ((selectedBodies b out.native).map NativeParameterLineage.asBody) := (checked h).originals

theorem completeOriginalPayloads {sha authority b f out} (h : check sha authority b f = some out) :
    (out.bindings.map (fun l => l.original.source)).Perm
      ((selectedBodies b out.native).map (·.source)) := by
  have left : out.bindings.map (fun l => l.original.source) =
      out.bindings.map (fun l => NativeParameter.bodyValue (NativeParameterLineage.asBody l.original)) := by
    apply List.map_congr_left
    intro l mem
    exact originalPayload h mem
  have right : (selectedBodies b out.native).map (·.source) =
      (selectedBodies b out.native).map (fun e => NativeParameter.bodyValue (NativeParameterLineage.asBody e)) := by
    apply List.map_congr_left
    intro e mem
    exact NativeParameterLineage.originalRetained
      (NativeParameterSection.proposedChecked (checked h).native (List.mem_filter.mp mem).1)
  rw [left,right]
  simpa only [List.map_map,Function.comp_def] using
    (completeOriginalBodies h).map NativeParameter.bodyValue

theorem missingBodyRejected {b s a} (missing : findBody b s a = none) : link b s a = none := by
  simp [link,missing]

theorem changedVoteContextRejected {b s a e} (found : findBody b s a = some e)
    (different : e.voteContext ≠ asciiBytes a.context) : link b s a = none := by
  simp [link,found,AssignmentChecks,different]

theorem changedFrameRejected {sha authority b f}
    (different : ¬ FrameChecks authority b f) : check sha authority b f = none := by
  unfold check
  cases NativeParameterSection.bindSection sha (policy b) (state b) <;> simp [different]

theorem emptyMatrixRejected {b f s} (nonempty : f.plan.assignments ≠ []) (empty : s.keys = []) :
    ¬ Coverage b f s := by
  intro h
  have eq := h.1.trans empty
  exact nonempty (List.map_eq_nil_iff.mp eq)

def join {codec store trust anchor} (binding : Binding codec trust anchor store)
    (sha : Bytes → Bytes) (b : Bound) (domain : Bytes) (index : Nat) := do
  let j ← NativeVectorJoin.join binding b domain index
  let original ← check sha binding.authority b j.native.frame
  some (j,original)

theorem joined {codec store trust anchor binding sha b domain index j original}
    (h : @join codec store trust anchor binding sha b domain index = some (j,original)) :
    NativeVectorJoin.join binding b domain index = some j ∧
    check sha binding.authority b j.native.frame = some original := by
  simp only [join,bind,Option.bind_eq_some_iff] at h
  obtain ⟨j',hj,o,ho,last⟩ := h
  cases Option.some.inj last
  exact ⟨hj,ho⟩

theorem joinedFromInputs {codec store trust anchor binding b domain index sha original}
    (i : @NativeVectorDerivation.Inputs codec store trust anchor binding b domain index)
    (identity : check sha binding.authority b i.frame = some original) :
    ∃ j, join binding sha b domain index = some (j,original) ∧ j.native = NativeVectorDerivation.derive i := by
  obtain ⟨j,hj,hd,_⟩ := NativeVectorDerivation.actualJoin i
  refine ⟨j,?_,hd⟩
  simp only [join,hj,bind,Option.bind,hd]
  change (check sha binding.authority b i.frame >>= fun o => some (j,o)) = some (j,original)
  simp only [identity,bind,Option.bind]

def sourceLeaves (index : Nat) : List NativeVectorContext.Slice → Option (List Bytes)
  | [] => some []
  | s::ss => do
    let r ← s.source.corpus.manifest.manifest.refs[index]?
    let rest ← sourceLeaves index ss
    some (r.wire.leaf::rest)

theorem sourceLeafCount {index ss leaves} (h : sourceLeaves index ss = some leaves) :
    leaves.length = ss.length := by
  induction ss generalizing leaves with
  | nil => simp [sourceLeaves] at h; subst leaves; rfl
  | cons s ss ih =>
    simp only [sourceLeaves,bind,Option.bind_eq_some_iff] at h
    obtain ⟨r,_,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp [ih hr]

theorem sourceLeafAt {index ss leaves} (h : sourceLeaves index ss = some leaves)
    {position : Nat} {s : NativeVectorContext.Slice} (atPosition : ss[position]? = some s) :
    ∃ r, s.source.corpus.manifest.manifest.refs[index]? = some r ∧
      leaves[position]? = some r.wire.leaf := by
  induction ss generalizing leaves position with
  | nil => simp at atPosition
  | cons first ss ih =>
    simp only [sourceLeaves,bind,Option.bind_eq_some_iff] at h
    obtain ⟨r,hr,rest,hs,last⟩ := h
    cases Option.some.inj last
    cases position with
    | zero => simp at atPosition; subst s; exact ⟨r,hr,rfl⟩
    | succ n => simpa using ih hs (by simpa using atPosition)

def bodyMatches (body : NativeParameter.Common) (leaves : List Bytes) (values : List Int) : Bool :=
  body.leaves == leaves.mergeSort NativePolicyBytes.bytesLT &&
  body.numerators.map NativeCertificateDecimal.number == values

theorem matchedBody {body leaves values} (h : bodyMatches body leaves values = true) :
    body.leaves.Perm leaves ∧
    body.numerators.map NativeCertificateDecimal.number = values := by
  have eq : body.leaves = leaves.mergeSort NativePolicyBytes.bytesLT ∧
      body.numerators.map NativeCertificateDecimal.number = values := by
    simpa [bodyMatches] using h
  exact ⟨eq.1 ▸ List.mergeSort_perm leaves NativePolicyBytes.bytesLT,eq.2⟩

structure Verified {codec store trust anchor} (binding : Binding codec trust anchor store)
    (b : Bound) (domain : Bytes) (index : Nat) where
  computation : NativeVectorJoin.Joined binding b domain index
  identity : Checked
  selected : Link
  leaves : List Bytes

/-- Original bodies are candidates to check, never expected arithmetic inputs.
The full source leaf list is sorted only for the original certificate encoding;
source/draft contribution order is retained separately. -/
def verify {codec store trust anchor} (binding : Binding codec trust anchor store)
    (sha : Bytes → Bytes) (b : Bound) (domain : Bytes) (index : Nat) :
    Option (Verified binding b domain index) := do
  let (j,identity) ← join binding sha b domain index
  let selected ← identity.bindings.find? (fun l => l.assignment == j.native.assignment)
  let leaves ← sourceLeaves index j.out.slices
  if bodyMatches selected.original.certificate.common leaves j.native.numerators then
    some ⟨j,identity,selected,leaves⟩ else none

structure VerifiedSource {codec store trust anchor} (binding : Binding codec trust anchor store)
    (sha : Bytes → Bytes) (b : Bound) (domain : Bytes) (index : Nat)
    (out : Verified binding b domain index) : Prop where
  joined : join binding sha b domain index = some (out.computation,out.identity)
  selected : out.identity.bindings.find? (fun l => l.assignment == out.computation.native.assignment)
    = some out.selected
  leaves : sourceLeaves index out.computation.out.slices = some out.leaves
  matched : bodyMatches out.selected.original.certificate.common out.leaves
    out.computation.native.numerators = true

theorem verifiedSource {codec store trust anchor binding sha b domain index out}
    (h : @verify codec store trust anchor binding sha b domain index = some out) :
    VerifiedSource binding sha b domain index out := by
  simp only [verify,bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨j,identity⟩,hj,l,hl,leaves,hs,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨hj,hl,hs,by assumption⟩

theorem verifiedNumbers {codec store trust anchor binding sha b domain index out}
    (h : @verify codec store trust anchor binding sha b domain index = some out) :
    out.selected.original.certificate.common.numerators.map NativeCertificateDecimal.number =
      out.computation.out.values :=
  (matchedBody (verifiedSource h).matched).2.trans (NativeVectorJoin.numeratorsDerived out.computation)

theorem verifiedLeaves {codec store trust anchor binding sha b domain index out}
    (h : @verify codec store trust anchor binding sha b domain index = some out) :
    out.selected.original.certificate.common.leaves.Perm out.leaves ∧
    out.leaves.length = out.computation.out.slices.length :=
  ⟨(matchedBody (verifiedSource h).matched).1,sourceLeafCount (verifiedSource h).leaves⟩

theorem verifiedContext {codec store trust anchor binding sha b domain index out}
    (h : @verify codec store trust anchor binding sha b domain index = some out) :
    out.selected.original.voteContext = asciiBytes out.computation.native.body.context := by
  have src := verifiedSource h
  have checks := (joined src.joined).2
  have ctx := (exactVoteContext checks (List.mem_of_find?_eq_some src.selected)).1
  have eq : out.selected.assignment = out.computation.native.assignment := by
    simpa using List.find?_some src.selected
  simpa only [eq,DerivedParameter.body] using ctx

theorem invalidBodyRejected (body : NativeParameter.Common) (leaves : List Bytes) (values : List Int)
    (bad : body.leaves ≠ leaves.mergeSort NativePolicyBytes.bytesLT ∨
      body.numerators.map NativeCertificateDecimal.number ≠ values) :
    bodyMatches body leaves values = false := by
  rcases bad with left | right
  · simp [bodyMatches,left]
  · simp [bodyMatches,right]

def run {codec store trust anchor} (binding : Binding codec trust anchor store)
    (sha : Bytes → Bytes) (policyRaw stateRaw apcId configRaw proofRaw profileRaw : Bytes)
    (permission : NativeAvailableQ.Permission) (inputs : List NativeAvailableQ.Input)
    (domain : Bytes) (index : Nat) : Option ((b : Bound) × Verified binding b domain index) := do
  let b ← NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs
  let out ← verify binding sha b domain index
  some ⟨b,out⟩

theorem runSource {codec store trust anchor binding sha policyRaw stateRaw apcId configRaw proofRaw
    profileRaw permission inputs domain index b out}
    (h : @run codec store trust anchor binding sha policyRaw stateRaw apcId configRaw proofRaw
      profileRaw permission inputs domain index = some ⟨b,out⟩) :
    NativeVectorContext.bind sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs
      = some b ∧ verify binding sha b domain index = some out := by
  simp only [run,bind,Option.bind_eq_some_iff] at h
  obtain ⟨b',hb,out',ho,last⟩ := h
  cases Option.some.inj last
  exact ⟨hb,ho⟩

end DeltaReduce.NativeVectorAuthority
