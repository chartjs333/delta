#include "sidecar_qualification_fsync_interposer.h"

#if !defined(__linux__)
#error "The qualification fsync interposer is Linux-only"
#endif

#include <sys/stat.h>
#include <sys/syscall.h>
#include <unistd.h>

#include <atomic>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <limits>

namespace {

constexpr int qualification_exit_code = 86;
constexpr char runtime_wal_suffix[] = "/runtime.wal";

std::atomic<bool> crash_claimed{false};
std::atomic<bool> crash_enabled{false};

[[nodiscard]] const char* configured_target() noexcept {
  const auto* target = std::getenv(DELTA_SIDECAR_QUALIFICATION_FSYNC_TARGET_ENV);
  if (target == nullptr || target[0] != '/') {
    return nullptr;
  }
  const auto length = std::strlen(target);
  constexpr auto suffix_length = sizeof(runtime_wal_suffix) - 1U;
  if (length < suffix_length ||
      std::memcmp(target + length - suffix_length, runtime_wal_suffix, suffix_length) != 0) {
    return nullptr;
  }
  return target;
}

[[nodiscard]] bool target_matches(int descriptor) noexcept {
  const auto* target = configured_target();
  if (target == nullptr) {
    return false;
  }
  struct stat descriptor_status {};
  struct stat target_status {};
  if (::fstat(descriptor, &descriptor_status) != 0 ||
      ::stat(target, &target_status) != 0) {
    return false;
  }
  return S_ISREG(descriptor_status.st_mode) && S_ISREG(target_status.st_mode) &&
         descriptor_status.st_dev == target_status.st_dev &&
         descriptor_status.st_ino == target_status.st_ino;
}

[[noreturn]] void crash_before_barrier() noexcept {
  static_cast<void>(crash_claimed.exchange(true, std::memory_order_relaxed));
  ::_exit(qualification_exit_code);
}

[[nodiscard]] int real_fsync(int descriptor) noexcept {
  return static_cast<int>(::syscall(SYS_fsync, descriptor));
}

[[nodiscard]] int real_fdatasync(int descriptor) noexcept {
#if defined(SYS_fdatasync)
  return static_cast<int>(::syscall(SYS_fdatasync, descriptor));
#else
  return real_fsync(descriptor);
#endif
}

}  // namespace

extern "C" uint32_t delta_sidecar_qualification_fsync_interposer_armed_v1(
    const std::uint8_t* expected_runtime_wal_utf8,
    std::uint64_t expected_runtime_wal_utf8_length) noexcept {
  const auto* target = configured_target();
  if (target == nullptr || expected_runtime_wal_utf8 == nullptr ||
      expected_runtime_wal_utf8_length > std::numeric_limits<std::size_t>::max()) {
    return 0U;
  }
  const auto expected_size = static_cast<std::size_t>(expected_runtime_wal_utf8_length);
  return std::strlen(target) == expected_size &&
                 std::memcmp(target, expected_runtime_wal_utf8, expected_size) == 0
             ? 1U
             : 0U;
}

extern "C" uint32_t delta_sidecar_qualification_fsync_interposer_arm_v1(
    const std::uint8_t* expected_runtime_wal_utf8,
    std::uint64_t expected_runtime_wal_utf8_length) noexcept {
  if (delta_sidecar_qualification_fsync_interposer_armed_v1(
          expected_runtime_wal_utf8, expected_runtime_wal_utf8_length) != 1U ||
      crash_claimed.load(std::memory_order_relaxed)) {
    return 0U;
  }
  crash_enabled.store(true, std::memory_order_release);
  return 1U;
}

extern "C" __attribute__((visibility("default"))) int fsync(int descriptor) {
  if (crash_enabled.load(std::memory_order_acquire) && target_matches(descriptor)) {
    crash_before_barrier();
  }
  return real_fsync(descriptor);
}

extern "C" __attribute__((visibility("default"))) int fdatasync(int descriptor) {
  if (crash_enabled.load(std::memory_order_acquire) && target_matches(descriptor)) {
    crash_before_barrier();
  }
  return real_fdatasync(descriptor);
}
