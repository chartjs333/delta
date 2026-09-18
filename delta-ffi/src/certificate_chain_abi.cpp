#include <delta_abi.h>

#include <delta/certificates/contracts.hpp>
#include <delta/certificates/verifier.hpp>
#include <delta/core/canonical.hpp>

#include <algorithm>
#include <charconv>
#include <cstddef>
#include <cstdint>
#include <initializer_list>
#include <limits>
#include <map>
#include <new>
#include <numeric>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <utility>
#include <vector>

namespace {

namespace certificates = delta::certificates;

constexpr std::size_t max_json_depth = 32U;
constexpr std::size_t max_json_nodes = 300'000U;
constexpr std::string_view bundle_domain =
    "deltareduce.010.native-chain-admission-bundle.v1";
constexpr std::string_view policy_domain =
    "deltareduce.010.certified-round-policy.v1";
constexpr std::string_view verifier_domain =
    "deltareduce.010.native-chain-verifier.v1";

class BundleError final : public std::runtime_error {
 public:
  explicit BundleError(std::string message) : std::runtime_error(std::move(message)) {}
};

[[noreturn]] void reject(const char* message) { throw BundleError(message); }

void require(bool condition, const char* message) {
  if (!condition) {
    reject(message);
  }
}

struct JsonValue final {
  enum class Kind { object, array, string, number, boolean };

  Kind kind{Kind::object};
  std::map<std::string, JsonValue> members;
  std::vector<JsonValue> elements;
  std::string text;
  std::uint64_t number{0U};
  bool boolean{false};
};

class CanonicalJsonParser final {
 public:
  explicit CanonicalJsonParser(std::string_view input) : input_(input) {}

  [[nodiscard]] JsonValue parse() {
    require(!input_.empty(), "bundle JSON is empty");
    auto result = value(0U);
    require(cursor_ == input_.size(), "bundle JSON has trailing bytes");
    return result;
  }

 private:
  [[nodiscard]] JsonValue value(std::size_t depth) {
    require(depth <= max_json_depth, "bundle JSON nesting exceeds bound");
    require(++nodes_ <= max_json_nodes, "bundle JSON node count exceeds bound");
    require(cursor_ < input_.size(), "bundle JSON is truncated");
    switch (input_[cursor_]) {
      case '{':
        return object(depth + 1U);
      case '[':
        return array(depth + 1U);
      case '"': {
        JsonValue result;
        result.kind = JsonValue::Kind::string;
        result.text = string();
        return result;
      }
      case 't':
        return literal("true", true);
      case 'f':
        return literal("false", false);
      default:
        return unsigned_number();
    }
  }

  [[nodiscard]] JsonValue object(std::size_t depth) {
    JsonValue result;
    result.kind = JsonValue::Kind::object;
    ++cursor_;
    if (take('}')) {
      return result;
    }
    std::string previous;
    while (true) {
      require(cursor_ < input_.size() && input_[cursor_] == '"', "object key is missing");
      auto key = string();
      require(previous.empty() || previous < key, "object keys are not canonical");
      previous = key;
      require(take(':'), "object colon is missing");
      const auto inserted = result.members.emplace(std::move(key), value(depth)).second;
      require(inserted, "object key is duplicated");
      if (take('}')) {
        return result;
      }
      require(take(','), "object comma is missing");
    }
  }

  [[nodiscard]] JsonValue array(std::size_t depth) {
    JsonValue result;
    result.kind = JsonValue::Kind::array;
    ++cursor_;
    if (take(']')) {
      return result;
    }
    while (true) {
      result.elements.push_back(value(depth));
      if (take(']')) {
        return result;
      }
      require(take(','), "array comma is missing");
    }
  }

  [[nodiscard]] std::string string() {
    require(take('"'), "string opener is missing");
    const auto begin = cursor_;
    while (cursor_ < input_.size() && input_[cursor_] != '"') {
      const auto byte = static_cast<unsigned char>(input_[cursor_]);
      require(
          byte >= 0x20U && byte <= 0x7eU && input_[cursor_] != '\\',
          "string is outside the canonical ASCII subset");
      ++cursor_;
    }
    require(cursor_ < input_.size(), "string is unterminated");
    auto result = std::string(input_.substr(begin, cursor_ - begin));
    ++cursor_;
    return result;
  }

  [[nodiscard]] JsonValue unsigned_number() {
    require(
        cursor_ < input_.size() && input_[cursor_] >= '0' && input_[cursor_] <= '9',
        "JSON number is not an unsigned integer");
    const auto begin = cursor_;
    while (cursor_ < input_.size() && input_[cursor_] >= '0' && input_[cursor_] <= '9') {
      ++cursor_;
    }
    const auto token = input_.substr(begin, cursor_ - begin);
    require(token == "0" || token.front() != '0', "JSON integer is not canonical");
    std::uint64_t parsed = 0U;
    const auto converted = std::from_chars(token.data(), token.data() + token.size(), parsed);
    require(
        converted.ec == std::errc{} && converted.ptr == token.data() + token.size(),
        "JSON integer is outside uint64");
    JsonValue result;
    result.kind = JsonValue::Kind::number;
    result.number = parsed;
    return result;
  }

  [[nodiscard]] JsonValue literal(std::string_view token, bool parsed) {
    require(input_.substr(cursor_, token.size()) == token, "JSON literal is invalid");
    cursor_ += token.size();
    JsonValue result;
    result.kind = JsonValue::Kind::boolean;
    result.boolean = parsed;
    return result;
  }

  [[nodiscard]] bool take(char expected) {
    if (cursor_ < input_.size() && input_[cursor_] == expected) {
      ++cursor_;
      return true;
    }
    return false;
  }

  std::string_view input_;
  std::size_t cursor_{0U};
  std::size_t nodes_{0U};
};

[[nodiscard]] std::string quote(std::string_view value) {
  require(
      std::all_of(value.begin(), value.end(), [](char character) {
        const auto byte = static_cast<unsigned char>(character);
        return byte >= 0x20U && byte <= 0x7eU && character != '"' && character != '\\';
      }),
      "receipt string is outside the canonical ASCII subset");
  return '"' + std::string(value) + '"';
}

[[nodiscard]] std::string canonical_json(const JsonValue& value) {
  switch (value.kind) {
    case JsonValue::Kind::object: {
      std::string result{"{"};
      for (const auto& [key, item] : value.members) {
        if (result.size() > 1U) {
          result.push_back(',');
        }
        result += quote(key) + ':' + canonical_json(item);
      }
      result.push_back('}');
      return result;
    }
    case JsonValue::Kind::array: {
      std::string result{"["};
      for (std::size_t index = 0U; index < value.elements.size(); ++index) {
        if (index != 0U) {
          result.push_back(',');
        }
        result += canonical_json(value.elements[index]);
      }
      result.push_back(']');
      return result;
    }
    case JsonValue::Kind::string:
      return quote(value.text);
    case JsonValue::Kind::number:
      return std::to_string(value.number);
    case JsonValue::Kind::boolean:
      return value.boolean ? "true" : "false";
  }
  reject("unknown JSON kind");
}

[[nodiscard]] const std::map<std::string, JsonValue>& object(const JsonValue& value) {
  require(value.kind == JsonValue::Kind::object, "JSON value is not an object");
  return value.members;
}

[[nodiscard]] const std::vector<JsonValue>& array(const JsonValue& value) {
  require(value.kind == JsonValue::Kind::array, "JSON value is not an array");
  return value.elements;
}

[[nodiscard]] const JsonValue& member(const JsonValue& value, std::string_view key) {
  const auto& values = object(value);
  const auto found = values.find(std::string(key));
  require(found != values.end(), "required JSON field is missing");
  return found->second;
}

void exact_fields(const JsonValue& value, std::initializer_list<std::string_view> keys) {
  const auto& values = object(value);
  require(values.size() == keys.size(), "JSON object field count is invalid");
  for (const auto key : keys) {
    require(values.contains(std::string(key)), "JSON object field set is invalid");
  }
}

[[nodiscard]] std::string text(const JsonValue& value) {
  require(value.kind == JsonValue::Kind::string, "JSON value is not a string");
  return value.text;
}

[[nodiscard]] std::uint64_t unsigned_integer(const JsonValue& value) {
  require(value.kind == JsonValue::Kind::number, "JSON value is not an unsigned integer");
  return value.number;
}

[[nodiscard]] std::uint32_t unsigned_32(const JsonValue& value) {
  const auto parsed = unsigned_integer(value);
  require(parsed <= std::numeric_limits<std::uint32_t>::max(), "integer is outside uint32");
  return static_cast<std::uint32_t>(parsed);
}

[[nodiscard]] bool boolean(const JsonValue& value) {
  require(value.kind == JsonValue::Kind::boolean, "JSON value is not a boolean");
  return value.boolean;
}

[[nodiscard]] std::int64_t signed_decimal(std::string_view value) {
  require(!value.empty(), "signed decimal is empty");
  std::int64_t parsed = 0;
  const auto converted = std::from_chars(value.data(), value.data() + value.size(), parsed);
  require(
      converted.ec == std::errc{} && converted.ptr == value.data() + value.size(),
      "signed decimal is outside int64");
  return parsed;
}

[[nodiscard]] std::vector<std::string> strings(const JsonValue& value) {
  std::vector<std::string> result;
  result.reserve(array(value).size());
  for (const auto& item : array(value)) {
    result.push_back(text(item));
  }
  return result;
}

[[nodiscard]] certificates::Context certificate_context(const JsonValue& value) {
  return {
      text(member(value, "arithmetic_profile_id")),
      unsigned_integer(member(value, "height")),
      text(member(value, "parameter_schema_id")),
      text(member(value, "round_config_id")),
      text(member(value, "round_id")),
      text(member(value, "validator_epoch_id")),
      unsigned_integer(member(value, "view")),
  };
}

[[nodiscard]] certificates::Rational rational(const JsonValue& value) {
  exact_fields(value, {"denominator", "numerator"});
  return {
      signed_decimal(text(member(value, "numerator"))),
      unsigned_integer(member(value, "denominator")),
  };
}

void exact_certificate_bytes(
    const JsonValue& value,
    std::span<const std::byte> expected) {
  const auto actual = canonical_json(value);
  require(actual.size() == expected.size(), "typed certificate field set is invalid");
  require(
      std::equal(
          expected.begin(), expected.end(), actual.begin(), [](std::byte left, char right) {
            return std::to_integer<unsigned char>(left) ==
                   static_cast<unsigned char>(right);
          }),
      "typed certificate bytes are not canonical");
}

[[nodiscard]] std::string content_id_for(
    std::string_view domain,
    std::string_view payload) {
  std::vector<std::byte> input;
  input.reserve(domain.size() + 1U + payload.size());
  for (const auto character : domain) {
    input.push_back(static_cast<std::byte>(character));
  }
  input.push_back(std::byte{0});
  for (const auto character : payload) {
    input.push_back(static_cast<std::byte>(character));
  }
  return "sha256:" + delta::core::canonical::sha256_hex(input);
}

[[nodiscard]] bool valid_hex_digest(std::string_view value) {
  return value.size() == 64U &&
         std::all_of(value.begin(), value.end(), [](char character) {
           return (character >= '0' && character <= '9') ||
                  (character >= 'a' && character <= 'f');
         });
}

[[nodiscard]] certificates::InputSetCertificate input_set(const JsonValue& value) {
  std::vector<certificates::InputTuple> tuples;
  for (const auto& item : array(member(value, "tuples"))) {
    tuples.push_back({
        text(member(item, "availability_certificate_id")),
        text(member(item, "commitment_id")),
        text(member(item, "domain_id")),
        text(member(item, "ticket_id")),
    });
  }
  certificates::InputSetCertificate result{
      certificate_context(value),
      text(member(value, "input_root")),
      unsigned_32(member(value, "quorum_threshold")),
      strings(member(value, "signer_ids")),
      std::move(tuples),
  };
  exact_certificate_bytes(value, certificates::canonical_json(result));
  return result;
}

[[nodiscard]] certificates::SeedTranscript seed_transcript(const JsonValue& value) {
  certificates::SeedTranscript result{
      certificate_context(value),
      text(member(value, "input_set_certificate_id")),
      text(member(value, "seed_id")),
      text(member(value, "seed_profile_id")),
      strings(member(value, "share_ids")),
  };
  exact_certificate_bytes(value, certificates::canonical_json(result));
  return result;
}

[[nodiscard]] certificates::NormEvidence norm_evidence(const JsonValue& value) {
  std::vector<certificates::NormEntry> entries;
  for (const auto& item : array(member(value, "entries"))) {
    entries.push_back({
        unsigned_integer(member(item, "scale_denominator")),
        text(member(item, "squared_norm")),
        text(member(item, "ticket_id")),
    });
  }
  certificates::NormEvidence result{
      certificate_context(value),
      std::move(entries),
      text(member(value, "input_set_certificate_id")),
      text(member(value, "norm_root")),
  };
  exact_certificate_bytes(value, certificates::canonical_json(result));
  return result;
}

[[nodiscard]] certificates::EligibilityCertificate eligibility(const JsonValue& value) {
  std::vector<certificates::EligibilityEntry> entries;
  for (const auto& item : array(member(value, "entries"))) {
    entries.push_back({
        boolean(member(item, "accepted")),
        text(member(item, "domain_id")),
        rational(member(item, "gamma")),
        text(member(item, "reason_code")),
        text(member(item, "ticket_id")),
    });
  }
  certificates::EligibilityCertificate result{
      certificate_context(value),
      std::move(entries),
      text(member(value, "input_set_certificate_id")),
      text(member(value, "norm_evidence_id")),
      unsigned_32(member(value, "quorum_threshold")),
      text(member(value, "robust_profile_id")),
      strings(member(value, "signer_ids")),
  };
  exact_certificate_bytes(value, certificates::canonical_json(result));
  return result;
}

[[nodiscard]] certificates::AggregationPlanCertificate aggregation_plan(
    const JsonValue& value) {
  std::vector<certificates::BucketAssignment> assignments;
  for (const auto& item : array(member(value, "bucket_assignments"))) {
    assignments.push_back({
        text(member(item, "bucket_id")),
        text(member(item, "ticket_id")),
    });
  }
  std::vector<certificates::Weight> weights;
  for (const auto& item : array(member(value, "weights"))) {
    weights.push_back({
        rational(member(item, "alpha")),
        text(member(item, "ticket_id")),
    });
  }
  certificates::AggregationPlanCertificate result{
      certificate_context(value),
      text(member(value, "accumulator_proof_id")),
      std::move(assignments),
      text(member(value, "eligibility_certificate_id")),
      text(member(value, "input_set_certificate_id")),
      unsigned_32(member(value, "iteration_count")),
      unsigned_32(member(value, "quorum_threshold")),
      text(member(value, "seed_transcript_id")),
      strings(member(value, "signer_ids")),
      text(member(value, "transcript_root")),
      std::move(weights),
  };
  exact_certificate_bytes(value, certificates::canonical_json(result));
  return result;
}

[[nodiscard]] certificates::ParameterShardQc parameter_shard(const JsonValue& value) {
  certificates::ParameterShardQc result{
      certificate_context(value),
      text(member(value, "aggregation_plan_certificate_id")),
      unsigned_integer(member(value, "denominator")),
      text(member(value, "domain_id")),
      text(member(value, "eligibility_certificate_id")),
      strings(member(value, "input_leaf_ids")),
      text(member(value, "input_set_certificate_id")),
      unsigned_32(member(value, "quorum_threshold")),
      strings(member(value, "result_numerators")),
      text(member(value, "shard_id")),
      strings(member(value, "signer_ids")),
  };
  exact_certificate_bytes(value, certificates::canonical_json(result));
  return result;
}

[[nodiscard]] certificates::AggregateRootQc aggregate_root(const JsonValue& value) {
  std::vector<certificates::RootLeaf> leaves;
  for (const auto& item : array(member(value, "leaves"))) {
    leaves.push_back({
        text(member(item, "domain_id")),
        text(member(item, "parameter_shard_qc_id")),
        text(member(item, "shard_id")),
    });
  }
  std::vector<certificates::ShardKey> required;
  for (const auto& item : array(member(value, "required_keys"))) {
    required.push_back({
        text(member(item, "domain_id")),
        text(member(item, "shard_id")),
    });
  }
  certificates::AggregateRootQc result{
      certificate_context(value),
      text(member(value, "aggregation_plan_certificate_id")),
      text(member(value, "eligibility_certificate_id")),
      text(member(value, "input_set_certificate_id")),
      std::move(leaves),
      text(member(value, "merkle_root")),
      unsigned_32(member(value, "quorum_threshold")),
      std::move(required),
      strings(member(value, "signer_ids")),
  };
  exact_certificate_bytes(value, certificates::canonical_json(result));
  return result;
}

[[nodiscard]] certificates::ApplyArithmeticProfile apply_profile(const JsonValue& value) {
  std::vector<certificates::DomainWeight> weights;
  for (const auto& item : array(member(value, "domain_weights"))) {
    weights.push_back({
        text(member(item, "domain_id")),
        rational(member(item, "pi")),
    });
  }
  certificates::ApplyArithmeticProfile result{
      text(member(value, "accumulator_proof_id")),
      std::move(weights),
      rational(member(value, "learning_rate")),
      rational(member(value, "momentum")),
      boolean(member(value, "nesterov")),
      text(member(value, "rounding")),
      rational(member(value, "weight_decay")),
  };
  exact_certificate_bytes(value, certificates::canonical_json(result));
  return result;
}

[[nodiscard]] certificates::ApplyCandidate apply_candidate(const JsonValue& value) {
  certificates::ApplyCandidate result{
      certificate_context(value),
      text(member(value, "aggregate_root_qc_id")),
      text(member(value, "apply_arithmetic_profile_id")),
      text(member(value, "next_model_hash")),
      strings(member(value, "next_model_values")),
      text(member(value, "next_optimizer_hash")),
      strings(member(value, "next_optimizer_values")),
      text(member(value, "parent_checkpoint_id")),
      text(member(value, "parent_optimizer_hash")),
  };
  exact_certificate_bytes(value, certificates::canonical_json(result));
  return result;
}

[[nodiscard]] certificates::ApplyQc apply_qc(const JsonValue& value) {
  certificates::ApplyQc result{
      certificate_context(value),
      text(member(value, "aggregate_root_qc_id")),
      text(member(value, "apply_arithmetic_profile_id")),
      text(member(value, "apply_candidate_id")),
      text(member(value, "next_model_hash")),
      text(member(value, "next_optimizer_hash")),
      text(member(value, "parent_checkpoint_id")),
      unsigned_32(member(value, "quorum_threshold")),
      strings(member(value, "signer_ids")),
  };
  exact_certificate_bytes(value, certificates::canonical_json(result));
  return result;
}

[[nodiscard]] certificates::CurrentPointerCommand current_pointer(const JsonValue& value) {
  certificates::CurrentPointerCommand result{
      certificate_context(value),
      text(member(value, "apply_qc_id")),
      text(member(value, "expected_parent_checkpoint_id")),
      text(member(value, "next_checkpoint_id")),
      text(member(value, "next_optimizer_hash")),
  };
  exact_certificate_bytes(value, certificates::canonical_json(result));
  return result;
}

struct CertifiedPolicy final {
  certificates::Context context;
  std::string accumulator_proof_id;
  std::string apply_arithmetic_profile_id;
  certificates::ValidatorPolicy validators;
  std::vector<certificates::ShardKey> required_shards;
  std::string content_id;
};

[[nodiscard]] CertifiedPolicy certified_policy(const JsonValue& value) {
  exact_fields(
      value,
      {
          "accumulator_proof_id",
          "apply_arithmetic_profile_id",
          "arithmetic_profile_id",
          "height",
          "parameter_schema_id",
          "quorum_threshold",
          "required_shards",
          "round_config_id",
          "round_id",
          "validator_epoch_id",
          "validator_ids",
          "view",
      });
  std::vector<certificates::ShardKey> required;
  for (const auto& item : array(member(value, "required_shards"))) {
    exact_fields(item, {"domain_id", "shard_id"});
    required.push_back({text(member(item, "domain_id")), text(member(item, "shard_id"))});
  }
  const auto policy_bytes = canonical_json(value);
  auto context = certificate_context(value);
  return {
      context,
      text(member(value, "accumulator_proof_id")),
      text(member(value, "apply_arithmetic_profile_id")),
      {
          context.validator_epoch_id,
          strings(member(value, "validator_ids")),
          unsigned_32(member(value, "quorum_threshold")),
      },
      std::move(required),
      content_id_for(policy_domain, policy_bytes),
  };
}

[[nodiscard]] std::vector<certificates::InputTuple> expected_inputs(const JsonValue& value) {
  std::vector<certificates::InputTuple> result;
  for (const auto& item : array(value)) {
    exact_fields(
        item,
        {
            "availability_certificate_id",
            "commitment_id",
            "domain_id",
            "ticket_id",
        });
    result.push_back({
        text(member(item, "availability_certificate_id")),
        text(member(item, "commitment_id")),
        text(member(item, "domain_id")),
        text(member(item, "ticket_id")),
    });
  }
  require(!result.empty(), "expected input set is empty");
  for (std::size_t index = 1U; index < result.size(); ++index) {
    require(
        std::tie(result[index - 1U].ticket_id, result[index - 1U].commitment_id) <
            std::tie(result[index].ticket_id, result[index].commitment_id),
        "expected input set is not canonical");
  }
  return result;
}

void validate_ordered_contributions(const JsonValue& value) {
  std::string prior_ticket;
  std::vector<std::string> contribution_ids;
  for (const auto& item : array(value)) {
    exact_fields(item, {"contribution_id", "ticket_id"});
    const auto ticket_id = text(member(item, "ticket_id"));
    const auto contribution_id = text(member(item, "contribution_id"));
    require(certificates::is_content_id(ticket_id), "ordered ticket ID is invalid");
    require(certificates::is_content_id(contribution_id), "ordered contribution ID is invalid");
    require(prior_ticket.empty() || prior_ticket < ticket_id, "ordered tickets are not canonical");
    prior_ticket = ticket_id;
    contribution_ids.push_back(contribution_id);
  }
  require(!contribution_ids.empty(), "ordered contribution set is empty");
  std::sort(contribution_ids.begin(), contribution_ids.end());
  require(
      std::adjacent_find(contribution_ids.begin(), contribution_ids.end()) ==
          contribution_ids.end(),
      "ordered contribution set contains duplicates");
}

[[nodiscard]] bool valid_view(delta_bytes_view_t view) noexcept {
  return view.data != nullptr || view.size == 0U;
}

[[nodiscard]] std::string view_text(delta_bytes_view_t view) {
  require(valid_view(view), "ABI byte view is invalid");
  return {reinterpret_cast<const char*>(view.data), view.size};
}

[[nodiscard]] bool equals(delta_bytes_view_t view, std::string_view expected) noexcept {
  if (!valid_view(view) || view.size != expected.size()) {
    return false;
  }
  if (view.size == 0U) {
    return true;
  }
  return std::equal(
      view.data,
      view.data + view.size,
      expected.begin(),
      [](std::uint8_t left, char right) {
        return left == static_cast<std::uint8_t>(static_cast<unsigned char>(right));
      });
}

void reset(delta_output_buffer_t* output) noexcept {
  if (output != nullptr) {
    output->required = 0U;
    output->written = 0U;
  }
}

[[nodiscard]] delta_status_t write(
    std::string_view value,
    delta_output_buffer_t* output) noexcept {
  if (output == nullptr) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  output->required = value.size();
  if (output->capacity < value.size()) {
    return DELTA_STATUS_BUFFER_TOO_SMALL;
  }
  if (!value.empty() && output->data == nullptr) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  std::copy(value.begin(), value.end(), reinterpret_cast<char*>(output->data));
  output->written = value.size();
  return DELTA_STATUS_OK;
}

[[nodiscard]] std::string native_verifier_id() {
  const auto identity =
      std::string{"{\"formal_semantics_id\":"} + quote(DELTA_FORMAL_SEMANTICS_ID) +
      ",\"native_build_id\":" + quote(DELTA_BUILD_ID) +
      ",\"type_name\":\"DELTA_CERTIFICATE_CHAIN_VERIFIER\"}";
  return content_id_for(verifier_domain, identity);
}

[[nodiscard]] std::string receipt_json(
    std::string_view bundle_id,
    std::string_view policy_id,
    std::string_view execution_plan_id,
    std::string_view input_set_certificate_id,
    std::string_view aggregate_root_qc_id,
    std::string_view apply_qc_id,
    std::string_view final_checkpoint_id,
    std::string_view runtime_state_id,
    std::string_view effect_set_id,
    std::string_view runtime_wal_sha256,
    std::string_view checkpoint_wal_sha256) {
  return std::string{"{\"aggregate_root_qc_id\":"} + quote(aggregate_root_qc_id) +
         ",\"apply_qc_id\":" + quote(apply_qc_id) +
         ",\"certificate_bundle_id\":" + quote(bundle_id) +
         ",\"certified_round_policy_id\":" + quote(policy_id) +
         ",\"checkpoint_wal_sha256\":" + quote(checkpoint_wal_sha256) +
         ",\"effect_set_id\":" + quote(effect_set_id) +
         ",\"execution_plan_id\":" + quote(execution_plan_id) +
         ",\"final_checkpoint_id\":" + quote(final_checkpoint_id) +
         ",\"formal_semantics_id\":" + quote(DELTA_FORMAL_SEMANTICS_ID) +
         ",\"input_set_certificate_id\":" + quote(input_set_certificate_id) +
         ",\"native_build_id\":" + quote(DELTA_BUILD_ID) +
         ",\"native_chain_verifier_id\":" + quote(native_verifier_id()) +
         ",\"runtime_state_id\":" + quote(runtime_state_id) +
         ",\"runtime_wal_sha256\":" + quote(runtime_wal_sha256) +
         ",\"schema_version\":\"1.0.0\",\"status\":\"ACCEPT\","
         "\"type_name\":\"CAMPAIGN02_NATIVE_CHAIN_ADMISSION_RECEIPT\"}";
}

[[nodiscard]] delta_status_t validate_abi_context(
    const delta_certificate_chain_context_t* context) noexcept {
  if (context == nullptr ||
      context->struct_size != DELTA_CERTIFICATE_CHAIN_CONTEXT_SIZE ||
      context->reserved != 0U) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  if (!equals(context->expected_formal_semantics_id, DELTA_FORMAL_SEMANTICS_ID)) {
    return DELTA_STATUS_FORMAL_SEMANTICS_MISMATCH;
  }
  if (!equals(context->expected_native_build_id, DELTA_BUILD_ID)) {
    return DELTA_STATUS_BUILD_MISMATCH;
  }
  const auto content_views = {
      context->expected_execution_plan_id,
      context->expected_certified_round_policy_id,
      context->expected_parent_checkpoint_id,
      context->expected_final_checkpoint_id,
      context->expected_runtime_state_id,
      context->expected_effect_set_id,
  };
  for (const auto value : content_views) {
    if (!valid_view(value) ||
        !certificates::is_content_id(
            {reinterpret_cast<const char*>(value.data), value.size})) {
      return DELTA_STATUS_INVALID_ARGUMENT;
    }
  }
  const auto runtime_wal = context->expected_runtime_wal_sha256;
  const auto checkpoint_wal = context->expected_checkpoint_wal_sha256;
  if (!valid_view(runtime_wal) || !valid_view(checkpoint_wal) ||
      !valid_hex_digest(
          {reinterpret_cast<const char*>(runtime_wal.data), runtime_wal.size}) ||
      !valid_hex_digest(
          {reinterpret_cast<const char*>(checkpoint_wal.data), checkpoint_wal.size})) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  return DELTA_STATUS_OK;
}

[[nodiscard]] std::string verify_bundle(
    const delta_certificate_chain_context_t& expected,
    std::string_view canonical_bundle) {
  require(
      !canonical_bundle.empty() &&
          canonical_bundle.size() <= certificates::max_contract_bytes,
      "certificate bundle size is invalid");
  const auto document = CanonicalJsonParser(canonical_bundle).parse();
  require(canonical_json(document) == canonical_bundle, "certificate bundle is not canonical");
  exact_fields(
      document,
      {
          "aggregate_root_qc",
          "aggregation_plan_certificate",
          "apply_arithmetic_profile",
          "apply_candidate",
          "apply_qc",
          "checkpoint_wal_sha256",
          "current_pointer_command",
          "effect_set_id",
          "eligibility_certificate",
          "execution_plan_id",
          "expected_input_tuples",
          "final_checkpoint_id",
          "formal_semantics_id",
          "input_set_certificate",
          "norm_evidence",
          "ordered_contributions",
          "parameter_shard_qcs",
          "parent_checkpoint_id",
          "policy",
          "runtime_state_id",
          "runtime_wal_sha256",
          "schema_version",
          "seed_transcript",
          "terminal_outcome",
          "type_name",
      });
  require(
      text(member(document, "formal_semantics_id")) == DELTA_FORMAL_SEMANTICS_ID &&
          text(member(document, "schema_version")) == "1.0.0" &&
          text(member(document, "type_name")) ==
              "CAMPAIGN02_NATIVE_CHAIN_ADMISSION_BUNDLE" &&
          text(member(document, "terminal_outcome")) == "APPLIED",
      "certificate bundle envelope is incompatible");

  const auto execution_plan_id = text(member(document, "execution_plan_id"));
  const auto parent_checkpoint_id = text(member(document, "parent_checkpoint_id"));
  const auto final_checkpoint_id = text(member(document, "final_checkpoint_id"));
  const auto runtime_state_id = text(member(document, "runtime_state_id"));
  const auto effect_set_id = text(member(document, "effect_set_id"));
  const auto runtime_wal_sha256 = text(member(document, "runtime_wal_sha256"));
  const auto checkpoint_wal_sha256 = text(member(document, "checkpoint_wal_sha256"));
  require(
      equals(expected.expected_execution_plan_id, execution_plan_id) &&
          equals(expected.expected_parent_checkpoint_id, parent_checkpoint_id) &&
          equals(expected.expected_final_checkpoint_id, final_checkpoint_id) &&
          equals(expected.expected_runtime_state_id, runtime_state_id) &&
          equals(expected.expected_effect_set_id, effect_set_id) &&
          equals(expected.expected_runtime_wal_sha256, runtime_wal_sha256) &&
          equals(expected.expected_checkpoint_wal_sha256, checkpoint_wal_sha256),
      "certificate bundle does not match the expected run context");
  require(
      certificates::is_content_id(execution_plan_id) &&
          certificates::is_content_id(parent_checkpoint_id) &&
          certificates::is_content_id(final_checkpoint_id) &&
          certificates::is_content_id(runtime_state_id) &&
          certificates::is_content_id(effect_set_id) &&
          valid_hex_digest(runtime_wal_sha256) && valid_hex_digest(checkpoint_wal_sha256),
      "certificate bundle run identity is invalid");

  const auto policy = certified_policy(member(document, "policy"));
  require(
      equals(expected.expected_certified_round_policy_id, policy.content_id),
      "certificate bundle policy identity mismatch");
  auto verifier = certificates::ChainVerifier(policy.context, policy.validators);

  const auto isc = input_set(member(document, "input_set_certificate"));
  const auto expected_isc = expected_inputs(member(document, "expected_input_tuples"));
  require(isc.tuples == expected_isc, "ISC does not match the expected input set");
  validate_ordered_contributions(member(document, "ordered_contributions"));
  require(
      array(member(document, "ordered_contributions")).size() == expected_isc.size(),
      "ordered contribution count differs from ISC membership");
  for (std::size_t index = 0U; index < expected_isc.size(); ++index) {
    require(
        text(member(array(member(document, "ordered_contributions"))[index], "ticket_id")) ==
            expected_isc[index].ticket_id,
        "ordered contribution ticket differs from ISC membership");
  }
  const auto isc_id = verifier.verify_input_set(isc);

  const auto seed = seed_transcript(member(document, "seed_transcript"));
  const auto seed_id = verifier.verify_seed(seed, isc_id);
  const auto norms = norm_evidence(member(document, "norm_evidence"));
  const auto norms_id = verifier.verify_norms(norms, isc_id);
  const auto ec = eligibility(member(document, "eligibility_certificate"));
  const auto ec_id = verifier.verify_eligibility(ec, isc, norms_id);
  const auto apc = aggregation_plan(member(document, "aggregation_plan_certificate"));
  const auto apc_id = verifier.verify_plan(
      apc, isc, ec, seed_id, policy.accumulator_proof_id);

  std::vector<certificates::ParameterShardQc> shards;
  for (const auto& item : array(member(document, "parameter_shard_qcs"))) {
    shards.push_back(parameter_shard(item));
  }
  const auto root = aggregate_root(member(document, "aggregate_root_qc"));
  const auto root_id = verifier.verify_root(
      root, isc_id, ec_id, apc_id, policy.required_shards, shards);

  const auto profile = apply_profile(member(document, "apply_arithmetic_profile"));
  const auto profile_id = certificates::content_id(profile);
  require(
      profile_id == policy.apply_arithmetic_profile_id,
      "apply profile differs from certified policy");
  const auto candidate = apply_candidate(member(document, "apply_candidate"));
  const auto apply = apply_qc(member(document, "apply_qc"));
  const auto apply_id = verifier.verify_apply(apply, candidate, root_id, profile_id);
  require(
      candidate.parent_checkpoint_id == parent_checkpoint_id &&
          apply.parent_checkpoint_id == parent_checkpoint_id &&
          apply.next_model_hash == final_checkpoint_id,
      "ApplyQC does not bind the expected parent/final checkpoint");

  const auto pointer = current_pointer(member(document, "current_pointer_command"));
  require(
      pointer.context == policy.context && pointer.apply_qc_id == apply_id &&
          pointer.expected_parent_checkpoint_id == parent_checkpoint_id &&
          pointer.next_checkpoint_id == final_checkpoint_id &&
          pointer.next_optimizer_hash == apply.next_optimizer_hash,
      "current pointer command does not descend from ApplyQC");
  static_cast<void>(certificates::content_id(pointer));

  const auto bundle_id = content_id_for(bundle_domain, canonical_bundle);
  return receipt_json(
      bundle_id,
      policy.content_id,
      execution_plan_id,
      isc_id,
      root_id,
      apply_id,
      final_checkpoint_id,
      runtime_state_id,
      effect_set_id,
      runtime_wal_sha256,
      checkpoint_wal_sha256);
}

template <typename Operation>
[[nodiscard]] delta_status_t boundary(Operation operation) noexcept {
  try {
    return operation();
  } catch (const BundleError&) {
    return DELTA_STATUS_TRANSITION_REJECTED;
  } catch (const certificates::CertificateError&) {
    return DELTA_STATUS_TRANSITION_REJECTED;
  } catch (const std::bad_alloc&) {
    return DELTA_STATUS_INTERNAL_ERROR;
  } catch (...) {
    return DELTA_STATUS_INTERNAL_ERROR;
  }
}

[[nodiscard]] delta_status_t verify_common(
    const delta_certificate_chain_context_t* context,
    std::string_view canonical_bundle,
    delta_output_buffer_t* output) noexcept {
  const auto context_status = validate_abi_context(context);
  if (context_status != DELTA_STATUS_OK || output == nullptr) {
    return context_status == DELTA_STATUS_OK ? DELTA_STATUS_INVALID_ARGUMENT : context_status;
  }
  return boundary([&]() {
    const auto receipt = verify_bundle(*context, canonical_bundle);
    return write(receipt, output);
  });
}

static_assert(sizeof(void*) == 8U, "certificate chain ABI requires a 64-bit process");
static_assert(sizeof(delta_certificate_chain_context_t) == DELTA_CERTIFICATE_CHAIN_CONTEXT_SIZE);

}  // namespace

extern "C" {

delta_status_t delta_certificate_chain_verify_borrowed(
    const delta_certificate_chain_context_t* context,
    delta_bytes_view_t canonical_bundle,
    delta_output_buffer_t* receipt_output) noexcept {
  reset(receipt_output);
  if (!valid_view(canonical_bundle) ||
      canonical_bundle.size > certificates::max_contract_bytes) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  return verify_common(
      context,
      {reinterpret_cast<const char*>(canonical_bundle.data), canonical_bundle.size},
      receipt_output);
}

delta_status_t delta_certificate_chain_verify_copy(
    const delta_certificate_chain_context_t* context,
    delta_bytes_view_t canonical_bundle,
    delta_output_buffer_t* receipt_output) noexcept {
  reset(receipt_output);
  if (!valid_view(canonical_bundle) ||
      canonical_bundle.size > certificates::max_contract_bytes) {
    return DELTA_STATUS_INVALID_ARGUMENT;
  }
  return boundary([&]() {
    const auto copied = view_text(canonical_bundle);
    return verify_common(context, copied, receipt_output);
  });
}

}  // extern "C"
