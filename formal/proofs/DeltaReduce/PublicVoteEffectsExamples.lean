import DeltaReduce.PublicVoteEffects
import DeltaReduce.PublicStateVectors
import DeltaReduce.PublicVoteEffectsCalculations

namespace DeltaReduce.PublicVoteEffectsExamples
open NativeBinding PublicState PublicStateValues PublicStateDocuments PublicStateLoads PublicStateVectors
set_option Elab.async false
set_option maxRecDepth 1000000
set_option maxHeartbeats 0

-- The eighteen complete states are reused without altering their preimages,
-- finite identity profile or original all-vote sequences 5/6/8.
theorem parameterFirstActor : (PublicVoteEffects.check state70 state71 (.model "v1")).isSome = true := PublicVoteEffectsCalculations.accepts0
theorem parameterSecondActor : (PublicVoteEffects.check state74 state75 (.model "v2")).isSome = true := PublicVoteEffectsCalculations.accepts1
theorem parameterThirdActor : (PublicVoteEffects.check state78 state79 (.model "v3")).isSome = true := PublicVoteEffectsCalculations.accepts2
theorem secondShardFirstActor : (PublicVoteEffects.check state85 state86 (.model "v1")).isSome = true := PublicVoteEffectsCalculations.accepts3
theorem secondShardSecondActor : (PublicVoteEffects.check state89 state90 (.model "v2")).isSome = true := PublicVoteEffectsCalculations.accepts4
theorem secondShardThirdActor : (PublicVoteEffects.check state93 state94 (.model "v3")).isSome = true := PublicVoteEffectsCalculations.accepts5
theorem applyFirstActor : (PublicVoteEffects.check state116 state117 (.model "v1")).isSome = true := PublicVoteEffectsCalculations.accepts6
theorem applySecondActor : (PublicVoteEffects.check state120 state121 (.model "v2")).isSome = true := PublicVoteEffectsCalculations.accepts7
theorem applyThirdActor : (PublicVoteEffects.check state124 state125 (.model "v3")).isSome = true := PublicVoteEffectsCalculations.accepts8

theorem completeParameterProjection :
    (PublicVoteEffects.project models identity sha256 observation70 observation71 (.model "v1")).isSome = true := by
  exact PublicVoteEffects.projectFromLoaded loaded70 loaded71 parameterFirstActor

theorem completeSecondShardProjection :
    (PublicVoteEffects.project models identity sha256 observation85 observation86 (.model "v1")).isSome = true := by
  exact PublicVoteEffects.projectFromLoaded loaded85 loaded86 secondShardFirstActor

theorem completeApplyProjection :
    (PublicVoteEffects.project models identity sha256 observation116 observation117 (.model "v1")).isSome = true := by
  exact PublicVoteEffects.projectFromLoaded loaded116 loaded117 applyFirstActor

-- This is exactly the preceding layer's admitted counterexample. It now fails
-- by the general unchanged-message theorem, not a finite exception table.
theorem priorMessageCounterexampleRejected :
    PublicVoteEffects.check initialState (replace nextState "messages" unexpectedMessages) (.model "v1") = none := by
  apply PublicVoteEffects.messageMutationRejected
  decide +kernel

theorem parameterTimeSideEffectRejected :
    PublicVoteEffects.check initialState (replace nextState "logicalTime" (.integer 999)) (.model "v1") = none := by
  apply PublicVoteEffects.unassignedMutationRejected (name := "logicalTime") (by decide +kernel) (by decide +kernel)
  decide +kernel

theorem parameterCurrentAdvanceRejected :
    PublicVoteEffects.check initialState (replace nextState "currentCheckpoint" (.model "next1")) (.model "v1") = none := by
  apply PublicVoteEffects.unassignedMutationRejected (name := "currentCheckpoint") (by decide +kernel) (by decide +kernel)
  decide +kernel

theorem applyCurrentAdvanceRejected :
    PublicVoteEffects.check state116 (replace state117 "currentCheckpoint" (.model "next1")) (.model "v1") = none := by
  apply PublicVoteEffects.unassignedMutationRejected (name := "currentCheckpoint") (by decide +kernel) (by decide +kernel)
  decide +kernel

theorem deliverySideEffectRejected :
    PublicVoteEffects.check initialState (replace nextState "receivedVotes" (.boolean true)) (.model "v1") = none := by
  apply PublicVoteEffects.unassignedMutationRejected (name := "receivedVotes") (by decide +kernel) (by decide +kernel)
  decide +kernel

theorem qcSideEffectRejected :
    PublicVoteEffects.check initialState (replace nextState "parameterQCs" (.boolean true)) (.model "v1") = none := by
  apply PublicVoteEffects.unassignedMutationRejected (name := "parameterQCs") (by decide +kernel) (by decide +kernel)
  decide +kernel

theorem missingPhaseVoteRejected :
    PublicVoteEffects.check initialState (replace nextState "parameterVotes" (.set .nil)) (.model "v1") = none :=
  PublicVoteEffects.emptyPhaseRejected (by decide +kernel) (by decide +kernel)

theorem missingVolatileVoteRejected :
    PublicVoteEffects.check initialState (replace nextState "volatileVotes" (.set .nil)) (.model "v1") = none :=
  PublicVoteEffects.emptyVolatileRejected (by decide +kernel)

theorem missingBothPhaseVotesRejected :
    PublicVoteEffects.check state116 (replace (replace state117 "applyVotes" (.set .nil)) "parameterVotes" (.set .nil)) (.model "v1") = none :=
  PublicVoteEffects.emptyPhaseRejected (by decide +kernel) (by decide +kernel)

theorem changedOtherActorSequenceRejected :
    PublicVoteEffects.check initialState
      (replace nextState "durableSequence" (.function (.cons (.model "v1") (.integer 5)
        (.cons (.model "v2") (.integer 99) (.cons (.model "v3") (.integer 4)
          (.cons (.model "v4") (.integer 0) .nil)))))) (.model "v1") = none := by
  apply PublicVoteEffects.otherSequenceMutationRejected (other := .model "v2") (by decide +kernel)
  decide +kernel

-- Component checks make empty/nonempty and duplicate-key/value behavior clear.
theorem insertEmpty : PublicVoteEffects.insert (.integer 1) .nil = .cons (.integer 1) .nil := by decide +kernel
theorem insertDuplicate : PublicVoteEffects.insert (.integer 1) (.cons (.integer 1) .nil) = .cons (.integer 1) .nil := by decide +kernel
theorem insertBefore : PublicVoteEffects.insert (.integer 1) (.cons (.integer 2) .nil) = .cons (.integer 1) (.cons (.integer 2) .nil) := by decide +kernel
theorem insertAfter : PublicVoteEffects.insert (.integer 2) (.cons (.integer 1) .nil) = .cons (.integer 1) (.cons (.integer 2) .nil) := by decide +kernel
theorem updateAbsentKeepsDomains : PublicVoteEffects.update (.model "v2") (.integer 9) (.cons (.model "v1") (.integer 4) .nil) = .cons (.model "v1") (.integer 4) .nil := by decide +kernel
theorem malformedSequenceSourceRejected :
    (first0.map (fun first => (PublicVoteEffects.readInputs
      (replace initialState "durableSequence" (.boolean true)) first.vote).isSome)) = some false := by decide +kernel
theorem negativeSequenceSourceRejected :
    (first0.map (fun first => (PublicVoteEffects.readInputs
      (replace initialState "durableSequence" (.function (.cons (.model "v1") (.integer (-1)) .nil))) first.vote).isSome)) = some false := by decide +kernel

end DeltaReduce.PublicVoteEffectsExamples
