#pragma once

#include <delta/core/canonical.hpp>

#include <cstdint>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace delta::core::protocol {

inline constexpr std::string_view schema_version = "1.0.0";
inline constexpr std::string_view formal_semantics_id =
    "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";

enum class ErrorCode {
  envelope_type_mismatch,
  field_set_mismatch,
  field_type_mismatch,
  constant_mismatch,
  identifier_invalid,
  decimal_not_canonical,
  decimal_out_of_range,
  u32_out_of_range,
  array_item_invalid,
  array_not_canonical,
  quorum_insufficient,
  profile_invalid,
  state_invalid,
};

class ProtocolError final : public std::runtime_error {
 public:
  ProtocolError(ErrorCode code, std::string message);

  [[nodiscard]] ErrorCode code() const noexcept;

 private:
  ErrorCode code_;
};

enum class RoundPhase {
  ticketing_open,
  committed,
  available,
  eligible,
  aggregated,
  aborted,
};

struct Command {
  std::string actor_id;
  std::string body_hash;
  std::string command_kind;
  std::uint64_t height;
  std::uint64_t logical_tick;
  std::string request_id;
  std::string round_id;
  std::uint64_t view;

  bool operator==(const Command&) const = default;
};

struct RoundState {
  std::uint32_t available_ticket_count;
  std::uint32_t committed_ticket_count;
  std::string config_id;
  std::uint64_t durable_sequence;
  std::uint64_t height;
  std::string parent_checkpoint_id;
  RoundPhase phase;
  std::string round_id;
  std::string state_root;
  std::uint32_t ticket_count;
  std::uint64_t view;

  bool operator==(const RoundState&) const = default;
};

struct QuorumCertificate {
  std::string body_hash;
  std::string context_id;
  std::uint64_t height;
  std::string kind;
  std::string qc_id;
  std::uint32_t quorum_threshold;
  std::string round_id;
  std::vector<std::string> signer_ids;
  std::string validator_epoch_id;
  std::uint64_t view;
  std::vector<std::string> vote_ids;

  bool operator==(const QuorumCertificate&) const = default;
};

struct Vote {
  std::string body_hash;
  std::string context_id;
  std::uint64_t durable_sequence;
  std::uint64_t height;
  std::string kind;
  std::string round_id;
  std::string signature_id;
  std::string validator_epoch_id;
  std::string validator_id;
  std::uint64_t view;

  bool operator==(const Vote&) const = default;
};

struct IntegerProfile {
  std::uint32_t accumulator_bits;
  std::string byte_order;
  std::string profile_id;
  std::uint32_t value_bits;

  bool operator==(const IntegerProfile&) const = default;
};

struct PreparedIntegerShard {
  std::int64_t coefficient;
  std::string input_leaf_id;
  IntegerProfile integer_profile;
  std::string parameter_id;
  std::string round_id;
  std::string shard_id;
  std::string ticket_id;
  std::vector<std::int64_t> values;

  bool operator==(const PreparedIntegerShard&) const = default;
};

struct Effect {
  std::string body_hash;
  std::string effect_id;
  std::string kind;
  std::string target_id;

  bool operator==(const Effect&) const = default;
};

struct EffectBatch {
  std::vector<Effect> effects;
  std::string next_state_root;
  std::string prior_state_root;
  std::string request_id;
  std::string round_id;

  bool operator==(const EffectBatch&) const = default;
};

struct WalRecord {
  std::string command_id;
  std::string effect_batch_id;
  std::string next_state_root;
  std::string prior_state_root;
  std::string record_kind;
  std::string round_id;
  std::uint64_t sequence;

  bool operator==(const WalRecord&) const = default;
};

[[nodiscard]] std::string_view round_phase_name(RoundPhase phase);
[[nodiscard]] std::uint64_t parse_u64_decimal(std::string_view value);
[[nodiscard]] std::int64_t parse_i64_decimal(std::string_view value);

[[nodiscard]] Command parse_command(
    std::span<const std::byte> bytes,
    const canonical::Limits& limits = {});
[[nodiscard]] RoundState parse_round_state(
    std::span<const std::byte> bytes,
    const canonical::Limits& limits = {});
[[nodiscard]] QuorumCertificate parse_quorum_certificate(
    std::span<const std::byte> bytes,
    const canonical::Limits& limits = {});
[[nodiscard]] Vote parse_vote(
    std::span<const std::byte> bytes,
    const canonical::Limits& limits = {});
[[nodiscard]] PreparedIntegerShard parse_prepared_integer_shard(
    std::span<const std::byte> bytes,
    const canonical::Limits& limits = {});
[[nodiscard]] EffectBatch parse_effect_batch(
    std::span<const std::byte> bytes,
    const canonical::Limits& limits = {});
[[nodiscard]] WalRecord parse_wal_record(
    std::span<const std::byte> bytes,
    const canonical::Limits& limits = {});

[[nodiscard]] canonical::Bytes encode(const Command& value, const canonical::Limits& limits = {});
[[nodiscard]] canonical::Bytes encode(
    const RoundState& value,
    const canonical::Limits& limits = {});
[[nodiscard]] canonical::Bytes encode(
    const QuorumCertificate& value,
    const canonical::Limits& limits = {});
[[nodiscard]] canonical::Bytes encode(const Vote& value, const canonical::Limits& limits = {});
[[nodiscard]] canonical::Bytes encode(
    const PreparedIntegerShard& value,
    const canonical::Limits& limits = {});
[[nodiscard]] canonical::Bytes encode(
    const EffectBatch& value,
    const canonical::Limits& limits = {});
[[nodiscard]] canonical::Bytes encode(
    const WalRecord& value,
    const canonical::Limits& limits = {});

}  // namespace delta::core::protocol
