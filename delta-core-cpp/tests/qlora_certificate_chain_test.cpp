#include <delta/certificates/contracts.hpp>
#include <delta/qlora/context.hpp>
#include <delta/robust/plan.hpp>

#include <cstdint>
#include <iostream>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {

[[noreturn]] void fail(const char* message) { throw std::runtime_error(message); }

void expect(bool condition, const char* message) {
  if (!condition) {
    fail(message);
  }
}

template <typename Function>
void expect_error(
    Function function,
    delta::certificates::ErrorCode expected,
    const char* message) {
  try {
    function();
  } catch (const delta::certificates::CertificateError& error) {
    expect(error.code() == expected, message);
    return;
  }
  fail(message);
}

[[nodiscard]] std::string id(char digit) {
  return "sha256:" + std::string(64U, digit);
}

[[nodiscard]] delta::qlora::Context qlora_context() {
  return {
      id('1'),
      id('2'),
      id('3'),
      id('4'),
      id('5'),
      id('6'),
  };
}

[[nodiscard]] delta::certificates::Context certificate_context() {
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

[[nodiscard]] std::vector<std::string> signers() {
  return {"validator-0", "validator-1", "validator-2"};
}

void test_existing_certificate_graph_is_context_bound() {
  using namespace delta::certificates;
  auto verifier = delta::qlora::make_chain_verifier(
      qlora_context(),
      certificate_context(),
      ValidatorPolicy{
          id('8'), {"validator-0", "validator-1", "validator-2", "validator-3"}, 3U});
  const auto isc = InputSetCertificate{
      .context = certificate_context(),
      .input_root = id('9'),
      .quorum_threshold = 3U,
      .signer_ids = signers(),
      .tuples = {{id('a'), id('b'), "text", "ticket-000"}},
  };
  const auto isc_id = verifier.verify_input_set(isc);
  const auto seed = SeedTranscript{
      .context = certificate_context(),
      .input_set_certificate_id = isc_id,
      .seed_id = id('c'),
      .seed_profile_id = id('d'),
      .share_ids = {id('e')},
  };
  const auto seed_id = verifier.verify_seed(seed, isc_id);
  const auto norms = NormEvidence{
      .context = certificate_context(),
      .entries = {{1U, "4", "ticket-000"}},
      .input_set_certificate_id = isc_id,
      .norm_root = id('f'),
  };
  const auto norm_id = verifier.verify_norms(norms, isc_id);
  const auto eligibility = EligibilityCertificate{
      .context = certificate_context(),
      .entries = {{true, "text", {1, 1U}, "ACCEPT", "ticket-000"}},
      .input_set_certificate_id = isc_id,
      .norm_evidence_id = norm_id,
      .quorum_threshold = 3U,
      .robust_profile_id = id('0'),
      .signer_ids = signers(),
  };
  const auto eligibility_id = verifier.verify_eligibility(eligibility, isc, norm_id);
  const auto plan = AggregationPlanCertificate{
      .context = certificate_context(),
      .accumulator_proof_id = id('a'),
      .bucket_assignments = {{"bucket-0", "ticket-000"}},
      .eligibility_certificate_id = eligibility_id,
      .input_set_certificate_id = isc_id,
      .iteration_count = 1U,
      .quorum_threshold = 3U,
      .seed_transcript_id = seed_id,
      .signer_ids = signers(),
      .transcript_root = id('b'),
      .weights = {{{1, 1U}, "ticket-000"}},
  };
  const auto plan_id = verifier.verify_plan(plan, isc, eligibility, seed_id, id('a'));
  const auto shard = ParameterShardQc{
      .context = certificate_context(),
      .aggregation_plan_certificate_id = plan_id,
      .denominator = 1U,
      .domain_id = "text",
      .eligibility_certificate_id = eligibility_id,
      .input_leaf_ids = {id('c')},
      .input_set_certificate_id = isc_id,
      .quorum_threshold = 3U,
      .result_numerators = {"12", "-3"},
      .shard_id = "model.layer0.lora_A",
      .signer_ids = signers(),
  };
  expect(
      verifier.verify_shard(shard, isc_id, eligibility_id, plan_id) == content_id(shard),
      "bound ParameterShardQC was not accepted");

  auto wrong = qlora_context();
  wrong.base_model_manifest_id = id('f');
  expect_error(
      [&] {
        (void)delta::qlora::make_chain_verifier(
            wrong,
            certificate_context(),
            ValidatorPolicy{
                id('8'), {"validator-0", "validator-1", "validator-2", "validator-3"}, 3U});
      },
      ErrorCode::context_mismatch,
      "base-model mismatch was accepted by the existing certificate graph");
}

void test_exact_adapter_matrix_and_integer_reduce() {
  const auto required = delta::qlora::required_adapter_keys(
      {"code", "text"},
      {"model.layer0.lora_A", "model.layer0.lora_B"});
  const std::vector<delta::qlora::AdapterVector> contributions{
      {{"code", "model.layer0.lora_A"}, 2, {1, -2}, "ticket-0"},
      {{"code", "model.layer0.lora_A"}, 3, {4, 1}, "ticket-1"},
      {{"code", "model.layer0.lora_B"}, 1, {5, 6}, "ticket-0"},
      {{"text", "model.layer0.lora_A"}, -1, {2, 3}, "ticket-2"},
      {{"text", "model.layer0.lora_B"}, 4, {1, 1}, "ticket-2"},
  };
  const auto reduced = delta::qlora::reduce_adapter_vectors(required, contributions);
  expect(reduced.size() == required.size(), "adapter reduce lost a required key");
  expect(
      reduced[0].numerators == std::vector<std::int64_t>({14, -1}),
      "adapter reduce differs from the direct fixed-point result");
  expect(
      delta::qlora::certificate_required_keys(required).size() == required.size(),
      "adapter matrix did not project to AggregateRootQC required keys");

  auto partial = contributions;
  partial.pop_back();
  expect_error(
      [&] { delta::qlora::validate_exact_coverage(required, partial); },
      delta::certificates::ErrorCode::coverage_incomplete,
      "incomplete adapter coverage was accepted");
  auto injected = contributions;
  injected.push_back({{"text", "model.layer0.base_weight"}, 1, {1, 1}, "ticket-2"});
  expect_error(
      [&] { delta::qlora::validate_exact_coverage(required, injected); },
      delta::certificates::ErrorCode::coverage_incomplete,
      "base tensor injection was accepted");
  auto duplicate = contributions;
  duplicate.push_back(contributions.front());
  expect_error(
      [&] { delta::qlora::validate_exact_coverage(required, duplicate); },
      delta::certificates::ErrorCode::duplicate_entry,
      "duplicate adapter contribution was accepted");
}

void test_existing_robust_plan_operates_on_adapter_q_vectors() {
  const std::vector<delta::robust::Contribution> adapters{
      {"text", {1, 2, 3, 4}, "ticket-000"},
      {"text", {2, 3, 4, 5}, "ticket-001"},
      {"text", {30, 30, 30, 30}, "ticket-002"},
  };
  const auto result = delta::robust::build_plan(
      certificate_context(),
      id('a'),
      id('b'),
      id('c'),
      id('d'),
      adapters,
      delta::robust::Profile{id('e'), 2U, 2U, 1U, 2U, 100, 3U},
      signers(),
      3U);
  expect(
      result.norms.context == certificate_context() &&
          result.eligibility.context == certificate_context() &&
          result.plan.context == certificate_context(),
      "existing norm/eligibility/plan pipeline lost the bound QLoRA context");
  expect(
      result.plan.weights.size() == 2U && result.eligibility.entries.size() == adapters.size(),
      "existing robust clipping/bucketing did not cover adapter q-vectors");
}

}  // namespace

int main() {
  try {
    test_existing_certificate_graph_is_context_bound();
    test_exact_adapter_matrix_and_integer_reduce();
    test_existing_robust_plan_operates_on_adapter_q_vectors();
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
  return 0;
}
