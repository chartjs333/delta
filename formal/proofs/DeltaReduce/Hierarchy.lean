import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Data.Fintype.BigOperators

/-! PO-H1/PO-H2 exact partition and indexed hierarchical reduction. -/

namespace DeltaReduce

open scoped BigOperators

theorem exactRegionAssignment {Ticket Region : Type*}
    (regionOf : Ticket → Region) :
    ∀ ticket, ∃! region, regionOf ticket = region := by
  intro ticket
  refine ⟨regionOf ticket, rfl, ?_⟩
  intro region hregion
  exact hregion.symm

theorem exactDomainShardPartition {Ticket Domain Shard Region : Type*}
    (regionOf : Ticket → Region) (domainOf : Ticket → Domain)
    (shardOf : Ticket → Shard) :
    ∀ ticket, ∃! metadata : Region × Domain × Shard,
      metadata = (regionOf ticket, domainOf ticket, shardOf ticket) := by
  intro ticket
  refine ⟨(regionOf ticket, domainOf ticket, shardOf ticket), rfl, ?_⟩
  intro metadata hmetadata
  exact hmetadata

theorem hierarchicalEqualsFlat
    {Ticket Region Domain Shard : Type*}
    [Fintype Ticket] [Fintype Region] [DecidableEq Region]
    (regionOf : Ticket → Region)
    (contribution : Ticket → Domain → Shard → ℤ) (domain : Domain) (shard : Shard) :
    (∑ region : Region, ∑ ticket : Ticket,
        if regionOf ticket = region then contribution ticket domain shard else 0) =
      ∑ ticket : Ticket, contribution ticket domain shard := by
  rw [Finset.sum_comm]
  apply Fintype.sum_congr
  intro ticket
  simp

theorem hierarchicalTicketCount
    {Ticket Region : Type*}
    [Fintype Ticket] [Fintype Region] [DecidableEq Region]
    (regionOf : Ticket → Region) :
    (∑ region : Region, ∑ ticket : Ticket,
        if regionOf ticket = region then 1 else 0) =
      ∑ _ticket : Ticket, 1 := by
  rw [Finset.sum_comm]
  simp

theorem hierarchicalCoefficientMetadata
    {Ticket Region : Type*}
    [Fintype Ticket] [Fintype Region] [DecidableEq Region]
    (regionOf : Ticket → Region) (coefficient : Ticket → ℤ) :
    (∑ region : Region, ∑ ticket : Ticket,
        if regionOf ticket = region then coefficient ticket else 0) =
      ∑ ticket : Ticket, coefficient ticket := by
  rw [Finset.sum_comm]
  apply Fintype.sum_congr
  intro ticket
  simp

theorem hierarchicalDenominatorMetadata
    {Ticket Region : Type*}
    [Fintype Ticket] [Fintype Region] [DecidableEq Region]
    (regionOf : Ticket → Region) (denominator : Ticket → ℤ) :
    (∑ region : Region, ∑ ticket : Ticket,
        if regionOf ticket = region then denominator ticket else 0) =
      ∑ ticket : Ticket, denominator ticket :=
  hierarchicalCoefficientMetadata regionOf denominator

end DeltaReduce
