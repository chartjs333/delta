#include <delta/qlora/adapter_apply.hpp>

#include <utility>

namespace delta::qlora {

certificates::ApplyCandidate compute_adapter_candidate(
    const Context& qlora_context,
    const certificates::Context& certificate_context,
    std::string aggregate_root_qc_id,
    const certificates::ApplyArithmeticProfile& profile,
    const AdapterState& parent,
    std::span<const apply::DomainAggregate> aggregates) {
  validate_binding(qlora_context, certificate_context);
  if (parent.adapter_checkpoint_id != qlora_context.parent_adapter_id) {
    throw certificates::CertificateError(
        certificates::ErrorCode::parent_mismatch,
        "adapter apply parent differs from the frozen QLoRA context");
  }
  return apply::compute_candidate(
      certificate_context,
      std::move(aggregate_root_qc_id),
      profile,
      apply::State{
          parent.values,
          parent.momentum,
          parent.adapter_checkpoint_id,
          parent.outer_optimizer_id,
      },
      aggregates);
}

certificates::CurrentPointerCommand make_adapter_pointer_command(
    const Context& qlora_context,
    const certificates::ApplyQc& apply_qc,
    std::string apply_qc_id,
    std::string next_adapter_checkpoint_id) {
  validate_binding(qlora_context, apply_qc.context);
  if (apply_qc.parent_checkpoint_id != qlora_context.parent_adapter_id ||
      !certificates::is_content_id(apply_qc_id) ||
      !certificates::is_content_id(next_adapter_checkpoint_id)) {
    throw certificates::CertificateError(
        certificates::ErrorCode::parent_mismatch,
        "adapter pointer command has an invalid parent or content ID");
  }
  return certificates::CurrentPointerCommand{
      .context = apply_qc.context,
      .apply_qc_id = std::move(apply_qc_id),
      .expected_parent_checkpoint_id = qlora_context.parent_adapter_id,
      .next_checkpoint_id = std::move(next_adapter_checkpoint_id),
      .next_optimizer_hash = apply_qc.next_optimizer_hash,
  };
}

}  // namespace delta::qlora
