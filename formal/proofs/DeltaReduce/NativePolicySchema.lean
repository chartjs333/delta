import DeltaReduce.NativePolicyCodec

/-! Generated pinned DVPOL001 field inventory. Not policy admission. -/
namespace DeltaReduce.NativePolicySchema
open NativePolicyCodec

def fmtContext : Format :=
  .field "arithmetic_profile_id" (.text) (.field "height" (.uint 8) (.field "parameter_schema_id" (.text) (.field "round_config_id" (.text) (.field "round_id" (.text) (.field "validator_epoch_id" (.text) (.field "view" (.uint 8) (.end)))))))

def fmtRational : Format :=
  .field "numerator" (.uint 8) (.field "denominator" (.uint 8) (.end))

def fmtTuple : Format :=
  .field "availability_certificate_id" (.text) (.field "commitment_id" (.text) (.field "domain_id" (.text) (.field "ticket_id" (.text) (.end))))

def fmtInputSetBody : Format :=
  .field "context" (fmtContext) (.field "input_root" (.text) (.field "tuples" (.vector 100000 (fmtTuple)) (.end)))

def fmtInputSet : Format :=
  .field "context" (fmtContext) (.field "input_root" (.text) (.field "quorum_threshold" (.uint 4) (.field "signer_ids" (.vector 100000 (.text)) (.field "tuples" (.vector 100000 (fmtTuple)) (.end)))))

def fmtSeed : Format :=
  .field "context" (fmtContext) (.field "input_set_certificate_id" (.text) (.field "seed_id" (.text) (.field "seed_profile_id" (.text) (.field "share_ids" (.vector 100000 (.text)) (.end)))))

def fmtNormEntry : Format :=
  .field "scale_denominator" (.uint 8) (.field "squared_norm" (.text) (.field "ticket_id" (.text) (.end)))

def fmtNorm : Format :=
  .field "context" (fmtContext) (.field "entries" (.vector 100000 (fmtNormEntry)) (.field "input_set_certificate_id" (.text) (.field "norm_root" (.text) (.end))))

def fmtEligibilityEntry : Format :=
  .field "accepted" (.boolean) (.field "domain_id" (.text) (.field "gamma" (fmtRational) (.field "reason_code" (.text) (.field "ticket_id" (.text) (.end)))))

def fmtEligibility : Format :=
  .field "context" (fmtContext) (.field "entries" (.vector 100000 (fmtEligibilityEntry)) (.field "input_set_certificate_id" (.text) (.field "norm_evidence_id" (.text) (.field "quorum_threshold" (.uint 4) (.field "robust_profile_id" (.text) (.field "signer_ids" (.vector 100000 (.text)) (.end)))))))

def fmtEligibilityBody : Format :=
  .field "context" (fmtContext) (.field "entries" (.vector 100000 (fmtEligibilityEntry)) (.field "input_set_certificate_id" (.text) (.field "norm_evidence_id" (.text) (.field "robust_profile_id" (.text) (.field "seed_transcript_id" (.text) (.end))))))

def fmtFinalizedEligibility : Format :=
  .field "certificate" (fmtEligibility) (.field "seed_transcript_id" (.text) (.end))

def fmtBucket : Format :=
  .field "bucket_id" (.text) (.field "ticket_id" (.text) (.end))

def fmtWeight : Format :=
  .field "alpha" (fmtRational) (.field "ticket_id" (.text) (.end))

def fmtPlan : Format :=
  .field "context" (fmtContext) (.field "accumulator_proof_id" (.text) (.field "bucket_assignments" (.vector 100000 (fmtBucket)) (.field "eligibility_certificate_id" (.text) (.field "input_set_certificate_id" (.text) (.field "iteration_count" (.uint 4) (.field "quorum_threshold" (.uint 4) (.field "seed_transcript_id" (.text) (.field "signer_ids" (.vector 100000 (.text)) (.field "transcript_root" (.text) (.field "weights" (.vector 100000 (fmtWeight)) (.end)))))))))))

def fmtPlanBody : Format :=
  .field "context" (fmtContext) (.field "accumulator_proof_id" (.text) (.field "bucket_assignments" (.vector 100000 (fmtBucket)) (.field "eligibility_certificate_id" (.text) (.field "input_set_certificate_id" (.text) (.field "iteration_count" (.uint 4) (.field "seed_transcript_id" (.text) (.field "transcript_root" (.text) (.field "weights" (.vector 100000 (fmtWeight)) (.end)))))))))

def fmtShardKey : Format :=
  .field "domain_id" (.text) (.field "shard_id" (.text) (.end))

def fmtParameter : Format :=
  .field "context" (fmtContext) (.field "aggregation_plan_certificate_id" (.text) (.field "denominator" (.uint 8) (.field "domain_id" (.text) (.field "eligibility_certificate_id" (.text) (.field "input_leaf_ids" (.vector 100000 (.text)) (.field "input_set_certificate_id" (.text) (.field "quorum_threshold" (.uint 4) (.field "result_numerators" (.vector 100000 (.text)) (.field "shard_id" (.text) (.field "signer_ids" (.vector 100000 (.text)) (.end)))))))))))

def fmtParameterBody : Format :=
  .field "context" (fmtContext) (.field "aggregation_plan_certificate_id" (.text) (.field "denominator" (.uint 8) (.field "domain_id" (.text) (.field "eligibility_certificate_id" (.text) (.field "input_leaf_ids" (.vector 100000 (.text)) (.field "input_set_certificate_id" (.text) (.field "result_numerators" (.vector 100000 (.text)) (.field "shard_id" (.text) (.field "vote_context_id" (.text) (.end))))))))))

def fmtRootLeaf : Format :=
  .field "domain_id" (.text) (.field "parameter_shard_qc_id" (.text) (.field "shard_id" (.text) (.end)))

def fmtRoot : Format :=
  .field "context" (fmtContext) (.field "aggregation_plan_certificate_id" (.text) (.field "eligibility_certificate_id" (.text) (.field "input_set_certificate_id" (.text) (.field "leaves" (.vector 100000 (fmtRootLeaf)) (.field "merkle_root" (.text) (.field "quorum_threshold" (.uint 4) (.field "required_keys" (.vector 100000 (fmtShardKey)) (.field "signer_ids" (.vector 100000 (.text)) (.end)))))))))

def fmtRootBody : Format :=
  .field "context" (fmtContext) (.field "aggregation_plan_certificate_id" (.text) (.field "eligibility_certificate_id" (.text) (.field "input_set_certificate_id" (.text) (.field "leaves" (.vector 100000 (fmtRootLeaf)) (.field "merkle_root" (.text) (.field "required_keys" (.vector 100000 (fmtShardKey)) (.end)))))))

def fmtDomainWeight : Format :=
  .field "domain_id" (.text) (.field "pi" (fmtRational) (.end))

def fmtApplyProfile : Format :=
  .field "accumulator_proof_id" (.text) (.field "domain_weights" (.vector 100000 (fmtDomainWeight)) (.field "learning_rate" (fmtRational) (.field "momentum" (fmtRational) (.field "nesterov" (.boolean) (.field "rounding" (.text) (.field "weight_decay" (fmtRational) (.end)))))))

def fmtApplyCandidate : Format :=
  .field "context" (fmtContext) (.field "aggregate_root_qc_id" (.text) (.field "apply_arithmetic_profile_id" (.text) (.field "next_model_hash" (.text) (.field "next_model_values" (.vector 100000 (.text)) (.field "next_optimizer_hash" (.text) (.field "next_optimizer_values" (.vector 100000 (.text)) (.field "parent_checkpoint_id" (.text) (.field "parent_optimizer_hash" (.text) (.end)))))))))

def fmtApplyQc : Format :=
  .field "context" (fmtContext) (.field "aggregate_root_qc_id" (.text) (.field "apply_arithmetic_profile_id" (.text) (.field "apply_candidate_id" (.text) (.field "next_model_hash" (.text) (.field "next_optimizer_hash" (.text) (.field "parent_checkpoint_id" (.text) (.field "quorum_threshold" (.uint 4) (.field "signer_ids" (.vector 100000 (.text)) (.end)))))))))

def fmtFinalizedApply : Format :=
  .field "certificate" (fmtApplyQc) (.field "candidate" (fmtApplyCandidate) (.end))

def fmtTimeout : Format :=
  .field "round_id" (.text) (.field "height" (.uint 8) (.field "view" (.uint 8) (.end)))

def fmtViewChange : Format :=
  .field "round_id" (.text) (.field "height" (.uint 8) (.field "from_view" (.uint 8) (.field "to_view" (.uint 8) (.field "soft_deadline_tick" (.uint 8) (.end)))))

def fmtAbortRequest : Format :=
  .field "round_id" (.text) (.field "reason_code" (.text) (.end))

def fmtAbortBody : Format :=
  .field "round_id" (.text) (.field "validator_epoch_id" (.text) (.field "height" (.uint 8) (.field "view" (.uint 8) (.field "hard_deadline_tick" (.uint 8) (.field "parent_checkpoint_id" (.text) (.field "reason_code" (.text) (.field "round_config_ids" (.vector 100000 (.text)) (.field "input_set_ids" (.vector 100000 (.text)) (.field "eligibility_ids" (.vector 100000 (.text)) (.field "aggregation_plan_ids" (.vector 100000 (.text)) (.field "parameter_ids" (.vector 100000 (.text)) (.field "aggregate_root_ids" (.vector 100000 (.text)) (.field "apply_ids" (.vector 100000 (.text)) (.end))))))))))))))

def fmtParents : Format :=
  .field "round_config_id" (.text) (.field "parent_checkpoint_id" (.text) (.field "input_set_certificate_id" (.text) (.field "seed_transcript_id" (.text) (.field "norm_evidence_id" (.text) (.field "eligibility_certificate_id" (.text) (.field "aggregation_plan_certificate_id" (.text) (.field "parameter_matrix_root" (.text) (.field "aggregate_root_certificate_id" (.text) (.field "apply_profile_id" (.text) (.field "apply_candidate_id" (.text) (.field "last_finalized_certificate_id" (.text) (.field "domain_id" (.text) (.field "shard_id" (.text) (.field "reason_code" (.text) (.end)))))))))))))))

def fmtCandidate : Format :=
  .field "action" (.uint 4) (.field "body_hash" (.text) (.field "context_id" (.text) (.field "height" (.uint 8) (.field "view" (.uint 8) (.field "parents" (fmtParents) (.end))))))

def fmtSnapshot : Format :=
  .field "state_id" (.text) (.field "parameter_schema_id" (.text) (.field "arithmetic_profile_id" (.text) (.field "required_accumulator_proof_id" (.text) (.field "proposed_round_config_ids" (.vector 100000 (.text)) (.field "finalized_round_config_ids" (.vector 100000 (.text)) (.field "closed_input_set_ids" (.vector 100000 (.text)) (.field "input_set_bodies" (.vector 100000 (fmtInputSetBody)) (.field "input_set_certificates" (.vector 100000 (fmtInputSet)) (.field "finalized_input_set_ids" (.vector 100000 (.text)) (.field "seed_transcripts" (.vector 100000 (fmtSeed)) (.field "norm_evidence" (.vector 100000 (fmtNorm)) (.field "eligibility_bodies" (.vector 100000 (fmtEligibilityBody)) (.field "eligibility_certificates" (.vector 100000 (fmtFinalizedEligibility)) (.field "finalized_eligibility_ids" (.vector 100000 (.text)) (.field "aggregation_plan_bodies" (.vector 100000 (fmtPlanBody)) (.field "aggregation_plan_certificates" (.vector 100000 (fmtPlan)) (.field "finalized_aggregation_plan_ids" (.vector 100000 (.text)) (.field "parameter_bodies" (.vector 100000 (fmtParameterBody)) (.field "parameter_qcs" (.vector 100000 (fmtParameter)) (.field "finalized_parameter_ids" (.vector 100000 (.text)) (.field "required_parameter_keys" (.vector 100000 (fmtShardKey)) (.field "aggregate_root_bodies" (.vector 100000 (fmtRootBody)) (.field "aggregate_root_qcs" (.vector 100000 (fmtRoot)) (.field "finalized_aggregate_root_ids" (.vector 100000 (.text)) (.field "apply_profiles" (.vector 100000 (fmtApplyProfile)) (.field "apply_candidates" (.vector 100000 (fmtApplyCandidate)) (.field "apply_qcs" (.vector 100000 (fmtFinalizedApply)) (.field "finalized_apply_ids" (.vector 100000 (.text)) (.field "timeout_observations" (.vector 100000 (fmtTimeout)) (.field "view_change_bodies" (.vector 100000 (fmtViewChange)) (.field "abort_requests" (.vector 100000 (fmtAbortRequest)) (.field "abort_bodies" (.vector 100000 (fmtAbortBody)) (.end)))))))))))))))))))))))))))))))))

def fmtPolicy : Format :=
  .field "local_validator_id" (.text) (.field "validator_epoch_id" (.text) (.field "validator_ids" (.vector 4096 (.text)) (.field "role" (.uint 4) (.field "round_id" (.text) (.field "round_config_id" (.text) (.field "configured_abort_reason" (.text) (.field "initial_logical_tick" (.uint 8) (.field "soft_deadline_tick" (.uint 8) (.field "hard_deadline_tick" (.uint 8) (.field "snapshot" (fmtSnapshot) (.field "candidates" (.vector 8192 (fmtCandidate)) (.end))))))))))))

end DeltaReduce.NativePolicySchema
