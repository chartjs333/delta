#pragma once

#include <delta/core/arithmetic.hpp>
#include <delta/core/protocol.hpp>
#include <delta/fixedpoint/bounds.hpp>

#include <cstddef>
#include <cstdint>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace delta::fixedpoint {

struct DirectQContext {
  std::int64_t coefficient;
  std::string input_leaf_id;
  std::string parameter_id;
  std::string round_id;
  std::string shard_id;
  std::string ticket_id;
};

[[nodiscard]] delta::core::protocol::PreparedIntegerShard prepare_direct_q(
    const DirectQContext& context,
    std::span<const std::int16_t> values,
    const ConcreteProofInstance& proof,
    std::string_view expected_proof_id);

class DirectQAccumulator final {
 public:
  DirectQAccumulator(
      ConcreteProofInstance proof,
      std::string expected_proof_id,
      std::size_t element_count);

  void add(std::int64_t coefficient, std::span<const std::int16_t> values);

  [[nodiscard]] std::uint64_t contribution_count() const noexcept;
  [[nodiscard]] std::span<const delta::core::arithmetic::Int128> values() const noexcept;

 private:
  ConcreteProofInstance proof_;
  std::uint64_t contribution_count_{};
  std::vector<delta::core::arithmetic::Int128> values_;
};

enum class ReduceArtifactKind {
  encoded_worker_q_shard,
  encoded_contribution_manifest,
  aggregate_certificate,
  model_checkpoint,
};

[[nodiscard]] constexpr bool distribution_publish_allowed(ReduceArtifactKind kind) noexcept {
  return kind == ReduceArtifactKind::aggregate_certificate ||
         kind == ReduceArtifactKind::model_checkpoint;
}

}  // namespace delta::fixedpoint
