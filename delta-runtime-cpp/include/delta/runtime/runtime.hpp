#pragma once

#include <delta/core/canonical.hpp>

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <future>
#include <memory>
#include <stdexcept>
#include <string>

namespace delta::runtime {

enum class ErrorCode {
  invalid_config,
  queue_full,
  closed,
  io_error,
  wal_corrupt,
  snapshot_corrupt,
  sequence_invalid,
  request_conflict,
  recovery_mismatch,
  simulated_crash,
};

class RuntimeError final : public std::runtime_error {
 public:
  RuntimeError(ErrorCode code, std::string message);

  [[nodiscard]] ErrorCode code() const noexcept;

 private:
  ErrorCode code_;
};

enum class CrashPoint {
  none,
  before_wal_append,
  during_wal_append,
  after_wal_append_before_durability,
  after_durability_before_commit,
  after_commit_before_effect_return,
  after_effect_copy_before_return,
};

struct Config {
  std::filesystem::path directory;
  core::canonical::Bytes initial_state_bytes;
  std::size_t submission_capacity = 64U;
};

struct SubmitReceipt {
  core::canonical::Bytes next_state_bytes;
  core::canonical::Bytes effect_batch_bytes;
  core::canonical::Bytes wal_record_bytes;
  std::string next_state_id;
  std::string effect_batch_id;
  std::string wal_record_id;
  std::uint64_t journal_sequence;
  bool replay = false;

  bool operator==(const SubmitReceipt&) const = default;
};

struct VoteReceipt {
  std::string vote_id;
  std::uint64_t journal_sequence;
  bool replay = false;

  bool operator==(const VoteReceipt&) const = default;
};

class Runtime {
 public:
  explicit Runtime(Config config);
  ~Runtime();

  Runtime(const Runtime&) = delete;
  Runtime& operator=(const Runtime&) = delete;
  Runtime(Runtime&&) = delete;
  Runtime& operator=(Runtime&&) = delete;

  [[nodiscard]] std::future<SubmitReceipt> submit_async(
      core::canonical::Bytes command_bytes,
      CrashPoint crash_point = CrashPoint::none);
  [[nodiscard]] SubmitReceipt submit(
      core::canonical::Bytes command_bytes,
      CrashPoint crash_point = CrashPoint::none);
  [[nodiscard]] std::future<VoteReceipt> record_vote_async(
      core::canonical::Bytes vote_bytes,
      CrashPoint crash_point = CrashPoint::none);
  [[nodiscard]] VoteReceipt record_vote(
      core::canonical::Bytes vote_bytes,
      CrashPoint crash_point = CrashPoint::none);
  void snapshot();
  void close() noexcept;

  [[nodiscard]] core::canonical::Bytes state_bytes() const;
  [[nodiscard]] std::uint64_t journal_sequence() const noexcept;
  [[nodiscard]] std::size_t recovered_vote_count() const noexcept;
  [[nodiscard]] bool accepting() const noexcept;

 private:
  class Impl;
  std::unique_ptr<Impl> impl_;
};

}  // namespace delta::runtime
