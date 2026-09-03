#include <delta/runtime/benchmark.hpp>

#include <cerrno>
#include <cstddef>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <map>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

#ifdef _WIN32
#include <io.h>
#else
#include <unistd.h>
#endif

namespace {

struct Record {
  std::size_t sequence{};
  std::string payload_hex;
};

[[nodiscard]] bool valid_request_id(std::string_view value) {
  if (value.empty() || value.size() > 128U) return false;
  for (const char character : value) {
    const bool valid = (character >= 'a' && character <= 'z') ||
                       (character >= 'A' && character <= 'Z') ||
                       (character >= '0' && character <= '9') || character == '.' ||
                       character == '_' || character == '-';
    if (!valid) return false;
  }
  return true;
}

[[nodiscard]] bool valid_hex(std::string_view value, std::size_t maximum_bytes) {
  if (value.size() % 2U != 0U || value.size() / 2U > maximum_bytes) return false;
  for (const char character : value) {
    const bool valid = (character >= '0' && character <= '9') ||
                       (character >= 'a' && character <= 'f');
    if (!valid) return false;
  }
  return true;
}

[[nodiscard]] std::map<std::string, Record, std::less<>> recover(
    const std::filesystem::path& path,
    std::size_t maximum_bytes) {
  std::map<std::string, Record, std::less<>> result;
  std::ifstream input(path);
  if (!input && std::filesystem::exists(path)) {
    throw std::runtime_error("journal open failed");
  }
  std::string line;
  std::size_t sequence = 0U;
  while (std::getline(input, line)) {
    const auto separator = line.find('|');
    if (separator == std::string::npos) throw std::runtime_error("journal corrupt");
    auto request_id = line.substr(0U, separator);
    auto payload = line.substr(separator + 1U);
    if (!valid_request_id(request_id) || !valid_hex(payload, maximum_bytes) ||
        result.contains(request_id)) {
      throw std::runtime_error("journal corrupt");
    }
    result.emplace(std::move(request_id), Record{++sequence, std::move(payload)});
  }
  return result;
}

void append_journal(
    const std::filesystem::path& path,
    std::string_view request_id,
    std::string_view payload) {
  const auto record = std::string(request_id) + '|' + std::string(payload) + '\n';
#ifdef _WIN32
  std::FILE* output = nullptr;
  if (_wfopen_s(&output, path.c_str(), L"ab") != 0 || output == nullptr) {
    throw std::runtime_error("journal append failed");
  }
#else
  auto* output = std::fopen(path.c_str(), "ab");
  if (output == nullptr) throw std::runtime_error("journal append failed");
#endif
  const auto written = std::fwrite(record.data(), 1U, record.size(), output);
  const auto flushed = std::fflush(output);
#ifdef _WIN32
  const auto durable = _commit(_fileno(output));
#else
  const auto durable = fsync(fileno(output));
#endif
  const auto closed = std::fclose(output);
  if (written != record.size() || flushed != 0 || durable != 0 || closed != 0) {
    throw std::runtime_error("journal durability barrier failed");
  }
}

[[nodiscard]] std::string hex_encode(std::string_view value) {
  constexpr std::string_view digits = "0123456789abcdef";
  std::string output;
  output.reserve(value.size() * 2U);
  for (const unsigned char character : value) {
    output.push_back(digits[character >> 4U]);
    output.push_back(digits[character & 0x0fU]);
  }
  return output;
}

[[nodiscard]] std::string hex_decode(std::string_view value, std::size_t maximum_bytes) {
  if (!valid_hex(value, maximum_bytes) || value.empty()) {
    throw std::runtime_error("invalid causal schedule");
  }
  const auto nibble = [](char character) -> unsigned char {
    if (character >= '0' && character <= '9') {
      return static_cast<unsigned char>(character - '0');
    }
    return static_cast<unsigned char>(10 + character - 'a');
  };
  std::string output;
  output.reserve(value.size() / 2U);
  for (std::size_t index = 0U; index < value.size(); index += 2U) {
    output.push_back(static_cast<char>((nibble(value[index]) << 4U) | nibble(value[index + 1U])));
  }
  return output;
}

[[nodiscard]] std::string fault_outcome(
    std::string_view actor,
    std::string_view action,
    bool assumptions_hold) {
  if (!assumptions_hold) return "SAFE_BLOCKED";
  if (actor == "WORKER" && action == "CRASH") return "APPLIED";
  if (actor == "VALIDATOR" && action == "CRASH") return "VIEW_CHANGE";
  if (actor == "VALIDATOR" && action == "RESTART") return "RECOVERED";
  if (actor == "STORAGE" && action == "CRASH") return "RETRIEVAL";
  if (actor == "STORAGE" && action == "RESTART") return "RECOVERED";
  if (actor == "REGION" && action == "DELAY") return "APPLIED";
  if (actor == "REGION" && action == "PARTITION") return "ABORTED";
  throw std::runtime_error("unsupported fault transition");
}

[[nodiscard]] delta::runtime::benchmark::FaultAction fault_action(std::string_view action) {
  using delta::runtime::benchmark::FaultAction;
  if (action == "CRASH") return FaultAction::crash;
  if (action == "RESTART") return FaultAction::restart;
  if (action == "DELAY") return FaultAction::delay;
  if (action == "PARTITION") return FaultAction::partition;
  throw std::runtime_error("unsupported fault action");
}

[[nodiscard]] std::size_t parse_step(std::string_view value) {
  std::size_t parsed = 0U;
  if (value.empty()) throw std::runtime_error("invalid logical step");
  for (const char character : value) {
    if (character < '0' || character > '9') throw std::runtime_error("invalid logical step");
    const auto digit = static_cast<std::size_t>(character - '0');
    if (parsed > (std::numeric_limits<std::size_t>::max() - digit) / 10U) {
      throw std::runtime_error("invalid logical step");
    }
    parsed = parsed * 10U + digit;
  }
  return parsed;
}

void execute_fault(
    std::string_view line,
    const std::filesystem::path& journal,
    std::size_t maximum_bytes,
    std::map<std::string, Record, std::less<>>& records) {
  std::vector<std::string> fields;
  std::size_t start = 6U;
  while (start <= line.size()) {
    const auto end = line.find(' ', start);
    fields.emplace_back(line.substr(start, end == std::string::npos ? end : end - start));
    if (end == std::string::npos) break;
    start = end + 1U;
  }
  if (fields.size() != 7U || !valid_request_id(fields[0]) || !valid_request_id(fields[1]) ||
      !valid_request_id(fields[2]) || !valid_request_id(fields[3]) ||
      (fields[5] != "0" && fields[5] != "1") || !valid_hex(fields[6], maximum_bytes)) {
    throw std::runtime_error("invalid fault command");
  }
  const auto step = parse_step(fields[4]);
  const auto assumptions_hold = fields[5] == "1";
  const auto expected_outcome = fault_outcome(fields[2], fields[3], assumptions_hold);
  const auto causal_schedule = hex_decode(fields[6], maximum_bytes);
  const auto event = delta::runtime::benchmark::FaultEvent{
      fields[1],
      fields[2],
      fault_action(fields[3]),
      step,
      assumptions_hold,
      expected_outcome,
      causal_schedule};
  const auto controller = delta::runtime::benchmark::FaultController({event});
  if (controller.events_at(step) != std::vector{event}) {
    throw std::runtime_error("native fault controller rejected transition");
  }
  const auto canonical = fields[1] + '|' + fields[2] + '|' + fields[3] + '|' +
                         std::to_string(step) + '|' + fields[5] + '|' + fields[6];
  const auto payload = hex_encode(canonical);
  if (!valid_hex(payload, maximum_bytes)) throw std::runtime_error("fault payload too large");
  bool replay = false;
  std::size_t sequence = 0U;
  if (const auto found = records.find(fields[0]); found != records.end()) {
    if (found->second.payload_hex != payload) throw std::runtime_error("conflicting fault replay");
    replay = true;
    sequence = found->second.sequence;
  } else {
    append_journal(journal, fields[0], payload);
    sequence = records.size() + 1U;
    records.emplace(fields[0], Record{sequence, payload});
  }
  const auto execution = delta::runtime::benchmark::execute_fault_scenario(
      event, journal.parent_path() / ("runtime-" + fields[0]), fields[0]);
  if (execution.observed_outcome != expected_outcome) {
    throw std::runtime_error("actual runtime fault outcome differs from oracle");
  }
  std::cout << "FAULT_OK " << sequence << ' ' << (replay ? 1 : 0) << ' '
            << execution.observed_outcome << " ACTUAL_RUNTIME_TRANSITION "
            << execution.native_trace_id << ' '
            << execution.native_state_root << ' ' << execution.native_effect_root << ' '
            << execution.native_wal_sha256 << ' ' << execution.runtime_operation_count << ' '
            << (execution.wal_replayed ? 1 : 0) << ' '
            << (execution.view_change_observed ? 1 : 0) << ' '
            << (execution.current_checkpoint_advanced ? 1 : 0) << ' '
            << (execution.availability_success ? 1 : 0) << ' '
            << hex_encode(execution.canonical_trace) << ' '
            << hex_encode(execution.canonical_causal_evidence) << '\n'
            << std::flush;
}

[[nodiscard]] std::size_t parse_size(const char* value) {
  const auto parsed = std::stoull(value);
  if (parsed == 0U || parsed > 16U * 1024U * 1024U) {
    throw std::runtime_error("invalid maximum payload");
  }
  return static_cast<std::size_t>(parsed);
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 3) throw std::runtime_error("usage: sidecar JOURNAL MAX_PAYLOAD_BYTES");
    const auto journal = std::filesystem::path(argv[1]);
    const auto maximum_bytes = parse_size(argv[2]);
    std::filesystem::create_directories(journal.parent_path());
    auto records = recover(journal, maximum_bytes);
    std::string line;
    while (std::getline(std::cin, line)) {
      if (line == "CRASH") {
        std::cerr << "SIMULATED_CRASH\n";
        return 86;
      }
      if (line.starts_with("FAULT ")) {
        try {
          execute_fault(line, journal, maximum_bytes, records);
        } catch (const std::exception&) {
          std::cout << "ERR FAULT\n" << std::flush;
        }
        continue;
      }
      if (!line.starts_with("ECHO ")) {
        std::cout << "ERR COMMAND\n" << std::flush;
        continue;
      }
      const auto separator = line.find(' ', 5U);
      if (separator == std::string::npos) {
        std::cout << "ERR FORMAT\n" << std::flush;
        continue;
      }
      const auto request_id = line.substr(5U, separator - 5U);
      const auto payload = line.substr(separator + 1U);
      if (!valid_request_id(request_id) || !valid_hex(payload, maximum_bytes)) {
        std::cout << "ERR INVALID\n" << std::flush;
        continue;
      }
      if (const auto found = records.find(request_id); found != records.end()) {
        if (found->second.payload_hex != payload) {
          std::cout << "ERR CONFLICT\n" << std::flush;
          continue;
        }
        std::cout << "OK " << found->second.sequence << " 1 " << payload << '\n' << std::flush;
        continue;
      }
      append_journal(journal, request_id, payload);
      const auto sequence = records.size() + 1U;
      records.emplace(request_id, Record{sequence, payload});
      std::cout << "OK " << sequence << " 0 " << payload << '\n' << std::flush;
    }
  } catch (const std::exception& error) {
    std::cerr << error.what() << '\n';
    return 2;
  }
  return 0;
}
