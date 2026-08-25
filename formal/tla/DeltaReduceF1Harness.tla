------------------------ MODULE DeltaReduceF1Harness -----------------------
EXTENDS DeltaReduce

\* This harness deliberately keeps the full 3f+1 constants and all protocol
\* state, while reducing the transition surface to the failure controller.
\* It makes the f=1 quorum thresholds for view-change and abort exhaustive
\* without multiplying the state graph by unrelated ticket permutations.
F1HarnessConstantsOK ==
    /\ F = 1
    /\ Cardinality(Validators) = 4
    /\ Cardinality(Tickets) >= 3
    /\ Cardinality(Workers) >= 3
    /\ Cardinality(Domains) = 2
    /\ Cardinality(Shards) = 2
    /\ QuorumSize = 3

ASSUME F = 1
ASSUME Cardinality(Validators) = 4
ASSUME Cardinality(Tickets) >= 3
ASSUME Cardinality(Workers) >= 3
ASSUME Cardinality(Domains) = 2
ASSUME Cardinality(Shards) = 2
ASSUME QuorumSize = 3

F1Init == Init /\ F1HarnessConstantsOK

F1Next == FailureNext \/ VoteTransportNext

F1Spec == F1Init /\ [][F1Next]_ProtocolVariables

=============================================================================
