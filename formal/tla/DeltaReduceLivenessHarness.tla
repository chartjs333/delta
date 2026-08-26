---------------------- MODULE DeltaReduceLivenessHarness ------------------
EXTENDS DeltaReduce

\* Positive liveness is checked from the real empty protocol Init.  Each
\* phase relation contains only success-path production actions; it never
\* contains timeout/abort actions.  Consequently APPLIED cannot be satisfied
\* by HardAbort and every QC still traverses the shared durable transport.

LivenessRound ==
    [height |-> CHOOSE height \in Heights : TRUE,
     epoch |-> CHOOSE epoch \in ValidatorEpochs : TRUE]
LivenessConfig == CHOOSE config \in ConfigBodies : TRUE
LivenessWorker == CHOOSE worker \in Workers : TRUE
LivenessDomain == CHOOSE domain \in Domains : TRUE
LivenessData == CHOOSE data \in DataRanges : TRUE
LivenessBatch == CHOOSE budget \in BatchBudgets : TRUE
LivenessSteps == CHOOSE steps \in StepBudgets : TRUE
LivenessContent == CHOOSE content \in ContentIds : TRUE
LivenessEvidence == CHOOSE evidence \in ValidNormEvidence : TRUE

LivenessConfigContext ==
    ConfigContext(LivenessRound.height, LivenessRound.epoch)

LivenessTicketDefinition(ticket) ==
    [ticket |-> ticket,
     domain |-> LivenessDomain,
     data |-> LivenessData,
     batchBudget |-> LivenessBatch,
     stepBudget |-> LivenessSteps,
     parent |-> ConfiguredParentCheckpoint,
     schema |-> ConfiguredParameterSchema,
     profile |-> ConfiguredArithmeticProfile]

PositiveProposeConfig ==
    ProposeRoundConfig(LivenessConfigContext, LivenessConfig)

PositivePersistConfigVote ==
    \E validator \in Validators :
        PersistConfigVote(
            validator, LivenessConfigContext, LivenessConfig)

PositiveFinalizeConfig ==
    FinalizeRoundConfig(LivenessConfigContext, LivenessConfig)

PositiveIssueTicket ==
    \E ticket \in RequiredTickets :
        IssueTicket(LivenessTicketDefinition(ticket))

PositiveLeaseTicket ==
    \E ticket \in RequiredTickets :
        LeaseTicket(ticket, LivenessWorker)

PositiveCommitTicket ==
    \E ticket \in RequiredTickets :
        CommitTicket(ticket, LivenessWorker, 0, LivenessContent)

PositiveUploadArtifact ==
    \E storage \in StoragePeers, ticket \in RequiredTickets,
       shard \in Shards :
        UploadArtifact(
            storage, ticket, LivenessContent, shard)

PositiveAttestAvailability ==
    \E storage \in StoragePeers, ticket \in RequiredTickets,
       shard \in Shards :
        AttestAvailability(
            storage, ticket, LivenessContent, shard)

PositiveFinalizeAvailability ==
    \E ticket \in RequiredTickets :
        FinalizeAvailability(ticket, LivenessContent)

PositiveCloseInput ==
    /\ RequiredInputComplete
    /\ CloseInput(LivenessRound, LivenessConfig)

PositiveVoteISC ==
    \E validator \in Validators, body \in closedInputBodies :
        VoteISC(validator, body)

PositiveFinalizeISC ==
    \E body \in closedInputBodies : FinalizeISC(body)

PositiveGenerateSeed ==
    \E isc \in FinalizedISCBodies : GenerateSeed(isc)

PositiveVoteEC ==
    \E validator \in Validators, isc \in FinalizedISCBodies,
       seed \in seedTranscripts :
        VoteEC(validator,
            EligibilityBody(
                isc, seed, RequiredTickets, LivenessEvidence))

PositiveFinalizeEC ==
    \E body \in {vote.body : vote \in ecVotes} : FinalizeEC(body)

PositiveVoteAPC ==
    \E validator \in Validators, ec \in FinalizedECBodies :
        VoteAPC(validator,
            AggregationPlanBody(
                ec.isc, ec.seed, ec, RequiredTickets,
                ConfiguredCoefficientProfile))

PositiveFinalizeAPC ==
    \E body \in {vote.body : vote \in apcVotes} : FinalizeAPC(body)

PositiveProposeParameter ==
    \E apc \in FinalizedAPCBodies, domain \in Domains,
       shard \in Shards :
        ProposeParameterResult(
            ParameterResultBody(
                apc, domain, shard, ConfiguredParentCheckpoint,
                ConfiguredParameterSchema, ConfiguredArithmeticProfile,
                ExpectedParameterValue, TRUE))

PositiveVoteParameter ==
    \E validator \in Validators, body \in parameterResults :
        VoteParameter(validator, body)

PositiveFinalizeParameter ==
    \E body \in parameterResults : FinalizeParameterQC(body)

PositiveAssembleAggregate ==
    \E apc \in FinalizedAPCBodies :
        AssembleAggregateRoot(
            AggregateRootBody(
                apc, FinalizedParameterBodiesForAPC(apc)))

PositiveVoteAggregate ==
    \E validator \in Validators, body \in aggregateCandidates :
        VoteAggregateRoot(validator, body)

PositiveFinalizeAggregate ==
    \E body \in aggregateCandidates : FinalizeAggregateRootQC(body)

PositiveComputeApply ==
    \E root \in FinalizedAggregateBodies :
        ComputeApplyCandidate(
            ApplyBody(
                root, root.parent, ConfiguredApplyProfile,
                ExpectedNextCheckpoint, ExpectedNextModelHash,
                ExpectedNextOptimizerHash, TRUE))

PositiveVoteApply ==
    \E validator \in Validators, body \in applyCandidates :
        VoteApply(validator, body)

PositiveFinalizeApply ==
    \E body \in applyCandidates : FinalizeApplyQC(body)

PositiveAdvanceCurrent ==
    \E body \in FinalizedApplyBodies : AdvanceCurrentCheckpoint(body)

\* The view-change witness may advance only as far as the soft deadline.
\* This removes the competing hard-deadline transition, so weak fairness
\* cannot satisfy the specification by bypassing an enabled view change.
PositiveAdvanceToSoftDeadline ==
    /\ logicalTime < SoftDeadline
    /\ AdvanceLogicalTime

PositiveAdvanceToHardDeadline == AdvanceLogicalTime

PositiveSoftTimeout == SoftTimeout(LivenessRound)

PositiveVoteViewChange ==
    \E validator \in Validators :
        VoteViewChange(
            validator, ViewChangeBody(LivenessRound, view, view + 1))

PositiveFinalizeViewChange ==
    \E body \in {vote.body : vote \in timeoutVotes} :
        FinalizeViewChange(body)

PositiveVoteHardAbort ==
    \E validator \in Validators :
        VoteHardAbort(validator, AbortBody(LivenessRound))

PositiveFinalizeHardAbort ==
    \E body \in {vote.body : vote \in abortVotes} : HardAbort(body)

ConfigLivenessNext ==
    \/ PositiveProposeConfig
    \/ PositivePersistConfigVote
    \/ VoteTransportNext
    \/ PositiveFinalizeConfig

ISCLivenessNext ==
    \/ ConfigLivenessNext
    \/ PositiveIssueTicket
    \/ PositiveLeaseTicket
    \/ PositiveCommitTicket
    \/ PositiveUploadArtifact
    \/ PositiveAttestAvailability
    \/ PositiveFinalizeAvailability
    \/ PositiveCloseInput
    \/ PositiveVoteISC
    \/ PositiveFinalizeISC

PlanLivenessNext ==
    \/ ISCLivenessNext
    \/ PositiveGenerateSeed
    \/ PositiveVoteEC
    \/ PositiveFinalizeEC
    \/ PositiveVoteAPC
    \/ PositiveFinalizeAPC

AppliedLivenessNext ==
    \/ PlanLivenessNext
    \/ PositiveProposeParameter
    \/ PositiveVoteParameter
    \/ PositiveFinalizeParameter
    \/ PositiveAssembleAggregate
    \/ PositiveVoteAggregate
    \/ PositiveFinalizeAggregate
    \/ PositiveComputeApply
    \/ PositiveVoteApply
    \/ PositiveFinalizeApply
    \/ PositiveAdvanceCurrent

ViewLivenessNext ==
    \/ PositiveAdvanceToSoftDeadline
    \/ PositiveSoftTimeout
    \/ PositiveVoteViewChange
    \/ VoteTransportNext
    \/ PositiveFinalizeViewChange

AbortLivenessNext ==
    \/ PositiveAdvanceToHardDeadline
    \/ PositiveVoteHardAbort
    \/ VoteTransportNext
    \/ PositiveFinalizeHardAbort

ConfigLivenessSpec ==
    /\ Init
    /\ [][ConfigLivenessNext]_ProtocolVariables
    /\ WF_ProtocolVariables(ConfigLivenessNext)

ISCLivenessSpec ==
    /\ Init
    /\ [][ISCLivenessNext]_ProtocolVariables
    /\ WF_ProtocolVariables(ISCLivenessNext)

PlanLivenessSpec ==
    /\ Init
    /\ [][PlanLivenessNext]_ProtocolVariables
    /\ WF_ProtocolVariables(PlanLivenessNext)

AppliedLivenessSpec ==
    /\ Init
    /\ [][AppliedLivenessNext]_ProtocolVariables
    /\ WF_ProtocolVariables(AppliedLivenessNext)

ViewLivenessSpec ==
    /\ Init
    /\ [][ViewLivenessNext]_ProtocolVariables
    /\ WF_ProtocolVariables(ViewLivenessNext)

AbortLivenessSpec ==
    /\ Init
    /\ [][AbortLivenessNext]_ProtocolVariables
    /\ WF_ProtocolVariables(AbortLivenessNext)

\* Compatibility alias used by the gate runner.  It now denotes the complete
\* proposal-to-APPLIED path, never a prefilled Phase6 or aborting path.
LivenessSpec == AppliedLivenessSpec

NoFairnessSpec ==
    /\ Init
    /\ [][AppliedLivenessNext]_ProtocolVariables

LivenessTypeOK == TypeOK

ConfigQCReached == <> (finalizedCertificates # {})
ISCReached == <> (inputSetCertificates # {})
PlanQCReached == <> (aggregationPlanCertificates # {})
AppliedReached == <> (phase = "APPLIED")
ViewQCReached == <> (viewChangeQCs # {})
AbortQCReached == <> (phase = "ABORTED" /\ abortQCs # {})

\* Conditional failure-outcome properties remain registered separately from
\* the positive milestones.  Passing any of these through ABORTED is never
\* reported as evidence for AppliedReached.
ConfigEventuallyFinalizesOrAborts ==
    <> (finalizedCertificates # {} \/ phase = "ABORTED")

CommittedEventuallyAvailableOrRejectedBeforeISC ==
    [](commitments # {}
        => <> (availableTickets # {}
            \/ rejectedCommitments # {}
            \/ phase = "ABORTED"))

FrozenRoundEventuallyGetsPlanOrAborts ==
    [](inputSetCertificates # {}
        => <> (aggregationPlanCertificates # {} \/ phase = "ABORTED"))

PlannedShardEventuallyGetsQCOrRoundAborts ==
    [](aggregationPlanCertificates # {}
        => <> (parameterQCs # {} \/ phase = "ABORTED"))

AggregateEventuallyAppliesOrAborts ==
    [](aggregationPlanCertificates # {}
        => <> (phase \in {"APPLIED", "ABORTED"}))

ExistingApplyQCEventuallyRepairsCurrentPointer ==
    [](applyQCs # {}
        => <> (currentCheckpoint = ExpectedNextCheckpoint))

SoftTimeoutEventuallyChangesView ==
    [](timeoutObservations # {}
        => <> (view # 0 \/ phase \in {"APPLIED", "ABORTED"}))

HardDeadlineEventuallyTerminatesNonfinalizedRound ==
    [](logicalTime >= HardDeadline
        => <> (phase \in {"APPLIED", "ABORTED"}))

\* Abort is unreachable in every positive transition relation; APPLIED is the
\* only accepted terminal milestone in the complete positive model.
NeverUsesAbortAsProgress == [] (phase # "ABORTED")

=============================================================================
