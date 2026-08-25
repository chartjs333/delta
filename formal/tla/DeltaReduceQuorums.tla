------------------------ MODULE DeltaReduceQuorums -------------------------
EXTENDS DeltaReduceTypes

QuorumInit ==
    /\ proposals = {}
    /\ byzantine = InitialByzantine
    /\ durableVotes = {}
    /\ volatileVotes = {}
    /\ messages = {}
    /\ messageMultiplicity = {}
    /\ receivedVotes = {}
    /\ finalizedCertificates = {}
    /\ durableSequence = [validator \in Validators |-> 0]
    /\ alive = Validators
    /\ recoveryState = [validator \in Validators |-> "READY"]

IsVoteEnvelope(vote) ==
    /\ vote.validator \in Validators
    /\ vote.kind \in VoteKinds

MessageCopy(vote, copy) == [vote |-> vote, copy |-> copy]

IsMessageCopy(messageCopy) ==
    /\ IsVoteEnvelope(messageCopy.vote)
    /\ messageCopy.copy \in 1..MaxMessageCopies

MessageCopiesFor(vote) ==
    {copy \in 1..MaxMessageCopies :
        MessageCopy(vote, copy) \in messageMultiplicity}

QuorumTypeOK ==
    /\ proposals \subseteq ProposalRecords
    /\ byzantine \subseteq Validators
    /\ Cardinality(byzantine) <= F
    /\ \A vote \in durableVotes : IsVoteEnvelope(vote)
    /\ \A vote \in volatileVotes : IsVoteEnvelope(vote)
    /\ \A vote \in messages : IsVoteEnvelope(vote)
    /\ \A copy \in messageMultiplicity : IsMessageCopy(copy)
    /\ messages = {copy.vote : copy \in messageMultiplicity}
    /\ \A vote \in receivedVotes : IsVoteEnvelope(vote)
    /\ finalizedCertificates \subseteq CertificateRecords
    /\ durableSequence \in [Validators -> 0..MaxDurableSequence]
    /\ alive \subseteq Validators
    /\ recoveryState \in [Validators -> RecoveryStates]

CanVote(validator) ==
    /\ validator \in alive
    /\ recoveryState[validator] = "READY"

CanPersistVoteEnvelope(vote) ==
    /\ IsVoteEnvelope(vote)
    /\ CanVote(vote.validator)
    /\ vote \notin durableVotes
    /\ durableSequence[vote.validator] < MaxDurableSequence

PersistVoteEnvelopeChanges(vote) ==
    /\ durableVotes' = durableVotes \cup {vote}
    /\ volatileVotes' = volatileVotes \cup {vote}
    /\ durableSequence' =
        [durableSequence EXCEPT ![vote.validator] = @ + 1]

HasDeliveredVote(validator, kind, body) ==
    \E vote \in receivedVotes :
        /\ vote.validator = validator
        /\ vote.kind = kind
        /\ vote.body = body

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
        /\ CanPersistVoteEnvelope(vote)
        /\ (validator \in byzantine
            \/ ~HasConflictingDurableVote(validator, context, body))
        /\ PersistVoteEnvelopeChanges(vote)
        /\ UNCHANGED <<proposals, byzantine, messages, receivedVotes,
                        messageMultiplicity,
                        finalizedCertificates, alive, recoveryState,
                        crashCoverage, TicketVariables,
                        AvailabilityVariables, CertificateVariables,
                        ReduceApplyVariables, FailureControlVariables>>

SendVoteEnvelope(vote) ==
    /\ vote \in volatileVotes
    /\ CanVote(vote.validator)
    /\ vote \notin receivedVotes
    /\ vote \notin messages
    /\ MessageCopiesFor(vote) = {}
    /\ messages' = messages \cup {vote}
    /\ messageMultiplicity' =
        messageMultiplicity \cup {MessageCopy(vote, 1)}
    /\ UNCHANGED <<proposals, byzantine, durableVotes, volatileVotes,
                    receivedVotes, finalizedCertificates, durableSequence,
                    alive, recoveryState, crashCoverage, TicketVariables,
                    AvailabilityVariables, CertificateVariables,
                    ReduceApplyVariables, FailureControlVariables>>

SendConfigVote(validator, context, body) ==
    LET vote == VoteRecord(validator, context, body)
    IN  /\ vote.kind = "ROUND_CONFIG"
        /\ SendVoteEnvelope(vote)

DeliverVoteEnvelope(vote, copy) ==
    /\ vote \in messages
    /\ vote.validator \notin partition
    /\ copy \in MessageCopiesFor(vote)
    /\ messageMultiplicity' =
        messageMultiplicity \ {MessageCopy(vote, copy)}
    /\ messages' =
        IF Cardinality(MessageCopiesFor(vote)) = 1
        THEN messages \ {vote}
        ELSE messages
    /\ receivedVotes' = receivedVotes \cup {vote}
    /\ UNCHANGED <<proposals, byzantine, durableVotes, volatileVotes,
                    finalizedCertificates, durableSequence, alive,
                    recoveryState, crashCoverage, TicketVariables,
                    AvailabilityVariables, CertificateVariables,
                    ReduceApplyVariables, FailureControlVariables>>

DeliverConfigVote(vote, copy) ==
    /\ vote.kind = "ROUND_CONFIG"
    /\ DeliverVoteEnvelope(vote, copy)

DropVoteEnvelope(vote, copy) ==
    /\ EnableMessageDrop
    /\ vote \in messages
    /\ copy \in MessageCopiesFor(vote)
    /\ messageMultiplicity' =
        messageMultiplicity \ {MessageCopy(vote, copy)}
    /\ messages' =
        IF Cardinality(MessageCopiesFor(vote)) = 1
        THEN messages \ {vote}
        ELSE messages
    /\ UNCHANGED <<proposals, byzantine, durableVotes, volatileVotes,
                    receivedVotes, finalizedCertificates, durableSequence,
                    alive, recoveryState, crashCoverage, TicketVariables,
                    AvailabilityVariables, CertificateVariables,
                    ReduceApplyVariables, FailureControlVariables>>

DropConfigVote(vote, copy) ==
    /\ vote.kind = "ROUND_CONFIG"
    /\ DropVoteEnvelope(vote, copy)

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

SendVoteEnvelopeAction ==
    \E vote \in volatileVotes : SendVoteEnvelope(vote)

DeliverVoteEnvelopeAction ==
    \E vote \in messages, copy \in 1..MaxMessageCopies :
        DeliverVoteEnvelope(vote, copy)

DeliverConfigVoteAction ==
    \E vote \in messages, copy \in 1..MaxMessageCopies :
        DeliverConfigVote(vote, copy)

DropConfigVoteAction ==
    \E vote \in messages, copy \in 1..MaxMessageCopies :
        DropConfigVote(vote, copy)

FinalizeRoundConfigAction ==
    \E context \in VoteContexts, body \in ConfigBodies :
        FinalizeRoundConfig(context, body)

QuorumNext ==
    \/ ProposeRoundConfigAction
    \/ PersistConfigVoteAction
    \/ DropConfigVoteAction
    \/ FinalizeRoundConfigAction

VoteTransportNext ==
    \/ SendVoteEnvelopeAction
    \/ DeliverVoteEnvelopeAction

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
