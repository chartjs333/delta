import DeltaReduce.NativeCandidateAuthority
import DeltaReduce.NativeFailureVote

/-! Selected fresh/recovery-scan VOTE admission on the original complete policy.
The CURRENT native PARAMETER/APPLY guard remains mandatory. Recovery mode only
bypasses readiness; historical journal retries are a different earlier branch.
Runtime facts and SHA are explicit inputs, not authenticated observations. -/
namespace DeltaReduce.NativeSelectedVote
open NativeReceiptBytes
open NativePolicyBytes (Policy Candidate)
open NativeStateBytes (State)
open NativeVoteBytes (Vote ascii actionName)
open NativeConfigAdmission (RuntimeFacts)
open NativeCandidateAuthority (Entry CheckedPolicy)
open NativeFailureSection (Tail)

def GuardedAction (a : Nat) : Prop := 1 ≤ a ∧ a ≤ 9 ∧ a ≠ 5 ∧ a ≠ 7
instance (a) : Decidable (GuardedAction a) := by unfold GuardedAction; infer_instance

def phaseAllows (a : Nat) (phase : Bytes) : Prop :=
  match a with
  | 1 => phase = ascii "TICKETING_OPEN"
  | 2 => phase = ascii "AVAILABLE"
  | 3 | 4 | 5 | 6 | 7 => phase = ascii "ELIGIBLE"
  | 8 | 9 => NativeFailureVote.phaseAllowed phase
  | _ => False
instance (a phase) : Decidable (phaseAllows a phase) := by
  unfold phaseAllows; split <;> infer_instance

def enabled (p : Policy) (t : Tail) (a : Nat) (body : Bytes) (r : RuntimeFacts) : Prop :=
  if a = 8 then t.requests = [] ∧ p.softDeadline ≤ r.tick ∧ r.tick < p.hardDeadline
  else if a = 9 then
    match t.aborts.find? (fun e => e.id == body) with
    | some e => e.body.reason = p.reason ∧
        (NativeFailureVote.requested p t = true ∨ p.hardDeadline ≤ r.tick)
    | none => False
  else t.requests = [] ∧ r.tick < p.hardDeadline
instance (p t a body r) : Decidable (enabled p t a body r) := by
  unfold enabled; split <;> first | infer_instance | (split <;> first | infer_instance | (split <;> infer_instance))

def matching (s : State) (v : Vote) (c : Candidate) : Bool :=
  decide (1 ≤ c.action ∧ c.action ≤ 9) && actionName c.action == v.wire.kind &&
  c.height == s.height && c.view == s.view && c.context == v.wire.context

def Identity (p : Policy) (s : State) (e : Entry) (r : RuntimeFacts) (v : Vote) : Prop :=
  v.wire.validator = p.localValidator ∧ v.wire.epoch = p.epoch ∧
  v.wire.round = s.wire.round ∧ v.height = s.height ∧ v.view = s.view ∧
  v.wire.context = e.original.context ∧ v.wire.bodyHash = e.original.body ∧
  e.parents.checkpoint = s.wire.parent ∧ v.sequence = r.expectedSequence
instance (p s e r v) : Decidable (Identity p s e r v) := by unfold Identity; infer_instance

def Environment (p : Policy) (s : State) (t : Tail) (e : Entry) (r : RuntimeFacts) : Prop :=
  (r.recovery = true ∨ r.ready = true) ∧ r.invalidated = false ∧
  phaseAllows e.original.action s.wire.phase ∧ enabled p t e.original.action e.original.body r ∧
  r.tick < 256^8 ∧ r.expectedSequence < 256^8
instance (p s t e r) : Decidable (Environment p s t e r) := by unfold Environment; infer_instance

def Checks (p : Policy) (s : State) (t : Tail) (e : Entry) (r : RuntimeFacts) (v : Vote) : Prop :=
  NativeVoteBytes.VoteValid v ∧ GuardedAction e.original.action ∧
  actionName e.original.action = v.wire.kind ∧ Identity p s e r v ∧ Environment p s t e r
instance (p s t e r v) : Decidable (Checks p s t e r v) := by unfold Checks; infer_instance

def checkVote (p : Policy) (s : State) (t : Tail) (e : Entry) (r : RuntimeFacts) (v : Vote) : Option Vote :=
  if Checks p s t e r v then some v else none

theorem checkedVote {p s t e r v out} (h : checkVote p s t e r v = some out) :
    out = v ∧ Checks p s t e r v := by
  unfold checkVote at h; split at h
  · exact ⟨(Option.some.inj h).symm,‹Checks _ _ _ _ _ _›⟩
  · contradiction
theorem voteFromComponents {p s t e r v} (h : Checks p s t e r v) :
    checkVote p s t e r v = some v := if_pos h

theorem arithmeticGuard {p s t e r v out} (h : checkVote p s t e r v = some out) :
    e.original.action ≠ 5 ∧ e.original.action ≠ 7 := (checkedVote h).2.2.1.2.2
theorem arithmeticRejected {p s t e r v} (a : e.original.action = 5 ∨ e.original.action = 7) :
    checkVote p s t e r v = none := by
  cases h : checkVote p s t e r v with
  | none => rfl
  | some out => rcases a with a | a; exact False.elim ((arithmeticGuard h).1 a); exact False.elim ((arithmeticGuard h).2 a)

theorem originalIdentity {p s t e r v out} (h : checkVote p s t e r v = some out) :
    out = v ∧ Identity p s e r v := ⟨(checkedVote h).1,(checkedVote h).2.2.2.2.1⟩
theorem environmentRetained {p s t e r v out} (h : checkVote p s t e r v = some out) :
    Environment p s t e r := (checkedVote h).2.2.2.2.2
theorem liveReady {p s t e r v out} (h : checkVote p s t e r v = some out)
    (live : r.recovery = false) : r.ready = true := by
  rcases (environmentRetained h).1 with ready | ready
  · simp [live] at ready
  · exact ready
theorem invalidatedRejected {p s t e r v} (bad : r.invalidated = true) :
    checkVote p s t e r v = none := by
  cases h : checkVote p s t e r v with
  | none => rfl
  | some out => have valid := (environmentRetained h).2.1; simp [bad] at valid
theorem exactSequence {p s t e r v out} (h : checkVote p s t e r v = some out) :
    out.sequence = r.expectedSequence := by
  rw [(checkedVote h).1]
  exact (originalIdentity h).2.2.2.2.2.2.2.2.2
theorem currentParent {p s t e r v out} (h : checkVote p s t e r v = some out) :
    e.parents.checkpoint = s.wire.parent := (originalIdentity h).2.2.2.2.2.2.2.2.1
theorem viewWindow {p s t e r v out} (h : checkVote p s t e r v = some out)
    (a : e.original.action = 8) :
    t.requests = [] ∧ p.softDeadline ≤ r.tick ∧ r.tick < p.hardDeadline := by
  simpa only [enabled,a,ite_true] using (environmentRetained h).2.2.2.1
theorem ordinaryWindow {p s t e r v out} (h : checkVote p s t e r v = some out)
    (nv : e.original.action ≠ 8) (na : e.original.action ≠ 9) :
    t.requests = [] ∧ r.tick < p.hardDeadline := by
  simpa only [enabled,if_neg nv,if_neg na] using (environmentRetained h).2.2.2.1
theorem abortOriginalRow {p s t e r v out} (h : checkVote p s t e r v = some out)
    (a : e.original.action = 9) :
    ∃ row, t.aborts.find? (fun row => row.id == e.original.body) = some row ∧
      row.body.reason = p.reason ∧
      (NativeFailureVote.requested p t = true ∨ p.hardDeadline ≤ r.tick) := by
  have valid := (environmentRetained h).2.2.2.1
  simp only [enabled,a,show ¬ (9:Nat) = 8 by decide,ite_false,ite_true] at valid
  cases hr : t.aborts.find? (fun row => row.id == e.original.body) with
  | none => simp only [hr] at valid
  | some row => exact ⟨row,rfl,by simpa only [hr] using valid⟩
theorem abortEarlyRequest {p s t e r v out} (h : checkVote p s t e r v = some out)
    (a : e.original.action = 9) (early : r.tick < p.hardDeadline) :
    ∃ request ∈ t.requests, request.round = p.round ∧ request.reason = p.reason := by
  obtain ⟨_,_,_,time⟩ := abortOriginalRow h a
  rcases time with request | late
  · obtain ⟨req,mem,ok⟩ := List.any_eq_true.mp request
    exact ⟨req,mem,by simpa using ok⟩
  · omega
theorem recoveryOnlyReadiness {p s t e r v out} (h : checkVote p s t e r v = some out) :
    checkVote p s t e {r with recovery := true, ready := false} v = some v := by
  obtain ⟨_,valid,guard,kind,identity,_,invalid,phase,time,bounds⟩ := checkedVote h
  apply voteFromComponents
  exact ⟨valid,guard,kind,identity,Or.inl rfl,invalid,phase,time,bounds⟩

def select (b : CheckedPolicy) (s : State) (v : Vote) : Option Entry :=
  b.entries.find? (fun e => matching s v e.original)
def checkSelected (p : Policy) (s : State) (b : CheckedPolicy) (r : RuntimeFacts) (v : Vote) :
    Option Entry := do
  let e ← select b s v
  let _ ← checkVote p s b.snapshot.prior.tail e r v
  some e

theorem selectedSource {p s b r v e} (h : checkSelected p s b r v = some e) :
    select b s v = some e ∧ checkVote p s b.snapshot.prior.tail e r v = some v := by
  unfold checkSelected at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨out,ho,vote,hv,last⟩ := h
  cases Option.some.inj last
  exact ⟨ho,(checkedVote hv).1 ▸ hv⟩
theorem selectedFromComponents {p s b r v e}
    (hs : select b s v = some e) (hc : checkVote p s b.snapshot.prior.tail e r v = some v) :
    checkSelected p s b r v = some e := by simp only [checkSelected,hs,hc,bind,Option.bind]

theorem findOriginal (es : List Entry) (pred : Candidate → Bool) :
    (es.find? (fun e => pred e.original)).map Entry.original =
      (es.map Entry.original).find? pred := by
  induction es with
  | nil => rfl
  | cons e es ih => simp only [List.find?_cons,List.map_cons]; split <;> simp_all

theorem selectedOriginal {sha p s b r v e}
    (hb : NativeCandidateAuthority.bindPolicy sha p s = some b)
    (h : checkSelected p s b r v = some e) :
    p.candidates.find? (matching s v) = some e.original ∧
    NativeCandidateAuthority.check sha p s b.snapshot e.original = some e := by
  have hs := (selectedSource h).1
  have original := findOriginal b.entries (matching s v)
  change b.entries.find? (fun e => matching s v e.original) = some e at hs
  rw [hs,NativeCandidateAuthority.completeCandidateList hb] at original
  exact ⟨original.symm,NativeCandidateAuthority.everyCandidate hb e (List.mem_of_find?_eq_some hs)⟩

structure Admitted where
  checked : CheckedPolicy
  selected : Entry

def checkAdmission (sha : Bytes → Bytes) (p : Policy) (s : State) (r : RuntimeFacts) (v : Vote) :
    Option Admitted := do
  let b ← NativeCandidateAuthority.bindPolicy sha p s
  let e ← checkSelected p s b r v
  some ⟨b,e⟩
theorem admittedSource {sha p s r v out} (h : checkAdmission sha p s r v = some out) :
    NativeCandidateAuthority.bindPolicy sha p s = some out.checked ∧
    checkSelected p s out.checked r v = some out.selected := by
  unfold checkAdmission at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨b,hb,e,he,last⟩ := h
  cases Option.some.inj last
  exact ⟨hb,he⟩
theorem admitFromComponents {sha p s r v out}
    (hb : NativeCandidateAuthority.bindPolicy sha p s = some out.checked)
    (he : checkSelected p s out.checked r v = some out.selected) :
    checkAdmission sha p s r v = some out := by simp only [checkAdmission,hb,he,bind,Option.bind]
theorem wholePolicyFailure {sha p s r v}
    (h : NativeCandidateAuthority.bindPolicy sha p s = none) : checkAdmission sha p s r v = none := by
  simp only [checkAdmission,h,bind,Option.bind]
theorem admittedOriginal {sha p s r v out} (h : checkAdmission sha p s r v = some out) :
    p.candidates.find? (matching s v) = some out.selected.original ∧
    NativeCandidateAuthority.check sha p s out.checked.snapshot out.selected.original = some out.selected :=
  selectedOriginal (admittedSource h).1 (admittedSource h).2
theorem allOriginalCandidates {sha p s r v out} (h : checkAdmission sha p s r v = some out) :
    out.checked.entries.map Entry.original = p.candidates ∧
    NativeSnapshotBase.bindSnapshot sha p s = some out.checked.snapshot :=
  ⟨NativeCandidateAuthority.completeCandidateList (admittedSource h).1,
   (NativeCandidateAuthority.policySource (admittedSource h).1).1⟩

structure Checked where
  policy : Policy
  state : State
  admitted : Admitted
  vote : Vote

def fromBytes (sha : Bytes → Bytes) (policyRaw stateRaw voteRaw : Bytes) (r : RuntimeFacts) :
    Option Checked := do
  let (_,p) ← NativePolicyBytes.decodePolicy policyRaw
  let s ← NativeStateBytes.decodeState stateRaw
  let v ← NativeVoteBytes.decodeFrame voteRaw
  let a ← checkAdmission sha p s r v
  some ⟨p,s,a,v⟩

structure Source (sha : Bytes → Bytes) (policyRaw stateRaw voteRaw : Bytes)
    (r : RuntimeFacts) (x : Checked) : Prop where
  policy : ∃ tree, NativePolicyBytes.decodePolicy policyRaw = some (tree,x.policy)
  state : NativeStateBytes.decodeState stateRaw = some x.state
  vote : NativeVoteBytes.decodeFrame voteRaw = some x.vote
  admitted : checkAdmission sha x.policy x.state r x.vote = some x.admitted

theorem fromBytesSource {sha policyRaw stateRaw voteRaw r x}
    (h : fromBytes sha policyRaw stateRaw voteRaw r = some x) :
    Source sha policyRaw stateRaw voteRaw r x := by
  unfold fromBytes at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨tree,p⟩,hp,s,hs,v,hv,a,ha,last⟩ := h
  cases Option.some.inj last
  exact ⟨⟨tree,hp⟩,hs,hv,ha⟩
theorem fromBytesComponents {sha policyRaw stateRaw voteRaw r x}
    (h : Source sha policyRaw stateRaw voteRaw r x) :
    fromBytes sha policyRaw stateRaw voteRaw r = some x := by
  obtain ⟨tree,hp⟩ := h.policy
  simp only [fromBytes,hp,h.state,h.vote,h.admitted,bind,Option.bind]
theorem originalBytes {sha policyRaw stateRaw voteRaw r x}
    (h : fromBytes sha policyRaw stateRaw voteRaw r = some x) :
    NativeVoteBytes.encodeFrame x.vote.wire = voteRaw ∧
    NativeStateBytes.encodeState x.state.wire = stateRaw ∧
    ∃ tree body, NativePolicyBytes.extract tree = some x.policy ∧
      NativePolicyCodec.encode NativePolicySchema.fmtPolicy tree = some body ∧
      policyRaw = NativePolicyBytes.header ++ body := by
  have src := fromBytesSource h
  obtain ⟨tree,hp⟩ := src.policy
  obtain ⟨body,encoded,bytes⟩ := (NativePolicyBytes.decoded hp).2
  exact ⟨(NativeVoteBytes.decodedVoteSound src.vote).2,(NativeStateBytes.stateSound src.state).2,
    tree,body,NativePolicyBytes.acceptedExtraction hp,encoded,bytes.symm⟩
theorem originalByteAuthority {sha policyRaw stateRaw voteRaw r x}
    (h : fromBytes sha policyRaw stateRaw voteRaw r = some x) :
    NativePolicyBytes.Canonical x.policy ∧
    NativeSnapshotBase.bindSnapshot sha x.policy x.state = some x.admitted.checked.snapshot ∧
    x.admitted.checked.entries.map Entry.original = x.policy.candidates ∧
    x.policy.candidates.find? (matching x.state x.vote) = some x.admitted.selected.original ∧
    Checks x.policy x.state x.admitted.checked.snapshot.prior.tail x.admitted.selected r x.vote := by
  have src := fromBytesSource h
  have all := allOriginalCandidates src.admitted
  exact ⟨NativePolicyBytes.acceptedCanonical src.policy.choose_spec,all.2,all.1,
    (admittedOriginal src.admitted).1,
    (checkedVote (selectedSource (admittedSource src.admitted).2).2).2⟩

theorem sharedFailureTail {sha p s r v out} (h : checkAdmission sha p s r v = some out) :
    NativeFailureSection.checkTail sha p s = some out.checked.snapshot.prior.tail :=
  NativeCandidateAuthority.failureTailOriginal (admittedSource h).1

theorem byteGuardRetained {sha policyRaw stateRaw voteRaw r x}
    (h : fromBytes sha policyRaw stateRaw voteRaw r = some x) :
    x.admitted.selected.original.action ≠ 5 ∧ x.admitted.selected.original.action ≠ 7 :=
  arithmeticGuard (selectedSource (admittedSource (fromBytesSource h).admitted).2).2

theorem allowedKinds {p s t e r v out} (h : checkVote p s t e r v = some out) :
    v.wire.kind ∈ [actionName 1,actionName 2,actionName 3,actionName 4,
      actionName 6,actionName 8,actionName 9] := by
  have guard := (checkedVote h).2.2.1
  have kind := (checkedVote h).2.2.2.1
  have actions : e.original.action = 1 ∨ e.original.action = 2 ∨ e.original.action = 3 ∨
      e.original.action = 4 ∨ e.original.action = 6 ∨ e.original.action = 8 ∨ e.original.action = 9 := by
    unfold GuardedAction at guard; omega
  rcases actions with a | a | a | a | a | a | a <;> rw [← kind,a] <;> simp

theorem arithmeticKindRejected {p s t e r v}
    (kind : v.wire.kind = actionName 5 ∨ v.wire.kind = actionName 7) :
    checkVote p s t e r v = none := by
  cases h : checkVote p s t e r v with
  | none => rfl
  | some out =>
    have allowed := allowedKinds h
    rcases kind with kind | kind <;> rw [kind] at allowed
    · exact False.elim ((by decide : ¬ actionName 5 ∈
        [actionName 1,actionName 2,actionName 3,actionName 4,actionName 6,actionName 8,actionName 9]) allowed)
    · exact False.elim ((by decide : ¬ actionName 7 ∈
        [actionName 1,actionName 2,actionName 3,actionName 4,actionName 6,actionName 8,actionName 9]) allowed)

theorem recoveryStillChecks {p s t e r v out}
    (h : checkVote p s t e {r with recovery := true, ready := false} v = some out) :
    GuardedAction e.original.action ∧ Identity p s e r v ∧ r.invalidated = false ∧
    phaseAllows e.original.action s.wire.phase ∧ enabled p t e.original.action e.original.body r := by
  have checks := (checkedVote h).2
  exact ⟨checks.2.1,checks.2.2.2.1,checks.2.2.2.2.2.1,
    checks.2.2.2.2.2.2.1,checks.2.2.2.2.2.2.2.1⟩
end DeltaReduce.NativeSelectedVote
