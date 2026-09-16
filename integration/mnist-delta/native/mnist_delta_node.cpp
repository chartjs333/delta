#include <delta/apply/engine.hpp>
#include <delta/certificates/verifier.hpp>
#include <delta/core/canonical.hpp>
#include <delta/core/consensus.hpp>
#include <delta/core/protocol.hpp>
#include <delta/robust/plan.hpp>
#include <delta/runtime/certificate_runtime.hpp>
#include <delta/runtime/runtime.hpp>

#include <algorithm>
#include <array>
#include <cstddef>
#include <cstdint>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <initializer_list>
#include <iostream>
#include <limits>
#include <map>
#include <memory>
#include <new>
#include <optional>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

#if defined(_WIN32)
#define NOMINMAX
#include <io.h>
#include <windows.h>
#else
#include <fcntl.h>
#include <unistd.h>
#endif

namespace {

namespace canonical = delta::core::canonical;
namespace consensus = delta::core::consensus;
namespace protocol = delta::core::protocol;
namespace certificates = delta::certificates;
namespace runtime = delta::runtime;

constexpr std::uint32_t workload_version = 2U;
constexpr std::uint32_t validator_count = 4U;
constexpr std::uint32_t quorum_threshold = 3U;
constexpr std::uint32_t pixel_coordinate_count = 10U * 28U * 28U;
constexpr std::uint32_t presence_coordinate_count = 10U;
constexpr std::uint32_t vector_width = pixel_coordinate_count + presence_coordinate_count;
constexpr std::size_t content_id_bytes = 71U;
constexpr std::size_t workload_header_bytes = 8U + 4U * sizeof(std::uint32_t) + content_id_bytes;
constexpr std::size_t workload_record_bytes =
    sizeof(std::uint32_t) + sizeof(std::uint64_t) + 2U * content_id_bytes +
    vector_width * sizeof(std::int16_t);
constexpr std::size_t exact_workload_bytes =
    workload_header_bytes + validator_count * workload_record_bytes;
constexpr std::size_t max_vote_frame_bytes = 64U * 1024U;
constexpr std::uint64_t max_samples_per_node = 60'000U;
constexpr int simulated_crash_exit_code = 75;

constexpr std::array<std::byte, 8U> workload_magic{
    std::byte{'D'},
    std::byte{'M'},
    std::byte{'N'},
    std::byte{'I'},
    std::byte{'S'},
    std::byte{'T'},
    std::byte{'2'},
    std::byte{0},
};

constexpr std::array<std::byte, 8U> model_magic{
    std::byte{'D'},
    std::byte{'M'},
    std::byte{'O'},
    std::byte{'D'},
    std::byte{'E'},
    std::byte{'L'},
    std::byte{'1'},
    std::byte{0},
};

const std::array<std::string, validator_count> validator_ids{
    "validator-01",
    "validator-02",
    "validator-03",
    "validator-04",
};

class DemoError final : public std::runtime_error {
 public:
  using std::runtime_error::runtime_error;
};

[[noreturn]] void fail(std::string message) { throw DemoError(std::move(message)); }

void require(bool condition, std::string message) {
  if (!condition) {
    fail(std::move(message));
  }
}

[[nodiscard]] std::vector<std::string> validators() {
  return {validator_ids.begin(), validator_ids.end()};
}

[[nodiscard]] bool known_validator(std::string_view value) {
  return std::binary_search(validator_ids.begin(), validator_ids.end(), value);
}

[[nodiscard]] std::string json_string(std::string_view value) {
  std::string output{"\""};
  for (const char character : value) {
    const auto byte = static_cast<unsigned char>(character);
    switch (character) {
      case '\"':
        output += "\\\"";
        break;
      case '\\':
        output += "\\\\";
        break;
      case '\b':
        output += "\\b";
        break;
      case '\f':
        output += "\\f";
        break;
      case '\n':
        output += "\\n";
        break;
      case '\r':
        output += "\\r";
        break;
      case '\t':
        output += "\\t";
        break;
      default:
        require(byte >= 0x20U && byte <= 0x7eU, "JSON value is outside canonical ASCII");
        output.push_back(character);
        break;
    }
  }
  output.push_back('\"');
  return output;
}

using JsonFields = std::vector<std::pair<std::string, std::string>>;

[[nodiscard]] std::string json_object(JsonFields fields) {
  std::sort(fields.begin(), fields.end(), [](const auto& left, const auto& right) {
    return left.first < right.first;
  });
  for (std::size_t index = 1U; index < fields.size(); ++index) {
    require(fields[index - 1U].first != fields[index].first, "duplicate JSON field");
  }
  std::string output{"{"};
  for (std::size_t index = 0U; index < fields.size(); ++index) {
    if (index != 0U) {
      output.push_back(',');
    }
    output += json_string(fields[index].first);
    output.push_back(':');
    output += fields[index].second;
  }
  output.push_back('}');
  return output;
}

[[nodiscard]] std::string json_array(const std::vector<std::string>& values) {
  std::string output{"["};
  for (std::size_t index = 0U; index < values.size(); ++index) {
    if (index != 0U) {
      output.push_back(',');
    }
    output += values[index];
  }
  output.push_back(']');
  return output;
}

[[nodiscard]] canonical::Bytes read_file(
    const std::filesystem::path& path,
    std::size_t maximum_bytes) {
  std::error_code error;
  const auto status = std::filesystem::symlink_status(path, error);
  require(
      !error && std::filesystem::is_regular_file(status) &&
          !std::filesystem::is_symlink(status),
      "input must be a regular non-symlink file: " + path.generic_string());
  const auto size = std::filesystem::file_size(path, error);
  require(!error, "cannot stat file: " + path.generic_string());
  require(size <= maximum_bytes, "file exceeds strict size bound: " + path.generic_string());
  require(
      size <= static_cast<std::uintmax_t>(std::numeric_limits<std::size_t>::max()),
      "file size cannot be represented");
  canonical::Bytes result(static_cast<std::size_t>(size));
  std::ifstream input(path, std::ios::binary);
  require(input.good(), "cannot open file: " + path.generic_string());
  if (!result.empty()) {
    input.read(reinterpret_cast<char*>(result.data()), static_cast<std::streamsize>(result.size()));
    require(
        input.gcount() == static_cast<std::streamsize>(result.size()),
        "short read: " + path.generic_string());
  }
  require(!input.bad(), "cannot finish reading file: " + path.generic_string());
  return result;
}

void require_plain_directory(const std::filesystem::path& path, std::string_view label) {
  std::error_code error;
  const auto status = std::filesystem::symlink_status(path, error);
  require(
      !error && std::filesystem::is_directory(status) &&
          !std::filesystem::is_symlink(status),
      std::string(label) + " must be a non-symlink directory: " + path.generic_string());
}

void sync_file_contents(const std::filesystem::path& path) {
#if defined(_WIN32)
  std::FILE* file = nullptr;
  const auto open_error = _wfopen_s(&file, path.c_str(), L"r+b");
  require(open_error == 0 && file != nullptr, "cannot reopen output for durability sync");
  const auto synced = _commit(_fileno(file));
  const auto closed = std::fclose(file);
  require(synced == 0 && closed == 0, "cannot durably sync output file");
#else
  const auto descriptor = ::open(path.c_str(), O_RDONLY | O_CLOEXEC | O_NOFOLLOW);
  require(descriptor >= 0, "cannot reopen output for durability sync");
  const auto synced = ::fsync(descriptor);
  const auto closed = ::close(descriptor);
  require(synced == 0 && closed == 0, "cannot durably sync output file");
#endif
}

void sync_directory_entry(const std::filesystem::path& directory) {
#if defined(_WIN32)
  // MoveFileExW(MOVEFILE_WRITE_THROUGH) below is the Windows durability
  // boundary for the renamed directory entry.
  static_cast<void>(directory);
#else
  const auto descriptor = ::open(directory.c_str(), O_RDONLY | O_CLOEXEC | O_DIRECTORY);
  require(descriptor >= 0, "cannot open output directory for durability sync");
  const auto synced = ::fsync(descriptor);
  const auto closed = ::close(descriptor);
  require(synced == 0 && closed == 0, "cannot durably sync output directory");
#endif
}

void replace_file_atomically(const std::filesystem::path& temporary, const std::filesystem::path& target) {
#if defined(_WIN32)
  const auto moved = MoveFileExW(
      temporary.c_str(),
      target.c_str(),
      MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH);
  require(moved != 0, "cannot atomically replace output: " + target.generic_string());
#else
  std::error_code error;
  std::filesystem::rename(temporary, target, error);
  require(!error, "cannot atomically replace output: " + target.generic_string());
#endif
}

void write_atomic(const std::filesystem::path& path, std::span<const std::byte> bytes) {
  const auto parent = path.parent_path();
  if (!parent.empty()) {
    std::filesystem::create_directories(parent);
    require_plain_directory(parent, "output parent");
  }
  std::error_code status_error;
  const auto target_status = std::filesystem::symlink_status(path, status_error);
  if (!status_error && std::filesystem::exists(target_status)) {
    require(
        std::filesystem::is_regular_file(target_status) &&
            !std::filesystem::is_symlink(target_status),
        "output target must be a regular non-symlink file");
  }
  auto temporary = path;
  temporary += ".tmp";
  status_error.clear();
  const auto temporary_status = std::filesystem::symlink_status(temporary, status_error);
  if (!status_error && std::filesystem::exists(temporary_status)) {
    require(
        std::filesystem::is_regular_file(temporary_status) &&
            !std::filesystem::is_symlink(temporary_status),
        "temporary output must be a regular non-symlink file");
    require(std::filesystem::remove(temporary), "cannot remove stale temporary output");
  }
  {
    std::ofstream output(temporary, std::ios::binary | std::ios::trunc);
    require(output.good(), "cannot create temporary output: " + temporary.generic_string());
    if (!bytes.empty()) {
      output.write(reinterpret_cast<const char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
    }
    output.flush();
    require(output.good(), "cannot flush temporary output: " + temporary.generic_string());
    output.close();
    require(!output.fail(), "cannot close temporary output: " + temporary.generic_string());
  }
  sync_file_contents(temporary);
  replace_file_atomically(temporary, path);
  if (!parent.empty()) {
    sync_directory_entry(parent);
  }
}

void write_atomic(const std::filesystem::path& path, std::string_view value) {
  const auto bytes = std::as_bytes(std::span(value.data(), value.size()));
  write_atomic(path, bytes);
}

[[nodiscard]] bool write_durable_once_or_verify(
    const std::filesystem::path& path,
    std::span<const std::byte> bytes) {
  std::error_code error;
  const auto status = std::filesystem::symlink_status(path, error);
  if (!error && std::filesystem::exists(status)) {
    require(
        std::filesystem::is_regular_file(status) && !std::filesystem::is_symlink(status),
        "durable artifact target must be a regular non-symlink file");
    const auto existing = read_file(path, bytes.size());
    require(
        existing.size() == bytes.size() &&
            std::equal(existing.begin(), existing.end(), bytes.begin(), bytes.end()),
        "durable artifact replay differs from existing canonical bytes");
    return true;
  }
  write_atomic(path, bytes);
  return false;
}

[[nodiscard]] std::string hash_bytes(std::span<const std::byte> bytes) {
  return "sha256:" + canonical::sha256_hex(bytes);
}

[[nodiscard]] std::string hash_file(const std::filesystem::path& path, std::size_t maximum_bytes) {
  const auto bytes = read_file(path, maximum_bytes);
  return hash_bytes(bytes);
}

void append_u64_be(canonical::Bytes& output, std::uint64_t value) {
  for (int shift = 56; shift >= 0; shift -= 8) {
    output.push_back(static_cast<std::byte>((value >> static_cast<unsigned>(shift)) & 0xffU));
  }
}

[[nodiscard]] std::string derived_id(
    std::string_view domain,
    std::span<const std::string> components) {
  canonical::Bytes bytes;
  for (const char character : domain) {
    bytes.push_back(static_cast<std::byte>(character));
  }
  bytes.push_back(std::byte{0});
  for (const auto& component : components) {
    append_u64_be(bytes, static_cast<std::uint64_t>(component.size()));
    for (const char character : component) {
      bytes.push_back(static_cast<std::byte>(character));
    }
  }
  return hash_bytes(bytes);
}

[[nodiscard]] std::string derived_id(
    std::string_view domain,
    std::initializer_list<std::string> components) {
  const std::vector<std::string> owned(components);
  return derived_id(domain, owned);
}

[[nodiscard]] std::string result_document(JsonFields fields) {
  const auto body = json_object(fields);
  fields.emplace_back(
      "result_id",
      json_string(derived_id("deltareduce.demo.mnist.result.v1", {body})));
  return json_object(std::move(fields)) + "\n";
}

class ByteReader final {
 public:
  explicit ByteReader(std::span<const std::byte> bytes) : bytes_(bytes) {}

  [[nodiscard]] std::uint32_t u32() {
    require(remaining() >= 4U, "canonical workload is truncated at u32");
    std::uint32_t result = 0U;
    for (std::size_t index = 0U; index < 4U; ++index) {
      result = static_cast<std::uint32_t>(
          (result << 8U) | std::to_integer<std::uint8_t>(bytes_[offset_++]));
    }
    return result;
  }

  [[nodiscard]] std::uint64_t u64() {
    require(remaining() >= 8U, "canonical workload is truncated at u64");
    std::uint64_t result = 0U;
    for (std::size_t index = 0U; index < 8U; ++index) {
      result = (result << 8U) | std::to_integer<std::uint8_t>(bytes_[offset_++]);
    }
    return result;
  }

  [[nodiscard]] std::int16_t i16() {
    require(remaining() >= 2U, "canonical workload is truncated at i16");
    const auto upper = static_cast<std::uint16_t>(std::to_integer<std::uint8_t>(bytes_[offset_++]));
    const auto lower = static_cast<std::uint16_t>(std::to_integer<std::uint8_t>(bytes_[offset_++]));
    const auto encoded = static_cast<std::uint16_t>((upper << 8U) | lower);
    const auto signed_value = encoded <= 0x7fffU
                                  ? static_cast<std::int32_t>(encoded)
                                  : static_cast<std::int32_t>(encoded) - 0x1'0000;
    return static_cast<std::int16_t>(signed_value);
  }

  [[nodiscard]] std::string ascii(std::size_t count) {
    require(remaining() >= count, "canonical workload is truncated at ASCII field");
    std::string result;
    result.reserve(count);
    for (std::size_t index = 0U; index < count; ++index) {
      const auto value = std::to_integer<unsigned char>(bytes_[offset_++]);
      require(value >= 0x20U && value <= 0x7eU, "canonical workload contains non-ASCII ID");
      result.push_back(static_cast<char>(value));
    }
    return result;
  }

  [[nodiscard]] std::span<const std::byte> raw(std::size_t count) {
    require(remaining() >= count, "canonical workload is truncated at raw field");
    const auto result = bytes_.subspan(offset_, count);
    offset_ += count;
    return result;
  }

  [[nodiscard]] std::size_t remaining() const noexcept { return bytes_.size() - offset_; }

 private:
  std::span<const std::byte> bytes_;
  std::size_t offset_ = 0U;
};

struct WorkloadRecord {
  std::uint32_t node_index;
  std::uint64_t sample_count;
  std::string shard_id;
  std::string summary_id;
  std::vector<std::int64_t> q_values;
};

struct Workload {
  canonical::Bytes bytes;
  std::string source_id;
  std::string workload_id;
  std::array<WorkloadRecord, validator_count> records;
  std::array<std::string, validator_count> contribution_ids;
};

[[nodiscard]] Workload parse_workload(const std::filesystem::path& path) {
  auto bytes = read_file(path, exact_workload_bytes);
  require(bytes.size() == exact_workload_bytes, "canonical workload has a non-canonical byte length");
  ByteReader reader(bytes);
  const auto magic = reader.raw(workload_magic.size());
  require(std::equal(magic.begin(), magic.end(), workload_magic.begin()), "canonical workload magic mismatch");
  require(reader.u32() == workload_version, "canonical workload version mismatch");
  require(reader.u32() == validator_count, "canonical workload must contain exactly four nodes");
  require(reader.u32() == vector_width, "canonical workload vector width must be exactly 7850");
  require(reader.u32() == validator_count, "canonical workload must contain exactly four records");
  auto source_id = reader.ascii(content_id_bytes);
  require(certificates::is_content_id(source_id), "canonical workload source_id is invalid");

  std::array<WorkloadRecord, validator_count> records;
  std::vector<std::string> shard_ids;
  std::vector<std::string> summary_ids;
  shard_ids.reserve(validator_count);
  summary_ids.reserve(validator_count);
  for (std::uint32_t record_index = 0U; record_index < validator_count; ++record_index) {
    const auto node_index = reader.u32();
    require(node_index == record_index + 1U, "canonical workload records are not ordered 1..4");
    const auto sample_count = reader.u64();
    require(
        sample_count > 0U && sample_count <= max_samples_per_node,
        "canonical workload sample_count is outside 1..60000");
    auto shard_id = reader.ascii(content_id_bytes);
    require(certificates::is_content_id(shard_id), "canonical workload shard_id is invalid");
    require(
        std::find(shard_ids.begin(), shard_ids.end(), shard_id) == shard_ids.end(),
        "canonical workload shard_id is duplicated");
    shard_ids.push_back(shard_id);
    auto summary_id = reader.ascii(content_id_bytes);
    require(certificates::is_content_id(summary_id), "canonical workload summary_id is invalid");
    require(
        std::find(summary_ids.begin(), summary_ids.end(), summary_id) == summary_ids.end(),
        "canonical workload summary_id is duplicated");
    summary_ids.push_back(summary_id);
    std::vector<std::int64_t> q_values;
    q_values.reserve(vector_width);
    bool any_presence = false;
    for (std::uint32_t coordinate = 0U; coordinate < vector_width; ++coordinate) {
      const auto value = reader.i16();
      if (coordinate < pixel_coordinate_count) {
        require(
            value >= -static_cast<std::int64_t>(validator_count) * 255 && value <= 0,
            "MNIST centroid coordinate is outside the frozen four-ticket scale");
      } else {
        require(
            value == -static_cast<std::int64_t>(validator_count) || value == 0,
            "MNIST presence coordinate must use the frozen four-ticket scale");
        any_presence =
            any_presence || value == -static_cast<std::int64_t>(validator_count);
      }
      q_values.push_back(value);
    }
    require(any_presence, "MNIST node record has no present class");
    records[record_index] = WorkloadRecord{
        node_index,
        sample_count,
        std::move(shard_id),
        std::move(summary_id),
        std::move(q_values),
    };
  }
  require(reader.remaining() == 0U, "canonical workload has trailing bytes");
  const auto workload_id = hash_bytes(bytes);
  std::array<std::string, validator_count> contribution_ids;
  for (std::size_t index = 0U; index < validator_count; ++index) {
    const auto offset = workload_header_bytes + index * workload_record_bytes;
    contribution_ids[index] = hash_bytes(
        std::span<const std::byte>(bytes).subspan(offset, workload_record_bytes));
  }
  return Workload{
      std::move(bytes),
      std::move(source_id),
      workload_id,
      std::move(records),
      std::move(contribution_ids)};
}

void verify_relayed_contributions(
    const Workload& workload,
    const std::filesystem::path& contributions_root) {
  std::error_code error;
  const auto root_status = std::filesystem::symlink_status(contributions_root, error);
  require(
      !error && std::filesystem::is_directory(root_status) &&
          !std::filesystem::is_symlink(root_status),
      "relayed contributions root must be a regular directory");

  std::array<bool, validator_count> observed{};
  std::size_t file_count = 0U;
  for (const auto& entry : std::filesystem::directory_iterator(contributions_root)) {
    const auto status = entry.symlink_status(error);
    require(
        !error && std::filesystem::is_regular_file(status) &&
            !std::filesystem::is_symlink(status),
        "relayed contributions root contains a non-regular entry");
    const auto filename = entry.path().filename().string();
    bool matched = false;
    for (std::size_t index = 0U; index < validator_count; ++index) {
      const auto expected = "worker-0" + std::to_string(index + 1U) + ".bin";
      if (filename == expected) {
        require(!observed[index], "relayed contribution filename is duplicated");
        observed[index] = true;
        const auto bytes = read_file(entry.path(), workload_record_bytes);
        require(
            bytes.size() == workload_record_bytes,
            "relayed contribution has a non-canonical byte length");
        const auto offset = workload_header_bytes + index * workload_record_bytes;
        const auto embedded =
            std::span<const std::byte>(workload.bytes).subspan(offset, workload_record_bytes);
        require(
            std::equal(bytes.begin(), bytes.end(), embedded.begin(), embedded.end()),
            "relayed contribution differs from its canonical workload record");
        require(
            hash_bytes(bytes) == workload.contribution_ids[index],
            "relayed contribution content identity mismatch");
        matched = true;
        break;
      }
    }
    require(matched, "relayed contributions root contains an unexpected file");
    ++file_count;
  }
  require(
      file_count == validator_count &&
          std::all_of(observed.begin(), observed.end(), [](bool value) { return value; }),
      "relayed contributions root must contain exactly worker-01..worker-04");
}

struct Chain {
  certificates::Context context;
  certificates::InputSetCertificate input_set;
  certificates::ApplyArithmeticProfile apply_profile;
  delta::apply::State parent_state;
  std::vector<delta::robust::Contribution> contributions;
  std::vector<std::string> input_leaf_ids;
  std::optional<certificates::SeedTranscript> seed;
  std::optional<delta::robust::PlanResult> robust;
  std::optional<certificates::ParameterShardQc> shard;
  std::optional<certificates::AggregateRootQc> root;
  std::vector<delta::apply::DomainAggregate> domain_aggregates;
  std::optional<certificates::ApplyCandidate> candidate;
  std::optional<certificates::ApplyQc> apply_qc;
  std::array<std::string, 6U> body_ids;
  std::string seed_id;
  std::string norm_id;
  std::string parent_checkpoint_id;
  std::string parent_optimizer_id;
};

[[nodiscard]] std::string ticket_id(std::uint32_t index) {
  return "mnist-ticket-0" + std::to_string(index);
}

[[nodiscard]] certificates::ApplyArithmeticProfile make_apply_profile(const Workload& workload) {
  return certificates::ApplyArithmeticProfile{
      .accumulator_proof_id = derived_id(
          "deltareduce.demo.mnist.accumulator-proof.v1", {workload.source_id, "int128", "4x255"}),
      .domain_weights = {{"mnist", {1, 1U}}},
      .learning_rate = {1, 1U},
      .momentum = {0, 1U},
      .nesterov = true,
      .rounding = "HALF_TOWARD_POSITIVE",
      .weight_decay = {0, 1U},
  };
}

[[nodiscard]] Chain build_base_chain(const Workload& workload) {
  auto apply_profile = make_apply_profile(workload);
  const auto apply_profile_id = certificates::content_id(apply_profile);
  const auto validator_epoch_id = derived_id(
      "deltareduce.demo.mnist.validator-epoch.v1",
      {validator_ids[0], validator_ids[1], validator_ids[2], validator_ids[3]});
  const auto parameter_schema_id = derived_id(
      "deltareduce.demo.mnist.parameter-schema.v1",
      {workload.source_id, "10x784-centroids", "10-presence", "int16-be"});
  const auto round_config_id = derived_id(
      "deltareduce.demo.mnist.round-config.v1",
      {workload.workload_id, parameter_schema_id, apply_profile_id, validator_epoch_id});
  const auto digest = workload.workload_id.substr(7U);
  certificates::Context context{
      .arithmetic_profile_id = apply_profile_id,
      .height = 1U,
      .parameter_schema_id = parameter_schema_id,
      .round_config_id = round_config_id,
      .round_id = "mnist-demo-" + digest.substr(0U, 20U),
      .validator_epoch_id = validator_epoch_id,
      .view = 0U,
  };
  std::vector<certificates::InputTuple> tuples;
  std::vector<delta::robust::Contribution> contributions;
  std::vector<std::string> input_leaf_ids;
  tuples.reserve(validator_count);
  contributions.reserve(validator_count);
  input_leaf_ids.reserve(validator_count);
  for (const auto& record : workload.records) {
    const auto ticket = ticket_id(record.node_index);
    const auto commitment_id = derived_id(
        "deltareduce.demo.mnist.commitment.v1",
        {workload.source_id, record.shard_id, record.summary_id, ticket});
    const auto availability_id = derived_id(
        "deltareduce.demo.mnist.availability.v1", {commitment_id, record.shard_id});
    tuples.push_back(certificates::InputTuple{
        availability_id,
        commitment_id,
        "mnist",
        ticket,
    });
    contributions.push_back(delta::robust::Contribution{"mnist", record.q_values, ticket});
    input_leaf_ids.push_back(record.shard_id);
  }
  std::sort(input_leaf_ids.begin(), input_leaf_ids.end());
  require(
      std::adjacent_find(input_leaf_ids.begin(), input_leaf_ids.end()) == input_leaf_ids.end(),
      "canonical workload does not define four unique input leaves");

  certificates::InputSetCertificate input_set{
      .context = context,
      .input_root = workload.workload_id,
      .quorum_threshold = quorum_threshold,
      .signer_ids = validators(),
      .tuples = std::move(tuples),
  };
  // The typed certificate is the deterministic proposal body.  Its production
  // quorum verifier is intentionally not invoked until the delivered votes
  // have formed and validated the corresponding generic quorum certificate.
  const auto input_set_id = certificates::content_id(input_set);
  const auto parent_checkpoint_id = derived_id(
      "deltareduce.demo.mnist.parent-model.v1", {workload.source_id, "all-zero-int16"});
  const auto parent_optimizer_id = derived_id(
      "deltareduce.demo.mnist.parent-optimizer.v1", {workload.source_id, "all-zero-int16"});
  delta::apply::State parent_state{
      std::vector<std::int64_t>(vector_width, 0),
      std::vector<std::int64_t>(vector_width, 0),
      parent_checkpoint_id,
      parent_optimizer_id,
  };
  return Chain{
      std::move(context),
      std::move(input_set),
      std::move(apply_profile),
      std::move(parent_state),
      std::move(contributions),
      std::move(input_leaf_ids),
      std::nullopt,
      std::nullopt,
      std::nullopt,
      std::nullopt,
      {},
      std::nullopt,
      std::nullopt,
      {input_set_id, {}, {}, {}, {}, {}},
      {},
      {},
      parent_checkpoint_id,
      parent_optimizer_id,
  };
}

[[nodiscard]] certificates::ChainVerifier chain_verifier(const Chain& chain) {
  return certificates::ChainVerifier(
      chain.context,
      certificates::ValidatorPolicy{
          chain.context.validator_epoch_id, validators(), quorum_threshold});
}

void build_plan_stage(Chain& chain, bool include_plan) {
  require(!chain.body_ids[0].empty(), "input-set stage is missing");
  if (!chain.robust.has_value()) {
    std::vector<std::string> seed_shares;
    seed_shares.reserve(validator_count);
    for (const auto& validator : validator_ids) {
      seed_shares.push_back(derived_id(
          "deltareduce.demo.mnist.seed-share.v1", {chain.body_ids[0], validator}));
    }
    std::sort(seed_shares.begin(), seed_shares.end());
    chain.seed.emplace(certificates::SeedTranscript{
        .context = chain.context,
        .input_set_certificate_id = chain.body_ids[0],
        .seed_id = derived_id("deltareduce.demo.mnist.seed.v1", {chain.body_ids[0]}),
        .seed_profile_id = derived_id(
            "deltareduce.demo.mnist.seed-profile.v1", {"LOCAL_DEMO_ONLY"}),
        .share_ids = std::move(seed_shares),
    });
    chain.seed_id = certificates::content_id(*chain.seed);
    const auto robust_profile_id = derived_id(
        "deltareduce.demo.mnist.robust-profile.v1",
        {"bucket_count=1", "iteration_count=1", "trim_highest=0", "equal_weight=1/4"});
    chain.robust.emplace(delta::robust::build_plan(
        chain.context,
        chain.body_ids[0],
        chain.seed_id,
        robust_profile_id,
        chain.seed->seed_id,
        chain.contributions,
        delta::robust::Profile{
            chain.apply_profile.accumulator_proof_id,
            1U,
            1U,
            0U,
            validator_count,
            static_cast<std::int64_t>(validator_count) * 255,
            validator_count,
        },
        validators(),
        quorum_threshold));
    chain.norm_id = certificates::content_id(chain.robust->norms);
    chain.body_ids[1] = certificates::content_id(chain.robust->eligibility);
  }
  if (include_plan && chain.body_ids[2].empty()) {
    chain.body_ids[2] = certificates::content_id(chain.robust->plan);
  }
}

void build_reduce_stage(Chain& chain) {
  require(!chain.body_ids[2].empty() && chain.robust.has_value(), "APC stage is missing");
  if (chain.shard.has_value()) {
    return;
  }
  chain.shard.emplace(delta::robust::reduce_parameter_shard(
      chain.context,
      chain.body_ids[0],
      chain.body_ids[1],
      chain.robust->plan,
      "mnist",
      "centroids-and-presence",
      chain.contributions,
      chain.input_leaf_ids,
      validators(),
      quorum_threshold));
  chain.body_ids[3] = certificates::content_id(*chain.shard);
}

void build_root_stage(Chain& chain) {
  require(chain.shard.has_value() && !chain.body_ids[3].empty(), "parameter-shard stage is missing");
  if (chain.root.has_value()) {
    return;
  }
  const std::vector<certificates::ShardKey> required_keys{{"mnist", "centroids-and-presence"}};
  const std::vector<certificates::ParameterShardQc> shards{*chain.shard};
  chain.root.emplace(certificates::AggregateRootQc{
      .context = chain.context,
      .aggregation_plan_certificate_id = chain.body_ids[2],
      .eligibility_certificate_id = chain.body_ids[1],
      .input_set_certificate_id = chain.body_ids[0],
      .leaves = {{"mnist", chain.body_ids[3], "centroids-and-presence"}},
      .merkle_root = {},
      .quorum_threshold = quorum_threshold,
      .required_keys = required_keys,
      .signer_ids = validators(),
  });
  chain.root->merkle_root = certificates::aggregate_merkle_root(chain.root->leaves);
  chain.body_ids[4] = certificates::content_id(*chain.root);
}

void build_apply_stage(Chain& chain) {
  require(chain.root.has_value() && !chain.body_ids[4].empty(), "aggregate-root stage is missing");
  if (chain.candidate.has_value()) {
    return;
  }
  std::vector<std::int64_t> aggregate_values;
  aggregate_values.reserve(chain.shard->result_numerators.size());
  for (const auto& numerator : chain.shard->result_numerators) {
    aggregate_values.push_back(delta::apply::round_half_toward_positive(
        protocol::parse_i64_decimal(numerator), chain.shard->denominator));
  }
  chain.domain_aggregates = {{"mnist", std::move(aggregate_values)}};
  chain.candidate.emplace(delta::apply::compute_candidate(
      chain.context,
      chain.body_ids[4],
      chain.apply_profile,
      chain.parent_state,
      chain.domain_aggregates));
  chain.apply_qc.emplace(certificates::ApplyQc{
      .context = chain.context,
      .aggregate_root_qc_id = chain.body_ids[4],
      .apply_arithmetic_profile_id = certificates::content_id(chain.apply_profile),
      .apply_candidate_id = certificates::content_id(*chain.candidate),
      .next_model_hash = chain.candidate->next_model_hash,
      .next_optimizer_hash = chain.candidate->next_optimizer_hash,
      .parent_checkpoint_id = chain.candidate->parent_checkpoint_id,
      .quorum_threshold = quorum_threshold,
      .signer_ids = validators(),
  });
  chain.body_ids[5] = certificates::content_id(*chain.apply_qc);
}

[[nodiscard]] std::string verify_typed_stage(
    const Chain& chain,
    std::size_t index,
    const protocol::QuorumCertificate& vote_quorum) {
  require(index < chain.body_ids.size(), "typed certificate phase index is out of range");
  require(
      vote_quorum.body_hash == chain.body_ids[index],
      "vote quorum does not bind the exact typed certificate body");
  const auto verifier = chain_verifier(chain);
  std::string verified_id;
  const std::vector<std::string>* typed_signers = nullptr;
  switch (index) {
    case 0U:
      typed_signers = &chain.input_set.signer_ids;
      verified_id = verifier.verify_input_set(chain.input_set);
      break;
    case 1U:
      require(chain.seed.has_value() && chain.robust.has_value(), "eligibility proposal is missing");
      require(
          verifier.verify_seed(*chain.seed, chain.body_ids[0]) == chain.seed_id,
          "seed transcript identity changed during post-quorum verification");
      require(
          verifier.verify_norms(chain.robust->norms, chain.body_ids[0]) == chain.norm_id,
          "norm evidence identity changed during post-quorum verification");
      typed_signers = &chain.robust->eligibility.signer_ids;
      verified_id = verifier.verify_eligibility(
          chain.robust->eligibility, chain.input_set, chain.norm_id);
      break;
    case 2U:
      require(chain.seed.has_value() && chain.robust.has_value(), "aggregation-plan proposal is missing");
      typed_signers = &chain.robust->plan.signer_ids;
      verified_id = verifier.verify_plan(
          chain.robust->plan,
          chain.input_set,
          chain.robust->eligibility,
          chain.seed_id,
          chain.apply_profile.accumulator_proof_id);
      break;
    case 3U:
      require(chain.shard.has_value(), "parameter-shard proposal is missing");
      typed_signers = &chain.shard->signer_ids;
      verified_id = verifier.verify_shard(
          *chain.shard, chain.body_ids[0], chain.body_ids[1], chain.body_ids[2]);
      break;
    case 4U: {
      require(chain.shard.has_value() && chain.root.has_value(), "aggregate-root proposal is missing");
      typed_signers = &chain.root->signer_ids;
      const std::vector<certificates::ShardKey> required_keys{
          {"mnist", "centroids-and-presence"}};
      const std::vector<certificates::ParameterShardQc> shards{*chain.shard};
      verified_id = verifier.verify_root(
          *chain.root,
          chain.body_ids[0],
          chain.body_ids[1],
          chain.body_ids[2],
          required_keys,
          shards);
      break;
    }
    case 5U:
      require(
          chain.candidate.has_value() && chain.apply_qc.has_value(),
          "Apply proposal is missing");
      typed_signers = &chain.apply_qc->signer_ids;
      verified_id = verifier.verify_apply(
          *chain.apply_qc,
          *chain.candidate,
          chain.body_ids[4],
          certificates::content_id(chain.apply_profile));
      break;
    default:
      fail("typed certificate phase index is out of range");
  }
  require(
      verified_id == chain.body_ids[index],
      "typed certificate identity changed during post-quorum verification");
  require(
      typed_signers != nullptr && *typed_signers == vote_quorum.signer_ids,
      "typed certificate signer set differs from the delivered-vote quorum");
  return verified_id;
}

[[nodiscard]] canonical::Bytes initial_state(const Chain& chain) {
  return protocol::encode(protocol::RoundState{
      .available_ticket_count = 0U,
      .committed_ticket_count = 0U,
      .config_id = chain.context.round_config_id,
      .durable_sequence = 0U,
      .height = chain.context.height,
      .parent_checkpoint_id = chain.parent_checkpoint_id,
      .phase = protocol::RoundPhase::ticketing_open,
      .round_id = chain.context.round_id,
      .state_root = derived_id(
          "deltareduce.demo.mnist.initial-state.v1",
          {chain.context.round_config_id, chain.parent_checkpoint_id}),
      .ticket_count = validator_count,
      .view = chain.context.view,
  });
}

struct PhaseDefinition {
  std::string_view key;
  std::string_view filename;
  certificates::VoteKind vote_kind;
  std::string_view vote_action;
};

constexpr std::array<PhaseDefinition, 6U> phases{
    PhaseDefinition{"input_set", "input_set.vote", certificates::VoteKind::input_set, "ACT-ISC-VOTE"},
    PhaseDefinition{"eligibility", "eligibility.vote", certificates::VoteKind::eligibility, "ACT-EC-VOTE"},
    PhaseDefinition{"aggregation_plan", "aggregation_plan.vote", certificates::VoteKind::aggregation_plan, "ACT-APC-VOTE"},
    PhaseDefinition{"parameter_shard", "parameter_shard.vote", certificates::VoteKind::parameter_shard, "ACT-PARAM-VOTE"},
    PhaseDefinition{"aggregate_root", "aggregate_root.vote", certificates::VoteKind::aggregate_root, "ACT-ROOT-VOTE"},
    PhaseDefinition{"apply", "apply.vote", certificates::VoteKind::apply, "ACT-APPLY-VOTE"},
};

[[nodiscard]] std::vector<std::string> exact_directory_entries(
    const std::filesystem::path& directory) {
  require_plain_directory(directory, "artifact directory");
  std::vector<std::string> entries;
  std::error_code error;
  for (const auto& entry : std::filesystem::directory_iterator(directory)) {
    const auto status = entry.symlink_status(error);
    require(!error && !std::filesystem::is_symlink(status), "artifact tree contains a symlink");
    const auto name = entry.path().filename().string();
    if (std::filesystem::is_directory(status)) {
      entries.push_back("D:" + name);
    } else {
      require(std::filesystem::is_regular_file(status), "artifact tree contains a special file");
      entries.push_back("F:" + name);
    }
  }
  std::sort(entries.begin(), entries.end());
  return entries;
}

void require_exact_directory_entries(
    const std::filesystem::path& directory,
    std::vector<std::string> expected,
    std::string_view label) {
  std::sort(expected.begin(), expected.end());
  require(
      exact_directory_entries(directory) == expected,
      std::string(label) + " does not contain the exact canonical entry set");
}

[[nodiscard]] std::vector<std::string> expected_qc_entries(std::size_t count) {
  require(count <= phases.size(), "QC entry count is out of range");
  std::vector<std::string> expected;
  expected.reserve(count);
  for (std::size_t index = 0U; index < count; ++index) {
    expected.push_back("F:" + std::string(phases[index].key) + ".qc");
  }
  std::sort(expected.begin(), expected.end());
  return expected;
}

void require_exact_qc_root(
    const std::filesystem::path& qcs_root,
    std::size_t completed_count,
    bool allow_current_replay) {
  const auto observed = exact_directory_entries(qcs_root);
  const auto completed = expected_qc_entries(completed_count);
  if (observed == completed) {
    return;
  }
  require(
      allow_current_replay && completed_count < phases.size() &&
          observed == expected_qc_entries(completed_count + 1U),
      "QC root does not contain exactly the required phase prefix");
}

void require_exact_vote_tree(
    const std::filesystem::path& votes_root,
    const PhaseDefinition& phase) {
  std::vector<std::string> root_entries{"D:relay-evidence"};
  for (const auto& validator : validator_ids) {
    root_entries.push_back("D:" + validator);
  }
  require_exact_directory_entries(votes_root, std::move(root_entries), "delivered-vote root");
  require_exact_directory_entries(
      votes_root / "relay-evidence",
      {"F:receipt.json", "F:trace.jsonl"},
      "delivered-vote relay evidence");
  for (const auto& validator : validator_ids) {
    const auto validator_root = votes_root / validator;
    require_exact_directory_entries(
        validator_root, {"D:vote-frames"}, "delivered-vote validator directory");
    require_exact_directory_entries(
        validator_root / "vote-frames",
        {"F:" + std::string(phase.filename)},
        "delivered-vote frame directory");
  }
}

[[nodiscard]] bool same_normalized_path(
    const std::filesystem::path& left,
    const std::filesystem::path& right) {
  return std::filesystem::absolute(left).lexically_normal() ==
         std::filesystem::absolute(right).lexically_normal();
}

[[nodiscard]] std::size_t phase_index(std::string_view value) {
  const auto found = std::find_if(phases.begin(), phases.end(), [&](const auto& phase) {
    return phase.key == value;
  });
  require(found != phases.end(), "phase must be input_set, eligibility, aggregation_plan, parameter_shard, aggregate_root, or apply");
  return static_cast<std::size_t>(found - phases.begin());
}

[[nodiscard]] std::string signature_id(
    const PhaseDefinition& phase,
    std::string_view validator_id,
    std::string_view body_id) {
  return derived_id(
      "deltareduce.demo.mnist.signature-placeholder.v1",
      {std::string(validator_id), std::string(phase.key), std::string(body_id)});
}

class TraceWriter final {
 public:
  TraceWriter(
      const std::filesystem::path& node_directory,
      std::string mode,
      std::string validator_id,
      certificates::Context context)
      : mode_(std::move(mode)),
        validator_id_(std::move(validator_id)),
        context_(std::move(context)) {
    std::filesystem::create_directories(node_directory);
    output_.open(node_directory / "trace.jsonl", std::ios::binary | std::ios::app);
    require(output_.good(), "cannot open node trace.jsonl");
  }

  void emit(
      std::string event,
      std::string action_id,
      std::optional<std::string> vote_kind,
      std::optional<std::string> vote_context_id,
      std::optional<std::string> body_hash,
      std::optional<std::string> result_hash,
      std::uint64_t durable_sequence,
      bool replay,
      std::string outcome,
      std::optional<std::string> error_code) {
    const auto optional_string = [](const std::optional<std::string>& value) {
      return value.has_value() ? json_string(*value) : std::string{"null"};
    };
    const auto line = json_object({
        {"action_id", json_string(action_id)},
        {"authoritative", "false"},
        {"body_hash", optional_string(body_hash)},
        {"classification", json_string("LOCAL_DEMO_ONLY")},
        {"durable_sequence", std::to_string(durable_sequence)},
        {"error_code", optional_string(error_code)},
        {"event", json_string(event)},
        {"formal_semantics_id", json_string(protocol::formal_semantics_id)},
        {"governance_eligible", "false"},
        {"height", std::to_string(context_.height)},
        {"mode", json_string(mode_)},
        {"outcome", json_string(outcome)},
        {"replay", replay ? "true" : "false"},
        {"result_hash", optional_string(result_hash)},
        {"round_id", json_string(context_.round_id)},
        {"schema_version", json_string("1.0.0")},
        {"type_name", json_string("MNIST_DELTA_DEMO_TRACE")},
        {"validator_id", json_string(validator_id_)},
        {"view", std::to_string(context_.view)},
        {"vote_context_id", optional_string(vote_context_id)},
        {"vote_kind", optional_string(vote_kind)},
    });
    output_ << line << '\n';
    output_.flush();
    require(output_.good(), "cannot append node trace.jsonl");
    std::cout << line << '\n';
    std::cout.flush();
  }

 private:
  std::string mode_;
  std::string validator_id_;
  certificates::Context context_;
  std::ofstream output_;
};

struct CliOptions {
  std::string mode;
  std::string phase;
  std::filesystem::path workload;
  std::filesystem::path contributions_root;
  std::filesystem::path node_directory;
  std::string validator_id;
  std::filesystem::path result;
  std::filesystem::path votes_root;
  std::filesystem::path qcs_root;
  std::filesystem::path qc_output;
  std::filesystem::path applied_model;
  std::optional<std::string> crash_after_durable_vote;
};

[[nodiscard]] CliOptions parse_cli(int argc, char** argv) {
  require(argc >= 2, "missing mode; expected vote-phase, certify-phase, or finalize");
  CliOptions options;
  options.mode = argv[1];
  require(
      options.mode == "vote-phase" || options.mode == "certify-phase" || options.mode == "finalize",
      "unknown mode; expected vote-phase, certify-phase, or finalize");
  std::map<std::string, std::string> values;
  for (int index = 2; index < argc; index += 2) {
    require(index + 1 < argc, "CLI option lacks a value");
    const std::string key = argv[index];
    require(key.starts_with("--"), "CLI option must start with --");
    require(values.emplace(key, argv[index + 1]).second, "duplicate CLI option: " + key);
  }
  const auto take = [&](std::string_view key, bool required) {
    const auto found = values.find(std::string(key));
    if (found == values.end()) {
      require(!required, "missing required CLI option: " + std::string(key));
      return std::string{};
    }
    const auto value = found->second;
    values.erase(found);
    require(!value.empty(), "CLI option is empty: " + std::string(key));
    return value;
  };
  options.workload = take("--workload", true);
  options.contributions_root = take("--contributions-root", true);
  options.node_directory = take("--node-dir", true);
  options.validator_id = take("--validator-id", true);
  options.result = take("--result", true);
  if (options.mode == "vote-phase" || options.mode == "certify-phase") {
    options.phase = take("--phase", true);
    static_cast<void>(phase_index(options.phase));
  }
  if (options.mode == "vote-phase") {
    if (phase_index(options.phase) > 0U) {
      options.qcs_root = take("--qcs-root", true);
    }
    const auto crash = take("--crash-after-durable-vote", false);
    if (!crash.empty()) {
      options.crash_after_durable_vote = crash;
    }
  } else if (options.mode == "certify-phase") {
    options.votes_root = take("--votes-root", true);
    if (phase_index(options.phase) > 0U) {
      options.qcs_root = take("--qcs-root", true);
    }
    options.qc_output = take("--qc-output", true);
    require(
        options.qc_output.filename() == options.phase + ".qc",
        "qc-output basename must equal <phase>.qc");
  } else {
    options.qcs_root = take("--qcs-root", true);
    options.applied_model = take("--applied-model", true);
  }
  if (!values.empty()) {
    fail("unknown CLI option: " + values.begin()->first);
  }
  require(known_validator(options.validator_id), "validator-id must be validator-01..validator-04");
  require(
      options.node_directory.filename().string() == options.validator_id,
      "node-dir basename must equal validator-id");
  if (options.crash_after_durable_vote.has_value()) {
    require(options.validator_id == "validator-04", "durable-vote crash injection is validator-04 only");
    require(
        options.mode == "vote-phase" && options.phase == "apply" &&
            *options.crash_after_durable_vote == "apply",
        "only vote-phase apply durable-vote crash is supported");
  }
  return options;
}

[[nodiscard]] runtime::SubmitReceipt submit_command(
    runtime::Runtime& state_runtime,
    const Chain& chain,
    std::string_view validator_id,
    std::string command_kind,
    std::string body_hash,
    std::string request_id,
    std::uint64_t logical_tick,
    std::string action_id,
    TraceWriter& trace) {
  const auto command = protocol::Command{
      std::string(validator_id),
      std::move(body_hash),
      std::move(command_kind),
      chain.context.height,
      logical_tick,
      std::move(request_id),
      chain.context.round_id,
      chain.context.view,
  };
  const auto receipt = state_runtime.submit(protocol::encode(command));
  trace.emit(
      "runtime_transition",
      std::move(action_id),
      std::nullopt,
      std::nullopt,
      command.body_hash,
      receipt.next_state_id,
      receipt.journal_sequence,
      receipt.replay,
      receipt.replay ? "NO_OP" : "ACCEPTED",
      std::nullopt);
  return receipt;
}

void ensure_available(
    runtime::Runtime& state_runtime,
    const Chain& chain,
    std::string_view validator_id,
    TraceWriter& trace) {
  auto state = protocol::parse_round_state(state_runtime.state_bytes());
  if (state.phase == protocol::RoundPhase::eligible ||
      state.phase == protocol::RoundPhase::aggregated) {
    return;
  }
  require(
      state.phase == protocol::RoundPhase::ticketing_open ||
          state.phase == protocol::RoundPhase::committed ||
          state.phase == protocol::RoundPhase::available,
      "node runtime is outside the demo commitment/availability path");
  for (std::uint32_t index = state.committed_ticket_count; index < validator_count; ++index) {
    const auto& tuple = chain.input_set.tuples[index];
    (void)submit_command(
        state_runtime,
        chain,
        validator_id,
        "ACCEPT_COMMITMENT",
        tuple.commitment_id,
        "mnist-demo-commit-0" + std::to_string(index + 1U),
        index + 1U,
        "ACT-COMMIT",
        trace);
  }
  state = protocol::parse_round_state(state_runtime.state_bytes());
  for (std::uint32_t index = state.available_ticket_count; index < validator_count; ++index) {
    const auto& tuple = chain.input_set.tuples[index];
    (void)submit_command(
        state_runtime,
        chain,
        validator_id,
        "ACCEPT_AVAILABILITY",
        tuple.availability_certificate_id,
        "mnist-demo-availability-0" + std::to_string(index + 1U),
        validator_count + index + 1U,
        "ACT-AVAIL-FINALIZE",
        trace);
  }
  state = protocol::parse_round_state(state_runtime.state_bytes());
  require(
      state.phase == protocol::RoundPhase::available &&
          state.committed_ticket_count == validator_count &&
          state.available_ticket_count == validator_count,
      "node runtime did not reach AVAILABLE with four inputs");
}

[[nodiscard]] std::string body_ids_json(const Chain& chain) {
  return json_object({
      {"aggregate_root", json_string(chain.body_ids[4])},
      {"aggregation_plan", json_string(chain.body_ids[2])},
      {"apply", json_string(chain.body_ids[5])},
      {"eligibility", json_string(chain.body_ids[1])},
      {"input_set", json_string(chain.body_ids[0])},
      {"parameter_shard", json_string(chain.body_ids[3])},
  });
}

[[nodiscard]] std::string file_reference_json(
    std::string logical_file,
    const std::filesystem::path& actual_file,
    std::size_t maximum_bytes) {
  return json_object({
      {"file", json_string(logical_file)},
      {"sha256", json_string(hash_file(actual_file, maximum_bytes))},
  });
}

struct VoteFrameResult {
  std::string phase;
  std::string file;
  std::string sha256;
  std::string body_hash;
  std::string context_id;
  std::uint64_t durable_sequence;
  bool replay;
};

[[nodiscard]] std::string vote_frame_json(const VoteFrameResult& frame) {
  return json_object({
      {"body_hash", json_string(frame.body_hash)},
      {"context_id", json_string(frame.context_id)},
      {"durable_sequence", std::to_string(frame.durable_sequence)},
      {"file", json_string(frame.file)},
      {"kind", json_string(frame.phase)},
      {"replay", frame.replay ? "true" : "false"},
      {"sha256", json_string(frame.sha256)},
  });
}

[[nodiscard]] JsonFields common_result_fields(
    const Workload& workload,
    const Chain& chain,
    const CliOptions& options,
    std::string type_name,
    std::string status,
    bool include_body_ids) {
  std::vector<std::string> contribution_ids;
  contribution_ids.reserve(workload.contribution_ids.size());
  for (const auto& content_id : workload.contribution_ids) {
    contribution_ids.push_back(json_string(content_id));
  }
  JsonFields fields{
      {"authoritative", "false"},
      {"classification", json_string("LOCAL_DEMO_ONLY")},
      {"contribution_ids", json_array(contribution_ids)},
      {"cryptographic_signatures_verified", "false"},
      {"formal_semantics_id", json_string(protocol::formal_semantics_id)},
      {"governance_eligible", "false"},
      {"height", std::to_string(chain.context.height)},
      {"mode", json_string(options.mode)},
      {"node_count", std::to_string(validator_count)},
      {"round_id", json_string(chain.context.round_id)},
      {"schema_version", json_string("1.0.0")},
      {"signature_semantics", json_string("CONTENT_ID_PLACEHOLDER_LOCAL_DEMO_ONLY")},
      {"source_id", json_string(workload.source_id)},
      {"status", json_string(status)},
      {"type_name", json_string(type_name)},
      {"validator_id", json_string(options.validator_id)},
      {"vector_width", std::to_string(vector_width)},
      {"view", std::to_string(chain.context.view)},
      {"workload_id", json_string(workload.workload_id)},
  };
  if (include_body_ids) {
    require(
        std::all_of(chain.body_ids.begin(), chain.body_ids.end(), [](const auto& value) {
          return !value.empty();
        }),
        "complete body IDs are required for the final result");
    fields.emplace_back("body_ids", body_ids_json(chain));
  }
  return fields;
}

struct QuorumResult {
  std::string phase;
  std::string qc_id;
  std::string body_hash;
  std::string context_id;
  std::size_t signer_count;
};

[[nodiscard]] std::string quorum_json(const QuorumResult& result) {
  return json_object({
      {"body_hash", json_string(result.body_hash)},
      {"context_id", json_string(result.context_id)},
      {"kind", json_string(result.phase)},
      {"qc_id", json_string(result.qc_id)},
      {"signer_count", std::to_string(result.signer_count)},
      {"threshold", std::to_string(quorum_threshold)},
  });
}

[[nodiscard]] protocol::Vote expected_vote(
    const Chain& chain,
    std::size_t index,
    std::string_view validator_id,
    std::string body_hash) {
  const auto& phase = phases[index];
  return certificates::make_vote(
      phase.vote_kind,
      chain.context,
      body_hash,
      std::string(validator_id),
      signature_id(phase, validator_id, body_hash),
      index + 1U);
}

[[nodiscard]] protocol::QuorumCertificate expected_quorum(
    const Chain& chain,
    std::size_t index,
    std::string body_hash) {
  const auto& phase = phases[index];
  std::vector<std::string> vote_ids;
  vote_ids.reserve(validator_count);
  std::optional<protocol::Vote> first_vote;
  for (const auto& validator : validator_ids) {
    auto vote = expected_vote(chain, index, validator, body_hash);
    auto frame = protocol::encode(vote);
    vote_ids.push_back(canonical::content_id(canonical::Type::vote, frame));
    if (!first_vote.has_value()) {
      first_vote = std::move(vote);
    }
  }
  require(first_vote.has_value(), "validator set is empty");
  std::vector<std::string> qc_components{
      std::string(phase.key), first_vote->body_hash, first_vote->context_id};
  qc_components.insert(qc_components.end(), vote_ids.begin(), vote_ids.end());
  return protocol::QuorumCertificate{
      .body_hash = first_vote->body_hash,
      .context_id = first_vote->context_id,
      .height = chain.context.height,
      .kind = first_vote->kind,
      .qc_id = derived_id("deltareduce.demo.mnist.quorum-certificate.v1", qc_components),
      .quorum_threshold = quorum_threshold,
      .round_id = chain.context.round_id,
      .signer_ids = validators(),
      .validator_epoch_id = chain.context.validator_epoch_id,
      .view = chain.context.view,
      .vote_ids = std::move(vote_ids),
  };
}

void verify_predecessor_vote_replays(
    runtime::CertificateVoteRuntime& vote_runtime,
    const Chain& chain,
    std::size_t exclusive_end,
    std::string_view validator_id,
    TraceWriter& trace) {
  for (std::size_t index = 0U; index < exclusive_end; ++index) {
    const auto vote = expected_vote(chain, index, validator_id, chain.body_ids[index]);
    const auto receipt = vote_runtime.persist_and_expose(vote);
    const auto expected_id = canonical::content_id(canonical::Type::vote, protocol::encode(vote));
    require(
        receipt.replay && receipt.vote_id == expected_id &&
            receipt.journal_sequence == index + 1U,
        "durable vote journal does not contain the exact predecessor phase vote");
    trace.emit(
        "predecessor_vote_replay_verified",
        "OBS-VOTE-WAL-REPLAY-VERIFIED",
        vote.kind,
        vote.context_id,
        vote.body_hash,
        receipt.vote_id,
        receipt.journal_sequence,
        true,
        "NO_OP",
        std::nullopt);
  }
}

[[nodiscard]] protocol::QuorumCertificate load_quorum(
    const Chain& chain,
    std::size_t index,
    const std::filesystem::path& qcs_root) {
  const auto path = qcs_root / (std::string(phases[index].key) + ".qc");
  const auto bytes = read_file(path, max_vote_frame_bytes);
  const auto parsed = protocol::parse_quorum_certificate(bytes);
  require(protocol::encode(parsed) == bytes, "quorum certificate is not byte-canonical");
  const auto expected = expected_quorum(chain, index, parsed.body_hash);
  require(parsed == expected, "quorum certificate differs from the exact four-validator certificate");
  consensus::validate_quorum(
      parsed,
      consensus::QuorumPolicy{
          chain.context.validator_epoch_id, validators(), quorum_threshold});
  return parsed;
}

void require_quorum_body(
    const protocol::QuorumCertificate& certificate,
    std::string_view expected_body) {
  require(
      certificate.body_hash == expected_body,
      "quorum certificate body differs from the stage reconstructed by Delta");
}

void emit_quorum(
    TraceWriter& trace,
    const protocol::QuorumCertificate& value,
    bool newly_finalized,
    bool replay = false) {
  trace.emit(
      "quorum_validated",
      newly_finalized ? std::string("OBS-CURRENT-QC-DURABLY-FINALIZED")
                      : std::string("OBS-PARENT-QC-VALIDATED"),
      value.kind,
      value.context_id,
      value.body_hash,
      value.qc_id,
      0U,
      replay,
      newly_finalized ? (replay ? "NO_OP" : "FINALIZED") : "VALIDATED_PARENT",
      std::nullopt);
}

void emit_current_vote_quorum_validated(
    TraceWriter& trace,
    const protocol::QuorumCertificate& value) {
  trace.emit(
      "vote_quorum_validated",
      "OBS-CURRENT-VOTE-QUORUM-VALIDATED",
      value.kind,
      value.context_id,
      value.body_hash,
      value.qc_id,
      0U,
      false,
      "VALIDATED",
      std::nullopt);
}

void emit_component(
    TraceWriter& trace,
    std::string event,
    std::size_t index,
    std::string action_id,
    std::string body_hash,
    std::string result_hash,
    bool replay = false) {
  const auto& phase = phases[index];
  trace.emit(
      std::move(event),
      std::move(action_id),
      std::string(certificates::vote_kind_name(phase.vote_kind)),
      std::nullopt,
      std::move(body_hash),
      std::move(result_hash),
      0U,
      replay,
      replay ? "NO_OP" : "ACCEPTED",
      std::nullopt);
}

void build_stage(Chain& chain, std::size_t index) {
  switch (index) {
    case 0U:
      require(!chain.body_ids[0].empty(), "input-set proposal is missing");
      return;
    case 1U:
      build_plan_stage(chain, false);
      return;
    case 2U:
      build_plan_stage(chain, true);
      return;
    case 3U:
      build_reduce_stage(chain);
      return;
    case 4U:
      build_root_stage(chain);
      return;
    case 5U:
      build_apply_stage(chain);
      return;
    default:
      fail("stage index is out of range");
  }
}

void emit_stage_materialized(
    TraceWriter& trace,
    const Chain& chain,
    std::size_t index,
    bool reconstructed) {
  switch (index) {
    case 0U:
      emit_component(
          trace,
          "input_set_closed",
          index,
          reconstructed ? "OBS-INPUT-SET-RECONSTRUCTED" : "ACT-INPUT-CLOSE",
          chain.input_set.input_root,
          chain.body_ids[0],
          reconstructed);
      return;
    case 1U:
      emit_component(
          trace,
          "seed_generated",
          index,
          reconstructed ? "OBS-SEED-RECONSTRUCTED" : "ACT-SEED-GENERATE",
          chain.body_ids[0],
          chain.seed_id,
          reconstructed);
      emit_component(
          trace,
          "typed_certificate_materialized",
          index,
          reconstructed ? "OBS-EC-BODY-RECONSTRUCTED" : "OBS-EC-BODY-MATERIALIZED",
          chain.seed_id,
          chain.body_ids[1],
          reconstructed);
      return;
    case 2U:
      emit_component(
          trace,
          "typed_certificate_materialized",
          index,
          reconstructed ? "OBS-AGGREGATION-PLAN-RECONSTRUCTED"
                        : "OBS-AGGREGATION-PLAN-COMPUTED",
          chain.body_ids[1],
          chain.body_ids[2],
          reconstructed);
      return;
    case 3U:
      emit_component(
          trace,
          "parameter_shard_reduced",
          index,
          reconstructed ? "OBS-PARAMETER-SHARD-RECONSTRUCTED" : "ACT-PARAM-PROPOSE",
          chain.body_ids[2],
          chain.body_ids[3],
          reconstructed);
      return;
    case 4U:
      emit_component(
          trace,
          "aggregate_root_assembled",
          index,
          reconstructed ? "OBS-AGGREGATE-ROOT-RECONSTRUCTED" : "ACT-ROOT-ASSEMBLE",
          chain.body_ids[3],
          chain.body_ids[4],
          reconstructed);
      return;
    case 5U:
      emit_component(
          trace,
          "apply_computed",
          index,
          reconstructed ? "OBS-APPLY-CANDIDATE-RECONSTRUCTED" : "ACT-APPLY-COMPUTE",
          chain.body_ids[4],
          certificates::content_id(*chain.candidate),
          reconstructed);
      emit_component(
          trace,
          "typed_certificate_materialized",
          index,
          reconstructed ? "OBS-APPLY-BODY-RECONSTRUCTED" : "OBS-APPLY-BODY-MATERIALIZED",
          certificates::content_id(*chain.candidate),
          chain.body_ids[5],
          reconstructed);
      return;
    default:
      fail("stage index is out of range");
  }
}

void emit_typed_stage_verified(TraceWriter& trace, const Chain& chain, std::size_t index) {
  emit_component(
      trace,
      "chain_verifier_verified",
      index,
      "OBS-TYPED-CERT-VERIFIED-AFTER-QC",
      chain.body_ids[index],
      chain.body_ids[index]);
}

[[nodiscard]] std::vector<protocol::QuorumCertificate> materialize_parent_quorums(
    Chain& chain,
    std::size_t target,
    const std::filesystem::path& qcs_root,
    TraceWriter& trace) {
  require(target <= phases.size(), "parent quorum target is out of range");
  std::vector<protocol::QuorumCertificate> parents;
  parents.reserve(target);
  for (std::size_t index = 0U; index < target; ++index) {
    build_stage(chain, index);
    auto certificate = load_quorum(chain, index, qcs_root);
    require_quorum_body(certificate, chain.body_ids[index]);
    emit_quorum(trace, certificate, false);
    static_cast<void>(verify_typed_stage(chain, index, certificate));
    emit_typed_stage_verified(trace, chain, index);
    parents.push_back(std::move(certificate));
  }
  return parents;
}

[[nodiscard]] std::string quorum_ids_json(
    const std::vector<protocol::QuorumCertificate>& values) {
  std::vector<std::string> ids;
  ids.reserve(values.size());
  for (const auto& value : values) {
    ids.push_back(json_string(value.qc_id));
  }
  return json_array(ids);
}

[[nodiscard]] protocol::QuorumCertificate collect_quorum(
    const Chain& chain,
    std::size_t index,
    const std::filesystem::path& votes_root) {
  const auto& phase = phases[index];
  std::vector<std::string> vote_ids;
  vote_ids.reserve(validator_count);
  for (const auto& validator : validator_ids) {
    const auto frame_path =
        votes_root / validator / "vote-frames" / std::string(phase.filename);
    const auto frame = read_file(frame_path, max_vote_frame_bytes);
    const auto vote = protocol::parse_vote(frame);
    const auto expected = expected_vote(chain, index, validator, chain.body_ids[index]);
    require(vote == expected, "vote frame differs from the exact canonical phase vote");
    require(protocol::encode(vote) == frame, "vote frame is not byte-canonical");
    vote_ids.push_back(canonical::content_id(canonical::Type::vote, frame));
  }
  auto certificate = expected_quorum(chain, index, chain.body_ids[index]);
  require(certificate.vote_ids == vote_ids, "quorum vote identities differ from relayed frames");
  consensus::validate_quorum(
      certificate,
      consensus::QuorumPolicy{
          chain.context.validator_epoch_id, validators(), quorum_threshold});
  return certificate;
}

void advance_runtime_for_vote(
    runtime::Runtime& state_runtime,
    const Chain& chain,
    std::size_t index,
    std::string_view validator_id,
    TraceWriter& trace) {
  if (index == 0U) {
    ensure_available(state_runtime, chain, validator_id, trace);
    return;
  }
  auto state = protocol::parse_round_state(state_runtime.state_bytes());
  if (index == 1U) {
    if (state.phase == protocol::RoundPhase::eligible) {
      return;
    }
    require(state.phase == protocol::RoundPhase::available, "ISC QC requires AVAILABLE state");
    static_cast<void>(submit_command(
        state_runtime,
        chain,
        validator_id,
        "FINALIZE_INPUT_FREEZE",
        chain.body_ids[0],
        "mnist-demo-input-freeze",
        9U,
        "ACT-ISC-FINALIZE",
        trace));
    state = protocol::parse_round_state(state_runtime.state_bytes());
    require(state.phase == protocol::RoundPhase::eligible, "ISC QC did not reach ELIGIBLE");
    return;
  }
  if (index < 5U) {
    require(state.phase == protocol::RoundPhase::eligible, "phase vote requires ELIGIBLE state");
    return;
  }
  if (state.phase == protocol::RoundPhase::aggregated) {
    require(
        state.state_root == chain.body_ids[4],
        "replayed Apply vote sees a different AggregateRootQC state");
    return;
  }
  require(state.phase == protocol::RoundPhase::eligible, "AggregateRootQC requires ELIGIBLE state");
  static_cast<void>(submit_command(
      state_runtime,
      chain,
      validator_id,
      "FINALIZE_AGGREGATE",
      chain.body_ids[4],
      "mnist-demo-finalize-aggregate",
      10U,
      "ACT-ROOT-FINALIZE",
      trace));
  state = protocol::parse_round_state(state_runtime.state_bytes());
  require(
      state.phase == protocol::RoundPhase::aggregated && state.state_root == chain.body_ids[4],
      "AggregateRootQC did not reach AGGREGATED");
}

void require_runtime_ready_for_stage(
    runtime::Runtime& state_runtime,
    const Chain& chain,
    std::size_t index) {
  const auto state = protocol::parse_round_state(state_runtime.state_bytes());
  if (index == 0U) {
    require(state.phase == protocol::RoundPhase::available, "ISC certification requires AVAILABLE state");
    return;
  }
  if (index < 5U) {
    require(state.phase == protocol::RoundPhase::eligible, "phase certification requires ELIGIBLE state");
    return;
  }
  require(
      state.phase == protocol::RoundPhase::aggregated && state.state_root == chain.body_ids[4],
      "Apply certification requires the durable AggregateRootQC state");
}

[[nodiscard]] Workload load_workload(const CliOptions& options) {
  try {
    auto workload = parse_workload(options.workload);
    verify_relayed_contributions(workload, options.contributions_root);
    return workload;
  } catch (const std::bad_alloc&) {
    fail("allocation failure while parsing the bounded workload");
  }
}

[[nodiscard]] Chain load_base_chain(const Workload& workload) {
  try {
    return build_base_chain(workload);
  } catch (const std::bad_alloc&) {
    fail("allocation failure while constructing the native Delta phase");
  }
}

[[nodiscard]] int vote_phase(const CliOptions& options) {
  const auto workload = load_workload(options);
  auto chain = load_base_chain(workload);
  const auto index = phase_index(options.phase);
  const auto& phase = phases[index];
  if (index > 0U) {
    require_exact_qc_root(options.qcs_root, index, false);
  }
  std::filesystem::create_directories(options.node_directory / "vote-frames");
  TraceWriter trace(options.node_directory, options.mode, options.validator_id, chain.context);
  trace.emit(
      "mode_started",
      "OBS-POST-CONFIG-SUBTRACE-START",
      std::string(certificates::vote_kind_name(phase.vote_kind)),
      std::nullopt,
      index == 0U ? std::optional<std::string>{chain.body_ids[0]} : std::nullopt,
      workload.workload_id,
      0U,
      false,
      "ACCEPTED",
      std::nullopt);
  runtime::Runtime state_runtime(runtime::Config{
      .directory = options.node_directory / "runtime",
      .initial_state_bytes = initial_state(chain),
      .submission_capacity = 64U,
  });
  auto parent_qcs = materialize_parent_quorums(chain, index, options.qcs_root, trace);
  auto vote_runtime = std::make_unique<runtime::CertificateVoteRuntime>(
      options.node_directory / "votes", initial_state(chain));
  const auto recovered_before = vote_runtime->recovered_vote_count();
  require(
      recovered_before == index || recovered_before == index + 1U,
      "durable vote journal is not at the current phase boundary");
  verify_predecessor_vote_replays(
      *vote_runtime, chain, index, options.validator_id, trace);
  // The persisted native phase transition is the gate for every computation
  // belonging to the new phase, not an after-the-fact observation.
  advance_runtime_for_vote(state_runtime, chain, index, options.validator_id, trace);
  build_stage(chain, index);
  emit_stage_materialized(trace, chain, index, recovered_before == index + 1U);
  if (recovered_before > 0U) {
    trace.emit(
        "journal_recovered",
        "ACT-JOURNAL-RECOVER",
        std::string(certificates::vote_kind_name(phase.vote_kind)),
        std::nullopt,
        chain.body_ids[index],
        std::nullopt,
        recovered_before,
        true,
        "ACCEPTED",
        std::nullopt);
  }
  const auto vote = expected_vote(chain, index, options.validator_id, chain.body_ids[index]);
  const bool inject = options.crash_after_durable_vote.has_value();
  try {
    auto receipt = vote_runtime->persist_and_expose(
        vote,
        inject ? runtime::CrashPoint::after_durability_before_commit
               : runtime::CrashPoint::none);
    const auto frame_path = options.node_directory / "vote-frames" / phase.filename;
    write_atomic(frame_path, receipt.frame);
    const VoteFrameResult frame{
        std::string(phase.key),
        "vote-frames/" + std::string(phase.filename),
        hash_bytes(receipt.frame),
        vote.body_hash,
        vote.context_id,
        receipt.journal_sequence,
        receipt.replay,
    };
    trace.emit(
        "vote_durable_and_exposed",
        std::string(phase.vote_action),
        vote.kind,
        vote.context_id,
        vote.body_hash,
        receipt.vote_id,
        receipt.journal_sequence,
        receipt.replay,
        receipt.replay ? "NO_OP" : "ACCEPTED",
        std::nullopt);
    auto fields = common_result_fields(
        workload, chain, options, "MNIST_DELTA_VOTE_PHASE_RESULT", "VOTE_EXPOSED", false);
    fields.emplace_back("phase", json_string(phase.key));
    fields.emplace_back("recovered_vote_count", std::to_string(recovered_before));
    fields.emplace_back("recovery_required", "false");
    fields.emplace_back(
        "runtime_wal",
        file_reference_json(
            "runtime/runtime.wal",
            options.node_directory / "runtime" / "runtime.wal",
            16U * 1024U * 1024U));
    fields.emplace_back("validated_parent_qc_ids", quorum_ids_json(parent_qcs));
    fields.emplace_back("vote_frame", vote_frame_json(frame));
    fields.emplace_back(
        "vote_wal",
        file_reference_json(
            "votes/runtime.wal",
            options.node_directory / "votes" / "runtime.wal",
            16U * 1024U * 1024U));
    const auto document = result_document(std::move(fields));
    write_atomic(options.result, document);
    trace.emit(
        "mode_complete",
        "OBS-POST-CONFIG-SUBTRACE-COMPLETE",
        vote.kind,
        vote.context_id,
        vote.body_hash,
        receipt.vote_id,
        receipt.journal_sequence,
        receipt.replay,
        "VOTE_EXPOSED",
        std::nullopt);
    return 0;
  } catch (const runtime::RuntimeError& error) {
    if (!inject || error.code() != runtime::ErrorCode::simulated_crash) {
      throw;
    }
    trace.emit(
        "simulated_crash",
        "ACT-CRASH",
        vote.kind,
        vote.context_id,
        vote.body_hash,
        std::nullopt,
        index + 1U,
        false,
        "DURABLE_NOT_EXPOSED",
        "SIMULATED_CRASH_AFTER_DURABILITY");
    vote_runtime.reset();
    trace.emit(
        "runtime_restarted",
        "ACT-RESTART",
        vote.kind,
        vote.context_id,
        vote.body_hash,
        std::nullopt,
        index + 1U,
        false,
        "ACCEPTED",
        std::nullopt);
    runtime::CertificateVoteRuntime recovery_probe(
        options.node_directory / "votes", initial_state(chain));
    const auto recovered_after = recovery_probe.recovered_vote_count();
    require(recovered_after == index + 1U, "durable vote was not recovered after injected crash");
    verify_predecessor_vote_replays(
        recovery_probe, chain, index + 1U, options.validator_id, trace);
    trace.emit(
        "journal_recovery_verified",
        "ACT-JOURNAL-RECOVER",
        vote.kind,
        vote.context_id,
        vote.body_hash,
        std::nullopt,
        recovered_after,
        true,
        "ACCEPTED",
        std::nullopt);
    auto fields = common_result_fields(
        workload, chain, options, "MNIST_DELTA_VOTE_PHASE_RESULT", "SIMULATED_CRASH", false);
    fields.emplace_back(
        "crashed_vote",
        json_object({
            {"body_hash", json_string(vote.body_hash)},
            {"context_id", json_string(vote.context_id)},
            {"durable_sequence", std::to_string(index + 1U)},
            {"kind", json_string(phase.key)},
        }));
    fields.emplace_back("phase", json_string(phase.key));
    fields.emplace_back("recovered_vote_count", std::to_string(recovered_after));
    fields.emplace_back("recovery_required", "true");
    fields.emplace_back(
        "runtime_wal",
        file_reference_json(
            "runtime/runtime.wal",
            options.node_directory / "runtime" / "runtime.wal",
            16U * 1024U * 1024U));
    fields.emplace_back("validated_parent_qc_ids", quorum_ids_json(parent_qcs));
    fields.emplace_back(
        "vote_wal",
        file_reference_json(
            "votes/runtime.wal",
            options.node_directory / "votes" / "runtime.wal",
            16U * 1024U * 1024U));
    write_atomic(options.result, result_document(std::move(fields)));
    return simulated_crash_exit_code;
  }
}

[[nodiscard]] int certify_phase(const CliOptions& options) {
  const auto workload = load_workload(options);
  auto chain = load_base_chain(workload);
  const auto index = phase_index(options.phase);
  const auto& phase = phases[index];
  const auto qc_parent = options.qc_output.parent_path();
  require(!qc_parent.empty(), "qc-output must have an explicit parent directory");
  if (index > 0U) {
    require(
        same_normalized_path(qc_parent, options.qcs_root),
        "qc-output must be located directly in qcs-root");
  }
  require_exact_qc_root(qc_parent, index, true);
  require_exact_vote_tree(options.votes_root, phase);
  TraceWriter trace(options.node_directory, options.mode, options.validator_id, chain.context);
  trace.emit(
      "mode_started",
      "OBS-POST-CONFIG-SUBTRACE-START",
      std::string(certificates::vote_kind_name(phase.vote_kind)),
      std::nullopt,
      index == 0U ? std::optional<std::string>{chain.body_ids[0]} : std::nullopt,
      workload.workload_id,
      0U,
      false,
      "ACCEPTED",
      std::nullopt);
  runtime::Runtime state_runtime(runtime::Config{
      .directory = options.node_directory / "runtime",
      .initial_state_bytes = initial_state(chain),
      .submission_capacity = 64U,
  });
  auto parent_qcs = materialize_parent_quorums(chain, index, options.qcs_root, trace);
  require_runtime_ready_for_stage(state_runtime, chain, index);
  build_stage(chain, index);
  const auto certificate = collect_quorum(chain, index, options.votes_root);
  emit_current_vote_quorum_validated(trace, certificate);
  static_cast<void>(verify_typed_stage(chain, index, certificate));
  emit_typed_stage_verified(trace, chain, index);
  const auto bytes = protocol::encode(certificate);
  const auto qc_replay = write_durable_once_or_verify(options.qc_output, bytes);
  emit_quorum(trace, certificate, true, qc_replay);
  const QuorumResult quorum{
      std::string(phase.key),
      certificate.qc_id,
      certificate.body_hash,
      certificate.context_id,
      certificate.signer_ids.size(),
  };
  auto fields = common_result_fields(
      workload, chain, options, "MNIST_DELTA_CERTIFY_PHASE_RESULT", "QC_FINALIZED", false);
  fields.emplace_back("phase", json_string(phase.key));
  fields.emplace_back(
      "qc_artifact",
      file_reference_json(
          std::string(phase.key) + ".qc", options.qc_output, max_vote_frame_bytes));
  fields.emplace_back("quorum_certificate", quorum_json(quorum));
  fields.emplace_back("validated_parent_qc_ids", quorum_ids_json(parent_qcs));
  const auto document = result_document(std::move(fields));
  write_atomic(options.result, document);
  trace.emit(
      "mode_complete",
      "OBS-POST-CONFIG-SUBTRACE-COMPLETE",
      certificate.kind,
      certificate.context_id,
      certificate.body_hash,
      certificate.qc_id,
      0U,
      false,
      "QC_FINALIZED",
      std::nullopt);
  return 0;
}

[[nodiscard]] canonical::Bytes model_bytes(const certificates::ApplyCandidate& candidate) {
  require(candidate.next_model_values.size() == vector_width, "applied model width differs from 7850");
  canonical::Bytes output;
  output.reserve(model_magic.size() + sizeof(std::uint32_t) + vector_width * sizeof(std::int16_t));
  output.insert(output.end(), model_magic.begin(), model_magic.end());
  output.push_back(static_cast<std::byte>((vector_width >> 24U) & 0xffU));
  output.push_back(static_cast<std::byte>((vector_width >> 16U) & 0xffU));
  output.push_back(static_cast<std::byte>((vector_width >> 8U) & 0xffU));
  output.push_back(static_cast<std::byte>(vector_width & 0xffU));
  for (const auto& encoded : candidate.next_model_values) {
    const auto value = protocol::parse_i64_decimal(encoded);
    require(
        value >= std::numeric_limits<std::int16_t>::min() &&
            value <= std::numeric_limits<std::int16_t>::max(),
        "applied model coordinate cannot be represented as int16");
    const auto unsigned_value = static_cast<std::uint16_t>(
        value < 0 ? 0x1'0000LL + value : value);
    output.push_back(static_cast<std::byte>((unsigned_value >> 8U) & 0xffU));
    output.push_back(static_cast<std::byte>(unsigned_value & 0xffU));
  }
  return output;
}


[[nodiscard]] int finalize(const CliOptions& options) {
  const auto workload = load_workload(options);
  auto chain = load_base_chain(workload);
  require_exact_qc_root(options.qcs_root, phases.size(), false);
  TraceWriter trace(options.node_directory, options.mode, options.validator_id, chain.context);
  trace.emit(
      "mode_started",
      "OBS-POST-CONFIG-SUBTRACE-START",
      std::nullopt,
      std::nullopt,
      std::nullopt,
      workload.workload_id,
      0U,
      false,
      "ACCEPTED",
      std::nullopt);

  runtime::Runtime state_runtime(runtime::Config{
      .directory = options.node_directory / "runtime",
      .initial_state_bytes = initial_state(chain),
      .submission_capacity = 64U,
  });
  const auto state = protocol::parse_round_state(state_runtime.state_bytes());
  require(
      state.phase == protocol::RoundPhase::aggregated,
      "finalize requires the durable AGGREGATED state produced before Apply vote");

  auto certificates_by_phase = materialize_parent_quorums(chain, 5U, options.qcs_root, trace);
  require(
      state.state_root == chain.body_ids[4],
      "finalize durable state differs from the verified AggregateRootQC body");
  build_stage(chain, 5U);
  auto apply_certificate = load_quorum(chain, 5U, options.qcs_root);
  require_quorum_body(apply_certificate, chain.body_ids[5]);
  emit_quorum(trace, apply_certificate, false);
  static_cast<void>(verify_typed_stage(chain, 5U, apply_certificate));
  emit_typed_stage_verified(trace, chain, 5U);
  certificates_by_phase.push_back(std::move(apply_certificate));
  require(
      certificates_by_phase.size() == phases.size(),
      "finalize requires one validated quorum certificate for every phase");

  require(chain.candidate.has_value() && chain.apply_qc.has_value(), "Apply stage is missing");
  const auto artifact = model_bytes(*chain.candidate);
  static_cast<void>(write_durable_once_or_verify(options.applied_model, artifact));
  runtime::CurrentPointerStore pointer_store(
      options.node_directory / "current",
      runtime::PointerState{
          chain.parent_checkpoint_id,
          chain.parent_optimizer_id,
          {},
          0U,
      });
  const certificates::CurrentPointerCommand pointer_command{
      chain.context,
      chain.body_ids[5],
      chain.parent_checkpoint_id,
      chain.candidate->next_model_hash,
      chain.candidate->next_optimizer_hash,
  };
  const auto disposition = pointer_store.advance(pointer_command, *chain.apply_qc);
  const auto& pointer = pointer_store.state();
  require(
      pointer.checkpoint_id == chain.candidate->next_model_hash &&
          pointer.optimizer_id == chain.candidate->next_optimizer_hash &&
          pointer.apply_qc_id == chain.body_ids[5] && pointer.height == chain.context.height,
      "current pointer did not reach the certified APPLIED state");
  trace.emit(
      "current_pointer_applied",
      "ACT-CURRENT-ADVANCE",
      std::nullopt,
      std::nullopt,
      chain.body_ids[5],
      pointer.checkpoint_id,
      state.durable_sequence,
      disposition == runtime::PointerDisposition::replay,
      disposition == runtime::PointerDisposition::replay ? "NO_OP" : "FINALIZED",
      std::nullopt);

  std::vector<std::string> quorum_documents;
  quorum_documents.reserve(certificates_by_phase.size());
  for (std::size_t index = 0U; index < certificates_by_phase.size(); ++index) {
    const auto& value = certificates_by_phase[index];
    quorum_documents.push_back(quorum_json(QuorumResult{
        std::string(phases[index].key),
        value.qc_id,
        value.body_hash,
        value.context_id,
        value.signer_ids.size(),
    }));
  }
  auto fields = common_result_fields(
      workload, chain, options, "MNIST_DELTA_FINALIZE_RESULT", "APPLIED", true);
  fields.emplace_back("aggregate_root_qc_id", json_string(chain.body_ids[4]));
  fields.emplace_back(
      "apply_candidate_id", json_string(certificates::content_id(*chain.candidate)));
  fields.emplace_back("apply_qc_id", json_string(chain.body_ids[5]));
  fields.emplace_back(
      "current_pointer",
      json_object({
          {"apply_qc_id", json_string(pointer.apply_qc_id)},
          {"checkpoint_id", json_string(pointer.checkpoint_id)},
          {"disposition", json_string(
               disposition == runtime::PointerDisposition::replay ? "REPLAY" : "ADVANCED")},
          {"height", std::to_string(pointer.height)},
          {"optimizer_id", json_string(pointer.optimizer_id)},
      }));
  fields.emplace_back(
      "current_pointer_wal",
      file_reference_json(
          "current/current-pointer.wal",
          options.node_directory / "current" / "current-pointer.wal",
          16U * 1024U * 1024U));
  fields.emplace_back(
      "model_artifact",
      json_object({
          {"bytes", std::to_string(artifact.size())},
          {"file", json_string("applied-model.bin")},
          {"format", json_string("DMODEL1_INT16_BE_V1")},
          {"sha256", json_string(hash_bytes(artifact))},
          {"width", std::to_string(vector_width)},
      }));
  fields.emplace_back("model_hash", json_string(chain.candidate->next_model_hash));
  fields.emplace_back("optimizer_hash", json_string(chain.candidate->next_optimizer_hash));
  fields.emplace_back("quorum_certificates", json_array(quorum_documents));
  fields.emplace_back(
      "runtime_wal",
      file_reference_json(
          "runtime/runtime.wal",
          options.node_directory / "runtime" / "runtime.wal",
          16U * 1024U * 1024U));
  fields.emplace_back(
      "vote_wal",
      file_reference_json(
          "votes/runtime.wal",
          options.node_directory / "votes" / "runtime.wal",
          16U * 1024U * 1024U));
  const auto document = result_document(std::move(fields));
  write_atomic(options.result, document);
  trace.emit(
      "mode_complete",
      "OBS-POST-CONFIG-SUBTRACE-COMPLETE",
      std::nullopt,
      std::nullopt,
      chain.body_ids[5],
      chain.candidate->next_model_hash,
      state.durable_sequence,
      disposition == runtime::PointerDisposition::replay,
      "APPLIED",
      std::nullopt);
  return 0;
}

[[nodiscard]] int describe() {
  std::cout
      << json_object({
             {"applied_model_format", json_string("DMODEL1_INT16_BE_V1")},
             {"authoritative", "false"},
             {"classification", json_string("LOCAL_DEMO_ONLY")},
             {"crash_exit_code", std::to_string(simulated_crash_exit_code)},
             {"executable", json_string("delta_mnist_native_node")},
             {"formal_semantics_id", json_string(protocol::formal_semantics_id)},
             {"governance_eligible", "false"},
             {"modes", json_array({
                  json_string("vote-phase"),
                  json_string("certify-phase"),
                  json_string("finalize")})},
             {"node_count", std::to_string(validator_count)},
             {"schema_version", json_string("1.0.0")},
             {"type_name", json_string("MNIST_DELTA_NATIVE_NODE_DESCRIPTOR")},
             {"vector_width", std::to_string(vector_width)},
             {"workload_bytes", std::to_string(exact_workload_bytes)},
             {"workload_format", json_string("DMNIST2_NODE_SUMMARY_INT16_BE_V1")},
         })
      << '\n';
  return 0;
}

}  // namespace

int main(int argc, char** argv) {
  try {
    if (argc == 2 && std::string_view(argv[1]) == "--describe") {
      return describe();
    }
    const auto options = parse_cli(argc, argv);
    if (options.mode == "vote-phase") {
      return vote_phase(options);
    }
    if (options.mode == "certify-phase") {
      return certify_phase(options);
    }
    return finalize(options);
  } catch (const std::exception& error) {
    std::cerr << json_object({
                     {"authoritative", "false"},
                     {"classification", json_string("LOCAL_DEMO_ONLY")},
                     {"error", json_string(error.what())},
                     {"governance_eligible", "false"},
                     {"status", json_string("ERROR")},
                     {"type_name", json_string("MNIST_DELTA_NATIVE_NODE_ERROR")},
                 })
              << '\n';
    return 1;
  }
}
