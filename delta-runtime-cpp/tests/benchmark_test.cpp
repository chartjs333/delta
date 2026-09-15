#include <delta/runtime/benchmark.hpp>
#include <delta/shards/envelope.hpp>

#include <array>
#include <cstddef>
#include <filesystem>
#include <fstream>
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
          event.event_id == "worker-loss-concentrated"
              ? index >= 2U
              : index != lost,
      });
    }
  };
  std::string profile = "lan-control";
  if (event.actor_class == "WORKER") {
    if (event.event_id == "mnist-4-workers") {
      tickets(4U, 4U);
      quorum("aggregate", "AGGREGATE_VOTE", event.logical_step + 20U);
      quorum("apply", "APPLY_VOTE", event.logical_step + 30U);
    } else if (event.event_id == "worker-loss-concentrated") {
      tickets(10U, 9U);
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
      tickets(10U, 9U);
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
      {"restart", "VALIDATOR", FaultAction::restart, 3U, true, {}},
      {"worker-loss", "WORKER", FaultAction::crash, 2U, true, {}},
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
      {"worker-loss-10pct", "WORKER", FaultAction::crash, 100U, true, {}},
      {"worker-loss-concentrated", "WORKER", FaultAction::crash, 110U, true, {}},
      {"validator-crash", "VALIDATOR", FaultAction::crash, 120U, true, {}},
      {"validator-restart", "VALIDATOR", FaultAction::restart, 140U, true, {}},
      {"storage-crash", "STORAGE", FaultAction::crash, 160U, true, {}},
      {"storage-restart", "STORAGE", FaultAction::restart, 180U, true, {}},
      {"regional-delay", "REGION", FaultAction::delay, 200U, true, {}},
      {"regional-partition", "REGION", FaultAction::partition, 240U, true, {}},
  };
  const std::array<std::string_view, 8U> expected_outcomes{
      "APPLIED", "ABORTED", "VIEW_CHANGE", "RECOVERED",
      "RETRIEVAL", "RECOVERED", "APPLIED", "ABORTED"};
  for (auto& event : events) event.causal_schedule = causal_schedule(event);
  auto root = std::filesystem::temp_directory_path() / "delta-stagec-actual-fault-test";
  std::error_code error;
  std::filesystem::remove_all(root, error);
  expect(!error, "cannot clean actual fault test root");
  for (std::size_t index = 0U; index < events.size(); ++index) {
    const auto& event = events[index];
    const auto result = execute_fault_scenario(event, root / event.event_id, event.event_id);
    expect(result.observed_outcome == expected_outcomes[index], "actual fault outcome drifted");
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
    if (event.event_id == "worker-loss-concentrated") {
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

void test_real_drq1_ingress_into_feature008() {
  using delta::runtime::benchmark::FaultAction;
  using delta::runtime::benchmark::FaultEvent;
  using delta::runtime::benchmark::execute_fault_scenario;

  FaultEvent event{"worker-loss-10pct", "WORKER", FaultAction::crash, 100U, true, {}};
  event.causal_schedule = causal_schedule(event);

  auto plan_root = std::filesystem::temp_directory_path() / "delta-real-drq1-stagec-test";
  std::error_code error;
  std::filesystem::remove_all(plan_root, error);
  std::filesystem::create_directories(plan_root / "shards");

  // 1. Write shards manifest.json
  const std::string manifest_json = R"({
  "formal_semantics_id": "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6",
  "parameter_schema_id": "sha256:f43c0259749b15ae0d0154a6e9094774c7ea65e55adefbaea400a6201acb6239",
  "profile_id": "sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61",
  "proof_instance_id": "sha256:993b4d5104810dd26a3159b60cf8fe9afe6154cdcca90d22b577ae1b6d1ac076",
  "round_config_id": "sha256:34bc08c316dfe22efe155ed11b866bcc0daf7ef8c3c7389c56b2f2c707443629",
  "scale_table_id": "sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205",
  "shard_plan_id": "sha256:4c644a3254edb3d7bff009bbe91ee99df6051516362fa1a1eac6f0a803a9c7a1",
  "element_count": 4,
  "element_start": 0,
  "ordinal": 0,
  "segment_id": "mnist.classifier",
  "segment_offset": 0
})";
  {
    std::ofstream manifest_out(plan_root / "shards" / "manifest.json");
    manifest_out << manifest_json;
  }

  // 2. Write real DRQ1 shards for all delivered tickets (0..8)
  for (std::size_t index = 0U; index < 9U; ++index) {
    const auto ticket_id = "ticket-" + padded(index);
    delta::shards::ShardHeader header{
        .ordinal = 0U,
        .segment_id = "mnist.classifier",
        .segment_offset = 0U,
        .element_start = 0U,
        .element_count = 4U,
        .formal_semantics_id = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6",
        .parameter_schema_id = "sha256:f43c0259749b15ae0d0154a6e9094774c7ea65e55adefbaea400a6201acb6239",
        .profile_id = "sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61",
        .proof_instance_id = "sha256:993b4d5104810dd26a3159b60cf8fe9afe6154cdcca90d22b577ae1b6d1ac076",
        .round_config_id = "sha256:34bc08c316dfe22efe155ed11b866bcc0daf7ef8c3c7389c56b2f2c707443629",
        .scale_table_id = "sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205",
        .shard_plan_id = "sha256:4c644a3254edb3d7bff009bbe91ee99df6051516362fa1a1eac6f0a803a9c7a1",
        .ticket_id = ticket_id,
        .payload_sha256 = "",
    };
    const std::vector<std::int16_t> q_values{
        static_cast<std::int16_t>(10 * (index + 1)),
        static_cast<std::int16_t>(-20 * (index + 1)),
        static_cast<std::int16_t>(30 * (index + 1)),
        static_cast<std::int16_t>(-40 * (index + 1)),
    };
    const auto encoded = delta::shards::write_shard(header, q_values);
    std::ofstream shard_out(plan_root / "shards" / (ticket_id + ".drq1"), std::ios::binary);
    shard_out.write(reinterpret_cast<const char*>(encoded.envelope.data()), encoded.envelope.size());
  }

  // 3. Execute scenario through Stage C pipeline
  const auto result = execute_fault_scenario(
      event, plan_root / "runtime-drq1-test", "drq1-test");

  expect(result.observed_outcome == "APPLIED", "REAL_DRQ1 mode did not reach APPLIED");
  expect(result.current_checkpoint_advanced, "REAL_DRQ1 mode did not advance checkpoint");
  expect(result.runtime_operation_count > 0U, "REAL_DRQ1 mode lacked runtime operations");
  expect(!result.canonical_trace.empty(), "REAL_DRQ1 mode trace is empty");
  expect(result.canonical_trace.find("ACT-APPLY-VOTE") != std::string::npos, "trace lacks apply vote");

  // 4. Verify fail-closed behavior: remove a shard to prove NO synthetic fallback
  std::filesystem::remove(plan_root / "shards" / "ticket-000.drq1");
  try {
    static_cast<void>(execute_fault_scenario(
        event, plan_root / "runtime-drq1-fail", "drq1-fail"));
    fail("REAL_DRQ1 mode accepted execution with missing shard without failing closed");
  } catch (const delta::runtime::benchmark::BenchmarkError& exc) {
    expect(std::string_view(exc.what()).find("REAL_DRQ1") != std::string::npos, "error is not REAL_DRQ1 fail-closed");
  }

  std::filesystem::remove_all(plan_root, error);
}

void test_mnist_4_workers_e2e_into_feature008() {
  using delta::runtime::benchmark::FaultAction;
  using delta::runtime::benchmark::FaultEvent;
  using delta::runtime::benchmark::execute_fault_scenario;

  FaultEvent event{"mnist-4-workers", "WORKER", FaultAction::crash, 100U, true, {}};
  event.causal_schedule = causal_schedule(event);

  auto plan_root = std::filesystem::temp_directory_path() / "delta-mnist-4w-stagec-test";
  std::error_code error;
  std::filesystem::remove_all(plan_root, error);
  std::filesystem::create_directories(plan_root / "shards");

  const std::string manifest_json = R"({
  "formal_semantics_id": "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6",
  "parameter_schema_id": "sha256:f43c0259749b15ae0d0154a6e9094774c7ea65e55adefbaea400a6201acb6239",
  "profile_id": "sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61",
  "proof_instance_id": "sha256:993b4d5104810dd26a3159b60cf8fe9afe6154cdcca90d22b577ae1b6d1ac076",
  "round_config_id": "sha256:34bc08c316dfe22efe155ed11b866bcc0daf7ef8c3c7389c56b2f2c707443629",
  "scale_table_id": "sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205",
  "shard_plan_id": "sha256:4c644a3254edb3d7bff009bbe91ee99df6051516362fa1a1eac6f0a803a9c7a1",
  "element_count": 7850,
  "element_start": 0,
  "ordinal": 0,
  "segment_id": "mnist.linear",
  "segment_offset": 0
})";
  {
    std::ofstream manifest_out(plan_root / "shards" / "manifest.json");
    manifest_out << manifest_json;
  }

  for (std::size_t index = 0U; index < 4U; ++index) {
    const auto ticket_id = "ticket-" + padded(index);
    delta::shards::ShardHeader header{
        .ordinal = 0U,
        .segment_id = "mnist.linear",
        .segment_offset = 0U,
        .element_start = 0U,
        .element_count = 7850U,
        .formal_semantics_id = "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6",
        .parameter_schema_id = "sha256:f43c0259749b15ae0d0154a6e9094774c7ea65e55adefbaea400a6201acb6239",
        .profile_id = "sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61",
        .proof_instance_id = "sha256:993b4d5104810dd26a3159b60cf8fe9afe6154cdcca90d22b577ae1b6d1ac076",
        .round_config_id = "sha256:34bc08c316dfe22efe155ed11b866bcc0daf7ef8c3c7389c56b2f2c707443629",
        .scale_table_id = "sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205",
        .shard_plan_id = "sha256:4c644a3254edb3d7bff009bbe91ee99df6051516362fa1a1eac6f0a803a9c7a1",
        .ticket_id = ticket_id,
        .payload_sha256 = "",
    };
    std::vector<std::int16_t> q_values(7850U, static_cast<std::int16_t>(0));
    for (std::size_t c = 0U; c < 784U; ++c) {
      q_values[index * 784U + c] = static_cast<std::int16_t>(100 + index * 10);
    }
    q_values[7840U + index] = static_cast<std::int16_t>(1);

    const auto encoded = delta::shards::write_shard(header, q_values);
    std::ofstream shard_out(plan_root / "shards" / (ticket_id + ".drq1"), std::ios::binary);
    shard_out.write(reinterpret_cast<const char*>(encoded.envelope.data()), encoded.envelope.size());
  }

  const auto result = execute_fault_scenario(
      event, plan_root / "runtime-mnist-4w", "mnist-4w");

  expect(result.observed_outcome == "APPLIED", "MNIST 4-workers did not reach APPLIED");
  expect(result.current_checkpoint_advanced, "MNIST 4-workers did not advance checkpoint");
  expect(!result.canonical_trace.empty(), "MNIST 4-workers trace is empty");
  expect(result.canonical_trace.find("ACT-APPLY-VOTE") != std::string::npos, "trace lacks apply vote");

  const auto current_store = plan_root / "runtime-mnist-4w" / "current";
  expect(std::filesystem::exists(current_store), "current pointer store missing");

  // 4. Verify fail-closed behavior: corrupt one shard to prove strict validation
  {
    std::ofstream corrupt_out(plan_root / "shards" / "ticket-002.drq1", std::ios::binary);
    corrupt_out.write("CORRUPT_BYTES", 13);
  }
  try {
    static_cast<void>(execute_fault_scenario(
        event, plan_root / "runtime-mnist-fail", "mnist-fail"));
    fail("REAL_DRQ1 mode accepted corrupt shard without failing closed");
  } catch (const delta::runtime::benchmark::BenchmarkError& exc) {
    expect(std::string_view(exc.what()).find("REAL_DRQ1") != std::string::npos, "error is not REAL_DRQ1 fail-closed");
  }

  std::filesystem::remove_all(plan_root, error);
}

}  // namespace

int main() {
  try {
    test_metrics_and_trace();
    test_fault_order_and_sidecar_replay();
    test_faults_are_observed_from_actual_runtime_state();
    test_real_drq1_ingress_into_feature008();
    test_mnist_4_workers_e2e_into_feature008();
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
  return 0;
}
