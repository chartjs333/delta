#include <delta/core/canonical.hpp>
#include <delta/core/protocol.hpp>
#include <delta/core/transition.hpp>

#include <algorithm>
#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <optional>
#include <sstream>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>

namespace {

namespace canonical = delta::core::canonical;
namespace protocol = delta::core::protocol;

constexpr std::uint64_t kMaximumFixtureBytes = 64U * 1024U * 1024U;
constexpr std::uint64_t kMaximumInitialStateBytes = 16U * 1024U * 1024U;
constexpr std::uint64_t kMaximumOperationCount = 10'000'000U;
constexpr std::array<std::byte, 8> kCorpusMagic = {
    std::byte{'D'}, std::byte{'L'}, std::byte{'T'}, std::byte{'S'},
    std::byte{'T'}, std::byte{'R'}, std::byte{'C'}, std::byte{'1'}};
constexpr std::uint16_t kCorpusMajor = 1U;
constexpr std::uint16_t kCorpusMinor = 0U;
constexpr std::string_view kRequestPrefix = "sidecar-benchmark-";
constexpr std::string_view kActorId = "sidecar-benchmark-worker";
constexpr std::string_view kCommitmentDomain =
    "deltareduce:010:sidecar-benchmark-commitment:v1:";
constexpr std::uint64_t kLogicalTick = 10U;
constexpr std::uint64_t kDeterministicOperationCount = 61'000U;
constexpr std::string_view kEpochId =
    "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd";
constexpr std::string_view kRoundContract =
    R"JSON({"contract_id":"sha256:c7a61fab1f690d454ca07f7158e3de896a5af24e315dbe0e9eab6b43ee6d3c59","parameter_schema":{"parameter_ids":["decoder.bias"],"schema_hash":"sha256:258d2956112fb49a078b4e2c001d215d1c733509eef180088ad19bb8963083e4"},"round_config":{"body_hash":"sha256:ba04c93913be2f015e22e3f731235fd5044fdc61a4929ad64bbf9ef966d8ae97","domain_ids":["domain-text-en"],"parameter_schema_hash":"sha256:258d2956112fb49a078b4e2c001d215d1c733509eef180088ad19bb8963083e4","shard_plan_hash":"sha256:6c5f44cfbdc8a4ca5f6c52e3bf61e63fff6c1538608b60868b3e38f6ff9b8078"},"round_id":"round-003-fixture","shard_plan":{"assignments":[{"domain_id":"domain-text-en","parameter_id":"decoder.bias","shard_id":"shard-000","vote_context_id":"NORMAL-PARAM-DOMAIN-TEXT-EN-SHARD-000:round-003-fixture"}],"plan_hash":"sha256:6c5f44cfbdc8a4ca5f6c52e3bf61e63fff6c1538608b60868b3e38f6ff9b8078"}})JSON";
constexpr std::string_view kPrefixEncoding =
    "DLTSTRC1_U64_ORDINAL_U32_LENGTH_COMMAND_SHA256";
constexpr std::string_view kExecutionBindingEncoding =
    "DLTSPB1_U64_COUNT_THEN_U64_ORDINAL_U32_REQUEST_BYTES_COMMAND_STATUS_EFFECT_ROOTS_SEQUENCE_EVENT_SHA256";
constexpr std::string_view kExecutionBindingDomain =
    "deltareduce:010:native-projection-binding:v1";
constexpr std::string_view kTicketMappingEncoding =
    "DLTSTW1_U64_COUNT_THEN_U64_ORDINAL_U32_TICKET_BYTES_U32_WORKER_BYTES_U64_EPOCH_BODY_SHA256";
constexpr std::string_view kTicketMappingDomain =
    "deltareduce:010:initial-abstraction-ticket-map:v1";

[[noreturn]] void fail(std::string message) {
  throw std::runtime_error(std::move(message));
}

void require(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

[[nodiscard]] constexpr std::uint32_t choose(
    std::uint32_t x,
    std::uint32_t y,
    std::uint32_t z) noexcept {
  return (x & y) ^ (~x & z);
}

[[nodiscard]] constexpr std::uint32_t majority(
    std::uint32_t x,
    std::uint32_t y,
    std::uint32_t z) noexcept {
  return (x & y) ^ (x & z) ^ (y & z);
}

[[nodiscard]] constexpr std::uint32_t large_sigma0(std::uint32_t value) noexcept {
  return std::rotr(value, 2) ^ std::rotr(value, 13) ^ std::rotr(value, 22);
}

[[nodiscard]] constexpr std::uint32_t large_sigma1(std::uint32_t value) noexcept {
  return std::rotr(value, 6) ^ std::rotr(value, 11) ^ std::rotr(value, 25);
}

[[nodiscard]] constexpr std::uint32_t small_sigma0(std::uint32_t value) noexcept {
  return std::rotr(value, 7) ^ std::rotr(value, 18) ^ (value >> 3U);
}

[[nodiscard]] constexpr std::uint32_t small_sigma1(std::uint32_t value) noexcept {
  return std::rotr(value, 17) ^ std::rotr(value, 19) ^ (value >> 10U);
}

class Sha256 final {
 public:
  void update(std::span<const std::byte> input) {
    require(
        input.size() <= (std::numeric_limits<std::uint64_t>::max() / 8U) - total_bytes_,
        "SHA-256 input length exceeds the 64-bit encoding");
    total_bytes_ += static_cast<std::uint64_t>(input.size());

    std::size_t cursor = 0U;
    if (buffer_size_ != 0U) {
      const auto count = std::min(input.size(), buffer_.size() - buffer_size_);
      std::copy_n(input.begin(), count, buffer_.begin() + static_cast<std::ptrdiff_t>(buffer_size_));
      buffer_size_ += count;
      cursor += count;
      if (buffer_size_ == buffer_.size()) {
        transform(buffer_.data());
        buffer_size_ = 0U;
      }
    }

    while ((input.size() - cursor) >= buffer_.size()) {
      // Keep transform's input backed by the fixed-size block. Besides making
      // the 64-byte precondition explicit, this avoids GCC 14 losing the loop
      // bound while inlining pointer arithmetic from a smaller caller span.
      std::copy_n(
          input.begin() + static_cast<std::ptrdiff_t>(cursor), buffer_.size(), buffer_.begin());
      transform(buffer_.data());
      cursor += buffer_.size();
    }
    const auto remaining = input.size() - cursor;
    if (remaining != 0U) {
      std::copy_n(input.begin() + static_cast<std::ptrdiff_t>(cursor), remaining, buffer_.begin());
      buffer_size_ = remaining;
    }
  }

  [[nodiscard]] std::array<std::byte, 32> digest() const {
    auto copy = *this;
    return copy.finish();
  }

 private:
  static constexpr std::array<std::uint32_t, 64> kRoundConstants = {
      0x428a2f98U, 0x71374491U, 0xb5c0fbcfU, 0xe9b5dba5U, 0x3956c25bU, 0x59f111f1U,
      0x923f82a4U, 0xab1c5ed5U, 0xd807aa98U, 0x12835b01U, 0x243185beU, 0x550c7dc3U,
      0x72be5d74U, 0x80deb1feU, 0x9bdc06a7U, 0xc19bf174U, 0xe49b69c1U, 0xefbe4786U,
      0x0fc19dc6U, 0x240ca1ccU, 0x2de92c6fU, 0x4a7484aaU, 0x5cb0a9dcU, 0x76f988daU,
      0x983e5152U, 0xa831c66dU, 0xb00327c8U, 0xbf597fc7U, 0xc6e00bf3U, 0xd5a79147U,
      0x06ca6351U, 0x14292967U, 0x27b70a85U, 0x2e1b2138U, 0x4d2c6dfcU, 0x53380d13U,
      0x650a7354U, 0x766a0abbU, 0x81c2c92eU, 0x92722c85U, 0xa2bfe8a1U, 0xa81a664bU,
      0xc24b8b70U, 0xc76c51a3U, 0xd192e819U, 0xd6990624U, 0xf40e3585U, 0x106aa070U,
      0x19a4c116U, 0x1e376c08U, 0x2748774cU, 0x34b0bcb5U, 0x391c0cb3U, 0x4ed8aa4aU,
      0x5b9cca4fU, 0x682e6ff3U, 0x748f82eeU, 0x78a5636fU, 0x84c87814U, 0x8cc70208U,
      0x90befffaU, 0xa4506cebU, 0xbef9a3f7U, 0xc67178f2U,
  };

  static constexpr std::array<std::uint32_t, 8> kInitialState = {
      0x6a09e667U,
      0xbb67ae85U,
      0x3c6ef372U,
      0xa54ff53aU,
      0x510e527fU,
      0x9b05688cU,
      0x1f83d9abU,
      0x5be0cd19U,
  };

  [[nodiscard]] static std::uint32_t load_u32(const std::byte* input) noexcept {
    return (static_cast<std::uint32_t>(std::to_integer<std::uint8_t>(input[0])) << 24U) |
           (static_cast<std::uint32_t>(std::to_integer<std::uint8_t>(input[1])) << 16U) |
           (static_cast<std::uint32_t>(std::to_integer<std::uint8_t>(input[2])) << 8U) |
           static_cast<std::uint32_t>(std::to_integer<std::uint8_t>(input[3]));
  }

  void transform(const std::byte* block) noexcept {
    std::array<std::uint32_t, 64> words{};
    for (std::size_t index = 0U; index < 16U; ++index) {
      words[index] = load_u32(block + (index * 4U));
    }
    for (std::size_t index = 16U; index < words.size(); ++index) {
      words[index] = small_sigma1(words[index - 2U]) + words[index - 7U] +
                     small_sigma0(words[index - 15U]) + words[index - 16U];
    }

    auto a = state_[0];
    auto b = state_[1];
    auto c = state_[2];
    auto d = state_[3];
    auto e = state_[4];
    auto f = state_[5];
    auto g = state_[6];
    auto h = state_[7];
    for (std::size_t index = 0U; index < words.size(); ++index) {
      const auto temporary1 =
          h + large_sigma1(e) + choose(e, f, g) + kRoundConstants[index] + words[index];
      const auto temporary2 = large_sigma0(a) + majority(a, b, c);
      h = g;
      g = f;
      f = e;
      e = d + temporary1;
      d = c;
      c = b;
      b = a;
      a = temporary1 + temporary2;
    }
    state_[0] += a;
    state_[1] += b;
    state_[2] += c;
    state_[3] += d;
    state_[4] += e;
    state_[5] += f;
    state_[6] += g;
    state_[7] += h;
  }

  [[nodiscard]] std::array<std::byte, 32> finish() {
    const auto bit_length = total_bytes_ * 8U;
    buffer_[buffer_size_++] = std::byte{0x80};
    if (buffer_size_ > 56U) {
      std::fill(buffer_.begin() + static_cast<std::ptrdiff_t>(buffer_size_), buffer_.end(),
                std::byte{0});
      transform(buffer_.data());
      buffer_size_ = 0U;
    }
    std::fill(buffer_.begin() + static_cast<std::ptrdiff_t>(buffer_size_),
              buffer_.begin() + 56, std::byte{0});
    for (std::size_t index = 0U; index < 8U; ++index) {
      const auto shift = static_cast<unsigned int>((7U - index) * 8U);
      buffer_[56U + index] = static_cast<std::byte>((bit_length >> shift) & 0xffU);
    }
    transform(buffer_.data());

    std::array<std::byte, 32> result{};
    for (std::size_t index = 0U; index < state_.size(); ++index) {
      result[(index * 4U)] = static_cast<std::byte>((state_[index] >> 24U) & 0xffU);
      result[(index * 4U) + 1U] = static_cast<std::byte>((state_[index] >> 16U) & 0xffU);
      result[(index * 4U) + 2U] = static_cast<std::byte>((state_[index] >> 8U) & 0xffU);
      result[(index * 4U) + 3U] = static_cast<std::byte>(state_[index] & 0xffU);
    }
    return result;
  }

  std::array<std::uint32_t, 8> state_ = kInitialState;
  std::array<std::byte, 64> buffer_{};
  std::size_t buffer_size_ = 0U;
  std::uint64_t total_bytes_ = 0U;
};

template <std::size_t Size>
[[nodiscard]] std::string hex(const std::array<std::byte, Size>& bytes) {
  constexpr char digits[] = "0123456789abcdef";
  std::string result;
  result.reserve(bytes.size() * 2U);
  for (const auto byte : bytes) {
    const auto value = std::to_integer<std::uint8_t>(byte);
    result.push_back(digits[value >> 4U]);
    result.push_back(digits[value & 0x0fU]);
  }
  return result;
}

[[nodiscard]] std::array<std::byte, 32> sha256(std::span<const std::byte> bytes) {
  Sha256 value;
  value.update(bytes);
  return value.digest();
}

[[nodiscard]] std::array<std::byte, 2> encode_u16(std::uint16_t value) noexcept {
  return {
      static_cast<std::byte>((value >> 8U) & 0xffU),
      static_cast<std::byte>(value & 0xffU),
  };
}

[[nodiscard]] std::array<std::byte, 4> encode_u32(std::uint32_t value) noexcept {
  std::array<std::byte, 4> result{};
  for (std::size_t index = 0U; index < result.size(); ++index) {
    const auto shift = static_cast<unsigned int>((result.size() - index - 1U) * 8U);
    result[index] = static_cast<std::byte>((value >> shift) & 0xffU);
  }
  return result;
}

[[nodiscard]] std::array<std::byte, 8> encode_u64(std::uint64_t value) noexcept {
  std::array<std::byte, 8> result{};
  for (std::size_t index = 0U; index < result.size(); ++index) {
    const auto shift = static_cast<unsigned int>((result.size() - index - 1U) * 8U);
    result[index] = static_cast<std::byte>((value >> shift) & 0xffU);
  }
  return result;
}

[[nodiscard]] std::uint32_t checked_u32(std::size_t value, std::string_view label) {
  require(value <= std::numeric_limits<std::uint32_t>::max(),
          std::string(label) + " exceeds u32");
  return static_cast<std::uint32_t>(value);
}

[[nodiscard]] std::uint64_t parse_count(std::string_view encoded) {
  require(!encoded.empty(), "operation count is empty");
  require(encoded == "0" || encoded.front() != '0',
          "operation count is not canonical decimal");
  std::uint64_t value = 0U;
  for (const char digit : encoded) {
    require(digit >= '0' && digit <= '9', "operation count is not unsigned decimal");
    const auto decoded = static_cast<std::uint64_t>(digit - '0');
    require(value <= (std::numeric_limits<std::uint64_t>::max() - decoded) / 10U,
            "operation count exceeds u64");
    value = (value * 10U) + decoded;
  }
  require(value <= kMaximumOperationCount, "operation count exceeds generator bound");
  return value;
}

[[nodiscard]] std::string read_bounded_file(const std::filesystem::path& path) {
  std::error_code error;
  const auto size = std::filesystem::file_size(path, error);
  require(!error, "cannot stat golden fixture");
  require(size <= kMaximumFixtureBytes, "golden fixture exceeds bounded parser limit");
  require(size <= static_cast<std::uintmax_t>(std::numeric_limits<std::size_t>::max()),
          "golden fixture exceeds addressable memory");

  std::ifstream input(path, std::ios::binary);
  require(input.good(), "cannot open golden fixture");
  std::string result(static_cast<std::size_t>(size), '\0');
  if (!result.empty()) {
    require(result.size() <= static_cast<std::size_t>(std::numeric_limits<std::streamsize>::max()),
            "golden fixture exceeds stream limit");
    input.read(result.data(), static_cast<std::streamsize>(result.size()));
    require(input.gcount() == static_cast<std::streamsize>(result.size()),
            "golden fixture read was truncated");
  }
  require(input.peek() == std::char_traits<char>::eof(), "golden fixture changed while reading");
  return result;
}

[[nodiscard]] std::uint8_t hex_nibble(char value) {
  if (value >= '0' && value <= '9') {
    return static_cast<std::uint8_t>(value - '0');
  }
  if (value >= 'a' && value <= 'f') {
    return static_cast<std::uint8_t>(value - 'a' + 10);
  }
  fail("golden fixture contains noncanonical hexadecimal");
}

[[nodiscard]] canonical::Bytes decode_hex(std::string_view encoded) {
  require((encoded.size() % 2U) == 0U, "golden envelope has odd hexadecimal length");
  require((encoded.size() / 2U) <= kMaximumInitialStateBytes,
          "golden initial state exceeds generator bound");
  canonical::Bytes result;
  result.reserve(encoded.size() / 2U);
  for (std::size_t index = 0U; index < encoded.size(); index += 2U) {
    const auto value = static_cast<std::uint8_t>(
        static_cast<std::uint8_t>(hex_nibble(encoded[index]) << 4U) |
        hex_nibble(encoded[index + 1U]));
    result.push_back(static_cast<std::byte>(value));
  }
  return result;
}

void require_at(std::string_view document, std::size_t offset, std::string_view expected) {
  require(offset <= document.size() && expected.size() <= document.size() - offset &&
              document.substr(offset, expected.size()) == expected,
          "golden fixture vector layout is not canonical");
}

[[nodiscard]] canonical::Bytes initial_state_from_fixture(
    const std::filesystem::path& fixture_path) {
  const auto document = read_bounded_file(fixture_path);
  constexpr std::string_view envelope_prefix = "\"envelope_hex\":\"";
  constexpr std::string_view digest_prefix = ",\"envelope_sha256\":\"";
  constexpr std::string_view type_prefix = ",\"type_code\":";
  std::size_t cursor = 0U;
  bool found = false;
  canonical::Bytes selected;

  while ((cursor = document.find(envelope_prefix, cursor)) != std::string::npos) {
    const auto hex_begin = cursor + envelope_prefix.size();
    const auto hex_end = document.find('"', hex_begin);
    require(hex_end != std::string::npos, "golden fixture envelope is unterminated");
    require_at(document, hex_end + 1U, digest_prefix);
    const auto digest_begin = hex_end + 1U + digest_prefix.size();
    const auto digest_end = document.find('"', digest_begin);
    require(digest_end != std::string::npos, "golden fixture digest is unterminated");
    require_at(document, digest_end + 1U, type_prefix);
    const auto type_begin = digest_end + 1U + type_prefix.size();
    auto type_end = type_begin;
    std::uint64_t type_code = 0U;
    while (type_end < document.size() && document[type_end] >= '0' &&
           document[type_end] <= '9') {
      const auto digit = static_cast<std::uint64_t>(document[type_end] - '0');
      require(type_code <= (std::numeric_limits<std::uint64_t>::max() - digit) / 10U,
              "golden fixture type code exceeds u64");
      type_code = (type_code * 10U) + digit;
      ++type_end;
    }
    require(type_end != type_begin, "golden fixture type code is empty");
    require(type_end < document.size() &&
                (document[type_end] == ',' || document[type_end] == '}'),
            "golden fixture type code is not delimited");

    if (type_code == static_cast<std::uint16_t>(canonical::Type::round_state)) {
      require(!found, "golden fixture contains duplicate type-5 vectors");
      const auto encoded_hex =
          std::string_view(document).substr(hex_begin, hex_end - hex_begin);
      const auto declared_digest =
          std::string_view(document).substr(digest_begin, digest_end - digest_begin);
      require(declared_digest.size() == 64U,
              "golden type-5 digest length is not SHA-256");
      selected = decode_hex(encoded_hex);
      require(canonical::sha256_hex(selected) == declared_digest,
              "golden type-5 envelope digest mismatch");
      static_cast<void>(protocol::parse_round_state(selected));
      found = true;
    }
    cursor = type_end;
  }
  require(found, "golden fixture has no type-5 initial state");
  return selected;
}

[[nodiscard]] std::string request_id(std::uint64_t ordinal) {
  const auto digits = std::to_string(ordinal);
  require(digits.size() <= 20U, "command ordinal exceeds fixed request-ID width");
  return std::string(kRequestPrefix) + std::string(20U - digits.size(), '0') + digits;
}

[[nodiscard]] std::string commitment_id(std::uint64_t ordinal) {
  const auto input = std::string(kCommitmentDomain) + request_id(ordinal);
  return "sha256:" + canonical::sha256_hex(std::as_bytes(std::span(input)));
}

[[nodiscard]] canonical::Bytes command_for(
    const protocol::RoundState& initial_state,
    std::uint64_t ordinal) {
  return protocol::encode(protocol::Command{
      std::string(kActorId),
      commitment_id(ordinal),
      "ACCEPT_COMMITMENT",
      initial_state.height,
      kLogicalTick,
      request_id(ordinal),
      initial_state.round_id,
      initial_state.view,
  });
}

class CorpusWriter final {
 public:
  explicit CorpusWriter(const std::filesystem::path& path)
      : output_(path, std::ios::binary | std::ios::trunc) {
    require(output_.good(), "cannot create benchmark trace output");
  }

  void write(std::span<const std::byte> bytes) {
    require(bytes.size() <= static_cast<std::size_t>(std::numeric_limits<std::streamsize>::max()),
            "benchmark trace write exceeds stream limit");
    require(bytes.size() <= std::numeric_limits<std::uint64_t>::max() - bytes_written_,
            "benchmark trace byte count exceeds u64");
    if (!bytes.empty()) {
      output_.write(
          reinterpret_cast<const char*>(bytes.data()),
          static_cast<std::streamsize>(bytes.size()));
      require(output_.good(), "benchmark trace write failed");
      file_hash_.update(bytes);
      bytes_written_ += static_cast<std::uint64_t>(bytes.size());
    }
  }

  template <std::size_t Size>
  void write(const std::array<std::byte, Size>& bytes) {
    write(std::span<const std::byte>(bytes));
  }

  [[nodiscard]] std::array<std::byte, 32> finish() {
    output_.flush();
    require(output_.good(), "benchmark trace flush failed");
    output_.close();
    require(!output_.fail(), "benchmark trace close failed");
    return file_hash_.digest();
  }

  [[nodiscard]] std::uint64_t bytes_written() const noexcept { return bytes_written_; }

 private:
  std::ofstream output_;
  Sha256 file_hash_;
  std::uint64_t bytes_written_ = 0U;
};

[[nodiscard]] std::string json_string(std::string_view value) {
  constexpr char hex_digits[] = "0123456789abcdef";
  std::string result{"\""};
  for (const unsigned char character : value) {
    switch (character) {
      case '"':
        result += "\\\"";
        break;
      case '\\':
        result += "\\\\";
        break;
      case '\b':
        result += "\\b";
        break;
      case '\f':
        result += "\\f";
        break;
      case '\n':
        result += "\\n";
        break;
      case '\r':
        result += "\\r";
        break;
      case '\t':
        result += "\\t";
        break;
      default:
        if (character < 0x20U) {
          result += "\\u00";
          result.push_back(hex_digits[character >> 4U]);
          result.push_back(hex_digits[character & 0x0fU]);
        } else {
          result.push_back(static_cast<char>(character));
        }
    }
  }
  result.push_back('"');
  return result;
}

struct ProjectionOutput final {
  std::string source_commit;
  std::string source_tree;
  std::filesystem::path formal_trace_path;
  std::filesystem::path receipt_path;
};

[[nodiscard]] std::span<const std::byte> as_bytes(std::string_view value) noexcept {
  return std::as_bytes(std::span(value.data(), value.size()));
}

void hash_ascii(Sha256& hash, std::string_view value) { hash.update(as_bytes(value)); }

template <std::size_t Size>
void hash_array(Sha256& hash, const std::array<std::byte, Size>& value) {
  hash.update(value);
}

[[nodiscard]] std::array<std::byte, 32> content_digest(std::string_view identity) {
  constexpr std::string_view prefix = "sha256:";
  require(identity.starts_with(prefix) && identity.size() == prefix.size() + 64U,
          "content identity is not canonical SHA-256");
  std::array<std::byte, 32> result{};
  for (std::size_t index = 0U; index < result.size(); ++index) {
    result[index] = static_cast<std::byte>(
        static_cast<std::uint8_t>(hex_nibble(identity[prefix.size() + (index * 2U)]) << 4U) |
        hex_nibble(identity[prefix.size() + (index * 2U) + 1U]));
  }
  return result;
}

void hash_length_prefixed_ascii(Sha256& hash, std::string_view value) {
  hash_array(hash, encode_u32(checked_u32(value.size(), "ASCII value length")));
  hash_ascii(hash, value);
}

[[nodiscard]] bool lowercase_git_id(std::string_view value) noexcept {
  return value.size() == 40U && std::all_of(value.begin(), value.end(), [](char character) {
           return (character >= '0' && character <= '9') ||
                  (character >= 'a' && character <= 'f');
         });
}

void write_text_file(const std::filesystem::path& path, std::string_view contents) {
  require(!path.empty(), "projection output path is empty");
  std::error_code error;
  if (!path.parent_path().empty()) {
    std::filesystem::create_directories(path.parent_path(), error);
    require(!error, "cannot create projection output directory");
  }
  std::ofstream output(path, std::ios::binary | std::ios::trunc);
  require(output.good(), "cannot create projection output");
  require(contents.size() <=
              static_cast<std::size_t>(std::numeric_limits<std::streamsize>::max()),
          "projection output exceeds stream limit");
  output.write(contents.data(), static_cast<std::streamsize>(contents.size()));
  output.flush();
  require(output.good(), "cannot flush projection output");
  output.close();
  require(!output.fail(), "cannot close projection output");
}

[[nodiscard]] std::string formal_event(
    const protocol::Command& command,
    const delta::core::transition::TransitionResult& transition,
    std::uint64_t durable_sequence) {
  std::ostringstream output;
  output << "{\"action_id\":\"ACT-COMMIT\",\"actor_id\":"
         << json_string(command.actor_id)
         << ",\"actor_role\":\"WORKER\",\"artifact_refs\":[],\"body_hash\":"
         << json_string(command.body_hash) << ",\"durable_sequence\":" << durable_sequence
         << ",\"error_code\":null,\"height\":" << command.height
         << ",\"logical_time\":" << command.logical_tick << ",\"next_state_root\":"
         << json_string(transition.next_state_id)
         << ",\"outcome\":\"ACCEPTED\",\"parent_hashes\":[],\"prior_state_root\":"
         << json_string(transition.prior_state_id) << ",\"request_id\":"
         << json_string(command.request_id)
         << ",\"result_hash\":null,\"round_id\":" << json_string(command.round_id)
         << ",\"schema_version\":\"1.0.0\",\"validator_epoch\":"
         << json_string(kEpochId) << ",\"view\":" << command.view
         << ",\"vote_context_id\":null}";
  return output.str();
}

[[nodiscard]] std::string initial_abstraction_witness(
    const protocol::RoundState& state,
    std::uint64_t operation_count,
    std::string_view initial_state_root,
    std::string_view command_transcript_sha256,
    std::string_view ticket_mapping_sha256) {
  std::ostringstream output;
  output << "{\"abort_request_count\":0,\"abstraction_version\":\"1.0.0\""
         << ",\"active_lease_count\":" << operation_count
         << ",\"canonical_input_operation_count\":" << operation_count
         << ",\"certificate_progress_open\":true"
         << ",\"command_transcript_encoding\":" << json_string(kPrefixEncoding)
         << ",\"command_transcript_sha256\":" << json_string(command_transcript_sha256)
         << ",\"completed_ticket_count\":" << operation_count
         << ",\"content_universe_rule\":\"EXACT_COMMAND_BODY_HASHES\""
         << ",\"enable_ticket_actions\":true,\"first_ordinal\":0"
         << ",\"initial_commitment_count\":0"
         << ",\"initial_phase\":\"TICKETING_OPEN\",\"initial_state_root\":"
         << json_string(initial_state_root) << ",\"input_closed\":false,\"last_ordinal\":"
         << (operation_count - 1U) << ",\"lease_epoch\":0"
         << ",\"mapping_rule\":\"TICKET_ID_REQUEST_ID_WORKER_COMMAND_ACTOR_LEASE_EPOCH_0_CONTENT_BODY_HASH\""
         << ",\"planned_ticket_count\":" << operation_count << ",\"round_id\":"
         << json_string(state.round_id)
         << ",\"schema_version\":\"1.0.0\",\"ticket_count\":" << operation_count
         << ",\"ticket_mapping_encoding\":" << json_string(kTicketMappingEncoding)
         << ",\"ticket_mapping_sha256\":" << json_string(ticket_mapping_sha256)
         << ",\"type_name\":\"FEATURE010_INITIAL_ABSTRACTION_WITNESS\""
         << ",\"worker_universe_rule\":\"EXACT_COMMAND_ACTOR_IDS\"}";
  return output.str();
}

void generate(
    const std::filesystem::path& fixture_path,
    std::uint64_t operation_count,
    const std::filesystem::path& output_path,
    const std::optional<ProjectionOutput>& projection) {
  require(!output_path.empty(), "benchmark trace output path is empty");
  require(operation_count > 0U, "operation count must be positive");
  if (projection.has_value()) {
    require(
        operation_count == kDeterministicOperationCount,
        "formal projection requires the exact 61,000-operation frozen workload");
    require(lowercase_git_id(projection->source_commit), "source commit is not a lowercase Git ID");
    require(lowercase_git_id(projection->source_tree), "source tree is not a lowercase Git ID");
    require(!projection->formal_trace_path.empty(), "formal trace output path is empty");
    require(!projection->receipt_path.empty(), "formal receipt output path is empty");
  }
  const auto initial_bytes = initial_state_from_fixture(fixture_path);
  auto initial_state = protocol::parse_round_state(initial_bytes);
  require(
      initial_state.phase != protocol::RoundPhase::aggregated &&
          initial_state.phase != protocol::RoundPhase::aborted,
      "type-5 initial state is terminal and cannot accept commitments");
  require(
      operation_count <=
          std::numeric_limits<std::uint64_t>::max() - initial_state.durable_sequence,
      "operation count would overflow the durable transition sequence");
  require(
      operation_count <= std::numeric_limits<std::uint32_t>::max(),
      "operation count exceeds the canonical ticket-count width");
  require(
      initial_state.committed_ticket_count == 0U &&
          initial_state.available_ticket_count == 0U,
      "golden initial state already contains ticket progress");
  initial_state.durable_sequence = 0U;
  initial_state.ticket_count = static_cast<std::uint32_t>(operation_count);
  initial_state.phase = protocol::RoundPhase::ticketing_open;
  const auto benchmark_initial_bytes = protocol::encode(initial_state);
  const auto initial_state_root = canonical::content_id(
      canonical::Type::round_state, benchmark_initial_bytes);

  CorpusWriter output(output_path);
  output.write(kCorpusMagic);
  output.write(encode_u16(kCorpusMajor));
  output.write(encode_u16(kCorpusMinor));
  output.write(encode_u64(operation_count));
  output.write(encode_u32(checked_u32(benchmark_initial_bytes.size(), "initial-state length")));
  output.write(benchmark_initial_bytes);

  Sha256 command_transcript_hash;
  Sha256 ticket_mapping_hash;
  Sha256 execution_binding_hash;
  std::string projected_events;
  auto projected_state = benchmark_initial_bytes;
  if (projection.has_value()) {
    hash_ascii(ticket_mapping_hash, kTicketMappingDomain);
    ticket_mapping_hash.update(std::array{std::byte{0}});
    hash_array(ticket_mapping_hash, encode_u64(operation_count));
    hash_ascii(execution_binding_hash, kExecutionBindingDomain);
    execution_binding_hash.update(std::array{std::byte{0}});
    hash_array(execution_binding_hash, encode_u64(operation_count));
    projected_events.reserve(static_cast<std::size_t>(operation_count) * 768U);
    require(
        initial_state.round_id == "round-003-fixture",
        "golden state round ID differs from the accepted native round contract");
  }
  for (std::uint64_t ordinal = 0U; ordinal < operation_count; ++ordinal) {
    const auto command = command_for(initial_state, ordinal);
    const auto ordinal_bytes = encode_u64(ordinal);
    const auto command_length = encode_u32(checked_u32(command.size(), "command length"));
    const auto command_hash = sha256(command);

    output.write(ordinal_bytes);
    output.write(command_length);
    output.write(command);
    output.write(command_hash);

    command_transcript_hash.update(ordinal_bytes);
    command_transcript_hash.update(command_length);
    command_transcript_hash.update(command);
    command_transcript_hash.update(command_hash);

    if (projection.has_value()) {
      const auto decoded = protocol::parse_command(command);
      require(decoded.command_kind == "ACCEPT_COMMITMENT", "projected command kind changed");
      require(decoded.request_id == request_id(ordinal), "projected request ID changed");
      require(decoded.body_hash == commitment_id(ordinal), "projected commitment ID changed");
      require(
          decoded.round_id == initial_state.round_id && decoded.height == initial_state.height &&
              decoded.view == initial_state.view,
          "projected command context changed");

      hash_array(ticket_mapping_hash, ordinal_bytes);
      hash_length_prefixed_ascii(ticket_mapping_hash, decoded.request_id);
      hash_length_prefixed_ascii(ticket_mapping_hash, decoded.actor_id);
      hash_array(ticket_mapping_hash, encode_u64(0U));
      hash_array(ticket_mapping_hash, content_digest(decoded.body_hash));

      const auto transition = delta::core::transition::apply(projected_state, command);
      const auto durable_sequence = ordinal + 1U;
      require(
          transition.next_state.durable_sequence == durable_sequence,
          "native projection durable sequence changed");
      const auto event = formal_event(decoded, transition, durable_sequence);
      const auto event_hash = sha256(as_bytes(event));

      hash_array(execution_binding_hash, ordinal_bytes);
      hash_length_prefixed_ascii(execution_binding_hash, decoded.request_id);
      hash_array(execution_binding_hash, command_hash);
      hash_array(execution_binding_hash, encode_u32(0U));
      hash_array(execution_binding_hash, content_digest(transition.effect_batch_id));
      hash_array(execution_binding_hash, content_digest(transition.prior_state_id));
      hash_array(execution_binding_hash, content_digest(transition.next_state_id));
      hash_array(execution_binding_hash, encode_u64(durable_sequence));
      hash_array(execution_binding_hash, event_hash);

      if (ordinal != 0U) {
        projected_events.push_back(',');
      }
      projected_events += event;
      projected_state = transition.next_state_bytes;
    }
  }

  const auto file_hash = output.finish();
  const auto initial_hash = sha256(benchmark_initial_bytes);
  const auto transcript_hash = command_transcript_hash.digest();
  require(hex(initial_hash) == canonical::sha256_hex(benchmark_initial_bytes),
          "incremental SHA-256 disagrees with canonical implementation");

  if (projection.has_value()) {
    const auto terminal_state_root = canonical::content_id(
        canonical::Type::round_state, projected_state);
    std::ostringstream trace_output;
    trace_output << "{\"abstraction_version\":\"1.0.0\",\"events\":["
                 << projected_events << "],\"formal_semantics_id\":"
                 << json_string(protocol::formal_semantics_id)
                 << ",\"initial_state_root\":" << json_string(initial_state_root)
                 << ",\"round_contract\":" << kRoundContract
                 << ",\"schema_version\":\"1.0.0\",\"terminal_outcome\":\"IN_PROGRESS\""
                 << ",\"terminal_state_root\":" << json_string(terminal_state_root)
                 << ",\"trace_id\":\"TRACE-FEATURE010-SIDECAR-COMMIT-PREFIX\"}";
    const auto trace = trace_output.str();
    const auto trace_sha256 = "sha256:" + hex(sha256(as_bytes(trace)));
    const auto transcript_sha256 = "sha256:" + hex(transcript_hash);
    const auto ticket_mapping_sha256 = "sha256:" + hex(ticket_mapping_hash.digest());
    const auto execution_binding_sha256 = "sha256:" + hex(execution_binding_hash.digest());
    const auto witness = initial_abstraction_witness(
        initial_state,
        operation_count,
        initial_state_root,
        transcript_sha256,
        ticket_mapping_sha256);
    const auto witness_sha256 = "sha256:" + hex(sha256(as_bytes(witness)));

    std::ostringstream receipt_output;
    receipt_output << "{\"canonical_input_trace_sha256\":\"sha256:" << hex(file_hash)
                   << "\",\"deterministic_prefix\":{\"encoding\":"
                   << json_string(kPrefixEncoding)
                   << ",\"execution_binding_encoding\":"
                   << json_string(kExecutionBindingEncoding)
                   << ",\"execution_binding_sha256\":"
                   << json_string(execution_binding_sha256)
                   << ",\"first_ordinal\":0,\"last_ordinal\":"
                   << (operation_count - 1U) << ",\"operation_count\":" << operation_count
                   << ",\"request_transcript_sha256\":" << json_string(transcript_sha256)
                   << "},\"formal_semantics_id\":"
                   << json_string(protocol::formal_semantics_id)
                   << ",\"initial_abstraction_witness\":" << witness
                   << ",\"initial_abstraction_witness_sha256\":"
                   << json_string(witness_sha256) << ",\"projected_trace\":" << trace
                   << ",\"projected_trace_sha256\":" << json_string(trace_sha256)
                   << ",\"schema_version\":\"1.0.0\",\"source\":{\"commit\":"
                   << json_string(projection->source_commit) << ",\"tree\":"
                   << json_string(projection->source_tree)
                   << "},\"type_name\":\"FEATURE010_PROJECTED_FORMAL_TRACE_RECEIPT\"}";
    const auto receipt = receipt_output.str();
    require(
        receipt.find("\":sha256:") == std::string::npos,
        "projected receipt contains an unquoted SHA-256 identity");
    require(
        receipt.starts_with("{\"canonical_input_trace_sha256\":\"sha256:") &&
            receipt.ends_with(
                "\"type_name\":\"FEATURE010_PROJECTED_FORMAL_TRACE_RECEIPT\"}"),
        "projected receipt canonical envelope is malformed");
    write_text_file(projection->formal_trace_path, trace + "\n");
    write_text_file(projection->receipt_path, receipt + "\n");
  }

  std::cout << "{\"command_count\":" << operation_count
            << ",\"command_transcript_sha256\":" << json_string(hex(transcript_hash))
            << ",\"file_bytes\":" << output.bytes_written()
            << ",\"file_sha256\":" << json_string(hex(file_hash))
            << ",\"initial_state_sha256\":" << json_string(hex(initial_hash))
            << ",\"schema_version\":\"1.0.0\""
            << ",\"type_name\":\"DELTA_SIDECAR_BENCHMARK_TRACE\"}\n";
}

void self_test() {
  const canonical::Bytes empty;
  const std::string abc = "abc";
  require(
      hex(sha256(empty)) ==
          "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "empty SHA-256 self-test failed");
  require(
      hex(sha256(std::as_bytes(std::span(abc.data(), abc.size())))) ==
          "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
      "abc SHA-256 self-test failed");
  require(request_id(42U) == "sidecar-benchmark-00000000000000000042",
          "request-ID self-test failed");
  protocol::RoundState state{};
  state.height = 7U;
  state.round_id = "sidecar-self-test-round";
  state.view = 17U;
  state.ticket_count = 1'000U;
  constexpr std::uint64_t command_count = 1'000U;
  const auto first = protocol::parse_command(command_for(state, 0U));
  const auto last = protocol::parse_command(command_for(state, command_count - 1U));
  require(
      first.command_kind == "ACCEPT_COMMITMENT" && first.view == state.view &&
          first.request_id == request_id(0U),
      "first commitment command self-test failed");
  require(
      last.command_kind == "ACCEPT_COMMITMENT" && last.view == state.view &&
          last.request_id == request_id(command_count - 1U),
      "last commitment command self-test failed");
  require(
      first.body_hash != last.body_hash && first.body_hash == commitment_id(0U) &&
          last.body_hash == commitment_id(command_count - 1U),
      "commitment identity self-test failed");
  require(encode_u16(0x0102U) ==
              std::array<std::byte, 2>{std::byte{0x01}, std::byte{0x02}},
          "u16 big-endian self-test failed");
  require(encode_u32(0x01020304U) ==
              std::array<std::byte, 4>{
                  std::byte{0x01}, std::byte{0x02}, std::byte{0x03}, std::byte{0x04}},
          "u32 big-endian self-test failed");
  require(encode_u64(UINT64_C(0x0102030405060708)) ==
              std::array<std::byte, 8>{
                  std::byte{0x01}, std::byte{0x02}, std::byte{0x03}, std::byte{0x04},
                  std::byte{0x05}, std::byte{0x06}, std::byte{0x07}, std::byte{0x08}},
          "u64 big-endian self-test failed");
  std::cout << "{\"status\":\"PASS\","
               "\"type_name\":\"DELTA_SIDECAR_TRACE_GENERATOR_SELF_TEST\"}\n";
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc == 2 && std::string_view(argv[1]) == "--self-test") {
      self_test();
      return 0;
    }
    require(
        argc == 4 || argc == 8,
        "usage: sidecar_trace_generator <golden-fixture.json> <operation-count> <output.bin> [<source-commit> <source-tree> <formal-trace.json> <receipt.json>]");
    std::optional<ProjectionOutput> projection;
    if (argc == 8) {
      projection = ProjectionOutput{argv[4], argv[5], argv[6], argv[7]};
    }
    generate(argv[1], parse_count(argv[2]), argv[3], projection);
  } catch (const std::exception& error) {
    std::cerr << "sidecar trace generation failed: " << error.what() << '\n';
    return 1;
  }
  return 0;
}
