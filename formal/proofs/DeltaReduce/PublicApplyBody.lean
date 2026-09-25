import DeltaReduce.PublicApplyArithmetic

/-! Complete computed leaf/aggregate/APPLY values. Configuration and identity
authentication remain independent premises; this is not phase/QC refinement. -/
namespace DeltaReduce.PublicApplyBody
open NativeBinding NativeInputProjection PublicState PublicArithmeticInputs PublicAuthority

def aggregateFieldNames : List String := ["apc","arithmeticProfile","canonicalRoot","coefficientProfile",
  "config","ec","isc","leaves","parent","round","schema","seed"]
def applyFieldNames : List String := ["aggregate","applyProfile","authority","checked","config",
  "nextCheckpoint","nextModelHash","nextOptimizerHash","parent","round"]

def aggregateFields (apc profile coefficient config ec isc parent round schema seed : Value)
    (leaves : List Value) : List (String × Value) :=
  [("apc",apc),("arithmeticProfile",profile),("canonicalRoot",setValue leaves),
   ("coefficientProfile",coefficient),("config",config),("ec",ec),("isc",isc),("leaves",setValue leaves),
   ("parent",parent),("round",round),("schema",schema),("seed",seed)]

def applyFields (aggregate profile authority config checkpoint model optimizer parent round : Value) :
    List (String × Value) :=
  [("aggregate",aggregate),("applyProfile",profile),("authority",authority),("checked",.boolean true),
   ("config",config),("nextCheckpoint",checkpoint),("nextModelHash",model),("nextOptimizerHash",optimizer),
   ("parent",parent),("round",round)]

section Leaves
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : Corpus binding} {limit : ModelLimit} {input : Projected corpus limit}
    {vocabulary : Vocabulary} {metadataTrust} {source : Metadata metadataTrust}
    (authority : PublicAuthority.Projection input vocabulary source)

inductive Leaves (authority : PublicAuthority.Projection input vocabulary source) : List (BoundParameter binding) → List Value → Type where
  | nil : Leaves authority [] []
  | cons {entry entries values}
      (head : PublicParameterBody.Projection (corpus := corpus) (limit := limit)
        (vocabulary := vocabulary) entry.result)
      (tail : Leaves authority entries values) :
      Leaves authority (entry :: entries) (head.value authority :: values)

def projectLeaves (authority : PublicAuthority.Projection input vocabulary source) : (entries : List (BoundParameter binding)) →
    Option (Σ values, Leaves authority entries values)
  | [] => some ⟨[],.nil⟩
  | entry :: entries => do
      let head ← PublicParameterBody.project (corpus := corpus) (limit := limit)
        (vocabulary := vocabulary) entry.result
      let tail ← projectLeaves authority entries
      some ⟨head.value authority :: tail.1,.cons head tail.2⟩

theorem leavesRetainCount {entries values} (bound : Leaves authority entries values) :
    values.length = entries.length := by
  induction bound with
  | nil => rfl
  | cons head tail ih => simp [ih]

theorem everyLeafComputed {entries values} (bound : Leaves authority entries values)
    (index : Nat) (value : Value) (found : values[index]? = some value) :
    ∃ entry, entries[index]? = some entry ∧
      ∃ p : PublicParameterBody.Projection (corpus := corpus) (limit := limit)
        (vocabulary := vocabulary) entry.result, value = p.value authority := by
  induction bound generalizing index with
  | nil => simp at found
  | @cons entry entries values head tail ih =>
      cases index with
      | zero =>
          simp only [List.getElem?_cons_zero,Option.some.injEq] at found
          exact ⟨entry,rfl,head,found.symm⟩
      | succ index => exact ih index found

theorem leavesShareEntireAuthority {entries values} (bound : Leaves authority entries values) :
    ∀ value ∈ values, readField value "authority" = some authority.value ∧
      readField value "apc" = some authority.apc := by
  induction bound with
  | nil => simp
  | cons head tail ih =>
      intro value member
      rcases List.mem_cons.mp member with same | member
      · subst value; exact ⟨rfl,rfl⟩
      · exact ih value member

end Leaves

section Checkpoint
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    (mapping : IdentityMap) (expected : Value) (native : NativeApply binding)

-- expected is the separate configuration's primitive ExpectedNextCheckpoint,
-- never a name read out of the candidate body. IdentityMap authentication and
-- correspondence to that configuration are deliberately not proved here.
structure Checkpoint : Type where
  symbol : String
  configured : expected = .model symbol
  nativeIdentity : (mapping.checkpoint expected).map asciiBytes = some (idBytes native.body.nextModelHash)

def checkCheckpoint : Option (Checkpoint mapping expected native) :=
  match shape : expected with
  | .model symbol =>
      if checked : (mapping.checkpoint expected).map asciiBytes = some (idBytes native.body.nextModelHash) then
        some ⟨symbol,rfl,by simpa only [shape] using checked⟩
      else none
  | _ => none

theorem checkpointUsesComputedModelHash (checked : Checkpoint mapping expected native) :
    (mapping.checkpoint expected).map asciiBytes = some (idBytes (codec.valueHash .model native.body.nextModel)) :=
  checked.nativeIdentity

theorem wrongCheckpointIdentityRejects (wrong : (mapping.checkpoint expected).map asciiBytes ≠ some (idBytes native.body.nextModelHash)) :
    checkCheckpoint mapping expected native = none := by
  unfold checkCheckpoint
  split <;> simp_all

end Checkpoint

section Projection
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : Corpus binding} {limit : ModelLimit} {input : Projected corpus limit}
    {vocabulary : Vocabulary} {metadataTrust} {source : Metadata metadataTrust}
    (authority : PublicAuthority.Projection input vocabulary source)
    (mapping : IdentityMap) (expected : Value) (native : NativeApply binding)

structure Projection where
  math : PublicApplyArithmetic.Checked native limit
  frame : native.core.conversion.certified.corpus.frame = corpus.frame
  leaves : List Value
  origin : Leaves authority native.core.conversion.certified.corpus.entries leaves
  scalar : NativeScalarProjection.Apply native
  model : Value
  modelEncoded : currentTable vocabulary.shard scalar.model.cells = some model
  optimizer : Value
  optimizerEncoded : currentTable vocabulary.shard scalar.optimizer.cells = some optimizer
  checkpoint : Checkpoint mapping expected native

def project : Option (Projection authority mapping expected native) := do
  if frame : native.core.conversion.certified.corpus.frame = corpus.frame then
    let leaves ← projectLeaves authority native.core.conversion.certified.corpus.entries
    let math ← PublicApplyArithmetic.check native limit
    let scalar ← NativeScalarProjection.applyResult native
    match modelEncoded : currentTable vocabulary.shard scalar.model.cells,
        optimizerEncoded : currentTable vocabulary.shard scalar.optimizer.cells with
    | some model, some optimizer => do
        let checkpoint ← checkCheckpoint mapping expected native
        some ⟨math,frame,leaves.1,leaves.2,scalar,model,modelEncoded,optimizer,optimizerEncoded,checkpoint⟩
    | _,_ => none
  else none

def Projection.aggregateFields (p : Projection authority mapping expected native) : List (String × Value) :=
  PublicApplyBody.aggregateFields authority.apc authority.header.profile.value authority.header.coefficient.value
    authority.header.config.value authority.ec authority.isc authority.header.parent.value authority.round
    authority.header.schema.value authority.seed p.leaves

def Projection.aggregate (p : Projection authority mapping expected native) : Value := record p.aggregateFields

def Projection.fields (p : Projection authority mapping expected native) : List (String × Value) :=
  applyFields p.aggregate authority.header.applyProfile.value authority.value authority.header.config.value expected
    (vectorValue "MODEL" authority.header.schema.value p.model)
    (vectorValue "OPTIMIZER" authority.header.schema.value p.optimizer) authority.header.parent.value authority.round

def Projection.value (p : Projection authority mapping expected native) : Value := record p.fields

structure Checked where
  projection : Projection authority mapping expected native
  canonical : PublicState.canonical vocabulary.models projection.value = true

def check (candidate : Value) : Option (Checked authority mapping expected native) := do
  let p ← project authority mapping expected native
  if valid : PublicState.canonical vocabulary.models p.value = true ∧ candidate = p.value then
    some ⟨p,valid.1⟩
  else none

theorem wholeApplyWasComputed {candidate checked}
    (accepted : check authority mapping expected native candidate = some checked) :
    candidate = checked.projection.value := by
  unfold check at accepted
  cases hp : project authority mapping expected native with
  | none => simp [hp] at accepted
  | some p =>
      simp only [hp,Bind.bind,Option.bind] at accepted
      split at accepted
      · rename_i valid; cases accepted; exact valid.2
      · contradiction

variable (p : Projection authority mapping expected native)

theorem exactAggregateInventory : p.aggregateFields.map Prod.fst = aggregateFieldNames := rfl
theorem exactApplyInventory : p.fields.map Prod.fst = applyFieldNames := rfl
theorem fullAuthorityAndAggregate : readField p.value "authority" = some authority.value ∧
    readField p.value "aggregate" = some p.aggregate := ⟨rfl,rfl⟩
theorem completeLeafCount : p.leaves.length = (expectedKeys corpus.frame binding.profile).length := by
  have keys := (parametersForSound native.core.conversion.certified.corpus.bound).1
  have lengths := congrArg List.length keys
  simpa only [List.length_map,p.frame,← leavesRetainCount authority p.origin] using lengths
theorem fullNativeCertifiedBodies :
    Resolves codec store native.core.conversion.certified.aggregate native.core.conversion.certified.bytes
      (.aggregate anchor.authority.id (native.core.conversion.certified.corpus.entries.map BoundParameter.body)) :=
  native.core.conversion.certified.resolved
theorem certificateUsesOriginalAnchor :
    anchor.aggregate = some native.core.conversion.certified.aggregate ∧
    trust.certificateAuthenticated native.core.conversion.certified.aggregate :=
  ⟨native.core.conversion.certified.anchored,native.core.conversion.certified.authenticated⟩
theorem everyPublicLeafHasOriginalSource (index : Nat) (value : Value)
    (found : p.leaves[index]? = some value) :
    ∃ entry, native.core.conversion.certified.corpus.entries[index]? = some entry ∧
      ∃ projected : PublicParameterBody.Projection (corpus := corpus) (limit := limit)
        (vocabulary := vocabulary) entry.result, value = projected.value authority :=
  everyLeafComputed authority p.origin index value found
theorem aggregatePreservesLeafSet : readField p.aggregate "leaves" = some (setValue p.leaves) ∧
    readField p.aggregate "canonicalRoot" = some (setValue p.leaves) := ⟨rfl,rfl⟩
theorem nextValuesFromActualNativeOutputs :
    currentTable vocabulary.shard p.scalar.model.cells = some p.model ∧
    currentTable vocabulary.shard p.scalar.optimizer.cells = some p.optimizer ∧
    p.math.arithmetic.nextModel = native.body.nextModel ∧
    p.math.arithmetic.nextOptimizer = native.body.nextOptimizer :=
  ⟨p.modelEncoded,p.optimizerEncoded,PublicApplyArithmetic.outputIdentity native limit p.math⟩
theorem noAssumedCheckpointName : readField p.value "nextCheckpoint" = some expected ∧
    (mapping.checkpoint expected).map asciiBytes = some (idBytes native.body.nextModelHash) := ⟨rfl,p.checkpoint.nativeIdentity⟩

theorem missingAuthorityRejected (candidate : Value) (missing : readField candidate "authority" = none) :
    check authority mapping expected native candidate = none := by
  cases outcome : check authority mapping expected native candidate with
  | none => rfl
  | some checked =>
      have same := wholeApplyWasComputed authority mapping expected native outcome
      rw [same,(fullAuthorityAndAggregate authority mapping expected native checked.projection).1] at missing
      contradiction

end Projection
end DeltaReduce.PublicApplyBody
