import DeltaReduce.PublicPlanningBody

/-! Historical EC/APC source/body composition. Full public durable coverage,
all-actor positions, live readiness and public/native Next remain separate. -/
namespace DeltaReduce.PublicPlanningHistory
open NativeBinding NativeVoteCache
variable {codec : Codec} {store : Store} {trust : NativeBinding.Trust} (adapter : HashAdapter codec)

structure Checked (policy : Bytes) (prior : NativeConfigReplay.Machine)
    (row : Row (store := store) (trust := trust) adapter)
    {earlyTrust metadataTrust} (source : PublicPlanningBody.Metadata earlyTrust metadataTrust)
    (models : List String) (candidate : PublicState.Vote) where
  state : row.beforeState = prior.core.state
  loaded : NativeEarlySource.Loaded adapter.sha256 policy row.beforeState row.entry.command (NativeConfigReplay.facts prior row.entry)
  body : PublicPlanningBody.Checked loaded source models candidate

def check (policy : Bytes) (prior : NativeConfigReplay.Machine)
    (row : Row (store := store) (trust := trust) adapter)
    {earlyTrust metadataTrust} (source : PublicPlanningBody.Metadata earlyTrust metadataTrust)
    (models : List String) (candidate : PublicState.Vote) :
    Option (Checked (store := store) (trust := trust) adapter policy prior row source models candidate) := do
  if state : row.beforeState = prior.core.state then
    let loaded ← NativeEarlySource.load adapter.sha256 policy row.beforeState row.entry.command (NativeConfigReplay.facts prior row.entry)
    let body ← PublicPlanningBody.check loaded source models candidate
    some ⟨state,loaded,body⟩
  else none

theorem exactNativeSource {policy prior row earlyTrust metadataTrust source models candidate}
    (h : Checked (store := store) (trust := trust) adapter policy prior row
      (earlyTrust := earlyTrust) (metadataTrust := metadataTrust) source models candidate) :
    NativeSelectedVote.Source adapter.sha256 policy prior.core.state row.entry.command
      (NativeConfigReplay.facts prior row.entry) h.loaded.original := by
  rw [← h.state]; exact NativeEarlySource.loadedOriginal h.loaded
theorem exactOriginalBytes {policy prior row earlyTrust metadataTrust source models candidate}
    (h : Checked (store := store) (trust := trust) adapter policy prior row
      (earlyTrust := earlyTrust) (metadataTrust := metadataTrust) source models candidate) :
    NativeVoteBytes.encodeFrame h.loaded.original.vote.wire = row.entry.command ∧
    NativeStateBytes.encodeState h.loaded.original.state.wire = row.beforeState := NativeEarlySource.loadedBytes h.loaded
theorem originalCapturedSelection {policy snap prior input row earlyTrust metadataTrust source models candidate}
    (origin : RowSource (store := store) (trust := trust) adapter policy snap prior input row)
    (h : Checked (store := store) (trust := trust) adapter policy prior row
      (earlyTrust := earlyTrust) (metadataTrust := metadataTrust) source models candidate)
    {selected id} (ordinary : row.payload = .ordinary selected id) : h.loaded.original = selected := by
  have old := NativeSelectedVote.fromBytesComponents (ordinaryOriginalAuthority adapter origin ordinary).1
  exact Option.some.inj (h.loaded.computed.symm.trans old)
theorem completePublicVote {policy prior row earlyTrust metadataTrust source models candidate}
    (h : Checked (store := store) (trust := trust) adapter policy prior row
      (earlyTrust := earlyTrust) (metadataTrust := metadataTrust) source models candidate) :
    candidate = h.body.image.vote ∧ PublicState.canonical models (.function (PublicState.voteEntries candidate)) = true :=
  PublicPlanningBody.checkedWholeVote h.body
theorem wrongPriorRejects {policy prior row earlyTrust metadataTrust source models candidate}
    (wrong : row.beforeState ≠ prior.core.state) :
    check (store := store) (trust := trust) adapter policy prior row
      (earlyTrust := earlyTrust) (metadataTrust := metadataTrust) source models candidate = none := by
  simp only [check,dif_neg wrong]

end DeltaReduce.PublicPlanningHistory
