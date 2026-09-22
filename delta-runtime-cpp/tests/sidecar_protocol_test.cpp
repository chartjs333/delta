#include <delta/runtime/sidecar_protocol.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace sidecar = delta::runtime::sidecar;

namespace {

[[noreturn]] void fail(std::string message) { throw std::runtime_error(std::move(message)); }

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

template <typename Operation>
void expect_rejected(Operation operation, std::string_view message) {
  try {
    operation();
  } catch (const std::invalid_argument&) {
    return;
  }
  fail(std::string(message));
}

[[nodiscard]] sidecar::Id128 id(std::uint8_t seed) {
  sidecar::Id128 result{};
  for (std::size_t index = 0U; index < result.size(); ++index) {
    result[index] = static_cast<std::byte>(seed + static_cast<std::uint8_t>(index));
  }
  return result;
}

[[nodiscard]] sidecar::Frame health_request() {
  std::vector<sidecar::Field> operation{sidecar::field_id128(16U, {})};
  const auto digest = sidecar::request_digest(sidecar::MessageType::health_request, operation);
  const std::vector<sidecar::Field> fields{
      sidecar::field_bytes(1U, std::as_bytes(std::span("health-1", 8U))),
      sidecar::field_digest(2U, digest),
      operation.front(),
  };
  return sidecar::Frame{
      sidecar::MessageType::health_request,
      sidecar::required_flags(sidecar::MessageType::health_request),
      id(1U),
      7U,
      id(33U),
      1U,
      sidecar::max_response_capacity,
      sidecar::encode_payload(sidecar::MessageType::health_request, fields),
  };
}

void test_round_trip_and_request_digest() {
  const auto frame = health_request();
  const auto encoded = sidecar::encode_frame(frame);
  expect(encoded.size() == sidecar::header_bytes + frame.payload.size(), "frame size differs");
  expect(sidecar::decode_frame(encoded) == frame, "frame round trip differs");
  const auto payload = sidecar::decode_payload(frame.payload);
  expect(payload.type == frame.type && payload.fields.size() == 3U, "payload round trip differs");

  auto changed_common = payload.fields;
  changed_common[0] = sidecar::field_bytes(1U, std::as_bytes(std::span("health-2", 8U)));
  expect(
      sidecar::request_digest(frame.type, changed_common) ==
          sidecar::field_as_digest(payload.fields[1]),
      "request digest improperly included response echo fields");
  auto changed_operation = payload.fields;
  changed_operation[2] = sidecar::field_id128(16U, id(99U));
  expect(
      sidecar::request_digest(frame.type, changed_operation) !=
          sidecar::field_as_digest(payload.fields[1]),
      "request digest omitted operation fields");
}

void test_frame_mutations() {
  const auto good = sidecar::encode_frame(health_request());
  const auto rejected_byte = [&good](std::size_t offset, std::byte mask) {
    auto changed = good;
    changed[offset] ^= mask;
    expect_rejected([&changed] { static_cast<void>(sidecar::decode_frame(changed)); },
                    "mutated frame was accepted");
  };
  for (const auto offset : {0U, 8U, 12U, 14U, 16U, 68U, 76U, 84U, 116U}) {
    rejected_byte(offset, std::byte{1});
  }
  for (const auto offset : {36U, 60U}) {
    auto zero = good;
    std::fill_n(zero.begin() + static_cast<std::ptrdiff_t>(offset), 8U, std::byte{0});
    expect_rejected([&zero] { static_cast<void>(sidecar::decode_frame(zero)); },
                    "zero generation or sequence was accepted");
  }
  auto trailing = good;
  trailing.push_back(std::byte{0});
  expect_rejected([&trailing] { static_cast<void>(sidecar::decode_frame(trailing)); },
                  "trailing frame byte was accepted");
  auto truncated = good;
  truncated.pop_back();
  expect_rejected([&truncated] { static_cast<void>(sidecar::decode_frame(truncated)); },
                  "truncated frame was accepted");
}

void test_payload_mutations() {
  const auto frame = health_request();
  const auto rejected_byte = [&frame](std::size_t offset, std::byte mask) {
    auto changed = frame.payload;
    changed[offset] ^= mask;
    expect_rejected([&changed] { static_cast<void>(sidecar::decode_payload(changed)); },
                    "mutated payload was accepted");
  };
  for (const auto offset : {0U, 2U, 4U, 6U, 8U, 19U, 20U}) {
    rejected_byte(offset, std::byte{1});
  }
  auto unknown_wire = frame.payload;
  unknown_wire[18U] = std::byte{0};
  expect_rejected([&unknown_wire] { static_cast<void>(sidecar::decode_payload(unknown_wire)); },
                  "unknown TLV wire type was accepted");
  auto trailing = frame.payload;
  trailing.push_back(std::byte{0});
  expect_rejected([&trailing] { static_cast<void>(sidecar::decode_payload(trailing)); },
                  "trailing payload byte was accepted");
  std::vector<sidecar::Field> duplicates{
      sidecar::field_u8(1U, 1U),
      sidecar::field_u8(1U, 2U),
  };
  expect_rejected([&duplicates] { static_cast<void>(sidecar::encode_fields(duplicates)); },
                  "duplicate TLV field was accepted");
}

void test_text_and_scalar_contracts() {
  const std::string precomposed = "caf\xc3\xa9";
  const auto text = sidecar::field_text(1U, precomposed);
  expect(sidecar::field_as_text(text) == precomposed, "valid UTF-8 changed");
  const std::string decomposed = "cafe\xcc\x81";
  expect_rejected([&decomposed] { static_cast<void>(sidecar::field_text(1U, decomposed)); },
                  "decomposed UTF-8 was accepted");
  const std::string angstrom_sign = "\xe2\x84\xab";
  expect_rejected([&angstrom_sign] { static_cast<void>(sidecar::field_text(1U, angstrom_sign)); },
                  "canonically decomposable scalar was accepted");
  const std::string composed_angstrom = "\xc3\x85";
  expect(sidecar::field_as_text(sidecar::field_text(1U, composed_angstrom)) == composed_angstrom,
         "valid composed Unicode changed");
  const std::string decomposed_hangul = "\xe1\x84\x80\xe1\x85\xa1";
  expect_rejected(
      [&decomposed_hangul] { static_cast<void>(sidecar::field_text(1U, decomposed_hangul)); },
      "decomposed Hangul was accepted");
  const std::string nul{"a\0b", 3U};
  expect_rejected([&nul] { static_cast<void>(sidecar::field_text(1U, nul)); },
                  "NUL text was accepted");
  const std::string overlong{"\xc0\x80", 2U};
  expect_rejected([&overlong] { static_cast<void>(sidecar::field_text(1U, overlong)); },
                  "overlong UTF-8 was accepted");

  expect(sidecar::field_as_u8(sidecar::field_u8(1U, 0xffU)) == 0xffU, "u8 differs");
  expect(sidecar::field_as_u16(sidecar::field_u16(1U, 0xabcdU)) == 0xabcdU, "u16 differs");
  expect(sidecar::field_as_u32(sidecar::field_u32(1U, 0x89abcdefU)) == 0x89abcdefU,
         "u32 differs");
  expect(sidecar::field_as_u64(sidecar::field_u64(1U, UINT64_C(0x0123456789abcdef))) ==
             UINT64_C(0x0123456789abcdef),
         "u64 differs");
}

void test_identity_and_bounds() {
  const auto empty_hash = sidecar::digest_identity(sidecar::sha256(sidecar::Bytes{}));
  expect(
      empty_hash == "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "SHA-256 empty vector differs");
  expect(sidecar::digest_identity(sidecar::digest_from_identity(empty_hash)) == empty_hash,
         "digest identity round trip differs");
  expect_rejected(
      [] { static_cast<void>(sidecar::digest_from_identity("sha256:ABC")); },
      "invalid digest identity was accepted");

  auto bad_flags = health_request();
  bad_flags.flags = sidecar::flag_payload_shared_memory | sidecar::flag_response_expected |
                    sidecar::flag_read_only;
  expect_rejected([&bad_flags] { static_cast<void>(sidecar::encode_frame(bad_flags)); },
                  "disabled shared-memory carrier was accepted");
  auto bad_capacity = health_request();
  --bad_capacity.response_capacity;
  expect_rejected([&bad_capacity] { static_cast<void>(sidecar::encode_frame(bad_capacity)); },
                  "lowered response capacity was accepted");
}

}  // namespace

int main() {
  try {
    test_round_trip_and_request_digest();
    test_frame_mutations();
    test_payload_mutations();
    test_text_and_scalar_contracts();
    test_identity_and_bounds();
  } catch (const std::exception& error) {
    std::cerr << "sidecar protocol test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "sidecar protocol tests passed\n";
  return 0;
}
