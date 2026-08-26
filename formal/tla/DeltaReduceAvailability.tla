---------------------- MODULE DeltaReduceAvailability ----------------------
EXTENDS DeltaReduceTickets

AvailabilityInit ==
    /\ materializedArtifacts = {}
    /\ availableArtifacts = {}
    /\ corruptArtifacts = {}
    /\ availabilityAttestations = {}
    /\ availabilityCertificates = {}
    /\ availableTickets = {}
    /\ availabilityShortfalls = {}
    /\ lateAvailabilityEvidence = {}
    /\ repairAttempts = [content \in ContentIds |-> 0]

AvailabilityTypeOK ==
    /\ materializedArtifacts \subseteq ArtifactLocations
    /\ availableArtifacts \subseteq ArtifactLocations
    /\ corruptArtifacts \subseteq ArtifactLocations
    /\ availabilityAttestations \subseteq AvailabilityAttestationRecords
    /\ availabilityCertificates \subseteq AvailabilityCertificateRecords
    /\ availableTickets \subseteq Tickets
    /\ availabilityShortfalls \subseteq AvailabilityCertificateRecords
    /\ lateAvailabilityEvidence \subseteq AvailabilityCertificateRecords
    /\ Cardinality(lateAvailabilityEvidence) <= MaxModeledRejections
    /\ repairAttempts \in [ContentIds -> 0..MaxRepairAttempts]

ArtifactLocation(storage, content, shard) ==
    [storage |-> storage, content |-> content, shard |-> shard]

AttestationRecord(storage, ticket, content, shard) ==
    [storage |-> storage, ticket |-> ticket,
     content |-> content, shard |-> shard]

AvailabilityCertificateRecord(ticket, content) ==
    [ticket |-> ticket, content |-> content]

TicketCommittedTo(ticket, content) ==
    \E commitment \in commitments :
        /\ commitment.ticket = ticket
        /\ commitment.content = content

ContentIsCommitted(content) ==
    \E ticket \in Tickets : TicketCommittedTo(ticket, content)

AttestersFor(ticket, content, shard) ==
    {storage \in StoragePeers :
        AttestationRecord(storage, ticket, content, shard)
            \in availabilityAttestations}

AvailableAttestersFor(ticket, content, shard) ==
    {storage \in AttestersFor(ticket, content, shard) :
        ArtifactLocation(storage, content, shard) \in availableArtifacts}

HasAttestationCoverage(ticket, content) ==
    /\ TicketCommittedTo(ticket, content)
    /\ \A shard \in Shards :
        Cardinality(AttestersFor(ticket, content, shard))
            >= AvailabilityThreshold

HasCompleteAvailability(ticket, content) ==
    /\ TicketCommittedTo(ticket, content)
    /\ \A shard \in Shards :
        Cardinality(AvailableAttestersFor(ticket, content, shard))
            >= AvailabilityThreshold

HasAvailabilityCertificate(ticket, content) ==
    AvailabilityCertificateRecord(ticket, content)
        \in availabilityCertificates

ContentIsFrozen(content) ==
    \E body \in closedInputBodies :
        \E entry \in body.entries : entry.content = content

UploadArtifact(storage, ticket, content, shard) ==
    LET location == ArtifactLocation(storage, content, shard)
    IN  /\ EnableAvailabilityActions
        /\ storage \in StoragePeers
        /\ ticket \in Tickets
        /\ content \in ContentIds
        /\ shard \in Shards
        /\ TicketCommittedTo(ticket, content)
        /\ CertificateProgressOpen
        /\ location \notin materializedArtifacts
        /\ materializedArtifacts' = materializedArtifacts \cup {location}
        /\ availableArtifacts' = availableArtifacts \cup {location}
        /\ corruptArtifacts' = corruptArtifacts \ {location}
        /\ UNCHANGED <<availabilityAttestations,
                        availabilityCertificates, availableTickets,
                        availabilityShortfalls, lateAvailabilityEvidence,
                        repairAttempts, QuorumVariables, crashCoverage,
                        TicketVariables, CertificateVariables, ReduceApplyVariables, FailureControlVariables>>

AttestAvailability(storage, ticket, content, shard) ==
    LET location == ArtifactLocation(storage, content, shard)
        attestation == AttestationRecord(storage, ticket, content, shard)
    IN  /\ EnableAvailabilityActions
        /\ storage \in StoragePeers
        /\ ticket \in Tickets
        /\ content \in ContentIds
        /\ shard \in Shards
        /\ CertificateProgressOpen
        /\ TicketCommittedTo(ticket, content)
        /\ location \in availableArtifacts
        /\ attestation \notin availabilityAttestations
        /\ availabilityAttestations' =
            availabilityAttestations \cup {attestation}
        /\ UNCHANGED <<materializedArtifacts, availableArtifacts,
                        corruptArtifacts,
                        availabilityCertificates, availableTickets,
                        availabilityShortfalls, lateAvailabilityEvidence,
                        repairAttempts, QuorumVariables, crashCoverage,
                        TicketVariables, CertificateVariables, ReduceApplyVariables, FailureControlVariables>>

ObserveACShortfall(ticket, content) ==
    LET shortfall == AvailabilityCertificateRecord(ticket, content)
    IN  /\ EnableAvailabilityActions
        /\ ticket \in Tickets
        /\ content \in ContentIds
        /\ CertificateProgressOpen
        /\ TicketCommittedTo(ticket, content)
        /\ ~HasCompleteAvailability(ticket, content)
        /\ shortfall \notin availabilityShortfalls
        /\ availabilityShortfalls' = availabilityShortfalls \cup {shortfall}
        /\ UNCHANGED <<materializedArtifacts, availableArtifacts,
                        corruptArtifacts,
                        availabilityAttestations, availabilityCertificates,
                        availableTickets, lateAvailabilityEvidence,
                        repairAttempts, QuorumVariables, crashCoverage,
                        TicketVariables, CertificateVariables, ReduceApplyVariables, FailureControlVariables>>

FinalizeAvailability(ticket, content) ==
    LET certificate == AvailabilityCertificateRecord(ticket, content)
    IN  /\ EnableAvailabilityActions
        /\ ticket \in Tickets
        /\ content \in ContentIds
        /\ CertificateProgressOpen
        /\ HasCompleteAvailability(ticket, content)
        /\ certificate \notin availabilityCertificates
        /\ availabilityCertificates' =
            availabilityCertificates \cup {certificate}
        /\ availableTickets' = availableTickets \cup {ticket}
        /\ UNCHANGED <<materializedArtifacts, availableArtifacts,
                        corruptArtifacts,
                        availabilityAttestations, availabilityShortfalls,
                        lateAvailabilityEvidence, repairAttempts,
                        QuorumVariables, crashCoverage, TicketVariables,
                        CertificateVariables, ReduceApplyVariables, FailureControlVariables>>

RejectLateAvailability(storage, ticket, content, shard) ==
    LET evidence == AvailabilityCertificateRecord(ticket, content)
    IN  /\ EnableAvailabilityActions
        /\ InputClosed
        /\ storage \in StoragePeers
        /\ ticket \in Tickets
        /\ content \in ContentIds
        /\ shard \in Shards
        /\ TicketCommittedTo(ticket, content)
        /\ Cardinality(lateAvailabilityEvidence) < MaxModeledRejections
        /\ evidence \notin lateAvailabilityEvidence
        /\ lateAvailabilityEvidence' = lateAvailabilityEvidence \cup {evidence}
        /\ UNCHANGED <<materializedArtifacts, availableArtifacts,
                        corruptArtifacts, availabilityAttestations,
                        availabilityCertificates, availableTickets,
                        availabilityShortfalls, repairAttempts,
                        QuorumVariables, crashCoverage, TicketVariables,
                        CertificateVariables, ReduceApplyVariables, FailureControlVariables>>

LoseArtifactPreFreeze(storage, content, shard) ==
    LET location == ArtifactLocation(storage, content, shard)
    IN  /\ EnableAvailabilityActions
        /\ EnableAvailabilityFaults
        /\ storage \in StoragePeers
        /\ content \in ContentIds
        /\ shard \in Shards
        /\ location \in availableArtifacts
        /\ ~ContentIsFrozen(content)
        /\ availableArtifacts' = availableArtifacts \ {location}
        /\ UNCHANGED <<materializedArtifacts, corruptArtifacts,
                        availabilityAttestations,
                        availabilityCertificates, availableTickets,
                        availabilityShortfalls, lateAvailabilityEvidence,
                        repairAttempts, QuorumVariables, crashCoverage,
                        TicketVariables, CertificateVariables, ReduceApplyVariables, FailureControlVariables>>

LoseArtifactPostFreeze(storage, content, shard) ==
    LET location == ArtifactLocation(storage, content, shard)
    IN  /\ EnableAvailabilityActions
        /\ EnableAvailabilityFaults
        /\ storage \in StoragePeers
        /\ content \in ContentIds
        /\ shard \in Shards
        /\ location \in availableArtifacts
        /\ ContentIsFrozen(content)
        /\ availableArtifacts' = availableArtifacts \ {location}
        /\ UNCHANGED <<materializedArtifacts, corruptArtifacts,
                        availabilityAttestations,
                        availabilityCertificates, availableTickets,
                        availabilityShortfalls, lateAvailabilityEvidence,
                        repairAttempts, QuorumVariables, crashCoverage,
                        TicketVariables, CertificateVariables, ReduceApplyVariables, FailureControlVariables>>

CorruptArtifact(storage, content, shard) ==
    LET location == ArtifactLocation(storage, content, shard)
    IN  /\ EnableAvailabilityActions
        /\ EnableAvailabilityFaults
        /\ storage \in StoragePeers
        /\ content \in ContentIds
        /\ shard \in Shards
        /\ location \in availableArtifacts
        /\ availableArtifacts' = availableArtifacts \ {location}
        /\ corruptArtifacts' = corruptArtifacts \cup {location}
        /\ UNCHANGED <<materializedArtifacts, availabilityAttestations,
                        availabilityCertificates, availableTickets,
                        availabilityShortfalls, lateAvailabilityEvidence,
                        repairAttempts, QuorumVariables, crashCoverage,
                        TicketVariables, CertificateVariables, ReduceApplyVariables, FailureControlVariables>>

RepairArtifact(source, target, content, shard) ==
    LET sourceLocation == ArtifactLocation(source, content, shard)
        targetLocation == ArtifactLocation(target, content, shard)
    IN  /\ EnableAvailabilityActions
        /\ EnableAvailabilityFaults
        /\ abortRequests = {}
        /\ source \in StoragePeers
        /\ target \in StoragePeers
        /\ source # target
        /\ content \in ContentIds
        /\ shard \in Shards
        /\ ContentIsCommitted(content)
        /\ sourceLocation \in availableArtifacts
        /\ targetLocation \notin availableArtifacts
        /\ repairAttempts[content] < MaxRepairAttempts
        /\ materializedArtifacts' =
            materializedArtifacts \cup {targetLocation}
        /\ availableArtifacts' = availableArtifacts \cup {targetLocation}
        /\ corruptArtifacts' = corruptArtifacts \ {targetLocation}
        /\ repairAttempts' =
            [repairAttempts EXCEPT ![content] = @ + 1]
        /\ UNCHANGED <<availabilityAttestations,
                        availabilityCertificates, availableTickets,
                        availabilityShortfalls, lateAvailabilityEvidence,
                        QuorumVariables, crashCoverage, TicketVariables,
                        CertificateVariables, ReduceApplyVariables, FailureControlVariables>>

UploadArtifactAction ==
    \E storage \in StoragePeers, ticket \in Tickets,
       content \in ContentIds, shard \in Shards :
        UploadArtifact(storage, ticket, content, shard)

AttestAvailabilityAction ==
    \E storage \in StoragePeers, ticket \in Tickets,
       content \in ContentIds, shard \in Shards :
        AttestAvailability(storage, ticket, content, shard)

ObserveACShortfallAction ==
    \E ticket \in Tickets, content \in ContentIds :
        ObserveACShortfall(ticket, content)

FinalizeAvailabilityAction ==
    \E ticket \in Tickets, content \in ContentIds :
        FinalizeAvailability(ticket, content)

RejectLateAvailabilityAction ==
    \E storage \in StoragePeers, ticket \in Tickets,
       content \in ContentIds, shard \in Shards :
        RejectLateAvailability(storage, ticket, content, shard)

LoseArtifactPreFreezeAction ==
    \E storage \in StoragePeers, content \in ContentIds,
       shard \in Shards :
        LoseArtifactPreFreeze(storage, content, shard)

LoseArtifactPostFreezeAction ==
    \E storage \in StoragePeers, content \in ContentIds,
       shard \in Shards :
        LoseArtifactPostFreeze(storage, content, shard)

CorruptArtifactAction ==
    \E storage \in StoragePeers, content \in ContentIds,
       shard \in Shards : CorruptArtifact(storage, content, shard)

RepairArtifactAction ==
    \E source \in StoragePeers, target \in StoragePeers,
       content \in ContentIds, shard \in Shards :
        RepairArtifact(source, target, content, shard)

AvailabilityNext ==
    \/ UploadArtifactAction
    \/ AttestAvailabilityAction
    \/ ObserveACShortfallAction
    \/ FinalizeAvailabilityAction
    \/ RejectLateAvailabilityAction
    \/ LoseArtifactPreFreezeAction
    \/ LoseArtifactPostFreezeAction
    \/ CorruptArtifactAction
    \/ RepairArtifactAction

ArtifactStateDisjoint ==
    availableArtifacts \intersect corruptArtifacts = {}

ArtifactStateMaterialized ==
    availableArtifacts \cup corruptArtifacts \subseteq materializedArtifacts

AvailabilityCertificateSound ==
    \A certificate \in availabilityCertificates :
        HasAttestationCoverage(certificate.ticket, certificate.content)

AvailabilityBeforeISC ==
    \A certificate \in inputSetCertificates :
        \A entry \in certificate.body.entries :
            /\ entry \in availabilityCertificates
            /\ HasAttestationCoverage(entry.ticket, entry.content)

RepairAttemptsBounded ==
    \A content \in ContentIds :
        repairAttempts[content] <= MaxRepairAttempts

RepairPreservesCertifiedLineage ==
    /\ \A certificate \in availabilityCertificates :
        TicketCommittedTo(certificate.ticket, certificate.content)
    /\ \A certificate \in inputSetCertificates :
        \A entry \in certificate.body.entries :
            /\ TicketCommittedTo(entry.ticket, entry.content)
            /\ HasAvailabilityCertificate(entry.ticket, entry.content)

AvailableTicketCertified ==
    \A ticket \in availableTickets :
        \E content \in ContentIds :
            HasAvailabilityCertificate(ticket, content)

=============================================================================
