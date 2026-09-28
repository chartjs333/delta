import FamilyApplyArithmetic
import DeltaReduce.PublicApplyBody

/-! Complete public aggregate/APPLY view from one original certified vector
corpus. Coordinates are representation indices, not additional leaf/QC objects.
The checkpoint adapter is the existing explicitly conditional boundary. -/
namespace DeltaReduce.FamilyApply
open NativeBinding NativeInputProjection PublicState PublicArithmeticInputs PublicAuthority

section Construction
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : FamilyInputs.Corpus binding} {choice : FamilyInputs.Choice corpus.frame}
    {limit : Int} {input : FamilyInputs.Projected corpus choice limit}
    {vocabulary : Vocabulary} {metadataTrust} {source : Metadata metadataTrust}
    (authority : FamilyAuthority.Projection input vocabulary source) (resultBound : Int)

inductive Leaves (authority : FamilyAuthority.Projection input vocabulary source) (resultBound : Int) :
    List (BoundParameter binding) → List Value → Type where
  | nil : Leaves authority resultBound [] []
  | cons {entry entries values}
      (head : FamilyParameter.Projection (corpus := corpus) (choice := choice) (limit := limit)
        (vocabulary := vocabulary) resultBound entry.result)
      (tail : Leaves authority resultBound entries values) :
      Leaves authority resultBound (entry :: entries) (head.body authority :: values)

def projectLeaves : (entries : List (BoundParameter binding)) →
    Option (Σ values, Leaves authority resultBound entries values)
  | [] => some ⟨[],.nil⟩
  | entry :: entries => do
      let head ← FamilyParameter.project (corpus := corpus) (choice := choice) (limit := limit)
        (vocabulary := vocabulary) resultBound entry.result
      let tail ← projectLeaves entries
      some ⟨head.body authority :: tail.1,.cons head tail.2⟩

theorem leavesRetainCount {entries values} (bound : Leaves authority resultBound entries values) :
    values.length = entries.length := by
  induction bound with
  | nil => rfl
  | cons head tail ih => simp [ih]

theorem everyLeafComputed {entries values} (bound : Leaves authority resultBound entries values)
    (index : Nat) (value : Value) (found : values[index]? = some value) :
    ∃ entry, entries[index]? = some entry ∧
      ∃ p : FamilyParameter.Projection (corpus := corpus) (choice := choice) (limit := limit)
        (vocabulary := vocabulary) resultBound entry.result, value = p.body authority := by
  induction bound generalizing index with
  | nil => simp at found
  | @cons entry entries values head tail ih =>
    cases index with
    | zero => simp only [List.getElem?_cons_zero,Option.some.injEq] at found
              exact ⟨entry,rfl,head,found.symm⟩
    | succ index => exact ih index found

theorem allLeavesConstructible
    {input : FamilyInputs.Projected corpus choice (accumulatorHi binding.profile)}
    (authority : FamilyAuthority.Projection input vocabulary source)
    (entries : List (BoundParameter binding)) :
    ∃ result, projectLeaves authority (accumulatorHi binding.profile+1) entries = some result := by
  induction entries with
  | nil => exact ⟨⟨[],.nil⟩,rfl⟩
  | cons entry entries ih =>
    obtain ⟨head,hh⟩ := FamilyParameter.parameterFromAuthority authority entry.result
    obtain ⟨tail,ht⟩ := ih
    exact ⟨⟨head.body authority::tail.1,.cons head tail.2⟩,
      by simp only [projectLeaves,hh,ht,bind,Option.bind]⟩

theorem everyLeafCanonical {entries values} (bound : Leaves authority resultBound entries values)
    (auth : canonical vocabulary.models authority.value = true)
    (names : ∀ n ∈ vocabulary.domains ++ vocabulary.shards, canonical vocabulary.models (.model n) = true) :
    ∀ value ∈ values, canonical vocabulary.models value = true := by
  induction bound with
  | nil => simp
  | cons head tail ih =>
    intro value member
    rcases List.mem_cons.mp member with same | member
    · subst value
      exact FamilyParameter.constructedBodyCanonical authority resultBound _ head auth
        (names _ (List.mem_append_left _ head.domainConfigured))
        (names _ (List.mem_append_right _ head.shardConfigured))
    · exact ih value member

/- This is the existing canonical set condition, not a new protocol gate.
The original leaf list remains complete and ordered before set encoding. -/
theorem aggregateConstructedCanonical {entries values} (bound : Leaves authority resultBound entries values)
    (auth : canonical vocabulary.models authority.value = true)
    (names : ∀ n ∈ vocabulary.domains ++ vocabulary.shards, canonical vocabulary.models (.model n) = true)
    (uniqueBytes : (values.map PublicState.encode).Nodup) :
    canonical vocabulary.models (record (PublicApplyBody.aggregateFields authority.apc authority.header.profile.value
      authority.header.coefficient.value authority.header.config.value authority.ec authority.isc
      authority.header.parent.value authority.round authority.header.schema.value authority.seed values)) = true := by
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
  have leaves := FamilyAuthority.canonicalSet vocabulary.models values
    (everyLeafCanonical authority resultBound bound auth names) uniqueBytes
  apply FamilyAuthority.canonicalRecord
  · intro f member
    simp only [PublicApplyBody.aggregateFields,List.mem_cons,List.not_mem_nil,or_false] at member
    rcases member with h|h|h|h|h|h|h|h|h|h|h|h
    all_goals subst f
    all_goals constructor
    all_goals first | assumption | (simp only [canonical]; try decide +kernel)
  · change ordered (PublicApplyBody.aggregateFieldNames.map (fun s => PublicState.encode (.text s))) = true
    decide +kernel

variable (mapping : IdentityMap) (expected : Value) (native : NativeApply binding)

structure Projection where
  math : FamilyApplyArithmetic.Checked native limit
  frame : native.core.conversion.certified.corpus.frame = corpus.frame
  leaves : List Value
  origin : Leaves authority resultBound native.core.conversion.certified.corpus.entries leaves
  modelCells : List (String × Int)
  modelSource : FamilyInputs.selectedCurrent corpus.frame choice native.body.nextModel = some modelCells
  optimizerCells : List (String × Int)
  optimizerSource : FamilyInputs.selectedCurrent corpus.frame choice native.body.nextOptimizer = some optimizerCells
  model : Value
  modelEncoded : currentTable vocabulary.shard modelCells = some model
  optimizer : Value
  optimizerEncoded : currentTable vocabulary.shard optimizerCells = some optimizer
  checkpoint : PublicApplyBody.Checkpoint mapping expected native

def project : Option (Projection authority resultBound mapping expected native) := do
  if frame : native.core.conversion.certified.corpus.frame = corpus.frame then
    let leaves ← projectLeaves authority resultBound native.core.conversion.certified.corpus.entries
    let math ← FamilyApplyArithmetic.check native limit
    match hm : FamilyInputs.selectedCurrent corpus.frame choice native.body.nextModel,
        ho : FamilyInputs.selectedCurrent corpus.frame choice native.body.nextOptimizer with
    | some modelCells, some optimizerCells =>
      match em : currentTable vocabulary.shard modelCells, eo : currentTable vocabulary.shard optimizerCells with
      | some model, some optimizer =>
        let checkpoint ← PublicApplyBody.checkCheckpoint mapping expected native
        some ⟨math,frame,leaves.1,leaves.2,modelCells,hm,optimizerCells,ho,model,em,optimizer,eo,checkpoint⟩
      | _,_ => none
    | _,_ => none
  else none

def Projection.aggregateFields (p : Projection authority resultBound mapping expected native) : List (String × Value) :=
  PublicApplyBody.aggregateFields authority.apc authority.header.profile.value authority.header.coefficient.value
    authority.header.config.value authority.ec authority.isc authority.header.parent.value authority.round
    authority.header.schema.value authority.seed p.leaves
def Projection.aggregate (p : Projection authority resultBound mapping expected native) : Value := record p.aggregateFields
def Projection.fields (p : Projection authority resultBound mapping expected native) : List (String × Value) :=
  PublicApplyBody.applyFields p.aggregate authority.header.applyProfile.value authority.value authority.header.config.value expected
    (vectorValue "MODEL" authority.header.schema.value p.model)
    (vectorValue "OPTIMIZER" authority.header.schema.value p.optimizer) authority.header.parent.value authority.round
def Projection.value (p : Projection authority resultBound mapping expected native) : Value := record p.fields

structure Checked where
  projection : Projection authority resultBound mapping expected native
  canonical : PublicState.canonical vocabulary.models projection.value = true
def check (candidate : Value) : Option (Checked authority resultBound mapping expected native) := do
  let p ← project authority resultBound mapping expected native
  if valid : PublicState.canonical vocabulary.models p.value = true ∧ candidate = p.value then
    some ⟨p,valid.1⟩
  else none
theorem computedWholeBody {candidate checked}
    (h : check authority resultBound mapping expected native candidate = some checked) :
    candidate = checked.projection.value := by
  unfold check at h
  cases hp : project authority resultBound mapping expected native with
  | none => simp [hp] at h
  | some p =>
    simp only [hp,bind,Option.bind] at h
    split at h
    · rename_i valid; cases h; exact valid.2
    · contradiction

variable (p : Projection authority resultBound mapping expected native)
theorem allAggregateFields : p.aggregateFields.map Prod.fst = PublicApplyBody.aggregateFieldNames := rfl
theorem allApplyFields : p.fields.map Prod.fst = PublicApplyBody.applyFieldNames := rfl
theorem entireAuthorityAndAggregate : readField p.value "authority" = some authority.value ∧
    readField p.value "aggregate" = some p.aggregate := ⟨rfl,rfl⟩
theorem originalLeafCount : p.leaves.length = native.core.conversion.certified.corpus.entries.length :=
  leavesRetainCount authority resultBound p.origin
theorem originalCertifiedCorpus :
    Resolves codec store native.core.conversion.certified.aggregate native.core.conversion.certified.bytes
      (.aggregate anchor.authority.id (native.core.conversion.certified.corpus.entries.map BoundParameter.body)) :=
  native.core.conversion.certified.resolved
theorem originalCertificate : anchor.aggregate = some native.core.conversion.certified.aggregate ∧
    trust.certificateAuthenticated native.core.conversion.certified.aggregate :=
  ⟨native.core.conversion.certified.anchored,native.core.conversion.certified.authenticated⟩
theorem actualNextVectors :
    FamilyInputs.selectedCurrent corpus.frame choice native.body.nextModel = some p.modelCells ∧
    FamilyInputs.selectedCurrent corpus.frame choice native.body.nextOptimizer = some p.optimizerCells ∧
    p.math.arithmetic.nextModel = native.body.nextModel ∧ p.math.arithmetic.nextOptimizer = native.body.nextOptimizer :=
  ⟨p.modelSource,p.optimizerSource,FamilyApplyArithmetic.outputIdentity native limit p.math⟩
theorem noInventedCheckpoint : readField p.value "nextCheckpoint" = some expected ∧
    (mapping.checkpoint expected).map asciiBytes = some (idBytes native.body.nextModelHash) :=
  ⟨rfl,p.checkpoint.nativeIdentity⟩

/- Same original shard/global coordinate for embedded current input and computed
next output. The scalar operation result is derived, never supplied as an
expected vector equality, and no coordinate-level protocol object is created. -/
theorem coordinateComputesNextCells (s : Fin corpus.frame.shards.length) :
    ∃ theta momentum gradient nextModel nextOptimizer total terms,
      input.model[s.val]? = some (corpus.frame.shards[s.val].id,theta) ∧
      input.optimizer[s.val]? = some (corpus.frame.shards[s.val].id,momentum) ∧
      p.modelCells[s.val]? = some (corpus.frame.shards[s.val].id,nextModel) ∧
      p.optimizerCells[s.val]? = some (corpus.frame.shards[s.val].id,nextOptimizer) ∧
      ApplyKernel.ColumnTerms (corpus.frame.shards[s.val].offset+(choice s).val) native.core.rows terms ∧
      ApplyKernel.checkedMix (-limit-1) limit (Int.ofNat p.math.arithmetic.plan.denominator) 0 terms = some total ∧
      round total (Int.ofNat p.math.arithmetic.plan.denominator) = gradient ∧
      ApplyKernel.checkedOptimizer (-limit-1) limit theta momentum gradient
        binding.profile.learningRate.kernelWeight binding.profile.momentum.kernelWeight
        binding.profile.weightDecay.kernelWeight = some (nextModel,nextOptimizer) := by
  have shape := StateFamily.nativeModelShape native
  change binding.model.values.length = native.core.conversion.certified.corpus.frame.coordinates.length at shape
  rw [p.frame] at shape
  have inside : corpus.frame.shards[s.val].offset+(choice s).val < binding.model.values.length := by
    rw [shape]
    exact (StateFamily.globalIndex (StateFamily.ofValidated corpus.valid) s (choice s)).isLt
  obtain ⟨theta,momentum,g,n,o,total,terms,hm,ho,hg,hn,hno,column,mix,rounded,optimizer⟩ :=
    VectorShardRepresentation.applyCoordinateFromSameVector p.math.arithmetic _ inside
  have output := FamilyApplyArithmetic.outputIdentity native limit p.math
  rw [output.1] at hn
  rw [output.2] at hno
  exact ⟨theta,momentum,g,n,o,total,terms,
    FamilyInputs.selectedCurrentAt input.modelLoaded s hm,
    FamilyInputs.selectedCurrentAt input.optimizerLoaded s ho,
    FamilyInputs.selectedCurrentAt p.modelSource s hn,
    FamilyInputs.selectedCurrentAt p.optimizerSource s hno,column,mix,rounded,optimizer⟩

theorem nextTablesCanonical : canonical vocabulary.models p.model = true ∧
    canonical vocabulary.models p.optimizer = true := by
  have tables := FamilyAuthority.currentTablesFromBoundVectors authority
  have model := FamilyAuthority.canonicalField authority.encoded.canonical
    (show readField authority.encoded.value "model" = some (authority.encoded.components.at 9) from rfl)
  have optimizer := FamilyAuthority.canonicalField authority.encoded.canonical
    (show readField authority.encoded.value "optimizer" = some (authority.encoded.components.at 10) from rfl)
  have names := FamilyInputs.projectedCurrentNames input
  exact ⟨FamilyAuthority.currentTableCanonicalSameKeys
      (names.1.trans (FamilyInputs.selectedCurrentNames p.modelSource).symm) tables.1 p.modelEncoded model,
    FamilyAuthority.currentTableCanonicalSameKeys
      (names.2.trans (FamilyInputs.selectedCurrentNames p.optimizerSource).symm) tables.2 p.optimizerEncoded optimizer⟩

theorem constructedBodyCanonical
    (auth : canonical vocabulary.models authority.value = true)
    (names : ∀ n ∈ vocabulary.domains ++ vocabulary.shards, canonical vocabulary.models (.model n) = true)
    (uniqueBytes : (p.leaves.map PublicState.encode).Nodup)
    (checkpoint : canonical vocabulary.models expected = true) :
    canonical vocabulary.models p.value = true := by
  have aggregate := aggregateConstructedCanonical authority resultBound p.origin auth names uniqueBytes
  have profile := FamilyAuthority.canonicalField auth
    (show readField authority.value "applyProfile" = some authority.header.applyProfile.value from rfl)
  have isc := FamilyAuthority.canonicalField auth (show readField authority.value "isc" = some authority.isc from rfl)
  have config := FamilyAuthority.canonicalField isc (show readField authority.isc "config" = some authority.header.config.value from rfl)
  have parent := FamilyAuthority.canonicalField auth (show readField authority.value "parent" = some authority.header.parent.value from rfl)
  have round := FamilyAuthority.canonicalField isc (show readField authority.isc "round" = some authority.round from rfl)
  have schema := FamilyAuthority.canonicalField auth (show readField authority.value "schema" = some authority.header.schema.value from rfl)
  have tables := nextTablesCanonical authority resultBound mapping expected native p
  have vector (kind : String) (kindSafe : canonical vocabulary.models (.text kind) = true)
      (value : Value) (valueSafe : canonical vocabulary.models value = true) :
      canonical vocabulary.models (vectorValue kind authority.header.schema.value value) = true := by
    apply FamilyAuthority.canonicalRecord
    · intro field member
      simp only [List.mem_cons,List.not_mem_nil,or_false] at member
      rcases member with h|h|h
      all_goals subst field
      all_goals constructor
      all_goals first | assumption | (simp only [canonical]; decide +kernel)
    · change ordered (["kind","schema","values"].map (fun s => encode (.text s))) = true
      decide +kernel
  have model := vector "MODEL" (by simp only [canonical]; decide +kernel) p.model tables.1
  have optimizer := vector "OPTIMIZER" (by simp only [canonical]; decide +kernel) p.optimizer tables.2
  apply FamilyAuthority.canonicalRecord
  · intro field member
    simp only [Projection.fields,PublicApplyBody.applyFields,List.mem_cons,List.not_mem_nil,or_false] at member
    rcases member with h|h|h|h|h|h|h|h|h|h
    all_goals subst field
    all_goals constructor
    all_goals first | assumption | (simp only [canonical]; try decide +kernel)
  · change ordered (PublicApplyBody.applyFieldNames.map (fun s => encode (.text s))) = true
    decide +kernel

theorem checkedFromConstructed
    (constructed : project authority resultBound mapping expected native = some p)
    (auth : canonical vocabulary.models authority.value = true)
    (names : ∀ n ∈ vocabulary.domains ++ vocabulary.shards, canonical vocabulary.models (.model n) = true)
    (uniqueBytes : (p.leaves.map PublicState.encode).Nodup)
    (checkpoint : canonical vocabulary.models expected = true) :
    ∃ checked, check authority resultBound mapping expected native p.value = some checked ∧
      checked.projection = p := by
  have safe := constructedBodyCanonical authority resultBound mapping expected native p auth names uniqueBytes checkpoint
  unfold check
  rw [constructed]
  simp only [bind,Option.bind]
  rw [dif_pos ⟨safe,by trivial⟩]
  exact ⟨_,rfl,rfl⟩
end Construction
end DeltaReduce.FamilyApply
