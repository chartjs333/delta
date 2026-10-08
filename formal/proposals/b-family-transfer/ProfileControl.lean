import ProfileSource

/-! T047/T053: exact typed control-document encoding under Profile v1.
Python may propose a typed descriptor; the kernel-side check compares its full
canonical bytes with the original. This is not authority, history legality or
the complete semantic field/cross-reference validation in ProfileSource. -/
namespace DeltaReduce.ProfileSource.Control
open NativeReceiptBytes (Bytes)
open NativeVoteBytes (ascii)

mutual
inductive Node where
  | text (value : Bytes)
  | boolean (value : Bool)
  | array (items : Nodes)
  | object (fields : Fields)
  deriving DecidableEq, Repr
inductive Nodes where
  | nil
  | cons (head : Node) (tail : Nodes)
  deriving DecidableEq, Repr
inductive Fields where
  | nil
  | cons (name : Bytes) (value : Node) (tail : Fields)
  deriving DecidableEq, Repr
end

def safe (raw : Bytes) : Bool := raw.all fun b =>
  decide (32 ≤ b.toNat ∧ b.toNat ≤ 126 ∧ b ≠ 34 ∧ b ≠ 92)
def quoted (raw : Bytes) : Bytes := [34] ++ raw ++ [34]

mutual
def encode : Node → Bytes
  | .text raw => quoted raw
  | .boolean value => ascii (if value then "true" else "false")
  | .array xs => [91] ++ encodeNodes xs ++ [93]
  | .object fs => [123] ++ encodeFields fs ++ [125]
def encodeNodes : Nodes → Bytes
  | .nil => []
  | .cons x .nil => encode x
  | .cons x xs => encode x ++ [44] ++ encodeNodes xs
def encodeFields : Fields → Bytes
  | .nil => []
  | .cons key value .nil => quoted key ++ [58] ++ encode value
  | .cons key value rest => quoted key ++ [58] ++ encode value ++ [44] ++ encodeFields rest
end

def names : Fields → List Bytes
  | .nil => []
  | .cons key _ rest => key :: names rest

def lookup : Fields → Bytes → Option Node
  | .nil, _ => none
  | .cons key value rest, wanted => if wanted = key then some value else lookup rest wanted

mutual
def canonical : Node → Bool
  | .text raw => safe raw
  | .boolean _ => true
  | .array xs => canonicalNodes xs
  | .object fs => canonicalFields fs
def canonicalNodes : Nodes → Bool
  | .nil => true
  | .cons x xs => canonical x && canonicalNodes xs
def canonicalFields : Fields → Bool
  | .nil => true
  | .cons key value rest => !key.isEmpty && safe key && canonical value &&
      (names rest).all (fun following => key.lex following (fun a b => decide (a < b))) &&
      canonicalFields rest
end

inductive Kind where
  | bootstrap | manifest | sourceIndex | init | activate | anchor
  deriving DecidableEq, Repr

def typeName : Kind → String
  | .bootstrap => "BOOTSTRAP"
  | .manifest => "MANIFEST"
  | .sourceIndex => "SOURCE_INDEX"
  | _ => "TRUST_RECORD"

def required : Kind → List String
  | .bootstrap => ["formal_semantics_id", "genesis_ref", "initial_anchor", "initial_config_ref",
      "local_validator_id", "origin_id", "producer_rules_id", "profile_id", "quorum_threshold",
      "runtime_build_id", "schema_set_id", "schema_version", "signature_codec_id", "type_name",
      "validator_epoch_id", "validators"]
  | .manifest => ["anchor", "apply_candidate_ref", "apply_qc_ref", "artifacts", "bootstrap_id",
      "cut_event_index", "formal_semantics_id", "journals", "local_validator_id", "origin_id",
      "profile_id", "schema_set_id", "schema_version", "snapshot_ref", "source_index_ref",
      "target_event_index", "type_name", "validator_epoch_id"]
  | .sourceIndex => ["artifacts", "events", "genesis_ref", "local_validator_id", "origin_id",
      "original_journal_refs", "profile_id", "schema_version", "type_name", "validator_epoch_id"]
  | .init => ["anchor", "bootstrap_id", "journal_cuts", "kind", "ordinal", "previous_record_id",
      "profile_id", "schema_version", "type_name"]
  | .activate | .anchor => ["anchor", "bootstrap_id", "generation_id", "journal_cuts", "kind",
      "manifest_id", "ordinal", "previous_record_id", "profile_id", "schema_version", "type_name"]

def recordKind : Kind → Option String
  | .init => some "INIT"
  | .activate => some "ACTIVATE"
  | .anchor => some "ANCHOR"
  | _ => none

def Shape (kind : Kind) (fs : Fields) : Prop :=
  names fs = (required kind).map ascii ∧ canonicalFields fs = true ∧
  lookup fs (ascii "type_name") = some (.text (ascii (typeName kind))) ∧
  lookup fs (ascii "schema_version") = some (.text (ascii "1")) ∧
  lookup fs (ascii "profile_id") = some (.text (ascii "snapshot-provenance-linux-single-epoch-v1")) ∧
  (match recordKind kind with
    | none => True
    | some k => lookup fs (ascii "kind") = some (.text (ascii k)))
instance (kind fs) : Decidable (Shape kind fs) := by
  unfold Shape
  cases recordKind kind <;> infer_instance

def check (kind : Kind) (descriptor : Fields) (original : Bytes) : Option Fields :=
  if Shape kind descriptor ∧ encode (.object descriptor) = original ∧ original.length ≤ 4*1024*1024
  then some descriptor else none

theorem checked {kind descriptor original out} (ok : check kind descriptor original = some out) :
    out = descriptor ∧ Shape kind out ∧ encode (.object out) = original ∧
    original.length ≤ 4*1024*1024 := by
  unfold check at ok
  split at ok
  · rename_i conditions
    cases Option.some.inj ok
    exact ⟨rfl, conditions⟩
  · contradiction

theorem complete {kind descriptor original}
    (shape : Shape kind descriptor) (bytes : encode (.object descriptor) = original)
    (bound : original.length ≤ 4*1024*1024) : check kind descriptor original = some descriptor := by
  simp [check, shape, bytes, bound]

theorem originalBytesCannotBeSubstituted {kind descriptor first second a b}
    (left : check kind descriptor first = some a) (right : check kind descriptor second = some b) :
    first = second := by
  have hl := checked left
  have hr := checked right
  rw [hl.1] at hl
  rw [hr.1] at hr
  exact hl.2.2.1.symm.trans hr.2.2.1

theorem rootFieldsExact {kind descriptor original out}
    (ok : check kind descriptor original = some out) : names out = (required kind).map ascii :=
  (checked ok).2.1.1

theorem profileIndependentOfImportedVersion {kind descriptor original out}
    (ok : check kind descriptor original = some out) :
    lookup out (ascii "schema_version") = some (.text (ascii "1")) ∧
    lookup out (ascii "profile_id") = some (.text (ascii "snapshot-provenance-linux-single-epoch-v1")) :=
  ⟨(checked ok).2.1.2.2.2.1, (checked ok).2.1.2.2.2.2.1⟩

end DeltaReduce.ProfileSource.Control
