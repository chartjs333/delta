import DeltaReduce.PublicRootParents

/-! Entire ROOT vote from computed source-bound body/parents. Primitive actor
metadata requires independent authentication; no live phase admission is proved. -/
namespace DeltaReduce.PublicRootEnvelope
open NativeBinding NativeInputProjection PublicState PublicArithmeticInputs

def envelope (actor apc body : Value) : Vote := ⟨actor,.text "AGGREGATE_ROOT",apc,body⟩

section Envelope
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : Corpus binding} {limit : ModelLimit} {input : Projected corpus limit}
    {vocabulary : Vocabulary} {metadataTrust} {source : PublicAuthority.Metadata metadataTrust}
    (authority : PublicAuthority.Projection input vocabulary source)
    {adapter : HashAdapter codec} {policy state vote facts}
    {loaded : NativeEarlySource.Loaded adapter.sha256 policy state vote facts}
    {root : NativeRootSource.Root loaded.original} {config proof profile permission inputs}
    (native : NativeRootCorpus.Checked binding loaded root config proof profile permission inputs)
    {earlyTrust planTrust} (original : PublicPlanningBody.Metadata earlyTrust planTrust)


def value {allInputs body} (p : PublicRootParents.Checked authority native original allInputs body) : Vote :=
  envelope p.parents.ec.parent.header.actor.value p.parents.value p.body.projection.value

structure Checked (allInputs : List NativeAvailableQ.Input) (candidate : Vote) where
  parents : PublicRootParents.Checked authority native original allInputs candidate.body
  entire : candidate = value authority native original parents
  canonical : PublicState.canonical vocabulary.models (.function (voteEntries candidate)) = true

def check (allInputs : List NativeAvailableQ.Input) (candidate : Vote) :
    Option (Checked authority native original allInputs candidate) := do
  let p ← PublicRootParents.check authority native original allInputs candidate.body
  if valid : candidate = value authority native original p ∧
      PublicState.canonical vocabulary.models (.function (voteEntries candidate)) = true then
    some ⟨p,valid.1,valid.2⟩ else none

variable {allInputs candidate} (h : Checked authority native original allInputs candidate)

theorem entireVote : candidate = value authority native original h.parents := h.entire

theorem fields : candidate.actor = h.parents.parents.ec.parent.header.actor.value ∧
    candidate.kind = .text "AGGREGATE_ROOT" ∧ candidate.context = h.parents.parents.value ∧
    candidate.body = h.parents.body.projection.value := by
  simp only [h.entire,value,envelope,and_self]

include h in
theorem fullApcContext : candidate.context = authority.apc :=
  (fields authority native original h).2.2.1.trans (PublicRootParents.apcIdentity authority native original h.parents).symm

include h in
theorem contextFromBody : readField candidate.body "apc" = some candidate.context := by
  rw [(fields authority native original h).2.2.1]
  exact (PublicRootParents.completeBodyParents authority native original h.parents).1

include h in
theorem arithmeticContextUnsupported : PublicState.expectedContext candidate = none := by
  simp only [PublicState.expectedContext,(fields authority native original h).2.1]
  rfl

theorem actorSource : original.early.atom (.actor loaded.original.vote.wire.validator loaded.original.vote.wire.epoch) =
    some h.parents.parents.ec.parent.header.actor.text := h.parents.parents.ec.parent.header.actor.selected

theorem nativeIdentity : loaded.original.admitted.selected.original.action = 6 ∧
    loaded.original.vote.wire.bodyHash = root.original.id ∧
    NativeCandidateAuthority.parentContext adapter.sha256 "deltareduce.vote-context.root.v1"
      root.original.certificate.common.plan = some loaded.original.vote.wire.context :=
  ⟨root.kind,NativeRootSource.identity loaded root⟩

include h in
theorem wholeCanonical : PublicState.canonical vocabulary.models (.function (voteEntries candidate)) = true := h.canonical

theorem wrongKindRejects (allInputs candidate) (bad : candidate.kind ≠ .text "AGGREGATE_ROOT") :
    check authority native original allInputs candidate = none := by
  cases found : check authority native original allInputs candidate with
  | none => rfl
  | some checked =>
    exact False.elim (bad (fields authority native original checked).2.1)

end Envelope
end DeltaReduce.PublicRootEnvelope
