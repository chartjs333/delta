#include <delta/shards/reader.hpp>

#include <delta/core/canonical.hpp>
#include <delta/fixedpoint/checked.hpp>
#include <delta/fixedpoint/profile.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <ranges>
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

[[nodiscard]] std::uint16_t read_u16(std::span<const std::byte> bytes, std::size_t offset) {
  return static_cast<std::uint16_t>(std::to_integer<std::uint8_t>(bytes[offset])) |
         static_cast<std::uint16_t>(
             static_cast<std::uint16_t>(std::to_integer<std::uint8_t>(bytes[offset + 1U])) << 8U);
}

[[nodiscard]] std::uint32_t read_u32(std::span<const std::byte> bytes, std::size_t offset) {
  std::uint32_t result = 0U;
  for (unsigned index = 0U; index < 4U; ++index) {
    result |= static_cast<std::uint32_t>(std::to_integer<std::uint8_t>(bytes[offset + index]))
              << (index * 8U);
  }
  return result;
}

struct EnvelopeView {
  std::span<const std::byte> header;
  std::span<const std::byte> payload;
};

[[nodiscard]] bool lowercase_hex(char value) noexcept {
  return (value >= '0' && value <= '9') || (value >= 'a' && value <= 'f');
}

[[nodiscard]] EnvelopeView validate_opaque(std::span<const std::byte> envelope) {
  if (envelope.size() < 16U) {
    reject(ErrorCode::truncated, "shard prefix is truncated");
  }
  if (std::to_integer<char>(envelope[0]) != 'D' || std::to_integer<char>(envelope[1]) != 'R' ||
      std::to_integer<char>(envelope[2]) != 'Q' || std::to_integer<char>(envelope[3]) != '1') {
    reject(ErrorCode::bad_magic, "shard magic is invalid");
  }
  if (read_u16(envelope, 4U) != 1U || read_u16(envelope, 6U) != 0U) {
    reject(ErrorCode::unsupported_version, "shard version is unsupported");
  }
  const auto header_length = static_cast<std::size_t>(read_u32(envelope, 8U));
  const auto payload_length = static_cast<std::size_t>(read_u32(envelope, 12U));
#if !defined(DELTA_FIXEDPOINT_MUTANT_UNBOUNDED_HEADER)
  if (header_length > delta::fixedpoint::max_header_bytes) {
    reject(ErrorCode::header_too_large, "declared header exceeds limit");
  }
#endif
  if (payload_length > delta::fixedpoint::max_payload_bytes) {
    reject(ErrorCode::payload_too_large, "declared payload exceeds limit");
  }
  if (header_length > envelope.size() - 16U ||
      payload_length > envelope.size() - 16U - header_length) {
    reject(ErrorCode::truncated, "declared shard bytes are truncated");
  }
  const auto expected_size = 16U + header_length + payload_length;
  if (envelope.size() != expected_size) {
    reject(ErrorCode::trailing_bytes, "shard contains trailing bytes");
  }
  const auto header = envelope.subspan(16U, header_length);
  const auto payload = envelope.subspan(16U + header_length, payload_length);
  if (header.empty() || std::to_integer<char>(header.front()) != '{' ||
      std::to_integer<char>(header.back()) != '}') {
    reject(ErrorCode::context_mismatch, "shard header is not a canonical JSON object");
  }
  for (const auto byte : header) {
    const auto value = std::to_integer<unsigned char>(byte);
    if (value < 0x20U || value > 0x7eU) {
      reject(ErrorCode::context_mismatch, "shard header is not canonical ASCII JSON");
    }
  }
  const auto header_json = std::string_view(
      reinterpret_cast<const char*>(header.data()), header.size());
  constexpr auto marker = std::string_view{"\"payload_sha256\":\"sha256:"};
  const auto marker_offset = header_json.find(marker);
  if (marker_offset == std::string_view::npos ||
      header_json.find(marker, marker_offset + marker.size()) != std::string_view::npos) {
    reject(ErrorCode::payload_hash_mismatch, "payload hash field is missing or duplicated");
  }
  const auto digest_offset = marker_offset + marker.size();
  if (digest_offset + 65U > header_json.size() || header_json[digest_offset + 64U] != '"' ||
      !std::ranges::all_of(header_json.substr(digest_offset, 64U), lowercase_hex)) {
    reject(ErrorCode::payload_hash_mismatch, "payload hash field is malformed");
  }
  const auto expected_digest = header_json.substr(digest_offset, 64U);
  if (delta::core::canonical::sha256_hex(payload) != expected_digest) {
    reject(ErrorCode::payload_hash_mismatch, "payload hash does not match bytes");
  }
  if ((payload.size() % 2U) != 0U) {
    reject(ErrorCode::payload_length_mismatch, "INT16 payload length is odd");
  }
  for (std::size_t offset = 0U; offset < payload.size(); offset += 2U) {
    const std::uint16_t raw = static_cast<std::uint16_t>(
        static_cast<std::uint16_t>(std::to_integer<std::uint8_t>(payload[offset])) |
        static_cast<std::uint16_t>(
            static_cast<std::uint16_t>(
                std::to_integer<std::uint8_t>(payload[offset + 1U]))
            << 8U));
    const auto wide = raw <= 0x7fffU ? static_cast<std::int32_t>(raw)
                                     : static_cast<std::int32_t>(raw) - 65'536;
    if (wide < delta::fixedpoint::q_min || wide > delta::fixedpoint::q_max) {
      reject(ErrorCode::q_value_invalid, "payload contains forbidden INT16 value");
    }
  }
  return EnvelopeView{header, payload};
}

}  // namespace

void validate_opaque_shard(std::span<const std::byte> envelope) {
  static_cast<void>(validate_opaque(envelope));
}

VerifiedShard read_shard(
    std::span<const std::byte> envelope,
    const ShardHeader& expected_header) {
  const auto verified = validate_opaque(envelope);
  const auto payload_length = verified.payload.size();
  if (expected_header.element_count > delta::fixedpoint::max_payload_bytes / 2U ||
      payload_length != static_cast<std::size_t>(expected_header.element_count) * 2U) {
    reject(ErrorCode::payload_length_mismatch, "payload length does not match expected count");
  }
  const auto payload = verified.payload;
  auto verified_header = expected_header;
  verified_header.payload_sha256 = "sha256:" + delta::core::canonical::sha256_hex(payload);
#if !defined(DELTA_FIXEDPOINT_MUTANT_SKIP_CONTEXT)
  const auto header_bytes = verified.header;
  const auto expected_json = canonical_header_json(verified_header);
  const auto expected_bytes = std::as_bytes(std::span(expected_json.data(), expected_json.size()));
  if (!std::ranges::equal(header_bytes, expected_bytes)) {
    reject(ErrorCode::context_mismatch, "canonical header does not match expected context");
  }
#endif
  std::vector<std::int16_t> values;
  values.reserve(expected_header.element_count);
  for (std::size_t offset = 0U; offset < payload.size(); offset += 2U) {
    const std::uint16_t raw = static_cast<std::uint16_t>(
        static_cast<std::uint16_t>(std::to_integer<std::uint8_t>(payload[offset])) |
        static_cast<std::uint16_t>(
            static_cast<std::uint16_t>(
                std::to_integer<std::uint8_t>(payload[offset + 1U]))
            << 8U));
    const auto wide = raw <= 0x7fffU ? static_cast<std::int32_t>(raw)
                                     : static_cast<std::int32_t>(raw) - 65'536;
    if (wide < delta::fixedpoint::q_min || wide > delta::fixedpoint::q_max) {
      reject(ErrorCode::q_value_invalid, "payload contains forbidden INT16 value");
    }
    values.push_back(static_cast<std::int16_t>(wide));
  }
  const auto leaf = delta::fixedpoint::domain_content_id(
      "deltareduce.004.shard-leaf.v1", envelope);
  return VerifiedShard{std::move(verified_header), std::move(values), leaf};
}

ShardCollector::ShardCollector(std::vector<PlanEntry> plan) : plan_(std::move(plan)) {
  if (plan_.empty() || plan_.size() > delta::fixedpoint::max_shards) {
    reject(ErrorCode::incomplete_shard_set, "collector plan size is invalid");
  }
  std::uint64_t cursor = 0U;
  for (std::size_t index = 0; index < plan_.size(); ++index) {
    const auto& entry = plan_[index];
    if (entry.ordinal != static_cast<std::uint32_t>(index) || entry.element_start != cursor ||
        entry.element_count == 0U ||
        entry.payload_bytes != static_cast<std::uint64_t>(entry.element_count) * 2U ||
        !delta::fixedpoint::is_ascii_token(entry.segment_id) ||
        entry.element_count > delta::fixedpoint::max_total_elements - cursor) {
      reject(ErrorCode::gap_or_overlap, "collector plan is not one exact canonical partition");
    }
    cursor += entry.element_count;
  }
}

bool ShardCollector::insert(VerifiedShard shard) {
  if (static_cast<std::size_t>(shard.header.ordinal) >= plan_.size()) {
    reject(ErrorCode::context_mismatch, "shard ordinal is outside plan");
  }
  const auto& expected = plan_[shard.header.ordinal];
  if (shard.header.ordinal != expected.ordinal || shard.header.segment_id != expected.segment_id ||
      shard.header.segment_offset != expected.segment_offset ||
      shard.header.element_start != expected.element_start ||
      shard.header.element_count != expected.element_count) {
    reject(ErrorCode::context_mismatch, "shard range does not match frozen plan");
  }
  const auto existing = std::ranges::find_if(shards_, [&shard](const VerifiedShard& candidate) {
    return candidate.header.ordinal == shard.header.ordinal;
  });
  if (existing != shards_.end()) {
    if (existing->leaf_id == shard.leaf_id) {
      return false;
    }
    reject(ErrorCode::duplicate_conflict, "duplicate ordinal carries conflicting bytes");
  }
  shards_.push_back(std::move(shard));
  return true;
}

bool ShardCollector::complete() const noexcept { return shards_.size() == plan_.size(); }

std::vector<std::int16_t> ShardCollector::canonical_values() const {
  if (!complete()) {
    reject(ErrorCode::incomplete_shard_set, "not all planned shards are present");
  }
  std::vector<const VerifiedShard*> ordered;
  ordered.reserve(shards_.size());
  for (const auto& shard : shards_) {
    ordered.push_back(&shard);
  }
  std::ranges::sort(ordered, {}, [](const VerifiedShard* shard) { return shard->header.ordinal; });
  std::vector<std::int16_t> result;
  for (const auto* shard : ordered) {
    result.insert(result.end(), shard->values.begin(), shard->values.end());
  }
  return result;
}

}  // namespace delta::shards
