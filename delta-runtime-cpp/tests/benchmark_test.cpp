#include <delta/runtime/benchmark.hpp>

#include <array>
#include <cstddef>
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

}  // namespace

int main() {
  try {
    test_metrics_and_trace();
    test_fault_order_and_sidecar_replay();
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
  return 0;
}
