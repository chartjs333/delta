#include "fixture_support.hpp"

#include <delta/core/canonical.hpp>
#include <delta/core/protocol.hpp>
#include <delta/runtime/runtime.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <future>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <sstream>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace canonical = delta::core::canonical;
namespace protocol = delta::core::protocol;
namespace runtime = delta::runtime;
namespace test = delta::test;

namespace {

struct Ticket {
  std::string id;
  std::string commitment_id;
  std::string availability_id;
};

struct RunResult {
  canonical::Bytes final_state;
  std::string final_state_id;
  std::string effect_transcript_sha256;
  std::string wal_transcript_sha256;
  std::string wal_file_sha256;
  std::vector<canonical::Bytes> commands;
  std::vector<runtime::SubmitReceipt> receipts;

  bool operator==(const RunResult&) const = default;
};

[[nodiscard]] std::string ticket_id(std::uint32_t index) {
  std::ostringstream output;
  output << "ticket-" << std::setw(3) << std::setfill('0') << index;
  return output.str();
}

void append_u32(canonical::Bytes& output, std::size_t value) {
  test::expect(value <= UINT32_MAX, "native exit transcript item is too large");
  const auto bounded = static_cast<std::uint32_t>(value);
  output.push_back(static_cast<std::byte>((bounded >> 24U) & 0xffU));
  output.push_back(static_cast<std::byte>((bounded >> 16U) & 0xffU));
  output.push_back(static_cast<std::byte>((bounded >> 8U) & 0xffU));
  output.push_back(static_cast<std::byte>(bounded & 0xffU));
}

void append_framed(canonical::Bytes& output, std::span<const std::byte> value) {
  append_u32(output, value.size());
  output.insert(output.end(), value.begin(), value.end());
}

[[nodiscard]] canonical::Bytes file_bytes(const std::filesystem::path& path) {
  std::ifstream input(path, std::ios::binary);
  test::expect(input.good(), "cannot open exact native WAL");
  const std::vector<char> chars{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  canonical::Bytes output;
  output.reserve(chars.size());
  for (const char value : chars) {
    output.push_back(static_cast<std::byte>(static_cast<unsigned char>(value)));
  }
  return output;
}

[[nodiscard]] protocol::PreparedIntegerShard prepared_shard(
    std::uint32_t index,
    const std::string& fixture) {
  const auto id = ticket_id(index);
  const auto signed_index = static_cast<std::int64_t>(index);
  return protocol::PreparedIntegerShard{
      static_cast<std::int64_t>(index % 5U) - 2,
      test::derived_id("leaf:", id),
      {128U, "BIG_ENDIAN", test::field(fixture, "integer_profile_id"), 64U},
      test::field(fixture, "parameter_id"),
      test::field(fixture, "round_id"),
      test::field(fixture, "shard_id"),
      id,
      {
          signed_index - 50,
          (2 * signed_index) - 99,
          (index % 2U) == 0U ? signed_index + 1 : -(signed_index + 1),
          1,
      },
  };
}

[[nodiscard]] std::vector<Ticket> tickets(const std::string& fixture) {
  test::expect(test::unsigned_field(fixture, "ticket_count") == 100U, "exit ticket count changed");
  std::vector<Ticket> output;
  output.reserve(100U);
  for (std::uint32_t index = 0U; index < 100U; ++index) {
    const auto shard = prepared_shard(index, fixture);
    const auto bytes = protocol::encode(shard);
    test::expect(
        protocol::parse_prepared_integer_shard(bytes) == shard,
        "native exit prepared ticket is not canonical");
    output.push_back(Ticket{
        shard.ticket_id,
        canonical::content_id(canonical::Type::prepared_integer_shard, bytes),
        test::derived_id("availability:", shard.ticket_id),
    });
  }
  return output;
}

[[nodiscard]] std::vector<canonical::Bytes> commands(
    const protocol::RoundState& initial,
    const std::vector<Ticket>& prepared) {
  std::vector<canonical::Bytes> output;
  output.reserve(201U);
  canonical::Bytes frozen_transcript;
  for (const auto& ticket : prepared) {
    output.push_back(protocol::encode(test::command_for(
        initial,
        "ACCEPT_COMMITMENT",
        "native-exit-commit-" + ticket.id,
        ticket.commitment_id)));
    append_framed(frozen_transcript, test::ascii_bytes(ticket.id));
    append_framed(frozen_transcript, test::ascii_bytes(ticket.commitment_id));
    append_framed(frozen_transcript, test::ascii_bytes(ticket.availability_id));
  }
  for (const auto& ticket : prepared) {
    output.push_back(protocol::encode(test::command_for(
        initial,
        "ACCEPT_AVAILABILITY",
        "native-exit-availability-" + ticket.id,
        ticket.availability_id)));
  }
  output.push_back(protocol::encode(test::command_for(
      initial,
      "FINALIZE_INPUT_FREEZE",
      "native-exit-freeze-100",
      "sha256:" + canonical::sha256_hex(frozen_transcript))));
  return output;
}

[[nodiscard]] std::pair<std::string, std::string> transcript_hashes(
    const std::vector<runtime::SubmitReceipt>& receipts) {
  canonical::Bytes effects;
  canonical::Bytes wal_records;
  for (const auto& receipt : receipts) {
    append_framed(effects, receipt.effect_batch_bytes);
    append_framed(wal_records, receipt.wal_record_bytes);
  }
  return {canonical::sha256_hex(effects), canonical::sha256_hex(wal_records)};
}

[[nodiscard]] runtime::Config config(
    const std::filesystem::path& directory,
    const canonical::Bytes& initial) {
  return runtime::Config{directory, initial, 512U};
}

[[nodiscard]] RunResult run_validator(
    std::uint32_t validator,
    const canonical::Bytes& initial,
    const std::vector<canonical::Bytes>& command_set) {
  const auto directory = test::fresh_directory("native-exit-validator-" + std::to_string(validator));
  std::vector<runtime::SubmitReceipt> receipts;
  receipts.reserve(command_set.size());
  canonical::Bytes final_state;
  {
    runtime::Runtime instance(config(directory, initial));
    for (const auto& command : command_set) {
      receipts.push_back(instance.submit(command));
    }
    instance.snapshot();
    final_state = instance.state_bytes();
    test::expect(
        instance.journal_sequence() == command_set.size(),
        "native exit journal count is not exact");
  }
  {
    runtime::Runtime recovered(config(directory, initial));
    test::expect(recovered.state_bytes() == final_state, "restart changed native exit state bytes");
    for (std::size_t index = 0; index < command_set.size(); ++index) {
      auto replay = recovered.submit(command_set[index]);
      auto expected = receipts[index];
      expected.replay = true;
      test::expect(replay == expected, "restart changed exact native receipt bytes");
    }
    test::expect(recovered.state_bytes() == final_state, "replay advanced native state twice");
  }
  const auto [effect_hash, wal_hash] = transcript_hashes(receipts);
  return RunResult{
      final_state,
      canonical::content_id(canonical::Type::round_state, final_state),
      effect_hash,
      wal_hash,
      canonical::sha256_hex(file_bytes(directory / "runtime.wal")),
      command_set,
      receipts,
  };
}

void verify_crash_equivalence(
    const RunResult& uninterrupted,
    const canonical::Bytes& initial,
    const std::vector<canonical::Bytes>& command_set) {
  const auto directory = test::fresh_directory("native-exit-crash-restart");
  {
    runtime::Runtime instance(config(directory, initial));
    for (std::size_t index = 0; index + 1U < command_set.size(); ++index) {
      static_cast<void>(instance.submit(command_set[index]));
    }
    try {
      static_cast<void>(instance.submit(
          command_set.back(), runtime::CrashPoint::after_durability_before_commit));
      test::fail("native exit crash injection unexpectedly returned an effect");
    } catch (const runtime::RuntimeError& error) {
      test::expect(error.code() == runtime::ErrorCode::simulated_crash, "wrong crash error code");
    }
  }
  std::vector<runtime::SubmitReceipt> replayed;
  replayed.reserve(command_set.size());
  {
    runtime::Runtime recovered(config(directory, initial));
    test::expect(
        recovered.state_bytes() == uninterrupted.final_state,
        "durable crash recovery differs from uninterrupted state");
    for (std::size_t index = 0; index < command_set.size(); ++index) {
      auto receipt = recovered.submit(command_set[index]);
      test::expect(receipt.replay, "durable crash replay appended a duplicate command");
      auto expected = uninterrupted.receipts[index];
      expected.replay = true;
      test::expect(receipt == expected, "crash replay receipt differs byte-for-byte");
      receipt.replay = false;
      replayed.push_back(std::move(receipt));
    }
  }
  const auto [effect_hash, wal_hash] = transcript_hashes(replayed);
  test::expect(
      effect_hash == uninterrupted.effect_transcript_sha256 &&
          wal_hash == uninterrupted.wal_transcript_sha256,
      "crash/restart transcript hashes differ from uninterrupted execution");
  test::expect(
      canonical::sha256_hex(file_bytes(directory / "runtime.wal")) ==
          uninterrupted.wal_file_sha256,
      "crash/restart physical WAL hash differs from uninterrupted execution");
}

}  // namespace

int main() {
  try {
    const auto fixture = test::load(DELTA_PREPARED_100_FIXTURE_PATH);
    const auto initial = test::golden(DELTA_GOLDEN_FIXTURE_PATH, 5U);
    const auto prepared = tickets(fixture);
    const auto command_set = commands(protocol::parse_round_state(initial), prepared);
    test::expect(command_set.size() == 201U, "native exit command count changed");

    std::vector<std::future<RunResult>> validators;
    for (std::uint32_t validator = 1U; validator <= 4U; ++validator) {
      validators.push_back(std::async(
          std::launch::async,
          [validator, &initial, &command_set] {
            return run_validator(validator, initial, command_set);
          }));
    }
    std::vector<RunResult> results;
    for (auto& validator : validators) {
      results.push_back(validator.get());
    }
    test::expect(
        std::all_of(results.begin() + 1, results.end(), [&results](const RunResult& value) {
          return value == results.front();
        }),
        "four independent native validators diverged");
    test::expect(
        results.front().final_state_id == test::field(fixture, "expected_eligible_state_id"),
        "native exit final state differs from prepared-100 contract");
    verify_crash_equivalence(results.front(), initial, command_set);
    std::cout << "{\"effect_transcript_sha256\":\""
              << results.front().effect_transcript_sha256 << "\",\"final_state_id\":\""
              << results.front().final_state_id << "\",\"runtime_count\":4,\"status\":\"PASS\""
              << ",\"ticket_count\":100,\"wal_file_sha256\":\""
              << results.front().wal_file_sha256 << "\",\"wal_transcript_sha256\":\""
              << results.front().wal_transcript_sha256 << "\"}\n";
  } catch (const std::exception& error) {
    std::cerr << "native four-runtime exit failed: " << error.what() << '\n';
    return 1;
  }
  return 0;
}
