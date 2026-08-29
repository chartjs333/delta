#pragma once

#include <delta/certificates/contracts.hpp>

#include <cstdint>
#include <span>
#include <string>
#include <vector>

namespace delta::robust {

struct Contribution {
  std::string domain_id;
  std::vector<std::int64_t> q_values;
  std::string ticket_id;
};

struct Profile {
  std::string accumulator_proof_id;
  std::uint32_t bucket_count;
  std::uint32_t iteration_count;
  std::uint32_t trim_highest;
  std::uint64_t coefficient_denominator;
  std::int64_t maximum_absolute_q;
  std::uint64_t maximum_eligible_tickets;
};

struct PlanResult {
  certificates::NormEvidence norms;
  certificates::EligibilityCertificate eligibility;
  certificates::AggregationPlanCertificate plan;
};

[[nodiscard]] std::int64_t exact_squared_norm(std::span<const std::int64_t> values);
[[nodiscard]] PlanResult build_plan(
    const certificates::Context& context,
    std::string input_set_certificate_id,
    std::string seed_transcript_id,
    std::string robust_profile_id,
    std::string seed_id,
    std::span<const Contribution> contributions,
    const Profile& profile,
    std::vector<std::string> signer_ids,
    std::uint32_t quorum_threshold);

[[nodiscard]] certificates::ParameterShardQc reduce_parameter_shard(
    const certificates::Context& context,
    std::string input_set_certificate_id,
    std::string eligibility_certificate_id,
    const certificates::AggregationPlanCertificate& plan,
    std::string domain_id,
    std::string shard_id,
    std::span<const Contribution> contributions,
    std::vector<std::string> input_leaf_ids,
    std::vector<std::string> signer_ids,
    std::uint32_t quorum_threshold);

}  // namespace delta::robust
