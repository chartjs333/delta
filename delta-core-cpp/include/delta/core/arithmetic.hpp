#pragma once

#include <cstdint>
#include <stdexcept>
#include <string>
#include <string_view>

namespace delta::core::arithmetic {

enum class ErrorCode {
  signed_add_overflow,
  signed_multiply_overflow,
};

class ArithmeticError final : public std::runtime_error {
 public:
  ArithmeticError(ErrorCode code, std::string message);

  [[nodiscard]] ErrorCode code() const noexcept;

 private:
  ErrorCode code_;
};

struct Int128 {
  std::uint64_t high;
  std::uint64_t low;

  [[nodiscard]] static constexpr Int128 from_bits(
      std::uint64_t high_bits,
      std::uint64_t low_bits) noexcept {
    return Int128{high_bits, low_bits};
  }

  [[nodiscard]] static constexpr Int128 from_u64(std::uint64_t value) noexcept {
    return Int128{0U, value};
  }

  [[nodiscard]] static constexpr Int128 from_i64(std::int64_t value) noexcept {
    return value < 0 ? Int128{UINT64_MAX, static_cast<std::uint64_t>(value)}
                     : Int128{0U, static_cast<std::uint64_t>(value)};
  }

  [[nodiscard]] static constexpr Int128 minimum() noexcept {
    return Int128{UINT64_C(0x8000000000000000), 0U};
  }

  [[nodiscard]] static constexpr Int128 maximum() noexcept {
    return Int128{UINT64_C(0x7fffffffffffffff), UINT64_MAX};
  }

  [[nodiscard]] constexpr bool negative() const noexcept {
    return (high & UINT64_C(0x8000000000000000)) != 0U;
  }

  bool operator==(const Int128&) const = default;
};

[[nodiscard]] int compare(Int128 left, Int128 right) noexcept;
[[nodiscard]] Int128 checked_add(Int128 left, Int128 right);
[[nodiscard]] Int128 checked_multiply(Int128 left, Int128 right);
[[nodiscard]] std::int64_t checked_add(std::int64_t left, std::int64_t right);
[[nodiscard]] std::int64_t checked_multiply(std::int64_t left, std::int64_t right);

enum class AccumulatorWidth {
  int64,
  int128,
};

enum class BoundErrorCode {
  profile_mismatch,
  range_invalid,
  headroom_invalid,
  accumulator_bound_unsafe,
};

class BoundError final : public std::runtime_error {
 public:
  BoundError(BoundErrorCode code, std::string message);

  [[nodiscard]] BoundErrorCode code() const noexcept;

 private:
  BoundErrorCode code_;
};

struct AccumulatorBoundRequest {
  std::string profile_id;
  AccumulatorWidth width;
  std::uint64_t maximum_eligible_tickets;
  std::int64_t minimum_value;
  std::int64_t maximum_value;
  std::int64_t minimum_coefficient;
  std::int64_t maximum_coefficient;
  Int128 headroom;
};

struct AccumulatorBound {
  Int128 maximum_absolute_value;
  Int128 maximum_absolute_coefficient;
  Int128 maximum_absolute_term;
  Int128 maximum_absolute_sum;
  Int128 headroom;
  Int128 required_bound;
  Int128 accumulator_limit;

  bool operator==(const AccumulatorBound&) const = default;
};

[[nodiscard]] AccumulatorBound validate_accumulator_bound(const AccumulatorBoundRequest& request);
[[nodiscard]] constexpr std::string_view fixture_profile_id() noexcept {
  return "bft-int-fixture-v1";
}

}  // namespace delta::core::arithmetic
