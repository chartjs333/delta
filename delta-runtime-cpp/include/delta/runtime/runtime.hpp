#pragma once

#include <delta/core/canonical.hpp>
#include <delta/core/consensus.hpp>

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <functional>
#include <future>
#include <memory>
#include <optional>
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
  durable_binding_lost,
  simulated_crash,
};

class RuntimeError final : public std::runtime_error {
 public:
  RuntimeError(ErrorCode code, std::string message);

  [[nodiscard]] ErrorCode code() const noexcept;

 private:
  ErrorCode code_;
};

[[nodiscard]] std::uint64_t checked_next_journal_sequence(std::uint64_t current);

enum class CrashPoint {
  none,
  before_wal_append,
  during_wal_append,
  after_wal_append_before_durability,
  after_durability_before_commit,
  after_commit_before_effect_return,
  after_effect_copy_before_return,
};

// Optional startup binding supplied by an owner that has already opened and
// validated the durable WAL. On POSIX this closes the pathname lookup gap
// between sidecar preflight and Runtime recovery. Embedded runtimes may omit
// it and let Wal establish its own identity.
struct DurableFileIdentity {
  std::uint64_t device;
  std::uint64_t inode;

  bool operator==(const DurableFileIdentity&) const = default;
};

struct Config {
  std::filesystem::path directory;
  core::canonical::Bytes initial_state_bytes;
  std::size_t submission_capacity = 64U;
  // Invoked at every durable I/O and replay-exposure boundary. The sidecar
  // supplies a fail-closed pathname-to-descriptor identity check; embedded
  // runtimes may leave it empty.
  std::function<void()> durable_binding_guard;
  // A missing policy makes this a submit-only handle. record_vote() always
  // fails closed unless the handle was opened with a validated immutable round
  // contract and validator binding.
  std::optional<core::consensus::VoteAdmissionPolicy> vote_policy;
  std::optional<DurableFileIdentity> expected_wal_identity;
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
  core::canonical::Bytes frame;
  std::string vote_id;
  std::uint64_t journal_sequence;
  core::consensus::VoteAction action;
  std::string formal_action_id;
  std::string context_id;
  core::consensus::VoteParentState parents;
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
