#include <delta_abi.h>

#include <algorithm>
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

namespace {

[[noreturn]] void fail(std::string message) { throw std::runtime_error(std::move(message)); }

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

[[nodiscard]] std::uint8_t nibble(char value) {
  if (value >= '0' && value <= '9') {
    return static_cast<std::uint8_t>(value - '0');
  }
  if (value >= 'a' && value <= 'f') {
    return static_cast<std::uint8_t>(value - 'a' + 10);
  }
  fail("scheduling ABI fixture contains non-hex bytes");
}

[[nodiscard]] std::vector<std::uint8_t> unhex(std::string_view input) {
  expect((input.size() % 2U) == 0U, "scheduling ABI fixture has odd hex length");
  std::vector<std::uint8_t> output;
  output.reserve(input.size() / 2U);
  for (std::size_t index = 0U; index < input.size(); index += 2U) {
    output.push_back(static_cast<std::uint8_t>(
        static_cast<std::uint8_t>(nibble(input[index]) << 4U) | nibble(input[index + 1U])));
  }
  return output;
}

struct Fixture {
  std::vector<std::uint8_t> profile;
  std::vector<std::uint8_t> decision;
};

[[nodiscard]] Fixture fixture() {
  std::ifstream input(DELTA_SCHEDULING_GOLDEN_PATH, std::ios::binary);
  expect(input.good(), "cannot open scheduling ABI golden fixture");
  const std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  const std::regex profile_pattern(
      R"REGEX("capability_profiles":\[\{"bytes_hex":"([0-9a-f]+)")REGEX");
  const std::regex decision_pattern(
      R"REGEX("eligibility_decisions":\[\{"bytes_hex":"([0-9a-f]+)")REGEX");
  std::smatch match;
  expect(std::regex_search(document, match, profile_pattern), "ABI capability fixture is missing");
  auto profile = unhex(match[1].str());
  expect(std::regex_search(document, match, decision_pattern), "ABI decision fixture is missing");
  return {std::move(profile), unhex(match[1].str())};
}

[[nodiscard]] delta_bytes_view_t view(std::string_view input) {
  return {reinterpret_cast<const std::uint8_t*>(input.data()), input.size()};
}

[[nodiscard]] delta_bytes_view_t view(const std::vector<std::uint8_t>& input) {
  return {input.data(), input.size()};
}

[[nodiscard]] delta_scheduling_eligibility_context_t context() {
  return {
      DELTA_SCHEDULING_ELIGIBILITY_CONTEXT_SIZE,
      0U,
      view("sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"),
      view("sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"),
      view("sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"),
      view("sha256:1111111111111111111111111111111111111111111111111111111111111111"),
      view("QLORA-8GB"),
      view("code,text"),
      view("eu,us"),
      view("sha256:3333333333333333333333333333333333333333333333333333333333333333"),
      view("sha256:8888888888888888888888888888888888888888888888888888888888888888,sha256:9999999999999999999999999999999999999999999999999999999999999999"),
      12U,
      7U,
      8'589'934'592U,
      8U,
  };
}

using Function = delta_status_t (*)(
    const delta_scheduling_eligibility_context_t*,
    delta_bytes_view_t,
    delta_output_buffer_t*);

[[nodiscard]] std::vector<std::uint8_t> evaluate(
    Function function,
    const delta_scheduling_eligibility_context_t& policy,
    const std::vector<std::uint8_t>& profile) {
  delta_output_buffer_t sizing{nullptr, 0U, 0U, 0U};
  expect(
      function(&policy, view(profile), &sizing) == DELTA_STATUS_BUFFER_TOO_SMALL,
      "scheduling ABI did not negotiate bounded output");
  expect(
      sizing.required > 0U && sizing.required <= 4096U && sizing.written == 0U,
      "scheduling ABI sizing escaped effect bounds");
  std::vector<std::uint8_t> output_bytes(sizing.required);
  delta_output_buffer_t output{output_bytes.data(), output_bytes.size(), 0U, 0U};
  expect(
      function(&policy, view(profile), &output) == DELTA_STATUS_OK &&
          output.required == output_bytes.size() && output.written == output_bytes.size(),
      "scheduling ABI bounded retry failed");
  return output_bytes;
}

void test_borrowed_copy_and_lifetime() {
  static_assert(
      sizeof(delta_scheduling_eligibility_context_t) ==
      DELTA_SCHEDULING_ELIGIBILITY_CONTEXT_SIZE);
  const auto data = fixture();
  const auto expected = context();
  const auto borrowed = evaluate(
      delta_scheduling_capability_evaluate_borrowed, expected, data.profile);
  const auto copied = evaluate(
      delta_scheduling_capability_evaluate_copy, expected, data.profile);
  expect(
      borrowed == copied && borrowed == data.decision,
      "borrowed/copy scheduling ABI decisions differ from the frozen fixture");
  auto mutable_profile = data.profile;
  const auto retained = evaluate(
      delta_scheduling_capability_evaluate_borrowed, expected, mutable_profile);
  std::fill(mutable_profile.begin(), mutable_profile.end(), std::uint8_t{0U});
  expect(retained == borrowed, "native scheduling ABI retained borrowed input memory");
}

void test_fail_closed_matrix() {
  const auto data = fixture();
  auto expected = context();
  auto malformed = data.profile;
  malformed.insert(malformed.begin() + 1, static_cast<std::uint8_t>(' '));
  delta_output_buffer_t output{nullptr, 0U, 99U, 99U};
  expect(
      delta_scheduling_capability_evaluate_borrowed(
          &expected, view(malformed), &output) == DELTA_STATUS_INVALID_ARGUMENT &&
          output.required == 0U && output.written == 0U,
      "scheduling ABI accepted noncanonical profile or exposed partial output");
  --expected.struct_size;
  expect(
      delta_scheduling_capability_evaluate_copy(
          &expected, view(data.profile), &output) == DELTA_STATUS_INVALID_ARGUMENT,
      "scheduling ABI accepted incompatible policy struct size");
  expected = context();
  expected.allowed_domain_ids_csv = view("text,code");
  expect(
      delta_scheduling_capability_evaluate_copy(
          &expected, view(data.profile), &output) == DELTA_STATUS_INVALID_ARGUMENT,
      "scheduling ABI accepted noncanonical policy ordering");
}

}  // namespace

int main() {
  try {
    test_borrowed_copy_and_lifetime();
    test_fail_closed_matrix();
  } catch (const std::exception& error) {
    std::cerr << "delta scheduling ABI test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta scheduling ABI tests passed\n";
  return 0;
}
