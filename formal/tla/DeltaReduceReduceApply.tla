----------------------- MODULE DeltaReduceReduceApply -----------------------
EXTENDS DeltaReduceCertificates

ReduceApplyInit ==
    /\ parameterResults = {}
    /\ parameterVotes = {}
    /\ parameterQCs = {}
    /\ aggregateCandidates = {}
    /\ aggregateVotes = {}
    /\ aggregateRootQCs = {}
    /\ applyCandidates = {}
    /\ applyVotes = {}
    /\ applyQCs = {}
    /\ currentCheckpoint = InitialCurrentCheckpoint
    /\ currentAdvanceReceipts = {}
    /\ currentReplayReceipts = {}
    /\ pendingPointerRecoveries = {}
    /\ publishedObjects = {}
    /\ rejectedPublications = {}
    /\ reduceApplyRejections = {}

ParameterKey(domain, shard) ==
    [domain |-> domain, shard |-> shard]

ParameterResultBody(apc, domain, shard, parent, schema,
                    arithmeticProfile, value, checked) ==
    [round |-> apc.isc.round,
     config |-> apc.isc.config,
     isc |-> apc.isc,
     seed |-> apc.seed,
     ec |-> apc.ec,
     apc |-> apc,
     domain |-> domain,
     shard |-> shard,
     parent |-> parent,
     schema |-> schema,
     arithmeticProfile |-> arithmeticProfile,
     coefficientProfile |-> apc.coefficientProfile,
     value |-> value,
     checked |-> checked]

IsParameterResultBody(body) ==
    /\ body.round \in RoundContexts
    /\ body.config \in ConfigBodies
    /\ IsInputSetBody(body.isc)
    /\ IsSeedTranscript(body.seed)
    /\ IsEligibilityBody(body.ec)
    /\ IsAggregationPlanBody(body.apc)
    /\ body.domain \in Domains
    /\ body.shard \in Shards
    /\ body.parent \in ParentCheckpoints
    /\ body.schema \in ParameterSchemas
    /\ body.arithmeticProfile \in ArithmeticProfiles
    /\ body.coefficientProfile \in CoefficientProfiles
    /\ body.value \in ParameterValues
    /\ body.checked \in BOOLEAN

ParameterVoteRecord(validator, body) ==
    [validator |-> validator, body |-> body]

IsParameterVote(vote) ==
    /\ vote.validator \in Validators
    /\ IsParameterResultBody(vote.body)

IsParameterQC(certificate) ==
    /\ IsParameterResultBody(certificate.body)
    /\ certificate.signers \subseteq Validators

AggregateRootBody(apc, leaves) ==
    [round |-> apc.isc.round,
     config |-> apc.isc.config,
     isc |-> apc.isc,
     seed |-> apc.seed,
     ec |-> apc.ec,
     apc |-> apc,
     parent |-> ConfiguredParentCheckpoint,
     schema |-> ConfiguredParameterSchema,
     arithmeticProfile |-> ConfiguredArithmeticProfile,
     coefficientProfile |-> apc.coefficientProfile,
     leaves |-> leaves,
     canonicalRoot |-> leaves]

IsAggregateRootBody(body) ==
    /\ body.round \in RoundContexts
    /\ body.config \in ConfigBodies
    /\ IsInputSetBody(body.isc)
    /\ IsSeedTranscript(body.seed)
    /\ IsEligibilityBody(body.ec)
    /\ IsAggregationPlanBody(body.apc)
    /\ body.parent \in ParentCheckpoints
    /\ body.schema \in ParameterSchemas
    /\ body.arithmeticProfile \in ArithmeticProfiles
    /\ body.coefficientProfile \in CoefficientProfiles
    /\ \A leaf \in body.leaves : IsParameterResultBody(leaf)
    /\ \A leaf \in body.canonicalRoot : IsParameterResultBody(leaf)

AggregateVoteRecord(validator, body) ==
    [validator |-> validator, body |-> body]

IsAggregateVote(vote) ==
    /\ vote.validator \in Validators
    /\ IsAggregateRootBody(vote.body)

IsAggregateRootQC(certificate) ==
    /\ IsAggregateRootBody(certificate.body)
    /\ certificate.signers \subseteq Validators

ApplyBody(root, parent, applyProfile, nextCheckpoint,
          nextModelHash, nextOptimizerHash, checked) ==
    [round |-> root.round,
     config |-> root.config,
     aggregate |-> root,
     parent |-> parent,
     applyProfile |-> applyProfile,
     nextCheckpoint |-> nextCheckpoint,
     nextModelHash |-> nextModelHash,
     nextOptimizerHash |-> nextOptimizerHash,
     checked |-> checked]

IsApplyBody(body) ==
    /\ body.round \in RoundContexts
    /\ body.config \in ConfigBodies
    /\ IsAggregateRootBody(body.aggregate)
    /\ body.parent \in CheckpointIds
    /\ body.applyProfile \in ApplyProfiles
    /\ body.nextCheckpoint \in CheckpointIds
    /\ body.nextModelHash \in ModelHashes
    /\ body.nextOptimizerHash \in OptimizerHashes
    /\ body.checked \in BOOLEAN

ApplyVoteRecord(validator, body) ==
    [validator |-> validator, body |-> body]

IsApplyVote(vote) ==
    /\ vote.validator \in Validators
    /\ IsApplyBody(vote.body)

IsApplyQC(certificate) ==
    /\ IsApplyBody(certificate.body)
    /\ certificate.signers \subseteq Validators

IsPublicationObject(object) ==
    /\ object.kind \in PublicationKinds
    /\ CASE object.kind = "AGGREGATE_ROOT_QC" ->
                IsAggregateRootBody(object.reference)
         [] object.kind = "APPLY_QC" ->
                IsApplyBody(object.reference)
         [] object.kind = "CURRENT_CHECKPOINT" ->
                object.reference \in CheckpointIds
         [] object.kind = "WORKER_COMMITMENT" ->
                object.reference \in CommitmentRecords
         [] object.kind = "AVAILABILITY_FRAGMENT" ->
                object.reference \in AvailabilityAttestationRecords
         [] object.kind = "PARAMETER_PARTIAL" ->
                IsParameterResultBody(object.reference)

ReduceApplyTypeOK ==
    /\ \A body \in parameterResults : IsParameterResultBody(body)
    /\ \A vote \in parameterVotes : IsParameterVote(vote)
    /\ \A certificate \in parameterQCs : IsParameterQC(certificate)
    /\ \A body \in aggregateCandidates : IsAggregateRootBody(body)
    /\ \A vote \in aggregateVotes : IsAggregateVote(vote)
    /\ \A certificate \in aggregateRootQCs :
        IsAggregateRootQC(certificate)
    /\ \A body \in applyCandidates : IsApplyBody(body)
    /\ \A vote \in applyVotes : IsApplyVote(vote)
    /\ \A certificate \in applyQCs : IsApplyQC(certificate)
    /\ currentCheckpoint \in CheckpointIds
    /\ \A body \in currentAdvanceReceipts : IsApplyBody(body)
    /\ \A body \in currentReplayReceipts : IsApplyBody(body)
    /\ \A body \in pendingPointerRecoveries : IsApplyBody(body)
    /\ \A object \in publishedObjects : IsPublicationObject(object)
    /\ \A object \in rejectedPublications : IsPublicationObject(object)
    /\ reduceApplyRejections \subseteq ReduceApplyRejectionRecords
    /\ Cardinality(reduceApplyRejections)
        <= MaxModeledReduceApplyRejections
    /\ Cardinality(rejectedPublications)
        <= MaxModeledReduceApplyRejections

UpstreamVariablesUnchanged ==
    UNCHANGED <<QuorumVariables, crashCoverage, TicketVariables,
                AvailabilityVariables, CertificateVariables,
                FailureControlVariables>>

PersistedReduceVoteUpstreamUnchanged ==
    UNCHANGED <<proposals, byzantine, messages, messageMultiplicity,
                receivedVotes, finalizedCertificates, alive, recoveryState,
                crashCoverage, TicketVariables, AvailabilityVariables,
                CertificateVariables, FailureControlVariables>>

AdvanceUpstreamVariablesUnchanged ==
    UNCHANGED <<QuorumVariables, crashCoverage, TicketVariables,
                AvailabilityVariables, CertificateVariables,
                partition, view, logicalTime, timeoutObservations,
                timeoutVotes, viewChangeQCs, abortVotes, abortQCs,
                abortReason>>

CheckedParameterValue(value) ==
    /\ value \in Int
    /\ -AccumulatorBound <= value
    /\ value <= AccumulatorBound

TicketMatchesParameterContext(ticket) ==
    \E definition \in ticketPlan :
        /\ definition.ticket = ticket
        /\ definition.parent = ConfiguredParentCheckpoint
        /\ definition.schema = ConfiguredParameterSchema
        /\ definition.profile = ConfiguredArithmeticProfile

DomainMembers(apc, domain) ==
    {ticket \in apc.members :
        \E definition \in ticketPlan :
            /\ definition.ticket = ticket
            /\ definition.domain = domain}

APCContextMatches(apc) ==
    /\ apc \in FinalizedAPCBodies
    /\ apc.coefficientProfile = ConfiguredCoefficientProfile
    /\ apc.coefficientProfile \in SafeCoefficientProfiles
    /\ \A ticket \in apc.members : TicketMatchesParameterContext(ticket)

ValidParameterParent(body) ==
    /\ body.apc \in FinalizedAPCBodies
    /\ APCContextMatches(body.apc)
    /\ body.round = body.apc.isc.round
    /\ body.config = body.apc.isc.config
    /\ body.isc = body.apc.isc
    /\ body.seed = body.apc.seed
    /\ body.ec = body.apc.ec
    /\ body.parent = ConfiguredParentCheckpoint
    /\ body.schema = ConfiguredParameterSchema
    /\ body.arithmeticProfile = ConfiguredArithmeticProfile
    /\ body.coefficientProfile = body.apc.coefficientProfile
    /\ DomainMembers(body.apc, body.domain) # {}

ValidParameterArithmetic(body) ==
    /\ body.checked = TRUE
    /\ CheckedParameterValue(body.value)
    /\ body.value = ExpectedParameterValue

ValidParameterResultBody(body) ==
    /\ IsParameterResultBody(body)
    /\ ValidParameterParent(body)
    /\ ValidParameterArithmetic(body)

ParameterContextEqual(left, right) ==
    /\ left.apc = right.apc
    /\ left.domain = right.domain
    /\ left.shard = right.shard

ParameterSigners(body) ==
    {validator \in Validators :
        HasDeliveredVote(validator, "PARAMETER", body)}

HasConflictingParameterVote(validator, body) ==
    \E vote \in parameterVotes :
        /\ vote.validator = validator
        /\ ParameterContextEqual(vote.body, body)
        /\ vote.body # body

FinalizedParameterBodies ==
    {certificate.body : certificate \in parameterQCs}

FinalizedParameterBodiesForKey(apc, domain, shard) ==
    {body \in FinalizedParameterBodies :
        /\ body.apc = apc
        /\ body.domain = domain
        /\ body.shard = shard}

FinalizedParameterBodiesForAPC(apc) ==
    {body \in FinalizedParameterBodies : body.apc = apc}

ProposeParameterResult(body) ==
    /\ EnableReduceApplyActions
    /\ IsParameterResultBody(body)
    /\ ValidParameterResultBody(body)
    /\ ~RoundAbortRequired(body.round)
    /\ currentCheckpoint = body.parent
    /\ body \notin parameterResults
    /\ parameterResults' = parameterResults \cup {body}
    /\ UNCHANGED <<parameterVotes, parameterQCs,
                    aggregateCandidates, aggregateVotes, aggregateRootQCs,
                    applyCandidates, applyVotes, applyQCs,
                    currentCheckpoint, currentAdvanceReceipts,
                    currentReplayReceipts, pendingPointerRecoveries,
                    publishedObjects, rejectedPublications,
                    reduceApplyRejections>>
    /\ UpstreamVariablesUnchanged

VoteParameter(validator, body) ==
    LET vote == ParameterVoteRecord(validator, body)
        envelope ==
            VoteEnvelope(
                validator, "PARAMETER",
                ParameterKey(body.domain, body.shard), body)
    IN  /\ EnableReduceApplyActions
        /\ validator \in Validators
        /\ body \in parameterResults
        /\ CanPersistVoteEnvelope(envelope)
        /\ vote \notin parameterVotes
        /\ \/ validator \in byzantine
           \/ ~HasConflictingParameterVote(validator, body)
        /\ PersistVoteEnvelopeChanges(envelope)
        /\ parameterVotes' = parameterVotes \cup {vote}
        /\ UNCHANGED <<parameterResults, parameterQCs,
                        aggregateCandidates, aggregateVotes,
                        aggregateRootQCs, applyCandidates, applyVotes,
                        applyQCs, currentCheckpoint,
                        currentAdvanceReceipts, currentReplayReceipts,
                        pendingPointerRecoveries, publishedObjects,
                        rejectedPublications, reduceApplyRejections>>
        /\ PersistedReduceVoteUpstreamUnchanged

FinalizeParameterQC(body) ==
    LET signers == ParameterSigners(body)
        certificate == [body |-> body, signers |-> signers]
    IN  /\ EnableReduceApplyActions
        /\ body \in parameterResults
        /\ ValidParameterResultBody(body)
        /\ Cardinality(signers) >= QuorumSize
        /\ FinalizedParameterBodiesForKey(
                body.apc, body.domain, body.shard) = {}
        /\ parameterQCs' = parameterQCs \cup {certificate}
        /\ UNCHANGED <<parameterResults, parameterVotes,
                        aggregateCandidates, aggregateVotes,
                        aggregateRootQCs, applyCandidates, applyVotes,
                        applyQCs, currentCheckpoint,
                        currentAdvanceReceipts, currentReplayReceipts,
                        pendingPointerRecoveries, publishedObjects,
                        rejectedPublications, reduceApplyRejections>>
        /\ UpstreamVariablesUnchanged

RecordReduceApplyRejection(rejection) ==
    /\ rejection \in ReduceApplyRejectionRecords
    /\ Cardinality(reduceApplyRejections)
        < MaxModeledReduceApplyRejections
    /\ rejection \notin reduceApplyRejections
    /\ reduceApplyRejections' = reduceApplyRejections \cup {rejection}

RejectParameterWrongParent(body) ==
    LET rejection ==
            [kind |-> "PARAMETER", round |-> body.round,
             reason |-> "WRONG_PARENT"]
    IN  /\ EnableReduceApplyActions
        /\ EnableReduceApplyFaults
        /\ IsParameterResultBody(body)
        /\ ~ValidParameterParent(body)
        /\ RecordReduceApplyRejection(rejection)
        /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                        aggregateCandidates, aggregateVotes,
                        aggregateRootQCs, applyCandidates, applyVotes,
                        applyQCs, currentCheckpoint,
                        currentAdvanceReceipts, currentReplayReceipts,
                        pendingPointerRecoveries, publishedObjects,
                        rejectedPublications>>
        /\ UpstreamVariablesUnchanged

RejectParameterUnchecked(body) ==
    LET rejection ==
            [kind |-> "PARAMETER", round |-> body.round,
             reason |-> "UNCHECKED_ARITHMETIC"]
    IN  /\ EnableReduceApplyActions
        /\ EnableReduceApplyFaults
        /\ IsParameterResultBody(body)
        /\ ValidParameterParent(body)
        /\ body.checked = FALSE
        /\ RecordReduceApplyRejection(rejection)
        /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                        aggregateCandidates, aggregateVotes,
                        aggregateRootQCs, applyCandidates, applyVotes,
                        applyQCs, currentCheckpoint,
                        currentAdvanceReceipts, currentReplayReceipts,
                        pendingPointerRecoveries, publishedObjects,
                        rejectedPublications>>
        /\ UpstreamVariablesUnchanged

RejectParameterOverflow(body) ==
    LET rejection ==
            [kind |-> "PARAMETER", round |-> body.round,
             reason |-> "ARITHMETIC_OVERFLOW"]
    IN  /\ EnableReduceApplyActions
        /\ EnableReduceApplyFaults
        /\ IsParameterResultBody(body)
        /\ ValidParameterParent(body)
        /\ body.checked = TRUE
        /\ ~CheckedParameterValue(body.value)
        /\ RecordReduceApplyRejection(rejection)
        /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                        aggregateCandidates, aggregateVotes,
                        aggregateRootQCs, applyCandidates, applyVotes,
                        applyQCs, currentCheckpoint,
                        currentAdvanceReceipts, currentReplayReceipts,
                        pendingPointerRecoveries, publishedObjects,
                        rejectedPublications>>
        /\ UpstreamVariablesUnchanged

RejectConflictingParameter(body) ==
    LET rejection ==
            [kind |-> "PARAMETER", round |-> body.round,
             reason |-> "CONFLICTING_CERTIFICATE"]
    IN  /\ EnableReduceApplyActions
        /\ EnableReduceApplyFaults
        /\ IsParameterResultBody(body)
        /\ FinalizedParameterBodiesForKey(
                body.apc, body.domain, body.shard) # {}
        /\ body \notin FinalizedParameterBodiesForKey(
                body.apc, body.domain, body.shard)
        /\ RecordReduceApplyRejection(rejection)
        /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                        aggregateCandidates, aggregateVotes,
                        aggregateRootQCs, applyCandidates, applyVotes,
                        applyQCs, currentCheckpoint,
                        currentAdvanceReceipts, currentReplayReceipts,
                        pendingPointerRecoveries, publishedObjects,
                        rejectedPublications>>
        /\ UpstreamVariablesUnchanged

LeafKey(leaf) == ParameterKey(leaf.domain, leaf.shard)

LeafKeys(leaves) == {LeafKey(leaf) : leaf \in leaves}

DuplicateLeafKeyExists(leaves) ==
    \E left, right \in leaves :
        /\ left # right
        /\ LeafKey(left) = LeafKey(right)

ValidAggregateParent(body) ==
    /\ body.apc \in FinalizedAPCBodies
    /\ body.round = body.apc.isc.round
    /\ body.config = body.apc.isc.config
    /\ body.isc = body.apc.isc
    /\ body.seed = body.apc.seed
    /\ body.ec = body.apc.ec
    /\ body.parent = ConfiguredParentCheckpoint
    /\ body.schema = ConfiguredParameterSchema
    /\ body.arithmeticProfile = ConfiguredArithmeticProfile
    /\ body.coefficientProfile = body.apc.coefficientProfile

LeavesUseExactParent(body) ==
    \A leaf \in body.leaves :
        /\ leaf \in FinalizedParameterBodies
        /\ leaf.apc = body.apc
        /\ leaf.round = body.round
        /\ leaf.config = body.config
        /\ leaf.isc = body.isc
        /\ leaf.seed = body.seed
        /\ leaf.ec = body.ec
        /\ leaf.parent = body.parent
        /\ leaf.schema = body.schema
        /\ leaf.arithmeticProfile = body.arithmeticProfile
        /\ leaf.coefficientProfile = body.coefficientProfile

ExactAggregateCoverage(body) ==
    /\ LeafKeys(body.leaves) = ParameterKeys
    /\ ~DuplicateLeafKeyExists(body.leaves)

ValidAggregateRootBody(body) ==
    /\ IsAggregateRootBody(body)
    /\ ValidAggregateParent(body)
    /\ LeavesUseExactParent(body)
    /\ ExactAggregateCoverage(body)
    /\ body.canonicalRoot = body.leaves

AggregateSigners(body) ==
    {validator \in Validators :
        HasDeliveredVote(validator, "AGGREGATE_ROOT", body)}

HasConflictingAggregateVote(validator, body) ==
    \E vote \in aggregateVotes :
        /\ vote.validator = validator
        /\ vote.body.apc = body.apc
        /\ vote.body # body

FinalizedAggregateBodies ==
    {certificate.body : certificate \in aggregateRootQCs}

FinalizedAggregateBodiesForAPC(apc) ==
    {body \in FinalizedAggregateBodies : body.apc = apc}

AssembleAggregateRoot(body) ==
    /\ EnableReduceApplyActions
    /\ EnableAggregateActions
    /\ ValidAggregateRootBody(body)
    /\ ~RoundAbortRequired(body.round)
    /\ body \notin aggregateCandidates
    /\ aggregateCandidates' = aggregateCandidates \cup {body}
    /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                    aggregateVotes, aggregateRootQCs, applyCandidates,
                    applyVotes, applyQCs, currentCheckpoint,
                    currentAdvanceReceipts, currentReplayReceipts,
                    pendingPointerRecoveries, publishedObjects,
                    rejectedPublications, reduceApplyRejections>>
    /\ UpstreamVariablesUnchanged

VoteAggregateRoot(validator, body) ==
    LET vote == AggregateVoteRecord(validator, body)
        envelope == VoteEnvelope(validator, "AGGREGATE_ROOT", body.apc, body)
    IN  /\ EnableReduceApplyActions
        /\ EnableAggregateActions
        /\ validator \in Validators
        /\ body \in aggregateCandidates
        /\ CanPersistVoteEnvelope(envelope)
        /\ vote \notin aggregateVotes
        /\ \/ validator \in byzantine
           \/ ~HasConflictingAggregateVote(validator, body)
        /\ PersistVoteEnvelopeChanges(envelope)
        /\ aggregateVotes' = aggregateVotes \cup {vote}
        /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                        aggregateCandidates, aggregateRootQCs,
                        applyCandidates, applyVotes, applyQCs,
                        currentCheckpoint, currentAdvanceReceipts,
                        currentReplayReceipts, pendingPointerRecoveries,
                        publishedObjects, rejectedPublications,
                        reduceApplyRejections>>
        /\ PersistedReduceVoteUpstreamUnchanged

FinalizeAggregateRootQC(body) ==
    LET signers == AggregateSigners(body)
        certificate == [body |-> body, signers |-> signers]
    IN  /\ EnableReduceApplyActions
        /\ EnableAggregateActions
        /\ body \in aggregateCandidates
        /\ ValidAggregateRootBody(body)
        /\ Cardinality(signers) >= QuorumSize
        /\ FinalizedAggregateBodiesForAPC(body.apc) = {}
        /\ aggregateRootQCs' = aggregateRootQCs \cup {certificate}
        /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                        aggregateCandidates, aggregateVotes,
                        applyCandidates, applyVotes, applyQCs,
                        currentCheckpoint, currentAdvanceReceipts,
                        currentReplayReceipts, pendingPointerRecoveries,
                        publishedObjects, rejectedPublications,
                        reduceApplyRejections>>
        /\ UpstreamVariablesUnchanged

RejectIncompleteAggregate(body) ==
    LET rejection ==
            [kind |-> "AGGREGATE_ROOT", round |-> body.round,
             reason |-> "INCOMPLETE_COVERAGE"]
    IN  /\ EnableReduceApplyActions
        /\ EnableAggregateActions
        /\ EnableReduceApplyFaults
        /\ IsAggregateRootBody(body)
        /\ ValidAggregateParent(body)
        /\ ~DuplicateLeafKeyExists(body.leaves)
        /\ LeafKeys(body.leaves) # ParameterKeys
        /\ RecordReduceApplyRejection(rejection)
        /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                        aggregateCandidates, aggregateVotes,
                        aggregateRootQCs, applyCandidates, applyVotes,
                        applyQCs, currentCheckpoint,
                        currentAdvanceReceipts, currentReplayReceipts,
                        pendingPointerRecoveries, publishedObjects,
                        rejectedPublications>>
        /\ UpstreamVariablesUnchanged

RejectDuplicateAggregate(body) ==
    LET rejection ==
            [kind |-> "AGGREGATE_ROOT", round |-> body.round,
             reason |-> "DUPLICATE_COVERAGE"]
    IN  /\ EnableReduceApplyActions
        /\ EnableAggregateActions
        /\ EnableReduceApplyFaults
        /\ IsAggregateRootBody(body)
        /\ ValidAggregateParent(body)
        /\ DuplicateLeafKeyExists(body.leaves)
        /\ RecordReduceApplyRejection(rejection)
        /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                        aggregateCandidates, aggregateVotes,
                        aggregateRootQCs, applyCandidates, applyVotes,
                        applyQCs, currentCheckpoint,
                        currentAdvanceReceipts, currentReplayReceipts,
                        pendingPointerRecoveries, publishedObjects,
                        rejectedPublications>>
        /\ UpstreamVariablesUnchanged

RejectMixedAggregate(body) ==
    LET rejection ==
            [kind |-> "AGGREGATE_ROOT", round |-> body.round,
             reason |-> "MIXED_PARENT"]
    IN  /\ EnableReduceApplyActions
        /\ EnableAggregateActions
        /\ EnableReduceApplyFaults
        /\ IsAggregateRootBody(body)
        /\ ValidAggregateParent(body)
        /\ \E leaf \in body.leaves :
            \/ leaf \notin FinalizedParameterBodies
            \/ leaf.apc # body.apc
            \/ leaf.config # body.config
            \/ leaf.parent # body.parent
            \/ leaf.schema # body.schema
            \/ leaf.arithmeticProfile # body.arithmeticProfile
            \/ leaf.coefficientProfile # body.coefficientProfile
        /\ RecordReduceApplyRejection(rejection)
        /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                        aggregateCandidates, aggregateVotes,
                        aggregateRootQCs, applyCandidates, applyVotes,
                        applyQCs, currentCheckpoint,
                        currentAdvanceReceipts, currentReplayReceipts,
                        pendingPointerRecoveries, publishedObjects,
                        rejectedPublications>>
        /\ UpstreamVariablesUnchanged

RejectConflictingAggregate(body) ==
    LET rejection ==
            [kind |-> "AGGREGATE_ROOT", round |-> body.round,
             reason |-> "CONFLICTING_CERTIFICATE"]
    IN  /\ EnableReduceApplyActions
        /\ EnableAggregateActions
        /\ EnableReduceApplyFaults
        /\ IsAggregateRootBody(body)
        /\ FinalizedAggregateBodiesForAPC(body.apc) # {}
        /\ body \notin FinalizedAggregateBodiesForAPC(body.apc)
        /\ RecordReduceApplyRejection(rejection)
        /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                        aggregateCandidates, aggregateVotes,
                        aggregateRootQCs, applyCandidates, applyVotes,
                        applyQCs, currentCheckpoint,
                        currentAdvanceReceipts, currentReplayReceipts,
                        pendingPointerRecoveries, publishedObjects,
                        rejectedPublications>>
        /\ UpstreamVariablesUnchanged

ValidApplyParent(body) ==
    /\ body.aggregate \in FinalizedAggregateBodies
    /\ body.round = body.aggregate.round
    /\ body.config = body.aggregate.config
    /\ body.parent = body.aggregate.parent

ValidApplyArithmetic(body) ==
    /\ body.applyProfile = ConfiguredApplyProfile
    /\ body.applyProfile \in SafeApplyProfiles
    /\ body.nextCheckpoint = ExpectedNextCheckpoint
    /\ body.nextModelHash = ExpectedNextModelHash
    /\ body.nextOptimizerHash = ExpectedNextOptimizerHash
    /\ body.checked = TRUE

ValidApplyBody(body) ==
    /\ IsApplyBody(body)
    /\ ValidApplyParent(body)
    /\ ValidApplyArithmetic(body)

ApplySigners(body) ==
    {validator \in Validators :
        HasDeliveredVote(validator, "APPLY", body)}

HasConflictingApplyVote(validator, body) ==
    \E vote \in applyVotes :
        /\ vote.validator = validator
        /\ vote.body.aggregate = body.aggregate
        /\ vote.body # body

FinalizedApplyBodies ==
    {certificate.body : certificate \in applyQCs}

FinalizedApplyBodiesForRoot(root) ==
    {body \in FinalizedApplyBodies : body.aggregate = root}

ComputeApplyCandidate(body) ==
    /\ EnableReduceApplyActions
    /\ EnableApplyActions
    /\ ValidApplyBody(body)
    /\ ~RoundAbortRequired(body.round)
    /\ currentCheckpoint = body.parent
    /\ body \notin applyCandidates
    /\ applyCandidates' = applyCandidates \cup {body}
    /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                    aggregateCandidates, aggregateVotes, aggregateRootQCs,
                    applyVotes, applyQCs, currentCheckpoint,
                    currentAdvanceReceipts, currentReplayReceipts,
                    pendingPointerRecoveries, publishedObjects,
                    rejectedPublications, reduceApplyRejections>>
    /\ UpstreamVariablesUnchanged

VoteApply(validator, body) ==
    LET vote == ApplyVoteRecord(validator, body)
        envelope == VoteEnvelope(validator, "APPLY", body.aggregate, body)
    IN  /\ EnableReduceApplyActions
        /\ EnableApplyActions
        /\ validator \in Validators
        /\ body \in applyCandidates
        /\ currentCheckpoint = body.parent
        /\ CanPersistVoteEnvelope(envelope)
        /\ vote \notin applyVotes
        /\ \/ validator \in byzantine
           \/ ~HasConflictingApplyVote(validator, body)
        /\ PersistVoteEnvelopeChanges(envelope)
        /\ applyVotes' = applyVotes \cup {vote}
        /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                        aggregateCandidates, aggregateVotes,
                        aggregateRootQCs, applyCandidates, applyQCs,
                        currentCheckpoint, currentAdvanceReceipts,
                        currentReplayReceipts, pendingPointerRecoveries,
                        publishedObjects, rejectedPublications,
                        reduceApplyRejections>>
        /\ PersistedReduceVoteUpstreamUnchanged

FinalizeApplyQC(body) ==
    LET signers == ApplySigners(body)
        certificate == [body |-> body, signers |-> signers]
    IN  /\ EnableReduceApplyActions
        /\ EnableApplyActions
        /\ body \in applyCandidates
        /\ ValidApplyBody(body)
        /\ currentCheckpoint = body.parent
        /\ Cardinality(signers) >= QuorumSize
        /\ FinalizedApplyBodiesForRoot(body.aggregate) = {}
        /\ applyQCs' = applyQCs \cup {certificate}
        /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                        aggregateCandidates, aggregateVotes,
                        aggregateRootQCs, applyCandidates, applyVotes,
                        currentCheckpoint, currentAdvanceReceipts,
                        currentReplayReceipts, pendingPointerRecoveries,
                        publishedObjects, rejectedPublications,
                        reduceApplyRejections>>
        /\ UpstreamVariablesUnchanged

RejectWrongApplyParent(body) ==
    LET rejection ==
            [kind |-> "APPLY", round |-> body.round,
             reason |-> "WRONG_PARENT"]
    IN  /\ EnableReduceApplyActions
        /\ EnableApplyActions
        /\ EnableReduceApplyFaults
        /\ IsApplyBody(body)
        /\ ~ValidApplyParent(body)
        /\ RecordReduceApplyRejection(rejection)
        /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                        aggregateCandidates, aggregateVotes,
                        aggregateRootQCs, applyCandidates, applyVotes,
                        applyQCs, currentCheckpoint,
                        currentAdvanceReceipts, currentReplayReceipts,
                        pendingPointerRecoveries, publishedObjects,
                        rejectedPublications>>
        /\ UpstreamVariablesUnchanged

RejectUnsafeApply(body) ==
    LET rejection ==
            [kind |-> "APPLY", round |-> body.round,
             reason |-> "UNSAFE_APPLY_PROFILE"]
    IN  /\ EnableReduceApplyActions
        /\ EnableApplyActions
        /\ EnableReduceApplyFaults
        /\ IsApplyBody(body)
        /\ ValidApplyParent(body)
        /\ body.applyProfile = ConfiguredApplyProfile
        /\ body.applyProfile \notin SafeApplyProfiles
        /\ RecordReduceApplyRejection(rejection)
        /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                        aggregateCandidates, aggregateVotes,
                        aggregateRootQCs, applyCandidates, applyVotes,
                        applyQCs, currentCheckpoint,
                        currentAdvanceReceipts, currentReplayReceipts,
                        pendingPointerRecoveries, publishedObjects,
                        rejectedPublications>>
        /\ UpstreamVariablesUnchanged

RejectConflictingApply(body) ==
    LET rejection ==
            [kind |-> "APPLY", round |-> body.round,
             reason |-> "CONFLICTING_CERTIFICATE"]
    IN  /\ EnableReduceApplyActions
        /\ EnableApplyActions
        /\ EnableReduceApplyFaults
        /\ IsApplyBody(body)
        /\ FinalizedApplyBodiesForRoot(body.aggregate) # {}
        /\ body \notin FinalizedApplyBodiesForRoot(body.aggregate)
        /\ RecordReduceApplyRejection(rejection)
        /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                        aggregateCandidates, aggregateVotes,
                        aggregateRootQCs, applyCandidates, applyVotes,
                        applyQCs, currentCheckpoint,
                        currentAdvanceReceipts, currentReplayReceipts,
                        pendingPointerRecoveries, publishedObjects,
                        rejectedPublications>>
        /\ UpstreamVariablesUnchanged

CrashAfterApplyQCBeforePointer(body) ==
    /\ EnableReduceApplyActions
    /\ EnableApplyActions
    /\ EnableReduceApplyFaults
    /\ body \in FinalizedApplyBodies
    /\ currentCheckpoint = body.parent
    /\ body \notin pendingPointerRecoveries
    /\ pendingPointerRecoveries' =
        pendingPointerRecoveries \cup {body}
    /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                    aggregateCandidates, aggregateVotes, aggregateRootQCs,
                    applyCandidates, applyVotes, applyQCs,
                    currentCheckpoint, currentAdvanceReceipts,
                    currentReplayReceipts, publishedObjects,
                    rejectedPublications, reduceApplyRejections>>
    /\ UpstreamVariablesUnchanged

AdvanceCurrentCheckpoint(body) ==
    /\ EnableReduceApplyActions
    /\ EnableApplyActions
    /\ body \in FinalizedApplyBodies
    /\ ValidApplyBody(body)
    /\ phase \in {"ACTIVE", "ABORTING"}
    /\ currentCheckpoint = body.parent
    /\ currentCheckpoint' = body.nextCheckpoint
    /\ phase' = "APPLIED"
    /\ currentAdvanceReceipts' = currentAdvanceReceipts \cup {body}
    /\ pendingPointerRecoveries' = pendingPointerRecoveries \ {body}
    /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                    aggregateCandidates, aggregateVotes, aggregateRootQCs,
                    applyCandidates, applyVotes, applyQCs,
                    currentReplayReceipts, publishedObjects,
                    rejectedPublications, reduceApplyRejections>>
    /\ AdvanceUpstreamVariablesUnchanged

ReplayCurrentAdvance(body) ==
    /\ EnableReduceApplyActions
    /\ EnableApplyActions
    /\ EnableReduceApplyFaults
    /\ body \in currentAdvanceReceipts
    /\ currentCheckpoint = body.nextCheckpoint
    /\ body \notin currentReplayReceipts
    /\ currentReplayReceipts' = currentReplayReceipts \cup {body}
    /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                    aggregateCandidates, aggregateVotes, aggregateRootQCs,
                    applyCandidates, applyVotes, applyQCs,
                    currentCheckpoint, currentAdvanceReceipts,
                    pendingPointerRecoveries, publishedObjects,
                    rejectedPublications, reduceApplyRejections>>
    /\ UpstreamVariablesUnchanged

RejectCurrentConflict(body) ==
    LET rejection ==
            [kind |-> "CURRENT", round |-> body.round,
             reason |-> "CURRENT_CONFLICT"]
    IN  /\ EnableReduceApplyActions
        /\ EnableApplyActions
        /\ EnableReduceApplyFaults
        /\ IsApplyBody(body)
        /\ currentCheckpoint # body.parent
        /\ currentCheckpoint # body.nextCheckpoint
        /\ RecordReduceApplyRejection(rejection)
        /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                        aggregateCandidates, aggregateVotes,
                        aggregateRootQCs, applyCandidates, applyVotes,
                        applyQCs, currentCheckpoint,
                        currentAdvanceReceipts, currentReplayReceipts,
                        pendingPointerRecoveries, publishedObjects,
                        rejectedPublications>>
        /\ UpstreamVariablesUnchanged

CertifiedGlobalObjects ==
    {[kind |-> "AGGREGATE_ROOT_QC", reference |-> certificate.body] :
        certificate \in aggregateRootQCs}
    \cup {[kind |-> "APPLY_QC", reference |-> certificate.body] :
        certificate \in applyQCs}
    \cup {[kind |-> "CURRENT_CHECKPOINT",
            reference |-> body.nextCheckpoint] :
        body \in currentAdvanceReceipts}

ForbiddenPublicationObjects ==
    {[kind |-> "WORKER_COMMITMENT", reference |-> commitment] :
        commitment \in commitments}
    \cup {[kind |-> "AVAILABILITY_FRAGMENT", reference |-> attestation] :
        attestation \in availabilityAttestations}
    \cup {[kind |-> "PARAMETER_PARTIAL", reference |-> body] :
        body \in parameterResults}

PublishCertifiedObject(object) ==
    /\ EnableReduceApplyActions
    /\ EnablePublicationActions
    /\ object \in CertifiedGlobalObjects
    /\ object \notin publishedObjects
    /\ publishedObjects' = publishedObjects \cup {object}
    /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                    aggregateCandidates, aggregateVotes, aggregateRootQCs,
                    applyCandidates, applyVotes, applyQCs,
                    currentCheckpoint, currentAdvanceReceipts,
                    currentReplayReceipts, pendingPointerRecoveries,
                    rejectedPublications, reduceApplyRejections>>
    /\ UpstreamVariablesUnchanged

RejectForbiddenPublication(object) ==
    /\ EnableReduceApplyActions
    /\ EnablePublicationActions
    /\ EnableReduceApplyFaults
    /\ object \in ForbiddenPublicationObjects
    /\ Cardinality(rejectedPublications)
        < MaxModeledReduceApplyRejections
    /\ object \notin rejectedPublications
    /\ rejectedPublications' = rejectedPublications \cup {object}
    /\ UNCHANGED <<parameterResults, parameterVotes, parameterQCs,
                    aggregateCandidates, aggregateVotes, aggregateRootQCs,
                    applyCandidates, applyVotes, applyQCs,
                    currentCheckpoint, currentAdvanceReceipts,
                    currentReplayReceipts, pendingPointerRecoveries,
                    publishedObjects, reduceApplyRejections>>
    /\ UpstreamVariablesUnchanged

ProposeParameterResultAction ==
    \E apc \in FinalizedAPCBodies, domain \in Domains,
       shard \in Shards :
        ProposeParameterResult(
            ParameterResultBody(
                apc, domain, shard, ConfiguredParentCheckpoint,
                ConfiguredParameterSchema, ConfiguredArithmeticProfile,
                ExpectedParameterValue, TRUE))

VoteParameterAction ==
    \E validator \in Validators, body \in parameterResults :
        VoteParameter(validator, body)

FinalizeParameterQCAction ==
    \E body \in parameterResults : FinalizeParameterQC(body)

RejectParameterWrongParentAction ==
    \E apc \in FinalizedAPCBodies :
        \E profile \in CoefficientProfiles \ {apc.coefficientProfile},
           domain \in Domains, shard \in Shards :
            LET otherAPC ==
                    [apc EXCEPT !.coefficientProfile = profile]
            IN RejectParameterWrongParent(
                ParameterResultBody(
                    otherAPC, domain, shard, ConfiguredParentCheckpoint,
                    ConfiguredParameterSchema, ConfiguredArithmeticProfile,
                    ExpectedParameterValue, TRUE))

RejectParameterUncheckedAction ==
    \E apc \in FinalizedAPCBodies, domain \in Domains,
       shard \in Shards :
        RejectParameterUnchecked(
            ParameterResultBody(
                apc, domain, shard, ConfiguredParentCheckpoint,
                ConfiguredParameterSchema, ConfiguredArithmeticProfile,
                ExpectedParameterValue, FALSE))

RejectParameterOverflowAction ==
    \E apc \in FinalizedAPCBodies, domain \in Domains,
       shard \in Shards, value \in ParameterValues :
        RejectParameterOverflow(
            ParameterResultBody(
                apc, domain, shard, ConfiguredParentCheckpoint,
                ConfiguredParameterSchema, ConfiguredArithmeticProfile,
                value, TRUE))

RejectConflictingParameterAction ==
    \E body \in FinalizedParameterBodies :
        RejectConflictingParameter([body EXCEPT !.checked = FALSE])

AssembleAggregateRootAction ==
    \E apc \in FinalizedAPCBodies :
        AssembleAggregateRoot(
            AggregateRootBody(
                apc, FinalizedParameterBodiesForAPC(apc)))

VoteAggregateRootAction ==
    \E validator \in Validators, body \in aggregateCandidates :
        VoteAggregateRoot(validator, body)

FinalizeAggregateRootQCAction ==
    \E body \in aggregateCandidates : FinalizeAggregateRootQC(body)

RejectIncompleteAggregateAction ==
    \E apc \in FinalizedAPCBodies :
        \E leaves \in SUBSET FinalizedParameterBodiesForAPC(apc) :
            RejectIncompleteAggregate(AggregateRootBody(apc, leaves))

RejectDuplicateAggregateAction ==
    \E apc \in FinalizedAPCBodies :
        \E leaf \in FinalizedParameterBodiesForAPC(apc) :
            LET duplicate == [leaf EXCEPT !.checked = FALSE]
            IN RejectDuplicateAggregate(
                AggregateRootBody(
                    apc,
                    FinalizedParameterBodiesForAPC(apc) \cup {duplicate}))

RejectMixedAggregateAction ==
    \E apc \in FinalizedAPCBodies :
        \E leaf \in FinalizedParameterBodiesForAPC(apc) :
            \E profile \in
                    CoefficientProfiles \ {apc.coefficientProfile} :
                LET otherAPC ==
                        [apc EXCEPT !.coefficientProfile = profile]
                    mixedLeaf ==
                        [leaf EXCEPT !.apc = otherAPC,
                                     !.coefficientProfile = profile]
                IN RejectMixedAggregate(
                    AggregateRootBody(
                        apc,
                        (FinalizedParameterBodiesForAPC(apc) \ {leaf})
                            \cup {mixedLeaf}))

RejectConflictingAggregateAction ==
    \E body \in FinalizedAggregateBodies :
        RejectConflictingAggregate(
            [body EXCEPT !.canonicalRoot = {}])

ComputeApplyCandidateAction ==
    \E root \in FinalizedAggregateBodies :
        ComputeApplyCandidate(
            ApplyBody(
                root, root.parent, ConfiguredApplyProfile,
                ExpectedNextCheckpoint, ExpectedNextModelHash,
                ExpectedNextOptimizerHash, TRUE))

VoteApplyAction ==
    \E validator \in Validators, body \in applyCandidates :
        VoteApply(validator, body)

FinalizeApplyQCAction ==
    \E body \in applyCandidates : FinalizeApplyQC(body)

RejectWrongApplyParentAction ==
    \E root \in FinalizedAggregateBodies :
        \E parent \in CheckpointIds \ {root.parent} :
            RejectWrongApplyParent(
                ApplyBody(
                    root, parent, ConfiguredApplyProfile,
                    ExpectedNextCheckpoint, ExpectedNextModelHash,
                    ExpectedNextOptimizerHash, TRUE))

RejectUnsafeApplyAction ==
    \E root \in FinalizedAggregateBodies :
        RejectUnsafeApply(
            ApplyBody(
                root, root.parent, ConfiguredApplyProfile,
                ExpectedNextCheckpoint, ExpectedNextModelHash,
                ExpectedNextOptimizerHash, TRUE))

RejectConflictingApplyAction ==
    \E body \in FinalizedApplyBodies :
        \E modelHash \in ModelHashes \ {body.nextModelHash} :
            RejectConflictingApply(
                [body EXCEPT !.nextModelHash = modelHash])

CrashAfterApplyQCBeforePointerAction ==
    \E body \in FinalizedApplyBodies :
        CrashAfterApplyQCBeforePointer(body)

AdvanceCurrentCheckpointAction ==
    \E body \in FinalizedApplyBodies :
        AdvanceCurrentCheckpoint(body)

ReplayCurrentAdvanceAction ==
    \E body \in currentAdvanceReceipts : ReplayCurrentAdvance(body)

RejectCurrentConflictAction ==
    \E body \in FinalizedApplyBodies :
        RejectCurrentConflict(
            [body EXCEPT !.nextCheckpoint = body.parent])

PublishCertifiedObjectAction ==
    \E object \in CertifiedGlobalObjects : PublishCertifiedObject(object)

RejectForbiddenPublicationAction ==
    \E object \in ForbiddenPublicationObjects :
        RejectForbiddenPublication(object)

ReduceApplyNext ==
    \/ ProposeParameterResultAction
    \/ VoteParameterAction
    \/ FinalizeParameterQCAction
    \/ RejectParameterWrongParentAction
    \/ RejectParameterUncheckedAction
    \/ RejectParameterOverflowAction
    \/ RejectConflictingParameterAction
    \/ AssembleAggregateRootAction
    \/ VoteAggregateRootAction
    \/ FinalizeAggregateRootQCAction
    \/ RejectIncompleteAggregateAction
    \/ RejectDuplicateAggregateAction
    \/ RejectMixedAggregateAction
    \/ RejectConflictingAggregateAction
    \/ ComputeApplyCandidateAction
    \/ VoteApplyAction
    \/ FinalizeApplyQCAction
    \/ RejectWrongApplyParentAction
    \/ RejectUnsafeApplyAction
    \/ RejectConflictingApplyAction
    \/ CrashAfterApplyQCBeforePointerAction
    \/ AdvanceCurrentCheckpointAction
    \/ ReplayCurrentAdvanceAction
    \/ RejectCurrentConflictAction
    \/ PublishCertifiedObjectAction
    \/ RejectForbiddenPublicationAction

ConsensusIntegerOnly ==
    /\ \A body \in parameterResults : body.value \in Int
    /\ \A certificate \in parameterQCs :
        certificate.body.value \in Int

NoOverflow ==
    /\ \A body \in parameterResults :
        /\ body.checked = TRUE
        /\ CheckedParameterValue(body.value)
    /\ \A certificate \in parameterQCs :
        /\ certificate.body.checked = TRUE
        /\ CheckedParameterValue(certificate.body.value)
    /\ \A body \in applyCandidates : body.checked = TRUE
    /\ \A certificate \in applyQCs : certificate.body.checked = TRUE

ShardViewAtomicity ==
    /\ \A certificate \in parameterQCs :
        ValidParameterResultBody(certificate.body)
    /\ \A body \in aggregateCandidates :
        /\ ValidAggregateParent(body)
        /\ LeavesUseExactParent(body)
    /\ \A certificate \in aggregateRootQCs :
        /\ ValidAggregateParent(certificate.body)
        /\ LeavesUseExactParent(certificate.body)

AggregateCompleteness ==
    \A certificate \in aggregateRootQCs :
        ValidAggregateRootBody(certificate.body)

ApplyUniqueness ==
    \A root \in FinalizedAggregateBodies :
        Cardinality(FinalizedApplyBodiesForRoot(root)) <= 1

CurrentCertified ==
    /\ \/ currentCheckpoint = InitialCurrentCheckpoint
       \/ \E body \in currentAdvanceReceipts :
            /\ body \in FinalizedApplyBodies
            /\ body.nextCheckpoint = currentCheckpoint
    /\ phase = "APPLIED" =>
        /\ currentCheckpoint # InitialCurrentCheckpoint
        /\ \E body \in currentAdvanceReceipts :
            body.nextCheckpoint = currentCheckpoint

RecoveryIdempotence ==
    /\ \A body \in currentReplayReceipts :
        /\ body \in currentAdvanceReceipts
        /\ currentCheckpoint = body.nextCheckpoint
    /\ \A body \in pendingPointerRecoveries :
        /\ body \in FinalizedApplyBodies
        /\ currentCheckpoint = body.parent

PlaneSeparation ==
    /\ publishedObjects \cap ForbiddenPublicationObjects = {}
    /\ \A object \in publishedObjects :
        object.kind \in SafePublicationKinds

CertifiedPublishOnly == publishedObjects \subseteq CertifiedGlobalObjects

ReduceApplyVoteUniqueness ==
    /\ \A validator \in Validators \ byzantine,
          apc \in FinalizedAPCBodies, key \in ParameterKeys :
        Cardinality(
            {vote.body : vote \in
                {candidate \in parameterVotes :
                    /\ candidate.validator = validator
                    /\ candidate.body.apc = apc
                    /\ LeafKey(candidate.body) = key}}) <= 1
    /\ \A validator \in Validators \ byzantine,
          apc \in FinalizedAPCBodies :
        Cardinality(
            {vote.body : vote \in
                {candidate \in aggregateVotes :
                    /\ candidate.validator = validator
                    /\ candidate.body.apc = apc}}) <= 1
    /\ \A validator \in Validators \ byzantine,
          root \in FinalizedAggregateBodies :
        Cardinality(
            {vote.body : vote \in
                {candidate \in applyVotes :
                    /\ candidate.validator = validator
                    /\ candidate.body.aggregate = root}}) <= 1

ReduceApplyQCUniqueness ==
    /\ \A apc \in FinalizedAPCBodies,
          domain \in Domains, shard \in Shards :
        Cardinality(
            FinalizedParameterBodiesForKey(apc, domain, shard)) <= 1
    /\ \A apc \in FinalizedAPCBodies :
        Cardinality(FinalizedAggregateBodiesForAPC(apc)) <= 1
    /\ ApplyUniqueness

ValidReduceApplyQuorums ==
    /\ \A certificate \in parameterQCs :
        /\ Cardinality(certificate.signers) >= QuorumSize
        /\ certificate.signers
            \subseteq ParameterSigners(certificate.body)
    /\ \A certificate \in aggregateRootQCs :
        /\ Cardinality(certificate.signers) >= QuorumSize
        /\ certificate.signers
            \subseteq AggregateSigners(certificate.body)
    /\ \A certificate \in applyQCs :
        /\ Cardinality(certificate.signers) >= QuorumSize
        /\ certificate.signers \subseteq ApplySigners(certificate.body)

=============================================================================
