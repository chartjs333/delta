import DeltaReduce.NativeCurrentPointer
import DeltaReduce.ArithmeticBinding

/-! Original candidate value spellings and hashes checked against actual graph
computation. Shared numeric profile/context/leaf fields are compared explicitly.
Different native contract and draft artifact IDs are NOT identified here.
This is a partial source relation, not full arithmetic admission/refinement. -/
namespace DeltaReduce.NativeApplyResult
open NativeBinding
open NativeApplyCertificate (Candidate)

def decimalValues (values : List Int) : List Bytes := values.map (asciiBytes ∘ toString)
def rawValueInput (kind : Kind) (values : List Bytes) : Bytes :=
  asciiBytes (if kind = .model then "deltareduce.008.model.v1" else "deltareduce.008.optimizer.v1") ++
    [0] ++ values.flatMap (fun v => v ++ [59])
theorem exactValueInput (kind values) :
    rawValueInput kind (decimalValues values) = valueHashInput kind values := by
  simp only [rawValueInput,decimalValues,valueHashInput,List.flatMap_map,Function.comp_def]
theorem exactValueCount (values) : (decimalValues values).length = values.length := by
  simp only [decimalValues,List.length_map]
theorem exactValuePosition {values : List Int} {i : Nat} {n : Int}
    (h : values[i]? = some n) : (decimalValues values)[i]? = some (asciiBytes (toString n)) := by
  simp only [decimalValues,List.getElem?_map,h,Option.map_some,Function.comp_def]

-- A mathematical component; callers cannot use it as an authenticated source.
structure Values where
  model : List Int
  optimizer : List Int
  parentModel : List Int
  parentOptimizer : List Int
  deriving DecidableEq, Repr
structure Digests where
  model : Bytes
  optimizer : Bytes
  parentModel : Bytes
  parentOptimizer : Bytes
  deriving DecidableEq, Repr
def digests (sha : Bytes → Bytes) (v : Values) : Digests :=
  ⟨sha (valueHashInput .model v.model),sha (valueHashInput .optimizer v.optimizer),
   sha (valueHashInput .model v.parentModel),sha (valueHashInput .optimizer v.parentOptimizer)⟩
def DigestsValid (d : Digests) : Prop :=
  d.model.length = 32 ∧ d.optimizer.length = 32 ∧
  d.parentModel.length = 32 ∧ d.parentOptimizer.length = 32
instance (d) : Decidable (DigestsValid d) := by unfold DigestsValid; infer_instance
def ValueMatches (c : Candidate) (v : Values) (d : Digests) : Prop :=
  c.modelValues = decimalValues v.model ∧ c.optimizerValues = decimalValues v.optimizer ∧
  c.model = idBytes d.model ∧ c.optimizer = idBytes d.optimizer ∧
  c.parent = idBytes d.parentModel ∧ c.parentOptimizer = idBytes d.parentOptimizer
instance (c v d) : Decidable (ValueMatches c v d) := by unfold ValueMatches; infer_instance
def checkValues (sha : Bytes → Bytes) (v : Values) (c : Candidate) : Option Digests :=
  let d := digests sha v
  if DigestsValid d ∧ ValueMatches c v d then some d else none
theorem checkedValues {sha v c d} (h : checkValues sha v c = some d) :
    d = digests sha v ∧ DigestsValid d ∧ ValueMatches c v d := by
  unfold checkValues at h
  dsimp only at h
  split at h <;> try contradiction
  cases Option.some.inj h
  exact ⟨rfl,by assumption⟩
theorem valuesFromComponents {sha v c}
    (h : DigestsValid (digests sha v) ∧ ValueMatches c v (digests sha v)) :
    checkValues sha v c = some (digests sha v) := if_pos h
theorem valuePreimages {sha v c d} (h : checkValues sha v c = some d) :
    c.model = idBytes (sha (rawValueInput .model c.modelValues)) ∧
    c.optimizer = idBytes (sha (rawValueInput .optimizer c.optimizerValues)) := by
  obtain ⟨rfl,_,hm,ho,hmi,hoi,_⟩ := checkedValues h
  rw [hm,ho,exactValueInput,exactValueInput]
  exact ⟨hmi,hoi⟩
theorem valueLengths {sha v c d} (h : checkValues sha v c = some d) :
    c.modelValues.length = v.model.length ∧ c.optimizerValues.length = v.optimizer.length := by
  have checked := (checkedValues h).2.2
  rw [checked.1,checked.2.1,exactValueCount,exactValueCount]
  exact ⟨rfl,rfl⟩
theorem changedValuesReject {sha v c} (different : c.modelValues ≠ decimalValues v.model) :
    checkValues sha v c = none := by
  unfold checkValues
  apply if_neg
  intro h
  exact different h.2.1
theorem changedParentOptimizerReject {sha v c}
    (different : c.parentOptimizer ≠ idBytes (digests sha v).parentOptimizer) :
    checkValues sha v c = none := by
  unfold checkValues
  apply if_neg
  intro h
  exact different h.2.2.2.2.2.2

def fraction (f : NativeApplyProfile.Fraction) : Rational := ⟨f.numerator,f.denominator⟩
def weights (p : NativeApplyProfile.Profile) : List (Bytes × Rational) :=
  p.weights.map (fun w => (w.domain,fraction w.fraction))
def ProfileMatches (p : NativeApplyProfile.Profile) (q : Profile) : Prop :=
  weights p = q.domainWeights.map (fun w => (asciiBytes w.domain,w.weight)) ∧
  fraction p.learning = q.learningRate ∧ fraction p.momentum = q.momentum ∧
  fraction p.decay = q.weightDecay ∧ p.rounding = asciiBytes q.rounding ∧
  p.nesterov = 1 ∧ q.nesterov = true
instance (p q) : Decidable (ProfileMatches p q) := by unfold ProfileMatches; infer_instance
theorem profileWeightPosition {p q} (h : ProfileMatches p q) (i : Nat) :
    (weights p)[i]? = (q.domainWeights.map (fun w => (asciiBytes w.domain,w.weight)))[i]? :=
  congrArg (fun xs => xs[i]?) h.1
def SharedContext (c : NativeInputSetBody.Context) (a : Context) : Prop :=
  c.round = asciiBytes a.round ∧ c.height = a.height ∧ c.view = a.view ∧ c.epoch = asciiBytes a.epoch
instance (c a) : Decidable (SharedContext c a) := by unfold SharedContext; infer_instance

-- Every selected original ROOT leaf is compared in original order, but the
-- independent ISC/EC/APC/Q-artifact identity bridge is deliberately still open.
structure LeafNumbers where
  domain : Bytes
  shard : Bytes
  denominator : Int
  numerators : List Bytes
  deriving DecidableEq, Repr
def originalLeaf (e : NativeParameterLineage.Edge) : LeafNumbers :=
  ⟨e.certificate.common.domain,e.certificate.common.shard,e.certificate.common.denominator,
    e.certificate.common.numerators⟩
def derivedLeaf (p : ParameterBody) : LeafNumbers :=
  ⟨asciiBytes p.domain,asciiBytes p.shard,p.denominator,decimalValues p.numerators⟩
def LeafMatches (original : List NativeParameterLineage.Edge) (computed : List ParameterBody) : Prop :=
  original.map originalLeaf = computed.map derivedLeaf
instance (original computed) : Decidable (LeafMatches original computed) := by unfold LeafMatches; infer_instance
theorem leafCounts {original computed} (h : LeafMatches original computed) :
    original.length = computed.length := by simpa using congrArg List.length h
theorem leafPosition {original computed} (h : LeafMatches original computed) (i : Nat) :
    (original.map originalLeaf)[i]? = (computed.map derivedLeaf)[i]? :=
  congrArg (fun xs => xs[i]?) h

section Native
variable {codec store trust anchor} (binding : Binding codec trust anchor store)
def nativeValues (r : NativeApply binding) : Values :=
  ⟨r.body.nextModel,r.body.nextOptimizer,binding.model.values,binding.optimizer.values⟩
def AnchorMatches (d : Digests) (r : NativeApply binding) : Prop :=
  d.model = r.body.nextModelHash ∧ d.optimizer = r.body.nextOptimizerHash ∧
  d.parentModel = anchor.currentModelHash ∧ d.parentOptimizer = anchor.currentOptimizerHash ∧
  asciiBytes anchor.context.parentCheckpoint = idBytes d.parentModel
instance (d r) : Decidable (AnchorMatches binding d r) := by unfold AnchorMatches; infer_instance
def SharedMatches (r : NativeApply binding) (e : NativeApplyLineage.Edge) : Prop :=
  SharedContext e.decoded.candidate.context anchor.context ∧
  ProfileMatches e.profile.profile binding.profile ∧
  LeafMatches e.root.shards (r.core.conversion.certified.corpus.entries.map BoundParameter.body)
instance (r e) : Decidable (SharedMatches binding r e) := by unfold SharedMatches; infer_instance
structure Checked where
  result : NativeApply binding
  hashes : Digests
def fromComputed (sha : Bytes → Bytes) (r : NativeApply binding) (e : NativeApplyLineage.Edge) :
    Option (Checked binding) := do
  let hashes ← checkValues sha (nativeValues binding r) e.decoded.candidate
  if AnchorMatches binding hashes r ∧ SharedMatches binding r e then some ⟨r,hashes⟩ else none
def check (sha : Bytes → Bytes) (e : NativeApplyLineage.Edge) : Option (Checked binding) := do
  let r ← deriveNativeApply binding
  fromComputed binding sha r e
theorem computedSource {sha r e out} (h : fromComputed binding sha r e = some out) :
    out.result = r ∧ checkValues sha (nativeValues binding r) e.decoded.candidate = some out.hashes ∧
    AnchorMatches binding out.hashes r ∧ SharedMatches binding r e := by
  unfold fromComputed at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨hashes,hh,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨rfl,hh,by assumption⟩
theorem checkedSource {sha e out} (h : check binding sha e = some out) :
    deriveNativeApply binding = some out.result ∧
    checkValues sha (nativeValues binding out.result) e.decoded.candidate = some out.hashes ∧
    AnchorMatches binding out.hashes out.result ∧ SharedMatches binding out.result e := by
  unfold check at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨r,hr,hc⟩ := h
  obtain ⟨same,values,rest⟩ := computedSource binding hc
  rw [same]
  exact ⟨hr,values,rest⟩
theorem checkFromComponents {sha e r d} (derived : deriveNativeApply binding = some r)
    (values : checkValues sha (nativeValues binding r) e.decoded.candidate = some d)
    (checked : AnchorMatches binding d r ∧ SharedMatches binding r e) :
    check binding sha e = some ⟨r,d⟩ := by
  simp only [check,derived,fromComputed,values,bind,Option.bind,if_pos checked]
theorem exactComputedValues {sha e out} (h : check binding sha e = some out) :
    e.decoded.candidate.modelValues = decimalValues out.result.body.nextModel ∧
    e.decoded.candidate.optimizerValues = decimalValues out.result.body.nextOptimizer := by
  have h := (checkedValues (checkedSource binding h).2.1).2.2
  exact ⟨h.1,h.2.1⟩
theorem exactComputedHashes {sha e out} (h : check binding sha e = some out) :
    e.decoded.candidate.model = idBytes out.result.body.nextModelHash ∧
    e.decoded.candidate.optimizer = idBytes out.result.body.nextOptimizerHash ∧
    e.decoded.candidate.parent = idBytes anchor.currentModelHash ∧
    e.decoded.candidate.parentOptimizer = idBytes anchor.currentOptimizerHash := by
  have src := checkedSource binding h
  have values := (checkedValues src.2.1).2.2
  exact ⟨values.2.2.1.trans (congrArg idBytes src.2.2.1.1),
    values.2.2.2.1.trans (congrArg idBytes src.2.2.1.2.1),
    values.2.2.2.2.1.trans (congrArg idBytes src.2.2.1.2.2.1),
    values.2.2.2.2.2.trans (congrArg idBytes src.2.2.1.2.2.2.1)⟩
theorem outputBounds {sha e out} (h : check binding sha e = some out) :
    e.decoded.candidate.modelValues.length = binding.model.values.length ∧
    e.decoded.candidate.optimizerValues.length = binding.model.values.length ∧
    ∀ v ∈ out.result.body.nextModel ++ out.result.body.nextOptimizer, Fits minInput maxInput v := by
  have lengths := valueLengths (checkedSource binding h).2.1
  have bounds := nativeApplyOutputBounds out.result
  exact ⟨lengths.1.trans bounds.1,lengths.2.trans bounds.2.1,bounds.2.2⟩
end Native
end DeltaReduce.NativeApplyResult
