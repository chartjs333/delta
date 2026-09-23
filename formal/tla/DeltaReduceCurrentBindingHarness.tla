-------------------- MODULE DeltaReduceCurrentBindingHarness --------------------
EXTENDS DeltaReducePhase6Harness

\* Focused f=1 suffix, starting with the Phase6 certified upstream premise.
\* Three validators persist/send/deliver each quorum; the fourth arrives only
\* after the production current-pointer transition. No production state is
\* assigned by this harness after Init. Scheduling is intentionally serialized;
\* this is a current-binding regression, not exhaustive lifecycle coverage.
CONSTANT ProbeAfterRecovery
VARIABLE bindingStep

LateValidator == CHOOSE validator \in Validators : TRUE
FirstSigner == CHOOSE validator \in Validators \ {LateValidator} : TRUE
SecondSigner == CHOOSE validator \in Validators \ {LateValidator, FirstSigner} : TRUE
ThirdSigner == CHOOSE validator \in Validators \ {LateValidator, FirstSigner, SecondSigner} : TRUE
BindingSigners == <<FirstSigner, SecondSigner, ThirdSigner>>
BindingShard == CHOOSE shard \in Shards : TRUE

BindingParameter ==
    ParameterResultBody(HarnessAPC, HarnessDomain, BindingShard,
        ConfiguredParentCheckpoint, ConfiguredParameterSchema,
        ConfiguredArithmeticProfile, NativeParameterValue(HarnessAPC, HarnessDomain), TRUE)
BindingRoot == AggregateRootBody(HarnessAPC, {BindingParameter})
BindingApply == ApplyBody(BindingRoot, ConfiguredParentCheckpoint,
    ConfiguredApplyProfile, ExpectedNextCheckpoint,
    NativeModelHash(BindingRoot), NativeOptimizerHash(BindingRoot), TRUE)

BindingEnvelope(validator, kind, key, body) == VoteEnvelope(validator, kind, key, body)
BindingSigner(offset) == BindingSigners[((bindingStep - offset) \div 3) + 1]
BindingSubstep(offset) == (bindingStep - offset) % 3

BindingInit ==
    /\ Cardinality(Validators) = 4 /\ F = 1
    /\ Cardinality(Domains) = 1 /\ Cardinality(Shards) = 1
    /\ InitialCurrentCheckpoint # ExpectedNextCheckpoint
    /\ ProbeAfterRecovery \in BOOLEAN
    /\ Phase6Init
    /\ bindingStep = 0

BindingPropose ==
    /\ bindingStep = 0 /\ ProposeParameterResult(BindingParameter)
    /\ bindingStep' = 1

BindingParameterQuorum ==
    /\ bindingStep \in 1..9
    /\ LET validator == BindingSigner(1)
           envelope == BindingEnvelope(validator, "PARAMETER",
                ParameterKey(HarnessDomain, BindingShard), BindingParameter)
       IN CASE BindingSubstep(1) = 0 -> VoteParameter(validator, BindingParameter)
            [] BindingSubstep(1) = 1 -> SendVoteEnvelope(envelope)
            [] OTHER -> DeliverVoteEnvelope(envelope, 1)
    /\ bindingStep' = bindingStep + 1

BindingParameterFinalize ==
    /\ bindingStep = 10 /\ FinalizeParameterQC(BindingParameter)
    /\ bindingStep' = 11
BindingAssemble ==
    /\ bindingStep = 11 /\ AssembleAggregateRoot(BindingRoot)
    /\ bindingStep' = 12

BindingRootQuorum ==
    /\ bindingStep \in 12..20
    /\ LET validator == BindingSigner(12)
           envelope == BindingEnvelope(validator, "AGGREGATE_ROOT", HarnessAPC, BindingRoot)
       IN CASE BindingSubstep(12) = 0 -> VoteAggregateRoot(validator, BindingRoot)
            [] BindingSubstep(12) = 1 -> SendVoteEnvelope(envelope)
            [] OTHER -> DeliverVoteEnvelope(envelope, 1)
    /\ bindingStep' = bindingStep + 1

BindingRootFinalize ==
    /\ bindingStep = 21 /\ FinalizeAggregateRootQC(BindingRoot)
    /\ bindingStep' = 22
BindingCompute ==
    /\ bindingStep = 22 /\ ComputeApplyCandidate(BindingApply)
    /\ bindingStep' = 23

BindingApplyQuorum ==
    /\ bindingStep \in 23..31
    /\ LET validator == BindingSigner(23)
           envelope == BindingEnvelope(validator, "APPLY", BindingRoot, BindingApply)
       IN CASE BindingSubstep(23) = 0 -> VoteApply(validator, BindingApply)
            [] BindingSubstep(23) = 1 -> SendVoteEnvelope(envelope)
            [] OTHER -> DeliverVoteEnvelope(envelope, 1)
    /\ bindingStep' = bindingStep + 1

BindingApplyFinalize ==
    /\ bindingStep = 32 /\ FinalizeApplyQC(BindingApply)
    /\ bindingStep' = 33
BindingAdvance ==
    /\ bindingStep = 33 /\ AdvanceCurrentCheckpoint(BindingApply)
    /\ bindingStep' = 34
BindingCrash ==
    /\ bindingStep = 34 /\ ProbeAfterRecovery
    /\ CrashBeforePersistKind(LateValidator, "PARAMETER")
    /\ bindingStep' = 35
BindingRestart ==
    /\ bindingStep = 35 /\ Restart(LateValidator)
    /\ bindingStep' = 36
BindingRecover ==
    /\ bindingStep = 36 /\ RecoverJournal(LateValidator)
    /\ bindingStep' = 37

BindingProbeReady == bindingStep = (IF ProbeAfterRecovery THEN 37 ELSE 34)
BindingLateParameter ==
    /\ BindingProbeReady /\ VoteParameter(LateValidator, BindingParameter)
    /\ UNCHANGED bindingStep
BindingLateApply ==
    /\ BindingProbeReady /\ VoteApply(LateValidator, BindingApply)
    /\ UNCHANGED bindingStep

BindingNext ==
    \/ BindingPropose \/ BindingParameterQuorum \/ BindingParameterFinalize
    \/ BindingAssemble \/ BindingRootQuorum \/ BindingRootFinalize
    \/ BindingCompute \/ BindingApplyQuorum \/ BindingApplyFinalize
    \/ BindingAdvance \/ BindingCrash \/ BindingRestart \/ BindingRecover
    \/ BindingLateParameter \/ BindingLateApply
CurrentBindingSpec == BindingInit /\ [][BindingNext]_<<ProtocolVariables, bindingStep>>

\* Historical quorum votes remain durable. Only the late validator is forbidden
\* to append a first PARAMETER/APPLY vote after its native parent has changed.
NoStaleArithmeticVotes ==
    /\ ~\E vote \in durableVotes :
        vote.validator = LateValidator /\ vote.kind \in {"PARAMETER", "APPLY"}
    /\ durableSequence[LateValidator] = 4

=============================================================================
