#pragma once

#include <delta/runtime/sidecar_protocol.hpp>
#include <delta/runtime/sidecar_directory_lock.hpp>
#include <delta/runtime/sidecar_shared_memory.hpp>

#include <cstdint>
#include <filesystem>
#include <iosfwd>
#include <memory>
#include <optional>
#include <string>
#include <string_view>

namespace delta::runtime::sidecar {

#if defined(DELTA_SIDECAR_QUALIFICATION_ENABLED)
enum class FaultPoint {
  none,
  before_wal_append,
  during_wal_append,
  after_wal_append_before_durability,
  after_durability_before_commit,
  after_commit_before_effect_return,
  after_effect_copy_before_return,
  after_native_return_before_response,
  during_ipc_response_frame,
  during_shared_memory_publication,
};
#endif

struct ServerConfig {
  Id128 session_id;
  std::uint64_t generation;
  std::filesystem::path executable;
#if defined(DELTA_SIDECAR_QUALIFICATION_ENABLED)
  FaultPoint fault_point = FaultPoint::none;
#endif
  std::optional<DurableDirectoryIdentity> expected_durable_identity;
  std::optional<std::filesystem::path> java_to_native_shared_memory;
  std::optional<std::filesystem::path> native_to_java_shared_memory;
  std::optional<SharedMemoryFileIdentity> java_to_native_shared_memory_identity;
  std::optional<SharedMemoryFileIdentity> native_to_java_shared_memory_identity;
};

class Server final {
 public:
  explicit Server(ServerConfig config);
  ~Server();

  Server(const Server&) = delete;
  Server& operator=(const Server&) = delete;
  Server(Server&&) = delete;
  Server& operator=(Server&&) = delete;

  [[nodiscard]] int run(std::istream& input, std::ostream& output);

 private:
  class Impl;
  std::unique_ptr<Impl> impl_;
};

[[nodiscard]] Id128 parse_id128_hex(std::string_view value);
#if defined(DELTA_SIDECAR_QUALIFICATION_ENABLED)
[[nodiscard]] FaultPoint parse_fault_point(std::string_view value);
#endif

}  // namespace delta::runtime::sidecar
