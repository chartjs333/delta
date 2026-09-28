---- MODULE BFamilySpike ----
EXTENDS Integers, FiniteSets, Sequences, TLC
CONSTANTS Tickets, Domains, Shards, Validators,
    InitialByzantine,
    Heights,
    ValidatorEpochs,
    ConfigBodies,
    Workers,
    DataRanges,
    BatchBudgets,
    StepBudgets,
    ParentCheckpoints,
    ParameterSchemas,
    ArithmeticProfiles,
    StoragePeers,
    ContentIds,
    CompletedTickets,
    RequiredTickets,
    ConfiguredClosePolicy,
    SeedValues,
    ExpectedSeedValue,
    NormEvidenceValues,
    ValidNormEvidence,
    CoefficientProfiles,
    ConfiguredCoefficientProfile,
    SafeCoefficientProfiles,
    ParameterValues,
    AccumulatorBound,
    ConfiguredParameterSchema,
    ConfiguredArithmeticProfile,
    ConfiguredParentCheckpoint,
    ApplyProfiles,
    ConfiguredApplyProfile,
    SafeApplyProfiles,
    CheckpointIds,
    InitialCurrentCheckpoint,
    ExpectedNextCheckpoint,
    ModelHashes,
    OptimizerHashes,
    Views,
    MaxLogicalTime,
    SoftDeadline,
    HardDeadline,
    MaxMessageCopies,
    ConfiguredAbortReason,
    F,
    MaxDurableSequence,
    MaxLeaseEpoch,
    MaxModeledRejections,
    MaxModeledCertificateRejections,
    MaxModeledReduceApplyRejections,
    AvailabilityThreshold,
    MaxRepairAttempts,
    EnableQuorumActions,
    EnableFailures,
    EnableMessageDrop,
    EnableTicketActions,
    EnableAvailabilityActions,
    EnableAvailabilityFaults,
    EnableCertificateActions,
    EnablePlanningActions,
    EnableCertificateFaults,
    EnableFrankensteinFaults,
    EnableReduceApplyActions,
    EnableAggregateActions,
    EnableApplyActions,
    EnablePublicationActions,
    EnableReduceApplyFaults,
    EnableNetworkFaults,
    EnablePartitionActions,
    EnableTimeoutActions
VARIABLES stage, originalJournal, originalQC, p0_abortQCs, p0_abortReason, p0_abortRequests, p0_abortVotes, p0_aggregateCandidates, p0_aggregateRootQCs, p0_aggregateVotes, p0_aggregationPlanCertificates, p0_alive, p0_apcVotes, p0_applyCandidates, p0_applyQCs, p0_applyVotes, p0_availabilityAttestations, p0_availabilityCertificates, p0_availabilityShortfalls, p0_availableArtifacts, p0_availableTickets, p0_byzantine, p0_certificateRejections, p0_certificateReplayReceipts, p0_closedInputBodies, p0_commitments, p0_corruptArtifacts, p0_crashCoverage, p0_currentAdvanceReceipts, p0_currentCheckpoint, p0_currentReplayReceipts, p0_durableSequence, p0_durableVotes, p0_ecVotes, p0_eligibilityCertificates, p0_finalizedCertificates, p0_inputSetCertificates, p0_iscVotes, p0_lateAvailabilityEvidence, p0_leaseActive, p0_leaseEpoch, p0_leaseOwner, p0_logicalTime, p0_materializedArtifacts, p0_messageMultiplicity, p0_messages, p0_parameterQCs, p0_parameterResults, p0_parameterVotes, p0_partition, p0_pendingPointerRecoveries, p0_phase, p0_proposals, p0_publishedObjects, p0_receivedVotes, p0_recoveryState, p0_reduceApplyRejections, p0_rejectedCommitments, p0_rejectedPublications, p0_repairAttempts, p0_seedTranscripts, p0_ticketPlan, p0_timeoutObservations, p0_timeoutVotes, p0_view, p0_viewChangeQCs, p0_volatileVotes, p1_abortQCs, p1_abortReason, p1_abortRequests, p1_abortVotes, p1_aggregateCandidates, p1_aggregateRootQCs, p1_aggregateVotes, p1_aggregationPlanCertificates, p1_alive, p1_apcVotes, p1_applyCandidates, p1_applyQCs, p1_applyVotes, p1_availabilityAttestations, p1_availabilityCertificates, p1_availabilityShortfalls, p1_availableArtifacts, p1_availableTickets, p1_byzantine, p1_certificateRejections, p1_certificateReplayReceipts, p1_closedInputBodies, p1_commitments, p1_corruptArtifacts, p1_crashCoverage, p1_currentAdvanceReceipts, p1_currentCheckpoint, p1_currentReplayReceipts, p1_durableSequence, p1_durableVotes, p1_ecVotes, p1_eligibilityCertificates, p1_finalizedCertificates, p1_inputSetCertificates, p1_iscVotes, p1_lateAvailabilityEvidence, p1_leaseActive, p1_leaseEpoch, p1_leaseOwner, p1_logicalTime, p1_materializedArtifacts, p1_messageMultiplicity, p1_messages, p1_parameterQCs, p1_parameterResults, p1_parameterVotes, p1_partition, p1_pendingPointerRecoveries, p1_phase, p1_proposals, p1_publishedObjects, p1_receivedVotes, p1_recoveryState, p1_reduceApplyRejections, p1_rejectedCommitments, p1_rejectedPublications, p1_repairAttempts, p1_seedTranscripts, p1_ticketPlan, p1_timeoutObservations, p1_timeoutVotes, p1_view, p1_viewChangeQCs, p1_volatileVotes, p2_abortQCs, p2_abortReason, p2_abortRequests, p2_abortVotes, p2_aggregateCandidates, p2_aggregateRootQCs, p2_aggregateVotes, p2_aggregationPlanCertificates, p2_alive, p2_apcVotes, p2_applyCandidates, p2_applyQCs, p2_applyVotes, p2_availabilityAttestations, p2_availabilityCertificates, p2_availabilityShortfalls, p2_availableArtifacts, p2_availableTickets, p2_byzantine, p2_certificateRejections, p2_certificateReplayReceipts, p2_closedInputBodies, p2_commitments, p2_corruptArtifacts, p2_crashCoverage, p2_currentAdvanceReceipts, p2_currentCheckpoint, p2_currentReplayReceipts, p2_durableSequence, p2_durableVotes, p2_ecVotes, p2_eligibilityCertificates, p2_finalizedCertificates, p2_inputSetCertificates, p2_iscVotes, p2_lateAvailabilityEvidence, p2_leaseActive, p2_leaseEpoch, p2_leaseOwner, p2_logicalTime, p2_materializedArtifacts, p2_messageMultiplicity, p2_messages, p2_parameterQCs, p2_parameterResults, p2_parameterVotes, p2_partition, p2_pendingPointerRecoveries, p2_phase, p2_proposals, p2_publishedObjects, p2_receivedVotes, p2_recoveryState, p2_reduceApplyRejections, p2_rejectedCommitments, p2_rejectedPublications, p2_repairAttempts, p2_seedTranscripts, p2_ticketPlan, p2_timeoutObservations, p2_timeoutVotes, p2_view, p2_viewChangeQCs, p2_volatileVotes
ProjectedParameterValues == {-4, 1, 3, 5}
Carrier == (("command" :> "{\"action\":\"ACT-PARAM-VOTE\",\"payload\":{\"authority_id\":\"sha256:43129f4bc6a83c77d5852c2d9db8a257c156a5d1724c2016dd502fc11c03c1c4\",\"context\":\"PARAM:d00:s01:round-1\",\"denominator\":1,\"domain\":\"d00\",\"input_leaf_ids\":[\"sha256:e5d14f4b6b2203d1447f67c475a754ad8ea39058a05600fe607ffdf53a159a00\"],\"kind\":\"PARAMETER_EXPECTED\",\"numerators\":[3,-4,5],\"shard\":\"s01\"}}") @@ ("receipt" :> "{\"command_id\":\"sha256:5e3b1054fc37c385b6dee9bab2a8d73fdd8344ec23d9632a5a11931e8c13247c\",\"effect_id\":\"sha256:cf74f16f4e4c957e86acf397423895498091f7df004dddd3e450f684eb30e9c9\",\"projection_version\":\"draft1\",\"sequence\":6,\"vote\":{\"action_id\":\"ACT-PARAM-VOTE\",\"actor_id\":\"validator-1\",\"body_hash\":\"sha256:ac5ef1d07377f6e1f2f528d6c56c25377d1e7e4799c324bdc126189280d5200f\",\"height\":1,\"parent_hashes\":[\"sha256:7b161a487013f018e9efbadef4cd948c859a7c4f02076dc29cae2f332d1aece6\"],\"round_id\":\"round-1\",\"validator_epoch\":\"epoch-1\",\"vote_context_id\":\"PARAM:d00:s01:round-1\"}}") @@ ("effect" :> "{\"projection_version\":\"draft1\",\"vote\":{\"action_id\":\"ACT-PARAM-VOTE\",\"actor_id\":\"validator-1\",\"body_hash\":\"sha256:ac5ef1d07377f6e1f2f528d6c56c25377d1e7e4799c324bdc126189280d5200f\",\"height\":1,\"parent_hashes\":[\"sha256:7b161a487013f018e9efbadef4cd948c859a7c4f02076dc29cae2f332d1aece6\"],\"round_id\":\"round-1\",\"validator_epoch\":\"epoch-1\",\"vote_context_id\":\"PARAM:d00:s01:round-1\"}}") @@ ("qc" :> "sha256:27e20cab65cf621e5cdca37f7d9dec2224332509ba0d5c77ae0a28e24d77dfcc") @@ ("body" :> "sha256:ac5ef1d07377f6e1f2f528d6c56c25377d1e7e4799c324bdc126189280d5200f") @@ ("shard" :> "s01"))
Signers == <<"validator-1", "validator-2", "validator-3">>
Shard == IF stage < 11 THEN "s00" ELSE "s01"
LocalStage == stage % 11
Signer == Signers[((LocalStage - 1) \div 3) + 1]
Substep == (LocalStage - 1) % 3
Inputs0 == (("ticketOrder" :> <<"t0000", "t0001", "t0002">>) @@ ("domainOrder" :> <<"d00", "d01", "d02">>) @@ ("ticketDomain" :> (("t0000" :> "d00") @@ ("t0001" :> "d01") @@ ("t0002" :> "d02"))) @@ ("q" :> (("t0000" :> (("s00" :> 1) @@ ("s01" :> 3))) @@ ("t0001" :> (("s00" :> (-1)) @@ ("s01" :> (-3)))) @@ ("t0002" :> (("s00" :> 1) @@ ("s01" :> 3))))) @@ ("weightN" :> (("t0000" :> 1) @@ ("t0001" :> 1) @@ ("t0002" :> 1))) @@ ("weightD" :> (("t0000" :> 1) @@ ("t0001" :> 1) @@ ("t0002" :> 1))) @@ ("denominator" :> (("d00" :> 1) @@ ("d01" :> 1) @@ ("d02" :> 1))) @@ ("qN" :> (("d00" :> (("s00" :> 1) @@ ("s01" :> 1))) @@ ("d01" :> (("s00" :> 1) @@ ("s01" :> 1))) @@ ("d02" :> (("s00" :> 1) @@ ("s01" :> 1))))) @@ ("qD" :> (("d00" :> (("s00" :> 2) @@ ("s01" :> 2))) @@ ("d01" :> (("s00" :> 2) @@ ("s01" :> 2))) @@ ("d02" :> (("s00" :> 2) @@ ("s01" :> 2))))) @@ ("piN" :> (("d00" :> 1) @@ ("d01" :> 1) @@ ("d02" :> 1))) @@ ("piD" :> (("d00" :> 3) @@ ("d01" :> 3) @@ ("d02" :> 3))) @@ ("mixtureD" :> 3) @@ ("applyN" :> 1) @@ ("applyD" :> 1) @@ ("model" :> (("s00" :> 20) @@ ("s01" :> 20))) @@ ("optimizer" :> (("s00" :> 2) @@ ("s01" :> 2))) @@ ("muN" :> 1) @@ ("muD" :> 2) @@ ("lrN" :> 1) @@ ("lrD" :> 2) @@ ("wdN" :> 0) @@ ("wdD" :> 1) @@ ("limit" :> 127))
V0 == INSTANCE DeltaReducePhase6Harness WITH NativeArithmeticInputs <- Inputs0,
abortQCs <- p0_abortQCs,
abortReason <- p0_abortReason,
abortRequests <- p0_abortRequests,
abortVotes <- p0_abortVotes,
aggregateCandidates <- p0_aggregateCandidates,
aggregateRootQCs <- p0_aggregateRootQCs,
aggregateVotes <- p0_aggregateVotes,
aggregationPlanCertificates <- p0_aggregationPlanCertificates,
alive <- p0_alive,
apcVotes <- p0_apcVotes,
applyCandidates <- p0_applyCandidates,
applyQCs <- p0_applyQCs,
applyVotes <- p0_applyVotes,
availabilityAttestations <- p0_availabilityAttestations,
availabilityCertificates <- p0_availabilityCertificates,
availabilityShortfalls <- p0_availabilityShortfalls,
availableArtifacts <- p0_availableArtifacts,
availableTickets <- p0_availableTickets,
byzantine <- p0_byzantine,
certificateRejections <- p0_certificateRejections,
certificateReplayReceipts <- p0_certificateReplayReceipts,
closedInputBodies <- p0_closedInputBodies,
commitments <- p0_commitments,
corruptArtifacts <- p0_corruptArtifacts,
crashCoverage <- p0_crashCoverage,
currentAdvanceReceipts <- p0_currentAdvanceReceipts,
currentCheckpoint <- p0_currentCheckpoint,
currentReplayReceipts <- p0_currentReplayReceipts,
durableSequence <- p0_durableSequence,
durableVotes <- p0_durableVotes,
ecVotes <- p0_ecVotes,
eligibilityCertificates <- p0_eligibilityCertificates,
finalizedCertificates <- p0_finalizedCertificates,
inputSetCertificates <- p0_inputSetCertificates,
iscVotes <- p0_iscVotes,
lateAvailabilityEvidence <- p0_lateAvailabilityEvidence,
leaseActive <- p0_leaseActive,
leaseEpoch <- p0_leaseEpoch,
leaseOwner <- p0_leaseOwner,
logicalTime <- p0_logicalTime,
materializedArtifacts <- p0_materializedArtifacts,
messageMultiplicity <- p0_messageMultiplicity,
messages <- p0_messages,
parameterQCs <- p0_parameterQCs,
parameterResults <- p0_parameterResults,
parameterVotes <- p0_parameterVotes,
partition <- p0_partition,
pendingPointerRecoveries <- p0_pendingPointerRecoveries,
phase <- p0_phase,
proposals <- p0_proposals,
publishedObjects <- p0_publishedObjects,
receivedVotes <- p0_receivedVotes,
recoveryState <- p0_recoveryState,
reduceApplyRejections <- p0_reduceApplyRejections,
rejectedCommitments <- p0_rejectedCommitments,
rejectedPublications <- p0_rejectedPublications,
repairAttempts <- p0_repairAttempts,
seedTranscripts <- p0_seedTranscripts,
ticketPlan <- p0_ticketPlan,
timeoutObservations <- p0_timeoutObservations,
timeoutVotes <- p0_timeoutVotes,
view <- p0_view,
viewChangeQCs <- p0_viewChangeQCs,
volatileVotes <- p0_volatileVotes
P0 == INSTANCE DeltaReduce WITH NativeArithmeticInputs <- Inputs0,
abortQCs <- p0_abortQCs,
abortReason <- p0_abortReason,
abortRequests <- p0_abortRequests,
abortVotes <- p0_abortVotes,
aggregateCandidates <- p0_aggregateCandidates,
aggregateRootQCs <- p0_aggregateRootQCs,
aggregateVotes <- p0_aggregateVotes,
aggregationPlanCertificates <- p0_aggregationPlanCertificates,
alive <- p0_alive,
apcVotes <- p0_apcVotes,
applyCandidates <- p0_applyCandidates,
applyQCs <- p0_applyQCs,
applyVotes <- p0_applyVotes,
availabilityAttestations <- p0_availabilityAttestations,
availabilityCertificates <- p0_availabilityCertificates,
availabilityShortfalls <- p0_availabilityShortfalls,
availableArtifacts <- p0_availableArtifacts,
availableTickets <- p0_availableTickets,
byzantine <- p0_byzantine,
certificateRejections <- p0_certificateRejections,
certificateReplayReceipts <- p0_certificateReplayReceipts,
closedInputBodies <- p0_closedInputBodies,
commitments <- p0_commitments,
corruptArtifacts <- p0_corruptArtifacts,
crashCoverage <- p0_crashCoverage,
currentAdvanceReceipts <- p0_currentAdvanceReceipts,
currentCheckpoint <- p0_currentCheckpoint,
currentReplayReceipts <- p0_currentReplayReceipts,
durableSequence <- p0_durableSequence,
durableVotes <- p0_durableVotes,
ecVotes <- p0_ecVotes,
eligibilityCertificates <- p0_eligibilityCertificates,
finalizedCertificates <- p0_finalizedCertificates,
inputSetCertificates <- p0_inputSetCertificates,
iscVotes <- p0_iscVotes,
lateAvailabilityEvidence <- p0_lateAvailabilityEvidence,
leaseActive <- p0_leaseActive,
leaseEpoch <- p0_leaseEpoch,
leaseOwner <- p0_leaseOwner,
logicalTime <- p0_logicalTime,
materializedArtifacts <- p0_materializedArtifacts,
messageMultiplicity <- p0_messageMultiplicity,
messages <- p0_messages,
parameterQCs <- p0_parameterQCs,
parameterResults <- p0_parameterResults,
parameterVotes <- p0_parameterVotes,
partition <- p0_partition,
pendingPointerRecoveries <- p0_pendingPointerRecoveries,
phase <- p0_phase,
proposals <- p0_proposals,
publishedObjects <- p0_publishedObjects,
receivedVotes <- p0_receivedVotes,
recoveryState <- p0_recoveryState,
reduceApplyRejections <- p0_reduceApplyRejections,
rejectedCommitments <- p0_rejectedCommitments,
rejectedPublications <- p0_rejectedPublications,
repairAttempts <- p0_repairAttempts,
seedTranscripts <- p0_seedTranscripts,
ticketPlan <- p0_ticketPlan,
timeoutObservations <- p0_timeoutObservations,
timeoutVotes <- p0_timeoutVotes,
view <- p0_view,
viewChangeQCs <- p0_viewChangeQCs,
volatileVotes <- p0_volatileVotes
Body0(shard) == V0!ParameterResultBody(V0!HarnessAPC, "d00", shard,
    ConfiguredParentCheckpoint, ConfiguredParameterSchema, ConfiguredArithmeticProfile,
    V0!NativeParameterValue(V0!HarnessAPC, "d00", shard), TRUE)
Envelope0 == V0!VoteEnvelope(Signer, "PARAMETER",
    V0!ParameterKey("d00", Shard), Body0(Shard))
Do0 == CASE LocalStage = 0 -> V0!ProposeParameterResult(Body0(Shard))
    [] LocalStage = 10 -> V0!FinalizeParameterQC(Body0(Shard))
    [] Substep = 0 -> V0!VoteParameter(Signer, Body0(Shard))
    [] Substep = 1 -> V0!SendVoteEnvelope(Envelope0)
    [] OTHER -> V0!DeliverVoteEnvelope(Envelope0, 1)
Inputs1 == (("ticketOrder" :> <<"t0000", "t0001", "t0002">>) @@ ("domainOrder" :> <<"d00", "d01", "d02">>) @@ ("ticketDomain" :> (("t0000" :> "d00") @@ ("t0001" :> "d01") @@ ("t0002" :> "d02"))) @@ ("q" :> (("t0000" :> (("s00" :> 1) @@ ("s01" :> (-4)))) @@ ("t0001" :> (("s00" :> (-1)) @@ ("s01" :> 4))) @@ ("t0002" :> (("s00" :> 1) @@ ("s01" :> (-4)))))) @@ ("weightN" :> (("t0000" :> 1) @@ ("t0001" :> 1) @@ ("t0002" :> 1))) @@ ("weightD" :> (("t0000" :> 1) @@ ("t0001" :> 1) @@ ("t0002" :> 1))) @@ ("denominator" :> (("d00" :> 1) @@ ("d01" :> 1) @@ ("d02" :> 1))) @@ ("qN" :> (("d00" :> (("s00" :> 1) @@ ("s01" :> 1))) @@ ("d01" :> (("s00" :> 1) @@ ("s01" :> 1))) @@ ("d02" :> (("s00" :> 1) @@ ("s01" :> 1))))) @@ ("qD" :> (("d00" :> (("s00" :> 2) @@ ("s01" :> 2))) @@ ("d01" :> (("s00" :> 2) @@ ("s01" :> 2))) @@ ("d02" :> (("s00" :> 2) @@ ("s01" :> 2))))) @@ ("piN" :> (("d00" :> 1) @@ ("d01" :> 1) @@ ("d02" :> 1))) @@ ("piD" :> (("d00" :> 3) @@ ("d01" :> 3) @@ ("d02" :> 3))) @@ ("mixtureD" :> 3) @@ ("applyN" :> 1) @@ ("applyD" :> 1) @@ ("model" :> (("s00" :> 20) @@ ("s01" :> (-20)))) @@ ("optimizer" :> (("s00" :> 2) @@ ("s01" :> (-2)))) @@ ("muN" :> 1) @@ ("muD" :> 2) @@ ("lrN" :> 1) @@ ("lrD" :> 2) @@ ("wdN" :> 0) @@ ("wdD" :> 1) @@ ("limit" :> 127))
V1 == INSTANCE DeltaReducePhase6Harness WITH NativeArithmeticInputs <- Inputs1,
abortQCs <- p1_abortQCs,
abortReason <- p1_abortReason,
abortRequests <- p1_abortRequests,
abortVotes <- p1_abortVotes,
aggregateCandidates <- p1_aggregateCandidates,
aggregateRootQCs <- p1_aggregateRootQCs,
aggregateVotes <- p1_aggregateVotes,
aggregationPlanCertificates <- p1_aggregationPlanCertificates,
alive <- p1_alive,
apcVotes <- p1_apcVotes,
applyCandidates <- p1_applyCandidates,
applyQCs <- p1_applyQCs,
applyVotes <- p1_applyVotes,
availabilityAttestations <- p1_availabilityAttestations,
availabilityCertificates <- p1_availabilityCertificates,
availabilityShortfalls <- p1_availabilityShortfalls,
availableArtifacts <- p1_availableArtifacts,
availableTickets <- p1_availableTickets,
byzantine <- p1_byzantine,
certificateRejections <- p1_certificateRejections,
certificateReplayReceipts <- p1_certificateReplayReceipts,
closedInputBodies <- p1_closedInputBodies,
commitments <- p1_commitments,
corruptArtifacts <- p1_corruptArtifacts,
crashCoverage <- p1_crashCoverage,
currentAdvanceReceipts <- p1_currentAdvanceReceipts,
currentCheckpoint <- p1_currentCheckpoint,
currentReplayReceipts <- p1_currentReplayReceipts,
durableSequence <- p1_durableSequence,
durableVotes <- p1_durableVotes,
ecVotes <- p1_ecVotes,
eligibilityCertificates <- p1_eligibilityCertificates,
finalizedCertificates <- p1_finalizedCertificates,
inputSetCertificates <- p1_inputSetCertificates,
iscVotes <- p1_iscVotes,
lateAvailabilityEvidence <- p1_lateAvailabilityEvidence,
leaseActive <- p1_leaseActive,
leaseEpoch <- p1_leaseEpoch,
leaseOwner <- p1_leaseOwner,
logicalTime <- p1_logicalTime,
materializedArtifacts <- p1_materializedArtifacts,
messageMultiplicity <- p1_messageMultiplicity,
messages <- p1_messages,
parameterQCs <- p1_parameterQCs,
parameterResults <- p1_parameterResults,
parameterVotes <- p1_parameterVotes,
partition <- p1_partition,
pendingPointerRecoveries <- p1_pendingPointerRecoveries,
phase <- p1_phase,
proposals <- p1_proposals,
publishedObjects <- p1_publishedObjects,
receivedVotes <- p1_receivedVotes,
recoveryState <- p1_recoveryState,
reduceApplyRejections <- p1_reduceApplyRejections,
rejectedCommitments <- p1_rejectedCommitments,
rejectedPublications <- p1_rejectedPublications,
repairAttempts <- p1_repairAttempts,
seedTranscripts <- p1_seedTranscripts,
ticketPlan <- p1_ticketPlan,
timeoutObservations <- p1_timeoutObservations,
timeoutVotes <- p1_timeoutVotes,
view <- p1_view,
viewChangeQCs <- p1_viewChangeQCs,
volatileVotes <- p1_volatileVotes
P1 == INSTANCE DeltaReduce WITH NativeArithmeticInputs <- Inputs1,
abortQCs <- p1_abortQCs,
abortReason <- p1_abortReason,
abortRequests <- p1_abortRequests,
abortVotes <- p1_abortVotes,
aggregateCandidates <- p1_aggregateCandidates,
aggregateRootQCs <- p1_aggregateRootQCs,
aggregateVotes <- p1_aggregateVotes,
aggregationPlanCertificates <- p1_aggregationPlanCertificates,
alive <- p1_alive,
apcVotes <- p1_apcVotes,
applyCandidates <- p1_applyCandidates,
applyQCs <- p1_applyQCs,
applyVotes <- p1_applyVotes,
availabilityAttestations <- p1_availabilityAttestations,
availabilityCertificates <- p1_availabilityCertificates,
availabilityShortfalls <- p1_availabilityShortfalls,
availableArtifacts <- p1_availableArtifacts,
availableTickets <- p1_availableTickets,
byzantine <- p1_byzantine,
certificateRejections <- p1_certificateRejections,
certificateReplayReceipts <- p1_certificateReplayReceipts,
closedInputBodies <- p1_closedInputBodies,
commitments <- p1_commitments,
corruptArtifacts <- p1_corruptArtifacts,
crashCoverage <- p1_crashCoverage,
currentAdvanceReceipts <- p1_currentAdvanceReceipts,
currentCheckpoint <- p1_currentCheckpoint,
currentReplayReceipts <- p1_currentReplayReceipts,
durableSequence <- p1_durableSequence,
durableVotes <- p1_durableVotes,
ecVotes <- p1_ecVotes,
eligibilityCertificates <- p1_eligibilityCertificates,
finalizedCertificates <- p1_finalizedCertificates,
inputSetCertificates <- p1_inputSetCertificates,
iscVotes <- p1_iscVotes,
lateAvailabilityEvidence <- p1_lateAvailabilityEvidence,
leaseActive <- p1_leaseActive,
leaseEpoch <- p1_leaseEpoch,
leaseOwner <- p1_leaseOwner,
logicalTime <- p1_logicalTime,
materializedArtifacts <- p1_materializedArtifacts,
messageMultiplicity <- p1_messageMultiplicity,
messages <- p1_messages,
parameterQCs <- p1_parameterQCs,
parameterResults <- p1_parameterResults,
parameterVotes <- p1_parameterVotes,
partition <- p1_partition,
pendingPointerRecoveries <- p1_pendingPointerRecoveries,
phase <- p1_phase,
proposals <- p1_proposals,
publishedObjects <- p1_publishedObjects,
receivedVotes <- p1_receivedVotes,
recoveryState <- p1_recoveryState,
reduceApplyRejections <- p1_reduceApplyRejections,
rejectedCommitments <- p1_rejectedCommitments,
rejectedPublications <- p1_rejectedPublications,
repairAttempts <- p1_repairAttempts,
seedTranscripts <- p1_seedTranscripts,
ticketPlan <- p1_ticketPlan,
timeoutObservations <- p1_timeoutObservations,
timeoutVotes <- p1_timeoutVotes,
view <- p1_view,
viewChangeQCs <- p1_viewChangeQCs,
volatileVotes <- p1_volatileVotes
Body1(shard) == V1!ParameterResultBody(V1!HarnessAPC, "d00", shard,
    ConfiguredParentCheckpoint, ConfiguredParameterSchema, ConfiguredArithmeticProfile,
    V1!NativeParameterValue(V1!HarnessAPC, "d00", shard), TRUE)
Envelope1 == V1!VoteEnvelope(Signer, "PARAMETER",
    V1!ParameterKey("d00", Shard), Body1(Shard))
Do1 == CASE LocalStage = 0 -> V1!ProposeParameterResult(Body1(Shard))
    [] LocalStage = 10 -> V1!FinalizeParameterQC(Body1(Shard))
    [] Substep = 0 -> V1!VoteParameter(Signer, Body1(Shard))
    [] Substep = 1 -> V1!SendVoteEnvelope(Envelope1)
    [] OTHER -> V1!DeliverVoteEnvelope(Envelope1, 1)
Inputs2 == (("ticketOrder" :> <<"t0000", "t0001", "t0002">>) @@ ("domainOrder" :> <<"d00", "d01", "d02">>) @@ ("ticketDomain" :> (("t0000" :> "d00") @@ ("t0001" :> "d01") @@ ("t0002" :> "d02"))) @@ ("q" :> (("t0000" :> (("s00" :> 1) @@ ("s01" :> 5))) @@ ("t0001" :> (("s00" :> (-1)) @@ ("s01" :> (-5)))) @@ ("t0002" :> (("s00" :> 1) @@ ("s01" :> 5))))) @@ ("weightN" :> (("t0000" :> 1) @@ ("t0001" :> 1) @@ ("t0002" :> 1))) @@ ("weightD" :> (("t0000" :> 1) @@ ("t0001" :> 1) @@ ("t0002" :> 1))) @@ ("denominator" :> (("d00" :> 1) @@ ("d01" :> 1) @@ ("d02" :> 1))) @@ ("qN" :> (("d00" :> (("s00" :> 1) @@ ("s01" :> 1))) @@ ("d01" :> (("s00" :> 1) @@ ("s01" :> 1))) @@ ("d02" :> (("s00" :> 1) @@ ("s01" :> 1))))) @@ ("qD" :> (("d00" :> (("s00" :> 2) @@ ("s01" :> 2))) @@ ("d01" :> (("s00" :> 2) @@ ("s01" :> 2))) @@ ("d02" :> (("s00" :> 2) @@ ("s01" :> 2))))) @@ ("piN" :> (("d00" :> 1) @@ ("d01" :> 1) @@ ("d02" :> 1))) @@ ("piD" :> (("d00" :> 3) @@ ("d01" :> 3) @@ ("d02" :> 3))) @@ ("mixtureD" :> 3) @@ ("applyN" :> 1) @@ ("applyD" :> 1) @@ ("model" :> (("s00" :> 20) @@ ("s01" :> 20))) @@ ("optimizer" :> (("s00" :> 2) @@ ("s01" :> 2))) @@ ("muN" :> 1) @@ ("muD" :> 2) @@ ("lrN" :> 1) @@ ("lrD" :> 2) @@ ("wdN" :> 0) @@ ("wdD" :> 1) @@ ("limit" :> 127))
V2 == INSTANCE DeltaReducePhase6Harness WITH NativeArithmeticInputs <- Inputs2,
abortQCs <- p2_abortQCs,
abortReason <- p2_abortReason,
abortRequests <- p2_abortRequests,
abortVotes <- p2_abortVotes,
aggregateCandidates <- p2_aggregateCandidates,
aggregateRootQCs <- p2_aggregateRootQCs,
aggregateVotes <- p2_aggregateVotes,
aggregationPlanCertificates <- p2_aggregationPlanCertificates,
alive <- p2_alive,
apcVotes <- p2_apcVotes,
applyCandidates <- p2_applyCandidates,
applyQCs <- p2_applyQCs,
applyVotes <- p2_applyVotes,
availabilityAttestations <- p2_availabilityAttestations,
availabilityCertificates <- p2_availabilityCertificates,
availabilityShortfalls <- p2_availabilityShortfalls,
availableArtifacts <- p2_availableArtifacts,
availableTickets <- p2_availableTickets,
byzantine <- p2_byzantine,
certificateRejections <- p2_certificateRejections,
certificateReplayReceipts <- p2_certificateReplayReceipts,
closedInputBodies <- p2_closedInputBodies,
commitments <- p2_commitments,
corruptArtifacts <- p2_corruptArtifacts,
crashCoverage <- p2_crashCoverage,
currentAdvanceReceipts <- p2_currentAdvanceReceipts,
currentCheckpoint <- p2_currentCheckpoint,
currentReplayReceipts <- p2_currentReplayReceipts,
durableSequence <- p2_durableSequence,
durableVotes <- p2_durableVotes,
ecVotes <- p2_ecVotes,
eligibilityCertificates <- p2_eligibilityCertificates,
finalizedCertificates <- p2_finalizedCertificates,
inputSetCertificates <- p2_inputSetCertificates,
iscVotes <- p2_iscVotes,
lateAvailabilityEvidence <- p2_lateAvailabilityEvidence,
leaseActive <- p2_leaseActive,
leaseEpoch <- p2_leaseEpoch,
leaseOwner <- p2_leaseOwner,
logicalTime <- p2_logicalTime,
materializedArtifacts <- p2_materializedArtifacts,
messageMultiplicity <- p2_messageMultiplicity,
messages <- p2_messages,
parameterQCs <- p2_parameterQCs,
parameterResults <- p2_parameterResults,
parameterVotes <- p2_parameterVotes,
partition <- p2_partition,
pendingPointerRecoveries <- p2_pendingPointerRecoveries,
phase <- p2_phase,
proposals <- p2_proposals,
publishedObjects <- p2_publishedObjects,
receivedVotes <- p2_receivedVotes,
recoveryState <- p2_recoveryState,
reduceApplyRejections <- p2_reduceApplyRejections,
rejectedCommitments <- p2_rejectedCommitments,
rejectedPublications <- p2_rejectedPublications,
repairAttempts <- p2_repairAttempts,
seedTranscripts <- p2_seedTranscripts,
ticketPlan <- p2_ticketPlan,
timeoutObservations <- p2_timeoutObservations,
timeoutVotes <- p2_timeoutVotes,
view <- p2_view,
viewChangeQCs <- p2_viewChangeQCs,
volatileVotes <- p2_volatileVotes
P2 == INSTANCE DeltaReduce WITH NativeArithmeticInputs <- Inputs2,
abortQCs <- p2_abortQCs,
abortReason <- p2_abortReason,
abortRequests <- p2_abortRequests,
abortVotes <- p2_abortVotes,
aggregateCandidates <- p2_aggregateCandidates,
aggregateRootQCs <- p2_aggregateRootQCs,
aggregateVotes <- p2_aggregateVotes,
aggregationPlanCertificates <- p2_aggregationPlanCertificates,
alive <- p2_alive,
apcVotes <- p2_apcVotes,
applyCandidates <- p2_applyCandidates,
applyQCs <- p2_applyQCs,
applyVotes <- p2_applyVotes,
availabilityAttestations <- p2_availabilityAttestations,
availabilityCertificates <- p2_availabilityCertificates,
availabilityShortfalls <- p2_availabilityShortfalls,
availableArtifacts <- p2_availableArtifacts,
availableTickets <- p2_availableTickets,
byzantine <- p2_byzantine,
certificateRejections <- p2_certificateRejections,
certificateReplayReceipts <- p2_certificateReplayReceipts,
closedInputBodies <- p2_closedInputBodies,
commitments <- p2_commitments,
corruptArtifacts <- p2_corruptArtifacts,
crashCoverage <- p2_crashCoverage,
currentAdvanceReceipts <- p2_currentAdvanceReceipts,
currentCheckpoint <- p2_currentCheckpoint,
currentReplayReceipts <- p2_currentReplayReceipts,
durableSequence <- p2_durableSequence,
durableVotes <- p2_durableVotes,
ecVotes <- p2_ecVotes,
eligibilityCertificates <- p2_eligibilityCertificates,
finalizedCertificates <- p2_finalizedCertificates,
inputSetCertificates <- p2_inputSetCertificates,
iscVotes <- p2_iscVotes,
lateAvailabilityEvidence <- p2_lateAvailabilityEvidence,
leaseActive <- p2_leaseActive,
leaseEpoch <- p2_leaseEpoch,
leaseOwner <- p2_leaseOwner,
logicalTime <- p2_logicalTime,
materializedArtifacts <- p2_materializedArtifacts,
messageMultiplicity <- p2_messageMultiplicity,
messages <- p2_messages,
parameterQCs <- p2_parameterQCs,
parameterResults <- p2_parameterResults,
parameterVotes <- p2_parameterVotes,
partition <- p2_partition,
pendingPointerRecoveries <- p2_pendingPointerRecoveries,
phase <- p2_phase,
proposals <- p2_proposals,
publishedObjects <- p2_publishedObjects,
receivedVotes <- p2_receivedVotes,
recoveryState <- p2_recoveryState,
reduceApplyRejections <- p2_reduceApplyRejections,
rejectedCommitments <- p2_rejectedCommitments,
rejectedPublications <- p2_rejectedPublications,
repairAttempts <- p2_repairAttempts,
seedTranscripts <- p2_seedTranscripts,
ticketPlan <- p2_ticketPlan,
timeoutObservations <- p2_timeoutObservations,
timeoutVotes <- p2_timeoutVotes,
view <- p2_view,
viewChangeQCs <- p2_viewChangeQCs,
volatileVotes <- p2_volatileVotes
Body2(shard) == V2!ParameterResultBody(V2!HarnessAPC, "d00", shard,
    ConfiguredParentCheckpoint, ConfiguredParameterSchema, ConfiguredArithmeticProfile,
    V2!NativeParameterValue(V2!HarnessAPC, "d00", shard), TRUE)
Envelope2 == V2!VoteEnvelope(Signer, "PARAMETER",
    V2!ParameterKey("d00", Shard), Body2(Shard))
Do2 == CASE LocalStage = 0 -> V2!ProposeParameterResult(Body2(Shard))
    [] LocalStage = 10 -> V2!FinalizeParameterQC(Body2(Shard))
    [] Substep = 0 -> V2!VoteParameter(Signer, Body2(Shard))
    [] Substep = 1 -> V2!SendVoteEnvelope(Envelope2)
    [] OTHER -> V2!DeliverVoteEnvelope(Envelope2, 1)
InitSpike == /\ stage = 0 /\ originalJournal = <<>> /\ originalQC = {}
 /\ V0!Phase6Init
 /\ V1!Phase6Init
 /\ V2!Phase6Init
NextSpike == /\ stage < 22 /\ stage' = stage + 1
 /\ (Do0)
 /\ (Do1)
 /\ (Do2)
 /\ originalJournal' = (IF stage = 12 THEN Append(originalJournal, Carrier.receipt) ELSE originalJournal)
 /\ originalQC' = (IF stage = 21 THEN {Carrier.qc} ELSE originalQC)
Skeleton0(votes) ==
 {[validator |-> v.validator, kind |-> v.kind, context |-> v.context] : v \in votes}
QC0 == {[domain |-> qc.body.domain, shard |-> qc.body.shard,
    signers |-> qc.signers] : qc \in p0_parameterQCs}
Results0 == {[domain |-> b.domain, shard |-> b.shard] : b \in p0_parameterResults}
Votes0 == {[validator |-> v.validator, domain |-> v.body.domain,
    shard |-> v.body.shard] : v \in p0_parameterVotes}
Copies0 == {[vote |-> Skeleton0({x.vote}), copy |-> x.copy] :
    x \in p0_messageMultiplicity}
Skeleton1(votes) ==
 {[validator |-> v.validator, kind |-> v.kind, context |-> v.context] : v \in votes}
QC1 == {[domain |-> qc.body.domain, shard |-> qc.body.shard,
    signers |-> qc.signers] : qc \in p1_parameterQCs}
Results1 == {[domain |-> b.domain, shard |-> b.shard] : b \in p1_parameterResults}
Votes1 == {[validator |-> v.validator, domain |-> v.body.domain,
    shard |-> v.body.shard] : v \in p1_parameterVotes}
Copies1 == {[vote |-> Skeleton1({x.vote}), copy |-> x.copy] :
    x \in p1_messageMultiplicity}
Skeleton2(votes) ==
 {[validator |-> v.validator, kind |-> v.kind, context |-> v.context] : v \in votes}
QC2 == {[domain |-> qc.body.domain, shard |-> qc.body.shard,
    signers |-> qc.signers] : qc \in p2_parameterQCs}
Results2 == {[domain |-> b.domain, shard |-> b.shard] : b \in p2_parameterResults}
Votes2 == {[validator |-> v.validator, domain |-> v.body.domain,
    shard |-> v.body.shard] : v \in p2_parameterVotes}
Copies2 == {[vote |-> Skeleton2({x.vote}), copy |-> x.copy] :
    x \in p2_messageMultiplicity}
CommonControl == /\ p0_abortQCs = p1_abortQCs
 /\ p0_abortReason = p1_abortReason
 /\ p0_abortRequests = p1_abortRequests
 /\ p0_abortVotes = p1_abortVotes
 /\ p0_aggregateCandidates = p1_aggregateCandidates
 /\ p0_aggregateRootQCs = p1_aggregateRootQCs
 /\ p0_aggregateVotes = p1_aggregateVotes
 /\ p0_aggregationPlanCertificates = p1_aggregationPlanCertificates
 /\ p0_alive = p1_alive
 /\ p0_apcVotes = p1_apcVotes
 /\ p0_applyCandidates = p1_applyCandidates
 /\ p0_applyQCs = p1_applyQCs
 /\ p0_applyVotes = p1_applyVotes
 /\ p0_availabilityAttestations = p1_availabilityAttestations
 /\ p0_availabilityCertificates = p1_availabilityCertificates
 /\ p0_availabilityShortfalls = p1_availabilityShortfalls
 /\ p0_availableArtifacts = p1_availableArtifacts
 /\ p0_availableTickets = p1_availableTickets
 /\ p0_byzantine = p1_byzantine
 /\ p0_certificateRejections = p1_certificateRejections
 /\ p0_certificateReplayReceipts = p1_certificateReplayReceipts
 /\ p0_closedInputBodies = p1_closedInputBodies
 /\ p0_commitments = p1_commitments
 /\ p0_corruptArtifacts = p1_corruptArtifacts
 /\ p0_crashCoverage = p1_crashCoverage
 /\ p0_currentAdvanceReceipts = p1_currentAdvanceReceipts
 /\ p0_currentCheckpoint = p1_currentCheckpoint
 /\ p0_currentReplayReceipts = p1_currentReplayReceipts
 /\ p0_durableSequence = p1_durableSequence
 /\ p0_ecVotes = p1_ecVotes
 /\ p0_eligibilityCertificates = p1_eligibilityCertificates
 /\ p0_finalizedCertificates = p1_finalizedCertificates
 /\ p0_inputSetCertificates = p1_inputSetCertificates
 /\ p0_iscVotes = p1_iscVotes
 /\ p0_lateAvailabilityEvidence = p1_lateAvailabilityEvidence
 /\ p0_leaseActive = p1_leaseActive
 /\ p0_leaseEpoch = p1_leaseEpoch
 /\ p0_leaseOwner = p1_leaseOwner
 /\ p0_logicalTime = p1_logicalTime
 /\ p0_materializedArtifacts = p1_materializedArtifacts
 /\ p0_partition = p1_partition
 /\ p0_pendingPointerRecoveries = p1_pendingPointerRecoveries
 /\ p0_phase = p1_phase
 /\ p0_proposals = p1_proposals
 /\ p0_publishedObjects = p1_publishedObjects
 /\ p0_recoveryState = p1_recoveryState
 /\ p0_reduceApplyRejections = p1_reduceApplyRejections
 /\ p0_rejectedCommitments = p1_rejectedCommitments
 /\ p0_rejectedPublications = p1_rejectedPublications
 /\ p0_repairAttempts = p1_repairAttempts
 /\ p0_seedTranscripts = p1_seedTranscripts
 /\ p0_ticketPlan = p1_ticketPlan
 /\ p0_timeoutObservations = p1_timeoutObservations
 /\ p0_timeoutVotes = p1_timeoutVotes
 /\ p0_view = p1_view
 /\ p0_viewChangeQCs = p1_viewChangeQCs
 /\ p0_abortQCs = p2_abortQCs
 /\ p0_abortReason = p2_abortReason
 /\ p0_abortRequests = p2_abortRequests
 /\ p0_abortVotes = p2_abortVotes
 /\ p0_aggregateCandidates = p2_aggregateCandidates
 /\ p0_aggregateRootQCs = p2_aggregateRootQCs
 /\ p0_aggregateVotes = p2_aggregateVotes
 /\ p0_aggregationPlanCertificates = p2_aggregationPlanCertificates
 /\ p0_alive = p2_alive
 /\ p0_apcVotes = p2_apcVotes
 /\ p0_applyCandidates = p2_applyCandidates
 /\ p0_applyQCs = p2_applyQCs
 /\ p0_applyVotes = p2_applyVotes
 /\ p0_availabilityAttestations = p2_availabilityAttestations
 /\ p0_availabilityCertificates = p2_availabilityCertificates
 /\ p0_availabilityShortfalls = p2_availabilityShortfalls
 /\ p0_availableArtifacts = p2_availableArtifacts
 /\ p0_availableTickets = p2_availableTickets
 /\ p0_byzantine = p2_byzantine
 /\ p0_certificateRejections = p2_certificateRejections
 /\ p0_certificateReplayReceipts = p2_certificateReplayReceipts
 /\ p0_closedInputBodies = p2_closedInputBodies
 /\ p0_commitments = p2_commitments
 /\ p0_corruptArtifacts = p2_corruptArtifacts
 /\ p0_crashCoverage = p2_crashCoverage
 /\ p0_currentAdvanceReceipts = p2_currentAdvanceReceipts
 /\ p0_currentCheckpoint = p2_currentCheckpoint
 /\ p0_currentReplayReceipts = p2_currentReplayReceipts
 /\ p0_durableSequence = p2_durableSequence
 /\ p0_ecVotes = p2_ecVotes
 /\ p0_eligibilityCertificates = p2_eligibilityCertificates
 /\ p0_finalizedCertificates = p2_finalizedCertificates
 /\ p0_inputSetCertificates = p2_inputSetCertificates
 /\ p0_iscVotes = p2_iscVotes
 /\ p0_lateAvailabilityEvidence = p2_lateAvailabilityEvidence
 /\ p0_leaseActive = p2_leaseActive
 /\ p0_leaseEpoch = p2_leaseEpoch
 /\ p0_leaseOwner = p2_leaseOwner
 /\ p0_logicalTime = p2_logicalTime
 /\ p0_materializedArtifacts = p2_materializedArtifacts
 /\ p0_partition = p2_partition
 /\ p0_pendingPointerRecoveries = p2_pendingPointerRecoveries
 /\ p0_phase = p2_phase
 /\ p0_proposals = p2_proposals
 /\ p0_publishedObjects = p2_publishedObjects
 /\ p0_recoveryState = p2_recoveryState
 /\ p0_reduceApplyRejections = p2_reduceApplyRejections
 /\ p0_rejectedCommitments = p2_rejectedCommitments
 /\ p0_rejectedPublications = p2_rejectedPublications
 /\ p0_repairAttempts = p2_repairAttempts
 /\ p0_seedTranscripts = p2_seedTranscripts
 /\ p0_ticketPlan = p2_ticketPlan
 /\ p0_timeoutObservations = p2_timeoutObservations
 /\ p0_timeoutVotes = p2_timeoutVotes
 /\ p0_view = p2_view
 /\ p0_viewChangeQCs = p2_viewChangeQCs
 /\ Skeleton0(p0_durableVotes) = Skeleton1(p1_durableVotes)
 /\ Skeleton0(p0_volatileVotes) = Skeleton1(p1_volatileVotes)
 /\ Skeleton0(p0_messages) = Skeleton1(p1_messages)
 /\ Skeleton0(p0_receivedVotes) = Skeleton1(p1_receivedVotes)
 /\ Skeleton0(p0_durableVotes) = Skeleton2(p2_durableVotes)
 /\ Skeleton0(p0_volatileVotes) = Skeleton2(p2_volatileVotes)
 /\ Skeleton0(p0_messages) = Skeleton2(p2_messages)
 /\ Skeleton0(p0_receivedVotes) = Skeleton2(p2_receivedVotes)
 /\ QC0 = QC1
 /\ QC0 = QC2
 /\ Results0 = Results1
 /\ Votes0 = Votes1
 /\ Copies0 = Copies1
 /\ Results0 = Results2
 /\ Votes0 = Votes2
 /\ Copies0 = Copies2
WholeRecordOnce ==
 /\ Len(originalJournal) = (IF stage >= 13 THEN 1 ELSE 0)
 /\ (stage >= 13 => originalJournal[1] = Carrier.receipt)
 /\ originalQC = (IF stage = 22 THEN {Carrier.qc} ELSE {})
 /\ (stage >= 13 => p0_durableSequence["validator-1"] = 6)
 /\ (stage = 22 => QC0 = {
    [domain |-> "d00", shard |-> "s00", signers |-> {"validator-1", "validator-2", "validator-3"}],
    [domain |-> "d00", shard |-> "s01", signers |-> {"validator-1", "validator-2", "validator-3"}]})
OriginalValues == /\ Body0("s01").value = 3
 /\ Body1("s01").value = (-4)
 /\ Body2("s01").value = 5
Types == /\ V0!Phase6TypeOK /\ V1!Phase6TypeOK /\ V2!Phase6TypeOK
Allowed == /\ ([][P0!Next]_(V0!ProtocolVariables))
 /\ ([][P1!Next]_(V1!ProtocolVariables))
 /\ ([][P2!Next]_(V2!ProtocolVariables))
====
