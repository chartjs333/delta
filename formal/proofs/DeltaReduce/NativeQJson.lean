import DeltaReduce.NativeQBytes
import DeltaReduce.NativeVoteBytes

/-! Canonical fixed-field ASCII JSON for native-004 headers. Native header
strings are content IDs/tokens and require no JSON escapes. This is not a
general JSON parser and not a SHA or source-authentication boundary. -/
namespace DeltaReduce.NativeQJson
open NativeReceiptBytes (Bytes consume consumeAppend)
open NativeVoteBytes (ascii DecimalValid)

def scanTo (delimiter : UInt8) : Bytes → Option (Bytes × Bytes)
  | [] => none
  | b :: rest =>
    if b = delimiter then some ([], rest)
    else (scanTo delimiter rest).map (fun pair => (b :: pair.1, pair.2))

theorem scanToEncoded (delimiter : UInt8) (value tail : Bytes)
    (safe : ∀ b ∈ value, b ≠ delimiter) :
    scanTo delimiter (value ++ delimiter :: tail) = some (value, tail) := by
  induction value with
  | nil => simp [scanTo]
  | cons b rest ih =>
    have head := safe b (by simp)
    have restSafe : ∀ x ∈ rest, x ≠ delimiter := by
      intro x hx; exact safe x (by simp [hx])
    simp [scanTo, head, ih restSafe]

theorem scanToSound {delimiter : UInt8} {raw value rest : Bytes}
    (h : scanTo delimiter raw = some (value, rest)) :
    raw = value ++ delimiter :: rest ∧ ∀ b ∈ value, b ≠ delimiter := by
  match raw with
  | [] => simp [scanTo] at h
  | b :: tail =>
    by_cases same : b = delimiter
    · simp [scanTo, same] at h
      rcases h with ⟨rfl, rfl⟩
      exact ⟨by simp [same], by simp⟩
    · cases e : scanTo delimiter tail with
      | none => simp [scanTo, same, e] at h
      | some pair =>
        rcases pair with ⟨v, r⟩
        simp [scanTo, same, e] at h
        rcases h with ⟨rfl, rfl⟩
        obtain ⟨eq, safe⟩ := scanToSound e
        exact ⟨by simp [eq], by simpa using And.intro same safe⟩

inductive Kind where
  | natural
  | text
  deriving DecidableEq, Repr

def TextValid (raw : Bytes) : Prop :=
  raw.length ≤ 65536 ∧ ∀ b ∈ raw, 32 ≤ b.toNat ∧ b.toNat ≤ 126 ∧ b ≠ 34 ∧ b ≠ 92
instance (raw) : Decidable (TextValid raw) := by unfold TextValid; infer_instance

def ValueValid (kind : Kind) (raw : Bytes) : Prop :=
  match kind with
  | .natural => DecimalValid raw
  | .text => TextValid raw
instance (kind raw) : Decidable (ValueValid kind raw) := by cases kind <;> unfold ValueValid <;> infer_instance

def encodeValue (kind : Kind) (value : Bytes) : Bytes :=
  match kind with
  | .natural => value
  | .text => [34] ++ value ++ [34]

def readValue (kind : Kind) (separator : UInt8) (raw : Bytes) : Option (Bytes × Bytes) := do
  match kind with
  | .natural =>
    let (value, rest) ← scanTo separator raw
    if DecimalValid value then some (value, rest) else none
  | .text =>
    let raw ← consume [34] raw
    let (value, rest) ← scanTo 34 raw
    let rest ← consume [separator] rest
    if TextValid value then some (value, rest) else none

theorem digitsAvoidSeparator (value : Bytes) (valid : DecimalValid value)
    (separator : UInt8) (sep : separator = 44 ∨ separator = 125) :
    ∀ b ∈ value, b ≠ separator := by
  intro b hb same
  have digit := valid.2.2.1 b hb
  rw [same] at digit
  rcases sep with rfl | rfl <;> simp [NativeVoteBytes.digit] at digit

theorem readValueEncoded (kind : Kind) (value tail : Bytes) (separator : UInt8)
    (sep : separator = 44 ∨ separator = 125) (valid : ValueValid kind value) :
    readValue kind separator (encodeValue kind value ++ separator :: tail) =
      some (value, tail) := by
  cases kind with
  | natural =>
    change DecimalValid value at valid
    have safe := digitsAvoidSeparator value valid separator sep
    simp [readValue, encodeValue, scanToEncoded separator value tail safe, valid]
  | text =>
    change TextValid value at valid
    have safe : ∀ b ∈ value, b ≠ 34 := by intro b hb; exact valid.2 b hb |>.2.2.1
    simp only [readValue, encodeValue, List.append_assoc, consumeAppend, bind, Option.bind]
    rw [show [34] ++ separator :: tail = 34 :: separator :: tail from rfl,
      scanToEncoded 34 value (separator :: tail) safe]
    simp [consume, valid]

structure Field where
  key : Bytes
  kind : Kind
  value : Bytes
  deriving DecidableEq, Repr

def keyPrefix (key : Bytes) : Bytes := [34] ++ key ++ [34, 58]
def separator (rest : List α) : UInt8 := if rest = [] then 125 else 44

theorem separatorValid (rest : List α) : separator rest = 44 ∨ separator rest = 125 := by
  unfold separator; split <;> simp

def encodeFields : List Field → Bytes
  | [] => []
  | field :: rest => keyPrefix field.key ++ encodeValue field.kind field.value ++
      [separator rest] ++ encodeFields rest

def specifications (fields : List Field) : List (Bytes × Kind) :=
  fields.map (fun f => (f.key, f.kind))

def readFields : List (Bytes × Kind) → Bytes → Option (List Bytes × Bytes)
  | [], raw => some ([], raw)
  | (key, kind) :: rest, raw => do
    let raw ← consume (keyPrefix key) raw
    let (value, raw) ← readValue kind (separator rest) raw
    let (values, raw) ← readFields rest raw
    some (value :: values, raw)

theorem separatorSpecifications (fields : List Field) :
    separator (specifications fields) = separator fields := by
  cases fields <;> simp [separator, specifications]

theorem readFieldsEncoded (fields : List Field) (tail : Bytes)
    (valid : ∀ f ∈ fields, ValueValid f.kind f.value) :
    readFields (specifications fields) (encodeFields fields ++ tail) =
      some (fields.map Field.value, tail) := by
  induction fields with
  | nil => rfl
  | cons f rest ih =>
    change readFields ((f.key, f.kind) :: specifications rest) _ = _
    simp only [readFields, encodeFields, List.append_assoc, consumeAppend,
      bind, Option.bind, separatorSpecifications]
    rw [show [separator rest] ++ (encodeFields rest ++ tail) =
      separator rest :: (encodeFields rest ++ tail) from rfl]
    rw [readValueEncoded f.kind f.value _ (separator rest) (separatorValid rest)
      (valid f (by simp))]
    simp only
    rw [ih (by intro x hx; exact valid x (by simp [hx]))]
    rfl

def encodeObject (fields : List Field) : Bytes := [123] ++ encodeFields fields

def readObject (keys : List (Bytes × Kind)) (raw : Bytes) : Option (List Bytes) := do
  if raw.length ≤ 65536 ∧ keys ≠ [] then do
    let rest ← consume [123] raw
    let (values, rest) ← readFields keys rest
    if rest = [] then some values else none
  else none

theorem readObjectEncoded (fields : List Field)
    (nonempty : fields ≠ []) (bounded : (encodeObject fields).length ≤ 65536)
    (valid : ∀ f ∈ fields, ValueValid f.kind f.value) :
    readObject (specifications fields) (encodeObject fields) = some (fields.map Field.value) := by
  have nonemptyKeys : specifications fields ≠ [] := by simpa [specifications] using nonempty
  unfold readObject
  rw [if_pos ⟨bounded, nonemptyKeys⟩]
  simp only [encodeObject, consumeAppend, bind, Option.bind]
  rw [← List.append_nil (encodeFields fields), readFieldsEncoded fields [] valid]
  rfl

end DeltaReduce.NativeQJson
