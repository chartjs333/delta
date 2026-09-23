#pragma once

#include <delta/runtime/sidecar_protocol.hpp>
#include <delta/runtime/sidecar_shared_memory.hpp>

#include <algorithm>
#include <optional>
#include <span>

namespace delta::runtime::sidecar::detail {

struct PublishedSharedMemoryNotification {
  SharedMemoryReference reference;
  Id128 correlation_id;
  Bytes request_id;
  Digest request_digest;
  bool notified = false;
  std::optional<SharedMemoryDisposition> disposition;
};

enum class SharedMemoryNotificationOwnership {
  stale,
  current,
  conflict,
};

// Correlations are unique for the whole sidecar session. A notification whose
// correlation has no live publication is therefore stale even when a reclaimed
// slot has been reused for byte-identical payload bytes. A live correlation has
// authority over exactly one reference/request owner and any mismatch is fatal.
[[nodiscard]] inline SharedMemoryNotificationOwnership classify_notification_ownership(
    std::span<const std::optional<PublishedSharedMemoryNotification>> publications,
    const SharedMemoryReference& reference,
    const Id128& correlation_id,
    const Bytes& request_id,
    const Digest& request_digest) noexcept {
  const auto current = std::find_if(
      publications.begin(),
      publications.end(),
      [&correlation_id](const auto& candidate) {
        return candidate.has_value() && candidate->correlation_id == correlation_id;
      });
  if (current == publications.end()) {
    return SharedMemoryNotificationOwnership::stale;
  }
  if (current->value().reference != reference ||
      current->value().request_id != request_id ||
      current->value().request_digest != request_digest) {
    return SharedMemoryNotificationOwnership::conflict;
  }
  return SharedMemoryNotificationOwnership::current;
}

}  // namespace delta::runtime::sidecar::detail
