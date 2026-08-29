#include <delta/scheduling/eligibility.hpp>

#include <delta/core/canonical.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <span>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace delta::scheduling {
namespace {

[[noreturn]] void reject(ErrorCode code, std::string message) {
  throw SchedulingError(code, std::move(message));
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

[[nodiscard]] bool label_valid(std::string_view value) noexcept {
  return !value.empty() && value.size() <= 128U &&
         std::all_of(value.begin(), value.end(), [](char character) {
           const bool letter = (character >= 'A' && character <= 'Z') ||
                               (character >= 'a' && character <= 'z');
           const bool digit = character >= '0' && character <= '9';
           return letter || digit || character == '.' || character == '_' || character == ':' ||
                  character == '-';
         });
}

class ObjectReader final {
 public:
  explicit ObjectReader(std::string_view input) : input_(input) {
    require(take('{'), ErrorCode::canonical_json_invalid, "capability object start is missing");
  }

  [[nodiscard]] std::string string_field(std::string_view key) {
    field(key);
    return string();
  }

  [[nodiscard]] std::uint64_t unsigned_field(std::string_view key) {
    field(key);
    return unsigned_integer();
  }

  void finish() {
    require(take('}'), ErrorCode::canonical_json_invalid, "capability object end is missing");
    require(cursor_ == input_.size(), ErrorCode::canonical_json_invalid, "trailing JSON bytes");
  }

 private:
  [[nodiscard]] bool take(char expected) {
    if (cursor_ < input_.size() && input_[cursor_] == expected) {
      ++cursor_;
      return true;
    }
    return false;
  }

  void field(std::string_view expected) {
    if (!first_) {
      require(take(','), ErrorCode::canonical_json_invalid, "capability field comma is missing");
    }
    first_ = false;
    require(
        string() == expected,
        ErrorCode::field_set_invalid,
        "capability field set or order is invalid");
    require(take(':'), ErrorCode::canonical_json_invalid, "capability field colon is missing");
  }

  [[nodiscard]] std::string string() {
    require(take('"'), ErrorCode::canonical_json_invalid, "capability string start is missing");
    const auto begin = cursor_;
    while (cursor_ < input_.size() && input_[cursor_] != '"') {
      const auto value = static_cast<unsigned char>(input_[cursor_]);
      require(
          value >= 0x20U && value <= 0x7eU && input_[cursor_] != '\\',
          ErrorCode::canonical_json_invalid,
          "capability string is outside the canonical ASCII subset");
      ++cursor_;
    }
    require(
        cursor_ < input_.size(), ErrorCode::canonical_json_invalid, "capability string is truncated");
    auto result = std::string(input_.substr(begin, cursor_ - begin));
    ++cursor_;
    return result;
  }

  [[nodiscard]] std::uint64_t unsigned_integer() {
    require(
        cursor_ < input_.size() && input_[cursor_] >= '0' && input_[cursor_] <= '9',
        ErrorCode::canonical_json_invalid,
        "capability integer is missing");
    const auto begin = cursor_;
    if (input_[cursor_] == '0') {
      ++cursor_;
      require(
          cursor_ == input_.size() || input_[cursor_] < '0' || input_[cursor_] > '9',
          ErrorCode::canonical_json_invalid,
          "capability integer contains a leading zero");
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
          "capability integer overflows uint64");
      value = value * 10U + next;
    }
    return value;
  }

  std::string_view input_;
  std::size_t cursor_ = 0U;
  bool first_ = true;
};

[[nodiscard]] std::string quote(std::string_view value) {
  require(
      std::all_of(value.begin(), value.end(), [](char character) {
        return character >= 0x20 && character <= 0x7e && character != '"' && character != '\\';
      }),
      ErrorCode::identifier_invalid,
      "eligibility string is outside the canonical ASCII subset");
  return "\"" + std::string(value) + "\"";
}

void append_field(std::string& output, std::string_view key, std::string_view encoded_value) {
  if (output.size() > 1U) {
    output.push_back(',');
  }
  output += quote(key);
  output.push_back(':');
  output += encoded_value;
}

[[nodiscard]] std::string string_array_json(const std::vector<std::string>& values) {
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

[[nodiscard]] std::vector<std::byte> bytes(std::string value) {
  const auto view = std::as_bytes(std::span(value.data(), value.size()));
  return {view.begin(), view.end()};
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

template <typename Values>
void validate_canonical_labels(const Values& values, const char* message) {
  require(
      std::is_sorted(values.begin(), values.end()) &&
          std::adjacent_find(values.begin(), values.end()) == values.end() &&
          std::all_of(values.begin(), values.end(), label_valid),
      ErrorCode::policy_invalid,
      message);
}

template <typename Values>
void validate_canonical_content_ids(const Values& values, const char* message) {
  require(
      std::is_sorted(values.begin(), values.end()) &&
          std::adjacent_find(values.begin(), values.end()) == values.end() &&
          std::all_of(values.begin(), values.end(), content_id_valid),
      ErrorCode::policy_invalid,
      message);
}

}  // namespace

CapabilityProfile parse_capability_profile(
    std::span<const std::byte> canonical_json,
    const Limits& limits) {
  require(
      !canonical_json.empty() && canonical_json.size() <= limits.contract_bytes,
      ErrorCode::input_too_large,
      "capability profile byte length is outside limits");
  const auto text = std::string_view(
      reinterpret_cast<const char*>(canonical_json.data()), canonical_json.size());
  ObjectReader reader(text);
  CapabilityProfile profile;
  profile.arithmetic_profile_id = reader.string_field("arithmetic_profile_id");
  profile.complete_ticket_throughput_milli =
      reader.unsigned_field("complete_ticket_throughput_milli");
  profile.expires_at_tick = reader.unsigned_field("expires_at_tick");
  require(
      reader.string_field("formal_semantics_id") == formal_semantics_id,
      ErrorCode::context_mismatch,
      "capability formal semantics ID is invalid");
  profile.identity_epoch = reader.unsigned_field("identity_epoch");
  profile.max_concurrent_leases = reader.unsigned_field("max_concurrent_leases");
  profile.measured_at_tick = reader.unsigned_field("measured_at_tick");
  profile.measurement_artifact_id = reader.string_field("measurement_artifact_id");
  profile.memory_bytes = reader.unsigned_field("memory_bytes");
  profile.model_mode = reader.string_field("model_mode");
  profile.parameter_schema_id = reader.string_field("parameter_schema_id");
  profile.region_id = reader.string_field("region_id");
  profile.round_config_id = reader.string_field("round_config_id");
  profile.sample_count = reader.unsigned_field("sample_count");
  require(
      reader.string_field("schema_version") == schema_version,
      ErrorCode::context_mismatch,
      "capability schema version is invalid");
  profile.signature_id = reader.string_field("signature_id");
  profile.software_build_id = reader.string_field("software_build_id");
  require(
      reader.string_field("type_name") == "CAPABILITY_PROFILE",
      ErrorCode::context_mismatch,
      "capability type name is invalid");
  profile.worker_id = reader.string_field("worker_id");
  reader.finish();
  require(
      canonical_capability_profile(profile) ==
          std::vector<std::byte>(canonical_json.begin(), canonical_json.end()),
      ErrorCode::canonical_json_invalid,
      "capability profile is not canonical");
  return profile;
}

std::vector<std::byte> canonical_capability_profile(const CapabilityProfile& profile) {
  std::string output{"{"};
  append_field(output, "arithmetic_profile_id", quote(profile.arithmetic_profile_id));
  append_field(
      output,
      "complete_ticket_throughput_milli",
      std::to_string(profile.complete_ticket_throughput_milli));
  append_field(output, "expires_at_tick", std::to_string(profile.expires_at_tick));
  append_field(output, "formal_semantics_id", quote(formal_semantics_id));
  append_field(output, "identity_epoch", std::to_string(profile.identity_epoch));
  append_field(
      output, "max_concurrent_leases", std::to_string(profile.max_concurrent_leases));
  append_field(output, "measured_at_tick", std::to_string(profile.measured_at_tick));
  append_field(output, "measurement_artifact_id", quote(profile.measurement_artifact_id));
  append_field(output, "memory_bytes", std::to_string(profile.memory_bytes));
  append_field(output, "model_mode", quote(profile.model_mode));
  append_field(output, "parameter_schema_id", quote(profile.parameter_schema_id));
  append_field(output, "region_id", quote(profile.region_id));
  append_field(output, "round_config_id", quote(profile.round_config_id));
  append_field(output, "sample_count", std::to_string(profile.sample_count));
  append_field(output, "schema_version", quote(schema_version));
  append_field(output, "signature_id", quote(profile.signature_id));
  append_field(output, "software_build_id", quote(profile.software_build_id));
  append_field(output, "type_name", quote("CAPABILITY_PROFILE"));
  append_field(output, "worker_id", quote(profile.worker_id));
  output.push_back('}');
  return bytes(std::move(output));
}

std::string capability_profile_content_id(std::span<const std::byte> canonical_json) {
  return content_id_for("deltareduce.007.capability-profile.v1", canonical_json);
}

EligibilityRecord evaluate_capability(
    const CapabilityProfile& profile,
    const EligibilityPolicy& policy) {
  require(
      content_id_valid(policy.eligibility_policy_id) &&
          content_id_valid(policy.arithmetic_profile_id) &&
          content_id_valid(policy.parameter_schema_id) &&
          content_id_valid(policy.round_config_id),
      ErrorCode::identifier_invalid,
      "eligibility policy content ID is invalid");
  validate_canonical_labels(policy.allowed_domain_ids, "allowed domain set is not canonical");
  validate_canonical_labels(policy.allowed_region_ids, "allowed region set is not canonical");
  validate_canonical_content_ids(
      policy.allowed_software_build_ids, "allowed software set is not canonical");
  validate_canonical_content_ids(
      policy.trusted_signature_ids, "trusted signature set is not canonical");

  const auto profile_bytes = canonical_capability_profile(profile);
  const auto profile_id = capability_profile_content_id(profile_bytes);
  std::vector<std::string> reasons;
  const auto mismatch = [&reasons](bool condition, std::string code) {
    if (condition) {
      reasons.push_back(std::move(code));
    }
  };
  mismatch(
      profile.arithmetic_profile_id != policy.arithmetic_profile_id,
      "ARITHMETIC_PROFILE_MISMATCH");
  mismatch(profile.expires_at_tick < policy.decision_tick, "PROFILE_EXPIRED");
  mismatch(profile.identity_epoch != policy.identity_epoch, "IDENTITY_EPOCH_MISMATCH");
  mismatch(profile.measured_at_tick > policy.decision_tick, "MEASUREMENT_FROM_FUTURE");
  mismatch(profile.memory_bytes < policy.minimum_memory_bytes, "MEMORY_INSUFFICIENT");
  mismatch(profile.model_mode != policy.model_mode, "MODEL_MODE_MISMATCH");
  mismatch(
      profile.parameter_schema_id != policy.parameter_schema_id,
      "PARAMETER_SCHEMA_MISMATCH");
  mismatch(
      !std::binary_search(
          policy.allowed_region_ids.begin(), policy.allowed_region_ids.end(), profile.region_id),
      "REGION_NOT_ALLOWED");
  mismatch(profile.round_config_id != policy.round_config_id, "ROUND_CONFIG_MISMATCH");
  mismatch(profile.sample_count < policy.minimum_sample_count, "MEASUREMENT_SAMPLE_INSUFFICIENT");
  mismatch(
      !std::binary_search(
          policy.trusted_signature_ids.begin(),
          policy.trusted_signature_ids.end(),
          profile.signature_id),
      "SIGNATURE_NOT_TRUSTED");
  mismatch(
      !std::binary_search(
          policy.allowed_software_build_ids.begin(),
          policy.allowed_software_build_ids.end(),
          profile.software_build_id),
      "SOFTWARE_BUILD_NOT_ALLOWED");
  mismatch(profile.complete_ticket_throughput_milli == 0U, "THROUGHPUT_EVIDENCE_MISSING");
  mismatch(
      profile.max_concurrent_leases == 0U || profile.max_concurrent_leases > 1024U,
      "CONCURRENCY_LIMIT_INVALID");
  mismatch(!content_id_valid(profile.measurement_artifact_id), "MEASUREMENT_ARTIFACT_INVALID");
  mismatch(!label_valid(profile.worker_id), "WORKER_ID_INVALID");
  std::sort(reasons.begin(), reasons.end());
  const bool eligible = reasons.empty();
  if (eligible) {
    reasons.push_back("ELIGIBLE");
  }
  EligibilityDecision decision{
      eligible ? policy.allowed_domain_ids : std::vector<std::string>{},
      profile_id,
      policy.decision_tick,
      policy.eligibility_policy_id,
      eligible,
      eligible ? profile.max_concurrent_leases : 0U,
      reasons,
      profile.region_id,
      policy.round_config_id,
      profile.worker_id,
  };
  auto decision_bytes = canonical_eligibility_decision(decision);
  auto decision_id = eligibility_decision_content_id(decision_bytes);
  return {
      profile,
      profile_bytes,
      profile_id,
      std::move(decision),
      decision_bytes,
      decision_id,
  };
}

std::vector<std::byte> canonical_eligibility_decision(const EligibilityDecision& decision) {
  std::string output{"{"};
  append_field(output, "allowed_domain_ids", string_array_json(decision.allowed_domain_ids));
  append_field(output, "capability_profile_id", quote(decision.capability_profile_id));
  append_field(output, "decision_tick", std::to_string(decision.decision_tick));
  append_field(output, "eligibility_policy_id", quote(decision.eligibility_policy_id));
  append_field(output, "eligible", decision.eligible ? "true" : "false");
  append_field(output, "formal_semantics_id", quote(formal_semantics_id));
  append_field(
      output, "max_concurrent_leases", std::to_string(decision.max_concurrent_leases));
  append_field(output, "reason_codes", string_array_json(decision.reason_codes));
  append_field(output, "region_route", quote(decision.region_route));
  append_field(output, "round_config_id", quote(decision.round_config_id));
  append_field(output, "schema_version", quote(schema_version));
  append_field(output, "type_name", quote("ELIGIBILITY_DECISION"));
  append_field(output, "worker_id", quote(decision.worker_id));
  output.push_back('}');
  return bytes(std::move(output));
}

std::string eligibility_decision_content_id(std::span<const std::byte> canonical_json) {
  return content_id_for("deltareduce.007.eligibility-decision.v1", canonical_json);
}

}  // namespace delta::scheduling
