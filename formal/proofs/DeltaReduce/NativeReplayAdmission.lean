import DeltaReduce.NativeProposalAdmission
import DeltaReduce.NativeSelectedVote

/-! Closed computed admission modes for the shared native journal fold.
No caller-defined admission function or successful-result Boolean is accepted. -/
namespace DeltaReduce.NativeReplayAdmission
open NativeReceiptBytes NativeVoteBytes

inductive Mode where
  | config
  | proposals
  | whole
  deriving DecidableEq, Repr

structure WholeStartup where
  policy : NativePolicyBytes.Policy
  state : NativeStateBytes.State
  checked : NativeCandidateAuthority.CheckedPolicy

def prepareWhole (sha : Bytes → Bytes) (policy initial : Bytes) : Option WholeStartup := do
  let (_,p) ← NativePolicyBytes.decodePolicy policy
  let s ← NativeStateBytes.decodeState initial
  let checked ← NativeCandidateAuthority.bindPolicy sha p s
  some ⟨p,s,checked⟩

theorem wholeStartupSource {sha policy initial b}
    (h : prepareWhole sha policy initial = some b) :
    (∃ tree, NativePolicyBytes.decodePolicy policy = some (tree,b.policy)) ∧
    NativeStateBytes.decodeState initial = some b.state ∧
    NativeCandidateAuthority.bindPolicy sha b.policy b.state = some b.checked := by
  unfold prepareWhole at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨tree,p⟩,hp,s,hs,c,hc,last⟩ := h
  cases Option.some.inj last
  exact ⟨⟨tree,hp⟩,hs,hc⟩

theorem wholeStartupComponents {sha policy initial tree b}
    (hp : NativePolicyBytes.decodePolicy policy = some (tree,b.policy))
    (hs : NativeStateBytes.decodeState initial = some b.state)
    (hc : NativeCandidateAuthority.bindPolicy sha b.policy b.state = some b.checked) :
    prepareWhole sha policy initial = some b := by
  simp only [prepareWhole,hp,hs,hc,bind,Option.bind]

def Startup : Mode → Type
  | .config => NativeConfigAdmission.Bound
  | .proposals => NativeProposalAdmission.Bound
  | .whole => WholeStartup

def Selected : Mode → Type
  | .config => NativeConfigAdmission.Bound
  | .proposals => NativeProposalAdmission.Bound × NativeProposalAdmission.Prepared
  | .whole => NativeSelectedVote.Checked

def prepare (mode : Mode) (sha : Bytes → Bytes) (policy initial : Bytes) : Option (Startup mode) :=
  match mode with
  | .config => NativeConfigAdmission.prepare sha policy initial
  | .proposals => NativeProposalAdmission.prepare sha policy initial
  | .whole => prepareWhole sha policy initial

def initialTick (mode : Mode) : Startup mode → Nat :=
  match mode with
  | .config => fun b => b.policy.initialTick
  | .proposals => fun b => b.graph.policy.initialTick
  | .whole => fun b => b.policy.initialTick

def fromBytes (mode : Mode) (sha : Bytes → Bytes) (policy state raw : Bytes)
    (facts : NativeConfigAdmission.RuntimeFacts) : Option (Selected mode × Vote) :=
  match mode with
  | .config => NativeConfigAdmission.fromBytes sha policy state raw facts
  | .proposals => do
    let (b,c,v) ← NativeProposalAdmission.fromBytes sha policy state raw facts
    some ((b,c),v)
  | .whole => do
    let x ← NativeSelectedVote.fromBytes sha policy state raw facts
    some (x,x.vote)

def parents (mode : Mode) : Selected mode → NativePolicyCodec.Value :=
  match mode with
  | .config => fun b => b.candidate.parents
  | .proposals => fun b => b.2.candidate.parents
  | .whole => fun b => b.admitted.selected.original.parents

def action (mode : Mode) : Selected mode → Nat :=
  match mode with
  | .config => fun _ => 1
  | .proposals => fun b => b.2.candidate.action
  | .whole => fun b => b.admitted.selected.original.action

theorem configExact (sha policy state raw facts) :
    fromBytes .config sha policy state raw facts =
      NativeConfigAdmission.fromBytes sha policy state raw facts := rfl

theorem proposalExact {sha policy state raw facts b c v}
    (h : fromBytes .proposals sha policy state raw facts = some ((b,c),v)) :
    NativeProposalAdmission.fromBytes sha policy state raw facts = some (b,c,v) := by
  unfold fromBytes at h
  cases hp : NativeProposalAdmission.fromBytes sha policy state raw facts with
  | none => simp [hp] at h
  | some out =>
    rcases out with ⟨bb,cc,vv⟩
    simp only [hp,bind,Option.bind] at h
    cases Option.some.inj h
    rfl

theorem proposalFromComponents {sha policy state raw facts b c v}
    (prepared : NativeProposalAdmission.prepare sha policy state = some b)
    (parsed : decodeFrame raw = some v)
    (selected : NativeProposalAdmission.select b facts v = some c) :
    fromBytes .proposals sha policy state raw facts = some ((b,c),v) := by
  simp only [fromBytes,NativeProposalAdmission.fromBytes,prepared,parsed,selected,bind,Option.bind]
  rfl

theorem wholeExact {sha policy state raw facts b v}
    (h : fromBytes .whole sha policy state raw facts = some (b,v)) :
    NativeSelectedVote.fromBytes sha policy state raw facts = some b ∧ v = b.vote := by
  unfold fromBytes at h
  cases hs : NativeSelectedVote.fromBytes sha policy state raw facts with
  | none => simp [hs] at h
  | some out =>
    simp only [hs,bind,Option.bind] at h
    cases Option.some.inj h
    exact ⟨rfl,rfl⟩

theorem wholeFromComponents {sha policy state raw facts b}
    (h : NativeSelectedVote.fromBytes sha policy state raw facts = some b) :
    fromBytes .whole sha policy state raw facts = some (b,b.vote) := by
  simp only [fromBytes,h,bind,Option.bind]
  rfl

theorem wholeChecks {sha policy state raw facts b v}
    (h : fromBytes .whole sha policy state raw facts = some (b,v)) :
    NativeSelectedVote.checkVote b.policy b.state b.admitted.checked.snapshot.prior.tail
      b.admitted.selected facts v = some v := by
  obtain ⟨original,rfl⟩ := wholeExact h
  exact (NativeSelectedVote.selectedSource
    (NativeSelectedVote.admittedSource (NativeSelectedVote.fromBytesSource original).admitted).2).2

theorem byteIdentity {mode sha policy state raw facts b v}
    (h : fromBytes mode sha policy state raw facts = some (b,v)) :
    encodeFrame v.wire = raw := by
  cases mode with
  | config => exact NativeConfigAdmission.byteIdentity h
  | proposals => exact NativeProposalAdmission.originalVoteBytes (proposalExact h)
  | whole =>
    obtain ⟨source,rfl⟩ := wholeExact h
    exact (NativeSelectedVote.originalBytes source).1

theorem originalSequence {mode sha policy state raw facts b v}
    (h : fromBytes mode sha policy state raw facts = some (b,v)) : v.sequence = facts.expectedSequence := by
  cases mode with
  | config => exact (NativeConfigAdmission.admittedSource h).2.2.2.2.2.2.2.2.2.2.2.1
  | proposals =>
    have checked := (NativeProposalAdmission.fromBytesSource (proposalExact h)).2.2.2
    exact checked.2.2.2.2.2.2.2.2.2.2.1
  | whole => exact NativeSelectedVote.exactSequence (wholeChecks h)

theorem proposalOriginalSource {sha policy state raw facts b c v}
    (h : fromBytes .proposals sha policy state raw facts = some ((b,c),v)) :
    c.candidate ∈ b.graph.policy.candidates ∧
    NativeProposalAdmission.CandidateSource sha b.graph c.candidate c ∧
    NativeProposalAdmission.VoteChecks b.graph c facts v := by
  have source := proposalExact h
  exact ⟨(NativeProposalAdmission.selectedOriginalCandidate source).1,
    (NativeProposalAdmission.selectedOriginalCandidate source).2,
    (NativeProposalAdmission.fromBytesSource source).2.2.2⟩

theorem proposalIscBody {sha policy state raw facts b c v}
    (h : fromBytes .proposals sha policy state raw facts = some ((b,c),v))
    (isc : c.candidate.action = 2) :
    ∃ body ∈ b.graph.bodies, body.id = v.wire.bodyHash ∧
      NativeInputSetBody.CheckedSource sha
        (NativeIscAdmission.expected b.graph.policy b.graph.state b.graph.schema b.graph.arithmetic)
        body.source body := NativeProposalAdmission.selectedIscBody (proposalExact h) isc

theorem actionMatches {mode sha policy state raw facts b v}
    (h : fromBytes mode sha policy state raw facts = some (b,v))
    (restricted : mode = .config ∨ mode = .proposals) :
    (action mode b = 1 ∧ v.wire.kind = NativeConfigAdmission.ascii "ROUND_CONFIG") ∨
    (action mode b = 2 ∧ v.wire.kind = NativeConfigAdmission.ascii "ISC") := by
  cases mode with
  | config => exact Or.inl ⟨rfl,(NativeConfigAdmission.admittedSource h).2.2.1⟩
  | proposals =>
    obtain ⟨body,candidate⟩ := b
    have original := proposalOriginalSource h
    have kind := original.2.2.2.1
    rcases original.2.1.2.2.2.1 with cfg | isc
    · exact Or.inl ⟨cfg.1,by simpa [NativeProposalAdmission.kind,cfg.1] using kind.symm⟩
    · exact Or.inr ⟨isc.1,by simpa [NativeProposalAdmission.kind,isc.1] using kind.symm⟩

  | whole => cases restricted <;> contradiction

theorem guardedActionMatches {mode sha policy state raw facts b v}
    (h : fromBytes mode sha policy state raw facts = some (b,v)) :
    NativeSelectedVote.GuardedAction (action mode b) ∧
      actionName (action mode b) = v.wire.kind := by
  cases mode with
  | config =>
    obtain ⟨act,kind⟩ | ⟨act,kind⟩ := actionMatches h (Or.inl rfl)
    · exact ⟨by rw [act]; decide,by rw [act,kind]; rfl⟩
    · exact ⟨by rw [act]; decide,by rw [act,kind]; rfl⟩
  | proposals =>
    obtain ⟨act,kind⟩ | ⟨act,kind⟩ := actionMatches h (Or.inr rfl)
    · exact ⟨by rw [act]; decide,by rw [act,kind]; rfl⟩
    · exact ⟨by rw [act]; decide,by rw [act,kind]; rfl⟩
  | whole =>
    have checked := (NativeSelectedVote.checkedVote (wholeChecks h)).2
    exact ⟨checked.2.1,checked.2.2.1⟩

theorem wholeInvalidated {sha policy state raw facts}
    (bad : facts.invalidated = true) : fromBytes .whole sha policy state raw facts = none := by
  cases h : fromBytes .whole sha policy state raw facts with
  | none => rfl
  | some pair =>
    obtain ⟨b,v⟩ := pair
    have valid := (NativeSelectedVote.environmentRetained (wholeChecks h)).2.1
    simp [bad] at valid

end DeltaReduce.NativeReplayAdmission
