---- MODULE FullStateReplay ----
EXTENDS DeltaReducePublicState
CONSTANTS witnessValue_apply1, witnessValue_coeff1, witnessValue_configA, witnessValue_configB, witnessValue_content1, witnessValue_d1, witnessValue_data1, witnessValue_epoch1, witnessValue_h1, witnessValue_model1, witnessValue_next1, witnessValue_norm1, witnessValue_optimizer1, witnessValue_parent1, witnessValue_profile1, witnessValue_s1, witnessValue_schema1, witnessValue_seed1, witnessValue_shard1, witnessValue_shard2, witnessValue_t1, witnessValue_v1, witnessValue_v2, witnessValue_v3, witnessValue_v4, witnessValue_w1
VARIABLE witnessIndex
ReplayValue0 == {}
ReplayValue1 == "NO_ABORT"
ReplayValue2 == witnessValue_v1
ReplayValue3 == witnessValue_v2
ReplayValue4 == witnessValue_v3
ReplayValue5 == witnessValue_v4
ReplayValue6 == {ReplayValue2, ReplayValue3, ReplayValue4, ReplayValue5}
ReplayValue7 == {ReplayValue5}
ReplayValue8 == witnessValue_parent1
ReplayValue9 == 0
ReplayValue10 == ((ReplayValue2 :> ReplayValue9) @@ (ReplayValue3 :> ReplayValue9) @@ (ReplayValue4 :> ReplayValue9) @@ (ReplayValue5 :> ReplayValue9))
ReplayValue11 == witnessValue_t1
ReplayValue12 == ((ReplayValue11 :> ReplayValue9))
ReplayValue13 == "NO_WORKER"
ReplayValue14 == ((ReplayValue11 :> ReplayValue13))
ReplayValue15 == "ACTIVE"
ReplayValue16 == "READY"
ReplayValue17 == ((ReplayValue2 :> ReplayValue16) @@ (ReplayValue3 :> ReplayValue16) @@ (ReplayValue4 :> ReplayValue16) @@ (ReplayValue5 :> ReplayValue16))
ReplayValue18 == witnessValue_content1
ReplayValue19 == ((ReplayValue18 :> ReplayValue9))
ReplayValue20 == "body"
ReplayValue21 == witnessValue_configA
ReplayValue22 == "context"
ReplayValue23 == "epoch"
ReplayValue24 == witnessValue_epoch1
ReplayValue25 == "height"
ReplayValue26 == witnessValue_h1
ReplayValue27 == "kind"
ReplayValue28 == "ROUND_CONFIG"
ReplayValue29 == ((ReplayValue23 :> ReplayValue24) @@ (ReplayValue25 :> ReplayValue26) @@ (ReplayValue27 :> ReplayValue28))
ReplayValue30 == ((ReplayValue20 :> ReplayValue21) @@ (ReplayValue22 :> ReplayValue29))
ReplayValue31 == {ReplayValue30}
ReplayStates == <<
[abortQCs |-> ReplayValue0,
abortReason |-> ReplayValue1,
abortRequests |-> ReplayValue0,
abortVotes |-> ReplayValue0,
aggregateCandidates |-> ReplayValue0,
aggregateRootQCs |-> ReplayValue0,
aggregateVotes |-> ReplayValue0,
aggregationPlanCertificates |-> ReplayValue0,
alive |-> ReplayValue6,
apcVotes |-> ReplayValue0,
applyCandidates |-> ReplayValue0,
applyQCs |-> ReplayValue0,
applyVotes |-> ReplayValue0,
availabilityAttestations |-> ReplayValue0,
availabilityCertificates |-> ReplayValue0,
availabilityShortfalls |-> ReplayValue0,
availableArtifacts |-> ReplayValue0,
availableTickets |-> ReplayValue0,
byzantine |-> ReplayValue7,
certificateRejections |-> ReplayValue0,
certificateReplayReceipts |-> ReplayValue0,
closedInputBodies |-> ReplayValue0,
commitments |-> ReplayValue0,
corruptArtifacts |-> ReplayValue0,
crashCoverage |-> ReplayValue0,
currentAdvanceReceipts |-> ReplayValue0,
currentCheckpoint |-> ReplayValue8,
currentReplayReceipts |-> ReplayValue0,
durableSequence |-> ReplayValue10,
durableVotes |-> ReplayValue0,
ecVotes |-> ReplayValue0,
eligibilityCertificates |-> ReplayValue0,
finalizedCertificates |-> ReplayValue0,
inputSetCertificates |-> ReplayValue0,
iscVotes |-> ReplayValue0,
lateAvailabilityEvidence |-> ReplayValue0,
leaseActive |-> ReplayValue0,
leaseEpoch |-> ReplayValue12,
leaseOwner |-> ReplayValue14,
logicalTime |-> ReplayValue9,
materializedArtifacts |-> ReplayValue0,
messageMultiplicity |-> ReplayValue0,
messages |-> ReplayValue0,
parameterQCs |-> ReplayValue0,
parameterResults |-> ReplayValue0,
parameterVotes |-> ReplayValue0,
partition |-> ReplayValue0,
pendingPointerRecoveries |-> ReplayValue0,
phase |-> ReplayValue15,
proposals |-> ReplayValue0,
publishedObjects |-> ReplayValue0,
receivedVotes |-> ReplayValue0,
recoveryState |-> ReplayValue17,
reduceApplyRejections |-> ReplayValue0,
rejectedCommitments |-> ReplayValue0,
rejectedPublications |-> ReplayValue0,
repairAttempts |-> ReplayValue19,
seedTranscripts |-> ReplayValue0,
ticketPlan |-> ReplayValue0,
timeoutObservations |-> ReplayValue0,
timeoutVotes |-> ReplayValue0,
view |-> ReplayValue9,
viewChangeQCs |-> ReplayValue0,
volatileVotes |-> ReplayValue0],
[abortQCs |-> ReplayValue0,
abortReason |-> ReplayValue1,
abortRequests |-> ReplayValue0,
abortVotes |-> ReplayValue0,
aggregateCandidates |-> ReplayValue0,
aggregateRootQCs |-> ReplayValue0,
aggregateVotes |-> ReplayValue0,
aggregationPlanCertificates |-> ReplayValue0,
alive |-> ReplayValue6,
apcVotes |-> ReplayValue0,
applyCandidates |-> ReplayValue0,
applyQCs |-> ReplayValue0,
applyVotes |-> ReplayValue0,
availabilityAttestations |-> ReplayValue0,
availabilityCertificates |-> ReplayValue0,
availabilityShortfalls |-> ReplayValue0,
availableArtifacts |-> ReplayValue0,
availableTickets |-> ReplayValue0,
byzantine |-> ReplayValue7,
certificateRejections |-> ReplayValue0,
certificateReplayReceipts |-> ReplayValue0,
closedInputBodies |-> ReplayValue0,
commitments |-> ReplayValue0,
corruptArtifacts |-> ReplayValue0,
crashCoverage |-> ReplayValue0,
currentAdvanceReceipts |-> ReplayValue0,
currentCheckpoint |-> ReplayValue8,
currentReplayReceipts |-> ReplayValue0,
durableSequence |-> ReplayValue10,
durableVotes |-> ReplayValue0,
ecVotes |-> ReplayValue0,
eligibilityCertificates |-> ReplayValue0,
finalizedCertificates |-> ReplayValue0,
inputSetCertificates |-> ReplayValue0,
iscVotes |-> ReplayValue0,
lateAvailabilityEvidence |-> ReplayValue0,
leaseActive |-> ReplayValue0,
leaseEpoch |-> ReplayValue12,
leaseOwner |-> ReplayValue14,
logicalTime |-> ReplayValue9,
materializedArtifacts |-> ReplayValue0,
messageMultiplicity |-> ReplayValue0,
messages |-> ReplayValue0,
parameterQCs |-> ReplayValue0,
parameterResults |-> ReplayValue0,
parameterVotes |-> ReplayValue0,
partition |-> ReplayValue0,
pendingPointerRecoveries |-> ReplayValue0,
phase |-> ReplayValue15,
proposals |-> ReplayValue31,
publishedObjects |-> ReplayValue0,
receivedVotes |-> ReplayValue0,
recoveryState |-> ReplayValue17,
reduceApplyRejections |-> ReplayValue0,
rejectedCommitments |-> ReplayValue0,
rejectedPublications |-> ReplayValue0,
repairAttempts |-> ReplayValue19,
seedTranscripts |-> ReplayValue0,
ticketPlan |-> ReplayValue0,
timeoutObservations |-> ReplayValue0,
timeoutVotes |-> ReplayValue0,
view |-> ReplayValue9,
viewChangeQCs |-> ReplayValue0,
volatileVotes |-> ReplayValue0]>>
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
WitnessSelected == CASE witnessIndex = 1 -> PersistConfigVoteAction
 [] OTHER -> UNCHANGED ProtocolVariables
WitnessLabelled == [][WitnessSelected]_<<ProtocolVariables, witnessIndex>>
====
