#include <delta/fixedpoint/encoder.hpp>

#include <delta/fixedpoint/profile.hpp>
#include <delta/fixedpoint/rounding.hpp>

#include <cstddef>
#include <cstdint>
#include <span>
#include <vector>

namespace delta::fixedpoint {

std::vector<std::byte> encode_q_payload(std::span<const std::int16_t> values) {
  if (values.size() > max_payload_bytes / 2U) {
    throw ContractError(ErrorCode::q_value_out_of_range, "encoded shard exceeds payload limit");
  }
  std::vector<std::byte> result;
  result.reserve(values.size() * 2U);
  for (const auto value : values) {
    if (value < q_min || value > q_max) {
      throw ContractError(ErrorCode::q_value_out_of_range, "q value is outside symmetric range");
    }
    const auto raw = static_cast<std::uint16_t>(value);
    result.push_back(static_cast<std::byte>(raw & 0xffU));
    result.push_back(static_cast<std::byte>((raw >> 8U) & 0xffU));
  }
  return result;
}

EncodedSegment encode_segment(std::span<const Rational> source, const Scale& quantum) {
  validate_scale(quantum);
  EncodedSegment result;
  result.values.reserve(source.size());
  for (const auto& value : source) {
    result.values.push_back(quantize(value, quantum));
  }
  result.payload = encode_q_payload(result.values);
  return result;
}

}  // namespace delta::fixedpoint
