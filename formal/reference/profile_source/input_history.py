"""Join original ticket/manifest/AC/close inputs to one native ledger facet.

This is part of the independent source fold, not a complete origin certificate.
All byte inputs are selected from original occurrences/backward dependencies.
The enclosing fold still checks lease/phase/time, normalized close-policy origin,
transport/control and durable producer edges. Unknown input layouts stay pending.
No current physical availability premise, supplied ledger or frozen tuple list
is accepted here.
"""

from dataclasses import dataclass

from formal.reference.isc_crypto.codec import CodecError, _require
from formal.reference.isc_source import identity as isc
from formal.reference.profile_source import availability_ledger as ledger
from formal.reference.profile_source import configuration as cfg
from formal.reference.profile_source import configuration_history as configs
from formal.reference.profile_source import manifest_context as manifests
from formal.reference.profile_source import scheduling
from formal.reference.profile_source import source_prefix as source
from formal.scripts import native_source_artifacts as native


@dataclass(frozen=True)
class Closed:
    original: source.Event
    body: isc.Body
    ledger: ledger.Ledger


@dataclass(frozen=True)
class Prefix:
    original_events: tuple[source.Event, ...]
    configuration: configs.History
    ledger: ledger.Ledger
    issued: tuple[tuple[source.Event, bytes], ...]
    closed: tuple[Closed, ...]
    dispositions: tuple[tuple[int, str], ...]
    # These are source-format/required-byte gaps, never silently failed votes.
    unresolved: tuple[source.Event, ...]
    # Even successful entries still need the outer native/control producer.
    producer_edges: tuple[source.Event, ...]


def metadata_inputs(events, event):
    """Build only existing domain identities from exact available raw inputs.

    The content-kind tag selects the existing004 domain; the full decoder then
    checks all fields/links. No invented manifest reference or later artifact.
    """
    kinds = {
        "PARAMETER_SCHEMA": "schema",
        "FIXED_POINT_PROFILE": "profile",
        "QUANTIZATION_SCALE_TABLE": "scale",
        "SHARD_PLAN": "plan",
        "FIXEDPOINT_ROUND_CONFIG": "config",
        "ACCUMULATOR_PROOF_INSTANCE": "proof",
        "ENCODED_CONTRIBUTION_MANIFEST": "manifest",
    }
    result = {}
    for raw in (event.original, *source.dependency_inputs(events, event)):
        try:
            value = manifests.decode(raw)
        except CodecError:
            continue
        kind = kinds.get(value.get("type_name"))
        # The original parameter schema has no envelope type_name. Its closed
        # decoder remains authoritative; this is lookup, not schema admission.
        if kind is None and set(value) == {
            "frozen_omission_policy",
            "parameters",
            "schema_version",
            "tied_aliases",
        }:
            kind = "schema"
        if kind is not None:
            identifier = native.content_id(raw, native.DOMAINS[kind])
            _require(identifier not in result or result[identifier] == raw, "input hash collision")
            result[identifier] = raw
    return result


def bound_plan(plan, original_config):
    scheduling.verify_plan(plan)
    body = cfg.decode(original_config)
    config_id = cfg.content_id(cfg.DOMAIN, original_config)
    _require(plan.semantics == body["formal_semantics_id"], "same original plan generation")
    p = plan.value
    _require(
        p["round_config_id"] == config_id
        and p["parent_checkpoint_id"] == body["parent_checkpoint_id"]
        and p["parameter_schema_id"] == body["parameter_schema_id"],
        "full original plan/configuration context",
    )
    policies = [scheduling.decode(raw) for raw in plan.policies]
    _require(
        [{"domain_id": p["domain_id"], "ticket_count": p["ticket_count"]} for p in policies]
        == body["domain_ticket_counts"]
        and all(
            p["batch_budget"] == body["batch_budget"] and p["step_budget"] == body["step_budget"]
            for p in policies
        )
        and p["lease_policy"]["hard_deadline_tick"] == int(body["hard_deadline_tick"]),
        "complete original ticket budget/deadline association",
    )
    return body, {scheduling.decode(raw)["ticket_id"]: raw for raw in plan.tickets}


def reconstruct(
    events, validators, storage, backend, plan, original_config, declaration, *, actor, close_policy
):
    """Read the existing original byte carriers and derive this ledger from empty.

    The initial planner/configuration arguments retain explicit provenance
    obligations; no dataclass or successful R2 result is accepted as authority.
    In particular `close_policy` must later be bound to normalized configuration.
    """
    _require(close_policy in ("OMIT_UNAVAILABLE", "ABORT_ON_INCOMPLETE"), "existing close policy")
    value, tickets = bound_plan(plan, original_config)
    configuration = cfg.bind(validators, storage, original_config, declaration)
    _require(actor in [name for name, _ in validators.validators], "original enrolled receiver")
    state, config_state = ledger.empty(tuple(sorted(tickets))), configs.History()
    issued, closed, outcomes, unresolved, producers = {}, [], [], [], []
    for i, event in enumerate(events):
        _require(event.index == i, "complete original ordered source prefix")
        occurrence = event.occurrence()
        # One local CONFIG facet. Other actors' source occurrences remain; they
        # cannot supply this receiver's proposal/finality/delivery state.
        if event.actor == actor and event.action == "ACT-CONFIG-PROPOSE":
            try:
                declared = source.declaration_for(event, event.original)
            except CodecError:
                config_state = configs.observed(config_state, occurrence)
                unresolved.append(event)
            else:
                config_state = configs.propose(
                    config_state, occurrence, validators, storage, declared
                ).state
        elif event.actor == actor and event.action == "ACT-CONFIG-FINALIZE":
            config_state = configs.finalize(
                config_state, occurrence, validators, storage, backend
            ).state
        elif event.actor == actor and event.action == "ACT-MESSAGE-DELIVER":
            config_state = configs.deliver(config_state, occurrence, validators, backend).state
        else:
            config_state = configs.observed(config_state, occurrence)
        disposition = "other_original_action"
        try:
            if event.action == "ACT-TICKET-ISSUE":
                ticket = scheduling.decode(event.original)
                selected = tickets.get(ticket.get("ticket_id"))
                _require(selected == event.original, "original issued ticket from full plan")
                originals = source.dependency_inputs(events, event)
                _require(
                    plan.original in originals and all(raw in originals for raw in plan.policies),
                    "original plan/input bytes at issue",
                )
                configs.finalized_config(config_state, configuration.body_id)
                name = ticket["ticket_id"]
                disposition = "ticket_replay" if name in issued else "ticket_issued"
                issued.setdefault(name, (event, event.original))
                state = ledger.observed(state, occurrence)
                producers.append(event)
            elif event.action == "ACT-COMMIT":
                raw = manifests.decode(event.original)
                _require(
                    raw.get("type_name") == "ENCODED_CONTRIBUTION_MANIFEST",
                    "original commitment manifest carrier required",
                )
                originals = metadata_inputs(events, event)
                mid = native.content_id(event.original, native.DOMAINS["manifest"])
                manifest = manifests.resolve(originals, validators.formal_semantics_id, mid)
                _require(manifest.ticket_id in issued, "original ticket not issued at commit cut")
                ticket_raw = issued[manifest.ticket_id][1]
                _require(
                    ticket_raw in source.dependency_inputs(events, event), "original ticket input"
                )
                ticket = scheduling.decode(ticket_raw)
                _require(
                    ticket["domain_id"] == manifest.domain_id
                    and ticket["parent_checkpoint_id"] == manifest.parent_id,
                    "original ticket/manifest domain and parent",
                )
                commitment = ledger.Commitment(manifest.ticket_id, manifest.commitment_id)
                manifests.bind_context(
                    validators, storage, original_config, declaration, originals, mid, commitment
                )
                result = ledger.record_commitment(state, occurrence, commitment)
                state, disposition = result.state, result.disposition
                producers.append(event)
            elif event.actor == actor and event.action == "ACT-MESSAGE-DELIVER":
                state = ledger.deliver(state, occurrence)
                disposition = "retained_original_delivery"
            elif event.actor == actor and event.action == "ACT-AVAIL-FINALIZE":
                ac = manifests.storage.load(event.original)
                originals = metadata_inputs(events, event)
                candidates = []
                for key, raw in originals.items():
                    obj = manifests.decode(raw)
                    if (
                        obj.get("type_name") == "ENCODED_CONTRIBUTION_MANIFEST"
                        and obj.get("ticket_id") == ac.get("ticket_id")
                        and obj.get("commitment_root") == ac.get("commitment_id")
                    ):
                        candidates.append(key)
                _require(len(candidates) == 1, "one original complete committed manifest")
                result = ledger.record_source_availability(
                    state,
                    occurrence,
                    validators,
                    storage,
                    backend,
                    original_config,
                    declaration,
                    originals,
                    candidates[0],
                )
                state, disposition = result.state, result.disposition
                producers.append(event)
            elif event.actor == actor and event.action == "ACT-INPUT-CLOSE":
                configs.finalized_config(config_state, configuration.body_id)
                _require(
                    close_policy == "OMIT_UNAVAILABLE" or len(state.availabilities) == len(tickets),
                    "incomplete original input set",
                )
                result = ledger.freeze(state, occurrence)
                _require(result.state.frozen is not None, "original nonempty input guard")
                domains = {
                    name: scheduling.decode(raw)["domain_id"] for name, raw in tickets.items()
                }
                tuples = ledger.original_tuples(result.state, domains)
                profile = scheduling.decode(plan.policies[0])["arithmetic_profile_id"]
                body = isc.Body(
                    validators.formal_semantics_id,
                    profile,
                    configuration.height,
                    value["parameter_schema_id"],
                    configuration.body_id,
                    configuration.round_id,
                    validators.validator_epoch_id,
                    configuration.view,
                    configuration.parent,
                    isc.input_root(tuples),
                    tuples,
                )
                _require(
                    event.original == isc.body_preimage(body), "whole original closed body differs"
                )
                state, disposition = result.state, result.disposition
                closed.append(Closed(event, body, state))
                producers.append(event)
            else:
                state = ledger.observed(state, occurrence)
        except (CodecError, native.SourceError):
            # Do not infer a legal rejection from an incomplete producer source.
            # Preserve the complete attempted event and prevent full qualification.
            if not state.events or state.events[-1].index != event.index:
                state = ledger.observed(state, occurrence)
            unresolved.append(event)
            disposition = "original_input_or_producer_edge_unresolved"
        outcomes.append((event.index, disposition))
    return Prefix(
        tuple(events),
        config_state,
        state,
        tuple(issued.values()),
        tuple(closed),
        tuple(outcomes),
        tuple(unresolved),
        tuple(producers),
    )
