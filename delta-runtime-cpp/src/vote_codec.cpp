#include <delta/runtime/vote_codec.hpp>

#include <algorithm>
#include <array>
#include <bit>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <set>
#include <span>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <type_traits>
#include <utility>
#include <vector>

namespace delta::runtime {
namespace {

using Bytes = core::canonical::Bytes;

constexpr std::array<std::byte, 8> policy_magic{
    std::byte{'D'}, std::byte{'V'}, std::byte{'P'}, std::byte{'O'},
    std::byte{'L'}, std::byte{'0'}, std::byte{'0'}, std::byte{'1'}};
constexpr std::array<std::byte, 8> receipt_magic{
    std::byte{'D'}, std::byte{'V'}, std::byte{'R'}, std::byte{'E'},
    std::byte{'C'}, std::byte{'0'}, std::byte{'0'}, std::byte{'1'}};
constexpr std::uint16_t codec_major = 1U;
constexpr std::uint16_t codec_minor = 0U;

[[noreturn]] void reject(const char* message) { throw std::invalid_argument(message); }

void require(bool condition, const char* message) {
  if (!condition) {
    reject(message);
  }
}

[[nodiscard]] bool canonical_ascii(std::string_view value) noexcept {
  return std::all_of(value.begin(), value.end(), [](char value) {
    const auto byte = static_cast<unsigned char>(value);
    return byte >= 0x20U && byte <= 0x7eU;
  });
}

template <typename Integer>
void append_be(Bytes& output, Integer value) {
  static_assert(std::is_unsigned_v<Integer>);
  for (std::size_t offset = sizeof(Integer); offset != 0U; --offset) {
    const auto shift = static_cast<unsigned>((offset - 1U) * 8U);
    output.push_back(static_cast<std::byte>((value >> shift) & static_cast<Integer>(0xffU)));
  }
}

void append_magic(Bytes& output, const std::array<std::byte, 8>& magic) {
  output.insert(output.end(), magic.begin(), magic.end());
  append_be(output, codec_major);
  append_be(output, codec_minor);
  append_be(output, std::uint32_t{0U});
}

void append_text(Bytes& output, std::string_view value, std::size_t maximum) {
  require(value.size() <= maximum, "vote codec text exceeds its frozen bound");
  require(value.size() <= std::numeric_limits<std::uint32_t>::max(), "vote codec text is too large");
  require(canonical_ascii(value), "vote codec text is not canonical ASCII");
  append_be(output, static_cast<std::uint32_t>(value.size()));
  for (const char character : value) {
    output.push_back(static_cast<std::byte>(static_cast<unsigned char>(character)));
  }
}

void append_bytes(Bytes& output, std::span<const std::byte> value, std::size_t maximum) {
  require(value.size() <= maximum, "vote codec byte string exceeds its frozen bound");
  require(value.size() <= std::numeric_limits<std::uint32_t>::max(), "vote codec bytes are too large");
  append_be(output, static_cast<std::uint32_t>(value.size()));
  output.insert(output.end(), value.begin(), value.end());
}

class Reader final {
 public:
  Reader(std::span<const std::byte> input, std::size_t maximum)
      : input_(input) {
    require(input.size() <= maximum, "vote codec envelope exceeds its frozen bound");
  }

  void require_header(const std::array<std::byte, 8>& expected) {
    require(remaining() >= 16U, "vote codec header is truncated");
    require(
        std::equal(expected.begin(), expected.end(), input_.begin()),
        "vote codec magic is invalid");
    offset_ = expected.size();
    require(read<std::uint16_t>() == codec_major, "vote codec major version is unsupported");
    require(read<std::uint16_t>() == codec_minor, "vote codec minor version is unsupported");
    require(read<std::uint32_t>() == 0U, "vote codec reserved header is nonzero");
  }

  template <typename Integer>
  [[nodiscard]] Integer read() {
    static_assert(std::is_unsigned_v<Integer>);
    require(remaining() >= sizeof(Integer), "vote codec integer is truncated");
    Integer result = 0U;
    for (std::size_t index = 0U; index < sizeof(Integer); ++index) {
      result = static_cast<Integer>(
          (result << 8U) | std::to_integer<unsigned>(input_[offset_ + index]));
    }
    offset_ += sizeof(Integer);
    return result;
  }

  [[nodiscard]] std::string text(std::size_t maximum) {
    const auto length = read<std::uint32_t>();
    require(length <= maximum, "vote codec text exceeds its frozen bound");
    require(remaining() >= length, "vote codec text is truncated");
    std::string result;
    result.reserve(length);
    for (std::size_t index = 0U; index < length; ++index) {
      result.push_back(static_cast<char>(std::to_integer<unsigned char>(input_[offset_ + index])));
    }
    offset_ += length;
    require(canonical_ascii(result), "vote codec text is not canonical ASCII");
    return result;
  }

  [[nodiscard]] Bytes bytes(std::size_t maximum) {
    const auto length = read<std::uint32_t>();
    require(length <= maximum, "vote codec byte string exceeds its frozen bound");
    require(remaining() >= length, "vote codec byte string is truncated");
    Bytes result(
        input_.begin() + static_cast<std::ptrdiff_t>(offset_),
        input_.begin() + static_cast<std::ptrdiff_t>(offset_ + length));
    offset_ += length;
    return result;
  }

  void reserved(std::size_t count) {
    require(remaining() >= count, "vote codec reserved bytes are truncated");
    for (std::size_t index = 0U; index < count; ++index) {
      require(input_[offset_ + index] == std::byte{0U}, "vote codec reserved byte is nonzero");
    }
    offset_ += count;
  }

  void finish() const { require(offset_ == input_.size(), "vote codec has trailing bytes"); }

  [[nodiscard]] std::size_t available() const noexcept { return remaining(); }

 private:
  [[nodiscard]] std::size_t remaining() const noexcept { return input_.size() - offset_; }

  std::span<const std::byte> input_;
  std::size_t offset_ = 0U;
};

void append_parents(Bytes& output, const core::consensus::VoteParentState& parents) {
  append_text(output, parents.round_config_id, max_vote_policy_v1_text_bytes);
  append_text(output, parents.parent_checkpoint_id, max_vote_policy_v1_text_bytes);
  append_text(output, parents.input_set_certificate_id, max_vote_policy_v1_text_bytes);
  append_text(output, parents.seed_transcript_id, max_vote_policy_v1_text_bytes);
  append_text(output, parents.norm_evidence_id, max_vote_policy_v1_text_bytes);
  append_text(output, parents.eligibility_certificate_id, max_vote_policy_v1_text_bytes);
  append_text(output, parents.aggregation_plan_certificate_id, max_vote_policy_v1_text_bytes);
  append_text(output, parents.parameter_matrix_root, max_vote_policy_v1_text_bytes);
  append_text(output, parents.aggregate_root_certificate_id, max_vote_policy_v1_text_bytes);
  append_text(output, parents.apply_profile_id, max_vote_policy_v1_text_bytes);
  append_text(output, parents.apply_candidate_id, max_vote_policy_v1_text_bytes);
  append_text(output, parents.last_finalized_certificate_id, max_vote_policy_v1_text_bytes);
  append_text(output, parents.domain_id, max_vote_policy_v1_text_bytes);
  append_text(output, parents.shard_id, max_vote_policy_v1_text_bytes);
  append_text(output, parents.reason_code, max_vote_policy_v1_text_bytes);
}

[[nodiscard]] core::consensus::VoteParentState read_parents(Reader& reader) {
  return core::consensus::VoteParentState{
      reader.text(max_vote_policy_v1_text_bytes),
      reader.text(max_vote_policy_v1_text_bytes),
      reader.text(max_vote_policy_v1_text_bytes),
      reader.text(max_vote_policy_v1_text_bytes),
      reader.text(max_vote_policy_v1_text_bytes),
      reader.text(max_vote_policy_v1_text_bytes),
      reader.text(max_vote_policy_v1_text_bytes),
      reader.text(max_vote_policy_v1_text_bytes),
      reader.text(max_vote_policy_v1_text_bytes),
      reader.text(max_vote_policy_v1_text_bytes),
      reader.text(max_vote_policy_v1_text_bytes),
      reader.text(max_vote_policy_v1_text_bytes),
      reader.text(max_vote_policy_v1_text_bytes),
      reader.text(max_vote_policy_v1_text_bytes),
      reader.text(max_vote_policy_v1_text_bytes),
  };
}

void append_bool(Bytes& output, bool value) {
  output.push_back(value ? std::byte{1U} : std::byte{0U});
}

[[nodiscard]] bool read_bool(Reader& reader) {
  const auto value = reader.read<std::uint8_t>();
  require(value <= 1U, "vote codec boolean is not canonical");
  return value != 0U;
}

template <typename Value, typename Encoder>
void append_vector(Bytes& output, const std::vector<Value>& values, Encoder encoder) {
  require(
      values.size() <= certificates::max_certificate_entries,
      "vote authority collection exceeds its frozen bound");
  append_be(output, static_cast<std::uint32_t>(values.size()));
  for (const auto& value : values) {
    encoder(output, value);
  }
}

template <typename Value, typename Decoder>
[[nodiscard]] std::vector<Value> read_vector(Reader& reader, Decoder decoder) {
  const auto count = reader.read<std::uint32_t>();
  require(
      count <= certificates::max_certificate_entries,
      "vote authority collection exceeds its frozen bound");
  std::vector<Value> values;
  values.reserve(count);
  for (std::uint32_t index = 0U; index < count; ++index) {
    values.push_back(decoder(reader));
  }
  return values;
}

void append_text_vector(Bytes& output, const std::vector<std::string>& values) {
  append_vector(output, values, [](Bytes& bytes, const std::string& value) {
    append_text(bytes, value, max_vote_policy_v1_text_bytes);
  });
}

[[nodiscard]] std::vector<std::string> read_text_vector(Reader& reader) {
  return read_vector<std::string>(reader, [](Reader& input) {
    return input.text(max_vote_policy_v1_text_bytes);
  });
}

void append_context(Bytes& output, const certificates::Context& value) {
  append_text(output, value.arithmetic_profile_id, max_vote_policy_v1_text_bytes);
  append_be(output, value.height);
  append_text(output, value.parameter_schema_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.round_config_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.round_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.validator_epoch_id, max_vote_policy_v1_text_bytes);
  append_be(output, value.view);
}

[[nodiscard]] certificates::Context read_context(Reader& reader) {
  return certificates::Context{
      reader.text(max_vote_policy_v1_text_bytes),
      reader.read<std::uint64_t>(),
      reader.text(max_vote_policy_v1_text_bytes),
      reader.text(max_vote_policy_v1_text_bytes),
      reader.text(max_vote_policy_v1_text_bytes),
      reader.text(max_vote_policy_v1_text_bytes),
      reader.read<std::uint64_t>(),
  };
}

void append_rational(Bytes& output, const certificates::Rational& value) {
  append_be(output, std::bit_cast<std::uint64_t>(value.numerator));
  append_be(output, value.denominator);
}

[[nodiscard]] certificates::Rational read_rational(Reader& reader) {
  return certificates::Rational{
      std::bit_cast<std::int64_t>(reader.read<std::uint64_t>()),
      reader.read<std::uint64_t>(),
  };
}

void append_input_set(Bytes& output, const certificates::InputSetCertificate& value) {
  append_context(output, value.context);
  append_text(output, value.input_root, max_vote_policy_v1_text_bytes);
  append_be(output, value.quorum_threshold);
  append_text_vector(output, value.signer_ids);
  append_vector(output, value.tuples, [](Bytes& bytes, const certificates::InputTuple& tuple) {
    append_text(bytes, tuple.availability_certificate_id, max_vote_policy_v1_text_bytes);
    append_text(bytes, tuple.commitment_id, max_vote_policy_v1_text_bytes);
    append_text(bytes, tuple.domain_id, max_vote_policy_v1_text_bytes);
    append_text(bytes, tuple.ticket_id, max_vote_policy_v1_text_bytes);
  });
}

[[nodiscard]] certificates::InputSetCertificate read_input_set(Reader& reader) {
  auto result = certificates::InputSetCertificate{};
  result.context = read_context(reader);
  result.input_root = reader.text(max_vote_policy_v1_text_bytes);
  result.quorum_threshold = reader.read<std::uint32_t>();
  result.signer_ids = read_text_vector(reader);
  result.tuples = read_vector<certificates::InputTuple>(reader, [](Reader& input) {
    return certificates::InputTuple{
        input.text(max_vote_policy_v1_text_bytes),
        input.text(max_vote_policy_v1_text_bytes),
        input.text(max_vote_policy_v1_text_bytes),
        input.text(max_vote_policy_v1_text_bytes),
    };
  });
  return result;
}

void append_input_set_body(
    Bytes& output,
    const core::consensus::VoteInputSetBody& value) {
  append_context(output, value.context);
  append_text(output, value.input_root, max_vote_policy_v1_text_bytes);
  append_vector(output, value.tuples, [](Bytes& bytes, const certificates::InputTuple& tuple) {
    append_text(bytes, tuple.availability_certificate_id, max_vote_policy_v1_text_bytes);
    append_text(bytes, tuple.commitment_id, max_vote_policy_v1_text_bytes);
    append_text(bytes, tuple.domain_id, max_vote_policy_v1_text_bytes);
    append_text(bytes, tuple.ticket_id, max_vote_policy_v1_text_bytes);
  });
}

[[nodiscard]] core::consensus::VoteInputSetBody read_input_set_body(Reader& reader) {
  auto result = core::consensus::VoteInputSetBody{};
  result.context = read_context(reader);
  result.input_root = reader.text(max_vote_policy_v1_text_bytes);
  result.tuples = read_vector<certificates::InputTuple>(reader, [](Reader& input) {
    return certificates::InputTuple{
        input.text(max_vote_policy_v1_text_bytes),
        input.text(max_vote_policy_v1_text_bytes),
        input.text(max_vote_policy_v1_text_bytes),
        input.text(max_vote_policy_v1_text_bytes),
    };
  });
  return result;
}

void append_seed(Bytes& output, const certificates::SeedTranscript& value) {
  append_context(output, value.context);
  append_text(output, value.input_set_certificate_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.seed_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.seed_profile_id, max_vote_policy_v1_text_bytes);
  append_text_vector(output, value.share_ids);
}

[[nodiscard]] certificates::SeedTranscript read_seed(Reader& reader) {
  auto result = certificates::SeedTranscript{};
  result.context = read_context(reader);
  result.input_set_certificate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.seed_id = reader.text(max_vote_policy_v1_text_bytes);
  result.seed_profile_id = reader.text(max_vote_policy_v1_text_bytes);
  result.share_ids = read_text_vector(reader);
  return result;
}

void append_norm(Bytes& output, const certificates::NormEvidence& value) {
  append_context(output, value.context);
  append_vector(output, value.entries, [](Bytes& bytes, const certificates::NormEntry& entry) {
    append_be(bytes, entry.scale_denominator);
    append_text(bytes, entry.squared_norm, max_vote_policy_v1_text_bytes);
    append_text(bytes, entry.ticket_id, max_vote_policy_v1_text_bytes);
  });
  append_text(output, value.input_set_certificate_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.norm_root, max_vote_policy_v1_text_bytes);
}

[[nodiscard]] certificates::NormEvidence read_norm(Reader& reader) {
  auto result = certificates::NormEvidence{};
  result.context = read_context(reader);
  result.entries = read_vector<certificates::NormEntry>(reader, [](Reader& input) {
    return certificates::NormEntry{
        input.read<std::uint64_t>(),
        input.text(max_vote_policy_v1_text_bytes),
        input.text(max_vote_policy_v1_text_bytes),
    };
  });
  result.input_set_certificate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.norm_root = reader.text(max_vote_policy_v1_text_bytes);
  return result;
}

void append_eligibility(Bytes& output, const certificates::EligibilityCertificate& value) {
  append_context(output, value.context);
  append_vector(
      output,
      value.entries,
      [](Bytes& bytes, const certificates::EligibilityEntry& entry) {
        append_bool(bytes, entry.accepted);
        append_text(bytes, entry.domain_id, max_vote_policy_v1_text_bytes);
        append_rational(bytes, entry.gamma);
        append_text(bytes, entry.reason_code, max_vote_policy_v1_text_bytes);
        append_text(bytes, entry.ticket_id, max_vote_policy_v1_text_bytes);
      });
  append_text(output, value.input_set_certificate_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.norm_evidence_id, max_vote_policy_v1_text_bytes);
  append_be(output, value.quorum_threshold);
  append_text(output, value.robust_profile_id, max_vote_policy_v1_text_bytes);
  append_text_vector(output, value.signer_ids);
}

[[nodiscard]] certificates::EligibilityCertificate read_eligibility(Reader& reader) {
  auto result = certificates::EligibilityCertificate{};
  result.context = read_context(reader);
  result.entries = read_vector<certificates::EligibilityEntry>(reader, [](Reader& input) {
    return certificates::EligibilityEntry{
        read_bool(input),
        input.text(max_vote_policy_v1_text_bytes),
        read_rational(input),
        input.text(max_vote_policy_v1_text_bytes),
        input.text(max_vote_policy_v1_text_bytes),
    };
  });
  result.input_set_certificate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.norm_evidence_id = reader.text(max_vote_policy_v1_text_bytes);
  result.quorum_threshold = reader.read<std::uint32_t>();
  result.robust_profile_id = reader.text(max_vote_policy_v1_text_bytes);
  result.signer_ids = read_text_vector(reader);
  return result;
}

void append_eligibility_body(
    Bytes& output,
    const core::consensus::VoteEligibilityBody& value) {
  append_context(output, value.context);
  append_vector(
      output,
      value.entries,
      [](Bytes& bytes, const certificates::EligibilityEntry& entry) {
        append_bool(bytes, entry.accepted);
        append_text(bytes, entry.domain_id, max_vote_policy_v1_text_bytes);
        append_rational(bytes, entry.gamma);
        append_text(bytes, entry.reason_code, max_vote_policy_v1_text_bytes);
        append_text(bytes, entry.ticket_id, max_vote_policy_v1_text_bytes);
      });
  append_text(output, value.input_set_certificate_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.norm_evidence_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.robust_profile_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.seed_transcript_id, max_vote_policy_v1_text_bytes);
}

[[nodiscard]] core::consensus::VoteEligibilityBody read_eligibility_body(
    Reader& reader) {
  auto result = core::consensus::VoteEligibilityBody{};
  result.context = read_context(reader);
  result.entries = read_vector<certificates::EligibilityEntry>(reader, [](Reader& input) {
    return certificates::EligibilityEntry{
        read_bool(input),
        input.text(max_vote_policy_v1_text_bytes),
        read_rational(input),
        input.text(max_vote_policy_v1_text_bytes),
        input.text(max_vote_policy_v1_text_bytes),
    };
  });
  result.input_set_certificate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.norm_evidence_id = reader.text(max_vote_policy_v1_text_bytes);
  result.robust_profile_id = reader.text(max_vote_policy_v1_text_bytes);
  result.seed_transcript_id = reader.text(max_vote_policy_v1_text_bytes);
  return result;
}

void append_plan(Bytes& output, const certificates::AggregationPlanCertificate& value) {
  append_context(output, value.context);
  append_text(output, value.accumulator_proof_id, max_vote_policy_v1_text_bytes);
  append_vector(
      output,
      value.bucket_assignments,
      [](Bytes& bytes, const certificates::BucketAssignment& assignment) {
        append_text(bytes, assignment.bucket_id, max_vote_policy_v1_text_bytes);
        append_text(bytes, assignment.ticket_id, max_vote_policy_v1_text_bytes);
      });
  append_text(output, value.eligibility_certificate_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.input_set_certificate_id, max_vote_policy_v1_text_bytes);
  append_be(output, value.iteration_count);
  append_be(output, value.quorum_threshold);
  append_text(output, value.seed_transcript_id, max_vote_policy_v1_text_bytes);
  append_text_vector(output, value.signer_ids);
  append_text(output, value.transcript_root, max_vote_policy_v1_text_bytes);
  append_vector(output, value.weights, [](Bytes& bytes, const certificates::Weight& weight) {
    append_rational(bytes, weight.alpha);
    append_text(bytes, weight.ticket_id, max_vote_policy_v1_text_bytes);
  });
}

[[nodiscard]] certificates::AggregationPlanCertificate read_plan(Reader& reader) {
  auto result = certificates::AggregationPlanCertificate{};
  result.context = read_context(reader);
  result.accumulator_proof_id = reader.text(max_vote_policy_v1_text_bytes);
  result.bucket_assignments =
      read_vector<certificates::BucketAssignment>(reader, [](Reader& input) {
        return certificates::BucketAssignment{
            input.text(max_vote_policy_v1_text_bytes),
            input.text(max_vote_policy_v1_text_bytes),
        };
      });
  result.eligibility_certificate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.input_set_certificate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.iteration_count = reader.read<std::uint32_t>();
  result.quorum_threshold = reader.read<std::uint32_t>();
  result.seed_transcript_id = reader.text(max_vote_policy_v1_text_bytes);
  result.signer_ids = read_text_vector(reader);
  result.transcript_root = reader.text(max_vote_policy_v1_text_bytes);
  result.weights = read_vector<certificates::Weight>(reader, [](Reader& input) {
    return certificates::Weight{
        read_rational(input), input.text(max_vote_policy_v1_text_bytes)};
  });
  return result;
}

void append_plan_body(
    Bytes& output,
    const core::consensus::VoteAggregationPlanBody& value) {
  append_context(output, value.context);
  append_text(output, value.accumulator_proof_id, max_vote_policy_v1_text_bytes);
  append_vector(
      output,
      value.bucket_assignments,
      [](Bytes& bytes, const certificates::BucketAssignment& assignment) {
        append_text(bytes, assignment.bucket_id, max_vote_policy_v1_text_bytes);
        append_text(bytes, assignment.ticket_id, max_vote_policy_v1_text_bytes);
      });
  append_text(output, value.eligibility_certificate_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.input_set_certificate_id, max_vote_policy_v1_text_bytes);
  append_be(output, value.iteration_count);
  append_text(output, value.seed_transcript_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.transcript_root, max_vote_policy_v1_text_bytes);
  append_vector(output, value.weights, [](Bytes& bytes, const certificates::Weight& weight) {
    append_rational(bytes, weight.alpha);
    append_text(bytes, weight.ticket_id, max_vote_policy_v1_text_bytes);
  });
}

[[nodiscard]] core::consensus::VoteAggregationPlanBody read_plan_body(
    Reader& reader) {
  auto result = core::consensus::VoteAggregationPlanBody{};
  result.context = read_context(reader);
  result.accumulator_proof_id = reader.text(max_vote_policy_v1_text_bytes);
  result.bucket_assignments =
      read_vector<certificates::BucketAssignment>(reader, [](Reader& input) {
        return certificates::BucketAssignment{
            input.text(max_vote_policy_v1_text_bytes),
            input.text(max_vote_policy_v1_text_bytes),
        };
      });
  result.eligibility_certificate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.input_set_certificate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.iteration_count = reader.read<std::uint32_t>();
  result.seed_transcript_id = reader.text(max_vote_policy_v1_text_bytes);
  result.transcript_root = reader.text(max_vote_policy_v1_text_bytes);
  result.weights = read_vector<certificates::Weight>(reader, [](Reader& input) {
    return certificates::Weight{
        read_rational(input), input.text(max_vote_policy_v1_text_bytes)};
  });
  return result;
}

void append_shard_key(Bytes& output, const certificates::ShardKey& value) {
  append_text(output, value.domain_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.shard_id, max_vote_policy_v1_text_bytes);
}

[[nodiscard]] certificates::ShardKey read_shard_key(Reader& reader) {
  return certificates::ShardKey{
      reader.text(max_vote_policy_v1_text_bytes),
      reader.text(max_vote_policy_v1_text_bytes),
  };
}

void append_parameter(Bytes& output, const certificates::ParameterShardQc& value) {
  append_context(output, value.context);
  append_text(output, value.aggregation_plan_certificate_id, max_vote_policy_v1_text_bytes);
  append_be(output, value.denominator);
  append_text(output, value.domain_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.eligibility_certificate_id, max_vote_policy_v1_text_bytes);
  append_text_vector(output, value.input_leaf_ids);
  append_text(output, value.input_set_certificate_id, max_vote_policy_v1_text_bytes);
  append_be(output, value.quorum_threshold);
  append_text_vector(output, value.result_numerators);
  append_text(output, value.shard_id, max_vote_policy_v1_text_bytes);
  append_text_vector(output, value.signer_ids);
}

[[nodiscard]] certificates::ParameterShardQc read_parameter(Reader& reader) {
  auto result = certificates::ParameterShardQc{};
  result.context = read_context(reader);
  result.aggregation_plan_certificate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.denominator = reader.read<std::uint64_t>();
  result.domain_id = reader.text(max_vote_policy_v1_text_bytes);
  result.eligibility_certificate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.input_leaf_ids = read_text_vector(reader);
  result.input_set_certificate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.quorum_threshold = reader.read<std::uint32_t>();
  result.result_numerators = read_text_vector(reader);
  result.shard_id = reader.text(max_vote_policy_v1_text_bytes);
  result.signer_ids = read_text_vector(reader);
  return result;
}

void append_parameter_body(
    Bytes& output,
    const core::consensus::VoteParameterBody& value) {
  append_context(output, value.context);
  append_text(output, value.aggregation_plan_certificate_id, max_vote_policy_v1_text_bytes);
  append_be(output, value.denominator);
  append_text(output, value.domain_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.eligibility_certificate_id, max_vote_policy_v1_text_bytes);
  append_text_vector(output, value.input_leaf_ids);
  append_text(output, value.input_set_certificate_id, max_vote_policy_v1_text_bytes);
  append_text_vector(output, value.result_numerators);
  append_text(output, value.shard_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.vote_context_id, max_vote_policy_v1_text_bytes);
}

[[nodiscard]] core::consensus::VoteParameterBody read_parameter_body(
    Reader& reader) {
  auto result = core::consensus::VoteParameterBody{};
  result.context = read_context(reader);
  result.aggregation_plan_certificate_id =
      reader.text(max_vote_policy_v1_text_bytes);
  result.denominator = reader.read<std::uint64_t>();
  result.domain_id = reader.text(max_vote_policy_v1_text_bytes);
  result.eligibility_certificate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.input_leaf_ids = read_text_vector(reader);
  result.input_set_certificate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.result_numerators = read_text_vector(reader);
  result.shard_id = reader.text(max_vote_policy_v1_text_bytes);
  result.vote_context_id = reader.text(max_vote_policy_v1_text_bytes);
  return result;
}

void append_root(Bytes& output, const certificates::AggregateRootQc& value) {
  append_context(output, value.context);
  append_text(output, value.aggregation_plan_certificate_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.eligibility_certificate_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.input_set_certificate_id, max_vote_policy_v1_text_bytes);
  append_vector(output, value.leaves, [](Bytes& bytes, const certificates::RootLeaf& leaf) {
    append_text(bytes, leaf.domain_id, max_vote_policy_v1_text_bytes);
    append_text(bytes, leaf.parameter_shard_qc_id, max_vote_policy_v1_text_bytes);
    append_text(bytes, leaf.shard_id, max_vote_policy_v1_text_bytes);
  });
  append_text(output, value.merkle_root, max_vote_policy_v1_text_bytes);
  append_be(output, value.quorum_threshold);
  append_vector(output, value.required_keys, append_shard_key);
  append_text_vector(output, value.signer_ids);
}

[[nodiscard]] certificates::AggregateRootQc read_root(Reader& reader) {
  auto result = certificates::AggregateRootQc{};
  result.context = read_context(reader);
  result.aggregation_plan_certificate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.eligibility_certificate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.input_set_certificate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.leaves = read_vector<certificates::RootLeaf>(reader, [](Reader& input) {
    return certificates::RootLeaf{
        input.text(max_vote_policy_v1_text_bytes),
        input.text(max_vote_policy_v1_text_bytes),
        input.text(max_vote_policy_v1_text_bytes),
    };
  });
  result.merkle_root = reader.text(max_vote_policy_v1_text_bytes);
  result.quorum_threshold = reader.read<std::uint32_t>();
  result.required_keys = read_vector<certificates::ShardKey>(reader, read_shard_key);
  result.signer_ids = read_text_vector(reader);
  return result;
}

void append_root_body(
    Bytes& output,
    const core::consensus::VoteAggregateRootBody& value) {
  append_context(output, value.context);
  append_text(output, value.aggregation_plan_certificate_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.eligibility_certificate_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.input_set_certificate_id, max_vote_policy_v1_text_bytes);
  append_vector(output, value.leaves, [](Bytes& bytes, const certificates::RootLeaf& leaf) {
    append_text(bytes, leaf.domain_id, max_vote_policy_v1_text_bytes);
    append_text(bytes, leaf.parameter_shard_qc_id, max_vote_policy_v1_text_bytes);
    append_text(bytes, leaf.shard_id, max_vote_policy_v1_text_bytes);
  });
  append_text(output, value.merkle_root, max_vote_policy_v1_text_bytes);
  append_vector(output, value.required_keys, append_shard_key);
}

[[nodiscard]] core::consensus::VoteAggregateRootBody read_root_body(
    Reader& reader) {
  auto result = core::consensus::VoteAggregateRootBody{};
  result.context = read_context(reader);
  result.aggregation_plan_certificate_id =
      reader.text(max_vote_policy_v1_text_bytes);
  result.eligibility_certificate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.input_set_certificate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.leaves = read_vector<certificates::RootLeaf>(reader, [](Reader& input) {
    return certificates::RootLeaf{
        input.text(max_vote_policy_v1_text_bytes),
        input.text(max_vote_policy_v1_text_bytes),
        input.text(max_vote_policy_v1_text_bytes),
    };
  });
  result.merkle_root = reader.text(max_vote_policy_v1_text_bytes);
  result.required_keys = read_vector<certificates::ShardKey>(reader, read_shard_key);
  return result;
}

void append_apply_profile(Bytes& output, const certificates::ApplyArithmeticProfile& value) {
  append_text(output, value.accumulator_proof_id, max_vote_policy_v1_text_bytes);
  append_vector(
      output,
      value.domain_weights,
      [](Bytes& bytes, const certificates::DomainWeight& weight) {
        append_text(bytes, weight.domain_id, max_vote_policy_v1_text_bytes);
        append_rational(bytes, weight.pi);
      });
  append_rational(output, value.learning_rate);
  append_rational(output, value.momentum);
  append_bool(output, value.nesterov);
  append_text(output, value.rounding, max_vote_policy_v1_text_bytes);
  append_rational(output, value.weight_decay);
}

[[nodiscard]] certificates::ApplyArithmeticProfile read_apply_profile(Reader& reader) {
  auto result = certificates::ApplyArithmeticProfile{};
  result.accumulator_proof_id = reader.text(max_vote_policy_v1_text_bytes);
  result.domain_weights = read_vector<certificates::DomainWeight>(reader, [](Reader& input) {
    return certificates::DomainWeight{
        input.text(max_vote_policy_v1_text_bytes), read_rational(input)};
  });
  result.learning_rate = read_rational(reader);
  result.momentum = read_rational(reader);
  result.nesterov = read_bool(reader);
  result.rounding = reader.text(max_vote_policy_v1_text_bytes);
  result.weight_decay = read_rational(reader);
  return result;
}

void append_apply_candidate(Bytes& output, const certificates::ApplyCandidate& value) {
  append_context(output, value.context);
  append_text(output, value.aggregate_root_qc_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.apply_arithmetic_profile_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.next_model_hash, max_vote_policy_v1_text_bytes);
  append_text_vector(output, value.next_model_values);
  append_text(output, value.next_optimizer_hash, max_vote_policy_v1_text_bytes);
  append_text_vector(output, value.next_optimizer_values);
  append_text(output, value.parent_checkpoint_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.parent_optimizer_hash, max_vote_policy_v1_text_bytes);
}

[[nodiscard]] certificates::ApplyCandidate read_apply_candidate(Reader& reader) {
  auto result = certificates::ApplyCandidate{};
  result.context = read_context(reader);
  result.aggregate_root_qc_id = reader.text(max_vote_policy_v1_text_bytes);
  result.apply_arithmetic_profile_id = reader.text(max_vote_policy_v1_text_bytes);
  result.next_model_hash = reader.text(max_vote_policy_v1_text_bytes);
  result.next_model_values = read_text_vector(reader);
  result.next_optimizer_hash = reader.text(max_vote_policy_v1_text_bytes);
  result.next_optimizer_values = read_text_vector(reader);
  result.parent_checkpoint_id = reader.text(max_vote_policy_v1_text_bytes);
  result.parent_optimizer_hash = reader.text(max_vote_policy_v1_text_bytes);
  return result;
}

void append_apply_qc(Bytes& output, const certificates::ApplyQc& value) {
  append_context(output, value.context);
  append_text(output, value.aggregate_root_qc_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.apply_arithmetic_profile_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.apply_candidate_id, max_vote_policy_v1_text_bytes);
  append_text(output, value.next_model_hash, max_vote_policy_v1_text_bytes);
  append_text(output, value.next_optimizer_hash, max_vote_policy_v1_text_bytes);
  append_text(output, value.parent_checkpoint_id, max_vote_policy_v1_text_bytes);
  append_be(output, value.quorum_threshold);
  append_text_vector(output, value.signer_ids);
}

[[nodiscard]] certificates::ApplyQc read_apply_qc(Reader& reader) {
  auto result = certificates::ApplyQc{};
  result.context = read_context(reader);
  result.aggregate_root_qc_id = reader.text(max_vote_policy_v1_text_bytes);
  result.apply_arithmetic_profile_id = reader.text(max_vote_policy_v1_text_bytes);
  result.apply_candidate_id = reader.text(max_vote_policy_v1_text_bytes);
  result.next_model_hash = reader.text(max_vote_policy_v1_text_bytes);
  result.next_optimizer_hash = reader.text(max_vote_policy_v1_text_bytes);
  result.parent_checkpoint_id = reader.text(max_vote_policy_v1_text_bytes);
  result.quorum_threshold = reader.read<std::uint32_t>();
  result.signer_ids = read_text_vector(reader);
  return result;
}

void append_snapshot(Bytes& output, const core::consensus::VoteAdmissionSnapshot& snapshot) {
  append_text(output, snapshot.state_id, max_vote_policy_v1_text_bytes);
  append_text(output, snapshot.parameter_schema_id, max_vote_policy_v1_text_bytes);
  append_text(output, snapshot.arithmetic_profile_id, max_vote_policy_v1_text_bytes);
  append_text(output, snapshot.required_accumulator_proof_id, max_vote_policy_v1_text_bytes);
  append_text_vector(output, snapshot.proposed_round_config_ids);
  append_text_vector(output, snapshot.finalized_round_config_ids);
  append_text_vector(output, snapshot.closed_input_set_ids);
  append_vector(output, snapshot.input_set_bodies, append_input_set_body);
  append_vector(output, snapshot.input_set_certificates, append_input_set);
  append_text_vector(output, snapshot.finalized_input_set_ids);
  append_vector(output, snapshot.seed_transcripts, append_seed);
  append_vector(output, snapshot.norm_evidence, append_norm);
  append_vector(output, snapshot.eligibility_bodies, append_eligibility_body);
  append_vector(
      output,
      snapshot.eligibility_certificates,
      [](Bytes& bytes, const core::consensus::VoteFinalizedEligibility& value) {
        append_eligibility(bytes, value.certificate);
        append_text(bytes, value.seed_transcript_id, max_vote_policy_v1_text_bytes);
      });
  append_text_vector(output, snapshot.finalized_eligibility_ids);
  append_vector(output, snapshot.aggregation_plan_bodies, append_plan_body);
  append_vector(output, snapshot.aggregation_plan_certificates, append_plan);
  append_text_vector(output, snapshot.finalized_aggregation_plan_ids);
  append_vector(output, snapshot.parameter_bodies, append_parameter_body);
  append_vector(output, snapshot.parameter_qcs, append_parameter);
  append_text_vector(output, snapshot.finalized_parameter_ids);
  append_vector(output, snapshot.required_parameter_keys, append_shard_key);
  append_vector(output, snapshot.aggregate_root_bodies, append_root_body);
  append_vector(output, snapshot.aggregate_root_qcs, append_root);
  append_text_vector(output, snapshot.finalized_aggregate_root_ids);
  append_vector(output, snapshot.apply_profiles, append_apply_profile);
  append_vector(output, snapshot.apply_candidates, append_apply_candidate);
  append_vector(
      output,
      snapshot.apply_qcs,
      [](Bytes& bytes, const core::consensus::VoteFinalizedApply& value) {
        append_apply_qc(bytes, value.certificate);
        append_apply_candidate(bytes, value.candidate);
      });
  append_text_vector(output, snapshot.finalized_apply_ids);
  append_vector(
      output,
      snapshot.timeout_observations,
      [](Bytes& bytes, const core::consensus::VoteTimeoutObservation& value) {
        append_text(bytes, value.round_id, max_vote_policy_v1_text_bytes);
        append_be(bytes, value.height);
        append_be(bytes, value.view);
      });
  append_vector(
      output,
      snapshot.view_change_bodies,
      [](Bytes& bytes, const core::consensus::VoteViewChangeBody& value) {
        append_text(bytes, value.round_id, max_vote_policy_v1_text_bytes);
        append_be(bytes, value.height);
        append_be(bytes, value.from_view);
        append_be(bytes, value.to_view);
        append_be(bytes, value.soft_deadline_tick);
      });
  append_vector(
      output,
      snapshot.abort_requests,
      [](Bytes& bytes, const core::consensus::VoteAbortRequest& value) {
        append_text(bytes, value.round_id, max_vote_policy_v1_text_bytes);
        append_text(bytes, value.reason_code, max_vote_policy_v1_text_bytes);
      });
  append_vector(
      output,
      snapshot.abort_bodies,
      [](Bytes& bytes, const core::consensus::VoteAbortBody& value) {
        append_text(bytes, value.round_id, max_vote_policy_v1_text_bytes);
        append_text(bytes, value.validator_epoch_id, max_vote_policy_v1_text_bytes);
        append_be(bytes, value.height);
        append_be(bytes, value.view);
        append_be(bytes, value.hard_deadline_tick);
        append_text(bytes, value.parent_checkpoint_id, max_vote_policy_v1_text_bytes);
        append_text(bytes, value.reason_code, max_vote_policy_v1_text_bytes);
        append_text_vector(bytes, value.round_config_ids);
        append_text_vector(bytes, value.input_set_ids);
        append_text_vector(bytes, value.eligibility_ids);
        append_text_vector(bytes, value.aggregation_plan_ids);
        append_text_vector(bytes, value.parameter_ids);
        append_text_vector(bytes, value.aggregate_root_ids);
        append_text_vector(bytes, value.apply_ids);
      });
}

[[nodiscard]] core::consensus::VoteAdmissionSnapshot read_snapshot(Reader& reader) {
  auto snapshot = core::consensus::VoteAdmissionSnapshot{};
  snapshot.state_id = reader.text(max_vote_policy_v1_text_bytes);
  snapshot.parameter_schema_id = reader.text(max_vote_policy_v1_text_bytes);
  snapshot.arithmetic_profile_id = reader.text(max_vote_policy_v1_text_bytes);
  snapshot.required_accumulator_proof_id = reader.text(max_vote_policy_v1_text_bytes);
  snapshot.proposed_round_config_ids = read_text_vector(reader);
  snapshot.finalized_round_config_ids = read_text_vector(reader);
  snapshot.closed_input_set_ids = read_text_vector(reader);
  snapshot.input_set_bodies =
      read_vector<core::consensus::VoteInputSetBody>(reader, read_input_set_body);
  snapshot.input_set_certificates =
      read_vector<certificates::InputSetCertificate>(reader, read_input_set);
  snapshot.finalized_input_set_ids = read_text_vector(reader);
  snapshot.seed_transcripts = read_vector<certificates::SeedTranscript>(reader, read_seed);
  snapshot.norm_evidence = read_vector<certificates::NormEvidence>(reader, read_norm);
  snapshot.eligibility_bodies =
      read_vector<core::consensus::VoteEligibilityBody>(reader, read_eligibility_body);
  snapshot.eligibility_certificates =
      read_vector<core::consensus::VoteFinalizedEligibility>(reader, [](Reader& input) {
        return core::consensus::VoteFinalizedEligibility{
            read_eligibility(input), input.text(max_vote_policy_v1_text_bytes)};
      });
  snapshot.finalized_eligibility_ids = read_text_vector(reader);
  snapshot.aggregation_plan_bodies =
      read_vector<core::consensus::VoteAggregationPlanBody>(reader, read_plan_body);
  snapshot.aggregation_plan_certificates =
      read_vector<certificates::AggregationPlanCertificate>(reader, read_plan);
  snapshot.finalized_aggregation_plan_ids = read_text_vector(reader);
  snapshot.parameter_bodies =
      read_vector<core::consensus::VoteParameterBody>(reader, read_parameter_body);
  snapshot.parameter_qcs =
      read_vector<certificates::ParameterShardQc>(reader, read_parameter);
  snapshot.finalized_parameter_ids = read_text_vector(reader);
  snapshot.required_parameter_keys =
      read_vector<certificates::ShardKey>(reader, read_shard_key);
  snapshot.aggregate_root_bodies =
      read_vector<core::consensus::VoteAggregateRootBody>(reader, read_root_body);
  snapshot.aggregate_root_qcs =
      read_vector<certificates::AggregateRootQc>(reader, read_root);
  snapshot.finalized_aggregate_root_ids = read_text_vector(reader);
  snapshot.apply_profiles =
      read_vector<certificates::ApplyArithmeticProfile>(reader, read_apply_profile);
  snapshot.apply_candidates =
      read_vector<certificates::ApplyCandidate>(reader, read_apply_candidate);
  snapshot.apply_qcs =
      read_vector<core::consensus::VoteFinalizedApply>(reader, [](Reader& input) {
        return core::consensus::VoteFinalizedApply{
            read_apply_qc(input), read_apply_candidate(input)};
      });
  snapshot.finalized_apply_ids = read_text_vector(reader);
  snapshot.timeout_observations =
      read_vector<core::consensus::VoteTimeoutObservation>(reader, [](Reader& input) {
        return core::consensus::VoteTimeoutObservation{
            input.text(max_vote_policy_v1_text_bytes),
            input.read<std::uint64_t>(),
            input.read<std::uint64_t>(),
        };
      });
  snapshot.view_change_bodies =
      read_vector<core::consensus::VoteViewChangeBody>(reader, [](Reader& input) {
        return core::consensus::VoteViewChangeBody{
            input.text(max_vote_policy_v1_text_bytes),
            input.read<std::uint64_t>(),
            input.read<std::uint64_t>(),
            input.read<std::uint64_t>(),
            input.read<std::uint64_t>(),
        };
      });
  snapshot.abort_requests =
      read_vector<core::consensus::VoteAbortRequest>(reader, [](Reader& input) {
        return core::consensus::VoteAbortRequest{
            input.text(max_vote_policy_v1_text_bytes),
            input.text(max_vote_policy_v1_text_bytes),
        };
      });
  snapshot.abort_bodies =
      read_vector<core::consensus::VoteAbortBody>(reader, [](Reader& input) {
        auto value = core::consensus::VoteAbortBody{};
        value.round_id = input.text(max_vote_policy_v1_text_bytes);
        value.validator_epoch_id = input.text(max_vote_policy_v1_text_bytes);
        value.height = input.read<std::uint64_t>();
        value.view = input.read<std::uint64_t>();
        value.hard_deadline_tick = input.read<std::uint64_t>();
        value.parent_checkpoint_id = input.text(max_vote_policy_v1_text_bytes);
        value.reason_code = input.text(max_vote_policy_v1_text_bytes);
        value.round_config_ids = read_text_vector(input);
        value.input_set_ids = read_text_vector(input);
        value.eligibility_ids = read_text_vector(input);
        value.aggregation_plan_ids = read_text_vector(input);
        value.parameter_ids = read_text_vector(input);
        value.aggregate_root_ids = read_text_vector(input);
        value.apply_ids = read_text_vector(input);
        return value;
      });
  return snapshot;
}

void require_canonical_policy_shape(const core::consensus::VoteAdmissionPolicy& policy) {
  require(
      !policy.validator_ids.empty() &&
          policy.validator_ids.size() <= core::consensus::max_vote_validator_count,
      "vote policy validator count is outside the frozen bound");
  require(
      std::is_sorted(policy.validator_ids.begin(), policy.validator_ids.end()) &&
          std::adjacent_find(policy.validator_ids.begin(), policy.validator_ids.end()) ==
              policy.validator_ids.end(),
      "vote policy validator IDs are not sorted and unique");
  require(
      !policy.candidates.empty() &&
          policy.candidates.size() <= core::consensus::max_vote_candidate_count,
      "vote policy candidate count is outside the frozen bound");
  require(
      policy.role == core::consensus::ValidatorRole::validator,
      "vote policy validator role is invalid");
  require(
      core::consensus::is_configured_abort_reason(policy.configured_abort_reason),
      "vote policy configured abort reason is invalid");
  std::tuple<std::uint64_t, std::uint64_t, std::uint32_t, std::string_view> previous{};
  std::set<std::string_view> contexts;
  bool first = true;
  for (const auto& candidate : policy.candidates) {
    const auto action = static_cast<std::uint32_t>(candidate.action);
    require(
        action >= static_cast<std::uint32_t>(core::consensus::VoteAction::round_config) &&
            action <= static_cast<std::uint32_t>(core::consensus::VoteAction::abort),
        "vote policy candidate action is invalid");
    const auto key = std::make_tuple(
        candidate.height, candidate.view, action, std::string_view(candidate.context_id));
    require(first || previous < key, "vote policy candidates are not strictly ordered");
    require(
        contexts.insert(candidate.context_id).second,
        "vote policy candidate contexts are not globally unique");
    previous = key;
    first = false;
  }
}

[[nodiscard]] std::size_t checked_add(std::size_t left, std::size_t right) {
  require(
      right <= std::numeric_limits<std::size_t>::max() - left,
      "vote receipt size overflow");
  return left + right;
}

}  // namespace

Bytes encode_vote_policy_v1(const core::consensus::VoteAdmissionPolicy& policy) {
  require_canonical_policy_shape(policy);
  Bytes output;
  append_magic(output, policy_magic);
  append_text(output, policy.local_validator_id, max_vote_policy_v1_text_bytes);
  append_text(output, policy.validator_epoch_id, max_vote_policy_v1_text_bytes);
  append_be(output, static_cast<std::uint32_t>(policy.validator_ids.size()));
  for (const auto& validator : policy.validator_ids) {
    append_text(output, validator, max_vote_policy_v1_text_bytes);
  }
  append_be(output, static_cast<std::uint32_t>(policy.role));
  append_text(output, policy.round_id, max_vote_policy_v1_text_bytes);
  append_text(output, policy.round_config_id, max_vote_policy_v1_text_bytes);
  append_text(output, policy.configured_abort_reason, max_vote_policy_v1_text_bytes);
  append_be(output, policy.initial_logical_tick);
  append_be(output, policy.soft_deadline_tick);
  append_be(output, policy.hard_deadline_tick);
  append_snapshot(output, policy.snapshot);
  append_be(output, static_cast<std::uint32_t>(policy.candidates.size()));
  for (const auto& candidate : policy.candidates) {
    append_be(output, static_cast<std::uint32_t>(candidate.action));
    append_text(output, candidate.body_hash, max_vote_policy_v1_text_bytes);
    append_text(output, candidate.context_id, max_vote_policy_v1_text_bytes);
    append_be(output, candidate.height);
    append_be(output, candidate.view);
    append_parents(output, candidate.parents);
  }
  require(output.size() <= max_vote_policy_v1_bytes, "vote policy exceeds its frozen byte bound");
  return output;
}

core::consensus::VoteAdmissionPolicy parse_vote_policy_v1(
    std::span<const std::byte> encoded) {
  Reader reader(encoded, max_vote_policy_v1_bytes);
  reader.require_header(policy_magic);
  core::consensus::VoteAdmissionPolicy policy;
  policy.local_validator_id = reader.text(max_vote_policy_v1_text_bytes);
  policy.validator_epoch_id = reader.text(max_vote_policy_v1_text_bytes);
  const auto validator_count = reader.read<std::uint32_t>();
  require(
      validator_count > 0U && validator_count <= core::consensus::max_vote_validator_count,
      "vote policy validator count is outside the frozen bound");
  constexpr std::size_t minimum_encoded_validator_bytes = sizeof(std::uint32_t);
  require(
      reader.available() >=
          static_cast<std::size_t>(validator_count) * minimum_encoded_validator_bytes,
      "vote policy validator aggregate is truncated");
  policy.validator_ids.reserve(validator_count);
  for (std::uint32_t index = 0U; index < validator_count; ++index) {
    policy.validator_ids.push_back(reader.text(max_vote_policy_v1_text_bytes));
  }
  const auto role = reader.read<std::uint32_t>();
  require(
      role == static_cast<std::uint32_t>(core::consensus::ValidatorRole::validator),
      "vote policy validator role is invalid");
  policy.role = core::consensus::ValidatorRole::validator;
  policy.round_id = reader.text(max_vote_policy_v1_text_bytes);
  policy.round_config_id = reader.text(max_vote_policy_v1_text_bytes);
  policy.configured_abort_reason = reader.text(max_vote_policy_v1_text_bytes);
  policy.initial_logical_tick = reader.read<std::uint64_t>();
  policy.soft_deadline_tick = reader.read<std::uint64_t>();
  policy.hard_deadline_tick = reader.read<std::uint64_t>();
  policy.snapshot = read_snapshot(reader);
  const auto candidate_count = reader.read<std::uint32_t>();
  require(
      candidate_count > 0U && candidate_count <= core::consensus::max_vote_candidate_count,
      "vote policy candidate count is outside the frozen bound");
  constexpr std::size_t minimum_encoded_candidate_bytes =
      sizeof(std::uint32_t) +          // action
      2U * sizeof(std::uint32_t) +     // body and context lengths
      2U * sizeof(std::uint64_t) +     // height and view
      15U * sizeof(std::uint32_t);     // typed-parent lengths
  require(
      reader.available() >=
          static_cast<std::size_t>(candidate_count) * minimum_encoded_candidate_bytes,
      "vote policy candidate aggregate is truncated");
  policy.candidates.reserve(candidate_count);
  for (std::uint32_t index = 0U; index < candidate_count; ++index) {
    const auto action = reader.read<std::uint32_t>();
    require(
        action >= static_cast<std::uint32_t>(core::consensus::VoteAction::round_config) &&
            action <= static_cast<std::uint32_t>(core::consensus::VoteAction::abort),
        "vote policy candidate action is invalid");
    core::consensus::VoteCandidateBinding candidate;
    candidate.action = static_cast<core::consensus::VoteAction>(action);
    candidate.body_hash = reader.text(max_vote_policy_v1_text_bytes);
    candidate.context_id = reader.text(max_vote_policy_v1_text_bytes);
    candidate.height = reader.read<std::uint64_t>();
    candidate.view = reader.read<std::uint64_t>();
    candidate.parents = read_parents(reader);
    policy.candidates.push_back(std::move(candidate));
  }
  reader.finish();
  require_canonical_policy_shape(policy);
  const auto reencoded = encode_vote_policy_v1(policy);
  require(
      reencoded.size() == encoded.size() &&
          std::equal(reencoded.begin(), reencoded.end(), encoded.begin()),
      "vote policy does not have a unique canonical encoding");
  return policy;
}

std::size_t vote_receipt_v1_encoded_size(
    std::size_t frame_size,
    std::string_view vote_id,
    std::string_view context_id) {
  require(frame_size <= max_vote_frame_v1_bytes, "vote frame exceeds its frozen bound");
  constexpr std::size_t max_vote_id_bytes = 71U;
  require(vote_id.size() <= max_vote_id_bytes, "vote ID exceeds its frozen bound");
  require(context_id.size() <= max_vote_policy_v1_text_bytes, "vote context exceeds its frozen bound");
  require(
      canonical_ascii(vote_id) && canonical_ascii(context_id),
      "vote receipt text is not canonical ASCII");
  std::size_t result = 16U + 4U + 1U + 3U + 8U;
  result = checked_add(result, 4U + frame_size);
  result = checked_add(result, 4U + vote_id.size());
  result = checked_add(result, 4U + context_id.size());
  require(
      result - frame_size <= vote_transport_metadata_v1_bytes,
      "vote receipt metadata exceeds its transport reserve");
  require(result <= max_vote_receipt_v1_bytes, "vote receipt exceeds its frozen byte bound");
  return result;
}

Bytes encode_vote_receipt_v1(const VoteReceipt& receipt) {
  const auto vote = core::protocol::parse_vote(receipt.frame);
  require(
      core::protocol::encode(vote) == receipt.frame,
      "vote receipt frame is not the unique canonical vote encoding");
  require(
      core::canonical::content_id(core::canonical::Type::vote, receipt.frame) ==
          receipt.vote_id,
      "vote receipt ID does not identify its frame");
  require(
      vote.durable_sequence == receipt.journal_sequence,
      "vote receipt sequence differs from its frame");
  require(
      core::consensus::parse_vote_action(vote.kind) == receipt.action,
      "vote receipt action differs from its frame");
  require(
      vote.context_id == receipt.context_id,
      "vote receipt context differs from its frame");
  const auto action_value = static_cast<std::uint32_t>(receipt.action);
  require(
      action_value >= static_cast<std::uint32_t>(core::consensus::VoteAction::round_config) &&
          action_value <= static_cast<std::uint32_t>(core::consensus::VoteAction::abort),
      "vote receipt action is invalid");
  require(
      receipt.formal_action_id == core::consensus::vote_formal_action_id(receipt.action),
      "vote receipt formal action differs from its closed action");
  require(receipt.journal_sequence > 0U, "vote receipt durable sequence is zero");
  const auto expected_size = vote_receipt_v1_encoded_size(
      receipt.frame.size(), receipt.vote_id, receipt.context_id);
  Bytes output;
  output.reserve(expected_size);
  append_magic(output, receipt_magic);
  append_be(output, action_value);
  // Replay classification is operational metadata, not part of the durable
  // canonical receipt.  An exact retry, including after process restart, must
  // reproduce byte-identical proof material.
  output.push_back(std::byte{0U});
  output.insert(output.end(), 3U, std::byte{0U});
  append_be(output, receipt.journal_sequence);
  append_bytes(output, receipt.frame, max_vote_frame_v1_bytes);
  append_text(output, receipt.vote_id, max_vote_policy_v1_text_bytes);
  append_text(output, receipt.context_id, max_vote_policy_v1_text_bytes);
  require(output.size() == expected_size, "vote receipt encoded size mismatch");
  return output;
}

DecodedVoteReceiptV1 parse_vote_receipt_v1(std::span<const std::byte> encoded) {
  Reader reader(encoded, max_vote_receipt_v1_bytes);
  reader.require_header(receipt_magic);
  const auto action_value = reader.read<std::uint32_t>();
  require(
      action_value >= static_cast<std::uint32_t>(core::consensus::VoteAction::round_config) &&
          action_value <= static_cast<std::uint32_t>(core::consensus::VoteAction::abort),
      "vote receipt action is invalid");
  const auto replay = reader.read<std::uint8_t>();
  require(replay == 0U, "vote receipt operational replay byte is nonzero");
  reader.reserved(3U);
  DecodedVoteReceiptV1 receipt{
      {},
      {},
      reader.read<std::uint64_t>(),
      static_cast<core::consensus::VoteAction>(action_value),
      {},
      {},
      false,
  };
  require(receipt.journal_sequence > 0U, "vote receipt durable sequence is zero");
  receipt.frame = reader.bytes(max_vote_frame_v1_bytes);
  receipt.vote_id = reader.text(max_vote_policy_v1_text_bytes);
  receipt.formal_action_id = std::string(core::consensus::vote_formal_action_id(receipt.action));
  receipt.context_id = reader.text(max_vote_policy_v1_text_bytes);
  reader.finish();
  require(
      vote_receipt_v1_encoded_size(
          receipt.frame.size(), receipt.vote_id, receipt.context_id) ==
      encoded.size(),
      "vote receipt does not have a unique canonical encoding");
  const auto vote = core::protocol::parse_vote(receipt.frame);
  require(
      core::protocol::encode(vote) == receipt.frame,
      "vote receipt frame is not the unique canonical vote encoding");
  require(
      core::canonical::content_id(core::canonical::Type::vote, receipt.frame) ==
          receipt.vote_id,
      "vote receipt ID does not identify its frame");
  require(
      vote.durable_sequence == receipt.journal_sequence,
      "vote receipt sequence differs from its frame");
  require(
      core::consensus::parse_vote_action(vote.kind) == receipt.action,
      "vote receipt action differs from its frame");
  require(
      vote.context_id == receipt.context_id,
      "vote receipt context differs from its frame");
  return receipt;
}

}  // namespace delta::runtime
