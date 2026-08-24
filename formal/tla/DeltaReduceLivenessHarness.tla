---------------------- MODULE DeltaReduceLivenessHarness ------------------
EXTENDS DeltaReduceFailures

Phase6 == INSTANCE DeltaReducePhase6Harness

LivenessProgressOpen ==
    /\ phase = "ACTIVE"
    /\ logicalTime < HardDeadline
    /\ abortRequests = {}

LivenessNext ==
    \/ /\ LivenessProgressOpen
       /\ Phase6!Phase6Next
    \/ FailureNext

LivenessFairness ==
    /\ WF_ProtocolVariables(AdvanceLogicalTime)
    /\ WF_ProtocolVariables(SoftTimeoutAction)
    /\ WF_ProtocolVariables(VoteViewChangeAction)
    /\ WF_ProtocolVariables(ViewChangeAction)
    /\ WF_ProtocolVariables(VoteHardAbortAction)
    /\ WF_ProtocolVariables(HardAbortAction)
    /\ WF_ProtocolVariables(ProposeParameterResultAction)
    /\ WF_ProtocolVariables(VoteParameterAction)
    /\ WF_ProtocolVariables(FinalizeParameterQCAction)
    /\ WF_ProtocolVariables(AssembleAggregateRootAction)
    /\ WF_ProtocolVariables(VoteAggregateRootAction)
    /\ WF_ProtocolVariables(FinalizeAggregateRootQCAction)
    /\ WF_ProtocolVariables(ComputeApplyCandidateAction)
    /\ WF_ProtocolVariables(VoteApplyAction)
    /\ WF_ProtocolVariables(FinalizeApplyQCAction)
    /\ WF_ProtocolVariables(AdvanceCurrentCheckpointAction)

LivenessSpec ==
    /\ Phase6!Phase6Init
    /\ [][LivenessNext]_ProtocolVariables
    /\ LivenessFairness

\* Negative control used by T059.  The same transition relation without the
\* declared weak-fairness assumptions admits infinite stuttering.
NoFairnessSpec ==
    /\ Phase6!Phase6Init
    /\ [][LivenessNext]_ProtocolVariables

LivenessTypeOK ==
    /\ QuorumTypeOK
    /\ FailureTypeOK
    /\ TicketTypeOK
    /\ AvailabilityTypeOK
    /\ CertificateTypeOK
    /\ ReduceApplyTypeOK

Terminal == phase \in {"APPLIED", "ABORTED"}

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
        => <> Terminal)

ExistingApplyQCEventuallyRepairsCurrentPointer ==
    [](applyQCs # {}
        => <> (currentCheckpoint = ExpectedNextCheckpoint))

SoftTimeoutEventuallyChangesView ==
    [](timeoutObservations # {}
        => <> (view # 0 \/ Terminal))

HardDeadlineEventuallyTerminatesNonfinalizedRound ==
    [](logicalTime >= HardDeadline => <> Terminal)

=============================================================================
