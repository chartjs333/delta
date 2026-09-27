import DeltaReduce.NativeJsonSequence

/-! Original parameter-schema canonical ASCII bytes, including omitted parameters
and aliases. Hash/source authority and native implementation equivalence are separate. -/
namespace DeltaReduce.NativeSchemaBytes
open NativeReceiptBytes (Bytes consume consumeAppend)
open NativeVoteBytes (ascii DecimalValid digit)
open NativeScaleBytes (memberBytes readMember memberEncoded)
open NativeJsonSequence (textBytes readText textEncoded)

def shapeBytes (xs : List Bytes) := NativeJsonSequence.encode 93 id xs
def readShape := NativeJsonSequence.read 93 NativeJsonSequence.readNatural 32

theorem shapeEncoded (xs : List Bytes) (tail : Bytes)
    (size : xs.length ≤ 32) (valid : ∀ x ∈ xs, DecimalValid x) :
    readShape (shapeBytes xs ++ tail) = some (xs,tail) := by
  apply NativeJsonSequence.encoded 93 (by decide) id _ DecimalValid xs 32 tail size valid
  · intro x hx
    cases x with
    | nil => exact False.elim (hx.1 rfl)
    | cons b rest =>
      refine ⟨b,rest,rfl,?_⟩
      have h := hx.2.2.1 b (by simp)
      intro eq; subst b; simp [digit] at h
  · intro x hx sep rest hs
    apply NativeJsonSequence.naturalEncoded x rest sep hx
    rcases hs with rfl | rfl <;> decide

def boolBytes (b : Bool) : Bytes := if b then ascii "true" else ascii "false"
def readBool (raw : Bytes) : Option (Bool × Bytes) :=
  match consume (ascii "true") raw with
  | some rest => some (true,rest)
  | none => (consume (ascii "false") raw).map (fun rest => (false,rest))

theorem boolEncoded (b : Bool) (tail : Bytes) :
    readBool (boolBytes b ++ tail) = some (b,tail) := by
  cases b <;> simp [readBool,boolBytes,ascii,consume]

structure Parameter where
  dtype : Bytes
  name : Bytes
  shape : List Bytes
  trainable : Bool
  deriving DecidableEq, Repr

def parameterBytes (p : Parameter) : Bytes :=
  [123] ++ memberBytes "logical_dtype" .text p.dtype 44 ++
    memberBytes "name" .text p.name 44 ++ ascii "\"shape\":[" ++ shapeBytes p.shape ++
    ascii ",\"trainable\":" ++ boolBytes p.trainable ++ [125]

def readParameter (raw : Bytes) : Option (Parameter × Bytes) := do
  let raw ← consume [123] raw
  let (dtype,raw) ← readMember "logical_dtype" .text 44 raw
  let (name,raw) ← readMember "name" .text 44 raw
  let raw ← consume (ascii "\"shape\":[") raw
  let (shape,raw) ← readShape raw
  let raw ← consume (ascii ",\"trainable\":") raw
  let (trainable,raw) ← readBool raw
  let raw ← consume [125] raw
  some (⟨dtype,name,shape,trainable⟩,raw)

def ParameterSyntax (p : Parameter) : Prop :=
  NativeQJson.TextValid p.dtype ∧ NativeQJson.TextValid p.name ∧
  p.shape.length ≤ 32 ∧ ∀ d ∈ p.shape, DecimalValid d
instance (p) : Decidable (ParameterSyntax p) := by unfold ParameterSyntax; infer_instance

theorem parameterEncoded (p : Parameter) (tail : Bytes) (h : ParameterSyntax p) :
    readParameter (parameterBytes p ++ tail) = some (p,tail) := by
  simp only [readParameter,parameterBytes,List.append_assoc,consumeAppend,bind,Option.bind]
  rw [memberEncoded _ .text _ _ _ (Or.inl rfl) h.1]
  dsimp only
  rw [memberEncoded _ .text _ _ _ (Or.inl rfl) h.2.1]
  simp only [consumeAppend]
  rw [shapeEncoded p.shape _ h.2.2.1 h.2.2.2]
  simp only [consumeAppend]
  rw [boolEncoded]
  simp [consume]

def parametersBytes := NativeJsonSequence.encode 93 parameterBytes
def readParameters := NativeJsonSequence.read 93 readParameter 65536

theorem parametersEncoded (ps : List Parameter) (tail : Bytes)
    (size : ps.length ≤ 65536) (valid : ∀ p ∈ ps, ParameterSyntax p) :
    readParameters (parametersBytes ps ++ tail) = some (ps,tail) := by
  apply NativeJsonSequence.encoded 93 (by decide) parameterBytes _ ParameterSyntax
    ps 65536 tail size valid
  · intro p _; exact ⟨123,_,rfl,by decide⟩
  · intro p hp sep rest _; exact parameterEncoded p (sep::rest) hp

def aliasBytes (a : Bytes × Bytes) := textBytes a.1 ++ [58] ++ textBytes a.2
def readAlias (raw : Bytes) : Option ((Bytes × Bytes) × Bytes) := do
  let (alias,raw) ← readText raw
  let raw ← consume [58] raw
  let (owner,raw) ← readText raw
  some ((alias,owner),raw)

def AliasSyntax (a : Bytes × Bytes) := NativeQJson.TextValid a.1 ∧ NativeQJson.TextValid a.2
instance (a) : Decidable (AliasSyntax a) := by unfold AliasSyntax; infer_instance

theorem aliasEncoded (a : Bytes × Bytes) (tail : Bytes) (h : AliasSyntax a) :
    readAlias (aliasBytes a ++ tail) = some (a,tail) := by
  simp only [readAlias,aliasBytes,List.append_assoc]
  rw [textEncoded a.1 _ h.1]
  simp only [bind,Option.bind,consumeAppend]
  rw [textEncoded a.2 tail h.2]

def aliasesBytes := NativeJsonSequence.encode 125 aliasBytes
def readAliases := NativeJsonSequence.read 125 readAlias 65536

theorem aliasesEncoded (xs : List (Bytes × Bytes)) (tail : Bytes)
    (size : xs.length ≤ 65536) (valid : ∀ a ∈ xs, AliasSyntax a) :
    readAliases (aliasesBytes xs ++ tail) = some (xs,tail) := by
  apply NativeJsonSequence.encoded 125 (by decide) aliasBytes _ AliasSyntax
    xs 65536 tail size valid
  · intro a _; exact ⟨34,_,rfl,by decide⟩
  · intro a ha sep rest _; exact aliasEncoded a (sep::rest) ha

structure Wire where
  policy : Bytes
  parameters : List Parameter
  version : Bytes
  aliases : List (Bytes × Bytes)
  deriving DecidableEq, Repr

def encode (w : Wire) : Bytes :=
  [123] ++ memberBytes "frozen_omission_policy" .text w.policy 44 ++
  ascii "\"parameters\":[" ++ parametersBytes w.parameters ++ [44] ++
  memberBytes "schema_version" .text w.version 44 ++ ascii "\"tied_aliases\":{" ++
  aliasesBytes w.aliases ++ [125]

def parse (raw : Bytes) : Option (Wire × Bytes) := do
  let raw ← consume [123] raw
  let (policy,raw) ← readMember "frozen_omission_policy" .text 44 raw
  let raw ← consume (ascii "\"parameters\":[") raw
  let (parameters,raw) ← readParameters raw
  let raw ← consume [44] raw
  let (version,raw) ← readMember "schema_version" .text 44 raw
  let raw ← consume (ascii "\"tied_aliases\":{") raw
  let (aliases,raw) ← readAliases raw
  let raw ← consume [125] raw
  some (⟨policy,parameters,version,aliases⟩,raw)

def Syntax (w : Wire) : Prop :=
  NativeQJson.TextValid w.policy ∧ w.parameters.length ≤ 65536 ∧
  (∀ p ∈ w.parameters, ParameterSyntax p) ∧ NativeQJson.TextValid w.version ∧
  w.aliases.length ≤ 65536 ∧ ∀ a ∈ w.aliases, AliasSyntax a
instance (w) : Decidable (Syntax w) := by unfold Syntax; infer_instance

theorem parsedEncoded (w : Wire) (tail : Bytes) (h : Syntax w) :
    parse (encode w ++ tail) = some (w,tail) := by
  simp only [parse,encode,List.append_assoc,consumeAppend,bind,Option.bind]
  rw [memberEncoded _ .text _ _ _ (Or.inl rfl) h.1]
  simp only [consumeAppend]
  rw [parametersEncoded w.parameters _ h.2.1 h.2.2.1]
  simp only [consumeAppend]
  rw [memberEncoded _ .text _ _ _ (Or.inl rfl) h.2.2.2.1]
  simp only [consumeAppend]
  rw [aliasesEncoded w.aliases _ h.2.2.2.2.1 h.2.2.2.2.2]
  simp [consume]

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

end DeltaReduce.NativeSchemaBytes
