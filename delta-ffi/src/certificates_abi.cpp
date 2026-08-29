#include <delta_abi.h>

#include <delta/certificates/contracts.hpp>
#include <delta/core/canonical.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <new>
#include <span>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {

struct KindInfo {
  std::string_view type_name;
  std::string_view domain;
};

[[nodiscard]] KindInfo kind_info(std::uint32_t kind) {
  switch (kind) {
    case DELTA_CERTIFICATE_INPUT_SET:
      return {"INPUT_SET_CERTIFICATE", "deltareduce.008.input-set-certificate.v1"};
    case DELTA_CERTIFICATE_SEED_TRANSCRIPT:
      return {"SEED_TRANSCRIPT", "deltareduce.008.seed-transcript.v1"};
    case DELTA_CERTIFICATE_NORM_EVIDENCE:
      return {"NORM_EVIDENCE", "deltareduce.008.norm-evidence.v1"};
    case DELTA_CERTIFICATE_ELIGIBILITY:
      return {"ELIGIBILITY_CERTIFICATE", "deltareduce.008.eligibility-certificate.v1"};
    case DELTA_CERTIFICATE_AGGREGATION_PLAN:
      return {
          "AGGREGATION_PLAN_CERTIFICATE",
          "deltareduce.008.aggregation-plan-certificate.v1"};
    case DELTA_CERTIFICATE_PARAMETER_SHARD_QC:
      return {"PARAMETER_SHARD_QC", "deltareduce.008.parameter-shard-qc.v1"};
    case DELTA_CERTIFICATE_AGGREGATE_ROOT_QC:
      return {"AGGREGATE_ROOT_QC", "deltareduce.008.aggregate-root-qc.v1"};
    case DELTA_CERTIFICATE_APPLY_PROFILE:
      return {"APPLY_ARITHMETIC_PROFILE", "deltareduce.008.apply-arithmetic-profile.v1"};
    case DELTA_CERTIFICATE_APPLY_CANDIDATE:
      return {"APPLY_CANDIDATE", "deltareduce.008.apply-candidate.v1"};
    case DELTA_CERTIFICATE_APPLY_QC:
      return {"APPLY_QC", "deltareduce.008.apply-qc.v1"};
    case DELTA_CERTIFICATE_CURRENT_POINTER_COMMAND:
      return {"CURRENT_POINTER_COMMAND", "deltareduce.008.current-pointer-command.v1"};
    default:
      throw delta::certificates::CertificateError(
          delta::certificates::ErrorCode::identifier_invalid, "unknown certificate ABI kind");
  }
}

[[nodiscard]] bool valid_view(delta_bytes_view_t view) noexcept {
  return view.data != nullptr || view.size == 0U;
}

[[nodiscard]] std::string text(delta_bytes_view_t view) {
  if (!valid_view(view)) {
    throw delta::certificates::CertificateError(
        delta::certificates::ErrorCode::identifier_invalid, "invalid certificate ABI view");
  }
  return {reinterpret_cast<const char*>(view.data), view.size};
}

void reset(delta_output_buffer_t* output) noexcept {
  if (output != nullptr) {
    output->required = 0U;
    output->written = 0U;
  }
}

[[nodiscard]] std::string derive_id(
    std::string_view domain,
    std::span<const std::byte> certificate) {
  std::vector<std::byte> input;
  input.reserve(domain.size() + 1U + certificate.size());
  for (const char character : domain) {
    input.push_back(static_cast<std::byte>(character));
  }
  input.push_back(std::byte{0});
  input.insert(input.end(), certificate.begin(), certificate.end());
  return "sha256:" + delta::core::canonical::sha256_hex(input);
}

[[nodiscard]] delta_status_t write(std::string_view value, delta_output_buffer_t* output) {
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
  std::copy(value.begin(), value.end(), reinterpret_cast<char*>(output->data));
  output->written = value.size();
  return DELTA_STATUS_OK;
}

[[nodiscard]] delta_status_t inspect(
    const delta_certificate_inspect_context_t* context,
    std::span<const std::byte> certificate,
    delta_output_buffer_t* output) {
  if (context == nullptr ||
      context->struct_size != DELTA_CERTIFICATE_INSPECT_CONTEXT_SIZE ||
      certificate.empty() || certificate.size() > delta::certificates::max_contract_bytes) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  const auto info = kind_info(context->kind);
  const auto expected_id = text(context->expected_content_id);
  const auto expected_formal = text(context->expected_formal_semantics_id);
  if (!delta::certificates::is_content_id(expected_id) ||
      expected_formal != delta::certificates::formal_semantics_id) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  const auto document = std::string_view(
      reinterpret_cast<const char*>(certificate.data()), certificate.size());
  if (document.front() != '{' || document.back() != '}' ||
      std::any_of(document.begin(), document.end(), [](char character) {
        const auto byte = static_cast<unsigned char>(character);
        return byte < 0x20U || byte > 0x7eU;
      }) ||
      document.find("\"formal_semantics_id\":\"" + expected_formal + "\"") ==
          std::string_view::npos ||
      document.find("\"type_name\":\"" + std::string(info.type_name) + "\"") ==
          std::string_view::npos ||
      derive_id(info.domain, certificate) != expected_id) {
    return DELTA_STATUS_TRANSITION_REJECTED;
  }
  const auto effect = std::string{"{\"content_id\":\""} + expected_id +
                      "\",\"formal_action_id\":\"ACT-VERIFY-CERTIFICATE\",\"status\":\"ACCEPT\",\"type_name\":\"" +
                      std::string(info.type_name) + "\"}";
  return write(effect, output);
}

template <typename Operation>
[[nodiscard]] delta_status_t boundary(Operation operation) noexcept {
  try {
    return operation();
  } catch (const delta::certificates::CertificateError&) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  } catch (const std::bad_alloc&) {
    return DELTA_STATUS_INTERNAL_ERROR;
  } catch (...) {
    return DELTA_STATUS_INTERNAL_ERROR;
  }
}

}  // namespace

extern "C" {

delta_status_t delta_certificate_inspect_borrowed(
    const delta_certificate_inspect_context_t* context,
    delta_bytes_view_t canonical_certificate,
    delta_output_buffer_t* effect_output) {
  reset(effect_output);
  return boundary([&]() {
    if (!valid_view(canonical_certificate)) {
      return DELTA_STATUS_INVALID_ARGUMENT;
    }
    return inspect(
        context,
        std::as_bytes(
            std::span(canonical_certificate.data, canonical_certificate.size)),
        effect_output);
  });
}

delta_status_t delta_certificate_inspect_copy(
    const delta_certificate_inspect_context_t* context,
    delta_bytes_view_t canonical_certificate,
    delta_output_buffer_t* effect_output) {
  reset(effect_output);
  return boundary([&]() {
    if (!valid_view(canonical_certificate) ||
        canonical_certificate.size > delta::certificates::max_contract_bytes) {
      return DELTA_STATUS_INVALID_ARGUMENT;
    }
    const auto input = std::as_bytes(
        std::span(canonical_certificate.data, canonical_certificate.size));
    const std::vector<std::byte> owned(input.begin(), input.end());
    return inspect(context, owned, effect_output);
  });
}

}  // extern "C"
