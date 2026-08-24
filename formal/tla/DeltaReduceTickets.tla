------------------------- MODULE DeltaReduceTickets -------------------------
EXTENDS DeltaReduceQuorums

TicketInit ==
    /\ ticketPlan = {}
    /\ leaseOwner = [ticket \in Tickets |-> "NO_WORKER"]
    /\ leaseEpoch = [ticket \in Tickets |-> 0]
    /\ leaseActive = {}
    /\ commitments = {}
    /\ rejectedCommitments = {}

TicketTypeOK ==
    /\ ticketPlan \subseteq TicketDefinitions
    /\ leaseOwner \in [Tickets -> Workers \cup {"NO_WORKER"}]
    /\ leaseEpoch \in [Tickets -> 0..MaxLeaseEpoch]
    /\ leaseActive \subseteq Tickets
    /\ commitments \subseteq CommitmentRecords
    /\ rejectedCommitments \subseteq RejectedCommitmentRecords
    /\ Cardinality(rejectedCommitments) <= MaxModeledRejections

DefinitionsFor(ticket) ==
    {definition \in ticketPlan : definition.ticket = ticket}

PlannedTickets ==
    {ticket \in Tickets : DefinitionsFor(ticket) # {}}

CommitmentsFor(ticket) ==
    {commitment \in commitments : commitment.ticket = ticket}

CommittedContents(ticket) ==
    {commitment.content : commitment \in CommitmentsFor(ticket)}

HasCommitment(ticket) == CommitmentsFor(ticket) # {}

ExactCommitmentExists(ticket, worker, epoch, content) ==
    [ticket |-> ticket, worker |-> worker,
     leaseEpoch |-> epoch, content |-> content] \in commitments

TicketingAuthorized == finalizedCertificates # {}

IssueTicket(definition) ==
    /\ EnableTicketActions
    /\ CertificateProgressOpen
    /\ TicketingAuthorized
    /\ definition \in TicketDefinitions
    /\ definition.ticket \in RequiredTickets
    /\ DefinitionsFor(definition.ticket) = {}
    /\ ticketPlan' = ticketPlan \cup {definition}
    /\ UNCHANGED <<leaseOwner, leaseEpoch, leaseActive, commitments,
                    rejectedCommitments, QuorumVariables, crashCoverage,
                    AvailabilityVariables, CertificateVariables, ReduceApplyVariables, FailureControlVariables>>

LeaseTicket(ticket, worker) ==
    /\ EnableTicketActions
    /\ CertificateProgressOpen
    /\ ticket \in PlannedTickets
    /\ worker \in Workers
    /\ ~HasCommitment(ticket)
    /\ ticket \notin leaseActive
    /\ leaseOwner[ticket] = "NO_WORKER"
    /\ leaseEpoch[ticket] = 0
    /\ leaseOwner' = [leaseOwner EXCEPT ![ticket] = worker]
    /\ leaseActive' = leaseActive \cup {ticket}
    /\ UNCHANGED <<ticketPlan, leaseEpoch, commitments,
                    rejectedCommitments, QuorumVariables, crashCoverage,
                    AvailabilityVariables, CertificateVariables, ReduceApplyVariables, FailureControlVariables>>

\* Lease renewal changes only a concrete deadline.  The formal abstraction
\* records the authorization guard and refines the deadline write to stutter;
\* owner, epoch, ticket definition and every consensus-visible value remain
\* unchanged.
RenewLease(ticket, worker, epoch) ==
    /\ EnableTicketActions
    /\ CertificateProgressOpen
    /\ ticket \in leaseActive
    /\ worker = leaseOwner[ticket]
    /\ epoch = leaseEpoch[ticket]
    /\ ~HasCommitment(ticket)
    /\ UNCHANGED <<ticketPlan, leaseOwner, leaseEpoch, leaseActive,
                    commitments, rejectedCommitments, QuorumVariables,
                    crashCoverage, AvailabilityVariables,
                    CertificateVariables, ReduceApplyVariables,
                    FailureControlVariables>>

ExpireLease(ticket) ==
    /\ EnableTicketActions
    /\ CertificateProgressOpen
    /\ ticket \in leaseActive
    /\ ~HasCommitment(ticket)
    /\ leaseActive' = leaseActive \ {ticket}
    /\ UNCHANGED <<ticketPlan, leaseOwner, leaseEpoch, commitments,
                    rejectedCommitments, QuorumVariables, crashCoverage,
                    AvailabilityVariables, CertificateVariables, ReduceApplyVariables, FailureControlVariables>>

ReassignTicket(ticket, worker) ==
    /\ EnableTicketActions
    /\ CertificateProgressOpen
    /\ ticket \in PlannedTickets
    /\ worker \in Workers
    /\ ~HasCommitment(ticket)
    /\ ticket \notin leaseActive
    /\ leaseOwner[ticket] \in Workers
    /\ worker # leaseOwner[ticket]
    /\ leaseEpoch[ticket] < MaxLeaseEpoch
    /\ leaseOwner' = [leaseOwner EXCEPT ![ticket] = worker]
    /\ leaseEpoch' = [leaseEpoch EXCEPT ![ticket] = @ + 1]
    /\ leaseActive' = leaseActive \cup {ticket}
    /\ UNCHANGED <<ticketPlan, commitments, rejectedCommitments,
                    QuorumVariables, crashCoverage, AvailabilityVariables,
                    CertificateVariables, ReduceApplyVariables, FailureControlVariables>>

CommitTicket(ticket, worker, epoch, content) ==
    LET commitment ==
            [ticket |-> ticket, worker |-> worker,
             leaseEpoch |-> epoch, content |-> content]
    IN  /\ EnableTicketActions
        /\ CertificateProgressOpen
        /\ ticket \in PlannedTickets
        /\ ticket \in CompletedTickets
        /\ worker \in Workers
        /\ epoch \in 0..MaxLeaseEpoch
        /\ content \in ContentIds
        /\ ~HasCommitment(ticket)
        /\ ticket \in leaseActive
        /\ leaseOwner[ticket] = worker
        /\ leaseEpoch[ticket] = epoch
        /\ commitments' = commitments \cup {commitment}
        /\ leaseActive' = leaseActive \ {ticket}
        /\ UNCHANGED <<ticketPlan, leaseOwner, leaseEpoch,
                        rejectedCommitments, QuorumVariables, crashCoverage,
                        AvailabilityVariables, CertificateVariables, ReduceApplyVariables, FailureControlVariables>>

RejectStaleCommitment(ticket, worker, epoch, content) ==
    LET rejection ==
            [ticket |-> ticket, worker |-> worker,
             leaseEpoch |-> epoch, content |-> content,
             reason |-> "STALE_LEASE"]
    IN  /\ EnableTicketActions
        /\ CertificateProgressOpen
        /\ ticket \in PlannedTickets
        /\ worker \in Workers
        /\ epoch \in 0..MaxLeaseEpoch
        /\ content \in ContentIds
        /\ Cardinality(rejectedCommitments) < MaxModeledRejections
        /\ ~ExactCommitmentExists(ticket, worker, epoch, content)
        /\ \/ ~HasCommitment(ticket)
           \/ content \in CommittedContents(ticket)
        /\ \/ ticket \notin leaseActive
           \/ leaseOwner[ticket] # worker
           \/ leaseEpoch[ticket] # epoch
        /\ rejection \notin rejectedCommitments
        /\ rejectedCommitments' = rejectedCommitments \cup {rejection}
        /\ UNCHANGED <<ticketPlan, leaseOwner, leaseEpoch, leaseActive,
                        commitments, QuorumVariables, crashCoverage,
                        AvailabilityVariables, CertificateVariables, ReduceApplyVariables, FailureControlVariables>>

RejectCommitmentEquivocation(ticket, worker, epoch, content) ==
    LET rejection ==
            [ticket |-> ticket, worker |-> worker,
             leaseEpoch |-> epoch, content |-> content,
             reason |-> "COMMIT_EQUIVOCATION"]
    IN  /\ EnableTicketActions
        /\ CertificateProgressOpen
        /\ ticket \in PlannedTickets
        /\ worker \in Workers
        /\ epoch \in 0..MaxLeaseEpoch
        /\ content \in ContentIds
        /\ Cardinality(rejectedCommitments) < MaxModeledRejections
        /\ HasCommitment(ticket)
        /\ content \notin CommittedContents(ticket)
        /\ rejection \notin rejectedCommitments
        /\ rejectedCommitments' = rejectedCommitments \cup {rejection}
        /\ UNCHANGED <<ticketPlan, leaseOwner, leaseEpoch, leaseActive,
                        commitments, QuorumVariables, crashCoverage,
                        AvailabilityVariables, CertificateVariables, ReduceApplyVariables, FailureControlVariables>>

RejectLateCommitment(ticket, worker, epoch, content) ==
    LET rejection ==
            [ticket |-> ticket, worker |-> worker,
             leaseEpoch |-> epoch, content |-> content,
             reason |-> "LATE_AFTER_CLOSE"]
    IN  /\ EnableTicketActions
        /\ InputClosed
        /\ ticket \in Tickets
        /\ worker \in Workers
        /\ epoch \in 0..MaxLeaseEpoch
        /\ content \in ContentIds
        /\ ~ExactCommitmentExists(ticket, worker, epoch, content)
        /\ Cardinality(rejectedCommitments) < MaxModeledRejections
        /\ rejection \notin rejectedCommitments
        /\ rejectedCommitments' = rejectedCommitments \cup {rejection}
        /\ UNCHANGED <<ticketPlan, leaseOwner, leaseEpoch, leaseActive,
                        commitments, QuorumVariables, crashCoverage,
                        AvailabilityVariables, CertificateVariables, ReduceApplyVariables, FailureControlVariables>>

IssueTicketAction ==
    \E definition \in TicketDefinitions : IssueTicket(definition)

LeaseTicketAction ==
    \E ticket \in Tickets, worker \in Workers : LeaseTicket(ticket, worker)

RenewLeaseAction ==
    \E ticket \in Tickets, worker \in Workers,
       epoch \in 0..MaxLeaseEpoch : RenewLease(ticket, worker, epoch)

ExpireLeaseAction ==
    \E ticket \in Tickets : ExpireLease(ticket)

ReassignTicketAction ==
    \E ticket \in Tickets, worker \in Workers : ReassignTicket(ticket, worker)

CommitTicketAction ==
    \E ticket \in Tickets, worker \in Workers,
       epoch \in 0..MaxLeaseEpoch, content \in ContentIds :
        CommitTicket(ticket, worker, epoch, content)

RejectStaleCommitmentAction ==
    \E ticket \in Tickets, worker \in Workers,
       epoch \in 0..MaxLeaseEpoch, content \in ContentIds :
        RejectStaleCommitment(ticket, worker, epoch, content)

RejectCommitmentEquivocationAction ==
    \E ticket \in Tickets, worker \in Workers,
       epoch \in 0..MaxLeaseEpoch, content \in ContentIds :
        RejectCommitmentEquivocation(ticket, worker, epoch, content)

RejectLateCommitmentAction ==
    \E ticket \in Tickets, worker \in Workers,
       epoch \in 0..MaxLeaseEpoch, content \in ContentIds :
        RejectLateCommitment(ticket, worker, epoch, content)

TicketNext ==
    \/ IssueTicketAction
    \/ LeaseTicketAction
    \/ RenewLeaseAction
    \/ ExpireLeaseAction
    \/ ReassignTicketAction
    \/ CommitTicketAction
    \/ RejectStaleCommitmentAction
    \/ RejectCommitmentEquivocationAction
    \/ RejectLateCommitmentAction

TicketImmutability ==
    \A ticket \in Tickets : Cardinality(DefinitionsFor(ticket)) <= 1

LeaseCommitSafety ==
    \A commitment \in commitments :
        /\ commitment.ticket \in PlannedTickets
        /\ commitment.ticket \in CompletedTickets
        /\ commitment.worker = leaseOwner[commitment.ticket]
        /\ commitment.leaseEpoch = leaseEpoch[commitment.ticket]
        /\ commitment.ticket \notin leaseActive

CommitUniqueness ==
    \A ticket \in Tickets : Cardinality(CommittedContents(ticket)) <= 1

NoReassignAfterCommit ==
    \A ticket \in Tickets :
        HasCommitment(ticket) => ticket \notin leaseActive

=============================================================================
