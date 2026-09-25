import DeltaReduce.NativeVoteBytes

/-! DRW1 byte relation. SHA is an explicit byte-function parameter. This is
not native admission, physical durability, a scan authenticator or PO-AB1. -/
namespace DeltaReduce.NativeWalBytes
open NativeReceiptBytes

structure Entry where
  sequence : Nat
  kind : Nat
  command : Bytes
  state : Bytes
  effects : Bytes
  record : Bytes
  deriving DecidableEq, Repr

def header : Bytes := [68,82,87,49,0,1,0,0]
def reserved : Bytes := [0,0,0]
def frameSize (e : Entry) : Nat :=
  72 + e.command.length + e.state.length + e.effects.length + e.record.length
def preimage (e : Entry) : Bytes :=
  header ++ be 4 (frameSize e) ++ be 8 e.sequence ++ be 1 e.kind ++ reserved ++
  sizedBytes e.command ++ sizedBytes e.state ++ sizedBytes e.effects ++ sizedBytes e.record
def encode (sha : Bytes → Bytes) (e : Entry) : Bytes := preimage e ++ sha (preimage e)
def Shape (e : Entry) : Prop :=
  (e.kind = 1 ∧ e.command ≠ [] ∧ e.state ≠ [] ∧ e.effects ≠ [] ∧ e.record ≠ []) ∨
  (e.kind = 2 ∧ e.command ≠ [] ∧ e.state = [] ∧ e.effects = [])
instance (e : Entry) : Decidable (Shape e) := by unfold Shape; infer_instance
def Valid (e : Entry) : Prop := e.sequence < 256^8 ∧ frameSize e < 256^4 ∧ Shape e
instance (e : Entry) : Decidable (Valid e) := by unfold Valid; infer_instance

theorem preimageLength (e : Entry) : (preimage e).length + 32 = frameSize e := by
  simp [preimage, frameSize, header, reserved, sizedBytes, beLength]; omega

theorem encodeLength (sha : Bytes → Bytes) (e : Entry)
    (digest : (sha (preimage e)).length = 32) : (encode sha e).length = frameSize e := by
  simp only [encode, List.length_append, digest]; exact preimageLength e

def readFields (raw : Bytes) : Option Entry := do
  let rest ← consume header raw
  let (size, rest) ← readNat 4 rest
  let (sequence, rest) ← readNat 8 rest
  let (kind, rest) ← readNat 1 rest
  let rest ← consume reserved rest
  let (command, rest) ← readSection (256^4-1) rest
  let (state, rest) ← readSection (256^4-1) rest
  let (effects, rest) ← readSection (256^4-1) rest
  let (record, rest) ← readSection (256^4-1) rest
  let e := Entry.mk sequence kind command state effects record
  if rest = [] ∧ size = raw.length + 32 ∧ Valid e then some e else none

theorem readFieldsEncoded (e : Entry) (valid : Valid e) : readFields (preimage e) = some e := by
  have bounds := valid
  obtain ⟨seq, size, shape⟩ := bounds
  have kind : e.kind < 256 := by rcases shape with h | h <;> omega
  have c : e.command.length < 256^4 := by unfold frameSize at size; omega
  have s : e.state.length < 256^4 := by unfold frameSize at size; omega
  have f : e.effects.length < 256^4 := by unfold frameSize at size; omega
  have r : e.record.length < 256^4 := by unfold frameSize at size; omega
  have cb : e.command.length ≤ 256^4-1 := by omega
  have sb : e.state.length ≤ 256^4-1 := by omega
  have fb : e.effects.length ≤ 256^4-1 := by omega
  have rb : e.record.length ≤ 256^4-1 := by omega
  unfold readFields
  simp only [preimage, List.append_assoc, consumeAppend, bind, Option.bind,
    readNatEncoded 4 _ _ size, readNatEncoded 8 _ _ seq, readNatEncoded 1 _ _ kind]
  rw [readSectionEncoded _ _ _ c cb]; dsimp only
  rw [readSectionEncoded _ _ _ s sb]; dsimp only
  rw [readSectionEncoded _ _ _ f fb]; dsimp only
  have last := readSectionEncoded e.record [] (256^4-1) r rb
  simp only [List.append_nil] at last
  rw [last]; dsimp only
  split
  · rfl
  · rename_i failed
    apply False.elim
    apply failed
    refine ⟨rfl, ?_, valid⟩
    simp only [List.length_append, beLength, sizedBytes]
    simp [header, reserved, frameSize]
    omega

def decode (sha : Bytes → Bytes) (raw : Bytes) : Option Entry := do
  if 72 ≤ raw.length then
    let bytes := raw.take (raw.length-32)
    let checksum := raw.drop (raw.length-32)
    if sha bytes = checksum ∧ checksum.length = 32 then
      let e ← readFields bytes
      if Valid e ∧ preimage e = bytes then some e else none
    else none
  else none

theorem decodeEncoded (sha : Bytes → Bytes) (e : Entry) (valid : Valid e)
    (digest : (sha (preimage e)).length = 32) : decode sha (encode sha e) = some e := by
  have len := preimageLength e
  have size : 72 ≤ frameSize e := by unfold frameSize; omega
  have splitSize : (encode sha e).length - 32 = (preimage e).length := by
    rw [encodeLength sha e digest]; omega
  have take : (encode sha e).take ((encode sha e).length-32) = preimage e := by
    rw [splitSize]; simp [encode]
  have drop : (encode sha e).drop ((encode sha e).length-32) = sha (preimage e) := by
    rw [splitSize]; simp [encode]
  unfold decode
  rw [if_pos (by rw [encodeLength sha e digest]; exact size)]
  dsimp only
  rw [take, drop]
  rw [if_pos ⟨rfl, digest⟩]
  rw [readFieldsEncoded e valid]
  simp only [bind, Option.bind]
  simp only [valid, and_self, if_true]

theorem decodedSound (sha : Bytes → Bytes) (raw : Bytes) (e : Entry)
    (ok : decode sha raw = some e) :
    Valid e ∧ preimage e = raw.take (raw.length-32) ∧
    sha (preimage e) = raw.drop (raw.length-32) ∧ (sha (preimage e)).length = 32 := by
  unfold decode at ok
  split at ok
  · dsimp only at ok
    split at ok
    · rename_i hash
      cases h : readFields (raw.take (raw.length-32)) with
      | none => simp [h] at ok
      | some value =>
        simp only [h, bind, Option.bind] at ok
        split at ok
        · rename_i accepted
          cases Option.some.inj ok
          exact ⟨accepted.1, accepted.2, accepted.2 ▸ hash.1, by rw [accepted.2, hash.1]; exact hash.2⟩
        · contradiction
    · contradiction
  · contradiction

theorem decodedCanonical (sha : Bytes → Bytes) (raw : Bytes) (e : Entry)
    (ok : decode sha raw = some e) : encode sha e = raw := by
  have h := decodedSound sha raw e ok
  unfold encode
  rw [h.2.2.1, h.2.1, List.take_append_drop]

theorem encodingInjective (sha : Bytes → Bytes) (a b : Entry)
    (va : Valid a) (vb : Valid b) (ha : (sha (preimage a)).length = 32)
    (hb : (sha (preimage b)).length = 32) (same : encode sha a = encode sha b) : a = b := by
  have h := congrArg (decode sha) same
  rw [decodeEncoded sha a va ha, decodeEncoded sha b vb hb] at h
  exact Option.some.inj h

theorem decodeFromBytes (sha : Bytes → Bytes) (e : Entry) (raw : Bytes)
    (valid : Valid e) (digest : (sha (preimage e)).length = 32)
    (bytes : encode sha e = raw) : decode sha raw = some e := by
  rw [← bytes]; exact decodeEncoded sha e valid digest

/- Scanner classifies a short header before inspecting its magic, as native Wal
does. It does not authenticate absence, truncate files, or check admission. -/
inductive Head where
  | done
  | torn
  | corrupt
  | frame (entry : Entry) (size : Nat) (rest : Bytes)
  deriving DecidableEq, Repr

def scanHead (sha : Bytes → Bytes) (raw : Bytes) : Head :=
  if raw = [] then .done
  else if raw.length < 12 then .torn
  else match consume header raw with
    | none => .corrupt
    | some rest => match readNat 4 rest with
      | none => .corrupt
      | some (size, _) =>
        if 72 ≤ size ∧ size ≤ 64*1024*1024 then
          if raw.length < size then .torn
          else match decode sha (raw.take size) with
            | none => .corrupt
            | some e => .frame e size (raw.drop size)
        else .corrupt

theorem shortHeaderIsIncomplete (sha : Bytes → Bytes) (raw : Bytes)
    (nonempty : raw ≠ []) (short : raw.length < 12) : scanHead sha raw = .torn := by
  simp [scanHead, nonempty, short]

theorem scannedFrameSound (sha : Bytes → Bytes) (raw rest : Bytes) (e : Entry) (size : Nat)
    (ok : scanHead sha raw = .frame e size rest) :
    72 ≤ size ∧ size ≤ 64*1024*1024 ∧ size ≤ raw.length ∧
    decode sha (raw.take size) = some e ∧ raw = raw.take size ++ rest := by
  unfold scanHead at ok
  split at ok
  · contradiction
  · split at ok
    · contradiction
    · cases h : consume header raw with
      | none => simp [h] at ok
      | some tail =>
        simp only [h] at ok
        cases n : readNat 4 tail with
        | none => simp [n] at ok
        | some pair =>
          obtain ⟨count,remaining⟩ := pair
          simp only [n] at ok
          split at ok
          · rename_i bounded
            split at ok
            · contradiction
            · rename_i complete
              cases d : decode sha (raw.take count) with
              | none => simp [d] at ok
              | some value =>
                simp only [d] at ok
                cases ok
                exact ⟨bounded.1,bounded.2,by omega,d,(List.take_append_drop size raw).symm⟩
          · contradiction

/- Runtime sequence admission is a distinct all-entry check, including state
commands. It is not vote count, state durable_sequence or a semantic replay. -/
def orderedFrom : Nat → List Entry → Bool
  | _, [] => true
  | next, e::rest => decide (e.sequence = next) && orderedFrom (next+1) rest

theorem orderedCons (next : Nat) (e : Entry) (rest : List Entry) :
    orderedFrom next (e::rest) = true ↔ e.sequence = next ∧ orderedFrom (next+1) rest = true := by
  simp [orderedFrom]

theorem orderedPosition (next : Nat) (entries : List Entry) (i : Nat) (e : Entry)
    (ok : orderedFrom next entries = true) (atIndex : entries[i]? = some e) :
    e.sequence = next + i := by
  induction entries generalizing next i with
  | nil => simp at atIndex
  | cons first rest ih =>
    obtain ⟨firstSeq, tail⟩ := (orderedCons next first rest).mp ok
    cases i with
    | zero => simp only [List.getElem?_cons_zero] at atIndex
              cases Option.some.inj atIndex; simpa using firstSeq
    | succ i =>
      have h := ih (next+1) i tail atIndex
      omega

def policyId (sha : Bytes → Bytes) (policy : Bytes) : Option Bytes :=
  if (sha policy).length = 32 then some (NativeVoteBytes.hexBytes (sha policy)) else none

theorem policyUsesWholeBytes (sha : Bytes → Bytes) (policy id : Bytes)
    (ok : policyId sha policy = some id) :
    id = NativeVoteBytes.hexBytes (sha policy) ∧ id.length = 64 := by
  unfold policyId at ok
  split at ok
  · rename_i size
    cases Option.some.inj ok
    exact ⟨rfl, by rw [NativeVoteBytes.hexadecimalLength, size]⟩
  · contradiction

def ReceiptLink (sha : Bytes → Bytes) (policy : Bytes) (e : Entry) (r : Receipt) : Prop :=
  e.kind = 2 ∧ e.sequence = r.sequence ∧ e.command = r.frame ∧
  e.state = [] ∧ e.effects = [] ∧ policyId sha policy = some e.record
instance (sha : Bytes → Bytes) (policy : Bytes) (e : Entry) (r : Receipt) :
    Decidable (ReceiptLink sha policy e r) := by unfold ReceiptLink; infer_instance

def bindReceipt (sha : Bytes → Bytes) (policy wal receipt : Bytes) :
    Option (Entry × Receipt × NativeVoteBytes.Vote) := do
  let e ← decode sha wal
  let (r,v) ← NativeVoteBytes.decodeReceipt sha receipt
  if ReceiptLink sha policy e r then some (e,r,v) else none

theorem bindFromComponents (sha : Bytes → Bytes) (policy wal receipt : Bytes)
    (e : Entry) (r : Receipt) (v : NativeVoteBytes.Vote)
    (entry : decode sha wal = some e)
    (vote : NativeVoteBytes.decodeReceipt sha receipt = some (r,v))
    (linked : ReceiptLink sha policy e r) : bindReceipt sha policy wal receipt = some (e,r,v) := by
  simp [bindReceipt, entry, vote, linked]

theorem bindingSound (sha : Bytes → Bytes) (policy wal receipt : Bytes)
    (e : Entry) (r : Receipt) (v : NativeVoteBytes.Vote)
    (ok : bindReceipt sha policy wal receipt = some (e,r,v)) :
    decode sha wal = some e ∧ NativeVoteBytes.decodeReceipt sha receipt = some (r,v) ∧
    ReceiptLink sha policy e r := by
  unfold bindReceipt at ok
  cases a : decode sha wal with
  | none => simp [a] at ok
  | some entry =>
    simp only [a, bind, Option.bind] at ok
    cases b : NativeVoteBytes.decodeReceipt sha receipt with
    | none => simp [b] at ok
    | some pair =>
      obtain ⟨record,vote⟩ := pair
      simp only [b] at ok
      split at ok
      · cases Option.some.inj ok
        exact ⟨rfl,rfl,‹_›⟩
      · contradiction

theorem boundOriginalBytes (sha : Bytes → Bytes) (policy wal receipt : Bytes)
    (e : Entry) (r : Receipt) (v : NativeVoteBytes.Vote)
    (ok : bindReceipt sha policy wal receipt = some (e,r,v)) :
    encode sha e = wal ∧ NativeReceiptBytes.encode r = receipt ∧
    NativeVoteBytes.encodeFrame v.wire = e.command ∧ e.sequence = v.sequence := by
  have h := bindingSound sha policy wal receipt e r v ok
  have vinfo := NativeVoteBytes.semanticReceiptSound h.2.1
  have link := h.2.2
  exact ⟨decodedCanonical sha wal e h.1, vinfo.2.2.2.2.1,
    vinfo.2.2.2.2.2.1.trans link.2.2.1.symm,
    link.2.1.trans vinfo.2.2.2.2.2.2.1⟩

end DeltaReduce.NativeWalBytes
