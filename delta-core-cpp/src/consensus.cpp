#include <delta/core/consensus.hpp>

#include <algorithm>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <string_view>
#include <tuple>
#include <utility>
#include <vector>

namespace delta::core::consensus {
namespace {

[[noreturn]] void reject(ErrorCode code, const char* message) {
  throw ConsensusError(code, message);
}

void require(bool condition, ErrorCode code, const char* message) {
  if (!condition) {
    reject(code, message);
  }
}

void require_content_id(std::string_view value) {
  constexpr std::string_view prefix = "sha256:";
  require(value.size() == prefix.size() + 64U, ErrorCode::identifier_invalid, "content ID length");
  require(value.starts_with(prefix), ErrorCode::identifier_invalid, "content ID prefix");
  for (const char digit : value.substr(prefix.size())) {
    const bool valid = (digit >= '0' && digit <= '9') || (digit >= 'a' && digit <= 'f');
    require(valid, ErrorCode::identifier_invalid, "content ID hexadecimal digit");
  }
}

void require_id(std::string_view value) {
  require(!value.empty(), ErrorCode::identifier_invalid, "identifier is empty");
}

void require_strict_order(const std::vector<std::string>& values, ErrorCode code) {
  for (std::size_t index = 1; index < values.size(); ++index) {
    require(values[index - 1U] < values[index], code, "set is not strictly ordered");
  }
}

[[nodiscard]] auto vote_key(const protocol::Vote& vote) noexcept {
  return std::tie(
      vote.validator_id,
      vote.validator_epoch_id,
      vote.context_id);
}

void require_vote(const protocol::Vote& vote) {
  require_id(vote.validator_id);
  require_content_id(vote.validator_epoch_id);
  require_id(vote.kind);
  require_id(vote.round_id);
  require_id(vote.context_id);
  require_content_id(vote.body_hash);
  require_content_id(vote.signature_id);
  require(vote.durable_sequence > 0U, ErrorCode::vote_invalid, "durable vote sequence is zero");
}

void append_hash_text(core::canonical::Bytes& output, std::string_view value) {
  const auto length = static_cast<std::uint64_t>(value.size());
  for (std::size_t offset = sizeof(length); offset != 0U; --offset) {
    const auto shift = static_cast<unsigned>((offset - 1U) * 8U);
    output.push_back(static_cast<std::byte>((length >> shift) & 0xffU));
  }
  const auto bytes = std::as_bytes(std::span(value.data(), value.size()));
  output.insert(output.end(), bytes.begin(), bytes.end());
}

void append_hash_u64(core::canonical::Bytes& output, std::uint64_t value) {
  for (std::size_t offset = sizeof(value); offset != 0U; --offset) {
    const auto shift = static_cast<unsigned>((offset - 1U) * 8U);
    output.push_back(static_cast<std::byte>((value >> shift) & 0xffU));
  }
}

void append_hash_texts(
    core::canonical::Bytes& output,
    const std::vector<std::string>& values) {
  append_hash_u64(output, values.size());
  for (const auto& value : values) {
    append_hash_text(output, value);
  }
}

void append_hash_bool(core::canonical::Bytes& output, bool value) {
  output.push_back(value ? std::byte{1U} : std::byte{0U});
}

void append_hash_context(
    core::canonical::Bytes& output,
    const certificates::Context& value) {
  append_hash_text(output, value.arithmetic_profile_id);
  append_hash_u64(output, value.height);
  append_hash_text(output, value.parameter_schema_id);
  append_hash_text(output, value.round_config_id);
  append_hash_text(output, value.round_id);
  append_hash_text(output, value.validator_epoch_id);
  append_hash_u64(output, value.view);
}

void append_hash_rational(
    core::canonical::Bytes& output,
    const certificates::Rational& value) {
  append_hash_u64(output, std::bit_cast<std::uint64_t>(value.numerator));
  append_hash_u64(output, value.denominator);
}

void append_hash_input_tuples(
    core::canonical::Bytes& output,
    const std::vector<certificates::InputTuple>& values) {
  append_hash_u64(output, values.size());
  for (const auto& value : values) {
    append_hash_text(output, value.availability_certificate_id);
    append_hash_text(output, value.commitment_id);
    append_hash_text(output, value.domain_id);
    append_hash_text(output, value.ticket_id);
  }
}

void append_hash_eligibility_entries(
    core::canonical::Bytes& output,
    const std::vector<certificates::EligibilityEntry>& values) {
  append_hash_u64(output, values.size());
  for (const auto& value : values) {
    append_hash_bool(output, value.accepted);
    append_hash_text(output, value.domain_id);
    append_hash_rational(output, value.gamma);
    append_hash_text(output, value.reason_code);
    append_hash_text(output, value.ticket_id);
  }
}

void append_hash_bucket_assignments(
    core::canonical::Bytes& output,
    const std::vector<certificates::BucketAssignment>& values) {
  append_hash_u64(output, values.size());
  for (const auto& value : values) {
    append_hash_text(output, value.bucket_id);
    append_hash_text(output, value.ticket_id);
  }
}

void append_hash_weights(
    core::canonical::Bytes& output,
    const std::vector<certificates::Weight>& values) {
  append_hash_u64(output, values.size());
  for (const auto& value : values) {
    append_hash_rational(output, value.alpha);
    append_hash_text(output, value.ticket_id);
  }
}

void append_hash_root_leaves(
    core::canonical::Bytes& output,
    const std::vector<certificates::RootLeaf>& values) {
  append_hash_u64(output, values.size());
  for (const auto& value : values) {
    append_hash_text(output, value.domain_id);
    append_hash_text(output, value.parameter_shard_qc_id);
    append_hash_text(output, value.shard_id);
  }
}

void append_hash_shard_keys(
    core::canonical::Bytes& output,
    const std::vector<certificates::ShardKey>& values) {
  append_hash_u64(output, values.size());
  for (const auto& value : values) {
    append_hash_text(output, value.domain_id);
    append_hash_text(output, value.shard_id);
  }
}

[[nodiscard]] std::string authority_content_id(
    std::string_view domain,
    const core::canonical::Bytes& body) {
  core::canonical::Bytes input;
  input.reserve(domain.size() + 1U + body.size());
  const auto domain_bytes = std::as_bytes(std::span(domain.data(), domain.size()));
  input.insert(input.end(), domain_bytes.begin(), domain_bytes.end());
  input.push_back(std::byte{0U});
  input.insert(input.end(), body.begin(), body.end());
  return "sha256:" + core::canonical::sha256_hex(input);
}


[[nodiscard]] auto find_commitment(
    std::vector<Commitment>& commitments,
    std::string_view ticket_id) {
  return std::lower_bound(
      commitments.begin(),
      commitments.end(),
      ticket_id,
      [](const Commitment& item, std::string_view key) { return item.ticket_id < key; });
}

[[nodiscard]] auto find_availability(
    std::vector<AvailabilityProof>& proofs,
    std::string_view ticket_id) {
  return std::lower_bound(
      proofs.begin(),
      proofs.end(),
      ticket_id,
      [](const AvailabilityProof& item, std::string_view key) { return item.ticket_id < key; });
}

void require_canonical_content_ids(const std::vector<std::string>& values, ErrorCode code) {
  require(!values.empty(), code, "content ID set is empty");
  require_strict_order(values, code);
  for (const auto& value : values) {
    require_content_id(value);
  }
}

void require_canonical_ids(const std::vector<std::string>& values, ErrorCode code) {
  require(!values.empty(), code, "identifier set is empty");
  require_strict_order(values, code);
  for (const auto& value : values) {
    require_id(value);
  }
}

}  // namespace

std::string_view vote_kind_name(VoteAction action) noexcept {
  switch (action) {
    case VoteAction::round_config:
      return "ROUND_CONFIG";
    case VoteAction::input_set:
      return "ISC";
    case VoteAction::eligibility:
      return "EC";
    case VoteAction::aggregation_plan:
      return "APC";
    case VoteAction::parameter:
      return "PARAMETER";
    case VoteAction::aggregate_root:
      return "AGGREGATE_ROOT";
    case VoteAction::apply:
      return "APPLY";
    case VoteAction::view_change:
      return "VIEW_CHANGE";
    case VoteAction::abort:
      return "ABORT";
  }
  return "UNKNOWN";
}

std::string_view vote_formal_action_id(VoteAction action) noexcept {
  switch (action) {
    case VoteAction::round_config:
      return "ACT-CONFIG-VOTE";
    case VoteAction::input_set:
      return "ACT-ISC-VOTE";
    case VoteAction::eligibility:
      return "ACT-EC-VOTE";
    case VoteAction::aggregation_plan:
      return "ACT-APC-VOTE";
    case VoteAction::parameter:
      return "ACT-PARAM-VOTE";
    case VoteAction::aggregate_root:
      return "ACT-ROOT-VOTE";
    case VoteAction::apply:
      return "ACT-APPLY-VOTE";
    case VoteAction::view_change:
      return "ACT-VIEW-VOTE";
    case VoteAction::abort:
      return "ACT-ABORT-VOTE";
  }
  return "UNKNOWN";
}

VoteAction parse_vote_action(std::string_view kind) {
  for (std::uint32_t value = static_cast<std::uint32_t>(VoteAction::round_config);
       value <= static_cast<std::uint32_t>(VoteAction::abort);
       ++value) {
    const auto action = static_cast<VoteAction>(value);
    if (kind == vote_kind_name(action)) {
      return action;
    }
  }
  reject(ErrorCode::vote_action_invalid, "vote kind has no accepted formal action");
}

bool is_configured_abort_reason(std::string_view reason) noexcept {
  return reason == "HARD_DEADLINE" || reason == "INCOMPLETE_INPUT" ||
         reason == "UNSAFE_COEFFICIENTS" ||
         reason == "IRRECOVERABLE_AVAILABILITY" || reason == "PARAMETER_FAILURE" ||
         reason == "APPLY_FAILURE";
}

std::string_view frozen_vote_context(const VoteCandidateBinding& candidate) noexcept {
  return candidate.context_id;
}

std::string vote_context_id(
    VoteAction action,
    std::string_view round_id,
    std::uint64_t height,
    std::uint64_t view,
    std::string_view validator_epoch_id,
    std::string_view formal_parent_or_assignment) {
  core::canonical::Bytes encoded;
  switch (action) {
    case VoteAction::round_config:
      require_content_id(validator_epoch_id);
      append_hash_u64(encoded, height);
      append_hash_text(encoded, validator_epoch_id);
      return authority_content_id("deltareduce.vote-context.config.v1", encoded);
    case VoteAction::input_set:
      require_id(round_id);
      append_hash_text(encoded, round_id);
      return authority_content_id("deltareduce.vote-context.isc.v1", encoded);
    case VoteAction::eligibility:
      require_content_id(formal_parent_or_assignment);
      append_hash_text(encoded, formal_parent_or_assignment);
      return authority_content_id("deltareduce.vote-context.ec.v1", encoded);
    case VoteAction::aggregation_plan:
      require_content_id(formal_parent_or_assignment);
      append_hash_text(encoded, formal_parent_or_assignment);
      return authority_content_id("deltareduce.vote-context.apc.v1", encoded);
    case VoteAction::parameter:
      require_id(formal_parent_or_assignment);
      return std::string(formal_parent_or_assignment);
    case VoteAction::aggregate_root:
      require_content_id(formal_parent_or_assignment);
      append_hash_text(encoded, formal_parent_or_assignment);
      return authority_content_id("deltareduce.vote-context.root.v1", encoded);
    case VoteAction::apply:
      require_content_id(formal_parent_or_assignment);
      append_hash_text(encoded, formal_parent_or_assignment);
      return authority_content_id("deltareduce.vote-context.apply.v1", encoded);
    case VoteAction::view_change:
      require_id(round_id);
      append_hash_text(encoded, round_id);
      append_hash_u64(encoded, view);
      return authority_content_id("deltareduce.vote-context.view.v1", encoded);
    case VoteAction::abort:
      require_id(round_id);
      append_hash_text(encoded, round_id);
      return authority_content_id("deltareduce.vote-context.abort.v1", encoded);
  }
  reject(ErrorCode::vote_action_invalid, "vote action has no formal context");
}

VoteInputSetBody project_input_set_vote_body(
    const certificates::InputSetCertificate& certificate) {
  return VoteInputSetBody{
      certificate.context,
      certificate.input_root,
      certificate.tuples,
  };
}

VoteEligibilityBody project_eligibility_vote_body(
    const certificates::EligibilityCertificate& certificate,
    std::string seed_transcript_id) {
  return VoteEligibilityBody{
      certificate.context,
      certificate.entries,
      certificate.input_set_certificate_id,
      certificate.norm_evidence_id,
      certificate.robust_profile_id,
      std::move(seed_transcript_id),
  };
}

VoteAggregationPlanBody project_aggregation_plan_vote_body(
    const certificates::AggregationPlanCertificate& certificate) {
  return VoteAggregationPlanBody{
      certificate.context,
      certificate.accumulator_proof_id,
      certificate.bucket_assignments,
      certificate.eligibility_certificate_id,
      certificate.input_set_certificate_id,
      certificate.iteration_count,
      certificate.seed_transcript_id,
      certificate.transcript_root,
      certificate.weights,
  };
}

VoteParameterBody project_parameter_vote_body(
    const certificates::ParameterShardQc& certificate,
    std::string assignment_vote_context_id) {
  return VoteParameterBody{
      certificate.context,
      certificate.aggregation_plan_certificate_id,
      certificate.denominator,
      certificate.domain_id,
      certificate.eligibility_certificate_id,
      certificate.input_leaf_ids,
      certificate.input_set_certificate_id,
      certificate.result_numerators,
      certificate.shard_id,
      std::move(assignment_vote_context_id),
  };
}

VoteAggregateRootBody project_aggregate_root_vote_body(
    const certificates::AggregateRootQc& certificate) {
  return VoteAggregateRootBody{
      certificate.context,
      certificate.aggregation_plan_certificate_id,
      certificate.eligibility_certificate_id,
      certificate.input_set_certificate_id,
      certificate.leaves,
      certificate.merkle_root,
      certificate.required_keys,
  };
}

std::string vote_input_set_body_id(const VoteInputSetBody& body) {
  core::canonical::Bytes encoded;
  append_hash_context(encoded, body.context);
  append_hash_text(encoded, body.input_root);
  append_hash_input_tuples(encoded, body.tuples);
  return authority_content_id("deltareduce.vote.input-set-body.v1", encoded);
}

std::string vote_eligibility_body_id(const VoteEligibilityBody& body) {
  core::canonical::Bytes encoded;
  append_hash_context(encoded, body.context);
  append_hash_eligibility_entries(encoded, body.entries);
  append_hash_text(encoded, body.input_set_certificate_id);
  append_hash_text(encoded, body.norm_evidence_id);
  append_hash_text(encoded, body.robust_profile_id);
  append_hash_text(encoded, body.seed_transcript_id);
  return authority_content_id("deltareduce.vote.eligibility-body.v1", encoded);
}

std::string vote_aggregation_plan_body_id(const VoteAggregationPlanBody& body) {
  core::canonical::Bytes encoded;
  append_hash_context(encoded, body.context);
  append_hash_text(encoded, body.accumulator_proof_id);
  append_hash_bucket_assignments(encoded, body.bucket_assignments);
  append_hash_text(encoded, body.eligibility_certificate_id);
  append_hash_text(encoded, body.input_set_certificate_id);
  append_hash_u64(encoded, body.iteration_count);
  append_hash_text(encoded, body.seed_transcript_id);
  append_hash_text(encoded, body.transcript_root);
  append_hash_weights(encoded, body.weights);
  return authority_content_id("deltareduce.vote.aggregation-plan-body.v1", encoded);
}

std::string vote_parameter_body_id(const VoteParameterBody& body) {
  core::canonical::Bytes encoded;
  append_hash_context(encoded, body.context);
  append_hash_text(encoded, body.aggregation_plan_certificate_id);
  append_hash_u64(encoded, body.denominator);
  append_hash_text(encoded, body.domain_id);
  append_hash_text(encoded, body.eligibility_certificate_id);
  append_hash_texts(encoded, body.input_leaf_ids);
  append_hash_text(encoded, body.input_set_certificate_id);
  append_hash_texts(encoded, body.result_numerators);
  append_hash_text(encoded, body.shard_id);
  return authority_content_id("deltareduce.vote.parameter-body.v1", encoded);
}

std::string vote_aggregate_root_body_id(const VoteAggregateRootBody& body) {
  core::canonical::Bytes encoded;
  append_hash_context(encoded, body.context);
  append_hash_text(encoded, body.aggregation_plan_certificate_id);
  append_hash_text(encoded, body.eligibility_certificate_id);
  append_hash_text(encoded, body.input_set_certificate_id);
  append_hash_root_leaves(encoded, body.leaves);
  append_hash_text(encoded, body.merkle_root);
  append_hash_shard_keys(encoded, body.required_keys);
  return authority_content_id("deltareduce.vote.aggregate-root-body.v1", encoded);
}

std::string vote_view_change_body_id(const VoteViewChangeBody& body) {
  core::canonical::Bytes encoded;
  append_hash_text(encoded, body.round_id);
  append_hash_u64(encoded, body.height);
  append_hash_u64(encoded, body.from_view);
  append_hash_u64(encoded, body.to_view);
  append_hash_u64(encoded, body.soft_deadline_tick);
  return authority_content_id("deltareduce.vote.view-change-body.v1", encoded);
}

std::string vote_abort_body_id(const VoteAbortBody& body) {
  core::canonical::Bytes encoded;
  append_hash_text(encoded, body.round_id);
  append_hash_text(encoded, body.validator_epoch_id);
  append_hash_u64(encoded, body.height);
  append_hash_u64(encoded, body.view);
  append_hash_u64(encoded, body.hard_deadline_tick);
  append_hash_text(encoded, body.parent_checkpoint_id);
  append_hash_text(encoded, body.reason_code);
  append_hash_texts(encoded, body.round_config_ids);
  append_hash_texts(encoded, body.input_set_ids);
  append_hash_texts(encoded, body.eligibility_ids);
  append_hash_texts(encoded, body.aggregation_plan_ids);
  append_hash_texts(encoded, body.parameter_ids);
  append_hash_texts(encoded, body.aggregate_root_ids);
  append_hash_texts(encoded, body.apply_ids);
  return authority_content_id("deltareduce.vote.abort-body.v1", encoded);
}


ConsensusError::ConsensusError(ErrorCode code, std::string message)
    : std::runtime_error(std::move(message)), code_(code) {}

ErrorCode ConsensusError::code() const noexcept { return code_; }

Disposition VoteJournal::record(const protocol::Vote& vote) {
  // The durable uniqueness key is validated and classified before any
  // non-key vote field. Once a key exists, every canonically decoded byte
  // change is a conflict even when the changed kind/body would independently
  // fail admission. This keeps equivocation classification stable.
  require_id(vote.validator_id);
  require_content_id(vote.validator_epoch_id);
  require_id(vote.context_id);
  const auto found = std::lower_bound(
      votes_.begin(), votes_.end(), vote, [](const protocol::Vote& left, const protocol::Vote& right) {
        return vote_key(left) < vote_key(right);
      });
  if (found != votes_.end() && vote_key(*found) == vote_key(vote)) {
#if defined(DELTA_RECORD_VOTE_MUTANT_SKIP_CONFLICT)
    static_cast<void>(vote);
#else
    require(
        *found == vote,
        ErrorCode::conflicting_vote,
        "validator attempted different canonical vote bytes in one context");
#endif
    return Disposition::replay;
  }
  require_vote(vote);
  votes_.insert(found, vote);
  return Disposition::recorded;
}

const std::vector<protocol::Vote>& VoteJournal::votes() const noexcept { return votes_; }

void validate_quorum(const protocol::QuorumCertificate& certificate, const QuorumPolicy& policy) {
  require_canonical_ids(policy.validator_ids, ErrorCode::validator_set_invalid);
  require_content_id(policy.validator_epoch_id);
  require(
      (policy.validator_ids.size() % 3U) == 1U,
      ErrorCode::validator_set_invalid,
      "validator count is not 3f+1");
  const auto fault_tolerance = (policy.validator_ids.size() - 1U) / 3U;
  const auto required_threshold = 2U * fault_tolerance + 1U;
  require(
      policy.quorum_threshold == required_threshold &&
          certificate.quorum_threshold == policy.quorum_threshold,
      ErrorCode::quorum_policy_mismatch,
      "quorum threshold differs from 2f+1");
  require(
      certificate.validator_epoch_id == policy.validator_epoch_id,
      ErrorCode::quorum_policy_mismatch,
      "certificate validator epoch mismatch");
  require_content_id(certificate.body_hash);
  require_content_id(certificate.qc_id);
  require_id(certificate.context_id);
  require_id(certificate.kind);
  require_id(certificate.round_id);
  require_strict_order(certificate.signer_ids, ErrorCode::signer_set_invalid);
  require(
      certificate.signer_ids.size() >= policy.quorum_threshold &&
          certificate.signer_ids.size() == certificate.vote_ids.size(),
      ErrorCode::signer_set_invalid,
      "certificate signer/vote set is insufficient");
  for (const auto& signer : certificate.signer_ids) {
    require(
        std::binary_search(policy.validator_ids.begin(), policy.validator_ids.end(), signer),
        ErrorCode::unknown_signer,
        "certificate includes an unknown signer");
  }
  for (std::size_t left = 0; left < certificate.vote_ids.size(); ++left) {
    require_content_id(certificate.vote_ids[left]);
    for (std::size_t right = left + 1U; right < certificate.vote_ids.size(); ++right) {
      require(
          certificate.vote_ids[left] != certificate.vote_ids[right],
          ErrorCode::signer_set_invalid,
          "certificate includes a duplicate vote");
    }
  }
}

InputLedger::InputLedger(std::vector<std::string> permitted_ticket_ids)
    : permitted_ticket_ids_(std::move(permitted_ticket_ids)) {
  require_canonical_ids(permitted_ticket_ids_, ErrorCode::ticket_set_invalid);
}

Disposition InputLedger::record_commitment(Commitment commitment) {
  require_id(commitment.ticket_id);
  require_content_id(commitment.commitment_id);
  require(
      std::binary_search(
          permitted_ticket_ids_.begin(), permitted_ticket_ids_.end(), commitment.ticket_id),
      ErrorCode::unknown_ticket,
      "commitment references a ticket outside the configured set");
  auto found = find_commitment(commitments_, commitment.ticket_id);
  if (found != commitments_.end() && found->ticket_id == commitment.ticket_id) {
    require(
        found->commitment_id == commitment.commitment_id,
        ErrorCode::commitment_equivocation,
        "ticket already binds a different commitment");
    return Disposition::replay;
  }
  if (frozen_) {
    const auto late = find_commitment(late_commitments_, commitment.ticket_id);
    if (late != late_commitments_.end() && late->ticket_id == commitment.ticket_id) {
      require(
          late->commitment_id == commitment.commitment_id,
          ErrorCode::commitment_equivocation,
          "late ticket evidence contains conflicting commitments");
      return Disposition::late;
    }
    late_commitments_.insert(late, std::move(commitment));
    return Disposition::late;
  }
  commitments_.insert(found, std::move(commitment));
  return Disposition::recorded;
}

Disposition InputLedger::record_availability(
    AvailabilityProof proof,
    const std::vector<std::string>& required_leaf_ids,
    const std::vector<std::string>& permitted_attester_ids,
    std::uint32_t required_threshold) {
  require_id(proof.ticket_id);
  require_content_id(proof.commitment_id);
  require_content_id(proof.certificate_id);
  require_canonical_content_ids(
      required_leaf_ids, ErrorCode::availability_coverage_incomplete);
  require_canonical_content_ids(
      proof.covered_leaf_ids, ErrorCode::availability_coverage_incomplete);
  require(
      proof.covered_leaf_ids == required_leaf_ids,
      ErrorCode::availability_coverage_incomplete,
      "availability proof does not cover the exact required leaf set");
  require_canonical_ids(permitted_attester_ids, ErrorCode::availability_attesters_invalid);
  require_canonical_ids(proof.attester_ids, ErrorCode::availability_attesters_invalid);
  require(
      required_threshold > 0U && proof.threshold == required_threshold &&
          proof.attester_ids.size() >= required_threshold,
      ErrorCode::availability_attesters_invalid,
      "availability attester quorum is insufficient");
  for (const auto& attester : proof.attester_ids) {
    require(
        std::binary_search(
            permitted_attester_ids.begin(), permitted_attester_ids.end(), attester),
        ErrorCode::availability_attesters_invalid,
        "availability proof includes an unknown attester");
  }

  const auto commitment = find_commitment(commitments_, proof.ticket_id);
  require(
      commitment != commitments_.end() && commitment->ticket_id == proof.ticket_id,
      ErrorCode::commitment_missing,
      "availability proof has no commitment");
  require(
      commitment->commitment_id == proof.commitment_id,
      ErrorCode::availability_commitment_mismatch,
      "availability proof references a different commitment");
  auto found = find_availability(availabilities_, proof.ticket_id);
  if (found != availabilities_.end() && found->ticket_id == proof.ticket_id) {
    require(
        *found == proof,
        ErrorCode::availability_conflict,
        "ticket already has different availability evidence");
    return Disposition::replay;
  }
  if (frozen_) {
    const auto late = find_availability(late_availabilities_, proof.ticket_id);
    if (late != late_availabilities_.end() && late->ticket_id == proof.ticket_id) {
      require(
          *late == proof,
          ErrorCode::availability_conflict,
          "late ticket evidence contains conflicting availability proofs");
      return Disposition::late;
    }
    late_availabilities_.insert(late, std::move(proof));
    return Disposition::late;
  }
  availabilities_.insert(found, std::move(proof));
  return Disposition::recorded;
}

const std::vector<FrozenInput>& InputLedger::freeze() {
  if (frozen_) {
    return frozen_inputs_;
  }
  require(!availabilities_.empty(), ErrorCode::input_set_empty, "no available input to freeze");
  frozen_inputs_.reserve(availabilities_.size());
  for (const auto& proof : availabilities_) {
    const auto commitment = find_commitment(commitments_, proof.ticket_id);
    require(
        commitment != commitments_.end() && commitment->ticket_id == proof.ticket_id &&
            commitment->commitment_id == proof.commitment_id,
        ErrorCode::availability_commitment_mismatch,
        "availability changed after validation");
    frozen_inputs_.push_back(FrozenInput{
        proof.ticket_id,
        proof.commitment_id,
        proof.certificate_id,
    });
  }
  frozen_ = true;
  return frozen_inputs_;
}

bool InputLedger::frozen() const noexcept { return frozen_; }

const std::vector<Commitment>& InputLedger::commitments() const noexcept { return commitments_; }

const std::vector<AvailabilityProof>& InputLedger::availabilities() const noexcept {
  return availabilities_;
}

const std::vector<FrozenInput>& InputLedger::frozen_inputs() const noexcept {
  return frozen_inputs_;
}

std::size_t InputLedger::late_commitment_count() const noexcept {
  return late_commitments_.size();
}

std::size_t InputLedger::late_availability_count() const noexcept {
  return late_availabilities_.size();
}

}  // namespace delta::core::consensus
