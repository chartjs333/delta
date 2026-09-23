#include <delta/runtime/sidecar_shared_memory.hpp>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#if !defined(_WIN32)
#include <fcntl.h>
#include <sys/stat.h>
#include <unistd.h>
#endif

namespace {

namespace sidecar = delta::runtime::sidecar;

[[noreturn]] void fail(std::string message) {
  throw std::runtime_error(std::move(message));
}

void expect(bool condition, std::string_view message) {
  if (!condition) {
    fail(std::string(message));
  }
}

template <typename Operation>
void expect_shared_error(Operation operation, std::string_view label) {
  try {
    operation();
  } catch (const sidecar::SharedMemoryError&) {
    return;
  }
  fail(std::string(label));
}

#if !defined(_WIN32)
[[nodiscard]] std::filesystem::path fresh_root() {
  const auto root = std::filesystem::temp_directory_path() /
                    "delta-sidecar-shared-memory-tests" /
                    std::to_string(static_cast<unsigned long>(::getpid()));
  std::error_code error;
  std::filesystem::remove_all(root, error);
  expect(!error, "cannot clean shared-memory test root");
  std::filesystem::create_directories(root, error);
  expect(!error, "cannot create shared-memory test root");
  return root;
}

void create_sparse_region(const std::filesystem::path& path) {
  const auto descriptor = ::open(path.c_str(), O_RDWR | O_CREAT | O_EXCL, S_IRUSR | S_IWUSR);
  expect(descriptor >= 0, "cannot create sparse shared-memory region");
  const auto resized = ::ftruncate(
      descriptor, static_cast<off_t>(sidecar::shared_memory_region_bytes));
  const auto closed = ::close(descriptor);
  expect(resized == 0 && closed == 0, "cannot size sparse shared-memory region");
}

[[nodiscard]] sidecar::SharedMemoryFileIdentity file_identity(
    const std::filesystem::path& path) {
  struct stat status {};
  expect(::lstat(path.c_str(), &status) == 0 && S_ISREG(status.st_mode),
         "cannot stat shared-memory region");
  return sidecar::SharedMemoryFileIdentity{
      static_cast<std::uint64_t>(status.st_dev),
      static_cast<std::uint64_t>(status.st_ino),
  };
}

[[nodiscard]] std::array<std::byte, 4> raw_state(
    const std::filesystem::path& path, std::uint32_t slot) {
  std::ifstream input(path, std::ios::binary);
  expect(input.good(), "cannot read shared-memory control state");
  input.seekg(static_cast<std::streamoff>(
      static_cast<std::uint64_t>(slot) * sidecar::shared_memory_control_record_bytes));
  std::array<std::byte, 4> result{};
  input.read(reinterpret_cast<char*>(result.data()), 4);
  expect(input.gcount() == 4, "shared-memory control state is truncated");
  return result;
}

template <typename Integer>
void write_be(sidecar::Bytes& bytes, std::size_t offset, Integer value) {
  for (std::size_t index = 0U; index < sizeof(Integer); ++index) {
    const auto shift = static_cast<unsigned>((sizeof(Integer) - index - 1U) * 8U);
    bytes[offset + index] =
        static_cast<std::byte>((value >> shift) & static_cast<Integer>(0xffU));
  }
}

void prepare_atomic_probe_record(
    const std::filesystem::path& path,
    sidecar::SharedMemoryRegionId region,
    std::uint64_t generation,
    std::uint32_t slot) {
  sidecar::Bytes record(sidecar::shared_memory_control_record_bytes, std::byte{0});
  write_be(record, 0U, static_cast<std::uint32_t>(sidecar::SharedMemoryState::writing));
  write_be(record, 4U, static_cast<std::uint32_t>(region));
  write_be(record, 8U, generation);
  write_be(record, 16U, slot);
  std::fstream output(path, std::ios::binary | std::ios::in | std::ios::out);
  expect(output.good(), "cannot open mapped atomic probe record");
  output.seekp(static_cast<std::streamoff>(
      static_cast<std::uint64_t>(slot) * sidecar::shared_memory_control_record_bytes));
  output.write(
      reinterpret_cast<const char*>(record.data()),
      static_cast<std::streamsize>(record.size()));
  output.flush();
  expect(output.good(), "cannot write mapped atomic probe record");
}

void write_control_record(
    const std::filesystem::path& path,
    sidecar::SharedMemoryState state,
    sidecar::SharedMemoryRegionId region,
    std::uint64_t generation,
    std::uint32_t slot,
    std::uint64_t offset,
    std::uint64_t length) {
  sidecar::Bytes record(sidecar::shared_memory_control_record_bytes, std::byte{0});
  write_be(record, 0U, static_cast<std::uint32_t>(state));
  write_be(record, 4U, static_cast<std::uint32_t>(region));
  write_be(record, 8U, generation);
  write_be(record, 16U, slot);
  write_be(record, 24U, offset);
  write_be(record, 32U, length);
  std::fstream output(path, std::ios::binary | std::ios::in | std::ios::out);
  expect(output.good(), "cannot open shared-memory control record");
  output.seekp(static_cast<std::streamoff>(
      static_cast<std::uint64_t>(slot) * sidecar::shared_memory_control_record_bytes));
  output.write(
      reinterpret_cast<const char*>(record.data()),
      static_cast<std::streamsize>(record.size()));
  output.flush();
  expect(output.good(), "cannot write shared-memory control record");
}

[[nodiscard]] sidecar::Id128 id(std::uint8_t seed) {
  sidecar::Id128 result{};
  result.back() = static_cast<std::byte>(seed);
  return result;
}

[[nodiscard]] sidecar::Bytes submit_frame(
    std::uint64_t generation, std::uint64_t sequence, std::uint8_t correlation_seed) {
  const std::vector<sidecar::Field> operation{
      sidecar::field_bytes(16U, std::as_bytes(std::span("command", 7U))),
  };
  const auto digest = sidecar::request_digest(sidecar::MessageType::submit_request, operation);
  const std::vector<sidecar::Field> fields{
      sidecar::field_bytes(1U, std::as_bytes(std::span("request", 7U))),
      sidecar::field_digest(2U, digest),
      operation.front(),
  };
  return sidecar::encode_frame(sidecar::Frame{
      sidecar::MessageType::submit_request,
      sidecar::inline_flags(sidecar::MessageType::submit_request),
      id(1U),
      generation,
      id(correlation_seed),
      sequence,
      sidecar::max_response_capacity,
      sidecar::encode_payload(sidecar::MessageType::submit_request, fields),
  });
}

[[nodiscard]] sidecar::Bytes vote_frame(
    std::uint64_t generation, std::uint64_t sequence, std::uint8_t correlation_seed) {
  const std::vector<sidecar::Field> operation{
      sidecar::field_bytes(16U, std::as_bytes(std::span("opaque-vote", 11U))),
  };
  const auto digest = sidecar::request_digest(sidecar::MessageType::vote_request, operation);
  const std::vector<sidecar::Field> fields{
      sidecar::field_bytes(1U, std::as_bytes(std::span("vote-request", 12U))),
      sidecar::field_digest(2U, digest),
      operation.front(),
  };
  return sidecar::encode_frame(sidecar::Frame{
      sidecar::MessageType::vote_request,
      sidecar::inline_flags(sidecar::MessageType::vote_request),
      id(1U),
      generation,
      id(correlation_seed),
      sequence,
      sidecar::max_response_capacity,
      sidecar::encode_payload(sidecar::MessageType::vote_request, fields),
  });
}

void test_mapping_identity_and_fresh_prefix(const std::filesystem::path& root) {
  const auto identity_path = root / "identity.region";
  create_sparse_region(identity_path);
  const auto identity = file_identity(identity_path);
  auto wrong = identity;
  ++wrong.inode;
  expect_shared_error(
      [&] {
        sidecar::SharedMemoryRegion region(
            identity_path,
            sidecar::SharedMemoryRegionId::java_to_native,
            29U,
            wrong);
      },
      "shared-memory replacement identity was accepted");

  const auto stale_path = root / "stale-prefix.region";
  create_sparse_region(stale_path);
  {
    std::fstream output(stale_path, std::ios::binary | std::ios::in | std::ios::out);
    output.seekp(static_cast<std::streamoff>(17U * sidecar::shared_memory_control_record_bytes + 3U));
    output.put(static_cast<char>(sidecar::SharedMemoryState::published));
  }
  expect_shared_error(
      [&] {
        sidecar::SharedMemoryRegion region(
            stale_path,
            sidecar::SharedMemoryRegionId::java_to_native,
            29U,
            file_identity(stale_path));
      },
      "nonzero later shared-memory control slot was accepted");
}

void test_exact_mapped_atomic_probe(const std::filesystem::path& root) {
  constexpr std::uint64_t generation = 41U;
  constexpr std::uint32_t slot = 0U;
  const auto path = root / "mapped-atomic-probe.region";
  create_sparse_region(path);
  const auto identity = file_identity(path);
  prepare_atomic_probe_record(
      path, sidecar::SharedMemoryRegionId::java_to_native, generation, slot);

  auto wrong_identity = identity;
  ++wrong_identity.inode;
  expect(
      !sidecar::probe_mapped_shared_memory_atomic_abi(
          path,
          sidecar::SharedMemoryRegionId::java_to_native,
          generation,
          wrong_identity,
          slot),
      "mapped atomic probe accepted a stale file identity");
  expect(
      !sidecar::probe_mapped_shared_memory_atomic_abi(
          path,
          sidecar::SharedMemoryRegionId::java_to_native,
          generation + 1U,
          identity,
          slot),
      "mapped atomic probe accepted a stale generation");
  expect(
      raw_state(path, slot) ==
          std::array<std::byte, 4>{
              std::byte{0}, std::byte{0}, std::byte{0}, std::byte{1}},
      "rejected mapped atomic probe changed the Java WRITING state");
  expect(
      sidecar::probe_mapped_shared_memory_atomic_abi(
          path,
          sidecar::SharedMemoryRegionId::java_to_native,
          generation,
          identity,
          slot),
      "exact mapped Java/native atomic probe failed");
  expect(
      raw_state(path, slot) ==
          std::array<std::byte, 4>{
              std::byte{0}, std::byte{0}, std::byte{0}, std::byte{2}},
      "native mapped atomic probe did not publish raw big-endian state bytes");
}

void test_carrier_and_atomic_states(const std::filesystem::path& root) {
  const auto request_path = root / "java-to-native.region";
  const auto response_path = root / "native-to-java.region";
  create_sparse_region(request_path);
  create_sparse_region(response_path);
  sidecar::SharedMemoryRegion requests(
      request_path,
      sidecar::SharedMemoryRegionId::java_to_native,
      29U,
      file_identity(request_path));
  sidecar::SharedMemoryRegion responses(
      response_path,
      sidecar::SharedMemoryRegionId::native_to_java,
      29U,
      file_identity(response_path));
  expect(requests.atomic_abi_supported(), "shared-memory u32 atomic is not lock-free");

  const auto inline_frame = submit_frame(29U, 1U, 2U);
  const auto carrier = sidecar::make_shared_memory_carrier(inline_frame, requests).value();
  expect(raw_state(request_path, 0U) ==
             std::array<std::byte, 4>{std::byte{0}, std::byte{0}, std::byte{0}, std::byte{2}},
         "native PUBLISHED atomic bytes are not big-endian");

  auto stale_reference = carrier;
  write_be(stale_reference, sidecar::header_bytes + 8U, std::uint64_t{30U});
  expect_shared_error(
      [&] {
        static_cast<void>(sidecar::resolve_shared_memory_carrier(stale_reference, requests));
      },
      "stale shared-memory reference generation was accepted");
  auto stale_header = carrier;
  write_be(stale_header, 36U, std::uint64_t{30U});
  expect_shared_error(
      [&] {
        static_cast<void>(sidecar::resolve_shared_memory_carrier(stale_header, requests));
      },
      "header/reference shared-memory generation mismatch was accepted");
  expect_shared_error(
      [&] {
        static_cast<void>(sidecar::resolve_shared_memory_carrier(carrier, responses));
      },
      "wrong-direction shared-memory region was accepted");

  expect(sidecar::resolve_shared_memory_carrier(carrier, requests) == inline_frame,
         "shared-memory carrier did not reconstruct exact canonical inline bytes");
  expect(raw_state(request_path, 0U) ==
             std::array<std::byte, 4>{std::byte{0}, std::byte{0}, std::byte{0}, std::byte{4}},
         "native ACKED atomic bytes are not big-endian");
  const auto acknowledged_reference = sidecar::decode_shared_memory_reference(
      std::span<const std::byte>(carrier).subspan(sidecar::header_bytes));
  expect(requests.classify_terminal_notification(
             acknowledged_reference, sidecar::SharedMemoryDisposition::acknowledged) ==
             sidecar::SharedMemoryNotificationMatch::matched,
         "matching ACK notification was rejected");
  expect(requests.classify_terminal_notification(
             acknowledged_reference, sidecar::SharedMemoryDisposition::rejected_digest) ==
             sidecar::SharedMemoryNotificationMatch::mismatch,
         "ACK notification accepted a rejected disposition");
  auto wrong_digest = acknowledged_reference;
  wrong_digest.digest.front() ^= std::byte{1};
  expect(requests.classify_terminal_notification(
             wrong_digest, sidecar::SharedMemoryDisposition::acknowledged) ==
             sidecar::SharedMemoryNotificationMatch::reclaimed,
         "ACK notification accepted a mismatched reference digest");

  try {
    static_cast<void>(sidecar::make_shared_memory_carrier(
        inline_frame, requests, [] { throw std::runtime_error("publication hook"); }));
    fail("publication hook did not interrupt publication");
  } catch (const std::runtime_error& error) {
    expect(error.what() == std::string_view("publication hook"),
           "unexpected publication hook failure");
  }
  expect(raw_state(request_path, 0U) ==
             std::array<std::byte, 4>{std::byte{0}, std::byte{0}, std::byte{0}, std::byte{5}},
         "failed native publication stranded WRITING instead of REJECTED");

  const auto first = sidecar::make_shared_memory_carrier(inline_frame, requests).value();
  const auto second_inline = submit_frame(29U, 2U, 3U);
  const auto second = sidecar::make_shared_memory_carrier(second_inline, requests).value();
  const auto first_reference = sidecar::decode_shared_memory_reference(
      std::span<const std::byte>(first).subspan(sidecar::header_bytes));
  const auto second_reference = sidecar::decode_shared_memory_reference(
      std::span<const std::byte>(second).subspan(sidecar::header_bytes));
  expect(
      first_reference.offset + first_reference.length <= second_reference.offset ||
          second_reference.offset + second_reference.length <= first_reference.offset,
      "live native shared-memory ranges overlap");
  expect(sidecar::resolve_shared_memory_carrier(first, requests) == inline_frame &&
             sidecar::resolve_shared_memory_carrier(second, requests) == second_inline,
         "multiple live native slots changed canonical payload bytes");
  const auto third_inline = submit_frame(29U, 3U, 4U);
  static_cast<void>(sidecar::make_shared_memory_carrier(third_inline, requests).value());
  expect(
      requests.classify_terminal_notification(
          second_reference, sidecar::SharedMemoryDisposition::acknowledged) ==
          sidecar::SharedMemoryNotificationMatch::reclaimed,
      "reclaimed non-overwritten shared-memory reference retained ownership");

  const auto vote_inline = vote_frame(29U, 4U, 5U);
  const auto vote_carrier =
      sidecar::make_shared_memory_carrier(vote_inline, requests).value();
  expect(sidecar::resolve_shared_memory_carrier(vote_carrier, requests) == vote_inline,
         "opaque VOTE_REQUEST changed across the shared-memory carrier");

  sidecar::Bytes invalid_reference(sidecar::shared_memory_reference_bytes, std::byte{0});
  write_be(invalid_reference, 0U, std::uint32_t{1U});
  write_be(invalid_reference, 8U, std::uint64_t{29U});
  write_be(
      invalid_reference, 16U, sidecar::shared_memory_region_bytes - 1U);
  write_be(invalid_reference, 24U, std::uint64_t{2U});
  expect_shared_error(
      [&] { static_cast<void>(sidecar::decode_shared_memory_reference(invalid_reference)); },
      "out-of-bounds shared-memory reference was accepted");
}

void test_consumer_does_not_read_writing_peer_slot(
    const std::filesystem::path& root) {
  constexpr std::uint64_t generation = 43U;
  const auto path = root / "consumer-writing-peer.region";
  create_sparse_region(path);
  const auto identity = file_identity(path);
  sidecar::SharedMemoryRegion producer(
      path, sidecar::SharedMemoryRegionId::java_to_native, generation, identity);
  sidecar::SharedMemoryRegion consumer(
      path, sidecar::SharedMemoryRegionId::java_to_native, generation, identity);
  const auto inline_frame = submit_frame(generation, 1U, 7U);
  const auto carrier =
      sidecar::make_shared_memory_carrier(inline_frame, producer).value();

  // Simulate another producer paused after FREE -> WRITING and before any
  // metadata write. Resolving the published slot must not read that record.
  write_control_record(
      path,
      sidecar::SharedMemoryState::writing,
      sidecar::SharedMemoryRegionId::java_to_native,
      generation,
      1U,
      0U,
      0U);
  expect(sidecar::resolve_shared_memory_carrier(carrier, consumer) == inline_frame,
         "consumer read metadata from an unrelated WRITING slot");
}

void test_producer_rejects_nested_live_ranges(
    const std::filesystem::path& root) {
  constexpr std::uint64_t generation = 47U;
  const auto path = root / "nested-live-ranges.region";
  create_sparse_region(path);
  sidecar::SharedMemoryRegion producer(
      path,
      sidecar::SharedMemoryRegionId::java_to_native,
      generation,
      file_identity(path));
  write_control_record(
      path,
      sidecar::SharedMemoryState::published,
      sidecar::SharedMemoryRegionId::java_to_native,
      generation,
      0U,
      sidecar::shared_memory_control_prefix_bytes,
      256U);
  write_control_record(
      path,
      sidecar::SharedMemoryState::published,
      sidecar::SharedMemoryRegionId::java_to_native,
      generation,
      1U,
      sidecar::shared_memory_control_prefix_bytes + 64U,
      64U);
  const std::array payload{std::byte{1}};
  expect_shared_error(
      [&] { static_cast<void>(producer.publish(payload)); },
      "nested live shared-memory ranges were accepted");
}
#endif

}  // namespace

int main() {
  try {
#if !defined(_WIN32)
    expect(sidecar::probe_shared_memory_atomic_abi(),
           "cross-process MAP_SHARED atomic ABI probe failed");
    const auto root = fresh_root();
    test_exact_mapped_atomic_probe(root);
    test_mapping_identity_and_fresh_prefix(root);
    test_carrier_and_atomic_states(root);
    test_consumer_does_not_read_writing_peer_slot(root);
    test_producer_rejects_nested_live_ranges(root);
#else
    expect(!sidecar::probe_shared_memory_atomic_abi(),
           "Windows unexpectedly enabled the POSIX shared-memory atomic ABI");
#endif
  } catch (const std::exception& error) {
    std::cerr << "sidecar shared-memory test failed: " << error.what() << '\n';
    return 1;
  }
  std::cout << "sidecar shared-memory tests passed\n";
  return 0;
}
