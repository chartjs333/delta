import DeltaReduce.NativeInputSetBody

/-! Computed ISC proposal admission: arbitrary ordered proposed ISC bodies, one
ISC candidate, no finalized ISC or later certificate graph. Root/closed-list
producer trust and actual availability remain outside this native subdomain. -/
namespace DeltaReduce.NativeIscAdmission
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativeConfigAdmission (ascii getText getTexts HeaderChecks ConfigIds Label)
open NativePolicyBytes (Policy Candidate)
open NativeStateBytes (State)
open NativeVoteBytes (Vote ContentId)
open NativeInputSetBody (Checked)

def allowedGraph : Format → Value → Bool
  | .end, .end => true
  | .field name _ rest, .pair value tail =>
    (name ∈ ["state_id","parameter_schema_id","arithmetic_profile_id",
      "required_accumulator_proof_id","proposed_round_config_ids","finalized_round_config_ids",
      "closed_input_set_ids","input_set_bodies"] || NativeConfigAdmission.isEmpty value) &&
    allowedGraph rest tail
  | _, _ => false

def expected (p : Policy) (s : State) (schema arithmetic : Bytes) : NativeInputSetBody.Context :=
  ⟨arithmetic,s.height,schema,p.config,p.round,p.epoch,s.view⟩
def iscPreimage (round : Bytes) : Bytes :=
  ascii "deltareduce.vote-context.isc.v1" ++ [0] ++ NativeInputSetBody.text64 round
def iscContext (sha : Bytes → Bytes) (round : Bytes) : Option Bytes :=
  let hash := sha (iscPreimage round)
  if hash.length = 32 then some (ascii "sha256:" ++ NativeVoteBytes.hexBytes hash) else none

structure Bound where
  policy : Policy
  state : State
  candidate : Candidate
  checkpoint : Bytes
  schema : Bytes
  arithmetic : Bytes
  accumulator : Bytes
  proposed : List Bytes
  finalized : List Bytes
  snapshotId : Bytes
  context : Bytes
  bodyTrees : List Value
  bodies : List Checked
  closed : List Bytes

def Checks (b : Bound) : Prop :=
  HeaderChecks b.policy b.state ∧ allowedGraph fmtSnapshot b.policy.snapshot = true ∧
  (∀ v ∈ b.policy.validators, Label v) ∧
  ContentId b.schema ∧ ContentId b.arithmetic ∧
  (b.accumulator = [] ∨ ContentId b.accumulator) ∧
  ConfigIds b.policy b.proposed ∧ ConfigIds b.policy b.finalized ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (b.bodies.map Checked.id) = true ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT b.closed = true ∧
  (∀ id ∈ b.closed, ContentId id ∧ id ∈ b.bodies.map Checked.id) ∧
  b.candidate.action = 2 ∧ b.candidate.body ∈ b.closed ∧
  b.candidate.height = b.state.height ∧ b.candidate.view = b.state.view ∧
  b.candidate.context = b.context ∧ ContentId b.checkpoint
instance (b) : Decidable (Checks b) := by unfold Checks; infer_instance

def bindIsc (sha : Bytes → Bytes) (p : Policy) (s : State) : Option Bound := do
  let c ← NativeConfigAdmission.singleCandidate p.candidates
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
  let bodies ← NativeInputSetBody.checkAll sha (expected p s schema arithmetic) trees
  let (config,checkpoint) ← NativeConfigAdmission.configParents c.parents
  let context ← iscContext sha p.round
  let b := Bound.mk p s c checkpoint schema arithmetic accumulator proposed finalized id context trees bodies closed
  if id = computed ∧ ContentId id ∧ config = p.config ∧ Checks b then some b else none

def SourceChecks (sha : Bytes → Bytes) (p : Policy) (s : State) (b : Bound) : Prop :=
  b.policy = p ∧ b.state = s ∧ p.candidates = [b.candidate] ∧
  getText fmtSnapshot p.snapshot "state_id" = some b.snapshotId ∧
  NativeStateBytes.contentId sha NativeStateBytes.stateDomain
    (NativeStateBytes.encodeState s.wire) = some b.snapshotId ∧ ContentId b.snapshotId ∧
  getText fmtSnapshot p.snapshot "parameter_schema_id" = some b.schema ∧
  getText fmtSnapshot p.snapshot "arithmetic_profile_id" = some b.arithmetic ∧
  getText fmtSnapshot p.snapshot "required_accumulator_proof_id" = some b.accumulator ∧
  getTexts fmtSnapshot p.snapshot "proposed_round_config_ids" = some b.proposed ∧
  getTexts fmtSnapshot p.snapshot "finalized_round_config_ids" = some b.finalized ∧
  getTexts fmtSnapshot p.snapshot "closed_input_set_ids" = some b.closed ∧
  (lookup fmtSnapshot p.snapshot "input_set_bodies" >>= NativePolicyBytes.items) = some b.bodyTrees ∧
  NativeInputSetBody.checkAll sha (expected p s b.schema b.arithmetic) b.bodyTrees = some b.bodies ∧
  NativeConfigAdmission.configParents b.candidate.parents = some (p.config,b.checkpoint) ∧
  iscContext sha p.round = some b.context ∧ Checks b

theorem bindSource {sha p s b} (ok : bindIsc sha p s = some b) : SourceChecks sha p s b := by
  unfold bindIsc at ok
  simp only [bind,Option.bind_eq_some_iff] at ok
  obtain ⟨c,hc,id,hi,computed,hh,schema,hs,arithmetic,ha,accumulator,hu,
    proposed,hp,finalized,hf,closed,hl,trees,ht,bodies,hb,parents,hr,last⟩ := ok
  rcases parents with ⟨config,checkpoint⟩
  obtain ⟨context,hx,last⟩ := last
  dsimp only at last
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  have singleton : p.candidates = [c] := by
    unfold NativeConfigAdmission.singleCandidate at hc; split at hc <;> simp_all
  rcases checks with ⟨same,valid,parent,checks⟩
  subst computed; subst config
  exact ⟨rfl,rfl,singleton,hi,hh,valid,hs,ha,hu,hp,hf,hl,
    by simpa only [bind,Option.bind_eq_some_iff] using ht,hb,hr,hx,checks⟩

theorem bindFromComponents {sha p s b} (h : SourceChecks sha p s b) :
    bindIsc sha p s = some b := by
  rcases h with ⟨policy,state,cs,id,hashed,valid,schema,arithmetic,accumulator,
    proposed,finalized,closed,trees,bodies,parents,context,checks⟩
  unfold bindIsc
  rw [cs]
  simp only [NativeConfigAdmission.singleCandidate,bind,Option.bind]
  rw [id,hashed,schema,arithmetic,accumulator,proposed,finalized,closed]
  change ((lookup fmtSnapshot p.snapshot "input_set_bodies" >>= NativePolicyBytes.items) >>= _) = _
  rw [trees]
  simp only [bind,Option.bind]
  rw [bodies,parents,context]
  dsimp only [bind,Option.bind]
  have rebuilt : Bound.mk p s b.candidate b.checkpoint b.schema b.arithmetic b.accumulator
      b.proposed b.finalized b.snapshotId b.context b.bodyTrees b.bodies b.closed = b := by
    rw [← policy,← state]
  rw [rebuilt]
  simp only [true_and,ite_true,valid,checks]

def prepare (sha : Bytes → Bytes) (policyRaw stateRaw : Bytes) : Option Bound := do
  let (_,p) ← NativePolicyBytes.decodePolicy policyRaw
  let s ← NativeStateBytes.decodeState stateRaw
  bindIsc sha p s

theorem prepareSource {sha policyRaw stateRaw b}
    (ok : prepare sha policyRaw stateRaw = some b) :
    ∃ tree, NativePolicyBytes.decodePolicy policyRaw = some (tree,b.policy) ∧
    NativeStateBytes.decodeState stateRaw = some b.state ∧ SourceChecks sha b.policy b.state b := by
  unfold prepare at ok
  simp only [bind,Option.bind_eq_some_iff] at ok
  obtain ⟨⟨tree,p⟩,hp,s,hs,hb⟩ := ok
  have h := bindSource hb
  exact ⟨tree,h.1 ▸ hp,h.2.1 ▸ hs,by simpa only [h.1,h.2.1] using h⟩

def VoteChecks (b : Bound) (r : NativeConfigAdmission.RuntimeFacts) (v : Vote) : Prop :=
  NativeVoteBytes.VoteValid v ∧ v.wire.kind = ascii "ISC" ∧
  v.wire.validator = b.policy.localValidator ∧ v.wire.epoch = b.policy.epoch ∧
  v.wire.round = b.state.wire.round ∧ v.height = b.state.height ∧ v.view = b.state.view ∧
  v.wire.context = b.candidate.context ∧ v.wire.bodyHash = b.candidate.body ∧
  b.checkpoint = b.state.wire.parent ∧ v.sequence = r.expectedSequence ∧
  (r.recovery = true ∨ r.ready = true) ∧ r.invalidated = false ∧
  b.state.wire.phase = ascii "AVAILABLE" ∧ r.tick < b.policy.hardDeadline ∧
  r.tick < 256^8 ∧ r.expectedSequence < 256^8
instance (b r v) : Decidable (VoteChecks b r v) := by unfold VoteChecks; infer_instance

def checkVote (b : Bound) (r : NativeConfigAdmission.RuntimeFacts) (v : Vote) : Option Vote :=
  if VoteChecks b r v then some v else none

def fromBytes (sha : Bytes → Bytes) (policyRaw stateRaw voteRaw : Bytes)
    (r : NativeConfigAdmission.RuntimeFacts) : Option (Bound × Vote) := do
  let b ← prepare sha policyRaw stateRaw
  let v ← NativeVoteBytes.decodeFrame voteRaw
  let v ← checkVote b r v
  some (b,v)

theorem voteChecked {b r v out} (ok : checkVote b r v = some out) :
    out = v ∧ VoteChecks b r v := by
  unfold checkVote at ok; split at ok
  · exact ⟨(Option.some.inj ok).symm,‹VoteChecks _ _ _›⟩
  · contradiction

theorem fromBytesSource {sha policyRaw stateRaw voteRaw r b v}
    (ok : fromBytes sha policyRaw stateRaw voteRaw r = some (b,v)) :
    prepare sha policyRaw stateRaw = some b ∧ NativeVoteBytes.decodeFrame voteRaw = some v ∧ VoteChecks b r v := by
  unfold fromBytes at ok
  cases a : prepare sha policyRaw stateRaw with
  | none => simp [a] at ok
  | some bound =>
    cases q : NativeVoteBytes.decodeFrame voteRaw with
    | none => simp [a,q] at ok
    | some vote =>
      cases t : checkVote bound r vote with
      | none => simp [a,q,t] at ok
      | some out =>
        simp only [a,q,t,bind,Option.bind,Option.some.injEq] at ok
        cases ok
        obtain ⟨eq,checks⟩ := voteChecked t
        cases eq
        exact ⟨rfl,rfl,checks⟩

theorem fromComponents {sha policyRaw stateRaw voteRaw r b v}
    (policy : prepare sha policyRaw stateRaw = some b)
    (vote : NativeVoteBytes.decodeFrame voteRaw = some v)
    (checks : VoteChecks b r v) : fromBytes sha policyRaw stateRaw voteRaw r = some (b,v) := by
  have accepted : checkVote b r v = some v := if_pos checks
  simp only [fromBytes,policy,vote,accepted,bind,Option.bind]

theorem originalBytes {sha policyRaw stateRaw voteRaw r b v}
    (ok : fromBytes sha policyRaw stateRaw voteRaw r = some (b,v)) :
    NativeVoteBytes.encodeFrame v.wire = voteRaw :=
  (NativeVoteBytes.decodedVoteSound (fromBytesSource ok).2.1).2

theorem selectedBody {sha p s b} (ok : bindIsc sha p s = some b) :
    ∃ body ∈ b.bodies, body.id = b.candidate.body ∧
      NativeInputSetBody.CheckedSource sha (expected p s b.schema b.arithmetic) body.source body := by
  have h := bindSource ok
  rcases h with ⟨_,_,_,_,_,_,_,_,_,_,_,_,_,all,_,_,checks⟩
  rcases checks with ⟨_,_,_,_,_,_,_,_,_,_,members,_,closed,_⟩
  obtain ⟨body,mem,eq⟩ := List.mem_map.mp (members _ closed).2
  exact ⟨body,mem,eq,NativeInputSetBody.allChecked all body mem⟩

theorem allOriginalBodies {sha p s b} (ok : bindIsc sha p s = some b) :
    b.bodies.map Checked.source = b.bodyTrees ∧ b.bodies.length = b.bodyTrees.length := by
  have h := bindSource ok
  rcases h with ⟨_,_,_,_,_,_,_,_,_,_,_,_,_,all,_⟩
  exact ⟨NativeInputSetBody.allSources all,NativeInputSetBody.allCount all⟩

theorem selectedOriginalBody {sha policyRaw stateRaw voteRaw r b v}
    (ok : fromBytes sha policyRaw stateRaw voteRaw r = some (b,v)) :
    ∃ body ∈ b.bodies, body.id = v.wire.bodyHash ∧
      NativeInputSetBody.BodyValid (expected b.policy b.state b.schema b.arithmetic) body.body := by
  have source := fromBytesSource ok
  obtain ⟨tree,hp,hs,checked⟩ := prepareSource source.1
  obtain ⟨body,mem,id,valid⟩ := selectedBody (bindFromComponents checked)
  have eq := source.2.2.2.2.2.2.2.2.2.2.1
  exact ⟨body,mem,id.trans eq.symm,valid.2.2.2.2⟩

theorem invalidatedRejects {b r v} (h : r.invalidated = true) : checkVote b r v = none := by
  unfold checkVote; split
  · rename_i checks
    have g := checks.2.2.2.2.2.2.2.2.2.2.2.2.1
    simp [h] at g
  · rfl

theorem liveReadiness {b r v out} (ok : checkVote b r v = some out)
    (live : r.recovery = false) : r.ready = true := by
  rcases (voteChecked ok).2 with ⟨_,_,_,_,_,_,_,_,_,_,_,ready,_⟩
  rcases ready with ready | ready
  · simp [live] at ready
  · exact ready

theorem synthesizedSignerPolicy {b : Bound} (h : Checks b) :
    0 < (b.policy.validators.length-1)/3*2+1 ∧
    (b.policy.validators.length-1)/3*2+1 ≤ b.policy.validators.length ∧
    (b.policy.validators.length-1)/3*2+1 < 256^4 ∧
    (∀ v ∈ b.policy.validators, Label v) := by
  have header := h.1
  have count := header.1.1
  have bound := header.1.2.1
  have remainder := header.2.2.2.2.1
  exact ⟨by omega,by omega,by omega,h.2.2.1⟩

theorem sequencePreserved {b r v out} (ok : checkVote b r v = some out) :
    out.sequence = r.expectedSequence := by
  have h := voteChecked ok
  rw [h.1]
  exact h.2.2.2.2.2.2.2.2.2.2.2.1

end DeltaReduce.NativeIscAdmission
