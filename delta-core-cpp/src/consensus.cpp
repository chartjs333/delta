#include <delta/core/consensus.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
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
      vote.kind,
      vote.round_id,
      vote.height,
      vote.view,
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

[[nodiscard]] auto find_commitment(
    std::vector<Commitment>& commitments,
    std::string_view ticket_id) {
  return std::lower_bound(
      commitments.begin(),
      commitments.end(),
      ticket_id,
      [](const Commitment& item, std::string_view key) { return item.ticket_id < key; });
}

[[nodiscard]] auto find_commitment(
    const std::vector<Commitment>& commitments,
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

ConsensusError::ConsensusError(ErrorCode code, std::string message)
    : std::runtime_error(std::move(message)), code_(code) {}

ErrorCode ConsensusError::code() const noexcept { return code_; }

Disposition VoteJournal::record(const protocol::Vote& vote) {
  require_vote(vote);
  const auto found = std::lower_bound(
      votes_.begin(), votes_.end(), vote, [](const protocol::Vote& left, const protocol::Vote& right) {
        return vote_key(left) < vote_key(right);
      });
  if (found != votes_.end() && vote_key(*found) == vote_key(vote)) {
    require(
        found->body_hash == vote.body_hash,
        ErrorCode::conflicting_vote,
        "validator attempted a conflicting vote in one context");
    return Disposition::replay;
  }
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
