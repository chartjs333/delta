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
#include <windows.h>
#endif

namespace {

namespace canonical = delta::core::canonical;
namespace consensus = delta::core::consensus;
namespace protocol = delta::core::protocol;
namespace certificates = delta::certificates;
namespace runtime = delta::runtime;

constexpr std::uint32_t workload_version = 1U;
constexpr std::uint32_t validator_count = 4U;
constexpr std::uint32_t quorum_threshold = 3U;
constexpr std::uint32_t pixel_coordinate_count = 10U * 28U * 28U;
constexpr std::uint32_t presence_coordinate_count = 10U;
constexpr std::uint32_t vector_width = pixel_coordinate_count + presence_coordinate_count;
constexpr std::size_t content_id_bytes = 71U;
constexpr std::size_t workload_header_bytes = 8U + 4U * sizeof(std::uint32_t) + content_id_bytes;
constexpr std::size_t workload_record_bytes =
    sizeof(std::uint32_t) + sizeof(std::uint64_t) + content_id_bytes +
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
    std::byte{'1'},
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
  }
  auto temporary = path;
  temporary += ".tmp";
  std::error_code ignored;
  std::filesystem::remove(temporary, ignored);
  {
    std::ofstream output(temporary, std::ios::binary | std::ios::trunc);
    require(output.good(), "cannot create temporary output: " + temporary.generic_string());
    if (!bytes.empty()) {
      output.write(reinterpret_cast<const char*>(bytes.data()), static_cast<std::streamsize>(bytes.size()));
    }
    output.flush();
    require(output.good(), "cannot flush temporary output: " + temporary.generic_string());
  }
  replace_file_atomically(temporary, path);
}

void write_atomic(const std::filesystem::path& path, std::string_view value) {
  const auto bytes = std::as_bytes(std::span(value.data(), value.size()));
  write_atomic(path, bytes);
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
  shard_ids.reserve(validator_count);
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
  certificates::SeedTranscript seed;
  delta::robust::PlanResult robust;
  certificates::ParameterShardQc shard;
  certificates::AggregateRootQc root;
  certificates::ApplyArithmeticProfile apply_profile;
  delta::apply::State parent_state;
  std::vector<delta::apply::DomainAggregate> domain_aggregates;
  certificates::ApplyCandidate candidate;
  certificates::ApplyQc apply_qc;
  std::array<std::string, 6U> body_ids;
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

[[nodiscard]] Chain build_chain(const Workload& workload) {
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
  certificates::ChainVerifier verifier(
      context,
      certificates::ValidatorPolicy{validator_epoch_id, validators(), quorum_threshold});

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
        {workload.source_id, record.shard_id, ticket});
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
  const auto input_set_id = verifier.verify_input_set(input_set);

  std::vector<std::string> seed_shares;
  seed_shares.reserve(validator_count);
  for (const auto& validator : validator_ids) {
    seed_shares.push_back(derived_id(
        "deltareduce.demo.mnist.seed-share.v1", {input_set_id, validator}));
  }
  std::sort(seed_shares.begin(), seed_shares.end());
  certificates::SeedTranscript seed{
      .context = context,
      .input_set_certificate_id = input_set_id,
      .seed_id = derived_id("deltareduce.demo.mnist.seed.v1", {input_set_id}),
      .seed_profile_id = derived_id(
          "deltareduce.demo.mnist.seed-profile.v1", {"LOCAL_DEMO_ONLY"}),
      .share_ids = std::move(seed_shares),
  };
  const auto seed_id = verifier.verify_seed(seed, input_set_id);
  const auto robust_profile_id = derived_id(
      "deltareduce.demo.mnist.robust-profile.v1",
      {"bucket_count=1", "iteration_count=1", "trim_highest=0", "equal_weight=1/4"});
  auto robust = delta::robust::build_plan(
      context,
      input_set_id,
      seed_id,
      robust_profile_id,
      seed.seed_id,
      contributions,
      delta::robust::Profile{
          apply_profile.accumulator_proof_id,
          1U,
          1U,
          0U,
          validator_count,
          static_cast<std::int64_t>(validator_count) * 255,
          validator_count,
      },
      validators(),
      quorum_threshold);
  const auto norm_id = verifier.verify_norms(robust.norms, input_set_id);
  const auto eligibility_id = verifier.verify_eligibility(robust.eligibility, input_set, norm_id);
  const auto plan_id = verifier.verify_plan(
      robust.plan,
      input_set,
      robust.eligibility,
      seed_id,
      apply_profile.accumulator_proof_id);
  auto shard = delta::robust::reduce_parameter_shard(
      context,
      input_set_id,
      eligibility_id,
      robust.plan,
      "mnist",
      "centroids-and-presence",
      contributions,
      input_leaf_ids,
      validators(),
      quorum_threshold);
  const auto shard_id = verifier.verify_shard(shard, input_set_id, eligibility_id, plan_id);
  const std::vector<certificates::ShardKey> required_keys{{"mnist", "centroids-and-presence"}};
  const std::vector<certificates::ParameterShardQc> shards{shard};
  certificates::AggregateRootQc root{
      .context = context,
      .aggregation_plan_certificate_id = plan_id,
      .eligibility_certificate_id = eligibility_id,
      .input_set_certificate_id = input_set_id,
      .leaves = {{"mnist", shard_id, "centroids-and-presence"}},
      .merkle_root = {},
      .quorum_threshold = quorum_threshold,
      .required_keys = required_keys,
      .signer_ids = validators(),
  };
  root.merkle_root = certificates::aggregate_merkle_root(root.leaves);
  const auto root_id = verifier.verify_root(
      root, input_set_id, eligibility_id, plan_id, required_keys, shards);

  std::vector<std::int64_t> aggregate_values;
  aggregate_values.reserve(shard.result_numerators.size());
  for (const auto& numerator : shard.result_numerators) {
    aggregate_values.push_back(delta::apply::round_half_toward_positive(
        protocol::parse_i64_decimal(numerator), shard.denominator));
  }
  std::vector<delta::apply::DomainAggregate> domain_aggregates{
      {"mnist", std::move(aggregate_values)}};
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
  auto candidate = delta::apply::compute_candidate(
      context, root_id, apply_profile, parent_state, domain_aggregates);
  certificates::ApplyQc apply_qc{
      .context = context,
      .aggregate_root_qc_id = root_id,
      .apply_arithmetic_profile_id = apply_profile_id,
      .apply_candidate_id = certificates::content_id(candidate),
      .next_model_hash = candidate.next_model_hash,
      .next_optimizer_hash = candidate.next_optimizer_hash,
      .parent_checkpoint_id = candidate.parent_checkpoint_id,
      .quorum_threshold = quorum_threshold,
      .signer_ids = validators(),
  };
  const auto apply_qc_id = verifier.verify_apply(apply_qc, candidate, root_id, apply_profile_id);
  return Chain{
      std::move(context),
      std::move(input_set),
      std::move(seed),
      std::move(robust),
      std::move(shard),
      std::move(root),
      std::move(apply_profile),
      std::move(parent_state),
      std::move(domain_aggregates),
      std::move(candidate),
      std::move(apply_qc),
      {input_set_id, eligibility_id, plan_id, shard_id, root_id, apply_qc_id},
      parent_checkpoint_id,
      parent_optimizer_id,
  };
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
  std::string_view finalize_action;
};

constexpr std::array<PhaseDefinition, 6U> phases{
    PhaseDefinition{"input_set", "input_set.vote", certificates::VoteKind::input_set, "ACT-ISC-VOTE", "ACT-ISC-FINALIZE"},
    PhaseDefinition{"eligibility", "eligibility.vote", certificates::VoteKind::eligibility, "ACT-EC-VOTE", "ACT-EC-FINALIZE"},
    PhaseDefinition{"aggregation_plan", "aggregation_plan.vote", certificates::VoteKind::aggregation_plan, "ACT-APC-VOTE", "ACT-APC-FINALIZE"},
    PhaseDefinition{"parameter_shard", "parameter_shard.vote", certificates::VoteKind::parameter_shard, "ACT-PARAM-VOTE", "ACT-PARAM-FINALIZE"},
    PhaseDefinition{"aggregate_root", "aggregate_root.vote", certificates::VoteKind::aggregate_root, "ACT-ROOT-VOTE", "ACT-ROOT-FINALIZE"},
    PhaseDefinition{"apply", "apply.vote", certificates::VoteKind::apply, "ACT-APPLY-VOTE", "ACT-APPLY-FINALIZE"},
};

[[nodiscard]] std::string signature_id(
    const Chain& chain,
    const PhaseDefinition& phase,
    std::string_view validator_id) {
  return derived_id(
      "deltareduce.demo.mnist.signature-placeholder.v1",
      {std::string(validator_id), std::string(phase.key), chain.body_ids[&phase - phases.data()]});
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
  std::filesystem::path workload;
  std::filesystem::path contributions_root;
  std::filesystem::path node_directory;
  std::string validator_id;
  std::filesystem::path result;
  std::filesystem::path votes_root;
  std::filesystem::path applied_model;
  std::optional<std::string> crash_after_durable_vote;
};

[[nodiscard]] CliOptions parse_cli(int argc, char** argv) {
  require(argc >= 2, "missing mode; expected prepare-votes or finalize");
  CliOptions options;
  options.mode = argv[1];
  require(
      options.mode == "prepare-votes" || options.mode == "finalize",
      "unknown mode; expected prepare-votes or finalize");
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
  if (options.mode == "prepare-votes") {
    const auto crash = take("--crash-after-durable-vote", false);
    if (!crash.empty()) {
      options.crash_after_durable_vote = crash;
    }
  } else {
    options.votes_root = take("--votes-root", true);
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
    require(*options.crash_after_durable_vote == "apply", "only apply durable-vote crash is supported");
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
    std::string status) {
  std::vector<std::string> contribution_ids;
  contribution_ids.reserve(workload.contribution_ids.size());
  for (const auto& content_id : workload.contribution_ids) {
    contribution_ids.push_back(json_string(content_id));
  }
  return {
      {"authoritative", "false"},
      {"body_ids", body_ids_json(chain)},
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
}

[[nodiscard]] int prepare_votes(const CliOptions& options) {
  const auto workload = [&]() {
    try {
      return parse_workload(options.workload);
    } catch (const std::bad_alloc&) {
      fail("allocation failure while parsing the bounded workload");
    }
  }();
  verify_relayed_contributions(workload, options.contributions_root);
  const auto chain = [&]() {
    try {
      return build_chain(workload);
    } catch (const std::bad_alloc&) {
      fail("allocation failure while constructing the native Delta certificate chain");
    }
  }();
  std::filesystem::create_directories(options.node_directory / "vote-frames");
  TraceWriter trace(options.node_directory, options.mode, options.validator_id, chain.context);
  trace.emit(
      "mode_started",
      "ACT-CONFIG-PROPOSE",
      std::nullopt,
      std::nullopt,
      chain.context.round_config_id,
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
  ensure_available(state_runtime, chain, options.validator_id, trace);

  auto vote_runtime = std::make_unique<runtime::CertificateVoteRuntime>(
      options.node_directory / "votes", initial_state(chain));
  const auto recovered_before = vote_runtime->recovered_vote_count();
  if (recovered_before > 0U) {
    trace.emit(
        "journal_recovered",
        "ACT-JOURNAL-RECOVER",
        std::nullopt,
        std::nullopt,
        std::nullopt,
        std::nullopt,
        recovered_before,
        true,
        "ACCEPTED",
        std::nullopt);
  }

  std::vector<VoteFrameResult> frames;
  frames.reserve(phases.size());
  for (std::size_t index = 0U; index < phases.size(); ++index) {
    const auto& phase = phases[index];
    const auto vote = certificates::make_vote(
        phase.vote_kind,
        chain.context,
        chain.body_ids[index],
        options.validator_id,
        signature_id(chain, phase, options.validator_id),
        index + 1U);
    const bool inject = options.crash_after_durable_vote.has_value() &&
                        *options.crash_after_durable_vote == phase.key;
    try {
      auto receipt = vote_runtime->persist_and_expose(
          vote,
          inject ? runtime::CrashPoint::after_durability_before_commit
                 : runtime::CrashPoint::none);
      const auto frame_path = options.node_directory / "vote-frames" / phase.filename;
      write_atomic(frame_path, receipt.frame);
      frames.push_back(VoteFrameResult{
          std::string(phase.key),
          "vote-frames/" + std::string(phase.filename),
          hash_bytes(receipt.frame),
          vote.body_hash,
          vote.context_id,
          receipt.journal_sequence,
          receipt.replay,
      });
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
    } catch (const runtime::RuntimeError& error) {
      if (!inject || error.code() != runtime::ErrorCode::simulated_crash) {
        throw;
      }
      vote_runtime.reset();
      const runtime::CertificateVoteRuntime recovery_probe(
          options.node_directory / "votes", initial_state(chain));
      const auto recovered_after = recovery_probe.recovered_vote_count();
      require(recovered_after == index + 1U, "durable vote was not recovered after injected crash");
      trace.emit(
          "simulated_crash",
          "ACT-CRASH",
          vote.kind,
          vote.context_id,
          vote.body_hash,
          std::nullopt,
          recovered_after,
          false,
          "DURABLE_NOT_EXPOSED",
          "SIMULATED_CRASH_AFTER_DURABILITY");
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
      std::vector<std::string> frame_json;
      for (const auto& frame : frames) {
        frame_json.push_back(vote_frame_json(frame));
      }
      auto fields = common_result_fields(
          workload, chain, options, "MNIST_DELTA_PREPARE_RESULT", "SIMULATED_CRASH");
      fields.emplace_back(
          "crashed_vote",
          json_object({
              {"body_hash", json_string(vote.body_hash)},
              {"context_id", json_string(vote.context_id)},
              {"durable_sequence", std::to_string(index + 1U)},
              {"kind", json_string(phase.key)},
          }));
      fields.emplace_back("recovered_vote_count", std::to_string(recovered_after));
      fields.emplace_back("recovery_required", "true");
      fields.emplace_back(
          "runtime_wal",
          file_reference_json(
              "runtime/runtime.wal", options.node_directory / "runtime" / "runtime.wal", 16U * 1024U * 1024U));
      fields.emplace_back("vote_frames", json_array(frame_json));
      fields.emplace_back(
          "vote_wal",
          file_reference_json(
              "votes/runtime.wal", options.node_directory / "votes" / "runtime.wal", 16U * 1024U * 1024U));
      write_atomic(options.result, result_document(std::move(fields)));
      return simulated_crash_exit_code;
    }
  }

  std::vector<std::string> frame_json;
  frame_json.reserve(frames.size());
  for (const auto& frame : frames) {
    frame_json.push_back(vote_frame_json(frame));
  }
  auto fields = common_result_fields(
      workload, chain, options, "MNIST_DELTA_PREPARE_RESULT", "VOTES_EXPOSED");
  fields.emplace_back("recovered_vote_count", std::to_string(recovered_before));
  fields.emplace_back("recovery_required", "false");
  fields.emplace_back(
      "runtime_wal",
      file_reference_json(
          "runtime/runtime.wal", options.node_directory / "runtime" / "runtime.wal", 16U * 1024U * 1024U));
  fields.emplace_back("vote_frames", json_array(frame_json));
  fields.emplace_back(
      "vote_wal",
      file_reference_json(
          "votes/runtime.wal", options.node_directory / "votes" / "runtime.wal", 16U * 1024U * 1024U));
  const auto document = result_document(std::move(fields));
  write_atomic(options.result, document);
  trace.emit(
      "mode_complete",
      "ACT-APPLY-VOTE",
      std::string("APPLY_QC"),
      "APPLY_QC:" + chain.context.round_id + ":1:0",
      chain.body_ids[5],
      derived_id("deltareduce.demo.mnist.prepare-result.v1", {document}),
      phases.size(),
      recovered_before > 0U,
      "VOTES_EXPOSED",
      std::nullopt);
  return 0;
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
  const auto workload = [&]() {
    try {
      return parse_workload(options.workload);
    } catch (const std::bad_alloc&) {
      fail("allocation failure while parsing the bounded workload");
    }
  }();
  verify_relayed_contributions(workload, options.contributions_root);
  const auto chain = [&]() {
    try {
      return build_chain(workload);
    } catch (const std::bad_alloc&) {
      fail("allocation failure while constructing the native Delta certificate chain");
    }
  }();
  TraceWriter trace(options.node_directory, options.mode, options.validator_id, chain.context);
  trace.emit(
      "mode_started",
      "ACT-RESTART",
      std::nullopt,
      std::nullopt,
      std::nullopt,
      workload.workload_id,
      0U,
      false,
      "ACCEPTED",
      std::nullopt);

  std::vector<QuorumResult> quorums;
  quorums.reserve(phases.size());
  const consensus::QuorumPolicy policy{
      chain.context.validator_epoch_id, validators(), quorum_threshold};
  for (std::size_t phase_index = 0U; phase_index < phases.size(); ++phase_index) {
    const auto& phase = phases[phase_index];
    std::vector<std::string> vote_ids;
    std::vector<protocol::Vote> votes;
    vote_ids.reserve(validator_count);
    votes.reserve(validator_count);
    for (const auto& validator : validator_ids) {
      const auto frame_path = options.votes_root / validator / "vote-frames" / phase.filename;
      const auto frame = read_file(frame_path, max_vote_frame_bytes);
      const auto vote = protocol::parse_vote(frame);
      const auto expected = certificates::make_vote(
          phase.vote_kind,
          chain.context,
          chain.body_ids[phase_index],
          validator,
          signature_id(chain, phase, validator),
          phase_index + 1U);
      require(vote == expected, "vote frame differs from the exact canonical demo vote: " + frame_path.generic_string());
      require(protocol::encode(vote) == frame, "vote frame is not byte-canonical: " + frame_path.generic_string());
      votes.push_back(vote);
      vote_ids.push_back(canonical::content_id(canonical::Type::vote, frame));
    }
    for (std::size_t index = 1U; index < votes.size(); ++index) {
      require(
          votes[index].body_hash == votes[0].body_hash &&
              votes[index].context_id == votes[0].context_id &&
              votes[index].kind == votes[0].kind,
          "four validator votes do not agree on body/context/kind");
    }
    std::vector<std::string> qc_components{
        std::string(phase.key), votes[0].body_hash, votes[0].context_id};
    qc_components.insert(qc_components.end(), vote_ids.begin(), vote_ids.end());
    const auto qc_id = derived_id("deltareduce.demo.mnist.quorum-certificate.v1", qc_components);
    const protocol::QuorumCertificate certificate{
        .body_hash = votes[0].body_hash,
        .context_id = votes[0].context_id,
        .height = chain.context.height,
        .kind = votes[0].kind,
        .qc_id = qc_id,
        .quorum_threshold = quorum_threshold,
        .round_id = chain.context.round_id,
        .signer_ids = validators(),
        .validator_epoch_id = chain.context.validator_epoch_id,
        .view = chain.context.view,
        .vote_ids = std::move(vote_ids),
    };
    consensus::validate_quorum(certificate, policy);
    quorums.push_back(QuorumResult{
        std::string(phase.key),
        qc_id,
        certificate.body_hash,
        certificate.context_id,
        certificate.signer_ids.size(),
    });
    trace.emit(
        "quorum_validated",
        std::string(phase.finalize_action),
        certificate.kind,
        certificate.context_id,
        certificate.body_hash,
        certificate.qc_id,
        0U,
        false,
        "FINALIZED",
        std::nullopt);
  }

  runtime::Runtime state_runtime(runtime::Config{
      .directory = options.node_directory / "runtime",
      .initial_state_bytes = initial_state(chain),
      .submission_capacity = 64U,
  });
  ensure_available(state_runtime, chain, options.validator_id, trace);
  auto state = protocol::parse_round_state(state_runtime.state_bytes());
  if (state.phase == protocol::RoundPhase::available) {
    (void)submit_command(
        state_runtime,
        chain,
        options.validator_id,
        "FINALIZE_INPUT_FREEZE",
        chain.body_ids[0],
        "mnist-demo-input-freeze",
        9U,
        "ACT-ISC-FINALIZE",
        trace);
    state = protocol::parse_round_state(state_runtime.state_bytes());
  }
  require(state.phase == protocol::RoundPhase::eligible || state.phase == protocol::RoundPhase::aggregated,
          "node runtime did not reach ELIGIBLE");
  if (state.phase == protocol::RoundPhase::eligible) {
    (void)submit_command(
        state_runtime,
        chain,
        options.validator_id,
        "FINALIZE_AGGREGATE",
        chain.body_ids[4],
        "mnist-demo-finalize-aggregate",
        10U,
        "ACT-ROOT-FINALIZE",
        trace);
    state = protocol::parse_round_state(state_runtime.state_bytes());
  }
  require(
      state.phase == protocol::RoundPhase::aggregated && state.state_root == chain.body_ids[4],
      "node runtime aggregate state differs from AggregateRootQC");

  const auto recomputed_candidate = delta::apply::compute_candidate(
      chain.context,
      chain.body_ids[4],
      chain.apply_profile,
      chain.parent_state,
      chain.domain_aggregates);
  require(recomputed_candidate == chain.candidate, "production Apply candidate is not reproducible");
  certificates::ChainVerifier verifier(
      chain.context,
      certificates::ValidatorPolicy{
          chain.context.validator_epoch_id, validators(), quorum_threshold});
  const auto apply_qc_id = verifier.verify_apply(
      chain.apply_qc,
      recomputed_candidate,
      chain.body_ids[4],
      certificates::content_id(chain.apply_profile));
  trace.emit(
      "apply_computed",
      "ACT-APPLY-COMPUTE",
      std::nullopt,
      std::nullopt,
      chain.body_ids[4],
      certificates::content_id(recomputed_candidate),
      state.durable_sequence,
      false,
      "ACCEPTED",
      std::nullopt);

  const auto artifact = model_bytes(recomputed_candidate);
  write_atomic(options.applied_model, artifact);
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
      apply_qc_id,
      chain.parent_checkpoint_id,
      recomputed_candidate.next_model_hash,
      recomputed_candidate.next_optimizer_hash,
  };
  const auto disposition = pointer_store.advance(pointer_command, chain.apply_qc);
  const auto& pointer = pointer_store.state();
  require(
      pointer.checkpoint_id == recomputed_candidate.next_model_hash &&
          pointer.optimizer_id == recomputed_candidate.next_optimizer_hash &&
          pointer.apply_qc_id == apply_qc_id && pointer.height == chain.context.height,
      "current pointer did not reach the certified APPLIED state");
  trace.emit(
      "current_pointer_applied",
      "ACT-CURRENT-ADVANCE",
      std::nullopt,
      std::nullopt,
      apply_qc_id,
      pointer.checkpoint_id,
      state.durable_sequence,
      disposition == runtime::PointerDisposition::replay,
      disposition == runtime::PointerDisposition::replay ? "NO_OP" : "FINALIZED",
      std::nullopt);

  std::vector<std::string> quorum_documents;
  quorum_documents.reserve(quorums.size());
  for (const auto& quorum : quorums) {
    quorum_documents.push_back(quorum_json(quorum));
  }
  auto fields = common_result_fields(
      workload, chain, options, "MNIST_DELTA_FINALIZE_RESULT", "APPLIED");
  fields.emplace_back("aggregate_root_qc_id", json_string(chain.body_ids[4]));
  fields.emplace_back("apply_candidate_id", json_string(certificates::content_id(recomputed_candidate)));
  fields.emplace_back("apply_qc_id", json_string(apply_qc_id));
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
  fields.emplace_back("model_hash", json_string(recomputed_candidate.next_model_hash));
  fields.emplace_back("optimizer_hash", json_string(recomputed_candidate.next_optimizer_hash));
  fields.emplace_back("quorum_certificates", json_array(quorum_documents));
  fields.emplace_back(
      "runtime_wal",
      file_reference_json(
          "runtime/runtime.wal", options.node_directory / "runtime" / "runtime.wal", 16U * 1024U * 1024U));
  fields.emplace_back(
      "vote_wal",
      file_reference_json(
          "votes/runtime.wal", options.node_directory / "votes" / "runtime.wal", 16U * 1024U * 1024U));
  const auto document = result_document(std::move(fields));
  write_atomic(options.result, document);
  trace.emit(
      "mode_complete",
      "ACT-CURRENT-ADVANCE",
      std::nullopt,
      std::nullopt,
      apply_qc_id,
      recomputed_candidate.next_model_hash,
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
             {"modes", json_array({json_string("prepare-votes"), json_string("finalize")})},
             {"node_count", std::to_string(validator_count)},
             {"schema_version", json_string("1.0.0")},
             {"type_name", json_string("MNIST_DELTA_NATIVE_NODE_DESCRIPTOR")},
             {"vector_width", std::to_string(vector_width)},
             {"workload_bytes", std::to_string(exact_workload_bytes)},
             {"workload_format", json_string("DMNIST1_INT16_BE_V1")},
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
    return options.mode == "prepare-votes" ? prepare_votes(options) : finalize(options);
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
