import DeltaReduce.PublicRootBody
import DeltaReduce.NativeAggregateVectors
import DeltaReduce.PublicApplyBodyVectors

/-! Original ROOT/leaf components and separate complete public body mutations.
No full raw vector/corpus/public-root execution is asserted by these cases. -/
namespace DeltaReduce.PublicRootBodyVectors
open NativeBinding NativeAggregateVectors
open PublicState PublicAuthority

theorem originalProposalHasCompleteLeafOrder :
    proposedEdge.shards.map NativeAggregateLineage.shardLeaf = proposedEdge.certificate.common.leaves :=
  NativeAggregateLineage.resolvedLeaves (NativeAggregateLineage.checkedSource proposedChecked).selected

theorem originalRootContainsFinalizedParameter :
    NativeParameterVectors.finalizedEdge ∈ proposedEdge.shards := by simp [proposedEdge]

theorem originalLeafHasNoProposedContext : NativeParameterVectors.finalizedEdge.voteContext = [] :=
  NativeFinalizedAssignment.originalContext NativeParameterVectors.finalizedChecked

theorem originalRootProposalPreimage : NativeAggregateRoot.bodyId sha proposedEdge.certificate.common =
    some proposedEdge.id := (NativeAggregateLineage.checkedSource proposedChecked).identity

theorem originalLeafCertificatePreimage :
    NativeContractSize.contentId sha NativeParameter.domain
      (NativeParameter.json NativeParameterVectors.finalizedEdge.certificate) =
      some NativeParameterVectors.finalizedEdge.id :=
  (NativeAggregateLineage.everyShard proposedChecked originalRootContainsFinalizedParameter).2.2

theorem originalLeafIsFinalized : NativeParameterVectors.finalizedEdge.id ∈ [NativeParameterVectors.qc] :=
  (NativeAggregateLineage.everyShard proposedChecked originalRootContainsFinalizedParameter).2.1.1

theorem missingCertificateRejects : NativeAggregateLineage.resolve sha certificate.common.context
    NativeIscCertificateVectors.committee [NativeParameterVectors.qc] certificate.common [] originalLeaf = none := rfl

theorem unfinalizedCertificateRejects : ¬ NativeAggregateLineage.ShardChecks certificate.common.context
    NativeIscCertificateVectors.committee [] certificate.common originalLeaf NativeParameterVectors.finalizedEdge :=
  NativeAggregateVectors.unfinalizedShard

theorem duplicateOriginalKeysReject : NativePolicyBytes.strictly NativeParameter.keyLT
    (certificate.common.keys ++ certificate.common.keys) = false := NativeAggregateVectors.duplicateKeyOrder

theorem sourceShardNameRequiresExplicitProjection : NativeVectorLayout.shardName 0 ≠
    NativeVectorLayout.text NativeParameterVectors.finalizedEdge.certificate.common.shard := by decide

def bodyFields (leaves : List PublicState.Value) : List (String × PublicState.Value) :=
  PublicApplyBody.aggregateFields PublicAuthorityVectors.apc (.model "profile1") (.model "coeff1")
    (.model "configA") PublicAuthorityVectors.ec PublicAuthorityVectors.isc (.model "parent1")
    PublicAuthorityVectors.round (.model "schema1") PublicAuthorityVectors.seed leaves

def body (leaves : List PublicState.Value) : PublicState.Value := record (bodyFields leaves)

theorem completeFieldInventory : (bodyFields PublicApplyBodyVectors.leaves).map Prod.fst =
    PublicApplyBody.aggregateFieldNames := rfl

theorem constructedBodyCanonical : canonical PublicAuthorityVectors.vocabulary.models
    (body PublicApplyBodyVectors.leaves) = true := by decide +kernel

theorem missingLeafChangesBody : body [PublicApplyBodyVectors.leaf "shard1" 1] ≠
    body PublicApplyBodyVectors.leaves := by decide +kernel

theorem changedNumberChangesBody : body [PublicApplyBodyVectors.leaf "shard1" 2,
    PublicApplyBodyVectors.leaf "shard2" (-2)] ≠ body PublicApplyBodyVectors.leaves := by decide +kernel

theorem nativeOpaqueQcIsNotPublicLeaf : body [.model "native-qc"] ≠
    body PublicApplyBodyVectors.leaves := by decide +kernel

theorem duplicatePublicLeafRejects : canonical PublicAuthorityVectors.vocabulary.models
    (body [PublicApplyBodyVectors.leaf "shard1" 1,PublicApplyBodyVectors.leaf "shard1" 1]) = false := by decide +kernel

theorem aggregateIsCanonicalSet : body PublicApplyBodyVectors.leaves =
    body PublicApplyBodyVectors.leaves.reverse := by decide +kernel

theorem authorityPreservedInsideEachLeaf : readField (PublicApplyBodyVectors.leaf "shard1" 1)
    "authority" = some PublicAuthorityVectors.authority := rfl

theorem noInventedRootAuthorityField : readField (body PublicApplyBodyVectors.leaves) "authority" = none := rfl

end DeltaReduce.PublicRootBodyVectors
