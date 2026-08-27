#include <delta/core/canonical.hpp>
#include <delta/core/protocol.hpp>
#include <delta/core/transition.hpp>

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
namespace transition = delta::core::transition;

namespace {

[[noreturn]] void fail(std::string message) { throw std::runtime_error(std::move(message)); }

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

[[nodiscard]] std::string load(std::string_view path) {
  std::ifstream input(std::string(path), std::ios::binary);
  expect(input.good(), "cannot open portability fixture");
  return {std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
}

[[nodiscard]] std::string field(const std::string& document, std::string_view name) {
  const std::regex pattern("\\\"" + std::string(name) + "\\\":\\\"([^\\\"]+)\\\"");
  std::smatch match;
  expect(std::regex_search(document, match, pattern), "required portability field is missing");
  return match[1].str();
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

[[nodiscard]] canonical::Bytes golden(const std::string& document, std::uint16_t type_code) {
  const std::regex pattern(
      R"REGEX("envelope_hex":"([0-9a-f]+)","envelope_sha256":"[0-9a-f]+","type_code":([0-9]+))REGEX");
  for (auto cursor = std::sregex_iterator(document.begin(), document.end(), pattern);
       cursor != std::sregex_iterator();
       ++cursor) {
    if (std::stoul((*cursor)[2].str()) == type_code) {
      return decode_hex((*cursor)[1].str());
    }
  }
  fail("registered golden vector not found");
}

[[nodiscard]] std::string encode_hex(const canonical::Bytes& bytes) {
  constexpr char digits[] = "0123456789abcdef";
  std::string result;
  result.reserve(bytes.size() * 2U);
  for (const auto byte : bytes) {
    const auto value = std::to_integer<std::uint8_t>(byte);
    result.push_back(digits[value >> 4U]);
    result.push_back(digits[value & 0x0fU]);
  }
  return result;
}

[[nodiscard]] canonical::Bytes string_bytes(std::string_view value) {
  canonical::Bytes result;
  result.reserve(value.size());
  for (const unsigned char byte : value) {
    result.push_back(static_cast<std::byte>(byte));
  }
  return result;
}

void test_explicit_wire_endian(const std::string& fixture) {
  const canonical::Envelope unsigned_probe{
      canonical::Type::command,
      {{"probe", canonical::Value::unsigned_integer(0x0102030405060708ULL)}},
  };
  expect(
      encode_hex(canonical::encode(unsigned_probe)) == field(fixture, "unsigned_probe_envelope_hex"),
      "unsigned multibyte wire order differs from golden bytes");

  const canonical::Envelope signed_probe{
      canonical::Type::command,
      {{"probe", canonical::Value::signed_integer(-2)}},
  };
  expect(
      encode_hex(canonical::encode(signed_probe)) == field(fixture, "signed_minus_two_envelope_hex"),
      "signed multibyte wire order differs from golden bytes");
  expect(field(fixture, "wire_byte_order") == "BIG_ENDIAN", "wire byte order changed");
}

void test_incompatible_profile_rejected(
    const std::string& fixture,
    const std::string& golden_document) {
  auto shard = protocol::parse_prepared_integer_shard(golden(golden_document, 10U));
  shard.integer_profile.byte_order = field(fixture, "rejected_profile_byte_order");
  try {
    static_cast<void>(protocol::encode(shard));
  } catch (const protocol::ProtocolError& error) {
    expect(error.code() == protocol::ErrorCode::profile_invalid, "wrong profile rejection code");
    return;
  }
  fail("incompatible integer profile byte order was accepted");
}

void test_golden_transition(const std::string& fixture, const std::string& golden_document) {
  expect(
      canonical::sha256_hex(string_bytes(golden_document)) ==
          field(fixture, "canonical_fixture_sha256"),
      "canonical fixture content hash changed");
  const auto prior_state = golden(golden_document, 5U);
  const auto command = golden(golden_document, 6U);
  const auto result = transition::apply(prior_state, command);
  expect(result.next_state_bytes == prior_state, "golden replay changed state bytes");
  expect(result.prior_state_id == field(fixture, "golden_prior_state_id"), "prior root mismatch");
  expect(result.command_id == field(fixture, "golden_command_id"), "command ID mismatch");
  expect(result.next_state_id == field(fixture, "golden_next_state_id"), "next root mismatch");
  expect(
      result.effect_batch_id == field(fixture, "golden_effect_batch_id"),
      "effect batch ID mismatch");
  expect(result.wal_record_id == field(fixture, "golden_wal_record_id"), "WAL ID mismatch");
}

}  // namespace

int main() {
  try {
    const auto fixture = load(DELTA_PORTABILITY_FIXTURE_PATH);
    const auto golden_document = load(DELTA_GOLDEN_FIXTURE_PATH);
    test_explicit_wire_endian(fixture);
    test_incompatible_profile_rejected(fixture, golden_document);
    test_golden_transition(fixture, golden_document);
  } catch (const std::exception& error) {
    std::cerr << "delta_core portability test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta_core portability tests passed\n";
  return 0;
}
