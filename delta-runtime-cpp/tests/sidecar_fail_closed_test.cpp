#include "fixture_support.hpp"

#include <delta/runtime/sidecar_protocol.hpp>
#include <delta/runtime/sidecar_server.hpp>

#include <delta/core/protocol.hpp>
#include <delta_abi.h>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <filesystem>
#include <fstream>
#include <functional>
#include <iostream>
#include <iterator>
#include <limits>
#include <span>
#include <sstream>
#include <streambuf>
#include <string>
#include <string_view>
#include <system_error>
#include <type_traits>
#include <utility>
#include <vector>

#if defined(_WIN32)
#define NOMINMAX
#include <Windows.h>
#include <fcntl.h>
#include <io.h>
#else
#include <fcntl.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#endif

namespace protocol = delta::core::protocol;
namespace sidecar = delta::runtime::sidecar;
namespace test = delta::test;

namespace {

constexpr int fail_closed_exit_code = 86;

template <typename Integer>
void append_be(sidecar::Bytes& output, Integer value) {
  static_assert(std::is_unsigned_v<Integer>);
  for (std::size_t offset = sizeof(Integer); offset != 0U; --offset) {
    const auto shift = static_cast<unsigned>((offset - 1U) * 8U);
    output.push_back(static_cast<std::byte>((value >> shift) & static_cast<Integer>(0xffU)));
  }
}

[[nodiscard]] sidecar::Bytes text_bytes(std::string_view text) {
  sidecar::Bytes result;
  result.reserve(text.size());
  for (const unsigned char value : text) {
    result.push_back(static_cast<std::byte>(value));
  }
  return result;
}

[[nodiscard]] std::string path_utf8(const std::filesystem::path& path) {
  const auto encoded = path.u8string();
  return {reinterpret_cast<const char*>(encoded.data()), encoded.size()};
}

[[nodiscard]] sidecar::Id128 id(std::uint8_t seed) {
  sidecar::Id128 result{};
  for (std::size_t index = 0U; index < result.size(); ++index) {
    result[index] = static_cast<std::byte>(seed + static_cast<std::uint8_t>(index));
  }
  return result;
}

[[nodiscard]] sidecar::Bytes nested_descriptor() {
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
  const std::array<std::string_view, 6> texts{
      descriptor.schema_version,
      descriptor.protocol_version,
      descriptor.formal_semantics_id,
      descriptor.build_id,
      descriptor.schema_set_id,
      descriptor.runtime_profile,
  };
  sidecar::Bytes result = text_bytes("DELTABI1");
  append_be(result, std::uint32_t{0U});
  append_be(result, descriptor.struct_size);
  append_be(result, descriptor.abi_major);
  append_be(result, descriptor.abi_minor);
  append_be(result, descriptor.feature_bits);
  for (const auto text : texts) {
    append_be(result, static_cast<std::uint32_t>(text.size()));
    const auto bytes = text_bytes(text);
    result.insert(result.end(), bytes.begin(), bytes.end());
  }
  const auto total = static_cast<std::uint32_t>(result.size());
  for (std::size_t index = 0U; index < 4U; ++index) {
    const auto shift = static_cast<unsigned>((3U - index) * 8U);
    result[8U + index] = static_cast<std::byte>((total >> shift) & 0xffU);
  }
  return result;
}

[[nodiscard]] sidecar::Frame request_frame(
    sidecar::MessageType type,
    const sidecar::Id128& session,
    std::uint64_t generation,
    std::uint8_t correlation_seed,
    std::uint64_t sequence,
    std::span<const sidecar::Field> fields) {
  return sidecar::Frame{
      type,
      sidecar::required_flags(type),
      session,
      generation,
      id(correlation_seed),
      sequence,
      sidecar::max_response_capacity,
      sidecar::encode_payload(type, fields),
  };
}

[[nodiscard]] sidecar::Frame hello(
    const sidecar::Id128& session,
    std::uint64_t generation,
    const std::filesystem::path& executable) {
  const auto descriptor = nested_descriptor();
  const std::vector<sidecar::Field> fields{
      sidecar::field_text(1U, sidecar::contract_name),
      sidecar::field_u16(2U, sidecar::ipc_major),
      sidecar::field_u16(3U, sidecar::ipc_minor),
      sidecar::field_digest(4U, sidecar::digest_from_identity(sidecar::canonical_encoding_id)),
      sidecar::field_digest(5U, sidecar::digest_from_identity(sidecar::frame_layout_sha256)),
      sidecar::field_digest(6U, sidecar::digest_from_identity(sidecar::payload_schema_sha256)),
      sidecar::field_digest(
          7U, sidecar::digest_from_identity(sidecar::message_type_table_sha256)),
      sidecar::field_digest(8U, sidecar::digest_from_identity(sidecar::flag_table_sha256)),
      sidecar::field_digest(9U, sidecar::digest_from_identity(sidecar::bounds_sha256)),
      sidecar::field_digest(
          10U, sidecar::digest_from_identity(sidecar::shared_memory_layout_sha256)),
      sidecar::field_id128(11U, session),
      sidecar::field_u64(12U, generation),
      sidecar::field_digest(13U, sidecar::sha256_file(executable)),
      sidecar::field_text(14U, DELTA_BUILD_ID),
      sidecar::field_u16(15U, 1U),
      sidecar::field_bytes(16U, descriptor),
      sidecar::field_digest(17U, sidecar::sha256(descriptor)),
  };
  return request_frame(
      sidecar::MessageType::client_hello, session, generation, 10U, 1U, fields);
}

[[nodiscard]] sidecar::Frame open_request(
    const sidecar::Id128& session,
    std::uint64_t generation,
    const std::filesystem::path& directory,
    std::span<const std::byte> initial_state) {
  const auto descriptor = nested_descriptor();
  const std::vector<sidecar::Field> operation{
      sidecar::field_u32(16U, sidecar::max_submission_capacity),
      sidecar::field_text(17U, path_utf8(directory)),
      sidecar::field_bytes(18U, initial_state),
      sidecar::field_digest(19U, sidecar::sha256(descriptor)),
  };
  std::vector<sidecar::Field> fields{
      sidecar::field_bytes(1U, text_bytes("open-io-fault")),
      sidecar::field_digest(
          2U, sidecar::request_digest(sidecar::MessageType::open_request, operation)),
  };
  fields.insert(fields.end(), operation.begin(), operation.end());
  return request_frame(
      sidecar::MessageType::open_request, session, generation, 11U, 2U, fields);
}

[[nodiscard]] sidecar::Frame submit_request(
    const sidecar::Id128& session,
    std::uint64_t generation,
    std::uint64_t sequence,
    std::uint8_t correlation_seed,
    std::string_view request_id,
    std::span<const std::byte> command) {
  const std::vector<sidecar::Field> operation{sidecar::field_bytes(16U, command)};
  const std::vector<sidecar::Field> fields{
      sidecar::field_bytes(1U, text_bytes(request_id)),
      sidecar::field_digest(
          2U, sidecar::request_digest(sidecar::MessageType::submit_request, operation)),
      operation.front(),
  };
  return request_frame(
      sidecar::MessageType::submit_request,
      session,
      generation,
      correlation_seed,
      sequence,
      fields);
}

void append_frame(std::string& output, const sidecar::Frame& frame) {
  const auto encoded = sidecar::encode_frame(frame);
  output.append(reinterpret_cast<const char*>(encoded.data()), encoded.size());
}

[[nodiscard]] std::vector<sidecar::Frame> decode_frames(std::span<const std::byte> bytes) {
  std::vector<sidecar::Frame> result;
  std::size_t offset = 0U;
  while (offset < bytes.size()) {
    test::expect(
        bytes.size() - offset >= sidecar::header_bytes,
        "sidecar emitted a truncated response header");
    std::uint64_t payload_size = 0U;
    for (std::size_t index = 68U; index < 76U; ++index) {
      payload_size =
          (payload_size << 8U) | std::to_integer<std::uint8_t>(bytes[offset + index]);
    }
    test::expect(
        payload_size <= std::numeric_limits<std::size_t>::max() - sidecar::header_bytes,
        "sidecar response length overflowed");
    const auto frame_size = sidecar::header_bytes + static_cast<std::size_t>(payload_size);
    test::expect(frame_size <= bytes.size() - offset, "sidecar emitted a truncated response");
    result.push_back(sidecar::decode_frame(bytes.subspan(offset, frame_size)));
    offset += frame_size;
  }
  return result;
}

[[nodiscard]] sidecar::Bytes file_bytes(const std::filesystem::path& path) {
  std::ifstream input(path, std::ios::binary);
  test::expect(input.good(), "cannot read child sidecar output");
  const std::vector<char> chars{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  sidecar::Bytes result;
  result.reserve(chars.size());
  for (const char value : chars) {
    result.push_back(static_cast<std::byte>(static_cast<unsigned char>(value)));
  }
  return result;
}

class SabotageInputBuffer final : public std::streambuf {
 public:
  SabotageInputBuffer(std::string input, std::size_t sabotage_offset, std::function<void()> sabotage)
      : input_(std::move(input)),
        sabotage_offset_(sabotage_offset),
        sabotage_(std::move(sabotage)) {}

 protected:
  std::streamsize xsgetn(char* destination, std::streamsize requested) override {
    trigger_if_needed();
    const auto remaining = input_.size() - position_;
    const auto bounded = static_cast<std::size_t>(std::min<std::streamsize>(
        requested, static_cast<std::streamsize>(remaining)));
    if (bounded != 0U) {
      std::memcpy(destination, input_.data() + position_, bounded);
      position_ += bounded;
    }
    return static_cast<std::streamsize>(bounded);
  }

  int_type underflow() override {
    trigger_if_needed();
    if (position_ == input_.size()) {
      return traits_type::eof();
    }
    return traits_type::to_int_type(input_[position_]);
  }

  int_type uflow() override {
    const auto value = underflow();
    if (!traits_type::eq_int_type(value, traits_type::eof())) {
      ++position_;
    }
    return value;
  }

 private:
  void trigger_if_needed() {
    if (!sabotaged_ && position_ >= sabotage_offset_) {
      sabotaged_ = true;
      sabotage_();
    }
  }

  std::string input_;
  std::size_t sabotage_offset_;
  std::function<void()> sabotage_;
  std::size_t position_ = 0U;
  bool sabotaged_ = false;
};

[[nodiscard]] sidecar::ServerConfig server_config(
    const sidecar::Id128& session,
    std::uint64_t generation,
    const std::filesystem::path& executable) {
  return sidecar::ServerConfig{
      session,
      generation,
      executable,
#if defined(DELTA_SIDECAR_QUALIFICATION_ENABLED)
      sidecar::FaultPoint::none,
#endif
  };
}

void install_wal_fault(const std::filesystem::path& directory) {
  const auto wal = directory / "runtime.wal";
  const auto saved = directory / "runtime.wal.saved";
  std::error_code error;
  std::filesystem::remove_all(saved, error);
  if (error) {
    std::_Exit(90);
  }
  std::filesystem::rename(wal, saved, error);
  if (error) {
    std::_Exit(91);
  }
  std::filesystem::create_directory(wal, error);
  if (error) {
    std::_Exit(92);
  }
}

[[nodiscard]] std::vector<sidecar::Bytes> commands(const sidecar::Bytes& initial) {
  const auto state = protocol::parse_round_state(initial);
  return {
      protocol::encode(test::command_for(
          state,
          "ACCEPT_COMMITMENT",
          "sidecar-io-first",
          "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")),
      protocol::encode(test::command_for(
          state,
          "ACCEPT_COMMITMENT",
          "sidecar-io-second",
          "sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb")),
  };
}

int run_fault_child(
    const std::filesystem::path& directory,
    const std::filesystem::path& executable) {
#if defined(_WIN32)
  test::expect(_setmode(_fileno(stdout), _O_BINARY) != -1,
               "cannot set child sidecar output to binary mode");
#endif
  const auto initial = test::golden(DELTA_GOLDEN_FIXTURE_PATH, 5U);
  const auto command_set = commands(initial);
  const auto session = id(21U);
  constexpr std::uint64_t generation = 1U;

  std::string input;
  append_frame(input, hello(session, generation, executable));
  append_frame(input, open_request(session, generation, directory, initial));
  append_frame(
      input,
      submit_request(
          session, generation, 3U, 12U, "sidecar-io-first", command_set.front()));
  const auto sabotage_offset = input.size();
  append_frame(
      input,
      submit_request(
          session, generation, 4U, 13U, "sidecar-io-second", command_set.back()));

  SabotageInputBuffer buffer(
      std::move(input), sabotage_offset, [&directory] { install_wal_fault(directory); });
  std::istream stream(&buffer);
  sidecar::Server server(server_config(session, generation, executable));
  return server.run(stream, std::cout);
}

#if defined(_WIN32)
[[nodiscard]] std::wstring quote_windows_argument(std::wstring_view argument) {
  std::wstring result{L"\""};
  result.append(argument);
  result.push_back(L'\"');
  return result;
}

[[nodiscard]] int spawn_fault_child(
    const std::filesystem::path& executable,
    const std::filesystem::path& directory,
    const std::filesystem::path& output_path) {
  SECURITY_ATTRIBUTES security{sizeof(SECURITY_ATTRIBUTES), nullptr, TRUE};
  const auto output = CreateFileW(
      output_path.c_str(),
      GENERIC_WRITE,
      FILE_SHARE_READ,
      &security,
      CREATE_ALWAYS,
      FILE_ATTRIBUTE_NORMAL,
      nullptr);
  test::expect(output != INVALID_HANDLE_VALUE, "cannot create child sidecar output file");
  STARTUPINFOW startup{};
  startup.cb = sizeof(startup);
  startup.dwFlags = STARTF_USESTDHANDLES;
  startup.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
  startup.hStdOutput = output;
  startup.hStdError = GetStdHandle(STD_ERROR_HANDLE);
  PROCESS_INFORMATION process{};
  auto command = quote_windows_argument(executable.native()) + L" --io-fault-child " +
                 quote_windows_argument(directory.native());
  std::vector<wchar_t> mutable_command(command.begin(), command.end());
  mutable_command.push_back(L'\0');
  const auto created = CreateProcessW(
      executable.c_str(),
      mutable_command.data(),
      nullptr,
      nullptr,
      TRUE,
      0U,
      nullptr,
      nullptr,
      &startup,
      &process);
  CloseHandle(output);
  test::expect(created != FALSE, "cannot start child sidecar process");
  test::expect(WaitForSingleObject(process.hProcess, 30'000U) == WAIT_OBJECT_0,
               "child sidecar did not terminate");
  DWORD exit_code = 0U;
  test::expect(GetExitCodeProcess(process.hProcess, &exit_code) != FALSE,
               "cannot read child sidecar exit code");
  CloseHandle(process.hThread);
  CloseHandle(process.hProcess);
  return static_cast<int>(exit_code);
}
#else
[[nodiscard]] int spawn_fault_child(
    const std::filesystem::path& executable,
    const std::filesystem::path& directory,
    const std::filesystem::path& output_path) {
  const auto pid = ::fork();
  test::expect(pid >= 0, "cannot fork child sidecar process");
  if (pid == 0) {
    const auto output = ::open(output_path.c_str(), O_WRONLY | O_CREAT | O_TRUNC, 0600);
    if (output < 0 || ::dup2(output, STDOUT_FILENO) < 0) {
      ::_exit(93);
    }
    ::close(output);
    const auto executable_text = executable.string();
    const auto directory_text = directory.string();
    ::execl(
        executable_text.c_str(),
        executable_text.c_str(),
        "--io-fault-child",
        directory_text.c_str(),
        static_cast<char*>(nullptr));
    ::_exit(94);
  }
  int status = 0;
  test::expect(::waitpid(pid, &status, 0) == pid, "cannot wait for child sidecar process");
  test::expect(WIFEXITED(status), "child sidecar did not exit normally");
  return WEXITSTATUS(status);
}
#endif

void restore_wal(const std::filesystem::path& directory) {
  const auto wal = directory / "runtime.wal";
  const auto saved = directory / "runtime.wal.saved";
  std::error_code error;
  std::filesystem::remove_all(wal, error);
  test::expect(!error, "cannot remove injected WAL fault path");
  std::filesystem::rename(saved, wal, error);
  test::expect(!error, "cannot restore durable WAL after injected I/O failure");
}

[[nodiscard]] std::vector<sidecar::Frame> run_server(
    const sidecar::Id128& session,
    std::uint64_t generation,
    const std::filesystem::path& executable,
    const std::string& input) {
  std::istringstream requests(input, std::ios::binary);
  std::ostringstream responses(std::ios::binary);
  {
    sidecar::Server server(server_config(session, generation, executable));
    test::expect(server.run(requests, responses) == 0, "sidecar test session did not finish cleanly");
  }
  const auto text = responses.str();
  return decode_frames(std::as_bytes(std::span(text.data(), text.size())));
}

void expect_not_admitted(const sidecar::Frame& frame, std::string_view context) {
  test::expect(frame.type == sidecar::MessageType::error_response,
               std::string(context) + " did not return ERROR_RESPONSE");
  const auto payload = sidecar::decode_payload(frame.payload);
  test::expect(sidecar::field_as_u8(payload.fields[2]) == 1U,
               std::string(context) + " was not NOT_ADMITTED_PROVEN");
  test::expect(sidecar::field_as_u64(payload.fields[3]) == 0U,
               std::string(context) + " exposed a native admission sequence");
}

void test_pre_wal_rejections_do_not_consume_admission(
    const std::filesystem::path& executable) {
  const auto directory = std::filesystem::absolute(
      test::fresh_directory("sidecar-pre-wal-admission"));
  const auto initial = test::golden(DELTA_GOLDEN_FIXTURE_PATH, 5U);
  const auto state = protocol::parse_round_state(initial);
  const auto transition_reject = protocol::encode(test::command_for(
      state,
      "ACCEPT_AVAILABILITY",
      "sidecar-transition-reject",
      "sha256:cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"));
  const auto durable_command = protocol::encode(test::command_for(
      state,
      "ACCEPT_COMMITMENT",
      "sidecar-admission-durable",
      "sha256:dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd"));
  const auto conflicting_command = protocol::encode(test::command_for(
      state,
      "ACCEPT_COMMITMENT",
      "sidecar-admission-durable",
      "sha256:eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"));

  const auto initial_session = id(81U);
  constexpr std::uint64_t initial_generation = 11U;
  std::string initial_input;
  append_frame(initial_input, hello(initial_session, initial_generation, executable));
  append_frame(
      initial_input,
      open_request(initial_session, initial_generation, directory, initial));
  append_frame(
      initial_input,
      submit_request(
          initial_session,
          initial_generation,
          3U,
          82U,
          "sidecar-transition-reject",
          transition_reject));
  append_frame(
      initial_input,
      submit_request(
          initial_session,
          initial_generation,
          4U,
          83U,
          "sidecar-transition-reject",
          transition_reject));
  append_frame(
      initial_input,
      submit_request(
          initial_session,
          initial_generation,
          5U,
          84U,
          "sidecar-admission-durable",
          durable_command));
  append_frame(
      initial_input,
      submit_request(
          initial_session,
          initial_generation,
          6U,
          85U,
          "sidecar-transition-reject",
          transition_reject));
  const auto initial_frames =
      run_server(initial_session, initial_generation, executable, initial_input);
  test::expect(initial_frames.size() == 6U, "pre-WAL rejection response count differs");
  expect_not_admitted(initial_frames[2], "transition rejection");
  expect_not_admitted(initial_frames[3], "exact transition rejection retry");
  test::expect(initial_frames[4].type == sidecar::MessageType::submit_response,
               "valid submit after rejection did not succeed");
  const auto durable_submit = sidecar::decode_payload(initial_frames[4].payload);
  test::expect(sidecar::field_as_u64(durable_submit.fields[3]) == 2U,
               "pre-WAL rejection consumed an admission sequence");
  test::expect(sidecar::field_as_u64(durable_submit.fields[8]) == 1U,
               "valid submit after rejection did not create durable sequence one");
  test::expect(initial_frames[5].type == sidecar::MessageType::submit_response,
               "exact rejected request did not succeed after its phase became valid");
  const auto later_retry = sidecar::decode_payload(initial_frames[5].payload);
  test::expect(sidecar::field_as_u64(later_retry.fields[3]) == 3U,
               "later exact retry did not receive the next admission sequence");
  test::expect(sidecar::field_as_u64(later_retry.fields[8]) == 2U,
               "later exact retry did not create durable sequence two");

  const auto conflict_session = id(101U);
  constexpr std::uint64_t conflict_generation = 12U;
  std::string conflict_input;
  append_frame(conflict_input, hello(conflict_session, conflict_generation, executable));
  append_frame(
      conflict_input,
      open_request(conflict_session, conflict_generation, directory, initial));
  append_frame(
      conflict_input,
      submit_request(
          conflict_session,
          conflict_generation,
          3U,
          102U,
          "sidecar-admission-durable",
          conflicting_command));
  append_frame(
      conflict_input,
      submit_request(
          conflict_session,
          conflict_generation,
          4U,
          103U,
          "sidecar-admission-durable",
          conflicting_command));
  const auto conflict_frames =
      run_server(conflict_session, conflict_generation, executable, conflict_input);
  test::expect(conflict_frames.size() == 4U, "request-conflict response count differs");
  expect_not_admitted(conflict_frames[2], "durable request conflict");
  expect_not_admitted(conflict_frames[3], "exact request-conflict retry");

  std::error_code error;
  const auto wal = directory / "runtime.wal";
  const auto wal_size_before_replay = std::filesystem::file_size(wal, error);
  test::expect(!error && wal_size_before_replay != 0U,
               "cannot measure WAL before exact durable replay");
  const auto replay_session = id(121U);
  constexpr std::uint64_t replay_generation = 13U;
  std::string replay_input;
  append_frame(replay_input, hello(replay_session, replay_generation, executable));
  append_frame(
      replay_input,
      open_request(replay_session, replay_generation, directory, initial));
  append_frame(
      replay_input,
      submit_request(
          replay_session,
          replay_generation,
          3U,
          122U,
          "sidecar-admission-durable",
          durable_command));
  const auto replay_frames =
      run_server(replay_session, replay_generation, executable, replay_input);
  test::expect(replay_frames.size() == 3U, "exact durable replay response count differs");
  test::expect(replay_frames[2].type == sidecar::MessageType::submit_response,
               "exact durable replay did not return SUBMIT_RESPONSE");
  const auto replay_submit = sidecar::decode_payload(replay_frames[2].payload);
  test::expect(sidecar::field_as_u64(replay_submit.fields[3]) == 2U,
               "request conflict consumed admission before exact durable replay");
  test::expect(sidecar::field_as_u64(replay_submit.fields[8]) == 1U,
               "exact durable replay changed journal sequence");
  test::expect(std::filesystem::file_size(wal, error) == wal_size_before_replay && !error,
               "exact durable replay appended a duplicate WAL entry");
}

void verify_recovery(
    const std::filesystem::path& directory,
    const std::filesystem::path& executable) {
  const auto initial = test::golden(DELTA_GOLDEN_FIXTURE_PATH, 5U);
  const auto command_set = commands(initial);
  const auto wal = directory / "runtime.wal";
  std::error_code error;
  const auto durable_size = std::filesystem::file_size(wal, error);
  test::expect(!error && durable_size != 0U, "cannot measure durable WAL before recovery");
  {
    std::ofstream torn(wal, std::ios::binary | std::ios::app);
    test::expect(torn.good(), "cannot append torn WAL tail");
    const std::array<char, 3> partial_magic{'D', 'E', 'L'};
    torn.write(partial_magic.data(), static_cast<std::streamsize>(partial_magic.size()));
    torn.close();
    test::expect(torn.good(), "cannot close torn WAL tail fixture");
  }
  test::expect(std::filesystem::file_size(wal, error) == durable_size + 3U && !error,
               "torn WAL tail fixture size differs");

  const auto recovery_session = id(41U);
  constexpr std::uint64_t recovery_generation = 2U;
  std::string recovery_input;
  append_frame(recovery_input, hello(recovery_session, recovery_generation, executable));
  append_frame(
      recovery_input,
      open_request(recovery_session, recovery_generation, directory, initial));
  std::istringstream recovery_requests(recovery_input, std::ios::binary);
  std::ostringstream recovery_responses(std::ios::binary);
  {
    sidecar::Server server(
        server_config(recovery_session, recovery_generation, executable));
    test::expect(server.run(recovery_requests, recovery_responses) == 0,
                 "recovery-only sidecar did not finish cleanly");
  }
  const auto recovery_text = recovery_responses.str();
  const auto recovery_bytes =
      std::as_bytes(std::span(recovery_text.data(), recovery_text.size()));
  const auto recovery_frames = decode_frames(recovery_bytes);
  test::expect(recovery_frames.size() == 2U, "recovery-only response count differs");
  test::expect(recovery_frames[1].type == sidecar::MessageType::open_response,
               "recovery-only sidecar did not answer OPEN");
  const auto recovery_open = sidecar::decode_payload(recovery_frames[1].payload);
  test::expect(sidecar::field_as_u64(recovery_open.fields[6]) == 1U,
               "OPEN admitted before recovering the exact durable sequence");
  test::expect(std::filesystem::file_size(wal, error) == durable_size && !error,
               "OPEN was exposed before torn WAL truncation completed");

  const auto retry_session = id(61U);
  constexpr std::uint64_t retry_generation = 3U;
  std::string retry_input;
  append_frame(retry_input, hello(retry_session, retry_generation, executable));
  append_frame(retry_input, open_request(retry_session, retry_generation, directory, initial));
  append_frame(
      retry_input,
      submit_request(
          retry_session,
          retry_generation,
          3U,
          62U,
          "sidecar-io-second",
          command_set.back()));
  std::istringstream retry_requests(retry_input, std::ios::binary);
  std::ostringstream retry_responses(std::ios::binary);
  {
    sidecar::Server server(server_config(retry_session, retry_generation, executable));
    test::expect(server.run(retry_requests, retry_responses) == 0,
                 "post-recovery sidecar did not finish cleanly");
  }
  const auto retry_text = retry_responses.str();
  const auto retry_bytes = std::as_bytes(std::span(retry_text.data(), retry_text.size()));
  const auto retry_frames = decode_frames(retry_bytes);
  test::expect(retry_frames.size() == 3U, "post-recovery response count differs");
  const auto retry_open = sidecar::decode_payload(retry_frames[1].payload);
  test::expect(sidecar::field_as_u64(retry_open.fields[6]) == 1U,
               "post-recovery OPEN durable sequence differs");
  test::expect(retry_frames[2].type == sidecar::MessageType::submit_response,
               "recovered sidecar did not admit retry after recovery");
  const auto retry_submit = sidecar::decode_payload(retry_frames[2].payload);
  test::expect(sidecar::field_as_u64(retry_submit.fields[8]) == 2U,
               "post-recovery submission did not extend the durable WAL exactly once");
}

void test_wal_io_failure_is_fail_closed(const std::filesystem::path& executable) {
  const auto directory = std::filesystem::absolute(
      test::fresh_directory("sidecar-fail-closed-wal-io"));
  const auto output = directory / "fault-child.out";
  const auto exit_code = spawn_fault_child(executable, directory, output);
  test::expect(exit_code == fail_closed_exit_code,
               "admitted WAL I/O failure did not kill the sidecar generation");

  const auto emitted = file_bytes(output);
  const auto frames = decode_frames(emitted);
  test::expect(frames.size() == 3U,
               "sidecar emitted a response for the admitted WAL I/O failure");
  test::expect(frames[0].type == sidecar::MessageType::server_descriptor,
               "child sidecar handshake response differs");
  test::expect(frames[1].type == sidecar::MessageType::open_response,
               "child sidecar OPEN response differs");
  test::expect(frames[2].type == sidecar::MessageType::submit_response,
               "child sidecar first durable submission response differs");

  restore_wal(directory);
  verify_recovery(directory, executable);
}

}  // namespace

int main(int argc, char** argv) {
  try {
    const auto executable = std::filesystem::absolute(argv[0]);
    if (argc == 3 && std::string_view(argv[1]) == "--io-fault-child") {
      return run_fault_child(std::filesystem::absolute(argv[2]), executable);
    }
    test::expect(argc == 1, "unexpected fail-closed test argument");
    test_wal_io_failure_is_fail_closed(executable);
    test_pre_wal_rejections_do_not_consume_admission(executable);
  } catch (const std::exception& error) {
    std::cerr << "sidecar fail-closed test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "sidecar fail-closed tests passed\n";
  return 0;
}
