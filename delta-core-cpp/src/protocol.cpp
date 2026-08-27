#include <delta/core/protocol.hpp>

#include <algorithm>
#include <array>
#include <charconv>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <span>
#include <string>
#include <string_view>
#include <system_error>
#include <utility>
#include <variant>
#include <vector>

namespace delta::core::protocol {
namespace {

using canonical::Envelope;
using canonical::MapEntry;
using canonical::Type;
using canonical::Value;

[[noreturn]] void reject(ErrorCode code, std::string message) {
  throw ProtocolError(code, std::move(message));
}

void require(bool condition, ErrorCode code, const char* message) {
  if (!condition) {
    reject(code, message);
  }
}

template <std::size_t Size>
void require_fields(const Value::Map& fields, const std::array<std::string_view, Size>& expected) {
  require(fields.size() == expected.size(), ErrorCode::field_set_mismatch, "field count mismatch");
  for (std::size_t index = 0; index < expected.size(); ++index) {
    require(
        fields[index].key == expected[index],
        ErrorCode::field_set_mismatch,
        "field name mismatch");
  }
}

[[nodiscard]] const Value& field(const Value::Map& fields, std::string_view name) {
  const auto found = std::lower_bound(
      fields.begin(), fields.end(), name, [](const MapEntry& entry, std::string_view candidate) {
        return entry.key < candidate;
      });
  require(
      found != fields.end() && found->key == name,
      ErrorCode::field_set_mismatch,
      "required field missing");
  return found->value;
}

[[nodiscard]] const std::string& text(const Value::Map& fields, std::string_view name) {
  const auto* result = std::get_if<std::string>(&field(fields, name).data);
  require(result != nullptr, ErrorCode::field_type_mismatch, "field is not text");
  return *result;
}

[[nodiscard]] std::uint32_t u32(const Value::Map& fields, std::string_view name) {
  const auto* result = std::get_if<std::uint64_t>(&field(fields, name).data);
  require(result != nullptr, ErrorCode::field_type_mismatch, "field is not unsigned integer");
  require(
      *result <= std::numeric_limits<std::uint32_t>::max(),
      ErrorCode::u32_out_of_range,
      "u32 field is out of range");
  return static_cast<std::uint32_t>(*result);
}

[[nodiscard]] const Value::Array& array(const Value::Map& fields, std::string_view name) {
  const auto* result = std::get_if<Value::Array>(&field(fields, name).data);
  require(result != nullptr, ErrorCode::field_type_mismatch, "field is not an array");
  return *result;
}

[[nodiscard]] const Value::Map& map(const Value::Map& fields, std::string_view name) {
  const auto* result = std::get_if<Value::Map>(&field(fields, name).data);
  require(result != nullptr, ErrorCode::field_type_mismatch, "field is not a map");
  return *result;
}

void require_constant(
    const Value::Map& fields,
    std::string_view name,
    std::string_view expected) {
  require(text(fields, name) == expected, ErrorCode::constant_mismatch, "constant field mismatch");
}

void require_ascii_id(std::string_view value) {
  require(!value.empty(), ErrorCode::identifier_invalid, "ASCII identifier is empty");
}

void require_content_id(std::string_view value) {
  constexpr std::string_view prefix = "sha256:";
  require(value.size() == prefix.size() + 64U, ErrorCode::identifier_invalid, "content ID length");
  require(value.starts_with(prefix), ErrorCode::identifier_invalid, "content ID prefix");
  for (const char digit : value.substr(prefix.size())) {
    const bool valid = (digit >= '0' && digit <= '9') || (digit >= 'a' && digit <= 'f');
    require(valid, ErrorCode::identifier_invalid, "content ID hexadecimal digit");
  }
}

void require_common(const Value::Map& fields, Type type) {
  require_constant(fields, "formal_semantics_id", formal_semantics_id);
  require_constant(fields, "schema_version", schema_version);
  require_constant(fields, "type_name", canonical::type_name(type));
}

[[nodiscard]] Envelope decode_expected(
    std::span<const std::byte> bytes,
    Type expected,
    const canonical::Limits& limits) {
  auto envelope = canonical::decode(bytes, limits);
  require(
      envelope.type == expected,
      ErrorCode::envelope_type_mismatch,
      "canonical envelope has the wrong registered type");
  return envelope;
}

[[nodiscard]] std::vector<std::string> text_array(const Value::Map& fields, std::string_view name) {
  std::vector<std::string> result;
  const auto& values = array(fields, name);
  result.reserve(values.size());
  for (const auto& value : values) {
    const auto* item = std::get_if<std::string>(&value.data);
    require(item != nullptr, ErrorCode::array_item_invalid, "array item is not text");
    result.push_back(*item);
  }
  return result;
}

void require_strict_order(const std::vector<std::string>& values) {
  for (std::size_t index = 1; index < values.size(); ++index) {
    require(
        values[index - 1U] < values[index],
        ErrorCode::array_not_canonical,
        "array is not strictly increasing");
  }
}

void require_unique(const std::vector<std::string>& values) {
  for (std::size_t left = 0; left < values.size(); ++left) {
    for (std::size_t right = left + 1U; right < values.size(); ++right) {
      require(values[left] != values[right], ErrorCode::array_not_canonical, "duplicate array item");
    }
  }
}

[[nodiscard]] RoundPhase parse_phase(std::string_view value) {
  if (value == "TICKETING_OPEN") {
    return RoundPhase::ticketing_open;
  }
  if (value == "COMMITTED") {
    return RoundPhase::committed;
  }
  if (value == "AVAILABLE") {
    return RoundPhase::available;
  }
  if (value == "ELIGIBLE") {
    return RoundPhase::eligible;
  }
  if (value == "AGGREGATED") {
    return RoundPhase::aggregated;
  }
  if (value == "ABORTED") {
    return RoundPhase::aborted;
  }
  reject(ErrorCode::state_invalid, "unknown round phase");
}

[[nodiscard]] IntegerProfile parse_integer_profile(const Value::Map& fields) {
  constexpr std::array expected = {
      std::string_view{"accumulator_bits"},
      std::string_view{"byte_order"},
      std::string_view{"profile_id"},
      std::string_view{"value_bits"},
  };
  require_fields(fields, expected);
  IntegerProfile result{
      u32(fields, "accumulator_bits"),
      text(fields, "byte_order"),
      text(fields, "profile_id"),
      u32(fields, "value_bits"),
  };
  require(
      result.accumulator_bits == 128U && result.byte_order == "BIG_ENDIAN" &&
          result.profile_id == "bft-int-fixture-v1" && result.value_bits == 64U,
      ErrorCode::profile_invalid,
      "prepared shard integer profile mismatch");
  return result;
}

[[nodiscard]] Value::Array encode_text_array(const std::vector<std::string>& values) {
  Value::Array result;
  result.reserve(values.size());
  for (const auto& value : values) {
    result.push_back(Value::text(value));
  }
  return result;
}

[[nodiscard]] Value::Map encode_integer_profile(const IntegerProfile& profile) {
  return {
      {"accumulator_bits", Value::unsigned_integer(profile.accumulator_bits)},
      {"byte_order", Value::text(profile.byte_order)},
      {"profile_id", Value::text(profile.profile_id)},
      {"value_bits", Value::unsigned_integer(profile.value_bits)},
  };
}

[[nodiscard]] std::string decimal(std::uint64_t value) { return std::to_string(value); }

[[nodiscard]] std::string decimal(std::int64_t value) { return std::to_string(value); }

}  // namespace

ProtocolError::ProtocolError(ErrorCode code, std::string message)
    : std::runtime_error(std::move(message)), code_(code) {}

ErrorCode ProtocolError::code() const noexcept { return code_; }

std::string_view round_phase_name(RoundPhase phase) {
  switch (phase) {
    case RoundPhase::ticketing_open:
      return "TICKETING_OPEN";
    case RoundPhase::committed:
      return "COMMITTED";
    case RoundPhase::available:
      return "AVAILABLE";
    case RoundPhase::eligible:
      return "ELIGIBLE";
    case RoundPhase::aggregated:
      return "AGGREGATED";
    case RoundPhase::aborted:
      return "ABORTED";
  }
  reject(ErrorCode::state_invalid, "unknown round phase value");
}

std::uint64_t parse_u64_decimal(std::string_view value) {
  require(!value.empty(), ErrorCode::decimal_not_canonical, "empty unsigned decimal");
  require(
      value == "0" || (value.front() >= '1' && value.front() <= '9'),
      ErrorCode::decimal_not_canonical,
      "unsigned decimal has a sign or leading zero");
  for (const char digit : value) {
    require(
        digit >= '0' && digit <= '9',
        ErrorCode::decimal_not_canonical,
        "unsigned decimal contains a non-digit");
  }
  std::uint64_t result = 0;
  const auto parsed = std::from_chars(value.data(), value.data() + value.size(), result);
  require(
      parsed.ec != std::errc::result_out_of_range,
      ErrorCode::decimal_out_of_range,
      "unsigned decimal is out of range");
  require(
      parsed.ec == std::errc{} && parsed.ptr == value.data() + value.size(),
      ErrorCode::decimal_not_canonical,
      "unsigned decimal is invalid");
  return result;
}

std::int64_t parse_i64_decimal(std::string_view value) {
  require(!value.empty(), ErrorCode::decimal_not_canonical, "empty signed decimal");
  const auto digits = value.front() == '-' ? value.substr(1U) : value;
  require(!digits.empty(), ErrorCode::decimal_not_canonical, "signed decimal has no digits");
  require(
      digits == "0" || (digits.front() >= '1' && digits.front() <= '9'),
      ErrorCode::decimal_not_canonical,
      "signed decimal has a leading zero");
  require(value != "-0" && value.front() != '+', ErrorCode::decimal_not_canonical, "signed zero");
  for (const char digit : digits) {
    require(
        digit >= '0' && digit <= '9',
        ErrorCode::decimal_not_canonical,
        "signed decimal contains a non-digit");
  }
  std::int64_t result = 0;
  const auto parsed = std::from_chars(value.data(), value.data() + value.size(), result);
  require(
      parsed.ec != std::errc::result_out_of_range,
      ErrorCode::decimal_out_of_range,
      "signed decimal is out of range");
  require(
      parsed.ec == std::errc{} && parsed.ptr == value.data() + value.size(),
      ErrorCode::decimal_not_canonical,
      "signed decimal is invalid");
  return result;
}

Command parse_command(std::span<const std::byte> bytes, const canonical::Limits& limits) {
  auto envelope = decode_expected(bytes, Type::command, limits);
  constexpr std::array expected = {
      std::string_view{"actor_id"},
      std::string_view{"body_hash"},
      std::string_view{"command_kind"},
      std::string_view{"formal_semantics_id"},
      std::string_view{"height"},
      std::string_view{"logical_tick"},
      std::string_view{"request_id"},
      std::string_view{"round_id"},
      std::string_view{"schema_version"},
      std::string_view{"type_name"},
      std::string_view{"view"},
  };
  require_fields(envelope.fields, expected);
  require_common(envelope.fields, Type::command);
  Command result{
      text(envelope.fields, "actor_id"),
      text(envelope.fields, "body_hash"),
      text(envelope.fields, "command_kind"),
      parse_u64_decimal(text(envelope.fields, "height")),
      parse_u64_decimal(text(envelope.fields, "logical_tick")),
      text(envelope.fields, "request_id"),
      text(envelope.fields, "round_id"),
      parse_u64_decimal(text(envelope.fields, "view")),
  };
  require_ascii_id(result.actor_id);
  require_content_id(result.body_hash);
  require_ascii_id(result.command_kind);
  require_ascii_id(result.request_id);
  require_ascii_id(result.round_id);
  return result;
}

RoundState parse_round_state(std::span<const std::byte> bytes, const canonical::Limits& limits) {
  auto envelope = decode_expected(bytes, Type::round_state, limits);
  constexpr std::array expected = {
      std::string_view{"available_ticket_count"},
      std::string_view{"committed_ticket_count"},
      std::string_view{"config_id"},
      std::string_view{"durable_sequence"},
      std::string_view{"formal_semantics_id"},
      std::string_view{"height"},
      std::string_view{"parent_checkpoint_id"},
      std::string_view{"phase"},
      std::string_view{"round_id"},
      std::string_view{"schema_version"},
      std::string_view{"state_root"},
      std::string_view{"ticket_count"},
      std::string_view{"type_name"},
      std::string_view{"view"},
  };
  require_fields(envelope.fields, expected);
  require_common(envelope.fields, Type::round_state);
  RoundState result{
      u32(envelope.fields, "available_ticket_count"),
      u32(envelope.fields, "committed_ticket_count"),
      text(envelope.fields, "config_id"),
      parse_u64_decimal(text(envelope.fields, "durable_sequence")),
      parse_u64_decimal(text(envelope.fields, "height")),
      text(envelope.fields, "parent_checkpoint_id"),
      parse_phase(text(envelope.fields, "phase")),
      text(envelope.fields, "round_id"),
      text(envelope.fields, "state_root"),
      u32(envelope.fields, "ticket_count"),
      parse_u64_decimal(text(envelope.fields, "view")),
  };
  require_content_id(result.config_id);
  require_content_id(result.parent_checkpoint_id);
  require_ascii_id(result.round_id);
  require_content_id(result.state_root);
  require(
      result.available_ticket_count <= result.committed_ticket_count &&
          result.committed_ticket_count <= result.ticket_count,
      ErrorCode::state_invalid,
      "round ticket counts are inconsistent");
  return result;
}

QuorumCertificate parse_quorum_certificate(
    std::span<const std::byte> bytes,
    const canonical::Limits& limits) {
  auto envelope = decode_expected(bytes, Type::quorum_certificate, limits);
  constexpr std::array expected = {
      std::string_view{"body_hash"},
      std::string_view{"context_id"},
      std::string_view{"formal_semantics_id"},
      std::string_view{"height"},
      std::string_view{"kind"},
      std::string_view{"qc_id"},
      std::string_view{"quorum_threshold"},
      std::string_view{"round_id"},
      std::string_view{"schema_version"},
      std::string_view{"signer_ids"},
      std::string_view{"type_name"},
      std::string_view{"validator_epoch_id"},
      std::string_view{"view"},
      std::string_view{"vote_ids"},
  };
  require_fields(envelope.fields, expected);
  require_common(envelope.fields, Type::quorum_certificate);
  QuorumCertificate result{
      text(envelope.fields, "body_hash"),
      text(envelope.fields, "context_id"),
      parse_u64_decimal(text(envelope.fields, "height")),
      text(envelope.fields, "kind"),
      text(envelope.fields, "qc_id"),
      u32(envelope.fields, "quorum_threshold"),
      text(envelope.fields, "round_id"),
      text_array(envelope.fields, "signer_ids"),
      text(envelope.fields, "validator_epoch_id"),
      parse_u64_decimal(text(envelope.fields, "view")),
      text_array(envelope.fields, "vote_ids"),
  };
  require_content_id(result.body_hash);
  require_ascii_id(result.context_id);
  require_ascii_id(result.kind);
  require_content_id(result.qc_id);
  require_ascii_id(result.round_id);
  require_content_id(result.validator_epoch_id);
  for (const auto& signer : result.signer_ids) {
    require_ascii_id(signer);
  }
  for (const auto& vote : result.vote_ids) {
    require_content_id(vote);
  }
  require_strict_order(result.signer_ids);
  require_unique(result.vote_ids);
  require(
      result.quorum_threshold > 0U && result.signer_ids.size() >= result.quorum_threshold,
      ErrorCode::quorum_insufficient,
      "certificate has insufficient unique signers");
  require(
      result.signer_ids.size() == result.vote_ids.size(),
      ErrorCode::array_item_invalid,
      "signer and vote arrays differ in length");
  return result;
}

PreparedIntegerShard parse_prepared_integer_shard(
    std::span<const std::byte> bytes,
    const canonical::Limits& limits) {
  auto envelope = decode_expected(bytes, Type::prepared_integer_shard, limits);
  constexpr std::array expected = {
      std::string_view{"coefficient"},
      std::string_view{"formal_semantics_id"},
      std::string_view{"input_leaf_id"},
      std::string_view{"integer_profile"},
      std::string_view{"parameter_id"},
      std::string_view{"round_id"},
      std::string_view{"schema_version"},
      std::string_view{"shard_id"},
      std::string_view{"ticket_id"},
      std::string_view{"type_name"},
      std::string_view{"values"},
  };
  require_fields(envelope.fields, expected);
  require_common(envelope.fields, Type::prepared_integer_shard);
  PreparedIntegerShard result{
      parse_i64_decimal(text(envelope.fields, "coefficient")),
      text(envelope.fields, "input_leaf_id"),
      parse_integer_profile(map(envelope.fields, "integer_profile")),
      text(envelope.fields, "parameter_id"),
      text(envelope.fields, "round_id"),
      text(envelope.fields, "shard_id"),
      text(envelope.fields, "ticket_id"),
      {},
  };
  require_content_id(result.input_leaf_id);
  require_ascii_id(result.parameter_id);
  require_ascii_id(result.round_id);
  require_ascii_id(result.shard_id);
  require_ascii_id(result.ticket_id);
  const auto& encoded_values = array(envelope.fields, "values");
  require(!encoded_values.empty(), ErrorCode::array_item_invalid, "prepared shard has no values");
  result.values.reserve(encoded_values.size());
  for (const auto& encoded_value : encoded_values) {
    const auto* item = std::get_if<std::string>(&encoded_value.data);
    require(item != nullptr, ErrorCode::array_item_invalid, "prepared shard value is not text");
    result.values.push_back(parse_i64_decimal(*item));
  }
  return result;
}

canonical::Bytes encode(const Command& value, const canonical::Limits& limits) {
  const Envelope envelope{
      Type::command,
      {
          {"actor_id", Value::text(value.actor_id)},
          {"body_hash", Value::text(value.body_hash)},
          {"command_kind", Value::text(value.command_kind)},
          {"formal_semantics_id", Value::text(std::string(formal_semantics_id))},
          {"height", Value::text(decimal(value.height))},
          {"logical_tick", Value::text(decimal(value.logical_tick))},
          {"request_id", Value::text(value.request_id)},
          {"round_id", Value::text(value.round_id)},
          {"schema_version", Value::text(std::string(schema_version))},
          {"type_name", Value::text(std::string(canonical::type_name(Type::command)))},
          {"view", Value::text(decimal(value.view))},
      },
  };
  auto bytes = canonical::encode(envelope, limits);
  static_cast<void>(parse_command(bytes, limits));
  return bytes;
}

canonical::Bytes encode(const RoundState& value, const canonical::Limits& limits) {
  const Envelope envelope{
      Type::round_state,
      {
          {"available_ticket_count", Value::unsigned_integer(value.available_ticket_count)},
          {"committed_ticket_count", Value::unsigned_integer(value.committed_ticket_count)},
          {"config_id", Value::text(value.config_id)},
          {"durable_sequence", Value::text(decimal(value.durable_sequence))},
          {"formal_semantics_id", Value::text(std::string(formal_semantics_id))},
          {"height", Value::text(decimal(value.height))},
          {"parent_checkpoint_id", Value::text(value.parent_checkpoint_id)},
          {"phase", Value::text(std::string(round_phase_name(value.phase)))},
          {"round_id", Value::text(value.round_id)},
          {"schema_version", Value::text(std::string(schema_version))},
          {"state_root", Value::text(value.state_root)},
          {"ticket_count", Value::unsigned_integer(value.ticket_count)},
          {"type_name", Value::text(std::string(canonical::type_name(Type::round_state)))},
          {"view", Value::text(decimal(value.view))},
      },
  };
  auto bytes = canonical::encode(envelope, limits);
  static_cast<void>(parse_round_state(bytes, limits));
  return bytes;
}

canonical::Bytes encode(const QuorumCertificate& value, const canonical::Limits& limits) {
  const Envelope envelope{
      Type::quorum_certificate,
      {
          {"body_hash", Value::text(value.body_hash)},
          {"context_id", Value::text(value.context_id)},
          {"formal_semantics_id", Value::text(std::string(formal_semantics_id))},
          {"height", Value::text(decimal(value.height))},
          {"kind", Value::text(value.kind)},
          {"qc_id", Value::text(value.qc_id)},
          {"quorum_threshold", Value::unsigned_integer(value.quorum_threshold)},
          {"round_id", Value::text(value.round_id)},
          {"schema_version", Value::text(std::string(schema_version))},
          {"signer_ids", Value::array(encode_text_array(value.signer_ids))},
          {"type_name", Value::text(std::string(canonical::type_name(Type::quorum_certificate)))},
          {"validator_epoch_id", Value::text(value.validator_epoch_id)},
          {"view", Value::text(decimal(value.view))},
          {"vote_ids", Value::array(encode_text_array(value.vote_ids))},
      },
  };
  auto bytes = canonical::encode(envelope, limits);
  static_cast<void>(parse_quorum_certificate(bytes, limits));
  return bytes;
}

canonical::Bytes encode(const PreparedIntegerShard& value, const canonical::Limits& limits) {
  std::vector<std::string> decimals;
  decimals.reserve(value.values.size());
  for (const auto item : value.values) {
    decimals.push_back(decimal(item));
  }
  const Envelope envelope{
      Type::prepared_integer_shard,
      {
          {"coefficient", Value::text(decimal(value.coefficient))},
          {"formal_semantics_id", Value::text(std::string(formal_semantics_id))},
          {"input_leaf_id", Value::text(value.input_leaf_id)},
          {"integer_profile", Value::map(encode_integer_profile(value.integer_profile))},
          {"parameter_id", Value::text(value.parameter_id)},
          {"round_id", Value::text(value.round_id)},
          {"schema_version", Value::text(std::string(schema_version))},
          {"shard_id", Value::text(value.shard_id)},
          {"ticket_id", Value::text(value.ticket_id)},
          {"type_name", Value::text(std::string(canonical::type_name(Type::prepared_integer_shard)))},
          {"values", Value::array(encode_text_array(decimals))},
      },
  };
  auto bytes = canonical::encode(envelope, limits);
  static_cast<void>(parse_prepared_integer_shard(bytes, limits));
  return bytes;
}

}  // namespace delta::core::protocol
