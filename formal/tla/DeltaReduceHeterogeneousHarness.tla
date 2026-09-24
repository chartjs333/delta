---------------- MODULE DeltaReduceHeterogeneousHarness ----------------
EXTENDS DeltaReducePhase6Harness
CONSTANT HeterogeneousCase
VARIABLE heteroStep

\* Pinned finite native inputs, not expected-result constants. Domain 1 has
\* weights 1/2, 1/3 and 0; domain 2 has weight 1. Each shard has one coordinate.
HeterogeneousInputs ==
    [ZeroArithmeticInputs EXCEPT
        !.ticketOrder = <<1, 2, 3, 4>>, !.domainOrder = <<1, 2>>,
        !.ticketDomain = [ticket \in Tickets |-> IF ticket = 3 THEN 2 ELSE 1],
        !.weightN = [ticket \in Tickets |-> IF ticket = 4 /\ HeterogeneousCase # "PREFIX" THEN 0 ELSE 1],
        !.weightD = [ticket \in Tickets |-> CASE ticket = 1 -> 2 [] ticket = 2 -> 3 [] ticket = 4 /\ HeterogeneousCase = "PREFIX" -> 6 [] OTHER -> 1],
        !.denominator = [domain \in Domains |-> IF domain = 1 THEN 6 ELSE 1],
        !.q = [ticket \in Tickets |-> [shard \in Shards |->
            CASE ticket = 3 -> IF shard = 1 THEN -1 ELSE -3
              [] ticket = 4 -> IF HeterogeneousCase = "PREFIX" /\ shard = 1 THEN -40 ELSE 0
              [] shard = 2 -> IF ticket = 1 THEN 2 ELSE 5
              [] HeterogeneousCase = "PREFIX" -> IF ticket = 1 THEN 40 ELSE 4
              [] HeterogeneousCase = "PRODUCT" -> IF ticket = 1 THEN -40 ELSE 80
              [] OTHER -> IF ticket = 1 THEN 1 ELSE 0]],
        !.qN = [domain \in Domains |-> [shard \in Shards |-> IF HeterogeneousCase = "CONVERSION" /\ domain = 1 /\ shard = 1 THEN 50 ELSE 1]],
        !.qD = [domain \in Domains |-> [shard \in Shards |-> IF domain = 1 THEN 1 ELSE 2]],
        !.piN = [domain \in Domains |-> IF domain = 1 THEN 2 ELSE 1],
        !.piD = [domain \in Domains |-> 3], !.mixtureD = 3,
        !.model = [shard \in Shards |-> IF shard = 1 THEN 20 ELSE -20],
        !.optimizer = [shard \in Shards |-> IF shard = 1 THEN 2 ELSE -2]]

HeteroParameterValues == {-3, -1, 0, 3, 16, 40, 88}

HeteroKeys == <<[domain |-> 1, shard |-> 1], [domain |-> 1, shard |-> 2],
                [domain |-> 2, shard |-> 1], [domain |-> 2, shard |-> 2]>>
HeteroBody(index) ==
    LET key == HeteroKeys[index]
    IN ParameterResultBody(HarnessAPC, key.domain, key.shard,
        ConfiguredParentCheckpoint, ConfiguredParameterSchema, ConfiguredArithmeticProfile,
        NativeParameterValue(HarnessAPC, key.domain, key.shard), TRUE)
HeteroRoot == AggregateRootBody(HarnessAPC, {HeteroBody(i) : i \in 1..4})
HeteroApply == ApplyBody(HeteroRoot, ConfiguredParentCheckpoint, ConfiguredApplyProfile,
    ExpectedNextCheckpoint, NativeModelHash(HeteroRoot), NativeOptimizerHash(HeteroRoot), TRUE)
HeteroSigners == <<1, 2, 3>>
HeteroQuorum(offset, kind, key, body) ==
    LET index == (heteroStep - offset) \div 3 + 1
        substep == (heteroStep - offset) % 3
        validator == HeteroSigners[index]
        envelope == VoteEnvelope(validator, kind, key, body)
    IN CASE substep = 1 -> SendVoteEnvelope(envelope)
         [] substep = 2 -> DeliverVoteEnvelope(envelope, 1)
         [] kind = "PARAMETER" -> VoteParameter(validator, body)
         [] kind = "AGGREGATE_ROOT" -> VoteAggregateRoot(validator, body)
         [] OTHER -> VoteApply(validator, body)
HeteroInit ==
    /\ Tickets = {1, 2, 3, 4} /\ Domains = {1, 2} /\ Shards = {1, 2}
    /\ Validators = {1, 2, 3, 4} /\ F = 1
    /\ HeterogeneousCase \in {"POSITIVE", "PREFIX", "PRODUCT", "CONVERSION"}
    /\ Phase6Init /\ heteroStep = 0
HeteroParameters ==
    /\ heteroStep \in 0..43
    /\ LET index == heteroStep \div 11 + 1
           stage == heteroStep % 11
           body == HeteroBody(index)
       IN CASE stage = 0 -> ProposeParameterResult(body)
            [] stage = 10 -> FinalizeParameterQC(body)
            [] OTHER -> HeteroQuorum((index - 1) * 11 + 1, "PARAMETER", HeteroKeys[index], body)
    /\ heteroStep' = heteroStep + 1
HeteroAssemble ==
    /\ heteroStep = 44 /\ AssembleAggregateRoot(HeteroRoot) /\ heteroStep' = 45
HeteroAggregateQuorum ==
    /\ heteroStep \in 45..53 /\ HeteroQuorum(45, "AGGREGATE_ROOT", HarnessAPC, HeteroRoot)
    /\ heteroStep' = heteroStep + 1
HeteroAggregateFinalize ==
    /\ heteroStep = 54 /\ FinalizeAggregateRootQC(HeteroRoot) /\ heteroStep' = 55
HeteroCompute ==
    /\ heteroStep = 55 /\ ComputeApplyCandidate(HeteroApply) /\ heteroStep' = 56
HeteroApplyQuorum ==
    /\ heteroStep \in 56..64 /\ HeteroQuorum(56, "APPLY", HeteroRoot, HeteroApply)
    /\ heteroStep' = heteroStep + 1
HeteroApplyFinalize ==
    /\ heteroStep = 65 /\ FinalizeApplyQC(HeteroApply) /\ heteroStep' = 66
HeteroAdvance ==
    /\ heteroStep = 66 /\ AdvanceCurrentCheckpoint(HeteroApply) /\ heteroStep' = 67
HeteroCrash ==
    /\ heteroStep = 67 /\ CrashBeforePersistKind(4, "APPLY") /\ heteroStep' = 68
HeteroRestart ==
    /\ heteroStep = 68 /\ Restart(4) /\ heteroStep' = 69
HeteroRecover ==
    /\ heteroStep = 69 /\ RecoverJournal(4) /\ heteroStep' = 70
HeteroReplay ==
    /\ heteroStep = 70 /\ ReplayCurrentAdvance(HeteroApply) /\ heteroStep' = 71
\* A probe can finish without changing production state. An incorrectly enabled
\* production transition remains a separate branch and violates the invariant.
HeteroBlockedProbe ==
    /\ \/ HeterogeneousCase \in {"PREFIX", "PRODUCT"} /\ heteroStep = 0
       \/ HeterogeneousCase = "CONVERSION" /\ heteroStep = 55
    /\ UNCHANGED ProtocolVariables /\ heteroStep' = 71
HeteroNext ==
    \/ HeteroParameters \/ HeteroAssemble \/ HeteroAggregateQuorum \/ HeteroAggregateFinalize
    \/ HeteroCompute \/ HeteroApplyQuorum \/ HeteroApplyFinalize \/ HeteroAdvance
    \/ HeteroCrash \/ HeteroRestart \/ HeteroRecover \/ HeteroReplay \/ HeteroBlockedProbe
HeterogeneousSpec == HeteroInit /\ [][HeteroNext]_<<ProtocolVariables, heteroStep>>

\* Independent literal oracle for this frozen fixture. Do not reuse the
\* production arithmetic to calculate an invariant's expected output.
HeterogeneousExpected ==
    /\ HeterogeneousCase = "POSITIVE" =>
        /\ \A body \in parameterResults :
            body.value = (IF body.domain = 1 THEN IF body.shard = 1 THEN 3 ELSE 16 ELSE IF body.shard = 1 THEN -1 ELSE -3)
        /\ \A body \in applyCandidates :
            /\ body.nextModelHash.values = [shard \in Shards |-> IF shard = 1 THEN 19 ELSE -22]
            /\ body.nextOptimizerHash.values = [shard \in Shards |-> IF shard = 1 THEN 2 ELSE 1]
    /\ HeterogeneousCase \in {"PREFIX", "PRODUCT"} =>
        /\ parameterResults = {} /\ parameterVotes = {} /\ parameterQCs = {}
        /\ durableSequence = [validator \in Validators |-> 4]
    /\ HeterogeneousCase = "CONVERSION" =>
        /\ applyCandidates = {} /\ applyVotes = {} /\ applyQCs = {}
        /\ currentCheckpoint = InitialCurrentCheckpoint
    /\ heteroStep = 71 /\ HeterogeneousCase = "POSITIVE" =>
        /\ currentCheckpoint = ExpectedNextCheckpoint
        /\ currentReplayReceipts = {HeteroApply}

=============================================================================
