#include <delta/distribution/certification_policy.hpp>

#include <cstddef>
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

namespace distribution = delta::distribution;

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
  std::vector<std::byte> manifest;
  std::vector<std::byte> certificate;
};

[[nodiscard]] Fixture golden_fixture() {
  std::ifstream input(DELTA_DISTRIBUTION_GOLDEN_PATH, std::ios::binary);
  expect(input.good(), "cannot open distribution golden fixture");
  const std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  const std::regex manifest_pattern(R"REGEX("manifest":\{"bytes_hex":"([0-9a-f]+)")REGEX");
  const std::regex certificate_pattern(
      R"REGEX("certificate":\{"bytes_hex":"([0-9a-f]+)")REGEX");
  std::smatch match;
  expect(std::regex_search(document, match, manifest_pattern), "manifest fixture bytes are missing");
  auto manifest = unhex(match[1].str());
  expect(std::regex_search(document, match, certificate_pattern),
         "certificate fixture bytes are missing");
  return Fixture{std::move(manifest), unhex(match[1].str())};
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
  return std::vector<std::byte>(bytes.begin(), bytes.end());
}

void expect_code(
    std::string_view expected,
    std::span<const std::byte> manifest,
    std::span<const std::byte> certificate,
    bool make_current = false) {
  const auto decision = distribution::evaluate_certified_manifest(manifest, certificate, make_current);
  expect(!decision.accepted, "invalid publication was accepted");
  expect(decision.code == expected, "publication produced the wrong typed rejection");
}

void test_valid_and_policy_failures() {
  const auto fixture = golden_fixture();
  const auto accepted =
      distribution::evaluate_certified_manifest(fixture.manifest, fixture.certificate);
  expect(accepted.accepted && accepted.code == "OK", "golden publication was rejected");
  expect(
      accepted.manifest_id ==
          "sha256:d48ff2208becabd6b380503c2de6746dbbe4ec0c450fe67308a9a17d726fc254",
      "native object-manifest identity drifted");
  expect(accepted.formal_action_id == "ACT-PUBLISH", "formal action binding drifted");
  expect(accepted.canonical_effect_json() ==
             "{\"certificate_policy_id\":\"sha256:95b0dac10dbe18d4394855a93d897b36e84fafeb2475ee9f416f689abe6f74a0\",\"code\":\"OK\",\"formal_action_id\":\"ACT-PUBLISH\",\"manifest_id\":\"sha256:d48ff2208becabd6b380503c2de6746dbbe4ec0c450fe67308a9a17d726fc254\",\"status\":\"ACCEPT\"}",
         "canonical native effect bytes drifted");

  constexpr auto zeros =
      "sha256:0000000000000000000000000000000000000000000000000000000000000000";
  auto unknown = replace_once(fixture.manifest, distribution::aggregate_policy_id, zeros);
  expect_code("POLICY_UNKNOWN", unknown, fixture.certificate);
  auto inactive = replace_once(
      fixture.manifest, distribution::aggregate_policy_id, distribution::inactive_apply_policy_id);
  expect_code("POLICY_INACTIVE", inactive, fixture.certificate);
  expect_code("CURRENT_REQUIRES_APPLY_QC", fixture.manifest, fixture.certificate, true);

  auto forbidden = replace_once(
      fixture.manifest,
      distribution::aggregate_media_type,
      "application/vnd.deltareduce.worker-q-shard;version=1");
  expect_code("MEDIA_FORBIDDEN", forbidden, fixture.certificate);

  auto wrong_certificate_root = replace_once(
      fixture.certificate,
      "sha256:e80916a8ec7d634b4c3524d873c13144b7760c7552e6788132a75fce5456296d",
      zeros);
  expect_code("CERTIFICATE_ROOT_MISMATCH", fixture.manifest, wrong_certificate_root);
  auto wrong_source_root = replace_once(
      fixture.certificate,
      "sha256:c6fcf9131d0a481aee2918bf894dbebc62442dcb26be3c559630841f4d26f967",
      zeros);
  expect_code("SOURCE_STATE_ROOT_MISMATCH", fixture.manifest, wrong_source_root);
}

void test_parser_and_allocation_bounds() {
  const auto fixture = golden_fixture();
  auto noncanonical = fixture.manifest;
  noncanonical.insert(noncanonical.begin() + 1, std::byte{' '});
  expect_code("CANONICAL_JSON_INVALID", noncanonical, fixture.certificate);

  std::vector<std::byte> oversized(distribution::max_manifest_bytes + 1U, std::byte{'x'});
  expect_code("MANIFEST_TOO_LARGE", oversized, fixture.certificate);
  std::vector<std::byte> oversized_certificate(
      distribution::max_certificate_bytes + 1U, std::byte{'x'});
  expect_code("CERTIFICATE_TOO_LARGE", fixture.manifest, oversized_certificate);
}

}  // namespace

int main() {
  try {
    test_valid_and_policy_failures();
    test_parser_and_allocation_bounds();
  } catch (const std::exception& error) {
    std::cerr << "distribution test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "distribution policy tests passed\n";
  return 0;
}
