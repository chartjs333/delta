------------------ MODULE DeltaReducePublicState ------------------
EXTENDS DeltaReduce

\* Candidate complete-state evidence projection; no production transition changes.
PublicStateFields ==
    {"abortQCs",
     "abortReason",
     "abortRequests",
     "abortVotes",
     "aggregateCandidates",
     "aggregateRootQCs",
     "aggregateVotes",
     "aggregationPlanCertificates",
     "alive",
     "apcVotes",
     "applyCandidates",
     "applyQCs",
     "applyVotes",
     "availabilityAttestations",
     "availabilityCertificates",
     "availabilityShortfalls",
     "availableArtifacts",
     "availableTickets",
     "byzantine",
     "certificateRejections",
     "certificateReplayReceipts",
     "closedInputBodies",
     "commitments",
     "corruptArtifacts",
     "crashCoverage",
     "currentAdvanceReceipts",
     "currentCheckpoint",
     "currentReplayReceipts",
     "durableSequence",
     "durableVotes",
     "ecVotes",
     "eligibilityCertificates",
     "finalizedCertificates",
     "inputSetCertificates",
     "iscVotes",
     "lateAvailabilityEvidence",
     "leaseActive",
     "leaseEpoch",
     "leaseOwner",
     "logicalTime",
     "materializedArtifacts",
     "messageMultiplicity",
     "messages",
     "parameterQCs",
     "parameterResults",
     "parameterVotes",
     "partition",
     "pendingPointerRecoveries",
     "phase",
     "proposals",
     "publishedObjects",
     "receivedVotes",
     "recoveryState",
     "reduceApplyRejections",
     "rejectedCommitments",
     "rejectedPublications",
     "repairAttempts",
     "seedTranscripts",
     "ticketPlan",
     "timeoutObservations",
     "timeoutVotes",
     "view",
     "viewChangeQCs",
     "volatileVotes"}

ProjectedPublicState ==
    [abortQCs |-> abortQCs,
     abortReason |-> abortReason,
     abortRequests |-> abortRequests,
     abortVotes |-> abortVotes,
     aggregateCandidates |-> aggregateCandidates,
     aggregateRootQCs |-> aggregateRootQCs,
     aggregateVotes |-> aggregateVotes,
     aggregationPlanCertificates |-> aggregationPlanCertificates,
     alive |-> alive,
     apcVotes |-> apcVotes,
     applyCandidates |-> applyCandidates,
     applyQCs |-> applyQCs,
     applyVotes |-> applyVotes,
     availabilityAttestations |-> availabilityAttestations,
     availabilityCertificates |-> availabilityCertificates,
     availabilityShortfalls |-> availabilityShortfalls,
     availableArtifacts |-> availableArtifacts,
     availableTickets |-> availableTickets,
     byzantine |-> byzantine,
     certificateRejections |-> certificateRejections,
     certificateReplayReceipts |-> certificateReplayReceipts,
     closedInputBodies |-> closedInputBodies,
     commitments |-> commitments,
     corruptArtifacts |-> corruptArtifacts,
     crashCoverage |-> crashCoverage,
     currentAdvanceReceipts |-> currentAdvanceReceipts,
     currentCheckpoint |-> currentCheckpoint,
     currentReplayReceipts |-> currentReplayReceipts,
     durableSequence |-> durableSequence,
     durableVotes |-> durableVotes,
     ecVotes |-> ecVotes,
     eligibilityCertificates |-> eligibilityCertificates,
     finalizedCertificates |-> finalizedCertificates,
     inputSetCertificates |-> inputSetCertificates,
     iscVotes |-> iscVotes,
     lateAvailabilityEvidence |-> lateAvailabilityEvidence,
     leaseActive |-> leaseActive,
     leaseEpoch |-> leaseEpoch,
     leaseOwner |-> leaseOwner,
     logicalTime |-> logicalTime,
     materializedArtifacts |-> materializedArtifacts,
     messageMultiplicity |-> messageMultiplicity,
     messages |-> messages,
     parameterQCs |-> parameterQCs,
     parameterResults |-> parameterResults,
     parameterVotes |-> parameterVotes,
     partition |-> partition,
     pendingPointerRecoveries |-> pendingPointerRecoveries,
     phase |-> phase,
     proposals |-> proposals,
     publishedObjects |-> publishedObjects,
     receivedVotes |-> receivedVotes,
     recoveryState |-> recoveryState,
     reduceApplyRejections |-> reduceApplyRejections,
     rejectedCommitments |-> rejectedCommitments,
     rejectedPublications |-> rejectedPublications,
     repairAttempts |-> repairAttempts,
     seedTranscripts |-> seedTranscripts,
     ticketPlan |-> ticketPlan,
     timeoutObservations |-> timeoutObservations,
     timeoutVotes |-> timeoutVotes,
     view |-> view,
     viewChangeQCs |-> viewChangeQCs,
     volatileVotes |-> volatileVotes]

CompletePublicState(state) == DOMAIN state = PublicStateFields

MatchesPublicState(state) ==
    /\ CompletePublicState(state)
    /\ abortQCs = state.abortQCs
    /\ abortReason = state.abortReason
    /\ abortRequests = state.abortRequests
    /\ abortVotes = state.abortVotes
    /\ aggregateCandidates = state.aggregateCandidates
    /\ aggregateRootQCs = state.aggregateRootQCs
    /\ aggregateVotes = state.aggregateVotes
    /\ aggregationPlanCertificates = state.aggregationPlanCertificates
    /\ alive = state.alive
    /\ apcVotes = state.apcVotes
    /\ applyCandidates = state.applyCandidates
    /\ applyQCs = state.applyQCs
    /\ applyVotes = state.applyVotes
    /\ availabilityAttestations = state.availabilityAttestations
    /\ availabilityCertificates = state.availabilityCertificates
    /\ availabilityShortfalls = state.availabilityShortfalls
    /\ availableArtifacts = state.availableArtifacts
    /\ availableTickets = state.availableTickets
    /\ byzantine = state.byzantine
    /\ certificateRejections = state.certificateRejections
    /\ certificateReplayReceipts = state.certificateReplayReceipts
    /\ closedInputBodies = state.closedInputBodies
    /\ commitments = state.commitments
    /\ corruptArtifacts = state.corruptArtifacts
    /\ crashCoverage = state.crashCoverage
    /\ currentAdvanceReceipts = state.currentAdvanceReceipts
    /\ currentCheckpoint = state.currentCheckpoint
    /\ currentReplayReceipts = state.currentReplayReceipts
    /\ durableSequence = state.durableSequence
    /\ durableVotes = state.durableVotes
    /\ ecVotes = state.ecVotes
    /\ eligibilityCertificates = state.eligibilityCertificates
    /\ finalizedCertificates = state.finalizedCertificates
    /\ inputSetCertificates = state.inputSetCertificates
    /\ iscVotes = state.iscVotes
    /\ lateAvailabilityEvidence = state.lateAvailabilityEvidence
    /\ leaseActive = state.leaseActive
    /\ leaseEpoch = state.leaseEpoch
    /\ leaseOwner = state.leaseOwner
    /\ logicalTime = state.logicalTime
    /\ materializedArtifacts = state.materializedArtifacts
    /\ messageMultiplicity = state.messageMultiplicity
    /\ messages = state.messages
    /\ parameterQCs = state.parameterQCs
    /\ parameterResults = state.parameterResults
    /\ parameterVotes = state.parameterVotes
    /\ partition = state.partition
    /\ pendingPointerRecoveries = state.pendingPointerRecoveries
    /\ phase = state.phase
    /\ proposals = state.proposals
    /\ publishedObjects = state.publishedObjects
    /\ receivedVotes = state.receivedVotes
    /\ recoveryState = state.recoveryState
    /\ reduceApplyRejections = state.reduceApplyRejections
    /\ rejectedCommitments = state.rejectedCommitments
    /\ rejectedPublications = state.rejectedPublications
    /\ repairAttempts = state.repairAttempts
    /\ seedTranscripts = state.seedTranscripts
    /\ ticketPlan = state.ticketPlan
    /\ timeoutObservations = state.timeoutObservations
    /\ timeoutVotes = state.timeoutVotes
    /\ view = state.view
    /\ viewChangeQCs = state.viewChangeQCs
    /\ volatileVotes = state.volatileVotes

=============================================================================
