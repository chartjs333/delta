#include <delta/core/canonical.hpp>
#include <delta/core/consensus.hpp>
#include <delta/core/protocol.hpp>
#include <delta/core/transition.hpp>
#include <delta/runtime/bounded_mpsc.hpp>
#include <delta/runtime/runtime.hpp>

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <future>
#include <iostream>
#include <iterator>
#include <regex>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace canonical = delta::core::canonical;
namespace consensus = delta::core::consensus;
namespace protocol = delta::core::protocol;
namespace runtime = delta::runtime;

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
  return runtime::Config{directory, golden(5U), 64U};
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
  const auto vote_bytes = golden(3U);
  runtime::VoteReceipt receipt;
  {
    runtime::Runtime instance(config(directory));
    receipt = instance.record_vote(vote_bytes);
    expect(!receipt.replay, "first vote was classified as replay");
    instance.snapshot();
  }
  {
    runtime::Runtime recovered(config(directory));
    expect(recovered.recovered_vote_count() == 1U, "vote journal was not recovered at open");
    const auto replay = recovered.record_vote(vote_bytes);
    expect(replay.replay && replay.vote_id == receipt.vote_id,
           "recovered exact vote replay changed receipt");
    auto conflicting = protocol::parse_vote(vote_bytes);
    conflicting.body_hash =
        "sha256:bcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbcbc";
    expect_consensus_error(consensus::ErrorCode::conflicting_vote, [&recovered, &conflicting] {
      static_cast<void>(recovered.record_vote(protocol::encode(conflicting)));
    });
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
    test_crash_matrix_and_torn_tail_recovery();
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
