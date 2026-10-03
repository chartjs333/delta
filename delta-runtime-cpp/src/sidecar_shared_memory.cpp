#include <delta/runtime/sidecar_shared_memory.hpp>

#include <algorithm>
#include <array>
#include <atomic>
#include <bit>
#include <cstdlib>
#include <cstring>
#include <limits>
#include <memory>
#include <mutex>
#include <new>
#include <utility>
#include <vector>

#if !defined(_WIN32)
#include <cerrno>
#include <fcntl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>
#endif

namespace delta::runtime::sidecar {
namespace {

[[noreturn]] void reject(const char* message) { throw SharedMemoryError(message); }

void require(bool condition, const char* message) {
  if (!condition) {
    reject(message);
  }
}

template <typename Integer>
[[nodiscard]] Integer read_be(std::span<const std::byte> input, std::size_t offset) {
  static_assert(std::is_unsigned_v<Integer>);
  require(offset <= input.size() && sizeof(Integer) <= input.size() - offset,
          "shared-memory integer is truncated");
  Integer result = 0U;
  for (std::size_t index = 0U; index < sizeof(Integer); ++index) {
    result = static_cast<Integer>(
        (result << 8U) | std::to_integer<std::uint8_t>(input[offset + index]));
  }
  return result;
}

template <typename Integer>
void write_be(std::span<std::byte> output, std::size_t offset, Integer value) {
  static_assert(std::is_unsigned_v<Integer>);
  require(offset <= output.size() && sizeof(Integer) <= output.size() - offset,
          "shared-memory integer write is out of bounds");
  for (std::size_t index = 0U; index < sizeof(Integer); ++index) {
    const auto shift = static_cast<unsigned>((sizeof(Integer) - index - 1U) * 8U);
    output[offset + index] =
        static_cast<std::byte>((value >> shift) & static_cast<Integer>(0xffU));
  }
}

[[nodiscard]] std::uint32_t atomic_encoding(SharedMemoryState state) noexcept {
  const auto value = static_cast<std::uint32_t>(state);
  if constexpr (std::endian::native == std::endian::little) {
    return ((value & 0x000000ffU) << 24U) |
           ((value & 0x0000ff00U) << 8U) |
           ((value & 0x00ff0000U) >> 8U) |
           ((value & 0xff000000U) >> 24U);
  } else {
    return value;
  }
}

// mmap is not a C++ allocation expression, so it does not by itself begin the
// lifetime of the uint32_t object required by atomic_ref.  Preserve the exact
// Java-authored big-endian representation in a live uint32_t, then explicitly
// start a uint32_t at the suitably aligned mapped address with that value.
[[nodiscard]] std::uint32_t* begin_mapped_atomic_lifetime(
    std::span<std::byte> record) noexcept {
  std::uint32_t representation = 0U;
  std::memcpy(&representation, record.data(), sizeof(representation));
  return std::construct_at(
      reinterpret_cast<std::uint32_t*>(record.data()), representation);
}

[[nodiscard]] SharedMemoryState decode_atomic(std::uint32_t encoded) {
  for (const auto state : {
           SharedMemoryState::free,
           SharedMemoryState::writing,
           SharedMemoryState::published,
           SharedMemoryState::reading,
           SharedMemoryState::acknowledged,
           SharedMemoryState::rejected,
       }) {
    if (encoded == atomic_encoding(state)) {
      return state;
    }
  }
  reject("shared-memory control state is invalid");
}

[[nodiscard]] bool checked_range(std::uint64_t offset, std::uint64_t length) noexcept {
  return offset >= shared_memory_control_prefix_bytes && length != 0U &&
         offset <= shared_memory_region_bytes &&
         length <= shared_memory_region_bytes - offset;
}

[[nodiscard]] std::uint64_t align64(std::uint64_t value) {
  constexpr std::uint64_t alignment = 64U;
  require(value <= std::numeric_limits<std::uint64_t>::max() - (alignment - 1U),
          "shared-memory offset alignment overflow");
  return (value + alignment - 1U) & ~(alignment - 1U);
}

void rewrite_flags(Bytes& frame, std::uint32_t flags) {
  require(frame.size() >= header_bytes, "shared-memory carrier header is truncated");
  write_be<std::uint32_t>(frame, 16U, flags);
}

}  // namespace

Bytes encode_shared_memory_reference(const SharedMemoryReference& reference) {
  require(reference.slot < shared_memory_slot_count, "shared-memory slot is out of bounds");
  require(reference.generation != 0U, "shared-memory generation is zero");
  require(checked_range(reference.offset, reference.length),
          "shared-memory reference range is invalid");
  Bytes result(shared_memory_reference_bytes, std::byte{0});
  write_be(result, 0U, static_cast<std::uint32_t>(reference.region));
  write_be(result, 4U, reference.slot);
  write_be(result, 8U, reference.generation);
  write_be(result, 16U, reference.offset);
  write_be(result, 24U, reference.length);
  std::copy(reference.digest.begin(), reference.digest.end(), result.begin() + 32);
  return result;
}

SharedMemoryReference decode_shared_memory_reference(std::span<const std::byte> bytes) {
  require(bytes.size() == shared_memory_reference_bytes,
          "shared-memory reference has wrong size");
  const auto region_value = read_be<std::uint32_t>(bytes, 0U);
  require(region_value == static_cast<std::uint32_t>(SharedMemoryRegionId::java_to_native) ||
              region_value == static_cast<std::uint32_t>(SharedMemoryRegionId::native_to_java),
          "shared-memory region ID is invalid");
  SharedMemoryReference result{
      static_cast<SharedMemoryRegionId>(region_value),
      read_be<std::uint32_t>(bytes, 4U),
      read_be<std::uint64_t>(bytes, 8U),
      read_be<std::uint64_t>(bytes, 16U),
      read_be<std::uint64_t>(bytes, 24U),
      {},
  };
  std::copy_n(bytes.begin() + 32, result.digest.size(), result.digest.begin());
  require(result.slot < shared_memory_slot_count, "shared-memory slot is out of bounds");
  require(result.generation != 0U, "shared-memory generation is zero");
  require(checked_range(result.offset, result.length),
          "shared-memory reference range is invalid");
  return result;
}

bool probe_shared_memory_atomic_abi() noexcept {
#if defined(_WIN32)
  return false;
#else
  if (!std::atomic_ref<std::uint32_t>::is_always_lock_free) {
    return false;
  }
  constexpr std::size_t mapping_bytes = 4096U;
  void* const mapped = ::mmap(
      nullptr,
      mapping_bytes,
      PROT_READ | PROT_WRITE,
      MAP_SHARED | MAP_ANONYMOUS,
      -1,
      0);
  if (mapped == MAP_FAILED) {
    return false;
  }
  if (reinterpret_cast<std::uintptr_t>(mapped) %
          std::atomic_ref<std::uint32_t>::required_alignment !=
      0U) {
    static_cast<void>(::munmap(mapped, mapping_bytes));
    return false;
  }
  bool supported = false;
  auto* const raw = static_cast<std::byte*>(mapped);
  auto* const word = std::construct_at(
      reinterpret_cast<std::uint32_t*>(mapped),
      atomic_encoding(SharedMemoryState::free));
  try {
    std::atomic_ref<std::uint32_t> atomic(*word);
    if (!atomic.is_lock_free() ||
        !std::all_of(raw, raw + sizeof(std::uint32_t), [](std::byte value) {
          return value == std::byte{0};
        })) {
      throw SharedMemoryError("mapped shared-memory atomic ABI is unavailable");
    }
    const auto child = ::fork();
    if (child == 0) {
      auto expected = atomic_encoding(SharedMemoryState::free);
      const auto changed = atomic.compare_exchange_strong(
          expected,
          atomic_encoding(SharedMemoryState::writing),
          std::memory_order_acq_rel,
          std::memory_order_acquire);
      const std::array<std::byte, 4> expected_bytes{
          std::byte{0}, std::byte{0}, std::byte{0}, std::byte{1}};
      const auto bytes_match = std::equal(expected_bytes.begin(), expected_bytes.end(), raw);
      std::_Exit(changed && bytes_match ? 0 : 3);
    }
    if (child < 0) {
      throw SharedMemoryError("cannot fork shared-memory atomic probe");
    }
    int status = 0;
    while (::waitpid(child, &status, 0) < 0) {
      if (errno != EINTR) {
        throw SharedMemoryError("cannot wait for shared-memory atomic probe");
      }
    }
    const std::array<std::byte, 4> writing_bytes{
        std::byte{0}, std::byte{0}, std::byte{0}, std::byte{1}};
    supported = WIFEXITED(status) && WEXITSTATUS(status) == 0 &&
                atomic.load(std::memory_order_acquire) ==
                    atomic_encoding(SharedMemoryState::writing) &&
                std::equal(writing_bytes.begin(), writing_bytes.end(), raw);
  } catch (...) {
    supported = false;
  }
  std::destroy_at(word);
  static_cast<void>(::munmap(mapped, mapping_bytes));
  return supported;
#endif
}

bool probe_mapped_shared_memory_atomic_abi(
    const std::filesystem::path& path,
    SharedMemoryRegionId region,
    std::uint64_t generation,
    SharedMemoryFileIdentity expected_identity,
    std::uint32_t slot) noexcept {
#if defined(_WIN32)
  static_cast<void>(path);
  static_cast<void>(region);
  static_cast<void>(generation);
  static_cast<void>(expected_identity);
  static_cast<void>(slot);
  return false;
#else
  if (!std::atomic_ref<std::uint32_t>::is_always_lock_free || generation == 0U ||
      slot >= shared_memory_slot_count) {
    return false;
  }
  int flags = O_RDWR;
#if defined(O_CLOEXEC)
  flags |= O_CLOEXEC;
#endif
#if defined(O_NOFOLLOW)
  flags |= O_NOFOLLOW;
#else
  return false;
#endif
  int descriptor = -1;
  do {
    descriptor = ::open(path.c_str(), flags);
  } while (descriptor < 0 && errno == EINTR);
  if (descriptor < 0) {
    return false;
  }

  bool supported = false;
  std::byte* mapping = nullptr;
  struct stat status {};
  const auto shape_matches =
      ::fstat(descriptor, &status) == 0 && S_ISREG(status.st_mode) &&
      status.st_size == static_cast<off_t>(shared_memory_region_bytes) &&
      static_cast<std::uint64_t>(status.st_dev) == expected_identity.device &&
      static_cast<std::uint64_t>(status.st_ino) == expected_identity.inode;
  if (shape_matches) {
    mapping = static_cast<std::byte*>(::mmap(
        nullptr,
        shared_memory_control_prefix_bytes,
        PROT_READ | PROT_WRITE,
        MAP_SHARED,
        descriptor,
        0));
    if (mapping == MAP_FAILED) {
      mapping = nullptr;
    }
  }
  if (mapping != nullptr) {
    const auto record_offset =
        static_cast<std::size_t>(slot) * shared_memory_control_record_bytes;
    auto record = std::span<std::byte>(
        mapping + record_offset, shared_memory_control_record_bytes);
    const std::array<std::byte, 4> writing_bytes{
        std::byte{0}, std::byte{0}, std::byte{0}, std::byte{1}};
    const std::array<std::byte, 4> published_bytes{
        std::byte{0}, std::byte{0}, std::byte{0}, std::byte{2}};
    const auto aligned = reinterpret_cast<std::uintptr_t>(record.data()) %
                             std::atomic_ref<std::uint32_t>::required_alignment ==
                         0U;
    if (aligned) {
      auto* const word = begin_mapped_atomic_lifetime(record);
      std::atomic_ref<std::uint32_t> atomic(*word);
      auto expected = atomic_encoding(SharedMemoryState::writing);
      const auto writing_published_by_java =
          atomic.is_lock_free() &&
          atomic.load(std::memory_order_acquire) == expected &&
          std::equal(writing_bytes.begin(), writing_bytes.end(), record.begin()) &&
          read_be<std::uint32_t>(record, 4U) == static_cast<std::uint32_t>(region) &&
          read_be<std::uint64_t>(record, 8U) == generation &&
          read_be<std::uint32_t>(record, 16U) == slot &&
          std::all_of(record.begin() + 20, record.end(), [](std::byte value) {
            return value == std::byte{0};
          });
      supported = writing_published_by_java &&
                  atomic.compare_exchange_strong(
                      expected,
                      atomic_encoding(SharedMemoryState::published),
                      std::memory_order_acq_rel,
                      std::memory_order_acquire) &&
                  atomic.load(std::memory_order_acquire) ==
                      atomic_encoding(SharedMemoryState::published) &&
                  std::equal(published_bytes.begin(), published_bytes.end(), record.begin());
    }
    static_cast<void>(::munmap(mapping, shared_memory_control_prefix_bytes));
  }
  static_cast<void>(::close(descriptor));
  return supported;
#endif
}

class SharedMemoryRegion::Impl final {
 public:
  Impl(
      const std::filesystem::path& path,
      SharedMemoryRegionId region,
      std::uint64_t generation,
      std::optional<SharedMemoryFileIdentity> expected_identity)
      : region_(region), generation_(generation) {
    require(generation_ != 0U, "shared-memory generation is zero");
#if defined(_WIN32)
    static_cast<void>(path);
    static_cast<void>(expected_identity);
    reject("POSIX shared memory is unavailable on Windows");
#else
    int flags = O_RDWR;
#if defined(O_CLOEXEC)
    flags |= O_CLOEXEC;
#endif
#if defined(O_NOFOLLOW)
    flags |= O_NOFOLLOW;
#endif
    do {
      descriptor_ = ::open(path.c_str(), flags);
    } while (descriptor_ < 0 && errno == EINTR);
    if (descriptor_ < 0) {
      reject("cannot open shared-memory region");
    }
    struct stat status {};
    if (::fstat(descriptor_, &status) != 0 || !S_ISREG(status.st_mode) ||
        status.st_size != static_cast<off_t>(shared_memory_region_bytes)) {
      release();
      reject("shared-memory region file has wrong shape");
    }
    const SharedMemoryFileIdentity actual_identity{
        static_cast<std::uint64_t>(status.st_dev),
        static_cast<std::uint64_t>(status.st_ino),
    };
    if (expected_identity.has_value() && *expected_identity != actual_identity) {
      release();
      reject("shared-memory region identity mismatch");
    }
    mapping_ = static_cast<std::byte*>(::mmap(
        nullptr,
        static_cast<std::size_t>(shared_memory_region_bytes),
        PROT_READ | PROT_WRITE,
        MAP_SHARED,
        descriptor_,
        0));
    if (mapping_ == MAP_FAILED) {
      mapping_ = nullptr;
      release();
      reject("cannot map shared-memory region");
    }
    for (std::uint32_t slot = 0U; slot < shared_memory_slot_count; ++slot) {
      const auto record = control_record(slot);
      if (reinterpret_cast<std::uintptr_t>(record.data()) %
              std::atomic_ref<std::uint32_t>::required_alignment !=
          0U) {
        release();
        reject("shared-memory control state does not satisfy atomic_ref alignment");
      }
      static_cast<void>(begin_mapped_atomic_lifetime(record));
    }
    atomic_supported_ = state_atomic(0U).is_lock_free();
    if (!atomic_supported_) {
      release();
      reject("shared-memory atomic ABI is not lock-free");
    }
    for (std::uint32_t slot = 0U; slot < shared_memory_slot_count; ++slot) {
      const auto record = control_record(slot);
      if (state_atomic(slot).load(std::memory_order_acquire) !=
              atomic_encoding(SharedMemoryState::free) ||
          !std::all_of(record.begin() + 4, record.end(), [](std::byte value) {
            return value == std::byte{0};
          })) {
        release();
        reject("shared-memory control prefix is not fresh");
      }
    }
#endif
  }

  ~Impl() { release(); }

  [[nodiscard]] bool atomic_abi_supported() const noexcept {
    return atomic_supported_;
  }

  [[nodiscard]] SharedMemoryRegionId region() const noexcept { return region_; }
  [[nodiscard]] std::uint64_t generation() const noexcept { return generation_; }

  [[nodiscard]] std::optional<SharedMemoryReference> publish(
      std::span<const std::byte> payload,
      const std::function<void()>& before_publish) {
    std::lock_guard lock(mutex_);
    require(atomic_supported_, "shared-memory atomic ABI is not lock-free");
    require(!payload.empty() && payload.size() <= max_logical_payload_bytes,
            "shared-memory logical payload is outside bounds");
    reclaim_terminal_slots();

    std::optional<std::uint32_t> free_slot;
    std::vector<std::pair<std::uint64_t, std::uint64_t>> occupied;
    for (std::uint32_t slot = 0U; slot < shared_memory_slot_count; ++slot) {
      const auto state = load_state(slot, std::memory_order_acquire);
      if (state == SharedMemoryState::free) {
        if (!free_slot.has_value()) {
          free_slot = slot;
        }
        continue;
      }
      // WRITING metadata is owned exclusively by the producer and is not
      // publication-safe.  A second producer (or corrupt leftover state) must
      // fall back without inspecting a partially initialized record.
      if (state == SharedMemoryState::writing) {
        return std::nullopt;
      }
      const auto record = control_record(slot);
      const auto offset = read_be<std::uint64_t>(record, 24U);
      const auto length = read_be<std::uint64_t>(record, 32U);
      require(checked_range(offset, length), "live shared-memory slot range is invalid");
      occupied.emplace_back(offset, offset + length);
    }
    if (!free_slot.has_value()) {
      return std::nullopt;
    }
    std::sort(occupied.begin(), occupied.end());
    auto previous_end = static_cast<std::uint64_t>(shared_memory_control_prefix_bytes);
    for (const auto& interval : occupied) {
      require(interval.first >= previous_end,
              "live shared-memory slot ranges overlap");
      previous_end = interval.second;
    }
    std::uint64_t offset = shared_memory_control_prefix_bytes;
    for (const auto& interval : occupied) {
      if (interval.first >= offset && payload.size() <= interval.first - offset) {
        break;
      }
      if (interval.second > offset) {
        offset = align64(interval.second);
      }
    }
    const auto length = static_cast<std::uint64_t>(payload.size());
    if (!checked_range(offset, length)) {
      return std::nullopt;
    }

    auto atomic = state_atomic(*free_slot);
    auto expected = atomic_encoding(SharedMemoryState::free);
    if (!atomic.compare_exchange_strong(
            expected,
            atomic_encoding(SharedMemoryState::writing),
            std::memory_order_acq_rel,
            std::memory_order_acquire)) {
      return std::nullopt;
    }
    try {
      const auto digest = sha256(payload);
      auto record = control_record(*free_slot);
      std::fill(record.begin() + 4, record.end(), std::byte{0});
      write_be(record, 4U, static_cast<std::uint32_t>(region_));
      write_be(record, 8U, generation_);
      write_be(record, 16U, *free_slot);
      write_be(record, 24U, offset);
      write_be(record, 32U, length);
      std::copy(digest.begin(), digest.end(), record.begin() + 40);
      std::copy(payload.begin(), payload.end(), mapping_ + offset);
      if (before_publish) {
        before_publish();
      }
      atomic.store(atomic_encoding(SharedMemoryState::published), std::memory_order_release);
      return SharedMemoryReference{region_, *free_slot, generation_, offset, length, digest};
    } catch (...) {
      atomic.store(atomic_encoding(SharedMemoryState::rejected), std::memory_order_release);
      throw;
    }
  }

  [[nodiscard]] Bytes consume(const SharedMemoryReference& reference) {
    std::lock_guard lock(mutex_);
    require(atomic_supported_, "shared-memory atomic ABI is not lock-free");
    require(reference.region == region_, "shared-memory reference region mismatch");
    require(reference.generation == generation_, "shared-memory reference generation mismatch");
    require(reference.slot < shared_memory_slot_count, "shared-memory slot is out of bounds");
    require(checked_range(reference.offset, reference.length),
            "shared-memory reference range is invalid");
    auto atomic = state_atomic(reference.slot);
    auto expected = atomic_encoding(SharedMemoryState::published);
    require(
        atomic.compare_exchange_strong(
            expected,
            atomic_encoding(SharedMemoryState::reading),
            std::memory_order_acq_rel,
            std::memory_order_acquire),
        "shared-memory slot is not published");
    try {
      const auto record = control_record(reference.slot);
      require(read_be<std::uint32_t>(record, 4U) ==
                  static_cast<std::uint32_t>(reference.region) &&
                  read_be<std::uint64_t>(record, 8U) == reference.generation &&
                  read_be<std::uint32_t>(record, 16U) == reference.slot &&
                  read_be<std::uint32_t>(record, 20U) == 0U &&
                  read_be<std::uint64_t>(record, 24U) == reference.offset &&
                  read_be<std::uint64_t>(record, 32U) == reference.length &&
                  std::equal(reference.digest.begin(), reference.digest.end(), record.begin() + 40) &&
                  std::all_of(record.begin() + 72, record.end(), [](std::byte value) {
                    return value == std::byte{0};
                  }),
              "shared-memory reference differs from control record");
      // The frozen region has exactly one serialized producer.  That producer
      // validates all stable live ranges before reserving a slot.  A consumer
      // must not scan unrelated records: another slot may be WRITING, or a
      // terminal record may be reclaimed, while its metadata is being read.
      Bytes result(
          mapping_ + reference.offset,
          mapping_ + reference.offset + reference.length);
      require(sha256(result) == reference.digest,
              "shared-memory logical payload digest mismatch");
      atomic.store(
          atomic_encoding(SharedMemoryState::acknowledged), std::memory_order_release);
      return result;
    } catch (...) {
      atomic.store(atomic_encoding(SharedMemoryState::rejected), std::memory_order_release);
      throw;
    }
  }

  [[nodiscard]] SharedMemoryNotificationMatch classify_terminal_notification(
      const SharedMemoryReference& reference,
      SharedMemoryDisposition disposition) {
    std::lock_guard lock(mutex_);
    require(reference.region == region_, "shared-memory notification region mismatch");
    require(reference.generation == generation_,
            "shared-memory notification generation mismatch");
    require(reference.slot < shared_memory_slot_count,
            "shared-memory notification slot is out of bounds");
    require(checked_range(reference.offset, reference.length),
            "shared-memory notification range is invalid");
    const auto expected_state = disposition == SharedMemoryDisposition::acknowledged
                                    ? SharedMemoryState::acknowledged
                                    : SharedMemoryState::rejected;
    const auto state = load_state(reference.slot, std::memory_order_acquire);
    if (state == SharedMemoryState::free || state == SharedMemoryState::writing) {
      return SharedMemoryNotificationMatch::reclaimed;
    }
    const auto record = control_record(reference.slot);
    const auto exact =
        read_be<std::uint32_t>(record, 4U) ==
            static_cast<std::uint32_t>(reference.region) &&
        read_be<std::uint64_t>(record, 8U) == reference.generation &&
        read_be<std::uint32_t>(record, 16U) == reference.slot &&
        read_be<std::uint32_t>(record, 20U) == 0U &&
        read_be<std::uint64_t>(record, 24U) == reference.offset &&
        read_be<std::uint64_t>(record, 32U) == reference.length &&
        std::equal(reference.digest.begin(), reference.digest.end(), record.begin() + 40) &&
        std::all_of(record.begin() + 72, record.end(), [](std::byte value) {
          return value == std::byte{0};
        });
    if (!exact) {
      return SharedMemoryNotificationMatch::reclaimed;
    }
    return state == expected_state ? SharedMemoryNotificationMatch::matched
                                   : SharedMemoryNotificationMatch::mismatch;
  }

 private:
  [[nodiscard]] std::span<std::byte> control_record(std::uint32_t slot) const {
    return {mapping_ + (static_cast<std::size_t>(slot) * shared_memory_control_record_bytes),
            shared_memory_control_record_bytes};
  }

  [[nodiscard]] std::atomic_ref<std::uint32_t> state_atomic(std::uint32_t slot) const {
    auto* state = reinterpret_cast<std::uint32_t*>(
        mapping_ + (static_cast<std::size_t>(slot) * shared_memory_control_record_bytes));
    return std::atomic_ref<std::uint32_t>(*state);
  }

  [[nodiscard]] SharedMemoryState load_state(
      std::uint32_t slot, std::memory_order order) const {
    return decode_atomic(state_atomic(slot).load(order));
  }

  void reclaim_terminal_slots() {
    for (std::uint32_t slot = 0U; slot < shared_memory_slot_count; ++slot) {
      auto atomic = state_atomic(slot);
      const auto state = decode_atomic(atomic.load(std::memory_order_acquire));
      if (state == SharedMemoryState::acknowledged || state == SharedMemoryState::rejected) {
        auto record = control_record(slot);
        std::fill(record.begin() + 4, record.end(), std::byte{0});
        atomic.store(atomic_encoding(SharedMemoryState::free), std::memory_order_release);
      }
    }
  }

  void release() noexcept {
#if !defined(_WIN32)
    if (mapping_ != nullptr) {
      static_cast<void>(::munmap(
          mapping_, static_cast<std::size_t>(shared_memory_region_bytes)));
      mapping_ = nullptr;
    }
    if (descriptor_ >= 0) {
      static_cast<void>(::close(descriptor_));
      descriptor_ = -1;
    }
#endif
  }

  SharedMemoryRegionId region_;
  std::uint64_t generation_;
  std::byte* mapping_ = nullptr;
  bool atomic_supported_ = false;
  std::mutex mutex_;
#if !defined(_WIN32)
  int descriptor_ = -1;
#endif
};

SharedMemoryRegion::SharedMemoryRegion(
    const std::filesystem::path& path,
    SharedMemoryRegionId region,
    std::uint64_t generation,
    std::optional<SharedMemoryFileIdentity> expected_identity)
    : impl_(std::make_unique<Impl>(path, region, generation, expected_identity)) {}

SharedMemoryRegion::~SharedMemoryRegion() noexcept = default;

bool SharedMemoryRegion::atomic_abi_supported() const noexcept {
  return impl_->atomic_abi_supported();
}

SharedMemoryRegionId SharedMemoryRegion::region() const noexcept {
  return impl_->region();
}

std::uint64_t SharedMemoryRegion::generation() const noexcept {
  return impl_->generation();
}

std::optional<SharedMemoryReference> SharedMemoryRegion::publish(
    std::span<const std::byte> logical_payload,
    const std::function<void()>& before_publish) {
  return impl_->publish(logical_payload, before_publish);
}

Bytes SharedMemoryRegion::consume(const SharedMemoryReference& reference) {
  return impl_->consume(reference);
}

SharedMemoryNotificationMatch SharedMemoryRegion::classify_terminal_notification(
    const SharedMemoryReference& reference,
    SharedMemoryDisposition disposition) {
  return impl_->classify_terminal_notification(reference, disposition);
}

std::optional<Bytes> make_shared_memory_carrier(
    std::span<const std::byte> canonical_inline_frame,
    SharedMemoryRegion& producer,
    const std::function<void()>& before_publish) {
  const auto inline_frame = decode_frame(canonical_inline_frame);
  if (!shared_memory_eligible(inline_frame.type)) {
    return std::nullopt;
  }
  const auto expected_region = is_request(inline_frame.type)
                                   ? SharedMemoryRegionId::java_to_native
                                   : SharedMemoryRegionId::native_to_java;
  require(producer.region() == expected_region,
          "shared-memory producer region has wrong direction");
  require(producer.generation() == inline_frame.generation,
          "shared-memory producer generation mismatch");
  const auto reference = producer.publish(inline_frame.payload, before_publish);
  if (!reference.has_value()) {
    return std::nullopt;
  }
  Bytes result(canonical_inline_frame.begin(), canonical_inline_frame.begin() + header_bytes);
  rewrite_flags(result, shared_memory_flags(inline_frame.type));
  const auto encoded_reference = encode_shared_memory_reference(*reference);
  result.insert(result.end(), encoded_reference.begin(), encoded_reference.end());
  return result;
}

Bytes resolve_shared_memory_carrier(
    std::span<const std::byte> carrier,
    SharedMemoryRegion& consumer) {
  require(carrier.size() == header_bytes + shared_memory_reference_bytes,
          "shared-memory carrier has wrong size");
  const auto header = decode_frame_header(carrier.first(header_bytes));
  require((header.flags & flag_payload_shared_memory) != 0U,
          "carrier is not shared memory");
  const auto reference = decode_shared_memory_reference(carrier.subspan(header_bytes));
  const auto expected_region = is_request(header.type)
                                   ? SharedMemoryRegionId::java_to_native
                                   : SharedMemoryRegionId::native_to_java;
  require(consumer.region() == expected_region && reference.region == expected_region,
          "shared-memory consumer region has wrong direction");
  require(consumer.generation() == header.generation &&
              reference.generation == header.generation,
          "shared-memory carrier generation mismatch");
  require(reference.length == header.payload_length &&
              reference.digest == header.payload_sha256,
          "shared-memory reference differs from frame header");
  auto payload = consumer.consume(reference);
  Bytes result(carrier.begin(), carrier.begin() + header_bytes);
  rewrite_flags(result, inline_flags(header.type));
  result.insert(result.end(), payload.begin(), payload.end());
  static_cast<void>(decode_frame(result));
  return result;
}

}  // namespace delta::runtime::sidecar
