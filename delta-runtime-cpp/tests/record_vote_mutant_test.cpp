#include "fixture_support.hpp"

#include "../../delta-core-cpp/tests/vote_fixture.hpp"

#include <delta/core/consensus.hpp>
#include <delta/core/protocol.hpp>
#if defined(DELTA_EXPECT_RECORD_VOTE_DURABILITY_MUTANT)
#include <delta/runtime/runtime.hpp>
#endif

#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>

namespace consensus = delta::core::consensus;
namespace protocol = delta::core::protocol;
#if defined(DELTA_EXPECT_RECORD_VOTE_DURABILITY_MUTANT)
namespace runtime = delta::runtime;
#endif
namespace test = delta::test;
namespace vote_fixture = delta::test::vote_fixture;

namespace {

[[noreturn]] void fail(std::string message) { throw std::runtime_error(std::move(message)); }

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

#if defined(DELTA_EXPECT_RECORD_VOTE_CONFLICT_MUTANT)
void production_rejects_same_context_conflict() {
  protocol::Vote vote{
      .body_hash = vote_fixture::id('1'),
      .context_id = "record-vote-mutant-context",
      .durable_sequence = 1U,
      .height = 1U,
      .kind = "ROUND_CONFIG",
      .round_id = "record-vote-mutant-round",
      .signature_id = vote_fixture::id('2'),
      .validator_epoch_id = vote_fixture::id('3'),
      .validator_id = "validator-1",
      .view = 0U,
  };
  consensus::VoteJournal journal;
  expect(
      journal.record(vote) == consensus::Disposition::recorded,
      "first vote was not recorded");
  vote.signature_id = vote_fixture::id('4');
  try {
    static_cast<void>(journal.record(vote));
  } catch (const consensus::ConsensusError& error) {
    expect(
        error.code() == consensus::ErrorCode::conflicting_vote,
        "same-context mutation returned the wrong stable error");
    return;
  }
  fail("same-context byte conflict was accepted as replay");
}
#endif

#if defined(DELTA_EXPECT_RECORD_VOTE_CONTEXT_GUARD_MUTANT)
void production_rejects_context_outside_native_policy() {
  auto fixture = vote_fixture::full(consensus::VoteAction::round_config);
  fixture.vote.context_id = "record-vote-mutant-outside-context";
  try {
    static_cast<void>(consensus::validate_vote_admission(
        fixture.policy,
        fixture.state,
        consensus::VoteAdmissionState{
            fixture.policy.initial_logical_tick,
            true,
            false,
        },
        fixture.vote,
        1U));
  } catch (const consensus::ConsensusError& error) {
    expect(
        error.code() == consensus::ErrorCode::vote_admission_rejected,
        "outside-policy context returned the wrong stable error");
    return;
  }
  fail("vote context outside the immutable native policy was admitted");
}
#endif

#if defined(DELTA_EXPECT_RECORD_VOTE_DURABILITY_MUTANT)
[[nodiscard]] runtime::Config vote_config(
    const std::filesystem::path& directory,
    const vote_fixture::Fixture& fixture) {
  return runtime::Config{
      .directory = directory,
      .initial_state_bytes = protocol::encode(fixture.state),
      .submission_capacity = 8U,
      .durable_binding_guard = {},
      .vote_policy = fixture.policy,
      .expected_wal_identity = {},
  };
}

void production_recovers_exposed_vote_receipt() {
  const auto fixture = vote_fixture::full(consensus::VoteAction::round_config);
  const auto directory = test::fresh_directory("record-vote-durability-mutant");
  const auto vote = protocol::encode(fixture.vote);
  runtime::VoteReceipt exposed;
  {
    runtime::Runtime instance(vote_config(directory, fixture));
    exposed = instance.record_vote(vote);
    expect(
        !exposed.replay && exposed.journal_sequence == 1U,
        "first vote receipt was not exposed");
  }
  {
    runtime::Runtime recovered(vote_config(directory, fixture));
    expect(
        recovered.journal_sequence() == exposed.journal_sequence &&
            recovered.recovered_vote_count() == 1U,
        "exposed vote receipt was not durable across restart");
    const auto replay = recovered.record_vote(vote);
    expect(
        replay.replay && replay.vote_id == exposed.vote_id &&
            replay.journal_sequence == exposed.journal_sequence && replay.frame == exposed.frame,
        "durable vote retry did not return its original native receipt identity");
  }
}
#endif

#if defined(DELTA_EXPECT_RECORD_VOTE_ARITHMETIC_ADMISSION_MUTANT)
[[nodiscard]] vote_fixture::Fixture arbitrary_arithmetic_fixture(
    consensus::VoteAction action) {
  auto fixture = vote_fixture::full(action);
  if (action == consensus::VoteAction::parameter) {
    auto& body = fixture.policy.snapshot.parameter_bodies.front();
    body.result_numerators = {"9223372036854775807"};
    fixture.policy.candidates.front().body_hash =
        consensus::vote_parameter_body_id(body);
  } else {
    auto& body = fixture.policy.snapshot.apply_candidates.front();
    body.next_model_hash = vote_fixture::id('a');
    body.next_model_values = {"9223372036854775807"};
    body.next_optimizer_hash = vote_fixture::id('b');
    body.next_optimizer_values = {"-9223372036854775808"};
    fixture.policy.candidates.front().body_hash =
        delta::certificates::content_id(body);
    fixture.policy.candidates.front().parents.apply_candidate_id =
        fixture.policy.candidates.front().body_hash;
  }
  fixture.candidate = fixture.policy.candidates.front();
  fixture.vote.body_hash = fixture.candidate.body_hash;
  return fixture;
}

[[nodiscard]] bool rejects_unverified_arithmetic(
    const vote_fixture::Fixture& fixture) {
  try {
    static_cast<void>(consensus::validate_vote_admission(
        fixture.policy,
        fixture.state,
        consensus::VoteAdmissionState{
            fixture.policy.initial_logical_tick,
            true,
            false,
        },
        fixture.vote,
        1U));
  } catch (const consensus::ConsensusError& error) {
    expect(
        error.code() == consensus::ErrorCode::vote_admission_rejected,
        "unverified arithmetic returned the wrong stable error");
    return true;
  }
  return false;
}

void production_rejects_arbitrary_arithmetic_without_authoritative_inputs() {
  expect(
      rejects_unverified_arithmetic(
          arbitrary_arithmetic_fixture(consensus::VoteAction::parameter)) &&
          rejects_unverified_arithmetic(
              arbitrary_arithmetic_fixture(consensus::VoteAction::apply)),
      "caller-selected PARAMETER/APPLY arithmetic was admitted");
}
#endif

}  // namespace

int main() {
  try {
#if defined(DELTA_EXPECT_RECORD_VOTE_CONFLICT_MUTANT)
    production_rejects_same_context_conflict();
#elif defined(DELTA_EXPECT_RECORD_VOTE_CONTEXT_GUARD_MUTANT)
    production_rejects_context_outside_native_policy();
#elif defined(DELTA_EXPECT_RECORD_VOTE_DURABILITY_MUTANT)
    production_recovers_exposed_vote_receipt();
#elif defined(DELTA_EXPECT_RECORD_VOTE_ARITHMETIC_ADMISSION_MUTANT)
    production_rejects_arbitrary_arithmetic_without_authoritative_inputs();
#else
#error "record vote mutant test requires one expected mutant"
#endif
  } catch (const std::exception& error) {
    std::cerr << "RECORD_VOTE production invariant failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "RECORD_VOTE production invariant held; configured mutant survived\n";
  return 0;
}
