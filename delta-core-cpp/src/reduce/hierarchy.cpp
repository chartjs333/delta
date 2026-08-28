#include <delta/reduce/hierarchy.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <numeric>
#include <set>
#include <span>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace delta::reduce {
namespace {

using Int128 = delta::core::arithmetic::Int128;
using Bytes = delta::core::canonical::Bytes;

[[noreturn]] void reject(ErrorCode code, std::string message) {
  throw ReduceError(code, std::move(message));
}

void require(bool condition, ErrorCode code, const char* message) {
  if (!condition) {
    reject(code, message);
  }
}

[[nodiscard]] bool content_id_valid(std::string_view value) noexcept {
  if (value.size() != 71U || !value.starts_with("sha256:")) {
    return false;
  }
  return std::all_of(value.begin() + 7, value.end(), [](char character) {
    return (character >= '0' && character <= '9') ||
           (character >= 'a' && character <= 'f');
  });
}

void append_u32(Bytes& output, std::uint32_t value) {
  for (int shift = 24; shift >= 0; shift -= 8) {
    output.push_back(static_cast<std::byte>((value >> static_cast<unsigned>(shift)) & 0xffU));
  }
}

void append_u64(Bytes& output, std::uint64_t value) {
  for (int shift = 56; shift >= 0; shift -= 8) {
    output.push_back(static_cast<std::byte>((value >> static_cast<unsigned>(shift)) & 0xffU));
  }
}

void append_string(Bytes& output, std::string_view value) {
  require(value.size() <= std::numeric_limits<std::uint32_t>::max(),
          ErrorCode::contribution_invalid, "canonical hierarchy string is too large");
  append_u32(output, static_cast<std::uint32_t>(value.size()));
  for (const char character : value) {
    require(character >= 0x20 && character <= 0x7e, ErrorCode::identifier_invalid,
            "canonical hierarchy string is outside ASCII");
    output.push_back(static_cast<std::byte>(character));
  }
}

void append_int128(Bytes& output, Int128 value) {
  append_u64(output, value.high);
  append_u64(output, value.low);
}

void append_context(Bytes& output, const Context& context) {
  append_string(output, context.accumulator_proof_instance_id);
  append_string(output, context.coefficient_plan_root);
  append_string(output, context.fixedpoint_config_id);
  append_string(output, context.formal_semantics_id);
  append_string(output, context.frozen_input_root);
  append_string(output, context.parent_checkpoint_id);
  append_string(output, context.profile_id);
  append_string(output, context.round_config_id);
  append_string(output, context.scale_table_id);
  append_string(output, context.shard_plan_id);
}

[[nodiscard]] std::string content_id(std::string_view domain, std::span<const std::byte> bytes) {
  Bytes input;
  input.reserve(domain.size() + 1U + bytes.size());
  for (const char character : domain) {
    input.push_back(static_cast<std::byte>(character));
  }
  input.push_back(std::byte{0});
  input.insert(input.end(), bytes.begin(), bytes.end());
  return "sha256:" + delta::core::canonical::sha256_hex(input);
}

[[nodiscard]] std::string json_string(std::string_view value) {
  require(std::all_of(value.begin(), value.end(), [](char character) {
            return character >= 0x20 && character <= 0x7e && character != '"' &&
                   character != '\\';
          }),
          ErrorCode::identifier_invalid, "canonical hierarchy JSON string is invalid");
  return "\"" + std::string(value) + "\"";
}

[[nodiscard]] Int128 absolute(Int128 value);

[[nodiscard]] std::string unsigned_decimal(Int128 value) {
  require(!value.negative(), ErrorCode::contribution_invalid,
          "unsigned decimal received a negative value");
  if (value == Int128::from_u64(0U)) {
    return "0";
  }
  std::string reversed;
  while (value != Int128::from_u64(0U)) {
    const auto quotient_high = value.high / 10U;
    std::uint64_t remainder = value.high % 10U;
    std::uint64_t quotient_low = 0U;
    for (int bit = 63; bit >= 0; --bit) {
      remainder = (remainder * 2U) + ((value.low >> static_cast<unsigned>(bit)) & 1U);
      if (remainder >= 10U) {
        remainder -= 10U;
        quotient_low |= UINT64_C(1) << static_cast<unsigned>(bit);
      }
    }
    reversed.push_back(static_cast<char>('0' + remainder));
    value = Int128::from_bits(quotient_high, quotient_low);
  }
  return {reversed.rbegin(), reversed.rend()};
}

[[nodiscard]] std::string decimal(Int128 value) {
  return value.negative() ? "-" + unsigned_decimal(absolute(value)) : unsigned_decimal(value);
}

[[nodiscard]] Bytes json_bytes(std::string value) {
  const auto bytes = std::as_bytes(std::span(value.data(), value.size()));
  return {bytes.begin(), bytes.end()};
}

[[nodiscard]] std::string string_array_json(std::span<const std::string> values) {
  std::string result = "[";
  for (std::size_t index = 0U; index < values.size(); ++index) {
    if (index != 0U) {
      result += ',';
    }
    result += json_string(values[index]);
  }
  return result + ']';
}

[[nodiscard]] std::string numerator_json(std::span<const Int128> values) {
  std::string result = "[";
  for (std::size_t index = 0U; index < values.size(); ++index) {
    if (index != 0U) {
      result += ',';
    }
    result += json_string(decimal(values[index]));
  }
  return result + ']';
}

[[nodiscard]] std::string q_values_json(std::span<const std::int16_t> values) {
  std::string result = "[";
  for (std::size_t index = 0U; index < values.size(); ++index) {
    if (index != 0U) {
      result += ',';
    }
    result += std::to_string(values[index]);
  }
  return result + ']';
}

[[nodiscard]] std::string regional_input_json(
    const Topology& topology,
    const HierarchyProofInstance& proof,
    std::string_view domain_id,
    std::string_view region_id,
    std::string_view shard_id,
    std::span<const Contribution> contributions) {
  std::string contribution_json = "[";
  for (std::size_t index = 0U; index < contributions.size(); ++index) {
    if (index != 0U) {
      contribution_json += ',';
    }
    const auto& item = contributions[index];
    contribution_json +=
        "{\"coefficient_denominator\":" + json_string(std::to_string(item.coefficient_denominator)) +
        ",\"coefficient_numerator\":" + json_string(std::to_string(item.coefficient)) +
        ",\"q_values\":" + q_values_json(item.q_values) +
        ",\"ticket_id\":" + json_string(item.ticket_id) +
        ",\"worker_shard_id\":" + json_string(item.worker_shard_id) + "}";
  }
  contribution_json += ']';
  const auto& context = topology.context;
  return "{\"accumulator_proof_instance_id\":" +
         json_string(context.accumulator_proof_instance_id) +
         ",\"coefficient_plan_root\":" + json_string(context.coefficient_plan_root) +
         ",\"committee_epoch\":" + std::to_string(topology.validator_epoch) +
         ",\"contributions\":" + contribution_json +
         ",\"domain_id\":" + json_string(domain_id) +
         ",\"fixedpoint_config_id\":" + json_string(context.fixedpoint_config_id) +
         ",\"formal_semantics_id\":" + json_string(context.formal_semantics_id) +
         ",\"frozen_input_root\":" + json_string(context.frozen_input_root) +
         ",\"hierarchy_proof_instance_id\":" +
         json_string(proof.hierarchy_proof_instance_id) +
         ",\"parent_checkpoint_id\":" + json_string(context.parent_checkpoint_id) +
         ",\"profile_id\":" + json_string(context.profile_id) +
         ",\"region_id\":" + json_string(region_id) +
         ",\"round_config_id\":" + json_string(context.round_config_id) +
         ",\"scale_table_id\":" + json_string(context.scale_table_id) +
         ",\"schema_version\":\"1.0.0\",\"shard_id\":" + json_string(shard_id) +
         ",\"shard_plan_id\":" + json_string(context.shard_plan_id) +
         ",\"topology_id\":" + json_string(topology.topology_id) +
         ",\"type_name\":\"REGIONAL_INPUT_SET\"}";
}

[[nodiscard]] std::string regional_input_set_id(
    const Topology& topology,
    const HierarchyProofInstance& proof,
    std::string_view domain_id,
    std::string_view region_id,
    std::string_view shard_id,
    std::span<const Contribution> contributions) {
  const auto bytes = json_bytes(
      regional_input_json(topology, proof, domain_id, region_id, shard_id, contributions));
  return content_id("deltareduce.006.regional-input-set.v1", bytes);
}

[[nodiscard]] std::uint64_t absolute_coefficient(std::int64_t value) {
  require(value != std::numeric_limits<std::int64_t>::min(), ErrorCode::contribution_invalid,
          "coefficient magnitude exceeds uint64 contract");
  return value < 0 ? static_cast<std::uint64_t>(-value) : static_cast<std::uint64_t>(value);
}

[[nodiscard]] Int128 absolute(Int128 value) {
  if (!value.negative()) {
    return value;
  }
  require(value != Int128::minimum(), ErrorCode::contribution_invalid,
          "INT128_MIN cannot be represented as an absolute value");
  const auto low = (~value.low) + 1U;
  const auto carry = low == 0U ? std::uint64_t{1U} : std::uint64_t{0U};
  return Int128::from_bits(~value.high + carry, low);
}

[[nodiscard]] bool fits_width(
    Int128 value,
    delta::core::arithmetic::AccumulatorWidth width) noexcept {
  if (width == delta::core::arithmetic::AccumulatorWidth::int128) {
    return true;
  }
  return delta::core::arithmetic::compare(value, Int128::from_i64(INT64_MIN)) >= 0 &&
         delta::core::arithmetic::compare(value, Int128::from_i64(INT64_MAX)) <= 0;
}

void validate_prefix(Int128 value, const HierarchyProofInstance& proof) {
  require(fits_width(value, proof.selected_width) &&
              delta::core::arithmetic::compare(absolute(value), proof.final_abs_bound) <= 0,
          ErrorCode::proof_invalid, "hierarchy accumulator exceeded frozen proof bounds");
}

[[nodiscard]] Int128 validate_contribution(
    const Contribution& contribution,
    const Topology& topology,
    const HierarchyProofInstance& proof,
    std::string_view domain_id,
    std::string_view shard_id,
    std::size_t width) {
  require(contribution.context == topology.context && contribution.domain_id == domain_id &&
              contribution.shard_id == shard_id,
          ErrorCode::context_mismatch, "contribution lineage or immutable key does not match");
  const auto magnitude = absolute_coefficient(contribution.coefficient);
  require(content_id_valid(contribution.worker_shard_id), ErrorCode::identifier_invalid,
          "contribution worker shard ID is invalid");
  require(contribution.coefficient_denominator > 0U &&
              proof.common_denominator % contribution.coefficient_denominator == 0U &&
              std::gcd(magnitude, contribution.coefficient_denominator) == 1U,
          ErrorCode::contribution_invalid,
          "contribution denominator is not positive, reduced or a divisor of the common denominator");
  const auto common_factor = proof.common_denominator / contribution.coefficient_denominator;
  const auto scaled = delta::core::arithmetic::checked_multiply(
      Int128::from_i64(contribution.coefficient), Int128::from_u64(common_factor));
  require(delta::core::arithmetic::compare(absolute(scaled),
                                           Int128::from_u64(proof.coefficient_abs_max)) <= 0,
          ErrorCode::proof_invalid,
          "common-denominator coefficient exceeds theorem instance");
  require(contribution.q_values.size() == width, ErrorCode::contribution_invalid,
          "contribution vector width does not match parameter shard");
  for (const auto value : contribution.q_values) {
    const auto q_magnitude =
        value < 0 ? static_cast<std::uint64_t>(-static_cast<std::int64_t>(value))
                  : static_cast<std::uint64_t>(value);
    require(q_magnitude <= proof.q_abs_max, ErrorCode::proof_invalid,
            "contribution q value exceeds theorem instance");
  }
  return scaled;
}

[[nodiscard]] std::string regional_set_id(
    const Topology& topology,
    const HierarchyProofInstance& proof,
    std::string_view domain_id,
    std::string_view shard_id,
    std::span<const RegionalResult> results) {
  std::string regional_results = "[";
  std::vector<std::string> required_regions;
  required_regions.reserve(results.size());
  for (std::size_t index = 0U; index < results.size(); ++index) {
    if (index != 0U) {
      regional_results += ',';
    }
    regional_results += "{\"region_id\":" + json_string(results[index].region_id) +
                        ",\"regional_result_id\":" +
                        json_string(results[index].result_id) + "}";
    required_regions.push_back(results[index].region_id);
  }
  regional_results += ']';
  const auto& context = topology.context;
  const auto bytes = json_bytes(
      "{\"accumulator_proof_instance_id\":" +
      json_string(context.accumulator_proof_instance_id) +
      ",\"coefficient_plan_root\":" + json_string(context.coefficient_plan_root) +
      ",\"domain_id\":" + json_string(domain_id) +
      ",\"fixedpoint_config_id\":" + json_string(context.fixedpoint_config_id) +
      ",\"formal_semantics_id\":" + json_string(context.formal_semantics_id) +
      ",\"frozen_input_root\":" + json_string(context.frozen_input_root) +
      ",\"hierarchy_proof_instance_id\":" +
      json_string(proof.hierarchy_proof_instance_id) +
      ",\"parent_checkpoint_id\":" + json_string(context.parent_checkpoint_id) +
      ",\"profile_id\":" + json_string(context.profile_id) +
      ",\"regional_results\":" + regional_results +
      ",\"required_regions\":" + string_array_json(required_regions) +
      ",\"round_config_id\":" + json_string(context.round_config_id) +
      ",\"scale_table_id\":" + json_string(context.scale_table_id) +
      ",\"schema_version\":\"1.0.0\",\"shard_id\":" + json_string(shard_id) +
      ",\"shard_plan_id\":" + json_string(context.shard_plan_id) +
      ",\"topology_id\":" + json_string(topology.topology_id) +
      ",\"type_name\":\"GLOBAL_REGIONAL_SET\"}");
  return content_id("deltareduce.006.global-regional-set.v1", bytes);
}

[[maybe_unused, nodiscard]] std::vector<RegionalResult> canonical_regional_results(
    const Domain& domain,
    std::span<const RegionalResult> input) {
  std::vector<RegionalResult> result;
  result.reserve(domain.regions.size());
  for (const auto& required_region : domain.regions) {
    const auto found = std::find_if(input.begin(), input.end(), [&](const RegionalResult& value) {
      return value.region_id == required_region.region_id;
    });
    require(found != input.end(), ErrorCode::required_result_missing,
            "required regional result is missing");
    result.push_back(*found);
  }
  return result;
}

void validate_regional_result(
    const RegionalResult& result,
    const Topology& topology,
    const HierarchyProofInstance& proof,
    std::string_view domain_id,
    std::string_view shard_id) {
  const auto& domain = require_domain(topology, domain_id);
  const auto& region = require_region(domain, result.region_id);
  const auto& shard = require_shard(topology, shard_id);
  require(result.context == topology.context && result.topology_id == topology.topology_id &&
              result.hierarchy_proof_instance_id == proof.hierarchy_proof_instance_id &&
              result.domain_id == domain_id && result.shard_id == shard_id,
          ErrorCode::context_mismatch, "regional result lineage or key does not match");
  require(result.eligible_count == region.tickets.size() &&
              result.coefficient_denominator == proof.common_denominator &&
              content_id_valid(result.regional_input_set_id) &&
              result.numerator.size() == shard.end_element - shard.start_element,
          ErrorCode::contribution_invalid, "regional result metadata does not match topology");
  require(result.result_id == regional_result_id(result), ErrorCode::result_conflict,
          "regional result content ID does not match canonical bytes");
  validate_prefix(result.coefficient_numerator_sum, proof);
  for (const auto value : result.numerator) {
    validate_prefix(value, proof);
  }
}

[[nodiscard]] std::string committee_epoch_id(
    const Topology& topology,
    std::string_view domain_id,
    std::string_view region_id,
    bool global) {
  Bytes bytes;
  append_string(bytes, topology.topology_id);
  append_string(bytes, domain_id);
  append_string(bytes, region_id);
  append_u64(bytes, topology.validator_epoch);
  append_u64(bytes, global ? 1U : 0U);
  return content_id("deltareduce.006.committee-epoch.v1", bytes);
}

#if defined(DELTA_HIERARCHY_MUTANT_AVERAGE_REGIONS)
[[nodiscard]] std::int64_t narrow_i64(Int128 value) {
  if (value.high == 0U && value.low <= static_cast<std::uint64_t>(INT64_MAX)) {
    return static_cast<std::int64_t>(value.low);
  }
  if (value.high == UINT64_MAX && value.low >= UINT64_C(0x8000000000000000)) {
    return static_cast<std::int64_t>(value.low);
  }
  reject(ErrorCode::proof_invalid, "average mutant cannot narrow hierarchy value");
}
#endif

}  // namespace

Bytes canonical_bytes(const RegionalResult& result) {
  return json_bytes(
      "{\"accumulator_proof_instance_id\":" +
      json_string(result.context.accumulator_proof_instance_id) +
      ",\"coefficient_denominator\":" +
      json_string(std::to_string(result.coefficient_denominator)) +
      ",\"coefficient_numerator_sum\":" +
      json_string(decimal(result.coefficient_numerator_sum)) +
      ",\"coefficient_plan_root\":" + json_string(result.context.coefficient_plan_root) +
      ",\"domain_id\":" + json_string(result.domain_id) +
      ",\"eligible_count\":" + std::to_string(result.eligible_count) +
      ",\"fixedpoint_config_id\":" + json_string(result.context.fixedpoint_config_id) +
      ",\"formal_semantics_id\":" + json_string(result.context.formal_semantics_id) +
      ",\"frozen_input_root\":" + json_string(result.context.frozen_input_root) +
      ",\"hierarchy_proof_instance_id\":" + json_string(result.hierarchy_proof_instance_id) +
      ",\"numerator\":" + numerator_json(result.numerator) +
      ",\"parent_checkpoint_id\":" + json_string(result.context.parent_checkpoint_id) +
      ",\"profile_id\":" + json_string(result.context.profile_id) +
      ",\"region_id\":" + json_string(result.region_id) +
      ",\"regional_input_set_id\":" + json_string(result.regional_input_set_id) +
      ",\"round_config_id\":" + json_string(result.context.round_config_id) +
      ",\"scale_table_id\":" + json_string(result.context.scale_table_id) +
      ",\"schema_version\":\"1.0.0\",\"shard_id\":" + json_string(result.shard_id) +
      ",\"shard_plan_id\":" + json_string(result.context.shard_plan_id) +
      ",\"topology_id\":" + json_string(result.topology_id) +
      ",\"type_name\":\"REGIONAL_SHARD_RESULT\"}");
}

Bytes canonical_bytes(const Contribution& contribution) {
  Bytes output;
  output.insert(output.end(), {std::byte{'D'}, std::byte{'R'}, std::byte{'C'}, std::byte{1}});
  append_context(output, contribution.context);
  append_string(output, contribution.domain_id);
  append_string(output, contribution.shard_id);
  append_string(output, contribution.ticket_id);
  append_string(output, contribution.worker_shard_id);
  append_int128(output, Int128::from_i64(contribution.coefficient));
  append_u64(output, contribution.coefficient_denominator);
  append_u32(output, static_cast<std::uint32_t>(contribution.q_values.size()));
  for (const auto value : contribution.q_values) {
    append_u32(output, static_cast<std::uint16_t>(value));
  }
  return output;
}

Bytes canonical_routing_projection(const Topology& topology) {
  struct RouteRef {
    const Domain* domain;
    const Region* region;
    const ParameterShard* shard;
  };
  std::vector<RouteRef> routes;
  for (const auto& domain : topology.domains) {
    for (const auto& shard : topology.shards) {
      for (const auto& region : domain.regions) {
        routes.push_back(RouteRef{&domain, &region, &shard});
      }
    }
  }
  require(routes.size() <= std::numeric_limits<std::uint32_t>::max(),
          ErrorCode::partition_invalid, "routing projection has too many routes");
  std::sort(routes.begin(), routes.end(), [](const RouteRef& left, const RouteRef& right) {
    if (left.domain->domain_id != right.domain->domain_id) {
      return left.domain->domain_id < right.domain->domain_id;
    }
    if (left.shard->shard_id != right.shard->shard_id) {
      return left.shard->shard_id < right.shard->shard_id;
    }
    return left.region->region_id < right.region->region_id;
  });

  Bytes output{
      std::byte{'D'}, std::byte{'R'}, std::byte{'R'}, std::byte{1},
  };
  append_string(output, topology.topology_id);
  append_u64(output, topology.soft_deadline_tick);
  append_u64(output, topology.hard_deadline_tick);
  append_u32(output, static_cast<std::uint32_t>(routes.size()));
  for (const auto& route : routes) {
    append_string(output, route.domain->domain_id);
    append_string(output, route.region->region_id);
    append_string(output, route.shard->shard_id);
    require(route.region->tickets.size() <= std::numeric_limits<std::uint32_t>::max() &&
                route.region->validator_set.size() <=
                    std::numeric_limits<std::uint32_t>::max(),
            ErrorCode::partition_invalid, "routing projection collection is too large");
    append_u32(output, static_cast<std::uint32_t>(route.region->tickets.size()));
    for (const auto& ticket : route.region->tickets) {
      append_string(output, ticket);
    }
    append_u32(output, static_cast<std::uint32_t>(route.region->validator_set.size()));
    for (const auto& validator : route.region->validator_set) {
      append_string(output, validator);
    }
  }
  return output;
}

std::string routing_projection_id(const Topology& topology) {
  const auto bytes = canonical_routing_projection(topology);
  return content_id("deltareduce.006.routing-projection.v1", bytes);
}

Bytes canonical_bytes(const GlobalResult& result) {
  return json_bytes(
      "{\"accumulator_proof_instance_id\":" +
      json_string(result.context.accumulator_proof_instance_id) +
      ",\"coefficient_denominator\":" +
      json_string(std::to_string(result.coefficient_denominator)) +
      ",\"coefficient_numerator_sum\":" +
      json_string(decimal(result.coefficient_numerator_sum)) +
      ",\"coefficient_plan_root\":" + json_string(result.context.coefficient_plan_root) +
      ",\"domain_id\":" + json_string(result.domain_id) +
      ",\"eligible_count\":" + std::to_string(result.eligible_count) +
      ",\"fixedpoint_config_id\":" + json_string(result.context.fixedpoint_config_id) +
      ",\"formal_semantics_id\":" + json_string(result.context.formal_semantics_id) +
      ",\"frozen_input_root\":" + json_string(result.context.frozen_input_root) +
      ",\"global_regional_set_id\":" + json_string(result.regional_set_id) +
      ",\"hierarchy_proof_instance_id\":" + json_string(result.hierarchy_proof_instance_id) +
      ",\"numerator\":" + numerator_json(result.numerator) +
      ",\"parent_checkpoint_id\":" + json_string(result.context.parent_checkpoint_id) +
      ",\"profile_id\":" + json_string(result.context.profile_id) +
      ",\"round_config_id\":" + json_string(result.context.round_config_id) +
      ",\"scale_table_id\":" + json_string(result.context.scale_table_id) +
      ",\"schema_version\":\"1.0.0\",\"shard_id\":" + json_string(result.shard_id) +
      ",\"shard_plan_id\":" + json_string(result.context.shard_plan_id) +
      ",\"topology_id\":" + json_string(result.topology_id) +
      ",\"type_name\":\"GLOBAL_PARAMETER_RESULT\"}");
}

std::string regional_result_id(const RegionalResult& result) {
  const auto bytes = canonical_bytes(result);
  return content_id("deltareduce.006.regional-shard-result.v1", bytes);
}

std::string global_result_id(const GlobalResult& result) {
  const auto bytes = canonical_bytes(result);
  return content_id("deltareduce.006.global-parameter-result.v1", bytes);
}

Bytes canonical_bytes(const CommitteeQc& certificate) {
  const auto& context = certificate.context;
  const auto phase = certificate.global ? std::string_view{"GLOBAL_PARAMETER_RESULT"}
                                        : std::string_view{"REGIONAL_RESULT"};
  const auto type = certificate.global ? std::string_view{"GLOBAL_PARAMETER_QC"}
                                       : std::string_view{"REGIONAL_SHARD_QC"};
  std::string value =
      "{\"accumulator_proof_instance_id\":" +
      json_string(context.accumulator_proof_instance_id) +
      ",\"body_id\":" + json_string(certificate.body_id) +
      ",\"coefficient_plan_root\":" + json_string(context.coefficient_plan_root) +
      ",\"committee_epoch\":" + std::to_string(certificate.committee_epoch) +
      ",\"domain_id\":" + json_string(certificate.domain_id) +
      ",\"fixedpoint_config_id\":" + json_string(context.fixedpoint_config_id) +
      ",\"formal_semantics_id\":" + json_string(context.formal_semantics_id) +
      ",\"frozen_input_root\":" + json_string(context.frozen_input_root) +
      ",\"hierarchy_proof_instance_id\":" +
      json_string(certificate.hierarchy_proof_instance_id) +
      ",\"parent_checkpoint_id\":" + json_string(context.parent_checkpoint_id) +
      ",\"phase\":" + json_string(phase) +
      ",\"profile_id\":" + json_string(context.profile_id) +
      ",\"quorum_threshold\":" + std::to_string(certificate.quorum_threshold);
  if (!certificate.global) {
    value += ",\"region_id\":" + json_string(certificate.region_id);
  }
  value += ",\"round_config_id\":" + json_string(context.round_config_id) +
           ",\"scale_table_id\":" + json_string(context.scale_table_id) +
           ",\"schema_version\":\"1.0.0\",\"shard_id\":" +
           json_string(certificate.shard_id) +
           ",\"shard_plan_id\":" + json_string(context.shard_plan_id) +
           ",\"signer_ids\":" + string_array_json(certificate.signer_ids) +
           ",\"topology_id\":" + json_string(certificate.topology_id) +
           ",\"type_name\":" + json_string(type) +
           ",\"view\":" + std::to_string(certificate.view) + "}";
  return json_bytes(std::move(value));
}

std::string committee_qc_id(const CommitteeQc& certificate) {
  const auto bytes = canonical_bytes(certificate);
  return content_id(
      certificate.global ? "deltareduce.006.global-parameter-qc.v1"
                         : "deltareduce.006.regional-shard-qc.v1",
      bytes);
}

RegionalResult reduce_region(
    const Topology& topology,
    const HierarchyProofInstance& proof,
    std::string_view domain_id,
    std::string_view region_id,
    std::string_view shard_id,
    std::span<const Contribution> contributions) {
  validate_hierarchy_proof(topology, proof);
  const auto& domain = require_domain(topology, domain_id);
  const auto& region = require_region(domain, region_id);
  const auto& shard = require_shard(topology, shard_id);
  require(contributions.size() == region.tickets.size(), ErrorCode::partition_invalid,
          "regional input is not the exact required ticket set");
  auto ordered = std::vector<Contribution>(contributions.begin(), contributions.end());
  std::sort(ordered.begin(), ordered.end(), [](const Contribution& left, const Contribution& right) {
    return left.ticket_id < right.ticket_id;
  });
  for (std::size_t index = 0U; index < ordered.size(); ++index) {
    require(ordered[index].ticket_id == region.tickets[index], ErrorCode::partition_invalid,
            "regional input contains a gap, duplicate, or wrong ticket");
  }
  const auto width = static_cast<std::size_t>(shard.end_element - shard.start_element);
  std::vector<Int128> numerator(width, Int128::from_i64(0));
  auto coefficient_sum = Int128::from_i64(0);
  for (const auto& contribution : ordered) {
    const auto coefficient =
        validate_contribution(contribution, topology, proof, domain_id, shard_id, width);
    coefficient_sum = delta::core::arithmetic::checked_add(
        coefficient_sum, coefficient);
    validate_prefix(coefficient_sum, proof);
    for (std::size_t index = 0U; index < width; ++index) {
      const auto term = delta::core::arithmetic::checked_multiply(
          coefficient, Int128::from_i64(contribution.q_values[index]));
      validate_prefix(term, proof);
      numerator[index] = delta::core::arithmetic::checked_add(numerator[index], term);
      validate_prefix(numerator[index], proof);
    }
  }
  RegionalResult result{
      topology.context,
      topology.topology_id,
      proof.hierarchy_proof_instance_id,
      std::string(domain_id),
      std::string(region_id),
      std::string(shard_id),
      std::move(numerator),
      static_cast<std::uint64_t>(ordered.size()),
      coefficient_sum,
      proof.common_denominator,
      regional_input_set_id(topology, proof, domain_id, region_id, shard_id, ordered),
      {},
  };
  result.result_id = regional_result_id(result);
  return result;
}

GlobalAccumulator::GlobalAccumulator(
    const Topology& topology,
    const HierarchyProofInstance& proof,
    std::string domain_id,
    std::string shard_id)
    : topology_(&topology),
      proof_(&proof),
      domain_id_(std::move(domain_id)),
      shard_id_(std::move(shard_id)) {
  validate_hierarchy_proof(topology, proof);
  static_cast<void>(require_domain(topology, domain_id_));
  static_cast<void>(require_shard(topology, shard_id_));
}

bool GlobalAccumulator::ingest(RegionalResult result, CommitteeQc certificate) {
  validate_regional_result(result, *topology_, *proof_, domain_id_, shard_id_);
  validate_committee_qc(*topology_, *proof_, certificate);
  require(!certificate.global && certificate.body_id == result.result_id &&
              certificate.domain_id == result.domain_id &&
              certificate.region_id == result.region_id &&
              certificate.shard_id == result.shard_id,
          ErrorCode::context_mismatch,
          "regional result does not match its finalized committee QC");
  if (!certificates_.empty()) {
    require(certificate.view == certificates_.front().view, ErrorCode::context_mismatch,
            "global intake cannot mix regional committee views");
  }
  const auto found = std::find_if(results_.begin(), results_.end(), [&](const RegionalResult& value) {
    return value.region_id == result.region_id;
  });
  if (found != results_.end()) {
    require(*found == result, ErrorCode::result_conflict,
            "regional result key was replayed with conflicting bytes");
    return false;
  }
  results_.push_back(std::move(result));
  certificates_.push_back(std::move(certificate));
  return true;
}

std::size_t GlobalAccumulator::received_count() const noexcept { return results_.size(); }

GlobalResult GlobalAccumulator::finalize() const {
  const auto& domain = require_domain(*topology_, domain_id_);
  const auto& shard = require_shard(*topology_, shard_id_);
  static_cast<void>(domain);
#if !defined(DELTA_HIERARCHY_MUTANT_PARTIAL_GLOBAL)
  require(results_.size() == domain.regions.size(), ErrorCode::required_result_missing,
          "global intake has not received every required regional result");
  const auto ordered = canonical_regional_results(domain, results_);
#else
  const auto ordered = results_;
#endif
  const auto width = static_cast<std::size_t>(shard.end_element - shard.start_element);
  std::vector<Int128> numerator(width, Int128::from_i64(0));
  auto coefficient_sum = Int128::from_i64(0);
  std::uint64_t eligible_count = 0U;
  for (const auto& result : ordered) {
    require(eligible_count <= std::numeric_limits<std::uint64_t>::max() - result.eligible_count,
            ErrorCode::proof_invalid, "global eligible count overflowed");
    eligible_count += result.eligible_count;
    coefficient_sum = delta::core::arithmetic::checked_add(
        coefficient_sum, result.coefficient_numerator_sum);
    validate_prefix(coefficient_sum, *proof_);
    for (std::size_t index = 0U; index < width; ++index) {
#if defined(DELTA_HIERARCHY_MUTANT_AVERAGE_REGIONS)
      const auto value = Int128::from_i64(
          narrow_i64(result.numerator[index]) / static_cast<std::int64_t>(result.eligible_count));
#else
      const auto value = result.numerator[index];
#endif
      numerator[index] = delta::core::arithmetic::checked_add(numerator[index], value);
      validate_prefix(numerator[index], *proof_);
    }
  }
#if !defined(DELTA_HIERARCHY_MUTANT_PARTIAL_GLOBAL)
  require(eligible_count == domain.tickets.size(), ErrorCode::partition_invalid,
          "global result does not cover the exact immutable domain ticket set");
#endif
  GlobalResult result{
      topology_->context,
      topology_->topology_id,
      proof_->hierarchy_proof_instance_id,
      domain_id_,
      shard_id_,
      std::move(numerator),
      eligible_count,
      coefficient_sum,
      proof_->common_denominator,
      regional_set_id(*topology_, *proof_, domain_id_, shard_id_, ordered),
      {},
  };
  result.result_id = global_result_id(result);
  return result;
}

GlobalResult reduce_flat(
    const Topology& topology,
    const HierarchyProofInstance& proof,
    std::string_view domain_id,
    std::string_view shard_id,
    std::span<const Contribution> contributions) {
  validate_hierarchy_proof(topology, proof);
  const auto& domain = require_domain(topology, domain_id);
  const auto& shard = require_shard(topology, shard_id);
  require(contributions.size() == domain.tickets.size(), ErrorCode::partition_invalid,
          "flat oracle input is not the exact domain ticket set");
  auto ordered = std::vector<Contribution>(contributions.begin(), contributions.end());
  std::sort(ordered.begin(), ordered.end(), [](const Contribution& left, const Contribution& right) {
    return left.ticket_id < right.ticket_id;
  });
  for (std::size_t index = 0U; index < ordered.size(); ++index) {
    require(ordered[index].ticket_id == domain.tickets[index], ErrorCode::partition_invalid,
            "flat oracle input contains a gap, duplicate, or wrong ticket");
  }

  std::vector<RegionalResult> regional;
  regional.reserve(domain.regions.size());
  for (const auto& region : domain.regions) {
    std::vector<Contribution> region_input;
    for (const auto& contribution : ordered) {
      if (std::binary_search(region.tickets.begin(), region.tickets.end(), contribution.ticket_id)) {
        region_input.push_back(contribution);
      }
    }
    regional.push_back(reduce_region(
        topology, proof, domain_id, region.region_id, shard_id, region_input));
  }

  const auto width = static_cast<std::size_t>(shard.end_element - shard.start_element);
  std::vector<Int128> numerator(width, Int128::from_i64(0));
  auto coefficient_sum = Int128::from_i64(0);
  for (const auto& contribution : ordered) {
    const auto coefficient =
        validate_contribution(contribution, topology, proof, domain_id, shard_id, width);
    coefficient_sum = delta::core::arithmetic::checked_add(
        coefficient_sum, coefficient);
    validate_prefix(coefficient_sum, proof);
    for (std::size_t index = 0U; index < width; ++index) {
      const auto term = delta::core::arithmetic::checked_multiply(
          coefficient, Int128::from_i64(contribution.q_values[index]));
      numerator[index] = delta::core::arithmetic::checked_add(numerator[index], term);
      validate_prefix(numerator[index], proof);
    }
  }
  GlobalResult result{
      topology.context,
      topology.topology_id,
      proof.hierarchy_proof_instance_id,
      std::string(domain_id),
      std::string(shard_id),
      std::move(numerator),
      static_cast<std::uint64_t>(ordered.size()),
      coefficient_sum,
      proof.common_denominator,
      regional_set_id(topology, proof, domain_id, shard_id, regional),
      {},
  };
  result.result_id = global_result_id(result);
  return result;
}

Assembly assemble_complete(
    const Topology& topology,
    const HierarchyProofInstance& proof,
    std::span<const GlobalResult> results,
    std::span<const CommitteeQc> certificates) {
  validate_hierarchy_proof(topology, proof);
  std::vector<GlobalResult> canonical;
  std::vector<CommitteeQc> canonical_certificates;
  canonical.reserve(topology.domains.size() * topology.shards.size());
  canonical_certificates.reserve(topology.domains.size() * topology.shards.size());
  for (const auto& domain : topology.domains) {
    for (const auto& shard : topology.shards) {
      std::vector<GlobalResult> matching;
      for (const auto& result : results) {
        if (result.domain_id == domain.domain_id && result.shard_id == shard.shard_id) {
          matching.push_back(result);
        }
      }
      require(!matching.empty(), ErrorCode::assembly_incomplete,
              "complete hierarchy is missing a required domain/shard result");
      for (const auto& duplicate : matching) {
        require(duplicate == matching.front(), ErrorCode::result_conflict,
                "complete hierarchy contains conflicting domain/shard results");
      }
      const auto& result = matching.front();
      require(result.context == topology.context && result.topology_id == topology.topology_id &&
                  result.hierarchy_proof_instance_id == proof.hierarchy_proof_instance_id &&
                  result.eligible_count == domain.tickets.size() &&
                  result.coefficient_denominator == proof.common_denominator &&
                  content_id_valid(result.regional_set_id) &&
                  result.numerator.size() == shard.end_element - shard.start_element &&
                  result.result_id == global_result_id(result),
              ErrorCode::context_mismatch,
              "global result cannot enter complete hierarchy under its lineage");
      validate_prefix(result.coefficient_numerator_sum, proof);
      for (const auto value : result.numerator) {
        validate_prefix(value, proof);
      }
      canonical.push_back(result);

      std::vector<CommitteeQc> matching_certificates;
      for (const auto& certificate : certificates) {
        if (certificate.global && certificate.domain_id == domain.domain_id &&
            certificate.shard_id == shard.shard_id) {
          matching_certificates.push_back(certificate);
        }
      }
      require(!matching_certificates.empty(), ErrorCode::assembly_incomplete,
              "complete hierarchy is missing a required global parameter QC");
      for (const auto& duplicate : matching_certificates) {
        require(duplicate == matching_certificates.front(), ErrorCode::result_conflict,
                "complete hierarchy contains conflicting global parameter QCs");
      }
      const auto& certificate = matching_certificates.front();
      validate_committee_qc(topology, proof, certificate);
      require(certificate.body_id == result.result_id, ErrorCode::context_mismatch,
              "global parameter QC certifies the wrong result body");
      if (!canonical_certificates.empty()) {
        require(certificate.view == canonical_certificates.front().view,
                ErrorCode::context_mismatch,
                "complete hierarchy cannot mix global committee views");
      }
      canonical_certificates.push_back(certificate);
    }
  }
  for (const auto& result : results) {
    static_cast<void>(require_domain(topology, result.domain_id));
    static_cast<void>(require_shard(topology, result.shard_id));
  }
  require(certificates.size() >= canonical_certificates.size(), ErrorCode::assembly_incomplete,
          "global parameter QC matrix is incomplete");
  for (const auto& certificate : certificates) {
    require(certificate.global, ErrorCode::context_mismatch,
            "regional QC cannot enter hierarchical aggregate coverage");
    static_cast<void>(require_domain(topology, certificate.domain_id));
    static_cast<void>(require_shard(topology, certificate.shard_id));
  }

  std::string coverage = "[";
  std::string required_shards = "[";
  for (std::size_t index = 0U; index < canonical.size(); ++index) {
    if (index != 0U) {
      coverage += ',';
      required_shards += ',';
    }
    coverage += "{\"domain_id\":" + json_string(canonical[index].domain_id) +
                ",\"global_parameter_qc_id\":" +
                json_string(committee_qc_id(canonical_certificates[index])) +
                ",\"global_parameter_result_id\":" +
                json_string(canonical[index].result_id) +
                ",\"shard_id\":" + json_string(canonical[index].shard_id) + "}";
    required_shards += "{\"domain_id\":" + json_string(canonical[index].domain_id) +
                       ",\"shard_id\":" + json_string(canonical[index].shard_id) + "}";
  }
  coverage += ']';
  required_shards += ']';
  const auto& context = topology.context;
  auto bytes = json_bytes(
      "{\"accumulator_proof_instance_id\":" +
      json_string(context.accumulator_proof_instance_id) +
      ",\"coefficient_plan_root\":" + json_string(context.coefficient_plan_root) +
      ",\"coverage\":" + coverage +
      ",\"fixedpoint_config_id\":" + json_string(context.fixedpoint_config_id) +
      ",\"formal_semantics_id\":" + json_string(context.formal_semantics_id) +
      ",\"frozen_input_root\":" + json_string(context.frozen_input_root) +
      ",\"hierarchy_proof_instance_id\":" +
      json_string(proof.hierarchy_proof_instance_id) +
      ",\"parent_checkpoint_id\":" + json_string(context.parent_checkpoint_id) +
      ",\"profile_id\":" + json_string(context.profile_id) +
      ",\"required_domain_shards\":" + required_shards +
      ",\"round_config_id\":" + json_string(context.round_config_id) +
      ",\"scale_table_id\":" + json_string(context.scale_table_id) +
      ",\"schema_version\":\"1.0.0\",\"shard_plan_id\":" +
      json_string(context.shard_plan_id) +
      ",\"topology_id\":" + json_string(topology.topology_id) +
      ",\"type_name\":\"HIERARCHICAL_AGGREGATE_ROOT\"}");
  return Assembly{
      bytes,
      content_id("deltareduce.006.hierarchical-aggregate-root.v1", bytes),
      std::move(canonical),
      std::move(canonical_certificates),
  };
}

void validate_committee_qc(
    const Topology& topology,
    const HierarchyProofInstance& proof,
    const CommitteeQc& certificate) {
  validate_hierarchy_proof(topology, proof);
  require(certificate.context == topology.context &&
              certificate.topology_id == topology.topology_id &&
              certificate.hierarchy_proof_instance_id == proof.hierarchy_proof_instance_id &&
              certificate.committee_epoch == topology.validator_epoch &&
              content_id_valid(certificate.body_id),
          ErrorCode::context_mismatch, "committee QC lineage does not match topology");
  static_cast<void>(require_shard(topology, certificate.shard_id));
  const auto& domain = require_domain(topology, certificate.domain_id);
  const std::vector<std::string>* validators = &domain.global_validator_set;
  std::uint32_t fault_bound = domain.global_fault_bound;
  if (!certificate.global) {
    const auto& region = require_region(domain, certificate.region_id);
    validators = &region.validator_set;
    fault_bound = region.fault_bound;
  } else {
    require(certificate.region_id.empty(), ErrorCode::quorum_invalid,
            "global committee QC unexpectedly names a region");
  }
  require(!certificate.signer_ids.empty() &&
              std::is_sorted(certificate.signer_ids.begin(), certificate.signer_ids.end()) &&
              std::adjacent_find(certificate.signer_ids.begin(), certificate.signer_ids.end()) ==
                  certificate.signer_ids.end(),
          ErrorCode::quorum_invalid, "committee QC signer set is noncanonical");
  require(fault_bound <= (std::numeric_limits<std::uint32_t>::max() - 1U) / 2U &&
              certificate.quorum_threshold == 2U * fault_bound + 1U &&
              certificate.signer_ids.size() >= certificate.quorum_threshold,
          ErrorCode::quorum_invalid, "committee QC has insufficient unique signers");
  for (const auto& signer : certificate.signer_ids) {
    require(std::binary_search(validators->begin(), validators->end(), signer),
            ErrorCode::quorum_invalid, "committee QC contains an unknown signer");
  }
}

delta::core::protocol::Vote make_committee_vote(
    const Topology& topology,
    const HierarchyProofInstance& proof,
    const CommitteeQc& intent,
    std::string validator_id,
    std::string signature_id,
    std::uint64_t durable_sequence) {
  validate_committee_qc(topology, proof, intent);
  require(std::binary_search(intent.signer_ids.begin(), intent.signer_ids.end(), validator_id),
          ErrorCode::quorum_invalid, "vote validator is outside the exact committee intent");
  require(content_id_valid(signature_id) && durable_sequence > 0U,
          ErrorCode::identifier_invalid, "vote durability/signature fields are invalid");
  const auto epoch_id = committee_epoch_id(
      topology, intent.domain_id, intent.region_id, intent.global);
  const auto context_id = intent.domain_id + "/" +
                          (intent.global ? std::string{"global"} : intent.region_id) + "/" +
                          intent.shard_id;
  return delta::core::protocol::Vote{
      intent.body_id,
      context_id,
      durable_sequence,
      topology.validator_epoch,
      intent.global ? "GLOBAL_PARAMETER_RESULT" : "REGIONAL_SHARD_RESULT",
      topology.context.round_config_id,
      std::move(signature_id),
      epoch_id,
      std::move(validator_id),
      intent.view,
  };
}

}  // namespace delta::reduce
