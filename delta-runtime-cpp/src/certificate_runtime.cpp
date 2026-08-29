#include <delta/runtime/certificate_runtime.hpp>

#include <delta/core/canonical.hpp>

#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#if defined(_WIN32)
#include <io.h>
#else
#include <unistd.h>
#endif

namespace delta::runtime {
namespace {

[[noreturn]] void reject(ErrorCode code, const char* message) {
  throw RuntimeError(code, message);
}

void require(bool condition, ErrorCode code, const char* message) {
  if (!condition) {
    reject(code, message);
  }
}

[[nodiscard]] std::filesystem::path pointer_path(const std::filesystem::path& directory) {
  return directory / "current-pointer.wal";
}

[[nodiscard]] std::string checksum(std::string_view payload) {
  const auto bytes = std::as_bytes(std::span(payload.data(), payload.size()));
  return core::canonical::sha256_hex(bytes);
}

[[nodiscard]] std::vector<std::string> split(std::string_view value, char separator) {
  std::vector<std::string> result;
  std::size_t begin = 0U;
  while (begin <= value.size()) {
    const auto end = value.find(separator, begin);
    result.emplace_back(value.substr(begin, end == std::string_view::npos ? end : end - begin));
    if (end == std::string_view::npos) {
      break;
    }
    begin = end + 1U;
  }
  return result;
}

void append_durable(const std::filesystem::path& path, std::string_view bytes) {
  std::FILE* file = nullptr;
#if defined(_WIN32)
  const auto error = _wfopen_s(&file, path.c_str(), L"ab");
  require(error == 0 && file != nullptr, ErrorCode::io_error, "cannot open pointer WAL");
#else
  file = std::fopen(path.c_str(), "ab");
  require(file != nullptr, ErrorCode::io_error, "cannot open pointer WAL");
#endif
  const auto written = std::fwrite(bytes.data(), 1U, bytes.size(), file);
  if (written != bytes.size() || std::fflush(file) != 0) {
    (void)std::fclose(file);
    reject(ErrorCode::io_error, "cannot append pointer WAL");
  }
#if defined(_WIN32)
  const auto synced = _commit(_fileno(file));
#else
  const auto synced = fsync(fileno(file));
#endif
  const auto closed = std::fclose(file);
  require(synced == 0 && closed == 0, ErrorCode::io_error, "cannot sync pointer WAL");
}

}  // namespace

CertificateVoteRuntime::CertificateVoteRuntime(
    std::filesystem::path directory,
    core::canonical::Bytes initial_state_bytes)
    : runtime_(std::make_unique<Runtime>(Config{
          .directory = std::move(directory),
          .initial_state_bytes = std::move(initial_state_bytes),
          .submission_capacity = 64U,
      })) {}

PersistedVoteFrame CertificateVoteRuntime::persist_and_expose(
    const core::protocol::Vote& vote,
    CrashPoint crash_point) {
  auto frame = core::protocol::encode(vote);
  const auto receipt = runtime_->record_vote(frame, crash_point);
  return PersistedVoteFrame{
      .frame = std::move(frame),
      .vote_id = receipt.vote_id,
      .journal_sequence = receipt.journal_sequence,
      .replay = receipt.replay,
  };
}

std::size_t CertificateVoteRuntime::recovered_vote_count() const noexcept {
  return runtime_->recovered_vote_count();
}

CurrentPointerStore::CurrentPointerStore(std::filesystem::path directory, PointerState initial)
    : directory_(std::move(directory)), state_(std::move(initial)) {
  require(
      certificates::is_content_id(state_.checkpoint_id) &&
          certificates::is_content_id(state_.optimizer_id) &&
          (state_.apply_qc_id.empty() || certificates::is_content_id(state_.apply_qc_id)),
      ErrorCode::invalid_config,
      "initial current-pointer state is invalid");
  std::filesystem::create_directories(directory_);
  recover();
}

void CurrentPointerStore::recover() {
  const auto path = pointer_path(directory_);
  if (!std::filesystem::exists(path)) {
    return;
  }
  std::ifstream input(path, std::ios::binary);
  require(input.good(), ErrorCode::io_error, "cannot read pointer WAL");
  std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  require(!input.bad(), ErrorCode::io_error, "cannot finish reading pointer WAL");
  if (!document.empty() && document.back() != '\n') {
    const auto last_complete = document.rfind('\n');
    const auto retained = last_complete == std::string::npos ? 0U : last_complete + 1U;
    std::filesystem::resize_file(path, retained);
    document.resize(retained);
  }
  std::size_t begin = 0U;
  while (begin < document.size()) {
    const auto end = document.find('\n', begin);
    require(end != std::string::npos, ErrorCode::wal_corrupt, "pointer WAL line is torn");
    const auto line = document.substr(begin, end - begin);
    const auto fields = split(line, '|');
    require(fields.size() == 6U, ErrorCode::wal_corrupt, "pointer WAL field count mismatch");
    const auto payload = line.substr(0U, line.rfind('|'));
    require(checksum(payload) == fields[5], ErrorCode::wal_corrupt, "pointer WAL checksum mismatch");
    std::uint64_t height = 0U;
    try {
      height = core::protocol::parse_u64_decimal(fields[0]);
    } catch (const core::protocol::ProtocolError&) {
      reject(ErrorCode::wal_corrupt, "pointer WAL height is invalid");
    }
    require(
        height > state_.height && fields[1] == state_.checkpoint_id &&
            certificates::is_content_id(fields[2]) && certificates::is_content_id(fields[3]) &&
            certificates::is_content_id(fields[4]),
        ErrorCode::recovery_mismatch,
        "pointer WAL does not extend the recovered state");
    state_ = PointerState{fields[2], fields[3], fields[4], height};
    begin = end + 1U;
  }
}

PointerDisposition CurrentPointerStore::advance(
    const certificates::CurrentPointerCommand& command,
    const certificates::ApplyQc& apply_qc,
    CrashPoint crash_point) {
  const auto command_id = certificates::content_id(command);
  static_cast<void>(command_id);
  const auto apply_qc_id = certificates::content_id(apply_qc);
#if !defined(DELTA_CURRENT_MUTANT_SKIP_APPLY_QC)
  require(
      command.apply_qc_id == apply_qc_id && command.context == apply_qc.context &&
          command.expected_parent_checkpoint_id == apply_qc.parent_checkpoint_id &&
          command.next_checkpoint_id == apply_qc.next_model_hash &&
          command.next_optimizer_hash == apply_qc.next_optimizer_hash,
      ErrorCode::request_conflict,
      "current-pointer command is not authorized by its ApplyQC");
#endif
  if (state_.apply_qc_id == apply_qc_id) {
    require(
        state_.checkpoint_id == command.next_checkpoint_id &&
            state_.optimizer_id == command.next_optimizer_hash &&
            state_.height == command.context.height,
        ErrorCode::recovery_mismatch,
        "ApplyQC replay does not match current state");
    return PointerDisposition::replay;
  }
  require(
      command.expected_parent_checkpoint_id == state_.checkpoint_id &&
          command.context.height > state_.height,
      ErrorCode::request_conflict,
      "ApplyQC does not extend the current checkpoint");
  if (crash_point == CrashPoint::before_wal_append ||
      crash_point == CrashPoint::after_wal_append_before_durability) {
    reject(ErrorCode::simulated_crash, "simulated pointer crash before durability");
  }
  if (crash_point == CrashPoint::during_wal_append) {
    append_durable(pointer_path(directory_), "truncated");
    reject(ErrorCode::simulated_crash, "simulated pointer crash during WAL append");
  }
  const auto payload = std::to_string(command.context.height) + "|" +
                       command.expected_parent_checkpoint_id + "|" + command.next_checkpoint_id +
                       "|" + command.next_optimizer_hash + "|" + apply_qc_id;
  append_durable(pointer_path(directory_), payload + "|" + checksum(payload) + "\n");
  if (crash_point == CrashPoint::after_durability_before_commit) {
    reject(ErrorCode::simulated_crash, "simulated pointer crash after durability");
  }
  state_ = PointerState{
      command.next_checkpoint_id,
      command.next_optimizer_hash,
      apply_qc_id,
      command.context.height,
  };
  if (crash_point == CrashPoint::after_commit_before_effect_return ||
      crash_point == CrashPoint::after_effect_copy_before_return) {
    reject(ErrorCode::simulated_crash, "simulated pointer crash after commit");
  }
  return PointerDisposition::advanced;
}

const PointerState& CurrentPointerStore::state() const noexcept { return state_; }

}  // namespace delta::runtime
