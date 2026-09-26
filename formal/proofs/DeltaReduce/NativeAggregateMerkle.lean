import DeltaReduce.NativeParameter
import DeltaReduce.NativeContractSize

/-! Original aggregate leaf JSON and odd-carry Merkle reduction. The strict
hex decoder is used only for generated IDs; it is not claimed equivalent to
native digest_bytes on arbitrary malformed input. -/
namespace DeltaReduce.NativeAggregateMerkle
open NativeReceiptBytes NativeVoteBytes
open NativeIscCertificate (object quoted)

structure Leaf where
  domain : Bytes
  qc : Bytes
  shard : Bytes
  deriving DecidableEq, Repr

def key (leaf : Leaf) : NativeParameter.Key := ⟨leaf.domain,leaf.shard⟩
def leafJSON (leaf : Leaf) : Bytes := object
  [("domain_id",quoted leaf.domain),("parameter_shard_qc_id",quoted leaf.qc),
   ("shard_id",quoted leaf.shard)]
def leafDomain : Bytes := ascii "deltareduce.008.aggregate-leaf.v1"
def nodeDomain : Bytes := ascii "deltareduce.008.aggregate-node.v1"

def nibble (b : UInt8) : Option Nat :=
  if 48 ≤ b.toNat ∧ b.toNat ≤ 57 then some (b.toNat-48)
  else if 97 ≤ b.toNat ∧ b.toNat ≤ 102 then some (b.toNat-87) else none

def decodePair (a b : UInt8) : Option UInt8 := do
  let x ← nibble a
  let y ← nibble b
  some (UInt8.ofNat (16*x+y))

set_option maxRecDepth 4096 in
set_option maxHeartbeats 2000000 in
theorem byteRoundTrip (b : UInt8) :
    decodePair (hexNibble (b.toNat / 16)) (hexNibble (b.toNat % 16)) = some b := by
  have all : ∀ n ∈ List.range 256,
      decodePair (hexNibble ((UInt8.ofNat n).toNat / 16))
        (hexNibble ((UInt8.ofNat n).toNat % 16)) = some (UInt8.ofNat n) := by decide
  have h := all b.toNat (List.mem_range.mpr b.toNat_lt)
  simpa only [UInt8.ofNat_toNat] using h

-- On generated lowercase hexadecimal ASCII this is the native unsigned-byte
-- nibble/shift/or expression. Non-ASCII C++ char signedness is outside this lemma.
def nativeNibble (b : UInt8) : UInt8 := if b ≤ 57 then b-48 else 10+b-97
def nativePair (a b : UInt8) : UInt8 := (nativeNibble a <<< 4) ||| nativeNibble b

set_option maxRecDepth 4096 in
set_option maxHeartbeats 2000000 in
theorem nativeByteRoundTrip (b : UInt8) :
    nativePair (hexNibble (b.toNat / 16)) (hexNibble (b.toNat % 16)) = b := by
  have all : ∀ n ∈ List.range 256,
      nativePair (hexNibble ((UInt8.ofNat n).toNat / 16))
        (hexNibble ((UInt8.ofNat n).toNat % 16)) = UInt8.ofNat n := by decide
  have h := all b.toNat (List.mem_range.mpr b.toNat_lt)
  simpa only [UInt8.ofNat_toNat] using h

theorem decoderMatchesNativeByte (b : UInt8) :
    decodePair (hexNibble (b.toNat / 16)) (hexNibble (b.toNat % 16)) =
    some (nativePair (hexNibble (b.toNat / 16)) (hexNibble (b.toNat % 16))) := by
  rw [byteRoundTrip,nativeByteRoundTrip]

def decodeHex : Bytes → Option Bytes
  | [] => some []
  | [_] => none
  | a::b::rest => do
    let byte ← decodePair a b
    let tail ← decodeHex rest
    some (byte::tail)

theorem hexRoundTrip (raw : Bytes) : decodeHex (hexBytes raw) = some raw := by
  induction raw with
  | nil => rfl
  | cons b bs ih =>
    simp only [hexBytes,List.flatMap_cons,List.cons_append,List.nil_append,decodeHex,
      byteRoundTrip,bind,Option.bind]
    change (decodeHex (hexBytes bs) >>= fun tail => some (b::tail)) = some (b::bs)
    rw [ih]; rfl

def digestBytes (id : Bytes) : Option Bytes :=
  if id.length = 71 ∧ id.take 7 = ascii "sha256:" then decodeHex (id.drop 7) else none

theorem digestRoundTrip (raw : Bytes) (size : raw.length = 32) :
    digestBytes (ascii "sha256:" ++ hexBytes raw) = some raw := by
  have prefixSize : (ascii "sha256:").length = 7 := by decide
  have len : (ascii "sha256:" ++ hexBytes raw).length = 71 := by
    rw [List.length_append,prefixSize,hexadecimalLength,size]
  have pre : (ascii "sha256:" ++ hexBytes raw).take 7 = ascii "sha256:" := by
    rw [← prefixSize,List.take_left]
  have drop : (ascii "sha256:" ++ hexBytes raw).drop 7 = hexBytes raw := by
    rw [← prefixSize,List.drop_left]
  have guard : (ascii "sha256:" ++ hexBytes raw).length = 71 ∧
      (ascii "sha256:" ++ hexBytes raw).take 7 = ascii "sha256:" := ⟨len,pre⟩
  rw [digestBytes,if_pos guard,drop,hexRoundTrip]

theorem generatedDigest {sha domain raw id}
    (h : NativeStateBytes.contentId sha domain raw = some id) :
    digestBytes id = some (sha (NativeStateBytes.contentPreimage domain raw)) ∧
    (sha (NativeStateBytes.contentPreimage domain raw)).length = 32 := by
  have src := NativeStateBytes.contentIdPreimage h
  rw [src.2]
  exact ⟨digestRoundTrip _ src.1,src.1⟩

def LeafValid (l : Leaf) : Prop :=
  NativeConfigAdmission.Label l.domain ∧ NativeConfigAdmission.Label l.shard ∧ ContentId l.qc
instance (l) : Decidable (LeafValid l) := by unfold LeafValid; infer_instance

def leafHash (sha : Bytes → Bytes) (leaf : Leaf) : Option Bytes :=
  if LeafValid leaf then NativeStateBytes.contentId sha leafDomain (leafJSON leaf) else none

def leafHashes (sha : Bytes → Bytes) : List Leaf → Option (List Bytes)
  | [] => some []
  | leaf::ls => do
    let id ← leafHash sha leaf
    let ids ← leafHashes sha ls
    some (id::ids)

theorem leafSource {sha leaf id} (h : leafHash sha leaf = some id) :
    LeafValid leaf ∧ NativeStateBytes.contentId sha leafDomain (leafJSON leaf) = some id := by
  unfold leafHash at h
  split at h <;> try contradiction
  exact ⟨by assumption,h⟩

theorem leafCount {sha ls ids} (h : leafHashes sha ls = some ids) : ids.length = ls.length := by
  induction ls generalizing ids with
  | nil => simp [leafHashes] at h; subst ids; rfl
  | cons l ls ih =>
    simp only [leafHashes,bind,Option.bind_eq_some_iff] at h
    obtain ⟨id,_,rest,hr,last⟩ := h
    cases Option.some.inj last
    simp only [List.length_cons,ih hr]

def parentHash (sha : Bytes → Bytes) (left right : Bytes) : Option Bytes := do
  let a ← digestBytes left
  let b ← digestBytes right
  NativeStateBytes.contentId sha nodeDomain (a ++ b)

theorem parentFromGenerated {sha ld lr li rd rr ri id}
    (left : NativeStateBytes.contentId sha ld lr = some li)
    (right : NativeStateBytes.contentId sha rd rr = some ri)
    (node : NativeStateBytes.contentId sha nodeDomain
      (sha (NativeStateBytes.contentPreimage ld lr) ++ sha (NativeStateBytes.contentPreimage rd rr)) = some id) :
    parentHash sha li ri = some id := by
  simp only [parentHash,(generatedDigest left).1,(generatedDigest right).1,bind,Option.bind,node]

def parentLevel (sha : Bytes → Bytes) : List Bytes → Option (List Bytes)
  | [] => some []
  | [x] => some [x]
  | x::y::rest => do
    let p ← parentHash sha x y
    let ps ← parentLevel sha rest
    some (p::ps)

theorem parentCount {sha level next} (h : parentLevel sha level = some next) :
    2 * next.length = level.length + level.length % 2 := by
  cases level with
  | nil => simp [parentLevel] at h; subst next; rfl
  | cons x xs =>
    cases xs with
    | nil => simp [parentLevel] at h; subst next; rfl
    | cons y rest =>
      simp only [parentLevel,bind,Option.bind_eq_some_iff] at h
      obtain ⟨p,_,ps,hp,last⟩ := h
      cases Option.some.inj last
      have small := parentCount hp
      simp only [List.length_cons]
      omega
termination_by level.length

theorem parentSmaller {sha x y rest next}
    (h : parentLevel sha (x::y::rest) = some next) : next.length < (x::y::rest).length := by
  have count := parentCount h
  simp only [List.length_cons] at *
  omega

def collapse (sha : Bytes → Bytes) (level : List Bytes) : Option Bytes :=
  match level with
  | [] => none
  | [x] => some x
  | x::y::rest =>
    match _h : parentLevel sha (x::y::rest) with
    | none => none
    | some next => collapse sha next
termination_by level.length
decreasing_by exact parentSmaller _h

theorem collapseStep {sha x y rest next} (h : parentLevel sha (x::y::rest) = some next) :
    collapse sha (x::y::rest) = collapse sha next := by rw [collapse,h]

theorem carrySingle (sha x) : parentLevel sha [x] = some [x] := rfl
theorem noExtraSingletonHash (sha x) : collapse sha [x] = some x := by rw [collapse]
theorem emptyLevelRejected (sha) : collapse sha [] = none := by rw [collapse]

def root (sha : Bytes → Bytes) (leaves : List Leaf) : Option Bytes := do
  if 0 < leaves.length ∧ leaves.length ≤ 100000 then
    let hashes ← leafHashes sha leaves
    collapse sha hashes
  else none

theorem rootSource {sha leaves id} (h : root sha leaves = some id) :
    0 < leaves.length ∧ leaves.length ≤ 100000 ∧
    ∃ hashes, leafHashes sha leaves = some hashes ∧ hashes.length = leaves.length ∧ collapse sha hashes = some id := by
  unfold root at h
  split at h <;> try contradiction
  rename_i bound
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨hashes,hh,hr⟩ := h
  exact ⟨bound.1,bound.2,hashes,hh,leafCount hh,hr⟩

theorem fromComponents {sha leaves hashes id}
    (bound : 0 < leaves.length ∧ leaves.length ≤ 100000)
    (hashed : leafHashes sha leaves = some hashes) (reduced : collapse sha hashes = some id) :
    root sha leaves = some id := by simp only [root,if_pos bound,hashed,bind,Option.bind,reduced]

theorem invalidCount {sha leaves} (bound : ¬ (0 < leaves.length ∧ leaves.length ≤ 100000)) :
    root sha leaves = none := by simp only [root,if_neg bound]

end DeltaReduce.NativeAggregateMerkle
