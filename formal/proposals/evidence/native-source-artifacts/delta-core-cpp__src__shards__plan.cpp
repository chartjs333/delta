#include <delta/shards/plan.hpp>

#include <delta/fixedpoint/checked.hpp>
#include <delta/fixedpoint/profile.hpp>

#include <algorithm>
#include <cstdint>
#include <limits>
#include <string>
#include <utility>
#include <vector>

namespace delta::shards {
namespace {

[[noreturn]] void reject(ErrorCode code, const char* message) {
  throw ShardError(code, message);
}

}  // namespace

ShardError::ShardError(ErrorCode code, std::string message)
    : std::runtime_error(std::move(message)), code_(code) {}

ErrorCode ShardError::code() const noexcept { return code_; }

std::vector<PlanEntry> plan_shards(
    std::span<const Segment> segments,
    std::uint32_t target_payload_bytes) {
  if (target_payload_bytes < 2U || target_payload_bytes > delta::fixedpoint::max_payload_bytes ||
      target_payload_bytes % 2U != 0U) {
    reject(ErrorCode::payload_size_invalid, "target payload size must be bounded and even");
  }
  if (segments.empty() || segments.size() > delta::fixedpoint::max_segments) {
    reject(ErrorCode::invalid_segment, "segment table size is invalid");
  }
  const auto per_shard = static_cast<std::uint64_t>(target_payload_bytes / 2U);
  std::vector<PlanEntry> result;
  std::uint64_t cursor = 0U;
  for (std::size_t segment_index = 0; segment_index < segments.size(); ++segment_index) {
    const auto& segment = segments[segment_index];
    if (!delta::fixedpoint::is_ascii_token(segment.id) ||
        segment.ordinal != static_cast<std::uint32_t>(segment_index) ||
        segment.element_count == 0U || segment.element_start != cursor ||
        segment.element_count > delta::fixedpoint::max_total_elements - cursor) {
      reject(ErrorCode::gap_or_overlap, "segments do not form one canonical exact partition");
    }
    std::uint64_t offset = 0U;
    while (offset < segment.element_count) {
      if (result.size() >= delta::fixedpoint::max_shards) {
        reject(ErrorCode::shard_count_limit, "shard plan exceeds maximum count");
      }
      const auto count = std::min(per_shard, segment.element_count - offset);
      if (count > std::numeric_limits<std::uint32_t>::max()) {
        reject(ErrorCode::payload_size_invalid, "shard element count exceeds UINT32");
      }
      result.push_back(PlanEntry{
          static_cast<std::uint32_t>(result.size()),
          segment.id,
          offset,
          segment.element_start + offset,
          static_cast<std::uint32_t>(count),
          static_cast<std::uint32_t>(count * 2U),
      });
      offset += count;
    }
    cursor += segment.element_count;
  }
  if (cursor > delta::fixedpoint::max_total_elements) {
    reject(ErrorCode::invalid_segment, "total element count exceeds profile limit");
  }
  return result;
}

}  // namespace delta::shards
