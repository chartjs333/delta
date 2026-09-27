#pragma once

#include <cstddef>
#include <cstdint>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <variant>
#include <vector>

namespace delta::core::canonical {

using Bytes = std::vector<std::byte>;

struct MapEntry;

enum class Type : std::uint16_t {
  round_config = 1,
  work_ticket = 2,
  vote = 3,
  quorum_certificate = 4,
  round_state = 5,
  command = 6,
  effect_batch = 7,
  wal_record = 8,
  runtime_descriptor = 9,
  prepared_integer_shard = 10,
};

struct Value {
  using Array = std::vector<Value>;
  using Map = std::vector<MapEntry>;
  using Data = std::variant<bool, std::uint64_t, std::int64_t, Bytes, std::string, Array, Map>;

  Data data;

  explicit Value(Data value);
  Value(const Value& other);
  Value(Value&& other) noexcept;
  Value& operator=(const Value& other);
  Value& operator=(Value&& other) noexcept;
  ~Value();

  static Value boolean(bool value);
  static Value unsigned_integer(std::uint64_t value);
  static Value signed_integer(std::int64_t value);
  static Value bytes(Bytes value);
  static Value text(std::string value);
  static Value array(Array value);
  static Value map(Map value);

  bool operator==(const Value& other) const;
};

struct MapEntry {
  std::string key;
  Value value;

  bool operator==(const MapEntry& other) const = default;
};

struct Envelope {
  Type type;
  Value::Map fields;

  bool operator==(const Envelope&) const = default;
};

enum class ErrorCode {
  envelope_too_large,
  bad_magic,
  unsupported_version,
  unknown_type,
  payload_length_mismatch,
  trailing_bytes,
  invalid_root,
  invalid_tag,
  truncated,
  value_too_large,
  collection_too_large,
  nesting_too_deep,
  invalid_ascii,
  invalid_map_key,
  noncanonical_map_order,
};

class DecodeError final : public std::runtime_error {
 public:
  DecodeError(ErrorCode code, std::string message);

  [[nodiscard]] ErrorCode code() const noexcept;

 private:
  ErrorCode code_;
};

struct Limits {
  std::size_t envelope_bytes = 16U * 1024U * 1024U;
  std::size_t nesting_depth = 32U;
  std::size_t collection_members = 100'000U;
  std::size_t value_bytes = 4U * 1024U * 1024U;
};

[[nodiscard]] Bytes encode(const Envelope& envelope, const Limits& limits = {});
[[nodiscard]] Envelope decode(std::span<const std::byte> bytes, const Limits& limits = {});
[[nodiscard]] std::string content_id(Type type, std::span<const std::byte> envelope);
[[nodiscard]] std::string sha256_hex(std::span<const std::byte> bytes);
[[nodiscard]] std::string_view hash_domain(Type type);
[[nodiscard]] std::string_view type_name(Type type);

}  // namespace delta::core::canonical
