#include <delta/distribution/certification_policy.hpp>

#include <cstddef>
#include <cstdint>
#include <iostream>
#include <span>
#include <vector>

namespace {

void exercise(std::span<const std::byte> bytes) noexcept {
  try {
    static_cast<void>(delta::distribution::evaluate_certified_manifest(bytes, bytes));
  } catch (...) {
  }
}

}  // namespace

extern "C" int LLVMFuzzerTestOneInput(const std::uint8_t* data, std::size_t size) {
  exercise(std::as_bytes(std::span(data, size)));
  return 0;
}

#ifdef DELTA_DISTRIBUTION_FUZZ_SMOKE_MAIN
int main() {
  const std::vector<std::vector<std::uint8_t>> corpus = {
      {},
      {'{', '}'},
      {'{', '"', 'a', '"', ':', '0', '}'},
      {'{', '"', 'b', '"', ':', '0', ',', '"', 'a', '"', ':', '0', '}'},
      {'[', '[', '[', '[', '[', '[', '[', '[', '[', '[', '[', '[', '[', '[', '[', '['},
      {'{', '"', 'a', '"', ':', '1', '8', '4', '4', '6', '7', '4', '4', '0', '7', '3', '7',
       '0', '9', '5', '5', '1', '6', '1', '6', '}'},
  };
  for (const auto& seed : corpus) {
    LLVMFuzzerTestOneInput(seed.data(), seed.size());
  }
  std::cout << "distribution parser fuzz smoke passed\n";
  return 0;
}
#endif
