import DeltaReduce.PublicRootEnvelope
import DeltaReduce.NativeHistoryRow

/-! Historical ROOT source/envelope from an actual complete mixed-WAL replay.
This view does not expose effects, infer public readiness or prove public Next. -/
namespace DeltaReduce.PublicRootHistory
open NativeBinding NativeInputProjection PublicState PublicArithmeticInputs NativeVoteCache
section History
variable {codec store trust anchor} {binding : Binding codec trust anchor store}
    {corpus : Corpus binding} {limit : ModelLimit} {input : Projected corpus limit}
    {vocabulary : Vocabulary} {metadataTrust} {source : PublicAuthority.Metadata metadataTrust}
    (authority : PublicAuthority.Projection input vocabulary source)
    (adapter : HashAdapter codec)
    {earlyTrust planTrust} (original : PublicPlanningBody.Metadata earlyTrust planTrust)

structure Checked (policy : Bytes) (prior : NativeConfigReplay.Machine)
    (row : Row (store := store) (trust := trust) adapter)
    (config proof profile : Bytes) (permission : NativeAvailableQ.Permission)
    (inputs allInputs : List NativeAvailableQ.Input) (candidate : Vote) where
  state : row.beforeState = prior.core.state
  loaded : NativeEarlySource.Loaded adapter.sha256 policy row.beforeState row.entry.command (NativeConfigReplay.facts prior row.entry)
  root : NativeRootSource.Root loaded.original
  native : NativeRootCorpus.Checked binding loaded root config proof profile permission inputs
  envelope : PublicRootEnvelope.Checked authority native original allInputs candidate
  cached : NativeSelectedVote.Checked
  cachedId : Bytes
  ordinary : row.payload = .ordinary cached cachedId

def check (policy : Bytes) (prior : NativeConfigReplay.Machine)
    (row : Row (store := store) (trust := trust) adapter)
    (config proof profile : Bytes) (permission : NativeAvailableQ.Permission)
    (inputs allInputs : List NativeAvailableQ.Input) (candidate : Vote) :
    Option (Checked authority adapter original policy prior row config proof profile permission inputs allInputs candidate) := do
  if state : row.beforeState = prior.core.state then
    let loaded ← NativeEarlySource.load adapter.sha256 policy row.beforeState row.entry.command (NativeConfigReplay.facts prior row.entry)
    let root ← NativeRootSource.loadRoot loaded.original
    let native ← NativeRootCorpus.check binding loaded root config proof profile permission inputs
    let envelope ← PublicRootEnvelope.check authority native original allInputs candidate
    match ordinary : row.payload with
    | .arithmetic _ _ => none
    | .ordinary cached cachedId => some ⟨state,loaded,root,native,envelope,cached,cachedId,ordinary⟩
  else none

variable {policy prior row config proof profile permission inputs allInputs candidate}
    (h : Checked authority adapter original policy prior row config proof profile permission inputs allInputs candidate)

theorem originalBytes : NativeVoteBytes.encodeFrame h.loaded.original.vote.wire = row.entry.command ∧
    NativeStateBytes.encodeState h.loaded.original.state.wire = row.beforeState := NativeEarlySource.loadedBytes h.loaded

theorem originalSource : NativeSelectedVote.Source adapter.sha256 policy prior.core.state row.entry.command
    (NativeConfigReplay.facts prior row.entry) h.loaded.original := by
  rw [← h.state]; exact NativeEarlySource.loadedOriginal h.loaded

theorem capturedSelection {snap i}
    (origin : RowSource adapter policy snap prior i row) {selected id}
    (ordinary : row.payload = .ordinary selected id) : h.loaded.original = selected := by
  have old := NativeSelectedVote.fromBytesComponents (ordinaryOriginalAuthority adapter origin ordinary).1
  exact Option.some.inj (h.loaded.computed.symm.trans old)

theorem completeVote : candidate = PublicRootEnvelope.value authority h.native original h.envelope.parents ∧
    PublicState.canonical vocabulary.models (.function (voteEntries candidate)) = true :=
  ⟨h.envelope.entire,h.envelope.canonical⟩

include h in
theorem completeContext : readField candidate.body "apc" = some candidate.context :=
  PublicRootEnvelope.contextFromBody authority h.native original h.envelope

theorem nativeIdentity : h.loaded.original.admitted.selected.original.action = 6 ∧
    h.loaded.original.vote.wire.bodyHash = h.root.original.id ∧
    NativeCandidateAuthority.parentContext adapter.sha256 "deltareduce.vote-context.root.v1"
      h.root.original.certificate.common.plan = some h.loaded.original.vote.wire.context :=
  PublicRootEnvelope.nativeIdentity (loaded := h.loaded) (root := h.root)

def fromHistory {policy initial snap log index}
    (history : NativeHistoryRow.Recovered (store := store) (trust := trust) adapter policy initial snap log index)
    (config proof profile : Bytes) (permission : NativeAvailableQ.Permission)
    (inputs allInputs : List NativeAvailableQ.Input) (candidate : Vote) :=
  check authority adapter original policy history.located.prior history.located.row config proof profile permission inputs allInputs candidate

variable {initial snap log index}
    (history : NativeHistoryRow.Recovered (store := store) (trust := trust) adapter policy initial snap log index)

theorem historicalPosition : ∃ pre suffix, log = pre ++ history.located.input::suffix ∧ pre.length = index ∧
    NativeArithmeticHistory.run adapter policy snap ⟨history.core,[]⟩ pre = some history.located.prior ∧
    capture adapter policy snap history.located.prior history.located.input = some history.located.one ∧
    history.located.one.rows = [history.located.row] ∧
    RowSource adapter policy snap history.located.prior history.located.input history.located.row :=
  NativeHistoryRow.source adapter history.computed

theorem originalSequences : history.located.row.entry.sequence = index+1 ∧
    history.located.row.ordinal = history.located.prior.votes.length+1 ∧
    history.located.row.entry.sequence = history.located.row.ordinal + history.located.prior.core.requests.length :=
  NativeHistoryRow.originalSequences adapter history

theorem retainedInWholeCache : history.located.row ∈ history.cache.rows :=
  NativeHistoryRow.locatedMember adapter history

theorem historySelection
    (checked : Checked authority adapter original policy history.located.prior history.located.row
      config proof profile permission inputs allInputs candidate) : checked.loaded.original = checked.cached := by
  obtain ⟨_,_,_,_,_,_,_,origin⟩ := historicalPosition adapter history
  exact capturedSelection authority adapter original checked origin checked.ordinary

theorem cachedOriginalParents
    (checked : Checked authority adapter original policy history.located.prior history.located.row
      config proof profile permission inputs allInputs candidate) :
    (NativeVoteCache.native adapter history.located.row).parents = checked.loaded.original.admitted.selected.original.parents := by
  simp only [NativeVoteCache.native,checked.ordinary,← historySelection authority adapter original history checked]

theorem wrongPriorRejects (bad : row.beforeState ≠ prior.core.state) :
    check authority adapter original policy prior row config proof profile permission inputs allInputs candidate = none := by
  simp only [check,dif_neg bad]

end History
end DeltaReduce.PublicRootHistory
