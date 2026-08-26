import Mathlib.Data.Finset.Sort
import Mathlib.Data.Finset.Prod

/-! PO-C1 canonical domain×shard coverage and named hash abstraction. -/

namespace DeltaReduce

abbrev ParameterKey (Domain Shard : Type*) := Domain × Shard

def requiredKeys (Domain Shard : Type*) [Fintype Domain] [Fintype Shard]
    [DecidableEq Domain] [DecidableEq Shard] : Finset (ParameterKey Domain Shard) :=
  Finset.univ.product Finset.univ

theorem requiredKeysComplete
    {Domain Shard : Type*} [Fintype Domain] [Fintype Shard]
    [DecidableEq Domain] [DecidableEq Shard]
    (key : ParameterKey Domain Shard) :
    key ∈ requiredKeys Domain Shard := by simp [requiredKeys]

theorem leafTableHasExactlyOnePerKey
    {Domain Shard Leaf : Type*} [Fintype Domain] [Fintype Shard]
    [DecidableEq Domain] [DecidableEq Shard]
    (leafAt : ParameterKey Domain Shard → Leaf) :
    ∀ key, ∃! leaf, leafAt key = leaf := by
  intro key
  exact ⟨leafAt key, rfl, fun leaf hleaf => hleaf.symm⟩

def canonicalKeyOrder {Key : Type*} [LinearOrder Key]
    (keys : Finset Key) : List Key := keys.sort (· ≤ ·)

theorem canonicalSortUnique {Key : Type*} [LinearOrder Key]
    (keys₁ keys₂ : Finset Key) (hkeys : keys₁ = keys₂) :
    canonicalKeyOrder keys₁ = canonicalKeyOrder keys₂ := by
  subst keys₂
  rfl

structure NamedInjectiveHash (Input Digest : Type*) where
  name : String
  hash : Input → Digest
  injective : Function.Injective hash

theorem canonicalRootUnique {Key Digest : Type*} [LinearOrder Key]
    (hash : NamedInjectiveHash (List Key) Digest)
    (keys₁ keys₂ : Finset Key)
    (hroot : hash.hash (canonicalKeyOrder keys₁) =
      hash.hash (canonicalKeyOrder keys₂)) :
    canonicalKeyOrder keys₁ = canonicalKeyOrder keys₂ :=
  hash.injective hroot

end DeltaReduce
