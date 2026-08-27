#pragma once

#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

#include <delta/fixedpoint/scale.hpp>

namespace delta::fixedpoint {

struct EncodedSegment {
  std::vector<std::int16_t> values;
  std::vector<std::byte> payload;

  bool operator==(const EncodedSegment&) const = default;
};

[[nodiscard]] std::vector<std::byte> encode_q_payload(std::span<const std::int16_t> values);
[[nodiscard]] EncodedSegment encode_segment(
    std::span<const Rational> source,
    const Scale& quantum);

}  // namespace delta::fixedpoint
