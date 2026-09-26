import DeltaReduce.NativeReceiptBytes

/-! Complete DVPOL001 structural grammar interpreter. Schema fields are named,
but names are not wire bytes. Signed rationals retain their uint64 bit pattern.
This layer does not validate startup authority, certificate graphs or votes. -/
namespace DeltaReduce.NativePolicyCodec
open NativeReceiptBytes

inductive Format where
  | uint (width : Nat)
  | text
  | boolean
  | field (name : String) (head tail : Format)
  | vector (bound : Nat) (item : Format)
  | end
  deriving DecidableEq, Repr

inductive Value where
  | number (n : Nat)
  | text (raw : Bytes)
  | pair (head tail : Value)
  | items (values : List Value)
  | end
  deriving Repr

def writeMany (write : Value → Option Bytes) : List Value → Option Bytes
  | [] => some []
  | v::vs => do
    let a ← write v
    let b ← writeMany write vs
    some (a ++ b)

def readMany (read : Bytes → Option (Value × Bytes)) : Nat → Bytes → Option (List Value × Bytes)
  | 0, raw => some ([], raw)
  | n+1, raw => do
    let (v, rest) ← read raw
    let (vs, rest) ← readMany read n rest
    some (v::vs, rest)

def encode : Format → Value → Option Bytes
  | .uint n, .number v => if v < 256^n then some (be n v) else none
  | .boolean, .number v => if v ≤ 1 then some (be 1 v) else none
  | .text, .text b => if b.length ≤ 4096 ∧ printable b then some (sizedBytes b) else none
  | .end, .end => some []
  | .field _ a b, .pair x y => do
    let left ← encode a x
    let right ← encode b y
    some (left ++ right)
  | .vector bound item, .items vs => do
    if vs.length ≤ bound ∧ vs.length < 256^4 then
      let body ← writeMany (encode item) vs
      some (be 4 vs.length ++ body)
    else none
  | _, _ => none

def parse : Format → Bytes → Option (Value × Bytes)
  | .uint n, raw => do
    let (v, rest) ← readNat n raw
    some (.number v, rest)
  | .boolean, raw => do
    let (v, rest) ← readNat 1 raw
    if v ≤ 1 then some (.number v, rest) else none
  | .text, raw => do
    let (b, rest) ← readSection 4096 raw
    if printable b then some (.text b, rest) else none
  | .end, raw => some (.end, raw)
  | .field _ a b, raw => do
    let (x, rest) ← parse a raw
    let (y, rest) ← parse b rest
    some (.pair x y, rest)
  | .vector bound item, raw => do
    let (n, rest) ← readNat 4 raw
    if n ≤ bound then
      let (vs, rest) ← readMany (parse item) n rest
      some (.items vs, rest)
    else none

theorem manyRoundTrip (write : Value → Option Bytes)
    (read : Bytes → Option (Value × Bytes))
    (inverse : ∀ v bytes tail, write v = some bytes → read (bytes ++ tail) = some (v,tail))
    (vs : List Value) (bytes tail : Bytes) (ok : writeMany write vs = some bytes) :
    readMany read vs.length (bytes ++ tail) = some (vs,tail) := by
  induction vs generalizing bytes with
  | nil => simp [writeMany] at ok; subst bytes; rfl
  | cons v vs ih =>
    simp only [writeMany] at ok
    cases a : write v with
    | none => simp [a] at ok
    | some x =>
      cases b : writeMany write vs with
      | none => simp [a,b] at ok
      | some y =>
        simp only [a,b,bind,Option.bind,Option.some.injEq] at ok
        subst bytes
        simp only [List.length_cons, readMany, List.append_assoc,
          inverse v x (y ++ tail) a, bind, Option.bind]
        rw [ih y b]

theorem roundTrip (fmt : Format) (v : Value) (bytes tail : Bytes)
    (ok : encode fmt v = some bytes) : parse fmt (bytes ++ tail) = some (v,tail) := by
  induction fmt generalizing v bytes tail with
  | uint n =>
    cases v <;> simp [encode] at ok
    rename_i value
    obtain ⟨bound,rfl⟩ := ok
    simp [parse, readNatEncoded n value tail bound]
  | boolean =>
    cases v <;> simp [encode] at ok
    rename_i value
    obtain ⟨bound,rfl⟩ := ok
    have small : value < 256^1 := by omega
    simp [parse, readNatEncoded 1 value tail small, bound]
  | text =>
    cases v <;> simp [encode] at ok
    rename_i raw
    obtain ⟨bound,rfl⟩ := ok
    have small : raw.length < 256^4 := by omega
    simp [parse, readSectionEncoded raw tail 4096 small bound.1, bound.2]
  | «end» => cases v <;> simp_all [encode, parse]
  | field name a b iha ihb =>
    cases v <;> simp [encode] at ok
    rename_i x y
    cases h : encode a x with
    | none => simp [h] at ok
    | some left =>
      cases j : encode b y with
      | none => simp [h,j] at ok
      | some right =>
        simp only [h,j,Option.bind,Option.some.injEq] at ok
        subst bytes
        simp only [parse, List.append_assoc, iha x left (right ++ tail) h, bind,Option.bind]
        rw [ihb y right tail j]
  | vector bound item ih =>
    cases v <;> simp [encode] at ok
    rename_i vs
    obtain ⟨bounds,ok⟩ := ok
    cases h : writeMany (encode item) vs with
    | none => simp [h] at ok
    | some body =>
      simp only [h,Option.bind,Option.some.injEq] at ok
      subst bytes
      simp only [parse,List.append_assoc,readNatEncoded 4 vs.length (body ++ tail) bounds.2,
        bind,Option.bind,if_pos bounds.1]
      rw [manyRoundTrip (encode item) (parse item) ih vs body tail h]

def decode (fmt : Format) (raw : Bytes) : Option Value := do
  let (v, rest) ← parse fmt raw
  if rest = [] ∧ encode fmt v = some raw then some v else none

theorem decoded {fmt raw v} (ok : decode fmt raw = some v) :
    parse fmt raw = some (v,[]) ∧ encode fmt v = some raw := by
  unfold decode at ok
  cases h : parse fmt raw with
  | none => simp [h] at ok
  | some result =>
    rcases result with ⟨value,rest⟩
    simp only [h,bind,Option.bind] at ok
    split at ok
    · rename_i checks
      cases Option.some.inj ok
      exact ⟨by simp [checks.1], checks.2⟩
    · contradiction

theorem encoded {fmt v bytes} (ok : encode fmt v = some bytes) :
    decode fmt bytes = some v := by
  have h := roundTrip fmt v bytes [] ok
  simp only [List.append_nil] at h
  simp [decode,h,ok]

theorem encodingInjective {fmt a b raw}
    (ha : encode fmt a = some raw) (hb : encode fmt b = some raw) : a = b := by
  have h := encoded ha
  rw [encoded hb] at h
  exact (Option.some.inj h).symm

def lookup : Format → Value → String → Option Value
  | .field name _ b, .pair x y, key =>
    if key = name then some x else lookup b y key
  | _, _, _ => none

def signed64 (n : Nat) : Int := if n < 2^63 then n else (n : Int) - 2^64

theorem fieldHead (name : String) (a b : Format) (x y : Value) :
    lookup (.field name a b) (.pair x y) name = some x := by simp [lookup]

theorem fieldTail {key name : String} (a b : Format) (x y : Value) (h : key ≠ name) :
    lookup (.field name a b) (.pair x y) key = lookup b y key := by simp [lookup,h]

theorem numberBound {width n raw} (h : encode (.uint width) (.number n) = some raw) :
    n < 256^width := by simp only [encode] at h; split at h <;> simp_all

theorem textBound {b raw} (h : encode .text (.text b) = some raw) :
    b.length ≤ 4096 ∧ printable b := by simp only [encode] at h; split at h <;> simp_all

theorem vectorBound {bound fmt vs raw}
    (h : encode (.vector bound fmt) (.items vs) = some raw) :
    vs.length ≤ bound ∧ vs.length < 256^4 := by
  simp only [encode] at h; split at h <;> simp_all

end DeltaReduce.NativePolicyCodec
