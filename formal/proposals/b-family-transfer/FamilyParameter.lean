import FamilyAuthority
import DeltaReduce.PublicParameterBody
import DeltaReduce.NativeVectorDerivation

/-! Complete PARAMETER bodies for a selected view of original vector shards.
The original native body and all rows are retained. Public arithmetic is checked
at explicit separate arithmetic/result bounds; total domain coverage is a
different R2 obligation, not assumed by this constructor. -/
namespace DeltaReduce.FamilyParameter
open NativeBinding NativeInputProjection PublicState PublicArithmeticInputs PublicAuthority

section Construction
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : FamilyInputs.Corpus binding} {choice : FamilyInputs.Choice corpus.frame}
    {limit : Int} {input : FamilyInputs.Projected corpus choice limit}
    {vocabulary : Vocabulary} {metadataTrust} {source : Metadata metadataTrust}
    (authority : FamilyAuthority.Projection input vocabulary source)
    (resultBound : Int) {domain shard : String} (native : DerivedParameter binding domain shard)

structure Projection where
  frame : native.frame = corpus.frame
  entry : FamilyInputs.Entry codec store binding.authority corpus.frame
  selected : corpus.entries.find? (fun e => e.assignment == native.assignment) = some entry
  assignment : entry.assignment = native.assignment
  rows : entry.block.rows = native.rows
  partition : corpus.frame.shards[entry.block.slot.val] = native.partition
  value : Int
  coordinate : native.numerators[(choice entry.block.slot).val]? = some value
  arithmetic : ParameterKernel.checkedParameter (-limit-1) limit minInput maxInput
    native.assignment.denominator native.partition.length native.rows = some native.numerators
  resultGuard : 0 ≤ resultBound ∧ Fits (-resultBound) resultBound value
  domainName : String
  domainAlias : vocabulary.domain domain = some domainName
  domainConfigured : domainName ∈ vocabulary.domains
  shardName : String
  shardAlias : vocabulary.shard shard = some shardName
  shardConfigured : shardName ∈ vocabulary.shards

def project : Option (Projection (corpus := corpus) (choice := choice) (limit := limit)
    (vocabulary := vocabulary) resultBound native) := do
  match found : corpus.entries.find? (fun e => e.assignment == native.assignment),
      hd : vocabulary.domain domain, hs : vocabulary.shard shard with
  | some entry, some domainName, some shardName =>
    if checked : native.frame = corpus.frame ∧ entry.assignment = native.assignment ∧
        entry.block.rows = native.rows ∧ corpus.frame.shards[entry.block.slot.val] = native.partition ∧
        domainName ∈ vocabulary.domains ∧ shardName ∈ vocabulary.shards then
      match atValue : native.numerators[(choice entry.block.slot).val]?,
          computed : ParameterKernel.checkedParameter (-limit-1) limit minInput maxInput
            native.assignment.denominator native.partition.length native.rows with
      | some value, some numerators =>
        if guard : 0 ≤ resultBound ∧ Fits (-resultBound) resultBound value then
          have same : numerators = native.numerators := PublicParameterBody.checkedWidthsAgree computed native.computed
          some ⟨checked.1,entry,found,checked.2.1,checked.2.2.1,checked.2.2.2.1,value,atValue,
            by simpa only [same] using computed,guard,domainName,hd,checked.2.2.2.2.1,
            shardName,hs,checked.2.2.2.2.2⟩
        else none
      | _,_ => none
    else none
  | _,_,_ => none

def Projection.fields (p : Projection (corpus := corpus) (choice := choice) (limit := limit)
    (vocabulary := vocabulary) resultBound native) : List (String × Value) :=
  PublicParameterBody.fields authority.apc authority.header.profile.value authority.value
    authority.header.coefficient.value authority.header.config.value (.model p.domainName)
    authority.ec authority.isc authority.header.parent.value authority.round authority.header.schema.value
    authority.seed (.model p.shardName) p.value

def Projection.body (p : Projection (corpus := corpus) (choice := choice) (limit := limit)
    (vocabulary := vocabulary) resultBound native) : Value := record (p.fields authority)

structure Checked where
  projection : Projection (corpus := corpus) (choice := choice) (limit := limit)
    (vocabulary := vocabulary) resultBound native
  canonical : PublicState.canonical vocabulary.models (projection.body authority) = true

def check (candidate : Value) : Option (Checked authority resultBound native) := do
  let p ← project (corpus := corpus) (choice := choice) (limit := limit) (vocabulary := vocabulary) resultBound native
  if valid : PublicState.canonical vocabulary.models (p.body authority) = true ∧ candidate = p.body authority then
    some ⟨p,valid.1⟩
  else none

theorem computedWholeBody {candidate checked} (accepted : check authority resultBound native candidate = some checked) :
    candidate = checked.projection.body authority := by
  unfold check at accepted
  cases hp : project (corpus := corpus) (choice := choice) (limit := limit) (vocabulary := vocabulary) resultBound native with
  | none => simp [hp] at accepted
  | some p =>
    simp only [hp,bind,Option.bind] at accepted
    split at accepted
    · rename_i valid; cases accepted; exact valid.2
    · contradiction

variable (p : Projection (corpus := corpus) (choice := choice) (limit := limit) (vocabulary := vocabulary) resultBound native)

theorem allFields : (p.fields authority).map Prod.fst = PublicParameterBody.parameterFieldNames := rfl
theorem entireAuthority : readField (p.body authority) "authority" = some authority.value := rfl
theorem entireParents : readField (p.body authority) "apc" = some authority.apc ∧
    readField (p.body authority) "ec" = some authority.ec ∧ readField (p.body authority) "isc" = some authority.isc ∧
    readField (p.body authority) "seed" = some authority.seed := ⟨rfl,rfl,rfl,rfl⟩
theorem sourceBeforeSelection : native.frame = corpus.frame ∧ p.entry.assignment = native.assignment ∧
    p.entry.block.rows = native.rows ∧ corpus.frame.shards[p.entry.block.slot.val] = native.partition :=
  ⟨p.frame,p.assignment,p.rows,p.partition⟩
theorem exactNativeCoordinate : native.body.numerators[(choice p.entry.block.slot).val]? = some p.value := p.coordinate
theorem publicCoordinateChecked :
    ParameterKernel.checkedParameter (-limit-1) limit minInput maxInput native.assignment.denominator 1
      (native.rows.map (VectorShardRepresentation.rowAt (choice p.entry.block.slot).val)) = some [p.value] := by
  have inside : (choice p.entry.block.slot).val < native.partition.length := by
    rw [← p.partition]; exact (choice p.entry.block.slot).isLt
  obtain ⟨value,hv,computed⟩ := VectorShardRepresentation.scalarParameterIsCoordinate p.arithmetic _ inside
  have same := Option.some.inj (hv.symm.trans p.coordinate)
  simpa only [same] using computed

theorem samePublicInputsComputeBody :
    ∃ selected, FamilyInputs.entryInput p.entry choice = some selected ∧
      ParameterKernel.checkedParameter (-limit-1) limit minInput maxInput
        selected.denominator 1 (FamilyInputs.scalarRows selected.cells) = some [p.value] := by
  obtain ⟨selected,computed⟩ := FamilyInputs.entryInputComplete p.entry choice
  have src := FamilyInputs.entryInputSource computed
  have rows := FamilyInputs.selectedRowsExact src.2.2.2.2
  rw [p.rows] at rows
  refine ⟨selected,computed,?_⟩
  rw [src.2.2.1,p.assignment,rows]
  exact publicCoordinateChecked resultBound native p
theorem actualInputImageComputesBody :
    ∃ d ∈ input.domains, d.domain = native.assignment.domain ∧
      d.denominator = native.assignment.denominator ∧
      ((FamilyInputs.imageRows (FamilyInputs.image input) d.domain p.entry.block.slot.val).bind
        (ParameterKernel.checkedParameter (-limit-1) limit minInput maxInput d.denominator 1)) =
          some [p.value] := by
  obtain ⟨selected,computed,arithmetic⟩ := samePublicInputsComputeBody resultBound native p
  have src := FamilyInputs.entryInputSource computed
  have member := FamilyInputs.selectedInputIsExposed input p.entry
    (List.mem_of_find?_eq_some p.selected) computed
  have shardAt : (shardIds corpus.frame)[p.entry.block.slot.val]? = some selected.shard := by
    simp only [shardIds,List.getElem?_map,List.getElem?_eq_getElem p.entry.block.slot.isLt,
      Option.map_some,p.entry.block.key,src.2.1]
  have rows := FamilyInputs.publicRowsAreSelectedNativeRows input member _ shardAt
  have domainMember : selected.domain ∈ NativeBinding.domains binding.profile := by
    have frame := corpus.valid
    simp only [ParameterFrameValid] at frame
    obtain ⟨_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,keys,_⟩ := frame
    have planned : p.entry.assignment ∈ corpus.frame.plan.assignments := by
      rw [← FamilyInputs.entryAssignments corpus.bound]
      exact List.mem_map.mpr ⟨p.entry,List.mem_of_find?_eq_some p.selected,rfl⟩
    have key : (selected.domain,p.entry.assignment.shard) ∈ expectedKeys corpus.frame binding.profile := by
      rw [← keys,src.1]
      exact List.mem_map.mpr ⟨p.entry.assignment,planned,rfl⟩
    obtain ⟨d,hd,inmap⟩ := List.mem_flatMap.mp key
    obtain ⟨s,hs,equal⟩ := List.mem_map.mp inmap
    have domainEqual : d = selected.domain := congrArg Prod.fst equal
    simpa only [domainEqual] using hd
  obtain ⟨d,inDomains,derived⟩ := FamilyInputs.collectInputHasOutput input.domainsLoaded domainMember
  have ds := derivedDomainSource derived
  have denominator := domainDenominatorAgreesWithEveryShard ds.2.1 member rfl
  refine ⟨d,inDomains,ds.1.trans (src.1.trans (congrArg Assignment.domain p.assignment)),?_,?_⟩
  · exact denominator.symm.trans (src.2.2.1.trans (congrArg Assignment.denominator p.assignment))
  · rw [ds.1,rows]
    simpa only [Option.bind_some,denominator] using arithmetic

theorem constructedBodyCanonical
    (auth : canonical vocabulary.models authority.value = true)
    (domain : canonical vocabulary.models (.model p.domainName) = true)
    (shard : canonical vocabulary.models (.model p.shardName) = true) :
    canonical vocabulary.models (p.body authority) = true := by
  have apc := FamilyAuthority.canonicalField auth (show readField authority.value "apc" = some authority.apc from rfl)
  have ec := FamilyAuthority.canonicalField auth (show readField authority.value "ec" = some authority.ec from rfl)
  have isc := FamilyAuthority.canonicalField auth (show readField authority.value "isc" = some authority.isc from rfl)
  have profile := FamilyAuthority.canonicalField auth (show readField authority.value "profile" = some authority.header.profile.value from rfl)
  have coefficient := FamilyAuthority.canonicalField apc
    (show readField authority.apc "coefficientProfile" = some authority.header.coefficient.value from rfl)
  have config := FamilyAuthority.canonicalField isc
    (show readField authority.isc "config" = some authority.header.config.value from rfl)
  have parent := FamilyAuthority.canonicalField auth
    (show readField authority.value "parent" = some authority.header.parent.value from rfl)
  have round := FamilyAuthority.canonicalField isc (show readField authority.isc "round" = some authority.round from rfl)
  have schema := FamilyAuthority.canonicalField auth
    (show readField authority.value "schema" = some authority.header.schema.value from rfl)
  have seed := FamilyAuthority.canonicalField ec (show readField authority.ec "seed" = some authority.seed from rfl)
  apply FamilyAuthority.canonicalRecord
  · intro f member
    simp only [Projection.fields,PublicParameterBody.fields,List.mem_cons,List.not_mem_nil,or_false] at member
    rcases member with h|h|h|h|h|h|h|h|h|h|h|h|h|h|h
    all_goals subst f
    all_goals constructor
    all_goals first | assumption | (simp only [canonical]; try decide +kernel)
  · change ordered (PublicParameterBody.parameterFieldNames.map (fun s => encode (.text s))) = true
    decide +kernel

theorem sourceAliases : vocabulary.domain native.body.domain = some p.domainName ∧
    vocabulary.shard native.body.shard = some p.shardName := ⟨p.domainAlias,p.shardAlias⟩
theorem originalBodyUnchanged : NativeFamily.reconstructedBody native p = native.body :=
  NativeFamily.completeBodyRecovered native p

end Construction

/- The independent input and result loaders cannot choose different frames,
rows or shard identities in one observed store. These equalities are derived,
not supplied as translations of the complete public body. -/
section Completeness
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    (corpus : FamilyInputs.Corpus binding) {domain shard} (native : DerivedParameter binding domain shard)

theorem sameFrame : native.frame = corpus.frame := by
  have equal := Option.some.inj ((NativeVectorDerivation.frameComplete native.origin).symm.trans
    (NativeVectorDerivation.frameComplete corpus.origin))
  exact congrArg Subtype.val equal

include native in
theorem originalNamespaces : domain ∈ NativeBinding.domains binding.profile ∧ shard ∈ shardIds corpus.frame := by
  have valid := native.validated
  simp only [ParameterFrameValid] at valid
  obtain ⟨_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,keys,_⟩ := valid
  have member : (domain,shard) ∈ expectedKeys native.frame binding.profile := by
    rw [← keys]
    exact List.mem_map.mpr ⟨native.assignment,native.planned,by simp only [native.key.1,native.key.2]⟩
  obtain ⟨d,hd,pair⟩ := List.mem_flatMap.mp member
  obtain ⟨s,hs,same⟩ := List.mem_map.mp pair
  have ed : d = domain := congrArg Prod.fst same
  have es : s = shard := congrArg Prod.snd same
  exact ⟨by simpa only [ed] using hd,by simpa only [sameFrame corpus native,es] using hs⟩

theorem originalEntry : ∃ entry : FamilyInputs.Entry codec store binding.authority corpus.frame,
    corpus.entries.find? (fun e => e.assignment == native.assignment) = some entry ∧
    entry.assignment = native.assignment ∧ corpus.frame.shards[entry.block.slot.val] = native.partition ∧
    entry.block.rows = native.rows := by
  have planned : native.assignment ∈ corpus.entries.map FamilyInputs.Entry.assignment := by
    rw [FamilyInputs.entryAssignments corpus.bound,← sameFrame corpus native]
    exact native.planned
  obtain ⟨witness,member,equal⟩ := List.mem_map.mp planned
  cases found : corpus.entries.find? (fun e => e.assignment == native.assignment) with
  | none =>
    have rejected := List.find?_eq_none.mp found witness member
    simp [equal] at rejected
  | some entry =>
    have assignment : entry.assignment = native.assignment := by simpa using List.find?_some found
    have unique : (shardIds corpus.frame).Nodup :=
      corpus.valid.2.2.2.1.imp (fun h eq => by subst eq; exact String.lt_irrefl _ h)
    have nativeMember : native.partition ∈ corpus.frame.shards := by
      rw [← sameFrame corpus native]; exact native.partitionMember
    have partition : corpus.frame.shards[entry.block.slot.val] = native.partition := by
      apply List.inj_on_of_nodup_map unique (List.getElem_mem entry.block.slot.isLt) nativeMember
      exact entry.block.key.trans (assignment ▸ native.key.2) |>.trans native.partitionKey.symm
    have rows := native.boundRows
    rw [sameFrame corpus native,← assignment,← partition] at rows
    have rowEquality := Option.some.inj ((NativeVectorDerivation.rowsComplete entry.block.bound).symm.trans
      (NativeVectorDerivation.rowsComplete rows))
    exact ⟨entry,rfl,assignment,partition,congrArg Subtype.val rowEquality⟩

theorem parameterConstructorTotal (choice : FamilyInputs.Choice corpus.frame)
    (vocabulary : Vocabulary) {dn sn : String}
    (domainAlias : vocabulary.domain domain = some dn) (shardAlias : vocabulary.shard shard = some sn)
    (domainConfigured : dn ∈ vocabulary.domains) (shardConfigured : sn ∈ vocabulary.shards) :
    ∃ p, project (corpus := corpus) (choice := choice) (limit := accumulatorHi binding.profile)
      (vocabulary := vocabulary) (accumulatorHi binding.profile+1) native = some p := by
  obtain ⟨entry,found,assignment,partition,rows⟩ := originalEntry corpus native
  have checks : native.frame = corpus.frame ∧ entry.assignment = native.assignment ∧
      entry.block.rows = native.rows ∧ corpus.frame.shards[entry.block.slot.val] = native.partition ∧
      dn ∈ vocabulary.domains ∧ sn ∈ vocabulary.shards :=
    ⟨sameFrame corpus native,assignment,rows,partition,domainConfigured,shardConfigured⟩
  have shape := (ParameterKernel.checkedParameterSound _ _ _ _ _ _ _ _ native.computed).2.2.1
  have inside : (choice entry.block.slot).val < native.numerators.length := by
    rw [shape,← partition]; exact (choice entry.block.slot).isLt
  have arithmetic : ParameterKernel.checkedParameter (-(accumulatorHi binding.profile)-1)
      (accumulatorHi binding.profile) minInput maxInput native.assignment.denominator
      native.partition.length native.rows = some native.numerators := by
    have same : accumulatorLo binding.profile = -(accumulatorHi binding.profile)-1 := by
      simp only [accumulatorLo,accumulatorHi]; omega
    simpa only [same] using native.computed
  have output := ParameterKernel.checkedParameterCoordinateRefines _ _ _ _ _ _ _ _ arithmetic
    (choice entry.block.slot).val (by rw [← partition]; exact (choice entry.block.slot).isLt)
  obtain ⟨value,atValue,computed⟩ := output
  have bounds := (checkedAccumulateSound _ _ _ _ _ _ _ computed).2.2
  have guard : 0 ≤ accumulatorHi binding.profile+1 ∧
      Fits (-(accumulatorHi binding.profile+1)) (accumulatorHi binding.profile+1) value := by
    have positive : 0 ≤ accumulatorHi binding.profile+1 := by
      simp only [accumulatorHi]; have : (0 : Int) ≤ 2 ^ (binding.profile.accumulatorBits-1) := by positivity
      omega
    exact ⟨positive,by unfold Fits at *; omega⟩
  unfold project
  split
  · rename_i e dn' sn' he hd hs
    have ee := Option.some.inj (he.symm.trans found)
    have ed := Option.some.inj (hd.symm.trans domainAlias)
    have es := Option.some.inj (hs.symm.trans shardAlias)
    subst e; subst dn'; subst sn'
    rw [dif_pos checks]
    split
    · rename_i v ns hv hn
      have ev := Option.some.inj (hv.symm.trans atValue)
      have en := Option.some.inj (hn.symm.trans arithmetic)
      subst v; subst ns
      rw [dif_pos guard]
      exact ⟨_,rfl⟩
    · simp_all
  · simp_all

end Completeness

theorem parameterFromAuthority {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : FamilyInputs.Corpus binding} {choice : FamilyInputs.Choice corpus.frame}
    {input : FamilyInputs.Projected corpus choice (accumulatorHi binding.profile)}
    {vocabulary : Vocabulary} {metadataTrust} {source : Metadata metadataTrust}
    (authority : FamilyAuthority.Projection input vocabulary source)
    {domain shard} (native : DerivedParameter binding domain shard) :
    ∃ p, project (corpus := corpus) (choice := choice) (limit := accumulatorHi binding.profile)
      (vocabulary := vocabulary) (accumulatorHi binding.profile+1) native = some p := by
  have names := originalNamespaces corpus native
  obtain ⟨dn,hd,cd⟩ := FamilyAuthority.domainAliasComplete authority names.1
  obtain ⟨sn,hs,cs⟩ := FamilyAuthority.shardAliasComplete authority names.2
  exact parameterConstructorTotal corpus native choice vocabulary hd hs cd cs

/- Existence for the executable complete-body gate, not just the pure body
constructor. The prerequisites concern the already checked source authority and
primitive model names; the whole result body is constructed here. -/
theorem checkedParameterFromAuthority {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : FamilyInputs.Corpus binding} {choice : FamilyInputs.Choice corpus.frame}
    {input : FamilyInputs.Projected corpus choice (accumulatorHi binding.profile)}
    {vocabulary : Vocabulary} {metadataTrust} {source : Metadata metadataTrust}
    (authority : FamilyAuthority.Checked input vocabulary source)
    (names : ∀ n ∈ vocabulary.domains ++ vocabulary.shards, canonical vocabulary.models (.model n) = true)
    {domain shard} (native : DerivedParameter binding domain shard) :
    ∃ value checked, check authority.projection (accumulatorHi binding.profile+1) native value = some checked := by
  obtain ⟨p,computed⟩ := parameterFromAuthority authority.projection native
  have bodyCanonical := constructedBodyCanonical authority.projection (accumulatorHi binding.profile+1) native p
    authority.canonical (names _ (List.mem_append_left _ p.domainConfigured))
    (names _ (List.mem_append_right _ p.shardConfigured))
  refine ⟨p.body authority.projection,⟨p,bodyCanonical⟩,?_⟩
  unfold check
  rw [computed]
  simp only [bind,Option.bind]
  split
  · rfl
  · rename_i bad; exact False.elim (bad ⟨bodyCanonical,by trivial⟩)


/- Full original vector arithmetic without the older signed-fraction or 4096
representation restrictions. Whole native objects are compared, never rebuilt. -/
structure OriginalVector where
  first : NativeScaleBinding.Bound
  slices : List NativeVectorContext.Slice
  values : List Int
  leaves : List Bytes

def originalVector (source : NativeVectorContext.Bound) (domain : Bytes) (block : Nat) : Option OriginalVector := do
  let first ← source.first.corpus.manifest.blocks[block]?
  let slices ← NativeVectorContext.sliceRows block (NativePlanQCorpus.inDomain domain source.source.rows)
  let leaves ← NativeVectorAuthority.sourceLeaves block slices
  let width := first.block.frame.values.length
  if 0 < width ∧ slices ≠ [] ∧ ∀ row ∈ slices, row.block.block.frame.values.length = width then
    some ⟨first,slices,ParameterKernel.exactParameterRows source.source.plan.accumulator.numbers.denominator
      (List.replicate width 0) (slices.map NativeVectorArithmetic.kernelRow),leaves⟩
  else none

theorem originalVectorSource {source domain block vector} (loaded : originalVector source domain block = some vector) :
    source.first.corpus.manifest.blocks[block]? = some vector.first ∧
    NativeVectorContext.sliceRows block (NativePlanQCorpus.inDomain domain source.source.rows) = some vector.slices ∧
    NativeVectorAuthority.sourceLeaves block vector.slices = some vector.leaves ∧
    0 < vector.first.block.frame.values.length ∧ vector.slices ≠ [] ∧
    (∀ row ∈ vector.slices, row.block.block.frame.values.length = vector.first.block.frame.values.length) ∧
    vector.values = ParameterKernel.exactParameterRows source.source.plan.accumulator.numbers.denominator
      (List.replicate vector.first.block.frame.values.length 0) (vector.slices.map NativeVectorArithmetic.kernelRow) := by
  simp only [originalVector,bind,Option.bind_eq_some_iff] at loaded
  obtain ⟨first,hf,slices,hs,leaves,hl,last⟩ := loaded
  split at last <;> try contradiction
  rename_i valid
  cases Option.some.inj last
  exact ⟨hf,hs,hl,valid.1,valid.2.1,valid.2.2,rfl⟩

def publicParameterRows (limit denominator : Int) (rows : List ParameterKernel.Row) : Option Int := do
  if ∀ row ∈ rows, row.values.length = 1 then
    let terms := ParameterKernel.coordinateTerms denominator 0 rows
    let _ ← checkedAccumulate (-limit-1) limit (-limit-1) limit 0 (terms.map (fun pair => (pair.1,1)))
    checkedAccumulate (-limit-1) limit (-limit-1) limit 0 terms
  else none

theorem originalSlicesTotal {first : NativeManifestBinding.Bound} {rows : List NativePlanQCorpus.Row}
    {block q} (slot : first.blocks[block]? = some q)
    (compatible : ∀ r ∈ rows, NativeVectorContext.Compatible first r.corpus.manifest) :
    ∃ slices, NativeVectorContext.sliceRows block rows = some slices := by
  induction rows with
  | nil => exact ⟨[],rfl⟩
  | cons r rs ih =>
    obtain ⟨head,atHead,_⟩ := NativeVectorContext.sameSlot (compatible r (by simp)) slot
    obtain ⟨tail,atTail⟩ := ih (fun r hr => compatible r (List.mem_cons_of_mem _ hr))
    exact ⟨⟨r,head⟩::tail,by simp only [NativeVectorContext.sliceRows,atHead,atTail,bind,Option.bind]⟩

theorem originalLeavesTotal {block slices}
    (slots : ∀ s ∈ slices, ∃ ref, s.source.corpus.manifest.manifest.refs[block]? = some ref) :
    ∃ leaves, NativeVectorAuthority.sourceLeaves block slices = some leaves := by
  induction slices with
  | nil => exact ⟨[],rfl⟩
  | cons s ss ih =>
    obtain ⟨ref,atRef⟩ := slots s (by simp)
    obtain ⟨leaves,rest⟩ := ih (fun s hs => slots s (List.mem_cons_of_mem _ hs))
    exact ⟨ref.wire.leaf::leaves,by simp only [NativeVectorAuthority.sourceLeaves,atRef,rest,bind,Option.bind]⟩

/- This completeness statement starts at the actual original-byte binder.
The nonempty selected domain is an existing plan/domain-coverage requirement;
there is no caller-provided result vector or bound on its coordinate count. -/
theorem originalVectorTotal {sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source}
    (bound : FamilyInputs.OriginalVectorSource sha policyRaw stateRaw apcId configRaw proofRaw profileRaw permission inputs source)
    {domain block first} (slot : source.first.corpus.manifest.blocks[block]? = some first)
    (nonempty : NativePlanQCorpus.inDomain domain source.source.rows ≠ []) :
    ∃ vector, originalVector source domain block = some vector := by
  have src := FamilyInputs.originalVectorSourceParts bound
  have rows := (FamilyInputs.originalRowsSourceParts src.1).2
  have subset : ∀ r ∈ NativePlanQCorpus.inDomain domain source.source.rows, r ∈ source.source.rows :=
    fun r hr => (List.mem_filter.mp hr).1
  obtain ⟨slices,sliced⟩ := originalSlicesTotal slot (fun r hr => src.2.2 r (subset r hr))
  have slicesSource := NativeVectorContext.slicedSources sliced
  have firstMember : source.first ∈ source.source.rows := List.mem_of_head? src.2.1
  obtain ⟨_,_,_,_,firstLoaded⟩ := NativePlanQCorpus.rowMember rows source.first firstMember
  have manifest := FamilyInputs.rowManifestSource firstLoaded
  have firstShape := ManifestFamily.corpusShapes (NativeManifestBinding.fullOrderedCorpus manifest)
    first (List.mem_of_getElem? slot)
  have positive : 0 < first.block.frame.values.length := by
    rw [firstShape]
    exact (ManifestFamily.positiveAndBounded manifest first (List.mem_of_getElem? slot)).1
  have eachSource (s : NativeVectorContext.Slice) (member : s ∈ slices) : s.source ∈ source.source.rows := by
    apply subset
    rw [← slicesSource.1]
    exact List.mem_map.mpr ⟨s,member,rfl⟩
  have widths : ∀ s ∈ slices, s.block.block.frame.values.length = first.block.frame.values.length := by
    intro s member
    obtain ⟨_,_,_,_,loaded⟩ := NativePlanQCorpus.rowMember rows s.source (eachSource s member)
    have manifest := FamilyInputs.rowManifestSource loaded
    have shape := ManifestFamily.corpusShapes (NativeManifestBinding.fullOrderedCorpus manifest)
      s.block (List.mem_of_getElem? (slicesSource.2 s member))
    obtain ⟨q,atQ,same⟩ := NativeVectorContext.sameSlot (src.2.2 s.source (eachSource s member)) slot
    have equal := Option.some.inj (atQ.symm.trans (slicesSource.2 s member))
    subst q
    rw [shape,same,firstShape]
  obtain ⟨leaves,leafSource⟩ := originalLeavesTotal (block := block) (slices := slices) (by
    intro s member
    obtain ⟨_,_,_,_,loaded⟩ := NativePlanQCorpus.rowMember rows s.source (eachSource s member)
    have lengths := NativeManifestBinding.corpusLengths
      (NativeManifestBinding.fullOrderedCorpus (FamilyInputs.rowManifestSource loaded))
    have inside := (List.getElem?_eq_some_iff.mp (slicesSource.2 s member)).1
    have refInside : block < s.source.corpus.manifest.manifest.refs.length := by omega
    exact ⟨_,List.getElem?_eq_getElem refInside⟩)
  have slicesNonempty : slices ≠ [] := by
    intro empty
    apply nonempty
    simpa only [empty,List.map_nil] using slicesSource.1.symm
  unfold originalVector
  simp only [slot,sliced,leafSource,bind,Option.bind]
  rw [if_pos ⟨positive,slicesNonempty,widths⟩]
  exact ⟨_,rfl⟩

section OriginalParameter
variable {source indices profile quantum current vocabulary configured names earlyTrust planningTrust metadata selected}
    (authority : FamilyAuthority.Original source indices profile quantum current vocabulary configured names
      (earlyTrust := earlyTrust) (planningTrust := planningTrust) metadata selected)
    (native : NativeParameterLineage.Edge) (block : Nat) (nativeShardAlias : Bytes → Option String)

structure OriginalProjection where
  vector : OriginalVector
  vectorSource : originalVector source native.certificate.common.domain block = some vector
  coordinate : Nat
  atCoordinate : indices[block]? = some coordinate
  value : Int
  nativeValue : vector.values[coordinate]? = some value
  exactNative : native.certificate.common.leaves = vector.leaves.mergeSort NativePolicyBytes.bytesLT ∧
    native.certificate.common.numerators = vector.values.map (asciiBytes ∘ toString)
  parents : native.certificate.common.context = source.source.plan.members.edge.certificate.common.context ∧
    native.certificate.common.plan = source.source.plan.members.edge.id ∧
    native.certificate.common.isc = source.source.plan.members.edge.parent.qcId ∧
    native.certificate.common.ec = source.source.plan.members.edge.ec.id ∧
    native.certificate.common.denominator = source.source.plan.accumulator.numbers.denominator
  rows : List ParameterKernel.Row
  imageRows : FamilyInputs.imageRows authority.input.image (NativeVectorLayout.text native.certificate.common.domain) block = some rows
  arithmetic : publicParameterRows authority.input.image.limit native.certificate.common.denominator rows = some value
  domainName : String
  domainAlias : vocabulary.domain (NativeVectorLayout.text native.certificate.common.domain) = some domainName
  domainConfigured : domainName ∈ vocabulary.domains
  shardName : String
  shardAlias : vocabulary.shard (NativeVectorLayout.shardName vector.first.block.header.ordinal) = some shardName
  nativeAlias : nativeShardAlias native.certificate.common.shard = some shardName
  shardConfigured : shardName ∈ vocabulary.shards

def projectOriginal : Option (OriginalProjection authority native block nativeShardAlias) := do
  match vs : originalVector source native.certificate.common.domain block, atIndex : indices[block]? with
  | some vector, some coordinate =>
    match nv : vector.values[coordinate]?, rs : FamilyInputs.imageRows authority.input.image
        (NativeVectorLayout.text native.certificate.common.domain) block,
        dn : vocabulary.domain (NativeVectorLayout.text native.certificate.common.domain),
        sn : vocabulary.shard (NativeVectorLayout.shardName vector.first.block.header.ordinal) with
    | some value,some rows,some domainName,some shardName =>
      if exactBody : native.certificate.common.leaves = vector.leaves.mergeSort NativePolicyBytes.bytesLT ∧
          native.certificate.common.numerators = vector.values.map (asciiBytes ∘ toString) then
        if parents : native.certificate.common.context = source.source.plan.members.edge.certificate.common.context ∧
            native.certificate.common.plan = source.source.plan.members.edge.id ∧
            native.certificate.common.isc = source.source.plan.members.edge.parent.qcId ∧
            native.certificate.common.ec = source.source.plan.members.edge.ec.id ∧
            native.certificate.common.denominator = source.source.plan.accumulator.numbers.denominator then
          if arithmetic : publicParameterRows authority.input.image.limit native.certificate.common.denominator rows = some value then
            if aliases : domainName ∈ vocabulary.domains ∧ nativeShardAlias native.certificate.common.shard = some shardName ∧
                shardName ∈ vocabulary.shards then
              some ⟨vector,vs,coordinate,atIndex,value,nv,exactBody,parents,rows,rs,arithmetic,
                domainName,dn,aliases.1,shardName,sn,aliases.2.1,aliases.2.2⟩
            else none
          else none
        else none
      else none
    | _,_,_,_ => none
  | _,_ => none

def OriginalProjection.fields (p : OriginalProjection authority native block nativeShardAlias) : List (String × Value) :=
  PublicParameterBody.fields authority.parents.value authority.header.arithmetic.value authority.value
    authority.parents.coefficient.value authority.parents.ec.parent.header.config.value (.model p.domainName)
    authority.parents.ec.value authority.parents.ec.parent.value authority.header.parent.value
    authority.parents.ec.parent.header.round authority.header.schema.value authority.parents.ec.seedValue
    (.model p.shardName) p.value

def OriginalProjection.body (p : OriginalProjection authority native block nativeShardAlias) : Value := record (p.fields authority native block nativeShardAlias)

def checkOriginal (candidate : Value) : Option (OriginalProjection authority native block nativeShardAlias) := do
  let p ← projectOriginal authority native block nativeShardAlias
  if canonical vocabulary.models (p.body authority native block nativeShardAlias) = true ∧
      candidate = p.body authority native block nativeShardAlias then some p else none

theorem originalProjectionLoaded (p : OriginalProjection authority native block nativeShardAlias) :
    projectOriginal authority native block nativeShardAlias = some p := by
  unfold projectOriginal
  split
  · rename_i vector coordinate hv hc
    have sameVector := Option.some.inj (hv.symm.trans p.vectorSource)
    have sameCoordinate := Option.some.inj (hc.symm.trans p.atCoordinate)
    subst vector; subst coordinate
    split
    · rename_i value rows domainName shardName hn hr hd hs
      have sameValue := Option.some.inj (hn.symm.trans p.nativeValue)
      have sameRows := Option.some.inj (hr.symm.trans p.imageRows)
      have sameDomain := Option.some.inj (hd.symm.trans p.domainAlias)
      have sameShard := Option.some.inj (hs.symm.trans p.shardAlias)
      subst value; subst rows; subst domainName; subst shardName
      rw [dif_pos p.exactNative,dif_pos p.parents,dif_pos p.arithmetic,
        dif_pos ⟨p.domainConfigured,p.nativeAlias,p.shardConfigured⟩]
    · simp_all [p.nativeValue,p.imageRows,p.domainAlias,p.shardAlias]
      rename_i bad
      exact (bad _ _ _ _ rfl rfl rfl) rfl
  · simp_all [p.vectorSource,p.atCoordinate]

theorem originalCheckFromCanonical (p : OriginalProjection authority native block nativeShardAlias)
    (safe : canonical vocabulary.models (p.body authority native block nativeShardAlias) = true) :
    checkOriginal authority native block nativeShardAlias (p.body authority native block nativeShardAlias) = some p := by
  simp only [checkOriginal,originalProjectionLoaded authority native block nativeShardAlias p,bind,Option.bind]
  exact if_pos ⟨safe,by trivial⟩

theorem originalFullVectorRetained (p : OriginalProjection authority native block nativeShardAlias) :
    native.certificate.common.numerators = p.vector.values.map (asciiBytes ∘ toString) ∧
    native.certificate.common.leaves.Perm p.vector.leaves :=
  ⟨p.exactNative.2,p.exactNative.1 ▸ List.mergeSort_perm p.vector.leaves NativePolicyBytes.bytesLT⟩

theorem originalValueFromOwnInputs (p : OriginalProjection authority native block nativeShardAlias) :
    (FamilyInputs.memberImageRows (FamilyInputs.completedImage authority.input.image configured)
      (FamilyInputs.activeNames authority.input.image.tickets)
      (NativeVectorLayout.text native.certificate.common.domain) block).bind
      (publicParameterRows authority.input.image.limit native.certificate.common.denominator) = some p.value := by
  rw [FamilyInputs.completedImageComputesSameRows _ _ authority.input.coverage.2.1
    authority.input.coverage.2.2.1,p.imageRows]
  exact p.arithmetic

theorem originalBodyFieldInventory (p : OriginalProjection authority native block nativeShardAlias) :
    (p.fields authority native block nativeShardAlias).map Prod.fst = PublicParameterBody.parameterFieldNames := rfl

theorem originalBodyContainsWholeAuthority (p : OriginalProjection authority native block nativeShardAlias) :
    readField (p.body authority native block nativeShardAlias) "authority" = some authority.value := rfl

theorem originalBodyCanonical (p : OriginalProjection authority native block nativeShardAlias)
    (auth : canonical vocabulary.models authority.value = true)
    (domain : canonical vocabulary.models (.model p.domainName) = true)
    (shard : canonical vocabulary.models (.model p.shardName) = true) :
    canonical vocabulary.models (p.body authority native block nativeShardAlias) = true := by
  have apc := FamilyAuthority.canonicalField auth
    (show readField authority.value "apc" = some authority.parents.value from rfl)
  have ec := FamilyAuthority.canonicalField auth
    (show readField authority.value "ec" = some authority.parents.ec.value from rfl)
  have isc := FamilyAuthority.canonicalField auth
    (show readField authority.value "isc" = some authority.parents.ec.parent.value from rfl)
  have profile := FamilyAuthority.canonicalField auth
    (show readField authority.value "profile" = some authority.header.arithmetic.value from rfl)
  have coefficient := FamilyAuthority.canonicalField apc
    (show readField authority.parents.value "coefficientProfile" = some authority.parents.coefficient.value from rfl)
  have config := FamilyAuthority.canonicalField isc
    (show readField authority.parents.ec.parent.value "config" = some authority.parents.ec.parent.header.config.value from rfl)
  have parent := FamilyAuthority.canonicalField auth
    (show readField authority.value "parent" = some authority.header.parent.value from rfl)
  have round := FamilyAuthority.canonicalField isc
    (show readField authority.parents.ec.parent.value "round" = some authority.parents.ec.parent.header.round from rfl)
  have schema := FamilyAuthority.canonicalField auth
    (show readField authority.value "schema" = some authority.header.schema.value from rfl)
  have seed := FamilyAuthority.canonicalField ec
    (show readField authority.parents.ec.value "seed" = some authority.parents.ec.seedValue from rfl)
  apply FamilyAuthority.canonicalRecord
  · intro f member
    simp only [OriginalProjection.fields,PublicParameterBody.fields,List.mem_cons,List.not_mem_nil,or_false] at member
    rcases member with h|h|h|h|h|h|h|h|h|h|h|h|h|h|h
    all_goals subst f
    all_goals constructor
    all_goals first | assumption | (simp only [canonical]; try decide +kernel)
  · change ordered (PublicParameterBody.parameterFieldNames.map (fun s => encode (.text s))) = true
    decide +kernel

end OriginalParameter

/- The full exact recurrence is independent of draft adapter bounds. This
identity holds for every present coordinate, with no out-of-range fallback. -/
theorem exactVectorLength (denominator : Int) {acc : List Int} {rows : List ParameterKernel.Row}
    (shapes : ∀ row ∈ rows, row.values.length = acc.length) :
    (ParameterKernel.exactParameterRows denominator acc rows).length = acc.length := by
  induction rows generalizing acc with
  | nil => rfl
  | cons row rows ih =>
    have shape := shapes row List.mem_cons_self
    have length : (ParameterKernel.exactAddVector (row.numerator*(denominator/row.denominator)) acc row.values).length = acc.length := by
      simp only [ParameterKernel.exactAddVector,List.length_zipWith,shape,Nat.min_self]
    exact (ih (fun r hr => (shapes r (List.mem_cons_of_mem _ hr)).trans length.symm)).trans length

theorem exactVectorCoordinate (denominator : Int) {acc : List Int} {rows : List ParameterKernel.Row}
    (shapes : ∀ row ∈ rows, row.values.length = acc.length) {index : Nat} {a : Int}
    (atIndex : acc[index]? = some a) :
    (ParameterKernel.exactParameterRows denominator acc rows)[index]? =
      some (exactAccumulate a (ParameterKernel.coordinateTerms denominator index rows)) := by
  induction rows generalizing acc a with
  | nil => exact atIndex
  | cons row rows ih =>
    have shape := shapes row List.mem_cons_self
    have inside : index < row.values.length := by
      rw [shape]; exact (List.getElem?_eq_some_iff.mp atIndex).1
    have lookup := List.getElem?_eq_getElem inside
    have length : (ParameterKernel.exactAddVector (row.numerator*(denominator/row.denominator)) acc row.values).length = acc.length := by
      simp only [ParameterKernel.exactAddVector,List.length_zipWith,shape,Nat.min_self]
    have next : (ParameterKernel.exactAddVector (row.numerator*(denominator/row.denominator)) acc row.values)[index]? =
        some (a + (row.numerator*(denominator/row.denominator))*row.values[index]) := by
      simp [ParameterKernel.exactAddVector,List.getElem?_zipWith,atIndex,lookup]
    have tail := ih (fun r hr => (shapes r (List.mem_cons_of_mem _ hr)).trans length.symm) next
    simpa only [ParameterKernel.exactParameterRows,ParameterKernel.coordinateTerms,List.map_cons,
      lookup,Option.getD_some,exactAccumulate] using tail

theorem scalarRowsFromSlices {source domain block coordinate vector}
    (computed : originalVector source domain block = some vector)
    (inside : coordinate < vector.first.block.frame.values.length) :
    FamilyInputs.originalScalarRows source.source domain block coordinate =
      some (vector.slices.map (fun s => VectorShardRepresentation.rowAt coordinate (NativeVectorArithmetic.kernelRow s))) := by
  have src := originalVectorSource computed
  have slices := NativeVectorContext.slicedSources src.2.1
  unfold FamilyInputs.originalScalarRows
  rw [← slices.1]
  have collector : ∀ s ∈ vector.slices,
      (NativeAvailableQ.coordinate s.source.corpus.manifest block coordinate).map
        (fun value => (⟨s.source.term.source.weight.numerator,s.source.term.source.weight.denominator,[value]⟩ : ParameterKernel.Row)) =
      some (VectorShardRepresentation.rowAt coordinate (NativeVectorArithmetic.kernelRow s)) := by
    intro s member
    have bound : coordinate < s.block.block.frame.values.length := by rw [src.2.2.2.2.2.1 s member]; exact inside
    simp only [NativeAvailableQ.coordinate,slices.2 s member,bind,Option.bind_some,
      List.getElem?_eq_getElem bound,Option.map_some,VectorShardRepresentation.rowAt,NativeVectorArithmetic.kernelRow]
    rfl
  generalize vector.slices = ss at collector ⊢
  induction ss with
  | nil => rfl
  | cons s ss ih =>
    simp only [List.map_cons,collect,collector s List.mem_cons_self,bind,Option.bind_some]
    rw [ih (fun t ht => collector t (List.mem_cons_of_mem _ ht))]
    rfl

theorem originalVectorCoordinate {source domain block coordinate vector}
    (computed : originalVector source domain block = some vector)
    (inside : coordinate < vector.first.block.frame.values.length) :
    vector.values[coordinate]? = some (exactAccumulate 0
      (ParameterKernel.coordinateTerms source.source.plan.accumulator.numbers.denominator coordinate
        (vector.slices.map NativeVectorArithmetic.kernelRow))) := by
  have src := originalVectorSource computed
  rw [src.2.2.2.2.2.2]
  apply exactVectorCoordinate
  · intro row member
    obtain ⟨s,hs,rfl⟩ := List.mem_map.mp member
    simpa only [List.length_replicate,NativeVectorArithmetic.kernelRow] using src.2.2.2.2.2.1 s hs
  · exact List.getElem?_replicate_of_lt inside

/- Resolve the original native shard name into exactly one original manifest
slot. The ordinal name is only a refinement key, never a native identity. -/
def originalBlockMatches (source : NativeVectorContext.Bound) (vocabulary : Vocabulary)
    (nativeShardAlias : Bytes → Option String) (native : NativeParameterLineage.Edge) : List Nat :=
  (List.range source.first.corpus.manifest.blocks.length).filter (fun block =>
    match source.first.corpus.manifest.blocks[block]? with
    | none => false
    | some q => match nativeShardAlias native.certificate.common.shard with
      | none => false
      | some name => vocabulary.shard (NativeVectorLayout.shardName q.block.header.ordinal) == some name)

section OriginalLeaf
variable {source indices profile quantum current vocabulary configured names earlyTrust planningTrust metadata selected}
    (authority : FamilyAuthority.Original source indices profile quantum current vocabulary configured names
      (earlyTrust := earlyTrust) (planningTrust := planningTrust) metadata selected)
    (nativeShardAlias : Bytes → Option String) (native : NativeParameterLineage.Edge)

structure OriginalLeaf where
  block : Nat
  uniqueBlock : originalBlockMatches source vocabulary nativeShardAlias native = [block]
  projection : OriginalProjection authority native block nativeShardAlias

def loadOriginalLeaf : Option (OriginalLeaf authority nativeShardAlias native) :=
  match found : originalBlockMatches source vocabulary nativeShardAlias native with
  | [block] => do
    let projection ← projectOriginal authority native block nativeShardAlias
    some ⟨block,found,projection⟩
  | _ => none

def OriginalLeaf.value (p : OriginalLeaf authority nativeShardAlias native) : Value :=
  p.projection.body authority native p.block nativeShardAlias

theorem originalLeafLoaded (p : OriginalLeaf authority nativeShardAlias native) :
    loadOriginalLeaf authority nativeShardAlias native = some p := by
  unfold loadOriginalLeaf
  split
  · rename_i block found
    have same : block = p.block := by simpa only [p.uniqueBlock,List.cons.injEq,and_true] using found.symm
    subst block
    rw [originalProjectionLoaded authority native p.block nativeShardAlias p.projection]
    rfl
  · simp_all [p.uniqueBlock]

theorem originalLeafRejectsAmbiguous
    (many : 1 < (originalBlockMatches source vocabulary nativeShardAlias native).length) :
    loadOriginalLeaf authority nativeShardAlias native = none := by
  unfold loadOriginalLeaf
  split <;> try rfl
  rename_i block found
  rw [found] at many; simp at many

end OriginalLeaf

end DeltaReduce.FamilyParameter
