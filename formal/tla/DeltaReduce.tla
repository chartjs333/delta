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
       \/ TicketNext
       \/ AvailabilityNext
       \/ CertificateNext
       \/ ReduceApplyNext

UngatedNext ==
    \/ EnabledQuorumNext
    \/ TicketNext
    \/ AvailabilityNext
    \/ CertificateNext
    \/ ReduceApplyNext

Next == OrdinaryNext \/ FailureNext

\* Reduced pre-failure configs use this spec solely to retain leaf-level TLC
\* action attribution. Mandatory deadline/view configs always use Spec.
UngatedSpec == Init /\ [][UngatedNext \/ FailureNext]_ProtocolVariables

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
