#pragma once

#include <delta/certificates/verifier.hpp>
#include <delta/runtime/runtime.hpp>

#include <filesystem>
#include <memory>
#include <string>
#include <vector>

namespace delta::runtime {

struct PersistedVoteFrame {
  core::canonical::Bytes frame;
  std::string vote_id;
  std::uint64_t journal_sequence;
  bool replay;
};

class CertificateVoteRuntime final {
 public:
  CertificateVoteRuntime(
      std::filesystem::path directory,
      core::canonical::Bytes initial_state_bytes);

  [[nodiscard]] PersistedVoteFrame persist_and_expose(
      const core::protocol::Vote& vote,
      CrashPoint crash_point = CrashPoint::none);
  [[nodiscard]] std::size_t recovered_vote_count() const noexcept;

 private:
  std::unique_ptr<Runtime> runtime_;
};

struct PointerState {
  std::string checkpoint_id;
  std::string optimizer_id;
  std::string apply_qc_id;
  std::uint64_t height;

  bool operator==(const PointerState&) const = default;
};

enum class PointerDisposition { advanced, replay };

class CurrentPointerStore final {
 public:
  CurrentPointerStore(std::filesystem::path directory, PointerState initial);

  [[nodiscard]] PointerDisposition advance(
      const certificates::CurrentPointerCommand& command,
      const certificates::ApplyQc& apply_qc,
      CrashPoint crash_point = CrashPoint::none);
  [[nodiscard]] const PointerState& state() const noexcept;

 private:
  void recover();

  std::filesystem::path directory_;
  PointerState state_;
};

}  // namespace delta::runtime
