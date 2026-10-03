#include "fixture_support.hpp"
#include "trace_support.hpp"
#include "../../delta-core-cpp/tests/vote_fixture.hpp"

#include <delta/core/canonical.hpp>
#include <delta/core/consensus.hpp>
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
namespace consensus = delta::core::consensus;
namespace protocol = delta::core::protocol;
namespace runtime = delta::runtime;
namespace test = delta::test;
namespace trace = delta::test::trace;
namespace vote_fixture = delta::test::vote_fixture;

namespace {

inline constexpr std::string_view config_hash =
    "sha256:ba04c93913be2f015e22e3f731235fd5044fdc61a4929ad64bbf9ef966d8ae97";

[[nodiscard]] std::string state_id(const canonical::Bytes& bytes) {
  return canonical::content_id(canonical::Type::round_state, bytes);
}

[[nodiscard]] runtime::Config config(
    const std::filesystem::path& directory,
    const canonical::Bytes& initial) {
  return runtime::Config{
      .directory = directory,
      .initial_state_bytes = initial,
      .submission_capacity = 64U,
      .durable_binding_guard = {},
      .vote_policy = {},
      .expected_wal_identity = {},
  };
}

[[nodiscard]] protocol::Vote vote_for(
    const consensus::VoteAdmissionPolicy& policy,
    const consensus::VoteCandidateBinding& candidate) {
  return protocol::Vote{
      candidate.body_hash,
      std::string(consensus::frozen_vote_context(candidate)),
      1U,
      candidate.height,
      std::string(consensus::vote_kind_name(candidate.action)),
      policy.round_id,
      test::derived_id("signature:", policy.local_validator_id),
      policy.validator_epoch_id,
      policy.local_validator_id,
      candidate.view,
  };
}

[[nodiscard]] consensus::VoteAdmissionPolicy vote_policy(
    std::string validator,
    consensus::VoteAdmissionPolicy policy,
    consensus::VoteCandidateBinding candidate,
    std::uint64_t logical_tick) {
  policy.local_validator_id = std::move(validator);
  policy.initial_logical_tick = logical_tick;
  policy.candidates = {std::move(candidate)};
  return policy;
}

[[nodiscard]] std::vector<std::string> parent_hashes(
    const consensus::VoteParentState& parents) {
  std::vector<std::string> result;
  const std::string* values[]{
      &parents.round_config_id,
      &parents.parent_checkpoint_id,
      &parents.input_set_certificate_id,
      &parents.seed_transcript_id,
      &parents.norm_evidence_id,
      &parents.eligibility_certificate_id,
      &parents.aggregation_plan_certificate_id,
      &parents.parameter_matrix_root,
      &parents.aggregate_root_certificate_id,
      &parents.apply_profile_id,
      &parents.apply_candidate_id,
      &parents.last_finalized_certificate_id,
  };
  for (const auto* value : values) {
    if (!value->empty()) {
      result.push_back(*value);
    }
  }
  return result;
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
    std::string_view root,
    const std::vector<runtime::VoteReceipt>& receipts,
    std::uint64_t logical_start) {
  for (std::size_t index = 0; index < receipts.size(); ++index) {
    const auto vote = protocol::parse_vote(receipts[index].frame);
    auto item = event(
        receipts[index].formal_action_id,
        vote.validator_id,
        "VALIDATOR",
        vote.body_hash,
        receipts[index].journal_sequence,
        std::string(root),
        std::string(root),
        "ACCEPTED",
        logical_start + index);
    item.request_id = receipts[index].vote_id;
    item.vote_context_id = receipts[index].context_id;
    item.parent_hashes = parent_hashes(receipts[index].parents);
    item.height = vote.height;
    item.round_id = vote.round_id;
    item.validator_epoch = vote.validator_epoch_id;
    item.view = vote.view;
    events.push_back(std::move(item));
  }
}

[[nodiscard]] std::vector<runtime::VoteReceipt> record_quorum(
    const std::filesystem::path& directory,
    const canonical::Bytes& state_bytes,
    const consensus::VoteAdmissionPolicy& policy_template,
    const consensus::VoteCandidateBinding& candidate,
    std::uint64_t logical_tick) {
  std::vector<runtime::VoteReceipt> receipts;
  for (std::uint64_t validator = 1U; validator <= 3U; ++validator) {
    const auto policy = vote_policy(
        "validator-" + std::to_string(validator), policy_template, candidate, logical_tick);
    runtime::Runtime instance(runtime::Config{
        .directory = directory / ("validator-" + std::to_string(validator)),
        .initial_state_bytes = state_bytes,
        .submission_capacity = 8U,
        .durable_binding_guard = {},
        .vote_policy = policy,
        .expected_wal_identity = {},
    });
    const auto value = vote_for(policy, candidate);
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
  auto fixture = vote_fixture::full(consensus::VoteAction::input_set, state);
  const auto context = fixture.candidate.context_id;
  fixture.policy.candidates = {fixture.candidate};
  const auto isc_body = fixture.candidate.body_hash;
  const auto votes = record_quorum(
      directory / "votes",
      available.next_state_bytes,
      fixture.policy,
      fixture.candidate,
      2U);
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
  append_vote_events(events, available.next_state_id, votes, 2U);
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
  const auto state = protocol::parse_round_state(initial);
  auto fixture = vote_fixture::full(consensus::VoteAction::view_change, state);
  const auto context = fixture.candidate.context_id;
  fixture.policy.candidates = {fixture.candidate};
  const auto body = fixture.candidate.body_hash;
  const auto votes = record_quorum(
      directory / "votes", initial, fixture.policy, fixture.candidate, 50U);
  auto command = test::command_for(state, "ADVANCE_VIEW", "native-view-finalize", body);
  command.view = 1U;
  const auto changed = instance.submit(protocol::encode(command));
  std::vector<trace::Event> events;
  append_vote_events(events, initial_root, votes, 0U);
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
  const auto state = protocol::parse_round_state(initial);
  auto fixture = vote_fixture::full(consensus::VoteAction::abort, state);
  const auto context = fixture.candidate.context_id;
  fixture.policy.candidates = {fixture.candidate};
  const auto body = fixture.candidate.body_hash;
  const auto votes = record_quorum(
      directory / "votes", initial, fixture.policy, fixture.candidate, 100U);
  const auto command = test::command_for(state, "CERTIFY_ABORT", "native-abort-finalize", body);
  const auto aborted = instance.submit(protocol::encode(command));
  std::vector<trace::Event> events;
  append_vote_events(events, initial_root, votes, 0U);
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
  const auto state = protocol::parse_round_state(initial);
  auto fixture = vote_fixture::full(consensus::VoteAction::round_config, state);
  const auto policy = vote_policy("validator-1", fixture.policy, fixture.candidate, 0U);
  const auto value = vote_for(policy, fixture.candidate);
  const auto vote_bytes = protocol::encode(value);
  const auto crash_config = [&] {
    return runtime::Config{
        .directory = directory,
        .initial_state_bytes = initial,
        .submission_capacity = 8U,
        .durable_binding_guard = {},
        .vote_policy = policy,
        .expected_wal_identity = {},
    };
  };
  {
    runtime::Runtime instance(crash_config());
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
  runtime::Runtime recovered(crash_config());
  test::expect(recovered.recovered_vote_count() == 1U, "durable vote was not recovered");
  const auto replay = recovered.record_vote(vote_bytes);
  test::expect(replay.replay && replay.journal_sequence == 1U, "recovered vote did not replay");
  const auto recovered_vote = protocol::parse_vote(replay.frame);

  std::vector<trace::Event> events;
  append_vote_events(events, initial_root, {replay}, 0U);
  auto crash = event(
      "ACT-CRASH",
      recovered_vote.validator_id,
      "VALIDATOR",
      std::nullopt,
      replay.journal_sequence,
      initial_root,
      initial_root,
      "FAULT",
      1U);
  crash.error_code = "CRASH_AFTER_DURABILITY";
  crash.height = recovered_vote.height;
  crash.round_id = recovered_vote.round_id;
  crash.validator_epoch = recovered_vote.validator_epoch_id;
  crash.view = recovered_vote.view;
  crash.vote_context_id = replay.context_id;
  events.push_back(std::move(crash));
  auto restart = event(
      "ACT-RESTART",
      recovered_vote.validator_id,
      "VALIDATOR",
      std::nullopt,
      replay.journal_sequence,
      initial_root,
      initial_root,
      "ACCEPTED",
      2U);
  restart.vote_context_id = replay.context_id;
  restart.height = recovered_vote.height;
  restart.round_id = recovered_vote.round_id;
  restart.validator_epoch = recovered_vote.validator_epoch_id;
  restart.view = recovered_vote.view;
  events.push_back(std::move(restart));
  auto recover = event(
      "ACT-JOURNAL-RECOVER",
      recovered_vote.validator_id,
      "VALIDATOR",
      replay.vote_id,
      replay.journal_sequence,
      initial_root,
      initial_root,
      "ACCEPTED",
      3U);
  recover.request_id = replay.vote_id;
  recover.height = recovered_vote.height;
  recover.parent_hashes = parent_hashes(replay.parents);
  recover.round_id = recovered_vote.round_id;
  recover.validator_epoch = recovered_vote.validator_epoch_id;
  recover.view = recovered_vote.view;
  recover.vote_context_id = replay.context_id;
  events.push_back(std::move(recover));
  auto replay_event = event(
      "ACT-MESSAGE-REPLAY",
      recovered_vote.validator_id,
      "VALIDATOR",
      replay.vote_id,
      replay.journal_sequence,
      initial_root,
      initial_root,
      "NO_OP",
      4U);
  replay_event.request_id = replay.vote_id;
  replay_event.height = recovered_vote.height;
  replay_event.parent_hashes = parent_hashes(replay.parents);
  replay_event.round_id = recovered_vote.round_id;
  replay_event.validator_epoch = recovered_vote.validator_epoch_id;
  replay_event.view = recovered_vote.view;
  replay_event.vote_context_id = replay.context_id;
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
    auto initial_state = protocol::parse_round_state(
        test::golden(DELTA_GOLDEN_FIXTURE_PATH, 5U));
    initial_state.config_id = std::string(config_hash);
    const auto initial = protocol::encode(initial_state);
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
