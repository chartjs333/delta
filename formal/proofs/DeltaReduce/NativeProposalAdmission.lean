import DeltaReduce.NativeIscAdmission

/-! Computed CONFIG/ISC proposal-list admission. The original complete policy
is retained; candidate-local checking never rewrites its list or policy bytes.
Only proposed ISC bodies are supported. SHA, snapshot origin and runtime facts
remain explicit boundaries, not authenticated physical observations. -/
namespace DeltaReduce.NativeProposalAdmission
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativeConfigAdmission (ascii getText getTexts HeaderChecks ConfigIds Label RuntimeFacts)
open NativePolicyBytes (Policy Candidate)
open NativeStateBytes (State)
open NativeVoteBytes (Vote ContentId)
open NativeInputSetBody (Checked)

structure Graph where
  policy : Policy
  state : State
  schema : Bytes
  arithmetic : Bytes
  accumulator : Bytes
  proposed : List Bytes
  finalized : List Bytes
  snapshotId : Bytes
  bodyTrees : List Value
  bodies : List Checked
  closed : List Bytes

def GraphChecks (g : Graph) : Prop :=
  HeaderChecks g.policy g.state ∧ NativeIscAdmission.allowedGraph fmtSnapshot g.policy.snapshot = true ∧
  (∀ v ∈ g.policy.validators, Label v) ∧ ContentId g.schema ∧ ContentId g.arithmetic ∧
  (g.accumulator = [] ∨ ContentId g.accumulator) ∧ ConfigIds g.policy g.proposed ∧
  ConfigIds g.policy g.finalized ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (g.bodies.map Checked.id) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT g.closed = true ∧
  (∀ id ∈ g.closed, ContentId id ∧ id ∈ g.bodies.map Checked.id)
instance (g) : Decidable (GraphChecks g) := by unfold GraphChecks; infer_instance

def kind : Nat → Option Bytes
  | 1 => some (ascii "ROUND_CONFIG")
  | 2 => some (ascii "ISC")
  | _ => none
def phase : Nat → Option Bytes
  | 1 => some (ascii "TICKETING_OPEN")
  | 2 => some (ascii "AVAILABLE")
  | _ => none
def context (sha : Bytes → Bytes) (g : Graph) (action : Nat) : Option Bytes :=
  if action = 1 then NativeConfigAdmission.configContext sha g.state.height g.policy.epoch
  else if action = 2 then NativeIscAdmission.iscContext sha g.policy.round else none

structure Prepared where
  candidate : Candidate
  checkpoint : Bytes
  context : Bytes

def CandidateChecks (g : Graph) (b : Prepared) : Prop :=
  ((b.candidate.action = 1 ∧ b.candidate.body = g.policy.config ∧ b.candidate.body ∈ g.proposed) ∨
   (b.candidate.action = 2 ∧ b.candidate.body ∈ g.closed)) ∧
  b.candidate.height = g.state.height ∧ b.candidate.view = g.state.view ∧
  b.candidate.context = b.context ∧ ContentId b.checkpoint
instance (g b) : Decidable (CandidateChecks g b) := by unfold CandidateChecks; infer_instance

def checkCandidate (sha : Bytes → Bytes) (g : Graph) (c : Candidate) : Option Prepared := do
  let (config,checkpoint) ← NativeConfigAdmission.configParents c.parents
  let ctx ← context sha g c.action
  let b := Prepared.mk c checkpoint ctx
  if config = g.policy.config ∧ CandidateChecks g b then some b else none

def CandidateSource (sha : Bytes → Bytes) (g : Graph) (c : Candidate) (b : Prepared) : Prop :=
  b.candidate = c ∧
  NativeConfigAdmission.configParents c.parents = some (g.policy.config,b.checkpoint) ∧
  context sha g c.action = some b.context ∧ CandidateChecks g b

theorem candidateSource {sha g c b} (ok : checkCandidate sha g c = some b) :
    CandidateSource sha g c b := by
  unfold checkCandidate at ok
  simp only [bind,Option.bind_eq_some_iff] at ok
  obtain ⟨⟨config,checkpoint⟩,parents,ctx,context,last⟩ := ok
  dsimp only at last
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  rcases checks with ⟨rfl,checks⟩
  exact ⟨rfl,parents,context,checks⟩

theorem candidateFromComponents {sha g c b} (h : CandidateSource sha g c b) :
    checkCandidate sha g c = some b := by
  rcases h with ⟨same,parents,ctx,checks⟩
  unfold checkCandidate
  rw [parents,ctx]
  dsimp only [bind,Option.bind]
  rw [← same]
  exact if_pos ⟨rfl,checks⟩

def checkCandidates (sha : Bytes → Bytes) (g : Graph) : List Candidate → Option (List Prepared)
  | [] => some []
  | c::cs => do
    let b ← checkCandidate sha g c
    let bs ← checkCandidates sha g cs
    some (b::bs)

theorem allOriginalCandidates {sha g cs bs} (ok : checkCandidates sha g cs = some bs) :
    bs.map Prepared.candidate = cs := by
  induction cs generalizing bs with
  | nil => simpa [checkCandidates] using ok.symm
  | cons c cs ih =>
    simp only [checkCandidates,bind,Option.bind_eq_some_iff] at ok
    obtain ⟨b,hb,rest,hr,last⟩ := ok
    cases Option.some.inj last
    simp only [List.map_cons,(candidateSource hb).1,ih hr]

theorem allCandidateChecks {sha g cs bs} (ok : checkCandidates sha g cs = some bs) :
    ∀ b ∈ bs, CandidateSource sha g b.candidate b := by
  induction cs generalizing bs with
  | nil => simp [checkCandidates] at ok; subst bs; simp
  | cons c cs ih =>
    simp only [checkCandidates,bind,Option.bind_eq_some_iff] at ok
    obtain ⟨b,hb,rest,hr,last⟩ := ok
    cases Option.some.inj last
    intro x mem
    rcases List.mem_cons.mp mem with rfl | mem
    · have h := candidateSource hb
      simpa only [h.1] using h
    · exact ih hr x mem

theorem candidateCount {sha g cs bs} (ok : checkCandidates sha g cs = some bs) :
    bs.length = cs.length := by
  have h := congrArg List.length (allOriginalCandidates ok)
  simpa only [List.length_map] using h

structure Bound where
  graph : Graph
  candidates : List Prepared

def bindGraph (sha : Bytes → Bytes) (p : Policy) (s : State) : Option Graph := do
  let id ← getText fmtSnapshot p.snapshot "state_id"
  let computed ← NativeStateBytes.contentId sha NativeStateBytes.stateDomain
    (NativeStateBytes.encodeState s.wire)
  let schema ← getText fmtSnapshot p.snapshot "parameter_schema_id"
  let arithmetic ← getText fmtSnapshot p.snapshot "arithmetic_profile_id"
  let accumulator ← getText fmtSnapshot p.snapshot "required_accumulator_proof_id"
  let proposed ← getTexts fmtSnapshot p.snapshot "proposed_round_config_ids"
  let finalized ← getTexts fmtSnapshot p.snapshot "finalized_round_config_ids"
  let closed ← getTexts fmtSnapshot p.snapshot "closed_input_set_ids"
  let trees ← lookup fmtSnapshot p.snapshot "input_set_bodies" >>= NativePolicyBytes.items
  let bodies ← NativeInputSetBody.checkAll sha (NativeIscAdmission.expected p s schema arithmetic) trees
  let g := Graph.mk p s schema arithmetic accumulator proposed finalized id trees bodies closed
  if id = computed ∧ ContentId id ∧ GraphChecks g then some g else none

def GraphSource (sha : Bytes → Bytes) (p : Policy) (s : State) (g : Graph) : Prop :=
  g.policy = p ∧ g.state = s ∧
  getText fmtSnapshot p.snapshot "state_id" = some g.snapshotId ∧
  NativeStateBytes.contentId sha NativeStateBytes.stateDomain
    (NativeStateBytes.encodeState s.wire) = some g.snapshotId ∧ ContentId g.snapshotId ∧
  getText fmtSnapshot p.snapshot "parameter_schema_id" = some g.schema ∧
  getText fmtSnapshot p.snapshot "arithmetic_profile_id" = some g.arithmetic ∧
  getText fmtSnapshot p.snapshot "required_accumulator_proof_id" = some g.accumulator ∧
  getTexts fmtSnapshot p.snapshot "proposed_round_config_ids" = some g.proposed ∧
  getTexts fmtSnapshot p.snapshot "finalized_round_config_ids" = some g.finalized ∧
  getTexts fmtSnapshot p.snapshot "closed_input_set_ids" = some g.closed ∧
  (lookup fmtSnapshot p.snapshot "input_set_bodies" >>= NativePolicyBytes.items) = some g.bodyTrees ∧
  NativeInputSetBody.checkAll sha (NativeIscAdmission.expected p s g.schema g.arithmetic)
    g.bodyTrees = some g.bodies ∧ GraphChecks g

theorem graphSource {sha p s g} (ok : bindGraph sha p s = some g) : GraphSource sha p s g := by
  unfold bindGraph at ok
  simp only [bind,Option.bind_eq_some_iff] at ok
  obtain ⟨id,hi,computed,hh,schema,hs,arithmetic,ha,accumulator,hu,
    proposed,hp,finalized,hf,closed,hl,trees,ht,bodies,hb,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  rcases checks with ⟨rfl,valid,checks⟩
  exact ⟨rfl,rfl,hi,hh,valid,hs,ha,hu,hp,hf,hl,
    by simpa only [bind,Option.bind_eq_some_iff] using ht,hb,checks⟩

def bind (sha : Bytes → Bytes) (p : Policy) (s : State) : Option Bound := do
  let g ← bindGraph sha p s
  let candidates ← checkCandidates sha g p.candidates
  some ⟨g,candidates⟩

theorem graphFromComponents {sha p s g} (h : GraphSource sha p s g) :
    bindGraph sha p s = some g := by
  rcases h with ⟨rfl,rfl,id,hash,valid,schema,arithmetic,accumulator,
    proposed,finalized,closed,trees,bodies,checks⟩
  unfold bindGraph
  rw [id,hash,schema,arithmetic,accumulator,proposed,finalized,closed,trees]
  dsimp only [Bind.bind,Option.bind]
  rw [bodies]
  dsimp only [Bind.bind,Option.bind]
  exact if_pos ⟨rfl,valid,checks⟩

theorem bindFromComponents {sha p s b} (graph : GraphSource sha p s b.graph)
    (candidates : checkCandidates sha b.graph p.candidates = some b.candidates) :
    bind sha p s = some b := by
  simp only [bind,graphFromComponents graph,candidates,Bind.bind,Option.bind]

theorem bindSource {sha p s b} (ok : bind sha p s = some b) :
    GraphSource sha p s b.graph ∧ checkCandidates sha b.graph p.candidates = some b.candidates := by
  unfold bind at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨g,hg,cs,hc,last⟩ := ok
  cases Option.some.inj last
  exact ⟨graphSource hg,hc⟩

def prepare (sha : Bytes → Bytes) (policyRaw stateRaw : Bytes) : Option Bound := do
  let (_,p) ← NativePolicyBytes.decodePolicy policyRaw
  let s ← NativeStateBytes.decodeState stateRaw
  bind sha p s

theorem prepareFromComponents {sha policyRaw stateRaw tree p s b}
    (policy : NativePolicyBytes.decodePolicy policyRaw = some (tree,p))
    (state : NativeStateBytes.decodeState stateRaw = some s)
    (bound : bind sha p s = some b) : prepare sha policyRaw stateRaw = some b := by
  simp only [prepare,policy,state,Bind.bind,Option.bind]
  exact bound

theorem prepareSource {sha policyRaw stateRaw b} (ok : prepare sha policyRaw stateRaw = some b) :
    ∃ tree, NativePolicyBytes.decodePolicy policyRaw = some (tree,b.graph.policy) ∧
      NativeStateBytes.decodeState stateRaw = some b.graph.state ∧
      GraphSource sha b.graph.policy b.graph.state b.graph ∧
      checkCandidates sha b.graph b.graph.policy.candidates = some b.candidates := by
  unfold prepare at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨⟨tree,p⟩,hp,s,hs,last⟩ := ok
  have h := bindSource last
  rcases h.1 with ⟨samePolicy,sameState,rest⟩
  change b.graph.policy = p at samePolicy
  subst p; subst s
  exact ⟨tree,hp,hs,⟨rfl,rfl,rest⟩,h.2⟩

def VoteChecks (g : Graph) (b : Prepared) (r : RuntimeFacts) (v : Vote) : Prop :=
  NativeVoteBytes.VoteValid v ∧ kind b.candidate.action = some v.wire.kind ∧
  v.wire.validator = g.policy.localValidator ∧ v.wire.epoch = g.policy.epoch ∧
  v.wire.round = g.state.wire.round ∧ v.height = g.state.height ∧ v.view = g.state.view ∧
  v.wire.context = b.candidate.context ∧ v.wire.bodyHash = b.candidate.body ∧
  b.checkpoint = g.state.wire.parent ∧ v.sequence = r.expectedSequence ∧
  (r.recovery = true ∨ r.ready = true) ∧ r.invalidated = false ∧
  phase b.candidate.action = some g.state.wire.phase ∧ r.tick < g.policy.hardDeadline ∧
  r.tick < 256^8 ∧ r.expectedSequence < 256^8
instance (g b r v) : Decidable (VoteChecks g b r v) := by unfold VoteChecks; infer_instance

def select (b : Bound) (r : RuntimeFacts) (v : Vote) : Option Prepared :=
  b.candidates.find? (fun c => decide (VoteChecks b.graph c r v))

theorem selectSource {b r v c} (ok : select b r v = some c) :
    c ∈ b.candidates ∧ VoteChecks b.graph c r v := by
  have checked : decide (VoteChecks b.graph c r v) = true :=
    List.find?_some (p := fun x => decide (VoteChecks b.graph x r v)) ok
  exact ⟨List.mem_of_find?_eq_some ok,of_decide_eq_true checked⟩

def fromBytes (sha : Bytes → Bytes) (policyRaw stateRaw voteRaw : Bytes) (r : RuntimeFacts) :
    Option (Bound × Prepared × Vote) := do
  let b ← prepare sha policyRaw stateRaw
  let v ← NativeVoteBytes.decodeFrame voteRaw
  let c ← select b r v
  some (b,c,v)

theorem fromBytesSource {sha policyRaw stateRaw voteRaw r b c v}
    (ok : fromBytes sha policyRaw stateRaw voteRaw r = some (b,c,v)) :
    prepare sha policyRaw stateRaw = some b ∧ NativeVoteBytes.decodeFrame voteRaw = some v ∧
    c ∈ b.candidates ∧ VoteChecks b.graph c r v := by
  unfold fromBytes at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨bb,hb,vv,hv,cc,hc,last⟩ := ok
  cases Option.some.inj last
  exact ⟨hb,hv,selectSource hc⟩

theorem originalPolicyList {sha policyRaw stateRaw b} (ok : prepare sha policyRaw stateRaw = some b) :
    b.candidates.map Prepared.candidate = b.graph.policy.candidates := by
  obtain ⟨_,_,_,_,cs⟩ := prepareSource ok
  exact allOriginalCandidates cs

theorem originalVoteBytes {sha policyRaw stateRaw voteRaw r b c v}
    (ok : fromBytes sha policyRaw stateRaw voteRaw r = some (b,c,v)) :
    NativeVoteBytes.encodeFrame v.wire = voteRaw :=
  (NativeVoteBytes.decodedVoteSound (fromBytesSource ok).2.1).2

theorem selectedOriginalCandidate {sha policyRaw stateRaw voteRaw r b c v}
    (ok : fromBytes sha policyRaw stateRaw voteRaw r = some (b,c,v)) :
    c.candidate ∈ b.graph.policy.candidates ∧ CandidateSource sha b.graph c.candidate c := by
  have h := fromBytesSource ok
  obtain ⟨_,_,_,_,cs⟩ := prepareSource h.1
  exact ⟨(allOriginalCandidates cs) ▸ List.mem_map_of_mem h.2.2.1,allCandidateChecks cs c h.2.2.1⟩

theorem selectedIscBody {sha policyRaw stateRaw voteRaw r b c v}
    (ok : fromBytes sha policyRaw stateRaw voteRaw r = some (b,c,v))
    (isc : c.candidate.action = 2) :
    ∃ body ∈ b.graph.bodies, body.id = v.wire.bodyHash ∧
      NativeInputSetBody.CheckedSource sha
        (NativeIscAdmission.expected b.graph.policy b.graph.state b.graph.schema b.graph.arithmetic)
        body.source body := by
  have h := fromBytesSource ok
  have candidate := (selectedOriginalCandidate ok).2
  obtain ⟨_,_,_,graph,_⟩ := prepareSource h.1
  rcases graph with ⟨_,_,_,_,_,_,_,_,_,_,_,_,bodies,checks⟩
  have closed : c.candidate.body ∈ b.graph.closed := by
    rcases candidate.2.2.2.1 with config | admitted
    · omega
    · exact admitted.2
  rcases checks with ⟨_,_,_,_,_,_,_,_,_,_,members⟩
  obtain ⟨body,mem,id⟩ := List.mem_map.mp (members _ closed).2
  have voteBody := h.2.2.2.2.2.2.2.2.2.2.2.1
  exact ⟨body,mem,id.trans voteBody.symm,NativeInputSetBody.allChecked bodies body mem⟩

end DeltaReduce.NativeProposalAdmission
