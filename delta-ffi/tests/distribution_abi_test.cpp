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

[[nodiscard]] std::vector<std::uint8_t> unhex(std::string_view value) {
  const auto nibble = [](char character) -> unsigned {
    if (character >= '0' && character <= '9') {
      return static_cast<unsigned>(character - '0');
    }
    if (character >= 'a' && character <= 'f') {
      return static_cast<unsigned>(character - 'a') + 10U;
    }
    fail("fixture contains non-hex bytes");
  };
  std::vector<std::uint8_t> result;
  result.reserve(value.size() / 2U);
  for (std::size_t index = 0U; index < value.size(); index += 2U) {
    result.push_back(static_cast<std::uint8_t>((nibble(value[index]) << 4U) | nibble(value[index + 1U])));
  }
  return result;
}

struct Fixture {
  std::vector<std::uint8_t> manifest;
  std::vector<std::uint8_t> certificate;
};

[[nodiscard]] Fixture fixture() {
  std::ifstream input(DELTA_DISTRIBUTION_GOLDEN_PATH, std::ios::binary);
  expect(input.good(), "cannot open distribution fixture");
  const std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  std::smatch match;
  expect(std::regex_search(
             document, match,
             std::regex(R"REGEX("manifest":\{"bytes_hex":"([0-9a-f]+)")REGEX")),
         "manifest fixture is missing");
  auto manifest = unhex(match[1].str());
  expect(std::regex_search(
             document, match,
             std::regex(R"REGEX("certificate":\{"bytes_hex":"([0-9a-f]+)")REGEX")),
         "certificate fixture is missing");
  return Fixture{std::move(manifest), unhex(match[1].str())};
}

[[nodiscard]] delta_bytes_view_t view(const std::vector<std::uint8_t>& value) {
  return delta_bytes_view_t{value.data(), value.size()};
}

[[nodiscard]] std::string evaluate(const Fixture& input, bool copy, std::uint8_t make_current = 0U) {
  delta_output_buffer_t sizing{nullptr, 0U, 0U, 0U};
  const auto first = copy
                         ? delta_distribution_policy_evaluate_copy(
                               view(input.manifest), view(input.certificate), make_current, &sizing)
                         : delta_distribution_policy_evaluate_borrowed(
                               view(input.manifest), view(input.certificate), make_current, &sizing);
  expect(first == DELTA_STATUS_BUFFER_TOO_SMALL && sizing.required > 0U && sizing.written == 0U,
         "distribution effect sizing failed");
  std::vector<std::uint8_t> bytes(sizing.required);
  delta_output_buffer_t output{bytes.data(), bytes.size(), 0U, 0U};
  const auto second = copy
                          ? delta_distribution_policy_evaluate_copy(
                                view(input.manifest), view(input.certificate), make_current, &output)
                          : delta_distribution_policy_evaluate_borrowed(
                                view(input.manifest), view(input.certificate), make_current, &output);
  expect(second == DELTA_STATUS_OK && output.required == bytes.size() &&
             output.written == bytes.size(),
         "distribution effect retry failed");
  return std::string(bytes.begin(), bytes.end());
}

void test_direct_copy_parity() {
  auto input = fixture();
  const auto borrowed = evaluate(input, false);
  const auto copied = evaluate(input, true);
  expect(borrowed == copied, "borrowed and copy policy effects differ");
  expect(borrowed.find("\"status\":\"ACCEPT\"") != std::string::npos,
         "golden policy effect is not ACCEPT");
  std::fill(input.manifest.begin(), input.manifest.end(), std::uint8_t{0U});
  expect(copied.find("d48ff2208") != std::string::npos,
         "copy path retained caller-owned memory");

  const auto current = evaluate(fixture(), false, 1U);
  expect(current.find("CURRENT_REQUIRES_APPLY_QC") != std::string::npos,
         "current-pointer protection was bypassed");

  delta_output_buffer_t output{nullptr, 0U, 99U, 99U};
  const auto valid = fixture();
  expect(delta_distribution_policy_evaluate_borrowed(
             view(valid.manifest), view(valid.certificate), 2U, &output) ==
             DELTA_STATUS_INVALID_ARGUMENT,
         "invalid make-current flag escaped stable status mapping");
  expect(output.required == 0U && output.written == 0U,
         "invalid ABI input exposed partial output metadata");
}

}  // namespace

int main() {
  try {
    test_direct_copy_parity();
  } catch (const std::exception& error) {
    std::cerr << "distribution ABI test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "distribution ABI tests passed\n";
  return 0;
}
