import ProfileConfiguration
import ProfileArithmeticUnits
import DeltaReduce.NativeCurrentPointer

/-! T047/T053, scope 15. The exact schema-3 DRC1 source grammar. Full original
configuration fields, enrollment and parent-unit admission precede any APC.
No old bytes are re-encoded as this generation. This is a source conjunct:
the enclosing original history must supply the independently derived parent.
-/
namespace DeltaReduce.ProfileSource.ConfigurationUnits
open NativeReceiptBytes (Bytes consume sizedBytes)
open NativeVoteBytes (ascii maxEnvelope)
open NativePolicyCodec (Value)
open Configuration (Format Body Enrollment)

def format : Format := match Configuration.configuration with
  | .object fields => .object (.field "apply_arithmetic_profile_source" .text fields)
  | _ => .end

def encodeFrame (value : Value) : Option Bytes := do
  let raw ← Configuration.encode format value
  let frame := Configuration.header ++ sizedBytes raw
  if frame.length ≤ maxEnvelope then some frame else none

def decodeFrame (raw : Bytes) : Option Value := do
  if raw.length ≤ maxEnvelope then
    let body ← consume Configuration.header raw
    let (body,rest) ← NativeReceiptBytes.readSection maxEnvelope body
    if rest = [] then
      let value ← Configuration.decode format body
      if encodeFrame value = some raw then some value else none
    else none
  else none

theorem frameEncoded {value raw} (ok : encodeFrame value = some raw) :
    decodeFrame raw = some value := by
  unfold encodeFrame at ok
  cases hp : Configuration.encode format value with
  | none => simp [hp] at ok
  | some body =>
    simp only [hp,Bind.bind,Option.bind] at ok
    split at ok <;> try contradiction
    rename_i bound
    cases Option.some.inj ok
    have small : body.length ≤ maxEnvelope := by
      have length : (Configuration.header ++ sizedBytes body).length = 12 + body.length := by
        simp [Configuration.header,sizedBytes,NativeReceiptBytes.beLength]; omega
      rw [length] at bound
      omega
    have width : body.length < 256^4 := by unfold maxEnvelope at small; omega
    simp only [decodeFrame,if_pos bound,NativeReceiptBytes.consumeAppend,Bind.bind,Option.bind]
    rw [← List.append_nil (sizedBytes body),NativeReceiptBytes.readSectionEncoded body [] maxEnvelope width small]
    simp only [↓reduceIte,Configuration.encoded hp]
    have encodedFrame : encodeFrame value = some (Configuration.header ++ sizedBytes body) := by
      simp only [encodeFrame,hp,Bind.bind,Option.bind,if_pos bound]
    simp only [encodedFrame,List.append_nil,↓reduceIte]

theorem frameDecoded {raw value} (ok : decodeFrame raw = some value) :
    encodeFrame value = some raw := by
  unfold decodeFrame at ok
  split at ok <;> try contradiction
  simp only [Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨rest,_,⟨body,tail⟩,_,last⟩ := ok
  split at last <;> try contradiction
  simp only [Option.bind_eq_some_iff] at last
  obtain ⟨v,_,last⟩ := last
  split at last <;> try contradiction
  rename_i same
  cases Option.some.inj last
  exact same

structure Bound where
  original : Bytes
  body : Body
  source : Bytes
  numeric : ArithmeticUnits.Numeric

def check (raw : Bytes) : Option Bound := do
  let value ← decodeFrame raw
  let body ← Configuration.interpretUsing format (ascii "3.0.0") value
  let source ← Configuration.textField format value "apply_arithmetic_profile_source"
  let numeric ← ArithmeticUnits.decodeNumeric source
  if body.semantics ≠ NativeVoteBytes.nativeSemantics then
    some ⟨raw,body,source,numeric⟩ else none

structure Source (raw : Bytes) (out : Bound) : Prop where
  original : out.original = raw
  bytes : decodeFrame raw = some out.body.originalValue
  fields : Configuration.interpretUsing format (ascii "3.0.0") out.body.originalValue = some out.body
  selected : Configuration.textField format out.body.originalValue "apply_arithmetic_profile_source" = some out.source
  numeric : ArithmeticUnits.decodeNumeric out.source = some out.numeric
  generation : out.body.semantics ≠ NativeVoteBytes.nativeSemantics

theorem checked {raw out} (ok : check raw = some out) : Source raw out := by
  simp only [check,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨value,hv,body,hb,source,hs,numeric,hn,last⟩ := ok
  split at last <;> try contradiction
  rename_i generation
  cases Option.some.inj last
  have same := (Configuration.interpretedUsing hb).1
  exact ⟨rfl,by simpa only [same] using hv,by simpa only [same] using hb,
    by simpa only [same] using hs,hn,generation⟩

theorem complete {raw out} (h : Source raw out) : check raw = some out := by
  simp only [check,h.bytes,h.fields,h.selected,h.numeric,Bind.bind,Option.bind,if_pos h.generation]
  cases out
  cases h.original
  rfl

theorem entireOriginalConfiguration {raw out} (ok : check raw = some out) :
    encodeFrame out.body.originalValue = some raw ∧ out.original = raw ∧
    ArithmeticUnits.Valid out.numeric ∧ out.source = ArithmeticUnits.numericJSON out.numeric := by
  have h := checked ok
  have n := ArithmeticUnits.numericSource h.numeric
  exact ⟨frameDecoded h.bytes,h.original,n.2.2.1,n.2.2.2⟩

/-- Parent carries the full tuple, never a bare model hash. Its independent
origin and accepted history are established by the outer source composition. -/
structure Parent where
  current : NativeCurrentPointer.State
  schema : Bytes
  modelQuantum : NativeApplyProfile.Fraction
  optimizerQuantum : NativeApplyProfile.Fraction

def ParentMatches (parent : Parent) (out : Bound) : Prop :=
  NativeCurrentPointer.StateValid parent.current ∧
  out.body.parent = parent.current.checkpoint ∧ parent.current.height < out.body.height ∧
  out.body.schema = parent.schema ∧
  out.numeric.quantum = parent.modelQuantum ∧ out.numeric.quantum = parent.optimizerQuantum
instance (p b) : Decidable (ParentMatches p b) := by unfold ParentMatches; infer_instance

def admit (enrolled : Enrollment) (parent : Parent) (raw : Bytes) : Option Bound := do
  let out ← check raw
  if Configuration.Matches enrolled out.body ∧ ParentMatches parent out then some out else none

theorem admitted {enrolled parent raw out} (ok : admit enrolled parent raw = some out) :
    check raw = some out ∧ Configuration.Matches enrolled out.body ∧ ParentMatches parent out := by
  simp only [admit,Bind.bind,Option.bind_eq_some_iff] at ok
  obtain ⟨b,hb,last⟩ := ok
  split at last <;> try contradiction
  rename_i checkedFields
  cases Option.some.inj last
  exact ⟨hb,checkedFields⟩

theorem admissionComplete {enrolled parent raw out} (bytes : check raw = some out)
    (authority : Configuration.Matches enrolled out.body) (units : ParentMatches parent out) :
    admit enrolled parent raw = some out := by
  simp only [admit,bytes,Bind.bind,Option.bind,if_pos (And.intro authority units)]

theorem noParentUnitOverride {enrolled parent raw out}
    (ok : admit enrolled parent raw = some out) :
    out.numeric.quantum = parent.modelQuantum ∧ parent.modelQuantum = parent.optimizerQuantum := by
  have h := (admitted ok).2.2
  exact ⟨h.2.2.2.2.1,h.2.2.2.2.1.symm.trans h.2.2.2.2.2⟩

end DeltaReduce.ProfileSource.ConfigurationUnits
