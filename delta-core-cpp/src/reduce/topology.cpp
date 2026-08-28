#include <delta/reduce/topology.hpp>

#include <delta/core/canonical.hpp>
#include <delta/fixedpoint/profile.hpp>

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

enum class JsonType { unsigned_integer, string, array, object };

struct JsonValue {
  JsonType type = JsonType::string;
  std::uint64_t unsigned_integer = 0U;
  std::string string;
  std::vector<JsonValue> array;
  std::vector<std::string> object_keys;
  std::vector<JsonValue> object_values;
};

[[noreturn]] void reject(ErrorCode code, std::string message) {
  throw ReduceError(code, std::move(message));
}

void require(bool condition, ErrorCode code, const char* message) {
  if (!condition) {
    reject(code, message);
  }
}

class CanonicalJsonParser final {
 public:
  CanonicalJsonParser(std::string_view input, const Limits& limits)
      : input_(input), limits_(limits) {}

  [[nodiscard]] JsonValue parse() {
    auto result = parse_value(0U);
    require(cursor_ == input_.size(), ErrorCode::canonical_json_invalid, "trailing JSON bytes");
    return result;
  }

 private:
  [[nodiscard]] bool take(char expected) {
    if (cursor_ < input_.size() && input_[cursor_] == expected) {
      ++cursor_;
      return true;
    }
    return false;
  }

  void count_member() {
    ++members_;
    require(
        members_ <= limits_.collection_members,
        ErrorCode::canonical_json_invalid,
        "JSON member limit exceeded");
  }

  [[nodiscard]] JsonValue parse_value(std::size_t depth) {
    require(
        depth <= limits_.nesting_depth,
        ErrorCode::canonical_json_invalid,
        "JSON nesting limit exceeded");
    require(
        cursor_ < input_.size(),
        ErrorCode::canonical_json_invalid,
        "JSON value is truncated");
    if (input_[cursor_] == '{') {
      return parse_object(depth + 1U);
    }
    if (input_[cursor_] == '[') {
      return parse_array(depth + 1U);
    }
    if (input_[cursor_] == '"') {
      JsonValue result;
      result.type = JsonType::string;
      result.string = parse_string();
      return result;
    }
    return parse_unsigned();
  }

  [[nodiscard]] JsonValue parse_object(std::size_t depth) {
    require(take('{'), ErrorCode::canonical_json_invalid, "object start is missing");
    JsonValue result;
    result.type = JsonType::object;
    if (take('}')) {
      return result;
    }
    std::string prior_key;
    for (;;) {
      require(
          cursor_ < input_.size() && input_[cursor_] == '"',
          ErrorCode::canonical_json_invalid,
          "object key is missing");
      auto key = parse_string();
      require(
          prior_key.empty() || prior_key < key,
          ErrorCode::canonical_json_invalid,
          "object keys are not canonical");
      require(take(':'), ErrorCode::canonical_json_invalid, "object colon is missing");
      count_member();
      auto value = parse_value(depth);
      result.object_keys.push_back(key);
      result.object_values.push_back(std::move(value));
      prior_key = std::move(key);
      if (take('}')) {
        return result;
      }
      require(take(','), ErrorCode::canonical_json_invalid, "object comma is missing");
    }
  }

  [[nodiscard]] JsonValue parse_array(std::size_t depth) {
    require(take('['), ErrorCode::canonical_json_invalid, "array start is missing");
    JsonValue result;
    result.type = JsonType::array;
    if (take(']')) {
      return result;
    }
    for (;;) {
      count_member();
      result.array.push_back(parse_value(depth));
      if (take(']')) {
        return result;
      }
      require(take(','), ErrorCode::canonical_json_invalid, "array comma is missing");
    }
  }

  [[nodiscard]] std::string parse_string() {
    require(take('"'), ErrorCode::canonical_json_invalid, "string start is missing");
    const auto begin = cursor_;
    while (cursor_ < input_.size() && input_[cursor_] != '"') {
      const auto value = static_cast<unsigned char>(input_[cursor_]);
      require(
          value >= 0x20U && value <= 0x7eU && input_[cursor_] != '\\',
          ErrorCode::canonical_json_invalid,
          "string is outside canonical ASCII subset");
      ++cursor_;
    }
    require(cursor_ < input_.size(), ErrorCode::canonical_json_invalid, "string is truncated");
    auto result = std::string(input_.substr(begin, cursor_ - begin));
    ++cursor_;
    return result;
  }

  [[nodiscard]] JsonValue parse_unsigned() {
    require(
        cursor_ < input_.size() && input_[cursor_] >= '0' && input_[cursor_] <= '9',
        ErrorCode::canonical_json_invalid,
        "only canonical unsigned JSON integers are accepted");
    const auto begin = cursor_;
    if (input_[cursor_] == '0') {
      ++cursor_;
      require(
          cursor_ == input_.size() || input_[cursor_] < '0' || input_[cursor_] > '9',
          ErrorCode::canonical_json_invalid,
          "integer contains a leading zero");
    } else {
      while (cursor_ < input_.size() && input_[cursor_] >= '0' && input_[cursor_] <= '9') {
        ++cursor_;
      }
    }
    std::uint64_t value = 0U;
    for (const char digit : input_.substr(begin, cursor_ - begin)) {
      const auto next = static_cast<unsigned>(digit - '0');
      require(
          value <= (std::numeric_limits<std::uint64_t>::max() - next) / 10U,
          ErrorCode::canonical_json_invalid,
          "integer overflows uint64");
      value = value * 10U + next;
    }
    JsonValue result;
    result.type = JsonType::unsigned_integer;
    result.unsigned_integer = value;
    return result;
  }

  std::string_view input_;
  const Limits& limits_;
  std::size_t cursor_ = 0U;
  std::size_t members_ = 0U;
};

void require_keys(
    const JsonValue& object,
    std::initializer_list<std::string_view> keys,
    const char* message) {
  require(object.type == JsonType::object, ErrorCode::field_set_invalid, message);
  require(object.object_keys.size() == keys.size(), ErrorCode::field_set_invalid, message);
  std::size_t index = 0U;
  for (const auto key : keys) {
    require(object.object_keys[index] == key, ErrorCode::field_set_invalid, message);
    ++index;
  }
}

[[nodiscard]] const JsonValue& member(const JsonValue& object, std::string_view key) {
  const auto found = std::lower_bound(object.object_keys.begin(), object.object_keys.end(), key);
  require(found != object.object_keys.end() && *found == key, ErrorCode::field_set_invalid,
          "required topology field is missing");
  return object.object_values[static_cast<std::size_t>(found - object.object_keys.begin())];
}

[[nodiscard]] std::string string_member(const JsonValue& object, std::string_view key) {
  const auto& value = member(object, key);
  require(value.type == JsonType::string, ErrorCode::field_set_invalid,
          "topology string field has the wrong type");
  return value.string;
}

[[nodiscard]] std::uint64_t unsigned_member(const JsonValue& object, std::string_view key) {
  const auto& value = member(object, key);
  require(value.type == JsonType::unsigned_integer, ErrorCode::field_set_invalid,
          "topology integer field has the wrong type");
  return value.unsigned_integer;
}

[[nodiscard]] std::vector<std::string> string_array(
    const JsonValue& object,
    std::string_view key,
    std::size_t maximum) {
  const auto& value = member(object, key);
  require(value.type == JsonType::array && !value.array.empty() && value.array.size() <= maximum,
          ErrorCode::field_set_invalid, "topology string array has invalid bounds");
  std::vector<std::string> result;
  result.reserve(value.array.size());
  for (const auto& item : value.array) {
    require(item.type == JsonType::string, ErrorCode::field_set_invalid,
            "topology string array contains a non-string");
    result.push_back(item.string);
  }
  return result;
}

[[nodiscard]] std::uint32_t checked_u32(std::uint64_t value) {
  require(value <= std::numeric_limits<std::uint32_t>::max(), ErrorCode::field_set_invalid,
          "topology integer exceeds uint32");
  return static_cast<std::uint32_t>(value);
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

[[nodiscard]] bool label_valid(std::string_view value) noexcept {
  return !value.empty() && value.size() <= 128U &&
         std::all_of(value.begin(), value.end(), [](char character) {
           return character >= 0x21 && character <= 0x7e;
         });
}

template <typename Values>
[[nodiscard]] bool unique_values(const Values& values) {
  std::set<typename Values::value_type> unique(values.begin(), values.end());
  return unique.size() == values.size();
}

void validate_sorted_labels(const std::vector<std::string>& values, const char* message) {
  require(unique_values(values), ErrorCode::partition_invalid, message);
  require(std::is_sorted(values.begin(), values.end()), ErrorCode::partition_invalid, message);
  require(std::all_of(values.begin(), values.end(), label_valid), ErrorCode::identifier_invalid,
          "topology label is invalid");
}

[[maybe_unused, nodiscard]] bool fits_width(
    delta::core::arithmetic::Int128 value,
    delta::core::arithmetic::AccumulatorWidth width) noexcept {
  if (width == delta::core::arithmetic::AccumulatorWidth::int128) {
    return true;
  }
  return delta::core::arithmetic::compare(
             value, delta::core::arithmetic::Int128::from_i64(INT64_MAX)) <= 0 &&
         delta::core::arithmetic::compare(
             value, delta::core::arithmetic::Int128::from_i64(INT64_MIN)) >= 0;
}

[[nodiscard]] delta::core::arithmetic::Int128 absolute(
    delta::core::arithmetic::Int128 value) {
  if (!value.negative()) {
    return value;
  }
  require(value != delta::core::arithmetic::Int128::minimum(), ErrorCode::proof_invalid,
          "proof bound cannot be INT128_MIN");
  const auto low = (~value.low) + 1U;
  const auto carry = low == 0U ? std::uint64_t{1U} : std::uint64_t{0U};
  return delta::core::arithmetic::Int128::from_bits(~value.high + carry, low);
}

[[nodiscard]] delta::core::arithmetic::Int128 proof_multiply(
    delta::core::arithmetic::Int128 left,
    delta::core::arithmetic::Int128 right) {
  try {
    return delta::core::arithmetic::checked_multiply(left, right);
  } catch (const delta::core::arithmetic::ArithmeticError&) {
    reject(ErrorCode::proof_invalid, "hierarchy proof multiplication exceeds int128");
  }
}

[[nodiscard]] std::uint64_t decimal_u64(std::string_view value) {
  require(!value.empty() && (value == "0" || value.front() >= '1'),
          ErrorCode::proof_invalid, "proof decimal is not canonical");
  std::uint64_t result = 0U;
  for (const char digit : value) {
    require(digit >= '0' && digit <= '9', ErrorCode::proof_invalid,
            "proof decimal is not unsigned");
    const auto next = static_cast<unsigned>(digit - '0');
    require(result <= (std::numeric_limits<std::uint64_t>::max() - next) / 10U,
            ErrorCode::proof_invalid, "proof decimal exceeds uint64");
    result = result * 10U + next;
  }
  return result;
}

[[nodiscard]] delta::core::arithmetic::Int128 decimal_int128(std::string_view value) {
  require(!value.empty() && (value == "0" || value.front() >= '1'),
          ErrorCode::proof_invalid, "proof bound is not canonical");
  auto result = delta::core::arithmetic::Int128::from_u64(0U);
  try {
    for (const char digit : value) {
      require(digit >= '0' && digit <= '9', ErrorCode::proof_invalid,
              "proof bound is not unsigned");
      result = delta::core::arithmetic::checked_add(
          delta::core::arithmetic::checked_multiply(
              result, delta::core::arithmetic::Int128::from_u64(10U)),
          delta::core::arithmetic::Int128::from_u64(static_cast<unsigned>(digit - '0')));
    }
  } catch (const delta::core::arithmetic::ArithmeticError&) {
    reject(ErrorCode::proof_invalid, "proof bound exceeds int128");
  }
  return result;
}

[[nodiscard]] std::vector<TheoremBinding> required_theorem_bindings() {
  return {
      {"PO-H1", {"exact-partition"}},
      {"PO-H2", {"hierarchy-equals-flat"}},
      {"PO-A1", {"product-bound"}},
      {"PO-A2", {"flat-accumulator-bound"}},
      {"PO-A3",
       {"canonical-reduced-input", "input-denominator-divides-common",
        "numerator-accumulator-bound", "positive-common-denominator",
        "positive-input-denominator", "round-at-or-above-half", "round-below-half",
        "round-half-tie-toward-positive", "rounding-deterministic"}},
  };
}

[[nodiscard]] std::string content_id_for(
    std::string_view domain,
    std::span<const std::byte> canonical_json) {
  std::vector<std::byte> input;
  input.reserve(domain.size() + 1U + canonical_json.size());
  for (const char character : domain) {
    input.push_back(static_cast<std::byte>(character));
  }
  input.push_back(std::byte{0});
  input.insert(input.end(), canonical_json.begin(), canonical_json.end());
  return "sha256:" + delta::core::canonical::sha256_hex(input);
}

}  // namespace

ReduceError::ReduceError(ErrorCode code, std::string message)
    : std::runtime_error(std::move(message)), code_(code) {}

ErrorCode ReduceError::code() const noexcept { return code_; }

std::string topology_content_id(std::span<const std::byte> canonical_json) {
  return content_id_for("deltareduce.006.reduce-topology.v1", canonical_json);
}

std::string hierarchy_proof_content_id(std::span<const std::byte> canonical_json) {
  return content_id_for("deltareduce.006.hierarchy-proof-instance.v1", canonical_json);
}

Topology parse_topology(
    std::span<const std::byte> canonical_json,
    const Context& expected_context,
    const Limits& limits) {
  require(!canonical_json.empty() && canonical_json.size() <= limits.topology_bytes,
          ErrorCode::input_too_large, "topology byte length is outside limits");
  const auto text = std::string_view(
      reinterpret_cast<const char*>(canonical_json.data()), canonical_json.size());
  const auto root = CanonicalJsonParser(text, limits).parse();
  require_keys(
      root,
      {"accumulator_proof_instance_id", "coefficient_plan_root", "domains",
       "fixedpoint_config_id", "formal_semantics_id", "frozen_input_root",
       "hard_deadline_tick", "parent_checkpoint_id", "profile_id", "round_config_id",
       "scale_table_id", "schema_version", "shard_plan_id", "shards",
       "soft_deadline_tick", "type_name", "validator_epoch"},
      "reduce topology root field set is invalid");
  require(string_member(root, "schema_version") == "1.0.0" &&
              string_member(root, "type_name") == "REDUCE_TOPOLOGY",
          ErrorCode::field_set_invalid, "reduce topology constants are invalid");

  Topology topology{
      Context{
          string_member(root, "accumulator_proof_instance_id"),
          string_member(root, "coefficient_plan_root"),
          string_member(root, "fixedpoint_config_id"),
          string_member(root, "formal_semantics_id"),
          string_member(root, "frozen_input_root"),
          string_member(root, "parent_checkpoint_id"),
          string_member(root, "profile_id"),
          string_member(root, "round_config_id"),
          string_member(root, "scale_table_id"),
          string_member(root, "shard_plan_id"),
      },
      {},
      unsigned_member(root, "hard_deadline_tick"),
      {},
      unsigned_member(root, "soft_deadline_tick"),
      unsigned_member(root, "validator_epoch"),
      topology_content_id(canonical_json),
  };
  require(topology.context == expected_context, ErrorCode::context_mismatch,
          "reduce topology context does not match the frozen round");

  const auto& domains = member(root, "domains");
  require(domains.type == JsonType::array && !domains.array.empty() &&
              domains.array.size() <= limits.domains,
          ErrorCode::field_set_invalid, "topology domain count is outside limits");
  topology.domains.reserve(domains.array.size());
  for (const auto& value : domains.array) {
    require_keys(value,
                 {"domain_id", "global_fault_bound", "global_validator_set", "regions",
                  "tickets"},
                 "domain field set is invalid");
    Domain domain{
        string_member(value, "domain_id"),
        checked_u32(unsigned_member(value, "global_fault_bound")),
        string_array(value, "global_validator_set", limits.validators_per_committee),
        {},
        string_array(value, "tickets", limits.tickets_per_domain),
    };
    const auto& regions = member(value, "regions");
    require(regions.type == JsonType::array && !regions.array.empty() &&
                regions.array.size() <= limits.regions_per_domain,
            ErrorCode::field_set_invalid, "topology region count is outside limits");
    domain.regions.reserve(regions.array.size());
    for (const auto& region_value : regions.array) {
      require_keys(region_value, {"fault_bound", "region_id", "tickets", "validator_set"},
                   "region field set is invalid");
      domain.regions.push_back(Region{
          checked_u32(unsigned_member(region_value, "fault_bound")),
          string_member(region_value, "region_id"),
          string_array(region_value, "tickets", limits.tickets_per_domain),
          string_array(region_value, "validator_set", limits.validators_per_committee),
      });
    }
    topology.domains.push_back(std::move(domain));
  }

  const auto& shards = member(root, "shards");
  require(shards.type == JsonType::array && !shards.array.empty() &&
              shards.array.size() <= limits.shards,
          ErrorCode::field_set_invalid, "topology shard count is outside limits");
  topology.shards.reserve(shards.array.size());
  for (const auto& value : shards.array) {
    require_keys(value, {"end_element", "shard_id", "start_element"},
                 "parameter shard field set is invalid");
    topology.shards.push_back(ParameterShard{
        unsigned_member(value, "end_element"),
        string_member(value, "shard_id"),
        unsigned_member(value, "start_element"),
    });
  }
  validate_topology(topology, limits);
  return topology;
}

HierarchyProofInstance parse_hierarchy_proof(
    std::span<const std::byte> canonical_json,
    const Topology& topology,
    const Limits& limits) {
  require(!canonical_json.empty() && canonical_json.size() <= limits.proof_bytes,
          ErrorCode::input_too_large, "hierarchy proof byte length is outside limits");
  const auto text = std::string_view(
      reinterpret_cast<const char*>(canonical_json.data()), canonical_json.size());
  const auto root = CanonicalJsonParser(text, limits).parse();
  require_keys(
      root,
      {"accumulator_proof_instance_id", "coefficient_abs_max", "coefficient_plan_root",
       "common_denominator", "domain_ticket_counts", "final_abs_bound",
       "fixedpoint_config_id", "formal_semantics_id", "frozen_input_root",
       "max_eligible_contributions", "parent_checkpoint_id", "product_abs_bound", "profile_id",
       "q_abs_max", "result", "round_config_id", "scale_table_id", "schema_version",
       "selected_accumulator_width_bits", "shard_plan_id", "shard_ranges", "theorems",
       "topology_id", "type_name"},
      "hierarchy proof field set is invalid");
  require(string_member(root, "schema_version") == "1.0.0" &&
              string_member(root, "type_name") == "HIERARCHY_PROOF_INSTANCE" &&
              string_member(root, "result") == "PASS",
          ErrorCode::proof_invalid, "hierarchy proof constants are invalid");
  const auto width = unsigned_member(root, "selected_accumulator_width_bits");
  require(width == 64U || width == 128U, ErrorCode::proof_invalid,
          "hierarchy proof accumulator width is invalid");

  HierarchyProofInstance proof{
      hierarchy_proof_content_id(canonical_json),
      string_member(root, "topology_id"),
      Context{
          string_member(root, "accumulator_proof_instance_id"),
          string_member(root, "coefficient_plan_root"),
          string_member(root, "fixedpoint_config_id"),
          string_member(root, "formal_semantics_id"),
          string_member(root, "frozen_input_root"),
          string_member(root, "parent_checkpoint_id"),
          string_member(root, "profile_id"),
          string_member(root, "round_config_id"),
          string_member(root, "scale_table_id"),
          string_member(root, "shard_plan_id"),
      },
      decimal_u64(string_member(root, "coefficient_abs_max")),
      decimal_u64(string_member(root, "common_denominator")),
      unsigned_member(root, "max_eligible_contributions"),
      decimal_int128(string_member(root, "product_abs_bound")),
      decimal_int128(string_member(root, "final_abs_bound")),
      decimal_u64(string_member(root, "q_abs_max")),
      width == 64U ? delta::core::arithmetic::AccumulatorWidth::int64
                   : delta::core::arithmetic::AccumulatorWidth::int128,
      {},
      {},
      {},
  };

  const auto& counts = member(root, "domain_ticket_counts");
  require(counts.type == JsonType::object && !counts.object_keys.empty() &&
              counts.object_keys.size() <= limits.domains,
          ErrorCode::proof_invalid, "proof domain count matrix is invalid");
  proof.domain_ticket_counts.reserve(counts.object_keys.size());
  for (std::size_t index = 0U; index < counts.object_keys.size(); ++index) {
    require(counts.object_values[index].type == JsonType::unsigned_integer,
            ErrorCode::proof_invalid, "proof domain count has the wrong type");
    proof.domain_ticket_counts.emplace_back(
        counts.object_keys[index], counts.object_values[index].unsigned_integer);
  }

  const auto& ranges = member(root, "shard_ranges");
  require(ranges.type == JsonType::array && !ranges.array.empty() &&
              ranges.array.size() <= limits.shards,
          ErrorCode::proof_invalid, "proof shard range matrix is invalid");
  proof.shard_ranges.reserve(ranges.array.size());
  for (const auto& range : ranges.array) {
    require(range.type == JsonType::array && range.array.size() == 2U &&
                range.array[0].type == JsonType::unsigned_integer &&
                range.array[1].type == JsonType::unsigned_integer,
            ErrorCode::proof_invalid, "proof shard range has the wrong shape");
    proof.shard_ranges.emplace_back(
        range.array[0].unsigned_integer, range.array[1].unsigned_integer);
  }

  const auto& theorems = member(root, "theorems");
  require(theorems.type == JsonType::array && !theorems.array.empty() &&
              theorems.array.size() <= 16U,
          ErrorCode::proof_invalid, "proof theorem matrix is invalid");
  proof.theorem_bindings.reserve(theorems.array.size());
  for (const auto& theorem : theorems.array) {
    require_keys(theorem, {"conjuncts", "obligation_id"},
                 "proof theorem binding field set is invalid");
    proof.theorem_bindings.push_back(TheoremBinding{
        string_member(theorem, "obligation_id"), string_array(theorem, "conjuncts", 64U)});
  }
  validate_hierarchy_proof(topology, proof);
  return proof;
}

void validate_topology(const Topology& topology, const Limits& limits) {
  const auto context_ids = std::vector<std::string>{
      topology.context.accumulator_proof_instance_id,
      topology.context.coefficient_plan_root,
      topology.context.fixedpoint_config_id,
      topology.context.formal_semantics_id,
      topology.context.frozen_input_root,
      topology.context.parent_checkpoint_id,
      topology.context.profile_id,
      topology.context.round_config_id,
      topology.context.scale_table_id,
      topology.context.shard_plan_id,
      topology.topology_id,
  };
  require(std::all_of(context_ids.begin(), context_ids.end(), content_id_valid),
          ErrorCode::identifier_invalid, "topology contains an invalid content ID");
  require(topology.context.formal_semantics_id == delta::fixedpoint::formal_semantics_id() &&
              topology.context.profile_id == delta::fixedpoint::fixed_profile_id(),
          ErrorCode::context_mismatch, "topology formal or fixed-point identity is unsupported");
  require(topology.soft_deadline_tick < topology.hard_deadline_tick,
          ErrorCode::deadline_invalid, "soft deadline must precede hard deadline");
  require(!topology.domains.empty() && topology.domains.size() <= limits.domains,
          ErrorCode::partition_invalid, "topology domain count is invalid");
  require(!topology.shards.empty() && topology.shards.size() <= limits.shards,
          ErrorCode::shard_coverage_invalid, "topology shard count is invalid");

  std::set<std::string> domain_ids;
  std::set<std::string> all_validators;
  std::string prior_domain;
  for (const auto& domain : topology.domains) {
    require(label_valid(domain.domain_id) && domain_ids.insert(domain.domain_id).second,
            ErrorCode::partition_invalid, "domain IDs are invalid or duplicated");
    require(prior_domain.empty() || prior_domain < domain.domain_id,
            ErrorCode::partition_invalid, "domain array is not canonical");
    prior_domain = domain.domain_id;
    validate_sorted_labels(domain.tickets, "domain tickets are duplicated or noncanonical");
    validate_sorted_labels(
        domain.global_validator_set, "global validator set is duplicated or noncanonical");
    require(domain.global_fault_bound <= (std::numeric_limits<std::uint32_t>::max() - 1U) / 3U &&
                domain.global_validator_set.size() == 3U * domain.global_fault_bound + 1U,
            ErrorCode::committee_invalid, "global validator set is not exactly 3f+1");
    for (const auto& validator : domain.global_validator_set) {
      require(all_validators.insert(validator).second, ErrorCode::committee_invalid,
              "validator unexpectedly overlaps committee boundaries");
    }
    require(!domain.regions.empty() && domain.regions.size() <= limits.regions_per_domain,
            ErrorCode::partition_invalid, "domain region count is invalid");
    std::set<std::string> region_ids;
    std::vector<std::string> routed_tickets;
    for (const auto& region : domain.regions) {
      require(label_valid(region.region_id) && region_ids.insert(region.region_id).second,
              ErrorCode::partition_invalid, "region IDs are invalid or duplicated");
      validate_sorted_labels(region.tickets, "regional tickets are duplicated or noncanonical");
      validate_sorted_labels(
          region.validator_set, "regional validator set is duplicated or noncanonical");
      require(region.fault_bound <= (std::numeric_limits<std::uint32_t>::max() - 1U) / 3U &&
                  region.validator_set.size() == 3U * region.fault_bound + 1U,
              ErrorCode::committee_invalid, "regional validator set is not exactly 3f+1");
      for (const auto& validator : region.validator_set) {
        require(all_validators.insert(validator).second, ErrorCode::committee_invalid,
                "validator unexpectedly overlaps committee boundaries");
      }
      routed_tickets.insert(
          routed_tickets.end(), region.tickets.begin(), region.tickets.end());
    }
#if !defined(DELTA_HIERARCHY_MUTANT_SKIP_COVERAGE)
    std::sort(routed_tickets.begin(), routed_tickets.end());
    require(routed_tickets == domain.tickets, ErrorCode::partition_invalid,
            "regional routing is not an exact partition of domain tickets");
#endif
  }

  std::set<std::string> shard_ids;
  [[maybe_unused]] std::uint64_t expected_start = 0U;
  std::string prior_shard;
  for (const auto& shard : topology.shards) {
    require(label_valid(shard.shard_id) && shard_ids.insert(shard.shard_id).second,
            ErrorCode::shard_coverage_invalid, "shard IDs are invalid or duplicated");
    require(prior_shard.empty() || prior_shard < shard.shard_id,
            ErrorCode::shard_coverage_invalid, "shard array is not canonical");
#if !defined(DELTA_HIERARCHY_MUTANT_SKIP_SHARD_COVERAGE)
    require(shard.start_element == expected_start && shard.end_element > shard.start_element,
            ErrorCode::shard_coverage_invalid, "parameter shards contain a gap or overlap");
#endif
    require(shard.end_element <= delta::fixedpoint::max_total_elements,
            ErrorCode::shard_coverage_invalid,
            "parameter shard coverage exceeds the fixed-point profile limit");
    expected_start = shard.end_element;
    prior_shard = shard.shard_id;
  }
}

void validate_hierarchy_proof(
    const Topology& topology,
    const HierarchyProofInstance& proof) {
  validate_topology(topology);
  require(content_id_valid(proof.hierarchy_proof_instance_id) &&
              proof.topology_id == topology.topology_id && proof.context == topology.context,
          ErrorCode::proof_invalid, "hierarchy proof lineage does not match topology");
  require(proof.coefficient_abs_max > 0U &&
              proof.coefficient_abs_max <= static_cast<std::uint64_t>(INT64_MAX) &&
              proof.common_denominator > 0U &&
              proof.max_eligible_contributions > 0U && proof.q_abs_max > 0U &&
              proof.q_abs_max == static_cast<std::uint64_t>(delta::fixedpoint::q_max),
          ErrorCode::proof_invalid, "hierarchy proof numeric preconditions are invalid");

  const auto expected_product = proof_multiply(
      delta::core::arithmetic::Int128::from_u64(proof.q_abs_max),
      delta::core::arithmetic::Int128::from_u64(proof.coefficient_abs_max));
  [[maybe_unused]] const auto expected_final = proof_multiply(
      expected_product,
      delta::core::arithmetic::Int128::from_u64(proof.max_eligible_contributions));
#if !defined(DELTA_HIERARCHY_MUTANT_UNCHECKED_OVERFLOW)
  require(proof.product_abs_bound == expected_product && proof.final_abs_bound == expected_final &&
              !proof.product_abs_bound.negative() && !proof.final_abs_bound.negative() &&
              fits_width(proof.final_abs_bound, proof.selected_width),
          ErrorCode::proof_invalid, "hierarchy proof accumulator bounds are unsafe");
#endif

  require(proof.domain_ticket_counts.size() == topology.domains.size(),
          ErrorCode::proof_invalid, "hierarchy proof domain counts are incomplete");
  std::uint64_t maximum_count = 0U;
  for (std::size_t index = 0U; index < topology.domains.size(); ++index) {
    const auto& expected = topology.domains[index];
    const auto& actual = proof.domain_ticket_counts[index];
    require(actual.first == expected.domain_id && actual.second == expected.tickets.size(),
            ErrorCode::proof_invalid, "hierarchy proof domain count does not match topology");
    maximum_count = std::max(maximum_count, actual.second);
  }
  require(maximum_count == proof.max_eligible_contributions,
          ErrorCode::proof_invalid, "hierarchy proof maximum contribution count is not exact");
  require(proof.shard_ranges.size() == topology.shards.size(), ErrorCode::proof_invalid,
          "hierarchy proof shard ranges are incomplete");
  for (std::size_t index = 0U; index < topology.shards.size(); ++index) {
    require(proof.shard_ranges[index].first == topology.shards[index].start_element &&
                proof.shard_ranges[index].second == topology.shards[index].end_element,
            ErrorCode::proof_invalid, "hierarchy proof shard range does not match topology");
  }
  require(proof.theorem_bindings == required_theorem_bindings(), ErrorCode::proof_invalid,
          "hierarchy proof does not bind every normative theorem conjunct");
  static_cast<void>(absolute(proof.final_abs_bound));
}

BoundValidation validate_coefficient_plan(
    const Topology& topology,
    const HierarchyProofInstance& proof,
    std::span<const CoefficientBinding> coefficients) {
  validate_hierarchy_proof(topology, proof);
  std::vector<std::string> expected;
  std::vector<std::string> actual;
  for (const auto& domain : topology.domains) {
    for (const auto& ticket : domain.tickets) {
      expected.push_back(domain.domain_id + std::string(1U, '\x1f') + ticket);
    }
  }
  require(coefficients.size() == expected.size(), ErrorCode::contribution_invalid,
          "coefficient plan does not cover every ticket exactly once");
  actual.reserve(coefficients.size());
  std::uint64_t maximum_numerator = 0U;
  for (const auto& coefficient : coefficients) {
    actual.push_back(
        coefficient.domain_id + std::string(1U, '\x1f') + coefficient.ticket_id);
    require(coefficient.denominator > 0U &&
                proof.common_denominator % coefficient.denominator == 0U,
            ErrorCode::proof_invalid,
            "coefficient denominator is not positive or does not divide the common denominator");
    const auto magnitude = coefficient.numerator == INT64_MIN
                               ? UINT64_C(0x8000000000000000)
                               : static_cast<std::uint64_t>(
                                     coefficient.numerator < 0 ? -coefficient.numerator
                                                               : coefficient.numerator);
    require(std::gcd(magnitude, coefficient.denominator) == 1U,
            ErrorCode::proof_invalid, "coefficient rational is not canonical and reduced");
    require(magnitude <= proof.coefficient_abs_max, ErrorCode::proof_invalid,
            "coefficient exceeds theorem product bound");
    maximum_numerator = std::max(maximum_numerator, magnitude);
  }
  std::sort(expected.begin(), expected.end());
  std::sort(actual.begin(), actual.end());
  require(actual == expected, ErrorCode::contribution_invalid,
          "coefficient keys are duplicated, missing or outside the topology");

  std::uint64_t maximum_regional_terms = 0U;
  std::uint64_t maximum_global_terms = 0U;
  for (const auto& domain : topology.domains) {
    maximum_global_terms =
        std::max(maximum_global_terms, static_cast<std::uint64_t>(domain.tickets.size()));
    for (const auto& region : domain.regions) {
      maximum_regional_terms =
          std::max(maximum_regional_terms, static_cast<std::uint64_t>(region.tickets.size()));
    }
  }
  const auto maximum_product = proof_multiply(
      delta::core::arithmetic::Int128::from_u64(maximum_numerator),
      delta::core::arithmetic::Int128::from_u64(proof.q_abs_max));
  const auto maximum_accumulator = proof_multiply(
      maximum_product,
      delta::core::arithmetic::Int128::from_u64(maximum_global_terms));
#if !defined(DELTA_HIERARCHY_MUTANT_UNCHECKED_OVERFLOW)
  require(delta::core::arithmetic::compare(maximum_product, proof.product_abs_bound) <= 0 &&
              delta::core::arithmetic::compare(maximum_accumulator, proof.final_abs_bound) <= 0 &&
              maximum_global_terms <= proof.max_eligible_contributions &&
              fits_width(maximum_accumulator, proof.selected_width),
          ErrorCode::proof_invalid,
          "regional or global accumulator exceeds the frozen theorem instance");
#endif
  return BoundValidation{coefficients.size(), maximum_regional_terms, maximum_global_terms,
                         maximum_product, maximum_accumulator};
}

const Domain& require_domain(const Topology& topology, std::string_view domain_id) {
  const auto found = std::find_if(topology.domains.begin(), topology.domains.end(),
                                  [domain_id](const Domain& domain) {
                                    return domain.domain_id == domain_id;
                                  });
  require(found != topology.domains.end(), ErrorCode::contribution_invalid,
          "domain is absent from immutable topology");
  return *found;
}

const Region& require_region(const Domain& domain, std::string_view region_id) {
  const auto found = std::find_if(domain.regions.begin(), domain.regions.end(),
                                  [region_id](const Region& region) {
                                    return region.region_id == region_id;
                                  });
  require(found != domain.regions.end(), ErrorCode::contribution_invalid,
          "region is absent from immutable topology");
  return *found;
}

const ParameterShard& require_shard(const Topology& topology, std::string_view shard_id) {
  const auto found = std::find_if(topology.shards.begin(), topology.shards.end(),
                                  [shard_id](const ParameterShard& shard) {
                                    return shard.shard_id == shard_id;
                                  });
  require(found != topology.shards.end(), ErrorCode::contribution_invalid,
          "parameter shard is absent from immutable topology");
  return *found;
}

}  // namespace delta::reduce
