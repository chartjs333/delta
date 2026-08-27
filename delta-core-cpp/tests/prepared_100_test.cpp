#include <delta/core/arithmetic.hpp>
#include <delta/core/canonical.hpp>
#include <delta/core/consensus.hpp>
#include <delta/core/protocol.hpp>
#include <delta/core/transition.hpp>

#include <algorithm>
#include <array>
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
#include <vector>

namespace arithmetic = delta::core::arithmetic;
namespace canonical = delta::core::canonical;
namespace consensus = delta::core::consensus;
namespace protocol = delta::core::protocol;
namespace transition = delta::core::transition;

namespace {

struct PreparedRecord {
  protocol::PreparedIntegerShard shard;
  canonical::Bytes bytes;
  std::string commitment_id;
  std::string availability_id;
};

struct FixtureResult {
  std::array<arithmetic::Int128, 4> sums;
  std::string prepared_transcript_sha256;
  std::string frozen_transcript_sha256;
  std::string eligible_state_id;
  canonical::Bytes eligible_state_bytes;

  bool operator==(const FixtureResult&) const = default;
};

[[noreturn]] void fail(std::string message) { throw std::runtime_error(std::move(message)); }

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

[[nodiscard]] std::string load(std::string_view path) {
  std::ifstream input(std::string(path), std::ios::binary);
  expect(input.good(), "cannot open prepared-100 fixture");
  return {std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
}

[[nodiscard]] std::string field(const std::string& document, std::string_view name) {
  const std::regex pattern("\\\"" + std::string(name) + "\\\":\\\"([^\\\"]+)\\\"");
  std::smatch match;
  expect(std::regex_search(document, match, pattern), "required prepared-100 field is missing");
  return match[1].str();
}

[[nodiscard]] std::uint32_t unsigned_field(
    const std::string& document,
    std::string_view name) {
  const std::regex pattern("\\\"" + std::string(name) + "\\\":([0-9]+)");
  std::smatch match;
  expect(std::regex_search(document, match, pattern), "required unsigned field is missing");
  return static_cast<std::uint32_t>(std::stoul(match[1].str()));
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
  const auto document = load(DELTA_GOLDEN_FIXTURE_PATH);
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

[[nodiscard]] std::string ticket_id(std::uint32_t index) {
  expect(index < 100U, "prepared fixture ticket index out of range");
  std::string result = "ticket-000";
  result[7] = static_cast<char>('0' + (index / 100U));
  result[8] = static_cast<char>('0' + ((index / 10U) % 10U));
  result[9] = static_cast<char>('0' + (index % 10U));
  return result;
}

[[nodiscard]] canonical::Bytes ascii_bytes(std::string_view value) {
  canonical::Bytes result;
  result.reserve(value.size());
  for (const unsigned char byte : value) {
    result.push_back(static_cast<std::byte>(byte));
  }
  return result;
}

void append_u32(canonical::Bytes& output, std::size_t value) {
  expect(value <= UINT32_MAX, "fixture record too large");
  const auto bounded = static_cast<std::uint32_t>(value);
  output.push_back(static_cast<std::byte>((bounded >> 24U) & 0xffU));
  output.push_back(static_cast<std::byte>((bounded >> 16U) & 0xffU));
  output.push_back(static_cast<std::byte>((bounded >> 8U) & 0xffU));
  output.push_back(static_cast<std::byte>(bounded & 0xffU));
}

void append_framed(canonical::Bytes& output, std::span<const std::byte> value) {
  append_u32(output, value.size());
  output.insert(output.end(), value.begin(), value.end());
}

[[nodiscard]] std::string derived_id(std::string_view domain, std::string_view value) {
  auto bytes = ascii_bytes(domain);
  const auto suffix = ascii_bytes(value);
  bytes.insert(bytes.end(), suffix.begin(), suffix.end());
  return "sha256:" + canonical::sha256_hex(bytes);
}

[[nodiscard]] protocol::PreparedIntegerShard make_shard(
    std::uint32_t index,
    const std::string& fixture) {
  const auto signed_index = static_cast<std::int64_t>(index);
  return protocol::PreparedIntegerShard{
      static_cast<std::int64_t>(index % 5U) - 2,
      derived_id("leaf:", ticket_id(index)),
      {128U, "BIG_ENDIAN", field(fixture, "integer_profile_id"), 64U},
      field(fixture, "parameter_id"),
      field(fixture, "round_id"),
      field(fixture, "shard_id"),
      ticket_id(index),
      {
          signed_index - 50,
          (2 * signed_index) - 99,
          (index % 2U) == 0U ? signed_index + 1 : -(signed_index + 1),
          1,
      },
  };
}

[[nodiscard]] std::vector<PreparedRecord> make_records(const std::string& fixture) {
  const auto count = unsigned_field(fixture, "ticket_count");
  expect(count == 100U, "prepared fixture must contain exactly 100 tickets");
  expect(unsigned_field(fixture, "value_count") == 4U, "prepared fixture value width changed");
  expect(
      field(fixture, "formula_id") == "prepared-100-linear-alternating-v1",
      "prepared fixture formula changed");
  expect(field(fixture, "ticket_id_pattern") == "ticket-%03u", "ticket pattern changed");

  std::vector<PreparedRecord> records;
  records.reserve(count);
  for (std::uint32_t index = 0; index < count; ++index) {
    auto shard = make_shard(index, fixture);
    auto bytes = protocol::encode(shard);
    expect(protocol::parse_prepared_integer_shard(bytes) == shard, "prepared shard roundtrip failed");
    const auto commitment = canonical::content_id(canonical::Type::prepared_integer_shard, bytes);
    records.push_back(PreparedRecord{
        std::move(shard),
        std::move(bytes),
        commitment,
        derived_id("availability:", ticket_id(index)),
    });
  }
  return records;
}

[[nodiscard]] transition::TransitionResult apply_command(
    const protocol::RoundState& state,
    std::string kind,
    std::string request_id,
    std::string body_hash) {
  const protocol::Command command{
      "validator-1",
      std::move(body_hash),
      std::move(kind),
      state.height,
      10U,
      std::move(request_id),
      state.round_id,
      state.view,
  };
  return transition::apply(protocol::encode(state), protocol::encode(command));
}

[[nodiscard]] FixtureResult run_fixture(const std::string& fixture, bool reverse_arrival) {
  auto records = make_records(fixture);
  std::vector<std::string> permitted;
  permitted.reserve(records.size());
  for (const auto& record : records) {
    permitted.push_back(record.shard.ticket_id);
  }
  consensus::InputLedger ledger(permitted);
  if (reverse_arrival) {
    std::reverse(records.begin(), records.end());
  }

  const std::vector<std::string> attesters{"storage-1", "storage-2", "storage-3", "storage-4"};
  for (const auto& record : records) {
    expect(
        ledger.record_commitment({record.shard.ticket_id, record.commitment_id}) ==
            consensus::Disposition::recorded,
        "prepared commitment was not recorded");
    const consensus::AvailabilityProof proof{
        record.shard.ticket_id,
        record.commitment_id,
        record.availability_id,
        {record.shard.input_leaf_id},
        {"storage-1", "storage-2", "storage-3"},
        3U,
    };
    expect(
        ledger.record_availability(
            proof,
            {record.shard.input_leaf_id},
            attesters,
            unsigned_field(fixture, "availability_threshold")) == consensus::Disposition::recorded,
        "prepared availability was not recorded");
  }
  const auto frozen = ledger.freeze();
  expect(frozen.size() == 100U, "frozen prepared input set is incomplete");

  std::sort(records.begin(), records.end(), [](const PreparedRecord& left, const PreparedRecord& right) {
    return left.shard.ticket_id < right.shard.ticket_id;
  });
  std::array<arithmetic::Int128, 4> sums{};
  canonical::Bytes prepared_transcript;
  for (const auto& record : records) {
    append_framed(prepared_transcript, record.bytes);
    for (std::size_t index = 0; index < sums.size(); ++index) {
      const auto term = arithmetic::checked_multiply(
          arithmetic::Int128::from_i64(record.shard.coefficient),
          arithmetic::Int128::from_i64(record.shard.values[index]));
      sums[index] = arithmetic::checked_add(sums[index], term);
    }
  }

  canonical::Bytes frozen_transcript;
  for (const auto& input : frozen) {
    append_framed(frozen_transcript, ascii_bytes(input.ticket_id));
    append_framed(frozen_transcript, ascii_bytes(input.commitment_id));
    append_framed(frozen_transcript, ascii_bytes(input.availability_certificate_id));
  }

  auto state = protocol::parse_round_state(golden(5U));
  for (const auto& record : records) {
    state = apply_command(
                state,
                "ACCEPT_COMMITMENT",
                "request-commit-" + record.shard.ticket_id,
                record.commitment_id)
                .next_state;
  }
  for (const auto& record : records) {
    state = apply_command(
                state,
                "ACCEPT_AVAILABILITY",
                "request-availability-" + record.shard.ticket_id,
                record.availability_id)
                .next_state;
  }
  const auto final = apply_command(
      state,
      "FINALIZE_INPUT_FREEZE",
      "request-freeze-100",
      "sha256:" + canonical::sha256_hex(frozen_transcript));
  expect(
      final.next_state.phase == protocol::RoundPhase::eligible &&
          final.next_state.committed_ticket_count == 100U &&
          final.next_state.available_ticket_count == 100U,
      "100-ticket lifecycle did not reach the exact eligible state");
  return FixtureResult{
      sums,
      canonical::sha256_hex(prepared_transcript),
      canonical::sha256_hex(frozen_transcript),
      final.next_state_id,
      final.next_state_bytes,
  };
}

[[nodiscard]] std::uint64_t expected_limb(
    const std::string& fixture,
    std::size_t index,
    std::string_view limb) {
  return std::stoull(field(fixture, "expected_sum_" + std::to_string(index) + "_" + std::string(limb)));
}

void test_exact_100_ticket_repeatability() {
  const auto fixture = load(DELTA_PREPARED_100_FIXTURE_PATH);
  expect(field(fixture, "formal_semantics_id") == protocol::formal_semantics_id, "formal ID mismatch");
  const auto forward = run_fixture(fixture, false);
  const auto reverse = run_fixture(fixture, true);
  expect(forward == reverse, "arrival order changed exact prepared-100 result");
  for (std::size_t index = 0; index < forward.sums.size(); ++index) {
    expect(
        forward.sums[index] == arithmetic::Int128::from_bits(
                                   expected_limb(fixture, index, "high"),
                                   expected_limb(fixture, index, "low")),
        "prepared-100 exact aggregate mismatch");
  }
  expect(
      forward.prepared_transcript_sha256 == field(fixture, "expected_prepared_transcript_sha256"),
      "prepared transcript hash mismatch");
  expect(
      forward.frozen_transcript_sha256 ==
          field(fixture, "expected_frozen_input_transcript_sha256"),
      "frozen input transcript hash mismatch");
  expect(
      forward.eligible_state_id == field(fixture, "expected_eligible_state_id"),
      "eligible state ID mismatch");
}

}  // namespace

int main() {
  try {
    test_exact_100_ticket_repeatability();
  } catch (const std::exception& error) {
    std::cerr << "delta_core prepared-100 test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta_core prepared-100 tests passed\n";
  return 0;
}
