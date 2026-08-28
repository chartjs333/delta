#include <delta/fixedpoint/profile.hpp>
#include <delta/shards/envelope.hpp>
#include <delta/shards/plan.hpp>
#include <delta/shards/reader.hpp>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <regex>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace fixed = delta::fixedpoint;
namespace shards = delta::shards;

namespace {

constexpr std::string_view parameter_schema_id =
    "sha256:f43c0259749b15ae0d0154a6e9094774c7ea65e55adefbaea400a6201acb6239";
constexpr std::string_view scale_table_id =
    "sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205";
constexpr std::string_view shard_plan_id =
    "sha256:4c644a3254edb3d7bff009bbe91ee99df6051516362fa1a1eac6f0a803a9c7a1";
constexpr std::string_view proof_instance_id =
    "sha256:993b4d5104810dd26a3159b60cf8fe9afe6154cdcca90d22b577ae1b6d1ac076";
constexpr std::string_view round_config_id =
    "sha256:34bc08c316dfe22efe155ed11b866bcc0daf7ef8c3c7389c56b2f2c707443629";

[[noreturn]] void fail(std::string message) { throw std::runtime_error(std::move(message)); }

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
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

[[nodiscard]] std::vector<std::string> golden_envelopes() {
  std::ifstream input(DELTA_FIXEDPOINT_GOLDEN_PATH, std::ios::binary);
  expect(input.good(), "cannot open cross-language golden fixture");
  const std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  const std::regex pattern(R"REGEX("envelope_hex":"([0-9a-f]+)")REGEX");
  std::vector<std::string> result;
  for (auto cursor = std::sregex_iterator(document.begin(), document.end(), pattern);
       cursor != std::sregex_iterator();
       ++cursor) {
    result.push_back((*cursor)[1].str());
  }
  expect(result.size() == 5U, "golden fixture shard count changed");
  return result;
}

template <typename Operation>
void expect_error(shards::ErrorCode expected, Operation operation) {
  try {
    operation();
  } catch (const shards::ShardError& error) {
    expect(error.code() == expected, "unexpected shard error code");
    return;
  }
  fail("invalid shard operation was accepted");
}

[[nodiscard]] shards::ShardHeader header_for(const shards::PlanEntry& entry) {
  return shards::ShardHeader{
      entry.ordinal,
      entry.segment_id,
      entry.segment_offset,
      entry.element_start,
      entry.element_count,
      std::string(fixed::formal_semantics_id()),
      std::string(parameter_schema_id),
      std::string(fixed::fixed_profile_id()),
      std::string(proof_instance_id),
      std::string(round_config_id),
      std::string(scale_table_id),
      std::string(shard_plan_id),
      "ticket-002-fixture",
      "",
  };
}

[[nodiscard]] std::vector<std::int16_t> golden_values() {
  std::vector<std::int16_t> values = {1, -2, 0, 4};
  for (std::int16_t value = -16; value < 16; ++value) {
    values.push_back(value);
  }
  return values;
}

void test_plan_and_golden_envelopes() {
  const std::array segments = {
      shards::Segment{"decoder.bias", 0U, 0U, 4U},
      shards::Segment{"embedding.weight", 1U, 4U, 32U},
  };
  const auto plan = shards::plan_shards(segments, 16U);
  const std::vector<shards::PlanEntry> expected_plan = {
      {0U, "decoder.bias", 0U, 0U, 4U, 8U},
      {1U, "embedding.weight", 0U, 4U, 8U, 16U},
      {2U, "embedding.weight", 8U, 12U, 8U, 16U},
      {3U, "embedding.weight", 16U, 20U, 8U, 16U},
      {4U, "embedding.weight", 24U, 28U, 8U, 16U},
  };
  expect(plan == expected_plan, "deterministic shard plan mismatch");
  const auto values = golden_values();
  const std::array expected_leaves = {
      std::string_view{"sha256:d31edb78c0fab575015c5085bc6d9549b46c5d80afa0d51b5297feced5a1667b"},
      std::string_view{"sha256:2912a9459c37329bc3c7561e9feced73631ff6fa3ede3ba7214fbef2412ab94c"},
      std::string_view{"sha256:3769b5d6bea026cd2d56497df9b7e18fdb8ccac4fd75fdb32e22dc44cbadb03b"},
      std::string_view{"sha256:b833682c5948f0342abce15da24ad931b67112f9a37cc033e1b78c3de520c2fe"},
      std::string_view{"sha256:982a683110d847f69e6e18523c036a6645fb4da3511b8e586a40f0df750a8ded"},
  };
  std::vector<shards::EncodedShard> encoded;
  std::vector<std::string> leaves;
  const auto expected_envelopes = golden_envelopes();
  for (std::size_t index = 0; index < plan.size(); ++index) {
    const auto& entry = plan[index];
    const auto begin = values.begin() + static_cast<std::ptrdiff_t>(entry.element_start);
    const auto shard = shards::write_shard(
        header_for(entry), std::span(begin, static_cast<std::size_t>(entry.element_count)));
    expect(shard.leaf_id == expected_leaves[index], "golden shard leaf mismatch");
    expect(hex(shard.envelope) == expected_envelopes[index], "golden shard envelope bytes mismatch");
    leaves.push_back(shard.leaf_id);
    encoded.push_back(shard);
  }
  expect(
      shards::merkle_root(leaves) ==
          "sha256:e80916a8ec7d634b4c3524d873c13144b7760c7552e6788132a75fce5456296d",
      "ordered Merkle root mismatch");

  shards::ShardCollector collector(plan);
  for (std::size_t index = encoded.size(); index-- > 0U;) {
    const auto verified = shards::read_shard(encoded[index].envelope, header_for(plan[index]));
    expect(collector.insert(verified), "first shard insert was not accepted");
    if (index == 2U) {
      expect(!collector.insert(verified), "idempotent duplicate was not ignored");
    }
  }
  expect(collector.complete(), "reordered collector did not complete");
  expect(collector.canonical_values() == values, "canonical q iteration changed order");

  auto conflicting_values = values;
  conflicting_values[0] = 2;
  const auto conflict_encoded = shards::write_shard(
      header_for(plan[0]), std::span(conflicting_values.data(), plan[0].element_count));
  const auto conflict = shards::read_shard(conflict_encoded.envelope, header_for(plan[0]));
  expect_error(shards::ErrorCode::duplicate_conflict, [&collector, &conflict] {
    static_cast<void>(collector.insert(conflict));
  });

  auto truncated = encoded[0].envelope;
  truncated.pop_back();
  expect_error(shards::ErrorCode::truncated, [&truncated, &plan] {
    static_cast<void>(shards::read_shard(truncated, header_for(plan[0])));
  });
  auto trailing = encoded[0].envelope;
  trailing.push_back(std::byte{0});
  expect_error(shards::ErrorCode::trailing_bytes, [&trailing, &plan] {
    static_cast<void>(shards::read_shard(trailing, header_for(plan[0])));
  });
  auto oversized = encoded[0].envelope;
  oversized[8] = std::byte{1};
  oversized[9] = std::byte{0};
  oversized[10] = std::byte{1};
  oversized[11] = std::byte{0};
  expect_error(shards::ErrorCode::header_too_large, [&oversized, &plan] {
    static_cast<void>(shards::read_shard(oversized, header_for(plan[0])));
  });
  auto wrong_context = header_for(plan[0]);
  wrong_context.ticket_id = "ticket-wrong";
  expect_error(shards::ErrorCode::context_mismatch, [&encoded, &wrong_context] {
    static_cast<void>(shards::read_shard(encoded[0].envelope, wrong_context));
  });
}

void test_invalid_plans_fail_closed() {
  const std::array gap = {
      shards::Segment{"a", 0U, 0U, 4U},
      shards::Segment{"b", 1U, 5U, 4U},
  };
  expect_error(shards::ErrorCode::gap_or_overlap, [gap] {
    static_cast<void>(shards::plan_shards(gap, 16U));
  });
  const std::array overlap = {
      shards::Segment{"a", 0U, 0U, 4U},
      shards::Segment{"b", 1U, 3U, 4U},
  };
  expect_error(shards::ErrorCode::gap_or_overlap, [overlap] {
    static_cast<void>(shards::plan_shards(overlap, 16U));
  });
  const std::array huge = {shards::Segment{"a", 0U, 0U, 4'097U}};
  expect_error(shards::ErrorCode::shard_count_limit, [huge] {
    static_cast<void>(shards::plan_shards(huge, 2U));
  });
}

}  // namespace

int main() {
  try {
    test_plan_and_golden_envelopes();
    test_invalid_plans_fail_closed();
  } catch (const std::exception& error) {
    std::cerr << "delta shards test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta shard tests passed\n";
  return 0;
}
