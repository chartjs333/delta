import DeltaReduce.PublicState
import DeltaReduce.NativeVoteVectors
namespace DeltaReduce.PublicStateValues
open NativeBinding PublicState
set_option Elab.async false
set_option maxRecDepth 1000000
set_option maxHeartbeats 0
set_option linter.unusedSimpArgs false
-- Synthetic semantic ID avoids hashing this file into its own literals.
-- Finite SHA samples below are not general SHA or exporter authentication.
noncomputable def models : List String := ["apply1","coeff1","configA","configB","content1","d1","data1","epoch1","h1","model1","next1","norm1","optimizer1","parent1","profile1","s1","schema1","seed1","shard1","shard2","t1","v1","v2","v3","v4","w1"]
noncomputable def identity : Identity := {
  semantics := List.replicate 32 0
  configuration := [131,211,25,187,117,168,208,58,59,59,206,83,82,216,171,209,28,62,205,200,173,248,41,162,126,103,74,45,49,174,74,100]
  modules := [("DeltaReduce",[64,215,219,113,244,35,117,234,112,189,167,150,143,84,103,7,197,79,169,57,185,98,101,45,187,113,34,152,8,67,114,209]),("DeltaReduceArithmetic",[169,200,221,82,17,174,52,30,62,100,46,62,66,40,66,93,82,80,61,235,136,242,64,1,74,141,47,83,28,176,236,38]),("DeltaReduceAvailability",[220,132,248,207,211,80,250,233,118,70,203,49,143,240,85,175,93,93,245,66,224,78,161,90,186,2,125,175,150,19,33,164]),("DeltaReduceCertificates",[91,8,110,109,79,68,68,114,99,17,17,230,214,116,93,111,113,47,17,251,26,167,115,233,135,6,91,219,237,45,75,0]),("DeltaReduceFailures",[238,148,193,198,115,53,136,133,68,177,104,146,0,184,41,82,111,9,214,24,189,244,233,194,86,173,44,28,7,136,236,245]),("DeltaReduceFixtureInputs",[160,125,86,123,166,24,145,251,93,84,31,83,207,156,211,20,237,127,33,174,186,67,79,197,246,144,73,133,204,145,213,48]),("DeltaReducePublicState",[240,35,143,94,241,49,49,139,25,0,109,8,155,161,58,195,166,253,92,55,186,89,29,220,127,103,58,205,41,130,121,21]),("DeltaReduceQuorums",[174,14,154,100,151,111,107,145,88,191,196,67,121,100,138,171,189,233,144,4,122,67,33,243,180,246,53,94,95,103,104,227]),("DeltaReduceReduceApply",[56,222,185,195,54,97,139,124,169,197,72,178,73,172,87,51,117,220,94,149,23,91,180,236,78,47,166,178,141,1,57,252]),("DeltaReduceTickets",[124,67,71,192,67,206,242,171,233,179,166,101,87,245,182,249,83,207,251,148,112,28,44,36,236,95,227,186,214,190,228,192]),("DeltaReduceTypes",[46,179,0,128,96,248,187,227,237,27,225,33,103,33,29,96,45,197,191,47,91,199,214,92,170,152,150,248,88,107,1,33])] }
theorem keyColon0 : quoted "abortQCs" ++ [58] = asciiBytes "\"abortQCs\":" := by decide +kernel
theorem keyColon1 : quoted "abortReason" ++ [58] = asciiBytes "\"abortReason\":" := by decide +kernel
theorem keyColon2 : quoted "abortRequests" ++ [58] = asciiBytes "\"abortRequests\":" := by decide +kernel
theorem keyColon3 : quoted "abortVotes" ++ [58] = asciiBytes "\"abortVotes\":" := by decide +kernel
theorem keyColon4 : quoted "aggregateCandidates" ++ [58] = asciiBytes "\"aggregateCandidates\":" := by decide +kernel
theorem keyColon5 : quoted "aggregateRootQCs" ++ [58] = asciiBytes "\"aggregateRootQCs\":" := by decide +kernel
theorem keyColon6 : quoted "aggregateVotes" ++ [58] = asciiBytes "\"aggregateVotes\":" := by decide +kernel
theorem keyColon7 : quoted "aggregationPlanCertificates" ++ [58] = asciiBytes "\"aggregationPlanCertificates\":" := by decide +kernel
theorem keyColon8 : quoted "alive" ++ [58] = asciiBytes "\"alive\":" := by decide +kernel
theorem keyColon9 : quoted "apcVotes" ++ [58] = asciiBytes "\"apcVotes\":" := by decide +kernel
theorem keyColon10 : quoted "applyCandidates" ++ [58] = asciiBytes "\"applyCandidates\":" := by decide +kernel
theorem keyColon11 : quoted "applyQCs" ++ [58] = asciiBytes "\"applyQCs\":" := by decide +kernel
theorem keyColon12 : quoted "applyVotes" ++ [58] = asciiBytes "\"applyVotes\":" := by decide +kernel
theorem keyColon13 : quoted "availabilityAttestations" ++ [58] = asciiBytes "\"availabilityAttestations\":" := by decide +kernel
theorem keyColon14 : quoted "availabilityCertificates" ++ [58] = asciiBytes "\"availabilityCertificates\":" := by decide +kernel
theorem keyColon15 : quoted "availabilityShortfalls" ++ [58] = asciiBytes "\"availabilityShortfalls\":" := by decide +kernel
theorem keyColon16 : quoted "availableArtifacts" ++ [58] = asciiBytes "\"availableArtifacts\":" := by decide +kernel
theorem keyColon17 : quoted "availableTickets" ++ [58] = asciiBytes "\"availableTickets\":" := by decide +kernel
theorem keyColon18 : quoted "byzantine" ++ [58] = asciiBytes "\"byzantine\":" := by decide +kernel
theorem keyColon19 : quoted "certificateRejections" ++ [58] = asciiBytes "\"certificateRejections\":" := by decide +kernel
theorem keyColon20 : quoted "certificateReplayReceipts" ++ [58] = asciiBytes "\"certificateReplayReceipts\":" := by decide +kernel
theorem keyColon21 : quoted "closedInputBodies" ++ [58] = asciiBytes "\"closedInputBodies\":" := by decide +kernel
theorem keyColon22 : quoted "commitments" ++ [58] = asciiBytes "\"commitments\":" := by decide +kernel
theorem keyColon23 : quoted "corruptArtifacts" ++ [58] = asciiBytes "\"corruptArtifacts\":" := by decide +kernel
theorem keyColon24 : quoted "crashCoverage" ++ [58] = asciiBytes "\"crashCoverage\":" := by decide +kernel
theorem keyColon25 : quoted "currentAdvanceReceipts" ++ [58] = asciiBytes "\"currentAdvanceReceipts\":" := by decide +kernel
theorem keyColon26 : quoted "currentCheckpoint" ++ [58] = asciiBytes "\"currentCheckpoint\":" := by decide +kernel
theorem keyColon27 : quoted "currentReplayReceipts" ++ [58] = asciiBytes "\"currentReplayReceipts\":" := by decide +kernel
theorem keyColon28 : quoted "durableSequence" ++ [58] = asciiBytes "\"durableSequence\":" := by decide +kernel
theorem keyColon29 : quoted "durableVotes" ++ [58] = asciiBytes "\"durableVotes\":" := by decide +kernel
theorem keyColon30 : quoted "ecVotes" ++ [58] = asciiBytes "\"ecVotes\":" := by decide +kernel
theorem keyColon31 : quoted "eligibilityCertificates" ++ [58] = asciiBytes "\"eligibilityCertificates\":" := by decide +kernel
theorem keyColon32 : quoted "finalizedCertificates" ++ [58] = asciiBytes "\"finalizedCertificates\":" := by decide +kernel
theorem keyColon33 : quoted "inputSetCertificates" ++ [58] = asciiBytes "\"inputSetCertificates\":" := by decide +kernel
theorem keyColon34 : quoted "iscVotes" ++ [58] = asciiBytes "\"iscVotes\":" := by decide +kernel
theorem keyColon35 : quoted "lateAvailabilityEvidence" ++ [58] = asciiBytes "\"lateAvailabilityEvidence\":" := by decide +kernel
theorem keyColon36 : quoted "leaseActive" ++ [58] = asciiBytes "\"leaseActive\":" := by decide +kernel
theorem keyColon37 : quoted "leaseEpoch" ++ [58] = asciiBytes "\"leaseEpoch\":" := by decide +kernel
theorem keyColon38 : quoted "leaseOwner" ++ [58] = asciiBytes "\"leaseOwner\":" := by decide +kernel
theorem keyColon39 : quoted "logicalTime" ++ [58] = asciiBytes "\"logicalTime\":" := by decide +kernel
theorem keyColon40 : quoted "materializedArtifacts" ++ [58] = asciiBytes "\"materializedArtifacts\":" := by decide +kernel
theorem keyColon41 : quoted "messageMultiplicity" ++ [58] = asciiBytes "\"messageMultiplicity\":" := by decide +kernel
theorem keyColon42 : quoted "messages" ++ [58] = asciiBytes "\"messages\":" := by decide +kernel
theorem keyColon43 : quoted "parameterQCs" ++ [58] = asciiBytes "\"parameterQCs\":" := by decide +kernel
theorem keyColon44 : quoted "parameterResults" ++ [58] = asciiBytes "\"parameterResults\":" := by decide +kernel
theorem keyColon45 : quoted "parameterVotes" ++ [58] = asciiBytes "\"parameterVotes\":" := by decide +kernel
theorem keyColon46 : quoted "partition" ++ [58] = asciiBytes "\"partition\":" := by decide +kernel
theorem keyColon47 : quoted "pendingPointerRecoveries" ++ [58] = asciiBytes "\"pendingPointerRecoveries\":" := by decide +kernel
theorem keyColon48 : quoted "phase" ++ [58] = asciiBytes "\"phase\":" := by decide +kernel
theorem keyColon49 : quoted "proposals" ++ [58] = asciiBytes "\"proposals\":" := by decide +kernel
theorem keyColon50 : quoted "publishedObjects" ++ [58] = asciiBytes "\"publishedObjects\":" := by decide +kernel
theorem keyColon51 : quoted "receivedVotes" ++ [58] = asciiBytes "\"receivedVotes\":" := by decide +kernel
theorem keyColon52 : quoted "recoveryState" ++ [58] = asciiBytes "\"recoveryState\":" := by decide +kernel
theorem keyColon53 : quoted "reduceApplyRejections" ++ [58] = asciiBytes "\"reduceApplyRejections\":" := by decide +kernel
theorem keyColon54 : quoted "rejectedCommitments" ++ [58] = asciiBytes "\"rejectedCommitments\":" := by decide +kernel
theorem keyColon55 : quoted "rejectedPublications" ++ [58] = asciiBytes "\"rejectedPublications\":" := by decide +kernel
theorem keyColon56 : quoted "repairAttempts" ++ [58] = asciiBytes "\"repairAttempts\":" := by decide +kernel
theorem keyColon57 : quoted "seedTranscripts" ++ [58] = asciiBytes "\"seedTranscripts\":" := by decide +kernel
theorem keyColon58 : quoted "ticketPlan" ++ [58] = asciiBytes "\"ticketPlan\":" := by decide +kernel
theorem keyColon59 : quoted "timeoutObservations" ++ [58] = asciiBytes "\"timeoutObservations\":" := by decide +kernel
theorem keyColon60 : quoted "timeoutVotes" ++ [58] = asciiBytes "\"timeoutVotes\":" := by decide +kernel
theorem keyColon61 : quoted "view" ++ [58] = asciiBytes "\"view\":" := by decide +kernel
theorem keyColon62 : quoted "viewChangeQCs" ++ [58] = asciiBytes "\"viewChangeQCs\":" := by decide +kernel
theorem keyColon63 : quoted "volatileVotes" ++ [58] = asciiBytes "\"volatileVotes\":" := by decide +kernel
noncomputable def value0 : Value := .set .nil
noncomputable def rawvalue0 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [] ++ [93,93]
theorem encoded_value0 : encode value0 = rawvalue0 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [] ++ [93,93] = _
  all_goals rfl
theorem nodes_value0 : nodes value0 = 1 := by
  change 1 + 0 = 1
  all_goals decide +kernel
theorem depth_value0 : depth value0 = 0 := by
  change 0 = 0
  all_goals decide +kernel
theorem canonical_value0 : canonical models value0 = true := by
  change (true && ordered []) = true
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value0 : rawvalue0.length = 10 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (show (List.intercalate [44] ([] : List Bytes)).length = 0 from rfl)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value1 : Value := .text "NO_ABORT"
noncomputable def rawvalue1 : Bytes := asciiBytes "[\"str\",\"NO_ABORT\"]"
theorem encoded_value1 : encode value1 = rawvalue1 := by
  all_goals rfl
theorem nodes_value1 : nodes value1 = 1 := by rfl
theorem depth_value1 : depth value1 = 0 := by rfl
theorem canonical_value1 : canonical models value1 = true := by decide +kernel
theorem rawLength_value1 : rawvalue1.length = 18 := by
  decide +kernel
noncomputable def value2 : Value := .text "body"
noncomputable def rawvalue2 : Bytes := asciiBytes "[\"str\",\"body\"]"
theorem encoded_value2 : encode value2 = rawvalue2 := by
  all_goals rfl
theorem nodes_value2 : nodes value2 = 1 := by rfl
theorem depth_value2 : depth value2 = 0 := by rfl
theorem canonical_value2 : canonical models value2 = true := by decide +kernel
theorem rawLength_value2 : rawvalue2.length = 14 := by
  decide +kernel
noncomputable def value3 : Value := .text "coefficientProfile"
noncomputable def rawvalue3 : Bytes := asciiBytes "[\"str\",\"coefficientProfile\"]"
theorem encoded_value3 : encode value3 = rawvalue3 := by
  all_goals rfl
theorem nodes_value3 : nodes value3 = 1 := by rfl
theorem depth_value3 : depth value3 = 0 := by rfl
theorem canonical_value3 : canonical models value3 = true := by decide +kernel
theorem rawLength_value3 : rawvalue3.length = 28 := by
  decide +kernel
noncomputable def value4 : Value := .model "coeff1"
noncomputable def rawvalue4 : Bytes := asciiBytes "[\"model\",\"coeff1\"]"
theorem encoded_value4 : encode value4 = rawvalue4 := by
  all_goals rfl
theorem nodes_value4 : nodes value4 = 1 := by rfl
theorem depth_value4 : depth value4 = 0 := by rfl
theorem canonical_value4 : canonical models value4 = true := by decide +kernel
theorem rawLength_value4 : rawvalue4.length = 18 := by
  decide +kernel
noncomputable def value5 : Value := .text "ec"
noncomputable def rawvalue5 : Bytes := asciiBytes "[\"str\",\"ec\"]"
theorem encoded_value5 : encode value5 = rawvalue5 := by
  all_goals rfl
theorem nodes_value5 : nodes value5 = 1 := by rfl
theorem depth_value5 : depth value5 = 0 := by rfl
theorem canonical_value5 : canonical models value5 = true := by decide +kernel
theorem rawLength_value5 : rawvalue5.length = 12 := by
  decide +kernel
noncomputable def value6 : Value := .text "isc"
noncomputable def rawvalue6 : Bytes := asciiBytes "[\"str\",\"isc\"]"
theorem encoded_value6 : encode value6 = rawvalue6 := by
  all_goals rfl
theorem nodes_value6 : nodes value6 = 1 := by rfl
theorem depth_value6 : depth value6 = 0 := by rfl
theorem canonical_value6 : canonical models value6 = true := by decide +kernel
theorem rawLength_value6 : rawvalue6.length = 13 := by
  decide +kernel
noncomputable def value7 : Value := .text "canonicalRoot"
noncomputable def rawvalue7 : Bytes := asciiBytes "[\"str\",\"canonicalRoot\"]"
theorem encoded_value7 : encode value7 = rawvalue7 := by
  all_goals rfl
theorem nodes_value7 : nodes value7 = 1 := by rfl
theorem depth_value7 : depth value7 = 0 := by rfl
theorem canonical_value7 : canonical models value7 = true := by decide +kernel
theorem rawLength_value7 : rawvalue7.length = 23 := by
  decide +kernel
noncomputable def value8 : Value := .text "content"
noncomputable def rawvalue8 : Bytes := asciiBytes "[\"str\",\"content\"]"
theorem encoded_value8 : encode value8 = rawvalue8 := by
  all_goals rfl
theorem nodes_value8 : nodes value8 = 1 := by rfl
theorem depth_value8 : depth value8 = 0 := by rfl
theorem canonical_value8 : canonical models value8 = true := by decide +kernel
theorem rawLength_value8 : rawvalue8.length = 17 := by
  decide +kernel
noncomputable def value9 : Value := .model "content1"
noncomputable def rawvalue9 : Bytes := asciiBytes "[\"model\",\"content1\"]"
theorem encoded_value9 : encode value9 = rawvalue9 := by
  all_goals rfl
theorem nodes_value9 : nodes value9 = 1 := by rfl
theorem depth_value9 : depth value9 = 0 := by rfl
theorem canonical_value9 : canonical models value9 = true := by decide +kernel
theorem rawLength_value9 : rawvalue9.length = 20 := by
  decide +kernel
noncomputable def value10 : Value := .text "ticket"
noncomputable def rawvalue10 : Bytes := asciiBytes "[\"str\",\"ticket\"]"
theorem encoded_value10 : encode value10 = rawvalue10 := by
  all_goals rfl
theorem nodes_value10 : nodes value10 = 1 := by rfl
theorem depth_value10 : depth value10 = 0 := by rfl
theorem canonical_value10 : canonical models value10 = true := by decide +kernel
theorem rawLength_value10 : rawvalue10.length = 16 := by
  decide +kernel
noncomputable def value11 : Value := .model "t1"
noncomputable def rawvalue11 : Bytes := asciiBytes "[\"model\",\"t1\"]"
theorem encoded_value11 : encode value11 = rawvalue11 := by
  all_goals rfl
theorem nodes_value11 : nodes value11 = 1 := by rfl
theorem depth_value11 : depth value11 = 0 := by rfl
theorem canonical_value11 : canonical models value11 = true := by decide +kernel
theorem rawLength_value11 : rawvalue11.length = 14 := by
  decide +kernel
noncomputable def value12 : Value := .function (.cons value8 value9 (.cons value10 value11 .nil))
noncomputable def rawvalue12 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue8 ++ [44] ++ rawvalue9 ++ [93]),([91] ++ rawvalue10 ++ [44] ++ rawvalue11 ++ [93])] ++ [93,93]
theorem encoded_value12 : encode value12 = rawvalue12 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value8 ++ [44] ++ encode value9 ++ [93]),([91] ++ encode value10 ++ [44] ++ encode value11 ++ [93])] ++ [93,93] = _
  simp only [encoded_value8,encoded_value9,encoded_value10,encoded_value11]
  all_goals rfl
theorem order_value8_value10 : byteLess rawvalue8 rawvalue10 = true := by
  simp only [rawvalue8,rawvalue10,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value12 : nodes value12 = 5 := by
  change 1 + (nodes value8 + nodes value9 + (nodes value10 + nodes value11 + 0)) = 5
  simp only [nodes_value8,nodes_value9,nodes_value10,nodes_value11]
  all_goals decide +kernel
theorem depth_value12 : depth value12 = 1 := by
  change max (max (1 + depth value8) (1 + depth value9)) (max (max (1 + depth value10) (1 + depth value11)) (0)) = 1
  simp only [depth_value8,depth_value9,depth_value10,depth_value11]
  all_goals decide +kernel
theorem canonical_value12 : canonical models value12 = true := by
  change ((canonical models value8 && canonical models value9 && (canonical models value10 && canonical models value11 && true)) && ordered [encode value8,encode value10]) = true
  simp only [canonical_value8,canonical_value9,canonical_value10,canonical_value11,encoded_value8,encoded_value10]
  simp only [ordered,List.all_cons,List.all_nil,order_value8_value10,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value12 : rawvalue12.length = 84 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value8) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value9) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value10) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value11) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value13 : Value := .set (.cons value12 .nil)
noncomputable def rawvalue13 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue12] ++ [93,93]
theorem encoded_value13 : encode value13 = rawvalue13 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value12] ++ [93,93] = _
  simp only [encoded_value12]
  all_goals rfl
theorem nodes_value13 : nodes value13 = 6 := by
  change 1 + (nodes value12 + 0) = 6
  simp only [nodes_value12]
  all_goals decide +kernel
theorem depth_value13 : depth value13 = 2 := by
  change max (1 + depth value12) (0) = 2
  simp only [depth_value12]
  all_goals decide +kernel
theorem canonical_value13 : canonical models value13 = true := by
  change ((canonical models value12 && true) && ordered [encode value12]) = true
  simp only [canonical_value12,encoded_value12]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value13 : rawvalue13.length = 94 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value12)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value14 : Value := .text "config"
noncomputable def rawvalue14 : Bytes := asciiBytes "[\"str\",\"config\"]"
theorem encoded_value14 : encode value14 = rawvalue14 := by
  all_goals rfl
theorem nodes_value14 : nodes value14 = 1 := by rfl
theorem depth_value14 : depth value14 = 0 := by rfl
theorem canonical_value14 : canonical models value14 = true := by decide +kernel
theorem rawLength_value14 : rawvalue14.length = 16 := by
  decide +kernel
noncomputable def value15 : Value := .model "configA"
noncomputable def rawvalue15 : Bytes := asciiBytes "[\"model\",\"configA\"]"
theorem encoded_value15 : encode value15 = rawvalue15 := by
  all_goals rfl
theorem nodes_value15 : nodes value15 = 1 := by rfl
theorem depth_value15 : depth value15 = 0 := by rfl
theorem canonical_value15 : canonical models value15 = true := by decide +kernel
theorem rawLength_value15 : rawvalue15.length = 19 := by
  decide +kernel
noncomputable def value16 : Value := .text "entries"
noncomputable def rawvalue16 : Bytes := asciiBytes "[\"str\",\"entries\"]"
theorem encoded_value16 : encode value16 = rawvalue16 := by
  all_goals rfl
theorem nodes_value16 : nodes value16 = 1 := by rfl
theorem depth_value16 : depth value16 = 0 := by rfl
theorem canonical_value16 : canonical models value16 = true := by decide +kernel
theorem rawLength_value16 : rawvalue16.length = 17 := by
  decide +kernel
noncomputable def value17 : Value := .text "policy"
noncomputable def rawvalue17 : Bytes := asciiBytes "[\"str\",\"policy\"]"
theorem encoded_value17 : encode value17 = rawvalue17 := by
  all_goals rfl
theorem nodes_value17 : nodes value17 = 1 := by rfl
theorem depth_value17 : depth value17 = 0 := by rfl
theorem canonical_value17 : canonical models value17 = true := by decide +kernel
theorem rawLength_value17 : rawvalue17.length = 16 := by
  decide +kernel
noncomputable def value18 : Value := .text "OMIT_UNAVAILABLE"
noncomputable def rawvalue18 : Bytes := asciiBytes "[\"str\",\"OMIT_UNAVAILABLE\"]"
theorem encoded_value18 : encode value18 = rawvalue18 := by
  all_goals rfl
theorem nodes_value18 : nodes value18 = 1 := by rfl
theorem depth_value18 : depth value18 = 0 := by rfl
theorem canonical_value18 : canonical models value18 = true := by decide +kernel
theorem rawLength_value18 : rawvalue18.length = 26 := by
  decide +kernel
noncomputable def value19 : Value := .text "round"
noncomputable def rawvalue19 : Bytes := asciiBytes "[\"str\",\"round\"]"
theorem encoded_value19 : encode value19 = rawvalue19 := by
  all_goals rfl
theorem nodes_value19 : nodes value19 = 1 := by rfl
theorem depth_value19 : depth value19 = 0 := by rfl
theorem canonical_value19 : canonical models value19 = true := by decide +kernel
theorem rawLength_value19 : rawvalue19.length = 15 := by
  decide +kernel
noncomputable def value20 : Value := .text "epoch"
noncomputable def rawvalue20 : Bytes := asciiBytes "[\"str\",\"epoch\"]"
theorem encoded_value20 : encode value20 = rawvalue20 := by
  all_goals rfl
theorem nodes_value20 : nodes value20 = 1 := by rfl
theorem depth_value20 : depth value20 = 0 := by rfl
theorem canonical_value20 : canonical models value20 = true := by decide +kernel
theorem rawLength_value20 : rawvalue20.length = 15 := by
  decide +kernel
noncomputable def value21 : Value := .model "epoch1"
noncomputable def rawvalue21 : Bytes := asciiBytes "[\"model\",\"epoch1\"]"
theorem encoded_value21 : encode value21 = rawvalue21 := by
  all_goals rfl
theorem nodes_value21 : nodes value21 = 1 := by rfl
theorem depth_value21 : depth value21 = 0 := by rfl
theorem canonical_value21 : canonical models value21 = true := by decide +kernel
theorem rawLength_value21 : rawvalue21.length = 18 := by
  decide +kernel
noncomputable def value22 : Value := .text "height"
noncomputable def rawvalue22 : Bytes := asciiBytes "[\"str\",\"height\"]"
theorem encoded_value22 : encode value22 = rawvalue22 := by
  all_goals rfl
theorem nodes_value22 : nodes value22 = 1 := by rfl
theorem depth_value22 : depth value22 = 0 := by rfl
theorem canonical_value22 : canonical models value22 = true := by decide +kernel
theorem rawLength_value22 : rawvalue22.length = 16 := by
  decide +kernel
noncomputable def value23 : Value := .model "h1"
noncomputable def rawvalue23 : Bytes := asciiBytes "[\"model\",\"h1\"]"
theorem encoded_value23 : encode value23 = rawvalue23 := by
  all_goals rfl
theorem nodes_value23 : nodes value23 = 1 := by rfl
theorem depth_value23 : depth value23 = 0 := by rfl
theorem canonical_value23 : canonical models value23 = true := by decide +kernel
theorem rawLength_value23 : rawvalue23.length = 14 := by
  decide +kernel
noncomputable def value24 : Value := .function (.cons value20 value21 (.cons value22 value23 .nil))
noncomputable def rawvalue24 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue20 ++ [44] ++ rawvalue21 ++ [93]),([91] ++ rawvalue22 ++ [44] ++ rawvalue23 ++ [93])] ++ [93,93]
theorem encoded_value24 : encode value24 = rawvalue24 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value20 ++ [44] ++ encode value21 ++ [93]),([91] ++ encode value22 ++ [44] ++ encode value23 ++ [93])] ++ [93,93] = _
  simp only [encoded_value20,encoded_value21,encoded_value22,encoded_value23]
  all_goals rfl
theorem order_value20_value22 : byteLess rawvalue20 rawvalue22 = true := by
  simp only [rawvalue20,rawvalue22,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value24 : nodes value24 = 5 := by
  change 1 + (nodes value20 + nodes value21 + (nodes value22 + nodes value23 + 0)) = 5
  simp only [nodes_value20,nodes_value21,nodes_value22,nodes_value23]
  all_goals decide +kernel
theorem depth_value24 : depth value24 = 1 := by
  change max (max (1 + depth value20) (1 + depth value21)) (max (max (1 + depth value22) (1 + depth value23)) (0)) = 1
  simp only [depth_value20,depth_value21,depth_value22,depth_value23]
  all_goals decide +kernel
theorem canonical_value24 : canonical models value24 = true := by
  change ((canonical models value20 && canonical models value21 && (canonical models value22 && canonical models value23 && true)) && ordered [encode value20,encode value22]) = true
  simp only [canonical_value20,canonical_value21,canonical_value22,canonical_value23,encoded_value20,encoded_value22]
  simp only [ordered,List.all_cons,List.all_nil,order_value20_value22,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value24 : rawvalue24.length = 80 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value20) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value21) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value22) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value23) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value25 : Value := .function (.cons value7 value13 (.cons value14 value15 (.cons value16 value13 (.cons value17 value18 (.cons value19 value24 .nil)))))
noncomputable def rawvalue25 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue7 ++ [44] ++ rawvalue13 ++ [93]),([91] ++ rawvalue14 ++ [44] ++ rawvalue15 ++ [93]),([91] ++ rawvalue16 ++ [44] ++ rawvalue13 ++ [93]),([91] ++ rawvalue17 ++ [44] ++ rawvalue18 ++ [93]),([91] ++ rawvalue19 ++ [44] ++ rawvalue24 ++ [93])] ++ [93,93]
theorem encoded_value25 : encode value25 = rawvalue25 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value7 ++ [44] ++ encode value13 ++ [93]),([91] ++ encode value14 ++ [44] ++ encode value15 ++ [93]),([91] ++ encode value16 ++ [44] ++ encode value13 ++ [93]),([91] ++ encode value17 ++ [44] ++ encode value18 ++ [93]),([91] ++ encode value19 ++ [44] ++ encode value24 ++ [93])] ++ [93,93] = _
  simp only [encoded_value7,encoded_value13,encoded_value14,encoded_value15,encoded_value16,encoded_value17,encoded_value18,encoded_value19,encoded_value24]
  all_goals rfl
theorem order_value7_value14 : byteLess rawvalue7 rawvalue14 = true := by
  simp only [rawvalue7,rawvalue14,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value7_value16 : byteLess rawvalue7 rawvalue16 = true := by
  simp only [rawvalue7,rawvalue16,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value7_value17 : byteLess rawvalue7 rawvalue17 = true := by
  simp only [rawvalue7,rawvalue17,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value7_value19 : byteLess rawvalue7 rawvalue19 = true := by
  simp only [rawvalue7,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value14_value16 : byteLess rawvalue14 rawvalue16 = true := by
  simp only [rawvalue14,rawvalue16,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value14_value17 : byteLess rawvalue14 rawvalue17 = true := by
  simp only [rawvalue14,rawvalue17,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value14_value19 : byteLess rawvalue14 rawvalue19 = true := by
  simp only [rawvalue14,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value16_value17 : byteLess rawvalue16 rawvalue17 = true := by
  simp only [rawvalue16,rawvalue17,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value16_value19 : byteLess rawvalue16 rawvalue19 = true := by
  simp only [rawvalue16,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value17_value19 : byteLess rawvalue17 rawvalue19 = true := by
  simp only [rawvalue17,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value25 : nodes value25 = 25 := by
  change 1 + (nodes value7 + nodes value13 + (nodes value14 + nodes value15 + (nodes value16 + nodes value13 + (nodes value17 + nodes value18 + (nodes value19 + nodes value24 + 0))))) = 25
  simp only [nodes_value7,nodes_value13,nodes_value14,nodes_value15,nodes_value16,nodes_value17,nodes_value18,nodes_value19,nodes_value24]
  all_goals decide +kernel
theorem depth_value25 : depth value25 = 3 := by
  change max (max (1 + depth value7) (1 + depth value13)) (max (max (1 + depth value14) (1 + depth value15)) (max (max (1 + depth value16) (1 + depth value13)) (max (max (1 + depth value17) (1 + depth value18)) (max (max (1 + depth value19) (1 + depth value24)) (0))))) = 3
  simp only [depth_value7,depth_value13,depth_value14,depth_value15,depth_value16,depth_value17,depth_value18,depth_value19,depth_value24]
  all_goals decide +kernel
theorem canonical_value25 : canonical models value25 = true := by
  change ((canonical models value7 && canonical models value13 && (canonical models value14 && canonical models value15 && (canonical models value16 && canonical models value13 && (canonical models value17 && canonical models value18 && (canonical models value19 && canonical models value24 && true))))) && ordered [encode value7,encode value14,encode value16,encode value17,encode value19]) = true
  simp only [canonical_value7,canonical_value13,canonical_value14,canonical_value15,canonical_value16,canonical_value17,canonical_value18,canonical_value19,canonical_value24,encoded_value7,encoded_value14,encoded_value16,encoded_value17,encoded_value19]
  simp only [ordered,List.all_cons,List.all_nil,order_value7_value14,order_value7_value16,order_value7_value17,order_value7_value19,order_value14_value16,order_value14_value17,order_value14_value19,order_value16_value17,order_value16_value19,order_value17_value19,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value25 : rawvalue25.length = 429 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value7) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value13) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value14) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value15) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value16) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value13) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value17) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value18) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value19) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value24) (show ([93] : Bytes).length = 1 from by decide +kernel)))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value26 : Value := .text "members"
noncomputable def rawvalue26 : Bytes := asciiBytes "[\"str\",\"members\"]"
theorem encoded_value26 : encode value26 = rawvalue26 := by
  all_goals rfl
theorem nodes_value26 : nodes value26 = 1 := by rfl
theorem depth_value26 : depth value26 = 0 := by rfl
theorem canonical_value26 : canonical models value26 = true := by decide +kernel
theorem rawLength_value26 : rawvalue26.length = 17 := by
  decide +kernel
noncomputable def value27 : Value := .set (.cons value11 .nil)
noncomputable def rawvalue27 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue11] ++ [93,93]
theorem encoded_value27 : encode value27 = rawvalue27 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value11] ++ [93,93] = _
  simp only [encoded_value11]
  all_goals rfl
theorem nodes_value27 : nodes value27 = 2 := by
  change 1 + (nodes value11 + 0) = 2
  simp only [nodes_value11]
  all_goals decide +kernel
theorem depth_value27 : depth value27 = 1 := by
  change max (1 + depth value11) (0) = 1
  simp only [depth_value11]
  all_goals decide +kernel
theorem canonical_value27 : canonical models value27 = true := by
  change ((canonical models value11 && true) && ordered [encode value11]) = true
  simp only [canonical_value11,encoded_value11]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value27 : rawvalue27.length = 24 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value11)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value28 : Value := .text "normEvidence"
noncomputable def rawvalue28 : Bytes := asciiBytes "[\"str\",\"normEvidence\"]"
theorem encoded_value28 : encode value28 = rawvalue28 := by
  all_goals rfl
theorem nodes_value28 : nodes value28 = 1 := by rfl
theorem depth_value28 : depth value28 = 0 := by rfl
theorem canonical_value28 : canonical models value28 = true := by decide +kernel
theorem rawLength_value28 : rawvalue28.length = 22 := by
  decide +kernel
noncomputable def value29 : Value := .model "norm1"
noncomputable def rawvalue29 : Bytes := asciiBytes "[\"model\",\"norm1\"]"
theorem encoded_value29 : encode value29 = rawvalue29 := by
  all_goals rfl
theorem nodes_value29 : nodes value29 = 1 := by rfl
theorem depth_value29 : depth value29 = 0 := by rfl
theorem canonical_value29 : canonical models value29 = true := by decide +kernel
theorem rawLength_value29 : rawvalue29.length = 17 := by
  decide +kernel
noncomputable def value30 : Value := .text "seed"
noncomputable def rawvalue30 : Bytes := asciiBytes "[\"str\",\"seed\"]"
theorem encoded_value30 : encode value30 = rawvalue30 := by
  all_goals rfl
theorem nodes_value30 : nodes value30 = 1 := by rfl
theorem depth_value30 : depth value30 = 0 := by rfl
theorem canonical_value30 : canonical models value30 = true := by decide +kernel
theorem rawLength_value30 : rawvalue30.length = 14 := by
  decide +kernel
noncomputable def value31 : Value := .text "value"
noncomputable def rawvalue31 : Bytes := asciiBytes "[\"str\",\"value\"]"
theorem encoded_value31 : encode value31 = rawvalue31 := by
  all_goals rfl
theorem nodes_value31 : nodes value31 = 1 := by rfl
theorem depth_value31 : depth value31 = 0 := by rfl
theorem canonical_value31 : canonical models value31 = true := by decide +kernel
theorem rawLength_value31 : rawvalue31.length = 15 := by
  decide +kernel
noncomputable def value32 : Value := .model "seed1"
noncomputable def rawvalue32 : Bytes := asciiBytes "[\"model\",\"seed1\"]"
theorem encoded_value32 : encode value32 = rawvalue32 := by
  all_goals rfl
theorem nodes_value32 : nodes value32 = 1 := by rfl
theorem depth_value32 : depth value32 = 0 := by rfl
theorem canonical_value32 : canonical models value32 = true := by decide +kernel
theorem rawLength_value32 : rawvalue32.length = 17 := by
  decide +kernel
noncomputable def value33 : Value := .function (.cons value20 value21 (.cons value6 value25 (.cons value31 value32 .nil)))
noncomputable def rawvalue33 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue20 ++ [44] ++ rawvalue21 ++ [93]),([91] ++ rawvalue6 ++ [44] ++ rawvalue25 ++ [93]),([91] ++ rawvalue31 ++ [44] ++ rawvalue32 ++ [93])] ++ [93,93]
theorem encoded_value33 : encode value33 = rawvalue33 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value20 ++ [44] ++ encode value21 ++ [93]),([91] ++ encode value6 ++ [44] ++ encode value25 ++ [93]),([91] ++ encode value31 ++ [44] ++ encode value32 ++ [93])] ++ [93,93] = _
  simp only [encoded_value20,encoded_value21,encoded_value6,encoded_value25,encoded_value31,encoded_value32]
  all_goals rfl
theorem order_value20_value6 : byteLess rawvalue20 rawvalue6 = true := by
  simp only [rawvalue20,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value20_value31 : byteLess rawvalue20 rawvalue31 = true := by
  simp only [rawvalue20,rawvalue31,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value6_value31 : byteLess rawvalue6 rawvalue31 = true := by
  simp only [rawvalue6,rawvalue31,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value33 : nodes value33 = 31 := by
  change 1 + (nodes value20 + nodes value21 + (nodes value6 + nodes value25 + (nodes value31 + nodes value32 + 0))) = 31
  simp only [nodes_value20,nodes_value21,nodes_value6,nodes_value25,nodes_value31,nodes_value32]
  all_goals decide +kernel
theorem depth_value33 : depth value33 = 4 := by
  change max (max (1 + depth value20) (1 + depth value21)) (max (max (1 + depth value6) (1 + depth value25)) (max (max (1 + depth value31) (1 + depth value32)) (0))) = 4
  simp only [depth_value20,depth_value21,depth_value6,depth_value25,depth_value31,depth_value32]
  all_goals decide +kernel
theorem canonical_value33 : canonical models value33 = true := by
  change ((canonical models value20 && canonical models value21 && (canonical models value6 && canonical models value25 && (canonical models value31 && canonical models value32 && true))) && ordered [encode value20,encode value6,encode value31]) = true
  simp only [canonical_value20,canonical_value21,canonical_value6,canonical_value25,canonical_value31,canonical_value32,encoded_value20,encoded_value6,encoded_value31]
  simp only [ordered,List.all_cons,List.all_nil,order_value20_value6,order_value20_value31,order_value6_value31,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value33 : rawvalue33.length = 528 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value20) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value21) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value6) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value25) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value31) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value32) (show ([93] : Bytes).length = 1 from by decide +kernel)))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value34 : Value := .function (.cons value6 value25 (.cons value26 value27 (.cons value28 value29 (.cons value30 value33 .nil))))
noncomputable def rawvalue34 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue6 ++ [44] ++ rawvalue25 ++ [93]),([91] ++ rawvalue26 ++ [44] ++ rawvalue27 ++ [93]),([91] ++ rawvalue28 ++ [44] ++ rawvalue29 ++ [93]),([91] ++ rawvalue30 ++ [44] ++ rawvalue33 ++ [93])] ++ [93,93]
theorem encoded_value34 : encode value34 = rawvalue34 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value6 ++ [44] ++ encode value25 ++ [93]),([91] ++ encode value26 ++ [44] ++ encode value27 ++ [93]),([91] ++ encode value28 ++ [44] ++ encode value29 ++ [93]),([91] ++ encode value30 ++ [44] ++ encode value33 ++ [93])] ++ [93,93] = _
  simp only [encoded_value6,encoded_value25,encoded_value26,encoded_value27,encoded_value28,encoded_value29,encoded_value30,encoded_value33]
  all_goals rfl
theorem order_value6_value26 : byteLess rawvalue6 rawvalue26 = true := by
  simp only [rawvalue6,rawvalue26,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value6_value28 : byteLess rawvalue6 rawvalue28 = true := by
  simp only [rawvalue6,rawvalue28,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value6_value30 : byteLess rawvalue6 rawvalue30 = true := by
  simp only [rawvalue6,rawvalue30,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value26_value28 : byteLess rawvalue26 rawvalue28 = true := by
  simp only [rawvalue26,rawvalue28,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value26_value30 : byteLess rawvalue26 rawvalue30 = true := by
  simp only [rawvalue26,rawvalue30,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value28_value30 : byteLess rawvalue28 rawvalue30 = true := by
  simp only [rawvalue28,rawvalue30,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value34 : nodes value34 = 64 := by
  change 1 + (nodes value6 + nodes value25 + (nodes value26 + nodes value27 + (nodes value28 + nodes value29 + (nodes value30 + nodes value33 + 0)))) = 64
  simp only [nodes_value6,nodes_value25,nodes_value26,nodes_value27,nodes_value28,nodes_value29,nodes_value30,nodes_value33]
  all_goals decide +kernel
theorem depth_value34 : depth value34 = 5 := by
  change max (max (1 + depth value6) (1 + depth value25)) (max (max (1 + depth value26) (1 + depth value27)) (max (max (1 + depth value28) (1 + depth value29)) (max (max (1 + depth value30) (1 + depth value33)) (0)))) = 5
  simp only [depth_value6,depth_value25,depth_value26,depth_value27,depth_value28,depth_value29,depth_value30,depth_value33]
  all_goals decide +kernel
theorem canonical_value34 : canonical models value34 = true := by
  change ((canonical models value6 && canonical models value25 && (canonical models value26 && canonical models value27 && (canonical models value28 && canonical models value29 && (canonical models value30 && canonical models value33 && true)))) && ordered [encode value6,encode value26,encode value28,encode value30]) = true
  simp only [canonical_value6,canonical_value25,canonical_value26,canonical_value27,canonical_value28,canonical_value29,canonical_value30,canonical_value33,encoded_value6,encoded_value26,encoded_value28,encoded_value30]
  simp only [ordered,List.all_cons,List.all_nil,order_value6_value26,order_value6_value28,order_value6_value30,order_value26_value28,order_value26_value30,order_value28_value30,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value34 : rawvalue34.length = 1089 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value6) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value25) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value26) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value27) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value28) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value29) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value30) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value33) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value35 : Value := .function (.cons value3 value4 (.cons value5 value34 (.cons value6 value25 (.cons value26 value27 (.cons value30 value33 .nil)))))
noncomputable def rawvalue35 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue3 ++ [44] ++ rawvalue4 ++ [93]),([91] ++ rawvalue5 ++ [44] ++ rawvalue34 ++ [93]),([91] ++ rawvalue6 ++ [44] ++ rawvalue25 ++ [93]),([91] ++ rawvalue26 ++ [44] ++ rawvalue27 ++ [93]),([91] ++ rawvalue30 ++ [44] ++ rawvalue33 ++ [93])] ++ [93,93]
theorem encoded_value35 : encode value35 = rawvalue35 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value3 ++ [44] ++ encode value4 ++ [93]),([91] ++ encode value5 ++ [44] ++ encode value34 ++ [93]),([91] ++ encode value6 ++ [44] ++ encode value25 ++ [93]),([91] ++ encode value26 ++ [44] ++ encode value27 ++ [93]),([91] ++ encode value30 ++ [44] ++ encode value33 ++ [93])] ++ [93,93] = _
  simp only [encoded_value3,encoded_value4,encoded_value5,encoded_value34,encoded_value6,encoded_value25,encoded_value26,encoded_value27,encoded_value30,encoded_value33]
  all_goals rfl
theorem order_value3_value5 : byteLess rawvalue3 rawvalue5 = true := by
  simp only [rawvalue3,rawvalue5,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value3_value6 : byteLess rawvalue3 rawvalue6 = true := by
  simp only [rawvalue3,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value3_value26 : byteLess rawvalue3 rawvalue26 = true := by
  simp only [rawvalue3,rawvalue26,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value3_value30 : byteLess rawvalue3 rawvalue30 = true := by
  simp only [rawvalue3,rawvalue30,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value5_value6 : byteLess rawvalue5 rawvalue6 = true := by
  simp only [rawvalue5,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value5_value26 : byteLess rawvalue5 rawvalue26 = true := by
  simp only [rawvalue5,rawvalue26,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value5_value30 : byteLess rawvalue5 rawvalue30 = true := by
  simp only [rawvalue5,rawvalue30,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value35 : nodes value35 = 129 := by
  change 1 + (nodes value3 + nodes value4 + (nodes value5 + nodes value34 + (nodes value6 + nodes value25 + (nodes value26 + nodes value27 + (nodes value30 + nodes value33 + 0))))) = 129
  simp only [nodes_value3,nodes_value4,nodes_value5,nodes_value34,nodes_value6,nodes_value25,nodes_value26,nodes_value27,nodes_value30,nodes_value33]
  all_goals decide +kernel
theorem depth_value35 : depth value35 = 6 := by
  change max (max (1 + depth value3) (1 + depth value4)) (max (max (1 + depth value5) (1 + depth value34)) (max (max (1 + depth value6) (1 + depth value25)) (max (max (1 + depth value26) (1 + depth value27)) (max (max (1 + depth value30) (1 + depth value33)) (0))))) = 6
  simp only [depth_value3,depth_value4,depth_value5,depth_value34,depth_value6,depth_value25,depth_value26,depth_value27,depth_value30,depth_value33]
  all_goals decide +kernel
theorem canonical_value35 : canonical models value35 = true := by
  change ((canonical models value3 && canonical models value4 && (canonical models value5 && canonical models value34 && (canonical models value6 && canonical models value25 && (canonical models value26 && canonical models value27 && (canonical models value30 && canonical models value33 && true))))) && ordered [encode value3,encode value5,encode value6,encode value26,encode value30]) = true
  simp only [canonical_value3,canonical_value4,canonical_value5,canonical_value34,canonical_value6,canonical_value25,canonical_value26,canonical_value27,canonical_value30,canonical_value33,encoded_value3,encoded_value5,encoded_value6,encoded_value26,encoded_value30]
  simp only [ordered,List.all_cons,List.all_nil,order_value3_value5,order_value3_value6,order_value3_value26,order_value3_value30,order_value5_value6,order_value5_value26,order_value5_value30,order_value6_value26,order_value6_value30,order_value26_value30,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value35 : rawvalue35.length = 2201 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value3) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value4) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value5) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value34) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value6) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value25) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value26) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value27) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value30) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value33) (show ([93] : Bytes).length = 1 from by decide +kernel)))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value36 : Value := .text "signers"
noncomputable def rawvalue36 : Bytes := asciiBytes "[\"str\",\"signers\"]"
theorem encoded_value36 : encode value36 = rawvalue36 := by
  all_goals rfl
theorem nodes_value36 : nodes value36 = 1 := by rfl
theorem depth_value36 : depth value36 = 0 := by rfl
theorem canonical_value36 : canonical models value36 = true := by decide +kernel
theorem rawLength_value36 : rawvalue36.length = 17 := by
  decide +kernel
noncomputable def value37 : Value := .model "v1"
noncomputable def rawvalue37 : Bytes := asciiBytes "[\"model\",\"v1\"]"
theorem encoded_value37 : encode value37 = rawvalue37 := by
  all_goals rfl
theorem nodes_value37 : nodes value37 = 1 := by rfl
theorem depth_value37 : depth value37 = 0 := by rfl
theorem canonical_value37 : canonical models value37 = true := by decide +kernel
theorem rawLength_value37 : rawvalue37.length = 14 := by
  decide +kernel
noncomputable def value38 : Value := .model "v2"
noncomputable def rawvalue38 : Bytes := asciiBytes "[\"model\",\"v2\"]"
theorem encoded_value38 : encode value38 = rawvalue38 := by
  all_goals rfl
theorem nodes_value38 : nodes value38 = 1 := by rfl
theorem depth_value38 : depth value38 = 0 := by rfl
theorem canonical_value38 : canonical models value38 = true := by decide +kernel
theorem rawLength_value38 : rawvalue38.length = 14 := by
  decide +kernel
noncomputable def value39 : Value := .model "v3"
noncomputable def rawvalue39 : Bytes := asciiBytes "[\"model\",\"v3\"]"
theorem encoded_value39 : encode value39 = rawvalue39 := by
  all_goals rfl
theorem nodes_value39 : nodes value39 = 1 := by rfl
theorem depth_value39 : depth value39 = 0 := by rfl
theorem canonical_value39 : canonical models value39 = true := by decide +kernel
theorem rawLength_value39 : rawvalue39.length = 14 := by
  decide +kernel
noncomputable def value40 : Value := .set (.cons value37 (.cons value38 (.cons value39 .nil)))
noncomputable def rawvalue40 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue37,rawvalue38,rawvalue39] ++ [93,93]
theorem encoded_value40 : encode value40 = rawvalue40 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value37,encode value38,encode value39] ++ [93,93] = _
  simp only [encoded_value37,encoded_value38,encoded_value39]
  all_goals rfl
theorem order_value37_value38 : byteLess rawvalue37 rawvalue38 = true := by
  simp only [rawvalue37,rawvalue38,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value37_value39 : byteLess rawvalue37 rawvalue39 = true := by
  simp only [rawvalue37,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value38_value39 : byteLess rawvalue38 rawvalue39 = true := by
  simp only [rawvalue38,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value40 : nodes value40 = 4 := by
  change 1 + (nodes value37 + (nodes value38 + (nodes value39 + 0))) = 4
  simp only [nodes_value37,nodes_value38,nodes_value39]
  all_goals decide +kernel
theorem depth_value40 : depth value40 = 1 := by
  change max (1 + depth value37) (max (1 + depth value38) (max (1 + depth value39) (0))) = 1
  simp only [depth_value37,depth_value38,depth_value39]
  all_goals decide +kernel
theorem canonical_value40 : canonical models value40 = true := by
  change ((canonical models value37 && (canonical models value38 && (canonical models value39 && true))) && ordered [encode value37,encode value38,encode value39]) = true
  simp only [canonical_value37,canonical_value38,canonical_value39,encoded_value37,encoded_value38,encoded_value39]
  simp only [ordered,List.all_cons,List.all_nil,order_value37_value38,order_value37_value39,order_value38_value39,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value40 : rawvalue40.length = 54 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value37 (commaConsLength rawLength_value38 (commaSingletonLength rawLength_value39)))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value41 : Value := .function (.cons value2 value35 (.cons value36 value40 .nil))
noncomputable def rawvalue41 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue35 ++ [93]),([91] ++ rawvalue36 ++ [44] ++ rawvalue40 ++ [93])] ++ [93,93]
theorem encoded_value41 : encode value41 = rawvalue41 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value35 ++ [93]),([91] ++ encode value36 ++ [44] ++ encode value40 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value35,encoded_value36,encoded_value40]
  all_goals rfl
theorem order_value2_value36 : byteLess rawvalue2 rawvalue36 = true := by
  simp only [rawvalue2,rawvalue36,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value41 : nodes value41 = 136 := by
  change 1 + (nodes value2 + nodes value35 + (nodes value36 + nodes value40 + 0)) = 136
  simp only [nodes_value2,nodes_value35,nodes_value36,nodes_value40]
  all_goals decide +kernel
theorem depth_value41 : depth value41 = 7 := by
  change max (max (1 + depth value2) (1 + depth value35)) (max (max (1 + depth value36) (1 + depth value40)) (0)) = 7
  simp only [depth_value2,depth_value35,depth_value36,depth_value40]
  all_goals decide +kernel
theorem canonical_value41 : canonical models value41 = true := by
  change ((canonical models value2 && canonical models value35 && (canonical models value36 && canonical models value40 && true)) && ordered [encode value2,encode value36]) = true
  simp only [canonical_value2,canonical_value35,canonical_value36,canonical_value40,encoded_value2,encoded_value36]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value36,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value41 : rawvalue41.length = 2303 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value35) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value36) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value40) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value42 : Value := .set (.cons value41 .nil)
noncomputable def rawvalue42 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue41] ++ [93,93]
theorem encoded_value42 : encode value42 = rawvalue42 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value41] ++ [93,93] = _
  simp only [encoded_value41]
  all_goals rfl
theorem nodes_value42 : nodes value42 = 137 := by
  change 1 + (nodes value41 + 0) = 137
  simp only [nodes_value41]
  all_goals decide +kernel
theorem depth_value42 : depth value42 = 8 := by
  change max (1 + depth value41) (0) = 8
  simp only [depth_value41]
  all_goals decide +kernel
theorem canonical_value42 : canonical models value42 = true := by
  change ((canonical models value41 && true) && ordered [encode value41]) = true
  simp only [canonical_value41,encoded_value41]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value42 : rawvalue42.length = 2313 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value41)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value43 : Value := .model "v4"
noncomputable def rawvalue43 : Bytes := asciiBytes "[\"model\",\"v4\"]"
theorem encoded_value43 : encode value43 = rawvalue43 := by
  all_goals rfl
theorem nodes_value43 : nodes value43 = 1 := by rfl
theorem depth_value43 : depth value43 = 0 := by rfl
theorem canonical_value43 : canonical models value43 = true := by decide +kernel
theorem rawLength_value43 : rawvalue43.length = 14 := by
  decide +kernel
noncomputable def value44 : Value := .set (.cons value37 (.cons value38 (.cons value39 (.cons value43 .nil))))
noncomputable def rawvalue44 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue37,rawvalue38,rawvalue39,rawvalue43] ++ [93,93]
theorem encoded_value44 : encode value44 = rawvalue44 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value37,encode value38,encode value39,encode value43] ++ [93,93] = _
  simp only [encoded_value37,encoded_value38,encoded_value39,encoded_value43]
  all_goals rfl
theorem order_value37_value43 : byteLess rawvalue37 rawvalue43 = true := by
  simp only [rawvalue37,rawvalue43,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value38_value43 : byteLess rawvalue38 rawvalue43 = true := by
  simp only [rawvalue38,rawvalue43,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value39_value43 : byteLess rawvalue39 rawvalue43 = true := by
  simp only [rawvalue39,rawvalue43,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value44 : nodes value44 = 5 := by
  change 1 + (nodes value37 + (nodes value38 + (nodes value39 + (nodes value43 + 0)))) = 5
  simp only [nodes_value37,nodes_value38,nodes_value39,nodes_value43]
  all_goals decide +kernel
theorem depth_value44 : depth value44 = 1 := by
  change max (1 + depth value37) (max (1 + depth value38) (max (1 + depth value39) (max (1 + depth value43) (0)))) = 1
  simp only [depth_value37,depth_value38,depth_value39,depth_value43]
  all_goals decide +kernel
theorem canonical_value44 : canonical models value44 = true := by
  change ((canonical models value37 && (canonical models value38 && (canonical models value39 && (canonical models value43 && true)))) && ordered [encode value37,encode value38,encode value39,encode value43]) = true
  simp only [canonical_value37,canonical_value38,canonical_value39,canonical_value43,encoded_value37,encoded_value38,encoded_value39,encoded_value43]
  simp only [ordered,List.all_cons,List.all_nil,order_value37_value38,order_value37_value39,order_value37_value43,order_value38_value39,order_value38_value43,order_value39_value43,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value44 : rawvalue44.length = 69 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value37 (commaConsLength rawLength_value38 (commaConsLength rawLength_value39 (commaSingletonLength rawLength_value43))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value45 : Value := .text "validator"
noncomputable def rawvalue45 : Bytes := asciiBytes "[\"str\",\"validator\"]"
theorem encoded_value45 : encode value45 = rawvalue45 := by
  all_goals rfl
theorem nodes_value45 : nodes value45 = 1 := by rfl
theorem depth_value45 : depth value45 = 0 := by rfl
theorem canonical_value45 : canonical models value45 = true := by decide +kernel
theorem rawLength_value45 : rawvalue45.length = 19 := by
  decide +kernel
noncomputable def value46 : Value := .function (.cons value2 value35 (.cons value45 value37 .nil))
noncomputable def rawvalue46 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue35 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue37 ++ [93])] ++ [93,93]
theorem encoded_value46 : encode value46 = rawvalue46 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value35 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value37 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value35,encoded_value45,encoded_value37]
  all_goals rfl
theorem order_value2_value45 : byteLess rawvalue2 rawvalue45 = true := by
  simp only [rawvalue2,rawvalue45,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value46 : nodes value46 = 133 := by
  change 1 + (nodes value2 + nodes value35 + (nodes value45 + nodes value37 + 0)) = 133
  simp only [nodes_value2,nodes_value35,nodes_value45,nodes_value37]
  all_goals decide +kernel
theorem depth_value46 : depth value46 = 7 := by
  change max (max (1 + depth value2) (1 + depth value35)) (max (max (1 + depth value45) (1 + depth value37)) (0)) = 7
  simp only [depth_value2,depth_value35,depth_value45,depth_value37]
  all_goals decide +kernel
theorem canonical_value46 : canonical models value46 = true := by
  change ((canonical models value2 && canonical models value35 && (canonical models value45 && canonical models value37 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value35,canonical_value45,canonical_value37,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value46 : rawvalue46.length = 2265 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value35) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value37) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value47 : Value := .function (.cons value2 value35 (.cons value45 value38 .nil))
noncomputable def rawvalue47 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue35 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue38 ++ [93])] ++ [93,93]
theorem encoded_value47 : encode value47 = rawvalue47 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value35 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value38 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value35,encoded_value45,encoded_value38]
  all_goals rfl
theorem nodes_value47 : nodes value47 = 133 := by
  change 1 + (nodes value2 + nodes value35 + (nodes value45 + nodes value38 + 0)) = 133
  simp only [nodes_value2,nodes_value35,nodes_value45,nodes_value38]
  all_goals decide +kernel
theorem depth_value47 : depth value47 = 7 := by
  change max (max (1 + depth value2) (1 + depth value35)) (max (max (1 + depth value45) (1 + depth value38)) (0)) = 7
  simp only [depth_value2,depth_value35,depth_value45,depth_value38]
  all_goals decide +kernel
theorem canonical_value47 : canonical models value47 = true := by
  change ((canonical models value2 && canonical models value35 && (canonical models value45 && canonical models value38 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value35,canonical_value45,canonical_value38,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value47 : rawvalue47.length = 2265 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value35) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value38) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value48 : Value := .function (.cons value2 value35 (.cons value45 value39 .nil))
noncomputable def rawvalue48 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue35 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue39 ++ [93])] ++ [93,93]
theorem encoded_value48 : encode value48 = rawvalue48 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value35 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value39 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value35,encoded_value45,encoded_value39]
  all_goals rfl
theorem nodes_value48 : nodes value48 = 133 := by
  change 1 + (nodes value2 + nodes value35 + (nodes value45 + nodes value39 + 0)) = 133
  simp only [nodes_value2,nodes_value35,nodes_value45,nodes_value39]
  all_goals decide +kernel
theorem depth_value48 : depth value48 = 7 := by
  change max (max (1 + depth value2) (1 + depth value35)) (max (max (1 + depth value45) (1 + depth value39)) (0)) = 7
  simp only [depth_value2,depth_value35,depth_value45,depth_value39]
  all_goals decide +kernel
theorem canonical_value48 : canonical models value48 = true := by
  change ((canonical models value2 && canonical models value35 && (canonical models value45 && canonical models value39 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value35,canonical_value45,canonical_value39,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value48 : rawvalue48.length = 2265 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value35) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value39) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value49 : Value := .set (.cons value46 (.cons value47 (.cons value48 .nil)))
noncomputable def rawvalue49 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue46,rawvalue47,rawvalue48] ++ [93,93]
theorem encoded_value49 : encode value49 = rawvalue49 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value46,encode value47,encode value48] ++ [93,93] = _
  simp only [encoded_value46,encoded_value47,encoded_value48]
  all_goals rfl
theorem order_value46_value47 : byteLess rawvalue46 rawvalue47 = true := by
  simp only [rawvalue46,rawvalue47,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue38,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value46_value48 : byteLess rawvalue46 rawvalue48 = true := by
  simp only [rawvalue46,rawvalue48,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value47_value48 : byteLess rawvalue47 rawvalue48 = true := by
  simp only [rawvalue47,rawvalue48,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue38,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value49 : nodes value49 = 400 := by
  change 1 + (nodes value46 + (nodes value47 + (nodes value48 + 0))) = 400
  simp only [nodes_value46,nodes_value47,nodes_value48]
  all_goals decide +kernel
theorem depth_value49 : depth value49 = 8 := by
  change max (1 + depth value46) (max (1 + depth value47) (max (1 + depth value48) (0))) = 8
  simp only [depth_value46,depth_value47,depth_value48]
  all_goals decide +kernel
theorem canonical_value49 : canonical models value49 = true := by
  change ((canonical models value46 && (canonical models value47 && (canonical models value48 && true))) && ordered [encode value46,encode value47,encode value48]) = true
  simp only [canonical_value46,canonical_value47,canonical_value48,encoded_value46,encoded_value47,encoded_value48]
  simp only [ordered,List.all_cons,List.all_nil,order_value46_value47,order_value46_value48,order_value47_value48,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value49 : rawvalue49.length = 6807 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value46 (commaConsLength rawLength_value47 (commaSingletonLength rawLength_value48)))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value50 : Value := .text "shard"
noncomputable def rawvalue50 : Bytes := asciiBytes "[\"str\",\"shard\"]"
theorem encoded_value50 : encode value50 = rawvalue50 := by
  all_goals rfl
theorem nodes_value50 : nodes value50 = 1 := by rfl
theorem depth_value50 : depth value50 = 0 := by rfl
theorem canonical_value50 : canonical models value50 = true := by decide +kernel
theorem rawLength_value50 : rawvalue50.length = 15 := by
  decide +kernel
noncomputable def value51 : Value := .model "shard1"
noncomputable def rawvalue51 : Bytes := asciiBytes "[\"model\",\"shard1\"]"
theorem encoded_value51 : encode value51 = rawvalue51 := by
  all_goals rfl
theorem nodes_value51 : nodes value51 = 1 := by rfl
theorem depth_value51 : depth value51 = 0 := by rfl
theorem canonical_value51 : canonical models value51 = true := by decide +kernel
theorem rawLength_value51 : rawvalue51.length = 18 := by
  decide +kernel
noncomputable def value52 : Value := .text "storage"
noncomputable def rawvalue52 : Bytes := asciiBytes "[\"str\",\"storage\"]"
theorem encoded_value52 : encode value52 = rawvalue52 := by
  all_goals rfl
theorem nodes_value52 : nodes value52 = 1 := by rfl
theorem depth_value52 : depth value52 = 0 := by rfl
theorem canonical_value52 : canonical models value52 = true := by decide +kernel
theorem rawLength_value52 : rawvalue52.length = 17 := by
  decide +kernel
noncomputable def value53 : Value := .model "s1"
noncomputable def rawvalue53 : Bytes := asciiBytes "[\"model\",\"s1\"]"
theorem encoded_value53 : encode value53 = rawvalue53 := by
  all_goals rfl
theorem nodes_value53 : nodes value53 = 1 := by rfl
theorem depth_value53 : depth value53 = 0 := by rfl
theorem canonical_value53 : canonical models value53 = true := by decide +kernel
theorem rawLength_value53 : rawvalue53.length = 14 := by
  decide +kernel
noncomputable def value54 : Value := .function (.cons value8 value9 (.cons value50 value51 (.cons value52 value53 (.cons value10 value11 .nil))))
noncomputable def rawvalue54 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue8 ++ [44] ++ rawvalue9 ++ [93]),([91] ++ rawvalue50 ++ [44] ++ rawvalue51 ++ [93]),([91] ++ rawvalue52 ++ [44] ++ rawvalue53 ++ [93]),([91] ++ rawvalue10 ++ [44] ++ rawvalue11 ++ [93])] ++ [93,93]
theorem encoded_value54 : encode value54 = rawvalue54 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value8 ++ [44] ++ encode value9 ++ [93]),([91] ++ encode value50 ++ [44] ++ encode value51 ++ [93]),([91] ++ encode value52 ++ [44] ++ encode value53 ++ [93]),([91] ++ encode value10 ++ [44] ++ encode value11 ++ [93])] ++ [93,93] = _
  simp only [encoded_value8,encoded_value9,encoded_value50,encoded_value51,encoded_value52,encoded_value53,encoded_value10,encoded_value11]
  all_goals rfl
theorem order_value8_value50 : byteLess rawvalue8 rawvalue50 = true := by
  simp only [rawvalue8,rawvalue50,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value8_value52 : byteLess rawvalue8 rawvalue52 = true := by
  simp only [rawvalue8,rawvalue52,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value50_value52 : byteLess rawvalue50 rawvalue52 = true := by
  simp only [rawvalue50,rawvalue52,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value50_value10 : byteLess rawvalue50 rawvalue10 = true := by
  simp only [rawvalue50,rawvalue10,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value52_value10 : byteLess rawvalue52 rawvalue10 = true := by
  simp only [rawvalue52,rawvalue10,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value54 : nodes value54 = 9 := by
  change 1 + (nodes value8 + nodes value9 + (nodes value50 + nodes value51 + (nodes value52 + nodes value53 + (nodes value10 + nodes value11 + 0)))) = 9
  simp only [nodes_value8,nodes_value9,nodes_value50,nodes_value51,nodes_value52,nodes_value53,nodes_value10,nodes_value11]
  all_goals decide +kernel
theorem depth_value54 : depth value54 = 1 := by
  change max (max (1 + depth value8) (1 + depth value9)) (max (max (1 + depth value50) (1 + depth value51)) (max (max (1 + depth value52) (1 + depth value53)) (max (max (1 + depth value10) (1 + depth value11)) (0)))) = 1
  simp only [depth_value8,depth_value9,depth_value50,depth_value51,depth_value52,depth_value53,depth_value10,depth_value11]
  all_goals decide +kernel
theorem canonical_value54 : canonical models value54 = true := by
  change ((canonical models value8 && canonical models value9 && (canonical models value50 && canonical models value51 && (canonical models value52 && canonical models value53 && (canonical models value10 && canonical models value11 && true)))) && ordered [encode value8,encode value50,encode value52,encode value10]) = true
  simp only [canonical_value8,canonical_value9,canonical_value50,canonical_value51,canonical_value52,canonical_value53,canonical_value10,canonical_value11,encoded_value8,encoded_value50,encoded_value52,encoded_value10]
  simp only [ordered,List.all_cons,List.all_nil,order_value8_value50,order_value8_value52,order_value8_value10,order_value50_value52,order_value50_value10,order_value52_value10,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value54 : rawvalue54.length = 156 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value8) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value9) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value50) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value51) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value52) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value53) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value10) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value11) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value55 : Value := .model "shard2"
noncomputable def rawvalue55 : Bytes := asciiBytes "[\"model\",\"shard2\"]"
theorem encoded_value55 : encode value55 = rawvalue55 := by
  all_goals rfl
theorem nodes_value55 : nodes value55 = 1 := by rfl
theorem depth_value55 : depth value55 = 0 := by rfl
theorem canonical_value55 : canonical models value55 = true := by decide +kernel
theorem rawLength_value55 : rawvalue55.length = 18 := by
  decide +kernel
noncomputable def value56 : Value := .function (.cons value8 value9 (.cons value50 value55 (.cons value52 value53 (.cons value10 value11 .nil))))
noncomputable def rawvalue56 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue8 ++ [44] ++ rawvalue9 ++ [93]),([91] ++ rawvalue50 ++ [44] ++ rawvalue55 ++ [93]),([91] ++ rawvalue52 ++ [44] ++ rawvalue53 ++ [93]),([91] ++ rawvalue10 ++ [44] ++ rawvalue11 ++ [93])] ++ [93,93]
theorem encoded_value56 : encode value56 = rawvalue56 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value8 ++ [44] ++ encode value9 ++ [93]),([91] ++ encode value50 ++ [44] ++ encode value55 ++ [93]),([91] ++ encode value52 ++ [44] ++ encode value53 ++ [93]),([91] ++ encode value10 ++ [44] ++ encode value11 ++ [93])] ++ [93,93] = _
  simp only [encoded_value8,encoded_value9,encoded_value50,encoded_value55,encoded_value52,encoded_value53,encoded_value10,encoded_value11]
  all_goals rfl
theorem nodes_value56 : nodes value56 = 9 := by
  change 1 + (nodes value8 + nodes value9 + (nodes value50 + nodes value55 + (nodes value52 + nodes value53 + (nodes value10 + nodes value11 + 0)))) = 9
  simp only [nodes_value8,nodes_value9,nodes_value50,nodes_value55,nodes_value52,nodes_value53,nodes_value10,nodes_value11]
  all_goals decide +kernel
theorem depth_value56 : depth value56 = 1 := by
  change max (max (1 + depth value8) (1 + depth value9)) (max (max (1 + depth value50) (1 + depth value55)) (max (max (1 + depth value52) (1 + depth value53)) (max (max (1 + depth value10) (1 + depth value11)) (0)))) = 1
  simp only [depth_value8,depth_value9,depth_value50,depth_value55,depth_value52,depth_value53,depth_value10,depth_value11]
  all_goals decide +kernel
theorem canonical_value56 : canonical models value56 = true := by
  change ((canonical models value8 && canonical models value9 && (canonical models value50 && canonical models value55 && (canonical models value52 && canonical models value53 && (canonical models value10 && canonical models value11 && true)))) && ordered [encode value8,encode value50,encode value52,encode value10]) = true
  simp only [canonical_value8,canonical_value9,canonical_value50,canonical_value55,canonical_value52,canonical_value53,canonical_value10,canonical_value11,encoded_value8,encoded_value50,encoded_value52,encoded_value10]
  simp only [ordered,List.all_cons,List.all_nil,order_value8_value50,order_value8_value52,order_value8_value10,order_value50_value52,order_value50_value10,order_value52_value10,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value56 : rawvalue56.length = 156 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value8) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value9) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value50) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value55) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value52) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value53) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value10) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value11) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value57 : Value := .set (.cons value54 (.cons value56 .nil))
noncomputable def rawvalue57 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue54,rawvalue56] ++ [93,93]
theorem encoded_value57 : encode value57 = rawvalue57 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value54,encode value56] ++ [93,93] = _
  simp only [encoded_value54,encoded_value56]
  all_goals rfl
theorem order_value54_value56 : byteLess rawvalue54 rawvalue56 = true := by
  simp only [rawvalue54,rawvalue56,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value57 : nodes value57 = 19 := by
  change 1 + (nodes value54 + (nodes value56 + 0)) = 19
  simp only [nodes_value54,nodes_value56]
  all_goals decide +kernel
theorem depth_value57 : depth value57 = 2 := by
  change max (1 + depth value54) (max (1 + depth value56) (0)) = 2
  simp only [depth_value54,depth_value56]
  all_goals decide +kernel
theorem canonical_value57 : canonical models value57 = true := by
  change ((canonical models value54 && (canonical models value56 && true)) && ordered [encode value54,encode value56]) = true
  simp only [canonical_value54,canonical_value56,encoded_value54,encoded_value56]
  simp only [ordered,List.all_cons,List.all_nil,order_value54_value56,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value57 : rawvalue57.length = 323 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value54 (commaSingletonLength rawLength_value56))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value58 : Value := .function (.cons value8 value9 (.cons value50 value51 (.cons value52 value53 .nil)))
noncomputable def rawvalue58 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue8 ++ [44] ++ rawvalue9 ++ [93]),([91] ++ rawvalue50 ++ [44] ++ rawvalue51 ++ [93]),([91] ++ rawvalue52 ++ [44] ++ rawvalue53 ++ [93])] ++ [93,93]
theorem encoded_value58 : encode value58 = rawvalue58 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value8 ++ [44] ++ encode value9 ++ [93]),([91] ++ encode value50 ++ [44] ++ encode value51 ++ [93]),([91] ++ encode value52 ++ [44] ++ encode value53 ++ [93])] ++ [93,93] = _
  simp only [encoded_value8,encoded_value9,encoded_value50,encoded_value51,encoded_value52,encoded_value53]
  all_goals rfl
theorem nodes_value58 : nodes value58 = 7 := by
  change 1 + (nodes value8 + nodes value9 + (nodes value50 + nodes value51 + (nodes value52 + nodes value53 + 0))) = 7
  simp only [nodes_value8,nodes_value9,nodes_value50,nodes_value51,nodes_value52,nodes_value53]
  all_goals decide +kernel
theorem depth_value58 : depth value58 = 1 := by
  change max (max (1 + depth value8) (1 + depth value9)) (max (max (1 + depth value50) (1 + depth value51)) (max (max (1 + depth value52) (1 + depth value53)) (0))) = 1
  simp only [depth_value8,depth_value9,depth_value50,depth_value51,depth_value52,depth_value53]
  all_goals decide +kernel
theorem canonical_value58 : canonical models value58 = true := by
  change ((canonical models value8 && canonical models value9 && (canonical models value50 && canonical models value51 && (canonical models value52 && canonical models value53 && true))) && ordered [encode value8,encode value50,encode value52]) = true
  simp only [canonical_value8,canonical_value9,canonical_value50,canonical_value51,canonical_value52,canonical_value53,encoded_value8,encoded_value50,encoded_value52]
  simp only [ordered,List.all_cons,List.all_nil,order_value8_value50,order_value8_value52,order_value50_value52,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value58 : rawvalue58.length = 122 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value8) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value9) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value50) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value51) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value52) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value53) (show ([93] : Bytes).length = 1 from by decide +kernel)))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value59 : Value := .function (.cons value8 value9 (.cons value50 value55 (.cons value52 value53 .nil)))
noncomputable def rawvalue59 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue8 ++ [44] ++ rawvalue9 ++ [93]),([91] ++ rawvalue50 ++ [44] ++ rawvalue55 ++ [93]),([91] ++ rawvalue52 ++ [44] ++ rawvalue53 ++ [93])] ++ [93,93]
theorem encoded_value59 : encode value59 = rawvalue59 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value8 ++ [44] ++ encode value9 ++ [93]),([91] ++ encode value50 ++ [44] ++ encode value55 ++ [93]),([91] ++ encode value52 ++ [44] ++ encode value53 ++ [93])] ++ [93,93] = _
  simp only [encoded_value8,encoded_value9,encoded_value50,encoded_value55,encoded_value52,encoded_value53]
  all_goals rfl
theorem nodes_value59 : nodes value59 = 7 := by
  change 1 + (nodes value8 + nodes value9 + (nodes value50 + nodes value55 + (nodes value52 + nodes value53 + 0))) = 7
  simp only [nodes_value8,nodes_value9,nodes_value50,nodes_value55,nodes_value52,nodes_value53]
  all_goals decide +kernel
theorem depth_value59 : depth value59 = 1 := by
  change max (max (1 + depth value8) (1 + depth value9)) (max (max (1 + depth value50) (1 + depth value55)) (max (max (1 + depth value52) (1 + depth value53)) (0))) = 1
  simp only [depth_value8,depth_value9,depth_value50,depth_value55,depth_value52,depth_value53]
  all_goals decide +kernel
theorem canonical_value59 : canonical models value59 = true := by
  change ((canonical models value8 && canonical models value9 && (canonical models value50 && canonical models value55 && (canonical models value52 && canonical models value53 && true))) && ordered [encode value8,encode value50,encode value52]) = true
  simp only [canonical_value8,canonical_value9,canonical_value50,canonical_value55,canonical_value52,canonical_value53,encoded_value8,encoded_value50,encoded_value52]
  simp only [ordered,List.all_cons,List.all_nil,order_value8_value50,order_value8_value52,order_value50_value52,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value59 : rawvalue59.length = 122 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value8) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value9) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value50) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value55) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value52) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value53) (show ([93] : Bytes).length = 1 from by decide +kernel)))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value60 : Value := .set (.cons value58 (.cons value59 .nil))
noncomputable def rawvalue60 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue58,rawvalue59] ++ [93,93]
theorem encoded_value60 : encode value60 = rawvalue60 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value58,encode value59] ++ [93,93] = _
  simp only [encoded_value58,encoded_value59]
  all_goals rfl
theorem order_value58_value59 : byteLess rawvalue58 rawvalue59 = true := by
  simp only [rawvalue58,rawvalue59,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value60 : nodes value60 = 15 := by
  change 1 + (nodes value58 + (nodes value59 + 0)) = 15
  simp only [nodes_value58,nodes_value59]
  all_goals decide +kernel
theorem depth_value60 : depth value60 = 2 := by
  change max (1 + depth value58) (max (1 + depth value59) (0)) = 2
  simp only [depth_value58,depth_value59]
  all_goals decide +kernel
theorem canonical_value60 : canonical models value60 = true := by
  change ((canonical models value58 && (canonical models value59 && true)) && ordered [encode value58,encode value59]) = true
  simp only [canonical_value58,canonical_value59,encoded_value58,encoded_value59]
  simp only [ordered,List.all_cons,List.all_nil,order_value58_value59,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value60 : rawvalue60.length = 255 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value58 (commaSingletonLength rawLength_value59))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value61 : Value := .set (.cons value43 .nil)
noncomputable def rawvalue61 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue43] ++ [93,93]
theorem encoded_value61 : encode value61 = rawvalue61 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value43] ++ [93,93] = _
  simp only [encoded_value43]
  all_goals rfl
theorem nodes_value61 : nodes value61 = 2 := by
  change 1 + (nodes value43 + 0) = 2
  simp only [nodes_value43]
  all_goals decide +kernel
theorem depth_value61 : depth value61 = 1 := by
  change max (1 + depth value43) (0) = 1
  simp only [depth_value43]
  all_goals decide +kernel
theorem canonical_value61 : canonical models value61 = true := by
  change ((canonical models value43 && true) && ordered [encode value43]) = true
  simp only [canonical_value43,encoded_value43]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value61 : rawvalue61.length = 24 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value43)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value62 : Value := .set (.cons value25 .nil)
noncomputable def rawvalue62 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue25] ++ [93,93]
theorem encoded_value62 : encode value62 = rawvalue62 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value25] ++ [93,93] = _
  simp only [encoded_value25]
  all_goals rfl
theorem nodes_value62 : nodes value62 = 26 := by
  change 1 + (nodes value25 + 0) = 26
  simp only [nodes_value25]
  all_goals decide +kernel
theorem depth_value62 : depth value62 = 4 := by
  change max (1 + depth value25) (0) = 4
  simp only [depth_value25]
  all_goals decide +kernel
theorem canonical_value62 : canonical models value62 = true := by
  change ((canonical models value25 && true) && ordered [encode value25]) = true
  simp only [canonical_value25,encoded_value25]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value62 : rawvalue62.length = 439 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value25)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value63 : Value := .text "leaseEpoch"
noncomputable def rawvalue63 : Bytes := asciiBytes "[\"str\",\"leaseEpoch\"]"
theorem encoded_value63 : encode value63 = rawvalue63 := by
  all_goals rfl
theorem nodes_value63 : nodes value63 = 1 := by rfl
theorem depth_value63 : depth value63 = 0 := by rfl
theorem canonical_value63 : canonical models value63 = true := by decide +kernel
theorem rawLength_value63 : rawvalue63.length = 20 := by
  decide +kernel
noncomputable def value64 : Value := .integer (0)
noncomputable def rawvalue64 : Bytes := asciiBytes "[\"int\",\"0\"]"
theorem encoded_value64 : encode value64 = rawvalue64 := by
  all_goals rfl
theorem nodes_value64 : nodes value64 = 1 := by rfl
theorem depth_value64 : depth value64 = 0 := by rfl
theorem canonical_value64 : canonical models value64 = true := by decide +kernel
theorem rawLength_value64 : rawvalue64.length = 11 := by
  decide +kernel
noncomputable def value65 : Value := .text "worker"
noncomputable def rawvalue65 : Bytes := asciiBytes "[\"str\",\"worker\"]"
theorem encoded_value65 : encode value65 = rawvalue65 := by
  all_goals rfl
theorem nodes_value65 : nodes value65 = 1 := by rfl
theorem depth_value65 : depth value65 = 0 := by rfl
theorem canonical_value65 : canonical models value65 = true := by decide +kernel
theorem rawLength_value65 : rawvalue65.length = 16 := by
  decide +kernel
noncomputable def value66 : Value := .model "w1"
noncomputable def rawvalue66 : Bytes := asciiBytes "[\"model\",\"w1\"]"
theorem encoded_value66 : encode value66 = rawvalue66 := by
  all_goals rfl
theorem nodes_value66 : nodes value66 = 1 := by rfl
theorem depth_value66 : depth value66 = 0 := by rfl
theorem canonical_value66 : canonical models value66 = true := by decide +kernel
theorem rawLength_value66 : rawvalue66.length = 14 := by
  decide +kernel
noncomputable def value67 : Value := .function (.cons value8 value9 (.cons value63 value64 (.cons value10 value11 (.cons value65 value66 .nil))))
noncomputable def rawvalue67 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue8 ++ [44] ++ rawvalue9 ++ [93]),([91] ++ rawvalue63 ++ [44] ++ rawvalue64 ++ [93]),([91] ++ rawvalue10 ++ [44] ++ rawvalue11 ++ [93]),([91] ++ rawvalue65 ++ [44] ++ rawvalue66 ++ [93])] ++ [93,93]
theorem encoded_value67 : encode value67 = rawvalue67 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value8 ++ [44] ++ encode value9 ++ [93]),([91] ++ encode value63 ++ [44] ++ encode value64 ++ [93]),([91] ++ encode value10 ++ [44] ++ encode value11 ++ [93]),([91] ++ encode value65 ++ [44] ++ encode value66 ++ [93])] ++ [93,93] = _
  simp only [encoded_value8,encoded_value9,encoded_value63,encoded_value64,encoded_value10,encoded_value11,encoded_value65,encoded_value66]
  all_goals rfl
theorem order_value8_value63 : byteLess rawvalue8 rawvalue63 = true := by
  simp only [rawvalue8,rawvalue63,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value8_value65 : byteLess rawvalue8 rawvalue65 = true := by
  simp only [rawvalue8,rawvalue65,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value63_value10 : byteLess rawvalue63 rawvalue10 = true := by
  simp only [rawvalue63,rawvalue10,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value63_value65 : byteLess rawvalue63 rawvalue65 = true := by
  simp only [rawvalue63,rawvalue65,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value10_value65 : byteLess rawvalue10 rawvalue65 = true := by
  simp only [rawvalue10,rawvalue65,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value67 : nodes value67 = 9 := by
  change 1 + (nodes value8 + nodes value9 + (nodes value63 + nodes value64 + (nodes value10 + nodes value11 + (nodes value65 + nodes value66 + 0)))) = 9
  simp only [nodes_value8,nodes_value9,nodes_value63,nodes_value64,nodes_value10,nodes_value11,nodes_value65,nodes_value66]
  all_goals decide +kernel
theorem depth_value67 : depth value67 = 1 := by
  change max (max (1 + depth value8) (1 + depth value9)) (max (max (1 + depth value63) (1 + depth value64)) (max (max (1 + depth value10) (1 + depth value11)) (max (max (1 + depth value65) (1 + depth value66)) (0)))) = 1
  simp only [depth_value8,depth_value9,depth_value63,depth_value64,depth_value10,depth_value11,depth_value65,depth_value66]
  all_goals decide +kernel
theorem canonical_value67 : canonical models value67 = true := by
  change ((canonical models value8 && canonical models value9 && (canonical models value63 && canonical models value64 && (canonical models value10 && canonical models value11 && (canonical models value65 && canonical models value66 && true)))) && ordered [encode value8,encode value63,encode value10,encode value65]) = true
  simp only [canonical_value8,canonical_value9,canonical_value63,canonical_value64,canonical_value10,canonical_value11,canonical_value65,canonical_value66,encoded_value8,encoded_value63,encoded_value10,encoded_value65]
  simp only [ordered,List.all_cons,List.all_nil,order_value8_value63,order_value8_value10,order_value8_value65,order_value63_value10,order_value63_value65,order_value10_value65,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value67 : rawvalue67.length = 153 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value8) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value9) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value63) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value64) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value10) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value11) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value65) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value66) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value68 : Value := .set (.cons value67 .nil)
noncomputable def rawvalue68 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue67] ++ [93,93]
theorem encoded_value68 : encode value68 = rawvalue68 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value67] ++ [93,93] = _
  simp only [encoded_value67]
  all_goals rfl
theorem nodes_value68 : nodes value68 = 10 := by
  change 1 + (nodes value67 + 0) = 10
  simp only [nodes_value67]
  all_goals decide +kernel
theorem depth_value68 : depth value68 = 2 := by
  change max (1 + depth value67) (0) = 2
  simp only [depth_value67]
  all_goals decide +kernel
theorem canonical_value68 : canonical models value68 = true := by
  change ((canonical models value67 && true) && ordered [encode value67]) = true
  simp only [canonical_value67,encoded_value67]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value68 : rawvalue68.length = 163 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value67)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value69 : Value := .model "parent1"
noncomputable def rawvalue69 : Bytes := asciiBytes "[\"model\",\"parent1\"]"
theorem encoded_value69 : encode value69 = rawvalue69 := by
  all_goals rfl
theorem nodes_value69 : nodes value69 = 1 := by rfl
theorem depth_value69 : depth value69 = 0 := by rfl
theorem canonical_value69 : canonical models value69 = true := by decide +kernel
theorem rawLength_value69 : rawvalue69.length = 19 := by
  decide +kernel
noncomputable def value70 : Value := .integer (4)
noncomputable def rawvalue70 : Bytes := asciiBytes "[\"int\",\"4\"]"
theorem encoded_value70 : encode value70 = rawvalue70 := by
  all_goals rfl
theorem nodes_value70 : nodes value70 = 1 := by rfl
theorem depth_value70 : depth value70 = 0 := by rfl
theorem canonical_value70 : canonical models value70 = true := by decide +kernel
theorem rawLength_value70 : rawvalue70.length = 11 := by
  decide +kernel
noncomputable def value71 : Value := .function (.cons value37 value70 (.cons value38 value70 (.cons value39 value70 (.cons value43 value64 .nil))))
noncomputable def rawvalue71 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue37 ++ [44] ++ rawvalue70 ++ [93]),([91] ++ rawvalue38 ++ [44] ++ rawvalue70 ++ [93]),([91] ++ rawvalue39 ++ [44] ++ rawvalue70 ++ [93]),([91] ++ rawvalue43 ++ [44] ++ rawvalue64 ++ [93])] ++ [93,93]
theorem encoded_value71 : encode value71 = rawvalue71 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value37 ++ [44] ++ encode value70 ++ [93]),([91] ++ encode value38 ++ [44] ++ encode value70 ++ [93]),([91] ++ encode value39 ++ [44] ++ encode value70 ++ [93]),([91] ++ encode value43 ++ [44] ++ encode value64 ++ [93])] ++ [93,93] = _
  simp only [encoded_value37,encoded_value70,encoded_value38,encoded_value39,encoded_value43,encoded_value64]
  all_goals rfl
theorem nodes_value71 : nodes value71 = 9 := by
  change 1 + (nodes value37 + nodes value70 + (nodes value38 + nodes value70 + (nodes value39 + nodes value70 + (nodes value43 + nodes value64 + 0)))) = 9
  simp only [nodes_value37,nodes_value70,nodes_value38,nodes_value39,nodes_value43,nodes_value64]
  all_goals decide +kernel
theorem depth_value71 : depth value71 = 1 := by
  change max (max (1 + depth value37) (1 + depth value70)) (max (max (1 + depth value38) (1 + depth value70)) (max (max (1 + depth value39) (1 + depth value70)) (max (max (1 + depth value43) (1 + depth value64)) (0)))) = 1
  simp only [depth_value37,depth_value70,depth_value38,depth_value39,depth_value43,depth_value64]
  all_goals decide +kernel
theorem canonical_value71 : canonical models value71 = true := by
  change ((canonical models value37 && canonical models value70 && (canonical models value38 && canonical models value70 && (canonical models value39 && canonical models value70 && (canonical models value43 && canonical models value64 && true)))) && ordered [encode value37,encode value38,encode value39,encode value43]) = true
  simp only [canonical_value37,canonical_value70,canonical_value38,canonical_value39,canonical_value43,canonical_value64,encoded_value37,encoded_value38,encoded_value39,encoded_value43]
  simp only [ordered,List.all_cons,List.all_nil,order_value37_value38,order_value37_value39,order_value37_value43,order_value38_value39,order_value38_value43,order_value39_value43,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value71 : rawvalue71.length = 125 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value37) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value70) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value38) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value70) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value39) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value70) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value43) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value64) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value72 : Value := .text "context"
noncomputable def rawvalue72 : Bytes := asciiBytes "[\"str\",\"context\"]"
theorem encoded_value72 : encode value72 = rawvalue72 := by
  all_goals rfl
theorem nodes_value72 : nodes value72 = 1 := by rfl
theorem depth_value72 : depth value72 = 0 := by rfl
theorem canonical_value72 : canonical models value72 = true := by decide +kernel
theorem rawLength_value72 : rawvalue72.length = 17 := by
  decide +kernel
noncomputable def value73 : Value := .text "kind"
noncomputable def rawvalue73 : Bytes := asciiBytes "[\"str\",\"kind\"]"
theorem encoded_value73 : encode value73 = rawvalue73 := by
  all_goals rfl
theorem nodes_value73 : nodes value73 = 1 := by rfl
theorem depth_value73 : depth value73 = 0 := by rfl
theorem canonical_value73 : canonical models value73 = true := by decide +kernel
theorem rawLength_value73 : rawvalue73.length = 14 := by
  decide +kernel
noncomputable def value74 : Value := .text "ISC"
noncomputable def rawvalue74 : Bytes := asciiBytes "[\"str\",\"ISC\"]"
theorem encoded_value74 : encode value74 = rawvalue74 := by
  all_goals rfl
theorem nodes_value74 : nodes value74 = 1 := by rfl
theorem depth_value74 : depth value74 = 0 := by rfl
theorem canonical_value74 : canonical models value74 = true := by decide +kernel
theorem rawLength_value74 : rawvalue74.length = 13 := by
  decide +kernel
noncomputable def value75 : Value := .function (.cons value2 value25 (.cons value72 value24 (.cons value73 value74 (.cons value45 value37 .nil))))
noncomputable def rawvalue75 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue25 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue24 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue74 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue37 ++ [93])] ++ [93,93]
theorem encoded_value75 : encode value75 = rawvalue75 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value25 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value24 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value74 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value37 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value25,encoded_value72,encoded_value24,encoded_value73,encoded_value74,encoded_value45,encoded_value37]
  all_goals rfl
theorem order_value2_value72 : byteLess rawvalue2 rawvalue72 = true := by
  simp only [rawvalue2,rawvalue72,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value2_value73 : byteLess rawvalue2 rawvalue73 = true := by
  simp only [rawvalue2,rawvalue73,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value72_value73 : byteLess rawvalue72 rawvalue73 = true := by
  simp only [rawvalue72,rawvalue73,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value72_value45 : byteLess rawvalue72 rawvalue45 = true := by
  simp only [rawvalue72,rawvalue45,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value73_value45 : byteLess rawvalue73 rawvalue45 = true := by
  simp only [rawvalue73,rawvalue45,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value75 : nodes value75 = 37 := by
  change 1 + (nodes value2 + nodes value25 + (nodes value72 + nodes value24 + (nodes value73 + nodes value74 + (nodes value45 + nodes value37 + 0)))) = 37
  simp only [nodes_value2,nodes_value25,nodes_value72,nodes_value24,nodes_value73,nodes_value74,nodes_value45,nodes_value37]
  all_goals decide +kernel
theorem depth_value75 : depth value75 = 4 := by
  change max (max (1 + depth value2) (1 + depth value25)) (max (max (1 + depth value72) (1 + depth value24)) (max (max (1 + depth value73) (1 + depth value74)) (max (max (1 + depth value45) (1 + depth value37)) (0)))) = 4
  simp only [depth_value2,depth_value25,depth_value72,depth_value24,depth_value73,depth_value74,depth_value45,depth_value37]
  all_goals decide +kernel
theorem canonical_value75 : canonical models value75 = true := by
  change ((canonical models value2 && canonical models value25 && (canonical models value72 && canonical models value24 && (canonical models value73 && canonical models value74 && (canonical models value45 && canonical models value37 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value25,canonical_value72,canonical_value24,canonical_value73,canonical_value74,canonical_value45,canonical_value37,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value75 : rawvalue75.length = 625 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value25) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value24) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value74) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value37) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value76 : Value := .function (.cons value2 value25 (.cons value72 value24 (.cons value73 value74 (.cons value45 value38 .nil))))
noncomputable def rawvalue76 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue25 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue24 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue74 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue38 ++ [93])] ++ [93,93]
theorem encoded_value76 : encode value76 = rawvalue76 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value25 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value24 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value74 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value38 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value25,encoded_value72,encoded_value24,encoded_value73,encoded_value74,encoded_value45,encoded_value38]
  all_goals rfl
theorem nodes_value76 : nodes value76 = 37 := by
  change 1 + (nodes value2 + nodes value25 + (nodes value72 + nodes value24 + (nodes value73 + nodes value74 + (nodes value45 + nodes value38 + 0)))) = 37
  simp only [nodes_value2,nodes_value25,nodes_value72,nodes_value24,nodes_value73,nodes_value74,nodes_value45,nodes_value38]
  all_goals decide +kernel
theorem depth_value76 : depth value76 = 4 := by
  change max (max (1 + depth value2) (1 + depth value25)) (max (max (1 + depth value72) (1 + depth value24)) (max (max (1 + depth value73) (1 + depth value74)) (max (max (1 + depth value45) (1 + depth value38)) (0)))) = 4
  simp only [depth_value2,depth_value25,depth_value72,depth_value24,depth_value73,depth_value74,depth_value45,depth_value38]
  all_goals decide +kernel
theorem canonical_value76 : canonical models value76 = true := by
  change ((canonical models value2 && canonical models value25 && (canonical models value72 && canonical models value24 && (canonical models value73 && canonical models value74 && (canonical models value45 && canonical models value38 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value25,canonical_value72,canonical_value24,canonical_value73,canonical_value74,canonical_value45,canonical_value38,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value76 : rawvalue76.length = 625 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value25) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value24) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value74) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value38) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value77 : Value := .function (.cons value2 value25 (.cons value72 value24 (.cons value73 value74 (.cons value45 value39 .nil))))
noncomputable def rawvalue77 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue25 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue24 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue74 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue39 ++ [93])] ++ [93,93]
theorem encoded_value77 : encode value77 = rawvalue77 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value25 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value24 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value74 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value39 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value25,encoded_value72,encoded_value24,encoded_value73,encoded_value74,encoded_value45,encoded_value39]
  all_goals rfl
theorem nodes_value77 : nodes value77 = 37 := by
  change 1 + (nodes value2 + nodes value25 + (nodes value72 + nodes value24 + (nodes value73 + nodes value74 + (nodes value45 + nodes value39 + 0)))) = 37
  simp only [nodes_value2,nodes_value25,nodes_value72,nodes_value24,nodes_value73,nodes_value74,nodes_value45,nodes_value39]
  all_goals decide +kernel
theorem depth_value77 : depth value77 = 4 := by
  change max (max (1 + depth value2) (1 + depth value25)) (max (max (1 + depth value72) (1 + depth value24)) (max (max (1 + depth value73) (1 + depth value74)) (max (max (1 + depth value45) (1 + depth value39)) (0)))) = 4
  simp only [depth_value2,depth_value25,depth_value72,depth_value24,depth_value73,depth_value74,depth_value45,depth_value39]
  all_goals decide +kernel
theorem canonical_value77 : canonical models value77 = true := by
  change ((canonical models value2 && canonical models value25 && (canonical models value72 && canonical models value24 && (canonical models value73 && canonical models value74 && (canonical models value45 && canonical models value39 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value25,canonical_value72,canonical_value24,canonical_value73,canonical_value74,canonical_value45,canonical_value39,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value77 : rawvalue77.length = 625 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value25) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value24) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value74) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value39) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value78 : Value := .text "APC"
noncomputable def rawvalue78 : Bytes := asciiBytes "[\"str\",\"APC\"]"
theorem encoded_value78 : encode value78 = rawvalue78 := by
  all_goals rfl
theorem nodes_value78 : nodes value78 = 1 := by rfl
theorem depth_value78 : depth value78 = 0 := by rfl
theorem canonical_value78 : canonical models value78 = true := by decide +kernel
theorem rawLength_value78 : rawvalue78.length = 13 := by
  decide +kernel
noncomputable def value79 : Value := .function (.cons value2 value35 (.cons value72 value34 (.cons value73 value78 (.cons value45 value37 .nil))))
noncomputable def rawvalue79 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue35 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue34 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue78 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue37 ++ [93])] ++ [93,93]
theorem encoded_value79 : encode value79 = rawvalue79 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value35 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value34 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value78 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value37 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value35,encoded_value72,encoded_value34,encoded_value73,encoded_value78,encoded_value45,encoded_value37]
  all_goals rfl
theorem nodes_value79 : nodes value79 = 200 := by
  change 1 + (nodes value2 + nodes value35 + (nodes value72 + nodes value34 + (nodes value73 + nodes value78 + (nodes value45 + nodes value37 + 0)))) = 200
  simp only [nodes_value2,nodes_value35,nodes_value72,nodes_value34,nodes_value73,nodes_value78,nodes_value45,nodes_value37]
  all_goals decide +kernel
theorem depth_value79 : depth value79 = 7 := by
  change max (max (1 + depth value2) (1 + depth value35)) (max (max (1 + depth value72) (1 + depth value34)) (max (max (1 + depth value73) (1 + depth value78)) (max (max (1 + depth value45) (1 + depth value37)) (0)))) = 7
  simp only [depth_value2,depth_value35,depth_value72,depth_value34,depth_value73,depth_value78,depth_value45,depth_value37]
  all_goals decide +kernel
theorem canonical_value79 : canonical models value79 = true := by
  change ((canonical models value2 && canonical models value35 && (canonical models value72 && canonical models value34 && (canonical models value73 && canonical models value78 && (canonical models value45 && canonical models value37 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value35,canonical_value72,canonical_value34,canonical_value73,canonical_value78,canonical_value45,canonical_value37,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value79 : rawvalue79.length = 3406 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value35) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value34) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value78) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value37) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value80 : Value := .function (.cons value2 value35 (.cons value72 value34 (.cons value73 value78 (.cons value45 value38 .nil))))
noncomputable def rawvalue80 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue35 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue34 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue78 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue38 ++ [93])] ++ [93,93]
theorem encoded_value80 : encode value80 = rawvalue80 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value35 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value34 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value78 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value38 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value35,encoded_value72,encoded_value34,encoded_value73,encoded_value78,encoded_value45,encoded_value38]
  all_goals rfl
theorem nodes_value80 : nodes value80 = 200 := by
  change 1 + (nodes value2 + nodes value35 + (nodes value72 + nodes value34 + (nodes value73 + nodes value78 + (nodes value45 + nodes value38 + 0)))) = 200
  simp only [nodes_value2,nodes_value35,nodes_value72,nodes_value34,nodes_value73,nodes_value78,nodes_value45,nodes_value38]
  all_goals decide +kernel
theorem depth_value80 : depth value80 = 7 := by
  change max (max (1 + depth value2) (1 + depth value35)) (max (max (1 + depth value72) (1 + depth value34)) (max (max (1 + depth value73) (1 + depth value78)) (max (max (1 + depth value45) (1 + depth value38)) (0)))) = 7
  simp only [depth_value2,depth_value35,depth_value72,depth_value34,depth_value73,depth_value78,depth_value45,depth_value38]
  all_goals decide +kernel
theorem canonical_value80 : canonical models value80 = true := by
  change ((canonical models value2 && canonical models value35 && (canonical models value72 && canonical models value34 && (canonical models value73 && canonical models value78 && (canonical models value45 && canonical models value38 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value35,canonical_value72,canonical_value34,canonical_value73,canonical_value78,canonical_value45,canonical_value38,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value80 : rawvalue80.length = 3406 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value35) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value34) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value78) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value38) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value81 : Value := .function (.cons value2 value35 (.cons value72 value34 (.cons value73 value78 (.cons value45 value39 .nil))))
noncomputable def rawvalue81 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue35 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue34 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue78 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue39 ++ [93])] ++ [93,93]
theorem encoded_value81 : encode value81 = rawvalue81 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value35 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value34 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value78 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value39 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value35,encoded_value72,encoded_value34,encoded_value73,encoded_value78,encoded_value45,encoded_value39]
  all_goals rfl
theorem nodes_value81 : nodes value81 = 200 := by
  change 1 + (nodes value2 + nodes value35 + (nodes value72 + nodes value34 + (nodes value73 + nodes value78 + (nodes value45 + nodes value39 + 0)))) = 200
  simp only [nodes_value2,nodes_value35,nodes_value72,nodes_value34,nodes_value73,nodes_value78,nodes_value45,nodes_value39]
  all_goals decide +kernel
theorem depth_value81 : depth value81 = 7 := by
  change max (max (1 + depth value2) (1 + depth value35)) (max (max (1 + depth value72) (1 + depth value34)) (max (max (1 + depth value73) (1 + depth value78)) (max (max (1 + depth value45) (1 + depth value39)) (0)))) = 7
  simp only [depth_value2,depth_value35,depth_value72,depth_value34,depth_value73,depth_value78,depth_value45,depth_value39]
  all_goals decide +kernel
theorem canonical_value81 : canonical models value81 = true := by
  change ((canonical models value2 && canonical models value35 && (canonical models value72 && canonical models value34 && (canonical models value73 && canonical models value78 && (canonical models value45 && canonical models value39 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value35,canonical_value72,canonical_value34,canonical_value73,canonical_value78,canonical_value45,canonical_value39,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value81 : rawvalue81.length = 3406 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value35) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value34) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value78) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value39) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value82 : Value := .text "EC"
noncomputable def rawvalue82 : Bytes := asciiBytes "[\"str\",\"EC\"]"
theorem encoded_value82 : encode value82 = rawvalue82 := by
  all_goals rfl
theorem nodes_value82 : nodes value82 = 1 := by rfl
theorem depth_value82 : depth value82 = 0 := by rfl
theorem canonical_value82 : canonical models value82 = true := by decide +kernel
theorem rawLength_value82 : rawvalue82.length = 12 := by
  decide +kernel
noncomputable def value83 : Value := .function (.cons value2 value34 (.cons value72 value25 (.cons value73 value82 (.cons value45 value37 .nil))))
noncomputable def rawvalue83 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue34 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue25 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue82 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue37 ++ [93])] ++ [93,93]
theorem encoded_value83 : encode value83 = rawvalue83 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value34 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value25 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value82 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value37 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value34,encoded_value72,encoded_value25,encoded_value73,encoded_value82,encoded_value45,encoded_value37]
  all_goals rfl
theorem nodes_value83 : nodes value83 = 96 := by
  change 1 + (nodes value2 + nodes value34 + (nodes value72 + nodes value25 + (nodes value73 + nodes value82 + (nodes value45 + nodes value37 + 0)))) = 96
  simp only [nodes_value2,nodes_value34,nodes_value72,nodes_value25,nodes_value73,nodes_value82,nodes_value45,nodes_value37]
  all_goals decide +kernel
theorem depth_value83 : depth value83 = 6 := by
  change max (max (1 + depth value2) (1 + depth value34)) (max (max (1 + depth value72) (1 + depth value25)) (max (max (1 + depth value73) (1 + depth value82)) (max (max (1 + depth value45) (1 + depth value37)) (0)))) = 6
  simp only [depth_value2,depth_value34,depth_value72,depth_value25,depth_value73,depth_value82,depth_value45,depth_value37]
  all_goals decide +kernel
theorem canonical_value83 : canonical models value83 = true := by
  change ((canonical models value2 && canonical models value34 && (canonical models value72 && canonical models value25 && (canonical models value73 && canonical models value82 && (canonical models value45 && canonical models value37 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value34,canonical_value72,canonical_value25,canonical_value73,canonical_value82,canonical_value45,canonical_value37,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value83 : rawvalue83.length = 1633 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value34) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value25) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value82) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value37) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value84 : Value := .function (.cons value2 value34 (.cons value72 value25 (.cons value73 value82 (.cons value45 value38 .nil))))
noncomputable def rawvalue84 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue34 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue25 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue82 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue38 ++ [93])] ++ [93,93]
theorem encoded_value84 : encode value84 = rawvalue84 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value34 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value25 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value82 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value38 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value34,encoded_value72,encoded_value25,encoded_value73,encoded_value82,encoded_value45,encoded_value38]
  all_goals rfl
theorem nodes_value84 : nodes value84 = 96 := by
  change 1 + (nodes value2 + nodes value34 + (nodes value72 + nodes value25 + (nodes value73 + nodes value82 + (nodes value45 + nodes value38 + 0)))) = 96
  simp only [nodes_value2,nodes_value34,nodes_value72,nodes_value25,nodes_value73,nodes_value82,nodes_value45,nodes_value38]
  all_goals decide +kernel
theorem depth_value84 : depth value84 = 6 := by
  change max (max (1 + depth value2) (1 + depth value34)) (max (max (1 + depth value72) (1 + depth value25)) (max (max (1 + depth value73) (1 + depth value82)) (max (max (1 + depth value45) (1 + depth value38)) (0)))) = 6
  simp only [depth_value2,depth_value34,depth_value72,depth_value25,depth_value73,depth_value82,depth_value45,depth_value38]
  all_goals decide +kernel
theorem canonical_value84 : canonical models value84 = true := by
  change ((canonical models value2 && canonical models value34 && (canonical models value72 && canonical models value25 && (canonical models value73 && canonical models value82 && (canonical models value45 && canonical models value38 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value34,canonical_value72,canonical_value25,canonical_value73,canonical_value82,canonical_value45,canonical_value38,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value84 : rawvalue84.length = 1633 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value34) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value25) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value82) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value38) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value85 : Value := .function (.cons value2 value34 (.cons value72 value25 (.cons value73 value82 (.cons value45 value39 .nil))))
noncomputable def rawvalue85 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue34 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue25 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue82 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue39 ++ [93])] ++ [93,93]
theorem encoded_value85 : encode value85 = rawvalue85 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value34 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value25 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value82 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value39 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value34,encoded_value72,encoded_value25,encoded_value73,encoded_value82,encoded_value45,encoded_value39]
  all_goals rfl
theorem nodes_value85 : nodes value85 = 96 := by
  change 1 + (nodes value2 + nodes value34 + (nodes value72 + nodes value25 + (nodes value73 + nodes value82 + (nodes value45 + nodes value39 + 0)))) = 96
  simp only [nodes_value2,nodes_value34,nodes_value72,nodes_value25,nodes_value73,nodes_value82,nodes_value45,nodes_value39]
  all_goals decide +kernel
theorem depth_value85 : depth value85 = 6 := by
  change max (max (1 + depth value2) (1 + depth value34)) (max (max (1 + depth value72) (1 + depth value25)) (max (max (1 + depth value73) (1 + depth value82)) (max (max (1 + depth value45) (1 + depth value39)) (0)))) = 6
  simp only [depth_value2,depth_value34,depth_value72,depth_value25,depth_value73,depth_value82,depth_value45,depth_value39]
  all_goals decide +kernel
theorem canonical_value85 : canonical models value85 = true := by
  change ((canonical models value2 && canonical models value34 && (canonical models value72 && canonical models value25 && (canonical models value73 && canonical models value82 && (canonical models value45 && canonical models value39 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value34,canonical_value72,canonical_value25,canonical_value73,canonical_value82,canonical_value45,canonical_value39,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value85 : rawvalue85.length = 1633 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value34) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value25) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value82) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value39) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value86 : Value := .text "ROUND_CONFIG"
noncomputable def rawvalue86 : Bytes := asciiBytes "[\"str\",\"ROUND_CONFIG\"]"
theorem encoded_value86 : encode value86 = rawvalue86 := by
  all_goals rfl
theorem nodes_value86 : nodes value86 = 1 := by rfl
theorem depth_value86 : depth value86 = 0 := by rfl
theorem canonical_value86 : canonical models value86 = true := by decide +kernel
theorem rawLength_value86 : rawvalue86.length = 22 := by
  decide +kernel
noncomputable def value87 : Value := .function (.cons value20 value21 (.cons value22 value23 (.cons value73 value86 .nil)))
noncomputable def rawvalue87 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue20 ++ [44] ++ rawvalue21 ++ [93]),([91] ++ rawvalue22 ++ [44] ++ rawvalue23 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue86 ++ [93])] ++ [93,93]
theorem encoded_value87 : encode value87 = rawvalue87 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value20 ++ [44] ++ encode value21 ++ [93]),([91] ++ encode value22 ++ [44] ++ encode value23 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value86 ++ [93])] ++ [93,93] = _
  simp only [encoded_value20,encoded_value21,encoded_value22,encoded_value23,encoded_value73,encoded_value86]
  all_goals rfl
theorem order_value20_value73 : byteLess rawvalue20 rawvalue73 = true := by
  simp only [rawvalue20,rawvalue73,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value22_value73 : byteLess rawvalue22 rawvalue73 = true := by
  simp only [rawvalue22,rawvalue73,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value87 : nodes value87 = 7 := by
  change 1 + (nodes value20 + nodes value21 + (nodes value22 + nodes value23 + (nodes value73 + nodes value86 + 0))) = 7
  simp only [nodes_value20,nodes_value21,nodes_value22,nodes_value23,nodes_value73,nodes_value86]
  all_goals decide +kernel
theorem depth_value87 : depth value87 = 1 := by
  change max (max (1 + depth value20) (1 + depth value21)) (max (max (1 + depth value22) (1 + depth value23)) (max (max (1 + depth value73) (1 + depth value86)) (0))) = 1
  simp only [depth_value20,depth_value21,depth_value22,depth_value23,depth_value73,depth_value86]
  all_goals decide +kernel
theorem canonical_value87 : canonical models value87 = true := by
  change ((canonical models value20 && canonical models value21 && (canonical models value22 && canonical models value23 && (canonical models value73 && canonical models value86 && true))) && ordered [encode value20,encode value22,encode value73]) = true
  simp only [canonical_value20,canonical_value21,canonical_value22,canonical_value23,canonical_value73,canonical_value86,encoded_value20,encoded_value22,encoded_value73]
  simp only [ordered,List.all_cons,List.all_nil,order_value20_value22,order_value20_value73,order_value22_value73,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value87 : rawvalue87.length = 120 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value20) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value21) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value22) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value23) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value86) (show ([93] : Bytes).length = 1 from by decide +kernel)))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value88 : Value := .function (.cons value2 value15 (.cons value72 value87 (.cons value73 value86 (.cons value45 value37 .nil))))
noncomputable def rawvalue88 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue15 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue87 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue86 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue37 ++ [93])] ++ [93,93]
theorem encoded_value88 : encode value88 = rawvalue88 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value15 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value87 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value86 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value37 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value15,encoded_value72,encoded_value87,encoded_value73,encoded_value86,encoded_value45,encoded_value37]
  all_goals rfl
theorem nodes_value88 : nodes value88 = 15 := by
  change 1 + (nodes value2 + nodes value15 + (nodes value72 + nodes value87 + (nodes value73 + nodes value86 + (nodes value45 + nodes value37 + 0)))) = 15
  simp only [nodes_value2,nodes_value15,nodes_value72,nodes_value87,nodes_value73,nodes_value86,nodes_value45,nodes_value37]
  all_goals decide +kernel
theorem depth_value88 : depth value88 = 2 := by
  change max (max (1 + depth value2) (1 + depth value15)) (max (max (1 + depth value72) (1 + depth value87)) (max (max (1 + depth value73) (1 + depth value86)) (max (max (1 + depth value45) (1 + depth value37)) (0)))) = 2
  simp only [depth_value2,depth_value15,depth_value72,depth_value87,depth_value73,depth_value86,depth_value45,depth_value37]
  all_goals decide +kernel
theorem canonical_value88 : canonical models value88 = true := by
  change ((canonical models value2 && canonical models value15 && (canonical models value72 && canonical models value87 && (canonical models value73 && canonical models value86 && (canonical models value45 && canonical models value37 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value15,canonical_value72,canonical_value87,canonical_value73,canonical_value86,canonical_value45,canonical_value37,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value88 : rawvalue88.length = 264 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value15) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value87) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value86) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value37) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value89 : Value := .function (.cons value2 value15 (.cons value72 value87 (.cons value73 value86 (.cons value45 value38 .nil))))
noncomputable def rawvalue89 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue15 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue87 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue86 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue38 ++ [93])] ++ [93,93]
theorem encoded_value89 : encode value89 = rawvalue89 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value15 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value87 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value86 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value38 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value15,encoded_value72,encoded_value87,encoded_value73,encoded_value86,encoded_value45,encoded_value38]
  all_goals rfl
theorem nodes_value89 : nodes value89 = 15 := by
  change 1 + (nodes value2 + nodes value15 + (nodes value72 + nodes value87 + (nodes value73 + nodes value86 + (nodes value45 + nodes value38 + 0)))) = 15
  simp only [nodes_value2,nodes_value15,nodes_value72,nodes_value87,nodes_value73,nodes_value86,nodes_value45,nodes_value38]
  all_goals decide +kernel
theorem depth_value89 : depth value89 = 2 := by
  change max (max (1 + depth value2) (1 + depth value15)) (max (max (1 + depth value72) (1 + depth value87)) (max (max (1 + depth value73) (1 + depth value86)) (max (max (1 + depth value45) (1 + depth value38)) (0)))) = 2
  simp only [depth_value2,depth_value15,depth_value72,depth_value87,depth_value73,depth_value86,depth_value45,depth_value38]
  all_goals decide +kernel
theorem canonical_value89 : canonical models value89 = true := by
  change ((canonical models value2 && canonical models value15 && (canonical models value72 && canonical models value87 && (canonical models value73 && canonical models value86 && (canonical models value45 && canonical models value38 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value15,canonical_value72,canonical_value87,canonical_value73,canonical_value86,canonical_value45,canonical_value38,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value89 : rawvalue89.length = 264 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value15) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value87) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value86) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value38) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value90 : Value := .function (.cons value2 value15 (.cons value72 value87 (.cons value73 value86 (.cons value45 value39 .nil))))
noncomputable def rawvalue90 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue15 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue87 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue86 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue39 ++ [93])] ++ [93,93]
theorem encoded_value90 : encode value90 = rawvalue90 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value15 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value87 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value86 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value39 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value15,encoded_value72,encoded_value87,encoded_value73,encoded_value86,encoded_value45,encoded_value39]
  all_goals rfl
theorem nodes_value90 : nodes value90 = 15 := by
  change 1 + (nodes value2 + nodes value15 + (nodes value72 + nodes value87 + (nodes value73 + nodes value86 + (nodes value45 + nodes value39 + 0)))) = 15
  simp only [nodes_value2,nodes_value15,nodes_value72,nodes_value87,nodes_value73,nodes_value86,nodes_value45,nodes_value39]
  all_goals decide +kernel
theorem depth_value90 : depth value90 = 2 := by
  change max (max (1 + depth value2) (1 + depth value15)) (max (max (1 + depth value72) (1 + depth value87)) (max (max (1 + depth value73) (1 + depth value86)) (max (max (1 + depth value45) (1 + depth value39)) (0)))) = 2
  simp only [depth_value2,depth_value15,depth_value72,depth_value87,depth_value73,depth_value86,depth_value45,depth_value39]
  all_goals decide +kernel
theorem canonical_value90 : canonical models value90 = true := by
  change ((canonical models value2 && canonical models value15 && (canonical models value72 && canonical models value87 && (canonical models value73 && canonical models value86 && (canonical models value45 && canonical models value39 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value15,canonical_value72,canonical_value87,canonical_value73,canonical_value86,canonical_value45,canonical_value39,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value90 : rawvalue90.length = 264 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value15) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value87) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value86) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value39) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value91 : Value := .set (.cons value75 (.cons value76 (.cons value77 (.cons value79 (.cons value80 (.cons value81 (.cons value83 (.cons value84 (.cons value85 (.cons value88 (.cons value89 (.cons value90 .nil))))))))))))
noncomputable def rawvalue91 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue75,rawvalue76,rawvalue77,rawvalue79,rawvalue80,rawvalue81,rawvalue83,rawvalue84,rawvalue85,rawvalue88,rawvalue89,rawvalue90] ++ [93,93]
theorem encoded_value91 : encode value91 = rawvalue91 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90] ++ [93,93] = _
  simp only [encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  all_goals rfl
theorem order_value75_value76 : byteLess rawvalue75 rawvalue76 = true := by
  simp only [rawvalue75,rawvalue76,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue38,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value75_value77 : byteLess rawvalue75 rawvalue77 = true := by
  simp only [rawvalue75,rawvalue77,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value75_value79 : byteLess rawvalue75 rawvalue79 = true := by
  simp only [rawvalue75,rawvalue79,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue7,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value75_value80 : byteLess rawvalue75 rawvalue80 = true := by
  simp only [rawvalue75,rawvalue80,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue7,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value75_value81 : byteLess rawvalue75 rawvalue81 = true := by
  simp only [rawvalue75,rawvalue81,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue7,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value75_value83 : byteLess rawvalue75 rawvalue83 = true := by
  simp only [rawvalue75,rawvalue83,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue7,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value75_value84 : byteLess rawvalue75 rawvalue84 = true := by
  simp only [rawvalue75,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue7,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value75_value85 : byteLess rawvalue75 rawvalue85 = true := by
  simp only [rawvalue75,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue7,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value75_value88 : byteLess rawvalue75 rawvalue88 = true := by
  simp only [rawvalue75,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value75_value89 : byteLess rawvalue75 rawvalue89 = true := by
  simp only [rawvalue75,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value75_value90 : byteLess rawvalue75 rawvalue90 = true := by
  simp only [rawvalue75,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value76_value77 : byteLess rawvalue76 rawvalue77 = true := by
  simp only [rawvalue76,rawvalue77,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue38,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value76_value79 : byteLess rawvalue76 rawvalue79 = true := by
  simp only [rawvalue76,rawvalue79,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue7,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value76_value80 : byteLess rawvalue76 rawvalue80 = true := by
  simp only [rawvalue76,rawvalue80,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue7,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value76_value81 : byteLess rawvalue76 rawvalue81 = true := by
  simp only [rawvalue76,rawvalue81,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue7,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value76_value83 : byteLess rawvalue76 rawvalue83 = true := by
  simp only [rawvalue76,rawvalue83,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue7,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value76_value84 : byteLess rawvalue76 rawvalue84 = true := by
  simp only [rawvalue76,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue7,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value76_value85 : byteLess rawvalue76 rawvalue85 = true := by
  simp only [rawvalue76,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue7,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value76_value88 : byteLess rawvalue76 rawvalue88 = true := by
  simp only [rawvalue76,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value76_value89 : byteLess rawvalue76 rawvalue89 = true := by
  simp only [rawvalue76,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value76_value90 : byteLess rawvalue76 rawvalue90 = true := by
  simp only [rawvalue76,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value77_value79 : byteLess rawvalue77 rawvalue79 = true := by
  simp only [rawvalue77,rawvalue79,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue7,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value77_value80 : byteLess rawvalue77 rawvalue80 = true := by
  simp only [rawvalue77,rawvalue80,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue7,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value77_value81 : byteLess rawvalue77 rawvalue81 = true := by
  simp only [rawvalue77,rawvalue81,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue7,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value77_value83 : byteLess rawvalue77 rawvalue83 = true := by
  simp only [rawvalue77,rawvalue83,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue7,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value77_value84 : byteLess rawvalue77 rawvalue84 = true := by
  simp only [rawvalue77,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue7,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value77_value85 : byteLess rawvalue77 rawvalue85 = true := by
  simp only [rawvalue77,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue7,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value77_value88 : byteLess rawvalue77 rawvalue88 = true := by
  simp only [rawvalue77,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value77_value89 : byteLess rawvalue77 rawvalue89 = true := by
  simp only [rawvalue77,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value77_value90 : byteLess rawvalue77 rawvalue90 = true := by
  simp only [rawvalue77,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue25,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value79_value80 : byteLess rawvalue79 rawvalue80 = true := by
  simp only [rawvalue79,rawvalue80,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue38,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value79_value81 : byteLess rawvalue79 rawvalue81 = true := by
  simp only [rawvalue79,rawvalue81,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value79_value83 : byteLess rawvalue79 rawvalue83 = true := by
  simp only [rawvalue79,rawvalue83,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue35,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue3,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value79_value84 : byteLess rawvalue79 rawvalue84 = true := by
  simp only [rawvalue79,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue35,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue3,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value79_value85 : byteLess rawvalue79 rawvalue85 = true := by
  simp only [rawvalue79,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue35,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue3,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value79_value88 : byteLess rawvalue79 rawvalue88 = true := by
  simp only [rawvalue79,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue35,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value79_value89 : byteLess rawvalue79 rawvalue89 = true := by
  simp only [rawvalue79,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue35,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value79_value90 : byteLess rawvalue79 rawvalue90 = true := by
  simp only [rawvalue79,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue35,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value80_value81 : byteLess rawvalue80 rawvalue81 = true := by
  simp only [rawvalue80,rawvalue81,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue38,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value80_value83 : byteLess rawvalue80 rawvalue83 = true := by
  simp only [rawvalue80,rawvalue83,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue35,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue3,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value80_value84 : byteLess rawvalue80 rawvalue84 = true := by
  simp only [rawvalue80,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue35,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue3,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value80_value85 : byteLess rawvalue80 rawvalue85 = true := by
  simp only [rawvalue80,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue35,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue3,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value80_value88 : byteLess rawvalue80 rawvalue88 = true := by
  simp only [rawvalue80,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue35,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value80_value89 : byteLess rawvalue80 rawvalue89 = true := by
  simp only [rawvalue80,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue35,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value80_value90 : byteLess rawvalue80 rawvalue90 = true := by
  simp only [rawvalue80,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue35,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value81_value83 : byteLess rawvalue81 rawvalue83 = true := by
  simp only [rawvalue81,rawvalue83,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue35,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue3,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value81_value84 : byteLess rawvalue81 rawvalue84 = true := by
  simp only [rawvalue81,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue35,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue3,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value81_value85 : byteLess rawvalue81 rawvalue85 = true := by
  simp only [rawvalue81,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue35,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue3,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value81_value88 : byteLess rawvalue81 rawvalue88 = true := by
  simp only [rawvalue81,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue35,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value81_value89 : byteLess rawvalue81 rawvalue89 = true := by
  simp only [rawvalue81,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue35,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value81_value90 : byteLess rawvalue81 rawvalue90 = true := by
  simp only [rawvalue81,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue35,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value83_value84 : byteLess rawvalue83 rawvalue84 = true := by
  simp only [rawvalue83,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue38,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value83_value85 : byteLess rawvalue83 rawvalue85 = true := by
  simp only [rawvalue83,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value83_value88 : byteLess rawvalue83 rawvalue88 = true := by
  simp only [rawvalue83,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue34,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value83_value89 : byteLess rawvalue83 rawvalue89 = true := by
  simp only [rawvalue83,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue34,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value83_value90 : byteLess rawvalue83 rawvalue90 = true := by
  simp only [rawvalue83,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue34,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value84_value85 : byteLess rawvalue84 rawvalue85 = true := by
  simp only [rawvalue84,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue38,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value84_value88 : byteLess rawvalue84 rawvalue88 = true := by
  simp only [rawvalue84,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue34,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value84_value89 : byteLess rawvalue84 rawvalue89 = true := by
  simp only [rawvalue84,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue34,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value84_value90 : byteLess rawvalue84 rawvalue90 = true := by
  simp only [rawvalue84,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue34,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value85_value88 : byteLess rawvalue85 rawvalue88 = true := by
  simp only [rawvalue85,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue34,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value85_value89 : byteLess rawvalue85 rawvalue89 = true := by
  simp only [rawvalue85,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue34,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value85_value90 : byteLess rawvalue85 rawvalue90 = true := by
  simp only [rawvalue85,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue34,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value88_value89 : byteLess rawvalue88 rawvalue89 = true := by
  simp only [rawvalue88,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue38,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value88_value90 : byteLess rawvalue88 rawvalue90 = true := by
  simp only [rawvalue88,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value89_value90 : byteLess rawvalue89 rawvalue90 = true := by
  simp only [rawvalue89,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue38,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value91 : nodes value91 = 1045 := by
  change 1 + (nodes value75 + (nodes value76 + (nodes value77 + (nodes value79 + (nodes value80 + (nodes value81 + (nodes value83 + (nodes value84 + (nodes value85 + (nodes value88 + (nodes value89 + (nodes value90 + 0)))))))))))) = 1045
  simp only [nodes_value75,nodes_value76,nodes_value77,nodes_value79,nodes_value80,nodes_value81,nodes_value83,nodes_value84,nodes_value85,nodes_value88,nodes_value89,nodes_value90]
  all_goals decide +kernel
theorem depth_value91 : depth value91 = 8 := by
  change max (1 + depth value75) (max (1 + depth value76) (max (1 + depth value77) (max (1 + depth value79) (max (1 + depth value80) (max (1 + depth value81) (max (1 + depth value83) (max (1 + depth value84) (max (1 + depth value85) (max (1 + depth value88) (max (1 + depth value89) (max (1 + depth value90) (0)))))))))))) = 8
  simp only [depth_value75,depth_value76,depth_value77,depth_value79,depth_value80,depth_value81,depth_value83,depth_value84,depth_value85,depth_value88,depth_value89,depth_value90]
  all_goals decide +kernel
theorem canonical_value91 : canonical models value91 = true := by
  change ((canonical models value75 && (canonical models value76 && (canonical models value77 && (canonical models value79 && (canonical models value80 && (canonical models value81 && (canonical models value83 && (canonical models value84 && (canonical models value85 && (canonical models value88 && (canonical models value89 && (canonical models value90 && true)))))))))))) && ordered [encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90]) = true
  simp only [canonical_value75,canonical_value76,canonical_value77,canonical_value79,canonical_value80,canonical_value81,canonical_value83,canonical_value84,canonical_value85,canonical_value88,canonical_value89,canonical_value90,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  simp only [ordered,List.all_cons,List.all_nil,order_value75_value76,order_value75_value77,order_value75_value79,order_value75_value80,order_value75_value81,order_value75_value83,order_value75_value84,order_value75_value85,order_value75_value88,order_value75_value89,order_value75_value90,order_value76_value77,order_value76_value79,order_value76_value80,order_value76_value81,order_value76_value83,order_value76_value84,order_value76_value85,order_value76_value88,order_value76_value89,order_value76_value90,order_value77_value79,order_value77_value80,order_value77_value81,order_value77_value83,order_value77_value84,order_value77_value85,order_value77_value88,order_value77_value89,order_value77_value90,order_value79_value80,order_value79_value81,order_value79_value83,order_value79_value84,order_value79_value85,order_value79_value88,order_value79_value89,order_value79_value90,order_value80_value81,order_value80_value83,order_value80_value84,order_value80_value85,order_value80_value88,order_value80_value89,order_value80_value90,order_value81_value83,order_value81_value84,order_value81_value85,order_value81_value88,order_value81_value89,order_value81_value90,order_value83_value84,order_value83_value85,order_value83_value88,order_value83_value89,order_value83_value90,order_value84_value85,order_value84_value88,order_value84_value89,order_value84_value90,order_value85_value88,order_value85_value89,order_value85_value90,order_value88_value89,order_value88_value90,order_value89_value90,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value91 : rawvalue91.length = 17805 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value75 (commaConsLength rawLength_value76 (commaConsLength rawLength_value77 (commaConsLength rawLength_value79 (commaConsLength rawLength_value80 (commaConsLength rawLength_value81 (commaConsLength rawLength_value83 (commaConsLength rawLength_value84 (commaConsLength rawLength_value85 (commaConsLength rawLength_value88 (commaConsLength rawLength_value89 (commaSingletonLength rawLength_value90))))))))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value92 : Value := .function (.cons value2 value34 (.cons value45 value37 .nil))
noncomputable def rawvalue92 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue34 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue37 ++ [93])] ++ [93,93]
theorem encoded_value92 : encode value92 = rawvalue92 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value34 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value37 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value34,encoded_value45,encoded_value37]
  all_goals rfl
theorem nodes_value92 : nodes value92 = 68 := by
  change 1 + (nodes value2 + nodes value34 + (nodes value45 + nodes value37 + 0)) = 68
  simp only [nodes_value2,nodes_value34,nodes_value45,nodes_value37]
  all_goals decide +kernel
theorem depth_value92 : depth value92 = 6 := by
  change max (max (1 + depth value2) (1 + depth value34)) (max (max (1 + depth value45) (1 + depth value37)) (0)) = 6
  simp only [depth_value2,depth_value34,depth_value45,depth_value37]
  all_goals decide +kernel
theorem canonical_value92 : canonical models value92 = true := by
  change ((canonical models value2 && canonical models value34 && (canonical models value45 && canonical models value37 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value34,canonical_value45,canonical_value37,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value92 : rawvalue92.length = 1153 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value34) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value37) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value93 : Value := .function (.cons value2 value34 (.cons value45 value38 .nil))
noncomputable def rawvalue93 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue34 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue38 ++ [93])] ++ [93,93]
theorem encoded_value93 : encode value93 = rawvalue93 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value34 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value38 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value34,encoded_value45,encoded_value38]
  all_goals rfl
theorem nodes_value93 : nodes value93 = 68 := by
  change 1 + (nodes value2 + nodes value34 + (nodes value45 + nodes value38 + 0)) = 68
  simp only [nodes_value2,nodes_value34,nodes_value45,nodes_value38]
  all_goals decide +kernel
theorem depth_value93 : depth value93 = 6 := by
  change max (max (1 + depth value2) (1 + depth value34)) (max (max (1 + depth value45) (1 + depth value38)) (0)) = 6
  simp only [depth_value2,depth_value34,depth_value45,depth_value38]
  all_goals decide +kernel
theorem canonical_value93 : canonical models value93 = true := by
  change ((canonical models value2 && canonical models value34 && (canonical models value45 && canonical models value38 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value34,canonical_value45,canonical_value38,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value93 : rawvalue93.length = 1153 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value34) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value38) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value94 : Value := .function (.cons value2 value34 (.cons value45 value39 .nil))
noncomputable def rawvalue94 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue34 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue39 ++ [93])] ++ [93,93]
theorem encoded_value94 : encode value94 = rawvalue94 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value34 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value39 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value34,encoded_value45,encoded_value39]
  all_goals rfl
theorem nodes_value94 : nodes value94 = 68 := by
  change 1 + (nodes value2 + nodes value34 + (nodes value45 + nodes value39 + 0)) = 68
  simp only [nodes_value2,nodes_value34,nodes_value45,nodes_value39]
  all_goals decide +kernel
theorem depth_value94 : depth value94 = 6 := by
  change max (max (1 + depth value2) (1 + depth value34)) (max (max (1 + depth value45) (1 + depth value39)) (0)) = 6
  simp only [depth_value2,depth_value34,depth_value45,depth_value39]
  all_goals decide +kernel
theorem canonical_value94 : canonical models value94 = true := by
  change ((canonical models value2 && canonical models value34 && (canonical models value45 && canonical models value39 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value34,canonical_value45,canonical_value39,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value94 : rawvalue94.length = 1153 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value34) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value39) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value95 : Value := .set (.cons value92 (.cons value93 (.cons value94 .nil)))
noncomputable def rawvalue95 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue92,rawvalue93,rawvalue94] ++ [93,93]
theorem encoded_value95 : encode value95 = rawvalue95 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value92,encode value93,encode value94] ++ [93,93] = _
  simp only [encoded_value92,encoded_value93,encoded_value94]
  all_goals rfl
theorem order_value92_value93 : byteLess rawvalue92 rawvalue93 = true := by
  simp only [rawvalue92,rawvalue93,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue38,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value92_value94 : byteLess rawvalue92 rawvalue94 = true := by
  simp only [rawvalue92,rawvalue94,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value93_value94 : byteLess rawvalue93 rawvalue94 = true := by
  simp only [rawvalue93,rawvalue94,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue38,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value95 : nodes value95 = 205 := by
  change 1 + (nodes value92 + (nodes value93 + (nodes value94 + 0))) = 205
  simp only [nodes_value92,nodes_value93,nodes_value94]
  all_goals decide +kernel
theorem depth_value95 : depth value95 = 7 := by
  change max (1 + depth value92) (max (1 + depth value93) (max (1 + depth value94) (0))) = 7
  simp only [depth_value92,depth_value93,depth_value94]
  all_goals decide +kernel
theorem canonical_value95 : canonical models value95 = true := by
  change ((canonical models value92 && (canonical models value93 && (canonical models value94 && true))) && ordered [encode value92,encode value93,encode value94]) = true
  simp only [canonical_value92,canonical_value93,canonical_value94,encoded_value92,encoded_value93,encoded_value94]
  simp only [ordered,List.all_cons,List.all_nil,order_value92_value93,order_value92_value94,order_value93_value94,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value95 : rawvalue95.length = 3471 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value92 (commaConsLength rawLength_value93 (commaSingletonLength rawLength_value94)))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value96 : Value := .function (.cons value2 value34 (.cons value36 value40 .nil))
noncomputable def rawvalue96 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue34 ++ [93]),([91] ++ rawvalue36 ++ [44] ++ rawvalue40 ++ [93])] ++ [93,93]
theorem encoded_value96 : encode value96 = rawvalue96 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value34 ++ [93]),([91] ++ encode value36 ++ [44] ++ encode value40 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value34,encoded_value36,encoded_value40]
  all_goals rfl
theorem nodes_value96 : nodes value96 = 71 := by
  change 1 + (nodes value2 + nodes value34 + (nodes value36 + nodes value40 + 0)) = 71
  simp only [nodes_value2,nodes_value34,nodes_value36,nodes_value40]
  all_goals decide +kernel
theorem depth_value96 : depth value96 = 6 := by
  change max (max (1 + depth value2) (1 + depth value34)) (max (max (1 + depth value36) (1 + depth value40)) (0)) = 6
  simp only [depth_value2,depth_value34,depth_value36,depth_value40]
  all_goals decide +kernel
theorem canonical_value96 : canonical models value96 = true := by
  change ((canonical models value2 && canonical models value34 && (canonical models value36 && canonical models value40 && true)) && ordered [encode value2,encode value36]) = true
  simp only [canonical_value2,canonical_value34,canonical_value36,canonical_value40,encoded_value2,encoded_value36]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value36,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value96 : rawvalue96.length = 1191 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value34) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value36) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value40) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value97 : Value := .set (.cons value96 .nil)
noncomputable def rawvalue97 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue96] ++ [93,93]
theorem encoded_value97 : encode value97 = rawvalue97 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value96] ++ [93,93] = _
  simp only [encoded_value96]
  all_goals rfl
theorem nodes_value97 : nodes value97 = 72 := by
  change 1 + (nodes value96 + 0) = 72
  simp only [nodes_value96]
  all_goals decide +kernel
theorem depth_value97 : depth value97 = 7 := by
  change max (1 + depth value96) (0) = 7
  simp only [depth_value96]
  all_goals decide +kernel
theorem canonical_value97 : canonical models value97 = true := by
  change ((canonical models value96 && true) && ordered [encode value96]) = true
  simp only [canonical_value96,encoded_value96]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value97 : rawvalue97.length = 1201 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value96)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value98 : Value := .function (.cons value2 value15 (.cons value72 value87 (.cons value36 value40 .nil)))
noncomputable def rawvalue98 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue15 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue87 ++ [93]),([91] ++ rawvalue36 ++ [44] ++ rawvalue40 ++ [93])] ++ [93,93]
theorem encoded_value98 : encode value98 = rawvalue98 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value15 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value87 ++ [93]),([91] ++ encode value36 ++ [44] ++ encode value40 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value15,encoded_value72,encoded_value87,encoded_value36,encoded_value40]
  all_goals rfl
theorem order_value72_value36 : byteLess rawvalue72 rawvalue36 = true := by
  simp only [rawvalue72,rawvalue36,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value98 : nodes value98 = 16 := by
  change 1 + (nodes value2 + nodes value15 + (nodes value72 + nodes value87 + (nodes value36 + nodes value40 + 0))) = 16
  simp only [nodes_value2,nodes_value15,nodes_value72,nodes_value87,nodes_value36,nodes_value40]
  all_goals decide +kernel
theorem depth_value98 : depth value98 = 2 := by
  change max (max (1 + depth value2) (1 + depth value15)) (max (max (1 + depth value72) (1 + depth value87)) (max (max (1 + depth value36) (1 + depth value40)) (0))) = 2
  simp only [depth_value2,depth_value15,depth_value72,depth_value87,depth_value36,depth_value40]
  all_goals decide +kernel
theorem canonical_value98 : canonical models value98 = true := by
  change ((canonical models value2 && canonical models value15 && (canonical models value72 && canonical models value87 && (canonical models value36 && canonical models value40 && true))) && ordered [encode value2,encode value72,encode value36]) = true
  simp only [canonical_value2,canonical_value15,canonical_value72,canonical_value87,canonical_value36,canonical_value40,encoded_value2,encoded_value72,encoded_value36]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value36,order_value72_value36,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value98 : rawvalue98.length = 262 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value15) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value87) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value36) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value40) (show ([93] : Bytes).length = 1 from by decide +kernel)))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value99 : Value := .set (.cons value98 .nil)
noncomputable def rawvalue99 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue98] ++ [93,93]
theorem encoded_value99 : encode value99 = rawvalue99 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value98] ++ [93,93] = _
  simp only [encoded_value98]
  all_goals rfl
theorem nodes_value99 : nodes value99 = 17 := by
  change 1 + (nodes value98 + 0) = 17
  simp only [nodes_value98]
  all_goals decide +kernel
theorem depth_value99 : depth value99 = 3 := by
  change max (1 + depth value98) (0) = 3
  simp only [depth_value98]
  all_goals decide +kernel
theorem canonical_value99 : canonical models value99 = true := by
  change ((canonical models value98 && true) && ordered [encode value98]) = true
  simp only [canonical_value98,encoded_value98]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value99 : rawvalue99.length = 272 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value98)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value100 : Value := .function (.cons value2 value25 (.cons value36 value40 .nil))
noncomputable def rawvalue100 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue25 ++ [93]),([91] ++ rawvalue36 ++ [44] ++ rawvalue40 ++ [93])] ++ [93,93]
theorem encoded_value100 : encode value100 = rawvalue100 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value25 ++ [93]),([91] ++ encode value36 ++ [44] ++ encode value40 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value25,encoded_value36,encoded_value40]
  all_goals rfl
theorem nodes_value100 : nodes value100 = 32 := by
  change 1 + (nodes value2 + nodes value25 + (nodes value36 + nodes value40 + 0)) = 32
  simp only [nodes_value2,nodes_value25,nodes_value36,nodes_value40]
  all_goals decide +kernel
theorem depth_value100 : depth value100 = 4 := by
  change max (max (1 + depth value2) (1 + depth value25)) (max (max (1 + depth value36) (1 + depth value40)) (0)) = 4
  simp only [depth_value2,depth_value25,depth_value36,depth_value40]
  all_goals decide +kernel
theorem canonical_value100 : canonical models value100 = true := by
  change ((canonical models value2 && canonical models value25 && (canonical models value36 && canonical models value40 && true)) && ordered [encode value2,encode value36]) = true
  simp only [canonical_value2,canonical_value25,canonical_value36,canonical_value40,encoded_value2,encoded_value36]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value36,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value100 : rawvalue100.length = 531 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value25) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value36) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value40) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value101 : Value := .set (.cons value100 .nil)
noncomputable def rawvalue101 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue100] ++ [93,93]
theorem encoded_value101 : encode value101 = rawvalue101 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value100] ++ [93,93] = _
  simp only [encoded_value100]
  all_goals rfl
theorem nodes_value101 : nodes value101 = 33 := by
  change 1 + (nodes value100 + 0) = 33
  simp only [nodes_value100]
  all_goals decide +kernel
theorem depth_value101 : depth value101 = 5 := by
  change max (1 + depth value100) (0) = 5
  simp only [depth_value100]
  all_goals decide +kernel
theorem canonical_value101 : canonical models value101 = true := by
  change ((canonical models value100 && true) && ordered [encode value100]) = true
  simp only [canonical_value100,encoded_value100]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value101 : rawvalue101.length = 541 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value100)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value102 : Value := .function (.cons value2 value25 (.cons value45 value37 .nil))
noncomputable def rawvalue102 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue25 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue37 ++ [93])] ++ [93,93]
theorem encoded_value102 : encode value102 = rawvalue102 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value25 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value37 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value25,encoded_value45,encoded_value37]
  all_goals rfl
theorem nodes_value102 : nodes value102 = 29 := by
  change 1 + (nodes value2 + nodes value25 + (nodes value45 + nodes value37 + 0)) = 29
  simp only [nodes_value2,nodes_value25,nodes_value45,nodes_value37]
  all_goals decide +kernel
theorem depth_value102 : depth value102 = 4 := by
  change max (max (1 + depth value2) (1 + depth value25)) (max (max (1 + depth value45) (1 + depth value37)) (0)) = 4
  simp only [depth_value2,depth_value25,depth_value45,depth_value37]
  all_goals decide +kernel
theorem canonical_value102 : canonical models value102 = true := by
  change ((canonical models value2 && canonical models value25 && (canonical models value45 && canonical models value37 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value25,canonical_value45,canonical_value37,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value102 : rawvalue102.length = 493 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value25) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value37) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value103 : Value := .function (.cons value2 value25 (.cons value45 value38 .nil))
noncomputable def rawvalue103 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue25 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue38 ++ [93])] ++ [93,93]
theorem encoded_value103 : encode value103 = rawvalue103 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value25 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value38 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value25,encoded_value45,encoded_value38]
  all_goals rfl
theorem nodes_value103 : nodes value103 = 29 := by
  change 1 + (nodes value2 + nodes value25 + (nodes value45 + nodes value38 + 0)) = 29
  simp only [nodes_value2,nodes_value25,nodes_value45,nodes_value38]
  all_goals decide +kernel
theorem depth_value103 : depth value103 = 4 := by
  change max (max (1 + depth value2) (1 + depth value25)) (max (max (1 + depth value45) (1 + depth value38)) (0)) = 4
  simp only [depth_value2,depth_value25,depth_value45,depth_value38]
  all_goals decide +kernel
theorem canonical_value103 : canonical models value103 = true := by
  change ((canonical models value2 && canonical models value25 && (canonical models value45 && canonical models value38 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value25,canonical_value45,canonical_value38,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value103 : rawvalue103.length = 493 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value25) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value38) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value104 : Value := .function (.cons value2 value25 (.cons value45 value39 .nil))
noncomputable def rawvalue104 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue25 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue39 ++ [93])] ++ [93,93]
theorem encoded_value104 : encode value104 = rawvalue104 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value25 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value39 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value25,encoded_value45,encoded_value39]
  all_goals rfl
theorem nodes_value104 : nodes value104 = 29 := by
  change 1 + (nodes value2 + nodes value25 + (nodes value45 + nodes value39 + 0)) = 29
  simp only [nodes_value2,nodes_value25,nodes_value45,nodes_value39]
  all_goals decide +kernel
theorem depth_value104 : depth value104 = 4 := by
  change max (max (1 + depth value2) (1 + depth value25)) (max (max (1 + depth value45) (1 + depth value39)) (0)) = 4
  simp only [depth_value2,depth_value25,depth_value45,depth_value39]
  all_goals decide +kernel
theorem canonical_value104 : canonical models value104 = true := by
  change ((canonical models value2 && canonical models value25 && (canonical models value45 && canonical models value39 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value25,canonical_value45,canonical_value39,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value104 : rawvalue104.length = 493 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value25) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value39) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value105 : Value := .set (.cons value102 (.cons value103 (.cons value104 .nil)))
noncomputable def rawvalue105 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue102,rawvalue103,rawvalue104] ++ [93,93]
theorem encoded_value105 : encode value105 = rawvalue105 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value102,encode value103,encode value104] ++ [93,93] = _
  simp only [encoded_value102,encoded_value103,encoded_value104]
  all_goals rfl
theorem order_value102_value103 : byteLess rawvalue102 rawvalue103 = true := by
  simp only [rawvalue102,rawvalue103,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue38,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value102_value104 : byteLess rawvalue102 rawvalue104 = true := by
  simp only [rawvalue102,rawvalue104,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value103_value104 : byteLess rawvalue103 rawvalue104 = true := by
  simp only [rawvalue103,rawvalue104,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue38,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value105 : nodes value105 = 88 := by
  change 1 + (nodes value102 + (nodes value103 + (nodes value104 + 0))) = 88
  simp only [nodes_value102,nodes_value103,nodes_value104]
  all_goals decide +kernel
theorem depth_value105 : depth value105 = 5 := by
  change max (1 + depth value102) (max (1 + depth value103) (max (1 + depth value104) (0))) = 5
  simp only [depth_value102,depth_value103,depth_value104]
  all_goals decide +kernel
theorem canonical_value105 : canonical models value105 = true := by
  change ((canonical models value102 && (canonical models value103 && (canonical models value104 && true))) && ordered [encode value102,encode value103,encode value104]) = true
  simp only [canonical_value102,canonical_value103,canonical_value104,encoded_value102,encoded_value103,encoded_value104]
  simp only [ordered,List.all_cons,List.all_nil,order_value102_value103,order_value102_value104,order_value103_value104,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value105 : rawvalue105.length = 1491 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value102 (commaConsLength rawLength_value103 (commaSingletonLength rawLength_value104)))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value106 : Value := .function (.cons value11 value64 .nil)
noncomputable def rawvalue106 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue11 ++ [44] ++ rawvalue64 ++ [93])] ++ [93,93]
theorem encoded_value106 : encode value106 = rawvalue106 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value11 ++ [44] ++ encode value64 ++ [93])] ++ [93,93] = _
  simp only [encoded_value11,encoded_value64]
  all_goals rfl
theorem nodes_value106 : nodes value106 = 3 := by
  change 1 + (nodes value11 + nodes value64 + 0) = 3
  simp only [nodes_value11,nodes_value64]
  all_goals decide +kernel
theorem depth_value106 : depth value106 = 1 := by
  change max (max (1 + depth value11) (1 + depth value64)) (0) = 1
  simp only [depth_value11,depth_value64]
  all_goals decide +kernel
theorem canonical_value106 : canonical models value106 = true := by
  change ((canonical models value11 && canonical models value64 && true) && ordered [encode value11]) = true
  simp only [canonical_value11,canonical_value64,encoded_value11]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value106 : rawvalue106.length = 38 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value11) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value64) (show ([93] : Bytes).length = 1 from by decide +kernel)))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value107 : Value := .function (.cons value11 value66 .nil)
noncomputable def rawvalue107 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue11 ++ [44] ++ rawvalue66 ++ [93])] ++ [93,93]
theorem encoded_value107 : encode value107 = rawvalue107 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value11 ++ [44] ++ encode value66 ++ [93])] ++ [93,93] = _
  simp only [encoded_value11,encoded_value66]
  all_goals rfl
theorem nodes_value107 : nodes value107 = 3 := by
  change 1 + (nodes value11 + nodes value66 + 0) = 3
  simp only [nodes_value11,nodes_value66]
  all_goals decide +kernel
theorem depth_value107 : depth value107 = 1 := by
  change max (max (1 + depth value11) (1 + depth value66)) (0) = 1
  simp only [depth_value11,depth_value66]
  all_goals decide +kernel
theorem canonical_value107 : canonical models value107 = true := by
  change ((canonical models value11 && canonical models value66 && true) && ordered [encode value11]) = true
  simp only [canonical_value11,canonical_value66,encoded_value11]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value107 : rawvalue107.length = 41 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value11) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value66) (show ([93] : Bytes).length = 1 from by decide +kernel)))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value108 : Value := .integer (18)
noncomputable def rawvalue108 : Bytes := asciiBytes "[\"int\",\"18\"]"
theorem encoded_value108 : encode value108 = rawvalue108 := by
  all_goals rfl
theorem nodes_value108 : nodes value108 = 1 := by rfl
theorem depth_value108 : depth value108 = 0 := by rfl
theorem canonical_value108 : canonical models value108 = true := by decide +kernel
theorem rawLength_value108 : rawvalue108.length = 12 := by
  decide +kernel
noncomputable def value109 : Value := .text "apc"
noncomputable def rawvalue109 : Bytes := asciiBytes "[\"str\",\"apc\"]"
theorem encoded_value109 : encode value109 = rawvalue109 := by
  all_goals rfl
theorem nodes_value109 : nodes value109 = 1 := by rfl
theorem depth_value109 : depth value109 = 0 := by rfl
theorem canonical_value109 : canonical models value109 = true := by decide +kernel
theorem rawLength_value109 : rawvalue109.length = 13 := by
  decide +kernel
noncomputable def value110 : Value := .text "arithmeticProfile"
noncomputable def rawvalue110 : Bytes := asciiBytes "[\"str\",\"arithmeticProfile\"]"
theorem encoded_value110 : encode value110 = rawvalue110 := by
  all_goals rfl
theorem nodes_value110 : nodes value110 = 1 := by rfl
theorem depth_value110 : depth value110 = 0 := by rfl
theorem canonical_value110 : canonical models value110 = true := by decide +kernel
theorem rawLength_value110 : rawvalue110.length = 27 := by
  decide +kernel
noncomputable def value111 : Value := .model "profile1"
noncomputable def rawvalue111 : Bytes := asciiBytes "[\"model\",\"profile1\"]"
theorem encoded_value111 : encode value111 = rawvalue111 := by
  all_goals rfl
theorem nodes_value111 : nodes value111 = 1 := by rfl
theorem depth_value111 : depth value111 = 0 := by rfl
theorem canonical_value111 : canonical models value111 = true := by decide +kernel
theorem rawLength_value111 : rawvalue111.length = 20 := by
  decide +kernel
noncomputable def value112 : Value := .text "authority"
noncomputable def rawvalue112 : Bytes := asciiBytes "[\"str\",\"authority\"]"
theorem encoded_value112 : encode value112 = rawvalue112 := by
  all_goals rfl
theorem nodes_value112 : nodes value112 = 1 := by rfl
theorem depth_value112 : depth value112 = 0 := by rfl
theorem canonical_value112 : canonical models value112 = true := by decide +kernel
theorem rawLength_value112 : rawvalue112.length = 19 := by
  decide +kernel
noncomputable def value113 : Value := .text "applyProfile"
noncomputable def rawvalue113 : Bytes := asciiBytes "[\"str\",\"applyProfile\"]"
theorem encoded_value113 : encode value113 = rawvalue113 := by
  all_goals rfl
theorem nodes_value113 : nodes value113 = 1 := by rfl
theorem depth_value113 : depth value113 = 0 := by rfl
theorem canonical_value113 : canonical models value113 = true := by decide +kernel
theorem rawLength_value113 : rawvalue113.length = 22 := by
  decide +kernel
noncomputable def value114 : Value := .model "apply1"
noncomputable def rawvalue114 : Bytes := asciiBytes "[\"model\",\"apply1\"]"
theorem encoded_value114 : encode value114 = rawvalue114 := by
  all_goals rfl
theorem nodes_value114 : nodes value114 = 1 := by rfl
theorem depth_value114 : depth value114 = 0 := by rfl
theorem canonical_value114 : canonical models value114 = true := by decide +kernel
theorem rawLength_value114 : rawvalue114.length = 18 := by
  decide +kernel
noncomputable def value115 : Value := .text "inputs"
noncomputable def rawvalue115 : Bytes := asciiBytes "[\"str\",\"inputs\"]"
theorem encoded_value115 : encode value115 = rawvalue115 := by
  all_goals rfl
theorem nodes_value115 : nodes value115 = 1 := by rfl
theorem depth_value115 : depth value115 = 0 := by rfl
theorem canonical_value115 : canonical models value115 = true := by decide +kernel
theorem rawLength_value115 : rawvalue115.length = 16 := by
  decide +kernel
noncomputable def value116 : Value := .text "applyD"
noncomputable def rawvalue116 : Bytes := asciiBytes "[\"str\",\"applyD\"]"
theorem encoded_value116 : encode value116 = rawvalue116 := by
  all_goals rfl
theorem nodes_value116 : nodes value116 = 1 := by rfl
theorem depth_value116 : depth value116 = 0 := by rfl
theorem canonical_value116 : canonical models value116 = true := by decide +kernel
theorem rawLength_value116 : rawvalue116.length = 16 := by
  decide +kernel
noncomputable def value117 : Value := .integer (1)
noncomputable def rawvalue117 : Bytes := asciiBytes "[\"int\",\"1\"]"
theorem encoded_value117 : encode value117 = rawvalue117 := by
  all_goals rfl
theorem nodes_value117 : nodes value117 = 1 := by rfl
theorem depth_value117 : depth value117 = 0 := by rfl
theorem canonical_value117 : canonical models value117 = true := by decide +kernel
theorem rawLength_value117 : rawvalue117.length = 11 := by
  decide +kernel
noncomputable def value118 : Value := .text "applyN"
noncomputable def rawvalue118 : Bytes := asciiBytes "[\"str\",\"applyN\"]"
theorem encoded_value118 : encode value118 = rawvalue118 := by
  all_goals rfl
theorem nodes_value118 : nodes value118 = 1 := by rfl
theorem depth_value118 : depth value118 = 0 := by rfl
theorem canonical_value118 : canonical models value118 = true := by decide +kernel
theorem rawLength_value118 : rawvalue118.length = 16 := by
  decide +kernel
noncomputable def value119 : Value := .text "denominator"
noncomputable def rawvalue119 : Bytes := asciiBytes "[\"str\",\"denominator\"]"
theorem encoded_value119 : encode value119 = rawvalue119 := by
  all_goals rfl
theorem nodes_value119 : nodes value119 = 1 := by rfl
theorem depth_value119 : depth value119 = 0 := by rfl
theorem canonical_value119 : canonical models value119 = true := by decide +kernel
theorem rawLength_value119 : rawvalue119.length = 21 := by
  decide +kernel
noncomputable def value120 : Value := .model "d1"
noncomputable def rawvalue120 : Bytes := asciiBytes "[\"model\",\"d1\"]"
theorem encoded_value120 : encode value120 = rawvalue120 := by
  all_goals rfl
theorem nodes_value120 : nodes value120 = 1 := by rfl
theorem depth_value120 : depth value120 = 0 := by rfl
theorem canonical_value120 : canonical models value120 = true := by decide +kernel
theorem rawLength_value120 : rawvalue120.length = 14 := by
  decide +kernel
noncomputable def value121 : Value := .function (.cons value120 value117 .nil)
noncomputable def rawvalue121 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue120 ++ [44] ++ rawvalue117 ++ [93])] ++ [93,93]
theorem encoded_value121 : encode value121 = rawvalue121 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value120 ++ [44] ++ encode value117 ++ [93])] ++ [93,93] = _
  simp only [encoded_value120,encoded_value117]
  all_goals rfl
theorem nodes_value121 : nodes value121 = 3 := by
  change 1 + (nodes value120 + nodes value117 + 0) = 3
  simp only [nodes_value120,nodes_value117]
  all_goals decide +kernel
theorem depth_value121 : depth value121 = 1 := by
  change max (max (1 + depth value120) (1 + depth value117)) (0) = 1
  simp only [depth_value120,depth_value117]
  all_goals decide +kernel
theorem canonical_value121 : canonical models value121 = true := by
  change ((canonical models value120 && canonical models value117 && true) && ordered [encode value120]) = true
  simp only [canonical_value120,canonical_value117,encoded_value120]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value121 : rawvalue121.length = 38 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value120) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value117) (show ([93] : Bytes).length = 1 from by decide +kernel)))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value122 : Value := .text "domainOrder"
noncomputable def rawvalue122 : Bytes := asciiBytes "[\"str\",\"domainOrder\"]"
theorem encoded_value122 : encode value122 = rawvalue122 := by
  all_goals rfl
theorem nodes_value122 : nodes value122 = 1 := by rfl
theorem depth_value122 : depth value122 = 0 := by rfl
theorem canonical_value122 : canonical models value122 = true := by decide +kernel
theorem rawLength_value122 : rawvalue122.length = 21 := by
  decide +kernel
noncomputable def value123 : Value := .function (.cons value117 value120 .nil)
noncomputable def rawvalue123 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue117 ++ [44] ++ rawvalue120 ++ [93])] ++ [93,93]
theorem encoded_value123 : encode value123 = rawvalue123 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value117 ++ [44] ++ encode value120 ++ [93])] ++ [93,93] = _
  simp only [encoded_value117,encoded_value120]
  all_goals rfl
theorem nodes_value123 : nodes value123 = 3 := by
  change 1 + (nodes value117 + nodes value120 + 0) = 3
  simp only [nodes_value117,nodes_value120]
  all_goals decide +kernel
theorem depth_value123 : depth value123 = 1 := by
  change max (max (1 + depth value117) (1 + depth value120)) (0) = 1
  simp only [depth_value117,depth_value120]
  all_goals decide +kernel
theorem canonical_value123 : canonical models value123 = true := by
  change ((canonical models value117 && canonical models value120 && true) && ordered [encode value117]) = true
  simp only [canonical_value117,canonical_value120,encoded_value117]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value123 : rawvalue123.length = 38 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value117) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value120) (show ([93] : Bytes).length = 1 from by decide +kernel)))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value124 : Value := .text "limit"
noncomputable def rawvalue124 : Bytes := asciiBytes "[\"str\",\"limit\"]"
theorem encoded_value124 : encode value124 = rawvalue124 := by
  all_goals rfl
theorem nodes_value124 : nodes value124 = 1 := by rfl
theorem depth_value124 : depth value124 = 0 := by rfl
theorem canonical_value124 : canonical models value124 = true := by decide +kernel
theorem rawLength_value124 : rawvalue124.length = 15 := by
  decide +kernel
noncomputable def value125 : Value := .integer (127)
noncomputable def rawvalue125 : Bytes := asciiBytes "[\"int\",\"127\"]"
theorem encoded_value125 : encode value125 = rawvalue125 := by
  all_goals rfl
theorem nodes_value125 : nodes value125 = 1 := by rfl
theorem depth_value125 : depth value125 = 0 := by rfl
theorem canonical_value125 : canonical models value125 = true := by decide +kernel
theorem rawLength_value125 : rawvalue125.length = 13 := by
  decide +kernel
noncomputable def value126 : Value := .text "lrD"
noncomputable def rawvalue126 : Bytes := asciiBytes "[\"str\",\"lrD\"]"
theorem encoded_value126 : encode value126 = rawvalue126 := by
  all_goals rfl
theorem nodes_value126 : nodes value126 = 1 := by rfl
theorem depth_value126 : depth value126 = 0 := by rfl
theorem canonical_value126 : canonical models value126 = true := by decide +kernel
theorem rawLength_value126 : rawvalue126.length = 13 := by
  decide +kernel
noncomputable def value127 : Value := .integer (2)
noncomputable def rawvalue127 : Bytes := asciiBytes "[\"int\",\"2\"]"
theorem encoded_value127 : encode value127 = rawvalue127 := by
  all_goals rfl
theorem nodes_value127 : nodes value127 = 1 := by rfl
theorem depth_value127 : depth value127 = 0 := by rfl
theorem canonical_value127 : canonical models value127 = true := by decide +kernel
theorem rawLength_value127 : rawvalue127.length = 11 := by
  decide +kernel
noncomputable def value128 : Value := .text "lrN"
noncomputable def rawvalue128 : Bytes := asciiBytes "[\"str\",\"lrN\"]"
theorem encoded_value128 : encode value128 = rawvalue128 := by
  all_goals rfl
theorem nodes_value128 : nodes value128 = 1 := by rfl
theorem depth_value128 : depth value128 = 0 := by rfl
theorem canonical_value128 : canonical models value128 = true := by decide +kernel
theorem rawLength_value128 : rawvalue128.length = 13 := by
  decide +kernel
noncomputable def value129 : Value := .text "mixtureD"
noncomputable def rawvalue129 : Bytes := asciiBytes "[\"str\",\"mixtureD\"]"
theorem encoded_value129 : encode value129 = rawvalue129 := by
  all_goals rfl
theorem nodes_value129 : nodes value129 = 1 := by rfl
theorem depth_value129 : depth value129 = 0 := by rfl
theorem canonical_value129 : canonical models value129 = true := by decide +kernel
theorem rawLength_value129 : rawvalue129.length = 18 := by
  decide +kernel
noncomputable def value130 : Value := .text "model"
noncomputable def rawvalue130 : Bytes := asciiBytes "[\"str\",\"model\"]"
theorem encoded_value130 : encode value130 = rawvalue130 := by
  all_goals rfl
theorem nodes_value130 : nodes value130 = 1 := by rfl
theorem depth_value130 : depth value130 = 0 := by rfl
theorem canonical_value130 : canonical models value130 = true := by decide +kernel
theorem rawLength_value130 : rawvalue130.length = 15 := by
  decide +kernel
noncomputable def value131 : Value := .integer (20)
noncomputable def rawvalue131 : Bytes := asciiBytes "[\"int\",\"20\"]"
theorem encoded_value131 : encode value131 = rawvalue131 := by
  all_goals rfl
theorem nodes_value131 : nodes value131 = 1 := by rfl
theorem depth_value131 : depth value131 = 0 := by rfl
theorem canonical_value131 : canonical models value131 = true := by decide +kernel
theorem rawLength_value131 : rawvalue131.length = 12 := by
  decide +kernel
noncomputable def value132 : Value := .integer (-20)
noncomputable def rawvalue132 : Bytes := asciiBytes "[\"int\",\"-20\"]"
theorem encoded_value132 : encode value132 = rawvalue132 := by
  all_goals rfl
theorem nodes_value132 : nodes value132 = 1 := by rfl
theorem depth_value132 : depth value132 = 0 := by rfl
theorem canonical_value132 : canonical models value132 = true := by decide +kernel
theorem rawLength_value132 : rawvalue132.length = 13 := by
  decide +kernel
noncomputable def value133 : Value := .function (.cons value51 value131 (.cons value55 value132 .nil))
noncomputable def rawvalue133 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue51 ++ [44] ++ rawvalue131 ++ [93]),([91] ++ rawvalue55 ++ [44] ++ rawvalue132 ++ [93])] ++ [93,93]
theorem encoded_value133 : encode value133 = rawvalue133 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value51 ++ [44] ++ encode value131 ++ [93]),([91] ++ encode value55 ++ [44] ++ encode value132 ++ [93])] ++ [93,93] = _
  simp only [encoded_value51,encoded_value131,encoded_value55,encoded_value132]
  all_goals rfl
theorem order_value51_value55 : byteLess rawvalue51 rawvalue55 = true := by
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value133 : nodes value133 = 5 := by
  change 1 + (nodes value51 + nodes value131 + (nodes value55 + nodes value132 + 0)) = 5
  simp only [nodes_value51,nodes_value131,nodes_value55,nodes_value132]
  all_goals decide +kernel
theorem depth_value133 : depth value133 = 1 := by
  change max (max (1 + depth value51) (1 + depth value131)) (max (max (1 + depth value55) (1 + depth value132)) (0)) = 1
  simp only [depth_value51,depth_value131,depth_value55,depth_value132]
  all_goals decide +kernel
theorem canonical_value133 : canonical models value133 = true := by
  change ((canonical models value51 && canonical models value131 && (canonical models value55 && canonical models value132 && true)) && ordered [encode value51,encode value55]) = true
  simp only [canonical_value51,canonical_value131,canonical_value55,canonical_value132,encoded_value51,encoded_value55]
  simp only [ordered,List.all_cons,List.all_nil,order_value51_value55,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value133 : rawvalue133.length = 78 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value51) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value131) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value55) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value132) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value134 : Value := .text "muD"
noncomputable def rawvalue134 : Bytes := asciiBytes "[\"str\",\"muD\"]"
theorem encoded_value134 : encode value134 = rawvalue134 := by
  all_goals rfl
theorem nodes_value134 : nodes value134 = 1 := by rfl
theorem depth_value134 : depth value134 = 0 := by rfl
theorem canonical_value134 : canonical models value134 = true := by decide +kernel
theorem rawLength_value134 : rawvalue134.length = 13 := by
  decide +kernel
noncomputable def value135 : Value := .text "muN"
noncomputable def rawvalue135 : Bytes := asciiBytes "[\"str\",\"muN\"]"
theorem encoded_value135 : encode value135 = rawvalue135 := by
  all_goals rfl
theorem nodes_value135 : nodes value135 = 1 := by rfl
theorem depth_value135 : depth value135 = 0 := by rfl
theorem canonical_value135 : canonical models value135 = true := by decide +kernel
theorem rawLength_value135 : rawvalue135.length = 13 := by
  decide +kernel
noncomputable def value136 : Value := .text "optimizer"
noncomputable def rawvalue136 : Bytes := asciiBytes "[\"str\",\"optimizer\"]"
theorem encoded_value136 : encode value136 = rawvalue136 := by
  all_goals rfl
theorem nodes_value136 : nodes value136 = 1 := by rfl
theorem depth_value136 : depth value136 = 0 := by rfl
theorem canonical_value136 : canonical models value136 = true := by decide +kernel
theorem rawLength_value136 : rawvalue136.length = 19 := by
  decide +kernel
noncomputable def value137 : Value := .integer (-2)
noncomputable def rawvalue137 : Bytes := asciiBytes "[\"int\",\"-2\"]"
theorem encoded_value137 : encode value137 = rawvalue137 := by
  all_goals rfl
theorem nodes_value137 : nodes value137 = 1 := by rfl
theorem depth_value137 : depth value137 = 0 := by rfl
theorem canonical_value137 : canonical models value137 = true := by decide +kernel
theorem rawLength_value137 : rawvalue137.length = 12 := by
  decide +kernel
noncomputable def value138 : Value := .function (.cons value51 value127 (.cons value55 value137 .nil))
noncomputable def rawvalue138 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue51 ++ [44] ++ rawvalue127 ++ [93]),([91] ++ rawvalue55 ++ [44] ++ rawvalue137 ++ [93])] ++ [93,93]
theorem encoded_value138 : encode value138 = rawvalue138 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value51 ++ [44] ++ encode value127 ++ [93]),([91] ++ encode value55 ++ [44] ++ encode value137 ++ [93])] ++ [93,93] = _
  simp only [encoded_value51,encoded_value127,encoded_value55,encoded_value137]
  all_goals rfl
theorem nodes_value138 : nodes value138 = 5 := by
  change 1 + (nodes value51 + nodes value127 + (nodes value55 + nodes value137 + 0)) = 5
  simp only [nodes_value51,nodes_value127,nodes_value55,nodes_value137]
  all_goals decide +kernel
theorem depth_value138 : depth value138 = 1 := by
  change max (max (1 + depth value51) (1 + depth value127)) (max (max (1 + depth value55) (1 + depth value137)) (0)) = 1
  simp only [depth_value51,depth_value127,depth_value55,depth_value137]
  all_goals decide +kernel
theorem canonical_value138 : canonical models value138 = true := by
  change ((canonical models value51 && canonical models value127 && (canonical models value55 && canonical models value137 && true)) && ordered [encode value51,encode value55]) = true
  simp only [canonical_value51,canonical_value127,canonical_value55,canonical_value137,encoded_value51,encoded_value55]
  simp only [ordered,List.all_cons,List.all_nil,order_value51_value55,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value138 : rawvalue138.length = 76 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value51) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value127) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value55) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value137) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value139 : Value := .text "piD"
noncomputable def rawvalue139 : Bytes := asciiBytes "[\"str\",\"piD\"]"
theorem encoded_value139 : encode value139 = rawvalue139 := by
  all_goals rfl
theorem nodes_value139 : nodes value139 = 1 := by rfl
theorem depth_value139 : depth value139 = 0 := by rfl
theorem canonical_value139 : canonical models value139 = true := by decide +kernel
theorem rawLength_value139 : rawvalue139.length = 13 := by
  decide +kernel
noncomputable def value140 : Value := .text "piN"
noncomputable def rawvalue140 : Bytes := asciiBytes "[\"str\",\"piN\"]"
theorem encoded_value140 : encode value140 = rawvalue140 := by
  all_goals rfl
theorem nodes_value140 : nodes value140 = 1 := by rfl
theorem depth_value140 : depth value140 = 0 := by rfl
theorem canonical_value140 : canonical models value140 = true := by decide +kernel
theorem rawLength_value140 : rawvalue140.length = 13 := by
  decide +kernel
noncomputable def value141 : Value := .text "q"
noncomputable def rawvalue141 : Bytes := asciiBytes "[\"str\",\"q\"]"
theorem encoded_value141 : encode value141 = rawvalue141 := by
  all_goals rfl
theorem nodes_value141 : nodes value141 = 1 := by rfl
theorem depth_value141 : depth value141 = 0 := by rfl
theorem canonical_value141 : canonical models value141 = true := by decide +kernel
theorem rawLength_value141 : rawvalue141.length = 11 := by
  decide +kernel
noncomputable def value142 : Value := .function (.cons value51 value117 (.cons value55 value137 .nil))
noncomputable def rawvalue142 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue51 ++ [44] ++ rawvalue117 ++ [93]),([91] ++ rawvalue55 ++ [44] ++ rawvalue137 ++ [93])] ++ [93,93]
theorem encoded_value142 : encode value142 = rawvalue142 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value51 ++ [44] ++ encode value117 ++ [93]),([91] ++ encode value55 ++ [44] ++ encode value137 ++ [93])] ++ [93,93] = _
  simp only [encoded_value51,encoded_value117,encoded_value55,encoded_value137]
  all_goals rfl
theorem nodes_value142 : nodes value142 = 5 := by
  change 1 + (nodes value51 + nodes value117 + (nodes value55 + nodes value137 + 0)) = 5
  simp only [nodes_value51,nodes_value117,nodes_value55,nodes_value137]
  all_goals decide +kernel
theorem depth_value142 : depth value142 = 1 := by
  change max (max (1 + depth value51) (1 + depth value117)) (max (max (1 + depth value55) (1 + depth value137)) (0)) = 1
  simp only [depth_value51,depth_value117,depth_value55,depth_value137]
  all_goals decide +kernel
theorem canonical_value142 : canonical models value142 = true := by
  change ((canonical models value51 && canonical models value117 && (canonical models value55 && canonical models value137 && true)) && ordered [encode value51,encode value55]) = true
  simp only [canonical_value51,canonical_value117,canonical_value55,canonical_value137,encoded_value51,encoded_value55]
  simp only [ordered,List.all_cons,List.all_nil,order_value51_value55,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value142 : rawvalue142.length = 76 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value51) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value117) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value55) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value137) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value143 : Value := .function (.cons value11 value142 .nil)
noncomputable def rawvalue143 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue11 ++ [44] ++ rawvalue142 ++ [93])] ++ [93,93]
theorem encoded_value143 : encode value143 = rawvalue143 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value11 ++ [44] ++ encode value142 ++ [93])] ++ [93,93] = _
  simp only [encoded_value11,encoded_value142]
  all_goals rfl
theorem nodes_value143 : nodes value143 = 7 := by
  change 1 + (nodes value11 + nodes value142 + 0) = 7
  simp only [nodes_value11,nodes_value142]
  all_goals decide +kernel
theorem depth_value143 : depth value143 = 2 := by
  change max (max (1 + depth value11) (1 + depth value142)) (0) = 2
  simp only [depth_value11,depth_value142]
  all_goals decide +kernel
theorem canonical_value143 : canonical models value143 = true := by
  change ((canonical models value11 && canonical models value142 && true) && ordered [encode value11]) = true
  simp only [canonical_value11,canonical_value142,encoded_value11]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value143 : rawvalue143.length = 103 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value11) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value142) (show ([93] : Bytes).length = 1 from by decide +kernel)))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value144 : Value := .text "qD"
noncomputable def rawvalue144 : Bytes := asciiBytes "[\"str\",\"qD\"]"
theorem encoded_value144 : encode value144 = rawvalue144 := by
  all_goals rfl
theorem nodes_value144 : nodes value144 = 1 := by rfl
theorem depth_value144 : depth value144 = 0 := by rfl
theorem canonical_value144 : canonical models value144 = true := by decide +kernel
theorem rawLength_value144 : rawvalue144.length = 12 := by
  decide +kernel
noncomputable def value145 : Value := .function (.cons value51 value127 (.cons value55 value127 .nil))
noncomputable def rawvalue145 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue51 ++ [44] ++ rawvalue127 ++ [93]),([91] ++ rawvalue55 ++ [44] ++ rawvalue127 ++ [93])] ++ [93,93]
theorem encoded_value145 : encode value145 = rawvalue145 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value51 ++ [44] ++ encode value127 ++ [93]),([91] ++ encode value55 ++ [44] ++ encode value127 ++ [93])] ++ [93,93] = _
  simp only [encoded_value51,encoded_value127,encoded_value55]
  all_goals rfl
theorem nodes_value145 : nodes value145 = 5 := by
  change 1 + (nodes value51 + nodes value127 + (nodes value55 + nodes value127 + 0)) = 5
  simp only [nodes_value51,nodes_value127,nodes_value55]
  all_goals decide +kernel
theorem depth_value145 : depth value145 = 1 := by
  change max (max (1 + depth value51) (1 + depth value127)) (max (max (1 + depth value55) (1 + depth value127)) (0)) = 1
  simp only [depth_value51,depth_value127,depth_value55]
  all_goals decide +kernel
theorem canonical_value145 : canonical models value145 = true := by
  change ((canonical models value51 && canonical models value127 && (canonical models value55 && canonical models value127 && true)) && ordered [encode value51,encode value55]) = true
  simp only [canonical_value51,canonical_value127,canonical_value55,encoded_value51,encoded_value55]
  simp only [ordered,List.all_cons,List.all_nil,order_value51_value55,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value145 : rawvalue145.length = 75 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value51) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value127) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value55) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value127) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value146 : Value := .function (.cons value120 value145 .nil)
noncomputable def rawvalue146 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue120 ++ [44] ++ rawvalue145 ++ [93])] ++ [93,93]
theorem encoded_value146 : encode value146 = rawvalue146 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value120 ++ [44] ++ encode value145 ++ [93])] ++ [93,93] = _
  simp only [encoded_value120,encoded_value145]
  all_goals rfl
theorem nodes_value146 : nodes value146 = 7 := by
  change 1 + (nodes value120 + nodes value145 + 0) = 7
  simp only [nodes_value120,nodes_value145]
  all_goals decide +kernel
theorem depth_value146 : depth value146 = 2 := by
  change max (max (1 + depth value120) (1 + depth value145)) (0) = 2
  simp only [depth_value120,depth_value145]
  all_goals decide +kernel
theorem canonical_value146 : canonical models value146 = true := by
  change ((canonical models value120 && canonical models value145 && true) && ordered [encode value120]) = true
  simp only [canonical_value120,canonical_value145,encoded_value120]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value146 : rawvalue146.length = 102 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value120) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value145) (show ([93] : Bytes).length = 1 from by decide +kernel)))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value147 : Value := .text "qN"
noncomputable def rawvalue147 : Bytes := asciiBytes "[\"str\",\"qN\"]"
theorem encoded_value147 : encode value147 = rawvalue147 := by
  all_goals rfl
theorem nodes_value147 : nodes value147 = 1 := by rfl
theorem depth_value147 : depth value147 = 0 := by rfl
theorem canonical_value147 : canonical models value147 = true := by decide +kernel
theorem rawLength_value147 : rawvalue147.length = 12 := by
  decide +kernel
noncomputable def value148 : Value := .function (.cons value51 value117 (.cons value55 value117 .nil))
noncomputable def rawvalue148 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue51 ++ [44] ++ rawvalue117 ++ [93]),([91] ++ rawvalue55 ++ [44] ++ rawvalue117 ++ [93])] ++ [93,93]
theorem encoded_value148 : encode value148 = rawvalue148 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value51 ++ [44] ++ encode value117 ++ [93]),([91] ++ encode value55 ++ [44] ++ encode value117 ++ [93])] ++ [93,93] = _
  simp only [encoded_value51,encoded_value117,encoded_value55]
  all_goals rfl
theorem nodes_value148 : nodes value148 = 5 := by
  change 1 + (nodes value51 + nodes value117 + (nodes value55 + nodes value117 + 0)) = 5
  simp only [nodes_value51,nodes_value117,nodes_value55]
  all_goals decide +kernel
theorem depth_value148 : depth value148 = 1 := by
  change max (max (1 + depth value51) (1 + depth value117)) (max (max (1 + depth value55) (1 + depth value117)) (0)) = 1
  simp only [depth_value51,depth_value117,depth_value55]
  all_goals decide +kernel
theorem canonical_value148 : canonical models value148 = true := by
  change ((canonical models value51 && canonical models value117 && (canonical models value55 && canonical models value117 && true)) && ordered [encode value51,encode value55]) = true
  simp only [canonical_value51,canonical_value117,canonical_value55,encoded_value51,encoded_value55]
  simp only [ordered,List.all_cons,List.all_nil,order_value51_value55,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value148 : rawvalue148.length = 75 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value51) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value117) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value55) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value117) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value149 : Value := .function (.cons value120 value148 .nil)
noncomputable def rawvalue149 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue120 ++ [44] ++ rawvalue148 ++ [93])] ++ [93,93]
theorem encoded_value149 : encode value149 = rawvalue149 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value120 ++ [44] ++ encode value148 ++ [93])] ++ [93,93] = _
  simp only [encoded_value120,encoded_value148]
  all_goals rfl
theorem nodes_value149 : nodes value149 = 7 := by
  change 1 + (nodes value120 + nodes value148 + 0) = 7
  simp only [nodes_value120,nodes_value148]
  all_goals decide +kernel
theorem depth_value149 : depth value149 = 2 := by
  change max (max (1 + depth value120) (1 + depth value148)) (0) = 2
  simp only [depth_value120,depth_value148]
  all_goals decide +kernel
theorem canonical_value149 : canonical models value149 = true := by
  change ((canonical models value120 && canonical models value148 && true) && ordered [encode value120]) = true
  simp only [canonical_value120,canonical_value148,encoded_value120]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value149 : rawvalue149.length = 102 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value120) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value148) (show ([93] : Bytes).length = 1 from by decide +kernel)))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value150 : Value := .text "ticketDomain"
noncomputable def rawvalue150 : Bytes := asciiBytes "[\"str\",\"ticketDomain\"]"
theorem encoded_value150 : encode value150 = rawvalue150 := by
  all_goals rfl
theorem nodes_value150 : nodes value150 = 1 := by rfl
theorem depth_value150 : depth value150 = 0 := by rfl
theorem canonical_value150 : canonical models value150 = true := by decide +kernel
theorem rawLength_value150 : rawvalue150.length = 22 := by
  decide +kernel
noncomputable def value151 : Value := .function (.cons value11 value120 .nil)
noncomputable def rawvalue151 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue11 ++ [44] ++ rawvalue120 ++ [93])] ++ [93,93]
theorem encoded_value151 : encode value151 = rawvalue151 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value11 ++ [44] ++ encode value120 ++ [93])] ++ [93,93] = _
  simp only [encoded_value11,encoded_value120]
  all_goals rfl
theorem nodes_value151 : nodes value151 = 3 := by
  change 1 + (nodes value11 + nodes value120 + 0) = 3
  simp only [nodes_value11,nodes_value120]
  all_goals decide +kernel
theorem depth_value151 : depth value151 = 1 := by
  change max (max (1 + depth value11) (1 + depth value120)) (0) = 1
  simp only [depth_value11,depth_value120]
  all_goals decide +kernel
theorem canonical_value151 : canonical models value151 = true := by
  change ((canonical models value11 && canonical models value120 && true) && ordered [encode value11]) = true
  simp only [canonical_value11,canonical_value120,encoded_value11]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value151 : rawvalue151.length = 41 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value11) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value120) (show ([93] : Bytes).length = 1 from by decide +kernel)))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value152 : Value := .text "ticketOrder"
noncomputable def rawvalue152 : Bytes := asciiBytes "[\"str\",\"ticketOrder\"]"
theorem encoded_value152 : encode value152 = rawvalue152 := by
  all_goals rfl
theorem nodes_value152 : nodes value152 = 1 := by rfl
theorem depth_value152 : depth value152 = 0 := by rfl
theorem canonical_value152 : canonical models value152 = true := by decide +kernel
theorem rawLength_value152 : rawvalue152.length = 21 := by
  decide +kernel
noncomputable def value153 : Value := .function (.cons value117 value11 .nil)
noncomputable def rawvalue153 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue117 ++ [44] ++ rawvalue11 ++ [93])] ++ [93,93]
theorem encoded_value153 : encode value153 = rawvalue153 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value117 ++ [44] ++ encode value11 ++ [93])] ++ [93,93] = _
  simp only [encoded_value117,encoded_value11]
  all_goals rfl
theorem nodes_value153 : nodes value153 = 3 := by
  change 1 + (nodes value117 + nodes value11 + 0) = 3
  simp only [nodes_value117,nodes_value11]
  all_goals decide +kernel
theorem depth_value153 : depth value153 = 1 := by
  change max (max (1 + depth value117) (1 + depth value11)) (0) = 1
  simp only [depth_value117,depth_value11]
  all_goals decide +kernel
theorem canonical_value153 : canonical models value153 = true := by
  change ((canonical models value117 && canonical models value11 && true) && ordered [encode value117]) = true
  simp only [canonical_value117,canonical_value11,encoded_value117]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value153 : rawvalue153.length = 38 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value117) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value11) (show ([93] : Bytes).length = 1 from by decide +kernel)))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value154 : Value := .text "wdD"
noncomputable def rawvalue154 : Bytes := asciiBytes "[\"str\",\"wdD\"]"
theorem encoded_value154 : encode value154 = rawvalue154 := by
  all_goals rfl
theorem nodes_value154 : nodes value154 = 1 := by rfl
theorem depth_value154 : depth value154 = 0 := by rfl
theorem canonical_value154 : canonical models value154 = true := by decide +kernel
theorem rawLength_value154 : rawvalue154.length = 13 := by
  decide +kernel
noncomputable def value155 : Value := .text "wdN"
noncomputable def rawvalue155 : Bytes := asciiBytes "[\"str\",\"wdN\"]"
theorem encoded_value155 : encode value155 = rawvalue155 := by
  all_goals rfl
theorem nodes_value155 : nodes value155 = 1 := by rfl
theorem depth_value155 : depth value155 = 0 := by rfl
theorem canonical_value155 : canonical models value155 = true := by decide +kernel
theorem rawLength_value155 : rawvalue155.length = 13 := by
  decide +kernel
noncomputable def value156 : Value := .text "weightD"
noncomputable def rawvalue156 : Bytes := asciiBytes "[\"str\",\"weightD\"]"
theorem encoded_value156 : encode value156 = rawvalue156 := by
  all_goals rfl
theorem nodes_value156 : nodes value156 = 1 := by rfl
theorem depth_value156 : depth value156 = 0 := by rfl
theorem canonical_value156 : canonical models value156 = true := by decide +kernel
theorem rawLength_value156 : rawvalue156.length = 17 := by
  decide +kernel
noncomputable def value157 : Value := .function (.cons value11 value117 .nil)
noncomputable def rawvalue157 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue11 ++ [44] ++ rawvalue117 ++ [93])] ++ [93,93]
theorem encoded_value157 : encode value157 = rawvalue157 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value11 ++ [44] ++ encode value117 ++ [93])] ++ [93,93] = _
  simp only [encoded_value11,encoded_value117]
  all_goals rfl
theorem nodes_value157 : nodes value157 = 3 := by
  change 1 + (nodes value11 + nodes value117 + 0) = 3
  simp only [nodes_value11,nodes_value117]
  all_goals decide +kernel
theorem depth_value157 : depth value157 = 1 := by
  change max (max (1 + depth value11) (1 + depth value117)) (0) = 1
  simp only [depth_value11,depth_value117]
  all_goals decide +kernel
theorem canonical_value157 : canonical models value157 = true := by
  change ((canonical models value11 && canonical models value117 && true) && ordered [encode value11]) = true
  simp only [canonical_value11,canonical_value117,encoded_value11]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value157 : rawvalue157.length = 38 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value11) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value117) (show ([93] : Bytes).length = 1 from by decide +kernel)))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value158 : Value := .text "weightN"
noncomputable def rawvalue158 : Bytes := asciiBytes "[\"str\",\"weightN\"]"
theorem encoded_value158 : encode value158 = rawvalue158 := by
  all_goals rfl
theorem nodes_value158 : nodes value158 = 1 := by rfl
theorem depth_value158 : depth value158 = 0 := by rfl
theorem canonical_value158 : canonical models value158 = true := by decide +kernel
theorem rawLength_value158 : rawvalue158.length = 17 := by
  decide +kernel
noncomputable def value159 : Value := .function (.cons value116 value117 (.cons value118 value117 (.cons value119 value121 (.cons value122 value123 (.cons value124 value125 (.cons value126 value127 (.cons value128 value117 (.cons value129 value117 (.cons value130 value133 (.cons value134 value127 (.cons value135 value117 (.cons value136 value138 (.cons value139 value121 (.cons value140 value121 (.cons value141 value143 (.cons value144 value146 (.cons value147 value149 (.cons value150 value151 (.cons value152 value153 (.cons value154 value117 (.cons value155 value64 (.cons value156 value157 (.cons value158 value157 .nil)))))))))))))))))))))))
noncomputable def rawvalue159 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue116 ++ [44] ++ rawvalue117 ++ [93]),([91] ++ rawvalue118 ++ [44] ++ rawvalue117 ++ [93]),([91] ++ rawvalue119 ++ [44] ++ rawvalue121 ++ [93]),([91] ++ rawvalue122 ++ [44] ++ rawvalue123 ++ [93]),([91] ++ rawvalue124 ++ [44] ++ rawvalue125 ++ [93]),([91] ++ rawvalue126 ++ [44] ++ rawvalue127 ++ [93]),([91] ++ rawvalue128 ++ [44] ++ rawvalue117 ++ [93]),([91] ++ rawvalue129 ++ [44] ++ rawvalue117 ++ [93]),([91] ++ rawvalue130 ++ [44] ++ rawvalue133 ++ [93]),([91] ++ rawvalue134 ++ [44] ++ rawvalue127 ++ [93]),([91] ++ rawvalue135 ++ [44] ++ rawvalue117 ++ [93]),([91] ++ rawvalue136 ++ [44] ++ rawvalue138 ++ [93]),([91] ++ rawvalue139 ++ [44] ++ rawvalue121 ++ [93]),([91] ++ rawvalue140 ++ [44] ++ rawvalue121 ++ [93]),([91] ++ rawvalue141 ++ [44] ++ rawvalue143 ++ [93]),([91] ++ rawvalue144 ++ [44] ++ rawvalue146 ++ [93]),([91] ++ rawvalue147 ++ [44] ++ rawvalue149 ++ [93]),([91] ++ rawvalue150 ++ [44] ++ rawvalue151 ++ [93]),([91] ++ rawvalue152 ++ [44] ++ rawvalue153 ++ [93]),([91] ++ rawvalue154 ++ [44] ++ rawvalue117 ++ [93]),([91] ++ rawvalue155 ++ [44] ++ rawvalue64 ++ [93]),([91] ++ rawvalue156 ++ [44] ++ rawvalue157 ++ [93]),([91] ++ rawvalue158 ++ [44] ++ rawvalue157 ++ [93])] ++ [93,93]
theorem encoded_value159 : encode value159 = rawvalue159 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value116 ++ [44] ++ encode value117 ++ [93]),([91] ++ encode value118 ++ [44] ++ encode value117 ++ [93]),([91] ++ encode value119 ++ [44] ++ encode value121 ++ [93]),([91] ++ encode value122 ++ [44] ++ encode value123 ++ [93]),([91] ++ encode value124 ++ [44] ++ encode value125 ++ [93]),([91] ++ encode value126 ++ [44] ++ encode value127 ++ [93]),([91] ++ encode value128 ++ [44] ++ encode value117 ++ [93]),([91] ++ encode value129 ++ [44] ++ encode value117 ++ [93]),([91] ++ encode value130 ++ [44] ++ encode value133 ++ [93]),([91] ++ encode value134 ++ [44] ++ encode value127 ++ [93]),([91] ++ encode value135 ++ [44] ++ encode value117 ++ [93]),([91] ++ encode value136 ++ [44] ++ encode value138 ++ [93]),([91] ++ encode value139 ++ [44] ++ encode value121 ++ [93]),([91] ++ encode value140 ++ [44] ++ encode value121 ++ [93]),([91] ++ encode value141 ++ [44] ++ encode value143 ++ [93]),([91] ++ encode value144 ++ [44] ++ encode value146 ++ [93]),([91] ++ encode value147 ++ [44] ++ encode value149 ++ [93]),([91] ++ encode value150 ++ [44] ++ encode value151 ++ [93]),([91] ++ encode value152 ++ [44] ++ encode value153 ++ [93]),([91] ++ encode value154 ++ [44] ++ encode value117 ++ [93]),([91] ++ encode value155 ++ [44] ++ encode value64 ++ [93]),([91] ++ encode value156 ++ [44] ++ encode value157 ++ [93]),([91] ++ encode value158 ++ [44] ++ encode value157 ++ [93])] ++ [93,93] = _
  simp only [encoded_value116,encoded_value117,encoded_value118,encoded_value119,encoded_value121,encoded_value122,encoded_value123,encoded_value124,encoded_value125,encoded_value126,encoded_value127,encoded_value128,encoded_value129,encoded_value130,encoded_value133,encoded_value134,encoded_value135,encoded_value136,encoded_value138,encoded_value139,encoded_value140,encoded_value141,encoded_value143,encoded_value144,encoded_value146,encoded_value147,encoded_value149,encoded_value150,encoded_value151,encoded_value152,encoded_value153,encoded_value154,encoded_value155,encoded_value64,encoded_value156,encoded_value157,encoded_value158]
  all_goals rfl
theorem order_value116_value118 : byteLess rawvalue116 rawvalue118 = true := by
  simp only [rawvalue116,rawvalue118,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value119 : byteLess rawvalue116 rawvalue119 = true := by
  simp only [rawvalue116,rawvalue119,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value122 : byteLess rawvalue116 rawvalue122 = true := by
  simp only [rawvalue116,rawvalue122,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value124 : byteLess rawvalue116 rawvalue124 = true := by
  simp only [rawvalue116,rawvalue124,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value126 : byteLess rawvalue116 rawvalue126 = true := by
  simp only [rawvalue116,rawvalue126,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value128 : byteLess rawvalue116 rawvalue128 = true := by
  simp only [rawvalue116,rawvalue128,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value129 : byteLess rawvalue116 rawvalue129 = true := by
  simp only [rawvalue116,rawvalue129,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value130 : byteLess rawvalue116 rawvalue130 = true := by
  simp only [rawvalue116,rawvalue130,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value134 : byteLess rawvalue116 rawvalue134 = true := by
  simp only [rawvalue116,rawvalue134,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value135 : byteLess rawvalue116 rawvalue135 = true := by
  simp only [rawvalue116,rawvalue135,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value136 : byteLess rawvalue116 rawvalue136 = true := by
  simp only [rawvalue116,rawvalue136,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value139 : byteLess rawvalue116 rawvalue139 = true := by
  simp only [rawvalue116,rawvalue139,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value140 : byteLess rawvalue116 rawvalue140 = true := by
  simp only [rawvalue116,rawvalue140,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value141 : byteLess rawvalue116 rawvalue141 = true := by
  simp only [rawvalue116,rawvalue141,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value144 : byteLess rawvalue116 rawvalue144 = true := by
  simp only [rawvalue116,rawvalue144,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value147 : byteLess rawvalue116 rawvalue147 = true := by
  simp only [rawvalue116,rawvalue147,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value150 : byteLess rawvalue116 rawvalue150 = true := by
  simp only [rawvalue116,rawvalue150,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value152 : byteLess rawvalue116 rawvalue152 = true := by
  simp only [rawvalue116,rawvalue152,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value154 : byteLess rawvalue116 rawvalue154 = true := by
  simp only [rawvalue116,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value155 : byteLess rawvalue116 rawvalue155 = true := by
  simp only [rawvalue116,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value156 : byteLess rawvalue116 rawvalue156 = true := by
  simp only [rawvalue116,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value116_value158 : byteLess rawvalue116 rawvalue158 = true := by
  simp only [rawvalue116,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value119 : byteLess rawvalue118 rawvalue119 = true := by
  simp only [rawvalue118,rawvalue119,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value122 : byteLess rawvalue118 rawvalue122 = true := by
  simp only [rawvalue118,rawvalue122,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value124 : byteLess rawvalue118 rawvalue124 = true := by
  simp only [rawvalue118,rawvalue124,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value126 : byteLess rawvalue118 rawvalue126 = true := by
  simp only [rawvalue118,rawvalue126,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value128 : byteLess rawvalue118 rawvalue128 = true := by
  simp only [rawvalue118,rawvalue128,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value129 : byteLess rawvalue118 rawvalue129 = true := by
  simp only [rawvalue118,rawvalue129,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value130 : byteLess rawvalue118 rawvalue130 = true := by
  simp only [rawvalue118,rawvalue130,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value134 : byteLess rawvalue118 rawvalue134 = true := by
  simp only [rawvalue118,rawvalue134,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value135 : byteLess rawvalue118 rawvalue135 = true := by
  simp only [rawvalue118,rawvalue135,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value136 : byteLess rawvalue118 rawvalue136 = true := by
  simp only [rawvalue118,rawvalue136,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value139 : byteLess rawvalue118 rawvalue139 = true := by
  simp only [rawvalue118,rawvalue139,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value140 : byteLess rawvalue118 rawvalue140 = true := by
  simp only [rawvalue118,rawvalue140,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value141 : byteLess rawvalue118 rawvalue141 = true := by
  simp only [rawvalue118,rawvalue141,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value144 : byteLess rawvalue118 rawvalue144 = true := by
  simp only [rawvalue118,rawvalue144,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value147 : byteLess rawvalue118 rawvalue147 = true := by
  simp only [rawvalue118,rawvalue147,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value150 : byteLess rawvalue118 rawvalue150 = true := by
  simp only [rawvalue118,rawvalue150,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value152 : byteLess rawvalue118 rawvalue152 = true := by
  simp only [rawvalue118,rawvalue152,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value154 : byteLess rawvalue118 rawvalue154 = true := by
  simp only [rawvalue118,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value155 : byteLess rawvalue118 rawvalue155 = true := by
  simp only [rawvalue118,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value156 : byteLess rawvalue118 rawvalue156 = true := by
  simp only [rawvalue118,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value118_value158 : byteLess rawvalue118 rawvalue158 = true := by
  simp only [rawvalue118,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value122 : byteLess rawvalue119 rawvalue122 = true := by
  simp only [rawvalue119,rawvalue122,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value124 : byteLess rawvalue119 rawvalue124 = true := by
  simp only [rawvalue119,rawvalue124,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value126 : byteLess rawvalue119 rawvalue126 = true := by
  simp only [rawvalue119,rawvalue126,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value128 : byteLess rawvalue119 rawvalue128 = true := by
  simp only [rawvalue119,rawvalue128,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value129 : byteLess rawvalue119 rawvalue129 = true := by
  simp only [rawvalue119,rawvalue129,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value130 : byteLess rawvalue119 rawvalue130 = true := by
  simp only [rawvalue119,rawvalue130,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value134 : byteLess rawvalue119 rawvalue134 = true := by
  simp only [rawvalue119,rawvalue134,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value135 : byteLess rawvalue119 rawvalue135 = true := by
  simp only [rawvalue119,rawvalue135,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value136 : byteLess rawvalue119 rawvalue136 = true := by
  simp only [rawvalue119,rawvalue136,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value139 : byteLess rawvalue119 rawvalue139 = true := by
  simp only [rawvalue119,rawvalue139,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value140 : byteLess rawvalue119 rawvalue140 = true := by
  simp only [rawvalue119,rawvalue140,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value141 : byteLess rawvalue119 rawvalue141 = true := by
  simp only [rawvalue119,rawvalue141,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value144 : byteLess rawvalue119 rawvalue144 = true := by
  simp only [rawvalue119,rawvalue144,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value147 : byteLess rawvalue119 rawvalue147 = true := by
  simp only [rawvalue119,rawvalue147,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value150 : byteLess rawvalue119 rawvalue150 = true := by
  simp only [rawvalue119,rawvalue150,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value152 : byteLess rawvalue119 rawvalue152 = true := by
  simp only [rawvalue119,rawvalue152,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value154 : byteLess rawvalue119 rawvalue154 = true := by
  simp only [rawvalue119,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value155 : byteLess rawvalue119 rawvalue155 = true := by
  simp only [rawvalue119,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value156 : byteLess rawvalue119 rawvalue156 = true := by
  simp only [rawvalue119,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value119_value158 : byteLess rawvalue119 rawvalue158 = true := by
  simp only [rawvalue119,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value124 : byteLess rawvalue122 rawvalue124 = true := by
  simp only [rawvalue122,rawvalue124,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value126 : byteLess rawvalue122 rawvalue126 = true := by
  simp only [rawvalue122,rawvalue126,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value128 : byteLess rawvalue122 rawvalue128 = true := by
  simp only [rawvalue122,rawvalue128,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value129 : byteLess rawvalue122 rawvalue129 = true := by
  simp only [rawvalue122,rawvalue129,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value130 : byteLess rawvalue122 rawvalue130 = true := by
  simp only [rawvalue122,rawvalue130,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value134 : byteLess rawvalue122 rawvalue134 = true := by
  simp only [rawvalue122,rawvalue134,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value135 : byteLess rawvalue122 rawvalue135 = true := by
  simp only [rawvalue122,rawvalue135,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value136 : byteLess rawvalue122 rawvalue136 = true := by
  simp only [rawvalue122,rawvalue136,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value139 : byteLess rawvalue122 rawvalue139 = true := by
  simp only [rawvalue122,rawvalue139,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value140 : byteLess rawvalue122 rawvalue140 = true := by
  simp only [rawvalue122,rawvalue140,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value141 : byteLess rawvalue122 rawvalue141 = true := by
  simp only [rawvalue122,rawvalue141,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value144 : byteLess rawvalue122 rawvalue144 = true := by
  simp only [rawvalue122,rawvalue144,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value147 : byteLess rawvalue122 rawvalue147 = true := by
  simp only [rawvalue122,rawvalue147,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value150 : byteLess rawvalue122 rawvalue150 = true := by
  simp only [rawvalue122,rawvalue150,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value152 : byteLess rawvalue122 rawvalue152 = true := by
  simp only [rawvalue122,rawvalue152,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value154 : byteLess rawvalue122 rawvalue154 = true := by
  simp only [rawvalue122,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value155 : byteLess rawvalue122 rawvalue155 = true := by
  simp only [rawvalue122,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value156 : byteLess rawvalue122 rawvalue156 = true := by
  simp only [rawvalue122,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value122_value158 : byteLess rawvalue122 rawvalue158 = true := by
  simp only [rawvalue122,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value124_value126 : byteLess rawvalue124 rawvalue126 = true := by
  simp only [rawvalue124,rawvalue126,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value124_value128 : byteLess rawvalue124 rawvalue128 = true := by
  simp only [rawvalue124,rawvalue128,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value124_value129 : byteLess rawvalue124 rawvalue129 = true := by
  simp only [rawvalue124,rawvalue129,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value124_value130 : byteLess rawvalue124 rawvalue130 = true := by
  simp only [rawvalue124,rawvalue130,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value124_value134 : byteLess rawvalue124 rawvalue134 = true := by
  simp only [rawvalue124,rawvalue134,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value124_value135 : byteLess rawvalue124 rawvalue135 = true := by
  simp only [rawvalue124,rawvalue135,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value124_value136 : byteLess rawvalue124 rawvalue136 = true := by
  simp only [rawvalue124,rawvalue136,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value124_value139 : byteLess rawvalue124 rawvalue139 = true := by
  simp only [rawvalue124,rawvalue139,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value124_value140 : byteLess rawvalue124 rawvalue140 = true := by
  simp only [rawvalue124,rawvalue140,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value124_value141 : byteLess rawvalue124 rawvalue141 = true := by
  simp only [rawvalue124,rawvalue141,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value124_value144 : byteLess rawvalue124 rawvalue144 = true := by
  simp only [rawvalue124,rawvalue144,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value124_value147 : byteLess rawvalue124 rawvalue147 = true := by
  simp only [rawvalue124,rawvalue147,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value124_value150 : byteLess rawvalue124 rawvalue150 = true := by
  simp only [rawvalue124,rawvalue150,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value124_value152 : byteLess rawvalue124 rawvalue152 = true := by
  simp only [rawvalue124,rawvalue152,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value124_value154 : byteLess rawvalue124 rawvalue154 = true := by
  simp only [rawvalue124,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value124_value155 : byteLess rawvalue124 rawvalue155 = true := by
  simp only [rawvalue124,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value124_value156 : byteLess rawvalue124 rawvalue156 = true := by
  simp only [rawvalue124,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value124_value158 : byteLess rawvalue124 rawvalue158 = true := by
  simp only [rawvalue124,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value126_value128 : byteLess rawvalue126 rawvalue128 = true := by
  simp only [rawvalue126,rawvalue128,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value126_value129 : byteLess rawvalue126 rawvalue129 = true := by
  simp only [rawvalue126,rawvalue129,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value126_value130 : byteLess rawvalue126 rawvalue130 = true := by
  simp only [rawvalue126,rawvalue130,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value126_value134 : byteLess rawvalue126 rawvalue134 = true := by
  simp only [rawvalue126,rawvalue134,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value126_value135 : byteLess rawvalue126 rawvalue135 = true := by
  simp only [rawvalue126,rawvalue135,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value126_value136 : byteLess rawvalue126 rawvalue136 = true := by
  simp only [rawvalue126,rawvalue136,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value126_value139 : byteLess rawvalue126 rawvalue139 = true := by
  simp only [rawvalue126,rawvalue139,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value126_value140 : byteLess rawvalue126 rawvalue140 = true := by
  simp only [rawvalue126,rawvalue140,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value126_value141 : byteLess rawvalue126 rawvalue141 = true := by
  simp only [rawvalue126,rawvalue141,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value126_value144 : byteLess rawvalue126 rawvalue144 = true := by
  simp only [rawvalue126,rawvalue144,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value126_value147 : byteLess rawvalue126 rawvalue147 = true := by
  simp only [rawvalue126,rawvalue147,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value126_value150 : byteLess rawvalue126 rawvalue150 = true := by
  simp only [rawvalue126,rawvalue150,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value126_value152 : byteLess rawvalue126 rawvalue152 = true := by
  simp only [rawvalue126,rawvalue152,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value126_value154 : byteLess rawvalue126 rawvalue154 = true := by
  simp only [rawvalue126,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value126_value155 : byteLess rawvalue126 rawvalue155 = true := by
  simp only [rawvalue126,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value126_value156 : byteLess rawvalue126 rawvalue156 = true := by
  simp only [rawvalue126,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value126_value158 : byteLess rawvalue126 rawvalue158 = true := by
  simp only [rawvalue126,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value128_value129 : byteLess rawvalue128 rawvalue129 = true := by
  simp only [rawvalue128,rawvalue129,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value128_value130 : byteLess rawvalue128 rawvalue130 = true := by
  simp only [rawvalue128,rawvalue130,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value128_value134 : byteLess rawvalue128 rawvalue134 = true := by
  simp only [rawvalue128,rawvalue134,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value128_value135 : byteLess rawvalue128 rawvalue135 = true := by
  simp only [rawvalue128,rawvalue135,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value128_value136 : byteLess rawvalue128 rawvalue136 = true := by
  simp only [rawvalue128,rawvalue136,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value128_value139 : byteLess rawvalue128 rawvalue139 = true := by
  simp only [rawvalue128,rawvalue139,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value128_value140 : byteLess rawvalue128 rawvalue140 = true := by
  simp only [rawvalue128,rawvalue140,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value128_value141 : byteLess rawvalue128 rawvalue141 = true := by
  simp only [rawvalue128,rawvalue141,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value128_value144 : byteLess rawvalue128 rawvalue144 = true := by
  simp only [rawvalue128,rawvalue144,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value128_value147 : byteLess rawvalue128 rawvalue147 = true := by
  simp only [rawvalue128,rawvalue147,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value128_value150 : byteLess rawvalue128 rawvalue150 = true := by
  simp only [rawvalue128,rawvalue150,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value128_value152 : byteLess rawvalue128 rawvalue152 = true := by
  simp only [rawvalue128,rawvalue152,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value128_value154 : byteLess rawvalue128 rawvalue154 = true := by
  simp only [rawvalue128,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value128_value155 : byteLess rawvalue128 rawvalue155 = true := by
  simp only [rawvalue128,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value128_value156 : byteLess rawvalue128 rawvalue156 = true := by
  simp only [rawvalue128,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value128_value158 : byteLess rawvalue128 rawvalue158 = true := by
  simp only [rawvalue128,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value129_value130 : byteLess rawvalue129 rawvalue130 = true := by
  simp only [rawvalue129,rawvalue130,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value129_value134 : byteLess rawvalue129 rawvalue134 = true := by
  simp only [rawvalue129,rawvalue134,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value129_value135 : byteLess rawvalue129 rawvalue135 = true := by
  simp only [rawvalue129,rawvalue135,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value129_value136 : byteLess rawvalue129 rawvalue136 = true := by
  simp only [rawvalue129,rawvalue136,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value129_value139 : byteLess rawvalue129 rawvalue139 = true := by
  simp only [rawvalue129,rawvalue139,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value129_value140 : byteLess rawvalue129 rawvalue140 = true := by
  simp only [rawvalue129,rawvalue140,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value129_value141 : byteLess rawvalue129 rawvalue141 = true := by
  simp only [rawvalue129,rawvalue141,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value129_value144 : byteLess rawvalue129 rawvalue144 = true := by
  simp only [rawvalue129,rawvalue144,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value129_value147 : byteLess rawvalue129 rawvalue147 = true := by
  simp only [rawvalue129,rawvalue147,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value129_value150 : byteLess rawvalue129 rawvalue150 = true := by
  simp only [rawvalue129,rawvalue150,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value129_value152 : byteLess rawvalue129 rawvalue152 = true := by
  simp only [rawvalue129,rawvalue152,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value129_value154 : byteLess rawvalue129 rawvalue154 = true := by
  simp only [rawvalue129,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value129_value155 : byteLess rawvalue129 rawvalue155 = true := by
  simp only [rawvalue129,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value129_value156 : byteLess rawvalue129 rawvalue156 = true := by
  simp only [rawvalue129,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value129_value158 : byteLess rawvalue129 rawvalue158 = true := by
  simp only [rawvalue129,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value130_value134 : byteLess rawvalue130 rawvalue134 = true := by
  simp only [rawvalue130,rawvalue134,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value130_value135 : byteLess rawvalue130 rawvalue135 = true := by
  simp only [rawvalue130,rawvalue135,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value130_value136 : byteLess rawvalue130 rawvalue136 = true := by
  simp only [rawvalue130,rawvalue136,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value130_value139 : byteLess rawvalue130 rawvalue139 = true := by
  simp only [rawvalue130,rawvalue139,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value130_value140 : byteLess rawvalue130 rawvalue140 = true := by
  simp only [rawvalue130,rawvalue140,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value130_value141 : byteLess rawvalue130 rawvalue141 = true := by
  simp only [rawvalue130,rawvalue141,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value130_value144 : byteLess rawvalue130 rawvalue144 = true := by
  simp only [rawvalue130,rawvalue144,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value130_value147 : byteLess rawvalue130 rawvalue147 = true := by
  simp only [rawvalue130,rawvalue147,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value130_value150 : byteLess rawvalue130 rawvalue150 = true := by
  simp only [rawvalue130,rawvalue150,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value130_value152 : byteLess rawvalue130 rawvalue152 = true := by
  simp only [rawvalue130,rawvalue152,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value130_value154 : byteLess rawvalue130 rawvalue154 = true := by
  simp only [rawvalue130,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value130_value155 : byteLess rawvalue130 rawvalue155 = true := by
  simp only [rawvalue130,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value130_value156 : byteLess rawvalue130 rawvalue156 = true := by
  simp only [rawvalue130,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value130_value158 : byteLess rawvalue130 rawvalue158 = true := by
  simp only [rawvalue130,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value134_value135 : byteLess rawvalue134 rawvalue135 = true := by
  simp only [rawvalue134,rawvalue135,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value134_value136 : byteLess rawvalue134 rawvalue136 = true := by
  simp only [rawvalue134,rawvalue136,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value134_value139 : byteLess rawvalue134 rawvalue139 = true := by
  simp only [rawvalue134,rawvalue139,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value134_value140 : byteLess rawvalue134 rawvalue140 = true := by
  simp only [rawvalue134,rawvalue140,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value134_value141 : byteLess rawvalue134 rawvalue141 = true := by
  simp only [rawvalue134,rawvalue141,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value134_value144 : byteLess rawvalue134 rawvalue144 = true := by
  simp only [rawvalue134,rawvalue144,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value134_value147 : byteLess rawvalue134 rawvalue147 = true := by
  simp only [rawvalue134,rawvalue147,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value134_value150 : byteLess rawvalue134 rawvalue150 = true := by
  simp only [rawvalue134,rawvalue150,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value134_value152 : byteLess rawvalue134 rawvalue152 = true := by
  simp only [rawvalue134,rawvalue152,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value134_value154 : byteLess rawvalue134 rawvalue154 = true := by
  simp only [rawvalue134,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value134_value155 : byteLess rawvalue134 rawvalue155 = true := by
  simp only [rawvalue134,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value134_value156 : byteLess rawvalue134 rawvalue156 = true := by
  simp only [rawvalue134,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value134_value158 : byteLess rawvalue134 rawvalue158 = true := by
  simp only [rawvalue134,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value135_value136 : byteLess rawvalue135 rawvalue136 = true := by
  simp only [rawvalue135,rawvalue136,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value135_value139 : byteLess rawvalue135 rawvalue139 = true := by
  simp only [rawvalue135,rawvalue139,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value135_value140 : byteLess rawvalue135 rawvalue140 = true := by
  simp only [rawvalue135,rawvalue140,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value135_value141 : byteLess rawvalue135 rawvalue141 = true := by
  simp only [rawvalue135,rawvalue141,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value135_value144 : byteLess rawvalue135 rawvalue144 = true := by
  simp only [rawvalue135,rawvalue144,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value135_value147 : byteLess rawvalue135 rawvalue147 = true := by
  simp only [rawvalue135,rawvalue147,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value135_value150 : byteLess rawvalue135 rawvalue150 = true := by
  simp only [rawvalue135,rawvalue150,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value135_value152 : byteLess rawvalue135 rawvalue152 = true := by
  simp only [rawvalue135,rawvalue152,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value135_value154 : byteLess rawvalue135 rawvalue154 = true := by
  simp only [rawvalue135,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value135_value155 : byteLess rawvalue135 rawvalue155 = true := by
  simp only [rawvalue135,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value135_value156 : byteLess rawvalue135 rawvalue156 = true := by
  simp only [rawvalue135,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value135_value158 : byteLess rawvalue135 rawvalue158 = true := by
  simp only [rawvalue135,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value136_value139 : byteLess rawvalue136 rawvalue139 = true := by
  simp only [rawvalue136,rawvalue139,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value136_value140 : byteLess rawvalue136 rawvalue140 = true := by
  simp only [rawvalue136,rawvalue140,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value136_value141 : byteLess rawvalue136 rawvalue141 = true := by
  simp only [rawvalue136,rawvalue141,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value136_value144 : byteLess rawvalue136 rawvalue144 = true := by
  simp only [rawvalue136,rawvalue144,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value136_value147 : byteLess rawvalue136 rawvalue147 = true := by
  simp only [rawvalue136,rawvalue147,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value136_value150 : byteLess rawvalue136 rawvalue150 = true := by
  simp only [rawvalue136,rawvalue150,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value136_value152 : byteLess rawvalue136 rawvalue152 = true := by
  simp only [rawvalue136,rawvalue152,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value136_value154 : byteLess rawvalue136 rawvalue154 = true := by
  simp only [rawvalue136,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value136_value155 : byteLess rawvalue136 rawvalue155 = true := by
  simp only [rawvalue136,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value136_value156 : byteLess rawvalue136 rawvalue156 = true := by
  simp only [rawvalue136,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value136_value158 : byteLess rawvalue136 rawvalue158 = true := by
  simp only [rawvalue136,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value139_value140 : byteLess rawvalue139 rawvalue140 = true := by
  simp only [rawvalue139,rawvalue140,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value139_value141 : byteLess rawvalue139 rawvalue141 = true := by
  simp only [rawvalue139,rawvalue141,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value139_value144 : byteLess rawvalue139 rawvalue144 = true := by
  simp only [rawvalue139,rawvalue144,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value139_value147 : byteLess rawvalue139 rawvalue147 = true := by
  simp only [rawvalue139,rawvalue147,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value139_value150 : byteLess rawvalue139 rawvalue150 = true := by
  simp only [rawvalue139,rawvalue150,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value139_value152 : byteLess rawvalue139 rawvalue152 = true := by
  simp only [rawvalue139,rawvalue152,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value139_value154 : byteLess rawvalue139 rawvalue154 = true := by
  simp only [rawvalue139,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value139_value155 : byteLess rawvalue139 rawvalue155 = true := by
  simp only [rawvalue139,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value139_value156 : byteLess rawvalue139 rawvalue156 = true := by
  simp only [rawvalue139,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value139_value158 : byteLess rawvalue139 rawvalue158 = true := by
  simp only [rawvalue139,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value140_value141 : byteLess rawvalue140 rawvalue141 = true := by
  simp only [rawvalue140,rawvalue141,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value140_value144 : byteLess rawvalue140 rawvalue144 = true := by
  simp only [rawvalue140,rawvalue144,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value140_value147 : byteLess rawvalue140 rawvalue147 = true := by
  simp only [rawvalue140,rawvalue147,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value140_value150 : byteLess rawvalue140 rawvalue150 = true := by
  simp only [rawvalue140,rawvalue150,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value140_value152 : byteLess rawvalue140 rawvalue152 = true := by
  simp only [rawvalue140,rawvalue152,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value140_value154 : byteLess rawvalue140 rawvalue154 = true := by
  simp only [rawvalue140,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value140_value155 : byteLess rawvalue140 rawvalue155 = true := by
  simp only [rawvalue140,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value140_value156 : byteLess rawvalue140 rawvalue156 = true := by
  simp only [rawvalue140,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value140_value158 : byteLess rawvalue140 rawvalue158 = true := by
  simp only [rawvalue140,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value141_value144 : byteLess rawvalue141 rawvalue144 = true := by
  simp only [rawvalue141,rawvalue144,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value141_value147 : byteLess rawvalue141 rawvalue147 = true := by
  simp only [rawvalue141,rawvalue147,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value141_value150 : byteLess rawvalue141 rawvalue150 = true := by
  simp only [rawvalue141,rawvalue150,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value141_value152 : byteLess rawvalue141 rawvalue152 = true := by
  simp only [rawvalue141,rawvalue152,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value141_value154 : byteLess rawvalue141 rawvalue154 = true := by
  simp only [rawvalue141,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value141_value155 : byteLess rawvalue141 rawvalue155 = true := by
  simp only [rawvalue141,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value141_value156 : byteLess rawvalue141 rawvalue156 = true := by
  simp only [rawvalue141,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value141_value158 : byteLess rawvalue141 rawvalue158 = true := by
  simp only [rawvalue141,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value144_value147 : byteLess rawvalue144 rawvalue147 = true := by
  simp only [rawvalue144,rawvalue147,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value144_value150 : byteLess rawvalue144 rawvalue150 = true := by
  simp only [rawvalue144,rawvalue150,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value144_value152 : byteLess rawvalue144 rawvalue152 = true := by
  simp only [rawvalue144,rawvalue152,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value144_value154 : byteLess rawvalue144 rawvalue154 = true := by
  simp only [rawvalue144,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value144_value155 : byteLess rawvalue144 rawvalue155 = true := by
  simp only [rawvalue144,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value144_value156 : byteLess rawvalue144 rawvalue156 = true := by
  simp only [rawvalue144,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value144_value158 : byteLess rawvalue144 rawvalue158 = true := by
  simp only [rawvalue144,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value147_value150 : byteLess rawvalue147 rawvalue150 = true := by
  simp only [rawvalue147,rawvalue150,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value147_value152 : byteLess rawvalue147 rawvalue152 = true := by
  simp only [rawvalue147,rawvalue152,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value147_value154 : byteLess rawvalue147 rawvalue154 = true := by
  simp only [rawvalue147,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value147_value155 : byteLess rawvalue147 rawvalue155 = true := by
  simp only [rawvalue147,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value147_value156 : byteLess rawvalue147 rawvalue156 = true := by
  simp only [rawvalue147,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value147_value158 : byteLess rawvalue147 rawvalue158 = true := by
  simp only [rawvalue147,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value150_value152 : byteLess rawvalue150 rawvalue152 = true := by
  simp only [rawvalue150,rawvalue152,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value150_value154 : byteLess rawvalue150 rawvalue154 = true := by
  simp only [rawvalue150,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value150_value155 : byteLess rawvalue150 rawvalue155 = true := by
  simp only [rawvalue150,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value150_value156 : byteLess rawvalue150 rawvalue156 = true := by
  simp only [rawvalue150,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value150_value158 : byteLess rawvalue150 rawvalue158 = true := by
  simp only [rawvalue150,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value152_value154 : byteLess rawvalue152 rawvalue154 = true := by
  simp only [rawvalue152,rawvalue154,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value152_value155 : byteLess rawvalue152 rawvalue155 = true := by
  simp only [rawvalue152,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value152_value156 : byteLess rawvalue152 rawvalue156 = true := by
  simp only [rawvalue152,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value152_value158 : byteLess rawvalue152 rawvalue158 = true := by
  simp only [rawvalue152,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value154_value155 : byteLess rawvalue154 rawvalue155 = true := by
  simp only [rawvalue154,rawvalue155,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value154_value156 : byteLess rawvalue154 rawvalue156 = true := by
  simp only [rawvalue154,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value154_value158 : byteLess rawvalue154 rawvalue158 = true := by
  simp only [rawvalue154,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value155_value156 : byteLess rawvalue155 rawvalue156 = true := by
  simp only [rawvalue155,rawvalue156,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value155_value158 : byteLess rawvalue155 rawvalue158 = true := by
  simp only [rawvalue155,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value156_value158 : byteLess rawvalue156 rawvalue158 = true := by
  simp only [rawvalue156,rawvalue158,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value159 : nodes value159 = 89 := by
  change 1 + (nodes value116 + nodes value117 + (nodes value118 + nodes value117 + (nodes value119 + nodes value121 + (nodes value122 + nodes value123 + (nodes value124 + nodes value125 + (nodes value126 + nodes value127 + (nodes value128 + nodes value117 + (nodes value129 + nodes value117 + (nodes value130 + nodes value133 + (nodes value134 + nodes value127 + (nodes value135 + nodes value117 + (nodes value136 + nodes value138 + (nodes value139 + nodes value121 + (nodes value140 + nodes value121 + (nodes value141 + nodes value143 + (nodes value144 + nodes value146 + (nodes value147 + nodes value149 + (nodes value150 + nodes value151 + (nodes value152 + nodes value153 + (nodes value154 + nodes value117 + (nodes value155 + nodes value64 + (nodes value156 + nodes value157 + (nodes value158 + nodes value157 + 0))))))))))))))))))))))) = 89
  simp only [nodes_value116,nodes_value117,nodes_value118,nodes_value119,nodes_value121,nodes_value122,nodes_value123,nodes_value124,nodes_value125,nodes_value126,nodes_value127,nodes_value128,nodes_value129,nodes_value130,nodes_value133,nodes_value134,nodes_value135,nodes_value136,nodes_value138,nodes_value139,nodes_value140,nodes_value141,nodes_value143,nodes_value144,nodes_value146,nodes_value147,nodes_value149,nodes_value150,nodes_value151,nodes_value152,nodes_value153,nodes_value154,nodes_value155,nodes_value64,nodes_value156,nodes_value157,nodes_value158]
  all_goals decide +kernel
theorem depth_value159 : depth value159 = 3 := by
  change max (max (1 + depth value116) (1 + depth value117)) (max (max (1 + depth value118) (1 + depth value117)) (max (max (1 + depth value119) (1 + depth value121)) (max (max (1 + depth value122) (1 + depth value123)) (max (max (1 + depth value124) (1 + depth value125)) (max (max (1 + depth value126) (1 + depth value127)) (max (max (1 + depth value128) (1 + depth value117)) (max (max (1 + depth value129) (1 + depth value117)) (max (max (1 + depth value130) (1 + depth value133)) (max (max (1 + depth value134) (1 + depth value127)) (max (max (1 + depth value135) (1 + depth value117)) (max (max (1 + depth value136) (1 + depth value138)) (max (max (1 + depth value139) (1 + depth value121)) (max (max (1 + depth value140) (1 + depth value121)) (max (max (1 + depth value141) (1 + depth value143)) (max (max (1 + depth value144) (1 + depth value146)) (max (max (1 + depth value147) (1 + depth value149)) (max (max (1 + depth value150) (1 + depth value151)) (max (max (1 + depth value152) (1 + depth value153)) (max (max (1 + depth value154) (1 + depth value117)) (max (max (1 + depth value155) (1 + depth value64)) (max (max (1 + depth value156) (1 + depth value157)) (max (max (1 + depth value158) (1 + depth value157)) (0))))))))))))))))))))))) = 3
  simp only [depth_value116,depth_value117,depth_value118,depth_value119,depth_value121,depth_value122,depth_value123,depth_value124,depth_value125,depth_value126,depth_value127,depth_value128,depth_value129,depth_value130,depth_value133,depth_value134,depth_value135,depth_value136,depth_value138,depth_value139,depth_value140,depth_value141,depth_value143,depth_value144,depth_value146,depth_value147,depth_value149,depth_value150,depth_value151,depth_value152,depth_value153,depth_value154,depth_value155,depth_value64,depth_value156,depth_value157,depth_value158]
  all_goals decide +kernel
theorem canonical_value159 : canonical models value159 = true := by
  change ((canonical models value116 && canonical models value117 && (canonical models value118 && canonical models value117 && (canonical models value119 && canonical models value121 && (canonical models value122 && canonical models value123 && (canonical models value124 && canonical models value125 && (canonical models value126 && canonical models value127 && (canonical models value128 && canonical models value117 && (canonical models value129 && canonical models value117 && (canonical models value130 && canonical models value133 && (canonical models value134 && canonical models value127 && (canonical models value135 && canonical models value117 && (canonical models value136 && canonical models value138 && (canonical models value139 && canonical models value121 && (canonical models value140 && canonical models value121 && (canonical models value141 && canonical models value143 && (canonical models value144 && canonical models value146 && (canonical models value147 && canonical models value149 && (canonical models value150 && canonical models value151 && (canonical models value152 && canonical models value153 && (canonical models value154 && canonical models value117 && (canonical models value155 && canonical models value64 && (canonical models value156 && canonical models value157 && (canonical models value158 && canonical models value157 && true))))))))))))))))))))))) && ordered [encode value116,encode value118,encode value119,encode value122,encode value124,encode value126,encode value128,encode value129,encode value130,encode value134,encode value135,encode value136,encode value139,encode value140,encode value141,encode value144,encode value147,encode value150,encode value152,encode value154,encode value155,encode value156,encode value158]) = true
  simp only [canonical_value116,canonical_value117,canonical_value118,canonical_value119,canonical_value121,canonical_value122,canonical_value123,canonical_value124,canonical_value125,canonical_value126,canonical_value127,canonical_value128,canonical_value129,canonical_value130,canonical_value133,canonical_value134,canonical_value135,canonical_value136,canonical_value138,canonical_value139,canonical_value140,canonical_value141,canonical_value143,canonical_value144,canonical_value146,canonical_value147,canonical_value149,canonical_value150,canonical_value151,canonical_value152,canonical_value153,canonical_value154,canonical_value155,canonical_value64,canonical_value156,canonical_value157,canonical_value158,encoded_value116,encoded_value118,encoded_value119,encoded_value122,encoded_value124,encoded_value126,encoded_value128,encoded_value129,encoded_value130,encoded_value134,encoded_value135,encoded_value136,encoded_value139,encoded_value140,encoded_value141,encoded_value144,encoded_value147,encoded_value150,encoded_value152,encoded_value154,encoded_value155,encoded_value156,encoded_value158]
  simp only [ordered,List.all_cons,List.all_nil,order_value116_value118,order_value116_value119,order_value116_value122,order_value116_value124,order_value116_value126,order_value116_value128,order_value116_value129,order_value116_value130,order_value116_value134,order_value116_value135,order_value116_value136,order_value116_value139,order_value116_value140,order_value116_value141,order_value116_value144,order_value116_value147,order_value116_value150,order_value116_value152,order_value116_value154,order_value116_value155,order_value116_value156,order_value116_value158,order_value118_value119,order_value118_value122,order_value118_value124,order_value118_value126,order_value118_value128,order_value118_value129,order_value118_value130,order_value118_value134,order_value118_value135,order_value118_value136,order_value118_value139,order_value118_value140,order_value118_value141,order_value118_value144,order_value118_value147,order_value118_value150,order_value118_value152,order_value118_value154,order_value118_value155,order_value118_value156,order_value118_value158,order_value119_value122,order_value119_value124,order_value119_value126,order_value119_value128,order_value119_value129,order_value119_value130,order_value119_value134,order_value119_value135,order_value119_value136,order_value119_value139,order_value119_value140,order_value119_value141,order_value119_value144,order_value119_value147,order_value119_value150,order_value119_value152,order_value119_value154,order_value119_value155,order_value119_value156,order_value119_value158,order_value122_value124,order_value122_value126,order_value122_value128,order_value122_value129,order_value122_value130,order_value122_value134,order_value122_value135,order_value122_value136,order_value122_value139,order_value122_value140,order_value122_value141,order_value122_value144,order_value122_value147,order_value122_value150,order_value122_value152,order_value122_value154,order_value122_value155,order_value122_value156,order_value122_value158,order_value124_value126,order_value124_value128,order_value124_value129,order_value124_value130,order_value124_value134,order_value124_value135,order_value124_value136,order_value124_value139,order_value124_value140,order_value124_value141,order_value124_value144,order_value124_value147,order_value124_value150,order_value124_value152,order_value124_value154,order_value124_value155,order_value124_value156,order_value124_value158,order_value126_value128,order_value126_value129,order_value126_value130,order_value126_value134,order_value126_value135,order_value126_value136,order_value126_value139,order_value126_value140,order_value126_value141,order_value126_value144,order_value126_value147,order_value126_value150,order_value126_value152,order_value126_value154,order_value126_value155,order_value126_value156,order_value126_value158,order_value128_value129,order_value128_value130,order_value128_value134,order_value128_value135,order_value128_value136,order_value128_value139,order_value128_value140,order_value128_value141,order_value128_value144,order_value128_value147,order_value128_value150,order_value128_value152,order_value128_value154,order_value128_value155,order_value128_value156,order_value128_value158,order_value129_value130,order_value129_value134,order_value129_value135,order_value129_value136,order_value129_value139,order_value129_value140,order_value129_value141,order_value129_value144,order_value129_value147,order_value129_value150,order_value129_value152,order_value129_value154,order_value129_value155,order_value129_value156,order_value129_value158,order_value130_value134,order_value130_value135,order_value130_value136,order_value130_value139,order_value130_value140,order_value130_value141,order_value130_value144,order_value130_value147,order_value130_value150,order_value130_value152,order_value130_value154,order_value130_value155,order_value130_value156,order_value130_value158,order_value134_value135,order_value134_value136,order_value134_value139,order_value134_value140,order_value134_value141,order_value134_value144,order_value134_value147,order_value134_value150,order_value134_value152,order_value134_value154,order_value134_value155,order_value134_value156,order_value134_value158,order_value135_value136,order_value135_value139,order_value135_value140,order_value135_value141,order_value135_value144,order_value135_value147,order_value135_value150,order_value135_value152,order_value135_value154,order_value135_value155,order_value135_value156,order_value135_value158,order_value136_value139,order_value136_value140,order_value136_value141,order_value136_value144,order_value136_value147,order_value136_value150,order_value136_value152,order_value136_value154,order_value136_value155,order_value136_value156,order_value136_value158,order_value139_value140,order_value139_value141,order_value139_value144,order_value139_value147,order_value139_value150,order_value139_value152,order_value139_value154,order_value139_value155,order_value139_value156,order_value139_value158,order_value140_value141,order_value140_value144,order_value140_value147,order_value140_value150,order_value140_value152,order_value140_value154,order_value140_value155,order_value140_value156,order_value140_value158,order_value141_value144,order_value141_value147,order_value141_value150,order_value141_value152,order_value141_value154,order_value141_value155,order_value141_value156,order_value141_value158,order_value144_value147,order_value144_value150,order_value144_value152,order_value144_value154,order_value144_value155,order_value144_value156,order_value144_value158,order_value147_value150,order_value147_value152,order_value147_value154,order_value147_value155,order_value147_value156,order_value147_value158,order_value150_value152,order_value150_value154,order_value150_value155,order_value150_value156,order_value150_value158,order_value152_value154,order_value152_value155,order_value152_value156,order_value152_value158,order_value154_value155,order_value154_value156,order_value154_value158,order_value155_value156,order_value155_value158,order_value156_value158,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value159 : rawvalue159.length = 1338 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value116) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value117) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value118) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value117) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value119) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value121) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value122) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value123) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value124) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value125) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value126) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value127) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value128) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value117) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value129) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value117) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value130) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value133) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value134) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value127) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value135) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value117) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value136) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value138) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value139) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value121) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value140) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value121) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value141) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value143) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value144) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value146) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value147) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value149) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value150) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value151) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value152) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value153) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value154) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value117) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value155) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value64) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value156) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value157) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value158) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value157) (show ([93] : Bytes).length = 1 from by decide +kernel)))))))))))))))))))))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value160 : Value := .text "MODEL"
noncomputable def rawvalue160 : Bytes := asciiBytes "[\"str\",\"MODEL\"]"
theorem encoded_value160 : encode value160 = rawvalue160 := by
  all_goals rfl
theorem nodes_value160 : nodes value160 = 1 := by rfl
theorem depth_value160 : depth value160 = 0 := by rfl
theorem canonical_value160 : canonical models value160 = true := by decide +kernel
theorem rawLength_value160 : rawvalue160.length = 15 := by
  decide +kernel
noncomputable def value161 : Value := .text "schema"
noncomputable def rawvalue161 : Bytes := asciiBytes "[\"str\",\"schema\"]"
theorem encoded_value161 : encode value161 = rawvalue161 := by
  all_goals rfl
theorem nodes_value161 : nodes value161 = 1 := by rfl
theorem depth_value161 : depth value161 = 0 := by rfl
theorem canonical_value161 : canonical models value161 = true := by decide +kernel
theorem rawLength_value161 : rawvalue161.length = 16 := by
  decide +kernel
noncomputable def value162 : Value := .model "schema1"
noncomputable def rawvalue162 : Bytes := asciiBytes "[\"model\",\"schema1\"]"
theorem encoded_value162 : encode value162 = rawvalue162 := by
  all_goals rfl
theorem nodes_value162 : nodes value162 = 1 := by rfl
theorem depth_value162 : depth value162 = 0 := by rfl
theorem canonical_value162 : canonical models value162 = true := by decide +kernel
theorem rawLength_value162 : rawvalue162.length = 19 := by
  decide +kernel
noncomputable def value163 : Value := .text "values"
noncomputable def rawvalue163 : Bytes := asciiBytes "[\"str\",\"values\"]"
theorem encoded_value163 : encode value163 = rawvalue163 := by
  all_goals rfl
theorem nodes_value163 : nodes value163 = 1 := by rfl
theorem depth_value163 : depth value163 = 0 := by rfl
theorem canonical_value163 : canonical models value163 = true := by decide +kernel
theorem rawLength_value163 : rawvalue163.length = 16 := by
  decide +kernel
noncomputable def value164 : Value := .function (.cons value73 value160 (.cons value161 value162 (.cons value163 value133 .nil)))
noncomputable def rawvalue164 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue73 ++ [44] ++ rawvalue160 ++ [93]),([91] ++ rawvalue161 ++ [44] ++ rawvalue162 ++ [93]),([91] ++ rawvalue163 ++ [44] ++ rawvalue133 ++ [93])] ++ [93,93]
theorem encoded_value164 : encode value164 = rawvalue164 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value73 ++ [44] ++ encode value160 ++ [93]),([91] ++ encode value161 ++ [44] ++ encode value162 ++ [93]),([91] ++ encode value163 ++ [44] ++ encode value133 ++ [93])] ++ [93,93] = _
  simp only [encoded_value73,encoded_value160,encoded_value161,encoded_value162,encoded_value163,encoded_value133]
  all_goals rfl
theorem order_value73_value161 : byteLess rawvalue73 rawvalue161 = true := by
  simp only [rawvalue73,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value73_value163 : byteLess rawvalue73 rawvalue163 = true := by
  simp only [rawvalue73,rawvalue163,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value161_value163 : byteLess rawvalue161 rawvalue163 = true := by
  simp only [rawvalue161,rawvalue163,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value164 : nodes value164 = 11 := by
  change 1 + (nodes value73 + nodes value160 + (nodes value161 + nodes value162 + (nodes value163 + nodes value133 + 0))) = 11
  simp only [nodes_value73,nodes_value160,nodes_value161,nodes_value162,nodes_value163,nodes_value133]
  all_goals decide +kernel
theorem depth_value164 : depth value164 = 2 := by
  change max (max (1 + depth value73) (1 + depth value160)) (max (max (1 + depth value161) (1 + depth value162)) (max (max (1 + depth value163) (1 + depth value133)) (0))) = 2
  simp only [depth_value73,depth_value160,depth_value161,depth_value162,depth_value163,depth_value133]
  all_goals decide +kernel
theorem canonical_value164 : canonical models value164 = true := by
  change ((canonical models value73 && canonical models value160 && (canonical models value161 && canonical models value162 && (canonical models value163 && canonical models value133 && true))) && ordered [encode value73,encode value161,encode value163]) = true
  simp only [canonical_value73,canonical_value160,canonical_value161,canonical_value162,canonical_value163,canonical_value133,encoded_value73,encoded_value161,encoded_value163]
  simp only [ordered,List.all_cons,List.all_nil,order_value73_value161,order_value73_value163,order_value161_value163,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value164 : rawvalue164.length = 179 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value160) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value161) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value162) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value163) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value133) (show ([93] : Bytes).length = 1 from by decide +kernel)))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value165 : Value := .text "OPTIMIZER"
noncomputable def rawvalue165 : Bytes := asciiBytes "[\"str\",\"OPTIMIZER\"]"
theorem encoded_value165 : encode value165 = rawvalue165 := by
  all_goals rfl
theorem nodes_value165 : nodes value165 = 1 := by rfl
theorem depth_value165 : depth value165 = 0 := by rfl
theorem canonical_value165 : canonical models value165 = true := by decide +kernel
theorem rawLength_value165 : rawvalue165.length = 19 := by
  decide +kernel
noncomputable def value166 : Value := .function (.cons value73 value165 (.cons value161 value162 (.cons value163 value138 .nil)))
noncomputable def rawvalue166 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue73 ++ [44] ++ rawvalue165 ++ [93]),([91] ++ rawvalue161 ++ [44] ++ rawvalue162 ++ [93]),([91] ++ rawvalue163 ++ [44] ++ rawvalue138 ++ [93])] ++ [93,93]
theorem encoded_value166 : encode value166 = rawvalue166 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value73 ++ [44] ++ encode value165 ++ [93]),([91] ++ encode value161 ++ [44] ++ encode value162 ++ [93]),([91] ++ encode value163 ++ [44] ++ encode value138 ++ [93])] ++ [93,93] = _
  simp only [encoded_value73,encoded_value165,encoded_value161,encoded_value162,encoded_value163,encoded_value138]
  all_goals rfl
theorem nodes_value166 : nodes value166 = 11 := by
  change 1 + (nodes value73 + nodes value165 + (nodes value161 + nodes value162 + (nodes value163 + nodes value138 + 0))) = 11
  simp only [nodes_value73,nodes_value165,nodes_value161,nodes_value162,nodes_value163,nodes_value138]
  all_goals decide +kernel
theorem depth_value166 : depth value166 = 2 := by
  change max (max (1 + depth value73) (1 + depth value165)) (max (max (1 + depth value161) (1 + depth value162)) (max (max (1 + depth value163) (1 + depth value138)) (0))) = 2
  simp only [depth_value73,depth_value165,depth_value161,depth_value162,depth_value163,depth_value138]
  all_goals decide +kernel
theorem canonical_value166 : canonical models value166 = true := by
  change ((canonical models value73 && canonical models value165 && (canonical models value161 && canonical models value162 && (canonical models value163 && canonical models value138 && true))) && ordered [encode value73,encode value161,encode value163]) = true
  simp only [canonical_value73,canonical_value165,canonical_value161,canonical_value162,canonical_value163,canonical_value138,encoded_value73,encoded_value161,encoded_value163]
  simp only [ordered,List.all_cons,List.all_nil,order_value73_value161,order_value73_value163,order_value161_value163,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value166 : rawvalue166.length = 181 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value165) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value161) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value162) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value163) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value138) (show ([93] : Bytes).length = 1 from by decide +kernel)))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value167 : Value := .text "parent"
noncomputable def rawvalue167 : Bytes := asciiBytes "[\"str\",\"parent\"]"
theorem encoded_value167 : encode value167 = rawvalue167 := by
  all_goals rfl
theorem nodes_value167 : nodes value167 = 1 := by rfl
theorem depth_value167 : depth value167 = 0 := by rfl
theorem canonical_value167 : canonical models value167 = true := by decide +kernel
theorem rawLength_value167 : rawvalue167.length = 16 := by
  decide +kernel
noncomputable def value168 : Value := .text "profile"
noncomputable def rawvalue168 : Bytes := asciiBytes "[\"str\",\"profile\"]"
theorem encoded_value168 : encode value168 = rawvalue168 := by
  all_goals rfl
theorem nodes_value168 : nodes value168 = 1 := by rfl
theorem depth_value168 : depth value168 = 0 := by rfl
theorem canonical_value168 : canonical models value168 = true := by decide +kernel
theorem rawLength_value168 : rawvalue168.length = 17 := by
  decide +kernel
noncomputable def value169 : Value := .function (.cons value109 value35 (.cons value113 value114 (.cons value5 value34 (.cons value115 value159 (.cons value6 value25 (.cons value130 value164 (.cons value136 value166 (.cons value167 value69 (.cons value168 value111 (.cons value161 value162 .nil))))))))))
noncomputable def rawvalue169 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue109 ++ [44] ++ rawvalue35 ++ [93]),([91] ++ rawvalue113 ++ [44] ++ rawvalue114 ++ [93]),([91] ++ rawvalue5 ++ [44] ++ rawvalue34 ++ [93]),([91] ++ rawvalue115 ++ [44] ++ rawvalue159 ++ [93]),([91] ++ rawvalue6 ++ [44] ++ rawvalue25 ++ [93]),([91] ++ rawvalue130 ++ [44] ++ rawvalue164 ++ [93]),([91] ++ rawvalue136 ++ [44] ++ rawvalue166 ++ [93]),([91] ++ rawvalue167 ++ [44] ++ rawvalue69 ++ [93]),([91] ++ rawvalue168 ++ [44] ++ rawvalue111 ++ [93]),([91] ++ rawvalue161 ++ [44] ++ rawvalue162 ++ [93])] ++ [93,93]
theorem encoded_value169 : encode value169 = rawvalue169 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value109 ++ [44] ++ encode value35 ++ [93]),([91] ++ encode value113 ++ [44] ++ encode value114 ++ [93]),([91] ++ encode value5 ++ [44] ++ encode value34 ++ [93]),([91] ++ encode value115 ++ [44] ++ encode value159 ++ [93]),([91] ++ encode value6 ++ [44] ++ encode value25 ++ [93]),([91] ++ encode value130 ++ [44] ++ encode value164 ++ [93]),([91] ++ encode value136 ++ [44] ++ encode value166 ++ [93]),([91] ++ encode value167 ++ [44] ++ encode value69 ++ [93]),([91] ++ encode value168 ++ [44] ++ encode value111 ++ [93]),([91] ++ encode value161 ++ [44] ++ encode value162 ++ [93])] ++ [93,93] = _
  simp only [encoded_value109,encoded_value35,encoded_value113,encoded_value114,encoded_value5,encoded_value34,encoded_value115,encoded_value159,encoded_value6,encoded_value25,encoded_value130,encoded_value164,encoded_value136,encoded_value166,encoded_value167,encoded_value69,encoded_value168,encoded_value111,encoded_value161,encoded_value162]
  all_goals rfl
theorem order_value109_value113 : byteLess rawvalue109 rawvalue113 = true := by
  simp only [rawvalue109,rawvalue113,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value109_value5 : byteLess rawvalue109 rawvalue5 = true := by
  simp only [rawvalue109,rawvalue5,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value109_value115 : byteLess rawvalue109 rawvalue115 = true := by
  simp only [rawvalue109,rawvalue115,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value109_value6 : byteLess rawvalue109 rawvalue6 = true := by
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value109_value130 : byteLess rawvalue109 rawvalue130 = true := by
  simp only [rawvalue109,rawvalue130,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value109_value136 : byteLess rawvalue109 rawvalue136 = true := by
  simp only [rawvalue109,rawvalue136,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value109_value167 : byteLess rawvalue109 rawvalue167 = true := by
  simp only [rawvalue109,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value109_value168 : byteLess rawvalue109 rawvalue168 = true := by
  simp only [rawvalue109,rawvalue168,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value109_value161 : byteLess rawvalue109 rawvalue161 = true := by
  simp only [rawvalue109,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value113_value5 : byteLess rawvalue113 rawvalue5 = true := by
  simp only [rawvalue113,rawvalue5,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value113_value115 : byteLess rawvalue113 rawvalue115 = true := by
  simp only [rawvalue113,rawvalue115,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value113_value6 : byteLess rawvalue113 rawvalue6 = true := by
  simp only [rawvalue113,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value113_value130 : byteLess rawvalue113 rawvalue130 = true := by
  simp only [rawvalue113,rawvalue130,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value113_value136 : byteLess rawvalue113 rawvalue136 = true := by
  simp only [rawvalue113,rawvalue136,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value113_value167 : byteLess rawvalue113 rawvalue167 = true := by
  simp only [rawvalue113,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value113_value168 : byteLess rawvalue113 rawvalue168 = true := by
  simp only [rawvalue113,rawvalue168,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value113_value161 : byteLess rawvalue113 rawvalue161 = true := by
  simp only [rawvalue113,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value5_value115 : byteLess rawvalue5 rawvalue115 = true := by
  simp only [rawvalue5,rawvalue115,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value5_value130 : byteLess rawvalue5 rawvalue130 = true := by
  simp only [rawvalue5,rawvalue130,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value5_value136 : byteLess rawvalue5 rawvalue136 = true := by
  simp only [rawvalue5,rawvalue136,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value5_value167 : byteLess rawvalue5 rawvalue167 = true := by
  simp only [rawvalue5,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value5_value168 : byteLess rawvalue5 rawvalue168 = true := by
  simp only [rawvalue5,rawvalue168,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value5_value161 : byteLess rawvalue5 rawvalue161 = true := by
  simp only [rawvalue5,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value115_value6 : byteLess rawvalue115 rawvalue6 = true := by
  simp only [rawvalue115,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value115_value130 : byteLess rawvalue115 rawvalue130 = true := by
  simp only [rawvalue115,rawvalue130,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value115_value136 : byteLess rawvalue115 rawvalue136 = true := by
  simp only [rawvalue115,rawvalue136,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value115_value167 : byteLess rawvalue115 rawvalue167 = true := by
  simp only [rawvalue115,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value115_value168 : byteLess rawvalue115 rawvalue168 = true := by
  simp only [rawvalue115,rawvalue168,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value115_value161 : byteLess rawvalue115 rawvalue161 = true := by
  simp only [rawvalue115,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value6_value130 : byteLess rawvalue6 rawvalue130 = true := by
  simp only [rawvalue6,rawvalue130,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value6_value136 : byteLess rawvalue6 rawvalue136 = true := by
  simp only [rawvalue6,rawvalue136,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value6_value167 : byteLess rawvalue6 rawvalue167 = true := by
  simp only [rawvalue6,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value6_value168 : byteLess rawvalue6 rawvalue168 = true := by
  simp only [rawvalue6,rawvalue168,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value6_value161 : byteLess rawvalue6 rawvalue161 = true := by
  simp only [rawvalue6,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value130_value167 : byteLess rawvalue130 rawvalue167 = true := by
  simp only [rawvalue130,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value130_value168 : byteLess rawvalue130 rawvalue168 = true := by
  simp only [rawvalue130,rawvalue168,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value130_value161 : byteLess rawvalue130 rawvalue161 = true := by
  simp only [rawvalue130,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value136_value167 : byteLess rawvalue136 rawvalue167 = true := by
  simp only [rawvalue136,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value136_value168 : byteLess rawvalue136 rawvalue168 = true := by
  simp only [rawvalue136,rawvalue168,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value136_value161 : byteLess rawvalue136 rawvalue161 = true := by
  simp only [rawvalue136,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value167_value168 : byteLess rawvalue167 rawvalue168 = true := by
  simp only [rawvalue167,rawvalue168,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value167_value161 : byteLess rawvalue167 rawvalue161 = true := by
  simp only [rawvalue167,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value168_value161 : byteLess rawvalue168 rawvalue161 = true := by
  simp only [rawvalue168,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value169 : nodes value169 = 344 := by
  change 1 + (nodes value109 + nodes value35 + (nodes value113 + nodes value114 + (nodes value5 + nodes value34 + (nodes value115 + nodes value159 + (nodes value6 + nodes value25 + (nodes value130 + nodes value164 + (nodes value136 + nodes value166 + (nodes value167 + nodes value69 + (nodes value168 + nodes value111 + (nodes value161 + nodes value162 + 0)))))))))) = 344
  simp only [nodes_value109,nodes_value35,nodes_value113,nodes_value114,nodes_value5,nodes_value34,nodes_value115,nodes_value159,nodes_value6,nodes_value25,nodes_value130,nodes_value164,nodes_value136,nodes_value166,nodes_value167,nodes_value69,nodes_value168,nodes_value111,nodes_value161,nodes_value162]
  all_goals decide +kernel
theorem depth_value169 : depth value169 = 7 := by
  change max (max (1 + depth value109) (1 + depth value35)) (max (max (1 + depth value113) (1 + depth value114)) (max (max (1 + depth value5) (1 + depth value34)) (max (max (1 + depth value115) (1 + depth value159)) (max (max (1 + depth value6) (1 + depth value25)) (max (max (1 + depth value130) (1 + depth value164)) (max (max (1 + depth value136) (1 + depth value166)) (max (max (1 + depth value167) (1 + depth value69)) (max (max (1 + depth value168) (1 + depth value111)) (max (max (1 + depth value161) (1 + depth value162)) (0)))))))))) = 7
  simp only [depth_value109,depth_value35,depth_value113,depth_value114,depth_value5,depth_value34,depth_value115,depth_value159,depth_value6,depth_value25,depth_value130,depth_value164,depth_value136,depth_value166,depth_value167,depth_value69,depth_value168,depth_value111,depth_value161,depth_value162]
  all_goals decide +kernel
theorem canonical_value169 : canonical models value169 = true := by
  change ((canonical models value109 && canonical models value35 && (canonical models value113 && canonical models value114 && (canonical models value5 && canonical models value34 && (canonical models value115 && canonical models value159 && (canonical models value6 && canonical models value25 && (canonical models value130 && canonical models value164 && (canonical models value136 && canonical models value166 && (canonical models value167 && canonical models value69 && (canonical models value168 && canonical models value111 && (canonical models value161 && canonical models value162 && true)))))))))) && ordered [encode value109,encode value113,encode value5,encode value115,encode value6,encode value130,encode value136,encode value167,encode value168,encode value161]) = true
  simp only [canonical_value109,canonical_value35,canonical_value113,canonical_value114,canonical_value5,canonical_value34,canonical_value115,canonical_value159,canonical_value6,canonical_value25,canonical_value130,canonical_value164,canonical_value136,canonical_value166,canonical_value167,canonical_value69,canonical_value168,canonical_value111,canonical_value161,canonical_value162,encoded_value109,encoded_value113,encoded_value5,encoded_value115,encoded_value6,encoded_value130,encoded_value136,encoded_value167,encoded_value168,encoded_value161]
  simp only [ordered,List.all_cons,List.all_nil,order_value109_value113,order_value109_value5,order_value109_value115,order_value109_value6,order_value109_value130,order_value109_value136,order_value109_value167,order_value109_value168,order_value109_value161,order_value113_value5,order_value113_value115,order_value113_value6,order_value113_value130,order_value113_value136,order_value113_value167,order_value113_value168,order_value113_value161,order_value5_value115,order_value5_value6,order_value5_value130,order_value5_value136,order_value5_value167,order_value5_value168,order_value5_value161,order_value115_value6,order_value115_value130,order_value115_value136,order_value115_value167,order_value115_value168,order_value115_value161,order_value6_value130,order_value6_value136,order_value6_value167,order_value6_value168,order_value6_value161,order_value130_value136,order_value130_value167,order_value130_value168,order_value130_value161,order_value136_value167,order_value136_value168,order_value136_value161,order_value167_value168,order_value167_value161,order_value168_value161,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value169 : rawvalue169.length = 5701 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value109) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value35) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value113) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value114) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value5) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value34) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value115) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value159) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value6) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value25) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value130) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value164) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value136) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value166) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value167) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value69) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value168) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value111) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value161) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value162) (show ([93] : Bytes).length = 1 from by decide +kernel))))))))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value170 : Value := .text "checked"
noncomputable def rawvalue170 : Bytes := asciiBytes "[\"str\",\"checked\"]"
theorem encoded_value170 : encode value170 = rawvalue170 := by
  all_goals rfl
theorem nodes_value170 : nodes value170 = 1 := by rfl
theorem depth_value170 : depth value170 = 0 := by rfl
theorem canonical_value170 : canonical models value170 = true := by decide +kernel
theorem rawLength_value170 : rawvalue170.length = 17 := by
  decide +kernel
noncomputable def value171 : Value := .boolean true
noncomputable def rawvalue171 : Bytes := asciiBytes "[\"bool\",true]"
theorem encoded_value171 : encode value171 = rawvalue171 := by
  all_goals rfl
theorem nodes_value171 : nodes value171 = 1 := by rfl
theorem depth_value171 : depth value171 = 0 := by rfl
theorem canonical_value171 : canonical models value171 = true := by decide +kernel
theorem rawLength_value171 : rawvalue171.length = 13 := by
  decide +kernel
noncomputable def value172 : Value := .text "domain"
noncomputable def rawvalue172 : Bytes := asciiBytes "[\"str\",\"domain\"]"
theorem encoded_value172 : encode value172 = rawvalue172 := by
  all_goals rfl
theorem nodes_value172 : nodes value172 = 1 := by rfl
theorem depth_value172 : depth value172 = 0 := by rfl
theorem canonical_value172 : canonical models value172 = true := by decide +kernel
theorem rawLength_value172 : rawvalue172.length = 16 := by
  decide +kernel
noncomputable def value173 : Value := .function (.cons value109 value35 (.cons value110 value111 (.cons value112 value169 (.cons value170 value171 (.cons value3 value4 (.cons value14 value15 (.cons value172 value120 (.cons value5 value34 (.cons value6 value25 (.cons value167 value69 (.cons value19 value24 (.cons value161 value162 (.cons value30 value33 (.cons value50 value51 (.cons value31 value117 .nil)))))))))))))))
noncomputable def rawvalue173 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue109 ++ [44] ++ rawvalue35 ++ [93]),([91] ++ rawvalue110 ++ [44] ++ rawvalue111 ++ [93]),([91] ++ rawvalue112 ++ [44] ++ rawvalue169 ++ [93]),([91] ++ rawvalue170 ++ [44] ++ rawvalue171 ++ [93]),([91] ++ rawvalue3 ++ [44] ++ rawvalue4 ++ [93]),([91] ++ rawvalue14 ++ [44] ++ rawvalue15 ++ [93]),([91] ++ rawvalue172 ++ [44] ++ rawvalue120 ++ [93]),([91] ++ rawvalue5 ++ [44] ++ rawvalue34 ++ [93]),([91] ++ rawvalue6 ++ [44] ++ rawvalue25 ++ [93]),([91] ++ rawvalue167 ++ [44] ++ rawvalue69 ++ [93]),([91] ++ rawvalue19 ++ [44] ++ rawvalue24 ++ [93]),([91] ++ rawvalue161 ++ [44] ++ rawvalue162 ++ [93]),([91] ++ rawvalue30 ++ [44] ++ rawvalue33 ++ [93]),([91] ++ rawvalue50 ++ [44] ++ rawvalue51 ++ [93]),([91] ++ rawvalue31 ++ [44] ++ rawvalue117 ++ [93])] ++ [93,93]
theorem encoded_value173 : encode value173 = rawvalue173 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value109 ++ [44] ++ encode value35 ++ [93]),([91] ++ encode value110 ++ [44] ++ encode value111 ++ [93]),([91] ++ encode value112 ++ [44] ++ encode value169 ++ [93]),([91] ++ encode value170 ++ [44] ++ encode value171 ++ [93]),([91] ++ encode value3 ++ [44] ++ encode value4 ++ [93]),([91] ++ encode value14 ++ [44] ++ encode value15 ++ [93]),([91] ++ encode value172 ++ [44] ++ encode value120 ++ [93]),([91] ++ encode value5 ++ [44] ++ encode value34 ++ [93]),([91] ++ encode value6 ++ [44] ++ encode value25 ++ [93]),([91] ++ encode value167 ++ [44] ++ encode value69 ++ [93]),([91] ++ encode value19 ++ [44] ++ encode value24 ++ [93]),([91] ++ encode value161 ++ [44] ++ encode value162 ++ [93]),([91] ++ encode value30 ++ [44] ++ encode value33 ++ [93]),([91] ++ encode value50 ++ [44] ++ encode value51 ++ [93]),([91] ++ encode value31 ++ [44] ++ encode value117 ++ [93])] ++ [93,93] = _
  simp only [encoded_value109,encoded_value35,encoded_value110,encoded_value111,encoded_value112,encoded_value169,encoded_value170,encoded_value171,encoded_value3,encoded_value4,encoded_value14,encoded_value15,encoded_value172,encoded_value120,encoded_value5,encoded_value34,encoded_value6,encoded_value25,encoded_value167,encoded_value69,encoded_value19,encoded_value24,encoded_value161,encoded_value162,encoded_value30,encoded_value33,encoded_value50,encoded_value51,encoded_value31,encoded_value117]
  all_goals rfl
theorem order_value109_value110 : byteLess rawvalue109 rawvalue110 = true := by
  simp only [rawvalue109,rawvalue110,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value109_value112 : byteLess rawvalue109 rawvalue112 = true := by
  simp only [rawvalue109,rawvalue112,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value109_value170 : byteLess rawvalue109 rawvalue170 = true := by
  simp only [rawvalue109,rawvalue170,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value109_value3 : byteLess rawvalue109 rawvalue3 = true := by
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value109_value14 : byteLess rawvalue109 rawvalue14 = true := by
  simp only [rawvalue109,rawvalue14,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value109_value172 : byteLess rawvalue109 rawvalue172 = true := by
  simp only [rawvalue109,rawvalue172,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value109_value19 : byteLess rawvalue109 rawvalue19 = true := by
  simp only [rawvalue109,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value109_value30 : byteLess rawvalue109 rawvalue30 = true := by
  simp only [rawvalue109,rawvalue30,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value109_value50 : byteLess rawvalue109 rawvalue50 = true := by
  simp only [rawvalue109,rawvalue50,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value109_value31 : byteLess rawvalue109 rawvalue31 = true := by
  simp only [rawvalue109,rawvalue31,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value110_value112 : byteLess rawvalue110 rawvalue112 = true := by
  simp only [rawvalue110,rawvalue112,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value110_value170 : byteLess rawvalue110 rawvalue170 = true := by
  simp only [rawvalue110,rawvalue170,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value110_value3 : byteLess rawvalue110 rawvalue3 = true := by
  simp only [rawvalue110,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value110_value14 : byteLess rawvalue110 rawvalue14 = true := by
  simp only [rawvalue110,rawvalue14,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value110_value172 : byteLess rawvalue110 rawvalue172 = true := by
  simp only [rawvalue110,rawvalue172,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value110_value5 : byteLess rawvalue110 rawvalue5 = true := by
  simp only [rawvalue110,rawvalue5,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value110_value6 : byteLess rawvalue110 rawvalue6 = true := by
  simp only [rawvalue110,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value110_value167 : byteLess rawvalue110 rawvalue167 = true := by
  simp only [rawvalue110,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value110_value19 : byteLess rawvalue110 rawvalue19 = true := by
  simp only [rawvalue110,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value110_value161 : byteLess rawvalue110 rawvalue161 = true := by
  simp only [rawvalue110,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value110_value30 : byteLess rawvalue110 rawvalue30 = true := by
  simp only [rawvalue110,rawvalue30,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value110_value50 : byteLess rawvalue110 rawvalue50 = true := by
  simp only [rawvalue110,rawvalue50,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value110_value31 : byteLess rawvalue110 rawvalue31 = true := by
  simp only [rawvalue110,rawvalue31,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value112_value170 : byteLess rawvalue112 rawvalue170 = true := by
  simp only [rawvalue112,rawvalue170,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value112_value3 : byteLess rawvalue112 rawvalue3 = true := by
  simp only [rawvalue112,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value112_value14 : byteLess rawvalue112 rawvalue14 = true := by
  simp only [rawvalue112,rawvalue14,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value112_value172 : byteLess rawvalue112 rawvalue172 = true := by
  simp only [rawvalue112,rawvalue172,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value112_value5 : byteLess rawvalue112 rawvalue5 = true := by
  simp only [rawvalue112,rawvalue5,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value112_value6 : byteLess rawvalue112 rawvalue6 = true := by
  simp only [rawvalue112,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value112_value167 : byteLess rawvalue112 rawvalue167 = true := by
  simp only [rawvalue112,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value112_value19 : byteLess rawvalue112 rawvalue19 = true := by
  simp only [rawvalue112,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value112_value161 : byteLess rawvalue112 rawvalue161 = true := by
  simp only [rawvalue112,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value112_value30 : byteLess rawvalue112 rawvalue30 = true := by
  simp only [rawvalue112,rawvalue30,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value112_value50 : byteLess rawvalue112 rawvalue50 = true := by
  simp only [rawvalue112,rawvalue50,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value112_value31 : byteLess rawvalue112 rawvalue31 = true := by
  simp only [rawvalue112,rawvalue31,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value170_value3 : byteLess rawvalue170 rawvalue3 = true := by
  simp only [rawvalue170,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value170_value14 : byteLess rawvalue170 rawvalue14 = true := by
  simp only [rawvalue170,rawvalue14,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value170_value172 : byteLess rawvalue170 rawvalue172 = true := by
  simp only [rawvalue170,rawvalue172,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value170_value5 : byteLess rawvalue170 rawvalue5 = true := by
  simp only [rawvalue170,rawvalue5,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value170_value6 : byteLess rawvalue170 rawvalue6 = true := by
  simp only [rawvalue170,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value170_value167 : byteLess rawvalue170 rawvalue167 = true := by
  simp only [rawvalue170,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value170_value19 : byteLess rawvalue170 rawvalue19 = true := by
  simp only [rawvalue170,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value170_value161 : byteLess rawvalue170 rawvalue161 = true := by
  simp only [rawvalue170,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value170_value30 : byteLess rawvalue170 rawvalue30 = true := by
  simp only [rawvalue170,rawvalue30,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value170_value50 : byteLess rawvalue170 rawvalue50 = true := by
  simp only [rawvalue170,rawvalue50,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value170_value31 : byteLess rawvalue170 rawvalue31 = true := by
  simp only [rawvalue170,rawvalue31,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value3_value14 : byteLess rawvalue3 rawvalue14 = true := by
  simp only [rawvalue3,rawvalue14,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value3_value172 : byteLess rawvalue3 rawvalue172 = true := by
  simp only [rawvalue3,rawvalue172,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value3_value167 : byteLess rawvalue3 rawvalue167 = true := by
  simp only [rawvalue3,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value3_value19 : byteLess rawvalue3 rawvalue19 = true := by
  simp only [rawvalue3,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value3_value161 : byteLess rawvalue3 rawvalue161 = true := by
  simp only [rawvalue3,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value3_value50 : byteLess rawvalue3 rawvalue50 = true := by
  simp only [rawvalue3,rawvalue50,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value3_value31 : byteLess rawvalue3 rawvalue31 = true := by
  simp only [rawvalue3,rawvalue31,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value14_value172 : byteLess rawvalue14 rawvalue172 = true := by
  simp only [rawvalue14,rawvalue172,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value14_value5 : byteLess rawvalue14 rawvalue5 = true := by
  simp only [rawvalue14,rawvalue5,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value14_value6 : byteLess rawvalue14 rawvalue6 = true := by
  simp only [rawvalue14,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value14_value167 : byteLess rawvalue14 rawvalue167 = true := by
  simp only [rawvalue14,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value14_value161 : byteLess rawvalue14 rawvalue161 = true := by
  simp only [rawvalue14,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value14_value30 : byteLess rawvalue14 rawvalue30 = true := by
  simp only [rawvalue14,rawvalue30,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value14_value50 : byteLess rawvalue14 rawvalue50 = true := by
  simp only [rawvalue14,rawvalue50,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value14_value31 : byteLess rawvalue14 rawvalue31 = true := by
  simp only [rawvalue14,rawvalue31,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value172_value5 : byteLess rawvalue172 rawvalue5 = true := by
  simp only [rawvalue172,rawvalue5,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value172_value6 : byteLess rawvalue172 rawvalue6 = true := by
  simp only [rawvalue172,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value172_value167 : byteLess rawvalue172 rawvalue167 = true := by
  simp only [rawvalue172,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value172_value19 : byteLess rawvalue172 rawvalue19 = true := by
  simp only [rawvalue172,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value172_value161 : byteLess rawvalue172 rawvalue161 = true := by
  simp only [rawvalue172,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value172_value30 : byteLess rawvalue172 rawvalue30 = true := by
  simp only [rawvalue172,rawvalue30,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value172_value50 : byteLess rawvalue172 rawvalue50 = true := by
  simp only [rawvalue172,rawvalue50,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value172_value31 : byteLess rawvalue172 rawvalue31 = true := by
  simp only [rawvalue172,rawvalue31,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value5_value19 : byteLess rawvalue5 rawvalue19 = true := by
  simp only [rawvalue5,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value5_value50 : byteLess rawvalue5 rawvalue50 = true := by
  simp only [rawvalue5,rawvalue50,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value5_value31 : byteLess rawvalue5 rawvalue31 = true := by
  simp only [rawvalue5,rawvalue31,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value6_value19 : byteLess rawvalue6 rawvalue19 = true := by
  simp only [rawvalue6,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value6_value50 : byteLess rawvalue6 rawvalue50 = true := by
  simp only [rawvalue6,rawvalue50,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value167_value19 : byteLess rawvalue167 rawvalue19 = true := by
  simp only [rawvalue167,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value167_value30 : byteLess rawvalue167 rawvalue30 = true := by
  simp only [rawvalue167,rawvalue30,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value167_value50 : byteLess rawvalue167 rawvalue50 = true := by
  simp only [rawvalue167,rawvalue50,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value167_value31 : byteLess rawvalue167 rawvalue31 = true := by
  simp only [rawvalue167,rawvalue31,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value19_value161 : byteLess rawvalue19 rawvalue161 = true := by
  simp only [rawvalue19,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value19_value30 : byteLess rawvalue19 rawvalue30 = true := by
  simp only [rawvalue19,rawvalue30,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value19_value50 : byteLess rawvalue19 rawvalue50 = true := by
  simp only [rawvalue19,rawvalue50,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value19_value31 : byteLess rawvalue19 rawvalue31 = true := by
  simp only [rawvalue19,rawvalue31,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value161_value30 : byteLess rawvalue161 rawvalue30 = true := by
  simp only [rawvalue161,rawvalue30,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value161_value50 : byteLess rawvalue161 rawvalue50 = true := by
  simp only [rawvalue161,rawvalue50,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value161_value31 : byteLess rawvalue161 rawvalue31 = true := by
  simp only [rawvalue161,rawvalue31,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value30_value50 : byteLess rawvalue30 rawvalue50 = true := by
  simp only [rawvalue30,rawvalue50,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value30_value31 : byteLess rawvalue30 rawvalue31 = true := by
  simp only [rawvalue30,rawvalue31,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value50_value31 : byteLess rawvalue50 rawvalue31 = true := by
  simp only [rawvalue50,rawvalue31,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value173 : nodes value173 = 623 := by
  change 1 + (nodes value109 + nodes value35 + (nodes value110 + nodes value111 + (nodes value112 + nodes value169 + (nodes value170 + nodes value171 + (nodes value3 + nodes value4 + (nodes value14 + nodes value15 + (nodes value172 + nodes value120 + (nodes value5 + nodes value34 + (nodes value6 + nodes value25 + (nodes value167 + nodes value69 + (nodes value19 + nodes value24 + (nodes value161 + nodes value162 + (nodes value30 + nodes value33 + (nodes value50 + nodes value51 + (nodes value31 + nodes value117 + 0))))))))))))))) = 623
  simp only [nodes_value109,nodes_value35,nodes_value110,nodes_value111,nodes_value112,nodes_value169,nodes_value170,nodes_value171,nodes_value3,nodes_value4,nodes_value14,nodes_value15,nodes_value172,nodes_value120,nodes_value5,nodes_value34,nodes_value6,nodes_value25,nodes_value167,nodes_value69,nodes_value19,nodes_value24,nodes_value161,nodes_value162,nodes_value30,nodes_value33,nodes_value50,nodes_value51,nodes_value31,nodes_value117]
  all_goals decide +kernel
theorem depth_value173 : depth value173 = 8 := by
  change max (max (1 + depth value109) (1 + depth value35)) (max (max (1 + depth value110) (1 + depth value111)) (max (max (1 + depth value112) (1 + depth value169)) (max (max (1 + depth value170) (1 + depth value171)) (max (max (1 + depth value3) (1 + depth value4)) (max (max (1 + depth value14) (1 + depth value15)) (max (max (1 + depth value172) (1 + depth value120)) (max (max (1 + depth value5) (1 + depth value34)) (max (max (1 + depth value6) (1 + depth value25)) (max (max (1 + depth value167) (1 + depth value69)) (max (max (1 + depth value19) (1 + depth value24)) (max (max (1 + depth value161) (1 + depth value162)) (max (max (1 + depth value30) (1 + depth value33)) (max (max (1 + depth value50) (1 + depth value51)) (max (max (1 + depth value31) (1 + depth value117)) (0))))))))))))))) = 8
  simp only [depth_value109,depth_value35,depth_value110,depth_value111,depth_value112,depth_value169,depth_value170,depth_value171,depth_value3,depth_value4,depth_value14,depth_value15,depth_value172,depth_value120,depth_value5,depth_value34,depth_value6,depth_value25,depth_value167,depth_value69,depth_value19,depth_value24,depth_value161,depth_value162,depth_value30,depth_value33,depth_value50,depth_value51,depth_value31,depth_value117]
  all_goals decide +kernel
theorem canonical_value173 : canonical models value173 = true := by
  change ((canonical models value109 && canonical models value35 && (canonical models value110 && canonical models value111 && (canonical models value112 && canonical models value169 && (canonical models value170 && canonical models value171 && (canonical models value3 && canonical models value4 && (canonical models value14 && canonical models value15 && (canonical models value172 && canonical models value120 && (canonical models value5 && canonical models value34 && (canonical models value6 && canonical models value25 && (canonical models value167 && canonical models value69 && (canonical models value19 && canonical models value24 && (canonical models value161 && canonical models value162 && (canonical models value30 && canonical models value33 && (canonical models value50 && canonical models value51 && (canonical models value31 && canonical models value117 && true))))))))))))))) && ordered [encode value109,encode value110,encode value112,encode value170,encode value3,encode value14,encode value172,encode value5,encode value6,encode value167,encode value19,encode value161,encode value30,encode value50,encode value31]) = true
  simp only [canonical_value109,canonical_value35,canonical_value110,canonical_value111,canonical_value112,canonical_value169,canonical_value170,canonical_value171,canonical_value3,canonical_value4,canonical_value14,canonical_value15,canonical_value172,canonical_value120,canonical_value5,canonical_value34,canonical_value6,canonical_value25,canonical_value167,canonical_value69,canonical_value19,canonical_value24,canonical_value161,canonical_value162,canonical_value30,canonical_value33,canonical_value50,canonical_value51,canonical_value31,canonical_value117,encoded_value109,encoded_value110,encoded_value112,encoded_value170,encoded_value3,encoded_value14,encoded_value172,encoded_value5,encoded_value6,encoded_value167,encoded_value19,encoded_value161,encoded_value30,encoded_value50,encoded_value31]
  simp only [ordered,List.all_cons,List.all_nil,order_value109_value110,order_value109_value112,order_value109_value170,order_value109_value3,order_value109_value14,order_value109_value172,order_value109_value5,order_value109_value6,order_value109_value167,order_value109_value19,order_value109_value161,order_value109_value30,order_value109_value50,order_value109_value31,order_value110_value112,order_value110_value170,order_value110_value3,order_value110_value14,order_value110_value172,order_value110_value5,order_value110_value6,order_value110_value167,order_value110_value19,order_value110_value161,order_value110_value30,order_value110_value50,order_value110_value31,order_value112_value170,order_value112_value3,order_value112_value14,order_value112_value172,order_value112_value5,order_value112_value6,order_value112_value167,order_value112_value19,order_value112_value161,order_value112_value30,order_value112_value50,order_value112_value31,order_value170_value3,order_value170_value14,order_value170_value172,order_value170_value5,order_value170_value6,order_value170_value167,order_value170_value19,order_value170_value161,order_value170_value30,order_value170_value50,order_value170_value31,order_value3_value14,order_value3_value172,order_value3_value5,order_value3_value6,order_value3_value167,order_value3_value19,order_value3_value161,order_value3_value30,order_value3_value50,order_value3_value31,order_value14_value172,order_value14_value5,order_value14_value6,order_value14_value167,order_value14_value19,order_value14_value161,order_value14_value30,order_value14_value50,order_value14_value31,order_value172_value5,order_value172_value6,order_value172_value167,order_value172_value19,order_value172_value161,order_value172_value30,order_value172_value50,order_value172_value31,order_value5_value6,order_value5_value167,order_value5_value19,order_value5_value161,order_value5_value30,order_value5_value50,order_value5_value31,order_value6_value167,order_value6_value19,order_value6_value161,order_value6_value30,order_value6_value50,order_value6_value31,order_value167_value19,order_value167_value161,order_value167_value30,order_value167_value50,order_value167_value31,order_value19_value161,order_value19_value30,order_value19_value50,order_value19_value31,order_value161_value30,order_value161_value50,order_value161_value31,order_value30_value50,order_value30_value31,order_value50_value31,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value173 : rawvalue173.length = 10500 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value109) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value35) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value110) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value111) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value112) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value169) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value170) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value171) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value3) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value4) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value14) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value15) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value172) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value120) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value5) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value34) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value6) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value25) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value167) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value69) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value19) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value24) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value161) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value162) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value30) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value33) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value50) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value51) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value31) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value117) (show ([93] : Bytes).length = 1 from by decide +kernel)))))))))))))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value174 : Value := .set (.cons value173 .nil)
noncomputable def rawvalue174 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue173] ++ [93,93]
theorem encoded_value174 : encode value174 = rawvalue174 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value173] ++ [93,93] = _
  simp only [encoded_value173]
  all_goals rfl
theorem nodes_value174 : nodes value174 = 624 := by
  change 1 + (nodes value173 + 0) = 624
  simp only [nodes_value173]
  all_goals decide +kernel
theorem depth_value174 : depth value174 = 9 := by
  change max (1 + depth value173) (0) = 9
  simp only [depth_value173]
  all_goals decide +kernel
theorem canonical_value174 : canonical models value174 = true := by
  change ((canonical models value173 && true) && ordered [encode value173]) = true
  simp only [canonical_value173,encoded_value173]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value174 : rawvalue174.length = 10510 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value173)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value175 : Value := .text "ACTIVE"
noncomputable def rawvalue175 : Bytes := asciiBytes "[\"str\",\"ACTIVE\"]"
theorem encoded_value175 : encode value175 = rawvalue175 := by
  all_goals rfl
theorem nodes_value175 : nodes value175 = 1 := by rfl
theorem depth_value175 : depth value175 = 0 := by rfl
theorem canonical_value175 : canonical models value175 = true := by decide +kernel
theorem rawLength_value175 : rawvalue175.length = 16 := by
  decide +kernel
noncomputable def value176 : Value := .function (.cons value2 value15 (.cons value72 value87 .nil))
noncomputable def rawvalue176 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue15 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue87 ++ [93])] ++ [93,93]
theorem encoded_value176 : encode value176 = rawvalue176 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value15 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value87 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value15,encoded_value72,encoded_value87]
  all_goals rfl
theorem nodes_value176 : nodes value176 = 11 := by
  change 1 + (nodes value2 + nodes value15 + (nodes value72 + nodes value87 + 0)) = 11
  simp only [nodes_value2,nodes_value15,nodes_value72,nodes_value87]
  all_goals decide +kernel
theorem depth_value176 : depth value176 = 2 := by
  change max (max (1 + depth value2) (1 + depth value15)) (max (max (1 + depth value72) (1 + depth value87)) (0)) = 2
  simp only [depth_value2,depth_value15,depth_value72,depth_value87]
  all_goals decide +kernel
theorem canonical_value176 : canonical models value176 = true := by
  change ((canonical models value2 && canonical models value15 && (canonical models value72 && canonical models value87 && true)) && ordered [encode value2,encode value72]) = true
  simp only [canonical_value2,canonical_value15,canonical_value72,canonical_value87,encoded_value2,encoded_value72]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value176 : rawvalue176.length = 187 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value15) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value87) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value177 : Value := .set (.cons value176 .nil)
noncomputable def rawvalue177 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue176] ++ [93,93]
theorem encoded_value177 : encode value177 = rawvalue177 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value176] ++ [93,93] = _
  simp only [encoded_value176]
  all_goals rfl
theorem nodes_value177 : nodes value177 = 12 := by
  change 1 + (nodes value176 + 0) = 12
  simp only [nodes_value176]
  all_goals decide +kernel
theorem depth_value177 : depth value177 = 3 := by
  change max (1 + depth value176) (0) = 3
  simp only [depth_value176]
  all_goals decide +kernel
theorem canonical_value177 : canonical models value177 = true := by
  change ((canonical models value176 && true) && ordered [encode value176]) = true
  simp only [canonical_value176,encoded_value176]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value177 : rawvalue177.length = 197 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value176)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value178 : Value := .text "READY"
noncomputable def rawvalue178 : Bytes := asciiBytes "[\"str\",\"READY\"]"
theorem encoded_value178 : encode value178 = rawvalue178 := by
  all_goals rfl
theorem nodes_value178 : nodes value178 = 1 := by rfl
theorem depth_value178 : depth value178 = 0 := by rfl
theorem canonical_value178 : canonical models value178 = true := by decide +kernel
theorem rawLength_value178 : rawvalue178.length = 15 := by
  decide +kernel
noncomputable def value179 : Value := .function (.cons value37 value178 (.cons value38 value178 (.cons value39 value178 (.cons value43 value178 .nil))))
noncomputable def rawvalue179 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue37 ++ [44] ++ rawvalue178 ++ [93]),([91] ++ rawvalue38 ++ [44] ++ rawvalue178 ++ [93]),([91] ++ rawvalue39 ++ [44] ++ rawvalue178 ++ [93]),([91] ++ rawvalue43 ++ [44] ++ rawvalue178 ++ [93])] ++ [93,93]
theorem encoded_value179 : encode value179 = rawvalue179 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value37 ++ [44] ++ encode value178 ++ [93]),([91] ++ encode value38 ++ [44] ++ encode value178 ++ [93]),([91] ++ encode value39 ++ [44] ++ encode value178 ++ [93]),([91] ++ encode value43 ++ [44] ++ encode value178 ++ [93])] ++ [93,93] = _
  simp only [encoded_value37,encoded_value178,encoded_value38,encoded_value39,encoded_value43]
  all_goals rfl
theorem nodes_value179 : nodes value179 = 9 := by
  change 1 + (nodes value37 + nodes value178 + (nodes value38 + nodes value178 + (nodes value39 + nodes value178 + (nodes value43 + nodes value178 + 0)))) = 9
  simp only [nodes_value37,nodes_value178,nodes_value38,nodes_value39,nodes_value43]
  all_goals decide +kernel
theorem depth_value179 : depth value179 = 1 := by
  change max (max (1 + depth value37) (1 + depth value178)) (max (max (1 + depth value38) (1 + depth value178)) (max (max (1 + depth value39) (1 + depth value178)) (max (max (1 + depth value43) (1 + depth value178)) (0)))) = 1
  simp only [depth_value37,depth_value178,depth_value38,depth_value39,depth_value43]
  all_goals decide +kernel
theorem canonical_value179 : canonical models value179 = true := by
  change ((canonical models value37 && canonical models value178 && (canonical models value38 && canonical models value178 && (canonical models value39 && canonical models value178 && (canonical models value43 && canonical models value178 && true)))) && ordered [encode value37,encode value38,encode value39,encode value43]) = true
  simp only [canonical_value37,canonical_value178,canonical_value38,canonical_value39,canonical_value43,encoded_value37,encoded_value38,encoded_value39,encoded_value43]
  simp only [ordered,List.all_cons,List.all_nil,order_value37_value38,order_value37_value39,order_value37_value43,order_value38_value39,order_value38_value43,order_value39_value43,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value179 : rawvalue179.length = 141 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value37) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value178) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value38) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value178) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value39) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value178) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value43) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value178) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value180 : Value := .function (.cons value9 value64 .nil)
noncomputable def rawvalue180 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue9 ++ [44] ++ rawvalue64 ++ [93])] ++ [93,93]
theorem encoded_value180 : encode value180 = rawvalue180 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value9 ++ [44] ++ encode value64 ++ [93])] ++ [93,93] = _
  simp only [encoded_value9,encoded_value64]
  all_goals rfl
theorem nodes_value180 : nodes value180 = 3 := by
  change 1 + (nodes value9 + nodes value64 + 0) = 3
  simp only [nodes_value9,nodes_value64]
  all_goals decide +kernel
theorem depth_value180 : depth value180 = 1 := by
  change max (max (1 + depth value9) (1 + depth value64)) (0) = 1
  simp only [depth_value9,depth_value64]
  all_goals decide +kernel
theorem canonical_value180 : canonical models value180 = true := by
  change ((canonical models value9 && canonical models value64 && true) && ordered [encode value9]) = true
  simp only [canonical_value9,canonical_value64,encoded_value9]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value180 : rawvalue180.length = 44 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value9) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value64) (show ([93] : Bytes).length = 1 from by decide +kernel)))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value181 : Value := .set (.cons value33 .nil)
noncomputable def rawvalue181 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue33] ++ [93,93]
theorem encoded_value181 : encode value181 = rawvalue181 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value33] ++ [93,93] = _
  simp only [encoded_value33]
  all_goals rfl
theorem nodes_value181 : nodes value181 = 32 := by
  change 1 + (nodes value33 + 0) = 32
  simp only [nodes_value33]
  all_goals decide +kernel
theorem depth_value181 : depth value181 = 5 := by
  change max (1 + depth value33) (0) = 5
  simp only [depth_value33]
  all_goals decide +kernel
theorem canonical_value181 : canonical models value181 = true := by
  change ((canonical models value33 && true) && ordered [encode value33]) = true
  simp only [canonical_value33,encoded_value33]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value181 : rawvalue181.length = 538 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value33)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value182 : Value := .text "batchBudget"
noncomputable def rawvalue182 : Bytes := asciiBytes "[\"str\",\"batchBudget\"]"
theorem encoded_value182 : encode value182 = rawvalue182 := by
  all_goals rfl
theorem nodes_value182 : nodes value182 = 1 := by rfl
theorem depth_value182 : depth value182 = 0 := by rfl
theorem canonical_value182 : canonical models value182 = true := by decide +kernel
theorem rawLength_value182 : rawvalue182.length = 21 := by
  decide +kernel
noncomputable def value183 : Value := .text "data"
noncomputable def rawvalue183 : Bytes := asciiBytes "[\"str\",\"data\"]"
theorem encoded_value183 : encode value183 = rawvalue183 := by
  all_goals rfl
theorem nodes_value183 : nodes value183 = 1 := by rfl
theorem depth_value183 : depth value183 = 0 := by rfl
theorem canonical_value183 : canonical models value183 = true := by decide +kernel
theorem rawLength_value183 : rawvalue183.length = 14 := by
  decide +kernel
noncomputable def value184 : Value := .model "data1"
noncomputable def rawvalue184 : Bytes := asciiBytes "[\"model\",\"data1\"]"
theorem encoded_value184 : encode value184 = rawvalue184 := by
  all_goals rfl
theorem nodes_value184 : nodes value184 = 1 := by rfl
theorem depth_value184 : depth value184 = 0 := by rfl
theorem canonical_value184 : canonical models value184 = true := by decide +kernel
theorem rawLength_value184 : rawvalue184.length = 17 := by
  decide +kernel
noncomputable def value185 : Value := .text "stepBudget"
noncomputable def rawvalue185 : Bytes := asciiBytes "[\"str\",\"stepBudget\"]"
theorem encoded_value185 : encode value185 = rawvalue185 := by
  all_goals rfl
theorem nodes_value185 : nodes value185 = 1 := by rfl
theorem depth_value185 : depth value185 = 0 := by rfl
theorem canonical_value185 : canonical models value185 = true := by decide +kernel
theorem rawLength_value185 : rawvalue185.length = 20 := by
  decide +kernel
noncomputable def value186 : Value := .function (.cons value182 value117 (.cons value183 value184 (.cons value172 value120 (.cons value167 value69 (.cons value168 value111 (.cons value161 value162 (.cons value185 value117 (.cons value10 value11 .nil))))))))
noncomputable def rawvalue186 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue182 ++ [44] ++ rawvalue117 ++ [93]),([91] ++ rawvalue183 ++ [44] ++ rawvalue184 ++ [93]),([91] ++ rawvalue172 ++ [44] ++ rawvalue120 ++ [93]),([91] ++ rawvalue167 ++ [44] ++ rawvalue69 ++ [93]),([91] ++ rawvalue168 ++ [44] ++ rawvalue111 ++ [93]),([91] ++ rawvalue161 ++ [44] ++ rawvalue162 ++ [93]),([91] ++ rawvalue185 ++ [44] ++ rawvalue117 ++ [93]),([91] ++ rawvalue10 ++ [44] ++ rawvalue11 ++ [93])] ++ [93,93]
theorem encoded_value186 : encode value186 = rawvalue186 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value182 ++ [44] ++ encode value117 ++ [93]),([91] ++ encode value183 ++ [44] ++ encode value184 ++ [93]),([91] ++ encode value172 ++ [44] ++ encode value120 ++ [93]),([91] ++ encode value167 ++ [44] ++ encode value69 ++ [93]),([91] ++ encode value168 ++ [44] ++ encode value111 ++ [93]),([91] ++ encode value161 ++ [44] ++ encode value162 ++ [93]),([91] ++ encode value185 ++ [44] ++ encode value117 ++ [93]),([91] ++ encode value10 ++ [44] ++ encode value11 ++ [93])] ++ [93,93] = _
  simp only [encoded_value182,encoded_value117,encoded_value183,encoded_value184,encoded_value172,encoded_value120,encoded_value167,encoded_value69,encoded_value168,encoded_value111,encoded_value161,encoded_value162,encoded_value185,encoded_value10,encoded_value11]
  all_goals rfl
theorem order_value182_value183 : byteLess rawvalue182 rawvalue183 = true := by
  simp only [rawvalue182,rawvalue183,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value182_value172 : byteLess rawvalue182 rawvalue172 = true := by
  simp only [rawvalue182,rawvalue172,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value182_value167 : byteLess rawvalue182 rawvalue167 = true := by
  simp only [rawvalue182,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value182_value168 : byteLess rawvalue182 rawvalue168 = true := by
  simp only [rawvalue182,rawvalue168,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value182_value161 : byteLess rawvalue182 rawvalue161 = true := by
  simp only [rawvalue182,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value182_value185 : byteLess rawvalue182 rawvalue185 = true := by
  simp only [rawvalue182,rawvalue185,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value182_value10 : byteLess rawvalue182 rawvalue10 = true := by
  simp only [rawvalue182,rawvalue10,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value183_value172 : byteLess rawvalue183 rawvalue172 = true := by
  simp only [rawvalue183,rawvalue172,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value183_value167 : byteLess rawvalue183 rawvalue167 = true := by
  simp only [rawvalue183,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value183_value168 : byteLess rawvalue183 rawvalue168 = true := by
  simp only [rawvalue183,rawvalue168,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value183_value161 : byteLess rawvalue183 rawvalue161 = true := by
  simp only [rawvalue183,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value183_value185 : byteLess rawvalue183 rawvalue185 = true := by
  simp only [rawvalue183,rawvalue185,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value183_value10 : byteLess rawvalue183 rawvalue10 = true := by
  simp only [rawvalue183,rawvalue10,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value172_value168 : byteLess rawvalue172 rawvalue168 = true := by
  simp only [rawvalue172,rawvalue168,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value172_value185 : byteLess rawvalue172 rawvalue185 = true := by
  simp only [rawvalue172,rawvalue185,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value172_value10 : byteLess rawvalue172 rawvalue10 = true := by
  simp only [rawvalue172,rawvalue10,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value167_value185 : byteLess rawvalue167 rawvalue185 = true := by
  simp only [rawvalue167,rawvalue185,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value167_value10 : byteLess rawvalue167 rawvalue10 = true := by
  simp only [rawvalue167,rawvalue10,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value168_value185 : byteLess rawvalue168 rawvalue185 = true := by
  simp only [rawvalue168,rawvalue185,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value168_value10 : byteLess rawvalue168 rawvalue10 = true := by
  simp only [rawvalue168,rawvalue10,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value161_value185 : byteLess rawvalue161 rawvalue185 = true := by
  simp only [rawvalue161,rawvalue185,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value161_value10 : byteLess rawvalue161 rawvalue10 = true := by
  simp only [rawvalue161,rawvalue10,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value185_value10 : byteLess rawvalue185 rawvalue10 = true := by
  simp only [rawvalue185,rawvalue10,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value186 : nodes value186 = 17 := by
  change 1 + (nodes value182 + nodes value117 + (nodes value183 + nodes value184 + (nodes value172 + nodes value120 + (nodes value167 + nodes value69 + (nodes value168 + nodes value111 + (nodes value161 + nodes value162 + (nodes value185 + nodes value117 + (nodes value10 + nodes value11 + 0)))))))) = 17
  simp only [nodes_value182,nodes_value117,nodes_value183,nodes_value184,nodes_value172,nodes_value120,nodes_value167,nodes_value69,nodes_value168,nodes_value111,nodes_value161,nodes_value162,nodes_value185,nodes_value10,nodes_value11]
  all_goals decide +kernel
theorem depth_value186 : depth value186 = 1 := by
  change max (max (1 + depth value182) (1 + depth value117)) (max (max (1 + depth value183) (1 + depth value184)) (max (max (1 + depth value172) (1 + depth value120)) (max (max (1 + depth value167) (1 + depth value69)) (max (max (1 + depth value168) (1 + depth value111)) (max (max (1 + depth value161) (1 + depth value162)) (max (max (1 + depth value185) (1 + depth value117)) (max (max (1 + depth value10) (1 + depth value11)) (0)))))))) = 1
  simp only [depth_value182,depth_value117,depth_value183,depth_value184,depth_value172,depth_value120,depth_value167,depth_value69,depth_value168,depth_value111,depth_value161,depth_value162,depth_value185,depth_value10,depth_value11]
  all_goals decide +kernel
theorem canonical_value186 : canonical models value186 = true := by
  change ((canonical models value182 && canonical models value117 && (canonical models value183 && canonical models value184 && (canonical models value172 && canonical models value120 && (canonical models value167 && canonical models value69 && (canonical models value168 && canonical models value111 && (canonical models value161 && canonical models value162 && (canonical models value185 && canonical models value117 && (canonical models value10 && canonical models value11 && true)))))))) && ordered [encode value182,encode value183,encode value172,encode value167,encode value168,encode value161,encode value185,encode value10]) = true
  simp only [canonical_value182,canonical_value117,canonical_value183,canonical_value184,canonical_value172,canonical_value120,canonical_value167,canonical_value69,canonical_value168,canonical_value111,canonical_value161,canonical_value162,canonical_value185,canonical_value10,canonical_value11,encoded_value182,encoded_value183,encoded_value172,encoded_value167,encoded_value168,encoded_value161,encoded_value185,encoded_value10]
  simp only [ordered,List.all_cons,List.all_nil,order_value182_value183,order_value182_value172,order_value182_value167,order_value182_value168,order_value182_value161,order_value182_value185,order_value182_value10,order_value183_value172,order_value183_value167,order_value183_value168,order_value183_value161,order_value183_value185,order_value183_value10,order_value172_value167,order_value172_value168,order_value172_value161,order_value172_value185,order_value172_value10,order_value167_value168,order_value167_value161,order_value167_value185,order_value167_value10,order_value168_value161,order_value168_value185,order_value168_value10,order_value161_value185,order_value161_value10,order_value185_value10,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value186 : rawvalue186.length = 302 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value182) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value117) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value183) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value184) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value172) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value120) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value167) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value69) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value168) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value111) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value161) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value162) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value185) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value117) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value10) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value11) (show ([93] : Bytes).length = 1 from by decide +kernel))))))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value187 : Value := .set (.cons value186 .nil)
noncomputable def rawvalue187 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue186] ++ [93,93]
theorem encoded_value187 : encode value187 = rawvalue187 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value186] ++ [93,93] = _
  simp only [encoded_value186]
  all_goals rfl
theorem nodes_value187 : nodes value187 = 18 := by
  change 1 + (nodes value186 + 0) = 18
  simp only [nodes_value186]
  all_goals decide +kernel
theorem depth_value187 : depth value187 = 2 := by
  change max (1 + depth value186) (0) = 2
  simp only [depth_value186]
  all_goals decide +kernel
theorem canonical_value187 : canonical models value187 = true := by
  change ((canonical models value186 && true) && ordered [encode value186]) = true
  simp only [canonical_value186,encoded_value186]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value187 : rawvalue187.length = 312 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value186)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value188 : Value := .integer (5)
noncomputable def rawvalue188 : Bytes := asciiBytes "[\"int\",\"5\"]"
theorem encoded_value188 : encode value188 = rawvalue188 := by
  all_goals rfl
theorem nodes_value188 : nodes value188 = 1 := by rfl
theorem depth_value188 : depth value188 = 0 := by rfl
theorem canonical_value188 : canonical models value188 = true := by decide +kernel
theorem rawLength_value188 : rawvalue188.length = 11 := by
  decide +kernel
noncomputable def value189 : Value := .function (.cons value37 value188 (.cons value38 value70 (.cons value39 value70 (.cons value43 value64 .nil))))
noncomputable def rawvalue189 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue37 ++ [44] ++ rawvalue188 ++ [93]),([91] ++ rawvalue38 ++ [44] ++ rawvalue70 ++ [93]),([91] ++ rawvalue39 ++ [44] ++ rawvalue70 ++ [93]),([91] ++ rawvalue43 ++ [44] ++ rawvalue64 ++ [93])] ++ [93,93]
theorem encoded_value189 : encode value189 = rawvalue189 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value37 ++ [44] ++ encode value188 ++ [93]),([91] ++ encode value38 ++ [44] ++ encode value70 ++ [93]),([91] ++ encode value39 ++ [44] ++ encode value70 ++ [93]),([91] ++ encode value43 ++ [44] ++ encode value64 ++ [93])] ++ [93,93] = _
  simp only [encoded_value37,encoded_value188,encoded_value38,encoded_value70,encoded_value39,encoded_value43,encoded_value64]
  all_goals rfl
theorem nodes_value189 : nodes value189 = 9 := by
  change 1 + (nodes value37 + nodes value188 + (nodes value38 + nodes value70 + (nodes value39 + nodes value70 + (nodes value43 + nodes value64 + 0)))) = 9
  simp only [nodes_value37,nodes_value188,nodes_value38,nodes_value70,nodes_value39,nodes_value43,nodes_value64]
  all_goals decide +kernel
theorem depth_value189 : depth value189 = 1 := by
  change max (max (1 + depth value37) (1 + depth value188)) (max (max (1 + depth value38) (1 + depth value70)) (max (max (1 + depth value39) (1 + depth value70)) (max (max (1 + depth value43) (1 + depth value64)) (0)))) = 1
  simp only [depth_value37,depth_value188,depth_value38,depth_value70,depth_value39,depth_value43,depth_value64]
  all_goals decide +kernel
theorem canonical_value189 : canonical models value189 = true := by
  change ((canonical models value37 && canonical models value188 && (canonical models value38 && canonical models value70 && (canonical models value39 && canonical models value70 && (canonical models value43 && canonical models value64 && true)))) && ordered [encode value37,encode value38,encode value39,encode value43]) = true
  simp only [canonical_value37,canonical_value188,canonical_value38,canonical_value70,canonical_value39,canonical_value43,canonical_value64,encoded_value37,encoded_value38,encoded_value39,encoded_value43]
  simp only [ordered,List.all_cons,List.all_nil,order_value37_value38,order_value37_value39,order_value37_value43,order_value38_value39,order_value38_value43,order_value39_value43,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value189 : rawvalue189.length = 125 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value37) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value188) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value38) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value70) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value39) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value70) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value43) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value64) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value190 : Value := .function (.cons value172 value120 (.cons value50 value51 .nil))
noncomputable def rawvalue190 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue172 ++ [44] ++ rawvalue120 ++ [93]),([91] ++ rawvalue50 ++ [44] ++ rawvalue51 ++ [93])] ++ [93,93]
theorem encoded_value190 : encode value190 = rawvalue190 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value172 ++ [44] ++ encode value120 ++ [93]),([91] ++ encode value50 ++ [44] ++ encode value51 ++ [93])] ++ [93,93] = _
  simp only [encoded_value172,encoded_value120,encoded_value50,encoded_value51]
  all_goals rfl
theorem nodes_value190 : nodes value190 = 5 := by
  change 1 + (nodes value172 + nodes value120 + (nodes value50 + nodes value51 + 0)) = 5
  simp only [nodes_value172,nodes_value120,nodes_value50,nodes_value51]
  all_goals decide +kernel
theorem depth_value190 : depth value190 = 1 := by
  change max (max (1 + depth value172) (1 + depth value120)) (max (max (1 + depth value50) (1 + depth value51)) (0)) = 1
  simp only [depth_value172,depth_value120,depth_value50,depth_value51]
  all_goals decide +kernel
theorem canonical_value190 : canonical models value190 = true := by
  change ((canonical models value172 && canonical models value120 && (canonical models value50 && canonical models value51 && true)) && ordered [encode value172,encode value50]) = true
  simp only [canonical_value172,canonical_value120,canonical_value50,canonical_value51,encoded_value172,encoded_value50]
  simp only [ordered,List.all_cons,List.all_nil,order_value172_value50,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value190 : rawvalue190.length = 80 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value172) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value120) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value50) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value51) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value191 : Value := .text "PARAMETER"
noncomputable def rawvalue191 : Bytes := asciiBytes "[\"str\",\"PARAMETER\"]"
theorem encoded_value191 : encode value191 = rawvalue191 := by
  all_goals rfl
theorem nodes_value191 : nodes value191 = 1 := by rfl
theorem depth_value191 : depth value191 = 0 := by rfl
theorem canonical_value191 : canonical models value191 = true := by decide +kernel
theorem rawLength_value191 : rawvalue191.length = 19 := by
  decide +kernel
noncomputable def value192 : Value := .function (.cons value2 value173 (.cons value72 value190 (.cons value73 value191 (.cons value45 value37 .nil))))
noncomputable def rawvalue192 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue173 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue190 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue191 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue37 ++ [93])] ++ [93,93]
theorem encoded_value192 : encode value192 = rawvalue192 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value173 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value190 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value191 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value37 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value173,encoded_value72,encoded_value190,encoded_value73,encoded_value191,encoded_value45,encoded_value37]
  all_goals rfl
theorem nodes_value192 : nodes value192 = 635 := by
  change 1 + (nodes value2 + nodes value173 + (nodes value72 + nodes value190 + (nodes value73 + nodes value191 + (nodes value45 + nodes value37 + 0)))) = 635
  simp only [nodes_value2,nodes_value173,nodes_value72,nodes_value190,nodes_value73,nodes_value191,nodes_value45,nodes_value37]
  all_goals decide +kernel
theorem depth_value192 : depth value192 = 9 := by
  change max (max (1 + depth value2) (1 + depth value173)) (max (max (1 + depth value72) (1 + depth value190)) (max (max (1 + depth value73) (1 + depth value191)) (max (max (1 + depth value45) (1 + depth value37)) (0)))) = 9
  simp only [depth_value2,depth_value173,depth_value72,depth_value190,depth_value73,depth_value191,depth_value45,depth_value37]
  all_goals decide +kernel
theorem canonical_value192 : canonical models value192 = true := by
  change ((canonical models value2 && canonical models value173 && (canonical models value72 && canonical models value190 && (canonical models value73 && canonical models value191 && (canonical models value45 && canonical models value37 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value173,canonical_value72,canonical_value190,canonical_value73,canonical_value191,canonical_value45,canonical_value37,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value192 : rawvalue192.length = 10702 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value173) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value190) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value191) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value37) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value193 : Value := .set (.cons value192 (.cons value75 (.cons value76 (.cons value77 (.cons value79 (.cons value80 (.cons value81 (.cons value83 (.cons value84 (.cons value85 (.cons value88 (.cons value89 (.cons value90 .nil)))))))))))))
noncomputable def rawvalue193 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue192,rawvalue75,rawvalue76,rawvalue77,rawvalue79,rawvalue80,rawvalue81,rawvalue83,rawvalue84,rawvalue85,rawvalue88,rawvalue89,rawvalue90] ++ [93,93]
theorem encoded_value193 : encode value193 = rawvalue193 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value192,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90] ++ [93,93] = _
  simp only [encoded_value192,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  all_goals rfl
theorem order_value192_value75 : byteLess rawvalue192 rawvalue75 = true := by
  simp only [rawvalue192,rawvalue75,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value192_value76 : byteLess rawvalue192 rawvalue76 = true := by
  simp only [rawvalue192,rawvalue76,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value192_value77 : byteLess rawvalue192 rawvalue77 = true := by
  simp only [rawvalue192,rawvalue77,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value192_value79 : byteLess rawvalue192 rawvalue79 = true := by
  simp only [rawvalue192,rawvalue79,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value192_value80 : byteLess rawvalue192 rawvalue80 = true := by
  simp only [rawvalue192,rawvalue80,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value192_value81 : byteLess rawvalue192 rawvalue81 = true := by
  simp only [rawvalue192,rawvalue81,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value192_value83 : byteLess rawvalue192 rawvalue83 = true := by
  simp only [rawvalue192,rawvalue83,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value192_value84 : byteLess rawvalue192 rawvalue84 = true := by
  simp only [rawvalue192,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value192_value85 : byteLess rawvalue192 rawvalue85 = true := by
  simp only [rawvalue192,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value192_value88 : byteLess rawvalue192 rawvalue88 = true := by
  simp only [rawvalue192,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value192_value89 : byteLess rawvalue192 rawvalue89 = true := by
  simp only [rawvalue192,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value192_value90 : byteLess rawvalue192 rawvalue90 = true := by
  simp only [rawvalue192,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value193 : nodes value193 = 1680 := by
  change 1 + (nodes value192 + (nodes value75 + (nodes value76 + (nodes value77 + (nodes value79 + (nodes value80 + (nodes value81 + (nodes value83 + (nodes value84 + (nodes value85 + (nodes value88 + (nodes value89 + (nodes value90 + 0))))))))))))) = 1680
  simp only [nodes_value192,nodes_value75,nodes_value76,nodes_value77,nodes_value79,nodes_value80,nodes_value81,nodes_value83,nodes_value84,nodes_value85,nodes_value88,nodes_value89,nodes_value90]
  all_goals decide +kernel
theorem depth_value193 : depth value193 = 10 := by
  change max (1 + depth value192) (max (1 + depth value75) (max (1 + depth value76) (max (1 + depth value77) (max (1 + depth value79) (max (1 + depth value80) (max (1 + depth value81) (max (1 + depth value83) (max (1 + depth value84) (max (1 + depth value85) (max (1 + depth value88) (max (1 + depth value89) (max (1 + depth value90) (0))))))))))))) = 10
  simp only [depth_value192,depth_value75,depth_value76,depth_value77,depth_value79,depth_value80,depth_value81,depth_value83,depth_value84,depth_value85,depth_value88,depth_value89,depth_value90]
  all_goals decide +kernel
theorem canonical_value193 : canonical models value193 = true := by
  change ((canonical models value192 && (canonical models value75 && (canonical models value76 && (canonical models value77 && (canonical models value79 && (canonical models value80 && (canonical models value81 && (canonical models value83 && (canonical models value84 && (canonical models value85 && (canonical models value88 && (canonical models value89 && (canonical models value90 && true))))))))))))) && ordered [encode value192,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90]) = true
  simp only [canonical_value192,canonical_value75,canonical_value76,canonical_value77,canonical_value79,canonical_value80,canonical_value81,canonical_value83,canonical_value84,canonical_value85,canonical_value88,canonical_value89,canonical_value90,encoded_value192,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  simp only [ordered,List.all_cons,List.all_nil,order_value192_value75,order_value192_value76,order_value192_value77,order_value192_value79,order_value192_value80,order_value192_value81,order_value192_value83,order_value192_value84,order_value192_value85,order_value192_value88,order_value192_value89,order_value192_value90,order_value75_value76,order_value75_value77,order_value75_value79,order_value75_value80,order_value75_value81,order_value75_value83,order_value75_value84,order_value75_value85,order_value75_value88,order_value75_value89,order_value75_value90,order_value76_value77,order_value76_value79,order_value76_value80,order_value76_value81,order_value76_value83,order_value76_value84,order_value76_value85,order_value76_value88,order_value76_value89,order_value76_value90,order_value77_value79,order_value77_value80,order_value77_value81,order_value77_value83,order_value77_value84,order_value77_value85,order_value77_value88,order_value77_value89,order_value77_value90,order_value79_value80,order_value79_value81,order_value79_value83,order_value79_value84,order_value79_value85,order_value79_value88,order_value79_value89,order_value79_value90,order_value80_value81,order_value80_value83,order_value80_value84,order_value80_value85,order_value80_value88,order_value80_value89,order_value80_value90,order_value81_value83,order_value81_value84,order_value81_value85,order_value81_value88,order_value81_value89,order_value81_value90,order_value83_value84,order_value83_value85,order_value83_value88,order_value83_value89,order_value83_value90,order_value84_value85,order_value84_value88,order_value84_value89,order_value84_value90,order_value85_value88,order_value85_value89,order_value85_value90,order_value88_value89,order_value88_value90,order_value89_value90,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value193 : rawvalue193.length = 28508 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value192 (commaConsLength rawLength_value75 (commaConsLength rawLength_value76 (commaConsLength rawLength_value77 (commaConsLength rawLength_value79 (commaConsLength rawLength_value80 (commaConsLength rawLength_value81 (commaConsLength rawLength_value83 (commaConsLength rawLength_value84 (commaConsLength rawLength_value85 (commaConsLength rawLength_value88 (commaConsLength rawLength_value89 (commaSingletonLength rawLength_value90)))))))))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value194 : Value := .function (.cons value2 value173 (.cons value45 value37 .nil))
noncomputable def rawvalue194 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue173 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue37 ++ [93])] ++ [93,93]
theorem encoded_value194 : encode value194 = rawvalue194 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value173 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value37 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value173,encoded_value45,encoded_value37]
  all_goals rfl
theorem nodes_value194 : nodes value194 = 627 := by
  change 1 + (nodes value2 + nodes value173 + (nodes value45 + nodes value37 + 0)) = 627
  simp only [nodes_value2,nodes_value173,nodes_value45,nodes_value37]
  all_goals decide +kernel
theorem depth_value194 : depth value194 = 9 := by
  change max (max (1 + depth value2) (1 + depth value173)) (max (max (1 + depth value45) (1 + depth value37)) (0)) = 9
  simp only [depth_value2,depth_value173,depth_value45,depth_value37]
  all_goals decide +kernel
theorem canonical_value194 : canonical models value194 = true := by
  change ((canonical models value2 && canonical models value173 && (canonical models value45 && canonical models value37 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value173,canonical_value45,canonical_value37,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value194 : rawvalue194.length = 10564 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value173) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value37) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value195 : Value := .set (.cons value194 .nil)
noncomputable def rawvalue195 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue194] ++ [93,93]
theorem encoded_value195 : encode value195 = rawvalue195 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value194] ++ [93,93] = _
  simp only [encoded_value194]
  all_goals rfl
theorem nodes_value195 : nodes value195 = 628 := by
  change 1 + (nodes value194 + 0) = 628
  simp only [nodes_value194]
  all_goals decide +kernel
theorem depth_value195 : depth value195 = 10 := by
  change max (1 + depth value194) (0) = 10
  simp only [depth_value194]
  all_goals decide +kernel
theorem canonical_value195 : canonical models value195 = true := by
  change ((canonical models value194 && true) && ordered [encode value194]) = true
  simp only [canonical_value194,encoded_value194]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value195 : rawvalue195.length = 10574 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value194)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value196 : Value := .integer (19)
noncomputable def rawvalue196 : Bytes := asciiBytes "[\"int\",\"19\"]"
theorem encoded_value196 : encode value196 = rawvalue196 := by
  all_goals rfl
theorem nodes_value196 : nodes value196 = 1 := by rfl
theorem depth_value196 : depth value196 = 0 := by rfl
theorem canonical_value196 : canonical models value196 = true := by decide +kernel
theorem rawLength_value196 : rawvalue196.length = 12 := by
  decide +kernel
noncomputable def value197 : Value := .function (.cons value37 value188 (.cons value38 value188 (.cons value39 value70 (.cons value43 value64 .nil))))
noncomputable def rawvalue197 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue37 ++ [44] ++ rawvalue188 ++ [93]),([91] ++ rawvalue38 ++ [44] ++ rawvalue188 ++ [93]),([91] ++ rawvalue39 ++ [44] ++ rawvalue70 ++ [93]),([91] ++ rawvalue43 ++ [44] ++ rawvalue64 ++ [93])] ++ [93,93]
theorem encoded_value197 : encode value197 = rawvalue197 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value37 ++ [44] ++ encode value188 ++ [93]),([91] ++ encode value38 ++ [44] ++ encode value188 ++ [93]),([91] ++ encode value39 ++ [44] ++ encode value70 ++ [93]),([91] ++ encode value43 ++ [44] ++ encode value64 ++ [93])] ++ [93,93] = _
  simp only [encoded_value37,encoded_value188,encoded_value38,encoded_value39,encoded_value70,encoded_value43,encoded_value64]
  all_goals rfl
theorem nodes_value197 : nodes value197 = 9 := by
  change 1 + (nodes value37 + nodes value188 + (nodes value38 + nodes value188 + (nodes value39 + nodes value70 + (nodes value43 + nodes value64 + 0)))) = 9
  simp only [nodes_value37,nodes_value188,nodes_value38,nodes_value39,nodes_value70,nodes_value43,nodes_value64]
  all_goals decide +kernel
theorem depth_value197 : depth value197 = 1 := by
  change max (max (1 + depth value37) (1 + depth value188)) (max (max (1 + depth value38) (1 + depth value188)) (max (max (1 + depth value39) (1 + depth value70)) (max (max (1 + depth value43) (1 + depth value64)) (0)))) = 1
  simp only [depth_value37,depth_value188,depth_value38,depth_value39,depth_value70,depth_value43,depth_value64]
  all_goals decide +kernel
theorem canonical_value197 : canonical models value197 = true := by
  change ((canonical models value37 && canonical models value188 && (canonical models value38 && canonical models value188 && (canonical models value39 && canonical models value70 && (canonical models value43 && canonical models value64 && true)))) && ordered [encode value37,encode value38,encode value39,encode value43]) = true
  simp only [canonical_value37,canonical_value188,canonical_value38,canonical_value39,canonical_value70,canonical_value43,canonical_value64,encoded_value37,encoded_value38,encoded_value39,encoded_value43]
  simp only [ordered,List.all_cons,List.all_nil,order_value37_value38,order_value37_value39,order_value37_value43,order_value38_value39,order_value38_value43,order_value39_value43,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value197 : rawvalue197.length = 125 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value37) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value188) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value38) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value188) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value39) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value70) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value43) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value64) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value198 : Value := .function (.cons value2 value173 (.cons value72 value190 (.cons value73 value191 (.cons value45 value38 .nil))))
noncomputable def rawvalue198 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue173 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue190 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue191 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue38 ++ [93])] ++ [93,93]
theorem encoded_value198 : encode value198 = rawvalue198 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value173 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value190 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value191 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value38 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value173,encoded_value72,encoded_value190,encoded_value73,encoded_value191,encoded_value45,encoded_value38]
  all_goals rfl
theorem nodes_value198 : nodes value198 = 635 := by
  change 1 + (nodes value2 + nodes value173 + (nodes value72 + nodes value190 + (nodes value73 + nodes value191 + (nodes value45 + nodes value38 + 0)))) = 635
  simp only [nodes_value2,nodes_value173,nodes_value72,nodes_value190,nodes_value73,nodes_value191,nodes_value45,nodes_value38]
  all_goals decide +kernel
theorem depth_value198 : depth value198 = 9 := by
  change max (max (1 + depth value2) (1 + depth value173)) (max (max (1 + depth value72) (1 + depth value190)) (max (max (1 + depth value73) (1 + depth value191)) (max (max (1 + depth value45) (1 + depth value38)) (0)))) = 9
  simp only [depth_value2,depth_value173,depth_value72,depth_value190,depth_value73,depth_value191,depth_value45,depth_value38]
  all_goals decide +kernel
theorem canonical_value198 : canonical models value198 = true := by
  change ((canonical models value2 && canonical models value173 && (canonical models value72 && canonical models value190 && (canonical models value73 && canonical models value191 && (canonical models value45 && canonical models value38 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value173,canonical_value72,canonical_value190,canonical_value73,canonical_value191,canonical_value45,canonical_value38,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value198 : rawvalue198.length = 10702 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value173) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value190) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value191) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value38) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value199 : Value := .set (.cons value192 (.cons value198 (.cons value75 (.cons value76 (.cons value77 (.cons value79 (.cons value80 (.cons value81 (.cons value83 (.cons value84 (.cons value85 (.cons value88 (.cons value89 (.cons value90 .nil))))))))))))))
noncomputable def rawvalue199 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue192,rawvalue198,rawvalue75,rawvalue76,rawvalue77,rawvalue79,rawvalue80,rawvalue81,rawvalue83,rawvalue84,rawvalue85,rawvalue88,rawvalue89,rawvalue90] ++ [93,93]
theorem encoded_value199 : encode value199 = rawvalue199 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value192,encode value198,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90] ++ [93,93] = _
  simp only [encoded_value192,encoded_value198,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  all_goals rfl
theorem order_value192_value198 : byteLess rawvalue192 rawvalue198 = true := by
  simp only [rawvalue192,rawvalue198,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue38,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value75 : byteLess rawvalue198 rawvalue75 = true := by
  simp only [rawvalue198,rawvalue75,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value76 : byteLess rawvalue198 rawvalue76 = true := by
  simp only [rawvalue198,rawvalue76,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value77 : byteLess rawvalue198 rawvalue77 = true := by
  simp only [rawvalue198,rawvalue77,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value79 : byteLess rawvalue198 rawvalue79 = true := by
  simp only [rawvalue198,rawvalue79,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value80 : byteLess rawvalue198 rawvalue80 = true := by
  simp only [rawvalue198,rawvalue80,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value81 : byteLess rawvalue198 rawvalue81 = true := by
  simp only [rawvalue198,rawvalue81,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value83 : byteLess rawvalue198 rawvalue83 = true := by
  simp only [rawvalue198,rawvalue83,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value84 : byteLess rawvalue198 rawvalue84 = true := by
  simp only [rawvalue198,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value85 : byteLess rawvalue198 rawvalue85 = true := by
  simp only [rawvalue198,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value88 : byteLess rawvalue198 rawvalue88 = true := by
  simp only [rawvalue198,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value89 : byteLess rawvalue198 rawvalue89 = true := by
  simp only [rawvalue198,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value90 : byteLess rawvalue198 rawvalue90 = true := by
  simp only [rawvalue198,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value199 : nodes value199 = 2315 := by
  change 1 + (nodes value192 + (nodes value198 + (nodes value75 + (nodes value76 + (nodes value77 + (nodes value79 + (nodes value80 + (nodes value81 + (nodes value83 + (nodes value84 + (nodes value85 + (nodes value88 + (nodes value89 + (nodes value90 + 0)))))))))))))) = 2315
  simp only [nodes_value192,nodes_value198,nodes_value75,nodes_value76,nodes_value77,nodes_value79,nodes_value80,nodes_value81,nodes_value83,nodes_value84,nodes_value85,nodes_value88,nodes_value89,nodes_value90]
  all_goals decide +kernel
theorem depth_value199 : depth value199 = 10 := by
  change max (1 + depth value192) (max (1 + depth value198) (max (1 + depth value75) (max (1 + depth value76) (max (1 + depth value77) (max (1 + depth value79) (max (1 + depth value80) (max (1 + depth value81) (max (1 + depth value83) (max (1 + depth value84) (max (1 + depth value85) (max (1 + depth value88) (max (1 + depth value89) (max (1 + depth value90) (0)))))))))))))) = 10
  simp only [depth_value192,depth_value198,depth_value75,depth_value76,depth_value77,depth_value79,depth_value80,depth_value81,depth_value83,depth_value84,depth_value85,depth_value88,depth_value89,depth_value90]
  all_goals decide +kernel
theorem canonical_value199 : canonical models value199 = true := by
  change ((canonical models value192 && (canonical models value198 && (canonical models value75 && (canonical models value76 && (canonical models value77 && (canonical models value79 && (canonical models value80 && (canonical models value81 && (canonical models value83 && (canonical models value84 && (canonical models value85 && (canonical models value88 && (canonical models value89 && (canonical models value90 && true)))))))))))))) && ordered [encode value192,encode value198,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90]) = true
  simp only [canonical_value192,canonical_value198,canonical_value75,canonical_value76,canonical_value77,canonical_value79,canonical_value80,canonical_value81,canonical_value83,canonical_value84,canonical_value85,canonical_value88,canonical_value89,canonical_value90,encoded_value192,encoded_value198,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  simp only [ordered,List.all_cons,List.all_nil,order_value192_value198,order_value192_value75,order_value192_value76,order_value192_value77,order_value192_value79,order_value192_value80,order_value192_value81,order_value192_value83,order_value192_value84,order_value192_value85,order_value192_value88,order_value192_value89,order_value192_value90,order_value198_value75,order_value198_value76,order_value198_value77,order_value198_value79,order_value198_value80,order_value198_value81,order_value198_value83,order_value198_value84,order_value198_value85,order_value198_value88,order_value198_value89,order_value198_value90,order_value75_value76,order_value75_value77,order_value75_value79,order_value75_value80,order_value75_value81,order_value75_value83,order_value75_value84,order_value75_value85,order_value75_value88,order_value75_value89,order_value75_value90,order_value76_value77,order_value76_value79,order_value76_value80,order_value76_value81,order_value76_value83,order_value76_value84,order_value76_value85,order_value76_value88,order_value76_value89,order_value76_value90,order_value77_value79,order_value77_value80,order_value77_value81,order_value77_value83,order_value77_value84,order_value77_value85,order_value77_value88,order_value77_value89,order_value77_value90,order_value79_value80,order_value79_value81,order_value79_value83,order_value79_value84,order_value79_value85,order_value79_value88,order_value79_value89,order_value79_value90,order_value80_value81,order_value80_value83,order_value80_value84,order_value80_value85,order_value80_value88,order_value80_value89,order_value80_value90,order_value81_value83,order_value81_value84,order_value81_value85,order_value81_value88,order_value81_value89,order_value81_value90,order_value83_value84,order_value83_value85,order_value83_value88,order_value83_value89,order_value83_value90,order_value84_value85,order_value84_value88,order_value84_value89,order_value84_value90,order_value85_value88,order_value85_value89,order_value85_value90,order_value88_value89,order_value88_value90,order_value89_value90,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value199 : rawvalue199.length = 39211 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value192 (commaConsLength rawLength_value198 (commaConsLength rawLength_value75 (commaConsLength rawLength_value76 (commaConsLength rawLength_value77 (commaConsLength rawLength_value79 (commaConsLength rawLength_value80 (commaConsLength rawLength_value81 (commaConsLength rawLength_value83 (commaConsLength rawLength_value84 (commaConsLength rawLength_value85 (commaConsLength rawLength_value88 (commaConsLength rawLength_value89 (commaSingletonLength rawLength_value90))))))))))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value200 : Value := .function (.cons value2 value173 (.cons value45 value38 .nil))
noncomputable def rawvalue200 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue173 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue38 ++ [93])] ++ [93,93]
theorem encoded_value200 : encode value200 = rawvalue200 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value173 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value38 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value173,encoded_value45,encoded_value38]
  all_goals rfl
theorem nodes_value200 : nodes value200 = 627 := by
  change 1 + (nodes value2 + nodes value173 + (nodes value45 + nodes value38 + 0)) = 627
  simp only [nodes_value2,nodes_value173,nodes_value45,nodes_value38]
  all_goals decide +kernel
theorem depth_value200 : depth value200 = 9 := by
  change max (max (1 + depth value2) (1 + depth value173)) (max (max (1 + depth value45) (1 + depth value38)) (0)) = 9
  simp only [depth_value2,depth_value173,depth_value45,depth_value38]
  all_goals decide +kernel
theorem canonical_value200 : canonical models value200 = true := by
  change ((canonical models value2 && canonical models value173 && (canonical models value45 && canonical models value38 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value173,canonical_value45,canonical_value38,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value200 : rawvalue200.length = 10564 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value173) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value38) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value201 : Value := .set (.cons value194 (.cons value200 .nil))
noncomputable def rawvalue201 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue194,rawvalue200] ++ [93,93]
theorem encoded_value201 : encode value201 = rawvalue201 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value194,encode value200] ++ [93,93] = _
  simp only [encoded_value194,encoded_value200]
  all_goals rfl
theorem order_value194_value200 : byteLess rawvalue194 rawvalue200 = true := by
  simp only [rawvalue194,rawvalue200,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue38,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value201 : nodes value201 = 1255 := by
  change 1 + (nodes value194 + (nodes value200 + 0)) = 1255
  simp only [nodes_value194,nodes_value200]
  all_goals decide +kernel
theorem depth_value201 : depth value201 = 10 := by
  change max (1 + depth value194) (max (1 + depth value200) (0)) = 10
  simp only [depth_value194,depth_value200]
  all_goals decide +kernel
theorem canonical_value201 : canonical models value201 = true := by
  change ((canonical models value194 && (canonical models value200 && true)) && ordered [encode value194,encode value200]) = true
  simp only [canonical_value194,canonical_value200,encoded_value194,encoded_value200]
  simp only [ordered,List.all_cons,List.all_nil,order_value194_value200,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value201 : rawvalue201.length = 21139 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value194 (commaSingletonLength rawLength_value200))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value202 : Value := .function (.cons value37 value188 (.cons value38 value188 (.cons value39 value188 (.cons value43 value64 .nil))))
noncomputable def rawvalue202 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue37 ++ [44] ++ rawvalue188 ++ [93]),([91] ++ rawvalue38 ++ [44] ++ rawvalue188 ++ [93]),([91] ++ rawvalue39 ++ [44] ++ rawvalue188 ++ [93]),([91] ++ rawvalue43 ++ [44] ++ rawvalue64 ++ [93])] ++ [93,93]
theorem encoded_value202 : encode value202 = rawvalue202 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value37 ++ [44] ++ encode value188 ++ [93]),([91] ++ encode value38 ++ [44] ++ encode value188 ++ [93]),([91] ++ encode value39 ++ [44] ++ encode value188 ++ [93]),([91] ++ encode value43 ++ [44] ++ encode value64 ++ [93])] ++ [93,93] = _
  simp only [encoded_value37,encoded_value188,encoded_value38,encoded_value39,encoded_value43,encoded_value64]
  all_goals rfl
theorem nodes_value202 : nodes value202 = 9 := by
  change 1 + (nodes value37 + nodes value188 + (nodes value38 + nodes value188 + (nodes value39 + nodes value188 + (nodes value43 + nodes value64 + 0)))) = 9
  simp only [nodes_value37,nodes_value188,nodes_value38,nodes_value39,nodes_value43,nodes_value64]
  all_goals decide +kernel
theorem depth_value202 : depth value202 = 1 := by
  change max (max (1 + depth value37) (1 + depth value188)) (max (max (1 + depth value38) (1 + depth value188)) (max (max (1 + depth value39) (1 + depth value188)) (max (max (1 + depth value43) (1 + depth value64)) (0)))) = 1
  simp only [depth_value37,depth_value188,depth_value38,depth_value39,depth_value43,depth_value64]
  all_goals decide +kernel
theorem canonical_value202 : canonical models value202 = true := by
  change ((canonical models value37 && canonical models value188 && (canonical models value38 && canonical models value188 && (canonical models value39 && canonical models value188 && (canonical models value43 && canonical models value64 && true)))) && ordered [encode value37,encode value38,encode value39,encode value43]) = true
  simp only [canonical_value37,canonical_value188,canonical_value38,canonical_value39,canonical_value43,canonical_value64,encoded_value37,encoded_value38,encoded_value39,encoded_value43]
  simp only [ordered,List.all_cons,List.all_nil,order_value37_value38,order_value37_value39,order_value37_value43,order_value38_value39,order_value38_value43,order_value39_value43,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value202 : rawvalue202.length = 125 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value37) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value188) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value38) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value188) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value39) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value188) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value43) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value64) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value203 : Value := .function (.cons value2 value173 (.cons value72 value190 (.cons value73 value191 (.cons value45 value39 .nil))))
noncomputable def rawvalue203 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue173 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue190 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue191 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue39 ++ [93])] ++ [93,93]
theorem encoded_value203 : encode value203 = rawvalue203 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value173 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value190 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value191 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value39 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value173,encoded_value72,encoded_value190,encoded_value73,encoded_value191,encoded_value45,encoded_value39]
  all_goals rfl
theorem nodes_value203 : nodes value203 = 635 := by
  change 1 + (nodes value2 + nodes value173 + (nodes value72 + nodes value190 + (nodes value73 + nodes value191 + (nodes value45 + nodes value39 + 0)))) = 635
  simp only [nodes_value2,nodes_value173,nodes_value72,nodes_value190,nodes_value73,nodes_value191,nodes_value45,nodes_value39]
  all_goals decide +kernel
theorem depth_value203 : depth value203 = 9 := by
  change max (max (1 + depth value2) (1 + depth value173)) (max (max (1 + depth value72) (1 + depth value190)) (max (max (1 + depth value73) (1 + depth value191)) (max (max (1 + depth value45) (1 + depth value39)) (0)))) = 9
  simp only [depth_value2,depth_value173,depth_value72,depth_value190,depth_value73,depth_value191,depth_value45,depth_value39]
  all_goals decide +kernel
theorem canonical_value203 : canonical models value203 = true := by
  change ((canonical models value2 && canonical models value173 && (canonical models value72 && canonical models value190 && (canonical models value73 && canonical models value191 && (canonical models value45 && canonical models value39 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value173,canonical_value72,canonical_value190,canonical_value73,canonical_value191,canonical_value45,canonical_value39,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value203 : rawvalue203.length = 10702 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value173) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value190) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value191) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value39) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value204 : Value := .set (.cons value192 (.cons value198 (.cons value203 (.cons value75 (.cons value76 (.cons value77 (.cons value79 (.cons value80 (.cons value81 (.cons value83 (.cons value84 (.cons value85 (.cons value88 (.cons value89 (.cons value90 .nil)))))))))))))))
noncomputable def rawvalue204 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue192,rawvalue198,rawvalue203,rawvalue75,rawvalue76,rawvalue77,rawvalue79,rawvalue80,rawvalue81,rawvalue83,rawvalue84,rawvalue85,rawvalue88,rawvalue89,rawvalue90] ++ [93,93]
theorem encoded_value204 : encode value204 = rawvalue204 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value192,encode value198,encode value203,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90] ++ [93,93] = _
  simp only [encoded_value192,encoded_value198,encoded_value203,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  all_goals rfl
theorem order_value192_value203 : byteLess rawvalue192 rawvalue203 = true := by
  simp only [rawvalue192,rawvalue203,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value203 : byteLess rawvalue198 rawvalue203 = true := by
  simp only [rawvalue198,rawvalue203,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue38,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value203_value75 : byteLess rawvalue203 rawvalue75 = true := by
  simp only [rawvalue203,rawvalue75,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value203_value76 : byteLess rawvalue203 rawvalue76 = true := by
  simp only [rawvalue203,rawvalue76,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value203_value77 : byteLess rawvalue203 rawvalue77 = true := by
  simp only [rawvalue203,rawvalue77,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value203_value79 : byteLess rawvalue203 rawvalue79 = true := by
  simp only [rawvalue203,rawvalue79,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value203_value80 : byteLess rawvalue203 rawvalue80 = true := by
  simp only [rawvalue203,rawvalue80,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value203_value81 : byteLess rawvalue203 rawvalue81 = true := by
  simp only [rawvalue203,rawvalue81,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value203_value83 : byteLess rawvalue203 rawvalue83 = true := by
  simp only [rawvalue203,rawvalue83,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value203_value84 : byteLess rawvalue203 rawvalue84 = true := by
  simp only [rawvalue203,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value203_value85 : byteLess rawvalue203 rawvalue85 = true := by
  simp only [rawvalue203,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value203_value88 : byteLess rawvalue203 rawvalue88 = true := by
  simp only [rawvalue203,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value203_value89 : byteLess rawvalue203 rawvalue89 = true := by
  simp only [rawvalue203,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value203_value90 : byteLess rawvalue203 rawvalue90 = true := by
  simp only [rawvalue203,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value204 : nodes value204 = 2950 := by
  change 1 + (nodes value192 + (nodes value198 + (nodes value203 + (nodes value75 + (nodes value76 + (nodes value77 + (nodes value79 + (nodes value80 + (nodes value81 + (nodes value83 + (nodes value84 + (nodes value85 + (nodes value88 + (nodes value89 + (nodes value90 + 0))))))))))))))) = 2950
  simp only [nodes_value192,nodes_value198,nodes_value203,nodes_value75,nodes_value76,nodes_value77,nodes_value79,nodes_value80,nodes_value81,nodes_value83,nodes_value84,nodes_value85,nodes_value88,nodes_value89,nodes_value90]
  all_goals decide +kernel
theorem depth_value204 : depth value204 = 10 := by
  change max (1 + depth value192) (max (1 + depth value198) (max (1 + depth value203) (max (1 + depth value75) (max (1 + depth value76) (max (1 + depth value77) (max (1 + depth value79) (max (1 + depth value80) (max (1 + depth value81) (max (1 + depth value83) (max (1 + depth value84) (max (1 + depth value85) (max (1 + depth value88) (max (1 + depth value89) (max (1 + depth value90) (0))))))))))))))) = 10
  simp only [depth_value192,depth_value198,depth_value203,depth_value75,depth_value76,depth_value77,depth_value79,depth_value80,depth_value81,depth_value83,depth_value84,depth_value85,depth_value88,depth_value89,depth_value90]
  all_goals decide +kernel
theorem canonical_value204 : canonical models value204 = true := by
  change ((canonical models value192 && (canonical models value198 && (canonical models value203 && (canonical models value75 && (canonical models value76 && (canonical models value77 && (canonical models value79 && (canonical models value80 && (canonical models value81 && (canonical models value83 && (canonical models value84 && (canonical models value85 && (canonical models value88 && (canonical models value89 && (canonical models value90 && true))))))))))))))) && ordered [encode value192,encode value198,encode value203,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90]) = true
  simp only [canonical_value192,canonical_value198,canonical_value203,canonical_value75,canonical_value76,canonical_value77,canonical_value79,canonical_value80,canonical_value81,canonical_value83,canonical_value84,canonical_value85,canonical_value88,canonical_value89,canonical_value90,encoded_value192,encoded_value198,encoded_value203,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  simp only [ordered,List.all_cons,List.all_nil,order_value192_value198,order_value192_value203,order_value192_value75,order_value192_value76,order_value192_value77,order_value192_value79,order_value192_value80,order_value192_value81,order_value192_value83,order_value192_value84,order_value192_value85,order_value192_value88,order_value192_value89,order_value192_value90,order_value198_value203,order_value198_value75,order_value198_value76,order_value198_value77,order_value198_value79,order_value198_value80,order_value198_value81,order_value198_value83,order_value198_value84,order_value198_value85,order_value198_value88,order_value198_value89,order_value198_value90,order_value203_value75,order_value203_value76,order_value203_value77,order_value203_value79,order_value203_value80,order_value203_value81,order_value203_value83,order_value203_value84,order_value203_value85,order_value203_value88,order_value203_value89,order_value203_value90,order_value75_value76,order_value75_value77,order_value75_value79,order_value75_value80,order_value75_value81,order_value75_value83,order_value75_value84,order_value75_value85,order_value75_value88,order_value75_value89,order_value75_value90,order_value76_value77,order_value76_value79,order_value76_value80,order_value76_value81,order_value76_value83,order_value76_value84,order_value76_value85,order_value76_value88,order_value76_value89,order_value76_value90,order_value77_value79,order_value77_value80,order_value77_value81,order_value77_value83,order_value77_value84,order_value77_value85,order_value77_value88,order_value77_value89,order_value77_value90,order_value79_value80,order_value79_value81,order_value79_value83,order_value79_value84,order_value79_value85,order_value79_value88,order_value79_value89,order_value79_value90,order_value80_value81,order_value80_value83,order_value80_value84,order_value80_value85,order_value80_value88,order_value80_value89,order_value80_value90,order_value81_value83,order_value81_value84,order_value81_value85,order_value81_value88,order_value81_value89,order_value81_value90,order_value83_value84,order_value83_value85,order_value83_value88,order_value83_value89,order_value83_value90,order_value84_value85,order_value84_value88,order_value84_value89,order_value84_value90,order_value85_value88,order_value85_value89,order_value85_value90,order_value88_value89,order_value88_value90,order_value89_value90,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value204 : rawvalue204.length = 49914 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value192 (commaConsLength rawLength_value198 (commaConsLength rawLength_value203 (commaConsLength rawLength_value75 (commaConsLength rawLength_value76 (commaConsLength rawLength_value77 (commaConsLength rawLength_value79 (commaConsLength rawLength_value80 (commaConsLength rawLength_value81 (commaConsLength rawLength_value83 (commaConsLength rawLength_value84 (commaConsLength rawLength_value85 (commaConsLength rawLength_value88 (commaConsLength rawLength_value89 (commaSingletonLength rawLength_value90)))))))))))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value205 : Value := .function (.cons value2 value173 (.cons value45 value39 .nil))
noncomputable def rawvalue205 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue173 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue39 ++ [93])] ++ [93,93]
theorem encoded_value205 : encode value205 = rawvalue205 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value173 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value39 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value173,encoded_value45,encoded_value39]
  all_goals rfl
theorem nodes_value205 : nodes value205 = 627 := by
  change 1 + (nodes value2 + nodes value173 + (nodes value45 + nodes value39 + 0)) = 627
  simp only [nodes_value2,nodes_value173,nodes_value45,nodes_value39]
  all_goals decide +kernel
theorem depth_value205 : depth value205 = 9 := by
  change max (max (1 + depth value2) (1 + depth value173)) (max (max (1 + depth value45) (1 + depth value39)) (0)) = 9
  simp only [depth_value2,depth_value173,depth_value45,depth_value39]
  all_goals decide +kernel
theorem canonical_value205 : canonical models value205 = true := by
  change ((canonical models value2 && canonical models value173 && (canonical models value45 && canonical models value39 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value173,canonical_value45,canonical_value39,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value205 : rawvalue205.length = 10564 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value173) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value39) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value206 : Value := .set (.cons value194 (.cons value200 (.cons value205 .nil)))
noncomputable def rawvalue206 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue194,rawvalue200,rawvalue205] ++ [93,93]
theorem encoded_value206 : encode value206 = rawvalue206 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value194,encode value200,encode value205] ++ [93,93] = _
  simp only [encoded_value194,encoded_value200,encoded_value205]
  all_goals rfl
theorem order_value194_value205 : byteLess rawvalue194 rawvalue205 = true := by
  simp only [rawvalue194,rawvalue205,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value200_value205 : byteLess rawvalue200 rawvalue205 = true := by
  simp only [rawvalue200,rawvalue205,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue38,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value206 : nodes value206 = 1882 := by
  change 1 + (nodes value194 + (nodes value200 + (nodes value205 + 0))) = 1882
  simp only [nodes_value194,nodes_value200,nodes_value205]
  all_goals decide +kernel
theorem depth_value206 : depth value206 = 10 := by
  change max (1 + depth value194) (max (1 + depth value200) (max (1 + depth value205) (0))) = 10
  simp only [depth_value194,depth_value200,depth_value205]
  all_goals decide +kernel
theorem canonical_value206 : canonical models value206 = true := by
  change ((canonical models value194 && (canonical models value200 && (canonical models value205 && true))) && ordered [encode value194,encode value200,encode value205]) = true
  simp only [canonical_value194,canonical_value200,canonical_value205,encoded_value194,encoded_value200,encoded_value205]
  simp only [ordered,List.all_cons,List.all_nil,order_value194_value200,order_value194_value205,order_value200_value205,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value206 : rawvalue206.length = 31704 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value194 (commaConsLength rawLength_value200 (commaSingletonLength rawLength_value205)))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value207 : Value := .integer (22)
noncomputable def rawvalue207 : Bytes := asciiBytes "[\"int\",\"22\"]"
theorem encoded_value207 : encode value207 = rawvalue207 := by
  all_goals rfl
theorem nodes_value207 : nodes value207 = 1 := by rfl
theorem depth_value207 : depth value207 = 0 := by rfl
theorem canonical_value207 : canonical models value207 = true := by decide +kernel
theorem rawLength_value207 : rawvalue207.length = 12 := by
  decide +kernel
noncomputable def value208 : Value := .function (.cons value2 value173 (.cons value36 value40 .nil))
noncomputable def rawvalue208 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue173 ++ [93]),([91] ++ rawvalue36 ++ [44] ++ rawvalue40 ++ [93])] ++ [93,93]
theorem encoded_value208 : encode value208 = rawvalue208 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value173 ++ [93]),([91] ++ encode value36 ++ [44] ++ encode value40 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value173,encoded_value36,encoded_value40]
  all_goals rfl
theorem nodes_value208 : nodes value208 = 630 := by
  change 1 + (nodes value2 + nodes value173 + (nodes value36 + nodes value40 + 0)) = 630
  simp only [nodes_value2,nodes_value173,nodes_value36,nodes_value40]
  all_goals decide +kernel
theorem depth_value208 : depth value208 = 9 := by
  change max (max (1 + depth value2) (1 + depth value173)) (max (max (1 + depth value36) (1 + depth value40)) (0)) = 9
  simp only [depth_value2,depth_value173,depth_value36,depth_value40]
  all_goals decide +kernel
theorem canonical_value208 : canonical models value208 = true := by
  change ((canonical models value2 && canonical models value173 && (canonical models value36 && canonical models value40 && true)) && ordered [encode value2,encode value36]) = true
  simp only [canonical_value2,canonical_value173,canonical_value36,canonical_value40,encoded_value2,encoded_value36]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value36,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value208 : rawvalue208.length = 10602 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value173) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value36) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value40) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value209 : Value := .set (.cons value208 .nil)
noncomputable def rawvalue209 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue208] ++ [93,93]
theorem encoded_value209 : encode value209 = rawvalue209 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value208] ++ [93,93] = _
  simp only [encoded_value208]
  all_goals rfl
theorem nodes_value209 : nodes value209 = 631 := by
  change 1 + (nodes value208 + 0) = 631
  simp only [nodes_value208]
  all_goals decide +kernel
theorem depth_value209 : depth value209 = 10 := by
  change max (1 + depth value208) (0) = 10
  simp only [depth_value208]
  all_goals decide +kernel
theorem canonical_value209 : canonical models value209 = true := by
  change ((canonical models value208 && true) && ordered [encode value208]) = true
  simp only [canonical_value208,encoded_value208]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value209 : rawvalue209.length = 10612 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value208)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value210 : Value := .function (.cons value109 value35 (.cons value110 value111 (.cons value112 value169 (.cons value170 value171 (.cons value3 value4 (.cons value14 value15 (.cons value172 value120 (.cons value5 value34 (.cons value6 value25 (.cons value167 value69 (.cons value19 value24 (.cons value161 value162 (.cons value30 value33 (.cons value50 value55 (.cons value31 value137 .nil)))))))))))))))
noncomputable def rawvalue210 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue109 ++ [44] ++ rawvalue35 ++ [93]),([91] ++ rawvalue110 ++ [44] ++ rawvalue111 ++ [93]),([91] ++ rawvalue112 ++ [44] ++ rawvalue169 ++ [93]),([91] ++ rawvalue170 ++ [44] ++ rawvalue171 ++ [93]),([91] ++ rawvalue3 ++ [44] ++ rawvalue4 ++ [93]),([91] ++ rawvalue14 ++ [44] ++ rawvalue15 ++ [93]),([91] ++ rawvalue172 ++ [44] ++ rawvalue120 ++ [93]),([91] ++ rawvalue5 ++ [44] ++ rawvalue34 ++ [93]),([91] ++ rawvalue6 ++ [44] ++ rawvalue25 ++ [93]),([91] ++ rawvalue167 ++ [44] ++ rawvalue69 ++ [93]),([91] ++ rawvalue19 ++ [44] ++ rawvalue24 ++ [93]),([91] ++ rawvalue161 ++ [44] ++ rawvalue162 ++ [93]),([91] ++ rawvalue30 ++ [44] ++ rawvalue33 ++ [93]),([91] ++ rawvalue50 ++ [44] ++ rawvalue55 ++ [93]),([91] ++ rawvalue31 ++ [44] ++ rawvalue137 ++ [93])] ++ [93,93]
theorem encoded_value210 : encode value210 = rawvalue210 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value109 ++ [44] ++ encode value35 ++ [93]),([91] ++ encode value110 ++ [44] ++ encode value111 ++ [93]),([91] ++ encode value112 ++ [44] ++ encode value169 ++ [93]),([91] ++ encode value170 ++ [44] ++ encode value171 ++ [93]),([91] ++ encode value3 ++ [44] ++ encode value4 ++ [93]),([91] ++ encode value14 ++ [44] ++ encode value15 ++ [93]),([91] ++ encode value172 ++ [44] ++ encode value120 ++ [93]),([91] ++ encode value5 ++ [44] ++ encode value34 ++ [93]),([91] ++ encode value6 ++ [44] ++ encode value25 ++ [93]),([91] ++ encode value167 ++ [44] ++ encode value69 ++ [93]),([91] ++ encode value19 ++ [44] ++ encode value24 ++ [93]),([91] ++ encode value161 ++ [44] ++ encode value162 ++ [93]),([91] ++ encode value30 ++ [44] ++ encode value33 ++ [93]),([91] ++ encode value50 ++ [44] ++ encode value55 ++ [93]),([91] ++ encode value31 ++ [44] ++ encode value137 ++ [93])] ++ [93,93] = _
  simp only [encoded_value109,encoded_value35,encoded_value110,encoded_value111,encoded_value112,encoded_value169,encoded_value170,encoded_value171,encoded_value3,encoded_value4,encoded_value14,encoded_value15,encoded_value172,encoded_value120,encoded_value5,encoded_value34,encoded_value6,encoded_value25,encoded_value167,encoded_value69,encoded_value19,encoded_value24,encoded_value161,encoded_value162,encoded_value30,encoded_value33,encoded_value50,encoded_value55,encoded_value31,encoded_value137]
  all_goals rfl
theorem nodes_value210 : nodes value210 = 623 := by
  change 1 + (nodes value109 + nodes value35 + (nodes value110 + nodes value111 + (nodes value112 + nodes value169 + (nodes value170 + nodes value171 + (nodes value3 + nodes value4 + (nodes value14 + nodes value15 + (nodes value172 + nodes value120 + (nodes value5 + nodes value34 + (nodes value6 + nodes value25 + (nodes value167 + nodes value69 + (nodes value19 + nodes value24 + (nodes value161 + nodes value162 + (nodes value30 + nodes value33 + (nodes value50 + nodes value55 + (nodes value31 + nodes value137 + 0))))))))))))))) = 623
  simp only [nodes_value109,nodes_value35,nodes_value110,nodes_value111,nodes_value112,nodes_value169,nodes_value170,nodes_value171,nodes_value3,nodes_value4,nodes_value14,nodes_value15,nodes_value172,nodes_value120,nodes_value5,nodes_value34,nodes_value6,nodes_value25,nodes_value167,nodes_value69,nodes_value19,nodes_value24,nodes_value161,nodes_value162,nodes_value30,nodes_value33,nodes_value50,nodes_value55,nodes_value31,nodes_value137]
  all_goals decide +kernel
theorem depth_value210 : depth value210 = 8 := by
  change max (max (1 + depth value109) (1 + depth value35)) (max (max (1 + depth value110) (1 + depth value111)) (max (max (1 + depth value112) (1 + depth value169)) (max (max (1 + depth value170) (1 + depth value171)) (max (max (1 + depth value3) (1 + depth value4)) (max (max (1 + depth value14) (1 + depth value15)) (max (max (1 + depth value172) (1 + depth value120)) (max (max (1 + depth value5) (1 + depth value34)) (max (max (1 + depth value6) (1 + depth value25)) (max (max (1 + depth value167) (1 + depth value69)) (max (max (1 + depth value19) (1 + depth value24)) (max (max (1 + depth value161) (1 + depth value162)) (max (max (1 + depth value30) (1 + depth value33)) (max (max (1 + depth value50) (1 + depth value55)) (max (max (1 + depth value31) (1 + depth value137)) (0))))))))))))))) = 8
  simp only [depth_value109,depth_value35,depth_value110,depth_value111,depth_value112,depth_value169,depth_value170,depth_value171,depth_value3,depth_value4,depth_value14,depth_value15,depth_value172,depth_value120,depth_value5,depth_value34,depth_value6,depth_value25,depth_value167,depth_value69,depth_value19,depth_value24,depth_value161,depth_value162,depth_value30,depth_value33,depth_value50,depth_value55,depth_value31,depth_value137]
  all_goals decide +kernel
theorem canonical_value210 : canonical models value210 = true := by
  change ((canonical models value109 && canonical models value35 && (canonical models value110 && canonical models value111 && (canonical models value112 && canonical models value169 && (canonical models value170 && canonical models value171 && (canonical models value3 && canonical models value4 && (canonical models value14 && canonical models value15 && (canonical models value172 && canonical models value120 && (canonical models value5 && canonical models value34 && (canonical models value6 && canonical models value25 && (canonical models value167 && canonical models value69 && (canonical models value19 && canonical models value24 && (canonical models value161 && canonical models value162 && (canonical models value30 && canonical models value33 && (canonical models value50 && canonical models value55 && (canonical models value31 && canonical models value137 && true))))))))))))))) && ordered [encode value109,encode value110,encode value112,encode value170,encode value3,encode value14,encode value172,encode value5,encode value6,encode value167,encode value19,encode value161,encode value30,encode value50,encode value31]) = true
  simp only [canonical_value109,canonical_value35,canonical_value110,canonical_value111,canonical_value112,canonical_value169,canonical_value170,canonical_value171,canonical_value3,canonical_value4,canonical_value14,canonical_value15,canonical_value172,canonical_value120,canonical_value5,canonical_value34,canonical_value6,canonical_value25,canonical_value167,canonical_value69,canonical_value19,canonical_value24,canonical_value161,canonical_value162,canonical_value30,canonical_value33,canonical_value50,canonical_value55,canonical_value31,canonical_value137,encoded_value109,encoded_value110,encoded_value112,encoded_value170,encoded_value3,encoded_value14,encoded_value172,encoded_value5,encoded_value6,encoded_value167,encoded_value19,encoded_value161,encoded_value30,encoded_value50,encoded_value31]
  simp only [ordered,List.all_cons,List.all_nil,order_value109_value110,order_value109_value112,order_value109_value170,order_value109_value3,order_value109_value14,order_value109_value172,order_value109_value5,order_value109_value6,order_value109_value167,order_value109_value19,order_value109_value161,order_value109_value30,order_value109_value50,order_value109_value31,order_value110_value112,order_value110_value170,order_value110_value3,order_value110_value14,order_value110_value172,order_value110_value5,order_value110_value6,order_value110_value167,order_value110_value19,order_value110_value161,order_value110_value30,order_value110_value50,order_value110_value31,order_value112_value170,order_value112_value3,order_value112_value14,order_value112_value172,order_value112_value5,order_value112_value6,order_value112_value167,order_value112_value19,order_value112_value161,order_value112_value30,order_value112_value50,order_value112_value31,order_value170_value3,order_value170_value14,order_value170_value172,order_value170_value5,order_value170_value6,order_value170_value167,order_value170_value19,order_value170_value161,order_value170_value30,order_value170_value50,order_value170_value31,order_value3_value14,order_value3_value172,order_value3_value5,order_value3_value6,order_value3_value167,order_value3_value19,order_value3_value161,order_value3_value30,order_value3_value50,order_value3_value31,order_value14_value172,order_value14_value5,order_value14_value6,order_value14_value167,order_value14_value19,order_value14_value161,order_value14_value30,order_value14_value50,order_value14_value31,order_value172_value5,order_value172_value6,order_value172_value167,order_value172_value19,order_value172_value161,order_value172_value30,order_value172_value50,order_value172_value31,order_value5_value6,order_value5_value167,order_value5_value19,order_value5_value161,order_value5_value30,order_value5_value50,order_value5_value31,order_value6_value167,order_value6_value19,order_value6_value161,order_value6_value30,order_value6_value50,order_value6_value31,order_value167_value19,order_value167_value161,order_value167_value30,order_value167_value50,order_value167_value31,order_value19_value161,order_value19_value30,order_value19_value50,order_value19_value31,order_value161_value30,order_value161_value50,order_value161_value31,order_value30_value50,order_value30_value31,order_value50_value31,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value210 : rawvalue210.length = 10501 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value109) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value35) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value110) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value111) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value112) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value169) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value170) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value171) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value3) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value4) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value14) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value15) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value172) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value120) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value5) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value34) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value6) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value25) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value167) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value69) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value19) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value24) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value161) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value162) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value30) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value33) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value50) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value55) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value31) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value137) (show ([93] : Bytes).length = 1 from by decide +kernel)))))))))))))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value211 : Value := .set (.cons value173 (.cons value210 .nil))
noncomputable def rawvalue211 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue173,rawvalue210] ++ [93,93]
theorem encoded_value211 : encode value211 = rawvalue211 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value173,encode value210] ++ [93,93] = _
  simp only [encoded_value173,encoded_value210]
  all_goals rfl
theorem order_value173_value210 : byteLess rawvalue173 rawvalue210 = true := by
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value211 : nodes value211 = 1247 := by
  change 1 + (nodes value173 + (nodes value210 + 0)) = 1247
  simp only [nodes_value173,nodes_value210]
  all_goals decide +kernel
theorem depth_value211 : depth value211 = 9 := by
  change max (1 + depth value173) (max (1 + depth value210) (0)) = 9
  simp only [depth_value173,depth_value210]
  all_goals decide +kernel
theorem canonical_value211 : canonical models value211 = true := by
  change ((canonical models value173 && (canonical models value210 && true)) && ordered [encode value173,encode value210]) = true
  simp only [canonical_value173,canonical_value210,encoded_value173,encoded_value210]
  simp only [ordered,List.all_cons,List.all_nil,order_value173_value210,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value211 : rawvalue211.length = 21012 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value173 (commaSingletonLength rawLength_value210))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value212 : Value := .integer (6)
noncomputable def rawvalue212 : Bytes := asciiBytes "[\"int\",\"6\"]"
theorem encoded_value212 : encode value212 = rawvalue212 := by
  all_goals rfl
theorem nodes_value212 : nodes value212 = 1 := by rfl
theorem depth_value212 : depth value212 = 0 := by rfl
theorem canonical_value212 : canonical models value212 = true := by decide +kernel
theorem rawLength_value212 : rawvalue212.length = 11 := by
  decide +kernel
noncomputable def value213 : Value := .function (.cons value37 value212 (.cons value38 value188 (.cons value39 value188 (.cons value43 value64 .nil))))
noncomputable def rawvalue213 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue37 ++ [44] ++ rawvalue212 ++ [93]),([91] ++ rawvalue38 ++ [44] ++ rawvalue188 ++ [93]),([91] ++ rawvalue39 ++ [44] ++ rawvalue188 ++ [93]),([91] ++ rawvalue43 ++ [44] ++ rawvalue64 ++ [93])] ++ [93,93]
theorem encoded_value213 : encode value213 = rawvalue213 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value37 ++ [44] ++ encode value212 ++ [93]),([91] ++ encode value38 ++ [44] ++ encode value188 ++ [93]),([91] ++ encode value39 ++ [44] ++ encode value188 ++ [93]),([91] ++ encode value43 ++ [44] ++ encode value64 ++ [93])] ++ [93,93] = _
  simp only [encoded_value37,encoded_value212,encoded_value38,encoded_value188,encoded_value39,encoded_value43,encoded_value64]
  all_goals rfl
theorem nodes_value213 : nodes value213 = 9 := by
  change 1 + (nodes value37 + nodes value212 + (nodes value38 + nodes value188 + (nodes value39 + nodes value188 + (nodes value43 + nodes value64 + 0)))) = 9
  simp only [nodes_value37,nodes_value212,nodes_value38,nodes_value188,nodes_value39,nodes_value43,nodes_value64]
  all_goals decide +kernel
theorem depth_value213 : depth value213 = 1 := by
  change max (max (1 + depth value37) (1 + depth value212)) (max (max (1 + depth value38) (1 + depth value188)) (max (max (1 + depth value39) (1 + depth value188)) (max (max (1 + depth value43) (1 + depth value64)) (0)))) = 1
  simp only [depth_value37,depth_value212,depth_value38,depth_value188,depth_value39,depth_value43,depth_value64]
  all_goals decide +kernel
theorem canonical_value213 : canonical models value213 = true := by
  change ((canonical models value37 && canonical models value212 && (canonical models value38 && canonical models value188 && (canonical models value39 && canonical models value188 && (canonical models value43 && canonical models value64 && true)))) && ordered [encode value37,encode value38,encode value39,encode value43]) = true
  simp only [canonical_value37,canonical_value212,canonical_value38,canonical_value188,canonical_value39,canonical_value43,canonical_value64,encoded_value37,encoded_value38,encoded_value39,encoded_value43]
  simp only [ordered,List.all_cons,List.all_nil,order_value37_value38,order_value37_value39,order_value37_value43,order_value38_value39,order_value38_value43,order_value39_value43,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value213 : rawvalue213.length = 125 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value37) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value212) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value38) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value188) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value39) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value188) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value43) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value64) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value214 : Value := .function (.cons value172 value120 (.cons value50 value55 .nil))
noncomputable def rawvalue214 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue172 ++ [44] ++ rawvalue120 ++ [93]),([91] ++ rawvalue50 ++ [44] ++ rawvalue55 ++ [93])] ++ [93,93]
theorem encoded_value214 : encode value214 = rawvalue214 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value172 ++ [44] ++ encode value120 ++ [93]),([91] ++ encode value50 ++ [44] ++ encode value55 ++ [93])] ++ [93,93] = _
  simp only [encoded_value172,encoded_value120,encoded_value50,encoded_value55]
  all_goals rfl
theorem nodes_value214 : nodes value214 = 5 := by
  change 1 + (nodes value172 + nodes value120 + (nodes value50 + nodes value55 + 0)) = 5
  simp only [nodes_value172,nodes_value120,nodes_value50,nodes_value55]
  all_goals decide +kernel
theorem depth_value214 : depth value214 = 1 := by
  change max (max (1 + depth value172) (1 + depth value120)) (max (max (1 + depth value50) (1 + depth value55)) (0)) = 1
  simp only [depth_value172,depth_value120,depth_value50,depth_value55]
  all_goals decide +kernel
theorem canonical_value214 : canonical models value214 = true := by
  change ((canonical models value172 && canonical models value120 && (canonical models value50 && canonical models value55 && true)) && ordered [encode value172,encode value50]) = true
  simp only [canonical_value172,canonical_value120,canonical_value50,canonical_value55,encoded_value172,encoded_value50]
  simp only [ordered,List.all_cons,List.all_nil,order_value172_value50,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value214 : rawvalue214.length = 80 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value172) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value120) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value50) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value55) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value215 : Value := .function (.cons value2 value210 (.cons value72 value214 (.cons value73 value191 (.cons value45 value37 .nil))))
noncomputable def rawvalue215 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue210 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue214 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue191 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue37 ++ [93])] ++ [93,93]
theorem encoded_value215 : encode value215 = rawvalue215 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value210 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value214 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value191 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value37 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value210,encoded_value72,encoded_value214,encoded_value73,encoded_value191,encoded_value45,encoded_value37]
  all_goals rfl
theorem nodes_value215 : nodes value215 = 635 := by
  change 1 + (nodes value2 + nodes value210 + (nodes value72 + nodes value214 + (nodes value73 + nodes value191 + (nodes value45 + nodes value37 + 0)))) = 635
  simp only [nodes_value2,nodes_value210,nodes_value72,nodes_value214,nodes_value73,nodes_value191,nodes_value45,nodes_value37]
  all_goals decide +kernel
theorem depth_value215 : depth value215 = 9 := by
  change max (max (1 + depth value2) (1 + depth value210)) (max (max (1 + depth value72) (1 + depth value214)) (max (max (1 + depth value73) (1 + depth value191)) (max (max (1 + depth value45) (1 + depth value37)) (0)))) = 9
  simp only [depth_value2,depth_value210,depth_value72,depth_value214,depth_value73,depth_value191,depth_value45,depth_value37]
  all_goals decide +kernel
theorem canonical_value215 : canonical models value215 = true := by
  change ((canonical models value2 && canonical models value210 && (canonical models value72 && canonical models value214 && (canonical models value73 && canonical models value191 && (canonical models value45 && canonical models value37 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value210,canonical_value72,canonical_value214,canonical_value73,canonical_value191,canonical_value45,canonical_value37,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value215 : rawvalue215.length = 10703 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value210) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value214) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value191) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value37) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value216 : Value := .set (.cons value192 (.cons value198 (.cons value203 (.cons value215 (.cons value75 (.cons value76 (.cons value77 (.cons value79 (.cons value80 (.cons value81 (.cons value83 (.cons value84 (.cons value85 (.cons value88 (.cons value89 (.cons value90 .nil))))))))))))))))
noncomputable def rawvalue216 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue192,rawvalue198,rawvalue203,rawvalue215,rawvalue75,rawvalue76,rawvalue77,rawvalue79,rawvalue80,rawvalue81,rawvalue83,rawvalue84,rawvalue85,rawvalue88,rawvalue89,rawvalue90] ++ [93,93]
theorem encoded_value216 : encode value216 = rawvalue216 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value192,encode value198,encode value203,encode value215,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90] ++ [93,93] = _
  simp only [encoded_value192,encoded_value198,encoded_value203,encoded_value215,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  all_goals rfl
theorem order_value192_value215 : byteLess rawvalue192 rawvalue215 = true := by
  simp only [rawvalue192,rawvalue215,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value215 : byteLess rawvalue198 rawvalue215 = true := by
  simp only [rawvalue198,rawvalue215,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value203_value215 : byteLess rawvalue203 rawvalue215 = true := by
  simp only [rawvalue203,rawvalue215,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value215_value75 : byteLess rawvalue215 rawvalue75 = true := by
  simp only [rawvalue215,rawvalue75,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value215_value76 : byteLess rawvalue215 rawvalue76 = true := by
  simp only [rawvalue215,rawvalue76,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value215_value77 : byteLess rawvalue215 rawvalue77 = true := by
  simp only [rawvalue215,rawvalue77,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value215_value79 : byteLess rawvalue215 rawvalue79 = true := by
  simp only [rawvalue215,rawvalue79,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value215_value80 : byteLess rawvalue215 rawvalue80 = true := by
  simp only [rawvalue215,rawvalue80,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value215_value81 : byteLess rawvalue215 rawvalue81 = true := by
  simp only [rawvalue215,rawvalue81,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value215_value83 : byteLess rawvalue215 rawvalue83 = true := by
  simp only [rawvalue215,rawvalue83,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value215_value84 : byteLess rawvalue215 rawvalue84 = true := by
  simp only [rawvalue215,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value215_value85 : byteLess rawvalue215 rawvalue85 = true := by
  simp only [rawvalue215,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value215_value88 : byteLess rawvalue215 rawvalue88 = true := by
  simp only [rawvalue215,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value215_value89 : byteLess rawvalue215 rawvalue89 = true := by
  simp only [rawvalue215,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value215_value90 : byteLess rawvalue215 rawvalue90 = true := by
  simp only [rawvalue215,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value216 : nodes value216 = 3585 := by
  change 1 + (nodes value192 + (nodes value198 + (nodes value203 + (nodes value215 + (nodes value75 + (nodes value76 + (nodes value77 + (nodes value79 + (nodes value80 + (nodes value81 + (nodes value83 + (nodes value84 + (nodes value85 + (nodes value88 + (nodes value89 + (nodes value90 + 0)))))))))))))))) = 3585
  simp only [nodes_value192,nodes_value198,nodes_value203,nodes_value215,nodes_value75,nodes_value76,nodes_value77,nodes_value79,nodes_value80,nodes_value81,nodes_value83,nodes_value84,nodes_value85,nodes_value88,nodes_value89,nodes_value90]
  all_goals decide +kernel
theorem depth_value216 : depth value216 = 10 := by
  change max (1 + depth value192) (max (1 + depth value198) (max (1 + depth value203) (max (1 + depth value215) (max (1 + depth value75) (max (1 + depth value76) (max (1 + depth value77) (max (1 + depth value79) (max (1 + depth value80) (max (1 + depth value81) (max (1 + depth value83) (max (1 + depth value84) (max (1 + depth value85) (max (1 + depth value88) (max (1 + depth value89) (max (1 + depth value90) (0)))))))))))))))) = 10
  simp only [depth_value192,depth_value198,depth_value203,depth_value215,depth_value75,depth_value76,depth_value77,depth_value79,depth_value80,depth_value81,depth_value83,depth_value84,depth_value85,depth_value88,depth_value89,depth_value90]
  all_goals decide +kernel
theorem canonical_value216 : canonical models value216 = true := by
  change ((canonical models value192 && (canonical models value198 && (canonical models value203 && (canonical models value215 && (canonical models value75 && (canonical models value76 && (canonical models value77 && (canonical models value79 && (canonical models value80 && (canonical models value81 && (canonical models value83 && (canonical models value84 && (canonical models value85 && (canonical models value88 && (canonical models value89 && (canonical models value90 && true)))))))))))))))) && ordered [encode value192,encode value198,encode value203,encode value215,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90]) = true
  simp only [canonical_value192,canonical_value198,canonical_value203,canonical_value215,canonical_value75,canonical_value76,canonical_value77,canonical_value79,canonical_value80,canonical_value81,canonical_value83,canonical_value84,canonical_value85,canonical_value88,canonical_value89,canonical_value90,encoded_value192,encoded_value198,encoded_value203,encoded_value215,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  simp only [ordered,List.all_cons,List.all_nil,order_value192_value198,order_value192_value203,order_value192_value215,order_value192_value75,order_value192_value76,order_value192_value77,order_value192_value79,order_value192_value80,order_value192_value81,order_value192_value83,order_value192_value84,order_value192_value85,order_value192_value88,order_value192_value89,order_value192_value90,order_value198_value203,order_value198_value215,order_value198_value75,order_value198_value76,order_value198_value77,order_value198_value79,order_value198_value80,order_value198_value81,order_value198_value83,order_value198_value84,order_value198_value85,order_value198_value88,order_value198_value89,order_value198_value90,order_value203_value215,order_value203_value75,order_value203_value76,order_value203_value77,order_value203_value79,order_value203_value80,order_value203_value81,order_value203_value83,order_value203_value84,order_value203_value85,order_value203_value88,order_value203_value89,order_value203_value90,order_value215_value75,order_value215_value76,order_value215_value77,order_value215_value79,order_value215_value80,order_value215_value81,order_value215_value83,order_value215_value84,order_value215_value85,order_value215_value88,order_value215_value89,order_value215_value90,order_value75_value76,order_value75_value77,order_value75_value79,order_value75_value80,order_value75_value81,order_value75_value83,order_value75_value84,order_value75_value85,order_value75_value88,order_value75_value89,order_value75_value90,order_value76_value77,order_value76_value79,order_value76_value80,order_value76_value81,order_value76_value83,order_value76_value84,order_value76_value85,order_value76_value88,order_value76_value89,order_value76_value90,order_value77_value79,order_value77_value80,order_value77_value81,order_value77_value83,order_value77_value84,order_value77_value85,order_value77_value88,order_value77_value89,order_value77_value90,order_value79_value80,order_value79_value81,order_value79_value83,order_value79_value84,order_value79_value85,order_value79_value88,order_value79_value89,order_value79_value90,order_value80_value81,order_value80_value83,order_value80_value84,order_value80_value85,order_value80_value88,order_value80_value89,order_value80_value90,order_value81_value83,order_value81_value84,order_value81_value85,order_value81_value88,order_value81_value89,order_value81_value90,order_value83_value84,order_value83_value85,order_value83_value88,order_value83_value89,order_value83_value90,order_value84_value85,order_value84_value88,order_value84_value89,order_value84_value90,order_value85_value88,order_value85_value89,order_value85_value90,order_value88_value89,order_value88_value90,order_value89_value90,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value216 : rawvalue216.length = 60618 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value192 (commaConsLength rawLength_value198 (commaConsLength rawLength_value203 (commaConsLength rawLength_value215 (commaConsLength rawLength_value75 (commaConsLength rawLength_value76 (commaConsLength rawLength_value77 (commaConsLength rawLength_value79 (commaConsLength rawLength_value80 (commaConsLength rawLength_value81 (commaConsLength rawLength_value83 (commaConsLength rawLength_value84 (commaConsLength rawLength_value85 (commaConsLength rawLength_value88 (commaConsLength rawLength_value89 (commaSingletonLength rawLength_value90))))))))))))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value217 : Value := .function (.cons value2 value210 (.cons value45 value37 .nil))
noncomputable def rawvalue217 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue210 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue37 ++ [93])] ++ [93,93]
theorem encoded_value217 : encode value217 = rawvalue217 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value210 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value37 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value210,encoded_value45,encoded_value37]
  all_goals rfl
theorem nodes_value217 : nodes value217 = 627 := by
  change 1 + (nodes value2 + nodes value210 + (nodes value45 + nodes value37 + 0)) = 627
  simp only [nodes_value2,nodes_value210,nodes_value45,nodes_value37]
  all_goals decide +kernel
theorem depth_value217 : depth value217 = 9 := by
  change max (max (1 + depth value2) (1 + depth value210)) (max (max (1 + depth value45) (1 + depth value37)) (0)) = 9
  simp only [depth_value2,depth_value210,depth_value45,depth_value37]
  all_goals decide +kernel
theorem canonical_value217 : canonical models value217 = true := by
  change ((canonical models value2 && canonical models value210 && (canonical models value45 && canonical models value37 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value210,canonical_value45,canonical_value37,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value217 : rawvalue217.length = 10565 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value210) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value37) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value218 : Value := .set (.cons value194 (.cons value200 (.cons value205 (.cons value217 .nil))))
noncomputable def rawvalue218 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue194,rawvalue200,rawvalue205,rawvalue217] ++ [93,93]
theorem encoded_value218 : encode value218 = rawvalue218 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value194,encode value200,encode value205,encode value217] ++ [93,93] = _
  simp only [encoded_value194,encoded_value200,encoded_value205,encoded_value217]
  all_goals rfl
theorem order_value194_value217 : byteLess rawvalue194 rawvalue217 = true := by
  simp only [rawvalue194,rawvalue217,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value200_value217 : byteLess rawvalue200 rawvalue217 = true := by
  simp only [rawvalue200,rawvalue217,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value205_value217 : byteLess rawvalue205 rawvalue217 = true := by
  simp only [rawvalue205,rawvalue217,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value218 : nodes value218 = 2509 := by
  change 1 + (nodes value194 + (nodes value200 + (nodes value205 + (nodes value217 + 0)))) = 2509
  simp only [nodes_value194,nodes_value200,nodes_value205,nodes_value217]
  all_goals decide +kernel
theorem depth_value218 : depth value218 = 10 := by
  change max (1 + depth value194) (max (1 + depth value200) (max (1 + depth value205) (max (1 + depth value217) (0)))) = 10
  simp only [depth_value194,depth_value200,depth_value205,depth_value217]
  all_goals decide +kernel
theorem canonical_value218 : canonical models value218 = true := by
  change ((canonical models value194 && (canonical models value200 && (canonical models value205 && (canonical models value217 && true)))) && ordered [encode value194,encode value200,encode value205,encode value217]) = true
  simp only [canonical_value194,canonical_value200,canonical_value205,canonical_value217,encoded_value194,encoded_value200,encoded_value205,encoded_value217]
  simp only [ordered,List.all_cons,List.all_nil,order_value194_value200,order_value194_value205,order_value194_value217,order_value200_value205,order_value200_value217,order_value205_value217,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value218 : rawvalue218.length = 42270 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value194 (commaConsLength rawLength_value200 (commaConsLength rawLength_value205 (commaSingletonLength rawLength_value217))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value219 : Value := .integer (23)
noncomputable def rawvalue219 : Bytes := asciiBytes "[\"int\",\"23\"]"
theorem encoded_value219 : encode value219 = rawvalue219 := by
  all_goals rfl
theorem nodes_value219 : nodes value219 = 1 := by rfl
theorem depth_value219 : depth value219 = 0 := by rfl
theorem canonical_value219 : canonical models value219 = true := by decide +kernel
theorem rawLength_value219 : rawvalue219.length = 12 := by
  decide +kernel
noncomputable def value220 : Value := .function (.cons value37 value212 (.cons value38 value212 (.cons value39 value188 (.cons value43 value64 .nil))))
noncomputable def rawvalue220 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue37 ++ [44] ++ rawvalue212 ++ [93]),([91] ++ rawvalue38 ++ [44] ++ rawvalue212 ++ [93]),([91] ++ rawvalue39 ++ [44] ++ rawvalue188 ++ [93]),([91] ++ rawvalue43 ++ [44] ++ rawvalue64 ++ [93])] ++ [93,93]
theorem encoded_value220 : encode value220 = rawvalue220 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value37 ++ [44] ++ encode value212 ++ [93]),([91] ++ encode value38 ++ [44] ++ encode value212 ++ [93]),([91] ++ encode value39 ++ [44] ++ encode value188 ++ [93]),([91] ++ encode value43 ++ [44] ++ encode value64 ++ [93])] ++ [93,93] = _
  simp only [encoded_value37,encoded_value212,encoded_value38,encoded_value39,encoded_value188,encoded_value43,encoded_value64]
  all_goals rfl
theorem nodes_value220 : nodes value220 = 9 := by
  change 1 + (nodes value37 + nodes value212 + (nodes value38 + nodes value212 + (nodes value39 + nodes value188 + (nodes value43 + nodes value64 + 0)))) = 9
  simp only [nodes_value37,nodes_value212,nodes_value38,nodes_value39,nodes_value188,nodes_value43,nodes_value64]
  all_goals decide +kernel
theorem depth_value220 : depth value220 = 1 := by
  change max (max (1 + depth value37) (1 + depth value212)) (max (max (1 + depth value38) (1 + depth value212)) (max (max (1 + depth value39) (1 + depth value188)) (max (max (1 + depth value43) (1 + depth value64)) (0)))) = 1
  simp only [depth_value37,depth_value212,depth_value38,depth_value39,depth_value188,depth_value43,depth_value64]
  all_goals decide +kernel
theorem canonical_value220 : canonical models value220 = true := by
  change ((canonical models value37 && canonical models value212 && (canonical models value38 && canonical models value212 && (canonical models value39 && canonical models value188 && (canonical models value43 && canonical models value64 && true)))) && ordered [encode value37,encode value38,encode value39,encode value43]) = true
  simp only [canonical_value37,canonical_value212,canonical_value38,canonical_value39,canonical_value188,canonical_value43,canonical_value64,encoded_value37,encoded_value38,encoded_value39,encoded_value43]
  simp only [ordered,List.all_cons,List.all_nil,order_value37_value38,order_value37_value39,order_value37_value43,order_value38_value39,order_value38_value43,order_value39_value43,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value220 : rawvalue220.length = 125 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value37) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value212) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value38) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value212) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value39) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value188) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value43) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value64) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value221 : Value := .function (.cons value2 value210 (.cons value72 value214 (.cons value73 value191 (.cons value45 value38 .nil))))
noncomputable def rawvalue221 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue210 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue214 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue191 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue38 ++ [93])] ++ [93,93]
theorem encoded_value221 : encode value221 = rawvalue221 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value210 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value214 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value191 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value38 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value210,encoded_value72,encoded_value214,encoded_value73,encoded_value191,encoded_value45,encoded_value38]
  all_goals rfl
theorem nodes_value221 : nodes value221 = 635 := by
  change 1 + (nodes value2 + nodes value210 + (nodes value72 + nodes value214 + (nodes value73 + nodes value191 + (nodes value45 + nodes value38 + 0)))) = 635
  simp only [nodes_value2,nodes_value210,nodes_value72,nodes_value214,nodes_value73,nodes_value191,nodes_value45,nodes_value38]
  all_goals decide +kernel
theorem depth_value221 : depth value221 = 9 := by
  change max (max (1 + depth value2) (1 + depth value210)) (max (max (1 + depth value72) (1 + depth value214)) (max (max (1 + depth value73) (1 + depth value191)) (max (max (1 + depth value45) (1 + depth value38)) (0)))) = 9
  simp only [depth_value2,depth_value210,depth_value72,depth_value214,depth_value73,depth_value191,depth_value45,depth_value38]
  all_goals decide +kernel
theorem canonical_value221 : canonical models value221 = true := by
  change ((canonical models value2 && canonical models value210 && (canonical models value72 && canonical models value214 && (canonical models value73 && canonical models value191 && (canonical models value45 && canonical models value38 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value210,canonical_value72,canonical_value214,canonical_value73,canonical_value191,canonical_value45,canonical_value38,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value221 : rawvalue221.length = 10703 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value210) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value214) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value191) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value38) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value222 : Value := .set (.cons value192 (.cons value198 (.cons value203 (.cons value215 (.cons value221 (.cons value75 (.cons value76 (.cons value77 (.cons value79 (.cons value80 (.cons value81 (.cons value83 (.cons value84 (.cons value85 (.cons value88 (.cons value89 (.cons value90 .nil)))))))))))))))))
noncomputable def rawvalue222 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue192,rawvalue198,rawvalue203,rawvalue215,rawvalue221,rawvalue75,rawvalue76,rawvalue77,rawvalue79,rawvalue80,rawvalue81,rawvalue83,rawvalue84,rawvalue85,rawvalue88,rawvalue89,rawvalue90] ++ [93,93]
theorem encoded_value222 : encode value222 = rawvalue222 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value192,encode value198,encode value203,encode value215,encode value221,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90] ++ [93,93] = _
  simp only [encoded_value192,encoded_value198,encoded_value203,encoded_value215,encoded_value221,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  all_goals rfl
theorem order_value192_value221 : byteLess rawvalue192 rawvalue221 = true := by
  simp only [rawvalue192,rawvalue221,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value221 : byteLess rawvalue198 rawvalue221 = true := by
  simp only [rawvalue198,rawvalue221,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value203_value221 : byteLess rawvalue203 rawvalue221 = true := by
  simp only [rawvalue203,rawvalue221,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value215_value221 : byteLess rawvalue215 rawvalue221 = true := by
  simp only [rawvalue215,rawvalue221,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue38,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value221_value75 : byteLess rawvalue221 rawvalue75 = true := by
  simp only [rawvalue221,rawvalue75,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value221_value76 : byteLess rawvalue221 rawvalue76 = true := by
  simp only [rawvalue221,rawvalue76,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value221_value77 : byteLess rawvalue221 rawvalue77 = true := by
  simp only [rawvalue221,rawvalue77,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value221_value79 : byteLess rawvalue221 rawvalue79 = true := by
  simp only [rawvalue221,rawvalue79,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value221_value80 : byteLess rawvalue221 rawvalue80 = true := by
  simp only [rawvalue221,rawvalue80,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value221_value81 : byteLess rawvalue221 rawvalue81 = true := by
  simp only [rawvalue221,rawvalue81,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value221_value83 : byteLess rawvalue221 rawvalue83 = true := by
  simp only [rawvalue221,rawvalue83,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value221_value84 : byteLess rawvalue221 rawvalue84 = true := by
  simp only [rawvalue221,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value221_value85 : byteLess rawvalue221 rawvalue85 = true := by
  simp only [rawvalue221,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value221_value88 : byteLess rawvalue221 rawvalue88 = true := by
  simp only [rawvalue221,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value221_value89 : byteLess rawvalue221 rawvalue89 = true := by
  simp only [rawvalue221,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value221_value90 : byteLess rawvalue221 rawvalue90 = true := by
  simp only [rawvalue221,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value222 : nodes value222 = 4220 := by
  change 1 + (nodes value192 + (nodes value198 + (nodes value203 + (nodes value215 + (nodes value221 + (nodes value75 + (nodes value76 + (nodes value77 + (nodes value79 + (nodes value80 + (nodes value81 + (nodes value83 + (nodes value84 + (nodes value85 + (nodes value88 + (nodes value89 + (nodes value90 + 0))))))))))))))))) = 4220
  simp only [nodes_value192,nodes_value198,nodes_value203,nodes_value215,nodes_value221,nodes_value75,nodes_value76,nodes_value77,nodes_value79,nodes_value80,nodes_value81,nodes_value83,nodes_value84,nodes_value85,nodes_value88,nodes_value89,nodes_value90]
  all_goals decide +kernel
theorem depth_value222 : depth value222 = 10 := by
  change max (1 + depth value192) (max (1 + depth value198) (max (1 + depth value203) (max (1 + depth value215) (max (1 + depth value221) (max (1 + depth value75) (max (1 + depth value76) (max (1 + depth value77) (max (1 + depth value79) (max (1 + depth value80) (max (1 + depth value81) (max (1 + depth value83) (max (1 + depth value84) (max (1 + depth value85) (max (1 + depth value88) (max (1 + depth value89) (max (1 + depth value90) (0))))))))))))))))) = 10
  simp only [depth_value192,depth_value198,depth_value203,depth_value215,depth_value221,depth_value75,depth_value76,depth_value77,depth_value79,depth_value80,depth_value81,depth_value83,depth_value84,depth_value85,depth_value88,depth_value89,depth_value90]
  all_goals decide +kernel
theorem canonical_value222 : canonical models value222 = true := by
  change ((canonical models value192 && (canonical models value198 && (canonical models value203 && (canonical models value215 && (canonical models value221 && (canonical models value75 && (canonical models value76 && (canonical models value77 && (canonical models value79 && (canonical models value80 && (canonical models value81 && (canonical models value83 && (canonical models value84 && (canonical models value85 && (canonical models value88 && (canonical models value89 && (canonical models value90 && true))))))))))))))))) && ordered [encode value192,encode value198,encode value203,encode value215,encode value221,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90]) = true
  simp only [canonical_value192,canonical_value198,canonical_value203,canonical_value215,canonical_value221,canonical_value75,canonical_value76,canonical_value77,canonical_value79,canonical_value80,canonical_value81,canonical_value83,canonical_value84,canonical_value85,canonical_value88,canonical_value89,canonical_value90,encoded_value192,encoded_value198,encoded_value203,encoded_value215,encoded_value221,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  simp only [ordered,List.all_cons,List.all_nil,order_value192_value198,order_value192_value203,order_value192_value215,order_value192_value221,order_value192_value75,order_value192_value76,order_value192_value77,order_value192_value79,order_value192_value80,order_value192_value81,order_value192_value83,order_value192_value84,order_value192_value85,order_value192_value88,order_value192_value89,order_value192_value90,order_value198_value203,order_value198_value215,order_value198_value221,order_value198_value75,order_value198_value76,order_value198_value77,order_value198_value79,order_value198_value80,order_value198_value81,order_value198_value83,order_value198_value84,order_value198_value85,order_value198_value88,order_value198_value89,order_value198_value90,order_value203_value215,order_value203_value221,order_value203_value75,order_value203_value76,order_value203_value77,order_value203_value79,order_value203_value80,order_value203_value81,order_value203_value83,order_value203_value84,order_value203_value85,order_value203_value88,order_value203_value89,order_value203_value90,order_value215_value221,order_value215_value75,order_value215_value76,order_value215_value77,order_value215_value79,order_value215_value80,order_value215_value81,order_value215_value83,order_value215_value84,order_value215_value85,order_value215_value88,order_value215_value89,order_value215_value90,order_value221_value75,order_value221_value76,order_value221_value77,order_value221_value79,order_value221_value80,order_value221_value81,order_value221_value83,order_value221_value84,order_value221_value85,order_value221_value88,order_value221_value89,order_value221_value90,order_value75_value76,order_value75_value77,order_value75_value79,order_value75_value80,order_value75_value81,order_value75_value83,order_value75_value84,order_value75_value85,order_value75_value88,order_value75_value89,order_value75_value90,order_value76_value77,order_value76_value79,order_value76_value80,order_value76_value81,order_value76_value83,order_value76_value84,order_value76_value85,order_value76_value88,order_value76_value89,order_value76_value90,order_value77_value79,order_value77_value80,order_value77_value81,order_value77_value83,order_value77_value84,order_value77_value85,order_value77_value88,order_value77_value89,order_value77_value90,order_value79_value80,order_value79_value81,order_value79_value83,order_value79_value84,order_value79_value85,order_value79_value88,order_value79_value89,order_value79_value90,order_value80_value81,order_value80_value83,order_value80_value84,order_value80_value85,order_value80_value88,order_value80_value89,order_value80_value90,order_value81_value83,order_value81_value84,order_value81_value85,order_value81_value88,order_value81_value89,order_value81_value90,order_value83_value84,order_value83_value85,order_value83_value88,order_value83_value89,order_value83_value90,order_value84_value85,order_value84_value88,order_value84_value89,order_value84_value90,order_value85_value88,order_value85_value89,order_value85_value90,order_value88_value89,order_value88_value90,order_value89_value90,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value222 : rawvalue222.length = 71322 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value192 (commaConsLength rawLength_value198 (commaConsLength rawLength_value203 (commaConsLength rawLength_value215 (commaConsLength rawLength_value221 (commaConsLength rawLength_value75 (commaConsLength rawLength_value76 (commaConsLength rawLength_value77 (commaConsLength rawLength_value79 (commaConsLength rawLength_value80 (commaConsLength rawLength_value81 (commaConsLength rawLength_value83 (commaConsLength rawLength_value84 (commaConsLength rawLength_value85 (commaConsLength rawLength_value88 (commaConsLength rawLength_value89 (commaSingletonLength rawLength_value90)))))))))))))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value223 : Value := .function (.cons value2 value210 (.cons value45 value38 .nil))
noncomputable def rawvalue223 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue210 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue38 ++ [93])] ++ [93,93]
theorem encoded_value223 : encode value223 = rawvalue223 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value210 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value38 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value210,encoded_value45,encoded_value38]
  all_goals rfl
theorem nodes_value223 : nodes value223 = 627 := by
  change 1 + (nodes value2 + nodes value210 + (nodes value45 + nodes value38 + 0)) = 627
  simp only [nodes_value2,nodes_value210,nodes_value45,nodes_value38]
  all_goals decide +kernel
theorem depth_value223 : depth value223 = 9 := by
  change max (max (1 + depth value2) (1 + depth value210)) (max (max (1 + depth value45) (1 + depth value38)) (0)) = 9
  simp only [depth_value2,depth_value210,depth_value45,depth_value38]
  all_goals decide +kernel
theorem canonical_value223 : canonical models value223 = true := by
  change ((canonical models value2 && canonical models value210 && (canonical models value45 && canonical models value38 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value210,canonical_value45,canonical_value38,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value223 : rawvalue223.length = 10565 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value210) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value38) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value224 : Value := .set (.cons value194 (.cons value200 (.cons value205 (.cons value217 (.cons value223 .nil)))))
noncomputable def rawvalue224 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue194,rawvalue200,rawvalue205,rawvalue217,rawvalue223] ++ [93,93]
theorem encoded_value224 : encode value224 = rawvalue224 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value194,encode value200,encode value205,encode value217,encode value223] ++ [93,93] = _
  simp only [encoded_value194,encoded_value200,encoded_value205,encoded_value217,encoded_value223]
  all_goals rfl
theorem order_value194_value223 : byteLess rawvalue194 rawvalue223 = true := by
  simp only [rawvalue194,rawvalue223,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value200_value223 : byteLess rawvalue200 rawvalue223 = true := by
  simp only [rawvalue200,rawvalue223,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value205_value223 : byteLess rawvalue205 rawvalue223 = true := by
  simp only [rawvalue205,rawvalue223,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value217_value223 : byteLess rawvalue217 rawvalue223 = true := by
  simp only [rawvalue217,rawvalue223,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue38,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value224 : nodes value224 = 3136 := by
  change 1 + (nodes value194 + (nodes value200 + (nodes value205 + (nodes value217 + (nodes value223 + 0))))) = 3136
  simp only [nodes_value194,nodes_value200,nodes_value205,nodes_value217,nodes_value223]
  all_goals decide +kernel
theorem depth_value224 : depth value224 = 10 := by
  change max (1 + depth value194) (max (1 + depth value200) (max (1 + depth value205) (max (1 + depth value217) (max (1 + depth value223) (0))))) = 10
  simp only [depth_value194,depth_value200,depth_value205,depth_value217,depth_value223]
  all_goals decide +kernel
theorem canonical_value224 : canonical models value224 = true := by
  change ((canonical models value194 && (canonical models value200 && (canonical models value205 && (canonical models value217 && (canonical models value223 && true))))) && ordered [encode value194,encode value200,encode value205,encode value217,encode value223]) = true
  simp only [canonical_value194,canonical_value200,canonical_value205,canonical_value217,canonical_value223,encoded_value194,encoded_value200,encoded_value205,encoded_value217,encoded_value223]
  simp only [ordered,List.all_cons,List.all_nil,order_value194_value200,order_value194_value205,order_value194_value217,order_value194_value223,order_value200_value205,order_value200_value217,order_value200_value223,order_value205_value217,order_value205_value223,order_value217_value223,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value224 : rawvalue224.length = 52836 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value194 (commaConsLength rawLength_value200 (commaConsLength rawLength_value205 (commaConsLength rawLength_value217 (commaSingletonLength rawLength_value223)))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value225 : Value := .integer (24)
noncomputable def rawvalue225 : Bytes := asciiBytes "[\"int\",\"24\"]"
theorem encoded_value225 : encode value225 = rawvalue225 := by
  all_goals rfl
theorem nodes_value225 : nodes value225 = 1 := by rfl
theorem depth_value225 : depth value225 = 0 := by rfl
theorem canonical_value225 : canonical models value225 = true := by decide +kernel
theorem rawLength_value225 : rawvalue225.length = 12 := by
  decide +kernel
noncomputable def value226 : Value := .function (.cons value37 value212 (.cons value38 value212 (.cons value39 value212 (.cons value43 value64 .nil))))
noncomputable def rawvalue226 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue37 ++ [44] ++ rawvalue212 ++ [93]),([91] ++ rawvalue38 ++ [44] ++ rawvalue212 ++ [93]),([91] ++ rawvalue39 ++ [44] ++ rawvalue212 ++ [93]),([91] ++ rawvalue43 ++ [44] ++ rawvalue64 ++ [93])] ++ [93,93]
theorem encoded_value226 : encode value226 = rawvalue226 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value37 ++ [44] ++ encode value212 ++ [93]),([91] ++ encode value38 ++ [44] ++ encode value212 ++ [93]),([91] ++ encode value39 ++ [44] ++ encode value212 ++ [93]),([91] ++ encode value43 ++ [44] ++ encode value64 ++ [93])] ++ [93,93] = _
  simp only [encoded_value37,encoded_value212,encoded_value38,encoded_value39,encoded_value43,encoded_value64]
  all_goals rfl
theorem nodes_value226 : nodes value226 = 9 := by
  change 1 + (nodes value37 + nodes value212 + (nodes value38 + nodes value212 + (nodes value39 + nodes value212 + (nodes value43 + nodes value64 + 0)))) = 9
  simp only [nodes_value37,nodes_value212,nodes_value38,nodes_value39,nodes_value43,nodes_value64]
  all_goals decide +kernel
theorem depth_value226 : depth value226 = 1 := by
  change max (max (1 + depth value37) (1 + depth value212)) (max (max (1 + depth value38) (1 + depth value212)) (max (max (1 + depth value39) (1 + depth value212)) (max (max (1 + depth value43) (1 + depth value64)) (0)))) = 1
  simp only [depth_value37,depth_value212,depth_value38,depth_value39,depth_value43,depth_value64]
  all_goals decide +kernel
theorem canonical_value226 : canonical models value226 = true := by
  change ((canonical models value37 && canonical models value212 && (canonical models value38 && canonical models value212 && (canonical models value39 && canonical models value212 && (canonical models value43 && canonical models value64 && true)))) && ordered [encode value37,encode value38,encode value39,encode value43]) = true
  simp only [canonical_value37,canonical_value212,canonical_value38,canonical_value39,canonical_value43,canonical_value64,encoded_value37,encoded_value38,encoded_value39,encoded_value43]
  simp only [ordered,List.all_cons,List.all_nil,order_value37_value38,order_value37_value39,order_value37_value43,order_value38_value39,order_value38_value43,order_value39_value43,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value226 : rawvalue226.length = 125 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value37) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value212) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value38) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value212) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value39) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value212) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value43) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value64) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value227 : Value := .function (.cons value2 value210 (.cons value72 value214 (.cons value73 value191 (.cons value45 value39 .nil))))
noncomputable def rawvalue227 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue210 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue214 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue191 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue39 ++ [93])] ++ [93,93]
theorem encoded_value227 : encode value227 = rawvalue227 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value210 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value214 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value191 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value39 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value210,encoded_value72,encoded_value214,encoded_value73,encoded_value191,encoded_value45,encoded_value39]
  all_goals rfl
theorem nodes_value227 : nodes value227 = 635 := by
  change 1 + (nodes value2 + nodes value210 + (nodes value72 + nodes value214 + (nodes value73 + nodes value191 + (nodes value45 + nodes value39 + 0)))) = 635
  simp only [nodes_value2,nodes_value210,nodes_value72,nodes_value214,nodes_value73,nodes_value191,nodes_value45,nodes_value39]
  all_goals decide +kernel
theorem depth_value227 : depth value227 = 9 := by
  change max (max (1 + depth value2) (1 + depth value210)) (max (max (1 + depth value72) (1 + depth value214)) (max (max (1 + depth value73) (1 + depth value191)) (max (max (1 + depth value45) (1 + depth value39)) (0)))) = 9
  simp only [depth_value2,depth_value210,depth_value72,depth_value214,depth_value73,depth_value191,depth_value45,depth_value39]
  all_goals decide +kernel
theorem canonical_value227 : canonical models value227 = true := by
  change ((canonical models value2 && canonical models value210 && (canonical models value72 && canonical models value214 && (canonical models value73 && canonical models value191 && (canonical models value45 && canonical models value39 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value210,canonical_value72,canonical_value214,canonical_value73,canonical_value191,canonical_value45,canonical_value39,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value227 : rawvalue227.length = 10703 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value210) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value214) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value191) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value39) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value228 : Value := .set (.cons value192 (.cons value198 (.cons value203 (.cons value215 (.cons value221 (.cons value227 (.cons value75 (.cons value76 (.cons value77 (.cons value79 (.cons value80 (.cons value81 (.cons value83 (.cons value84 (.cons value85 (.cons value88 (.cons value89 (.cons value90 .nil))))))))))))))))))
noncomputable def rawvalue228 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue192,rawvalue198,rawvalue203,rawvalue215,rawvalue221,rawvalue227,rawvalue75,rawvalue76,rawvalue77,rawvalue79,rawvalue80,rawvalue81,rawvalue83,rawvalue84,rawvalue85,rawvalue88,rawvalue89,rawvalue90] ++ [93,93]
theorem encoded_value228 : encode value228 = rawvalue228 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value192,encode value198,encode value203,encode value215,encode value221,encode value227,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90] ++ [93,93] = _
  simp only [encoded_value192,encoded_value198,encoded_value203,encoded_value215,encoded_value221,encoded_value227,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  all_goals rfl
theorem order_value192_value227 : byteLess rawvalue192 rawvalue227 = true := by
  simp only [rawvalue192,rawvalue227,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value227 : byteLess rawvalue198 rawvalue227 = true := by
  simp only [rawvalue198,rawvalue227,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value203_value227 : byteLess rawvalue203 rawvalue227 = true := by
  simp only [rawvalue203,rawvalue227,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value215_value227 : byteLess rawvalue215 rawvalue227 = true := by
  simp only [rawvalue215,rawvalue227,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value221_value227 : byteLess rawvalue221 rawvalue227 = true := by
  simp only [rawvalue221,rawvalue227,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue38,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value227_value75 : byteLess rawvalue227 rawvalue75 = true := by
  simp only [rawvalue227,rawvalue75,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value227_value76 : byteLess rawvalue227 rawvalue76 = true := by
  simp only [rawvalue227,rawvalue76,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value227_value77 : byteLess rawvalue227 rawvalue77 = true := by
  simp only [rawvalue227,rawvalue77,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value227_value79 : byteLess rawvalue227 rawvalue79 = true := by
  simp only [rawvalue227,rawvalue79,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value227_value80 : byteLess rawvalue227 rawvalue80 = true := by
  simp only [rawvalue227,rawvalue80,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value227_value81 : byteLess rawvalue227 rawvalue81 = true := by
  simp only [rawvalue227,rawvalue81,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value227_value83 : byteLess rawvalue227 rawvalue83 = true := by
  simp only [rawvalue227,rawvalue83,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value227_value84 : byteLess rawvalue227 rawvalue84 = true := by
  simp only [rawvalue227,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value227_value85 : byteLess rawvalue227 rawvalue85 = true := by
  simp only [rawvalue227,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value227_value88 : byteLess rawvalue227 rawvalue88 = true := by
  simp only [rawvalue227,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value227_value89 : byteLess rawvalue227 rawvalue89 = true := by
  simp only [rawvalue227,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value227_value90 : byteLess rawvalue227 rawvalue90 = true := by
  simp only [rawvalue227,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value228 : nodes value228 = 4855 := by
  change 1 + (nodes value192 + (nodes value198 + (nodes value203 + (nodes value215 + (nodes value221 + (nodes value227 + (nodes value75 + (nodes value76 + (nodes value77 + (nodes value79 + (nodes value80 + (nodes value81 + (nodes value83 + (nodes value84 + (nodes value85 + (nodes value88 + (nodes value89 + (nodes value90 + 0)))))))))))))))))) = 4855
  simp only [nodes_value192,nodes_value198,nodes_value203,nodes_value215,nodes_value221,nodes_value227,nodes_value75,nodes_value76,nodes_value77,nodes_value79,nodes_value80,nodes_value81,nodes_value83,nodes_value84,nodes_value85,nodes_value88,nodes_value89,nodes_value90]
  all_goals decide +kernel
theorem depth_value228 : depth value228 = 10 := by
  change max (1 + depth value192) (max (1 + depth value198) (max (1 + depth value203) (max (1 + depth value215) (max (1 + depth value221) (max (1 + depth value227) (max (1 + depth value75) (max (1 + depth value76) (max (1 + depth value77) (max (1 + depth value79) (max (1 + depth value80) (max (1 + depth value81) (max (1 + depth value83) (max (1 + depth value84) (max (1 + depth value85) (max (1 + depth value88) (max (1 + depth value89) (max (1 + depth value90) (0)))))))))))))))))) = 10
  simp only [depth_value192,depth_value198,depth_value203,depth_value215,depth_value221,depth_value227,depth_value75,depth_value76,depth_value77,depth_value79,depth_value80,depth_value81,depth_value83,depth_value84,depth_value85,depth_value88,depth_value89,depth_value90]
  all_goals decide +kernel
theorem canonical_value228 : canonical models value228 = true := by
  change ((canonical models value192 && (canonical models value198 && (canonical models value203 && (canonical models value215 && (canonical models value221 && (canonical models value227 && (canonical models value75 && (canonical models value76 && (canonical models value77 && (canonical models value79 && (canonical models value80 && (canonical models value81 && (canonical models value83 && (canonical models value84 && (canonical models value85 && (canonical models value88 && (canonical models value89 && (canonical models value90 && true)))))))))))))))))) && ordered [encode value192,encode value198,encode value203,encode value215,encode value221,encode value227,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90]) = true
  simp only [canonical_value192,canonical_value198,canonical_value203,canonical_value215,canonical_value221,canonical_value227,canonical_value75,canonical_value76,canonical_value77,canonical_value79,canonical_value80,canonical_value81,canonical_value83,canonical_value84,canonical_value85,canonical_value88,canonical_value89,canonical_value90,encoded_value192,encoded_value198,encoded_value203,encoded_value215,encoded_value221,encoded_value227,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  simp only [ordered,List.all_cons,List.all_nil,order_value192_value198,order_value192_value203,order_value192_value215,order_value192_value221,order_value192_value227,order_value192_value75,order_value192_value76,order_value192_value77,order_value192_value79,order_value192_value80,order_value192_value81,order_value192_value83,order_value192_value84,order_value192_value85,order_value192_value88,order_value192_value89,order_value192_value90,order_value198_value203,order_value198_value215,order_value198_value221,order_value198_value227,order_value198_value75,order_value198_value76,order_value198_value77,order_value198_value79,order_value198_value80,order_value198_value81,order_value198_value83,order_value198_value84,order_value198_value85,order_value198_value88,order_value198_value89,order_value198_value90,order_value203_value215,order_value203_value221,order_value203_value227,order_value203_value75,order_value203_value76,order_value203_value77,order_value203_value79,order_value203_value80,order_value203_value81,order_value203_value83,order_value203_value84,order_value203_value85,order_value203_value88,order_value203_value89,order_value203_value90,order_value215_value221,order_value215_value227,order_value215_value75,order_value215_value76,order_value215_value77,order_value215_value79,order_value215_value80,order_value215_value81,order_value215_value83,order_value215_value84,order_value215_value85,order_value215_value88,order_value215_value89,order_value215_value90,order_value221_value227,order_value221_value75,order_value221_value76,order_value221_value77,order_value221_value79,order_value221_value80,order_value221_value81,order_value221_value83,order_value221_value84,order_value221_value85,order_value221_value88,order_value221_value89,order_value221_value90,order_value227_value75,order_value227_value76,order_value227_value77,order_value227_value79,order_value227_value80,order_value227_value81,order_value227_value83,order_value227_value84,order_value227_value85,order_value227_value88,order_value227_value89,order_value227_value90,order_value75_value76,order_value75_value77,order_value75_value79,order_value75_value80,order_value75_value81,order_value75_value83,order_value75_value84,order_value75_value85,order_value75_value88,order_value75_value89,order_value75_value90,order_value76_value77,order_value76_value79,order_value76_value80,order_value76_value81,order_value76_value83,order_value76_value84,order_value76_value85,order_value76_value88,order_value76_value89,order_value76_value90,order_value77_value79,order_value77_value80,order_value77_value81,order_value77_value83,order_value77_value84,order_value77_value85,order_value77_value88,order_value77_value89,order_value77_value90,order_value79_value80,order_value79_value81,order_value79_value83,order_value79_value84,order_value79_value85,order_value79_value88,order_value79_value89,order_value79_value90,order_value80_value81,order_value80_value83,order_value80_value84,order_value80_value85,order_value80_value88,order_value80_value89,order_value80_value90,order_value81_value83,order_value81_value84,order_value81_value85,order_value81_value88,order_value81_value89,order_value81_value90,order_value83_value84,order_value83_value85,order_value83_value88,order_value83_value89,order_value83_value90,order_value84_value85,order_value84_value88,order_value84_value89,order_value84_value90,order_value85_value88,order_value85_value89,order_value85_value90,order_value88_value89,order_value88_value90,order_value89_value90,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value228 : rawvalue228.length = 82026 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value192 (commaConsLength rawLength_value198 (commaConsLength rawLength_value203 (commaConsLength rawLength_value215 (commaConsLength rawLength_value221 (commaConsLength rawLength_value227 (commaConsLength rawLength_value75 (commaConsLength rawLength_value76 (commaConsLength rawLength_value77 (commaConsLength rawLength_value79 (commaConsLength rawLength_value80 (commaConsLength rawLength_value81 (commaConsLength rawLength_value83 (commaConsLength rawLength_value84 (commaConsLength rawLength_value85 (commaConsLength rawLength_value88 (commaConsLength rawLength_value89 (commaSingletonLength rawLength_value90))))))))))))))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value229 : Value := .function (.cons value2 value210 (.cons value45 value39 .nil))
noncomputable def rawvalue229 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue210 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue39 ++ [93])] ++ [93,93]
theorem encoded_value229 : encode value229 = rawvalue229 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value210 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value39 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value210,encoded_value45,encoded_value39]
  all_goals rfl
theorem nodes_value229 : nodes value229 = 627 := by
  change 1 + (nodes value2 + nodes value210 + (nodes value45 + nodes value39 + 0)) = 627
  simp only [nodes_value2,nodes_value210,nodes_value45,nodes_value39]
  all_goals decide +kernel
theorem depth_value229 : depth value229 = 9 := by
  change max (max (1 + depth value2) (1 + depth value210)) (max (max (1 + depth value45) (1 + depth value39)) (0)) = 9
  simp only [depth_value2,depth_value210,depth_value45,depth_value39]
  all_goals decide +kernel
theorem canonical_value229 : canonical models value229 = true := by
  change ((canonical models value2 && canonical models value210 && (canonical models value45 && canonical models value39 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value210,canonical_value45,canonical_value39,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value229 : rawvalue229.length = 10565 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value210) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value39) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value230 : Value := .set (.cons value194 (.cons value200 (.cons value205 (.cons value217 (.cons value223 (.cons value229 .nil))))))
noncomputable def rawvalue230 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue194,rawvalue200,rawvalue205,rawvalue217,rawvalue223,rawvalue229] ++ [93,93]
theorem encoded_value230 : encode value230 = rawvalue230 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value194,encode value200,encode value205,encode value217,encode value223,encode value229] ++ [93,93] = _
  simp only [encoded_value194,encoded_value200,encoded_value205,encoded_value217,encoded_value223,encoded_value229]
  all_goals rfl
theorem order_value194_value229 : byteLess rawvalue194 rawvalue229 = true := by
  simp only [rawvalue194,rawvalue229,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value200_value229 : byteLess rawvalue200 rawvalue229 = true := by
  simp only [rawvalue200,rawvalue229,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value205_value229 : byteLess rawvalue205 rawvalue229 = true := by
  simp only [rawvalue205,rawvalue229,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value217_value229 : byteLess rawvalue217 rawvalue229 = true := by
  simp only [rawvalue217,rawvalue229,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value223_value229 : byteLess rawvalue223 rawvalue229 = true := by
  simp only [rawvalue223,rawvalue229,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue38,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value230 : nodes value230 = 3763 := by
  change 1 + (nodes value194 + (nodes value200 + (nodes value205 + (nodes value217 + (nodes value223 + (nodes value229 + 0)))))) = 3763
  simp only [nodes_value194,nodes_value200,nodes_value205,nodes_value217,nodes_value223,nodes_value229]
  all_goals decide +kernel
theorem depth_value230 : depth value230 = 10 := by
  change max (1 + depth value194) (max (1 + depth value200) (max (1 + depth value205) (max (1 + depth value217) (max (1 + depth value223) (max (1 + depth value229) (0)))))) = 10
  simp only [depth_value194,depth_value200,depth_value205,depth_value217,depth_value223,depth_value229]
  all_goals decide +kernel
theorem canonical_value230 : canonical models value230 = true := by
  change ((canonical models value194 && (canonical models value200 && (canonical models value205 && (canonical models value217 && (canonical models value223 && (canonical models value229 && true)))))) && ordered [encode value194,encode value200,encode value205,encode value217,encode value223,encode value229]) = true
  simp only [canonical_value194,canonical_value200,canonical_value205,canonical_value217,canonical_value223,canonical_value229,encoded_value194,encoded_value200,encoded_value205,encoded_value217,encoded_value223,encoded_value229]
  simp only [ordered,List.all_cons,List.all_nil,order_value194_value200,order_value194_value205,order_value194_value217,order_value194_value223,order_value194_value229,order_value200_value205,order_value200_value217,order_value200_value223,order_value200_value229,order_value205_value217,order_value205_value223,order_value205_value229,order_value217_value223,order_value217_value229,order_value223_value229,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value230 : rawvalue230.length = 63402 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value194 (commaConsLength rawLength_value200 (commaConsLength rawLength_value205 (commaConsLength rawLength_value217 (commaConsLength rawLength_value223 (commaSingletonLength rawLength_value229))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value231 : Value := .text "leaves"
noncomputable def rawvalue231 : Bytes := asciiBytes "[\"str\",\"leaves\"]"
theorem encoded_value231 : encode value231 = rawvalue231 := by
  all_goals rfl
theorem nodes_value231 : nodes value231 = 1 := by rfl
theorem depth_value231 : depth value231 = 0 := by rfl
theorem canonical_value231 : canonical models value231 = true := by decide +kernel
theorem rawLength_value231 : rawvalue231.length = 16 := by
  decide +kernel
noncomputable def value232 : Value := .function (.cons value109 value35 (.cons value110 value111 (.cons value7 value211 (.cons value3 value4 (.cons value14 value15 (.cons value5 value34 (.cons value6 value25 (.cons value231 value211 (.cons value167 value69 (.cons value19 value24 (.cons value161 value162 (.cons value30 value33 .nil))))))))))))
noncomputable def rawvalue232 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue109 ++ [44] ++ rawvalue35 ++ [93]),([91] ++ rawvalue110 ++ [44] ++ rawvalue111 ++ [93]),([91] ++ rawvalue7 ++ [44] ++ rawvalue211 ++ [93]),([91] ++ rawvalue3 ++ [44] ++ rawvalue4 ++ [93]),([91] ++ rawvalue14 ++ [44] ++ rawvalue15 ++ [93]),([91] ++ rawvalue5 ++ [44] ++ rawvalue34 ++ [93]),([91] ++ rawvalue6 ++ [44] ++ rawvalue25 ++ [93]),([91] ++ rawvalue231 ++ [44] ++ rawvalue211 ++ [93]),([91] ++ rawvalue167 ++ [44] ++ rawvalue69 ++ [93]),([91] ++ rawvalue19 ++ [44] ++ rawvalue24 ++ [93]),([91] ++ rawvalue161 ++ [44] ++ rawvalue162 ++ [93]),([91] ++ rawvalue30 ++ [44] ++ rawvalue33 ++ [93])] ++ [93,93]
theorem encoded_value232 : encode value232 = rawvalue232 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value109 ++ [44] ++ encode value35 ++ [93]),([91] ++ encode value110 ++ [44] ++ encode value111 ++ [93]),([91] ++ encode value7 ++ [44] ++ encode value211 ++ [93]),([91] ++ encode value3 ++ [44] ++ encode value4 ++ [93]),([91] ++ encode value14 ++ [44] ++ encode value15 ++ [93]),([91] ++ encode value5 ++ [44] ++ encode value34 ++ [93]),([91] ++ encode value6 ++ [44] ++ encode value25 ++ [93]),([91] ++ encode value231 ++ [44] ++ encode value211 ++ [93]),([91] ++ encode value167 ++ [44] ++ encode value69 ++ [93]),([91] ++ encode value19 ++ [44] ++ encode value24 ++ [93]),([91] ++ encode value161 ++ [44] ++ encode value162 ++ [93]),([91] ++ encode value30 ++ [44] ++ encode value33 ++ [93])] ++ [93,93] = _
  simp only [encoded_value109,encoded_value35,encoded_value110,encoded_value111,encoded_value7,encoded_value211,encoded_value3,encoded_value4,encoded_value14,encoded_value15,encoded_value5,encoded_value34,encoded_value6,encoded_value25,encoded_value231,encoded_value167,encoded_value69,encoded_value19,encoded_value24,encoded_value161,encoded_value162,encoded_value30,encoded_value33]
  all_goals rfl
theorem order_value109_value7 : byteLess rawvalue109 rawvalue7 = true := by
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value109_value231 : byteLess rawvalue109 rawvalue231 = true := by
  simp only [rawvalue109,rawvalue231,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value110_value7 : byteLess rawvalue110 rawvalue7 = true := by
  simp only [rawvalue110,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value110_value231 : byteLess rawvalue110 rawvalue231 = true := by
  simp only [rawvalue110,rawvalue231,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value7_value3 : byteLess rawvalue7 rawvalue3 = true := by
  simp only [rawvalue7,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value7_value5 : byteLess rawvalue7 rawvalue5 = true := by
  simp only [rawvalue7,rawvalue5,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value7_value6 : byteLess rawvalue7 rawvalue6 = true := by
  simp only [rawvalue7,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value7_value231 : byteLess rawvalue7 rawvalue231 = true := by
  simp only [rawvalue7,rawvalue231,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value7_value167 : byteLess rawvalue7 rawvalue167 = true := by
  simp only [rawvalue7,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value7_value161 : byteLess rawvalue7 rawvalue161 = true := by
  simp only [rawvalue7,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value7_value30 : byteLess rawvalue7 rawvalue30 = true := by
  simp only [rawvalue7,rawvalue30,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value3_value231 : byteLess rawvalue3 rawvalue231 = true := by
  simp only [rawvalue3,rawvalue231,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value14_value231 : byteLess rawvalue14 rawvalue231 = true := by
  simp only [rawvalue14,rawvalue231,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value5_value231 : byteLess rawvalue5 rawvalue231 = true := by
  simp only [rawvalue5,rawvalue231,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value6_value231 : byteLess rawvalue6 rawvalue231 = true := by
  simp only [rawvalue6,rawvalue231,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value231_value167 : byteLess rawvalue231 rawvalue167 = true := by
  simp only [rawvalue231,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value231_value19 : byteLess rawvalue231 rawvalue19 = true := by
  simp only [rawvalue231,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value231_value161 : byteLess rawvalue231 rawvalue161 = true := by
  simp only [rawvalue231,rawvalue161,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value231_value30 : byteLess rawvalue231 rawvalue30 = true := by
  simp only [rawvalue231,rawvalue30,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value232 : nodes value232 = 2766 := by
  change 1 + (nodes value109 + nodes value35 + (nodes value110 + nodes value111 + (nodes value7 + nodes value211 + (nodes value3 + nodes value4 + (nodes value14 + nodes value15 + (nodes value5 + nodes value34 + (nodes value6 + nodes value25 + (nodes value231 + nodes value211 + (nodes value167 + nodes value69 + (nodes value19 + nodes value24 + (nodes value161 + nodes value162 + (nodes value30 + nodes value33 + 0)))))))))))) = 2766
  simp only [nodes_value109,nodes_value35,nodes_value110,nodes_value111,nodes_value7,nodes_value211,nodes_value3,nodes_value4,nodes_value14,nodes_value15,nodes_value5,nodes_value34,nodes_value6,nodes_value25,nodes_value231,nodes_value167,nodes_value69,nodes_value19,nodes_value24,nodes_value161,nodes_value162,nodes_value30,nodes_value33]
  all_goals decide +kernel
theorem depth_value232 : depth value232 = 10 := by
  change max (max (1 + depth value109) (1 + depth value35)) (max (max (1 + depth value110) (1 + depth value111)) (max (max (1 + depth value7) (1 + depth value211)) (max (max (1 + depth value3) (1 + depth value4)) (max (max (1 + depth value14) (1 + depth value15)) (max (max (1 + depth value5) (1 + depth value34)) (max (max (1 + depth value6) (1 + depth value25)) (max (max (1 + depth value231) (1 + depth value211)) (max (max (1 + depth value167) (1 + depth value69)) (max (max (1 + depth value19) (1 + depth value24)) (max (max (1 + depth value161) (1 + depth value162)) (max (max (1 + depth value30) (1 + depth value33)) (0)))))))))))) = 10
  simp only [depth_value109,depth_value35,depth_value110,depth_value111,depth_value7,depth_value211,depth_value3,depth_value4,depth_value14,depth_value15,depth_value5,depth_value34,depth_value6,depth_value25,depth_value231,depth_value167,depth_value69,depth_value19,depth_value24,depth_value161,depth_value162,depth_value30,depth_value33]
  all_goals decide +kernel
theorem canonical_value232 : canonical models value232 = true := by
  change ((canonical models value109 && canonical models value35 && (canonical models value110 && canonical models value111 && (canonical models value7 && canonical models value211 && (canonical models value3 && canonical models value4 && (canonical models value14 && canonical models value15 && (canonical models value5 && canonical models value34 && (canonical models value6 && canonical models value25 && (canonical models value231 && canonical models value211 && (canonical models value167 && canonical models value69 && (canonical models value19 && canonical models value24 && (canonical models value161 && canonical models value162 && (canonical models value30 && canonical models value33 && true)))))))))))) && ordered [encode value109,encode value110,encode value7,encode value3,encode value14,encode value5,encode value6,encode value231,encode value167,encode value19,encode value161,encode value30]) = true
  simp only [canonical_value109,canonical_value35,canonical_value110,canonical_value111,canonical_value7,canonical_value211,canonical_value3,canonical_value4,canonical_value14,canonical_value15,canonical_value5,canonical_value34,canonical_value6,canonical_value25,canonical_value231,canonical_value167,canonical_value69,canonical_value19,canonical_value24,canonical_value161,canonical_value162,canonical_value30,canonical_value33,encoded_value109,encoded_value110,encoded_value7,encoded_value3,encoded_value14,encoded_value5,encoded_value6,encoded_value231,encoded_value167,encoded_value19,encoded_value161,encoded_value30]
  simp only [ordered,List.all_cons,List.all_nil,order_value109_value110,order_value109_value7,order_value109_value3,order_value109_value14,order_value109_value5,order_value109_value6,order_value109_value231,order_value109_value167,order_value109_value19,order_value109_value161,order_value109_value30,order_value110_value7,order_value110_value3,order_value110_value14,order_value110_value5,order_value110_value6,order_value110_value231,order_value110_value167,order_value110_value19,order_value110_value161,order_value110_value30,order_value7_value3,order_value7_value14,order_value7_value5,order_value7_value6,order_value7_value231,order_value7_value167,order_value7_value19,order_value7_value161,order_value7_value30,order_value3_value14,order_value3_value5,order_value3_value6,order_value3_value231,order_value3_value167,order_value3_value19,order_value3_value161,order_value3_value30,order_value14_value5,order_value14_value6,order_value14_value231,order_value14_value167,order_value14_value19,order_value14_value161,order_value14_value30,order_value5_value6,order_value5_value231,order_value5_value167,order_value5_value19,order_value5_value161,order_value5_value30,order_value6_value231,order_value6_value167,order_value6_value19,order_value6_value161,order_value6_value30,order_value231_value167,order_value231_value19,order_value231_value161,order_value231_value30,order_value167_value19,order_value167_value161,order_value167_value30,order_value19_value161,order_value19_value30,order_value161_value30,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value232 : rawvalue232.length = 46712 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value109) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value35) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value110) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value111) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value7) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value211) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value3) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value4) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value14) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value15) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value5) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value34) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value6) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value25) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value231) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value211) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value167) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value69) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value19) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value24) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value161) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value162) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value30) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value33) (show ([93] : Bytes).length = 1 from by decide +kernel))))))))))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value233 : Value := .set (.cons value232 .nil)
noncomputable def rawvalue233 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue232] ++ [93,93]
theorem encoded_value233 : encode value233 = rawvalue233 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value232] ++ [93,93] = _
  simp only [encoded_value232]
  all_goals rfl
theorem nodes_value233 : nodes value233 = 2767 := by
  change 1 + (nodes value232 + 0) = 2767
  simp only [nodes_value232]
  all_goals decide +kernel
theorem depth_value233 : depth value233 = 11 := by
  change max (1 + depth value232) (0) = 11
  simp only [depth_value232]
  all_goals decide +kernel
theorem canonical_value233 : canonical models value233 = true := by
  change ((canonical models value232 && true) && ordered [encode value232]) = true
  simp only [canonical_value232,encoded_value232]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value233 : rawvalue233.length = 46722 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value232)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value234 : Value := .function (.cons value2 value232 (.cons value36 value40 .nil))
noncomputable def rawvalue234 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue232 ++ [93]),([91] ++ rawvalue36 ++ [44] ++ rawvalue40 ++ [93])] ++ [93,93]
theorem encoded_value234 : encode value234 = rawvalue234 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value232 ++ [93]),([91] ++ encode value36 ++ [44] ++ encode value40 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value232,encoded_value36,encoded_value40]
  all_goals rfl
theorem nodes_value234 : nodes value234 = 2773 := by
  change 1 + (nodes value2 + nodes value232 + (nodes value36 + nodes value40 + 0)) = 2773
  simp only [nodes_value2,nodes_value232,nodes_value36,nodes_value40]
  all_goals decide +kernel
theorem depth_value234 : depth value234 = 11 := by
  change max (max (1 + depth value2) (1 + depth value232)) (max (max (1 + depth value36) (1 + depth value40)) (0)) = 11
  simp only [depth_value2,depth_value232,depth_value36,depth_value40]
  all_goals decide +kernel
theorem canonical_value234 : canonical models value234 = true := by
  change ((canonical models value2 && canonical models value232 && (canonical models value36 && canonical models value40 && true)) && ordered [encode value2,encode value36]) = true
  simp only [canonical_value2,canonical_value232,canonical_value36,canonical_value40,encoded_value2,encoded_value36]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value36,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value234 : rawvalue234.length = 46814 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value232) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value36) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value40) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value235 : Value := .set (.cons value234 .nil)
noncomputable def rawvalue235 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue234] ++ [93,93]
theorem encoded_value235 : encode value235 = rawvalue235 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value234] ++ [93,93] = _
  simp only [encoded_value234]
  all_goals rfl
theorem nodes_value235 : nodes value235 = 2774 := by
  change 1 + (nodes value234 + 0) = 2774
  simp only [nodes_value234]
  all_goals decide +kernel
theorem depth_value235 : depth value235 = 12 := by
  change max (1 + depth value234) (0) = 12
  simp only [depth_value234]
  all_goals decide +kernel
theorem canonical_value235 : canonical models value235 = true := by
  change ((canonical models value234 && true) && ordered [encode value234]) = true
  simp only [canonical_value234,encoded_value234]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value235 : rawvalue235.length = 46824 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value234)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value236 : Value := .function (.cons value2 value232 (.cons value45 value37 .nil))
noncomputable def rawvalue236 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue232 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue37 ++ [93])] ++ [93,93]
theorem encoded_value236 : encode value236 = rawvalue236 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value232 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value37 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value232,encoded_value45,encoded_value37]
  all_goals rfl
theorem nodes_value236 : nodes value236 = 2770 := by
  change 1 + (nodes value2 + nodes value232 + (nodes value45 + nodes value37 + 0)) = 2770
  simp only [nodes_value2,nodes_value232,nodes_value45,nodes_value37]
  all_goals decide +kernel
theorem depth_value236 : depth value236 = 11 := by
  change max (max (1 + depth value2) (1 + depth value232)) (max (max (1 + depth value45) (1 + depth value37)) (0)) = 11
  simp only [depth_value2,depth_value232,depth_value45,depth_value37]
  all_goals decide +kernel
theorem canonical_value236 : canonical models value236 = true := by
  change ((canonical models value2 && canonical models value232 && (canonical models value45 && canonical models value37 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value232,canonical_value45,canonical_value37,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value236 : rawvalue236.length = 46776 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value232) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value37) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value237 : Value := .function (.cons value2 value232 (.cons value45 value38 .nil))
noncomputable def rawvalue237 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue232 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue38 ++ [93])] ++ [93,93]
theorem encoded_value237 : encode value237 = rawvalue237 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value232 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value38 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value232,encoded_value45,encoded_value38]
  all_goals rfl
theorem nodes_value237 : nodes value237 = 2770 := by
  change 1 + (nodes value2 + nodes value232 + (nodes value45 + nodes value38 + 0)) = 2770
  simp only [nodes_value2,nodes_value232,nodes_value45,nodes_value38]
  all_goals decide +kernel
theorem depth_value237 : depth value237 = 11 := by
  change max (max (1 + depth value2) (1 + depth value232)) (max (max (1 + depth value45) (1 + depth value38)) (0)) = 11
  simp only [depth_value2,depth_value232,depth_value45,depth_value38]
  all_goals decide +kernel
theorem canonical_value237 : canonical models value237 = true := by
  change ((canonical models value2 && canonical models value232 && (canonical models value45 && canonical models value38 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value232,canonical_value45,canonical_value38,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value237 : rawvalue237.length = 46776 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value232) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value38) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value238 : Value := .function (.cons value2 value232 (.cons value45 value39 .nil))
noncomputable def rawvalue238 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue232 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue39 ++ [93])] ++ [93,93]
theorem encoded_value238 : encode value238 = rawvalue238 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value232 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value39 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value232,encoded_value45,encoded_value39]
  all_goals rfl
theorem nodes_value238 : nodes value238 = 2770 := by
  change 1 + (nodes value2 + nodes value232 + (nodes value45 + nodes value39 + 0)) = 2770
  simp only [nodes_value2,nodes_value232,nodes_value45,nodes_value39]
  all_goals decide +kernel
theorem depth_value238 : depth value238 = 11 := by
  change max (max (1 + depth value2) (1 + depth value232)) (max (max (1 + depth value45) (1 + depth value39)) (0)) = 11
  simp only [depth_value2,depth_value232,depth_value45,depth_value39]
  all_goals decide +kernel
theorem canonical_value238 : canonical models value238 = true := by
  change ((canonical models value2 && canonical models value232 && (canonical models value45 && canonical models value39 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value232,canonical_value45,canonical_value39,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value238 : rawvalue238.length = 46776 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value232) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value39) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value239 : Value := .set (.cons value236 (.cons value237 (.cons value238 .nil)))
noncomputable def rawvalue239 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue236,rawvalue237,rawvalue238] ++ [93,93]
theorem encoded_value239 : encode value239 = rawvalue239 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value236,encode value237,encode value238] ++ [93,93] = _
  simp only [encoded_value236,encoded_value237,encoded_value238]
  all_goals rfl
theorem order_value236_value237 : byteLess rawvalue236 rawvalue237 = true := by
  simp only [rawvalue236,rawvalue237,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue38,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value236_value238 : byteLess rawvalue236 rawvalue238 = true := by
  simp only [rawvalue236,rawvalue238,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value237_value238 : byteLess rawvalue237 rawvalue238 = true := by
  simp only [rawvalue237,rawvalue238,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue38,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value239 : nodes value239 = 8311 := by
  change 1 + (nodes value236 + (nodes value237 + (nodes value238 + 0))) = 8311
  simp only [nodes_value236,nodes_value237,nodes_value238]
  all_goals decide +kernel
theorem depth_value239 : depth value239 = 12 := by
  change max (1 + depth value236) (max (1 + depth value237) (max (1 + depth value238) (0))) = 12
  simp only [depth_value236,depth_value237,depth_value238]
  all_goals decide +kernel
theorem canonical_value239 : canonical models value239 = true := by
  change ((canonical models value236 && (canonical models value237 && (canonical models value238 && true))) && ordered [encode value236,encode value237,encode value238]) = true
  simp only [canonical_value236,canonical_value237,canonical_value238,encoded_value236,encoded_value237,encoded_value238]
  simp only [ordered,List.all_cons,List.all_nil,order_value236_value237,order_value236_value238,order_value237_value238,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value239 : rawvalue239.length = 140340 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value236 (commaConsLength rawLength_value237 (commaSingletonLength rawLength_value238)))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value240 : Value := .text "aggregate"
noncomputable def rawvalue240 : Bytes := asciiBytes "[\"str\",\"aggregate\"]"
theorem encoded_value240 : encode value240 = rawvalue240 := by
  all_goals rfl
theorem nodes_value240 : nodes value240 = 1 := by rfl
theorem depth_value240 : depth value240 = 0 := by rfl
theorem canonical_value240 : canonical models value240 = true := by decide +kernel
theorem rawLength_value240 : rawvalue240.length = 19 := by
  decide +kernel
noncomputable def value241 : Value := .text "nextCheckpoint"
noncomputable def rawvalue241 : Bytes := asciiBytes "[\"str\",\"nextCheckpoint\"]"
theorem encoded_value241 : encode value241 = rawvalue241 := by
  all_goals rfl
theorem nodes_value241 : nodes value241 = 1 := by rfl
theorem depth_value241 : depth value241 = 0 := by rfl
theorem canonical_value241 : canonical models value241 = true := by decide +kernel
theorem rawLength_value241 : rawvalue241.length = 24 := by
  decide +kernel
noncomputable def value242 : Value := .model "next1"
noncomputable def rawvalue242 : Bytes := asciiBytes "[\"model\",\"next1\"]"
theorem encoded_value242 : encode value242 = rawvalue242 := by
  all_goals rfl
theorem nodes_value242 : nodes value242 = 1 := by rfl
theorem depth_value242 : depth value242 = 0 := by rfl
theorem canonical_value242 : canonical models value242 = true := by decide +kernel
theorem rawLength_value242 : rawvalue242.length = 17 := by
  decide +kernel
noncomputable def value243 : Value := .text "nextModelHash"
noncomputable def rawvalue243 : Bytes := asciiBytes "[\"str\",\"nextModelHash\"]"
theorem encoded_value243 : encode value243 = rawvalue243 := by
  all_goals rfl
theorem nodes_value243 : nodes value243 = 1 := by rfl
theorem depth_value243 : depth value243 = 0 := by rfl
theorem canonical_value243 : canonical models value243 = true := by decide +kernel
theorem rawLength_value243 : rawvalue243.length = 23 := by
  decide +kernel
noncomputable def value244 : Value := .integer (-19)
noncomputable def rawvalue244 : Bytes := asciiBytes "[\"int\",\"-19\"]"
theorem encoded_value244 : encode value244 = rawvalue244 := by
  all_goals rfl
theorem nodes_value244 : nodes value244 = 1 := by rfl
theorem depth_value244 : depth value244 = 0 := by rfl
theorem canonical_value244 : canonical models value244 = true := by decide +kernel
theorem rawLength_value244 : rawvalue244.length = 13 := by
  decide +kernel
noncomputable def value245 : Value := .function (.cons value51 value196 (.cons value55 value244 .nil))
noncomputable def rawvalue245 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue51 ++ [44] ++ rawvalue196 ++ [93]),([91] ++ rawvalue55 ++ [44] ++ rawvalue244 ++ [93])] ++ [93,93]
theorem encoded_value245 : encode value245 = rawvalue245 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value51 ++ [44] ++ encode value196 ++ [93]),([91] ++ encode value55 ++ [44] ++ encode value244 ++ [93])] ++ [93,93] = _
  simp only [encoded_value51,encoded_value196,encoded_value55,encoded_value244]
  all_goals rfl
theorem nodes_value245 : nodes value245 = 5 := by
  change 1 + (nodes value51 + nodes value196 + (nodes value55 + nodes value244 + 0)) = 5
  simp only [nodes_value51,nodes_value196,nodes_value55,nodes_value244]
  all_goals decide +kernel
theorem depth_value245 : depth value245 = 1 := by
  change max (max (1 + depth value51) (1 + depth value196)) (max (max (1 + depth value55) (1 + depth value244)) (0)) = 1
  simp only [depth_value51,depth_value196,depth_value55,depth_value244]
  all_goals decide +kernel
theorem canonical_value245 : canonical models value245 = true := by
  change ((canonical models value51 && canonical models value196 && (canonical models value55 && canonical models value244 && true)) && ordered [encode value51,encode value55]) = true
  simp only [canonical_value51,canonical_value196,canonical_value55,canonical_value244,encoded_value51,encoded_value55]
  simp only [ordered,List.all_cons,List.all_nil,order_value51_value55,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value245 : rawvalue245.length = 78 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value51) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value196) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value55) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value244) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value246 : Value := .function (.cons value73 value160 (.cons value161 value162 (.cons value163 value245 .nil)))
noncomputable def rawvalue246 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue73 ++ [44] ++ rawvalue160 ++ [93]),([91] ++ rawvalue161 ++ [44] ++ rawvalue162 ++ [93]),([91] ++ rawvalue163 ++ [44] ++ rawvalue245 ++ [93])] ++ [93,93]
theorem encoded_value246 : encode value246 = rawvalue246 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value73 ++ [44] ++ encode value160 ++ [93]),([91] ++ encode value161 ++ [44] ++ encode value162 ++ [93]),([91] ++ encode value163 ++ [44] ++ encode value245 ++ [93])] ++ [93,93] = _
  simp only [encoded_value73,encoded_value160,encoded_value161,encoded_value162,encoded_value163,encoded_value245]
  all_goals rfl
theorem nodes_value246 : nodes value246 = 11 := by
  change 1 + (nodes value73 + nodes value160 + (nodes value161 + nodes value162 + (nodes value163 + nodes value245 + 0))) = 11
  simp only [nodes_value73,nodes_value160,nodes_value161,nodes_value162,nodes_value163,nodes_value245]
  all_goals decide +kernel
theorem depth_value246 : depth value246 = 2 := by
  change max (max (1 + depth value73) (1 + depth value160)) (max (max (1 + depth value161) (1 + depth value162)) (max (max (1 + depth value163) (1 + depth value245)) (0))) = 2
  simp only [depth_value73,depth_value160,depth_value161,depth_value162,depth_value163,depth_value245]
  all_goals decide +kernel
theorem canonical_value246 : canonical models value246 = true := by
  change ((canonical models value73 && canonical models value160 && (canonical models value161 && canonical models value162 && (canonical models value163 && canonical models value245 && true))) && ordered [encode value73,encode value161,encode value163]) = true
  simp only [canonical_value73,canonical_value160,canonical_value161,canonical_value162,canonical_value163,canonical_value245,encoded_value73,encoded_value161,encoded_value163]
  simp only [ordered,List.all_cons,List.all_nil,order_value73_value161,order_value73_value163,order_value161_value163,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value246 : rawvalue246.length = 179 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value160) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value161) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value162) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value163) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value245) (show ([93] : Bytes).length = 1 from by decide +kernel)))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value247 : Value := .text "nextOptimizerHash"
noncomputable def rawvalue247 : Bytes := asciiBytes "[\"str\",\"nextOptimizerHash\"]"
theorem encoded_value247 : encode value247 = rawvalue247 := by
  all_goals rfl
theorem nodes_value247 : nodes value247 = 1 := by rfl
theorem depth_value247 : depth value247 = 0 := by rfl
theorem canonical_value247 : canonical models value247 = true := by decide +kernel
theorem rawLength_value247 : rawvalue247.length = 27 := by
  decide +kernel
noncomputable def value248 : Value := .function (.cons value240 value232 (.cons value113 value114 (.cons value112 value169 (.cons value170 value171 (.cons value14 value15 (.cons value241 value242 (.cons value243 value246 (.cons value247 value166 (.cons value167 value69 (.cons value19 value24 .nil))))))))))
noncomputable def rawvalue248 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue240 ++ [44] ++ rawvalue232 ++ [93]),([91] ++ rawvalue113 ++ [44] ++ rawvalue114 ++ [93]),([91] ++ rawvalue112 ++ [44] ++ rawvalue169 ++ [93]),([91] ++ rawvalue170 ++ [44] ++ rawvalue171 ++ [93]),([91] ++ rawvalue14 ++ [44] ++ rawvalue15 ++ [93]),([91] ++ rawvalue241 ++ [44] ++ rawvalue242 ++ [93]),([91] ++ rawvalue243 ++ [44] ++ rawvalue246 ++ [93]),([91] ++ rawvalue247 ++ [44] ++ rawvalue166 ++ [93]),([91] ++ rawvalue167 ++ [44] ++ rawvalue69 ++ [93]),([91] ++ rawvalue19 ++ [44] ++ rawvalue24 ++ [93])] ++ [93,93]
theorem encoded_value248 : encode value248 = rawvalue248 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value240 ++ [44] ++ encode value232 ++ [93]),([91] ++ encode value113 ++ [44] ++ encode value114 ++ [93]),([91] ++ encode value112 ++ [44] ++ encode value169 ++ [93]),([91] ++ encode value170 ++ [44] ++ encode value171 ++ [93]),([91] ++ encode value14 ++ [44] ++ encode value15 ++ [93]),([91] ++ encode value241 ++ [44] ++ encode value242 ++ [93]),([91] ++ encode value243 ++ [44] ++ encode value246 ++ [93]),([91] ++ encode value247 ++ [44] ++ encode value166 ++ [93]),([91] ++ encode value167 ++ [44] ++ encode value69 ++ [93]),([91] ++ encode value19 ++ [44] ++ encode value24 ++ [93])] ++ [93,93] = _
  simp only [encoded_value240,encoded_value232,encoded_value113,encoded_value114,encoded_value112,encoded_value169,encoded_value170,encoded_value171,encoded_value14,encoded_value15,encoded_value241,encoded_value242,encoded_value243,encoded_value246,encoded_value247,encoded_value166,encoded_value167,encoded_value69,encoded_value19,encoded_value24]
  all_goals rfl
theorem order_value240_value113 : byteLess rawvalue240 rawvalue113 = true := by
  simp only [rawvalue240,rawvalue113,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value240_value112 : byteLess rawvalue240 rawvalue112 = true := by
  simp only [rawvalue240,rawvalue112,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value240_value170 : byteLess rawvalue240 rawvalue170 = true := by
  simp only [rawvalue240,rawvalue170,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value240_value14 : byteLess rawvalue240 rawvalue14 = true := by
  simp only [rawvalue240,rawvalue14,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value240_value241 : byteLess rawvalue240 rawvalue241 = true := by
  simp only [rawvalue240,rawvalue241,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value240_value243 : byteLess rawvalue240 rawvalue243 = true := by
  simp only [rawvalue240,rawvalue243,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value240_value247 : byteLess rawvalue240 rawvalue247 = true := by
  simp only [rawvalue240,rawvalue247,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value240_value167 : byteLess rawvalue240 rawvalue167 = true := by
  simp only [rawvalue240,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value240_value19 : byteLess rawvalue240 rawvalue19 = true := by
  simp only [rawvalue240,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value113_value112 : byteLess rawvalue113 rawvalue112 = true := by
  simp only [rawvalue113,rawvalue112,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value113_value170 : byteLess rawvalue113 rawvalue170 = true := by
  simp only [rawvalue113,rawvalue170,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value113_value14 : byteLess rawvalue113 rawvalue14 = true := by
  simp only [rawvalue113,rawvalue14,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value113_value241 : byteLess rawvalue113 rawvalue241 = true := by
  simp only [rawvalue113,rawvalue241,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value113_value243 : byteLess rawvalue113 rawvalue243 = true := by
  simp only [rawvalue113,rawvalue243,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value113_value247 : byteLess rawvalue113 rawvalue247 = true := by
  simp only [rawvalue113,rawvalue247,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value113_value19 : byteLess rawvalue113 rawvalue19 = true := by
  simp only [rawvalue113,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value112_value241 : byteLess rawvalue112 rawvalue241 = true := by
  simp only [rawvalue112,rawvalue241,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value112_value243 : byteLess rawvalue112 rawvalue243 = true := by
  simp only [rawvalue112,rawvalue243,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value112_value247 : byteLess rawvalue112 rawvalue247 = true := by
  simp only [rawvalue112,rawvalue247,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value170_value241 : byteLess rawvalue170 rawvalue241 = true := by
  simp only [rawvalue170,rawvalue241,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value170_value243 : byteLess rawvalue170 rawvalue243 = true := by
  simp only [rawvalue170,rawvalue243,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value170_value247 : byteLess rawvalue170 rawvalue247 = true := by
  simp only [rawvalue170,rawvalue247,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value14_value241 : byteLess rawvalue14 rawvalue241 = true := by
  simp only [rawvalue14,rawvalue241,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value14_value243 : byteLess rawvalue14 rawvalue243 = true := by
  simp only [rawvalue14,rawvalue243,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value14_value247 : byteLess rawvalue14 rawvalue247 = true := by
  simp only [rawvalue14,rawvalue247,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value241_value243 : byteLess rawvalue241 rawvalue243 = true := by
  simp only [rawvalue241,rawvalue243,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value241_value247 : byteLess rawvalue241 rawvalue247 = true := by
  simp only [rawvalue241,rawvalue247,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value241_value167 : byteLess rawvalue241 rawvalue167 = true := by
  simp only [rawvalue241,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value241_value19 : byteLess rawvalue241 rawvalue19 = true := by
  simp only [rawvalue241,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value243_value247 : byteLess rawvalue243 rawvalue247 = true := by
  simp only [rawvalue243,rawvalue247,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value243_value167 : byteLess rawvalue243 rawvalue167 = true := by
  simp only [rawvalue243,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value243_value19 : byteLess rawvalue243 rawvalue19 = true := by
  simp only [rawvalue243,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value247_value167 : byteLess rawvalue247 rawvalue167 = true := by
  simp only [rawvalue247,rawvalue167,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value247_value19 : byteLess rawvalue247 rawvalue19 = true := by
  simp only [rawvalue247,rawvalue19,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value248 : nodes value248 = 3153 := by
  change 1 + (nodes value240 + nodes value232 + (nodes value113 + nodes value114 + (nodes value112 + nodes value169 + (nodes value170 + nodes value171 + (nodes value14 + nodes value15 + (nodes value241 + nodes value242 + (nodes value243 + nodes value246 + (nodes value247 + nodes value166 + (nodes value167 + nodes value69 + (nodes value19 + nodes value24 + 0)))))))))) = 3153
  simp only [nodes_value240,nodes_value232,nodes_value113,nodes_value114,nodes_value112,nodes_value169,nodes_value170,nodes_value171,nodes_value14,nodes_value15,nodes_value241,nodes_value242,nodes_value243,nodes_value246,nodes_value247,nodes_value166,nodes_value167,nodes_value69,nodes_value19,nodes_value24]
  all_goals decide +kernel
theorem depth_value248 : depth value248 = 11 := by
  change max (max (1 + depth value240) (1 + depth value232)) (max (max (1 + depth value113) (1 + depth value114)) (max (max (1 + depth value112) (1 + depth value169)) (max (max (1 + depth value170) (1 + depth value171)) (max (max (1 + depth value14) (1 + depth value15)) (max (max (1 + depth value241) (1 + depth value242)) (max (max (1 + depth value243) (1 + depth value246)) (max (max (1 + depth value247) (1 + depth value166)) (max (max (1 + depth value167) (1 + depth value69)) (max (max (1 + depth value19) (1 + depth value24)) (0)))))))))) = 11
  simp only [depth_value240,depth_value232,depth_value113,depth_value114,depth_value112,depth_value169,depth_value170,depth_value171,depth_value14,depth_value15,depth_value241,depth_value242,depth_value243,depth_value246,depth_value247,depth_value166,depth_value167,depth_value69,depth_value19,depth_value24]
  all_goals decide +kernel
theorem canonical_value248 : canonical models value248 = true := by
  change ((canonical models value240 && canonical models value232 && (canonical models value113 && canonical models value114 && (canonical models value112 && canonical models value169 && (canonical models value170 && canonical models value171 && (canonical models value14 && canonical models value15 && (canonical models value241 && canonical models value242 && (canonical models value243 && canonical models value246 && (canonical models value247 && canonical models value166 && (canonical models value167 && canonical models value69 && (canonical models value19 && canonical models value24 && true)))))))))) && ordered [encode value240,encode value113,encode value112,encode value170,encode value14,encode value241,encode value243,encode value247,encode value167,encode value19]) = true
  simp only [canonical_value240,canonical_value232,canonical_value113,canonical_value114,canonical_value112,canonical_value169,canonical_value170,canonical_value171,canonical_value14,canonical_value15,canonical_value241,canonical_value242,canonical_value243,canonical_value246,canonical_value247,canonical_value166,canonical_value167,canonical_value69,canonical_value19,canonical_value24,encoded_value240,encoded_value113,encoded_value112,encoded_value170,encoded_value14,encoded_value241,encoded_value243,encoded_value247,encoded_value167,encoded_value19]
  simp only [ordered,List.all_cons,List.all_nil,order_value240_value113,order_value240_value112,order_value240_value170,order_value240_value14,order_value240_value241,order_value240_value243,order_value240_value247,order_value240_value167,order_value240_value19,order_value113_value112,order_value113_value170,order_value113_value14,order_value113_value241,order_value113_value243,order_value113_value247,order_value113_value167,order_value113_value19,order_value112_value170,order_value112_value14,order_value112_value241,order_value112_value243,order_value112_value247,order_value112_value167,order_value112_value19,order_value170_value14,order_value170_value241,order_value170_value243,order_value170_value247,order_value170_value167,order_value170_value19,order_value14_value241,order_value14_value243,order_value14_value247,order_value14_value167,order_value14_value19,order_value241_value243,order_value241_value247,order_value241_value167,order_value241_value19,order_value243_value247,order_value243_value167,order_value243_value19,order_value247_value167,order_value247_value19,order_value167_value19,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value248 : rawvalue248.length = 53186 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value240) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value232) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value113) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value114) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value112) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value169) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value170) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value171) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value14) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value15) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value241) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value242) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value243) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value246) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value247) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value166) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value167) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value69) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value19) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value24) (show ([93] : Bytes).length = 1 from by decide +kernel))))))))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value249 : Value := .set (.cons value248 .nil)
noncomputable def rawvalue249 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue248] ++ [93,93]
theorem encoded_value249 : encode value249 = rawvalue249 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value248] ++ [93,93] = _
  simp only [encoded_value248]
  all_goals rfl
theorem nodes_value249 : nodes value249 = 3154 := by
  change 1 + (nodes value248 + 0) = 3154
  simp only [nodes_value248]
  all_goals decide +kernel
theorem depth_value249 : depth value249 = 12 := by
  change max (1 + depth value248) (0) = 12
  simp only [depth_value248]
  all_goals decide +kernel
theorem canonical_value249 : canonical models value249 = true := by
  change ((canonical models value248 && true) && ordered [encode value248]) = true
  simp only [canonical_value248,encoded_value248]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value249 : rawvalue249.length = 53196 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value248)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value250 : Value := .integer (7)
noncomputable def rawvalue250 : Bytes := asciiBytes "[\"int\",\"7\"]"
theorem encoded_value250 : encode value250 = rawvalue250 := by
  all_goals rfl
theorem nodes_value250 : nodes value250 = 1 := by rfl
theorem depth_value250 : depth value250 = 0 := by rfl
theorem canonical_value250 : canonical models value250 = true := by decide +kernel
theorem rawLength_value250 : rawvalue250.length = 11 := by
  decide +kernel
noncomputable def value251 : Value := .function (.cons value37 value250 (.cons value38 value250 (.cons value39 value250 (.cons value43 value64 .nil))))
noncomputable def rawvalue251 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue37 ++ [44] ++ rawvalue250 ++ [93]),([91] ++ rawvalue38 ++ [44] ++ rawvalue250 ++ [93]),([91] ++ rawvalue39 ++ [44] ++ rawvalue250 ++ [93]),([91] ++ rawvalue43 ++ [44] ++ rawvalue64 ++ [93])] ++ [93,93]
theorem encoded_value251 : encode value251 = rawvalue251 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value37 ++ [44] ++ encode value250 ++ [93]),([91] ++ encode value38 ++ [44] ++ encode value250 ++ [93]),([91] ++ encode value39 ++ [44] ++ encode value250 ++ [93]),([91] ++ encode value43 ++ [44] ++ encode value64 ++ [93])] ++ [93,93] = _
  simp only [encoded_value37,encoded_value250,encoded_value38,encoded_value39,encoded_value43,encoded_value64]
  all_goals rfl
theorem nodes_value251 : nodes value251 = 9 := by
  change 1 + (nodes value37 + nodes value250 + (nodes value38 + nodes value250 + (nodes value39 + nodes value250 + (nodes value43 + nodes value64 + 0)))) = 9
  simp only [nodes_value37,nodes_value250,nodes_value38,nodes_value39,nodes_value43,nodes_value64]
  all_goals decide +kernel
theorem depth_value251 : depth value251 = 1 := by
  change max (max (1 + depth value37) (1 + depth value250)) (max (max (1 + depth value38) (1 + depth value250)) (max (max (1 + depth value39) (1 + depth value250)) (max (max (1 + depth value43) (1 + depth value64)) (0)))) = 1
  simp only [depth_value37,depth_value250,depth_value38,depth_value39,depth_value43,depth_value64]
  all_goals decide +kernel
theorem canonical_value251 : canonical models value251 = true := by
  change ((canonical models value37 && canonical models value250 && (canonical models value38 && canonical models value250 && (canonical models value39 && canonical models value250 && (canonical models value43 && canonical models value64 && true)))) && ordered [encode value37,encode value38,encode value39,encode value43]) = true
  simp only [canonical_value37,canonical_value250,canonical_value38,canonical_value39,canonical_value43,canonical_value64,encoded_value37,encoded_value38,encoded_value39,encoded_value43]
  simp only [ordered,List.all_cons,List.all_nil,order_value37_value38,order_value37_value39,order_value37_value43,order_value38_value39,order_value38_value43,order_value39_value43,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value251 : rawvalue251.length = 125 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value37) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value250) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value38) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value250) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value39) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value250) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value43) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value64) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value252 : Value := .text "AGGREGATE_ROOT"
noncomputable def rawvalue252 : Bytes := asciiBytes "[\"str\",\"AGGREGATE_ROOT\"]"
theorem encoded_value252 : encode value252 = rawvalue252 := by
  all_goals rfl
theorem nodes_value252 : nodes value252 = 1 := by rfl
theorem depth_value252 : depth value252 = 0 := by rfl
theorem canonical_value252 : canonical models value252 = true := by decide +kernel
theorem rawLength_value252 : rawvalue252.length = 24 := by
  decide +kernel
noncomputable def value253 : Value := .function (.cons value2 value232 (.cons value72 value35 (.cons value73 value252 (.cons value45 value37 .nil))))
noncomputable def rawvalue253 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue232 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue35 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue252 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue37 ++ [93])] ++ [93,93]
theorem encoded_value253 : encode value253 = rawvalue253 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value232 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value35 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value252 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value37 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value232,encoded_value72,encoded_value35,encoded_value73,encoded_value252,encoded_value45,encoded_value37]
  all_goals rfl
theorem nodes_value253 : nodes value253 = 2902 := by
  change 1 + (nodes value2 + nodes value232 + (nodes value72 + nodes value35 + (nodes value73 + nodes value252 + (nodes value45 + nodes value37 + 0)))) = 2902
  simp only [nodes_value2,nodes_value232,nodes_value72,nodes_value35,nodes_value73,nodes_value252,nodes_value45,nodes_value37]
  all_goals decide +kernel
theorem depth_value253 : depth value253 = 11 := by
  change max (max (1 + depth value2) (1 + depth value232)) (max (max (1 + depth value72) (1 + depth value35)) (max (max (1 + depth value73) (1 + depth value252)) (max (max (1 + depth value45) (1 + depth value37)) (0)))) = 11
  simp only [depth_value2,depth_value232,depth_value72,depth_value35,depth_value73,depth_value252,depth_value45,depth_value37]
  all_goals decide +kernel
theorem canonical_value253 : canonical models value253 = true := by
  change ((canonical models value2 && canonical models value232 && (canonical models value72 && canonical models value35 && (canonical models value73 && canonical models value252 && (canonical models value45 && canonical models value37 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value232,canonical_value72,canonical_value35,canonical_value73,canonical_value252,canonical_value45,canonical_value37,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value253 : rawvalue253.length = 49040 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value232) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value35) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value252) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value37) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value254 : Value := .function (.cons value2 value232 (.cons value72 value35 (.cons value73 value252 (.cons value45 value38 .nil))))
noncomputable def rawvalue254 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue232 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue35 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue252 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue38 ++ [93])] ++ [93,93]
theorem encoded_value254 : encode value254 = rawvalue254 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value232 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value35 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value252 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value38 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value232,encoded_value72,encoded_value35,encoded_value73,encoded_value252,encoded_value45,encoded_value38]
  all_goals rfl
theorem nodes_value254 : nodes value254 = 2902 := by
  change 1 + (nodes value2 + nodes value232 + (nodes value72 + nodes value35 + (nodes value73 + nodes value252 + (nodes value45 + nodes value38 + 0)))) = 2902
  simp only [nodes_value2,nodes_value232,nodes_value72,nodes_value35,nodes_value73,nodes_value252,nodes_value45,nodes_value38]
  all_goals decide +kernel
theorem depth_value254 : depth value254 = 11 := by
  change max (max (1 + depth value2) (1 + depth value232)) (max (max (1 + depth value72) (1 + depth value35)) (max (max (1 + depth value73) (1 + depth value252)) (max (max (1 + depth value45) (1 + depth value38)) (0)))) = 11
  simp only [depth_value2,depth_value232,depth_value72,depth_value35,depth_value73,depth_value252,depth_value45,depth_value38]
  all_goals decide +kernel
theorem canonical_value254 : canonical models value254 = true := by
  change ((canonical models value2 && canonical models value232 && (canonical models value72 && canonical models value35 && (canonical models value73 && canonical models value252 && (canonical models value45 && canonical models value38 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value232,canonical_value72,canonical_value35,canonical_value73,canonical_value252,canonical_value45,canonical_value38,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value254 : rawvalue254.length = 49040 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value232) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value35) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value252) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value38) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value255 : Value := .function (.cons value2 value232 (.cons value72 value35 (.cons value73 value252 (.cons value45 value39 .nil))))
noncomputable def rawvalue255 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue232 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue35 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue252 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue39 ++ [93])] ++ [93,93]
theorem encoded_value255 : encode value255 = rawvalue255 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value232 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value35 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value252 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value39 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value232,encoded_value72,encoded_value35,encoded_value73,encoded_value252,encoded_value45,encoded_value39]
  all_goals rfl
theorem nodes_value255 : nodes value255 = 2902 := by
  change 1 + (nodes value2 + nodes value232 + (nodes value72 + nodes value35 + (nodes value73 + nodes value252 + (nodes value45 + nodes value39 + 0)))) = 2902
  simp only [nodes_value2,nodes_value232,nodes_value72,nodes_value35,nodes_value73,nodes_value252,nodes_value45,nodes_value39]
  all_goals decide +kernel
theorem depth_value255 : depth value255 = 11 := by
  change max (max (1 + depth value2) (1 + depth value232)) (max (max (1 + depth value72) (1 + depth value35)) (max (max (1 + depth value73) (1 + depth value252)) (max (max (1 + depth value45) (1 + depth value39)) (0)))) = 11
  simp only [depth_value2,depth_value232,depth_value72,depth_value35,depth_value73,depth_value252,depth_value45,depth_value39]
  all_goals decide +kernel
theorem canonical_value255 : canonical models value255 = true := by
  change ((canonical models value2 && canonical models value232 && (canonical models value72 && canonical models value35 && (canonical models value73 && canonical models value252 && (canonical models value45 && canonical models value39 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value232,canonical_value72,canonical_value35,canonical_value73,canonical_value252,canonical_value45,canonical_value39,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value255 : rawvalue255.length = 49040 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value232) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value35) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value252) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value39) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value256 : Value := .set (.cons value192 (.cons value198 (.cons value203 (.cons value215 (.cons value221 (.cons value227 (.cons value253 (.cons value254 (.cons value255 (.cons value75 (.cons value76 (.cons value77 (.cons value79 (.cons value80 (.cons value81 (.cons value83 (.cons value84 (.cons value85 (.cons value88 (.cons value89 (.cons value90 .nil)))))))))))))))))))))
noncomputable def rawvalue256 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue192,rawvalue198,rawvalue203,rawvalue215,rawvalue221,rawvalue227,rawvalue253,rawvalue254,rawvalue255,rawvalue75,rawvalue76,rawvalue77,rawvalue79,rawvalue80,rawvalue81,rawvalue83,rawvalue84,rawvalue85,rawvalue88,rawvalue89,rawvalue90] ++ [93,93]
theorem encoded_value256 : encode value256 = rawvalue256 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value192,encode value198,encode value203,encode value215,encode value221,encode value227,encode value253,encode value254,encode value255,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90] ++ [93,93] = _
  simp only [encoded_value192,encoded_value198,encoded_value203,encoded_value215,encoded_value221,encoded_value227,encoded_value253,encoded_value254,encoded_value255,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  all_goals rfl
theorem order_value192_value253 : byteLess rawvalue192 rawvalue253 = true := by
  simp only [rawvalue192,rawvalue253,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue112,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value192_value254 : byteLess rawvalue192 rawvalue254 = true := by
  simp only [rawvalue192,rawvalue254,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue112,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value192_value255 : byteLess rawvalue192 rawvalue255 = true := by
  simp only [rawvalue192,rawvalue255,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue112,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value253 : byteLess rawvalue198 rawvalue253 = true := by
  simp only [rawvalue198,rawvalue253,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue112,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value254 : byteLess rawvalue198 rawvalue254 = true := by
  simp only [rawvalue198,rawvalue254,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue112,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value198_value255 : byteLess rawvalue198 rawvalue255 = true := by
  simp only [rawvalue198,rawvalue255,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue112,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value203_value253 : byteLess rawvalue203 rawvalue253 = true := by
  simp only [rawvalue203,rawvalue253,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue112,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value203_value254 : byteLess rawvalue203 rawvalue254 = true := by
  simp only [rawvalue203,rawvalue254,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue112,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value203_value255 : byteLess rawvalue203 rawvalue255 = true := by
  simp only [rawvalue203,rawvalue255,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue112,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value215_value253 : byteLess rawvalue215 rawvalue253 = true := by
  simp only [rawvalue215,rawvalue253,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue112,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value215_value254 : byteLess rawvalue215 rawvalue254 = true := by
  simp only [rawvalue215,rawvalue254,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue112,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value215_value255 : byteLess rawvalue215 rawvalue255 = true := by
  simp only [rawvalue215,rawvalue255,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue112,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value221_value253 : byteLess rawvalue221 rawvalue253 = true := by
  simp only [rawvalue221,rawvalue253,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue112,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value221_value254 : byteLess rawvalue221 rawvalue254 = true := by
  simp only [rawvalue221,rawvalue254,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue112,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value221_value255 : byteLess rawvalue221 rawvalue255 = true := by
  simp only [rawvalue221,rawvalue255,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue112,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value227_value253 : byteLess rawvalue227 rawvalue253 = true := by
  simp only [rawvalue227,rawvalue253,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue112,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value227_value254 : byteLess rawvalue227 rawvalue254 = true := by
  simp only [rawvalue227,rawvalue254,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue112,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value227_value255 : byteLess rawvalue227 rawvalue255 = true := by
  simp only [rawvalue227,rawvalue255,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue210,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue112,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value253_value254 : byteLess rawvalue253 rawvalue254 = true := by
  simp only [rawvalue253,rawvalue254,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue38,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value253_value255 : byteLess rawvalue253 rawvalue255 = true := by
  simp only [rawvalue253,rawvalue255,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value253_value75 : byteLess rawvalue253 rawvalue75 = true := by
  simp only [rawvalue253,rawvalue75,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value253_value76 : byteLess rawvalue253 rawvalue76 = true := by
  simp only [rawvalue253,rawvalue76,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value253_value77 : byteLess rawvalue253 rawvalue77 = true := by
  simp only [rawvalue253,rawvalue77,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value253_value79 : byteLess rawvalue253 rawvalue79 = true := by
  simp only [rawvalue253,rawvalue79,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value253_value80 : byteLess rawvalue253 rawvalue80 = true := by
  simp only [rawvalue253,rawvalue80,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value253_value81 : byteLess rawvalue253 rawvalue81 = true := by
  simp only [rawvalue253,rawvalue81,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value253_value83 : byteLess rawvalue253 rawvalue83 = true := by
  simp only [rawvalue253,rawvalue83,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value253_value84 : byteLess rawvalue253 rawvalue84 = true := by
  simp only [rawvalue253,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value253_value85 : byteLess rawvalue253 rawvalue85 = true := by
  simp only [rawvalue253,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value253_value88 : byteLess rawvalue253 rawvalue88 = true := by
  simp only [rawvalue253,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value253_value89 : byteLess rawvalue253 rawvalue89 = true := by
  simp only [rawvalue253,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value253_value90 : byteLess rawvalue253 rawvalue90 = true := by
  simp only [rawvalue253,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value254_value255 : byteLess rawvalue254 rawvalue255 = true := by
  simp only [rawvalue254,rawvalue255,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue38,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value254_value75 : byteLess rawvalue254 rawvalue75 = true := by
  simp only [rawvalue254,rawvalue75,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value254_value76 : byteLess rawvalue254 rawvalue76 = true := by
  simp only [rawvalue254,rawvalue76,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value254_value77 : byteLess rawvalue254 rawvalue77 = true := by
  simp only [rawvalue254,rawvalue77,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value254_value79 : byteLess rawvalue254 rawvalue79 = true := by
  simp only [rawvalue254,rawvalue79,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value254_value80 : byteLess rawvalue254 rawvalue80 = true := by
  simp only [rawvalue254,rawvalue80,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value254_value81 : byteLess rawvalue254 rawvalue81 = true := by
  simp only [rawvalue254,rawvalue81,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value254_value83 : byteLess rawvalue254 rawvalue83 = true := by
  simp only [rawvalue254,rawvalue83,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value254_value84 : byteLess rawvalue254 rawvalue84 = true := by
  simp only [rawvalue254,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value254_value85 : byteLess rawvalue254 rawvalue85 = true := by
  simp only [rawvalue254,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value254_value88 : byteLess rawvalue254 rawvalue88 = true := by
  simp only [rawvalue254,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value254_value89 : byteLess rawvalue254 rawvalue89 = true := by
  simp only [rawvalue254,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value254_value90 : byteLess rawvalue254 rawvalue90 = true := by
  simp only [rawvalue254,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value255_value75 : byteLess rawvalue255 rawvalue75 = true := by
  simp only [rawvalue255,rawvalue75,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value255_value76 : byteLess rawvalue255 rawvalue76 = true := by
  simp only [rawvalue255,rawvalue76,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value255_value77 : byteLess rawvalue255 rawvalue77 = true := by
  simp only [rawvalue255,rawvalue77,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value255_value79 : byteLess rawvalue255 rawvalue79 = true := by
  simp only [rawvalue255,rawvalue79,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value255_value80 : byteLess rawvalue255 rawvalue80 = true := by
  simp only [rawvalue255,rawvalue80,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value255_value81 : byteLess rawvalue255 rawvalue81 = true := by
  simp only [rawvalue255,rawvalue81,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value255_value83 : byteLess rawvalue255 rawvalue83 = true := by
  simp only [rawvalue255,rawvalue83,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value255_value84 : byteLess rawvalue255 rawvalue84 = true := by
  simp only [rawvalue255,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value255_value85 : byteLess rawvalue255 rawvalue85 = true := by
  simp only [rawvalue255,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue109,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value255_value88 : byteLess rawvalue255 rawvalue88 = true := by
  simp only [rawvalue255,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value255_value89 : byteLess rawvalue255 rawvalue89 = true := by
  simp only [rawvalue255,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value255_value90 : byteLess rawvalue255 rawvalue90 = true := by
  simp only [rawvalue255,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue232,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value256 : nodes value256 = 13561 := by
  change 1 + (nodes value192 + (nodes value198 + (nodes value203 + (nodes value215 + (nodes value221 + (nodes value227 + (nodes value253 + (nodes value254 + (nodes value255 + (nodes value75 + (nodes value76 + (nodes value77 + (nodes value79 + (nodes value80 + (nodes value81 + (nodes value83 + (nodes value84 + (nodes value85 + (nodes value88 + (nodes value89 + (nodes value90 + 0))))))))))))))))))))) = 13561
  simp only [nodes_value192,nodes_value198,nodes_value203,nodes_value215,nodes_value221,nodes_value227,nodes_value253,nodes_value254,nodes_value255,nodes_value75,nodes_value76,nodes_value77,nodes_value79,nodes_value80,nodes_value81,nodes_value83,nodes_value84,nodes_value85,nodes_value88,nodes_value89,nodes_value90]
  all_goals decide +kernel
theorem depth_value256 : depth value256 = 12 := by
  change max (1 + depth value192) (max (1 + depth value198) (max (1 + depth value203) (max (1 + depth value215) (max (1 + depth value221) (max (1 + depth value227) (max (1 + depth value253) (max (1 + depth value254) (max (1 + depth value255) (max (1 + depth value75) (max (1 + depth value76) (max (1 + depth value77) (max (1 + depth value79) (max (1 + depth value80) (max (1 + depth value81) (max (1 + depth value83) (max (1 + depth value84) (max (1 + depth value85) (max (1 + depth value88) (max (1 + depth value89) (max (1 + depth value90) (0))))))))))))))))))))) = 12
  simp only [depth_value192,depth_value198,depth_value203,depth_value215,depth_value221,depth_value227,depth_value253,depth_value254,depth_value255,depth_value75,depth_value76,depth_value77,depth_value79,depth_value80,depth_value81,depth_value83,depth_value84,depth_value85,depth_value88,depth_value89,depth_value90]
  all_goals decide +kernel
theorem canonical_value256 : canonical models value256 = true := by
  change ((canonical models value192 && (canonical models value198 && (canonical models value203 && (canonical models value215 && (canonical models value221 && (canonical models value227 && (canonical models value253 && (canonical models value254 && (canonical models value255 && (canonical models value75 && (canonical models value76 && (canonical models value77 && (canonical models value79 && (canonical models value80 && (canonical models value81 && (canonical models value83 && (canonical models value84 && (canonical models value85 && (canonical models value88 && (canonical models value89 && (canonical models value90 && true))))))))))))))))))))) && ordered [encode value192,encode value198,encode value203,encode value215,encode value221,encode value227,encode value253,encode value254,encode value255,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90]) = true
  simp only [canonical_value192,canonical_value198,canonical_value203,canonical_value215,canonical_value221,canonical_value227,canonical_value253,canonical_value254,canonical_value255,canonical_value75,canonical_value76,canonical_value77,canonical_value79,canonical_value80,canonical_value81,canonical_value83,canonical_value84,canonical_value85,canonical_value88,canonical_value89,canonical_value90,encoded_value192,encoded_value198,encoded_value203,encoded_value215,encoded_value221,encoded_value227,encoded_value253,encoded_value254,encoded_value255,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  simp only [ordered,List.all_cons,List.all_nil,order_value192_value198,order_value192_value203,order_value192_value215,order_value192_value221,order_value192_value227,order_value192_value253,order_value192_value254,order_value192_value255,order_value192_value75,order_value192_value76,order_value192_value77,order_value192_value79,order_value192_value80,order_value192_value81,order_value192_value83,order_value192_value84,order_value192_value85,order_value192_value88,order_value192_value89,order_value192_value90,order_value198_value203,order_value198_value215,order_value198_value221,order_value198_value227,order_value198_value253,order_value198_value254,order_value198_value255,order_value198_value75,order_value198_value76,order_value198_value77,order_value198_value79,order_value198_value80,order_value198_value81,order_value198_value83,order_value198_value84,order_value198_value85,order_value198_value88,order_value198_value89,order_value198_value90,order_value203_value215,order_value203_value221,order_value203_value227,order_value203_value253,order_value203_value254,order_value203_value255,order_value203_value75,order_value203_value76,order_value203_value77,order_value203_value79,order_value203_value80,order_value203_value81,order_value203_value83,order_value203_value84,order_value203_value85,order_value203_value88,order_value203_value89,order_value203_value90,order_value215_value221,order_value215_value227,order_value215_value253,order_value215_value254,order_value215_value255,order_value215_value75,order_value215_value76,order_value215_value77,order_value215_value79,order_value215_value80,order_value215_value81,order_value215_value83,order_value215_value84,order_value215_value85,order_value215_value88,order_value215_value89,order_value215_value90,order_value221_value227,order_value221_value253,order_value221_value254,order_value221_value255,order_value221_value75,order_value221_value76,order_value221_value77,order_value221_value79,order_value221_value80,order_value221_value81,order_value221_value83,order_value221_value84,order_value221_value85,order_value221_value88,order_value221_value89,order_value221_value90,order_value227_value253,order_value227_value254,order_value227_value255,order_value227_value75,order_value227_value76,order_value227_value77,order_value227_value79,order_value227_value80,order_value227_value81,order_value227_value83,order_value227_value84,order_value227_value85,order_value227_value88,order_value227_value89,order_value227_value90,order_value253_value254,order_value253_value255,order_value253_value75,order_value253_value76,order_value253_value77,order_value253_value79,order_value253_value80,order_value253_value81,order_value253_value83,order_value253_value84,order_value253_value85,order_value253_value88,order_value253_value89,order_value253_value90,order_value254_value255,order_value254_value75,order_value254_value76,order_value254_value77,order_value254_value79,order_value254_value80,order_value254_value81,order_value254_value83,order_value254_value84,order_value254_value85,order_value254_value88,order_value254_value89,order_value254_value90,order_value255_value75,order_value255_value76,order_value255_value77,order_value255_value79,order_value255_value80,order_value255_value81,order_value255_value83,order_value255_value84,order_value255_value85,order_value255_value88,order_value255_value89,order_value255_value90,order_value75_value76,order_value75_value77,order_value75_value79,order_value75_value80,order_value75_value81,order_value75_value83,order_value75_value84,order_value75_value85,order_value75_value88,order_value75_value89,order_value75_value90,order_value76_value77,order_value76_value79,order_value76_value80,order_value76_value81,order_value76_value83,order_value76_value84,order_value76_value85,order_value76_value88,order_value76_value89,order_value76_value90,order_value77_value79,order_value77_value80,order_value77_value81,order_value77_value83,order_value77_value84,order_value77_value85,order_value77_value88,order_value77_value89,order_value77_value90,order_value79_value80,order_value79_value81,order_value79_value83,order_value79_value84,order_value79_value85,order_value79_value88,order_value79_value89,order_value79_value90,order_value80_value81,order_value80_value83,order_value80_value84,order_value80_value85,order_value80_value88,order_value80_value89,order_value80_value90,order_value81_value83,order_value81_value84,order_value81_value85,order_value81_value88,order_value81_value89,order_value81_value90,order_value83_value84,order_value83_value85,order_value83_value88,order_value83_value89,order_value83_value90,order_value84_value85,order_value84_value88,order_value84_value89,order_value84_value90,order_value85_value88,order_value85_value89,order_value85_value90,order_value88_value89,order_value88_value90,order_value89_value90,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value256 : rawvalue256.length = 229149 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value192 (commaConsLength rawLength_value198 (commaConsLength rawLength_value203 (commaConsLength rawLength_value215 (commaConsLength rawLength_value221 (commaConsLength rawLength_value227 (commaConsLength rawLength_value253 (commaConsLength rawLength_value254 (commaConsLength rawLength_value255 (commaConsLength rawLength_value75 (commaConsLength rawLength_value76 (commaConsLength rawLength_value77 (commaConsLength rawLength_value79 (commaConsLength rawLength_value80 (commaConsLength rawLength_value81 (commaConsLength rawLength_value83 (commaConsLength rawLength_value84 (commaConsLength rawLength_value85 (commaConsLength rawLength_value88 (commaConsLength rawLength_value89 (commaSingletonLength rawLength_value90)))))))))))))))))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value257 : Value := .integer (31)
noncomputable def rawvalue257 : Bytes := asciiBytes "[\"int\",\"31\"]"
theorem encoded_value257 : encode value257 = rawvalue257 := by
  all_goals rfl
theorem nodes_value257 : nodes value257 = 1 := by rfl
theorem depth_value257 : depth value257 = 0 := by rfl
theorem canonical_value257 : canonical models value257 = true := by decide +kernel
theorem rawLength_value257 : rawvalue257.length = 12 := by
  decide +kernel
noncomputable def value258 : Value := .function (.cons value2 value210 (.cons value36 value40 .nil))
noncomputable def rawvalue258 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue210 ++ [93]),([91] ++ rawvalue36 ++ [44] ++ rawvalue40 ++ [93])] ++ [93,93]
theorem encoded_value258 : encode value258 = rawvalue258 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value210 ++ [93]),([91] ++ encode value36 ++ [44] ++ encode value40 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value210,encoded_value36,encoded_value40]
  all_goals rfl
theorem nodes_value258 : nodes value258 = 630 := by
  change 1 + (nodes value2 + nodes value210 + (nodes value36 + nodes value40 + 0)) = 630
  simp only [nodes_value2,nodes_value210,nodes_value36,nodes_value40]
  all_goals decide +kernel
theorem depth_value258 : depth value258 = 9 := by
  change max (max (1 + depth value2) (1 + depth value210)) (max (max (1 + depth value36) (1 + depth value40)) (0)) = 9
  simp only [depth_value2,depth_value210,depth_value36,depth_value40]
  all_goals decide +kernel
theorem canonical_value258 : canonical models value258 = true := by
  change ((canonical models value2 && canonical models value210 && (canonical models value36 && canonical models value40 && true)) && ordered [encode value2,encode value36]) = true
  simp only [canonical_value2,canonical_value210,canonical_value36,canonical_value40,encoded_value2,encoded_value36]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value36,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value258 : rawvalue258.length = 10603 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value210) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value36) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value40) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value259 : Value := .set (.cons value208 (.cons value258 .nil))
noncomputable def rawvalue259 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue208,rawvalue258] ++ [93,93]
theorem encoded_value259 : encode value259 = rawvalue259 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value208,encode value258] ++ [93,93] = _
  simp only [encoded_value208,encoded_value258]
  all_goals rfl
theorem order_value208_value258 : byteLess rawvalue208 rawvalue258 = true := by
  simp only [rawvalue208,rawvalue258,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue173,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue51,rawvalue55,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value259 : nodes value259 = 1261 := by
  change 1 + (nodes value208 + (nodes value258 + 0)) = 1261
  simp only [nodes_value208,nodes_value258]
  all_goals decide +kernel
theorem depth_value259 : depth value259 = 10 := by
  change max (1 + depth value208) (max (1 + depth value258) (0)) = 10
  simp only [depth_value208,depth_value258]
  all_goals decide +kernel
theorem canonical_value259 : canonical models value259 = true := by
  change ((canonical models value208 && (canonical models value258 && true)) && ordered [encode value208,encode value258]) = true
  simp only [canonical_value208,canonical_value258,encoded_value208,encoded_value258]
  simp only [ordered,List.all_cons,List.all_nil,order_value208_value258,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value259 : rawvalue259.length = 21216 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value208 (commaSingletonLength rawLength_value258))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value260 : Value := .function (.cons value2 value248 (.cons value45 value37 .nil))
noncomputable def rawvalue260 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue248 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue37 ++ [93])] ++ [93,93]
theorem encoded_value260 : encode value260 = rawvalue260 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value248 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value37 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value248,encoded_value45,encoded_value37]
  all_goals rfl
theorem nodes_value260 : nodes value260 = 3157 := by
  change 1 + (nodes value2 + nodes value248 + (nodes value45 + nodes value37 + 0)) = 3157
  simp only [nodes_value2,nodes_value248,nodes_value45,nodes_value37]
  all_goals decide +kernel
theorem depth_value260 : depth value260 = 12 := by
  change max (max (1 + depth value2) (1 + depth value248)) (max (max (1 + depth value45) (1 + depth value37)) (0)) = 12
  simp only [depth_value2,depth_value248,depth_value45,depth_value37]
  all_goals decide +kernel
theorem canonical_value260 : canonical models value260 = true := by
  change ((canonical models value2 && canonical models value248 && (canonical models value45 && canonical models value37 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value248,canonical_value45,canonical_value37,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value260 : rawvalue260.length = 53250 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value248) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value37) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value261 : Value := .set (.cons value260 .nil)
noncomputable def rawvalue261 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue260] ++ [93,93]
theorem encoded_value261 : encode value261 = rawvalue261 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value260] ++ [93,93] = _
  simp only [encoded_value260]
  all_goals rfl
theorem nodes_value261 : nodes value261 = 3158 := by
  change 1 + (nodes value260 + 0) = 3158
  simp only [nodes_value260]
  all_goals decide +kernel
theorem depth_value261 : depth value261 = 13 := by
  change max (1 + depth value260) (0) = 13
  simp only [depth_value260]
  all_goals decide +kernel
theorem canonical_value261 : canonical models value261 = true := by
  change ((canonical models value260 && true) && ordered [encode value260]) = true
  simp only [canonical_value260,encoded_value260]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value261 : rawvalue261.length = 53260 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value260)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value262 : Value := .integer (8)
noncomputable def rawvalue262 : Bytes := asciiBytes "[\"int\",\"8\"]"
theorem encoded_value262 : encode value262 = rawvalue262 := by
  all_goals rfl
theorem nodes_value262 : nodes value262 = 1 := by rfl
theorem depth_value262 : depth value262 = 0 := by rfl
theorem canonical_value262 : canonical models value262 = true := by decide +kernel
theorem rawLength_value262 : rawvalue262.length = 11 := by
  decide +kernel
noncomputable def value263 : Value := .function (.cons value37 value262 (.cons value38 value250 (.cons value39 value250 (.cons value43 value64 .nil))))
noncomputable def rawvalue263 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue37 ++ [44] ++ rawvalue262 ++ [93]),([91] ++ rawvalue38 ++ [44] ++ rawvalue250 ++ [93]),([91] ++ rawvalue39 ++ [44] ++ rawvalue250 ++ [93]),([91] ++ rawvalue43 ++ [44] ++ rawvalue64 ++ [93])] ++ [93,93]
theorem encoded_value263 : encode value263 = rawvalue263 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value37 ++ [44] ++ encode value262 ++ [93]),([91] ++ encode value38 ++ [44] ++ encode value250 ++ [93]),([91] ++ encode value39 ++ [44] ++ encode value250 ++ [93]),([91] ++ encode value43 ++ [44] ++ encode value64 ++ [93])] ++ [93,93] = _
  simp only [encoded_value37,encoded_value262,encoded_value38,encoded_value250,encoded_value39,encoded_value43,encoded_value64]
  all_goals rfl
theorem nodes_value263 : nodes value263 = 9 := by
  change 1 + (nodes value37 + nodes value262 + (nodes value38 + nodes value250 + (nodes value39 + nodes value250 + (nodes value43 + nodes value64 + 0)))) = 9
  simp only [nodes_value37,nodes_value262,nodes_value38,nodes_value250,nodes_value39,nodes_value43,nodes_value64]
  all_goals decide +kernel
theorem depth_value263 : depth value263 = 1 := by
  change max (max (1 + depth value37) (1 + depth value262)) (max (max (1 + depth value38) (1 + depth value250)) (max (max (1 + depth value39) (1 + depth value250)) (max (max (1 + depth value43) (1 + depth value64)) (0)))) = 1
  simp only [depth_value37,depth_value262,depth_value38,depth_value250,depth_value39,depth_value43,depth_value64]
  all_goals decide +kernel
theorem canonical_value263 : canonical models value263 = true := by
  change ((canonical models value37 && canonical models value262 && (canonical models value38 && canonical models value250 && (canonical models value39 && canonical models value250 && (canonical models value43 && canonical models value64 && true)))) && ordered [encode value37,encode value38,encode value39,encode value43]) = true
  simp only [canonical_value37,canonical_value262,canonical_value38,canonical_value250,canonical_value39,canonical_value43,canonical_value64,encoded_value37,encoded_value38,encoded_value39,encoded_value43]
  simp only [ordered,List.all_cons,List.all_nil,order_value37_value38,order_value37_value39,order_value37_value43,order_value38_value39,order_value38_value43,order_value39_value43,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value263 : rawvalue263.length = 125 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value37) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value262) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value38) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value250) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value39) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value250) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value43) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value64) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value264 : Value := .text "APPLY"
noncomputable def rawvalue264 : Bytes := asciiBytes "[\"str\",\"APPLY\"]"
theorem encoded_value264 : encode value264 = rawvalue264 := by
  all_goals rfl
theorem nodes_value264 : nodes value264 = 1 := by rfl
theorem depth_value264 : depth value264 = 0 := by rfl
theorem canonical_value264 : canonical models value264 = true := by decide +kernel
theorem rawLength_value264 : rawvalue264.length = 15 := by
  decide +kernel
noncomputable def value265 : Value := .function (.cons value2 value248 (.cons value72 value232 (.cons value73 value264 (.cons value45 value37 .nil))))
noncomputable def rawvalue265 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue248 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue232 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue264 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue37 ++ [93])] ++ [93,93]
theorem encoded_value265 : encode value265 = rawvalue265 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value248 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value232 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value264 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value37 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value248,encoded_value72,encoded_value232,encoded_value73,encoded_value264,encoded_value45,encoded_value37]
  all_goals rfl
theorem nodes_value265 : nodes value265 = 5926 := by
  change 1 + (nodes value2 + nodes value248 + (nodes value72 + nodes value232 + (nodes value73 + nodes value264 + (nodes value45 + nodes value37 + 0)))) = 5926
  simp only [nodes_value2,nodes_value248,nodes_value72,nodes_value232,nodes_value73,nodes_value264,nodes_value45,nodes_value37]
  all_goals decide +kernel
theorem depth_value265 : depth value265 = 12 := by
  change max (max (1 + depth value2) (1 + depth value248)) (max (max (1 + depth value72) (1 + depth value232)) (max (max (1 + depth value73) (1 + depth value264)) (max (max (1 + depth value45) (1 + depth value37)) (0)))) = 12
  simp only [depth_value2,depth_value248,depth_value72,depth_value232,depth_value73,depth_value264,depth_value45,depth_value37]
  all_goals decide +kernel
theorem canonical_value265 : canonical models value265 = true := by
  change ((canonical models value2 && canonical models value248 && (canonical models value72 && canonical models value232 && (canonical models value73 && canonical models value264 && (canonical models value45 && canonical models value37 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value248,canonical_value72,canonical_value232,canonical_value73,canonical_value264,canonical_value45,canonical_value37,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value265 : rawvalue265.length = 100016 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value248) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value232) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value264) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value37) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value266 : Value := .set (.cons value265 (.cons value192 (.cons value198 (.cons value203 (.cons value215 (.cons value221 (.cons value227 (.cons value253 (.cons value254 (.cons value255 (.cons value75 (.cons value76 (.cons value77 (.cons value79 (.cons value80 (.cons value81 (.cons value83 (.cons value84 (.cons value85 (.cons value88 (.cons value89 (.cons value90 .nil))))))))))))))))))))))
noncomputable def rawvalue266 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue265,rawvalue192,rawvalue198,rawvalue203,rawvalue215,rawvalue221,rawvalue227,rawvalue253,rawvalue254,rawvalue255,rawvalue75,rawvalue76,rawvalue77,rawvalue79,rawvalue80,rawvalue81,rawvalue83,rawvalue84,rawvalue85,rawvalue88,rawvalue89,rawvalue90] ++ [93,93]
theorem encoded_value266 : encode value266 = rawvalue266 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value265,encode value192,encode value198,encode value203,encode value215,encode value221,encode value227,encode value253,encode value254,encode value255,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90] ++ [93,93] = _
  simp only [encoded_value265,encoded_value192,encoded_value198,encoded_value203,encoded_value215,encoded_value221,encoded_value227,encoded_value253,encoded_value254,encoded_value255,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  all_goals rfl
theorem order_value265_value192 : byteLess rawvalue265 rawvalue192 = true := by
  simp only [rawvalue265,rawvalue192,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue173,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value198 : byteLess rawvalue265 rawvalue198 = true := by
  simp only [rawvalue265,rawvalue198,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue173,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value203 : byteLess rawvalue265 rawvalue203 = true := by
  simp only [rawvalue265,rawvalue203,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue173,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value215 : byteLess rawvalue265 rawvalue215 = true := by
  simp only [rawvalue265,rawvalue215,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value221 : byteLess rawvalue265 rawvalue221 = true := by
  simp only [rawvalue265,rawvalue221,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value227 : byteLess rawvalue265 rawvalue227 = true := by
  simp only [rawvalue265,rawvalue227,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value253 : byteLess rawvalue265 rawvalue253 = true := by
  simp only [rawvalue265,rawvalue253,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value254 : byteLess rawvalue265 rawvalue254 = true := by
  simp only [rawvalue265,rawvalue254,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value255 : byteLess rawvalue265 rawvalue255 = true := by
  simp only [rawvalue265,rawvalue255,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value75 : byteLess rawvalue265 rawvalue75 = true := by
  simp only [rawvalue265,rawvalue75,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value76 : byteLess rawvalue265 rawvalue76 = true := by
  simp only [rawvalue265,rawvalue76,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value77 : byteLess rawvalue265 rawvalue77 = true := by
  simp only [rawvalue265,rawvalue77,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value79 : byteLess rawvalue265 rawvalue79 = true := by
  simp only [rawvalue265,rawvalue79,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value80 : byteLess rawvalue265 rawvalue80 = true := by
  simp only [rawvalue265,rawvalue80,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value81 : byteLess rawvalue265 rawvalue81 = true := by
  simp only [rawvalue265,rawvalue81,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value83 : byteLess rawvalue265 rawvalue83 = true := by
  simp only [rawvalue265,rawvalue83,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value84 : byteLess rawvalue265 rawvalue84 = true := by
  simp only [rawvalue265,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value85 : byteLess rawvalue265 rawvalue85 = true := by
  simp only [rawvalue265,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value88 : byteLess rawvalue265 rawvalue88 = true := by
  simp only [rawvalue265,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value89 : byteLess rawvalue265 rawvalue89 = true := by
  simp only [rawvalue265,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value265_value90 : byteLess rawvalue265 rawvalue90 = true := by
  simp only [rawvalue265,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value266 : nodes value266 = 19487 := by
  change 1 + (nodes value265 + (nodes value192 + (nodes value198 + (nodes value203 + (nodes value215 + (nodes value221 + (nodes value227 + (nodes value253 + (nodes value254 + (nodes value255 + (nodes value75 + (nodes value76 + (nodes value77 + (nodes value79 + (nodes value80 + (nodes value81 + (nodes value83 + (nodes value84 + (nodes value85 + (nodes value88 + (nodes value89 + (nodes value90 + 0)))))))))))))))))))))) = 19487
  simp only [nodes_value265,nodes_value192,nodes_value198,nodes_value203,nodes_value215,nodes_value221,nodes_value227,nodes_value253,nodes_value254,nodes_value255,nodes_value75,nodes_value76,nodes_value77,nodes_value79,nodes_value80,nodes_value81,nodes_value83,nodes_value84,nodes_value85,nodes_value88,nodes_value89,nodes_value90]
  all_goals decide +kernel
theorem depth_value266 : depth value266 = 13 := by
  change max (1 + depth value265) (max (1 + depth value192) (max (1 + depth value198) (max (1 + depth value203) (max (1 + depth value215) (max (1 + depth value221) (max (1 + depth value227) (max (1 + depth value253) (max (1 + depth value254) (max (1 + depth value255) (max (1 + depth value75) (max (1 + depth value76) (max (1 + depth value77) (max (1 + depth value79) (max (1 + depth value80) (max (1 + depth value81) (max (1 + depth value83) (max (1 + depth value84) (max (1 + depth value85) (max (1 + depth value88) (max (1 + depth value89) (max (1 + depth value90) (0)))))))))))))))))))))) = 13
  simp only [depth_value265,depth_value192,depth_value198,depth_value203,depth_value215,depth_value221,depth_value227,depth_value253,depth_value254,depth_value255,depth_value75,depth_value76,depth_value77,depth_value79,depth_value80,depth_value81,depth_value83,depth_value84,depth_value85,depth_value88,depth_value89,depth_value90]
  all_goals decide +kernel
theorem canonical_value266 : canonical models value266 = true := by
  change ((canonical models value265 && (canonical models value192 && (canonical models value198 && (canonical models value203 && (canonical models value215 && (canonical models value221 && (canonical models value227 && (canonical models value253 && (canonical models value254 && (canonical models value255 && (canonical models value75 && (canonical models value76 && (canonical models value77 && (canonical models value79 && (canonical models value80 && (canonical models value81 && (canonical models value83 && (canonical models value84 && (canonical models value85 && (canonical models value88 && (canonical models value89 && (canonical models value90 && true)))))))))))))))))))))) && ordered [encode value265,encode value192,encode value198,encode value203,encode value215,encode value221,encode value227,encode value253,encode value254,encode value255,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90]) = true
  simp only [canonical_value265,canonical_value192,canonical_value198,canonical_value203,canonical_value215,canonical_value221,canonical_value227,canonical_value253,canonical_value254,canonical_value255,canonical_value75,canonical_value76,canonical_value77,canonical_value79,canonical_value80,canonical_value81,canonical_value83,canonical_value84,canonical_value85,canonical_value88,canonical_value89,canonical_value90,encoded_value265,encoded_value192,encoded_value198,encoded_value203,encoded_value215,encoded_value221,encoded_value227,encoded_value253,encoded_value254,encoded_value255,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  simp only [ordered,List.all_cons,List.all_nil,order_value265_value192,order_value265_value198,order_value265_value203,order_value265_value215,order_value265_value221,order_value265_value227,order_value265_value253,order_value265_value254,order_value265_value255,order_value265_value75,order_value265_value76,order_value265_value77,order_value265_value79,order_value265_value80,order_value265_value81,order_value265_value83,order_value265_value84,order_value265_value85,order_value265_value88,order_value265_value89,order_value265_value90,order_value192_value198,order_value192_value203,order_value192_value215,order_value192_value221,order_value192_value227,order_value192_value253,order_value192_value254,order_value192_value255,order_value192_value75,order_value192_value76,order_value192_value77,order_value192_value79,order_value192_value80,order_value192_value81,order_value192_value83,order_value192_value84,order_value192_value85,order_value192_value88,order_value192_value89,order_value192_value90,order_value198_value203,order_value198_value215,order_value198_value221,order_value198_value227,order_value198_value253,order_value198_value254,order_value198_value255,order_value198_value75,order_value198_value76,order_value198_value77,order_value198_value79,order_value198_value80,order_value198_value81,order_value198_value83,order_value198_value84,order_value198_value85,order_value198_value88,order_value198_value89,order_value198_value90,order_value203_value215,order_value203_value221,order_value203_value227,order_value203_value253,order_value203_value254,order_value203_value255,order_value203_value75,order_value203_value76,order_value203_value77,order_value203_value79,order_value203_value80,order_value203_value81,order_value203_value83,order_value203_value84,order_value203_value85,order_value203_value88,order_value203_value89,order_value203_value90,order_value215_value221,order_value215_value227,order_value215_value253,order_value215_value254,order_value215_value255,order_value215_value75,order_value215_value76,order_value215_value77,order_value215_value79,order_value215_value80,order_value215_value81,order_value215_value83,order_value215_value84,order_value215_value85,order_value215_value88,order_value215_value89,order_value215_value90,order_value221_value227,order_value221_value253,order_value221_value254,order_value221_value255,order_value221_value75,order_value221_value76,order_value221_value77,order_value221_value79,order_value221_value80,order_value221_value81,order_value221_value83,order_value221_value84,order_value221_value85,order_value221_value88,order_value221_value89,order_value221_value90,order_value227_value253,order_value227_value254,order_value227_value255,order_value227_value75,order_value227_value76,order_value227_value77,order_value227_value79,order_value227_value80,order_value227_value81,order_value227_value83,order_value227_value84,order_value227_value85,order_value227_value88,order_value227_value89,order_value227_value90,order_value253_value254,order_value253_value255,order_value253_value75,order_value253_value76,order_value253_value77,order_value253_value79,order_value253_value80,order_value253_value81,order_value253_value83,order_value253_value84,order_value253_value85,order_value253_value88,order_value253_value89,order_value253_value90,order_value254_value255,order_value254_value75,order_value254_value76,order_value254_value77,order_value254_value79,order_value254_value80,order_value254_value81,order_value254_value83,order_value254_value84,order_value254_value85,order_value254_value88,order_value254_value89,order_value254_value90,order_value255_value75,order_value255_value76,order_value255_value77,order_value255_value79,order_value255_value80,order_value255_value81,order_value255_value83,order_value255_value84,order_value255_value85,order_value255_value88,order_value255_value89,order_value255_value90,order_value75_value76,order_value75_value77,order_value75_value79,order_value75_value80,order_value75_value81,order_value75_value83,order_value75_value84,order_value75_value85,order_value75_value88,order_value75_value89,order_value75_value90,order_value76_value77,order_value76_value79,order_value76_value80,order_value76_value81,order_value76_value83,order_value76_value84,order_value76_value85,order_value76_value88,order_value76_value89,order_value76_value90,order_value77_value79,order_value77_value80,order_value77_value81,order_value77_value83,order_value77_value84,order_value77_value85,order_value77_value88,order_value77_value89,order_value77_value90,order_value79_value80,order_value79_value81,order_value79_value83,order_value79_value84,order_value79_value85,order_value79_value88,order_value79_value89,order_value79_value90,order_value80_value81,order_value80_value83,order_value80_value84,order_value80_value85,order_value80_value88,order_value80_value89,order_value80_value90,order_value81_value83,order_value81_value84,order_value81_value85,order_value81_value88,order_value81_value89,order_value81_value90,order_value83_value84,order_value83_value85,order_value83_value88,order_value83_value89,order_value83_value90,order_value84_value85,order_value84_value88,order_value84_value89,order_value84_value90,order_value85_value88,order_value85_value89,order_value85_value90,order_value88_value89,order_value88_value90,order_value89_value90,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value266 : rawvalue266.length = 329166 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value265 (commaConsLength rawLength_value192 (commaConsLength rawLength_value198 (commaConsLength rawLength_value203 (commaConsLength rawLength_value215 (commaConsLength rawLength_value221 (commaConsLength rawLength_value227 (commaConsLength rawLength_value253 (commaConsLength rawLength_value254 (commaConsLength rawLength_value255 (commaConsLength rawLength_value75 (commaConsLength rawLength_value76 (commaConsLength rawLength_value77 (commaConsLength rawLength_value79 (commaConsLength rawLength_value80 (commaConsLength rawLength_value81 (commaConsLength rawLength_value83 (commaConsLength rawLength_value84 (commaConsLength rawLength_value85 (commaConsLength rawLength_value88 (commaConsLength rawLength_value89 (commaSingletonLength rawLength_value90))))))))))))))))))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value267 : Value := .integer (32)
noncomputable def rawvalue267 : Bytes := asciiBytes "[\"int\",\"32\"]"
theorem encoded_value267 : encode value267 = rawvalue267 := by
  all_goals rfl
theorem nodes_value267 : nodes value267 = 1 := by rfl
theorem depth_value267 : depth value267 = 0 := by rfl
theorem canonical_value267 : canonical models value267 = true := by decide +kernel
theorem rawLength_value267 : rawvalue267.length = 12 := by
  decide +kernel
noncomputable def value268 : Value := .function (.cons value2 value248 (.cons value45 value38 .nil))
noncomputable def rawvalue268 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue248 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue38 ++ [93])] ++ [93,93]
theorem encoded_value268 : encode value268 = rawvalue268 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value248 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value38 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value248,encoded_value45,encoded_value38]
  all_goals rfl
theorem nodes_value268 : nodes value268 = 3157 := by
  change 1 + (nodes value2 + nodes value248 + (nodes value45 + nodes value38 + 0)) = 3157
  simp only [nodes_value2,nodes_value248,nodes_value45,nodes_value38]
  all_goals decide +kernel
theorem depth_value268 : depth value268 = 12 := by
  change max (max (1 + depth value2) (1 + depth value248)) (max (max (1 + depth value45) (1 + depth value38)) (0)) = 12
  simp only [depth_value2,depth_value248,depth_value45,depth_value38]
  all_goals decide +kernel
theorem canonical_value268 : canonical models value268 = true := by
  change ((canonical models value2 && canonical models value248 && (canonical models value45 && canonical models value38 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value248,canonical_value45,canonical_value38,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value268 : rawvalue268.length = 53250 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value248) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value38) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value269 : Value := .set (.cons value260 (.cons value268 .nil))
noncomputable def rawvalue269 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue260,rawvalue268] ++ [93,93]
theorem encoded_value269 : encode value269 = rawvalue269 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value260,encode value268] ++ [93,93] = _
  simp only [encoded_value260,encoded_value268]
  all_goals rfl
theorem order_value260_value268 : byteLess rawvalue260 rawvalue268 = true := by
  simp only [rawvalue260,rawvalue268,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue38,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value269 : nodes value269 = 6315 := by
  change 1 + (nodes value260 + (nodes value268 + 0)) = 6315
  simp only [nodes_value260,nodes_value268]
  all_goals decide +kernel
theorem depth_value269 : depth value269 = 13 := by
  change max (1 + depth value260) (max (1 + depth value268) (0)) = 13
  simp only [depth_value260,depth_value268]
  all_goals decide +kernel
theorem canonical_value269 : canonical models value269 = true := by
  change ((canonical models value260 && (canonical models value268 && true)) && ordered [encode value260,encode value268]) = true
  simp only [canonical_value260,canonical_value268,encoded_value260,encoded_value268]
  simp only [ordered,List.all_cons,List.all_nil,order_value260_value268,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value269 : rawvalue269.length = 106511 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value260 (commaSingletonLength rawLength_value268))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value270 : Value := .function (.cons value37 value262 (.cons value38 value262 (.cons value39 value250 (.cons value43 value64 .nil))))
noncomputable def rawvalue270 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue37 ++ [44] ++ rawvalue262 ++ [93]),([91] ++ rawvalue38 ++ [44] ++ rawvalue262 ++ [93]),([91] ++ rawvalue39 ++ [44] ++ rawvalue250 ++ [93]),([91] ++ rawvalue43 ++ [44] ++ rawvalue64 ++ [93])] ++ [93,93]
theorem encoded_value270 : encode value270 = rawvalue270 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value37 ++ [44] ++ encode value262 ++ [93]),([91] ++ encode value38 ++ [44] ++ encode value262 ++ [93]),([91] ++ encode value39 ++ [44] ++ encode value250 ++ [93]),([91] ++ encode value43 ++ [44] ++ encode value64 ++ [93])] ++ [93,93] = _
  simp only [encoded_value37,encoded_value262,encoded_value38,encoded_value39,encoded_value250,encoded_value43,encoded_value64]
  all_goals rfl
theorem nodes_value270 : nodes value270 = 9 := by
  change 1 + (nodes value37 + nodes value262 + (nodes value38 + nodes value262 + (nodes value39 + nodes value250 + (nodes value43 + nodes value64 + 0)))) = 9
  simp only [nodes_value37,nodes_value262,nodes_value38,nodes_value39,nodes_value250,nodes_value43,nodes_value64]
  all_goals decide +kernel
theorem depth_value270 : depth value270 = 1 := by
  change max (max (1 + depth value37) (1 + depth value262)) (max (max (1 + depth value38) (1 + depth value262)) (max (max (1 + depth value39) (1 + depth value250)) (max (max (1 + depth value43) (1 + depth value64)) (0)))) = 1
  simp only [depth_value37,depth_value262,depth_value38,depth_value39,depth_value250,depth_value43,depth_value64]
  all_goals decide +kernel
theorem canonical_value270 : canonical models value270 = true := by
  change ((canonical models value37 && canonical models value262 && (canonical models value38 && canonical models value262 && (canonical models value39 && canonical models value250 && (canonical models value43 && canonical models value64 && true)))) && ordered [encode value37,encode value38,encode value39,encode value43]) = true
  simp only [canonical_value37,canonical_value262,canonical_value38,canonical_value39,canonical_value250,canonical_value43,canonical_value64,encoded_value37,encoded_value38,encoded_value39,encoded_value43]
  simp only [ordered,List.all_cons,List.all_nil,order_value37_value38,order_value37_value39,order_value37_value43,order_value38_value39,order_value38_value43,order_value39_value43,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value270 : rawvalue270.length = 125 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value37) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value262) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value38) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value262) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value39) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value250) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value43) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value64) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value271 : Value := .function (.cons value2 value248 (.cons value72 value232 (.cons value73 value264 (.cons value45 value38 .nil))))
noncomputable def rawvalue271 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue248 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue232 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue264 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue38 ++ [93])] ++ [93,93]
theorem encoded_value271 : encode value271 = rawvalue271 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value248 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value232 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value264 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value38 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value248,encoded_value72,encoded_value232,encoded_value73,encoded_value264,encoded_value45,encoded_value38]
  all_goals rfl
theorem nodes_value271 : nodes value271 = 5926 := by
  change 1 + (nodes value2 + nodes value248 + (nodes value72 + nodes value232 + (nodes value73 + nodes value264 + (nodes value45 + nodes value38 + 0)))) = 5926
  simp only [nodes_value2,nodes_value248,nodes_value72,nodes_value232,nodes_value73,nodes_value264,nodes_value45,nodes_value38]
  all_goals decide +kernel
theorem depth_value271 : depth value271 = 12 := by
  change max (max (1 + depth value2) (1 + depth value248)) (max (max (1 + depth value72) (1 + depth value232)) (max (max (1 + depth value73) (1 + depth value264)) (max (max (1 + depth value45) (1 + depth value38)) (0)))) = 12
  simp only [depth_value2,depth_value248,depth_value72,depth_value232,depth_value73,depth_value264,depth_value45,depth_value38]
  all_goals decide +kernel
theorem canonical_value271 : canonical models value271 = true := by
  change ((canonical models value2 && canonical models value248 && (canonical models value72 && canonical models value232 && (canonical models value73 && canonical models value264 && (canonical models value45 && canonical models value38 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value248,canonical_value72,canonical_value232,canonical_value73,canonical_value264,canonical_value45,canonical_value38,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value271 : rawvalue271.length = 100016 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value248) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value232) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value264) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value38) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value272 : Value := .set (.cons value265 (.cons value271 (.cons value192 (.cons value198 (.cons value203 (.cons value215 (.cons value221 (.cons value227 (.cons value253 (.cons value254 (.cons value255 (.cons value75 (.cons value76 (.cons value77 (.cons value79 (.cons value80 (.cons value81 (.cons value83 (.cons value84 (.cons value85 (.cons value88 (.cons value89 (.cons value90 .nil)))))))))))))))))))))))
noncomputable def rawvalue272 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue265,rawvalue271,rawvalue192,rawvalue198,rawvalue203,rawvalue215,rawvalue221,rawvalue227,rawvalue253,rawvalue254,rawvalue255,rawvalue75,rawvalue76,rawvalue77,rawvalue79,rawvalue80,rawvalue81,rawvalue83,rawvalue84,rawvalue85,rawvalue88,rawvalue89,rawvalue90] ++ [93,93]
theorem encoded_value272 : encode value272 = rawvalue272 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value265,encode value271,encode value192,encode value198,encode value203,encode value215,encode value221,encode value227,encode value253,encode value254,encode value255,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90] ++ [93,93] = _
  simp only [encoded_value265,encoded_value271,encoded_value192,encoded_value198,encoded_value203,encoded_value215,encoded_value221,encoded_value227,encoded_value253,encoded_value254,encoded_value255,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  all_goals rfl
theorem order_value265_value271 : byteLess rawvalue265 rawvalue271 = true := by
  simp only [rawvalue265,rawvalue271,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue38,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value192 : byteLess rawvalue271 rawvalue192 = true := by
  simp only [rawvalue271,rawvalue192,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue173,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value198 : byteLess rawvalue271 rawvalue198 = true := by
  simp only [rawvalue271,rawvalue198,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue173,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value203 : byteLess rawvalue271 rawvalue203 = true := by
  simp only [rawvalue271,rawvalue203,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue173,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value215 : byteLess rawvalue271 rawvalue215 = true := by
  simp only [rawvalue271,rawvalue215,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value221 : byteLess rawvalue271 rawvalue221 = true := by
  simp only [rawvalue271,rawvalue221,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value227 : byteLess rawvalue271 rawvalue227 = true := by
  simp only [rawvalue271,rawvalue227,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value253 : byteLess rawvalue271 rawvalue253 = true := by
  simp only [rawvalue271,rawvalue253,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value254 : byteLess rawvalue271 rawvalue254 = true := by
  simp only [rawvalue271,rawvalue254,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value255 : byteLess rawvalue271 rawvalue255 = true := by
  simp only [rawvalue271,rawvalue255,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value75 : byteLess rawvalue271 rawvalue75 = true := by
  simp only [rawvalue271,rawvalue75,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value76 : byteLess rawvalue271 rawvalue76 = true := by
  simp only [rawvalue271,rawvalue76,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value77 : byteLess rawvalue271 rawvalue77 = true := by
  simp only [rawvalue271,rawvalue77,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value79 : byteLess rawvalue271 rawvalue79 = true := by
  simp only [rawvalue271,rawvalue79,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value80 : byteLess rawvalue271 rawvalue80 = true := by
  simp only [rawvalue271,rawvalue80,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value81 : byteLess rawvalue271 rawvalue81 = true := by
  simp only [rawvalue271,rawvalue81,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value83 : byteLess rawvalue271 rawvalue83 = true := by
  simp only [rawvalue271,rawvalue83,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value84 : byteLess rawvalue271 rawvalue84 = true := by
  simp only [rawvalue271,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value85 : byteLess rawvalue271 rawvalue85 = true := by
  simp only [rawvalue271,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value88 : byteLess rawvalue271 rawvalue88 = true := by
  simp only [rawvalue271,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value89 : byteLess rawvalue271 rawvalue89 = true := by
  simp only [rawvalue271,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value90 : byteLess rawvalue271 rawvalue90 = true := by
  simp only [rawvalue271,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value272 : nodes value272 = 25413 := by
  change 1 + (nodes value265 + (nodes value271 + (nodes value192 + (nodes value198 + (nodes value203 + (nodes value215 + (nodes value221 + (nodes value227 + (nodes value253 + (nodes value254 + (nodes value255 + (nodes value75 + (nodes value76 + (nodes value77 + (nodes value79 + (nodes value80 + (nodes value81 + (nodes value83 + (nodes value84 + (nodes value85 + (nodes value88 + (nodes value89 + (nodes value90 + 0))))))))))))))))))))))) = 25413
  simp only [nodes_value265,nodes_value271,nodes_value192,nodes_value198,nodes_value203,nodes_value215,nodes_value221,nodes_value227,nodes_value253,nodes_value254,nodes_value255,nodes_value75,nodes_value76,nodes_value77,nodes_value79,nodes_value80,nodes_value81,nodes_value83,nodes_value84,nodes_value85,nodes_value88,nodes_value89,nodes_value90]
  all_goals decide +kernel
theorem depth_value272 : depth value272 = 13 := by
  change max (1 + depth value265) (max (1 + depth value271) (max (1 + depth value192) (max (1 + depth value198) (max (1 + depth value203) (max (1 + depth value215) (max (1 + depth value221) (max (1 + depth value227) (max (1 + depth value253) (max (1 + depth value254) (max (1 + depth value255) (max (1 + depth value75) (max (1 + depth value76) (max (1 + depth value77) (max (1 + depth value79) (max (1 + depth value80) (max (1 + depth value81) (max (1 + depth value83) (max (1 + depth value84) (max (1 + depth value85) (max (1 + depth value88) (max (1 + depth value89) (max (1 + depth value90) (0))))))))))))))))))))))) = 13
  simp only [depth_value265,depth_value271,depth_value192,depth_value198,depth_value203,depth_value215,depth_value221,depth_value227,depth_value253,depth_value254,depth_value255,depth_value75,depth_value76,depth_value77,depth_value79,depth_value80,depth_value81,depth_value83,depth_value84,depth_value85,depth_value88,depth_value89,depth_value90]
  all_goals decide +kernel
theorem canonical_value272 : canonical models value272 = true := by
  change ((canonical models value265 && (canonical models value271 && (canonical models value192 && (canonical models value198 && (canonical models value203 && (canonical models value215 && (canonical models value221 && (canonical models value227 && (canonical models value253 && (canonical models value254 && (canonical models value255 && (canonical models value75 && (canonical models value76 && (canonical models value77 && (canonical models value79 && (canonical models value80 && (canonical models value81 && (canonical models value83 && (canonical models value84 && (canonical models value85 && (canonical models value88 && (canonical models value89 && (canonical models value90 && true))))))))))))))))))))))) && ordered [encode value265,encode value271,encode value192,encode value198,encode value203,encode value215,encode value221,encode value227,encode value253,encode value254,encode value255,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90]) = true
  simp only [canonical_value265,canonical_value271,canonical_value192,canonical_value198,canonical_value203,canonical_value215,canonical_value221,canonical_value227,canonical_value253,canonical_value254,canonical_value255,canonical_value75,canonical_value76,canonical_value77,canonical_value79,canonical_value80,canonical_value81,canonical_value83,canonical_value84,canonical_value85,canonical_value88,canonical_value89,canonical_value90,encoded_value265,encoded_value271,encoded_value192,encoded_value198,encoded_value203,encoded_value215,encoded_value221,encoded_value227,encoded_value253,encoded_value254,encoded_value255,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  simp only [ordered,List.all_cons,List.all_nil,order_value265_value271,order_value265_value192,order_value265_value198,order_value265_value203,order_value265_value215,order_value265_value221,order_value265_value227,order_value265_value253,order_value265_value254,order_value265_value255,order_value265_value75,order_value265_value76,order_value265_value77,order_value265_value79,order_value265_value80,order_value265_value81,order_value265_value83,order_value265_value84,order_value265_value85,order_value265_value88,order_value265_value89,order_value265_value90,order_value271_value192,order_value271_value198,order_value271_value203,order_value271_value215,order_value271_value221,order_value271_value227,order_value271_value253,order_value271_value254,order_value271_value255,order_value271_value75,order_value271_value76,order_value271_value77,order_value271_value79,order_value271_value80,order_value271_value81,order_value271_value83,order_value271_value84,order_value271_value85,order_value271_value88,order_value271_value89,order_value271_value90,order_value192_value198,order_value192_value203,order_value192_value215,order_value192_value221,order_value192_value227,order_value192_value253,order_value192_value254,order_value192_value255,order_value192_value75,order_value192_value76,order_value192_value77,order_value192_value79,order_value192_value80,order_value192_value81,order_value192_value83,order_value192_value84,order_value192_value85,order_value192_value88,order_value192_value89,order_value192_value90,order_value198_value203,order_value198_value215,order_value198_value221,order_value198_value227,order_value198_value253,order_value198_value254,order_value198_value255,order_value198_value75,order_value198_value76,order_value198_value77,order_value198_value79,order_value198_value80,order_value198_value81,order_value198_value83,order_value198_value84,order_value198_value85,order_value198_value88,order_value198_value89,order_value198_value90,order_value203_value215,order_value203_value221,order_value203_value227,order_value203_value253,order_value203_value254,order_value203_value255,order_value203_value75,order_value203_value76,order_value203_value77,order_value203_value79,order_value203_value80,order_value203_value81,order_value203_value83,order_value203_value84,order_value203_value85,order_value203_value88,order_value203_value89,order_value203_value90,order_value215_value221,order_value215_value227,order_value215_value253,order_value215_value254,order_value215_value255,order_value215_value75,order_value215_value76,order_value215_value77,order_value215_value79,order_value215_value80,order_value215_value81,order_value215_value83,order_value215_value84,order_value215_value85,order_value215_value88,order_value215_value89,order_value215_value90,order_value221_value227,order_value221_value253,order_value221_value254,order_value221_value255,order_value221_value75,order_value221_value76,order_value221_value77,order_value221_value79,order_value221_value80,order_value221_value81,order_value221_value83,order_value221_value84,order_value221_value85,order_value221_value88,order_value221_value89,order_value221_value90,order_value227_value253,order_value227_value254,order_value227_value255,order_value227_value75,order_value227_value76,order_value227_value77,order_value227_value79,order_value227_value80,order_value227_value81,order_value227_value83,order_value227_value84,order_value227_value85,order_value227_value88,order_value227_value89,order_value227_value90,order_value253_value254,order_value253_value255,order_value253_value75,order_value253_value76,order_value253_value77,order_value253_value79,order_value253_value80,order_value253_value81,order_value253_value83,order_value253_value84,order_value253_value85,order_value253_value88,order_value253_value89,order_value253_value90,order_value254_value255,order_value254_value75,order_value254_value76,order_value254_value77,order_value254_value79,order_value254_value80,order_value254_value81,order_value254_value83,order_value254_value84,order_value254_value85,order_value254_value88,order_value254_value89,order_value254_value90,order_value255_value75,order_value255_value76,order_value255_value77,order_value255_value79,order_value255_value80,order_value255_value81,order_value255_value83,order_value255_value84,order_value255_value85,order_value255_value88,order_value255_value89,order_value255_value90,order_value75_value76,order_value75_value77,order_value75_value79,order_value75_value80,order_value75_value81,order_value75_value83,order_value75_value84,order_value75_value85,order_value75_value88,order_value75_value89,order_value75_value90,order_value76_value77,order_value76_value79,order_value76_value80,order_value76_value81,order_value76_value83,order_value76_value84,order_value76_value85,order_value76_value88,order_value76_value89,order_value76_value90,order_value77_value79,order_value77_value80,order_value77_value81,order_value77_value83,order_value77_value84,order_value77_value85,order_value77_value88,order_value77_value89,order_value77_value90,order_value79_value80,order_value79_value81,order_value79_value83,order_value79_value84,order_value79_value85,order_value79_value88,order_value79_value89,order_value79_value90,order_value80_value81,order_value80_value83,order_value80_value84,order_value80_value85,order_value80_value88,order_value80_value89,order_value80_value90,order_value81_value83,order_value81_value84,order_value81_value85,order_value81_value88,order_value81_value89,order_value81_value90,order_value83_value84,order_value83_value85,order_value83_value88,order_value83_value89,order_value83_value90,order_value84_value85,order_value84_value88,order_value84_value89,order_value84_value90,order_value85_value88,order_value85_value89,order_value85_value90,order_value88_value89,order_value88_value90,order_value89_value90,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value272 : rawvalue272.length = 429183 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value265 (commaConsLength rawLength_value271 (commaConsLength rawLength_value192 (commaConsLength rawLength_value198 (commaConsLength rawLength_value203 (commaConsLength rawLength_value215 (commaConsLength rawLength_value221 (commaConsLength rawLength_value227 (commaConsLength rawLength_value253 (commaConsLength rawLength_value254 (commaConsLength rawLength_value255 (commaConsLength rawLength_value75 (commaConsLength rawLength_value76 (commaConsLength rawLength_value77 (commaConsLength rawLength_value79 (commaConsLength rawLength_value80 (commaConsLength rawLength_value81 (commaConsLength rawLength_value83 (commaConsLength rawLength_value84 (commaConsLength rawLength_value85 (commaConsLength rawLength_value88 (commaConsLength rawLength_value89 (commaSingletonLength rawLength_value90)))))))))))))))))))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value273 : Value := .integer (33)
noncomputable def rawvalue273 : Bytes := asciiBytes "[\"int\",\"33\"]"
theorem encoded_value273 : encode value273 = rawvalue273 := by
  all_goals rfl
theorem nodes_value273 : nodes value273 = 1 := by rfl
theorem depth_value273 : depth value273 = 0 := by rfl
theorem canonical_value273 : canonical models value273 = true := by decide +kernel
theorem rawLength_value273 : rawvalue273.length = 12 := by
  decide +kernel
noncomputable def value274 : Value := .function (.cons value2 value248 (.cons value45 value39 .nil))
noncomputable def rawvalue274 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue248 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue39 ++ [93])] ++ [93,93]
theorem encoded_value274 : encode value274 = rawvalue274 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value248 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value39 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value248,encoded_value45,encoded_value39]
  all_goals rfl
theorem nodes_value274 : nodes value274 = 3157 := by
  change 1 + (nodes value2 + nodes value248 + (nodes value45 + nodes value39 + 0)) = 3157
  simp only [nodes_value2,nodes_value248,nodes_value45,nodes_value39]
  all_goals decide +kernel
theorem depth_value274 : depth value274 = 12 := by
  change max (max (1 + depth value2) (1 + depth value248)) (max (max (1 + depth value45) (1 + depth value39)) (0)) = 12
  simp only [depth_value2,depth_value248,depth_value45,depth_value39]
  all_goals decide +kernel
theorem canonical_value274 : canonical models value274 = true := by
  change ((canonical models value2 && canonical models value248 && (canonical models value45 && canonical models value39 && true)) && ordered [encode value2,encode value45]) = true
  simp only [canonical_value2,canonical_value248,canonical_value45,canonical_value39,encoded_value2,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value274 : rawvalue274.length = 53250 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value248) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value39) (show ([93] : Bytes).length = 1 from by decide +kernel))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value275 : Value := .set (.cons value260 (.cons value268 (.cons value274 .nil)))
noncomputable def rawvalue275 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue260,rawvalue268,rawvalue274] ++ [93,93]
theorem encoded_value275 : encode value275 = rawvalue275 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value260,encode value268,encode value274] ++ [93,93] = _
  simp only [encoded_value260,encoded_value268,encoded_value274]
  all_goals rfl
theorem order_value260_value274 : byteLess rawvalue260 rawvalue274 = true := by
  simp only [rawvalue260,rawvalue274,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value268_value274 : byteLess rawvalue268 rawvalue274 = true := by
  simp only [rawvalue268,rawvalue274,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue38,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value275 : nodes value275 = 9472 := by
  change 1 + (nodes value260 + (nodes value268 + (nodes value274 + 0))) = 9472
  simp only [nodes_value260,nodes_value268,nodes_value274]
  all_goals decide +kernel
theorem depth_value275 : depth value275 = 13 := by
  change max (1 + depth value260) (max (1 + depth value268) (max (1 + depth value274) (0))) = 13
  simp only [depth_value260,depth_value268,depth_value274]
  all_goals decide +kernel
theorem canonical_value275 : canonical models value275 = true := by
  change ((canonical models value260 && (canonical models value268 && (canonical models value274 && true))) && ordered [encode value260,encode value268,encode value274]) = true
  simp only [canonical_value260,canonical_value268,canonical_value274,encoded_value260,encoded_value268,encoded_value274]
  simp only [ordered,List.all_cons,List.all_nil,order_value260_value268,order_value260_value274,order_value268_value274,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value275 : rawvalue275.length = 159762 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value260 (commaConsLength rawLength_value268 (commaSingletonLength rawLength_value274)))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value276 : Value := .function (.cons value37 value262 (.cons value38 value262 (.cons value39 value262 (.cons value43 value64 .nil))))
noncomputable def rawvalue276 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue37 ++ [44] ++ rawvalue262 ++ [93]),([91] ++ rawvalue38 ++ [44] ++ rawvalue262 ++ [93]),([91] ++ rawvalue39 ++ [44] ++ rawvalue262 ++ [93]),([91] ++ rawvalue43 ++ [44] ++ rawvalue64 ++ [93])] ++ [93,93]
theorem encoded_value276 : encode value276 = rawvalue276 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value37 ++ [44] ++ encode value262 ++ [93]),([91] ++ encode value38 ++ [44] ++ encode value262 ++ [93]),([91] ++ encode value39 ++ [44] ++ encode value262 ++ [93]),([91] ++ encode value43 ++ [44] ++ encode value64 ++ [93])] ++ [93,93] = _
  simp only [encoded_value37,encoded_value262,encoded_value38,encoded_value39,encoded_value43,encoded_value64]
  all_goals rfl
theorem nodes_value276 : nodes value276 = 9 := by
  change 1 + (nodes value37 + nodes value262 + (nodes value38 + nodes value262 + (nodes value39 + nodes value262 + (nodes value43 + nodes value64 + 0)))) = 9
  simp only [nodes_value37,nodes_value262,nodes_value38,nodes_value39,nodes_value43,nodes_value64]
  all_goals decide +kernel
theorem depth_value276 : depth value276 = 1 := by
  change max (max (1 + depth value37) (1 + depth value262)) (max (max (1 + depth value38) (1 + depth value262)) (max (max (1 + depth value39) (1 + depth value262)) (max (max (1 + depth value43) (1 + depth value64)) (0)))) = 1
  simp only [depth_value37,depth_value262,depth_value38,depth_value39,depth_value43,depth_value64]
  all_goals decide +kernel
theorem canonical_value276 : canonical models value276 = true := by
  change ((canonical models value37 && canonical models value262 && (canonical models value38 && canonical models value262 && (canonical models value39 && canonical models value262 && (canonical models value43 && canonical models value64 && true)))) && ordered [encode value37,encode value38,encode value39,encode value43]) = true
  simp only [canonical_value37,canonical_value262,canonical_value38,canonical_value39,canonical_value43,canonical_value64,encoded_value37,encoded_value38,encoded_value39,encoded_value43]
  simp only [ordered,List.all_cons,List.all_nil,order_value37_value38,order_value37_value39,order_value37_value43,order_value38_value39,order_value38_value43,order_value39_value43,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value276 : rawvalue276.length = 125 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value37) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value262) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value38) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value262) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value39) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value262) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value43) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value64) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value277 : Value := .function (.cons value2 value248 (.cons value72 value232 (.cons value73 value264 (.cons value45 value39 .nil))))
noncomputable def rawvalue277 : Bytes := asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ rawvalue2 ++ [44] ++ rawvalue248 ++ [93]),([91] ++ rawvalue72 ++ [44] ++ rawvalue232 ++ [93]),([91] ++ rawvalue73 ++ [44] ++ rawvalue264 ++ [93]),([91] ++ rawvalue45 ++ [44] ++ rawvalue39 ++ [93])] ++ [93,93]
theorem encoded_value277 : encode value277 = rawvalue277 := by
  change asciiBytes "[\"fun\",[" ++ List.intercalate [44] [([91] ++ encode value2 ++ [44] ++ encode value248 ++ [93]),([91] ++ encode value72 ++ [44] ++ encode value232 ++ [93]),([91] ++ encode value73 ++ [44] ++ encode value264 ++ [93]),([91] ++ encode value45 ++ [44] ++ encode value39 ++ [93])] ++ [93,93] = _
  simp only [encoded_value2,encoded_value248,encoded_value72,encoded_value232,encoded_value73,encoded_value264,encoded_value45,encoded_value39]
  all_goals rfl
theorem nodes_value277 : nodes value277 = 5926 := by
  change 1 + (nodes value2 + nodes value248 + (nodes value72 + nodes value232 + (nodes value73 + nodes value264 + (nodes value45 + nodes value39 + 0)))) = 5926
  simp only [nodes_value2,nodes_value248,nodes_value72,nodes_value232,nodes_value73,nodes_value264,nodes_value45,nodes_value39]
  all_goals decide +kernel
theorem depth_value277 : depth value277 = 12 := by
  change max (max (1 + depth value2) (1 + depth value248)) (max (max (1 + depth value72) (1 + depth value232)) (max (max (1 + depth value73) (1 + depth value264)) (max (max (1 + depth value45) (1 + depth value39)) (0)))) = 12
  simp only [depth_value2,depth_value248,depth_value72,depth_value232,depth_value73,depth_value264,depth_value45,depth_value39]
  all_goals decide +kernel
theorem canonical_value277 : canonical models value277 = true := by
  change ((canonical models value2 && canonical models value248 && (canonical models value72 && canonical models value232 && (canonical models value73 && canonical models value264 && (canonical models value45 && canonical models value39 && true)))) && ordered [encode value2,encode value72,encode value73,encode value45]) = true
  simp only [canonical_value2,canonical_value248,canonical_value72,canonical_value232,canonical_value73,canonical_value264,canonical_value45,canonical_value39,encoded_value2,encoded_value72,encoded_value73,encoded_value45]
  simp only [ordered,List.all_cons,List.all_nil,order_value2_value72,order_value2_value73,order_value2_value45,order_value72_value73,order_value72_value45,order_value73_value45,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value277 : rawvalue277.length = 100016 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"fun\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value2) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value248) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value72) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value232) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaConsLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value73) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value264) (show ([93] : Bytes).length = 1 from by decide +kernel)) (commaSingletonLength (byteAppendLength (byteAppendLength (byteAppendLength (byteAppendLength (show ([91] : Bytes).length = 1 from by decide +kernel) rawLength_value45) (show ([44] : Bytes).length = 1 from by decide +kernel)) rawLength_value39) (show ([93] : Bytes).length = 1 from by decide +kernel))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value278 : Value := .set (.cons value265 (.cons value271 (.cons value277 (.cons value192 (.cons value198 (.cons value203 (.cons value215 (.cons value221 (.cons value227 (.cons value253 (.cons value254 (.cons value255 (.cons value75 (.cons value76 (.cons value77 (.cons value79 (.cons value80 (.cons value81 (.cons value83 (.cons value84 (.cons value85 (.cons value88 (.cons value89 (.cons value90 .nil))))))))))))))))))))))))
noncomputable def rawvalue278 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue265,rawvalue271,rawvalue277,rawvalue192,rawvalue198,rawvalue203,rawvalue215,rawvalue221,rawvalue227,rawvalue253,rawvalue254,rawvalue255,rawvalue75,rawvalue76,rawvalue77,rawvalue79,rawvalue80,rawvalue81,rawvalue83,rawvalue84,rawvalue85,rawvalue88,rawvalue89,rawvalue90] ++ [93,93]
theorem encoded_value278 : encode value278 = rawvalue278 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value265,encode value271,encode value277,encode value192,encode value198,encode value203,encode value215,encode value221,encode value227,encode value253,encode value254,encode value255,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90] ++ [93,93] = _
  simp only [encoded_value265,encoded_value271,encoded_value277,encoded_value192,encoded_value198,encoded_value203,encoded_value215,encoded_value221,encoded_value227,encoded_value253,encoded_value254,encoded_value255,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  all_goals rfl
theorem order_value265_value277 : byteLess rawvalue265 rawvalue277 = true := by
  simp only [rawvalue265,rawvalue277,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue37,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value271_value277 : byteLess rawvalue271 rawvalue277 = true := by
  simp only [rawvalue271,rawvalue277,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue38,rawvalue39,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value192 : byteLess rawvalue277 rawvalue192 = true := by
  simp only [rawvalue277,rawvalue192,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue173,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value198 : byteLess rawvalue277 rawvalue198 = true := by
  simp only [rawvalue277,rawvalue198,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue173,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value203 : byteLess rawvalue277 rawvalue203 = true := by
  simp only [rawvalue277,rawvalue203,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue173,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value215 : byteLess rawvalue277 rawvalue215 = true := by
  simp only [rawvalue277,rawvalue215,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value221 : byteLess rawvalue277 rawvalue221 = true := by
  simp only [rawvalue277,rawvalue221,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value227 : byteLess rawvalue277 rawvalue227 = true := by
  simp only [rawvalue277,rawvalue227,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue210,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value253 : byteLess rawvalue277 rawvalue253 = true := by
  simp only [rawvalue277,rawvalue253,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value254 : byteLess rawvalue277 rawvalue254 = true := by
  simp only [rawvalue277,rawvalue254,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value255 : byteLess rawvalue277 rawvalue255 = true := by
  simp only [rawvalue277,rawvalue255,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue232,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue109,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value75 : byteLess rawvalue277 rawvalue75 = true := by
  simp only [rawvalue277,rawvalue75,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value76 : byteLess rawvalue277 rawvalue76 = true := by
  simp only [rawvalue277,rawvalue76,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value77 : byteLess rawvalue277 rawvalue77 = true := by
  simp only [rawvalue277,rawvalue77,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue25,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue7,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value79 : byteLess rawvalue277 rawvalue79 = true := by
  simp only [rawvalue277,rawvalue79,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value80 : byteLess rawvalue277 rawvalue80 = true := by
  simp only [rawvalue277,rawvalue80,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value81 : byteLess rawvalue277 rawvalue81 = true := by
  simp only [rawvalue277,rawvalue81,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue35,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue3,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value83 : byteLess rawvalue277 rawvalue83 = true := by
  simp only [rawvalue277,rawvalue83,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value84 : byteLess rawvalue277 rawvalue84 = true := by
  simp only [rawvalue277,rawvalue84,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value85 : byteLess rawvalue277 rawvalue85 = true := by
  simp only [rawvalue277,rawvalue85,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue34,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue240,rawvalue6,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value88 : byteLess rawvalue277 rawvalue88 = true := by
  simp only [rawvalue277,rawvalue88,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value89 : byteLess rawvalue277 rawvalue89 = true := by
  simp only [rawvalue277,rawvalue89,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem order_value277_value90 : byteLess rawvalue277 rawvalue90 = true := by
  simp only [rawvalue277,rawvalue90,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  simp only [rawvalue248,rawvalue15,List.intercalate_cons_cons,List.intercalate_singleton,List.intercalate_nil,List.append_assoc,byteLessCommonPrefix]
  all_goals decide +kernel
theorem nodes_value278 : nodes value278 = 31339 := by
  change 1 + (nodes value265 + (nodes value271 + (nodes value277 + (nodes value192 + (nodes value198 + (nodes value203 + (nodes value215 + (nodes value221 + (nodes value227 + (nodes value253 + (nodes value254 + (nodes value255 + (nodes value75 + (nodes value76 + (nodes value77 + (nodes value79 + (nodes value80 + (nodes value81 + (nodes value83 + (nodes value84 + (nodes value85 + (nodes value88 + (nodes value89 + (nodes value90 + 0)))))))))))))))))))))))) = 31339
  simp only [nodes_value265,nodes_value271,nodes_value277,nodes_value192,nodes_value198,nodes_value203,nodes_value215,nodes_value221,nodes_value227,nodes_value253,nodes_value254,nodes_value255,nodes_value75,nodes_value76,nodes_value77,nodes_value79,nodes_value80,nodes_value81,nodes_value83,nodes_value84,nodes_value85,nodes_value88,nodes_value89,nodes_value90]
  all_goals decide +kernel
theorem depth_value278 : depth value278 = 13 := by
  change max (1 + depth value265) (max (1 + depth value271) (max (1 + depth value277) (max (1 + depth value192) (max (1 + depth value198) (max (1 + depth value203) (max (1 + depth value215) (max (1 + depth value221) (max (1 + depth value227) (max (1 + depth value253) (max (1 + depth value254) (max (1 + depth value255) (max (1 + depth value75) (max (1 + depth value76) (max (1 + depth value77) (max (1 + depth value79) (max (1 + depth value80) (max (1 + depth value81) (max (1 + depth value83) (max (1 + depth value84) (max (1 + depth value85) (max (1 + depth value88) (max (1 + depth value89) (max (1 + depth value90) (0)))))))))))))))))))))))) = 13
  simp only [depth_value265,depth_value271,depth_value277,depth_value192,depth_value198,depth_value203,depth_value215,depth_value221,depth_value227,depth_value253,depth_value254,depth_value255,depth_value75,depth_value76,depth_value77,depth_value79,depth_value80,depth_value81,depth_value83,depth_value84,depth_value85,depth_value88,depth_value89,depth_value90]
  all_goals decide +kernel
theorem canonical_value278 : canonical models value278 = true := by
  change ((canonical models value265 && (canonical models value271 && (canonical models value277 && (canonical models value192 && (canonical models value198 && (canonical models value203 && (canonical models value215 && (canonical models value221 && (canonical models value227 && (canonical models value253 && (canonical models value254 && (canonical models value255 && (canonical models value75 && (canonical models value76 && (canonical models value77 && (canonical models value79 && (canonical models value80 && (canonical models value81 && (canonical models value83 && (canonical models value84 && (canonical models value85 && (canonical models value88 && (canonical models value89 && (canonical models value90 && true)))))))))))))))))))))))) && ordered [encode value265,encode value271,encode value277,encode value192,encode value198,encode value203,encode value215,encode value221,encode value227,encode value253,encode value254,encode value255,encode value75,encode value76,encode value77,encode value79,encode value80,encode value81,encode value83,encode value84,encode value85,encode value88,encode value89,encode value90]) = true
  simp only [canonical_value265,canonical_value271,canonical_value277,canonical_value192,canonical_value198,canonical_value203,canonical_value215,canonical_value221,canonical_value227,canonical_value253,canonical_value254,canonical_value255,canonical_value75,canonical_value76,canonical_value77,canonical_value79,canonical_value80,canonical_value81,canonical_value83,canonical_value84,canonical_value85,canonical_value88,canonical_value89,canonical_value90,encoded_value265,encoded_value271,encoded_value277,encoded_value192,encoded_value198,encoded_value203,encoded_value215,encoded_value221,encoded_value227,encoded_value253,encoded_value254,encoded_value255,encoded_value75,encoded_value76,encoded_value77,encoded_value79,encoded_value80,encoded_value81,encoded_value83,encoded_value84,encoded_value85,encoded_value88,encoded_value89,encoded_value90]
  simp only [ordered,List.all_cons,List.all_nil,order_value265_value271,order_value265_value277,order_value265_value192,order_value265_value198,order_value265_value203,order_value265_value215,order_value265_value221,order_value265_value227,order_value265_value253,order_value265_value254,order_value265_value255,order_value265_value75,order_value265_value76,order_value265_value77,order_value265_value79,order_value265_value80,order_value265_value81,order_value265_value83,order_value265_value84,order_value265_value85,order_value265_value88,order_value265_value89,order_value265_value90,order_value271_value277,order_value271_value192,order_value271_value198,order_value271_value203,order_value271_value215,order_value271_value221,order_value271_value227,order_value271_value253,order_value271_value254,order_value271_value255,order_value271_value75,order_value271_value76,order_value271_value77,order_value271_value79,order_value271_value80,order_value271_value81,order_value271_value83,order_value271_value84,order_value271_value85,order_value271_value88,order_value271_value89,order_value271_value90,order_value277_value192,order_value277_value198,order_value277_value203,order_value277_value215,order_value277_value221,order_value277_value227,order_value277_value253,order_value277_value254,order_value277_value255,order_value277_value75,order_value277_value76,order_value277_value77,order_value277_value79,order_value277_value80,order_value277_value81,order_value277_value83,order_value277_value84,order_value277_value85,order_value277_value88,order_value277_value89,order_value277_value90,order_value192_value198,order_value192_value203,order_value192_value215,order_value192_value221,order_value192_value227,order_value192_value253,order_value192_value254,order_value192_value255,order_value192_value75,order_value192_value76,order_value192_value77,order_value192_value79,order_value192_value80,order_value192_value81,order_value192_value83,order_value192_value84,order_value192_value85,order_value192_value88,order_value192_value89,order_value192_value90,order_value198_value203,order_value198_value215,order_value198_value221,order_value198_value227,order_value198_value253,order_value198_value254,order_value198_value255,order_value198_value75,order_value198_value76,order_value198_value77,order_value198_value79,order_value198_value80,order_value198_value81,order_value198_value83,order_value198_value84,order_value198_value85,order_value198_value88,order_value198_value89,order_value198_value90,order_value203_value215,order_value203_value221,order_value203_value227,order_value203_value253,order_value203_value254,order_value203_value255,order_value203_value75,order_value203_value76,order_value203_value77,order_value203_value79,order_value203_value80,order_value203_value81,order_value203_value83,order_value203_value84,order_value203_value85,order_value203_value88,order_value203_value89,order_value203_value90,order_value215_value221,order_value215_value227,order_value215_value253,order_value215_value254,order_value215_value255,order_value215_value75,order_value215_value76,order_value215_value77,order_value215_value79,order_value215_value80,order_value215_value81,order_value215_value83,order_value215_value84,order_value215_value85,order_value215_value88,order_value215_value89,order_value215_value90,order_value221_value227,order_value221_value253,order_value221_value254,order_value221_value255,order_value221_value75,order_value221_value76,order_value221_value77,order_value221_value79,order_value221_value80,order_value221_value81,order_value221_value83,order_value221_value84,order_value221_value85,order_value221_value88,order_value221_value89,order_value221_value90,order_value227_value253,order_value227_value254,order_value227_value255,order_value227_value75,order_value227_value76,order_value227_value77,order_value227_value79,order_value227_value80,order_value227_value81,order_value227_value83,order_value227_value84,order_value227_value85,order_value227_value88,order_value227_value89,order_value227_value90,order_value253_value254,order_value253_value255,order_value253_value75,order_value253_value76,order_value253_value77,order_value253_value79,order_value253_value80,order_value253_value81,order_value253_value83,order_value253_value84,order_value253_value85,order_value253_value88,order_value253_value89,order_value253_value90,order_value254_value255,order_value254_value75,order_value254_value76,order_value254_value77,order_value254_value79,order_value254_value80,order_value254_value81,order_value254_value83,order_value254_value84,order_value254_value85,order_value254_value88,order_value254_value89,order_value254_value90,order_value255_value75,order_value255_value76,order_value255_value77,order_value255_value79,order_value255_value80,order_value255_value81,order_value255_value83,order_value255_value84,order_value255_value85,order_value255_value88,order_value255_value89,order_value255_value90,order_value75_value76,order_value75_value77,order_value75_value79,order_value75_value80,order_value75_value81,order_value75_value83,order_value75_value84,order_value75_value85,order_value75_value88,order_value75_value89,order_value75_value90,order_value76_value77,order_value76_value79,order_value76_value80,order_value76_value81,order_value76_value83,order_value76_value84,order_value76_value85,order_value76_value88,order_value76_value89,order_value76_value90,order_value77_value79,order_value77_value80,order_value77_value81,order_value77_value83,order_value77_value84,order_value77_value85,order_value77_value88,order_value77_value89,order_value77_value90,order_value79_value80,order_value79_value81,order_value79_value83,order_value79_value84,order_value79_value85,order_value79_value88,order_value79_value89,order_value79_value90,order_value80_value81,order_value80_value83,order_value80_value84,order_value80_value85,order_value80_value88,order_value80_value89,order_value80_value90,order_value81_value83,order_value81_value84,order_value81_value85,order_value81_value88,order_value81_value89,order_value81_value90,order_value83_value84,order_value83_value85,order_value83_value88,order_value83_value89,order_value83_value90,order_value84_value85,order_value84_value88,order_value84_value89,order_value84_value90,order_value85_value88,order_value85_value89,order_value85_value90,order_value88_value89,order_value88_value90,order_value89_value90,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value278 : rawvalue278.length = 529200 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaConsLength rawLength_value265 (commaConsLength rawLength_value271 (commaConsLength rawLength_value277 (commaConsLength rawLength_value192 (commaConsLength rawLength_value198 (commaConsLength rawLength_value203 (commaConsLength rawLength_value215 (commaConsLength rawLength_value221 (commaConsLength rawLength_value227 (commaConsLength rawLength_value253 (commaConsLength rawLength_value254 (commaConsLength rawLength_value255 (commaConsLength rawLength_value75 (commaConsLength rawLength_value76 (commaConsLength rawLength_value77 (commaConsLength rawLength_value79 (commaConsLength rawLength_value80 (commaConsLength rawLength_value81 (commaConsLength rawLength_value83 (commaConsLength rawLength_value84 (commaConsLength rawLength_value85 (commaConsLength rawLength_value88 (commaConsLength rawLength_value89 (commaSingletonLength rawLength_value90))))))))))))))))))))))))) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
noncomputable def value279 : Value := .set (.cons value88 .nil)
noncomputable def rawvalue279 : Bytes := asciiBytes "[\"set\",[" ++ List.intercalate [44] [rawvalue88] ++ [93,93]
theorem encoded_value279 : encode value279 = rawvalue279 := by
  change asciiBytes "[\"set\",[" ++ List.intercalate [44] [encode value88] ++ [93,93] = _
  simp only [encoded_value88]
  all_goals rfl
theorem nodes_value279 : nodes value279 = 16 := by
  change 1 + (nodes value88 + 0) = 16
  simp only [nodes_value88]
  all_goals decide +kernel
theorem depth_value279 : depth value279 = 3 := by
  change max (1 + depth value88) (0) = 3
  simp only [depth_value88]
  all_goals decide +kernel
theorem canonical_value279 : canonical models value279 = true := by
  change ((canonical models value88 && true) && ordered [encode value88]) = true
  simp only [canonical_value88,encoded_value88]
  simp only [ordered,List.all_cons,List.all_nil,Bool.true_and]
  all_goals decide +kernel
theorem rawLength_value279 : rawvalue279.length = 274 := by
  have assembled := (byteAppendLength (byteAppendLength (show (asciiBytes "[\"set\",[" : Bytes).length = 8 from by decide +kernel) (commaSingletonLength rawLength_value88)) (show ([93,93] : Bytes).length = 2 from by decide +kernel))
  exact assembled
end DeltaReduce.PublicStateValues
