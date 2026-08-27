#include <delta/core/transition.hpp>

#include <cstdint>
#include <limits>
#include <string>
#include <string_view>
#include <utility>

namespace delta::core::transition {
namespace {

[[noreturn]] void reject(ErrorCode code, const char* message) {
  throw TransitionError(code, message);
}

void require(bool condition, ErrorCode code, const char* message) {
  if (!condition) {
    reject(code, message);
  }
}

[[nodiscard]] bool terminal(protocol::RoundPhase phase) noexcept {
  return phase == protocol::RoundPhase::aggregated || phase == protocol::RoundPhase::aborted;
}

[[nodiscard]] std::uint64_t next_sequence(std::uint64_t current) {
  require(
      current != std::numeric_limits<std::uint64_t>::max(),
      ErrorCode::durable_sequence_overflow,
      "durable transition sequence is exhausted");
  return current + 1U;
}

void apply_command(protocol::RoundState& state, const protocol::Command& command) {
  if (command.command_kind == "FINALIZE_ROUND_CONFIG") {
    require(
        state.phase == protocol::RoundPhase::ticketing_open,
        ErrorCode::illegal_phase,
        "round-config replay requires TICKETING_OPEN");
    return;
  }
  require(!terminal(state.phase), ErrorCode::terminal_state, "terminal state rejects transitions");
  if (command.command_kind == "ADVANCE_VIEW") {
#if defined(DELTA_NATIVE_MUTANT_ALLOW_VIEW_JUMP)
    require(
        state.view != std::numeric_limits<std::uint64_t>::max(),
        ErrorCode::view_mismatch,
        "mutant only retains the view overflow guard");
#else
    require(
        state.view != std::numeric_limits<std::uint64_t>::max() && command.view == state.view + 1U,
        ErrorCode::view_mismatch,
        "view-change command does not name the next view");
#endif
    state.view = command.view;
    state.durable_sequence = next_sequence(state.durable_sequence);
    return;
  }
  require(command.view == state.view, ErrorCode::view_mismatch, "command view differs from state");
  if (command.command_kind == "ACCEPT_COMMITMENT") {
    require(
        state.phase == protocol::RoundPhase::ticketing_open ||
            state.phase == protocol::RoundPhase::committed,
        ErrorCode::illegal_phase,
        "commitment is outside the commitment window");
    require(
        state.committed_ticket_count < state.ticket_count,
        ErrorCode::ticket_limit_reached,
        "all configured tickets are already committed");
    ++state.committed_ticket_count;
    state.phase = protocol::RoundPhase::committed;
  } else if (command.command_kind == "ACCEPT_AVAILABILITY") {
    require(
        state.phase == protocol::RoundPhase::committed ||
            state.phase == protocol::RoundPhase::available,
        ErrorCode::illegal_phase,
        "availability is outside the availability window");
    require(
        state.available_ticket_count < state.committed_ticket_count,
        ErrorCode::availability_limit_reached,
        "availability exceeds committed tickets");
    ++state.available_ticket_count;
    state.phase = protocol::RoundPhase::available;
  } else if (command.command_kind == "FINALIZE_INPUT_FREEZE") {
    require(
        state.phase == protocol::RoundPhase::available,
        ErrorCode::illegal_phase,
        "input freeze requires AVAILABLE state");
    require(
        state.available_ticket_count > 0U,
        ErrorCode::input_set_empty,
        "input freeze cannot certify an empty set");
    state.phase = protocol::RoundPhase::eligible;
  } else if (command.command_kind == "FINALIZE_AGGREGATE") {
    require(
        state.phase == protocol::RoundPhase::eligible,
        ErrorCode::illegal_phase,
        "aggregate finalization requires ELIGIBLE state");
    state.phase = protocol::RoundPhase::aggregated;
    state.state_root = command.body_hash;
  } else if (command.command_kind == "CERTIFY_ABORT") {
    state.phase = protocol::RoundPhase::aborted;
  } else {
    reject(ErrorCode::unsupported_command, "command kind is not registered for feature 003");
  }
  state.durable_sequence = next_sequence(state.durable_sequence);
}

[[nodiscard]] protocol::EffectBatch make_effect_batch(
    const protocol::Command& command,
    std::string prior_state_id,
    std::string next_state_id) {
  const auto prefix = "effect:" + command.request_id + ":";
  return protocol::EffectBatch{
      {
          protocol::Effect{
              next_state_id,
              prefix + "01:persist",
              "PERSIST_STATE",
              command.actor_id,
          },
          protocol::Effect{
              command.body_hash,
              prefix + "02:publish",
              "PUBLISH_CERTIFICATE",
              "validators",
          },
      },
      std::move(next_state_id),
      std::move(prior_state_id),
      command.request_id,
      command.round_id,
  };
}

}  // namespace

TransitionError::TransitionError(ErrorCode code, std::string message)
    : std::runtime_error(std::move(message)), code_(code) {}

ErrorCode TransitionError::code() const noexcept { return code_; }

TransitionResult apply(
    std::span<const std::byte> prior_state_bytes,
    std::span<const std::byte> command_bytes,
    const canonical::Limits& limits) {
  const auto prior_state = protocol::parse_round_state(prior_state_bytes, limits);
  const auto command = protocol::parse_command(command_bytes, limits);
  require(command.round_id == prior_state.round_id, ErrorCode::round_mismatch, "round mismatch");
  require(command.height == prior_state.height, ErrorCode::height_mismatch, "height mismatch");
  if (command.command_kind != "ADVANCE_VIEW") {
    require(command.view == prior_state.view, ErrorCode::view_mismatch, "view mismatch");
  }

  auto next_state = prior_state;
  apply_command(next_state, command);
  auto next_state_encoded = protocol::encode(next_state, limits);
  const auto prior_state_id =
      canonical::content_id(canonical::Type::round_state, prior_state_bytes);
  const auto command_id = canonical::content_id(canonical::Type::command, command_bytes);
  const auto next_state_id =
      canonical::content_id(canonical::Type::round_state, next_state_encoded);

  auto effect_batch = make_effect_batch(command, prior_state_id, next_state_id);
  auto effect_batch_encoded = protocol::encode(effect_batch, limits);
  const auto effect_batch_id =
      canonical::content_id(canonical::Type::effect_batch, effect_batch_encoded);
  protocol::WalRecord wal_record{
      command_id,
      effect_batch_id,
      next_state_id,
      prior_state_id,
      "TRANSITION",
      command.round_id,
      next_state.durable_sequence,
  };
  auto wal_record_encoded = protocol::encode(wal_record, limits);
  const auto wal_record_id =
      canonical::content_id(canonical::Type::wal_record, wal_record_encoded);
  return TransitionResult{
      std::move(next_state),
      std::move(effect_batch),
      std::move(wal_record),
      std::move(next_state_encoded),
      std::move(effect_batch_encoded),
      std::move(wal_record_encoded),
      prior_state_id,
      command_id,
      next_state_id,
      effect_batch_id,
      wal_record_id,
  };
}

}  // namespace delta::core::transition
