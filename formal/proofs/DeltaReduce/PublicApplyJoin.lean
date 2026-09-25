import DeltaReduce.PublicApplyBody
import DeltaReduce.PublicParameterJoin
import DeltaReduce.PublicScalarNumbers

/-! Both complete arithmetic bodies plus original preparation and all-field footprint.
Phase/QC guards and the entire prior durable-prefix relation remain open. -/
namespace DeltaReduce.PublicApplyJoin
open NativeBinding NativeInputProjection PublicState PublicArithmeticInputs

structure Body {codec store trust anchor} {binding : Binding codec trust anchor store}
    (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust)
    (limit : ModelLimit) (mapping : IdentityMap) (expected : Value)
    (native : NativeApply binding) (candidate : Value) where
  corpus : Corpus binding
  input : Projected corpus limit
  authority : PublicAuthority.Projection input vocabulary source
  checked : PublicApplyBody.Checked authority mapping expected native
  exactBody : candidate = checked.projection.value

def loadBody {codec store trust anchor} {binding : Binding codec trust anchor store}
    (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust)
    (limit : ModelLimit) (mapping : IdentityMap) (expected : Value)
    (native : NativeApply binding) (candidate : Value) :
    Option (Body vocabulary source limit mapping expected native candidate) := do
  let corpus ← loadCorpus binding
  let input ← projectInputs corpus limit
  let authority ← PublicAuthority.project input vocabulary source
  match accepted : PublicApplyBody.check authority mapping expected native candidate with
  | none => none
  | some checked => some ⟨corpus,input,authority,checked,
      PublicApplyBody.wholeApplyWasComputed authority mapping expected native accepted⟩

def SourceBody {codec store trust anchor} {binding : Binding codec trust anchor store}
    (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust)
    (limit : ModelLimit) (mapping : IdentityMap) (expected : Value)
    {kind} (native : VoteSource binding kind) (candidate : Value) : Type :=
  match native with
  | .parameter result => PublicParameterJoin.Body vocabulary source limit result candidate
  | .apply result => Body vocabulary source limit mapping expected result candidate

def loadSourceBody {codec store trust anchor} {binding : Binding codec trust anchor store}
    (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust)
    (limit : ModelLimit) (mapping : IdentityMap) (expected : Value)
    {kind} (native : VoteSource binding kind) (candidate : Value) :
    Option (SourceBody vocabulary source limit mapping expected native candidate) :=
  match native with
  | .parameter result => PublicParameterJoin.loadBody vocabulary source limit result candidate
  | .apply result => loadBody vocabulary source limit mapping expected result candidate

structure Joined {codec trust voteTrust} (env : PublicJournal.Environment codec trust voteTrust)
    (mapping : IdentityMap) (symbols : String → Option Value) (schema : Value)
    (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust) (limit : ModelLimit) (expected : Value)
    (journal : PublicJournal.Journal) (slot : PublicJournal.Slot) (before after : PublicState.State) (actor : Value) where
  numbers : PublicScalarNumbers.VoteNumbers env mapping symbols schema journal slot before after actor
  body : SourceBody vocabulary source limit mapping expected numbers.native.resolved.expected.source numbers.effects.first.vote.body

def bindVote {codec trust voteTrust} (env : PublicJournal.Environment codec trust voteTrust)
    (mapping : IdentityMap) (symbols : String → Option Value) (schema : Value)
    (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust) (limit : ModelLimit) (expected : Value)
    (journal : PublicJournal.Journal) (slot : PublicJournal.Slot) (before after : PublicState.State) (actor : Value) :
    Option (Joined env mapping symbols schema vocabulary source limit expected journal slot before after actor) := do
  let numbers ← PublicScalarNumbers.bindVoteNumbers env mapping symbols schema journal slot before after actor
  let body ← loadSourceBody vocabulary source limit mapping expected numbers.native.resolved.expected.source numbers.effects.first.vote.body
  some ⟨numbers,body⟩

theorem joinedOriginalPreparation {codec trust voteTrust env mapping symbols schema vocabulary metadataTrust source limit expected journal slot before after actor}
    (joined : Joined (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping symbols schema
      vocabulary (metadataTrust := metadataTrust) source limit expected journal slot before after actor) :
    ∃ resolved : NativeReplay.Resolved env.native joined.numbers.native.record.data,
      ∃ prepared : NativePrepared resolved.binding voteTrust resolved.input.metadata .ready
        journal.admissionState joined.numbers.native.record.data.command,
        joined.numbers.native.record = prepared.record :=
  PublicScalarNumbers.boundNumbersHaveOriginalPreparation joined.numbers

theorem joinedCompleteAfterFootprint {codec trust voteTrust env mapping symbols schema vocabulary metadataTrust source limit expected journal slot before after actor}
    (joined : Joined (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping symbols schema
      vocabulary (metadataTrust := metadataTrust) source limit expected journal slot before after actor) :
    after.rows = (PublicVoteEffects.expected joined.numbers.effects.inputs).rows ∧
    after.read "messages" = before.read "messages" ∧ after.read "currentCheckpoint" = before.read "currentCheckpoint" :=
  PublicScalarNumbers.boundNumbersPreserveCompleteFootprint joined.numbers

theorem joinedOriginalSequence {codec trust voteTrust env mapping symbols schema vocabulary metadataTrust source limit expected journal slot before after actor}
    (joined : Joined (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping symbols schema
      vocabulary (metadataTrust := metadataTrust) source limit expected journal slot before after actor) :
    joined.numbers.effects.first.next.data.sequence = journal.slots.length + 1 ∧
    joined.numbers.native.record.sequence = slot.sequence ∧ slot.native = some joined.numbers.native.record :=
  PublicScalarNumbers.boundNumbersRetainAllVoteSequence joined.numbers

structure Executed {codec trust voteTrust} (env : PublicRecovery.Environment codec trust voteTrust)
    (mapping : IdentityMap) (symbols : String → Option Value) (schema : Value)
    (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust) (limit : ModelLimit) (expected : Value)
    (machine : PublicRecovery.Machine) (slot : PublicJournal.Slot) (before after : PublicState.State) (actor : Value)
    (stages : List String) (observation : PublicRecovery.Observation) where
  joined : Joined env.journal mapping symbols schema vocabulary source limit expected machine.journal slot before after actor
  known : PublicRecovery.classify stages ≠ some .unknown
  final : PublicRecovery.Machine
  executed : PublicRecovery.persist env.journal machine slot stages observation = some final

def executeKnown {codec trust voteTrust} (env : PublicRecovery.Environment codec trust voteTrust)
    (mapping : IdentityMap) (symbols : String → Option Value) (schema : Value)
    (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust) (limit : ModelLimit) (expected : Value)
    (machine : PublicRecovery.Machine) (slot : PublicJournal.Slot) (before after : PublicState.State) (actor : Value)
    (stages : List String) (observation : PublicRecovery.Observation) :
    Option (Executed env mapping symbols schema vocabulary source limit expected machine slot before after actor stages observation) := do
  if known : PublicRecovery.classify stages ≠ some .unknown then
    let joined ← bindVote env.journal mapping symbols schema vocabulary source limit expected machine.journal slot before after actor
    match executed : PublicRecovery.persist env.journal machine slot stages observation with
    | none => none
    | some final => some ⟨joined,known,final,executed⟩
  else none

theorem checkedBodyPersistencePreservesReachability {codec trust voteTrust env mapping symbols schema vocabulary metadataTrust source limit expected machine slot before after actor stages observation}
    (executed : Executed (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping symbols schema
      vocabulary (metadataTrust := metadataTrust) source limit expected machine slot before after actor stages observation)
    {nativeActor current} (prior : PublicReachability.Reachable env nativeActor current machine) :
    PublicReachability.Reachable env nativeActor current executed.final := .next prior (.persist executed.executed)

theorem unknownHasNoCompleteState {codec trust voteTrust env mapping symbols schema vocabulary metadataTrust source limit expected machine slot before after actor stages observation}
    (unknown : PublicRecovery.classify stages = some .unknown) :
    executeKnown (codec := codec) (trust := trust) (voteTrust := voteTrust) env mapping symbols schema
      vocabulary (metadataTrust := metadataTrust) source limit expected machine slot before after actor stages observation = none := by
  simp [executeKnown,unknown]

end DeltaReduce.PublicApplyJoin
