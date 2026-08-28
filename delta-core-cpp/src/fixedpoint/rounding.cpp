#include <delta/fixedpoint/rounding.hpp>

#include <delta/fixedpoint/profile.hpp>

#include <cstdint>
#include <limits>

namespace delta::fixedpoint {
namespace {

[[noreturn]] void reject(ErrorCode code, const char* message) {
  throw ContractError(code, message);
}

[[nodiscard]] std::uint64_t magnitude(std::int64_t value) noexcept {
  if (value >= 0) {
    return static_cast<std::uint64_t>(value);
  }
  return static_cast<std::uint64_t>(-(value + 1)) + 1U;
}

[[nodiscard]] std::uint64_t checked_product(std::uint64_t left, std::uint64_t right) {
  constexpr auto limit = static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max());
  if (right != 0U && left > limit / right) {
    reject(
        ErrorCode::quantization_intermediate_overflow,
        "scaled rational exceeds signed INT64");
  }
  return left * right;
}

}  // namespace

std::int16_t quantize(const Rational& source, const Scale& quantum) {
  validate_rational(source);
  validate_scale(quantum);
  const auto scaled_magnitude =
      checked_product(magnitude(source.numerator), quantum.denominator);
  const auto divisor = checked_product(source.denominator, quantum.numerator);
  auto quotient = scaled_magnitude / divisor;
  const auto remainder = scaled_magnitude % divisor;
  const auto twice_remainder = remainder * 2U;
  if (twice_remainder > divisor || (twice_remainder == divisor && (quotient & 1U) != 0U)) {
    ++quotient;
  }
  if (quotient > static_cast<std::uint64_t>(q_max)) {
    reject(ErrorCode::quantization_range_exceeded, "quantized value exceeds symmetric INT16");
  }
  const auto signed_value = source.numerator < 0 ? -static_cast<std::int32_t>(quotient)
                                                  : static_cast<std::int32_t>(quotient);
  return static_cast<std::int16_t>(signed_value);
}

}  // namespace delta::fixedpoint
