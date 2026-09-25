import DeltaReduce.PublicReachability

/-! Exact existing native snapshot witness bytes and first-event binding.
Public state roots are opaque authenticated snapshot fields at this layer;
neither their preimages nor the full public state transition are proved here. -/
namespace DeltaReduce.PublicSnapshot
open NativeBinding PublicJournal PublicRecovery
abbrev Bytes := NativeBinding.Bytes

structure Header where
  priorRoot : ContentId
  contract : ContentId
  sequence : Nat
  deriving DecidableEq, Repr

def jsonHash (hash : ContentId) : Option Bytes :=
  if hash.length = 32 then some (quotedBytes (idBytes hash)) else none

def jsonNat (n : Nat) : Bytes := asciiBytes (toString n)
def jsonBool (b : Bool) : Bytes := asciiBytes (if b then "true" else "false")

def jsonObject (fields : List (String × Bytes)) : Bytes :=
  [123] ++ List.intercalate [44] (fields.map (fun (key, value) => quotedBytes (asciiBytes key) ++ [58] ++ value)) ++ [125]

def action (kind : VoteKind) : Action := match kind with
  | .parameter _ _ => .parameter
  | .apply => .apply

def role (kind : VoteKind) : String := match kind with
  | .parameter _ _ => "PARAMETER"
  | .apply => "APPLY"

/-- Sorted ASCII JSON keys, exactly nativeSnapshot/nativeAnchor witness v1.
No production WAL or C ABI encoding is introduced. -/
def encode (anchor : Anchor) (metadata : VoteMetadata) (header : Header) : Option Bytes := do
  let actor ← jsonASCII metadata.actor
  let context ← jsonASCII metadata.voteContext
  let checkpoint ← jsonASCII anchor.context.parentCheckpoint
  let round ← jsonASCII anchor.context.round
  let epoch ← jsonASCII anchor.context.epoch
  let authority ← jsonHash anchor.authority.id
  let model ← jsonHash anchor.currentModelHash
  let optimizer ← jsonHash anchor.currentOptimizerHash
  let prior ← jsonHash header.priorRoot
  let contract ← jsonHash header.contract
  let parent ← jsonHash metadata.parentCertificate
  let projection ← jsonHash metadata.projection.id
  let (aggregate, aggregateLength) ← match anchor.aggregate with
    | none => some (asciiBytes "null", 0)
    | some ref => (jsonHash ref.id).map (fun bytes => (bytes, ref.length))
  if anchor.authority.kind = .authority ∧ 0 < anchor.authority.length ∧
      0 < header.sequence ∧ header.sequence ≤ 9223372036854775807 then
    let inner := jsonObject [
      ("aggregate_id", aggregate), ("aggregate_length", jsonNat aggregateLength),
      ("authority_id", authority), ("current_model_hash", model), ("current_optimizer_hash", optimizer),
      ("epoch", epoch), ("hard_deadline", jsonNat anchor.context.hardDeadline),
      ("height", jsonNat anchor.context.height), ("logical_time", jsonNat metadata.logicalTime),
      ("parent_checkpoint", checkpoint), ("recovered", jsonBool metadata.recovered),
      ("role", quotedBytes (asciiBytes (role metadata.kind))), ("round_id", round),
      ("view", jsonNat anchor.context.view)]
    some (jsonObject [
      ("action_id", quotedBytes (asciiBytes metadata.kind.action)), ("actor_id", actor), ("anchor", inner),
      ("authority", jsonObject [("id", authority), ("kind", asciiBytes "\"AUTHORITY\""),
        ("length", jsonNat anchor.authority.length)]),
      ("current_checkpoint", checkpoint), ("durable_sequence", jsonNat header.sequence),
      ("parent_certificate", parent), ("prior_state_root", prior), ("projection_id", projection),
      ("round_contract_id", contract), ("vote_context_id", context)])
  else none

def preimage (bytes : Bytes) : Bytes :=
  asciiBytes "deltareduce.native-snapshot-witness.v1" ++ [0] ++ bytes

/-- Separate producer authentication; a digest alone does not establish this. -/
structure ExportTrust where
  authentic : Anchor → VoteMetadata → Header → Bytes → Prop

structure Exported (trust : ExportTrust) where
  anchor : Anchor
  metadata : VoteMetadata
  header : Header
  bytes : Bytes
  provenance : trust.authentic anchor metadata header bytes

structure Environment (codec : Codec) (trust : Trust) (voteTrust : NativeVoteTrust)
    (exportTrust : ExportTrust) where
  recovery : PublicRecovery.Environment codec trust voteTrust
  snapshots : ContentId → Option (Exported exportTrust)
  sha256 : Bytes → ContentId

structure Loaded {codec trust voteTrust exportTrust}
    (env : Environment codec trust voteTrust exportTrust) (id : ContentId) where
  exported : Exported exportTrust
  present : env.snapshots id = some exported
  encoded : encode exported.anchor exported.metadata exported.header = some exported.bytes
  digest : env.sha256 (preimage exported.bytes) = id
  bounded : 0 < exported.bytes.length ∧ exported.bytes.length ≤ 4194304 ∧ id.length = 32

def load {codec trust voteTrust exportTrust}
    (env : Environment codec trust voteTrust exportTrust) (id : ContentId) : Option (Loaded env id) := do
  match present : env.snapshots id with
  | none => none
  | some source =>
    if checked : encode source.anchor source.metadata source.header = some source.bytes ∧
        env.sha256 (preimage source.bytes) = id ∧
        (0 < source.bytes.length ∧ source.bytes.length ≤ 4194304 ∧ id.length = 32) then
      some ⟨source, present, checked.1, checked.2.1, checked.2.2⟩
    else none

inductive Outcome where
  | accepted | finalized | fault
  deriving DecidableEq, Repr

/-- First arithmetic event fields used at this boundary. Durability observation
binds all remaining event fields separately; this is not a full event decoder. -/
structure Event where
  envelope : Envelope
  validator : Bool
  view : Nat
  logicalTime : Nat
  priorRoot : ContentId
  nextRoot : ContentId
  sequence : Option Nat
  outcome : Outcome
  snapshotId : ContentId
  command : Bytes
  deriving DecidableEq, Repr

def expectedEnvelope (anchor : Anchor) (metadata : VoteMetadata) (body : ContentId) : Envelope :=
  ⟨action metadata.kind, metadata.actor, anchor.context.round, anchor.context.height,
    anchor.context.epoch, metadata.voteContext, [metadata.parentCertificate], body⟩

def outcomeMatches (stages : List String) (event : Event) (sequence : Nat) : Prop :=
  match classify stages with
  | none => False
  | some .unknown => event.outcome = .fault ∧ event.sequence = none ∧ event.nextRoot = event.priorRoot
  | some .exposed | some .unexposed =>
    (event.outcome = .accepted ∨ event.outcome = .finalized) ∧ event.sequence = some sequence

instance (stages event sequence) : Decidable (outcomeMatches stages event sequence) := by
  unfold outcomeMatches; cases classify stages with
  | none => infer_instance
  | some cut => cases cut <;> infer_instance

def snapshotMatches {codec trust voteTrust exportTrust}
    (source : Exported exportTrust) {env : NativeReplay.Environment codec trust voteTrust} {data}
    (resolved : NativeReplay.Resolved env data) (m : Machine) (contract : ContentId)
    (finalizedParents : List ContentId) (event : Event) : Prop :=
  source.anchor = resolved.input.anchor ∧ source.metadata = resolved.input.metadata ∧
  source.header.contract = contract ∧ source.header.priorRoot = event.priorRoot ∧
  source.header.sequence = m.journal.slots.length + 1 ∧
  source.metadata.parentCertificate ∈ finalizedParents

instance {codec trust voteTrust exportTrust}
    (source : Exported exportTrust) {env : NativeReplay.Environment codec trust voteTrust} {data}
    (resolved : NativeReplay.Resolved env data) (m contract parents event) :
    Decidable (snapshotMatches source resolved m contract parents event) := by
  unfold snapshotMatches; infer_instance

def eventMatches {exportTrust} (codec : Codec) (source : Exported exportTrust)
    (slot : Slot) (record : RecoveryKernel.Record) (event : Event) : Prop :=
  slot.envelope = event.envelope ∧
  event.envelope = expectedEnvelope source.anchor source.metadata (codec.hash record.data.body) ∧
  event.command = record.data.command ∧ event.validator = true ∧
  event.view = source.anchor.context.view ∧ event.logicalTime = source.metadata.logicalTime ∧
  (∀ root ∈ [event.priorRoot, event.nextRoot], root.length = 32)

instance {exportTrust} (codec) (source : Exported exportTrust) (slot record event) :
    Decidable (eventMatches codec source slot record event) := by
  unfold eventMatches; infer_instance

structure FirstBound {codec trust voteTrust exportTrust}
    (env : Environment codec trust voteTrust exportTrust)
    (m : Machine) (contract : ContentId) (parents : List ContentId)
    (slot : Slot) (event : Event) (stages : List String) where
  loaded : Loaded env event.snapshotId
  checked : CheckedSlot env.recovery.journal m.journal slot
  arithmetic : slot.envelope.action.arithmetic = true
  record : RecoveryKernel.Record
  original : slot.native = some record
  resolved : NativeReplay.Resolved env.recovery.journal.native record.data
  contextBound : snapshotMatches loaded.exported resolved m contract parents event
  eventBound : eventMatches codec loaded.exported slot record event
  outcomeBound : outcomeMatches stages event loaded.exported.header.sequence

def bindFirst {codec trust voteTrust exportTrust}
    (env : Environment codec trust voteTrust exportTrust) (m : Machine)
    (contract : ContentId) (parents : List ContentId) (slot : Slot) (event : Event)
    (stages : List String) : Option (FirstBound env m contract parents slot event stages) := do
  let loaded ← load env event.snapshotId
  let checked ← checkSlot env.recovery.journal m.journal slot
  if arithmetic : slot.envelope.action.arithmetic = true then
    match original : slot.native with
    | none => none
    | some record =>
      let resolved ← NativeReplay.resolve env.recovery.journal.native record.data
      if bound : snapshotMatches loaded.exported resolved m contract parents event ∧
          eventMatches codec loaded.exported slot record event ∧
          outcomeMatches stages event loaded.exported.header.sequence then
        some ⟨loaded, checked, arithmetic, record, original, resolved, bound.1, bound.2.1, bound.2.2⟩
      else none
  else none

structure Executed {codec trust voteTrust exportTrust}
    (env : Environment codec trust voteTrust exportTrust) (m : Machine)
    (contract : ContentId) (parents : List ContentId) (slot : Slot) (event : Event)
    (stages : List String) (observation : Observation) where
  bound : FirstBound env m contract parents slot event stages
  final : Machine
  persisted : persist env.recovery.journal m slot stages observation = some final

def executeFirst {codec trust voteTrust exportTrust}
    (env : Environment codec trust voteTrust exportTrust) (m : Machine)
    (contract : ContentId) (parents : List ContentId) (slot : Slot) (event : Event)
    (stages : List String) (observation : Observation) :
    Option (Executed env m contract parents slot event stages observation) := do
  let bound ← bindFirst env m contract parents slot event stages
  match persisted : persist env.recovery.journal m slot stages observation with
  | none => none
  | some final => some ⟨bound, final, persisted⟩

theorem loadedCanonical {codec trust voteTrust exportTrust}
    {env : Environment codec trust voteTrust exportTrust} {id} (loaded : Loaded env id) :
    encode loaded.exported.anchor loaded.exported.metadata loaded.exported.header = some loaded.exported.bytes ∧
    env.sha256 (preimage loaded.exported.bytes) = id ∧
    exportTrust.authentic loaded.exported.anchor loaded.exported.metadata loaded.exported.header loaded.exported.bytes :=
  ⟨loaded.encoded, loaded.digest, loaded.exported.provenance⟩

theorem missingSnapshotRejected {codec trust voteTrust exportTrust}
    {env : Environment codec trust voteTrust exportTrust} {id}
    (missing : env.snapshots id = none) : load env id = none := by
  unfold load
  split
  · rfl
  · rename_i source selected
    rw [missing] at selected
    contradiction

theorem changedSnapshotBytesRejected {codec trust voteTrust exportTrust}
    {env : Environment codec trust voteTrust exportTrust} {id source}
    (present : env.snapshots id = some source)
    (changed : encode source.anchor source.metadata source.header ≠ some source.bytes) :
    load env id = none := by
  unfold load
  split
  · rfl
  · rename_i other selected
    have same := Option.some.inj (selected.symm.trans present)
    subst other
    split
    · rename_i checked
      exact False.elim (changed checked.1)
    · rfl

theorem changedSnapshotDigestRejected {codec trust voteTrust exportTrust}
    {env : Environment codec trust voteTrust exportTrust} {id source}
    (present : env.snapshots id = some source)
    (changed : env.sha256 (preimage source.bytes) ≠ id) :
    load env id = none := by
  unfold load
  split
  · rfl
  · rename_i other selected
    have same := Option.some.inj (selected.symm.trans present)
    subst other
    split
    · rename_i checked
      exact False.elim (changed checked.2.1)
    · rfl

theorem originalSnapshotAnchored {codec trust voteTrust exportTrust}
    {env : Environment codec trust voteTrust exportTrust} {m contract parents slot event stages}
    (bound : FirstBound env m contract parents slot event stages) :
    bound.loaded.exported.anchor = bound.resolved.input.anchor ∧
    bound.loaded.exported.metadata = bound.resolved.input.metadata ∧
    env.recovery.journal.native.input bound.record.data.context = some bound.resolved.input :=
  ⟨bound.contextBound.1, bound.contextBound.2.1, bound.resolved.selected⟩

theorem originalSnapshotEventBound {codec trust voteTrust exportTrust}
    {env : Environment codec trust voteTrust exportTrust} {m contract parents slot event stages}
    (bound : FirstBound env m contract parents slot event stages) :
    bound.loaded.exported.header.priorRoot = event.priorRoot ∧
    bound.loaded.exported.header.contract = contract ∧
    bound.loaded.exported.header.sequence = m.journal.slots.length + 1 ∧
    bound.loaded.exported.metadata.parentCertificate ∈ parents :=
  ⟨bound.contextBound.2.2.2.1, bound.contextBound.2.2.1,
    bound.contextBound.2.2.2.2.1, bound.contextBound.2.2.2.2.2⟩

theorem originalContextAndCommand {codec trust voteTrust exportTrust}
    {env : Environment codec trust voteTrust exportTrust} {m contract parents slot event stages}
    (bound : FirstBound env m contract parents slot event stages) :
    slot.envelope = event.envelope ∧ event.command = bound.record.data.command ∧
    event.view = bound.loaded.exported.anchor.context.view ∧
    event.logicalTime = bound.loaded.exported.metadata.logicalTime :=
  ⟨bound.eventBound.1, bound.eventBound.2.2.1, bound.eventBound.2.2.2.2.1,
    bound.eventBound.2.2.2.2.2.1⟩

theorem unknownEventCannotClaimSequence {codec trust voteTrust exportTrust}
    {env : Environment codec trust voteTrust exportTrust} {m contract parents slot event stages}
    (bound : FirstBound env m contract parents slot event stages) (cut : classify stages = some .unknown) :
    event.outcome = .fault ∧ event.sequence = none ∧ event.nextRoot = event.priorRoot := by
  simpa [outcomeMatches, cut] using bound.outcomeBound

theorem knownEventKeepsOriginalSequence {codec trust voteTrust exportTrust}
    {env : Environment codec trust voteTrust exportTrust} {m contract parents slot event stages cut}
    (bound : FirstBound env m contract parents slot event stages)
    (classified : classify stages = some cut) (known : cut ≠ .unknown) :
    event.sequence = some (m.journal.slots.length + 1) := by
  have outcome := bound.outcomeBound
  cases cut <;> simp_all [outcomeMatches]
  all_goals exact bound.contextBound.2.2.2.2.1

theorem executionPreservesReachability {codec trust voteTrust exportTrust}
    {env : Environment codec trust voteTrust exportTrust} {m contract parents slot event stages observation actor current}
    (prior : PublicReachability.Reachable env.recovery actor current m)
    (executed : Executed env m contract parents slot event stages observation) :
    PublicReachability.Reachable env.recovery actor current executed.final :=
  .next prior (.persist executed.persisted)

theorem executionReplaysOriginalJournal {codec trust voteTrust exportTrust}
    {env : Environment codec trust voteTrust exportTrust} {m contract parents slot event stages observation actor current}
    (prior : PublicReachability.Reachable env.recovery actor current m)
    (executed : Executed env m contract parents slot event stages observation) :
    PublicJournal.replay env.recovery.journal executed.final.initial executed.final.log = some executed.final.journal :=
  (PublicReachability.reachableInvariant (executionPreservesReachability prior executed)).replayed

theorem executionUnknownRetainsPrefix {codec trust voteTrust exportTrust}
    {env : Environment codec trust voteTrust exportTrust} {m contract parents slot event stages observation}
    (executed : Executed env m contract parents slot event stages observation)
    (cut : classify stages = some .unknown) :
    executed.final.journal = m.journal ∧ executed.final.log = m.log ∧
    executed.final.pending = some slot ∧ event.sequence = none := by
  have held := unknownPersistPreservesKnownPrefix cut executed.persisted
  exact ⟨held.1, held.2.1, held.2.2.2.1, (unknownEventCannotClaimSequence executed.bound cut).2.1⟩

theorem boundNativePreparation {codec trust voteTrust exportTrust}
    {env : Environment codec trust voteTrust exportTrust} {m contract parents slot event stages}
    (bound : FirstBound env m contract parents slot event stages) :
    ∃ native : NativeSlot env.recovery.journal m.journal slot,
      ∃ resolved : NativeReplay.Resolved env.recovery.journal.native native.record.data,
      ∃ prepared : NativePrepared resolved.binding voteTrust resolved.input.metadata .ready
        m.journal.admissionState native.record.data.command,
        native.record = prepared.record ∧ bound.record = prepared.record := by
  obtain ⟨native, resolved, prepared, same⟩ := checkedNativeHasPreparation bound.checked bound.arithmetic
  refine ⟨native, resolved, prepared, same, ?_⟩
  exact (Option.some.inj (bound.original.symm.trans native.projected)).trans same

end DeltaReduce.PublicSnapshot
