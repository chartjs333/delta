#include <delta/apply/engine.hpp>
#include <delta/certificates/verifier.hpp>
#include <delta/core/canonical.hpp>
#include <delta/core/protocol.hpp>
#include <delta/core/transition.hpp>
#include <delta/robust/plan.hpp>
#include <delta/runtime/benchmark.hpp>
#include <delta/runtime/certificate_runtime.hpp>
#include <delta/runtime/runtime.hpp>

#include <algorithm>
#include <charconv>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iterator>
#include <map>
#include <optional>
#include <set>
#include <span>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

namespace delta::runtime::benchmark {
namespace {

namespace canonical = core::canonical;
namespace protocol = core::protocol;

[[nodiscard]] canonical::Bytes ascii_bytes(std::string_view value) {
  canonical::Bytes result;
  result.reserve(value.size());
  for (const unsigned char character : value) {
    result.push_back(static_cast<std::byte>(character));
  }
  return result;
}

[[nodiscard]] std::string derived_id(std::string_view domain, std::string_view value) {
  auto input = ascii_bytes(domain);
  const auto suffix = ascii_bytes(value);
  input.insert(input.end(), suffix.begin(), suffix.end());
  return "sha256:" + canonical::sha256_hex(input);
}

[[nodiscard]] std::string raw_id(std::span<const std::byte> value) {
  return "sha256:" + canonical::sha256_hex(value);
}

[[nodiscard]] std::vector<std::string> split(std::string_view value, char separator) {
  std::vector<std::string> result;
  std::size_t begin = 0U;
  while (begin <= value.size()) {
    const auto end = value.find(separator, begin);
    result.emplace_back(value.substr(begin, end == std::string_view::npos ? end : end - begin));
    if (end == std::string_view::npos) break;
    begin = end + 1U;
  }
  return result;
}

[[nodiscard]] std::uint64_t parse_u64(std::string_view value) {
  std::uint64_t result = 0U;
  const auto parsed = std::from_chars(value.data(), value.data() + value.size(), result);
  if (value.empty() || parsed.ec != std::errc{} || parsed.ptr != value.data() + value.size()) {
    throw BenchmarkError("causal schedule integer is invalid");
  }
  return result;
}

void require_schedule_token(std::string_view value) {
  if (value.empty() || value.size() > 128U ||
      value.find_first_of("\r\n,=") != std::string_view::npos) {
    throw BenchmarkError("causal schedule token is invalid");
  }
}

struct CausalMessage {
  std::string message_id;
  std::string actor_id;
  std::string domain_id;
  std::string ticket_id;
  std::string kind;
  std::uint64_t scheduled_tick{};
  std::uint64_t delivered_tick{};
  bool delivered{};
};

struct CausalSchedule {
  std::string event_id;
  std::string network_profile_id;
  std::uint64_t gst_tick{};
  std::uint64_t hard_deadline_tick{};
  std::vector<CausalMessage> messages;
  std::string receipt_id;
};

[[nodiscard]] CausalSchedule parse_causal_schedule(const FaultEvent& event) {
  if (event.causal_schedule.empty() || event.causal_schedule.back() != '\n') {
    throw BenchmarkError("causal fault scenario lacks a canonical Netty schedule");
  }
  std::map<std::string, std::string, std::less<>> fields;
  std::size_t begin = 0U;
  while (begin < event.causal_schedule.size()) {
    const auto end = event.causal_schedule.find('\n', begin);
    if (end == std::string::npos || end == begin) {
      throw BenchmarkError("causal schedule line is invalid");
    }
    const auto line = event.causal_schedule.substr(begin, end - begin);
    const auto separator = line.find('=');
    if (separator == std::string::npos || separator == 0U || separator + 1U == line.size() ||
        !fields.emplace(line.substr(0U, separator), line.substr(separator + 1U)).second) {
      throw BenchmarkError("causal schedule field is invalid");
    }
    begin = end + 1U;
  }
  const auto take = [&fields](std::string_view name) {
    const auto found = fields.find(name);
    if (found == fields.end()) throw BenchmarkError("causal schedule field is absent");
    auto value = found->second;
    fields.erase(found);
    return value;
  };
  if (take("schema_version") != "1.0.0") {
    throw BenchmarkError("causal schedule version is unsupported");
  }
  auto event_id = take("event_id");
  require_schedule_token(event_id);
  if (event_id != event.event_id) throw BenchmarkError("causal schedule event is mismatched");
  auto network_profile_id = take("network_profile_id");
  require_schedule_token(network_profile_id);
  const auto gst_tick = parse_u64(take("gst_tick"));
  const auto hard_deadline_tick = parse_u64(take("hard_deadline_tick"));
  const auto message_count = parse_u64(take("message_count"));
  if (message_count == 0U || message_count > 64U || gst_tick > hard_deadline_tick) {
    throw BenchmarkError("causal schedule bounds are invalid");
  }
  std::vector<CausalMessage> messages;
  messages.reserve(static_cast<std::size_t>(message_count));
  std::set<std::string, std::less<>> message_ids;
  for (std::uint64_t index = 0U; index < message_count; ++index) {
    const auto parts = split(take("message." + std::to_string(index)), ',');
    if (parts.size() != 8U || (parts[7] != "0" && parts[7] != "1")) {
      throw BenchmarkError("causal message field set is invalid");
    }
    for (std::size_t item = 0U; item < 5U; ++item) require_schedule_token(parts[item]);
    const auto scheduled_tick = parse_u64(parts[5]);
    const auto delivered_tick = parse_u64(parts[6]);
    const bool delivered = parts[7] == "1";
    if (!message_ids.insert(parts[0]).second || scheduled_tick < event.logical_step ||
        (delivered && delivered_tick < scheduled_tick) || (!delivered && delivered_tick != 0U) ||
        delivered_tick > hard_deadline_tick) {
      throw BenchmarkError("causal message timing or identity is invalid");
    }
    messages.push_back(CausalMessage{
        parts[0], parts[1], parts[2], parts[3], parts[4], scheduled_tick, delivered_tick, delivered});
  }
  if (!fields.empty()) throw BenchmarkError("causal schedule contains unknown fields");
  return CausalSchedule{
      std::move(event_id),
      std::move(network_profile_id),
      gst_tick,
      hard_deadline_tick,
      std::move(messages),
      raw_id(ascii_bytes(event.causal_schedule)),
  };
}

[[nodiscard]] std::vector<const CausalMessage*> messages_of_kind(
    const CausalSchedule& schedule,
    std::string_view kind,
    bool delivered_only = true) {
  std::vector<const CausalMessage*> result;
  for (const auto& message : schedule.messages) {
    if (message.kind == kind && (!delivered_only || message.delivered)) result.push_back(&message);
  }
  std::sort(result.begin(), result.end(), [](const auto* left, const auto* right) {
    if (left->delivered_tick != right->delivered_tick) {
      return left->delivered_tick < right->delivered_tick;
    }
    return left->message_id < right->message_id;
  });
  return result;
}

[[nodiscard]] std::string state_id(std::span<const std::byte> value) {
  return canonical::content_id(canonical::Type::round_state, value);
}

[[nodiscard]] canonical::Bytes read_bytes(const std::filesystem::path& path) {
  std::ifstream input(path, std::ios::binary);
  if (!input) {
    throw BenchmarkError("actual runtime WAL is absent");
  }
  const std::string value{
      std::istreambuf_iterator<char>(input), std::istreambuf_iterator<char>()};
  if (input.bad()) {
    throw BenchmarkError("actual runtime WAL cannot be read");
  }
  return ascii_bytes(value);
}

[[nodiscard]] protocol::RoundState initial_state(
    const FaultEvent& event,
    std::uint32_t ticket_count = 4U) {
  return protocol::RoundState{
      .available_ticket_count = 0U,
      .committed_ticket_count = 0U,
      .config_id = derived_id("stagec-config:", event.event_id),
      .durable_sequence = 0U,
      .height = 1U,
      .parent_checkpoint_id = derived_id("stagec-parent:", event.event_id),
      .phase = protocol::RoundPhase::ticketing_open,
      .round_id = "stagec-" + event.event_id,
      .state_root = derived_id("stagec-current:", event.event_id),
      .ticket_count = ticket_count,
      .view = 0U,
  };
}

[[nodiscard]] Config config(
    const std::filesystem::path& directory,
    const canonical::Bytes& initial) {
  return Config{directory, initial, 64U};
}

[[nodiscard]] protocol::Command command(
    const protocol::RoundState& state,
    std::string kind,
    std::string request_id,
    std::string body,
    std::optional<std::uint64_t> view = std::nullopt,
    std::uint64_t logical_tick = 10U,
    std::string actor_id = "validator-1") {
  return protocol::Command{
      .actor_id = std::move(actor_id),
      .body_hash = std::move(body),
      .command_kind = std::move(kind),
      .height = state.height,
      .logical_tick = logical_tick,
      .request_id = std::move(request_id),
      .round_id = state.round_id,
      .view = view.value_or(state.view),
  };
}

[[nodiscard]] protocol::Vote vote(
    const protocol::RoundState& state,
    std::string_view event_id,
    std::uint64_t validator,
    std::string_view kind,
    std::string_view context,
    std::string_view body) {
  const auto validator_id = "validator-" + std::to_string(validator);
  return protocol::Vote{
      .body_hash = std::string(body),
      .context_id = std::string(context),
      .durable_sequence = validator,
      .height = state.height,
      .kind = std::string(kind),
      .round_id = state.round_id,
      .signature_id = derived_id("stagec-signature:", std::string(event_id) + validator_id),
      .validator_epoch_id = derived_id("stagec-validator-epoch:", event_id),
      .validator_id = validator_id,
      .view = state.view,
  };
}

void append_transition(
    TraceExporter& trace,
    std::string action,
    const SubmitReceipt& receipt,
    std::string outcome) {
  trace.append(TraceEntry{
      .sequence = trace.entries().size() + 1U,
      .action_id = std::move(action),
      .state_id = receipt.next_state_id,
      .effect_id = receipt.effect_batch_id,
      .terminal_outcome = std::move(outcome),
  });
}

void append_vote(
    TraceExporter& trace,
    std::string action,
    std::string state_root,
    const VoteReceipt& receipt,
    std::string outcome) {
  trace.append(TraceEntry{
      .sequence = trace.entries().size() + 1U,
      .action_id = std::move(action),
      .state_id = std::move(state_root),
      .effect_id = receipt.vote_id,
      .terminal_outcome = std::move(outcome),
  });
}

[[nodiscard]] SubmitReceipt submit(
    Runtime& runtime,
    TraceExporter& trace,
    std::string action,
    std::string request_prefix,
    std::string command_kind,
    std::uint64_t logical_tick = 10U,
    std::string actor_id = "validator-1",
    std::optional<std::string> body_override = std::nullopt) {
  const auto state = protocol::parse_round_state(runtime.state_bytes());
  const auto body = body_override.value_or(derived_id("stagec-body:", request_prefix + command_kind));
  auto receipt = runtime.submit(protocol::encode(command(
      state,
      std::move(command_kind),
      std::move(request_prefix),
      std::move(body),
      std::nullopt,
      logical_tick,
      std::move(actor_id))));
  append_transition(trace, std::move(action), receipt, "ACCEPTED");
  return receipt;
}

struct ScenarioObservation {
  std::string outcome;
  canonical::Bytes state_bytes;
  std::string effect_root;
  TraceExporter trace;
  std::uint64_t operation_count{};
  bool wal_replayed{};
  bool view_change_observed{};
  bool current_checkpoint_advanced{};
  bool availability_success{};
  std::string causal_evidence;
};

[[nodiscard]] std::vector<std::string> apply_signers() {
  return {"validator-0", "validator-1", "validator-2"};
}

[[nodiscard]] certificates::Context certificate_context(const FaultEvent& event) {
  return certificates::Context{
      .arithmetic_profile_id = derived_id("stagec-arithmetic-profile:", event.event_id),
      .height = 1U,
      .parameter_schema_id = derived_id("stagec-parameter-schema:", event.event_id),
      .round_config_id = derived_id("stagec-config:", event.event_id),
      .round_id = "stagec-" + event.event_id,
      .validator_epoch_id = derived_id("stagec-validator-epoch:", event.event_id),
      .view = 0U,
  };
}

[[nodiscard]] certificates::ValidatorPolicy validator_policy(const FaultEvent& event) {
  return certificates::ValidatorPolicy{
      .validator_epoch_id = certificate_context(event).validator_epoch_id,
      .validator_ids = {"validator-0", "validator-1", "validator-2", "validator-3"},
      .quorum_threshold = 3U,
  };
}

[[nodiscard]] std::string join_strings(
    const std::vector<std::string>& values,
    std::string_view separator = ",") {
  if (values.empty()) return "NONE";
  std::string result;
  for (std::size_t index = 0U; index < values.size(); ++index) {
    if (index != 0U) result.append(separator);
    result.append(values[index]);
  }
  return result;
}

[[nodiscard]] std::string canonical_causal_fields(
    const std::map<std::string, std::string, std::less<>>& fields) {
  std::string result;
  for (const auto& [name, value] : fields) {
    if (name.empty() || value.empty() || name.find_first_of("\r\n=") != std::string::npos ||
        value.find_first_of("\r\n") != std::string::npos) {
      throw BenchmarkError("causal evidence field is invalid");
    }
    result += name + "=" + value + "\n";
  }
  return result;
}

[[nodiscard]] std::map<std::string, std::string, std::less<>> base_causal_fields(
    const FaultEvent& event,
    const CausalSchedule& schedule) {
  std::vector<std::string> delivered;
  std::vector<std::string> dropped;
  for (const auto& message : schedule.messages) {
    if (message.delivered) {
      delivered.push_back(message.message_id + ":" + std::to_string(message.delivered_tick));
    } else {
      dropped.push_back(message.message_id);
    }
  }
  std::sort(delivered.begin(), delivered.end());
  std::sort(dropped.begin(), dropped.end());
  return {
      {"abort_qc_id", "NONE"},
      {"aggregate_root_qc_id", "NONE"},
      {"aggregate_root_qc_tick", "0"},
      {"apply_qc_id", "NONE"},
      {"apply_qc_tick", "0"},
      {"apply_quorum_threshold", "0"},
      {"apply_validator_set_id", "NONE"},
      {"apply_work_item_id", "NONE"},
      {"causal_transport_receipt_id", schedule.receipt_id},
      {"certified_abort_tick", "0"},
      {"current_checkpoint_advanced", "false"},
      {"current_pointer_after", "NONE"},
      {"current_pointer_before", "NONE"},
      {"dropped_message_ids", join_strings(dropped)},
      {"event_id", event.event_id},
      {"failed_quorum_reason", "NONE"},
      {"gst_tick", std::to_string(schedule.gst_tick)},
      {"hard_deadline_tick", std::to_string(schedule.hard_deadline_tick)},
      {"isc_ticket_set", "NONE"},
      {"loss_fraction", "0/1"},
      {"lost_ticket_ids", "NONE"},
      {"lost_worker_ids", "NONE"},
      {"message_delivery_ticks", join_strings(delivered)},
      {"missing_work_policy_result", "NOT_APPLICABLE"},
      {"next_checkpoint_id", "NONE"},
      {"next_optimizer_state_id", "NONE"},
      {"network_profile_id", schedule.network_profile_id},
      {"parent_checkpoint_id", "NONE"},
      {"parent_optimizer_state_id", "NONE"},
      {"partition_start_tick", "0"},
      {"per_domain_remaining_tickets", "NONE"},
      {"per_domain_required_tickets", "NONE"},
      {"pi_d_renormalized", "false"},
      {"quorum_capacity_after", "0"},
      {"quorum_capacity_before", "0"},
      {"quorum_formation_tick", "0"},
      {"schema_version", "1.0.0"},
      {"unavailable_ids", "NONE"},
      {"worker_count_before", "0"},
      {"worker_count_lost", "0"},
  };
}

struct ApplyObservation {
  std::string aggregate_root_qc_id;
  std::string apply_work_item_id;
  std::string apply_qc_id;
  std::string parent_checkpoint_id;
  std::string next_checkpoint_id;
  std::string parent_optimizer_state_id;
  std::string next_optimizer_state_id;
  std::string current_pointer_before;
  std::string current_pointer_after;
  std::string apply_validator_set_id;
  std::uint32_t apply_quorum_threshold{};
  std::uint64_t aggregate_root_qc_tick{};
  std::uint64_t apply_qc_tick{};
  std::uint64_t operation_count{};
  std::string final_effect_id;
};

[[nodiscard]] std::vector<const CausalMessage*> exact_delivered_votes(
    const CausalSchedule& schedule,
    std::string_view kind) {
  auto votes = messages_of_kind(schedule, kind);
  if (votes.size() != 3U) throw BenchmarkError("causal schedule lacks exact 2f+1 quorum");
  std::vector<std::string> actors;
  for (const auto* vote_message : votes) actors.push_back(vote_message->actor_id);
  std::sort(actors.begin(), actors.end());
  if (actors != apply_signers()) throw BenchmarkError("causal quorum signer set is invalid");
  return votes;
}

[[nodiscard]] ApplyObservation execute_complete_apply(
    const FaultEvent& event,
    const CausalSchedule& schedule,
    const std::filesystem::path& directory,
    std::string_view request_id,
    Runtime& runtime,
    TraceExporter& trace,
    const std::vector<const CausalMessage*>& tickets) {
  if (tickets.empty()) throw BenchmarkError("causal progress has no delivered tickets");
  const auto context = certificate_context(event);
  const auto policy = validator_policy(event);
  certificates::ChainVerifier verifier(context, policy);
  const auto signers = apply_signers();

  std::vector<certificates::InputTuple> tuples;
  std::vector<robust::Contribution> contributions;
  tuples.reserve(tickets.size());
  contributions.reserve(tickets.size());
  std::vector<std::string> ordered_ticket_ids;
  for (const auto* ticket : tickets) ordered_ticket_ids.push_back(ticket->ticket_id);
  std::sort(ordered_ticket_ids.begin(), ordered_ticket_ids.end());
  if (std::adjacent_find(ordered_ticket_ids.begin(), ordered_ticket_ids.end()) !=
      ordered_ticket_ids.end()) {
    throw BenchmarkError("causal ISC has duplicate tickets");
  }
  for (const auto& ticket_id : ordered_ticket_ids) {
    const auto found = std::find_if(tickets.begin(), tickets.end(), [&ticket_id](const auto* item) {
      return item->ticket_id == ticket_id;
    });
    if (found == tickets.end() || ((*found)->domain_id != "code" && (*found)->domain_id != "text")) {
      throw BenchmarkError("causal ISC ticket domain is invalid");
    }
    const auto& ticket = **found;
    tuples.push_back(certificates::InputTuple{
        .availability_certificate_id =
            derived_id("stagec-availability:", event.event_id + ":" + ticket_id),
        .commitment_id = derived_id("stagec-commitment:", event.event_id + ":" + ticket_id),
        .domain_id = ticket.domain_id,
        .ticket_id = ticket_id,
    });
    const auto ordinal = parse_u64(ticket_id.substr(ticket_id.rfind('-') + 1U));
    contributions.push_back(robust::Contribution{
        .domain_id = ticket.domain_id,
        .q_values = {
            static_cast<std::int64_t>(ordinal % 7U + 1U),
            static_cast<std::int64_t>(ordinal % 5U + 2U),
        },
        .ticket_id = ticket_id,
    });
  }
  const auto ticket_transcript = join_strings(ordered_ticket_ids);
  certificates::InputSetCertificate isc{
      .context = context,
      .input_root = derived_id("stagec-input-root:", event.event_id + ":" + ticket_transcript),
      .quorum_threshold = 3U,
      .signer_ids = signers,
      .tuples = std::move(tuples),
  };
  const auto isc_id = verifier.verify_input_set(isc);
  certificates::SeedTranscript seed{
      .context = context,
      .input_set_certificate_id = isc_id,
      .seed_id = derived_id("stagec-seed:", event.event_id),
      .seed_profile_id = derived_id("stagec-seed-profile:", event.event_id),
      .share_ids = {
          derived_id("stagec-seed-share:", event.event_id + ":0"),
          derived_id("stagec-seed-share:", event.event_id + ":1"),
          derived_id("stagec-seed-share:", event.event_id + ":2"),
      },
  };
  std::sort(seed.share_ids.begin(), seed.share_ids.end());
  const auto seed_id = verifier.verify_seed(seed, isc_id);
  const auto accumulator_proof_id = derived_id("stagec-accumulator-proof:", event.event_id);
  auto robust_plan = robust::build_plan(
      context,
      isc_id,
      seed_id,
      derived_id("stagec-robust-profile:", event.event_id),
      seed.seed_id,
      contributions,
      robust::Profile{
          accumulator_proof_id,
          2U,
          2U,
          0U,
          static_cast<std::uint64_t>(contributions.size()),
          100,
          static_cast<std::uint64_t>(contributions.size()),
      },
      signers,
      3U);
  const auto norms_id = verifier.verify_norms(robust_plan.norms, isc_id);
  const auto eligibility_id = verifier.verify_eligibility(robust_plan.eligibility, isc, norms_id);
  const auto plan_id = verifier.verify_plan(
      robust_plan.plan, isc, robust_plan.eligibility, seed_id, accumulator_proof_id);

  std::vector<certificates::ParameterShardQc> shards;
  std::vector<certificates::ShardKey> required;
  std::vector<apply::DomainAggregate> aggregates;
  for (const std::string domain : {"code", "text"}) {
    std::vector<robust::Contribution> domain_contributions;
    std::vector<std::string> leaves;
    for (const auto& contribution : contributions) {
      if (contribution.domain_id == domain) {
        domain_contributions.push_back(contribution);
        leaves.push_back(derived_id(
            "stagec-input-leaf:", event.event_id + ":" + contribution.ticket_id));
      }
    }
    if (domain_contributions.empty()) throw BenchmarkError("causal ISC lost a mandatory domain");
    std::sort(leaves.begin(), leaves.end());
    auto shard = robust::reduce_parameter_shard(
        context,
        isc_id,
        eligibility_id,
        robust_plan.plan,
        domain,
        "shard-000",
        domain_contributions,
        std::move(leaves),
        signers,
        3U);
    std::vector<std::int64_t> values;
    for (const auto& numerator : shard.result_numerators) {
      values.push_back(apply::round_half_toward_positive(
          core::protocol::parse_i64_decimal(numerator), shard.denominator));
    }
    aggregates.push_back(apply::DomainAggregate{domain, std::move(values)});
    required.push_back(certificates::ShardKey{domain, "shard-000"});
    shards.push_back(std::move(shard));
  }
  certificates::AggregateRootQc root{
      .context = context,
      .aggregation_plan_certificate_id = plan_id,
      .eligibility_certificate_id = eligibility_id,
      .input_set_certificate_id = isc_id,
      .leaves = {
          {"code", certificates::content_id(shards[0]), "shard-000"},
          {"text", certificates::content_id(shards[1]), "shard-000"},
      },
      .merkle_root = {},
      .quorum_threshold = 3U,
      .required_keys = required,
      .signer_ids = signers,
  };
  root.merkle_root = certificates::aggregate_merkle_root(root.leaves);
  const auto root_id = verifier.verify_root(root, isc_id, eligibility_id, plan_id, required, shards);

  const auto aggregate_votes = exact_delivered_votes(schedule, "AGGREGATE_VOTE");
  for (std::size_t index = 0U; index < aggregate_votes.size(); ++index) {
    const auto* message = aggregate_votes[index];
    const auto persisted = runtime.record_vote(core::protocol::encode(certificates::make_vote(
        certificates::VoteKind::aggregate_root,
        context,
        root_id,
        message->actor_id,
        derived_id("stagec-aggregate-signature:", event.event_id + ":" + message->actor_id),
        index + 1U)));
    append_vote(
        trace, "ACT-AGGREGATE-ROOT-VOTE", state_id(runtime.state_bytes()), persisted, "DELIVERED");
  }
  const auto aggregate_tick = aggregate_votes.back()->delivered_tick;
  const auto finalized = submit(
      runtime,
      trace,
      "ACT-AGGREGATE-FINALIZE",
      std::string(request_id) + "-aggregate",
      "FINALIZE_AGGREGATE",
      aggregate_tick,
      "validator-1",
      root_id);
  const auto aggregated = protocol::parse_round_state(runtime.state_bytes());
  if (aggregated.phase != protocol::RoundPhase::aggregated || aggregated.state_root != root_id) {
    throw BenchmarkError("actual Feature 003 aggregation did not bind AggregateRootQC");
  }

  certificates::ApplyArithmeticProfile profile{
      .accumulator_proof_id = accumulator_proof_id,
      .domain_weights = {{"code", {1, 2U}}, {"text", {1, 2U}}},
      .learning_rate = {1, 10U},
      .momentum = {9, 10U},
      .nesterov = true,
      .rounding = "HALF_TOWARD_POSITIVE",
      .weight_decay = {1, 100U},
  };
  const auto parent_optimizer_id = derived_id("stagec-parent-optimizer:", event.event_id);
  const apply::State parent{
      {100, -50}, {10, -5}, aggregated.parent_checkpoint_id, parent_optimizer_id};
  auto candidate = apply::compute_candidate(context, root_id, profile, parent, aggregates);
  const auto work_item_id = certificates::content_id(candidate);
  const auto apply_votes = exact_delivered_votes(schedule, "APPLY_VOTE");
  for (std::size_t index = 0U; index < apply_votes.size(); ++index) {
    const auto* message = apply_votes[index];
    const auto persisted = runtime.record_vote(core::protocol::encode(certificates::make_vote(
        certificates::VoteKind::apply,
        context,
        work_item_id,
        message->actor_id,
        derived_id("stagec-apply-signature:", event.event_id + ":" + message->actor_id),
        index + 1U)));
    append_vote(trace, "ACT-APPLY-VOTE", root_id, persisted, "DELIVERED");
  }
  certificates::ApplyQc apply_qc{
      .context = context,
      .aggregate_root_qc_id = root_id,
      .apply_arithmetic_profile_id = certificates::content_id(profile),
      .apply_candidate_id = work_item_id,
      .next_model_hash = candidate.next_model_hash,
      .next_optimizer_hash = candidate.next_optimizer_hash,
      .parent_checkpoint_id = candidate.parent_checkpoint_id,
      .quorum_threshold = 3U,
      .signer_ids = signers,
  };
  const auto apply_qc_id = verifier.verify_apply(
      apply_qc, candidate, root_id, certificates::content_id(profile));
  trace.append(TraceEntry{
      .sequence = trace.entries().size() + 1U,
      .action_id = "ACT-APPLY-FINALIZE",
      .state_id = candidate.next_model_hash,
      .effect_id = apply_qc_id,
      .terminal_outcome = "FINALIZED",
  });

  const auto pointer_directory = directory / "current";
  CurrentPointerStore pointer(
      pointer_directory,
      PointerState{parent.checkpoint_id, parent.optimizer_id, {}, 0U});
  const auto pointer_before = pointer.state();
  const certificates::CurrentPointerCommand pointer_command{
      .context = context,
      .apply_qc_id = apply_qc_id,
      .expected_parent_checkpoint_id = parent.checkpoint_id,
      .next_checkpoint_id = candidate.next_model_hash,
      .next_optimizer_hash = candidate.next_optimizer_hash,
  };
  if (pointer.advance(pointer_command, apply_qc) != PointerDisposition::advanced) {
    throw BenchmarkError("ApplyQC did not advance current checkpoint");
  }
  const auto pointer_after = pointer.state();
  if (pointer_after.checkpoint_id != candidate.next_model_hash ||
      pointer_after.optimizer_id != candidate.next_optimizer_hash ||
      pointer_after.apply_qc_id != apply_qc_id || pointer_after == pointer_before) {
    throw BenchmarkError("APPLIED outcome lacks exact current-pointer advance");
  }
  trace.append(TraceEntry{
      .sequence = trace.entries().size() + 1U,
      .action_id = "ACT-APPLY-CURRENT",
      .state_id = pointer_after.checkpoint_id,
      .effect_id = apply_qc_id,
      .terminal_outcome = "APPLIED",
  });
  const auto validator_set_id = derived_id(
      "stagec-apply-validator-set:", join_strings(policy.validator_ids) + ":3");
  return ApplyObservation{
      .aggregate_root_qc_id = root_id,
      .apply_work_item_id = work_item_id,
      .apply_qc_id = apply_qc_id,
      .parent_checkpoint_id = parent.checkpoint_id,
      .next_checkpoint_id = candidate.next_model_hash,
      .parent_optimizer_state_id = parent.optimizer_id,
      .next_optimizer_state_id = candidate.next_optimizer_hash,
      .current_pointer_before = pointer_before.checkpoint_id,
      .current_pointer_after = pointer_after.checkpoint_id,
      .apply_validator_set_id = validator_set_id,
      .apply_quorum_threshold = 3U,
      .aggregate_root_qc_tick = aggregate_tick,
      .apply_qc_tick = apply_votes.back()->delivered_tick,
      .operation_count = static_cast<std::uint64_t>(tickets.size() * 2U + 11U),
      .final_effect_id = finalized.effect_batch_id,
  };
}

[[nodiscard]] ScenarioObservation execute_progress(
    const FaultEvent& event,
    const std::filesystem::path& directory,
    std::string_view request_id) {
  const auto schedule = parse_causal_schedule(event);
  const auto planned_tickets = messages_of_kind(schedule, "WORK_TICKET", false);
  const auto tickets = messages_of_kind(schedule, "WORK_TICKET");
  if (planned_tickets.size() < tickets.size() || tickets.empty()) {
    throw BenchmarkError("causal ticket schedule is invalid");
  }
  auto fields = base_causal_fields(event, schedule);
  if (event.actor_class == "WORKER") {
    if (planned_tickets.size() != 10U) {
      throw BenchmarkError("worker-loss schedule does not bind the exact worker set");
    }
    std::vector<std::string> lost_workers;
    std::vector<std::string> lost_tickets;
    std::map<std::string, std::size_t, std::less<>> remaining{{"code", 0U}, {"text", 0U}};
    for (const auto* ticket : planned_tickets) {
      if (ticket->delivered) {
        ++remaining.at(ticket->domain_id);
      } else {
        lost_workers.push_back(ticket->actor_id);
        lost_tickets.push_back(ticket->ticket_id);
      }
    }
    fields["worker_count_before"] = "10";
    fields["worker_count_lost"] = std::to_string(lost_workers.size());
    fields["loss_fraction"] = std::to_string(lost_workers.size()) + "/10";
    fields["lost_worker_ids"] = join_strings(lost_workers);
    fields["lost_ticket_ids"] = join_strings(lost_tickets);
    fields["per_domain_required_tickets"] = "code:4,text:4";
    fields["per_domain_remaining_tickets"] =
        "code:" + std::to_string(remaining.at("code")) +
        ",text:" + std::to_string(remaining.at("text"));
    fields["quorum_capacity_before"] = "10";
    fields["quorum_capacity_after"] = std::to_string(tickets.size());
    const bool domain_capacity_sufficient =
        remaining.at("code") >= 4U && remaining.at("text") >= 4U;
    if (!domain_capacity_sufficient) {
      const auto abort_votes = exact_delivered_votes(schedule, "ABORT_VOTE");
      const auto planned_aggregate_votes = messages_of_kind(schedule, "AGGREGATE_VOTE", false);
      const auto planned_apply_votes = messages_of_kind(schedule, "APPLY_VOTE", false);
      if (lost_workers.size() != 2U || tickets.size() != 8U || remaining.at("code") != 3U ||
          remaining.at("text") != 5U ||
          lost_workers != std::vector<std::string>{"worker-000", "worker-001"} ||
          lost_tickets != std::vector<std::string>{"ticket-000", "ticket-001"} ||
          !planned_aggregate_votes.empty() || !planned_apply_votes.empty() ||
          abort_votes.front()->delivered_tick != schedule.hard_deadline_tick ||
          abort_votes.back()->delivered_tick != schedule.hard_deadline_tick) {
        throw BenchmarkError("concentrated worker loss lacks exact mandatory-domain evidence");
      }
      fields["missing_work_policy_result"] = "MANDATORY_DOMAIN_CAPACITY_UNSATISFIED_ABORT";
      fields["failed_quorum_reason"] = "MANDATORY_DOMAIN_CODE_3_OF_4_AT_HARD_DEADLINE";
      fields["certified_abort_tick"] = std::to_string(schedule.hard_deadline_tick);
      fields["unavailable_ids"] = join_strings(lost_workers);
      const auto initial = protocol::encode(initial_state(event, 10U));
      const auto before = protocol::parse_round_state(initial);
      Runtime runtime(config(directory, initial));
      TraceExporter trace;
      for (const auto* ticket : tickets) {
        static_cast<void>(submit(
            runtime,
            trace,
            "ACT-COMMIT",
            std::string(request_id) + "-commit-" + ticket->ticket_id,
            "ACCEPT_COMMITMENT",
            ticket->delivered_tick,
            ticket->actor_id));
      }
      for (const auto* ticket : tickets) {
        static_cast<void>(submit(
            runtime,
            trace,
            "ACT-AVAIL-ATTEST",
            std::string(request_id) + "-availability-" + ticket->ticket_id,
            "ACCEPT_AVAILABILITY",
            ticket->delivered_tick,
            ticket->actor_id));
      }
      const auto abort_body = derived_id("stagec-worker-capacity-abort:", event.event_id);
      std::vector<std::string> abort_vote_ids;
      const auto state_before_abort = protocol::parse_round_state(runtime.state_bytes());
      for (std::size_t index = 0U; index < abort_votes.size(); ++index) {
        const auto* message = abort_votes[index];
        const auto receipt = runtime.record_vote(protocol::encode(protocol::Vote{
            .body_hash = abort_body,
            .context_id = "ABORT:" + state_before_abort.round_id + ":MANDATORY_DOMAIN_CAPACITY",
            .durable_sequence = index + 1U,
            .height = state_before_abort.height,
            .kind = "ABORT",
            .round_id = state_before_abort.round_id,
            .signature_id = derived_id(
                "stagec-worker-abort-signature:", event.event_id + ":" + message->actor_id),
            .validator_epoch_id = certificate_context(event).validator_epoch_id,
            .validator_id = message->actor_id,
            .view = state_before_abort.view,
        }));
        abort_vote_ids.push_back(receipt.vote_id);
        append_vote(trace, "ACT-HARD-ABORT-VOTE", state_id(runtime.state_bytes()), receipt, "DELIVERED");
      }
      trace.append(TraceEntry{
          .sequence = trace.entries().size() + 1U,
          .action_id = "ACT-HARD-DEADLINE",
          .state_id = state_id(runtime.state_bytes()),
          .effect_id = derived_id("stagec-worker-capacity-deadline:", event.event_id),
          .terminal_outcome = "MANDATORY_DOMAIN_UNAVAILABLE",
      });
      const auto aborted = submit(
          runtime,
          trace,
          "ACT-ABORT-FINALIZE",
          std::string(request_id) + "-abort",
          "CERTIFY_ABORT",
          schedule.hard_deadline_tick,
          "validator-1",
          abort_body);
      const auto terminal = protocol::parse_round_state(runtime.state_bytes());
      if (terminal.phase != protocol::RoundPhase::aborted ||
          terminal.parent_checkpoint_id != before.parent_checkpoint_id ||
          terminal.state_root != before.state_root) {
        throw BenchmarkError("mandatory-domain abort changed the current checkpoint");
      }
      fields["abort_qc_id"] =
          derived_id("stagec-worker-abort-qc:", abort_body + ":" + join_strings(abort_vote_ids));
      fields["current_pointer_before"] = before.parent_checkpoint_id;
      fields["current_pointer_after"] = before.parent_checkpoint_id;
      fields["parent_checkpoint_id"] = before.parent_checkpoint_id;
      return ScenarioObservation{
          .outcome = "ABORTED",
          .state_bytes = runtime.state_bytes(),
          .effect_root = aborted.effect_batch_id,
          .trace = std::move(trace),
          .operation_count = static_cast<std::uint64_t>(tickets.size() * 2U + 5U),
          .current_checkpoint_advanced = false,
          .availability_success = false,
          .causal_evidence = canonical_causal_fields(fields),
      };
    }
    if (lost_workers.size() != 1U || tickets.size() != 9U) {
      throw BenchmarkError("successful worker loss is not the exact 10 percent scenario");
    }
    fields["missing_work_policy_result"] = "OMIT_PRE_FREEZE_LOST_TICKET_EXACT_ISC";
  }
  std::vector<std::string> ticket_ids;
  for (const auto* ticket : tickets) ticket_ids.push_back(ticket->ticket_id);
  std::sort(ticket_ids.begin(), ticket_ids.end());
  fields["isc_ticket_set"] = join_strings(ticket_ids);

  const auto initial = protocol::encode(
      initial_state(event, static_cast<std::uint32_t>(planned_tickets.size())));
  Runtime runtime(config(directory, initial));
  TraceExporter trace;
  for (const auto* ticket : tickets) {
    static_cast<void>(submit(
        runtime,
        trace,
        "ACT-COMMIT",
        std::string(request_id) + "-commit-" + ticket->ticket_id,
        "ACCEPT_COMMITMENT",
        ticket->delivered_tick,
        ticket->actor_id));
  }
  for (const auto* ticket : tickets) {
    static_cast<void>(submit(
        runtime,
        trace,
        "ACT-AVAIL-ATTEST",
        std::string(request_id) + "-availability-" + ticket->ticket_id,
        "ACCEPT_AVAILABILITY",
        ticket->delivered_tick,
        ticket->actor_id));
  }
  static_cast<void>(submit(
      runtime,
      trace,
      "ACT-ISC-FINALIZE",
      std::string(request_id) + "-freeze",
      "FINALIZE_INPUT_FREEZE",
      tickets.back()->delivered_tick));
  const auto applied = execute_complete_apply(
      event, schedule, directory, request_id, runtime, trace, tickets);
  fields["aggregate_root_qc_id"] = applied.aggregate_root_qc_id;
  fields["aggregate_root_qc_tick"] = std::to_string(applied.aggregate_root_qc_tick);
  fields["apply_qc_id"] = applied.apply_qc_id;
  fields["apply_qc_tick"] = std::to_string(applied.apply_qc_tick);
  fields["apply_quorum_threshold"] = std::to_string(applied.apply_quorum_threshold);
  fields["apply_validator_set_id"] = applied.apply_validator_set_id;
  fields["apply_work_item_id"] = applied.apply_work_item_id;
  fields["current_checkpoint_advanced"] = "true";
  fields["current_pointer_after"] = applied.current_pointer_after;
  fields["current_pointer_before"] = applied.current_pointer_before;
  fields["next_checkpoint_id"] = applied.next_checkpoint_id;
  fields["next_optimizer_state_id"] = applied.next_optimizer_state_id;
  fields["parent_checkpoint_id"] = applied.parent_checkpoint_id;
  fields["parent_optimizer_state_id"] = applied.parent_optimizer_state_id;
  fields["quorum_formation_tick"] = std::to_string(applied.aggregate_root_qc_tick);
  if (event.actor_class == "REGION") {
    if (applied.aggregate_root_qc_tick <= schedule.gst_tick ||
        applied.apply_qc_tick <= applied.aggregate_root_qc_tick ||
        applied.apply_qc_tick >= schedule.hard_deadline_tick) {
      throw BenchmarkError("eventual-synchrony schedule did not causally reach ApplyQC");
    }
  }
  return ScenarioObservation{
      .outcome = "APPLIED",
      .state_bytes = runtime.state_bytes(),
      .effect_root = applied.apply_qc_id,
      .trace = std::move(trace),
      .operation_count = applied.operation_count,
      .current_checkpoint_advanced = true,
      .availability_success = true,
      .causal_evidence = canonical_causal_fields(fields),
  };
}

[[nodiscard]] ScenarioObservation execute_validator_crash(
    const FaultEvent& event,
    const std::filesystem::path& directory,
    std::string_view request_id) {
  const auto schedule = parse_causal_schedule(event);
  const auto delivered_votes = exact_delivered_votes(schedule, "VIEW_CHANGE_VOTE");
  auto fields = base_causal_fields(event, schedule);
  const auto initial = protocol::encode(initial_state(event));
  Runtime runtime(config(directory, initial));
  TraceExporter trace;
  const auto state = protocol::parse_round_state(initial);
  const auto body = derived_id("stagec-view-change-body:", event.event_id);
  const auto context = "VIEW-CHANGE:" + state.round_id + ":1";
  for (std::size_t index = 0U; index < delivered_votes.size(); ++index) {
    const auto* delivered = delivered_votes[index];
    const auto receipt = runtime.record_vote(
        protocol::encode(protocol::Vote{
            .body_hash = body,
            .context_id = context,
            .durable_sequence = index + 1U,
            .height = state.height,
            .kind = "VIEW_CHANGE",
            .round_id = state.round_id,
            .signature_id = derived_id(
                "stagec-view-change-signature:", event.event_id + ":" + delivered->actor_id),
            .validator_epoch_id = certificate_context(event).validator_epoch_id,
            .validator_id = delivered->actor_id,
            .view = state.view,
        }));
    append_vote(trace, "ACT-VIEW-VOTE", state_id(runtime.state_bytes()), receipt, "ACCEPTED");
  }
  const auto changed = runtime.submit(protocol::encode(command(
      state,
      "ADVANCE_VIEW",
      std::string(request_id) + "-view-change",
      body,
      1U,
      delivered_votes.back()->delivered_tick)));
  append_transition(trace, "ACT-VIEW-FINALIZE", changed, "FINALIZED");
  const auto terminal = protocol::parse_round_state(runtime.state_bytes());
  const bool observed = terminal.view == 1U && runtime.recovered_vote_count() == 3U;
  if (!observed) {
    throw BenchmarkError("validator crash lacks actual view-change evidence");
  }
  return ScenarioObservation{
      .outcome = "VIEW_CHANGE",
      .state_bytes = runtime.state_bytes(),
      .effect_root = changed.effect_batch_id,
      .trace = std::move(trace),
      .operation_count = 4U,
      .view_change_observed = true,
      .causal_evidence = canonical_causal_fields(fields),
  };
}

[[nodiscard]] ScenarioObservation execute_validator_restart(
    const FaultEvent& event,
    const std::filesystem::path& directory) {
  const auto schedule = parse_causal_schedule(event);
  const auto recovery_signals = messages_of_kind(schedule, "RECOVERY_SIGNAL");
  if (recovery_signals.size() != 1U) {
    throw BenchmarkError("validator restart lacks delivered recovery signal");
  }
  auto fields = base_causal_fields(event, schedule);
  const auto initial = protocol::encode(initial_state(event));
  const auto state = protocol::parse_round_state(initial);
  const auto body = derived_id("stagec-recovery-vote-body:", event.event_id);
  const auto context = "ROUND_CONFIG:" + state.round_id + ":1:0";
  const auto frame = protocol::encode(vote(state, event.event_id, 1U, "ROUND_CONFIG", context, body));
  if (!std::filesystem::exists(directory / "runtime.wal")) {
    Runtime crashed(config(directory, initial));
    try {
      static_cast<void>(crashed.record_vote(frame, CrashPoint::after_durability_before_commit));
      throw BenchmarkError("validator restart fault injection did not crash runtime");
    } catch (const RuntimeError& error) {
      if (error.code() != ErrorCode::simulated_crash) {
        throw;
      }
    }
  }
  Runtime recovered(config(directory, initial));
  if (recovered.recovered_vote_count() != 1U) {
    throw BenchmarkError("validator restart did not recover durable vote journal");
  }
  const auto replay = recovered.record_vote(frame);
  if (!replay.replay || replay.journal_sequence != 1U) {
    throw BenchmarkError("validator restart accepted vote without exact WAL replay");
  }
  TraceExporter trace;
  const auto root = state_id(recovered.state_bytes());
  append_vote(trace, "ACT-CRASH-AFTER-DURABILITY", root, replay, "FAULT");
  append_vote(trace, "ACT-JOURNAL-RECOVER", root, replay, "RECOVERED");
  append_vote(trace, "ACT-MESSAGE-REPLAY", root, replay, "NO_OP");
  return ScenarioObservation{
      .outcome = "RECOVERED",
      .state_bytes = recovered.state_bytes(),
      .effect_root = replay.vote_id,
      .trace = std::move(trace),
      .operation_count = 3U,
      .wal_replayed = true,
      .causal_evidence = canonical_causal_fields(fields),
  };
}

[[nodiscard]] ScenarioObservation execute_storage_crash(
    const FaultEvent& event,
    const std::filesystem::path& directory,
    std::string_view request_id) {
  const auto schedule = parse_causal_schedule(event);
  const auto storage_signals = messages_of_kind(schedule, "STORAGE_SIGNAL");
  if (!storage_signals.empty()) {
    throw BenchmarkError("storage crash unexpectedly delivered availability signal");
  }
  auto fields = base_causal_fields(event, schedule);
  const auto initial = protocol::encode(initial_state(event));
  Runtime runtime(config(directory, initial));
  TraceExporter trace;
  const auto committed = submit(
      runtime, trace, "ACT-COMMIT", std::string(request_id) + "-commit", "ACCEPT_COMMITMENT");
  const auto state = protocol::parse_round_state(runtime.state_bytes());
  bool rejected_without_availability = false;
  try {
    const auto body = derived_id("stagec-body:", event.event_id + std::string("freeze"));
    static_cast<void>(runtime.submit(protocol::encode(command(
        state,
        "FINALIZE_INPUT_FREEZE",
        std::string(request_id) + "-forbidden-freeze",
        body))));
  } catch (const core::transition::TransitionError&) {
    rejected_without_availability = true;
  }
  const auto terminal = protocol::parse_round_state(runtime.state_bytes());
  if (!rejected_without_availability || terminal.available_ticket_count != 0U ||
      terminal.phase != protocol::RoundPhase::committed) {
    throw BenchmarkError("storage crash fabricated availability success");
  }
  return ScenarioObservation{
      .outcome = "RETRIEVAL",
      .state_bytes = runtime.state_bytes(),
      .effect_root = committed.effect_batch_id,
      .trace = std::move(trace),
      .operation_count = 2U,
      .availability_success = false,
      .causal_evidence = canonical_causal_fields(fields),
  };
}

[[nodiscard]] ScenarioObservation execute_storage_restart(
    const FaultEvent& event,
    const std::filesystem::path& directory,
    std::string_view request_id) {
  const auto schedule = parse_causal_schedule(event);
  const auto storage_signals = messages_of_kind(schedule, "STORAGE_SIGNAL");
  if (storage_signals.size() != 1U) {
    throw BenchmarkError("storage restart lacks delivered repair signal");
  }
  auto fields = base_causal_fields(event, schedule);
  const auto initial = protocol::encode(initial_state(event));
  TraceExporter trace;
  {
    Runtime before_restart(config(directory, initial));
    const auto committed = submit(
        before_restart,
        trace,
        "ACT-COMMIT",
        std::string(request_id) + "-commit",
        "ACCEPT_COMMITMENT");
    static_cast<void>(committed);
  }
  Runtime recovered(config(directory, initial));
  const auto recovered_state = protocol::parse_round_state(recovered.state_bytes());
  if (recovered.journal_sequence() < 1U ||
      recovered_state.phase != protocol::RoundPhase::committed) {
    throw BenchmarkError("storage restart did not recover committed state from WAL");
  }
  const auto available = submit(
      recovered,
      trace,
      "ACT-ARTIFACT-REPAIR",
      std::string(request_id) + "-availability",
      "ACCEPT_AVAILABILITY");
  const auto terminal = protocol::parse_round_state(recovered.state_bytes());
  if (terminal.phase != protocol::RoundPhase::available ||
      terminal.available_ticket_count != 1U) {
    throw BenchmarkError("storage restart did not restore exact artifact availability");
  }
  return ScenarioObservation{
      .outcome = "RECOVERED",
      .state_bytes = recovered.state_bytes(),
      .effect_root = available.effect_batch_id,
      .trace = std::move(trace),
      .operation_count = 2U,
      .wal_replayed = true,
      .availability_success = true,
      .causal_evidence = canonical_causal_fields(fields),
  };
}

[[nodiscard]] ScenarioObservation execute_partition(
    const FaultEvent& event,
    const std::filesystem::path& directory,
    std::string_view request_id) {
  const auto schedule = parse_causal_schedule(event);
  const auto planned_tickets = messages_of_kind(schedule, "WORK_TICKET", false);
  const auto tickets = messages_of_kind(schedule, "WORK_TICKET");
  const auto planned_aggregate_votes = messages_of_kind(schedule, "AGGREGATE_VOTE", false);
  const auto delivered_aggregate_votes = messages_of_kind(schedule, "AGGREGATE_VOTE");
  const auto abort_votes = exact_delivered_votes(schedule, "ABORT_VOTE");
  if (planned_tickets.size() != 4U || tickets.size() != 4U ||
      planned_aggregate_votes.size() != 4U || delivered_aggregate_votes.size() >= 3U ||
      abort_votes.front()->delivered_tick != schedule.hard_deadline_tick ||
      abort_votes.back()->delivered_tick != schedule.hard_deadline_tick) {
    throw BenchmarkError("partition schedule does not prove deadline-caused quorum loss");
  }
  auto fields = base_causal_fields(event, schedule);
  const auto initial = protocol::encode(initial_state(event, 4U));
  const auto before = protocol::parse_round_state(initial);
  Runtime runtime(config(directory, initial));
  TraceExporter trace;
  for (const auto* ticket : tickets) {
    static_cast<void>(submit(
        runtime,
        trace,
        "ACT-COMMIT",
        std::string(request_id) + "-commit-" + ticket->ticket_id,
        "ACCEPT_COMMITMENT",
        ticket->delivered_tick,
        ticket->actor_id));
  }
  for (const auto* ticket : tickets) {
    static_cast<void>(submit(
        runtime,
        trace,
        "ACT-AVAIL-ATTEST",
        std::string(request_id) + "-availability-" + ticket->ticket_id,
        "ACCEPT_AVAILABILITY",
        ticket->delivered_tick,
        ticket->actor_id));
  }
  static_cast<void>(submit(
      runtime,
      trace,
      "ACT-ISC-FINALIZE",
      std::string(request_id) + "-freeze",
      "FINALIZE_INPUT_FREEZE",
      tickets.back()->delivered_tick));
  const auto terminal_before_abort = protocol::parse_round_state(runtime.state_bytes());
  const auto aggregate_body = derived_id("stagec-partition-aggregate:", event.event_id);
  for (std::size_t index = 0U; index < delivered_aggregate_votes.size(); ++index) {
    const auto* message = delivered_aggregate_votes[index];
    const auto receipt = runtime.record_vote(protocol::encode(protocol::Vote{
        .body_hash = aggregate_body,
        .context_id = "AGGREGATE_ROOT_QC:" + terminal_before_abort.round_id,
        .durable_sequence = index + 1U,
        .height = terminal_before_abort.height,
        .kind = "AGGREGATE_ROOT_QC",
        .round_id = terminal_before_abort.round_id,
        .signature_id = derived_id(
            "stagec-partition-aggregate-signature:", event.event_id + ":" + message->actor_id),
        .validator_epoch_id = certificate_context(event).validator_epoch_id,
        .validator_id = message->actor_id,
        .view = terminal_before_abort.view,
    }));
    append_vote(trace, "ACT-AGGREGATE-ROOT-VOTE", state_id(runtime.state_bytes()), receipt, "DELIVERED");
  }
  const auto abort_body = derived_id("stagec-abort-body:", event.event_id);
  std::vector<std::string> abort_vote_ids;
  for (std::size_t index = 0U; index < abort_votes.size(); ++index) {
    const auto* message = abort_votes[index];
    const auto receipt = runtime.record_vote(protocol::encode(protocol::Vote{
        .body_hash = abort_body,
        .context_id = "ABORT:" + terminal_before_abort.round_id + ":HARD_DEADLINE",
        .durable_sequence = index + 1U,
        .height = terminal_before_abort.height,
        .kind = "ABORT",
        .round_id = terminal_before_abort.round_id,
        .signature_id =
            derived_id("stagec-abort-signature:", event.event_id + ":" + message->actor_id),
        .validator_epoch_id = certificate_context(event).validator_epoch_id,
        .validator_id = message->actor_id,
        .view = terminal_before_abort.view,
    }));
    abort_vote_ids.push_back(receipt.vote_id);
    append_vote(trace, "ACT-HARD-ABORT-VOTE", state_id(runtime.state_bytes()), receipt, "DELIVERED");
  }
  trace.append(TraceEntry{
      .sequence = trace.entries().size() + 1U,
      .action_id = "ACT-HARD-DEADLINE",
      .state_id = state_id(runtime.state_bytes()),
      .effect_id = derived_id("stagec-deadline:", event.event_id),
      .terminal_outcome = "QUORUM_UNAVAILABLE",
  });
  const auto aborted = submit(
      runtime,
      trace,
      "ACT-ABORT-FINALIZE",
      std::string(request_id) + "-abort",
      "CERTIFY_ABORT",
      schedule.hard_deadline_tick,
      "validator-1",
      abort_body);
  const auto terminal = protocol::parse_round_state(runtime.state_bytes());
  const bool current_advanced = terminal.parent_checkpoint_id != before.parent_checkpoint_id ||
                                terminal.state_root != before.state_root;
  if (terminal.phase != protocol::RoundPhase::aborted || current_advanced) {
    throw BenchmarkError("partition advanced current checkpoint");
  }
  std::vector<std::string> unavailable;
  for (const auto* message : planned_aggregate_votes) {
    if (!message->delivered) unavailable.push_back(message->actor_id);
  }
  std::sort(unavailable.begin(), unavailable.end());
  fields["abort_qc_id"] =
      derived_id("stagec-abort-qc:", abort_body + ":" + join_strings(abort_vote_ids));
  fields["certified_abort_tick"] = std::to_string(schedule.hard_deadline_tick);
  fields["current_pointer_after"] = before.parent_checkpoint_id;
  fields["current_pointer_before"] = before.parent_checkpoint_id;
  fields["failed_quorum_reason"] = "AGGREGATE_ROOT_QC_2_OF_3_AT_HARD_DEADLINE";
  fields["parent_checkpoint_id"] = before.parent_checkpoint_id;
  fields["partition_start_tick"] = std::to_string(event.logical_step);
  fields["quorum_capacity_before"] = "4";
  fields["quorum_capacity_after"] = std::to_string(delivered_aggregate_votes.size());
  fields["unavailable_ids"] = join_strings(unavailable);
  return ScenarioObservation{
      .outcome = "ABORTED",
      .state_bytes = runtime.state_bytes(),
      .effect_root = aborted.effect_batch_id,
      .trace = std::move(trace),
      .operation_count = static_cast<std::uint64_t>(tickets.size() * 2U + 8U),
      .current_checkpoint_advanced = current_advanced,
      .causal_evidence = canonical_causal_fields(fields),
  };
}

[[nodiscard]] ScenarioObservation observe(
    const FaultEvent& event,
    const std::filesystem::path& directory,
    std::string_view request_id) {
  if (!event.assumptions_hold) {
    const auto initial = protocol::encode(initial_state(event));
    return ScenarioObservation{
        .outcome = "SAFE_BLOCKED",
        .state_bytes = initial,
        .effect_root = raw_id(ascii_bytes("NO_EXTERNALLY_SENDABLE_EFFECT")),
        .trace = {},
        .operation_count = 0U,
        .wal_replayed = false,
        .view_change_observed = false,
        .current_checkpoint_advanced = false,
        .availability_success = false,
        .causal_evidence = {},
    };
  }
  if ((event.actor_class == "WORKER" && event.action == FaultAction::crash) ||
      (event.actor_class == "REGION" && event.action == FaultAction::delay)) {
    return execute_progress(event, directory, request_id);
  }
  if (event.actor_class == "VALIDATOR" && event.action == FaultAction::crash) {
    return execute_validator_crash(event, directory, request_id);
  }
  if (event.actor_class == "VALIDATOR" && event.action == FaultAction::restart) {
    return execute_validator_restart(event, directory);
  }
  if (event.actor_class == "STORAGE" && event.action == FaultAction::crash) {
    return execute_storage_crash(event, directory, request_id);
  }
  if (event.actor_class == "STORAGE" && event.action == FaultAction::restart) {
    return execute_storage_restart(event, directory, request_id);
  }
  if (event.actor_class == "REGION" && event.action == FaultAction::partition) {
    return execute_partition(event, directory, request_id);
  }
  throw BenchmarkError("fault scenario has no production runtime projection");
}

}  // namespace

FaultExecutionResult execute_fault_scenario(
    const FaultEvent& event,
    const std::filesystem::path& directory,
    std::string_view request_id) {
  std::filesystem::create_directories(directory);
  auto observation = observe(event, directory, request_id);
  if (observation.outcome != "SAFE_BLOCKED" && observation.operation_count == 0U) {
    throw BenchmarkError("fault observation has no actual runtime operation");
  }
  const auto trace = observation.trace.canonical_text();
  if (observation.outcome != "SAFE_BLOCKED" && trace.empty()) {
    throw BenchmarkError("fault observation has no actual runtime trace");
  }
  if (observation.outcome != "SAFE_BLOCKED" && observation.causal_evidence.empty()) {
    throw BenchmarkError("fault observation lacks causal transport evidence");
  }
  if ((observation.outcome == "APPLIED") != observation.current_checkpoint_advanced) {
    throw BenchmarkError("APPLIED must be equivalent to verified current-pointer advance");
  }
  const auto wal = observation.outcome == "SAFE_BLOCKED"
                       ? ascii_bytes("NO_DURABLE_TRANSITION")
                       : read_bytes(directory / "runtime.wal");
  return FaultExecutionResult{
      .observed_outcome = std::move(observation.outcome),
      .native_trace_id = raw_id(ascii_bytes(trace)),
      .native_state_root = state_id(observation.state_bytes),
      .native_effect_root = std::move(observation.effect_root),
      .native_wal_sha256 = raw_id(wal),
      .canonical_trace = trace,
      .runtime_operation_count = observation.operation_count,
      .wal_replayed = observation.wal_replayed,
      .view_change_observed = observation.view_change_observed,
      .current_checkpoint_advanced = observation.current_checkpoint_advanced,
      .availability_success = observation.availability_success,
      .canonical_causal_evidence = std::move(observation.causal_evidence),
  };
}

}  // namespace delta::runtime::benchmark
