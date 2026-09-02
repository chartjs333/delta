#include <delta/runtime/runtime.hpp>

#include "wal.hpp"

#include <delta/core/consensus.hpp>
#include <delta/core/protocol.hpp>
#include <delta/core/transition.hpp>
#include <delta/runtime/bounded_mpsc.hpp>

#include <atomic>
#include <cstdint>
#include <filesystem>
#include <future>
#include <map>
#include <mutex>
#include <optional>
#include <string>
#include <thread>
#include <type_traits>
#include <utility>
#include <variant>

namespace delta::runtime {
namespace {

[[noreturn]] void reject(ErrorCode code, std::string message) {
  throw RuntimeError(code, std::move(message));
}

void require(bool condition, ErrorCode code, const char* message) {
  if (!condition) {
    reject(code, message);
  }
}

[[noreturn]] void simulated_crash(const char* boundary) {
  reject(ErrorCode::simulated_crash, boundary);
}

struct CachedRequest {
  std::string command_id;
  SubmitReceipt receipt;
};

struct SubmitWork {
  core::canonical::Bytes command_bytes;
  CrashPoint crash_point;
  std::promise<SubmitReceipt> promise;
};

struct VoteWork {
  core::canonical::Bytes vote_bytes;
  CrashPoint crash_point;
  std::promise<VoteReceipt> promise;
};

struct SnapshotWork {
  std::promise<void> promise;
};

using Work = std::variant<SubmitWork, VoteWork, SnapshotWork>;

template <typename Promise>
void set_exception(Promise& promise, std::exception_ptr exception) noexcept {
  try {
    promise.set_exception(std::move(exception));
  } catch (...) {
  }
}

}  // namespace

RuntimeError::RuntimeError(ErrorCode code, std::string message)
    : std::runtime_error(std::move(message)), code_(code) {}

ErrorCode RuntimeError::code() const noexcept { return code_; }

class Runtime::Impl {
 public:
  explicit Impl(Config config)
      : config_(std::move(config)),
        wal_(config_.directory / "runtime.wal"),
        snapshot_path_(config_.directory / "runtime.snapshot"),
        queue_(config_.submission_capacity) {
    require(!config_.directory.empty(), ErrorCode::invalid_config, "runtime directory is empty");
    require(
        !config_.initial_state_bytes.empty(),
        ErrorCode::invalid_config,
        "runtime initial state is empty");
    static_cast<void>(core::protocol::parse_round_state(config_.initial_state_bytes));
    std::error_code error;
    std::filesystem::create_directories(config_.directory, error);
    if (error) {
      reject(ErrorCode::io_error, "cannot create runtime directory");
    }
    recover();
    accepting_.store(true);
    reactor_ = std::thread([this] { reactor_loop(); });
  }

  ~Impl() { close(); }

  [[nodiscard]] std::future<SubmitReceipt> submit_async(
      core::canonical::Bytes command_bytes,
      CrashPoint crash_point) {
    require(accepting_.load(), ErrorCode::closed, "runtime is not accepting commands");
    SubmitWork work{std::move(command_bytes), crash_point, {}};
    auto future = work.promise.get_future();
    if (!queue_.try_push(Work{std::move(work)})) {
      reject(ErrorCode::queue_full, "runtime submission queue is full or closed");
    }
    return future;
  }

  [[nodiscard]] std::future<VoteReceipt> record_vote_async(
      core::canonical::Bytes vote_bytes,
      CrashPoint crash_point) {
    require(accepting_.load(), ErrorCode::closed, "runtime is not accepting votes");
    VoteWork work{std::move(vote_bytes), crash_point, {}};
    auto future = work.promise.get_future();
    if (!queue_.try_push(Work{std::move(work)})) {
      reject(ErrorCode::queue_full, "runtime submission queue is full or closed");
    }
    return future;
  }

  void snapshot() {
    require(accepting_.load(), ErrorCode::closed, "runtime is not accepting snapshots");
    SnapshotWork work;
    auto future = work.promise.get_future();
    if (!queue_.try_push(Work{std::move(work)})) {
      reject(ErrorCode::queue_full, "runtime submission queue is full or closed");
    }
    try {
      future.get();
    } catch (const RuntimeError& error) {
      throw RuntimeError(error.code(), error.what());
    }
  }

  void close() noexcept {
    accepting_.store(false);
    queue_.close();
    if (reactor_.joinable() && reactor_.get_id() != std::this_thread::get_id()) {
      reactor_.join();
    }
  }

  [[nodiscard]] core::canonical::Bytes state_bytes() const {
    std::lock_guard lock(state_mutex_);
    return state_bytes_;
  }

  [[nodiscard]] std::uint64_t journal_sequence() const noexcept { return sequence_.load(); }

  [[nodiscard]] std::size_t recovered_vote_count() const noexcept {
    return recovered_vote_count_.load();
  }

  [[nodiscard]] bool accepting() const noexcept { return accepting_.load(); }

 private:
  void recover() {
    auto recovered = wal_.recover();
    if (recovered.torn_tail) {
      wal_.truncate(recovered.durable_prefix_bytes);
    }
    std::optional<detail::Snapshot> snapshot;
    if (detail::snapshot_exists(snapshot_path_)) {
      snapshot = detail::read_snapshot(snapshot_path_);
      static_cast<void>(core::protocol::parse_round_state(snapshot->state_bytes));
    }

    auto recovered_state = config_.initial_state_bytes;
    std::uint64_t expected_sequence = 1U;
    bool snapshot_matched = !snapshot.has_value() || snapshot->journal_sequence == 0U;
    for (const auto& entry : recovered.entries) {
      require(
          entry.sequence == expected_sequence,
          ErrorCode::sequence_invalid,
          "runtime journal sequence is not strictly monotonic");
      if (entry.kind == detail::JournalKind::transition) {
        const auto command = core::protocol::parse_command(entry.command_or_vote_bytes);
        const auto result = core::transition::apply(recovered_state, entry.command_or_vote_bytes);
        require(
            result.next_state_bytes == entry.next_state_bytes &&
                result.effect_batch_bytes == entry.effect_batch_bytes &&
                result.wal_record_bytes == entry.wal_record_bytes,
            ErrorCode::recovery_mismatch,
            "replayed transition bytes differ from durable journal");
        require(
            requests_.find(command.request_id) == requests_.end(),
            ErrorCode::recovery_mismatch,
            "durable journal contains a duplicate request ID");
        requests_.emplace(
            command.request_id,
            CachedRequest{
                result.command_id,
                SubmitReceipt{
                    entry.next_state_bytes,
                    entry.effect_batch_bytes,
                    entry.wal_record_bytes,
                    result.next_state_id,
                    result.effect_batch_id,
                    result.wal_record_id,
                    entry.sequence,
                    false,
                },
            });
        recovered_state = entry.next_state_bytes;
      } else {
        const auto vote = core::protocol::parse_vote(entry.command_or_vote_bytes);
        const auto disposition = vote_journal_.record(vote);
        require(
            disposition == core::consensus::Disposition::recorded,
            ErrorCode::recovery_mismatch,
            "durable vote journal contains an exact duplicate");
        const auto vote_id = core::canonical::content_id(
            core::canonical::Type::vote, entry.command_or_vote_bytes);
        vote_sequences_.emplace(vote_id, entry.sequence);
      }
      if (snapshot.has_value() && entry.sequence == snapshot->journal_sequence) {
        require(
            recovered_state == snapshot->state_bytes,
            ErrorCode::snapshot_corrupt,
            "snapshot state differs from exact WAL replay");
        snapshot_matched = true;
      }
      ++expected_sequence;
    }
    require(snapshot_matched, ErrorCode::snapshot_corrupt, "snapshot sequence is absent from WAL");
    if (snapshot.has_value()) {
      require(
          snapshot->journal_sequence <= recovered.entries.size(),
          ErrorCode::snapshot_corrupt,
          "snapshot sequence is ahead of WAL");
    }
    {
      std::lock_guard lock(state_mutex_);
      state_bytes_ = std::move(recovered_state);
    }
    sequence_.store(expected_sequence - 1U);
    recovered_vote_count_.store(vote_journal_.votes().size());
  }

  [[nodiscard]] SubmitReceipt process_submit(SubmitWork& work) {
    const auto command = core::protocol::parse_command(work.command_bytes);
    const auto command_id =
        core::canonical::content_id(core::canonical::Type::command, work.command_bytes);
    if (const auto found = requests_.find(command.request_id); found != requests_.end()) {
      require(
          found->second.command_id == command_id,
          ErrorCode::request_conflict,
          "request ID was replayed with different command bytes");
      auto replay = found->second.receipt;
      replay.replay = true;
      return replay;
    }

    core::canonical::Bytes prior;
    {
      std::lock_guard lock(state_mutex_);
      prior = state_bytes_;
    }
    const auto result = core::transition::apply(prior, work.command_bytes);
    const auto next_sequence = sequence_.load() + 1U;
    const detail::JournalEntry entry{
        next_sequence,
        detail::JournalKind::transition,
        work.command_bytes,
        result.next_state_bytes,
        result.effect_batch_bytes,
        result.wal_record_bytes,
    };
    if (work.crash_point == CrashPoint::before_wal_append) {
      simulated_crash("simulated crash before WAL append");
    }
    if (work.crash_point == CrashPoint::during_wal_append) {
      wal_.append_and_sync(entry, true);
      simulated_crash("simulated crash during WAL append");
    }
    if (work.crash_point == CrashPoint::after_wal_append_before_durability) {
      simulated_crash("simulated crash after WAL append before durability");
    }
#if defined(DELTA_NATIVE_MUTANT_EXPOSE_BEFORE_DURABILITY)
    static_cast<void>(entry);
#else
    wal_.append_and_sync(entry, false);
#endif
    if (work.crash_point == CrashPoint::after_durability_before_commit) {
      simulated_crash("simulated crash after durability before commit");
    }

    SubmitReceipt receipt{
        result.next_state_bytes,
        result.effect_batch_bytes,
        result.wal_record_bytes,
        result.next_state_id,
        result.effect_batch_id,
        result.wal_record_id,
        next_sequence,
        false,
    };
    {
      std::lock_guard lock(state_mutex_);
      state_bytes_ = result.next_state_bytes;
    }
    sequence_.store(next_sequence);
    requests_.emplace(command.request_id, CachedRequest{command_id, receipt});
    if (work.crash_point == CrashPoint::after_commit_before_effect_return) {
      simulated_crash("simulated crash after commit before effect return");
    }
    const auto released = receipt;
    if (work.crash_point == CrashPoint::after_effect_copy_before_return) {
      static_cast<void>(released);
      simulated_crash("simulated crash after effect copy before return");
    }
    return released;
  }

  [[nodiscard]] VoteReceipt process_vote(VoteWork& work) {
    const auto vote = core::protocol::parse_vote(work.vote_bytes);
    const auto vote_id =
        core::canonical::content_id(core::canonical::Type::vote, work.vote_bytes);
    auto candidate = vote_journal_;
    const auto disposition = candidate.record(vote);
    if (disposition == core::consensus::Disposition::replay) {
      const auto found = vote_sequences_.find(vote_id);
      require(
          found != vote_sequences_.end(),
          ErrorCode::recovery_mismatch,
          "vote replay sequence is missing");
      return VoteReceipt{vote_id, found->second, true};
    }
    const auto next_sequence = sequence_.load() + 1U;
    const detail::JournalEntry entry{
        next_sequence,
        detail::JournalKind::vote,
        work.vote_bytes,
        {},
        {},
        {},
    };
    if (work.crash_point == CrashPoint::before_wal_append) {
      simulated_crash("simulated vote crash before WAL append");
    }
    if (work.crash_point == CrashPoint::during_wal_append) {
      wal_.append_and_sync(entry, true);
      simulated_crash("simulated vote crash during WAL append");
    }
    if (work.crash_point == CrashPoint::after_wal_append_before_durability) {
      simulated_crash("simulated vote crash after append before durability");
    }
    wal_.append_and_sync(entry, false);
    if (work.crash_point == CrashPoint::after_durability_before_commit) {
      simulated_crash("simulated vote crash after durability before commit");
    }
    vote_journal_ = std::move(candidate);
    vote_sequences_.emplace(vote_id, next_sequence);
    sequence_.store(next_sequence);
    recovered_vote_count_.store(vote_journal_.votes().size());
    if (work.crash_point == CrashPoint::after_commit_before_effect_return ||
        work.crash_point == CrashPoint::after_effect_copy_before_return) {
      simulated_crash("simulated vote crash after commit before receipt return");
    }
    return VoteReceipt{vote_id, next_sequence, false};
  }

  void process_snapshot(SnapshotWork&) {
    core::canonical::Bytes state;
    {
      std::lock_guard lock(state_mutex_);
      state = state_bytes_;
    }
    detail::write_snapshot(snapshot_path_, detail::Snapshot{sequence_.load(), std::move(state)});
  }

  void reactor_loop() noexcept {
    while (auto work = queue_.wait_pop()) {
      bool crashed = false;
      std::visit(
          [this, &crashed](auto& request) {
            try {
              using Request = std::decay_t<decltype(request)>;
              if constexpr (std::is_same_v<Request, SubmitWork>) {
                request.promise.set_value(process_submit(request));
              } else if constexpr (std::is_same_v<Request, VoteWork>) {
                request.promise.set_value(process_vote(request));
              } else {
                process_snapshot(request);
                request.promise.set_value();
              }
            } catch (...) {
              const auto exception = std::current_exception();
              try {
                std::rethrow_exception(exception);
              } catch (const RuntimeError& error) {
                crashed = error.code() == ErrorCode::simulated_crash;
              } catch (...) {
              }
              if (crashed) {
                accepting_.store(false);
                queue_.close();
              }
              set_exception(request.promise, exception);
            }
          },
          *work);
      if (crashed) {
        break;
      }
    }
    while (auto abandoned = queue_.wait_pop()) {
      std::visit(
          [](auto& request) {
            set_exception(
                request.promise,
                std::make_exception_ptr(RuntimeError(ErrorCode::closed, "runtime stopped")));
          },
          *abandoned);
    }
  }

  Config config_;
  detail::Wal wal_;
  std::filesystem::path snapshot_path_;
  BoundedMpscQueue<Work> queue_;
  std::thread reactor_;
  std::atomic<bool> accepting_{false};
  std::atomic<std::uint64_t> sequence_{0U};
  std::atomic<std::size_t> recovered_vote_count_{0U};
  mutable std::mutex state_mutex_;
  core::canonical::Bytes state_bytes_;
  core::consensus::VoteJournal vote_journal_;
  std::map<std::string, std::uint64_t> vote_sequences_;
  std::map<std::string, CachedRequest> requests_;
};

Runtime::Runtime(Config config) : impl_(std::make_unique<Impl>(std::move(config))) {}

Runtime::~Runtime() = default;

std::future<SubmitReceipt> Runtime::submit_async(
    core::canonical::Bytes command_bytes,
    CrashPoint crash_point) {
  return impl_->submit_async(std::move(command_bytes), crash_point);
}

SubmitReceipt Runtime::submit(core::canonical::Bytes command_bytes, CrashPoint crash_point) {
  auto future = submit_async(std::move(command_bytes), crash_point);
  try {
    return future.get();
  } catch (const RuntimeError& error) {
    // Keep the consumer's shared state alive while copying the reactor-owned
    // exception.  Otherwise its final producer reference can be released while
    // the caller is inspecting the exception rethrown by future::get().
    throw RuntimeError(error.code(), error.what());
  }
}

std::future<VoteReceipt> Runtime::record_vote_async(
    core::canonical::Bytes vote_bytes,
    CrashPoint crash_point) {
  return impl_->record_vote_async(std::move(vote_bytes), crash_point);
}

VoteReceipt Runtime::record_vote(core::canonical::Bytes vote_bytes, CrashPoint crash_point) {
  auto future = record_vote_async(std::move(vote_bytes), crash_point);
  try {
    return future.get();
  } catch (const RuntimeError& error) {
    throw RuntimeError(error.code(), error.what());
  }
}

void Runtime::snapshot() { impl_->snapshot(); }

void Runtime::close() noexcept { impl_->close(); }

core::canonical::Bytes Runtime::state_bytes() const { return impl_->state_bytes(); }

std::uint64_t Runtime::journal_sequence() const noexcept { return impl_->journal_sequence(); }

std::size_t Runtime::recovered_vote_count() const noexcept {
  return impl_->recovered_vote_count();
}

bool Runtime::accepting() const noexcept { return impl_->accepting(); }

}  // namespace delta::runtime
