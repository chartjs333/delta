import DeltaReduce.PublicAuthority

/-! Complete PARAMETER body construction with separately checked model-width
arithmetic. This is not phase/QC admission, TLA Next or native recovery. -/
namespace DeltaReduce.PublicParameterBody
open NativeBinding NativeInputProjection PublicState PublicArithmeticInputs PublicAuthority

def modelLo (limit : ModelLimit) : Int := -limit.value - 1

-- This projection uses the same numeric bound for the separate public result
-- guard. Matching that bound to the actual TLA configuration remains required.
def resultFits (limit : ModelLimit) (value : Int) : Bool :=
  decide (Fits (-limit.value) limit.value value)

-- Recompute at the projected accumulator width. Mathematical output identity
-- follows from the exact row recurrence, not an expected-result premise.
theorem checkedWidthsAgree {lo hi inputLo inputHi otherLo otherHi otherInputLo otherInputHi denominator width rows a b}
    (left : ParameterKernel.checkedParameter lo hi inputLo inputHi denominator width rows = some a)
    (right : ParameterKernel.checkedParameter otherLo otherHi otherInputLo otherInputHi denominator width rows = some b) :
    a = b := by
  have l := ParameterKernel.checkedParameterSound _ _ _ _ _ _ _ _ left
  have r := ParameterKernel.checkedParameterSound _ _ _ _ _ _ _ _ right
  exact l.2.2.2.1.trans r.2.2.2.1.symm

structure Narrow {codec store trust anchor} {binding : Binding codec trust anchor store}
    {domain shard} (native : DerivedParameter binding domain shard) (limit : ModelLimit) where
  scalar : NativeScalarProjection.Parameter native
  resultRange : resultFits limit scalar.value = true
  computed : ParameterKernel.checkedParameter (modelLo limit) limit.value minInput maxInput
    native.assignment.denominator native.partition.length native.rows = some [scalar.value]

def narrow {codec store trust anchor} {binding : Binding codec trust anchor store}
    {domain shard} (native : DerivedParameter binding domain shard) (limit : ModelLimit) :
    Option (Narrow native limit) := do
  let scalar ← NativeScalarProjection.parameter native
  if inRange : resultFits limit scalar.value = true then
  match computed : ParameterKernel.checkedParameter (modelLo limit) limit.value minInput maxInput
      native.assignment.denominator native.partition.length native.rows with
  | none => none
  | some result =>
      have same : result = [scalar.value] := (checkedWidthsAgree computed native.computed).trans scalar.exactNumerator
      some ⟨scalar,inRange,by simpa only [same] using computed⟩
  else none

theorem resultGuardIsSymmetric {codec store trust anchor binding domain shard native limit}
    (n : Narrow (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (domain := domain) (shard := shard) native limit) :
    Fits (-limit.value) limit.value n.scalar.value := by
  simpa only [resultFits,decide_eq_true_eq] using n.resultRange

theorem narrowPreservesNativeNumerator {codec store trust anchor binding domain shard native limit}
    (n : Narrow (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (domain := domain) (shard := shard) native limit) :
    native.body.numerators = [n.scalar.value] := n.scalar.exactNumerator

theorem narrowChecksEveryCoefficientProductAndPrefix {codec store trust anchor binding domain shard native limit}
    (n : Narrow (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (domain := domain) (shard := shard) native limit) :
    ParameterKernel.PrefixesSafe (modelLo limit) limit.value minInput maxInput
      native.assignment.denominator 0 [0] native.rows := by
  have safe := (ParameterKernel.checkedParameterSound _ _ _ _ _ _ _ _ n.computed).2.2.2.2.2
  simpa only [n.scalar.scalar,List.replicate_succ,List.replicate_zero] using safe

theorem narrowScalarRefinesCheckedFold {codec store trust anchor binding domain shard native limit}
    (n : Narrow (codec := codec) (store := store) (trust := trust) (anchor := anchor)
      (binding := binding) (domain := domain) (shard := shard) native limit) :
    checkedAccumulate (modelLo limit) limit.value (modelLo limit) limit.value 0
      (ParameterKernel.coordinateTerms native.assignment.denominator 0 native.rows) = some n.scalar.value := by
  obtain ⟨value,atIndex,computed⟩ := ParameterKernel.checkedParameterCoordinateRefines
    (modelLo limit) limit.value minInput maxInput native.assignment.denominator native.partition.length
    native.rows [n.scalar.value] n.computed 0 (by rw [n.scalar.scalar]; omega)
  have same : value = n.scalar.value := by simpa using atIndex.symm
  simpa only [same] using computed

def parameterFieldNames : List String :=
  ["apc","arithmeticProfile","authority","checked","coefficientProfile","config","domain","ec","isc",
    "parent","round","schema","seed","shard","value"]

-- Low-level mathematical constructor; the source-bound entry point is check.
def fields (apc profile authority coefficient config domain ec isc parent round schema seed shard : Value)
    (number : Int) : List (String × Value) := [
  ("apc",apc),("arithmeticProfile",profile),("authority",authority),("checked",.boolean true),
  ("coefficientProfile",coefficient),("config",config),("domain",domain),("ec",ec),("isc",isc),
  ("parent",parent),("round",round),("schema",schema),("seed",seed),("shard",shard),("value",.integer number)]

section Binding
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : Corpus binding} {limit : ModelLimit} {input : Projected corpus limit}
    {vocabulary : Vocabulary} {metadataTrust} {source : Metadata metadataTrust}
    (authority : PublicAuthority.Projection input vocabulary source)
    {domain shard : String} (native : DerivedParameter binding domain shard)

structure Projection where
  math : Narrow native limit
  frame : native.frame = corpus.frame
  block : BlockEntry codec store binding.authority corpus.frame
  selected : corpus.blocks.find? (fun b => b.assignment == native.assignment) = some block
  assignment : block.assignment = native.assignment
  rows : block.data.rows = native.rows
  domainName : String
  domainAlias : vocabulary.domain domain = some domainName
  domainConfigured : domainName ∈ vocabulary.domains
  shardName : String
  shardAlias : vocabulary.shard shard = some shardName
  shardConfigured : shardName ∈ vocabulary.shards

def project : Option (Projection (corpus := corpus) (limit := limit) (vocabulary := vocabulary) native) := do
  let math ← narrow native limit
  match found : corpus.blocks.find? (fun b => b.assignment == native.assignment),
      hd : vocabulary.domain domain, hs : vocabulary.shard shard with
  | some block, some domainName, some shardName =>
      if checked : native.frame = corpus.frame ∧ block.assignment = native.assignment ∧
          block.data.rows = native.rows ∧ domainName ∈ vocabulary.domains ∧ shardName ∈ vocabulary.shards then
        some ⟨math,checked.1,block,found,checked.2.1,checked.2.2.1,domainName,hd,checked.2.2.2.1,
          shardName,hs,checked.2.2.2.2⟩
      else none
  | _,_,_ => none

def Projection.fields (p : Projection (corpus := corpus) (limit := limit) (vocabulary := vocabulary) native) : List (String × Value) :=
  PublicParameterBody.fields authority.apc authority.header.profile.value authority.value
    authority.header.coefficient.value authority.header.config.value (.model p.domainName)
    authority.ec authority.isc authority.header.parent.value authority.round authority.header.schema.value
    authority.seed (.model p.shardName) p.math.scalar.value

def Projection.value (p : Projection (corpus := corpus) (limit := limit) (vocabulary := vocabulary) native) : Value :=
  record (p.fields authority)

structure Checked where
  projection : Projection (corpus := corpus) (limit := limit) (vocabulary := vocabulary) native
  canonical : PublicState.canonical vocabulary.models (projection.value authority) = true

def check (candidate : Value) : Option (Checked authority native) := do
  let p ← project (corpus := corpus) (limit := limit) (vocabulary := vocabulary) native
  if valid : PublicState.canonical vocabulary.models (p.value authority) = true ∧ candidate = p.value authority then
    some ⟨p,valid.1⟩
  else none

theorem fullBodyWasComputed {candidate checked} (accepted : check authority native candidate = some checked) :
    candidate = checked.projection.value authority := by
  unfold check at accepted
  cases hp : project (corpus := corpus) (limit := limit) (vocabulary := vocabulary) native with
  | none => simp [hp] at accepted
  | some p =>
      simp only [hp,Bind.bind,Option.bind] at accepted
      split at accepted
      · rename_i valid; cases accepted; exact valid.2
      · contradiction

variable (p : Projection (corpus := corpus) (limit := limit) (vocabulary := vocabulary) native)

theorem completeFieldInventory : (p.fields authority).map Prod.fst = parameterFieldNames := rfl
theorem exactFullAuthority : readField (p.value authority) "authority" = some authority.value := rfl
theorem exactEntireParents : readField (p.value authority) "apc" = some authority.apc ∧
    readField (p.value authority) "ec" = some authority.ec ∧ readField (p.value authority) "isc" = some authority.isc ∧
    readField (p.value authority) "seed" = some authority.seed := ⟨rfl,rfl,rfl,rfl⟩
theorem exactConfiguredHeader : readField (p.value authority) "parent" = some authority.header.parent.value ∧
    readField (p.value authority) "round" = some authority.round ∧
    readField (p.value authority) "schema" = some authority.header.schema.value ∧
    readField (p.value authority) "coefficientProfile" = some authority.header.coefficient.value ∧
    readField (p.value authority) "arithmeticProfile" = some authority.header.profile.value := ⟨rfl,rfl,rfl,rfl,rfl⟩

theorem bodyNumberHasBothNativeAndProjectedChecks :
    readField (p.value authority) "value" = some (.integer p.math.scalar.value) ∧
    native.body.numerators = [p.math.scalar.value] ∧
    ParameterKernel.PrefixesSafe (modelLo limit) limit.value minInput maxInput native.assignment.denominator 0 [0] native.rows :=
  ⟨rfl,narrowPreservesNativeNumerator p.math,narrowChecksEveryCoefficientProductAndPrefix p.math⟩

theorem publicAliasesFromOriginalNativeKey : vocabulary.domain native.body.domain = some p.domainName ∧
    vocabulary.shard native.body.shard = some p.shardName := ⟨p.domainAlias,p.shardAlias⟩
theorem fullInputBlockRetained : p.block ∈ corpus.blocks ∧ p.block.assignment = native.assignment ∧
    p.block.data.rows = native.rows := ⟨List.mem_of_find?_eq_some p.selected,p.assignment,p.rows⟩
theorem fullDenominatorAndQuantum : p.block.input.denominator = native.body.denominator ∧
    p.block.input.quantum = native.assignment.quantum := by
  simp [BlockEntry.input,DerivedParameter.body,p.assignment]

theorem originalQAndWeightsAt (index : Nat) (row : ParameterKernel.Row) (found : native.rows[index]? = some row) :
    ∃ contribution, native.assignment.contributions[index]? = some contribution ∧
      ∃ loaded : LoadedRow codec store binding.authority.schema native.frame native.assignment
        native.partition.length contribution, row = loaded.row :=
  rowsBoundAt native.boundRows index row found

theorem fullPublicInputsAndNativeRowsShareFrame : native.frame = corpus.frame ∧
    readField authority.value "inputs" = some authority.encoded.value ∧ p.block.data.rows = native.rows :=
  ⟨p.frame,PublicAuthority.authorityHasAllCheckedInputs authority,p.rows⟩

theorem missingAuthorityRejected (candidate : Value) (missing : readField candidate "authority" = none) :
    check authority native candidate = none := by
  cases outcome : check authority native candidate with
  | none => rfl
  | some checked =>
      have exactBody := fullBodyWasComputed authority native outcome
      rw [exactBody,exactFullAuthority] at missing
      contradiction

end Binding
end DeltaReduce.PublicParameterBody
