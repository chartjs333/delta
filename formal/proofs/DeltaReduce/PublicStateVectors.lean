import DeltaReduce.PublicStateLoads
namespace DeltaReduce.PublicStateVectors
open NativeBinding PublicState PublicStateValues PublicStateDocuments PublicStateLoads
set_option Elab.async false
set_option maxRecDepth 1000000
set_option maxHeartbeats 0
set_option linter.unusedSimpArgs false
noncomputable def first0 := extractFirst state70 state71 (.model "v1")
noncomputable def first1 := extractFirst state74 state75 (.model "v2")
noncomputable def first2 := extractFirst state78 state79 (.model "v3")
noncomputable def first3 := extractFirst state85 state86 (.model "v1")
noncomputable def first4 := extractFirst state89 state90 (.model "v2")
noncomputable def first5 := extractFirst state93 state94 (.model "v3")
noncomputable def first6 := extractFirst state116 state117 (.model "v1")
noncomputable def first7 := extractFirst state120 state121 (.model "v2")
noncomputable def first8 := extractFirst state124 state125 (.model "v3")
noncomputable abbrev initialState := state70
noncomputable abbrev nextState := state71
noncomputable abbrev original := observation70
noncomputable def replace (state : State) (name : String) (value : Value) : State :=
  ⟨state.rows.map (fun (k,v) => (k,if k = name then value else v)), by simpa [List.map_map, Function.comp_def] using state.complete⟩
noncomputable def reencode (state : State) : Observation := { original with rows := state.rows, bytes := documentBytes identity state, root := List.replicate 32 7 }
-- Deliberately collision-full test adapter: validation failures must not rely on a stale hash.
noncomputable def rehashed (state : State) := load models identity (fun _ => List.replicate 32 7) (reencode state)
noncomputable def mapping : IdentityMap := {
  actor := fun v => if v = .model "v1" then some "validator-1" else none
  checkpoint := fun v => if v = .model "parent1" then some NativeVoteVectors.parameterAnchor.context.parentCheckpoint else none
  height := fun v => if v = .model "h1" then some NativeVoteVectors.parameterAnchor.context.height else none
  epoch := fun v => if v = .model "epoch1" then some NativeVoteVectors.parameterAnchor.context.epoch else none }
noncomputable def originalNative := first0.map (fun p => (bindNativeFrame mapping p NativeVoteVectors.parameterAnchor NativeVoteVectors.metadata0).isSome)
theorem first0ExtractsOriginalSequence : (first0.map (fun p => p.next.data.sequence)) = some 5 := by decide +kernel
theorem first0CompleteProjection : ((projectFirst models identity sha256 observation70 observation71 (.model "v1")).isSome) = true := by
  simp only [projectFirst, loadProvided loaded70, loadProvided loaded71, Option.bind_some]
  decide +kernel
theorem originalDocument70 : documentBytes identity state70 = bytes70 := by exact encodedDocument70
theorem first1ExtractsOriginalSequence : (first1.map (fun p => p.next.data.sequence)) = some 5 := by decide +kernel
theorem first2ExtractsOriginalSequence : (first2.map (fun p => p.next.data.sequence)) = some 5 := by decide +kernel
theorem first3ExtractsOriginalSequence : (first3.map (fun p => p.next.data.sequence)) = some 6 := by decide +kernel
theorem first3CompleteProjection : ((projectFirst models identity sha256 observation85 observation86 (.model "v1")).isSome) = true := by
  simp only [projectFirst, loadProvided loaded85, loadProvided loaded86, Option.bind_some]
  decide +kernel
theorem originalDocument85 : documentBytes identity state85 = bytes85 := by exact encodedDocument85
theorem first4ExtractsOriginalSequence : (first4.map (fun p => p.next.data.sequence)) = some 6 := by decide +kernel
theorem first5ExtractsOriginalSequence : (first5.map (fun p => p.next.data.sequence)) = some 6 := by decide +kernel
theorem first6ExtractsOriginalSequence : (first6.map (fun p => p.next.data.sequence)) = some 8 := by decide +kernel
theorem first6CompleteProjection : ((projectFirst models identity sha256 observation116 observation117 (.model "v1")).isSome) = true := by
  simp only [projectFirst, loadProvided loaded116, loadProvided loaded117, Option.bind_some]
  decide +kernel
theorem originalDocument116 : documentBytes identity state116 = bytes116 := by exact encodedDocument116
theorem first7ExtractsOriginalSequence : (first7.map (fun p => p.next.data.sequence)) = some 8 := by decide +kernel
theorem first8ExtractsOriginalSequence : (first8.map (fun p => p.next.data.sequence)) = some 8 := by decide +kernel
theorem originalNativeFrame : originalNative = some true := by decide +kernel
theorem missingActorMapping : (first0.map (fun p => (bindNativeFrame { mapping with actor := fun _ => none } p NativeVoteVectors.parameterAnchor NativeVoteVectors.metadata0).isSome)) = some false := by decide +kernel
theorem wrongNativeClock : (first0.map (fun p => (bindNativeFrame mapping p NativeVoteVectors.parameterAnchor { NativeVoteVectors.metadata0 with logicalTime := 0 }).isSome)) = some false := by decide +kernel
theorem oldSnapshotProfileRejected : (load models identity sha256 { original with version := "deltareduce.native-snapshot-witness.v1" }).isSome = false := by decide +kernel
theorem wrongSourceRejected : (load models identity sha256 { original with identity := { identity with modules := [] } }).isSome = false := by decide +kernel
theorem wrongConfigRejected : (load models identity sha256 { original with identity := { identity with configuration := List.replicate 32 3 } }).isSome = false := by decide +kernel
theorem wrongRootRejected : (load models identity sha256 { original with root := [] }).isSome = false := by
  cases checked : load models identity sha256 { original with root := [] } with
  | none => rfl
  | some loaded =>
    have impossible : (0 : Nat) = 32 := loaded.checked.2.2.2.2.2.2.2.1
    cases impossible
theorem wrongBytesRejected : (load models identity sha256 { original with bytes := [] }).isSome = false := by
  cases checked : load models identity sha256 { original with bytes := [] } with
  | none => rfl
  | some loaded =>
    have empty : ([] : Bytes) = documentBytes identity loaded.state := loaded.checked.2.2.2.2.2.1
    have head : (documentBytes identity loaded.state).head? = some 123 := rfl
    rw [← empty] at head
    cases head
theorem missingVariableRejected : (loadRows (initialState.rows.filter (fun row => row.1 != "messages"))).isSome = false := by decide +kernel
theorem duplicateVariableRejected : (loadRows (("messages", .set .nil) :: initialState.rows)).isSome = false := by decide +kernel
theorem reversedVariablesRejected : (loadRows initialState.rows.reverse).isSome = false := by decide +kernel
theorem duplicateSetRejected : (rehashed (replace initialState "alive" (.set (.cons (.model "v1") (.cons (.model "v1") .nil))))).isSome = false := by decide +kernel
theorem unconfiguredModelRejected : (rehashed (replace initialState "currentCheckpoint" (.model "alien"))).isSome = false := by decide +kernel
theorem nonASCIIRejected : (rehashed (replace initialState "phase" (.text "é"))).isSome = false := by decide +kernel
theorem stringModelDistinct : encode (.model "v1") ≠ encode (.text "v1") := by decide +kernel
theorem setFunctionDistinct : encode (.set .nil) ≠ encode (.function .nil) := by decide +kernel
theorem boolIntDistinct : encode (.boolean true) ≠ encode (.integer 1) := by decide +kernel
theorem falseSequenceRejected : (extract (replace initialState "durableSequence" (.function (.cons (.model "v1") (.integer 0) .nil))) (.model "v1")).isSome = false := by decide +kernel
theorem recoveringRejected : (extract (replace initialState "recoveryState" (.function (.cons (.model "v1") (.text "RECOVERING") .nil))) (.model "v1")).isSome = false := by decide +kernel
theorem staleParentRejected : (extractFirst (replace initialState "currentCheckpoint" (.model "next1")) nextState (.model "v1")).isSome = false := by decide +kernel
theorem noAppendRejected : (extractFirst initialState initialState (.model "v1")).isSome = false := by decide +kernel
theorem wrongActorRejected : (extractFirst initialState nextState (.model "v2")).isSome = false := by decide +kernel
theorem inactiveRejected : (extract (replace initialState "phase" (.text "ABORTED")) (.model "v1")).isSome = false := by decide +kernel
theorem notAliveRejected : (extract (replace initialState "alive" (.set .nil)) (.model "v1")).isSome = false := by decide +kernel
theorem extractionAloneDoesNotValidateMessages : (replace nextState "messages" unexpectedMessages).read "messages" ≠ nextState.read "messages" ∧ (extractFirst initialState (replace nextState "messages" unexpectedMessages) (.model "v1")).isSome = true := by decide +kernel
end DeltaReduce.PublicStateVectors
