#include <delta/runtime/sidecar_protocol.hpp>

#include <delta/core/canonical.hpp>

#include <algorithm>
#include <array>
#include <cctype>
#include <cstring>
#include <fstream>
#include <limits>
#include <stdexcept>
#include <type_traits>
#include <utility>

#if defined(_WIN32)
#ifndef NOMINMAX
#define NOMINMAX
#endif
#include <windows.h>
#else
#include <unicode/unorm2.h>
#include <unicode/ustring.h>
#endif

namespace delta::runtime::sidecar {
namespace {

constexpr std::array<std::byte, 8> magic{
    std::byte{'D'}, std::byte{'E'}, std::byte{'L'}, std::byte{'T'},
    std::byte{'A'}, std::byte{'I'}, std::byte{'P'}, std::byte{'C'}};
[[noreturn]] void reject(const char* message) { throw std::invalid_argument(message); }

void require(bool condition, const char* message) {
  if (!condition) {
    reject(message);
  }
}

template <typename Integer>
void append_be(Bytes& output, Integer value) {
  static_assert(std::is_unsigned_v<Integer>);
  for (std::size_t offset = sizeof(Integer); offset != 0U; --offset) {
    const auto shift = static_cast<unsigned>((offset - 1U) * 8U);
    output.push_back(static_cast<std::byte>((value >> shift) & static_cast<Integer>(0xffU)));
  }
}

template <typename Integer>
Integer read_be(std::span<const std::byte> input, std::size_t offset) {
  static_assert(std::is_unsigned_v<Integer>);
  require(offset <= input.size() && input.size() - offset >= sizeof(Integer), "truncated integer");
  Integer result = 0U;
  for (std::size_t index = 0U; index < sizeof(Integer); ++index) {
    result = static_cast<Integer>((result << 8U) | std::to_integer<unsigned>(input[offset + index]));
  }
  return result;
}

void write_be(Bytes& output, std::size_t offset, std::uint64_t value, std::size_t width) {
  require(offset <= output.size() && output.size() - offset >= width, "integer write out of range");
  for (std::size_t index = 0U; index < width; ++index) {
    const auto shift = static_cast<unsigned>((width - index - 1U) * 8U);
    output[offset + index] = static_cast<std::byte>((value >> shift) & 0xffU);
  }
}

bool known_type(MessageType type) noexcept {
  switch (type) {
    case MessageType::client_hello:
    case MessageType::server_descriptor:
    case MessageType::open_request:
    case MessageType::open_response:
    case MessageType::submit_request:
    case MessageType::submit_response:
    case MessageType::vote_request:
    case MessageType::vote_response:
    case MessageType::state_request:
    case MessageType::state_response:
    case MessageType::snapshot_request:
    case MessageType::snapshot_response:
    case MessageType::close_request:
    case MessageType::close_response:
    case MessageType::health_request:
    case MessageType::health_response:
    case MessageType::shared_memory_ack:
    case MessageType::error_response:
      return true;
  }
  return false;
}

bool canonical_utf8(std::span<const std::byte> value) noexcept {
  if (std::find(value.begin(), value.end(), std::byte{0}) != value.end()) {
    return false;
  }
  if (value.empty()) {
    return true;
  }
  if (value.size() > static_cast<std::size_t>(std::numeric_limits<std::int32_t>::max())) {
    return false;
  }
  const auto* input = reinterpret_cast<const char*>(value.data());
  const auto input_size = static_cast<std::int32_t>(value.size());
#if defined(_WIN32)
  const auto utf16_size = MultiByteToWideChar(
      CP_UTF8,
      MB_ERR_INVALID_CHARS,
      input,
      input_size,
      nullptr,
      0);
  if (utf16_size <= 0) {
    return false;
  }
  std::vector<wchar_t> utf16(static_cast<std::size_t>(utf16_size));
  if (MultiByteToWideChar(
          CP_UTF8,
          MB_ERR_INVALID_CHARS,
          input,
          input_size,
          utf16.data(),
          utf16_size) != utf16_size) {
    return false;
  }
  return IsNormalizedString(NormalizationC, utf16.data(), utf16_size) != FALSE;
#else
  UErrorCode status = U_ZERO_ERROR;
  std::int32_t utf16_size = 0;
  u_strFromUTF8(nullptr, 0, &utf16_size, input, input_size, &status);
  if (status != U_BUFFER_OVERFLOW_ERROR || utf16_size <= 0) {
    return false;
  }
  status = U_ZERO_ERROR;
  std::vector<UChar> utf16(static_cast<std::size_t>(utf16_size));
  u_strFromUTF8(utf16.data(), utf16_size, nullptr, input, input_size, &status);
  if (U_FAILURE(status)) {
    return false;
  }
  status = U_ZERO_ERROR;
  const auto* normalizer = unorm2_getNFCInstance(&status);
  if (U_FAILURE(status) || normalizer == nullptr) {
    return false;
  }
  const auto normalized = unorm2_isNormalized(normalizer, utf16.data(), utf16_size, &status);
  return U_SUCCESS(status) && normalized != 0;
#endif
}

Bytes from_digest(const Digest& digest) { return Bytes(digest.begin(), digest.end()); }

}  // namespace

bool is_request(MessageType type) noexcept {
  switch (type) {
    case MessageType::client_hello:
    case MessageType::open_request:
    case MessageType::submit_request:
    case MessageType::vote_request:
    case MessageType::state_request:
    case MessageType::snapshot_request:
    case MessageType::close_request:
    case MessageType::health_request:
      return true;
    default:
      return false;
  }
}

bool is_response(MessageType type) noexcept {
  switch (type) {
    case MessageType::server_descriptor:
    case MessageType::open_response:
    case MessageType::submit_response:
    case MessageType::vote_response:
    case MessageType::state_response:
    case MessageType::snapshot_response:
    case MessageType::close_response:
    case MessageType::health_response:
    case MessageType::error_response:
      return true;
    default:
      return false;
  }
}

bool is_notification(MessageType type) noexcept {
  return type == MessageType::shared_memory_ack;
}

bool shared_memory_eligible(MessageType type) noexcept {
  switch (type) {
    case MessageType::open_request:
    case MessageType::submit_request:
    case MessageType::submit_response:
    case MessageType::vote_request:
    case MessageType::vote_response:
    case MessageType::state_response:
    case MessageType::snapshot_response:
      return true;
    default:
      return false;
  }
}

std::uint32_t inline_flags(MessageType type) {
  switch (type) {
    case MessageType::client_hello:
    case MessageType::open_request:
    case MessageType::submit_request:
    case MessageType::vote_request:
    case MessageType::snapshot_request:
    case MessageType::close_request:
      return flag_payload_inline | flag_response_expected;
    case MessageType::state_request:
    case MessageType::health_request:
      return flag_payload_inline | flag_response_expected | flag_read_only;
    case MessageType::server_descriptor:
    case MessageType::open_response:
    case MessageType::submit_response:
    case MessageType::vote_response:
    case MessageType::state_response:
    case MessageType::snapshot_response:
    case MessageType::close_response:
    case MessageType::health_response:
    case MessageType::shared_memory_ack:
    case MessageType::error_response:
      return flag_payload_inline;
  }
  reject("unknown message type");
}

std::uint32_t shared_memory_flags(MessageType type) {
  require(shared_memory_eligible(type), "message type is not shared-memory eligible");
  return (inline_flags(type) & ~flag_payload_inline) | flag_payload_shared_memory;
}

std::uint32_t required_flags(MessageType type) { return inline_flags(type); }

Digest sha256(std::span<const std::byte> bytes) {
  return digest_from_identity("sha256:" + delta::core::canonical::sha256_hex(bytes));
}

Digest sha256_file(const std::filesystem::path& path) {
  std::ifstream input(path, std::ios::binary);
  require(input.good(), "cannot open sidecar executable for hashing");
  Bytes bytes;
  std::array<char, 64U * 1024U> buffer{};
  while (input.good()) {
    input.read(buffer.data(), static_cast<std::streamsize>(buffer.size()));
    const auto count = input.gcount();
    for (std::streamsize index = 0; index < count; ++index) {
      bytes.push_back(static_cast<std::byte>(static_cast<unsigned char>(buffer[static_cast<std::size_t>(index)])));
    }
  }
  require(input.eof(), "cannot read sidecar executable for hashing");
  return sha256(bytes);
}

Digest digest_from_identity(std::string_view identity) {
  require(identity.size() == 71U && identity.starts_with("sha256:"), "invalid SHA-256 identity");
  Digest result{};
  const auto hex_value = [](char item) -> unsigned {
    if (item >= '0' && item <= '9') {
      return static_cast<unsigned>(item - '0');
    }
    if (item >= 'a' && item <= 'f') {
      return static_cast<unsigned>(item - 'a' + 10);
    }
    reject("SHA-256 identity is not lowercase hexadecimal");
  };
  for (std::size_t index = 0U; index < result.size(); ++index) {
    result[index] = static_cast<std::byte>(
        (hex_value(identity[7U + (index * 2U)]) << 4U) |
        hex_value(identity[8U + (index * 2U)]));
  }
  return result;
}

std::string digest_identity(const Digest& digest) {
  constexpr char digits[] = "0123456789abcdef";
  std::string result = "sha256:";
  result.reserve(71U);
  for (const auto item : digest) {
    const auto value = std::to_integer<unsigned>(item);
    result.push_back(digits[(value >> 4U) & 0x0fU]);
    result.push_back(digits[value & 0x0fU]);
  }
  return result;
}

Bytes encode_fields(std::span<const Field> fields) {
  Bytes output;
  std::uint16_t prior = 0U;
  for (const auto& field : fields) {
    require(field.id > prior, "field IDs must be strictly increasing");
    require(field.value.size() <= std::numeric_limits<std::uint32_t>::max(), "field is too large");
    append_be(output, field.id);
    output.push_back(static_cast<std::byte>(field.wire_type));
    output.push_back(std::byte{0});
    append_be(output, static_cast<std::uint32_t>(field.value.size()));
    output.insert(output.end(), field.value.begin(), field.value.end());
    prior = field.id;
  }
  return output;
}

Bytes encode_payload(MessageType type, std::span<const Field> fields) {
  require(known_type(type), "unknown payload message type");
  const auto value = encode_fields(fields);
  require(value.size() <= max_logical_payload_bytes - 16U, "payload metadata exceeds bound");
  Bytes output;
  output.reserve(16U + value.size());
  append_be(output, static_cast<std::uint16_t>(type));
  append_be(output, static_cast<std::uint16_t>(1U));
  append_be(output, static_cast<std::uint16_t>(0U));
  append_be(output, static_cast<std::uint16_t>(0U));
  append_be(output, static_cast<std::uint64_t>(value.size()));
  output.insert(output.end(), value.begin(), value.end());
  return output;
}

Payload decode_payload(std::span<const std::byte> encoded) {
  require(encoded.size() >= 16U && encoded.size() <= max_logical_payload_bytes, "invalid payload size");
  const auto type = static_cast<MessageType>(read_be<std::uint16_t>(encoded, 0U));
  require(known_type(type), "unknown payload type");
  require(read_be<std::uint16_t>(encoded, 2U) == 1U, "unsupported payload major");
  require(read_be<std::uint16_t>(encoded, 4U) == 0U, "unsupported payload minor");
  require(read_be<std::uint16_t>(encoded, 6U) == 0U, "nonzero payload reserved field");
  const auto declared = read_be<std::uint64_t>(encoded, 8U);
  require(declared == encoded.size() - 16U, "payload value length mismatch");
  std::vector<Field> fields;
  std::size_t offset = 16U;
  std::uint16_t prior = 0U;
  while (offset < encoded.size()) {
    require(encoded.size() - offset >= 8U, "truncated TLV header");
    const auto id = read_be<std::uint16_t>(encoded, offset);
    const auto wire = static_cast<WireType>(std::to_integer<std::uint8_t>(encoded[offset + 2U]));
    require(std::to_integer<unsigned>(encoded[offset + 3U]) == 0U, "nonzero TLV flags");
    const auto length = read_be<std::uint32_t>(encoded, offset + 4U);
    offset += 8U;
    require(id > prior, "TLV fields are not strictly increasing");
    require(length <= encoded.size() - offset, "truncated TLV value");
    switch (wire) {
      case WireType::u8:
      case WireType::u16_be:
      case WireType::u32_be:
      case WireType::u64_be:
      case WireType::id128:
      case WireType::sha256:
      case WireType::bytes:
      case WireType::canonical_utf8:
      case WireType::shm_reference_64:
        break;
      default:
        reject("unknown TLV wire type");
    }
    Bytes value(encoded.begin() + static_cast<std::ptrdiff_t>(offset),
                encoded.begin() + static_cast<std::ptrdiff_t>(offset + length));
    if (wire == WireType::canonical_utf8) {
      require(canonical_utf8(value), "text is not canonical UTF-8");
    }
    fields.push_back(Field{id, wire, std::move(value)});
    offset += length;
    prior = id;
  }
  return Payload{type, std::move(fields)};
}

Bytes encode_frame(const Frame& frame) {
  require(known_type(frame.type), "unknown frame message type");
  require(frame.flags == inline_flags(frame.type), "frame flags differ from frozen table");
  require(frame.generation != 0U && frame.sequence != 0U, "zero generation or sequence");
  require(!frame.payload.empty() && frame.payload.size() <= max_logical_payload_bytes, "invalid inline payload size");
  const auto expected_capacity = is_request(frame.type) ? max_response_capacity : 0U;
  require(frame.response_capacity == expected_capacity, "invalid response capacity");
  require(frame.payload.size() <= max_control_envelope_bytes - header_bytes, "control frame exceeds bound");
  Bytes output(header_bytes, std::byte{0});
  std::copy(magic.begin(), magic.end(), output.begin());
  write_be(output, 8U, ipc_major, 2U);
  write_be(output, 10U, ipc_minor, 2U);
  write_be(output, 12U, header_bytes, 2U);
  write_be(output, 14U, static_cast<std::uint16_t>(frame.type), 2U);
  write_be(output, 16U, frame.flags, 4U);
  std::copy(frame.session_id.begin(), frame.session_id.end(), output.begin() + 20);
  write_be(output, 36U, frame.generation, 8U);
  std::copy(frame.correlation_id.begin(), frame.correlation_id.end(), output.begin() + 44);
  write_be(output, 60U, frame.sequence, 8U);
  write_be(output, 68U, frame.payload.size(), 8U);
  write_be(output, 76U, frame.response_capacity, 8U);
  const auto digest = sha256(frame.payload);
  std::copy(digest.begin(), digest.end(), output.begin() + 84);
  output.insert(output.end(), frame.payload.begin(), frame.payload.end());
  return output;
}

FrameHeader decode_frame_header(std::span<const std::byte> encoded) {
  require(encoded.size() == header_bytes, "invalid frame header size");
  require(std::equal(magic.begin(), magic.end(), encoded.begin()), "bad frame magic");
  require(read_be<std::uint16_t>(encoded, 8U) == ipc_major, "unsupported IPC major");
  require(read_be<std::uint16_t>(encoded, 10U) == ipc_minor, "unsupported IPC minor");
  require(read_be<std::uint16_t>(encoded, 12U) == header_bytes, "invalid frame header length");
  const auto type = static_cast<MessageType>(read_be<std::uint16_t>(encoded, 14U));
  require(known_type(type), "unknown frame message type");
  const auto flags = read_be<std::uint32_t>(encoded, 16U);
  constexpr auto known_flags = flag_payload_inline | flag_payload_shared_memory |
                               flag_response_expected | flag_read_only;
  require((flags & ~known_flags) == 0U, "unknown frame flag bit");
  const auto inline_carrier = (flags & flag_payload_inline) != 0U;
  const auto shared_carrier = (flags & flag_payload_shared_memory) != 0U;
  require(inline_carrier != shared_carrier, "frame payload carrier is not exclusive");
  if (shared_carrier) {
    require(shared_memory_eligible(type), "message type is not shared-memory eligible");
    require(flags == shared_memory_flags(type), "frame flags differ from frozen table");
  } else {
    require(flags == inline_flags(type), "frame flags differ from frozen table");
  }
  const auto generation = read_be<std::uint64_t>(encoded, 36U);
  const auto sequence = read_be<std::uint64_t>(encoded, 60U);
  const auto payload_length = read_be<std::uint64_t>(encoded, 68U);
  const auto response_capacity = read_be<std::uint64_t>(encoded, 76U);
  require(generation != 0U && sequence != 0U, "zero generation or sequence");
  require(payload_length != 0U && payload_length <= max_logical_payload_bytes,
          "invalid payload length");
  require(response_capacity == (is_request(type) ? max_response_capacity : 0U),
          "invalid response capacity");
  require(std::all_of(encoded.begin() + 116, encoded.end(), [](std::byte item) {
    return item == std::byte{0};
  }), "nonzero reserved header byte");
  Id128 session{};
  Id128 correlation{};
  Digest digest{};
  std::copy_n(encoded.begin() + 20, session.size(), session.begin());
  std::copy_n(encoded.begin() + 44, correlation.size(), correlation.begin());
  std::copy_n(encoded.begin() + 84, digest.size(), digest.begin());
  return FrameHeader{
      type,
      flags,
      session,
      generation,
      correlation,
      sequence,
      payload_length,
      response_capacity,
      digest,
  };
}

Frame decode_frame(std::span<const std::byte> encoded) {
  require(encoded.size() >= header_bytes && encoded.size() <= max_control_envelope_bytes, "invalid frame size");
  const auto header = decode_frame_header(encoded.first(header_bytes));
  require(header.flags == inline_flags(header.type),
          "decode_frame requires an inline carrier");
  require(header.payload_length == static_cast<std::uint64_t>(encoded.size() - header_bytes),
          "frame length mismatch or trailing bytes");
  Bytes payload(encoded.begin() + header_bytes, encoded.end());
  require(sha256(payload) == header.payload_sha256, "payload digest mismatch");
  const auto decoded_payload = decode_payload(payload);
  require(decoded_payload.type == header.type, "frame and payload types differ");
  return Frame{
      header.type,
      header.flags,
      header.session_id,
      header.generation,
      header.correlation_id,
      header.sequence,
      header.response_capacity,
      std::move(payload),
  };
}

Digest request_digest(MessageType type, std::span<const Field> fields) {
  require(is_request(type) && type != MessageType::client_hello, "request digest requires operation request");
  std::vector<Field> operation_fields;
  for (const auto& field : fields) {
    if (field.id >= 16U) {
      operation_fields.push_back(field);
    }
  }
  require(!operation_fields.empty(), "request has no operation fields");
  auto encoded = encode_fields(operation_fields);
  Bytes input;
  input.reserve(16U + encoded.size());
  constexpr std::string_view domain = "DELTAIPCREQUEST1";
  for (const char item : domain) {
    input.push_back(static_cast<std::byte>(item));
  }
  append_be(input, static_cast<std::uint16_t>(type));
  append_be(input, static_cast<std::uint16_t>(1U));
  append_be(input, static_cast<std::uint16_t>(0U));
  input.insert(input.end(), encoded.begin(), encoded.end());
  return sha256(input);
}

Field field_u8(std::uint16_t id, std::uint8_t value) {
  return Field{id, WireType::u8, Bytes{static_cast<std::byte>(value)}};
}

Field field_u16(std::uint16_t id, std::uint16_t value) {
  Bytes bytes;
  append_be(bytes, value);
  return Field{id, WireType::u16_be, std::move(bytes)};
}

Field field_u32(std::uint16_t id, std::uint32_t value) {
  Bytes bytes;
  append_be(bytes, value);
  return Field{id, WireType::u32_be, std::move(bytes)};
}

Field field_u64(std::uint16_t id, std::uint64_t value) {
  Bytes bytes;
  append_be(bytes, value);
  return Field{id, WireType::u64_be, std::move(bytes)};
}

Field field_id128(std::uint16_t id, const Id128& value) {
  return Field{id, WireType::id128, Bytes(value.begin(), value.end())};
}

Field field_digest(std::uint16_t id, const Digest& value) {
  return Field{id, WireType::sha256, from_digest(value)};
}

Field field_bytes(std::uint16_t id, std::span<const std::byte> value) {
  return Field{id, WireType::bytes, Bytes(value.begin(), value.end())};
}

Field field_text(std::uint16_t id, std::string_view value) {
  Bytes bytes;
  bytes.reserve(value.size());
  for (const char item : value) {
    bytes.push_back(static_cast<std::byte>(item));
  }
  require(canonical_utf8(bytes), "text is not canonical UTF-8");
  return Field{id, WireType::canonical_utf8, std::move(bytes)};
}

Field field_shared_memory_reference(
    std::uint16_t id,
    std::span<const std::byte> value) {
  require(value.size() == 64U, "shared-memory reference has wrong size");
  return Field{id, WireType::shm_reference_64, Bytes(value.begin(), value.end())};
}

const Field& require_field(
    const Payload& payload,
    std::size_t index,
    std::uint16_t id,
    WireType wire_type,
    std::size_t minimum_size,
    std::size_t maximum_size) {
  require(index < payload.fields.size(), "required field is missing");
  const auto& field = payload.fields[index];
  require(field.id == id && field.wire_type == wire_type, "field schema mismatch");
  require(field.value.size() >= minimum_size && field.value.size() <= maximum_size, "field size out of bounds");
  return field;
}

std::uint8_t field_as_u8(const Field& field) {
  require(field.wire_type == WireType::u8 && field.value.size() == 1U, "field is not u8");
  return std::to_integer<std::uint8_t>(field.value.front());
}

std::uint16_t field_as_u16(const Field& field) {
  require(field.wire_type == WireType::u16_be && field.value.size() == 2U, "field is not u16");
  return read_be<std::uint16_t>(field.value, 0U);
}

std::uint32_t field_as_u32(const Field& field) {
  require(field.wire_type == WireType::u32_be && field.value.size() == 4U, "field is not u32");
  return read_be<std::uint32_t>(field.value, 0U);
}

std::uint64_t field_as_u64(const Field& field) {
  require(field.wire_type == WireType::u64_be && field.value.size() == 8U, "field is not u64");
  return read_be<std::uint64_t>(field.value, 0U);
}

Id128 field_as_id128(const Field& field) {
  require(field.wire_type == WireType::id128 && field.value.size() == 16U, "field is not ID128");
  Id128 result{};
  std::copy(field.value.begin(), field.value.end(), result.begin());
  return result;
}

Digest field_as_digest(const Field& field) {
  require(field.wire_type == WireType::sha256 && field.value.size() == 32U, "field is not SHA-256");
  Digest result{};
  std::copy(field.value.begin(), field.value.end(), result.begin());
  return result;
}

std::string field_as_text(const Field& field) {
  require(field.wire_type == WireType::canonical_utf8, "field is not text");
  require(canonical_utf8(field.value), "field text is not canonical");
  std::string result;
  result.reserve(field.value.size());
  for (const auto item : field.value) {
    result.push_back(static_cast<char>(std::to_integer<unsigned char>(item)));
  }
  return result;
}

}  // namespace delta::runtime::sidecar
