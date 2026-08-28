#include <delta/scheduling/planner.hpp>

#include <delta/core/canonical.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <iomanip>
#include <limits>
#include <map>
#include <span>
#include <sstream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace delta::scheduling {
namespace {

[[noreturn]] void reject(ErrorCode code, std::string message) {
  throw SchedulingError(code, std::move(message));
}

void require(bool condition, ErrorCode code, const char* message) {
  if (!condition) {
    reject(code, message);
  }
}

[[nodiscard]] bool content_id_valid(std::string_view value) noexcept {
  if (value.size() != 71U || !value.starts_with("sha256:")) {
    return false;
  }
  return std::all_of(value.begin() + 7, value.end(), [](char character) {
    return (character >= '0' && character <= '9') ||
           (character >= 'a' && character <= 'f');
  });
}

[[nodiscard]] bool label_valid(std::string_view value) noexcept {
  return !value.empty() && value.size() <= 128U &&
         std::all_of(value.begin(), value.end(), [](char character) {
           const bool letter = (character >= 'A' && character <= 'Z') ||
                               (character >= 'a' && character <= 'z');
           const bool digit = character >= '0' && character <= '9';
           return letter || digit || character == '.' || character == '_' || character == ':' ||
                  character == '-';
         });
}

[[nodiscard]] std::string quote(std::string_view value) {
  require(
      std::all_of(value.begin(), value.end(), [](char character) {
        return character >= 0x20 && character <= 0x7e && character != '"' && character != '\\';
      }),
      ErrorCode::identifier_invalid,
      "plan string is outside the canonical ASCII subset");
  return "\"" + std::string(value) + "\"";
}

void append_field(std::string& output, std::string_view key, std::string_view encoded_value) {
  if (output.size() > 1U) {
    output.push_back(',');
  }
  output += quote(key);
  output.push_back(':');
  output += encoded_value;
}

[[nodiscard]] std::vector<std::byte> bytes(std::string value) {
  const auto view = std::as_bytes(std::span(value.data(), value.size()));
  return {view.begin(), view.end()};
}

[[nodiscard]] std::string content_id_for(
    std::string_view domain,
    std::span<const std::byte> canonical_json) {
  std::vector<std::byte> input;
  input.reserve(domain.size() + 1U + canonical_json.size());
  for (const char character : domain) {
    input.push_back(static_cast<std::byte>(character));
  }
  input.push_back(std::byte{0});
  input.insert(input.end(), canonical_json.begin(), canonical_json.end());
  return "sha256:" + delta::core::canonical::sha256_hex(input);
}

[[nodiscard]] std::string ticket_name(std::string_view domain, std::uint64_t ordinal) {
  std::ostringstream output;
  output << "ticket-" << domain << '-' << std::setw(3) << std::setfill('0') << ordinal;
  return output.str();
}

[[nodiscard]] std::string decision_json(
    const std::vector<std::pair<std::string, std::string>>& decisions) {
  std::string output{"["};
  for (std::size_t index = 0U; index < decisions.size(); ++index) {
    if (index != 0U) {
      output.push_back(',');
    }
    output += "{\"decision_id\":" + quote(decisions[index].second) +
              ",\"worker_id\":" + quote(decisions[index].first) + "}";
  }
  output.push_back(']');
  return output;
}

[[nodiscard]] std::string policy_json(
    const std::vector<DomainTicketPolicy>& policies,
    const std::vector<std::string>& policy_ids) {
  std::string output{"["};
  for (std::size_t index = 0U; index < policies.size(); ++index) {
    if (index != 0U) {
      output.push_back(',');
    }
    output += "{\"domain_id\":" + quote(policies[index].domain_id) +
              ",\"policy_id\":" + quote(policy_ids[index]) + "}";
  }
  output.push_back(']');
  return output;
}

[[nodiscard]] std::string ticket_json(const std::vector<TicketRecord>& tickets) {
  std::string output{"["};
  for (std::size_t index = 0U; index < tickets.size(); ++index) {
    if (index != 0U) {
      output.push_back(',');
    }
    output += "{\"ticket_content_id\":" + quote(tickets[index].content_id) +
              ",\"ticket_id\":" + quote(tickets[index].ticket.ticket_id) + "}";
  }
  output.push_back(']');
  return output;
}

[[nodiscard]] std::vector<std::byte> canonical_plan(
    const RoundTicketPlan& plan,
    const PlanContext& context) {
  std::string lease{"{"};
  append_field(
      lease, "hard_deadline_tick", std::to_string(context.lease_policy.hard_deadline_tick));
  append_field(
      lease, "lease_duration_ticks", std::to_string(context.lease_policy.lease_duration_ticks));
  append_field(
      lease, "maximum_lease_epochs", std::to_string(context.lease_policy.maximum_lease_epochs));
  append_field(lease, "maximum_renewals", std::to_string(context.lease_policy.maximum_renewals));
  lease.push_back('}');

  std::string output{"{"};
  append_field(output, "assignment_policy_id", quote(context.assignment_policy_id));
  append_field(output, "capability_snapshot_root", quote(context.capability_snapshot_root));
  append_field(output, "decisions", decision_json(context.decisions));
  append_field(output, "formal_semantics_id", quote(formal_semantics_id));
  append_field(output, "lease_policy", lease);
  append_field(output, "parameter_schema_id", quote(context.round.parameter_schema_id));
  append_field(output, "parent_checkpoint_id", quote(context.round.parent_checkpoint_id));
  append_field(output, "policies", policy_json(plan.policies, plan.policy_ids));
  append_field(output, "round_config_id", quote(context.round.round_config_id));
  append_field(output, "schema_version", quote(schema_version));
  append_field(output, "tickets", ticket_json(plan.tickets));
  append_field(output, "type_name", quote("ROUND_TICKET_PLAN"));
  output.push_back('}');
  return bytes(std::move(output));
}

}  // namespace

RoundTicketPlan plan_round_tickets(
    std::vector<DomainTicketPolicy> policies,
    const PlanContext& context,
    const Limits& limits) {
  require(
      !policies.empty() && policies.size() <= limits.domains,
      ErrorCode::policy_invalid,
      "domain policy count is outside limits");
  require(
      content_id_valid(context.assignment_policy_id) &&
          content_id_valid(context.capability_snapshot_root),
      ErrorCode::identifier_invalid,
      "plan policy or capability root is invalid");
  require(
      context.lease_policy.hard_deadline_tick > 0U &&
          context.lease_policy.lease_duration_ticks > 0U &&
          context.lease_policy.maximum_lease_epochs > 0U,
      ErrorCode::policy_invalid,
      "lease policy bounds are invalid");
  std::sort(policies.begin(), policies.end(), [](const auto& left, const auto& right) {
    return left.domain_id < right.domain_id;
  });
  require(
      std::adjacent_find(policies.begin(), policies.end(), [](const auto& left, const auto& right) {
        return left.domain_id == right.domain_id;
      }) == policies.end(),
      ErrorCode::policy_invalid,
      "duplicate domain policy is forbidden");

  auto decisions = context.decisions;
  std::sort(decisions.begin(), decisions.end());
  require(
      !decisions.empty() &&
          std::adjacent_find(decisions.begin(), decisions.end(), [](const auto& left, const auto& right) {
            return left.first == right.first;
          }) == decisions.end(),
      ErrorCode::policy_invalid,
      "eligibility decision set is empty or duplicated");
  for (const auto& [worker_id, decision_id] : decisions) {
    require(
        label_valid(worker_id) && content_id_valid(decision_id),
        ErrorCode::identifier_invalid,
        "eligibility decision reference is invalid");
  }

  PlanContext canonical_context = context;
  canonical_context.decisions = std::move(decisions);
  RoundTicketPlan result;
  result.policies = std::move(policies);
  std::uint64_t total_tickets = 0U;
  for (const auto& policy : result.policies) {
    validate_domain_ticket_policy(policy, context.round, limits);
    require(
        total_tickets <= std::numeric_limits<std::uint64_t>::max() - policy.ticket_count,
        ErrorCode::policy_invalid,
        "total ticket count overflows uint64");
    total_tickets += policy.ticket_count;
  }
  require(
      total_tickets <= limits.tickets,
      ErrorCode::policy_invalid,
      "round ticket count exceeds limits");
  result.policy_ids.reserve(result.policies.size());
  result.tickets.reserve(static_cast<std::size_t>(total_tickets));

  for (const auto& policy : result.policies) {
    const auto policy_bytes = canonical_domain_ticket_policy(policy);
    const auto policy_id = domain_ticket_policy_content_id(policy_bytes);
    result.policy_ids.push_back(policy_id);
    const auto width = (policy.token_cursor_end - policy.token_cursor_start) / policy.ticket_count;
    for (std::uint64_t ordinal = 0U; ordinal < policy.ticket_count; ++ordinal) {
      const auto start = policy.token_cursor_start + width * ordinal;
#if defined(DELTA_SCHEDULING_MUTANT_OVERLAP_RANGES)
      const auto effective_start = policy.token_cursor_start;
#else
      const auto effective_start = start;
#endif
#if defined(DELTA_SCHEDULING_MUTANT_ADAPT_WORK)
      const auto effective_steps = policy.step_budget + ordinal;
#else
      const auto effective_steps = policy.step_budget;
#endif
      WorkTicket ticket{
          policy.arithmetic_profile_id,
          policy.batch_budget,
          policy.domain_id,
          "sha256:0000000000000000000000000000000000000000000000000000000000000000",
          policy.parameter_schema_id,
          policy.parent_checkpoint_id,
          policy_id,
          policy.round_config_id,
          effective_steps,
          ticket_name(policy.domain_id, ordinal),
          start + width,
          effective_start,
      };
      const auto canonical = canonical_work_ticket(ticket);
      result.tickets.push_back(
          {std::move(ticket), canonical, work_ticket_content_id(canonical)});
    }
  }

  for (std::size_t index = 0U; index < result.tickets.size(); ++index) {
    const auto& ticket = result.tickets[index].ticket;
    const auto policy = std::lower_bound(
        result.policies.begin(), result.policies.end(), ticket.domain_id, [](const auto& item, const auto& id) {
          return item.domain_id < id;
        });
    require(policy != result.policies.end(), ErrorCode::ticket_invalid, "ticket domain is missing");
    validate_work_ticket(ticket, context.round, *policy);
    if (index != 0U && result.tickets[index - 1U].ticket.domain_id == ticket.domain_id) {
      require(
          result.tickets[index - 1U].ticket.token_cursor_end == ticket.token_cursor_start,
          ErrorCode::allocation_invalid,
          "ticket data ranges contain a gap or overlap");
    }
  }
  result.canonical_bytes = canonical_plan(result, canonical_context);
  result.content_id = round_ticket_plan_content_id(result.canonical_bytes);
  return result;
}

Feasibility validate_feasibility(
    const std::vector<DomainTicketPolicy>& policies,
    std::vector<DomainCapacity> capacity) {
  std::sort(capacity.begin(), capacity.end(), [](const auto& left, const auto& right) {
    return left.domain_id < right.domain_id;
  });
  require(
      std::adjacent_find(capacity.begin(), capacity.end(), [](const auto& left, const auto& right) {
        return left.domain_id == right.domain_id;
      }) == capacity.end(),
      ErrorCode::policy_invalid,
      "duplicate domain capacity is forbidden");
  std::map<std::string, std::uint64_t> slots;
  for (const auto& item : capacity) {
    require(label_valid(item.domain_id), ErrorCode::identifier_invalid, "capacity domain is invalid");
    slots.emplace(item.domain_id, item.available_slots);
  }
  Feasibility result{true, {}};
  for (const auto& policy : policies) {
    const auto found = slots.find(policy.domain_id);
    const auto available = found == slots.end() ? 0U : found->second;
    if (available < policy.ticket_count) {
      result.feasible = false;
      result.unmet.push_back({available, policy.domain_id, policy.ticket_count});
    }
  }
  std::sort(result.unmet.begin(), result.unmet.end(), [](const auto& left, const auto& right) {
    return left.domain_id < right.domain_id;
  });
#if defined(DELTA_SCHEDULING_MUTANT_SKIP_INFEASIBILITY)
  result.feasible = true;
  result.unmet.clear();
#endif
  return result;
}

std::string round_ticket_plan_content_id(std::span<const std::byte> canonical_json) {
  return content_id_for("deltareduce.007.round-ticket-plan.v1", canonical_json);
}

}  // namespace delta::scheduling
