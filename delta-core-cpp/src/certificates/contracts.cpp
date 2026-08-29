#include <delta/certificates/contracts.hpp>

#include <delta/core/canonical.hpp>

#include <algorithm>
#include <cctype>
#include <charconv>
#include <cstddef>
#include <cstdint>
#include <numeric>
#include <span>
#include <string>
#include <string_view>
#include <tuple>
#include <utility>
#include <vector>

namespace delta::certificates {
namespace {

[[noreturn]] void reject(ErrorCode code, std::string message) {
  throw CertificateError(code, std::move(message));
}

void require(bool condition, ErrorCode code, const char* message) {
  if (!condition) {
    reject(code, message);
  }
}

[[nodiscard]] std::uint64_t magnitude(std::int64_t value) noexcept {
  return value >= 0 ? static_cast<std::uint64_t>(value)
                    : static_cast<std::uint64_t>(-(value + 1)) + 1U;
}

[[nodiscard]] std::string quote(std::string_view value) {
  require(
      std::all_of(value.begin(), value.end(), [](char character) {
        const auto byte = static_cast<unsigned char>(character);
        return byte >= 0x20U && byte <= 0x7eU && character != '"' && character != '\\';
      }),
      ErrorCode::identifier_invalid,
      "canonical certificate string is outside the ASCII subset");
  return '"' + std::string(value) + '"';
}

[[nodiscard]] std::string number(std::int64_t value) { return std::to_string(value); }

[[nodiscard]] std::string number(std::uint64_t value) { return std::to_string(value); }

[[nodiscard]] std::string number(std::uint32_t value) { return std::to_string(value); }

[[nodiscard]] std::string boolean(bool value) { return value ? "true" : "false"; }

void field(std::string& output, std::string_view key, std::string value) {
  if (output.size() > 1U) {
    output.push_back(',');
  }
  output += quote(key);
  output.push_back(':');
  output += std::move(value);
}

[[nodiscard]] std::string string_array(const std::vector<std::string>& values) {
  std::string output{"["};
  for (std::size_t index = 0U; index < values.size(); ++index) {
    if (index != 0U) {
      output.push_back(',');
    }
    output += quote(values[index]);
  }
  output.push_back(']');
  return output;
}

template <typename Item, typename Encoder>
[[nodiscard]] std::string object_array(const std::vector<Item>& values, Encoder encoder) {
  std::string output{"["};
  for (std::size_t index = 0U; index < values.size(); ++index) {
    if (index != 0U) {
      output.push_back(',');
    }
    output += encoder(values[index]);
  }
  output.push_back(']');
  return output;
}

[[nodiscard]] std::string rational_json(const Rational& value) {
  validate_rational(value);
  return "{\"denominator\":" + number(value.denominator) +
         ",\"numerator\":" + quote(number(value.numerator)) + '}';
}

[[nodiscard]] core::canonical::Bytes bytes(std::string value) {
  const auto view = std::as_bytes(std::span(value.data(), value.size()));
  return {view.begin(), view.end()};
}

[[nodiscard]] std::string id_for(
    std::string_view domain,
    std::span<const std::byte> canonical_json) {
  std::vector<std::byte> input;
  input.reserve(domain.size() + 1U + canonical_json.size());
  for (const char character : domain) {
    input.push_back(static_cast<std::byte>(character));
  }
  input.push_back(std::byte{0});
  input.insert(input.end(), canonical_json.begin(), canonical_json.end());
  return "sha256:" + core::canonical::sha256_hex(input);
}

[[nodiscard]] std::vector<std::byte> digest_bytes(std::string_view content_id) {
  require(
      content_id.size() == 71U && content_id.starts_with("sha256:"),
      ErrorCode::identifier_invalid,
      "Merkle digest ID is invalid");
  std::vector<std::byte> result;
  result.reserve(32U);
  for (std::size_t index = 7U; index < content_id.size(); index += 2U) {
    const auto nibble = [](char digit) -> std::uint8_t {
      return static_cast<std::uint8_t>(
          digit <= '9' ? digit - '0' : 10 + digit - 'a');
    };
    result.push_back(static_cast<std::byte>(
        static_cast<std::uint8_t>((nibble(content_id[index]) << 4U) |
                                  nibble(content_id[index + 1U]))));
  }
  return result;
}

void require_bounded(std::size_t count, const char* message) {
  require(
      count > 0U && count <= max_certificate_entries,
      ErrorCode::limit_exceeded,
      message);
}

void require_content(std::string_view value, const char* message) {
  require(is_content_id(value), ErrorCode::identifier_invalid, message);
}

void require_label(std::string_view value, const char* message) {
  require(is_label(value), ErrorCode::identifier_invalid, message);
}

void require_decimal(std::string_view value, bool non_negative, const char* message) {
  require(!value.empty(), ErrorCode::arithmetic_invalid, message);
  require(
      value == "0" || (value.front() != '0' && value != "-0"),
      ErrorCode::arithmetic_invalid,
      message);
  std::int64_t parsed = 0;
  const auto result = std::from_chars(value.data(), value.data() + value.size(), parsed);
  require(
      result.ec == std::errc{} && result.ptr == value.data() + value.size() &&
          (!non_negative || parsed >= 0),
      ErrorCode::arithmetic_invalid,
      message);
}

void validate_context_values(const Context& value) {
  require_content(value.arithmetic_profile_id, "arithmetic profile ID is invalid");
  require(value.height > 0U, ErrorCode::context_mismatch, "height is zero");
  require_content(value.parameter_schema_id, "parameter schema ID is invalid");
  require_content(value.round_config_id, "round config ID is invalid");
  require_label(value.round_id, "round ID is invalid");
  require_content(value.validator_epoch_id, "validator epoch ID is invalid");
}

template <typename Item, typename Projection>
void require_strict_order(
    const std::vector<Item>& values,
    Projection projection,
    const char* message) {
  for (std::size_t index = 1U; index < values.size(); ++index) {
    require(
        projection(values[index - 1U]) < projection(values[index]),
        ErrorCode::order_invalid,
        message);
  }
}

void validate_signers(const std::vector<std::string>& signers, std::uint32_t threshold) {
  require_bounded(signers.size(), "signer set is empty or too large");
  require(
      threshold > 0U && signers.size() >= threshold,
      ErrorCode::quorum_invalid,
      "signer set is below quorum");
  require_strict_order(signers, [](const auto& value) { return value; }, "signers not ordered");
  for (const auto& signer : signers) {
    require_label(signer, "signer ID is invalid");
  }
}

}  // namespace

CertificateError::CertificateError(ErrorCode code, std::string message)
    : std::runtime_error(std::move(message)), code_(code) {}

ErrorCode CertificateError::code() const noexcept { return code_; }

bool ShardKey::operator<(const ShardKey& other) const noexcept {
  return std::tie(domain_id, shard_id) < std::tie(other.domain_id, other.shard_id);
}

bool is_content_id(std::string_view value) noexcept {
  return value.size() == 71U && value.starts_with("sha256:") &&
         std::all_of(value.begin() + 7, value.end(), [](char character) {
           return (character >= '0' && character <= '9') ||
                  (character >= 'a' && character <= 'f');
         });
}

bool is_label(std::string_view value) noexcept {
  return !value.empty() && value.size() <= 128U &&
         std::all_of(value.begin(), value.end(), [](char character) {
           return std::isalnum(static_cast<unsigned char>(character)) != 0 || character == '.' ||
                  character == '_' || character == ':' || character == '-';
         });
}

void validate_context(const Context& actual, const Context& expected) {
  validate_context_values(actual);
  require(actual == expected, ErrorCode::context_mismatch, "certificate context mismatch");
}

void validate_rational(const Rational& value, bool non_negative) {
  require(value.denominator > 0U, ErrorCode::arithmetic_invalid, "rational denominator is zero");
  require(
      !non_negative || value.numerator >= 0,
      ErrorCode::arithmetic_invalid,
      "rational must be non-negative");
  require(
      std::gcd(magnitude(value.numerator), value.denominator) == 1U,
      ErrorCode::arithmetic_invalid,
      "rational is not canonically reduced");
}

core::canonical::Bytes canonical_json(const InputSetCertificate& value) {
  validate_context_values(value.context);
  require_content(value.input_root, "input root is invalid");
  validate_signers(value.signer_ids, value.quorum_threshold);
  require_bounded(value.tuples.size(), "input tuple set is empty or too large");
  require_strict_order(
      value.tuples,
      [](const InputTuple& item) { return std::tie(item.ticket_id, item.commitment_id); },
      "input tuple set is not canonical");
  const auto tuples = object_array(value.tuples, [](const InputTuple& item) {
    require_content(item.availability_certificate_id, "availability certificate ID invalid");
    require_content(item.commitment_id, "commitment ID invalid");
    require_label(item.domain_id, "domain ID invalid");
    require_label(item.ticket_id, "ticket ID invalid");
    return "{\"availability_certificate_id\":" + quote(item.availability_certificate_id) +
           ",\"commitment_id\":" + quote(item.commitment_id) +
           ",\"domain_id\":" + quote(item.domain_id) +
           ",\"ticket_id\":" + quote(item.ticket_id) + '}';
  });
  std::string output{"{"};
  field(output, "arithmetic_profile_id", quote(value.context.arithmetic_profile_id));
  field(output, "formal_semantics_id", quote(formal_semantics_id));
  field(output, "height", number(value.context.height));
  field(output, "input_root", quote(value.input_root));
  field(output, "parameter_schema_id", quote(value.context.parameter_schema_id));
  field(output, "quorum_threshold", number(value.quorum_threshold));
  field(output, "round_config_id", quote(value.context.round_config_id));
  field(output, "round_id", quote(value.context.round_id));
  field(output, "schema_version", quote(schema_version));
  field(output, "signer_ids", string_array(value.signer_ids));
  field(output, "tuples", tuples);
  field(output, "type_name", quote("INPUT_SET_CERTIFICATE"));
  field(output, "validator_epoch_id", quote(value.context.validator_epoch_id));
  field(output, "view", number(value.context.view));
  output.push_back('}');
  return bytes(std::move(output));
}

core::canonical::Bytes canonical_json(const SeedTranscript& value) {
  validate_context_values(value.context);
  require_content(value.input_set_certificate_id, "ISC ID invalid");
  require_content(value.seed_id, "seed ID invalid");
  require_content(value.seed_profile_id, "seed profile ID invalid");
  require_bounded(value.share_ids.size(), "seed share set empty or too large");
  require_strict_order(
      value.share_ids, [](const auto& item) { return item; }, "seed shares not ordered");
  for (const auto& share : value.share_ids) {
    require_content(share, "seed share ID invalid");
  }
  std::string output{"{"};
  field(output, "arithmetic_profile_id", quote(value.context.arithmetic_profile_id));
  field(output, "formal_semantics_id", quote(formal_semantics_id));
  field(output, "height", number(value.context.height));
  field(output, "input_set_certificate_id", quote(value.input_set_certificate_id));
  field(output, "parameter_schema_id", quote(value.context.parameter_schema_id));
  field(output, "round_config_id", quote(value.context.round_config_id));
  field(output, "round_id", quote(value.context.round_id));
  field(output, "schema_version", quote(schema_version));
  field(output, "seed_id", quote(value.seed_id));
  field(output, "seed_profile_id", quote(value.seed_profile_id));
  field(output, "share_ids", string_array(value.share_ids));
  field(output, "type_name", quote("SEED_TRANSCRIPT"));
  field(output, "validator_epoch_id", quote(value.context.validator_epoch_id));
  field(output, "view", number(value.context.view));
  output.push_back('}');
  return bytes(std::move(output));
}

core::canonical::Bytes canonical_json(const NormEvidence& value) {
  validate_context_values(value.context);
  require_content(value.input_set_certificate_id, "norm ISC ID invalid");
  require_content(value.norm_root, "norm root invalid");
  require_bounded(value.entries.size(), "norm set empty or too large");
  require_strict_order(
      value.entries, [](const NormEntry& item) { return item.ticket_id; }, "norms not ordered");
  const auto entries = object_array(value.entries, [](const NormEntry& item) {
    require(item.scale_denominator > 0U, ErrorCode::arithmetic_invalid, "norm scale zero");
    require_label(item.ticket_id, "norm ticket invalid");
    require_decimal(item.squared_norm, true, "norm value is not canonical int64");
    return "{\"scale_denominator\":" + number(item.scale_denominator) +
           ",\"squared_norm\":" + quote(item.squared_norm) +
           ",\"ticket_id\":" + quote(item.ticket_id) + '}';
  });
  std::string output{"{"};
  field(output, "arithmetic_profile_id", quote(value.context.arithmetic_profile_id));
  field(output, "entries", entries);
  field(output, "formal_semantics_id", quote(formal_semantics_id));
  field(output, "height", number(value.context.height));
  field(output, "input_set_certificate_id", quote(value.input_set_certificate_id));
  field(output, "norm_root", quote(value.norm_root));
  field(output, "parameter_schema_id", quote(value.context.parameter_schema_id));
  field(output, "round_config_id", quote(value.context.round_config_id));
  field(output, "round_id", quote(value.context.round_id));
  field(output, "schema_version", quote(schema_version));
  field(output, "type_name", quote("NORM_EVIDENCE"));
  field(output, "validator_epoch_id", quote(value.context.validator_epoch_id));
  field(output, "view", number(value.context.view));
  output.push_back('}');
  return bytes(std::move(output));
}

core::canonical::Bytes canonical_json(const EligibilityCertificate& value) {
  validate_context_values(value.context);
  require_content(value.input_set_certificate_id, "EC ISC ID invalid");
  require_content(value.norm_evidence_id, "norm evidence ID invalid");
  require_content(value.robust_profile_id, "robust profile ID invalid");
  validate_signers(value.signer_ids, value.quorum_threshold);
  require_bounded(value.entries.size(), "eligibility set empty or too large");
  require_strict_order(
      value.entries,
      [](const EligibilityEntry& item) { return item.ticket_id; },
      "eligibility entries not ordered");
  const auto entries = object_array(value.entries, [](const EligibilityEntry& item) {
    require_label(item.domain_id, "eligibility domain invalid");
    validate_rational(item.gamma, true);
    require_label(item.reason_code, "eligibility reason invalid");
    require_label(item.ticket_id, "eligibility ticket invalid");
    return "{\"accepted\":" + boolean(item.accepted) +
           ",\"domain_id\":" + quote(item.domain_id) +
           ",\"gamma\":" + rational_json(item.gamma) +
           ",\"reason_code\":" + quote(item.reason_code) +
           ",\"ticket_id\":" + quote(item.ticket_id) + '}';
  });
  std::string output{"{"};
  field(output, "arithmetic_profile_id", quote(value.context.arithmetic_profile_id));
  field(output, "entries", entries);
  field(output, "formal_semantics_id", quote(formal_semantics_id));
  field(output, "height", number(value.context.height));
  field(output, "input_set_certificate_id", quote(value.input_set_certificate_id));
  field(output, "norm_evidence_id", quote(value.norm_evidence_id));
  field(output, "parameter_schema_id", quote(value.context.parameter_schema_id));
  field(output, "quorum_threshold", number(value.quorum_threshold));
  field(output, "robust_profile_id", quote(value.robust_profile_id));
  field(output, "round_config_id", quote(value.context.round_config_id));
  field(output, "round_id", quote(value.context.round_id));
  field(output, "schema_version", quote(schema_version));
  field(output, "signer_ids", string_array(value.signer_ids));
  field(output, "type_name", quote("ELIGIBILITY_CERTIFICATE"));
  field(output, "validator_epoch_id", quote(value.context.validator_epoch_id));
  field(output, "view", number(value.context.view));
  output.push_back('}');
  return bytes(std::move(output));
}

core::canonical::Bytes canonical_json(const AggregationPlanCertificate& value) {
  validate_context_values(value.context);
  require_content(value.accumulator_proof_id, "APC accumulator proof invalid");
  require_content(value.eligibility_certificate_id, "APC EC ID invalid");
  require_content(value.input_set_certificate_id, "APC ISC ID invalid");
  require_content(value.seed_transcript_id, "APC seed transcript invalid");
  require_content(value.transcript_root, "APC transcript root invalid");
  require(value.iteration_count > 0U, ErrorCode::arithmetic_invalid, "APC iteration count zero");
  validate_signers(value.signer_ids, value.quorum_threshold);
  require_bounded(value.bucket_assignments.size(), "APC buckets empty or too large");
  require_bounded(value.weights.size(), "APC weights empty or too large");
  require_strict_order(
      value.bucket_assignments,
      [](const BucketAssignment& item) { return item.ticket_id; },
      "APC buckets not ordered");
  require_strict_order(
      value.weights, [](const Weight& item) { return item.ticket_id; }, "APC weights not ordered");
  const auto buckets = object_array(value.bucket_assignments, [](const BucketAssignment& item) {
    require_label(item.bucket_id, "bucket ID invalid");
    require_label(item.ticket_id, "bucket ticket invalid");
    return "{\"bucket_id\":" + quote(item.bucket_id) +
           ",\"ticket_id\":" + quote(item.ticket_id) + '}';
  });
  const auto weights = object_array(value.weights, [](const Weight& item) {
    validate_rational(item.alpha, true);
    require_label(item.ticket_id, "weight ticket invalid");
    return "{\"alpha\":" + rational_json(item.alpha) +
           ",\"ticket_id\":" + quote(item.ticket_id) + '}';
  });
  std::string output{"{"};
  field(output, "accumulator_proof_id", quote(value.accumulator_proof_id));
  field(output, "arithmetic_profile_id", quote(value.context.arithmetic_profile_id));
  field(output, "bucket_assignments", buckets);
  field(output, "eligibility_certificate_id", quote(value.eligibility_certificate_id));
  field(output, "formal_semantics_id", quote(formal_semantics_id));
  field(output, "height", number(value.context.height));
  field(output, "input_set_certificate_id", quote(value.input_set_certificate_id));
  field(output, "iteration_count", number(value.iteration_count));
  field(output, "parameter_schema_id", quote(value.context.parameter_schema_id));
  field(output, "quorum_threshold", number(value.quorum_threshold));
  field(output, "round_config_id", quote(value.context.round_config_id));
  field(output, "round_id", quote(value.context.round_id));
  field(output, "schema_version", quote(schema_version));
  field(output, "seed_transcript_id", quote(value.seed_transcript_id));
  field(output, "signer_ids", string_array(value.signer_ids));
  field(output, "transcript_root", quote(value.transcript_root));
  field(output, "type_name", quote("AGGREGATION_PLAN_CERTIFICATE"));
  field(output, "validator_epoch_id", quote(value.context.validator_epoch_id));
  field(output, "view", number(value.context.view));
  field(output, "weights", weights);
  output.push_back('}');
  return bytes(std::move(output));
}

core::canonical::Bytes canonical_json(const ParameterShardQc& value) {
  validate_context_values(value.context);
  require_content(value.aggregation_plan_certificate_id, "shard APC ID invalid");
  require_content(value.eligibility_certificate_id, "shard EC ID invalid");
  require_content(value.input_set_certificate_id, "shard ISC ID invalid");
  require(value.denominator > 0U, ErrorCode::arithmetic_invalid, "shard denominator zero");
  require_label(value.domain_id, "shard domain invalid");
  require_label(value.shard_id, "shard ID invalid");
  validate_signers(value.signer_ids, value.quorum_threshold);
  require_bounded(value.input_leaf_ids.size(), "shard input leaves empty or too large");
  require_bounded(value.result_numerators.size(), "shard result empty or too large");
  require_strict_order(
      value.input_leaf_ids, [](const auto& item) { return item; }, "input leaves not ordered");
  for (const auto& leaf : value.input_leaf_ids) {
    require_content(leaf, "input leaf ID invalid");
  }
  for (const auto& numerator : value.result_numerators) {
    require_decimal(numerator, false, "shard numerator is not canonical int64");
  }
  std::string output{"{"};
  field(output, "aggregation_plan_certificate_id", quote(value.aggregation_plan_certificate_id));
  field(output, "arithmetic_profile_id", quote(value.context.arithmetic_profile_id));
  field(output, "denominator", number(value.denominator));
  field(output, "domain_id", quote(value.domain_id));
  field(output, "eligibility_certificate_id", quote(value.eligibility_certificate_id));
  field(output, "formal_semantics_id", quote(formal_semantics_id));
  field(output, "height", number(value.context.height));
  field(output, "input_leaf_ids", string_array(value.input_leaf_ids));
  field(output, "input_set_certificate_id", quote(value.input_set_certificate_id));
  field(output, "parameter_schema_id", quote(value.context.parameter_schema_id));
  field(output, "quorum_threshold", number(value.quorum_threshold));
  field(output, "result_numerators", string_array(value.result_numerators));
  field(output, "round_config_id", quote(value.context.round_config_id));
  field(output, "round_id", quote(value.context.round_id));
  field(output, "schema_version", quote(schema_version));
  field(output, "shard_id", quote(value.shard_id));
  field(output, "signer_ids", string_array(value.signer_ids));
  field(output, "type_name", quote("PARAMETER_SHARD_QC"));
  field(output, "validator_epoch_id", quote(value.context.validator_epoch_id));
  field(output, "view", number(value.context.view));
  output.push_back('}');
  return bytes(std::move(output));
}

core::canonical::Bytes canonical_json(const AggregateRootQc& value) {
  validate_context_values(value.context);
  require_content(value.aggregation_plan_certificate_id, "root APC ID invalid");
  require_content(value.eligibility_certificate_id, "root EC ID invalid");
  require_content(value.input_set_certificate_id, "root ISC ID invalid");
  require_content(value.merkle_root, "root Merkle ID invalid");
  validate_signers(value.signer_ids, value.quorum_threshold);
  require_bounded(value.leaves.size(), "root leaves empty or too large");
  require_bounded(value.required_keys.size(), "required keys empty or too large");
  require_strict_order(
      value.required_keys, [](const ShardKey& item) { return item; }, "required keys not ordered");
  require_strict_order(
      value.leaves,
      [](const RootLeaf& item) { return std::tie(item.domain_id, item.shard_id); },
      "root leaves not ordered");
  require(
      value.merkle_root == aggregate_merkle_root(value.leaves),
      ErrorCode::coverage_incomplete,
      "aggregate Merkle root does not commit to the exact leaves");
  const auto leaves = object_array(value.leaves, [](const RootLeaf& item) {
    require_label(item.domain_id, "root leaf domain invalid");
    require_content(item.parameter_shard_qc_id, "root shard QC ID invalid");
    require_label(item.shard_id, "root leaf shard invalid");
    return "{\"domain_id\":" + quote(item.domain_id) +
           ",\"parameter_shard_qc_id\":" + quote(item.parameter_shard_qc_id) +
           ",\"shard_id\":" + quote(item.shard_id) + '}';
  });
  const auto required = object_array(value.required_keys, [](const ShardKey& item) {
    require_label(item.domain_id, "required domain invalid");
    require_label(item.shard_id, "required shard invalid");
    return "{\"domain_id\":" + quote(item.domain_id) +
           ",\"shard_id\":" + quote(item.shard_id) + '}';
  });
  std::string output{"{"};
  field(output, "aggregation_plan_certificate_id", quote(value.aggregation_plan_certificate_id));
  field(output, "arithmetic_profile_id", quote(value.context.arithmetic_profile_id));
  field(output, "eligibility_certificate_id", quote(value.eligibility_certificate_id));
  field(output, "formal_semantics_id", quote(formal_semantics_id));
  field(output, "height", number(value.context.height));
  field(output, "input_set_certificate_id", quote(value.input_set_certificate_id));
  field(output, "leaves", leaves);
  field(output, "merkle_root", quote(value.merkle_root));
  field(output, "parameter_schema_id", quote(value.context.parameter_schema_id));
  field(output, "quorum_threshold", number(value.quorum_threshold));
  field(output, "required_keys", required);
  field(output, "round_config_id", quote(value.context.round_config_id));
  field(output, "round_id", quote(value.context.round_id));
  field(output, "schema_version", quote(schema_version));
  field(output, "signer_ids", string_array(value.signer_ids));
  field(output, "type_name", quote("AGGREGATE_ROOT_QC"));
  field(output, "validator_epoch_id", quote(value.context.validator_epoch_id));
  field(output, "view", number(value.context.view));
  output.push_back('}');
  return bytes(std::move(output));
}

std::string aggregate_merkle_root(const std::vector<RootLeaf>& leaves) {
  require_bounded(leaves.size(), "aggregate Merkle leaf set empty or too large");
  std::vector<std::string> level;
  level.reserve(leaves.size());
  for (const auto& leaf : leaves) {
    require_label(leaf.domain_id, "aggregate Merkle domain invalid");
    require_label(leaf.shard_id, "aggregate Merkle shard invalid");
    require_content(leaf.parameter_shard_qc_id, "aggregate Merkle shard QC invalid");
    const auto canonical = "{\"domain_id\":" + quote(leaf.domain_id) +
                           ",\"parameter_shard_qc_id\":" +
                           quote(leaf.parameter_shard_qc_id) + ",\"shard_id\":" +
                           quote(leaf.shard_id) + '}';
    const auto leaf_bytes = std::as_bytes(std::span(canonical.data(), canonical.size()));
    level.push_back(id_for("deltareduce.008.aggregate-leaf.v1", leaf_bytes));
  }
  while (level.size() > 1U) {
    std::vector<std::string> parent;
    parent.reserve((level.size() + 1U) / 2U);
    for (std::size_t index = 0U; index < level.size(); index += 2U) {
      if (index + 1U == level.size()) {
        parent.push_back(level[index]);
        continue;
      }
      auto pair = digest_bytes(level[index]);
      const auto right = digest_bytes(level[index + 1U]);
      pair.insert(pair.end(), right.begin(), right.end());
      parent.push_back(id_for("deltareduce.008.aggregate-node.v1", pair));
    }
    level = std::move(parent);
  }
  return level.front();
}

core::canonical::Bytes canonical_json(const ApplyArithmeticProfile& value) {
  require_content(value.accumulator_proof_id, "apply accumulator proof invalid");
  require_bounded(value.domain_weights.size(), "domain weights empty or too large");
  require_strict_order(
      value.domain_weights,
      [](const DomainWeight& item) { return item.domain_id; },
      "domain weights not ordered");
  const auto weights = object_array(value.domain_weights, [](const DomainWeight& item) {
    require_label(item.domain_id, "domain weight ID invalid");
    validate_rational(item.pi, true);
    return "{\"domain_id\":" + quote(item.domain_id) +
           ",\"pi\":" + rational_json(item.pi) + '}';
  });
  validate_rational(value.learning_rate, true);
  validate_rational(value.momentum, true);
  validate_rational(value.weight_decay, true);
  require(value.nesterov, ErrorCode::arithmetic_invalid, "Nesterov profile disabled");
  require(
      value.rounding == "HALF_TOWARD_POSITIVE",
      ErrorCode::arithmetic_invalid,
      "apply rounding profile invalid");
  std::string output{"{"};
  field(output, "accumulator_proof_id", quote(value.accumulator_proof_id));
  field(output, "domain_weights", weights);
  field(output, "formal_semantics_id", quote(formal_semantics_id));
  field(output, "learning_rate", rational_json(value.learning_rate));
  field(output, "momentum", rational_json(value.momentum));
  field(output, "nesterov", boolean(value.nesterov));
  field(output, "rounding", quote(value.rounding));
  field(output, "schema_version", quote(schema_version));
  field(output, "type_name", quote("APPLY_ARITHMETIC_PROFILE"));
  field(output, "weight_decay", rational_json(value.weight_decay));
  output.push_back('}');
  return bytes(std::move(output));
}

core::canonical::Bytes canonical_json(const ApplyCandidate& value) {
  validate_context_values(value.context);
  require_content(value.aggregate_root_qc_id, "candidate root QC invalid");
  require_content(value.apply_arithmetic_profile_id, "candidate apply profile invalid");
  require_content(value.next_model_hash, "candidate model hash invalid");
  require_content(value.next_optimizer_hash, "candidate optimizer hash invalid");
  require_content(value.parent_checkpoint_id, "candidate parent checkpoint invalid");
  require_content(value.parent_optimizer_hash, "candidate parent optimizer invalid");
  require_bounded(value.next_model_values.size(), "candidate model empty or too large");
  require(
      value.next_optimizer_values.size() == value.next_model_values.size(),
      ErrorCode::arithmetic_invalid,
      "candidate optimizer/model length mismatch");
  for (const auto& coordinate : value.next_model_values) {
    require_decimal(coordinate, false, "candidate model coordinate is not canonical int64");
  }
  for (const auto& coordinate : value.next_optimizer_values) {
    require_decimal(coordinate, false, "candidate optimizer coordinate is not canonical int64");
  }
  std::string output{"{"};
  field(output, "aggregate_root_qc_id", quote(value.aggregate_root_qc_id));
  field(output, "apply_arithmetic_profile_id", quote(value.apply_arithmetic_profile_id));
  field(output, "arithmetic_profile_id", quote(value.context.arithmetic_profile_id));
  field(output, "formal_semantics_id", quote(formal_semantics_id));
  field(output, "height", number(value.context.height));
  field(output, "next_model_hash", quote(value.next_model_hash));
  field(output, "next_model_values", string_array(value.next_model_values));
  field(output, "next_optimizer_hash", quote(value.next_optimizer_hash));
  field(output, "next_optimizer_values", string_array(value.next_optimizer_values));
  field(output, "parameter_schema_id", quote(value.context.parameter_schema_id));
  field(output, "parent_checkpoint_id", quote(value.parent_checkpoint_id));
  field(output, "parent_optimizer_hash", quote(value.parent_optimizer_hash));
  field(output, "round_config_id", quote(value.context.round_config_id));
  field(output, "round_id", quote(value.context.round_id));
  field(output, "schema_version", quote(schema_version));
  field(output, "type_name", quote("APPLY_CANDIDATE"));
  field(output, "validator_epoch_id", quote(value.context.validator_epoch_id));
  field(output, "view", number(value.context.view));
  output.push_back('}');
  return bytes(std::move(output));
}

core::canonical::Bytes canonical_json(const ApplyQc& value) {
  validate_context_values(value.context);
  require_content(value.aggregate_root_qc_id, "ApplyQC root invalid");
  require_content(value.apply_arithmetic_profile_id, "ApplyQC profile invalid");
  require_content(value.apply_candidate_id, "ApplyQC candidate invalid");
  require_content(value.next_model_hash, "ApplyQC model invalid");
  require_content(value.next_optimizer_hash, "ApplyQC optimizer invalid");
  require_content(value.parent_checkpoint_id, "ApplyQC parent invalid");
  validate_signers(value.signer_ids, value.quorum_threshold);
  std::string output{"{"};
  field(output, "aggregate_root_qc_id", quote(value.aggregate_root_qc_id));
  field(output, "apply_arithmetic_profile_id", quote(value.apply_arithmetic_profile_id));
  field(output, "apply_candidate_id", quote(value.apply_candidate_id));
  field(output, "arithmetic_profile_id", quote(value.context.arithmetic_profile_id));
  field(output, "formal_semantics_id", quote(formal_semantics_id));
  field(output, "height", number(value.context.height));
  field(output, "next_model_hash", quote(value.next_model_hash));
  field(output, "next_optimizer_hash", quote(value.next_optimizer_hash));
  field(output, "parameter_schema_id", quote(value.context.parameter_schema_id));
  field(output, "parent_checkpoint_id", quote(value.parent_checkpoint_id));
  field(output, "quorum_threshold", number(value.quorum_threshold));
  field(output, "round_config_id", quote(value.context.round_config_id));
  field(output, "round_id", quote(value.context.round_id));
  field(output, "schema_version", quote(schema_version));
  field(output, "signer_ids", string_array(value.signer_ids));
  field(output, "type_name", quote("APPLY_QC"));
  field(output, "validator_epoch_id", quote(value.context.validator_epoch_id));
  field(output, "view", number(value.context.view));
  output.push_back('}');
  return bytes(std::move(output));
}

core::canonical::Bytes canonical_json(const CurrentPointerCommand& value) {
  validate_context_values(value.context);
  require_content(value.apply_qc_id, "pointer ApplyQC ID invalid");
  require_content(value.expected_parent_checkpoint_id, "pointer parent invalid");
  require_content(value.next_checkpoint_id, "pointer next checkpoint invalid");
  require_content(value.next_optimizer_hash, "pointer next optimizer invalid");
  std::string output{"{"};
  field(output, "apply_qc_id", quote(value.apply_qc_id));
  field(output, "arithmetic_profile_id", quote(value.context.arithmetic_profile_id));
  field(output, "expected_parent_checkpoint_id", quote(value.expected_parent_checkpoint_id));
  field(output, "formal_semantics_id", quote(formal_semantics_id));
  field(output, "height", number(value.context.height));
  field(output, "next_checkpoint_id", quote(value.next_checkpoint_id));
  field(output, "next_optimizer_hash", quote(value.next_optimizer_hash));
  field(output, "parameter_schema_id", quote(value.context.parameter_schema_id));
  field(output, "round_config_id", quote(value.context.round_config_id));
  field(output, "round_id", quote(value.context.round_id));
  field(output, "schema_version", quote(schema_version));
  field(output, "type_name", quote("CURRENT_POINTER_COMMAND"));
  field(output, "validator_epoch_id", quote(value.context.validator_epoch_id));
  field(output, "view", number(value.context.view));
  output.push_back('}');
  return bytes(std::move(output));
}

#define DELTA_CERTIFICATE_ID(TypeName, Domain)                                      \
  std::string content_id(const TypeName& value) {                                   \
    const auto encoded = canonical_json(value);                                     \
    require(encoded.size() <= max_contract_bytes, ErrorCode::limit_exceeded,        \
            "certificate bytes exceed bound");                                    \
    return id_for(Domain, encoded);                                                  \
  }

DELTA_CERTIFICATE_ID(InputSetCertificate, "deltareduce.008.input-set-certificate.v1")
DELTA_CERTIFICATE_ID(SeedTranscript, "deltareduce.008.seed-transcript.v1")
DELTA_CERTIFICATE_ID(NormEvidence, "deltareduce.008.norm-evidence.v1")
DELTA_CERTIFICATE_ID(EligibilityCertificate, "deltareduce.008.eligibility-certificate.v1")
DELTA_CERTIFICATE_ID(
    AggregationPlanCertificate,
    "deltareduce.008.aggregation-plan-certificate.v1")
DELTA_CERTIFICATE_ID(ParameterShardQc, "deltareduce.008.parameter-shard-qc.v1")
DELTA_CERTIFICATE_ID(AggregateRootQc, "deltareduce.008.aggregate-root-qc.v1")
DELTA_CERTIFICATE_ID(
    ApplyArithmeticProfile,
    "deltareduce.008.apply-arithmetic-profile.v1")
DELTA_CERTIFICATE_ID(ApplyCandidate, "deltareduce.008.apply-candidate.v1")
DELTA_CERTIFICATE_ID(ApplyQc, "deltareduce.008.apply-qc.v1")
DELTA_CERTIFICATE_ID(CurrentPointerCommand, "deltareduce.008.current-pointer-command.v1")

#undef DELTA_CERTIFICATE_ID

}  // namespace delta::certificates
