#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <span>
#include <string>
#include <string_view>
#include <vector>

namespace delta::runtime::sidecar {

using Bytes = std::vector<std::byte>;
using Id128 = std::array<std::byte, 16>;
using Digest = std::array<std::byte, 32>;

inline constexpr std::uint16_t ipc_major = 1U;
inline constexpr std::uint16_t ipc_minor = 1U;
inline constexpr std::uint16_t header_bytes = 128U;
inline constexpr std::uint64_t max_logical_payload_bytes = 16'785'408U;
inline constexpr std::uint64_t max_control_envelope_bytes = 16'785'536U;
inline constexpr std::uint64_t max_command_bytes = 16'777'216U;
inline constexpr std::uint64_t max_effect_bytes = 16'777'216U;
inline constexpr std::uint64_t max_vote_policy_bytes = 4'194'304U;
inline constexpr std::uint64_t max_vote_bytes = 16'769'024U;
inline constexpr std::uint64_t max_vote_receipt_bytes = 16'777'216U;
inline constexpr std::uint64_t max_response_capacity = max_logical_payload_bytes;
inline constexpr std::uint32_t max_submission_capacity = 64U;

inline constexpr std::uint32_t flag_payload_inline = 0x01U;
inline constexpr std::uint32_t flag_payload_shared_memory = 0x02U;
inline constexpr std::uint32_t flag_response_expected = 0x04U;
inline constexpr std::uint32_t flag_read_only = 0x08U;

inline constexpr std::string_view contract_name = "delta-local-sidecar-ipc";
inline constexpr std::string_view canonical_encoding_id =
    "sha256:393cd207a2cd3fd4da366be56095a3467e3184c2c5db1d300d1c07d49cdd7aff";
inline constexpr std::string_view frame_layout_sha256 =
    "sha256:b8d8a521133d4d5b41ab5035f2cfaa82594a4789c8b83ad0c81b77a67afbcb4b";
inline constexpr std::string_view payload_schema_sha256 =
    "sha256:fdeb9e2607dfe2661fff8e99a9510ae1eb6658e516f1496ade6fd1dd6e7af7ce";
inline constexpr std::string_view message_type_table_sha256 =
    "sha256:1581d40a12765ea54c1abf7f3c5434025f40d6718e639c9f9fbfcc1eb6e07950";
inline constexpr std::string_view flag_table_sha256 =
    "sha256:857da723287529fe38f3f6479decb962f435e21b541b38abe71b28489933b248";
inline constexpr std::string_view bounds_sha256 =
    "sha256:12259ada8ff8a14febf167b2631768911fefd9fd26c7298b7ff0f3d103837708";
inline constexpr std::string_view shared_memory_layout_sha256 =
    "sha256:17ce8022d0075e715e8c699ba17c27d9901bf08727579ab977e74f169b205b78";

enum class MessageType : std::uint16_t {
  client_hello = 1U,
  server_descriptor = 2U,
  open_request = 16U,
  open_response = 17U,
  submit_request = 32U,
  submit_response = 33U,
  vote_request = 34U,
  vote_response = 35U,
  state_request = 48U,
  state_response = 49U,
  snapshot_request = 64U,
  snapshot_response = 65U,
  close_request = 80U,
  close_response = 81U,
  health_request = 96U,
  health_response = 97U,
  shared_memory_ack = 112U,
  error_response = 255U,
};

enum class WireType : std::uint8_t {
  u8 = 1U,
  u16_be = 2U,
  u32_be = 3U,
  u64_be = 4U,
  id128 = 5U,
  sha256 = 6U,
  bytes = 7U,
  canonical_utf8 = 8U,
  shm_reference_64 = 9U,
};

struct Field {
  std::uint16_t id;
  WireType wire_type;
  Bytes value;

  bool operator==(const Field&) const = default;
};

struct Payload {
  MessageType type;
  std::vector<Field> fields;

  bool operator==(const Payload&) const = default;
};

struct Frame {
  MessageType type;
  std::uint32_t flags;
  Id128 session_id;
  std::uint64_t generation;
  Id128 correlation_id;
  std::uint64_t sequence;
  std::uint64_t response_capacity;
  Bytes payload;

  bool operator==(const Frame&) const = default;
};

struct FrameHeader {
  MessageType type;
  std::uint32_t flags;
  Id128 session_id;
  std::uint64_t generation;
  Id128 correlation_id;
  std::uint64_t sequence;
  std::uint64_t payload_length;
  std::uint64_t response_capacity;
  Digest payload_sha256;

  bool operator==(const FrameHeader&) const = default;
};

[[nodiscard]] Bytes encode_frame(const Frame& frame);
[[nodiscard]] Frame decode_frame(std::span<const std::byte> encoded);
[[nodiscard]] FrameHeader decode_frame_header(std::span<const std::byte> encoded_header);
[[nodiscard]] Bytes encode_payload(MessageType type, std::span<const Field> fields);
[[nodiscard]] Payload decode_payload(std::span<const std::byte> encoded);
[[nodiscard]] Bytes encode_fields(std::span<const Field> fields);
[[nodiscard]] Digest request_digest(MessageType type, std::span<const Field> fields);
[[nodiscard]] Digest sha256(std::span<const std::byte> bytes);
[[nodiscard]] Digest sha256_file(const std::filesystem::path& path);
[[nodiscard]] Digest digest_from_identity(std::string_view identity);
[[nodiscard]] std::string digest_identity(const Digest& digest);

[[nodiscard]] Field field_u8(std::uint16_t id, std::uint8_t value);
[[nodiscard]] Field field_u16(std::uint16_t id, std::uint16_t value);
[[nodiscard]] Field field_u32(std::uint16_t id, std::uint32_t value);
[[nodiscard]] Field field_u64(std::uint16_t id, std::uint64_t value);
[[nodiscard]] Field field_id128(std::uint16_t id, const Id128& value);
[[nodiscard]] Field field_digest(std::uint16_t id, const Digest& value);
[[nodiscard]] Field field_bytes(std::uint16_t id, std::span<const std::byte> value);
[[nodiscard]] Field field_text(std::uint16_t id, std::string_view value);
[[nodiscard]] Field field_shared_memory_reference(
    std::uint16_t id,
    std::span<const std::byte> value);

[[nodiscard]] const Field& require_field(
    const Payload& payload,
    std::size_t index,
    std::uint16_t id,
    WireType wire_type,
    std::size_t minimum_size,
    std::size_t maximum_size);
[[nodiscard]] std::uint8_t field_as_u8(const Field& field);
[[nodiscard]] std::uint16_t field_as_u16(const Field& field);
[[nodiscard]] std::uint32_t field_as_u32(const Field& field);
[[nodiscard]] std::uint64_t field_as_u64(const Field& field);
[[nodiscard]] Id128 field_as_id128(const Field& field);
[[nodiscard]] Digest field_as_digest(const Field& field);
[[nodiscard]] std::string field_as_text(const Field& field);

[[nodiscard]] bool is_request(MessageType type) noexcept;
[[nodiscard]] bool is_response(MessageType type) noexcept;
[[nodiscard]] bool is_notification(MessageType type) noexcept;
[[nodiscard]] bool shared_memory_eligible(MessageType type) noexcept;
[[nodiscard]] std::uint32_t inline_flags(MessageType type);
[[nodiscard]] std::uint32_t shared_memory_flags(MessageType type);
[[nodiscard]] std::uint32_t required_flags(MessageType type);

}  // namespace delta::runtime::sidecar
