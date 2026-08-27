#include "fixture_support.hpp"
#include "trace_support.hpp"

#include <delta/core/canonical.hpp>
#include <delta/core/protocol.hpp>
#include <delta/runtime/runtime.hpp>

#include <cstdint>
#include <filesystem>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace canonical = delta::core::canonical;
namespace protocol = delta::core::protocol;
namespace runtime = delta::runtime;
namespace test = delta::test;
namespace trace = delta::test::trace;

namespace {

inline constexpr std::string_view config_hash =
    "sha256:ba04c93913be2f015e22e3f731235fd5044fdc61a4929ad64bbf9ef966d8ae97";

[[nodiscard]] std::string state_id(const canonical::Bytes& bytes) {
  return canonical::content_id(canonical::Type::round_state, bytes);
}

[[nodiscard]] runtime::Config config(
    const std::filesystem::path& directory,
    const canonical::Bytes& initial) {
  return runtime::Config{directory, initial, 64U};
}

[[nodiscard]] protocol::Vote vote_for(
    std::string kind,
    std::string validator,
    std::string context,
    std::string body,
    std::uint64_t view) {
  return protocol::Vote{
      std::move(body),
      std::move(context),
      1U,
      1U,
      std::move(kind),
      std::string(trace::round_id),
      test::derived_id("signature:", validator),
      std::string(trace::epoch_id),
      std::move(validator),
      view,
  };
}

[[nodiscard]] trace::Event event(
    std::string action,
    std::optional<std::string> actor,
    std::optional<std::string> role,
    std::optional<std::string> body,
    std::optional<std::uint64_t> sequence,
    std::string prior,
    std::string next,
    std::string outcome,
    std::uint64_t logical_time) {
  trace::Event result;
  result.action_id = std::move(action);
  result.actor_id = std::move(actor);
  result.actor_role = std::move(role);
  result.body_hash = std::move(body);
  result.durable_sequence = sequence;
  result.prior_state_root = std::move(prior);
  result.next_state_root = std::move(next);
  result.outcome = std::move(outcome);
  result.logical_time = logical_time;
  return result;
}

void append_vote_events(
    std::vector<trace::Event>& events,
    std::string_view action,
    std::string_view context,
    std::string_view body,
    std::string_view root,
    const std::vector<runtime::VoteReceipt>& receipts,
    std::uint64_t logical_start,
    std::uint64_t view) {
  for (std::size_t index = 0; index < receipts.size(); ++index) {
    auto item = event(
        std::string(action),
        "validator-" + std::to_string(index + 1U),
        "VALIDATOR",
        std::string(body),
        receipts[index].journal_sequence,
        std::string(root),
        std::string(root),
        "ACCEPTED",
        logical_start + index);
    item.request_id = "native-vote-" + std::to_string(index + 1U);
    item.vote_context_id = std::string(context);
    item.view = view;
    events.push_back(std::move(item));
  }
}

[[nodiscard]] std::vector<runtime::VoteReceipt> record_quorum(
    runtime::Runtime& instance,
    std::string_view kind,
    std::string_view context,
    std::string_view body,
    std::uint64_t view) {
  std::vector<runtime::VoteReceipt> receipts;
  for (std::uint64_t validator = 1U; validator <= 3U; ++validator) {
    const auto value = vote_for(
        std::string(kind),
        "validator-" + std::to_string(validator),
        std::string(context),
        std::string(body),
        view);
    receipts.push_back(instance.record_vote(protocol::encode(value)));
  }
  return receipts;
}

void export_normal(const std::filesystem::path& output, const canonical::Bytes& initial) {
  const auto directory = test::fresh_directory("trace-normal");
  const auto initial_root = state_id(initial);
  runtime::Runtime instance(config(directory, initial));
  auto state = protocol::parse_round_state(initial);
  const auto commitment = test::derived_id("commitment:", "ticket-000");
  const auto commit_command = test::command_for(
      state, "ACCEPT_COMMITMENT", "native-normal-commit", commitment);
  const auto committed = instance.submit(protocol::encode(commit_command));
  state = protocol::parse_round_state(committed.next_state_bytes);
  const auto availability = test::derived_id("availability:", "ticket-000");
  const auto availability_command = test::command_for(
      state, "ACCEPT_AVAILABILITY", "native-normal-availability", availability);
  const auto available = instance.submit(protocol::encode(availability_command));
  state = protocol::parse_round_state(available.next_state_bytes);
  const auto isc_body = test::derived_id("isc-body:", "ticket-000");
  const std::string context = "ISC:round-003-fixture:1:0";
  const auto votes = record_quorum(instance, "INPUT_SET", context, isc_body, 0U);
  const auto freeze_command = test::command_for(
      state, "FINALIZE_INPUT_FREEZE", "native-normal-freeze", isc_body);
  const auto frozen = instance.submit(protocol::encode(freeze_command));
  const auto isc_id = test::derived_id("isc-result:", isc_body);

  std::vector<trace::Event> events;
  auto commit_event = event(
      "ACT-COMMIT",
      "validator-1",
      "VALIDATOR",
      commitment,
      committed.journal_sequence,
      initial_root,
      committed.next_state_id,
      "ACCEPTED",
      0U);
  commit_event.request_id = commit_command.request_id;
  events.push_back(std::move(commit_event));
  auto availability_event = event(
      "ACT-AVAIL-ATTEST",
      "validator-1",
      "VALIDATOR",
      availability,
      available.journal_sequence,
      committed.next_state_id,
      available.next_state_id,
      "ACCEPTED",
      1U);
  availability_event.request_id = availability_command.request_id;
  events.push_back(std::move(availability_event));
  append_vote_events(events, "ACT-ISC-VOTE", context, isc_body, available.next_state_id, votes, 2U, 0U);
  auto final = event(
      "ACT-ISC-FINALIZE",
      "validator-1",
      "VALIDATOR",
      isc_body,
      frozen.journal_sequence,
      available.next_state_id,
      frozen.next_state_id,
      "FINALIZED",
      5U);
  final.artifact_refs = {commitment};
  final.request_id = freeze_command.request_id;
  final.result_hash = isc_id;
  final.vote_context_id = context;
  events.push_back(std::move(final));
  trace::write(
      output / "native-normal.json",
      "TRACE-NATIVE-003-NORMAL",
      initial_root,
      frozen.next_state_id,
      "IN_PROGRESS",
      events);
}

void export_view_change(const std::filesystem::path& output, const canonical::Bytes& initial) {
  const auto directory = test::fresh_directory("trace-view");
  const auto initial_root = state_id(initial);
  runtime::Runtime instance(config(directory, initial));
  const auto body = test::derived_id("view-change:", "view-1");
  const std::string context = "VIEW-CHANGE:round-003-fixture:1";
  const auto votes = record_quorum(instance, "VIEW_CHANGE", context, body, 0U);
  auto state = protocol::parse_round_state(initial);
  auto command = test::command_for(state, "ADVANCE_VIEW", "native-view-finalize", body);
  command.view = 1U;
  const auto changed = instance.submit(protocol::encode(command));
  std::vector<trace::Event> events;
  append_vote_events(events, "ACT-VIEW-VOTE", context, body, initial_root, votes, 0U, 0U);
  auto final = event(
      "ACT-VIEW-FINALIZE",
      "validator-1",
      "VALIDATOR",
      body,
      changed.journal_sequence,
      initial_root,
      changed.next_state_id,
      "FINALIZED",
      3U);
  final.request_id = command.request_id;
  final.result_hash = test::derived_id("view-qc:", body);
  final.vote_context_id = context;
  events.push_back(std::move(final));
  trace::write(
      output / "native-view-change.json",
      "TRACE-NATIVE-003-VIEW-CHANGE",
      initial_root,
      changed.next_state_id,
      "IN_PROGRESS",
      events);
}

void export_abort(const std::filesystem::path& output, const canonical::Bytes& initial) {
  const auto directory = test::fresh_directory("trace-abort");
  const auto initial_root = state_id(initial);
  runtime::Runtime instance(config(directory, initial));
  const auto body = test::derived_id("abort:", "hard-deadline");
  const std::string context = "HARD-ABORT:round-003-fixture";
  const auto votes = record_quorum(instance, "ABORT", context, body, 0U);
  const auto state = protocol::parse_round_state(initial);
  const auto command = test::command_for(state, "CERTIFY_ABORT", "native-abort-finalize", body);
  const auto aborted = instance.submit(protocol::encode(command));
  std::vector<trace::Event> events;
  append_vote_events(events, "ACT-ABORT-VOTE", context, body, initial_root, votes, 0U, 0U);
  auto final = event(
      "ACT-ABORT-FINALIZE",
      "validator-1",
      "VALIDATOR",
      body,
      aborted.journal_sequence,
      initial_root,
      aborted.next_state_id,
      "FINALIZED",
      3U);
  final.request_id = command.request_id;
  final.result_hash = test::derived_id("abort-qc:", body);
  final.vote_context_id = context;
  events.push_back(std::move(final));
  trace::write(
      output / "native-certified-abort.json",
      "TRACE-NATIVE-003-CERTIFIED-ABORT",
      initial_root,
      aborted.next_state_id,
      "ABORTED",
      events);
}

void export_crash_recovery(const std::filesystem::path& output, const canonical::Bytes& initial) {
  const auto directory = test::fresh_directory("trace-crash-recovery");
  const auto initial_root = state_id(initial);
  const std::string context = "ROUND_CONFIG:round-003-fixture:1:0";
  const auto value = vote_for(
      "ROUND_CONFIG", "validator-1", context, std::string(config_hash), 0U);
  const auto vote_bytes = protocol::encode(value);
  {
    runtime::Runtime instance(config(directory, initial));
    try {
      static_cast<void>(instance.record_vote(
          vote_bytes, runtime::CrashPoint::after_durability_before_commit));
      test::fail("durable crash injection did not stop the native runtime");
    } catch (const runtime::RuntimeError& error) {
      test::expect(
          error.code() == runtime::ErrorCode::simulated_crash,
          "unexpected native crash error code");
    }
  }
  runtime::Runtime recovered(config(directory, initial));
  test::expect(recovered.recovered_vote_count() == 1U, "durable vote was not recovered");
  const auto replay = recovered.record_vote(vote_bytes);
  test::expect(replay.replay && replay.journal_sequence == 1U, "recovered vote did not replay");

  std::vector<trace::Event> events;
  auto persisted = event(
      "ACT-CONFIG-VOTE",
      "validator-1",
      "VALIDATOR",
      std::string(config_hash),
      1U,
      initial_root,
      initial_root,
      "ACCEPTED",
      0U);
  persisted.vote_context_id = context;
  events.push_back(std::move(persisted));
  auto crash = event(
      "ACT-CRASH",
      "validator-1",
      "VALIDATOR",
      std::nullopt,
      1U,
      initial_root,
      initial_root,
      "FAULT",
      1U);
  crash.error_code = "CRASH_AFTER_DURABILITY";
  crash.vote_context_id = context;
  events.push_back(std::move(crash));
  auto restart = event(
      "ACT-RESTART",
      "validator-1",
      "VALIDATOR",
      std::nullopt,
      1U,
      initial_root,
      initial_root,
      "ACCEPTED",
      2U);
  restart.vote_context_id = context;
  events.push_back(std::move(restart));
  auto recover = event(
      "ACT-JOURNAL-RECOVER",
      "validator-1",
      "VALIDATOR",
      replay.vote_id,
      replay.journal_sequence,
      initial_root,
      initial_root,
      "ACCEPTED",
      3U);
  recover.vote_context_id = context;
  events.push_back(std::move(recover));
  auto replay_event = event(
      "ACT-MESSAGE-REPLAY",
      "validator-1",
      "VALIDATOR",
      replay.vote_id,
      replay.journal_sequence,
      initial_root,
      initial_root,
      "NO_OP",
      4U);
  replay_event.request_id = "native-recovered-vote-replay";
  replay_event.vote_context_id = context;
  events.push_back(std::move(replay_event));
  trace::write(
      output / "native-crash-recovery.json",
      "TRACE-NATIVE-003-CRASH-RECOVERY",
      initial_root,
      initial_root,
      "IN_PROGRESS",
      events);
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 2) {
      test::fail("expected exact trace output directory");
    }
    const auto initial = test::golden(DELTA_GOLDEN_FIXTURE_PATH, 5U);
    const std::filesystem::path output(argv[1]);
    export_normal(output, initial);
    export_view_change(output, initial);
    export_abort(output, initial);
    export_crash_recovery(output, initial);
  } catch (const std::exception& error) {
    std::cerr << "native trace export failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "four native implementation traces exported\n";
  return 0;
}
