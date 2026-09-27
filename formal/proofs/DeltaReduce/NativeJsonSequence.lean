import DeltaReduce.NativeScaleBytes

/-! Bounded comma-separated fixed-grammar sequences. Not general JSON. -/
namespace DeltaReduce.NativeJsonSequence
open NativeReceiptBytes (Bytes consume consumeAppend)
open NativeVoteBytes (ascii digit DecimalValid)

def encode (close : UInt8) (item : α → Bytes) : List α → Bytes
  | [] => [close]
  | [x] => item x ++ [close]
  | x::y::xs => item x ++ [44] ++ encode close item (y::xs)

def read (close : UInt8) (item : Bytes → Option (α × Bytes)) :
    Nat → Bytes → Option (List α × Bytes)
  | 0, raw => do
      let tail ← consume [close] raw
      some ([],tail)
  | n+1, raw =>
      if raw.head? = some close then some ([],raw.drop 1) else do
        let (x,raw) ← item raw
        match raw with
        | b::tail =>
            if b = close then some ([x],tail)
            else if b = 44 then do
              let (xs,tail) ← read close item n tail
              if xs ≠ [] then some (x::xs,tail) else none
            else none
        | [] => none

theorem encoded (close : UInt8) (notComma : close ≠ 44)
    (item : α → Bytes) (reader : Bytes → Option (α × Bytes))
    (valid : α → Prop) (xs : List α) (bound : Nat) (tail : Bytes)
    (size : xs.length ≤ bound) (values : ∀ x ∈ xs, valid x)
    (starts : ∀ x, valid x → ∃ b rest, item x = b::rest ∧ b ≠ close)
    (roundtrip : ∀ x, valid x → ∀ sep rest, sep = close ∨ sep = 44 →
      reader (item x ++ sep::rest) = some (x,sep::rest)) :
    read close reader bound (encode close item xs ++ tail) = some (xs,tail) := by
  induction xs generalizing bound with
  | nil => cases bound <;> simp [encode,read,consume]
  | cons x xs ih =>
    cases bound with
    | zero => simp at size
    | succ n =>
      have head := values x (by simp)
      have restValid : ∀ y ∈ xs, valid y := by intro y hy; exact values y (by simp [hy])
      have restSize : xs.length ≤ n := by simpa using size
      obtain ⟨b,rest,hb,hclose⟩ := starts x head
      cases xs with
      | nil =>
        have parsed := roundtrip x head close tail (Or.inl rfl)
        rw [hb,List.cons_append] at parsed
        simp [encode,List.append_assoc,hb,read,hclose,parsed]
      | cons y ys =>
        have parsed := roundtrip x head 44 (encode close item (y::ys) ++ tail) (Or.inr rfl)
        rw [hb,List.cons_append] at parsed
        simp [encode,List.append_assoc,hb,read,hclose,parsed,Ne.symm notComma,
          ih n restSize restValid]

theorem countBound {close : UInt8} {reader : Bytes → Option (α × Bytes)}
    {bound raw xs tail} (h : read close reader bound raw = some (xs,tail)) :
    xs.length ≤ bound := by
  induction bound generalizing raw xs tail with
  | zero =>
    unfold read at h
    simp only [bind,Option.bind_eq_some_iff] at h
    obtain ⟨rest,_,same⟩ := h
    cases Option.some.inj same; simp
  | succ n ih =>
    unfold read at h
    split at h
    · cases Option.some.inj h; simp
    · simp only [bind,Option.bind_eq_some_iff] at h
      obtain ⟨⟨x,rest⟩,_,last⟩ := h
      split at last
      · split at last
        · cases Option.some.inj last; simp
        · split at last
          · simp only [Option.bind_eq_some_iff] at last
            obtain ⟨⟨ys,t⟩,hy,last⟩ := last
            split at last <;> try contradiction
            cases Option.some.inj last
            have small := ih hy
            simpa using Nat.succ_le_succ small
          · contradiction
      · contradiction

def textBytes (s : Bytes) : Bytes := [34] ++ s ++ [34]

def readText (raw : Bytes) : Option (Bytes × Bytes) := do
  let raw ← consume [34] raw
  let (s,rest) ← NativeQJson.scanTo 34 raw
  if NativeQJson.TextValid s then some (s,rest) else none

theorem textEncoded (s tail : Bytes) (h : NativeQJson.TextValid s) :
    readText (textBytes s ++ tail) = some (s,tail) := by
  have safe : ∀ b ∈ s, b ≠ 34 := by intro b hb; exact (h.2 b hb).2.2.1
  simp only [readText,textBytes,List.append_assoc,consumeAppend,bind,Option.bind]
  rw [show [34] ++ tail = 34::tail from rfl,NativeQJson.scanToEncoded 34 s tail safe]
  exact if_pos h

def digits : Bytes → Bytes × Bytes
  | [] => ([],[])
  | b::rest => if digit b then
      let result := digits rest
      (b::result.1,result.2)
    else ([],b::rest)

theorem digitsEncoded (s : Bytes) (sep : UInt8) (tail : Bytes)
    (all : ∀ b ∈ s, digit b) (stop : ¬ digit sep) :
    digits (s ++ sep::tail) = (s,sep::tail) := by
  induction s with
  | nil => simp [digits,stop]
  | cons b rest ih =>
    have head := all b (by simp)
    have hv : ∀ x ∈ rest, digit x := by intro x hx; exact all x (by simp [hx])
    simp [digits,head,ih hv]

def readNatural (raw : Bytes) : Option (Bytes × Bytes) :=
  let result := digits raw
  if DecimalValid result.1 then some result else none

theorem naturalEncoded (s tail : Bytes) (sep : UInt8)
    (valid : DecimalValid s) (stop : ¬ digit sep) :
    readNatural (s ++ sep::tail) = some (s,sep::tail) := by
  simp [readNatural,digitsEncoded s sep tail valid.2.2.1 stop,valid]

end DeltaReduce.NativeJsonSequence
