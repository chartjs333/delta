#pragma once

#include <delta/scheduling/contracts.hpp>

#include <cstdint>
#include <string>
#include <utility>
#include <vector>

namespace delta::scheduling {

struct LeasePolicy {
  std::uint64_t hard_deadline_tick;
  std::uint64_t lease_duration_ticks;
  std::uint64_t maximum_lease_epochs;
  std::uint64_t maximum_renewals;

  bool operator==(const LeasePolicy&) const = default;
};

struct PlanContext {
  std::string assignment_policy_id;
  std::string capability_snapshot_root;
  std::vector<std::pair<std::string, std::string>> decisions;
  LeasePolicy lease_policy;
  Context round;
};

struct TicketRecord {
  WorkTicket ticket;
  std::vector<std::byte> canonical_bytes;
  std::string content_id;
};

struct RoundTicketPlan {
  std::vector<DomainTicketPolicy> policies;
  std::vector<std::string> policy_ids;
  std::vector<TicketRecord> tickets;
  std::vector<std::byte> canonical_bytes;
  std::string content_id;
};

struct DomainCapacity {
  std::string domain_id;
  std::uint64_t available_slots;
};

struct UnmetConstraint {
  std::uint64_t available_slots;
  std::string domain_id;
  std::uint64_t required_slots;

  bool operator==(const UnmetConstraint&) const = default;
};

struct Feasibility {
  bool feasible;
  std::vector<UnmetConstraint> unmet;
};

[[nodiscard]] RoundTicketPlan plan_round_tickets(
    std::vector<DomainTicketPolicy> policies,
    const PlanContext& context,
    const Limits& limits = {});
[[nodiscard]] Feasibility validate_feasibility(
    const std::vector<DomainTicketPolicy>& policies,
    std::vector<DomainCapacity> capacity);
[[nodiscard]] std::string round_ticket_plan_content_id(
    std::span<const std::byte> canonical_json);

}  // namespace delta::scheduling
