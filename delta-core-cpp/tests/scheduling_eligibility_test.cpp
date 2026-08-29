#include <delta/scheduling/eligibility.hpp>
#include <delta/scheduling/leases.hpp>
#include <delta/scheduling/planner.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <iterator>
#include <regex>
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
    auto record_bytes = unhex((*iterator)[1].str());
    const std::string text(
        reinterpret_cast<const char*>(record_bytes.data()), record_bytes.size());
    const std::regex type_pattern(R"REGEX("type_name":"([A-Z_]+)")REGEX");
    std::smatch type_match;
    expect(std::regex_search(text, type_match, type_pattern), "fixture record type is missing");
    result.push_back(
        {std::move(record_bytes), (*iterator)[2].str(), type_match[1].str()});
  }
  expect(result.size() == 17U, "scheduling fixture record count changed");
  return result;
}

[[nodiscard]] std::vector<Record> records_of_type(
    const std::vector<Record>& records,
    std::string_view type_name) {
  std::vector<Record> result;
  for (const auto& record : records) {
    if (record.type_name == type_name) {
      result.push_back(record);
    }
  }
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

[[nodiscard]] scheduling::EligibilityPolicy eligibility_policy() {
  return {
      {"code", "text"},
      {"eu", "us"},
      {"sha256:3333333333333333333333333333333333333333333333333333333333333333"},
      "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      12U,
      "sha256:1111111111111111111111111111111111111111111111111111111111111111",
      7U,
      8'589'934'592U,
      8U,
      "QLORA-8GB",
      "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      {"sha256:8888888888888888888888888888888888888888888888888888888888888888",
       "sha256:9999999999999999999999999999999999999999999999999999999999999999"},
  };
}

[[nodiscard]] std::vector<scheduling::DomainTicketPolicy> policies(
    const std::vector<Record>& records) {
  std::vector<scheduling::DomainTicketPolicy> result;
  for (const auto& record : records) {
    if (record.type_name == "DOMAIN_TICKET_POLICY") {
      result.push_back(scheduling::parse_domain_ticket_policy(record.bytes, context()));
    }
  }
  return result;
}

[[nodiscard]] std::vector<scheduling::EligibilityRecord> evaluated_profiles(
    const std::vector<Record>& records) {
  const auto profiles = records_of_type(records, "CAPABILITY_PROFILE");
  const auto decisions = records_of_type(records, "ELIGIBILITY_DECISION");
  expect(profiles.size() == 2U && decisions.size() == 2U, "eligibility fixture count changed");
  std::vector<scheduling::EligibilityRecord> result;
  for (std::size_t index = 0U; index < profiles.size(); ++index) {
    const auto profile = scheduling::parse_capability_profile(profiles[index].bytes);
    auto record = scheduling::evaluate_capability(profile, eligibility_policy());
    expect(
        record.profile_bytes == profiles[index].bytes &&
            record.profile_id == profiles[index].content_id &&
            record.decision_bytes == decisions[index].bytes &&
            record.decision_id == decisions[index].content_id && record.decision.eligible,
        "native eligibility bytes differ from the frozen fixture");
    result.push_back(std::move(record));
  }
  return result;
}

[[nodiscard]] scheduling::RoundTicketPlan plan(
    const std::vector<Record>& records,
    const std::vector<scheduling::EligibilityRecord>& eligible) {
  scheduling::PlanContext plan_context{
      "sha256:2222222222222222222222222222222222222222222222222222222222222222",
      "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      {{eligible[1].decision.worker_id, eligible[1].decision_id},
       {eligible[0].decision.worker_id, eligible[0].decision_id}},
      {100U, 20U, 3U, 1U},
      context(),
  };
  return scheduling::plan_round_tickets(policies(records), plan_context);
}

void test_golden_capability_decisions_and_leases() {
  const auto records = fixture_records();
  const auto eligible = evaluated_profiles(records);
  const auto ticket_plan = plan(records, eligible);
  std::vector<scheduling::EligibleWorker> workers;
  for (const auto& record : eligible) {
    workers.push_back(
        {record.decision, record.profile.complete_ticket_throughput_milli});
  }
  std::reverse(workers.begin(), workers.end());
  const auto allocated = scheduling::allocate_initial_leases(ticket_plan, workers, 15U);
  const auto golden_leases = records_of_type(records, "TICKET_LEASE");
  expect(
      allocated.feasible && allocated.leases.size() == golden_leases.size(),
      "golden initial lease allocation is infeasible");
  for (std::size_t index = 0U; index < golden_leases.size(); ++index) {
    expect(
        allocated.leases[index].canonical_bytes == golden_leases[index].bytes &&
            allocated.leases[index].content_id == golden_leases[index].content_id,
        "native initial lease differs from the frozen fixture");
  }
}

void test_capability_rejection_matrix() {
  const auto records = fixture_records();
  const auto profile_record = records_of_type(records, "CAPABILITY_PROFILE").front();
  const auto base = scheduling::parse_capability_profile(profile_record.bytes);
  const auto expect_reason = [&](auto mutation, std::string_view reason) {
    auto profile = base;
    mutation(profile);
    const auto result = scheduling::evaluate_capability(profile, eligibility_policy());
    expect(
        !result.decision.eligible && result.decision.max_concurrent_leases == 0U &&
            result.decision.allowed_domain_ids.empty() &&
            std::binary_search(
                result.decision.reason_codes.begin(), result.decision.reason_codes.end(), reason),
        "capability mismatch did not produce its stable reason");
  };
  expect_reason([](auto& profile) { profile.expires_at_tick = 11U; }, "PROFILE_EXPIRED");
  expect_reason([](auto& profile) { profile.memory_bytes = 1U; }, "MEMORY_INSUFFICIENT");
  expect_reason(
      [](auto& profile) {
        profile.parameter_schema_id =
            "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee";
      },
      "PARAMETER_SCHEMA_MISMATCH");
  expect_reason(
      [](auto& profile) {
        profile.signature_id =
            "sha256:7777777777777777777777777777777777777777777777777777777777777777";
      },
      "SIGNATURE_NOT_TRUSTED");
  expect_reason(
      [](auto& profile) { profile.complete_ticket_throughput_milli = 0U; },
      "THROUGHPUT_EVIDENCE_MISSING");
  auto region_policy = eligibility_policy();
  region_policy.allowed_region_ids = {"us"};
  const auto excluded = scheduling::evaluate_capability(base, region_policy);
  expect(
      excluded.decision.reason_codes == std::vector<std::string>{"REGION_NOT_ALLOWED"},
      "region loss did not fail closed");
}

void test_speed_changes_ownership_only_and_input_order_is_stable() {
  const auto records = fixture_records();
  const auto eligible = evaluated_profiles(records);
  const auto ticket_plan = plan(records, eligible);
  std::vector<scheduling::EligibleWorker> normal;
  for (const auto& record : eligible) {
    normal.push_back({record.decision, record.profile.complete_ticket_throughput_milli});
  }
  auto reversed = normal;
  std::reverse(reversed.begin(), reversed.end());
  const auto first = scheduling::allocate_initial_leases(ticket_plan, normal, 15U);
  const auto reordered = scheduling::allocate_initial_leases(ticket_plan, reversed, 15U);
  expect(
      first.leases == reordered.leases,
      "worker input order changed deterministic initial leases");

  auto speed_swapped = normal;
  std::swap(
      speed_swapped[0].complete_ticket_throughput_milli,
      speed_swapped[1].complete_ticket_throughput_milli);
  const auto changed = scheduling::allocate_initial_leases(ticket_plan, speed_swapped, 15U);
  expect(changed.feasible, "speed-swapped ownership became infeasible");
  bool owner_changed = false;
  for (std::size_t index = 0U; index < first.leases.size(); ++index) {
    owner_changed = owner_changed ||
                    first.leases[index].lease.worker_id != changed.leases[index].lease.worker_id;
    expect(
        first.leases[index].lease.ticket_id == changed.leases[index].lease.ticket_id &&
            first.leases[index].lease.ticket_content_id ==
                changed.leases[index].lease.ticket_content_id &&
            first.leases[index].lease.expiry_tick == changed.leases[index].lease.expiry_tick,
        "throughput changed ticket mathematics or deadline");
  }
  expect(owner_changed, "speed scenario did not exercise capacity-aware ownership");
}

void test_insufficient_capacity_and_region_loss() {
  const auto records = fixture_records();
  const auto eligible = evaluated_profiles(records);
  const auto ticket_plan = plan(records, eligible);
  const auto one_region = scheduling::allocate_initial_leases(
      ticket_plan,
      {{eligible.front().decision,
        eligible.front().profile.complete_ticket_throughput_milli}},
      15U);
  expect(
      !one_region.feasible && one_region.leases.empty() && !one_region.unmet.empty(),
      "region loss silently mutated or partially leased the plan");
  auto excluded = eligible.front().decision;
  excluded.eligible = false;
  excluded.max_concurrent_leases = 0U;
  excluded.allowed_domain_ids.clear();
  const auto no_capacity = scheduling::allocate_initial_leases(
      ticket_plan, {{excluded, eligible.front().profile.complete_ticket_throughput_milli}}, 15U);
  expect(
      !no_capacity.feasible && no_capacity.leases.empty(),
      "ineligible capacity was used for ticket ownership");
}

}  // namespace

int main() {
  try {
    test_golden_capability_decisions_and_leases();
    test_capability_rejection_matrix();
    test_speed_changes_ownership_only_and_input_order_is_stable();
    test_insufficient_capacity_and_region_loss();
  } catch (const std::exception& error) {
    std::cerr << "delta scheduling eligibility test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta scheduling eligibility tests passed\n";
  return 0;
}
