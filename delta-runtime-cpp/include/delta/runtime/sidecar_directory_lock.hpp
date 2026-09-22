#pragma once

#include <filesystem>
#include <memory>
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
      const std::filesystem::path& durable_directory);
  ~DurableDirectoryLock() noexcept;

  DurableDirectoryLock(const DurableDirectoryLock&) = delete;
  DurableDirectoryLock& operator=(const DurableDirectoryLock&) = delete;
  DurableDirectoryLock(DurableDirectoryLock&&) = delete;
  DurableDirectoryLock& operator=(DurableDirectoryLock&&) = delete;

  [[nodiscard]] bool owns_lock() const noexcept;
  [[nodiscard]] const std::filesystem::path& durable_directory() const noexcept;
  [[nodiscard]] const std::filesystem::path& path() const noexcept;

  // Establishes and durably synchronizes the WAL directory entry before the
  // native runtime can accept a command. The exclusive directory lock must
  // remain held for the entire runtime lifetime.
  void prepare_runtime_wal();

 private:
  class Impl;

  std::filesystem::path durable_directory_;
  std::filesystem::path lock_path_;
  std::unique_ptr<Impl> impl_;
};

}  // namespace delta::runtime::sidecar
