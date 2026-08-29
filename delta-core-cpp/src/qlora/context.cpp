#include <delta/qlora/context.hpp>

#include <delta/core/arithmetic.hpp>
#include <delta/core/canonical.hpp>

#include <algorithm>
#include <cstddef>
#include <span>
#include <string>
#include <tuple>
#include <utility>
#include <vector>

namespace delta::qlora {
namespace {

[[noreturn]] void reject(certificates::ErrorCode code, const char* message) {
  throw certificates::CertificateError(code, message);
}

void require(bool condition, certificates::ErrorCode code, const char* message) {
  if (!condition) {
    reject(code, message);
  }
}

[[nodiscard]] std::string quote(const std::string& value) {
  require(
      !value.empty() && std::all_of(value.begin(), value.end(), [](char character) {
        return character >= 0x20 && character <= 0x7e && character != '"' && character != '\\';
      }),
      certificates::ErrorCode::identifier_invalid,
      "QLoRA context string is outside the canonical ASCII subset");
  return '"' + value + '"';
}

void field(std::string& output, const char* name, const std::string& value) {
  if (output.size() > 1U) {
    output.push_back(',');
  }
  output += quote(name);
  output.push_back(':');
  output += quote(value);
}

void validate_context_ids(const Context& value) {
  const std::vector<std::string> ids{
      value.adapter_parameter_schema_id,
      value.base_model_manifest_id,
      value.parent_adapter_id,
      value.quantized_base_profile_id,
      value.tokenizer_hash,
      value.training_mode_id,
  };
  require(
      std::all_of(ids.begin(), ids.end(), certificates::is_content_id),
      certificates::ErrorCode::identifier_invalid,
      "QLoRA context contains an invalid content ID");
}

[[nodiscard]] std::int64_t checked_add(std::int64_t left, std::int64_t right) {
  try {
    return core::arithmetic::checked_add(left, right);
  } catch (const core::arithmetic::ArithmeticError&) {
    reject(certificates::ErrorCode::arithmetic_invalid, "adapter reduction addition overflows");
  }
}

[[nodiscard]] std::int64_t checked_multiply(std::int64_t left, std::int64_t right) {
  try {
    return core::arithmetic::checked_multiply(left, right);
  } catch (const core::arithmetic::ArithmeticError&) {
    reject(certificates::ErrorCode::arithmetic_invalid, "adapter reduction product overflows");
  }
}

}  // namespace

bool AdapterKey::operator<(const AdapterKey& other) const noexcept {
  return std::tie(domain_id, parameter_name) < std::tie(other.domain_id, other.parameter_name);
}

std::string canonical_json(const Context& value) {
  validate_context_ids(value);
  std::string output{"{"};
  field(output, "adapter_parameter_schema_id", value.adapter_parameter_schema_id);
  field(output, "base_model_manifest_id", value.base_model_manifest_id);
  field(output, "formal_semantics_id", std::string(certificates::formal_semantics_id));
  field(output, "parent_adapter_id", value.parent_adapter_id);
  field(output, "quantized_base_profile_id", value.quantized_base_profile_id);
  field(output, "schema_version", std::string(certificates::schema_version));
  field(output, "tokenizer_hash", value.tokenizer_hash);
  field(output, "training_mode_id", value.training_mode_id);
  field(output, "type_name", "QLORA_CONTEXT_BINDING");
  output.push_back('}');
  require(
      output.size() <= max_context_bytes,
      certificates::ErrorCode::limit_exceeded,
      "QLoRA context exceeds the canonical bound");
  return output;
}

std::string content_id(const Context& value) {
  const auto document = canonical_json(value);
  constexpr std::string_view domain = "deltareduce.009.qlora-context.v1";
  std::vector<std::byte> bytes;
  bytes.reserve(domain.size() + 1U + document.size());
  for (const char character : domain) {
    bytes.push_back(static_cast<std::byte>(character));
  }
  bytes.push_back(std::byte{0});
  const auto view = std::as_bytes(std::span(document.data(), document.size()));
  bytes.insert(bytes.end(), view.begin(), view.end());
  return "sha256:" + core::canonical::sha256_hex(bytes);
}

void validate_binding(
    const Context& value,
    const certificates::Context& certificate_context) {
  validate_context_ids(value);
  require(
      certificate_context.parameter_schema_id == value.adapter_parameter_schema_id,
      certificates::ErrorCode::context_mismatch,
      "certificate parameter schema is not the QLoRA adapter schema");
  require(
      certificate_context.round_config_id == content_id(value),
      certificates::ErrorCode::context_mismatch,
      "certificate RoundConfig does not bind the complete QLoRA context");
}

certificates::ChainVerifier make_chain_verifier(
    const Context& value,
    certificates::Context certificate_context,
    certificates::ValidatorPolicy validators) {
  validate_binding(value, certificate_context);
  return certificates::ChainVerifier(std::move(certificate_context), std::move(validators));
}

std::vector<AdapterKey> required_adapter_keys(
    const std::vector<std::string>& ordered_domains,
    const std::vector<std::string>& ordered_parameters) {
  require(
      !ordered_domains.empty() && !ordered_parameters.empty() &&
          std::is_sorted(ordered_domains.begin(), ordered_domains.end()) &&
          std::adjacent_find(ordered_domains.begin(), ordered_domains.end()) ==
              ordered_domains.end() &&
          std::is_sorted(ordered_parameters.begin(), ordered_parameters.end()) &&
          std::adjacent_find(ordered_parameters.begin(), ordered_parameters.end()) ==
              ordered_parameters.end(),
      certificates::ErrorCode::order_invalid,
      "adapter domains and parameter names must be non-empty ordered unique lists");
  std::vector<AdapterKey> result;
  result.reserve(ordered_domains.size() * ordered_parameters.size());
  for (const auto& domain : ordered_domains) {
    for (const auto& parameter : ordered_parameters) {
      require(
          certificates::is_label(domain) && certificates::is_label(parameter),
          certificates::ErrorCode::identifier_invalid,
          "adapter coverage key is invalid");
      result.push_back({domain, parameter});
    }
  }
  return result;
}

void validate_exact_coverage(
    const std::vector<AdapterKey>& required,
    const std::vector<AdapterVector>& contributions) {
  require(
      !required.empty() && std::is_sorted(required.begin(), required.end()) &&
          std::adjacent_find(required.begin(), required.end()) == required.end(),
      certificates::ErrorCode::order_invalid,
      "required adapter matrix is not canonical");
  std::vector<AdapterKey> observed;
  std::vector<std::pair<AdapterKey, std::string>> leaves;
  for (const auto& contribution : contributions) {
    observed.push_back(contribution.key);
    leaves.emplace_back(contribution.key, contribution.ticket_id);
    require(
        !contribution.ticket_id.empty() && !contribution.q_values.empty(),
        certificates::ErrorCode::coverage_incomplete,
        "adapter contribution is empty");
  }
  std::sort(observed.begin(), observed.end());
  observed.erase(std::unique(observed.begin(), observed.end()), observed.end());
  std::sort(leaves.begin(), leaves.end());
  require(
      std::adjacent_find(leaves.begin(), leaves.end()) == leaves.end(),
      certificates::ErrorCode::duplicate_entry,
      "duplicate ticket contribution for an adapter key");
  require(
      observed == required,
      certificates::ErrorCode::coverage_incomplete,
      "adapter contribution coverage differs from the immutable required matrix");
}

std::vector<ReducedAdapterVector> reduce_adapter_vectors(
    const std::vector<AdapterKey>& required,
    const std::vector<AdapterVector>& contributions) {
  validate_exact_coverage(required, contributions);
  std::vector<ReducedAdapterVector> result;
  result.reserve(required.size());
  for (const auto& key : required) {
    std::vector<std::int64_t> accumulator;
    for (const auto& contribution : contributions) {
      if (contribution.key != key) {
        continue;
      }
      if (accumulator.empty()) {
        accumulator.assign(contribution.q_values.size(), 0);
      }
      require(
          accumulator.size() == contribution.q_values.size(),
          certificates::ErrorCode::coverage_incomplete,
          "adapter vectors for one required key have different shapes");
      for (std::size_t index = 0U; index < accumulator.size(); ++index) {
        accumulator[index] = checked_add(
            accumulator[index],
            checked_multiply(contribution.q_values[index], contribution.coefficient));
      }
    }
    result.push_back({key, std::move(accumulator)});
  }
  return result;
}

std::vector<certificates::ShardKey> certificate_required_keys(
    const std::vector<AdapterKey>& required) {
  std::vector<certificates::ShardKey> result;
  result.reserve(required.size());
  for (const auto& key : required) {
    result.push_back({key.domain_id, key.parameter_name});
  }
  return result;
}

}  // namespace delta::qlora
