#include <delta/qlora/distribution.hpp>

namespace delta::qlora {

MediaDisposition validate_media_policy(
    const Context& context,
    std::string_view media_type,
    std::string_view object_id,
    const certificates::ApplyQc* apply_qc) {
  (void)canonical_json(context);
  if (!certificates::is_content_id(object_id)) {
    throw certificates::CertificateError(
        certificates::ErrorCode::identifier_invalid, "QLoRA distribution object ID is invalid");
  }
  if (media_type == base_media_type) {
    if (object_id != context.base_model_manifest_id || apply_qc != nullptr) {
      throw certificates::CertificateError(
          certificates::ErrorCode::context_mismatch,
          "QLoRA base media differs from the certified base context");
    }
    return MediaDisposition::certified_base;
  }
  if (media_type == tokenizer_media_type) {
    if (object_id != context.tokenizer_hash || apply_qc != nullptr) {
      throw certificates::CertificateError(
          certificates::ErrorCode::context_mismatch,
          "QLoRA tokenizer media differs from the certified base context");
    }
    return MediaDisposition::certified_base;
  }
  if (media_type == quantization_profile_media_type) {
    if (object_id != context.quantized_base_profile_id || apply_qc != nullptr) {
      throw certificates::CertificateError(
          certificates::ErrorCode::context_mismatch,
          "QLoRA profile media differs from the certified base context");
    }
    return MediaDisposition::certified_base;
  }
  if (media_type == adapter_checkpoint_media_type) {
    if (apply_qc == nullptr || object_id != apply_qc->next_model_hash ||
        apply_qc->parent_checkpoint_id != context.parent_adapter_id) {
      throw certificates::CertificateError(
          certificates::ErrorCode::apply_qc_required,
          "QLoRA adapter media requires its exact existing ApplyQC");
    }
    validate_binding(context, apply_qc->context);
    return MediaDisposition::applied_adapter;
  }
  throw certificates::CertificateError(
      certificates::ErrorCode::identifier_invalid, "QLoRA distribution media type is unknown");
}

}  // namespace delta::qlora
