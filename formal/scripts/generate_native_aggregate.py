"""Original ROOT policy/certificate/Merkle components; explicit finite SHA samples."""

import hashlib
import json
from pathlib import Path

import generate_native_parameter as prior
import native_policy_codec as codec
from formal_artifacts import canonical_json_bytes, load_json_strict
from generate_native_policy_schema import format_of, lean_value
from generate_native_wal_lean import lit
from native_certificate_chain import content_id, merkle_root
from native_isc_body import Context, text, u64

ROOT = Path(__file__).resolve().parents[2]
TARGET = ROOT / "formal/proofs/DeltaReduce/NativeAggregateVectors.lean"


def source():
    _, _, _, docs, committee, observed = prior.source()
    doc = docs["ROOT"]
    policy = load_json_strict(
        ROOT / "formal/proposals/evidence/native-policy-wal/cpp-cross-check.json"
    )
    if (
        hashlib.sha256(canonical_json_bytes(policy)).hexdigest()
        != "d82c14dda8356bfebc1cc1febe3c2fd09c3393b467cc99bacd565b506a91d2ea"
    ):
        raise ValueError("pinned original policy observation changed")
    snapshots = {}
    for name in ["codec-AGGREGATE_ROOT", "codec-APPLY"]:
        row = next(r for r in policy["observed"] if r["name"] == name)
        raw = bytes.fromhex(row["policy_hex"])
        parsed = codec.decode(raw)
        if codec.HEADER + codec.encode_value("policy", parsed) != raw:
            raise ValueError("original ROOT policy wire changed")
        snapshots[name] = parsed["snapshot"]
    proposed = snapshots["codec-AGGREGATE_ROOT"]["aggregate_root_bodies"][0]
    snap = snapshots["codec-APPLY"]
    tree = snap["aggregate_root_qcs"][0]
    projected = {
        **tree["context"],
        **{k: v for k, v in tree.items() if k != "context"},
        "formal_semantics_id": doc["formal_semantics_id"],
        "schema_version": "1.0.0",
        "type_name": "AGGREGATE_ROOT_QC",
    }
    expected = {k: v for k, v in tree.items() if k not in ["quorum_threshold", "signer_ids"]}
    if (
        projected != doc
        or proposed != expected
        or canonical_json_bytes(doc).hex() != observed["certificates"]["ROOT"]["json_hex"]
        or content_id(doc) != observed["certificates"]["ROOT"]["id"]
        or snap["finalized_aggregate_root_ids"] != [content_id(doc)]
        or doc["required_keys"] != snap["required_parameter_keys"]
        or doc["input_set_certificate_id"] != content_id(docs["ISC"])
        or doc["eligibility_certificate_id"] != content_id(docs["EC"])
        or doc["aggregation_plan_certificate_id"] != content_id(docs["APC"])
        or doc["leaves"]
        != [
            {
                "domain_id": docs["PARAMETER"]["domain_id"],
                "shard_id": docs["PARAMETER"]["shard_id"],
                "parameter_shard_qc_id": content_id(docs["PARAMETER"]),
            }
        ]
        or doc["merkle_root"] != merkle_root(doc["leaves"])
        or body_id(doc) != observed["bodies"]["ROOT"]
    ):
        raise ValueError("original ROOT bytes/identity/parents/matrix changed")
    for count in range(1, 5):
        if merkle_root(sample_leaves(count)) != observed["merkle_cases"][str(count)]:
            raise ValueError("pinned native Merkle component changed")
    return doc, tree, proposed, docs, committee, observed


def sample_leaves(count):
    return [
        {
            "domain_id": "domain-a",
            "parameter_shard_qc_id": "sha256:" + str(i + 1) * 64,
            "shard_id": f"shard-{i}",
        }
        for i in range(count)
    ]


def body_bytes(doc):
    return (
        Context(**{k: doc[k] for k in Context.__annotations__}).encode()
        + text(doc["aggregation_plan_certificate_id"])
        + text(doc["eligibility_certificate_id"])
        + text(doc["input_set_certificate_id"])
        + u64(len(doc["leaves"]))
        + b"".join(
            text(item["domain_id"]) + text(item["parameter_shard_qc_id"]) + text(item["shard_id"])
            for item in doc["leaves"]
        )
        + text(doc["merkle_root"])
        + u64(len(doc["required_keys"]))
        + b"".join(text(k["domain_id"]) + text(k["shard_id"]) for k in doc["required_keys"])
    )


def body_id(doc):
    return (
        "sha256:"
        + hashlib.sha256(b"deltareduce.vote.aggregate-root-body.v1\0" + body_bytes(doc)).hexdigest()
    )


def generate():
    doc, tree, proposed, _, committee, observed = source()

    def asc(x):
        return "(NativeVoteBytes.ascii " + json.dumps(x) + ")"

    def strings(xs):
        return "[" + ",".join(map(asc, xs)) + "]"

    def leaf(item):
        return (
            "⟨"
            + ",".join(asc(item[k]) for k in ["domain_id", "parameter_shard_qc_id", "shard_id"])
            + "⟩"
        )

    leaves = "[" + ",".join(map(leaf, doc["leaves"])) + "]"
    keys = (
        "["
        + ",".join(
            "⟨" + asc(k["domain_id"]) + "," + asc(k["shard_id"]) + "⟩" for k in doc["required_keys"]
        )
        + "]"
    )
    common = (
        "⟨NativeIscAdmissionVectors.inputContext,"
        + ",".join(
            asc(doc[k])
            for k in [
                "aggregation_plan_certificate_id",
                "eligibility_certificate_id",
                "input_set_certificate_id",
            ]
        )
        + ","
        + leaves
        + ","
        + asc(doc["merkle_root"])
        + ","
        + keys
        + "⟩"
    )
    out = [
        "import DeltaReduce.NativeAggregateSection",
        "import DeltaReduce.NativeParameterVectors",
        "",
        "/-! Pinned original ROOT and retained native Merkle counts1..4. No new native run.",
        "Finite SHA samples are not a general hash proof or authenticated exporter. -/",
        "namespace DeltaReduce.NativeAggregateVectors",
        "open NativeReceiptBytes NativePolicyCodec NativePolicySchema NativeAggregateRoot",
        "open NativeConfigAdmission (encodedField encodedCons encodedVector)",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 200000",
        "def certificate : Certificate := ⟨"
        + common
        + ","
        + str(doc["quorum_threshold"])
        + ","
        + strings(doc["signer_ids"])
        + "⟩",
        "def originalLeaf : NativeAggregateMerkle.Leaf := " + leaf(doc["leaves"][0]),
        "def tree : Value := " + lean_value("root", tree),
        "def bodyTree : Value := " + lean_value("root_body", proposed),
        "theorem treeValue : tree = value certificate := by rfl",
        "theorem parsed : read tree = some certificate := treeValue ▸ certRead certificate",
        "theorem bodyTreeValue : bodyTree = bodyValue certificate.common := by rfl",
        (
            "theorem bodyParsed : readBody bodyTree = some certificate.common "
            ":= bodyTreeValue ▸ bodyRead certificate.common"
        ),
        (
            "theorem commonValid : CommonValid certificate.common.context "
            "certificate.common := "
            "⟨NativeIscCertificateVectors.valid.2.1.1,rfl,"
        )
        + ",".join(["by decide"] * 12)
        + "⟩",
        (
            "theorem valid : Valid certificate.common.context "
            "NativeIscCertificateVectors.committee certificate := "
            "⟨commonValid,NativeIscCertificateVectors.valid.1,NativeIscCertificateVectors.valid.2.2⟩"
        ),
        "def originalJSON : Bytes := " + lit(canonical_json_bytes(doc)),
        "theorem exactJSON : json certificate = originalJSON := by rfl",
        "def computedBodyBytes : Bytes := " + lit(body_bytes(doc)),
        "theorem exactBodyBytes : bodyBytes certificate.common = computedBodyBytes := by rfl",
    ]
    cache = {}

    def encode(kind, value):
        key = (kind, json.dumps(value, sort_keys=True))
        if key in cache:
            return cache[key]
        vector = codec.vector_shape(kind)
        if kind in codec.SCHEMAS:
            proof = "(by rfl)"
            for field, typ in reversed(codec.SCHEMAS[kind]):
                proof = f"(encodedField {encode(typ, value[field])} {proof})"
        elif vector:
            proof = "(by rfl)"
            for item in reversed(value):
                proof = f"(encodedCons {encode(vector[0], item)} {proof})"
            proof = f"(encodedVector (by decide) {proof})"
        else:
            proof = "(by decide)"
        name = f"encoding{len(cache)}"
        cache[key] = name
        out.append(
            f"theorem {name} : encode ({format_of(kind)}) "
            f"({lean_value(kind, value)}) = some "
            f"{lit(codec.encode_value(kind, value))} := {proof}"
        )
        return name

    for name, kind, obj, var, fmt in [
        ("raw", "root", tree, "tree", "fmtRoot"),
        ("bodyRaw", "root_body", proposed, "bodyTree", "fmtRootBody"),
    ]:
        proof = encode(kind, obj)
        out.extend(
            [
                "def " + name + " : Bytes := " + lit(codec.encode_value(kind, obj)),
                f"theorem {name}Encoded : encode {fmt} {var} = some {name} := {proof}",
                (
                    f"theorem {name}Decoded : NativePolicyCodec.decode {fmt} {name} = "
                    f"some {var} := NativePolicyCodec.encoded {name}Encoded"
                ),
            ]
        )
    pres = []

    def add(pre):
        if pre not in pres:
            pres.append(pre)
        return pres.index(pre)

    qcpre = add(b"deltareduce.008.aggregate-root-qc.v1\0" + canonical_json_bytes(doc))
    bodypre = add(b"deltareduce.vote.aggregate-root-body.v1\0" + body_bytes(doc))
    proposal = {**doc, "signer_ids": committee}
    proposalpre = add(b"deltareduce.008.aggregate-root-qc.v1\0" + canonical_json_bytes(proposal))
    cases = []
    for name, ls in [
        ("original", doc["leaves"]),
        *((f"case{n}", sample_leaves(n)) for n in range(1, 5)),
    ]:
        hashes = []
        leafpre = []
        nodes = []
        levels = []
        for item in ls:
            i = add(b"deltareduce.008.aggregate-leaf.v1\0" + canonical_json_bytes(item))
            leafpre.append(i)
            hashes.append("sha256:" + hashlib.sha256(pres[i]).hexdigest())
        level = hashes
        levels.append(level)
        while len(level) > 1:
            next_level = []
            for j in range(0, len(level), 2):
                if j + 1 == len(level):
                    next_level.append(level[j])
                    continue
                pre = (
                    b"deltareduce.008.aggregate-node.v1\0"
                    + bytes.fromhex(level[j][7:])
                    + bytes.fromhex(level[j + 1][7:])
                )
                i = add(pre)
                result = "sha256:" + hashlib.sha256(pre).hexdigest()
                nodes.append((level[j], level[j + 1], result, i))
                next_level.append(result)
            level = next_level
            levels.append(level)
        assert level[0] == (
            doc["merkle_root"] if name == "original" else observed["merkle_cases"][name[4:]]
        )
        cases.append((name, ls, leafpre, nodes, levels))
    for i, pre in enumerate(pres):
        out.append(f"def preimage{i} : Bytes := {lit(pre)}")
    expr = "NativeParameterVectors.sha raw"
    for i in reversed(range(len(pres))):
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
        "(preimage : domain ++ [0] ++ raw = pre) (hashed : sha pre = "
        "digest) (size : digest.length = 32) (spelling : "
        'NativeVoteBytes.ascii "sha256:" ++ NativeVoteBytes.hexBytes '
        "digest = expected) : NativeStateBytes.contentId sha domain raw = "
        "some expected := by simp only "
        "[NativeStateBytes.contentId,NativeStateBytes.contentPreimage,preimage,hashed,size,ite_true,spelling]"
    )
    for name, ls, leafpre, nodes, levels in cases:
        out.append(
            f"def {name}Leaves : List NativeAggregateMerkle.Leaf := ["
            + ",".join(map(leaf, ls))
            + "]"
        )
        lhs = []
        for j, (item, i) in enumerate(zip(ls, leafpre, strict=True)):
            hn = f"{name}Leaf{j}"
            lhs.append(hn)
            out.append(
                f"theorem {hn} : NativeAggregateMerkle.leafHash sha {leaf(item)} = "
                f"some {asc(levels[0][j])} := by rw "
                f"[NativeAggregateMerkle.leafHash,if_pos (by decide)]; exact "
                f"contentFromHash rfl hash{i} rfl rfl"
            )
        out.append(
            f"theorem {name}Hashes : NativeAggregateMerkle.leafHashes sha "
            f"{name}Leaves = some {strings(levels[0])} := by simp only "
            f"[{name}Leaves,NativeAggregateMerkle.leafHashes,{','.join(lhs)},bind,Option.bind]"
        )
        ns = []
        for j, (left, right, result, i) in enumerate(nodes):
            hn = f"{name}Node{j}"
            ns.append(hn)
            out.append(
                f"theorem {hn} : NativeAggregateMerkle.parentHash sha {asc(left)} "
                f"{asc(right)} = some {asc(result)} := by rw "
                f"[NativeAggregateMerkle.parentHash,show "
                f"NativeAggregateMerkle.digestBytes {asc(left)} = some "
                f"{lit(bytes.fromhex(left[7:]))} from by decide]; dsimp only "
                f"[bind,Option.bind]; rw [show NativeAggregateMerkle.digestBytes "
                f"{asc(right)} = some {lit(bytes.fromhex(right[7:]))} from by "
                f"decide]; exact contentFromHash rfl hash{i} rfl rfl"
            )
        for j in range(len(levels) - 1):
            used = [
                ns[k]
                for k, node in enumerate(nodes)
                if node[0] in levels[j] and node[1] in levels[j]
            ]
            out.append(
                f"theorem {name}Level{j} : NativeAggregateMerkle.parentLevel sha "
                f"{strings(levels[j])} = some {strings(levels[j + 1])} := by simp "
                f"only "
                f"[NativeAggregateMerkle.parentLevel,{','.join(used)},bind,Option.bind]"
            )
        reduced = (
            "NativeAggregateMerkle.noExtraSingletonHash sha _"
            if len(levels) == 1
            else "by rw ["
            + ",".join(
                [
                    f"NativeAggregateMerkle.collapseStep {name}Level{j}"
                    for j in range(len(levels) - 1)
                ]
                + ["NativeAggregateMerkle.noExtraSingletonHash"]
            )
            + "]"
        )
        out.append(
            f"theorem {name}Collapsed : NativeAggregateMerkle.collapse sha "
            f"{strings(levels[0])} = some {asc(levels[-1][0])} := "
            f"{reduced}"
        )
        out.append(
            f"theorem {name}Root : NativeAggregateMerkle.root sha {name}Leaves "
            f"= some {asc(levels[-1][0])} := "
            f"NativeAggregateMerkle.fromComponents (by decide) {name}Hashes "
            f"{name}Collapsed"
        )
    out.extend(
        [
            "def qc : Bytes := " + asc(content_id(doc)),
            "def bid : Bytes := " + asc(body_id(doc)),
            (
                f"theorem qcComputed : id sha certificate = some qc := "
                f"identityFromComponents originalRoot (by rw [exactJSON]; decide) "
                f"(contentFromHash rfl hash{qcpre} rfl rfl)"
            ),
            (
                f"theorem bodyComputed : bodyId sha certificate.common = some bid "
                f":= contentFromHash rfl hash{bodypre} rfl rfl"
            ),
            (
                "def proposal : Certificate := proposedCertificate "
                "NativeIscCertificateVectors.committee certificate.common"
            ),
            (
                "theorem proposalValid : Valid certificate.common.context "
                "NativeIscCertificateVectors.committee proposal := "
                "⟨commonValid,NativeIscCertificateVectors.valid.1,by decide⟩"
            ),
            "def proposalQc : Bytes := " + asc(content_id(proposal)),
            "def proposalJSON : Bytes := " + lit(canonical_json_bytes(proposal)),
            "theorem proposalJSONExact : json proposal = proposalJSON := by rfl",
            (
                f"theorem proposalComputed : id sha proposal = some proposalQc := "
                f"identityFromComponents originalRoot (by rw [proposalJSONExact]; "
                f"decide) (contentFromHash rfl hash{proposalpre} rfl rfl)"
            ),
            "theorem proposalFinalIdentitiesDistinct : proposalQc ≠ qc := by decide",
            "theorem proposalFinalBodySame : bodyId sha proposal.common = some bid := bodyComputed",
        ]
    )
    # The selected original PARAMETER certificate is independently rehashed and size-checked.
    steps = ",".join(["if_neg (by decide)"] * len(pres))
    out.extend(
        [
            (
                f"theorem parameterHash : sha NativeParameterVectors.preimage0 = "
                f"NativeParameterVectors.sha NativeParameterVectors.preimage0 := "
                f"by unfold sha; rw [{steps}]"
            ),
            (
                "theorem parameterBounded : NativeContractSize.contentId sha "
                "NativeParameter.domain (NativeParameter.json "
                "NativeParameterVectors.certificate) = some "
                "NativeParameterVectors.qc := NativeContractSize.fromComponents "
                "(by rw [NativeParameterVectors.exactJSON]; decide) "
                "(contentFromHash rfl (parameterHash.trans "
                "NativeParameterVectors.hash0) rfl rfl)"
            ),
            (
                "theorem shardFound : "
                "[NativeParameterVectors.finalizedEdge].find? (fun e => e.id == "
                "originalLeaf.qc) = some NativeParameterVectors.finalizedEdge := "
                "by rfl"
            ),
            (
                "theorem shardChecks : NativeAggregateLineage.ShardChecks "
                "certificate.common.context NativeIscCertificateVectors.committee "
                "[NativeParameterVectors.qc] certificate.common originalLeaf "
                "NativeParameterVectors.finalizedEdge := ⟨by "
                "decide,rfl,NativeParameterVectors.valid,rfl,rfl,rfl⟩"
            ),
            (
                "theorem shardResolved : NativeAggregateLineage.resolve sha "
                "certificate.common.context NativeIscCertificateVectors.committee "
                "[NativeParameterVectors.qc] certificate.common "
                "[NativeParameterVectors.finalizedEdge] originalLeaf = some "
                "NativeParameterVectors.finalizedEdge := "
                "NativeAggregateLineage.resolvedFromComponents shardFound "
                "shardChecks parameterBounded"
            ),
            (
                "theorem allShardsResolved : NativeAggregateLineage.resolveAll "
                "sha certificate.common.context "
                "NativeIscCertificateVectors.committee "
                "[NativeParameterVectors.qc] certificate.common "
                "[NativeParameterVectors.finalizedEdge] certificate.common.leaves "
                "= some [NativeParameterVectors.finalizedEdge] := by change "
                "(NativeAggregateLineage.resolve sha _ _ _ _ _ originalLeaf >>= "
                "fun e => some [e]) = _; rw [shardResolved]; rfl"
            ),
        ]
    )
    args = (
        "certificate.common.context NativeIscCertificateVectors.committee "
        "[NativeIscCertificateVectors.checked] [NativeIscCertificateVectors.qc] "
        "[NativeEligibilityVectors.qc] [NativePlanVectors.qc] [NativeParameterVectors.qc] "
        "certificate.common.keys [NativeEligibilityVectors.finalEdge] "
        "[NativePlanVectors.finalEdge] [NativeParameterVectors.finalizedEdge]"
    )
    for mode, cert, var, parse, qcname, hashname in [
        ("finalized", "certificate", "tree", "parsed", "qc", "qcComputed"),
        ("proposed", "proposal", "bodyTree", "bodyParsed", "proposalQc", "proposalComputed"),
    ]:
        out.extend(
            [
                f"def {mode}Edge : NativeAggregateLineage.Edge := ⟨{cert},{var},"
                + ("qc" if mode == "finalized" else "bid")
                + f",{qcname},NativeIscCertificateVectors.checked,"
                "NativeEligibilityVectors.finalEdge,NativePlanVectors.finalEdge,"
                "[NativeParameterVectors.finalizedEdge]⟩",
                (
                    f"theorem {mode}Parsed : NativeAggregateLineage.decode .{mode} "
                    f"NativeIscCertificateVectors.committee {var} = some {cert} := "
                    f""
                )
                + (
                    parse
                    if mode == "finalized"
                    else (
                        f"by simp only [NativeAggregateLineage.decode,{parse},"
                        "bind,Option.bind]; rfl"
                    )
                ),
                (
                    f"theorem {mode}Source : NativeAggregateLineage.Source sha .{mode} "
                    f"{args} {var} {mode}Edge := ⟨rfl,{mode}Parsed,by rfl,by rfl,by "
                    f"rfl,"
                )
                + ("valid" if mode == "finalized" else "proposalValid")
                + ",by decide,allShardsResolved,"
                + hashname
                + (",rfl⟩" if mode == "finalized" else ",bodyComputed⟩"),
                (
                    f"theorem {mode}Checked : NativeAggregateLineage.check sha .{mode} "
                    f"{args} {var} = some {mode}Edge := "
                    f"NativeAggregateLineage.fromComponents {mode}Source"
                ),
            ]
        )
    out.extend(negatives())
    return "\n".join([*out, "end DeltaReduce.NativeAggregateVectors", ""])


def negatives():
    return [
        (
            "theorem emptyMerkle : NativeAggregateMerkle.root sha [] = none "
            ":= NativeAggregateMerkle.invalidCount (by decide)"
        ),
        (
            "theorem malformedDigest : NativeAggregateMerkle.digestBytes "
            '(NativeVoteBytes.ascii "sha256:01") = none := by decide'
        ),
        (
            "theorem uppercaseDigestRejected : "
            "NativeAggregateMerkle.digestBytes (NativeVoteBytes.ascii "
            '"sha256:" ++ List.replicate 64 65) = none := by decide'
        ),
        "theorem oddNibbleRejected : NativeAggregateMerkle.decodeHex [48] = none := by decide",
        (
            "theorem wrongMerkleRejected : id sha {certificate with common := "
            "{certificate.common with merkle := NativeVoteBytes.ascii "
            '"wrong"}} = none := wrongMerkle originalRoot (by decide)'
        ),
        (
            "theorem duplicateLeafOrder : NativePolicyBytes.strictly "
            "NativeParameter.keyLT ((certificate.common.leaves ++ "
            "certificate.common.leaves).map NativeAggregateMerkle.key) = "
            "false := by decide"
        ),
        (
            "theorem duplicateKeyOrder : NativePolicyBytes.strictly "
            "NativeParameter.keyLT (certificate.common.keys ++ "
            "certificate.common.keys) = false := by decide"
        ),
        (
            "theorem missingShard : NativeAggregateLineage.resolve sha "
            "certificate.common.context NativeIscCertificateVectors.committee "
            "[NativeParameterVectors.qc] certificate.common [] originalLeaf = "
            "none := by rfl"
        ),
        (
            "theorem unfinalizedShard : ¬ NativeAggregateLineage.ShardChecks "
            "certificate.common.context NativeIscCertificateVectors.committee "
            "[] certificate.common originalLeaf "
            "NativeParameterVectors.finalizedEdge := by intro h; exact "
            "List.not_mem_nil h.1"
        ),
        (
            "theorem wrongLeafQc : NativeAggregateLineage.resolve sha "
            "certificate.common.context NativeIscCertificateVectors.committee "
            "[NativeParameterVectors.qc] certificate.common "
            "[NativeParameterVectors.finalizedEdge] {originalLeaf with qc := "
            'NativeVoteBytes.ascii "wrong"} = none := by rfl'
        ),
        (
            "theorem changedLeafIdentity : NativeAggregateLineage.shardLeaf "
            "NativeParameterVectors.finalizedEdge ≠ {originalLeaf with domain "
            ':= NativeVoteBytes.ascii "different"} := by decide'
        ),
        (
            "theorem emptyRequiredRejected : ¬ "
            "NativeAggregateLineage.ParentChecks "
            "[NativeIscCertificateVectors.qc] [NativeEligibilityVectors.qc] "
            "[NativePlanVectors.qc] [] certificate.common "
            "NativeIscCertificateVectors.checked "
            "NativeEligibilityVectors.finalEdge NativePlanVectors.finalEdge "
            ":= by decide"
        ),
        (
            "theorem missingPlanFinalization : ¬ "
            "NativeAggregateLineage.ParentChecks "
            "[NativeIscCertificateVectors.qc] [NativeEligibilityVectors.qc] "
            "[] certificate.common.keys certificate.common "
            "NativeIscCertificateVectors.checked "
            "NativeEligibilityVectors.finalEdge NativePlanVectors.finalEdge "
            ":= by decide"
        ),
    ]


if __name__ == "__main__":
    TARGET.write_text(generate(), encoding="utf-8", newline="\n")
