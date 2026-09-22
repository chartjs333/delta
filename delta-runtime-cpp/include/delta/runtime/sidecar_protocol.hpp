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
inline constexpr std::uint16_t ipc_minor = 0U;
inline constexpr std::uint16_t header_bytes = 128U;
inline constexpr std::uint64_t max_logical_payload_bytes = 16'785'408U;
inline constexpr std::uint64_t max_control_envelope_bytes = 16'785'536U;
inline constexpr std::uint64_t max_command_bytes = 16'777'216U;
inline constexpr std::uint64_t max_effect_bytes = 16'777'216U;
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
    "sha256:46fcc91280fc2c878cb176bf6e9d855f8e39ac9fffcf18709b1a6b80a30ce18e";
inline constexpr std::string_view payload_schema_sha256 =
    "sha256:31edfa48d707fb06cd24624d1790946981294bb093d74d44c202a5d15c5376c5";
inline constexpr std::string_view message_type_table_sha256 =
    "sha256:dfa3fe65b946e6527b317168ef0ea000a4610bba1e9c1ed9ebd099adff71e64e";
inline constexpr std::string_view flag_table_sha256 =
    "sha256:6aa94eb75b5b6af99132f71b2753d56988454be86a371b46f46241cf7a8e33d5";
inline constexpr std::string_view bounds_sha256 =
    "sha256:32d9e791ac35dc6bb061aaedb0a67ee28ad1a2662bbb0ffd1bfc9177b055d0f8";
inline constexpr std::string_view shared_memory_layout_sha256 =
    "sha256:0a48282fddae72060e9b93c02f97f174b56f8a20b07aabb88ee51f7ef03f5aa4";

enum class MessageType : std::uint16_t {
  client_hello = 1U,
  server_descriptor = 2U,
  open_request = 16U,
  open_response = 17U,
  submit_request = 32U,
  submit_response = 33U,
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

[[nodiscard]] Bytes encode_frame(const Frame& frame);
[[nodiscard]] Frame decode_frame(std::span<const std::byte> encoded);
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
[[nodiscard]] std::uint32_t required_flags(MessageType type);

}  // namespace delta::runtime::sidecar
