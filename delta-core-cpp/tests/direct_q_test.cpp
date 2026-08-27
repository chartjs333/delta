#include <delta/core/canonical.hpp>
#include <delta/core/protocol.hpp>
#include <delta/fixedpoint/direct_q.hpp>
#include <delta/fixedpoint/profile.hpp>

#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>

namespace arithmetic = delta::core::arithmetic;
namespace canonical = delta::core::canonical;
namespace fixed = delta::fixedpoint;
namespace protocol = delta::core::protocol;

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
    expect(error.code() == expected, "unexpected direct-q error code");
    return;
  }
  fail("unsafe direct-q operation was accepted");
}

[[nodiscard]] fixed::ConcreteProofInstance proof(std::uint64_t count = 3U) {
  const auto product = arithmetic::Int128::from_u64(98'301U);
  const auto final = arithmetic::Int128::from_u64(98'301U * count);
  return fixed::ConcreteProofInstance{
      {
          std::string(fixed::fixed_profile_id()),
          3U,
          count,
          arithmetic::AccumulatorWidth::int64,
          arithmetic::Int128::from_i64(0),
      },
      1U,
      "sha256:1111111111111111111111111111111111111111111111111111111111111111",
      final,
      std::string(fixed::formal_semantics_id()),
      "sha256:6d8c715eacf55f99a2bbc5fca7242610d871a1ef76ae58d51305b81e66364736",
      final,
      product,
      arithmetic::AccumulatorWidth::int64,
      32'767U,
      "PASS",
      "sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205",
      "1.0.0",
      fixed::required_theorem_bindings(),
  };
}

void test_prepared_bridge_is_integer_only() {
  const std::array values = {
      std::int16_t{-32'767}, std::int16_t{-1}, std::int16_t{0}, std::int16_t{32'767}};
  const fixed::DirectQContext context{
      -3,
      "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "embedding.weight",
      "round-direct-q",
      "shard-000",
      "ticket-direct-q",
  };
  const auto instance = proof();
  const auto prepared =
      fixed::prepare_direct_q(context, values, instance, fixed::derive_proof_instance_id(instance));
  expect(
      prepared.values == std::vector<std::int64_t>({-32'767, -1, 0, 32'767}),
      "q values changed while widening directly to consensus integers");
  expect(
      prepared.integer_profile == protocol::IntegerProfile{
                                      64U,
                                      "LITTLE_ENDIAN",
                                      std::string(fixed::fixed_profile_id()),
                                      16U,
                                  },
      "direct-q prepared profile is not explicit");
  const auto bytes = protocol::encode(prepared);
  expect(protocol::parse_prepared_integer_shard(bytes) == prepared, "direct-q bridge is not canonical");
  expect(
      canonical::content_id(canonical::Type::prepared_integer_shard, bytes).starts_with("sha256:"),
      "direct-q bridge is not content addressed");
}

void test_checked_incremental_prefix() {
  const auto instance = proof();
  fixed::DirectQAccumulator accumulator(
      instance,
      fixed::derive_proof_instance_id(instance),
      3U);
  const std::array first = {std::int16_t{2}, std::int16_t{-3}, std::int16_t{4}};
  const std::array second = {std::int16_t{-5}, std::int16_t{6}, std::int16_t{-7}};
  accumulator.add(3, first);
  accumulator.add(-2, second);
  expect(accumulator.contribution_count() == 2U, "direct-q contribution count mismatch");
  const auto sums = accumulator.values();
  expect(sums[0] == arithmetic::Int128::from_i64(16), "direct-q sum[0] mismatch");
  expect(sums[1] == arithmetic::Int128::from_i64(-21), "direct-q sum[1] mismatch");
  expect(sums[2] == arithmetic::Int128::from_i64(26), "direct-q sum[2] mismatch");

  expect_error(fixed::ErrorCode::accumulator_bound_unsafe, [&accumulator, &first] {
    accumulator.add(4, first);
  });
  const auto limited_instance = proof(1U);
  fixed::DirectQAccumulator count_limited(
      limited_instance,
      fixed::derive_proof_instance_id(limited_instance),
      3U);
  count_limited.add(1, first);
  expect_error(fixed::ErrorCode::accumulator_bound_unsafe, [&count_limited, &first] {
    count_limited.add(1, first);
  });
}

void test_distribution_plane_denylist() {
  expect(
      !fixed::distribution_publish_allowed(fixed::ReduceArtifactKind::encoded_worker_q_shard),
      "worker q shard escaped the reduce plane");
  expect(
      !fixed::distribution_publish_allowed(
          fixed::ReduceArtifactKind::encoded_contribution_manifest),
      "worker contribution manifest escaped the reduce plane");
  expect(
      fixed::distribution_publish_allowed(fixed::ReduceArtifactKind::aggregate_certificate),
      "certified aggregate was denied");
  expect(
      fixed::distribution_publish_allowed(fixed::ReduceArtifactKind::model_checkpoint),
      "model checkpoint was denied");
}

}  // namespace

int main() {
  try {
    test_prepared_bridge_is_integer_only();
    test_checked_incremental_prefix();
    test_distribution_plane_denylist();
  } catch (const std::exception& error) {
    std::cerr << "delta direct-q test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta direct-q tests passed\n";
  return 0;
}
