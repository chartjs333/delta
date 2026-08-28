#include <delta_abi.h>

#include <delta/scheduling/eligibility.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <new>
#include <span>
#include <string>
#include <string_view>
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

[[nodiscard]] std::string text(delta_bytes_view_t view) {
  if (!valid_view(view)) {
    throw delta::scheduling::SchedulingError(
        delta::scheduling::ErrorCode::identifier_invalid,
        "scheduling eligibility policy view is invalid");
  }
  return {reinterpret_cast<const char*>(view.data), view.size};
}

[[nodiscard]] std::vector<std::string> csv(delta_bytes_view_t view) {
  const auto value = text(view);
  std::vector<std::string> result;
  std::size_t start = 0U;
  while (start <= value.size()) {
    const auto end = value.find(',', start);
    const auto count = end == std::string::npos ? value.size() - start : end - start;
    if (count == 0U) {
      throw delta::scheduling::SchedulingError(
          delta::scheduling::ErrorCode::policy_invalid,
          "scheduling eligibility CSV contains an empty member");
    }
    result.push_back(value.substr(start, count));
    if (end == std::string::npos) {
      break;
    }
    start = end + 1U;
  }
  return result;
}

[[nodiscard]] delta::scheduling::EligibilityPolicy policy(
    const delta_scheduling_eligibility_context_t* input) {
  if (input == nullptr ||
      input->struct_size != DELTA_SCHEDULING_ELIGIBILITY_CONTEXT_SIZE ||
      input->reserved != 0U) {
    throw delta::scheduling::SchedulingError(
        delta::scheduling::ErrorCode::policy_invalid,
        "scheduling eligibility ABI context shape is invalid");
  }
  return {
      csv(input->allowed_domain_ids_csv),
      csv(input->allowed_region_ids_csv),
      csv(input->allowed_software_build_ids_csv),
      text(input->arithmetic_profile_id),
      input->decision_tick,
      text(input->eligibility_policy_id),
      input->identity_epoch,
      input->minimum_memory_bytes,
      input->minimum_sample_count,
      text(input->model_mode),
      text(input->parameter_schema_id),
      text(input->round_config_id),
      csv(input->trusted_signature_ids_csv),
  };
}

[[nodiscard]] delta_status_t write_effect(
    std::span<const std::byte> value,
    delta_output_buffer_t* output) {
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
    output->data[index] = std::to_integer<std::uint8_t>(value[index]);
  }
  output->written = value.size();
  return DELTA_STATUS_OK;
}

[[nodiscard]] delta_status_t evaluate(
    const delta_scheduling_eligibility_context_t* expected_policy,
    std::span<const std::byte> canonical_profile,
    delta_output_buffer_t* decision_output) {
  delta::scheduling::Limits limits;
  limits.contract_bytes = 256U * 1024U;
  const auto profile = delta::scheduling::parse_capability_profile(canonical_profile, limits);
  const auto decision = delta::scheduling::evaluate_capability(profile, policy(expected_policy));
  return write_effect(decision.decision_bytes, decision_output);
}

template <typename Operation>
[[nodiscard]] delta_status_t boundary(Operation operation) noexcept {
  try {
    return operation();
  } catch (const delta::scheduling::SchedulingError&) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  } catch (const std::bad_alloc&) {
    return DELTA_STATUS_INTERNAL_ERROR;
  } catch (...) {
    return DELTA_STATUS_INTERNAL_ERROR;
  }
}

}  // namespace

extern "C" {

delta_status_t delta_scheduling_capability_evaluate_borrowed(
    const delta_scheduling_eligibility_context_t* expected_policy,
    delta_bytes_view_t canonical_profile,
    delta_output_buffer_t* decision_output) {
  reset_output(decision_output);
  return boundary([&]() {
    if (!valid_view(canonical_profile)) {
      return DELTA_STATUS_INVALID_ARGUMENT;
    }
    return evaluate(
        expected_policy,
        std::as_bytes(std::span<const std::uint8_t>(
            canonical_profile.data, canonical_profile.size)),
        decision_output);
  });
}

delta_status_t delta_scheduling_capability_evaluate_copy(
    const delta_scheduling_eligibility_context_t* expected_policy,
    delta_bytes_view_t canonical_profile,
    delta_output_buffer_t* decision_output) {
  reset_output(decision_output);
  return boundary([&]() {
    if (!valid_view(canonical_profile)) {
      return DELTA_STATUS_INVALID_ARGUMENT;
    }
    const auto view = std::as_bytes(std::span<const std::uint8_t>(
        canonical_profile.data, canonical_profile.size));
    const std::vector<std::byte> owned(view.begin(), view.end());
    return evaluate(expected_policy, owned, decision_output);
  });
}

}  // extern "C"
