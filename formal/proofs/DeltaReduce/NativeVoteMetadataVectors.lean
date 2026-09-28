import DeltaReduce.NativeVoteMetadata
import DeltaReduce.NativeArithmeticVoteVectors

/-! Original wire/parent components and separately synthetic readiness cases.
No complete native source graph, metadata trust instance or native write. -/
namespace DeltaReduce.NativeVoteMetadataVectors
open NativeBinding NativeVoteMetadata
open NativeVoteCodecVectors (vote5 vote7)
open NativeSelectedVoteVectors (entry5 entry7 live)
open NativeCandidateAuthorityVectors (policy)
open NativeVoteBytes (ascii)
set_option maxRecDepth 4096

def parameterFields : Fields := ⟨"validator-1","PARAMETER:domain-a:shard-a",
  (NativeAggregateMerkle.digestBytes entry5.parents.plan).getD []⟩
def applyFields : Fields := ⟨"validator-1",NativeVectorLayout.text vote7.wire.context,
  (NativeAggregateMerkle.digestBytes entry7.parents.root).getD []⟩

theorem parameterOriginalFields : fields vote5.wire.validator vote5.wire.context entry5.parents.plan =
    some parameterFields := by decide
theorem applyOriginalFields : fields vote7.wire.validator vote7.wire.context entry7.parents.root =
    some applyFields := by decide
theorem originalParameterParent : idBytes parameterFields.parent = entry5.parents.plan :=
  (fieldsRetained parameterOriginalFields).2.2.2.2
theorem originalApplyParent : idBytes applyFields.parent = entry7.parents.root :=
  (fieldsRetained applyOriginalFields).2.2.2.2
theorem rawDigestNotText : parameterFields.parent.length = 32 ∧ entry5.parents.plan.length = 71 := by decide
theorem differentParents : parameterFields.parent ≠ applyFields.parent := by decide
theorem wrongDigestTag : readDigest (ascii "sha257:" ++ List.replicate 64 48) = none := by decide
theorem shortDigest : readDigest (ascii "sha256:" ++ List.replicate 63 48) = none := by decide
theorem upperDigest : readDigest (ascii "sha256:" ++ List.replicate 64 65) = none := by decide
theorem rawDigestRejected : readDigest parameterFields.parent = none := by decide
theorem unicodeRejected : readText [195,169] = none := by decide
theorem asciiEscapedRetained : readText [34,92,10] = some "\"\\\n" := by decide

def projection : Ref := ⟨List.replicate 32 0,.apc,0⟩
def liveMetadata := metadata (.parameter "domain-a" "shard-a") projection policy live vote5 parameterFields
theorem liveFlags : liveMetadata.recovered = true ∧ liveMetadata.validator = true := by decide
theorem exactTime : liveMetadata.logicalTime = live.tick := rfl
theorem unreadyFlag : (metadata .apply projection policy {live with ready := false} vote7 applyFields).recovered = false := rfl
theorem recoveryOverridesReady : (metadata .apply projection policy {live with recovery := true} vote7 applyFields).recovered = false := rfl
theorem invalidationOverridesReady : (metadata .apply projection policy {live with invalidated := true} vote7 applyFields).recovered = false := rfl
theorem absentCommittee : (metadata .apply projection {policy with validators := []} live vote7 applyFields).validator = false := by decide
theorem wrongLocalActor : (metadata .apply projection {policy with localValidator := ascii "other"} live vote7 applyFields).validator = false := by decide
theorem originalRecoveryNotComplete : completed (NativeArithmeticPrefix.facts NativeArithmeticVoteVectors.actualPrefix) = false := rfl
theorem metadataNoGlobalSequence : (metadata .apply projection policy live {vote7 with sequence := 3} applyFields) =
    metadata .apply projection policy live {vote7 with sequence := 2} applyFields := rfl
theorem metadataNoSignature : (metadata .apply projection policy live
    {vote7 with wire := {vote7.wire with signature := []}} applyFields) =
    metadata .apply projection policy live vote7 applyFields := rfl
theorem metadataNoView : (metadata .apply projection policy live {vote7 with view := 9} applyFields) =
    metadata .apply projection policy live vote7 applyFields := rfl
theorem entireFrameRetainsSignature : (NativeVoteBytes.fields vote7.wire)[8]? =
    some (ascii "signature_id",vote7.wire.signature) := rfl
theorem entireFrameRetainsSemantics : (NativeVoteBytes.fields vote5.wire)[3]? =
    some (ascii "formal_semantics_id",NativeVoteBytes.nativeSemantics) := rfl

end DeltaReduce.NativeVoteMetadataVectors
