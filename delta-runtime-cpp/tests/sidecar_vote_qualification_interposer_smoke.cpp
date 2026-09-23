#include "sidecar_qualification_probe.h"

#include <delta/core/canonical.hpp>
#include <delta/core/consensus.hpp>
#include <delta/core/protocol.hpp>
#include <delta/runtime/runtime.hpp>
#include <delta/runtime/vote_codec.hpp>

#include "../../delta-core-cpp/tests/vote_fixture.hpp"

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <iostream>
#include <span>
#include <stdexcept>
#include <string_view>
#include <utility>

namespace {

namespace canonical = delta::core::canonical;
namespace consensus = delta::core::consensus;
namespace protocol = delta::core::protocol;
namespace runtime = delta::runtime;
namespace vote_fixture = delta::test::vote_fixture;

[[nodiscard]] std::span<const std::uint8_t> unsigned_bytes(
    const canonical::Bytes& bytes) noexcept {
  return {reinterpret_cast<const std::uint8_t*>(bytes.data()), bytes.size()};
}

[[noreturn]] void fail(const char* message) { throw std::runtime_error(message); }

void require(bool condition, const char* message) {
  if (!condition) {
    fail(message);
  }
}

[[nodiscard]] runtime::Config config(
    const std::filesystem::path& directory,
    const vote_fixture::Fixture& fixture) {
  return runtime::Config{
      .directory = directory,
      .initial_state_bytes = protocol::encode(fixture.state),
      .submission_capacity = 64U,
      .durable_binding_guard = {},
      .vote_policy = fixture.policy,
      .expected_wal_identity = {},
  };
}

[[noreturn]] void crash_at_real_vote_pre_durability_cut(
    const std::filesystem::path& directory,
    const vote_fixture::Fixture& fixture) {
  std::filesystem::create_directories(directory);
  const auto initial = protocol::encode(fixture.state);
  const auto policy = runtime::encode_vote_policy_v1(fixture.policy);
  const auto vote = protocol::encode(fixture.vote);
  const auto directory_utf8 = directory.u8string();
  delta_sidecar_qualification_vote_pre_durability_crash_v1(
      reinterpret_cast<const std::uint8_t*>(directory_utf8.data()),
      directory_utf8.size(),
      unsigned_bytes(initial).data(),
      initial.size(),
      unsigned_bytes(policy).data(),
      policy.size(),
      unsigned_bytes(vote).data(),
      vote.size());
  fail("vote qualification crash hook unexpectedly returned");
}

void inspect_recovered_vote(
    const std::filesystem::path& directory,
    const vote_fixture::Fixture& fixture) {
  const auto vote = protocol::encode(fixture.vote);
  runtime::Runtime recovered(config(directory, fixture));
  require(recovered.journal_sequence() == 1U, "real-cut vote sequence was not recovered");
  require(recovered.recovered_vote_count() == 1U, "real-cut vote was lost or duplicated");
  const auto replay = recovered.record_vote(vote);
  require(replay.replay, "real-cut vote retry was not a native replay");
  require(replay.journal_sequence == 1U, "real-cut vote replay sequence changed");
  require(replay.frame == vote, "real-cut vote replay frame changed");
  require(
      replay.action == consensus::VoteAction::round_config,
      "real-cut vote replay action changed");
  const auto receipt = runtime::encode_vote_receipt_v1(replay);
  require(
      runtime::parse_vote_receipt_v1(receipt).frame == vote,
      "real-cut vote canonical receipt did not round-trip");
  const auto wal_size = std::filesystem::file_size(directory / "runtime.wal");
  require(wal_size > 0U, "real-cut vote WAL is empty");
  std::cout << "{\"canonical_receipt_sha256\":\"sha256:"
            << canonical::sha256_hex(receipt)
            << "\",\"native_replay\":true,\"recovered_durable_sequence\":1"
               ",\"recovered_vote_count\":1,\"type_name\":"
               "\"DELTA_VOTE_PRE_DURABILITY_INSPECTION\",\"wal_size_bytes\":"
            << wal_size << "}\n";
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 3) {
      fail("usage: sidecar_vote_qualification_interposer_smoke crash|inspect DIRECTORY");
    }
    const auto mode = std::string_view(argv[1]);
    const auto directory = std::filesystem::absolute(argv[2]).lexically_normal();
    const auto fixture = vote_fixture::full(consensus::VoteAction::round_config);
    if (mode == "crash") {
      crash_at_real_vote_pre_durability_cut(directory, fixture);
    }
    if (mode == "inspect") {
      inspect_recovered_vote(directory, fixture);
      return 0;
    }
    fail("unknown vote qualification smoke mode");
  } catch (const std::exception& error) {
    std::cerr << "sidecar_vote_qualification_interposer_smoke: " << error.what() << '\n';
    return 2;
  }
}
