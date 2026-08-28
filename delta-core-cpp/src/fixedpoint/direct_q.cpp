#include <delta/fixedpoint/direct_q.hpp>

#include <delta/fixedpoint/profile.hpp>

#include <cstddef>
#include <cstdint>
#include <limits>
#include <span>
#include <string>
#include <utility>
#include <vector>

namespace delta::fixedpoint {
namespace {

[[noreturn]] void reject(ErrorCode code, const char* message) {
  throw ContractError(code, message);
}

[[nodiscard]] std::uint64_t absolute_coefficient(std::int64_t value) {
  if (value == std::numeric_limits<std::int64_t>::min()) {
    reject(ErrorCode::accumulator_bound_unsafe, "coefficient absolute value exceeds INT64_MAX");
  }
  return value < 0 ? static_cast<std::uint64_t>(-value) : static_cast<std::uint64_t>(value);
}

void validate_values(std::span<const std::int16_t> values) {
  if (values.empty() || values.size() > max_payload_bytes / 2U) {
    reject(ErrorCode::q_value_out_of_range, "direct q stream size is outside profile limits");
  }
  for (const auto value : values) {
    if (value < q_min || value > q_max) {
      reject(ErrorCode::q_value_out_of_range, "direct q stream contains a forbidden value");
    }
  }
}

[[nodiscard]] bool fits_width(
    delta::core::arithmetic::Int128 value,
    delta::core::arithmetic::AccumulatorWidth width) noexcept {
  if (width == delta::core::arithmetic::AccumulatorWidth::int128) {
    return true;
  }
  return delta::core::arithmetic::compare(
             value,
             delta::core::arithmetic::Int128::from_i64(INT64_MIN)) >= 0 &&
         delta::core::arithmetic::compare(
             value,
             delta::core::arithmetic::Int128::from_i64(INT64_MAX)) <= 0;
}

void validate_actual_coefficient(std::int64_t coefficient, const ProofRequest& proof) {
  if (absolute_coefficient(coefficient) > proof.coefficient_abs_max) {
    reject(
        ErrorCode::accumulator_bound_unsafe,
        "actual coefficient exceeds the validated proof instance");
  }
}

}  // namespace

delta::core::protocol::PreparedIntegerShard prepare_direct_q(
    const DirectQContext& context,
    std::span<const std::int16_t> values,
    const ConcreteProofInstance& proof,
    std::string_view expected_proof_id) {
  static_cast<void>(validate_concrete_proof_instance(proof, expected_proof_id));
  validate_actual_coefficient(context.coefficient, proof.request);
  validate_values(values);
  std::vector<std::int64_t> widened;
  widened.reserve(values.size());
  for (const auto value : values) {
    widened.push_back(value);
  }
  return delta::core::protocol::PreparedIntegerShard{
      context.coefficient,
      context.input_leaf_id,
      {
          proof.request.width == delta::core::arithmetic::AccumulatorWidth::int64 ? 64U : 128U,
          "LITTLE_ENDIAN",
          std::string(fixed_profile_id()),
          16U,
      },
      context.parameter_id,
      context.round_id,
      context.shard_id,
      context.ticket_id,
      std::move(widened),
  };
}

DirectQAccumulator::DirectQAccumulator(
    ConcreteProofInstance proof,
    std::string expected_proof_id,
    std::size_t element_count)
    : proof_(std::move(proof)),
      values_(element_count, delta::core::arithmetic::Int128::from_i64(0)) {
  static_cast<void>(validate_concrete_proof_instance(proof_, expected_proof_id));
  if (element_count == 0U || element_count > max_payload_bytes / 2U) {
    reject(ErrorCode::q_value_out_of_range, "direct accumulator width is outside profile limits");
  }
}

void DirectQAccumulator::add(
    std::int64_t coefficient,
    std::span<const std::int16_t> values) {
  validate_actual_coefficient(coefficient, proof_.request);
  validate_values(values);
  if (values.size() != values_.size()) {
    reject(ErrorCode::proof_instance_invalid, "direct q vector width changed during accumulation");
  }
#if !defined(DELTA_FIXEDPOINT_MUTANT_UNCHECKED_COUNT)
  if (contribution_count_ >= proof_.request.maximum_eligible_contributions) {
    reject(
        ErrorCode::accumulator_bound_unsafe,
        "direct q contribution count exceeds the validated proof instance");
  }
#endif
  std::vector<delta::core::arithmetic::Int128> next = values_;
  for (std::size_t index = 0U; index < values.size(); ++index) {
    const auto term = delta::core::arithmetic::checked_multiply(
        delta::core::arithmetic::Int128::from_i64(coefficient),
        delta::core::arithmetic::Int128::from_i64(values[index]));
    const auto sum = delta::core::arithmetic::checked_add(next[index], term);
    if (!fits_width(term, proof_.request.width) || !fits_width(sum, proof_.request.width)) {
      reject(
          ErrorCode::accumulator_bound_unsafe,
          "direct q product or incremental prefix exceeds the selected width");
    }
    next[index] = sum;
  }
  values_ = std::move(next);
  ++contribution_count_;
}

std::uint64_t DirectQAccumulator::contribution_count() const noexcept {
  return contribution_count_;
}

std::span<const delta::core::arithmetic::Int128> DirectQAccumulator::values() const noexcept {
  return values_;
}

}  // namespace delta::fixedpoint
