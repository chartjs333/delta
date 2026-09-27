#pragma once

#include <cstdint>
#include <string>
#include <string_view>
#include <vector>

#include <delta/core/arithmetic.hpp>

namespace delta::fixedpoint {

struct ProofRequest {
  std::string profile_id;
  std::uint64_t coefficient_abs_max;
  std::uint64_t maximum_eligible_contributions;
  delta::core::arithmetic::AccumulatorWidth width;
  delta::core::arithmetic::Int128 headroom;
};

struct ProofResult {
  delta::core::arithmetic::Int128 product_abs_bound;
  delta::core::arithmetic::Int128 maximum_incremental_prefix_abs;
  delta::core::arithmetic::Int128 final_abs_bound;
  delta::core::arithmetic::AccumulatorWidth selected_width;

  bool operator==(const ProofResult&) const = default;
};

struct TheoremBinding {
  std::string obligation_id;
  std::vector<std::string> theorem_names;

  bool operator==(const TheoremBinding&) const = default;
};

struct ConcreteProofInstance {
  ProofRequest request;
  std::uint64_t common_denominator;
  std::string config_id;
  delta::core::arithmetic::Int128 declared_final_abs_bound;
  std::string formal_id;
  std::string lean_artifact_sha256;
  delta::core::arithmetic::Int128 declared_incremental_prefix_abs;
  delta::core::arithmetic::Int128 declared_product_abs_bound;
  delta::core::arithmetic::AccumulatorWidth product_width;
  std::uint64_t q_abs_max;
  std::string result;
  std::string scale_table_id;
  std::string schema_version;
  std::vector<TheoremBinding> theorems;
};

[[nodiscard]] ProofResult validate_proof_instance(const ProofRequest& request);
[[nodiscard]] std::vector<TheoremBinding> required_theorem_bindings();
[[nodiscard]] std::string canonical_proof_instance_json(const ConcreteProofInstance& instance);
[[nodiscard]] std::string derive_proof_instance_id(const ConcreteProofInstance& instance);
[[nodiscard]] ProofResult validate_concrete_proof_instance(
    const ConcreteProofInstance& instance,
    std::string_view expected_content_id);

}  // namespace delta::fixedpoint
