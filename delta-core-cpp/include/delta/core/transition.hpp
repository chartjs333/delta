#pragma once

#include <delta/core/canonical.hpp>
#include <delta/core/protocol.hpp>

#include <span>
#include <stdexcept>
#include <string>

namespace delta::core::transition {

enum class ErrorCode {
  round_mismatch,
  height_mismatch,
  view_mismatch,
  unsupported_command,
  illegal_phase,
  ticket_limit_reached,
  availability_limit_reached,
  input_set_empty,
  terminal_state,
  durable_sequence_overflow,
};

class TransitionError final : public std::runtime_error {
 public:
  TransitionError(ErrorCode code, std::string message);

  [[nodiscard]] ErrorCode code() const noexcept;

 private:
  ErrorCode code_;
};

struct TransitionResult {
  protocol::RoundState next_state;
  protocol::EffectBatch effect_batch;
  protocol::WalRecord wal_record;
  canonical::Bytes next_state_bytes;
  canonical::Bytes effect_batch_bytes;
  canonical::Bytes wal_record_bytes;
  std::string prior_state_id;
  std::string command_id;
  std::string next_state_id;
  std::string effect_batch_id;
  std::string wal_record_id;

  bool operator==(const TransitionResult&) const = default;
};

[[nodiscard]] TransitionResult apply(
    std::span<const std::byte> prior_state_bytes,
    std::span<const std::byte> command_bytes,
    const canonical::Limits& limits = {});

}  // namespace delta::core::transition
