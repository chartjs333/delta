#include "fixture_support.hpp"
#include "sidecar_qualification_probe.h"

#include <delta/core/protocol.hpp>

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <limits>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>

namespace {

using delta::core::canonical::Bytes;

void write_bytes(const std::filesystem::path& path, std::span<const std::byte> bytes) {
  if (bytes.size() > static_cast<std::size_t>(std::numeric_limits<std::streamsize>::max())) {
    throw std::runtime_error("qualification smoke fixture is too large");
  }
  std::ofstream output(path, std::ios::binary | std::ios::trunc);
  if (!output.good()) {
    throw std::runtime_error("cannot create qualification smoke fixture");
  }
  output.write(
      reinterpret_cast<const char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
  if (!output.good()) {
    throw std::runtime_error("cannot write qualification smoke fixture");
  }
}

[[nodiscard]] Bytes command_for(const Bytes& initial_state) {
  const auto state = delta::core::protocol::parse_round_state(initial_state);
  return delta::core::protocol::encode(delta::core::protocol::Command{
      "validator-1",
      "sha256:abababababababababababababababababababababababababababababababab",
      "ACCEPT_COMMITMENT",
      state.height,
      10U,
      "qualification-after-append-before-durability",
      state.round_id,
      state.view,
  });
}

[[nodiscard]] std::span<const std::uint8_t> unsigned_bytes(const Bytes& bytes) noexcept {
  return {reinterpret_cast<const std::uint8_t*>(bytes.data()), bytes.size()};
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc != 2) {
      throw std::invalid_argument("usage: sidecar_qualification_interposer_smoke DIRECTORY");
    }
    const auto directory = std::filesystem::absolute(argv[1]).lexically_normal();
    std::filesystem::create_directories(directory);
    const auto initial_state = delta::test::golden(DELTA_GOLDEN_FIXTURE_PATH, 5U);
    const auto command = command_for(initial_state);
    write_bytes(directory / "qualification.initial", initial_state);
    write_bytes(directory / "qualification.command", command);

    const auto directory_utf8 = directory.u8string();
    delta_sidecar_qualification_crash_v1(
        reinterpret_cast<const std::uint8_t*>(directory_utf8.data()),
        directory_utf8.size(),
        unsigned_bytes(initial_state).data(),
        initial_state.size(),
        unsigned_bytes(command).data(),
        command.size(),
        DELTA_SIDECAR_QUALIFICATION_AFTER_APPEND_BEFORE_DURABILITY);
    return 89;
  } catch (...) {
    return 90;
  }
}
