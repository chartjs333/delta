import DeltaReduce.NativeReceiptBytes

/-! Fixed native DRC1 VOTE parser and semantic receipt binding. This is a byte
codec, not signature validation, admission, WAL replay or PO-AB1 recovery.
SHA-256 is an explicit executable adapter, not proved by this module. -/
namespace DeltaReduce.NativeVoteBytes
open NativeReceiptBytes

def ascii (s : String) : Bytes := s.toList.map (fun c => UInt8.ofNat c.toNat)
def maxValue : Nat := 4*1024*1024
def maxEnvelope : Nat := 16*1024*1024
def nativeSemantics : Bytes := ascii
  "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"
def textBytes (b : Bytes) : Bytes := [33] ++ sizedBytes b
def TextValid (b : Bytes) : Prop := b.length ≤ maxValue ∧ printable b
instance (b : Bytes) : Decidable (TextValid b) := by unfold TextValid; infer_instance

def readText (raw : Bytes) : Option (Bytes × Bytes) := do
  let rest ← consume [33] raw
  let (value, rest) ← readSection maxValue rest
  if printable value then some (value, rest) else none

theorem readTextEncoded (b tail : Bytes) (valid : TextValid b) :
    readText (textBytes b ++ tail) = some (b, tail) := by
  have bound : b.length < 256^4 := by have := valid.1; unfold maxValue at this; omega
  simp only [readText, textBytes, List.append_assoc, consumeAppend, bind, Option.bind]
  rw [readSectionEncoded b tail maxValue bound valid.1]
  simp [valid.2]

def encodeFields : List (Bytes × Bytes) → Bytes
  | [] => []
  | (key,value)::rest => textBytes key ++ textBytes value ++ encodeFields rest

def readFields : List Bytes → Bytes → Option (List Bytes × Bytes)
  | [], raw => some ([], raw)
  | key::keys, raw => do
    let rest ← consume (textBytes key) raw
    let (value, rest) ← readText rest
    let (values, rest) ← readFields keys rest
    some (value::values, rest)

theorem readFieldsEncoded (fields : List (Bytes × Bytes)) (tail : Bytes)
    (valid : ∀ p ∈ fields, TextValid p.2) :
    readFields (fields.map Prod.fst) (encodeFields fields ++ tail) =
      some (fields.map Prod.snd, tail) := by
  induction fields with
  | nil => rfl
  | cons p rest ih =>
    simp only [List.map_cons, encodeFields, List.append_assoc, readFields, consumeAppend,
      bind, Option.bind]
    rw [readTextEncoded _ _ (valid p (by simp))]
    dsimp only
    rw [ih (by intro q member; exact valid q (by simp [member]))]

structure WireVote where
  bodyHash : Bytes
  context : Bytes
  sequence : Bytes
  height : Bytes
  kind : Bytes
  round : Bytes
  signature : Bytes
  epoch : Bytes
  validator : Bytes
  view : Bytes
  deriving DecidableEq, Repr

def fields (v : WireVote) : List (Bytes × Bytes) :=
  [(ascii "body_hash",v.bodyHash), (ascii "context_id",v.context),
   (ascii "durable_sequence",v.sequence), (ascii "formal_semantics_id",nativeSemantics),
   (ascii "height",v.height), (ascii "kind",v.kind), (ascii "round_id",v.round),
   (ascii "schema_version",ascii "1.0.0"), (ascii "signature_id",v.signature),
   (ascii "type_name",ascii "VOTE"), (ascii "validator_epoch_id",v.epoch),
   (ascii "validator_id",v.validator), (ascii "view",v.view)]

def keys : List Bytes := (fields ⟨[],[],[],[],[],[],[],[],[],[]⟩).map Prod.fst

theorem exactKeys (v : WireVote) : (fields v).map Prod.fst = keys := rfl

def fromValues : List Bytes → Option WireVote
  | [body,context,sequence,semantics,height,kind,round,schema,signature,name,epoch,validator,view] =>
    if semantics = nativeSemantics ∧ schema = ascii "1.0.0" ∧ name = ascii "VOTE" then
      some ⟨body,context,sequence,height,kind,round,signature,epoch,validator,view⟩
    else none
  | _ => none

theorem valuesRetainAllFields (v : WireVote) : fromValues ((fields v).map Prod.snd) = some v := by
  simp [fields, fromValues]

def drcHeader : Bytes := [68,82,67,49,1,0,0,3]
def mapHeader : Bytes := [49,0,0,0,13]
def payload (v : WireVote) : Bytes := mapHeader ++ encodeFields (fields v)
def encodeFrame (v : WireVote) : Bytes := drcHeader ++ sizedBytes (payload v)

def FrameValid (v : WireVote) : Prop :=
  (∀ p ∈ fields v, TextValid p.2) ∧ (encodeFrame v).length ≤ maxEnvelope
instance (v : WireVote) : Decidable (FrameValid v) := by unfold FrameValid; infer_instance

def readFrame (raw : Bytes) : Option WireVote := do
  if raw.length ≤ maxEnvelope then
    let rest ← consume drcHeader raw
    let (body, rest) ← readSection maxEnvelope rest
    if rest = [] then
      let body ← consume mapHeader body
      let (values, rest) ← readFields keys body
      if rest = [] then fromValues values else none
    else none
  else none

theorem frameLength (v : WireVote) : (encodeFrame v).length = 12 + (payload v).length := by
  simp [encodeFrame, sizedBytes, drcHeader, beLength]; omega

theorem readFrameEncoded (v : WireVote) (valid : FrameValid v) :
    readFrame (encodeFrame v) = some v := by
  have small : (payload v).length ≤ maxEnvelope := by have := valid.2; rw [frameLength] at this; omega
  have bound : (payload v).length < 256^4 := by unfold maxEnvelope at small; omega
  unfold readFrame
  rw [if_pos valid.2]
  simp only [encodeFrame, consumeAppend, bind, Option.bind]
  rw [← List.append_nil (sizedBytes (payload v)), readSectionEncoded _ _ _ bound small]
  simp only [↓reduceIte, payload, consumeAppend]
  rw [← exactKeys v, ← List.append_nil (encodeFields (fields v)), readFieldsEncoded _ _ valid.1]
  simpa using valuesRetainAllFields v

def digit (b : UInt8) : Prop := 48 ≤ b.toNat ∧ b.toNat ≤ 57
instance (b : UInt8) : Decidable (digit b) := by unfold digit; infer_instance
def decimalValue (b : Bytes) : Nat := b.foldl (fun n c => n*10+(c.toNat-48)) 0
def DecimalValid (b : Bytes) : Prop :=
  b ≠ [] ∧ (b = [48] ∨ (∃ c ∈ b.head?, 49 ≤ c.toNat ∧ c.toNat ≤ 57)) ∧
  (∀ c ∈ b, digit c) ∧ decimalValue b < 256^8
instance (b : Bytes) : Decidable (DecimalValid b) := by unfold DecimalValid; infer_instance
def parseDecimal (b : Bytes) : Option Nat := if DecimalValid b then some (decimalValue b) else none

theorem decimalSound {b n} (ok : parseDecimal b = some n) :
    DecimalValid b ∧ n = decimalValue b := by
  unfold parseDecimal at ok
  split at ok
  · exact ⟨‹DecimalValid b›, (Option.some.inj ok).symm⟩
  · contradiction

def hexDigit (b : UInt8) : Prop :=
  (48 ≤ b.toNat ∧ b.toNat ≤ 57) ∨ (97 ≤ b.toNat ∧ b.toNat ≤ 102)
instance (b : UInt8) : Decidable (hexDigit b) := by unfold hexDigit; infer_instance
def ContentId (b : Bytes) : Prop :=
  b.length = 71 ∧ b.take 7 = ascii "sha256:" ∧ ∀ c ∈ b.drop 7, hexDigit c
instance (b : Bytes) : Decidable (ContentId b) := by unfold ContentId; infer_instance
def IdentitiesValid (v : WireVote) : Prop :=
  ContentId v.bodyHash ∧ ContentId v.signature ∧ ContentId v.epoch ∧
  v.context ≠ [] ∧ v.kind ≠ [] ∧ v.round ≠ [] ∧ v.validator ≠ []
instance (v : WireVote) : Decidable (IdentitiesValid v) := by unfold IdentitiesValid; infer_instance

structure Vote where
  wire : WireVote
  sequence : Nat
  height : Nat
  view : Nat
  deriving DecidableEq, Repr

def VoteValid (v : Vote) : Prop :=
  FrameValid v.wire ∧ IdentitiesValid v.wire ∧ 0 < v.sequence ∧
  parseDecimal v.wire.sequence = some v.sequence ∧
  parseDecimal v.wire.height = some v.height ∧ parseDecimal v.wire.view = some v.view
instance (v : Vote) : Decidable (VoteValid v) := by unfold VoteValid; infer_instance

def interpret (w : WireVote) : Option Vote := do
  let sequence ← parseDecimal w.sequence
  let height ← parseDecimal w.height
  let view ← parseDecimal w.view
  let v := Vote.mk w sequence height view
  if VoteValid v then some v else none

theorem interpretValid (v : Vote) (valid : VoteValid v) : interpret v.wire = some v := by
  rcases valid with ⟨f,i,s,a,b,c⟩
  simp only [interpret, a, b, c, bind, Option.bind]
  cases v
  exact if_pos ⟨f,i,s,a,b,c⟩

theorem interpretedSound {w v} (ok : interpret w = some v) : v.wire = w ∧ VoteValid v := by
  unfold interpret at ok
  cases a : parseDecimal w.sequence with
  | none => simp [a] at ok
  | some sequence =>
    simp only [a, bind, Option.bind] at ok
    cases b : parseDecimal w.height with
    | none => simp [b] at ok
    | some height =>
      simp only [b] at ok
      cases c : parseDecimal w.view with
      | none => simp [c] at ok
      | some view =>
        simp only [c] at ok
        split at ok
        · cases Option.some.inj ok
          exact ⟨rfl, ‹VoteValid _›⟩
        · contradiction

def decodeFrame (raw : Bytes) : Option Vote := do
  let w ← readFrame raw
  let v ← interpret w
  if encodeFrame w = raw then some v else none

theorem decodeFrameEncoded (v : Vote) (valid : VoteValid v) :
    decodeFrame (encodeFrame v.wire) = some v := by
  simp [decodeFrame, readFrameEncoded _ valid.1, interpretValid _ valid]

theorem decodeFrameFromEncoding (v : Vote) (raw : Bytes) (valid : VoteValid v)
    (bytes : encodeFrame v.wire = raw) : decodeFrame raw = some v := by
  rw [← bytes]
  exact decodeFrameEncoded v valid

theorem decodedVoteSound {raw v} (ok : decodeFrame raw = some v) :
    VoteValid v ∧ encodeFrame v.wire = raw := by
  unfold decodeFrame at ok
  cases a : readFrame raw with
  | none => simp [a] at ok
  | some w =>
    simp only [a, bind, Option.bind] at ok
    cases b : interpret w with
    | none => simp [b] at ok
    | some value =>
      simp only [b] at ok
      split at ok
      · cases Option.some.inj ok
        have h := interpretedSound b
        exact ⟨h.2, h.1 ▸ ‹encodeFrame w = raw›⟩
      · contradiction

theorem wireEncodingInjective {a b : WireVote} (va : FrameValid a) (vb : FrameValid b)
    (same : encodeFrame a = encodeFrame b) : a = b := by
  have h := congrArg readFrame same
  rw [readFrameEncoded _ va, readFrameEncoded _ vb] at h
  exact Option.some.inj h

def actionName : Nat → Bytes
  | 1 => ascii "ROUND_CONFIG" | 2 => ascii "ISC" | 3 => ascii "EC" | 4 => ascii "APC"
  | 5 => ascii "PARAMETER" | 6 => ascii "AGGREGATE_ROOT" | 7 => ascii "APPLY"
  | 8 => ascii "VIEW_CHANGE" | 9 => ascii "ABORT" | _ => []

def votePreimage (frame : Bytes) : Bytes := ascii "deltareduce:003:vote:v1" ++ [0] ++ frame
def hexNibble (n : Nat) : UInt8 := UInt8.ofNat (if n < 10 then 48+n else 87+n)
def hexBytes (bytes : Bytes) : Bytes := bytes.flatMap (fun b =>
  [hexNibble (b.toNat / 16), hexNibble (b.toNat % 16)])
def voteId (sha256 : Bytes → Bytes) (frame : Bytes) : Option Bytes :=
  let digest := sha256 (votePreimage frame)
  if digest.length = 32 then some (ascii "sha256:" ++ hexBytes digest) else none

def ReceiptLinked (sha256 : Bytes → Bytes) (r : Receipt) (v : Vote) : Prop :=
  r.sequence = v.sequence ∧ r.context = v.wire.context ∧
  actionName r.action = v.wire.kind ∧ voteId sha256 r.frame = some r.voteId
instance (sha256 : Bytes → Bytes) (r : Receipt) (v : Vote) :
    Decidable (ReceiptLinked sha256 r v) := by unfold ReceiptLinked; infer_instance

def bindReceipt (sha256 : Bytes → Bytes) (r : Receipt) : Option Vote := do
  let v ← decodeFrame r.frame
  if ReceiptLinked sha256 r v then some v else none

def decodeReceipt (sha256 : Bytes → Bytes) (raw : Bytes) : Option (Receipt × Vote) := do
  let r ← NativeReceiptBytes.decode raw
  let v ← bindReceipt sha256 r
  some (r,v)

theorem bindingSound {sha256 r v} (ok : bindReceipt sha256 r = some v) :
    decodeFrame r.frame = some v ∧ ReceiptLinked sha256 r v := by
  unfold bindReceipt at ok
  cases h : decodeFrame r.frame with
  | none => simp [h] at ok
  | some value =>
    simp only [h, bind, Option.bind] at ok
    split at ok
    · cases Option.some.inj ok
      exact ⟨rfl, ‹ReceiptLinked sha256 r v›⟩
    · contradiction

theorem bindingFromComponents (sha256 : Bytes → Bytes) (r : Receipt) (v : Vote)
    (frame : decodeFrame r.frame = some v) (linked : ReceiptLinked sha256 r v) :
    bindReceipt sha256 r = some v := by simp [bindReceipt, frame, linked]

theorem bindingRejectsMismatch (sha256 : Bytes → Bytes) (r : Receipt) (v : Vote)
    (frame : decodeFrame r.frame = some v) (different : ¬ ReceiptLinked sha256 r v) :
    bindReceipt sha256 r = none := by simp [bindReceipt, frame, different]

theorem receiptFromComponents (sha256 : Bytes → Bytes) (r : Receipt) (v : Vote)
    (valid : Valid r) (bound : bindReceipt sha256 r = some v) :
    decodeReceipt sha256 (encode r) = some (r,v) := by
  simp [decodeReceipt, decodeEncoded _ valid, bound]

theorem receiptFromNativeBytes (sha256 : Bytes → Bytes) (r : Receipt) (v : Vote)
    (raw : Bytes) (valid : Valid r) (bound : bindReceipt sha256 r = some v)
    (bytes : encode r = raw) : decodeReceipt sha256 raw = some (r,v) := by
  rw [← bytes]
  exact receiptFromComponents sha256 r v valid bound

theorem semanticReceiptSound {sha256 raw r v}
    (ok : decodeReceipt sha256 raw = some (r,v)) :
    NativeReceiptBytes.decode raw = some r ∧ decodeFrame r.frame = some v ∧
    Valid r ∧ VoteValid v ∧ encode r = raw ∧ encodeFrame v.wire = r.frame ∧
    ReceiptLinked sha256 r v := by
  unfold decodeReceipt at ok
  cases a : NativeReceiptBytes.decode raw with
  | none => simp [a] at ok
  | some record =>
    simp only [a, bind, Option.bind] at ok
    cases b : bindReceipt sha256 record with
    | none => simp [b] at ok
    | some vote =>
      simp only [b] at ok
      cases Option.some.inj ok
      have link := bindingSound b
      have decoded := decodedVoteSound link.1
      exact ⟨rfl, link.1, decodedValid a, decoded.1, decodedCanonical a, decoded.2, link.2⟩

theorem contentIdUsesExactPreimage {sha256 frame id} (ok : voteId sha256 frame = some id) :
    (sha256 (ascii "deltareduce:003:vote:v1" ++ [0] ++ frame)).length = 32 ∧
    id = ascii "sha256:" ++ hexBytes (sha256 (votePreimage frame)) := by
  unfold voteId at ok
  dsimp only at ok
  split at ok
  · exact ⟨‹_›, (Option.some.inj ok).symm⟩
  · contradiction

theorem hexadecimalLength (bytes : Bytes) : (hexBytes bytes).length = 2 * bytes.length := by
  induction bytes with
  | nil => rfl
  | cons b rest ih =>
    simp only [hexBytes, List.flatMap_cons, List.length_append, List.length_cons, List.length_nil]
    change 2 + (hexBytes rest).length = 2 * (rest.length + 1)
    rw [ih]; omega

theorem contentIdLength {sha256 frame id} (ok : voteId sha256 frame = some id) :
    id.length = 71 := by
  obtain ⟨width, exactId⟩ := contentIdUsesExactPreimage ok
  rw [exactId, List.length_append, hexadecimalLength]
  have prefixSize : (ascii "sha256:").length = 7 := by decide
  rw [prefixSize]
  change (sha256 (votePreimage frame)).length = 32 at width
  omega

theorem decodedNativeNumberBounds {raw v} (ok : decodeFrame raw = some v) :
    0 < v.sequence ∧ v.sequence < 256^8 ∧ v.height < 256^8 ∧ v.view < 256^8 := by
  obtain ⟨_,_,positive,sequence,height,view⟩ := (decodedVoteSound ok).1
  have s := decimalSound sequence
  have h := decimalSound height
  have w := decimalSound view
  exact ⟨positive, s.2 ▸ s.1.2.2.2, h.2 ▸ h.1.2.2.2, w.2 ▸ w.1.2.2.2⟩

theorem decodedNativeIdentities {raw v} (ok : decodeFrame raw = some v) :
    ContentId v.wire.bodyHash ∧ ContentId v.wire.signature ∧ ContentId v.wire.epoch ∧
    v.wire.context ≠ [] ∧ v.wire.kind ≠ [] ∧ v.wire.round ≠ [] ∧ v.wire.validator ≠ [] :=
  (decodedVoteSound ok).1.2.1

theorem noUnknownKindReceipt {sha256 raw r v}
    (ok : decodeReceipt sha256 raw = some (r,v)) :
    1 ≤ r.action ∧ r.action ≤ 9 ∧ v.wire.kind = actionName r.action := by
  have h := semanticReceiptSound ok
  exact ⟨h.2.2.1.1, h.2.2.1.2.1, h.2.2.2.2.2.2.2.2.1.symm⟩

end DeltaReduce.NativeVoteBytes
