---------------------- MODULE DeltaReduceCertificates ----------------------
EXTENDS DeltaReduceAvailability

CertificateInit ==
    /\ closedInputBodies = {}
    /\ iscVotes = {}
    /\ inputSetCertificates = {}
    /\ seedTranscripts = {}
    /\ ecVotes = {}
    /\ eligibilityCertificates = {}
    /\ apcVotes = {}
    /\ aggregationPlanCertificates = {}
    /\ certificateRejections = {}
    /\ certificateReplayReceipts = {}
    /\ abortRequests = {}

IsInputSetBody(body) == body \in InputSetBodies

IsSeedTranscript(seed) ==
    /\ seed.isc \in InputSetBodies
    /\ seed.epoch \in ValidatorEpochs
    /\ seed.value \in SeedValues

IsEligibilityBody(body) ==
    /\ IsInputSetBody(body.isc)
    /\ IsSeedTranscript(body.seed)
    /\ body.members \subseteq Tickets
    /\ body.normEvidence \in NormEvidenceValues

IsAggregationPlanBody(body) ==
    /\ IsInputSetBody(body.isc)
    /\ IsSeedTranscript(body.seed)
    /\ IsEligibilityBody(body.ec)
    /\ body.members \subseteq Tickets
    /\ body.coefficientProfile \in CoefficientProfiles

CertificateTypeOK ==
    /\ \A body \in closedInputBodies : IsInputSetBody(body)
    /\ \A vote \in iscVotes :
        /\ vote.validator \in Validators
        /\ IsInputSetBody(vote.body)
    /\ \A certificate \in inputSetCertificates :
        /\ IsInputSetBody(certificate.body)
        /\ certificate.signers \subseteq Validators
    /\ \A seed \in seedTranscripts : IsSeedTranscript(seed)
    /\ \A vote \in ecVotes :
        /\ vote.validator \in Validators
        /\ IsEligibilityBody(vote.body)
    /\ \A certificate \in eligibilityCertificates :
        /\ IsEligibilityBody(certificate.body)
        /\ certificate.signers \subseteq Validators
    /\ \A vote \in apcVotes :
        /\ vote.validator \in Validators
        /\ IsAggregationPlanBody(vote.body)
    /\ \A certificate \in aggregationPlanCertificates :
        /\ IsAggregationPlanBody(certificate.body)
        /\ certificate.signers \subseteq Validators
    /\ certificateRejections \subseteq CertificateRejectionRecords
    /\ Cardinality(certificateRejections)
        <= MaxModeledCertificateRejections
    /\ certificateReplayReceipts \subseteq CertificateReplayRecords
    /\ Cardinality(certificateReplayReceipts)
        <= MaxModeledCertificateRejections
    /\ abortRequests \subseteq AbortRequestRecords

BaseVariablesUnchanged ==
    UNCHANGED <<QuorumVariables, crashCoverage, TicketVariables,
                AvailabilityVariables, ReduceApplyVariables,
                FailureControlVariables>>

RoundContext(height, epoch) == [height |-> height, epoch |-> epoch]

FinalizedRoundConfig(round, config) ==
    \E certificate \in finalizedCertificates :
        /\ certificate.context =
            ConfigContext(round.height, round.epoch)
        /\ certificate.body = config

CanonicalEligibleEntries ==
    {certificate \in availabilityCertificates :
        /\ certificate.ticket \in RequiredTickets
        /\ HasCompleteAvailability(
            certificate.ticket, certificate.content)}

RequiredInputComplete ==
    \A ticket \in RequiredTickets :
        \E entry \in CanonicalEligibleEntries : entry.ticket = ticket

InputBody(round, config, entries) ==
    [round |-> round,
     config |-> config,
     policy |-> ConfiguredClosePolicy,
     entries |-> entries,
     canonicalRoot |-> entries]

ClosedBodiesFor(round) ==
    {body \in closedInputBodies : body.round = round}

FinalizedISCBodies ==
    {certificate.body : certificate \in inputSetCertificates}

FinalizedISCBodiesFor(round) ==
    {body \in FinalizedISCBodies : body.round = round}

ISCTickets(body) == {entry.ticket : entry \in body.entries}

ISCVoteRecord(validator, body) ==
    [validator |-> validator, body |-> body]

ISCSigners(body) ==
    {validator \in Validators :
        ISCVoteRecord(validator, body) \in iscVotes}

HasConflictingISCVote(validator, body) ==
    \E vote \in iscVotes :
        /\ vote.validator = validator
        /\ vote.body.round = body.round
        /\ vote.body # body

RoundAbortRequired(round) ==
    \E request \in abortRequests : request.round = round

CloseInput(round, config) ==
    LET entries == CanonicalEligibleEntries
        body == InputBody(round, config, entries)
    IN  /\ EnableCertificateActions
        /\ round \in RoundContexts
        /\ config \in ConfigBodies
        /\ CertificateProgressOpen
        /\ FinalizedRoundConfig(round, config)
        /\ \/ ConfiguredClosePolicy = "OMIT_UNAVAILABLE"
           \/ /\ ConfiguredClosePolicy = "ABORT_ON_INCOMPLETE"
              /\ RequiredInputComplete
        /\ closedInputBodies' = closedInputBodies \cup {body}
        /\ UNCHANGED <<iscVotes, inputSetCertificates, seedTranscripts,
                        ecVotes, eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateRejections, certificateReplayReceipts,
                        abortRequests>>
        /\ BaseVariablesUnchanged

RequestIncompleteInputAbort(round, config) ==
    LET request ==
            [round |-> round, reason |-> "INCOMPLETE_INPUT"]
    IN  /\ EnableCertificateActions
        /\ round \in RoundContexts
        /\ config \in ConfigBodies
        /\ CertificateProgressOpen
        /\ ConfiguredClosePolicy = "ABORT_ON_INCOMPLETE"
        /\ FinalizedRoundConfig(round, config)
        /\ ~RequiredInputComplete
        /\ request \notin abortRequests
        /\ abortRequests' = abortRequests \cup {request}
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts, ecVotes,
                        eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateRejections, certificateReplayReceipts>>
        /\ BaseVariablesUnchanged

VoteISC(validator, body) ==
    LET vote == ISCVoteRecord(validator, body)
    IN  /\ EnableCertificateActions
        /\ validator \in Validators
        /\ body \in closedInputBodies
        /\ CanVote(validator)
        /\ ~RoundAbortRequired(body.round)
        /\ vote \notin iscVotes
        /\ \/ validator \in byzantine
           \/ ~HasConflictingISCVote(validator, body)
        /\ iscVotes' = iscVotes \cup {vote}
        /\ UNCHANGED <<closedInputBodies, inputSetCertificates,
                        seedTranscripts, ecVotes, eligibilityCertificates,
                        apcVotes, aggregationPlanCertificates,
                        certificateRejections, certificateReplayReceipts,
                        abortRequests>>
        /\ BaseVariablesUnchanged

FinalizeISC(body) ==
    LET signers == ISCSigners(body)
        certificate == [body |-> body, signers |-> signers]
    IN  /\ EnableCertificateActions
        /\ body \in closedInputBodies
        /\ Cardinality(signers) >= QuorumSize
        /\ FinalizedISCBodiesFor(body.round) = {}
        /\ inputSetCertificates' =
            inputSetCertificates \cup {certificate}
        /\ UNCHANGED <<closedInputBodies, iscVotes, seedTranscripts,
                        ecVotes, eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateRejections, certificateReplayReceipts,
                        abortRequests>>
        /\ BaseVariablesUnchanged

RecordCertificateRejection(rejection) ==
    /\ rejection \in CertificateRejectionRecords
    /\ Cardinality(certificateRejections)
        < MaxModeledCertificateRejections
    /\ rejection \notin certificateRejections
    /\ certificateRejections' = certificateRejections \cup {rejection}

RejectConflictingISC(body) ==
    LET rejection ==
            [kind |-> "ISC", round |-> body.round,
             reason |-> "CONFLICTING_CERTIFICATE"]
    IN  /\ EnableCertificateActions
        /\ EnableCertificateFaults
        /\ body \in InputSetBodies
        /\ FinalizedISCBodiesFor(body.round) # {}
        /\ body \notin FinalizedISCBodiesFor(body.round)
        /\ RecordCertificateRejection(rejection)
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts, ecVotes,
                        eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateReplayReceipts, abortRequests>>
        /\ BaseVariablesUnchanged

SeedRecord(isc, value) ==
    [isc |-> isc, epoch |-> isc.round.epoch, value |-> value]

SeedsForISC(isc) ==
    {seed \in seedTranscripts : seed.isc = isc}

GenerateSeed(isc) ==
    LET seed == SeedRecord(isc, ExpectedSeedValue)
    IN  /\ EnableCertificateActions
        /\ EnablePlanningActions
        /\ isc \in FinalizedISCBodies
        /\ ~RoundAbortRequired(isc.round)
        /\ SeedsForISC(isc) = {}
        /\ seedTranscripts' = seedTranscripts \cup {seed}
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, ecVotes,
                        eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateRejections, certificateReplayReceipts,
                        abortRequests>>
        /\ BaseVariablesUnchanged

RejectEarlySeed(round) ==
    LET rejection ==
            [kind |-> "SEED", round |-> round,
             reason |-> "EARLY_SEED"]
    IN  /\ EnableCertificateActions
        /\ EnablePlanningActions
        /\ EnableCertificateFaults
        /\ round \in RoundContexts
        /\ FinalizedISCBodiesFor(round) = {}
        /\ RecordCertificateRejection(rejection)
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts, ecVotes,
                        eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateReplayReceipts, abortRequests>>
        /\ BaseVariablesUnchanged

RejectWrongSeedParent(isc) ==
    LET rejection ==
            [kind |-> "SEED", round |-> isc.round,
             reason |-> "WRONG_PARENT"]
    IN  /\ EnableCertificateActions
        /\ EnablePlanningActions
        /\ EnableCertificateFaults
        /\ isc \in InputSetBodies
        /\ FinalizedISCBodiesFor(isc.round) # {}
        /\ isc \notin FinalizedISCBodiesFor(isc.round)
        /\ RecordCertificateRejection(rejection)
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts, ecVotes,
                        eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateReplayReceipts, abortRequests>>
        /\ BaseVariablesUnchanged

RejectConflictingSeed(isc, value) ==
    LET rejection ==
            [kind |-> "SEED", round |-> isc.round,
             reason |-> "CONFLICTING_CERTIFICATE"]
    IN  /\ EnableCertificateActions
        /\ EnablePlanningActions
        /\ EnableCertificateFaults
        /\ isc \in FinalizedISCBodies
        /\ value \in SeedValues
        /\ SeedsForISC(isc) # {}
        /\ \A seed \in SeedsForISC(isc) : seed.value # value
        /\ RecordCertificateRejection(rejection)
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts, ecVotes,
                        eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateReplayReceipts, abortRequests>>
        /\ BaseVariablesUnchanged

EligibilityBody(isc, seed, members, evidence) ==
    [isc |-> isc, seed |-> seed, members |-> members,
     normEvidence |-> evidence]

FinalizedECBodies ==
    {certificate.body : certificate \in eligibilityCertificates}

FinalizedECBodiesFor(isc) ==
    {body \in FinalizedECBodies : body.isc = isc}

ValidECParent(body) ==
    /\ body.isc \in FinalizedISCBodies
    /\ body.seed \in seedTranscripts
    /\ body.seed.isc = body.isc

ValidEligibilityBody(body) ==
    /\ ValidECParent(body)
    /\ body.members \subseteq ISCTickets(body.isc)
    /\ body.normEvidence \in ValidNormEvidence
    /\ ~RoundAbortRequired(body.isc.round)

ECVoteRecord(validator, body) ==
    [validator |-> validator, body |-> body]

ECSigners(body) ==
    {validator \in Validators :
        ECVoteRecord(validator, body) \in ecVotes}

HasConflictingECVote(validator, body) ==
    \E vote \in ecVotes :
        /\ vote.validator = validator
        /\ vote.body.isc = body.isc
        /\ vote.body # body

VoteEC(validator, body) ==
    LET vote == ECVoteRecord(validator, body)
    IN  /\ EnableCertificateActions
        /\ EnablePlanningActions
        /\ validator \in Validators
        /\ IsEligibilityBody(body)
        /\ ValidEligibilityBody(body)
        /\ CanVote(validator)
        /\ vote \notin ecVotes
        /\ \/ validator \in byzantine
           \/ ~HasConflictingECVote(validator, body)
        /\ ecVotes' = ecVotes \cup {vote}
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts,
                        eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateRejections, certificateReplayReceipts,
                        abortRequests>>
        /\ BaseVariablesUnchanged

FinalizeEC(body) ==
    LET signers == ECSigners(body)
        certificate == [body |-> body, signers |-> signers]
    IN  /\ EnableCertificateActions
        /\ EnablePlanningActions
        /\ ValidEligibilityBody(body)
        /\ Cardinality(signers) >= QuorumSize
        /\ FinalizedECBodiesFor(body.isc) = {}
        /\ eligibilityCertificates' =
            eligibilityCertificates \cup {certificate}
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts, ecVotes,
                        apcVotes, aggregationPlanCertificates,
                        certificateRejections, certificateReplayReceipts,
                        abortRequests>>
        /\ BaseVariablesUnchanged

RejectInvalidECParent(body) ==
    LET rejection ==
            [kind |-> "EC", round |-> body.isc.round,
             reason |-> "WRONG_PARENT"]
    IN  /\ EnableCertificateActions
        /\ EnablePlanningActions
        /\ EnableCertificateFaults
        /\ EnableFrankensteinFaults
        /\ IsEligibilityBody(body)
        /\ ~ValidECParent(body)
        /\ RecordCertificateRejection(rejection)
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts, ecVotes,
                        eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateReplayReceipts, abortRequests>>
        /\ BaseVariablesUnchanged

RejectECMembership(body) ==
    LET rejection ==
            [kind |-> "EC", round |-> body.isc.round,
             reason |-> "NON_SUBSET_MEMBERSHIP"]
    IN  /\ EnableCertificateActions
        /\ EnablePlanningActions
        /\ EnableCertificateFaults
        /\ EnableFrankensteinFaults
        /\ IsEligibilityBody(body)
        /\ ValidECParent(body)
        /\ ~(body.members \subseteq ISCTickets(body.isc))
        /\ RecordCertificateRejection(rejection)
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts, ecVotes,
                        eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateReplayReceipts, abortRequests>>
        /\ BaseVariablesUnchanged

RejectNormEvidence(body) ==
    LET rejection ==
            [kind |-> "EC", round |-> body.isc.round,
             reason |-> "INVALID_NORM_EVIDENCE"]
    IN  /\ EnableCertificateActions
        /\ EnablePlanningActions
        /\ EnableCertificateFaults
        /\ EnableFrankensteinFaults
        /\ IsEligibilityBody(body)
        /\ ValidECParent(body)
        /\ body.members \subseteq ISCTickets(body.isc)
        /\ body.normEvidence \notin ValidNormEvidence
        /\ RecordCertificateRejection(rejection)
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts, ecVotes,
                        eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateReplayReceipts, abortRequests>>
        /\ BaseVariablesUnchanged

RejectConflictingEC(body) ==
    LET rejection ==
            [kind |-> "EC", round |-> body.isc.round,
             reason |-> "CONFLICTING_CERTIFICATE"]
    IN  /\ EnableCertificateActions
        /\ EnablePlanningActions
        /\ EnableCertificateFaults
        /\ IsEligibilityBody(body)
        /\ FinalizedECBodiesFor(body.isc) # {}
        /\ body \notin FinalizedECBodiesFor(body.isc)
        /\ RecordCertificateRejection(rejection)
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts, ecVotes,
                        eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateReplayReceipts, abortRequests>>
        /\ BaseVariablesUnchanged

AggregationPlanBody(isc, seed, ec, members, profile) ==
    [isc |-> isc, seed |-> seed, ec |-> ec, members |-> members,
     coefficientProfile |-> profile]

FinalizedAPCBodies ==
    {certificate.body : certificate \in aggregationPlanCertificates}

FinalizedAPCBodiesFor(ec) ==
    {body \in FinalizedAPCBodies : body.ec = ec}

ValidAPCParent(body) ==
    /\ body.isc \in FinalizedISCBodies
    /\ body.seed \in seedTranscripts
    /\ body.seed.isc = body.isc
    /\ body.ec \in FinalizedECBodies
    /\ body.ec.isc = body.isc
    /\ body.ec.seed = body.seed

ValidAggregationPlanBody(body) ==
    /\ ValidAPCParent(body)
    /\ body.members = body.ec.members
    /\ body.coefficientProfile = ConfiguredCoefficientProfile
    /\ body.coefficientProfile \in SafeCoefficientProfiles
    /\ ~RoundAbortRequired(body.isc.round)

APCVoteRecord(validator, body) ==
    [validator |-> validator, body |-> body]

APCSigners(body) ==
    {validator \in Validators :
        APCVoteRecord(validator, body) \in apcVotes}

HasConflictingAPCVote(validator, body) ==
    \E vote \in apcVotes :
        /\ vote.validator = validator
        /\ vote.body.ec = body.ec
        /\ vote.body # body

VoteAPC(validator, body) ==
    LET vote == APCVoteRecord(validator, body)
    IN  /\ EnableCertificateActions
        /\ EnablePlanningActions
        /\ validator \in Validators
        /\ IsAggregationPlanBody(body)
        /\ ValidAggregationPlanBody(body)
        /\ CanVote(validator)
        /\ vote \notin apcVotes
        /\ \/ validator \in byzantine
           \/ ~HasConflictingAPCVote(validator, body)
        /\ apcVotes' = apcVotes \cup {vote}
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts, ecVotes,
                        eligibilityCertificates,
                        aggregationPlanCertificates,
                        certificateRejections, certificateReplayReceipts,
                        abortRequests>>
        /\ BaseVariablesUnchanged

FinalizeAPC(body) ==
    LET signers == APCSigners(body)
        certificate == [body |-> body, signers |-> signers]
    IN  /\ EnableCertificateActions
        /\ EnablePlanningActions
        /\ ValidAggregationPlanBody(body)
        /\ Cardinality(signers) >= QuorumSize
        /\ FinalizedAPCBodiesFor(body.ec) = {}
        /\ aggregationPlanCertificates' =
            aggregationPlanCertificates \cup {certificate}
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts, ecVotes,
                        eligibilityCertificates, apcVotes,
                        certificateRejections, certificateReplayReceipts,
                        abortRequests>>
        /\ BaseVariablesUnchanged

RejectInvalidAPCParent(body) ==
    LET rejection ==
            [kind |-> "APC", round |-> body.isc.round,
             reason |-> "WRONG_PARENT"]
    IN  /\ EnableCertificateActions
        /\ EnablePlanningActions
        /\ EnableCertificateFaults
        /\ EnableFrankensteinFaults
        /\ IsAggregationPlanBody(body)
        /\ ~ValidAPCParent(body)
        /\ RecordCertificateRejection(rejection)
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts, ecVotes,
                        eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateReplayReceipts, abortRequests>>
        /\ BaseVariablesUnchanged

RejectAPCMembership(body) ==
    LET rejection ==
            [kind |-> "APC", round |-> body.isc.round,
             reason |-> "MEMBERSHIP_REWRITE"]
    IN  /\ EnableCertificateActions
        /\ EnablePlanningActions
        /\ EnableCertificateFaults
        /\ EnableFrankensteinFaults
        /\ IsAggregationPlanBody(body)
        /\ ValidAPCParent(body)
        /\ body.members # body.ec.members
        /\ RecordCertificateRejection(rejection)
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts, ecVotes,
                        eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateReplayReceipts, abortRequests>>
        /\ BaseVariablesUnchanged

RejectWrongCoefficientProfile(body) ==
    LET rejection ==
            [kind |-> "APC", round |-> body.isc.round,
             reason |-> "WRONG_COEFFICIENT_PROFILE"]
    IN  /\ EnableCertificateActions
        /\ EnablePlanningActions
        /\ EnableCertificateFaults
        /\ EnableFrankensteinFaults
        /\ IsAggregationPlanBody(body)
        /\ ValidAPCParent(body)
        /\ body.members = body.ec.members
        /\ body.coefficientProfile # ConfiguredCoefficientProfile
        /\ RecordCertificateRejection(rejection)
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts, ecVotes,
                        eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateReplayReceipts, abortRequests>>
        /\ BaseVariablesUnchanged

RequestUnsafePlanAbort(body) ==
    LET request ==
            [round |-> body.isc.round,
             reason |-> "UNSAFE_COEFFICIENTS"]
    IN  /\ EnableCertificateActions
        /\ EnablePlanningActions
        /\ EnableCertificateFaults
        /\ EnableFrankensteinFaults
        /\ IsAggregationPlanBody(body)
        /\ ValidAPCParent(body)
        /\ body.members = body.ec.members
        /\ body.coefficientProfile = ConfiguredCoefficientProfile
        /\ body.coefficientProfile \notin SafeCoefficientProfiles
        /\ request \notin abortRequests
        /\ abortRequests' = abortRequests \cup {request}
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts, ecVotes,
                        eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateRejections, certificateReplayReceipts>>
        /\ BaseVariablesUnchanged

RejectConflictingAPC(body) ==
    LET rejection ==
            [kind |-> "APC", round |-> body.isc.round,
             reason |-> "CONFLICTING_CERTIFICATE"]
    IN  /\ EnableCertificateActions
        /\ EnablePlanningActions
        /\ EnableCertificateFaults
        /\ IsAggregationPlanBody(body)
        /\ FinalizedAPCBodiesFor(body.ec) # {}
        /\ body \notin FinalizedAPCBodiesFor(body.ec)
        /\ RecordCertificateRejection(rejection)
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts, ecVotes,
                        eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateReplayReceipts, abortRequests>>
        /\ BaseVariablesUnchanged

CertificateExists(kind, round) ==
    \/ /\ kind = "ISC"
       /\ FinalizedISCBodiesFor(round) # {}
    \/ /\ kind = "SEED"
       /\ \E seed \in seedTranscripts : seed.isc.round = round
    \/ /\ kind = "EC"
       /\ \E body \in FinalizedECBodies : body.isc.round = round
    \/ /\ kind = "APC"
       /\ \E body \in FinalizedAPCBodies : body.isc.round = round

ReplayMessage(kind, round) ==
    LET receipt == [kind |-> kind, round |-> round]
    IN  /\ EnableCertificateActions
        /\ EnableCertificateFaults
        /\ kind \in CertificateKinds
        /\ round \in RoundContexts
        /\ CertificateExists(kind, round)
        /\ Cardinality(certificateReplayReceipts)
            < MaxModeledCertificateRejections
        /\ receipt \notin certificateReplayReceipts
        /\ certificateReplayReceipts' =
            certificateReplayReceipts \cup {receipt}
        /\ UNCHANGED <<closedInputBodies, iscVotes,
                        inputSetCertificates, seedTranscripts, ecVotes,
                        eligibilityCertificates, apcVotes,
                        aggregationPlanCertificates,
                        certificateRejections, abortRequests>>
        /\ BaseVariablesUnchanged

CloseInputAction ==
    \E round \in RoundContexts, config \in ConfigBodies :
        CloseInput(round, config)

RequestIncompleteInputAbortAction ==
    \E round \in RoundContexts, config \in ConfigBodies :
        RequestIncompleteInputAbort(round, config)

VoteISCAction ==
    \E validator \in Validators, body \in closedInputBodies :
        VoteISC(validator, body)

FinalizeISCAction ==
    \E body \in closedInputBodies : FinalizeISC(body)

RejectConflictingISCAction ==
    \E body \in InputSetBodies : RejectConflictingISC(body)

GenerateSeedAction ==
    \E isc \in FinalizedISCBodies : GenerateSeed(isc)

RejectEarlySeedAction ==
    \E round \in RoundContexts : RejectEarlySeed(round)

RejectWrongSeedParentAction ==
    \E isc \in InputSetBodies : RejectWrongSeedParent(isc)

RejectConflictingSeedAction ==
    \E isc \in FinalizedISCBodies, value \in SeedValues :
        RejectConflictingSeed(isc, value)

VoteECAction ==
    \E validator \in Validators, isc \in FinalizedISCBodies,
       seed \in seedTranscripts, members \in SUBSET Tickets,
       evidence \in NormEvidenceValues :
        VoteEC(validator, EligibilityBody(isc, seed, members, evidence))

FinalizeECAction ==
    \E body \in {vote.body : vote \in ecVotes} : FinalizeEC(body)

RejectInvalidECParentAction ==
    /\ EnableFrankensteinFaults
    /\ \E isc \in InputSetBodies, seed \in seedTranscripts,
          members \in SUBSET Tickets, evidence \in NormEvidenceValues :
        RejectInvalidECParent(
            EligibilityBody(isc, seed, members, evidence))

RejectECMembershipAction ==
    /\ EnableFrankensteinFaults
    /\ \E isc \in FinalizedISCBodies, seed \in seedTranscripts,
          members \in SUBSET Tickets, evidence \in NormEvidenceValues :
        RejectECMembership(
            EligibilityBody(isc, seed, members, evidence))

RejectNormEvidenceAction ==
    /\ EnableFrankensteinFaults
    /\ \E isc \in FinalizedISCBodies, seed \in seedTranscripts,
          members \in SUBSET Tickets, evidence \in NormEvidenceValues :
        RejectNormEvidence(
            EligibilityBody(isc, seed, members, evidence))

RejectConflictingECAction ==
    \E isc \in FinalizedISCBodies, seed \in seedTranscripts,
       members \in SUBSET Tickets, evidence \in NormEvidenceValues :
        RejectConflictingEC(
            EligibilityBody(isc, seed, members, evidence))

VoteAPCAction ==
    \E validator \in Validators, ec \in FinalizedECBodies,
       members \in SUBSET Tickets, profile \in CoefficientProfiles :
        VoteAPC(validator,
            AggregationPlanBody(
                ec.isc, ec.seed, ec, members, profile))

FinalizeAPCAction ==
    \E body \in {vote.body : vote \in apcVotes} : FinalizeAPC(body)

RejectInvalidAPCParentAction ==
    /\ EnableFrankensteinFaults
    /\ \E isc \in InputSetBodies, seed \in seedTranscripts,
          ec \in FinalizedECBodies, members \in SUBSET Tickets,
          profile \in CoefficientProfiles :
        RejectInvalidAPCParent(
            AggregationPlanBody(isc, seed, ec, members, profile))

RejectAPCMembershipAction ==
    /\ EnableFrankensteinFaults
    /\ \E ec \in FinalizedECBodies, members \in SUBSET Tickets,
          profile \in CoefficientProfiles :
        RejectAPCMembership(
            AggregationPlanBody(
                ec.isc, ec.seed, ec, members, profile))

RejectWrongCoefficientProfileAction ==
    /\ EnableFrankensteinFaults
    /\ \E ec \in FinalizedECBodies, members \in SUBSET Tickets,
          profile \in CoefficientProfiles :
        RejectWrongCoefficientProfile(
            AggregationPlanBody(
                ec.isc, ec.seed, ec, members, profile))

RequestUnsafePlanAbortAction ==
    /\ EnableFrankensteinFaults
    /\ \E ec \in FinalizedECBodies, members \in SUBSET Tickets,
          profile \in CoefficientProfiles :
        RequestUnsafePlanAbort(
            AggregationPlanBody(
                ec.isc, ec.seed, ec, members, profile))

RejectConflictingAPCAction ==
    \E ec \in FinalizedECBodies, members \in SUBSET Tickets,
       profile \in CoefficientProfiles :
        RejectConflictingAPC(
            AggregationPlanBody(
                ec.isc, ec.seed, ec, members, profile))

ReplayMessageAction ==
    \E kind \in CertificateKinds, round \in RoundContexts :
        ReplayMessage(kind, round)

CertificateNext ==
    \/ CloseInputAction
    \/ RequestIncompleteInputAbortAction
    \/ VoteISCAction
    \/ FinalizeISCAction
    \/ RejectConflictingISCAction
    \/ GenerateSeedAction
    \/ RejectEarlySeedAction
    \/ RejectWrongSeedParentAction
    \/ RejectConflictingSeedAction
    \/ VoteECAction
    \/ FinalizeECAction
    \/ RejectInvalidECParentAction
    \/ RejectECMembershipAction
    \/ RejectNormEvidenceAction
    \/ RejectConflictingECAction
    \/ VoteAPCAction
    \/ FinalizeAPCAction
    \/ RejectInvalidAPCParentAction
    \/ RejectAPCMembershipAction
    \/ RejectWrongCoefficientProfileAction
    \/ RequestUnsafePlanAbortAction
    \/ RejectConflictingAPCAction
    \/ ReplayMessageAction

ClosedInputWellFormed ==
    \A body \in closedInputBodies :
        /\ body.policy = ConfiguredClosePolicy
        /\ body.canonicalRoot = body.entries
        /\ FinalizedRoundConfig(body.round, body.config)
        /\ \A entry \in body.entries :
            /\ entry.ticket \in RequiredTickets
            /\ entry \in availabilityCertificates
            /\ HasAttestationCoverage(entry.ticket, entry.content)
        /\ body.policy = "ABORT_ON_INCOMPLETE"
            => ISCTickets(body) = RequiredTickets

ISCImmutability ==
    \A round \in RoundContexts :
        /\ Cardinality(ClosedBodiesFor(round)) <= 1
        /\ Cardinality(FinalizedISCBodiesFor(round)) <= 1
        /\ FinalizedISCBodiesFor(round) \subseteq ClosedBodiesFor(round)

SeedAfterInputFreeze ==
    /\ \A seed \in seedTranscripts :
        /\ seed.isc \in FinalizedISCBodies
        /\ seed.epoch = seed.isc.round.epoch
        /\ seed.value = ExpectedSeedValue
    /\ \A isc \in FinalizedISCBodies :
        Cardinality(SeedsForISC(isc)) <= 1

ECSubsetISC ==
    \A certificate \in eligibilityCertificates :
        /\ certificate.body.isc \in FinalizedISCBodies
        /\ certificate.body.seed \in seedTranscripts
        /\ certificate.body.seed.isc = certificate.body.isc
        /\ certificate.body.members
            \subseteq ISCTickets(certificate.body.isc)
        /\ certificate.body.normEvidence \in ValidNormEvidence

APCParentage ==
    \A certificate \in aggregationPlanCertificates :
        /\ certificate.body.isc \in FinalizedISCBodies
        /\ certificate.body.seed \in seedTranscripts
        /\ certificate.body.seed.isc = certificate.body.isc
        /\ certificate.body.ec \in FinalizedECBodies
        /\ certificate.body.ec.isc = certificate.body.isc
        /\ certificate.body.ec.seed = certificate.body.seed
        /\ certificate.body.members = certificate.body.ec.members
        /\ certificate.body.coefficientProfile
            = ConfiguredCoefficientProfile
        /\ certificate.body.coefficientProfile \in SafeCoefficientProfiles

CertificateVoteUniqueness ==
    /\ \A validator \in Validators \ byzantine,
          round \in RoundContexts :
        Cardinality(
            {vote.body : vote \in
                {candidate \in iscVotes :
                    candidate.validator = validator
                    /\ candidate.body.round = round}}) <= 1
    /\ \A validator \in Validators \ byzantine,
          isc \in FinalizedISCBodies :
        Cardinality(
            {vote.body : vote \in
                {candidate \in ecVotes :
                    candidate.validator = validator
                    /\ candidate.body.isc = isc}}) <= 1
    /\ \A validator \in Validators \ byzantine,
          ec \in FinalizedECBodies :
        Cardinality(
            {vote.body : vote \in
                {candidate \in apcVotes :
                    candidate.validator = validator
                    /\ candidate.body.ec = ec}}) <= 1

CertificateQCUniqueness ==
    /\ \A round \in RoundContexts :
        Cardinality(FinalizedISCBodiesFor(round)) <= 1
    /\ \A isc \in FinalizedISCBodies :
        Cardinality(FinalizedECBodiesFor(isc)) <= 1
    /\ \A ec \in FinalizedECBodies :
        Cardinality(FinalizedAPCBodiesFor(ec)) <= 1

ValidCertificateQuorums ==
    /\ \A certificate \in inputSetCertificates :
        /\ Cardinality(certificate.signers) >= QuorumSize
        /\ certificate.signers \subseteq ISCSigners(certificate.body)
    /\ \A certificate \in eligibilityCertificates :
        /\ Cardinality(certificate.signers) >= QuorumSize
        /\ certificate.signers \subseteq ECSigners(certificate.body)
    /\ \A certificate \in aggregationPlanCertificates :
        /\ Cardinality(certificate.signers) >= QuorumSize
        /\ certificate.signers \subseteq APCSigners(certificate.body)

CertificateReplayIdempotence ==
    \A receipt \in certificateReplayReceipts :
        CertificateExists(receipt.kind, receipt.round)

AbortRequestSound ==
    \A request \in abortRequests :
        \/ /\ request.reason = "INCOMPLETE_INPUT"
           /\ ConfiguredClosePolicy = "ABORT_ON_INCOMPLETE"
           /\ ~RequiredInputComplete
        \/ /\ request.reason = "UNSAFE_COEFFICIENTS"
           /\ ConfiguredCoefficientProfile \notin SafeCoefficientProfiles

=============================================================================
