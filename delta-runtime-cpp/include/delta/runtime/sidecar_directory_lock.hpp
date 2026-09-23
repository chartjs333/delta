#pragma once

#include <cstdint>
#include <filesystem>
#include <memory>
#include <optional>
#include <stdexcept>
#include <string>
#include <string_view>

namespace delta::runtime::sidecar {

inline constexpr std::string_view durable_directory_lock_filename =
    ".delta-sidecar.lock";
inline constexpr std::string_view runtime_wal_filename = "runtime.wal";

enum class DurableDirectoryLockErrorCode {
  invalid_directory,
  directory_not_found,
  not_a_directory,
  directory_status_failed,
  lock_open_failed,
  lock_unavailable,
  lock_operation_failed,
};

struct DurableDirectoryIdentity {
  std::uint64_t device;
  std::uint64_t inode;

  bool operator==(const DurableDirectoryIdentity&) const = default;
};

class DurableDirectoryLockError final : public std::runtime_error {
 public:
  DurableDirectoryLockError(
      DurableDirectoryLockErrorCode code,
      std::string message);

  [[nodiscard]] DurableDirectoryLockErrorCode code() const noexcept;

 private:
  DurableDirectoryLockErrorCode code_;
};

// Holds the operating-system lock until destruction. The object is deliberately
// nonmovable so a session cannot accidentally transfer or outlive its durable
// runtime ownership boundary.
class DurableDirectoryLock final {
 public:
  explicit DurableDirectoryLock(
      const std::filesystem::path& durable_directory,
      std::optional<DurableDirectoryIdentity> expected_identity = std::nullopt);
  ~DurableDirectoryLock() noexcept;

  DurableDirectoryLock(const DurableDirectoryLock&) = delete;
  DurableDirectoryLock& operator=(const DurableDirectoryLock&) = delete;
  DurableDirectoryLock(DurableDirectoryLock&&) = delete;
  DurableDirectoryLock& operator=(DurableDirectoryLock&&) = delete;

  [[nodiscard]] bool owns_lock() const noexcept;
  [[nodiscard]] const std::filesystem::path& durable_directory() const noexcept;
  // Path used by the native runtime while this lock is alive. On POSIX this is
  // a descriptor-anchored procfd/devfd alias (for example /proc/self/fd/N), so
  // renaming or replacing
  // the caller-supplied pathname cannot redirect later WAL/snapshot operations
  // away from the directory inode that was validated and locked.
  [[nodiscard]] const std::filesystem::path& runtime_directory() const noexcept;
  [[nodiscard]] const std::filesystem::path& path() const noexcept;
  [[nodiscard]] DurableDirectoryIdentity identity() const noexcept;
  void verify_path_binding() const;

  // Present on POSIX after prepare_runtime_wal(). The descriptor that owns
  // this identity stays open until the lock is destroyed so Runtime recovery
  // can be bound to the exact preflighted inode.
  [[nodiscard]] std::optional<DurableDirectoryIdentity> runtime_wal_identity()
      const noexcept;
  void verify_runtime_wal_binding() const;

  // Establishes and durably synchronizes the WAL directory entry before the
  // native runtime can accept a command. The exclusive directory lock must
  // remain held for the entire runtime lifetime.
  void prepare_runtime_wal();

 private:
  class Impl;

  std::filesystem::path durable_directory_;
  std::filesystem::path runtime_directory_;
  std::filesystem::path lock_path_;
  std::unique_ptr<Impl> impl_;
};

}  // namespace delta::runtime::sidecar
