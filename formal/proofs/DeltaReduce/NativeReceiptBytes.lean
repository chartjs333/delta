import Std

/-! Exact DVREC001 structural byte codec. General inverse/injectivity proofs
cover the receipt container, not native vote parsing, admission, SHA or WAL.
The complete DRC1 frame is retained as opaque bytes. Its semantic validation
remains a distinct required boundary. No theorem here is PO-AB1 recovery. -/
namespace DeltaReduce.NativeReceiptBytes
abbrev Bytes := List UInt8
def be : Nat → Nat → Bytes
  | 0, _ => []
  | n+1, value => be n (value / 256) ++ [UInt8.ofNat (value % 256)]
def readBE (bytes : Bytes) : Nat := bytes.foldl (fun n b => n * 256 + b.toNat) 0
theorem foldStarting (bytes : Bytes) (a : Nat) :
    bytes.foldl (fun n b => n * 256 + b.toNat) a = a * 256 ^ bytes.length + readBE bytes := by
  induction bytes generalizing a with
  | nil => simp [readBE]
  | cons b rest ih =>
      simp only [List.foldl_cons, List.length_cons, readBE, List.foldl_cons]
      rw [ih, ih]
      simp [Nat.pow_succ, Nat.mul_add, Nat.mul_assoc, Nat.mul_comm, Nat.add_assoc]
theorem readAppend (a b : Bytes) : readBE (a ++ b) = readBE a * 256 ^ b.length + readBE b := by
  simp only [readBE, List.foldl_append]
  exact foldStarting b _
theorem beLength (n value : Nat) : (be n value).length = n := by
  induction n generalizing value with
  | zero => rfl
  | succ n ih => simp [be, ih]
theorem readBeBounded (n value : Nat) (bound : value < 256 ^ n) : readBE (be n value) = value := by
  induction n generalizing value with
  | zero =>
      have : value = 0 := by simpa using bound
      simp [be, readBE, this]
  | succ n ih =>
      have small : value / 256 < 256 ^ n := by
        apply (Nat.div_lt_iff_lt_mul (by decide : 0 < 256)).mpr
        simpa [Nat.pow_succ, Nat.mul_comm] using bound
      rw [be, readAppend, ih _ small]
      simp only [List.length_singleton, readBE, List.foldl_cons, List.foldl_nil,
        Nat.zero_mul, Nat.zero_add, UInt8.toNat_ofNat', show (2^8:Nat) = 256 from rfl, Nat.mod_mod]
      omega





def readNat (width : Nat) (raw : Bytes) : Option (Nat × Bytes) :=
  if width ≤ raw.length then some (readBE (raw.take width), raw.drop width) else none

theorem readNatEncoded (width value : Nat) (tail : Bytes) (bound : value < 256 ^ width) :
    readNat width (be width value ++ tail) = some (value, tail) := by
  unfold readNat
  have len := beLength width value
  have enough : width ≤ (be width value ++ tail).length := by simp [len]
  rw [if_pos enough]
  have take : (be width value ++ tail).take width = be width value := by
    have h : (be width value ++ tail).take (be width value).length = be width value := by simp
    simpa only [len] using h
  have drop : (be width value ++ tail).drop width = tail := by
    have h : (be width value ++ tail).drop (be width value).length = tail := by simp
    simpa only [len] using h
  rw [take, drop, readBeBounded width value bound]

def sizedBytes (bytes : Bytes) : Bytes := be 4 bytes.length ++ bytes

def readSection (limit : Nat) (raw : Bytes) : Option (Bytes × Bytes) := do
  let (n, rest) ← readNat 4 raw
  if n ≤ limit ∧ n ≤ rest.length then some (rest.take n, rest.drop n) else none

theorem readSectionEncoded (bytes tail : Bytes) (limit : Nat)
    (size : bytes.length < 256^4) (bounded : bytes.length ≤ limit) :
    readSection limit (sizedBytes bytes ++ tail) = some (bytes, tail) := by
  simp only [sizedBytes, List.append_assoc, readSection, readNatEncoded 4 _ _ size]
  simp [bounded]

def consume (magic raw : Bytes) : Option Bytes :=
  if raw.take magic.length = magic ∧ magic.length ≤ raw.length then
    some (raw.drop magic.length) else none

theorem consumeAppend (magic tail : Bytes) : consume magic (magic ++ tail) = some tail := by
  simp [consume]

structure Receipt where
  action : Nat
  sequence : Nat
  frame : Bytes
  voteId : Bytes
  context : Bytes
  deriving DecidableEq, Repr

def header : Bytes := [68,86,82,69,67,48,48,49,0,1,0,0,0,0,0,0]
def reserved : Bytes := [0,0,0,0]
def maxFrame : Nat := 16*1024*1024 - 8*1024

def printable (bs : Bytes) : Prop := ∀ b ∈ bs, 32 ≤ b.toNat ∧ b.toNat ≤ 126
instance (bs : Bytes) : Decidable (printable bs) := by unfold printable; infer_instance

def Valid (r : Receipt) : Prop :=
  1 ≤ r.action ∧ r.action ≤ 9 ∧ 0 < r.sequence ∧ r.sequence < 256^8 ∧
  r.frame.length ≤ maxFrame ∧ r.voteId.length ≤ 71 ∧ r.context.length ≤ 4096 ∧
  printable r.voteId ∧ printable r.context
instance (r : Receipt) : Decidable (Valid r) := by unfold Valid; infer_instance

def encode (r : Receipt) : Bytes :=
  header ++ be 4 r.action ++ reserved ++ be 8 r.sequence ++
    sizedBytes r.frame ++ sizedBytes r.voteId ++ sizedBytes r.context

def decodeFields (raw : Bytes) : Option Receipt := do
  if raw.length ≤ 16*1024*1024 then
    let rest ← consume header raw
    let (action, rest) ← readNat 4 rest
    let rest ← consume reserved rest
    let (sequence, rest) ← readNat 8 rest
    let (frame, rest) ← readSection maxFrame rest
    let (voteId, rest) ← readSection 71 rest
    let (context, rest) ← readSection 4096 rest
    if rest = [] then
      let r := Receipt.mk action sequence frame voteId context
      if Valid r then some r else none
    else none
  else none

def decode (raw : Bytes) : Option Receipt := do
  let r ← decodeFields raw
  if Valid r ∧ encode r = raw then some r else none

theorem encodeLength (r : Receipt) :
    (encode r).length = 44 + r.frame.length + r.voteId.length + r.context.length := by
  simp [encode, sizedBytes, header, reserved, beLength]
  omega

theorem validFits (r : Receipt) (valid : Valid r) : (encode r).length ≤ 16*1024*1024 := by
  rw [encodeLength]
  obtain ⟨_,_,_,_,frame,id,context,_,_⟩ := valid
  unfold maxFrame at frame
  omega

theorem decodeFieldsEncoded (r : Receipt) (valid : Valid r) : decodeFields (encode r) = some r := by
  have bounds := valid
  obtain ⟨alo,ahi,slo,shi,frame,id,context,pid,pctx⟩ := bounds
  have action : r.action < 256^4 := by omega
  have fs : r.frame.length < 256^4 := by unfold maxFrame at frame; omega
  have ids : r.voteId.length < 256^4 := by omega
  have cs : r.context.length < 256^4 := by omega
  unfold decodeFields
  rw [if_pos (validFits r valid)]
  simp only [encode, List.append_assoc, consumeAppend]
  simp only [bind, Option.bind, readNatEncoded 4 _ _ action]
  simp only [consumeAppend, readNatEncoded 8 _ _ shi]
  rw [readSectionEncoded _ _ _ fs frame]
  dsimp only
  rw [readSectionEncoded _ _ _ ids id]
  dsimp only
  rw [← List.append_nil (sizedBytes r.context), readSectionEncoded _ _ _ cs context]
  simp [valid]

theorem decodeEncoded (r : Receipt) (valid : Valid r) : decode (encode r) = some r := by
  simp [decode, decodeFieldsEncoded r valid, valid]

theorem encodingInjective {a b : Receipt} (va : Valid a) (vb : Valid b)
    (same : encode a = encode b) : a = b := by
  have equal := congrArg decode same
  rw [decodeEncoded a va, decodeEncoded b vb] at equal
  exact Option.some.inj equal

theorem decodedCanonical {raw r} (accepted : decode raw = some r) : encode r = raw := by
  unfold decode at accepted
  cases result : decodeFields raw with
  | none => simp [result] at accepted
  | some value =>
      simp only [result, bind, Option.bind] at accepted
      split at accepted
      · cases Option.some.inj accepted
        exact ‹Valid r ∧ encode r = raw›.2
      · contradiction

theorem decodedValid {raw r} (accepted : decode raw = some r) : Valid r := by
  unfold decode at accepted
  cases result : decodeFields raw with
  | none => simp [result] at accepted
  | some value =>
      simp only [result, bind, Option.bind] at accepted
      split at accepted
      · cases Option.some.inj accepted
        exact ‹Valid r ∧ encode r = raw›.1
      · contradiction

theorem decodedUnique {raw a b} (left : decode raw = some a) (right : decode raw = some b) : a = b := by
  exact Option.some.inj (left.symm.trans right)

theorem encodedFieldsUnchanged {a b : Receipt} (validA : Valid a) (validB : Valid b)
    (same : encode a = encode b) :
    a.action = b.action ∧ a.sequence = b.sequence ∧ a.frame = b.frame ∧
    a.voteId = b.voteId ∧ a.context = b.context := by
  cases encodingInjective validA validB same
  exact ⟨rfl, rfl, rfl, rfl, rfl⟩

structure Returned where
  proof : Receipt
  replay : Bool
  deriving DecidableEq, Repr

def returnedBytes (r : Returned) : Bytes := encode r.proof

theorem operationalReplayDoesNotRewrite (r : Receipt) (a b : Bool) :
    returnedBytes ⟨r, a⟩ = returnedBytes ⟨r, b⟩ := rfl

theorem decodedReturnRetainsAllFields (r : Returned) (valid : Valid r.proof) :
    decode (returnedBytes r) = some r.proof := decodeEncoded _ valid

theorem reservedMismatch (action : Nat) (tail : Bytes) (bound : action < 256^4) :
    decode (header ++ be 4 action ++ [1,0,0,0] ++ tail) = none := by
  unfold decode decodeFields
  split
  · simp only [List.append_assoc, consumeAppend, readNatEncoded 4 _ _ bound, bind, Option.bind]
    simp [consume, reserved]
  · rfl

end DeltaReduce.NativeReceiptBytes
