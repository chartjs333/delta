#include <delta/core/canonical.hpp>
#include <delta/core/consensus.hpp>
#include <delta/core/protocol.hpp>
#include <delta/reduce/hierarchy.hpp>
#include <delta/runtime/runtime.hpp>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <regex>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace arithmetic = delta::core::arithmetic;
namespace canonical = delta::core::canonical;
namespace consensus = delta::core::consensus;
namespace protocol = delta::core::protocol;
namespace reduce = delta::reduce;
namespace runtime = delta::runtime;

namespace {

struct FanInMetrics {
  std::uint64_t flat_objects = 0U;
  std::uint64_t hierarchy_objects = 0U;
  std::uint64_t flat_payload_bytes = 0U;
  std::uint64_t hierarchy_payload_bytes = 0U;
};

FanInMetrics fan_in;

[[noreturn]] void fail(std::string message) { throw std::runtime_error(std::move(message)); }

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

template <typename Operation>
void expect_reduce_error(reduce::ErrorCode expected, Operation operation) {
  try {
    operation();
  } catch (const reduce::ReduceError& error) {
    expect(error.code() == expected, "unexpected hierarchy reduce error code");
    return;
  }
  fail("invalid hierarchy reduce operation was accepted");
}

template <typename Operation>
void expect_runtime_error(runtime::ErrorCode expected, Operation operation) {
  try {
    operation();
  } catch (const runtime::RuntimeError& error) {
    expect(error.code() == expected, "unexpected hierarchy runtime error code");
    return;
  }
  fail("hierarchy runtime failure was not reported");
}

template <typename Operation>
void expect_consensus_error(consensus::ErrorCode expected, Operation operation) {
  try {
    operation();
  } catch (const consensus::ConsensusError& error) {
    expect(error.code() == expected, "unexpected hierarchy vote-journal error code");
    return;
  }
  fail("conflicting hierarchy vote was accepted");
}

[[nodiscard]] std::string read_file(const std::filesystem::path& path) {
  std::ifstream input(path, std::ios::binary);
  expect(input.good(), "cannot open hierarchy reduce fixture");
  return {std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
}

[[nodiscard]] std::uint8_t hex_nibble(char value) {
  if (value >= '0' && value <= '9') {
    return static_cast<std::uint8_t>(value - '0');
  }
  if (value >= 'a' && value <= 'f') {
    return static_cast<std::uint8_t>(value - 'a' + 10);
  }
  fail("invalid lowercase hexadecimal fixture");
}

[[nodiscard]] canonical::Bytes decode_hex(std::string_view encoded) {
  expect((encoded.size() % 2U) == 0U, "odd hexadecimal fixture length");
  canonical::Bytes result;
  result.reserve(encoded.size() / 2U);
  for (std::size_t index = 0U; index < encoded.size(); index += 2U) {
    const auto value = static_cast<std::uint8_t>(
        static_cast<std::uint8_t>(hex_nibble(encoded[index]) << 4U) |
        hex_nibble(encoded[index + 1U]));
    result.push_back(static_cast<std::byte>(value));
  }
  return result;
}

struct Fixture {
  canonical::Bytes topology;
  canonical::Bytes proof;
};

[[nodiscard]] Fixture hierarchy_fixture() {
  const auto document = read_file(DELTA_HIERARCHY_GOLDEN_PATH);
  const std::regex topology_pattern(
      R"REGEX("topology":\{"bytes_hex":"([0-9a-f]+)")REGEX");
  const std::regex proof_pattern(
      R"REGEX("hierarchy_proof_instance":\{"bytes_hex":"([0-9a-f]+)")REGEX");
  std::smatch match;
  expect(std::regex_search(document, match, topology_pattern), "topology fixture is missing");
  auto topology = decode_hex(match[1].str());
  expect(std::regex_search(document, match, proof_pattern), "proof fixture is missing");
  return {std::move(topology), decode_hex(match[1].str())};
}

[[nodiscard]] canonical::Bytes core_golden(std::uint16_t type_code) {
  const auto document = read_file(DELTA_CORE_GOLDEN_PATH);
  const std::regex pattern(
      R"REGEX("envelope_hex":"([0-9a-f]+)","envelope_sha256":"[0-9a-f]+","type_code":([0-9]+))REGEX");
  for (auto cursor = std::sregex_iterator(document.begin(), document.end(), pattern);
       cursor != std::sregex_iterator(); ++cursor) {
    if (std::stoul((*cursor)[2].str()) == type_code) {
      return decode_hex((*cursor)[1].str());
    }
  }
  fail("core golden vector is absent");
}

[[nodiscard]] reduce::Context context() {
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

struct Contracts {
  reduce::Topology topology;
  reduce::HierarchyProofInstance proof;
};

[[nodiscard]] Contracts contracts() {
  const auto fixture = hierarchy_fixture();
  auto topology = reduce::parse_topology(fixture.topology, context());
  auto proof = reduce::parse_hierarchy_proof(fixture.proof, topology);
  return {std::move(topology), std::move(proof)};
}

[[nodiscard]] std::uint64_t ticket_number(std::string_view ticket_id) {
  return static_cast<std::uint64_t>(
      std::stoul(std::string(ticket_id.substr(ticket_id.size() - 2U))));
}

[[nodiscard]] std::string fixture_content_id(std::string_view domain, std::string_view value) {
  canonical::Bytes bytes;
  bytes.reserve(domain.size() + 1U + value.size());
  for (const char character : domain) {
    bytes.push_back(static_cast<std::byte>(character));
  }
  bytes.push_back(std::byte{0});
  for (const char character : value) {
    bytes.push_back(static_cast<std::byte>(character));
  }
  return "sha256:" + canonical::sha256_hex(bytes);
}

[[nodiscard]] std::vector<reduce::Contribution> contributions_for(
    const reduce::Topology& topology,
    std::string_view domain_id,
    std::string_view shard_id) {
  const auto& domain = reduce::require_domain(topology, domain_id);
  const auto& shard = reduce::require_shard(topology, shard_id);
  const auto width = static_cast<std::size_t>(shard.end_element - shard.start_element);
  const auto shard_ordinal = shard_id == "parameter-000" ? 0U : 1U;
  std::vector<reduce::Contribution> result;
  for (const auto& ticket : domain.tickets) {
    const auto number = ticket_number(ticket);
    std::vector<std::int16_t> values;
    values.reserve(width);
    const auto base = static_cast<std::int64_t>(number * 7U + shard_ordinal * 3U);
    values = {
        static_cast<std::int16_t>(base + 1), static_cast<std::int16_t>(-(base + 2)),
        static_cast<std::int16_t>(base + 3), static_cast<std::int16_t>(-(base + 4))};
    expect(values.size() == width, "fixture q vector width changed");
    const auto worker_id = fixture_content_id(
        "deltareduce.006.worker-q.v1",
        std::string(domain_id) + ":" + ticket + ":" + std::string(shard_id));
    result.push_back(reduce::Contribution{
        topology.context,
        std::string(domain_id),
        std::string(shard_id),
        ticket,
        worker_id,
        static_cast<std::int64_t>(number),
        1U,
        std::move(values),
    });
  }
  return result;
}

[[nodiscard]] std::vector<reduce::Contribution> region_input(
    const reduce::Region& region,
    std::span<const reduce::Contribution> input) {
  std::vector<reduce::Contribution> result;
  for (const auto& contribution : input) {
    if (std::binary_search(region.tickets.begin(), region.tickets.end(), contribution.ticket_id)) {
      result.push_back(contribution);
    }
  }
  std::reverse(result.begin(), result.end());
  return result;
}

constexpr std::array<std::string_view, 12> expected_regional_ids = {
    "sha256:9c236998c942ff14cda1f6009966b9bafed8d12ec24d410e351c814afbce5d69",
    "sha256:4adaa36a584e0e2f26c0f9cb8cdbd70f0f84cb55eb647013457bd22a18ff4d09",
    "sha256:70f431be8fd2417668d647ca5c5c755de0c3057799df1c9fe6e65a9696c07128",
    "sha256:4000f05fbd72b76e025f6c19bfd4744549ea813d254347206043383e057a00e8",
    "sha256:dba0653e051fce5b4d28b458b89bc0a07f0ed2f625d28a995178dd1c82f7dced",
    "sha256:e6505fe3b68cb018aa50afb44eb7e59ba39452b84b51600435772ed2cc609d0b",
    "sha256:89e67660c24189d81ed762f49bfba022c219c538ded9d1d94afdc98e7a603a49",
    "sha256:7da5f79c703f1d4b92d665a8b0cd2a29bf3cdf92c0e10dac91ef252a067e5c9e",
    "sha256:ace868228cc2972e83179ec2a457c8d416612f578c695b68c00f637bfe8edebe",
    "sha256:4696894292b4ad0426ffe6d342127068e22039ddb492b415a6407551ae1760cb",
    "sha256:57315478f8effc6c6f7e1cb5255b6b4ce9642856f41e68ea67e2d8c55cba79bb",
    "sha256:933de7cf7a12311805205e720c02e016fe7e592396f5ef013c7e1065b56f1a4d",
};

constexpr std::array<std::string_view, 4> expected_global_ids = {
    "sha256:f500141867f7bed83184c6fe14d3433584cb837f94e385367a70ab3078979373",
    "sha256:b0d372b6b01e0984a2e7a8c0b732a8e648f12e31a9217648f3b59decf1af25e3",
    "sha256:3b269c00dedea9a3c2adee40413637b16d42da2a344b962737a504ecf4bc50e4",
    "sha256:9cc7ca534c0df60ef96a6325fb5de0f8769e33225d5b1842f06ee8975c7b99b0",
};

constexpr std::array<std::string_view, 12> expected_regional_qc_ids = {
    "sha256:f174b7806c62a26abed1a92952719d4de0db71e956f7c188fc72a968c8faa868",
    "sha256:896794300ee4190f7b131c2c79693dcb47b0d1edbe048113e4f42850b6c27091",
    "sha256:8ea3ebdbcb415c62fffe6b478541d611d188917531012fadea621534213e09e7",
    "sha256:51402856d1e761c3719ffb1b527e2ab9c99bcc588e5e810e13cfc90a32427a64",
    "sha256:e58d22c9a9f693005caa40e1aa65a94f3213a8418d25d80e6433cda40f90d96e",
    "sha256:75313c628385b63d634116f54d12529a9aafba97a2f8618482eb33f94b811b53",
    "sha256:e99578d050b8b785c2fd6d23f6d0749ea6778d55d845b593cf2cacbc8aba7a39",
    "sha256:a4e94928c64a9a54f7425509fbcdf9a2e1c8d46b29a8d8b56077804a8a89243d",
    "sha256:493942a9143e0ef6f37461d6779c6e6cfdaa4ad87d2425b25c5c17b16ae6f575",
    "sha256:8328303d283535314842c89b8f188644af9af3d068e33c7706f9851e2ce36678",
    "sha256:35d8a31383f97961468174b7cc9840bf50102423995a1308911d1965204fd533",
    "sha256:2b979fe34615efc99db6bcdef8f82c32d562ddb79b8b675758dedb24a0b3c95f",
};

constexpr std::array<std::string_view, 4> expected_global_qc_ids = {
    "sha256:2a89c355a45a7f3273544a41789777e9f3be5ffbd83e5ae89218f758ba7b9254",
    "sha256:265cb03a87da5c76390a2fd1b851c1f86e7cd611d232402b2a80ffa30751383c",
    "sha256:9b6a67523aae9e7859e30d1b2f752c004e41c5c2fa1c1f025bf8074401ca8951",
    "sha256:90778ce7747a6a47d054046e8b992f10c167c9f47156a276f126cd7fe1c76b94",
};

struct HierarchyResults {
  std::vector<reduce::RegionalResult> regionals;
  std::vector<reduce::CommitteeQc> regional_certificates;
  std::vector<reduce::GlobalResult> globals;
  std::vector<reduce::CommitteeQc> global_certificates;
};

[[nodiscard]] HierarchyResults test_hierarchy_equals_flat(
    const reduce::Topology& topology,
    const reduce::HierarchyProofInstance& proof) {
  HierarchyResults output;
  std::size_t regional_index = 0U;
  std::size_t global_index = 0U;
  for (const auto& domain : topology.domains) {
    for (const auto& shard : topology.shards) {
      auto all = contributions_for(topology, domain.domain_id, shard.shard_id);
      fan_in.flat_objects += all.size();
      for (const auto& contribution : all) {
        fan_in.flat_payload_bytes += reduce::canonical_bytes(contribution).size();
      }
      std::reverse(all.begin(), all.end());
      reduce::GlobalAccumulator accumulator(topology, proof, domain.domain_id, shard.shard_id);
      std::vector<reduce::RegionalResult> regional;
      for (const auto& region : domain.regions) {
        const auto input = region_input(region, all);
        regional.push_back(reduce::reduce_region(
            topology, proof, domain.domain_id, region.region_id, shard.shard_id, input));
        expect(regional.back().result_id == expected_regional_ids[regional_index],
               "native regional canonical JSON differs from cross-language fixture");
        const reduce::CommitteeQc regional_certificate{
            topology.context,
            topology.topology_id,
            proof.hierarchy_proof_instance_id,
            regional.back().result_id,
            domain.domain_id,
            region.region_id,
            shard.shard_id,
            topology.validator_epoch,
            0U,
            3U,
            {region.validator_set[0], region.validator_set[1], region.validator_set[2]},
            false,
        };
        reduce::validate_committee_qc(topology, proof, regional_certificate);
        expect(reduce::committee_qc_id(regional_certificate) ==
                   expected_regional_qc_ids[regional_index],
               "native regional QC canonical JSON differs from cross-language fixture");
        output.regionals.push_back(regional.back());
        output.regional_certificates.push_back(regional_certificate);
        ++regional_index;
      }
      fan_in.hierarchy_objects += regional.size();
      for (const auto& result : regional) {
        fan_in.hierarchy_payload_bytes += reduce::canonical_bytes(result).size();
      }
      std::reverse(regional.begin(), regional.end());
      auto regional_certificates = std::vector<reduce::CommitteeQc>{};
      regional_certificates.reserve(regional.size());
      for (const auto& result : regional) {
        const auto& region = reduce::require_region(domain, result.region_id);
        regional_certificates.push_back(reduce::CommitteeQc{
            topology.context,
            topology.topology_id,
            proof.hierarchy_proof_instance_id,
            result.result_id,
            domain.domain_id,
            result.region_id,
            shard.shard_id,
            topology.validator_epoch,
            0U,
            3U,
            {region.validator_set[0], region.validator_set[1], region.validator_set[2]},
            false,
        });
        expect(accumulator.ingest(result, regional_certificates.back()),
               "first finalized regional result was classified as replay");
      }
      expect(!accumulator.ingest(regional.front(), regional_certificates.front()),
             "exact finalized regional replay was not idempotent");
      const auto hierarchical = accumulator.finalize();
      const auto flat = reduce::reduce_flat(
          topology, proof, domain.domain_id, shard.shard_id, all);
      expect(reduce::canonical_bytes(hierarchical) == reduce::canonical_bytes(flat) &&
                 hierarchical.result_id == flat.result_id,
             "hierarchical integer result differs byte-for-byte from flat oracle");
      expect(hierarchical.result_id == expected_global_ids[global_index],
             "native global canonical JSON differs from cross-language fixture");
      reduce::CommitteeQc global_certificate{
          topology.context,
          topology.topology_id,
          proof.hierarchy_proof_instance_id,
          hierarchical.result_id,
          domain.domain_id,
          {},
          shard.shard_id,
          topology.validator_epoch,
          0U,
          3U,
          {domain.global_validator_set[0], domain.global_validator_set[1],
           domain.global_validator_set[2]},
          true,
      };
      reduce::validate_committee_qc(topology, proof, global_certificate);
      expect(reduce::committee_qc_id(global_certificate) == expected_global_qc_ids[global_index],
             "native global QC canonical JSON differs from cross-language fixture");
      output.globals.push_back(hierarchical);
      output.global_certificates.push_back(std::move(global_certificate));
      ++global_index;

      auto conflict = regional.front();
      conflict.numerator[0] = arithmetic::checked_add(
          conflict.numerator[0], arithmetic::Int128::from_i64(1));
      conflict.result_id = reduce::regional_result_id(conflict);
      expect_reduce_error(reduce::ErrorCode::result_conflict, [&] {
        auto conflict_certificate = regional_certificates.front();
        conflict_certificate.body_id = conflict.result_id;
        static_cast<void>(accumulator.ingest(conflict, conflict_certificate));
      });

      reduce::GlobalAccumulator partial(topology, proof, domain.domain_id, shard.shard_id);
      expect(partial.ingest(regional.front(), regional_certificates.front()),
             "partial global intake rejected its first finalized result");
      expect_reduce_error(reduce::ErrorCode::required_result_missing, [&] {
        static_cast<void>(partial.finalize());
      });

      auto insufficient_qc = regional_certificates.back();
      insufficient_qc.signer_ids.pop_back();
      expect_reduce_error(reduce::ErrorCode::quorum_invalid, [&] {
        reduce::GlobalAccumulator rejected(topology, proof, domain.domain_id, shard.shard_id);
        static_cast<void>(rejected.ingest(regional.back(), insufficient_qc));
      });
      auto wrong_body_qc = regional_certificates.back();
      wrong_body_qc.body_id = regional.front().result_id;
      expect_reduce_error(reduce::ErrorCode::context_mismatch, [&] {
        reduce::GlobalAccumulator rejected(topology, proof, domain.domain_id, shard.shard_id);
        static_cast<void>(rejected.ingest(regional.back(), wrong_body_qc));
      });
      auto mixed_view_qc = regional_certificates.back();
      ++mixed_view_qc.view;
      expect_reduce_error(reduce::ErrorCode::context_mismatch, [&] {
        static_cast<void>(accumulator.ingest(regional.back(), mixed_view_qc));
      });

      auto missing = all;
      missing.pop_back();
      expect_reduce_error(reduce::ErrorCode::partition_invalid, [&] {
        static_cast<void>(reduce::reduce_flat(
            topology, proof, domain.domain_id, shard.shard_id, missing));
      });
      auto wrong_context = all;
      wrong_context.front().context.frozen_input_root =
          "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee";
      expect_reduce_error(reduce::ErrorCode::context_mismatch, [&] {
        static_cast<void>(reduce::reduce_flat(
            topology, proof, domain.domain_id, shard.shard_id, wrong_context));
      });
    }
  }
  expect(regional_index == expected_regional_ids.size() &&
             global_index == expected_global_ids.size(),
         "cross-language hierarchy result matrix is incomplete");
  return output;
}

void test_complete_assembly(
    const reduce::Topology& topology,
    const reduce::HierarchyProofInstance& proof,
    const HierarchyResults& hierarchy) {
  auto certificates = hierarchy.global_certificates;
  std::reverse(certificates.begin(), certificates.end());
  certificates.push_back(certificates.front());
  auto shuffled = hierarchy.globals;
  std::reverse(shuffled.begin(), shuffled.end());
  shuffled.push_back(shuffled.front());
  const auto assembly = reduce::assemble_complete(topology, proof, shuffled, certificates);
  expect(assembly.results.size() == topology.domains.size() * topology.shards.size() &&
             assembly.certificates.size() == assembly.results.size() &&
             assembly.aggregate_id ==
                 "sha256:f247578ef2b8e76b27274fc95f92fc50a1eb8586b4052952075a0fddfd4bdd29",
         "complete hierarchy assembly lost exact canonical coverage");
  auto incomplete = hierarchy.globals;
  incomplete.pop_back();
  expect_reduce_error(reduce::ErrorCode::assembly_incomplete, [&] {
    static_cast<void>(reduce::assemble_complete(topology, proof, incomplete, certificates));
  });
  auto missing_certificate = certificates;
  missing_certificate.erase(missing_certificate.begin(), missing_certificate.begin() + 2);
  expect_reduce_error(reduce::ErrorCode::assembly_incomplete, [&] {
    static_cast<void>(
        reduce::assemble_complete(topology, proof, hierarchy.globals, missing_certificate));
  });
  auto conflict = hierarchy.globals;
  auto changed = conflict.front();
  changed.numerator[0] = arithmetic::checked_add(
      changed.numerator[0], arithmetic::Int128::from_i64(1));
  changed.result_id = reduce::global_result_id(changed);
  conflict.push_back(std::move(changed));
  expect_reduce_error(reduce::ErrorCode::result_conflict, [&] {
    static_cast<void>(reduce::assemble_complete(topology, proof, conflict, certificates));
  });
  auto mixed_view_certificates = hierarchy.global_certificates;
  ++mixed_view_certificates.back().view;
  expect_reduce_error(reduce::ErrorCode::context_mismatch, [&] {
    static_cast<void>(reduce::assemble_complete(
        topology, proof, hierarchy.globals, mixed_view_certificates));
  });
  auto unsafe_results = hierarchy.globals;
  unsafe_results.front().coefficient_numerator_sum = arithmetic::checked_add(
      proof.final_abs_bound, arithmetic::Int128::from_i64(1));
  unsafe_results.front().result_id = reduce::global_result_id(unsafe_results.front());
  auto unsafe_certificates = hierarchy.global_certificates;
  unsafe_certificates.front().body_id = unsafe_results.front().result_id;
  expect_reduce_error(reduce::ErrorCode::proof_invalid, [&] {
    static_cast<void>(reduce::assemble_complete(
        topology, proof, unsafe_results, unsafe_certificates));
  });
}

[[nodiscard]] std::filesystem::path case_directory(std::string_view name) {
  auto path = std::filesystem::temp_directory_path() / "delta-hierarchy-006-tests" / name;
  std::error_code error;
  std::filesystem::remove_all(path, error);
  expect(!error, "cannot clean hierarchy runtime test directory");
  std::filesystem::create_directories(path, error);
  expect(!error, "cannot create hierarchy runtime test directory");
  return path;
}

struct RecoveryEvidence {
  std::string global_vote_id;
  std::string regional_vote_id;
  std::size_t recovered_vote_count;
};

[[nodiscard]] RecoveryEvidence test_quorum_and_durable_vote(
    const reduce::Topology& topology,
    const reduce::HierarchyProofInstance& proof,
    const reduce::GlobalResult& body) {
  const auto& domain = reduce::require_domain(topology, body.domain_id);
  reduce::CommitteeQc intent{
      topology.context,
      topology.topology_id,
      proof.hierarchy_proof_instance_id,
      body.result_id,
      body.domain_id,
      {},
      body.shard_id,
      topology.validator_epoch,
      0U,
      3U,
      {domain.global_validator_set[0], domain.global_validator_set[1],
       domain.global_validator_set[2]},
      true,
  };
  reduce::validate_committee_qc(topology, proof, intent);
  auto insufficient = intent;
  insufficient.signer_ids.pop_back();
  expect_reduce_error(reduce::ErrorCode::quorum_invalid, [&] {
    reduce::validate_committee_qc(topology, proof, insufficient);
  });
  auto wrong_epoch = intent;
  ++wrong_epoch.committee_epoch;
  expect_reduce_error(reduce::ErrorCode::context_mismatch, [&] {
    reduce::validate_committee_qc(topology, proof, wrong_epoch);
  });

  auto duplicate_signer = intent;
  duplicate_signer.signer_ids[1] = duplicate_signer.signer_ids[0];
  expect_reduce_error(reduce::ErrorCode::quorum_invalid, [&] {
    reduce::validate_committee_qc(topology, proof, duplicate_signer);
  });

  const auto vote = reduce::make_committee_vote(
      topology, proof, intent, intent.signer_ids.front(),
      "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee", 1U);
  const auto vote_bytes = protocol::encode(vote);
  const auto& region = domain.regions.front();
  const auto all = contributions_for(topology, body.domain_id, body.shard_id);
  const auto regional_body = reduce::reduce_region(
      topology, proof, body.domain_id, region.region_id, body.shard_id,
      region_input(region, all));
  reduce::CommitteeQc regional_intent{
      topology.context,
      topology.topology_id,
      proof.hierarchy_proof_instance_id,
      regional_body.result_id,
      body.domain_id,
      region.region_id,
      body.shard_id,
      topology.validator_epoch,
      0U,
      3U,
      {region.validator_set[0], region.validator_set[1], region.validator_set[2]},
      false,
  };
  reduce::validate_committee_qc(topology, proof, regional_intent);
  const auto regional_vote_bytes = protocol::encode(reduce::make_committee_vote(
      topology, proof, regional_intent, regional_intent.signer_ids.front(),
      "sha256:abababababababababababababababababababababababababababababababab", 2U));
  const auto directory = case_directory("vote-recovery");
  runtime::VoteReceipt first;
  runtime::VoteReceipt regional_first;
  {
    runtime::Runtime durable({directory, core_golden(5U), 8U});
    first = durable.record_vote(vote_bytes);
    regional_first = durable.record_vote(regional_vote_bytes);
    expect(!first.replay && std::filesystem::file_size(directory / "runtime.wal") > 0U,
           "committee vote became visible before durable WAL persistence");
    expect(!regional_first.replay, "regional committee vote was classified as replay");
  }
  {
    runtime::Runtime recovered({directory, core_golden(5U), 8U});
    expect(recovered.recovered_vote_count() == 2U,
           "regional/global vote journals were not recovered before admission");
    const auto replay = recovered.record_vote(vote_bytes);
    const auto regional_replay = recovered.record_vote(regional_vote_bytes);
    expect(replay.replay && replay.vote_id == first.vote_id,
           "durable committee vote replay changed identity");
    expect(regional_replay.replay && regional_replay.vote_id == regional_first.vote_id,
           "durable regional vote replay changed identity");
    auto conflict = vote;
    conflict.body_hash =
        "sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff";
    expect_consensus_error(consensus::ErrorCode::conflicting_vote, [&] {
      static_cast<void>(recovered.record_vote(protocol::encode(conflict)));
    });
  }

  const auto crash_directory = case_directory("vote-crash-after-durability");
  {
    runtime::Runtime crashing({crash_directory, core_golden(5U), 8U});
    expect_runtime_error(runtime::ErrorCode::simulated_crash, [&] {
      static_cast<void>(crashing.record_vote(
          vote_bytes, runtime::CrashPoint::after_durability_before_commit));
    });
  }
  {
    runtime::Runtime recovered({crash_directory, core_golden(5U), 8U});
    expect(recovered.recovered_vote_count() == 1U,
           "durable committee vote was lost after proposer crash");
  }
  return {first.vote_id, regional_first.vote_id, 2U};
}

void test_artifact_repair_and_quorum_loss(
    const reduce::Topology& topology,
    const reduce::HierarchyProofInstance& proof,
    const HierarchyResults& hierarchy) {
  const auto& domain = topology.domains.front();
  const auto& region = domain.regions.front();
  const auto& shard = topology.shards.front();
  const auto all = contributions_for(topology, domain.domain_id, shard.shard_id);
  const auto exact_input = region_input(region, all);
  auto unavailable = exact_input;
  unavailable.pop_back();
  expect_reduce_error(reduce::ErrorCode::partition_invalid, [&] {
    static_cast<void>(reduce::reduce_region(
        topology, proof, domain.domain_id, region.region_id, shard.shard_id, unavailable));
  });
  const auto repaired = reduce::reduce_region(
      topology, proof, domain.domain_id, region.region_id, shard.shard_id, exact_input);
  expect(repaired.result_id == hierarchy.regionals.front().result_id,
         "exact-ID artifact repair changed the regional result");

  auto quorum_loss = hierarchy.regional_certificates.front();
  quorum_loss.signer_ids.resize(2U);
  expect_reduce_error(reduce::ErrorCode::quorum_invalid, [&] {
    reduce::validate_committee_qc(topology, proof, quorum_loss);
  });
  auto absent_proposer = hierarchy.global_certificates.front();
  absent_proposer.signer_ids.clear();
  expect_reduce_error(reduce::ErrorCode::quorum_invalid, [&] {
    reduce::validate_committee_qc(topology, proof, absent_proposer);
  });
}

[[nodiscard]] std::string quote(std::string_view value) {
  return '"' + std::string(value) + '"';
}

void write_trace(const std::filesystem::path& path, const std::string& value) {
  std::ofstream output(path, std::ios::binary | std::ios::trunc);
  expect(output.good(), "cannot create hierarchy refinement trace");
  output << value << '\n';
  output.close();
  expect(output.good(), "cannot persist hierarchy refinement trace");
}

void export_refinement_traces(
    const std::filesystem::path& directory,
    const reduce::Topology& topology,
    const reduce::HierarchyProofInstance& proof,
    const HierarchyResults& hierarchy,
    const reduce::Assembly& assembly,
    const RecoveryEvidence& recovery) {
  std::error_code error;
  std::filesystem::create_directories(directory, error);
  expect(!error, "cannot create hierarchy refinement trace directory");
  constexpr auto formal_id =
      "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
  std::string events = "[";
  for (std::size_t index = 0U; index < hierarchy.regionals.size(); ++index) {
    if (index != 0U) {
      events += ',';
    }
    const auto& result = hierarchy.regionals[index];
    events += "{\"action\":\"REGIONAL_RESULT_FINALIZED\",\"body_id\":" +
              quote(result.result_id) + ",\"certificate_id\":" +
              quote(reduce::committee_qc_id(hierarchy.regional_certificates[index])) +
              ",\"domain_id\":" + quote(result.domain_id) + ",\"region_id\":" +
              quote(result.region_id) + ",\"shard_id\":" + quote(result.shard_id) +
              ",\"view\":0}";
  }
  for (std::size_t index = 0U; index < hierarchy.globals.size(); ++index) {
    events += ",{\"action\":\"GLOBAL_PARAMETER_RESULT_FINALIZED\",\"body_id\":" +
              quote(hierarchy.globals[index].result_id) + ",\"certificate_id\":" +
              quote(reduce::committee_qc_id(hierarchy.global_certificates[index])) +
              ",\"domain_id\":" + quote(hierarchy.globals[index].domain_id) +
              ",\"shard_id\":" + quote(hierarchy.globals[index].shard_id) +
              ",\"view\":0}";
  }
  events += ",{\"action\":\"HIERARCHY_ASSEMBLED\",\"aggregate_id\":" +
            quote(assembly.aggregate_id) + "}]";
  write_trace(
      directory / "legal-hierarchy-flat.json",
      "{\"abstraction_version\":\"1.0.0\",\"aggregate_id\":" +
          quote(assembly.aggregate_id) + ",\"current_checkpoint_advanced\":false,\"events\":" +
          events + ",\"flat_metrics\":{\"objects\":" + std::to_string(fan_in.flat_objects) +
          ",\"payload_bytes\":" + std::to_string(fan_in.flat_payload_bytes) +
          "},\"formal_semantics_id\":" + quote(formal_id) +
          ",\"hierarchy_metrics\":{\"objects\":" +
          std::to_string(fan_in.hierarchy_objects) + ",\"payload_bytes\":" +
          std::to_string(fan_in.hierarchy_payload_bytes) +
          "},\"hierarchy_proof_instance_id\":" + quote(proof.hierarchy_proof_instance_id) +
          ",\"schema_version\":\"1.0.0\",\"terminal_outcome\":\"IN_PROGRESS\",\"topology_id\":" +
          quote(topology.topology_id) + ",\"trace_id\":\"TRACE-NATIVE-006-HIERARCHY-FLAT\"}");
  write_trace(
      directory / "legal-crash-recovery.json",
      "{\"abstraction_version\":\"1.0.0\",\"events\":[{\"action\":\"PERSIST_VOTE\",\"vote_id\":" +
          quote(recovery.regional_vote_id) +
          "},{\"action\":\"PERSIST_VOTE\",\"vote_id\":" + quote(recovery.global_vote_id) +
          "},{\"action\":\"CRASH\"},{\"action\":\"RESTART\"},{\"action\":\"RECOVER_JOURNAL\",\"vote_count\":" +
          std::to_string(recovery.recovered_vote_count) +
          "},{\"action\":\"REPLAY_VOTE\",\"same_identity\":true}],\"formal_semantics_id\":" +
          quote(formal_id) +
          ",\"schema_version\":\"1.0.0\",\"terminal_outcome\":\"IN_PROGRESS\",\"trace_id\":\"TRACE-NATIVE-006-CRASH-RECOVERY\"}");
  const auto illegal = [&](std::string_view name, std::string_view trace_id,
                           std::string_view error_code, std::string_view outcome) {
    write_trace(
        directory / std::string(name),
        "{\"abstraction_version\":\"1.0.0\",\"accepted\":false,\"error_code\":" +
            quote(error_code) + ",\"formal_semantics_id\":" + quote(formal_id) +
            ",\"schema_version\":\"1.0.0\",\"terminal_outcome\":" + quote(outcome) +
            ",\"trace_id\":" + quote(trace_id) + "}");
  };
  illegal("illegal-artifact-loss.json", "TRACE-NATIVE-006-ARTIFACT-LOSS",
          "EXACT_ARTIFACT_REQUIRED", "BLOCKED");
  illegal("illegal-mixed-view.json", "TRACE-NATIVE-006-MIXED-VIEW",
          "MIXED_VIEW_REJECTED", "BLOCKED");
  illegal("illegal-partial-coverage.json", "TRACE-NATIVE-006-PARTIAL-COVERAGE",
          "REQUIRED_MATRIX_INCOMPLETE", "BLOCKED");
  illegal("illegal-quorum-loss.json", "TRACE-NATIVE-006-QUORUM-LOSS",
          "QC_QUORUM_MISSING", "BLOCKED");
}

}  // namespace

int main(int argc, char** argv) {
  try {
    expect(argc == 1 || argc == 2, "usage: hierarchy_reduce_test [trace-directory]");
    const auto contract = contracts();
    expect(reduce::routing_projection_id(contract.topology) ==
               "sha256:22caad4705d05abcdb56958095bacd1686dc37d9d1b8996f3bf2f312f79a3472",
           "native routing projection identity changed");
    const auto hierarchy = test_hierarchy_equals_flat(contract.topology, contract.proof);
    expect(fan_in.flat_objects == 22U && fan_in.hierarchy_objects == 12U,
           "cross-region fan-in object measurement changed");
    const auto assembly = reduce::assemble_complete(
        contract.topology, contract.proof, hierarchy.globals, hierarchy.global_certificates);
    test_complete_assembly(contract.topology, contract.proof, hierarchy);
    const auto recovery = test_quorum_and_durable_vote(
        contract.topology, contract.proof, hierarchy.globals.front());
    test_artifact_repair_and_quorum_loss(contract.topology, contract.proof, hierarchy);
    if (argc == 2) {
      export_refinement_traces(
          std::filesystem::path(argv[1]), contract.topology, contract.proof, hierarchy, assembly,
          recovery);
    }
  } catch (const std::exception& error) {
    std::cerr << "delta hierarchy reduce test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "delta hierarchy reduce tests passed: flat_objects=" << fan_in.flat_objects
            << " hierarchy_objects=" << fan_in.hierarchy_objects
            << " flat_payload_bytes=" << fan_in.flat_payload_bytes
            << " hierarchy_payload_bytes=" << fan_in.hierarchy_payload_bytes << '\n';
  return 0;
}
