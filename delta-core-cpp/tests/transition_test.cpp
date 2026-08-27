#include <delta/core/canonical.hpp>
#include <delta/core/protocol.hpp>
#include <delta/core/transition.hpp>

#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <regex>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>

namespace canonical = delta::core::canonical;
namespace protocol = delta::core::protocol;
namespace transition = delta::core::transition;

namespace {

[[noreturn]] void fail(std::string message) { throw std::runtime_error(std::move(message)); }

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

[[nodiscard]] std::uint8_t hex_nibble(char value) {
  if (value >= '0' && value <= '9') {
    return static_cast<std::uint8_t>(value - '0');
  }
  if (value >= 'a' && value <= 'f') {
    return static_cast<std::uint8_t>(value - 'a' + 10);
  }
  fail("invalid lowercase hexadecimal fixture");
}

[[nodiscard]] canonical::Bytes decode_hex(std::string_view encoded) {
  expect((encoded.size() % 2U) == 0U, "odd hexadecimal fixture length");
  canonical::Bytes result;
  result.reserve(encoded.size() / 2U);
  for (std::size_t index = 0; index < encoded.size(); index += 2U) {
    const auto value = static_cast<std::uint8_t>(
        static_cast<std::uint8_t>(hex_nibble(encoded[index]) << 4U) |
        hex_nibble(encoded[index + 1U]));
    result.push_back(static_cast<std::byte>(value));
  }
  return result;
}

[[nodiscard]] canonical::Bytes golden(std::uint16_t type_code) {
  std::ifstream input(DELTA_GOLDEN_FIXTURE_PATH, std::ios::binary);
  expect(input.good(), "cannot open canonical golden fixture");
  const std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  const std::regex pattern(
      R"REGEX("envelope_hex":"([0-9a-f]+)","envelope_sha256":"[0-9a-f]+","type_code":([0-9]+))REGEX");
  for (auto cursor = std::sregex_iterator(document.begin(), document.end(), pattern);
       cursor != std::sregex_iterator();
       ++cursor) {
    const auto& match = *cursor;
    if (std::stoul(match[2].str()) == type_code) {
      return decode_hex(match[1].str());
    }
  }
  fail("registered golden vector not found");
}

[[nodiscard]] protocol::Command command_for(
    const protocol::RoundState& state,
    std::string kind,
    std::string request_id,
    std::string body_hash =
        "sha256:abababababababababababababababababababababababababababababababab") {
  return protocol::Command{
      "validator-1",
      std::move(body_hash),
      std::move(kind),
      state.height,
      10U,
      std::move(request_id),
      state.round_id,
      state.view,
  };
}

[[nodiscard]] transition::TransitionResult apply(
    const protocol::RoundState& state,
    const protocol::Command& command) {
  const auto state_bytes = protocol::encode(state);
  const auto command_bytes = protocol::encode(command);
  return transition::apply(state_bytes, command_bytes);
}

template <typename Operation>
void expect_transition_error(transition::ErrorCode expected, Operation operation) {
  try {
    operation();
  } catch (const transition::TransitionError& error) {
    expect(error.code() == expected, "unexpected stable transition error code");
    return;
  }
  fail("illegal transition was accepted");
}

void verify_result_links(const transition::TransitionResult& result) {
  expect(
      protocol::parse_round_state(result.next_state_bytes) == result.next_state,
      "next-state bytes do not decode to the returned state");
  expect(
      protocol::parse_effect_batch(result.effect_batch_bytes) == result.effect_batch,
      "effect bytes do not decode to the returned batch");
  expect(
      protocol::parse_wal_record(result.wal_record_bytes) == result.wal_record,
      "WAL bytes do not decode to the returned record");
  expect(
      result.effect_batch.prior_state_root == result.prior_state_id &&
          result.effect_batch.next_state_root == result.next_state_id,
      "effect state links differ from content IDs");
  expect(
      result.wal_record.command_id == result.command_id &&
          result.wal_record.effect_batch_id == result.effect_batch_id &&
          result.wal_record.next_state_root == result.next_state_id,
      "WAL links differ from content IDs");
  expect(
      result.wal_record_id ==
          canonical::content_id(canonical::Type::wal_record, result.wal_record_bytes),
      "WAL content ID mismatch");
}

void test_exact_replay_is_deterministic() {
  const auto state_bytes = golden(5U);
  const auto command_bytes = golden(6U);
  const auto first = transition::apply(state_bytes, command_bytes);
  const auto second = transition::apply(state_bytes, command_bytes);

  expect(first == second, "same prior-state and command bytes produced different results");
  expect(first.next_state_bytes == state_bytes, "round-config replay changed current state");
  verify_result_links(first);
}

void test_legal_lifecycle() {
  auto state = protocol::parse_round_state(golden(5U));
  const auto committed = apply(state, command_for(state, "ACCEPT_COMMITMENT", "request-commit"));
  expect(
      committed.next_state.phase == protocol::RoundPhase::committed &&
          committed.next_state.committed_ticket_count == 1U,
      "commitment transition mismatch");
  verify_result_links(committed);

  state = committed.next_state;
  const auto available = apply(state, command_for(state, "ACCEPT_AVAILABILITY", "request-ac"));
  expect(
      available.next_state.phase == protocol::RoundPhase::available &&
          available.next_state.available_ticket_count == 1U,
      "availability transition mismatch");

  state = available.next_state;
  const auto eligible = apply(state, command_for(state, "FINALIZE_INPUT_FREEZE", "request-freeze"));
  expect(eligible.next_state.phase == protocol::RoundPhase::eligible, "freeze transition mismatch");

  state = eligible.next_state;
  const std::string aggregate_root =
      "sha256:cdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd";
  const auto aggregated = apply(
      state,
      command_for(state, "FINALIZE_AGGREGATE", "request-aggregate", aggregate_root));
  expect(
      aggregated.next_state.phase == protocol::RoundPhase::aggregated &&
          aggregated.next_state.state_root == aggregate_root,
      "aggregate transition mismatch");
  expect(
      aggregated.next_state.durable_sequence == state.durable_sequence + 1U,
      "durable sequence did not advance exactly once");
  verify_result_links(aggregated);
}

void test_abort_and_view_change() {
  auto state = protocol::parse_round_state(golden(5U));
  auto view_command = command_for(state, "ADVANCE_VIEW", "request-view");
  view_command.view = state.view + 1U;
  const auto changed = apply(state, view_command);
  expect(changed.next_state.view == 1U, "view change did not select the next view");

  state = changed.next_state;
  const auto aborted = apply(state, command_for(state, "CERTIFY_ABORT", "request-abort"));
  expect(aborted.next_state.phase == protocol::RoundPhase::aborted, "abort transition mismatch");
  expect(
      aborted.next_state.parent_checkpoint_id == state.parent_checkpoint_id,
      "abort changed the parent checkpoint");
}

void test_context_and_phase_fail_closed() {
  const auto state = protocol::parse_round_state(golden(5U));
  auto command = command_for(state, "ACCEPT_COMMITMENT", "request-wrong-round");
  command.round_id = "another-round";
  expect_transition_error(transition::ErrorCode::round_mismatch, [&state, &command] {
    static_cast<void>(apply(state, command));
  });

  command = command_for(state, "ACCEPT_COMMITMENT", "request-wrong-height");
  ++command.height;
  expect_transition_error(transition::ErrorCode::height_mismatch, [&state, &command] {
    static_cast<void>(apply(state, command));
  });

  command = command_for(state, "NOT_REGISTERED", "request-unknown");
  expect_transition_error(transition::ErrorCode::unsupported_command, [&state, &command] {
    static_cast<void>(apply(state, command));
  });

  auto aggregated = state;
  aggregated.phase = protocol::RoundPhase::aggregated;
  command = command_for(aggregated, "ACCEPT_COMMITMENT", "request-terminal");
  expect_transition_error(transition::ErrorCode::terminal_state, [&aggregated, &command] {
    static_cast<void>(apply(aggregated, command));
  });
}

void test_sequence_and_count_bounds() {
  auto state = protocol::parse_round_state(golden(5U));
  state.durable_sequence = std::numeric_limits<std::uint64_t>::max();
  auto command = command_for(state, "ACCEPT_COMMITMENT", "request-sequence");
  expect_transition_error(transition::ErrorCode::durable_sequence_overflow, [&state, &command] {
    static_cast<void>(apply(state, command));
  });

  state = protocol::parse_round_state(golden(5U));
  state.committed_ticket_count = state.ticket_count;
  state.available_ticket_count = state.ticket_count;
  state.phase = protocol::RoundPhase::committed;
  command = command_for(state, "ACCEPT_COMMITMENT", "request-limit");
  expect_transition_error(transition::ErrorCode::ticket_limit_reached, [&state, &command] {
    static_cast<void>(apply(state, command));
  });
}

}  // namespace

int main() {
  try {
    test_exact_replay_is_deterministic();
    test_legal_lifecycle();
    test_abort_and_view_change();
    test_context_and_phase_fail_closed();
    test_sequence_and_count_bounds();
  } catch (const std::exception& error) {
    std::cerr << "delta_core transition test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta_core transition tests passed\n";
  return 0;
}
