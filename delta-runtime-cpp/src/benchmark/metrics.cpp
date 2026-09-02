#include <delta/runtime/benchmark.hpp>

#include <charconv>
#include <string>

namespace delta::runtime::benchmark {
namespace {

void append_number(std::string& output, std::uint64_t value) {
  char buffer[32]{};
  const auto result = std::to_chars(buffer, buffer + sizeof(buffer), value);
  if (result.ec != std::errc{}) {
    throw BenchmarkError("metric encoding failed");
  }
  output.append(buffer, result.ptr);
}

}  // namespace

Metrics::Metrics(MetricsSnapshot initial) : value_(initial) {
  if (value_.zero_copy_hits > value_.zero_copy_eligible) {
    throw BenchmarkError("zero-copy hits exceed eligible operations");
  }
}

void Metrics::add_phase(std::string_view phase, std::uint64_t microseconds) {
  auto* target = [&]() -> std::uint64_t* {
    if (phase == "java_queue") return &value_.java_queue_us;
    if (phase == "boundary") return &value_.boundary_us;
    if (phase == "native_transition") return &value_.native_transition_us;
    if (phase == "wal") return &value_.wal_us;
    if (phase == "network") return &value_.network_us;
    if (phase == "artifact") return &value_.artifact_us;
    return nullptr;
  }();
  if (target == nullptr || microseconds > UINT64_MAX - *target) {
    throw BenchmarkError("invalid or overflowing benchmark phase");
  }
  *target += microseconds;
}

void Metrics::record_zero_copy(bool eligible, bool used, std::uint64_t fallback_bytes) {
  if (used && !eligible) {
    throw BenchmarkError("zero-copy use was not eligible");
  }
  if ((eligible && value_.zero_copy_eligible == UINT64_MAX) ||
      (used && value_.zero_copy_hits == UINT64_MAX)) {
    throw BenchmarkError("zero-copy counter overflow");
  }
  value_.zero_copy_eligible += eligible ? 1U : 0U;
  value_.zero_copy_hits += used ? 1U : 0U;
  if (fallback_bytes > UINT64_MAX - value_.copy_fallback_bytes) {
    throw BenchmarkError("copy fallback counter overflow");
  }
  value_.copy_fallback_bytes += fallback_bytes;
}

MetricsSnapshot Metrics::snapshot() const noexcept { return value_; }

std::string Metrics::canonical_text() const {
  const auto values = snapshot();
  std::string output;
  for (const auto& [name, value] : std::initializer_list<std::pair<std::string_view, std::uint64_t>>{
           {"artifact_us", values.artifact_us},
           {"boundary_us", values.boundary_us},
           {"copy_fallback_bytes", values.copy_fallback_bytes},
           {"java_queue_us", values.java_queue_us},
           {"native_transition_us", values.native_transition_us},
           {"network_us", values.network_us},
           {"wal_us", values.wal_us},
           {"zero_copy_eligible", values.zero_copy_eligible},
           {"zero_copy_hits", values.zero_copy_hits},
       }) {
    output.append(name);
    output.push_back('=');
    append_number(output, value);
    output.push_back('\n');
  }
  return output;
}

}  // namespace delta::runtime::benchmark
