import ProfileConfiguration
import SourcePolicy

/-! T047/T053: full original CONFIG/S0/P0 header association. This is a source
conjunct, not initial-state authority, collection origin or public refinement.
The descriptor check compares the entire original byte objects; it never
rewrites a legacy state or drops unprojected policy/certificate fields. -/
namespace DeltaReduce.ProfileSource.NativeHeader
open NativeReceiptBytes NativeVoteBytes
open NativePolicyCodec (Value)


def stateFormat : Configuration.Format := Configuration.object [
  ("available_ticket_count",.uint 4),("committed_ticket_count",.uint 4),
  ("config_id",.text),("durable_sequence",.text),("formal_semantics_id",.text),
  ("height",.text),("parent_checkpoint_id",.text),("phase",.text),("round_id",.text),
  ("schema_version",.text),("state_root",.text),("ticket_count",.uint 4),
  ("type_name",.text),("view",.text)]

def stateHeader : Bytes := [68,82,67,49,1,0,0,5]

def stateBytes (value : Value) : Option Bytes := do
  let payload ← Configuration.encode stateFormat value
  let raw := stateHeader ++ sizedBytes payload
  if raw.length ≤ maxEnvelope then some raw else none

def policyFormat := ISCSourceV2.successor NativePolicySchema.fmtPolicy
def snapshotFormat := ISCSourceV2.successor NativePolicySchema.fmtSnapshot

def policyBytes (value : Value) : Option Bytes := do
  let payload ← NativePolicyCodec.encode policyFormat value
  let raw := ISCSourceV2.header ++ payload
  if raw.length ≤ 4194304 then some raw else none

theorem policyNoErasure {left right raw}
    (a : policyBytes left = some raw) (b : policyBytes right = some raw) : left = right := by
  unfold policyBytes at a b
  cases ha : NativePolicyCodec.encode policyFormat left with
  | none => simp [ha] at a
  | some first =>
    cases hb : NativePolicyCodec.encode policyFormat right with
    | none => simp [hb] at b
    | some second =>
      simp only [ha,bind,Option.bind] at a
      simp only [hb,bind,Option.bind] at b
      split at a <;> try contradiction
      split at b <;> try contradiction
      have same : first = second := List.append_cancel_left
        ((Option.some.inj a).trans (Option.some.inj b).symm)
      apply NativePolicyCodec.encodingInjective ha
      simpa only [same] using hb

theorem policyEveryField {left right raw}
    (a : policyBytes left = some raw) (b : policyBytes right = some raw) (field : String) :
    NativePolicyCodec.lookup policyFormat left field =
      NativePolicyCodec.lookup policyFormat right field := by rw [policyNoErasure a b]

def ptext (fmt : NativePolicyCodec.Format) (value : Value) (key : String) : Option Bytes :=
  Configuration.text (NativePolicyCodec.lookup fmt value key)

def pnumber (value : Value) (key : String) : Option Nat :=
  Configuration.number (NativePolicyCodec.lookup policyFormat value key)

structure Coarse where
  original : Value
  semantics : Bytes
  config : Bytes
  parent : Bytes
  root : Bytes
  round : Bytes
  phase : Bytes
  height : Nat
  view : Nat
  sequence : Nat
  total : Nat
  committed : Nat
  available : Nat

def StateValid (s : Coarse) : Prop :=
  ContentId s.semantics ∧ ContentId s.config ∧ ContentId s.parent ∧ ContentId s.root ∧
  s.round ≠ [] ∧ s.phase ∈ NativeStateBytes.phases ∧
  s.available ≤ s.committed ∧ s.committed ≤ s.total
instance (s) : Decidable (StateValid s) := by unfold StateValid; infer_instance

def readCoarse (v : Value) : Option Coarse := do
  let semantics ← Configuration.textField stateFormat v "formal_semantics_id"
  let config ← Configuration.textField stateFormat v "config_id"
  let parent ← Configuration.textField stateFormat v "parent_checkpoint_id"
  let root ← Configuration.textField stateFormat v "state_root"
  let round ← Configuration.textField stateFormat v "round_id"
  let phase ← Configuration.textField stateFormat v "phase"
  let height ← Configuration.decimalField stateFormat v "height"
  let view ← Configuration.decimalField stateFormat v "view"
  let sequence ← Configuration.decimalField stateFormat v "durable_sequence"
  let total ← Configuration.numberField stateFormat v "ticket_count"
  let committed ← Configuration.numberField stateFormat v "committed_ticket_count"
  let available ← Configuration.numberField stateFormat v "available_ticket_count"
  let s := Coarse.mk v semantics config parent root round phase height view sequence
    total committed available
  if StateValid s ∧ Configuration.textField stateFormat v "schema_version" = some (ascii "1.0.0") ∧
      Configuration.textField stateFormat v "type_name" = some (ascii "ROUND_STATE") then some s else none

theorem coarseSource {v s} (ok : readCoarse v = some s) :
    s.original = v ∧ StateValid s := by
  unfold readCoarse at ok
  simp only [bind,Option.bind_eq_some_iff] at ok
  repeat (obtain ⟨_,_,ok⟩ := ok)
  split at ok <;> try contradiction
  rename_i checks
  cases Option.some.inj ok
  exact ⟨rfl,checks.1⟩

def Matches (sha : Bytes → Bytes) (configRaw stateRaw actor : Bytes)
    (c : Configuration.Body) (s : Coarse) (p : Value) : Prop :=
  NativeStateBytes.contentId sha (ascii "deltareduce:003:round-config:v1") configRaw = some s.config ∧
  s.semantics = c.semantics ∧ s.parent = c.parent ∧ s.height = c.height ∧
  s.round = c.round ∧ s.total = c.tickets ∧ actor ∈ c.validators ∧
  ptext policyFormat p "local_validator_id" = some actor ∧
  ptext policyFormat p "validator_epoch_id" = some c.epoch ∧
  (Configuration.items (NativePolicyCodec.lookup policyFormat p "validator_ids") >>= Configuration.texts) = some c.validators ∧
  ptext policyFormat p "round_id" = some c.round ∧
  ptext policyFormat p "round_config_id" = some s.config ∧
  pnumber p "soft_deadline_tick" = some c.soft ∧
  pnumber p "hard_deadline_tick" = some c.hard ∧
  ∃ snapshot, NativePolicyCodec.lookup policyFormat p "snapshot" = some snapshot ∧
    ptext snapshotFormat snapshot "parameter_schema_id" = some c.schema ∧
    ptext snapshotFormat snapshot "state_id" =
      NativeStateBytes.contentId sha NativeStateBytes.stateDomain stateRaw

-- The closed tree has at most one snapshot field. This executable form avoids
-- an unbounded search or a public-state predicate in the source checker.
def matchFields (sha : Bytes → Bytes) (configRaw stateRaw actor : Bytes)
    (c : Configuration.Body) (s : Coarse) (p : Value) : Bool :=
  decide (
    NativeStateBytes.contentId sha (ascii "deltareduce:003:round-config:v1") configRaw = some s.config ∧
    s.semantics = c.semantics ∧ s.parent = c.parent ∧ s.height = c.height ∧
    s.round = c.round ∧ s.total = c.tickets ∧ actor ∈ c.validators ∧
    ptext policyFormat p "local_validator_id" = some actor ∧
    ptext policyFormat p "validator_epoch_id" = some c.epoch ∧
    (Configuration.items (NativePolicyCodec.lookup policyFormat p "validator_ids") >>= Configuration.texts) = some c.validators ∧
    ptext policyFormat p "round_id" = some c.round ∧
    ptext policyFormat p "round_config_id" = some s.config ∧
    pnumber p "soft_deadline_tick" = some c.soft ∧
    pnumber p "hard_deadline_tick" = some c.hard) &&
  match NativePolicyCodec.lookup policyFormat p "snapshot" with
  | none => false
  | some snapshot => decide (
      ptext snapshotFormat snapshot "parameter_schema_id" = some c.schema ∧
      ptext snapshotFormat snapshot "state_id" =
        NativeStateBytes.contentId sha NativeStateBytes.stateDomain stateRaw)

theorem matchFieldsCorrect {sha configRaw stateRaw actor c s p} :
    matchFields sha configRaw stateRaw actor c s p = true ↔ Matches sha configRaw stateRaw actor c s p := by
  unfold matchFields Matches
  cases hs : NativePolicyCodec.lookup policyFormat p "snapshot" <;> simp [and_assoc]

structure Bound where
  config : Configuration.Body
  state : Coarse
  policy : Value

def check (sha : Bytes → Bytes) (enrolled : Configuration.Enrollment) (actor configRaw stateRaw policyRaw : Bytes)
    (stateValue policyValue : Value) : Option Bound := do
  let c ← Configuration.checkEnrolled enrolled configRaw
  if stateBytes stateValue = some stateRaw ∧ policyBytes policyValue = some policyRaw then
    let s ← readCoarse stateValue
    if matchFields sha configRaw stateRaw actor c s policyValue then some ⟨c,s,policyValue⟩ else none
  else none

theorem checked {sha enrolled actor configRaw stateRaw policyRaw stateValue policyValue out}
    (ok : check sha enrolled actor configRaw stateRaw policyRaw stateValue policyValue = some out) :
    Configuration.checkEnrolled enrolled configRaw = some out.config ∧
    stateBytes stateValue = some stateRaw ∧ policyBytes policyValue = some policyRaw ∧
    readCoarse stateValue = some out.state ∧ out.policy = policyValue ∧
    Matches sha configRaw stateRaw actor out.config out.state out.policy := by
  unfold check at ok
  simp only [bind,Option.bind_eq_some_iff] at ok
  obtain ⟨c,hc,ok⟩ := ok
  split at ok <;> try contradiction
  rename_i originals
  simp only [Option.bind_eq_some_iff] at ok
  obtain ⟨s,hs,ok⟩ := ok
  split at ok <;> try contradiction
  rename_i same
  cases Option.some.inj ok
  exact ⟨hc,originals.1,originals.2,hs,rfl,matchFieldsCorrect.mp same⟩

theorem complete {sha enrolled actor configRaw stateRaw policyRaw stateValue policyValue c s}
    (config : Configuration.checkEnrolled enrolled configRaw = some c)
    (stateBytesOriginal : stateBytes stateValue = some stateRaw)
    (policyBytesOriginal : policyBytes policyValue = some policyRaw)
    (state : readCoarse stateValue = some s)
    (fields : Matches sha configRaw stateRaw actor c s policyValue) :
    check sha enrolled actor configRaw stateRaw policyRaw stateValue policyValue = some ⟨c,s,policyValue⟩ := by
  simp only [check,config,bind,Option.bind,stateBytesOriginal,policyBytesOriginal,
    and_self,↓reduceIte,state,matchFieldsCorrect.mpr fields]

theorem originalConfigurationAndPolicy {sha enrolled actor configRaw stateRaw policyRaw sv pv out}
    (ok : check sha enrolled actor configRaw stateRaw policyRaw sv pv = some out) :
    Configuration.encodeFrame out.config.originalValue = some configRaw ∧
    Configuration.closePolicy configRaw = some out.config.policy ∧
    stateBytes out.state.original = some stateRaw ∧ policyBytes out.policy = some policyRaw := by
  obtain ⟨hc,hs,hp,read,same,_⟩ := checked ok
  have configuration := Configuration.wholeSource (Configuration.enrolledSource hc).1
  have original := coarseSource read
  exact ⟨configuration.2.1,configuration.2.2.1,by simpa only [original.1] using hs,
    by simpa only [same] using hp⟩

end DeltaReduce.ProfileSource.NativeHeader
