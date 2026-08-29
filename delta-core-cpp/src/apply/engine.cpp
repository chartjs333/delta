#include <delta/apply/engine.hpp>

#include <delta/core/arithmetic.hpp>
#include <delta/core/canonical.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <numeric>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace delta::apply {
namespace {

[[noreturn]] void reject(certificates::ErrorCode code, const char* message) {
  throw certificates::CertificateError(code, message);
}

void require(bool condition, certificates::ErrorCode code, const char* message) {
  if (!condition) {
    reject(code, message);
  }
}

[[nodiscard]] std::int64_t checked_add(std::int64_t left, std::int64_t right) {
  try {
    return core::arithmetic::checked_add(left, right);
  } catch (const core::arithmetic::ArithmeticError&) {
    reject(certificates::ErrorCode::arithmetic_invalid, "Apply addition overflows int64");
  }
}

[[nodiscard]] std::int64_t checked_multiply(std::int64_t left, std::int64_t right) {
  try {
    return core::arithmetic::checked_multiply(left, right);
  } catch (const core::arithmetic::ArithmeticError&) {
    reject(certificates::ErrorCode::arithmetic_invalid, "Apply product overflows int64");
  }
}

[[nodiscard]] std::int64_t scaled(
    std::int64_t value,
    const certificates::Rational& coefficient) {
  certificates::validate_rational(coefficient, true);
  return round_half_toward_positive(
      checked_multiply(value, coefficient.numerator), coefficient.denominator);
}

[[nodiscard]] std::string values_hash(
    std::string_view domain,
    const std::vector<std::int64_t>& values) {
  std::string transcript;
  for (const auto value : values) {
    transcript += std::to_string(value);
    transcript.push_back(';');
  }
  std::vector<std::byte> bytes;
  bytes.reserve(domain.size() + 1U + transcript.size());
  for (const char character : domain) {
    bytes.push_back(static_cast<std::byte>(character));
  }
  bytes.push_back(std::byte{0});
  for (const char character : transcript) {
    bytes.push_back(static_cast<std::byte>(character));
  }
  return "sha256:" + core::canonical::sha256_hex(bytes);
}

[[nodiscard]] std::int64_t weighted_coordinate(
    const certificates::ApplyArithmeticProfile& profile,
    std::span<const DomainAggregate> aggregates,
    std::size_t coordinate) {
  std::uint64_t common_denominator = 1U;
  for (const auto& weight : profile.domain_weights) {
    certificates::validate_rational(weight.pi, true);
    const auto divisor = std::gcd(common_denominator, weight.pi.denominator);
    require(
        common_denominator <=
            std::numeric_limits<std::uint64_t>::max() /
                (weight.pi.denominator / divisor),
        certificates::ErrorCode::arithmetic_invalid,
        "domain-weight common denominator overflows");
    common_denominator *= weight.pi.denominator / divisor;
  }
  require(
      common_denominator <= static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),
      certificates::ErrorCode::arithmetic_invalid,
      "domain-weight denominator exceeds int64");
  std::int64_t numerator = 0;
  for (std::size_t index = 0U; index < aggregates.size(); ++index) {
    const auto scale = common_denominator / profile.domain_weights[index].pi.denominator;
    require(
        scale <= static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),
        certificates::ErrorCode::arithmetic_invalid,
        "domain-weight scale exceeds int64");
    const auto term = checked_multiply(
        checked_multiply(
            aggregates[index].values[coordinate], profile.domain_weights[index].pi.numerator),
        static_cast<std::int64_t>(scale));
    numerator = checked_add(numerator, term);
  }
  return round_half_toward_positive(numerator, common_denominator);
}

}  // namespace

std::int64_t round_half_toward_positive(
    std::int64_t numerator,
    std::uint64_t denominator) {
  require(denominator > 0U, certificates::ErrorCode::arithmetic_invalid, "zero denominator");
  const auto magnitude = numerator >= 0
                             ? static_cast<std::uint64_t>(numerator)
                             : static_cast<std::uint64_t>(-(numerator + 1)) + 1U;
  const auto quotient = magnitude / denominator;
  const auto remainder = magnitude % denominator;
  require(
      quotient <= static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),
      certificates::ErrorCode::arithmetic_invalid,
      "rounded result exceeds int64");
  if (numerator >= 0) {
    const bool round_up = remainder >= denominator - remainder;
    require(
        !round_up || quotient < static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),
        certificates::ErrorCode::arithmetic_invalid,
        "rounded result exceeds int64");
    return static_cast<std::int64_t>(quotient + (round_up ? 1U : 0U));
  }
  const auto truncated = -static_cast<std::int64_t>(quotient);
  if (remainder == 0U) {
    return truncated;
  }
  const bool toward_zero = remainder <= denominator - remainder;
  return toward_zero ? truncated : checked_add(truncated, -1);
}

certificates::ApplyCandidate compute_candidate(
    const certificates::Context& context,
    std::string aggregate_root_qc_id,
    const certificates::ApplyArithmeticProfile& profile,
    const State& parent,
    std::span<const DomainAggregate> aggregates) {
  require(
      certificates::is_content_id(aggregate_root_qc_id) &&
          certificates::is_content_id(parent.checkpoint_id) &&
          certificates::is_content_id(parent.optimizer_id),
      certificates::ErrorCode::identifier_invalid,
      "Apply parent ID is invalid");
  const auto profile_id = certificates::content_id(profile);
  require(
      !parent.model.empty() && parent.model.size() == parent.momentum.size(),
      certificates::ErrorCode::arithmetic_invalid,
      "parent model and optimizer state are incompatible");
  require(
      aggregates.size() == profile.domain_weights.size() && !aggregates.empty(),
      certificates::ErrorCode::coverage_incomplete,
      "domain aggregate coverage differs from the apply profile");
  for (std::size_t index = 0U; index < aggregates.size(); ++index) {
    require(
        aggregates[index].domain_id == profile.domain_weights[index].domain_id &&
            aggregates[index].values.size() == parent.model.size(),
        certificates::ErrorCode::coverage_incomplete,
        "domain aggregate is missing, reordered, or has the wrong shape");
  }

  std::vector<std::int64_t> next_model;
  std::vector<std::int64_t> next_momentum;
  next_model.reserve(parent.model.size());
  next_momentum.reserve(parent.model.size());
  for (std::size_t coordinate = 0U; coordinate < parent.model.size(); ++coordinate) {
    const auto gradient = weighted_coordinate(profile, aggregates, coordinate);
    const auto momentum = checked_add(scaled(parent.momentum[coordinate], profile.momentum), gradient);
    const auto direction = checked_add(scaled(momentum, profile.momentum), gradient);
    const auto decay = scaled(parent.model[coordinate], profile.weight_decay);
    const auto step = scaled(checked_add(direction, decay), profile.learning_rate);
    next_momentum.push_back(momentum);
    next_model.push_back(checked_add(parent.model[coordinate], checked_multiply(step, -1)));
  }

  certificates::ApplyCandidate result{
      .context = context,
      .aggregate_root_qc_id = std::move(aggregate_root_qc_id),
      .apply_arithmetic_profile_id = profile_id,
      .next_model_hash = values_hash("deltareduce.008.model.v1", next_model),
      .next_model_values = {},
      .next_optimizer_hash = values_hash("deltareduce.008.optimizer.v1", next_momentum),
      .next_optimizer_values = {},
      .parent_checkpoint_id = parent.checkpoint_id,
      .parent_optimizer_hash = parent.optimizer_id,
  };
  result.next_model_values.reserve(next_model.size());
  result.next_optimizer_values.reserve(next_momentum.size());
  for (const auto value : next_model) {
    result.next_model_values.push_back(std::to_string(value));
  }
  for (const auto value : next_momentum) {
    result.next_optimizer_values.push_back(std::to_string(value));
  }
  (void)certificates::content_id(result);
  return result;
}

}  // namespace delta::apply
