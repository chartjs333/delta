#include <delta_benchmark_abi.h>

#include <delta/runtime/benchmark.hpp>

#include <cstddef>
#include <cstdint>
#include <new>
#include <span>
#include <string>

namespace {

void reset(delta_output_buffer_t* output) noexcept {
  if (output != nullptr) {
    output->required = 0U;
    output->written = 0U;
  }
}

[[nodiscard]] delta_status_t write_bytes(
    std::span<const std::byte> value,
    delta_output_buffer_t* output) noexcept {
  if (output == nullptr) return DELTA_STATUS_INVALID_ARGUMENT;
  output->required = value.size();
  if (output->capacity < value.size()) return DELTA_STATUS_BUFFER_TOO_SMALL;
  if (!value.empty() && output->data == nullptr) return DELTA_STATUS_INVALID_ARGUMENT;
  for (std::size_t index = 0U; index < value.size(); ++index) {
    output->data[index] = std::to_integer<std::uint8_t>(value[index]);
  }
  output->written = value.size();
  return DELTA_STATUS_OK;
}

[[nodiscard]] delta_status_t write_text(
    const std::string& value,
    delta_output_buffer_t* output) noexcept {
  return write_bytes(
      std::as_bytes(std::span<const char>(value.data(), value.size())), output);
}

}  // namespace

extern "C" delta_status_t delta_benchmark_metrics_canonical(
    const delta_benchmark_metrics_v1_t* metrics,
    delta_output_buffer_t* output) {
  reset(output);
  if (metrics == nullptr || metrics->struct_size != DELTA_BENCHMARK_METRICS_V1_SIZE ||
      metrics->reserved != 0U || metrics->zero_copy_hits > metrics->zero_copy_eligible) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  try {
    const delta::runtime::benchmark::Metrics value({
        metrics->java_queue_us,
        metrics->boundary_us,
        metrics->native_transition_us,
        metrics->wal_us,
        metrics->network_us,
        metrics->artifact_us,
        metrics->zero_copy_eligible,
        metrics->zero_copy_hits,
        metrics->copy_fallback_bytes,
    });
    return write_text(value.canonical_text(), output);
  } catch (const std::bad_alloc&) {
    return DELTA_STATUS_INTERNAL_ERROR;
  } catch (...) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
}

extern "C" delta_status_t delta_benchmark_sidecar_echo(
    delta_bytes_view_t request,
    size_t maximum_payload_bytes,
    delta_output_buffer_t* output) {
  reset(output);
  if ((request.size > 0U && request.data == nullptr) || request.size > maximum_payload_bytes ||
      maximum_payload_bytes == 0U) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  try {
    return write_bytes(
        std::as_bytes(std::span<const std::uint8_t>(request.data, request.size)), output);
  } catch (...) {
    return DELTA_STATUS_INTERNAL_ERROR;
  }
}
