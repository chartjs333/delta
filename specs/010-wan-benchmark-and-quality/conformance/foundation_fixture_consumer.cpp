#include <array>
#include <charconv>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <initializer_list>
#include <iostream>
#include <iterator>
#include <limits>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace {
constexpr std::array<std::string_view, 7> kArtifactNames = {
    "arm", "attestation", "definition", "evidence_manifest", "evidence_node", "result",
    "run_manifest",
};
constexpr std::array<std::string_view, 7> kExpectedIds = {
    "sha256:476b466992370b989ac24ef63569bb179b1c3ac9e215b8ce01fe68054c5c9b73",
    "sha256:0ce29dfbdab797db41850031ec6ee4fdd01fe8ea34ec1e4e0a63ba31ced39892",
    "sha256:32c8e884d1d93a3de77881d30df2bf78ed45d59017b38ca1318664e77485a449",
    "sha256:4ae1806f1ce4fb165d698f6d28648e4287b47689332c8859df008695ad8b6308",
    "sha256:50c42bee228b98c5bb58238251ef897fdc2a2286027f4f2f011dfc86b6e8efbb",
    "sha256:1f29322d968fd99538395765dafea1cc37c6d052cdb5160ca543b289d7b95faa",
    "sha256:e837f264cc59a92a1537aa24d44cefe9410008f2c826a5c50e3172455309e2cc",
};
constexpr std::array<std::string_view, 7> kExpectedTypes = {
    "BENCHMARK_ARM",
    "BENCHMARK_ATTESTATION_MANIFEST",
    "BENCHMARK_DEFINITION",
    "BENCHMARK_EVIDENCE_MANIFEST",
    "BENCHMARK_EVIDENCE_NODE",
    "BENCHMARK_RESULT",
    "BENCHMARK_RUN_MANIFEST",
};
constexpr std::string_view kFormalSemanticsId =
    "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
constexpr std::size_t kDefinitionIndex = 2U;
constexpr std::size_t kResultIndex = 5U;
constexpr std::size_t kRunManifestIndex = 6U;
constexpr auto kCorpusPrefix =
    R"json({"artifact_ids":["sha256:476b466992370b989ac24ef63569bb179b1c3ac9e215b8ce01fe68054c5c9b73","sha256:0ce29dfbdab797db41850031ec6ee4fdd01fe8ea34ec1e4e0a63ba31ced39892","sha256:32c8e884d1d93a3de77881d30df2bf78ed45d59017b38ca1318664e77485a449","sha256:4ae1806f1ce4fb165d698f6d28648e4287b47689332c8859df008695ad8b6308","sha256:50c42bee228b98c5bb58238251ef897fdc2a2286027f4f2f011dfc86b6e8efbb","sha256:1f29322d968fd99538395765dafea1cc37c6d052cdb5160ca543b289d7b95faa","sha256:e837f264cc59a92a1537aa24d44cefe9410008f2c826a5c50e3172455309e2cc"],"execution_class":"CONFORMANCE_SAFETY_ONLY","formal_semantics_id":"sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6","negative_statuses":[{"case_id":"definition-leading-space","status":"JSON_BYTES_NOT_CANONICAL"},{"case_id":"run-primary-promotion","status":"PRIMARY_ELIGIBILITY_FORBIDDEN"}],"primary_observation_count":0,"schema_version":"1.0.0","status":"PASS","type_name":"FEATURE010_EXACTNESS_CORPUS"})json";
constexpr auto kExpectedHex =
    "7b22616461707465725f6964223a227368613235363a34633262333736393664643037633862376465666666323163643932343865393837623564346133393761363562643539353430613865323732333735366336222c2261726d5f6b696e64223a2244454c5441524544554345222c22617574686f726974795f73636f7065223a2242454e43484d41524b5f474f5645524e414e43455f4f4e4c59222c226465706c6f796d656e745f70726f66696c65223a22454d4245444445445f46464d222c2265766964656e63655f636c617373223a22544553545f46495854555245222c22666f726d616c5f73656d616e746963735f6964223a227368613235363a63633938663135616332306663336564323635636237363638326361313561393336653234363630613635316532623866383136333861626233323635636236222c22676174655f656c696769626c65223a66616c73652c226d6f64656c5f6d6f6465223a22514c4f52415f41444150544552222c227072696d6172795f656c696769626c65223a66616c73652c22736368656d615f76657273696f6e223a22312e302e30222c22746f706f6c6f6779223a2248494552415243484943414c222c22747970655f6e616d65223a2242454e43484d41524b5f41524d227d";
constexpr auto kExpectedCanonical =
    R"json({"adapter_id":"sha256:4c2b37696dd07c8b7defff21cd9248e987b5d4a397a65bd59540a8e2723756c6","arm_kind":"DELTAREDUCE","authority_scope":"BENCHMARK_GOVERNANCE_ONLY","deployment_profile":"EMBEDDED_FFM","evidence_class":"TEST_FIXTURE","formal_semantics_id":"sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6","gate_eligible":false,"model_mode":"QLORA_ADAPTER","primary_eligible":false,"schema_version":"1.0.0","topology":"HIERARCHICAL","type_name":"BENCHMARK_ARM"})json";

class ArtifactError final : public std::runtime_error {
 public:
  explicit ArtifactError(std::string status)
      : std::runtime_error(status), status_(std::move(status)) {}

  [[nodiscard]] const std::string& status() const noexcept { return status_; }

 private:
  std::string status_;
};

struct JsonValue {
  enum class Kind { null_value, boolean, integer, string, array, object };

  Kind kind{Kind::null_value};
  bool boolean{};
  std::int64_t integer{};
  std::string string;
  std::vector<JsonValue> array;
  std::vector<std::string> object_keys;
  std::vector<JsonValue> object_values;

  [[nodiscard]] const JsonValue& field(std::string_view name) const {
    if (kind != Kind::object) throw ArtifactError("JSON_BYTES_NOT_CANONICAL");
    for (std::size_t index = 0U; index < object_keys.size(); ++index) {
      if (object_keys[index] == name) return object_values[index];
    }
    throw ArtifactError("ARTIFACT_FIELD_MISSING");
  }

  [[nodiscard]] JsonValue& field(std::string_view name) {
    if (kind != Kind::object) throw ArtifactError("JSON_BYTES_NOT_CANONICAL");
    for (std::size_t index = 0U; index < object_keys.size(); ++index) {
      if (object_keys[index] == name) return object_values[index];
    }
    throw ArtifactError("ARTIFACT_FIELD_MISSING");
  }
};

[[nodiscard]] JsonValue json_boolean(bool value) {
  JsonValue result;
  result.kind = JsonValue::Kind::boolean;
  result.boolean = value;
  return result;
}

[[nodiscard]] JsonValue json_integer(std::int64_t value) {
  JsonValue result;
  result.kind = JsonValue::Kind::integer;
  result.integer = value;
  return result;
}

[[nodiscard]] JsonValue json_string(std::string value) {
  JsonValue result;
  result.kind = JsonValue::Kind::string;
  result.string = std::move(value);
  return result;
}

[[nodiscard]] JsonValue json_container(JsonValue::Kind kind) {
  JsonValue result;
  result.kind = kind;
  return result;
}

void append_utf8(std::string& output, std::uint32_t code_point) {
  if (code_point <= 0x7fU) {
    output.push_back(static_cast<char>(code_point));
  } else if (code_point <= 0x7ffU) {
    output.push_back(static_cast<char>(0xc0U | (code_point >> 6U)));
    output.push_back(static_cast<char>(0x80U | (code_point & 0x3fU)));
  } else if (code_point <= 0xffffU) {
    if (code_point >= 0xd800U && code_point <= 0xdfffU) {
      throw ArtifactError("JSON_BYTES_NOT_CANONICAL");
    }
    output.push_back(static_cast<char>(0xe0U | (code_point >> 12U)));
    output.push_back(static_cast<char>(0x80U | ((code_point >> 6U) & 0x3fU)));
    output.push_back(static_cast<char>(0x80U | (code_point & 0x3fU)));
  } else if (code_point <= 0x10ffffU) {
    output.push_back(static_cast<char>(0xf0U | (code_point >> 18U)));
    output.push_back(static_cast<char>(0x80U | ((code_point >> 12U) & 0x3fU)));
    output.push_back(static_cast<char>(0x80U | ((code_point >> 6U) & 0x3fU)));
    output.push_back(static_cast<char>(0x80U | (code_point & 0x3fU)));
  } else {
    throw ArtifactError("JSON_BYTES_NOT_CANONICAL");
  }
}

[[nodiscard]] bool is_utf8_continuation(unsigned char byte) {
  return byte >= 0x80U && byte <= 0xbfU;
}

void validate_utf8(std::string_view input) {
  const auto reject = [] { throw ArtifactError("JSON_BYTES_NOT_CANONICAL"); };
  std::size_t position = 0U;
  while (position < input.size()) {
    const auto lead = static_cast<unsigned char>(input[position]);
    if (lead <= 0x7fU) {
      ++position;
      continue;
    }
    if (lead >= 0xc2U && lead <= 0xdfU) {
      if (input.size() - position < 2U ||
          !is_utf8_continuation(static_cast<unsigned char>(input[position + 1U]))) {
        reject();
      }
      position += 2U;
      continue;
    }
    if (lead >= 0xe0U && lead <= 0xefU) {
      if (input.size() - position < 3U) reject();
      const auto second = static_cast<unsigned char>(input[position + 1U]);
      const auto third = static_cast<unsigned char>(input[position + 2U]);
      const auto second_valid =
          (lead == 0xe0U && second >= 0xa0U && second <= 0xbfU) ||
          (lead >= 0xe1U && lead <= 0xecU && is_utf8_continuation(second)) ||
          (lead == 0xedU && second >= 0x80U && second <= 0x9fU) ||
          (lead >= 0xeeU && lead <= 0xefU && is_utf8_continuation(second));
      if (!second_valid || !is_utf8_continuation(third)) reject();
      position += 3U;
      continue;
    }
    if (lead >= 0xf0U && lead <= 0xf4U) {
      if (input.size() - position < 4U) reject();
      const auto second = static_cast<unsigned char>(input[position + 1U]);
      const auto third = static_cast<unsigned char>(input[position + 2U]);
      const auto fourth = static_cast<unsigned char>(input[position + 3U]);
      const auto second_valid =
          (lead == 0xf0U && second >= 0x90U && second <= 0xbfU) ||
          (lead >= 0xf1U && lead <= 0xf3U && is_utf8_continuation(second)) ||
          (lead == 0xf4U && second >= 0x80U && second <= 0x8fU);
      if (!second_valid || !is_utf8_continuation(third) ||
          !is_utf8_continuation(fourth)) {
        reject();
      }
      position += 4U;
      continue;
    }
    reject();
  }
}

class JsonParser final {
 public:
  explicit JsonParser(std::string_view input) : input_(input) {}

  [[nodiscard]] JsonValue parse() {
    const auto result = parse_value();
    if (position_ != input_.size()) fail();
    return result;
  }

 private:
  [[noreturn]] static void fail() { throw ArtifactError("JSON_BYTES_NOT_CANONICAL"); }

  [[nodiscard]] char peek() const {
    if (position_ >= input_.size()) fail();
    return input_[position_];
  }

  bool consume(char value) {
    if (position_ < input_.size() && input_[position_] == value) {
      ++position_;
      return true;
    }
    return false;
  }

  void expect(char value) {
    if (!consume(value)) fail();
  }

  [[nodiscard]] JsonValue parse_value() {
    switch (peek()) {
      case 'n':
        parse_literal("null");
        return {};
      case 't':
        parse_literal("true");
        return json_boolean(true);
      case 'f':
        parse_literal("false");
        return json_boolean(false);
      case '"':
        return json_string(parse_string());
      case '[':
        return parse_array();
      case '{':
        return parse_object();
      default:
        if (peek() == '-' || (peek() >= '0' && peek() <= '9')) return parse_integer();
        fail();
    }
  }

  void parse_literal(std::string_view literal) {
    if (input_.substr(position_, literal.size()) != literal) fail();
    position_ += literal.size();
  }

  [[nodiscard]] std::uint32_t parse_hex_quad() {
    if (input_.size() - position_ < 4U) fail();
    std::uint32_t value = 0U;
    for (std::size_t index = 0U; index < 4U; ++index) {
      const auto digit = input_[position_++];
      value <<= 4U;
      if (digit >= '0' && digit <= '9') {
        value |= static_cast<std::uint32_t>(digit - '0');
      } else if (digit >= 'a' && digit <= 'f') {
        value |= static_cast<std::uint32_t>(digit - 'a' + 10);
      } else {
        fail();
      }
    }
    return value;
  }

  [[nodiscard]] std::string parse_string() {
    expect('"');
    std::string result;
    while (true) {
      const auto current = static_cast<unsigned char>(peek());
      ++position_;
      if (current == '"') return result;
      if (current < 0x20U) fail();
      if (current != '\\') {
        result.push_back(static_cast<char>(current));
        continue;
      }
      const auto escape = peek();
      ++position_;
      switch (escape) {
        case '"': result.push_back('"'); break;
        case '\\': result.push_back('\\'); break;
        case 'b': result.push_back('\b'); break;
        case 'f': result.push_back('\f'); break;
        case 'n': result.push_back('\n'); break;
        case 'r': result.push_back('\r'); break;
        case 't': result.push_back('\t'); break;
        case 'u': {
          auto code_point = parse_hex_quad();
          if (code_point >= 0xd800U && code_point <= 0xdbffU) {
            if (!consume('\\') || !consume('u')) fail();
            const auto low = parse_hex_quad();
            if (low < 0xdc00U || low > 0xdfffU) fail();
            code_point = 0x10000U + ((code_point - 0xd800U) << 10U) + (low - 0xdc00U);
          } else if (code_point >= 0xdc00U && code_point <= 0xdfffU) {
            fail();
          }
          append_utf8(result, code_point);
          break;
        }
        default: fail();
      }
    }
  }

  [[nodiscard]] JsonValue parse_integer() {
    const auto start = position_;
    consume('-');
    if (consume('0')) {
      if (position_ < input_.size() && input_[position_] >= '0' && input_[position_] <= '9') {
        fail();
      }
    } else {
      if (peek() < '1' || peek() > '9') fail();
      while (position_ < input_.size() && input_[position_] >= '0' && input_[position_] <= '9') {
        ++position_;
      }
    }
    const auto token = input_.substr(start, position_ - start);
    if (token == "-0") fail();
    std::int64_t value{};
    const auto [end, error] =
        std::from_chars(token.data(), token.data() + token.size(), value);
    if (error != std::errc{} || end != token.data() + token.size()) fail();
    return json_integer(value);
  }

  [[nodiscard]] JsonValue parse_array() {
    expect('[');
    auto result = json_container(JsonValue::Kind::array);
    if (consume(']')) return result;
    while (true) {
      result.array.push_back(parse_value());
      if (consume(']')) return result;
      expect(',');
    }
  }

  [[nodiscard]] JsonValue parse_object() {
    expect('{');
    auto result = json_container(JsonValue::Kind::object);
    if (consume('}')) return result;
    std::string previous;
    bool first = true;
    while (true) {
      if (peek() != '"') fail();
      auto key = parse_string();
      if (!first && previous >= key) fail();
      first = false;
      previous = key;
      expect(':');
      result.object_keys.push_back(std::move(key));
      result.object_values.push_back(parse_value());
      if (consume('}')) return result;
      expect(',');
    }
  }

  std::string_view input_;
  std::size_t position_{0U};
};

void append_json_string(std::string& output, std::string_view value) {
  constexpr char hex[] = "0123456789abcdef";
  output.push_back('"');
  for (const auto byte : value) {
    const auto current = static_cast<unsigned char>(byte);
    switch (current) {
      case '"': output += "\\\""; break;
      case '\\': output += "\\\\"; break;
      case '\b': output += "\\b"; break;
      case '\f': output += "\\f"; break;
      case '\n': output += "\\n"; break;
      case '\r': output += "\\r"; break;
      case '\t': output += "\\t"; break;
      default:
        if (current < 0x20U) {
          output += "\\u00";
          output.push_back(hex[current >> 4U]);
          output.push_back(hex[current & 0x0fU]);
        } else {
          output.push_back(static_cast<char>(current));
        }
    }
  }
  output.push_back('"');
}

void append_canonical_json(std::string& output, const JsonValue& value) {
  switch (value.kind) {
    case JsonValue::Kind::null_value: output += "null"; break;
    case JsonValue::Kind::boolean: output += value.boolean ? "true" : "false"; break;
    case JsonValue::Kind::integer: output += std::to_string(value.integer); break;
    case JsonValue::Kind::string: append_json_string(output, value.string); break;
    case JsonValue::Kind::array:
      output.push_back('[');
      for (std::size_t index = 0U; index < value.array.size(); ++index) {
        if (index != 0U) output.push_back(',');
        append_canonical_json(output, value.array[index]);
      }
      output.push_back(']');
      break;
    case JsonValue::Kind::object:
      output.push_back('{');
      if (value.object_keys.size() != value.object_values.size()) {
        throw ArtifactError("JSON_BYTES_NOT_CANONICAL");
      }
      for (std::size_t index = 0U; index < value.object_keys.size(); ++index) {
        if (index != 0U) output.push_back(',');
        append_json_string(output, value.object_keys[index]);
        output.push_back(':');
        append_canonical_json(output, value.object_values[index]);
      }
      output.push_back('}');
      break;
  }
}

[[nodiscard]] std::string canonical_json(const JsonValue& value) {
  std::string result;
  append_canonical_json(result, value);
  return result;
}

[[nodiscard]] JsonValue parse_canonical_artifact(std::string_view bytes) {
  validate_utf8(bytes);
  auto value = JsonParser(bytes).parse();
  if (canonical_json(value) != bytes) throw ArtifactError("JSON_BYTES_NOT_CANONICAL");
  return value;
}

[[nodiscard]] const std::string& string_value(const JsonValue& value) {
  if (value.kind != JsonValue::Kind::string) throw ArtifactError("ARTIFACT_FIELD_TYPE");
  return value.string;
}

[[nodiscard]] bool boolean_value(const JsonValue& value) {
  if (value.kind != JsonValue::Kind::boolean) throw ArtifactError("ARTIFACT_FIELD_TYPE");
  return value.boolean;
}

[[nodiscard]] JsonValue admit_artifact(std::string_view bytes, std::size_t artifact_index) {
  if (artifact_index >= kExpectedTypes.size()) throw ArtifactError("ARTIFACT_TYPE_UNKNOWN");
  auto value = parse_canonical_artifact(bytes);
  if (string_value(value.field("schema_version")) != "1.0.0") {
    throw ArtifactError("SCHEMA_VERSION_MISMATCH");
  }
  if (string_value(value.field("type_name")) != kExpectedTypes[artifact_index]) {
    throw ArtifactError("TYPE_NAME_MISMATCH");
  }
  if (string_value(value.field("formal_semantics_id")) != kFormalSemanticsId) {
    throw ArtifactError("FORMAL_SEMANTICS_MISMATCH");
  }
  if (string_value(value.field("authority_scope")) != "BENCHMARK_GOVERNANCE_ONLY" ||
      string_value(value.field("evidence_class")) != "TEST_FIXTURE") {
    throw ArtifactError("ARTIFACT_AUTHORITY_FORBIDDEN");
  }
  if (boolean_value(value.field("primary_eligible"))) {
    throw ArtifactError("PRIMARY_ELIGIBILITY_FORBIDDEN");
  }
  if (boolean_value(value.field("gate_eligible"))) {
    throw ArtifactError("GATE_ELIGIBILITY_FORBIDDEN");
  }
  if (artifact_index == kRunManifestIndex) {
    if (string_value(value.field("execution_mode")) != "CONFORMANCE_FIXTURE") {
      throw ArtifactError("EXECUTION_MODE_FORBIDDEN");
    }
    if (value.field("execution_authorization_id").kind != JsonValue::Kind::null_value) {
      throw ArtifactError("EXECUTION_AUTHORIZATION_FORBIDDEN");
    }
  } else if (artifact_index == kResultIndex &&
             string_value(value.field("decision")) != "NOT_EVALUATED") {
    throw ArtifactError("RESULT_DECISION_FORBIDDEN");
  }
  return value;
}

template <typename Operation>
[[nodiscard]] std::string rejection_status(Operation&& operation) {
  try {
    static_cast<void>(operation());
  } catch (const ArtifactError& error) {
    return error.status();
  }
  throw std::runtime_error("negative corpus mutation was admitted");
}

constexpr std::array<std::uint32_t, 64> kSha256Constants = {
    0x428a2f98U, 0x71374491U, 0xb5c0fbcfU, 0xe9b5dba5U, 0x3956c25bU, 0x59f111f1U,
    0x923f82a4U, 0xab1c5ed5U, 0xd807aa98U, 0x12835b01U, 0x243185beU, 0x550c7dc3U,
    0x72be5d74U, 0x80deb1feU, 0x9bdc06a7U, 0xc19bf174U, 0xe49b69c1U, 0xefbe4786U,
    0x0fc19dc6U, 0x240ca1ccU, 0x2de92c6fU, 0x4a7484aaU, 0x5cb0a9dcU, 0x76f988daU,
    0x983e5152U, 0xa831c66dU, 0xb00327c8U, 0xbf597fc7U, 0xc6e00bf3U, 0xd5a79147U,
    0x06ca6351U, 0x14292967U, 0x27b70a85U, 0x2e1b2138U, 0x4d2c6dfcU, 0x53380d13U,
    0x650a7354U, 0x766a0abbU, 0x81c2c92eU, 0x92722c85U, 0xa2bfe8a1U, 0xa81a664bU,
    0xc24b8b70U, 0xc76c51a3U, 0xd192e819U, 0xd6990624U, 0xf40e3585U, 0x106aa070U,
    0x19a4c116U, 0x1e376c08U, 0x2748774cU, 0x34b0bcb5U, 0x391c0cb3U, 0x4ed8aa4aU,
    0x5b9cca4fU, 0x682e6ff3U, 0x748f82eeU, 0x78a5636fU, 0x84c87814U, 0x8cc70208U,
    0x90befffaU, 0xa4506cebU, 0xbef9a3f7U, 0xc67178f2U,
};

std::uint32_t rotate_right(std::uint32_t value, unsigned count) {
  return (value >> count) | (value << (32U - count));
}

std::string sha256_hex(std::string_view input) {
  std::vector<std::uint8_t> bytes(input.begin(), input.end());
  const auto bit_length = static_cast<std::uint64_t>(bytes.size()) * 8U;
  bytes.push_back(0x80U);
  while (bytes.size() % 64U != 56U) bytes.push_back(0U);
  for (int shift = 56; shift >= 0; shift -= 8) {
    bytes.push_back(static_cast<std::uint8_t>((bit_length >> shift) & 0xffU));
  }

  std::array<std::uint32_t, 8> hash = {
      0x6a09e667U, 0xbb67ae85U, 0x3c6ef372U, 0xa54ff53aU,
      0x510e527fU, 0x9b05688cU, 0x1f83d9abU, 0x5be0cd19U,
  };
  for (std::size_t offset = 0; offset < bytes.size(); offset += 64U) {
    std::array<std::uint32_t, 64> words{};
    for (std::size_t index = 0; index < 16U; ++index) {
      const auto base = offset + index * 4U;
      words[index] = (static_cast<std::uint32_t>(bytes[base]) << 24U) |
                     (static_cast<std::uint32_t>(bytes[base + 1U]) << 16U) |
                     (static_cast<std::uint32_t>(bytes[base + 2U]) << 8U) |
                     static_cast<std::uint32_t>(bytes[base + 3U]);
    }
    for (std::size_t index = 16U; index < words.size(); ++index) {
      const auto s0 = rotate_right(words[index - 15U], 7U) ^
                      rotate_right(words[index - 15U], 18U) ^ (words[index - 15U] >> 3U);
      const auto s1 = rotate_right(words[index - 2U], 17U) ^
                      rotate_right(words[index - 2U], 19U) ^ (words[index - 2U] >> 10U);
      words[index] = words[index - 16U] + s0 + words[index - 7U] + s1;
    }

    auto a = hash[0];
    auto b = hash[1];
    auto c = hash[2];
    auto d = hash[3];
    auto e = hash[4];
    auto f = hash[5];
    auto g = hash[6];
    auto h = hash[7];
    for (std::size_t index = 0; index < words.size(); ++index) {
      const auto sum1 = rotate_right(e, 6U) ^ rotate_right(e, 11U) ^ rotate_right(e, 25U);
      const auto choose = (e & f) ^ ((~e) & g);
      const auto temp1 = h + sum1 + choose + kSha256Constants[index] + words[index];
      const auto sum0 = rotate_right(a, 2U) ^ rotate_right(a, 13U) ^ rotate_right(a, 22U);
      const auto majority = (a & b) ^ (a & c) ^ (b & c);
      const auto temp2 = sum0 + majority;
      h = g;
      g = f;
      f = e;
      e = d + temp1;
      d = c;
      c = b;
      b = a;
      a = temp1 + temp2;
    }
    hash[0] += a;
    hash[1] += b;
    hash[2] += c;
    hash[3] += d;
    hash[4] += e;
    hash[5] += f;
    hash[6] += g;
    hash[7] += h;
  }

  std::ostringstream output;
  output << std::hex << std::setfill('0');
  for (const auto word : hash) output << std::setw(8) << word;
  return output.str();
}

int nibble(char value) {
  if (value >= '0' && value <= '9') return value - '0';
  if (value >= 'a' && value <= 'f') return value - 'a' + 10;
  throw std::runtime_error("non-lowercase hex");
}

std::string decode_hex(const std::string& value) {
  if (value.size() % 2 != 0) throw std::runtime_error("odd hex length");
  std::string result;
  result.reserve(value.size() / 2);
  for (std::size_t index = 0; index < value.size(); index += 2) {
    result.push_back(static_cast<char>((nibble(value[index]) << 4) | nibble(value[index + 1])));
  }
  return result;
}
}  // namespace

int main(int argc, char** argv) {
  if (argc != 2 && argc != 3) throw std::runtime_error("fixture path required");
  std::ifstream input(argv[1], std::ios::binary);
  if (!input) throw std::runtime_error("fixture unavailable");
  const std::string fixture((std::istreambuf_iterator<char>(input)), {});
  std::string definition_canonical;
  std::string run_canonical;
  for (std::size_t index = 0; index < kArtifactNames.size(); ++index) {
    const auto prefix_text = std::string("\"") + std::string(kArtifactNames[index]) +
                             "\":{\"bytes_hex\":\"";
    const auto prefix = fixture.find(prefix_text);
    if (prefix == std::string::npos) throw std::runtime_error("artifact vector missing");
    const auto start = prefix + prefix_text.size();
    const auto end = fixture.find('"', start);
    const auto encoded = fixture.substr(start, end - start);
    if (index == 0 && encoded != kExpectedHex) throw std::runtime_error("fixture hex differs");
    const auto canonical = decode_hex(encoded);
    if (kArtifactNames[index] == "definition") definition_canonical = canonical;
    if (kArtifactNames[index] == "run_manifest") run_canonical = canonical;
    if (index == 0 && canonical != kExpectedCanonical) {
      throw std::runtime_error("canonical bytes differ");
    }
    static_cast<void>(admit_artifact(canonical, index));
    const auto actual_id = std::string("sha256:") + sha256_hex(canonical);
    if (actual_id != kExpectedIds[index]) throw std::runtime_error("content ID differs");
    const auto stored_prefix = fixture.find(",\"content_id\":\"", end);
    if (stored_prefix == std::string::npos) {
      throw std::runtime_error("stored content ID missing");
    }
    const auto stored_start = stored_prefix + std::string(",\"content_id\":\"").size();
    const auto stored_end = fixture.find('"', stored_start);
    if (fixture.substr(stored_start, stored_end - stored_start) != actual_id) {
      throw std::runtime_error("stored content ID differs");
    }
  }
  if (argc == 3) {
    if (std::string_view(argv[2]) != "--emit-corpus") {
      throw std::runtime_error("unknown mode");
    }
    const auto canonical_status = rejection_status(
        [&] { return admit_artifact(" " + definition_canonical, kDefinitionIndex); });
    auto promoted_run = parse_canonical_artifact(run_canonical);
    auto& primary_eligible = promoted_run.field("primary_eligible");
    if (primary_eligible.kind != JsonValue::Kind::boolean || primary_eligible.boolean) {
      throw std::runtime_error("run policy field invalid");
    }
    primary_eligible.boolean = true;
    const auto promoted = canonical_json(promoted_run);
    const auto primary_status =
        rejection_status([&] { return admit_artifact(promoted, kRunManifestIndex); });
    const auto invalid_utf8_object = [](std::initializer_list<unsigned int> encoded) {
      std::string candidate = "{\"value\":\"";
      for (const auto byte : encoded) candidate.push_back(static_cast<char>(byte));
      candidate += "\"}";
      return candidate;
    };
    const std::array invalid_utf8_cases = {
        invalid_utf8_object({0x80U}),
        invalid_utf8_object({0xc0U, 0xafU}),
        invalid_utf8_object({0xedU, 0xa0U, 0x80U}),
    };
    for (const auto& invalid_utf8 : invalid_utf8_cases) {
      const auto status =
          rejection_status([&] { return parse_canonical_artifact(invalid_utf8); });
      if (std::string_view(status) != "JSON_BYTES_NOT_CANONICAL") {
        throw std::runtime_error("invalid UTF-8 corpus mutation was not rejected");
      }
    }
    if (std::string_view(canonical_status) != "JSON_BYTES_NOT_CANONICAL" ||
        std::string_view(primary_status) != "PRIMARY_ELIGIBILITY_FORBIDDEN") {
      throw std::runtime_error("negative corpus mutation was not rejected");
    }
    std::cout << kCorpusPrefix << '\n';
  } else {
    std::cout << kExpectedIds[0] << '\n';
  }
}
