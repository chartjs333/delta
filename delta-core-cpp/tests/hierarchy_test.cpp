#include <delta/fixedpoint/profile.hpp>
#include <delta/reduce/topology.hpp>

#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <regex>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace hierarchy = delta::reduce;

namespace {

[[noreturn]] void fail(std::string message) { throw std::runtime_error(std::move(message)); }

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

[[nodiscard]] std::vector<std::byte> unhex(std::string_view value) {
  const auto nibble = [](char character) -> unsigned {
    if (character >= '0' && character <= '9') {
      return static_cast<unsigned>(character - '0');
    }
    if (character >= 'a' && character <= 'f') {
      return static_cast<unsigned>(character - 'a') + 10U;
    }
    fail("fixture contains non-hex bytes");
  };
  expect((value.size() % 2U) == 0U, "fixture hex has odd length");
  std::vector<std::byte> result;
  result.reserve(value.size() / 2U);
  for (std::size_t index = 0U; index < value.size(); index += 2U) {
    result.push_back(static_cast<std::byte>((nibble(value[index]) << 4U) | nibble(value[index + 1U])));
  }
  return result;
}

struct Fixture {
  std::vector<std::byte> topology;
  std::string topology_id;
  std::vector<std::byte> proof;
  std::string proof_id;
};

[[nodiscard]] Fixture fixture() {
  std::ifstream input(DELTA_HIERARCHY_GOLDEN_PATH, std::ios::binary);
  expect(input.good(), "cannot open hierarchy golden fixture");
  const std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  const std::regex topology_pattern(
      R"REGEX("topology":\{"bytes_hex":"([0-9a-f]+)","content_id":"(sha256:[0-9a-f]{64})")REGEX");
  const std::regex proof_pattern(
      R"REGEX("hierarchy_proof_instance":\{"bytes_hex":"([0-9a-f]+)","content_id":"(sha256:[0-9a-f]{64})")REGEX");
  std::smatch match;
  expect(std::regex_search(document, match, topology_pattern), "topology fixture is missing");
  auto topology = unhex(match[1].str());
  auto topology_id = match[2].str();
  expect(std::regex_search(document, match, proof_pattern), "proof fixture is missing");
  return Fixture{std::move(topology), std::move(topology_id), unhex(match[1].str()), match[2].str()};
}

[[nodiscard]] hierarchy::Context context() {
  return {
      "sha256:993b4d5104810dd26a3159b60cf8fe9afe6154cdcca90d22b577ae1b6d1ac076",
      "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "sha256:34bc08c316dfe22efe155ed11b866bcc0daf7ef8c3c7389c56b2f2c707443629",
      "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6",
      "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61",
      "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205",
      "sha256:4c644a3254edb3d7bff009bbe91ee99df6051516362fa1a1eac6f0a803a9c7a1",
  };
}

template <typename Operation>
void expect_error(hierarchy::ErrorCode expected, Operation operation) {
  try {
    operation();
  } catch (const hierarchy::ReduceError& error) {
    expect(error.code() == expected, "hierarchy operation returned the wrong error code");
    return;
  }
  fail("invalid hierarchy input was accepted");
}

[[nodiscard]] std::vector<std::byte> replace_once(
    std::span<const std::byte> input,
    std::string_view before,
    std::string_view after) {
  std::string text(reinterpret_cast<const char*>(input.data()), input.size());
  const auto offset = text.find(before);
  expect(offset != std::string::npos, "mutation target is missing");
  expect(text.find(before, offset + before.size()) == std::string::npos,
         "mutation target is duplicated");
  text.replace(offset, before.size(), after);
  const auto bytes = std::as_bytes(std::span(text.data(), text.size()));
  return {bytes.begin(), bytes.end()};
}

[[nodiscard]] std::vector<hierarchy::CoefficientBinding> coefficients() {
  std::vector<hierarchy::CoefficientBinding> result;
  for (const auto domain : {std::string_view{"code"}, std::string_view{"text"}}) {
    const auto prefix = domain == "code" ? 'c' : 't';
    const auto count = domain == "code" ? 6U : 5U;
    for (std::uint32_t ordinal = 1U; ordinal <= count; ++ordinal) {
      const auto suffix = "0" + std::to_string(ordinal);
      result.push_back({std::string(domain), std::string(1U, prefix) + "-ticket-" + suffix,
                        static_cast<std::int64_t>(ordinal), 1U});
    }
  }
  return result;
}

void test_golden_contract() {
  const auto data = fixture();
  const auto topology = hierarchy::parse_topology(data.topology, context());
  expect(topology.topology_id == data.topology_id && topology.domains.size() == 2U &&
             topology.shards.size() == 2U,
         "golden hierarchy shape or identity changed");
  expect(topology.soft_deadline_tick == 50U && topology.hard_deadline_tick == 100U &&
             topology.validator_epoch == 7U,
         "golden immutable topology metadata changed");
  const auto proof = hierarchy::parse_hierarchy_proof(data.proof, topology);
  expect(proof.hierarchy_proof_instance_id == data.proof_id &&
             proof.coefficient_abs_max == 6U && proof.common_denominator == 1U &&
             proof.product_abs_bound == delta::core::arithmetic::Int128::from_u64(196602U) &&
             proof.final_abs_bound == delta::core::arithmetic::Int128::from_u64(1179612U),
         "golden theorem instance changed");
  const auto bound = hierarchy::validate_coefficient_plan(topology, proof, coefficients());
  expect(bound == hierarchy::BoundValidation{
                      11U, 3U, 6U, delta::core::arithmetic::Int128::from_u64(196602U),
                      delta::core::arithmetic::Int128::from_u64(1179612U)},
         "concrete regional/global bound validation changed");
}

void test_partition_and_shard_mutants() {
  const auto data = fixture();
  const auto overlap = replace_once(
      data.topology, "\"tickets\":[\"c-ticket-01\"]",
      "\"tickets\":[\"c-ticket-01\",\"c-ticket-02\"]");
  expect_error(hierarchy::ErrorCode::partition_invalid, [&] {
    static_cast<void>(hierarchy::parse_topology(overlap, context()));
  });
  const auto gap = replace_once(
      data.topology,
      "{\"end_element\":8,\"shard_id\":\"parameter-001\",\"start_element\":4}",
      "{\"end_element\":8,\"shard_id\":\"parameter-001\",\"start_element\":5}");
  expect_error(hierarchy::ErrorCode::shard_coverage_invalid, [&] {
    static_cast<void>(hierarchy::parse_topology(gap, context()));
  });
}

void test_proof_and_coefficient_failures() {
  const auto data = fixture();
  const auto topology = hierarchy::parse_topology(data.topology, context());
  const auto unsafe = replace_once(data.proof, "\"final_abs_bound\":\"1179612\"",
                                   "\"final_abs_bound\":\"1179611\"");
  expect_error(hierarchy::ErrorCode::proof_invalid, [&] {
    static_cast<void>(hierarchy::parse_hierarchy_proof(unsafe, topology));
  });
  const auto proof = hierarchy::parse_hierarchy_proof(data.proof, topology);
  auto bad_denominator = coefficients();
  bad_denominator[0].denominator = 2U;
  expect_error(hierarchy::ErrorCode::proof_invalid, [&] {
    static_cast<void>(hierarchy::validate_coefficient_plan(topology, proof, bad_denominator));
  });
  auto duplicate = coefficients();
  duplicate[0].ticket_id = duplicate[1].ticket_id;
  expect_error(hierarchy::ErrorCode::contribution_invalid, [&] {
    static_cast<void>(hierarchy::validate_coefficient_plan(topology, proof, duplicate));
  });
  auto outside_bound = coefficients();
  outside_bound[0].numerator = 7;
  expect_error(hierarchy::ErrorCode::proof_invalid, [&] {
    static_cast<void>(hierarchy::validate_coefficient_plan(topology, proof, outside_bound));
  });
}

void test_parser_limits_and_context() {
  const auto data = fixture();
  hierarchy::Limits limits;
  limits.topology_bytes = data.topology.size() - 1U;
  expect_error(hierarchy::ErrorCode::input_too_large, [&] {
    static_cast<void>(hierarchy::parse_topology(data.topology, context(), limits));
  });
  auto wrong_context = context();
  wrong_context.frozen_input_root =
      "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee";
  expect_error(hierarchy::ErrorCode::context_mismatch, [&] {
    static_cast<void>(hierarchy::parse_topology(data.topology, wrong_context));
  });
  auto noncanonical = data.topology;
  noncanonical.insert(noncanonical.begin() + 1, std::byte{' '});
  expect_error(hierarchy::ErrorCode::canonical_json_invalid, [&] {
    static_cast<void>(hierarchy::parse_topology(noncanonical, context()));
  });
}

}  // namespace

int main() {
  try {
    test_golden_contract();
    test_partition_and_shard_mutants();
    test_proof_and_coefficient_failures();
    test_parser_limits_and_context();
  } catch (const std::exception& error) {
    std::cerr << "delta hierarchy test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta hierarchy tests passed\n";
  return 0;
}
