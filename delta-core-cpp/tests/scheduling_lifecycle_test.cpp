#include <delta/scheduling/eligibility.hpp>
#include <delta/scheduling/leases.hpp>
#include <delta/scheduling/planner.hpp>
#include <delta/scheduling/recovery.hpp>

#include <algorithm>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <regex>
#include <sstream>
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

template <typename Operation>
void expect_error(scheduling::ErrorCode expected, Operation operation) {
  try {
    operation();
  } catch (const scheduling::SchedulingError& error) {
    expect(error.code() == expected, "lifecycle operation returned the wrong error code");
    return;
  }
  fail("invalid lifecycle operation was accepted");
}

[[nodiscard]] std::filesystem::path case_directory(std::string_view name) {
#if defined(_MSVC_LANG)
  constexpr auto language_mode = _MSVC_LANG;
#else
  constexpr auto language_mode = __cplusplus;
#endif
  auto path = std::filesystem::temp_directory_path() / "delta-scheduling-007-tests" /
              std::to_string(language_mode) / name;
  std::error_code error;
  std::filesystem::remove_all(path, error);
  expect(!error, "cannot clean scheduling lifecycle test directory");
  std::filesystem::create_directories(path, error);
  expect(!error, "cannot create scheduling lifecycle test directory");
  return path;
}

[[nodiscard]] scheduling::Context context() {
  return {
      "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  };
}

[[nodiscard]] scheduling::DomainTicketPolicy policy(
    std::string domain,
    std::uint64_t ticket_count,
    std::uint64_t batch,
    std::uint64_t steps,
    std::uint64_t end,
    char mixture) {
  return {
      "CONTIGUOUS_NO_OVERLAP",
      context().arithmetic_profile_id,
      batch,
      "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",
      std::move(domain),
      "sha256:1111111111111111111111111111111111111111111111111111111111111111",
      "sha256:" + std::string(64U, mixture),
      context().parameter_schema_id,
      context().parent_checkpoint_id,
      {"eu", "us"},
      context().round_config_id,
      steps,
      ticket_count,
      end,
      0U,
  };
}

[[nodiscard]] scheduling::EligibilityPolicy eligibility_policy() {
  return {
      {"code", "text"},
      {"eu", "us"},
      {"sha256:3333333333333333333333333333333333333333333333333333333333333333"},
      context().arithmetic_profile_id,
      12U,
      "sha256:1111111111111111111111111111111111111111111111111111111111111111",
      7U,
      8'589'934'592U,
      8U,
      "QLORA-8GB",
      context().parameter_schema_id,
      context().round_config_id,
      {"sha256:8888888888888888888888888888888888888888888888888888888888888888",
       "sha256:9999999999999999999999999999999999999999999999999999999999999999"},
  };
}

[[nodiscard]] scheduling::CapabilityProfile profile(
    std::string worker,
    std::string region,
    std::uint64_t throughput,
    std::uint64_t concurrency,
    char measurement,
    char signature) {
  return {
      context().arithmetic_profile_id,
      throughput,
      80U,
      7U,
      concurrency,
      10U,
      "sha256:" + std::string(64U, measurement),
      8'589'934'592U,
      "QLORA-8GB",
      context().parameter_schema_id,
      std::move(region),
      context().round_config_id,
      8U,
      "sha256:" + std::string(64U, signature),
      "sha256:3333333333333333333333333333333333333333333333333333333333333333",
      std::move(worker),
  };
}

struct Setup {
  scheduling::RoundTicketPlan plan;
  std::vector<scheduling::LeaseRecord> leases;
};

[[nodiscard]] Setup setup() {
  const auto first = scheduling::evaluate_capability(
      profile("worker-a", "eu", 2400U, 2U, '6', '8'), eligibility_policy());
  const auto second = scheduling::evaluate_capability(
      profile("worker-b", "us", 900U, 1U, '7', '9'), eligibility_policy());
  scheduling::PlanContext plan_context{
      "sha256:2222222222222222222222222222222222222222222222222222222222222222",
      "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      {{second.decision.worker_id, second.decision_id},
       {first.decision.worker_id, first.decision_id}},
      {100U, 20U, 3U, 1U},
      context(),
  };
  auto plan = scheduling::plan_round_tickets(
      {policy("text", 1U, 2048U, 4U, 2048U, '5'),
       policy("code", 2U, 1024U, 8U, 4096U, '4')},
      plan_context);
  auto initial = scheduling::allocate_initial_leases(
      plan,
      {{second.decision, second.profile.complete_ticket_throughput_milli},
       {first.decision, first.profile.complete_ticket_throughput_milli}},
      15U);
  expect(initial.feasible, "lifecycle setup is infeasible");
  return {std::move(plan), std::move(initial.leases)};
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
  std::vector<std::byte> result;
  result.reserve(value.size() / 2U);
  for (std::size_t index = 0U; index < value.size(); index += 2U) {
    result.push_back(static_cast<std::byte>((nibble(value[index]) << 4U) | nibble(value[index + 1U])));
  }
  return result;
}

struct TimerFixture {
  std::vector<std::byte> bytes;
  std::string content_id;
};

[[nodiscard]] std::vector<TimerFixture> timer_fixtures() {
  std::ifstream input(DELTA_SCHEDULING_GOLDEN_PATH, std::ios::binary);
  expect(input.good(), "cannot open scheduling golden fixture");
  const std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  const std::regex pattern(
      R"REGEX("bytes_hex":"([0-9a-f]+)","content_id":"(sha256:[0-9a-f]{64})","value":\{[^{}]*"type_name":"LEASE_TIMER_TOKEN")REGEX");
  std::vector<TimerFixture> result;
  for (auto iterator = std::sregex_iterator(document.begin(), document.end(), pattern);
       iterator != std::sregex_iterator(); ++iterator) {
    result.push_back({unhex((*iterator)[1].str()), (*iterator)[2].str()});
  }
  expect(result.size() == 3U, "timer fixture count changed");
  return result;
}

void test_golden_opaque_timer_tokens() {
  auto data = setup();
  scheduling::LeaseStateMachine machine(
      case_directory("golden-timers"), data.plan, data.leases);
  const auto golden = timer_fixtures();
  for (std::size_t index = 0U; index < data.leases.size(); ++index) {
    const auto token = machine.timer_token(data.leases[index].lease.ticket_id);
    expect(
        token.canonical_bytes == golden[index].bytes && token.content_id == golden[index].content_id,
        "native opaque timer token differs from the frozen fixture");
  }
  expect(machine.journal_sequence() == 3U, "initial leases were not durably journaled");
}

void test_renew_expire_reassign_commit_and_replay() {
  auto data = setup();
  scheduling::LeaseStateMachine machine(
      case_directory("full-lifecycle"), data.plan, data.leases);
  const auto ticket = std::string{"ticket-code-000"};
  const auto old_timer = machine.timer_token(ticket);
  const auto renewed = machine.renew(ticket, "worker-a", 0U, 0U, 20U);
  expect(
      renewed.status == scheduling::TransitionStatus::applied &&
          renewed.lease.lease.expiry_tick == 55U && renewed.lease.lease.renewal_count == 1U &&
          renewed.lease.lease.ticket_content_id == data.leases[0].lease.ticket_content_id,
      "bounded renewal changed immutable ticket state");
  expect(
      machine.renew(ticket, "worker-a", 0U, 0U, 20U).status ==
          scheduling::TransitionStatus::replay,
      "exact renewal retry was not idempotent");
  expect(
      machine.expire(old_timer, 35U).status == scheduling::TransitionStatus::stale_noop,
      "old timer was not rejected as stale");
  const auto renewed_timer = machine.timer_token(ticket);
  expect(
      machine.expire(renewed_timer, 54U).status == scheduling::TransitionStatus::early_noop,
      "early timer delivery changed lease state");
  const auto expired = machine.expire(renewed_timer, 55U);
  expect(
      expired.status == scheduling::TransitionStatus::applied &&
          expired.lease.lease.state == "EXPIRED",
      "lease did not expire at its logical deadline");
  expect(
      machine.expire(renewed_timer, 55U).status == scheduling::TransitionStatus::replay,
      "duplicate expiry was not idempotent");
  const auto reassigned = machine.reassign(
      ticket, expired.lease.content_id, "worker-b", "us", 56U);
  expect(
      reassigned.lease.lease.lease_epoch == 1U &&
          reassigned.lease.lease.prior_lease_id == expired.lease.content_id &&
          reassigned.lease.lease.ticket_content_id == expired.lease.lease.ticket_content_id &&
          reassigned.lease.lease.worker_id == "worker-b",
      "reassignment broke prior-lease or immutable ticket lineage");
  expect(
      machine
              .reassign(ticket, expired.lease.content_id, "worker-b", "us", 56U)
              .status == scheduling::TransitionStatus::replay,
      "exact reassignment retry was not idempotent");
  expect_error(scheduling::ErrorCode::ticket_invalid, [&] {
    static_cast<void>(machine.commit(
        ticket,
        "worker-a",
        0U,
        "sha256:abababababababababababababababababababababababababababababababab",
        60U));
  });
  const auto commitment =
      "sha256:cdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd";
  const auto committed = machine.commit(ticket, "worker-b", 1U, commitment, 70U);
  expect(
      committed.status == scheduling::TransitionStatus::applied &&
          machine.commitment(ticket) == commitment,
      "current reassigned holder commitment was not accepted");
  expect(
      machine.commit(ticket, "worker-b", 1U, commitment, 70U).status ==
          scheduling::TransitionStatus::replay,
      "exact commitment retry was not idempotent");
  expect_error(scheduling::ErrorCode::ticket_invalid, [&] {
    static_cast<void>(machine.commit(
        ticket,
        "worker-b",
        1U,
        "sha256:efefefefefefefefefefefefefefefefefefefefefefefefefefefefefefefef",
        70U));
  });
  const auto committed_timer = machine.timer_token(ticket);
  expect(
      machine.expire(committed_timer, 76U).status ==
          scheduling::TransitionStatus::committed_noop,
      "expiry changed a committed ticket binding");
}

void test_commit_versus_expiry_ordering() {
  auto first_data = setup();
  scheduling::LeaseStateMachine commit_first(
      case_directory("commit-first"), first_data.plan, first_data.leases);
  const auto ticket = std::string{"ticket-code-000"};
  const auto timer = commit_first.timer_token(ticket);
  const auto commitment =
      "sha256:abababababababababababababababababababababababababababababababab";
  expect(
      commit_first.commit(ticket, "worker-a", 0U, commitment, 35U).status ==
          scheduling::TransitionStatus::applied &&
          commit_first.expire(timer, 35U).status ==
              scheduling::TransitionStatus::committed_noop,
      "commit-first race did not preserve the accepted commitment");

  auto second_data = setup();
  scheduling::LeaseStateMachine expiry_first(
      case_directory("expiry-first"), second_data.plan, second_data.leases);
  const auto second_timer = expiry_first.timer_token(ticket);
  static_cast<void>(expiry_first.expire(second_timer, 35U));
  expect_error(scheduling::ErrorCode::ticket_invalid, [&] {
    static_cast<void>(expiry_first.commit(ticket, "worker-a", 0U, commitment, 35U));
  });
}

void test_crash_recovery_and_persist_before_expose() {
  const auto directory = case_directory("crash-recovery");
  auto data = setup();
  {
    scheduling::LeaseStateMachine machine(directory, data.plan, data.leases);
    expect_error(scheduling::ErrorCode::canonical_json_invalid, [&] {
      static_cast<void>(machine.renew(
          "ticket-code-000",
          "worker-a",
          0U,
          0U,
          20U,
          scheduling::SchedulingCrashPoint::before_wal_append));
    });
    expect(
        machine.lease("ticket-code-000").lease.renewal_count == 0U &&
            machine.journal_sequence() == 3U,
        "transition became visible before durable journal append");
    expect_error(scheduling::ErrorCode::canonical_json_invalid, [&] {
      static_cast<void>(machine.renew(
          "ticket-code-000",
          "worker-a",
          0U,
          0U,
          20U,
          scheduling::SchedulingCrashPoint::after_durability_before_apply));
    });
    expect(
        machine.lease("ticket-code-000").lease.renewal_count == 0U,
        "post-durability crash exposed an unapplied transition");
  }
  {
    scheduling::LeaseStateMachine recovered(directory, data.plan, data.leases);
    expect(
        recovered.lease("ticket-code-000").lease.renewal_count == 1U &&
            recovered.lease("ticket-code-000").lease.expiry_tick == 55U &&
            recovered.journal_sequence() == 4U,
        "durable renewal was not recovered exactly");
    const auto timer = recovered.timer_token("ticket-code-000");
    expect_error(scheduling::ErrorCode::canonical_json_invalid, [&] {
      static_cast<void>(recovered.expire(
          timer,
          55U,
          scheduling::SchedulingCrashPoint::after_durability_before_apply));
    });
  }
  std::string expired_id;
  {
    scheduling::LeaseStateMachine recovered(directory, data.plan, data.leases);
    expect(
        recovered.lease("ticket-code-000").lease.state == "EXPIRED",
        "durable expiry was not recovered");
    expired_id = recovered.lease("ticket-code-000").content_id;
    expect_error(scheduling::ErrorCode::canonical_json_invalid, [&] {
      static_cast<void>(recovered.reassign(
          "ticket-code-000",
          expired_id,
          "worker-b",
          "us",
          56U,
          scheduling::SchedulingCrashPoint::after_durability_before_apply));
    });
  }
  {
    scheduling::LeaseStateMachine recovered(directory, data.plan, data.leases);
    expect(
        recovered.lease("ticket-code-000").lease.worker_id == "worker-b" &&
            recovered.lease("ticket-code-000").lease.lease_epoch == 1U,
        "durable reassignment was not recovered");
    expect_error(scheduling::ErrorCode::canonical_json_invalid, [&] {
      static_cast<void>(recovered.commit(
          "ticket-code-000",
          "worker-b",
          1U,
          "sha256:cdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd",
          70U,
          scheduling::SchedulingCrashPoint::after_durability_before_apply));
    });
  }
  {
    scheduling::LeaseStateMachine recovered(directory, data.plan, data.leases);
    expect(
        recovered.commitment("ticket-code-000") ==
            "sha256:cdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd",
        "durable commitment was not recovered");
  }
}

void test_max_epoch_hard_deadline_and_journal_corruption() {
  auto data = setup();
  const auto directory = case_directory("bounds");
  {
    scheduling::LeaseStateMachine machine(directory, data.plan, data.leases);
    auto timer = machine.timer_token("ticket-code-000");
    auto expired = machine.expire(timer, 35U);
    static_cast<void>(machine.reassign(
        "ticket-code-000", expired.lease.content_id, "worker-b", "us", 36U));
    timer = machine.timer_token("ticket-code-000");
    expired = machine.expire(timer, 56U);
    static_cast<void>(machine.reassign(
        "ticket-code-000", expired.lease.content_id, "worker-a", "eu", 57U));
    timer = machine.timer_token("ticket-code-000");
    expired = machine.expire(timer, 77U);
    expect_error(scheduling::ErrorCode::policy_invalid, [&] {
      static_cast<void>(machine.reassign(
          "ticket-code-000", expired.lease.content_id, "worker-b", "us", 78U));
    });
  }
  auto deadline_data = setup();
  scheduling::LeaseStateMachine deadline(
      case_directory("hard-deadline"), deadline_data.plan, deadline_data.leases);
  const auto expired = deadline.expire(deadline.timer_token("ticket-code-000"), 35U);
  expect_error(scheduling::ErrorCode::policy_invalid, [&] {
    static_cast<void>(deadline.reassign(
        "ticket-code-000", expired.lease.content_id, "worker-b", "us", 90U));
  });

  auto bytes = std::vector<char>{};
  {
    std::ifstream input(directory / "scheduling.wal", std::ios::binary);
    bytes.assign(std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>());
  }
  expect(!bytes.empty(), "journal corruption fixture is empty");
  bytes.back() = bytes.back() == '0' ? '1' : '0';
  {
    std::ofstream output(directory / "scheduling.wal", std::ios::binary | std::ios::trunc);
    output.write(bytes.data(), static_cast<std::streamsize>(bytes.size()));
  }
  expect_error(scheduling::ErrorCode::canonical_json_invalid, [&] {
    scheduling::LeaseStateMachine corrupted(directory, data.plan, data.leases);
  });
}

[[nodiscard]] std::string quote(std::string_view value) {
  return '"' + std::string(value) + '"';
}

void write_trace(const std::filesystem::path& path, const std::string& value) {
  std::ofstream output(path, std::ios::binary | std::ios::trunc);
  expect(output.good(), "cannot create scheduling refinement trace");
  output << value << '\n';
  output.close();
  expect(output.good(), "cannot persist scheduling refinement trace");
}

void expect_forbidden_policy_field(std::string_view field, std::string_view value) {
  auto bytes = scheduling::canonical_domain_ticket_policy(
      policy("code", 2U, 1024U, 8U, 4096U, '4'));
  std::string mutated;
  mutated.reserve(bytes.size() + field.size() + value.size() + 8U);
  for (const auto byte : bytes) {
    mutated.push_back(std::to_integer<char>(byte));
  }
  expect(!mutated.empty() && mutated.back() == '}', "canonical policy mutation is malformed");
  mutated.pop_back();
  mutated += ",\"" + std::string(field) + "\":" + std::string(value) + '}';
  try {
    static_cast<void>(scheduling::parse_domain_ticket_policy(
        std::as_bytes(std::span<const char>(mutated.data(), mutated.size())), context()));
  } catch (const scheduling::SchedulingError& error) {
    expect(
        error.code() == scheduling::ErrorCode::field_set_invalid ||
            error.code() == scheduling::ErrorCode::canonical_json_invalid,
        "forbidden policy field returned an unrelated error code");
    return;
  }
  fail("forbidden scheduling policy field was accepted");
}

[[nodiscard]] std::string worker_id(std::uint64_t ordinal) {
  std::ostringstream output;
  output << "worker-" << std::setw(3) << std::setfill('0') << ordinal;
  return output.str();
}

void export_fifty_worker_measurement(const std::filesystem::path& directory) {
  std::vector<scheduling::EligibilityRecord> records;
  records.reserve(50U);
  for (std::uint64_t ordinal = 0U; ordinal < 50U; ++ordinal) {
    records.push_back(scheduling::evaluate_capability(
        profile(
            worker_id(ordinal),
            ordinal % 2U == 0U ? "eu" : "us",
            1'000U + ordinal,
            2U,
            '6',
            '8'),
        eligibility_policy()));
  }
  scheduling::PlanContext plan_context{
      "sha256:2222222222222222222222222222222222222222222222222222222222222222",
      "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff",
      {},
      {100U, 20U, 3U, 1U},
      context(),
  };
  for (const auto& record : records) {
    plan_context.decisions.emplace_back(record.decision.worker_id, record.decision_id);
  }
  auto policies = std::vector{
      policy("text", 1U, 2048U, 4U, 2048U, '5'),
      policy("code", 2U, 1024U, 8U, 4096U, '4'),
  };
  const auto started = std::chrono::steady_clock::now();
  const auto reference = scheduling::plan_round_tickets(policies, plan_context);
  constexpr std::size_t permutations = 64U;
  for (std::size_t index = 0U; index < permutations; ++index) {
    auto permuted_policies = policies;
    auto permuted_context = plan_context;
    std::rotate(
        permuted_context.decisions.begin(),
        permuted_context.decisions.begin() + static_cast<std::ptrdiff_t>(index % 50U),
        permuted_context.decisions.end());
    if (index % 2U != 0U) {
      std::reverse(permuted_policies.begin(), permuted_policies.end());
    }
    const auto candidate = scheduling::plan_round_tickets(permuted_policies, permuted_context);
    expect(
        candidate.canonical_bytes == reference.canonical_bytes &&
            candidate.content_id == reference.content_id,
        "50-worker planning permutation changed canonical ticket bytes");
  }

  std::vector<scheduling::EligibleWorker> workers;
  workers.reserve(records.size());
  for (const auto& record : records) {
    workers.push_back({record.decision, record.profile.complete_ticket_throughput_milli});
  }
  const auto baseline = scheduling::allocate_initial_leases(reference, workers, 15U);
  expect(baseline.feasible, "50-worker baseline lease allocation is infeasible");
  for (std::size_t index = 0U; index < permutations; ++index) {
    auto permuted_workers = workers;
    std::rotate(
        permuted_workers.begin(),
        permuted_workers.begin() + static_cast<std::ptrdiff_t>(index % 50U),
        permuted_workers.end());
    const auto candidate = scheduling::allocate_initial_leases(reference, permuted_workers, 15U);
    expect(
        candidate.leases == baseline.leases,
        "50-worker input order changed deterministic lease ownership");
  }
  auto speed_swapped = workers;
  std::swap(
      speed_swapped.front().complete_ticket_throughput_milli,
      speed_swapped.back().complete_ticket_throughput_milli);
  const auto changed = scheduling::allocate_initial_leases(reference, speed_swapped, 15U);
  expect(changed.feasible && changed.leases.size() == baseline.leases.size(),
         "50-worker speed scenario became infeasible");
  bool owner_changed = false;
  for (std::size_t index = 0U; index < baseline.leases.size(); ++index) {
    owner_changed = owner_changed ||
                    baseline.leases[index].lease.worker_id != changed.leases[index].lease.worker_id;
    expect(
        baseline.leases[index].lease.ticket_id == changed.leases[index].lease.ticket_id &&
            baseline.leases[index].lease.ticket_content_id ==
                changed.leases[index].lease.ticket_content_id &&
            baseline.leases[index].lease.expiry_tick == changed.leases[index].lease.expiry_tick,
        "worker speed changed frozen ticket bytes or lease deadline");
  }
  expect(owner_changed, "50-worker speed scenario did not change ownership");
  const auto elapsed = std::chrono::duration_cast<std::chrono::nanoseconds>(
                           std::chrono::steady_clock::now() - started)
                           .count();
  expect(elapsed > 0, "50-worker measurement clock did not advance");
  write_trace(
      directory / "measurement-50-worker.json",
      "{\"elapsed_ns\":" + std::to_string(elapsed) +
          ",\"formal_semantics_id\":" + quote(scheduling::formal_semantics_id) +
          ",\"lease_permutations\":64,\"owner_changed\":true,\"plan_id\":" +
          quote(reference.content_id) +
          ",\"plan_permutations\":64,\"schema_version\":\"1.0.0\"," +
          "\"speed_independent_ticket_bytes\":true,\"terminal_outcome\":\"IN_PROGRESS\"," +
          "\"trace_id\":\"TRACE-NATIVE-007-50-WORKER\",\"worker_count\":50}");
}

void export_refinement_traces(const std::filesystem::path& directory) {
  std::error_code error;
  std::filesystem::remove_all(directory, error);
  expect(!error, "cannot clean scheduling refinement trace directory");
  std::filesystem::create_directories(directory, error);
  expect(!error, "cannot create scheduling refinement trace directory");

  auto data = setup();
  scheduling::LeaseStateMachine machine(directory / "full-lifecycle-state", data.plan, data.leases);
  const auto ticket = std::string{"ticket-code-000"};
  const auto initial = machine.lease(ticket);
  const auto old_timer = machine.timer_token(ticket);
  const auto renewed = machine.renew(ticket, "worker-a", 0U, 0U, 20U);
  const auto stale = machine.expire(old_timer, 35U);
  expect(stale.status == scheduling::TransitionStatus::stale_noop,
         "trace stale timer was not a native no-op");
  const auto expired = machine.expire(machine.timer_token(ticket), 55U);
  const auto reassigned = machine.reassign(
      ticket, expired.lease.content_id, "worker-b", "us", 56U);
  expect_error(scheduling::ErrorCode::ticket_invalid, [&] {
    static_cast<void>(machine.commit(
        ticket,
        "worker-a",
        0U,
        "sha256:abababababababababababababababababababababababababababababababab",
        60U));
  });
  const auto commitment =
      "sha256:cdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd";
  const auto committed = machine.commit(ticket, "worker-b", 1U, commitment, 70U);
  expect_error(scheduling::ErrorCode::ticket_invalid, [&] {
    static_cast<void>(machine.reassign(
        ticket, reassigned.lease.content_id, "worker-a", "eu", 71U));
  });
  const auto legal_events =
      "[{\"action\":\"PLAN_FINALIZED\",\"artifact_id\":" + quote(data.plan.content_id) +
      ",\"journal_sequence\":0,\"status\":\"APPLIED\",\"ticket_id\":" + quote(ticket) +
      "},{\"action\":\"LEASE_OPEN\",\"artifact_id\":" + quote(initial.content_id) +
      ",\"journal_sequence\":1,\"status\":\"APPLIED\",\"ticket_id\":" + quote(ticket) +
      "},{\"action\":\"LEASE_RENEW\",\"artifact_id\":" + quote(renewed.lease.content_id) +
      ",\"journal_sequence\":" + std::to_string(renewed.journal_sequence) +
      ",\"status\":\"APPLIED\",\"ticket_id\":" + quote(ticket) +
      "},{\"action\":\"LEASE_EXPIRE\",\"artifact_id\":" + quote(expired.lease.content_id) +
      ",\"journal_sequence\":" + std::to_string(expired.journal_sequence) +
      ",\"status\":\"APPLIED\",\"ticket_id\":" + quote(ticket) +
      "},{\"action\":\"LEASE_REASSIGN\",\"artifact_id\":" +
      quote(reassigned.lease.content_id) + ",\"journal_sequence\":" +
      std::to_string(reassigned.journal_sequence) +
      ",\"status\":\"APPLIED\",\"ticket_id\":" + quote(ticket) +
      "},{\"action\":\"COMMIT\",\"artifact_id\":" + quote(commitment) +
      ",\"journal_sequence\":" + std::to_string(committed.journal_sequence) +
      ",\"status\":\"APPLIED\",\"ticket_id\":" + quote(ticket) + "}]";
  write_trace(
      directory / "legal-full-lifecycle.json",
      "{\"abstraction_version\":\"1.0.0\",\"events\":" + legal_events +
          ",\"formal_semantics_id\":" + quote(scheduling::formal_semantics_id) +
          ",\"plan_id\":" + quote(data.plan.content_id) +
          ",\"schema_version\":\"1.0.0\",\"terminal_outcome\":\"IN_PROGRESS\"," +
          "\"trace_id\":\"TRACE-NATIVE-007-FULL-LIFECYCLE\"}");

  const auto recovery_directory = directory / "recovery-state";
  auto recovery_data = setup();
  {
    scheduling::LeaseStateMachine recovery(
        recovery_directory, recovery_data.plan, recovery_data.leases);
    expect_error(scheduling::ErrorCode::canonical_json_invalid, [&] {
      static_cast<void>(recovery.renew(
          ticket,
          "worker-a",
          0U,
          0U,
          20U,
          scheduling::SchedulingCrashPoint::after_durability_before_apply));
    });
  }
  scheduling::LeaseStateMachine recovered(
      recovery_directory, recovery_data.plan, recovery_data.leases);
  const auto replayed = recovered.renew(ticket, "worker-a", 0U, 0U, 20U);
  expect(replayed.status == scheduling::TransitionStatus::replay,
         "recovery trace did not replay the durable native transition");
  write_trace(
      directory / "legal-restart-replay.json",
      "{\"abstraction_version\":\"1.0.0\",\"events\":["
      "{\"action\":\"CRASH_AFTER_DURABILITY\",\"artifact_id\":" +
          quote(replayed.lease.content_id) +
          ",\"journal_sequence\":4,\"status\":\"FAULT\",\"ticket_id\":" + quote(ticket) +
          "},{\"action\":\"RESTART\",\"artifact_id\":" + quote(recovery_data.plan.content_id) +
          ",\"journal_sequence\":4,\"status\":\"APPLIED\",\"ticket_id\":" + quote(ticket) +
          "},{\"action\":\"RECOVER_JOURNAL\",\"artifact_id\":" +
          quote(replayed.lease.content_id) +
          ",\"journal_sequence\":4,\"status\":\"APPLIED\",\"ticket_id\":" + quote(ticket) +
          "},{\"action\":\"REPLAY_TRANSITION\",\"artifact_id\":" +
          quote(replayed.lease.content_id) +
          ",\"journal_sequence\":4,\"status\":\"REPLAY\",\"ticket_id\":" + quote(ticket) +
          "}],\"formal_semantics_id\":" + quote(scheduling::formal_semantics_id) +
          ",\"plan_id\":" + quote(recovery_data.plan.content_id) +
          ",\"schema_version\":\"1.0.0\",\"terminal_outcome\":\"IN_PROGRESS\"," +
          "\"trace_id\":\"TRACE-NATIVE-007-RESTART-REPLAY\"}");

  const auto illegal = [&](std::string_view name, std::string_view trace_id,
                           std::string_view action, std::string_view error_code) {
    write_trace(
        directory / std::string(name),
        "{\"accepted\":false,\"action\":" + quote(action) + ",\"error_code\":" +
            quote(error_code) + ",\"formal_semantics_id\":" +
            quote(scheduling::formal_semantics_id) +
            ",\"schema_version\":\"1.0.0\",\"terminal_outcome\":\"BLOCKED\"," +
            "\"trace_id\":" + quote(trace_id) + '}');
  };
  illegal(
      "illegal-old-holder.json",
      "TRACE-NATIVE-007-OLD-HOLDER",
      "COMMIT",
      "STALE_LEASE");
  illegal(
      "illegal-post-commit-reassign.json",
      "TRACE-NATIVE-007-POST-COMMIT-REASSIGN",
      "LEASE_REASSIGN",
      "COMMIT_ALREADY_ACCEPTED");
  illegal(
      "illegal-stale-timer.json",
      "TRACE-NATIVE-007-STALE-TIMER",
      "LEASE_EXPIRE",
      "STALE_TIMER_NOOP");
  expect_forbidden_policy_field("adaptive_h", "9");
  illegal(
      "illegal-adaptive-h.json",
      "TRACE-NATIVE-007-ADAPTIVE-H",
      "PLAN_FINALIZE",
      "FORBIDDEN_ADAPTIVE_WORK_FIELD");
  expect_forbidden_policy_field("device_speed_weight", "17");
  illegal(
      "illegal-device-weight.json",
      "TRACE-NATIVE-007-DEVICE-WEIGHT",
      "PLAN_FINALIZE",
      "FORBIDDEN_DEVICE_WEIGHT_FIELD");
  expect_forbidden_policy_field("rho_t", quote("sha256:" + std::string(64U, '7')));
  illegal(
      "illegal-early-randomness.json",
      "TRACE-NATIVE-007-EARLY-RANDOMNESS",
      "PLAN_FINALIZE",
      "EARLY_RANDOMNESS_FORBIDDEN");
  export_fifty_worker_measurement(directory);
}

}  // namespace

int main(int argc, char** argv) {
  try {
    expect(argc == 1 || argc == 2, "usage: scheduling_lifecycle_test [trace-directory]");
    test_golden_opaque_timer_tokens();
    test_renew_expire_reassign_commit_and_replay();
    test_commit_versus_expiry_ordering();
    test_crash_recovery_and_persist_before_expose();
    test_max_epoch_hard_deadline_and_journal_corruption();
    if (argc == 2) {
      export_refinement_traces(std::filesystem::path(argv[1]));
    }
  } catch (const std::exception& error) {
    std::cerr << "delta scheduling lifecycle test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta scheduling lifecycle tests passed\n";
  return 0;
}
