#pragma once

#include <delta/core/canonical.hpp>

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <optional>
#include <vector>

namespace delta::runtime::detail {

enum class JournalKind : std::uint8_t {
  transition = 1U,
  vote = 2U,
};

struct JournalEntry {
  std::uint64_t sequence;
  JournalKind kind;
  core::canonical::Bytes command_or_vote_bytes;
  core::canonical::Bytes next_state_bytes;
  core::canonical::Bytes effect_batch_bytes;
  core::canonical::Bytes wal_record_bytes;

  bool operator==(const JournalEntry&) const = default;
};

struct RecoveryLog {
  std::vector<JournalEntry> entries;
  std::uintmax_t durable_prefix_bytes;
  bool torn_tail;
};

struct Snapshot {
  std::uint64_t journal_sequence;
  core::canonical::Bytes state_bytes;

  bool operator==(const Snapshot&) const = default;
};

struct WalFileIdentity {
  std::uintmax_t device;
  std::uintmax_t inode;

  bool operator==(const WalFileIdentity&) const = default;
};

class Wal {
 public:
  explicit Wal(
      std::filesystem::path path,
      std::optional<WalFileIdentity> expected_identity = std::nullopt);
  ~Wal();

  Wal(const Wal&) = delete;
  Wal& operator=(const Wal&) = delete;
  Wal(Wal&&) = delete;
  Wal& operator=(Wal&&) = delete;

  [[nodiscard]] RecoveryLog recover() const;
  void truncate(std::uintmax_t size) const;
  void append_and_sync(const JournalEntry& entry, bool partial);
  [[nodiscard]] bool snapshot_exists(const std::filesystem::path& path) const;
  [[nodiscard]] Snapshot read_snapshot(const std::filesystem::path& path) const;
  void write_snapshot(const std::filesystem::path& path, const Snapshot& snapshot) const;
  [[nodiscard]] const std::filesystem::path& path() const noexcept;

 private:
#if !defined(_WIN32)
  void initialize_for_recovery() const;
  void ensure_file_for_append();
  void verify_snapshot_parent(const std::filesystem::path& path) const;
  void verify_pinned_file() const;
#endif

  std::filesystem::path path_;
  std::optional<WalFileIdentity> expected_identity_;
#if !defined(_WIN32)
  mutable int directory_fd_ = -1;
  mutable int file_fd_ = -1;
  mutable std::uintmax_t directory_device_ = 0U;
  mutable std::uintmax_t directory_inode_ = 0U;
  mutable std::uintmax_t file_device_ = 0U;
  mutable std::uintmax_t file_inode_ = 0U;
  mutable bool recovery_initialized_ = false;
#endif
};

}  // namespace delta::runtime::detail
