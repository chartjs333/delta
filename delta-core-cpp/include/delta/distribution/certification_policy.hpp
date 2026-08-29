#pragma once

#include <cstddef>
#include <span>
#include <string>
#include <string_view>

#include <delta/certificates/contracts.hpp>

namespace delta::distribution {

inline constexpr std::size_t max_manifest_bytes = 1U * 1024U * 1024U;
inline constexpr std::size_t max_certificate_bytes = 64U * 1024U;
inline constexpr std::size_t max_piece_bytes = 1U * 1024U * 1024U;
inline constexpr std::size_t max_piece_count = 8192U;
inline constexpr std::size_t max_object_bytes = 8ULL * 1024ULL * 1024ULL * 1024ULL;

inline constexpr std::string_view formal_semantics_id =
    "sha256:cc98f15ac20fc3ed265cb76682ca15a936e24660a651e2b8f81638abb3265cb6";
inline constexpr std::string_view policy_registry_id =
    "sha256:c0d1e26526a772498041c34a5c0c5735a4aec3d133e190635f01eb251203d64b";
inline constexpr std::string_view aggregate_policy_id =
    "sha256:95b0dac10dbe18d4394855a93d897b36e84fafeb2475ee9f416f689abe6f74a0";
inline constexpr std::string_view inactive_apply_policy_id =
    "sha256:9e69f3d44cd98b7885987fdd524498f913473e0bb50d10f9163399ff0fabd89b";
inline constexpr std::string_view aggregate_media_type =
    "application/vnd.deltareduce.aggregate-bundle;version=1";

struct PolicyDecision {
  bool accepted = false;
  std::string code;
  std::string manifest_id;
  std::string certificate_policy_id;
  std::string formal_action_id = "ACT-PUBLISH";

  [[nodiscard]] std::string canonical_effect_json() const;
  bool operator==(const PolicyDecision&) const = default;
};

// Evaluates the native policy boundary. Every bounded semantic failure is returned as a typed
// REJECT decision; no Java-side policy reconstruction is required or permitted.
[[nodiscard]] PolicyDecision evaluate_certified_manifest(
    std::span<const std::byte> canonical_manifest,
    std::span<const std::byte> canonical_certificate,
    bool request_make_current = false);

// Feature 008 activation of the feature-005 reserved apply-qc-v1 policy. The generic feature-005
// evaluator remains backward-compatible and inactive; current publication must use this stronger
// entry point with an already verified native ApplyQC body.
[[nodiscard]] PolicyDecision evaluate_applied_checkpoint(
    std::span<const std::byte> canonical_manifest,
    const certificates::ApplyQc& apply_qc,
    bool request_make_current = true);

[[nodiscard]] std::string object_manifest_id(std::span<const std::byte> canonical_manifest);

}  // namespace delta::distribution
