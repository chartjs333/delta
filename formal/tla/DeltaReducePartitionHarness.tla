--------------------- MODULE DeltaReducePartitionHarness -------------------
EXTENDS DeltaReduce

VARIABLE splitHealed

SplitVariables == <<ProtocolVariables, splitHealed>>

SplitBodyA == CHOOSE body \in ConfigBodies : TRUE
SplitBodyB == CHOOSE body \in ConfigBodies \ {SplitBodyA} : TRUE
SplitContext == CHOOSE context \in VoteContexts : TRUE
SplitValidatorsA ==
    CHOOSE validators \in SUBSET Validators : Cardinality(validators) = 2
SplitValidatorsB == Validators \ SplitValidatorsA

SplitVotesA ==
    {VoteRecord(validator, SplitContext, SplitBodyA) :
        validator \in SplitValidatorsA}
SplitVotesB ==
    {VoteRecord(validator, SplitContext, SplitBodyB) :
        validator \in SplitValidatorsB}
SplitVotes == SplitVotesA \cup SplitVotesB

SplitHarnessConstantsOK ==
    /\ F = 1
    /\ Cardinality(Validators) = 4
    /\ Cardinality(ConfigBodies) = 2
    /\ QuorumSize = 3
    /\ MaxMessageCopies >= 2

ASSUME F = 1
ASSUME Cardinality(Validators) = 4
ASSUME Cardinality(ConfigBodies) = 2
ASSUME QuorumSize = 3
ASSUME MaxMessageCopies >= 2

SplitInit ==
    /\ ModelConstantsOK
    /\ SplitHarnessConstantsOK
    /\ proposals =
        {[context |-> SplitContext, body |-> SplitBodyA],
         [context |-> SplitContext, body |-> SplitBodyB]}
    /\ byzantine = InitialByzantine
    /\ durableVotes = SplitVotes
    /\ volatileVotes = SplitVotes
    /\ messages = SplitVotes
    /\ messageMultiplicity =
        {MessageCopy(vote, 1) : vote \in SplitVotes}
    /\ receivedVotes = {}
    /\ finalizedCertificates = {}
    /\ durableSequence = [validator \in Validators |-> 1]
    /\ alive = Validators
    /\ recoveryState = [validator \in Validators |-> "READY"]
    /\ TicketInit
    /\ AvailabilityInit
    /\ CertificateInit
    /\ ReduceApplyInit
    /\ FailureInit
    /\ splitHealed = FALSE

SplitDeliverMessage ==
    /\ DeliverMessageAction
    /\ UNCHANGED splitHealed

SplitDropMessage ==
    /\ DropMessageAction
    /\ UNCHANGED splitHealed

SplitDuplicateMessage ==
    /\ DuplicateMessageAction
    /\ UNCHANGED splitHealed

SplitEnablePartition ==
    /\ EnablePartitionAction
    /\ UNCHANGED splitHealed

SplitHealPartition ==
    /\ HealPartitionAction
    /\ splitHealed' = TRUE

SplitFinalizeRoundConfig ==
    /\ FinalizeRoundConfigAction
    /\ UNCHANGED splitHealed

SplitNext ==
    \/ SplitDeliverMessage
    \/ SplitDropMessage
    \/ SplitDuplicateMessage
    \/ SplitEnablePartition
    \/ SplitHealPartition
    \/ SplitFinalizeRoundConfig

SplitSpec == SplitInit /\ [][SplitNext]_SplitVariables

SplitTypeOK == TypeOK /\ splitHealed \in BOOLEAN

SplitBrainNoQC == finalizedCertificates = {}

=============================================================================
