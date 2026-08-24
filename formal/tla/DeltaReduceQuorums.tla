------------------------ MODULE DeltaReduceQuorums -------------------------
EXTENDS DeltaReduceTypes

QuorumInit ==
    /\ proposals = {}
    /\ byzantine = InitialByzantine
    /\ durableVotes = {}
    /\ volatileVotes = {}
    /\ messages = {}
    /\ messageMultiplicity = [vote \in VoteRecords |-> 0]
    /\ receivedVotes = {}
    /\ finalizedCertificates = {}
    /\ durableSequence = [validator \in Validators |-> 0]
    /\ alive = Validators
    /\ recoveryState = [validator \in Validators |-> "READY"]

QuorumTypeOK ==
    /\ proposals \subseteq ProposalRecords
    /\ byzantine \subseteq Validators
    /\ Cardinality(byzantine) <= F
    /\ durableVotes \subseteq VoteRecords
    /\ volatileVotes \subseteq VoteRecords
    /\ messages \subseteq VoteRecords
    /\ messageMultiplicity \in [VoteRecords -> 0..MaxMessageCopies]
    /\ messages =
        {vote \in VoteRecords : messageMultiplicity[vote] > 0}
    /\ receivedVotes \subseteq VoteRecords
    /\ finalizedCertificates \subseteq CertificateRecords
    /\ durableSequence \in [Validators -> 0..MaxDurableSequence]
    /\ alive \subseteq Validators
    /\ recoveryState \in [Validators -> RecoveryStates]

CanVote(validator) ==
    /\ validator \in alive
    /\ recoveryState[validator] = "READY"

HasDurableVote(validator, context) ==
    \E vote \in durableVotes :
        /\ vote.validator = validator
        /\ vote.context = context

HasConflictingDurableVote(validator, context, body) ==
    \E vote \in durableVotes :
        /\ vote.validator = validator
        /\ vote.context = context
        /\ vote.body # body

ProposeRoundConfig(context, body) ==
    LET proposal == [context |-> context, body |-> body]
    IN  /\ context \in VoteContexts
        /\ body \in ConfigBodies
        /\ proposal \notin proposals
        /\ proposals' = proposals \cup {proposal}
        /\ UNCHANGED <<byzantine, durableVotes, volatileVotes, messages,
                        messageMultiplicity,
                        receivedVotes, finalizedCertificates, durableSequence,
                        alive, recoveryState, crashCoverage, TicketVariables,
                        AvailabilityVariables, CertificateVariables,
                        ReduceApplyVariables, FailureControlVariables>>

PersistConfigVote(validator, context, body) ==
    LET vote == VoteRecord(validator, context, body)
        proposal == [context |-> context, body |-> body]
    IN  /\ validator \in Validators
        /\ context \in VoteContexts
        /\ body \in ConfigBodies
        /\ proposal \in proposals
        /\ CanVote(validator)
        /\ vote \notin durableVotes
        /\ durableSequence[validator] < MaxDurableSequence
        /\ (validator \in byzantine
            \/ ~HasConflictingDurableVote(validator, context, body))
        /\ durableVotes' = durableVotes \cup {vote}
        /\ volatileVotes' = volatileVotes \cup {vote}
        /\ durableSequence' =
            [durableSequence EXCEPT ![validator] = @ + 1]
        /\ UNCHANGED <<proposals, byzantine, messages, receivedVotes,
                        messageMultiplicity,
                        finalizedCertificates, alive, recoveryState,
                        crashCoverage, TicketVariables,
                        AvailabilityVariables, CertificateVariables,
                        ReduceApplyVariables, FailureControlVariables>>

SendConfigVote(validator, context, body) ==
    LET vote == VoteRecord(validator, context, body)
    IN  /\ vote \in volatileVotes
        /\ CanVote(validator)
        /\ vote \notin messages
        /\ messageMultiplicity[vote] = 0
        /\ messages' = messages \cup {vote}
        /\ messageMultiplicity' =
            [messageMultiplicity EXCEPT ![vote] = 1]
        /\ UNCHANGED <<proposals, byzantine, durableVotes, volatileVotes,
                        receivedVotes, finalizedCertificates, durableSequence,
                        alive, recoveryState, crashCoverage, TicketVariables,
                        AvailabilityVariables, CertificateVariables,
                        ReduceApplyVariables, FailureControlVariables>>

DeliverConfigVote(vote) ==
    /\ vote \in messages
    /\ vote.validator \notin partition
    /\ messageMultiplicity[vote] > 0
    /\ messageMultiplicity' =
        [messageMultiplicity EXCEPT ![vote] = @ - 1]
    /\ messages' =
        IF messageMultiplicity[vote] = 1
        THEN messages \ {vote}
        ELSE messages
    /\ receivedVotes' = receivedVotes \cup {vote}
    /\ UNCHANGED <<proposals, byzantine, durableVotes, volatileVotes,
                    finalizedCertificates, durableSequence, alive,
                    recoveryState, crashCoverage, TicketVariables,
                    AvailabilityVariables, CertificateVariables,
                    ReduceApplyVariables, FailureControlVariables>>

DropConfigVote(vote) ==
    /\ EnableMessageDrop
    /\ vote \in messages
    /\ messageMultiplicity[vote] > 0
    /\ messageMultiplicity' =
        [messageMultiplicity EXCEPT ![vote] = @ - 1]
    /\ messages' =
        IF messageMultiplicity[vote] = 1
        THEN messages \ {vote}
        ELSE messages
    /\ UNCHANGED <<proposals, byzantine, durableVotes, volatileVotes,
                    receivedVotes, finalizedCertificates, durableSequence,
                    alive, recoveryState, crashCoverage, TicketVariables,
                    AvailabilityVariables, CertificateVariables,
                    ReduceApplyVariables, FailureControlVariables>>

ReceivedSigners(context, body) ==
    {validator \in Validators :
        VoteRecord(validator, context, body) \in receivedVotes}

ValidQC(context, body, signers) ==
    /\ context \in VoteContexts
    /\ body \in ConfigBodies
    /\ signers \subseteq ReceivedSigners(context, body)
    /\ Cardinality(signers) >= QuorumSize

FinalizeRoundConfig(context, body) ==
    LET signers == ReceivedSigners(context, body)
        certificate == CertificateRecord(context, body, signers)
    IN  /\ ValidQC(context, body, signers)
        /\ ~\E prior \in finalizedCertificates :
                /\ prior.context = context
                /\ prior.body = body
        /\ finalizedCertificates' = finalizedCertificates \cup {certificate}
        /\ UNCHANGED <<proposals, byzantine, durableVotes, volatileVotes,
                        messages, messageMultiplicity, receivedVotes,
                        durableSequence, alive,
                        recoveryState, crashCoverage, TicketVariables,
                        AvailabilityVariables, CertificateVariables,
                        ReduceApplyVariables, FailureControlVariables>>

ProposeRoundConfigAction ==
    \E context \in VoteContexts, body \in ConfigBodies :
        ProposeRoundConfig(context, body)

PersistConfigVoteAction ==
    \E validator \in Validators, context \in VoteContexts,
       body \in ConfigBodies :
        PersistConfigVote(validator, context, body)

SendConfigVoteAction ==
    \E validator \in Validators, context \in VoteContexts,
       body \in ConfigBodies :
        SendConfigVote(validator, context, body)

DeliverConfigVoteAction ==
    \E vote \in VoteRecords : DeliverConfigVote(vote)

DropConfigVoteAction ==
    \E vote \in VoteRecords : DropConfigVote(vote)

FinalizeRoundConfigAction ==
    \E context \in VoteContexts, body \in ConfigBodies :
        FinalizeRoundConfig(context, body)

QuorumNext ==
    \/ ProposeRoundConfigAction
    \/ PersistConfigVoteAction
    \/ SendConfigVoteAction
    \/ DeliverConfigVoteAction
    \/ DropConfigVoteAction
    \/ FinalizeRoundConfigAction

VoteUniqueness ==
    \A validator \in Validators \ byzantine, context \in VoteContexts :
        Cardinality(
            {body \in ConfigBodies :
                VoteRecord(validator, context, body) \in durableVotes}
        ) <= 1

QCUniqueness ==
    \A context \in VoteContexts :
        Cardinality(
            {body \in ConfigBodies :
                \E certificate \in finalizedCertificates :
                    /\ certificate.context = context
                    /\ certificate.body = body}
        ) <= 1

ConfigUniqueness == QCUniqueness

PersistBeforeSend ==
    /\ messages \subseteq durableVotes
    /\ receivedVotes \subseteq durableVotes

ValidFinalizedCertificates ==
    \A certificate \in finalizedCertificates :
        /\ Cardinality(certificate.signers) >= QuorumSize
        /\ certificate.signers \subseteq
            ReceivedSigners(certificate.context, certificate.body)

=============================================================================
