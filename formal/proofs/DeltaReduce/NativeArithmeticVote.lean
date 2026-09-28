import DeltaReduce.NativeAggregateBinding
import DeltaReduce.NativeSelectedVote

/-! Candidate-only arithmetic vote admission. The original NativeSelectedVote
guard is unchanged. Original DRC1 votes and projected JSON bodies are retained
separately; neither identity nor signature authentication is manufactured. -/
namespace DeltaReduce.NativeArithmeticVote
open NativeBinding
open NativeVectorAuthority (policy state)
open NativeVectorLayout (text)
open NativeVoteBytes (Vote)
open NativeConfigAdmission (RuntimeFacts)
open NativeCandidateAuthority (Entry CheckedPolicy)

def Checks (p : NativePolicyBytes.Policy) (s : NativeStateBytes.State)
    (t : NativeFailureSection.Tail) (e : Entry) (r : RuntimeFacts) (v : Vote) : Prop :=
  NativeVoteBytes.VoteValid v ∧ (e.original.action = 5 ∨ e.original.action = 7) ∧
  NativeVoteBytes.actionName e.original.action = v.wire.kind ∧
  NativeSelectedVote.Identity p s e r v ∧ NativeSelectedVote.Environment p s t e r
instance (p s t e r v) : Decidable (Checks p s t e r v) := by unfold Checks; infer_instance

def select (sha : Bytes → Bytes) (b : NativeVectorContext.Bound) (r : RuntimeFacts) (v : Vote) :
    Option NativeSelectedVote.Admitted := do
  let checked ← NativeCandidateAuthority.bindPolicy sha (policy b) (state b)
  let e ← NativeSelectedVote.select checked (state b) v
  if Checks (policy b) (state b) checked.snapshot.prior.tail e r v then
    some ⟨checked,e⟩ else none

theorem selected {sha b r v out} (h : select sha b r v = some out) :
    NativeCandidateAuthority.bindPolicy sha (policy b) (state b) = some out.checked ∧
    NativeSelectedVote.select out.checked (state b) v = some out.selected ∧
    Checks (policy b) (state b) out.checked.snapshot.prior.tail out.selected r v := by
  simp only [select,bind,Option.bind_eq_some_iff] at h
  obtain ⟨s,hs,e,he,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨hs,he,by assumption⟩

theorem originalCandidate {sha b r v out} (h : select sha b r v = some out) :
    (policy b).candidates.find? (NativeSelectedVote.matching (state b) v) = some out.selected.original ∧
    NativeCandidateAuthority.check sha (policy b) (state b) out.checked.snapshot
      out.selected.original = some out.selected := by
  have src := selected h
  have hs := src.2.1
  change out.checked.entries.find? (fun e => NativeSelectedVote.matching (state b) v e.original) = some out.selected at hs
  have same := NativeSelectedVote.findOriginal out.checked.entries (NativeSelectedVote.matching (state b) v)
  rw [hs,NativeCandidateAuthority.completeCandidateList src.1] at same
  exact ⟨same.symm,NativeCandidateAuthority.everyCandidate src.1 _ (List.mem_of_find?_eq_some hs)⟩

theorem identity {sha b r v out} (h : select sha b r v = some out) :
    NativeSelectedVote.Identity (policy b) (state b) out.selected r v :=
  (selected h).2.2.2.2.2.1

theorem environment {sha b r v out} (h : select sha b r v = some out) :
    NativeSelectedVote.Environment (policy b) (state b) out.checked.snapshot.prior.tail out.selected r :=
  (selected h).2.2.2.2.2.2

theorem originalGuardStillRejects {sha b r v out} (h : select sha b r v = some out) :
    NativeSelectedVote.checkVote (policy b) (state b) out.checked.snapshot.prior.tail out.selected r v = none :=
  NativeSelectedVote.arithmeticRejected (selected h).2.2.2.1

theorem selectedSequence {sha b r v out} (h : select sha b r v = some out) :
    v.sequence = r.expectedSequence := (identity h).2.2.2.2.2.2.2.2

theorem selectedWindow {sha b r v out} (h : select sha b r v = some out) :
    out.checked.snapshot.prior.tail.requests = [] ∧ r.tick < (policy b).hardDeadline := by
  have a := (selected h).2.2.2.1
  have window := (environment h).2.2.2.1
  rcases a with a | a <;> simpa [NativeSelectedVote.enabled,a] using window

theorem invalidatedRejected {sha b r v} (bad : r.invalidated = true) : select sha b r v = none := by
  cases h : select sha b r v with
  | none => rfl
  | some out => have good := (environment h).2.1; simp [bad] at good

section Arithmetic
variable {codec store trust anchor} (binding : Binding codec trust anchor store)

structure Parameter (b : NativeVectorContext.Bound) where
  admitted : NativeSelectedVote.Admitted
  body : NativeParameterLineage.Edge
  index : Nat
  computed : NativeVectorAuthority.Verified binding b body.certificate.common.domain index

def parameter (adapter : HashAdapter codec) (b : NativeVectorContext.Bound) (r : RuntimeFacts) (v : Vote) :
    Option (Parameter binding b) := do
  let admitted ← select adapter.sha256 b r v
  if admitted.selected.original.action = 5 then
    let body ← (NativeCandidateAuthority.parameterSection admitted.checked.snapshot).bodies.find?
      (fun e => e.id == admitted.selected.original.body)
    let index ← NativeCertifiedCorpus.ordinal b (text body.certificate.common.shard)
    let computed ← NativeVectorAuthority.verify binding adapter.sha256 b body.certificate.common.domain index
    if computed.selected.original.certificate.common = body.certificate.common ∧
        computed.selected.original.voteContext = body.voteContext ∧
        computed.selected.original.id = body.id ∧
        NativeCertifiedCorpus.ExactBody body.certificate.common computed.leaves computed.computation.native.numerators = true then
      some ⟨admitted,body,index,computed⟩ else none
  else none

theorem parameterSource {adapter b r v out} (h : parameter binding adapter b r v = some out) :
    select adapter.sha256 b r v = some out.admitted ∧ out.admitted.selected.original.action = 5 ∧
    (NativeCandidateAuthority.parameterSection out.admitted.checked.snapshot).bodies.find?
      (fun e => e.id == out.admitted.selected.original.body) = some out.body ∧
    NativeCertifiedCorpus.ordinal b (text out.body.certificate.common.shard) = some out.index ∧
    NativeVectorAuthority.verify binding adapter.sha256 b out.body.certificate.common.domain out.index = some out.computed ∧
    out.computed.selected.original.certificate.common = out.body.certificate.common ∧
    out.computed.selected.original.voteContext = out.body.voteContext ∧ out.computed.selected.original.id = out.body.id ∧
    NativeCertifiedCorpus.ExactBody out.body.certificate.common out.computed.leaves out.computed.computation.native.numerators = true := by
  simp only [parameter,bind,Option.bind_eq_some_iff] at h
  obtain ⟨a,ha,last⟩ := h
  split at last <;> try contradiction
  rename_i action
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨e,he,i,hi,c,hc,last⟩ := last
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨ha,action,he,hi,hc,by assumption⟩

theorem parameterIdentity {adapter b r v out} (h : parameter binding adapter b r v = some out) :
    v.wire.bodyHash = out.body.id ∧ v.wire.context = out.body.voteContext := by
  have src := parameterSource binding h
  have ident := identity src.1
  have bodyId : out.body.id = out.admitted.selected.original.body := by simpa using List.find?_some src.2.2.1
  obtain ⟨e,plan,he,_,valid⟩ := NativeCandidateAuthority.parameterWitness (originalCandidate src.1).2 src.2.1
  have same : e = out.body := Option.some.inj (he.symm.trans src.2.2.1)
  subst e
  exact ⟨ident.2.2.2.2.2.2.1.trans bodyId.symm,ident.2.2.2.2.2.1.trans valid.1.symm⟩

theorem parameterValues {adapter b r v out} (h : parameter binding adapter b r v = some out) :
    out.body.certificate.common.numerators = out.computed.computation.native.numerators.map (asciiBytes ∘ toString) ∧
    out.body.certificate.common.leaves.Perm out.computed.leaves ∧
    out.computed.computation.native.numerators = out.computed.computation.out.values := by
  have exactBody := NativeCertifiedCorpus.exactBody (parameterSource binding h).2.2.2.2.2.2.2.2
  exact ⟨exactBody.2.2,exactBody.1,NativeVectorJoin.numeratorsDerived out.computed.computation⟩

theorem parameterPreimage {adapter b r v out} (h : parameter binding adapter b r v = some out) :
    NativeParameter.bodyId adapter.sha256 (NativeParameterLineage.asBody out.body) = some v.wire.bodyHash := by
  have src := parameterSource binding h
  have sectionOk := (NativeCandidateAuthority.sourceSections (NativeCandidateAuthority.policySource (selected src.1).1).1).2.2.1
  have lineage := NativeParameterSection.proposedChecked sectionOk (List.mem_of_find?_eq_some src.2.2.1)
  rw [(parameterIdentity binding h).1]
  exact (NativeParameterLineage.checkedSource lineage).identity

theorem parameterOriginalSource {adapter b r v out} (h : parameter binding adapter b r v = some out) :
    out.computed.selected.original.source = out.body.source := by
  have src := parameterSource binding h
  have sectionOk := (NativeCandidateAuthority.sourceSections (NativeCandidateAuthority.policySource (selected src.1).1).1).2.2.1
  have right := NativeParameterLineage.originalRetained
    (NativeParameterSection.proposedChecked sectionOk (List.mem_of_find?_eq_some src.2.2.1))
  have computed := NativeVectorAuthority.verifiedSource src.2.2.2.2.1
  have left := NativeVectorAuthority.originalPayload (NativeVectorAuthority.joined computed.joined).2
    (List.mem_of_find?_eq_some computed.selected)
  have eq := src.2.2.2.2.2
  rw [left,right]
  simp only [NativeParameterLineage.asBody,eq.1,eq.2.1,NativeParameterLineage.original]

structure Applied where
  admitted : NativeSelectedVote.Admitted
  computed : NativeAggregateBinding.Applied binding

def applyVote (adapter : HashAdapter codec) (b : NativeVectorContext.Bound)
    (root : NativeAggregateLineage.Edge) (profileId : Bytes) (r : RuntimeFacts) (v : Vote) :
    Option (Applied binding) := do
  let admitted ← select adapter.sha256 b r v
  if admitted.selected.original.action = 7 then
    let computed ← NativeAggregateBinding.checkApply binding adapter b root profileId admitted.selected.original.body
    some ⟨admitted,computed⟩
  else none

theorem applySource {adapter b root profileId r v out}
    (h : applyVote binding adapter b root profileId r v = some out) :
    select adapter.sha256 b r v = some out.admitted ∧ out.admitted.selected.original.action = 7 ∧
    NativeAggregateBinding.checkApply binding adapter b root profileId out.admitted.selected.original.body = some out.computed := by
  simp only [applyVote,bind,Option.bind_eq_some_iff] at h
  obtain ⟨a,ha,last⟩ := h
  split at last <;> try contradiction
  rename_i action
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨c,hc,last⟩ := last
  cases Option.some.inj last
  exact ⟨ha,action,hc⟩

theorem applyIdentity {adapter b root profileId r v out}
    (h : applyVote binding adapter b root profileId r v = some out) :
    v.wire.bodyHash = out.computed.original.id ∧
    NativeCandidateAuthority.parentContext adapter.sha256 "deltareduce.vote-context.apply.v1"
      out.computed.original.decoded.candidate.root = some v.wire.context := by
  have src := applySource binding h
  have computed := NativeAggregateBinding.applySource binding src.2.2
  have bodyId : out.computed.original.id = out.admitted.selected.original.body := by simpa using List.find?_some computed.2.1
  have sectionOk := (NativeCandidateAuthority.sourceSections (NativeCandidateAuthority.policySource (selected src.1).1).1).1
  have sameSection := Option.some.inj (sectionOk.symm.trans computed.1)
  obtain ⟨e,he,valid⟩ := NativeCandidateAuthority.applyWitness (originalCandidate src.1).2 src.2.1
  rw [sameSection] at he
  have same : e = out.computed.original := Option.some.inj (he.symm.trans computed.2.1)
  subst e
  have ident := identity src.1
  exact ⟨ident.2.2.2.2.2.2.1.trans bodyId.symm,ident.2.2.2.2.2.1 ▸ valid.2.2.2.2.2⟩

theorem applyValues {adapter b root profileId r v out}
    (h : applyVote binding adapter b root profileId r v = some out) :
    out.computed.original.decoded.candidate.modelValues = NativeApplyResult.decimalValues out.computed.checked.result.body.nextModel ∧
    out.computed.original.decoded.candidate.optimizerValues = NativeApplyResult.decimalValues out.computed.checked.result.body.nextOptimizer :=
  NativeAggregateBinding.exactOutput binding (applySource binding h).2.2

theorem applyPreimage {adapter b root profileId r v out}
    (h : applyVote binding adapter b root profileId r v = some out) :
    NativeApplyCertificate.candidateId adapter.sha256 out.computed.original.decoded.candidate = some v.wire.bodyHash := by
  have lineage := NativeAggregateBinding.originalCandidate binding (applySource binding h).2.2
  have src := NativeApplyLineage.checkedSource lineage
  have encoded := (NativeApplyLineage.decodedOriginal src.decoded).2
  rw [(applyIdentity binding h).1,src.identity]
  exact encoded

end Arithmetic
end DeltaReduce.NativeArithmeticVote
