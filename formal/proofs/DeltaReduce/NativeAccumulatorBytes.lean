import DeltaReduce.NativeScaleBytes
/-! Exact original004 configuration/proof byte grammar. The fixed theorem-name
array is checked metadata, never accepted as a mathematical proof. -/
namespace DeltaReduce.NativeAccumulatorBytes
open NativeReceiptBytes (Bytes consume consumeAppend)
open NativeVoteBytes (ascii)
open NativeQJson (ValueValid)
open NativeScaleBytes (memberBytes readMember memberEncoded)
def theoremBytes : Bytes := [34, 116, 104, 101, 111, 114, 101, 109, 115, 34, 58, 91, 123, 34, 111, 98, 108, 105, 103, 97, 116, 105, 111, 110, 95, 105, 100, 34, 58, 34, 80, 79, 45, 65, 49, 34, 44, 34, 116, 104, 101, 111, 114, 101, 109, 95, 110, 97, 109, 101, 115, 34, 58, 91, 34, 68, 101, 108, 116, 97, 82, 101, 100, 117, 99, 101, 46, 115, 105, 103, 110, 101, 100, 80, 114, 111, 100, 117, 99, 116, 66, 111, 117, 110, 100, 34, 44, 34, 68, 101, 108, 116, 97, 82, 101, 100, 117, 99, 101, 46, 105, 110, 116, 101, 114, 109, 101, 100, 105, 97, 116, 101, 80, 114, 111, 100, 117, 99, 116, 70, 105, 116, 115, 34, 93, 125, 44, 123, 34, 111, 98, 108, 105, 103, 97, 116, 105, 111, 110, 95, 105, 100, 34, 58, 34, 80, 79, 45, 65, 50, 34, 44, 34, 116, 104, 101, 111, 114, 101, 109, 95, 110, 97, 109, 101, 115, 34, 58, 91, 34, 68, 101, 108, 116, 97, 82, 101, 100, 117, 99, 101, 46, 102, 108, 97, 116, 65, 99, 99, 117, 109, 117, 108, 97, 116, 111, 114, 66, 111, 117, 110, 100, 34, 44, 34, 68, 101, 108, 116, 97, 82, 101, 100, 117, 99, 101, 46, 101, 118, 101, 114, 121, 67, 97, 110, 111, 110, 105, 99, 97, 108, 80, 114, 101, 102, 105, 120, 70, 105, 116, 115, 34, 93, 125, 44, 123, 34, 111, 98, 108, 105, 103, 97, 116, 105, 111, 110, 95, 105, 100, 34, 58, 34, 80, 79, 45, 65, 51, 34, 44, 34, 116, 104, 101, 111, 114, 101, 109, 95, 110, 97, 109, 101, 115, 34, 58, 91, 34, 68, 101, 108, 116, 97, 82, 101, 100, 117, 99, 101, 46, 99, 111, 109, 109, 111, 110, 68, 101, 110, 111, 109, 105, 110, 97, 116, 111, 114, 78, 117, 109, 101, 114, 97, 116, 111, 114, 83, 97, 102, 101, 34, 44, 34, 68, 101, 108, 116, 97, 82, 101, 100, 117, 99, 101, 46, 114, 101, 100, 117, 99, 101, 100, 82, 97, 116, 105, 111, 110, 97, 108, 68, 101, 110, 111, 109, 105, 110, 97, 116, 111, 114, 80, 111, 115, 105, 116, 105, 118, 101, 34, 44, 34, 68, 101, 108, 116, 97, 82, 101, 100, 117, 99, 101, 46, 114, 101, 100, 117, 99, 101, 100, 82, 97, 116, 105, 111, 110, 97, 108, 73, 115, 67, 111, 112, 114, 105, 109, 101, 34, 44, 34, 68, 101, 108, 116, 97, 82, 101, 100, 117, 99, 101, 46, 99, 111, 109, 109, 111, 110, 68, 101, 110, 111, 109, 105, 110, 97, 116, 111, 114, 80, 111, 115, 105, 116, 105, 118, 101, 34, 44, 34, 68, 101, 108, 116, 97, 82, 101, 100, 117, 99, 101, 46, 101, 97, 99, 104, 68, 101, 110, 111, 109, 105, 110, 97, 116, 111, 114, 68, 105, 118, 105, 100, 101, 115, 67, 111, 109, 109, 111, 110, 34, 44, 34, 68, 101, 108, 116, 97, 82, 101, 100, 117, 99, 101, 46, 99, 97, 110, 111, 110, 105, 99, 97, 108, 82, 111, 117, 110, 100, 66, 101, 108, 111, 119, 72, 97, 108, 102, 34, 44, 34, 68, 101, 108, 116, 97, 82, 101, 100, 117, 99, 101, 46, 99, 97, 110, 111, 110, 105, 99, 97, 108, 82, 111, 117, 110, 100, 65, 116, 79, 114, 65, 98, 111, 118, 101, 72, 97, 108, 102, 34, 44, 34, 68, 101, 108, 116, 97, 82, 101, 100, 117, 99, 101, 46, 99, 97, 110, 111, 110, 105, 99, 97, 108, 82, 111, 117, 110, 100, 84, 105, 101, 84, 111, 119, 97, 114, 100, 80, 111, 115, 105, 116, 105, 118, 101, 34, 44, 34, 68, 101, 108, 116, 97, 82, 101, 100, 117, 99, 101, 46, 99, 97, 110, 111, 110, 105, 99, 97, 108, 82, 111, 117, 110, 100, 68, 101, 116, 101, 114, 109, 105, 110, 105, 115, 116, 105, 99, 34, 93, 125, 93, 44]

structure Config where
  width : Bytes
  base : Bytes
  coefficient : Bytes
  semantics : Bytes
  count : Bytes
  schema : Bytes
  profile : Bytes
  q : Bytes
  scale : Bytes
  version : Bytes
  plan : Bytes
  kind : Bytes
  deriving DecidableEq, Repr

def encodeConfig (w : Config) : Bytes :=
  [123] ++
  memberBytes "accumulator_width_bits" .natural w.width 44 ++
  memberBytes "base_round_config_id" .text w.base 44 ++
  memberBytes "coefficient_abs_max" .text w.coefficient 44 ++
  memberBytes "formal_semantics_id" .text w.semantics 44 ++
  memberBytes "max_eligible_contributions" .text w.count 44 ++
  memberBytes "parameter_schema_id" .text w.schema 44 ++
  memberBytes "profile_id" .text w.profile 44 ++
  memberBytes "q_abs_max" .text w.q 44 ++
  memberBytes "scale_table_id" .text w.scale 44 ++
  memberBytes "schema_version" .text w.version 44 ++
  memberBytes "shard_plan_id" .text w.plan 44 ++
  memberBytes "type_name" .text w.kind 125

def parseConfig (raw : Bytes) : Option (Config × Bytes) := do
  let raw ← consume [123] raw
  let (width,raw) ← readMember "accumulator_width_bits" .natural 44 raw
  let (base,raw) ← readMember "base_round_config_id" .text 44 raw
  let (coefficient,raw) ← readMember "coefficient_abs_max" .text 44 raw
  let (semantics,raw) ← readMember "formal_semantics_id" .text 44 raw
  let (count,raw) ← readMember "max_eligible_contributions" .text 44 raw
  let (schema,raw) ← readMember "parameter_schema_id" .text 44 raw
  let (profile,raw) ← readMember "profile_id" .text 44 raw
  let (q,raw) ← readMember "q_abs_max" .text 44 raw
  let (scale,raw) ← readMember "scale_table_id" .text 44 raw
  let (version,raw) ← readMember "schema_version" .text 44 raw
  let (plan,raw) ← readMember "shard_plan_id" .text 44 raw
  let (kind,raw) ← readMember "type_name" .text 125 raw
  some (⟨width,base,coefficient,semantics,count,schema,profile,q,scale,version,plan,kind⟩,raw)

def ConfigSyntax (w : Config) : Prop :=
  ValueValid .natural w.width ∧
  ValueValid .text w.base ∧
  ValueValid .text w.coefficient ∧
  ValueValid .text w.semantics ∧
  ValueValid .text w.count ∧
  ValueValid .text w.schema ∧
  ValueValid .text w.profile ∧
  ValueValid .text w.q ∧
  ValueValid .text w.scale ∧
  ValueValid .text w.version ∧
  ValueValid .text w.plan ∧
  ValueValid .text w.kind
instance (w) : Decidable (ConfigSyntax w) := by unfold ConfigSyntax; infer_instance

theorem parsedConfig (w : Config) (tail : Bytes) (valid : ConfigSyntax w) :
    parseConfig (encodeConfig w ++ tail) = some (w,tail) := by
  rcases valid with ⟨h0,h1,h2,h3,h4,h5,h6,h7,h8,h9,h10,h11⟩
  simp only [parseConfig,encodeConfig,List.append_assoc,consumeAppend,bind,Option.bind]
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
  rw [memberEncoded _ _ _ _ _ (Or.inr rfl) h11]

def decodeConfig (raw : Bytes) : Option Config := do
  if raw.length ≤ 65536 then do
    let (w,rest) ← parseConfig raw
    if rest = [] ∧ ConfigSyntax w ∧ encodeConfig w = raw then some w else none
  else none

theorem decodedConfig {raw w} (h : decodeConfig raw = some w) :
    raw.length ≤ 65536 ∧ parseConfig raw = some (w,[]) ∧ ConfigSyntax w ∧ encodeConfig w = raw := by
  unfold decodeConfig at h
  split at h <;> try contradiction
  rename_i size
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨w,rest⟩,parsed,last⟩ := h
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  rcases checks with ⟨rfl,valid,eq⟩
  exact ⟨size,parsed,valid,eq⟩

theorem decodeConfigEncoded (w : Config) (valid : ConfigSyntax w)
    (size : (encodeConfig w).length ≤ 65536) : decodeConfig (encodeConfig w) = some w := by
  have parsed := parsedConfig w [] valid
  simp only [List.append_nil] at parsed
  simp [decodeConfig,size,parsed,valid]

theorem configUnique {a b} (va : ConfigSyntax a) (vb : ConfigSyntax b)
    (same : encodeConfig a = encodeConfig b) : a = b := by
  have h := parsedConfig a [] va
  rw [same,parsedConfig b [] vb] at h
  exact (Prod.mk.inj (Option.some.inj h)).1.symm

structure Proof where
  coefficient : Bytes
  denominator : Bytes
  config : Bytes
  finalBound : Bytes
  semantics : Bytes
  lean : Bytes
  count : Bytes
  prefixBound : Bytes
  product : Bytes
  productWidth : Bytes
  profile : Bytes
  q : Bytes
  result : Bytes
  scale : Bytes
  version : Bytes
  width : Bytes
  kind : Bytes
  deriving DecidableEq, Repr

def encodeProof (w : Proof) : Bytes :=
  [123] ++
  memberBytes "coefficient_abs_max" .text w.coefficient 44 ++
  memberBytes "common_denominator" .text w.denominator 44 ++
  memberBytes "config_id" .text w.config 44 ++
  memberBytes "final_abs_bound" .text w.finalBound 44 ++
  memberBytes "formal_semantics_id" .text w.semantics 44 ++
  memberBytes "lean_artifact_sha256" .text w.lean 44 ++
  memberBytes "max_eligible_contributions" .text w.count 44 ++
  memberBytes "max_incremental_prefix_abs" .text w.prefixBound 44 ++
  memberBytes "product_abs_bound" .text w.product 44 ++
  memberBytes "product_width_bits" .natural w.productWidth 44 ++
  memberBytes "profile_id" .text w.profile 44 ++
  memberBytes "q_abs_max" .text w.q 44 ++
  memberBytes "result" .text w.result 44 ++
  memberBytes "scale_table_id" .text w.scale 44 ++
  memberBytes "schema_version" .text w.version 44 ++
  memberBytes "selected_accumulator_width_bits" .natural w.width 44 ++
  theoremBytes ++
  memberBytes "type_name" .text w.kind 125

def parseProof (raw : Bytes) : Option (Proof × Bytes) := do
  let raw ← consume [123] raw
  let (coefficient,raw) ← readMember "coefficient_abs_max" .text 44 raw
  let (denominator,raw) ← readMember "common_denominator" .text 44 raw
  let (config,raw) ← readMember "config_id" .text 44 raw
  let (finalBound,raw) ← readMember "final_abs_bound" .text 44 raw
  let (semantics,raw) ← readMember "formal_semantics_id" .text 44 raw
  let (lean,raw) ← readMember "lean_artifact_sha256" .text 44 raw
  let (count,raw) ← readMember "max_eligible_contributions" .text 44 raw
  let (prefixBound,raw) ← readMember "max_incremental_prefix_abs" .text 44 raw
  let (product,raw) ← readMember "product_abs_bound" .text 44 raw
  let (productWidth,raw) ← readMember "product_width_bits" .natural 44 raw
  let (profile,raw) ← readMember "profile_id" .text 44 raw
  let (q,raw) ← readMember "q_abs_max" .text 44 raw
  let (result,raw) ← readMember "result" .text 44 raw
  let (scale,raw) ← readMember "scale_table_id" .text 44 raw
  let (version,raw) ← readMember "schema_version" .text 44 raw
  let (width,raw) ← readMember "selected_accumulator_width_bits" .natural 44 raw
  let raw ← consume theoremBytes raw
  let (kind,raw) ← readMember "type_name" .text 125 raw
  some (⟨coefficient,denominator,config,finalBound,semantics,lean,count,prefixBound,product,productWidth,profile,q,result,scale,version,width,kind⟩,raw)

def ProofSyntax (w : Proof) : Prop :=
  ValueValid .text w.coefficient ∧
  ValueValid .text w.denominator ∧
  ValueValid .text w.config ∧
  ValueValid .text w.finalBound ∧
  ValueValid .text w.semantics ∧
  ValueValid .text w.lean ∧
  ValueValid .text w.count ∧
  ValueValid .text w.prefixBound ∧
  ValueValid .text w.product ∧
  ValueValid .natural w.productWidth ∧
  ValueValid .text w.profile ∧
  ValueValid .text w.q ∧
  ValueValid .text w.result ∧
  ValueValid .text w.scale ∧
  ValueValid .text w.version ∧
  ValueValid .natural w.width ∧
  ValueValid .text w.kind
instance (w) : Decidable (ProofSyntax w) := by unfold ProofSyntax; infer_instance

theorem parsedProof (w : Proof) (tail : Bytes) (valid : ProofSyntax w) :
    parseProof (encodeProof w ++ tail) = some (w,tail) := by
  rcases valid with ⟨h0,h1,h2,h3,h4,h5,h6,h7,h8,h9,h10,h11,h12,h13,h14,h15,h16⟩
  simp only [parseProof,encodeProof,List.append_assoc,consumeAppend,bind,Option.bind]
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
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h12]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h13]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h14]
  dsimp only
  rw [memberEncoded _ _ _ _ _ (Or.inl rfl) h15]
  dsimp only
  simp only [consumeAppend]
  rw [memberEncoded _ _ _ _ _ (Or.inr rfl) h16]

def decodeProof (raw : Bytes) : Option Proof := do
  if raw.length ≤ 65536 then do
    let (w,rest) ← parseProof raw
    if rest = [] ∧ ProofSyntax w ∧ encodeProof w = raw then some w else none
  else none

theorem decodedProof {raw w} (h : decodeProof raw = some w) :
    raw.length ≤ 65536 ∧ parseProof raw = some (w,[]) ∧ ProofSyntax w ∧ encodeProof w = raw := by
  unfold decodeProof at h
  split at h <;> try contradiction
  rename_i size
  simp only [bind,Option.bind_eq_some_iff] at h
  obtain ⟨⟨w,rest⟩,parsed,last⟩ := h
  split at last <;> try contradiction
  rename_i checks
  cases Option.some.inj last
  rcases checks with ⟨rfl,valid,eq⟩
  exact ⟨size,parsed,valid,eq⟩

theorem decodeProofEncoded (w : Proof) (valid : ProofSyntax w)
    (size : (encodeProof w).length ≤ 65536) : decodeProof (encodeProof w) = some w := by
  have parsed := parsedProof w [] valid
  simp only [List.append_nil] at parsed
  simp [decodeProof,size,parsed,valid]

theorem proofUnique {a b} (va : ProofSyntax a) (vb : ProofSyntax b)
    (same : encodeProof a = encodeProof b) : a = b := by
  have h := parsedProof a [] va
  rw [same,parsedProof b [] vb] at h
  exact (Prod.mk.inj (Option.some.inj h)).1.symm

end DeltaReduce.NativeAccumulatorBytes
