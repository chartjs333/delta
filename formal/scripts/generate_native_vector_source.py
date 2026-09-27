"""Separate synthetic raw source; original004 artifact preimages stay unchanged.

This is a proposal test fixture, not a native export or a reachable native state.
The policy/state container, certificates and primitive observations are synthetic.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path

import native_policy_codec as codec
from formal_artifacts import canonical_json_bytes, write_canonical_json
from generate_native_available_q import fixture, joined_fixture
from generate_native_plan_source import MODULES
from generate_native_plan_source import source as original_source
from generate_native_policy_schema import format_of, lean_value
from generate_native_state_vectors import envelope
from generate_native_wal_lean import lit
from native_admission_snapshot import decode_flat, state_id
from native_certificate_chain import DOMAINS as CERT_DOMAINS
from native_certificate_chain import content_id
from native_source_artifacts import DOMAINS, resolve_q_source

ROOT = Path(__file__).resolve().parents[2]
VERSION = "deltareduce.synthetic-raw-vector-source.v1"


def tree_of(kind, value):
    """Exact native wire field order, from the separately constructed documents."""
    if kind in codec.SCHEMAS:
        return {
            k: tree_of(t, value if k == "context" else value[k]) for k, t in codec.SCHEMAS[kind]
        }
    if vec := codec.vector_shape(kind):
        return [tree_of(vec[0], v) for v in value]
    return int(value) if kind in {"i64", "u64", "u32"} else value


def source():
    store, apc, edges, observations, docs, obs = joined_fixture()
    _, golden, _ = fixture()
    original, _, state, _ = original_source()
    policy = copy.deepcopy(original)
    state = copy.deepcopy(state)
    manifest = golden["manifest"]["value"]
    config = golden["fixedpoint_config"]["value"]
    trees = {
        n: tree_of(k, docs[n])
        for n, k in [
            ("ISC", "input_set"),
            ("NORM", "norm"),
            ("SEED", "seed"),
            ("EC", "eligibility"),
            ("APC", "plan"),
        ]
    }
    state["config_id"] = config["base_round_config_id"]
    state["parent_checkpoint_id"] = manifest["parent_checkpoint_id"]
    # This is an explicit opaque synthetic inner-root symbol, not a computed native state root.
    state["state_root"] = (
        "sha256:" + hashlib.sha256((VERSION + ":inner-root-symbol").encode()).hexdigest()
    )
    raw = envelope(5, sorted(state.items()))
    assert decode_flat(raw, 5) == state
    policy["round_config_id"] = state["config_id"]
    candidate = policy["candidates"][0]
    candidate["context_id"] = "STRUCTURAL-ONLY:synthetic-vector-source"
    candidate["body_hash"] = (
        "sha256:" + hashlib.sha256((VERSION + ":candidate-not-admitted").encode()).hexdigest()
    )
    candidate["parents"] = {k: "" for k in candidate["parents"]}
    snap = policy["snapshot"]
    for key, typ in codec.SCHEMAS["snapshot"]:
        if codec.vector_shape(typ):
            snap[key] = []
    snap.update(
        state_id=state_id(raw),
        parameter_schema_id=manifest["parameter_schema_id"],
        arithmetic_profile_id=docs["APC"]["arithmetic_profile_id"],
        required_accumulator_proof_id=manifest["proof_instance_id"],
        input_set_certificates=[trees["ISC"]],
        finalized_input_set_ids=[content_id(docs["ISC"])],
        seed_transcripts=[trees["SEED"]],
        norm_evidence=[trees["NORM"]],
        eligibility_certificates=[
            {"certificate": trees["EC"], "seed_transcript_id": content_id(docs["SEED"])}
        ],
        finalized_eligibility_ids=[content_id(docs["EC"])],
        aggregation_plan_certificates=[trees["APC"]],
        finalized_aggregation_plan_ids=[apc],
    )
    policy_raw = codec.encode(policy)
    assert codec.decode(policy_raw) == policy
    assert docs["APC"]["accumulator_proof_id"] == golden["proof_instance"]["content_id"]
    return policy, policy_raw, state, raw, trees, docs, store, golden, obs, edges, observations


def asc(x):
    return lit(x.encode("ascii"))


def seq(xs):
    return "[" + ",".join(xs) + "]"


def tup(*xs):
    return "⟨" + ",".join(map(str, xs)) + "⟩"


def generate():
    p, policy_raw, state, raw, trees, docs, store, golden, _obs, edges, observations = source()
    out = [
        "import DeltaReduce.NativeSourceRefusal",
        "import DeltaReduce.NativePlanSourceVectors",
        "import DeltaReduce.NativeAvailableQVectors",
        "",
        "/-! Separately versioned SYNTHETIC raw policy/state/certificates.",
        "Original004 Q preimages are unchanged; finite SHA is not authentication. -/",
        "namespace DeltaReduce.NativeVectorSourceVectors",
        "open NativeReceiptBytes NativePolicyCodec NativePolicySchema",
        "open NativeConfigAdmission (encodedField encodedCons encodedVector)",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 60000",
    ]
    ctx = trees["ISC"]["context"]
    out += [
        "def context : NativeInputSetBody.Context := "
        + tup(
            *[
                str(ctx[k]) if k in ["height", "view"] else asc(ctx[k])
                for k, _ in codec.SCHEMAS["context"]
            ]
        ),
        "def committee : List Bytes := " + seq(map(asc, p["validator_ids"])),
    ]
    i, n, s, e, a = [docs[k] for k in ["ISC", "NORM", "SEED", "EC", "APC"]]
    out += [
        "def iscBody : NativeInputSetBody.Body := "
        + tup(
            "context",
            asc(i["input_root"]),
            seq(tup(*[asc(t[k]) for k, _ in codec.SCHEMAS["tuple"]]) for t in i["tuples"]),
        ),
        "def isc : NativeIscCertificate.Certificate := "
        + tup("iscBody", i["quorum_threshold"], seq(map(asc, i["signer_ids"]))),
        "def norm : NativeNormEvidence.Evidence := "
        + tup(
            "context",
            seq(
                tup(t["scale_denominator"], asc(t["squared_norm"]), asc(t["ticket_id"]))
                for t in n["entries"]
            ),
            asc(n["input_set_certificate_id"]),
            asc(n["norm_root"]),
        ),
        "def seed : NativeSeedTranscript.Transcript := "
        + tup(
            "context",
            asc(s["input_set_certificate_id"]),
            asc(s["seed_id"]),
            asc(s["seed_profile_id"]),
            seq(map(asc, s["share_ids"])),
        ),
        "def ec : NativeEligibility.Certificate := "
        + tup(
            tup(
                "context",
                seq(
                    tup(
                        int(t["accepted"]),
                        asc(t["domain_id"]),
                        t["gamma"]["numerator"],
                        t["gamma"]["denominator"],
                        asc(t["reason_code"]),
                        asc(t["ticket_id"]),
                    )
                    for t in e["entries"]
                ),
                asc(e["input_set_certificate_id"]),
                asc(e["norm_evidence_id"]),
                asc(e["robust_profile_id"]),
            ),
            e["quorum_threshold"],
            seq(map(asc, e["signer_ids"])),
        ),
        "def apc : NativePlan.Certificate := "
        + tup(
            tup(
                "context",
                asc(a["accumulator_proof_id"]),
                seq(tup(asc(t["bucket_id"]), asc(t["ticket_id"])) for t in a["bucket_assignments"]),
                asc(a["eligibility_certificate_id"]),
                asc(a["input_set_certificate_id"]),
                a["iteration_count"],
                asc(a["seed_transcript_id"]),
                asc(a["transcript_root"]),
                seq(
                    tup(t["alpha"]["numerator"], t["alpha"]["denominator"], asc(t["ticket_id"]))
                    for t in a["weights"]
                ),
            ),
            a["quorum_threshold"],
            seq(map(asc, a["signer_ids"])),
        ),
    ]
    for name, kind, mod in [
        ("isc", "input_set", "NativeIscCertificate"),
        ("norm", "norm", "NativeNormEvidence"),
        ("seed", "seed", "NativeSeedTranscript"),
        ("ec", "eligibility", "NativeEligibility"),
        ("apc", "plan", "NativePlan"),
    ]:
        out += [
            f"def {name}Tree : Value := " + lean_value(kind, trees[name.upper()]),
            f"theorem {name}Parsed : {mod}.read {name}Tree = some {name} := by rfl",
            f"theorem {name}Valid : {mod}.Valid context "
            + ("committee " if name in ["isc", "ec", "apc"] else "")
            + f"{name} := by decide",
            f"def {name}Id : Bytes := " + asc(content_id(docs[name.upper()])),
            f"def {name}JSON : Bytes := " + lit(canonical_json_bytes(docs[name.upper()])),
            f"theorem {name}JSONExact : {mod}.json {name} = {name}JSON := by rfl",
        ]
    out += [
        "def ecFinalTree : Value := "
        + lean_value("finalized_eligibility", p["snapshot"]["eligibility_certificates"][0]),
        "def tree : Value := " + lean_value("policy", p),
        "def snapshot : Value := " + lean_value("snapshot", p["snapshot"]),
        "def candidate : NativePolicyBytes.Candidate := "
        + tup(
            p["candidates"][0]["action"],
            asc(p["candidates"][0]["body_hash"]),
            asc(p["candidates"][0]["context_id"]),
            1,
            0,
            lean_value("parents", p["candidates"][0]["parents"]),
            lean_value("candidate", p["candidates"][0]),
        ),
        "def policy : NativePolicyBytes.Policy := "
        + tup(
            asc(p["local_validator_id"]),
            asc(p["validator_epoch_id"]),
            "committee",
            p["role"],
            asc(p["round_id"]),
            asc(p["round_config_id"]),
            asc(p["configured_abort_reason"]),
            p["initial_logical_tick"],
            p["soft_deadline_tick"],
            p["hard_deadline_tick"],
            "snapshot",
            "[candidate]",
            "tree",
        ),
        "theorem extracted : NativePolicyBytes.extract tree = some policy := by rfl",
    ]
    reuse = {}
    for module in [*MODULES, "NativePlanSourceVectors"]:
        text = (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").read_text("utf-8")
        for name, expr in re.findall(
            r"^theorem (encoding\d+) : (?:NativePolicyCodec\.)?encode (.*?) = some", text, re.M
        ):
            reuse[expr] = module + "." + name
    cache = {}

    def encode(kind, value):
        expr = f"({format_of(kind)}) ({lean_value(kind, value)})"
        if expr in reuse:
            return reuse[expr]
        if expr in cache:
            return cache[expr]
        proof = "(by rfl)"
        if kind in codec.SCHEMAS:
            for key, typ in reversed(codec.SCHEMAS[kind]):
                proof = f"(encodedField {encode(typ, value[key])} {proof})"
        elif vector := codec.vector_shape(kind):
            for v in reversed(value):
                proof = f"(encodedCons {encode(vector[0], v)} {proof})"
            proof = f"(encodedVector (by decide) {proof})"
        else:
            proof = "(by decide)"
        name = f"encoding{len(cache)}"
        cache[expr] = name
        out.append(
            f"theorem {name} : encode {expr} = some "
            f"{lit(codec.encode_value(kind, value))} := {proof}"
        )
        return name

    enc = encode("policy", p)
    out.insert(
        next(i for i, line in enumerate(out) if line.startswith("theorem " + enc + " :")),
        "set_option maxHeartbeats 200000 in",
    )
    out += [
        "def policyBody : Bytes := " + lit(policy_raw[16:]),
        "def policyRaw : Bytes := NativePolicyBytes.header ++ policyBody",
        f"theorem encoded : encode fmtPolicy tree = some policyBody := {enc}",
        "theorem canonical : NativePolicyBytes.Canonical policy := by decide",
        "set_option maxRecDepth 65536 in",
        f"theorem policyLength : policyRaw.length = {len(policy_raw)} := by decide",
        "theorem policyParsed : NativePolicyBytes.decodePolicy policyRaw = some (tree,policy) :=",
        (
            "  NativePolicyBytes.encoded encoded extracted "
            "canonical (by change policyRaw.length ≤ _; rw "
            "[policyLength]; decide)"
        ),
    ]
    statekeys = (
        "available_ticket_count committed_ticket_count "
        "config_id durable_sequence height parent_checkpoint_id "
        "phase round_id state_root ticket_count view"
    ).split()
    out += [
        "def stateWire : NativeStateBytes.WireState := "
        + tup(*[str(state[k]) if type(state[k]) is int else asc(state[k]) for k in statekeys]),
        "def state : NativeStateBytes.State := ⟨stateWire,0,1,0⟩",
        "def stateRaw : Bytes := " + lit(raw),
        "theorem stateValid : NativeStateBytes.StateValid state := by decide",
        "theorem stateEncoded : NativeStateBytes.encodeState stateWire = stateRaw := by rfl",
        (
            "theorem stateParsed : NativeStateBytes.decodeState "
            "stateRaw = some state := stateEncoded ▸ NativeStateBytes.stateEncoded "
            "state stateValid"
        ),
        "def snapshotId : Bytes := " + asc(state_id(raw)),
    ]
    # Actual hash preimages, with exact Lean expressions linked below. Never an approval table.
    pairs = []
    for name in ["isc", "norm", "seed", "ec", "apc"]:
        doc = docs[name.upper()]
        data = (
            ("deltareduce.008." + CERT_DOMAINS[doc["type_name"]] + ".v1").encode()
            + b"\0"
            + canonical_json_bytes(doc)
        )
        pairs.append((name, data))
    from native_isc_body import DOMAIN, Body, Context, InputTuple

    body_raw = Body(
        Context(**ctx), i["input_root"], tuple(InputTuple(**t) for t in i["tuples"])
    ).encode()
    pairs += [("iscBody", DOMAIN + body_raw), ("state", b"deltareduce:003:round-state:v1\0" + raw)]
    for label, key in [
        ("config", "fixedpoint_config"),
        ("proof", "proof_instance"),
        ("profile", "profile"),
    ]:
        pairs.append(
            (label, DOMAINS[label].encode() + b"\0" + canonical_json_bytes(golden[key]["value"]))
        )
    m = golden["manifest"]["value"]
    mp = [
        store[m["parameter_schema_id"]],
        b"deltareduce.004.scale-table.v1\0" + store[m["scale_table_id"]],
        b"deltareduce.004.shard-plan.v1\0" + store[m["shard_plan_id"]],
        b"deltareduce.004.manifest.v1\0" + store[golden["manifest"]["content_id"]],
    ]
    for r in m["shards"]:
        frame = store[r["leaf_id"]]
        mp += [frame[-r["payload_bytes"] :], b"deltareduce.004.shard-leaf.v1\0" + frame]
    layer = [r["leaf_id"] for r in m["shards"]]
    while len(layer) > 1:
        if len(layer) % 2:
            layer.append(layer[-1])
        next_layer = []
        for a, b in zip(layer[::2], layer[1::2], strict=True):
            pre = b"deltareduce.004.merkle-node.v1\0" + bytes.fromhex(a[7:]) + bytes.fromhex(b[7:])
            mp.append(pre)
            next_layer.append("sha256:" + hashlib.sha256(pre).hexdigest())
        layer = next_layer
    assert layer == [m["commitment_root"]]
    pairs += [(f"manifest{i}", v) for i, v in enumerate(mp)]
    groups = {}
    for label, data in pairs:
        expr = (
            f"NativeManifestVectors.hashInput{label[8:]}"
            if label.startswith("manifest")
            else lit(data)
        )
        out += [
            f"def pre{label} : Bytes := {expr}",
            f"theorem length{label} : pre{label}.length = {len(data)} := rfl",
        ]
        groups.setdefault(len(data), []).append(label)
    out += ["@[irreducible]", "def sha (raw : Bytes) : Bytes :="]
    pdata = dict(pairs)
    for size, labels in groups.items():
        out += [f"  if raw.length = {size} then"]
        out += [
            f"    if raw = pre{label} then {lit(hashlib.sha256(pdata[label]).digest())} else"
            for label in labels
        ]
        out += ["    [] else"]
    out += ["  []"]
    for label, data in pairs:
        out += [
            f"theorem hash{label} : sha pre{label} = {lit(hashlib.sha256(data).digest())} := by",
            f"  simp only [sha,length{label}]; decide",
        ]
    out += [
        (
            "theorem contentFromHash {domain raw pre digest expected} "
            "(preimage : domain ++ [0] ++ raw = pre)"
        ),
        "    (hashed : sha pre = digest) (size : digest.length = 32)",
        '    (spelling : NativeVoteBytes.ascii "sha256:" ++ '
        "NativeVoteBytes.hexBytes digest = expected) :",
        "    NativeStateBytes.contentId sha domain raw = some expected := by",
        "  simp only [NativeStateBytes.contentId,NativeStateBytes.contentPreimage,"
        "preimage,hashed,size,ite_true,spelling]",
        (
            "theorem contentAdapter {raw pre digest expected} "
            "(preimage : raw = pre) (hashed : sha pre = digest)"
        ),
        '    (size : digest.length = 32) (spelling : NativeVoteBytes.ascii "sha256:" ++ '
        "NativeVoteBytes.hexBytes digest = expected) :",
        "    NativePlanCoefficients.contentHash sha raw = expected := by",
        "  simp only [NativePlanCoefficients.contentHash,preimage,hashed,size,ite_true,spelling]",
    ]
    for label, mod, expr in [
        ("isc", "NativeIscCertificate", "isc"),
        ("norm", "NativeNormEvidence", "norm"),
        ("seed", "NativeSeedTranscript", "seed"),
        ("ec", "NativeEligibility", "ec"),
        ("apc", "NativePlan", "apc"),
    ]:
        out += [
            f"theorem {label}Hash : {mod}.id sha {expr} = some {label}Id := "
            f"contentFromHash rfl hash{label} rfl rfl"
        ]
    body_id = "sha256:" + hashlib.sha256(DOMAIN + body_raw).hexdigest()
    out += [
        "def iscBodyId : Bytes := " + asc(body_id),
        (
            "theorem iscBodyHash : NativeInputSetBody.bodyId "
            "sha iscBody = some iscBodyId := contentFromHash "
            "rfl hashiscBody rfl rfl"
        ),
        (
            "theorem stateHash : NativeStateBytes.contentId "
            "sha NativeStateBytes.stateDomain stateRaw = some "
            "snapshotId := contentFromHash rfl hashstate rfl "
            "rfl"
        ),
    ]
    out += [POLICY_TAIL]
    out += ["end DeltaReduce.NativeVectorSourceVectors"]
    q = [
        "import DeltaReduce.NativeVectorSourceVectors",
        "namespace DeltaReduce.NativeVectorCorpusVectors",
        "open NativeReceiptBytes (Bytes)",
        "open NativeManifestBinding",
        "open NativeManifestVectors",
        "open NativeVectorSourceVectors",
        "@[irreducible]",
        "def sourceHash (raw : Bytes) := NativePlanCoefficients.contentHash sha raw",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 60000",
    ]
    for j in range(20):
        q += [
            f"theorem hashChecked{j} : sourceHash ("
            + re.search(
                r"^theorem hashChecked" + str(j) + r" : fixtureHash (.*?) = hashOutput",
                (ROOT / "formal/proofs/DeltaReduce/NativeManifestVectors.lean").read_text("utf-8"),
                re.M,
            )[1]
            + f") = hashOutput{j} := by unfold sourceHash; "
            f"exact contentAdapter rfl hashmanifest{j} rfl rfl"
        ]
    # Reuse component proof equations with a separately checked hash registry.
    manifest_text = (ROOT / "formal/proofs/DeltaReduce/NativeManifestVectors.lean").read_text(
        "utf-8"
    )
    tail = manifest_text[
        manifest_text.index("theorem pairChecked14") : manifest_text.index(
            "theorem exactCompleteSizes"
        )
    ]
    tail = tail.replace("fixtureHash", "sourceHash")
    tail = tail.replace(
        "theorem rootChecked", "set_option maxHeartbeats 200000 in\ntheorem rootChecked"
    )
    tail = tail.replace(
        "rw [NativeManifestMerkle.tree,if_pos (by decide)]\n  rfl",
        "rw [NativeManifestMerkle.tree]\n"
        "  exact if_pos (show NativeVoteBytes.ContentId hashOutput19 by decide)",
    )
    q += [tail, Q_TAIL]
    source_q = resolve_q_source(store, golden["manifest"]["content_id"])
    for index, source_row in enumerate(source_q.rows):
        values = seq(map(str, source_row["values"]))
        q += [
            f"def result{index} : NativeVectorArithmetic.Result := "
            f"⟨row.term.source.member.input.domain,{index},NativeScaleVectors.bound{index},"
            f"[⟨row,NativeScaleVectors.bound{index}⟩],{values}⟩",
            f"theorem computed{index} : NativeVectorArithmetic.compute "
            f"NativeAccumulatorVectors.numbers {len(source_row['values'])} "
            f"[⟨row,NativeScaleVectors.bound{index}⟩] = some {values} := by",
            "  change ParameterKernel.checkedParameter (-9223372036854775808) "
            "9223372036854775807 NativeBinding.minInput NativeBinding.maxInput "
            f"1 {len(source_row['values'])} [⟨1,1,{values}⟩] = some {values}",
            "  decide",
            f"theorem reduced{index} : NativeVectorArithmetic.reduce vectorContext "
            f"row.term.source.member.input.domain {index} = some result{index} := "
            f"NativeVectorArithmetic.reducedFromSources rfl rfl computed{index}",
        ]
    q += [
        r"""
theorem originalCoefficientCoordinate (i : Nat) (within : i < 4) :
    ∃ v, result0.values[i]? = some v ∧
      checkedAccumulate (NativeVectorArithmetic.lo NativeAccumulatorVectors.numbers)
        (NativeVectorArithmetic.hi NativeAccumulatorVectors.numbers)
        (NativeVectorArithmetic.lo NativeAccumulatorVectors.numbers)
        (NativeVectorArithmetic.hi NativeAccumulatorVectors.numbers) 0
        (result0.slices.map (fun s => ((s.source.term.coefficient : Int),
          (s.block.block.frame.values[i]?).getD 0))) = some v :=
  NativeVectorArithmetic.originalCoordinateRefines contextLoaded reduced0 i within
theorem allCoordinatesRetained : (result0.values ++ result1.values ++ result2.values ++
    result3.values ++ result4.values).length = 36 := rfl
theorem sourceEntryReachesDraftJoin {codec store trust anchor}
    (binding : NativeBinding.Binding codec trust anchor store) (domain : Bytes) (index : Nat) :
    NativeVectorJoin.run binding sha policyRaw stateRaw apcId
        NativeAccumulatorVectors.configOriginal
      NativeAccumulatorVectors.proofOriginal NativeAccumulatorBinding.workerProfileBytes
      NativeAvailableQVectors.permission0 [input] domain index =
    (NativeVectorJoin.join binding vectorContext domain index).map (fun j => ⟨vectorContext,j⟩) :=
  NativeVectorJoin.runFromContext binding contextLoaded domain index
""",
        "end DeltaReduce.NativeVectorCorpusVectors",
    ]
    data = {
        "version": VERSION,
        "scope": "SIMULATED_LOCAL_RAW_POLICY_STATE_WITH_ORIGINAL004_PREIMAGES",
        "policy_hex": policy_raw.hex(),
        "state_hex": raw.hex(),
        "snapshot_id": state_id(raw),
        "certificates": docs,
        "certificate_ids": {k: content_id(v) for k, v in docs.items()},
        "original_artifacts": {
            k: v["content_id"]
            for k, v in golden.items()
            if isinstance(v, dict) and "content_id" in v
        },
        "hash_samples": {
            k: {"length": len(v), "sha256": hashlib.sha256(v).hexdigest()} for k, v in pairs
        },
        "new_encoding_lemmas": len(cache),
        "manifest_id": golden["manifest"]["content_id"],
        "native_export_authenticated": False,
        "native_execution": False,
        "gate_eligible": False,
        "state_root_preimage_verified": False,
        "native_reachability_verified": False,
        "primitive_availability_authenticated": False,
        "sha_implementation_verified": False,
        "original008_repaired": False,
        "full_draft_parameter_join_instantiated": False,
        "synthetic_candidate_admitted": False,
        "original_coordinates": 36,
        "original_q_blocks": 5,
    }
    # Independent existing Python source path; includes exact source Q validation.
    from native_available_q import resolve_plan_available_q

    checked = resolve_plan_available_q(store, content_id(docs["APC"]), edges, observations)
    assert checked is not None
    assert resolve_q_source(store, golden["manifest"]["content_id"]).manifest == m
    return "\n".join(out) + "\n", "\n".join(q) + "\n", data


POLICY_TAIL = r"""
def iscResult : NativeIscCertificate.Checked := ⟨isc,iscTree,iscId,iscBodyId⟩
def normResult : NativeNormEvidence.Checked := ⟨norm,normTree,normId⟩
def seedResult : NativeSeedTranscript.Checked := ⟨seed,seedTree,seedId⟩
def ecResult : NativeEligibilityLineage.Edge :=
    ⟨ec,seedId,ecFinalTree,ecId,iscResult,normResult,seedResult⟩
def apcResult : NativePlanLineage.Edge := ⟨apc,apcTree,apcId,iscResult,ecResult,seedResult⟩
theorem iscChecked : NativeIscCertificate.check sha context committee iscTree = some iscResult :=
  NativeIscCertificate.fromComponents iscParsed iscValid iscHash iscBodyHash
theorem normChecked : NativeNormEvidence.check sha context [iscId] normTree = some normResult :=
  NativeNormEvidence.fromComponents normParsed normValid (by decide) normHash
theorem seedChecked : NativeSeedTranscript.check sha context [iscId] seedTree = some seedResult :=
  NativeSeedTranscript.fromComponents seedParsed seedValid (by decide) seedHash
theorem ecChecked : NativeEligibilityLineage.check sha .finalized context committee
    [iscResult] [iscId] [normResult] [seedResult] ecFinalTree = some ecResult :=
  NativeEligibilityLineage.fromComponents ⟨rfl,rfl,by rfl,by rfl,by rfl,ecValid,by decide,ecHash⟩
theorem apcChecked : NativePlanLineage.check sha .finalized context committee
    [iscResult] [iscId] [ecId] apc.common.accumulator [ecResult] [seedResult] apcTree = some
        apcResult :=
  NativePlanLineage.fromComponents ⟨rfl,apcParsed,by rfl,by rfl,by rfl,apcValid,by decide,apcHash⟩
def iscSection : NativeFinalizedIscSection.Bound :=
  ⟨policy,state,context.schema,context.arithmetic,snapshotId,[iscTree],[iscResult],[iscId]⟩
theorem iscSectionChecked : NativeFinalizedIscSection.bindSection sha policy state = some
    iscSection := by
  apply NativeFinalizedIscSection.fromComponents
  refine ⟨rfl,rfl,rfl,?_,rfl,rfl,rfl,?_,rfl,?_,?_,?_,?_,?_⟩
  · change NativeStateBytes.contentId sha NativeStateBytes.stateDomain
      (NativeStateBytes.encodeState stateWire) = some snapshotId
    rw [stateEncoded]; exact stateHash
  · exact NativeIscCertificate.listFromComponents iscChecked rfl
  · decide
  · exact iscValid.1
  · decide
  · decide
  · decide
def normSection : NativeNormSection.Bound := ⟨iscSection,[normTree],[normResult]⟩
theorem normSectionChecked : NativeNormSection.bindSection sha policy state = some normSection :=
  NativeNormSection.fromComponents ⟨iscSectionChecked,rfl,NativeNormEvidence.listFromComponents
      normChecked rfl,by decide⟩
def ecSection : NativeEligibilitySection.Bound :=
  ⟨normSection,[seedTree],[seedResult],[],[],[ecFinalTree],[ecResult],[ecId]⟩
theorem ecSectionChecked : NativeEligibilitySection.bindSection sha policy state = some ecSection
    :=
  NativeEligibilitySection.fromComponents ⟨normSectionChecked,rfl,
    NativeSeedTranscript.listFromComponents seedChecked rfl,rfl,rfl,rfl,by
      change NativeEligibilityLineage.checkAll sha .finalized context committee [iscResult]
          [iscId]
        [normResult] [seedResult] [ecFinalTree] = some [ecResult]
      simp only [NativeEligibilityLineage.checkAll,ecChecked,Bind.bind,Option.bind],rfl,by decide⟩
def planSection : NativePlanSection.Bound :=
    ⟨ecSection,apc.common.accumulator,[],[],[apcTree],[apcResult],[apcId]⟩
theorem planSectionChecked : NativePlanSection.bindSection sha policy state = some planSection :=
  NativePlanSection.fromComponents ⟨ecSectionChecked,rfl,rfl,rfl,rfl,by
    change NativePlanLineage.checkAll sha .finalized context committee [iscResult] [iscId] [ecId]
      apc.common.accumulator [ecResult] [seedResult] [apcTree] = some [apcResult]
    simp only [NativePlanLineage.checkAll,apcChecked,Bind.bind,Option.bind],rfl,by decide⟩
theorem rawPlanPrepared : NativePlanSection.prepare sha policyRaw stateRaw = some planSection :=
  NativeSourceRefusal.sectionFromSources policyParsed stateParsed planSectionChecked
def sourceRow : NativePlanMembers.Row :=
  ⟨⟨isc.body.tuples.head (by decide),ec.common.entries.head (by decide)⟩,
    apc.common.weights.head (by decide),apc.common.buckets.head (by decide)⟩
def members : NativePlanMembers.Bound := ⟨planSection,apcResult,[sourceRow]⟩
theorem derivedMembers : NativePlanMembers.derive apcResult = some [sourceRow] := by decide
theorem rawMembersPrepared : NativePlanMembers.prepare sha policyRaw stateRaw apcId = some members
    :=
  NativePlanMembers.prepareFromSource ⟨rawPlanPrepared,by rfl,by decide,derivedMembers⟩
theorem configHash : NativePlanCoefficients.contentHash sha NativeAccumulatorVectors.input0 =
    NativeAccumulatorVectors.id0 := contentAdapter rfl hashconfig rfl rfl
theorem proofHash : NativePlanCoefficients.contentHash sha NativeAccumulatorVectors.input1 =
    NativeAccumulatorVectors.id1 := contentAdapter rfl hashproof rfl rfl
theorem profileHash : NativePlanCoefficients.contentHash sha NativeAccumulatorVectors.input2 =
    NativeAccumulatorVectors.id2 := contentAdapter rfl hashprofile rfl rfl
theorem accumulatorLoaded : NativeAccumulatorBinding.load (NativePlanCoefficients.contentHash sha)
    NativeAccumulatorVectors.configOriginal NativeAccumulatorVectors.proofOriginal
    NativeAccumulatorBinding.workerProfileBytes apc.common.accumulator = some
        NativeAccumulatorVectors.bound :=
  NativeAccumulatorBinding.loadFromSource ⟨NativeAccumulatorVectors.configDecoded,
    NativeAccumulatorVectors.proofDecoded,NativeAccumulatorVectors.numericDecoded,
    NativeAccumulatorVectors.metadata,rfl,profileHash,configHash,by decide,proofHash⟩
def coefficients : NativePlanCoefficients.Bound :=
    ⟨members,NativeAccumulatorVectors.bound,[⟨sourceRow,1⟩]⟩
theorem rawCoefficients : NativePlanCoefficients.bind sha policyRaw stateRaw apcId
    NativeAccumulatorVectors.configOriginal NativeAccumulatorVectors.proofOriginal
    NativeAccumulatorBinding.workerProfileBytes = some coefficients :=
  NativePlanCoefficients.bindFromSource ⟨rawMembersPrepared,accumulatorLoaded,by decide,by decide⟩
theorem original008NotRepaired : apcId ≠ NativePlanVectors.qc ∧
    apc.common.accumulator ≠ NativePlanVectors.certificate.common.accumulator := by decide
"""
Q_TAIL = r"""
def input : NativeAvailableQ.Input :=
  ⟨NativeSchemaVectors.original,NativeScaleVectors.original,NativeShardPlanVectors.original,
    original,hashOutput3,raws,NativeAvailableQVectors.observation0⟩
def available : NativeAccumulatorBinding.BoundCorpus := ⟨bound,NativeAccumulatorVectors.bound⟩
theorem availableLoaded : NativeAvailableQ.load (NativePlanCoefficients.contentHash sha)
    NativeAccumulatorVectors.configOriginal NativeAccumulatorVectors.proofOriginal
    NativeAccumulatorBinding.workerProfileBytes input = some available :=
  by
    have bounds : NativeAccumulatorBinding.load sourceHash NativeAccumulatorVectors.configOriginal
        NativeAccumulatorVectors.proofOriginal NativeAccumulatorBinding.workerProfileBytes
        apc.common.accumulator = some NativeAccumulatorVectors.bound := by
      delta sourceHash
      exact accumulatorLoaded
    have joined : NativeAvailableQ.load sourceHash NativeAccumulatorVectors.configOriginal
        NativeAccumulatorVectors.proofOriginal NativeAccumulatorBinding.workerProfileBytes input =
          some available := NativeAccumulatorBinding.corpusFromSources wholeManifest bounds
      (show NativeAccumulatorBinding.CorpusLinks bound NativeAccumulatorVectors.bound from
        ⟨rfl,rfl,rfl,rfl,rfl,rfl⟩)
    have sameHash : sourceHash = NativePlanCoefficients.contentHash sha := by
      unfold sourceHash
      rfl
    exact (congrArg (fun h => NativeAvailableQ.load h NativeAccumulatorVectors.configOriginal
      NativeAccumulatorVectors.proofOriginal NativeAccumulatorBinding.workerProfileBytes input =
        some available) sameHash).mp joined
def row : NativePlanQCorpus.Row := ⟨⟨sourceRow,1⟩,available⟩
theorem rowLoaded : NativePlanQCorpus.loadRow sha NativeAccumulatorVectors.configOriginal
    NativeAccumulatorVectors.proofOriginal NativeAccumulatorBinding.workerProfileBytes
        coefficients
    NativeAvailableQVectors.permission0 row.term input = some row :=
  NativePlanQCorpus.rowFromSources availableLoaded NativeAvailableQVectors.primitive0
    NativeAvailableQVectors.coverage0
      ⟨rfl,rfl,rfl,rfl,rfl,rfl,rfl⟩
def corpusBound : NativePlanQCorpus.Bound := ⟨coefficients,[row]⟩
theorem corpusLoaded : NativePlanQCorpus.bind sha policyRaw stateRaw apcId
    NativeAccumulatorVectors.configOriginal NativeAccumulatorVectors.proofOriginal
    NativeAccumulatorBinding.workerProfileBytes NativeAvailableQVectors.permission0 [input] = some
        corpusBound :=
  NativePlanQCorpus.bindFromSources rawCoefficients
    (NativePlanQCorpus.rowsFromSources (.cons rowLoaded .nil))
def vectorContext : NativeVectorContext.Bound := ⟨corpusBound,row⟩
theorem contextLoaded : NativeVectorContext.bind sha policyRaw stateRaw apcId
    NativeAccumulatorVectors.configOriginal NativeAccumulatorVectors.proofOriginal
    NativeAccumulatorBinding.workerProfileBytes NativeAvailableQVectors.permission0 [input] = some
        vectorContext :=
  NativeVectorContext.bindFromSources corpusLoaded (NativeVectorContext.alignFromSources rfl (by
      intro r h
      have same : r = row := List.mem_singleton.mp h
      subst r
      exact ⟨rfl,rfl,rfl⟩))
theorem completeRawInputs : vectorContext.source.rows.map (fun r => r.term.source) = members.rows
    ∧
    vectorContext.source.rows.length = 1 := NativeVectorContext.completeOriginalRows contextLoaded
theorem originalCurrentParentOnly : vectorContext.first.corpus.manifest.manifest.wire.parent =
    state.wire.parent := rfl
theorem candidateRetainedOnly : policy.candidates = [candidate] := rfl
theorem missingInputsRejected : NativePlanQCorpus.bind sha policyRaw stateRaw apcId
    NativeAccumulatorVectors.configOriginal NativeAccumulatorVectors.proofOriginal
    NativeAccumulatorBinding.workerProfileBytes NativeAvailableQVectors.permission0 [] = none :=
  NativePlanQCorpus.bindFromAbsentRows rawCoefficients rfl
theorem extraInputsRejected : NativePlanQCorpus.bind sha policyRaw stateRaw apcId
    NativeAccumulatorVectors.configOriginal NativeAccumulatorVectors.proofOriginal
    NativeAccumulatorBinding.workerProfileBytes NativeAvailableQVectors.permission0 [input,input]
        = none :=
  NativePlanQCorpus.bindFromAbsentRows rawCoefficients
    (NativePlanQCorpus.extraSingleInput rowLoaded)

"""


if __name__ == "__main__":
    policy, corpus, summary = generate()
    for module, text in [
        ("NativeVectorSourceVectors", policy),
        ("NativeVectorCorpusVectors", corpus),
    ]:
        (ROOT / f"formal/proofs/DeltaReduce/{module}.lean").write_text(
            text, encoding="utf-8", newline="\n"
        )
    write_canonical_json(ROOT / "formal/proposals/native-vector-source-vectors.json", summary)
    print(
        json.dumps(
            {k: v for k, v in summary.items() if not k.endswith("hex") and k != "certificates"}
        )
    )
