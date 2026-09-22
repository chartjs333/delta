#include <delta/runtime/sidecar_server.hpp>

#include <delta/runtime/sidecar_directory_lock.hpp>

#include <delta/core/canonical.hpp>
#include <delta/core/consensus.hpp>
#include <delta/core/protocol.hpp>
#include <delta/core/transition.hpp>
#include <delta/runtime/runtime.hpp>
#include <delta_abi.h>

#if defined(DELTA_SIDECAR_QUALIFICATION_ENABLED)
#include "sidecar_qualification_fsync_interposer.h"
#endif

#include <algorithm>
#include <array>
#include <cstdlib>
#include <cstring>
#include <filesystem>
#include <istream>
#include <limits>
#include <map>
#include <memory>
#include <optional>
#include <ostream>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <type_traits>
#include <utility>
#include <vector>

namespace delta::runtime::sidecar {
namespace {

constexpr std::uint8_t admission_not_applicable = 0U;
constexpr std::uint8_t admission_not_admitted = 1U;
constexpr std::uint8_t admission_outcome_available = 2U;
constexpr std::uint8_t admission_outcome_unknown = 3U;
constexpr std::uint32_t native_status_unavailable = 0xffffffffU;
constexpr std::uint32_t local_frame_invalid = 1U;
constexpr std::uint32_t local_identity_mismatch = 2U;
constexpr std::uint32_t local_internal_transport = 6U;

[[noreturn]] void reject(const char* message) { throw std::invalid_argument(message); }

class LocalProtocolError final : public std::invalid_argument {
 public:
  LocalProtocolError(std::uint32_t local_error, const char* message)
      : std::invalid_argument(message), local_error_(local_error) {}

  [[nodiscard]] std::uint32_t local_error() const noexcept { return local_error_; }

 private:
  std::uint32_t local_error_;
};

void require(bool condition, const char* message) {
  if (!condition) {
    reject(message);
  }
}

void require_identity(bool condition, const char* message) {
  if (!condition) {
    throw LocalProtocolError(local_identity_mismatch, message);
  }
}

template <typename Integer>
void append_be(Bytes& output, Integer value) {
  static_assert(std::is_unsigned_v<Integer>);
  for (std::size_t offset = sizeof(Integer); offset != 0U; --offset) {
    const auto shift = static_cast<unsigned>((offset - 1U) * 8U);
    output.push_back(static_cast<std::byte>((value >> shift) & static_cast<Integer>(0xffU)));
  }
}

[[nodiscard]] std::uint64_t header_payload_length(std::span<const std::byte> header) {
  require(header.size() == header_bytes, "sidecar header has wrong size");
  std::uint64_t result = 0U;
  for (std::size_t index = 68U; index < 76U; ++index) {
    result = (result << 8U) | std::to_integer<std::uint8_t>(header[index]);
  }
  return result;
}

[[nodiscard]] std::optional<Frame> read_frame(std::istream& input) {
  std::array<std::byte, header_bytes> header{};
  input.read(reinterpret_cast<char*>(header.data()), static_cast<std::streamsize>(header.size()));
  const auto header_count = input.gcount();
  if (header_count == 0 && input.eof()) {
    return std::nullopt;
  }
  require(header_count == static_cast<std::streamsize>(header.size()), "truncated sidecar header");
  const auto payload_length = header_payload_length(header);
  require(payload_length != 0U && payload_length <= max_logical_payload_bytes,
          "sidecar payload length exceeds bound");
  require(payload_length <= std::numeric_limits<std::size_t>::max() - header.size(),
          "sidecar frame size overflow");
  Bytes encoded(header.begin(), header.end());
  encoded.resize(header.size() + static_cast<std::size_t>(payload_length));
  input.read(
      reinterpret_cast<char*>(encoded.data() + header.size()),
      static_cast<std::streamsize>(payload_length));
  require(input.gcount() == static_cast<std::streamsize>(payload_length), "truncated sidecar payload");
  return decode_frame(encoded);
}

void write_all(std::ostream& output, std::span<const std::byte> bytes) {
  output.write(reinterpret_cast<const char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
  output.flush();
  require(output.good(), "sidecar response write failed");
}

[[nodiscard]] std::string byte_key(std::span<const std::byte> bytes) {
  std::string result;
  result.reserve(bytes.size());
  for (const auto value : bytes) {
    result.push_back(static_cast<char>(std::to_integer<unsigned char>(value)));
  }
  return result;
}

[[nodiscard]] Bytes text_bytes(std::string_view text) {
  Bytes result;
  result.reserve(text.size());
  for (const char value : text) {
    result.push_back(static_cast<std::byte>(static_cast<unsigned char>(value)));
  }
  return result;
}

[[nodiscard]] std::string safe_detail(std::string_view detail) {
  std::string result;
  result.reserve(std::min<std::size_t>(detail.size(), 512U));
  for (const unsigned char value : detail) {
    if (result.size() == 512U) {
      break;
    }
    result.push_back(value >= 0x20U && value <= 0x7eU ? static_cast<char>(value) : '?');
  }
  return result;
}

[[nodiscard]] std::filesystem::path utf8_path(std::string_view text) {
  std::u8string encoded;
  encoded.reserve(text.size());
  for (const char value : text) {
    encoded.push_back(static_cast<char8_t>(static_cast<unsigned char>(value)));
  }
  return std::filesystem::path(encoded);
}

[[nodiscard]] Bytes encode_nested_descriptor(const delta_runtime_descriptor_t& descriptor) {
  const std::array<std::string_view, 6> texts{
      descriptor.schema_version,
      descriptor.protocol_version,
      descriptor.formal_semantics_id,
      descriptor.build_id,
      descriptor.schema_set_id,
      descriptor.runtime_profile,
  };
  Bytes result;
  constexpr std::string_view magic = "DELTABI1";
  for (const char value : magic) {
    result.push_back(static_cast<std::byte>(static_cast<unsigned char>(value)));
  }
  append_be(result, std::uint32_t{0U});
  append_be(result, descriptor.struct_size);
  append_be(result, descriptor.abi_major);
  append_be(result, descriptor.abi_minor);
  append_be(result, descriptor.feature_bits);
  for (const auto text : texts) {
    require(!text.empty() && text.size() <= 256U, "nested ABI text field is out of bounds");
    append_be(result, static_cast<std::uint32_t>(text.size()));
    const auto bytes = text_bytes(text);
    result.insert(result.end(), bytes.begin(), bytes.end());
  }
  require(result.size() <= 2048U, "nested ABI descriptor exceeds bound");
  const auto total = static_cast<std::uint32_t>(result.size());
  for (std::size_t index = 0U; index < 4U; ++index) {
    const auto shift = static_cast<unsigned>((3U - index) * 8U);
    result[8U + index] = static_cast<std::byte>((total >> shift) & 0xffU);
  }
  return result;
}

[[nodiscard]] std::uint32_t map_runtime_error(ErrorCode code) noexcept {
  switch (code) {
    case ErrorCode::invalid_config:
      return DELTA_STATUS_INVALID_ARGUMENT;
    case ErrorCode::queue_full:
      return DELTA_STATUS_QUEUE_FULL;
    case ErrorCode::closed:
      return DELTA_STATUS_CLOSED;
    case ErrorCode::io_error:
      return DELTA_STATUS_IO_ERROR;
    case ErrorCode::wal_corrupt:
    case ErrorCode::snapshot_corrupt:
    case ErrorCode::sequence_invalid:
    case ErrorCode::recovery_mismatch:
      return DELTA_STATUS_CORRUPT_DURABLE_STATE;
    case ErrorCode::request_conflict:
      return DELTA_STATUS_CONFLICT;
    case ErrorCode::simulated_crash:
      return DELTA_STATUS_INTERNAL_ERROR;
  }
  return DELTA_STATUS_INTERNAL_ERROR;
}

#if defined(DELTA_SIDECAR_QUALIFICATION_ENABLED)
[[nodiscard]] CrashPoint runtime_crash_point(FaultPoint point) noexcept {
  switch (point) {
    case FaultPoint::before_wal_append:
      return CrashPoint::before_wal_append;
    case FaultPoint::during_wal_append:
      return CrashPoint::during_wal_append;
    case FaultPoint::after_wal_append_before_durability:
      // The legacy core crash point stops before append. The exact
      // post-append/pre-fsync qualification cut is supplied by the guarded
      // Linux interposer and therefore submits without a core crash point.
      return CrashPoint::none;
    case FaultPoint::after_durability_before_commit:
      return CrashPoint::after_durability_before_commit;
    case FaultPoint::after_commit_before_effect_return:
      return CrashPoint::after_commit_before_effect_return;
    case FaultPoint::after_effect_copy_before_return:
      return CrashPoint::after_effect_copy_before_return;
    case FaultPoint::none:
    case FaultPoint::after_native_return_before_response:
    case FaultPoint::during_ipc_response_frame:
      return CrashPoint::none;
  }
  return CrashPoint::none;
}

void require_exact_pre_durability_interposer(const std::filesystem::path& directory) {
#if defined(__linux__)
  require(
      delta_sidecar_qualification_fsync_interposer_arm_v1 != nullptr,
      "qualification fsync interposer is not loaded");
  const auto wal_path = std::filesystem::absolute(directory / "runtime.wal")
                            .lexically_normal()
                            .u8string();
  const auto* bytes = reinterpret_cast<const std::uint8_t*>(wal_path.data());
  require(
      delta_sidecar_qualification_fsync_interposer_arm_v1(bytes, wal_path.size()) == 1U,
      "qualification fsync interposer is not armed for this runtime.wal");
#else
  static_cast<void>(directory);
  reject(
      "qualification after-append-before-durability cut requires Linux "
      "LD_PRELOAD and DELTA_BUILD_SIDECAR_QUALIFICATION");
#endif
}
#endif

[[nodiscard]] Digest state_root(std::span<const std::byte> state) {
  return digest_from_identity(core::canonical::content_id(core::canonical::Type::round_state, state));
}

struct CommonRequest {
  Bytes request_id;
  Digest digest;
};

}  // namespace

class Server::Impl final {
 public:
  explicit Impl(ServerConfig config) : config_(std::move(config)) {
    require(config_.generation != 0U, "zero sidecar generation");
    const auto all_zero = std::all_of(config_.session_id.begin(), config_.session_id.end(), [](std::byte value) {
      return value == std::byte{0};
    });
    require(!all_zero, "zero sidecar session ID");
    require(!config_.executable.empty(), "sidecar executable path is empty");
    const delta_runtime_descriptor_t descriptor{
        DELTA_ABI_DESCRIPTOR_SIZE,
        DELTA_ABI_MAJOR,
        DELTA_ABI_MINOR,
        DELTA_ABI_FEATURE_BITS,
        DELTA_SCHEMA_VERSION,
        DELTA_PROTOCOL_VERSION,
        DELTA_FORMAL_SEMANTICS_ID,
        DELTA_BUILD_ID,
        DELTA_SCHEMA_SET_ID,
        DELTA_RUNTIME_PROFILE,
    };
    nested_descriptor_ = encode_nested_descriptor(descriptor);
    nested_descriptor_digest_ = sha256(nested_descriptor_);
    executable_digest_ = sha256_file(config_.executable);
    build_id_ = descriptor.build_id;
  }

  [[nodiscard]] int run(std::istream& input, std::ostream& output) {
    while (true) {
      const auto request_optional = read_frame(input);
      if (!request_optional.has_value()) {
        return handshaken_ ? 0 : 2;
      }
      const auto& request = *request_optional;
      validate_transport(request);
      current_admission_sequence_ = 0U;
      Frame response{};
      try {
        response = !handshaken_ ? handle_hello(request) : handle_request(request);
      } catch (const std::exception& error) {
        if (current_admission_sequence_ != 0U || native_submit_outcome_uncertain_) {
          // Once dispatch has assigned native admission order, an unexpected
          // failure is conservatively outcome-unknown transport loss. Exiting
          // forces generation fencing and exact recovery/retry; it must never be
          // mislabeled as a pre-admission rejection.
          std::_Exit(86);
        }
        if (!handshaken_ || !is_request(request.type)) {
          throw;
        }
        response = error_response(
            request,
            {},
            sha256(Bytes{}),
            admission_not_admitted,
            0U,
            native_status_unavailable,
            local_frame_invalid,
            error.what());
      }
      const auto encoded = encode_frame(response);
#if defined(DELTA_SIDECAR_QUALIFICATION_ENABLED)
      if (crash_during_response_) {
        crash_during_response_ = false;
        const auto partial = std::max<std::size_t>(1U, encoded.size() / 2U);
        write_all(output, std::span<const std::byte>(encoded).first(partial));
        std::_Exit(87);
      }
#endif
      write_all(output, encoded);
      if (close_after_response_) {
        runtime_.reset();
        directory_lock_.reset();
        return 0;
      }
    }
  }

 private:
  void validate_transport(const Frame& request) {
    require(is_request(request.type), "sidecar received a non-request frame");
    require(request.session_id == config_.session_id, "sidecar session mismatch");
    require(request.generation == config_.generation, "sidecar generation mismatch");
    require(!client_sequence_exhausted_, "sidecar request sequence is exhausted");
    require(request.sequence == next_client_sequence_, "sidecar request sequence is not exact");
    if (next_client_sequence_ == std::numeric_limits<std::uint64_t>::max()) {
      client_sequence_exhausted_ = true;
    } else {
      ++next_client_sequence_;
    }
  }

  [[nodiscard]] std::vector<Field> descriptor_fields() const {
    return {
        field_text(1U, contract_name),
        field_u16(2U, ipc_major),
        field_u16(3U, ipc_minor),
        field_digest(4U, digest_from_identity(canonical_encoding_id)),
        field_digest(5U, digest_from_identity(frame_layout_sha256)),
        field_digest(6U, digest_from_identity(payload_schema_sha256)),
        field_digest(7U, digest_from_identity(message_type_table_sha256)),
        field_digest(8U, digest_from_identity(flag_table_sha256)),
        field_digest(9U, digest_from_identity(bounds_sha256)),
        field_digest(10U, digest_from_identity(shared_memory_layout_sha256)),
        field_id128(11U, config_.session_id),
        field_u64(12U, config_.generation),
        field_digest(13U, executable_digest_),
        field_text(14U, build_id_),
        field_u16(15U, 1U),
        field_bytes(16U, nested_descriptor_),
        field_digest(17U, nested_descriptor_digest_),
    };
  }

  [[nodiscard]] Frame handle_hello(const Frame& request) {
    require(request.type == MessageType::client_hello, "first frame is not CLIENT_HELLO");
    const auto payload = decode_payload(request.payload);
    const auto expected = descriptor_fields();
    require(payload.fields == expected, "CLIENT_HELLO identity mismatch");
    handshaken_ = true;
    return response_frame(request, MessageType::server_descriptor, expected);
  }

  [[nodiscard]] CommonRequest validate_common(const Payload& payload, std::size_t expected_fields) {
    require(payload.fields.size() == expected_fields, "operation field count mismatch");
    const auto& request_id = require_field(payload, 0U, 1U, WireType::bytes, 1U, 256U);
    const auto& digest = require_field(payload, 1U, 2U, WireType::sha256, 32U, 32U);
    const auto expected_digest = request_digest(payload.type, payload.fields);
    require(field_as_digest(digest) == expected_digest, "request digest mismatch");
    return CommonRequest{request_id.value, expected_digest};
  }

  void bind_request_identity(MessageType type, const CommonRequest& common) {
    const auto key = byte_key(common.request_id);
    const auto existing = requests_.find(key);
    if (existing == requests_.end()) {
      requests_.emplace(key, std::pair{type, common.digest});
    } else {
      require_identity(
          existing->second.first == type && existing->second.second == common.digest,
          "request ID conflicts with a different operation or body");
    }
  }

  [[nodiscard]] Frame handle_request(const Frame& request) {
    require(request.type != MessageType::client_hello, "duplicate CLIENT_HELLO");
    const auto payload = decode_payload(request.payload);
    CommonRequest common{Bytes{}, sha256(Bytes{})};
    try {
      switch (request.type) {
        case MessageType::open_request:
          common = validate_common(payload, 6U);
          bind_request_identity(payload.type, common);
          return handle_open(request, payload, common);
        case MessageType::submit_request:
          common = validate_common(payload, 3U);
          bind_request_identity(payload.type, common);
          return handle_submit(request, payload, common);
        case MessageType::state_request:
          common = validate_common(payload, 3U);
          bind_request_identity(payload.type, common);
          return handle_state(request, payload, common);
        case MessageType::snapshot_request:
          common = validate_common(payload, 3U);
          bind_request_identity(payload.type, common);
          return handle_snapshot(request, payload, common);
        case MessageType::close_request:
          common = validate_common(payload, 4U);
          bind_request_identity(payload.type, common);
          return handle_close(request, payload, common);
        case MessageType::health_request:
          common = validate_common(payload, 3U);
          bind_request_identity(payload.type, common);
          return handle_health(request, payload, common);
        default:
          reject("operation is not supported by bounded-copy sidecar");
      }
    } catch (const RuntimeError& error) {
      // A request-conflict is computed before the WAL candidate is constructed.
      // Invalid configuration is also deterministic only when OPEN has not yet
      // assigned admission. Every other runtime failure can reflect lost
      // acceptance, failed durability, a stopped reactor, or unsafe recovery.
      // Terminate the generation without emitting a response so the supervisor
      // must recover the WAL and retry under a fresh generation fence.
      const auto request_conflict =
          current_admission_sequence_ == 0U && native_submit_outcome_uncertain_ &&
          error.code() == ErrorCode::request_conflict;
      const auto deterministic_rejection = request_conflict ||
          (current_admission_sequence_ == 0U && !native_submit_outcome_uncertain_ &&
           error.code() == ErrorCode::invalid_config);
      if (!deterministic_rejection) {
        std::_Exit(86);
      }
      if (request_conflict) {
        // Runtime checks the durable request cache before constructing a WAL
        // candidate, so this rejection cannot have mutated durable state.
        native_submit_outcome_uncertain_ = false;
      }
      return native_error(request, common, map_runtime_error(error.code()), error.what());
    } catch (const core::consensus::ConsensusError& error) {
      // Consensus validation completes before Runtime constructs/appends a WAL
      // candidate. It is therefore a proven NOT_ADMITTED rejection.
      if (current_admission_sequence_ != 0U) {
        throw;
      }
      native_submit_outcome_uncertain_ = false;
      return native_error(request, common, DELTA_STATUS_CONFLICT, error.what());
    } catch (const core::transition::TransitionError& error) {
      // Transition evaluation completes before Runtime constructs/appends a WAL
      // candidate. It is therefore a proven NOT_ADMITTED rejection.
      if (current_admission_sequence_ != 0U) {
        throw;
      }
      native_submit_outcome_uncertain_ = false;
      return native_error(request, common, DELTA_STATUS_TRANSITION_REJECTED, error.what());
    } catch (const core::protocol::ProtocolError& error) {
      if (current_admission_sequence_ != 0U || native_submit_outcome_uncertain_) {
        throw;
      }
      return native_error(request, common, DELTA_STATUS_INVALID_ARGUMENT, error.what());
    } catch (const core::canonical::DecodeError& error) {
      if (current_admission_sequence_ != 0U || native_submit_outcome_uncertain_) {
        throw;
      }
      return native_error(request, common, DELTA_STATUS_INVALID_ARGUMENT, error.what());
    } catch (const DurableDirectoryLockError& error) {
      return native_error(request, common, DELTA_STATUS_IO_ERROR, error.what());
    } catch (const LocalProtocolError& error) {
      if (current_admission_sequence_ != 0U || native_submit_outcome_uncertain_) {
        throw;
      }
      return not_admitted_error(request, common, error.local_error(), error.what());
    } catch (const std::invalid_argument& error) {
      if (current_admission_sequence_ != 0U || native_submit_outcome_uncertain_) {
        throw;
      }
      return not_admitted_error(request, common, error.what());
    }
  }

  [[nodiscard]] Frame handle_open(
      const Frame& request,
      const Payload& payload,
      const CommonRequest& common) {
    require(runtime_ == nullptr && directory_lock_ == nullptr, "runtime is already open");
    const auto capacity = field_as_u32(require_field(payload, 2U, 16U, WireType::u32_be, 4U, 4U));
    require(capacity == max_submission_capacity, "submission capacity differs from frozen bound");
    const auto directory_text = field_as_text(
        require_field(payload, 3U, 17U, WireType::canonical_utf8, 1U, 4096U));
    const auto& initial_state = require_field(
        payload, 4U, 18U, WireType::bytes, 1U, static_cast<std::size_t>(max_command_bytes));
    const auto nested_hash = field_as_digest(
        require_field(payload, 5U, 19U, WireType::sha256, 32U, 32U));
    require_identity(
        nested_hash == nested_descriptor_digest_,
        "OPEN nested ABI descriptor mismatch");
    const auto directory = utf8_path(directory_text);
    auto candidate_lock = std::make_unique<DurableDirectoryLock>(directory);
    candidate_lock->prepare_runtime_wal();
    auto candidate_runtime = std::make_unique<Runtime>(Config{
        directory,
        initial_state.value,
        max_submission_capacity,
    });
    // Recovery may truncate a torn WAL tail. Re-run the sidecar-owned file and
    // directory durability barrier before assigning OPEN admission or exposing
    // READY so a replacement process can rely on the repaired durable prefix.
    try {
      candidate_lock->prepare_runtime_wal();
    } catch (const DurableDirectoryLockError&) {
      // A failed post-recovery barrier leaves the recovery mutation's
      // durability uncertain. Do not answer or reuse this generation.
      std::_Exit(86);
    }
    const auto candidate_instance_id = make_runtime_instance_id(directory_text);
    const auto state = candidate_runtime->state_bytes();
    const auto durable_sequence = candidate_runtime->journal_sequence();
    const auto admission_sequence = assign_admission();
    directory_lock_ = std::move(candidate_lock);
    runtime_ = std::move(candidate_runtime);
    runtime_directory_ = directory;
    runtime_instance_id_ = candidate_instance_id;
    const std::vector<Field> fields{
        field_bytes(1U, common.request_id),
        field_digest(2U, common.digest),
        field_u8(3U, admission_outcome_available),
        field_u64(4U, admission_sequence),
        field_u32(5U, DELTA_STATUS_OK),
        field_id128(16U, runtime_instance_id_),
        field_u64(17U, durable_sequence),
        field_digest(18U, state_root(state)),
        field_u8(19U, 1U),
    };
    return response_frame(request, MessageType::open_response, fields);
  }

  [[nodiscard]] Frame handle_submit(
      const Frame& request,
      const Payload& payload,
      const CommonRequest& common) {
    require_ready();
    const auto& command = require_field(
        payload, 2U, 16U, WireType::bytes, 1U, static_cast<std::size_t>(max_command_bytes));
    const auto parsed_command = core::protocol::parse_command(command.value);
    require_identity(
        text_bytes(parsed_command.request_id) == common.request_id,
        "SUBMIT canonical request ID differs from the native command request ID");
#if defined(DELTA_SIDECAR_QUALIFICATION_ENABLED)
    const auto fault = fault_consumed_ ? FaultPoint::none : config_.fault_point;
    if (fault == FaultPoint::after_wal_append_before_durability) {
      // Validate the exact cut before assigning native admission. An unavailable
      // or mis-targeted interposer is a fail-closed qualification setup error,
      // never evidence that the requested crash point was reached.
      require_exact_pre_durability_interposer(runtime_directory_);
    }
    fault_consumed_ = fault != FaultPoint::none;
    native_submit_outcome_uncertain_ = true;
    const auto receipt = runtime_->submit(command.value, runtime_crash_point(fault));
#else
    native_submit_outcome_uncertain_ = true;
    const auto receipt = runtime_->submit(command.value);
#endif
    // Native parsing/transition/conflict rejection is pre-admission. Assign the
    // sidecar proof sequence only after Runtime returns a durable or exact-replay
    // receipt; otherwise a NOT_ADMITTED retry could later contradict the proof.
    const auto admission_sequence = assign_admission();
    native_submit_outcome_uncertain_ = false;
#if defined(DELTA_SIDECAR_QUALIFICATION_ENABLED)
    if (fault == FaultPoint::after_native_return_before_response) {
      std::_Exit(86);
    }
    if (fault == FaultPoint::during_ipc_response_frame) {
      crash_during_response_ = true;
    }
#endif
    if (receipt.effect_batch_bytes.size() > static_cast<std::size_t>(max_effect_bytes)) {
      close_after_response_ = true;
      return error_response(
          request,
          common.request_id,
          common.digest,
          admission_outcome_unknown,
          admission_sequence,
          native_status_unavailable,
          local_internal_transport,
          "native effect exceeds the frozen sidecar bound");
    }
    const auto wal_record = core::protocol::parse_wal_record(receipt.wal_record_bytes);
    require(
        wal_record.next_state_root == receipt.next_state_id,
        "native receipt and WAL next-state identities differ");
    const std::vector<Field> fields{
        field_bytes(1U, common.request_id),
        field_digest(2U, common.digest),
        field_u8(3U, admission_outcome_available),
        field_u64(4U, admission_sequence),
        field_u32(5U, DELTA_STATUS_OK),
        field_bytes(16U, text_bytes(receipt.effect_batch_id)),
        field_bytes(17U, receipt.effect_batch_bytes),
        field_digest(18U, sha256(receipt.effect_batch_bytes)),
        field_u64(19U, receipt.journal_sequence),
        field_digest(20U, digest_from_identity(wal_record.prior_state_root)),
        field_digest(21U, digest_from_identity(wal_record.next_state_root)),
    };
    return response_frame(request, MessageType::submit_response, fields);
  }

  [[nodiscard]] Frame handle_state(
      const Frame& request,
      const Payload& payload,
      const CommonRequest& common) {
    require_ready();
    validate_runtime_id(payload, 2U, 16U);
    const auto admission_sequence = assign_admission();
    const auto state = runtime_->state_bytes();
    const std::vector<Field> fields{
        field_bytes(1U, common.request_id),
        field_digest(2U, common.digest),
        field_u8(3U, admission_outcome_available),
        field_u64(4U, admission_sequence),
        field_u32(5U, DELTA_STATUS_OK),
        field_u64(16U, runtime_->journal_sequence()),
        field_digest(17U, state_root(state)),
        field_digest(18U, sha256(state)),
        field_bytes(19U, state),
    };
    return response_frame(request, MessageType::state_response, fields);
  }

  [[nodiscard]] Frame handle_snapshot(
      const Frame& request,
      const Payload& payload,
      const CommonRequest& common) {
    require_ready();
    validate_runtime_id(payload, 2U, 16U);
    const auto admission_sequence = assign_admission();
    runtime_->snapshot();
    const auto state = runtime_->state_bytes();
    const Bytes empty;
    const std::vector<Field> fields{
        field_bytes(1U, common.request_id),
        field_digest(2U, common.digest),
        field_u8(3U, admission_outcome_available),
        field_u64(4U, admission_sequence),
        field_u32(5U, DELTA_STATUS_OK),
        field_u64(16U, runtime_->journal_sequence()),
        field_digest(17U, state_root(state)),
        field_digest(18U, sha256(empty)),
        field_bytes(19U, empty),
    };
    return response_frame(request, MessageType::snapshot_response, fields);
  }

  [[nodiscard]] Frame handle_close(
      const Frame& request,
      const Payload& payload,
      const CommonRequest& common) {
    require_ready();
    validate_runtime_id(payload, 2U, 16U);
    const auto mode = field_as_u8(require_field(payload, 3U, 17U, WireType::u8, 1U, 1U));
    require(mode == 1U || mode == 2U, "unknown CLOSE mode");
    const auto state = runtime_->state_bytes();
    if (mode == 1U) {
      const auto parsed = core::protocol::parse_round_state(state);
      require(
          parsed.phase == core::protocol::RoundPhase::aggregated ||
              parsed.phase == core::protocol::RoundPhase::aborted,
          "DRAINED_TERMINAL_ONLY requires a terminal native state");
    }
    const auto admission_sequence = assign_admission();
    const auto durable_sequence = runtime_->journal_sequence();
    runtime_->close();
    close_after_response_ = true;
    const std::vector<Field> fields{
        field_bytes(1U, common.request_id),
        field_digest(2U, common.digest),
        field_u8(3U, admission_outcome_available),
        field_u64(4U, admission_sequence),
        field_u32(5U, DELTA_STATUS_OK),
        field_u64(16U, durable_sequence),
        field_digest(17U, state_root(state)),
        field_u8(18U, 1U),
    };
    return response_frame(request, MessageType::close_response, fields);
  }

  [[nodiscard]] Frame handle_health(
      const Frame& request,
      const Payload& payload,
      const CommonRequest& common) {
    const auto supplied = field_as_id128(require_field(payload, 2U, 16U, WireType::id128, 16U, 16U));
    const auto zero = std::all_of(supplied.begin(), supplied.end(), [](std::byte value) {
      return value == std::byte{0};
    });
    if (runtime_ != nullptr) {
      require_identity(supplied == runtime_instance_id_, "HEALTH runtime instance mismatch");
    } else {
      require_identity(zero, "pre-OPEN HEALTH requires zero runtime instance ID");
    }
    const auto ready = runtime_ != nullptr && runtime_->accepting();
    const std::vector<Field> fields{
        field_bytes(1U, common.request_id),
        field_digest(2U, common.digest),
        field_u8(3U, admission_not_applicable),
        field_u64(4U, 0U),
        field_u32(5U, DELTA_STATUS_OK),
        field_u8(16U, ready ? 2U : 0U),
        field_u64(17U, config_.generation),
        field_u64(18U, last_admitted_sequence_),
        field_u32(19U, 0U),
        field_u8(20U, directory_lock_ != nullptr ? 1U : 0U),
        field_u8(21U, ready ? 1U : 0U),
    };
    return response_frame(request, MessageType::health_response, fields);
  }

  void require_ready() const {
    require(runtime_ != nullptr && directory_lock_ != nullptr && runtime_->accepting(),
            "runtime is not READY");
  }

  void validate_runtime_id(const Payload& payload, std::size_t index, std::uint16_t id) const {
    const auto supplied = field_as_id128(require_field(payload, index, id, WireType::id128, 16U, 16U));
    require_identity(supplied == runtime_instance_id_, "runtime instance ID mismatch");
  }

  [[nodiscard]] Id128 make_runtime_instance_id(std::string_view directory) const {
    auto input = text_bytes("DELTA_SIDECAR_RUNTIME_INSTANCE_V1");
    input.insert(input.end(), config_.session_id.begin(), config_.session_id.end());
    append_be(input, config_.generation);
    const auto directory_bytes = text_bytes(directory);
    input.insert(input.end(), directory_bytes.begin(), directory_bytes.end());
    const auto digest = sha256(input);
    Id128 result{};
    std::copy_n(digest.begin(), result.size(), result.begin());
    return result;
  }

  [[nodiscard]] std::uint64_t assign_admission() {
    if (admission_sequence_exhausted_) {
      // Exhaustion permanently fences this generation. There is no reserved
      // value or wraparound and therefore no new arithmetic precondition.
      std::_Exit(86);
    }
    const auto admitted = next_admission_sequence_;
    last_admitted_sequence_ = admitted;
    current_admission_sequence_ = admitted;
    if (admitted == std::numeric_limits<std::uint64_t>::max()) {
      admission_sequence_exhausted_ = true;
    } else {
      ++next_admission_sequence_;
    }
    return admitted;
  }

  [[nodiscard]] Frame native_error(
      const Frame& request,
      const CommonRequest& common,
      std::uint32_t native_status,
      std::string_view detail) {
    if (current_admission_sequence_ == 0U) {
      return not_admitted_error(request, common, detail);
    }
    return error_response(
        request,
        common.request_id,
        common.digest,
        admission_outcome_available,
        current_admission_sequence_,
        native_status,
        local_internal_transport,
        detail);
  }

  [[nodiscard]] Frame not_admitted_error(
      const Frame& request,
      const CommonRequest& common,
      std::string_view detail) {
    return not_admitted_error(request, common, local_frame_invalid, detail);
  }

  [[nodiscard]] Frame not_admitted_error(
      const Frame& request,
      const CommonRequest& common,
      std::uint32_t local_error,
      std::string_view detail) {
    return error_response(
        request,
        common.request_id,
        common.digest,
        admission_not_admitted,
        0U,
        native_status_unavailable,
        local_error,
        detail);
  }

  [[nodiscard]] Frame error_response(
      const Frame& request,
      std::span<const std::byte> request_id,
      const Digest& digest,
      std::uint8_t admission_state,
      std::uint64_t admitted_sequence,
      std::uint32_t native_status,
      std::uint32_t local_error,
      std::string_view detail) {
    const auto bounded_detail = safe_detail(detail);
    const std::vector<Field> fields{
        field_bytes(1U, request_id),
        field_digest(2U, digest),
        field_u8(3U, admission_state),
        field_u64(4U, admitted_sequence),
        field_u32(5U, native_status),
        field_u32(16U, local_error),
        field_u16(17U, static_cast<std::uint16_t>(request.type)),
        field_u64(18U, max_response_capacity),
        field_text(19U, bounded_detail),
    };
    return response_frame(request, MessageType::error_response, fields);
  }

  [[nodiscard]] Frame response_frame(
      const Frame& request,
      MessageType type,
      std::span<const Field> fields) {
    require(!server_sequence_exhausted_, "sidecar response sequence is exhausted");
    const auto sequence = next_server_sequence_;
    if (next_server_sequence_ == std::numeric_limits<std::uint64_t>::max()) {
      server_sequence_exhausted_ = true;
    } else {
      ++next_server_sequence_;
    }
    return Frame{
        type,
        required_flags(type),
        config_.session_id,
        config_.generation,
        request.correlation_id,
        sequence,
        0U,
        encode_payload(type, fields),
    };
  }

  ServerConfig config_;
  Bytes nested_descriptor_;
  Digest nested_descriptor_digest_{};
  Digest executable_digest_{};
  std::string build_id_;
  bool handshaken_ = false;
  bool close_after_response_ = false;
#if defined(DELTA_SIDECAR_QUALIFICATION_ENABLED)
  bool fault_consumed_ = false;
  bool crash_during_response_ = false;
#endif
  bool admission_sequence_exhausted_ = false;
  bool client_sequence_exhausted_ = false;
  bool server_sequence_exhausted_ = false;
  bool native_submit_outcome_uncertain_ = false;
  std::uint64_t next_client_sequence_ = 1U;
  std::uint64_t next_server_sequence_ = 1U;
  std::uint64_t next_admission_sequence_ = 1U;
  std::uint64_t current_admission_sequence_ = 0U;
  std::uint64_t last_admitted_sequence_ = 0U;
  Id128 runtime_instance_id_{};
  std::filesystem::path runtime_directory_;
  std::map<std::string, std::pair<MessageType, Digest>> requests_;
  std::unique_ptr<DurableDirectoryLock> directory_lock_;
  std::unique_ptr<Runtime> runtime_;
};

Server::Server(ServerConfig config) : impl_(std::make_unique<Impl>(std::move(config))) {}
Server::~Server() = default;

int Server::run(std::istream& input, std::ostream& output) { return impl_->run(input, output); }

Id128 parse_id128_hex(std::string_view value) {
  require(value.size() == 32U, "session ID must be 32 lowercase hexadecimal characters");
  const auto nibble = [](char item) -> std::uint8_t {
    if (item >= '0' && item <= '9') {
      return static_cast<std::uint8_t>(item - '0');
    }
    if (item >= 'a' && item <= 'f') {
      return static_cast<std::uint8_t>(item - 'a' + 10);
    }
    reject("session ID is not lowercase hexadecimal");
  };
  Id128 result{};
  for (std::size_t index = 0U; index < result.size(); ++index) {
    result[index] = static_cast<std::byte>(
        static_cast<std::uint8_t>(nibble(value[index * 2U]) << 4U) |
        nibble(value[(index * 2U) + 1U]));
  }
  return result;
}

#if defined(DELTA_SIDECAR_QUALIFICATION_ENABLED)
FaultPoint parse_fault_point(std::string_view value) {
  if (value == "none") {
    return FaultPoint::none;
  }
  if (value == "before-wal-append") {
    return FaultPoint::before_wal_append;
  }
  if (value == "during-wal-append") {
    return FaultPoint::during_wal_append;
  }
  if (value == "after-append-before-durability") {
    return FaultPoint::after_wal_append_before_durability;
  }
  if (value == "after-durability-before-commit") {
    return FaultPoint::after_durability_before_commit;
  }
  if (value == "after-commit-before-effect-return") {
    return FaultPoint::after_commit_before_effect_return;
  }
  if (value == "after-effect-copy-before-return") {
    return FaultPoint::after_effect_copy_before_return;
  }
  if (value == "after-native-return-before-response") {
    return FaultPoint::after_native_return_before_response;
  }
  if (value == "during-ipc-response-frame") {
    return FaultPoint::during_ipc_response_frame;
  }
  reject("unknown sidecar fault point");
}
#endif

}  // namespace delta::runtime::sidecar
