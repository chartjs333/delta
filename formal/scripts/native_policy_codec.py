"""Complete pinned DVPOL001 wire grammar; structural decoding is not admission."""

from itertools import pairwise

from native_admission_snapshot import require

HEADER = b"DVPOL001\x00\x01\x00\x00\x00\x00\x00\x00"
MAX_BYTES, MAX_TEXT, MAX_ENTRIES = 4 * 1024 * 1024, 4096, 100000
REASONS = (
    "HARD_DEADLINE",
    "INCOMPLETE_INPUT",
    "UNSAFE_COEFFICIENTS",
    "IRRECOVERABLE_AVAILABILITY",
    "PARAMETER_FAILURE",
    "APPLY_FAILURE",
)
SCHEMAS = {}


def record(name, fields):
    """Explicit native append/read order. Unqualified fields are ASCII text."""
    result = tuple(
        (s.split(":")[0], s.split(":")[1] if ":" in s else "text") for s in fields.split()
    )
    require(len(dict(result)) == len(result), "duplicate schema field")
    SCHEMAS[name] = result
    return name


record(
    "context",
    (
        "arithmetic_profile_id height:u64 parameter_schema_id round_c"
        "onfig_id round_id validator_epoch_id view:u64"
    ),
)
record("rational", "numerator:i64 denominator:u64")
record("tuple", "availability_certificate_id commitment_id domain_id ticket_id")
record("input_set_body", "context:context input_root tuples:tuple[]")
record(
    "input_set", "context:context input_root quorum_threshold:u32 signer_ids:text[] tuples:tuple[]"
)
record("seed", "context:context input_set_certificate_id seed_id seed_profile_id share_ids:text[]")
record("norm_entry", "scale_denominator:u64 squared_norm ticket_id")
record("norm", "context:context entries:norm_entry[] input_set_certificate_id norm_root")
record("eligibility_entry", "accepted:bool domain_id gamma:rational reason_code ticket_id")
record(
    "eligibility",
    (
        "context:context entries:eligibility_entry[] input_set_certif"
        "icate_id norm_evidence_id quorum_threshold:u32 robust_profil"
        "e_id signer_ids:text[]"
    ),
)
record(
    "eligibility_body",
    (
        "context:context entries:eligibility_entry[] input_set_certif"
        "icate_id norm_evidence_id robust_profile_id seed_transcript_"
        "id"
    ),
)
record("finalized_eligibility", "certificate:eligibility seed_transcript_id")
record("bucket", "bucket_id ticket_id")
record("weight", "alpha:rational ticket_id")
record(
    "plan",
    (
        "context:context accumulator_proof_id bucket_assignments:buck"
        "et[] eligibility_certificate_id input_set_certificate_id ite"
        "ration_count:u32 quorum_threshold:u32 seed_transcript_id sig"
        "ner_ids:text[] transcript_root weights:weight[]"
    ),
)
record(
    "plan_body",
    (
        "context:context accumulator_proof_id bucket_assignments:buck"
        "et[] eligibility_certificate_id input_set_certificate_id ite"
        "ration_count:u32 seed_transcript_id transcript_root weights:"
        "weight[]"
    ),
)
record("shard_key", "domain_id shard_id")
record(
    "parameter",
    (
        "context:context aggregation_plan_certificate_id denominator:"
        "u64 domain_id eligibility_certificate_id input_leaf_ids:text"
        "[] input_set_certificate_id quorum_threshold:u32 result_nume"
        "rators:text[] shard_id signer_ids:text[]"
    ),
)
record(
    "parameter_body",
    (
        "context:context aggregation_plan_certificate_id denominator:"
        "u64 domain_id eligibility_certificate_id input_leaf_ids:text"
        "[] input_set_certificate_id result_numerators:text[] shard_i"
        "d vote_context_id"
    ),
)
record("root_leaf", "domain_id parameter_shard_qc_id shard_id")
record(
    "root",
    (
        "context:context aggregation_plan_certificate_id eligibility_"
        "certificate_id input_set_certificate_id leaves:root_leaf[] m"
        "erkle_root quorum_threshold:u32 required_keys:shard_key[] si"
        "gner_ids:text[]"
    ),
)
record(
    "root_body",
    (
        "context:context aggregation_plan_certificate_id eligibility_"
        "certificate_id input_set_certificate_id leaves:root_leaf[] m"
        "erkle_root required_keys:shard_key[]"
    ),
)
record("domain_weight", "domain_id pi:rational")
record(
    "apply_profile",
    (
        "accumulator_proof_id domain_weights:domain_weight[] learning"
        "_rate:rational momentum:rational nesterov:bool rounding weig"
        "ht_decay:rational"
    ),
)
record(
    "apply_candidate",
    (
        "context:context aggregate_root_qc_id apply_arithmetic_profil"
        "e_id next_model_hash next_model_values:text[] next_optimizer"
        "_hash next_optimizer_values:text[] parent_checkpoint_id pare"
        "nt_optimizer_hash"
    ),
)
record(
    "apply_qc",
    (
        "context:context aggregate_root_qc_id apply_arithmetic_profil"
        "e_id apply_candidate_id next_model_hash next_optimizer_hash "
        "parent_checkpoint_id quorum_threshold:u32 signer_ids:text[]"
    ),
)
record("finalized_apply", "certificate:apply_qc candidate:apply_candidate")
record("timeout", "round_id height:u64 view:u64")
record("view_change", "round_id height:u64 from_view:u64 to_view:u64 soft_deadline_tick:u64")
record("abort_request", "round_id reason_code")
record(
    "abort_body",
    (
        "round_id validator_epoch_id height:u64 view:u64 hard_deadlin"
        "e_tick:u64 parent_checkpoint_id reason_code round_config_ids"
        ":text[] input_set_ids:text[] eligibility_ids:text[] aggregat"
        "ion_plan_ids:text[] parameter_ids:text[] aggregate_root_ids:"
        "text[] apply_ids:text[]"
    ),
)
record(
    "parents",
    (
        "round_config_id parent_checkpoint_id input_set_certificate_i"
        "d seed_transcript_id norm_evidence_id eligibility_certificat"
        "e_id aggregation_plan_certificate_id parameter_matrix_root a"
        "ggregate_root_certificate_id apply_profile_id apply_candidat"
        "e_id last_finalized_certificate_id domain_id shard_id reason"
        "_code"
    ),
)
record("candidate", "action:u32 body_hash context_id height:u64 view:u64 parents:parents")
record(
    "snapshot",
    (
        "state_id parameter_schema_id arithmetic_profile_id required_"
        "accumulator_proof_id proposed_round_config_ids:text[] finali"
        "zed_round_config_ids:text[] closed_input_set_ids:text[] inpu"
        "t_set_bodies:input_set_body[] input_set_certificates:input_s"
        "et[] finalized_input_set_ids:text[] seed_transcripts:seed[] "
        "norm_evidence:norm[] eligibility_bodies:eligibility_body[] e"
        "ligibility_certificates:finalized_eligibility[] finalized_el"
        "igibility_ids:text[] aggregation_plan_bodies:plan_body[] agg"
        "regation_plan_certificates:plan[] finalized_aggregation_plan"
        "_ids:text[] parameter_bodies:parameter_body[] parameter_qcs:"
        "parameter[] finalized_parameter_ids:text[] required_paramete"
        "r_keys:shard_key[] aggregate_root_bodies:root_body[] aggrega"
        "te_root_qcs:root[] finalized_aggregate_root_ids:text[] apply"
        "_profiles:apply_profile[] apply_candidates:apply_candidate[]"
        " apply_qcs:finalized_apply[] finalized_apply_ids:text[] time"
        "out_observations:timeout[] view_change_bodies:view_change[] "
        "abort_requests:abort_request[] abort_bodies:abort_body[]"
    ),
)
record(
    "policy",
    (
        "local_validator_id validator_epoch_id validator_ids:validato"
        "rs role:u32 round_id round_config_id configured_abort_reason"
        " initial_logical_tick:u64 soft_deadline_tick:u64 hard_deadli"
        "ne_tick:u64 snapshot:snapshot candidates:candidates"
    ),
)


def vector_shape(shape):
    if shape == "validators":
        return "text", 4096
    if shape == "candidates":
        return "candidate", 8192
    return (shape[:-2], MAX_ENTRIES) if shape.endswith("[]") else None


class Reader:
    def __init__(self, raw):
        require(type(raw) is bytes and len(raw) <= MAX_BYTES, "policy byte bound")
        self.raw, self.at = raw, 0

    def take(self, n):
        require(0 <= n <= len(self.raw) - self.at, "policy truncated")
        result = self.raw[self.at : self.at + n]
        self.at += n
        return result

    def uint(self, n):
        return int.from_bytes(self.take(n), "big")

    def value(self, shape):
        if shape in {"u32", "u64", "i64"}:
            n = self.uint(4 if shape == "u32" else 8)
            return n - 2**64 if shape == "i64" and n >= 2**63 else n
        if shape == "bool":
            n = self.uint(1)
            require(n <= 1, "policy bool")
            return bool(n)
        if shape == "text":
            n = self.uint(4)
            require(n <= MAX_TEXT, "policy text bound")
            raw = self.take(n)
            require(all(32 <= b <= 126 for b in raw), "policy ASCII")
            return raw.decode("ascii")
        vector = vector_shape(shape)
        if vector:
            item, bound = vector
            n = self.uint(4)
            require(n <= bound, "policy vector bound")
            if shape in {"validators", "candidates"}:
                require(n > 0, "policy nonempty")
                require(
                    n * (4 if shape == "validators" else 88) <= len(self.raw) - self.at,
                    "policy aggregate truncation",
                )
            return [self.value(item) for _ in range(n)]
        return {name: self.value(kind) for name, kind in SCHEMAS[shape]}


def encode_value(shape, value):
    if shape in {"u32", "u64", "i64"}:
        bits = 32 if shape == "u32" else 64
        low, high = (-(2**63), 2**63) if shape == "i64" else (0, 2**bits)
        require(type(value) is int and low <= value < high, "policy integer")
        return (value % (2**bits)).to_bytes(bits // 8, "big")
    if shape == "bool":
        require(type(value) is bool, "policy bool type")
        return bytes([int(value)])
    if shape == "text":
        require(type(value) is str and len(value) <= MAX_TEXT, "policy text")
        require(all(32 <= ord(c) <= 126 for c in value), "policy ASCII")
        return len(value).to_bytes(4, "big") + value.encode("ascii")
    vector = vector_shape(shape)
    if vector:
        item, bound = vector
        require(type(value) is list and len(value) <= bound, "policy vector")
        return len(value).to_bytes(4, "big") + b"".join(encode_value(item, x) for x in value)
    require(type(value) is dict and set(value) == {k for k, _ in SCHEMAS[shape]}, "policy fields")
    return b"".join(encode_value(kind, value[name]) for name, kind in SCHEMAS[shape])


def canonical_shape(p):
    vs, cs = p["validator_ids"], p["candidates"]
    require(0 < len(vs) <= 4096 and vs == sorted(set(vs)), "policy validators")
    require(p["role"] == 1 and p["configured_abort_reason"] in REASONS, "policy role/reason")
    require(0 < len(cs) <= 8192, "policy candidates")
    require(all(1 <= c["action"] <= 9 for c in cs), "policy action")
    keys = [(c["height"], c["view"], c["action"], c["context_id"]) for c in cs]
    require(all(a < b for a, b in pairwise(keys)), "policy candidate order")
    require(len({c["context_id"] for c in cs}) == len(cs), "policy duplicate context")


def encode(p):
    canonical_shape(p)
    raw = HEADER + encode_value("policy", p)
    require(len(raw) <= MAX_BYTES, "policy byte bound")
    return raw


def decode(raw):
    reader = Reader(raw)
    require(reader.take(16) == HEADER, "policy header")
    value = reader.value("policy")
    require(reader.at == len(raw), "policy trailing")
    canonical_shape(value)
    require(encode(value) == raw, "policy canonical bytes")
    return value
