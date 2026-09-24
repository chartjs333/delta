--------------------- MODULE DeltaReducePersistenceHarness --------------------
EXTENDS DeltaReduceCurrentBindingHarness

\* Candidate concrete persistence suffix over production arithmetic vote,
\* transport and recovery actions. Upstream certificates are Phase6 premises;
\* the remaining prefix is production 3-of-4 PARAMETER/ROOT processing. One
\* validator and one injected fault are explored, with no concurrent current
\* change. Receipt tuples abstract bytes; they are not a native WAL encoding.
CONSTANT PersistenceKind
VARIABLES ioStage, ioCut, ioCrashed, ioRecord, ioReturned, ioCommitted, ioCorrupt

IOVariables == <<ioStage, ioCut, ioCrashed, ioRecord, ioReturned, ioCommitted, ioCorrupt>>
CutPoints == {"NONE", "VALIDATED", "APPENDED", "DURABLE", "COMMITTED",
              "EXPOSED", "BARRIER_FAILURE", "TORN"}
TargetStep == IF PersistenceKind = "PARAMETER" THEN 1 ELSE 23
TargetBody == IF PersistenceKind = "PARAMETER" THEN BindingParameter ELSE BindingApply
TargetKey == IF PersistenceKind = "PARAMETER"
             THEN ParameterKey(HarnessDomain, BindingShard) ELSE BindingRoot
TargetEnvelope == VoteEnvelope(LateValidator, PersistenceKind, TargetKey, TargetBody)
PrefixSequence == Cardinality(VotesBy(LateValidator, HarnessDurableVotes))
ExpectedReceipt == [vote |-> TargetEnvelope, sequence |-> PrefixSequence + 1]
NativePersist == IF PersistenceKind = "PARAMETER"
                 THEN VoteParameter(LateValidator, BindingParameter)
                 ELSE VoteApply(LateValidator, BindingApply)
HoldProtocol == UNCHANGED <<ProtocolVariables, bindingStep>>
NotCut(point) == ioCrashed \/ ioCut # point

PersistenceInit ==
    /\ PersistenceKind \in {"PARAMETER", "APPLY"}
    /\ BindingInit
    /\ ioStage = "PREFIX" /\ ioCut \in CutPoints
    /\ ioCrashed = FALSE /\ ioCommitted = FALSE /\ ioCorrupt = FALSE
    /\ ioRecord = {} /\ ioReturned = {}

PersistPrefix ==
    /\ UNCHANGED ioCut
    /\ bindingStep < TargetStep /\ BindingNext
    /\ UNCHANGED IOVariables

PersistAdmit ==
    /\ UNCHANGED ioCut
    /\ bindingStep = TargetStep /\ ioStage = "PREFIX"
    /\ ENABLED NativePersist
    /\ ioStage' = "VALIDATED"
    /\ HoldProtocol
    /\ UNCHANGED <<ioCrashed, ioRecord, ioReturned, ioCommitted, ioCorrupt>>

PersistAppend ==
    /\ UNCHANGED ioCut
    /\ ioStage = "VALIDATED" /\ NotCut("VALIDATED")
    /\ ioStage' = "APPENDED"
    /\ HoldProtocol
    /\ UNCHANGED <<ioCrashed, ioRecord, ioReturned, ioCommitted, ioCorrupt>>

PersistBarrier ==
    /\ UNCHANGED ioCut
    /\ ioStage = "APPENDED"
    /\ NotCut("APPENDED") /\ NotCut("BARRIER_FAILURE") /\ NotCut("TORN")
    /\ NativePersist /\ UNCHANGED bindingStep
    /\ ioStage' = "DURABLE" /\ ioRecord' = {ExpectedReceipt}
    /\ UNCHANGED <<ioCrashed, ioReturned, ioCommitted, ioCorrupt>>

PersistCommit ==
    /\ UNCHANGED ioCut
    /\ ioStage = "DURABLE" /\ NotCut("DURABLE")
    /\ ioStage' = "COMMITTED" /\ ioCommitted' = TRUE
    /\ HoldProtocol
    /\ UNCHANGED <<ioCrashed, ioRecord, ioReturned, ioCorrupt>>

PersistExpose ==
    /\ UNCHANGED ioCut
    /\ ioStage = "COMMITTED" /\ NotCut("COMMITTED")
    /\ ioCommitted /\ CanVote(LateValidator)
    /\ TargetEnvelope \in durableVotes /\ ioRecord = {ExpectedReceipt}
    /\ IF TargetEnvelope \in messages \cup receivedVotes
          THEN HoldProtocol
          ELSE SendVoteEnvelope(TargetEnvelope) /\ UNCHANGED bindingStep
    /\ ioStage' = "EXPOSED" /\ ioReturned' = ioReturned \cup ioRecord
    /\ UNCHANGED <<ioCrashed, ioRecord, ioCommitted, ioCorrupt>>

PersistReplay ==
    /\ UNCHANGED ioCut
    /\ ioStage = "EXPOSED" /\ NotCut("EXPOSED")
    /\ CanVote(LateValidator) /\ ioRecord = {ExpectedReceipt}
    /\ ioStage' = "DONE" /\ ioReturned' = ioReturned \cup ioRecord
    /\ HoldProtocol
    /\ UNCHANGED <<ioCrashed, ioRecord, ioCommitted, ioCorrupt>>

CrashBeforeRecord ==
    /\ CrashBeforePersistKind(LateValidator, PersistenceKind)
    /\ UNCHANGED bindingStep
    /\ ioStage' = "CRASHED" /\ ioCrashed' = TRUE /\ ioCommitted' = FALSE
    /\ UNCHANGED <<ioRecord, ioReturned, ioCorrupt>>
CrashAfterRecord ==
    /\ CrashAfterPersistKind(LateValidator, PersistenceKind)
    /\ UNCHANGED bindingStep
    /\ ioStage' = "CRASHED" /\ ioCrashed' = TRUE /\ ioCommitted' = FALSE
    /\ UNCHANGED <<ioRecord, ioReturned, ioCorrupt>>

PersistCrashBefore ==
    /\ UNCHANGED ioCut
    /\ ioStage = "VALIDATED" /\ ~ioCrashed /\ ioCut = "VALIDATED"
    /\ CrashBeforeRecord
PersistCrashAfterDurable ==
    /\ UNCHANGED ioCut
    /\ ioStage = "DURABLE" /\ ~ioCrashed /\ ioCut = "DURABLE"
    /\ CrashAfterRecord
PersistCrashAfterCommit ==
    /\ UNCHANGED ioCut
    /\ ioStage = "COMMITTED" /\ ~ioCrashed /\ ioCut = "COMMITTED"
    /\ CrashAfterRecord
PersistCrashAfterExpose ==
    /\ UNCHANGED ioCut
    /\ ioStage = "EXPOSED" /\ ~ioCrashed /\ ioCut = "EXPOSED"
    /\ CrashAfterSendKind(LateValidator, PersistenceKind)
    /\ UNCHANGED bindingStep
    /\ ioStage' = "CRASHED" /\ ioCrashed' = TRUE /\ ioCommitted' = FALSE
    /\ UNCHANGED <<ioRecord, ioReturned, ioCorrupt>>

\* Without an acknowledged barrier, either the complete valid prefix survived
\* or it did not. Never infer absence from a failed fsync. The complete branch
\* linearizes the production vote before the crash; neither branch can expose.
PersistAppendLost ==
    /\ UNCHANGED ioCut
    /\ ioStage = "APPENDED" /\ ~ioCrashed /\ ioCut = "APPENDED"
    /\ CrashBeforeRecord
PersistAppendSurvived ==
    /\ UNCHANGED ioCut
    /\ ioStage = "APPENDED" /\ ~ioCrashed /\ ioCut = "APPENDED"
    /\ NativePersist /\ UNCHANGED bindingStep
    /\ ioStage' = "UNACKED" /\ ioRecord' = {ExpectedReceipt}
    /\ UNCHANGED <<ioCrashed, ioReturned, ioCommitted, ioCorrupt>>
PersistBarrierFailedAbsent ==
    /\ UNCHANGED ioCut
    /\ ioStage = "APPENDED" /\ ~ioCrashed /\ ioCut = "BARRIER_FAILURE"
    /\ HoldProtocol /\ ioStage' = "FAILED_ABSENT"
    /\ UNCHANGED <<ioCrashed, ioRecord, ioReturned, ioCommitted, ioCorrupt>>
PersistBarrierFailedPresent ==
    /\ UNCHANGED ioCut
    /\ ioStage = "APPENDED" /\ ~ioCrashed /\ ioCut = "BARRIER_FAILURE"
    /\ NativePersist /\ UNCHANGED bindingStep
    /\ ioStage' = "UNACKED" /\ ioRecord' = {ExpectedReceipt}
    /\ UNCHANGED <<ioCrashed, ioReturned, ioCommitted, ioCorrupt>>
PersistStopOnError ==
    /\ UNCHANGED ioCut
    /\ \/ (ioStage = "UNACKED" /\ CrashAfterRecord)
       \/ (ioStage \in {"FAILED_ABSENT", "TORN"} /\ CrashBeforeRecord)

PersistTornAppend ==
    /\ UNCHANGED ioCut
    /\ ioStage = "APPENDED" /\ ~ioCrashed /\ ioCut = "TORN"
    /\ HoldProtocol /\ ioStage' = "TORN" /\ ioCorrupt' = TRUE
    /\ UNCHANGED <<ioCrashed, ioRecord, ioReturned, ioCommitted>>
PersistRestart ==
    /\ UNCHANGED ioCut
    /\ ioStage = "CRASHED" /\ Restart(LateValidator)
    /\ UNCHANGED bindingStep /\ ioStage' = "RECOVERING"
    /\ UNCHANGED <<ioCrashed, ioRecord, ioReturned, ioCommitted, ioCorrupt>>
PersistRecover ==
    /\ UNCHANGED ioCut
    /\ ioStage = "RECOVERING" /\ ~ioCorrupt
    /\ RecoverJournal(LateValidator) /\ UNCHANGED bindingStep
    /\ ioStage' = IF ioRecord = {} THEN "PREFIX" ELSE "COMMITTED"
    /\ ioCommitted' = (ioRecord # {})
    /\ UNCHANGED <<ioCrashed, ioRecord, ioReturned, ioCorrupt>>
PersistCorruptRecovery ==
    /\ UNCHANGED ioCut
    /\ ioStage = "RECOVERING" /\ ioCorrupt
    /\ HoldProtocol /\ ioStage' = "BLOCKED"
    /\ UNCHANGED <<ioCrashed, ioRecord, ioReturned, ioCommitted, ioCorrupt>>

\* Enable deadlock checking everywhere except the two intended terminal states.
\* This explicit stutter does not assert eventual recovery or a repair policy.
PersistTerminal ==
    /\ ioStage \in {"DONE", "BLOCKED"}
    /\ UNCHANGED <<ProtocolVariables, bindingStep, IOVariables>>

PersistenceNext ==
    \/ PersistPrefix \/ PersistAdmit \/ PersistAppend \/ PersistBarrier
    \/ PersistCommit \/ PersistExpose \/ PersistReplay
    \/ PersistCrashBefore \/ PersistCrashAfterDurable \/ PersistCrashAfterCommit
    \/ PersistCrashAfterExpose \/ PersistAppendLost \/ PersistAppendSurvived
    \/ PersistBarrierFailedAbsent \/ PersistBarrierFailedPresent \/ PersistStopOnError
    \/ PersistTornAppend \/ PersistRestart \/ PersistRecover \/ PersistCorruptRecovery
    \/ PersistTerminal
PersistenceSpec == PersistenceInit /\ [][PersistenceNext]_<<ProtocolVariables, bindingStep, IOVariables>>

PersistenceRecordSound ==
    /\ ioStage \in {"PREFIX", "VALIDATED", "APPENDED", "DURABLE", "COMMITTED",
        "EXPOSED", "DONE", "CRASHED", "RECOVERING", "UNACKED", "FAILED_ABSENT", "TORN", "BLOCKED"}
    /\ ioCut \in CutPoints /\ ioCrashed \in BOOLEAN
    /\ ioCommitted \in BOOLEAN /\ ioCorrupt \in BOOLEAN
    /\ ioRecord \in {{}, {ExpectedReceipt}}
    /\ (TargetEnvelope \in durableVotes) <=> (ioRecord # {})
    /\ durableSequence[LateValidator] = PrefixSequence + Cardinality(ioRecord)
    /\ ioReturned \subseteq ioRecord
    /\ TargetEnvelope \in messages \cup receivedVotes => ioReturned = {ExpectedReceipt}
    /\ ioStage \in {"EXPOSED", "DONE"} =>
        (ioCommitted /\ CanVote(LateValidator) /\ ioReturned = {ExpectedReceipt})

PersistenceRecoverySound ==
    /\ ioStage = "COMMITTED" =>
        (CanVote(LateValidator) /\ TargetEnvelope \in volatileVotes)
    /\ ioStage \in {"FAILED_ABSENT", "UNACKED", "TORN", "BLOCKED"} => ioReturned = {}
    /\ ioCorrupt => ioRecord = {} /\ ioReturned = {}
    /\ ioStage = "BLOCKED" => recoveryState[LateValidator] = "RECOVERING"

=============================================================================
