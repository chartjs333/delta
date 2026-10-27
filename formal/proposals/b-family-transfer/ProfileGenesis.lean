import ProfileOrigin
import ProfileArithmeticUnits
import DeltaReduce.NativeCurrentValues

/-! T047/T053. Initial source value/unit binding under the existing independent
bootstrap. Whole native Init/history, certified imported floor and public-state
composition are NOT assumed or established here. No synthetic ApplyCandidate/QC
is created to load genesis values. Original bytes are checked in full. -/
namespace DeltaReduce.ProfileSource.Genesis
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ascii ContentId)
open NativeIscCertificate (object quoted array number)

structure Descriptor where
  semantics : Bytes
  origin : Bytes
  epoch : Bytes
  height : Nat
  modelValues : List Bytes
  optimizerValues : List Bytes
  deriving DecidableEq, Repr

def json (g : Descriptor) : Bytes := object [
  ("formal_semantics_id",quoted g.semantics),("height",quoted (number g.height)),
  ("model_values",array (g.modelValues.map quoted)),
  ("optimizer_values",array (g.optimizerValues.map quoted)),("origin_id",quoted g.origin),
  ("schema_version",quoted (ascii "1.0.0")),
  ("type_name",quoted (ascii "PROFILE_GENESIS_VALUES")),("validator_epoch_id",quoted g.epoch)]

structure Bound where
  original : Bytes
  initialConfiguration : Bytes
  initialUnits : Bytes
  units : ArithmeticUnits.Initial
  descriptor : Descriptor
  model : List Int
  optimizer : List Int
  current : NativeCurrentPointer.State

def Checks (sha : Bytes → Bytes) (origin : Origin.Bound) (g : Descriptor)
    (configuration : Control.Fields) (model optimizer : List Int) : Prop :=
  ContentId g.semantics ∧ g.semantics ≠ NativeVoteBytes.nativeSemantics ∧
  Index.text (Index.field origin.bootstrap.descriptor "formal_semantics_id") = some g.semantics ∧
  ContentId g.origin ∧ ContentId g.epoch ∧ g.origin = origin.bootstrap.origin.id ∧
  g.epoch = origin.bootstrap.origin.epoch ∧ g.height < 256^8 ∧
  0 < model.length ∧ model.length ≤ 100000 ∧ optimizer.length = model.length ∧
  (sha (NativeBinding.valueHashInput .model model)).length = 32 ∧
  (sha (NativeBinding.valueHashInput .optimizer optimizer)).length = 32 ∧
  origin.source.genesis = json g ∧ origin.source.genesis.length ≤ 64*1024^3 ∧
  Control.canonicalFields configuration = true ∧
  Control.encode (.object configuration) = origin.initialConfiguration ∧
  origin.initialConfiguration.length ≤ 4*1024*1024
instance (sha origin g configuration model optimizer) :
    Decidable (Checks sha origin g configuration model optimizer) := by
  unfold Checks; infer_instance

def pointer (sha : Bytes → Bytes) (g : Descriptor) (model optimizer : List Int) :
    NativeCurrentPointer.State :=
  ⟨NativeBinding.idBytes (sha (NativeBinding.valueHashInput .model model)),
   NativeBinding.idBytes (sha (NativeBinding.valueHashInput .optimizer optimizer)),[],g.height⟩

def bind (sha : Bytes → Bytes) (origin : Origin.Bound) (g : Descriptor)
    (configuration : Control.Fields) : Option Bound := do
  let model ← NativeCurrentValues.readValues g.modelValues
  let optimizer ← NativeCurrentValues.readValues g.optimizerValues
  let u ← Control.lookup configuration (ascii "arithmetic_units")
  let units ← ArithmeticUnits.decodeInitial (Control.encode u)
  if Checks sha origin g configuration model optimizer then
    some ⟨origin.source.genesis,origin.initialConfiguration,Control.encode u,units,g,
      model,optimizer,pointer sha g model optimizer⟩
  else none

structure Source (sha : Bytes → Bytes) (origin : Origin.Bound) (g : Descriptor)
    (configuration : Control.Fields) (out : Bound) : Prop where
  model : NativeCurrentValues.readValues g.modelValues = some out.model
  optimizer : NativeCurrentValues.readValues g.optimizerValues = some out.optimizer
  member : ∃ u, Control.lookup configuration (ascii "arithmetic_units") = some u ∧
    Control.encode u = out.initialUnits
  units : ArithmeticUnits.decodeInitial out.initialUnits = some out.units
  checks : Checks sha origin g configuration out.model out.optimizer
  original : out.original = origin.source.genesis
  configuration : out.initialConfiguration = origin.initialConfiguration
  descriptor : out.descriptor = g
  current : out.current = pointer sha g out.model out.optimizer

theorem boundSource {sha origin g configuration out}
    (ok : bind sha origin g configuration = some out) : Source sha origin g configuration out := by
  simp only [bind,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨model,hm,optimizer,ho,u,hu,units,hs,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  exact ⟨hm,ho,⟨u,hu,rfl⟩,hs,checks,rfl,rfl,rfl,rfl⟩

theorem complete {sha origin g configuration out}
    (h : Source sha origin g configuration out) : bind sha origin g configuration = some out := by
  obtain ⟨u,hu,bytes⟩ := h.member
  simp only [bind,h.model,h.optimizer,hu,Bind.bind,Option.bind,bytes,h.units,if_pos h.checks]
  have original := h.original
  have cfg := h.configuration
  have desc := h.descriptor
  have current := h.current
  cases out
  simp_all

theorem originalCoordinateSpellings {sha origin g configuration out}
    (ok : bind sha origin g configuration = some out) :
    g.modelValues = NativeApplyResult.decimalValues out.model ∧
    g.optimizerValues = NativeApplyResult.decimalValues out.optimizer :=
  ⟨(NativeCurrentValues.valuesSource (boundSource ok).model).1,
   (NativeCurrentValues.valuesSource (boundSource ok).optimizer).1⟩

theorem fullCoordinateCounts {sha origin g configuration out}
    (ok : bind sha origin g configuration = some out) :
    g.modelValues.length = out.model.length ∧ g.optimizerValues.length = out.optimizer.length :=
  ⟨NativeCurrentValues.valuesLength (boundSource ok).model,
   NativeCurrentValues.valuesLength (boundSource ok).optimizer⟩

theorem nativeValueBounds {sha origin g configuration out}
    (ok : bind sha origin g configuration = some out) :
    (∀ x ∈ out.model, Fits NativeBinding.minInput NativeBinding.maxInput x) ∧
    (∀ x ∈ out.optimizer, Fits NativeBinding.minInput NativeBinding.maxInput x) :=
  ⟨(NativeCurrentValues.valuesSource (boundSource ok).model).2,
   (NativeCurrentValues.valuesSource (boundSource ok).optimizer).2⟩

theorem existingHashPreimages {sha origin g configuration out}
    (ok : bind sha origin g configuration = some out) :
    out.current.checkpoint = NativeBinding.idBytes
      (sha (NativeApplyResult.rawValueInput .model g.modelValues)) ∧
    out.current.optimizer = NativeBinding.idBytes
      (sha (NativeApplyResult.rawValueInput .optimizer g.optimizerValues)) := by
  rw [(boundSource ok).current]
  simp [pointer,(originalCoordinateSpellings ok).1,(originalCoordinateSpellings ok).2,
    NativeApplyResult.exactValueInput]

theorem noInventedCertificate {sha origin g configuration out}
    (ok : bind sha origin g configuration = some out) : out.current.qc = [] := by
  rw [(boundSource ok).current]; rfl

theorem originalConfigurationAndUnits {sha origin g configuration out}
    (ok : bind sha origin g configuration = some out) :
    out.initialConfiguration = origin.initialConfiguration ∧
    ArithmeticUnits.QuantumValid out.units.quantum ∧
    out.initialUnits = ArithmeticUnits.initialJSON out.units :=
  ⟨(boundSource ok).configuration,(ArithmeticUnits.initialSource (boundSource ok).units).2.2.2⟩

theorem independentlyBoundOrigin {sha known bootstrap index bootstrapRaw indexRaw store origin
    g configuration out}
    (anchored : Origin.bind sha known bootstrap index bootstrapRaw indexRaw store = some origin)
    (ok : bind sha origin g configuration = some out) :
    Index.check sha origin.bootstrap.origin index indexRaw store = some origin.source ∧
    sha indexRaw = known.indexDigest ∧ out.original = origin.source.genesis ∧
    out.initialConfiguration = origin.initialConfiguration :=
  ⟨(Origin.boundSource anchored).source,(Origin.boundSource anchored).retainedIndex,
    (boundSource ok).original,(boundSource ok).configuration⟩

end DeltaReduce.ProfileSource.Genesis
