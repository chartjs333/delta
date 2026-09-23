#include <delta/core/canonical.hpp>
#include <delta/runtime/runtime.hpp>

#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <limits>
#include <optional>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>

namespace {

using delta::core::canonical::Bytes;

constexpr std::uintmax_t max_canonical_bytes = 16U * 1024U * 1024U;

struct Arguments {
  std::filesystem::path directory;
  std::filesystem::path initial_state_file;
  std::optional<std::filesystem::path> retry_command_file;
};

[[noreturn]] void reject(const char* message) { throw std::invalid_argument(message); }

[[nodiscard]] Arguments parse_arguments(int argc, char** argv) {
  Arguments result;
  for (int index = 1; index < argc; ++index) {
    const std::string_view argument = argv[index];
    if (index + 1 >= argc) {
      reject("missing qualification inspector option value");
    }
    const std::filesystem::path value = argv[++index];
    if (argument == "--directory" && result.directory.empty()) {
      result.directory = value;
    } else if (argument == "--initial-state-file" && result.initial_state_file.empty()) {
      result.initial_state_file = value;
    } else if (argument == "--retry-command-file" && !result.retry_command_file.has_value()) {
      result.retry_command_file = value;
    } else {
      reject("unknown or repeated qualification inspector option");
    }
  }
  if (result.directory.empty() || result.initial_state_file.empty()) {
    reject(
        "usage: delta_sidecar_durable_inspector --directory PATH "
        "--initial-state-file FILE [--retry-command-file FILE]");
  }
  std::error_code error;
  if (!std::filesystem::is_directory(result.directory, error) || error) {
    reject("qualification durable directory does not exist or is not a directory");
  }
  return result;
}

[[nodiscard]] Bytes read_file(
    const std::filesystem::path& path,
    std::optional<std::uintmax_t> maximum,
    const char* label) {
  std::error_code error;
  const auto size = std::filesystem::file_size(path, error);
  if (error || size > std::numeric_limits<std::size_t>::max() ||
      size > static_cast<std::uintmax_t>(std::numeric_limits<std::streamsize>::max()) ||
      (maximum.has_value() && (size == 0U || size > *maximum))) {
    throw std::runtime_error(label);
  }
  std::ifstream input(path, std::ios::binary);
  if (!input.good()) {
    throw std::runtime_error(label);
  }
  Bytes result(static_cast<std::size_t>(size));
  if (!result.empty()) {
    input.read(
        reinterpret_cast<char*>(result.data()),
        static_cast<std::streamsize>(result.size()));
  }
  if (input.gcount() != static_cast<std::streamsize>(result.size()) ||
      input.peek() != std::char_traits<char>::eof()) {
    throw std::runtime_error(label);
  }
  return result;
}

[[nodiscard]] Bytes read_wal(const std::filesystem::path& directory) {
  const auto path = directory / "runtime.wal";
  std::error_code error;
  if (!std::filesystem::exists(path, error)) {
    if (error) {
      throw std::runtime_error("cannot inspect recovered runtime WAL");
    }
    return {};
  }
  return read_file(path, std::nullopt, "cannot inspect recovered runtime WAL");
}

[[nodiscard]] std::string sha256_identity(std::span<const std::byte> bytes) {
  return "sha256:" + delta::core::canonical::sha256_hex(bytes);
}

[[nodiscard]] std::string state_root(std::span<const std::byte> state) {
  return delta::core::canonical::content_id(delta::core::canonical::Type::round_state, state);
}

void emit_json(
    std::uint64_t recovered_sequence,
    std::span<const std::byte> recovered_state,
    std::span<const std::byte> wal,
    const std::optional<delta::runtime::SubmitReceipt>& retry) {
  std::cout << "{\"recovered_durable_sequence\":" << recovered_sequence
            << ",\"retry\":";
  if (!retry.has_value()) {
    std::cout << "null";
  } else {
    std::cout << "{\"durable_sequence\":" << retry->journal_sequence
              << ",\"effect_identity\":\"" << retry->effect_batch_id
              << "\",\"effect_sha256\":\"" << sha256_identity(retry->effect_batch_bytes)
              << "\",\"native_replay\":" << (retry->replay ? "true" : "false")
              << ",\"wal_receipt_identity\":\"" << retry->wal_record_id
              << "\",\"wal_receipt_sha256\":\"" << sha256_identity(retry->wal_record_bytes)
              << "\"}";
  }
  std::cout << ",\"schema_version\":\"1.0.0\""
            << ",\"state_bytes_sha256\":\"" << sha256_identity(recovered_state) << '"'
            << ",\"state_root\":\"" << state_root(recovered_state) << '"'
            << ",\"type_name\":\"DELTA_SIDECAR_DURABLE_INSPECTION\""
            << ",\"wal_sha256\":\"" << sha256_identity(wal) << '"'
            << ",\"wal_size_bytes\":" << wal.size() << "}\n";
}

}  // namespace

int main(int argc, char** argv) {
  try {
    const auto arguments = parse_arguments(argc, argv);
    auto initial_state = read_file(
        arguments.initial_state_file, max_canonical_bytes,
        "cannot read bounded qualification initial state");
    std::optional<Bytes> retry_command;
    if (arguments.retry_command_file.has_value()) {
      retry_command = read_file(
          *arguments.retry_command_file, max_canonical_bytes,
          "cannot read bounded qualification retry command");
    }

    std::uint64_t recovered_sequence = 0U;
    Bytes recovered_state;
    Bytes recovered_wal;
    std::optional<delta::runtime::SubmitReceipt> retry;
    {
      delta::runtime::Runtime runtime(delta::runtime::Config{
          .directory = arguments.directory,
          .initial_state_bytes = std::move(initial_state),
          .submission_capacity = 64U,
          .durable_binding_guard = {},
          .vote_policy = {},
          .expected_wal_identity = {},
      });
      // Runtime recovery may legitimately truncate a torn WAL tail before these
      // observations are captured; this inspector is not filesystem-read-only.
      recovered_sequence = runtime.journal_sequence();
      recovered_state = runtime.state_bytes();
      recovered_wal = read_wal(arguments.directory);
      if (retry_command.has_value()) {
        retry = runtime.submit(std::move(*retry_command));
      }
      runtime.close();
    }
    emit_json(recovered_sequence, recovered_state, recovered_wal, retry);
    return 0;
  } catch (const std::exception& error) {
    std::cerr << "delta_sidecar_durable_inspector: " << error.what() << '\n';
    return 2;
  }
}
