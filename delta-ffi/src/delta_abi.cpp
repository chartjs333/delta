#include <delta_abi.h>

#include <delta/core/canonical.hpp>
#include <delta/core/consensus.hpp>
#include <delta/core/protocol.hpp>
#include <delta/core/transition.hpp>
#include <delta/runtime/runtime.hpp>
#include <delta/runtime/vote_codec.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <limits>
#include <memory>
#include <new>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <utility>

struct delta_runtime {
  std::unique_ptr<delta::runtime::Runtime> instance;
};

namespace {

namespace canonical = delta::core::canonical;

static_assert(sizeof(void*) == 8U, "DeltaReduce ABI v1 requires a 64-bit process");
static_assert(sizeof(delta_bytes_view_t) == 16U);
static_assert(sizeof(delta_output_buffer_t) == DELTA_ABI_OUTPUT_BUFFER_SIZE);
static_assert(sizeof(delta_runtime_descriptor_t) == DELTA_ABI_DESCRIPTOR_SIZE);
static_assert(sizeof(delta_runtime_open_options_t) == DELTA_ABI_OPEN_OPTIONS_SIZE);
static_assert(sizeof(delta_vote_receipt_v1_t) == DELTA_VOTE_RECEIPT_V1_SIZE);
static_assert(sizeof(delta_submit_receipt_v1_t) == DELTA_SUBMIT_RECEIPT_V1_SIZE);

constexpr delta_runtime_descriptor_t descriptor{
    DELTA_ABI_DESCRIPTOR_SIZE,
    DELTA_ABI_MAJOR,
    DELTA_ABI_MINOR,
    DELTA_ABI_FEATURE_BITS,
    DELTA_SCHEMA_VERSION,
    DELTA_PROTOCOL_VERSION,
    DELTA_FORMAL_SEMANTICS_ID,
    DELTA_BUILD_ID,
    DELTA_SCHEMA_SET_ID,
    DELTA_RUNTIME_PROFILE,
};

[[nodiscard]] bool valid_view(delta_bytes_view_t view) noexcept {
  return view.data != nullptr || view.size == 0U;
}

[[nodiscard]] std::string copy_string(delta_bytes_view_t view) {
  if (!valid_view(view)) {
    throw std::invalid_argument("invalid borrowed byte view");
  }
  return {reinterpret_cast<const char*>(view.data), view.size};
}

[[nodiscard]] canonical::Bytes copy_bytes(delta_bytes_view_t view) {
  if (!valid_view(view)) {
    throw std::invalid_argument("invalid borrowed byte view");
  }
  canonical::Bytes result;
  result.reserve(view.size);
  for (std::size_t index = 0; index < view.size; ++index) {
    result.push_back(static_cast<std::byte>(view.data[index]));
  }
  return result;
}

[[nodiscard]] bool equals(delta_bytes_view_t view, std::string_view expected) noexcept {
  if (!valid_view(view) || view.size != expected.size()) {
    return false;
  }
  if (view.size == 0U) {
    return true;
  }
  return std::equal(view.data, view.data + view.size, expected.begin(), [](std::uint8_t left, char right) {
    return left == static_cast<std::uint8_t>(static_cast<unsigned char>(right));
  });
}

[[nodiscard]] delta_status_t copy_output(
    std::span<const std::byte> value,
    delta_output_buffer_t* output) noexcept {
  if (output == nullptr) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  output->required = value.size();
  output->written = 0U;
  if (output->capacity < value.size()) {
    return DELTA_STATUS_BUFFER_TOO_SMALL;
  }
  if (!value.empty() && output->data == nullptr) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  for (std::size_t index = 0; index < value.size(); ++index) {
    output->data[index] = std::to_integer<std::uint8_t>(value[index]);
  }
  output->written = value.size();
  return DELTA_STATUS_OK;
}

void reset_output(delta_output_buffer_t* output) noexcept {
  if (output != nullptr) {
    output->required = 0U;
    output->written = 0U;
  }
}

[[nodiscard]] delta_status_t map_runtime_error(delta::runtime::ErrorCode code) noexcept {
  switch (code) {
    case delta::runtime::ErrorCode::invalid_config:
      return DELTA_STATUS_INVALID_ARGUMENT;
    case delta::runtime::ErrorCode::queue_full:
      return DELTA_STATUS_QUEUE_FULL;
    case delta::runtime::ErrorCode::closed:
      return DELTA_STATUS_CLOSED;
    case delta::runtime::ErrorCode::io_error:
    case delta::runtime::ErrorCode::durable_binding_lost:
      return DELTA_STATUS_IO_ERROR;
    case delta::runtime::ErrorCode::wal_corrupt:
    case delta::runtime::ErrorCode::snapshot_corrupt:
    case delta::runtime::ErrorCode::sequence_invalid:
    case delta::runtime::ErrorCode::recovery_mismatch:
      return DELTA_STATUS_CORRUPT_DURABLE_STATE;
    case delta::runtime::ErrorCode::request_conflict:
      return DELTA_STATUS_CONFLICT;
    case delta::runtime::ErrorCode::simulated_crash:
      return DELTA_STATUS_INTERNAL_ERROR;
  }
  return DELTA_STATUS_INTERNAL_ERROR;
}

[[nodiscard]] delta_status_t map_consensus_error(
    delta::core::consensus::ErrorCode code) noexcept {
  switch (code) {
    case delta::core::consensus::ErrorCode::conflicting_vote:
      return DELTA_STATUS_CONFLICT;
    case delta::core::consensus::ErrorCode::vote_admission_rejected:
      return DELTA_STATUS_TRANSITION_REJECTED;
    case delta::core::consensus::ErrorCode::validator_set_invalid:
    case delta::core::consensus::ErrorCode::quorum_policy_mismatch:
    case delta::core::consensus::ErrorCode::unknown_signer:
    case delta::core::consensus::ErrorCode::signer_set_invalid:
    case delta::core::consensus::ErrorCode::vote_invalid:
    case delta::core::consensus::ErrorCode::identifier_invalid:
    case delta::core::consensus::ErrorCode::ticket_set_invalid:
    case delta::core::consensus::ErrorCode::unknown_ticket:
    case delta::core::consensus::ErrorCode::commitment_equivocation:
    case delta::core::consensus::ErrorCode::commitment_missing:
    case delta::core::consensus::ErrorCode::availability_commitment_mismatch:
    case delta::core::consensus::ErrorCode::availability_coverage_incomplete:
    case delta::core::consensus::ErrorCode::availability_attesters_invalid:
    case delta::core::consensus::ErrorCode::availability_conflict:
    case delta::core::consensus::ErrorCode::input_set_empty:
    case delta::core::consensus::ErrorCode::vote_action_invalid:
    case delta::core::consensus::ErrorCode::vote_policy_invalid:
      return DELTA_STATUS_INVALID_ARGUMENT;
  }
  return DELTA_STATUS_INVALID_ARGUMENT;
}

template <typename Operation>
[[nodiscard]] delta_status_t boundary(Operation operation) noexcept {
  try {
    return operation();
  } catch (const delta::runtime::RuntimeError& error) {
    return map_runtime_error(error.code());
  } catch (const delta::core::consensus::ConsensusError& error) {
    return map_consensus_error(error.code());
  } catch (const delta::core::transition::TransitionError&) {
    return DELTA_STATUS_TRANSITION_REJECTED;
  } catch (const delta::core::protocol::ProtocolError&) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  } catch (const delta::core::canonical::DecodeError&) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  } catch (const std::invalid_argument&) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  } catch (const std::bad_alloc&) {
    return DELTA_STATUS_INTERNAL_ERROR;
  } catch (...) {
    return DELTA_STATUS_INTERNAL_ERROR;
  }
}

[[nodiscard]] delta_status_t validate_expectations(
    const delta_runtime_open_options_t& options) noexcept {
  if (options.expected_abi_major != DELTA_ABI_MAJOR ||
      options.expected_abi_minor != DELTA_ABI_MINOR) {
    return DELTA_STATUS_ABI_MISMATCH;
  }
  if (!equals(options.expected_schema_version, DELTA_SCHEMA_VERSION) ||
      !equals(options.expected_schema_set_id, DELTA_SCHEMA_SET_ID)) {
    return DELTA_STATUS_SCHEMA_MISMATCH;
  }
  if (!equals(options.expected_protocol_version, DELTA_PROTOCOL_VERSION)) {
    return DELTA_STATUS_PROTOCOL_MISMATCH;
  }
  if (!equals(options.expected_formal_semantics_id, DELTA_FORMAL_SEMANTICS_ID)) {
    return DELTA_STATUS_FORMAL_SEMANTICS_MISMATCH;
  }
  if (!equals(options.expected_build_id, DELTA_BUILD_ID)) {
    return DELTA_STATUS_BUILD_MISMATCH;
  }
  return DELTA_STATUS_OK;
}

[[nodiscard]] delta_status_t validate_open_options(
    const delta_runtime_open_options_t* options) noexcept {
  if (options == nullptr || options->struct_size != DELTA_ABI_OPEN_OPTIONS_SIZE ||
      options->reserved != 0U || options->submission_capacity == 0U ||
      !valid_view(options->directory_utf8) || options->directory_utf8.size == 0U ||
      !valid_view(options->initial_state) || options->initial_state.size == 0U) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  return validate_expectations(*options);
}

void reset_vote_receipt(delta_vote_receipt_v1_t* receipt) noexcept {
  if (receipt == nullptr) {
    return;
  }
  reset_output(&receipt->canonical_receipt);
}

[[nodiscard]] bool valid_vote_receipt_shape(
    const delta_vote_receipt_v1_t* receipt) noexcept {
  return receipt != nullptr && receipt->struct_size == DELTA_VOTE_RECEIPT_V1_SIZE &&
         receipt->reserved == 0U;
}

void reset_submit_receipt(delta_submit_receipt_v1_t* receipt) noexcept {
  if (receipt == nullptr) {
    return;
  }
  receipt->journal_sequence = 0U;
  reset_output(&receipt->canonical_effect);
}

[[nodiscard]] bool valid_submit_receipt_shape(
    const delta_submit_receipt_v1_t* receipt) noexcept {
  return receipt != nullptr && receipt->struct_size == DELTA_SUBMIT_RECEIPT_V1_SIZE &&
         receipt->reserved == 0U;
}

[[nodiscard]] bool prepare_output(
    delta_output_buffer_t& output,
    std::size_t required) noexcept {
  output.required = required;
  output.written = 0U;
  return output.capacity >= required;
}

[[nodiscard]] bool output_storage_valid(
    const delta_output_buffer_t& output) noexcept {
  return output.required == 0U || output.data != nullptr;
}

[[nodiscard]] delta_status_t record_vote_common(
    delta_runtime_t* runtime,
    canonical::Bytes vote_bytes,
    delta_vote_receipt_v1_t* output) {
  if (runtime == nullptr || runtime->instance == nullptr || !valid_vote_receipt_shape(output)) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  const auto vote = delta::core::protocol::parse_vote(vote_bytes);
  const auto vote_id = canonical::content_id(canonical::Type::vote, vote_bytes);
  const auto required = delta::runtime::vote_receipt_v1_encoded_size(
      vote_bytes.size(), vote_id, vote.context_id);
  if (!prepare_output(output->canonical_receipt, required)) {
    return DELTA_STATUS_BUFFER_TOO_SMALL;
  }
  if (!output_storage_valid(output->canonical_receipt)) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  const auto receipt = runtime->instance->record_vote(std::move(vote_bytes));
  const auto encoded_receipt = delta::runtime::encode_vote_receipt_v1(receipt);
  if (encoded_receipt.size() != required) {
    throw std::logic_error("vote receipt size changed across native admission");
  }
  return copy_output(encoded_receipt, &output->canonical_receipt);
}

[[nodiscard]] delta_status_t submit_common(
    delta_runtime_t* runtime,
    canonical::Bytes command,
    delta_output_buffer_t* effect_output) {
  if (runtime == nullptr || runtime->instance == nullptr || effect_output == nullptr) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  effect_output->required = 0U;
  effect_output->written = 0U;
  const auto receipt = runtime->instance->submit(std::move(command));
  return copy_output(receipt.effect_batch_bytes, effect_output);
}

[[nodiscard]] delta_status_t submit_receipt_common(
    delta_runtime_t* runtime,
    canonical::Bytes command,
    delta_submit_receipt_v1_t* output) {
  if (runtime == nullptr || runtime->instance == nullptr ||
      !valid_submit_receipt_shape(output)) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  const auto receipt = runtime->instance->submit(std::move(command));
  if (receipt.journal_sequence == 0U) {
    throw std::logic_error("native submit receipt has zero journal sequence");
  }
  output->journal_sequence = receipt.journal_sequence;
  return copy_output(receipt.effect_batch_bytes, &output->canonical_effect);
}

}  // namespace

extern "C" {

delta_status_t delta_runtime_descriptor(
    uint32_t caller_struct_size,
    delta_runtime_descriptor_t* output) {
  if (output == nullptr) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  std::memset(output, 0, sizeof(*output));
  if (caller_struct_size != DELTA_ABI_DESCRIPTOR_SIZE) {
    return DELTA_STATUS_ABI_MISMATCH;
  }
  *output = descriptor;
  return DELTA_STATUS_OK;
}

const char* delta_status_message(delta_status_t status) {
  switch (status) {
    case DELTA_STATUS_OK:
      return "OK";
    case DELTA_STATUS_INVALID_ARGUMENT:
      return "INVALID_ARGUMENT";
    case DELTA_STATUS_ABI_MISMATCH:
      return "ABI_MISMATCH";
    case DELTA_STATUS_SCHEMA_MISMATCH:
      return "SCHEMA_MISMATCH";
    case DELTA_STATUS_PROTOCOL_MISMATCH:
      return "PROTOCOL_MISMATCH";
    case DELTA_STATUS_FORMAL_SEMANTICS_MISMATCH:
      return "FORMAL_SEMANTICS_MISMATCH";
    case DELTA_STATUS_BUILD_MISMATCH:
      return "BUILD_MISMATCH";
    case DELTA_STATUS_BUFFER_TOO_SMALL:
      return "BUFFER_TOO_SMALL";
    case DELTA_STATUS_CLOSED:
      return "CLOSED";
    case DELTA_STATUS_QUEUE_FULL:
      return "QUEUE_FULL";
    case DELTA_STATUS_IO_ERROR:
      return "IO_ERROR";
    case DELTA_STATUS_CORRUPT_DURABLE_STATE:
      return "CORRUPT_DURABLE_STATE";
    case DELTA_STATUS_CONFLICT:
      return "CONFLICT";
    case DELTA_STATUS_TRANSITION_REJECTED:
      return "TRANSITION_REJECTED";
    case DELTA_STATUS_INTERNAL_ERROR:
      return "INTERNAL_ERROR";
  }
  return "UNKNOWN_STATUS";
}

delta_status_t delta_runtime_open(
    const delta_runtime_open_options_t* options,
    delta_runtime_t** output) {
  if (output == nullptr) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  *output = nullptr;
  const auto expectation_status = validate_open_options(options);
  if (expectation_status != DELTA_STATUS_OK) {
    return expectation_status;
  }
  return boundary([options, output] {
    auto handle = std::make_unique<delta_runtime>();
    handle->instance = std::make_unique<delta::runtime::Runtime>(delta::runtime::Config{
        .directory = std::filesystem::path(copy_string(options->directory_utf8)),
        .initial_state_bytes = copy_bytes(options->initial_state),
        .submission_capacity = options->submission_capacity,
        .durable_binding_guard = {},
        .vote_policy = {},
        .expected_wal_identity = {},
    });
    *output = handle.release();
    return DELTA_STATUS_OK;
  });
}

delta_status_t delta_runtime_open_with_vote_policy_v1(
    const delta_runtime_open_options_t* options,
    delta_bytes_view_t canonical_vote_policy,
    delta_runtime_t** output) {
  if (output == nullptr) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  *output = nullptr;
  const auto expectation_status = validate_open_options(options);
  if (expectation_status != DELTA_STATUS_OK) {
    return expectation_status;
  }
  if (!valid_view(canonical_vote_policy) ||
      canonical_vote_policy.size > delta::runtime::max_vote_policy_v1_bytes) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  return boundary([options, canonical_vote_policy, output] {
    const auto policy_bytes = copy_bytes(canonical_vote_policy);
    auto handle = std::make_unique<delta_runtime>();
    handle->instance = std::make_unique<delta::runtime::Runtime>(delta::runtime::Config{
        .directory = std::filesystem::path(copy_string(options->directory_utf8)),
        .initial_state_bytes = copy_bytes(options->initial_state),
        .submission_capacity = options->submission_capacity,
        .durable_binding_guard = {},
        .vote_policy = delta::runtime::parse_vote_policy_v1(policy_bytes),
        .expected_wal_identity = {},
    });
    *output = handle.release();
    return DELTA_STATUS_OK;
  });
}

delta_status_t delta_runtime_submit_borrowed(
    delta_runtime_t* runtime,
    delta_bytes_view_t command,
    delta_output_buffer_t* effect_output) {
  reset_output(effect_output);
  return boundary([runtime, command, effect_output] {
    return submit_common(runtime, copy_bytes(command), effect_output);
  });
}

delta_status_t delta_runtime_submit_copy(
    delta_runtime_t* runtime,
    delta_bytes_view_t command,
    delta_output_buffer_t* effect_output) {
  reset_output(effect_output);
  return boundary([runtime, command, effect_output] {
    auto owned_copy = copy_bytes(command);
    return submit_common(runtime, canonical::Bytes(owned_copy), effect_output);
  });
}

delta_status_t delta_runtime_submit_receipt_borrowed_v1(
    delta_runtime_t* runtime,
    delta_bytes_view_t command,
    delta_submit_receipt_v1_t* receipt) {
  if (!valid_submit_receipt_shape(receipt)) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  reset_submit_receipt(receipt);
  if (!valid_view(command)) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  if (receipt->canonical_effect.capacity > 0U &&
      receipt->canonical_effect.data == nullptr) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  return boundary([runtime, command, receipt] {
    return submit_receipt_common(runtime, copy_bytes(command), receipt);
  });
}

delta_status_t delta_runtime_submit_receipt_copy_v1(
    delta_runtime_t* runtime,
    delta_bytes_view_t command,
    delta_submit_receipt_v1_t* receipt) {
  if (!valid_submit_receipt_shape(receipt)) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  reset_submit_receipt(receipt);
  if (!valid_view(command)) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  if (receipt->canonical_effect.capacity > 0U &&
      receipt->canonical_effect.data == nullptr) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  return boundary([runtime, command, receipt] {
    const auto copied = copy_bytes(command);
    return submit_receipt_common(runtime, canonical::Bytes(copied), receipt);
  });
}

delta_status_t delta_runtime_record_vote_borrowed_v1(
    delta_runtime_t* runtime,
    delta_bytes_view_t canonical_vote,
    delta_vote_receipt_v1_t* receipt) {
  if (!valid_vote_receipt_shape(receipt)) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  reset_vote_receipt(receipt);
  if (!valid_view(canonical_vote) ||
      canonical_vote.size > delta::runtime::max_vote_frame_v1_bytes) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  return boundary([runtime, canonical_vote, receipt] {
    return record_vote_common(runtime, copy_bytes(canonical_vote), receipt);
  });
}

delta_status_t delta_runtime_record_vote_copy_v1(
    delta_runtime_t* runtime,
    delta_bytes_view_t canonical_vote,
    delta_vote_receipt_v1_t* receipt) {
  if (!valid_vote_receipt_shape(receipt)) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  reset_vote_receipt(receipt);
  if (!valid_view(canonical_vote) ||
      canonical_vote.size > delta::runtime::max_vote_frame_v1_bytes) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  return boundary([runtime, canonical_vote, receipt] {
    const auto copied = copy_bytes(canonical_vote);
    return record_vote_common(runtime, canonical::Bytes(copied), receipt);
  });
}

delta_status_t delta_runtime_state(
    delta_runtime_t* runtime,
    delta_output_buffer_t* state_output) {
  reset_output(state_output);
  return boundary([runtime, state_output] {
    if (runtime == nullptr || runtime->instance == nullptr || state_output == nullptr) {
      return DELTA_STATUS_INVALID_ARGUMENT;
    }
    const auto state = runtime->instance->state_bytes();
    return copy_output(state, state_output);
  });
}

delta_status_t delta_runtime_snapshot(delta_runtime_t* runtime) {
  return boundary([runtime] {
    if (runtime == nullptr || runtime->instance == nullptr) {
      return DELTA_STATUS_INVALID_ARGUMENT;
    }
    runtime->instance->snapshot();
    return DELTA_STATUS_OK;
  });
}

delta_status_t delta_runtime_release(delta_runtime_t** runtime) {
  return boundary([runtime] {
    if (runtime == nullptr) {
      return DELTA_STATUS_INVALID_ARGUMENT;
    }
    delete *runtime;
    *runtime = nullptr;
    return DELTA_STATUS_OK;
  });
}

}  // extern "C"
