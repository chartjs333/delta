#include <delta/scheduling/leases.hpp>

#include <delta/core/canonical.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <map>
#include <span>
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
      "lease string is outside the canonical ASCII subset");
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

[[nodiscard]] bool allows_domain(
    const EligibilityDecision& decision,
    std::string_view domain_id) {
  return std::binary_search(
      decision.allowed_domain_ids.begin(), decision.allowed_domain_ids.end(), domain_id);
}

}  // namespace

InitialLeaseResult allocate_initial_leases(
    const RoundTicketPlan& plan,
    std::vector<EligibleWorker> workers,
    std::uint64_t issue_tick) {
  require(
      issue_tick <= std::numeric_limits<std::uint64_t>::max() -
                        plan.lease_policy.lease_duration_ticks,
      ErrorCode::policy_invalid,
      "lease expiry overflows logical time");
  const auto expiry_tick = issue_tick + plan.lease_policy.lease_duration_ticks;
  require(
      expiry_tick <= plan.lease_policy.hard_deadline_tick,
      ErrorCode::policy_invalid,
      "initial lease exceeds the hard deadline");
  require(!plan.tickets.empty(), ErrorCode::policy_invalid, "ticket plan is empty");
  const auto& round_config_id = plan.tickets.front().ticket.round_config_id;

  workers.erase(
      std::remove_if(workers.begin(), workers.end(), [](const auto& worker) {
        return !worker.decision.eligible;
      }),
      workers.end());
  std::sort(workers.begin(), workers.end(), [](const auto& left, const auto& right) {
    if (left.complete_ticket_throughput_milli != right.complete_ticket_throughput_milli) {
      return left.complete_ticket_throughput_milli > right.complete_ticket_throughput_milli;
    }
    return left.decision.worker_id < right.decision.worker_id;
  });
  require(
      std::adjacent_find(workers.begin(), workers.end(), [](const auto& left, const auto& right) {
        return left.decision.worker_id == right.decision.worker_id;
      }) == workers.end(),
      ErrorCode::policy_invalid,
      "eligible worker identity is duplicated");
  for (const auto& worker : workers) {
    require(
        label_valid(worker.decision.worker_id) && label_valid(worker.decision.region_route) &&
            worker.decision.round_config_id == round_config_id &&
            worker.decision.max_concurrent_leases > 0U &&
            worker.complete_ticket_throughput_milli > 0U &&
            std::is_sorted(
                worker.decision.allowed_domain_ids.begin(),
                worker.decision.allowed_domain_ids.end()) &&
            std::adjacent_find(
                worker.decision.allowed_domain_ids.begin(),
                worker.decision.allowed_domain_ids.end()) ==
                worker.decision.allowed_domain_ids.end(),
        ErrorCode::policy_invalid,
        "eligible worker decision is invalid");
  }

  std::vector<std::uint64_t> remaining;
  remaining.reserve(workers.size());
  for (const auto& worker : workers) {
    remaining.push_back(worker.decision.max_concurrent_leases);
  }
  InitialLeaseResult result{true, {}, {}};
  result.leases.reserve(plan.tickets.size());
  for (const auto& ticket : plan.tickets) {
    std::size_t selected = workers.size();
    for (std::size_t index = 0U; index < workers.size(); ++index) {
      if (remaining[index] > 0U && allows_domain(workers[index].decision, ticket.ticket.domain_id)) {
        selected = index;
        break;
      }
    }
    if (selected == workers.size()) {
      result.feasible = false;
      break;
    }
    --remaining[selected];
    const auto& worker = workers[selected].decision;
    TicketLease lease{
        expiry_tick,
        issue_tick,
        0U,
        plan.content_id,
        "NONE",
        worker.region_route,
        0U,
        round_config_id,
        "ACTIVE",
        ticket.content_id,
        ticket.ticket.ticket_id,
        worker.worker_id,
    };
    const auto canonical = canonical_ticket_lease(lease);
    result.leases.push_back({std::move(lease), canonical, ticket_lease_content_id(canonical)});
  }
  if (!result.feasible) {
    result.leases.clear();
    std::map<std::string, std::uint64_t> required;
    std::map<std::string, std::uint64_t> available;
    for (const auto& ticket : plan.tickets) {
      ++required[ticket.ticket.domain_id];
    }
    for (const auto& [domain, count] : required) {
      for (const auto& worker : workers) {
        if (allows_domain(worker.decision, domain)) {
          available[domain] += worker.decision.max_concurrent_leases;
        }
      }
      if (available[domain] < count) {
        result.unmet.push_back({available[domain], domain, count});
      }
    }
    if (result.unmet.empty()) {
      result.unmet.push_back(
          {0U, "cross-domain-capacity", static_cast<std::uint64_t>(plan.tickets.size())});
    }
  }
  return result;
}

std::vector<std::byte> canonical_ticket_lease(const TicketLease& lease) {
  std::string output{"{"};
  append_field(output, "expiry_tick", std::to_string(lease.expiry_tick));
  append_field(output, "formal_semantics_id", quote(formal_semantics_id));
  append_field(output, "issue_tick", std::to_string(lease.issue_tick));
  append_field(output, "lease_epoch", std::to_string(lease.lease_epoch));
  append_field(output, "plan_id", quote(lease.plan_id));
  append_field(output, "prior_lease_id", quote(lease.prior_lease_id));
  append_field(output, "region_route", quote(lease.region_route));
  append_field(output, "renewal_count", std::to_string(lease.renewal_count));
  append_field(output, "round_config_id", quote(lease.round_config_id));
  append_field(output, "schema_version", quote(schema_version));
  append_field(output, "state", quote(lease.state));
  append_field(output, "ticket_content_id", quote(lease.ticket_content_id));
  append_field(output, "ticket_id", quote(lease.ticket_id));
  append_field(output, "type_name", quote("TICKET_LEASE"));
  append_field(output, "worker_id", quote(lease.worker_id));
  output.push_back('}');
  return bytes(std::move(output));
}

std::string ticket_lease_content_id(std::span<const std::byte> canonical_json) {
  return content_id_for("deltareduce.007.ticket-lease.v1", canonical_json);
}

}  // namespace delta::scheduling
