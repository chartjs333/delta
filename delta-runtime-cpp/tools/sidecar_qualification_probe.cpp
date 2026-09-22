#include "sidecar_qualification_probe.h"
#include "sidecar_qualification_fsync_interposer.h"

#include <delta/runtime/runtime.hpp>

#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <filesystem>
#include <limits>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>

namespace {

using delta::core::canonical::Bytes;
using delta::runtime::CrashPoint;

struct SelectedCrashPoint {
  CrashPoint runtime_point;
  bool after_native_return;
};

[[nodiscard]] std::u8string absolute_wal_path(const std::filesystem::path& directory) {
  return std::filesystem::absolute(directory / "runtime.wal").lexically_normal().u8string();
}

void require_exact_pre_durability_interposer(const std::filesystem::path& directory) {
#if defined(__linux__)
  if (delta_sidecar_qualification_fsync_interposer_arm_v1 == nullptr) {
    throw std::invalid_argument("qualification fsync interposer is not loaded");
  }
  const auto wal_path = absolute_wal_path(directory);
  const auto* bytes = reinterpret_cast<const std::uint8_t*>(wal_path.data());
  if (delta_sidecar_qualification_fsync_interposer_arm_v1(bytes, wal_path.size()) != 1U) {
    throw std::invalid_argument(
        "qualification fsync interposer is not armed for this runtime.wal");
  }
#else
  static_cast<void>(directory);
  throw std::invalid_argument(
      "qualification after-append-before-durability cut requires Linux LD_PRELOAD");
#endif
}

[[nodiscard]] bool valid_utf8_without_nul(std::span<const std::uint8_t> value) noexcept {
  std::size_t offset = 0U;
  while (offset < value.size()) {
    const auto first = value[offset];
    std::uint32_t code_point = 0U;
    std::size_t width = 0U;
    if (first <= 0x7fU) {
      code_point = first;
      width = 1U;
    } else if (first >= 0xc2U && first <= 0xdfU) {
      code_point = first & 0x1fU;
      width = 2U;
    } else if (first >= 0xe0U && first <= 0xefU) {
      code_point = first & 0x0fU;
      width = 3U;
    } else if (first >= 0xf0U && first <= 0xf4U) {
      code_point = first & 0x07U;
      width = 4U;
    } else {
      return false;
    }
    if (value.size() - offset < width) {
      return false;
    }
    for (std::size_t index = 1U; index < width; ++index) {
      const auto continuation = value[offset + index];
      if ((continuation & 0xc0U) != 0x80U) {
        return false;
      }
      code_point = (code_point << 6U) | (continuation & 0x3fU);
    }
    if ((width == 2U && code_point < 0x80U) ||
        (width == 3U && code_point < 0x800U) ||
        (width == 4U && code_point < 0x10000U) || code_point > 0x10ffffU ||
        (code_point >= 0xd800U && code_point <= 0xdfffU) || code_point == 0U) {
      return false;
    }
    offset += width;
  }
  return true;
}

[[nodiscard]] std::size_t bounded_size(
    std::uint64_t size,
    std::uint64_t maximum,
    const char* label) {
  if (size == 0U || size > maximum || size > std::numeric_limits<std::size_t>::max()) {
    throw std::invalid_argument(label);
  }
  return static_cast<std::size_t>(size);
}

[[nodiscard]] Bytes bounded_bytes(
    const std::uint8_t* data,
    std::uint64_t size,
    const char* label) {
  const auto bounded = bounded_size(
      size, DELTA_SIDECAR_QUALIFICATION_MAX_CANONICAL_BYTES, label);
  if (data == nullptr) {
    throw std::invalid_argument(label);
  }
  const auto view = std::span(data, bounded);
  const auto bytes = std::as_bytes(view);
  return Bytes(bytes.begin(), bytes.end());
}

[[nodiscard]] std::filesystem::path bounded_directory(
    const std::uint8_t* data,
    std::uint64_t size) {
  const auto bounded = bounded_size(
      size, DELTA_SIDECAR_QUALIFICATION_MAX_DIRECTORY_UTF8_BYTES,
      "qualification durable-directory UTF-8 is out of bounds");
  if (data == nullptr) {
    throw std::invalid_argument("qualification durable-directory UTF-8 is null");
  }
  const auto view = std::span(data, bounded);
  if (!valid_utf8_without_nul(view)) {
    throw std::invalid_argument("qualification durable-directory text is not UTF-8");
  }
  const std::string text(reinterpret_cast<const char*>(data), bounded);
  std::u8string utf8;
  utf8.reserve(text.size());
  for (const unsigned char value : text) {
    utf8.push_back(static_cast<char8_t>(value));
  }
  return std::filesystem::path(std::move(utf8));
}

[[nodiscard]] SelectedCrashPoint select_crash_point(
    delta_sidecar_qualification_crash_point_t point,
    const std::filesystem::path& directory) {
  switch (point) {
    case DELTA_SIDECAR_QUALIFICATION_BEFORE_WAL_APPEND:
      return {CrashPoint::before_wal_append, false};
    case DELTA_SIDECAR_QUALIFICATION_DURING_WAL_APPEND:
      return {CrashPoint::during_wal_append, false};
    case DELTA_SIDECAR_QUALIFICATION_AFTER_APPEND_BEFORE_DURABILITY:
      require_exact_pre_durability_interposer(directory);
      return {CrashPoint::none, false};
    case DELTA_SIDECAR_QUALIFICATION_AFTER_DURABILITY_BEFORE_COMMIT:
      return {CrashPoint::after_durability_before_commit, false};
    case DELTA_SIDECAR_QUALIFICATION_AFTER_COMMIT_BEFORE_EFFECT_RETURN:
      return {CrashPoint::after_commit_before_effect_return, false};
    case DELTA_SIDECAR_QUALIFICATION_AFTER_EFFECT_COPY_BEFORE_RETURN:
      return {CrashPoint::after_effect_copy_before_return, false};
    case DELTA_SIDECAR_QUALIFICATION_AFTER_NATIVE_RETURN_BEFORE_JAVA_SEND:
      return {CrashPoint::none, true};
    default:
      throw std::invalid_argument("unknown qualification crash point");
  }
}

[[noreturn]] void exit_now(int code) noexcept { std::_Exit(code); }

}  // namespace

extern "C" void delta_sidecar_qualification_crash_v1(
    const std::uint8_t* directory_utf8,
    std::uint64_t directory_utf8_length,
    const std::uint8_t* initial_state,
    std::uint64_t initial_state_length,
    const std::uint8_t* canonical_command,
    std::uint64_t canonical_command_length,
    delta_sidecar_qualification_crash_point_t crash_point) noexcept {
  try {
    auto directory = bounded_directory(directory_utf8, directory_utf8_length);
    auto initial = bounded_bytes(
        initial_state, initial_state_length, "qualification initial state is out of bounds");
    auto command = bounded_bytes(
        canonical_command, canonical_command_length,
        "qualification canonical command is out of bounds");
    const auto selected = select_crash_point(crash_point, directory);
    delta::runtime::Runtime runtime(delta::runtime::Config{
        std::move(directory),
        std::move(initial),
        64U,
    });
    static_cast<void>(runtime.submit(std::move(command), selected.runtime_point));
    exit_now(selected.after_native_return ? 86 : 88);
  } catch (const delta::runtime::RuntimeError& error) {
    exit_now(error.code() == delta::runtime::ErrorCode::simulated_crash ? 86 : 87);
  } catch (...) {
    exit_now(87);
  }
}
