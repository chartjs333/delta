#include <delta/scheduling/contracts.hpp>
#include <delta/scheduling/planner.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <regex>
#include <sstream>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace scheduling = delta::scheduling;

namespace {

[[noreturn]] void fail(std::string message) { throw std::runtime_error(std::move(message)); }

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

[[nodiscard]] std::vector<std::byte> unhex(std::string_view value) {
  const auto nibble = [](char character) -> unsigned {
    if (character >= '0' && character <= '9') {
      return static_cast<unsigned>(character - '0');
    }
    if (character >= 'a' && character <= 'f') {
      return static_cast<unsigned>(character - 'a') + 10U;
    }
    fail("fixture contains non-hex bytes");
  };
  expect((value.size() % 2U) == 0U, "fixture hex has odd length");
  std::vector<std::byte> result;
  result.reserve(value.size() / 2U);
  for (std::size_t index = 0U; index < value.size(); index += 2U) {
    result.push_back(static_cast<std::byte>((nibble(value[index]) << 4U) | nibble(value[index + 1U])));
  }
  return result;
}

struct Record {
  std::vector<std::byte> bytes;
  std::string content_id;
  std::string type_name;
};

[[nodiscard]] std::vector<Record> fixture_records() {
  std::ifstream input(DELTA_SCHEDULING_GOLDEN_PATH, std::ios::binary);
  expect(input.good(), "cannot open scheduling golden fixture");
  const std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  const std::regex pattern(
      R"REGEX("bytes_hex":"([0-9a-f]+)","content_id":"(sha256:[0-9a-f]{64})")REGEX");
  std::vector<Record> result;
  for (auto iterator = std::sregex_iterator(document.begin(), document.end(), pattern);
       iterator != std::sregex_iterator(); ++iterator) {
    auto bytes = unhex((*iterator)[1].str());
    const std::string text(reinterpret_cast<const char*>(bytes.data()), bytes.size());
    const std::regex type_pattern(R"REGEX("type_name":"([A-Z_]+)")REGEX");
    std::smatch type_match;
    expect(std::regex_search(text, type_match, type_pattern), "fixture record type is missing");
    result.push_back({std::move(bytes), (*iterator)[2].str(), type_match[1].str()});
  }
  expect(result.size() == 17U, "scheduling fixture record count changed");
  return result;
}

[[nodiscard]] scheduling::Context context() {
  return {
      "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  };
}

[[nodiscard]] scheduling::PlanContext plan_context() {
  return {
      "sha256:2222222222222222222222222222222222222222222222222222222222222222",
      "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      {{"worker-b", "sha256:f20ae4094d885c9a995f848c51d6c670eff267011c767c66b8401ade367af59c"},
       {"worker-a", "sha256:b257010c4285bbe512d8f39818ff818786a21f68f17d81bcfe1e8c93d6e6a4dc"}},
      {100U, 20U, 3U, 1U},
      context(),
  };
}

template <typename Operation>
void expect_error(scheduling::ErrorCode expected, Operation operation) {
  try {
    operation();
  } catch (const scheduling::SchedulingError& error) {
    expect(error.code() == expected, "scheduling operation returned the wrong error code");
    return;
  }
  fail("invalid scheduling input was accepted");
}

[[nodiscard]] std::vector<scheduling::DomainTicketPolicy> policies(
    const std::vector<Record>& records) {
  std::vector<scheduling::DomainTicketPolicy> result;
  for (const auto& record : records) {
    if (record.type_name == "DOMAIN_TICKET_POLICY") {
      const auto policy = scheduling::parse_domain_ticket_policy(record.bytes, context());
      expect(
          scheduling::canonical_domain_ticket_policy(policy) == record.bytes &&
              scheduling::domain_ticket_policy_content_id(record.bytes) == record.content_id,
          "domain policy canonical identity changed");
      result.push_back(policy);
    }
  }
  expect(result.size() == 2U, "domain policy count changed");
  return result;
}

void test_golden_parser_and_planner() {
  const auto records = fixture_records();
  auto parsed_policies = policies(records);
  std::reverse(parsed_policies.begin(), parsed_policies.end());
  const auto plan = scheduling::plan_round_tickets(parsed_policies, plan_context());
  expect(
      plan.policies.size() == 2U && plan.policies[0].domain_id == "code" &&
          plan.tickets.size() == 3U && plan.tickets[0].ticket.ticket_id == "ticket-code-000" &&
          plan.tickets[1].ticket.ticket_id == "ticket-code-001" &&
          plan.tickets[2].ticket.ticket_id == "ticket-text-000",
      "native planner did not produce canonical domain/ticket order");

  std::size_t ticket_index = 0U;
  for (const auto& record : records) {
    if (record.type_name == "SCHEDULING_WORK_TICKET") {
      const auto& policy = plan.policies[record.bytes == plan.tickets[2].canonical_bytes ? 1U : 0U];
      const auto ticket = scheduling::parse_work_ticket(record.bytes, context(), policy);
      expect(
          ticket == plan.tickets[ticket_index].ticket &&
              record.bytes == plan.tickets[ticket_index].canonical_bytes &&
              record.content_id == plan.tickets[ticket_index].content_id,
          "native ticket bytes or identity differ from the frozen fixture");
      ++ticket_index;
    }
  }
  expect(ticket_index == 3U, "work ticket fixture count changed");
  for (const auto& record : records) {
    if (record.type_name == "ROUND_TICKET_PLAN") {
      expect(
          record.bytes == plan.canonical_bytes && record.content_id == plan.content_id &&
              plan.content_id ==
                  "sha256:e5dfb51a67b48809b78167156130e6cddbadcde73919ae6e6ae192db7b452a5f",
          "native plan bytes or identity differ from the frozen fixture");
    }
  }
}

void test_parser_limits_context_and_allocation() {
  const auto records = fixture_records();
  const auto parsed_policies = policies(records);
  const auto policy_record = std::find_if(records.begin(), records.end(), [](const auto& record) {
    return record.type_name == "DOMAIN_TICKET_POLICY";
  });
  scheduling::Limits limits;
  limits.contract_bytes = policy_record->bytes.size() - 1U;
  expect_error(scheduling::ErrorCode::input_too_large, [&] {
    static_cast<void>(
        scheduling::parse_domain_ticket_policy(policy_record->bytes, context(), limits));
  });
  auto wrong_context = context();
  wrong_context.parent_checkpoint_id =
      "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee";
  expect_error(scheduling::ErrorCode::context_mismatch, [&] {
    static_cast<void>(
        scheduling::parse_domain_ticket_policy(policy_record->bytes, wrong_context));
  });
  auto noncanonical = policy_record->bytes;
  noncanonical.insert(noncanonical.begin() + 1, std::byte{' '});
  expect_error(scheduling::ErrorCode::canonical_json_invalid, [&] {
    static_cast<void>(scheduling::parse_domain_ticket_policy(noncanonical, context()));
  });
  auto indivisible = parsed_policies.front();
  indivisible.token_cursor_end = 4095U;
  expect_error(scheduling::ErrorCode::allocation_invalid, [&] {
    scheduling::validate_domain_ticket_policy(indivisible, context());
  });
  auto duplicate = parsed_policies;
  duplicate[1].domain_id = duplicate[0].domain_id;
  expect_error(scheduling::ErrorCode::policy_invalid, [&] {
    static_cast<void>(scheduling::plan_round_tickets(duplicate, plan_context()));
  });
}

void test_exact_feasibility_without_work_mutation() {
  const auto parsed_policies = policies(fixture_records());
  const auto feasible = scheduling::validate_feasibility(
      parsed_policies, {{"text", 1U}, {"code", 2U}});
  expect(feasible.feasible && feasible.unmet.empty(), "exact capacity was rejected");
  const auto infeasible = scheduling::validate_feasibility(
      parsed_policies, {{"code", 99U}, {"text", 0U}});
  expect(
      !infeasible.feasible &&
          infeasible.unmet ==
              std::vector<scheduling::UnmetConstraint>{{0U, "text", 1U}} &&
          parsed_policies[0].ticket_count == 2U && parsed_policies[1].ticket_count == 1U,
      "infeasibility did not preserve the immutable domain policy");
}

[[nodiscard]] std::string synthetic_id(std::uint64_t value) {
  std::ostringstream output;
  output << "sha256:" << std::hex << std::setw(64) << std::setfill('0') << value;
  return output.str();
}

void test_fifty_worker_input_permutation() {
  const auto parsed_policies = policies(fixture_records());
  auto first = plan_context();
  first.decisions.clear();
  for (std::uint64_t ordinal = 0U; ordinal < 50U; ++ordinal) {
    std::ostringstream worker;
    worker << "worker-" << std::setw(3) << std::setfill('0') << ordinal;
    first.decisions.emplace_back(worker.str(), synthetic_id(ordinal + 1U));
  }
  auto second = first;
  std::reverse(second.decisions.begin(), second.decisions.end());
  const auto first_plan = scheduling::plan_round_tickets(parsed_policies, first);
  auto reversed_policies = parsed_policies;
  std::reverse(reversed_policies.begin(), reversed_policies.end());
  const auto second_plan = scheduling::plan_round_tickets(reversed_policies, second);
  expect(
      first_plan.canonical_bytes == second_plan.canonical_bytes &&
          first_plan.content_id == second_plan.content_id,
      "50-worker input permutation changed native plan bytes");
}

}  // namespace

int main() {
  try {
    test_golden_parser_and_planner();
    test_parser_limits_context_and_allocation();
    test_exact_feasibility_without_work_mutation();
    test_fifty_worker_input_permutation();
  } catch (const std::exception& error) {
    std::cerr << "delta scheduling planner test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta scheduling planner tests passed\n";
  return 0;
}
