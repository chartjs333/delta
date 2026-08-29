#include <delta/distribution/certification_policy.hpp>

#include <delta/core/canonical.hpp>

#include <algorithm>
#include <cctype>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace delta::distribution {
namespace {

enum class JsonType { boolean, unsigned_integer, string, array, object };

struct JsonValue {
  JsonType type = JsonType::string;
  bool boolean = false;
  std::uint64_t unsigned_integer = 0U;
  std::string string;
  std::vector<JsonValue> array;
  std::vector<std::string> object_keys;
  std::vector<JsonValue> object_values;
};

class ParseError final : public std::runtime_error {
 public:
  explicit ParseError(const char* message) : std::runtime_error(message) {}
};

class CanonicalJsonParser final {
 public:
  explicit CanonicalJsonParser(std::string_view input) : input_(input) {}

  [[nodiscard]] JsonValue parse() {
    skip_relaxed_space();
    auto result = parse_value(0U);
    skip_relaxed_space();
    require(cursor_ == input_.size(), "trailing JSON bytes");
    return result;
  }

 private:
  static constexpr std::size_t max_depth = 32U;
  static constexpr std::size_t max_members = 20'000U;

  void require(bool condition, const char* message) const {
    if (!condition) {
      throw ParseError(message);
    }
  }

  void skip_relaxed_space() {
#if defined(DELTA_DISTRIBUTION_MUTANT_ALLOW_NONCANONICAL)
    while (cursor_ < input_.size() &&
           std::isspace(static_cast<unsigned char>(input_[cursor_])) != 0) {
      ++cursor_;
    }
#endif
  }

  [[nodiscard]] bool take(char expected) {
    skip_relaxed_space();
    if (cursor_ < input_.size() && input_[cursor_] == expected) {
      ++cursor_;
      return true;
    }
    return false;
  }

  [[nodiscard]] JsonValue parse_value(std::size_t depth) {
    require(depth <= max_depth, "JSON nesting limit exceeded");
    skip_relaxed_space();
    require(cursor_ < input_.size(), "JSON value is truncated");
    switch (input_[cursor_]) {
      case '{':
        return parse_object(depth + 1U);
      case '[':
        return parse_array(depth + 1U);
      case '"': {
        JsonValue result;
        result.type = JsonType::string;
        result.string = parse_string();
        return result;
      }
      case 't':
        return parse_boolean(true);
      case 'f':
        return parse_boolean(false);
      default:
        return parse_unsigned();
    }
  }

  [[nodiscard]] JsonValue parse_object(std::size_t depth) {
    require(take('{'), "object start is missing");
    JsonValue result;
    result.type = JsonType::object;
    if (take('}')) {
      return result;
    }
    std::string prior_key;
    for (;;) {
      skip_relaxed_space();
      require(cursor_ < input_.size() && input_[cursor_] == '"', "object key is missing");
      auto key = parse_string();
      require(prior_key.empty() || prior_key < key, "object keys are not canonical");
      require(take(':'), "object colon is missing");
      require(++members_ <= max_members, "JSON member limit exceeded");
      auto value = parse_value(depth);
      result.object_keys.push_back(key);
      result.object_values.push_back(std::move(value));
      prior_key = std::move(key);
      if (take('}')) {
        return result;
      }
      require(take(','), "object comma is missing");
    }
  }

  [[nodiscard]] JsonValue parse_array(std::size_t depth) {
    require(take('['), "array start is missing");
    JsonValue result;
    result.type = JsonType::array;
    if (take(']')) {
      return result;
    }
    for (;;) {
      require(++members_ <= max_members, "JSON member limit exceeded");
      result.array.push_back(parse_value(depth));
      if (take(']')) {
        return result;
      }
      require(take(','), "array comma is missing");
    }
  }

  [[nodiscard]] std::string parse_string() {
    require(cursor_ < input_.size() && input_[cursor_] == '"', "string start is missing");
    ++cursor_;
    const auto begin = cursor_;
    while (cursor_ < input_.size() && input_[cursor_] != '"') {
      const auto value = static_cast<unsigned char>(input_[cursor_]);
      require(value >= 0x20U && value <= 0x7eU && input_[cursor_] != '\\',
              "string is outside canonical ASCII subset");
      ++cursor_;
    }
    require(cursor_ < input_.size(), "string is truncated");
    auto result = std::string(input_.substr(begin, cursor_ - begin));
    ++cursor_;
    return result;
  }

  [[nodiscard]] JsonValue parse_boolean(bool value) {
    const auto literal = value ? std::string_view{"true"} : std::string_view{"false"};
    require(input_.substr(cursor_, literal.size()) == literal, "boolean is malformed");
    cursor_ += literal.size();
    JsonValue result;
    result.type = JsonType::boolean;
    result.boolean = value;
    return result;
  }

  [[nodiscard]] JsonValue parse_unsigned() {
    require(cursor_ < input_.size() && input_[cursor_] >= '0' && input_[cursor_] <= '9',
            "only canonical unsigned JSON integers are accepted");
    const auto begin = cursor_;
    if (input_[cursor_] == '0') {
      ++cursor_;
      require(cursor_ == input_.size() || input_[cursor_] < '0' || input_[cursor_] > '9',
              "integer contains a leading zero");
    } else {
      while (cursor_ < input_.size() && input_[cursor_] >= '0' && input_[cursor_] <= '9') {
        ++cursor_;
      }
    }
    std::uint64_t value = 0U;
    for (const char digit : input_.substr(begin, cursor_ - begin)) {
      const auto next = static_cast<unsigned>(digit - '0');
      require(value <= (std::numeric_limits<std::uint64_t>::max() - next) / 10U,
              "integer overflows uint64");
      value = value * 10U + next;
    }
    JsonValue result;
    result.type = JsonType::unsigned_integer;
    result.unsigned_integer = value;
    return result;
  }

  std::string_view input_;
  std::size_t cursor_ = 0U;
  std::size_t members_ = 0U;
};

[[nodiscard]] const JsonValue* find_member(const JsonValue& object, std::string_view key) {
  if (object.type != JsonType::object) {
    return nullptr;
  }
  const auto item = std::lower_bound(object.object_keys.begin(), object.object_keys.end(), key);
  if (item == object.object_keys.end() || *item != key) {
    return nullptr;
  }
  const auto index = static_cast<std::size_t>(item - object.object_keys.begin());
  return &object.object_values[index];
}

[[nodiscard]] const std::string* string_member(const JsonValue& object, std::string_view key) {
  const auto* value = find_member(object, key);
  return value != nullptr && value->type == JsonType::string ? &value->string : nullptr;
}

[[nodiscard]] const std::uint64_t* unsigned_member(
    const JsonValue& object,
    std::string_view key) {
  const auto* value = find_member(object, key);
  return value != nullptr && value->type == JsonType::unsigned_integer
             ? &value->unsigned_integer
             : nullptr;
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

[[nodiscard]] PolicyDecision reject(
    std::string code,
    std::string manifest_id = {},
    std::string policy_id = {}) {
  return PolicyDecision{false, std::move(code), std::move(manifest_id), std::move(policy_id),
                        "ACT-PUBLISH"};
}

[[maybe_unused, nodiscard]] bool forbidden_media(std::string_view media_type) noexcept {
  constexpr std::string_view forbidden[] = {
      "application/vnd.deltareduce.ac-fragment;version=1",
      "application/vnd.deltareduce.commitment;version=1",
      "application/vnd.deltareduce.input-candidate;version=1",
      "application/vnd.deltareduce.parameter-partial;version=1",
      "application/vnd.deltareduce.regional-partial;version=1",
      "application/vnd.deltareduce.worker-q-shard;version=1",
  };
  return std::find(std::begin(forbidden), std::end(forbidden), media_type) !=
         std::end(forbidden);
}

[[nodiscard]] std::string json_string(std::string_view value) {
  std::string result;
  result.reserve(value.size() + 2U);
  result.push_back('"');
  for (const char character : value) {
    if (character == '"' || character == '\\') {
      result.push_back('\\');
    }
    result.push_back(character);
  }
  result.push_back('"');
  return result;
}

}  // namespace

std::string PolicyDecision::canonical_effect_json() const {
  return std::string{"{\"certificate_policy_id\":"} + json_string(certificate_policy_id) +
         ",\"code\":" + json_string(code) + ",\"formal_action_id\":" +
         json_string(formal_action_id) + ",\"manifest_id\":" + json_string(manifest_id) +
         ",\"status\":" + json_string(accepted ? "ACCEPT" : "REJECT") + "}";
}

std::string object_manifest_id(std::span<const std::byte> canonical_manifest) {
  constexpr auto domain = std::string_view{"deltareduce.005.object-manifest.v1"};
  std::vector<std::byte> input;
  input.reserve(domain.size() + 1U + canonical_manifest.size());
  for (const char character : domain) {
    input.push_back(static_cast<std::byte>(character));
  }
  input.push_back(std::byte{0});
  input.insert(input.end(), canonical_manifest.begin(), canonical_manifest.end());
  return "sha256:" + delta::core::canonical::sha256_hex(input);
}

PolicyDecision evaluate_certified_manifest(
    std::span<const std::byte> canonical_manifest,
    std::span<const std::byte> canonical_certificate,
    bool request_make_current) {
  if (canonical_manifest.size() > max_manifest_bytes) {
    return reject("MANIFEST_TOO_LARGE");
  }
  if (canonical_certificate.size() > max_certificate_bytes) {
    return reject("CERTIFICATE_TOO_LARGE");
  }
  const auto manifest_id = object_manifest_id(canonical_manifest);
  JsonValue manifest;
  JsonValue certificate;
  try {
    const auto manifest_text = std::string_view(
        reinterpret_cast<const char*>(canonical_manifest.data()), canonical_manifest.size());
    const auto certificate_text = std::string_view(
        reinterpret_cast<const char*>(canonical_certificate.data()), canonical_certificate.size());
    manifest = CanonicalJsonParser(manifest_text).parse();
    certificate = CanonicalJsonParser(certificate_text).parse();
  } catch (const ParseError&) {
    return reject("CANONICAL_JSON_INVALID", manifest_id);
  }
  if (manifest.type != JsonType::object || certificate.type != JsonType::object) {
    return reject("CANONICAL_JSON_INVALID", manifest_id);
  }

  const auto* policy = string_member(manifest, "certificate_policy_id");
  const auto policy_value = policy == nullptr ? std::string{} : *policy;
  if (policy == nullptr || !content_id_valid(*policy)) {
    return reject("POLICY_UNKNOWN", manifest_id, policy_value);
  }
  if (*policy == inactive_apply_policy_id) {
    return reject("POLICY_INACTIVE", manifest_id, *policy);
  }
#if !defined(DELTA_DISTRIBUTION_MUTANT_ALLOW_DOWNGRADE)
  if (*policy != aggregate_policy_id) {
    return reject("POLICY_UNKNOWN", manifest_id, *policy);
  }
#endif
  const auto* registry = string_member(manifest, "policy_registry_id");
  if (registry == nullptr || *registry != policy_registry_id) {
    return reject("POLICY_WEAKER", manifest_id, *policy);
  }
  const auto* media = string_member(manifest, "media_type");
#if !defined(DELTA_DISTRIBUTION_MUTANT_ALLOW_FORBIDDEN)
  if (media != nullptr && forbidden_media(*media)) {
    return reject("MEDIA_FORBIDDEN", manifest_id, *policy);
  }
#endif
  if (request_make_current) {
    return reject("CURRENT_REQUIRES_APPLY_QC", manifest_id, *policy);
  }
  if (media == nullptr || *media != aggregate_media_type) {
    return reject("POLICY_WEAKER", manifest_id, *policy);
  }

  const auto* type_name = string_member(manifest, "type_name");
  const auto* schema_version = string_member(manifest, "schema_version");
  const auto* formal_id = string_member(manifest, "formal_semantics_id");
  const auto* source_state = string_member(manifest, "source_state");
  const auto* source_root = string_member(manifest, "source_state_root");
  const auto* certificate_root = string_member(manifest, "certificate_root");
  const auto* piece_profile = string_member(manifest, "piece_profile_id");
  const auto* payload_hash = string_member(manifest, "payload_sha256");
  const auto* piece_tree_root = string_member(manifest, "piece_tree_root");
  const auto* total_length = unsigned_member(manifest, "total_length");
  const auto* pieces = find_member(manifest, "pieces");
  if (type_name == nullptr || *type_name != "OBJECT_MANIFEST" || schema_version == nullptr ||
      *schema_version != "1.0.0" || formal_id == nullptr || *formal_id != formal_semantics_id ||
      source_state == nullptr || *source_state != "AGGREGATED" || source_root == nullptr ||
      certificate_root == nullptr || piece_profile == nullptr ||
      *piece_profile !=
          "sha256:de9ca7f1a4e2630f729227e34d51c0c03c565062cc9ba924e465a884acc7987d" ||
      payload_hash == nullptr || !content_id_valid(*payload_hash) || piece_tree_root == nullptr ||
      !content_id_valid(*piece_tree_root) || total_length == nullptr || pieces == nullptr ||
      pieces->type != JsonType::array) {
    return reject("MANIFEST_CONTRACT_MISMATCH", manifest_id, *policy);
  }
  if (!content_id_valid(*source_root) || !content_id_valid(*certificate_root)) {
    return reject("MANIFEST_CONTRACT_MISMATCH", manifest_id, *policy);
  }
  if (*total_length > max_object_bytes || pieces->array.size() > max_piece_count) {
    return reject("OBJECT_LIMIT_EXCEEDED", manifest_id, *policy);
  }
  std::uint64_t expected_offset = 0U;
  for (std::size_t ordinal = 0U; ordinal < pieces->array.size(); ++ordinal) {
    const auto& piece = pieces->array[ordinal];
    const auto* piece_ordinal = unsigned_member(piece, "ordinal");
    const auto* offset = unsigned_member(piece, "offset");
    const auto* length = unsigned_member(piece, "length");
    const auto* content_id = string_member(piece, "content_id");
    if (piece_ordinal == nullptr || *piece_ordinal != ordinal || offset == nullptr ||
        *offset != expected_offset || length == nullptr || *length == 0U ||
        *length > max_piece_bytes ||
        (ordinal + 1U < pieces->array.size() && *length != max_piece_bytes) ||
        content_id == nullptr || !content_id_valid(*content_id) ||
        expected_offset > max_object_bytes - *length) {
      return reject("PIECE_LAYOUT_INVALID", manifest_id, *policy);
    }
    expected_offset += *length;
  }
  if (expected_offset != *total_length || (pieces->array.empty() != (*total_length == 0U))) {
    return reject("PIECE_LAYOUT_INVALID", manifest_id, *policy);
  }

  const auto* certificate_type = string_member(certificate, "type_name");
  const auto* certificate_formal = string_member(certificate, "formal_semantics_id");
  const auto* certificate_state = string_member(certificate, "source_state");
  const auto* certificate_source_root = string_member(certificate, "source_state_root");
  const auto* actual_certificate_root = string_member(certificate, "certificate_root");
  if (certificate_type == nullptr || *certificate_type != "AGGREGATED_TRANSITION_CERTIFICATE" ||
      certificate_formal == nullptr || *certificate_formal != formal_semantics_id ||
      certificate_state == nullptr || *certificate_state != "AGGREGATED" ||
      certificate_source_root == nullptr || actual_certificate_root == nullptr ||
      !content_id_valid(*certificate_source_root) || !content_id_valid(*actual_certificate_root)) {
    return reject("CERTIFICATE_CONTRACT_MISMATCH", manifest_id, *policy);
  }
  if (*actual_certificate_root != *certificate_root) {
    return reject("CERTIFICATE_ROOT_MISMATCH", manifest_id, *policy);
  }
  if (*certificate_source_root != *source_root) {
    return reject("SOURCE_STATE_ROOT_MISMATCH", manifest_id, *policy);
  }
  return PolicyDecision{true, "OK", manifest_id, *policy, "ACT-PUBLISH"};
}

PolicyDecision evaluate_applied_checkpoint(
    std::span<const std::byte> canonical_manifest,
    const certificates::ApplyQc& apply_qc,
    bool request_make_current) {
  if (canonical_manifest.size() > max_manifest_bytes) {
    return reject("MANIFEST_TOO_LARGE");
  }
  const auto manifest_id = object_manifest_id(canonical_manifest);
  JsonValue manifest;
  try {
    const auto manifest_text = std::string_view(
        reinterpret_cast<const char*>(canonical_manifest.data()), canonical_manifest.size());
    manifest = CanonicalJsonParser(manifest_text).parse();
    (void)certificates::content_id(apply_qc);
  } catch (const std::exception&) {
    return reject("CANONICAL_JSON_INVALID", manifest_id, std::string(inactive_apply_policy_id));
  }
  const auto* policy = string_member(manifest, "certificate_policy_id");
  const auto* registry = string_member(manifest, "policy_registry_id");
  const auto* media = string_member(manifest, "media_type");
  const auto* source_state = string_member(manifest, "source_state");
  const auto* certificate_root = string_member(manifest, "certificate_root");
  const auto* formal_id = string_member(manifest, "formal_semantics_id");
  if (!request_make_current || policy == nullptr || *policy != inactive_apply_policy_id ||
      registry == nullptr || *registry != policy_registry_id || media == nullptr ||
      *media != "application/vnd.deltareduce.checkpoint;version=1" || source_state == nullptr ||
      *source_state != "APPLIED" || certificate_root == nullptr ||
      *certificate_root != apply_qc.next_model_hash || formal_id == nullptr ||
      *formal_id != formal_semantics_id) {
    return reject("APPLY_POLICY_MISMATCH", manifest_id, std::string(inactive_apply_policy_id));
  }
  return PolicyDecision{
      true,
      "OK",
      manifest_id,
      std::string(inactive_apply_policy_id),
      "ACT-APPLY-CURRENT",
  };
}

}  // namespace delta::distribution
