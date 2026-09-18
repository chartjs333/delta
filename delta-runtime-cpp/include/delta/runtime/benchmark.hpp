#pragma once

#include <cstddef>
#include <cstdint>
#include <map>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace delta::runtime::benchmark {

inline constexpr std::string_view formal_semantics_id =
    "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";

class BenchmarkError final : public std::runtime_error {
 public:
  using std::runtime_error::runtime_error;
};

struct MetricsSnapshot {
  std::uint64_t java_queue_us{};
  std::uint64_t boundary_us{};
  std::uint64_t native_transition_us{};
  std::uint64_t wal_us{};
  std::uint64_t network_us{};
  std::uint64_t artifact_us{};
  std::uint64_t zero_copy_eligible{};
  std::uint64_t zero_copy_hits{};
  std::uint64_t copy_fallback_bytes{};

  bool operator==(const MetricsSnapshot&) const = default;
};

class Metrics {
 public:
  explicit Metrics(MetricsSnapshot initial = {});
  void add_phase(std::string_view phase, std::uint64_t microseconds);
  void record_zero_copy(bool eligible, bool used, std::uint64_t fallback_bytes);
  [[nodiscard]] MetricsSnapshot snapshot() const noexcept;
  [[nodiscard]] std::string canonical_text() const;

 private:
  MetricsSnapshot value_{};
};

enum class FaultAction { crash, delay, disconnect, drop_storage, duplicate, partition, reorder, restart };

struct FaultEvent {
  std::string event_id;
  std::string actor_class;
  FaultAction action{};
  std::uint64_t logical_step{};
  bool assumptions_hold{};
  std::string expected_outcome;

  bool operator==(const FaultEvent&) const = default;
};

class FaultController {
 public:
  explicit FaultController(std::vector<FaultEvent> events);
  [[nodiscard]] std::vector<FaultEvent> events_at(std::uint64_t logical_step) const;
  [[nodiscard]] const std::vector<FaultEvent>& events() const noexcept;

 private:
  std::vector<FaultEvent> events_;
};

struct TraceEntry {
  std::uint64_t sequence{};
  std::string action_id;
  std::string state_id;
  std::string effect_id;
  std::string terminal_outcome;

  bool operator==(const TraceEntry&) const = default;
};

class TraceExporter {
 public:
  void append(TraceEntry entry);
  [[nodiscard]] const std::vector<TraceEntry>& entries() const noexcept;
  [[nodiscard]] std::string canonical_text() const;

 private:
  std::vector<TraceEntry> entries_;
};

struct SidecarReceipt {
  std::uint64_t request_sequence{};
  std::vector<std::byte> response;
  bool replay{};

  bool operator==(const SidecarReceipt&) const = default;
};

class SidecarServer {
 public:
  SidecarServer(std::size_t queue_capacity, std::size_t maximum_payload_bytes);
  [[nodiscard]] SidecarReceipt execute(std::string request_id, std::span<const std::byte> payload);
  void crash() noexcept;
  void restart() noexcept;
  [[nodiscard]] bool accepting() const noexcept;
  [[nodiscard]] std::size_t replay_entry_count() const noexcept;

 private:
  std::size_t queue_capacity_;
  std::size_t maximum_payload_bytes_;
  bool accepting_{true};
  std::uint64_t next_sequence_{1U};
  std::map<std::string, SidecarReceipt, std::less<>> receipts_;
};

}  // namespace delta::runtime::benchmark
