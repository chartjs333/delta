#pragma once

#include <delta/core/protocol.hpp>

#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <vector>

namespace delta::core::consensus {

enum class ErrorCode {
  validator_set_invalid,
  quorum_policy_mismatch,
  unknown_signer,
  signer_set_invalid,
  conflicting_vote,
  vote_invalid,
  identifier_invalid,
  ticket_set_invalid,
  unknown_ticket,
  commitment_equivocation,
  commitment_missing,
  availability_commitment_mismatch,
  availability_coverage_incomplete,
  availability_attesters_invalid,
  availability_conflict,
  input_set_empty,
};

class ConsensusError final : public std::runtime_error {
 public:
  ConsensusError(ErrorCode code, std::string message);

  [[nodiscard]] ErrorCode code() const noexcept;

 private:
  ErrorCode code_;
};

enum class Disposition {
  recorded,
  replay,
  late,
};

class VoteJournal {
 public:
  [[nodiscard]] Disposition record(const protocol::Vote& vote);
  [[nodiscard]] const std::vector<protocol::Vote>& votes() const noexcept;

 private:
  std::vector<protocol::Vote> votes_;
};

struct QuorumPolicy {
  std::string validator_epoch_id;
  std::vector<std::string> validator_ids;
  std::uint32_t quorum_threshold;
};

void validate_quorum(const protocol::QuorumCertificate& certificate, const QuorumPolicy& policy);

struct Commitment {
  std::string ticket_id;
  std::string commitment_id;

  bool operator==(const Commitment&) const = default;
};

struct AvailabilityProof {
  std::string ticket_id;
  std::string commitment_id;
  std::string certificate_id;
  std::vector<std::string> covered_leaf_ids;
  std::vector<std::string> attester_ids;
  std::uint32_t threshold;

  bool operator==(const AvailabilityProof&) const = default;
};

struct FrozenInput {
  std::string ticket_id;
  std::string commitment_id;
  std::string availability_certificate_id;

  bool operator==(const FrozenInput&) const = default;
};

class InputLedger {
 public:
  explicit InputLedger(std::vector<std::string> permitted_ticket_ids);

  [[nodiscard]] Disposition record_commitment(Commitment commitment);
  [[nodiscard]] Disposition record_availability(
      AvailabilityProof proof,
      const std::vector<std::string>& required_leaf_ids,
      const std::vector<std::string>& permitted_attester_ids,
      std::uint32_t required_threshold);
  [[nodiscard]] const std::vector<FrozenInput>& freeze();

  [[nodiscard]] bool frozen() const noexcept;
  [[nodiscard]] const std::vector<Commitment>& commitments() const noexcept;
  [[nodiscard]] const std::vector<AvailabilityProof>& availabilities() const noexcept;
  [[nodiscard]] const std::vector<FrozenInput>& frozen_inputs() const noexcept;
  [[nodiscard]] std::size_t late_commitment_count() const noexcept;
  [[nodiscard]] std::size_t late_availability_count() const noexcept;

 private:
  std::vector<std::string> permitted_ticket_ids_;
  std::vector<Commitment> commitments_;
  std::vector<AvailabilityProof> availabilities_;
  std::vector<FrozenInput> frozen_inputs_;
  std::vector<Commitment> late_commitments_;
  std::vector<AvailabilityProof> late_availabilities_;
  bool frozen_ = false;
};

}  // namespace delta::core::consensus
