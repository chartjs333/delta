#include "fixture_support.hpp"
#include "trace_support.hpp"

#include <delta/core/canonical.hpp>
#include <delta/core/protocol.hpp>
#include <delta/core/transition.hpp>
#if defined(DELTA_EXPECT_DURABILITY_MUTANT)
#include <delta/runtime/runtime.hpp>
#endif

#include <filesystem>
#include <iostream>
#include <string>

namespace canonical = delta::core::canonical;
namespace protocol = delta::core::protocol;
#if defined(DELTA_EXPECT_DURABILITY_MUTANT)
namespace runtime = delta::runtime;
#endif
namespace test = delta::test;
namespace trace = delta::test::trace;

namespace {

[[nodiscard]] std::string state_id(const canonical::Bytes& value) {
  return canonical::content_id(canonical::Type::round_state, value);
}

#if defined(DELTA_EXPECT_VIEW_MUTANT)
void expose_view_mutant(const std::filesystem::path& output) {
  const auto initial = test::golden(DELTA_GOLDEN_FIXTURE_PATH, 5U);
  const auto state = protocol::parse_round_state(initial);
  const auto body = test::derived_id("mutant-view:", "skipped-view");
  auto command = test::command_for(state, "ADVANCE_VIEW", "mutant-view-jump", body);
  command.view = state.view + 2U;
  const auto accepted = delta::core::transition::apply(initial, protocol::encode(command));
  test::expect(accepted.next_state.view == 2U, "production view mutant was not activated");

  trace::Event event;
  event.action_id = "ACT-VIEW-FINALIZE";
  event.actor_id = "validator-1";
  event.actor_role = "VALIDATOR";
  event.body_hash = body;
  event.durable_sequence = accepted.next_state.durable_sequence;
  event.logical_time = 0U;
  event.next_state_root = accepted.next_state_id;
  event.outcome = "FINALIZED";
  event.prior_state_root = accepted.prior_state_id;
  event.request_id = command.request_id;
  event.result_hash = test::derived_id("mutant-view-result:", body);
  event.vote_context_id = "VIEW-CHANGE:round-003-fixture:2";
  trace::write(
      output,
      "TRACE-NATIVE-003-MUTANT-VIEW-WITHOUT-QC",
      state_id(initial),
      accepted.next_state_id,
      "IN_PROGRESS",
      {event});
  std::cout << "COUNTEREXAMPLE QC_QUORUM_MISSING: production ADVANCE_VIEW guard removed\n";
}
#endif

#if defined(DELTA_EXPECT_DURABILITY_MUTANT)
void expose_durability_mutant(const std::filesystem::path& output) {
  const auto initial = test::golden(DELTA_GOLDEN_FIXTURE_PATH, 5U);
  const auto directory = test::fresh_directory("native-durability-mutant");
  const auto state = protocol::parse_round_state(initial);
  const auto body = test::derived_id("mutant-commitment:", "ticket-000");
  const auto command = test::command_for(
      state, "ACCEPT_COMMITMENT", "mutant-undurable-effect", body);
  runtime::SubmitReceipt exposed;
  {
    runtime::Runtime instance({directory, initial, 16U});
    exposed = instance.submit(protocol::encode(command));
    test::expect(!exposed.effect_batch_bytes.empty(), "durability mutant exposed no effect");
  }
  {
    runtime::Runtime recovered({directory, initial, 16U});
    test::expect(
        recovered.journal_sequence() == 0U && recovered.state_bytes() == initial &&
            recovered.state_bytes() != exposed.next_state_bytes,
        "production durability mutant was not activated");
  }

  trace::Event event;
  event.action_id = "ACT-PUBLISH";
  event.actor_id = "validator-1";
  event.actor_role = "VALIDATOR";
  event.body_hash = exposed.effect_batch_id;
  event.durable_sequence = std::nullopt;
  event.error_code = "PARTIAL_PUBLICATION";
  event.logical_time = 0U;
  event.next_state_root = exposed.next_state_id;
  event.outcome = "ACCEPTED";
  event.prior_state_root = state_id(initial);
  event.request_id = command.request_id;
  event.result_hash = exposed.effect_batch_id;
  trace::write(
      output,
      "TRACE-NATIVE-003-MUTANT-EFFECT-BEFORE-DURABILITY",
      state_id(initial),
      exposed.next_state_id,
      "IN_PROGRESS",
      {event});
  std::cout
      << "COUNTEREXAMPLE PARTIAL_OR_UNCERTIFIED_PUBLICATION: production WAL barrier removed\n";
}
#endif

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 2) {
      test::fail("expected native mutant counterexample trace path");
    }
#if defined(DELTA_EXPECT_VIEW_MUTANT)
    expose_view_mutant(argv[1]);
#elif defined(DELTA_EXPECT_DURABILITY_MUTANT)
    expose_durability_mutant(argv[1]);
#else
#error "native mutant harness requires one expected production mutant"
#endif
  } catch (const std::exception& error) {
    std::cerr << "native production mutant was not exposed: " << error.what() << '\n';
    return 1;
  }
  return 0;
}
