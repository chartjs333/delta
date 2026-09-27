#include <delta/fixedpoint/scale.hpp>

#include <delta/fixedpoint/profile.hpp>

#include <cstdint>
#include <numeric>

namespace delta::fixedpoint {
namespace {

[[nodiscard]] std::uint64_t magnitude(std::int64_t value) noexcept {
  if (value >= 0) {
    return static_cast<std::uint64_t>(value);
  }
  return static_cast<std::uint64_t>(-(value + 1)) + 1U;
}

[[noreturn]] void reject(ErrorCode code, const char* message) {
  throw ContractError(code, message);
}

}  // namespace

void validate_rational(const Rational& value) {
  if (value.denominator == 0U) {
    reject(ErrorCode::rational_zero_denominator, "rational denominator must be positive");
  }
  if (value.numerator == 0 && value.denominator != 1U) {
    reject(ErrorCode::rational_zero_not_canonical, "canonical zero is exactly 0/1");
  }
  if (std::gcd(magnitude(value.numerator), static_cast<std::uint64_t>(value.denominator)) != 1U) {
    reject(ErrorCode::rational_not_reduced, "rational must be in lowest terms");
  }
}

void validate_scale(const Scale& value) {
  if (value.numerator == 0U || value.denominator == 0U) {
    reject(ErrorCode::scale_not_positive, "scale must be a positive rational");
  }
  if (std::gcd(value.numerator, value.denominator) != 1U) {
    reject(ErrorCode::rational_not_reduced, "scale must be in lowest terms");
  }
}

}  // namespace delta::fixedpoint
