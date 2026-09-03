#include <delta/runtime/benchmark.hpp>

#include <array>
#include <cstddef>
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace {

[[noreturn]] void fail(const char* message) { throw std::runtime_error(message); }

void expect(bool condition, const char* message) {
  if (!condition) fail(message);
}

[[nodiscard]] std::string padded(std::size_t value) {
  auto digits = std::to_string(value);
  return std::string(3U - digits.size(), '0') + digits;
}

[[nodiscard]] std::string causal_schedule(
    const delta::runtime::benchmark::FaultEvent& event,
    bool omit_apply_vote = false) {
  struct Message {
    std::string id;
    std::string actor;
    std::string domain;
    std::string ticket;
    std::string kind;
    std::uint64_t tick;
    bool delivered;
  };
  std::vector<Message> messages;
  const auto quorum = [&](std::string_view prefix, std::string_view kind, std::uint64_t tick) {
    for (std::size_t index = 0U; index < 3U; ++index) {
      messages.push_back(Message{
          std::string(prefix) + "-" + std::to_string(index),
          "validator-" + std::to_string(index),
          "NONE",
          "NONE",
          std::string(kind),
          tick + index,
          !(omit_apply_vote && kind == "APPLY_VOTE" && index == 2U),
      });
    }
  };
  const auto tickets = [&](std::size_t count, std::size_t lost) {
    for (std::size_t index = 0U; index < count; ++index) {
      const auto ordinal = padded(index);
      messages.push_back(Message{
          "worker-ticket-" + ordinal,
          "worker-" + ordinal,
          index < count / 2U ? "code" : "text",
          "ticket-" + ordinal,
          "WORK_TICKET",
          event.logical_step + index,
          event.actor_class == "WORKER" && event.expected_outcome == "ABORTED"
              ? index >= 2U
              : index != lost,
      });
    }
  };
  std::string profile = "lan-control";
  if (event.actor_class == "WORKER") {
    tickets(10U, 9U);
    if (event.expected_outcome == "ABORTED") {
      for (std::size_t index = 0U; index < 3U; ++index) {
        messages.push_back(Message{
            "abort-" + std::to_string(index),
            "validator-" + std::to_string(index),
            "NONE",
            "NONE",
            "ABORT_VOTE",
            event.logical_step + 60U,
            true,
        });
      }
    } else {
      quorum("aggregate", "AGGREGATE_VOTE", event.logical_step + 20U);
      quorum("apply", "APPLY_VOTE", event.logical_step + 30U);
    }
  } else if (event.actor_class == "REGION" &&
             event.action == delta::runtime::benchmark::FaultAction::delay) {
    profile = "wan-regional";
    tickets(4U, 4U);
    quorum("aggregate", "AGGREGATE_VOTE", event.logical_step + 20U);
    quorum("apply", "APPLY_VOTE", event.logical_step + 30U);
  } else if (event.actor_class == "REGION") {
    profile = "wan-intercontinental";
    tickets(4U, 4U);
    for (std::size_t index = 0U; index < 4U; ++index) {
      messages.push_back(Message{
          "partition-aggregate-" + std::to_string(index),
          "validator-" + std::to_string(index),
          "NONE",
          "NONE",
          "AGGREGATE_VOTE",
          event.logical_step + 10U + index,
          index < 2U,
      });
    }
    for (std::size_t index = 0U; index < 3U; ++index) {
      messages.push_back(Message{
          "abort-" + std::to_string(index),
          "validator-" + std::to_string(index),
          "NONE",
          "NONE",
          "ABORT_VOTE",
          event.logical_step + 60U,
          true,
      });
    }
  } else if (event.actor_class == "VALIDATOR" &&
             event.action == delta::runtime::benchmark::FaultAction::crash) {
    quorum("view-change", "VIEW_CHANGE_VOTE", event.logical_step + 1U);
  } else if (event.actor_class == "VALIDATOR") {
    messages.push_back(
        Message{"recovery", "validator-0", "NONE", "NONE", "RECOVERY_SIGNAL",
                event.logical_step, true});
  } else if (event.actor_class == "STORAGE") {
    messages.push_back(Message{
        "storage",
        "storage-0",
        "NONE",
        "NONE",
        "STORAGE_SIGNAL",
        event.logical_step,
        event.action == delta::runtime::benchmark::FaultAction::restart,
    });
  }
  std::string result = "schema_version=1.0.0\nevent_id=" + event.event_id +
                       "\nnetwork_profile_id=" + profile + "\ngst_tick=" +
                       std::to_string(event.logical_step) + "\nhard_deadline_tick=" +
                       std::to_string(event.logical_step + 60U) + "\nmessage_count=" +
                       std::to_string(messages.size()) + "\n";
  for (std::size_t index = 0U; index < messages.size(); ++index) {
    const auto& message = messages[index];
    result += "message." + std::to_string(index) + "=" + message.id + "," + message.actor +
              "," + message.domain + "," + message.ticket + "," + message.kind + "," +
              std::to_string(message.tick) + "," +
              std::to_string(message.delivered ? message.tick : 0U) + "," +
              (message.delivered ? "1\n" : "0\n");
  }
  return result;
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
  std::vector<FaultEvent> events{
      {"worker-loss", "WORKER", FaultAction::crash, 100U, true, "APPLIED"},
      {"worker-domain-loss", "WORKER", FaultAction::crash, 110U, true, "ABORTED"},
      {"validator-crash", "VALIDATOR", FaultAction::crash, 120U, true, "VIEW_CHANGE"},
      {"validator-restart", "VALIDATOR", FaultAction::restart, 140U, true, "RECOVERED"},
      {"storage-crash", "STORAGE", FaultAction::crash, 160U, true, "RETRIEVAL"},
      {"storage-restart", "STORAGE", FaultAction::restart, 180U, true, "RECOVERED"},
      {"regional-delay", "REGION", FaultAction::delay, 200U, true, "APPLIED"},
      {"regional-partition", "REGION", FaultAction::partition, 240U, true, "ABORTED"},
  };
  for (auto& event : events) event.causal_schedule = causal_schedule(event);
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
      expect(
          result.canonical_causal_evidence.find("certified_abort_tick=300\n") !=
              std::string::npos,
          "partition abort did not wait for exact hard deadline");
    }
    if (event.actor_class == "STORAGE" && event.action == FaultAction::crash) {
      expect(!result.availability_success, "storage crash fabricated availability");
    }
    if (result.observed_outcome == "APPLIED") {
      expect(result.current_checkpoint_advanced, "APPLIED lacks current-pointer advance");
      expect(
          result.canonical_causal_evidence.find("apply_qc_id=sha256:") != std::string::npos &&
              result.canonical_causal_evidence.find("aggregate_root_qc_id=sha256:") !=
                  std::string::npos,
          "APPLIED lacks AggregateRootQC or ApplyQC evidence");
    }
    if (event.event_id == "worker-domain-loss") {
      expect(!result.current_checkpoint_advanced, "mandatory-domain abort advanced current");
      expect(
          result.canonical_causal_evidence.find(
              "missing_work_policy_result=MANDATORY_DOMAIN_CAPACITY_UNSATISFIED_ABORT\n") !=
              std::string::npos &&
              result.canonical_causal_evidence.find("per_domain_remaining_tickets=code:3,text:5\n") !=
                  std::string::npos,
          "concentrated worker loss lacks causal capacity evidence");
    }
  }

  auto missing_apply = events.front();
  missing_apply.causal_schedule = causal_schedule(missing_apply, true);
  try {
    static_cast<void>(execute_fault_scenario(
        missing_apply, root / "missing-apply-quorum", "missing-apply-quorum"));
    fail("APPLIED without exact ApplyQC quorum was accepted");
  } catch (const delta::runtime::benchmark::BenchmarkError&) {
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
