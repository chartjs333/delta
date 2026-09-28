import DeltaReduce.NativeRootParents
import DeltaReduce.PublicParentNames
import DeltaReduce.PublicRootBody

/-! Complete structured ROOT parents are derived from original lineage and
checked primitive metadata agreement. Authentication of either metadata source
and equality to the live public configuration remain external obligations. -/
namespace DeltaReduce.PublicRootParents
open NativeBinding NativeInputProjection PublicState PublicArithmeticInputs

section Parents
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : Corpus binding} {limit : ModelLimit} {input : Projected corpus limit}
    {vocabulary : Vocabulary} {metadataTrust} {source : PublicAuthority.Metadata metadataTrust}
    (authority : PublicAuthority.Projection input vocabulary source)
    {adapter : HashAdapter codec} {policy state vote facts}
    {loaded : NativeEarlySource.Loaded adapter.sha256 policy state vote facts}
    {root : NativeRootSource.Root loaded.original} {config proof profile permission inputs}
    (native : NativeRootCorpus.Checked binding loaded root config proof profile permission inputs)
    {earlyTrust planTrust} (original : PublicPlanningBody.Metadata earlyTrust planTrust)

def PrimitiveChecks (p : PublicPlanningBody.ApcBody original loaded.original root.original.plan) : Prop :=
  authority.header.height.name = p.ec.parent.header.height.text ∧
  authority.header.epoch.name = p.ec.parent.header.epoch.text ∧
  authority.header.config.name = p.ec.parent.header.config.text ∧
  authority.header.policy = p.ec.parent.policy ∧
  authority.header.seed.name = p.ec.seed.text ∧
  authority.header.norm.name = p.ec.norm.text ∧
  authority.header.coefficient.name = p.coefficient.text ∧
  PublicParentNames.entriesAgree source binding.authority.isc vocabulary
    corpus.frame.commitments p.ec.parent.entries = true ∧
  PublicParentNames.membersAgree vocabulary corpus.frame.eligible p.ec.members = true

instance (p) : Decidable (PrimitiveChecks authority original (root := root) p) := by
  unfold PrimitiveChecks; infer_instance

structure Checked (allInputs : List NativeAvailableQ.Input) (candidate : Value) where
  full : NativeRootParents.Complete binding loaded root native allInputs
  body : PublicRootBody.Checked authority native
  bodyComputed : PublicRootBody.check authority native candidate = some body
  parents : PublicPlanningBody.ApcBody original loaded.original root.original.plan
  parentComputed : PublicPlanningBody.loadApcBody original loaded.original root.original.plan = some parents
  primitives : PrimitiveChecks authority original parents
  separated : parents.ec.Separated

def check (allInputs : List NativeAvailableQ.Input) (candidate : Value) :
    Option (Checked authority native original allInputs candidate) := do
  let full ← NativeRootParents.complete binding loaded root native allInputs
  match bodyComputed : PublicRootBody.check authority native candidate with
  | none => none
  | some body =>
    match parentComputed : PublicPlanningBody.loadApcBody original loaded.original root.original.plan with
    | none => none
    | some parents =>
      if valid : PrimitiveChecks authority original parents ∧ parents.ec.Separated then
        some ⟨full,body,bodyComputed,parents,parentComputed,valid.1,valid.2⟩ else none

variable {allInputs candidate} (checked : Checked authority native original allInputs candidate)

theorem roundIdentity : authority.round = checked.parents.ec.parent.header.round := by
  simp only [PublicAuthority.Projection.round,PublicEarlyBody.Header.round,
    PublicAuthority.Atom.value,PublicEarlyBody.Name.value,checked.primitives.1,checked.primitives.2.1]

theorem fullEntryIdentity : authority.entryValues =
    checked.parents.ec.parent.entries.map PublicEarlyBody.Entry.value :=
  PublicParentNames.completeEntries authority.entryOrigin _ checked.primitives.2.2.2.2.2.2.2.1

theorem fullMemberIdentity : authority.eligibleNames.map Value.model =
    checked.parents.ec.members.map PublicPlanningBody.Member.value :=
  PublicParentNames.completeMembers authority.eligible _ checked.primitives.2.2.2.2.2.2.2.2

theorem iscIdentity : authority.isc = checked.parents.ec.parent.value := by
  simp only [PublicAuthority.Projection.isc,PublicPlanningBody.IscBody.value,
    roundIdentity authority native original checked,fullEntryIdentity authority native original checked,
    PublicAuthority.Atom.value,PublicEarlyBody.Name.value,checked.primitives.2.2.1,checked.primitives.2.2.2.1]

theorem seedIdentity : authority.seed = checked.parents.ec.seedValue := by
  simp only [PublicAuthority.Projection.seed,PublicPlanningBody.EcBody.seedValue,
    iscIdentity authority native original checked,PublicAuthority.Atom.value,
    PublicEarlyBody.Name.value,PublicPlanningBody.Name.value,checked.primitives.2.1,checked.primitives.2.2.2.2.1]

theorem ecIdentity : authority.ec = checked.parents.ec.value := by
  simp only [PublicAuthority.Projection.ec,PublicPlanningBody.EcBody.value,
    iscIdentity authority native original checked,seedIdentity authority native original checked,
    fullMemberIdentity authority native original checked,PublicAuthority.Atom.value,
    PublicPlanningBody.Name.value,checked.primitives.2.2.2.2.2.1]

theorem apcIdentity : authority.apc = checked.parents.value := by
  simp only [PublicAuthority.Projection.apc,PublicPlanningBody.ApcBody.value,
    iscIdentity authority native original checked,seedIdentity authority native original checked,
    ecIdentity authority native original checked,fullMemberIdentity authority native original checked,
    checked.parents.sameMembers,PublicAuthority.Atom.value,PublicPlanningBody.Name.value,
    checked.primitives.2.2.2.2.2.2.1]

theorem originalEntrySources : checked.parents.ec.parent.entries.map PublicEarlyBody.Entry.original =
    root.original.parent.certificate.body.tuples := by
  rw [PublicPlanningBody.completeOriginalIsc checked.parents.ec.parent,
    ← NativeRootParents.sameEcIsc binding loaded root native,
    ← NativeRootParents.sameIsc binding loaded root native]

include native in
theorem originalParentChecksDerived : PublicPlanningBody.SamePlanParents root.original.plan := by
  have isc := NativeRootParents.sameEcIsc binding loaded root native
  have seed := NativeRootParents.sameEcSeed binding loaded root native
  exact ⟨congrArg NativeIscCertificate.Checked.qcId isc,
    congrArg NativeIscCertificate.Checked.certificate isc,
    congrArg NativeSeedTranscript.Checked.id seed,congrArg NativeSeedTranscript.Checked.transcript seed⟩

theorem sameFullIscOrder : checked.full.image.rows.map (fun r => r.source.member.input) =
    checked.parents.ec.parent.entries.map PublicEarlyBody.Entry.original := by
  rw [NativeRootParents.everyOriginalTuple binding loaded root native checked.full,
    originalEntrySources authority native original checked]

theorem completeBodyParents : readField candidate "apc" = some checked.parents.value ∧
    readField candidate "ec" = some checked.parents.ec.value ∧
    readField candidate "isc" = some checked.parents.ec.parent.value ∧
    readField candidate "seed" = some checked.parents.ec.seedValue := by
  simp only [PublicRootBody.wholeBody authority native checked.bodyComputed]
  have full := PublicRootBody.completeParents authority native checked.body.projection
  rw [apcIdentity authority native original checked,ecIdentity authority native original checked,
    iscIdentity authority native original checked,seedIdentity authority native original checked] at full
  exact full

theorem actualCommitmentAt {index : Nat} {row}
    (position : checked.full.image.rows[index]? = some row) :
    corpus.frame.commitments[index]? = some (NativeIscProjection.commitment row) := by
  rw [← checked.body.projection.frame]
  exact NativeRootParents.originalCommitmentAt binding loaded root native checked.full position

theorem missingOriginalParentRejects (allInputs candidate)
    (missing : PublicPlanningBody.loadApcBody original loaded.original root.original.plan = none) :
    check authority native original allInputs candidate = none := by
  unfold check
  cases h : NativeRootParents.complete binding loaded root native allInputs with
  | none => simp only [bind,Option.bind]
  | some full =>
    simp only [bind,Option.bind]
    split <;> try rfl
    split
    · rfl
    · rename_i p hp; rw [missing] at hp; contradiction

end Parents
end DeltaReduce.PublicRootParents
