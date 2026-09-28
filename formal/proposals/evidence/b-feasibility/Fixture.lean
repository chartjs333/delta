import SyncFamily
namespace DeltaReduce.BFeasibilityFixture
open BFeasibility
def rows : List ParameterKernel.Row := [⟨1, 1, [3, -4, 5]⟩]
theorem checkedOriginal :
  ParameterKernel.checkedParameter (-128) 127 (-128) 127 1 3 rows =
    some [3, -4, 5] := by decide
theorem actualFamily (original : Original) (control : RecoveryKernel.State) :
  ∃ s : Whole Original 3, s.original = original ∧ s.control = control ∧
    s.values = [3, -4, 5] ∧ reconstruct (project s) = s ∧
    ∀ k : Fin 3, ParameterKernel.checkedParameter (-128) 127 (-128) 127 1 1
      (rows.map (VectorShardRepresentation.rowAt k.val)) = some [(project s).coordinate k] :=
  checked_parameter_family checkedOriginal original control
structure Cell where
  input : Int
  parameter : Int
  model : Int
  optimizer : Int
  deriving DecidableEq
def fullState : Whole String 3 Cell := ⟨"s01", exampleControl,
  [⟨3, 3, 20, 2⟩, ⟨-4, -4, -20, -2⟩, ⟨5, 5, 20, 2⟩], rfl⟩
theorem wholeStateRoundTrip : reconstruct (project fullState) = fullState :=
  reconstruct_project fullState
theorem originalModel : (reconstruct (project fullState)).values.map Cell.model =
  [20, -20, 20] := by decide
theorem originalOptimizer : (reconstruct (project fullState)).values.map Cell.optimizer =
  [2, -2, 2] := by decide
end DeltaReduce.BFeasibilityFixture
#print axioms DeltaReduce.BFeasibility.Whole
#print axioms DeltaReduce.BFeasibility.Family
#print axioms DeltaReduce.BFeasibility.project
#print axioms DeltaReduce.BFeasibility.reconstruct
#print axioms DeltaReduce.BFeasibility.reconstruct_project
#print axioms DeltaReduce.BFeasibility.project_reconstruct
#print axioms DeltaReduce.BFeasibility.joint_injective
#print axioms DeltaReduce.BFeasibility.coordinates
#print axioms DeltaReduce.BFeasibility.acceptsCoordinates
#print axioms DeltaReduce.BFeasibility.accepted_coordinates_exact
#print axioms DeltaReduce.BFeasibility.complete_coordinate_domain
#print axioms DeltaReduce.BFeasibility.ordered_values_exact
#print axioms DeltaReduce.BFeasibility.scalarView
#print axioms DeltaReduce.BFeasibility.one_identity
#print axioms DeltaReduce.BFeasibility.one_control
#print axioms DeltaReduce.BFeasibility.wholeStep
#print axioms DeltaReduce.BFeasibility.familyStep
#print axioms DeltaReduce.BFeasibility.step_commutes
#print axioms DeltaReduce.BFeasibility.rejection_is_atomic
#print axioms DeltaReduce.BFeasibility.whole_result_of_family_step
#print axioms DeltaReduce.BFeasibility.one_original_record
#print axioms DeltaReduce.BFeasibility.original_record_checks_retained
#print axioms DeltaReduce.BFeasibility.familyReplay
#print axioms DeltaReduce.BFeasibility.history_keeps_exact_original_records
#print axioms DeltaReduce.BFeasibility.Synchronized
#print axioms DeltaReduce.BFeasibility.synchronized_reconstruct
#print axioms DeltaReduce.BFeasibility.checked_parameter_family
#print axioms DeltaReduce.BFeasibility.exampleControl
#print axioms DeltaReduce.BFeasibility.exampleFamily
#print axioms DeltaReduce.BFeasibility.exampleRoundTrip
#print axioms DeltaReduce.BFeasibility.exampleComplete
#print axioms DeltaReduce.BFeasibility.exampleMissing
#print axioms DeltaReduce.BFeasibility.exampleReordered
#print axioms DeltaReduce.BFeasibility.exampleDuplicate
#print axioms DeltaReduce.BFeasibility.exampleChanged
#print axioms DeltaReduce.BFeasibilityFixture.rows
#print axioms DeltaReduce.BFeasibilityFixture.checkedOriginal
#print axioms DeltaReduce.BFeasibilityFixture.actualFamily
#print axioms DeltaReduce.BFeasibilityFixture.Cell
#print axioms DeltaReduce.BFeasibilityFixture.fullState
#print axioms DeltaReduce.BFeasibilityFixture.wholeStateRoundTrip
#print axioms DeltaReduce.BFeasibilityFixture.originalModel
#print axioms DeltaReduce.BFeasibilityFixture.originalOptimizer
