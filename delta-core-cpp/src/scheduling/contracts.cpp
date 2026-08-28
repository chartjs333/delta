#include <delta/scheduling/contracts.hpp>

#include <delta/core/canonical.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <set>
#include <span>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace delta::scheduling {
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
  throw SchedulingError(code, std::move(message));
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
    require(
        cursor_ < input_.size(), ErrorCode::canonical_json_invalid, "string is truncated");
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
  require(
      found != object.object_keys.end() && *found == key,
      ErrorCode::field_set_invalid,
      "required scheduling field is missing");
  return object.object_values[static_cast<std::size_t>(found - object.object_keys.begin())];
}

[[nodiscard]] std::string string_member(const JsonValue& object, std::string_view key) {
  const auto& value = member(object, key);
  require(
      value.type == JsonType::string,
      ErrorCode::field_set_invalid,
      "scheduling string field has the wrong type");
  return value.string;
}

[[nodiscard]] std::uint64_t unsigned_member(const JsonValue& object, std::string_view key) {
  const auto& value = member(object, key);
  require(
      value.type == JsonType::unsigned_integer,
      ErrorCode::field_set_invalid,
      "scheduling integer field has the wrong type");
  return value.unsigned_integer;
}

[[nodiscard]] std::vector<std::string> string_array(
    const JsonValue& object,
    std::string_view key,
    std::size_t maximum) {
  const auto& value = member(object, key);
  require(
      value.type == JsonType::array && !value.array.empty() && value.array.size() <= maximum,
      ErrorCode::field_set_invalid,
      "scheduling string array has invalid bounds");
  std::vector<std::string> result;
  result.reserve(value.array.size());
  for (const auto& item : value.array) {
    require(
        item.type == JsonType::string,
        ErrorCode::field_set_invalid,
        "scheduling string array contains a non-string");
    result.push_back(item.string);
  }
  return result;
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

void require_content_id(std::string_view value, const char* message) {
  require(content_id_valid(value), ErrorCode::identifier_invalid, message);
}

void require_label(std::string_view value, const char* message) {
  require(label_valid(value), ErrorCode::identifier_invalid, message);
}

[[nodiscard]] std::vector<std::byte> bytes(std::string value) {
  const auto view = std::as_bytes(std::span(value.data(), value.size()));
  return {view.begin(), view.end()};
}

[[nodiscard]] std::string quote(std::string_view value) {
  require(
      std::all_of(value.begin(), value.end(), [](char character) {
        return character >= 0x20 && character <= 0x7e && character != '"' && character != '\\';
      }),
      ErrorCode::identifier_invalid,
      "canonical scheduling string is outside the ASCII subset");
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
  std::string result{"["};
  for (std::size_t index = 0U; index < values.size(); ++index) {
    if (index != 0U) {
      result.push_back(',');
    }
    result += quote(values[index]);
  }
  result.push_back(']');
  return result;
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

void validate_context_fields(
    std::string_view arithmetic,
    std::string_view parameter,
    std::string_view parent,
    std::string_view round,
    const Context& expected) {
  require(
      arithmetic == expected.arithmetic_profile_id && parameter == expected.parameter_schema_id &&
          parent == expected.parent_checkpoint_id && round == expected.round_config_id,
      ErrorCode::context_mismatch,
      "scheduling context does not match the round");
}

}  // namespace

SchedulingError::SchedulingError(ErrorCode code, std::string message)
    : std::runtime_error(std::move(message)), code_(code) {}

ErrorCode SchedulingError::code() const noexcept { return code_; }

void validate_domain_ticket_policy(
    const DomainTicketPolicy& policy,
    const Context& expected_context,
    const Limits& limits) {
  require(
      policy.allocation_policy == "CONTIGUOUS_NO_OVERLAP",
      ErrorCode::policy_invalid,
      "unsupported ticket allocation policy");
  validate_context_fields(
      policy.arithmetic_profile_id,
      policy.parameter_schema_id,
      policy.parent_checkpoint_id,
      policy.round_config_id,
      expected_context);
  require_content_id(policy.dataset_manifest_id, "dataset manifest ID is invalid");
  require_content_id(policy.eligibility_policy_id, "eligibility policy ID is invalid");
  require_content_id(policy.mixture_coefficient_id, "mixture coefficient ID is invalid");
  require_label(policy.domain_id, "domain ID is invalid");
  require(
      policy.batch_budget > 0U && policy.batch_budget <= 2'147'483'647U &&
          policy.step_budget > 0U && policy.step_budget <= 2'147'483'647U,
      ErrorCode::policy_invalid,
      "fixed batch or step budget is invalid");
  require(
      policy.ticket_count > 0U && policy.ticket_count <= limits.tickets,
      ErrorCode::policy_invalid,
      "domain ticket count is outside limits");
  require(
      policy.token_cursor_start < policy.token_cursor_end,
      ErrorCode::allocation_invalid,
      "domain token cursor is empty or reversed");
  const auto span = policy.token_cursor_end - policy.token_cursor_start;
  require(
      span >= policy.ticket_count && (span % policy.ticket_count) == 0U,
      ErrorCode::allocation_invalid,
      "domain token range cannot be partitioned exactly");
  require(
      !policy.region_ids.empty() && policy.region_ids.size() <= limits.domains &&
          std::is_sorted(policy.region_ids.begin(), policy.region_ids.end()) &&
          std::adjacent_find(policy.region_ids.begin(), policy.region_ids.end()) ==
              policy.region_ids.end(),
      ErrorCode::policy_invalid,
      "policy region set is not canonical");
  for (const auto& region : policy.region_ids) {
    require_label(region, "policy region ID is invalid");
  }
}

void validate_work_ticket(
    const WorkTicket& ticket,
    const Context& expected_context,
    const DomainTicketPolicy& policy) {
  validate_context_fields(
      ticket.arithmetic_profile_id,
      ticket.parameter_schema_id,
      ticket.parent_checkpoint_id,
      ticket.round_config_id,
      expected_context);
  require_content_id(ticket.normalized_artifact_id, "normalized artifact ID is invalid");
  require_label(ticket.domain_id, "ticket domain ID is invalid");
  require_label(ticket.ticket_id, "ticket ID is invalid");
  const auto policy_bytes = canonical_domain_ticket_policy(policy);
  require(
      ticket.policy_id == domain_ticket_policy_content_id(policy_bytes),
      ErrorCode::ticket_invalid,
      "ticket policy identity does not match the immutable policy");
  require(
      ticket.domain_id == policy.domain_id && ticket.batch_budget == policy.batch_budget &&
          ticket.step_budget == policy.step_budget,
      ErrorCode::ticket_invalid,
      "ticket fixed work differs from the domain policy");
  require(
      ticket.token_cursor_start >= policy.token_cursor_start &&
          ticket.token_cursor_end <= policy.token_cursor_end &&
          ticket.token_cursor_start < ticket.token_cursor_end,
      ErrorCode::allocation_invalid,
      "ticket data range is outside the domain allocation");
}

DomainTicketPolicy parse_domain_ticket_policy(
    std::span<const std::byte> canonical_json,
    const Context& expected_context,
    const Limits& limits) {
  require(
      !canonical_json.empty() && canonical_json.size() <= limits.contract_bytes,
      ErrorCode::input_too_large,
      "domain policy byte length is outside limits");
  const auto text = std::string_view(
      reinterpret_cast<const char*>(canonical_json.data()), canonical_json.size());
  const auto root = CanonicalJsonParser(text, limits).parse();
  require_keys(
      root,
      {"allocation_policy", "arithmetic_profile_id", "batch_budget", "dataset_manifest_id",
       "domain_id", "eligibility_policy_id", "formal_semantics_id", "mixture_coefficient_id",
       "parameter_schema_id", "parent_checkpoint_id", "region_ids", "round_config_id",
       "schema_version", "step_budget", "ticket_count", "token_cursor_end",
       "token_cursor_start", "type_name"},
      "domain ticket policy field set is invalid");
  require(
      string_member(root, "formal_semantics_id") == formal_semantics_id &&
          string_member(root, "schema_version") == schema_version &&
          string_member(root, "type_name") == "DOMAIN_TICKET_POLICY",
      ErrorCode::context_mismatch,
      "domain policy envelope identity is invalid");
  DomainTicketPolicy policy{
      string_member(root, "allocation_policy"),
      string_member(root, "arithmetic_profile_id"),
      unsigned_member(root, "batch_budget"),
      string_member(root, "dataset_manifest_id"),
      string_member(root, "domain_id"),
      string_member(root, "eligibility_policy_id"),
      string_member(root, "mixture_coefficient_id"),
      string_member(root, "parameter_schema_id"),
      string_member(root, "parent_checkpoint_id"),
      string_array(root, "region_ids", limits.domains),
      string_member(root, "round_config_id"),
      unsigned_member(root, "step_budget"),
      unsigned_member(root, "ticket_count"),
      unsigned_member(root, "token_cursor_end"),
      unsigned_member(root, "token_cursor_start"),
  };
  validate_domain_ticket_policy(policy, expected_context, limits);
  return policy;
}

WorkTicket parse_work_ticket(
    std::span<const std::byte> canonical_json,
    const Context& expected_context,
    const DomainTicketPolicy& policy,
    const Limits& limits) {
  require(
      !canonical_json.empty() && canonical_json.size() <= limits.contract_bytes,
      ErrorCode::input_too_large,
      "work ticket byte length is outside limits");
  const auto text = std::string_view(
      reinterpret_cast<const char*>(canonical_json.data()), canonical_json.size());
  const auto root = CanonicalJsonParser(text, limits).parse();
  require_keys(
      root,
      {"arithmetic_profile_id", "batch_budget", "domain_id", "formal_semantics_id",
       "normalized_artifact_id", "parameter_schema_id", "parent_checkpoint_id", "policy_id",
       "round_config_id", "schema_version", "step_budget", "ticket_id", "token_cursor_end",
       "token_cursor_start", "type_name"},
      "work ticket field set is invalid");
  require(
      string_member(root, "formal_semantics_id") == formal_semantics_id &&
          string_member(root, "schema_version") == schema_version &&
          string_member(root, "type_name") == "SCHEDULING_WORK_TICKET",
      ErrorCode::context_mismatch,
      "work ticket envelope identity is invalid");
  WorkTicket ticket{
      string_member(root, "arithmetic_profile_id"),
      unsigned_member(root, "batch_budget"),
      string_member(root, "domain_id"),
      string_member(root, "normalized_artifact_id"),
      string_member(root, "parameter_schema_id"),
      string_member(root, "parent_checkpoint_id"),
      string_member(root, "policy_id"),
      string_member(root, "round_config_id"),
      unsigned_member(root, "step_budget"),
      string_member(root, "ticket_id"),
      unsigned_member(root, "token_cursor_end"),
      unsigned_member(root, "token_cursor_start"),
  };
  validate_work_ticket(ticket, expected_context, policy);
  return ticket;
}

std::vector<std::byte> canonical_domain_ticket_policy(const DomainTicketPolicy& policy) {
  std::string output{"{"};
  append_field(output, "allocation_policy", quote(policy.allocation_policy));
  append_field(output, "arithmetic_profile_id", quote(policy.arithmetic_profile_id));
  append_field(output, "batch_budget", std::to_string(policy.batch_budget));
  append_field(output, "dataset_manifest_id", quote(policy.dataset_manifest_id));
  append_field(output, "domain_id", quote(policy.domain_id));
  append_field(output, "eligibility_policy_id", quote(policy.eligibility_policy_id));
  append_field(output, "formal_semantics_id", quote(formal_semantics_id));
  append_field(output, "mixture_coefficient_id", quote(policy.mixture_coefficient_id));
  append_field(output, "parameter_schema_id", quote(policy.parameter_schema_id));
  append_field(output, "parent_checkpoint_id", quote(policy.parent_checkpoint_id));
  append_field(output, "region_ids", string_array_json(policy.region_ids));
  append_field(output, "round_config_id", quote(policy.round_config_id));
  append_field(output, "schema_version", quote(schema_version));
  append_field(output, "step_budget", std::to_string(policy.step_budget));
  append_field(output, "ticket_count", std::to_string(policy.ticket_count));
  append_field(output, "token_cursor_end", std::to_string(policy.token_cursor_end));
  append_field(output, "token_cursor_start", std::to_string(policy.token_cursor_start));
  append_field(output, "type_name", quote("DOMAIN_TICKET_POLICY"));
  output.push_back('}');
  return bytes(std::move(output));
}

std::vector<std::byte> canonical_work_ticket(const WorkTicket& ticket) {
  std::string output{"{"};
  append_field(output, "arithmetic_profile_id", quote(ticket.arithmetic_profile_id));
  append_field(output, "batch_budget", std::to_string(ticket.batch_budget));
  append_field(output, "domain_id", quote(ticket.domain_id));
  append_field(output, "formal_semantics_id", quote(formal_semantics_id));
  append_field(output, "normalized_artifact_id", quote(ticket.normalized_artifact_id));
  append_field(output, "parameter_schema_id", quote(ticket.parameter_schema_id));
  append_field(output, "parent_checkpoint_id", quote(ticket.parent_checkpoint_id));
  append_field(output, "policy_id", quote(ticket.policy_id));
  append_field(output, "round_config_id", quote(ticket.round_config_id));
  append_field(output, "schema_version", quote(schema_version));
  append_field(output, "step_budget", std::to_string(ticket.step_budget));
  append_field(output, "ticket_id", quote(ticket.ticket_id));
  append_field(output, "token_cursor_end", std::to_string(ticket.token_cursor_end));
  append_field(output, "token_cursor_start", std::to_string(ticket.token_cursor_start));
  append_field(output, "type_name", quote("SCHEDULING_WORK_TICKET"));
  output.push_back('}');
  return bytes(std::move(output));
}

std::string domain_ticket_policy_content_id(std::span<const std::byte> canonical_json) {
  return content_id_for("deltareduce.007.domain-ticket-policy.v1", canonical_json);
}

std::string work_ticket_content_id(std::span<const std::byte> canonical_json) {
  return content_id_for("deltareduce.007.work-ticket.v1", canonical_json);
}

}  // namespace delta::scheduling
