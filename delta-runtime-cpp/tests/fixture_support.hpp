#pragma once

#include <delta/core/canonical.hpp>
#include <delta/core/protocol.hpp>

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <regex>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>

namespace delta::test {

[[noreturn]] inline void fail(std::string message) { throw std::runtime_error(std::move(message)); }

inline void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

[[nodiscard]] inline std::string load(std::string_view path) {
  std::ifstream input(std::string(path), std::ios::binary);
  expect(input.good(), "cannot open native fixture");
  return {std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
}

[[nodiscard]] inline std::string field(const std::string& document, std::string_view name) {
  const std::regex pattern("\\\"" + std::string(name) + "\\\":\\\"([^\\\"]+)\\\"");
  std::smatch match;
  expect(std::regex_search(document, match, pattern), "required native fixture field is missing");
  return match[1].str();
}

[[nodiscard]] inline std::uint32_t unsigned_field(
    const std::string& document,
    std::string_view name) {
  const std::regex pattern("\\\"" + std::string(name) + "\\\":([0-9]+)");
  std::smatch match;
  expect(std::regex_search(document, match, pattern), "required native unsigned field is missing");
  return static_cast<std::uint32_t>(std::stoul(match[1].str()));
}

[[nodiscard]] inline std::uint8_t hex_nibble(char value) {
  if (value >= '0' && value <= '9') {
    return static_cast<std::uint8_t>(value - '0');
  }
  if (value >= 'a' && value <= 'f') {
    return static_cast<std::uint8_t>(value - 'a' + 10);
  }
  fail("invalid lowercase hexadecimal fixture");
}

[[nodiscard]] inline core::canonical::Bytes decode_hex(std::string_view encoded) {
  expect((encoded.size() % 2U) == 0U, "odd hexadecimal fixture length");
  core::canonical::Bytes result;
  result.reserve(encoded.size() / 2U);
  for (std::size_t index = 0; index < encoded.size(); index += 2U) {
    const auto value = static_cast<std::uint8_t>(
        static_cast<std::uint8_t>(hex_nibble(encoded[index]) << 4U) |
        hex_nibble(encoded[index + 1U]));
    result.push_back(static_cast<std::byte>(value));
  }
  return result;
}

[[nodiscard]] inline core::canonical::Bytes golden(
    std::string_view fixture_path,
    std::uint16_t type_code) {
  const auto document = load(fixture_path);
  const std::regex pattern(
      R"REGEX("envelope_hex":"([0-9a-f]+)","envelope_sha256":"[0-9a-f]+","type_code":([0-9]+))REGEX");
  for (auto cursor = std::sregex_iterator(document.begin(), document.end(), pattern);
       cursor != std::sregex_iterator();
       ++cursor) {
    if (std::stoul((*cursor)[2].str()) == type_code) {
      return decode_hex((*cursor)[1].str());
    }
  }
  fail("registered golden vector not found");
}

[[nodiscard]] inline core::canonical::Bytes ascii_bytes(std::string_view value) {
  core::canonical::Bytes result;
  result.reserve(value.size());
  for (const unsigned char byte : value) {
    result.push_back(static_cast<std::byte>(byte));
  }
  return result;
}

[[nodiscard]] inline std::string derived_id(std::string_view domain, std::string_view value) {
  auto bytes = ascii_bytes(domain);
  const auto suffix = ascii_bytes(value);
  bytes.insert(bytes.end(), suffix.begin(), suffix.end());
  return "sha256:" + core::canonical::sha256_hex(bytes);
}

[[nodiscard]] inline std::filesystem::path fresh_directory(std::string_view name) {
#if defined(_MSVC_LANG)
  constexpr auto language_mode = _MSVC_LANG;
#else
  constexpr auto language_mode = __cplusplus;
#endif
  auto result = std::filesystem::temp_directory_path() / "delta-native-003-tests" /
                std::to_string(language_mode) / std::string(name);
  std::error_code error;
  std::filesystem::remove_all(result, error);
  expect(!error, "cannot clean exact native test directory");
  std::filesystem::create_directories(result, error);
  expect(!error, "cannot create exact native test directory");
  return result;
}

[[nodiscard]] inline core::protocol::Command command_for(
    const core::protocol::RoundState& state,
    std::string kind,
    std::string request_id,
    std::string body_hash) {
  return core::protocol::Command{
      "validator-1",
      std::move(body_hash),
      std::move(kind),
      state.height,
      10U,
      std::move(request_id),
      state.round_id,
      state.view,
  };
}

}  // namespace delta::test
