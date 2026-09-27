import DeltaReduce.NativeReceiptBytes

/-!
Original feature-004 DRQ1 framing and ordered INT16 payload decoding.
Header JSON, payload SHA, source identity and admission are separate obligations.
No mathematical vector or acceptance flag is supplied to this decoder.
-/
namespace DeltaReduce.NativeQBytes
open NativeReceiptBytes

def le (width value : Nat) : Bytes := (be width value).reverse
def readLE (raw : Bytes) : Nat := readBE raw.reverse

theorem leLength (width value : Nat) : (le width value).length = width := by
  simp [le, beLength]

theorem readLeBounded (width value : Nat) (bound : value < 256 ^ width) :
    readLE (le width value) = value := by
  simpa [le, readLE] using readBeBounded width value bound

def readLENat (width : Nat) (raw : Bytes) : Option (Nat × Bytes) :=
  if width ≤ raw.length then some (readLE (raw.take width), raw.drop width)
  else none

theorem readLENatEncoded (width value : Nat) (tail : Bytes)
    (bound : value < 256 ^ width) :
    readLENat width (le width value ++ tail) = some (value, tail) := by
  unfold readLENat
  have len := leLength width value
  have enough : width ≤ (le width value ++ tail).length := by simp [len]
  rw [if_pos enough]
  have take : (le width value ++ tail).take width = le width value := by
    have h : (le width value ++ tail).take (le width value).length = le width value := by simp
    simpa only [len] using h
  have drop : (le width value ++ tail).drop width = tail := by
    have h : (le width value ++ tail).drop (le width value).length = tail := by simp
    simpa only [len] using h
  rw [take, drop, readLeBounded width value bound]

def word (lo hi : UInt8) : Nat := lo.toNat + 256 * hi.toNat

theorem pairLittleEndian (lo hi : UInt8) : readLE [lo, hi] = word lo hi := by
  simp [readLE, readBE, word, Nat.mul_comm, Nat.add_comm]

def signed (lo hi : UInt8) : Int :=
  let n := word lo hi
  if n < 32768 then Int.ofNat n else Int.ofNat n - 65536

theorem wordBound (lo hi : UInt8) : word lo hi < 65536 := by
  have hlo := lo.toNat_lt
  have hhi := hi.toNat_lt
  unfold word
  omega

theorem signedRange (lo hi : UInt8) (valid : word lo hi ≠ 32768) :
    -32767 ≤ signed lo hi ∧ signed lo hi ≤ 32767 := by
  have bounded := wordBound lo hi
  by_cases small : word lo hi < 32768
  · simp [signed, small]; omega
  · simp [signed, small]; omega

def decodePayload : Bytes → Option (List Int)
  | [] => some []
  | [_] => none
  | lo :: hi :: tail =>
    if word lo hi = 32768 then none
    else (decodePayload tail).map (signed lo hi :: ·)

inductive PayloadRelation : Bytes → List Int → Prop
  | nil : PayloadRelation [] []
  | cons (lo hi : UInt8) (tail : Bytes) (values : List Int)
      (valid : word lo hi ≠ 32768) (rest : PayloadRelation tail values) :
      PayloadRelation (lo :: hi :: tail) (signed lo hi :: values)

theorem payloadDecoded (raw : Bytes) (values : List Int)
    (h : decodePayload raw = some values) : PayloadRelation raw values := by
  match raw with
  | [] => simp [decodePayload] at h; subst values; exact .nil
  | [_] => simp [decodePayload] at h
  | lo :: hi :: tail =>
    by_cases bad : word lo hi = 32768
    · simp [decodePayload, bad] at h
    · cases hr : decodePayload tail with
      | none => simp [decodePayload, bad, hr] at h
      | some rest =>
        simp [decodePayload, bad, hr] at h
        subst values
        exact .cons lo hi tail rest bad (payloadDecoded tail rest hr)

theorem payloadComplete {raw : Bytes} {values : List Int}
    (h : PayloadRelation raw values) : decodePayload raw = some values := by
  induction h with
  | nil => rfl
  | cons lo hi tail values valid rest ih => simp [decodePayload, valid, ih]

theorem payloadLength {raw : Bytes} {values : List Int}
    (h : PayloadRelation raw values) : raw.length = 2 * values.length := by
  induction h with
  | nil => rfl
  | cons lo hi tail values valid rest ih => simp_all; omega

theorem payloadRange {raw : Bytes} {values : List Int}
    (h : PayloadRelation raw values) :
    ∀ x ∈ values, -32767 ≤ x ∧ x ≤ 32767 := by
  induction h with
  | nil => simp
  | cons lo hi tail values valid rest ih =>
    intro x hx
    rcases List.mem_cons.mp hx with hx | hx
    · subst x; exact signedRange lo hi valid
    · exact ih x hx

/-- Position is retained, including zeros and duplicate coordinates. -/
theorem payloadAt {raw : Bytes} {values : List Int}
    (h : PayloadRelation raw values) (i : Nat) (inside : i < values.length) :
    ∃ lo hi, raw[2 * i]? = some lo ∧ raw[2 * i + 1]? = some hi ∧
      values[i]? = some (signed lo hi) ∧ word lo hi ≠ 32768 := by
  induction h generalizing i with
  | nil => simp at inside
  | cons lo hi tail values valid rest ih =>
    cases i with
    | zero => exact ⟨lo, hi, rfl, rfl, rfl, valid⟩
    | succ i =>
      have bound : i < values.length := by simpa using inside
      obtain ⟨a, b, ha, hb, hv, hab⟩ := ih i bound
      refine ⟨a, b, ?_, ?_, ?_, hab⟩
      · simpa [Nat.mul_add, Nat.add_assoc] using ha
      · simpa [Nat.mul_add, Nat.add_assoc] using hb
      · simpa using hv

theorem payloadUnique {raw : Bytes} {a b : List Int}
    (ha : PayloadRelation raw a) (hb : PayloadRelation raw b) : a = b := by
  have ea := payloadComplete ha
  have eb := payloadComplete hb
  rw [ea] at eb
  exact Option.some.inj eb

def magic : Bytes := [68, 82, 81, 49, 1, 0, 0, 0]
def maxHeader : Nat := 65536
def maxPayload : Nat := 1048576

structure Frame where
  header : Bytes
  payload : Bytes
  values : List Int
  deriving DecidableEq, Repr

def encodeFrame (header payload : Bytes) : Bytes :=
  magic ++ le 4 header.length ++ le 4 payload.length ++ header ++ payload

/-- Framing only: the header is preserved as bytes, not admitted as JSON. -/
def decodeFields (raw : Bytes) : Option Frame := do
  if raw.length > 16 + maxHeader + maxPayload then none else do
    let rest ← consume magic raw
    let (nh, rest) ← readLENat 4 rest
    let (np, rest) ← readLENat 4 rest
    if 0 < nh ∧ nh ≤ maxHeader ∧ 0 < np ∧ np ≤ maxPayload ∧
        nh + np = rest.length then do
      let header := rest.take nh
      let payload := rest.drop nh
      let values ← decodePayload payload
      some ⟨header, payload, values⟩
    else none

def decode (raw : Bytes) : Option Frame := do
  let frame ← decodeFields raw
  if encodeFrame frame.header frame.payload = raw then some frame else none

theorem decodedFields {raw : Bytes} {frame : Frame} (h : decode raw = some frame) :
    decodeFields raw = some frame ∧ encodeFrame frame.header frame.payload = raw := by
  unfold decode at h
  cases e : decodeFields raw with
  | none => simp [e] at h
  | some f =>
    simp [e] at h
    rcases h with ⟨same, eq⟩
    subst f
    exact ⟨rfl, same⟩

theorem fieldsPayload {raw : Bytes} {frame : Frame}
    (h : decodeFields raw = some frame) :
    PayloadRelation frame.payload frame.values ∧
    0 < frame.header.length ∧ frame.header.length ≤ maxHeader ∧
    0 < frame.payload.length ∧ frame.payload.length ≤ maxPayload := by
  unfold decodeFields at h
  split at h
  · contradiction
  · cases e : consume magic raw with
    | none => simp [e] at h
    | some rest =>
      simp only [e, bind, Option.bind] at h
      cases e1 : readLENat 4 rest with
      | none => simp [e1] at h
      | some p =>
        rcases p with ⟨nh, r1⟩
        simp only [e1] at h
        cases e2 : readLENat 4 r1 with
        | none => simp [e2] at h
        | some p =>
          rcases p with ⟨np, r2⟩
          simp only [e2] at h
          split at h
          · rename_i good
            cases ep : decodePayload (r2.drop nh) with
            | none => simp [ep] at h
            | some values =>
              simp only [ep, Option.some.injEq] at h
              subst frame
              have rel := payloadDecoded _ _ ep
              have htake : (r2.take nh).length = nh := by simp; omega
              have hdrop : (r2.drop nh).length = np := by simp; omega
              exact ⟨rel, by simpa [htake] using good.1,
                by simpa [htake] using good.2.1,
                by simpa [hdrop] using good.2.2.1,
                by simpa [hdrop] using good.2.2.2.1⟩
          · contradiction

theorem decodedPayload {raw : Bytes} {frame : Frame} (h : decode raw = some frame) :
    PayloadRelation frame.payload frame.values :=
  (fieldsPayload (decodedFields h).1).1

theorem decodedLength {raw : Bytes} {frame : Frame} (h : decode raw = some frame) :
    frame.payload.length = 2 * frame.values.length := payloadLength (decodedPayload h)

theorem decodedRange {raw : Bytes} {frame : Frame} (h : decode raw = some frame) :
    ∀ x ∈ frame.values, -32767 ≤ x ∧ x ≤ 32767 := payloadRange (decodedPayload h)


theorem encodeLength (header payload : Bytes) :
    (encodeFrame header payload).length = 16 + header.length + payload.length := by
  simp [encodeFrame, magic, leLength, Nat.add_assoc]; omega

theorem fieldsEncoded (header payload : Bytes) (values : List Int)
    (hpos : 0 < header.length) (hbound : header.length ≤ maxHeader)
    (ppos : 0 < payload.length) (pbound : payload.length ≤ maxPayload)
    (decoded : decodePayload payload = some values) :
    decodeFields (encodeFrame header payload) = some ⟨header, payload, values⟩ := by
  have hsize : header.length < 256 ^ 4 := by unfold maxHeader at hbound; omega
  have psize : payload.length < 256 ^ 4 := by unfold maxPayload at pbound; omega
  have total : ¬ (encodeFrame header payload).length > 16 + maxHeader + maxPayload := by
    rw [encodeLength]; omega
  unfold decodeFields
  rw [if_neg total]
  simp only [encodeFrame, List.append_assoc,
    consumeAppend, bind, Option.bind, readLENatEncoded 4 _ _ hsize,
    readLENatEncoded 4 _ _ psize]
  simp [hpos, hbound, ppos, pbound, decoded]

theorem frameEncoded (header payload : Bytes) (values : List Int)
    (hpos : 0 < header.length) (hbound : header.length ≤ maxHeader)
    (ppos : 0 < payload.length) (pbound : payload.length ≤ maxPayload)
    (decoded : decodePayload payload = some values) :
    decode (encodeFrame header payload) = some ⟨header, payload, values⟩ := by
  simp [decode, fieldsEncoded header payload values hpos hbound ppos pbound decoded]

theorem frameFromRelation (header payload : Bytes) (values : List Int)
    (hpos : 0 < header.length) (hbound : header.length ≤ maxHeader)
    (ppos : 0 < payload.length) (pbound : payload.length ≤ maxPayload)
    (relation : PayloadRelation payload values) :
    decode (encodeFrame header payload) = some ⟨header, payload, values⟩ :=
  frameEncoded header payload values hpos hbound ppos pbound (payloadComplete relation)

theorem decodedNonempty {raw : Bytes} {frame : Frame} (h : decode raw = some frame) :
    0 < frame.values.length := by
  have bounded := fieldsPayload (decodedFields h).1
  have len := decodedLength h
  omega

theorem decodedExactSize {raw : Bytes} {frame : Frame} (h : decode raw = some frame) :
    raw.length = 16 + frame.header.length + 2 * frame.values.length := by
  rw [← (decodedFields h).2, encodeLength, decodedLength h]

theorem decodedAt {raw : Bytes} {frame : Frame} (h : decode raw = some frame)
    (i : Nat) (inside : i < frame.values.length) :
    ∃ lo hi, frame.payload[2 * i]? = some lo ∧ frame.payload[2 * i + 1]? = some hi ∧
      frame.values[i]? = some (signed lo hi) ∧ word lo hi ≠ 32768 :=
  payloadAt (decodedPayload h) i inside

theorem payloadAppend {a b : Bytes} {xs ys : List Int}
    (ha : PayloadRelation a xs) (hb : PayloadRelation b ys) :
    PayloadRelation (a ++ b) (xs ++ ys) := by
  induction ha with
  | nil => exact hb
  | cons lo hi tail values valid rest ih => exact .cons lo hi _ _ valid ih

theorem oddPayloadRejected (raw : Bytes) (odd : raw.length % 2 = 1) :
    decodePayload raw = none := by
  cases e : decodePayload raw with
  | none => rfl
  | some values =>
    have len := payloadLength (payloadDecoded raw values e)
    omega

theorem invalidPairRejected (lo hi : UInt8) (tail : Bytes)
    (bad : word lo hi = 32768) : decodePayload (lo :: hi :: tail) = none := by
  simp [decodePayload, bad]

end DeltaReduce.NativeQBytes
