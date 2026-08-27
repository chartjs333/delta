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
#include <span>
#include <string>
#include <system_error>

#ifdef _WIN32
#include <io.h>
#include <windows.h>
#else
#include <fcntl.h>
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
            entry.effect_batch_bytes.empty() && entry.wal_record_bytes.empty(),
        ErrorCode::wal_corrupt,
        "vote journal entry contains transition bytes");
  }
  return entry;
}

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
#ifdef _WIN32
  require(_commit(_fileno(file)) == 0, ErrorCode::io_error, "runtime file commit failed");
#else
  require(::fsync(::fileno(file)) == 0, ErrorCode::io_error, "runtime file fsync failed");
#endif
}

[[nodiscard]] std::FILE* open_file(const std::filesystem::path& path, const char* mode) {
  std::FILE* file = nullptr;
#ifdef _WIN32
  static_cast<void>(fopen_s(&file, path.string().c_str(), mode));
#else
  file = std::fopen(path.string().c_str(), mode);
#endif
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

void replace_file(const std::filesystem::path& source, const std::filesystem::path& target) {
#ifdef _WIN32
  if (MoveFileExW(
          source.c_str(),
          target.c_str(),
          MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH) == 0) {
    reject(ErrorCode::io_error, "atomic snapshot replace failed");
  }
#else
  if (::rename(source.c_str(), target.c_str()) != 0) {
    reject(ErrorCode::io_error, "atomic snapshot replace failed");
  }
  const auto directory = target.parent_path();
  const auto descriptor = ::open(directory.c_str(), O_RDONLY | O_DIRECTORY);
  if (descriptor < 0) {
    reject(ErrorCode::io_error, "cannot open snapshot directory for sync");
  }
  const auto result = ::fsync(descriptor);
  static_cast<void>(::close(descriptor));
  require(result == 0, ErrorCode::io_error, "snapshot directory fsync failed");
#endif
}

}  // namespace

Wal::Wal(std::filesystem::path path) : path_(std::move(path)) {}

RecoveryLog Wal::recover() const {
  if (!std::filesystem::exists(path_)) {
    return RecoveryLog{{}, 0U, false};
  }
  const auto bytes = read_file(path_, ErrorCode::io_error);
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
  std::error_code error;
  std::filesystem::resize_file(path_, size, error);
  if (error) {
    reject(ErrorCode::io_error, "cannot truncate torn WAL tail");
  }
}

void Wal::append_and_sync(const JournalEntry& entry, bool partial) {
  const auto encoded = encode_entry(entry);
  const auto count = partial ? encoded.size() / 2U : encoded.size();
  append_file(path_, std::span<const std::byte>(encoded).first(count));
}

const std::filesystem::path& Wal::path() const noexcept { return path_; }

bool snapshot_exists(const std::filesystem::path& path) { return std::filesystem::exists(path); }

Snapshot read_snapshot(const std::filesystem::path& path) {
  const auto bytes = read_file(path, ErrorCode::snapshot_corrupt);
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
  return Snapshot{sequence, Bytes(state.begin(), state.end())};
}

void write_snapshot(const std::filesystem::path& path, const Snapshot& snapshot) {
  const auto encoded = encode_snapshot(snapshot);
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
}

}  // namespace delta::runtime::detail
