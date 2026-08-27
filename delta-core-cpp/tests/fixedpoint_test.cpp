#include <delta/fixedpoint/bounds.hpp>
#include <delta/fixedpoint/encoder.hpp>
#include <delta/fixedpoint/profile.hpp>
#include <delta/fixedpoint/rounding.hpp>
#include <delta/fixedpoint/scale.hpp>

#include <array>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <limits>
#include <numeric>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace fixed = delta::fixedpoint;
namespace arithmetic = delta::core::arithmetic;

namespace {

[[noreturn]] void fail(std::string message) { throw std::runtime_error(std::move(message)); }

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

template <typename Operation>
void expect_error(fixed::ErrorCode expected, Operation operation) {
  try {
    operation();
  } catch (const fixed::ContractError& error) {
    expect(error.code() == expected, "unexpected fixed-point error code");
    return;
  }
  fail("invalid fixed-point input was accepted");
}

[[nodiscard]] std::string hex(std::span<const std::byte> bytes) {
  constexpr std::array<char, 16> alphabet = {
      '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'};
  std::string result;
  result.reserve(bytes.size() * 2U);
  for (const auto byte : bytes) {
    const auto value = std::to_integer<std::uint8_t>(byte);
    result.push_back(alphabet[value >> 4U]);
    result.push_back(alphabet[value & 0x0fU]);
  }
  return result;
}

void test_profile_identity() {
  const auto profile = fixed::int16_fixed_v1();
  fixed::validate_profile(profile);
  expect(fixed::derive_profile_id(profile) == fixed::fixed_profile_id(), "profile ID mismatch");
  const auto encoded = fixed::canonical_profile_json(profile);
  expect(encoded.size() == 752U, "profile canonical byte length changed");

  auto invalid = profile;
  invalid.minimum_q = -32'768;
  expect_error(fixed::ErrorCode::profile_mismatch, [&invalid] { fixed::validate_profile(invalid); });
}

void test_signed_rounding_and_range() {
  constexpr fixed::Scale unit{1U, 1U};
  const std::array cases = {
      std::pair{fixed::Rational{0, 1U}, std::int16_t{0}},
      std::pair{fixed::Rational{1, 2U}, std::int16_t{0}},
      std::pair{fixed::Rational{3, 2U}, std::int16_t{2}},
      std::pair{fixed::Rational{-1, 2U}, std::int16_t{0}},
      std::pair{fixed::Rational{-3, 2U}, std::int16_t{-2}},
      std::pair{fixed::Rational{32'767, 1U}, std::int16_t{32'767}},
      std::pair{fixed::Rational{-32'767, 1U}, std::int16_t{-32'767}},
  };
  for (const auto& [source, expected] : cases) {
    expect(fixed::quantize(source, unit) == expected, "signed ties-to-even mismatch");
  }
  const std::array payload_values = {
      std::int16_t{0}, std::int16_t{1}, std::int16_t{-1}, std::int16_t{32'767},
      std::int16_t{-32'767}};
  expect(
      hex(fixed::encode_q_payload(payload_values)) == "00000100ffffff7f0180",
      "little-endian q payload mismatch");
  expect_error(fixed::ErrorCode::quantization_range_exceeded, [unit] {
    static_cast<void>(fixed::quantize(fixed::Rational{32'768, 1U}, unit));
  });
  expect_error(fixed::ErrorCode::quantization_range_exceeded, [unit] {
    static_cast<void>(fixed::quantize(fixed::Rational{-32'768, 1U}, unit));
  });
  expect_error(fixed::ErrorCode::quantization_intermediate_overflow, [] {
    static_cast<void>(fixed::quantize(
        fixed::Rational{INT64_MAX, 1U}, fixed::Scale{1U, UINT32_MAX}));
  });
  expect_error(fixed::ErrorCode::rational_zero_denominator, [] {
    fixed::validate_rational(fixed::Rational{1, 0U});
  });
  expect_error(fixed::ErrorCode::rational_not_reduced, [] {
    fixed::validate_rational(fixed::Rational{2, 2U});
  });
  expect_error(fixed::ErrorCode::rational_zero_not_canonical, [] {
    fixed::validate_rational(fixed::Rational{0, 2U});
  });
}

void test_feature002_vector() {
  const std::array decoder = {
      fixed::Rational{1, 4U},
      fixed::Rational{-1, 2U},
      fixed::Rational{0, 1U},
      fixed::Rational{1, 1U},
  };
  const auto decoder_encoded = fixed::encode_segment(decoder, fixed::Scale{1U, 4U});
  expect(
      decoder_encoded.values == std::vector<std::int16_t>({1, -2, 0, 4}),
      "decoder q values mismatch");
  expect(hex(decoder_encoded.payload) == "0100feff00000400", "decoder payload mismatch");

  std::vector<fixed::Rational> embedding;
  std::vector<std::int16_t> expected;
  for (std::int64_t numerator = -16; numerator < 16; ++numerator) {
    const auto divisor = std::gcd(numerator < 0 ? -numerator : numerator, std::int64_t{16});
    embedding.push_back(
        fixed::Rational{numerator / divisor, static_cast<std::uint32_t>(16 / divisor)});
    expected.push_back(static_cast<std::int16_t>(numerator));
  }
  const auto encoded = fixed::encode_segment(embedding, fixed::Scale{1U, 16U});
  expect(encoded.values == expected, "feature-002 embedding q values mismatch");
  expect(
      hex(encoded.payload) ==
          "f0fff1fff2fff3fff4fff5fff6fff7fff8fff9fffafffbfffcfffdfffeffffff"
          "00000100020003000400050006000700080009000a000b000c000d000e000f00",
      "feature-002 embedding payload mismatch");
}

void test_proof_instances() {
  const auto safe64 = fixed::validate_proof_instance(fixed::ProofRequest{
      std::string(fixed::fixed_profile_id()),
      65'538U,
      UINT32_MAX,
      arithmetic::AccumulatorWidth::int64,
      arithmetic::Int128::from_i64(0),
  });
  expect(
      safe64.product_abs_bound == arithmetic::Int128::from_u64(2'147'483'646U),
      "maximum-safe INT64 product mismatch");
  expect(
      safe64.final_abs_bound ==
          arithmetic::Int128::from_u64(UINT64_C(0x7ffffffd80000002)),
      "maximum-safe INT64 final bound mismatch");
  expect_error(fixed::ErrorCode::accumulator_bound_unsafe, [] {
    static_cast<void>(fixed::validate_proof_instance(fixed::ProofRequest{
        std::string(fixed::fixed_profile_id()),
        65'539U,
        UINT32_MAX,
        arithmetic::AccumulatorWidth::int64,
        arithmetic::Int128::from_i64(0),
    }));
  });
  const auto safe128 = fixed::validate_proof_instance(fixed::ProofRequest{
      std::string(fixed::fixed_profile_id()),
      static_cast<std::uint64_t>(INT64_MAX),
      UINT32_MAX,
      arithmetic::AccumulatorWidth::int128,
      arithmetic::Int128::from_i64(0),
  });
  expect(
      safe128.product_abs_bound ==
          arithmetic::Int128::from_bits(UINT64_C(0x3fff), UINT64_C(0x7fffffffffff8001)),
      "INT128 product bound mismatch");
  expect(
      safe128.final_abs_bound == arithmetic::Int128::from_bits(
                                           UINT64_C(0x3fff7fffc000),
                                           UINT64_C(0x7fff800100007fff)),
      "INT128 final bound mismatch");

  const fixed::ConcreteProofInstance concrete{
      {
          std::string(fixed::fixed_profile_id()),
          65'538U,
          UINT32_MAX,
          arithmetic::AccumulatorWidth::int64,
          arithmetic::Int128::from_i64(0),
      },
      1U,
      "sha256:34bc08c316dfe22efe155ed11b866bcc0daf7ef8c3c7389c56b2f2c707443629",
      arithmetic::Int128::from_u64(UINT64_C(0x7ffffffd80000002)),
      std::string(fixed::formal_semantics_id()),
      "sha256:6d8c715eacf55f99a2bbc5fca7242610d871a1ef76ae58d51305b81e66364736",
      arithmetic::Int128::from_u64(UINT64_C(0x7ffffffd80000002)),
      arithmetic::Int128::from_u64(2'147'483'646U),
      arithmetic::AccumulatorWidth::int64,
      32'767U,
      "PASS",
      "sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205",
      "1.0.0",
      fixed::required_theorem_bindings(),
  };
  constexpr std::string_view proof_id =
      "sha256:993b4d5104810dd26a3159b60cf8fe9afe6154cdcca90d22b577ae1b6d1ac076";
  expect(fixed::derive_proof_instance_id(concrete) == proof_id, "proof content ID mismatch");
  expect(
      fixed::validate_concrete_proof_instance(concrete, proof_id) == safe64,
      "concrete proof validation changed recomputed bounds");

  const auto expect_invalidated = [&concrete, proof_id](auto mutate) {
    auto changed = concrete;
    mutate(changed);
    expect_error(fixed::ErrorCode::proof_instance_invalid, [&changed, proof_id] {
      static_cast<void>(fixed::validate_concrete_proof_instance(changed, proof_id));
    });
  };
  expect_invalidated([](fixed::ConcreteProofInstance& value) { --value.request.coefficient_abs_max; });
  expect_invalidated([](fixed::ConcreteProofInstance& value) {
    --value.request.maximum_eligible_contributions;
  });
  expect_invalidated([](fixed::ConcreteProofInstance& value) {
    value.request.profile_id =
        "sha256:2222222222222222222222222222222222222222222222222222222222222222";
  });
  expect_invalidated([](fixed::ConcreteProofInstance& value) {
    value.scale_table_id =
        "sha256:3333333333333333333333333333333333333333333333333333333333333333";
  });
  expect_invalidated([](fixed::ConcreteProofInstance& value) {
    value.config_id =
        "sha256:4444444444444444444444444444444444444444444444444444444444444444";
  });
  expect_invalidated([](fixed::ConcreteProofInstance& value) { value.schema_version = "1.0.1"; });
  expect_invalidated([](fixed::ConcreteProofInstance& value) {
    value.theorems[0].theorem_names[0] = "DeltaReduce.mutatedProductBound";
  });
}

void test_fixture_binding() {
  std::ifstream input(DELTA_FIXEDPOINT_FIXTURE_PATH, std::ios::binary);
  expect(input.good(), "cannot open fixed-point golden fixture");
  std::ostringstream stream;
  stream << input.rdbuf();
  const auto fixture = stream.str();
  for (const auto token : {
           fixed::fixed_profile_id(),
           std::string_view{"sha256:e80916a8ec7d634b4c3524d873c13144b7760c7552e6788132a75fce5456296d"},
           std::string_view{"\"q_values\":[1,-2,0,4,-16,-15"},
       }) {
    expect(fixture.find(token) != std::string::npos, "golden fixture binding missing");
  }
}

}  // namespace

int main() {
  try {
    test_profile_identity();
    test_signed_rounding_and_range();
    test_feature002_vector();
    test_proof_instances();
    test_fixture_binding();
  } catch (const std::exception& error) {
    std::cerr << "delta fixed-point test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta fixed-point tests passed\n";
  return 0;
}
