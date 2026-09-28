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

end DeltaReduce.FamilyParameter
