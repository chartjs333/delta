---------------------- MODULE DeltaReduceRefinement ----------------------
EXTENDS DeltaReduce

FormalActionIds == {
    "ACT-CONFIG-PROPOSE", "ACT-CONFIG-VOTE", "ACT-CONFIG-FINALIZE",
    "ACT-TICKET-ISSUE", "ACT-LEASE-OPEN", "ACT-LEASE-RENEW",
    "ACT-LEASE-EXPIRE", "ACT-LEASE-REASSIGN", "ACT-COMMIT",
    "ACT-AVAIL-ATTEST", "ACT-AVAIL-FINALIZE", "ACT-INPUT-CLOSE",
    "ACT-ISC-VOTE", "ACT-ISC-FINALIZE", "ACT-SEED-GENERATE",
    "ACT-EC-VOTE", "ACT-EC-FINALIZE", "ACT-APC-VOTE",
    "ACT-APC-FINALIZE", "ACT-PARAM-PROPOSE", "ACT-PARAM-VOTE",
    "ACT-PARAM-FINALIZE", "ACT-ROOT-ASSEMBLE", "ACT-ROOT-VOTE",
    "ACT-ROOT-FINALIZE", "ACT-APPLY-COMPUTE", "ACT-APPLY-VOTE",
    "ACT-APPLY-FINALIZE", "ACT-CURRENT-ADVANCE",
    "ACT-TIMEOUT-SOFT", "ACT-VIEW-VOTE", "ACT-VIEW-FINALIZE",
    "ACT-ABORT-VOTE", "ACT-ABORT-FINALIZE", "ACT-CRASH",
    "ACT-RESTART", "ACT-JOURNAL-RECOVER", "ACT-ARTIFACT-CORRUPT",
    "ACT-ARTIFACT-LOSE", "ACT-ARTIFACT-REPAIR", "ACT-PUBLISH",
    "ACT-MESSAGE-ENQUEUE", "ACT-MESSAGE-DELIVER", "ACT-MESSAGE-DROP",
    "ACT-MESSAGE-DUPLICATE", "ACT-MESSAGE-REPLAY",
    "ACT-PARTITION-ENABLE", "ACT-PARTITION-HEAL",
    "ACT-LOGICAL-TIME-ADVANCE"
}

ActionModule(actionId) ==
    CASE actionId \in {
            "ACT-CONFIG-PROPOSE", "ACT-CONFIG-VOTE",
            "ACT-CONFIG-FINALIZE"} -> "DeltaReduceCertificates"
      [] actionId \in {
            "ACT-TICKET-ISSUE", "ACT-LEASE-OPEN", "ACT-LEASE-RENEW",
            "ACT-LEASE-EXPIRE", "ACT-LEASE-REASSIGN", "ACT-COMMIT"}
            -> "DeltaReduceTickets"
      [] actionId \in {
            "ACT-AVAIL-ATTEST", "ACT-AVAIL-FINALIZE"}
            -> "DeltaReduceAvailability"
      [] actionId \in {
            "ACT-INPUT-CLOSE", "ACT-ISC-VOTE", "ACT-ISC-FINALIZE",
            "ACT-SEED-GENERATE", "ACT-EC-VOTE", "ACT-EC-FINALIZE",
            "ACT-APC-VOTE", "ACT-APC-FINALIZE",
            "ACT-MESSAGE-REPLAY"} -> "DeltaReduceCertificates"
      [] actionId \in {
            "ACT-PARAM-PROPOSE", "ACT-PARAM-VOTE",
            "ACT-PARAM-FINALIZE", "ACT-ROOT-ASSEMBLE",
            "ACT-ROOT-VOTE", "ACT-ROOT-FINALIZE",
            "ACT-APPLY-COMPUTE", "ACT-APPLY-VOTE",
            "ACT-APPLY-FINALIZE", "ACT-CURRENT-ADVANCE",
            "ACT-PUBLISH"} -> "DeltaReduceReduceApply"
      [] OTHER -> "DeltaReduceFailures"

ProjectedAction(actionId) ==
    CASE actionId = "ACT-CONFIG-PROPOSE" -> ProposeRoundConfigAction
      [] actionId = "ACT-CONFIG-VOTE" -> PersistConfigVoteAction
      [] actionId = "ACT-CONFIG-FINALIZE" -> FinalizeRoundConfigAction
      [] actionId = "ACT-TICKET-ISSUE" -> IssueTicketAction
      [] actionId = "ACT-LEASE-OPEN" -> LeaseTicketAction
      [] actionId = "ACT-LEASE-RENEW" -> RenewLeaseAction
      [] actionId = "ACT-LEASE-EXPIRE" -> ExpireLeaseAction
      [] actionId = "ACT-LEASE-REASSIGN" -> ReassignTicketAction
      [] actionId = "ACT-COMMIT" -> CommitTicketAction
      [] actionId = "ACT-AVAIL-ATTEST" -> AttestAvailabilityAction
      [] actionId = "ACT-AVAIL-FINALIZE" -> FinalizeAvailabilityAction
      [] actionId = "ACT-INPUT-CLOSE" -> CloseInputAction
      [] actionId = "ACT-ISC-VOTE" -> VoteISCAction
      [] actionId = "ACT-ISC-FINALIZE" -> FinalizeISCAction
      [] actionId = "ACT-SEED-GENERATE" -> GenerateSeedAction
      [] actionId = "ACT-EC-VOTE" -> VoteECAction
      [] actionId = "ACT-EC-FINALIZE" -> FinalizeECAction
      [] actionId = "ACT-APC-VOTE" -> VoteAPCAction
      [] actionId = "ACT-APC-FINALIZE" -> FinalizeAPCAction
      [] actionId = "ACT-PARAM-PROPOSE" -> ProposeParameterResultAction
      [] actionId = "ACT-PARAM-VOTE" -> VoteParameterAction
      [] actionId = "ACT-PARAM-FINALIZE" -> FinalizeParameterQCAction
      [] actionId = "ACT-ROOT-ASSEMBLE" -> AssembleAggregateRootAction
      [] actionId = "ACT-ROOT-VOTE" -> VoteAggregateRootAction
      [] actionId = "ACT-ROOT-FINALIZE" -> FinalizeAggregateRootQCAction
      [] actionId = "ACT-APPLY-COMPUTE" -> ComputeApplyCandidateAction
      [] actionId = "ACT-APPLY-VOTE" -> VoteApplyAction
      [] actionId = "ACT-APPLY-FINALIZE" -> FinalizeApplyQCAction
      [] actionId = "ACT-CURRENT-ADVANCE" ->
            (AdvanceCurrentCheckpointAction \/ ReplayCurrentAdvanceAction)
      [] actionId = "ACT-TIMEOUT-SOFT" -> SoftTimeoutAction
      [] actionId = "ACT-VIEW-VOTE" -> VoteViewChangeAction
      [] actionId = "ACT-VIEW-FINALIZE" -> ViewChangeAction
      [] actionId = "ACT-ABORT-VOTE" -> VoteHardAbortAction
      [] actionId = "ACT-ABORT-FINALIZE" -> HardAbortAction
      [] actionId = "ACT-CRASH" ->
            (CrashBeforePersistAction \/ CrashAfterPersistAction \/
             CrashAfterSendAction \/
             CrashAfterApplyQCBeforePointerAction)
      [] actionId = "ACT-RESTART" -> RestartAction
      [] actionId = "ACT-JOURNAL-RECOVER" -> RecoverJournalAction
      [] actionId = "ACT-ARTIFACT-CORRUPT" -> CorruptArtifactAction
      [] actionId = "ACT-ARTIFACT-LOSE" ->
            (LoseArtifactPreFreezeAction \/ LoseArtifactPostFreezeAction)
      [] actionId = "ACT-ARTIFACT-REPAIR" -> RepairArtifactAction
      [] actionId = "ACT-PUBLISH" -> PublishCertifiedObjectAction
      [] actionId = "ACT-MESSAGE-ENQUEUE" -> EnqueueMessageAction
      [] actionId = "ACT-MESSAGE-DELIVER" -> DeliverMessageAction
      [] actionId = "ACT-MESSAGE-DROP" -> DropMessageAction
      [] actionId = "ACT-MESSAGE-DUPLICATE" -> DuplicateMessageAction
      [] actionId = "ACT-MESSAGE-REPLAY" -> ReplayMessageAction
      [] actionId = "ACT-PARTITION-ENABLE" -> EnablePartitionAction
      [] actionId = "ACT-PARTITION-HEAL" -> HealPartitionAction
      [] actionId = "ACT-LOGICAL-TIME-ADVANCE" -> AdvanceLogicalTime
      [] OTHER -> FALSE

RejectedProjectedAction(actionId) ==
    CASE actionId = "ACT-COMMIT" ->
            (RejectStaleCommitmentAction \/
             RejectCommitmentEquivocationAction \/
             RejectLateCommitmentAction)
      [] actionId = "ACT-AVAIL-FINALIZE" -> RejectLateAvailabilityAction
      [] actionId = "ACT-ISC-FINALIZE" -> RejectConflictingISCAction
      [] actionId = "ACT-SEED-GENERATE" ->
            (RejectEarlySeedAction \/ RejectWrongSeedParentAction \/
             RejectConflictingSeedAction)
      [] actionId = "ACT-EC-FINALIZE" ->
            (RejectInvalidECParentAction \/ RejectECMembershipAction \/
             RejectNormEvidenceAction \/ RejectConflictingECAction)
      [] actionId = "ACT-APC-FINALIZE" ->
            (RejectInvalidAPCParentAction \/ RejectAPCMembershipAction \/
             RejectWrongCoefficientProfileAction \/
             RejectConflictingAPCAction)
      [] actionId = "ACT-PARAM-PROPOSE" ->
            (RejectParameterWrongParentAction \/
             RejectParameterUncheckedAction \/
             RejectParameterOverflowAction \/
             RejectConflictingParameterAction)
      [] actionId = "ACT-ROOT-ASSEMBLE" ->
            (RejectIncompleteAggregateAction \/
             RejectDuplicateAggregateAction \/ RejectMixedAggregateAction \/
             RejectConflictingAggregateAction)
      [] actionId = "ACT-APPLY-COMPUTE" ->
            (RejectWrongApplyParentAction \/ RejectUnsafeApplyAction \/
             RejectConflictingApplyAction)
      [] actionId = "ACT-CURRENT-ADVANCE" -> RejectCurrentConflictAction
      [] actionId = "ACT-PUBLISH" -> RejectForbiddenPublicationAction
      [] OTHER -> FALSE

StutteringProjection ==
    UNCHANGED ProtocolVariables

RefinesEvent(actionId, outcome) ==
    /\ actionId \in FormalActionIds
    /\ IF outcome \in {"REJECTED", "BLOCKED"}
          THEN RejectedProjectedAction(actionId) \/ StutteringProjection
          ELSE IF outcome \in {"NO_OP", "STUTTER"}
          THEN StutteringProjection
          ELSE ProjectedAction(actionId)

=============================================================================
