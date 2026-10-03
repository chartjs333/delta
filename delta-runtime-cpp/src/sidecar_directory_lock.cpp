#include <delta/runtime/sidecar_directory_lock.hpp>

#include <cerrno>
#include <string>
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

[[nodiscard]] std::filesystem::path absolute_normalized(
    const std::filesystem::path& path) {
  if (path.empty() || contains_embedded_nul(path)) {
    return path;
  }
  std::error_code error;
  auto result = std::filesystem::absolute(path, error);
  return error ? path : result.lexically_normal();
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

#if !defined(_WIN32)
class UniqueDescriptor final {
 public:
  explicit UniqueDescriptor(int descriptor = -1) noexcept
      : descriptor_(descriptor) {}
  ~UniqueDescriptor() noexcept {
    if (descriptor_ >= 0) {
      static_cast<void>(::close(descriptor_));
    }
  }

  UniqueDescriptor(const UniqueDescriptor&) = delete;
  UniqueDescriptor& operator=(const UniqueDescriptor&) = delete;

  UniqueDescriptor(UniqueDescriptor&& other) noexcept
      : descriptor_(std::exchange(other.descriptor_, -1)) {}
  UniqueDescriptor& operator=(UniqueDescriptor&& other) noexcept {
    if (this != &other) {
      if (descriptor_ >= 0) {
        static_cast<void>(::close(descriptor_));
      }
      descriptor_ = std::exchange(other.descriptor_, -1);
    }
    return *this;
  }

  [[nodiscard]] int get() const noexcept { return descriptor_; }
  [[nodiscard]] int release() noexcept {
    return std::exchange(descriptor_, -1);
  }

 private:
  int descriptor_;
};

#if defined(O_NOFOLLOW)
[[nodiscard]] int directory_open_flags() noexcept {
  int flags = O_RDONLY;
#if defined(O_DIRECTORY)
  flags |= O_DIRECTORY;
#endif
#if defined(O_CLOEXEC)
  flags |= O_CLOEXEC;
#endif
#if defined(O_NOFOLLOW)
  flags |= O_NOFOLLOW;
#endif
  return flags;
}
#endif

[[nodiscard]] int open_directory_componentwise(
    const std::filesystem::path& directory,
    DurableDirectoryLockErrorCode error_code,
    const char* error_message) {
#if !defined(O_NOFOLLOW)
  static_cast<void>(directory);
  reject(error_code, error_message);
#else
  if (!directory.is_absolute()) {
    reject(error_code, error_message);
  }
  const auto flags = directory_open_flags();
  UniqueDescriptor current;
  int descriptor = -1;
  do {
    descriptor = ::open(directory.root_path().c_str(), flags);
  } while (descriptor < 0 && errno == EINTR);
  current = UniqueDescriptor(descriptor);
  if (current.get() < 0) {
    reject(error_code, error_message);
  }

  for (const auto& component : directory.relative_path()) {
    const auto name = component.string();
    if (name.empty() || name == "." || name == "..") {
      reject(error_code, error_message);
    }
    int next_descriptor = -1;
    do {
      next_descriptor = ::openat(current.get(), name.c_str(), flags);
    } while (next_descriptor < 0 && errno == EINTR);
    UniqueDescriptor next(next_descriptor);
    if (next.get() < 0) {
      reject(error_code, error_message);
    }
    struct stat status {};
    if (::fstat(next.get(), &status) != 0 || !S_ISDIR(status.st_mode)) {
      reject(error_code, error_message);
    }
    current = std::move(next);
  }
  return current.release();
#endif
}
#endif

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
      const std::filesystem::path& lock_path,
      std::optional<DurableDirectoryIdentity> expected_identity) {
#if defined(_WIN32)
    static_cast<void>(durable_directory);
    static_cast<void>(expected_identity);
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
    static_cast<void>(lock_path);
    directory_descriptor_ = open_directory_componentwise(
        durable_directory,
        DurableDirectoryLockErrorCode::lock_open_failed,
        "sidecar durable directory lock open failed");

    struct stat directory_status {};
    if (::fstat(directory_descriptor_, &directory_status) != 0 ||
        !S_ISDIR(directory_status.st_mode)) {
      release();
      reject(
          DurableDirectoryLockErrorCode::lock_open_failed,
          "sidecar durable directory lock open failed");
    }
    identity_ = DurableDirectoryIdentity{
        static_cast<std::uint64_t>(directory_status.st_dev),
        static_cast<std::uint64_t>(directory_status.st_ino),
    };
    if (expected_identity.has_value() && *expected_identity != identity_) {
      release();
      reject(
          DurableDirectoryLockErrorCode::lock_operation_failed,
          "sidecar durable directory identity mismatch");
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

    const auto descriptor_text = std::to_string(directory_descriptor_);
#if defined(__linux__)
    runtime_directory_ = std::filesystem::path("/proc/self/fd") / descriptor_text;
#else
    runtime_directory_ = std::filesystem::path("/dev/fd") / descriptor_text;
#endif
    struct stat runtime_directory_status {};
    if (::stat(runtime_directory_.c_str(), &runtime_directory_status) != 0 ||
        !S_ISDIR(runtime_directory_status.st_mode) ||
        runtime_directory_status.st_dev != directory_status.st_dev ||
        runtime_directory_status.st_ino != directory_status.st_ino) {
      release();
      reject(
          DurableDirectoryLockErrorCode::lock_operation_failed,
          "sidecar descriptor-relative durable directory is unavailable");
    }

    int flags = O_RDWR | O_CREAT;
#if defined(O_CLOEXEC)
    flags |= O_CLOEXEC;
#endif
#if defined(O_NOFOLLOW)
    flags |= O_NOFOLLOW;
#endif
    do {
      descriptor_ = ::openat(
          directory_descriptor_, durable_directory_lock_filename.data(), flags,
          S_IRUSR | S_IWUSR);
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
    UniqueDescriptor candidate;
    if (wal_descriptor_ < 0) {
      int descriptor = -1;
      do {
        descriptor = ::openat(
            directory_descriptor_, runtime_wal_filename.data(), flags,
            S_IRUSR | S_IWUSR);
      } while (descriptor < 0 && errno == EINTR);
      candidate = UniqueDescriptor(descriptor);
      if (candidate.get() < 0) {
        reject(
            DurableDirectoryLockErrorCode::lock_operation_failed,
            "sidecar runtime WAL durability preflight failed");
      }

      struct stat wal_status {};
      if (::fstat(candidate.get(), &wal_status) != 0 ||
          !S_ISREG(wal_status.st_mode) || wal_status.st_nlink != 1) {
        reject(
            DurableDirectoryLockErrorCode::lock_operation_failed,
            "sidecar runtime WAL durability preflight failed");
      }
      wal_identity_ = DurableDirectoryIdentity{
          static_cast<std::uint64_t>(wal_status.st_dev),
          static_cast<std::uint64_t>(wal_status.st_ino),
      };
      require_runtime_wal_binding(candidate.get(), wal_identity_);
    }
    const auto descriptor =
        wal_descriptor_ >= 0 ? wal_descriptor_ : candidate.get();
    const auto identity = wal_identity_;

    int wal_sync_result = -1;
    do {
      wal_sync_result = ::fsync(descriptor);
    } while (wal_sync_result != 0 && errno == EINTR);
    if (wal_sync_result != 0) {
      reject(
          DurableDirectoryLockErrorCode::lock_operation_failed,
          "sidecar runtime WAL durability preflight failed");
    }
    require_runtime_wal_binding(descriptor, identity);

    int directory_sync_result = -1;
    do {
      directory_sync_result = ::fsync(directory_descriptor_);
    } while (directory_sync_result != 0 && errno == EINTR);
    if (directory_sync_result != 0) {
      reject(
          DurableDirectoryLockErrorCode::lock_operation_failed,
          "sidecar runtime WAL durability preflight failed");
    }
    require_runtime_wal_binding(descriptor, identity);
    if (wal_descriptor_ < 0) {
      wal_descriptor_ = candidate.release();
    }
#endif
  }

  void verify_runtime_wal_binding() const {
#if defined(_WIN32)
    return;
#else
    if (wal_descriptor_ < 0) {
      reject(
          DurableDirectoryLockErrorCode::lock_operation_failed,
          "sidecar runtime WAL binding is unavailable");
    }
    require_runtime_wal_binding(wal_descriptor_, wal_identity_);
#endif
  }

  [[nodiscard]] std::optional<DurableDirectoryIdentity> runtime_wal_identity()
      const noexcept {
#if defined(_WIN32)
    return std::nullopt;
#else
    if (wal_descriptor_ < 0) {
      return std::nullopt;
    }
    return wal_identity_;
#endif
  }

  void verify_path_binding(const std::filesystem::path& durable_directory) const {
#if defined(_WIN32)
    static_cast<void>(durable_directory);
#else
    struct stat descriptor_status {};
    if (::fstat(directory_descriptor_, &descriptor_status) != 0 ||
        !S_ISDIR(descriptor_status.st_mode) ||
        static_cast<std::uint64_t>(descriptor_status.st_dev) != identity_.device ||
        static_cast<std::uint64_t>(descriptor_status.st_ino) != identity_.inode) {
      reject(
          DurableDirectoryLockErrorCode::lock_operation_failed,
          "sidecar durable directory pathname binding changed");
    }

    UniqueDescriptor rebound_descriptor(open_directory_componentwise(
        durable_directory,
        DurableDirectoryLockErrorCode::lock_operation_failed,
        "sidecar durable directory pathname binding changed"));
    struct stat rebound_status {};
    const auto valid = ::fstat(rebound_descriptor.get(), &rebound_status) == 0 &&
                       S_ISDIR(rebound_status.st_mode) &&
                       static_cast<std::uint64_t>(rebound_status.st_dev) == identity_.device &&
                       static_cast<std::uint64_t>(rebound_status.st_ino) == identity_.inode;
    if (!valid) {
      reject(
          DurableDirectoryLockErrorCode::lock_operation_failed,
          "sidecar durable directory pathname binding changed");
    }
#endif
  }

  [[nodiscard]] DurableDirectoryIdentity identity() const noexcept {
    return identity_;
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

  [[nodiscard]] const std::filesystem::path& runtime_directory(
      const std::filesystem::path& durable_directory) const noexcept {
#if defined(_WIN32)
    return durable_directory;
#else
    static_cast<void>(durable_directory);
    return runtime_directory_;
#endif
  }

 private:
#if !defined(_WIN32)
  void require_runtime_wal_binding(
      int descriptor,
      DurableDirectoryIdentity expected) const {
    struct stat descriptor_status {};
    struct stat named_status {};
    const auto valid =
        ::fstat(descriptor, &descriptor_status) == 0 &&
        S_ISREG(descriptor_status.st_mode) && descriptor_status.st_nlink == 1 &&
        ::fstatat(
            directory_descriptor_,
            runtime_wal_filename.data(),
            &named_status,
            AT_SYMLINK_NOFOLLOW) == 0 &&
        S_ISREG(named_status.st_mode) && named_status.st_nlink == 1 &&
        static_cast<std::uint64_t>(descriptor_status.st_dev) == expected.device &&
        static_cast<std::uint64_t>(descriptor_status.st_ino) == expected.inode &&
        named_status.st_dev == descriptor_status.st_dev &&
        named_status.st_ino == descriptor_status.st_ino;
    if (!valid) {
      reject(
          DurableDirectoryLockErrorCode::lock_operation_failed,
          "sidecar runtime WAL binding changed");
    }
  }
#endif

  void release() noexcept {
#if defined(_WIN32)
    if (handle_ != INVALID_HANDLE_VALUE) {
      static_cast<void>(CloseHandle(handle_));
      handle_ = INVALID_HANDLE_VALUE;
    }
#else
    if (wal_descriptor_ >= 0) {
      static_cast<void>(::close(wal_descriptor_));
      wal_descriptor_ = -1;
    }
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
  int wal_descriptor_ = -1;
  std::filesystem::path runtime_directory_;
  DurableDirectoryIdentity wal_identity_{0U, 0U};
#endif
  DurableDirectoryIdentity identity_{0U, 0U};
};

DurableDirectoryLock::DurableDirectoryLock(
    const std::filesystem::path& durable_directory,
    std::optional<DurableDirectoryIdentity> expected_identity)
    : durable_directory_(absolute_normalized(durable_directory)),
      lock_path_(durable_directory_ /
                 std::filesystem::path(durable_directory_lock_filename)) {
  validate_directory(durable_directory_);
  impl_ = std::make_unique<Impl>(durable_directory_, lock_path_, expected_identity);
  runtime_directory_ = impl_->runtime_directory(durable_directory_);
  verify_path_binding();
}

DurableDirectoryLock::~DurableDirectoryLock() noexcept = default;

bool DurableDirectoryLock::owns_lock() const noexcept {
  return impl_ != nullptr && impl_->owns_lock();
}

const std::filesystem::path& DurableDirectoryLock::durable_directory() const noexcept {
  return durable_directory_;
}

const std::filesystem::path& DurableDirectoryLock::runtime_directory() const noexcept {
  return runtime_directory_;
}

const std::filesystem::path& DurableDirectoryLock::path() const noexcept {
  return lock_path_;
}

DurableDirectoryIdentity DurableDirectoryLock::identity() const noexcept {
  return impl_->identity();
}

void DurableDirectoryLock::verify_path_binding() const {
  if (!owns_lock()) {
    reject(
        DurableDirectoryLockErrorCode::lock_operation_failed,
        "sidecar durable directory pathname binding changed");
  }
  impl_->verify_path_binding(durable_directory_);
}

std::optional<DurableDirectoryIdentity>
DurableDirectoryLock::runtime_wal_identity() const noexcept {
  if (impl_ == nullptr) {
    return std::nullopt;
  }
  return impl_->runtime_wal_identity();
}

void DurableDirectoryLock::verify_runtime_wal_binding() const {
  if (!owns_lock()) {
    reject(
        DurableDirectoryLockErrorCode::lock_operation_failed,
        "sidecar runtime WAL binding is unavailable");
  }
  impl_->verify_runtime_wal_binding();
}

void DurableDirectoryLock::prepare_runtime_wal() {
  if (!owns_lock()) {
    reject(
        DurableDirectoryLockErrorCode::lock_operation_failed,
        "sidecar runtime WAL durability preflight failed");
  }
  verify_path_binding();
  impl_->prepare_runtime_wal(
      runtime_directory_ / std::filesystem::path(runtime_wal_filename));
  verify_path_binding();
}

}  // namespace delta::runtime::sidecar
