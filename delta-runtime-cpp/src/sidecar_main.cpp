#include <delta/runtime/sidecar_server.hpp>

#include <charconv>
#include <cstdint>
#include <filesystem>
#include <iostream>
#include <stdexcept>
#include <string_view>

#if defined(_WIN32)
#include <fcntl.h>
#include <io.h>
#endif

namespace sidecar = delta::runtime::sidecar;

namespace {

[[noreturn]] void reject(const char* message) { throw std::invalid_argument(message); }

[[nodiscard]] std::uint64_t parse_generation(std::string_view text) {
  std::uint64_t value = 0U;
  const auto result = std::from_chars(text.data(), text.data() + text.size(), value);
  if (text.empty() || result.ec != std::errc{} || result.ptr != text.data() + text.size() || value == 0U) {
    reject("generation must be a nonzero unsigned decimal integer");
  }
  return value;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    std::string_view session;
    std::string_view generation;
#if defined(DELTA_SIDECAR_QUALIFICATION_ENABLED)
    auto fault = sidecar::FaultPoint::none;
#endif
    for (int index = 1; index < argc; ++index) {
      const std::string_view argument = argv[index];
      if (argument == "--session" && index + 1 < argc) {
        session = argv[++index];
      } else if (argument == "--generation" && index + 1 < argc) {
        generation = argv[++index];
#if defined(DELTA_SIDECAR_QUALIFICATION_ENABLED)
      } else if (argument == "--fault" && index + 1 < argc) {
        fault = sidecar::parse_fault_point(argv[++index]);
#endif
      } else {
#if defined(DELTA_SIDECAR_QUALIFICATION_ENABLED)
        reject("usage: delta_runtime_sidecar --session <hex128> --generation <u64> [--fault <point>]");
#else
        reject("usage: delta_runtime_sidecar --session <hex128> --generation <u64>");
#endif
      }
    }
    if (session.empty() || generation.empty()) {
      reject("session and generation are required");
    }
#if defined(_WIN32)
    if (_setmode(_fileno(stdin), _O_BINARY) == -1 || _setmode(_fileno(stdout), _O_BINARY) == -1) {
      reject("cannot set sidecar standard streams to binary mode");
    }
#endif
    std::ios::sync_with_stdio(false);
    sidecar::Server server(sidecar::ServerConfig{
        sidecar::parse_id128_hex(session),
        parse_generation(generation),
        std::filesystem::absolute(argv[0]),
#if defined(DELTA_SIDECAR_QUALIFICATION_ENABLED)
        fault,
#endif
    });
    return server.run(std::cin, std::cout);
  } catch (const std::exception& error) {
    std::cerr << "delta_runtime_sidecar: " << error.what() << '\n';
    return 2;
  }
}
