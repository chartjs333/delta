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
  fail("hierarchy ABI fixture contains non-hex bytes");
}

[[nodiscard]] std::vector<std::uint8_t> unhex(std::string_view input) {
  expect((input.size() % 2U) == 0U, "hierarchy ABI fixture has odd hex length");
  std::vector<std::uint8_t> output;
  output.reserve(input.size() / 2U);
  for (std::size_t index = 0U; index < input.size(); index += 2U) {
    output.push_back(static_cast<std::uint8_t>(
        static_cast<std::uint8_t>(nibble(input[index]) << 4U) | nibble(input[index + 1U])));
  }
  return output;
}

struct Fixture {
  std::vector<std::uint8_t> topology;
  std::vector<std::uint8_t> proof;
};

[[nodiscard]] Fixture fixture() {
  std::ifstream input(DELTA_HIERARCHY_GOLDEN_PATH, std::ios::binary);
  expect(input.good(), "cannot open hierarchy ABI golden fixture");
  const std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  const std::regex topology_pattern(
      R"REGEX("topology":\{"bytes_hex":"([0-9a-f]+)")REGEX");
  const std::regex proof_pattern(
      R"REGEX("hierarchy_proof_instance":\{"bytes_hex":"([0-9a-f]+)")REGEX");
  std::smatch match;
  expect(std::regex_search(document, match, topology_pattern), "ABI topology fixture is missing");
  auto topology = unhex(match[1].str());
  expect(std::regex_search(document, match, proof_pattern), "ABI proof fixture is missing");
  return {std::move(topology), unhex(match[1].str())};
}

[[nodiscard]] delta_bytes_view_t view(std::string_view input) {
  return {reinterpret_cast<const std::uint8_t*>(input.data()), input.size()};
}

[[nodiscard]] delta_bytes_view_t view(const std::vector<std::uint8_t>& input) {
  return {input.data(), input.size()};
}

[[nodiscard]] delta_hierarchy_context_t context() {
  return {
      DELTA_HIERARCHY_CONTEXT_SIZE,
      0U,
      view("sha256:993b4d5104810dd26a3159b60cf8fe9afe6154cdcca90d22b577ae1b6d1ac076"),
      view("sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"),
      view("sha256:34bc08c316dfe22efe155ed11b866bcc0daf7ef8c3c7389c56b2f2c707443629"),
      view("sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6"),
      view("sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"),
      view("sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"),
      view("sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61"),
      view("sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"),
      view("sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205"),
      view("sha256:4c644a3254edb3d7bff009bbe91ee99df6051516362fa1a1eac6f0a803a9c7a1"),
  };
}

using Function = delta_status_t (*)(
    const delta_hierarchy_context_t*, delta_bytes_view_t, delta_bytes_view_t,
    delta_output_buffer_t*);

[[nodiscard]] std::string validate(
    Function function,
    const delta_hierarchy_context_t& expected,
    const std::vector<std::uint8_t>& topology,
    const std::vector<std::uint8_t>& proof) {
  delta_output_buffer_t sizing{nullptr, 0U, 0U, 0U};
  expect(function(&expected, view(topology), view(proof), &sizing) == DELTA_STATUS_BUFFER_TOO_SMALL,
         "hierarchy ABI did not negotiate bounded output");
  expect(sizing.required > 0U && sizing.required <= 512U && sizing.written == 0U,
         "hierarchy ABI sizing escaped effect bounds");
  std::vector<std::uint8_t> bytes(sizing.required);
  delta_output_buffer_t output{bytes.data(), bytes.size(), 0U, 0U};
  expect(function(&expected, view(topology), view(proof), &output) == DELTA_STATUS_OK &&
             output.required == bytes.size() && output.written == bytes.size(),
         "hierarchy ABI bounded retry failed");
  return {bytes.begin(), bytes.end()};
}

void test_borrowed_copy_and_lifetime() {
  static_assert(sizeof(delta_hierarchy_context_t) == DELTA_HIERARCHY_CONTEXT_SIZE);
  const auto data = fixture();
  const auto expected = context();
  const auto borrowed = validate(
      delta_hierarchy_contract_validate_borrowed, expected, data.topology, data.proof);
  const auto copied = validate(
      delta_hierarchy_contract_validate_copy, expected, data.topology, data.proof);
  expect(borrowed == copied &&
             borrowed ==
                 "{\"hierarchy_proof_instance_id\":\"sha256:cdad45d964352c7cd33e1588279ce4459fdb1c959661029fb56ee567b00c5245\",\"routing_projection_id\":\"sha256:22caad4705d05abcdb56958095bacd1686dc37d9d1b8996f3bf2f312f79a3472\",\"status\":\"ACCEPT\",\"topology_id\":\"sha256:99b0c5ce4fe5c850e95750d39c8a9844148adc8b0f00353da02f2f1ad00da157\"}",
         "borrowed/copy hierarchy ABI effects differ from frozen identities");

  auto mutable_topology = data.topology;
  const auto retained_effect = validate(
      delta_hierarchy_contract_validate_borrowed, expected, mutable_topology, data.proof);
  std::fill(mutable_topology.begin(), mutable_topology.end(), std::uint8_t{0U});
  expect(retained_effect == borrowed, "native hierarchy ABI retained borrowed input memory");
}

void test_fail_closed_matrix() {
  const auto data = fixture();
  auto expected = context();
  auto malformed = data.topology;
  malformed.insert(malformed.begin() + 1, static_cast<std::uint8_t>(' '));
  delta_output_buffer_t output{nullptr, 0U, 99U, 99U};
  expect(delta_hierarchy_contract_validate_borrowed(
             &expected, view(malformed), view(data.proof), &output) ==
             DELTA_STATUS_INVALID_ARGUMENT &&
             output.required == 0U && output.written == 0U,
         "hierarchy ABI accepted noncanonical topology or exposed partial output");
  expected.frozen_input_root =
      view("sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee");
  expect(delta_hierarchy_contract_validate_copy(
             &expected, view(data.topology), view(data.proof), &output) ==
             DELTA_STATUS_INVALID_ARGUMENT,
         "hierarchy ABI accepted wrong frozen context");
  expected = context();
  --expected.struct_size;
  expect(delta_hierarchy_contract_validate_copy(
             &expected, view(data.topology), view(data.proof), &output) ==
             DELTA_STATUS_INVALID_ARGUMENT,
         "hierarchy ABI accepted incompatible context struct size");
}

}  // namespace

int main() {
  try {
    test_borrowed_copy_and_lifetime();
    test_fail_closed_matrix();
  } catch (const std::exception& error) {
    std::cerr << "delta hierarchy ABI test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta hierarchy ABI tests passed\n";
  return 0;
}
