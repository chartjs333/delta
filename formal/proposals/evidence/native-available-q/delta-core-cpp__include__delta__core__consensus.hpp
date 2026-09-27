#pragma once

#include <delta/certificates/contracts.hpp>
#include <delta/core/protocol.hpp>

#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <string>
#include <string_view>
#include <vector>

namespace delta::core::consensus {

enum class ErrorCode {
  validator_set_invalid,
  quorum_policy_mismatch,
  unknown_signer,
  signer_set_invalid,
  conflicting_vote,
  vote_invalid,
  identifier_invalid,
  ticket_set_invalid,
  unknown_ticket,
  commitment_equivocation,
  commitment_missing,
  availability_commitment_mismatch,
  availability_coverage_incomplete,
  availability_attesters_invalid,
  availability_conflict,
  input_set_empty,
  vote_action_invalid,
  vote_policy_invalid,
  vote_admission_rejected,
};

class ConsensusError final : public std::runtime_error {
 public:
  ConsensusError(ErrorCode code, std::string message);

  [[nodiscard]] ErrorCode code() const noexcept;

 private:
  ErrorCode code_;
};

enum class Disposition {
  recorded,
  replay,
  late,
};

// These values are a closed implementation mapping to the nine accepted
// formal vote actions.  They are not a second protocol vocabulary.
enum class VoteAction : std::uint32_t {
  round_config = 1U,
  input_set = 2U,
  eligibility = 3U,
  aggregation_plan = 4U,
  parameter = 5U,
  aggregate_root = 6U,
  apply = 7U,
  view_change = 8U,
  abort = 9U,
};

// The accepted formal model has one active consensus role.  Action-specific
// authorization roles would add protocol behavior, so the implementation keeps
// this vocabulary deliberately closed.
enum class ValidatorRole : std::uint32_t { validator = 1U };

inline constexpr std::size_t max_vote_validator_count = 4'096U;
inline constexpr std::size_t max_vote_candidate_count = 8'192U;

struct VoteParentState {
  std::string round_config_id;
  std::string parent_checkpoint_id;
  std::string input_set_certificate_id;
  std::string seed_transcript_id;
  std::string norm_evidence_id;
  std::string eligibility_certificate_id;
  std::string aggregation_plan_certificate_id;
  std::string parameter_matrix_root;
  std::string aggregate_root_certificate_id;
  std::string apply_profile_id;
  std::string apply_candidate_id;
  std::string last_finalized_certificate_id;
  std::string domain_id;
  std::string shard_id;
  std::string reason_code;

  bool operator==(const VoteParentState&) const = default;
};

struct VoteCandidateBinding {
  VoteAction action;
  std::string body_hash;
  // Canonical concrete projection supplied by the native-validated immutable
  // round contract. Typed parents below carry the formal abstraction; this
  // field preserves the already-frozen wire identifier instead of inventing a
  // second context encoder.
  std::string context_id;
  std::uint64_t height;
  std::uint64_t view;
  VoteParentState parents;

  bool operator==(const VoteCandidateBinding&) const = default;
};

struct VoteInputSetBody {
  certificates::Context context;
  std::string input_root;
  std::vector<certificates::InputTuple> tuples;

  bool operator==(const VoteInputSetBody&) const = default;
};

struct VoteEligibilityBody {
  certificates::Context context;
  std::vector<certificates::EligibilityEntry> entries;
  std::string input_set_certificate_id;
  std::string norm_evidence_id;
  std::string robust_profile_id;
  std::string seed_transcript_id;

  bool operator==(const VoteEligibilityBody&) const = default;
};

struct VoteAggregationPlanBody {
  certificates::Context context;
  std::string accumulator_proof_id;
  std::vector<certificates::BucketAssignment> bucket_assignments;
  std::string eligibility_certificate_id;
  std::string input_set_certificate_id;
  std::uint32_t iteration_count;
  std::string seed_transcript_id;
  std::string transcript_root;
  std::vector<certificates::Weight> weights;

  bool operator==(const VoteAggregationPlanBody&) const = default;
};

struct VoteParameterBody {
  certificates::Context context;
  std::string aggregation_plan_certificate_id;
  std::uint64_t denominator;
  std::string domain_id;
  std::string eligibility_certificate_id;
  std::vector<std::string> input_leaf_ids;
  std::string input_set_certificate_id;
  std::vector<std::string> result_numerators;
  std::string shard_id;
  // Exact immutable shard-plan assignment context.  It is not reconstructed
  // from domain/shard labels at admission time.
  std::string vote_context_id;

  bool operator==(const VoteParameterBody&) const = default;
};

struct VoteAggregateRootBody {
  certificates::Context context;
  std::string aggregation_plan_certificate_id;
  std::string eligibility_certificate_id;
  std::string input_set_certificate_id;
  std::vector<certificates::RootLeaf> leaves;
  std::string merkle_root;
  std::vector<certificates::ShardKey> required_keys;

  bool operator==(const VoteAggregateRootBody&) const = default;
};

// EC certificates do not carry the seed parent in the feature-008 wire
// contract, while the formal EC body does. Keep that exact parent beside the
// finalized certificate so later proposal guards cannot reconstruct it.
struct VoteFinalizedEligibility {
  certificates::EligibilityCertificate certificate;
  std::string seed_transcript_id;

  bool operator==(const VoteFinalizedEligibility&) const = default;
};

struct VoteFinalizedApply {
  certificates::ApplyQc certificate;
  certificates::ApplyCandidate candidate;

  bool operator==(const VoteFinalizedApply&) const = default;
};

struct VoteTimeoutObservation {
  std::string round_id;
  std::uint64_t height;
  std::uint64_t view;

  bool operator==(const VoteTimeoutObservation&) const = default;
};

struct VoteViewChangeBody {
  std::string round_id;
  std::uint64_t height;
  std::uint64_t from_view;
  std::uint64_t to_view;
  std::uint64_t soft_deadline_tick;

  bool operator==(const VoteViewChangeBody&) const = default;
};

struct VoteAbortRequest {
  std::string round_id;
  std::string reason_code;

  bool operator==(const VoteAbortRequest&) const = default;
};

struct VoteAbortBody {
  std::string round_id;
  std::string validator_epoch_id;
  std::uint64_t height;
  std::uint64_t view;
  std::uint64_t hard_deadline_tick;
  std::string parent_checkpoint_id;
  std::string reason_code;
  std::vector<std::string> round_config_ids;
  std::vector<std::string> input_set_ids;
  std::vector<std::string> eligibility_ids;
  std::vector<std::string> aggregation_plan_ids;
  std::vector<std::string> parameter_ids;
  std::vector<std::string> aggregate_root_ids;
  std::vector<std::string> apply_ids;

  bool operator==(const VoteAbortBody&) const = default;
};

// This is an immutable, typed projection of one already-prepared formal state,
// not a collection of caller-selected readiness flags.  Every referenced
// proposal body and finalized certificate is content-addressed independently,
// and the complete prerequisite chain is checked natively before the runtime
// opens. A proposal never contains the signer set or QC-only threshold of the
// certificate that its votes may later form. The state_id binds the snapshot to
// the exact canonical RoundState bytes; any subsequently committed submit
// invalidates the authority for new votes.
struct VoteAdmissionSnapshot {
  std::string state_id;
  std::string parameter_schema_id;
  std::string arithmetic_profile_id;
  std::string required_accumulator_proof_id;
  std::vector<std::string> proposed_round_config_ids;
  std::vector<std::string> finalized_round_config_ids;
  std::vector<std::string> closed_input_set_ids;
  std::vector<VoteInputSetBody> input_set_bodies;
  std::vector<certificates::InputSetCertificate> input_set_certificates;
  std::vector<std::string> finalized_input_set_ids;
  std::vector<certificates::SeedTranscript> seed_transcripts;
  std::vector<certificates::NormEvidence> norm_evidence;
  std::vector<VoteEligibilityBody> eligibility_bodies;
  std::vector<VoteFinalizedEligibility> eligibility_certificates;
  std::vector<std::string> finalized_eligibility_ids;
  std::vector<VoteAggregationPlanBody> aggregation_plan_bodies;
  std::vector<certificates::AggregationPlanCertificate> aggregation_plan_certificates;
  std::vector<std::string> finalized_aggregation_plan_ids;
  std::vector<VoteParameterBody> parameter_bodies;
  std::vector<certificates::ParameterShardQc> parameter_qcs;
  std::vector<std::string> finalized_parameter_ids;
  std::vector<certificates::ShardKey> required_parameter_keys;
  std::vector<VoteAggregateRootBody> aggregate_root_bodies;
  std::vector<certificates::AggregateRootQc> aggregate_root_qcs;
  std::vector<std::string> finalized_aggregate_root_ids;
  std::vector<certificates::ApplyArithmeticProfile> apply_profiles;
  std::vector<certificates::ApplyCandidate> apply_candidates;
  std::vector<VoteFinalizedApply> apply_qcs;
  std::vector<std::string> finalized_apply_ids;
  std::vector<VoteTimeoutObservation> timeout_observations;
  std::vector<VoteViewChangeBody> view_change_bodies;
  std::vector<VoteAbortRequest> abort_requests;
  std::vector<VoteAbortBody> abort_bodies;

  bool operator==(const VoteAdmissionSnapshot&) const = default;
};

struct VoteAdmissionPolicy {
  std::string local_validator_id;
  std::string validator_epoch_id;
  std::vector<std::string> validator_ids;
  ValidatorRole role;
  std::string round_id;
  std::string round_config_id;
  // Exact value of the formal ConfiguredAbortReason constant for this round.
  // It is immutable authority, not a per-vote caller-selected reason.
  std::string configured_abort_reason;
  std::uint64_t initial_logical_tick;
  std::uint64_t soft_deadline_tick;
  std::uint64_t hard_deadline_tick;
  VoteAdmissionSnapshot snapshot;
  // Complete, canonically ordered native projection of the immutable
  // round_contract. It is decoded and validated once at runtime startup, then
  // retained by value; no per-vote caller can add or replace a binding. In
  // particular, PARAMETER context_id is the exact shard-plan assignment's
  // vote_context_id from refinement-contract.md.
  std::vector<VoteCandidateBinding> candidates;
};

struct VoteAdmissionState {
  std::uint64_t logical_tick;
  bool recovery_ready;
  bool authority_invalidated;
};

enum class VoteAdmissionMode { live, recovery };

struct VoteAdmission {
  VoteAction action;
  std::string formal_action_id;
  std::string context_id;
  VoteParentState parents;
};

[[nodiscard]] std::string_view vote_kind_name(VoteAction action) noexcept;
[[nodiscard]] std::string_view vote_formal_action_id(VoteAction action) noexcept;
[[nodiscard]] VoteAction parse_vote_action(std::string_view kind);
// Closed formal AbortReasons vocabulary excluding NO_ABORT, exactly matching
// the ConfiguredAbortReason constraint in DeltaReduceTypes.tla.
[[nodiscard]] bool is_configured_abort_reason(std::string_view reason) noexcept;
// The context is an exact concrete identifier carried by the canonically
// decoded immutable round-contract projection. There is deliberately no
// synthetic context vocabulary: native admission resolves the closed action,
// current height/view, context, body, and typed parents to one frozen binding,
// and authors the admitted context from that binding rather than from the
// per-vote input.
[[nodiscard]] std::string_view frozen_vote_context(
    const VoteCandidateBinding& candidate) noexcept;
// Domain-separated concrete realization of the formal vote context. For EC,
// APC, ROOT, and APPLY, formal_parent_or_assignment is the exact finalized
// parent QC ID. For PARAMETER it is the immutable round-contract assignment
// vote_context_id and is returned unchanged. Other actions ignore it.
[[nodiscard]] std::string vote_context_id(
    VoteAction action,
    std::string_view round_id,
    std::uint64_t height,
    std::uint64_t view,
    std::string_view validator_epoch_id,
    std::string_view formal_parent_or_assignment = {});
[[nodiscard]] VoteInputSetBody project_input_set_vote_body(
    const certificates::InputSetCertificate& certificate);
[[nodiscard]] VoteEligibilityBody project_eligibility_vote_body(
    const certificates::EligibilityCertificate& certificate,
    std::string seed_transcript_id);
[[nodiscard]] VoteAggregationPlanBody project_aggregation_plan_vote_body(
    const certificates::AggregationPlanCertificate& certificate);
[[nodiscard]] VoteParameterBody project_parameter_vote_body(
    const certificates::ParameterShardQc& certificate,
    std::string vote_context_id);
[[nodiscard]] VoteAggregateRootBody project_aggregate_root_vote_body(
    const certificates::AggregateRootQc& certificate);
[[nodiscard]] std::string vote_input_set_body_id(const VoteInputSetBody& body);
[[nodiscard]] std::string vote_eligibility_body_id(const VoteEligibilityBody& body);
[[nodiscard]] std::string vote_aggregation_plan_body_id(
    const VoteAggregationPlanBody& body);
[[nodiscard]] std::string vote_parameter_body_id(const VoteParameterBody& body);
[[nodiscard]] std::string vote_aggregate_root_body_id(
    const VoteAggregateRootBody& body);
[[nodiscard]] std::string vote_view_change_body_id(const VoteViewChangeBody& body);
[[nodiscard]] std::string vote_abort_body_id(const VoteAbortBody& body);
void validate_vote_admission_policy(
    const VoteAdmissionPolicy& policy,
    const protocol::RoundState& state);
[[nodiscard]] VoteAdmission validate_vote_admission(
    const VoteAdmissionPolicy& policy,
    const protocol::RoundState& state,
    const VoteAdmissionState& admission_state,
    const protocol::Vote& vote,
    std::uint64_t expected_durable_sequence,
    VoteAdmissionMode mode = VoteAdmissionMode::live);

class VoteJournal {
 public:
  [[nodiscard]] Disposition record(const protocol::Vote& vote);
  [[nodiscard]] const std::vector<protocol::Vote>& votes() const noexcept;

 private:
  std::vector<protocol::Vote> votes_;
};

struct QuorumPolicy {
  std::string validator_epoch_id;
  std::vector<std::string> validator_ids;
  std::uint32_t quorum_threshold;
};

void validate_quorum(const protocol::QuorumCertificate& certificate, const QuorumPolicy& policy);

struct Commitment {
  std::string ticket_id;
  std::string commitment_id;

  bool operator==(const Commitment&) const = default;
};

struct AvailabilityProof {
  std::string ticket_id;
  std::string commitment_id;
  std::string certificate_id;
  std::vector<std::string> covered_leaf_ids;
  std::vector<std::string> attester_ids;
  std::uint32_t threshold;

  bool operator==(const AvailabilityProof&) const = default;
};

struct FrozenInput {
  std::string ticket_id;
  std::string commitment_id;
  std::string availability_certificate_id;

  bool operator==(const FrozenInput&) const = default;
};

class InputLedger {
 public:
  explicit InputLedger(std::vector<std::string> permitted_ticket_ids);

  [[nodiscard]] Disposition record_commitment(Commitment commitment);
  [[nodiscard]] Disposition record_availability(
      AvailabilityProof proof,
      const std::vector<std::string>& required_leaf_ids,
      const std::vector<std::string>& permitted_attester_ids,
      std::uint32_t required_threshold);
  [[nodiscard]] const std::vector<FrozenInput>& freeze();

  [[nodiscard]] bool frozen() const noexcept;
  [[nodiscard]] const std::vector<Commitment>& commitments() const noexcept;
  [[nodiscard]] const std::vector<AvailabilityProof>& availabilities() const noexcept;
  [[nodiscard]] const std::vector<FrozenInput>& frozen_inputs() const noexcept;
  [[nodiscard]] std::size_t late_commitment_count() const noexcept;
  [[nodiscard]] std::size_t late_availability_count() const noexcept;

 private:
  std::vector<std::string> permitted_ticket_ids_;
  std::vector<Commitment> commitments_;
  std::vector<AvailabilityProof> availabilities_;
  std::vector<FrozenInput> frozen_inputs_;
  std::vector<Commitment> late_commitments_;
  std::vector<AvailabilityProof> late_availabilities_;
  bool frozen_ = false;
};

}  // namespace delta::core::consensus
