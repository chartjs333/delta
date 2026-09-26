import DeltaReduce.NativeAggregateSection

/-! Original APPLY profile, nonnegative rational wire bits and bounded JSON.
Primitive identifiers remain unauthenticated; no optimizer arithmetic is assumed. -/
namespace DeltaReduce.NativeApplyProfile
open NativeReceiptBytes NativePolicyCodec NativePolicySchema
open NativeIscCertificate (quoted array object number readTexts)

structure Fraction where
  numerator : Nat
  denominator : Nat
  deriving DecidableEq, Repr
def fractionValue (f : Fraction) : Value := .pair (.number f.numerator) (.pair (.number f.denominator) .end)
def readFraction : Value → Option Fraction
  | .pair (.number n) (.pair (.number d) .end) => some ⟨n,d⟩
  | _ => none
theorem fractionRead (f) : readFraction (fractionValue f) = some f := by cases f; rfl
theorem fractionOriginal {v f} (h : readFraction v = some f) : v = fractionValue f := by
  unfold readFraction at h; split at h <;> try contradiction
  cases Option.some.inj h; rfl
def FractionValid (f : Fraction) : Prop := f.numerator < 2^63 ∧ 0 < f.denominator ∧
  f.denominator < 256^8 ∧ Nat.gcd f.numerator f.denominator = 1
instance (f) : Decidable (FractionValid f) := by unfold FractionValid; infer_instance
def fractionJSON (f : Fraction) : Bytes :=
  object [("denominator",number f.denominator),("numerator",quoted (number f.numerator))]
structure Weight where
  domain : Bytes
  fraction : Fraction
  deriving DecidableEq, Repr
def weightValue (c : Weight) : Value :=
  .pair (.text c.domain) (.pair (fractionValue c.fraction) (.end))
def readWeight : Value → Option Weight
  | .pair (.text domain) (.pair (fraction) (.end)) => do
    let fractionValue ← readFraction fraction
    some ⟨domain,fractionValue⟩
  | _ => none

theorem weightRead (c) : readWeight (weightValue c) = some c := by
  cases c
  simp only [weightValue,readWeight,fractionRead,bind,Option.bind]
theorem weightOriginal {v c} (h : readWeight v = some c) : v = weightValue c := by
  unfold readWeight at h; split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨a0,h0,last⟩ := h
  cases Option.some.inj last
  simp only [weightValue,← fractionOriginal h0]

def readWeights : List Value → Option (List Weight)
  | [] => some []
  | v::vs => do let w ← readWeight v; let ws ← readWeights vs; some (w::ws)
theorem weightsRead (ws) : readWeights (ws.map weightValue) = some ws := by
  induction ws with
  | nil => rfl
  | cons w ws ih => simp only [List.map_cons,readWeights,weightRead,ih,bind,Option.bind]
theorem weightsOriginal {vs ws} (h : readWeights vs = some ws) : vs = ws.map weightValue := by
  induction vs generalizing ws with
  | nil => simp [readWeights] at h; subst ws; rfl
  | cons v vs ih =>
    simp only [readWeights,bind,Option.bind_eq_some_iff] at h
    obtain ⟨w,hw,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,← weightOriginal hw,← ih hr]
structure Profile where
  accumulator : Bytes
  weights : List Weight
  learning : Fraction
  momentum : Fraction
  nesterov : Nat
  rounding : Bytes
  decay : Fraction
  deriving DecidableEq, Repr
def profileValue (c : Profile) : Value :=
  .pair (.text c.accumulator) (.pair (.items (c.weights.map weightValue)) (.pair (fractionValue c.learning) (.pair (fractionValue c.momentum) (.pair (.number c.nesterov) (.pair (.text c.rounding) (.pair (fractionValue c.decay) (.end)))))))
def readProfile : Value → Option Profile
  | .pair (.text accumulator) (.pair (.items weights) (.pair (learning) (.pair (momentum) (.pair (.number nesterov) (.pair (.text rounding) (.pair (decay) (.end))))))) => do
    let weightsValue ← readWeights weights
    let learningValue ← readFraction learning
    let momentumValue ← readFraction momentum
    let decayValue ← readFraction decay
    some ⟨accumulator,weightsValue,learningValue,momentumValue,nesterov,rounding,decayValue⟩
  | _ => none

theorem profileRead (c) : readProfile (profileValue c) = some c := by
  cases c
  simp only [profileValue,readProfile,weightsRead,fractionRead,bind,Option.bind]
theorem profileOriginal {v c} (h : readProfile v = some c) : v = profileValue c := by
  unfold readProfile at h; split at h <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨a0,h0,a1,h1,a2,h2,a3,h3,last⟩ := h
  cases Option.some.inj last
  simp only [profileValue,← weightsOriginal h0,← fractionOriginal h1,← fractionOriginal h2,← fractionOriginal h3]

def Valid (p : Profile) : Prop := NativeVoteBytes.ContentId p.accumulator ∧
  0 < p.weights.length ∧ p.weights.length ≤ 100000 ∧
  NativePolicyBytes.strictly NativePolicyBytes.bytesLT (p.weights.map Weight.domain) = true ∧
  (∀ w ∈ p.weights, NativeConfigAdmission.Label w.domain ∧ FractionValid w.fraction) ∧
  FractionValid p.learning ∧ FractionValid p.momentum ∧ FractionValid p.decay ∧
  p.nesterov = 1 ∧ p.rounding = NativeVoteBytes.ascii "HALF_TOWARD_POSITIVE"
instance (p) : Decidable (Valid p) := by unfold Valid; infer_instance
def weightJSON (w : Weight) : Bytes := object [("domain_id",quoted w.domain),("pi",fractionJSON w.fraction)]
def fields (p : Profile) : List (String × Bytes) :=
  [("accumulator_proof_id",quoted p.accumulator),("domain_weights",array (p.weights.map weightJSON)),
   ("formal_semantics_id",quoted NativeVoteBytes.nativeSemantics),("learning_rate",fractionJSON p.learning),
   ("momentum",fractionJSON p.momentum),("nesterov",if p.nesterov = 0 then NativeVoteBytes.ascii "false" else NativeVoteBytes.ascii "true"),
   ("rounding",quoted p.rounding),("schema_version",quoted (NativeVoteBytes.ascii "1.0.0")),
   ("type_name",quoted (NativeVoteBytes.ascii "APPLY_ARITHMETIC_PROFILE")),("weight_decay",fractionJSON p.decay)]
def json (p : Profile) : Bytes := object (fields p)
def domain : Bytes := NativeVoteBytes.ascii "deltareduce.008.apply-arithmetic-profile.v1"
def id (sha : Bytes → Bytes) (p : Profile) : Option Bytes := NativeContractSize.contentId sha domain (json p)
structure Checked where
  profile : Profile
  source : Value
  id : Bytes
def check (sha : Bytes → Bytes) (source : Value) : Option Checked := do
  let p ← readProfile source
  if Valid p then
    let pid ← id sha p
    some ⟨p,source,pid⟩
  else none
theorem checkedSource {sha source e} (h : check sha source = some e) :
    e.source = source ∧ source = profileValue e.profile ∧ Valid e.profile ∧ id sha e.profile = some e.id := by
  unfold check at h
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨p,hp,last⟩ := h
  split at last <;> try contradiction
  rename_i valid
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨pid,hi,last⟩ := last
  cases Option.some.inj last
  exact ⟨rfl,profileOriginal hp,valid,hi⟩
theorem fromComponents {sha p source pid} (hp : readProfile source = some p)
    (hv : Valid p) (hi : id sha p = some pid) : check sha source = some ⟨p,source,pid⟩ := by
  simp only [check,hp,bind,Option.bind,if_pos hv,hi]
theorem checkedBound {sha source e} (h : check sha source = some e) :
    (json e.profile).length ≤ NativeContractSize.maxBytes :=
  (NativeContractSize.accepted (checkedSource h).2.2.2).1
def checkAll (sha : Bytes → Bytes) : List Value → Option (List Checked)
  | [] => some []
  | v::vs => do let e ← check sha v; let es ← checkAll sha vs; some (e::es)
theorem allSources {sha vs es} (h : checkAll sha vs = some es) : es.map Checked.source = vs := by
  induction vs generalizing es with
  | nil => simp [checkAll] at h; subst es; rfl
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨e,he,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.map_cons,(checkedSource he).1,ih hr]
theorem allChecked {sha vs es} (h : checkAll sha vs = some es) (e : Checked) (mem : e ∈ es) :
    check sha e.source = some e := by
  induction vs generalizing es with
  | nil => simp [checkAll] at h; subst es; simp at mem
  | cons v vs ih =>
    simp only [checkAll,bind,Option.bind_eq_some_iff] at h
    obtain ⟨x,hx,rest,hr,last⟩ := h
    cases Option.some.inj last
    rcases List.mem_cons.mp mem with rfl | mem
    · simpa only [(checkedSource hx).1] using hx
    · exact ih hr mem
end DeltaReduce.NativeApplyProfile
