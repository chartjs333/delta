#include <delta/robust/plan.hpp>

#include <delta/core/arithmetic.hpp>
#include <delta/core/canonical.hpp>

#include <algorithm>
#include <cstddef>
#include <cstdint>
#include <cstdlib>
#include <limits>
#include <numeric>
#include <span>
#include <string>
#include <string_view>
#include <tuple>
#include <utility>
#include <vector>

namespace delta::robust {
namespace {

[[noreturn]] void reject(certificates::ErrorCode code, const char* message) {
  throw certificates::CertificateError(code, message);
}

void require(bool condition, certificates::ErrorCode code, const char* message) {
  if (!condition) {
    reject(code, message);
  }
}

[[nodiscard]] std::string derived_id(std::string_view domain, std::string_view value) {
  std::vector<std::byte> bytes;
  bytes.reserve(domain.size() + 1U + value.size());
  for (const char character : domain) {
    bytes.push_back(static_cast<std::byte>(character));
  }
  bytes.push_back(std::byte{0});
  for (const char character : value) {
    bytes.push_back(static_cast<std::byte>(character));
  }
  return "sha256:" + core::canonical::sha256_hex(bytes);
}

[[nodiscard]] std::uint64_t seed_number(std::string_view seed_id, std::string_view ticket_id) {
  const auto digest = derived_id("deltareduce.008.bucket.v1", std::string(seed_id) + ":" +
                                                                    std::string(ticket_id));
  std::uint64_t value = 0U;
  for (const char digit : std::string_view(digest).substr(7U, 16U)) {
    value <<= 4U;
    value |= static_cast<std::uint64_t>(
        digit <= '9' ? digit - '0' : 10 + digit - 'a');
  }
  return value;
}

[[nodiscard]] std::string padded_bucket(std::uint64_t bucket) {
  auto digits = std::to_string(bucket);
  return "bucket-" + std::string(6U - std::min<std::size_t>(6U, digits.size()), '0') + digits;
}

[[nodiscard]] std::int64_t divide_round_positive_tie(
    std::int64_t numerator,
    std::uint64_t denominator) {
  require(denominator > 0U, certificates::ErrorCode::arithmetic_invalid, "zero divisor");
  const auto magnitude = numerator >= 0
                             ? static_cast<std::uint64_t>(numerator)
                             : static_cast<std::uint64_t>(-(numerator + 1)) + 1U;
  const auto quotient = magnitude / denominator;
  const auto remainder = magnitude % denominator;
  require(
      quotient <= static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),
      certificates::ErrorCode::arithmetic_invalid,
      "robust rounded quotient exceeds int64");
  if (numerator >= 0) {
    return static_cast<std::int64_t>(
        quotient + (remainder >= denominator - remainder ? 1U : 0U));
  }
  const auto truncated = -static_cast<std::int64_t>(quotient);
  if (remainder == 0U || remainder <= denominator - remainder) {
    return truncated;
  }
  return core::arithmetic::checked_add(truncated, -1);
}

struct ClipResult {
  std::vector<std::int64_t> center;
  std::string transcript;
};

[[nodiscard]] ClipResult centered_clip(
    const std::vector<Contribution>& ordered,
    const std::vector<std::size_t>& rejected,
    std::uint32_t iteration_count) {
  const auto width = ordered.front().q_values.size();
  require(width > 0U, certificates::ErrorCode::arithmetic_invalid, "empty robust vector");
  for (const auto& contribution : ordered) {
    require(
        contribution.q_values.size() == width,
        certificates::ErrorCode::arithmetic_invalid,
        "robust vectors have different shapes");
  }
  const auto accepted_count = ordered.size() - rejected.size();
  std::vector<std::int64_t> center(width, 0);
  std::string transcript;
  for (std::uint32_t iteration = 0U; iteration < iteration_count; ++iteration) {
    std::vector<std::uint64_t> deviations;
    for (std::size_t index = 0U; index < ordered.size(); ++index) {
      if (std::binary_search(rejected.begin(), rejected.end(), index)) {
        continue;
      }
      for (std::size_t coordinate = 0U; coordinate < width; ++coordinate) {
        const auto difference = core::arithmetic::checked_add(
            ordered[index].q_values[coordinate],
            core::arithmetic::checked_multiply(center[coordinate], -1));
        deviations.push_back(
            difference >= 0 ? static_cast<std::uint64_t>(difference)
                            : static_cast<std::uint64_t>(-(difference + 1)) + 1U);
      }
    }
    std::sort(deviations.begin(), deviations.end());
    const auto radius = deviations[deviations.size() / 2U];
    require(
        radius <= static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),
        certificates::ErrorCode::arithmetic_invalid,
        "clip radius exceeds int64");
    std::vector<std::int64_t> next(width, 0);
    for (std::size_t coordinate = 0U; coordinate < width; ++coordinate) {
      std::int64_t sum = 0;
      for (std::size_t index = 0U; index < ordered.size(); ++index) {
        if (std::binary_search(rejected.begin(), rejected.end(), index)) {
          continue;
        }
        const auto difference = core::arithmetic::checked_add(
            ordered[index].q_values[coordinate],
            core::arithmetic::checked_multiply(center[coordinate], -1));
        const auto bounded = std::clamp(
            difference,
            -static_cast<std::int64_t>(radius),
            static_cast<std::int64_t>(radius));
        sum = core::arithmetic::checked_add(
            sum, core::arithmetic::checked_add(center[coordinate], bounded));
      }
      next[coordinate] = divide_round_positive_tie(sum, accepted_count);
    }
    center = std::move(next);
    transcript += "iteration=" + std::to_string(iteration) + ",radius=" +
                  std::to_string(radius) + ",center=";
    for (const auto coordinate : center) {
      transcript += std::to_string(coordinate) + ",";
    }
    transcript.push_back(';');
  }
  return {std::move(center), std::move(transcript)};
}

}  // namespace

std::int64_t exact_squared_norm(std::span<const std::int64_t> values) {
  require(!values.empty(), certificates::ErrorCode::arithmetic_invalid, "empty contribution");
  std::int64_t total = 0;
  try {
    for (const auto value : values) {
      total = core::arithmetic::checked_add(
          total, core::arithmetic::checked_multiply(value, value));
    }
  } catch (const core::arithmetic::ArithmeticError&) {
    reject(certificates::ErrorCode::arithmetic_invalid, "squared norm overflows int64");
  }
  return total;
}

PlanResult build_plan(
    const certificates::Context& context,
    std::string input_set_certificate_id,
    std::string seed_transcript_id,
    std::string robust_profile_id,
    std::string seed_id,
    std::span<const Contribution> contributions,
    const Profile& profile,
    std::vector<std::string> signer_ids,
    std::uint32_t quorum_threshold) {
  require(
      certificates::is_content_id(input_set_certificate_id) &&
          certificates::is_content_id(seed_transcript_id) &&
          certificates::is_content_id(robust_profile_id) &&
          certificates::is_content_id(seed_id) &&
          certificates::is_content_id(profile.accumulator_proof_id),
      certificates::ErrorCode::identifier_invalid,
      "robust plan parent or profile ID is invalid");
  require(
      !contributions.empty() && contributions.size() <= profile.maximum_eligible_tickets,
      certificates::ErrorCode::limit_exceeded,
      "contribution count exceeds the certified maximum");
  require(
      profile.bucket_count > 0U && profile.iteration_count > 0U &&
          profile.coefficient_denominator > 0U && profile.maximum_absolute_q > 0,
      certificates::ErrorCode::arithmetic_invalid,
      "robust profile is invalid");
  require(
      profile.trim_highest < contributions.size(),
      certificates::ErrorCode::membership_mutation,
      "trim policy rejects every contribution");

  std::vector<Contribution> ordered(contributions.begin(), contributions.end());
  std::sort(ordered.begin(), ordered.end(), [](const auto& left, const auto& right) {
    return left.ticket_id < right.ticket_id;
  });
  require(
      std::adjacent_find(ordered.begin(), ordered.end(), [](const auto& left, const auto& right) {
        return left.ticket_id == right.ticket_id;
      }) == ordered.end(),
      certificates::ErrorCode::duplicate_entry,
      "duplicate ticket contribution");

  std::vector<std::int64_t> norms;
  norms.reserve(ordered.size());
  std::string norm_transcript;
  for (const auto& contribution : ordered) {
    require(
        certificates::is_label(contribution.ticket_id) &&
            certificates::is_label(contribution.domain_id),
        certificates::ErrorCode::identifier_invalid,
        "contribution identity is invalid");
#if !defined(DELTA_ROBUST_MUTANT_SKIP_Q_BOUND)
    for (const auto value : contribution.q_values) {
      require(
          value >= -profile.maximum_absolute_q && value <= profile.maximum_absolute_q,
          certificates::ErrorCode::accumulator_unsafe,
          "contribution exceeds the certified q bound");
    }
#endif
    const auto norm = exact_squared_norm(contribution.q_values);
    norms.push_back(norm);
    norm_transcript += contribution.ticket_id + ":" + std::to_string(norm) + ";";
  }

  try {
    (void)core::arithmetic::validate_accumulator_bound(core::arithmetic::AccumulatorBoundRequest{
        std::string(core::arithmetic::fixture_profile_id()),
        core::arithmetic::AccumulatorWidth::int128,
        profile.maximum_eligible_tickets,
        -profile.maximum_absolute_q,
        profile.maximum_absolute_q,
        -static_cast<std::int64_t>(profile.coefficient_denominator),
        static_cast<std::int64_t>(profile.coefficient_denominator),
        core::arithmetic::Int128::from_u64(0U),
    });
  } catch (const core::arithmetic::BoundError&) {
    reject(certificates::ErrorCode::accumulator_unsafe, "robust accumulator proof is unsafe");
  }

  std::vector<std::size_t> rejected;
  rejected.reserve(profile.trim_highest);
  std::vector<std::size_t> ranking(ordered.size());
  for (std::size_t index = 0U; index < ranking.size(); ++index) {
    ranking[index] = index;
  }
  std::sort(ranking.begin(), ranking.end(), [&](std::size_t left, std::size_t right) {
    if (norms[left] != norms[right]) {
      return norms[left] > norms[right];
    }
    return ordered[left].ticket_id > ordered[right].ticket_id;
  });
  rejected.assign(ranking.begin(), ranking.begin() + profile.trim_highest);
  std::sort(rejected.begin(), rejected.end());
  ClipResult clip;
  try {
    clip = centered_clip(ordered, rejected, profile.iteration_count);
  } catch (const core::arithmetic::ArithmeticError&) {
    reject(certificates::ErrorCode::arithmetic_invalid, "centered clipping overflows int64");
  }
  const auto accepted_count = ordered.size() - rejected.size();
  require(
      profile.coefficient_denominator == accepted_count,
      certificates::ErrorCode::arithmetic_invalid,
      "APC coefficients do not form the canonical equal-weight plan");

  certificates::NormEvidence norm_evidence{
      .context = context,
      .entries = {},
      .input_set_certificate_id = input_set_certificate_id,
      .norm_root = derived_id("deltareduce.008.norm-root.v1", norm_transcript),
  };
  certificates::EligibilityCertificate eligibility{
      .context = context,
      .entries = {},
      .input_set_certificate_id = input_set_certificate_id,
      .norm_evidence_id = {},
      .quorum_threshold = quorum_threshold,
      .robust_profile_id = std::move(robust_profile_id),
      .signer_ids = signer_ids,
  };
  for (std::size_t index = 0U; index < ordered.size(); ++index) {
    const bool accepted = !std::binary_search(rejected.begin(), rejected.end(), index);
    norm_evidence.entries.push_back(certificates::NormEntry{
        .scale_denominator = 1U,
        .squared_norm = std::to_string(norms[index]),
        .ticket_id = ordered[index].ticket_id,
    });
    std::vector<std::int64_t> centered;
    centered.reserve(ordered[index].q_values.size());
    try {
      for (std::size_t coordinate = 0U; coordinate < ordered[index].q_values.size(); ++coordinate) {
        centered.push_back(core::arithmetic::checked_add(
            ordered[index].q_values[coordinate],
            core::arithmetic::checked_multiply(clip.center[coordinate], -1)));
      }
    } catch (const core::arithmetic::ArithmeticError&) {
      reject(certificates::ErrorCode::arithmetic_invalid, "centered norm difference overflows");
    }
    eligibility.entries.push_back(certificates::EligibilityEntry{
        .accepted = accepted,
        .domain_id = ordered[index].domain_id,
        .gamma = certificates::Rational{exact_squared_norm(centered), 1U},
        .reason_code = accepted ? "ACCEPTED" : "TRIMMED_HIGH_NORM",
        .ticket_id = ordered[index].ticket_id,
    });
  }
  eligibility.norm_evidence_id = certificates::content_id(norm_evidence);

  certificates::AggregationPlanCertificate plan{
      .context = context,
      .accumulator_proof_id = profile.accumulator_proof_id,
      .bucket_assignments = {},
      .eligibility_certificate_id = certificates::content_id(eligibility),
      .input_set_certificate_id = std::move(input_set_certificate_id),
      .iteration_count = profile.iteration_count,
      .quorum_threshold = quorum_threshold,
      .seed_transcript_id = std::move(seed_transcript_id),
      .signer_ids = std::move(signer_ids),
      .transcript_root = {},
      .weights = {},
  };
  std::string plan_transcript = clip.transcript;
  for (const auto& entry : eligibility.entries) {
    if (!entry.accepted) {
      continue;
    }
    const auto bucket = seed_number(seed_id, entry.ticket_id) % profile.bucket_count;
    plan.bucket_assignments.push_back(
        certificates::BucketAssignment{padded_bucket(bucket), entry.ticket_id});
    plan.weights.push_back(certificates::Weight{
        certificates::Rational{1, profile.coefficient_denominator}, entry.ticket_id});
    plan_transcript += entry.ticket_id + ":" + std::to_string(bucket) + ":1/" +
                       std::to_string(profile.coefficient_denominator) + ";";
  }
  plan.transcript_root = derived_id("deltareduce.008.plan-transcript.v1", plan_transcript);
  (void)certificates::content_id(plan);
  return PlanResult{std::move(norm_evidence), std::move(eligibility), std::move(plan)};
}

certificates::ParameterShardQc reduce_parameter_shard(
    const certificates::Context& context,
    std::string input_set_certificate_id,
    std::string eligibility_certificate_id,
    const certificates::AggregationPlanCertificate& plan,
    std::string domain_id,
    std::string shard_id,
    std::span<const Contribution> contributions,
    std::vector<std::string> input_leaf_ids,
    std::vector<std::string> signer_ids,
    std::uint32_t quorum_threshold) {
  require(
      !contributions.empty() && contributions.size() == input_leaf_ids.size(),
      certificates::ErrorCode::coverage_incomplete,
      "parameter shard lacks exact contribution/leaf coverage");
  require(
      certificates::is_content_id(input_set_certificate_id) &&
          certificates::is_content_id(eligibility_certificate_id) &&
          certificates::is_label(domain_id) && certificates::is_label(shard_id),
      certificates::ErrorCode::identifier_invalid,
      "parameter shard identity is invalid");
  std::vector<Contribution> ordered(contributions.begin(), contributions.end());
  std::sort(ordered.begin(), ordered.end(), [](const auto& left, const auto& right) {
    return left.ticket_id < right.ticket_id;
  });
  require(
      std::adjacent_find(ordered.begin(), ordered.end(), [](const auto& left, const auto& right) {
        return left.ticket_id == right.ticket_id;
      }) == ordered.end(),
      certificates::ErrorCode::duplicate_entry,
      "parameter shard has duplicate tickets");
  const auto width = ordered.front().q_values.size();
  require(width > 0U, certificates::ErrorCode::arithmetic_invalid, "parameter shard is empty");
  std::vector<certificates::Weight> weights;
  weights.reserve(ordered.size());
  for (const auto& contribution : ordered) {
    require(
        contribution.domain_id == domain_id && contribution.q_values.size() == width,
        certificates::ErrorCode::coverage_incomplete,
        "parameter shard mixed domains or vector shapes");
    const auto found = std::lower_bound(
        plan.weights.begin(),
        plan.weights.end(),
        contribution.ticket_id,
        [](const auto& weight, const auto& ticket) { return weight.ticket_id < ticket; });
    require(
        found != plan.weights.end() && found->ticket_id == contribution.ticket_id,
        certificates::ErrorCode::membership_mutation,
        "parameter shard contribution is outside the APC");
    weights.push_back(*found);
  }
  require(
      std::is_sorted(input_leaf_ids.begin(), input_leaf_ids.end()) &&
          std::adjacent_find(input_leaf_ids.begin(), input_leaf_ids.end()) == input_leaf_ids.end(),
      certificates::ErrorCode::order_invalid,
      "parameter shard input leaves are not canonical");

  std::uint64_t denominator = 1U;
  for (const auto& weight : weights) {
    certificates::validate_rational(weight.alpha, true);
    const auto divisor = std::gcd(denominator, weight.alpha.denominator);
    require(
        denominator <= std::numeric_limits<std::uint64_t>::max() /
                           (weight.alpha.denominator / divisor),
        certificates::ErrorCode::accumulator_unsafe,
        "parameter shard common denominator overflows");
    denominator *= weight.alpha.denominator / divisor;
  }
  require(
      denominator <= static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),
      certificates::ErrorCode::accumulator_unsafe,
      "parameter shard denominator exceeds int64");
  std::vector<std::string> numerators;
  numerators.reserve(width);
  try {
    for (std::size_t coordinate = 0U; coordinate < width; ++coordinate) {
      std::int64_t sum = 0;
      for (std::size_t index = 0U; index < ordered.size(); ++index) {
        const auto multiplier = denominator / weights[index].alpha.denominator;
        require(
            multiplier <= static_cast<std::uint64_t>(std::numeric_limits<std::int64_t>::max()),
            certificates::ErrorCode::accumulator_unsafe,
            "parameter shard multiplier exceeds int64");
        const auto term = core::arithmetic::checked_multiply(
            core::arithmetic::checked_multiply(
                ordered[index].q_values[coordinate], weights[index].alpha.numerator),
            static_cast<std::int64_t>(multiplier));
        sum = core::arithmetic::checked_add(sum, term);
      }
      numerators.push_back(std::to_string(sum));
    }
  } catch (const core::arithmetic::ArithmeticError&) {
    reject(certificates::ErrorCode::accumulator_unsafe, "parameter shard accumulator overflows");
  }
  certificates::ParameterShardQc result{
      .context = context,
      .aggregation_plan_certificate_id = certificates::content_id(plan),
      .denominator = denominator,
      .domain_id = std::move(domain_id),
      .eligibility_certificate_id = std::move(eligibility_certificate_id),
      .input_leaf_ids = std::move(input_leaf_ids),
      .input_set_certificate_id = std::move(input_set_certificate_id),
      .quorum_threshold = quorum_threshold,
      .result_numerators = std::move(numerators),
      .shard_id = std::move(shard_id),
      .signer_ids = std::move(signer_ids),
  };
  (void)certificates::content_id(result);
  return result;
}

}  // namespace delta::robust
