---------------------------- MODULE DeltaReduce ----------------------------
EXTENDS DeltaReduceFailures

Init ==
    /\ ModelConstantsOK
    /\ QuorumInit
    /\ FailureInit
    /\ TicketInit
    /\ AvailabilityInit
    /\ CertificateInit
    /\ ReduceApplyInit

EnabledQuorumNext ==
    /\ EnableQuorumActions
    /\ QuorumNext

OrdinaryProgressOpen ==
    /\ phase = "ACTIVE"
    /\ logicalTime < HardDeadline
    /\ abortRequests = {}

OrdinaryNext ==
    /\ OrdinaryProgressOpen
    /\ \/ EnabledQuorumNext
       \/ VoteTransportNext
       \/ TicketNext
       \/ AvailabilityNext
       \/ CertificateNext
       \/ ReduceApplyNext

UngatedNext ==
    \/ EnabledQuorumNext
    \/ VoteTransportNext
    \/ TicketNext
    \/ AvailabilityNext
    \/ CertificateNext
    \/ ReduceApplyNext

FailureActionsEnabled ==
    \/ EnableFailures
    \/ EnableNetworkFaults
    \/ EnablePartitionActions
    \/ EnableTimeoutActions

EnabledFailureNext == FailureActionsEnabled /\ FailureNext

Next == OrdinaryNext \/ EnabledFailureNext

\* Reduced pre-failure configs use this spec solely to retain leaf-level TLC
\* action attribution. Mandatory deadline/view configs always use Spec.
UngatedSpec == Init /\ [][UngatedNext \/ EnabledFailureNext]_ProtocolVariables

Spec == Init /\ [][Next]_ProtocolVariables

TypeOK ==
    /\ QuorumTypeOK
    /\ FailureTypeOK
    /\ TicketTypeOK
    /\ AvailabilityTypeOK
    /\ CertificateTypeOK
    /\ ReduceApplyTypeOK

CrashCoverageTypeOK == crashCoverage \subseteq CrashPoints

=============================================================================
