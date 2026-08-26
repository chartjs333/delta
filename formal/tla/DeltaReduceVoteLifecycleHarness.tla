------------------ MODULE DeltaReduceVoteLifecycleHarness -----------------
EXTENDS DeltaReduceLivenessHarness

\* Fault injection is confined to one QC window per spec.  This avoids a
\* detached transport model and keeps exhaustive TLC tractable: the prefix and
\* the vote action are the production path, while every crash/drop/duplicate
\* acts on the actual envelope for TargetKind.

TargetDrop(kind) ==
    \E vote \in messages, copy \in 1..MaxMessageCopies :
        /\ vote.kind = kind
        /\ DropMessage(vote, copy)

TargetDuplicate(kind) ==
    \E vote \in messages :
        /\ vote.kind = kind
        /\ DuplicateMessage(vote)

TargetCrashBeforePersist(kind) ==
    \E validator \in Validators :
        CrashBeforePersistKind(validator, kind)

TargetCrashAfterPersist(kind) ==
    \E validator \in Validators :
        CrashAfterPersistKind(validator, kind)

TargetCrashAfterSend(kind) ==
    \E validator \in Validators :
        CrashAfterSendKind(validator, kind)

TargetFaultNext(kind) ==
    \/ TargetCrashBeforePersist(kind)
    \/ TargetCrashAfterPersist(kind)
    \/ TargetCrashAfterSend(kind)
    \/ RestartAction
    \/ RecoverJournalAction
    \/ TargetDrop(kind)
    \/ TargetDuplicate(kind)

ConfigWindow == finalizedCertificates = {}
ISCWindow == closedInputBodies # {} /\ inputSetCertificates = {}
ECWindow == seedTranscripts # {} /\ eligibilityCertificates = {}
APCWindow == eligibilityCertificates # {}
    /\ aggregationPlanCertificates = {}
ParameterWindow == aggregationPlanCertificates # {} /\ parameterQCs = {}
AggregateWindow == parameterQCs # {} /\ aggregateRootQCs = {}
ApplyWindow == aggregateRootQCs # {} /\ applyQCs = {}

SeedLivenessNext == ISCLivenessNext \/ PositiveGenerateSeed
ECLivenessNext ==
    \/ SeedLivenessNext
    \/ PositiveVoteEC
    \/ PositiveFinalizeEC
APCLivenessNext ==
    \/ ECLivenessNext
    \/ PositiveVoteAPC
    \/ PositiveFinalizeAPC
ParameterLivenessNext ==
    \/ APCLivenessNext
    \/ PositiveProposeParameter
    \/ PositiveVoteParameter
    \/ PositiveFinalizeParameter
AggregateLivenessNext ==
    \/ ParameterLivenessNext
    \/ PositiveAssembleAggregate
    \/ PositiveVoteAggregate
    \/ PositiveFinalizeAggregate
ApplyLivenessNext ==
    \/ AggregateLivenessNext
    \/ PositiveComputeApply
    \/ PositiveVoteApply
    \/ PositiveFinalizeApply

ConfigCrashBefore == ConfigWindow /\ TargetCrashBeforePersist("ROUND_CONFIG")
ConfigCrashAfterPersist == ConfigWindow /\ TargetCrashAfterPersist("ROUND_CONFIG")
ConfigCrashAfterSend == ConfigWindow /\ TargetCrashAfterSend("ROUND_CONFIG")
ConfigRestart == ConfigWindow /\ RestartAction
ConfigRecover == ConfigWindow /\ RecoverJournalAction
ConfigDrop == ConfigWindow /\ TargetDrop("ROUND_CONFIG")
ConfigDuplicate == ConfigWindow /\ TargetDuplicate("ROUND_CONFIG")

ISCCrashBefore == ISCWindow /\ TargetCrashBeforePersist("ISC")
ISCCrashAfterPersist == ISCWindow /\ TargetCrashAfterPersist("ISC")
ISCCrashAfterSend == ISCWindow /\ TargetCrashAfterSend("ISC")
ISCRestart == ISCWindow /\ RestartAction
ISCRecover == ISCWindow /\ RecoverJournalAction
ISCDrop == ISCWindow /\ TargetDrop("ISC")
ISCDuplicate == ISCWindow /\ TargetDuplicate("ISC")

ECCrashBefore == ECWindow /\ TargetCrashBeforePersist("EC")
ECCrashAfterPersist == ECWindow /\ TargetCrashAfterPersist("EC")
ECCrashAfterSend == ECWindow /\ TargetCrashAfterSend("EC")
ECRestart == ECWindow /\ RestartAction
ECRecover == ECWindow /\ RecoverJournalAction
ECDrop == ECWindow /\ TargetDrop("EC")
ECDuplicate == ECWindow /\ TargetDuplicate("EC")

APCCrashBefore == APCWindow /\ TargetCrashBeforePersist("APC")
APCCrashAfterPersist == APCWindow /\ TargetCrashAfterPersist("APC")
APCCrashAfterSend == APCWindow /\ TargetCrashAfterSend("APC")
APCRestart == APCWindow /\ RestartAction
APCRecover == APCWindow /\ RecoverJournalAction
APCDrop == APCWindow /\ TargetDrop("APC")
APCDuplicate == APCWindow /\ TargetDuplicate("APC")

ParameterCrashBefore ==
    ParameterWindow /\ TargetCrashBeforePersist("PARAMETER")
ParameterCrashAfterPersist ==
    ParameterWindow /\ TargetCrashAfterPersist("PARAMETER")
ParameterCrashAfterSend ==
    ParameterWindow /\ TargetCrashAfterSend("PARAMETER")
ParameterRestart == ParameterWindow /\ RestartAction
ParameterRecover == ParameterWindow /\ RecoverJournalAction
ParameterDrop == ParameterWindow /\ TargetDrop("PARAMETER")
ParameterDuplicate == ParameterWindow /\ TargetDuplicate("PARAMETER")

AggregateCrashBefore ==
    AggregateWindow /\ TargetCrashBeforePersist("AGGREGATE_ROOT")
AggregateCrashAfterPersist ==
    AggregateWindow /\ TargetCrashAfterPersist("AGGREGATE_ROOT")
AggregateCrashAfterSend ==
    AggregateWindow /\ TargetCrashAfterSend("AGGREGATE_ROOT")
AggregateRestart == AggregateWindow /\ RestartAction
AggregateRecover == AggregateWindow /\ RecoverJournalAction
AggregateDrop == AggregateWindow /\ TargetDrop("AGGREGATE_ROOT")
AggregateDuplicate == AggregateWindow /\ TargetDuplicate("AGGREGATE_ROOT")

ApplyCrashBefore == ApplyWindow /\ TargetCrashBeforePersist("APPLY")
ApplyCrashAfterPersist == ApplyWindow /\ TargetCrashAfterPersist("APPLY")
ApplyCrashAfterSend == ApplyWindow /\ TargetCrashAfterSend("APPLY")
ApplyRestart == ApplyWindow /\ RestartAction
ApplyRecover == ApplyWindow /\ RecoverJournalAction
ApplyDrop == ApplyWindow /\ TargetDrop("APPLY")
ApplyDuplicate == ApplyWindow /\ TargetDuplicate("APPLY")

TimeoutRound ==
    [height |-> CHOOSE height \in Heights : TRUE,
     epoch |-> CHOOSE epoch \in ValidatorEpochs : TRUE]

LifecycleSoftTimeout == SoftTimeout(TimeoutRound)
LifecycleVoteViewChange ==
    \E validator \in Validators :
        VoteViewChange(
            validator, ViewChangeBody(TimeoutRound, view, view + 1))
LifecycleFinalizeViewChange ==
    \E body \in {vote.body : vote \in timeoutVotes} :
        FinalizeViewChange(body)

ViewWindow == timeoutObservations # {} /\ viewChangeQCs = {}
ViewCrashBefore == ViewWindow /\ TargetCrashBeforePersist("VIEW_CHANGE")
ViewCrashAfterPersist == ViewWindow /\ TargetCrashAfterPersist("VIEW_CHANGE")
ViewCrashAfterSend == ViewWindow /\ TargetCrashAfterSend("VIEW_CHANGE")
ViewRestart == ViewWindow /\ RestartAction
ViewRecover == ViewWindow /\ RecoverJournalAction
ViewDrop == ViewWindow /\ TargetDrop("VIEW_CHANGE")
ViewDuplicate == ViewWindow /\ TargetDuplicate("VIEW_CHANGE")

AbortWindow == logicalTime >= HardDeadline /\ abortQCs = {}
AbortCrashBefore == AbortWindow /\ TargetCrashBeforePersist("ABORT")
AbortCrashAfterPersist == AbortWindow /\ TargetCrashAfterPersist("ABORT")
AbortCrashAfterSend == AbortWindow /\ TargetCrashAfterSend("ABORT")
AbortRestart == AbortWindow /\ RestartAction
AbortRecover == AbortWindow /\ RecoverJournalAction
AbortDrop == AbortWindow /\ TargetDrop("ABORT")
AbortDuplicate == AbortWindow /\ TargetDuplicate("ABORT")

ConfigVoteLifecycleNext ==
    \/ ConfigLivenessNext
    \/ ConfigCrashBefore
    \/ ConfigCrashAfterPersist
    \/ ConfigCrashAfterSend
    \/ ConfigRestart
    \/ ConfigRecover
    \/ ConfigDrop
    \/ ConfigDuplicate
ISCVoteLifecycleNext ==
    \/ ISCLivenessNext
    \/ ISCCrashBefore
    \/ ISCCrashAfterPersist
    \/ ISCCrashAfterSend
    \/ ISCRestart
    \/ ISCRecover
    \/ ISCDrop
    \/ ISCDuplicate
ECVoteLifecycleNext ==
    \/ ECLivenessNext
    \/ ECCrashBefore
    \/ ECCrashAfterPersist
    \/ ECCrashAfterSend
    \/ ECRestart
    \/ ECRecover
    \/ ECDrop
    \/ ECDuplicate
APCVoteLifecycleNext ==
    \/ APCLivenessNext
    \/ APCCrashBefore
    \/ APCCrashAfterPersist
    \/ APCCrashAfterSend
    \/ APCRestart
    \/ APCRecover
    \/ APCDrop
    \/ APCDuplicate
ParameterVoteLifecycleNext ==
    \/ ParameterLivenessNext
    \/ ParameterCrashBefore
    \/ ParameterCrashAfterPersist
    \/ ParameterCrashAfterSend
    \/ ParameterRestart
    \/ ParameterRecover
    \/ ParameterDrop
    \/ ParameterDuplicate
AggregateVoteLifecycleNext ==
    \/ AggregateLivenessNext
    \/ AggregateCrashBefore
    \/ AggregateCrashAfterPersist
    \/ AggregateCrashAfterSend
    \/ AggregateRestart
    \/ AggregateRecover
    \/ AggregateDrop
    \/ AggregateDuplicate
ApplyVoteLifecycleNext ==
    \/ ApplyLivenessNext
    \/ ApplyCrashBefore
    \/ ApplyCrashAfterPersist
    \/ ApplyCrashAfterSend
    \/ ApplyRestart
    \/ ApplyRecover
    \/ ApplyDrop
    \/ ApplyDuplicate
ViewVoteLifecycleNext ==
    \/ AdvanceLogicalTime
    \/ LifecycleSoftTimeout
    \/ LifecycleVoteViewChange
    \/ VoteTransportNext
    \/ LifecycleFinalizeViewChange
    \/ ViewCrashBefore
    \/ ViewCrashAfterPersist
    \/ ViewCrashAfterSend
    \/ ViewRestart
    \/ ViewRecover
    \/ ViewDrop
    \/ ViewDuplicate
AbortVoteLifecycleNext ==
    \/ AdvanceLogicalTime
    \/ VoteHardAbortAction
    \/ VoteTransportNext
    \/ HardAbortAction
    \/ AbortCrashBefore
    \/ AbortCrashAfterPersist
    \/ AbortCrashAfterSend
    \/ AbortRestart
    \/ AbortRecover
    \/ AbortDrop
    \/ AbortDuplicate

ConfigVoteLifecycleSpec ==
    Init /\ [][ConfigVoteLifecycleNext]_ProtocolVariables
ISCVoteLifecycleSpec ==
    Init /\ [][ISCVoteLifecycleNext]_ProtocolVariables
ECVoteLifecycleSpec ==
    Init /\ [][ECVoteLifecycleNext]_ProtocolVariables
APCVoteLifecycleSpec ==
    Init /\ [][APCVoteLifecycleNext]_ProtocolVariables
ParameterVoteLifecycleSpec ==
    Init /\ [][ParameterVoteLifecycleNext]_ProtocolVariables
AggregateVoteLifecycleSpec ==
    Init /\ [][AggregateVoteLifecycleNext]_ProtocolVariables
ApplyVoteLifecycleSpec ==
    Init /\ [][ApplyVoteLifecycleNext]_ProtocolVariables
ViewVoteLifecycleSpec ==
    Init /\ [][ViewVoteLifecycleNext]_ProtocolVariables
AbortVoteLifecycleSpec ==
    Init /\ [][AbortVoteLifecycleNext]_ProtocolVariables

VoteLifecycleTypeOK == TypeOK

=============================================================================
