#include <delta/core/arithmetic.hpp>

#include <cstdint>
#include <limits>
#include <string>
#include <utility>

namespace delta::core::arithmetic {
namespace {

struct UInt128 {
  std::uint64_t high;
  std::uint64_t low;
};

[[noreturn]] void reject(ErrorCode code, const char* message) {
  throw ArithmeticError(code, message);
}

[[noreturn]] void reject_bound(BoundErrorCode code, const char* message) {
  throw BoundError(code, message);
}

[[nodiscard]] int compare_unsigned(UInt128 left, UInt128 right) noexcept {
  if (left.high < right.high) {
    return -1;
  }
  if (left.high > right.high) {
    return 1;
  }
  if (left.low < right.low) {
    return -1;
  }
  if (left.low > right.low) {
    return 1;
  }
  return 0;
}

[[nodiscard]] UInt128 add_unsigned(UInt128 left, UInt128 right) noexcept {
  const auto low = left.low + right.low;
  const auto carry = low < left.low ? std::uint64_t{1} : std::uint64_t{0};
  return UInt128{left.high + right.high + carry, low};
}

[[nodiscard]] UInt128 shift_right(UInt128 value) noexcept {
  return UInt128{value.high >> 1U, (value.low >> 1U) | (value.high << 63U)};
}

[[nodiscard]] UInt128 shift_left(UInt128 value) noexcept {
  return UInt128{(value.high << 1U) | (value.low >> 63U), value.low << 1U};
}

[[nodiscard]] bool is_zero(UInt128 value) noexcept { return value.high == 0U && value.low == 0U; }

[[nodiscard]] UInt128 negate_unsigned(UInt128 value) noexcept {
  const auto low = (~value.low) + 1U;
  const auto carry = low == 0U ? std::uint64_t{1} : std::uint64_t{0};
  return UInt128{~value.high + carry, low};
}

[[nodiscard]] UInt128 magnitude(Int128 value) noexcept {
  const UInt128 bits{value.high, value.low};
  return value.negative() ? negate_unsigned(bits) : bits;
}

[[nodiscard]] Int128 from_magnitude(UInt128 value, bool negative) noexcept {
  const auto bits = negative && !is_zero(value) ? negate_unsigned(value) : value;
  return Int128::from_bits(bits.high, bits.low);
}

[[nodiscard]] UInt128 multiply_magnitude(UInt128 left, UInt128 right, UInt128 limit) {
  UInt128 result{0U, 0U};
  auto addend = left;
  auto remaining = right;
  while (!is_zero(remaining)) {
    if ((remaining.low & 1U) != 0U) {
      const auto candidate = add_unsigned(result, addend);
      if (candidate.high < result.high || compare_unsigned(candidate, limit) > 0) {
        reject(ErrorCode::signed_multiply_overflow, "signed 128-bit product exceeds its range");
      }
      result = candidate;
    }
    remaining = shift_right(remaining);
    if (!is_zero(remaining)) {
      if ((addend.high & UINT64_C(0x8000000000000000)) != 0U) {
        reject(ErrorCode::signed_multiply_overflow, "signed 128-bit product exceeds its range");
      }
      addend = shift_left(addend);
    }
  }
  return result;
}

[[nodiscard]] Int128 absolute_i64(std::int64_t value) noexcept {
  if (value >= 0) {
    return Int128::from_i64(value);
  }
  if (value == std::numeric_limits<std::int64_t>::min()) {
    return Int128::from_u64(UINT64_C(0x8000000000000000));
  }
  return Int128::from_i64(-value);
}

[[nodiscard]] Int128 maximum(Int128 left, Int128 right) noexcept {
  return compare(left, right) >= 0 ? left : right;
}

[[nodiscard]] Int128 multiply_bound(Int128 left, Int128 right) {
  try {
    return checked_multiply(left, right);
  } catch (const ArithmeticError&) {
    reject_bound(BoundErrorCode::accumulator_bound_unsafe, "conservative product exceeds INT128");
  }
}

[[nodiscard]] Int128 add_bound(Int128 left, Int128 right) {
  try {
    return checked_add(left, right);
  } catch (const ArithmeticError&) {
    reject_bound(BoundErrorCode::accumulator_bound_unsafe, "conservative sum exceeds INT128");
  }
}

[[nodiscard]] std::int64_t narrow_i64(Int128 value) {
  if (value.high == 0U && value.low <= static_cast<std::uint64_t>(INT64_MAX)) {
    return static_cast<std::int64_t>(value.low);
  }
  if (value.high == UINT64_MAX && value.low >= UINT64_C(0x8000000000000000)) {
    if (value.low == UINT64_C(0x8000000000000000)) {
      return INT64_MIN;
    }
    const auto magnitude_value = (~value.low) + 1U;
    return -static_cast<std::int64_t>(magnitude_value);
  }
  reject(ErrorCode::signed_multiply_overflow, "signed 64-bit product exceeds its range");
}

}  // namespace

ArithmeticError::ArithmeticError(ErrorCode code, std::string message)
    : std::runtime_error(std::move(message)), code_(code) {}

ErrorCode ArithmeticError::code() const noexcept { return code_; }

int compare(Int128 left, Int128 right) noexcept {
  const bool left_negative = left.negative();
  const bool right_negative = right.negative();
  if (left_negative != right_negative) {
    return left_negative ? -1 : 1;
  }
  return compare_unsigned(UInt128{left.high, left.low}, UInt128{right.high, right.low});
}

Int128 checked_add(Int128 left, Int128 right) {
  const auto low = left.low + right.low;
  const auto carry = low < left.low ? std::uint64_t{1} : std::uint64_t{0};
  const auto result = Int128::from_bits(left.high + right.high + carry, low);
  if (left.negative() == right.negative() && result.negative() != left.negative()) {
    reject(ErrorCode::signed_add_overflow, "signed 128-bit addition exceeds its range");
  }
  return result;
}

Int128 checked_multiply(Int128 left, Int128 right) {
  const bool negative = left.negative() != right.negative();
  const UInt128 limit = negative
                            ? UInt128{UINT64_C(0x8000000000000000), 0U}
                            : UInt128{UINT64_C(0x7fffffffffffffff), UINT64_MAX};
  return from_magnitude(multiply_magnitude(magnitude(left), magnitude(right), limit), negative);
}

std::int64_t checked_add(std::int64_t left, std::int64_t right) {
  if ((right > 0 && left > INT64_MAX - right) || (right < 0 && left < INT64_MIN - right)) {
    reject(ErrorCode::signed_add_overflow, "signed 64-bit addition exceeds its range");
  }
  return left + right;
}

std::int64_t checked_multiply(std::int64_t left, std::int64_t right) {
  return narrow_i64(checked_multiply(Int128::from_i64(left), Int128::from_i64(right)));
}

BoundError::BoundError(BoundErrorCode code, std::string message)
    : std::runtime_error(std::move(message)), code_(code) {}

BoundErrorCode BoundError::code() const noexcept { return code_; }

AccumulatorBound validate_accumulator_bound(const AccumulatorBoundRequest& request) {
  if (request.profile_id != fixture_profile_id()) {
    reject_bound(BoundErrorCode::profile_mismatch, "unsupported fixed-point profile");
  }
  if (request.maximum_eligible_tickets == 0U || request.minimum_value > request.maximum_value ||
      request.minimum_coefficient > request.maximum_coefficient) {
    reject_bound(BoundErrorCode::range_invalid, "invalid conservative-bound range");
  }
  if (request.headroom.negative()) {
    reject_bound(BoundErrorCode::headroom_invalid, "accumulator headroom is negative");
  }

  const auto value_bound = maximum(
      absolute_i64(request.minimum_value), absolute_i64(request.maximum_value));
  const auto coefficient_bound = maximum(
      absolute_i64(request.minimum_coefficient), absolute_i64(request.maximum_coefficient));
  const auto term_bound = multiply_bound(value_bound, coefficient_bound);
  const auto sum_bound =
      multiply_bound(term_bound, Int128::from_u64(request.maximum_eligible_tickets));
  const auto required = add_bound(sum_bound, request.headroom);
  const auto limit = request.width == AccumulatorWidth::int64
                         ? Int128::from_i64(INT64_MAX)
                         : Int128::maximum();
  if (compare(required, limit) > 0) {
    reject_bound(
        BoundErrorCode::accumulator_bound_unsafe,
        "maximum absolute sum plus headroom exceeds accumulator limit");
  }
  return AccumulatorBound{
      value_bound,
      coefficient_bound,
      term_bound,
      sum_bound,
      request.headroom,
      required,
      limit,
  };
}

}  // namespace delta::core::arithmetic
