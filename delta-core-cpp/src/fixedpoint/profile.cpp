#include <delta/fixedpoint/profile.hpp>

#include <delta/fixedpoint/checked.hpp>

#include <cstddef>
#include <span>
#include <string>
#include <utility>

namespace delta::fixedpoint {
namespace {

[[noreturn]] void reject(ErrorCode code, const char* message) {
  throw ContractError(code, message);
}

}  // namespace

ContractError::ContractError(ErrorCode code, std::string message)
    : std::runtime_error(std::move(message)), code_(code) {}

ErrorCode ContractError::code() const noexcept { return code_; }

Profile int16_fixed_v1() {
  return Profile{
      "int16-fixed-v1",
      q_min,
      q_max,
      Limits{max_header_bytes, max_payload_bytes, max_segments, max_shards, max_total_elements},
      true,
      true,
      true,
      true,
      true,
  };
}

void validate_profile(const Profile& profile) {
  if (!(profile == int16_fixed_v1())) {
    reject(ErrorCode::profile_mismatch, "profile is not the immutable int16-fixed-v1 contract");
  }
}

std::string canonical_profile_json(const Profile& profile) {
  validate_profile(profile);
  return std::string{
             R"({"accumulator_widths":[64,128],"byte_order":"LITTLE_ENDIAN","element_encoding":"SIGNED_TWOS_COMPLEMENT_INT16","formal_semantics_id":")"} +
         std::string(formal_semantics_id()) +
         R"(","limits":{"max_header_bytes":65536,"max_payload_bytes":1048576,"max_segments":65536,"max_shards":4096,"max_total_elements":1073741824},"out_of_range_action":"REJECT","profile_name":"int16-fixed-v1","q_max":32767,"q_min":-32767,"residual_mode":"FORBIDDEN","rounding":"ROUND_TO_NEAREST_TIES_TO_EVEN","scale_granularity":"CANONICAL_PARAMETER_SEGMENT","scale_representation":"REDUCED_POSITIVE_RATIONAL_U32","schema_version":"1.0.0","source_representation":"REDUCED_RATIONAL_I64_U32","trailing_bytes_action":"REJECT","type_name":"FIXED_POINT_PROFILE"})";
}

std::string derive_profile_id(const Profile& profile) {
  const auto encoded = canonical_profile_json(profile);
  const auto bytes = std::as_bytes(std::span(encoded.data(), encoded.size()));
  return domain_content_id("deltareduce.004.profile.v1", bytes);
}

}  // namespace delta::fixedpoint
