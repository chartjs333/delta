import DeltaReduce.NativeRootCorpus
import DeltaReduce.PublicApplyBody

/-! Complete ROOT from executed original proposal/corpus checks and complete
computed scalar PARAMETER bodies. Metadata/configuration authority remains a
named boundary, not inferred from equal numbers or native opaque identifiers. -/
namespace DeltaReduce.PublicRootBody
open NativeBinding NativeInputProjection PublicState PublicArithmeticInputs PublicAuthority

section Body
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : Corpus binding} {limit : ModelLimit} {input : Projected corpus limit}
    {vocabulary : Vocabulary} {metadataTrust} {source : Metadata metadataTrust}
    (authority : PublicAuthority.Projection input vocabulary source)
    {adapter : HashAdapter codec} {policy state vote facts} {loaded : NativeEarlySource.Loaded adapter.sha256 policy state vote facts}
    {root : NativeRootSource.Root loaded.original} {config proof profile permission inputs}
    (native : NativeRootCorpus.Checked binding loaded root config proof profile permission inputs)

structure Projection where
  frame : native.image.corpus.frame = corpus.frame
  leaves : List Value
  origin : PublicApplyBody.Leaves authority native.image.corpus.entries leaves

def project : Option (Projection authority native) := do
  if frame : native.image.corpus.frame = corpus.frame then
    let leaves ← PublicApplyBody.projectLeaves authority native.image.corpus.entries
    some ⟨frame,leaves.1,leaves.2⟩
  else none

def Projection.fields (p : Projection authority native) : List (String × Value) :=
  PublicApplyBody.aggregateFields authority.apc authority.header.profile.value authority.header.coefficient.value
    authority.header.config.value authority.ec authority.isc authority.header.parent.value authority.round
    authority.header.schema.value authority.seed p.leaves

def Projection.value (p : Projection authority native) : Value := record p.fields

structure Checked where
  projection : Projection authority native
  canonical : PublicState.canonical vocabulary.models projection.value = true

def check (candidate : Value) : Option (Checked authority native) := do
  let p ← project authority native
  if valid : PublicState.canonical vocabulary.models p.value = true ∧ candidate = p.value then
    some ⟨p,valid.1⟩ else none

theorem wholeBody {candidate checked} (h : check authority native candidate = some checked) :
    candidate = checked.projection.value := by
  unfold check at h
  cases hp : project authority native with
  | none => simp [hp] at h
  | some p =>
    simp only [hp,Bind.bind,Option.bind] at h
    split at h
    · rename_i valid; cases h; exact valid.2
    · contradiction

variable (p : Projection authority native)

theorem entireFieldInventory : p.fields.map Prod.fst = PublicApplyBody.aggregateFieldNames := rfl

theorem nativeLeafCount : p.leaves.length = root.original.shards.length :=
  (PublicApplyBody.leavesRetainCount authority p.origin).trans
    (NativeRootCorpus.completeOrder binding loaded root native).1

theorem nativeLeafAt {index : Nat} {value} (found : p.leaves[index]? = some value) :
    ∃ entry, native.image.corpus.entries[index]? = some entry ∧
      ∃ projected : PublicParameterBody.Projection (corpus := corpus) (limit := limit)
        (vocabulary := vocabulary) entry.result,
        value = projected.value authority ∧
        ∃ original leaf, root.original.shards[index]? = some original ∧
          NativeCertifiedCorpus.checkLeaf binding native.image.vector entry original = some leaf := by
  obtain ⟨entry,position,projected,body⟩ := PublicApplyBody.everyLeafComputed authority p.origin index value found
  exact ⟨entry,position,projected,body,NativeRootCorpus.originalPosition binding loaded root native position⟩

theorem completeParents : readField p.value "apc" = some authority.apc ∧
    readField p.value "ec" = some authority.ec ∧ readField p.value "isc" = some authority.isc ∧
    readField p.value "seed" = some authority.seed := ⟨rfl,rfl,rfl,rfl⟩

theorem originalScalarAt {index : Nat} {value} (found : p.leaves[index]? = some value) :
    ∃ original number, root.original.shards[index]? = some original ∧
      original.certificate.common.numerators = [asciiBytes (toString number)] ∧
      readField value "value" = some (.integer number) := by
  obtain ⟨entry,_,projected,body,original,leaf,position,computed⟩ :=
    nativeLeafAt authority native p found
  have same := congrArg ParameterBody.numerators (NativeCertifiedCorpus.leafBody binding computed).1
  have numbers : leaf.computation.native.numerators = [projected.math.scalar.value] :=
    same.trans (PublicParameterBody.narrowPreservesNativeNumerator projected.math)
  have spelling := (NativeCertifiedCorpus.exactBody
    (NativeCertifiedCorpus.leafChecked binding computed).2.2.2.2).2.2
  refine ⟨original,projected.math.scalar.value,position,?_,?_⟩
  · simpa only [numbers,List.map_cons,List.map_nil,Function.comp_apply] using spelling
  · rw [body]; rfl

theorem originalVoteIdentity : loaded.original.vote.wire.bodyHash = root.original.id ∧
    NativeCandidateAuthority.parentContext adapter.sha256 "deltareduce.vote-context.root.v1"
      root.original.certificate.common.plan = some loaded.original.vote.wire.context :=
  NativeRootSource.identity loaded root

theorem leavesKeepWholeAuthority : ∀ value ∈ p.leaves,
    readField value "authority" = some authority.value ∧ readField value "apc" = some authority.apc :=
  PublicApplyBody.leavesShareEntireAuthority authority p.origin

theorem leafSetPreservesOrderWitness :
    readField p.value "leaves" = some (setValue p.leaves) ∧
    readField p.value "canonicalRoot" = some (setValue p.leaves) ∧
    (∃ v, setValue p.leaves = .set v ∧ (PublicAuthority.valuesList v).Perm p.leaves) := by
  exact ⟨rfl,rfl,PublicAuthority.setRetainsAllValues p.leaves⟩

theorem missingLeavesRejected (candidate : Value) (missing : readField candidate "leaves" = none) :
    check authority native candidate = none := by
  cases h : check authority native candidate with
  | none => rfl
  | some checked =>
    have same := wholeBody authority native h
    rw [same,(leafSetPreservesOrderWitness authority native checked.projection).1] at missing
    contradiction

end Body
end DeltaReduce.PublicRootBody
