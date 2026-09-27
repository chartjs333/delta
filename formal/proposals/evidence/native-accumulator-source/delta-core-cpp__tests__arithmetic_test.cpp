#include <delta/core/arithmetic.hpp>

#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>

namespace arithmetic = delta::core::arithmetic;

namespace {

[[noreturn]] void fail(std::string message) { throw std::runtime_error(std::move(message)); }

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

template <typename Operation>
void expect_arithmetic_error(arithmetic::ErrorCode expected, Operation operation) {
  try {
    operation();
  } catch (const arithmetic::ArithmeticError& error) {
    expect(error.code() == expected, "unexpected stable arithmetic error code");
    return;
  }
  fail("unsafe arithmetic operation was accepted");
}

template <typename Operation>
void expect_bound_error(arithmetic::BoundErrorCode expected, Operation operation) {
  try {
    operation();
  } catch (const arithmetic::BoundError& error) {
    expect(error.code() == expected, "unexpected stable bound error code");
    return;
  }
  fail("unsafe accumulator bound was accepted");
}

void test_checked_int64() {
  expect(arithmetic::checked_add(INT64_MAX, 0) == INT64_MAX, "INT64 max add failed");
  expect(arithmetic::checked_add(INT64_MIN, 1) == INT64_MIN + 1, "INT64 negative add failed");
  expect_arithmetic_error(arithmetic::ErrorCode::signed_add_overflow, [] {
    static_cast<void>(arithmetic::checked_add(INT64_MAX, 1));
  });
  expect_arithmetic_error(arithmetic::ErrorCode::signed_add_overflow, [] {
    static_cast<void>(arithmetic::checked_add(INT64_MIN, -1));
  });

  expect(arithmetic::checked_multiply(-3, 7) == -21, "INT64 signed product failed");
  expect(arithmetic::checked_multiply(INT64_MIN, 1) == INT64_MIN, "INT64 min product failed");
  expect_arithmetic_error(arithmetic::ErrorCode::signed_multiply_overflow, [] {
    static_cast<void>(arithmetic::checked_multiply(INT64_MIN, -1));
  });
  expect_arithmetic_error(arithmetic::ErrorCode::signed_multiply_overflow, [] {
    static_cast<void>(arithmetic::checked_multiply(INT64_MAX, 2));
  });
}

void test_checked_int128() {
  const auto zero = arithmetic::Int128::from_i64(0);
  const auto one = arithmetic::Int128::from_i64(1);
  const auto negative_one = arithmetic::Int128::from_i64(-1);
  expect(
      arithmetic::checked_add(arithmetic::Int128::maximum(), zero) ==
          arithmetic::Int128::maximum(),
      "INT128 max add failed");
  expect_arithmetic_error(arithmetic::ErrorCode::signed_add_overflow, [one] {
    static_cast<void>(arithmetic::checked_add(arithmetic::Int128::maximum(), one));
  });
  expect_arithmetic_error(arithmetic::ErrorCode::signed_add_overflow, [negative_one] {
    static_cast<void>(arithmetic::checked_add(arithmetic::Int128::minimum(), negative_one));
  });

  const auto square = arithmetic::checked_multiply(
      arithmetic::Int128::from_i64(INT64_MAX), arithmetic::Int128::from_i64(INT64_MAX));
  expect(
      square == arithmetic::Int128::from_bits(UINT64_C(0x3fffffffffffffff), 1U),
      "portable INT128 limb product mismatch");
  const auto negative = arithmetic::checked_multiply(
      arithmetic::Int128::from_i64(-3), arithmetic::Int128::from_i64(7));
  expect(negative == arithmetic::Int128::from_i64(-21), "INT128 negative product mismatch");
  expect_arithmetic_error(arithmetic::ErrorCode::signed_multiply_overflow, [negative_one] {
    static_cast<void>(
        arithmetic::checked_multiply(arithmetic::Int128::minimum(), negative_one));
  });
  expect_arithmetic_error(arithmetic::ErrorCode::signed_multiply_overflow, [] {
    static_cast<void>(arithmetic::checked_multiply(
        arithmetic::Int128::maximum(), arithmetic::Int128::from_i64(2)));
  });
}

arithmetic::AccumulatorBoundRequest safe_int128_request() {
  return arithmetic::AccumulatorBoundRequest{
      std::string(arithmetic::fixture_profile_id()),
      arithmetic::AccumulatorWidth::int128,
      100U,
      INT64_MIN,
      INT64_MAX,
      -1,
      1,
      arithmetic::Int128::from_i64(0),
  };
}

void test_conservative_accumulator_bound() {
  const auto safe = arithmetic::validate_accumulator_bound(safe_int128_request());
  expect(
      safe.maximum_absolute_sum == arithmetic::Int128::from_bits(50U, 0U),
      "100-ticket INT128 conservative sum mismatch");
  expect(
      safe.required_bound == safe.maximum_absolute_sum,
      "zero headroom changed conservative bound");

  auto int64_safe = safe_int128_request();
  int64_safe.width = arithmetic::AccumulatorWidth::int64;
  int64_safe.maximum_eligible_tickets = 1U;
  int64_safe.minimum_value = 0;
  int64_safe.maximum_value = INT64_MAX;
  int64_safe.minimum_coefficient = 1;
  int64_safe.maximum_coefficient = 1;
  static_cast<void>(arithmetic::validate_accumulator_bound(int64_safe));

  int64_safe.headroom = arithmetic::Int128::from_i64(1);
  expect_bound_error(arithmetic::BoundErrorCode::accumulator_bound_unsafe, [&int64_safe] {
    static_cast<void>(arithmetic::validate_accumulator_bound(int64_safe));
  });

  auto unsafe_int128 = safe_int128_request();
  unsafe_int128.maximum_eligible_tickets = 2U;
  unsafe_int128.minimum_coefficient = INT64_MIN;
  unsafe_int128.maximum_coefficient = INT64_MAX;
  expect_bound_error(arithmetic::BoundErrorCode::accumulator_bound_unsafe, [&unsafe_int128] {
    static_cast<void>(arithmetic::validate_accumulator_bound(unsafe_int128));
  });
}

void test_bound_inputs_fail_closed() {
  auto request = safe_int128_request();
  request.profile_id = "production-profile-not-owned-by-003";
  expect_bound_error(arithmetic::BoundErrorCode::profile_mismatch, [&request] {
    static_cast<void>(arithmetic::validate_accumulator_bound(request));
  });

  request = safe_int128_request();
  request.minimum_value = 1;
  request.maximum_value = -1;
  expect_bound_error(arithmetic::BoundErrorCode::range_invalid, [&request] {
    static_cast<void>(arithmetic::validate_accumulator_bound(request));
  });

  request = safe_int128_request();
  request.headroom = arithmetic::Int128::from_i64(-1);
  expect_bound_error(arithmetic::BoundErrorCode::headroom_invalid, [&request] {
    static_cast<void>(arithmetic::validate_accumulator_bound(request));
  });
}

}  // namespace

int main() {
  try {
    test_checked_int64();
    test_checked_int128();
    test_conservative_accumulator_bound();
    test_bound_inputs_fail_closed();
  } catch (const std::exception& error) {
    std::cerr << "delta_core arithmetic test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta_core arithmetic tests passed\n";
  return 0;
}
