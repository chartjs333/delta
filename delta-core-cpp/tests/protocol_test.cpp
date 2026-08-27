#include <delta/core/canonical.hpp>
#include <delta/core/protocol.hpp>

#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <regex>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>

namespace canonical = delta::core::canonical;
namespace protocol = delta::core::protocol;

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

[[nodiscard]] canonical::Value& mutable_field(canonical::Envelope& envelope, std::string_view name) {
  for (auto& entry : envelope.fields) {
    if (entry.key == name) {
      return entry.value;
    }
  }
  fail("test fixture field not found");
}

template <typename Parser>
void expect_protocol_error(
    const canonical::Envelope& envelope,
    protocol::ErrorCode expected,
    Parser parser) {
  try {
    const auto bytes = canonical::encode(envelope);
    static_cast<void>(parser(bytes, canonical::Limits{}));
  } catch (const protocol::ProtocolError& error) {
    expect(error.code() == expected, "unexpected stable protocol error code");
    return;
  }
  fail("invalid protocol object was accepted");
}

void test_explicit_golden_types() {
  const auto command_bytes = golden(6U);
  const auto state_bytes = golden(5U);
  const auto qc_bytes = golden(4U);
  const auto shard_bytes = golden(10U);

  const auto command = protocol::parse_command(command_bytes);
  expect(command.command_kind == "FINALIZE_ROUND_CONFIG", "command kind mismatch");
  expect(command.height == 1U && command.logical_tick == 10U, "command decimal mismatch");
  expect(protocol::encode(command) == command_bytes, "command encoding differs from golden bytes");

  const auto state = protocol::parse_round_state(state_bytes);
  expect(state.phase == protocol::RoundPhase::ticketing_open, "round phase mismatch");
  expect(state.ticket_count == 100U, "round ticket count mismatch");
  expect(protocol::encode(state) == state_bytes, "round state encoding differs from golden bytes");

  const auto qc = protocol::parse_quorum_certificate(qc_bytes);
  expect(qc.quorum_threshold == 3U && qc.signer_ids.size() == 3U, "QC quorum mismatch");
  expect(protocol::encode(qc) == qc_bytes, "QC encoding differs from golden bytes");

  const auto shard = protocol::parse_prepared_integer_shard(shard_bytes);
  expect(shard.coefficient == 1 && shard.values.size() == 5U, "prepared shard mismatch");
  expect(
      shard.values.front() == -9223372036854775807LL - 1 &&
          shard.values.back() == 9223372036854775807LL,
      "prepared shard signed boundary mismatch");
  expect(protocol::encode(shard) == shard_bytes, "prepared shard encoding differs from golden bytes");
}

void test_command_fails_closed() {
  auto command = canonical::decode(golden(6U));
  command.fields.pop_back();
  expect_protocol_error(command, protocol::ErrorCode::field_set_mismatch, protocol::parse_command);

  command = canonical::decode(golden(6U));
  mutable_field(command, "height") = canonical::Value::text("01");
  expect_protocol_error(
      command, protocol::ErrorCode::decimal_not_canonical, protocol::parse_command);

  command = canonical::decode(golden(6U));
  mutable_field(command, "logical_tick") = canonical::Value::unsigned_integer(10U);
  expect_protocol_error(command, protocol::ErrorCode::field_type_mismatch, protocol::parse_command);

  command = canonical::decode(golden(6U));
  mutable_field(command, "body_hash") = canonical::Value::text("sha256:ABC");
  expect_protocol_error(command, protocol::ErrorCode::identifier_invalid, protocol::parse_command);

  const auto state = canonical::decode(golden(5U));
  expect_protocol_error(state, protocol::ErrorCode::envelope_type_mismatch, protocol::parse_command);
}

void test_state_fails_closed() {
  auto state = canonical::decode(golden(5U));
  mutable_field(state, "phase") = canonical::Value::text("UNKNOWN");
  expect_protocol_error(state, protocol::ErrorCode::state_invalid, protocol::parse_round_state);

  state = canonical::decode(golden(5U));
  mutable_field(state, "available_ticket_count") = canonical::Value::unsigned_integer(2U);
  mutable_field(state, "committed_ticket_count") = canonical::Value::unsigned_integer(1U);
  expect_protocol_error(state, protocol::ErrorCode::state_invalid, protocol::parse_round_state);

  state = canonical::decode(golden(5U));
  mutable_field(state, "ticket_count") =
      canonical::Value::unsigned_integer(std::uint64_t{1} << 32U);
  expect_protocol_error(state, protocol::ErrorCode::u32_out_of_range, protocol::parse_round_state);
}

void test_qc_fails_closed() {
  auto qc = canonical::decode(golden(4U));
  auto* signers = std::get_if<canonical::Value::Array>(&mutable_field(qc, "signer_ids").data);
  expect(signers != nullptr, "golden signer array missing");
  std::swap((*signers)[0], (*signers)[1]);
  expect_protocol_error(qc, protocol::ErrorCode::array_not_canonical, protocol::parse_quorum_certificate);

  qc = canonical::decode(golden(4U));
  mutable_field(qc, "quorum_threshold") = canonical::Value::unsigned_integer(4U);
  expect_protocol_error(qc, protocol::ErrorCode::quorum_insufficient, protocol::parse_quorum_certificate);

  qc = canonical::decode(golden(4U));
  auto* votes = std::get_if<canonical::Value::Array>(&mutable_field(qc, "vote_ids").data);
  expect(votes != nullptr, "golden vote array missing");
  (*votes)[1] = (*votes)[0];
  expect_protocol_error(qc, protocol::ErrorCode::array_not_canonical, protocol::parse_quorum_certificate);
}

void test_prepared_shard_fails_closed() {
  auto shard = canonical::decode(golden(10U));
  auto* profile =
      std::get_if<canonical::Value::Map>(&mutable_field(shard, "integer_profile").data);
  expect(profile != nullptr, "golden integer profile missing");
  for (auto& entry : *profile) {
    if (entry.key == "value_bits") {
      entry.value = canonical::Value::unsigned_integer(32U);
    }
  }
  expect_protocol_error(
      shard, protocol::ErrorCode::profile_invalid, protocol::parse_prepared_integer_shard);

  shard = canonical::decode(golden(10U));
  auto* values = std::get_if<canonical::Value::Array>(&mutable_field(shard, "values").data);
  expect(values != nullptr, "golden prepared values missing");
  (*values)[0] = canonical::Value::text("9223372036854775808");
  expect_protocol_error(
      shard, protocol::ErrorCode::decimal_out_of_range, protocol::parse_prepared_integer_shard);

  shard = canonical::decode(golden(10U));
  values = std::get_if<canonical::Value::Array>(&mutable_field(shard, "values").data);
  expect(values != nullptr, "golden prepared values missing");
  values->clear();
  expect_protocol_error(
      shard, protocol::ErrorCode::array_item_invalid, protocol::parse_prepared_integer_shard);
}

void test_decimal_boundaries() {
  expect(protocol::parse_u64_decimal("18446744073709551615") == UINT64_MAX, "u64 max rejected");
  expect(protocol::parse_i64_decimal("-9223372036854775808") == INT64_MIN, "i64 min rejected");
  try {
    static_cast<void>(protocol::parse_i64_decimal("-0"));
  } catch (const protocol::ProtocolError& error) {
    expect(error.code() == protocol::ErrorCode::decimal_not_canonical, "negative zero error");
    return;
  }
  fail("negative zero was accepted");
}

}  // namespace

int main() {
  try {
    test_explicit_golden_types();
    test_command_fails_closed();
    test_state_fails_closed();
    test_qc_fails_closed();
    test_prepared_shard_fails_closed();
    test_decimal_boundaries();
  } catch (const std::exception& error) {
    std::cerr << "delta_core protocol test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta_core protocol tests passed\n";
  return 0;
}
