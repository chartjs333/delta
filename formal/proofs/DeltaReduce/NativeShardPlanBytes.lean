import DeltaReduce.NativeJsonSequence

/-! Original004 canonical shard-plan bytes, without hash/authority claims. -/
namespace DeltaReduce.NativeShardPlanBytes
open NativeReceiptBytes (Bytes consume consumeAppend)
open NativeVoteBytes (ascii)
open NativeQJson (ValueValid)
open NativeScaleBytes (memberBytes readMember memberEncoded)

structure EntryWire where
  count : Bytes
  start : Bytes
  ordinal : Bytes
  payload : Bytes
  name : Bytes
  offset : Bytes
  deriving DecidableEq, Repr

def entryBytes (w : EntryWire) : Bytes :=
  [123] ++
    memberBytes "element_count" .natural w.count 44 ++
    memberBytes "element_start" .natural w.start 44 ++
    memberBytes "ordinal" .natural w.ordinal 44 ++
    memberBytes "payload_bytes" .natural w.payload 44 ++
    memberBytes "segment_id" .text w.name 44 ++
    memberBytes "segment_offset" .natural w.offset 125

def readEntry (raw : Bytes) : Option (EntryWire × Bytes) := do
  let raw ← consume [123] raw
  let (count,raw) ← readMember "element_count" .natural 44 raw
  let (start,raw) ← readMember "element_start" .natural 44 raw
  let (ordinal,raw) ← readMember "ordinal" .natural 44 raw
  let (payload,raw) ← readMember "payload_bytes" .natural 44 raw
  let (name,raw) ← readMember "segment_id" .text 44 raw
  let (offset,raw) ← readMember "segment_offset" .natural 125 raw
  some (⟨count,start,ordinal,payload,name,offset⟩,raw)

def EntrySyntax (w : EntryWire) : Prop :=
  ValueValid .natural w.count ∧
  ValueValid .natural w.start ∧
  ValueValid .natural w.ordinal ∧
  ValueValid .natural w.payload ∧
  ValueValid .text w.name ∧
  ValueValid .natural w.offset
instance (w) : Decidable (EntrySyntax w) := by unfold EntrySyntax; infer_instance

theorem entryEncoded (w : EntryWire) (tail : Bytes) (h : EntrySyntax w) :
    readEntry (entryBytes w ++ tail) = some (w,tail) := by
  rcases h with ⟨h0,h1,h2,h3,h4,h5⟩
  simp only [readEntry,entryBytes,List.append_assoc,consumeAppend,bind,Option.bind]
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h0]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h1]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h2]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h3]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h4]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inr rfl) h5]

def entriesBytes := NativeJsonSequence.encode 93 entryBytes
def readEntries := NativeJsonSequence.read 93 readEntry 4096

theorem entriesEncoded (es : List EntryWire) (tail : Bytes)
    (size : es.length ≤ 4096) (valid : ∀ e ∈ es, EntrySyntax e) :
    readEntries (entriesBytes es ++ tail) = some (es,tail) := by
  apply NativeJsonSequence.encoded 93 (by decide) entryBytes _ EntrySyntax es 4096 tail size valid
  · intro e _; exact ⟨123,_,rfl,by decide⟩
  · intro e he sep rest _; exact entryEncoded e (sep::rest) he

structure Wire where
  entries : List EntryWire
  semantics : Bytes
  schema : Bytes
  profile : Bytes
  scale : Bytes
  version : Bytes
  target : Bytes
  total : Bytes
  kind : Bytes
  deriving DecidableEq, Repr

def encode (w : Wire) : Bytes :=
  ascii "{\"entries\":[" ++ entriesBytes w.entries ++ [44] ++
    memberBytes "formal_semantics_id" .text w.semantics 44 ++
    memberBytes "parameter_schema_id" .text w.schema 44 ++
    memberBytes "profile_id" .text w.profile 44 ++
    memberBytes "scale_table_id" .text w.scale 44 ++
    memberBytes "schema_version" .text w.version 44 ++
    memberBytes "target_payload_bytes" .natural w.target 44 ++
    memberBytes "total_elements" .natural w.total 44 ++
    memberBytes "type_name" .text w.kind 125

def parse (raw : Bytes) : Option (Wire × Bytes) := do
  let raw ← consume (ascii "{\"entries\":[") raw
  let (entries,raw) ← readEntries raw
  let raw ← consume [44] raw
  let (semantics,raw) ← readMember "formal_semantics_id" .text 44 raw
  let (schema,raw) ← readMember "parameter_schema_id" .text 44 raw
  let (profile,raw) ← readMember "profile_id" .text 44 raw
  let (scale,raw) ← readMember "scale_table_id" .text 44 raw
  let (version,raw) ← readMember "schema_version" .text 44 raw
  let (target,raw) ← readMember "target_payload_bytes" .natural 44 raw
  let (total,raw) ← readMember "total_elements" .natural 44 raw
  let (kind,raw) ← readMember "type_name" .text 125 raw
  some (⟨entries,semantics,schema,profile,scale,version,target,total,kind⟩,raw)

def Syntax (w : Wire) : Prop :=
  w.entries.length ≤ 4096 ∧
  (∀ e ∈ w.entries, EntrySyntax e) ∧
  ValueValid .text w.semantics ∧
  ValueValid .text w.schema ∧
  ValueValid .text w.profile ∧
  ValueValid .text w.scale ∧
  ValueValid .text w.version ∧
  ValueValid .natural w.target ∧
  ValueValid .natural w.total ∧
  ValueValid .text w.kind
instance (w) : Decidable (Syntax w) := by unfold Syntax; infer_instance

theorem parsedEncoded (w : Wire) (tail : Bytes) (h : Syntax w) :
    parse (encode w ++ tail) = some (w,tail) := by
  rcases h with ⟨h0,h1,h2,h3,h4,h5,h6,h7,h8,h9⟩
  simp only [parse,encode,List.append_assoc,consumeAppend,bind,Option.bind]
  rw [entriesEncoded w.entries _ h0 h1]
  simp only [consumeAppend]
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h2]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h3]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h4]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h5]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h6]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h7]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h8]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inr rfl) h9]

def decode (raw : Bytes) : Option Wire := do
  if raw.length ≤ 4194304 then
    let (w,tail) ← parse raw
    if tail = [] ∧ Syntax w ∧ encode w = raw then some w else none
  else none

theorem decoded {raw w} (h : decode raw = some w) :
    parse raw = some (w,[]) ∧ raw.length ≤ 4194304 ∧ Syntax w ∧ encode w = raw := by
  unfold decode at h
  split at h <;> try contradiction
  rename_i small
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨v,tail⟩,parsed,last⟩ := h
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  rcases checks with ⟨rfl,syn,eq⟩
  exact ⟨parsed,small,syn,eq⟩

theorem decodeEncoded (w : Wire) (syntaxOk : Syntax w)
    (small : (encode w).length ≤ 4194304) : decode (encode w) = some w := by
  unfold decode
  rw [if_pos small,← List.append_nil (encode w),parsedEncoded w [] syntaxOk]
  simp [syntaxOk]

theorem encodingUnique {a b : Wire} (ha : Syntax a) (hb : Syntax b)
    (same : encode a = encode b) : a = b := by
  have pa := parsedEncoded a [] ha
  have pb := parsedEncoded b [] hb
  rw [same] at pa
  exact (Prod.mk.inj (Option.some.inj (pa.symm.trans pb))).1

end DeltaReduce.NativeShardPlanBytes
