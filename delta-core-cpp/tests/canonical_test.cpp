#include <delta/core/canonical.hpp>

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
#include <vector>

namespace canonical = delta::core::canonical;

namespace {

struct GoldenVector {
  std::string content_id;
  canonical::Bytes envelope;
  std::string envelope_sha256;
  std::uint16_t type_code;
  std::string type_name;
};

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

[[nodiscard]] std::vector<GoldenVector> load_golden_vectors() {
  std::ifstream input(DELTA_GOLDEN_FIXTURE_PATH, std::ios::binary);
  expect(input.good(), "cannot open canonical golden fixture");
  const std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  const std::regex pattern(
      R"REGEX("content_id":"([^"]+)","envelope_hex":"([0-9a-f]+)","envelope_sha256":"([0-9a-f]+)","type_code":([0-9]+),"type_name":"([A-Z_]+)")REGEX");

  std::vector<GoldenVector> vectors;
  for (auto cursor = std::sregex_iterator(document.begin(), document.end(), pattern);
       cursor != std::sregex_iterator();
       ++cursor) {
    const auto& match = *cursor;
    vectors.push_back(GoldenVector{
        match[1].str(),
        decode_hex(match[2].str()),
        match[3].str(),
        static_cast<std::uint16_t>(std::stoul(match[4].str())),
        match[5].str(),
    });
  }
  expect(vectors.size() == 10U, "golden fixture must contain all ten canonical types");
  return vectors;
}

void expect_decode_error(
    const canonical::Bytes& encoded,
    canonical::ErrorCode expected,
    const canonical::Limits& limits = {}) {
  try {
    static_cast<void>(canonical::decode(encoded, limits));
  } catch (const canonical::DecodeError& error) {
    expect(error.code() == expected, "unexpected stable decoder error code");
    return;
  }
  fail("invalid envelope was accepted");
}

void test_golden_vectors() {
  const auto vectors = load_golden_vectors();
  std::uint16_t expected_code = 1U;
  for (const auto& vector : vectors) {
    expect(vector.type_code == expected_code, "canonical type codes are not contiguous");
    const auto envelope = canonical::decode(vector.envelope);
    const auto type = static_cast<canonical::Type>(vector.type_code);
    expect(envelope.type == type, "decoded type differs from golden vector");
    expect(canonical::type_name(type) == vector.type_name, "type name differs from registry");
    expect(canonical::encode(envelope) == vector.envelope, "decode/encode changed canonical bytes");
    expect(
        canonical::sha256_hex(vector.envelope) == vector.envelope_sha256,
        "envelope SHA-256 differs from golden vector");
    expect(
        canonical::content_id(type, vector.envelope) == vector.content_id,
        "domain-separated content ID differs from golden vector");
    ++expected_code;
  }
}

void test_explicit_values_round_trip() {
  canonical::Envelope envelope{
      canonical::Type::command,
      {
          {"a", canonical::Value::boolean(true)},
          {"b", canonical::Value::unsigned_integer(std::numeric_limits<std::uint64_t>::max())},
          {"c", canonical::Value::signed_integer(std::numeric_limits<std::int64_t>::min())},
          {"d", canonical::Value::bytes({std::byte{0}, std::byte{0xff}})},
          {"e", canonical::Value::text("ASCII")},
          {"f", canonical::Value::array({canonical::Value::boolean(false)})},
          {"g", canonical::Value::map({{"nested", canonical::Value::signed_integer(-1)}})},
      },
  };
  const auto encoded = canonical::encode(envelope);
  expect(canonical::decode(encoded) == envelope, "explicit canonical value round-trip failed");
}

void test_fail_closed_decoder() {
  expect_decode_error({}, canonical::ErrorCode::truncated);
  expect_decode_error(decode_hex("58524331010000010000000101"), canonical::ErrorCode::bad_magic);
  expect_decode_error(
      decode_hex("44524331020000010000000101"), canonical::ErrorCode::unsupported_version);
  expect_decode_error(decode_hex("44524331010000ff0000000101"), canonical::ErrorCode::unknown_type);
  expect_decode_error(
      decode_hex("44524331010000010000000201"),
      canonical::ErrorCode::payload_length_mismatch);
  expect_decode_error(
      decode_hex("4452433101000001000000010100"), canonical::ErrorCode::trailing_bytes);
  expect_decode_error(decode_hex("44524331010000010000000101"), canonical::ErrorCode::invalid_root);
  expect_decode_error(decode_hex("445243310100000100000001ff"), canonical::ErrorCode::invalid_tag);
  expect_decode_error(
      decode_hex("44524331010000010000001331000000022100000001620121000000016101"),
      canonical::ErrorCode::noncanonical_map_order);
  expect_decode_error(
      decode_hex("445243310100000100000011310000000121000000016121000000017f"),
      canonical::ErrorCode::invalid_ascii);

  canonical::Limits shallow;
  shallow.nesting_depth = 0U;
  expect_decode_error(
      decode_hex("44524331010000010000000c310000000121000000016101"),
      canonical::ErrorCode::nesting_too_deep,
      shallow);
}

void test_sha256_known_answer() {
  const canonical::Bytes empty;
  expect(
      canonical::sha256_hex(empty) ==
          "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "SHA-256 known-answer test failed");
}

}  // namespace

int main() {
  try {
    test_sha256_known_answer();
    test_golden_vectors();
    test_explicit_values_round_trip();
    test_fail_closed_decoder();
  } catch (const std::exception& error) {
    std::cerr << "delta_core canonical test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta_core canonical tests passed\n";
  return 0;
}
