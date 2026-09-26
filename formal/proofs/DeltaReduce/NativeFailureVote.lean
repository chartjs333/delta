import DeltaReduce.NativeFailureAuthority

/-! Original selected VIEW/ABORT vote identities and live/replay enabling.
Shared whole-policy validation, journal retry classification, WAL and QC remain open. -/
namespace DeltaReduce.NativeFailureVote
open NativeReceiptBytes NativeFailurePayload
open NativePolicyBytes (Policy Candidate)
open NativeStateBytes (State)
open NativeFailureAuthority (Entry checkpoint)
open NativeConfigAdmission (RuntimeFacts)
open NativeVoteBytes (Vote ascii)
open NativeFailureSection (Tail)

def kind : Nat → Option Bytes
  | 8 => some (ascii "VIEW_CHANGE")
  | 9 => some (ascii "ABORT")
  | _ => none

def matching (s : State) (v : Vote) (c : Candidate) : Bool :=
  kind c.action == some v.wire.kind && c.height == s.height && c.view == s.view &&
  c.context == v.wire.context

def phaseAllowed (phase : Bytes) : Prop :=
  phase ∈ NativeStateBytes.phases ∧ phase ≠ ascii "AGGREGATED" ∧ phase ≠ ascii "ABORTED"
instance (phase) : Decidable (phaseAllowed phase) := by unfold phaseAllowed; infer_instance

def requested (p : Policy) (t : Tail) : Bool :=
  t.requests.any (fun r => r.round == p.round && r.reason == p.reason)

def Enabled (p : Policy) (t : Tail) (r : RuntimeFacts) : Entry → Prop
  | .view _ => t.requests = [] ∧ p.softDeadline ≤ r.tick ∧ r.tick < p.hardDeadline
  | .abort a => a.row.body.reason = p.reason ∧ (requested p t = true ∨ p.hardDeadline ≤ r.tick)
instance (p t r e) : Decidable (Enabled p t r e) := by cases e <;> unfold Enabled <;> infer_instance

def VoteChecks (p : Policy) (s : State) (t : Tail) (c : Candidate) (e : Entry)
    (r : RuntimeFacts) (v : Vote) : Prop :=
  NativeVoteBytes.VoteValid v ∧ kind c.action = some v.wire.kind ∧
  v.wire.validator = p.localValidator ∧ v.wire.epoch = p.epoch ∧
  v.wire.round = s.wire.round ∧ v.height = s.height ∧ v.view = s.view ∧
  v.wire.context = c.context ∧ v.wire.bodyHash = c.body ∧
  checkpoint e = s.wire.parent ∧ v.sequence = r.expectedSequence ∧
  (r.recovery = true ∨ r.ready = true) ∧ r.invalidated = false ∧
  phaseAllowed s.wire.phase ∧ Enabled p t r e ∧ r.tick < 256^8 ∧ r.expectedSequence < 256^8
instance (p s t c e r v) : Decidable (VoteChecks p s t c e r v) := by
  unfold VoteChecks; infer_instance

def checkVote (p : Policy) (s : State) (t : Tail) (c : Candidate) (e : Entry)
    (r : RuntimeFacts) (v : Vote) : Option Vote :=
  if VoteChecks p s t c e r v then some v else none

theorem checkedVote {p s t c e r v out} (h : checkVote p s t c e r v = some out) :
    out = v ∧ VoteChecks p s t c e r v := by
  unfold checkVote at h; split at h
  · exact ⟨(Option.some.inj h).symm,‹VoteChecks _ _ _ _ _ _ _›⟩
  · contradiction

theorem voteFromComponents {p s t c e r v} (h : VoteChecks p s t c e r v) :
    checkVote p s t c e r v = some v := if_pos h

theorem liveReady {p s t c e r v out} (h : checkVote p s t c e r v = some out)
    (live : r.recovery = false) : r.ready = true := by
  rcases (checkedVote h).2 with ⟨_,_,_,_,_,_,_,_,_,_,_,ready,_⟩
  rcases ready with ready | ready
  · simp [live] at ready
  · exact ready

theorem temporal {p s t c e r v out} (h : checkVote p s t c e r v = some out) :
    phaseAllowed s.wire.phase ∧ Enabled p t r e := by
  rcases (checkedVote h).2 with ⟨_,_,_,_,_,_,_,_,_,_,_,_,_,phase,time,_⟩
  exact ⟨phase,time⟩

theorem viewWindow {p s t c e r v out} (h : checkVote p s t c (.view e) r v = some out) :
    t.requests = [] ∧ p.softDeadline ≤ r.tick ∧ r.tick < p.hardDeadline := (temporal h).2

theorem abortEarlyRequest {p s t c e r v out}
    (h : checkVote p s t c (.abort e) r v = some out) (early : r.tick < p.hardDeadline) :
    ∃ request ∈ t.requests, request.round = p.round ∧ request.reason = p.reason := by
  have time := (temporal h).2
  rcases time.2 with request | late
  · unfold requested at request
    obtain ⟨req,mem,ok⟩ := List.any_eq_true.mp request
    exact ⟨req,mem,by simpa using ok⟩
  · omega

theorem noTerminal {p s t c e r v out} (h : checkVote p s t c e r v = some out) :
    s.wire.phase ≠ ascii "AGGREGATED" ∧ s.wire.phase ≠ ascii "ABORTED" :=
  (temporal h).1.2

theorem originalIdentity {p s t c e r v out} (h : checkVote p s t c e r v = some out) :
    out = v ∧ v.wire.validator = p.localValidator ∧ v.wire.epoch = p.epoch ∧
    v.wire.bodyHash = c.body ∧ v.sequence = r.expectedSequence ∧ checkpoint e = s.wire.parent := by
  rcases checkedVote h with ⟨same,_,_,actor,epoch,_,_,_,_,body,parent,seq,_⟩
  exact ⟨same,actor,epoch,body,seq,parent⟩

structure Checked where
  policy : Policy
  state : State
  candidate : Candidate
  bound : NativeFailureAuthority.Bound
  vote : Vote

def fromBytes (sha : Bytes → Bytes) (policyRaw stateRaw voteRaw : Bytes) (r : RuntimeFacts) :
    Option Checked := do
  let (_,p) ← NativePolicyBytes.decodePolicy policyRaw
  let s ← NativeStateBytes.decodeState stateRaw
  let v ← NativeVoteBytes.decodeFrame voteRaw
  let c ← p.candidates.find? (matching s v)
  let b ← NativeFailureAuthority.bindCandidate sha p s c
  let v ← checkVote p s b.prior.tail c b.entry r v
  some ⟨p,s,c,b,v⟩

structure Source (sha : Bytes → Bytes) (policyRaw stateRaw voteRaw : Bytes)
    (r : RuntimeFacts) (x : Checked) : Prop where
  policy : ∃ tree, NativePolicyBytes.decodePolicy policyRaw = some (tree,x.policy)
  state : NativeStateBytes.decodeState stateRaw = some x.state
  vote : NativeVoteBytes.decodeFrame voteRaw = some x.vote
  selected : x.policy.candidates.find? (matching x.state x.vote) = some x.candidate
  bound : NativeFailureAuthority.bindCandidate sha x.policy x.state x.candidate = some x.bound
  checked : VoteChecks x.policy x.state x.bound.prior.tail x.candidate x.bound.entry r x.vote

theorem fromBytesSource {sha policyRaw stateRaw voteRaw r x}
    (h : fromBytes sha policyRaw stateRaw voteRaw r = some x) :
    Source sha policyRaw stateRaw voteRaw r x := by
  unfold fromBytes at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨tree,p⟩,hp,s,hs,v,hv,c,hc,b,hb,out,ho,last⟩ := h
  cases Option.some.inj last
  obtain ⟨same,checks⟩ := checkedVote ho
  cases same
  exact ⟨⟨tree,hp⟩,hs,hv,hc,hb,checks⟩

theorem selectedOriginal {sha policyRaw stateRaw voteRaw r x}
    (h : fromBytes sha policyRaw stateRaw voteRaw r = some x) :
    x.candidate ∈ x.policy.candidates ∧
    NativeFailureSection.bindSection sha x.policy x.state = some x.bound.prior ∧
    NativeFailureAuthority.EntrySource sha x.policy x.state x.bound.prior.tail x.candidate x.bound.entry := by
  have src := fromBytesSource h
  have b := NativeFailureAuthority.boundSource src.bound
  exact ⟨List.mem_of_find?_eq_some src.selected,b.1,NativeFailureAuthority.candidateSource b.2⟩

theorem exactVoteBytes {sha policyRaw stateRaw voteRaw r x}
    (h : fromBytes sha policyRaw stateRaw voteRaw r = some x) :
    NativeVoteBytes.encodeFrame x.vote.wire = voteRaw :=
  (NativeVoteBytes.decodedVoteSound (fromBytesSource h).vote).2
end DeltaReduce.NativeFailureVote
