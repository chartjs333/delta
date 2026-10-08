import DeltaReduce.NativeQJson
import DeltaReduce.NativeConfigAdmission

/-! T047/T053, approved scope13. Exact R bytes and actual raw E resolution.
No configuration authority, producer-origin, public success, physical retention
or temporal interpretation is assumed or concluded here. SHA is the same named
primitive parameter used by the existing byte proofs, not a success oracle. -/
namespace DeltaReduce.RetentionSource
open NativeReceiptBytes (Bytes consume consumeAppend)
open NativeVoteBytes (ascii DecimalValid decimalValue hexDigit hexBytes)
open NativeConfigAdmission (Label)

structure Wire where
  length : Bytes
  digest : Bytes
  epoch : Bytes
  deriving DecidableEq, Repr

def start := ascii "{\"obligation_ref\":{\"byte_length\":"
def middle := ascii ",\"sha256\":"
def afterRef := ascii "},\"retention_epoch_id\":"
def finish := ascii ",\"schema_version\":\"1.0.0\",\"type_name\":\"STORAGE_RETENTION_POLICY_SOURCE\"}"
def quoted (raw : Bytes) : Bytes := [34] ++ raw ++ [34]
def encode (r : Wire) : Bytes :=
  start ++ quoted r.length ++ middle ++ quoted r.digest ++ afterRef ++ quoted r.epoch ++ finish

def Safe (raw : Bytes) : Prop :=
  ∀ b ∈ raw, 32 ≤ b.toNat ∧ b.toNat ≤ 126 ∧ b ≠ 34 ∧ b ≠ 92
instance (raw) : Decidable (Safe raw) := by unfold Safe; infer_instance

def readQuoted (raw : Bytes) : Option (Bytes × Bytes) := do
  let rest ← consume [34] raw
  let (value, rest) ← NativeQJson.scanTo 34 rest
  if Safe value then some (value, rest) else none

theorem quotedEncoded (value tail : Bytes) (safe : Safe value) :
    readQuoted (quoted value ++ tail) = some (value, tail) := by
  have noQuote : ∀ b ∈ value, b ≠ 34 := by
    intro b hb; exact (safe b hb).2.2.1
  simp only [readQuoted, quoted, List.append_assoc, consumeAppend, bind, Option.bind]
  rw [show [34] ++ tail = 34 :: tail from rfl,
    NativeQJson.scanToEncoded 34 value tail noQuote]
  simp [safe]

def read (raw : Bytes) : Option Wire := do
  let raw ← consume start raw
  let (length, raw) ← readQuoted raw
  let raw ← consume middle raw
  let (digest, raw) ← readQuoted raw
  let raw ← consume afterRef raw
  let (epoch, raw) ← readQuoted raw
  let raw ← consume finish raw
  if raw = [] then some ⟨length, digest, epoch⟩ else none

def Valid (r : Wire) : Prop :=
  DecimalValid r.length ∧ 0 < decimalValue r.length ∧
  r.digest.length = 64 ∧ (∀ b ∈ r.digest, hexDigit b) ∧ Label r.epoch
instance (r) : Decidable (Valid r) := by unfold Valid; infer_instance

theorem validSafe {r} (valid : Valid r) : Safe r.length ∧ Safe r.digest ∧ Safe r.epoch := by
  rcases valid with ⟨length, _, _, digest, epoch⟩
  constructor
  · intro b hb
    have h := length.2.2.1 b hb
    simp only [NativeVoteBytes.digit] at h
    have nq : b ≠ 34 := by intro e; subst b; simp at h
    have nb : b ≠ 92 := by intro e; subst b; simp at h
    exact ⟨by omega, by omega, nq, nb⟩
  constructor
  · intro b hb
    have h := digest b hb
    simp only [hexDigit] at h
    have nq : b ≠ 34 := by intro e; subst b; simp at h
    have nb : b ≠ 92 := by intro e; subst b; simp at h
    exact ⟨by omega, by omega, nq, nb⟩
  · intro b hb
    have h := epoch.2.2 b hb
    simp only [NativeConfigAdmission.labelByte, List.mem_cons, List.not_mem_nil, or_false] at h
    have nq : b ≠ 34 := by intro e; subst b; simp at h
    have nb : b ≠ 92 := by intro e; subst b; simp at h
    exact ⟨by omega, by omega, nq, nb⟩

theorem readEncoded (r : Wire) (valid : Valid r) : read (encode r) = some r := by
  obtain ⟨hl, hd, he⟩ := validSafe valid
  unfold read encode
  simp only [List.append_assoc, consumeAppend, bind, Option.bind]
  rw [quotedEncoded _ _ hl]
  simp only [consumeAppend]
  rw [quotedEncoded _ _ hd]
  simp only [consumeAppend]
  rw [quotedEncoded _ _ he]
  simp [consume]

def decode (raw : Bytes) : Option Wire := do
  let r ← read raw
  if Valid r ∧ encode r = raw then some r else none

theorem decoded {raw r} (ok : decode raw = some r) : Valid r ∧ encode r = raw := by
  unfold decode at ok
  cases hr : read raw with
  | none => simp [hr] at ok
  | some x =>
    simp only [hr, bind, Option.bind] at ok
    split at ok <;> try contradiction
    cases Option.some.inj ok
    assumption

theorem roundTrip (r : Wire) (valid : Valid r) : decode (encode r) = some r := by
  simp [decode, readEncoded r valid, valid]

theorem encodingInjective {a b : Wire} (ha : Valid a) (hb : Valid b)
    (same : encode a = encode b) : a = b := by
  have h := roundTrip a ha
  rw [same, roundTrip b hb] at h
  exact (Option.some.inj h).symm

def domain := ascii "deltareduce.storage-retention-policy-source.v1"

structure Resolution where
  source : Wire
  rawSource : Bytes
  declaration : Bytes
  sourceId : Bytes
  deriving DecidableEq, Repr

def resolve (sha : Bytes → Bytes) (epoch raw declaration : Bytes) : Option Resolution := do
  let r ← decode raw
  if r.epoch = epoch ∧ declaration.length = decimalValue r.length ∧
      (sha declaration).length = 32 ∧ hexBytes (sha declaration) = r.digest then
    let id ← NativeStateBytes.contentId sha domain raw
    some ⟨r, raw, declaration, id⟩
  else none

def Exact (sha : Bytes → Bytes) (epoch raw declaration : Bytes) (result : Resolution) : Prop :=
  result.rawSource = raw ∧ result.declaration = declaration ∧
  decode raw = some result.source ∧ Valid result.source ∧
  encode result.source = raw ∧ result.source.epoch = epoch ∧
  declaration.length = decimalValue result.source.length ∧
  (sha declaration).length = 32 ∧ hexBytes (sha declaration) = result.source.digest ∧
  NativeStateBytes.contentId sha domain raw = some result.sourceId

theorem resolved {sha epoch raw declaration result}
    (ok : resolve sha epoch raw declaration = some result) :
    Exact sha epoch raw declaration result := by
  unfold resolve at ok
  cases hr : decode raw with
  | none => simp [hr] at ok
  | some r =>
    simp only [hr, bind, Option.bind] at ok
    split at ok <;> try contradiction
    rename_i checks
    cases hi : NativeStateBytes.contentId sha domain raw with
    | none => simp [hi] at ok
    | some id =>
      simp only [hi] at ok
      cases Option.some.inj ok
      exact ⟨rfl, rfl, hr, (decoded hr).1, (decoded hr).2,
        checks.1, checks.2.1, checks.2.2.1, checks.2.2.2, hi⟩

theorem complete {sha epoch raw declaration r id}
    (parsed : decode raw = some r)
    (checks : r.epoch = epoch ∧ declaration.length = decimalValue r.length ∧
      (sha declaration).length = 32 ∧ hexBytes (sha declaration) = r.digest)
    (identity : NativeStateBytes.contentId sha domain raw = some id) :
    resolve sha epoch raw declaration = some ⟨r, raw, declaration, id⟩ := by
  simp only [resolve, parsed, bind, Option.bind, if_pos checks, identity]

theorem nonemptyOriginal {sha epoch raw declaration result}
    (ok : resolve sha epoch raw declaration = some result) : declaration ≠ [] := by
  have h := resolved ok
  have positive := h.2.2.2.1.2.1
  have len := h.2.2.2.2.2.2.1
  intro empty
  rw [empty] at len
  simp only [List.length_nil] at len
  omega

-- No collision-freedom axiom: two differing accepted declarations for the same
-- original R would exhibit an actual equal SHA-256 digest representation.
theorem substitutionRequiresDigestCollision {sha epoch raw a b x y}
    (left : resolve sha epoch raw a = some x) (right : resolve sha epoch raw b = some y)
    (different : a ≠ b) :
    a ≠ b ∧ a.length = b.length ∧ hexBytes (sha a) = hexBytes (sha b) := by
  have l := resolved left
  have r := resolved right
  have same : x.source = y.source := by
    have h := l.2.2.1
    rw [r.2.2.1] at h
    exact (Option.some.inj h).symm
  exact ⟨different, l.2.2.2.2.2.2.1.trans (same ▸ r.2.2.2.2.2.2.1.symm),
    l.2.2.2.2.2.2.2.2.1.trans (same ▸ r.2.2.2.2.2.2.2.2.1.symm)⟩

end DeltaReduce.RetentionSource
