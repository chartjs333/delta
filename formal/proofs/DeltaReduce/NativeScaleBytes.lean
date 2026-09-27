import DeltaReduce.NativeQHeader

/-! Original004 scale-table JSON bytes. Fixed nested grammar, not general JSON,
SHA, source-schema equality or producer authentication. -/
namespace DeltaReduce.NativeScaleBytes
open NativeReceiptBytes (Bytes consume consumeAppend)
open NativeVoteBytes (ascii)
open NativeQJson (Kind ValueValid)

def memberBytes (key : String) (kind : Kind) (value : Bytes) (sep : UInt8) : Bytes :=
  NativeQJson.keyPrefix (ascii key) ++ NativeQJson.encodeValue kind value ++ [sep]

def readMember (key : String) (kind : Kind) (sep : UInt8) (raw : Bytes) := do
  let tail ← consume (NativeQJson.keyPrefix (ascii key)) raw
  NativeQJson.readValue kind sep tail

theorem memberEncoded (key : String) (kind : Kind) (value tail : Bytes) (sep : UInt8)
    (separator : sep = 44 ∨ sep = 125) (valid : ValueValid kind value) :
    readMember key kind sep (memberBytes key kind value sep ++ tail) = some (value,tail) := by
  simp only [readMember,memberBytes,List.append_assoc,consumeAppend,bind,Option.bind]
  exact NativeQJson.readValueEncoded kind value tail sep separator valid

structure SegmentWire where
  count : Bytes
  start : Bytes
  denominator : Bytes
  numerator : Bytes
  name : Bytes
  ordinal : Bytes
  deriving DecidableEq, Repr

def segmentBytes (s : SegmentWire) : Bytes :=
  [123] ++ memberBytes "element_count" .natural s.count 44 ++
    memberBytes "element_start" .natural s.start 44 ++ ascii "\"quantum\":{" ++
    memberBytes "denominator" .natural s.denominator 44 ++
    memberBytes "numerator" .text s.numerator 125 ++ [44] ++
    memberBytes "segment_id" .text s.name 44 ++
    memberBytes "segment_ordinal" .natural s.ordinal 125

def readSegment (raw : Bytes) : Option (SegmentWire × Bytes) := do
  let raw ← consume [123] raw
  let (count,raw) ← readMember "element_count" .natural 44 raw
  let (start,raw) ← readMember "element_start" .natural 44 raw
  let raw ← consume (ascii "\"quantum\":{") raw
  let (denominator,raw) ← readMember "denominator" .natural 44 raw
  let (numerator,raw) ← readMember "numerator" .text 125 raw
  let raw ← consume [44] raw
  let (name,raw) ← readMember "segment_id" .text 44 raw
  let (ordinal,raw) ← readMember "segment_ordinal" .natural 125 raw
  some (⟨count,start,denominator,numerator,name,ordinal⟩,raw)

def SegmentSyntax (s : SegmentWire) : Prop :=
  ValueValid .natural s.count ∧ ValueValid .natural s.start ∧
  ValueValid .natural s.denominator ∧ ValueValid .text s.numerator ∧
  ValueValid .text s.name ∧ ValueValid .natural s.ordinal
instance (s) : Decidable (SegmentSyntax s) := by unfold SegmentSyntax; infer_instance

theorem segmentEncoded (s : SegmentWire) (tail : Bytes) (valid : SegmentSyntax s) :
    readSegment (segmentBytes s ++ tail) = some (s,tail) := by
  rcases valid with ⟨c,a,d,n,k,o⟩
  simp only [readSegment,segmentBytes,List.append_assoc,consumeAppend,bind,Option.bind]
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) c]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) a]
  simp only [consumeAppend]
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) d]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inr rfl) n]
  simp only [consumeAppend]
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) k]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inr rfl) o]

def segmentListBytes : List SegmentWire → Bytes
  | [] => [93]
  | [s] => segmentBytes s ++ [93]
  | s :: next :: rest => segmentBytes s ++ [44] ++ segmentListBytes (next :: rest)

def readSegments : Nat → Bytes → Option (List SegmentWire × Bytes)
  | 0, raw => do
      let rest ← consume [93] raw
      some ([],rest)
  | n+1, raw =>
      match raw with
      | 93 :: rest => some ([],rest)
      | _ => do
          let (s,rest) ← readSegment raw
          match rest with
          | 93 :: tail => some ([s],tail)
          | 44 :: tail => do
              let (ss,tail) ← readSegments n tail
              if ss ≠ [] then some (s::ss,tail) else none
          | _ => none

theorem segmentStarts (s : SegmentWire) : ∃ rest, segmentBytes s = 123 :: rest := by
  exact ⟨_,rfl⟩

theorem segmentsEncoded (ss : List SegmentWire) (bound : Nat) (tail : Bytes)
    (size : ss.length ≤ bound) (valid : ∀ s ∈ ss, SegmentSyntax s) :
    readSegments bound (segmentListBytes ss ++ tail) = some (ss,tail) := by
  induction ss generalizing bound with
  | nil => cases bound <;> simp [segmentListBytes,readSegments,consume]
  | cons s ss ih =>
      cases bound with
      | zero => simp at size
      | succ n =>
        have hs := valid s (by simp)
        have hv : ∀ x ∈ ss, SegmentSyntax x := by intro x hx; exact valid x (by simp [hx])
        have hn : ss.length ≤ n := by simpa using size
        obtain ⟨prefixBytes,hp⟩ := segmentStarts s
        cases ss with
        | nil =>
          have decoded := segmentEncoded s ([93] ++ tail) hs
          rw [hp,List.cons_append] at decoded
          simp only [List.cons_append,List.nil_append] at decoded
          simp [segmentListBytes,List.append_assoc,hp,readSegments,decoded]
        | cons x xs =>
          have decoded := segmentEncoded s ([44] ++ (segmentListBytes (x::xs) ++ tail)) hs
          rw [hp,List.cons_append] at decoded
          simp only [List.cons_append,List.nil_append] at decoded
          simp [segmentListBytes,List.append_assoc,hp,readSegments,decoded,ih n hn hv]

theorem segmentsCount {bound raw ss rest} (ok : readSegments bound raw = some (ss,rest)) :
    ss.length ≤ bound := by
  induction bound generalizing raw ss rest with
  | zero =>
    unfold readSegments at ok
    simp only [bind,Option.bind_eq_some_iff] at ok
    obtain ⟨tail,_,same⟩ := ok
    cases Option.some.inj same; simp
  | succ n ih =>
    unfold readSegments at ok
    split at ok
    · cases Option.some.inj ok; simp
    · simp only [bind,Option.bind_eq_some_iff] at ok
      obtain ⟨⟨s,left⟩,_,last⟩ := ok
      split at last
      · cases Option.some.inj last; simp
      · simp only [Option.bind_eq_some_iff] at last
        obtain ⟨⟨xs,tail⟩,hx,last⟩ := last
        split at last <;> try contradiction
        cases Option.some.inj last
        have h := ih hx
        simpa using Nat.succ_le_succ h
      · contradiction

structure Wire where
  semantics : Bytes
  schema : Bytes
  profile : Bytes
  version : Bytes
  segments : List SegmentWire
  total : Bytes
  kind : Bytes
  deriving DecidableEq, Repr

def encode (w : Wire) : Bytes :=
  [123] ++ memberBytes "formal_semantics_id" .text w.semantics 44 ++
    memberBytes "parameter_schema_id" .text w.schema 44 ++
    memberBytes "profile_id" .text w.profile 44 ++
    memberBytes "schema_version" .text w.version 44 ++ ascii "\"segments\":[" ++
    segmentListBytes w.segments ++ [44] ++ memberBytes "total_elements" .natural w.total 44 ++
    memberBytes "type_name" .text w.kind 125

def parse (raw : Bytes) : Option (Wire × Bytes) := do
  let raw ← consume [123] raw
  let (semantics,raw) ← readMember "formal_semantics_id" .text 44 raw
  let (schema,raw) ← readMember "parameter_schema_id" .text 44 raw
  let (profile,raw) ← readMember "profile_id" .text 44 raw
  let (version,raw) ← readMember "schema_version" .text 44 raw
  let raw ← consume (ascii "\"segments\":[") raw
  let (segments,raw) ← readSegments 65536 raw
  let raw ← consume [44] raw
  let (total,raw) ← readMember "total_elements" .natural 44 raw
  let (kind,raw) ← readMember "type_name" .text 125 raw
  some (⟨semantics,schema,profile,version,segments,total,kind⟩,raw)

def Syntax (w : Wire) : Prop :=
  ValueValid .text w.semantics ∧ ValueValid .text w.schema ∧
  ValueValid .text w.profile ∧ ValueValid .text w.version ∧
  (∀ s ∈ w.segments, SegmentSyntax s) ∧ w.segments.length ≤ 65536 ∧
  ValueValid .natural w.total ∧ ValueValid .text w.kind
instance (w) : Decidable (Syntax w) := by unfold Syntax; infer_instance

theorem parsedEncoded (w : Wire) (tail : Bytes) (valid : Syntax w) :
    parse (encode w ++ tail) = some (w,tail) := by
  rcases valid with ⟨a,b,c,d,e,f,g,h⟩
  simp only [parse,encode,List.append_assoc,consumeAppend,bind,Option.bind]
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) a]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) b]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) c]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) d]
  simp only [consumeAppend]
  rw [segmentsEncoded w.segments 65536 _ f e]
  simp only [consumeAppend]
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) g]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inr rfl) h]

def decode (raw : Bytes) : Option Wire := do
  if raw.length ≤ 4194304 then do
    let (w,rest) ← parse raw
    if rest = [] ∧ Syntax w ∧ encode w = raw then some w else none
  else none

theorem decoded {raw w} (ok : decode raw = some w) :
    raw.length ≤ 4194304 ∧ parse raw = some (w,[]) ∧ Syntax w ∧ encode w = raw := by
  unfold decode at ok
  split at ok <;> try contradiction
  rename_i bounded
  simp only [bind,Option.bind_eq_some_iff] at ok
  obtain ⟨⟨value,rest⟩,parsed,last⟩ := ok
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  rcases checks with ⟨rfl,syn,eq⟩
  exact ⟨bounded,parsed,syn,eq⟩

theorem decodeEncoded (w : Wire) (valid : Syntax w) (bound : (encode w).length ≤ 4194304) :
    decode (encode w) = some w := by
  have parsed := parsedEncoded w [] valid
  simp only [List.append_nil] at parsed
  simp [decode,bound,parsed,valid]

theorem encodingUnique {a b} (va : Syntax a) (vb : Syntax b)
    (same : encode a = encode b) : a = b := by
  have first := parsedEncoded a [] va
  rw [same,parsedEncoded b [] vb] at first
  exact (Prod.mk.inj (Option.some.inj first)).1.symm

end DeltaReduce.NativeScaleBytes
