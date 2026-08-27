#include <delta/core/canonical.hpp>

#include "sha256.hpp"

#include <array>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <string>
#include <type_traits>
#include <utility>

namespace delta::core::canonical {
namespace {

constexpr std::array<std::byte, 4> magic = {
    std::byte{'D'}, std::byte{'R'}, std::byte{'C'}, std::byte{'1'}};
constexpr std::uint8_t encoding_major = 1U;
constexpr std::uint8_t encoding_minor = 0U;
constexpr std::size_t header_size = 12U;

constexpr std::uint8_t tag_false = 0x01U;
constexpr std::uint8_t tag_true = 0x02U;
constexpr std::uint8_t tag_unsigned = 0x10U;
constexpr std::uint8_t tag_signed = 0x11U;
constexpr std::uint8_t tag_bytes = 0x20U;
constexpr std::uint8_t tag_text = 0x21U;
constexpr std::uint8_t tag_array = 0x30U;
constexpr std::uint8_t tag_map = 0x31U;

[[noreturn]] void reject(ErrorCode code, std::string message) {
  throw DecodeError(code, std::move(message));
}

void require(bool condition, ErrorCode code, const char* message) {
  if (!condition) {
    reject(code, message);
  }
}

[[nodiscard]] bool is_printable_ascii(std::string_view value) noexcept {
  for (const unsigned char byte : value) {
    if (byte < 0x20U || byte > 0x7eU) {
      return false;
    }
  }
  return true;
}

[[nodiscard]] bool is_map_key(std::string_view value) noexcept {
  if (value.empty()) {
    return false;
  }
  for (const unsigned char byte : value) {
    const bool lowercase = byte >= static_cast<unsigned char>('a') &&
                           byte <= static_cast<unsigned char>('z');
    const bool digit = byte >= static_cast<unsigned char>('0') &&
                       byte <= static_cast<unsigned char>('9');
    if (!lowercase && !digit && byte != static_cast<unsigned char>('_')) {
      return false;
    }
  }
  return true;
}

void append_u8(Bytes& output, std::uint8_t value) {
  output.push_back(static_cast<std::byte>(value));
}

void append_u16(Bytes& output, std::uint16_t value) {
  append_u8(output, static_cast<std::uint8_t>((value >> 8U) & 0xffU));
  append_u8(output, static_cast<std::uint8_t>(value & 0xffU));
}

void append_u32(Bytes& output, std::uint32_t value) {
  for (unsigned int shift = 24U;; shift -= 8U) {
    append_u8(output, static_cast<std::uint8_t>((value >> shift) & 0xffU));
    if (shift == 0U) {
      break;
    }
  }
}

void append_u64(Bytes& output, std::uint64_t value) {
  for (unsigned int shift = 56U;; shift -= 8U) {
    append_u8(output, static_cast<std::uint8_t>((value >> shift) & 0xffU));
    if (shift == 0U) {
      break;
    }
  }
}

[[nodiscard]] std::uint32_t checked_u32(std::size_t value, ErrorCode code) {
  require(value <= std::numeric_limits<std::uint32_t>::max(), code, "length exceeds u32");
  return static_cast<std::uint32_t>(value);
}

void encode_text(Bytes& output, std::string_view value, const Limits& limits) {
  require(value.size() <= limits.value_bytes, ErrorCode::value_too_large, "text too large");
  require(is_printable_ascii(value), ErrorCode::invalid_ascii, "text is not printable ASCII");
  append_u8(output, tag_text);
  append_u32(output, checked_u32(value.size(), ErrorCode::value_too_large));
  for (const unsigned char byte : value) {
    output.push_back(static_cast<std::byte>(byte));
  }
}

void encode_value(Bytes& output, const Value& value, const Limits& limits, std::size_t depth) {
  require(depth <= limits.nesting_depth, ErrorCode::nesting_too_deep, "nesting too deep");
  std::visit(
      [&output, &limits, depth](const auto& item) {
        using Item = std::decay_t<decltype(item)>;
        if constexpr (std::is_same_v<Item, bool>) {
          append_u8(output, item ? tag_true : tag_false);
        } else if constexpr (std::is_same_v<Item, std::uint64_t>) {
          append_u8(output, tag_unsigned);
          append_u64(output, item);
        } else if constexpr (std::is_same_v<Item, std::int64_t>) {
          append_u8(output, tag_signed);
          append_u64(output, static_cast<std::uint64_t>(item));
        } else if constexpr (std::is_same_v<Item, Bytes>) {
          require(
              item.size() <= limits.value_bytes,
              ErrorCode::value_too_large,
              "byte string too large");
          append_u8(output, tag_bytes);
          append_u32(output, checked_u32(item.size(), ErrorCode::value_too_large));
          output.insert(output.end(), item.begin(), item.end());
        } else if constexpr (std::is_same_v<Item, std::string>) {
          encode_text(output, item, limits);
        } else if constexpr (std::is_same_v<Item, Value::Array>) {
          require(
              item.size() <= limits.collection_members,
              ErrorCode::collection_too_large,
              "array too large");
          append_u8(output, tag_array);
          append_u32(output, checked_u32(item.size(), ErrorCode::collection_too_large));
          for (const auto& child : item) {
            encode_value(output, child, limits, depth + 1U);
          }
        } else if constexpr (std::is_same_v<Item, Value::Map>) {
          require(
              item.size() <= limits.collection_members,
              ErrorCode::collection_too_large,
              "map too large");
          append_u8(output, tag_map);
          append_u32(output, checked_u32(item.size(), ErrorCode::collection_too_large));
          std::string_view prior;
          bool first = true;
          for (const auto& [key, child] : item) {
            require(is_map_key(key), ErrorCode::invalid_map_key, "invalid map key");
            require(
                first || prior < key,
                ErrorCode::noncanonical_map_order,
                "map keys are not strictly increasing");
            encode_text(output, key, limits);
            encode_value(output, child, limits, depth + 1U);
            prior = key;
            first = false;
          }
        }
      },
      value.data);
}

class Reader {
 public:
  explicit Reader(std::span<const std::byte> input) : input_(input) {}

  [[nodiscard]] std::size_t remaining() const noexcept { return input_.size() - cursor_; }

  [[nodiscard]] std::uint8_t read_u8() {
    require(remaining() >= 1U, ErrorCode::truncated, "truncated u8");
    return std::to_integer<std::uint8_t>(input_[cursor_++]);
  }

  [[nodiscard]] std::uint16_t read_u16() {
    require(remaining() >= 2U, ErrorCode::truncated, "truncated u16");
    const auto value =
        static_cast<std::uint16_t>((static_cast<std::uint16_t>(read_u8()) << 8U) | read_u8());
    return value;
  }

  [[nodiscard]] std::uint32_t read_u32() {
    require(remaining() >= 4U, ErrorCode::truncated, "truncated u32");
    std::uint32_t value = 0;
    for (std::size_t index = 0; index < 4U; ++index) {
      value = (value << 8U) | read_u8();
    }
    return value;
  }

  [[nodiscard]] std::uint64_t read_u64() {
    require(remaining() >= 8U, ErrorCode::truncated, "truncated u64");
    std::uint64_t value = 0;
    for (std::size_t index = 0; index < 8U; ++index) {
      value = (value << 8U) | read_u8();
    }
    return value;
  }

  [[nodiscard]] std::span<const std::byte> read_bytes(std::size_t count) {
    require(count <= remaining(), ErrorCode::truncated, "truncated value");
    const auto result = input_.subspan(cursor_, count);
    cursor_ += count;
    return result;
  }

 private:
  std::span<const std::byte> input_;
  std::size_t cursor_ = 0;
};

[[nodiscard]] std::string decode_text_body(Reader& reader, const Limits& limits) {
  const auto length = static_cast<std::size_t>(reader.read_u32());
  require(length <= limits.value_bytes, ErrorCode::value_too_large, "text too large");
  const auto encoded = reader.read_bytes(length);
  std::string value;
  value.reserve(length);
  for (const auto byte : encoded) {
    value.push_back(static_cast<char>(std::to_integer<unsigned char>(byte)));
  }
  require(is_printable_ascii(value), ErrorCode::invalid_ascii, "text is not printable ASCII");
  return value;
}

[[nodiscard]] Type decode_type(std::uint16_t code) {
  if (code < static_cast<std::uint16_t>(Type::round_config) ||
      code > static_cast<std::uint16_t>(Type::prepared_integer_shard)) {
    reject(ErrorCode::unknown_type, "unknown type code");
  }
  return static_cast<Type>(code);
}

[[nodiscard]] std::int64_t decode_signed(std::uint64_t bits) noexcept {
  constexpr auto sign_bit = std::uint64_t{1} << 63U;
  if ((bits & sign_bit) == 0U) {
    return static_cast<std::int64_t>(bits);
  }
  if (bits == sign_bit) {
    return std::numeric_limits<std::int64_t>::min();
  }
  const auto magnitude = (~bits) + 1U;
  return -static_cast<std::int64_t>(magnitude);
}

[[nodiscard]] Value decode_value(Reader& reader, const Limits& limits, std::size_t depth) {
  require(depth <= limits.nesting_depth, ErrorCode::nesting_too_deep, "nesting too deep");
  const auto tag = reader.read_u8();
  switch (tag) {
    case tag_false:
      return Value::boolean(false);
    case tag_true:
      return Value::boolean(true);
    case tag_unsigned:
      return Value::unsigned_integer(reader.read_u64());
    case tag_signed:
      return Value::signed_integer(decode_signed(reader.read_u64()));
    case tag_bytes: {
      const auto length = static_cast<std::size_t>(reader.read_u32());
      require(length <= limits.value_bytes, ErrorCode::value_too_large, "byte string too large");
      const auto encoded = reader.read_bytes(length);
      return Value::bytes(Bytes(encoded.begin(), encoded.end()));
    }
    case tag_text:
      return Value::text(decode_text_body(reader, limits));
    case tag_array: {
      const auto count = static_cast<std::size_t>(reader.read_u32());
      require(
          count <= limits.collection_members,
          ErrorCode::collection_too_large,
          "array too large");
      Value::Array values;
      values.reserve(count);
      for (std::size_t index = 0; index < count; ++index) {
        values.push_back(decode_value(reader, limits, depth + 1U));
      }
      return Value::array(std::move(values));
    }
    case tag_map: {
      const auto count = static_cast<std::size_t>(reader.read_u32());
      require(
          count <= limits.collection_members,
          ErrorCode::collection_too_large,
          "map too large");
      Value::Map values;
      values.reserve(count);
      std::string prior;
      for (std::size_t index = 0; index < count; ++index) {
        require(reader.read_u8() == tag_text, ErrorCode::invalid_map_key, "map key is not text");
        auto key = decode_text_body(reader, limits);
        require(is_map_key(key), ErrorCode::invalid_map_key, "invalid map key");
        require(
            index == 0U || prior < key,
            ErrorCode::noncanonical_map_order,
            "map keys are not strictly increasing");
        auto child = decode_value(reader, limits, depth + 1U);
        prior = key;
        values.emplace_back(std::move(key), std::move(child));
      }
      return Value::map(std::move(values));
    }
    default:
      reject(ErrorCode::invalid_tag, "invalid typed-value tag");
  }
}

}  // namespace

Value Value::boolean(bool value) { return Value{Data{std::in_place_type<bool>, value}}; }

Value Value::unsigned_integer(std::uint64_t value) {
  return Value{Data{std::in_place_type<std::uint64_t>, value}};
}

Value Value::signed_integer(std::int64_t value) {
  return Value{Data{std::in_place_type<std::int64_t>, value}};
}

Value Value::bytes(Bytes value) {
  return Value{Data{std::in_place_type<Bytes>, std::move(value)}};
}

Value Value::text(std::string value) {
  return Value{Data{std::in_place_type<std::string>, std::move(value)}};
}

Value Value::array(Array value) {
  return Value{Data{std::in_place_type<Array>, std::move(value)}};
}

Value Value::map(Map value) { return Value{Data{std::in_place_type<Map>, std::move(value)}}; }

bool Value::operator==(const Value& other) const { return data == other.data; }

DecodeError::DecodeError(ErrorCode code, std::string message)
    : std::runtime_error(std::move(message)), code_(code) {}

ErrorCode DecodeError::code() const noexcept { return code_; }

Bytes encode(const Envelope& envelope, const Limits& limits) {
  static_cast<void>(hash_domain(envelope.type));
  Bytes payload;
  encode_value(payload, Value::map(envelope.fields), limits, 0U);

  Bytes output;
  output.reserve(header_size + payload.size());
  output.insert(output.end(), magic.begin(), magic.end());
  append_u8(output, encoding_major);
  append_u8(output, encoding_minor);
  append_u16(output, static_cast<std::uint16_t>(envelope.type));
  append_u32(output, checked_u32(payload.size(), ErrorCode::envelope_too_large));
  output.insert(output.end(), payload.begin(), payload.end());
  require(
      output.size() <= limits.envelope_bytes,
      ErrorCode::envelope_too_large,
      "envelope too large");
  return output;
}

Envelope decode(std::span<const std::byte> bytes, const Limits& limits) {
  require(bytes.size() <= limits.envelope_bytes, ErrorCode::envelope_too_large, "envelope too large");
  require(bytes.size() >= header_size, ErrorCode::truncated, "truncated envelope header");
  for (std::size_t index = 0; index < magic.size(); ++index) {
    require(bytes[index] == magic[index], ErrorCode::bad_magic, "invalid envelope magic");
  }

  Reader header(bytes.subspan(magic.size()));
  require(
      header.read_u8() == encoding_major && header.read_u8() == encoding_minor,
      ErrorCode::unsupported_version,
      "unsupported encoding version");
  const auto type = decode_type(header.read_u16());
  const auto payload_length = static_cast<std::size_t>(header.read_u32());
  const auto actual_length = bytes.size() - header_size;
  require(
      payload_length <= actual_length,
      ErrorCode::payload_length_mismatch,
      "declared payload is truncated");
  require(payload_length == actual_length, ErrorCode::trailing_bytes, "trailing envelope bytes");

  Reader payload(bytes.subspan(header_size, payload_length));
  auto root = decode_value(payload, limits, 0U);
  require(payload.remaining() == 0U, ErrorCode::trailing_bytes, "trailing payload bytes");
  auto* fields = std::get_if<Value::Map>(&root.data);
  require(fields != nullptr, ErrorCode::invalid_root, "envelope root is not a map");
  return Envelope{type, std::move(*fields)};
}

std::string sha256_hex(std::span<const std::byte> bytes) {
  constexpr std::array<char, 16> alphabet = {
      '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f'};
  const auto digest = detail::sha256(bytes);
  std::string result;
  result.reserve(digest.size() * 2U);
  for (const auto byte : digest) {
    const auto value = std::to_integer<std::uint8_t>(byte);
    result.push_back(alphabet[value >> 4U]);
    result.push_back(alphabet[value & 0x0fU]);
  }
  return result;
}

std::string content_id(Type type, std::span<const std::byte> envelope) {
  const auto domain = hash_domain(type);
  Bytes input;
  input.reserve(domain.size() + 1U + envelope.size());
  for (const unsigned char byte : domain) {
    input.push_back(static_cast<std::byte>(byte));
  }
  input.push_back(std::byte{0});
  input.insert(input.end(), envelope.begin(), envelope.end());
  return "sha256:" + sha256_hex(input);
}

std::string_view hash_domain(Type type) {
  switch (type) {
    case Type::round_config:
      return "deltareduce:003:round-config:v1";
    case Type::work_ticket:
      return "deltareduce:003:work-ticket:v1";
    case Type::vote:
      return "deltareduce:003:vote:v1";
    case Type::quorum_certificate:
      return "deltareduce:003:quorum-certificate:v1";
    case Type::round_state:
      return "deltareduce:003:round-state:v1";
    case Type::command:
      return "deltareduce:003:command:v1";
    case Type::effect_batch:
      return "deltareduce:003:effect-batch:v1";
    case Type::wal_record:
      return "deltareduce:003:wal-record:v1";
    case Type::runtime_descriptor:
      return "deltareduce:003:runtime-descriptor:v1";
    case Type::prepared_integer_shard:
      return "deltareduce:003:prepared-integer-shard:v1";
  }
  throw std::invalid_argument("unknown canonical type");
}

std::string_view type_name(Type type) {
  switch (type) {
    case Type::round_config:
      return "ROUND_CONFIG";
    case Type::work_ticket:
      return "WORK_TICKET";
    case Type::vote:
      return "VOTE";
    case Type::quorum_certificate:
      return "QUORUM_CERTIFICATE";
    case Type::round_state:
      return "ROUND_STATE";
    case Type::command:
      return "COMMAND";
    case Type::effect_batch:
      return "EFFECT_BATCH";
    case Type::wal_record:
      return "WAL_RECORD";
    case Type::runtime_descriptor:
      return "RUNTIME_DESCRIPTOR";
    case Type::prepared_integer_shard:
      return "PREPARED_INTEGER_SHARD";
  }
  throw std::invalid_argument("unknown canonical type");
}

}  // namespace delta::core::canonical
