#pragma once

#include <cstddef>
#include <cstdint>
#include <span>
#include <stdexcept>
#include <string>
#include <vector>

namespace delta::shards {

enum class ErrorCode {
  invalid_segment,
  gap_or_overlap,
  shard_count_limit,
  payload_size_invalid,
  bad_magic,
  unsupported_version,
  header_too_large,
  payload_too_large,
  truncated,
  trailing_bytes,
  context_mismatch,
  payload_length_mismatch,
  payload_hash_mismatch,
  q_value_invalid,
  content_id_invalid,
  empty_shard_table,
  duplicate_conflict,
  incomplete_shard_set,
};

class ShardError final : public std::runtime_error {
 public:
  ShardError(ErrorCode code, std::string message);

  [[nodiscard]] ErrorCode code() const noexcept;

 private:
  ErrorCode code_;
};

struct Segment {
  std::string id;
  std::uint32_t ordinal;
  std::uint64_t element_start;
  std::uint64_t element_count;
};

struct PlanEntry {
  std::uint32_t ordinal;
  std::string segment_id;
  std::uint64_t segment_offset;
  std::uint64_t element_start;
  std::uint32_t element_count;
  std::uint32_t payload_bytes;

  bool operator==(const PlanEntry&) const = default;
};

[[nodiscard]] std::vector<PlanEntry> plan_shards(
    std::span<const Segment> segments,
    std::uint32_t target_payload_bytes);

}  // namespace delta::shards
