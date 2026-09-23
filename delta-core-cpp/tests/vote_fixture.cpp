#include "vote_fixture.hpp"

namespace delta::test::vote_fixture {

Fixture full(
    core::consensus::VoteAction action,
    core::protocol::RoundState state) {
  using namespace certificates;
  using namespace core::consensus;
  const auto epoch = id('d');
  const Context context{
      id('4'), state.height, id('5'), state.config_id, state.round_id, epoch, state.view};
  const InputSetCertificate input{
      context,
      id('6'),
      3U,
      signers(),
      {{id('7'), id('8'), "domain-a", "ticket-a"}},
  };
  const auto input_body = project_input_set_vote_body(input);
  const auto input_body_id = vote_input_set_body_id(input_body);
  const auto input_id = content_id(input);
  const SeedTranscript seed{
      context, input_id, id('9'), id('a'), {id('b')},
  };
  const auto seed_id = content_id(seed);
  const NormEvidence norms{
      context,
      {{1U, "1", "ticket-a"}},
      input_id,
      id('c'),
  };
  const auto norm_id = content_id(norms);
  const EligibilityCertificate eligibility{
      context,
      {{true, "domain-a", {1, 1U}, "ACCEPTED", "ticket-a"}},
      input_id,
      norm_id,
      3U,
      id('e'),
      signers(),
  };
  const auto eligibility_body =
      project_eligibility_vote_body(eligibility, seed_id);
  const auto eligibility_body_id = vote_eligibility_body_id(eligibility_body);
  const auto eligibility_id = content_id(eligibility);
  const auto accumulator = id('f');
  const AggregationPlanCertificate plan{
      context,
      accumulator,
      {{"bucket-a", "ticket-a"}},
      eligibility_id,
      input_id,
      1U,
      3U,
      seed_id,
      signers(),
      id('0'),
      {{{1, 1U}, "ticket-a"}},
  };
  const auto plan_body = project_aggregation_plan_vote_body(plan);
  const auto plan_body_id = vote_aggregation_plan_body_id(plan_body);
  const auto plan_id = content_id(plan);
  const ParameterShardQc parameter{
      context,
      plan_id,
      1U,
      "domain-a",
      eligibility_id,
      {id('1')},
      input_id,
      3U,
      {"1"},
      "shard-a",
      signers(),
  };
  const auto parameter_body =
      project_parameter_vote_body(parameter, "PARAMETER:domain-a:shard-a");
  const auto parameter_body_id = vote_parameter_body_id(parameter_body);
  const auto parameter_id = content_id(parameter);
  const std::vector<ShardKey> required{{"domain-a", "shard-a"}};
  const std::vector<RootLeaf> leaves{{"domain-a", parameter_id, "shard-a"}};
  const AggregateRootQc root{
      context,
      plan_id,
      eligibility_id,
      input_id,
      leaves,
      aggregate_merkle_root(leaves),
      3U,
      required,
      signers(),
  };
  const auto root_body = project_aggregate_root_vote_body(root);
  const auto root_body_id = vote_aggregate_root_body_id(root_body);
  const auto root_id = content_id(root);
  const ApplyArithmeticProfile profile{
      accumulator,
      {{"domain-a", {1, 1U}}},
      {1, 1U},
      {0, 1U},
      true,
      "HALF_TOWARD_POSITIVE",
      {0, 1U},
  };
  const auto profile_id = content_id(profile);
  const ApplyCandidate apply_candidate{
      context,
      root_id,
      profile_id,
      id('2'),
      {"1"},
      id('3'),
      {"0"},
      state.parent_checkpoint_id,
      id('4'),
  };
  const auto apply_candidate_id = content_id(apply_candidate);
  const VoteViewChangeBody view_body{
      state.round_id, state.height, state.view, state.view + 1U, 50U};
  VoteAdmissionSnapshot snapshot;
  snapshot.state_id = core::canonical::content_id(
      core::canonical::Type::round_state, core::protocol::encode(state));
  snapshot.parameter_schema_id = context.parameter_schema_id;
  snapshot.arithmetic_profile_id = context.arithmetic_profile_id;
  snapshot.required_accumulator_proof_id = accumulator;
  snapshot.proposed_round_config_ids = {state.config_id};
  if (action != VoteAction::round_config) {
    snapshot.finalized_round_config_ids = {state.config_id};
  }

  const auto add_input_final = [&] {
    snapshot.input_set_certificates = {input};
    snapshot.finalized_input_set_ids = {input_id};
    snapshot.seed_transcripts = {seed};
    snapshot.norm_evidence = {norms};
  };
  const auto add_eligibility_final = [&] {
    snapshot.eligibility_certificates = {{eligibility, seed_id}};
    snapshot.finalized_eligibility_ids = {eligibility_id};
  };
  const auto add_plan_final = [&] {
    snapshot.aggregation_plan_certificates = {plan};
    snapshot.finalized_aggregation_plan_ids = {plan_id};
  };
  const auto add_parameter_final = [&] {
    snapshot.parameter_qcs = {parameter};
    snapshot.finalized_parameter_ids = {parameter_id};
    snapshot.required_parameter_keys = required;
  };
  const auto add_root_final = [&] {
    snapshot.aggregate_root_qcs = {root};
    snapshot.finalized_aggregate_root_ids = {root_id};
  };

  switch (action) {
    case VoteAction::round_config:
      break;
    case VoteAction::input_set:
      snapshot.closed_input_set_ids = {input_body_id};
      snapshot.input_set_bodies = {input_body};
      break;
    case VoteAction::eligibility:
      add_input_final();
      snapshot.eligibility_bodies = {eligibility_body};
      break;
    case VoteAction::aggregation_plan:
      add_input_final();
      add_eligibility_final();
      snapshot.aggregation_plan_bodies = {plan_body};
      break;
    case VoteAction::parameter:
      add_input_final();
      add_eligibility_final();
      add_plan_final();
      snapshot.required_parameter_keys = required;
      snapshot.parameter_bodies = {parameter_body};
      break;
    case VoteAction::aggregate_root:
      add_input_final();
      add_eligibility_final();
      add_plan_final();
      add_parameter_final();
      snapshot.aggregate_root_bodies = {root_body};
      break;
    case VoteAction::apply:
      add_input_final();
      add_eligibility_final();
      add_plan_final();
      add_parameter_final();
      add_root_final();
      snapshot.apply_profiles = {profile};
      snapshot.apply_candidates = {apply_candidate};
      break;
    case VoteAction::view_change:
      snapshot.timeout_observations = {
          {state.round_id, state.height, state.view}};
      snapshot.view_change_bodies = {view_body};
      break;
    case VoteAction::abort:
      break;
  }
  const VoteAbortBody abort_body{
      state.round_id,
      epoch,
      state.height,
      state.view,
      100U,
      state.parent_checkpoint_id,
      "HARD_DEADLINE",
      snapshot.finalized_round_config_ids,
      snapshot.finalized_input_set_ids,
      snapshot.finalized_eligibility_ids,
      snapshot.finalized_aggregation_plan_ids,
      snapshot.finalized_parameter_ids,
      snapshot.finalized_aggregate_root_ids,
      snapshot.finalized_apply_ids,
  };
  if (action == VoteAction::abort) {
    snapshot.abort_bodies = {abort_body};
  }

  VoteParentState parents;
  parents.round_config_id = state.config_id;
  parents.parent_checkpoint_id = state.parent_checkpoint_id;
  std::string body;
  std::string vote_context;
  switch (action) {
    case VoteAction::round_config:
      body = state.config_id;
      vote_context = vote_context_id(
          action, state.round_id, state.height, state.view, epoch);
      break;
    case VoteAction::input_set:
      body = input_body_id;
      vote_context = vote_context_id(
          action, state.round_id, state.height, state.view, epoch);
      break;
    case VoteAction::eligibility:
      body = eligibility_body_id;
      parents.input_set_certificate_id = input_id;
      parents.seed_transcript_id = seed_id;
      parents.norm_evidence_id = norm_id;
      vote_context = vote_context_id(
          action, state.round_id, state.height, state.view, epoch, input_id);
      break;
    case VoteAction::aggregation_plan:
      body = plan_body_id;
      parents.input_set_certificate_id = input_id;
      parents.seed_transcript_id = seed_id;
      parents.norm_evidence_id = norm_id;
      parents.eligibility_certificate_id = eligibility_id;
      vote_context = vote_context_id(
          action,
          state.round_id,
          state.height,
          state.view,
          epoch,
          eligibility_id);
      break;
    case VoteAction::parameter:
      body = parameter_body_id;
      vote_context = vote_context_id(
          action,
          state.round_id,
          state.height,
          state.view,
          epoch,
          parameter_body.vote_context_id);
      parents.input_set_certificate_id = input_id;
      parents.seed_transcript_id = seed_id;
      parents.eligibility_certificate_id = eligibility_id;
      parents.aggregation_plan_certificate_id = plan_id;
      parents.domain_id = parameter.domain_id;
      parents.shard_id = parameter.shard_id;
      break;
    case VoteAction::aggregate_root:
      body = root_body_id;
      parents.input_set_certificate_id = input_id;
      parents.seed_transcript_id = seed_id;
      parents.eligibility_certificate_id = eligibility_id;
      parents.aggregation_plan_certificate_id = plan_id;
      parents.parameter_matrix_root = root.merkle_root;
      vote_context = vote_context_id(
          action, state.round_id, state.height, state.view, epoch, plan_id);
      break;
    case VoteAction::apply:
      body = apply_candidate_id;
      parents.aggregate_root_certificate_id = root_id;
      parents.apply_profile_id = profile_id;
      parents.apply_candidate_id = apply_candidate_id;
      vote_context = vote_context_id(
          action, state.round_id, state.height, state.view, epoch, root_id);
      break;
    case VoteAction::view_change:
      body = vote_view_change_body_id(view_body);
      vote_context = vote_context_id(
          action, state.round_id, state.height, state.view, epoch);
      break;
    case VoteAction::abort:
      body = vote_abort_body_id(abort_body);
      parents.reason_code = abort_body.reason_code;
      vote_context = vote_context_id(
          action, state.round_id, state.height, state.view, epoch);
      break;
  }
  VoteCandidateBinding candidate{
      action, body, vote_context, state.height, state.view, std::move(parents)};
  VoteAdmissionPolicy policy;
  policy.local_validator_id = "validator-1";
  policy.validator_epoch_id = epoch;
  policy.validator_ids = validators();
  policy.role = ValidatorRole::validator;
  policy.round_id = state.round_id;
  policy.round_config_id = state.config_id;
  policy.configured_abort_reason = "HARD_DEADLINE";
  policy.initial_logical_tick =
      action == VoteAction::abort ? 100U
      : action == VoteAction::view_change ? 50U
                                          : 10U;
  policy.soft_deadline_tick = 50U;
  policy.hard_deadline_tick = 100U;
  policy.snapshot = std::move(snapshot);
  policy.candidates = {candidate};
  core::protocol::Vote vote{
      .body_hash = candidate.body_hash,
      .context_id = candidate.context_id,
      .durable_sequence = 1U,
      .height = state.height,
      .kind = std::string(vote_kind_name(action)),
      .round_id = state.round_id,
      .signature_id = id('e'),
      .validator_epoch_id = epoch,
      .validator_id = policy.local_validator_id,
      .view = state.view,
  };
  return Fixture{std::move(state), std::move(policy), std::move(candidate), std::move(vote)};
}

core::consensus::VoteAdmissionPolicy round_config_policy(
    const core::protocol::RoundState& state,
    const core::protocol::Vote& vote) {
  using namespace core::consensus;
  VoteParentState parents;
  parents.round_config_id = state.config_id;
  parents.parent_checkpoint_id = state.parent_checkpoint_id;
  VoteAdmissionSnapshot snapshot;
  snapshot.state_id = core::canonical::content_id(
      core::canonical::Type::round_state, core::protocol::encode(state));
  snapshot.parameter_schema_id = id('5');
  snapshot.arithmetic_profile_id = id('4');
  snapshot.proposed_round_config_ids = {state.config_id};

  VoteCandidateBinding candidate;
  candidate.action = VoteAction::round_config;
  candidate.body_hash = state.config_id;
  candidate.context_id = vote_context_id(
      VoteAction::round_config,
      state.round_id,
      state.height,
      state.view,
      vote.validator_epoch_id);
  candidate.height = vote.height;
  candidate.view = vote.view;
  candidate.parents = std::move(parents);

  VoteAdmissionPolicy policy;
  policy.local_validator_id = vote.validator_id;
  policy.validator_epoch_id = vote.validator_epoch_id;
  policy.validator_ids = validators();
  policy.role = ValidatorRole::validator;
  policy.round_id = state.round_id;
  policy.round_config_id = state.config_id;
  policy.configured_abort_reason = "HARD_DEADLINE";
  policy.initial_logical_tick = 10U;
  policy.soft_deadline_tick = 50U;
  policy.hard_deadline_tick = 100U;
  policy.snapshot = std::move(snapshot);
  policy.candidates = {std::move(candidate)};
  return policy;
}

}  // namespace delta::test::vote_fixture
