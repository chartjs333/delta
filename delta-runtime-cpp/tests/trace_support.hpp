#pragma once

#include <delta/core/protocol.hpp>

#include <cstdint>
#include <filesystem>
#include <fstream>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace delta::test::trace {

inline constexpr std::string_view formal_id = core::protocol::formal_semantics_id;
inline constexpr std::string_view round_id = "round-003-fixture";
inline constexpr std::string_view epoch_id =
    "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";
inline constexpr std::string_view round_contract =
    R"JSON({"contract_id":"sha256:c7a61fab1f690d454ca07f7158e3de896a5af24e315dbe0e9eab6b43ee6d3c59","parameter_schema":{"parameter_ids":["decoder.bias"],"schema_hash":"sha256:258d2956112fb49a078b4e2c001d215d1c733509eef180088ad19bb8963083e4"},"round_config":{"body_hash":"sha256:ba04c93913be2f015e22e3f731235fd5044fdc61a4929ad64bbf9ef966d8ae97","domain_ids":["domain-text-en"],"parameter_schema_hash":"sha256:258d2956112fb49a078b4e2c001d215d1c733509eef180088ad19bb8963083e4","shard_plan_hash":"sha256:6c5f44cfbdc8a4ca5f6c52e3bf61e63fff6c1538608b60868b3e38f6ff9b8078"},"round_id":"round-003-fixture","shard_plan":{"assignments":[{"domain_id":"domain-text-en","parameter_id":"decoder.bias","shard_id":"shard-000","vote_context_id":"NORMAL-PARAM-DOMAIN-TEXT-EN-SHARD-000:round-003-fixture"}],"plan_hash":"sha256:6c5f44cfbdc8a4ca5f6c52e3bf61e63fff6c1538608b60868b3e38f6ff9b8078"}})JSON";

struct Event {
  std::string action_id;
  std::optional<std::string> actor_id;
  std::optional<std::string> actor_role;
  std::vector<std::string> artifact_refs;
  std::optional<std::string> body_hash;
  std::optional<std::uint64_t> durable_sequence;
  std::optional<std::string> error_code;
  std::uint64_t height = 1U;
  std::uint64_t logical_time = 0U;
  std::string next_state_root;
  std::string outcome;
  std::vector<std::string> parent_hashes;
  std::string prior_state_root;
  std::optional<std::string> request_id;
  std::optional<std::string> result_hash;
  std::uint64_t view = 0U;
  std::optional<std::string> vote_context_id;
};

[[nodiscard]] inline std::string quote(std::string_view value) {
  std::string output{"\""};
  for (const unsigned char byte : value) {
    switch (byte) {
      case '\"':
        output += "\\\"";
        break;
      case '\\':
        output += "\\\\";
        break;
      case '\b':
        output += "\\b";
        break;
      case '\f':
        output += "\\f";
        break;
      case '\n':
        output += "\\n";
        break;
      case '\r':
        output += "\\r";
        break;
      case '\t':
        output += "\\t";
        break;
      default:
        if (byte < 0x20U) {
          constexpr char hex[] = "0123456789abcdef";
          output += "\\u00";
          output.push_back(hex[(byte >> 4U) & 0x0fU]);
          output.push_back(hex[byte & 0x0fU]);
        } else {
          output.push_back(static_cast<char>(byte));
        }
    }
  }
  output.push_back('\"');
  return output;
}

[[nodiscard]] inline std::string nullable(const std::optional<std::string>& value) {
  return value.has_value() ? quote(*value) : "null";
}

[[nodiscard]] inline std::string nullable(const std::optional<std::uint64_t>& value) {
  return value.has_value() ? std::to_string(*value) : "null";
}

[[nodiscard]] inline std::string array(const std::vector<std::string>& values) {
  std::ostringstream output;
  output << '[';
  for (std::size_t index = 0; index < values.size(); ++index) {
    if (index != 0U) {
      output << ',';
    }
    output << quote(values[index]);
  }
  output << ']';
  return output.str();
}

[[nodiscard]] inline std::string encode(const Event& event) {
  std::ostringstream output;
  output << "{\"action_id\":" << quote(event.action_id)
         << ",\"actor_id\":" << nullable(event.actor_id)
         << ",\"actor_role\":" << nullable(event.actor_role)
         << ",\"artifact_refs\":" << array(event.artifact_refs)
         << ",\"body_hash\":" << nullable(event.body_hash)
         << ",\"durable_sequence\":" << nullable(event.durable_sequence)
         << ",\"error_code\":" << nullable(event.error_code)
         << ",\"height\":" << event.height << ",\"logical_time\":" << event.logical_time
         << ",\"next_state_root\":" << quote(event.next_state_root)
         << ",\"outcome\":" << quote(event.outcome)
         << ",\"parent_hashes\":" << array(event.parent_hashes)
         << ",\"prior_state_root\":" << quote(event.prior_state_root)
         << ",\"request_id\":" << nullable(event.request_id)
         << ",\"result_hash\":" << nullable(event.result_hash)
         << ",\"round_id\":" << quote(round_id)
         << ",\"schema_version\":\"1.0.0\""
         << ",\"validator_epoch\":" << quote(epoch_id) << ",\"view\":" << event.view
         << ",\"vote_context_id\":" << nullable(event.vote_context_id) << '}';
  return output.str();
}

inline void write(
    const std::filesystem::path& path,
    std::string_view trace_id,
    std::string_view initial_state_root,
    std::string_view terminal_state_root,
    std::string_view terminal_outcome,
    const std::vector<Event>& events) {
  std::error_code error;
  std::filesystem::create_directories(path.parent_path(), error);
  if (error) {
    throw std::runtime_error("cannot create native trace output directory");
  }
  std::ofstream output(path, std::ios::binary | std::ios::trunc);
  if (!output.good()) {
    throw std::runtime_error("cannot create native trace output");
  }
  output << "{\"abstraction_version\":\"1.0.0\",\"events\":[";
  for (std::size_t index = 0; index < events.size(); ++index) {
    if (index != 0U) {
      output << ',';
    }
    output << encode(events[index]);
  }
  output << "],\"formal_semantics_id\":" << quote(formal_id)
         << ",\"initial_state_root\":" << quote(initial_state_root)
         << ",\"round_contract\":" << round_contract
         << ",\"schema_version\":\"1.0.0\",\"terminal_outcome\":"
         << quote(terminal_outcome) << ",\"terminal_state_root\":" << quote(terminal_state_root)
         << ",\"trace_id\":" << quote(trace_id) << "}\n";
  if (!output.good()) {
    throw std::runtime_error("cannot flush native trace output");
  }
}

}  // namespace delta::test::trace
