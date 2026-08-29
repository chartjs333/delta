#pragma once

#include <delta/scheduling/contracts.hpp>

#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <vector>

namespace delta::scheduling {

struct CapabilityProfile {
  std::string arithmetic_profile_id;
  std::uint64_t complete_ticket_throughput_milli;
  std::uint64_t expires_at_tick;
  std::uint64_t identity_epoch;
  std::uint64_t max_concurrent_leases;
  std::uint64_t measured_at_tick;
  std::string measurement_artifact_id;
  std::uint64_t memory_bytes;
  std::string model_mode;
  std::string parameter_schema_id;
  std::string region_id;
  std::string round_config_id;
  std::uint64_t sample_count;
  std::string signature_id;
  std::string software_build_id;
  std::string worker_id;

  bool operator==(const CapabilityProfile&) const = default;
};

struct EligibilityPolicy {
  std::vector<std::string> allowed_domain_ids;
  std::vector<std::string> allowed_region_ids;
  std::vector<std::string> allowed_software_build_ids;
  std::string arithmetic_profile_id;
  std::uint64_t decision_tick;
  std::string eligibility_policy_id;
  std::uint64_t identity_epoch;
  std::uint64_t minimum_memory_bytes;
  std::uint64_t minimum_sample_count;
  std::string model_mode;
  std::string parameter_schema_id;
  std::string round_config_id;
  std::vector<std::string> trusted_signature_ids;
};

struct EligibilityDecision {
  std::vector<std::string> allowed_domain_ids;
  std::string capability_profile_id;
  std::uint64_t decision_tick;
  std::string eligibility_policy_id;
  bool eligible;
  std::uint64_t max_concurrent_leases;
  std::vector<std::string> reason_codes;
  std::string region_route;
  std::string round_config_id;
  std::string worker_id;

  bool operator==(const EligibilityDecision&) const = default;
};

struct EligibilityRecord {
  CapabilityProfile profile;
  std::vector<std::byte> profile_bytes;
  std::string profile_id;
  EligibilityDecision decision;
  std::vector<std::byte> decision_bytes;
  std::string decision_id;
};

[[nodiscard]] CapabilityProfile parse_capability_profile(
    std::span<const std::byte> canonical_json,
    const Limits& limits = {});
[[nodiscard]] std::vector<std::byte> canonical_capability_profile(
    const CapabilityProfile& profile);
[[nodiscard]] std::string capability_profile_content_id(
    std::span<const std::byte> canonical_json);
[[nodiscard]] EligibilityRecord evaluate_capability(
    const CapabilityProfile& profile,
    const EligibilityPolicy& policy);
[[nodiscard]] std::vector<std::byte> canonical_eligibility_decision(
    const EligibilityDecision& decision);
[[nodiscard]] std::string eligibility_decision_content_id(
    std::span<const std::byte> canonical_json);

}  // namespace delta::scheduling
