#include <delta/scheduling/eligibility.hpp>
#include <delta/scheduling/leases.hpp>
#include <delta/scheduling/planner.hpp>
#include <delta/scheduling/recovery.hpp>

#include <cstddef>
#include <cstdint>
#include <filesystem>
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

}  // namespace

int main() {
  try {
    test_golden_opaque_timer_tokens();
    test_renew_expire_reassign_commit_and_replay();
    test_commit_versus_expiry_ordering();
    test_crash_recovery_and_persist_before_expose();
    test_max_epoch_hard_deadline_and_journal_corruption();
  } catch (const std::exception& error) {
    std::cerr << "delta scheduling lifecycle test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta scheduling lifecycle tests passed\n";
  return 0;
}
