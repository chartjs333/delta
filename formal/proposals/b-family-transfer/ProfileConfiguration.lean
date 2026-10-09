import DeltaReduce.NativePolicyCodec
import DeltaReduce.NativeVoteBytes
import DeltaReduce.NativeConfigAdmission

/-! T047/T053. Exact full DRC1 configuration source, using the existing tags,
widths and closed future schema. The original two input-close policies are read
from these bytes, never supplied by the public projection. This is the source
codec conjunct of R2.3, not CONFIG finality or complete producer provenance. -/
namespace DeltaReduce.ProfileSource.Configuration
open NativeReceiptBytes NativeVoteBytes
open NativePolicyCodec (Value writeMany readMany manyRoundTrip)

inductive Format where
  | uint (width : Nat)
  | text
  | field (name : String) (head tail : Format)
  | vector (item : Format)
  | object (fields : Format)
  | end
  deriving DecidableEq, Repr

def fieldCount : Format → Nat
  | .field _ _ tail => 1 + fieldCount tail
  | _ => 0

def mapPrefix (fmt : Format) : Bytes := [49] ++ be 4 (fieldCount fmt)

theorem consumeTag (tag : UInt8) (raw : Bytes) : consume [tag] (tag :: raw) = some raw := by
  simp [consume]

def encode : Format → Value → Option Bytes
  | .uint width, .number n =>
      if n < 256^width ∧ n < 256^8 then some ([16] ++ be 8 n) else none
  | .text, .text raw => if TextValid raw then some (textBytes raw) else none
  | .field name head tail, .pair x y => do
      let a ← encode head x
      let b ← encode tail y
      some (textBytes (ascii name) ++ a ++ b)
  | .vector item, .items vs => do
      if vs.length ≤ 100000 then
        let raw ← writeMany (encode item) vs
        some ([48] ++ be 4 vs.length ++ raw)
      else none
  | .object fields, v => do
      if fieldCount fields ≤ 100000 then
        let raw ← encode fields v
        some (mapPrefix fields ++ raw)
      else none
  | .end, .end => some []
  | _, _ => none

def parse : Format → Bytes → Option (Value × Bytes)
  | .uint width, raw => do
      let raw ← consume [16] raw
      let (n,rest) ← readNat 8 raw
      if n < 256^width ∧ n < 256^8 then some (.number n,rest) else none
  | .text, raw => do
      let (value,rest) ← readText raw
      some (.text value,rest)
  | .field name head tail, raw => do
      let raw ← consume (textBytes (ascii name)) raw
      let (a,raw) ← parse head raw
      let (b,raw) ← parse tail raw
      some (.pair a b,raw)
  | .vector item, raw => do
      let raw ← consume [48] raw
      let (n,raw) ← readNat 4 raw
      if n ≤ 100000 then
        let (vs,rest) ← readMany (parse item) n raw
        some (.items vs,rest)
      else none
  | .object fields, raw => do
      if fieldCount fields ≤ 100000 then
        let raw ← consume (mapPrefix fields) raw
        parse fields raw
      else none
  | .end, raw => some (.end,raw)

theorem roundTrip (fmt : Format) (v : Value) (raw tail : Bytes)
    (ok : encode fmt v = some raw) : parse fmt (raw ++ tail) = some (v,tail) := by
  induction fmt generalizing v raw tail with
  | uint width =>
    cases v <;> simp [encode] at ok
    rename_i n
    obtain ⟨bound,rfl⟩ := ok
    simp only [parse,List.cons_append,consumeTag,bind,Option.bind,
      readNatEncoded 8 n tail bound.2,if_pos bound]
  | text =>
    cases v <;> simp [encode] at ok
    rename_i value
    obtain ⟨valid,rfl⟩ := ok
    simp [parse,readTextEncoded value tail valid]
  | «end» => cases v <;> simp_all [encode,parse]
  | field name head rest ihHead ihRest =>
    cases v <;> simp [encode] at ok
    rename_i x y
    cases hx : encode head x with
    | none => simp [hx] at ok
    | some a =>
      cases hy : encode rest y with
      | none => simp [hx,hy] at ok
      | some b =>
        simp only [hx,hy,Option.bind,Option.some.injEq] at ok
        subst raw
        simp only [parse,List.append_assoc,consumeAppend,bind,Option.bind]
        rw [ihHead x a (b ++ tail) hx]
        dsimp only
        rw [ihRest y b tail hy]
  | vector item ih =>
    cases v <;> simp [encode] at ok
    rename_i vs
    obtain ⟨bound,ok⟩ := ok
    cases hb : writeMany (encode item) vs with
    | none => simp [hb] at ok
    | some body =>
      simp only [hb,Option.bind,Option.some.injEq] at ok
      subst raw
      have small : vs.length < 256^4 := by omega
      simp only [parse,List.cons_append,List.append_assoc,consumeTag,bind,Option.bind,
        readNatEncoded 4 vs.length (body ++ tail) small,if_pos bound]
      rw [manyRoundTrip (encode item) (parse item) ih vs body tail hb]
  | object fields ih =>
    simp only [encode] at ok
    split at ok <;> try contradiction
    rename_i bound
    cases hb : encode fields v with
    | none => simp [hb] at ok
    | some body =>
      simp only [hb,bind,Option.bind,Option.some.injEq] at ok
      subst raw
      simp only [parse,if_pos bound,List.append_assoc,consumeAppend,bind,Option.bind]
      exact ih v body tail hb

def decode (fmt : Format) (raw : Bytes) : Option Value := do
  let (value,rest) ← parse fmt raw
  if rest = [] ∧ encode fmt value = some raw then some value else none

theorem decoded {fmt raw value} (ok : decode fmt raw = some value) :
    parse fmt raw = some (value,[]) ∧ encode fmt value = some raw := by
  unfold decode at ok
  cases hp : parse fmt raw with
  | none => simp [hp] at ok
  | some pair =>
    rcases pair with ⟨v,rest⟩
    simp only [hp,bind,Option.bind] at ok
    split at ok <;> try contradiction
    rename_i checks
    cases Option.some.inj ok
    exact ⟨by simp [checks.1], checks.2⟩

theorem encoded {fmt value raw} (ok : encode fmt value = some raw) :
    decode fmt raw = some value := by
  have h := roundTrip fmt value raw [] ok
  simp only [List.append_nil] at h
  simp [decode,h,ok]

theorem encodingInjective {fmt a b raw}
    (ha : encode fmt a = some raw) (hb : encode fmt b = some raw) : a = b := by
  have left := encoded ha
  rw [encoded hb] at left
  exact (Option.some.inj left).symm

def fields : List (String × Format) → Format
  | [] => .end
  | (name,fmt)::tail => .field name fmt (fields tail)

def object (items : List (String × Format)) : Format := .object (fields items)

def retentionSource : Format := object [
  ("obligation_ref",object [("byte_length",.text),("sha256",.text)]),
  ("retention_epoch_id",.text),("schema_version",.text),("type_name",.text)]

def availability : Format := object [
  ("close_policy",.text),
  ("storage_binding",object [
    ("retention_epoch_id",.text),("retention_policy_source",retentionSource),
    ("storage_epoch_id",.text),("storage_registry_id",.text),("threshold",.text)])]

def configuration : Format := object [
  ("availability_policy",availability),("availability_threshold",.uint 4),
  ("batch_budget",.uint 4),("dataset_manifest_id",.text),
  ("domain_ticket_counts",.vector (object [("domain_id",.text),("ticket_count",.uint 4)])),
  ("fault_tolerance",.uint 4),("formal_semantics_id",.text),("hard_deadline_tick",.text),
  ("height",.text),("integer_profile",object [
    ("accumulator_bits",.uint 4),("byte_order",.text),("profile_id",.text),("value_bits",.uint 4)]),
  ("parameter_schema_id",.text),("parent_checkpoint_id",.text),("protocol_version",.text),
  ("quorum_threshold",.uint 4),("round_id",.text),("schema_version",.text),
  ("soft_deadline_tick",.text),("step_budget",.uint 4),("ticket_count",.uint 4),
  ("type_name",.text),("validator_epoch_id",.text),("validator_ids",.vector .text),
  ("view",.text)]

def lookup : Format → Value → String → Option Value
  | .object fs,v,name => lookup fs v name
  | .field key _ rest,.pair value tail,name =>
      if name = key then some value else lookup rest tail name
  | _,_,_ => none

def text : Option Value → Option Bytes
  | some (.text raw) => some raw
  | _ => none

def selectedClosePolicy (value : Value) : Option Bytes := do
  let policy ← lookup configuration value "availability_policy"
  let selected ← text (lookup availability policy "close_policy")
  if selected = ascii "OMIT_UNAVAILABLE" ∨ selected = ascii "ABORT_ON_INCOMPLETE"
  then some selected else none

def header : Bytes := [68,82,67,49,1,0,0,1]

def encodeFrame (value : Value) : Option Bytes := do
  let raw ← encode configuration value
  let frame := header ++ sizedBytes raw
  if frame.length ≤ maxEnvelope then some frame else none

def decodeFrame (raw : Bytes) : Option Value := do
  if raw.length ≤ maxEnvelope then
    let body ← consume header raw
    let (body,rest) ← readSection maxEnvelope body
    if rest = [] then
      let value ← decode configuration body
      if encodeFrame value = some raw then some value else none
    else none
  else none

theorem frameEncoded {value raw} (ok : encodeFrame value = some raw) :
    decodeFrame raw = some value := by
  unfold encodeFrame at ok
  cases hp : encode configuration value with
  | none => simp [hp] at ok
  | some body =>
    simp only [hp,bind,Option.bind] at ok
    split at ok <;> try contradiction
    rename_i bound
    cases Option.some.inj ok
    have small : body.length ≤ maxEnvelope := by
      have length : (header ++ sizedBytes body).length = 12 + body.length := by
        simp [header,sizedBytes,beLength]; omega
      rw [length] at bound
      omega
    have width : body.length < 256^4 := by unfold maxEnvelope at small; omega
    simp only [decodeFrame,if_pos bound,consumeAppend,bind,Option.bind]
    rw [← List.append_nil (sizedBytes body),readSectionEncoded body [] maxEnvelope width small]
    simp only [↓reduceIte,encoded hp]
    have encodedFrame : encodeFrame value = some (header ++ sizedBytes body) := by
      simp only [encodeFrame,hp,bind,Option.bind,if_pos bound]
    simp only [encodedFrame,List.append_nil,↓reduceIte]

theorem frameDecoded {raw value} (ok : decodeFrame raw = some value) :
    encodeFrame value = some raw := by
  unfold decodeFrame at ok
  split at ok <;> try contradiction
  simp only [bind,Option.bind_eq_some_iff] at ok
  obtain ⟨rest,_,⟨body,tail⟩,_,ok⟩ := ok
  split at ok <;> try contradiction
  simp only [Option.bind_eq_some_iff] at ok
  obtain ⟨v,_,ok⟩ := ok
  split at ok <;> try contradiction
  rename_i same
  cases Option.some.inj ok
  exact same

theorem frameInjective {a b raw}
    (ha : encodeFrame a = some raw) (hb : encodeFrame b = some raw) : a = b := by
  have left := frameEncoded ha
  rw [frameEncoded hb] at left
  exact (Option.some.inj left).symm

def closePolicy (raw : Bytes) : Option Bytes := do
  let value ← decodeFrame raw
  selectedClosePolicy value

theorem policySource {raw selected} (ok : closePolicy raw = some selected) :
    ∃ value, decodeFrame raw = some value ∧ encodeFrame value = some raw ∧
      selectedClosePolicy value = some selected := by
  simp only [closePolicy,bind,Option.bind_eq_some_iff] at ok
  obtain ⟨value,parsed,selected⟩ := ok
  exact ⟨value,parsed,frameDecoded parsed,selected⟩

theorem noPolicyOverride {raw a b}
    (left : closePolicy raw = some a) (right : closePolicy raw = some b) : a = b :=
  Option.some.inj (left.symm.trans right)

def number : Option Value → Option Nat
  | some (.number n) => some n
  | _ => none

def items : Option Value → Option (List Value)
  | some (.items vs) => some vs
  | _ => none

def textField (fmt : Format) (value : Value) (key : String) : Option Bytes :=
  text (lookup fmt value key)

def numberField (fmt : Format) (value : Value) (key : String) : Option Nat :=
  number (lookup fmt value key)

def decimalField (fmt : Format) (value : Value) (key : String) : Option Nat := do
  let raw ← textField fmt value key
  parseDecimal raw

def texts : List Value → Option (List Bytes)
  | [] => some []
  | .text raw::tail => do
      let xs ← texts tail
      some (raw::xs)
  | _ => none

def domainRows : List Value → Option (List (Bytes × Nat))
  | [] => some []
  | .pair (.text domain) (.pair (.number n) .end)::tail => do
      let rows ← domainRows tail
      some ((domain,n)::rows)
  | _ => none

def ordered (vs : List Bytes) : Bool :=
  decide (vs.Pairwise (fun a b => a.lex b (fun x y => decide (x < y)) = true))

structure Body where
  originalValue : Value
  policy : Bytes
  parent : Bytes
  schema : Bytes
  dataset : Bytes
  semantics : Bytes
  epoch : Bytes
  round : Bytes
  height : Nat
  view : Nat
  validators : List Bytes
  domains : List (Bytes × Nat)
  tickets : Nat
  batches : Nat
  steps : Nat
  fault : Nat
  quorum : Nat
  soft : Nat
  hard : Nat
  threshold : Nat
  storageEpoch : Bytes
  storageRegistry : Bytes
  retentionEpoch : Bytes
  declarationLength : Nat
  declarationDigest : Bytes

def storageFields := object [
  ("retention_epoch_id",.text),("retention_policy_source",retentionSource),
  ("storage_epoch_id",.text),("storage_registry_id",.text),("threshold",.text)]

def Valid (b : Body) : Prop :=
  (∀ id ∈ [b.parent,b.schema,b.dataset,b.semantics,b.epoch,b.storageRegistry], ContentId id) ∧
  NativeConfigAdmission.Label b.round ∧
  (∀ id ∈ b.validators, NativeConfigAdmission.Label id) ∧ ordered b.validators = true ∧
  b.validators.length = 3*b.fault+1 ∧ b.quorum = 2*b.fault+1 ∧ b.soft < b.hard ∧
  ordered (b.domains.map Prod.fst) = true ∧ (b.domains.map Prod.snd).sum = b.tickets ∧
  NativeConfigAdmission.Label b.storageEpoch ∧ NativeConfigAdmission.Label b.retentionEpoch ∧
  0 < b.threshold ∧ b.threshold < 256^4 ∧ 0 < b.declarationLength ∧
  b.declarationDigest.length = 64 ∧ (∀ c ∈ b.declarationDigest, hexDigit c)
instance (b) : Decidable (Valid b) := by unfold Valid; infer_instance

def interpret (value : Value) : Option Body := do
  let policy ← selectedClosePolicy value
  let parent ← textField configuration value "parent_checkpoint_id"
  let schema ← textField configuration value "parameter_schema_id"
  let dataset ← textField configuration value "dataset_manifest_id"
  let semantics ← textField configuration value "formal_semantics_id"
  let epoch ← textField configuration value "validator_epoch_id"
  let round ← textField configuration value "round_id"
  let height ← decimalField configuration value "height"
  let view ← decimalField configuration value "view"
  let validators ← items (lookup configuration value "validator_ids") >>= texts
  let domains ← items (lookup configuration value "domain_ticket_counts") >>= domainRows
  let tickets ← numberField configuration value "ticket_count"
  let batches ← numberField configuration value "batch_budget"
  let steps ← numberField configuration value "step_budget"
  let fault ← numberField configuration value "fault_tolerance"
  let quorum ← numberField configuration value "quorum_threshold"
  let soft ← decimalField configuration value "soft_deadline_tick"
  let hard ← decimalField configuration value "hard_deadline_tick"
  let threshold ← numberField configuration value "availability_threshold"
  let ap ← lookup configuration value "availability_policy"
  let binding ← lookup availability ap "storage_binding"
  let storageEpoch ← textField storageFields binding "storage_epoch_id"
  let storageRegistry ← textField storageFields binding "storage_registry_id"
  let retentionEpoch ← textField storageFields binding "retention_epoch_id"
  let sourceThreshold ← decimalField storageFields binding "threshold"
  let source ← lookup storageFields binding "retention_policy_source"
  let originalEpoch ← textField retentionSource source "retention_epoch_id"
  let reference ← lookup retentionSource source "obligation_ref"
  let refFormat := object [("byte_length",.text),("sha256",.text)]
  let declarationLength ← decimalField refFormat reference "byte_length"
  let declarationDigest ← textField refFormat reference "sha256"
  let body := Body.mk value policy parent schema dataset semantics epoch round height view
    validators domains tickets batches steps fault quorum soft hard threshold storageEpoch
    storageRegistry retentionEpoch declarationLength declarationDigest
  if Valid body ∧ sourceThreshold = threshold ∧ originalEpoch = retentionEpoch ∧
      textField configuration value "schema_version" = some (ascii "2.0.0") ∧
      textField configuration value "type_name" = some (ascii "ROUND_CONFIG") ∧
      textField retentionSource source "schema_version" = some (ascii "1.0.0") ∧
      textField retentionSource source "type_name" = some (ascii "STORAGE_RETENTION_POLICY_SOURCE")
  then some body else none

theorem interpreted {value body} (ok : interpret value = some body) :
    body.originalValue = value ∧ selectedClosePolicy value = some body.policy ∧ Valid body := by
  unfold interpret at ok
  simp only [bind,Option.bind_eq_some_iff] at ok
  repeat (obtain ⟨_,_,ok⟩ := ok)
  split at ok <;> try contradiction
  rename_i checks
  cases Option.some.inj ok
  exact ⟨rfl,by assumption,checks.1⟩

/- Complete original bytes are retained even for fields not projected into the
public arithmetic metadata. Enrolled authority is checked independently below,
not supplied as a public success proposition. -/
def check (raw : Bytes) : Option Body := do
  let value ← decodeFrame raw
  interpret value

theorem checked {raw body} (ok : check raw = some body) :
    ∃ value, decodeFrame raw = some value ∧ encodeFrame value = some raw ∧
      interpret value = some body := by
  simp only [check,bind,Option.bind_eq_some_iff] at ok
  obtain ⟨value,hv,hi⟩ := ok
  exact ⟨value,hv,frameDecoded hv,hi⟩

theorem complete {raw value body}
    (bytes : encodeFrame value = some raw) (fields : interpret value = some body) :
    check raw = some body := by simp only [check,frameEncoded bytes,bind,Option.bind,fields]

theorem wholeSource {raw body} (ok : check raw = some body) :
    decodeFrame raw = some body.originalValue ∧ encodeFrame body.originalValue = some raw ∧
      closePolicy raw = some body.policy ∧ Valid body := by
  obtain ⟨value,parsed,encoded,fields⟩ := checked ok
  have original := interpreted fields
  exact ⟨by simpa only [original.1] using parsed,
    by simpa only [original.1] using encoded,
    by simp only [closePolicy,parsed,bind,Option.bind,original.2.1],original.2.2⟩

structure Enrollment where
  semantics : Bytes
  epoch : Bytes
  validators : List Bytes
  storageEpoch : Bytes
  storageRegistry : Bytes

def Matches (independent : Enrollment) (body : Body) : Prop :=
  body.semantics = independent.semantics ∧ body.epoch = independent.epoch ∧
  body.validators = independent.validators ∧ body.fault = 1 ∧ body.quorum = 3 ∧
  body.storageEpoch = independent.storageEpoch ∧ body.storageRegistry = independent.storageRegistry
instance (a b) : Decidable (Matches a b) := by unfold Matches; infer_instance

def checkEnrolled (independent : Enrollment) (raw : Bytes) : Option Body := do
  let body ← check raw
  if Matches independent body then some body else none

theorem enrolledSource {independent raw body}
    (ok : checkEnrolled independent raw = some body) :
    check raw = some body ∧ Matches independent body := by
  unfold checkEnrolled at ok
  cases hb : check raw with
  | none => simp [hb] at ok
  | some b =>
    simp only [hb,bind,Option.bind] at ok
    split at ok <;> try contradiction
    rename_i matchSource
    cases Option.some.inj ok
    exact ⟨rfl,matchSource⟩


/- Shared interpretation of original configuration fields under an independently
selected closed grammar. It does not dispatch from an imported version string.
The historical interpreter is definitionally unchanged; the unit generation
adds its numeric checks in ProfileConfigurationUnits. -/
def selectedClosePolicyUsing (fmt : Format) (value : Value) : Option Bytes := do
  let policy ← lookup fmt value "availability_policy"
  let selected ← text (lookup availability policy "close_policy")
  if selected = ascii "OMIT_UNAVAILABLE" ∨ selected = ascii "ABORT_ON_INCOMPLETE"
  then some selected else none

def interpretUsing (fmt : Format) (schemaVersion : Bytes) (value : Value) : Option Body := do
  let policy ← selectedClosePolicyUsing fmt value
  let parent ← textField fmt value "parent_checkpoint_id"
  let schema ← textField fmt value "parameter_schema_id"
  let dataset ← textField fmt value "dataset_manifest_id"
  let semantics ← textField fmt value "formal_semantics_id"
  let epoch ← textField fmt value "validator_epoch_id"
  let round ← textField fmt value "round_id"
  let height ← decimalField fmt value "height"
  let view ← decimalField fmt value "view"
  let validators ← items (lookup fmt value "validator_ids") >>= texts
  let domains ← items (lookup fmt value "domain_ticket_counts") >>= domainRows
  let tickets ← numberField fmt value "ticket_count"
  let batches ← numberField fmt value "batch_budget"
  let steps ← numberField fmt value "step_budget"
  let fault ← numberField fmt value "fault_tolerance"
  let quorum ← numberField fmt value "quorum_threshold"
  let soft ← decimalField fmt value "soft_deadline_tick"
  let hard ← decimalField fmt value "hard_deadline_tick"
  let threshold ← numberField fmt value "availability_threshold"
  let ap ← lookup fmt value "availability_policy"
  let binding ← lookup availability ap "storage_binding"
  let storageEpoch ← textField storageFields binding "storage_epoch_id"
  let storageRegistry ← textField storageFields binding "storage_registry_id"
  let retentionEpoch ← textField storageFields binding "retention_epoch_id"
  let sourceThreshold ← decimalField storageFields binding "threshold"
  let source ← lookup storageFields binding "retention_policy_source"
  let originalEpoch ← textField retentionSource source "retention_epoch_id"
  let reference ← lookup retentionSource source "obligation_ref"
  let refFormat := object [("byte_length",.text),("sha256",.text)]
  let declarationLength ← decimalField refFormat reference "byte_length"
  let declarationDigest ← textField refFormat reference "sha256"
  let body := Body.mk value policy parent schema dataset semantics epoch round height view
    validators domains tickets batches steps fault quorum soft hard threshold storageEpoch
    storageRegistry retentionEpoch declarationLength declarationDigest
  if Valid body ∧ sourceThreshold = threshold ∧ originalEpoch = retentionEpoch ∧
      textField fmt value "schema_version" = some schemaVersion ∧
      textField fmt value "type_name" = some (ascii "ROUND_CONFIG") ∧
      textField retentionSource source "schema_version" = some (ascii "1.0.0") ∧
      textField retentionSource source "type_name" = some (ascii "STORAGE_RETENTION_POLICY_SOURCE")
  then some body else none

theorem originalInterpreterUnchanged (value : Value) :
    interpretUsing configuration (ascii "2.0.0") value = interpret value := rfl

theorem interpretedUsing {fmt version value body}
    (ok : interpretUsing fmt version value = some body) :
    body.originalValue = value ∧ selectedClosePolicyUsing fmt value = some body.policy ∧ Valid body := by
  unfold interpretUsing at ok
  simp only [bind,Option.bind_eq_some_iff] at ok
  repeat (obtain ⟨_,_,ok⟩ := ok)
  split at ok <;> try contradiction
  rename_i checks
  cases Option.some.inj ok
  exact ⟨rfl,by assumption,checks.1⟩

end DeltaReduce.ProfileSource.Configuration
