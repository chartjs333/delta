import DeltaReduce.PublicAuthority
import DeltaReduce.NativeGraphVectors
import DeltaReduce.PublicArithmeticInputsVectors

-- Synthetic metadata, finite identity aliases and component examples. No native
-- exporter authentication, phase/QC admission or joined recovery is claimed.
namespace DeltaReduce.PublicAuthorityVectors
open NativeBinding PublicState PublicArithmeticInputs PublicAuthority NativeGraphVectors
set_option Elab.async false
set_option maxRecDepth 16000
set_option maxHeartbeats 3000000

def commitment : Commitment := ⟨"t0000","d1",[⟨"s1",a4Ref⟩,⟨"s2",a3Ref⟩]⟩
def metadataTrust : MetadataTrust := ⟨fun _ _ => True,fun _ _ _ => True⟩
def atoms : List (AtomKey × String) := [
  (.height 1,"h1"),(.epoch "epoch-1","epoch1"),(.parent "parent1","parent1"),
  (.schema a10Ref,"schema1"),(.profile a7Ref,"profile1"),(.applyProfile a7Ref,"apply1"),
  (.config a11Ref anchor.context,"configA"),(.seed a8Ref "epoch-1","seed1"),
  (.norm a1Ref,"norm1"),(.coefficient a5Ref a0Ref,"coeff1"),(.content a8Ref commitment,"content1")]
def source : Metadata metadataTrust := {
  atom := fun key => (atoms.find? (fun x => x.1 == key)).map Prod.snd
  policy := fun ref context => if ref == a11Ref && context == anchor.context then some .omitUnavailable else none
  atomAuthentic := by intros; trivial
  policyAuthentic := by intros; trivial }
def vocabulary : Vocabulary := { PublicArithmeticInputsVectors.vocabulary with
  models := ["t1","d1","shard1","shard2","h1","epoch1","parent1","schema1","profile1","apply1",
    "configA","seed1","norm1","coeff1","content1"] }
def absent : Metadata metadataTrust := { source with atom := fun _ => none, atomAuthentic := by intros; trivial }
def noPolicy : Metadata metadataTrust := { source with policy := fun _ _ => none, policyAuthentic := by intros; trivial }

theorem originalCommitmentPayload : a8Payload = .isc ["t0000"] [commitment] := by decide +kernel
theorem originalHeaderLoads : (loadHeader fixtureBinding source).isSome = true := by decide +kernel
theorem originalHeaderConfig : ((loadHeader fixtureBinding source).map (fun h => h.config.name)) = some "configA" := by decide +kernel
theorem missingHeaderRejects : (loadHeader fixtureBinding absent).isSome = false := by decide +kernel
theorem missingPolicyRejects : (loadHeader fixtureBinding noPolicy).isSome = false := by decide +kernel
theorem changedAuthorityRejects : source.atom (.config a0Ref anchor.context) = none := by decide +kernel
theorem changedHeightRejects : source.atom (.config a11Ref {anchor.context with height := 2}) = none := by decide +kernel
theorem changedViewRejects : source.atom (.config a11Ref {anchor.context with view := 1}) = none := by decide +kernel
theorem changedDeadlineRejects : source.atom (.config a11Ref {anchor.context with hardDeadline := 99999}) = none := by decide +kernel
theorem changedParentRejects : source.atom (.config a11Ref {anchor.context with parentCheckpoint := "other"}) = none := by decide +kernel
theorem changedProfileKindRejects : source.atom (.profile {a7Ref with kind := .schema}) = none := by decide +kernel
theorem changedSchemaRejects : source.atom (.schema a7Ref) = none := by decide +kernel
theorem changedPlanRejects : source.atom (.coefficient a5Ref a7Ref) = none := by decide +kernel
theorem changedAPCRejects : source.atom (.coefficient a1Ref a0Ref) = none := by decide +kernel
theorem changedECRejects : source.atom (.norm a5Ref) = none := by decide +kernel
theorem changedISCSSeedRejects : source.atom (.seed a5Ref "epoch-1") = none := by decide +kernel
theorem changedEpochRejects : source.atom (.seed a8Ref "epoch-2") = none := by decide +kernel
theorem originalEntryLoads : (loadEntry source a8Ref vocabulary commitment).isSome = true := by decide +kernel
theorem missingTicketAliasRejects : (loadEntry source a8Ref {vocabulary with ticket := fun _ => none} commitment).isSome = false := by decide +kernel
theorem changedContentISCRootRejects : (loadEntry source a5Ref vocabulary commitment).isSome = false := by decide +kernel
theorem changedLeafRejects : (loadEntry source a8Ref vocabulary {commitment with leaves := [⟨"s1",a3Ref⟩,⟨"s2",a3Ref⟩]}).isSome = false := by decide +kernel
theorem droppedLeafRejects : (loadEntry source a8Ref vocabulary {commitment with leaves := [⟨"s1",a4Ref⟩]}).isSome = false := by decide +kernel
theorem reversedLeavesReject : (loadEntry source a8Ref vocabulary {commitment with leaves := commitment.leaves.reverse}).isSome = false := by decide +kernel
theorem changedDomainRejects : (loadEntry source a8Ref vocabulary {commitment with domain := "d2"}).isSome = false := by decide +kernel

def entry : Value := record [("content",.model "content1"),("ticket",.model "t1")]
def round : Value := roundValue (.model "h1") (.model "epoch1")
def isc : Value := iscValue round (.model "configA") .omitUnavailable (setValue [entry])
def seed : Value := seedValue isc (.model "epoch1") (.model "seed1")
def ec : Value := ecValue isc seed (setValue [.model "t1"]) (.model "norm1")
def apc : Value := apcValue isc seed ec (setValue [.model "t1"]) (.model "coeff1")
def authority : Value := record [
  ("apc",apc),("applyProfile",.model "apply1"),("ec",ec),
  ("inputs",PublicArithmeticInputsVectors.expectedValue),("isc",isc),
  ("model",vectorValue "MODEL" (.model "schema1") PublicArithmeticInputsVectors.table9),
  ("optimizer",vectorValue "OPTIMIZER" (.model "schema1") PublicArithmeticInputsVectors.table10),
  ("parent",.model "parent1"),("profile",.model "profile1"),("schema",.model "schema1")]

theorem exactEntryValue : (loadEntry source a8Ref vocabulary commitment).map Entry.value = some entry := by decide +kernel
theorem exactEntryList : (loadEntries source a8Ref vocabulary [commitment]).map Subtype.val = some [entry] := by decide +kernel
theorem noEntriesDropped : (loadEntries source a8Ref vocabulary [commitment,commitment]).map Subtype.val = some [entry,entry] := by decide +kernel
theorem duplicatesNotSilentlyRemoved : canonical vocabulary.models (setValue [entry,entry]) = false := by decide +kernel
theorem completeAuthorityCanonical : canonical vocabulary.models authority = true := by decide +kernel
theorem wrongNamespaceRejects : canonical ["t1"] authority = false := by decide +kernel
theorem entireInputRecordRetained : readField authority "inputs" = some PublicArithmeticInputsVectors.expectedValue := by rfl
theorem entireISCParentRetained : readField apc "isc" = some isc := by rfl
theorem entireECParentRetained : readField apc "ec" = some ec := by rfl
theorem bothSeedParentsMatch : readField ec "seed" = readField apc "seed" := by rfl
theorem structuredModelCoordinates : readField authority "model" = some (vectorValue "MODEL" (.model "schema1") PublicArithmeticInputsVectors.table9) := by rfl
theorem wrongParentDifferent : authority ≠ record [("parent",.model "other")] := by decide +kernel
theorem sortingDoesNotDropValues : setValue [.model "t2",.model "t1"] = setValue [.model "t1",.model "t2"] := by decide +kernel
theorem abortPolicyIsSeparate : iscValue round (.model "configA") .abortOnIncomplete (setValue [entry]) ≠ isc := by decide +kernel

end DeltaReduce.PublicAuthorityVectors
