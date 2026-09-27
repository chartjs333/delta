import DeltaReduce.NativeApplyResult
import DeltaReduce.NativePointerWal

/-! Recover vector values from the original finalized candidate spellings.
Alternate native decimal spellings are rejected, never normalized. Hash and
observed-source authentication remain explicit boundaries. -/
namespace DeltaReduce.NativeCurrentValues
open NativeBinding
open NativeApplyCertificate (Candidate)

def readNumber (raw : Bytes) : Option Int := do
  let n ← NativeCertificateDecimal.parse false raw
  if raw = asciiBytes (toString n) then some n else none

theorem numberSource {raw n} (h : readNumber raw = some n) :
    NativeCertificateDecimal.parse false raw = some n ∧
    raw = asciiBytes (toString n) ∧ Fits minInput maxInput n := by
  simp only [readNumber,bind,Option.bind_eq_some_iff] at h
  obtain ⟨v,hv,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  have bounds := NativeCertificateDecimal.range hv
  exact ⟨hv,by assumption,by dsimp [Fits,minInput,maxInput]; omega⟩

theorem numberFromSource {raw n} (parsed : NativeCertificateDecimal.parse false raw = some n)
    (spelling : raw = asciiBytes (toString n)) : readNumber raw = some n := by
  simp only [readNumber,parsed,bind,Option.bind,if_pos spelling]

theorem alternateRejected {raw n} (parsed : NativeCertificateDecimal.parse false raw = some n)
    (spelling : raw ≠ asciiBytes (toString n)) : readNumber raw = none := by
  simp only [readNumber,parsed,bind,Option.bind,if_neg spelling]

def readValues : List Bytes → Option (List Int)
  | [] => some []
  | raw::raws => do
    let n ← readNumber raw
    let rest ← readValues raws
    some (n::rest)

theorem valuesSource {raws ns} (h : readValues raws = some ns) :
    raws = NativeApplyResult.decimalValues ns ∧ ∀ n ∈ ns, Fits minInput maxInput n := by
  induction raws generalizing ns with
  | nil => simp [readValues] at h; subst ns; exact ⟨rfl,by simp⟩
  | cons raw raws ih =>
    simp only [readValues,bind,Option.bind_eq_some_iff] at h
    obtain ⟨n,hn,rest,hr,last⟩ := h
    cases Option.some.inj last
    have tail := ih hr
    exact ⟨by simp only [NativeApplyResult.decimalValues,List.map_cons,
      (numberSource hn).2.1]; exact congrArg _ tail.1,
      by simpa using And.intro (numberSource hn).2.2 tail.2⟩

theorem valuesLength {raws ns} (h : readValues raws = some ns) : raws.length = ns.length := by
  rw [(valuesSource h).1,NativeApplyResult.exactValueCount]

theorem valuesPosition {raws ns} (h : readValues raws = some ns) (i : Nat) :
    raws[i]? = (ns.map (asciiBytes ∘ toString))[i]? := congrArg (fun xs => xs[i]?) (valuesSource h).1

structure Image where
  original : Candidate
  model : List Int
  optimizer : List Int
  modelHash : Bytes
  optimizerHash : Bytes
  deriving DecidableEq, Repr

def Checks (c : Candidate) (model optimizer : List Int) (mh oh : Bytes) : Prop :=
  0 < model.length ∧ model.length ≤ 100000 ∧ optimizer.length = model.length ∧
  mh.length = 32 ∧ oh.length = 32 ∧ c.model = idBytes mh ∧ c.optimizer = idBytes oh
instance (c m o mh oh) : Decidable (Checks c m o mh oh) := by unfold Checks; infer_instance

def load (sha : Bytes → Bytes) (c : Candidate) : Option Image := do
  let model ← readValues c.modelValues
  let optimizer ← readValues c.optimizerValues
  let mh := sha (valueHashInput .model model)
  let oh := sha (valueHashInput .optimizer optimizer)
  if Checks c model optimizer mh oh then some ⟨c,model,optimizer,mh,oh⟩ else none

structure Source (sha : Bytes → Bytes) (c : Candidate) (out : Image) : Prop where
  original : out.original = c
  model : readValues c.modelValues = some out.model
  optimizer : readValues c.optimizerValues = some out.optimizer
  modelHash : out.modelHash = sha (valueHashInput .model out.model)
  optimizerHash : out.optimizerHash = sha (valueHashInput .optimizer out.optimizer)
  checked : Checks c out.model out.optimizer out.modelHash out.optimizerHash

theorem loaded {sha c out} (h : load sha c = some out) : Source sha c out := by
  simp only [load,bind,Option.bind_eq_some_iff] at h
  obtain ⟨model,hm,optimizer,ho,last⟩ := h
  split at last <;> try contradiction
  cases Option.some.inj last
  exact ⟨rfl,hm,ho,rfl,rfl,by assumption⟩

theorem loadFromSource {sha c out} (h : Source sha c out) : load sha c = some out := by
  cases out
  cases h.original
  simp only [load,h.model,h.optimizer,bind,Option.bind,← h.modelHash,← h.optimizerHash,
    if_pos h.checked]

theorem originalPreimages {sha c out} (h : load sha c = some out) :
    c.modelValues = NativeApplyResult.decimalValues out.model ∧
    c.optimizerValues = NativeApplyResult.decimalValues out.optimizer :=
  ⟨(valuesSource (loaded h).model).1,(valuesSource (loaded h).optimizer).1⟩

theorem originalHashes {sha c out} (h : load sha c = some out) :
    c.model = idBytes (sha (NativeApplyResult.rawValueInput .model c.modelValues)) ∧
    c.optimizer = idBytes (sha (NativeApplyResult.rawValueInput .optimizer c.optimizerValues)) := by
  have src := loaded h
  rw [(originalPreimages h).1,(originalPreimages h).2,
    NativeApplyResult.exactValueInput,NativeApplyResult.exactValueInput,
    ← src.modelHash,← src.optimizerHash]
  exact ⟨src.checked.2.2.2.2.2.1,src.checked.2.2.2.2.2.2⟩

theorem valueBounds {sha c out} (h : load sha c = some out) :
    (∀ n ∈ out.model, Fits minInput maxInput n) ∧
    (∀ n ∈ out.optimizer, Fits minInput maxInput n) :=
  ⟨(valuesSource (loaded h).model).2,(valuesSource (loaded h).optimizer).2⟩

theorem absentModelRejected {sha c} (h : readValues c.modelValues = none) : load sha c = none := by
  simp only [load,h,bind,Option.bind]

end DeltaReduce.NativeCurrentValues
