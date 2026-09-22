#include <delta/runtime/sidecar_directory_lock.hpp>

#include <cerrno>
#include <system_error>
#include <utility>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <fcntl.h>
#include <sys/file.h>
#include <sys/stat.h>
#include <unistd.h>
#endif

namespace delta::runtime::sidecar {
namespace {

[[noreturn]] void reject(
    DurableDirectoryLockErrorCode code,
    const char* message) {
  throw DurableDirectoryLockError(code, message);
}

[[nodiscard]] bool contains_embedded_nul(
    const std::filesystem::path& path) {
  const auto& native = path.native();
  return native.find(std::filesystem::path::value_type{}) !=
         native.npos;
}

void validate_directory(const std::filesystem::path& directory) {
  if (directory.empty() || contains_embedded_nul(directory)) {
    reject(
        DurableDirectoryLockErrorCode::invalid_directory,
        "sidecar durable directory path is invalid");
  }

  std::error_code error;
  const auto status = std::filesystem::status(directory, error);
  if (error) {
    if (error == std::errc::no_such_file_or_directory) {
      reject(
          DurableDirectoryLockErrorCode::directory_not_found,
          "sidecar durable directory does not exist");
    }
    reject(
        DurableDirectoryLockErrorCode::directory_status_failed,
        "sidecar durable directory status failed");
  }
  if (!std::filesystem::exists(status)) {
    reject(
        DurableDirectoryLockErrorCode::directory_not_found,
        "sidecar durable directory does not exist");
  }
  if (!std::filesystem::is_directory(status)) {
    reject(
        DurableDirectoryLockErrorCode::not_a_directory,
        "sidecar durable path is not a directory");
  }
}

}  // namespace

DurableDirectoryLockError::DurableDirectoryLockError(
    DurableDirectoryLockErrorCode code,
    std::string message)
    : std::runtime_error(std::move(message)), code_(code) {}

DurableDirectoryLockErrorCode DurableDirectoryLockError::code() const noexcept {
  return code_;
}

class DurableDirectoryLock::Impl {
 public:
  Impl(
      const std::filesystem::path& durable_directory,
      const std::filesystem::path& lock_path) {
#if defined(_WIN32)
    static_cast<void>(durable_directory);
    handle_ = CreateFileW(
        lock_path.c_str(),
        GENERIC_READ | GENERIC_WRITE,
        0,
        nullptr,
        OPEN_ALWAYS,
        FILE_ATTRIBUTE_NORMAL,
        nullptr);
    if (handle_ == INVALID_HANDLE_VALUE) {
      const auto error = GetLastError();
      if (error == ERROR_SHARING_VIOLATION || error == ERROR_LOCK_VIOLATION) {
        reject(
            DurableDirectoryLockErrorCode::lock_unavailable,
            "sidecar durable directory is already locked");
      }
      reject(
          DurableDirectoryLockErrorCode::lock_open_failed,
          "sidecar lock file open failed");
    }
#else
    int directory_flags = O_RDONLY;
#if defined(O_DIRECTORY)
    directory_flags |= O_DIRECTORY;
#endif
#if defined(O_CLOEXEC)
    directory_flags |= O_CLOEXEC;
#endif
#if defined(O_NOFOLLOW)
    directory_flags |= O_NOFOLLOW;
#endif
    do {
      directory_descriptor_ = ::open(durable_directory.c_str(), directory_flags);
    } while (directory_descriptor_ < 0 && errno == EINTR);
    if (directory_descriptor_ < 0) {
      reject(
          DurableDirectoryLockErrorCode::lock_open_failed,
          "sidecar durable directory lock open failed");
    }

    struct stat directory_status {};
    if (::fstat(directory_descriptor_, &directory_status) != 0 ||
        !S_ISDIR(directory_status.st_mode)) {
      release();
      reject(
          DurableDirectoryLockErrorCode::lock_open_failed,
          "sidecar durable directory lock open failed");
    }

    int directory_lock_result = 0;
    do {
      directory_lock_result = ::flock(directory_descriptor_, LOCK_EX | LOCK_NB);
    } while (directory_lock_result != 0 && errno == EINTR);
    if (directory_lock_result != 0) {
      const auto error = errno;
      release();
      if (error == EWOULDBLOCK || error == EAGAIN) {
        reject(
            DurableDirectoryLockErrorCode::lock_unavailable,
            "sidecar durable directory is already locked");
      }
      reject(
          DurableDirectoryLockErrorCode::lock_operation_failed,
          "sidecar directory lock operation failed");
    }

    int flags = O_RDWR | O_CREAT;
#if defined(O_CLOEXEC)
    flags |= O_CLOEXEC;
#endif
#if defined(O_NOFOLLOW)
    flags |= O_NOFOLLOW;
#endif
    do {
      descriptor_ = ::open(lock_path.c_str(), flags, S_IRUSR | S_IWUSR);
    } while (descriptor_ < 0 && errno == EINTR);
    if (descriptor_ < 0) {
      release();
      reject(
          DurableDirectoryLockErrorCode::lock_open_failed,
          "sidecar lock file open failed");
    }

    struct stat status {};
    if (::fstat(descriptor_, &status) != 0 || !S_ISREG(status.st_mode) ||
        status.st_nlink != 1) {
      release();
      reject(
          DurableDirectoryLockErrorCode::lock_open_failed,
          "sidecar lock file open failed");
    }

    int result = 0;
    do {
      result = ::flock(descriptor_, LOCK_EX | LOCK_NB);
    } while (result != 0 && errno == EINTR);
    if (result != 0) {
      const auto error = errno;
      release();
      if (error == EWOULDBLOCK || error == EAGAIN) {
        reject(
            DurableDirectoryLockErrorCode::lock_unavailable,
            "sidecar durable directory is already locked");
      }
      reject(
          DurableDirectoryLockErrorCode::lock_operation_failed,
          "sidecar directory lock operation failed");
    }
#endif
  }

  void prepare_runtime_wal(const std::filesystem::path& wal_path) {
#if defined(_WIN32)
    const auto wal_handle = CreateFileW(
        wal_path.c_str(),
        GENERIC_READ | GENERIC_WRITE,
        FILE_SHARE_READ,
        nullptr,
        OPEN_ALWAYS,
        FILE_ATTRIBUTE_NORMAL | FILE_FLAG_OPEN_REPARSE_POINT |
            FILE_FLAG_WRITE_THROUGH,
        nullptr);
    if (wal_handle == INVALID_HANDLE_VALUE) {
      reject(
          DurableDirectoryLockErrorCode::lock_operation_failed,
          "sidecar runtime WAL durability preflight failed");
    }
    BY_HANDLE_FILE_INFORMATION status{};
    const auto valid = GetFileType(wal_handle) == FILE_TYPE_DISK &&
                       GetFileInformationByHandle(wal_handle, &status) != 0 &&
                       (status.dwFileAttributes &
                        (FILE_ATTRIBUTE_DIRECTORY | FILE_ATTRIBUTE_REPARSE_POINT)) == 0U &&
                       status.nNumberOfLinks == 1U;
    const auto flushed = valid && FlushFileBuffers(wal_handle) != 0;
    const auto closed = CloseHandle(wal_handle) != 0;
    if (!valid || !flushed || !closed) {
      reject(
          DurableDirectoryLockErrorCode::lock_operation_failed,
          "sidecar runtime WAL durability preflight failed");
    }
#else
    static_cast<void>(wal_path);
    int flags = O_RDWR | O_CREAT;
#if defined(O_CLOEXEC)
    flags |= O_CLOEXEC;
#endif
#if defined(O_NOFOLLOW)
    flags |= O_NOFOLLOW;
#endif
    int wal_descriptor = -1;
    do {
      wal_descriptor = ::openat(
          directory_descriptor_, runtime_wal_filename.data(), flags,
          S_IRUSR | S_IWUSR);
    } while (wal_descriptor < 0 && errno == EINTR);
    if (wal_descriptor < 0) {
      reject(
          DurableDirectoryLockErrorCode::lock_operation_failed,
          "sidecar runtime WAL durability preflight failed");
    }

    struct stat wal_status {};
    const auto valid = ::fstat(wal_descriptor, &wal_status) == 0 &&
                       S_ISREG(wal_status.st_mode) && wal_status.st_nlink == 1;
    int wal_sync_result = -1;
    if (valid) {
      do {
        wal_sync_result = ::fsync(wal_descriptor);
      } while (wal_sync_result != 0 && errno == EINTR);
    }
    const auto wal_close_result = ::close(wal_descriptor);
    if (!valid || wal_sync_result != 0 || wal_close_result != 0) {
      reject(
          DurableDirectoryLockErrorCode::lock_operation_failed,
          "sidecar runtime WAL durability preflight failed");
    }

    int directory_sync_result = -1;
    do {
      directory_sync_result = ::fsync(directory_descriptor_);
    } while (directory_sync_result != 0 && errno == EINTR);
    if (directory_sync_result != 0) {
      reject(
          DurableDirectoryLockErrorCode::lock_operation_failed,
          "sidecar runtime WAL durability preflight failed");
    }
#endif
  }

  ~Impl() { release(); }

  Impl(const Impl&) = delete;
  Impl& operator=(const Impl&) = delete;

  [[nodiscard]] bool owns_lock() const noexcept {
#if defined(_WIN32)
    return handle_ != INVALID_HANDLE_VALUE;
#else
    return descriptor_ >= 0 && directory_descriptor_ >= 0;
#endif
  }

 private:
  void release() noexcept {
#if defined(_WIN32)
    if (handle_ != INVALID_HANDLE_VALUE) {
      static_cast<void>(CloseHandle(handle_));
      handle_ = INVALID_HANDLE_VALUE;
    }
#else
    if (descriptor_ >= 0) {
      static_cast<void>(::flock(descriptor_, LOCK_UN));
      static_cast<void>(::close(descriptor_));
      descriptor_ = -1;
    }
    if (directory_descriptor_ >= 0) {
      static_cast<void>(::flock(directory_descriptor_, LOCK_UN));
      static_cast<void>(::close(directory_descriptor_));
      directory_descriptor_ = -1;
    }
#endif
  }

#if defined(_WIN32)
  HANDLE handle_ = INVALID_HANDLE_VALUE;
#else
  int descriptor_ = -1;
  int directory_descriptor_ = -1;
#endif
};

DurableDirectoryLock::DurableDirectoryLock(
    const std::filesystem::path& durable_directory)
    : durable_directory_(durable_directory),
      lock_path_(durable_directory_ /
                 std::filesystem::path(durable_directory_lock_filename)) {
  validate_directory(durable_directory_);
  impl_ = std::make_unique<Impl>(durable_directory_, lock_path_);
}

DurableDirectoryLock::~DurableDirectoryLock() noexcept = default;

bool DurableDirectoryLock::owns_lock() const noexcept {
  return impl_ != nullptr && impl_->owns_lock();
}

const std::filesystem::path& DurableDirectoryLock::durable_directory() const noexcept {
  return durable_directory_;
}

const std::filesystem::path& DurableDirectoryLock::path() const noexcept {
  return lock_path_;
}

void DurableDirectoryLock::prepare_runtime_wal() {
  if (!owns_lock()) {
    reject(
        DurableDirectoryLockErrorCode::lock_operation_failed,
        "sidecar runtime WAL durability preflight failed");
  }
  impl_->prepare_runtime_wal(
      durable_directory_ / std::filesystem::path(runtime_wal_filename));
}

}  // namespace delta::runtime::sidecar
