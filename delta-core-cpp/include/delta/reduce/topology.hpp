#pragma once

#include <delta/core/arithmetic.hpp>

#include <cstddef>
#include <cstdint>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace delta::reduce {

enum class ErrorCode {
  input_too_large,
  canonical_json_invalid,
  field_set_invalid,
  identifier_invalid,
  context_mismatch,
  deadline_invalid,
  partition_invalid,
  shard_coverage_invalid,
  committee_invalid,
  proof_invalid,
  contribution_invalid,
  result_conflict,
  required_result_missing,
  quorum_invalid,
  assembly_incomplete,
};

class ReduceError final : public std::runtime_error {
 public:
  ReduceError(ErrorCode code, std::string message);

  [[nodiscard]] ErrorCode code() const noexcept;

 private:
  ErrorCode code_;
};

struct Limits {
  std::size_t topology_bytes = 1U * 1024U * 1024U;
  std::size_t proof_bytes = 256U * 1024U;
  std::size_t nesting_depth = 16U;
  std::size_t collection_members = 16'384U;
  std::size_t domains = 256U;
  std::size_t regions_per_domain = 256U;
  std::size_t tickets_per_domain = 1'000'000U;
  std::size_t shards = 4'096U;
  std::size_t validators_per_committee = 4'096U;
};

struct Context {
  std::string accumulator_proof_instance_id;
  std::string coefficient_plan_root;
  std::string fixedpoint_config_id;
  std::string formal_semantics_id;
  std::string frozen_input_root;
  std::string parent_checkpoint_id;
  std::string profile_id;
  std::string round_config_id;
  std::string scale_table_id;
  std::string shard_plan_id;

  bool operator==(const Context&) const = default;
};

struct ParameterShard {
  std::uint64_t end_element;
  std::string shard_id;
  std::uint64_t start_element;

  bool operator==(const ParameterShard&) const = default;
};

struct Region {
  std::uint32_t fault_bound;
  std::string region_id;
  std::vector<std::string> tickets;
  std::vector<std::string> validator_set;

  bool operator==(const Region&) const = default;
};

struct Domain {
  std::string domain_id;
  std::uint32_t global_fault_bound;
  std::vector<std::string> global_validator_set;
  std::vector<Region> regions;
  std::vector<std::string> tickets;

  bool operator==(const Domain&) const = default;
};

struct Topology {
  Context context;
  std::vector<Domain> domains;
  std::uint64_t hard_deadline_tick;
  std::vector<ParameterShard> shards;
  std::uint64_t soft_deadline_tick;
  std::uint64_t validator_epoch;
  std::string topology_id;

  bool operator==(const Topology&) const = default;
};

struct TheoremBinding {
  std::string obligation_id;
  std::vector<std::string> conjuncts;

  bool operator==(const TheoremBinding&) const = default;
};

struct HierarchyProofInstance {
  std::string hierarchy_proof_instance_id;
  std::string topology_id;
  Context context;
  std::uint64_t coefficient_abs_max;
  std::uint64_t common_denominator;
  std::uint64_t max_eligible_contributions;
  delta::core::arithmetic::Int128 product_abs_bound;
  delta::core::arithmetic::Int128 final_abs_bound;
  std::uint64_t q_abs_max;
  delta::core::arithmetic::AccumulatorWidth selected_width;
  std::vector<std::pair<std::string, std::uint64_t>> domain_ticket_counts;
  std::vector<std::pair<std::uint64_t, std::uint64_t>> shard_ranges;
  std::vector<TheoremBinding> theorem_bindings;
};

struct CoefficientBinding {
  std::string domain_id;
  std::string ticket_id;
  std::int64_t numerator;
  std::uint64_t denominator;

  bool operator==(const CoefficientBinding&) const = default;
};

struct BoundValidation {
  std::size_t checked_coefficients;
  std::uint64_t maximum_regional_terms;
  std::uint64_t maximum_global_terms;
  delta::core::arithmetic::Int128 maximum_product_abs;
  delta::core::arithmetic::Int128 maximum_accumulator_abs;

  bool operator==(const BoundValidation&) const = default;
};

[[nodiscard]] Topology parse_topology(
    std::span<const std::byte> canonical_json,
    const Context& expected_context,
    const Limits& limits = {});
[[nodiscard]] HierarchyProofInstance parse_hierarchy_proof(
    std::span<const std::byte> canonical_json,
    const Topology& topology,
    const Limits& limits = {});
void validate_topology(const Topology& topology, const Limits& limits = {});
void validate_hierarchy_proof(
    const Topology& topology,
    const HierarchyProofInstance& proof);
[[nodiscard]] BoundValidation validate_coefficient_plan(
    const Topology& topology,
    const HierarchyProofInstance& proof,
    std::span<const CoefficientBinding> coefficients);

[[nodiscard]] std::string topology_content_id(std::span<const std::byte> canonical_json);
[[nodiscard]] std::string hierarchy_proof_content_id(
    std::span<const std::byte> canonical_json);
[[nodiscard]] const Domain& require_domain(const Topology& topology, std::string_view domain_id);
[[nodiscard]] const Region& require_region(const Domain& domain, std::string_view region_id);
[[nodiscard]] const ParameterShard& require_shard(
    const Topology& topology,
    std::string_view shard_id);

}  // namespace delta::reduce
