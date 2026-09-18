#include <delta_benchmark_abi.h>

#include <array>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

[[noreturn]] void fail(const char* message) { throw std::runtime_error(message); }

void expect(bool condition, const char* message) {
  if (!condition) fail(message);
}

void test_metrics_and_echo() {
  static_assert(sizeof(delta_benchmark_metrics_v1_t) == DELTA_BENCHMARK_METRICS_V1_SIZE);
  const auto metrics = delta_benchmark_metrics_v1_t{
      DELTA_BENCHMARK_METRICS_V1_SIZE,
      0U,
      10U,
      20U,
      30U,
      40U,
      50U,
      60U,
      2U,
      1U,
      128U,
  };
  delta_output_buffer_t sizing{nullptr, 0U, 0U, 0U};
  expect(
      delta_benchmark_metrics_canonical(&metrics, &sizing) == DELTA_STATUS_BUFFER_TOO_SMALL,
      "benchmark metrics sizing failed");
  std::vector<std::uint8_t> bytes(sizing.required);
  delta_output_buffer_t output{bytes.data(), bytes.size(), 0U, 0U};
  expect(
      delta_benchmark_metrics_canonical(&metrics, &output) == DELTA_STATUS_OK,
      "benchmark metrics encoding failed");
  const std::string text(bytes.begin(), bytes.end());
  expect(text.find("zero_copy_hits=1\n") != std::string::npos, "zero-copy metric missing");

  const std::array request{std::uint8_t{1}, std::uint8_t{2}, std::uint8_t{3}};
  delta_output_buffer_t echo{bytes.data(), bytes.size(), 0U, 0U};
  expect(
      delta_benchmark_sidecar_echo({request.data(), request.size()}, 16U, &echo) ==
          DELTA_STATUS_OK,
      "sidecar echo failed");
  expect(echo.written == request.size(), "sidecar echo length drifted");
  expect(
      delta_benchmark_sidecar_echo({request.data(), request.size()}, 2U, &echo) ==
          DELTA_STATUS_INVALID_ARGUMENT,
      "sidecar echo accepted an oversized request");
}

}  // namespace

int main() {
  try {
    test_metrics_and_echo();
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
  return 0;
}
