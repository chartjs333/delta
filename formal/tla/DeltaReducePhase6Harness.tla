---------------------- MODULE DeltaReducePhase6Harness ----------------------
EXTENDS DeltaReduceFailures

HarnessRound ==
    [height |-> CHOOSE height \in Heights : TRUE,
     epoch |-> CHOOSE epoch \in ValidatorEpochs : TRUE]

HarnessConfig == CHOOSE config \in ConfigBodies : TRUE
HarnessWorker == CHOOSE worker \in Workers : TRUE
HarnessDomain == CHOOSE domain \in Domains : TRUE
HarnessData == CHOOSE data \in DataRanges : TRUE
HarnessBatch == CHOOSE budget \in BatchBudgets : TRUE
HarnessSteps == CHOOSE steps \in StepBudgets : TRUE
HarnessContent == CHOOSE content \in ContentIds : TRUE
HarnessNormEvidence == CHOOSE evidence \in ValidNormEvidence : TRUE

HarnessConfigContext ==
    ConfigContext(HarnessRound.height, HarnessRound.epoch)

HarnessConfigVotes ==
    {VoteRecord(validator, HarnessConfigContext, HarnessConfig) :
        validator \in Validators}

HarnessConfigCertificate ==
    CertificateRecord(HarnessConfigContext, HarnessConfig, Validators)

HarnessTicketPlan ==
    {[ticket |-> ticket,
      domain |-> HarnessDomain,
      data |-> HarnessData,
      batchBudget |-> HarnessBatch,
      stepBudget |-> HarnessSteps,
      parent |-> ConfiguredParentCheckpoint,
      schema |-> ConfiguredParameterSchema,
      profile |-> ConfiguredArithmeticProfile] :
        ticket \in RequiredTickets}

HarnessCommitments ==
    {[ticket |-> ticket,
      worker |-> HarnessWorker,
      leaseEpoch |-> 0,
      content |-> HarnessContent] :
        ticket \in RequiredTickets}

HarnessArtifactLocations ==
    {[storage |-> storage,
      content |-> HarnessContent,
      shard |-> shard] :
        storage \in StoragePeers, shard \in Shards}

HarnessAvailabilityAttestations ==
    {[storage |-> storage,
      ticket |-> ticket,
      content |-> HarnessContent,
      shard |-> shard] :
        storage \in StoragePeers,
        ticket \in RequiredTickets,
        shard \in Shards}

HarnessAvailabilityCertificates ==
    {[ticket |-> ticket, content |-> HarnessContent] :
        ticket \in RequiredTickets}

HarnessInputBody ==
    InputBody(
        HarnessRound, HarnessConfig, HarnessAvailabilityCertificates)

HarnessSeed == SeedRecord(HarnessInputBody, ExpectedSeedValue)

HarnessEC ==
    EligibilityBody(
        HarnessInputBody, HarnessSeed, RequiredTickets,
        HarnessNormEvidence)

HarnessAPC ==
    AggregationPlanBody(
        HarnessInputBody, HarnessSeed, HarnessEC, RequiredTickets,
        ConfiguredCoefficientProfile)

Phase6Init ==
    /\ ModelConstantsOK
    /\ FailureInit
    /\ proposals =
        {[context |-> HarnessConfigContext, body |-> HarnessConfig]}
    /\ byzantine = InitialByzantine
    /\ durableVotes = HarnessConfigVotes
    /\ volatileVotes = HarnessConfigVotes
    /\ messages = {}
    /\ messageMultiplicity = [vote \in VoteRecords |-> 0]
    /\ receivedVotes = HarnessConfigVotes
    /\ finalizedCertificates = {HarnessConfigCertificate}
    /\ durableSequence = [validator \in Validators |-> 1]
    /\ alive = Validators
    /\ recoveryState = [validator \in Validators |-> "READY"]
    /\ crashCoverage = {}
    /\ ticketPlan = HarnessTicketPlan
    /\ leaseOwner = [ticket \in Tickets |-> HarnessWorker]
    /\ leaseEpoch = [ticket \in Tickets |-> 0]
    /\ leaseActive = {}
    /\ commitments = HarnessCommitments
    /\ rejectedCommitments = {}
    /\ materializedArtifacts = HarnessArtifactLocations
    /\ availableArtifacts = HarnessArtifactLocations
    /\ corruptArtifacts = {}
    /\ availabilityAttestations = HarnessAvailabilityAttestations
    /\ availabilityCertificates = HarnessAvailabilityCertificates
    /\ availableTickets = RequiredTickets
    /\ availabilityShortfalls = {}
    /\ lateAvailabilityEvidence = {}
    /\ repairAttempts = [content \in ContentIds |-> 0]
    /\ closedInputBodies = {HarnessInputBody}
    /\ iscVotes =
        {[validator |-> validator, body |-> HarnessInputBody] :
            validator \in Validators}
    /\ inputSetCertificates =
        {[body |-> HarnessInputBody, signers |-> Validators]}
    /\ seedTranscripts = {HarnessSeed}
    /\ ecVotes =
        {[validator |-> validator, body |-> HarnessEC] :
            validator \in Validators}
    /\ eligibilityCertificates =
        {[body |-> HarnessEC, signers |-> Validators]}
    /\ apcVotes =
        {[validator |-> validator, body |-> HarnessAPC] :
            validator \in Validators}
    /\ aggregationPlanCertificates =
        {[body |-> HarnessAPC, signers |-> Validators]}
    /\ certificateRejections = {}
    /\ certificateReplayReceipts = {}
    /\ abortRequests = {}
    /\ ReduceApplyInit

Phase6Next == ReduceApplyNext

Spec == Phase6Init /\ [][Phase6Next]_ProtocolVariables

TypeOK ==
    /\ QuorumTypeOK
    /\ FailureTypeOK
    /\ TicketTypeOK
    /\ AvailabilityTypeOK
    /\ CertificateTypeOK
    /\ ReduceApplyTypeOK

Phase6Spec == Spec

Phase6TypeOK == TypeOK

=============================================================================
