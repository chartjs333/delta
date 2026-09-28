import FamilyApply
import DeltaReduce.NativeRootParents
import DeltaReduce.PublicParentNames

/- The ROOT constructor is needed before APPLY exists. It consumes the actual
selected native ROOT corpus, with every original finalized vector leaf, and does
not require later conversion/optimizer success. This is part of R2 body/source
composition, not a new protocol action or proof obligation. -/
namespace DeltaReduce.FamilyRoot
open NativeBinding NativeInputProjection PublicState PublicArithmeticInputs
open PublicAuthority (record)

section Root
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : FamilyInputs.Corpus binding} {choice : FamilyInputs.Choice corpus.frame}
    {limit : Int} {input : FamilyInputs.Projected corpus choice limit}
    {vocabulary : Vocabulary} {metadataTrust} {source : PublicAuthority.Metadata metadataTrust}
    (authority : FamilyAuthority.Projection input vocabulary source) (resultBound : Int)
    {adapter : HashAdapter codec} {policy state vote facts}
    {loaded : NativeEarlySource.Loaded adapter.sha256 policy state vote facts}
    {root : NativeRootSource.Root loaded.original} {config proof profile permission inputs}
    (native : NativeRootCorpus.Checked binding loaded root config proof profile permission inputs)

structure Projection where
  frame : native.image.corpus.frame = corpus.frame
  leaves : List Value
  origin : FamilyApply.Leaves authority resultBound native.image.corpus.entries leaves

def project : Option (Projection authority resultBound native) := do
  if frame : native.image.corpus.frame = corpus.frame then
    let leaves ← FamilyApply.projectLeaves authority resultBound native.image.corpus.entries
    some ⟨frame,leaves.1,leaves.2⟩
  else none

def Projection.fields (p : Projection authority resultBound native) : List (String × Value) :=
  PublicApplyBody.aggregateFields authority.apc authority.header.profile.value authority.header.coefficient.value
    authority.header.config.value authority.ec authority.isc authority.header.parent.value authority.round
    authority.header.schema.value authority.seed p.leaves

def Projection.value (p : Projection authority resultBound native) : Value := record p.fields

structure Checked where
  projection : Projection authority resultBound native
  canonical : PublicState.canonical vocabulary.models projection.value = true

def check (candidate : Value) : Option (Checked authority resultBound native) := do
  let p ← project authority resultBound native
  if valid : PublicState.canonical vocabulary.models p.value = true ∧ candidate = p.value then
    some ⟨p,valid.1⟩ else none

theorem wholeBody {candidate checked} (h : check authority resultBound native candidate = some checked) :
    candidate = checked.projection.value := by
  unfold check at h
  cases hp : project authority resultBound native with
  | none => simp [hp] at h
  | some p =>
    simp only [hp,Bind.bind,Option.bind] at h
    split at h
    · rename_i valid; cases h; exact valid.2
    · contradiction

variable (p : Projection authority resultBound native)

theorem completeFields : p.fields.map Prod.fst = PublicApplyBody.aggregateFieldNames := rfl

theorem constructedCanonical
    (auth : PublicState.canonical vocabulary.models authority.value = true)
    (names : ∀ n ∈ vocabulary.domains ++ vocabulary.shards, PublicState.canonical vocabulary.models (.model n) = true)
    (uniqueBytes : (p.leaves.map PublicState.encode).Nodup) :
    PublicState.canonical vocabulary.models p.value = true :=
  FamilyApply.aggregateConstructedCanonical authority resultBound p.origin auth names uniqueBytes

theorem nativeLeafCount : p.leaves.length = root.original.shards.length :=
  (FamilyApply.leavesRetainCount authority resultBound p.origin).trans
    (NativeRootCorpus.completeOrder binding loaded root native).1

theorem nativeLeafAt {index : Nat} {value} (found : p.leaves[index]? = some value) :
    ∃ entry, native.image.corpus.entries[index]? = some entry ∧
      ∃ projected : FamilyParameter.Projection (corpus := corpus) (choice := choice) (limit := limit)
        (vocabulary := vocabulary) resultBound entry.result,
        value = projected.body authority ∧
        ∃ original leaf, root.original.shards[index]? = some original ∧
          NativeCertifiedCorpus.checkLeaf binding native.image.vector entry original = some leaf := by
  obtain ⟨entry,position,projected,body⟩ := FamilyApply.everyLeafComputed authority resultBound p.origin index value found
  exact ⟨entry,position,projected,body,NativeRootCorpus.originalPosition binding loaded root native position⟩

theorem originalVectorAt {index : Nat} {value} (found : p.leaves[index]? = some value) :
    ∃ original entry, root.original.shards[index]? = some original ∧
      native.image.corpus.entries[index]? = some entry ∧
      original.certificate.common.numerators = NativeApplyResult.decimalValues entry.result.numerators ∧
      ∃ coordinate : Nat, ∃ number, entry.result.numerators[coordinate]? = some number ∧
        readField value "value" = some (.integer number) := by
  obtain ⟨entry,position,projected,body,original,leaf,atOriginal,computed⟩ :=
    nativeLeafAt authority resultBound native p found
  have same := congrArg ParameterBody.numerators (NativeCertifiedCorpus.leafBody binding computed).1
  change leaf.computation.native.numerators = entry.result.numerators at same
  have spelling := (NativeCertifiedCorpus.exactBody
    (NativeCertifiedCorpus.leafChecked binding computed).2.2.2.2).2.2
  refine ⟨original,entry,atOriginal,position,?_,_,projected.value,projected.coordinate,?_⟩
  · simpa only [same,NativeApplyResult.decimalValues] using spelling
  · rw [body]; rfl

theorem allParents : readField p.value "apc" = some authority.apc ∧
    readField p.value "ec" = some authority.ec ∧ readField p.value "isc" = some authority.isc ∧
    readField p.value "seed" = some authority.seed := ⟨rfl,rfl,rfl,rfl⟩

theorem originalVoteIdentity : loaded.original.vote.wire.bodyHash = root.original.id ∧
    NativeCandidateAuthority.parentContext adapter.sha256 "deltareduce.vote-context.root.v1"
      root.original.certificate.common.plan = some loaded.original.vote.wire.context :=
  NativeRootSource.identity loaded root

theorem constructorTotal
    {input : FamilyInputs.Projected corpus choice (accumulatorHi binding.profile)}
    (authority : FamilyAuthority.Projection input vocabulary source) :
    ∃ p, project authority (accumulatorHi binding.profile+1) native = some p := by
  have frame : native.image.corpus.frame = corpus.frame := by
    exact congrArg Subtype.val (Option.some.inj
      ((NativeVectorDerivation.frameComplete native.image.corpus.origin).symm.trans
        (NativeVectorDerivation.frameComplete corpus.origin)))
  obtain ⟨leaves,h⟩ := FamilyApply.allLeavesConstructible authority native.image.corpus.entries
  exact ⟨⟨frame,leaves.1,leaves.2⟩,by simp only [project,dif_pos frame,h,bind,Option.bind]⟩

/- The two independently sourced parent constructions must agree on primitive
metadata and each original commitment/member. Equality of their whole public
APC body is a conclusion, never an input. -/
variable {earlyTrust planTrust} (original : PublicPlanningBody.Metadata earlyTrust planTrust)

def PrimitiveChecks (parents : PublicPlanningBody.ApcBody original loaded.original root.original.plan) : Prop :=
  authority.header.height.name = parents.ec.parent.header.height.text ∧
  authority.header.epoch.name = parents.ec.parent.header.epoch.text ∧
  authority.header.config.name = parents.ec.parent.header.config.text ∧
  authority.header.policy = parents.ec.parent.policy ∧
  authority.header.seed.name = parents.ec.seed.text ∧
  authority.header.norm.name = parents.ec.norm.text ∧
  authority.header.coefficient.name = parents.coefficient.text ∧
  PublicParentNames.entriesAgree source binding.authority.isc vocabulary
    corpus.frame.commitments parents.ec.parent.entries = true ∧
  PublicParentNames.membersAgree vocabulary corpus.frame.eligible parents.ec.members = true
instance (parents) : Decidable (PrimitiveChecks authority original (root := root) parents) := by
  unfold PrimitiveChecks; infer_instance

structure Joined (allInputs : List NativeAvailableQ.Input) (candidate : Value) where
  full : NativeRootParents.Complete binding loaded root native allInputs
  body : Checked authority resultBound native
  computed : check authority resultBound native candidate = some body
  parents : PublicPlanningBody.ApcBody original loaded.original root.original.plan
  parentsComputed : PublicPlanningBody.loadApcBody original loaded.original root.original.plan = some parents
  primitives : PrimitiveChecks authority original parents
  separated : parents.ec.Separated

def join (allInputs : List NativeAvailableQ.Input) (candidate : Value) :
    Option (Joined authority resultBound native original allInputs candidate) := do
  let full ← NativeRootParents.complete binding loaded root native allInputs
  match computed : check authority resultBound native candidate with
  | none => none
  | some body =>
    match parentsComputed : PublicPlanningBody.loadApcBody original loaded.original root.original.plan with
    | none => none
    | some parents =>
      if valid : PrimitiveChecks authority original parents ∧ parents.ec.Separated then
        some ⟨full,body,computed,parents,parentsComputed,valid.1,valid.2⟩ else none

variable {allInputs candidate} (joined : Joined authority resultBound native original allInputs candidate)

theorem roundIdentity : authority.round = joined.parents.ec.parent.header.round := by
  simp only [FamilyAuthority.Projection.round,PublicEarlyBody.Header.round,
    PublicAuthority.Atom.value,PublicEarlyBody.Name.value,joined.primitives.1,joined.primitives.2.1]

theorem entryIdentity : authority.entryValues = joined.parents.ec.parent.entries.map PublicEarlyBody.Entry.value :=
  PublicParentNames.completeEntries authority.entryOrigin _ joined.primitives.2.2.2.2.2.2.2.1

theorem memberIdentity : authority.eligibleNames.map Value.model = joined.parents.ec.members.map PublicPlanningBody.Member.value :=
  PublicParentNames.completeMembers authority.eligible _ joined.primitives.2.2.2.2.2.2.2.2

theorem iscIdentity : authority.isc = joined.parents.ec.parent.value := by
  simp only [FamilyAuthority.Projection.isc,PublicPlanningBody.IscBody.value,
    roundIdentity authority resultBound native original joined,entryIdentity authority resultBound native original joined,
    PublicAuthority.Atom.value,PublicEarlyBody.Name.value,joined.primitives.2.2.1,joined.primitives.2.2.2.1]

theorem seedIdentity : authority.seed = joined.parents.ec.seedValue := by
  simp only [FamilyAuthority.Projection.seed,PublicPlanningBody.EcBody.seedValue,
    iscIdentity authority resultBound native original joined,PublicAuthority.Atom.value,
    PublicEarlyBody.Name.value,PublicPlanningBody.Name.value,joined.primitives.2.1,joined.primitives.2.2.2.2.1]

theorem ecIdentity : authority.ec = joined.parents.ec.value := by
  simp only [FamilyAuthority.Projection.ec,PublicPlanningBody.EcBody.value,
    iscIdentity authority resultBound native original joined,seedIdentity authority resultBound native original joined,
    memberIdentity authority resultBound native original joined,PublicAuthority.Atom.value,
    PublicPlanningBody.Name.value,joined.primitives.2.2.2.2.2.1]

theorem apcIdentity : authority.apc = joined.parents.value := by
  simp only [FamilyAuthority.Projection.apc,PublicPlanningBody.ApcBody.value,
    iscIdentity authority resultBound native original joined,seedIdentity authority resultBound native original joined,
    ecIdentity authority resultBound native original joined,memberIdentity authority resultBound native original joined,
    joined.parents.sameMembers,PublicAuthority.Atom.value,PublicPlanningBody.Name.value,
    joined.primitives.2.2.2.2.2.2.1]

theorem sourceParentContext : readField candidate "apc" = some joined.parents.value ∧
    readField candidate "ec" = some joined.parents.ec.value ∧
    readField candidate "isc" = some joined.parents.ec.parent.value ∧
    readField candidate "seed" = some joined.parents.ec.seedValue := by
  simp only [wholeBody authority resultBound native joined.computed]
  have parents := allParents authority resultBound native joined.body.projection
  rw [apcIdentity authority resultBound native original joined,ecIdentity authority resultBound native original joined,
    iscIdentity authority resultBound native original joined,seedIdentity authority resultBound native original joined] at parents
  exact parents

end Root
end DeltaReduce.FamilyRoot
