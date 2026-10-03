#pragma once

#include <delta/core/canonical.hpp>
#include <delta/core/consensus.hpp>
#include <delta/runtime/runtime.hpp>

#include <cstddef>
#include <cstdint>
#include <span>
#include <string>

namespace delta::runtime {

inline constexpr std::size_t max_vote_policy_v1_bytes = 4U * 1024U * 1024U;
inline constexpr std::size_t max_vote_policy_v1_text_bytes = 4U * 1024U;
// The isolated transport freezes 16 MiB of operation-result bytes plus 8 KiB
// of response-schema metadata. Keeping the complete opaque receipt at or below
// 16 MiB makes every accepted embedded receipt transportable under the same
// 16,785,408-byte logical-payload ceiling.
inline constexpr std::size_t vote_transport_metadata_v1_bytes = 8U * 1024U;
inline constexpr std::size_t max_vote_receipt_v1_bytes = 16U * 1024U * 1024U;
inline constexpr std::size_t max_vote_frame_v1_bytes =
    max_vote_receipt_v1_bytes - vote_transport_metadata_v1_bytes;
inline constexpr std::size_t max_vote_response_logical_v1_bytes =
    max_vote_receipt_v1_bytes + vote_transport_metadata_v1_bytes;
static_assert(max_vote_response_logical_v1_bytes == 16'785'408U);

struct DecodedVoteReceiptV1 {
  core::canonical::Bytes frame;
  std::string vote_id;
  std::uint64_t journal_sequence;
  core::consensus::VoteAction action;
  std::string formal_action_id;
  std::string context_id;
  bool replay;

  bool operator==(const DecodedVoteReceiptV1&) const = default;
};

// These operational codecs are shared by the embedded C ABI and isolated
// sidecar. They do not add protocol types: Java transports the resulting bytes
// opaquely. Native code alone decodes and validates the startup round-contract
// projection, retains it by value for the handle lifetime, resolves every
// per-vote binding, and authors the durable receipt.
[[nodiscard]] core::canonical::Bytes encode_vote_policy_v1(
    const core::consensus::VoteAdmissionPolicy& policy);
[[nodiscard]] core::consensus::VoteAdmissionPolicy parse_vote_policy_v1(
    std::span<const std::byte> encoded);

[[nodiscard]] std::size_t vote_receipt_v1_encoded_size(
    std::size_t frame_size,
    std::string_view vote_id,
    std::string_view context_id);
[[nodiscard]] core::canonical::Bytes encode_vote_receipt_v1(const VoteReceipt& receipt);
[[nodiscard]] DecodedVoteReceiptV1 parse_vote_receipt_v1(
    std::span<const std::byte> encoded);

}  // namespace delta::runtime
