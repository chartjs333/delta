#include <delta/core/canonical.hpp>
#include <delta/core/consensus.hpp>
#include <delta/core/protocol.hpp>
#include <delta/core/transition.hpp>
#include <delta/runtime/bounded_mpsc.hpp>
#include <delta/runtime/runtime.hpp>
#include <delta/runtime/vote_codec.hpp>

#include "../../delta-core-cpp/tests/vote_fixture.hpp"

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <future>
#include <iostream>
#include <iterator>
#include <limits>
#include <regex>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <utility>
#include <vector>

#if !defined(_WIN32)
#include <sys/stat.h>
#endif

namespace canonical = delta::core::canonical;
namespace consensus = delta::core::consensus;
namespace protocol = delta::core::protocol;
namespace runtime = delta::runtime;
namespace vote_fixture = delta::test::vote_fixture;

namespace {

[[noreturn]] void fail(std::string message) { throw std::runtime_error(std::move(message)); }

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

template <typename Operation>
void expect_runtime_error(runtime::ErrorCode expected, Operation operation) {
  try {
    operation();
  } catch (const runtime::RuntimeError& error) {
    expect(error.code() == expected, "unexpected stable runtime error code");
    return;
  }
  fail("runtime failure was not reported");
}

template <typename Operation>
void expect_consensus_error(consensus::ErrorCode expected, Operation operation) {
  try {
    operation();
  } catch (const consensus::ConsensusError& error) {
    expect(error.code() == expected, "unexpected recovered vote error code");
    return;
  }
  fail("conflicting recovered vote was accepted");
}

[[nodiscard]] std::uint8_t hex_nibble(char value) {
  if (value >= '0' && value <= '9') {
    return static_cast<std::uint8_t>(value - '0');
  }
  if (value >= 'a' && value <= 'f') {
    return static_cast<std::uint8_t>(value - 'a' + 10);
  }
  fail("invalid lowercase hexadecimal fixture");
}

[[nodiscard]] canonical::Bytes decode_hex(std::string_view encoded) {
  expect((encoded.size() % 2U) == 0U, "odd hexadecimal fixture length");
  canonical::Bytes result;
  result.reserve(encoded.size() / 2U);
  for (std::size_t index = 0; index < encoded.size(); index += 2U) {
    const auto value = static_cast<std::uint8_t>(
        static_cast<std::uint8_t>(hex_nibble(encoded[index]) << 4U) |
        hex_nibble(encoded[index + 1U]));
    result.push_back(static_cast<std::byte>(value));
  }
  return result;
}

[[nodiscard]] canonical::Bytes golden(std::uint16_t type_code) {
  std::ifstream input(DELTA_GOLDEN_FIXTURE_PATH, std::ios::binary);
  expect(input.good(), "cannot open canonical golden fixture");
  const std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  const std::regex pattern(
      R"REGEX("envelope_hex":"([0-9a-f]+)","envelope_sha256":"[0-9a-f]+","type_code":([0-9]+))REGEX");
  for (auto cursor = std::sregex_iterator(document.begin(), document.end(), pattern);
       cursor != std::sregex_iterator();
       ++cursor) {
    if (std::stoul((*cursor)[2].str()) == type_code) {
      return decode_hex((*cursor)[1].str());
    }
  }
  fail("registered golden vector not found");
}

[[nodiscard]] std::filesystem::path case_directory(std::string_view name) {
#if defined(_MSVC_LANG)
  constexpr auto language_mode = _MSVC_LANG;
#else
  constexpr auto language_mode = __cplusplus;
#endif
  auto path = std::filesystem::temp_directory_path() / "delta-runtime-003-tests" /
              std::to_string(language_mode) / name;
  std::error_code error;
  std::filesystem::remove_all(path, error);
  expect(!error, "cannot clean exact runtime test directory");
  std::filesystem::create_directories(path, error);
  expect(!error, "cannot create runtime test directory");
  return path;
}

[[nodiscard]] runtime::Config config(const std::filesystem::path& directory) {
  return runtime::Config{
      .directory = directory,
      .initial_state_bytes = golden(5U),
      .submission_capacity = 64U,
      .durable_binding_guard = {},
      .vote_policy = {},
      .expected_wal_identity = {},
  };
}

[[nodiscard]] runtime::Config vote_config(const std::filesystem::path& directory) {
  const auto state = protocol::parse_round_state(golden(5U));
  auto result = config(directory);
  result.vote_policy = vote_fixture::full(consensus::VoteAction::round_config, state).policy;
  return result;
}

[[nodiscard]] canonical::Bytes round_config_vote_bytes() {
  const auto state = protocol::parse_round_state(golden(5U));
  return protocol::encode(
      vote_fixture::full(consensus::VoteAction::round_config, state).vote);
}

[[nodiscard]] vote_fixture::Fixture arbitrary_arithmetic_fixture(
    consensus::VoteAction action) {
  auto fixture = vote_fixture::full(action);
  if (action == consensus::VoteAction::parameter) {
    auto& body = fixture.policy.snapshot.parameter_bodies.front();
    body.result_numerators = {"9223372036854775807"};
    fixture.policy.candidates.front().body_hash =
        consensus::vote_parameter_body_id(body);
  } else if (action == consensus::VoteAction::apply) {
    auto& body = fixture.policy.snapshot.apply_candidates.front();
    body.next_model_hash = vote_fixture::id('a');
    body.next_model_values = {"9223372036854775807"};
    body.next_optimizer_hash = vote_fixture::id('b');
    body.next_optimizer_values = {"-9223372036854775808"};
    fixture.policy.candidates.front().body_hash =
        delta::certificates::content_id(body);
    fixture.policy.candidates.front().parents.apply_candidate_id =
        fixture.policy.candidates.front().body_hash;
  } else {
    fail("arbitrary arithmetic fixture requires PARAMETER or APPLY");
  }
  fixture.candidate = fixture.policy.candidates.front();
  fixture.vote.body_hash = fixture.candidate.body_hash;
  return fixture;
}

[[nodiscard]] protocol::Command command_for(
    const protocol::RoundState& state,
    std::string request_id,
    std::string body_hash =
        "sha256:abababababababababababababababababababababababababababababababab") {
  return protocol::Command{
      "validator-1",
      std::move(body_hash),
      "ACCEPT_COMMITMENT",
      state.height,
      10U,
      std::move(request_id),
      state.round_id,
      state.view,
  };
}

[[nodiscard]] canonical::Bytes first_command(std::string request_id = "runtime-request-001") {
  return protocol::encode(
      command_for(protocol::parse_round_state(golden(5U)), std::move(request_id)));
}

void test_bounded_mpsc_contract() {
  runtime::BoundedMpscQueue<int> queue(2U);
  expect(queue.try_push(1), "first MPSC item rejected");
  expect(queue.try_push(2), "second MPSC item rejected");
  expect(!queue.try_push(3), "bounded MPSC accepted over capacity");
  expect(queue.wait_pop() == 1, "MPSC FIFO order mismatch");
  queue.close();
  expect(!queue.try_push(3), "closed MPSC accepted an item");
  expect(queue.wait_pop() == 2, "closed MPSC lost queued item");
  expect(!queue.wait_pop().has_value(), "closed empty MPSC did not terminate");
  expect_runtime_error(runtime::ErrorCode::sequence_invalid, [] {
    static_cast<void>(runtime::checked_next_journal_sequence(
        std::numeric_limits<std::uint64_t>::max()));
  });
}

void test_persist_before_expose_and_request_replay() {
  const auto directory = case_directory("normal-replay");
  const auto command = first_command();
  runtime::SubmitReceipt durable;
  {
    runtime::Runtime instance(config(directory));
    durable = instance.submit(command);
    expect(instance.journal_sequence() == 1U, "durable journal sequence did not advance");
    expect(
        std::filesystem::file_size(directory / "runtime.wal") > 0U,
        "effect was returned without durable WAL bytes");
    const auto replay = instance.submit(command);
    expect(replay.replay, "exact request replay was not classified as replay");
    auto expected = durable;
    expected.replay = true;
    expect(replay == expected, "exact request replay changed receipt bytes or IDs");
    expect(instance.journal_sequence() == 1U, "exact replay appended another WAL record");

    auto conflicting = protocol::parse_command(command);
    conflicting.body_hash =
        "sha256:cdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd";
    expect_runtime_error(runtime::ErrorCode::request_conflict, [&instance, &conflicting] {
      static_cast<void>(instance.submit(protocol::encode(conflicting)));
    });
    instance.snapshot();
  }
  {
    runtime::Runtime recovered(config(directory));
    expect(recovered.state_bytes() == durable.next_state_bytes, "recovered state bytes differ");
    expect(recovered.journal_sequence() == 1U, "recovered sequence differs");
    const auto replay = recovered.submit(command);
    expect(replay.replay && replay.effect_batch_bytes == durable.effect_batch_bytes,
           "restart replay did not return the exact durable effect");
  }
}

void test_vote_journal_recovers_before_admission() {
  const auto directory = case_directory("vote-recovery");
  const auto vote_bytes = round_config_vote_bytes();
  runtime::VoteReceipt receipt;
  {
    runtime::Runtime instance(vote_config(directory));
    receipt = instance.record_vote(vote_bytes);
    expect(!receipt.replay, "first vote was classified as replay");
    expect(receipt.frame == vote_bytes, "first vote receipt changed the persisted frame");
    instance.snapshot();
  }
  {
    runtime::Runtime recovered(vote_config(directory));
    expect(recovered.recovered_vote_count() == 1U, "vote journal was not recovered at open");
    const auto replay = recovered.record_vote(vote_bytes);
    expect(replay.replay && replay.vote_id == receipt.vote_id && replay.frame == receipt.frame,
           "recovered exact vote replay changed receipt");
    auto conflicting = protocol::parse_vote(vote_bytes);
    conflicting.body_hash =
        "sha256:bcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbc";
    expect_consensus_error(consensus::ErrorCode::conflicting_vote, [&recovered, &conflicting] {
      static_cast<void>(recovered.record_vote(protocol::encode(conflicting)));
    });
    auto changed_signature = protocol::parse_vote(vote_bytes);
    changed_signature.signature_id =
        "sha256:cdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcdcd";
    expect_consensus_error(
        consensus::ErrorCode::conflicting_vote, [&recovered, &changed_signature] {
          static_cast<void>(recovered.record_vote(protocol::encode(changed_signature)));
        });
    auto changed_sequence = protocol::parse_vote(vote_bytes);
    ++changed_sequence.durable_sequence;
    expect_consensus_error(
        consensus::ErrorCode::conflicting_vote, [&recovered, &changed_sequence] {
          static_cast<void>(recovered.record_vote(protocol::encode(changed_sequence)));
        });
    auto changed_kind = protocol::parse_vote(vote_bytes);
    changed_kind.kind = "ISC";
    expect_consensus_error(consensus::ErrorCode::conflicting_vote, [&] {
      static_cast<void>(recovered.record_vote(protocol::encode(changed_kind)));
    });
    auto unknown_kind = protocol::parse_vote(vote_bytes);
    unknown_kind.kind = "FREE_FORM";
    expect_consensus_error(consensus::ErrorCode::conflicting_vote, [&] {
      static_cast<void>(recovered.record_vote(protocol::encode(unknown_kind)));
    });
    auto changed_round = protocol::parse_vote(vote_bytes);
    changed_round.round_id = "round-conflict";
    expect_consensus_error(consensus::ErrorCode::conflicting_vote, [&] {
      static_cast<void>(recovered.record_vote(protocol::encode(changed_round)));
    });
    auto changed_height = protocol::parse_vote(vote_bytes);
    ++changed_height.height;
    expect_consensus_error(consensus::ErrorCode::conflicting_vote, [&] {
      static_cast<void>(recovered.record_vote(protocol::encode(changed_height)));
    });
    auto changed_view = protocol::parse_vote(vote_bytes);
    ++changed_view.view;
    expect_consensus_error(consensus::ErrorCode::conflicting_vote, [&] {
      static_cast<void>(recovered.record_vote(protocol::encode(changed_view)));
    });
    expect(recovered.journal_sequence() == 1U,
           "same-context byte conflicts appended a vote WAL record");
  }
}

void test_vote_recovery_revalidates_semantic_guards() {
  const auto vote_bytes = round_config_vote_bytes();
  const auto persist_vote = [&](const std::filesystem::path& directory) {
    runtime::Runtime instance(vote_config(directory));
    const auto receipt = instance.record_vote(vote_bytes);
    expect(!receipt.replay && receipt.journal_sequence == 1U,
           "recovery-guard fixture vote was not durably admitted");
  };

  const auto wrong_phase_directory = case_directory("vote-recovery-wrong-phase");
  persist_vote(wrong_phase_directory);
  auto wrong_phase = vote_config(wrong_phase_directory);
  auto state = protocol::parse_round_state(wrong_phase.initial_state_bytes);
  state.phase = protocol::RoundPhase::aggregated;
  wrong_phase.initial_state_bytes = protocol::encode(state);
  expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
    runtime::Runtime rejected(std::move(wrong_phase));
    static_cast<void>(rejected);
  });

  const auto expired_directory = case_directory("vote-recovery-expired");
  persist_vote(expired_directory);
  auto expired = vote_config(expired_directory);
  expired.vote_policy->initial_logical_tick = expired.vote_policy->hard_deadline_tick;
  expect_runtime_error(runtime::ErrorCode::recovery_mismatch, [&] {
    runtime::Runtime rejected(std::move(expired));
    static_cast<void>(rejected);
  });

  const auto abort_directory = case_directory("vote-recovery-abort-requested");
  persist_vote(abort_directory);
  auto abort_requested = vote_config(abort_directory);
  abort_requested.vote_policy->snapshot.abort_requests.push_back(
      {abort_requested.vote_policy->round_id, "INCOMPLETE_INPUT"});
  expect_runtime_error(runtime::ErrorCode::recovery_mismatch, [&] {
    runtime::Runtime rejected(std::move(abort_requested));
    static_cast<void>(rejected);
  });

  const auto policy_directory = case_directory("vote-recovery-policy-identity");
  persist_vote(policy_directory);
  auto changed_policy = vote_config(policy_directory);
  ++changed_policy.vote_policy->soft_deadline_tick;
  expect_runtime_error(runtime::ErrorCode::recovery_mismatch, [&] {
    runtime::Runtime rejected(std::move(changed_policy));
    static_cast<void>(rejected);
  });
}

void test_native_wal_sequence_is_authoritative_for_votes() {
  const auto directory = case_directory("vote-native-sequence-authority");
  const auto canonical_vote = round_config_vote_bytes();
  const auto baseline = protocol::parse_vote(canonical_vote);
  const std::string wrong_content_id =
      "sha256:0000000000000000000000000000000000000000000000000000000000000000";
  std::vector<std::pair<std::string_view, protocol::Vote>> rejected_votes;

  auto changed = baseline;
  changed.durable_sequence = 2U;
  rejected_votes.emplace_back("future native WAL sequence", changed);
  changed = baseline;
  changed.validator_id = "validator-2";
  rejected_votes.emplace_back("foreign validator", changed);
  changed = baseline;
  changed.validator_epoch_id = wrong_content_id;
  rejected_votes.emplace_back("foreign validator epoch", changed);
  changed = baseline;
  changed.round_id = "round-foreign";
  rejected_votes.emplace_back("foreign round", changed);
  changed = baseline;
  ++changed.height;
  rejected_votes.emplace_back("foreign height", changed);
  changed = baseline;
  ++changed.view;
  rejected_votes.emplace_back("foreign view", changed);
  changed = baseline;
  changed.context_id += ":foreign";
  rejected_votes.emplace_back("foreign vote context", changed);
  changed = baseline;
  changed.body_hash = wrong_content_id;
  rejected_votes.emplace_back("foreign vote body", changed);
  changed = baseline;
  changed.kind = "ISC";
  rejected_votes.emplace_back("known but unauthorized vote action", changed);

  runtime::Runtime instance(vote_config(directory));
  for (const auto& [guard, rejected_vote] : rejected_votes) {
    expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
      static_cast<void>(instance.record_vote(protocol::encode(rejected_vote)));
    });
    expect(
        instance.journal_sequence() == 0U && instance.recovered_vote_count() == 0U,
        std::string(guard) + " changed native WAL or recovered vote state");
  }
  const auto accepted = instance.record_vote(canonical_vote);
  expect(
      accepted.journal_sequence == 1U && !accepted.replay,
      "native WAL did not author the expected vote sequence");
}

void test_unverified_arithmetic_votes_never_reach_the_wal() {
  for (const auto action :
       {consensus::VoteAction::parameter, consensus::VoteAction::apply}) {
    const auto fixture = arbitrary_arithmetic_fixture(action);
    const auto directory = case_directory(
        action == consensus::VoteAction::parameter
            ? "vote-parameter-without-authoritative-inputs"
            : "vote-apply-without-authoritative-inputs");
    const auto runtime_config = [&] {
      auto result = config(directory);
      result.initial_state_bytes = protocol::encode(fixture.state);
      result.vote_policy = fixture.policy;
      return result;
    };
    const auto wal_path = directory / "runtime.wal";
    {
      runtime::Runtime instance(runtime_config());
      expect(
          !std::filesystem::exists(wal_path),
          "arithmetic negative created a WAL before voting");
      expect_consensus_error(consensus::ErrorCode::vote_admission_rejected, [&] {
        static_cast<void>(instance.record_vote(protocol::encode(fixture.vote)));
      });
      expect(
          instance.journal_sequence() == 0U && instance.recovered_vote_count() == 0U &&
              !std::filesystem::exists(wal_path),
          "unverified arithmetic vote changed or created durable WAL state");
    }
    {
      runtime::Runtime recovered(runtime_config());
      expect(
          recovered.journal_sequence() == 0U && recovered.recovered_vote_count() == 0U &&
              !std::filesystem::exists(wal_path),
          "recovery observed a rejected arithmetic vote");
    }
  }
}

void test_committed_submit_invalidates_vote_authority_across_restart() {
  const auto directory = case_directory("vote-authority-invalidation");
  auto fixture = vote_fixture::full(consensus::VoteAction::round_config);
  const auto view_fixture =
      vote_fixture::full(consensus::VoteAction::view_change, fixture.state);
  auto runtime_config = config(directory);
  runtime_config.initial_state_bytes = protocol::encode(fixture.state);
  runtime_config.vote_policy = fixture.policy;
  auto first_vote = fixture.vote;
  auto& policy = *runtime_config.vote_policy;
  policy.initial_logical_tick = policy.soft_deadline_tick;
  policy.snapshot.timeout_observations =
      view_fixture.policy.snapshot.timeout_observations;
  policy.snapshot.view_change_bodies =
      view_fixture.policy.snapshot.view_change_bodies;
  const auto second_candidate = view_fixture.candidate;
  policy.candidates.push_back(second_candidate);
  std::sort(policy.candidates.begin(), policy.candidates.end(), [](const auto& left, const auto& right) {
    return std::tuple{
               left.height,
               left.view,
               static_cast<std::uint32_t>(left.action),
               std::string_view(left.context_id)} <
           std::tuple{
               right.height,
               right.view,
               static_cast<std::uint32_t>(right.action),
               std::string_view(right.context_id)};
  });
  auto second_vote = view_fixture.vote;
  second_vote.durable_sequence = 3U;
  const auto first_bytes = protocol::encode(first_vote);
  const auto second_bytes = protocol::encode(second_vote);
  runtime::VoteReceipt first_receipt;
  {
    runtime::Runtime instance(runtime_config);
    first_receipt = instance.record_vote(first_bytes);
    expect(!first_receipt.replay && first_receipt.journal_sequence == 1U,
           "initial vote was not committed before authority invalidation");
    const protocol::Command transition{
        "validator-1",
        "sha256:abababababababababababababababababababababababababababababababab",
        "ADVANCE_VIEW",
        fixture.state.height,
        policy.initial_logical_tick,
        "invalidate-vote-authority",
        fixture.state.round_id,
        fixture.state.view + 1U,
    };
    static_cast<void>(instance.submit(protocol::encode(transition)));
    expect(instance.journal_sequence() == 2U, "committed submit did not advance the WAL");
    const auto replay = instance.record_vote(first_bytes);
    expect(replay.replay && replay.vote_id == first_receipt.vote_id,
           "exact vote replay was not classified before invalidation");
    auto conflict = first_vote;
    conflict.body_hash =
        "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
    expect_consensus_error(consensus::ErrorCode::conflicting_vote, [&] {
      static_cast<void>(instance.record_vote(protocol::encode(conflict)));
    });
    expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
      static_cast<void>(instance.record_vote(second_bytes));
    });
    expect(instance.journal_sequence() == 2U, "invalidated vote appended a WAL record");
  }
  {
    runtime::Runtime recovered(runtime_config);
    expect(recovered.journal_sequence() == 2U, "authority-invalidation WAL did not recover");
    const auto replay = recovered.record_vote(first_bytes);
    expect(replay.replay && replay.vote_id == first_receipt.vote_id,
           "restart changed exact replay classification after invalidation");
    expect_consensus_error(consensus::ErrorCode::vote_policy_invalid, [&] {
      static_cast<void>(recovered.record_vote(second_bytes));
    });
    expect(recovered.journal_sequence() == 2U,
           "restart admitted a new vote from invalidated authority");
  }
}

[[nodiscard]] bool durable_crash(runtime::CrashPoint point) {
  return point == runtime::CrashPoint::after_durability_before_commit ||
         point == runtime::CrashPoint::after_commit_before_effect_return ||
         point == runtime::CrashPoint::after_effect_copy_before_return;
}

void test_crash_matrix_and_torn_tail_recovery() {
  const std::vector<runtime::CrashPoint> points{
      runtime::CrashPoint::before_wal_append,
      runtime::CrashPoint::during_wal_append,
      runtime::CrashPoint::after_wal_append_before_durability,
      runtime::CrashPoint::after_durability_before_commit,
      runtime::CrashPoint::after_commit_before_effect_return,
      runtime::CrashPoint::after_effect_copy_before_return,
  };
  std::size_t index = 0U;
  for (const auto point : points) {
    const auto directory = case_directory("crash-" + std::to_string(index++));
    const auto command = first_command("crash-request");
    {
      runtime::Runtime instance(config(directory));
      expect_runtime_error(runtime::ErrorCode::simulated_crash, [&instance, &command, point] {
        static_cast<void>(instance.submit(command, point));
      });
      expect(!instance.accepting(), "crashed runtime continued accepting commands");
    }
    {
      runtime::Runtime recovered(config(directory));
      if (durable_crash(point)) {
        expect(recovered.journal_sequence() == 1U, "durable crash record was lost");
        expect(recovered.submit(command).replay, "durable crash replay appended twice");
      } else {
        expect(recovered.journal_sequence() == 0U, "nondurable crash became visible");
        expect(!recovered.submit(command).replay, "nondurable crash fabricated a replay");
      }
    }
  }
}

void test_vote_wal_crash_matrix() {
  const auto vote = round_config_vote_bytes();
  canonical::Bytes canonical_receipt;
  {
    const auto directory = case_directory("vote-crash-control");
    runtime::Runtime control(vote_config(directory));
    canonical_receipt = runtime::encode_vote_receipt_v1(control.record_vote(vote));
  }

  const std::vector<runtime::CrashPoint> points{
      runtime::CrashPoint::before_wal_append,
      runtime::CrashPoint::during_wal_append,
      runtime::CrashPoint::after_wal_append_before_durability,
      runtime::CrashPoint::after_durability_before_commit,
      runtime::CrashPoint::after_commit_before_effect_return,
      runtime::CrashPoint::after_effect_copy_before_return,
  };
  std::size_t index = 0U;
  for (const auto point : points) {
    const auto directory =
        case_directory("vote-crash-" + std::to_string(index++));
    {
      runtime::Runtime instance(vote_config(directory));
      expect_runtime_error(runtime::ErrorCode::simulated_crash, [&] {
        static_cast<void>(instance.record_vote(vote, point));
      });
      expect(!instance.accepting(), "vote-crashed runtime remained accepting");
    }
    {
      runtime::Runtime recovered(vote_config(directory));
      if (durable_crash(point)) {
        expect(
            recovered.journal_sequence() == 1U &&
                recovered.recovered_vote_count() == 1U,
            "durable vote crash record was lost or duplicated");
        const auto replay = recovered.record_vote(vote);
        expect(replay.replay, "durable vote crash was not classified as replay");
        expect(
            runtime::encode_vote_receipt_v1(replay) == canonical_receipt,
            "durable vote crash changed canonical receipt bytes");
      } else {
        expect(
            recovered.journal_sequence() == 0U &&
                recovered.recovered_vote_count() == 0U,
            "nondurable vote crash became visible");
        const auto accepted = recovered.record_vote(vote);
        expect(!accepted.replay, "nondurable vote crash fabricated a replay");
        expect(
            runtime::encode_vote_receipt_v1(accepted) == canonical_receipt,
            "nondurable vote retry changed canonical receipt bytes");
      }
    }
  }
}

void flip_durable_byte(const std::filesystem::path& path, std::streamoff offset) {
  std::fstream file(path, std::ios::in | std::ios::out | std::ios::binary);
  expect(file.good(), "cannot open durable test file for corruption");
  file.seekg(offset);
  char value = 0;
  file.read(&value, 1);
  expect(file.gcount() == 1, "durable test file is too short");
  value = static_cast<char>(static_cast<unsigned char>(value) ^ 0x01U);
  file.seekp(offset);
  file.write(&value, 1);
  file.flush();
  expect(file.good(), "cannot write durable corruption fixture");
}

[[nodiscard]] canonical::Bytes read_durable_bytes(const std::filesystem::path& path) {
  std::ifstream input(path, std::ios::binary);
  expect(input.good(), "cannot open durable binary fixture");
  const std::vector<char> characters{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  canonical::Bytes result;
  result.reserve(characters.size());
  for (const char character : characters) {
    result.push_back(static_cast<std::byte>(static_cast<unsigned char>(character)));
  }
  return result;
}

void write_durable_bytes(
    const std::filesystem::path& path,
    std::span<const std::byte> bytes) {
  std::ofstream output(path, std::ios::binary | std::ios::trunc);
  expect(output.good(), "cannot create durable binary fixture");
  output.write(
      reinterpret_cast<const char*>(bytes.data()),
      static_cast<std::streamsize>(bytes.size()));
  output.close();
  expect(output.good(), "cannot finish durable binary fixture");
}

[[nodiscard]] std::uint32_t read_be_u32(
    std::span<const std::byte> bytes,
    std::size_t offset) {
  expect(offset <= bytes.size() && bytes.size() - offset >= 4U, "truncated WAL u32 fixture");
  std::uint32_t result = 0U;
  for (std::size_t index = 0U; index < 4U; ++index) {
    result = (result << 8U) | std::to_integer<std::uint8_t>(bytes[offset + index]);
  }
  return result;
}

[[nodiscard]] std::pair<std::size_t, std::size_t> wal_section(
    std::span<const std::byte> frame,
    std::size_t section_index) {
  constexpr std::size_t wal_entry_prefix_bytes = 24U;
  constexpr std::size_t wal_checksum_bytes = 32U;
  expect(frame.size() >= wal_entry_prefix_bytes + wal_checksum_bytes, "vote WAL fixture is short");
  const auto payload_end = frame.size() - wal_checksum_bytes;
  std::size_t cursor = wal_entry_prefix_bytes;
  for (std::size_t index = 0U; index <= section_index; ++index) {
    expect(cursor <= payload_end && payload_end - cursor >= 4U, "vote WAL section is truncated");
    const auto length = static_cast<std::size_t>(read_be_u32(frame, cursor));
    cursor += 4U;
    expect(length <= payload_end - cursor, "vote WAL section exceeds its frame");
    if (index == section_index) {
      return {cursor, length};
    }
    cursor += length;
  }
  fail("vote WAL section index is unreachable");
}

void replace_wal_checksum(canonical::Bytes& frame) {
  constexpr std::size_t wal_checksum_bytes = 32U;
  expect(frame.size() > wal_checksum_bytes, "vote WAL fixture has no checksum body");
  const auto checksum_offset = frame.size() - wal_checksum_bytes;
  const auto digest = decode_hex(canonical::sha256_hex(
      std::span<const std::byte>(frame).first(checksum_offset)));
  expect(digest.size() == wal_checksum_bytes, "vote WAL replacement checksum size differs");
  std::copy(digest.begin(), digest.end(), frame.begin() + static_cast<std::ptrdiff_t>(checksum_offset));
}

void test_vote_wal_corruption_fails_closed() {
  const auto vote = round_config_vote_bytes();

  const auto checksum_directory = case_directory("vote-wal-checksum-corrupt");
  const auto checksum_wal = checksum_directory / "runtime.wal";
  {
    runtime::Runtime instance(vote_config(checksum_directory));
    static_cast<void>(instance.record_vote(vote));
  }
  const auto checksum_frame = read_durable_bytes(checksum_wal);
  const auto [vote_offset, vote_size] = wal_section(checksum_frame, 0U);
  expect(vote_size > 0U, "durable vote WAL frame has an empty vote section");
  flip_durable_byte(checksum_wal, static_cast<std::streamoff>(vote_offset));
  const auto checksum_corruption = read_durable_bytes(checksum_wal);
  expect_runtime_error(runtime::ErrorCode::wal_corrupt, [&] {
    runtime::Runtime rejected(vote_config(checksum_directory));
  });
  expect(
      read_durable_bytes(checksum_wal) == checksum_corruption,
      "checksum-corrupt vote WAL was mutated during failed recovery");

  const auto semantic_directory = case_directory("vote-wal-semantic-corrupt");
  const auto semantic_wal = semantic_directory / "runtime.wal";
  {
    runtime::Runtime instance(vote_config(semantic_directory));
    static_cast<void>(instance.record_vote(vote));
  }
  auto semantic_frame = read_durable_bytes(semantic_wal);
  const auto [policy_offset, policy_size] = wal_section(semantic_frame, 3U);
  expect(policy_size > 0U, "durable vote WAL frame has no policy identity");
  semantic_frame[policy_offset] ^= std::byte{0x01U};
  replace_wal_checksum(semantic_frame);
  write_durable_bytes(semantic_wal, semantic_frame);
  expect_runtime_error(runtime::ErrorCode::recovery_mismatch, [&] {
    runtime::Runtime rejected(vote_config(semantic_directory));
  });
  expect(
      read_durable_bytes(semantic_wal) == semantic_frame,
      "semantic-corrupt vote WAL was mutated during failed recovery");
}

#if !defined(_WIN32)

void write_text(const std::filesystem::path& path, std::string_view value) {
  std::ofstream output(path, std::ios::binary | std::ios::trunc);
  expect(output.good(), "cannot create adversarial durable-file fixture");
  output.write(value.data(), static_cast<std::streamsize>(value.size()));
  output.close();
  expect(output.good(), "cannot finish adversarial durable-file fixture");
}

[[nodiscard]] std::string read_text(const std::filesystem::path& path) {
  std::ifstream input(path, std::ios::binary);
  expect(input.good(), "cannot open adversarial durable-file fixture");
  return {
      std::istreambuf_iterator<char>(input),
      std::istreambuf_iterator<char>(),
  };
}

void expect_rename(
    const std::filesystem::path& source,
    const std::filesystem::path& target,
    std::string_view message) {
  std::error_code error;
  std::filesystem::rename(source, target, error);
  expect(!error, message);
}

void expect_symlink(
    const std::filesystem::path& target,
    const std::filesystem::path& link,
    std::string_view message) {
  std::error_code error;
  std::filesystem::create_symlink(target, link, error);
  expect(!error, message);
}

void expect_hard_link(
    const std::filesystem::path& target,
    const std::filesystem::path& link,
    std::string_view message) {
  std::error_code error;
  std::filesystem::create_hard_link(target, link, error);
  expect(!error, message);
}

void test_posix_preflight_to_recovery_wal_substitution_fails_closed() {
  const auto directory = case_directory("posix-preflight-recovery-wal-substitution");
  const auto wal = directory / "runtime.wal";
  const auto preflighted = directory / "runtime.wal.preflighted";
  write_text(wal, "");

  struct stat status {};
  expect(::lstat(wal.c_str(), &status) == 0, "cannot inspect preflighted WAL identity");
  auto runtime_config = config(directory);
  runtime_config.expected_wal_identity = runtime::DurableFileIdentity{
      static_cast<std::uint64_t>(status.st_dev),
      static_cast<std::uint64_t>(status.st_ino),
  };

  expect_rename(wal, preflighted, "cannot displace preflighted WAL");
  write_text(wal, "");
  struct stat replacement_status {};
  expect(::lstat(wal.c_str(), &replacement_status) == 0,
         "cannot inspect replacement WAL identity");
  expect(
      replacement_status.st_dev != status.st_dev ||
          replacement_status.st_ino != status.st_ino,
      "replacement WAL unexpectedly reused the preflighted identity");

  expect_runtime_error(runtime::ErrorCode::durable_binding_lost, [&runtime_config] {
    runtime::Runtime rejected(std::move(runtime_config));
    static_cast<void>(rejected);
  });
  expect(
      std::filesystem::file_size(wal) == 0U &&
          std::filesystem::file_size(preflighted) == 0U,
      "identity handoff rejection changed either WAL inode");
}

void test_posix_wal_leaf_identity_is_pinned() {
  {
    const auto root = case_directory("posix-directory-startup-symlink");
    const auto actual = root / "actual";
    const auto configured = root / "configured";
    std::error_code create_error;
    std::filesystem::create_directories(actual, create_error);
    expect(!create_error, "cannot create configured-directory symlink target");
    expect_symlink(actual, configured, "cannot create configured-directory symlink fixture");
    expect_runtime_error(runtime::ErrorCode::io_error, [&configured] {
      runtime::Runtime rejected(config(configured));
    });
    expect(
        !std::filesystem::exists(actual / "runtime.wal"),
        "runtime startup followed a configured-directory symlink");
  }

  {
    const auto directory = case_directory("posix-wal-startup-symlink");
    const auto victim = directory / "victim";
    write_text(victim, "victim-stays-unchanged");
    expect_symlink(victim, directory / "runtime.wal", "cannot create WAL symlink fixture");
    expect_runtime_error(runtime::ErrorCode::io_error, [&directory] {
      runtime::Runtime rejected(config(directory));
    });
    expect(read_text(victim) == "victim-stays-unchanged", "WAL startup followed a symlink");
  }

  {
    const auto directory = case_directory("posix-wal-startup-hardlink");
    const auto wal = directory / "runtime.wal";
    write_text(wal, "");
    expect_hard_link(wal, directory / "runtime.wal.alias", "cannot create WAL hard-link fixture");
    expect_runtime_error(runtime::ErrorCode::io_error, [&directory] {
      runtime::Runtime rejected(config(directory));
    });
  }

  {
    const auto directory = case_directory("posix-wal-symlink-rebind");
    const auto wal = directory / "runtime.wal";
    const auto saved = directory / "runtime.wal.saved";
    const auto victim = directory / "victim";
    runtime::Runtime instance(config(directory));
    static_cast<void>(instance.submit(first_command("wal-symlink-first")));
    const auto state_before = instance.state_bytes();
    const auto saved_size = std::filesystem::file_size(wal);
    expect_rename(wal, saved, "cannot displace pinned WAL");
    write_text(victim, "victim-stays-unchanged");
    expect_symlink(victim, wal, "cannot replace WAL with a symlink");
    auto next_state = protocol::parse_round_state(state_before);
    const auto next = protocol::encode(command_for(next_state, "wal-symlink-second"));
    expect_runtime_error(runtime::ErrorCode::durable_binding_lost, [&instance, &next] {
      static_cast<void>(instance.submit(next));
    });
    expect(!instance.accepting(), "WAL symlink rebind did not stop the runtime");
    expect(instance.journal_sequence() == 1U, "WAL symlink rebind advanced durable sequence");
    expect(instance.state_bytes() == state_before, "WAL symlink rebind exposed candidate state");
    expect(std::filesystem::file_size(saved) == saved_size, "WAL symlink rebind appended elsewhere");
    expect(read_text(victim) == "victim-stays-unchanged", "WAL rebind followed a symlink");
  }

  {
    const auto directory = case_directory("posix-wal-regular-rebind");
    const auto wal = directory / "runtime.wal";
    const auto saved = directory / "runtime.wal.saved";
    runtime::Runtime instance(config(directory));
    static_cast<void>(instance.submit(first_command("wal-regular-first")));
    const auto state_before = instance.state_bytes();
    const auto saved_size = std::filesystem::file_size(wal);
    expect_rename(wal, saved, "cannot displace pinned WAL for regular replacement");
    write_text(wal, "replacement-must-not-receive-an-append");
    auto next_state = protocol::parse_round_state(state_before);
    const auto next = protocol::encode(command_for(next_state, "wal-regular-second"));
    expect_runtime_error(runtime::ErrorCode::durable_binding_lost, [&instance, &next] {
      static_cast<void>(instance.submit(next));
    });
    expect(!instance.accepting(), "regular WAL rebind did not stop the runtime");
    expect(instance.journal_sequence() == 1U, "regular WAL rebind advanced durable sequence");
    expect(instance.state_bytes() == state_before, "regular WAL rebind exposed candidate state");
    expect(std::filesystem::file_size(saved) == saved_size, "regular WAL rebind changed pinned bytes");
    expect(
        read_text(wal) == "replacement-must-not-receive-an-append",
        "regular WAL replacement received consensus bytes");
  }

  {
    const auto directory = case_directory("posix-directory-rebind");
    auto displaced = directory;
    displaced += ".pinned";
    std::error_code cleanup_error;
    std::filesystem::remove_all(displaced, cleanup_error);
    expect(!cleanup_error, "cannot clean displaced-directory fixture");
    {
      runtime::Runtime instance(config(directory));
      expect_rename(directory, displaced, "cannot displace pinned runtime directory");
      std::error_code create_error;
      std::filesystem::create_directories(directory, create_error);
      expect(!create_error, "cannot create replacement runtime directory");
      const auto command = first_command("directory-rebind");
      expect_runtime_error(runtime::ErrorCode::durable_binding_lost, [&instance, &command] {
        static_cast<void>(instance.submit(command));
      });
      expect(!instance.accepting(), "runtime directory rebind did not stop the runtime");
      expect(instance.journal_sequence() == 0U, "runtime directory rebind appended a WAL record");
      expect(
          !std::filesystem::exists(directory / "runtime.wal"),
          "runtime directory rebind created a WAL in the replacement directory");
    }
    std::filesystem::remove_all(displaced, cleanup_error);
    expect(!cleanup_error, "cannot remove displaced-directory fixture");
  }

  {
    const auto directory = case_directory("posix-directory-same-inode-symlink-back");
    auto displaced = directory;
    displaced += ".pinned";
    std::error_code cleanup_error;
    std::filesystem::remove_all(displaced, cleanup_error);
    expect(!cleanup_error, "cannot clean same-inode displaced-directory fixture");
    {
      runtime::Runtime instance(config(directory));
      static_cast<void>(instance.submit(first_command("directory-symlink-back-first")));
      const auto state_before = instance.state_bytes();
      const auto wal_size = std::filesystem::file_size(directory / "runtime.wal");
      expect_rename(directory, displaced, "cannot displace same-inode runtime directory");
      expect_symlink(displaced, directory, "cannot link configured path to the pinned inode");
      const auto next_state = protocol::parse_round_state(state_before);
      const auto next =
          protocol::encode(command_for(next_state, "directory-symlink-back-second"));
      expect_runtime_error(runtime::ErrorCode::durable_binding_lost, [&instance, &next] {
        static_cast<void>(instance.submit(next));
      });
      expect(!instance.accepting(), "same-inode directory symlink-back did not stop the runtime");
      expect(
          instance.journal_sequence() == 1U,
          "same-inode directory symlink-back advanced durable sequence");
      expect(
          instance.state_bytes() == state_before,
          "same-inode directory symlink-back exposed candidate state");
      expect(
          std::filesystem::file_size(displaced / "runtime.wal") == wal_size,
          "same-inode directory symlink-back appended through the configured pathname");
    }
    std::filesystem::remove(directory, cleanup_error);
    expect(!cleanup_error, "cannot remove same-inode configured-directory symlink");
    std::filesystem::remove_all(displaced, cleanup_error);
    expect(!cleanup_error, "cannot remove same-inode displaced-directory fixture");
  }
}

void test_posix_snapshot_leaf_hardening() {
  {
    const auto directory = case_directory("posix-snapshot-stale-regular-temp");
    const auto temporary = directory / "runtime.snapshot.tmp";
    runtime::Runtime instance(config(directory));
    static_cast<void>(instance.submit(first_command("snapshot-stale-regular-first")));
    write_text(temporary, "stale-snapshot-temp-must-remain");
    struct stat before {};
    expect(::lstat(temporary.c_str(), &before) == 0, "cannot inspect stale snapshot temporary");
    expect_runtime_error(runtime::ErrorCode::io_error, [&instance] { instance.snapshot(); });
    struct stat after {};
    expect(::lstat(temporary.c_str(), &after) == 0, "snapshot removed stale regular temporary");
    expect(
        before.st_dev == after.st_dev && before.st_ino == after.st_ino &&
            read_text(temporary) == "stale-snapshot-temp-must-remain",
        "snapshot changed the stale regular temporary inode or bytes");
    expect(
        !std::filesystem::exists(directory / "runtime.snapshot"),
        "stale regular temporary allowed snapshot installation");
  }

  {
    const auto directory = case_directory("posix-snapshot-temp-symlink");
    const auto victim = directory / "victim";
    const auto temporary = directory / "runtime.snapshot.tmp";
    runtime::Runtime instance(config(directory));
    static_cast<void>(instance.submit(first_command("snapshot-temp-first")));
    write_text(victim, "victim-stays-unchanged");
    expect_symlink(victim, temporary, "cannot create snapshot temporary symlink fixture");
    expect_runtime_error(runtime::ErrorCode::io_error, [&instance] { instance.snapshot(); });
    expect(read_text(victim) == "victim-stays-unchanged", "snapshot temporary symlink was followed");
    expect(
        !std::filesystem::exists(directory / "runtime.snapshot"),
        "failed snapshot temporary attack installed a target");
    std::error_code remove_error;
    std::filesystem::remove(temporary, remove_error);
    expect(!remove_error, "cannot remove snapshot temporary symlink fixture");
    instance.snapshot();
    expect(
        std::filesystem::is_regular_file(directory / "runtime.snapshot") &&
            std::filesystem::hard_link_count(directory / "runtime.snapshot") == 1U,
        "descriptor-relative snapshot regression did not install one regular target");
    expect(!std::filesystem::exists(temporary), "successful snapshot left its temporary leaf");
  }

  {
    const auto directory = case_directory("posix-snapshot-target-symlink");
    const auto victim = directory / "victim";
    const auto target = directory / "runtime.snapshot";
    runtime::Runtime instance(config(directory));
    static_cast<void>(instance.submit(first_command("snapshot-target-first")));
    write_text(victim, "victim-stays-unchanged");
    expect_symlink(victim, target, "cannot create snapshot target symlink fixture");
    expect_runtime_error(runtime::ErrorCode::io_error, [&instance] { instance.snapshot(); });
    expect(read_text(victim) == "victim-stays-unchanged", "snapshot target symlink was followed");
    expect(std::filesystem::is_symlink(target), "snapshot target symlink was unexpectedly replaced");
  }

  {
    const auto directory = case_directory("posix-snapshot-target-hardlink");
    const auto target = directory / "runtime.snapshot";
    runtime::Runtime instance(config(directory));
    static_cast<void>(instance.submit(first_command("snapshot-hardlink-first")));
    write_text(target, "hard-linked-target");
    expect_hard_link(
        target,
        directory / "runtime.snapshot.alias",
        "cannot create snapshot target hard-link fixture");
    expect_runtime_error(runtime::ErrorCode::io_error, [&instance] { instance.snapshot(); });
    expect(read_text(target) == "hard-linked-target", "multi-link snapshot target was overwritten");
  }

  {
    const auto directory = case_directory("posix-snapshot-read-rebind");
    const auto target = directory / "runtime.snapshot";
    const auto saved = directory / "runtime.snapshot.saved";
    const auto victim = directory / "victim";
    {
      runtime::Runtime instance(config(directory));
      static_cast<void>(instance.submit(first_command("snapshot-read-first")));
      instance.snapshot();
    }
    expect_rename(target, saved, "cannot displace durable snapshot");
    write_text(victim, "victim-stays-unchanged");
    expect_symlink(victim, target, "cannot replace durable snapshot with a symlink");
    expect_runtime_error(runtime::ErrorCode::snapshot_corrupt, [&directory] {
      runtime::Runtime rejected(config(directory));
    });
    expect(read_text(victim) == "victim-stays-unchanged", "snapshot recovery followed a symlink");
  }
}

void test_posix_snapshot_uses_wal_directory_anchor() {
  {
    const auto directory = case_directory("posix-snapshot-directory-rebind");
    auto displaced = directory;
    displaced += ".pinned";
    std::error_code cleanup_error;
    std::filesystem::remove_all(displaced, cleanup_error);
    expect(!cleanup_error, "cannot clean snapshot displaced-directory fixture");
    {
      runtime::Runtime instance(config(directory));
      static_cast<void>(instance.submit(first_command("snapshot-directory-rebind")));
      expect_rename(directory, displaced, "cannot displace snapshot runtime directory");
      std::error_code create_error;
      std::filesystem::create_directories(directory, create_error);
      expect(!create_error, "cannot create replacement snapshot runtime directory");
      expect_runtime_error(runtime::ErrorCode::durable_binding_lost, [&instance] {
        instance.snapshot();
      });
      expect(!instance.accepting(), "snapshot directory rebind did not stop the runtime");
      expect(
          !std::filesystem::exists(directory / "runtime.snapshot"),
          "snapshot directory rebind wrote into the replacement directory");
      expect(
          !std::filesystem::exists(displaced / "runtime.snapshot"),
          "snapshot directory rebind wrote through the pinned directory descriptor");
    }
    std::filesystem::remove_all(displaced, cleanup_error);
    expect(!cleanup_error, "cannot remove snapshot displaced-directory fixture");
  }

  {
    const auto directory = case_directory("posix-snapshot-same-inode-symlink-back");
    auto displaced = directory;
    displaced += ".pinned";
    std::error_code cleanup_error;
    std::filesystem::remove_all(displaced, cleanup_error);
    expect(!cleanup_error, "cannot clean snapshot same-inode displaced-directory fixture");
    {
      runtime::Runtime instance(config(directory));
      static_cast<void>(instance.submit(first_command("snapshot-symlink-back")));
      expect_rename(directory, displaced, "cannot displace snapshot same-inode directory");
      expect_symlink(
          displaced,
          directory,
          "cannot link snapshot configured path to the pinned directory inode");
      expect_runtime_error(runtime::ErrorCode::durable_binding_lost, [&instance] {
        instance.snapshot();
      });
      expect(
          !instance.accepting(),
          "snapshot same-inode directory symlink-back did not stop the runtime");
      expect(
          !std::filesystem::exists(displaced / "runtime.snapshot"),
          "snapshot same-inode directory symlink-back installed a snapshot");
    }
    std::filesystem::remove(directory, cleanup_error);
    expect(!cleanup_error, "cannot remove snapshot configured-directory symlink");
    std::filesystem::remove_all(displaced, cleanup_error);
    expect(!cleanup_error, "cannot remove snapshot same-inode displaced-directory fixture");
  }
}

#endif

void test_corruption_fails_closed() {
  const auto wal_directory = case_directory("wal-corrupt");
  {
    runtime::Runtime instance(config(wal_directory));
    static_cast<void>(instance.submit(first_command()));
  }
  flip_durable_byte(wal_directory / "runtime.wal", 20);
  expect_runtime_error(runtime::ErrorCode::wal_corrupt, [&wal_directory] {
    runtime::Runtime rejected(config(wal_directory));
  });

  const auto snapshot_directory = case_directory("snapshot-corrupt");
  {
    runtime::Runtime instance(config(snapshot_directory));
    static_cast<void>(instance.submit(first_command()));
    instance.snapshot();
  }
  flip_durable_byte(snapshot_directory / "runtime.snapshot", 20);
  expect_runtime_error(runtime::ErrorCode::snapshot_corrupt, [&snapshot_directory] {
    runtime::Runtime rejected(config(snapshot_directory));
  });
}

void test_concurrent_producers_have_one_serial_state() {
  const auto directory = case_directory("mpsc-producers");
  runtime::Runtime instance(config(directory));
  std::vector<std::future<void>> producers;
  for (std::uint32_t producer = 0; producer < 4U; ++producer) {
    producers.push_back(std::async(std::launch::async, [&instance, producer] {
      for (std::uint32_t item = 0; item < 5U; ++item) {
        const auto request = "producer-" + std::to_string(producer) + "-" + std::to_string(item);
        static_cast<void>(instance.submit(first_command(request)));
      }
    }));
  }
  for (auto& producer : producers) {
    producer.get();
  }
  const auto state = protocol::parse_round_state(instance.state_bytes());
  expect(state.committed_ticket_count == 20U, "MPSC submissions did not serialize exactly once");
  expect(instance.journal_sequence() == 20U, "MPSC journal sequence is not exact");
}

void test_stale_command_rejected_without_append() {
  const auto directory = case_directory("stale-command");
  runtime::Runtime instance(config(directory));
  auto state = protocol::parse_round_state(instance.state_bytes());
  const protocol::Command view_change{
      "validator-1",
      "sha256:abababababababababababababababababababababababababababababababab",
      "ADVANCE_VIEW",
      state.height,
      10U,
      "advance-view",
      state.round_id,
      1U,
  };
  static_cast<void>(instance.submit(protocol::encode(view_change)));
  const auto stale = protocol::encode(command_for(state, "stale-view"));
  try {
    static_cast<void>(instance.submit(stale));
  } catch (const delta::core::transition::TransitionError&) {
    expect(instance.journal_sequence() == 1U, "stale command appended a journal record");
    return;
  }
  fail("stale command was accepted after view change");
}

void test_uninterrupted_and_replayed_execution_are_identical() {
  const auto directory = case_directory("replay-equivalence");
  std::vector<canonical::Bytes> commands;
  std::vector<runtime::SubmitReceipt> receipts;
  canonical::Bytes final_state;
  {
    runtime::Runtime uninterrupted(config(directory));
    auto state = protocol::parse_round_state(uninterrupted.state_bytes());
    commands.push_back(protocol::encode(command_for(state, "equivalence-commit-1")));
    receipts.push_back(uninterrupted.submit(commands.back()));
    state = protocol::parse_round_state(uninterrupted.state_bytes());
    commands.push_back(protocol::encode(command_for(state, "equivalence-commit-2")));
    receipts.push_back(uninterrupted.submit(commands.back()));
    state = protocol::parse_round_state(uninterrupted.state_bytes());
    auto availability = command_for(state, "equivalence-availability");
    availability.command_kind = "ACCEPT_AVAILABILITY";
    commands.push_back(protocol::encode(availability));
    receipts.push_back(uninterrupted.submit(commands.back()));
    final_state = uninterrupted.state_bytes();
    uninterrupted.snapshot();
  }
  {
    runtime::Runtime replayed(config(directory));
    expect(replayed.state_bytes() == final_state, "WAL/snapshot replay changed final state bytes");
    expect(replayed.journal_sequence() == receipts.size(), "replayed sequence differs");
    for (std::size_t index = 0; index < commands.size(); ++index) {
      auto replay = replayed.submit(commands[index]);
      expect(replay.replay, "recovered command was not an idempotent replay");
      auto expected = receipts[index];
      expected.replay = true;
      expect(replay == expected, "replayed state/effect/WAL receipt differs byte-for-byte");
    }
    expect(replayed.state_bytes() == final_state, "receipt replay advanced final state twice");
  }
}

}  // namespace

int main() {
  try {
    test_bounded_mpsc_contract();
    test_persist_before_expose_and_request_replay();
    test_vote_journal_recovers_before_admission();
    test_vote_recovery_revalidates_semantic_guards();
    test_native_wal_sequence_is_authoritative_for_votes();
    test_unverified_arithmetic_votes_never_reach_the_wal();
    test_committed_submit_invalidates_vote_authority_across_restart();
    test_crash_matrix_and_torn_tail_recovery();
    test_vote_wal_crash_matrix();
    test_vote_wal_corruption_fails_closed();
#if !defined(_WIN32)
    test_posix_preflight_to_recovery_wal_substitution_fails_closed();
    test_posix_wal_leaf_identity_is_pinned();
    test_posix_snapshot_leaf_hardening();
    test_posix_snapshot_uses_wal_directory_anchor();
#endif
    test_corruption_fails_closed();
    test_concurrent_producers_have_one_serial_state();
    test_stale_command_rejected_without_append();
    test_uninterrupted_and_replayed_execution_are_identical();
  } catch (const std::exception& error) {
    std::cerr << "delta_runtime test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta_runtime tests passed\n";
  return 0;
}
