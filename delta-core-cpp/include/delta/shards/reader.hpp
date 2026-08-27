#pragma once

#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

#include <delta/shards/envelope.hpp>
#include <delta/shards/plan.hpp>

namespace delta::shards {

struct VerifiedShard {
  ShardHeader header;
  std::vector<std::int16_t> values;
  std::string leaf_id;
};

void validate_opaque_shard(std::span<const std::byte> envelope);

[[nodiscard]] VerifiedShard read_shard(
    std::span<const std::byte> envelope,
    const ShardHeader& expected_header);

class ShardCollector final {
 public:
  explicit ShardCollector(std::vector<PlanEntry> plan);

  [[nodiscard]] bool insert(VerifiedShard shard);
  [[nodiscard]] bool complete() const noexcept;
  [[nodiscard]] std::vector<std::int16_t> canonical_values() const;

 private:
  std::vector<PlanEntry> plan_;
  std::vector<VerifiedShard> shards_;
};

}  // namespace delta::shards
