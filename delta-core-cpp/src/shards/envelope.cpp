#include <delta/shards/envelope.hpp>

#include <delta/core/canonical.hpp>
#include <delta/fixedpoint/checked.hpp>
#include <delta/fixedpoint/encoder.hpp>
#include <delta/fixedpoint/profile.hpp>
#include <delta/shards/plan.hpp>

#include <array>
#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace delta::shards {
namespace {

[[noreturn]] void reject(ErrorCode code, const char* message) {
  throw ShardError(code, message);
}

void append_u16(std::vector<std::byte>& target, std::uint16_t value) {
  target.push_back(static_cast<std::byte>(value & 0xffU));
  target.push_back(static_cast<std::byte>((value >> 8U) & 0xffU));
}

void append_u32(std::vector<std::byte>& target, std::uint32_t value) {
  for (unsigned shift = 0U; shift < 32U; shift += 8U) {
    target.push_back(static_cast<std::byte>((value >> shift) & 0xffU));
  }
}

void validate_header(const ShardHeader& header, bool require_payload_hash) {
  for (const auto* identifier : {
           &header.formal_semantics_id,
           &header.parameter_schema_id,
           &header.profile_id,
           &header.proof_instance_id,
           &header.round_config_id,
           &header.scale_table_id,
           &header.shard_plan_id,
       }) {
    if (!delta::fixedpoint::is_content_id(*identifier)) {
      reject(ErrorCode::context_mismatch, "header content identifier is invalid");
    }
  }
  if ((require_payload_hash && !delta::fixedpoint::is_content_id(header.payload_sha256)) ||
      !delta::fixedpoint::is_ascii_token(header.segment_id) ||
      !delta::fixedpoint::is_ascii_token(header.ticket_id) ||
      header.formal_semantics_id != delta::fixedpoint::formal_semantics_id() ||
      header.profile_id != delta::fixedpoint::fixed_profile_id() ||
      static_cast<std::size_t>(header.ordinal) >= delta::fixedpoint::max_shards ||
      header.element_count == 0U ||
      header.element_count > delta::fixedpoint::max_payload_bytes / 2U ||
      header.element_start > delta::fixedpoint::max_total_elements - header.element_count) {
    reject(ErrorCode::context_mismatch, "shard header context or range is invalid");
  }
}

[[nodiscard]] std::array<std::byte, 32> decode_content_id(std::string_view value) {
  if (!delta::fixedpoint::is_content_id(value)) {
    reject(ErrorCode::content_id_invalid, "Merkle leaf ID is invalid");
  }
  auto digit = [](char character) -> std::uint8_t {
    return character <= '9' ? static_cast<std::uint8_t>(character - '0')
                            : static_cast<std::uint8_t>(character - 'a' + 10);
  };
  std::array<std::byte, 32> result{};
  for (std::size_t index = 0; index < result.size(); ++index) {
    result[index] = static_cast<std::byte>(
        static_cast<std::uint8_t>((digit(value[7U + index * 2U]) << 4U) |
                                  digit(value[8U + index * 2U])));
  }
  return result;
}

}  // namespace

std::string canonical_header_json(const ShardHeader& header) {
  validate_header(header, true);
  return std::string{"{\"element_count\":"} + std::to_string(header.element_count) +
         ",\"element_start\":" + std::to_string(header.element_start) +
         ",\"formal_semantics_id\":\"" + header.formal_semantics_id + "\",\"ordinal\":" +
         std::to_string(header.ordinal) + ",\"parameter_schema_id\":\"" +
         header.parameter_schema_id + "\",\"payload_sha256\":\"" + header.payload_sha256 +
         "\",\"profile_id\":\"" + header.profile_id + "\",\"proof_instance_id\":\"" +
         header.proof_instance_id + "\",\"round_config_id\":\"" + header.round_config_id +
         "\",\"scale_table_id\":\"" + header.scale_table_id +
         "\",\"schema_version\":\"1.0.0\",\"segment_id\":\"" + header.segment_id +
         "\",\"segment_offset\":" + std::to_string(header.segment_offset) +
         ",\"shard_plan_id\":\"" + header.shard_plan_id + "\",\"ticket_id\":\"" +
         header.ticket_id + "\",\"type_name\":\"ENCODED_INT16_SHARD\"}";
}

EncodedShard write_shard(const ShardHeader& input, std::span<const std::int16_t> values) {
  validate_header(input, false);
  if (values.size() != static_cast<std::size_t>(input.element_count)) {
    reject(ErrorCode::payload_length_mismatch, "q count does not match shard header");
  }
  const auto payload = delta::fixedpoint::encode_q_payload(values);
  auto header = input;
  header.payload_sha256 = "sha256:" + delta::core::canonical::sha256_hex(payload);
  const auto header_json = canonical_header_json(header);
  if (header_json.size() > delta::fixedpoint::max_header_bytes) {
    reject(ErrorCode::header_too_large, "canonical shard header exceeds limit");
  }
  std::vector<std::byte> envelope;
  envelope.reserve(16U + header_json.size() + payload.size());
  for (const char character : std::string_view{"DRQ1"}) {
    envelope.push_back(static_cast<std::byte>(character));
  }
  append_u16(envelope, 1U);
  append_u16(envelope, 0U);
  append_u32(envelope, static_cast<std::uint32_t>(header_json.size()));
  append_u32(envelope, static_cast<std::uint32_t>(payload.size()));
  const auto header_bytes = std::as_bytes(std::span(header_json.data(), header_json.size()));
  envelope.insert(envelope.end(), header_bytes.begin(), header_bytes.end());
  envelope.insert(envelope.end(), payload.begin(), payload.end());
  const auto leaf =
      delta::fixedpoint::domain_content_id("deltareduce.004.shard-leaf.v1", envelope);
  return EncodedShard{std::move(header), std::move(envelope), leaf};
}

std::string merkle_root(std::span<const std::string> ordered_leaf_ids) {
  if (ordered_leaf_ids.empty()) {
    reject(ErrorCode::empty_shard_table, "Merkle tree cannot be empty");
  }
  std::vector<std::array<std::byte, 32>> nodes;
  nodes.reserve(ordered_leaf_ids.size());
  for (const auto& leaf : ordered_leaf_ids) {
    nodes.push_back(decode_content_id(leaf));
  }
  while (nodes.size() > 1U) {
    if (nodes.size() % 2U != 0U) {
      nodes.push_back(nodes.back());
    }
    std::vector<std::array<std::byte, 32>> next;
    next.reserve(nodes.size() / 2U);
    for (std::size_t index = 0; index < nodes.size(); index += 2U) {
      std::vector<std::byte> input;
      constexpr std::string_view domain = "deltareduce.004.merkle-node.v1";
      input.reserve(domain.size() + 1U + 64U);
      for (const char character : domain) {
        input.push_back(static_cast<std::byte>(character));
      }
      input.push_back(std::byte{0});
      input.insert(input.end(), nodes[index].begin(), nodes[index].end());
      input.insert(input.end(), nodes[index + 1U].begin(), nodes[index + 1U].end());
      const auto digest_hex = delta::core::canonical::sha256_hex(input);
      next.push_back(decode_content_id("sha256:" + digest_hex));
    }
    nodes = std::move(next);
  }
  std::string result = "sha256:";
  result.reserve(71U);
  const auto bytes = std::span(nodes.front());
  constexpr std::array<char, 16> alphabet = {
      '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'};
  for (const auto byte : bytes) {
    const auto value = std::to_integer<std::uint8_t>(byte);
    result.push_back(alphabet[value >> 4U]);
    result.push_back(alphabet[value & 0x0fU]);
  }
  return result;
}

}  // namespace delta::shards
