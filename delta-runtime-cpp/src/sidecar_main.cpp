#include <delta/runtime/sidecar_server.hpp>

#include <charconv>
#include <cstdint>
#include <filesystem>
#include <iostream>
#include <optional>
#include <string>
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

[[nodiscard]] std::uint64_t parse_u64(std::string_view text, const char* message) {
  std::uint64_t value = 0U;
  const auto result = std::from_chars(text.data(), text.data() + text.size(), value);
  if (text.empty() || result.ec != std::errc{} || result.ptr != text.data() + text.size()) {
    reject(message);
  }
  return value;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc == 2 && std::string_view(argv[1]) == "--probe-shm-atomic") {
#if !defined(_WIN32)
      if (sidecar::probe_shared_memory_atomic_abi()) {
        std::cout << "LOCK_FREE_INTERPROCESS_U32_BIG_ENDIAN\n";
        return 0;
      }
#endif
      return 3;
    }
    if (argc >= 2 &&
        std::string_view(argv[1]) == "--probe-mapped-shm-atomic") {
      if (argc != 13 || std::string_view(argv[3]) != "--region" ||
          std::string_view(argv[5]) != "--generation" ||
          std::string_view(argv[7]) != "--device" ||
          std::string_view(argv[9]) != "--inode" ||
          std::string_view(argv[11]) != "--slot") {
        reject(
            "usage: delta_runtime_sidecar --probe-mapped-shm-atomic <path> "
            "--region <1|2> --generation <u64> --device <u64> --inode <u64> "
            "--slot <u32>");
      }
      const auto region_value = parse_u64(argv[4], "SHM region must be 1 or 2");
      if (region_value != 1U && region_value != 2U) {
        reject("SHM region must be 1 or 2");
      }
      const auto slot = parse_u64(argv[12], "SHM slot must be an unsigned decimal integer");
      if (slot >= sidecar::shared_memory_slot_count) {
        reject("SHM slot is out of bounds");
      }
#if !defined(_WIN32)
      if (sidecar::probe_mapped_shared_memory_atomic_abi(
              std::filesystem::path(argv[2]),
              static_cast<sidecar::SharedMemoryRegionId>(region_value),
              parse_generation(argv[6]),
              sidecar::SharedMemoryFileIdentity{
                  parse_u64(argv[8], "SHM device must be an unsigned decimal integer"),
                  parse_u64(argv[10], "SHM inode must be an unsigned decimal integer"),
              },
              static_cast<std::uint32_t>(slot))) {
        std::cout << "LOCK_FREE_JAVA_NATIVE_MAP_SHARED_U32_BIG_ENDIAN\n";
        return 0;
      }
#endif
      return 3;
    }
    std::string_view session;
    std::string_view generation;
    std::string_view durable_device;
    std::string_view durable_inode;
    std::string_view java_to_native_shared_memory;
    std::string_view native_to_java_shared_memory;
    std::string_view java_to_native_shared_memory_device;
    std::string_view java_to_native_shared_memory_inode;
    std::string_view native_to_java_shared_memory_device;
    std::string_view native_to_java_shared_memory_inode;
#if defined(DELTA_SIDECAR_QUALIFICATION_ENABLED)
    auto fault = sidecar::FaultPoint::none;
#endif
    for (int index = 1; index < argc; ++index) {
      const std::string_view argument = argv[index];
      if (argument == "--session" && index + 1 < argc) {
        session = argv[++index];
      } else if (argument == "--generation" && index + 1 < argc) {
        generation = argv[++index];
      } else if (argument == "--durable-device" && index + 1 < argc) {
        durable_device = argv[++index];
      } else if (argument == "--durable-inode" && index + 1 < argc) {
        durable_inode = argv[++index];
      } else if (argument == "--java-to-native-shm" && index + 1 < argc) {
        java_to_native_shared_memory = argv[++index];
      } else if (argument == "--native-to-java-shm" && index + 1 < argc) {
        native_to_java_shared_memory = argv[++index];
      } else if (argument == "--java-to-native-shm-device" && index + 1 < argc) {
        java_to_native_shared_memory_device = argv[++index];
      } else if (argument == "--java-to-native-shm-inode" && index + 1 < argc) {
        java_to_native_shared_memory_inode = argv[++index];
      } else if (argument == "--native-to-java-shm-device" && index + 1 < argc) {
        native_to_java_shared_memory_device = argv[++index];
      } else if (argument == "--native-to-java-shm-inode" && index + 1 < argc) {
        native_to_java_shared_memory_inode = argv[++index];
#if defined(DELTA_SIDECAR_QUALIFICATION_ENABLED)
      } else if (argument == "--fault" && index + 1 < argc) {
        fault = sidecar::parse_fault_point(argv[++index]);
#endif
      } else {
#if defined(DELTA_SIDECAR_QUALIFICATION_ENABLED)
        reject("usage: delta_runtime_sidecar --session <hex128> --generation <u64> "
#if defined(_WIN32)
               "[--durable-device <u64> --durable-inode <u64>] "
#else
               "--durable-device <u64> --durable-inode <u64> "
#endif
               "[--java-to-native-shm <path> --native-to-java-shm <path>] "
               "[--java-to-native-shm-device <u64> --java-to-native-shm-inode <u64> "
               "--native-to-java-shm-device <u64> --native-to-java-shm-inode <u64>] "
               "[--fault <point>]");
#else
        reject("usage: delta_runtime_sidecar --session <hex128> --generation <u64> "
#if defined(_WIN32)
               "[--durable-device <u64> --durable-inode <u64>] "
#else
               "--durable-device <u64> --durable-inode <u64> "
#endif
               "[--java-to-native-shm <path> --native-to-java-shm <path>]");
#endif
      }
    }
    if (session.empty() || generation.empty()) {
      reject("session and generation are required");
    }
    if (durable_device.empty() != durable_inode.empty()) {
      reject("durable device and inode must be supplied together");
    }
#if !defined(_WIN32)
    if (durable_device.empty()) {
      reject("durable device and inode are required on POSIX");
    }
#endif
    if (java_to_native_shared_memory.empty() != native_to_java_shared_memory.empty()) {
      reject("both shared-memory region paths must be supplied together");
    }
    const auto shared_memory_identity_missing =
        java_to_native_shared_memory_device.empty() ||
        java_to_native_shared_memory_inode.empty() ||
        native_to_java_shared_memory_device.empty() ||
        native_to_java_shared_memory_inode.empty();
    const auto shared_memory_identity_any =
        !java_to_native_shared_memory_device.empty() ||
        !java_to_native_shared_memory_inode.empty() ||
        !native_to_java_shared_memory_device.empty() ||
        !native_to_java_shared_memory_inode.empty();
    if (java_to_native_shared_memory.empty() ? shared_memory_identity_any
                                             : shared_memory_identity_missing) {
      reject("shared-memory paths require all pinned device/inode identities");
    }
    std::optional<sidecar::DurableDirectoryIdentity> expected_durable_identity;
    if (!durable_device.empty()) {
      expected_durable_identity = sidecar::DurableDirectoryIdentity{
          parse_u64(durable_device, "durable device must be an unsigned decimal integer"),
          parse_u64(durable_inode, "durable inode must be an unsigned decimal integer"),
      };
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
        expected_durable_identity,
        java_to_native_shared_memory.empty()
            ? std::nullopt
            : std::optional<std::filesystem::path>(
                  std::string(java_to_native_shared_memory)),
        native_to_java_shared_memory.empty()
            ? std::nullopt
            : std::optional<std::filesystem::path>(
                  std::string(native_to_java_shared_memory)),
        java_to_native_shared_memory.empty()
            ? std::nullopt
            : std::optional<sidecar::SharedMemoryFileIdentity>(
                  sidecar::SharedMemoryFileIdentity{
                      parse_u64(
                          java_to_native_shared_memory_device,
                          "Java-to-native SHM device must be unsigned decimal"),
                      parse_u64(
                          java_to_native_shared_memory_inode,
                          "Java-to-native SHM inode must be unsigned decimal"),
                  }),
        native_to_java_shared_memory.empty()
            ? std::nullopt
            : std::optional<sidecar::SharedMemoryFileIdentity>(
                  sidecar::SharedMemoryFileIdentity{
                      parse_u64(
                          native_to_java_shared_memory_device,
                          "native-to-Java SHM device must be unsigned decimal"),
                      parse_u64(
                          native_to_java_shared_memory_inode,
                          "native-to-Java SHM inode must be unsigned decimal"),
                  }),
    });
    return server.run(std::cin, std::cout);
  } catch (const std::exception& error) {
    std::cerr << "delta_runtime_sidecar: " << error.what() << '\n';
    return 2;
  }
}
