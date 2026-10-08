import ProfileInstalledState
import SourceVote
import DeltaReduce.NativeSelectedVote

/-! T047/T053. Join successor original vote bytes to the whole installed state
and existing native fresh/recovery-scan admission guards. The field-only entry
view is never serialized through a legacy codec. Arithmetic refusal remains;
replay of an already retained vote is a distinct earlier journal branch.
RuntimeFacts are still source inputs: this checker is not their provenance. -/
namespace DeltaReduce.ProfileSource.SelectedVote
open NativeReceiptBytes (Bytes)
open NativePolicyCodec (Value)
open NativeConfigAdmission (RuntimeFacts)

def entryView (e : Candidates.Entry) : NativeCandidateAuthority.Entry :=
  ⟨e.original,e.parents⟩

def matching (s : NativeHeader.Coarse) (v : Vote.Vote) (c : NativePolicyBytes.Candidate) : Bool :=
  decide (1 ≤ c.action ∧ c.action ≤ 9) && NativeVoteBytes.actionName c.action == v.wire.kind &&
  c.height == s.height && c.view == s.view && c.context == v.wire.context

def Identity (p : NativePolicyBytes.Policy) (s : NativeHeader.Coarse)
    (e : Candidates.Entry) (r : RuntimeFacts) (v : Vote.Vote) : Prop :=
  v.wire.semantics = s.semantics ∧ v.wire.validator = p.localValidator ∧
  v.wire.epoch = p.epoch ∧ v.wire.round = s.round ∧ v.height = s.height ∧ v.view = s.view ∧
  v.wire.context = e.original.context ∧ v.wire.bodyHash = e.original.body ∧
  e.parents.checkpoint = s.parent ∧ v.sequence = r.expectedSequence
instance (p s e r v) : Decidable (Identity p s e r v) := by unfold Identity; infer_instance

def Checks (b : InstalledState.Bound) (e : Candidates.Entry) (r : RuntimeFacts) (v : Vote.Vote) : Prop :=
  Vote.VoteValid v ∧ NativeSelectedVote.GuardedAction e.original.action ∧
  NativeVoteBytes.actionName e.original.action = v.wire.kind ∧
  Identity b.installed.policy b.installed.header.state e r v ∧
  NativeSelectedVote.Environment b.installed.policy (Collections.stateView b.installed.header.state)
    b.collections.tail (entryView e) r
instance (b e r v) : Decidable (Checks b e r v) := by unfold Checks; infer_instance

def select (b : InstalledState.Bound) (v : Vote.Vote) : Option Candidates.Entry :=
  b.candidates.find? (fun e => matching b.installed.header.state v e.original)

def check (b : InstalledState.Bound) (r : RuntimeFacts) (v : Vote.Vote) : Option Candidates.Entry := do
  let e ← select b v
  if Checks b e r v then some e else none

theorem checked {b r v e} (ok : check b r v = some e) :
    select b v = some e ∧ Checks b e r v := by
  unfold check at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨e,hs,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  exact ⟨hs,checks⟩

theorem complete {b r v e} (selected : select b v = some e) (guards : Checks b e r v) :
    check b r v = some e := by simp only [check,selected,Bind.bind,Option.bind,if_pos guards]

theorem originalCandidate {sha enrolled actor configRaw stateRaw policyRaw stateValue originals b r v e}
    (source : InstalledState.bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals = some b)
    (ok : check b r v = some e) :
    e ∈ b.candidates ∧ Candidates.check sha b.installed.policy b.installed.header.state
      b.collections e.original = some e := by
  have member := List.mem_of_find?_eq_some (checked ok).1
  exact ⟨member,InstalledState.allCandidateSource source e member⟩

theorem currentParent {b r v e} (ok : check b r v = some e) :
    e.parents.checkpoint = b.installed.header.state.parent :=
  (checked ok).2.2.2.2.1.2.2.2.2.2.2.2.2.1

theorem originalPhysicalSequence {b r v e} (ok : check b r v = some e) :
    v.sequence = r.expectedSequence := (checked ok).2.2.2.2.1.2.2.2.2.2.2.2.2.2

theorem arithmeticRefusal {b r v e} (ok : check b r v = some e) :
    e.original.action ≠ 5 ∧ e.original.action ≠ 7 := (checked ok).2.2.1.2.2

theorem recoveryOnlyReadiness {b r v e} (ok : check b r v = some e) :
    check b {r with recovery := true, ready := false} v = some e := by
  have h := checked ok
  apply complete h.1
  obtain ⟨valid,guard,kind,identity,_,invalid,phase,time,bounds⟩ := h.2
  exact ⟨valid,guard,kind,identity,Or.inl rfl,invalid,phase,time,bounds⟩

structure Bound where
  state : InstalledState.Bound
  selected : Candidates.Entry
  vote : Vote.Vote

def bind (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment)
    (actor configRaw stateRaw policyRaw : Bytes) (stateValue : Value)
    (originals : Collections.Originals) (r : RuntimeFacts) (voteRaw : Bytes) : Option Bound := do
  let state ← InstalledState.bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals
  let vote ← Vote.decodeFrame voteRaw
  let selected ← check state r vote
  some ⟨state,selected,vote⟩

theorem boundSource {sha enrolled actor configRaw stateRaw policyRaw stateValue originals r voteRaw out}
    (ok : bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals r voteRaw = some out) :
    InstalledState.bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals = some out.state ∧
    Vote.decodeFrame voteRaw = some out.vote ∧ check out.state r out.vote = some out.selected := by
  unfold bind at ok
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨state,hs,vote,hv,selected,he,last⟩ := ok
  cases Option.some.inj last
  exact ⟨hs,hv,he⟩

theorem originalVoteBytes {sha enrolled actor configRaw stateRaw policyRaw stateValue originals r voteRaw out}
    (ok : bind sha enrolled actor configRaw stateRaw policyRaw stateValue originals r voteRaw = some out) :
    Vote.encodeFrame out.vote.wire = voteRaw ∧ out.vote.wire.semantics = out.state.installed.header.state.semantics ∧
    out.vote.sequence = r.expectedSequence ∧ out.selected.original.action ≠ 5 ∧
    out.selected.original.action ≠ 7 := by
  have h := boundSource ok
  exact ⟨(Vote.decodedVoteSound h.2.1).2,(checked h.2.2).2.2.2.2.1.1,
    originalPhysicalSequence h.2.2,arithmeticRefusal h.2.2⟩

end DeltaReduce.ProfileSource.SelectedVote
