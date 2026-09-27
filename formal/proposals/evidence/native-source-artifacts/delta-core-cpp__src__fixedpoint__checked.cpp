#include <delta/fixedpoint/checked.hpp>

#include <delta/core/canonical.hpp>

#include <cctype>
#include <cstdint>
#include <string>

namespace delta::fixedpoint {

bool is_content_id(std::string_view value) noexcept {
  constexpr std::string_view prefix = "sha256:";
  if (!value.starts_with(prefix) || value.size() != prefix.size() + 64U) {
    return false;
  }
  for (const char character : value.substr(prefix.size())) {
    if (!((character >= '0' && character <= '9') || (character >= 'a' && character <= 'f'))) {
      return false;
    }
  }
  return true;
}

bool is_ascii_token(std::string_view value) noexcept {
  if (value.empty() || value.size() > 255U) {
    return false;
  }
  for (const unsigned char character : value) {
    const bool accepted =
        character <= 0x7fU &&
        (std::isalnum(character) != 0 || character == '.' || character == '_' ||
         character == '/' || character == '-');
    if (!accepted) {
      return false;
    }
  }
  return true;
}

std::string domain_content_id(std::string_view domain, std::span<const std::byte> bytes) {
  if (!domain.starts_with("deltareduce.004.") || domain.empty()) {
    throw std::invalid_argument("feature-004 hash domain is invalid");
  }
  delta::core::canonical::Bytes input;
  input.reserve(domain.size() + 1U + bytes.size());
  for (const unsigned char character : domain) {
    input.push_back(static_cast<std::byte>(character));
  }
  input.push_back(std::byte{0});
  input.insert(input.end(), bytes.begin(), bytes.end());
  return "sha256:" + delta::core::canonical::sha256_hex(input);
}

}  // namespace delta::fixedpoint
