#pragma once

#include <delta/core/canonical.hpp>

#include <cstddef>
#include <cstdint>
#include <filesystem>
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

class Wal {
 public:
  explicit Wal(std::filesystem::path path);

  [[nodiscard]] RecoveryLog recover() const;
  void truncate(std::uintmax_t size) const;
  void append_and_sync(const JournalEntry& entry, bool partial);
  [[nodiscard]] const std::filesystem::path& path() const noexcept;

 private:
  std::filesystem::path path_;
};

struct Snapshot {
  std::uint64_t journal_sequence;
  core::canonical::Bytes state_bytes;

  bool operator==(const Snapshot&) const = default;
};

[[nodiscard]] Snapshot read_snapshot(const std::filesystem::path& path);
[[nodiscard]] bool snapshot_exists(const std::filesystem::path& path);
void write_snapshot(const std::filesystem::path& path, const Snapshot& snapshot);

}  // namespace delta::runtime::detail
