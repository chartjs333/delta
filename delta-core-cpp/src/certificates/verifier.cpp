#include <delta/certificates/verifier.hpp>

#include <algorithm>
#include <cstddef>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace delta::certificates {
namespace {

[[noreturn]] void reject(ErrorCode code, const char* message) {
  throw CertificateError(code, message);
}

void require(bool condition, ErrorCode code, const char* message) {
  if (!condition) {
    reject(code, message);
  }
}

void require_parent(std::string_view actual, std::string_view expected, const char* message) {
#if defined(DELTA_CERTIFICATE_MUTANT_SEED_PARENT)
  static_cast<void>(actual);
  static_cast<void>(expected);
  static_cast<void>(message);
#else
  require(actual == expected, ErrorCode::parent_mismatch, message);
#endif
}

[[nodiscard]] std::vector<std::string> accepted_tickets(
    const EligibilityCertificate& eligibility) {
  std::vector<std::string> result;
  for (const auto& entry : eligibility.entries) {
    if (entry.accepted) {
      result.push_back(entry.ticket_id);
    }
  }
  return result;
}

[[nodiscard]] std::vector<std::string> assignment_tickets(
    const AggregationPlanCertificate& plan) {
  std::vector<std::string> result;
  result.reserve(plan.bucket_assignments.size());
  for (const auto& entry : plan.bucket_assignments) {
    result.push_back(entry.ticket_id);
  }
  std::sort(result.begin(), result.end());
  return result;
}

[[nodiscard]] std::vector<std::string> weight_tickets(
    const AggregationPlanCertificate& plan) {
  std::vector<std::string> result;
  result.reserve(plan.weights.size());
  for (const auto& entry : plan.weights) {
    result.push_back(entry.ticket_id);
  }
  return result;
}

}  // namespace

std::string_view vote_kind_name(VoteKind kind) noexcept {
  switch (kind) {
    case VoteKind::input_set:
      return "ISC";
    case VoteKind::eligibility:
      return "EC";
    case VoteKind::aggregation_plan:
      return "APC";
    case VoteKind::parameter_shard:
      return "PARAMETER_SHARD_QC";
    case VoteKind::aggregate_root:
      return "AGGREGATE_ROOT_QC";
    case VoteKind::apply:
      return "APPLY_QC";
  }
  return "UNKNOWN";
}

core::protocol::Vote make_vote(
    VoteKind kind,
    const Context& context,
    std::string body_id,
    std::string validator_id,
    std::string signature_id,
    std::uint64_t durable_sequence) {
  require(is_content_id(body_id), ErrorCode::identifier_invalid, "vote body ID is invalid");
  require(
      is_content_id(signature_id), ErrorCode::identifier_invalid, "vote signature ID is invalid");
  require(durable_sequence > 0U, ErrorCode::context_mismatch, "vote sequence is zero");
  require(!validator_id.empty(), ErrorCode::identifier_invalid, "validator ID is empty");
  return core::protocol::Vote{
      .body_hash = std::move(body_id),
      .context_id = std::string(vote_kind_name(kind)) + ":" + context.round_id + ":" +
                    std::to_string(context.height) + ":" + std::to_string(context.view),
      .durable_sequence = durable_sequence,
      .height = context.height,
      .kind = std::string(vote_kind_name(kind)),
      .round_id = context.round_id,
      .signature_id = std::move(signature_id),
      .validator_epoch_id = context.validator_epoch_id,
      .validator_id = std::move(validator_id),
      .view = context.view,
  };
}

ChainVerifier::ChainVerifier(Context expected_context, ValidatorPolicy validators)
    : expected_context_(std::move(expected_context)), validators_(std::move(validators)) {
  validate_context(expected_context_, expected_context_);
  require(
      validators_.validator_epoch_id == expected_context_.validator_epoch_id,
      ErrorCode::context_mismatch,
      "validator policy epoch differs from the certificate context");
  require(
      !validators_.validator_ids.empty() && (validators_.validator_ids.size() % 3U) == 1U,
      ErrorCode::quorum_invalid,
      "validator set is not 3f+1");
  require(
      std::is_sorted(validators_.validator_ids.begin(), validators_.validator_ids.end()) &&
          std::adjacent_find(
              validators_.validator_ids.begin(), validators_.validator_ids.end()) ==
              validators_.validator_ids.end(),
      ErrorCode::order_invalid,
      "validator set is not canonical");
  const auto fault_tolerance = (validators_.validator_ids.size() - 1U) / 3U;
  require(
      validators_.quorum_threshold == 2U * fault_tolerance + 1U,
      ErrorCode::quorum_invalid,
      "validator threshold is not 2f+1");
}

void ChainVerifier::validate_signers(
    const std::vector<std::string>& signer_ids,
    std::uint32_t threshold) const {
  require(
      threshold == validators_.quorum_threshold && signer_ids.size() >= threshold,
      ErrorCode::quorum_invalid,
      "certificate does not satisfy the configured quorum");
  require(
      std::is_sorted(signer_ids.begin(), signer_ids.end()) &&
          std::adjacent_find(signer_ids.begin(), signer_ids.end()) == signer_ids.end(),
      ErrorCode::order_invalid,
      "certificate signer set is not canonical");
  for (const auto& signer : signer_ids) {
    require(
        std::binary_search(
            validators_.validator_ids.begin(), validators_.validator_ids.end(), signer),
        ErrorCode::quorum_invalid,
        "certificate includes an unknown signer");
  }
}

std::string ChainVerifier::verify_input_set(const InputSetCertificate& value) const {
  validate_context(value.context, expected_context_);
  validate_signers(value.signer_ids, value.quorum_threshold);
  return content_id(value);
}

std::string ChainVerifier::verify_seed(
    const SeedTranscript& value,
    std::string_view input_set_certificate_id) const {
  validate_context(value.context, expected_context_);
  require_parent(
      value.input_set_certificate_id,
      input_set_certificate_id,
      "seed transcript does not descend from the certified input set");
  return content_id(value);
}

std::string ChainVerifier::verify_norms(
    const NormEvidence& value,
    std::string_view input_set_certificate_id) const {
  validate_context(value.context, expected_context_);
  require_parent(
      value.input_set_certificate_id,
      input_set_certificate_id,
      "norm evidence does not descend from the certified input set");
  return content_id(value);
}

std::string ChainVerifier::verify_eligibility(
    const EligibilityCertificate& value,
    const InputSetCertificate& input_set,
    std::string_view norm_evidence_id) const {
  const auto input_set_id = verify_input_set(input_set);
  validate_context(value.context, expected_context_);
  require_parent(
      value.input_set_certificate_id,
      input_set_id,
      "eligibility certificate has the wrong input-set parent");
  require_parent(
      value.norm_evidence_id,
      norm_evidence_id,
      "eligibility certificate has the wrong norm-evidence parent");
  validate_signers(value.signer_ids, value.quorum_threshold);
  require(
      value.entries.size() == input_set.tuples.size(),
      ErrorCode::membership_mutation,
      "eligibility certificate changed the frozen membership");
  for (std::size_t index = 0U; index < value.entries.size(); ++index) {
    require(
        value.entries[index].ticket_id == input_set.tuples[index].ticket_id &&
            value.entries[index].domain_id == input_set.tuples[index].domain_id,
        ErrorCode::membership_mutation,
        "eligibility entry is not a member of the certified input set");
  }
  return content_id(value);
}

std::string ChainVerifier::verify_plan(
    const AggregationPlanCertificate& value,
    const InputSetCertificate& input_set,
    const EligibilityCertificate& eligibility,
    std::string_view seed_transcript_id,
    std::string_view required_accumulator_proof_id) const {
  const auto input_set_id = verify_input_set(input_set);
  const auto eligibility_id = content_id(eligibility);
  validate_context(value.context, expected_context_);
  require_parent(value.input_set_certificate_id, input_set_id, "plan has wrong ISC parent");
  require_parent(
      value.eligibility_certificate_id, eligibility_id, "plan has wrong eligibility parent");
  require_parent(
      value.seed_transcript_id, seed_transcript_id, "plan has wrong seed transcript parent");
  require_parent(
      value.accumulator_proof_id,
      required_accumulator_proof_id,
      "plan has wrong accumulator proof");
  validate_signers(value.signer_ids, value.quorum_threshold);
  const auto accepted = accepted_tickets(eligibility);
  require(
      accepted == assignment_tickets(value) && accepted == weight_tickets(value),
      ErrorCode::membership_mutation,
      "plan does not cover exactly the eligible tickets");
  return content_id(value);
}

std::string ChainVerifier::verify_shard(
    const ParameterShardQc& value,
    std::string_view input_set_certificate_id,
    std::string_view eligibility_certificate_id,
    std::string_view aggregation_plan_certificate_id) const {
  validate_context(value.context, expected_context_);
  require_parent(
      value.input_set_certificate_id, input_set_certificate_id, "shard has wrong ISC parent");
  require_parent(
      value.eligibility_certificate_id,
      eligibility_certificate_id,
      "shard has wrong eligibility parent");
  require_parent(
      value.aggregation_plan_certificate_id,
      aggregation_plan_certificate_id,
      "shard has wrong aggregation-plan parent");
  validate_signers(value.signer_ids, value.quorum_threshold);
  return content_id(value);
}

std::string ChainVerifier::verify_root(
    const AggregateRootQc& value,
    std::string_view input_set_certificate_id,
    std::string_view eligibility_certificate_id,
    std::string_view aggregation_plan_certificate_id,
    const std::vector<ShardKey>& required_keys,
    const std::vector<ParameterShardQc>& shards) const {
  validate_context(value.context, expected_context_);
  require_parent(
      value.input_set_certificate_id, input_set_certificate_id, "root has wrong ISC parent");
  require_parent(
      value.eligibility_certificate_id,
      eligibility_certificate_id,
      "root has wrong eligibility parent");
  require_parent(
      value.aggregation_plan_certificate_id,
      aggregation_plan_certificate_id,
      "root has wrong aggregation-plan parent");
  validate_signers(value.signer_ids, value.quorum_threshold);
  require(
      std::is_sorted(required_keys.begin(), required_keys.end()) &&
          std::adjacent_find(required_keys.begin(), required_keys.end()) == required_keys.end(),
      ErrorCode::coverage_duplicate,
      "required shard matrix is not canonical");
#if !defined(DELTA_CERTIFICATE_MUTANT_OBSERVED_COVERAGE)
  require(
      value.required_keys == required_keys && value.leaves.size() == required_keys.size() &&
          shards.size() == required_keys.size(),
      ErrorCode::coverage_incomplete,
      "aggregate root does not match the immutable required shard matrix");
#endif
  const auto checked_count = value.required_keys.size();
  for (std::size_t index = 0U; index < checked_count; ++index) {
    const auto& key = required_keys[index];
    const auto& leaf = value.leaves[index];
    const auto& shard = shards[index];
    require(
        leaf.domain_id == key.domain_id && leaf.shard_id == key.shard_id &&
            shard.domain_id == key.domain_id && shard.shard_id == key.shard_id,
        ErrorCode::coverage_incomplete,
        "aggregate root leaf is outside the required shard matrix");
    const auto shard_id = verify_shard(
        shard,
        input_set_certificate_id,
        eligibility_certificate_id,
        aggregation_plan_certificate_id);
    require_parent(
        leaf.parameter_shard_qc_id,
        shard_id,
        "aggregate root references the wrong parameter-shard QC");
  }
  return content_id(value);
}

std::string ChainVerifier::verify_apply(
    const ApplyQc& value,
    const ApplyCandidate& candidate,
    std::string_view aggregate_root_qc_id,
    std::string_view apply_profile_id) const {
  validate_context(value.context, expected_context_);
  validate_context(candidate.context, expected_context_);
  require_parent(value.aggregate_root_qc_id, aggregate_root_qc_id, "ApplyQC has wrong root parent");
  require_parent(
      candidate.aggregate_root_qc_id,
      aggregate_root_qc_id,
      "apply candidate has wrong root parent");
  require_parent(
      value.apply_arithmetic_profile_id, apply_profile_id, "ApplyQC has wrong arithmetic profile");
  require_parent(
      candidate.apply_arithmetic_profile_id,
      apply_profile_id,
      "apply candidate has wrong arithmetic profile");
  require_parent(
      value.apply_candidate_id, content_id(candidate), "ApplyQC has wrong candidate parent");
  require(
      value.parent_checkpoint_id == candidate.parent_checkpoint_id &&
          value.next_model_hash == candidate.next_model_hash &&
          value.next_optimizer_hash == candidate.next_optimizer_hash,
      ErrorCode::apply_conflict,
      "ApplyQC body differs from its candidate");
  validate_signers(value.signer_ids, value.quorum_threshold);
  return content_id(value);
}

void ChainVerifier::verify_timer(
    const OpaqueTimerToken& token,
    std::uint64_t observed_logical_tick) const {
  validate_context(token.context, expected_context_);
  require(
      is_label(token.action_id) && is_content_id(token.token_id) &&
          token.not_before_tick <= token.expires_at_tick,
      ErrorCode::identifier_invalid,
      "opaque native timer token is invalid");
  require(
      observed_logical_tick >= token.not_before_tick &&
          observed_logical_tick <= token.expires_at_tick,
      ErrorCode::stale_timer,
      "opaque timer was delivered early or stale");
}

}  // namespace delta::certificates
