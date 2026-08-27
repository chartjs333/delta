#include "sha256.hpp"

#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <vector>

namespace delta::core::detail {
namespace {

constexpr std::array<std::uint32_t, 64> round_constants = {
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

constexpr std::array<std::uint32_t, 8> initial_state = {
    0x6a09e667U,
    0xbb67ae85U,
    0x3c6ef372U,
    0xa54ff53aU,
    0x510e527fU,
    0x9b05688cU,
    0x1f83d9abU,
    0x5be0cd19U,
};

[[nodiscard]] constexpr std::uint32_t choose(
    std::uint32_t x, std::uint32_t y, std::uint32_t z) noexcept {
  return (x & y) ^ (~x & z);
}

[[nodiscard]] constexpr std::uint32_t majority(
    std::uint32_t x, std::uint32_t y, std::uint32_t z) noexcept {
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

[[nodiscard]] std::uint32_t load_u32(const std::byte* input) noexcept {
  return (static_cast<std::uint32_t>(std::to_integer<std::uint8_t>(input[0])) << 24U) |
         (static_cast<std::uint32_t>(std::to_integer<std::uint8_t>(input[1])) << 16U) |
         (static_cast<std::uint32_t>(std::to_integer<std::uint8_t>(input[2])) << 8U) |
         static_cast<std::uint32_t>(std::to_integer<std::uint8_t>(input[3]));
}

void transform(std::array<std::uint32_t, 8>& state, const std::byte* block) noexcept {
  std::array<std::uint32_t, 64> words{};
  for (std::size_t index = 0; index < 16; ++index) {
    words[index] = load_u32(block + (index * 4U));
  }
  for (std::size_t index = 16; index < words.size(); ++index) {
    words[index] = small_sigma1(words[index - 2U]) + words[index - 7U] +
                   small_sigma0(words[index - 15U]) + words[index - 16U];
  }

  auto a = state[0];
  auto b = state[1];
  auto c = state[2];
  auto d = state[3];
  auto e = state[4];
  auto f = state[5];
  auto g = state[6];
  auto h = state[7];

  for (std::size_t index = 0; index < words.size(); ++index) {
    const auto temporary1 =
        h + large_sigma1(e) + choose(e, f, g) + round_constants[index] + words[index];
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

  state[0] += a;
  state[1] += b;
  state[2] += c;
  state[3] += d;
  state[4] += e;
  state[5] += f;
  state[6] += g;
  state[7] += h;
}

}  // namespace

std::array<std::byte, 32> sha256(std::span<const std::byte> input) {
  if (input.size() > (std::numeric_limits<std::uint64_t>::max() / 8U)) {
    throw std::length_error("SHA-256 input length exceeds the 64-bit encoding");
  }
  const auto bit_length = static_cast<std::uint64_t>(input.size()) * 8U;
  std::vector<std::byte> message(input.begin(), input.end());
  message.push_back(std::byte{0x80});
  while ((message.size() % 64U) != 56U) {
    message.push_back(std::byte{0});
  }
  for (unsigned int shift = 56U;; shift -= 8U) {
    message.push_back(static_cast<std::byte>((bit_length >> shift) & 0xffU));
    if (shift == 0U) {
      break;
    }
  }

  auto state = initial_state;
  for (std::size_t offset = 0; offset < message.size(); offset += 64U) {
    transform(state, message.data() + offset);
  }

  std::array<std::byte, 32> digest{};
  for (std::size_t index = 0; index < state.size(); ++index) {
    const auto value = state[index];
    digest[(index * 4U)] = static_cast<std::byte>((value >> 24U) & 0xffU);
    digest[(index * 4U) + 1U] = static_cast<std::byte>((value >> 16U) & 0xffU);
    digest[(index * 4U) + 2U] = static_cast<std::byte>((value >> 8U) & 0xffU);
    digest[(index * 4U) + 3U] = static_cast<std::byte>(value & 0xffU);
  }
  return digest;
}

}  // namespace delta::core::detail
