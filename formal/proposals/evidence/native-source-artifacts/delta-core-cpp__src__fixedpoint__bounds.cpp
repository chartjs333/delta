#include <delta/fixedpoint/bounds.hpp>

#include <delta/fixedpoint/checked.hpp>
#include <delta/fixedpoint/profile.hpp>

#include <cstdint>
#include <limits>
#include <span>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace delta::fixedpoint {
namespace {

constexpr std::string_view lean_source_id =
    "sha256:6d8c715eacf55f99a2bbc5fca7242610d871a1ef76ae58d51305b81e66364736";

[[noreturn]] void reject(ErrorCode code, const char* message) {
  throw ContractError(code, message);
}

[[nodiscard]] bool content_id_valid(std::string_view value) noexcept {
  if (value.size() != 71U || !value.starts_with("sha256:")) {
    return false;
  }
  for (const char digit : value.substr(7U)) {
    if (!((digit >= '0' && digit <= '9') || (digit >= 'a' && digit <= 'f'))) {
      return false;
    }
  }
  return true;
}

[[nodiscard]] std::string decimal(delta::core::arithmetic::Int128 value) {
  if (value.negative()) {
    reject(ErrorCode::proof_instance_invalid, "proof bounds must be non-negative");
  }
  if (value == delta::core::arithmetic::Int128::from_u64(0U)) {
    return "0";
  }
  std::string reversed;
  while (value != delta::core::arithmetic::Int128::from_u64(0U)) {
    const auto quotient_high = value.high / 10U;
    std::uint64_t remainder = value.high % 10U;
    std::uint64_t quotient_low = 0U;
    for (int bit = 63; bit >= 0; --bit) {
      remainder = (remainder * 2U) + ((value.low >> static_cast<unsigned>(bit)) & 1U);
      if (remainder >= 10U) {
        remainder -= 10U;
        quotient_low |= UINT64_C(1) << static_cast<unsigned>(bit);
      }
    }
    reversed.push_back(static_cast<char>('0' + remainder));
    value = delta::core::arithmetic::Int128::from_bits(quotient_high, quotient_low);
  }
  return {reversed.rbegin(), reversed.rend()};
}

[[nodiscard]] unsigned width_bits(delta::core::arithmetic::AccumulatorWidth width) noexcept {
  return width == delta::core::arithmetic::AccumulatorWidth::int64 ? 64U : 128U;
}

[[nodiscard]] bool fits_width(
    delta::core::arithmetic::Int128 value,
    delta::core::arithmetic::AccumulatorWidth width) noexcept {
  if (value.negative()) {
    return false;
  }
  return width == delta::core::arithmetic::AccumulatorWidth::int128 ||
         delta::core::arithmetic::compare(
             value,
             delta::core::arithmetic::Int128::from_i64(INT64_MAX)) <= 0;
}

[[nodiscard]] std::string theorem_json(const std::vector<TheoremBinding>& theorems) {
  std::string result = "[";
  for (std::size_t group = 0U; group < theorems.size(); ++group) {
    if (group != 0U) {
      result += ',';
    }
    result += "{\"obligation_id\":\"" + theorems[group].obligation_id +
              "\",\"theorem_names\":[";
    for (std::size_t theorem = 0U; theorem < theorems[group].theorem_names.size(); ++theorem) {
      if (theorem != 0U) {
        result += ',';
      }
      result += "\"" + theorems[group].theorem_names[theorem] + "\"";
    }
    result += "]}";
  }
  result += ']';
  return result;
}

}  // namespace

ProofResult validate_proof_instance(const ProofRequest& request) {
  if (request.profile_id != fixed_profile_id() || request.coefficient_abs_max == 0U ||
      request.coefficient_abs_max > static_cast<std::uint64_t>(INT64_MAX) ||
      request.maximum_eligible_contributions == 0U) {
    throw ContractError(ErrorCode::proof_instance_invalid, "proof inputs are not canonical");
  }
  delta::core::arithmetic::AccumulatorBound bound;
  try {
    bound = delta::core::arithmetic::validate_accumulator_bound(
        delta::core::arithmetic::AccumulatorBoundRequest{
            std::string(delta::core::arithmetic::fixture_profile_id()),
            request.width,
            request.maximum_eligible_contributions,
            q_min,
            q_max,
            -static_cast<std::int64_t>(request.coefficient_abs_max),
            static_cast<std::int64_t>(request.coefficient_abs_max),
            request.headroom,
        });
  } catch (const delta::core::arithmetic::BoundError&) {
    throw ContractError(
        ErrorCode::accumulator_bound_unsafe,
        "proof product, incremental prefix or final bound is unsafe");
  }
  return ProofResult{
      bound.maximum_absolute_term,
      bound.maximum_absolute_sum,
      bound.required_bound,
      request.width,
  };
}

std::vector<TheoremBinding> required_theorem_bindings() {
  return {
      {
          "PO-A1",
          {
              "DeltaReduce.signedProductBound",
              "DeltaReduce.intermediateProductFits",
          },
      },
      {
          "PO-A2",
          {
              "DeltaReduce.flatAccumulatorBound",
              "DeltaReduce.everyCanonicalPrefixFits",
          },
      },
      {
          "PO-A3",
          {
              "DeltaReduce.commonDenominatorNumeratorSafe",
              "DeltaReduce.reducedRationalDenominatorPositive",
              "DeltaReduce.reducedRationalIsCoprime",
              "DeltaReduce.commonDenominatorPositive",
              "DeltaReduce.eachDenominatorDividesCommon",
              "DeltaReduce.canonicalRoundBelowHalf",
              "DeltaReduce.canonicalRoundAtOrAboveHalf",
              "DeltaReduce.canonicalRoundTieTowardPositive",
              "DeltaReduce.canonicalRoundDeterministic",
          },
      },
  };
}

std::string canonical_proof_instance_json(const ConcreteProofInstance& instance) {
  return "{\"coefficient_abs_max\":\"" + std::to_string(instance.request.coefficient_abs_max) +
         "\",\"common_denominator\":\"" + std::to_string(instance.common_denominator) +
         "\",\"config_id\":\"" + instance.config_id + "\",\"final_abs_bound\":\"" +
         decimal(instance.declared_final_abs_bound) + "\",\"formal_semantics_id\":\"" +
         instance.formal_id + "\",\"lean_artifact_sha256\":\"" +
         instance.lean_artifact_sha256 + "\",\"max_eligible_contributions\":\"" +
         std::to_string(instance.request.maximum_eligible_contributions) +
         "\",\"max_incremental_prefix_abs\":\"" +
         decimal(instance.declared_incremental_prefix_abs) +
         "\",\"product_abs_bound\":\"" + decimal(instance.declared_product_abs_bound) +
         "\",\"product_width_bits\":" + std::to_string(width_bits(instance.product_width)) +
         ",\"profile_id\":\"" + instance.request.profile_id + "\",\"q_abs_max\":\"" +
         std::to_string(instance.q_abs_max) + "\",\"result\":\"" + instance.result +
         "\",\"scale_table_id\":\"" + instance.scale_table_id +
         "\",\"schema_version\":\"" + instance.schema_version +
         "\",\"selected_accumulator_width_bits\":" +
         std::to_string(width_bits(instance.request.width)) +
         ",\"theorems\":" + theorem_json(instance.theorems) +
         ",\"type_name\":\"ACCUMULATOR_PROOF_INSTANCE\"}";
}

std::string derive_proof_instance_id(const ConcreteProofInstance& instance) {
  auto canonical = canonical_proof_instance_json(instance);
  const auto bytes = std::as_bytes(std::span(canonical.data(), canonical.size()));
  return domain_content_id("deltareduce.004.proof-instance.v1", bytes);
}

ProofResult validate_concrete_proof_instance(
    const ConcreteProofInstance& instance,
    std::string_view expected_content_id) {
  if (!content_id_valid(expected_content_id) || !content_id_valid(instance.config_id) ||
      !content_id_valid(instance.request.profile_id) || !content_id_valid(instance.scale_table_id) ||
      !content_id_valid(instance.formal_id) || !content_id_valid(instance.lean_artifact_sha256) ||
      instance.formal_id != formal_semantics_id() || instance.lean_artifact_sha256 != lean_source_id ||
      instance.schema_version != "1.0.0" || instance.result != "PASS" ||
      instance.common_denominator == 0U || instance.q_abs_max != static_cast<std::uint64_t>(q_max) ||
      instance.theorems != required_theorem_bindings()) {
    reject(ErrorCode::proof_instance_invalid, "proof metadata does not match the formal contract");
  }
  const auto result = validate_proof_instance(instance.request);
  if (!fits_width(result.product_abs_bound, instance.product_width) ||
      instance.declared_product_abs_bound != result.product_abs_bound ||
      instance.declared_incremental_prefix_abs != result.maximum_incremental_prefix_abs ||
      instance.declared_final_abs_bound != result.final_abs_bound ||
      derive_proof_instance_id(instance) != expected_content_id) {
    reject(
        ErrorCode::proof_instance_invalid,
        "declared proof bounds or content identity do not match recomputation");
  }
  return result;
}

}  // namespace delta::fixedpoint
