import FamilyApplyArithmetic
import FamilyGuards
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
/- Original native objects are retained in this direct constructor path. It
avoids the older draft graph layout/name/signed-denominator adapters. ROOT body
construction is separate from later conversion/optimizer success. -/
section OriginalBodies
variable {source indices profile quantum current vocabulary configured names earlyTrust planningTrust metadata selected}
    (authority : FamilyAuthority.Original source indices profile quantum current vocabulary configured names
      (earlyTrust := earlyTrust) (planningTrust := planningTrust) metadata selected)
    (nativeShardAlias : Bytes → Option String)

structure OriginalEntry where
  native : NativeParameterLineage.Edge
  leaf : FamilyParameter.OriginalLeaf authority nativeShardAlias native

def loadOriginalEntry (native : NativeParameterLineage.Edge) : Option (OriginalEntry authority nativeShardAlias) := do
  let leaf ← FamilyParameter.loadOriginalLeaf authority nativeShardAlias native
  some ⟨native,leaf⟩

def OriginalEntry.value (entry : OriginalEntry authority nativeShardAlias) : Value :=
  entry.leaf.value authority nativeShardAlias entry.native

def loadOriginalEntries (originals : List NativeParameterLineage.Edge) :
    Option (List (OriginalEntry authority nativeShardAlias)) :=
  collect (loadOriginalEntry authority nativeShardAlias) originals

theorem originalEntrySource {native entry} (loaded : loadOriginalEntry authority nativeShardAlias native = some entry) :
    entry.native = native := by
  simp only [loadOriginalEntry,bind,Option.bind_eq_some_iff] at loaded
  obtain ⟨_,_,last⟩ := loaded
  cases Option.some.inj last; rfl

theorem originalEntriesExact {originals entries}
    (loaded : loadOriginalEntries authority nativeShardAlias originals = some entries) :
    entries.map OriginalEntry.native = originals := by
  have keys := FamilyInputs.collectedKeys loaded (left := fun x => x) (right := OriginalEntry.native)
    (fun _ _ h => originalEntrySource authority nativeShardAlias h)
  exact keys.trans (List.map_id originals)

def originalAggregateFields (entries : List (OriginalEntry authority nativeShardAlias)) : List (String × Value) :=
  PublicApplyBody.aggregateFields authority.parents.value authority.header.arithmetic.value authority.parents.coefficient.value
    authority.parents.ec.parent.header.config.value authority.parents.ec.value authority.parents.ec.parent.value
    authority.header.parent.value authority.parents.ec.parent.header.round authority.header.schema.value
    authority.parents.ec.seedValue (entries.map (OriginalEntry.value authority nativeShardAlias))

def originalAggregate (entries : List (OriginalEntry authority nativeShardAlias)) : Value :=
  record (originalAggregateFields authority nativeShardAlias entries)

structure OriginalRoot (native : NativeAggregateLineage.Edge) where
  entries : List (OriginalEntry authority nativeShardAlias)
  computed : loadOriginalEntries authority nativeShardAlias native.shards = some entries
  parent : native.plan.id = source.source.plan.members.edge.id

def loadOriginalRoot (native : NativeAggregateLineage.Edge) : Option (OriginalRoot authority nativeShardAlias native) := do
  if parent : native.plan.id = source.source.plan.members.edge.id then
    match computed : loadOriginalEntries authority nativeShardAlias native.shards with
    | none => none
    | some entries => some ⟨entries,computed,parent⟩
  else none

theorem originalRootExact {native} (root : OriginalRoot authority nativeShardAlias native) :
    root.entries.map OriginalEntry.native = native.shards :=
  originalEntriesExact authority nativeShardAlias root.computed

theorem originalRootLoaded {native} (root : OriginalRoot authority nativeShardAlias native) :
    loadOriginalRoot authority nativeShardAlias native = some root := by
  unfold loadOriginalRoot
  rw [dif_pos root.parent]
  split
  · rename_i absent; simp [root.computed] at absent
  · rename_i entries computed
    have same := Option.some.inj (computed.symm.trans root.computed)
    subst entries; rfl

def originalConvertEntry (entry : OriginalEntry authority nativeShardAlias) : Option (List PlacedCell) := do
  let vector := entry.leaf.projection.vector
  let q := vector.first.quantum
  let values ← ParameterKernel.checkedConvertRows (-authority.input.image.limit-1) authority.input.image.limit
    source.source.plan.accumulator.numbers.denominator q.numerator q.denominator quantum.numerator quantum.denominator vector.values
  some (placeValues (NativeVectorLayout.text entry.native.certificate.common.domain) vector.first.block.header.start values)

def originalCells (entries : List (OriginalEntry authority nativeShardAlias)) : Option (List PlacedCell) := do
  let blocks ← collect (originalConvertEntry authority nativeShardAlias) entries
  some blocks.flatten

structure OriginalArithmetic (entries : List (OriginalEntry authority nativeShardAlias)) where
  cells : List PlacedCell
  converted : originalCells authority nativeShardAlias entries = some cells
  vectors : List (DomainVector cells current.model.length)
  domains : vectors.map (·.domain) = profile.profile.weights.map (fun w => NativeVectorLayout.text w.domain)
  rows : List ApplyKernel.DomainRow
  aligned : ApplyRows authority.input.image.profile.domainWeights (domainValues vectors) rows
  arithmetic : FamilyGuards.OriginalApplyMath profile.profile current.model current.optimizer rows

def loadOriginalArithmetic (entries : List (OriginalEntry authority nativeShardAlias)) :
    Option (OriginalArithmetic authority nativeShardAlias entries) := do
  match converted : originalCells authority nativeShardAlias entries with
  | none => none
  | some cells =>
    let vectors ← assembleDomains cells current.model.length (profile.profile.weights.map (fun w => NativeVectorLayout.text w.domain))
    let rows ← alignApplyRows authority.input.image.profile.domainWeights (domainValues vectors.val)
    let arithmetic ← FamilyGuards.checkOriginalApplyMath profile.profile current.model current.optimizer rows.val
    some ⟨cells,converted,vectors.val,vectors.property,rows.val,rows.property,arithmetic⟩

structure OriginalApply (sha : Bytes → Bytes) (checkpointNames : Value → Option Bytes) (expected : Value)
    (native : NativeApplyLineage.Edge) where
  root : OriginalRoot authority nativeShardAlias native.root
  arithmetic : OriginalArithmetic authority nativeShardAlias root.entries
  originalProfile : native.profile.id = profile.id ∧ native.profile.profile = profile.profile
  digests : NativeApplyResult.Digests
  values : NativeApplyResult.checkValues sha
    ⟨arithmetic.arithmetic.nextModel,arithmetic.arithmetic.nextOptimizer,current.model,current.optimizer⟩
    native.decoded.candidate = some digests
  checkpoint : checkpointNames expected = some native.decoded.candidate.model
  modelCells : List (String × Int)
  modelSource : FamilyInputs.selectOriginalCurrent source.first.corpus.manifest indices arithmetic.arithmetic.nextModel = some modelCells
  optimizerCells : List (String × Int)
  optimizerSource : FamilyInputs.selectOriginalCurrent source.first.corpus.manifest indices arithmetic.arithmetic.nextOptimizer = some optimizerCells
  model : Value
  modelEncoded : currentTable vocabulary.shard modelCells = some model
  optimizer : Value
  optimizerEncoded : currentTable vocabulary.shard optimizerCells = some optimizer

def loadOriginalApply (sha : Bytes → Bytes) (checkpointNames : Value → Option Bytes) (expected : Value)
    (native : NativeApplyLineage.Edge) : Option (OriginalApply authority nativeShardAlias sha checkpointNames expected native) := do
  let root ← loadOriginalRoot authority nativeShardAlias native.root
  let arithmetic ← loadOriginalArithmetic authority nativeShardAlias root.entries
  if originalProfile : native.profile.id = profile.id ∧ native.profile.profile = profile.profile then
    match values : NativeApplyResult.checkValues sha
        ⟨arithmetic.arithmetic.nextModel,arithmetic.arithmetic.nextOptimizer,current.model,current.optimizer⟩ native.decoded.candidate with
    | none => none
    | some digests =>
      if checkpoint : checkpointNames expected = some native.decoded.candidate.model then
        match ms : FamilyInputs.selectOriginalCurrent source.first.corpus.manifest indices arithmetic.arithmetic.nextModel,
            os : FamilyInputs.selectOriginalCurrent source.first.corpus.manifest indices arithmetic.arithmetic.nextOptimizer with
        | some modelCells,some optimizerCells =>
          match me : currentTable vocabulary.shard modelCells, oe : currentTable vocabulary.shard optimizerCells with
          | some model,some optimizer => some ⟨root,arithmetic,originalProfile,digests,values,checkpoint,
              modelCells,ms,optimizerCells,os,model,me,optimizer,oe⟩
          | _,_ => none
        | _,_ => none
      else none
  else none

def OriginalApply.fields {sha checkpointNames expected native}
    (p : OriginalApply authority nativeShardAlias sha checkpointNames expected native) : List (String × Value) :=
  PublicApplyBody.applyFields (originalAggregate authority nativeShardAlias p.root.entries) authority.header.apply.value
    authority.value authority.parents.ec.parent.header.config.value expected
    (vectorValue "MODEL" authority.header.schema.value p.model) (vectorValue "OPTIMIZER" authority.header.schema.value p.optimizer)
    authority.header.parent.value authority.parents.ec.parent.header.round

def OriginalApply.value {sha checkpointNames expected native}
    (p : OriginalApply authority nativeShardAlias sha checkpointNames expected native) : Value := record (p.fields authority nativeShardAlias)

theorem originalApplyFullNextVectors {sha checkpointNames expected native}
    (p : OriginalApply authority nativeShardAlias sha checkpointNames expected native) :
    native.decoded.candidate.modelValues = NativeApplyResult.decimalValues p.arithmetic.arithmetic.nextModel ∧
    native.decoded.candidate.optimizerValues = NativeApplyResult.decimalValues p.arithmetic.arithmetic.nextOptimizer :=
  ⟨(NativeApplyResult.checkedValues p.values).2.2.1,(NativeApplyResult.checkedValues p.values).2.2.2.1⟩

theorem originalApplyFieldInventory {sha checkpointNames expected native}
    (p : OriginalApply authority nativeShardAlias sha checkpointNames expected native) :
    (p.fields authority nativeShardAlias).map Prod.fst = PublicApplyBody.applyFieldNames := rfl

theorem originalAggregateCanonical (entries : List (OriginalEntry authority nativeShardAlias))
    (auth : canonical vocabulary.models authority.value = true)
    (atoms : ∀ n ∈ vocabulary.domains ++ vocabulary.shards, canonical vocabulary.models (.model n) = true)
    (unique : ((entries.map (OriginalEntry.value authority nativeShardAlias)).map encode).Nodup) :
    canonical vocabulary.models (originalAggregate authority nativeShardAlias entries) = true := by
  have leaves := FamilyAuthority.canonicalSet vocabulary.models (entries.map (OriginalEntry.value authority nativeShardAlias))
    (by
      intro value member
      obtain ⟨entry,_,rfl⟩ := List.mem_map.mp member
      exact FamilyParameter.originalBodyCanonical authority entry.native entry.leaf.block nativeShardAlias entry.leaf.projection auth
        (atoms _ (List.mem_append_left _ entry.leaf.projection.domainConfigured))
        (atoms _ (List.mem_append_right _ entry.leaf.projection.shardConfigured))) unique
  have apc := FamilyAuthority.canonicalField auth (show readField authority.value "apc" = some authority.parents.value from rfl)
  have ec := FamilyAuthority.canonicalField auth (show readField authority.value "ec" = some authority.parents.ec.value from rfl)
  have isc := FamilyAuthority.canonicalField auth (show readField authority.value "isc" = some authority.parents.ec.parent.value from rfl)
  have profile := FamilyAuthority.canonicalField auth (show readField authority.value "profile" = some authority.header.arithmetic.value from rfl)
  have coefficient := FamilyAuthority.canonicalField apc
    (show readField authority.parents.value "coefficientProfile" = some authority.parents.coefficient.value from rfl)
  have config := FamilyAuthority.canonicalField isc
    (show readField authority.parents.ec.parent.value "config" = some authority.parents.ec.parent.header.config.value from rfl)
  have parent := FamilyAuthority.canonicalField auth (show readField authority.value "parent" = some authority.header.parent.value from rfl)
  have round := FamilyAuthority.canonicalField isc
    (show readField authority.parents.ec.parent.value "round" = some authority.parents.ec.parent.header.round from rfl)
  have schema := FamilyAuthority.canonicalField auth (show readField authority.value "schema" = some authority.header.schema.value from rfl)
  have seed := FamilyAuthority.canonicalField ec (show readField authority.parents.ec.value "seed" = some authority.parents.ec.seedValue from rfl)
  apply FamilyAuthority.canonicalRecord
  · intro f member
    simp only [originalAggregateFields,PublicApplyBody.aggregateFields,List.mem_cons,List.not_mem_nil,or_false] at member
    rcases member with h|h|h|h|h|h|h|h|h|h|h|h
    all_goals subst f
    all_goals constructor
    all_goals first | assumption | (simp only [canonical]; try decide +kernel)
  · change ordered (PublicApplyBody.aggregateFieldNames.map (fun s => encode (.text s))) = true
    decide +kernel

theorem originalNextTablesCanonical {sha checkpointNames expected native}
    (p : OriginalApply authority nativeShardAlias sha checkpointNames expected native) :
    canonical vocabulary.models p.model = true ∧ canonical vocabulary.models p.optimizer = true := by
  have model := FamilyAuthority.canonicalField authority.input.encoded.canonical
    (show readField authority.input.encoded.value "model" = some (authority.input.encoded.components.at 9) from rfl)
  have optimizer := FamilyAuthority.canonicalField authority.input.encoded.canonical
    (show readField authority.input.encoded.value "optimizer" = some (authority.input.encoded.components.at 10) from rfl)
  have mt := componentIsComputed authority.input.encoded.components 9
  have ot := componentIsComputed authority.input.encoded.components 10
  change some (currentTable vocabulary.shard authority.input.image.model) = some (some (authority.input.encoded.components.at 9)) at mt
  change some (currentTable vocabulary.shard authority.input.image.optimizer) = some (some (authority.input.encoded.components.at 10)) at ot
  have names : authority.input.image.model.map Prod.fst = FamilyInputs.originalShardNames source.first.corpus.manifest ∧
      authority.input.image.optimizer.map Prod.fst = FamilyInputs.originalShardNames source.first.corpus.manifest := by
    have computed := authority.input.computed
    simp only [FamilyInputs.readOriginalImage,bind,Option.bind_eq_some_iff] at computed
    obtain ⟨tickets,_,ms,hm,os,ho,last⟩ := computed
    have image := Option.some.inj last
    rw [← image]
    exact ⟨FamilyInputs.originalCurrentKeys hm,FamilyInputs.originalCurrentKeys ho⟩
  exact ⟨FamilyAuthority.currentTableCanonicalSameKeys
      (names.1.trans (FamilyInputs.originalCurrentKeys p.modelSource).symm) (Option.some.inj mt) p.modelEncoded model,
    FamilyAuthority.currentTableCanonicalSameKeys
      (names.2.trans (FamilyInputs.originalCurrentKeys p.optimizerSource).symm) (Option.some.inj ot) p.optimizerEncoded optimizer⟩

theorem originalVectorCanonical {models : List String} (kind : String) (schema table : Value)
    (kindSafe : canonical models (.text kind) = true) (schemaSafe : canonical models schema = true)
    (tableSafe : canonical models table = true) : canonical models (vectorValue kind schema table) = true := by
  apply FamilyAuthority.canonicalRecord
  · intro field member
    simp only [List.mem_cons,List.not_mem_nil,or_false] at member
    rcases member with rfl | rfl | rfl
    all_goals constructor
    all_goals first | assumption | (simp only [canonical]; decide +kernel)
  · change ordered (["kind","schema","values"].map (fun s => encode (.text s))) = true
    decide +kernel

theorem originalApplyCanonical {sha checkpointNames expected native}
    (p : OriginalApply authority nativeShardAlias sha checkpointNames expected native)
    (auth : canonical vocabulary.models authority.value = true)
    (atoms : ∀ n ∈ vocabulary.domains ++ vocabulary.shards, canonical vocabulary.models (.model n) = true)
    (unique : ((p.root.entries.map (OriginalEntry.value authority nativeShardAlias)).map encode).Nodup)
    (checkpoint : canonical vocabulary.models expected = true) :
    canonical vocabulary.models (p.value authority nativeShardAlias) = true := by
  have aggregate := originalAggregateCanonical authority nativeShardAlias p.root.entries auth atoms unique
  have profile := FamilyAuthority.canonicalField auth (show readField authority.value "applyProfile" = some authority.header.apply.value from rfl)
  have isc := FamilyAuthority.canonicalField auth (show readField authority.value "isc" = some authority.parents.ec.parent.value from rfl)
  have config := FamilyAuthority.canonicalField isc
    (show readField authority.parents.ec.parent.value "config" = some authority.parents.ec.parent.header.config.value from rfl)
  have parent := FamilyAuthority.canonicalField auth (show readField authority.value "parent" = some authority.header.parent.value from rfl)
  have round := FamilyAuthority.canonicalField isc
    (show readField authority.parents.ec.parent.value "round" = some authority.parents.ec.parent.header.round from rfl)
  have schema := FamilyAuthority.canonicalField auth (show readField authority.value "schema" = some authority.header.schema.value from rfl)
  have tables := originalNextTablesCanonical authority nativeShardAlias p
  have model := originalVectorCanonical "MODEL" authority.header.schema.value p.model
    (by simp only [canonical]; decide +kernel) schema tables.1
  have optimizer := originalVectorCanonical "OPTIMIZER" authority.header.schema.value p.optimizer
    (by simp only [canonical]; decide +kernel) schema tables.2
  apply FamilyAuthority.canonicalRecord
  · intro field member
    simp only [OriginalApply.fields,PublicApplyBody.applyFields,List.mem_cons,List.not_mem_nil,or_false] at member
    rcases member with h|h|h|h|h|h|h|h|h|h
    all_goals subst field
    all_goals constructor
    all_goals first | assumption | (simp only [canonical]; try decide +kernel)
  · change ordered (PublicApplyBody.applyFieldNames.map (fun s => encode (.text s))) = true
    decide +kernel

def checkOriginalApply (sha : Bytes → Bytes) (checkpointNames : Value → Option Bytes) (expected : Value)
    (native : NativeApplyLineage.Edge) (candidate : Value) :
    Option (OriginalApply authority nativeShardAlias sha checkpointNames expected native) := do
  let p ← loadOriginalApply authority nativeShardAlias sha checkpointNames expected native
  if canonical vocabulary.models (p.value authority nativeShardAlias) = true ∧ candidate = p.value authority nativeShardAlias then
    some p else none

theorem originalApplyWholeCandidate {sha checkpointNames expected native candidate p}
    (accepted : checkOriginalApply authority nativeShardAlias sha checkpointNames expected native candidate = some p) :
    candidate = p.value authority nativeShardAlias := by
  simp only [checkOriginalApply,bind,Option.bind_eq_some_iff] at accepted
  obtain ⟨out,_,last⟩ := accepted
  split at last <;> try contradiction
  rename_i valid
  cases Option.some.inj last
  exact valid.2

theorem originalUniqueCellLoaded {cells domain coordinate value}
    (present : cellsAt cells domain coordinate = [⟨domain,coordinate,value⟩]) :
    uniqueCell cells domain coordinate = some ⟨value,present⟩ := by
  let scan (xs : List PlacedCell) : Option {v : Int // xs = [⟨domain,coordinate,v⟩]} :=
    match observed : xs with
    | [cell] => if unique : xs = [⟨domain,coordinate,cell.value⟩] then
        some ⟨cell.value,by simpa only [observed] using unique⟩ else none
    | _ => none
  have general : ∀ xs (same : xs = [⟨domain,coordinate,value⟩]), scan xs = some ⟨value,same⟩ := by
    intro xs same
    subst xs
    simp only [scan,dif_pos rfl]
  exact general _ present

theorem originalPlacedCoordinatesLoaded {cells domain coordinates values}
    (placed : PlacedCoordinates cells domain coordinates values) :
    placeCoordinates cells domain coordinates = some ⟨values,placed⟩ := by
  induction placed with
  | nil => rfl
  | cons unique tail ih =>
    simp only [placeCoordinates,originalUniqueCellLoaded unique,ih,bind,Option.bind]

theorem originalDomainVectorsLoaded {cells width} (vectors : List (DomainVector cells width))
    {domains : List String} (names : vectors.map (·.domain) = domains) :
    assembleDomains cells width domains = some ⟨vectors,names⟩ := by
  subst domains
  induction vectors with
  | nil => rfl
  | cons vector vectors ih =>
    simp only [List.map_cons,assembleDomains,originalPlacedCoordinatesLoaded vector.placed,ih,bind,Option.bind]

theorem originalApplyRowsLoaded {weights vectors rows} (aligned : ApplyRows weights vectors rows) :
    alignApplyRows weights vectors = some ⟨rows,aligned⟩ := by
  induction aligned with
  | nil => rfl
  | cons name tail ih => simp only [alignApplyRows,dif_pos name,ih,bind,Option.bind]

theorem originalArithmeticLoaded {entries} (p : OriginalArithmetic authority nativeShardAlias entries) :
    loadOriginalArithmetic authority nativeShardAlias entries = some p := by
  unfold loadOriginalArithmetic
  split
  · rename_i absent; simp [p.converted] at absent
  · rename_i cells computed
    have same := Option.some.inj (computed.symm.trans p.converted)
    subst cells
    rw [originalDomainVectorsLoaded p.vectors p.domains]
    simp only [bind,Option.bind,originalApplyRowsLoaded p.aligned,FamilyGuards.originalApplyMathTotal p.arithmetic]

theorem originalApplyLoaded {sha checkpointNames expected native}
    (p : OriginalApply authority nativeShardAlias sha checkpointNames expected native) :
    loadOriginalApply authority nativeShardAlias sha checkpointNames expected native = some p := by
  unfold loadOriginalApply
  rw [originalRootLoaded authority nativeShardAlias p.root]
  simp only [bind,Option.bind,originalArithmeticLoaded authority nativeShardAlias p.arithmetic]
  rw [dif_pos p.originalProfile]
  split
  · rename_i absent; simp [p.values] at absent
  · rename_i digests computed
    have same := Option.some.inj (computed.symm.trans p.values)
    subst digests
    rw [dif_pos p.checkpoint]
    split
    · rename_i modelCells optimizerCells hm ho
      have sameM := Option.some.inj (hm.symm.trans p.modelSource)
      have sameO := Option.some.inj (ho.symm.trans p.optimizerSource)
      subst modelCells; subst optimizerCells
      split
      · rename_i model optimizer hm ho
        have sameM := Option.some.inj (hm.symm.trans p.modelEncoded)
        have sameO := Option.some.inj (ho.symm.trans p.optimizerEncoded)
        subst model; subst optimizer; rfl
      · simp_all [p.modelEncoded,p.optimizerEncoded]
    · simp_all [p.modelSource,p.optimizerSource]

theorem originalApplyCheckedFromConstructed {sha checkpointNames expected native}
    (p : OriginalApply authority nativeShardAlias sha checkpointNames expected native)
    (auth : canonical vocabulary.models authority.value = true)
    (atoms : ∀ n ∈ vocabulary.domains ++ vocabulary.shards, canonical vocabulary.models (.model n) = true)
    (unique : ((p.root.entries.map (OriginalEntry.value authority nativeShardAlias)).map encode).Nodup)
    (checkpoint : canonical vocabulary.models expected = true) :
    checkOriginalApply authority nativeShardAlias sha checkpointNames expected native (p.value authority nativeShardAlias) = some p := by
  have safe := originalApplyCanonical authority nativeShardAlias p auth atoms unique checkpoint
  simp only [checkOriginalApply,originalApplyLoaded authority nativeShardAlias p,bind,Option.bind]
  exact if_pos ⟨safe,by trivial⟩

theorem originalConversionPublicGuards (entry : OriginalEntry authority nativeShardAlias) {cells}
    (loaded : originalConvertEntry authority nativeShardAlias entry = some cells)
    {coordinate : Nat} {numerator : Int} (atNumerator : entry.leaf.projection.vector.values[coordinate]? = some numerator) :
    ∃ values value,
      cells = placeValues (NativeVectorLayout.text entry.native.certificate.common.domain)
        entry.leaf.projection.vector.first.block.header.start values ∧
      values[coordinate]? = some value ∧
      FamilyGuards.PublicConversion authority.input.image.limit numerator
        source.source.plan.accumulator.numbers.denominator entry.leaf.projection.vector.first.quantum.numerator
        entry.leaf.projection.vector.first.quantum.denominator quantum.numerator quantum.denominator value := by
  simp only [originalConvertEntry,bind,Option.bind_eq_some_iff] at loaded
  obtain ⟨values,converted,last⟩ := loaded
  cases Option.some.inj last
  have checked := ParameterKernel.checkedConvertRowsSound _ _ _ _ _ _ _ _ _ converted
  obtain ⟨value,atValue,safe⟩ := FamilyGuards.conversionCoordinate checked.2.1 atNumerator
  exact ⟨values,value,rfl,atValue,safe.2⟩

theorem originalEveryEntryConverted {entries} (p : OriginalArithmetic authority nativeShardAlias entries) :
    ∀ entry ∈ entries, ∃ cells, originalConvertEntry authority nativeShardAlias entry = some cells := by
  have computed := p.converted
  simp only [originalCells,bind,Option.bind_eq_some_iff] at computed
  obtain ⟨blocks,converted,_⟩ := computed
  intro entry member
  obtain ⟨cells,_,loaded⟩ := FamilyInputs.collectInputHasOutput converted member
  exact ⟨cells,loaded⟩

theorem originalEmbeddedCurrentSource :
    FamilyInputs.selectOriginalCurrent source.first.corpus.manifest indices current.model = some authority.input.image.model ∧
    FamilyInputs.selectOriginalCurrent source.first.corpus.manifest indices current.optimizer = some authority.input.image.optimizer := by
  have computed := authority.input.computed
  simp only [FamilyInputs.readOriginalImage,bind,Option.bind_eq_some_iff] at computed
  obtain ⟨_,_,_,hm,_,ho,last⟩ := computed
  rw [← Option.some.inj last]
  exact ⟨hm,ho⟩

/- One actual shard-local choice names the same global coordinate in current
inputs, all ordered domain rows and the computed next vectors. This is the
public scalar APPLY computation over the single original full-vector object. -/
theorem originalCoordinateComputesNextCells {sha checkpointNames expected native}
    (p : OriginalApply authority nativeShardAlias sha checkpointNames expected native)
    (s : Fin source.first.corpus.manifest.blocks.length) {coordinate}
    (atIndex : indices[s.val]? = some coordinate) {value}
    (atValue : p.arithmetic.arithmetic.values[source.first.corpus.manifest.blocks[s.val].block.header.start+coordinate]? = some value) :
    ∃ theta momentum gradient total terms,
      authority.input.image.model[s.val]? = some (NativeVectorLayout.shardName source.first.corpus.manifest.blocks[s.val].block.header.ordinal,theta) ∧
      authority.input.image.optimizer[s.val]? = some (NativeVectorLayout.shardName source.first.corpus.manifest.blocks[s.val].block.header.ordinal,momentum) ∧
      p.modelCells[s.val]? = some (NativeVectorLayout.shardName source.first.corpus.manifest.blocks[s.val].block.header.ordinal,value.nextModel) ∧
      p.optimizerCells[s.val]? = some (NativeVectorLayout.shardName source.first.corpus.manifest.blocks[s.val].block.header.ordinal,value.nextOptimizer) ∧
      ApplyKernel.ColumnTerms (source.first.corpus.manifest.blocks[s.val].block.header.start+coordinate) p.arithmetic.rows terms ∧
      ApplyKernel.checkedMix minInput maxInput p.arithmetic.arithmetic.plan.denominator 0 terms = some total ∧
      gradient = round total p.arithmetic.arithmetic.plan.denominator ∧
      value = ApplyKernel.optimizerValues theta momentum gradient
        (NativeApplyResult.fraction profile.profile.learning).kernelWeight
        (NativeApplyResult.fraction profile.profile.momentum).kernelWeight
        (NativeApplyResult.fraction profile.profile.decay).kernelWeight := by
  obtain ⟨theta,momentum,gradient,total,terms,hm,ho,_,column,mix,rounded,computed⟩ :=
    FamilyGuards.originalApplyMathCoordinate p.arithmetic.arithmetic atValue
  have nextModel : p.arithmetic.arithmetic.nextModel[source.first.corpus.manifest.blocks[s.val].block.header.start+coordinate]? = some value.nextModel := by
    simp only [FamilyGuards.OriginalApplyMath.nextModel,List.getElem?_map,atValue,Option.map_some]
  have nextOptimizer : p.arithmetic.arithmetic.nextOptimizer[source.first.corpus.manifest.blocks[s.val].block.header.start+coordinate]? = some value.nextOptimizer := by
    simp only [FamilyGuards.OriginalApplyMath.nextOptimizer,List.getElem?_map,atValue,Option.map_some]
  have input := originalEmbeddedCurrentSource authority
  exact ⟨theta,momentum,gradient,total,terms,FamilyInputs.originalCurrentAt input.1 s atIndex hm,
    FamilyInputs.originalCurrentAt input.2 s atIndex ho,FamilyInputs.originalCurrentAt p.modelSource s atIndex nextModel,
    FamilyInputs.originalCurrentAt p.optimizerSource s atIndex nextOptimizer,column,mix,rounded,computed⟩

end OriginalBodies

end DeltaReduce.FamilyApply
