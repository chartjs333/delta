#include "wal.hpp"

#include <delta/runtime/runtime.hpp>

#include <algorithm>
#include <array>
#include <cerrno>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <limits>
#include <optional>
#include <span>
#include <string>
#include <string_view>
#include <system_error>
#include <utility>

#ifdef _WIN32
#include <io.h>
#include <windows.h>
#else
#include <fcntl.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>
#endif

namespace delta::runtime::detail {
namespace {

using core::canonical::Bytes;

constexpr std::array<std::byte, 4> wal_magic = {
    std::byte{'D'}, std::byte{'R'}, std::byte{'W'}, std::byte{'1'}};
constexpr std::array<std::byte, 4> snapshot_magic = {
    std::byte{'D'}, std::byte{'R'}, std::byte{'S'}, std::byte{'1'}};
constexpr std::uint16_t format_version = 1U;
constexpr std::size_t wal_header_size = 12U;
constexpr std::size_t digest_size = 32U;
constexpr std::size_t maximum_frame_size = 64U * 1024U * 1024U;
constexpr std::size_t minimum_frame_size = wal_header_size + 12U + (4U * 4U) + digest_size;

[[noreturn]] void reject(ErrorCode code, std::string message) {
  throw RuntimeError(code, std::move(message));
}

void require(bool condition, ErrorCode code, const char* message) {
  if (!condition) {
    reject(code, message);
  }
}

void append_u8(Bytes& output, std::uint8_t value) {
  output.push_back(static_cast<std::byte>(value));
}

void append_u16(Bytes& output, std::uint16_t value) {
  append_u8(output, static_cast<std::uint8_t>((value >> 8U) & 0xffU));
  append_u8(output, static_cast<std::uint8_t>(value & 0xffU));
}

void append_u32(Bytes& output, std::uint32_t value) {
  for (unsigned int shift = 24U;; shift -= 8U) {
    append_u8(output, static_cast<std::uint8_t>((value >> shift) & 0xffU));
    if (shift == 0U) {
      break;
    }
  }
}

void append_u64(Bytes& output, std::uint64_t value) {
  for (unsigned int shift = 56U;; shift -= 8U) {
    append_u8(output, static_cast<std::uint8_t>((value >> shift) & 0xffU));
    if (shift == 0U) {
      break;
    }
  }
}

void replace_u32(Bytes& output, std::size_t offset, std::uint32_t value) {
  for (std::size_t index = 0; index < 4U; ++index) {
    const auto shift = static_cast<unsigned int>((3U - index) * 8U);
    output[offset + index] = static_cast<std::byte>((value >> shift) & 0xffU);
  }
}

[[nodiscard]] std::uint32_t checked_u32(std::size_t value) {
  require(value <= UINT32_MAX, ErrorCode::io_error, "runtime record exceeds u32");
  return static_cast<std::uint32_t>(value);
}

[[nodiscard]] std::uint8_t hex_nibble(char value) {
  if (value >= '0' && value <= '9') {
    return static_cast<std::uint8_t>(value - '0');
  }
  if (value >= 'a' && value <= 'f') {
    return static_cast<std::uint8_t>(value - 'a' + 10);
  }
  reject(ErrorCode::io_error, "invalid digest returned by canonical SHA-256");
}

[[nodiscard]] Bytes decode_digest(std::string_view digest) {
  require(digest.size() == 64U, ErrorCode::io_error, "invalid SHA-256 digest length");
  Bytes result;
  result.reserve(digest_size);
  for (std::size_t index = 0; index < digest.size(); index += 2U) {
    const auto value = static_cast<std::uint8_t>(
        static_cast<std::uint8_t>(hex_nibble(digest[index]) << 4U) |
        hex_nibble(digest[index + 1U]));
    result.push_back(static_cast<std::byte>(value));
  }
  return result;
}

[[nodiscard]] std::string encode_digest(std::span<const std::byte> digest) {
  constexpr char digits[] = "0123456789abcdef";
  require(digest.size() == digest_size, ErrorCode::wal_corrupt, "invalid digest byte length");
  std::string result;
  result.reserve(64U);
  for (const auto byte : digest) {
    const auto value = std::to_integer<std::uint8_t>(byte);
    result.push_back(digits[value >> 4U]);
    result.push_back(digits[value & 0x0fU]);
  }
  return result;
}

template <std::size_t Size>
[[nodiscard]] bool equals(
    std::span<const std::byte> value,
    const std::array<std::byte, Size>& expected) {
  return value.size() == expected.size() &&
         std::equal(value.begin(), value.end(), expected.begin());
}

void append_section(Bytes& output, std::span<const std::byte> section) {
  append_u32(output, checked_u32(section.size()));
  output.insert(output.end(), section.begin(), section.end());
}

[[nodiscard]] Bytes encode_entry(const JournalEntry& entry) {
  Bytes output(wal_magic.begin(), wal_magic.end());
  append_u16(output, format_version);
  append_u16(output, 0U);
  const auto frame_size_offset = output.size();
  append_u32(output, 0U);
  append_u64(output, entry.sequence);
  append_u8(output, static_cast<std::uint8_t>(entry.kind));
  append_u8(output, 0U);
  append_u8(output, 0U);
  append_u8(output, 0U);
  append_section(output, entry.command_or_vote_bytes);
  append_section(output, entry.next_state_bytes);
  append_section(output, entry.effect_batch_bytes);
  append_section(output, entry.wal_record_bytes);
  const auto total_size = checked_u32(output.size() + digest_size);
  replace_u32(output, frame_size_offset, total_size);
  const auto checksum = decode_digest(core::canonical::sha256_hex(output));
  output.insert(output.end(), checksum.begin(), checksum.end());
  return output;
}

class Reader {
 public:
  explicit Reader(std::span<const std::byte> bytes) : bytes_(bytes) {}

  [[nodiscard]] std::size_t remaining() const noexcept { return bytes_.size() - cursor_; }
  [[nodiscard]] std::size_t position() const noexcept { return cursor_; }

  [[nodiscard]] std::uint8_t u8() {
    require(remaining() >= 1U, ErrorCode::wal_corrupt, "truncated runtime u8");
    return std::to_integer<std::uint8_t>(bytes_[cursor_++]);
  }

  [[nodiscard]] std::uint16_t u16() {
    return static_cast<std::uint16_t>((static_cast<std::uint16_t>(u8()) << 8U) | u8());
  }

  [[nodiscard]] std::uint32_t u32() {
    std::uint32_t value = 0U;
    for (std::size_t index = 0; index < 4U; ++index) {
      value = (value << 8U) | u8();
    }
    return value;
  }

  [[nodiscard]] std::uint64_t u64() {
    std::uint64_t value = 0U;
    for (std::size_t index = 0; index < 8U; ++index) {
      value = (value << 8U) | u8();
    }
    return value;
  }

  [[nodiscard]] std::span<const std::byte> take(std::size_t count) {
    require(count <= remaining(), ErrorCode::wal_corrupt, "truncated runtime bytes");
    const auto result = bytes_.subspan(cursor_, count);
    cursor_ += count;
    return result;
  }

  [[nodiscard]] Bytes section() {
    const auto value = take(u32());
    return Bytes(value.begin(), value.end());
  }

 private:
  std::span<const std::byte> bytes_;
  std::size_t cursor_ = 0U;
};

[[nodiscard]] JournalEntry decode_entry(std::span<const std::byte> frame) {
  require(frame.size() >= minimum_frame_size, ErrorCode::wal_corrupt, "runtime frame too small");
  const auto checksum_offset = frame.size() - digest_size;
  require(
      core::canonical::sha256_hex(frame.first(checksum_offset)) ==
          encode_digest(frame.subspan(checksum_offset)),
      ErrorCode::wal_corrupt,
      "runtime frame checksum mismatch");
  Reader reader(frame.first(checksum_offset));
  require(
      equals(reader.take(wal_magic.size()), wal_magic),
      ErrorCode::wal_corrupt,
      "runtime WAL magic mismatch");
  require(reader.u16() == format_version, ErrorCode::wal_corrupt, "runtime WAL version mismatch");
  require(reader.u16() == 0U, ErrorCode::wal_corrupt, "runtime WAL flags are nonzero");
  require(reader.u32() == frame.size(), ErrorCode::wal_corrupt, "runtime frame length mismatch");
  const auto sequence = reader.u64();
  const auto kind_raw = reader.u8();
  require(reader.u8() == 0U && reader.u8() == 0U && reader.u8() == 0U,
          ErrorCode::wal_corrupt,
          "runtime record reserved bytes are nonzero");
  require(
      kind_raw == static_cast<std::uint8_t>(JournalKind::transition) ||
          kind_raw == static_cast<std::uint8_t>(JournalKind::vote),
      ErrorCode::wal_corrupt,
      "runtime journal kind is unknown");
  JournalEntry entry{
      sequence,
      static_cast<JournalKind>(kind_raw),
      reader.section(),
      reader.section(),
      reader.section(),
      reader.section(),
  };
  require(reader.remaining() == 0U, ErrorCode::wal_corrupt, "runtime frame has trailing bytes");
  if (entry.kind == JournalKind::transition) {
    require(
        !entry.command_or_vote_bytes.empty() && !entry.next_state_bytes.empty() &&
            !entry.effect_batch_bytes.empty() && !entry.wal_record_bytes.empty(),
        ErrorCode::wal_corrupt,
        "transition journal entry is incomplete");
  } else {
    require(
        !entry.command_or_vote_bytes.empty() && entry.next_state_bytes.empty() &&
            entry.effect_batch_bytes.empty(),
        ErrorCode::wal_corrupt,
        "vote journal entry contains state/effect bytes");
  }
  return entry;
}

#ifdef _WIN32

[[nodiscard]] Bytes read_file(const std::filesystem::path& path, ErrorCode code) {
  std::ifstream input(path, std::ios::binary);
  if (!input.good()) {
    reject(code, "cannot open runtime durable file");
  }
  const std::vector<char> characters{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  Bytes result;
  result.reserve(characters.size());
  for (const unsigned char character : characters) {
    result.push_back(static_cast<std::byte>(character));
  }
  return result;
}

void sync_file(std::FILE* file) {
  require(std::fflush(file) == 0, ErrorCode::io_error, "runtime file flush failed");
  require(_commit(_fileno(file)) == 0, ErrorCode::io_error, "runtime file commit failed");
}

[[nodiscard]] std::FILE* open_file(const std::filesystem::path& path, const char* mode) {
  std::FILE* file = nullptr;
  static_cast<void>(fopen_s(&file, path.string().c_str(), mode));
  return file;
}

void append_file(const std::filesystem::path& path, std::span<const std::byte> bytes) {
  auto* file = open_file(path, "ab");
  if (file == nullptr) {
    reject(ErrorCode::io_error, "cannot open runtime WAL for append");
  }
  const auto close_file = [&file] { static_cast<void>(std::fclose(file)); };
  if (!bytes.empty() && std::fwrite(bytes.data(), 1U, bytes.size(), file) != bytes.size()) {
    close_file();
    reject(ErrorCode::io_error, "runtime WAL append failed");
  }
  try {
    sync_file(file);
  } catch (...) {
    close_file();
    throw;
  }
  if (std::fclose(file) != 0) {
    reject(ErrorCode::io_error, "runtime WAL close failed");
  }
}

#else

class UniqueFd final {
 public:
  UniqueFd() = default;
  explicit UniqueFd(int descriptor) noexcept : descriptor_(descriptor) {}
  ~UniqueFd() {
    if (descriptor_ >= 0) {
      static_cast<void>(::close(descriptor_));
    }
  }

  UniqueFd(const UniqueFd&) = delete;
  UniqueFd& operator=(const UniqueFd&) = delete;

  UniqueFd(UniqueFd&& other) noexcept : descriptor_(other.release()) {}
  UniqueFd& operator=(UniqueFd&& other) noexcept {
    if (this != &other) {
      if (descriptor_ >= 0) {
        static_cast<void>(::close(descriptor_));
      }
      descriptor_ = other.release();
    }
    return *this;
  }

  [[nodiscard]] int get() const noexcept { return descriptor_; }
  [[nodiscard]] int release() noexcept {
    const auto result = descriptor_;
    descriptor_ = -1;
    return result;
  }

 private:
  int descriptor_ = -1;
};

struct FileIdentity {
  std::uintmax_t device;
  std::uintmax_t inode;

  bool operator==(const FileIdentity&) const = default;
};

struct OpenDirectory {
  UniqueFd descriptor;
  std::filesystem::path configured_path;
  FileIdentity identity;
};

struct ResolvedDirectoryPath {
  std::filesystem::path normalized;
  bool trusted_descriptor_alias;
};

[[nodiscard]] FileIdentity identity_of(const struct stat& status) noexcept {
  return FileIdentity{
      static_cast<std::uintmax_t>(status.st_dev),
      static_cast<std::uintmax_t>(status.st_ino),
  };
}

[[nodiscard]] std::filesystem::path parent_path_for(
    const std::filesystem::path& path) {
  const auto parent = path.parent_path();
  return parent.empty() ? std::filesystem::path{"."} : parent;
}

[[nodiscard]] std::string leaf_name_for(
    const std::filesystem::path& path,
    ErrorCode code) {
  const auto leaf = path.filename().string();
  require(
      !leaf.empty() && leaf != "." && leaf != "..",
      code,
      "runtime durable leaf name is invalid");
  return leaf;
}

[[nodiscard]] struct stat descriptor_status(
    int descriptor,
    ErrorCode code,
    const char* message) {
  struct stat status {};
  if (::fstat(descriptor, &status) != 0) {
    reject(code, message);
  }
  return status;
}

[[nodiscard]] bool is_exact_descriptor_alias(std::string_view path) noexcept {
  constexpr std::array<std::string_view, 2> prefixes = {
      "/proc/self/fd/",
      "/dev/fd/",
  };
  for (const auto prefix : prefixes) {
    if (!path.starts_with(prefix)) {
      continue;
    }
    const auto descriptor = path.substr(prefix.size());
    return !descriptor.empty() &&
           std::all_of(descriptor.begin(), descriptor.end(), [](char value) {
             return value >= '0' && value <= '9';
           });
  }
  return false;
}

[[nodiscard]] ResolvedDirectoryPath resolve_directory_path(
    const std::filesystem::path& path,
    ErrorCode code) {
  std::error_code error;
  const auto absolute = std::filesystem::absolute(path, error);
  if (error) {
    reject(code, "cannot resolve runtime durable directory path");
  }
  const auto normalized = absolute.lexically_normal();
  require(
      normalized.is_absolute(), code, "runtime durable directory path is not absolute");
  const auto trusted_descriptor_alias =
      absolute == normalized && is_exact_descriptor_alias(normalized.generic_string());
  return ResolvedDirectoryPath{normalized, trusted_descriptor_alias};
}

[[nodiscard]] UniqueFd open_resolved_directory(
    const ResolvedDirectoryPath& path,
    ErrorCode code) {
  constexpr int flags = O_RDONLY | O_DIRECTORY | O_CLOEXEC;
  if (path.trusted_descriptor_alias) {
    UniqueFd descriptor(::open(path.normalized.c_str(), flags));
    if (descriptor.get() < 0) {
      reject(code, "cannot open trusted runtime directory descriptor alias");
    }
    return descriptor;
  }

  UniqueFd descriptor(::open(path.normalized.root_path().c_str(), flags | O_NOFOLLOW));
  if (descriptor.get() < 0) {
    reject(code, "cannot open runtime durable filesystem root");
  }
  for (const auto& component : path.normalized.relative_path()) {
    const auto name = component.string();
    require(
        !name.empty() && name != "." && name != "..",
        code,
        "runtime durable directory path contains an invalid component");
    UniqueFd next(::openat(descriptor.get(), name.c_str(), flags | O_NOFOLLOW));
    if (next.get() < 0) {
      reject(code, "runtime durable directory path contains a link or is unavailable");
    }
    descriptor = std::move(next);
  }
  return descriptor;
}

void verify_directory_binding(
    int descriptor,
    const std::filesystem::path& configured_path,
    FileIdentity expected,
    ErrorCode code) {
  const auto descriptor_value =
      descriptor_status(descriptor, code, "runtime durable directory descriptor is invalid");
  const auto resolved = resolve_directory_path(configured_path, code);
  const auto reopened = open_resolved_directory(resolved, code);
  const auto path_value = descriptor_status(
      reopened.get(), code, "runtime durable directory binding is unavailable");
  require(
      S_ISDIR(descriptor_value.st_mode) && S_ISDIR(path_value.st_mode) &&
          identity_of(descriptor_value) == expected && identity_of(path_value) == expected,
      code,
      "runtime durable directory binding changed");
}

[[nodiscard]] OpenDirectory open_directory_for(
    const std::filesystem::path& durable_path,
    ErrorCode code) {
  auto configured_path = parent_path_for(durable_path);
  const auto resolved = resolve_directory_path(configured_path, code);
  auto descriptor = open_resolved_directory(resolved, code);
  const auto status =
      descriptor_status(descriptor.get(), code, "cannot inspect runtime durable directory");
  require(S_ISDIR(status.st_mode), code, "runtime durable parent is not a directory");
  const auto identity = identity_of(status);
  verify_directory_binding(descriptor.get(), configured_path, identity, code);
  return OpenDirectory{std::move(descriptor), std::move(configured_path), identity};
}

[[nodiscard]] std::optional<struct stat> leaf_status(
    int directory,
    std::string_view leaf,
    ErrorCode code,
    const char* message) {
  struct stat status {};
  const std::string name(leaf);
  if (::fstatat(directory, name.c_str(), &status, AT_SYMLINK_NOFOLLOW) == 0) {
    return status;
  }
  if (errno == ENOENT) {
    return std::nullopt;
  }
  reject(code, message);
}

void require_regular_single_link(
    const struct stat& status,
    ErrorCode code,
    const char* message) {
  require(S_ISREG(status.st_mode) && status.st_nlink == 1, code, message);
}

[[nodiscard]] struct stat verify_named_descriptor(
    int directory,
    std::string_view leaf,
    int descriptor,
    FileIdentity expected,
    ErrorCode code,
    const char* message) {
  const auto descriptor_value = descriptor_status(descriptor, code, message);
  require_regular_single_link(descriptor_value, code, message);
  const auto named_value = leaf_status(directory, leaf, code, message);
  require(named_value.has_value(), code, message);
  require_regular_single_link(*named_value, code, message);
  require(
      identity_of(descriptor_value) == expected && identity_of(*named_value) == expected,
      code,
      message);
  return descriptor_value;
}

[[nodiscard]] Bytes read_descriptor(
    int descriptor,
    ErrorCode code,
    const char* message) {
  const auto before = descriptor_status(descriptor, code, message);
  require(before.st_size >= 0, code, message);
  const auto length = static_cast<std::uintmax_t>(before.st_size);
  require(length <= std::numeric_limits<std::size_t>::max(), code, message);
  Bytes result(static_cast<std::size_t>(length));
  std::size_t offset = 0U;
  while (offset < result.size()) {
    const auto remaining = result.size() - offset;
    const auto count = std::min(
        remaining, static_cast<std::size_t>(std::numeric_limits<ssize_t>::max()));
    const auto read = ::pread(
        descriptor,
        result.data() + static_cast<std::ptrdiff_t>(offset),
        count,
        static_cast<off_t>(offset));
    if (read < 0 && errno == EINTR) {
      continue;
    }
    if (read <= 0) {
      reject(code, message);
    }
    offset += static_cast<std::size_t>(read);
  }
  const auto after = descriptor_status(descriptor, code, message);
  require(after.st_size == before.st_size, code, message);
  return result;
}

void write_descriptor(
    int descriptor,
    std::span<const std::byte> bytes,
    ErrorCode code,
    const char* message) {
  std::size_t offset = 0U;
  while (offset < bytes.size()) {
    const auto remaining = bytes.size() - offset;
    const auto count = std::min(
        remaining, static_cast<std::size_t>(std::numeric_limits<ssize_t>::max()));
    const auto written = ::write(
        descriptor,
        bytes.data() + static_cast<std::ptrdiff_t>(offset),
        count);
    if (written < 0 && errno == EINTR) {
      continue;
    }
    if (written <= 0) {
      reject(code, message);
    }
    offset += static_cast<std::size_t>(written);
  }
}

void sync_descriptor(int descriptor, ErrorCode code, const char* message) {
  if (::fsync(descriptor) != 0) {
    reject(code, message);
  }
}

[[nodiscard]] std::optional<FileIdentity> validated_leaf_identity(
    int directory,
    std::string_view leaf,
    ErrorCode code,
    const char* message) {
  const auto status = leaf_status(directory, leaf, code, message);
  if (!status.has_value()) {
    return std::nullopt;
  }
  require_regular_single_link(*status, code, message);
  return identity_of(*status);
}

void require_leaf_unchanged(
    int directory,
    std::string_view leaf,
    const std::optional<FileIdentity>& expected,
    ErrorCode code,
    const char* message) {
  const auto observed = validated_leaf_identity(directory, leaf, code, message);
  require(observed == expected, code, message);
}

#endif

[[nodiscard]] Bytes encode_snapshot(const Snapshot& snapshot) {
  Bytes output(snapshot_magic.begin(), snapshot_magic.end());
  append_u16(output, format_version);
  append_u16(output, 0U);
  append_u64(output, snapshot.journal_sequence);
  append_u32(output, checked_u32(snapshot.state_bytes.size()));
  const auto state_hash = decode_digest(core::canonical::sha256_hex(snapshot.state_bytes));
  output.insert(output.end(), state_hash.begin(), state_hash.end());
  output.insert(output.end(), snapshot.state_bytes.begin(), snapshot.state_bytes.end());
  const auto checksum = decode_digest(core::canonical::sha256_hex(output));
  output.insert(output.end(), checksum.begin(), checksum.end());
  return output;
}

#ifdef _WIN32
void replace_file(const std::filesystem::path& source, const std::filesystem::path& target) {
  if (MoveFileExW(
          source.c_str(),
          target.c_str(),
          MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH) == 0) {
    reject(ErrorCode::io_error, "atomic snapshot replace failed");
  }
}
#endif

}  // namespace

Wal::Wal(
    std::filesystem::path path,
    std::optional<WalFileIdentity> expected_identity)
    : path_(std::move(path)), expected_identity_(expected_identity) {}

Wal::~Wal() {
#if !defined(_WIN32)
  if (file_fd_ >= 0) {
    static_cast<void>(::close(file_fd_));
  }
  if (directory_fd_ >= 0) {
    static_cast<void>(::close(directory_fd_));
  }
#endif
}

#if !defined(_WIN32)

void Wal::initialize_for_recovery() const {
  const auto leaf = leaf_name_for(path_, ErrorCode::io_error);
  if (recovery_initialized_) {
    verify_directory_binding(
        directory_fd_,
        parent_path_for(path_),
        FileIdentity{directory_device_, directory_inode_},
        ErrorCode::durable_binding_lost);
    if (file_fd_ >= 0) {
      static_cast<void>(verify_named_descriptor(
          directory_fd_,
          leaf,
          file_fd_,
          FileIdentity{file_device_, file_inode_},
          ErrorCode::durable_binding_lost,
          "runtime WAL identity changed"));
    } else {
      require(
          !leaf_status(
               directory_fd_,
               leaf,
               ErrorCode::durable_binding_lost,
               "cannot inspect runtime WAL leaf")
               .has_value(),
          ErrorCode::durable_binding_lost,
          "runtime WAL leaf appeared after recovery");
    }
    return;
  }

  auto directory = open_directory_for(path_, ErrorCode::io_error);
  const auto existing = leaf_status(
      directory.descriptor.get(), leaf, ErrorCode::io_error, "cannot inspect runtime WAL leaf");
  UniqueFd file;
  FileIdentity file_identity{0U, 0U};
  if (expected_identity_.has_value()) {
    require(
        existing.has_value(),
        ErrorCode::durable_binding_lost,
        "preflighted runtime WAL is no longer installed");
  }
  if (existing.has_value()) {
    const auto validation_code = expected_identity_.has_value()
                                     ? ErrorCode::durable_binding_lost
                                     : ErrorCode::io_error;
    require_regular_single_link(
        *existing,
        validation_code,
        "runtime WAL is not a single-link regular file");
    file_identity = identity_of(*existing);
    if (expected_identity_.has_value()) {
      require(
          file_identity == FileIdentity{
                               expected_identity_->device,
                               expected_identity_->inode,
                           },
          ErrorCode::durable_binding_lost,
          "runtime WAL differs from sidecar preflight identity");
    }
    file = UniqueFd(::openat(
        directory.descriptor.get(),
        leaf.c_str(),
        O_RDWR | O_APPEND | O_CLOEXEC | O_NOFOLLOW));
    if (file.get() < 0) {
      reject(validation_code, "cannot open runtime WAL without following links");
    }
    static_cast<void>(verify_named_descriptor(
        directory.descriptor.get(),
        leaf,
        file.get(),
        file_identity,
        validation_code,
        "runtime WAL changed while it was opened"));
  }
  verify_directory_binding(
      directory.descriptor.get(), directory.configured_path, directory.identity, ErrorCode::io_error);

  directory_device_ = directory.identity.device;
  directory_inode_ = directory.identity.inode;
  directory_fd_ = directory.descriptor.release();
  if (file.get() >= 0) {
    file_device_ = file_identity.device;
    file_inode_ = file_identity.inode;
    file_fd_ = file.release();
  }
  recovery_initialized_ = true;
}

void Wal::verify_pinned_file() const {
  initialize_for_recovery();
  verify_directory_binding(
      directory_fd_,
      parent_path_for(path_),
      FileIdentity{directory_device_, directory_inode_},
      ErrorCode::durable_binding_lost);
  require(
      file_fd_ >= 0,
      ErrorCode::durable_binding_lost,
      "runtime WAL was not created");
  static_cast<void>(verify_named_descriptor(
      directory_fd_,
      leaf_name_for(path_, ErrorCode::io_error),
      file_fd_,
      FileIdentity{file_device_, file_inode_},
      ErrorCode::durable_binding_lost,
      "runtime WAL identity changed"));
  verify_directory_binding(
      directory_fd_,
      parent_path_for(path_),
      FileIdentity{directory_device_, directory_inode_},
      ErrorCode::durable_binding_lost);
}

void Wal::ensure_file_for_append() {
  initialize_for_recovery();
  if (file_fd_ >= 0) {
    verify_pinned_file();
    return;
  }

  require(
      !expected_identity_.has_value(),
      ErrorCode::durable_binding_lost,
      "preflighted runtime WAL is no longer installed");

  verify_directory_binding(
      directory_fd_,
      parent_path_for(path_),
      FileIdentity{directory_device_, directory_inode_},
      ErrorCode::durable_binding_lost);
  const auto leaf = leaf_name_for(path_, ErrorCode::io_error);
  UniqueFd file(::openat(
      directory_fd_,
      leaf.c_str(),
      O_RDWR | O_APPEND | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW,
      S_IRUSR | S_IWUSR));
  if (file.get() < 0) {
    reject(
        ErrorCode::durable_binding_lost,
        "runtime WAL leaf appeared before exclusive creation");
  }
  const auto status = descriptor_status(
      file.get(), ErrorCode::io_error, "cannot inspect newly created runtime WAL");
  require_regular_single_link(
      status, ErrorCode::io_error, "new runtime WAL is not a single-link regular file");
  const auto identity = identity_of(status);
  // A pathname-based cleanup cannot atomically prove that it unlinks this
  // inode. Any setup failure therefore leaves the residue and fails closed.
  static_cast<void>(verify_named_descriptor(
      directory_fd_,
      leaf,
      file.get(),
      identity,
      ErrorCode::durable_binding_lost,
      "new runtime WAL identity changed"));
  sync_descriptor(
      directory_fd_, ErrorCode::io_error, "runtime WAL directory fsync failed");
  verify_directory_binding(
      directory_fd_,
      parent_path_for(path_),
      FileIdentity{directory_device_, directory_inode_},
      ErrorCode::durable_binding_lost);
  static_cast<void>(verify_named_descriptor(
      directory_fd_,
      leaf,
      file.get(),
      identity,
      ErrorCode::durable_binding_lost,
      "new runtime WAL identity changed"));
  file_device_ = identity.device;
  file_inode_ = identity.inode;
  file_fd_ = file.release();
}

void Wal::verify_snapshot_parent(const std::filesystem::path& path) const {
  initialize_for_recovery();
  const auto wal_parent = resolve_directory_path(parent_path_for(path_), ErrorCode::durable_binding_lost);
  const auto snapshot_parent =
      resolve_directory_path(parent_path_for(path), ErrorCode::durable_binding_lost);
  require(
      snapshot_parent.normalized == wal_parent.normalized &&
          snapshot_parent.trusted_descriptor_alias == wal_parent.trusted_descriptor_alias,
      ErrorCode::durable_binding_lost,
      "snapshot and WAL do not share one durable directory binding");
  verify_directory_binding(
      directory_fd_,
      parent_path_for(path_),
      FileIdentity{directory_device_, directory_inode_},
      ErrorCode::durable_binding_lost);
}

#endif

RecoveryLog Wal::recover() const {
#ifdef _WIN32
  if (!std::filesystem::exists(path_)) {
    return RecoveryLog{{}, 0U, false};
  }
  const auto bytes = read_file(path_, ErrorCode::io_error);
#else
  initialize_for_recovery();
  if (file_fd_ < 0) {
    return RecoveryLog{{}, 0U, false};
  }
  verify_pinned_file();
  const auto bytes = read_descriptor(
      file_fd_, ErrorCode::io_error, "cannot read pinned runtime WAL");
  verify_pinned_file();
#endif
  RecoveryLog result{{}, 0U, false};
  std::size_t cursor = 0U;
  while (cursor < bytes.size()) {
    const auto remaining = bytes.size() - cursor;
    if (remaining < wal_header_size) {
      result.torn_tail = true;
      break;
    }
    Reader header(std::span<const std::byte>(bytes).subspan(cursor, wal_header_size));
    require(
        equals(header.take(wal_magic.size()), wal_magic),
        ErrorCode::wal_corrupt,
        "runtime WAL magic mismatch");
    require(header.u16() == format_version, ErrorCode::wal_corrupt, "runtime WAL version mismatch");
    require(header.u16() == 0U, ErrorCode::wal_corrupt, "runtime WAL flags are nonzero");
    const auto frame_size = static_cast<std::size_t>(header.u32());
    require(
        frame_size >= minimum_frame_size && frame_size <= maximum_frame_size,
        ErrorCode::wal_corrupt,
        "runtime WAL frame size invalid");
    if (frame_size > remaining) {
      result.torn_tail = true;
      break;
    }
    result.entries.push_back(
        decode_entry(std::span<const std::byte>(bytes).subspan(cursor, frame_size)));
    cursor += frame_size;
  }
  result.durable_prefix_bytes = cursor;
  return result;
}

void Wal::truncate(std::uintmax_t size) const {
#ifdef _WIN32
  std::error_code error;
  std::filesystem::resize_file(path_, size, error);
  if (error) {
    reject(ErrorCode::io_error, "cannot truncate torn WAL tail");
  }
#else
  verify_pinned_file();
  require(
      size <= static_cast<std::uintmax_t>(std::numeric_limits<off_t>::max()),
      ErrorCode::io_error,
      "runtime WAL truncate size is outside off_t");
  if (::ftruncate(file_fd_, static_cast<off_t>(size)) != 0) {
    reject(ErrorCode::io_error, "cannot truncate torn WAL tail");
  }
  sync_descriptor(file_fd_, ErrorCode::io_error, "runtime WAL truncate fsync failed");
  verify_pinned_file();
#endif
}

void Wal::append_and_sync(const JournalEntry& entry, bool partial) {
  const auto encoded = encode_entry(entry);
  const auto count = partial ? encoded.size() / 2U : encoded.size();
#ifdef _WIN32
  append_file(path_, std::span<const std::byte>(encoded).first(count));
#else
  ensure_file_for_append();
  verify_pinned_file();
  write_descriptor(
      file_fd_,
      std::span<const std::byte>(encoded).first(count),
      ErrorCode::io_error,
      "runtime WAL append failed");
  verify_pinned_file();
  sync_descriptor(file_fd_, ErrorCode::io_error, "runtime WAL fsync failed");
  verify_pinned_file();
#endif
}

const std::filesystem::path& Wal::path() const noexcept { return path_; }

bool Wal::snapshot_exists(const std::filesystem::path& path) const {
#ifdef _WIN32
  return std::filesystem::exists(path);
#else
  verify_snapshot_parent(path);
  const auto leaf = leaf_name_for(path, ErrorCode::snapshot_corrupt);
  const auto status = leaf_status(
      directory_fd_,
      leaf,
      ErrorCode::snapshot_corrupt,
      "cannot inspect snapshot leaf");
  if (!status.has_value()) {
    verify_snapshot_parent(path);
    return false;
  }
  require_regular_single_link(
      *status,
      ErrorCode::snapshot_corrupt,
      "snapshot is not a single-link regular file");
  verify_snapshot_parent(path);
  return true;
#endif
}

Snapshot Wal::read_snapshot(const std::filesystem::path& path) const {
#ifdef _WIN32
  const auto bytes = read_file(path, ErrorCode::snapshot_corrupt);
#else
  verify_snapshot_parent(path);
  const auto leaf = leaf_name_for(path, ErrorCode::snapshot_corrupt);
  const auto expected = validated_leaf_identity(
      directory_fd_,
      leaf,
      ErrorCode::snapshot_corrupt,
      "snapshot is not a single-link regular file");
  require(expected.has_value(), ErrorCode::snapshot_corrupt, "snapshot leaf is absent");
  UniqueFd file(::openat(
      directory_fd_, leaf.c_str(), O_RDONLY | O_CLOEXEC | O_NOFOLLOW));
  if (file.get() < 0) {
    reject(ErrorCode::snapshot_corrupt, "cannot open snapshot without following links");
  }
  static_cast<void>(verify_named_descriptor(
      directory_fd_,
      leaf,
      file.get(),
      *expected,
      ErrorCode::snapshot_corrupt,
      "snapshot identity changed while opening"));
  const auto bytes = read_descriptor(
      file.get(), ErrorCode::snapshot_corrupt, "cannot read pinned snapshot");
  static_cast<void>(verify_named_descriptor(
      directory_fd_,
      leaf,
      file.get(),
      *expected,
      ErrorCode::snapshot_corrupt,
      "snapshot identity changed while reading"));
  verify_snapshot_parent(path);
#endif
  constexpr std::size_t fixed_size = 4U + 2U + 2U + 8U + 4U + digest_size + digest_size;
  require(bytes.size() >= fixed_size, ErrorCode::snapshot_corrupt, "snapshot is truncated");
  const auto checksum_offset = bytes.size() - digest_size;
  require(
      core::canonical::sha256_hex(std::span<const std::byte>(bytes).first(checksum_offset)) ==
          encode_digest(std::span<const std::byte>(bytes).subspan(checksum_offset)),
      ErrorCode::snapshot_corrupt,
      "snapshot checksum mismatch");
  Reader reader(std::span<const std::byte>(bytes).first(checksum_offset));
  require(
      equals(reader.take(snapshot_magic.size()), snapshot_magic),
      ErrorCode::snapshot_corrupt,
      "snapshot magic mismatch");
  require(
      reader.u16() == format_version, ErrorCode::snapshot_corrupt, "snapshot version mismatch");
  require(reader.u16() == 0U, ErrorCode::snapshot_corrupt, "snapshot flags are nonzero");
  const auto sequence = reader.u64();
  const auto state_length = static_cast<std::size_t>(reader.u32());
  const auto state_hash = reader.take(digest_size);
  const auto state = reader.take(state_length);
  require(reader.remaining() == 0U, ErrorCode::snapshot_corrupt, "snapshot has trailing bytes");
  require(
      core::canonical::sha256_hex(state) == encode_digest(state_hash),
      ErrorCode::snapshot_corrupt,
      "snapshot state hash mismatch");
#if !defined(_WIN32)
  verify_snapshot_parent(path);
#endif
  return Snapshot{sequence, Bytes(state.begin(), state.end())};
}

void Wal::write_snapshot(const std::filesystem::path& path, const Snapshot& snapshot) const {
  const auto encoded = encode_snapshot(snapshot);
#ifdef _WIN32
  auto temporary = path;
  temporary += ".tmp";
  std::error_code remove_error;
  std::filesystem::remove(temporary, remove_error);
  auto* file = open_file(temporary, "wb");
  if (file == nullptr) {
    reject(ErrorCode::io_error, "cannot open snapshot temporary file");
  }
  if (std::fwrite(encoded.data(), 1U, encoded.size(), file) != encoded.size()) {
    static_cast<void>(std::fclose(file));
    reject(ErrorCode::io_error, "snapshot write failed");
  }
  try {
    sync_file(file);
  } catch (...) {
    static_cast<void>(std::fclose(file));
    throw;
  }
  if (std::fclose(file) != 0) {
    reject(ErrorCode::io_error, "snapshot close failed");
  }
  replace_file(temporary, path);
#else
  verify_snapshot_parent(path);
  const auto leaf = leaf_name_for(path, ErrorCode::io_error);
  const auto temporary = leaf + ".tmp";
  const auto target_identity = validated_leaf_identity(
      directory_fd_,
      leaf,
      ErrorCode::io_error,
      "snapshot target is not a single-link regular file");
  verify_snapshot_parent(path);

  const auto stale_temporary = leaf_status(
      directory_fd_,
      temporary,
      ErrorCode::io_error,
      "cannot inspect snapshot temporary leaf");
  require(
      !stale_temporary.has_value(),
      ErrorCode::io_error,
      "snapshot temporary leaf already exists");

  UniqueFd file(::openat(
      directory_fd_,
      temporary.c_str(),
      O_WRONLY | O_CREAT | O_EXCL | O_CLOEXEC | O_NOFOLLOW,
      S_IRUSR | S_IWUSR));
  if (file.get() < 0) {
    reject(ErrorCode::io_error, "cannot exclusively create snapshot temporary file");
  }
  const auto temporary_status = descriptor_status(
      file.get(), ErrorCode::io_error, "cannot inspect snapshot temporary file");
  require_regular_single_link(
      temporary_status,
      ErrorCode::io_error,
      "snapshot temporary is not a single-link regular file");
  const auto temporary_identity = identity_of(temporary_status);
  try {
    static_cast<void>(verify_named_descriptor(
        directory_fd_,
        temporary,
        file.get(),
        temporary_identity,
        ErrorCode::io_error,
        "snapshot temporary identity changed"));
    write_descriptor(
        file.get(), encoded, ErrorCode::io_error, "snapshot temporary write failed");
    static_cast<void>(verify_named_descriptor(
        directory_fd_,
        temporary,
        file.get(),
        temporary_identity,
        ErrorCode::io_error,
        "snapshot temporary identity changed while writing"));
    sync_descriptor(file.get(), ErrorCode::io_error, "snapshot temporary fsync failed");
    verify_snapshot_parent(path);
    require_leaf_unchanged(
        directory_fd_,
        leaf,
        target_identity,
        ErrorCode::io_error,
        "snapshot target identity changed before replace");
    static_cast<void>(verify_named_descriptor(
        directory_fd_,
        temporary,
        file.get(),
        temporary_identity,
        ErrorCode::io_error,
        "snapshot temporary identity changed before replace"));
    if (::renameat(
            directory_fd_,
            temporary.c_str(),
            directory_fd_,
            leaf.c_str()) != 0) {
      reject(ErrorCode::io_error, "atomic snapshot replace failed");
    }
    static_cast<void>(verify_named_descriptor(
        directory_fd_,
        leaf,
        file.get(),
        temporary_identity,
        ErrorCode::io_error,
        "installed snapshot identity differs from the durable temporary"));
    verify_snapshot_parent(path);
    sync_descriptor(
        directory_fd_, ErrorCode::io_error, "snapshot directory fsync failed");
    static_cast<void>(verify_named_descriptor(
        directory_fd_,
        leaf,
        file.get(),
        temporary_identity,
        ErrorCode::io_error,
        "installed snapshot identity changed after directory fsync"));
    verify_snapshot_parent(path);
  } catch (...) {
    // A pathname-based cleanup cannot atomically prove that it unlinks the
    // inode created above. Leave the residue to fail future writes closed.
    throw;
  }
#endif
}

}  // namespace delta::runtime::detail
