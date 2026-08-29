#include <delta/apply/engine.hpp>
#include <delta/certificates/contracts.hpp>

#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

[[nodiscard]] std::string id(char digit) {
  return "sha256:" + std::string(64U, digit);
}

[[nodiscard]] delta::certificates::InputSetCertificate valid() {
  return {
      {id('d'), 8U, id('c'), id('a'), "round-008", id('e'), 0U},
      id('1'),
      3U,
      {"validator-0", "validator-1", "validator-2"},
      {{id('2'), id('3'), "code", "ticket-000"}},
  };
}

void fuzz_smoke() {
  for (std::uint32_t iteration = 0U; iteration < 2'000U; ++iteration) {
    auto candidate = valid();
    switch (iteration % 5U) {
      case 0U:
        candidate.input_root = "sha256:INVALID";
        break;
      case 1U:
        candidate.signer_ids = {"validator-1", "validator-0", "validator-2"};
        break;
      case 2U:
        candidate.quorum_threshold = 4U;
        break;
      case 3U:
        candidate.tuples.push_back(candidate.tuples.front());
        break;
      default:
        candidate.context.round_id.clear();
        break;
    }
    bool rejected = false;
    try {
      (void)delta::certificates::content_id(candidate);
    } catch (const delta::certificates::CertificateError&) {
      rejected = true;
    }
    if (!rejected) {
      throw std::runtime_error("mutated certificate escaped bounded canonical validation");
    }
    const auto numerator = static_cast<std::int64_t>(iteration) - 1'000;
    const auto first = delta::apply::round_half_toward_positive(numerator, 7U);
    const auto second = delta::apply::round_half_toward_positive(numerator, 7U);
    if (first != second) {
      throw std::runtime_error("canonical apply rounding is nondeterministic");
    }
  }
}

}  // namespace

int main() {
  try {
    fuzz_smoke();
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
  return 0;
}
