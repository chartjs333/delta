#include <delta/fixedpoint/profile.hpp>
#include <delta/shards/reader.hpp>

#include <cstddef>
#include <cstdint>
#include <iostream>
#include <span>
#include <string>
#include <vector>

namespace {

[[nodiscard]] delta::shards::ShardHeader expected_header() {
  return delta::shards::ShardHeader{
      0U,
      "decoder.bias",
      0U,
      0U,
      4U,
      std::string(delta::fixedpoint::formal_semantics_id()),
      "sha256:f43c0259749b15ae0d0154a6e9094774c7ea65e55adefbaea400a6201acb6239",
      std::string(delta::fixedpoint::fixed_profile_id()),
      "sha256:993b4d5104810dd26a3159b60cf8fe9afe6154cdcca90d22b577ae1b6d1ac076",
      "sha256:34bc08c316dfe22efe155ed11b866bcc0daf7ef8c3c7389c56b2f2c707443629",
      "sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205",
      "sha256:4c644a3254edb3d7bff009bbe91ee99df6051516362fa1a1eac6f0a803a9c7a1",
      "ticket-002-fixture",
      "",
  };
}

void exercise(std::span<const std::byte> bytes) noexcept {
  try {
    static_cast<void>(delta::shards::read_shard(bytes, expected_header()));
  } catch (const delta::shards::ShardError&) {
  }
}

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t* data, std::size_t size) {
  exercise(std::as_bytes(std::span(data, size)));
  return 0;
}

#ifdef DELTA_FIXEDPOINT_FUZZ_SMOKE_MAIN
int main() {
  const std::vector<std::vector<std::uint8_t>> corpus = {
      {},
      {'D', 'R', 'Q', '1'},
      {'D', 'R', 'Q', '1', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
      {'D', 'R', 'Q', '1', 1, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 0},
      {'D', 'R', 'Q', '1', 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 16, 0},
      {'D', 'R', 'Q', '2', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},
  };
  for (const auto& seed : corpus) {
    LLVMFuzzerTestOneInput(seed.data(), seed.size());
  }
  std::cout << "fixed-point parser fuzz smoke passed\n";
  return 0;
}
#endif
