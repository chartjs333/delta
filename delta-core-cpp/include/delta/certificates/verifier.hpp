#pragma once

#include <delta/certificates/contracts.hpp>
#include <delta/core/consensus.hpp>
#include <delta/core/protocol.hpp>

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

namespace delta::certificates {

enum class VoteKind {
  input_set,
  eligibility,
  aggregation_plan,
  parameter_shard,
  aggregate_root,
  apply,
};

[[nodiscard]] std::string_view vote_kind_name(VoteKind kind) noexcept;

struct ValidatorPolicy {
  std::string validator_epoch_id;
  std::vector<std::string> validator_ids;
  std::uint32_t quorum_threshold;
};

struct OpaqueTimerToken {
  Context context;
  std::string action_id;
  std::uint64_t not_before_tick;
  std::uint64_t expires_at_tick;
  std::string token_id;
};

[[nodiscard]] core::protocol::Vote make_vote(
    VoteKind kind,
    const Context& context,
    std::string body_id,
    std::string validator_id,
    std::string signature_id,
    std::uint64_t durable_sequence);

class ChainVerifier final {
 public:
  ChainVerifier(Context expected_context, ValidatorPolicy validators);

  [[nodiscard]] std::string verify_input_set(const InputSetCertificate& value) const;
  [[nodiscard]] std::string verify_seed(
      const SeedTranscript& value,
      std::string_view input_set_certificate_id) const;
  [[nodiscard]] std::string verify_norms(
      const NormEvidence& value,
      std::string_view input_set_certificate_id) const;
  [[nodiscard]] std::string verify_eligibility(
      const EligibilityCertificate& value,
      const InputSetCertificate& input_set,
      std::string_view norm_evidence_id) const;
  [[nodiscard]] std::string verify_plan(
      const AggregationPlanCertificate& value,
      const InputSetCertificate& input_set,
      const EligibilityCertificate& eligibility,
      std::string_view seed_transcript_id,
      std::string_view required_accumulator_proof_id) const;
  [[nodiscard]] std::string verify_shard(
      const ParameterShardQc& value,
      std::string_view input_set_certificate_id,
      std::string_view eligibility_certificate_id,
      std::string_view aggregation_plan_certificate_id) const;
  [[nodiscard]] std::string verify_root(
      const AggregateRootQc& value,
      std::string_view input_set_certificate_id,
      std::string_view eligibility_certificate_id,
      std::string_view aggregation_plan_certificate_id,
      const std::vector<ShardKey>& required_keys,
      const std::vector<ParameterShardQc>& shards) const;
  [[nodiscard]] std::string verify_apply(
      const ApplyQc& value,
      const ApplyCandidate& candidate,
      std::string_view aggregate_root_qc_id,
      std::string_view apply_profile_id) const;
  void verify_timer(const OpaqueTimerToken& token, std::uint64_t observed_logical_tick) const;

 private:
  void validate_signers(
      const std::vector<std::string>& signer_ids,
      std::uint32_t threshold) const;

  Context expected_context_;
  ValidatorPolicy validators_;
};

}  // namespace delta::certificates
