#include <delta_abi.h>

#include <delta/shards/reader.hpp>

#include <cstddef>
#include <cstdint>
#include <new>
#include <span>
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

[[nodiscard]] delta_status_t validate_and_copy(
    std::span<const std::byte> envelope,
    delta_output_buffer_t* output) {
  if (output == nullptr) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  delta::shards::validate_opaque_shard(envelope);
  output->required = envelope.size();
  if (output->capacity < envelope.size()) {
    return DELTA_STATUS_BUFFER_TOO_SMALL;
  }
  if (!envelope.empty() && output->data == nullptr) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  for (std::size_t index = 0U; index < envelope.size(); ++index) {
    output->data[index] = std::to_integer<std::uint8_t>(envelope[index]);
  }
  output->written = envelope.size();
  return DELTA_STATUS_OK;
}

template <typename Operation>
[[nodiscard]] delta_status_t boundary(Operation operation) noexcept {
  try {
    return operation();
  } catch (const delta::shards::ShardError&) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  } catch (const std::bad_alloc&) {
    return DELTA_STATUS_INTERNAL_ERROR;
  } catch (...) {
    return DELTA_STATUS_INTERNAL_ERROR;
  }
}

}  // namespace

extern "C" {

delta_status_t delta_fixedpoint_shard_validate_borrowed(
    delta_bytes_view_t envelope,
    delta_output_buffer_t* envelope_output) {
  reset_output(envelope_output);
  return boundary([&]() {
    if (!valid_view(envelope)) {
      return DELTA_STATUS_INVALID_ARGUMENT;
    }
    return validate_and_copy(
        std::as_bytes(std::span(envelope.data, envelope.size)), envelope_output);
  });
}

delta_status_t delta_fixedpoint_shard_validate_copy(
    delta_bytes_view_t envelope,
    delta_output_buffer_t* envelope_output) {
  reset_output(envelope_output);
  return boundary([&]() {
    if (!valid_view(envelope)) {
      return DELTA_STATUS_INVALID_ARGUMENT;
    }
    const auto borrowed = std::as_bytes(std::span(envelope.data, envelope.size));
    delta::shards::validate_opaque_shard(borrowed);
    std::vector<std::byte> owned;
    owned.reserve(envelope.size);
    for (std::size_t index = 0U; index < envelope.size; ++index) {
      owned.push_back(static_cast<std::byte>(envelope.data[index]));
    }
    return validate_and_copy(owned, envelope_output);
  });
}

}  // extern "C"
