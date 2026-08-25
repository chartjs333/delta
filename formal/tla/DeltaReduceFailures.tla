------------------------ MODULE DeltaReduceFailures ------------------------
EXTENDS DeltaReduceReduceApply

FailureInit ==
    /\ crashCoverage = {}
    /\ partition = {}
    /\ view = 0
    /\ logicalTime = 0
    /\ timeoutObservations = {}
    /\ timeoutVotes = {}
    /\ viewChangeQCs = {}
    /\ abortVotes = {}
    /\ abortQCs = {}
    /\ phase = "ACTIVE"
    /\ abortReason = "NO_ABORT"

IsViewChangeBody(body) ==
    /\ body.round \in RoundContexts
    /\ body.fromView \in Views
    /\ body.toView \in Views
    /\ body.softDeadline \in 0..MaxLogicalTime

IsViewChangeVote(vote) ==
    /\ vote.validator \in Validators
    /\ IsViewChangeBody(vote.body)

IsViewChangeQC(certificate) ==
    /\ IsViewChangeBody(certificate.body)
    /\ certificate.signers \subseteq Validators

IsAbortBody(body) ==
    /\ body.round \in RoundContexts
    /\ body.validatorEpoch \in ValidatorEpochs
    /\ body.view \in Views
    /\ body.configs \subseteq ConfigBodies
    /\ body.hardDeadline \in 0..MaxLogicalTime
    /\ body.parentCheckpoint \in CheckpointIds
    /\ body.reason \in AbortReasons \ {"NO_ABORT"}

IsAbortVote(vote) ==
    /\ vote.validator \in Validators
    /\ IsAbortBody(vote.body)

IsAbortQC(certificate) ==
    /\ IsAbortBody(certificate.body)
    /\ certificate.signers \subseteq Validators

FailureTypeOK ==
    /\ crashCoverage \subseteq CrashPoints
    /\ partition \subseteq Validators
    /\ view \in Views
    /\ logicalTime \in 0..MaxLogicalTime
    /\ timeoutObservations \subseteq TimeoutObservationRecords
    /\ \A vote \in timeoutVotes : IsViewChangeVote(vote)
    /\ \A certificate \in viewChangeQCs :
        IsViewChangeQC(certificate)
    /\ \A vote \in abortVotes : IsAbortVote(vote)
    /\ \A certificate \in abortQCs : IsAbortQC(certificate)
    /\ phase \in PhaseValues
    /\ abortReason \in AbortReasons

DownstreamVariablesUnchanged ==
    UNCHANGED <<TicketVariables, AvailabilityVariables,
                CertificateVariables, ReduceApplyVariables>>

VotesBy(validator, votes) ==
    {vote \in votes : vote.validator = validator}

CrashAt(validator, point) ==
    /\ EnableFailures
    /\ validator \in alive
    /\ point \in CrashPoints
    /\ alive' = alive \ {validator}
    /\ recoveryState' =
        [recoveryState EXCEPT ![validator] = "CRASHED"]
    /\ volatileVotes' =
        {vote \in volatileVotes : vote.validator # validator}
    /\ crashCoverage' = crashCoverage \cup {point}
    /\ UNCHANGED <<proposals, byzantine, durableVotes, messages,
                    messageMultiplicity, receivedVotes,
                    finalizedCertificates, durableSequence,
                    FailureControlVariables>>
    /\ DownstreamVariablesUnchanged

CrashBeforePersistKind(validator, kind) ==
    /\ kind \in VoteKinds
    /\ ~\E vote \in VotesBy(validator, durableVotes) :
        vote.kind = kind
    /\ CrashAt(validator, "BEFORE_PERSIST")

CrashBeforePersist(validator) ==
    \E kind \in VoteKinds : CrashBeforePersistKind(validator, kind)

CrashAfterPersistKind(validator, kind) ==
    /\ kind \in VoteKinds
    /\ \E vote \in VotesBy(validator, durableVotes) :
        /\ vote.kind = kind
        /\ vote \notin messages \cup receivedVotes
    /\ CrashAt(validator, "AFTER_PERSIST")

CrashAfterPersist(validator) ==
    \E kind \in VoteKinds : CrashAfterPersistKind(validator, kind)

CrashAfterSendKind(validator, kind) ==
    /\ kind \in VoteKinds
    /\ \E vote \in VotesBy(validator, messages \cup receivedVotes) :
        vote.kind = kind
    /\ CrashAt(validator, "AFTER_SEND")

CrashAfterSend(validator) ==
    \E kind \in VoteKinds : CrashAfterSendKind(validator, kind)

Crash(validator) ==
    \/ CrashBeforePersist(validator)
    \/ CrashAfterPersist(validator)
    \/ CrashAfterSend(validator)

Restart(validator) ==
    /\ EnableFailures
    /\ validator \notin alive
    /\ recoveryState[validator] = "CRASHED"
    /\ alive' = alive \cup {validator}
    /\ recoveryState' =
        [recoveryState EXCEPT ![validator] = "RECOVERING"]
    /\ UNCHANGED <<proposals, byzantine, durableVotes, volatileVotes,
                    messages, messageMultiplicity, receivedVotes,
                    finalizedCertificates, durableSequence,
                    crashCoverage, FailureControlVariables>>
    /\ DownstreamVariablesUnchanged

RecoverJournal(validator) ==
    /\ EnableFailures
    /\ validator \in alive
    /\ recoveryState[validator] = "RECOVERING"
    /\ recoveryState' =
        [recoveryState EXCEPT ![validator] = "READY"]
    /\ volatileVotes' =
        volatileVotes \cup VotesBy(validator, durableVotes)
    /\ UNCHANGED <<proposals, byzantine, durableVotes, messages,
                    messageMultiplicity, receivedVotes,
                    finalizedCertificates, durableSequence, alive,
                    crashCoverage, FailureControlVariables>>
    /\ DownstreamVariablesUnchanged

EnqueueMessage(vote) ==
    /\ EnableNetworkFaults
    /\ SendVoteEnvelope(vote)

DeliverMessage(vote, copy) ==
    /\ EnableNetworkFaults
    /\ DeliverVoteEnvelope(vote, copy)

DropMessage(vote, copy) ==
    /\ EnableNetworkFaults
    /\ DropVoteEnvelope(vote, copy)

DuplicateMessage(vote) ==
    /\ EnableNetworkFaults
    /\ vote \in messages
    /\ Cardinality(MessageCopiesFor(vote)) < MaxMessageCopies
    /\ \E copy \in 1..MaxMessageCopies :
        /\ copy \notin MessageCopiesFor(vote)
        /\ messageMultiplicity' =
            messageMultiplicity \cup {MessageCopy(vote, copy)}
    /\ UNCHANGED <<proposals, byzantine, durableVotes, volatileVotes,
                    messages, receivedVotes, finalizedCertificates,
                    durableSequence, alive, recoveryState, crashCoverage,
                    FailureControlVariables>>
    /\ DownstreamVariablesUnchanged

EnablePartition(validator) ==
    /\ EnablePartitionActions
    /\ validator \in Validators \ partition
    /\ partition' = partition \cup {validator}
    /\ UNCHANGED <<QuorumVariables, crashCoverage, view, logicalTime,
                    timeoutObservations, timeoutVotes, viewChangeQCs,
                    abortVotes, abortQCs, phase, abortReason>>
    /\ DownstreamVariablesUnchanged

HealPartition(validator) ==
    /\ EnablePartitionActions
    /\ validator \in partition
    /\ partition' = partition \ {validator}
    /\ UNCHANGED <<QuorumVariables, crashCoverage, view, logicalTime,
                    timeoutObservations, timeoutVotes, viewChangeQCs,
                    abortVotes, abortQCs, phase, abortReason>>
    /\ DownstreamVariablesUnchanged

AdvanceLogicalTime ==
    /\ EnableTimeoutActions
    /\ phase = "ACTIVE"
    /\ logicalTime < MaxLogicalTime
    /\ logicalTime' = logicalTime + 1
    /\ phase' =
        IF logicalTime + 1 >= HardDeadline THEN "ABORTING" ELSE phase
    /\ UNCHANGED <<QuorumVariables, crashCoverage, partition, view,
                    timeoutObservations, timeoutVotes, viewChangeQCs,
                    abortVotes, abortQCs, abortReason>>
    /\ DownstreamVariablesUnchanged

SoftTimeout(round) ==
    LET observation == [round |-> round, view |-> view]
    IN  /\ EnableTimeoutActions
        /\ phase = "ACTIVE"
        /\ round \in RoundContexts
        /\ logicalTime >= SoftDeadline
        /\ logicalTime < HardDeadline
        /\ abortRequests = {}
        /\ view + 1 \in Views
        /\ observation \notin timeoutObservations
        /\ timeoutObservations' = timeoutObservations \cup {observation}
        /\ UNCHANGED <<QuorumVariables, crashCoverage, partition, view,
                        logicalTime, timeoutVotes, viewChangeQCs,
                        abortVotes, abortQCs, phase, abortReason>>
        /\ DownstreamVariablesUnchanged

ViewChangeBody(round, fromView, toView) ==
    [round |-> round, fromView |-> fromView, toView |-> toView,
     softDeadline |-> SoftDeadline]

ViewChangeVoteRecord(validator, body) ==
    [validator |-> validator, body |-> body]

ViewChangeSigners(body) ==
    {validator \in Validators :
        HasDeliveredVote(validator, "VIEW_CHANGE", body)}

HasConflictingViewChangeVote(validator, body) ==
    \E vote \in timeoutVotes :
        /\ vote.validator = validator
        /\ vote.body.round = body.round
        /\ vote.body.fromView = body.fromView
        /\ vote.body # body

VoteViewChange(validator, body) ==
    LET vote == ViewChangeVoteRecord(validator, body)
        envelope ==
            VoteEnvelope(validator, "VIEW_CHANGE",
                [round |-> body.round, fromView |-> body.fromView], body)
        observation ==
            [round |-> body.round, view |-> body.fromView]
    IN  /\ EnableTimeoutActions
        /\ validator \in Validators
        /\ IsViewChangeBody(body)
        /\ phase = "ACTIVE"
        /\ logicalTime < HardDeadline
        /\ abortRequests = {}
        /\ body.fromView = view
        /\ body.toView = view + 1
        /\ body.softDeadline = SoftDeadline
        /\ observation \in timeoutObservations
        /\ CanPersistVoteEnvelope(envelope)
        /\ vote \notin timeoutVotes
        /\ \/ validator \in byzantine
           \/ ~HasConflictingViewChangeVote(validator, body)
        /\ PersistVoteEnvelopeChanges(envelope)
        /\ timeoutVotes' = timeoutVotes \cup {vote}
        /\ UNCHANGED <<proposals, byzantine, messages,
                        messageMultiplicity, receivedVotes,
                        finalizedCertificates, alive, recoveryState,
                        crashCoverage, partition, view,
                        logicalTime, timeoutObservations, viewChangeQCs,
                        abortVotes, abortQCs, phase, abortReason>>
        /\ DownstreamVariablesUnchanged

FinalizeViewChange(body) ==
    LET signers == ViewChangeSigners(body)
        certificate == [body |-> body, signers |-> signers]
    IN  /\ EnableTimeoutActions
        /\ IsViewChangeBody(body)
        /\ phase = "ACTIVE"
        /\ logicalTime < HardDeadline
        /\ abortRequests = {}
        /\ body.fromView = view
        /\ body.toView = view + 1
        /\ Cardinality(signers) >= QuorumSize
        /\ certificate \notin viewChangeQCs
        /\ view' = body.toView
        /\ viewChangeQCs' = viewChangeQCs \cup {certificate}
        /\ UNCHANGED <<QuorumVariables, crashCoverage, partition,
                        logicalTime, timeoutObservations, timeoutVotes,
                        abortVotes, abortQCs, phase, abortReason>>
        /\ DownstreamVariablesUnchanged

RoundConfigBodies(round) ==
    {certificate.body : certificate \in
        {candidate \in finalizedCertificates :
            /\ candidate.context.height = round.height
            /\ candidate.context.epoch = round.epoch}}

RoundLineage(round) ==
    [isc |-> FinalizedISCBodiesFor(round),
     ec |-> {body \in FinalizedECBodies : body.isc.round = round},
     apc |-> {body \in FinalizedAPCBodies : body.isc.round = round},
     parameter |->
        {body \in FinalizedParameterBodies : body.round = round},
     aggregate |->
        {body \in FinalizedAggregateBodies : body.round = round},
     apply |-> {body \in FinalizedApplyBodies : body.round = round}]

AbortBody(round) ==
    [round |-> round,
     validatorEpoch |-> round.epoch,
     view |-> view,
     configs |-> RoundConfigBodies(round),
     hardDeadline |-> HardDeadline,
     parentCheckpoint |-> currentCheckpoint,
     lineage |-> RoundLineage(round),
     reason |-> ConfiguredAbortReason]

AbortEnabled(round) ==
    /\ {body \in FinalizedApplyBodies : body.round = round} = {}
    /\ \/ logicalTime >= HardDeadline
       \/ \E request \in abortRequests :
            /\ request.round = round
            /\ request.reason = ConfiguredAbortReason

AbortVoteRecord(validator, body) ==
    [validator |-> validator, body |-> body]

AbortSigners(body) ==
    {validator \in Validators :
        HasDeliveredVote(validator, "ABORT", body)}

HasConflictingAbortVote(validator, body) ==
    \E vote \in abortVotes :
        /\ vote.validator = validator
        /\ vote.body.round = body.round
        /\ vote.body # body

VoteHardAbort(validator, body) ==
    LET vote == AbortVoteRecord(validator, body)
        envelope == VoteEnvelope(validator, "ABORT", body.round, body)
    IN  /\ EnableTimeoutActions
        /\ validator \in Validators
        /\ IsAbortBody(body)
        /\ phase \in {"ACTIVE", "ABORTING"}
        /\ body = AbortBody(body.round)
        /\ AbortEnabled(body.round)
        /\ CanPersistVoteEnvelope(envelope)
        /\ vote \notin abortVotes
        /\ \/ validator \in byzantine
           \/ ~HasConflictingAbortVote(validator, body)
        /\ PersistVoteEnvelopeChanges(envelope)
        /\ abortVotes' = abortVotes \cup {vote}
        /\ UNCHANGED <<proposals, byzantine, messages,
                        messageMultiplicity, receivedVotes,
                        finalizedCertificates, alive, recoveryState,
                        crashCoverage, partition, view,
                        logicalTime, timeoutObservations, timeoutVotes,
                        viewChangeQCs, abortQCs, phase, abortReason>>
        /\ DownstreamVariablesUnchanged

HardAbort(body) ==
    LET signers == AbortSigners(body)
        certificate == [body |-> body, signers |-> signers]
    IN  /\ EnableTimeoutActions
        /\ IsAbortBody(body)
        /\ phase \in {"ACTIVE", "ABORTING"}
        /\ body = AbortBody(body.round)
        /\ AbortEnabled(body.round)
        /\ Cardinality(signers) >= QuorumSize
        /\ abortQCs = {}
        /\ abortQCs' = {certificate}
        /\ phase' = "ABORTED"
        /\ abortReason' = body.reason
        /\ UNCHANGED <<QuorumVariables, crashCoverage, partition, view,
                        logicalTime, timeoutObservations, timeoutVotes,
                        viewChangeQCs, abortVotes>>
        /\ DownstreamVariablesUnchanged

CrashBeforePersistAction ==
    \E validator \in Validators : CrashBeforePersist(validator)

CrashAfterPersistAction ==
    \E validator \in Validators : CrashAfterPersist(validator)

CrashAfterSendAction ==
    \E validator \in Validators : CrashAfterSend(validator)

RestartAction ==
    \E validator \in Validators : Restart(validator)

RecoverJournalAction ==
    \E validator \in Validators : RecoverJournal(validator)

EnqueueMessageAction ==
    \E vote \in volatileVotes : EnqueueMessage(vote)

DeliverMessageAction ==
    \E vote \in messages, copy \in 1..MaxMessageCopies :
        DeliverMessage(vote, copy)

DropMessageAction ==
    \E vote \in messages, copy \in 1..MaxMessageCopies :
        DropMessage(vote, copy)

DuplicateMessageAction ==
    \E vote \in messages : DuplicateMessage(vote)

EnablePartitionAction ==
    \E validator \in Validators : EnablePartition(validator)

HealPartitionAction ==
    \E validator \in Validators : HealPartition(validator)

SoftTimeoutAction ==
    \E round \in RoundContexts : SoftTimeout(round)

VoteViewChangeAction ==
    \E round \in RoundContexts :
        \E validator \in Validators :
            VoteViewChange(
                validator, ViewChangeBody(round, view, view + 1))

ViewChangeAction ==
    \E body \in {vote.body : vote \in timeoutVotes} :
        FinalizeViewChange(body)

VoteHardAbortAction ==
    \E round \in RoundContexts :
        \E validator \in Validators :
            VoteHardAbort(validator, AbortBody(round))

HardAbortAction ==
    \E body \in {vote.body : vote \in abortVotes} : HardAbort(body)

FailureNext ==
    \/ CrashBeforePersistAction
    \/ CrashAfterPersistAction
    \/ CrashAfterSendAction
    \/ RestartAction
    \/ RecoverJournalAction
    \/ EnqueueMessageAction
    \/ DeliverMessageAction
    \/ DropMessageAction
    \/ DuplicateMessageAction
    \/ EnablePartitionAction
    \/ HealPartitionAction
    \/ AdvanceLogicalTime
    \/ SoftTimeoutAction
    \/ VoteViewChangeAction
    \/ ViewChangeAction
    \/ VoteHardAbortAction
    \/ HardAbortAction

RecoveryOrdering ==
    \A validator \in Validators :
        /\ (recoveryState[validator] = "CRASHED")
            <=> (validator \notin alive)
        /\ recoveryState[validator] = "READY"
            => VotesBy(validator, durableVotes)
                \subseteq VotesBy(validator, volatileVotes)
        /\ recoveryState[validator] # "READY"
            => VotesBy(validator, volatileVotes) = {}

DurableSequenceExact ==
    \A validator \in Validators :
        durableSequence[validator]
            = Cardinality(VotesBy(validator, durableVotes))

MessageMultisetConsistent ==
    messages = {copy.vote : copy \in messageMultiplicity}

\* Domain vote sets are durable journal projections.  A certificate signer
\* is computed separately from receivedVotes, so persistence alone never
\* creates quorum power.
AllQCVotesPersisted ==
    /\ \A vote \in iscVotes :
        VoteEnvelope(vote.validator, "ISC", vote.body.round, vote.body)
            \in durableVotes
    /\ \A vote \in ecVotes :
        VoteEnvelope(vote.validator, "EC", vote.body.isc, vote.body)
            \in durableVotes
    /\ \A vote \in apcVotes :
        VoteEnvelope(vote.validator, "APC", vote.body.ec, vote.body)
            \in durableVotes
    /\ \A vote \in parameterVotes :
        VoteEnvelope(
            vote.validator, "PARAMETER",
            ParameterKey(vote.body.domain, vote.body.shard), vote.body)
            \in durableVotes
    /\ \A vote \in aggregateVotes :
        VoteEnvelope(
            vote.validator, "AGGREGATE_ROOT", vote.body.apc, vote.body)
            \in durableVotes
    /\ \A vote \in applyVotes :
        VoteEnvelope(
            vote.validator, "APPLY", vote.body.aggregate, vote.body)
            \in durableVotes
    /\ \A vote \in timeoutVotes :
        VoteEnvelope(
            vote.validator, "VIEW_CHANGE",
            [round |-> vote.body.round,
             fromView |-> vote.body.fromView], vote.body)
            \in durableVotes
    /\ \A vote \in abortVotes :
        VoteEnvelope(vote.validator, "ABORT", vote.body.round, vote.body)
            \in durableVotes

ViewChangeVoteUniqueness ==
    \A validator \in Validators \ byzantine,
       round \in RoundContexts, fromView \in Views :
        Cardinality(
            {vote.body : vote \in
                {candidate \in timeoutVotes :
                    /\ candidate.validator = validator
                    /\ candidate.body.round = round
                    /\ candidate.body.fromView = fromView}}) <= 1

ViewChangeCertified ==
    \A certificate \in viewChangeQCs :
        /\ Cardinality(certificate.signers) >= QuorumSize
        /\ certificate.signers
            \subseteq ViewChangeSigners(certificate.body)
        /\ certificate.body.toView = certificate.body.fromView + 1

ViewChangeQCUniqueness ==
    \A round \in RoundContexts, fromView \in Views :
        Cardinality(
            {certificate.body : certificate \in
                {candidate \in viewChangeQCs :
                    /\ candidate.body.round = round
                    /\ candidate.body.fromView = fromView}}) <= 1

AbortVoteUniqueness ==
    \A validator \in Validators \ byzantine,
       round \in RoundContexts :
        Cardinality(
            {vote.body : vote \in
                {candidate \in abortVotes :
                    /\ candidate.validator = validator
                    /\ candidate.body.round = round}}) <= 1

AbortCertified ==
    /\ phase = "ABORTED" => abortQCs # {}
    /\ Cardinality(abortQCs) <= 1
    /\ \A certificate \in abortQCs :
        /\ Cardinality(certificate.signers) >= QuorumSize
        /\ certificate.signers \subseteq AbortSigners(certificate.body)
        /\ certificate.body.reason = abortReason

AbortPreservesParent ==
    \A certificate \in abortQCs :
        /\ certificate.body.parentCheckpoint = currentCheckpoint
        /\ currentCheckpoint = InitialCurrentCheckpoint

NoProgressPastHardDeadline ==
    logicalTime >= HardDeadline => phase \in {"ABORTING", "ABORTED"}

LegalTerminal == phase \in {"APPLIED", "ABORTED"}

=============================================================================
