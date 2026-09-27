#pragma once

#include <delta/certificates/contracts.hpp>

#include <cstdint>
#include <span>
#include <string>
#include <vector>

namespace delta::apply {

struct DomainAggregate {
  std::string domain_id;
  std::vector<std::int64_t> values;
};

struct State {
  std::vector<std::int64_t> model;
  std::vector<std::int64_t> momentum;
  std::string checkpoint_id;
  std::string optimizer_id;
};

[[nodiscard]] std::int64_t round_half_toward_positive(
    std::int64_t numerator,
    std::uint64_t denominator);

[[nodiscard]] certificates::ApplyCandidate compute_candidate(
    const certificates::Context& context,
    std::string aggregate_root_qc_id,
    const certificates::ApplyArithmeticProfile& profile,
    const State& parent,
    std::span<const DomainAggregate> aggregates);

}  // namespace delta::apply
