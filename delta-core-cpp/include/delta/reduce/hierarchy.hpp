#pragma once

#include <delta/core/arithmetic.hpp>
#include <delta/core/canonical.hpp>
#include <delta/core/protocol.hpp>
#include <delta/reduce/topology.hpp>

#include <cstdint>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace delta::reduce {

struct Contribution {
  Context context;
  std::string domain_id;
  std::string shard_id;
  std::string ticket_id;
  std::string worker_shard_id;
  std::int64_t coefficient;
  std::uint64_t coefficient_denominator;
  std::vector<std::int16_t> q_values;

  bool operator==(const Contribution&) const = default;
};

struct RegionalResult {
  Context context;
  std::string topology_id;
  std::string hierarchy_proof_instance_id;
  std::string domain_id;
  std::string region_id;
  std::string shard_id;
  std::vector<delta::core::arithmetic::Int128> numerator;
  std::uint64_t eligible_count;
  delta::core::arithmetic::Int128 coefficient_numerator_sum;
  std::uint64_t coefficient_denominator;
  std::string regional_input_set_id;
  std::string result_id;

  bool operator==(const RegionalResult&) const = default;
};

struct GlobalResult {
  Context context;
  std::string topology_id;
  std::string hierarchy_proof_instance_id;
  std::string domain_id;
  std::string shard_id;
  std::vector<delta::core::arithmetic::Int128> numerator;
  std::uint64_t eligible_count;
  delta::core::arithmetic::Int128 coefficient_numerator_sum;
  std::uint64_t coefficient_denominator;
  std::string regional_set_id;
  std::string result_id;

  bool operator==(const GlobalResult&) const = default;
};

struct CommitteeQc {
  Context context;
  std::string topology_id;
  std::string hierarchy_proof_instance_id;
  std::string body_id;
  std::string domain_id;
  std::string region_id;
  std::string shard_id;
  std::uint64_t committee_epoch;
  std::uint64_t view;
  std::uint32_t quorum_threshold;
  std::vector<std::string> signer_ids;
  bool global;

  bool operator==(const CommitteeQc&) const = default;
};

struct Assembly {
  delta::core::canonical::Bytes canonical_bytes;
  std::string aggregate_id;
  std::vector<GlobalResult> results;
  std::vector<CommitteeQc> certificates;
};

[[nodiscard]] RegionalResult reduce_region(
    const Topology& topology,
    const HierarchyProofInstance& proof,
    std::string_view domain_id,
    std::string_view region_id,
    std::string_view shard_id,
    std::span<const Contribution> contributions);

class GlobalAccumulator final {
 public:
  GlobalAccumulator(
      const Topology& topology,
      const HierarchyProofInstance& proof,
      std::string domain_id,
      std::string shard_id);

  [[nodiscard]] bool ingest(RegionalResult result, CommitteeQc certificate);
  [[nodiscard]] GlobalResult finalize() const;
  [[nodiscard]] std::size_t received_count() const noexcept;

 private:
  const Topology* topology_;
  const HierarchyProofInstance* proof_;
  std::string domain_id_;
  std::string shard_id_;
  std::vector<RegionalResult> results_;
  std::vector<CommitteeQc> certificates_;
};

[[nodiscard]] GlobalResult reduce_flat(
    const Topology& topology,
    const HierarchyProofInstance& proof,
    std::string_view domain_id,
    std::string_view shard_id,
    std::span<const Contribution> contributions);

[[nodiscard]] Assembly assemble_complete(
    const Topology& topology,
    const HierarchyProofInstance& proof,
    std::span<const GlobalResult> results,
    std::span<const CommitteeQc> certificates);

[[nodiscard]] delta::core::canonical::Bytes canonical_bytes(const RegionalResult& result);
[[nodiscard]] delta::core::canonical::Bytes canonical_bytes(const GlobalResult& result);
[[nodiscard]] delta::core::canonical::Bytes canonical_bytes(const Contribution& contribution);
[[nodiscard]] delta::core::canonical::Bytes canonical_bytes(const CommitteeQc& certificate);
[[nodiscard]] delta::core::canonical::Bytes canonical_routing_projection(
    const Topology& topology);
[[nodiscard]] std::string regional_result_id(const RegionalResult& result);
[[nodiscard]] std::string global_result_id(const GlobalResult& result);
[[nodiscard]] std::string committee_qc_id(const CommitteeQc& certificate);
[[nodiscard]] std::string routing_projection_id(const Topology& topology);

void validate_committee_qc(
    const Topology& topology,
    const HierarchyProofInstance& proof,
    const CommitteeQc& certificate);

[[nodiscard]] delta::core::protocol::Vote make_committee_vote(
    const Topology& topology,
    const HierarchyProofInstance& proof,
    const CommitteeQc& intent,
    std::string validator_id,
    std::string signature_id,
    std::uint64_t durable_sequence);

}  // namespace delta::reduce
