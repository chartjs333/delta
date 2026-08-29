#pragma once

#include <cstddef>
#include <cstdint>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace delta::scheduling {

inline constexpr std::string_view formal_semantics_id =
    "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
inline constexpr std::string_view schema_version = "1.0.0";

enum class ErrorCode {
  input_too_large,
  canonical_json_invalid,
  field_set_invalid,
  identifier_invalid,
  context_mismatch,
  policy_invalid,
  ticket_invalid,
  allocation_invalid,
  infeasible,
};

class SchedulingError final : public std::runtime_error {
 public:
  SchedulingError(ErrorCode code, std::string message);

  [[nodiscard]] ErrorCode code() const noexcept;

 private:
  ErrorCode code_;
};

struct Limits {
  std::size_t contract_bytes = 256U * 1024U;
  std::size_t nesting_depth = 12U;
  std::size_t collection_members = 100'000U;
  std::size_t domains = 256U;
  std::size_t tickets = 100'000U;
};

struct Context {
  std::string arithmetic_profile_id;
  std::string parameter_schema_id;
  std::string parent_checkpoint_id;
  std::string round_config_id;

  bool operator==(const Context&) const = default;
};

struct DomainTicketPolicy {
  std::string allocation_policy;
  std::string arithmetic_profile_id;
  std::uint64_t batch_budget;
  std::string dataset_manifest_id;
  std::string domain_id;
  std::string eligibility_policy_id;
  std::string mixture_coefficient_id;
  std::string parameter_schema_id;
  std::string parent_checkpoint_id;
  std::vector<std::string> region_ids;
  std::string round_config_id;
  std::uint64_t step_budget;
  std::uint64_t ticket_count;
  std::uint64_t token_cursor_end;
  std::uint64_t token_cursor_start;

  bool operator==(const DomainTicketPolicy&) const = default;
};

struct WorkTicket {
  std::string arithmetic_profile_id;
  std::uint64_t batch_budget;
  std::string domain_id;
  std::string normalized_artifact_id;
  std::string parameter_schema_id;
  std::string parent_checkpoint_id;
  std::string policy_id;
  std::string round_config_id;
  std::uint64_t step_budget;
  std::string ticket_id;
  std::uint64_t token_cursor_end;
  std::uint64_t token_cursor_start;

  bool operator==(const WorkTicket&) const = default;
};

[[nodiscard]] DomainTicketPolicy parse_domain_ticket_policy(
    std::span<const std::byte> canonical_json,
    const Context& expected_context,
    const Limits& limits = {});
[[nodiscard]] WorkTicket parse_work_ticket(
    std::span<const std::byte> canonical_json,
    const Context& expected_context,
    const DomainTicketPolicy& policy,
    const Limits& limits = {});

void validate_domain_ticket_policy(
    const DomainTicketPolicy& policy,
    const Context& expected_context,
    const Limits& limits = {});
void validate_work_ticket(
    const WorkTicket& ticket,
    const Context& expected_context,
    const DomainTicketPolicy& policy);

[[nodiscard]] std::vector<std::byte> canonical_domain_ticket_policy(
    const DomainTicketPolicy& policy);
[[nodiscard]] std::vector<std::byte> canonical_work_ticket(const WorkTicket& ticket);
[[nodiscard]] std::string domain_ticket_policy_content_id(
    std::span<const std::byte> canonical_json);
[[nodiscard]] std::string work_ticket_content_id(std::span<const std::byte> canonical_json);

}  // namespace delta::scheduling
