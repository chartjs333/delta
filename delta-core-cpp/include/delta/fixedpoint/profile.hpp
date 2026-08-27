#pragma once

#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <string_view>

namespace delta::fixedpoint {

inline constexpr std::int16_t q_min = -32767;
inline constexpr std::int16_t q_max = 32767;
inline constexpr std::size_t max_header_bytes = 65'536U;
inline constexpr std::size_t max_payload_bytes = 1'048'576U;
inline constexpr std::size_t max_segments = 65'536U;
inline constexpr std::size_t max_shards = 4'096U;
inline constexpr std::uint64_t max_total_elements = 1'073'741'824U;

[[nodiscard]] constexpr std::string_view formal_semantics_id() noexcept {
  return "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
}

[[nodiscard]] constexpr std::string_view fixed_profile_id() noexcept {
  return "sha256:17c8d23790047966e42f3204502623c74a0ff0383319d23e67ab15cf92fe3e61";
}

enum class ErrorCode {
  profile_mismatch,
  rational_fields_invalid,
  rational_zero_denominator,
  rational_not_reduced,
  rational_zero_not_canonical,
  scale_not_positive,
  scale_out_of_range,
  quantization_intermediate_overflow,
  quantization_range_exceeded,
  q_value_out_of_range,
  proof_instance_invalid,
  accumulator_bound_unsafe,
};

class ContractError final : public std::runtime_error {
 public:
  ContractError(ErrorCode code, std::string message);

  [[nodiscard]] ErrorCode code() const noexcept;

 private:
  ErrorCode code_;
};

struct Limits {
  std::size_t header_bytes;
  std::size_t payload_bytes;
  std::size_t segments;
  std::size_t shards;
  std::uint64_t total_elements;

  bool operator==(const Limits&) const = default;
};

struct Profile {
  std::string name;
  std::int32_t minimum_q;
  std::int32_t maximum_q;
  Limits limits;
  bool little_endian;
  bool ties_to_even;
  bool reject_out_of_range;
  bool per_segment_scale;
  bool residual_forbidden;

  bool operator==(const Profile&) const = default;
};

[[nodiscard]] Profile int16_fixed_v1();
void validate_profile(const Profile& profile);
[[nodiscard]] std::string canonical_profile_json(const Profile& profile);
[[nodiscard]] std::string derive_profile_id(const Profile& profile);

}  // namespace delta::fixedpoint
