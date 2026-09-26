import DeltaReduce.NativeProposalAdmission

/-! Closed computed admission modes for the shared native journal fold.
No caller-defined admission function or successful-result Boolean is accepted. -/
namespace DeltaReduce.NativeReplayAdmission
open NativeReceiptBytes NativeVoteBytes

inductive Mode where
  | config
  | proposals
  deriving DecidableEq, Repr

def Startup : Mode → Type
  | .config => NativeConfigAdmission.Bound
  | .proposals => NativeProposalAdmission.Bound

def Selected : Mode → Type
  | .config => NativeConfigAdmission.Bound
  | .proposals => NativeProposalAdmission.Bound × NativeProposalAdmission.Prepared

def prepare (mode : Mode) (sha : Bytes → Bytes) (policy initial : Bytes) : Option (Startup mode) :=
  match mode with
  | .config => NativeConfigAdmission.prepare sha policy initial
  | .proposals => NativeProposalAdmission.prepare sha policy initial

def initialTick (mode : Mode) : Startup mode → Nat :=
  match mode with
  | .config => fun b => b.policy.initialTick
  | .proposals => fun b => b.graph.policy.initialTick

def fromBytes (mode : Mode) (sha : Bytes → Bytes) (policy state raw : Bytes)
    (facts : NativeConfigAdmission.RuntimeFacts) : Option (Selected mode × Vote) :=
  match mode with
  | .config => NativeConfigAdmission.fromBytes sha policy state raw facts
  | .proposals => do
    let (b,c,v) ← NativeProposalAdmission.fromBytes sha policy state raw facts
    some ((b,c),v)

def parents (mode : Mode) : Selected mode → NativePolicyCodec.Value :=
  match mode with
  | .config => fun b => b.candidate.parents
  | .proposals => fun b => b.2.candidate.parents

def action (mode : Mode) : Selected mode → Nat :=
  match mode with
  | .config => fun _ => 1
  | .proposals => fun b => b.2.candidate.action

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

theorem byteIdentity {mode sha policy state raw facts b v}
    (h : fromBytes mode sha policy state raw facts = some (b,v)) :
    encodeFrame v.wire = raw := by
  cases mode with
  | config => exact NativeConfigAdmission.byteIdentity h
  | proposals => exact NativeProposalAdmission.originalVoteBytes (proposalExact h)

theorem originalSequence {mode sha policy state raw facts b v}
    (h : fromBytes mode sha policy state raw facts = some (b,v)) : v.sequence = facts.expectedSequence := by
  cases mode with
  | config => exact (NativeConfigAdmission.admittedSource h).2.2.2.2.2.2.2.2.2.2.2.1
  | proposals =>
    have checked := (NativeProposalAdmission.fromBytesSource (proposalExact h)).2.2.2
    exact checked.2.2.2.2.2.2.2.2.2.2.1

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
    (h : fromBytes mode sha policy state raw facts = some (b,v)) :
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

end DeltaReduce.NativeReplayAdmission
