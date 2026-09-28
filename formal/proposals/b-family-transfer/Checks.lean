import ManifestFamily
import StateFamily

/- Small regression checks on the EXISTING original manifest. No generated
vote, QC, authority, journal or replacement protocol fixture. -/
namespace DeltaReduce.FamilyTransferChecks

def layout := ManifestFamily.layout NativeManifestVectors.wholeManifest
def first : ShardFamily.Selector layout := ShardFamily.base layout
def last : ShardFamily.Selector layout := fun s =>
  ⟨layout.width s - 1,Nat.sub_lt (layout.positive s) (by decide)⟩

theorem firstCoordinates : List.ofFn (ManifestFamily.original.view first) = [1,-16,-8,0,8] := by decide
theorem lastCoordinates : List.ofFn (ManifestFamily.original.view last) = [4,-9,-1,7,15] := by decide
theorem original36 : (ShardFamily.flatten (ShardFamily.reconstruct ManifestFamily.original)).length = 36 := by
  rw [ManifestFamily.originalRoundtrip]
  decide

def firstShard : Fin layout.count := ⟨0,by decide⟩
theorem originalRows : ShardFamily.rows ManifestFamily.original firstShard = [(0,1),(1,-2),(2,0),(3,4)] := by decide

theorem missingRejects : ShardFamily.validateRows ManifestFamily.original firstShard [(0,1),(1,-2),(3,4)] = false := by
  simp [ShardFamily.validateRows,originalRows]
theorem duplicateRejects : ShardFamily.validateRows ManifestFamily.original firstShard [(0,1),(1,-2),(1,-2),(3,4)] = false := by
  simp [ShardFamily.validateRows,originalRows]
theorem swappedRejects : ShardFamily.validateRows ManifestFamily.original firstShard [(1,-2),(0,1),(2,0),(3,4)] = false := by
  simp [ShardFamily.validateRows,originalRows]
theorem valueRejects : ShardFamily.validateRows ManifestFamily.original firstShard [(0,1),(1,2),(2,0),(3,4)] = false := by
  simp [ShardFamily.validateRows,originalRows]

/-- Counterexample to an unsynchronized family: a component may not secretly
depend on another shard's selector. This would violate the checked locality. -/
theorem noHiddenCrossShardDependency (f : ShardFamily.Family l Common Cell)
    (a b : ShardFamily.Selector l) (s : Fin l.count) (same : a s = b s)
    (changed : f.view a s ≠ f.view b s) : False := changed (f.locality a b s same)

end DeltaReduce.FamilyTransferChecks
