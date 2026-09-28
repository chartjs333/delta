import DeltaReduce.PublicEarlyBody

/-! Historical original cache composition for CONFIG/ISC. This does not alter
NativeReplay, arithmetic scan flags, full public durable coverage or TLA Next. -/
namespace DeltaReduce.PublicEarlyHistory
open NativeBinding NativeVoteCache
variable {codec : Codec} {store : Store} {trust : NativeBinding.Trust} (adapter : HashAdapter codec)

structure Checked (policy : Bytes) (prior : NativeConfigReplay.Machine)
    (row : Row (store := store) (trust := trust) adapter)
    {metadataTrust} (source : PublicEarlyBody.Metadata metadataTrust) (models : List String) (candidate : PublicState.Vote) where
  state : row.beforeState = prior.core.state
  loaded : NativeEarlySource.Loaded adapter.sha256 policy row.beforeState row.entry.command (NativeConfigReplay.facts prior row.entry)
  body : PublicEarlyBody.Checked (sha := adapter.sha256) (x := loaded.original) (source := source) models candidate

def check (policy : Bytes) (prior : NativeConfigReplay.Machine)
    (row : Row (store := store) (trust := trust) adapter)
    {metadataTrust} (source : PublicEarlyBody.Metadata metadataTrust) (models : List String) (candidate : PublicState.Vote) :
    Option (Checked (store := store) (trust := trust) adapter policy prior row source models candidate) := do
  if state : row.beforeState = prior.core.state then
    let loaded ← NativeEarlySource.load adapter.sha256 policy row.beforeState row.entry.command (NativeConfigReplay.facts prior row.entry)
    let body ← PublicEarlyBody.check (sha := adapter.sha256) (x := loaded.original) source models candidate
    some ⟨state,loaded,body⟩
  else none

theorem exactNativeSource {policy prior row metadataTrust source models candidate}
    (h : Checked (store := store) (trust := trust) adapter policy prior row (metadataTrust := metadataTrust) source models candidate) :
    NativeSelectedVote.Source adapter.sha256 policy prior.core.state row.entry.command
      (NativeConfigReplay.facts prior row.entry) h.loaded.original := by
  rw [← h.state]
  exact NativeEarlySource.loadedOriginal h.loaded

theorem exactOriginalBytes {policy prior row metadataTrust source models candidate}
    (h : Checked (store := store) (trust := trust) adapter policy prior row (metadataTrust := metadataTrust) source models candidate) :
    NativeVoteBytes.encodeFrame h.loaded.original.vote.wire = row.entry.command ∧
    NativeStateBytes.encodeState h.loaded.original.state.wire = row.beforeState := NativeEarlySource.loadedBytes h.loaded

theorem originalCapturedSelection {policy snap prior input row metadataTrust source models candidate}
    (origin : RowSource (store := store) (trust := trust) adapter policy snap prior input row)
    (h : Checked (store := store) (trust := trust) adapter policy prior row (metadataTrust := metadataTrust) source models candidate)
    {selected id} (ordinary : row.payload = .ordinary selected id) : h.loaded.original = selected := by
  have old := NativeSelectedVote.fromBytesComponents (ordinaryOriginalAuthority adapter origin ordinary).1
  exact Option.some.inj (h.loaded.computed.symm.trans old)

theorem completePublicVote {policy prior row metadataTrust source models candidate}
    (h : Checked (store := store) (trust := trust) adapter policy prior row (metadataTrust := metadataTrust) source models candidate) :
    candidate = h.body.image.vote ∧ PublicState.canonical models (.function (PublicState.voteEntries candidate)) = true :=
  PublicEarlyBody.checkedWholeVote h.body

theorem historicalConfigContext {policy prior row metadataTrust source models candidate}
    (h : Checked (store := store) (trust := trust) adapter policy prior row (metadataTrust := metadataTrust) source models candidate)
    (config : NativeEarlySource.Config h.loaded.original) :
    NativeConfigAdmission.configContext adapter.sha256 h.loaded.original.state.height h.loaded.original.policy.epoch =
      some h.loaded.original.admitted.selected.original.context := NativeEarlySource.configParentContext h.loaded config

theorem historicalIscContext {policy prior row metadataTrust source models candidate}
    (h : Checked (store := store) (trust := trust) adapter policy prior row (metadataTrust := metadataTrust) source models candidate)
    (isc : NativeEarlySource.Isc adapter.sha256 h.loaded.original) :
    isc.original.body.id ∈ h.loaded.original.admitted.checked.snapshot.base.closed ∧
    NativeIscAdmission.iscContext adapter.sha256 h.loaded.original.policy.round =
      some h.loaded.original.admitted.selected.original.context := NativeEarlySource.iscParentContext h.loaded isc

theorem capturedLoads {policy snap prior input row selected id}
    (origin : RowSource (store := store) (trust := trust) adapter policy snap prior input row) (ordinary : row.payload = .ordinary selected id) :
    ∃ loaded, NativeEarlySource.load adapter.sha256 policy row.beforeState row.entry.command
      (NativeConfigReplay.facts prior row.entry) = some loaded ∧ loaded.original = selected := by
  have source := NativeSelectedVote.fromBytesComponents (ordinaryOriginalAuthority adapter origin ordinary).1
  exact ⟨⟨selected,source⟩,NativeEarlySource.loadFromComponents source,rfl⟩

/-- The historical prior comes from executed recovery, not the final current
state; each ordinary row supplies its actual full native source load. -/
theorem recoveredOrdinarySource {policy initial snap log result}
    (recovered : NativeCacheHistory.recover (store := store) (trust := trust) adapter policy initial snap log = some result)
    {row selected id} (member : row ∈ result.rows) (ordinary : row.payload = .ordinary selected id) :
    ∃ core pre input suffix prior one loaded,
      log = pre ++ input::suffix ∧
      NativeArithmeticHistory.run adapter policy snap ⟨core,[]⟩ pre = some prior ∧
      capture adapter policy snap prior input = some one ∧ RowSource (store := store) (trust := trust) adapter policy snap prior input row ∧
      NativeEarlySource.load adapter.sha256 policy row.beforeState row.entry.command
        (NativeConfigReplay.facts prior row.entry) = some loaded ∧ loaded.original = selected ∧
      row.entry.sequence = row.ordinal + prior.core.requests.length := by
  obtain ⟨core,pre,input,suffix,prior,one,parts,executed,step,origin,_,_,position⟩ :=
    NativeCacheHistory.positionMapping adapter recovered member
  obtain ⟨loaded,hl,same⟩ := capturedLoads adapter origin ordinary
  exact ⟨core,pre,input,suffix,prior,one,loaded,parts,executed,step,origin,hl,same,position⟩

theorem wrongPriorRejects {policy prior row metadataTrust source models candidate}
    (wrong : row.beforeState ≠ prior.core.state) :
    check (store := store) (trust := trust) adapter policy prior row (metadataTrust := metadataTrust) source models candidate = none := by
  simp only [check,dif_neg wrong]

end DeltaReduce.PublicEarlyHistory
