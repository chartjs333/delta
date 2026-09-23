#include <delta/core/canonical.hpp>
#include <delta/core/consensus.hpp>
#include <delta/core/protocol.hpp>
#include <delta/runtime/runtime.hpp>
#include <delta/runtime/vote_codec.hpp>

#include "../../delta-core-cpp/tests/vote_fixture.hpp"

#include <cstddef>
#include <cstdint>
#include <iostream>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>

namespace canonical = delta::core::canonical;
namespace consensus = delta::core::consensus;
namespace protocol = delta::core::protocol;
namespace runtime = delta::runtime;
namespace vote_fixture = delta::test::vote_fixture;

namespace {

[[nodiscard]] std::string hex(std::span<const std::byte> bytes) {
  constexpr std::string_view digits = "0123456789abcdef";
  std::string result;
  result.reserve(bytes.size() * 2U);
  for (const auto value : bytes) {
    const auto octet = std::to_integer<std::uint8_t>(value);
    result.push_back(digits[octet >> 4U]);
    result.push_back(digits[octet & 0x0fU]);
  }
  return result;
}

void require(bool condition, const char* message) {
  if (!condition) {
    throw std::runtime_error(message);
  }
}

template <typename Operation>
void require_invalid(Operation operation, const char* message) {
  try {
    operation();
  } catch (const std::invalid_argument&) {
    return;
  }
  throw std::runtime_error(message);
}

}  // namespace

int main() {
  try {
    const auto fixture = vote_fixture::full(consensus::VoteAction::round_config);
    const auto state = protocol::encode(fixture.state);
    const auto policy = runtime::encode_vote_policy_v1(fixture.policy);
    const auto vote = protocol::encode(fixture.vote);
    const auto vote_id =
        canonical::content_id(canonical::Type::vote, vote);
    const runtime::VoteReceipt receipt{
        vote,
        vote_id,
        1U,
        fixture.candidate.action,
        std::string(consensus::vote_formal_action_id(fixture.candidate.action)),
        fixture.candidate.context_id,
        fixture.candidate.parents,
        false,
    };
    const auto receipt_bytes = runtime::encode_vote_receipt_v1(receipt);

    require(
        runtime::encode_vote_policy_v1(runtime::parse_vote_policy_v1(policy)) ==
            policy,
        "vote policy codec is not canonically idempotent");
    require(protocol::encode(protocol::parse_vote(vote)) == vote,
            "vote protocol codec is not canonically idempotent");
    const auto decoded_receipt = runtime::parse_vote_receipt_v1(receipt_bytes);
    require(
        decoded_receipt.frame == vote && decoded_receipt.vote_id == vote_id &&
            decoded_receipt.context_id == fixture.candidate.context_id &&
            !decoded_receipt.replay,
        "native vote receipt fixture does not round-trip");

    auto wrong_id = receipt;
    wrong_id.vote_id = vote_fixture::id('0');
    require_invalid(
        [&] { static_cast<void>(runtime::encode_vote_receipt_v1(wrong_id)); },
        "receipt encoder accepted an ID that does not identify its vote frame");
    auto wrong_sequence = receipt;
    ++wrong_sequence.journal_sequence;
    require_invalid(
        [&] { static_cast<void>(runtime::encode_vote_receipt_v1(wrong_sequence)); },
        "receipt encoder accepted a sequence that differs from its vote frame");
    auto wrong_action = receipt;
    wrong_action.action = consensus::VoteAction::input_set;
    wrong_action.formal_action_id =
        consensus::vote_formal_action_id(wrong_action.action);
    require_invalid(
        [&] { static_cast<void>(runtime::encode_vote_receipt_v1(wrong_action)); },
        "receipt encoder accepted an action that differs from its vote frame");
    auto wrong_context = receipt;
    wrong_context.context_id += "-different";
    require_invalid(
        [&] { static_cast<void>(runtime::encode_vote_receipt_v1(wrong_context)); },
        "receipt encoder accepted a context that differs from its vote frame");

    auto mutated_receipt = receipt_bytes;
    constexpr std::size_t action_last_byte = 19U;
    constexpr std::size_t sequence_last_byte = 31U;
    constexpr std::size_t first_section = 32U;
    constexpr std::size_t length_bytes = 4U;
    mutated_receipt[action_last_byte] = std::byte{2U};
    require_invalid(
        [&] { static_cast<void>(runtime::parse_vote_receipt_v1(mutated_receipt)); },
        "receipt parser accepted an action that differs from its vote frame");
    mutated_receipt = receipt_bytes;
    mutated_receipt[sequence_last_byte] = std::byte{2U};
    require_invalid(
        [&] { static_cast<void>(runtime::parse_vote_receipt_v1(mutated_receipt)); },
        "receipt parser accepted a sequence that differs from its vote frame");
    mutated_receipt = receipt_bytes;
    const auto vote_id_offset = first_section + length_bytes + vote.size() + length_bytes;
    mutated_receipt[vote_id_offset + 7U] ^= std::byte{1U};
    require_invalid(
        [&] { static_cast<void>(runtime::parse_vote_receipt_v1(mutated_receipt)); },
        "receipt parser accepted an ID that does not identify its vote frame");
    mutated_receipt = receipt_bytes;
    const auto context_offset = vote_id_offset + vote_id.size() + length_bytes;
    mutated_receipt[context_offset] ^= std::byte{1U};
    require_invalid(
        [&] { static_cast<void>(runtime::parse_vote_receipt_v1(mutated_receipt)); },
        "receipt parser accepted a context that differs from its vote frame");

    std::cout << "{\"expected_receipt_hex\":\"" << hex(receipt_bytes)
              << "\",\"formal_semantics_id\":\""
              << delta::certificates::formal_semantics_id
              << "\",\"initial_state_hex\":\"" << hex(state)
              << "\",\"schema_version\":\"1.0.0\",\"type_name\":\""
                 "DELTA_RECORD_VOTE_V1_FIXTURE\",\"vote_hex\":\""
              << hex(vote) << "\",\"vote_policy_hex\":\"" << hex(policy)
              << "\"}\n";
  } catch (const std::exception& error) {
    std::cerr << "vote fixture exporter failed: " << error.what() << '\n';
    return 1;
  }
  return 0;
}
