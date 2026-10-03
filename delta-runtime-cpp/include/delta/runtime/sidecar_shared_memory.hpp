#pragma once

#include <delta/runtime/sidecar_protocol.hpp>

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <functional>
#include <memory>
#include <optional>
#include <span>
#include <stdexcept>

namespace delta::runtime::sidecar {

inline constexpr std::size_t shared_memory_reference_bytes = 64U;
inline constexpr std::size_t shared_memory_control_record_bytes = 128U;
inline constexpr std::size_t shared_memory_slot_count = 64U;
inline constexpr std::size_t shared_memory_control_prefix_bytes = 8192U;
inline constexpr std::uint64_t shared_memory_region_bytes = 1ULL << 30U;

enum class SharedMemoryRegionId : std::uint32_t {
  java_to_native = 1U,
  native_to_java = 2U,
};

enum class SharedMemoryState : std::uint32_t {
  free = 0U,
  writing = 1U,
  published = 2U,
  reading = 3U,
  acknowledged = 4U,
  rejected = 5U,
};

enum class SharedMemoryDisposition : std::uint8_t {
  acknowledged = 1U,
  rejected_digest = 2U,
  rejected_stale = 3U,
  rejected_bounds = 4U,
};

enum class SharedMemoryNotificationMatch : std::uint8_t {
  matched = 1U,
  reclaimed = 2U,
  mismatch = 3U,
};

struct SharedMemoryReference {
  SharedMemoryRegionId region;
  std::uint32_t slot;
  std::uint64_t generation;
  std::uint64_t offset;
  std::uint64_t length;
  Digest digest;

  bool operator==(const SharedMemoryReference&) const = default;
};

struct SharedMemoryFileIdentity {
  std::uint64_t device;
  std::uint64_t inode;

  bool operator==(const SharedMemoryFileIdentity&) const = default;
};

class SharedMemoryError final : public std::runtime_error {
 public:
  using std::runtime_error::runtime_error;
};

[[nodiscard]] Bytes encode_shared_memory_reference(
    const SharedMemoryReference& reference);
[[nodiscard]] SharedMemoryReference decode_shared_memory_reference(
    std::span<const std::byte> bytes);
[[nodiscard]] bool probe_shared_memory_atomic_abi() noexcept;
// Proves the Java VarHandle/native atomic_ref ABI against the exact generation
// mapping before the sidecar protocol process is launched. The Java producer
// prepares slot zero as WRITING with exact region/generation metadata; native
// validates the pinned file and CASes it to PUBLISHED.
[[nodiscard]] bool probe_mapped_shared_memory_atomic_abi(
    const std::filesystem::path& path,
    SharedMemoryRegionId region,
    std::uint64_t generation,
    SharedMemoryFileIdentity expected_identity,
    std::uint32_t slot = 0U) noexcept;

// One mapped, single-producer/single-consumer region. The producer and consumer
// still synchronize every slot through the frozen interprocess atomic state.
class SharedMemoryRegion final {
 public:
  SharedMemoryRegion(
      const std::filesystem::path& path,
      SharedMemoryRegionId region,
      std::uint64_t generation,
      std::optional<SharedMemoryFileIdentity> expected_identity = std::nullopt);
  ~SharedMemoryRegion() noexcept;

  SharedMemoryRegion(const SharedMemoryRegion&) = delete;
  SharedMemoryRegion& operator=(const SharedMemoryRegion&) = delete;
  SharedMemoryRegion(SharedMemoryRegion&&) = delete;
  SharedMemoryRegion& operator=(SharedMemoryRegion&&) = delete;

  [[nodiscard]] bool atomic_abi_supported() const noexcept;
  [[nodiscard]] SharedMemoryRegionId region() const noexcept;
  [[nodiscard]] std::uint64_t generation() const noexcept;
  [[nodiscard]] std::optional<SharedMemoryReference> publish(
      std::span<const std::byte> logical_payload,
      const std::function<void()>& before_publish = {});
  [[nodiscard]] Bytes consume(const SharedMemoryReference& reference);
  // Classifies a terminal notification while holding the producer lock.  The
  // implementation never reads metadata from a WRITING record and therefore
  // cannot race a producer that is initializing a reused slot.
  [[nodiscard]] SharedMemoryNotificationMatch classify_terminal_notification(
      const SharedMemoryReference& reference,
      SharedMemoryDisposition disposition);

 private:
  class Impl;
  std::unique_ptr<Impl> impl_;
};

// Carrier helpers are intentionally reusable by every opcode (including future
// vote operations): upper layers always operate on canonical inline frames.
[[nodiscard]] std::optional<Bytes> make_shared_memory_carrier(
    std::span<const std::byte> canonical_inline_frame,
    SharedMemoryRegion& producer,
    const std::function<void()>& before_publish = {});
[[nodiscard]] Bytes resolve_shared_memory_carrier(
    std::span<const std::byte> carrier,
    SharedMemoryRegion& consumer);

}  // namespace delta::runtime::sidecar
