---- MODULE FullStateReplay ----
EXTENDS DeltaReducePublicState
CONSTANTS witnessValue_apply1, witnessValue_coeff1, witnessValue_configA, witnessValue_configB, witnessValue_content1, witnessValue_d1, witnessValue_data1, witnessValue_epoch1, witnessValue_h1, witnessValue_model1, witnessValue_next1, witnessValue_norm1, witnessValue_optimizer1, witnessValue_parent1, witnessValue_profile1, witnessValue_s1, witnessValue_schema1, witnessValue_seed1, witnessValue_shard1, witnessValue_t1, witnessValue_v1, witnessValue_v2, witnessValue_v3, witnessValue_v4, witnessValue_w1
VARIABLE witnessIndex
ReplayStates == <<
[abortQCs |-> {},
abortReason |-> "NO_ABORT",
abortRequests |-> {},
abortVotes |-> {},
aggregateCandidates |-> {},
aggregateRootQCs |-> {},
aggregateVotes |-> {},
aggregationPlanCertificates |-> {},
alive |-> {witnessValue_v1, witnessValue_v2, witnessValue_v3, witnessValue_v4},
apcVotes |-> {},
applyCandidates |-> {},
applyQCs |-> {},
applyVotes |-> {},
availabilityAttestations |-> {},
availabilityCertificates |-> {},
availabilityShortfalls |-> {},
availableArtifacts |-> {},
availableTickets |-> {},
byzantine |-> {witnessValue_v4},
certificateRejections |-> {},
certificateReplayReceipts |-> {},
closedInputBodies |-> {},
commitments |-> {},
corruptArtifacts |-> {},
crashCoverage |-> {},
currentAdvanceReceipts |-> {},
currentCheckpoint |-> witnessValue_parent1,
currentReplayReceipts |-> {},
durableSequence |-> ((witnessValue_v1 :> 0) @@ (witnessValue_v2 :> 0) @@ (witnessValue_v3 :> 0) @@ (witnessValue_v4 :> 0)),
durableVotes |-> {},
ecVotes |-> {},
eligibilityCertificates |-> {},
finalizedCertificates |-> {},
inputSetCertificates |-> {},
iscVotes |-> {},
lateAvailabilityEvidence |-> {},
leaseActive |-> {},
leaseEpoch |-> ((witnessValue_t1 :> 0)),
leaseOwner |-> ((witnessValue_t1 :> "NO_WORKER")),
logicalTime |-> 1,
materializedArtifacts |-> {},
messageMultiplicity |-> {},
messages |-> {},
parameterQCs |-> {},
parameterResults |-> {},
parameterVotes |-> {},
partition |-> {},
pendingPointerRecoveries |-> {},
phase |-> "ACTIVE",
proposals |-> {},
publishedObjects |-> {},
receivedVotes |-> {},
recoveryState |-> ((witnessValue_v1 :> "READY") @@ (witnessValue_v2 :> "READY") @@ (witnessValue_v3 :> "READY") @@ (witnessValue_v4 :> "READY")),
reduceApplyRejections |-> {},
rejectedCommitments |-> {},
rejectedPublications |-> {},
repairAttempts |-> ((witnessValue_content1 :> 0)),
seedTranscripts |-> {},
ticketPlan |-> {},
timeoutObservations |-> {},
timeoutVotes |-> {},
view |-> 0,
viewChangeQCs |-> {},
volatileVotes |-> {}],
[abortQCs |-> {},
abortReason |-> "NO_ABORT",
abortRequests |-> {},
abortVotes |-> {},
aggregateCandidates |-> {},
aggregateRootQCs |-> {},
aggregateVotes |-> {},
aggregationPlanCertificates |-> {},
alive |-> {witnessValue_v1, witnessValue_v2, witnessValue_v3, witnessValue_v4},
apcVotes |-> {},
applyCandidates |-> {},
applyQCs |-> {},
applyVotes |-> {},
availabilityAttestations |-> {},
availabilityCertificates |-> {},
availabilityShortfalls |-> {},
availableArtifacts |-> {},
availableTickets |-> {},
byzantine |-> {witnessValue_v4},
certificateRejections |-> {},
certificateReplayReceipts |-> {},
closedInputBodies |-> {},
commitments |-> {},
corruptArtifacts |-> {},
crashCoverage |-> {},
currentAdvanceReceipts |-> {},
currentCheckpoint |-> witnessValue_parent1,
currentReplayReceipts |-> {},
durableSequence |-> ((witnessValue_v1 :> 0) @@ (witnessValue_v2 :> 0) @@ (witnessValue_v3 :> 0) @@ (witnessValue_v4 :> 0)),
durableVotes |-> {},
ecVotes |-> {},
eligibilityCertificates |-> {},
finalizedCertificates |-> {},
inputSetCertificates |-> {},
iscVotes |-> {},
lateAvailabilityEvidence |-> {},
leaseActive |-> {},
leaseEpoch |-> ((witnessValue_t1 :> 0)),
leaseOwner |-> ((witnessValue_t1 :> "NO_WORKER")),
logicalTime |-> 0,
materializedArtifacts |-> {},
messageMultiplicity |-> {},
messages |-> {},
parameterQCs |-> {},
parameterResults |-> {},
parameterVotes |-> {},
partition |-> {},
pendingPointerRecoveries |-> {},
phase |-> "ACTIVE",
proposals |-> {(("body" :> witnessValue_configA) @@ ("context" :> (("epoch" :> witnessValue_epoch1) @@ ("height" :> witnessValue_h1) @@ ("kind" :> "ROUND_CONFIG"))))},
publishedObjects |-> {},
receivedVotes |-> {},
recoveryState |-> ((witnessValue_v1 :> "READY") @@ (witnessValue_v2 :> "READY") @@ (witnessValue_v3 :> "READY") @@ (witnessValue_v4 :> "READY")),
reduceApplyRejections |-> {},
rejectedCommitments |-> {},
rejectedPublications |-> {},
repairAttempts |-> ((witnessValue_content1 :> 0)),
seedTranscripts |-> {},
ticketPlan |-> {},
timeoutObservations |-> {},
timeoutVotes |-> {},
view |-> 0,
viewChangeQCs |-> {},
volatileVotes |-> {}]>>
WitnessInit == witnessIndex = 1 /\ MatchesPublicState(ReplayStates[1])
WitnessNext == /\ witnessIndex < Len(ReplayStates)
               /\ witnessIndex' = witnessIndex + 1
               /\ abortQCs' = ReplayStates[witnessIndex + 1].abortQCs
               /\ abortReason' = ReplayStates[witnessIndex + 1].abortReason
               /\ abortRequests' = ReplayStates[witnessIndex + 1].abortRequests
               /\ abortVotes' = ReplayStates[witnessIndex + 1].abortVotes
               /\ aggregateCandidates' = ReplayStates[witnessIndex + 1].aggregateCandidates
               /\ aggregateRootQCs' = ReplayStates[witnessIndex + 1].aggregateRootQCs
               /\ aggregateVotes' = ReplayStates[witnessIndex + 1].aggregateVotes
               /\ aggregationPlanCertificates' = ReplayStates[witnessIndex + 1].aggregationPlanCertificates
               /\ alive' = ReplayStates[witnessIndex + 1].alive
               /\ apcVotes' = ReplayStates[witnessIndex + 1].apcVotes
               /\ applyCandidates' = ReplayStates[witnessIndex + 1].applyCandidates
               /\ applyQCs' = ReplayStates[witnessIndex + 1].applyQCs
               /\ applyVotes' = ReplayStates[witnessIndex + 1].applyVotes
               /\ availabilityAttestations' = ReplayStates[witnessIndex + 1].availabilityAttestations
               /\ availabilityCertificates' = ReplayStates[witnessIndex + 1].availabilityCertificates
               /\ availabilityShortfalls' = ReplayStates[witnessIndex + 1].availabilityShortfalls
               /\ availableArtifacts' = ReplayStates[witnessIndex + 1].availableArtifacts
               /\ availableTickets' = ReplayStates[witnessIndex + 1].availableTickets
               /\ byzantine' = ReplayStates[witnessIndex + 1].byzantine
               /\ certificateRejections' = ReplayStates[witnessIndex + 1].certificateRejections
               /\ certificateReplayReceipts' = ReplayStates[witnessIndex + 1].certificateReplayReceipts
               /\ closedInputBodies' = ReplayStates[witnessIndex + 1].closedInputBodies
               /\ commitments' = ReplayStates[witnessIndex + 1].commitments
               /\ corruptArtifacts' = ReplayStates[witnessIndex + 1].corruptArtifacts
               /\ crashCoverage' = ReplayStates[witnessIndex + 1].crashCoverage
               /\ currentAdvanceReceipts' = ReplayStates[witnessIndex + 1].currentAdvanceReceipts
               /\ currentCheckpoint' = ReplayStates[witnessIndex + 1].currentCheckpoint
               /\ currentReplayReceipts' = ReplayStates[witnessIndex + 1].currentReplayReceipts
               /\ durableSequence' = ReplayStates[witnessIndex + 1].durableSequence
               /\ durableVotes' = ReplayStates[witnessIndex + 1].durableVotes
               /\ ecVotes' = ReplayStates[witnessIndex + 1].ecVotes
               /\ eligibilityCertificates' = ReplayStates[witnessIndex + 1].eligibilityCertificates
               /\ finalizedCertificates' = ReplayStates[witnessIndex + 1].finalizedCertificates
               /\ inputSetCertificates' = ReplayStates[witnessIndex + 1].inputSetCertificates
               /\ iscVotes' = ReplayStates[witnessIndex + 1].iscVotes
               /\ lateAvailabilityEvidence' = ReplayStates[witnessIndex + 1].lateAvailabilityEvidence
               /\ leaseActive' = ReplayStates[witnessIndex + 1].leaseActive
               /\ leaseEpoch' = ReplayStates[witnessIndex + 1].leaseEpoch
               /\ leaseOwner' = ReplayStates[witnessIndex + 1].leaseOwner
               /\ logicalTime' = ReplayStates[witnessIndex + 1].logicalTime
               /\ materializedArtifacts' = ReplayStates[witnessIndex + 1].materializedArtifacts
               /\ messageMultiplicity' = ReplayStates[witnessIndex + 1].messageMultiplicity
               /\ messages' = ReplayStates[witnessIndex + 1].messages
               /\ parameterQCs' = ReplayStates[witnessIndex + 1].parameterQCs
               /\ parameterResults' = ReplayStates[witnessIndex + 1].parameterResults
               /\ parameterVotes' = ReplayStates[witnessIndex + 1].parameterVotes
               /\ partition' = ReplayStates[witnessIndex + 1].partition
               /\ pendingPointerRecoveries' = ReplayStates[witnessIndex + 1].pendingPointerRecoveries
               /\ phase' = ReplayStates[witnessIndex + 1].phase
               /\ proposals' = ReplayStates[witnessIndex + 1].proposals
               /\ publishedObjects' = ReplayStates[witnessIndex + 1].publishedObjects
               /\ receivedVotes' = ReplayStates[witnessIndex + 1].receivedVotes
               /\ recoveryState' = ReplayStates[witnessIndex + 1].recoveryState
               /\ reduceApplyRejections' = ReplayStates[witnessIndex + 1].reduceApplyRejections
               /\ rejectedCommitments' = ReplayStates[witnessIndex + 1].rejectedCommitments
               /\ rejectedPublications' = ReplayStates[witnessIndex + 1].rejectedPublications
               /\ repairAttempts' = ReplayStates[witnessIndex + 1].repairAttempts
               /\ seedTranscripts' = ReplayStates[witnessIndex + 1].seedTranscripts
               /\ ticketPlan' = ReplayStates[witnessIndex + 1].ticketPlan
               /\ timeoutObservations' = ReplayStates[witnessIndex + 1].timeoutObservations
               /\ timeoutVotes' = ReplayStates[witnessIndex + 1].timeoutVotes
               /\ view' = ReplayStates[witnessIndex + 1].view
               /\ viewChangeQCs' = ReplayStates[witnessIndex + 1].viewChangeQCs
               /\ volatileVotes' = ReplayStates[witnessIndex + 1].volatileVotes
WitnessInitialOK == witnessIndex # 1 \/ Init
WitnessTypes == TypeOK
WitnessAllowed == [][Next]_ProtocolVariables
WitnessSelected == CASE witnessIndex = 1 -> ProposeRoundConfigAction
 [] OTHER -> UNCHANGED ProtocolVariables
WitnessLabelled == [][WitnessSelected]_<<ProtocolVariables, witnessIndex>>
====
