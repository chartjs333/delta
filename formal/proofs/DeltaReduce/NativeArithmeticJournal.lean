import DeltaReduce.NativeVoteMetadata

/-! Separate candidate journal step. Source objects carry actual graph-loading
proofs and independently authenticated Binding premises, never vote approval
callbacks. The original whole mode and runtime arithmetic guard are unchanged. -/
namespace DeltaReduce.NativeArithmeticJournal
open NativeBinding
open NativeConfigReplay (Machine Stored facts fresh atVote)
open NativeVoteBytes (Vote)

structure Source (codec : Codec) (store : Store) (trust : Trust) (sha : Bytes → Bytes) where
  anchor : Anchor
  binding : Binding codec trust anchor store
  policyRaw : Bytes
  stateRaw : Bytes
  apc : Bytes
  config : Bytes
  proof : Bytes
  profile : Bytes
  permission : NativeAvailableQ.Permission
  inputs : List NativeAvailableQ.Input
  bound : NativeVectorContext.Bound
  loaded : NativeVectorContext.bind sha policyRaw stateRaw apc config proof profile permission inputs = some bound
  application : Option (NativeAggregateLineage.Edge × Bytes)

section Journal
variable {codec : Codec} {store : Store} {trust : Trust} (adapter : HashAdapter codec)

structure Arithmetic (s : Source codec store trust adapter.sha256) where
  vote : Vote
  computation : NativeArithmeticPrefix.Computation s.binding s.bound
  image : NativeVoteMetadata.Image s.binding
  id : Bytes

def projected (s : Source codec store trust adapter.sha256)
    (c : NativeArithmeticPrefix.Computation s.binding s.bound)
    (r : NativeConfigAdmission.RuntimeFacts) (v : Vote) : Option (NativeVoteMetadata.Image s.binding) :=
  match c with
  | .parameter p => NativeVoteMetadata.encode s.binding (.parameter p.computed.computation.native)
      s.bound r v p.admitted.selected.parents p.body.certificate.common.plan
  | .apply p => NativeVoteMetadata.encode s.binding (.apply p.computed.checked.result)
      s.bound r v p.admitted.selected.parents p.computed.original.decoded.candidate.root

theorem projectedOriginal {s : Source codec store trust adapter.sha256} {c r v image} (h : projected adapter s c r v = some image) :
    image.original = v ∧ image.metadata.logicalTime = r.tick ∧
    image.metadata.recovered = NativeVoteMetadata.completed r := by
  unfold projected at h
  split at h
  all_goals
    obtain ⟨f,_,_,hv,_,hm,_⟩ := NativeVoteMetadata.encoded _ h
    rw [hm]
    exact ⟨hv,rfl,rfl⟩

def stored {s : Source codec store trust adapter.sha256} (e : NativeWalBytes.Entry)
    (x : Arithmetic adapter s) : Stored :=
  let a := NativeArithmeticPrefix.admitted s.binding x.computation
  ⟨x.vote,NativeArithmeticPrefix.receipt e x.vote a.selected.original.action x.id,a.selected.original.parents⟩

def added (snap : Option NativeCommandReplay.Snapshot) (m : Machine) (e : NativeWalBytes.Entry)
    {s : Source codec store trust adapter.sha256} (x : Arithmetic adapter s) : Machine :=
  ⟨{m.core with sequence := e.sequence,matched := m.core.matched || NativeCommandReplay.mark snap e},
    m.votes ++ [stored adapter e x]⟩

def arithmetic (policy : Bytes) (snap : Option NativeCommandReplay.Snapshot)
    (m : Machine) (e : NativeWalBytes.Entry) (s : Source codec store trust adapter.sha256) :
    Option (Arithmetic adapter s) := do
  if s.policyRaw = policy ∧ s.stateRaw = m.core.state ∧ e.kind = 2 ∧
      e.sequence = m.core.sequence+1 ∧ e.sequence < 256^8 ∧ e.state = [] ∧ e.effects = [] ∧
      NativeWalBytes.policyId adapter.sha256 policy = some e.record then
    let v ← NativeVoteBytes.decodeFrame e.command
    let c ← NativeArithmeticPrefix.compute s.binding adapter s.bound s.application (facts m e) v
    let image ← projected adapter s c (facts m e) v
    let id ← NativeVoteBytes.voteId adapter.sha256 e.command
    let x := Arithmetic.mk v c image id
    if NativeReceiptBytes.Valid (stored adapter e x).receipt ∧ fresh m v ∧
        NativeCommandReplay.snapshotGuard snap (atVote m e) then some x else none
  else none

structure Checked (policy : Bytes) (snap : Option NativeCommandReplay.Snapshot)
    (m : Machine) (e : NativeWalBytes.Entry) (s : Source codec store trust adapter.sha256)
    (x : Arithmetic adapter s) : Prop where
  samePolicy : s.policyRaw = policy
  state : s.stateRaw = m.core.state
  kind : e.kind = 2
  position : e.sequence = m.core.sequence+1
  bounded : e.sequence < 256^8
  noState : e.state = []
  noEffects : e.effects = []
  policyHash : NativeWalBytes.policyId adapter.sha256 policy = some e.record
  vote : NativeVoteBytes.decodeFrame e.command = some x.vote
  computation : NativeArithmeticPrefix.compute s.binding adapter s.bound s.application (facts m e) x.vote = some x.computation
  image : projected adapter s x.computation (facts m e) x.vote = some x.image
  id : NativeVoteBytes.voteId adapter.sha256 e.command = some x.id
  receipt : NativeReceiptBytes.Valid (stored adapter e x).receipt
  fresh : fresh m x.vote
  snapshot : NativeCommandReplay.snapshotGuard snap (atVote m e)

theorem checked {policy snap m e} {s : Source codec store trust adapter.sha256} {x} (h : arithmetic adapter policy snap m e s = some x) :
    Checked adapter policy snap m e s x := by
  unfold arithmetic at h
  split at h <;> try contradiction
  rename_i shape
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨v,hv,c,hc,i,hi,id,hid,last⟩ := h
  split at last <;> try contradiction
  rename_i rest
  cases Option.some.inj last
  exact ⟨shape.1,shape.2.1,shape.2.2.1,shape.2.2.2.1,shape.2.2.2.2.1,
    shape.2.2.2.2.2.1,shape.2.2.2.2.2.2.1,shape.2.2.2.2.2.2.2,hv,hc,hi,hid,rest.1,rest.2.1,rest.2.2⟩

theorem arithmeticFromComponents {policy snap m e} {s : Source codec store trust adapter.sha256} {x} (h : Checked adapter policy snap m e s x) :
    arithmetic adapter policy snap m e s = some x := by
  have shape := And.intro h.samePolicy (And.intro h.state (And.intro h.kind (And.intro h.position
    (And.intro h.bounded (And.intro h.noState (And.intro h.noEffects h.policyHash))))))
  simp only [arithmetic,if_pos shape,h.vote,h.computation,h.image,h.id,bind,Option.bind]
  have eta : Arithmetic.mk x.vote x.computation x.image x.id = x := by cases x; rfl
  rw [eta]
  exact if_pos ⟨h.receipt,h.fresh,h.snapshot⟩

theorem actualPreparation {policy snap m e} {s : Source codec store trust adapter.sha256} {x} (h : Checked adapter policy snap m e s x) :
    NativeVectorContext.bind adapter.sha256 policy m.core.state s.apc s.config s.proof s.profile
      s.permission s.inputs = some s.bound := by
  rw [← h.samePolicy,← h.state]
  exact s.loaded

theorem originalVote {policy snap m e} {s : Source codec store trust adapter.sha256} {x} (h : Checked adapter policy snap m e s x) :
    NativeVoteBytes.encodeFrame x.vote.wire = e.command ∧ x.vote.sequence = e.sequence ∧
    x.image.original = x.vote ∧ x.image.metadata.recovered = false := by
  have selected := NativeArithmeticPrefix.computationSource s.binding h.computation
  have position := NativeArithmeticVote.selectedSequence selected
  have image := projectedOriginal adapter h.image
  exact ⟨(NativeVoteBytes.decodedVoteSound h.vote).2,position,image.1,
    image.2.2.trans (by rfl)⟩

theorem originalGuard {policy snap m e} {s : Source codec store trust adapter.sha256} {x} (h : Checked adapter policy snap m e s x) :
    NativeSelectedVote.checkVote (NativeVectorAuthority.policy s.bound) (NativeVectorAuthority.state s.bound)
      (NativeArithmeticPrefix.admitted s.binding x.computation).checked.snapshot.prior.tail
      (NativeArithmeticPrefix.admitted s.binding x.computation).selected (facts m e) x.vote = none :=
  NativeArithmeticVote.originalGuardStillRejects (NativeArithmeticPrefix.computationSource s.binding h.computation)

theorem scanCannotPrepare {policy snap m e} {s : Source codec store trust adapter.sha256} {x} (h : Checked adapter policy snap m e s x)
    (voteTrust : NativeVoteTrust) (auth : voteTrust.authenticated s.anchor x.image.metadata) (mode durable request) :
    prepareNativeFirst s.binding voteTrust x.image.metadata auth mode durable request = none := by
  apply nativeFirstRejectsUnready auth
  intro fresh
  have good := fresh.2.1
  simp [(originalVote adapter h).2.2.2] at good

theorem invalidatedRejects {policy snap m e} {s : Source codec store trust adapter.sha256} (bad : m.core.invalidated = true) :
    arithmetic adapter policy snap m e s = none := by
  cases h : arithmetic adapter policy snap m e s with
  | none => rfl
  | some x =>
    have source := NativeArithmeticPrefix.computationSource s.binding (checked adapter h).computation
    have good := (NativeArithmeticVote.environment source).2.1
    change m.core.invalidated = false at good
    simp [bad] at good

structure Input where
  entry : NativeWalBytes.Entry
  source : Option (Source codec store trust adapter.sha256)

structure Record where
  entry : NativeWalBytes.Entry
  source : Source codec store trust adapter.sha256
  result : Arithmetic adapter source

structure Transition where
  after : Machine
  arithmetic : Option (Record (store := store) (trust := trust) adapter)

/-- No-source selects only the original closed whole mode; a source selects only
the computed arithmetic path. Missing arithmetic or extra non-arithmetic source
data cannot be replaced by an approval callback. -/
def step (policy : Bytes) (snap : Option NativeCommandReplay.Snapshot)
    (m : Machine) (input : Input (store := store) (trust := trust) adapter) : Option (Transition (store := store) (trust := trust) adapter) :=
  match input.source with
  | none => (NativeConfigReplay.step .whole adapter.sha256 policy snap m input.entry).map (fun n => ⟨n,none⟩)
  | some s => do
    let x ← arithmetic adapter policy snap m input.entry s
    some ⟨added adapter snap m input.entry x,some ⟨input.entry,s,x⟩⟩

theorem stepSource {policy snap m} {input : Input (store := store) (trust := trust) adapter} {out} (h : step adapter policy snap m input = some out) :
    (input.source = none ∧ NativeConfigReplay.step .whole adapter.sha256 policy snap m input.entry = some out.after ∧ out.arithmetic = none) ∨
    (∃ s x, input.source = some s ∧ arithmetic adapter policy snap m input.entry s = some x ∧
      out = ⟨added adapter snap m input.entry x,some ⟨input.entry,s,x⟩⟩) := by
  unfold step at h
  cases hs : input.source with
  | none =>
    rw [hs] at h
    obtain ⟨n,hn,eq⟩ := Option.map_eq_some_iff.mp h
    cases eq
    exact Or.inl ⟨rfl,hn,rfl⟩
  | some s =>
    rw [hs] at h
    simp only [bind,Option.bind_eq_some_iff] at h
    obtain ⟨x,hx,last⟩ := h
    exact Or.inr ⟨s,x,rfl,hx,(Option.some.inj last).symm⟩

theorem stepSequence {policy snap m} {input : Input (store := store) (trust := trust) adapter} {out} (h : step adapter policy snap m input = some out) :
    out.after.core.sequence = m.core.sequence+1 ∧ out.after.core.sequence = input.entry.sequence := by
  rcases stepSource adapter h with ⟨_,legacy,_⟩ | ⟨s,x,_,arith,rfl⟩
  · exact NativeConfigReplay.stepSequence legacy
  · exact ⟨(checked adapter arith).position,rfl⟩

theorem stepCounts {policy snap m} {input : Input (store := store) (trust := trust) adapter} {out} (h : step adapter policy snap m input = some out) :
    out.after.core.requests.length + out.after.votes.length = m.core.requests.length + m.votes.length+1 := by
  rcases stepSource adapter h with ⟨_,legacy,_⟩ | ⟨s,x,_,arith,rfl⟩
  · exact NativeConfigReplay.stepCounts legacy
  · simp [added]; omega

theorem stepClock {policy snap m} {input : Input (store := store) (trust := trust) adapter} {out} (h : step adapter policy snap m input = some out) :
    m.core.tick ≤ out.after.core.tick ∧ (m.core.invalidated = true → out.after.core.invalidated = true) := by
  rcases stepSource adapter h with ⟨_,legacy,_⟩ | ⟨s,x,_,_,rfl⟩
  · exact NativeConfigReplay.stepClock legacy
  · exact ⟨Nat.le_refl _,fun h => h⟩

theorem stepUnique {policy snap m} {input : Input (store := store) (trust := trust) adapter} {out} (h : step adapter policy snap m input = some out)
    (unique : NativeConfigReplay.Unique m) : NativeConfigReplay.Unique out.after := by
  rcases stepSource adapter h with ⟨_,legacy,_⟩ | ⟨s,x,_,arith,rfl⟩
  · exact NativeConfigReplay.stepUnique legacy unique
  · refine ⟨unique.1,?_⟩
    change (m.votes ++ [stored adapter input.entry x]).Pairwise _
    rw [List.pairwise_append]
    refine ⟨unique.2,by simp,?_⟩
    intro old hold new hnew
    simp only [List.mem_singleton] at hnew
    subst new
    exact (checked adapter arith).fresh old hold

theorem stepSnapshot {policy snap m} {input : Input (store := store) (trust := trust) adapter} {out} (h : step adapter policy snap m input = some out) :
    (∀ s ∈ snap, input.entry.sequence = s.sequence → out.after.core.state = s.state) ∧
    out.after.core.matched = (m.core.matched || NativeCommandReplay.mark snap input.entry) := by
  rcases stepSource adapter h with ⟨_,legacy,_⟩ | ⟨s,x,_,arith,rfl⟩
  · exact NativeConfigReplay.stepSnapshot legacy
  · exact ⟨(checked adapter arith).snapshot,rfl⟩

def VoteCause (policy : Bytes) (snap : Option NativeCommandReplay.Snapshot)
    (m : Machine) (input : Input (store := store) (trust := trust) adapter) (vote : Stored) : Prop :=
  (input.source = none ∧ ∃ b v id,
    NativeConfigReplay.VoteEntry .whole adapter.sha256 policy snap m input.entry b v id ∧
    vote = ⟨v,NativeConfigReplay.voteReceipt .whole b input.entry v id,NativeReplayAdmission.parents .whole b⟩) ∨
  (∃ s x, input.source = some s ∧ arithmetic adapter policy snap m input.entry s = some x ∧
    vote = stored adapter input.entry x)

theorem stepVoteOrigin {policy snap m} {input : Input (store := store) (trust := trust) adapter} {out} (h : step adapter policy snap m input = some out)
    (vote : Stored) (mem : vote ∈ out.after.votes) :
    vote ∈ m.votes ∨ VoteCause adapter policy snap m input vote := by
  rcases stepSource adapter h with ⟨source,legacy,_⟩ | ⟨s,x,source,arith,rfl⟩
  · rcases NativeConfigReplay.stepSound legacy with ⟨_,_,same⟩ | ⟨b,v,id,checks,eq⟩
    · exact Or.inl (same ▸ mem)
    · rw [eq] at mem
      simp only [NativeConfigReplay.added,List.mem_append,List.mem_singleton] at mem
      rcases mem with old | eq
      · exact Or.inl old
      · exact Or.inr (Or.inl ⟨source,b,v,id,checks,eq⟩)
  · simp only [added,List.mem_append,List.mem_singleton] at mem
    rcases mem with old | eq
    · exact Or.inl old
    · exact Or.inr (Or.inr ⟨s,x,source,arith,eq⟩)

theorem stepRecord {policy snap m} {input : Input (store := store) (trust := trust) adapter} {out record} (h : step adapter policy snap m input = some out)
    (recorded : out.arithmetic = some record) :
    record.entry = input.entry ∧ input.source = some record.source ∧
    arithmetic adapter policy snap m input.entry record.source = some record.result := by
  rcases stepSource adapter h with ⟨_,_,none⟩ | ⟨s,x,source,arith,rfl⟩
  · rw [none] at recorded; contradiction
  · cases Option.some.inj recorded
    exact ⟨rfl,source,arith⟩

end Journal
end DeltaReduce.NativeArithmeticJournal
