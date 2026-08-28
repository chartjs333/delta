#pragma once

#include <cstddef>
#include <span>
#include <string>
#include <string_view>

namespace delta::fixedpoint {

[[nodiscard]] bool is_content_id(std::string_view value) noexcept;
[[nodiscard]] bool is_ascii_token(std::string_view value) noexcept;
[[nodiscard]] std::string domain_content_id(
    std::string_view domain,
    std::span<const std::byte> bytes);

}  // namespace delta::fixedpoint
