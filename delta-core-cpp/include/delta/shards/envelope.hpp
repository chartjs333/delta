#pragma once

#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <vector>

namespace delta::shards {

struct ShardHeader {
  std::uint32_t ordinal;
  std::string segment_id;
  std::uint64_t segment_offset;
  std::uint64_t element_start;
  std::uint32_t element_count;
  std::string formal_semantics_id;
  std::string parameter_schema_id;
  std::string profile_id;
  std::string proof_instance_id;
  std::string round_config_id;
  std::string scale_table_id;
  std::string shard_plan_id;
  std::string ticket_id;
  std::string payload_sha256;

  bool operator==(const ShardHeader&) const = default;
};

struct EncodedShard {
  ShardHeader header;
  std::vector<std::byte> envelope;
  std::string leaf_id;
};

[[nodiscard]] std::string canonical_header_json(const ShardHeader& header);
[[nodiscard]] EncodedShard write_shard(
    const ShardHeader& header,
    std::span<const std::int16_t> values);
[[nodiscard]] std::string merkle_root(std::span<const std::string> ordered_leaf_ids);

}  // namespace delta::shards
