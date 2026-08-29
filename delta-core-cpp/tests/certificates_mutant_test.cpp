#include <delta/certificates/verifier.hpp>
#include <delta/robust/plan.hpp>
#include <delta/runtime/certificate_runtime.hpp>

#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

[[nodiscard]] std::string id(char digit) {
  return "sha256:" + std::string(64U, digit);
}

[[nodiscard]] delta::certificates::Context context() {
  return {id('d'), 8U, id('c'), id('a'), "round-008", id('e'), 0U};
}

[[nodiscard]] delta::certificates::ChainVerifier verifier() {
  return delta::certificates::ChainVerifier(
      context(), {id('e'), {"validator-0", "validator-1", "validator-2", "validator-3"}, 3U});
}

template <typename Function>
void must_reject(Function function, const char* message) {
  try {
    function();
  } catch (const std::exception&) {
    return;
  }
  throw std::runtime_error(message);
}

[[maybe_unused]] void seed_parent() {
  const delta::certificates::SeedTranscript seed{
      context(), id('1'), id('2'), id('3'), {id('4'), id('5'), id('6')}};
  auto check = verifier();
  must_reject([&] { (void)check.verify_seed(seed, id('f')); }, "wrong seed parent accepted");
}

[[maybe_unused]] void observed_coverage() {
  auto check = verifier();
  const auto signers = std::vector<std::string>{"validator-0", "validator-1", "validator-2"};
  const delta::certificates::ParameterShardQc shard{
      context(), id('3'), 1U, "code", id('2'), {id('4')}, id('1'), 3U, {"1"},
      "shard-000", signers};
  delta::certificates::AggregateRootQc root{
      context(),
      id('3'),
      id('2'),
      id('1'),
      {{"code", delta::certificates::content_id(shard), "shard-000"}},
      {},
      3U,
      {{"code", "shard-000"}},
      signers};
  root.merkle_root = delta::certificates::aggregate_merkle_root(root.leaves);
  const std::vector<delta::certificates::ShardKey> required{
      {"code", "shard-000"}, {"text", "shard-000"}};
  must_reject(
      [&] { (void)check.verify_root(root, id('1'), id('2'), id('3'), required, {shard}); },
      "observed-only aggregate coverage accepted");
}

[[maybe_unused]] void unsafe_coefficient() {
  const std::vector<delta::robust::Contribution> values{{"code", {11}, "ticket-000"}};
  must_reject(
      [&] {
        (void)delta::robust::build_plan(
            context(),
            id('1'),
            id('2'),
            id('3'),
            id('4'),
            values,
            {id('5'), 1U, 1U, 0U, 1U, 10, 1U},
            {"validator-0", "validator-1", "validator-2"},
            3U);
      },
      "out-of-proof q coefficient accepted");
}

[[maybe_unused]] void uncertified_current() {
  const auto signers = std::vector<std::string>{"validator-0", "validator-1", "validator-2"};
  const delta::certificates::ApplyQc qc{
      context(), id('1'), id('2'), id('3'), id('4'), id('5'), id('b'), 3U, signers};
  const delta::certificates::CurrentPointerCommand command{
      context(), id('f'), id('b'), id('4'), id('5')};
  const auto directory = std::filesystem::temp_directory_path() / "delta-008-current-mutant";
  std::filesystem::remove_all(directory);
  delta::runtime::CurrentPointerStore store(directory, {id('b'), id('7'), {}, 7U});
  must_reject([&] { (void)store.advance(command, qc); }, "uncertified current accepted");
  std::filesystem::remove_all(directory);
}

}  // namespace

int main() {
  try {
#if defined(DELTA_EXPECT_SEED_PARENT_MUTANT)
    seed_parent();
#elif defined(DELTA_EXPECT_OBSERVED_COVERAGE_MUTANT)
    observed_coverage();
#elif defined(DELTA_EXPECT_COEFFICIENT_MUTANT)
    unsafe_coefficient();
#elif defined(DELTA_EXPECT_CURRENT_MUTANT)
    uncertified_current();
#else
#error A mutant expectation must be selected
#endif
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
  return 0;
}
