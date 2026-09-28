import DeltaReduce.PublicEarlyHistory
import DeltaReduce.NativeWholeReplayVectors

/-! Original ISC source plus explicitly synthetic primitive metadata. Small
public component checks are not a new native capture or configuration authority. -/
namespace DeltaReduce.PublicEarlyBodyVectors
open NativeBinding PublicState PublicEarlyBody
open NativeWholeReplayVectors (sha selected wholeOriginalVote)
open NativeMixedPolicyVectors (policyRaw)
open NativeMixedReplayVectors (initial)
set_option maxRecDepth 16384

def loaded : NativeEarlySource.Loaded sha policyRaw initial.core.state
    NativeWalVectors.entry2.command (NativeConfigReplay.facts initial NativeWalVectors.entry2) :=
  ⟨selected,wholeOriginalVote⟩

theorem originalSource : NativeSelectedVote.Source sha policyRaw initial.core.state
    NativeWalVectors.entry2.command (NativeConfigReplay.facts initial NativeWalVectors.entry2) selected :=
  NativeEarlySource.loadedOriginal loaded

theorem singletonSource : NativeEarlySource.iscMatches selected = [NativeSnapshotBaseVectors.checked] := by
  change (if NativeSnapshotBaseVectors.checkedBody.id == NativeSnapshotBaseVectors.checkedBody.id then
    [NativeSnapshotBaseVectors.checked] else []) = _
  simp

def isc : NativeEarlySource.Isc sha selected :=
  ⟨NativeSnapshotBaseVectors.checked,singletonSource,rfl,
    NativeIscAdmissionVectors.bodyRead,NativeWholeReplayVectors.bodyHash,NativeIscAdmissionVectors.inputValid⟩

theorem loadedIsc : NativeEarlySource.loadIsc sha selected = some isc :=
  NativeEarlySource.iscFromComponents singletonSource rfl isc.recomputed

theorem originalContext : NativeIscAdmission.iscContext sha selected.policy.round =
    some selected.admitted.selected.original.context := (NativeEarlySource.iscParentContext loaded isc).2

def syntheticTrust : PublicEarlyBody.Trust := ⟨fun _ _ => True,fun _ _ _ => True⟩
def names : Metadata syntheticTrust :=
  ⟨(fun k => some (match k with
    | .actor _ _ => "v1" | .height _ => "h1" | .epoch _ => "e1"
    | .config _ => "cfg1" | .ticket _ _ => "t1" | .content _ _ _ => "q1")),
    (fun _ _ => some .omitUnavailable),(by intros; trivial),(by intros; trivial)⟩
def header : Header names selected := ⟨⟨"v1",rfl⟩,⟨"h1",rfl⟩,⟨"e1",rfl⟩,⟨"cfg1",rfl⟩⟩
def entry : Entry names isc.original.body.id isc.original.body.body :=
  ⟨NativeIscAdmissionVectors.tuple0,⟨"t1",rfl⟩,⟨"q1",rfl⟩⟩
def image : IscImage isc names := ⟨header,.omitUnavailable,rfl,[entry],rfl⟩

theorem headerLoaded : loadHeader names selected = some header := rfl
theorem imageLoaded : loadIscImage isc names = some image := rfl
theorem fullOriginalTuples : image.entries.map Entry.original = isc.original.body.body.tuples :=
  iscCompleteOriginalList image

theorem iscIsNotConfig : ¬ NativeEarlySource.Config selected := by
  intro h; have kind := h.kind; contradiction

theorem imageProjected : project sha selected names = some (.isc isc image) :=
  projectIscFromComponents iscIsNotConfig loadedIsc imageLoaded

def round : Value := PublicAuthority.roundValue (.model "h1") (.model "e1")
def publicEntry : Value := PublicAuthority.record [("content",.model "q1"),("ticket",.model "t1")]
def vote : Vote := ⟨.model "v1",.text "ISC",round,
  PublicAuthority.iscValue round (.model "cfg1") .omitUnavailable (PublicAuthority.setValue [publicEntry])⟩
def models : List String := ["v1","h1","e1","cfg1","t1","q1"]
theorem completeImage : vote = iscVote image := rfl
theorem canonicalVote : canonical models (.function (voteEntries vote)) = true := by decide
theorem separatedImage : (Image.isc isc image).Separated := by change [publicEntry].Nodup; simp
theorem completeChecked : check (sha := sha) (x := selected) names models vote =
    some ⟨.isc isc image,imageProjected,completeImage,separatedImage,canonicalVote⟩ :=
  checkFromComponents _ imageProjected completeImage separatedImage canonicalVote

theorem changedActorRejects : check (sha := sha) (x := selected) names models
    {vote with actor := .model "other"} = none := changedVoteRejects imageProjected (by decide)
theorem changedContextRejects : check (sha := sha) (x := selected) names models
    {vote with context := .model "other"} = none := changedVoteRejects imageProjected (by decide)
theorem changedKindRejects : check (sha := sha) (x := selected) names models
    {vote with kind := .text "ROUND_CONFIG"} = none := changedVoteRejects imageProjected (by decide)
theorem changedBodyRejects : check (sha := sha) (x := selected) names models
    {vote with body := .model "q1"} = none := changedVoteRejects imageProjected (by decide)
theorem omittedEntryRejects : check (sha := sha) (x := selected) names models
    {vote with body := PublicAuthority.iscValue round (.model "cfg1") .omitUnavailable (.set .nil)} = none :=
  changedVoteRejects imageProjected (by decide)
theorem changedPolicyRejects : check (sha := sha) (x := selected) names models
    {vote with body := PublicAuthority.iscValue round (.model "cfg1") .abortOnIncomplete (PublicAuthority.setValue [publicEntry])} = none :=
  changedVoteRejects imageProjected (by decide)

-- CONFIG shape only: selected is the ISC fixture, not a claimed native CONFIG admission.
theorem completeConfigShape : header.configVote =
    ⟨.model "v1",.text "ROUND_CONFIG",PublicAuthority.record [("epoch",.model "e1"),
      ("height",.model "h1"),("kind",.text "ROUND_CONFIG")],.model "cfg1"⟩ := rfl
theorem canonicalConfigShape : canonical models (.function (voteEntries header.configVote)) = true := by decide

def noNames : Metadata syntheticTrust := ⟨fun _ => none,fun _ _ => none,
  (by intros; trivial),(by intros; trivial)⟩
def noPolicy : Metadata syntheticTrust := ⟨names.atom,fun _ _ => none,names.atomAuthentic,(by intros; trivial)⟩
theorem missingHeaderRejects : loadHeader noNames selected = none := rfl
theorem missingPolicyRejects : loadIscImage isc noPolicy = none := rfl
theorem missingEntryRejects : loadEntries noNames isc.original.body.id isc.original.body.body
    isc.original.body.body.tuples = none := rfl
theorem twoOriginalEntriesRetained : ∃ es, loadEntries names isc.original.body.id isc.original.body.body
    [entry.original,entry.original] = some es ∧ es.map Entry.original = [entry.original,entry.original] :=
  ⟨[entry,entry],rfl,rfl⟩
theorem collapsedPublicEntries : ¬ [entry.value,entry.value].Nodup := by simp
theorem duplicatedSetNoncanonical : canonical models (PublicAuthority.setValue [publicEntry,publicEntry]) = false := by decide
theorem originalAvailabilityKey : NameKey.content isc.original.body.id isc.original.body.body entry.original ≠
    .content isc.original.body.id isc.original.body.body {entry.original with availability := []} :=
  contentKeyRetainsAvailability (by decide)
theorem originalRootKey : NameKey.content isc.original.body.id isc.original.body.body entry.original ≠
    .content isc.original.body.id {isc.original.body.body with root := []} entry.original :=
  contentKeyRetainsRoot (by decide)

end DeltaReduce.PublicEarlyBodyVectors
