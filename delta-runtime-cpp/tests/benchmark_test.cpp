#include <delta/runtime/benchmark.hpp>

#include <array>
#include <cstddef>
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

[[noreturn]] void fail(const char* message) { throw std::runtime_error(message); }

void expect(bool condition, const char* message) {
  if (!condition) fail(message);
}

void test_metrics_and_trace() {
  delta::runtime::benchmark::Metrics metrics;
  metrics.add_phase("boundary", 25U);
  metrics.add_phase("wal", 75U);
  metrics.record_zero_copy(true, true, 0U);
  metrics.record_zero_copy(false, false, 128U);
  const auto snapshot = metrics.snapshot();
  expect(snapshot.boundary_us == 25U && snapshot.wal_us == 75U, "phase metrics drifted");
  expect(
      snapshot.zero_copy_eligible == 1U && snapshot.zero_copy_hits == 1U &&
          snapshot.copy_fallback_bytes == 128U,
      "zero-copy accounting drifted");
  expect(metrics.canonical_text().find("boundary_us=25\n") != std::string::npos, "metrics not canonical");

  delta::runtime::benchmark::TraceExporter traces;
  traces.append({1U, "ACT-COMMIT", "sha256:state", "sha256:effect", "APPLIED"});
  traces.append({2U, "ACT-APPLY-FINALIZE", "sha256:next", "sha256:apply", "APPLIED"});
  expect(traces.entries().size() == 2U, "trace count drifted");
  expect(traces.canonical_text().starts_with("1|ACT-COMMIT|"), "trace encoding drifted");
}

void test_fault_order_and_sidecar_replay() {
  using delta::runtime::benchmark::FaultAction;
  using delta::runtime::benchmark::FaultController;
  using delta::runtime::benchmark::FaultEvent;
  FaultController controller(std::vector<FaultEvent>{
      {"restart", "VALIDATOR", FaultAction::restart, 3U, true, "RECOVERED"},
      {"worker-loss", "WORKER", FaultAction::crash, 2U, true, "APPLIED"},
  });
  expect(controller.events().front().event_id == "worker-loss", "fault events not sorted");
  expect(controller.events_at(3U).size() == 1U, "fault event lookup failed");

  delta::runtime::benchmark::SidecarServer sidecar(4U, 16U);
  const std::array payload{std::byte{1}, std::byte{2}, std::byte{3}};
  const auto first = sidecar.execute("request-1", payload);
  sidecar.crash();
  expect(!sidecar.accepting(), "sidecar crash did not isolate process");
  sidecar.restart();
  const auto replay = sidecar.execute("request-1", payload);
  expect(replay.replay && replay.response == first.response, "sidecar replay was not exact");
  expect(replay.request_sequence == first.request_sequence, "sidecar replay sequence changed");
  const std::array conflicting{std::byte{9}};
  try {
    static_cast<void>(sidecar.execute("request-1", conflicting));
    fail("sidecar accepted conflicting replay");
  } catch (const delta::runtime::benchmark::BenchmarkError&) {
  }
}

void test_faults_are_observed_from_actual_runtime_state() {
  using delta::runtime::benchmark::FaultAction;
  using delta::runtime::benchmark::FaultEvent;
  using delta::runtime::benchmark::execute_fault_scenario;
  const std::vector<FaultEvent> events{
      {"worker-loss", "WORKER", FaultAction::crash, 100U, true, "APPLIED"},
      {"validator-crash", "VALIDATOR", FaultAction::crash, 120U, true, "VIEW_CHANGE"},
      {"validator-restart", "VALIDATOR", FaultAction::restart, 140U, true, "RECOVERED"},
      {"storage-crash", "STORAGE", FaultAction::crash, 160U, true, "RETRIEVAL"},
      {"storage-restart", "STORAGE", FaultAction::restart, 180U, true, "RECOVERED"},
      {"regional-delay", "REGION", FaultAction::delay, 200U, true, "APPLIED"},
      {"regional-partition", "REGION", FaultAction::partition, 240U, true, "ABORTED"},
  };
  auto root = std::filesystem::temp_directory_path() / "delta-stagec-actual-fault-test";
  std::error_code error;
  std::filesystem::remove_all(root, error);
  expect(!error, "cannot clean actual fault test root");
  for (const auto& event : events) {
    const auto result = execute_fault_scenario(event, root / event.event_id, event.event_id);
    expect(result.observed_outcome == event.expected_outcome, "actual fault outcome drifted");
    expect(result.runtime_operation_count > 0U, "actual runtime operation is absent");
    expect(!result.canonical_trace.empty(), "actual native trace is absent");
    if (event.action == FaultAction::restart) {
      expect(result.wal_replayed, "restart did not prove WAL replay");
    }
    if (event.actor_class == "VALIDATOR" && event.action == FaultAction::crash) {
      expect(result.view_change_observed, "validator crash did not prove view change");
    }
    if (event.actor_class == "REGION" && event.action == FaultAction::partition) {
      expect(!result.current_checkpoint_advanced, "partition advanced current checkpoint");
    }
    if (event.actor_class == "STORAGE" && event.action == FaultAction::crash) {
      expect(!result.availability_success, "storage crash fabricated availability");
    }
  }
}

}  // namespace

int main() {
  try {
    test_metrics_and_trace();
    test_fault_order_and_sidecar_replay();
    test_faults_are_observed_from_actual_runtime_state();
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
  return 0;
}
