#include <delta/scheduling/contracts.hpp>

#include <cstddef>
#include <cstdint>
#include <span>

namespace {

[[nodiscard]] delta::scheduling::Context context() {
  return {
      "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
      "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
      "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
      "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  };
}

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t* data, std::size_t size) {
  try {
    const auto input = std::as_bytes(std::span(data, size));
    static_cast<void>(delta::scheduling::parse_domain_ticket_policy(input, context()));
  } catch (const delta::scheduling::SchedulingError&) {
  }
  return 0;
}

#if defined(DELTA_SCHEDULING_FUZZ_SMOKE_MAIN)
int main() {
  const std::uint8_t input[] = {'{', '}'};
  return LLVMFuzzerTestOneInput(input, sizeof(input));
}
#endif
