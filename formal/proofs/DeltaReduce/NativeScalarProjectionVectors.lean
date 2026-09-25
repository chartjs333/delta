import DeltaReduce.NativeScalarProjection
import DeltaReduce.NativeGraphVectors

/-! Four actual native graph derivations plus small abstraction counterchecks.
The graph codec and authentication in NativeGraphVectors are finite/synthetic.
These are kernel examples, not native execution or production TLA mutants. -/
namespace DeltaReduce.NativeScalarProjectionVectors
open NativeBinding NativeScalarProjection
open NativeGraphVectors (fixtureBinding parameterFrame)
set_option maxRecDepth 12000
set_option maxHeartbeats 4000000

def twoCoordinates : Layout :=
  ⟨2, [⟨"s1",0,1⟩,⟨"s2",1,1⟩], by decide, by decide, by decide, by decide⟩

def reversedOffsets : Layout :=
  ⟨2, [⟨"s1",1,1⟩,⟨"s2",0,1⟩], by decide, by decide, by decide, by decide⟩

theorem fixtureLayoutLoads :
    (layout parameterFrame).map (fun l => (l.width,l.shards)) =
      some (2,[⟨"s1",0,1⟩,⟨"s2",1,1⟩]) := by decide

theorem firstParameterFromBoundGraph :
    ((deriveParameter fixtureBinding "d1" "s1").bind fun native =>
      (parameter native).map (fun p => (p.value,native.body.denominator))) = some (1,1) := by decide

theorem secondParameterFromBoundGraph :
    ((deriveParameter fixtureBinding "d1" "s2").bind fun native =>
      (parameter native).map (fun p => (p.value,native.body.denominator))) = some (-2,1) := by decide

theorem applyCoordinatesFromBoundGraph :
    ((deriveNativeApply fixtureBinding).bind fun native =>
      (applyResult native).map (fun p => (p.model.cells,p.optimizer.cells))) =
      some ([("s1",19),("s2",-19)],[("s1",2),("s2",-2)]) := by decide

theorem projectionUsesOffsets :
    (project reversedOffsets [10,20]).map (fun p => p.cells) =
      some [("s1",20),("s2",10)] := by decide

theorem signedEndpointsRetained :
    (project twoCoordinates [-9223372036854775808,9223372036854775807]).map (fun p => p.cells) =
      some [("s1",-9223372036854775808),("s2",9223372036854775807)] := by decide

theorem emptyVectorRejected : (project twoCoordinates []).isNone = true := by decide
theorem missingCoordinateRejected : (project twoCoordinates [10]).isNone = true := by decide
theorem extraCoordinateRejected : (project twoCoordinates [10,20,30]).isNone = true := by decide
theorem noDefaultZeroOnMissing : (readCells [10] [⟨"s2",1,1⟩]).isNone = true := by decide

theorem vectorShardIsUnrepresentable :
    (layout {parameterFrame with shards := [⟨"s1",0,2⟩]}).isNone = true := by decide

theorem zeroLengthShardRejected :
    (layout {parameterFrame with shards := [⟨"s1",0,0⟩,⟨"s2",1,1⟩]}).isNone = true := by decide

theorem overlappingCoordinatesRejected :
    (layout {parameterFrame with shards := [⟨"s1",0,1⟩,⟨"s2",0,1⟩]}).isNone = true := by decide

theorem missingShardRejected :
    (layout {parameterFrame with shards := [⟨"s1",0,1⟩]}).isNone = true := by decide

theorem duplicateNamesRejected :
    (layout {parameterFrame with shards := [⟨"s1",0,1⟩,⟨"s1",1,1⟩]}).isNone = true := by decide

theorem outOfRangeOffsetRejected :
    (layout {parameterFrame with shards := [⟨"s1",0,1⟩,⟨"s2",2,1⟩]}).isNone = true := by decide

theorem zeroWidthRejected :
    (layout {parameterFrame with coordinates := [], shards := []}).isNone = true := by decide

theorem thirdCoordinateCannotBeForgotten :
    (layout {parameterFrame with coordinates := ["a","b","c"]}).isNone = true := by decide

end DeltaReduce.NativeScalarProjectionVectors
