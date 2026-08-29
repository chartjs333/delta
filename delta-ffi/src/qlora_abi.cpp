#include <delta_abi.h>

#include <delta/qlora/context.hpp>

#include <cstddef>
#include <cstdint>
#include <new>
#include <string>

namespace {

[[nodiscard]] bool valid_view(delta_bytes_view_t value) noexcept {
  return value.size == 0U || value.data != nullptr;
}

[[nodiscard]] bool bounded_id(delta_bytes_view_t value) noexcept {
  return valid_view(value) && value.size == 71U;
}

[[nodiscard]] std::string text(delta_bytes_view_t value) {
  return {reinterpret_cast<const char*>(value.data), value.size};
}

void reset_output(delta_output_buffer_t* output) noexcept {
  if (output != nullptr) {
    output->required = 0U;
    output->written = 0U;
  }
}

[[nodiscard]] delta_status_t write_id(
    const std::string& value,
    delta_output_buffer_t* output) noexcept {
  if (output == nullptr) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  output->required = value.size();
  if (output->capacity < value.size()) {
    return DELTA_STATUS_BUFFER_TOO_SMALL;
  }
  if (!value.empty() && output->data == nullptr) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  for (std::size_t index = 0U; index < value.size(); ++index) {
    output->data[index] = static_cast<std::uint8_t>(value[index]);
  }
  output->written = value.size();
  return DELTA_STATUS_OK;
}

}  // namespace

extern "C" delta_status_t delta_qlora_context_id(
    const delta_qlora_context_t* context,
    delta_output_buffer_t* content_id_output) {
  reset_output(content_id_output);
  if (context == nullptr || context->struct_size != DELTA_QLORA_CONTEXT_SIZE ||
      context->reserved != 0U || !bounded_id(context->adapter_parameter_schema_id) ||
      !bounded_id(context->base_model_manifest_id) ||
      !bounded_id(context->parent_adapter_id) ||
      !bounded_id(context->quantized_base_profile_id) ||
      !bounded_id(context->tokenizer_hash) || !bounded_id(context->training_mode_id)) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  try {
    const auto value = delta::qlora::Context{
        text(context->adapter_parameter_schema_id),
        text(context->base_model_manifest_id),
        text(context->parent_adapter_id),
        text(context->quantized_base_profile_id),
        text(context->tokenizer_hash),
        text(context->training_mode_id),
    };
    return write_id(delta::qlora::content_id(value), content_id_output);
  } catch (const std::bad_alloc&) {
    return DELTA_STATUS_INTERNAL_ERROR;
  } catch (...) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
}
