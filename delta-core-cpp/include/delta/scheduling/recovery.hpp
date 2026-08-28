#pragma once

#include <delta/scheduling/leases.hpp>

#include <cstdint>
#include <filesystem>
#include <memory>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace delta::scheduling {

struct LeaseTimerToken {
  std::string effect_kind;
  std::uint64_t expiry_tick;
  std::uint64_t lease_epoch;
  std::string lease_id;
  std::string plan_id;
  std::string round_config_id;
  std::string ticket_id;
  std::string token_nonce;
  std::string worker_id;

  bool operator==(const LeaseTimerToken&) const = default;
};

struct TimerTokenRecord {
  LeaseTimerToken token;
  std::vector<std::byte> canonical_bytes;
  std::string content_id;

  bool operator==(const TimerTokenRecord&) const = default;
};

enum class TransitionStatus {
  applied,
  replay,
  stale_noop,
  early_noop,
  committed_noop,
};

enum class SchedulingCrashPoint {
  none,
  before_wal_append,
  after_durability_before_apply,
};

struct LeaseTransitionReceipt {
  TransitionStatus status;
  LeaseRecord lease;
  std::uint64_t journal_sequence;

  bool operator==(const LeaseTransitionReceipt&) const = default;
};

struct CommitReceipt {
  TransitionStatus status;
  std::string commitment_id;
  std::uint64_t journal_sequence;

  bool operator==(const CommitReceipt&) const = default;
};

class LeaseStateMachine final {
 public:
  LeaseStateMachine(
      std::filesystem::path directory,
      RoundTicketPlan plan,
      std::vector<LeaseRecord> initial_leases);
  ~LeaseStateMachine();

  LeaseStateMachine(const LeaseStateMachine&) = delete;
  LeaseStateMachine& operator=(const LeaseStateMachine&) = delete;
  LeaseStateMachine(LeaseStateMachine&&) = delete;
  LeaseStateMachine& operator=(LeaseStateMachine&&) = delete;

  [[nodiscard]] TimerTokenRecord timer_token(std::string_view ticket_id) const;
  [[nodiscard]] LeaseTransitionReceipt renew(
      std::string_view ticket_id,
      std::string_view worker_id,
      std::uint64_t lease_epoch,
      std::uint64_t expected_renewal_count,
      std::uint64_t logical_tick,
      SchedulingCrashPoint crash_point = SchedulingCrashPoint::none);
  [[nodiscard]] LeaseTransitionReceipt expire(
      const TimerTokenRecord& token,
      std::uint64_t logical_tick,
      SchedulingCrashPoint crash_point = SchedulingCrashPoint::none);
  [[nodiscard]] LeaseTransitionReceipt reassign(
      std::string_view ticket_id,
      std::string_view prior_lease_id,
      std::string new_worker_id,
      std::string new_region_route,
      std::uint64_t logical_tick,
      SchedulingCrashPoint crash_point = SchedulingCrashPoint::none);
  [[nodiscard]] CommitReceipt commit(
      std::string_view ticket_id,
      std::string_view worker_id,
      std::uint64_t lease_epoch,
      std::string commitment_id,
      std::uint64_t logical_tick,
      SchedulingCrashPoint crash_point = SchedulingCrashPoint::none);

  [[nodiscard]] const LeaseRecord& lease(std::string_view ticket_id) const;
  [[nodiscard]] std::string commitment(std::string_view ticket_id) const;
  [[nodiscard]] std::uint64_t journal_sequence() const noexcept;

 private:
  class Impl;
  std::unique_ptr<Impl> impl_;
};

[[nodiscard]] std::vector<std::byte> canonical_lease_timer_token(
    const LeaseTimerToken& token);
[[nodiscard]] std::string lease_timer_token_content_id(
    std::span<const std::byte> canonical_json);

}  // namespace delta::scheduling
