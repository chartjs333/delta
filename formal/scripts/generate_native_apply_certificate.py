"""Original native APPLY wire inputs; computed JSON and synthetic QC samples.

The finalized sample is constructed by the source as_apply_certificate rule;
it is not an independently observed finalized native QC or execution.
"""

import hashlib
import json
from pathlib import Path

import generate_native_aggregate as prior
import native_policy_codec as codec
from formal_artifacts import canonical_json_bytes, load_json_strict
from generate_native_policy_schema import format_of, lean_value
from generate_native_wal_lean import lit
from native_certificate_chain import NATIVE_SEMANTICS, content_id

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "formal/proofs/DeltaReduce/NativeApplyCertificateVectors.lean"
PIN = "d82c14dda8356bfebc1cc1febe3c2fd09c3393b467cc99bacd565b506a91d2ea"


def digest(domain, doc):
    return (
        "sha256:" + hashlib.sha256(domain.encode() + b"\0" + canonical_json_bytes(doc)).hexdigest()
    )


def document(kind, tree):
    value = {**tree.get("context", {}), **{k: v for k, v in tree.items() if k != "context"}}
    value.update(formal_semantics_id=NATIVE_SEMANTICS, schema_version="1.0.0", type_name=kind)
    if kind == "APPLY_ARITHMETIC_PROFILE":
        value = json.loads(json.dumps(value))
        for key in ["learning_rate", "momentum", "weight_decay"]:
            value[key]["numerator"] = str(value[key]["numerator"])
        for row in value["domain_weights"]:
            row["pi"]["numerator"] = str(row["pi"]["numerator"])
    return value


def source():
    root, _, _, _, committee, _ = prior.source()
    observed = load_json_strict(
        ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
    )
    if hashlib.sha256(canonical_json_bytes(observed)).hexdigest() != PIN:
        raise ValueError("original native APPLY policy observation changed")
    policies = []
    for name in ["codec-APPLY", "guard-APPLY"]:
        row = next(r for r in observed["observed"] if r["name"] == name)
        raw = bytes.fromhex(row["policy_hex"])
        parsed = codec.decode(raw)
        if codec.HEADER + codec.encode_value("policy", parsed) != raw:
            raise ValueError("original APPLY policy bytes changed")
        policies.append(parsed)
    if policies[0] != policies[1]:
        raise ValueError("original codec and guarded APPLY policy differ")
    snap = policies[0]["snapshot"]
    profile = snap["apply_profiles"][0]
    candidate = snap["apply_candidates"][0]
    pd = document("APPLY_ARITHMETIC_PROFILE", profile)
    cd = document("APPLY_CANDIDATE", candidate)
    pid = digest("deltareduce.008.apply-arithmetic-profile.v1", pd)
    cid = digest("deltareduce.008.apply-candidate.v1", cd)
    if (
        candidate["apply_arithmetic_profile_id"] != pid
        or candidate["aggregate_root_qc_id"] != content_id(root)
        or snap["finalized_aggregate_root_ids"] != [content_id(root)]
        or snap["apply_qcs"]
        or snap["finalized_apply_ids"]
    ):
        raise ValueError("original APPLY profile/root/finalized scope changed")
    cert = {
        k: candidate[k]
        for k in [
            "context",
            "aggregate_root_qc_id",
            "apply_arithmetic_profile_id",
            "next_model_hash",
            "next_optimizer_hash",
            "parent_checkpoint_id",
        ]
    }
    cert.update(
        apply_candidate_id=cid, quorum_threshold=(2 * len(committee)) // 3 + 1, signer_ids=committee
    )
    qd = document("APPLY_QC", cert)
    return profile, candidate, cert, pd, cd, qd, pid, cid, committee


def generate():
    profile, candidate, cert, pd, cd, qd, pid, cid, _ = source()
    asc = lambda x: "(NativeVoteBytes.ascii " + json.dumps(x) + ")"  # noqa: E731
    strings = lambda xs: "[" + ",".join(map(asc, xs)) + "]"  # noqa: E731
    frac = lambda x: "⟨" + str(x["numerator"]) + "," + str(x["denominator"]) + "⟩"  # noqa: E731
    out = [
        "import DeltaReduce.NativeApplySection",
        "import DeltaReduce.NativeAggregateVectors",
        "",
        "/-! Original pinned APPLY wire components; JSON/SHA rederived in Python.",
        ("Finalized QC is synthetic via the actual native proposed-certificate rule."),
        ("No full native policy execution, crypto authentication or arithmetic derivation. -/"),
        "namespace DeltaReduce.NativeApplyCertificateVectors",
        ("open NativeReceiptBytes NativePolicyCodec NativePolicySchema NativeApplyCertificate"),
        "open NativeConfigAdmission (encodedField encodedCons encodedVector)",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 200000",
        "def profile : NativeApplyProfile.Profile := ⟨"
        + asc(profile["accumulator_proof_id"])
        + ",["
        + ",".join(
            "⟨" + asc(w["domain_id"]) + "," + frac(w["pi"]) + "⟩" for w in profile["domain_weights"]
        )
        + "],"
        + frac(profile["learning_rate"])
        + ","
        + frac(profile["momentum"])
        + ",1,"
        + asc(profile["rounding"])
        + ","
        + frac(profile["weight_decay"])
        + "⟩",
        "def candidate : Candidate := ⟨NativeIscAdmissionVectors.inputContext,"
        + ",".join(
            asc(candidate[k])
            for k in ["aggregate_root_qc_id", "apply_arithmetic_profile_id", "next_model_hash"]
        )
        + ","
        + strings(candidate["next_model_values"])
        + ","
        + asc(candidate["next_optimizer_hash"])
        + ","
        + strings(candidate["next_optimizer_values"])
        + ","
        + asc(candidate["parent_checkpoint_id"])
        + ","
        + asc(candidate["parent_optimizer_hash"])
        + "⟩",
        "def pid : Bytes := " + asc(pid),
        "def cid : Bytes := " + asc(cid),
        (
            "def certificate : Certificate := proposedCertificate "
            "NativeIscCertificateVectors.committee candidate cid"
        ),
        "def profileTree : Value := " + lean_value("apply_profile", profile),
        "def candidateTree : Value := " + lean_value("apply_candidate", candidate),
        "def certificateTree : Value := " + lean_value("apply_qc", cert),
        ("def finalizedTree : Value := .pair certificateTree (.pair candidateTree .end)"),
        (
            "theorem profileParsed : NativeApplyProfile.readProfile "
            "profileTree = some profile := NativeApplyProfile.profileRead "
            "profile"
        ),
        (
            "theorem candidateParsed : readCandidate candidateTree = some "
            "candidate := candidateRead candidate"
        ),
        (
            "theorem certificateParsed : readCertificate certificateTree = "
            "some certificate := certificateRead certificate"
        ),
        (
            "theorem finalizedParsed : readFinalized finalizedTree = some "
            "⟨certificate,candidate⟩ := finalizedRead ⟨certificate,candidate⟩"
        ),
        "theorem profileValid : NativeApplyProfile.Valid profile := by decide",
        (
            "theorem candidateValid : CandidateValid candidate.context "
            "candidate := ⟨NativeIscCertificateVectors.valid.2.1.1,rfl,"
        )
        + ",".join(["by decide"] * 11)
        + "⟩",
        (
            "theorem certificateValid : CertificateValid candidate.context "
            "NativeIscCertificateVectors.committee certificate := "
        )
        + "⟨NativeIscCertificateVectors.valid.2.1.1,rfl,"
        + ",".join(["by decide"] * 6)
        + ",NativeIscCertificateVectors.valid.1,by decide⟩",
    ]
    cache = {}

    def encode(kind, value):
        key = (kind, json.dumps(value, sort_keys=True))
        if key in cache:
            return cache[key]
        vector = codec.vector_shape(kind)
        proof = "(by rfl)"
        if kind in codec.SCHEMAS:
            for field, typ in reversed(codec.SCHEMAS[kind]):
                proof = f"(encodedField {encode(typ, value[field])} {proof})"
        elif vector:
            for item in reversed(value):
                proof = f"(encodedCons {encode(vector[0], item)} {proof})"
            proof = f"(encodedVector (by decide) {proof})"
        else:
            proof = "(by decide)"
        name = f"encoding{len(cache)}"
        cache[key] = name
        out.append(
            f"theorem {name} : encode ({format_of(kind)}) ({lean_value(kind, value)}) = some "
            f"{lit(codec.encode_value(kind, value))} := {proof}"
        )
        return name

    for name, kind, obj, fmt in [
        ("profile", "apply_profile", profile, "fmtApplyProfile"),
        ("candidate", "apply_candidate", candidate, "fmtApplyCandidate"),
        ("certificate", "apply_qc", cert, "fmtApplyQc"),
    ]:
        proof = encode(kind, obj)
        out.extend(
            [
                f"def {name}Raw : Bytes := " + lit(codec.encode_value(kind, obj)),
                f"theorem {name}Encoded : encode {fmt} {name}Tree = some {name}Raw := {proof}",
                (
                    f"theorem {name}Decoded : NativePolicyCodec.decode {fmt} {name}Raw "
                    f"= some {name}Tree := NativePolicyCodec.encoded {name}Encoded"
                ),
            ]
        )
    docs = [pd, cd, qd]
    prefixes = [
        "deltareduce.008.apply-arithmetic-profile.v1",
        "deltareduce.008.apply-candidate.v1",
        "deltareduce.008.apply-qc.v1",
    ]
    pres = [
        d.encode() + b"\0" + canonical_json_bytes(doc)
        for d, doc in zip(prefixes, docs, strict=True)
    ]
    for i, pre in enumerate(pres):
        out.append(f"def preimage{i} : Bytes := " + lit(pre))
    expr = "NativeAggregateVectors.sha raw"
    for i in reversed(range(3)):
        expr = f"if raw = preimage{i} then {lit(hashlib.sha256(pres[i]).digest())} else {expr}"
    out.append("def sha (raw : Bytes) : Bytes := " + expr)
    for i, pre in enumerate(pres):
        steps = ",".join(["if_neg (by decide)"] * i + ["if_pos rfl"])
        out.append(
            f"theorem hash{i} : sha preimage{i} = "
            f"{lit(hashlib.sha256(pre).digest())} := by unfold sha; rw "
            f"[{steps}]"
        )
    out.append(
        "theorem contentFromHash {domain raw pre digest expected} "
        "(preimage : domain ++ [0] ++ raw = pre) "
        "(hashed : sha pre = digest) (size : digest.length = 32) "
        '(spelling : NativeVoteBytes.ascii "sha256:" ++ '
        "NativeVoteBytes.hexBytes digest = expected) : "
        "NativeStateBytes.contentId sha domain raw = some expected := by simp only "
        "[NativeStateBytes.contentId,NativeStateBytes.contentPreimage,"
        "preimage,hashed,size,ite_true,spelling]"
    )
    out.append("def qid : Bytes := " + asc(digest(prefixes[2], qd)))
    for i, (name, doc, expr, ident, identifier) in enumerate(
        [
            (
                "profile",
                pd,
                "NativeApplyProfile.json profile",
                "NativeApplyProfile.id sha profile",
                "pid",
            ),
            ("candidate", cd, "candidateJSON candidate", "candidateId sha candidate", "cid"),
            (
                "certificate",
                qd,
                "certificateJSON certificate",
                "certificateId sha certificate",
                "qid",
            ),
        ]
    ):
        out.extend(
            [
                f"def {name}JSONBytes : Bytes := " + lit(canonical_json_bytes(doc)),
                f"theorem {name}JSONExact : {expr} = {name}JSONBytes := by rfl",
                (
                    f"theorem {name}Computed : {ident} = some {identifier} := "
                    f"NativeContractSize.fromComponents "
                )
                + f"(by rw [{name}JSONExact]; decide) (contentFromHash rfl hash{i} rfl rfl)",
            ]
        )
    out.extend(
        [
            ("def checkedProfile : NativeApplyProfile.Checked := ⟨profile,profileTree,pid⟩"),
            (
                "theorem profileChecked : NativeApplyProfile.check sha "
                "profileTree = some checkedProfile := "
                "NativeApplyProfile.fromComponents profileParsed profileValid "
                "profileComputed"
            ),
            "def decoded : NativeApplyLineage.Decoded := ⟨candidate,certificate,cid⟩",
            (
                "theorem proposedParsed : NativeApplyLineage.decode sha .proposed"
                " NativeIscCertificateVectors.committee candidateTree = some "
                "decoded := by simp only "
                "[NativeApplyLineage.decode,candidateParsed,bind,Option.bind,candidateComputed];"
                " rfl"
            ),
            (
                "theorem finalParsed : NativeApplyLineage.decode sha .finalized "
                "NativeIscCertificateVectors.committee finalizedTree = some "
                "decoded := by simp only "
                "[NativeApplyLineage.decode,finalizedParsed,bind,Option.bind,candidateComputed];"
                " rfl"
            ),
            (
                "theorem links : NativeApplyLineage.Links candidate.parent "
                "[NativeAggregateVectors.qc] decoded "
                "NativeAggregateVectors.finalizedEdge checkedProfile := by decide"
            ),
        ]
    )
    for name, mode, tree, ident, parsing in [
        ("proposed", "proposed", "candidateTree", "cid", "proposedParsed"),
        ("final", "finalized", "finalizedTree", "qid", "finalParsed"),
    ]:
        args = (
            f"sha .{mode} candidate.context "
            f"NativeIscCertificateVectors.committee candidate.parent "
            f"[NativeAggregateVectors.qc] "
            f"[NativeAggregateVectors.finalizedEdge] [checkedProfile] {tree}"
        )
        out.extend(
            [
                (
                    f"def {name}Edge : NativeApplyLineage.Edge := "
                    f"⟨decoded,{tree},NativeAggregateVectors.finalizedEdge,checkedProfile,qid,{ident}⟩"
                ),
                f"theorem {name}Source : NativeApplyLineage.Source {args} {name}Edge := "
                + (
                    f"⟨rfl,{parsing},by rfl,by "
                    f"rfl,candidateValid,certificateValid,links,certificateComputed,rfl⟩"
                ),
                (
                    f"theorem {name}Checked : NativeApplyLineage.check {args} = some "
                    f"{name}Edge := NativeApplyLineage.fromComponents {name}Source"
                ),
            ]
        )
    negative = [
        ("zeroDenominator", "¬ NativeApplyProfile.FractionValid ⟨1,0⟩"),
        ("unreducedFraction", "¬ NativeApplyProfile.FractionValid ⟨2,2⟩"),
        ("negativeWireBits", "¬ NativeApplyProfile.FractionValid ⟨2^64-1,1⟩"),
        ("largeUnsignedDenominator", "NativeApplyProfile.FractionValid ⟨1,2^64-1⟩"),
        ("zeroRationalReduced", "NativeApplyProfile.FractionValid ⟨0,1⟩"),
        ("nonreducedZero", "¬ NativeApplyProfile.FractionValid ⟨0,2⟩"),
        ("noNesterov", "¬ NativeApplyProfile.Valid {profile with nesterov := 0}"),
        (
            "wrongRounding",
            ('¬ NativeApplyProfile.Valid {profile with rounding := NativeVoteBytes.ascii "OTHER"}'),
        ),
        ("noWeights", "¬ NativeApplyProfile.Valid {profile with weights := []}"),
        (
            "duplicateWeights",
            (
                "¬ NativeApplyProfile.Valid {profile with weights := "
                "profile.weights ++ profile.weights}"
            ),
        ),
        ("emptyModel", "¬ CandidateValid candidate.context {candidate with modelValues := []}"),
        (
            "unequalVectors",
            "¬ CandidateValid candidate.context {candidate with optimizerValues := []}",
        ),
        (
            "outOfRangeCoordinate",
            (
                "¬ CandidateValid candidate.context {candidate with modelValues "
                ':= [NativeVoteBytes.ascii "9223372036854775808"]}'
            ),
        ),
        (
            "negativeEndpoint",
            ('NativeCertificateDecimal.Valid false (NativeVoteBytes.ascii "-9223372036854775808")'),
        ),
        (
            "retainedNegativeZero",
            'NativeCertificateDecimal.Valid false (NativeVoteBytes.ascii "-00")',
        ),
        (
            "retainedNegativeLeadingZero",
            'NativeCertificateDecimal.Valid false (NativeVoteBytes.ascii "-01")',
        ),
        (
            "wrongParent",
            (
                "¬ NativeApplyLineage.Links [] [NativeAggregateVectors.qc] "
                "decoded NativeAggregateVectors.finalizedEdge checkedProfile"
            ),
        ),
        (
            "unfinalizedRoot",
            (
                "¬ NativeApplyLineage.Links candidate.parent [] decoded "
                "NativeAggregateVectors.finalizedEdge checkedProfile"
            ),
        ),
        (
            "wrongCertifiedCandidate",
            (
                "¬ NativeApplyLineage.Links candidate.parent "
                "[NativeAggregateVectors.qc] {decoded with certificate := "
                "{certificate with candidate := []}} "
                "NativeAggregateVectors.finalizedEdge checkedProfile"
            ),
        ),
        (
            "wrongCertifiedModel",
            (
                "¬ NativeApplyLineage.Links candidate.parent "
                "[NativeAggregateVectors.qc] {decoded with certificate := "
                "{certificate with model := []}} "
                "NativeAggregateVectors.finalizedEdge checkedProfile"
            ),
        ),
        (
            "wrongCertifiedOptimizer",
            (
                "¬ NativeApplyLineage.Links candidate.parent "
                "[NativeAggregateVectors.qc] {decoded with certificate := "
                "{certificate with optimizer := []}} "
                "NativeAggregateVectors.finalizedEdge checkedProfile"
            ),
        ),
        (
            "wrongProfile",
            (
                "¬ NativeApplyLineage.Links candidate.parent "
                "[NativeAggregateVectors.qc] decoded "
                "NativeAggregateVectors.finalizedEdge {checkedProfile with id := "
                "[]}"
            ),
        ),
    ]
    out.extend(f"theorem {n} : {p} := by decide" for n, p in negative)
    out.extend(
        [
            (
                "theorem valuesNotRecomputed : CandidateValid candidate.context "
                '{candidate with modelValues := [NativeVoteBytes.ascii "999"]} :='
                " by decide"
            ),
            (
                "theorem parentOptimizerNotCompared : NativeApplyLineage.Links "
                "candidate.parent [NativeAggregateVectors.qc] {decoded with "
                "candidate := {candidate with parentOptimizer := "
                "candidate.model}} NativeAggregateVectors.finalizedEdge "
                "checkedProfile := by decide"
            ),
            "end DeltaReduce.NativeApplyCertificateVectors",
            "",
        ]
    )
    return "\n".join(out)


if __name__ == "__main__":
    TARGET.write_text(generate(), encoding="utf-8", newline="\n")
    print(TARGET.relative_to(ROOT))
