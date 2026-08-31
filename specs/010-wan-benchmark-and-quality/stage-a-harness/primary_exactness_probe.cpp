#include <delta/apply/engine.hpp>
#include <delta/certificates/verifier.hpp>
#include <delta/core/arithmetic.hpp>
#include <delta/core/canonical.hpp>
#include <delta/core/protocol.hpp>
#include <delta/fixedpoint/profile.hpp>
#include <delta/reduce/hierarchy.hpp>
#include <delta/robust/plan.hpp>
#include <delta/runtime/certificate_runtime.hpp>
#include <delta/runtime/runtime.hpp>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {

namespace apply = delta::apply;
namespace arithmetic = delta::core::arithmetic;
namespace canonical = delta::core::canonical;
namespace certificates = delta::certificates;
namespace fixedpoint = delta::fixedpoint;
namespace protocol = delta::core::protocol;
namespace reduce = delta::reduce;
namespace robust = delta::robust;
namespace runtime = delta::runtime;

constexpr std::size_t primary_ticket_count = 32U;
constexpr std::size_t primary_token_budget = 32'768U;
constexpr std::size_t primary_tokens_per_ticket =
    primary_token_budget / primary_ticket_count;
constexpr std::size_t vector_width = 4U;
constexpr std::string_view benchmark_definition_id =
    "sha256:dd607651128bca0b8edfa861093945b0bac2355c93d9d45b4c8b08457fba4244";

[[noreturn]] void fail(std::string message) { throw std::runtime_error(std::move(message)); }

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

[[nodiscard]] std::string content_id(std::string_view value) {
  const auto bytes = std::as_bytes(std::span(value.data(), value.size()));
  return "sha256:" + canonical::sha256_hex(bytes);
}

[[nodiscard]] std::string file_content_id(const std::filesystem::path& path) {
  std::ifstream input(path, std::ios::binary);
  expect(input.good(), "cannot open durable artifact");
  std::vector<char> raw{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  const auto bytes = std::as_bytes(std::span(raw.data(), raw.size()));
  return "sha256:" + canonical::sha256_hex(bytes);
}

[[nodiscard]] std::string ticket_id(std::size_t index) {
  auto digits = std::to_string(index);
  return "ticket-" + std::string(3U - digits.size(), '0') + digits;
}

[[nodiscard]] std::vector<std::string> primary_tickets() {
  std::vector<std::string> result;
  result.reserve(primary_ticket_count);
  for (std::size_t index = 0U; index < primary_ticket_count; ++index) {
    result.push_back(ticket_id(index));
  }
  return result;
}

[[nodiscard]] std::array<std::int64_t, vector_width> q_values(std::size_t index) {
  const auto value = static_cast<std::int64_t>(index);
  return {
      value + 1,
      -(value + 2),
      static_cast<std::int64_t>(index % 7U) - 3,
      static_cast<std::int64_t>(index % 5U) + 1,
  };
}

[[nodiscard]] certificates::Context certificate_context() {
  return certificates::Context{
      .arithmetic_profile_id = content_id("stage-a-arithmetic-profile"),
      .height = 10U,
      .parameter_schema_id = content_id("stage-a-parameter-schema"),
      .round_config_id = std::string(benchmark_definition_id),
      .round_id = "primary-exactness-010",
      .validator_epoch_id = content_id("stage-a-validator-epoch"),
      .view = 0U,
  };
}

[[nodiscard]] std::vector<std::string> quorum_signers() {
  return {"validator-0", "validator-1", "validator-2"};
}

[[nodiscard]] certificates::ChainVerifier chain_verifier() {
  const auto context = certificate_context();
  return certificates::ChainVerifier(
      context,
      certificates::ValidatorPolicy{
          context.validator_epoch_id,
          {"validator-0", "validator-1", "validator-2", "validator-3"},
          3U,
      });
}

struct CertificateChain {
  certificates::InputSetCertificate input_set;
  certificates::SeedTranscript seed;
  robust::PlanResult robust_plan;
  certificates::ParameterShardQc shard;
  certificates::AggregateRootQc root;
  certificates::ApplyArithmeticProfile apply_profile;
  certificates::ApplyCandidate candidate;
  certificates::ApplyQc apply_qc;
  certificates::CurrentPointerCommand pointer_command;
  std::vector<robust::Contribution> contributions;
};

[[nodiscard]] CertificateChain build_certificate_chain() {
  const auto context = certificate_context();
  auto verifier = chain_verifier();
  const auto tickets = primary_tickets();
  std::vector<certificates::InputTuple> tuples;
  std::vector<robust::Contribution> contributions;
  std::string input_transcript =
      std::string(benchmark_definition_id) + ";B=" +
      std::to_string(primary_token_budget) + ";H=" +
      std::to_string(primary_ticket_count) + ";tokens-per-ticket=" +
      std::to_string(primary_tokens_per_ticket) + ";";
  tuples.reserve(tickets.size());
  contributions.reserve(tickets.size());
  for (std::size_t index = 0U; index < tickets.size(); ++index) {
    const auto& ticket = tickets[index];
    const auto values = q_values(index);
    tuples.push_back(certificates::InputTuple{
        .availability_certificate_id = content_id("availability:" + ticket),
        .commitment_id = content_id("commitment:" + ticket),
        .domain_id = "wikitext-en",
        .ticket_id = ticket,
    });
    contributions.push_back(robust::Contribution{
        .domain_id = "wikitext-en",
        .q_values = std::vector<std::int64_t>(values.begin(), values.end()),
        .ticket_id = ticket,
    });
    input_transcript += ticket + ";";
  }
  certificates::InputSetCertificate input_set{
      .context = context,
      .input_root = content_id(input_transcript),
      .quorum_threshold = 3U,
      .signer_ids = quorum_signers(),
      .tuples = std::move(tuples),
  };
  const auto input_set_id = verifier.verify_input_set(input_set);
  std::vector<std::string> seed_shares{
      content_id("stage-a-seed-share-0"),
      content_id("stage-a-seed-share-1"),
      content_id("stage-a-seed-share-2"),
  };
  std::sort(seed_shares.begin(), seed_shares.end());
  certificates::SeedTranscript seed{
      .context = context,
      .input_set_certificate_id = input_set_id,
      .seed_id = content_id("2026090101"),
      .seed_profile_id = content_id("stage-a-seed-profile"),
      .share_ids = std::move(seed_shares),
  };
  const auto seed_id = verifier.verify_seed(seed, input_set_id);
  auto robust_plan = robust::build_plan(
      context,
      input_set_id,
      seed_id,
      content_id("stage-a-robust-profile"),
      seed.seed_id,
      contributions,
      robust::Profile{
          content_id("stage-a-accumulator-proof"),
          4U,
          4U,
          0U,
          primary_ticket_count,
          100,
          primary_ticket_count,
      },
      quorum_signers(),
      3U);
  const auto norm_id = verifier.verify_norms(robust_plan.norms, input_set_id);
  const auto eligibility_id =
      verifier.verify_eligibility(robust_plan.eligibility, input_set, norm_id);
  const auto plan_id = verifier.verify_plan(
      robust_plan.plan,
      input_set,
      robust_plan.eligibility,
      seed_id,
      robust_plan.plan.accumulator_proof_id);
  std::vector<std::string> leaves;
  leaves.reserve(tickets.size());
  for (const auto& ticket : tickets) {
    leaves.push_back(content_id("leaf:" + ticket));
  }
  std::sort(leaves.begin(), leaves.end());
  auto shard = robust::reduce_parameter_shard(
      context,
      input_set_id,
      eligibility_id,
      robust_plan.plan,
      "wikitext-en",
      "shard-000",
      contributions,
      std::move(leaves),
      quorum_signers(),
      3U);
  const auto shard_id = verifier.verify_shard(
      shard, input_set_id, eligibility_id, plan_id);
  std::vector<certificates::ShardKey> required{{"wikitext-en", "shard-000"}};
  certificates::AggregateRootQc root{
      .context = context,
      .aggregation_plan_certificate_id = plan_id,
      .eligibility_certificate_id = eligibility_id,
      .input_set_certificate_id = input_set_id,
      .leaves = {{"wikitext-en", shard_id, "shard-000"}},
      .merkle_root = {},
      .quorum_threshold = 3U,
      .required_keys = required,
      .signer_ids = quorum_signers(),
  };
  root.merkle_root = certificates::aggregate_merkle_root(root.leaves);
  const auto root_id = verifier.verify_root(
      root, input_set_id, eligibility_id, plan_id, required, {shard});
  certificates::ApplyArithmeticProfile apply_profile{
      .accumulator_proof_id = robust_plan.plan.accumulator_proof_id,
      .domain_weights = {{"wikitext-en", {1, 1U}}},
      .learning_rate = {1, 10U},
      .momentum = {9, 10U},
      .nesterov = true,
      .rounding = "HALF_TOWARD_POSITIVE",
      .weight_decay = {0, 1U},
  };
  std::vector<std::int64_t> aggregate_values;
  aggregate_values.reserve(shard.result_numerators.size());
  for (const auto& value : shard.result_numerators) {
    aggregate_values.push_back(std::stoll(value));
  }
  const apply::State parent{
      {100, -50, 25, -10},
      {10, -5, 2, -1},
      content_id("stage-a-parent-checkpoint"),
      content_id("stage-a-parent-optimizer"),
  };
  auto candidate = apply::compute_candidate(
      context,
      root_id,
      apply_profile,
      parent,
      std::array{apply::DomainAggregate{"wikitext-en", aggregate_values}});
  certificates::ApplyQc apply_qc{
      .context = context,
      .aggregate_root_qc_id = root_id,
      .apply_arithmetic_profile_id = certificates::content_id(apply_profile),
      .apply_candidate_id = certificates::content_id(candidate),
      .next_model_hash = candidate.next_model_hash,
      .next_optimizer_hash = candidate.next_optimizer_hash,
      .parent_checkpoint_id = candidate.parent_checkpoint_id,
      .quorum_threshold = 3U,
      .signer_ids = quorum_signers(),
  };
  static_cast<void>(verifier.verify_apply(
      apply_qc, candidate, root_id, certificates::content_id(apply_profile)));
  certificates::CurrentPointerCommand pointer_command{
      .context = context,
      .apply_qc_id = certificates::content_id(apply_qc),
      .expected_parent_checkpoint_id = parent.checkpoint_id,
      .next_checkpoint_id = apply_qc.next_model_hash,
      .next_optimizer_hash = apply_qc.next_optimizer_hash,
  };
  return CertificateChain{
      std::move(input_set),
      std::move(seed),
      std::move(robust_plan),
      std::move(shard),
      std::move(root),
      std::move(apply_profile),
      std::move(candidate),
      std::move(apply_qc),
      std::move(pointer_command),
      std::move(contributions),
  };
}

[[nodiscard]] reduce::Context reduce_context() {
  return reduce::Context{
      .accumulator_proof_instance_id = content_id("stage-a-hierarchy-accumulator"),
      .coefficient_plan_root = content_id("stage-a-coefficient-plan"),
      .fixedpoint_config_id = content_id("stage-a-fixedpoint-config"),
      .formal_semantics_id = std::string(certificates::formal_semantics_id),
      .frozen_input_root = content_id("stage-a-frozen-input"),
      .parent_checkpoint_id = content_id("stage-a-parent-checkpoint"),
      .profile_id = std::string(fixedpoint::fixed_profile_id()),
      .round_config_id = std::string(benchmark_definition_id),
      .scale_table_id = content_id("stage-a-scale-table"),
      .shard_plan_id = content_id("stage-a-shard-plan"),
  };
}

[[nodiscard]] reduce::Topology primary_topology() {
  const auto tickets = primary_tickets();
  std::vector<reduce::Region> regions;
  regions.reserve(4U);
  for (std::size_t region_index = 0U; region_index < 4U; ++region_index) {
    const auto begin = tickets.begin() + static_cast<std::ptrdiff_t>(region_index * 8U);
    const auto end = begin + 8;
    const auto prefix = "region-" + std::to_string(region_index);
    regions.push_back(reduce::Region{
        .fault_bound = 1U,
        .region_id = prefix,
        .tickets = std::vector<std::string>(begin, end),
        .validator_set = {
            prefix + "-validator-0",
            prefix + "-validator-1",
            prefix + "-validator-2",
            prefix + "-validator-3",
        },
    });
  }
  return reduce::Topology{
      .context = reduce_context(),
      .domains = {{
          .domain_id = "wikitext-en",
          .global_fault_bound = 1U,
          .global_validator_set = {
              "global-validator-0",
              "global-validator-1",
              "global-validator-2",
              "global-validator-3",
          },
          .regions = std::move(regions),
          .tickets = tickets,
      }},
      .hard_deadline_tick = 200U,
      .shards = {{4U, "shard-000", 0U}},
      .soft_deadline_tick = 100U,
      .validator_epoch = 10U,
      .topology_id = content_id("stage-a-primary-topology"),
  };
}

[[nodiscard]] reduce::HierarchyProofInstance primary_hierarchy_proof(
    const reduce::Topology& topology) {
  const auto product = arithmetic::checked_multiply(
      arithmetic::Int128::from_u64(static_cast<std::uint64_t>(fixedpoint::q_max)),
      arithmetic::Int128::from_u64(1U));
  const auto final_bound = arithmetic::checked_multiply(
      product, arithmetic::Int128::from_u64(primary_ticket_count));
  return reduce::HierarchyProofInstance{
      .hierarchy_proof_instance_id = content_id("stage-a-hierarchy-proof"),
      .topology_id = topology.topology_id,
      .context = topology.context,
      .coefficient_abs_max = 1U,
      .common_denominator = primary_ticket_count,
      .max_eligible_contributions = primary_ticket_count,
      .product_abs_bound = product,
      .final_abs_bound = final_bound,
      .q_abs_max = static_cast<std::uint64_t>(fixedpoint::q_max),
      .selected_width = arithmetic::AccumulatorWidth::int128,
      .domain_ticket_counts = {{"wikitext-en", primary_ticket_count}},
      .shard_ranges = {{0U, vector_width}},
      .theorem_bindings = {
          {"PO-H1", {"exact-partition"}},
          {"PO-H2", {"hierarchy-equals-flat"}},
          {"PO-A1", {"product-bound"}},
          {"PO-A2", {"flat-accumulator-bound"}},
          {"PO-A3",
           {"canonical-reduced-input", "input-denominator-divides-common",
            "numerator-accumulator-bound", "positive-common-denominator",
            "positive-input-denominator", "round-at-or-above-half", "round-below-half",
            "round-half-tie-toward-positive", "rounding-deterministic"}},
      },
  };
}

struct HierarchyResult {
  std::string flat_id;
  std::string hierarchical_id;
  std::string assembly_id;
  std::vector<std::string> committee_qc_ids;
  std::array<std::int64_t, vector_width> numerator;
};

[[nodiscard]] HierarchyResult execute_hierarchy_exactness(
    const std::vector<robust::Contribution>& robust_contributions) {
  const auto topology = primary_topology();
  const auto proof = primary_hierarchy_proof(topology);
  reduce::validate_topology(topology);
  reduce::validate_hierarchy_proof(topology, proof);
  std::vector<reduce::CoefficientBinding> coefficients;
  std::vector<reduce::Contribution> contributions;
  coefficients.reserve(robust_contributions.size());
  contributions.reserve(robust_contributions.size());
  std::array<std::int64_t, vector_width> sums{};
  for (const auto& contribution : robust_contributions) {
    std::vector<std::int16_t> values;
    values.reserve(contribution.q_values.size());
    for (std::size_t coordinate = 0U; coordinate < contribution.q_values.size(); ++coordinate) {
      const auto value = contribution.q_values[coordinate];
      values.push_back(static_cast<std::int16_t>(value));
      sums[coordinate] = arithmetic::checked_add(sums[coordinate], value);
    }
    coefficients.push_back({"wikitext-en", contribution.ticket_id, 1, primary_ticket_count});
    contributions.push_back(reduce::Contribution{
        .context = topology.context,
        .domain_id = "wikitext-en",
        .shard_id = "shard-000",
        .ticket_id = contribution.ticket_id,
        .worker_shard_id = content_id("worker-shard:" + contribution.ticket_id),
        .coefficient = 1,
        .coefficient_denominator = primary_ticket_count,
        .q_values = std::move(values),
    });
  }
  const auto bounds = reduce::validate_coefficient_plan(topology, proof, coefficients);
  expect(
      bounds.checked_coefficients == primary_ticket_count &&
          bounds.maximum_regional_terms == 8U && bounds.maximum_global_terms == primary_ticket_count,
      "primary hierarchy theorem preconditions changed");
  const auto flat = reduce::reduce_flat(
      topology, proof, "wikitext-en", "shard-000", contributions);
  reduce::GlobalAccumulator accumulator(topology, proof, "wikitext-en", "shard-000");
  std::vector<std::string> certificate_ids;
  for (const auto& region : topology.domains.front().regions) {
    std::vector<reduce::Contribution> regional;
    for (const auto& contribution : contributions) {
      if (std::binary_search(
              region.tickets.begin(), region.tickets.end(), contribution.ticket_id)) {
        regional.push_back(contribution);
      }
    }
    const auto result = reduce::reduce_region(
        topology, proof, "wikitext-en", region.region_id, "shard-000", regional);
    reduce::CommitteeQc certificate{
        .context = topology.context,
        .topology_id = topology.topology_id,
        .hierarchy_proof_instance_id = proof.hierarchy_proof_instance_id,
        .body_id = result.result_id,
        .domain_id = "wikitext-en",
        .region_id = region.region_id,
        .shard_id = "shard-000",
        .committee_epoch = topology.validator_epoch,
        .view = 0U,
        .quorum_threshold = 3U,
        .signer_ids = {region.validator_set[0], region.validator_set[1], region.validator_set[2]},
        .global = false,
    };
    reduce::validate_committee_qc(topology, proof, certificate);
    certificate_ids.push_back(reduce::committee_qc_id(certificate));
    expect(accumulator.ingest(result, certificate), "regional result was not admitted");
  }
  const auto hierarchical = accumulator.finalize();
  expect(
      reduce::canonical_bytes(flat) == reduce::canonical_bytes(hierarchical) &&
          flat.result_id == hierarchical.result_id,
      "flat and hierarchical primary results differ");
  for (std::size_t coordinate = 0U; coordinate < vector_width; ++coordinate) {
    expect(
        hierarchical.numerator[coordinate] == arithmetic::Int128::from_i64(sums[coordinate]),
        "hierarchy numerator differs from independent integer sum");
  }
  const auto& domain = topology.domains.front();
  reduce::CommitteeQc global_certificate{
      .context = topology.context,
      .topology_id = topology.topology_id,
      .hierarchy_proof_instance_id = proof.hierarchy_proof_instance_id,
      .body_id = hierarchical.result_id,
      .domain_id = "wikitext-en",
      .region_id = {},
      .shard_id = "shard-000",
      .committee_epoch = topology.validator_epoch,
      .view = 0U,
      .quorum_threshold = 3U,
      .signer_ids = {
          domain.global_validator_set[0],
          domain.global_validator_set[1],
          domain.global_validator_set[2],
      },
      .global = true,
  };
  reduce::validate_committee_qc(topology, proof, global_certificate);
  certificate_ids.push_back(reduce::committee_qc_id(global_certificate));
  const auto assembly = reduce::assemble_complete(
      topology,
      proof,
      std::array{hierarchical},
      std::array{global_certificate});
  return HierarchyResult{
      flat.result_id,
      hierarchical.result_id,
      assembly.aggregate_id,
      std::move(certificate_ids),
      sums,
  };
}

[[nodiscard]] canonical::Bytes initial_runtime_state() {
  return protocol::encode(protocol::RoundState{
      .available_ticket_count = 0U,
      .committed_ticket_count = 0U,
      .config_id = content_id("stage-a-runtime-config"),
      .durable_sequence = 0U,
      .height = 10U,
      .parent_checkpoint_id = content_id("stage-a-parent-checkpoint"),
      .phase = protocol::RoundPhase::ticketing_open,
      .round_id = "primary-exactness-010",
      .state_root = content_id("stage-a-initial-state"),
      .ticket_count = primary_ticket_count,
      .view = 0U,
  });
}

struct RuntimeResult {
  std::string state_id;
  std::string effect_set_id;
  std::string wal_sha256;
};

[[nodiscard]] RuntimeResult execute_runtime_exactness(const std::filesystem::path& root) {
  const auto directory = root / "runtime";
  runtime::Runtime instance({directory, initial_runtime_state(), 64U});
  std::string effect_transcript;
  std::string state_id;
  for (std::size_t index = 0U; index < primary_ticket_count; ++index) {
    const auto state = protocol::parse_round_state(instance.state_bytes());
    const protocol::Command command{
        "worker-" + std::to_string(index),
        content_id("runtime-body:" + ticket_id(index)),
        "ACCEPT_COMMITMENT",
        state.height,
        10U + index,
        "primary-request-" + std::to_string(index),
        state.round_id,
        state.view,
    };
    const auto receipt = instance.submit(protocol::encode(command));
    expect(!receipt.replay, "fresh primary commitment was classified as replay");
    state_id = receipt.next_state_id;
    effect_transcript += receipt.effect_batch_id + ";";
  }
  expect(instance.journal_sequence() == primary_ticket_count, "runtime WAL sequence is incomplete");
  instance.snapshot();
  const auto final_state = instance.state_bytes();
  instance.close();
  {
    runtime::Runtime recovered({directory, initial_runtime_state(), 64U});
    expect(recovered.journal_sequence() == primary_ticket_count, "runtime WAL replay is incomplete");
    expect(
        protocol::parse_round_state(recovered.state_bytes()).state_root ==
            protocol::parse_round_state(final_state).state_root,
        "runtime recovered a different state root");
  }
  return RuntimeResult{
      std::move(state_id),
      content_id(effect_transcript),
      file_content_id(directory / "runtime.wal"),
  };
}

struct PointerResult {
  std::string checkpoint_id;
  std::string optimizer_id;
  std::string wal_sha256;
};

[[nodiscard]] PointerResult execute_pointer_exactness(
    const std::filesystem::path& root,
    const CertificateChain& chain) {
  const auto directory = root / "current-pointer";
  const runtime::PointerState initial{
      chain.pointer_command.expected_parent_checkpoint_id,
      chain.candidate.parent_optimizer_hash,
      content_id("stage-a-no-apply-qc"),
      chain.pointer_command.context.height - 1U,
  };
  {
    runtime::CurrentPointerStore store(directory, initial);
    expect(
        store.advance(chain.pointer_command, chain.apply_qc) ==
            runtime::PointerDisposition::advanced,
        "ApplyQC did not advance the current pointer");
    expect(
        store.advance(chain.pointer_command, chain.apply_qc) ==
            runtime::PointerDisposition::replay,
        "ApplyQC replay was not idempotent");
  }
  runtime::CurrentPointerStore recovered(directory, initial);
  expect(
      recovered.state().checkpoint_id == chain.apply_qc.next_model_hash &&
          recovered.state().optimizer_id == chain.apply_qc.next_optimizer_hash,
      "current pointer recovery differs from ApplyQC");
  return PointerResult{
      recovered.state().checkpoint_id,
      recovered.state().optimizer_id,
      file_content_id(directory / "current-pointer.wal"),
  };
}

[[nodiscard]] std::string json_array(const std::vector<std::string>& values) {
  std::string output{"["};
  for (std::size_t index = 0U; index < values.size(); ++index) {
    if (index != 0U) {
      output += ',';
    }
    output += '"' + values[index] + '"';
  }
  output += ']';
  return output;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    expect(argc == 2, "usage: stage_a_primary_exactness_probe OUTPUT_DIRECTORY");
    const std::filesystem::path output_root = std::filesystem::absolute(argv[1]);
    expect(!std::filesystem::exists(output_root), "output directory already exists");
    std::filesystem::create_directories(output_root);
    const auto chain = build_certificate_chain();
    const auto hierarchy = execute_hierarchy_exactness(chain.contributions);
    expect(
        chain.shard.result_numerators.size() == hierarchy.numerator.size(),
        "certificate and hierarchy vector widths differ");
    for (std::size_t coordinate = 0U; coordinate < hierarchy.numerator.size(); ++coordinate) {
      expect(
          std::stoll(chain.shard.result_numerators[coordinate]) == hierarchy.numerator[coordinate],
          "certificate parameter result differs from hierarchy result");
    }
    const auto runtime_result = execute_runtime_exactness(output_root);
    const auto pointer = execute_pointer_exactness(output_root, chain);
    const auto input_set_id = certificates::content_id(chain.input_set);
    const auto plan_id = certificates::content_id(chain.robust_plan.plan);
    const auto shard_id = certificates::content_id(chain.shard);
    const auto root_id = certificates::content_id(chain.root);
    const auto candidate_id = certificates::content_id(chain.candidate);
    const auto apply_qc_id = certificates::content_id(chain.apply_qc);
    const auto protocol_result_id = content_id(
        input_set_id + plan_id + shard_id + root_id + candidate_id + apply_qc_id +
        hierarchy.assembly_id + runtime_result.state_id + runtime_result.effect_set_id +
        runtime_result.wal_sha256 + pointer.checkpoint_id + pointer.optimizer_id +
        pointer.wal_sha256);
    std::cout
        << "{\"aggregate_root_qc_id\":\"" << root_id
        << "\",\"apply_candidate_id\":\"" << candidate_id
        << "\",\"apply_qc_id\":\"" << apply_qc_id
        << "\",\"benchmark_definition_id\":\"" << benchmark_definition_id
        << "\",\"checkpoint_id\":\"" << pointer.checkpoint_id
        << "\",\"checkpoint_wal_sha256\":\"" << pointer.wal_sha256
        << "\",\"committee_qc_ids\":" << json_array(hierarchy.committee_qc_ids)
        << ",\"effect_set_id\":\"" << runtime_result.effect_set_id
        << "\",\"flat_result_id\":\"" << hierarchy.flat_id
        << "\",\"formal_semantics_id\":\"" << certificates::formal_semantics_id
        << "\",\"hierarchical_assembly_id\":\"" << hierarchy.assembly_id
        << "\",\"hierarchical_result_id\":\"" << hierarchy.hierarchical_id
        << "\",\"input_set_certificate_id\":\"" << input_set_id
        << "\",\"parameter_shard_qc_id\":\"" << shard_id
        << "\",\"primary_ticket_count\":" << primary_ticket_count
        << ",\"primary_token_budget\":" << primary_token_budget
        << ",\"primary_tokens_per_ticket\":" << primary_tokens_per_ticket
        << ",\"protocol_result_id\":\"" << protocol_result_id
        << "\",\"robust_plan_id\":\"" << plan_id
        << "\",\"runtime_state_id\":\"" << runtime_result.state_id
        << "\",\"runtime_wal_sha256\":\"" << runtime_result.wal_sha256
        << "\",\"schema_version\":\"1.0.0\",\"status\":\"PASS\","
           "\"type_name\":\"PRIMARY_EXACTNESS_PROCESS_RESULT\"}\n";
  } catch (const std::exception& error) {
    std::cerr << "stage A primary exactness probe failed: " << error.what() << '\n';
    return 1;
  }
  return 0;
}
