#include <delta/reduce/topology.hpp>

#include <cstddef>
#include <cstdint>
#include <fstream>
#include <iterator>
#include <regex>
#include <span>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {

[[nodiscard]] delta::reduce::Context expected_context() {
  return {
      "sha256:993b4d5104810dd26a3159b60cf8fe9afe6154cdcca90d22b577ae1b6d1ac076",
      "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "sha256:34bc08c316dfe22efe155ed11b866bcc0daf7ef8c3c7389c56b2f2c707443629",
      "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6",
      "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61",
      "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
      "sha256:434092f82188337d0a273cd13c93e06dec55ae842df0498e4d52caa1d1844205",
      "sha256:4c644a3254edb3d7bff009bbe91ee99df6051516362fa1a1eac6f0a803a9c7a1",
  };
}

[[nodiscard]] std::vector<std::uint8_t> unhex(std::string_view value) {
  const auto nibble = [](char character) -> unsigned {
    return character <= '9' ? static_cast<unsigned>(character - '0')
                            : static_cast<unsigned>(character - 'a') + 10U;
  };
  std::vector<std::uint8_t> result;
  result.reserve(value.size() / 2U);
  for (std::size_t index = 0U; index + 1U < value.size(); index += 2U) {
    result.push_back(static_cast<std::uint8_t>(
        (nibble(value[index]) << 4U) | nibble(value[index + 1U])));
  }
  return result;
}

[[nodiscard]] std::vector<std::uint8_t> golden_topology() {
  std::ifstream input(DELTA_HIERARCHY_GOLDEN_PATH, std::ios::binary);
  const std::string document{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  const std::regex pattern(R"REGEX("topology":\{"bytes_hex":"([0-9a-f]+)")REGEX");
  std::smatch match;
  return std::regex_search(document, match, pattern) ? unhex(match[1].str())
                                                      : std::vector<std::uint8_t>{};
}

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t* data, std::size_t size) {
  if (size > 1U * 1024U * 1024U) {
    return 0;
  }
  const auto bytes = std::span(
      reinterpret_cast<const std::byte*>(data), size);
  try {
    static_cast<void>(delta::reduce::parse_topology(bytes, expected_context()));
  } catch (const delta::reduce::ReduceError&) {
  }
  return 0;
}

#if defined(DELTA_HIERARCHY_FUZZ_SMOKE_MAIN)
int main() {
  auto seed = golden_topology();
  if (seed.empty()) {
    return 1;
  }
  std::vector<std::vector<std::uint8_t>> corpus{
      {},
      {'{'},
      {'{', '}'},
      {'[', ']'},
      {'{', '"', 'x', '"', ':', '0', '}'},
      std::vector<std::uint8_t>(1'048'577U, static_cast<std::uint8_t>('x')),
      seed,
  };
  for (std::size_t index = 0U; index < seed.size(); index += 17U) {
    auto mutation = seed;
    mutation[index] ^= 0x5aU;
    corpus.push_back(std::move(mutation));
    corpus.emplace_back(seed.begin(), seed.begin() + static_cast<std::ptrdiff_t>(index));
  }
  for (const auto& input : corpus) {
    static_cast<void>(LLVMFuzzerTestOneInput(input.data(), input.size()));
  }
  return 0;
}
#endif
