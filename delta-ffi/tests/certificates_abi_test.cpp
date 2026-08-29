#include <delta_abi.h>

#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <regex>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

[[noreturn]] void fail(const char* message) { throw std::runtime_error(message); }

void expect(bool condition, const char* message) {
  if (!condition) {
    fail(message);
  }
}

[[nodiscard]] std::uint8_t nibble(char value) {
  if (value >= '0' && value <= '9') {
    return static_cast<std::uint8_t>(value - '0');
  }
  if (value >= 'a' && value <= 'f') {
    return static_cast<std::uint8_t>(10 + value - 'a');
  }
  fail("fixture hex is invalid");
}

[[nodiscard]] std::vector<std::uint8_t> unhex(std::string_view value) {
  expect((value.size() % 2U) == 0U, "fixture hex length is odd");
  std::vector<std::uint8_t> result;
  result.reserve(value.size() / 2U);
  for (std::size_t index = 0U; index < value.size(); index += 2U) {
    result.push_back(static_cast<std::uint8_t>((nibble(value[index]) << 4U) |
                                               nibble(value[index + 1U])));
  }
  return result;
}

struct Fixture {
  std::vector<std::uint8_t> bytes;
  std::string content_id;
};

[[nodiscard]] Fixture fixture() {
  std::ifstream input(DELTA_CERTIFICATE_GOLDEN_PATH, std::ios::binary);
  expect(input.good(), "cannot open certificate fixture");
  const std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  const std::regex pattern(
      R"REGEX("input_set_certificate":\{"bytes_hex":"([0-9a-f]+)","content_id":"(sha256:[0-9a-f]{64})")REGEX");
  std::smatch match;
  expect(std::regex_search(document, match, pattern), "input-set fixture is missing");
  return {unhex(match[1].str()), match[2].str()};
}

[[nodiscard]] delta_bytes_view_t view(std::string_view value) {
  return {reinterpret_cast<const std::uint8_t*>(value.data()), value.size()};
}

[[nodiscard]] delta_bytes_view_t view(const std::vector<std::uint8_t>& value) {
  return {value.data(), value.size()};
}

using Function = delta_status_t (*)(
    const delta_certificate_inspect_context_t*,
    delta_bytes_view_t,
    delta_output_buffer_t*);

[[nodiscard]] std::vector<std::uint8_t> inspect(
    Function function,
    const delta_certificate_inspect_context_t& context,
    const std::vector<std::uint8_t>& bytes) {
  delta_output_buffer_t sizing{nullptr, 0U, 0U, 0U};
  expect(
      function(&context, view(bytes), &sizing) == DELTA_STATUS_BUFFER_TOO_SMALL,
      "certificate ABI did not negotiate output size");
  expect(sizing.required > 0U && sizing.written == 0U, "certificate ABI size is invalid");
  std::vector<std::uint8_t> result(sizing.required);
  delta_output_buffer_t output{result.data(), result.size(), 0U, 0U};
  expect(
      function(&context, view(bytes), &output) == DELTA_STATUS_OK &&
          output.written == result.size(),
      "certificate ABI retry failed");
  return result;
}

void test_abi() {
  static_assert(
      sizeof(delta_certificate_inspect_context_t) == DELTA_CERTIFICATE_INSPECT_CONTEXT_SIZE);
  const auto value = fixture();
  const auto context = delta_certificate_inspect_context_t{
      DELTA_CERTIFICATE_INSPECT_CONTEXT_SIZE,
      DELTA_CERTIFICATE_INPUT_SET,
      view(value.content_id),
      view(DELTA_FORMAL_SEMANTICS_ID),
  };
  const auto borrowed = inspect(delta_certificate_inspect_borrowed, context, value.bytes);
  const auto copied = inspect(delta_certificate_inspect_copy, context, value.bytes);
  expect(borrowed == copied, "borrowed/copy certificate effects differ");
  auto corrupted = value.bytes;
  corrupted.back() = static_cast<std::uint8_t>(']');
  delta_output_buffer_t output{nullptr, 0U, 91U, 92U};
  expect(
      delta_certificate_inspect_borrowed(&context, view(corrupted), &output) ==
              DELTA_STATUS_TRANSITION_REJECTED &&
          output.required == 0U && output.written == 0U,
      "certificate ABI accepted corrupt bytes or exposed partial output");
  auto wrong = context;
  wrong.kind = DELTA_CERTIFICATE_APPLY_QC;
  expect(
      delta_certificate_inspect_copy(&wrong, view(value.bytes), &output) ==
          DELTA_STATUS_TRANSITION_REJECTED,
      "certificate ABI accepted the wrong type domain");
}

}  // namespace

int main() {
  try {
    test_abi();
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
  return 0;
}
