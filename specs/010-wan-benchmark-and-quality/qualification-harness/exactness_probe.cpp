#include <delta/apply/engine.hpp>
#include <delta/certificates/verifier.hpp>
#include <delta/core/arithmetic.hpp>
#include <delta/core/canonical.hpp>
#include <delta/fixedpoint/profile.hpp>
#include <delta/reduce/hierarchy.hpp>
#include <delta/robust/plan.hpp>
#include <delta/runtime/certificate_runtime.hpp>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <map>
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
namespace reduce = delta::reduce;
namespace robust = delta::robust;
namespace runtime = delta::runtime;

constexpr std::size_t kDeclaredH = 16U;
constexpr std::size_t kDeclaredB = 64U;
constexpr std::size_t kSyntheticContributionCount = 16U;
constexpr std::size_t kVectorWidth = 4U;
constexpr std::string_view kDefinitionId =
    "sha256:32c8e884d1d93a3de77881d30df2bf78ed45d59017b38ca1318664e77485a449";

[[noreturn]] void fail(std::string message) { throw std::runtime_error(std::move(message)); }

void expect(bool condition, std::string_view message) {
  if (!condition) fail(std::string(message));
}

[[nodiscard]] std::string content_id(std::string_view value) {
  return "sha256:" + canonical::sha256_hex(std::as_bytes(std::span(value.data(), value.size())));
}

[[nodiscard]] std::string file_content_id(const std::filesystem::path& path) {
  std::ifstream input(path, std::ios::binary);
  expect(input.good(), "cannot open exact durable artifact");
  const std::vector<char> raw{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  return "sha256:" + canonical::sha256_hex(std::as_bytes(std::span(raw.data(), raw.size())));
}

[[nodiscard]] std::string read_file(const std::filesystem::path& path) {
  std::ifstream input(path, std::ios::binary);
  expect(input.good(), "cannot open process receipt");
  return {std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
}

[[nodiscard]] std::string json_string_field(std::string_view document,
                                            std::string_view field) {
  const auto prefix = "\"" + std::string(field) + "\":\"";
  const auto start = document.find(prefix);
  expect(start != std::string_view::npos, "receipt field missing");
  const auto value_start = start + prefix.size();
  const auto end = document.find('"', value_start);
  expect(end != std::string_view::npos, "receipt field unterminated");
  return std::string(document.substr(value_start, end - value_start));
}

[[nodiscard]] std::string ticket_id(std::size_t index) {
  auto digits = std::to_string(index);
  return "ticket-" + std::string(3U - digits.size(), '0') + digits;
}

[[nodiscard]] std::vector<std::string> tickets() {
  std::vector<std::string> result;
  result.reserve(kSyntheticContributionCount);
  for (std::size_t index = 0U; index < kSyntheticContributionCount; ++index) {
    result.push_back(ticket_id(index));
  }
  return result;
}

[[nodiscard]] std::array<std::int64_t, kVectorWidth> q_values(std::size_t index) {
  const auto value = static_cast<std::int64_t>(index);
  return {value + 1, -(value + 2), static_cast<std::int64_t>(index % 7U) - 3,
          static_cast<std::int64_t>(index % 5U) + 1};
}

[[nodiscard]] certificates::Context certificate_context() {
  return certificates::Context{
      .arithmetic_profile_id = content_id("feature010-exactness-arithmetic"),
      .height = 10U,
      .parameter_schema_id = content_id("feature010-exactness-parameters"),
      .round_config_id = std::string(kDefinitionId),
      .round_id = "feature010-exactness-round",
      .validator_epoch_id = content_id("feature010-exactness-validators"),
      .view = 0U,
  };
}

[[nodiscard]] std::vector<std::string> quorum() {
  return {"validator-0", "validator-1", "validator-2"};
}

[[nodiscard]] certificates::ChainVerifier verifier() {
  const auto context = certificate_context();
  return certificates::ChainVerifier(
      context,
      certificates::ValidatorPolicy{
          context.validator_epoch_id,
          {"validator-0", "validator-1", "validator-2", "validator-3"},
          3U,
      });
}

struct Chain {
  certificates::InputSetCertificate input_set;
  robust::PlanResult robust_plan;
  certificates::ParameterShardQc shard;
  certificates::AggregateRootQc root;
  certificates::ApplyCandidate candidate;
  certificates::ApplyQc apply_qc;
  certificates::CurrentPointerCommand pointer;
  std::vector<robust::Contribution> contributions;
};

[[nodiscard]] Chain build_chain() {
  const auto context = certificate_context();
  auto check = verifier();
  const auto frozen_tickets = tickets();
  std::vector<certificates::InputTuple> tuples;
  std::vector<robust::Contribution> contributions;
  std::string transcript = std::string(kDefinitionId) + ";declared-B=" +
                           std::to_string(kDeclaredB) + ";declared-H=" +
                           std::to_string(kDeclaredH) + ";fixture-contributions=" +
                           std::to_string(kSyntheticContributionCount) + ";";
  for (std::size_t index = 0U; index < frozen_tickets.size(); ++index) {
    const auto& ticket = frozen_tickets[index];
    const auto values = q_values(index);
    tuples.push_back(certificates::InputTuple{
        .availability_certificate_id = content_id("availability:" + ticket),
        .commitment_id = content_id("commitment:" + ticket),
        .domain_id = "qualification-domain",
        .ticket_id = ticket,
    });
    contributions.push_back(robust::Contribution{
        .domain_id = "qualification-domain",
        .q_values = std::vector<std::int64_t>(values.begin(), values.end()),
        .ticket_id = ticket,
    });
    transcript += ticket + ";";
  }
  certificates::InputSetCertificate input_set{
      .context = context,
      .input_root = content_id(transcript),
      .quorum_threshold = 3U,
      .signer_ids = quorum(),
      .tuples = std::move(tuples),
  };
  const auto input_set_id = check.verify_input_set(input_set);
  std::vector<std::string> shares{
      content_id("feature010-seed-share-0"), content_id("feature010-seed-share-1"),
      content_id("feature010-seed-share-2")};
  std::sort(shares.begin(), shares.end());
  const certificates::SeedTranscript seed{
      .context = context,
      .input_set_certificate_id = input_set_id,
      .seed_id = content_id("feature010-seed"),
      .seed_profile_id = content_id("feature010-seed-profile"),
      .share_ids = std::move(shares),
  };
  const auto seed_id = check.verify_seed(seed, input_set_id);
  auto plan = robust::build_plan(
      context, input_set_id, seed_id, content_id("feature010-robust-profile"), seed.seed_id,
      contributions,
      robust::Profile{content_id("feature010-accumulator-proof"), 4U, 4U, 0U,
                      kSyntheticContributionCount, 100U, kSyntheticContributionCount},
      quorum(), 3U);
  const auto norm_id = check.verify_norms(plan.norms, input_set_id);
  const auto eligibility_id = check.verify_eligibility(plan.eligibility, input_set, norm_id);
  const auto plan_id = check.verify_plan(
      plan.plan, input_set, plan.eligibility, seed_id, plan.plan.accumulator_proof_id);
  std::vector<std::string> leaves;
  for (const auto& ticket : frozen_tickets) leaves.push_back(content_id("leaf:" + ticket));
  std::sort(leaves.begin(), leaves.end());
  auto shard = robust::reduce_parameter_shard(
      context, input_set_id, eligibility_id, plan.plan, "qualification-domain", "shard-000",
      contributions, std::move(leaves), quorum(), 3U);
  const auto shard_id = check.verify_shard(shard, input_set_id, eligibility_id, plan_id);
  const std::vector<certificates::ShardKey> required{{"qualification-domain", "shard-000"}};
  certificates::AggregateRootQc root{
      .context = context,
      .aggregation_plan_certificate_id = plan_id,
      .eligibility_certificate_id = eligibility_id,
      .input_set_certificate_id = input_set_id,
      .leaves = {{"qualification-domain", shard_id, "shard-000"}},
      .merkle_root = {},
      .quorum_threshold = 3U,
      .required_keys = required,
      .signer_ids = quorum(),
  };
  root.merkle_root = certificates::aggregate_merkle_root(root.leaves);
  const auto root_id = check.verify_root(
      root, input_set_id, eligibility_id, plan_id, required,
      std::vector<certificates::ParameterShardQc>{shard});
  const certificates::ApplyArithmeticProfile apply_profile{
      .accumulator_proof_id = plan.plan.accumulator_proof_id,
      .domain_weights = {{"qualification-domain", {1, 1U}}},
      .learning_rate = {1, 10U},
      .momentum = {9, 10U},
      .nesterov = true,
      .rounding = "HALF_TOWARD_POSITIVE",
      .weight_decay = {0, 1U},
  };
  std::vector<std::int64_t> aggregate;
  for (const auto& value : shard.result_numerators) aggregate.push_back(std::stoll(value));
  const apply::State parent{{100, -50, 25, -10}, {10, -5, 2, -1},
                            content_id("feature010-parent-checkpoint"),
                            content_id("feature010-parent-optimizer")};
  auto candidate = apply::compute_candidate(
      context, root_id, apply_profile, parent,
      std::array{apply::DomainAggregate{"qualification-domain", aggregate}});
  certificates::ApplyQc apply_qc{
      .context = context,
      .aggregate_root_qc_id = root_id,
      .apply_arithmetic_profile_id = certificates::content_id(apply_profile),
      .apply_candidate_id = certificates::content_id(candidate),
      .next_model_hash = candidate.next_model_hash,
      .next_optimizer_hash = candidate.next_optimizer_hash,
      .parent_checkpoint_id = candidate.parent_checkpoint_id,
      .quorum_threshold = 3U,
      .signer_ids = quorum(),
  };
  static_cast<void>(check.verify_apply(
      apply_qc, candidate, root_id, certificates::content_id(apply_profile)));
  certificates::CurrentPointerCommand pointer{
      .context = context,
      .apply_qc_id = certificates::content_id(apply_qc),
      .expected_parent_checkpoint_id = parent.checkpoint_id,
      .next_checkpoint_id = apply_qc.next_model_hash,
      .next_optimizer_hash = apply_qc.next_optimizer_hash,
  };
  return Chain{std::move(input_set), std::move(plan), std::move(shard), std::move(root),
               std::move(candidate), std::move(apply_qc), std::move(pointer),
               std::move(contributions)};
}

[[nodiscard]] std::string validator_receipt(std::string_view validator_id,
                                            std::string_view state_root,
                                            std::string_view effect_root) {
  return "{\"effect_root\":\"" + std::string(effect_root) +
         "\",\"state_root\":\"" + std::string(state_root) +
         "\",\"validator_id\":\"" + std::string(validator_id) + "\"}\n";
}

void run_validator(std::string_view validator_id) {
  const auto validators = quorum();
  const auto expected = std::find(validators.begin(), validators.end(), validator_id);
  const auto known_fourth = validator_id == "validator-3";
  expect(expected != validators.end() || known_fourth, "unknown validator identity");
  const auto chain = build_chain();
  std::cout << validator_receipt(validator_id, certificates::content_id(chain.root),
                                 certificates::content_id(chain.candidate));
}

struct AggregatorReceipt {
  std::string aggregator_effect_root;
  std::string aggregator_state_root;
  std::string validator_effect_root;
  std::string validator_receipts_sha256;
  std::string validator_state_root;
};

[[nodiscard]] std::string aggregator_receipt(const AggregatorReceipt& receipt) {
  return "{\"aggregator_effect_root\":\"" + receipt.aggregator_effect_root +
         "\",\"aggregator_state_root\":\"" + receipt.aggregator_state_root +
         "\",\"validator_effect_root\":\"" + receipt.validator_effect_root +
         "\",\"validator_process_count\":4,\"validator_receipts_sha256\":\"" +
         receipt.validator_receipts_sha256 + "\",\"validator_state_root\":\"" +
         receipt.validator_state_root + "\"}\n";
}

[[nodiscard]] AggregatorReceipt parse_aggregator_receipt(std::string_view document) {
  AggregatorReceipt result{
      json_string_field(document, "aggregator_effect_root"),
      json_string_field(document, "aggregator_state_root"),
      json_string_field(document, "validator_effect_root"),
      json_string_field(document, "validator_receipts_sha256"),
      json_string_field(document, "validator_state_root"),
  };
  expect(document == aggregator_receipt(result), "aggregator receipt is not canonical");
  return result;
}

void run_aggregator(std::span<char*> receipt_paths) {
  expect(receipt_paths.size() == 4U, "four validator receipts required");
  const auto chain = build_chain();
  const auto expected_state = certificates::content_id(chain.root);
  const auto expected_effect = certificates::content_id(chain.candidate);
  std::map<std::string, std::string> receipts;
  for (const auto* path : receipt_paths) {
    const auto raw = read_file(path);
    const auto validator_id = json_string_field(raw, "validator_id");
    const auto state_root = json_string_field(raw, "state_root");
    const auto effect_root = json_string_field(raw, "effect_root");
    expect(raw == validator_receipt(validator_id, state_root, effect_root),
           "validator receipt is not canonical");
    expect(state_root == expected_state, "validator state root differs");
    expect(effect_root == expected_effect, "validator effect root differs");
    expect(receipts.emplace(validator_id, raw).second, "duplicate validator process identity");
  }
  expect(receipts.size() == 4U && receipts.contains("validator-0") &&
             receipts.contains("validator-1") && receipts.contains("validator-2") &&
             receipts.contains("validator-3"),
         "validator process set is incomplete");
  std::string transcript;
  for (const auto& [validator_id, raw] : receipts) {
    transcript += validator_id;
    transcript.push_back('\0');
    transcript += raw;
  }
  const AggregatorReceipt receipt{
      certificates::content_id(chain.apply_qc), expected_state, expected_effect,
      content_id(transcript), expected_state};
  std::cout << aggregator_receipt(receipt);
}

[[nodiscard]] reduce::Context hierarchy_context() {
  return reduce::Context{
      .accumulator_proof_instance_id = content_id("feature010-hierarchy-accumulator"),
      .coefficient_plan_root = content_id("feature010-coefficients"),
      .fixedpoint_config_id = content_id("feature010-fixedpoint"),
      .formal_semantics_id = std::string(certificates::formal_semantics_id),
      .frozen_input_root = content_id("feature010-frozen-input"),
      .parent_checkpoint_id = content_id("feature010-parent-checkpoint"),
      .profile_id = std::string(fixedpoint::fixed_profile_id()),
      .round_config_id = std::string(kDefinitionId),
      .scale_table_id = content_id("feature010-scale-table"),
      .shard_plan_id = content_id("feature010-shard-plan"),
  };
}

[[nodiscard]] reduce::Topology topology() {
  const auto frozen_tickets = tickets();
  std::vector<reduce::Region> regions;
  for (std::size_t region_index = 0U; region_index < 4U; ++region_index) {
    const auto begin = frozen_tickets.begin() + static_cast<std::ptrdiff_t>(region_index * 4U);
    const auto prefix = "region-" + std::to_string(region_index);
    regions.push_back(reduce::Region{
        .fault_bound = 1U,
        .region_id = prefix,
        .tickets = std::vector<std::string>(begin, begin + 4),
        .validator_set = {prefix + "-validator-0", prefix + "-validator-1",
                          prefix + "-validator-2", prefix + "-validator-3"},
    });
  }
  return reduce::Topology{
      .context = hierarchy_context(),
      .domains = {{.domain_id = "qualification-domain",
                   .global_fault_bound = 1U,
                   .global_validator_set = {"global-validator-0", "global-validator-1",
                                            "global-validator-2", "global-validator-3"},
                   .regions = std::move(regions),
                   .tickets = frozen_tickets}},
      .hard_deadline_tick = 200U,
      .shards = {{4U, "shard-000", 0U}},
      .soft_deadline_tick = 100U,
      .validator_epoch = 10U,
      .topology_id = content_id("feature010-topology"),
  };
}

[[nodiscard]] reduce::HierarchyProofInstance proof(const reduce::Topology& value) {
  const auto product = arithmetic::checked_multiply(
      arithmetic::Int128::from_u64(static_cast<std::uint64_t>(fixedpoint::q_max)),
      arithmetic::Int128::from_u64(1U));
  return reduce::HierarchyProofInstance{
      .hierarchy_proof_instance_id = content_id("feature010-hierarchy-proof"),
      .topology_id = value.topology_id,
      .context = value.context,
      .coefficient_abs_max = 1U,
      .common_denominator = kSyntheticContributionCount,
      .max_eligible_contributions = kSyntheticContributionCount,
      .product_abs_bound = product,
      .final_abs_bound = arithmetic::checked_multiply(
          product, arithmetic::Int128::from_u64(kSyntheticContributionCount)),
      .q_abs_max = static_cast<std::uint64_t>(fixedpoint::q_max),
      .selected_width = arithmetic::AccumulatorWidth::int128,
      .domain_ticket_counts = {{"qualification-domain", kSyntheticContributionCount}},
      .shard_ranges = {{0U, kVectorWidth}},
      .theorem_bindings = {{"PO-H1", {"exact-partition"}},
                           {"PO-H2", {"hierarchy-equals-flat"}},
                           {"PO-A1", {"product-bound"}},
                           {"PO-A2", {"flat-accumulator-bound"}},
                           {"PO-A3", {"canonical-reduced-input",
                                      "input-denominator-divides-common",
                                      "numerator-accumulator-bound",
                                      "positive-common-denominator",
                                      "positive-input-denominator", "round-at-or-above-half",
                                      "round-below-half", "round-half-tie-toward-positive",
                                      "rounding-deterministic"}}},
  };
}

struct HierarchyResult {
  std::string flat_id;
  std::string hierarchy_id;
  std::string assembly_id;
};

[[nodiscard]] HierarchyResult execute_hierarchy(
    const std::vector<robust::Contribution>& robust_contributions) {
  const auto frozen_topology = topology();
  const auto frozen_proof = proof(frozen_topology);
  reduce::validate_topology(frozen_topology);
  reduce::validate_hierarchy_proof(frozen_topology, frozen_proof);
  std::vector<reduce::CoefficientBinding> coefficients;
  std::vector<reduce::Contribution> contributions;
  for (const auto& contribution : robust_contributions) {
    std::vector<std::int16_t> values;
    for (const auto value : contribution.q_values) values.push_back(static_cast<std::int16_t>(value));
    coefficients.push_back(
        {"qualification-domain", contribution.ticket_id, 1, kSyntheticContributionCount});
    contributions.push_back(reduce::Contribution{
        .context = frozen_topology.context,
        .domain_id = "qualification-domain",
        .shard_id = "shard-000",
        .ticket_id = contribution.ticket_id,
        .worker_shard_id = content_id("worker-shard:" + contribution.ticket_id),
        .coefficient = 1,
        .coefficient_denominator = kSyntheticContributionCount,
        .q_values = std::move(values),
    });
  }
  const auto bounds =
      reduce::validate_coefficient_plan(frozen_topology, frozen_proof, coefficients);
  expect(bounds.checked_coefficients == kSyntheticContributionCount,
         "coefficient matrix is incomplete");
  const auto flat = reduce::reduce_flat(
      frozen_topology, frozen_proof, "qualification-domain", "shard-000", contributions);
  reduce::GlobalAccumulator accumulator(
      frozen_topology, frozen_proof, "qualification-domain", "shard-000");
  for (const auto& region : frozen_topology.domains.front().regions) {
    std::vector<reduce::Contribution> regional;
    for (const auto& contribution : contributions) {
      if (std::binary_search(region.tickets.begin(), region.tickets.end(),
                             contribution.ticket_id)) {
        regional.push_back(contribution);
      }
    }
    const auto result = reduce::reduce_region(
        frozen_topology, frozen_proof, "qualification-domain", region.region_id,
        "shard-000", regional);
    const reduce::CommitteeQc certificate{
        .context = frozen_topology.context,
        .topology_id = frozen_topology.topology_id,
        .hierarchy_proof_instance_id = frozen_proof.hierarchy_proof_instance_id,
        .body_id = result.result_id,
        .domain_id = "qualification-domain",
        .region_id = region.region_id,
        .shard_id = "shard-000",
        .committee_epoch = frozen_topology.validator_epoch,
        .view = 0U,
        .quorum_threshold = 3U,
        .signer_ids = {region.validator_set[0], region.validator_set[1],
                       region.validator_set[2]},
        .global = false,
    };
    reduce::validate_committee_qc(frozen_topology, frozen_proof, certificate);
    expect(accumulator.ingest(result, certificate), "regional result was not admitted");
  }
  const auto hierarchical = accumulator.finalize();
  expect(reduce::canonical_bytes(flat) == reduce::canonical_bytes(hierarchical) &&
             flat.result_id == hierarchical.result_id,
         "frozen-scale hierarchy differs from flat reduction");
  const auto& domain = frozen_topology.domains.front();
  const reduce::CommitteeQc global{
      .context = frozen_topology.context,
      .topology_id = frozen_topology.topology_id,
      .hierarchy_proof_instance_id = frozen_proof.hierarchy_proof_instance_id,
      .body_id = hierarchical.result_id,
      .domain_id = "qualification-domain",
      .region_id = {},
      .shard_id = "shard-000",
      .committee_epoch = frozen_topology.validator_epoch,
      .view = 0U,
      .quorum_threshold = 3U,
      .signer_ids = {domain.global_validator_set[0], domain.global_validator_set[1],
                     domain.global_validator_set[2]},
      .global = true,
  };
  reduce::validate_committee_qc(frozen_topology, frozen_proof, global);
  const auto assembly = reduce::assemble_complete(
      frozen_topology, frozen_proof, std::array{hierarchical}, std::array{global});
  return {flat.result_id, hierarchical.result_id, assembly.aggregate_id};
}

[[nodiscard]] std::string advance_current(const std::filesystem::path& root, const Chain& chain) {
  const runtime::PointerState initial{
      chain.pointer.expected_parent_checkpoint_id, chain.candidate.parent_optimizer_hash,
      content_id("feature010-no-apply-qc"), chain.pointer.context.height - 1U};
  {
    runtime::CurrentPointerStore store(root, initial);
    expect(store.advance(chain.pointer, chain.apply_qc) == runtime::PointerDisposition::advanced,
           "ApplyQC did not advance current");
    expect(store.advance(chain.pointer, chain.apply_qc) == runtime::PointerDisposition::replay,
           "ApplyQC replay was not exact");
  }
  runtime::CurrentPointerStore recovered(root, initial);
  expect(recovered.state().checkpoint_id == chain.apply_qc.next_model_hash &&
             recovered.state().optimizer_id == chain.apply_qc.next_optimizer_hash,
         "recovered current differs");
  return file_content_id(root / "current-pointer.wal");
}

void run_apply(const std::filesystem::path& aggregate_path,
               const std::filesystem::path& output_root) {
  const auto aggregate_raw = read_file(aggregate_path);
  const auto aggregate = parse_aggregator_receipt(aggregate_raw);
  expect(!std::filesystem::exists(output_root), "output directory already exists");
  std::filesystem::create_directories(output_root);
  const auto chain = build_chain();
  const auto hierarchy = execute_hierarchy(chain.contributions);
  const auto current_wal = advance_current(output_root / "current", chain);
  const auto input_id = certificates::content_id(chain.input_set);
  const auto plan_id = certificates::content_id(chain.robust_plan.plan);
  const auto shard_id = certificates::content_id(chain.shard);
  const auto root_id = certificates::content_id(chain.root);
  const auto candidate_id = certificates::content_id(chain.candidate);
  const auto apply_id = certificates::content_id(chain.apply_qc);
  expect(aggregate.validator_state_root == root_id &&
             aggregate.aggregator_state_root == root_id,
         "aggregate state root differs at apply boundary");
  expect(aggregate.validator_effect_root == candidate_id &&
             aggregate.aggregator_effect_root == apply_id,
         "aggregate effect root differs at apply boundary");
  std::size_t processed_q_values = 0U;
  for (const auto& contribution : chain.contributions) {
    processed_q_values += contribution.q_values.size();
  }
  expect(processed_q_values == kSyntheticContributionCount * kVectorWidth,
         "fixture reduction shape was not fully processed");
  const auto apply_state_root = chain.apply_qc.next_model_hash;
  const auto apply_effect_root = certificates::content_id(chain.pointer);
  const auto transcript_id = content_id(
      input_id + plan_id + shard_id + root_id + candidate_id + apply_id +
      hierarchy.assembly_id + current_wal + aggregate.validator_receipts_sha256 +
      apply_state_root + apply_effect_root);
  std::cout << "{\"aggregate_root_qc_id\":\"" << root_id
            << "\",\"aggregator_effect_root\":\"" << aggregate.aggregator_effect_root
            << "\",\"aggregator_state_root\":\"" << aggregate.aggregator_state_root
            << "\",\"apply_candidate_id\":\"" << candidate_id
            << "\",\"apply_effect_root\":\"" << apply_effect_root
            << "\",\"apply_qc_id\":\"" << apply_id << "\",\"apply_state_root\":\""
            << apply_state_root << "\",\"benchmark_definition_id\":\"" << kDefinitionId
            << "\",\"current_wal_sha256\":\"" << current_wal
            << "\",\"declared_B\":" << kDeclaredB << ",\"declared_H\":" << kDeclaredH
            << ",\"execution_class\":\"CONFORMANCE_SAFETY_FAULT_ONLY\""
            << ",\"feature010_go\":false,\"flat_result_id\":\"" << hierarchy.flat_id
            << "\",\"formal_semantics_id\":\"" << certificates::formal_semantics_id
            << "\",\"hierarchical_assembly_id\":\"" << hierarchy.assembly_id
            << "\",\"hierarchical_result_id\":\"" << hierarchy.hierarchy_id
            << "\",\"input_set_certificate_id\":\"" << input_id
            << "\",\"parameter_shard_qc_id\":\"" << shard_id
            << "\",\"primary_observation_count\":0,\"primary_parameter_shape_bound\":false"
            << ",\"processed_q_value_count\":"
            << processed_q_values << ",\"protocol_result_id\":\"" << transcript_id
            << "\",\"qualifying_gate_c\":false,\"qualifying_gate_d\":false"
            << ",\"reduction_vector_width\":" << kVectorWidth
            << ",\"robust_plan_id\":\"" << plan_id
            << "\",\"schema_version\":\"1.0.0\",\"status\":\"PASS\""
            << ",\"synthetic_contribution_count\":" << kSyntheticContributionCount
            << ",\"type_name\":\"FEATURE010_EXACTNESS_PROCESS_RESULT\""
            << ",\"validator_effect_root\":\"" << aggregate.validator_effect_root
            << "\",\"validator_process_count\":4,\"validator_receipts_sha256\":\""
            << aggregate.validator_receipts_sha256 << "\",\"validator_state_root\":\""
            << aggregate.validator_state_root << "\",\"work_ticket_budget_exercised\":false}\n";
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc == 3 && std::string_view(argv[1]) == "validator") {
      run_validator(argv[2]);
    } else if (argc == 6 && std::string_view(argv[1]) == "aggregator") {
      run_aggregator(std::span(argv + 2, 4U));
    } else if (argc == 4 && std::string_view(argv[1]) == "apply") {
      run_apply(argv[2], std::filesystem::absolute(argv[3]));
    } else {
      fail("usage: feature010_exactness_probe validator ID | aggregator V0 V1 V2 V3 | "
           "apply AGGREGATE OUTPUT_DIRECTORY");
    }
  } catch (const std::exception& error) {
    std::cerr << "feature010 exactness probe failed: " << error.what() << '\n';
    return 1;
  }
  return 0;
}
