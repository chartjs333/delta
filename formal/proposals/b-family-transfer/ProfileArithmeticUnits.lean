import DeltaReduce.NativeApplyProfile
import DeltaReduce.NativeJsonSequence

/-! T047/T053, scope 15. Executable exact U/R parsers and acyclic R/proof/P
byte selection for the approved unit-source generation. No result, public
projection, candidate-selected quantum or acceptance callback is an input.

The original initial/configuration/APC producer authority and complete current
history must be established by the enclosing R2.3 source relation. These byte
lemmas do not assert that an arbitrary supplied proof ID is that original APC,
that U alone is lawful genesis, or that the full recovery obligation is closed.
-/
namespace DeltaReduce.ProfileSource.ArithmeticUnits
open NativeReceiptBytes (Bytes consume)
open NativeVoteBytes (ascii ContentId parseDecimal)
open NativeIscCertificate (object quoted array number)
open NativeApplyProfile (Fraction Weight fractionJSON weightJSON)

def QuantumValid (q : Fraction) : Prop :=
  0 < q.numerator ∧ q.numerator < 2^63 ∧ 0 < q.denominator ∧
  q.denominator < 2^63 ∧ Nat.gcd q.numerator q.denominator = 1
instance (q) : Decidable (QuantumValid q) := by unfold QuantumValid; infer_instance

structure Numeric where
  quantum : Fraction
  weights : List Weight
  learning : Fraction
  momentum : Fraction
  decay : Fraction
  deriving DecidableEq, Repr

-- Nesterov and rounding are fixed by the existing native validity contract.
def originalProfile (r : Numeric) (proof : Bytes) : NativeApplyProfile.Profile :=
  ⟨proof,r.weights,r.learning,r.momentum,1,ascii "HALF_TOWARD_POSITIVE",r.decay⟩

def Valid (r : Numeric) : Prop := QuantumValid r.quantum ∧
  0 < r.weights.length ∧ r.weights.length ≤ 100000 ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (r.weights.map Weight.domain) = true ∧
  (∀ w ∈ r.weights, NativeConfigAdmission.Label w.domain ∧ NativeApplyProfile.FractionValid w.fraction) ∧
  NativeApplyProfile.FractionValid r.learning ∧ NativeApplyProfile.FractionValid r.momentum ∧
  NativeApplyProfile.FractionValid r.decay
instance (r) : Decidable (Valid r) := by unfold Valid; infer_instance

def numericFields (r : Numeric) : List (String × Bytes) :=
  [("apply_quantum",fractionJSON r.quantum),("domain_weights",array (r.weights.map weightJSON)),
   ("learning_rate",fractionJSON r.learning),("momentum",fractionJSON r.momentum),
   ("nesterov",ascii "true"),("rounding",quoted (ascii "HALF_TOWARD_POSITIVE")),
   ("weight_decay",fractionJSON r.decay)]
def numericJSON (r : Numeric) : Bytes := object (numericFields r)

def profileJSON (sigma proof : Bytes) (r : Numeric) : Bytes := object [
  ("accumulator_proof_id",quoted proof),("apply_quantum",fractionJSON r.quantum),
  ("domain_weights",array (r.weights.map weightJSON)),("formal_semantics_id",quoted sigma),
  ("learning_rate",fractionJSON r.learning),("momentum",fractionJSON r.momentum),
  ("nesterov",ascii "true"),("rounding",quoted (ascii "HALF_TOWARD_POSITIVE")),
  ("schema_version",quoted (ascii "2.0.0")),
  ("type_name",quoted (ascii "APPLY_ARITHMETIC_PROFILE")),("weight_decay",fractionJSON r.decay)]

def readFraction (raw : Bytes) : Option (Fraction × Bytes) := do
  let raw ← consume (ascii "{\"denominator\":") raw
  let (denominator,raw) ← NativeJsonSequence.readNatural raw
  let d ← parseDecimal denominator
  let raw ← consume (ascii ",\"numerator\":") raw
  let (numerator,raw) ← NativeJsonSequence.readText raw
  let n ← parseDecimal numerator
  let raw ← consume [125] raw
  some (⟨n,d⟩,raw)

def readWeight (raw : Bytes) : Option (Weight × Bytes) := do
  let raw ← consume (ascii "{\"domain_id\":") raw
  let (domain,raw) ← NativeJsonSequence.readText raw
  let raw ← consume (ascii ",\"pi\":") raw
  let (fraction,raw) ← readFraction raw
  let raw ← consume [125] raw
  some (⟨domain,fraction⟩,raw)

def readNumeric (raw : Bytes) : Option (Numeric × Bytes) := do
  let raw ← consume (ascii "{\"apply_quantum\":") raw
  let (q,raw) ← readFraction raw
  let raw ← consume (ascii ",\"domain_weights\":[") raw
  let (weights,raw) ← NativeJsonSequence.read 93 readWeight 100000 raw
  let raw ← consume (ascii ",\"learning_rate\":") raw
  let (learning,raw) ← readFraction raw
  let raw ← consume (ascii ",\"momentum\":") raw
  let (momentum,raw) ← readFraction raw
  let raw ← consume (ascii ",\"nesterov\":true,\"rounding\":\"HALF_TOWARD_POSITIVE\",\"weight_decay\":") raw
  let (decay,raw) ← readFraction raw
  let raw ← consume [125] raw
  some (⟨q,weights,learning,momentum,decay⟩,raw)

def decodeNumeric (raw : Bytes) : Option Numeric := do
  if raw.length ≤ NativeContractSize.maxBytes then
    let (r,tail) ← readNumeric raw
    if tail = [] ∧ Valid r ∧ raw = numericJSON r then some r else none
  else none

theorem numericSource {raw r} (ok : decodeNumeric raw = some r) :
    raw.length ≤ NativeContractSize.maxBytes ∧ readNumeric raw = some (r,[]) ∧
    Valid r ∧ raw = numericJSON r := by
  unfold decodeNumeric at ok
  split at ok <;> try contradiction
  rename_i bound
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨⟨parsed,tail⟩,hp,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  rcases checks with ⟨rfl,valid,original⟩
  exact ⟨bound,hp,valid,original⟩

theorem numericComplete {raw r}
    (bound : raw.length ≤ NativeContractSize.maxBytes)
    (parsed : readNumeric raw = some (r,[])) (valid : Valid r)
    (original : raw = numericJSON r) : decodeNumeric raw = some r := by
  simp only [decodeNumeric,if_pos bound,parsed,Bind.bind,Option.bind]
  simp only [valid,original,and_self,if_true]

theorem sourceNumbersUnique {raw a b}
    (left : decodeNumeric raw = some a) (right : decodeNumeric raw = some b) : a = b :=
  Option.some.inj (left.symm.trans right)

theorem sourceQuantumUnique {raw a b}
    (left : decodeNumeric raw = some a) (right : decodeNumeric raw = some b) :
    a.quantum = b.quantum := congrArg Numeric.quantum (sourceNumbersUnique left right)

theorem originalNumericConditions {raw r proof}
    (ok : decodeNumeric raw = some r) (hp : ContentId proof) :
    NativeApplyProfile.Valid (originalProfile r proof) := by
  have h := (numericSource ok).2.2.1
  exact ⟨hp,h.2.1,h.2.2.1,h.2.2.2.1,h.2.2.2.2.1,
    h.2.2.2.2.2.1,h.2.2.2.2.2.2.1,h.2.2.2.2.2.2.2,rfl,rfl⟩

structure Initial where
  schema : Bytes
  quantum : Fraction
  deriving DecidableEq, Repr

def initialJSON (u : Initial) : Bytes := object [
  ("parameter_schema_id",quoted u.schema),
  ("quantum",object [("denominator",quoted (number u.quantum.denominator)),
    ("numerator",quoted (number u.quantum.numerator))]),
  ("schema_version",quoted (ascii "1.0.0")),("type_name",quoted (ascii "INITIAL_ARITHMETIC_UNITS"))]

def readInitial (raw : Bytes) : Option (Initial × Bytes) := do
  let raw ← consume (ascii "{\"parameter_schema_id\":") raw
  let (schema,raw) ← NativeJsonSequence.readText raw
  let raw ← consume (ascii ",\"quantum\":{\"denominator\":") raw
  let (denominator,raw) ← NativeJsonSequence.readText raw
  let d ← parseDecimal denominator
  let raw ← consume (ascii ",\"numerator\":") raw
  let (numerator,raw) ← NativeJsonSequence.readText raw
  let n ← parseDecimal numerator
  let raw ← consume (ascii "},\"schema_version\":\"1.0.0\",\"type_name\":\"INITIAL_ARITHMETIC_UNITS\"}") raw
  some (⟨schema,⟨n,d⟩⟩,raw)

def decodeInitial (raw : Bytes) : Option Initial := do
  if raw.length ≤ NativeContractSize.maxBytes then
    let (u,tail) ← readInitial raw
    if tail = [] ∧ ContentId u.schema ∧ QuantumValid u.quantum ∧ raw = initialJSON u then
      some u
    else none
  else none

theorem initialSource {raw u} (ok : decodeInitial raw = some u) :
    raw.length ≤ NativeContractSize.maxBytes ∧ readInitial raw = some (u,[]) ∧
    ContentId u.schema ∧ QuantumValid u.quantum ∧ raw = initialJSON u := by
  unfold decodeInitial at ok
  split at ok <;> try contradiction
  rename_i bound
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨⟨parsed,tail⟩,hp,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  rcases checks with ⟨rfl,valid,quantum,original⟩
  exact ⟨bound,hp,valid,quantum,original⟩

theorem initialUnitsUnique {raw a b}
    (left : decodeInitial raw = some a) (right : decodeInitial raw = some b) : a = b :=
  Option.some.inj (left.symm.trans right)

structure Selected where
  numeric : Numeric
  profile : NativeApplyProfile.Profile
  original : Bytes
  id : Bytes

def select (sha : Bytes → Bytes) (sigma proof source original : Bytes) : Option Selected := do
  let r ← decodeNumeric source
  if ContentId sigma ∧ sigma ≠ NativeVoteBytes.nativeSemantics ∧
      ContentId proof ∧ original = profileJSON sigma proof r then
    let id ← NativeContractSize.contentId sha NativeApplyProfile.domain original
    some ⟨r,originalProfile r proof,original,id⟩
  else none

structure SelectionSource (sha : Bytes → Bytes) (sigma proof source original : Bytes)
    (out : Selected) : Prop where
  decoded : decodeNumeric source = some out.numeric
  semantic : ContentId sigma
  futureGeneration : sigma ≠ NativeVoteBytes.nativeSemantics
  proofId : ContentId proof
  profile : out.profile = originalProfile out.numeric proof
  retained : out.original = original
  bytes : original = profileJSON sigma proof out.numeric
  identity : NativeContractSize.contentId sha NativeApplyProfile.domain original = some out.id

theorem selectedSource {sha sigma proof source original out}
    (ok : select sha sigma proof source original = some out) :
    SelectionSource sha sigma proof source original out := by
  simp only [select,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨r,hr,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨id,hi,last⟩ := last
  cases Option.some.inj last
  exact ⟨hr,checks.1,checks.2.1,checks.2.2.1,rfl,rfl,checks.2.2.2,hi⟩

theorem selectionComplete {sha sigma proof source original out}
    (h : SelectionSource sha sigma proof source original out) :
    select sha sigma proof source original = some out := by
  simp only [select,h.decoded,Bind.bind,Option.bind,
    if_pos (And.intro h.semantic (And.intro h.futureGeneration (And.intro h.proofId h.bytes))),h.identity]
  have profile := h.profile
  have retained := h.retained
  cases out
  simp only at profile retained
  cases profile
  cases retained
  rfl

theorem selectedQuantum {sha sigma proof source original out}
    (ok : select sha sigma proof source original = some out) :
    QuantumValid out.numeric.quantum ∧ source = numericJSON out.numeric ∧
    original = profileJSON sigma proof out.numeric := by
  have h := selectedSource ok
  have r := numericSource h.decoded
  exact ⟨r.2.2.1.1,r.2.2.2,h.bytes⟩

theorem selectedProof {sha sigma proof source original out}
    (ok : select sha sigma proof source original = some out) :
    out.profile.accumulator = proof := by
  rw [(selectedSource ok).profile]; rfl

theorem selectedOriginalBound {sha sigma proof source original out}
    (ok : select sha sigma proof source original = some out) :
    original.length ≤ NativeContractSize.maxBytes :=
  (NativeContractSize.accepted (selectedSource ok).identity).1

theorem selectedNumbersUnique {sha sigma proof source left right a b}
    (ha : select sha sigma proof source left = some a)
    (hb : select sha sigma proof source right = some b) :
    a.numeric = b.numeric ∧ left = right := by
  have x := selectedSource ha
  have y := selectedSource hb
  have same := sourceNumbersUnique x.decoded y.decoded
  exact ⟨same,by rw [x.bytes,y.bytes,same]⟩

theorem legacyGenerationRejected (sha : Bytes → Bytes) (proof source original : Bytes) :
    select sha NativeVoteBytes.nativeSemantics proof source original = none := by
  unfold select
  cases decodeNumeric source <;> simp

end DeltaReduce.ProfileSource.ArithmeticUnits
