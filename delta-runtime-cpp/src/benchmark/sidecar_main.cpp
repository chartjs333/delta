#include <cstddef>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

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
  std::ofstream output(path, std::ios::app);
  if (!output) throw std::runtime_error("journal append failed");
  output << request_id << '|' << payload << '\n';
  output.flush();
  if (!output) throw std::runtime_error("journal flush failed");
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
