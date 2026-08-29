#pragma once

#include <delta/apply/engine.hpp>
#include <delta/qlora/context.hpp>

#include <span>
#include <string>

namespace delta::qlora {

struct AdapterState {
  std::vector<std::int64_t> values;
  std::vector<std::int64_t> momentum;
  std::string adapter_checkpoint_id;
  std::string outer_optimizer_id;
};

[[nodiscard]] certificates::ApplyCandidate compute_adapter_candidate(
    const Context& qlora_context,
    const certificates::Context& certificate_context,
    std::string aggregate_root_qc_id,
    const certificates::ApplyArithmeticProfile& profile,
    const AdapterState& parent,
    std::span<const apply::DomainAggregate> aggregates);

[[nodiscard]] certificates::CurrentPointerCommand make_adapter_pointer_command(
    const Context& qlora_context,
    const certificates::ApplyQc& apply_qc,
    std::string apply_qc_id,
    std::string next_adapter_checkpoint_id);

}  // namespace delta::qlora
