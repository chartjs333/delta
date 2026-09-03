#include <delta/core/canonical.hpp>
#include <delta/core/protocol.hpp>
#include <delta/core/transition.hpp>
#include <delta/runtime/benchmark.hpp>
#include <delta/runtime/runtime.hpp>

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace delta::runtime::benchmark {
namespace {

namespace canonical = core::canonical;
namespace protocol = core::protocol;

[[nodiscard]] canonical::Bytes ascii_bytes(std::string_view value) {
  canonical::Bytes result;
  result.reserve(value.size());
  for (const unsigned char character : value) {
    result.push_back(static_cast<std::byte>(character));
  }
  return result;
}

[[nodiscard]] std::string derived_id(std::string_view domain, std::string_view value) {
  auto input = ascii_bytes(domain);
  const auto suffix = ascii_bytes(value);
  input.insert(input.end(), suffix.begin(), suffix.end());
  return "sha256:" + canonical::sha256_hex(input);
}

[[nodiscard]] std::string raw_id(std::span<const std::byte> value) {
  return "sha256:" + canonical::sha256_hex(value);
}

[[nodiscard]] std::string state_id(std::span<const std::byte> value) {
  return canonical::content_id(canonical::Type::round_state, value);
}

[[nodiscard]] canonical::Bytes read_bytes(const std::filesystem::path& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) {
    throw BenchmarkError("actual runtime WAL is absent");
  }
  const std::string value{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  if (input.bad()) {
    throw BenchmarkError("actual runtime WAL cannot be read");
  }
  return ascii_bytes(value);
}

[[nodiscard]] protocol::RoundState initial_state(const FaultEvent& event) {
  return protocol::RoundState{
      .available_ticket_count = 0U,
      .committed_ticket_count = 0U,
      .config_id = derived_id("stagec-config:", event.event_id),
      .durable_sequence = 0U,
      .height = 1U,
      .parent_checkpoint_id = derived_id("stagec-parent:", event.event_id),
      .phase = protocol::RoundPhase::ticketing_open,
      .round_id = "stagec-" + event.event_id,
      .state_root = derived_id("stagec-current:", event.event_id),
      .ticket_count = 4U,
      .view = 0U,
  };
}

[[nodiscard]] Config config(
    const std::filesystem::path& directory,
    const canonical::Bytes& initial) {
  return Config{directory, initial, 64U};
}

[[nodiscard]] protocol::Command command(
    const protocol::RoundState& state,
    std::string kind,
    std::string request_id,
    std::string body,
    std::optional<std::uint64_t> view = std::nullopt) {
  return protocol::Command{
      .actor_id = "validator-1",
      .body_hash = std::move(body),
      .command_kind = std::move(kind),
      .height = state.height,
      .logical_tick = 10U,
      .request_id = std::move(request_id),
      .round_id = state.round_id,
      .view = view.value_or(state.view),
  };
}

[[nodiscard]] protocol::Vote vote(
    const protocol::RoundState& state,
    std::string_view event_id,
    std::uint64_t validator,
    std::string_view kind,
    std::string_view context,
    std::string_view body) {
  const auto validator_id = "validator-" + std::to_string(validator);
  return protocol::Vote{
      .body_hash = std::string(body),
      .context_id = std::string(context),
      .durable_sequence = validator,
      .height = state.height,
      .kind = std::string(kind),
      .round_id = state.round_id,
      .signature_id = derived_id("stagec-signature:", std::string(event_id) + validator_id),
      .validator_epoch_id = derived_id("stagec-validator-epoch:", event_id),
      .validator_id = validator_id,
      .view = state.view,
  };
}

void append_transition(
    TraceExporter& trace,
    std::string action,
    const SubmitReceipt& receipt,
    std::string outcome) {
  trace.append(TraceEntry{
      .sequence = trace.entries().size() + 1U,
      .action_id = std::move(action),
      .state_id = receipt.next_state_id,
      .effect_id = receipt.effect_batch_id,
      .terminal_outcome = std::move(outcome),
  });
}

void append_vote(
    TraceExporter& trace,
    std::string action,
    std::string state_root,
    const VoteReceipt& receipt,
    std::string outcome) {
  trace.append(TraceEntry{
      .sequence = trace.entries().size() + 1U,
      .action_id = std::move(action),
      .state_id = std::move(state_root),
      .effect_id = receipt.vote_id,
      .terminal_outcome = std::move(outcome),
  });
}

[[nodiscard]] SubmitReceipt submit(
    Runtime& runtime,
    TraceExporter& trace,
    std::string action,
    std::string request_prefix,
    std::string command_kind) {
  const auto state = protocol::parse_round_state(runtime.state_bytes());
  const auto body = derived_id("stagec-body:", request_prefix + command_kind);
  auto receipt = runtime.submit(protocol::encode(command(
      state,
      std::move(command_kind),
      std::move(request_prefix),
      std::move(body))));
  append_transition(trace, std::move(action), receipt, "ACCEPTED");
  return receipt;
}

struct ScenarioObservation {
  std::string outcome;
  canonical::Bytes state_bytes;
  std::string effect_root;
  TraceExporter trace;
  std::uint64_t operation_count{};
  bool wal_replayed{};
  bool view_change_observed{};
  bool current_checkpoint_advanced{};
  bool availability_success{};
};

[[nodiscard]] ScenarioObservation execute_progress(
    const FaultEvent& event,
    const std::filesystem::path& directory,
    std::string_view request_id) {
  const auto initial = protocol::encode(initial_state(event));
  Runtime runtime(config(directory, initial));
  TraceExporter trace;
  static_cast<void>(submit(
      runtime, trace, "ACT-COMMIT", std::string(request_id) + "-commit", "ACCEPT_COMMITMENT"));
  static_cast<void>(submit(
      runtime,
      trace,
      "ACT-AVAIL-ATTEST",
      std::string(request_id) + "-availability",
      "ACCEPT_AVAILABILITY"));
  static_cast<void>(submit(
      runtime,
      trace,
      "ACT-ISC-FINALIZE",
      std::string(request_id) + "-freeze",
      "FINALIZE_INPUT_FREEZE"));
  const auto final = submit(
      runtime,
      trace,
      "ACT-AGGREGATE-FINALIZE",
      std::string(request_id) + "-aggregate",
      "FINALIZE_AGGREGATE");
  const auto state = protocol::parse_round_state(runtime.state_bytes());
  if (state.phase != protocol::RoundPhase::aggregated || runtime.journal_sequence() < 4U) {
    throw BenchmarkError("actual progress transition did not reach AGGREGATED");
  }
  return ScenarioObservation{
      .outcome = "APPLIED",
      .state_bytes = runtime.state_bytes(),
      .effect_root = final.effect_batch_id,
      .trace = std::move(trace),
      .operation_count = 4U,
      .availability_success = true,
  };
}

[[nodiscard]] ScenarioObservation execute_validator_crash(
    const FaultEvent& event,
    const std::filesystem::path& directory,
    std::string_view request_id) {
  const auto initial = protocol::encode(initial_state(event));
  Runtime runtime(config(directory, initial));
  TraceExporter trace;
  const auto state = protocol::parse_round_state(initial);
  const auto body = derived_id("stagec-view-change-body:", event.event_id);
  const auto context = "VIEW-CHANGE:" + state.round_id + ":1";
  for (std::uint64_t validator = 1U; validator <= 3U; ++validator) {
    const auto receipt = runtime.record_vote(
        protocol::encode(vote(state, event.event_id, validator, "VIEW_CHANGE", context, body)));
    append_vote(trace, "ACT-VIEW-VOTE", state_id(runtime.state_bytes()), receipt, "ACCEPTED");
  }
  const auto changed = runtime.submit(protocol::encode(command(
      state,
      "ADVANCE_VIEW",
      std::string(request_id) + "-view-change",
      body,
      1U)));
  append_transition(trace, "ACT-VIEW-FINALIZE", changed, "FINALIZED");
  const auto terminal = protocol::parse_round_state(runtime.state_bytes());
  const bool observed = terminal.view == 1U && runtime.recovered_vote_count() == 3U;
  if (!observed) {
    throw BenchmarkError("validator crash lacks actual view-change evidence");
  }
  return ScenarioObservation{
      .outcome = "VIEW_CHANGE",
      .state_bytes = runtime.state_bytes(),
      .effect_root = changed.effect_batch_id,
      .trace = std::move(trace),
      .operation_count = 4U,
      .view_change_observed = true,
  };
}

[[nodiscard]] ScenarioObservation execute_validator_restart(
    const FaultEvent& event,
    const std::filesystem::path& directory) {
  const auto initial = protocol::encode(initial_state(event));
  const auto state = protocol::parse_round_state(initial);
  const auto body = derived_id("stagec-recovery-vote-body:", event.event_id);
  const auto context = "ROUND_CONFIG:" + state.round_id + ":1:0";
  const auto frame = protocol::encode(vote(state, event.event_id, 1U, "ROUND_CONFIG", context, body));
  if (!std::filesystem::exists(directory / "runtime.wal")) {
    Runtime crashed(config(directory, initial));
    try {
      static_cast<void>(crashed.record_vote(frame, CrashPoint::after_durability_before_commit));
      throw BenchmarkError("validator restart fault injection did not crash runtime");
    } catch (const RuntimeError& error) {
      if (error.code() != ErrorCode::simulated_crash) {
        throw;
      }
    }
  }
  Runtime recovered(config(directory, initial));
  if (recovered.recovered_vote_count() != 1U) {
    throw BenchmarkError("validator restart did not recover durable vote journal");
  }
  const auto replay = recovered.record_vote(frame);
  if (!replay.replay || replay.journal_sequence != 1U) {
    throw BenchmarkError("validator restart accepted vote without exact WAL replay");
  }
  TraceExporter trace;
  const auto root = state_id(recovered.state_bytes());
  append_vote(trace, "ACT-CRASH-AFTER-DURABILITY", root, replay, "FAULT");
  append_vote(trace, "ACT-JOURNAL-RECOVER", root, replay, "RECOVERED");
  append_vote(trace, "ACT-MESSAGE-REPLAY", root, replay, "NO_OP");
  return ScenarioObservation{
      .outcome = "RECOVERED",
      .state_bytes = recovered.state_bytes(),
      .effect_root = replay.vote_id,
      .trace = std::move(trace),
      .operation_count = 3U,
      .wal_replayed = true,
  };
}

[[nodiscard]] ScenarioObservation execute_storage_crash(
    const FaultEvent& event,
    const std::filesystem::path& directory,
    std::string_view request_id) {
  const auto initial = protocol::encode(initial_state(event));
  Runtime runtime(config(directory, initial));
  TraceExporter trace;
  const auto committed = submit(
      runtime, trace, "ACT-COMMIT", std::string(request_id) + "-commit", "ACCEPT_COMMITMENT");
  const auto state = protocol::parse_round_state(runtime.state_bytes());
  bool rejected_without_availability = false;
  try {
    const auto body = derived_id("stagec-body:", event.event_id + std::string("freeze"));
    static_cast<void>(runtime.submit(protocol::encode(command(
        state,
        "FINALIZE_INPUT_FREEZE",
        std::string(request_id) + "-forbidden-freeze",
        body))));
  } catch (const core::transition::TransitionError&) {
    rejected_without_availability = true;
  }
  const auto terminal = protocol::parse_round_state(runtime.state_bytes());
  if (!rejected_without_availability || terminal.available_ticket_count != 0U ||
      terminal.phase != protocol::RoundPhase::committed) {
    throw BenchmarkError("storage crash fabricated availability success");
  }
  return ScenarioObservation{
      .outcome = "RETRIEVAL",
      .state_bytes = runtime.state_bytes(),
      .effect_root = committed.effect_batch_id,
      .trace = std::move(trace),
      .operation_count = 2U,
      .availability_success = false,
  };
}

[[nodiscard]] ScenarioObservation execute_storage_restart(
    const FaultEvent& event,
    const std::filesystem::path& directory,
    std::string_view request_id) {
  const auto initial = protocol::encode(initial_state(event));
  TraceExporter trace;
  {
    Runtime before_restart(config(directory, initial));
    const auto committed = submit(
        before_restart,
        trace,
        "ACT-COMMIT",
        std::string(request_id) + "-commit",
        "ACCEPT_COMMITMENT");
    static_cast<void>(committed);
  }
  Runtime recovered(config(directory, initial));
  const auto recovered_state = protocol::parse_round_state(recovered.state_bytes());
  if (recovered.journal_sequence() < 1U ||
      recovered_state.phase != protocol::RoundPhase::committed) {
    throw BenchmarkError("storage restart did not recover committed state from WAL");
  }
  const auto available = submit(
      recovered,
      trace,
      "ACT-ARTIFACT-REPAIR",
      std::string(request_id) + "-availability",
      "ACCEPT_AVAILABILITY");
  const auto terminal = protocol::parse_round_state(recovered.state_bytes());
  if (terminal.phase != protocol::RoundPhase::available ||
      terminal.available_ticket_count != 1U) {
    throw BenchmarkError("storage restart did not restore exact artifact availability");
  }
  return ScenarioObservation{
      .outcome = "RECOVERED",
      .state_bytes = recovered.state_bytes(),
      .effect_root = available.effect_batch_id,
      .trace = std::move(trace),
      .operation_count = 2U,
      .wal_replayed = true,
      .availability_success = true,
  };
}

[[nodiscard]] ScenarioObservation execute_partition(
    const FaultEvent& event,
    const std::filesystem::path& directory,
    std::string_view request_id) {
  const auto initial = protocol::encode(initial_state(event));
  const auto before = protocol::parse_round_state(initial);
  Runtime runtime(config(directory, initial));
  TraceExporter trace;
  const auto aborted = submit(
      runtime,
      trace,
      "ACT-ABORT-FINALIZE",
      std::string(request_id) + "-abort",
      "CERTIFY_ABORT");
  const auto terminal = protocol::parse_round_state(runtime.state_bytes());
  const bool current_advanced = terminal.parent_checkpoint_id != before.parent_checkpoint_id ||
                                terminal.state_root != before.state_root;
  if (terminal.phase != protocol::RoundPhase::aborted || current_advanced) {
    throw BenchmarkError("partition advanced current checkpoint");
  }
  return ScenarioObservation{
      .outcome = "ABORTED",
      .state_bytes = runtime.state_bytes(),
      .effect_root = aborted.effect_batch_id,
      .trace = std::move(trace),
      .operation_count = 1U,
      .current_checkpoint_advanced = current_advanced,
  };
}

[[nodiscard]] ScenarioObservation observe(
    const FaultEvent& event,
    const std::filesystem::path& directory,
    std::string_view request_id) {
  if (!event.assumptions_hold) {
    const auto initial = protocol::encode(initial_state(event));
    return ScenarioObservation{
        .outcome = "SAFE_BLOCKED",
        .state_bytes = initial,
        .effect_root = raw_id(ascii_bytes("NO_EXTERNALLY_SENDABLE_EFFECT")),
    };
  }
  if ((event.actor_class == "WORKER" && event.action == FaultAction::crash) ||
      (event.actor_class == "REGION" && event.action == FaultAction::delay)) {
    return execute_progress(event, directory, request_id);
  }
  if (event.actor_class == "VALIDATOR" && event.action == FaultAction::crash) {
    return execute_validator_crash(event, directory, request_id);
  }
  if (event.actor_class == "VALIDATOR" && event.action == FaultAction::restart) {
    return execute_validator_restart(event, directory);
  }
  if (event.actor_class == "STORAGE" && event.action == FaultAction::crash) {
    return execute_storage_crash(event, directory, request_id);
  }
  if (event.actor_class == "STORAGE" && event.action == FaultAction::restart) {
    return execute_storage_restart(event, directory, request_id);
  }
  if (event.actor_class == "REGION" && event.action == FaultAction::partition) {
    return execute_partition(event, directory, request_id);
  }
  throw BenchmarkError("fault scenario has no production runtime projection");
}

}  // namespace

FaultExecutionResult execute_fault_scenario(
    const FaultEvent& event,
    const std::filesystem::path& directory,
    std::string_view request_id) {
  std::filesystem::create_directories(directory);
  auto observation = observe(event, directory, request_id);
  if (observation.outcome != "SAFE_BLOCKED" && observation.operation_count == 0U) {
    throw BenchmarkError("fault observation has no actual runtime operation");
  }
  const auto trace = observation.trace.canonical_text();
  if (observation.outcome != "SAFE_BLOCKED" && trace.empty()) {
    throw BenchmarkError("fault observation has no actual runtime trace");
  }
  const auto wal = observation.outcome == "SAFE_BLOCKED"
                       ? ascii_bytes("NO_DURABLE_TRANSITION")
                       : read_bytes(directory / "runtime.wal");
  return FaultExecutionResult{
      .observed_outcome = std::move(observation.outcome),
      .native_trace_id = raw_id(ascii_bytes(trace)),
      .native_state_root = state_id(observation.state_bytes),
      .native_effect_root = std::move(observation.effect_root),
      .native_wal_sha256 = raw_id(wal),
      .canonical_trace = trace,
      .runtime_operation_count = observation.operation_count,
      .wal_replayed = observation.wal_replayed,
      .view_change_observed = observation.view_change_observed,
      .current_checkpoint_advanced = observation.current_checkpoint_advanced,
      .availability_success = observation.availability_success,
  };
}

}  // namespace delta::runtime::benchmark
