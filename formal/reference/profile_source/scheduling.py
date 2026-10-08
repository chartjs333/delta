"""Original feature-007 planner and durable lease producer, as pure source rules.

This is a reference projection of the pinned native functions, not a new wire
format, BFT authority or production recovery implementation. Raw command/input
occurrences and DSJ1 records remain separate. The enclosing source fold must
bind a command's fields to its original invocation and finalized configuration.
No public refinement result is a premise of these rules.
"""

import json
import re
from dataclasses import dataclass, replace
from hashlib import sha256
from itertools import pairwise

from formal.reference.isc_crypto.codec import CodecError, _id, _pairs, _require

U64 = 2**64 - 1
CONTEXT = (
    "arithmetic_profile_id",
    "parameter_schema_id",
    "parent_checkpoint_id",
    "round_config_id",
)
COMMON = {"formal_semantics_id", "schema_version", "type_name"}
POLICY_FIELDS = (
    COMMON
    | set(CONTEXT)
    | {
        "allocation_policy",
        "batch_budget",
        "dataset_manifest_id",
        "domain_id",
        "eligibility_policy_id",
        "mixture_coefficient_id",
        "region_ids",
        "step_budget",
        "ticket_count",
        "token_cursor_end",
        "token_cursor_start",
    }
)
LEASE_FIELDS = COMMON | {
    "expiry_tick",
    "issue_tick",
    "lease_epoch",
    "plan_id",
    "prior_lease_id",
    "region_route",
    "renewal_count",
    "round_config_id",
    "state",
    "ticket_content_id",
    "ticket_id",
    "worker_id",
}


def uint(n):
    _require(type(n) is int and 0 <= n <= U64, "original native uint64")
    return n


def label(s):
    _require(type(s) is str and re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", s), "native label")


def canonical(value):
    def check(v):
        if type(v) is str:
            _require(all(32 <= ord(c) <= 126 and c not in '\\"' for c in v), "native ASCII")
        elif type(v) is int:
            uint(v)
        elif type(v) is bool:
            pass
        elif type(v) is list:
            for item in v:
                check(item)
        elif type(v) is dict:
            for k, item in v.items():
                _require(type(k) is str, "native field name")
                check(k)
                check(item)
        else:
            raise CodecError("native scheduling JSON type")

    check(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("ascii")


def decode(raw):
    _require(type(raw) is bytes, "original scheduling bytes")
    try:
        value = json.loads(raw.decode("ascii"), object_pairs_hook=_pairs)
    except (UnicodeError, ValueError, RecursionError) as e:
        raise CodecError("native scheduling JSON") from e
    _require(type(value) is dict and canonical(value) == raw, "exact canonical scheduling bytes")
    return value


def identifier(kind, raw):
    return "sha256:" + sha256(f"deltareduce.007.{kind}.v1".encode() + b"\0" + raw).hexdigest()


def envelope(kind, semantics):
    _id(semantics)
    return {"formal_semantics_id": semantics, "schema_version": "1.0.0", "type_name": kind}


def policy(raw, context, semantics):
    _require(0 < len(raw) <= 256 * 1024, "existing native contract byte bound")
    p = decode(raw)
    _require(set(p) == POLICY_FIELDS, "complete original policy fields")
    _require(
        all(p[k] == v for k, v in envelope("DOMAIN_TICKET_POLICY", semantics).items()),
        "policy generation",
    )
    _require(all(p[k] == context[k] for k in CONTEXT), "original scheduling context")
    _require(p["allocation_policy"] == "CONTIGUOUS_NO_OVERLAP", "native allocation")
    for key in ("dataset_manifest_id", "eligibility_policy_id", "mixture_coefficient_id"):
        _id(p[key])
    label(p["domain_id"])
    for key in ("batch_budget", "step_budget"):
        _require(0 < uint(p[key]) <= 2**31 - 1, "native fixed work")
    count = uint(p["ticket_count"])
    _require(0 < count <= 100000, "native ticket bound")
    lo, hi = uint(p["token_cursor_start"]), uint(p["token_cursor_end"])
    _require(lo < hi and hi - lo >= count and (hi - lo) % count == 0, "native exact partition")
    regions = p["region_ids"]
    _require(type(regions) is list and 0 < len(regions) <= 256, "native region bound")
    for region in regions:
        label(region)
    _require(regions == sorted(set(regions)), "native ordered region set")
    return p


@dataclass(frozen=True)
class Plan:
    original: bytes
    policies: tuple[bytes, ...]
    tickets: tuple[bytes, ...]
    semantics: str

    @property
    def id(self):
        return identifier("round-ticket-plan", self.original)

    @property
    def value(self):
        return decode(self.original)


def plan(
    policy_raws, context, assignment_policy, capability_root, decisions, lease_policy, semantics
):
    """Exact native plan construction; no supplied ticket list becomes authority."""
    _require(type(policy_raws) is tuple and 0 < len(policy_raws) <= 256, "native domain count")
    _id(assignment_policy)
    _id(capability_root)
    _require(
        set(lease_policy)
        == {
            "hard_deadline_tick",
            "lease_duration_ticks",
            "maximum_lease_epochs",
            "maximum_renewals",
        },
        "native lease policy",
    )
    for key, v in lease_policy.items():
        uint(v)
        _require(key == "maximum_renewals" or v > 0, "native positive lease bound")
    policies = sorted(
        (policy(raw, context, semantics) for raw in policy_raws), key=lambda p: p["domain_id"]
    )
    _require(len({p["domain_id"] for p in policies}) == len(policies), "duplicate domain")
    _require(sum(p["ticket_count"] for p in policies) <= 100000, "native total ticket bound")
    decisions = sorted(decisions)
    _require(
        bool(decisions) and len({d[0] for d in decisions}) == len(decisions),
        "native decision identities",
    )
    for worker, decision in decisions:
        label(worker)
        _id(decision)
    tickets = []
    for p in policies:
        width = (p["token_cursor_end"] - p["token_cursor_start"]) // p["ticket_count"]
        for ordinal in range(p["ticket_count"]):
            ticket = {k: p[k] for k in CONTEXT}
            ticket.update(envelope("SCHEDULING_WORK_TICKET", semantics))
            ticket.update(
                batch_budget=p["batch_budget"],
                domain_id=p["domain_id"],
                normalized_artifact_id="sha256:" + "0" * 64,
                policy_id=identifier("domain-ticket-policy", canonical(p)),
                step_budget=p["step_budget"],
                ticket_id=f"ticket-{p['domain_id']}-{ordinal:03d}",
                token_cursor_start=p["token_cursor_start"] + width * ordinal,
                token_cursor_end=p["token_cursor_start"] + width * (ordinal + 1),
            )
            label(ticket["ticket_id"])
            tickets.append(canonical(ticket))
    value = envelope("ROUND_TICKET_PLAN", semantics)
    value.update(
        assignment_policy_id=assignment_policy,
        capability_snapshot_root=capability_root,
        decisions=[{"worker_id": w, "decision_id": d} for w, d in decisions],
        lease_policy=lease_policy,
        parameter_schema_id=context["parameter_schema_id"],
        parent_checkpoint_id=context["parent_checkpoint_id"],
        round_config_id=context["round_config_id"],
        policies=[
            {
                "domain_id": p["domain_id"],
                "policy_id": identifier("domain-ticket-policy", canonical(p)),
            }
            for p in policies
        ],
        tickets=[
            {"ticket_id": decode(t)["ticket_id"], "ticket_content_id": identifier("work-ticket", t)}
            for t in tickets
        ],
    )
    return Plan(canonical(value), tuple(canonical(p) for p in policies), tuple(tickets), semantics)


def verify_plan(p):
    """A forged dataclass is not a producer witness; recompute the full output."""
    _require(type(p) is Plan and bool(p.policies), "original planner output required")
    value = p.value
    context = {k: decode(p.policies[0])[k] for k in CONTEXT}
    _require(
        p
        == plan(
            p.policies,
            context,
            value["assignment_policy_id"],
            value["capability_snapshot_root"],
            [(d["worker_id"], d["decision_id"]) for d in value["decisions"]],
            value["lease_policy"],
            p.semantics,
        ),
        "complete independently reconstructed plan",
    )


def evaluate_capability(raw, policy_fields, semantics):
    """Exact existing native eligibility calculation, not signature verification.

    The original feature007 policy uses trusted signature-ID membership. This
    function preserves that rule and does not call it Ed25519 authentication,
    measured performance, or bootstrap authority. The original policy input's
    provenance is required by the enclosing independently checked source.
    """
    _require(type(raw) is bytes and 0 < len(raw) <= 256 * 1024, "native capability byte bound")
    p, policy_fields = decode(raw), dict(policy_fields)
    numbers = {
        "complete_ticket_throughput_milli",
        "expires_at_tick",
        "identity_epoch",
        "max_concurrent_leases",
        "measured_at_tick",
        "memory_bytes",
        "sample_count",
    }
    texts = {
        "arithmetic_profile_id",
        "measurement_artifact_id",
        "model_mode",
        "parameter_schema_id",
        "region_id",
        "round_config_id",
        "signature_id",
        "software_build_id",
        "worker_id",
    }
    _require(
        set(p) == COMMON | numbers | texts
        and all(p[k] == v for k, v in envelope("CAPABILITY_PROFILE", semantics).items()),
        "native capability field set/generation",
    )
    for k in numbers:
        uint(p[k])
    _require(all(type(p[k]) is str for k in texts), "native capability string fields")
    _require(
        set(policy_fields)
        == {
            "allowed_domain_ids",
            "allowed_region_ids",
            "allowed_software_build_ids",
            "arithmetic_profile_id",
            "decision_tick",
            "eligibility_policy_id",
            "identity_epoch",
            "minimum_memory_bytes",
            "minimum_sample_count",
            "model_mode",
            "parameter_schema_id",
            "round_config_id",
            "trusted_signature_ids",
        },
        "existing eligibility policy fields",
    )
    for k in (
        "arithmetic_profile_id",
        "eligibility_policy_id",
        "parameter_schema_id",
        "round_config_id",
    ):
        _id(policy_fields[k])
    for k in ("decision_tick", "identity_epoch", "minimum_memory_bytes", "minimum_sample_count"):
        uint(policy_fields[k])
    for k in (
        "allowed_domain_ids",
        "allowed_region_ids",
        "allowed_software_build_ids",
        "trusted_signature_ids",
    ):
        values = policy_fields[k]
        _require(
            type(values) is list and values == sorted(set(values)), "native ordered policy set"
        )
        for value in values:
            (label if k in {"allowed_domain_ids", "allowed_region_ids"} else _id)(value)
    tests = {
        "ARITHMETIC_PROFILE_MISMATCH": p["arithmetic_profile_id"]
        != policy_fields["arithmetic_profile_id"],
        "PROFILE_EXPIRED": p["expires_at_tick"] < policy_fields["decision_tick"],
        "IDENTITY_EPOCH_MISMATCH": p["identity_epoch"] != policy_fields["identity_epoch"],
        "MEASUREMENT_FROM_FUTURE": p["measured_at_tick"] > policy_fields["decision_tick"],
        "MEMORY_INSUFFICIENT": p["memory_bytes"] < policy_fields["minimum_memory_bytes"],
        "MODEL_MODE_MISMATCH": p["model_mode"] != policy_fields["model_mode"],
        "PARAMETER_SCHEMA_MISMATCH": p["parameter_schema_id"]
        != policy_fields["parameter_schema_id"],
        "REGION_NOT_ALLOWED": p["region_id"] not in policy_fields["allowed_region_ids"],
        "ROUND_CONFIG_MISMATCH": p["round_config_id"] != policy_fields["round_config_id"],
        "MEASUREMENT_SAMPLE_INSUFFICIENT": p["sample_count"]
        < policy_fields["minimum_sample_count"],
        "SIGNATURE_NOT_TRUSTED": p["signature_id"] not in policy_fields["trusted_signature_ids"],
        "SOFTWARE_BUILD_NOT_ALLOWED": p["software_build_id"]
        not in policy_fields["allowed_software_build_ids"],
        "THROUGHPUT_EVIDENCE_MISSING": p["complete_ticket_throughput_milli"] == 0,
        "CONCURRENCY_LIMIT_INVALID": not 0 < p["max_concurrent_leases"] <= 1024,
        "MEASUREMENT_ARTIFACT_INVALID": re.fullmatch(
            r"sha256:[0-9a-f]{64}", p["measurement_artifact_id"]
        )
        is None,
        "WORKER_ID_INVALID": re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", p["worker_id"]) is None,
    }
    reasons = sorted(k for k, invalid in tests.items() if invalid)
    eligible = not reasons
    value = envelope("ELIGIBILITY_DECISION", semantics)
    value.update(
        allowed_domain_ids=policy_fields["allowed_domain_ids"] if eligible else [],
        capability_profile_id=identifier("capability-profile", raw),
        decision_tick=policy_fields["decision_tick"],
        eligibility_policy_id=policy_fields["eligibility_policy_id"],
        eligible=eligible,
        max_concurrent_leases=p["max_concurrent_leases"] if eligible else 0,
        reason_codes=reasons or ["ELIGIBLE"],
        region_route=p["region_id"],
        round_config_id=policy_fields["round_config_id"],
        worker_id=p["worker_id"],
    )
    return canonical(value)


def allocate(p, workers, issue_tick):
    """Existing greedy initial allocation; workers contain original decision + rate.

    The caller must bind each decision to its original evaluate_capability result;
    this function does not pretend that measurement IDs prove performance.
    """
    verify_plan(p)
    expiry = uint(uint(issue_tick) + p.value["lease_policy"]["lease_duration_ticks"])
    _require(expiry <= p.value["lease_policy"]["hard_deadline_tick"], "initial hard deadline")
    available = sorted(
        ((d, rate) for d, rate in workers if d["eligible"]),
        key=lambda x: (-x[1], x[0]["worker_id"]),
    )
    # The native implementation tests adjacent duplicates after throughput sort.
    # Preserve that exact rule, rather than silently strengthening its domain.
    _require(
        all(a[0]["worker_id"] != b[0]["worker_id"] for a, b in pairwise(available)),
        "adjacent duplicate native worker",
    )
    for d, rate in available:
        label(d["worker_id"])
        label(d["region_route"])
        _require(
            d["round_config_id"] == p.value["round_config_id"]
            and uint(d["max_concurrent_leases"]) > 0
            and uint(rate) > 0,
            "original worker allocation input",
        )
        _require(
            d["allowed_domain_ids"] == sorted(set(d["allowed_domain_ids"])),
            "native domain ordering",
        )
    remaining = [d["max_concurrent_leases"] for d, _ in available]
    leases = []
    for raw in p.tickets:
        t = decode(raw)
        choice = next(
            (
                i
                for i, (d, _) in enumerate(available)
                if remaining[i] and t["domain_id"] in d["allowed_domain_ids"]
            ),
            None,
        )
        if choice is None:
            return None  # Native infeasibility: no partial lease publication.
        remaining[choice] -= 1
        d = available[choice][0]
        value = envelope("TICKET_LEASE", p.semantics)
        value.update(
            expiry_tick=expiry,
            issue_tick=issue_tick,
            lease_epoch=0,
            plan_id=p.id,
            prior_lease_id="NONE",
            region_route=d["region_route"],
            renewal_count=0,
            round_config_id=p.value["round_config_id"],
            state="ACTIVE",
            ticket_content_id=identifier("work-ticket", raw),
            ticket_id=t["ticket_id"],
            worker_id=d["worker_id"],
        )
        leases.append(canonical(value))
    return tuple(leases)


@dataclass(frozen=True)
class LeaseState:
    plan: Plan
    initial: tuple[bytes, ...]
    leases: tuple[bytes, ...]
    commitments: tuple[tuple[str, str], ...] = ()
    requests: tuple[tuple[str, int], ...] = ()
    frames: tuple[bytes, ...] = ()


def lease_id(raw):
    return identifier("ticket-lease", raw)


def frame(sequence, kind, request, lease, commitment=""):
    """Unchanged DSJ1 storage identity; distinct from the DRW1 vote journal."""
    v = decode(lease)
    _require(set(v) == LEASE_FIELDS and kind in (1, 2), "original DSJ1 fields")

    def string(s):
        raw = s.encode("ascii")
        _require(len(raw) <= 65535, "DSJ1 u16 string")
        return len(raw).to_bytes(2, "big") + raw

    body = uint(sequence).to_bytes(8, "big") + bytes([kind]) + string(request)
    for key in (
        "ticket_id",
        "worker_id",
        "region_route",
        "plan_id",
        "prior_lease_id",
        "round_config_id",
        "state",
        "ticket_content_id",
    ):
        body += string(v[key])
    for key in ("lease_epoch", "issue_tick", "expiry_tick", "renewal_count"):
        body += uint(v[key]).to_bytes(8, "big")
    body += string(commitment)
    prefix = b"DSJ1" + (8 + len(body) + 64).to_bytes(4, "big") + body
    return prefix + sha256(prefix).hexdigest().encode("ascii")


def current(state, ticket):
    raw = next((v for v in state.leases if decode(v)["ticket_id"] == ticket), None)
    _require(raw is not None, "native unknown ticket")
    return raw


def _append(state, request, lease, commitment=""):
    # The pure result represents only the committed durable-prefix boundary.
    # It is not an assertion that any filesystem append/barrier was performed.
    _require(request not in dict(state.requests), "native duplicate journal request")
    seq = len(state.frames) + 1
    v = decode(lease)
    leases = {decode(raw)["ticket_id"]: raw for raw in state.leases}
    commits = dict(state.commitments)
    if commitment:
        _id(commitment)
        _require(v["ticket_id"] not in commits, "native commitment equivocation")
        commits[v["ticket_id"]] = commitment
    else:
        leases[v["ticket_id"]] = lease
    return replace(
        state,
        leases=tuple(leases[k] for k in sorted(leases)),
        commitments=tuple(sorted(commits.items())),
        requests=(*state.requests, (request, seq)),
        frames=(*state.frames, frame(seq, 2 if commitment else 1, request, lease, commitment)),
    )


def initialize(p, leases):
    """Original native constructor, after plan/allocation provenance was joined."""
    verify_plan(p)
    _require(len(leases) == len(p.tickets), "native full initial lease set")
    for raw, ticket in zip(leases, p.tickets, strict=True):
        v, t = decode(raw), decode(ticket)
        _require(
            set(v) == LEASE_FIELDS
            and all(v[k] == x for k, x in envelope("TICKET_LEASE", p.semantics).items()),
            "original lease encoding",
        )
        _require(
            v["ticket_id"] == t["ticket_id"]
            and v["ticket_content_id"] == identifier("work-ticket", ticket)
            and v["plan_id"] == p.id
            and v["lease_epoch"] == 0
            and v["renewal_count"] == 0
            and v["state"] == "ACTIVE",
            "native initial lease/immutable plan",
        )
    state = LeaseState(p, leases, ())
    for raw in sorted(leases, key=lambda x: decode(x)["ticket_id"]):
        state = _append(state, "init:" + lease_id(raw), raw)
    return state


def timer(state, ticket):
    raw = current(state, ticket)
    v = decode(raw)
    _require(v["state"] == "ACTIVE", "native active timer")
    result = envelope("LEASE_TIMER_TOKEN", state.plan.semantics)
    result.update(
        effect_kind="LEASE_EXPIRY",
        expiry_tick=v["expiry_tick"],
        lease_epoch=v["lease_epoch"],
        lease_id=lease_id(raw),
        plan_id=v["plan_id"],
        round_config_id=v["round_config_id"],
        ticket_id=ticket,
        token_nonce="sha256:" + sha256(lease_id(raw).encode()).hexdigest(),
        worker_id=v["worker_id"],
    )
    return canonical(result)


@dataclass(frozen=True)
class Transition:
    state: LeaseState
    disposition: str
    receipt_sequence: int


def invoke(
    state,
    kind,
    ticket,
    *,
    tick,
    worker=None,
    epoch=None,
    renewal=None,
    prior=None,
    region=None,
    commitment=None,
    token=None,
):
    """Existing producer call, with fields bound by the enclosing original event.

    Replays return the original receipt slot even after later transitions. They
    never create a second record or erase any source-command occurrence.
    """
    uint(tick)
    lp = state.plan.value["lease_policy"]
    if kind == "renew":
        uint(epoch)
        uint(renewal)
        request = f"renew:{ticket}:{worker}:{epoch}:{renewal}:{tick}"
    elif kind == "reassign":
        request = f"reassign:{ticket}:{prior}:{worker}:{region}:{tick}"
    elif kind == "commit":
        _id(commitment)
        uint(epoch)
        request = f"commit:{ticket}:{commitment}"
    elif kind == "expire":
        t = decode(token)
        _require(
            set(t)
            == COMMON
            | {
                "effect_kind",
                "expiry_tick",
                "lease_epoch",
                "lease_id",
                "plan_id",
                "round_config_id",
                "ticket_id",
                "token_nonce",
                "worker_id",
            }
            and all(
                t[k] == x for k, x in envelope("LEASE_TIMER_TOKEN", state.plan.semantics).items()
            ),
            "native original timer type",
        )
        uint(t["expiry_tick"])
        uint(t["lease_epoch"])
        ticket = t["ticket_id"]
        request = "expire:" + identifier("lease-timer-token", token)
    else:
        raise CodecError("not an original lease producer call")
    previous = dict(state.requests).get(request)
    if previous is not None:
        return Transition(state, "replay", previous)
    raw = current(state, ticket)
    v = decode(raw)
    committed = ticket in dict(state.commitments)
    if kind == "expire":
        if committed:
            return Transition(state, "committed_noop", len(state.frames))
        if token != timer(state, ticket):
            return Transition(state, "stale_noop", len(state.frames))
        if tick < v["expiry_tick"]:
            return Transition(state, "early_noop", len(state.frames))
        v["state"] = "EXPIRED"
    elif kind == "renew":
        _require(
            not committed
            and v["state"] == "ACTIVE"
            and v["worker_id"] == worker
            and v["lease_epoch"] == epoch
            and v["renewal_count"] == renewal,
            "native renewal current lease",
        )
        _require(
            tick <= v["expiry_tick"] and renewal < lp["maximum_renewals"], "native renewal guard"
        )
        v["expiry_tick"] = uint(v["expiry_tick"] + lp["lease_duration_ticks"])
        v["renewal_count"] += 1
        _require(v["expiry_tick"] <= lp["hard_deadline_tick"], "native renewal deadline")
    elif kind == "reassign":
        _require(
            not committed and v["state"] == "EXPIRED" and lease_id(raw) == prior,
            "native finalized expired predecessor",
        )
        label(worker)
        label(region)
        _require(
            (v["lease_epoch"] + 1) % (U64 + 1) < lp["maximum_lease_epochs"], "native epoch guard"
        )
        expiry = uint(tick + lp["lease_duration_ticks"])
        _require(expiry <= lp["hard_deadline_tick"], "native reassign deadline")
        v.update(
            expiry_tick=expiry,
            issue_tick=tick,
            lease_epoch=(v["lease_epoch"] + 1) % (U64 + 1),
            prior_lease_id=lease_id(raw),
            region_route=region,
            renewal_count=0,
            state="ACTIVE",
            worker_id=worker,
        )
    else:
        _require(
            not committed
            and v["state"] == "ACTIVE"
            and v["worker_id"] == worker
            and v["lease_epoch"] == epoch,
            "native commit current lease",
        )
        _require(
            tick <= v["expiry_tick"] and tick <= lp["hard_deadline_tick"], "native commit deadline"
        )
        after = _append(state, request, raw, commitment)
        return Transition(after, "applied", len(after.frames))
    after = _append(state, request, canonical(v))
    return Transition(after, "applied", len(after.frames))


def public_lease_fields(state):
    """Static ticket fields; native ACTIVE+committed is public inactive.

    Original DSJ1 bytes and current lease remain on state; this is not a claim
    that each native reassignment matches the old TLA ReassignTicket action.
    """
    committed = dict(state.commitments)
    rows = [decode(raw) for raw in state.leases]
    return {
        "leaseOwner": {v["ticket_id"]: v["worker_id"] for v in rows},
        "leaseEpoch": {v["ticket_id"]: v["lease_epoch"] for v in rows},
        "leaseActive": tuple(
            v["ticket_id"]
            for v in rows
            if v["state"] == "ACTIVE" and v["ticket_id"] not in committed
        ),
        "commitments": tuple(
            (v["ticket_id"], v["worker_id"], v["lease_epoch"], committed[v["ticket_id"]])
            for v in rows
            if v["ticket_id"] in committed
        ),
    }
