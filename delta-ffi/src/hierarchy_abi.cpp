#include <delta_abi.h>

#include <delta/reduce/hierarchy.hpp>

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
    throw delta::reduce::ReduceError(
        delta::reduce::ErrorCode::identifier_invalid, "hierarchy context view is invalid");
  }
  return {reinterpret_cast<const char*>(view.data), view.size};
}

[[nodiscard]] delta::reduce::Context context(const delta_hierarchy_context_t* input) {
  if (input == nullptr || input->struct_size != DELTA_HIERARCHY_CONTEXT_SIZE ||
      input->reserved != 0U) {
    throw delta::reduce::ReduceError(
        delta::reduce::ErrorCode::context_mismatch, "hierarchy ABI context shape is invalid");
  }
  return {
      text(input->accumulator_proof_instance_id),
      text(input->coefficient_plan_root),
      text(input->fixedpoint_config_id),
      text(input->formal_semantics_id),
      text(input->frozen_input_root),
      text(input->parent_checkpoint_id),
      text(input->profile_id),
      text(input->round_config_id),
      text(input->scale_table_id),
      text(input->shard_plan_id),
  };
}

[[nodiscard]] delta_status_t write_effect(
    std::string_view value,
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
    output->data[index] = static_cast<std::uint8_t>(value[index]);
  }
  output->written = value.size();
  return DELTA_STATUS_OK;
}

[[nodiscard]] delta_status_t validate_contract(
    const delta_hierarchy_context_t* expected_context,
    std::span<const std::byte> topology_bytes,
    std::span<const std::byte> proof_bytes,
    delta_output_buffer_t* output) {
  const auto topology = delta::reduce::parse_topology(
      topology_bytes, context(expected_context));
  const auto proof = delta::reduce::parse_hierarchy_proof(proof_bytes, topology);
  const auto effect = std::string{"{\"hierarchy_proof_instance_id\":\""} +
                      proof.hierarchy_proof_instance_id +
                      "\",\"routing_projection_id\":\"" +
                      delta::reduce::routing_projection_id(topology) +
                      "\",\"status\":\"ACCEPT\"," +
                      "\"topology_id\":\"" + topology.topology_id + "\"}";
  return write_effect(effect, output);
}

template <typename Operation>
[[nodiscard]] delta_status_t boundary(Operation operation) noexcept {
  try {
    return operation();
  } catch (const delta::reduce::ReduceError&) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  } catch (const delta::core::arithmetic::ArithmeticError&) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  } catch (const std::bad_alloc&) {
    return DELTA_STATUS_INTERNAL_ERROR;
  } catch (...) {
    return DELTA_STATUS_INTERNAL_ERROR;
  }
}

}  // namespace

extern "C" {

delta_status_t delta_hierarchy_contract_validate_borrowed(
    const delta_hierarchy_context_t* expected_context,
    delta_bytes_view_t canonical_topology,
    delta_bytes_view_t canonical_proof,
    delta_output_buffer_t* effect_output) {
  reset_output(effect_output);
  return boundary([&]() {
    if (!valid_view(canonical_topology) || !valid_view(canonical_proof)) {
      return DELTA_STATUS_INVALID_ARGUMENT;
    }
    return validate_contract(
        expected_context,
        std::as_bytes(std::span(canonical_topology.data, canonical_topology.size)),
        std::as_bytes(std::span(canonical_proof.data, canonical_proof.size)),
        effect_output);
  });
}

delta_status_t delta_hierarchy_contract_validate_copy(
    const delta_hierarchy_context_t* expected_context,
    delta_bytes_view_t canonical_topology,
    delta_bytes_view_t canonical_proof,
    delta_output_buffer_t* effect_output) {
  reset_output(effect_output);
  return boundary([&]() {
    if (!valid_view(canonical_topology) || !valid_view(canonical_proof)) {
      return DELTA_STATUS_INVALID_ARGUMENT;
    }
    const auto topology_view =
        std::as_bytes(std::span(canonical_topology.data, canonical_topology.size));
    const auto proof_view = std::as_bytes(std::span(canonical_proof.data, canonical_proof.size));
    const std::vector<std::byte> topology(topology_view.begin(), topology_view.end());
    const std::vector<std::byte> proof(proof_view.begin(), proof_view.end());
    return validate_contract(expected_context, topology, proof, effect_output);
  });
}

}  // extern "C"
