import DeltaReduce.NativeShardPlanBytes
namespace DeltaReduce.NativeManifestBytes
open NativeReceiptBytes (Bytes consume consumeAppend)
open NativeVoteBytes (ascii)
open NativeQJson (ValueValid)
open NativeScaleBytes (memberBytes readMember memberEncoded)

structure RefWire where
  count : Bytes
  start : Bytes
  envelope : Bytes
  leaf : Bytes
  ordinal : Bytes
  payload : Bytes
  name : Bytes
  offset : Bytes
  deriving DecidableEq, Repr

def refBytes (w : RefWire) : Bytes :=
  [123] ++
    memberBytes "element_count" .natural w.count 44 ++
    memberBytes "element_start" .natural w.start 44 ++
    memberBytes "envelope_bytes" .natural w.envelope 44 ++
    memberBytes "leaf_id" .text w.leaf 44 ++
    memberBytes "ordinal" .natural w.ordinal 44 ++
    memberBytes "payload_bytes" .natural w.payload 44 ++
    memberBytes "segment_id" .text w.name 44 ++
    memberBytes "segment_offset" .natural w.offset 125

def readRef (raw : Bytes) : Option (RefWire × Bytes) := do
  let raw ← consume [123] raw
  let (count,raw) ← readMember "element_count" .natural 44 raw
  let (start,raw) ← readMember "element_start" .natural 44 raw
  let (envelope,raw) ← readMember "envelope_bytes" .natural 44 raw
  let (leaf,raw) ← readMember "leaf_id" .text 44 raw
  let (ordinal,raw) ← readMember "ordinal" .natural 44 raw
  let (payload,raw) ← readMember "payload_bytes" .natural 44 raw
  let (name,raw) ← readMember "segment_id" .text 44 raw
  let (offset,raw) ← readMember "segment_offset" .natural 125 raw
  some (⟨count,start,envelope,leaf,ordinal,payload,name,offset⟩,raw)

def RefSyntax (w : RefWire) : Prop :=
  ValueValid .natural w.count ∧
  ValueValid .natural w.start ∧
  ValueValid .natural w.envelope ∧
  ValueValid .text w.leaf ∧
  ValueValid .natural w.ordinal ∧
  ValueValid .natural w.payload ∧
  ValueValid .text w.name ∧
  ValueValid .natural w.offset
instance (w) : Decidable (RefSyntax w) := by unfold RefSyntax; infer_instance

theorem refEncoded (w : RefWire) (tail : Bytes) (h : RefSyntax w) :
    readRef (refBytes w ++ tail) = some (w,tail) := by
  rcases h with ⟨h0,h1,h2,h3,h4,h5,h6,h7⟩
  simp only [readRef,refBytes,List.append_assoc,consumeAppend,bind,Option.bind]
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
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h5]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h6]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inr rfl) h7]

def refsBytes := NativeJsonSequence.encode 93 refBytes
def readRefs := NativeJsonSequence.read 93 readRef 4096
theorem refsEncoded (es : List RefWire) (tail : Bytes)
    (size : es.length ≤ 4096) (valid : ∀ e ∈ es, RefSyntax e) :
    readRefs (refsBytes es ++ tail) = some (es,tail) := by
  apply NativeJsonSequence.encoded 93 (by decide) refBytes _ RefSyntax es 4096 tail size valid
  · intro e _; exact ⟨123,_,rfl,by decide⟩
  · intro e he sep rest _; exact refEncoded e (sep::rest) he

structure Wire where
  steps : Bytes
  root : Bytes
  domain : Bytes
  semantics : Bytes
  schema : Bytes
  parent : Bytes
  profile : Bytes
  proof : Bytes
  config : Bytes
  scale : Bytes
  version : Bytes
  plan : Bytes
  refs : List RefWire
  ticket : Bytes
  total : Bytes
  envelopes : Bytes
  payloads : Bytes
  kind : Bytes
  deriving DecidableEq, Repr

def encode (w : Wire) : Bytes :=
  [123] ++
    memberBytes "aggregation_steps" .natural w.steps 44 ++
    memberBytes "commitment_root" .text w.root 44 ++
    memberBytes "domain_id" .text w.domain 44 ++
    memberBytes "formal_semantics_id" .text w.semantics 44 ++
    memberBytes "parameter_schema_id" .text w.schema 44 ++
    memberBytes "parent_checkpoint_id" .text w.parent 44 ++
    memberBytes "profile_id" .text w.profile 44 ++
    memberBytes "proof_instance_id" .text w.proof 44 ++
    memberBytes "round_config_id" .text w.config 44 ++
    memberBytes "scale_table_id" .text w.scale 44 ++
    memberBytes "schema_version" .text w.version 44 ++
    memberBytes "shard_plan_id" .text w.plan 44 ++
    ascii "\"shards\":[" ++ refsBytes w.refs ++ [44] ++
    memberBytes "ticket_id" .text w.ticket 44 ++
    memberBytes "total_elements" .natural w.total 44 ++
    memberBytes "total_envelope_bytes" .natural w.envelopes 44 ++
    memberBytes "total_payload_bytes" .natural w.payloads 44 ++
    memberBytes "type_name" .text w.kind 125

def parse (raw : Bytes) : Option (Wire × Bytes) := do
  let raw ← consume [123] raw
  let (steps,raw) ← readMember "aggregation_steps" .natural 44 raw
  let (root,raw) ← readMember "commitment_root" .text 44 raw
  let (domain,raw) ← readMember "domain_id" .text 44 raw
  let (semantics,raw) ← readMember "formal_semantics_id" .text 44 raw
  let (schema,raw) ← readMember "parameter_schema_id" .text 44 raw
  let (parent,raw) ← readMember "parent_checkpoint_id" .text 44 raw
  let (profile,raw) ← readMember "profile_id" .text 44 raw
  let (proof,raw) ← readMember "proof_instance_id" .text 44 raw
  let (config,raw) ← readMember "round_config_id" .text 44 raw
  let (scale,raw) ← readMember "scale_table_id" .text 44 raw
  let (version,raw) ← readMember "schema_version" .text 44 raw
  let (plan,raw) ← readMember "shard_plan_id" .text 44 raw
  let raw ← consume (ascii "\"shards\":[") raw
  let (refs,raw) ← readRefs raw
  let raw ← consume [44] raw
  let (ticket,raw) ← readMember "ticket_id" .text 44 raw
  let (total,raw) ← readMember "total_elements" .natural 44 raw
  let (envelopes,raw) ← readMember "total_envelope_bytes" .natural 44 raw
  let (payloads,raw) ← readMember "total_payload_bytes" .natural 44 raw
  let (kind,raw) ← readMember "type_name" .text 125 raw
  some (⟨steps,root,domain,semantics,schema,parent,profile,proof,config,scale,version,plan,refs,ticket,total,envelopes,payloads,kind⟩,raw)

def Syntax (w : Wire) : Prop :=
  ValueValid .natural w.steps ∧
  ValueValid .text w.root ∧
  ValueValid .text w.domain ∧
  ValueValid .text w.semantics ∧
  ValueValid .text w.schema ∧
  ValueValid .text w.parent ∧
  ValueValid .text w.profile ∧
  ValueValid .text w.proof ∧
  ValueValid .text w.config ∧
  ValueValid .text w.scale ∧
  ValueValid .text w.version ∧
  ValueValid .text w.plan ∧
  w.refs.length ≤ 4096 ∧ (∀ e ∈ w.refs, RefSyntax e) ∧
  ValueValid .text w.ticket ∧
  ValueValid .natural w.total ∧
  ValueValid .natural w.envelopes ∧
  ValueValid .natural w.payloads ∧
  ValueValid .text w.kind
instance (w) : Decidable (Syntax w) := by unfold Syntax; infer_instance

theorem parsedEncoded (w : Wire) (tail : Bytes) (h : Syntax w) :
    parse (encode w ++ tail) = some (w,tail) := by
  rcases h with ⟨h0,h1,h2,h3,h4,h5,h6,h7,h8,h9,h10,h11,h12,h13,h14,h15,h16,h17,h18⟩
  simp only [parse,encode,List.append_assoc,consumeAppend,bind,Option.bind]
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
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h5]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h6]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h7]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h8]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h9]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h10]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h11]
  dsimp only
  rw [consumeAppend]
  dsimp only
  rw [refsEncoded w.refs _ h12 h13]
  simp only [consumeAppend]
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h14]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h15]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h16]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h17]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inr rfl) h18]

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


end DeltaReduce.NativeManifestBytes
