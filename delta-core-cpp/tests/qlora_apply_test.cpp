#include <delta/certificates/verifier.hpp>
#include <delta/qlora/adapter_apply.hpp>
#include <delta/runtime/certificate_runtime.hpp>

#include <array>
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

[[noreturn]] void fail(const char* message) { throw std::runtime_error(message); }

void expect(bool condition, const char* message) {
  if (!condition) {
    fail(message);
  }
}

template <typename Function>
void expect_certificate_error(Function function, const char* message) {
  try {
    function();
  } catch (const delta::certificates::CertificateError&) {
    return;
  }
  fail(message);
}

[[nodiscard]] std::string id(char digit) {
  return "sha256:" + std::string(64U, digit);
}

[[nodiscard]] delta::qlora::Context qlora_context() {
  return {id('1'), id('2'), id('3'), id('4'), id('5'), id('6')};
}

[[nodiscard]] delta::certificates::Context context() {
  const auto binding = qlora_context();
  return {
      .arithmetic_profile_id = id('7'),
      .height = 9U,
      .parameter_schema_id = binding.adapter_parameter_schema_id,
      .round_config_id = delta::qlora::content_id(binding),
      .round_id = "round-009",
      .validator_epoch_id = id('8'),
      .view = 0U,
  };
}

[[nodiscard]] delta::certificates::ApplyArithmeticProfile profile() {
  return {
      .accumulator_proof_id = id('9'),
      .domain_weights = {{"text", {1, 1U}}},
      .learning_rate = {1, 10U},
      .momentum = {0, 1U},
      .nesterov = true,
      .rounding = "HALF_TOWARD_POSITIVE",
      .weight_decay = {0, 1U},
  };
}

struct AppliedChain {
  delta::certificates::ApplyCandidate candidate;
  delta::certificates::ApplyQc apply_qc;
  delta::certificates::CurrentPointerCommand command;
};

[[nodiscard]] AppliedChain chain() {
  const auto candidate = delta::qlora::compute_adapter_candidate(
      qlora_context(),
      context(),
      id('a'),
      profile(),
      delta::qlora::AdapterState{{100, -50}, {0, 0}, id('3'), id('b')},
      std::vector<delta::apply::DomainAggregate>{{"text", {10, -20}}});
  const auto candidate_id = delta::certificates::content_id(candidate);
  const auto apply_qc = delta::certificates::ApplyQc{
      .context = context(),
      .aggregate_root_qc_id = candidate.aggregate_root_qc_id,
      .apply_arithmetic_profile_id = candidate.apply_arithmetic_profile_id,
      .apply_candidate_id = candidate_id,
      .next_model_hash = candidate.next_model_hash,
      .next_optimizer_hash = candidate.next_optimizer_hash,
      .parent_checkpoint_id = candidate.parent_checkpoint_id,
      .quorum_threshold = 3U,
      .signer_ids = {"validator-0", "validator-1", "validator-2"},
  };
  const auto apply_qc_id = delta::certificates::content_id(apply_qc);
  return {
      candidate,
      apply_qc,
      delta::qlora::make_adapter_pointer_command(
          qlora_context(), apply_qc, apply_qc_id, candidate.next_model_hash),
  };
}

void test_four_validator_apply_and_wal_equality() {
  const auto value = chain();
  delta::certificates::ChainVerifier verifier(
      context(),
      {id('8'), {"validator-0", "validator-1", "validator-2", "validator-3"}, 3U});
  expect(
      verifier.verify_apply(
          value.apply_qc,
          value.candidate,
          value.candidate.aggregate_root_qc_id,
          value.candidate.apply_arithmetic_profile_id) ==
          delta::certificates::content_id(value.apply_qc),
      "QLoRA ApplyQC did not pass the existing verifier");

  const auto bytes = delta::certificates::canonical_json(value.candidate);
  for (int validator = 0; validator < 4; ++validator) {
    const auto repeated = chain();
    expect(
        repeated.candidate == value.candidate &&
            delta::certificates::canonical_json(repeated.candidate) == bytes &&
            repeated.command == value.command,
        "validators produced different adapter Apply bytes/hash/effect");
  }

  const auto root = std::filesystem::temp_directory_path() / "delta-009-qlora-apply";
  std::filesystem::remove_all(root);
  const delta::runtime::PointerState initial{id('3'), id('b'), {}, 8U};
  for (int validator = 0; validator < 4; ++validator) {
    delta::runtime::CurrentPointerStore store(
        root / ("validator-" + std::to_string(validator)), initial);
    expect(
        store.advance(value.command, value.apply_qc) ==
            delta::runtime::PointerDisposition::advanced,
        "validator did not atomically advance its adapter pointer");
    expect(
        store.state().checkpoint_id == value.candidate.next_model_hash &&
            store.state().optimizer_id == value.candidate.next_optimizer_hash,
        "adapter ApplyQC advanced different native state");
    expect(
        store.advance(value.command, value.apply_qc) ==
            delta::runtime::PointerDisposition::replay,
        "adapter ApplyQC replay was not idempotent");
  }

  const auto crash_path = root / "crash-replay";
  try {
    delta::runtime::CurrentPointerStore store(crash_path, initial);
    (void)store.advance(
        value.command,
        value.apply_qc,
        delta::runtime::CrashPoint::after_durability_before_commit);
    fail("durable adapter-pointer crash was not injected");
  } catch (const delta::runtime::RuntimeError&) {
  }
  delta::runtime::CurrentPointerStore recovered(crash_path, initial);
  expect(
      recovered.state().checkpoint_id == value.candidate.next_model_hash &&
          recovered.advance(value.command, value.apply_qc) ==
              delta::runtime::PointerDisposition::replay,
      "durable adapter pointer did not recover idempotently");
  std::filesystem::remove_all(root);
}

void test_wrong_parent_profile_and_base_mutation_are_rejected() {
  auto wrong_parent = qlora_context();
  wrong_parent.parent_adapter_id = id('f');
  expect_certificate_error(
      [&] {
        (void)delta::qlora::compute_adapter_candidate(
            wrong_parent,
            context(),
            id('a'),
            profile(),
            delta::qlora::AdapterState{{100}, {0}, id('3'), id('b')},
            std::vector<delta::apply::DomainAggregate>{{"text", {1}}});
      },
      "wrong adapter parent was accepted");

  auto wrong_profile = qlora_context();
  wrong_profile.quantized_base_profile_id = id('f');
  expect_certificate_error(
      [&] { delta::qlora::validate_binding(wrong_profile, context()); },
      "quantized-base profile mutation was accepted");

  const auto value = chain();
  auto conflicting = value.apply_qc;
  conflicting.next_model_hash = id('f');
  delta::certificates::ChainVerifier verifier(
      context(),
      {id('8'), {"validator-0", "validator-1", "validator-2", "validator-3"}, 3U});
  expect_certificate_error(
      [&] {
        (void)verifier.verify_apply(
            conflicting,
            value.candidate,
            value.candidate.aggregate_root_qc_id,
            value.candidate.apply_arithmetic_profile_id);
      },
      "conflicting adapter ApplyQC was accepted");
}

}  // namespace

int main() {
  try {
    test_four_validator_apply_and_wal_equality();
    test_wrong_parent_profile_and_base_mutation_are_rejected();
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
  return 0;
}
