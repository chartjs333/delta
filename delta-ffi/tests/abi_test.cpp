#include <delta_abi.h>

#include <cstddef>
#include <cstdint>
#include <filesystem>
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

[[nodiscard]] std::uint8_t hex_nibble(char value) {
  if (value >= '0' && value <= '9') {
    return static_cast<std::uint8_t>(value - '0');
  }
  if (value >= 'a' && value <= 'f') {
    return static_cast<std::uint8_t>(value - 'a' + 10);
  }
  fail("invalid lowercase hexadecimal fixture");
}

[[nodiscard]] std::vector<std::uint8_t> decode_hex(std::string_view encoded) {
  expect((encoded.size() % 2U) == 0U, "odd hexadecimal fixture length");
  std::vector<std::uint8_t> result;
  result.reserve(encoded.size() / 2U);
  for (std::size_t index = 0; index < encoded.size(); index += 2U) {
    result.push_back(static_cast<std::uint8_t>(
        static_cast<std::uint8_t>(hex_nibble(encoded[index]) << 4U) |
        hex_nibble(encoded[index + 1U])));
  }
  return result;
}

[[nodiscard]] std::vector<std::uint8_t> golden(std::uint16_t type_code) {
  std::ifstream input(DELTA_GOLDEN_FIXTURE_PATH, std::ios::binary);
  expect(input.good(), "cannot open canonical golden fixture");
  const std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  const std::regex pattern(
      R"REGEX("envelope_hex":"([0-9a-f]+)","envelope_sha256":"[0-9a-f]+","type_code":([0-9]+))REGEX");
  for (auto cursor = std::sregex_iterator(document.begin(), document.end(), pattern);
       cursor != std::sregex_iterator();
       ++cursor) {
    if (std::stoul((*cursor)[2].str()) == type_code) {
      return decode_hex((*cursor)[1].str());
    }
  }
  fail("registered golden vector not found");
}

[[nodiscard]] delta_bytes_view_t view(std::string_view value) {
  return {reinterpret_cast<const std::uint8_t*>(value.data()), value.size()};
}

[[nodiscard]] delta_bytes_view_t view(const std::vector<std::uint8_t>& value) {
  return {value.data(), value.size()};
}

[[nodiscard]] delta_runtime_open_options_t options(
    std::string_view directory,
    const std::vector<std::uint8_t>& initial_state) {
  return delta_runtime_open_options_t{
      DELTA_ABI_OPEN_OPTIONS_SIZE,
      64U,
      view(directory),
      view(initial_state),
      DELTA_ABI_MAJOR,
      DELTA_ABI_MINOR,
      0U,
      view(DELTA_SCHEMA_VERSION),
      view(DELTA_PROTOCOL_VERSION),
      view(DELTA_FORMAL_SEMANTICS_ID),
      view(DELTA_BUILD_ID),
      view(DELTA_SCHEMA_SET_ID),
  };
}

[[nodiscard]] std::filesystem::path fresh_directory(std::string_view name) {
  auto result = std::filesystem::temp_directory_path() / "delta-ffi-003-tests" / name;
  std::error_code error;
  std::filesystem::remove_all(result, error);
  expect(!error, "cannot clean exact ABI test directory");
  std::filesystem::create_directories(result, error);
  expect(!error, "cannot create ABI test directory");
  return result;
}

void test_frozen_descriptor_and_status_taxonomy() {
  expect(sizeof(delta_runtime_descriptor_t) == 64U, "descriptor ABI size changed");
  expect(sizeof(delta_runtime_open_options_t) == 128U, "open-options ABI size changed");
  expect(sizeof(delta_output_buffer_t) == 32U, "output-buffer ABI size changed");

  delta_runtime_descriptor_t descriptor{};
  expect(
      delta_runtime_descriptor(DELTA_ABI_DESCRIPTOR_SIZE - 1U, &descriptor) ==
          DELTA_STATUS_ABI_MISMATCH,
      "descriptor size mismatch was accepted");
  expect(descriptor.struct_size == 0U, "descriptor mismatch exposed partial fields");
  expect(
      delta_runtime_descriptor(DELTA_ABI_DESCRIPTOR_SIZE, &descriptor) == DELTA_STATUS_OK,
      "descriptor query failed");
  expect(
      descriptor.struct_size == DELTA_ABI_DESCRIPTOR_SIZE &&
          descriptor.abi_major == DELTA_ABI_MAJOR && descriptor.abi_minor == DELTA_ABI_MINOR &&
          descriptor.feature_bits == DELTA_ABI_FEATURE_BITS,
      "descriptor numeric fields mismatch");
  expect(descriptor.formal_semantics_id == std::string_view(DELTA_FORMAL_SEMANTICS_ID),
         "descriptor formal semantics mismatch");
  expect(descriptor.build_id == std::string_view(DELTA_BUILD_ID), "descriptor build mismatch");
  for (int status = DELTA_STATUS_OK; status <= DELTA_STATUS_INTERNAL_ERROR; ++status) {
    expect(
        std::string_view(delta_status_message(static_cast<delta_status_t>(status))) !=
            "UNKNOWN_STATUS",
        "registered status has no stable name");
  }
}

void test_startup_mismatch_matrix() {
  const auto initial = golden(5U);
  const auto directory = fresh_directory("mismatch").string();
  auto valid = options(directory, initial);
  delta_runtime_t* output = reinterpret_cast<delta_runtime_t*>(UINTPTR_MAX);

  auto changed = valid;
  changed.expected_abi_major = 2U;
  expect(delta_runtime_open(&changed, &output) == DELTA_STATUS_ABI_MISMATCH && output == nullptr,
         "ABI mismatch did not fail closed");

  const std::string wrong_schema = "2.0.0";
  changed = valid;
  changed.expected_schema_version = view(wrong_schema);
  expect(delta_runtime_open(&changed, &output) == DELTA_STATUS_SCHEMA_MISMATCH && output == nullptr,
         "schema mismatch did not fail closed");

  const std::string wrong_protocol = "999.0.0";
  changed = valid;
  changed.expected_protocol_version = view(wrong_protocol);
  expect(
      delta_runtime_open(&changed, &output) == DELTA_STATUS_PROTOCOL_MISMATCH && output == nullptr,
      "protocol mismatch did not fail closed");

  const std::string wrong_formal =
      "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
  changed = valid;
  changed.expected_formal_semantics_id = view(wrong_formal);
  expect(
      delta_runtime_open(&changed, &output) == DELTA_STATUS_FORMAL_SEMANTICS_MISMATCH &&
          output == nullptr,
      "formal mismatch did not fail closed");

  const std::string wrong_build =
      "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb";
  changed = valid;
  changed.expected_build_id = view(wrong_build);
  expect(
      delta_runtime_open(&changed, &output) == DELTA_STATUS_BUILD_MISMATCH && output == nullptr,
      "build mismatch did not fail closed");

  const std::string wrong_schema_set =
      "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc";
  changed = valid;
  changed.expected_schema_set_id = view(wrong_schema_set);
  expect(
      delta_runtime_open(&changed, &output) == DELTA_STATUS_SCHEMA_MISMATCH && output == nullptr,
      "schema-set mismatch did not fail closed");
}

[[nodiscard]] std::vector<std::uint8_t> retry_effect(
    delta_runtime_t* runtime,
    const std::vector<std::uint8_t>& command,
    bool copy_path) {
  delta_output_buffer_t sizing{nullptr, 0U, 0U, 0U};
  const auto first = copy_path ? delta_runtime_submit_copy(runtime, view(command), &sizing)
                               : delta_runtime_submit_borrowed(runtime, view(command), &sizing);
  expect(first == DELTA_STATUS_BUFFER_TOO_SMALL, "zero-capacity call did not negotiate size");
  expect(sizing.required > 0U && sizing.written == 0U, "size negotiation exposed partial bytes");
  std::vector<std::uint8_t> output(sizing.required);
  delta_output_buffer_t destination{output.data(), output.size(), 0U, 0U};
  const auto second = copy_path ? delta_runtime_submit_copy(runtime, view(command), &destination)
                                : delta_runtime_submit_borrowed(runtime, view(command), &destination);
  expect(second == DELTA_STATUS_OK, "capacity retry failed");
  expect(destination.required == output.size() && destination.written == output.size(),
         "capacity retry size fields mismatch");
  return output;
}

void test_open_submit_snapshot_release_and_memory_rules() {
  const auto initial = golden(5U);
  auto command = golden(6U);
  const auto directory = fresh_directory("lifecycle").string();
  auto open_options = options(directory, initial);
  delta_runtime_t* handle = nullptr;
  expect(delta_runtime_open(&open_options, &handle) == DELTA_STATUS_OK && handle != nullptr,
         "valid ABI open failed");

  const auto borrowed_effect = retry_effect(handle, command, false);
  const auto copy_effect = retry_effect(handle, command, true);
  expect(borrowed_effect == copy_effect, "borrowed and copy paths produced different effects");
  std::fill(command.begin(), command.end(), std::uint8_t{0U});
  expect(delta_runtime_snapshot(handle) == DELTA_STATUS_OK,
         "native retained borrowed command memory after synchronous call");

  delta_output_buffer_t state_size{nullptr, 0U, 0U, 0U};
  expect(delta_runtime_state(handle, &state_size) == DELTA_STATUS_BUFFER_TOO_SMALL,
         "state getter did not negotiate size");
  std::vector<std::uint8_t> state(state_size.required);
  delta_output_buffer_t state_output{state.data(), state.size(), 0U, 0U};
  expect(delta_runtime_state(handle, &state_output) == DELTA_STATUS_OK,
         "state getter retry failed");
  expect(state == initial, "round-config replay unexpectedly changed state bytes");

  std::vector<std::uint8_t> malformed{0U, 1U, 2U};
  std::vector<std::uint8_t> sentinel(16U, 0x5aU);
  delta_output_buffer_t rejected{sentinel.data(), sentinel.size(), 99U, 99U};
  expect(delta_runtime_submit_borrowed(handle, view(malformed), &rejected) ==
             DELTA_STATUS_INVALID_ARGUMENT,
         "malformed command escaped stable status mapping");
  expect(rejected.required == 0U && rejected.written == 0U,
         "rejected command exposed partial output metadata");
  expect(delta_runtime_release(&handle) == DELTA_STATUS_OK && handle == nullptr,
         "explicit handle release failed");
  expect(delta_runtime_release(&handle) == DELTA_STATUS_OK && handle == nullptr,
         "repeated null handle release was not idempotent");
}

}  // namespace

int main() {
  try {
    test_frozen_descriptor_and_status_taxonomy();
    test_startup_mismatch_matrix();
    test_open_submit_snapshot_release_and_memory_rules();
  } catch (const std::exception& error) {
    std::cerr << "delta_ffi ABI test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta_ffi ABI tests passed\n";
  return 0;
}
