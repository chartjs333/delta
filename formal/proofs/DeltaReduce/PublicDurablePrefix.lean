import DeltaReduce.PublicApplyJoin

/-! Fail-closed historical arithmetic correspondence and exact per-actor set
coverage. The legacy non-arithmetic slots have opaque label hashes, not encoded
certificate bodies. They deliberately have no accepting branch here. This is
not the missing full public/native recovery theorem. -/
namespace DeltaReduce.PublicDurablePrefix
open NativeBinding PublicState PublicArithmeticInputs NativeInputProjection

def nativeAction : VoteKind → PublicJournal.Action
  | .parameter _ _ => .parameter
  | .apply => .apply

def nativeEnvelope (anchor : Anchor) (metadata : VoteMetadata) (hash : ContentId) : PublicJournal.Envelope :=
  ⟨nativeAction metadata.kind,metadata.actor,anchor.context.round,anchor.context.height,
    anchor.context.epoch,metadata.voteContext,[metadata.parentCertificate],hash⟩

def identityMatches (mapping : IdentityMap) (vote : Vote) (anchor : Anchor) (metadata : VoteMetadata) : Prop :=
  mapping.actor vote.actor = some metadata.actor ∧
  vote.kind = PublicScalarNumbers.kindName metadata.kind ∧
  expectedContext vote = some vote.context ∧
  (readField vote.body "parent" >>= mapping.checkpoint) = some anchor.context.parentCheckpoint ∧
  ((readField vote.body "round" >>= fun r => readField r "height") >>= mapping.height) = some anchor.context.height ∧
  ((readField vote.body "round" >>= fun r => readField r "epoch") >>= mapping.epoch) = some anchor.context.epoch

instance (mapping vote anchor metadata) : Decidable (identityMatches mapping vote anchor metadata) := by
  unfold identityMatches; infer_instance

structure Historical {codec trust voteTrust} (env : PublicJournal.Environment codec trust voteTrust)
    (mapping : IdentityMap) (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust)
    (limit : ModelLimit) (expected : Value) (slot : PublicJournal.Slot) (vote : Vote) where
  supported : slot.envelope.action.arithmetic = true
  record : RecoveryKernel.Record
  stored : slot.native = some record
  resolved : NativeReplay.Resolved env.native record.data
  envelope : slot.envelope = nativeEnvelope resolved.input.anchor resolved.input.metadata (codec.hash resolved.expected.body)
  canonicalEnvelope : slot.envelope.encode = some slot.bytes
  bytes : slot.bytes = resolved.expected.envelope
  key : slot.key = record.data.context
  encodedKey : slot.envelope.key = some slot.key
  sequence : record.sequence = slot.sequence
  effect : record.effect = resolved.expected.effect
  receipt : encodeDiagnosticReceipt codec record.data.command slot.bytes record.effect slot.sequence = some record.receipt
  identity : identityMatches mapping vote resolved.input.anchor resolved.input.metadata
  body : PublicApplyJoin.SourceBody vocabulary source limit mapping expected resolved.expected.source vote.body

/-- Resolve the original record and original metadata, without rechecking it
against the current checkpoint/time. Reachability separately supplies original
admission; successful historical decoding alone cannot authorize a first vote. -/
def checkHistorical {codec trust voteTrust} (env : PublicJournal.Environment codec trust voteTrust)
    (mapping : IdentityMap) (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust)
    (limit : ModelLimit) (expected : Value) (slot : PublicJournal.Slot) (vote : Vote) :
    Option (Historical env mapping vocabulary source limit expected slot vote) := do
  if supported : slot.envelope.action.arithmetic = true then
    match stored : slot.native with
    | none => none
    | some record =>
      let resolved ← NativeReplay.resolve env.native record.data
      if checks : slot.envelope = nativeEnvelope resolved.input.anchor resolved.input.metadata (codec.hash resolved.expected.body) ∧
          slot.envelope.encode = some slot.bytes ∧ slot.bytes = resolved.expected.envelope ∧
          slot.key = record.data.context ∧ slot.envelope.key = some slot.key ∧
          record.sequence = slot.sequence ∧ record.effect = resolved.expected.effect ∧
          encodeDiagnosticReceipt codec record.data.command slot.bytes record.effect slot.sequence = some record.receipt ∧
          identityMatches mapping vote resolved.input.anchor resolved.input.metadata then
        let body ← PublicApplyJoin.loadSourceBody vocabulary source limit mapping expected resolved.expected.source vote.body
        some ⟨supported,record,stored,resolved,checks.1,checks.2.1,checks.2.2.1,checks.2.2.2.1,
          checks.2.2.2.2.1,checks.2.2.2.2.2.1,checks.2.2.2.2.2.2.1,checks.2.2.2.2.2.2.2.1,
          checks.2.2.2.2.2.2.2.2,body⟩
      else none
  else none

theorem unsupportedCannotBorrowAuthorization {codec trust voteTrust env mapping vocabulary metadataTrust source limit expected slot vote}
    (unsupported : slot.envelope.action.arithmetic = false) :
    checkHistorical (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping vocabulary
      (metadataTrust := metadataTrust) source limit expected slot vote = none := by
  simp [checkHistorical,unsupported]

theorem historicalExactRecord {codec trust voteTrust env mapping vocabulary metadataTrust source limit expected slot vote}
    (h : Historical (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping vocabulary
      (metadataTrust := metadataTrust) source limit expected slot vote) :
    slot.native = some h.record ∧ h.record.sequence = slot.sequence ∧
    h.record.effect = h.resolved.expected.effect ∧ slot.bytes = h.resolved.expected.envelope :=
  ⟨h.stored,h.sequence,h.effect,h.bytes⟩

theorem historicalActorContextAndParent {codec trust voteTrust env mapping vocabulary metadataTrust source limit expected slot vote}
    (h : Historical (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping vocabulary
      (metadataTrust := metadataTrust) source limit expected slot vote) :
    mapping.actor vote.actor = some h.resolved.input.metadata.actor ∧
    expectedContext vote = some vote.context ∧
    (readField vote.body "parent" >>= mapping.checkpoint) = some h.resolved.input.anchor.context.parentCheckpoint :=
  ⟨h.identity.1,h.identity.2.2.1,h.identity.2.2.2.1⟩

inductive Pairs {codec trust voteTrust} (env : PublicJournal.Environment codec trust voteTrust)
    (mapping : IdentityMap) (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust)
    (limit : ModelLimit) (expected : Value) : Nat → List PublicJournal.Slot → List Vote → Type where
  | nil (next : Nat) : Pairs env mapping vocabulary source limit expected next [] []
  | cons {next slot slots vote votes} (sequence : slot.sequence = next)
      (head : Historical env mapping vocabulary source limit expected slot vote)
      (tail : Pairs env mapping vocabulary source limit expected (next + 1) slots votes) :
      Pairs env mapping vocabulary source limit expected next (slot :: slots) (vote :: votes)

/-- The ordered public list is untrusted matching evidence, never an authority
mapping. Every body is rederived; exact permutation against the state is checked
below. Public sets have no chronological order to reuse as journal order. -/
def checkPairs {codec trust voteTrust} (env : PublicJournal.Environment codec trust voteTrust)
    (mapping : IdentityMap) (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust)
    (limit : ModelLimit) (expected : Value) : (next : Nat) → (slots : List PublicJournal.Slot) → (votes : List Vote) →
    Option (Pairs env mapping vocabulary source limit expected next slots votes)
  | next, [], [] => some (.nil next)
  | next, slot :: slots, vote :: votes => do
      if sequence : slot.sequence = next then
        let head ← checkHistorical env mapping vocabulary source limit expected slot vote
        let tail ← checkPairs env mapping vocabulary source limit expected (next + 1) slots votes
        some (.cons sequence head tail)
      else none
  | _,_,_ => none

theorem pairsLength {codec trust voteTrust env mapping vocabulary metadataTrust source limit expected next slots votes}
    (p : Pairs (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping vocabulary
      (metadataTrust := metadataTrust) source limit expected next slots votes) : slots.length = votes.length := by
  induction p with
  | nil => rfl
  | cons _ _ _ ih => simpa using congrArg Nat.succ ih

theorem wrongSequencePairsRejected {codec trust voteTrust env mapping vocabulary metadataTrust source limit expected next slot slots vote votes}
    (wrong : slot.sequence ≠ next) :
    checkPairs (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping vocabulary
      (metadataTrust := metadataTrust) source limit expected next (slot :: slots) (vote :: votes) = none := by
  simp only [checkPairs,dif_neg wrong]

theorem pairsOriginalSequence {codec trust voteTrust env mapping vocabulary metadataTrust source limit expected next slots votes}
    (p : Pairs (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping vocabulary
      (metadataTrust := metadataTrust) source limit expected next slots votes) (i : Nat) {slot}
    (indexed : slots[i]? = some slot) : slot.sequence = next + i := by
  induction p generalizing i with
  | nil => simp at indexed
  | cons sequence head tail ih =>
      cases i with
      | zero => cases Option.some.inj indexed; simpa using sequence
      | succ i => simpa [Nat.add_assoc,Nat.add_comm,Nat.add_left_comm] using ih i indexed

theorem pairsEverySlot {codec trust voteTrust env mapping vocabulary metadataTrust source limit expected next slots votes}
    (p : Pairs (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping vocabulary
      (metadataTrust := metadataTrust) source limit expected next slots votes) {slot} (member : slot ∈ slots) :
    ∃ vote ∈ votes, Nonempty (Historical env mapping vocabulary source limit expected slot vote) := by
  induction p with
  | nil => simp at member
  | cons sequence head tail ih =>
      rcases List.mem_cons.mp member with same | rest
      · subst slot; exact ⟨_,List.mem_cons_self,⟨head⟩⟩
      · obtain ⟨v,hv,h⟩ := ih rest
        exact ⟨v,List.mem_cons_of_mem _ hv,h⟩

theorem pairsEveryVote {codec trust voteTrust env mapping vocabulary metadataTrust source limit expected next slots votes}
    (p : Pairs (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping vocabulary
      (metadataTrust := metadataTrust) source limit expected next slots votes) {vote} (member : vote ∈ votes) :
    ∃ slot ∈ slots, Nonempty (Historical env mapping vocabulary source limit expected slot vote) := by
  induction p with
  | nil => simp at member
  | cons sequence head tail ih =>
      rcases List.mem_cons.mp member with same | rest
      · subst vote; exact ⟨_,List.mem_cons_self,⟨head⟩⟩
      · obtain ⟨s,hs,h⟩ := ih rest
        exact ⟨s,List.mem_cons_of_mem _ hs,h⟩

def alignment (actor : Value) (frame : Frame) (journal : PublicJournal.Journal) (ordered : List Vote) : Prop :=
  (actorVotes actor frame).Perm ordered ∧ ordered.Nodup ∧ frame.sequence = journal.slots.length

instance (actor frame journal ordered) : Decidable (alignment actor frame journal ordered) := by
  unfold alignment; infer_instance

structure Prefix {codec trust voteTrust} (env : PublicJournal.Environment codec trust voteTrust)
    (mapping : IdentityMap) (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust)
    (limit : ModelLimit) (expected : Value) (journal : PublicJournal.Journal) (frame : Frame)
    (actor : Value) (ordered : List Vote) where
  actorBound : mapping.actor actor = some journal.actor
  setBound : alignment actor frame journal ordered
  pairs : Pairs env mapping vocabulary source limit expected 1 journal.slots ordered

def checkPrefix {codec trust voteTrust} (env : PublicJournal.Environment codec trust voteTrust)
    (mapping : IdentityMap) (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust)
    (limit : ModelLimit) (expected : Value) (journal : PublicJournal.Journal) (frame : Frame)
    (actor : Value) (ordered : List Vote) : Option (Prefix env mapping vocabulary source limit expected journal frame actor ordered) := do
  if h : mapping.actor actor = some journal.actor ∧ alignment actor frame journal ordered then
    let pairs ← checkPairs env mapping vocabulary source limit expected 1 journal.slots ordered
    some ⟨h.1,h.2,pairs⟩
  else none

theorem prefixNoMissingVote {codec trust voteTrust env mapping vocabulary metadataTrust source limit expected journal frame actor ordered}
    (p : Prefix (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping vocabulary
      (metadataTrust := metadataTrust) source limit expected journal frame actor ordered) {vote}
    (member : vote ∈ actorVotes actor frame) :
    ∃ slot ∈ journal.slots, Nonempty (Historical env mapping vocabulary source limit expected slot vote) :=
  pairsEveryVote p.pairs (p.setBound.1.mem_iff.mp member)

theorem prefixNoExtraRecord {codec trust voteTrust env mapping vocabulary metadataTrust source limit expected journal frame actor ordered}
    (p : Prefix (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping vocabulary
      (metadataTrust := metadataTrust) source limit expected journal frame actor ordered) {slot}
    (member : slot ∈ journal.slots) :
    ∃ vote ∈ actorVotes actor frame, Nonempty (Historical env mapping vocabulary source limit expected slot vote) := by
  obtain ⟨v,hv,h⟩ := pairsEverySlot p.pairs member
  exact ⟨v,p.setBound.1.mem_iff.mpr hv,h⟩

theorem prefixNoDuplicates {codec trust voteTrust env mapping vocabulary metadataTrust source limit expected journal frame actor ordered}
    (p : Prefix (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping vocabulary
      (metadataTrust := metadataTrust) source limit expected journal frame actor ordered) :
    (actorVotes actor frame).Nodup := p.setBound.1.nodup_iff.mpr p.setBound.2.1

theorem opaqueSlotBlocksCompletePrefix {codec trust voteTrust env mapping vocabulary metadataTrust source limit expected journal frame actor ordered slot}
    (member : slot ∈ journal.slots) (unsupported : slot.envelope.action.arithmetic = false) :
    checkPrefix (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping vocabulary
      (metadataTrust := metadataTrust) source limit expected journal frame actor ordered = none := by
  cases result : checkPrefix env mapping vocabulary source limit expected journal frame actor ordered with
  | none => rfl
  | some p =>
      obtain ⟨v,_,⟨h⟩⟩ := prefixNoExtraRecord p member
      have accepted := h.supported
      rw [unsupported] at accepted
      contradiction

theorem reachablePrefixHasOriginalPreparation {codec trust voteTrust env mapping vocabulary metadataTrust source limit expected machine frame actor ordered nativeActor current vote}
    (reachable : PublicReachability.Reachable (codec := codec) (trust := trust) (voteTrust := voteTrust) env nativeActor current machine)
    (p : Prefix env.journal mapping vocabulary (metadataTrust := metadataTrust) source limit expected machine.journal frame actor ordered)
    (member : vote ∈ actorVotes actor frame) :
    ∃ slot ∈ machine.journal.slots, (∃ before, Nonempty (PublicJournal.CheckedSlot env.journal before slot)) ∧
      Nonempty (Historical env.journal mapping vocabulary source limit expected slot vote) := by
  obtain ⟨slot,hs,h⟩ := prefixNoMissingVote p member
  exact ⟨slot,hs,PublicReachability.reachableSlotProvenance reachable hs,h⟩

structure Executed {codec trust voteTrust} (env : PublicRecovery.Environment codec trust voteTrust)
    (mapping : IdentityMap) (symbols : String → Option Value) (schema : Value)
    (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust)
    (limit : ModelLimit) (expected : Value) (machine : PublicRecovery.Machine) (slot : PublicJournal.Slot)
    (before after : PublicState.State) (actor : Value) (ordered : List Vote)
    (stages : List String) (observation : PublicRecovery.Observation) where
  joined : PublicApplyJoin.Joined env.journal mapping symbols schema vocabulary source limit expected machine.journal slot before after actor
  history : Prefix env.journal mapping vocabulary source limit expected machine.journal joined.numbers.effects.first.prior.data actor ordered
  known : PublicRecovery.classify stages ≠ some .unknown
  final : PublicRecovery.Machine
  persisted : PublicRecovery.persist env.journal machine slot stages observation = some final

/-- No persistence call is reached until the entire actor prefix matches. The
present partial body vocabulary consequently rejects legacy mixed prefixes. -/
def executeKnown {codec trust voteTrust} (env : PublicRecovery.Environment codec trust voteTrust)
    (mapping : IdentityMap) (symbols : String → Option Value) (schema : Value)
    (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust)
    (limit : ModelLimit) (expected : Value) (machine : PublicRecovery.Machine) (slot : PublicJournal.Slot)
    (before after : PublicState.State) (actor : Value) (ordered : List Vote)
    (stages : List String) (observation : PublicRecovery.Observation) :
    Option (Executed env mapping symbols schema vocabulary source limit expected machine slot before after actor ordered stages observation) := do
  if known : PublicRecovery.classify stages ≠ some .unknown then
    let joined ← PublicApplyJoin.bindVote env.journal mapping symbols schema vocabulary source limit expected machine.journal slot before after actor
    let history ← checkPrefix env.journal mapping vocabulary source limit expected machine.journal joined.numbers.effects.first.prior.data actor ordered
    match persisted : PublicRecovery.persist env.journal machine slot stages observation with
    | none => none
    | some final => some ⟨joined,history,known,final,persisted⟩
  else none

theorem executedPreservesReachability {codec trust voteTrust env mapping symbols schema vocabulary metadataTrust source limit expected machine slot before after actor ordered stages observation nativeActor current}
    (executed : Executed (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping symbols schema vocabulary
      (metadataTrust := metadataTrust) source limit expected machine slot before after actor ordered stages observation)
    (reachable : PublicReachability.Reachable env nativeActor current machine) :
    PublicReachability.Reachable env nativeActor current executed.final := .next reachable (.persist executed.persisted)

theorem executedMatchesEveryPreviousPublicVote {codec trust voteTrust env mapping symbols schema vocabulary metadataTrust source limit expected machine slot before after actor ordered stages observation}
    (executed : Executed (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping symbols schema vocabulary
      (metadataTrust := metadataTrust) source limit expected machine slot before after actor ordered stages observation)
    {vote} (member : vote ∈ actorVotes actor executed.joined.numbers.effects.first.prior.data) :
    ∃ original ∈ machine.journal.slots,
      Nonempty (Historical env.journal mapping vocabulary source limit expected original vote) :=
  prefixNoMissingVote executed.history member

theorem unknownCannotSupplyCompletePrefix {codec trust voteTrust env mapping symbols schema vocabulary metadataTrust source limit expected machine slot before after actor ordered stages observation}
    (unknown : PublicRecovery.classify stages = some .unknown) :
    executeKnown (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping symbols schema vocabulary
      (metadataTrust := metadataTrust) source limit expected machine slot before after actor ordered stages observation = none := by
  simp [executeKnown,unknown]

end DeltaReduce.PublicDurablePrefix
