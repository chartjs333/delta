#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <span>

namespace delta::core::detail {

[[nodiscard]] std::array<std::byte, 32> sha256(std::span<const std::byte> input);

}  // namespace delta::core::detail
