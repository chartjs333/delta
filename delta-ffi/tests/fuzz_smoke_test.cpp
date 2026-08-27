#include <delta_abi.h>

#include "../../delta-runtime-cpp/tests/fixture_support.hpp"

#include <delta/core/canonical.hpp>
#include <delta/core/protocol.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <iostream>
#include <limits>
#include <string>
#include <string_view>
#include <vector>

namespace canonical = delta::core::canonical;
namespace protocol = delta::core::protocol;
namespace test = delta::test;

namespace {

[[nodiscard]] delta_bytes_view_t view(const canonical::Bytes& value) {
  return {
      reinterpret_cast<const std::uint8_t*>(value.data()),
      value.size(),
  };
}

[[nodiscard]] delta_bytes_view_t view(std::string_view value) {
  return {
      reinterpret_cast<const std::uint8_t*>(value.data()),
      value.size(),
  };
}

[[nodiscard]] delta_runtime_open_options_t options(
    std::string_view directory,
    const canonical::Bytes& initial) {
  return delta_runtime_open_options_t{
      DELTA_ABI_OPEN_OPTIONS_SIZE,
      64U,
      view(directory),
      view(initial),
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

[[nodiscard]] std::uint64_t next_random(std::uint64_t& state) noexcept {
  state ^= state << 13U;
  state ^= state >> 7U;
  state ^= state << 17U;
  return state;
}

void exercise_parsers(std::span<const std::byte> bytes) {
  try {
    static_cast<void>(canonical::decode(bytes));
  } catch (const canonical::DecodeError&) {
  }
  try {
    static_cast<void>(protocol::parse_command(bytes));
  } catch (const std::exception&) {
  }
  try {
    static_cast<void>(protocol::parse_round_state(bytes));
  } catch (const std::exception&) {
  }
  try {
    static_cast<void>(protocol::parse_vote(bytes));
  } catch (const std::exception&) {
  }
  try {
    static_cast<void>(protocol::parse_quorum_certificate(bytes));
  } catch (const std::exception&) {
  }
  try {
    static_cast<void>(protocol::parse_prepared_integer_shard(bytes));
  } catch (const std::exception&) {
  }
}

void exercise_abi(delta_runtime_t* runtime, const canonical::Bytes& bytes, bool copy_path) {
  delta_output_buffer_t sizing{nullptr, 0U, 99U, 99U};
  const auto first = copy_path ? delta_runtime_submit_copy(runtime, view(bytes), &sizing)
                               : delta_runtime_submit_borrowed(runtime, view(bytes), &sizing);
  test::expect(
      first != DELTA_STATUS_INTERNAL_ERROR && first != DELTA_STATUS_IO_ERROR &&
          first != DELTA_STATUS_CORRUPT_DURABLE_STATE,
      "bounded ABI fuzz input escaped stable fail-closed handling");
  if (first == DELTA_STATUS_BUFFER_TOO_SMALL) {
    test::expect(
        sizing.required > 0U && sizing.required <= 16U * 1024U * 1024U && sizing.written == 0U,
        "ABI fuzz sizing result is not bounded");
    std::vector<std::uint8_t> output(sizing.required);
    delta_output_buffer_t retry{output.data(), output.size(), 0U, 0U};
    const auto second = copy_path ? delta_runtime_submit_copy(runtime, view(bytes), &retry)
                                  : delta_runtime_submit_borrowed(runtime, view(bytes), &retry);
    test::expect(
        second == DELTA_STATUS_OK && retry.required == retry.written &&
            retry.written == output.size(),
        "ABI fuzz output-capacity retry changed outcome");
  } else if (first != DELTA_STATUS_OK) {
    test::expect(
        sizing.required == 0U && sizing.written == 0U,
        "rejected ABI fuzz input exposed partial output metadata");
  }
}

}  // namespace

int main() {
  try {
    const auto initial = test::golden(DELTA_GOLDEN_FIXTURE_PATH, 5U);
    const auto seed = test::golden(DELTA_GOLDEN_FIXTURE_PATH, 6U);
    const auto directory = test::fresh_directory("ffi-fuzz-smoke").string();
    auto open_options = options(directory, initial);
    delta_runtime_t* handle = nullptr;
    test::expect(
        delta_runtime_open(&open_options, &handle) == DELTA_STATUS_OK && handle != nullptr,
        "cannot open bounded ABI fuzz runtime");

    delta_output_buffer_t rejected{nullptr, 0U, 77U, 77U};
    test::expect(
        delta_runtime_submit_borrowed(handle, {nullptr, 1U}, &rejected) ==
            DELTA_STATUS_INVALID_ARGUMENT &&
            rejected.required == 0U && rejected.written == 0U,
        "invalid borrowed pointer did not fail closed");

    exercise_parsers({});
    const auto truncated = test::decode_hex("44524331");
    const auto unknown = test::decode_hex("445243310100ffff00000000");
    exercise_parsers(truncated);
    exercise_parsers(unknown);
    exercise_abi(handle, truncated, false);
    exercise_abi(handle, unknown, true);

    std::uint64_t random = UINT64_C(0x9e3779b97f4a7c15);
    for (std::size_t iteration = 0U; iteration < 2'048U; ++iteration) {
      auto mutated = seed;
      const auto operation = next_random(random) % 4U;
      if (operation == 0U && !mutated.empty()) {
        mutated.resize(static_cast<std::size_t>(next_random(random) % mutated.size()));
      } else if (operation == 1U && !mutated.empty()) {
        const auto index = static_cast<std::size_t>(next_random(random) % mutated.size());
        mutated[index] ^= static_cast<std::byte>(1U << (next_random(random) % 8U));
      } else if (operation == 2U && mutated.size() < 4'096U) {
        mutated.push_back(static_cast<std::byte>(next_random(random) & 0xffU));
      } else if (!mutated.empty()) {
        const auto index = static_cast<std::size_t>(next_random(random) % mutated.size());
        mutated[index] = static_cast<std::byte>(next_random(random) & 0xffU);
      }
      exercise_parsers(mutated);
      exercise_abi(handle, mutated, (iteration % 2U) != 0U);
    }
    test::expect(
        delta_runtime_release(&handle) == DELTA_STATUS_OK && handle == nullptr,
        "ABI fuzz runtime release failed");
  } catch (const std::exception& error) {
    std::cerr << "bounded parser/ABI fuzz smoke failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "bounded parser and ABI fuzz smoke passed: 2052 cases\n";
  return 0;
}
