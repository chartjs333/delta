#include <delta/apply/engine.hpp>
#include <delta/certificates/verifier.hpp>
#include <delta/core/protocol.hpp>
#include <delta/distribution/certification_policy.hpp>
#include <delta/robust/plan.hpp>
#include <delta/runtime/certificate_runtime.hpp>

#include <cstdint>
#include <filesystem>
#include <iostream>
#include <limits>
#include <span>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

namespace {

using delta::certificates::AggregateRootQc;
using delta::certificates::AggregationPlanCertificate;
using delta::certificates::ApplyArithmeticProfile;
using delta::certificates::ApplyQc;
using delta::certificates::ChainVerifier;
using delta::certificates::Context;
using delta::certificates::EligibilityCertificate;
using delta::certificates::InputSetCertificate;
using delta::certificates::ParameterShardQc;
using delta::certificates::ShardKey;

[[noreturn]] void fail(const char* message) { throw std::runtime_error(message); }

void expect(bool condition, const char* message) {
  if (!condition) {
    fail(message);
  }
}

template <typename Function>
void expect_certificate_error(
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

[[nodiscard]] Context context() {
  return Context{
      .arithmetic_profile_id = id('d'),
      .height = 8U,
      .parameter_schema_id = id('c'),
      .round_config_id = id('a'),
      .round_id = "round-008",
      .validator_epoch_id = id('e'),
      .view = 0U,
  };
}

[[nodiscard]] std::vector<std::string> signers() {
  return {"validator-0", "validator-1", "validator-2"};
}

[[nodiscard]] InputSetCertificate input_set() {
  return InputSetCertificate{
      .context = context(),
      .input_root = "sha256:1ec8ff982235c59be66cbc34206a90751c685d86a2aca810ec07fc9361564896",
      .quorum_threshold = 3U,
      .signer_ids = signers(),
      .tuples = {
          {
              "sha256:b377488b0af300123073d8872b59f48f58a241be09c827acc378ca5150248648",
              "sha256:3287d4180e6037e0d89aea675878429416f61530c2c285177ecada417899bad0",
              "code",
              "ticket-000",
          },
          {
              "sha256:01aa10748bcea19d1d7237f3adf3d60cbec5cb1fe11dfdd609342cbe90172cca",
              "sha256:69fdd6276a37f5e42af7f0405a21703b605543d088242983ac425fa848b38906",
              "code",
              "ticket-001",
          },
          {
              "sha256:acc2f4c6f126edf31ac85a36e5d1c758514e9e7a1c9e684950a9463ece4d9f4e",
              "sha256:566a44a3b3bcd2b692af3477a4bd1d05ae1872acf81ee1d4284c2e8e2c5cc374",
              "text",
              "ticket-002",
          },
      },
  };
}

[[nodiscard]] ParameterShardQc shard(
    const std::string& isc,
    const std::string& ec,
    const std::string& apc,
    std::string domain,
    std::string shard_id,
    char leaf_digit) {
  return ParameterShardQc{
      .context = context(),
      .aggregation_plan_certificate_id = apc,
      .denominator = 2U,
      .domain_id = std::move(domain),
      .eligibility_certificate_id = ec,
      .input_leaf_ids = {id(leaf_digit)},
      .input_set_certificate_id = isc,
      .quorum_threshold = 3U,
      .result_numerators = {"12", "-3"},
      .shard_id = std::move(shard_id),
      .signer_ids = signers(),
  };
}

[[nodiscard]] delta::core::canonical::Bytes initial_state() {
  return delta::core::protocol::encode(delta::core::protocol::RoundState{
      .available_ticket_count = 0U,
      .committed_ticket_count = 0U,
      .config_id = id('a'),
      .durable_sequence = 0U,
      .height = 8U,
      .parent_checkpoint_id = id('b'),
      .phase = delta::core::protocol::RoundPhase::ticketing_open,
      .round_id = "round-008",
      .state_root = id('0'),
      .ticket_count = 3U,
      .view = 0U,
  });
}

struct Chain {
  InputSetCertificate isc;
  delta::certificates::SeedTranscript seed;
  delta::robust::PlanResult robust;
  std::vector<ShardKey> required;
  std::vector<ParameterShardQc> shards;
  AggregateRootQc root;
  ApplyArithmeticProfile profile;
  delta::certificates::ApplyCandidate candidate;
  ApplyQc apply_qc;
};

[[nodiscard]] Chain make_chain() {
  ChainVerifier verifier(
      context(),
      delta::certificates::ValidatorPolicy{
          id('e'), {"validator-0", "validator-1", "validator-2", "validator-3"}, 3U});
  auto isc = input_set();
  const auto isc_id = verifier.verify_input_set(isc);
  auto seed = delta::certificates::SeedTranscript{
      .context = context(),
      .input_set_certificate_id = isc_id,
      .seed_id = id('4'),
      .seed_profile_id = id('3'),
      .share_ids = {id('5'), id('6'), id('7')},
  };
  const auto seed_id = verifier.verify_seed(seed, isc_id);
  const std::vector<delta::robust::Contribution> contributions{
      {"code", {3, 4}, "ticket-000"},
      {"code", {4, 5}, "ticket-001"},
      {"text", {0, 3}, "ticket-002"},
  };
  auto robust = delta::robust::build_plan(
      context(),
      isc_id,
      seed_id,
      id('1'),
      seed.seed_id,
      contributions,
      delta::robust::Profile{id('2'), 2U, 4U, 1U, 2U, 100, 3U},
      signers(),
      3U);
  const auto norm_id = verifier.verify_norms(robust.norms, isc_id);
  const auto ec_id = verifier.verify_eligibility(robust.eligibility, isc, norm_id);
  const auto apc_id = verifier.verify_plan(robust.plan, isc, robust.eligibility, seed_id, id('2'));
  std::vector<ShardKey> required{{"code", "shard-000"}, {"text", "shard-000"}};
  std::vector<ParameterShardQc> shards{
      shard(isc_id, ec_id, apc_id, "code", "shard-000", '8'),
      shard(isc_id, ec_id, apc_id, "text", "shard-000", '9'),
  };
  AggregateRootQc root{
      .context = context(),
      .aggregation_plan_certificate_id = apc_id,
      .eligibility_certificate_id = ec_id,
      .input_set_certificate_id = isc_id,
      .leaves = {
          {"code", delta::certificates::content_id(shards[0]), "shard-000"},
          {"text", delta::certificates::content_id(shards[1]), "shard-000"},
      },
      .merkle_root = {},
      .quorum_threshold = 3U,
      .required_keys = required,
      .signer_ids = signers(),
  };
  root.merkle_root = delta::certificates::aggregate_merkle_root(root.leaves);
  const auto root_id = verifier.verify_root(root, isc_id, ec_id, apc_id, required, shards);
  ApplyArithmeticProfile profile{
      .accumulator_proof_id = id('2'),
      .domain_weights = {{"code", {1, 2U}}, {"text", {1, 2U}}},
      .learning_rate = {1, 10U},
      .momentum = {9, 10U},
      .nesterov = true,
      .rounding = "HALF_TOWARD_POSITIVE",
      .weight_decay = {1, 100U},
  };
  const delta::apply::State parent{{100, -50}, {10, -5}, id('b'), id('7')};
  const std::vector<delta::apply::DomainAggregate> aggregates{
      {"code", {8, -2}}, {"text", {4, 6}}};
  auto candidate = delta::apply::compute_candidate(context(), root_id, profile, parent, aggregates);
  ApplyQc apply_qc{
      .context = context(),
      .aggregate_root_qc_id = root_id,
      .apply_arithmetic_profile_id = delta::certificates::content_id(profile),
      .apply_candidate_id = delta::certificates::content_id(candidate),
      .next_model_hash = candidate.next_model_hash,
      .next_optimizer_hash = candidate.next_optimizer_hash,
      .parent_checkpoint_id = candidate.parent_checkpoint_id,
      .quorum_threshold = 3U,
      .signer_ids = signers(),
  };
  (void)verifier.verify_apply(
      apply_qc, candidate, root_id, delta::certificates::content_id(profile));
  return Chain{
      std::move(isc),
      std::move(seed),
      std::move(robust),
      std::move(required),
      std::move(shards),
      std::move(root),
      std::move(profile),
      std::move(candidate),
      std::move(apply_qc),
  };
}

void test_golden_and_chain() {
  const auto chain = make_chain();
  expect(
      delta::certificates::content_id(chain.isc) ==
          "sha256:abf1eaf832da858d0dbf41ffd146675be5189bee70a34a0c258429a3ac68ebac",
      "C++ ISC bytes differ from the frozen cross-language fixture");
  for (std::size_t validator = 1U; validator < 4U; ++validator) {
    const auto independent = make_chain();
    expect(
        delta::certificates::content_id(chain.robust.plan) ==
                delta::certificates::content_id(independent.robust.plan) &&
            delta::certificates::content_id(chain.root) ==
                delta::certificates::content_id(independent.root) &&
            delta::certificates::content_id(chain.candidate) ==
                delta::certificates::content_id(independent.candidate),
        "four validators produced different chain bytes");
  }
  const std::vector<delta::robust::Contribution> code{{"code", {3, 4}, "ticket-000"}};
  const auto reduced = delta::robust::reduce_parameter_shard(
      context(),
      delta::certificates::content_id(chain.isc),
      delta::certificates::content_id(chain.robust.eligibility),
      chain.robust.plan,
      "code",
      "shard-000",
      code,
      {id('8')},
      signers(),
      3U);
  expect(
      reduced.denominator == 2U && reduced.result_numerators == std::vector<std::string>{"3", "4"},
      "APC exact integer parameter reduction changed");
  const auto manifest = std::string{"{\"certificate_policy_id\":\""} +
                        std::string(delta::distribution::inactive_apply_policy_id) +
                        "\",\"certificate_root\":\"" + chain.apply_qc.next_model_hash +
                        "\",\"formal_semantics_id\":\"" +
                        std::string(delta::distribution::formal_semantics_id) +
                        "\",\"media_type\":\"application/vnd.deltareduce.checkpoint;version=1\"," +
                        "\"policy_registry_id\":\"" +
                        std::string(delta::distribution::policy_registry_id) +
                        "\",\"source_state\":\"APPLIED\",\"type_name\":\"OBJECT_MANIFEST\"}";
  const auto manifest_bytes = std::as_bytes(std::span(manifest.data(), manifest.size()));
  const auto publish =
      delta::distribution::evaluate_applied_checkpoint(manifest_bytes, chain.apply_qc, true);
  expect(
      publish.accepted && publish.formal_action_id == "ACT-APPLY-CURRENT",
      "feature-005 apply-qc-v1 distribution strength was not activated by native ApplyQC");
}

void test_rejections() {
  auto chain = make_chain();
  ChainVerifier verifier(
      context(),
      delta::certificates::ValidatorPolicy{
          id('e'), {"validator-0", "validator-1", "validator-2", "validator-3"}, 3U});
  auto early_seed = chain.seed;
  early_seed.input_set_certificate_id = id('f');
  expect_certificate_error(
      [&] { (void)verifier.verify_seed(early_seed, delta::certificates::content_id(chain.isc)); },
      delta::certificates::ErrorCode::parent_mismatch,
      "early/wrong-parent seed was accepted");
  const delta::certificates::OpaqueTimerToken timer{
      context(), "VIEW-TIMEOUT", 10U, 20U, id('6')};
  expect_certificate_error(
      [&] { verifier.verify_timer(timer, 21U); },
      delta::certificates::ErrorCode::stale_timer,
      "stale opaque timer was accepted");
  verifier.verify_timer(timer, 10U);
  auto mutated = chain.robust.eligibility;
  mutated.entries[0].ticket_id = "ticket-999";
  expect_certificate_error(
      [&] {
        (void)verifier.verify_eligibility(
            mutated, chain.isc, delta::certificates::content_id(chain.robust.norms));
      },
      delta::certificates::ErrorCode::membership_mutation,
      "eligibility membership mutation was accepted");
  auto incomplete = chain.root;
  incomplete.leaves.pop_back();
  expect_certificate_error(
      [&] {
        (void)verifier.verify_root(
            incomplete,
            delta::certificates::content_id(chain.isc),
            delta::certificates::content_id(chain.robust.eligibility),
            delta::certificates::content_id(chain.robust.plan),
            chain.required,
            chain.shards);
      },
      delta::certificates::ErrorCode::coverage_incomplete,
      "incomplete aggregate root was accepted");
  auto mixed = chain.shards;
  mixed[1].context.view = 1U;
  expect_certificate_error(
      [&] {
        (void)verifier.verify_root(
            chain.root,
            delta::certificates::content_id(chain.isc),
            delta::certificates::content_id(chain.robust.eligibility),
            delta::certificates::content_id(chain.robust.plan),
            chain.required,
            mixed);
      },
      delta::certificates::ErrorCode::context_mismatch,
      "mixed-view Frankenstein root was accepted");
  expect_certificate_error(
      [] {
        const std::vector<std::int64_t> values{
            std::numeric_limits<std::int64_t>::max(), 1};
        (void)delta::robust::exact_squared_norm(values);
      },
      delta::certificates::ErrorCode::arithmetic_invalid,
      "norm overflow was accepted");
}

void test_rounding() {
  expect(delta::apply::round_half_toward_positive(1, 2U) == 1, "positive tie failed");
  expect(delta::apply::round_half_toward_positive(-1, 2U) == 0, "negative tie failed");
  expect(delta::apply::round_half_toward_positive(-2, 3U) == -1, "negative rounding failed");
  expect(delta::apply::round_half_toward_positive(2, 3U) == 1, "positive rounding failed");
}

void test_vote_and_pointer_recovery() {
  const auto chain = make_chain();
  const auto directory = std::filesystem::temp_directory_path() / "delta-008-certificate-test";
  std::filesystem::remove_all(directory);
  {
    delta::runtime::CertificateVoteRuntime runtime(directory / "votes", initial_state());
    std::uint64_t sequence = 1U;
    const std::vector<std::pair<delta::certificates::VoteKind, std::string>> bodies{
        {delta::certificates::VoteKind::input_set, delta::certificates::content_id(chain.isc)},
        {delta::certificates::VoteKind::eligibility,
         delta::certificates::content_id(chain.robust.eligibility)},
        {delta::certificates::VoteKind::aggregation_plan,
         delta::certificates::content_id(chain.robust.plan)},
        {delta::certificates::VoteKind::parameter_shard,
         delta::certificates::content_id(chain.shards[0])},
        {delta::certificates::VoteKind::aggregate_root,
         delta::certificates::content_id(chain.root)},
        {delta::certificates::VoteKind::apply, delta::certificates::content_id(chain.apply_qc)},
    };
    for (const auto& [kind, body] : bodies) {
      const auto vote = delta::certificates::make_vote(
          kind, context(), body, "validator-0", id('6'), sequence++);
      const auto receipt = runtime.persist_and_expose(vote);
      expect(!receipt.replay, "new certificate vote was treated as replay");
    }
  }
  {
    delta::runtime::CertificateVoteRuntime recovered(directory / "votes", initial_state());
    expect(recovered.recovered_vote_count() == 6U, "certificate votes were not recovered");
    const auto replay_vote = delta::certificates::make_vote(
        delta::certificates::VoteKind::apply,
        context(),
        delta::certificates::content_id(chain.apply_qc),
        "validator-0",
        id('6'),
        6U);
    expect(recovered.persist_and_expose(replay_vote).replay, "durable vote replay was not idempotent");
    const auto conflict = delta::certificates::make_vote(
        delta::certificates::VoteKind::apply,
        context(),
        id('f'),
        "validator-0",
        id('6'),
        7U);
    bool rejected = false;
    try {
      (void)recovered.persist_and_expose(conflict);
    } catch (const delta::core::consensus::ConsensusError&) {
      rejected = true;
    }
    expect(rejected, "conflicting durable vote was accepted");
  }

  const delta::runtime::PointerState initial{id('b'), id('7'), {}, 7U};
  const auto command = delta::certificates::CurrentPointerCommand{
      context(),
      delta::certificates::content_id(chain.apply_qc),
      chain.apply_qc.parent_checkpoint_id,
      chain.apply_qc.next_model_hash,
      chain.apply_qc.next_optimizer_hash,
  };
  {
    delta::runtime::CurrentPointerStore store(directory / "pointer-torn", initial);
    bool crashed = false;
    try {
      (void)store.advance(command, chain.apply_qc, delta::runtime::CrashPoint::during_wal_append);
    } catch (const delta::runtime::RuntimeError& error) {
      crashed = error.code() == delta::runtime::ErrorCode::simulated_crash;
    }
    expect(crashed, "torn pointer crash was not injected");
  }
  {
    delta::runtime::CurrentPointerStore recovered(directory / "pointer-torn", initial);
    expect(recovered.state() == initial, "torn pointer tail changed current state");
  }
  {
    delta::runtime::CurrentPointerStore store(directory / "pointer", initial);
    bool crashed = false;
    try {
      (void)store.advance(
          command, chain.apply_qc, delta::runtime::CrashPoint::after_durability_before_commit);
    } catch (const delta::runtime::RuntimeError& error) {
      crashed = error.code() == delta::runtime::ErrorCode::simulated_crash;
    }
    expect(crashed, "pointer durability crash was not injected");
  }
  {
    delta::runtime::CurrentPointerStore recovered(directory / "pointer", initial);
    expect(
        recovered.state().checkpoint_id == chain.apply_qc.next_model_hash,
        "durable pointer command was not recovered");
    expect(
        recovered.advance(command, chain.apply_qc) == delta::runtime::PointerDisposition::replay,
        "recovered pointer command was not idempotent");
  }
  std::filesystem::remove_all(directory);
}

}  // namespace

int main() {
  try {
    test_golden_and_chain();
    test_rejections();
    test_rounding();
    test_vote_and_pointer_recovery();
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 1;
  }
  return 0;
}
