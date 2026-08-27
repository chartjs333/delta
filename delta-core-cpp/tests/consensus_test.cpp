#include <delta/core/canonical.hpp>
#include <delta/core/consensus.hpp>
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
#include <vector>

namespace canonical = delta::core::canonical;
namespace consensus = delta::core::consensus;
namespace protocol = delta::core::protocol;

namespace {

[[noreturn]] void fail(std::string message) { throw std::runtime_error(std::move(message)); }

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

template <typename Operation>
void expect_consensus_error(consensus::ErrorCode expected, Operation operation) {
  try {
    operation();
  } catch (const consensus::ConsensusError& error) {
    expect(error.code() == expected, "unexpected stable consensus error code");
    return;
  }
  fail("invalid consensus input was accepted");
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

[[nodiscard]] std::string content_id(char digit) {
  return "sha256:" + std::string(64U, digit);
}

void test_durable_vote_uniqueness() {
  auto vote = protocol::parse_vote(golden(3U));
  consensus::VoteJournal journal;
  expect(
      journal.record(vote) == consensus::Disposition::recorded,
      "first durable vote was not recorded");
  expect(
      journal.record(vote) == consensus::Disposition::replay,
      "exact durable vote replay was not idempotent");

  auto conflicting = vote;
  conflicting.body_hash = content_id('b');
  expect_consensus_error(consensus::ErrorCode::conflicting_vote, [&journal, &conflicting] {
    static_cast<void>(journal.record(conflicting));
  });
  expect(journal.votes().size() == 1U, "conflicting vote changed durable journal");

  auto next_view = vote;
  next_view.view = 1U;
  next_view.context_id = "ROUND_CONFIG:round-003-fixture:1:1";
  next_view.durable_sequence = 2U;
  expect(
      journal.record(next_view) == consensus::Disposition::recorded,
      "distinct vote context was rejected");
}

consensus::QuorumPolicy f1_policy() {
  return consensus::QuorumPolicy{
      content_id('d'),
      {"validator-1", "validator-2", "validator-3", "validator-4"},
      3U,
  };
}

void test_exact_quorum_policy() {
  auto certificate = protocol::parse_quorum_certificate(golden(4U));
  const auto policy = f1_policy();
  consensus::validate_quorum(certificate, policy);

  auto unknown = certificate;
  unknown.signer_ids.back() = "validator-9";
  expect_consensus_error(consensus::ErrorCode::unknown_signer, [&unknown, &policy] {
    consensus::validate_quorum(unknown, policy);
  });

  auto wrong_threshold = policy;
  wrong_threshold.quorum_threshold = 2U;
  expect_consensus_error(
      consensus::ErrorCode::quorum_policy_mismatch, [&certificate, &wrong_threshold] {
        consensus::validate_quorum(certificate, wrong_threshold);
      });

  auto malformed = policy;
  malformed.validator_ids.pop_back();
  expect_consensus_error(consensus::ErrorCode::validator_set_invalid, [&certificate, &malformed] {
    consensus::validate_quorum(certificate, malformed);
  });
}

consensus::AvailabilityProof availability(
    std::string ticket_id,
    std::string commitment_id,
    char certificate_digit) {
  return consensus::AvailabilityProof{
      std::move(ticket_id),
      std::move(commitment_id),
      content_id(certificate_digit),
      {content_id('1'), content_id('2')},
      {"storage-1", "storage-2", "storage-3"},
      3U,
  };
}

void test_commitment_availability_and_freeze() {
  consensus::InputLedger ledger({"ticket-a", "ticket-b", "ticket-c"});
  const consensus::Commitment ticket_b{"ticket-b", content_id('b')};
  const consensus::Commitment ticket_a{"ticket-a", content_id('a')};
  expect(
      ledger.record_commitment(ticket_b) == consensus::Disposition::recorded,
      "ticket-b commitment rejected");
  expect(
      ledger.record_commitment(ticket_a) == consensus::Disposition::recorded,
      "ticket-a commitment rejected");
  expect(
      ledger.commitments().front().ticket_id == "ticket-a",
      "commitments are not stored in canonical ticket order");
  expect(
      ledger.record_commitment(ticket_a) == consensus::Disposition::replay,
      "exact commitment replay was not idempotent");

  auto conflicting = ticket_a;
  conflicting.commitment_id = content_id('c');
  expect_consensus_error(consensus::ErrorCode::commitment_equivocation, [&ledger, &conflicting] {
    static_cast<void>(ledger.record_commitment(conflicting));
  });
  const consensus::Commitment unknown{"ticket-z", content_id('f')};
  expect_consensus_error(consensus::ErrorCode::unknown_ticket, [&ledger, &unknown] {
    static_cast<void>(ledger.record_commitment(unknown));
  });

  const std::vector<std::string> leaves{content_id('1'), content_id('2')};
  const std::vector<std::string> attesters{"storage-1", "storage-2", "storage-3", "storage-4"};
  auto proof_a = availability("ticket-a", ticket_a.commitment_id, '3');
  expect(
      ledger.record_availability(proof_a, leaves, attesters, 3U) ==
          consensus::Disposition::recorded,
      "valid availability proof rejected");
  expect(
      ledger.record_availability(proof_a, leaves, attesters, 3U) ==
          consensus::Disposition::replay,
      "availability replay was not idempotent");

  const auto frozen = ledger.freeze();
  expect(frozen.size() == 1U && frozen.front().ticket_id == "ticket-a", "frozen input mismatch");
  expect(ledger.freeze() == frozen, "input freeze replay changed the frozen set");

  const consensus::Commitment late{"ticket-c", content_id('c')};
  expect(
      ledger.record_commitment(late) == consensus::Disposition::late,
      "late commitment was not classified as late");
  expect(ledger.late_commitment_count() == 1U, "late commitment evidence was not retained");

  auto proof_b = availability("ticket-b", ticket_b.commitment_id, '4');
  expect(
      ledger.record_availability(proof_b, leaves, attesters, 3U) ==
          consensus::Disposition::late,
      "late availability was not classified as late");
  expect(ledger.late_availability_count() == 1U, "late availability evidence was not retained");
  expect(ledger.frozen_inputs() == frozen, "late evidence changed frozen inputs");
}

void test_availability_fails_closed() {
  consensus::InputLedger ledger({"ticket-a"});
  const consensus::Commitment commitment{"ticket-a", content_id('a')};
  static_cast<void>(ledger.record_commitment(commitment));
  const std::vector<std::string> leaves{content_id('1'), content_id('2')};
  const std::vector<std::string> attesters{"storage-1", "storage-2", "storage-3"};

  auto incomplete = availability("ticket-a", commitment.commitment_id, '3');
  incomplete.covered_leaf_ids.pop_back();
  expect_consensus_error(
      consensus::ErrorCode::availability_coverage_incomplete,
      [&ledger, &incomplete, &leaves, &attesters] {
        static_cast<void>(ledger.record_availability(incomplete, leaves, attesters, 3U));
      });

  auto insufficient = availability("ticket-a", commitment.commitment_id, '3');
  insufficient.attester_ids.pop_back();
  expect_consensus_error(
      consensus::ErrorCode::availability_attesters_invalid,
      [&ledger, &insufficient, &leaves, &attesters] {
        static_cast<void>(ledger.record_availability(insufficient, leaves, attesters, 3U));
      });

  auto wrong_threshold = availability("ticket-a", commitment.commitment_id, '3');
  wrong_threshold.threshold = 1U;
  expect_consensus_error(
      consensus::ErrorCode::availability_attesters_invalid,
      [&ledger, &wrong_threshold, &leaves, &attesters] {
        static_cast<void>(ledger.record_availability(wrong_threshold, leaves, attesters, 3U));
      });

  auto wrong_parent = availability("ticket-a", content_id('b'), '3');
  expect_consensus_error(
      consensus::ErrorCode::availability_commitment_mismatch,
      [&ledger, &wrong_parent, &leaves, &attesters] {
        static_cast<void>(ledger.record_availability(wrong_parent, leaves, attesters, 3U));
      });

  consensus::InputLedger empty({"ticket-a"});
  expect_consensus_error(consensus::ErrorCode::input_set_empty, [&empty] {
    static_cast<void>(empty.freeze());
  });
}

}  // namespace

int main() {
  try {
    test_durable_vote_uniqueness();
    test_exact_quorum_policy();
    test_commitment_availability_and_freeze();
    test_availability_fails_closed();
  } catch (const std::exception& error) {
    std::cerr << "delta_core consensus test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta_core consensus tests passed\n";
  return 0;
}
