#pragma once

#include <delta/scheduling/eligibility.hpp>
#include <delta/scheduling/planner.hpp>

#include <cstdint>
#include <span>
#include <string>
#include <vector>

namespace delta::scheduling {

struct TicketLease {
  std::uint64_t expiry_tick;
  std::uint64_t issue_tick;
  std::uint64_t lease_epoch;
  std::string plan_id;
  std::string prior_lease_id;
  std::string region_route;
  std::uint64_t renewal_count;
  std::string round_config_id;
  std::string state;
  std::string ticket_content_id;
  std::string ticket_id;
  std::string worker_id;

  bool operator==(const TicketLease&) const = default;
};

struct LeaseRecord {
  TicketLease lease;
  std::vector<std::byte> canonical_bytes;
  std::string content_id;

  bool operator==(const LeaseRecord&) const = default;
};

struct EligibleWorker {
  EligibilityDecision decision;
  std::uint64_t complete_ticket_throughput_milli;
};

struct InitialLeaseResult {
  bool feasible;
  std::vector<LeaseRecord> leases;
  std::vector<UnmetConstraint> unmet;
};

[[nodiscard]] InitialLeaseResult allocate_initial_leases(
    const RoundTicketPlan& plan,
    std::vector<EligibleWorker> workers,
    std::uint64_t issue_tick);
[[nodiscard]] std::vector<std::byte> canonical_ticket_lease(const TicketLease& lease);
[[nodiscard]] std::string ticket_lease_content_id(
    std::span<const std::byte> canonical_json);

}  // namespace delta::scheduling
