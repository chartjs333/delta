import DeltaReduce.PublicApplyJoin
import DeltaReduce.NativeVectorArithmeticVectors

/-! R2 diagnostic, not a replacement refinement theorem or a new GO gate.
The current complete-body bridge is structurally scalar-only. These statements
quantify over every metadata/alias/candidate choice, not one failed fixture.
The final example reuses the previously checked original schema partition.
-/
namespace DeltaReduce.R2DomainAudit
open NativeBinding NativeInputProjection PublicState PublicArithmeticInputs

theorem parameterBodyRequiresScalar
    {codec store trust anchor} {binding : Binding codec trust anchor store}
    {vocabulary : Vocabulary} {metadataTrust} {source : PublicAuthority.Metadata metadataTrust}
    {limit : ModelLimit} {domain shard} {native : DerivedParameter binding domain shard}
    {candidate : Value} (body : PublicParameterJoin.Body vocabulary source limit native candidate) :
    native.partition.length = 1 := body.checked.projection.math.scalar.scalar

theorem vectorParameterHasNoCompletePublicBody
    {codec store trust anchor} {binding : Binding codec trust anchor store}
    {vocabulary : Vocabulary} {metadataTrust} {source : PublicAuthority.Metadata metadataTrust}
    {limit : ModelLimit} {domain shard} {native : DerivedParameter binding domain shard}
    (vector : native.partition.length ≠ 1) (candidate : Value) :
    ¬ Nonempty (PublicParameterJoin.Body vocabulary source limit native candidate) := by
  rintro ⟨body⟩
  exact vector (parameterBodyRequiresScalar body)

theorem vectorParameterCompleteLoaderRejects
    {codec store trust anchor} {binding : Binding codec trust anchor store}
    (vocabulary : Vocabulary) {metadataTrust} (source : PublicAuthority.Metadata metadataTrust)
    (limit : ModelLimit) {domain shard} (native : DerivedParameter binding domain shard)
    (vector : native.partition.length ≠ 1) (candidate : Value) :
    PublicParameterJoin.loadBody vocabulary source limit native candidate = none := by
  cases h : PublicParameterJoin.loadBody vocabulary source limit native candidate with
  | none => rfl
  | some body => exact False.elim (vectorParameterHasNoCompletePublicBody vector candidate ⟨body⟩)

theorem applyBodyRequiresScalarPartition
    {codec store trust anchor} {binding : Binding codec trust anchor store}
    {vocabulary : Vocabulary} {metadataTrust} {source : PublicAuthority.Metadata metadataTrust}
    {limit : ModelLimit} {mapping : PublicState.IdentityMap} {expected candidate : Value}
    {native : NativeApply binding}
    (body : PublicApplyJoin.Body vocabulary source limit mapping expected native candidate)
    {shard : Shard} (member : shard ∈ native.core.conversion.certified.corpus.frame.shards) :
    shard.length = 1 := by
  have origin := NativeScalarProjection.layoutSource body.checked.projection.scalar.layoutSelected
  exact (body.checked.projection.scalar.scalarLayout.scalar shard (by rw [origin.2]; exact member)).1

theorem vectorApplyHasNoCompletePublicBody
    {codec store trust anchor} {binding : Binding codec trust anchor store}
    {vocabulary : Vocabulary} {metadataTrust} {source : PublicAuthority.Metadata metadataTrust}
    {limit : ModelLimit} {mapping : PublicState.IdentityMap} {expected candidate : Value}
    {native : NativeApply binding} {shard : Shard}
    (member : shard ∈ native.core.conversion.certified.corpus.frame.shards)
    (vector : shard.length ≠ 1) :
    ¬ Nonempty (PublicApplyJoin.Body vocabulary source limit mapping expected native candidate) := by
  rintro ⟨body⟩
  exact vector (applyBodyRequiresScalarPartition body member)

theorem signedMinimumFailsEveryCurrentResultGuard (limit : ModelLimit) :
    PublicParameterBody.resultFits limit minInput = false := by
  have bound := limit.bounded
  simp only [PublicParameterBody.resultFits, decide_eq_false_iff_not, Fits]
  dsimp [minInput, maxInput] at *
  omega

/-- A source partition already present in the candidate, not a new native run.
Its original block widths are 4,8,8,8,8. Authentication remains a named boundary.
-/
theorem originalPartitionIsOutsideCompleteBodyBridge :
    ∃ entry ∈ NativeVectorArithmeticVectors.original.plan.plan.entries, entry.count ≠ 1 := by
  have widths := NativeVectorArithmeticVectors.actualWidths
  have slots := NativeVectorArithmeticVectors.originalSlots
  have present : 4 ∈ NativeVectorArithmeticVectors.original.plan.plan.entries.map
      NativeShardPartition.Entry.count := by
    rw [← slots, List.map_map]
    change 4 ∈ NativeVectorArithmeticVectors.original.blocks.map
      (fun q => (NativeVectorContext.shape q).entry.count)
    rw [widths]
    simp
  obtain ⟨entry, member, count⟩ := List.mem_map.mp present
  exact ⟨entry, member, by omega⟩

#print axioms parameterBodyRequiresScalar
#print axioms vectorParameterHasNoCompletePublicBody
#print axioms vectorParameterCompleteLoaderRejects
#print axioms applyBodyRequiresScalarPartition
#print axioms vectorApplyHasNoCompletePublicBody
#print axioms signedMinimumFailsEveryCurrentResultGuard
#print axioms originalPartitionIsOutsideCompleteBodyBridge
end DeltaReduce.R2DomainAudit
