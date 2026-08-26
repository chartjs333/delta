------------------------- MODULE DeltaReduceTypes -------------------------
EXTENDS Integers, FiniteSets, TLC

CONSTANTS
    Validators,
    InitialByzantine,
    Heights,
    ValidatorEpochs,
    ConfigBodies,
    Workers,
    Tickets,
    Domains,
    DataRanges,
    BatchBudgets,
    StepBudgets,
    ParentCheckpoints,
    ParameterSchemas,
    ArithmeticProfiles,
    StoragePeers,
    Shards,
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
    ExpectedParameterValue,
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
    ExpectedNextModelHash,
    ExpectedNextOptimizerHash,
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

VARIABLES
    proposals,
    byzantine,
    durableVotes,
    volatileVotes,
    messages,
    messageMultiplicity,
    receivedVotes,
    finalizedCertificates,
    durableSequence,
    alive,
    recoveryState,
    crashCoverage,
    ticketPlan,
    leaseOwner,
    leaseEpoch,
    leaseActive,
    commitments,
    rejectedCommitments,
    materializedArtifacts,
    availableArtifacts,
    corruptArtifacts,
    availabilityAttestations,
    availabilityCertificates,
    availableTickets,
    availabilityShortfalls,
    lateAvailabilityEvidence,
    repairAttempts,
    closedInputBodies,
    iscVotes,
    inputSetCertificates,
    seedTranscripts,
    ecVotes,
    eligibilityCertificates,
    apcVotes,
    aggregationPlanCertificates,
    certificateRejections,
    certificateReplayReceipts,
    abortRequests,
    parameterResults,
    parameterVotes,
    parameterQCs,
    aggregateCandidates,
    aggregateVotes,
    aggregateRootQCs,
    applyCandidates,
    applyVotes,
    applyQCs,
    currentCheckpoint,
    currentAdvanceReceipts,
    currentReplayReceipts,
    pendingPointerRecoveries,
    publishedObjects,
    rejectedPublications,
    reduceApplyRejections,
    partition,
    view,
    logicalTime,
    timeoutObservations,
    timeoutVotes,
    viewChangeQCs,
    abortVotes,
    abortQCs,
    phase,
    abortReason

QuorumVariables ==
    <<proposals, byzantine, durableVotes, volatileVotes, messages,
      messageMultiplicity,
      receivedVotes, finalizedCertificates, durableSequence, alive,
      recoveryState>>

TicketVariables ==
    <<ticketPlan, leaseOwner, leaseEpoch, leaseActive, commitments,
      rejectedCommitments>>

AvailabilityVariables ==
    <<materializedArtifacts, availableArtifacts, corruptArtifacts,
      availabilityAttestations, availabilityCertificates, availableTickets,
      availabilityShortfalls, lateAvailabilityEvidence, repairAttempts>>

CertificateVariables ==
    <<closedInputBodies, iscVotes, inputSetCertificates, seedTranscripts,
      ecVotes, eligibilityCertificates, apcVotes,
      aggregationPlanCertificates, certificateRejections,
      certificateReplayReceipts, abortRequests>>

ReduceApplyVariables ==
    <<parameterResults, parameterVotes, parameterQCs,
      aggregateCandidates, aggregateVotes, aggregateRootQCs,
      applyCandidates, applyVotes, applyQCs, currentCheckpoint,
      currentAdvanceReceipts, currentReplayReceipts,
      pendingPointerRecoveries, publishedObjects,
      rejectedPublications, reduceApplyRejections>>

FailureControlVariables ==
    <<partition, view, logicalTime, timeoutObservations, timeoutVotes,
      viewChangeQCs, abortVotes, abortQCs, phase, abortReason>>

ProtocolVariables ==
    <<proposals, byzantine, durableVotes, volatileVotes, messages,
      messageMultiplicity,
      receivedVotes, finalizedCertificates, durableSequence, alive,
      recoveryState, crashCoverage, ticketPlan, leaseOwner, leaseEpoch,
      leaseActive, commitments, rejectedCommitments, availableArtifacts,
      materializedArtifacts, corruptArtifacts, availabilityAttestations,
      availabilityCertificates, availableTickets, availabilityShortfalls,
      lateAvailabilityEvidence, repairAttempts, closedInputBodies, iscVotes,
      inputSetCertificates, seedTranscripts, ecVotes,
      eligibilityCertificates, apcVotes, aggregationPlanCertificates,
      certificateRejections, certificateReplayReceipts, abortRequests,
      parameterResults, parameterVotes, parameterQCs,
      aggregateCandidates, aggregateVotes, aggregateRootQCs,
      applyCandidates, applyVotes, applyQCs, currentCheckpoint,
      currentAdvanceReceipts, currentReplayReceipts,
      pendingPointerRecoveries, publishedObjects,
      rejectedPublications, reduceApplyRejections, partition, view,
      logicalTime, timeoutObservations, timeoutVotes, viewChangeQCs,
      abortVotes, abortQCs, phase, abortReason>>

InputClosed == closedInputBodies # {}

CertificateProgressOpen == ~InputClosed /\ abortRequests = {}

\* Every signature that can contribute to a QC uses the same durable
\* persist -> send -> deliver lifecycle.  The domain-specific vote sets below
\* are durable projections; only delivered envelopes count as QC signers.
VoteKinds ==
    {"ROUND_CONFIG", "ISC", "EC", "APC", "PARAMETER",
     "AGGREGATE_ROOT", "APPLY", "VIEW_CHANGE", "ABORT"}
RecoveryStates == {"READY", "CRASHED", "RECOVERING"}
CrashPoints == {"BEFORE_PERSIST", "AFTER_PERSIST", "AFTER_SEND"}

VoteContexts ==
    [kind : {"ROUND_CONFIG"}, height : Heights, epoch : ValidatorEpochs]

ProposalRecords ==
    [context : VoteContexts, body : ConfigBodies]

ConfigVoteRecords ==
    [validator : Validators, kind : {"ROUND_CONFIG"},
     context : VoteContexts, body : ConfigBodies]

CertificateRecords ==
    [context : VoteContexts, body : ConfigBodies, signers : SUBSET Validators]

TicketDefinitions ==
    [ticket : Tickets,
     domain : Domains,
     data : DataRanges,
     batchBudget : BatchBudgets,
     stepBudget : StepBudgets,
     parent : ParentCheckpoints,
     schema : ParameterSchemas,
     profile : ArithmeticProfiles]

CommitmentRecords ==
    [ticket : Tickets,
     worker : Workers,
     leaseEpoch : 0..MaxLeaseEpoch,
     content : ContentIds]

CommitmentRejectReasons ==
    {"STALE_LEASE", "COMMIT_EQUIVOCATION", "LATE_AFTER_CLOSE"}

RejectedCommitmentRecords ==
    [ticket : Tickets,
     worker : Workers,
     leaseEpoch : 0..MaxLeaseEpoch,
     content : ContentIds,
     reason : CommitmentRejectReasons]

ArtifactLocations ==
    [storage : StoragePeers, content : ContentIds, shard : Shards]

AvailabilityAttestationRecords ==
    [storage : StoragePeers,
     ticket : Tickets,
     content : ContentIds,
     shard : Shards]

AvailabilityCertificateRecords ==
    [ticket : Tickets, content : ContentIds]

ClosePolicies == {"OMIT_UNAVAILABLE", "ABORT_ON_INCOMPLETE"}
CertificateKinds == {"ISC", "SEED", "EC", "APC"}
CertificateRejectionReasons ==
    {"EARLY_SEED", "WRONG_PARENT", "CONFLICTING_CERTIFICATE",
     "NON_SUBSET_MEMBERSHIP", "INVALID_NORM_EVIDENCE",
     "MEMBERSHIP_REWRITE", "WRONG_COEFFICIENT_PROFILE"}
AbortRequestReasons == {"INCOMPLETE_INPUT", "UNSAFE_COEFFICIENTS"}

RoundContexts == [height : Heights, epoch : ValidatorEpochs]

InputSetBodies ==
    [round : RoundContexts,
     config : ConfigBodies,
     policy : ClosePolicies,
     entries : SUBSET AvailabilityCertificateRecords,
     canonicalRoot : SUBSET AvailabilityCertificateRecords]

ISCVoteRecords == [validator : Validators, body : InputSetBodies]

InputSetCertificateRecords ==
    [body : InputSetBodies, signers : SUBSET Validators]

SeedTranscriptRecords ==
    [isc : InputSetBodies, epoch : ValidatorEpochs, value : SeedValues]

EligibilityBodies ==
    [isc : InputSetBodies,
     seed : SeedTranscriptRecords,
     members : SUBSET Tickets,
     normEvidence : NormEvidenceValues]

ECVoteRecords == [validator : Validators, body : EligibilityBodies]

EligibilityCertificateRecords ==
    [body : EligibilityBodies, signers : SUBSET Validators]

AggregationPlanBodies ==
    [isc : InputSetBodies,
     seed : SeedTranscriptRecords,
     ec : EligibilityBodies,
     members : SUBSET Tickets,
     coefficientProfile : CoefficientProfiles]

APCVoteRecords == [validator : Validators, body : AggregationPlanBodies]

AggregationPlanCertificateRecords ==
    [body : AggregationPlanBodies, signers : SUBSET Validators]

CertificateRejectionRecords ==
    [kind : CertificateKinds,
     round : RoundContexts,
     reason : CertificateRejectionReasons]

CertificateReplayRecords ==
    [kind : CertificateKinds, round : RoundContexts]

AbortRequestRecords ==
    [round : RoundContexts, reason : AbortRequestReasons]

ParameterKeys == [domain : Domains, shard : Shards]

ReduceApplyKinds ==
    {"PARAMETER", "AGGREGATE_ROOT", "APPLY", "CURRENT"}

ReduceApplyRejectionReasons ==
    {"WRONG_PARENT", "UNCHECKED_ARITHMETIC", "ARITHMETIC_OVERFLOW",
     "CONFLICTING_CERTIFICATE", "INCOMPLETE_COVERAGE",
     "DUPLICATE_COVERAGE", "MIXED_PARENT", "UNSAFE_APPLY_PROFILE",
     "CURRENT_CONFLICT"}

ReduceApplyRejectionRecords ==
    [kind : ReduceApplyKinds,
     round : RoundContexts,
     reason : ReduceApplyRejectionReasons]

SafePublicationKinds ==
    {"AGGREGATE_ROOT_QC", "APPLY_QC", "CURRENT_CHECKPOINT"}

ForbiddenPublicationKinds ==
    {"WORKER_COMMITMENT", "AVAILABILITY_FRAGMENT",
     "PARAMETER_PARTIAL"}

PublicationKinds == SafePublicationKinds \cup ForbiddenPublicationKinds

PhaseValues == {"ACTIVE", "ABORTING", "APPLIED", "ABORTED"}
AbortReasons ==
    {"NO_ABORT", "HARD_DEADLINE", "INCOMPLETE_INPUT",
     "UNSAFE_COEFFICIENTS", "IRRECOVERABLE_AVAILABILITY",
     "PARAMETER_FAILURE", "APPLY_FAILURE"}

TimeoutObservationRecords ==
    [round : RoundContexts, view : Views]

ViewChangeBodies ==
    [round : RoundContexts,
     fromView : Views,
     toView : Views,
     softDeadline : 0..MaxLogicalTime]

QuorumSize == (2 * F) + 1

ModelConstantsOK ==
    /\ Validators # {}
    /\ Heights # {}
    /\ ValidatorEpochs # {}
    /\ ConfigBodies # {}
    /\ Workers # {}
    /\ Tickets # {}
    /\ Domains # {}
    /\ DataRanges # {}
    /\ BatchBudgets \subseteq Nat \ {0}
    /\ BatchBudgets # {}
    /\ StepBudgets \subseteq Nat \ {0}
    /\ StepBudgets # {}
    /\ ParentCheckpoints # {}
    /\ ParameterSchemas # {}
    /\ ArithmeticProfiles # {}
    /\ StoragePeers # {}
    /\ Shards # {}
    /\ ContentIds # {}
    /\ CompletedTickets \subseteq Tickets
    /\ RequiredTickets \subseteq Tickets
    /\ RequiredTickets # {}
    /\ ConfiguredClosePolicy \in ClosePolicies
    /\ SeedValues # {}
    /\ ExpectedSeedValue \in SeedValues
    /\ NormEvidenceValues # {}
    /\ ValidNormEvidence \subseteq NormEvidenceValues
    /\ ValidNormEvidence # {}
    /\ CoefficientProfiles # {}
    /\ ConfiguredCoefficientProfile \in CoefficientProfiles
    /\ SafeCoefficientProfiles \subseteq CoefficientProfiles
    /\ ParameterValues # {}
    /\ ParameterValues \subseteq Int
    /\ AccumulatorBound \in Nat
    /\ ExpectedParameterValue \in ParameterValues
    /\ -AccumulatorBound <= ExpectedParameterValue
    /\ ExpectedParameterValue <= AccumulatorBound
    /\ ConfiguredParameterSchema \in ParameterSchemas
    /\ ConfiguredArithmeticProfile \in ArithmeticProfiles
    /\ ConfiguredParentCheckpoint \in ParentCheckpoints
    /\ ApplyProfiles # {}
    /\ ConfiguredApplyProfile \in ApplyProfiles
    /\ SafeApplyProfiles \subseteq ApplyProfiles
    /\ CheckpointIds # {}
    /\ ParentCheckpoints \subseteq CheckpointIds
    /\ InitialCurrentCheckpoint \in CheckpointIds
    /\ ConfiguredParentCheckpoint = InitialCurrentCheckpoint
    /\ ExpectedNextCheckpoint \in CheckpointIds
    /\ ExpectedNextCheckpoint # InitialCurrentCheckpoint
    /\ ModelHashes # {}
    /\ OptimizerHashes # {}
    /\ ExpectedNextModelHash \in ModelHashes
    /\ ExpectedNextOptimizerHash \in OptimizerHashes
    /\ Views \subseteq Nat
    /\ 0 \in Views
    /\ MaxLogicalTime \in Nat \ {0}
    /\ SoftDeadline \in 0..MaxLogicalTime
    /\ HardDeadline \in 0..MaxLogicalTime
    /\ SoftDeadline < HardDeadline
    /\ MaxMessageCopies \in Nat \ {0}
    /\ ConfiguredAbortReason \in AbortReasons \ {"NO_ABORT"}
    /\ F \in Nat
    /\ MaxDurableSequence \in Nat \ {0}
    /\ MaxLeaseEpoch \in Nat \ {0}
    /\ MaxModeledRejections \in Nat \ {0}
    /\ MaxModeledCertificateRejections \in Nat \ {0}
    /\ MaxModeledReduceApplyRejections \in Nat \ {0}
    /\ AvailabilityThreshold \in 1..Cardinality(StoragePeers)
    /\ MaxRepairAttempts \in Nat \ {0}
    /\ InitialByzantine \subseteq Validators
    /\ Cardinality(Validators) = (3 * F) + 1
    /\ Cardinality(InitialByzantine) <= F
    /\ EnableQuorumActions \in BOOLEAN
    /\ EnableFailures \in BOOLEAN
    /\ EnableMessageDrop \in BOOLEAN
    /\ EnableTicketActions \in BOOLEAN
    /\ EnableAvailabilityActions \in BOOLEAN
    /\ EnableAvailabilityFaults \in BOOLEAN
    /\ EnableCertificateActions \in BOOLEAN
    /\ EnablePlanningActions \in BOOLEAN
    /\ EnableCertificateFaults \in BOOLEAN
    /\ EnableFrankensteinFaults \in BOOLEAN
    /\ EnableReduceApplyActions \in BOOLEAN
    /\ EnableAggregateActions \in BOOLEAN
    /\ EnableApplyActions \in BOOLEAN
    /\ EnablePublicationActions \in BOOLEAN
    /\ EnableReduceApplyFaults \in BOOLEAN
    /\ EnableNetworkFaults \in BOOLEAN
    /\ EnablePartitionActions \in BOOLEAN
    /\ EnableTimeoutActions \in BOOLEAN

ConfigContext(height, epoch) ==
    [kind |-> "ROUND_CONFIG", height |-> height, epoch |-> epoch]

VoteEnvelope(validator, kind, context, body) ==
    [validator |-> validator, kind |-> kind,
     context |-> context, body |-> body]

VoteRecord(validator, context, body) ==
    VoteEnvelope(validator, "ROUND_CONFIG", context, body)

CertificateRecord(context, body, signers) ==
    [context |-> context, body |-> body, signers |-> signers]

ValidatorSymmetry ==
    Permutations(Validators \ InitialByzantine)

ValidatorAndBodySymmetry ==
    ValidatorSymmetry \cup Permutations(ConfigBodies)

=============================================================================
