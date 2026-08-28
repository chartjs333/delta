#include <delta_abi.h>

#include <delta/distribution/certification_policy.hpp>

#include <cstddef>
#include <cstdint>
#include <new>
#include <span>
#include <string>
#include <vector>

namespace {

[[nodiscard]] bool valid_view(delta_bytes_view_t view) noexcept {
  return view.data != nullptr || view.size == 0U;
}

void reset_output(delta_output_buffer_t* output) noexcept {
  if (output != nullptr) {
    output->required = 0U;
    output->written = 0U;
  }
}

[[nodiscard]] delta_status_t write_effect(
    const delta::distribution::PolicyDecision& decision,
    delta_output_buffer_t* output) {
  if (output == nullptr) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  const auto effect = decision.canonical_effect_json();
  output->required = effect.size();
  if (output->capacity < effect.size()) {
    return DELTA_STATUS_BUFFER_TOO_SMALL;
  }
  if (!effect.empty() && output->data == nullptr) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  for (std::size_t index = 0U; index < effect.size(); ++index) {
    output->data[index] = static_cast<std::uint8_t>(effect[index]);
  }
  output->written = effect.size();
  return DELTA_STATUS_OK;
}

template <typename Operation>
[[nodiscard]] delta_status_t boundary(Operation operation) noexcept {
  try {
    return operation();
  } catch (const std::bad_alloc&) {
    return DELTA_STATUS_INTERNAL_ERROR;
  } catch (...) {
    return DELTA_STATUS_INTERNAL_ERROR;
  }
}

[[nodiscard]] std::span<const std::byte> as_bytes(delta_bytes_view_t view) noexcept {
  return std::as_bytes(std::span(view.data, view.size));
}

}  // namespace

extern "C" {

delta_status_t delta_distribution_policy_evaluate_borrowed(
    delta_bytes_view_t canonical_manifest,
    delta_bytes_view_t canonical_certificate,
    std::uint8_t request_make_current,
    delta_output_buffer_t* effect_output) {
  reset_output(effect_output);
  return boundary([&]() {
    if (!valid_view(canonical_manifest) || !valid_view(canonical_certificate) ||
        request_make_current > 1U) {
      return DELTA_STATUS_INVALID_ARGUMENT;
    }
    const auto decision = delta::distribution::evaluate_certified_manifest(
        as_bytes(canonical_manifest), as_bytes(canonical_certificate), request_make_current == 1U);
    return write_effect(decision, effect_output);
  });
}

delta_status_t delta_distribution_policy_evaluate_copy(
    delta_bytes_view_t canonical_manifest,
    delta_bytes_view_t canonical_certificate,
    std::uint8_t request_make_current,
    delta_output_buffer_t* effect_output) {
  reset_output(effect_output);
  return boundary([&]() {
    if (!valid_view(canonical_manifest) || !valid_view(canonical_certificate) ||
        request_make_current > 1U) {
      return DELTA_STATUS_INVALID_ARGUMENT;
    }
    // Refuse attacker-controlled lengths before either owned allocation.
    if (canonical_manifest.size > delta::distribution::max_manifest_bytes ||
        canonical_certificate.size > delta::distribution::max_certificate_bytes) {
      const auto decision = delta::distribution::evaluate_certified_manifest(
          as_bytes(canonical_manifest), as_bytes(canonical_certificate), request_make_current == 1U);
      return write_effect(decision, effect_output);
    }
    const auto manifest_view = as_bytes(canonical_manifest);
    const auto certificate_view = as_bytes(canonical_certificate);
    const std::vector<std::byte> manifest(manifest_view.begin(), manifest_view.end());
    const std::vector<std::byte> certificate(certificate_view.begin(), certificate_view.end());
    const auto decision = delta::distribution::evaluate_certified_manifest(
        manifest, certificate, request_make_current == 1U);
    return write_effect(decision, effect_output);
  });
}

}  // extern "C"
