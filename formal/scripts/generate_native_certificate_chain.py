"""Compile pinned certificate components; preserve the old native semantic ID."""

import argparse
import hashlib
import re
import subprocess
from dataclasses import asdict
from pathlib import Path

import generate_native_isc_body_vectors as isc
from formal_artifacts import canonical_json_bytes, write_canonical_json
from native_certificate_chain import (
    NATIVE_SEMANTICS,
    bind_graph,
    content_id,
    merkle_root,
    voted_body,
)

ROOT = isc.ROOT
SOURCE = isc.SOURCE
TARGET = ROOT / "formal/proposals/native-certificate-chain-vectors.json"
FOLDER = ROOT / "formal/proposals/evidence/native-certificate-chain"
EXTRA = [
    "delta-core-cpp/include/delta/core/canonical.hpp",
    "delta-core-cpp/src/certificates/contracts.cpp",
]


def blobs():
    result = isc.source_blobs()
    for path in EXTRA:
        result[path] = subprocess.check_output(["git", "show", SOURCE + ":" + path], cwd=ROOT)
    return result


def fixture():
    def cid(digit):
        return "sha256:" + digit * 64

    context = asdict(isc.cases()["pinned-vote-fixture"].context)
    common = {**context, "formal_semantics_id": NATIVE_SEMANTICS, "schema_version": "1.0.0"}
    signed = {"quorum_threshold": 3, "signer_ids": ["validator-1", "validator-2", "validator-3"]}
    docs = {}

    def add(name, kind, **fields):
        doc = {**common, "type_name": kind, **fields}
        docs[name] = doc
        return content_id(doc)

    input_id = add(
        "ISC",
        "INPUT_SET_CERTIFICATE",
        input_root=cid("6"),
        tuples=[asdict(isc.cases()["pinned-vote-fixture"].tuples[0])],
        **signed,
    )
    seed_id = add(
        "SEED",
        "SEED_TRANSCRIPT",
        input_set_certificate_id=input_id,
        seed_id=cid("9"),
        seed_profile_id=cid("a"),
        share_ids=[cid("b")],
    )
    norm_id = add(
        "NORM",
        "NORM_EVIDENCE",
        entries=[{"scale_denominator": 1, "squared_norm": "1", "ticket_id": "ticket-a"}],
        input_set_certificate_id=input_id,
        norm_root=cid("c"),
    )
    ec_id = add(
        "EC",
        "ELIGIBILITY_CERTIFICATE",
        entries=[
            {
                "accepted": True,
                "domain_id": "domain-a",
                "gamma": {"denominator": 1, "numerator": "1"},
                "reason_code": "ACCEPTED",
                "ticket_id": "ticket-a",
            }
        ],
        input_set_certificate_id=input_id,
        norm_evidence_id=norm_id,
        robust_profile_id=cid("e"),
        **signed,
    )
    plan_id = add(
        "APC",
        "AGGREGATION_PLAN_CERTIFICATE",
        accumulator_proof_id=cid("f"),
        bucket_assignments=[{"bucket_id": "bucket-a", "ticket_id": "ticket-a"}],
        eligibility_certificate_id=ec_id,
        input_set_certificate_id=input_id,
        iteration_count=1,
        seed_transcript_id=seed_id,
        transcript_root=cid("0"),
        weights=[{"alpha": {"denominator": 1, "numerator": "1"}, "ticket_id": "ticket-a"}],
        **signed,
    )
    param_id = add(
        "PARAMETER",
        "PARAMETER_SHARD_QC",
        aggregation_plan_certificate_id=plan_id,
        denominator=1,
        domain_id="domain-a",
        eligibility_certificate_id=ec_id,
        input_leaf_ids=[cid("1")],
        input_set_certificate_id=input_id,
        result_numerators=["1"],
        shard_id="shard-a",
        **signed,
    )
    leaves = [{"domain_id": "domain-a", "parameter_shard_qc_id": param_id, "shard_id": "shard-a"}]
    root_id = add(
        "ROOT",
        "AGGREGATE_ROOT_QC",
        aggregation_plan_certificate_id=plan_id,
        eligibility_certificate_id=ec_id,
        input_set_certificate_id=input_id,
        leaves=leaves,
        merkle_root=merkle_root(leaves),
        required_keys=[{"domain_id": "domain-a", "shard_id": "shard-a"}],
        **signed,
    )
    store = {content_id(doc): canonical_json_bytes(doc) for doc in docs.values()}
    binding = {ec_id: seed_id}
    return docs, store, root_id, binding


def expected_components():
    docs, store, root_id, binding = fixture()
    relation = bind_graph(store, root_id, binding)
    certificates = {
        name: {"id": content_id(doc), "json_hex": canonical_json_bytes(doc).hex()}
        for name, doc in docs.items()
    }
    alternate = {**docs["ISC"], "signer_ids": ["validator-1", "validator-2", "validator-4"]}
    merkle_cases = {}
    for count in [1, 2, 3, 4]:
        leaves = [
            {
                "domain_id": "domain-a",
                "parameter_shard_qc_id": "sha256:" + str(i + 1) * 64,
                "shard_id": "shard-" + str(i),
            }
            for i in range(count)
        ]
        merkle_cases[str(count)] = merkle_root(leaves)
    return {
        "certificates": certificates,
        "bodies": {name: body["body_id"] for name, body in relation["bodies"].items()},
        "merkle_cases": merkle_cases,
        "alternate_signer_qc": content_id(alternate),
        "alternate_signer_body": voted_body(alternate)["body_id"],
        "alternate_seed_body": voted_body(docs["EC"], "sha256:" + "9" * 64)["body_id"],
        "rejections": [
            "empty-input",
            "duplicate-signer",
            "invalid-root",
            "wrong-merkle",
            "duplicate-leaf",
        ],
    }


def document():
    sources = blobs()
    _docs, store, root_id, binding = fixture()
    return {
        "version": "deltareduce.native-certificate-chain.v1-candidate",
        "source_commit": SOURCE,
        "source_sha256": {path: hashlib.sha256(raw).hexdigest() for path, raw in sources.items()},
        "provenance": "SYNTHETIC_PINNED_SOURCE_FIXTURE_NOT_NATIVE_EXPORT",
        "artifact_ascii": {key: raw.decode("ascii") for key, raw in store.items()},
        "root_id": root_id,
        "ec_seed_bindings": binding,
        "projection": bind_graph(store, root_id, binding),
        "components": expected_components(),
        "native_semantics_id": NATIVE_SEMANTICS,
        "native_export_authenticated": False,
        "gate_eligible": False,
        "scope": "CERTIFICATE_ENCODER_SHA_MERKLE_AND_VOTED_BODY_COMPONENTS_ONLY",
    }


def function(raw, name):
    source = raw.decode()
    matches = list(
        re.finditer(
            r"^(?:\[\[nodiscard\]\] )?(?:void|std::string|Vote\w+) " + re.escape(name) + r"\(",
            source,
            re.M,
        )
    )
    if len(matches) != 1:
        raise ValueError("unique native function missing: " + name)
    start = matches[0].start()
    brace = source.index("{", matches[0].end())
    end, depth = brace + 1, 1
    while depth:
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    code = source[start:end]
    return code, {
        "name": name,
        "first_line": source.count("\n", 0, start) + 1,
        "last_line": source.count("\n", 0, end) + 1,
        "sha256": hashlib.sha256(code.encode()).hexdigest(),
    }


def harness(sources):
    spans = []
    code = (
        "#include <delta/certificates/contracts.hpp>\n#include <bit>\n"
        "#include <iostream>\nnamespace delta::core::consensus {\n"
    )
    header = "delta-core-cpp/include/delta/core/consensus.hpp"
    for name in [
        "VoteInputSetBody",
        "VoteEligibilityBody",
        "VoteAggregationPlanBody",
        "VoteAggregateRootBody",
    ]:
        selected, span = isc.definition(sources[header], name, True)
        code += selected + "\n"
        spans.append({"path": header, **span})
    path = "delta-core-cpp/src/consensus.cpp"
    for name in [
        "append_hash_text",
        "append_hash_u64",
        "append_hash_bool",
        "append_hash_context",
        "append_hash_rational",
        "append_hash_input_tuples",
        "append_hash_eligibility_entries",
        "append_hash_bucket_assignments",
        "append_hash_weights",
        "append_hash_root_leaves",
        "append_hash_shard_keys",
        "authority_content_id",
        "project_input_set_vote_body",
        "project_eligibility_vote_body",
        "project_aggregation_plan_vote_body",
        "project_aggregate_root_vote_body",
        "vote_input_set_body_id",
        "vote_eligibility_body_id",
        "vote_aggregation_plan_body_id",
        "vote_aggregate_root_body_id",
    ]:
        selected, span = function(sources[path], name)
        code += selected + "\n"
        spans.append({"path": path, **span})
    code += "}\n" + HARNESS
    return code, spans


HARNESS = r"""
using namespace delta::certificates;
using namespace delta::core::consensus;
std::string id(char c) {return "sha256:"+std::string(64,c);}
template<class T> void emit(const char* name,const T& value) {
 const auto raw=canonical_json(value);const char* hex="0123456789abcdef";
 std::cout<<"CERT\t"<<name<<'\t'<<content_id(value)<<'\t';
 for(auto x:raw){auto n=std::to_integer<unsigned>(x);std::cout<<hex[n>>4]<<hex[n&15];}
 std::cout<<'\n';
}
template<class F> void rejects(const char* name,F fn) {
 try {fn();throw std::runtime_error("expected rejection missing");}
 catch(const CertificateError&) {std::cout<<"REJECT\t"<<name<<'\n';}
}
int main() {
 const Context c{id('4'),1,id('5'),id('1'),"round-vote-fixture",id('d'),0};
 const std::vector<std::string> signers{"validator-1","validator-2","validator-3"};
 const InputSetCertificate input{c,id('6'),3,signers,{{id('7'),id('8'),"domain-a","ticket-a"}}};
 const auto isc=content_id(input);
 const SeedTranscript seed{c,isc,id('9'),id('a'),{id('b')}};const auto sid=content_id(seed);
 const NormEvidence norm{c,{{1,"1","ticket-a"}},isc,id('c')};const auto nid=content_id(norm);
 const EligibilityCertificate ec{c,
 {{true,"domain-a",{1,1},"ACCEPTED","ticket-a"}},isc,nid,3,id('e'),signers};
 const auto eid=content_id(ec);
 const AggregationPlanCertificate plan{c,id('f'),{{"bucket-a","ticket-a"}},
 eid,isc,1,3,sid,signers,id('0'),{{{1,1},"ticket-a"}}};const auto pid=content_id(plan);
 const ParameterShardQc parameter{c,pid,1,"domain-a",eid,{id('1')},isc,3,
 {"1"},"shard-a",signers};const auto qid=content_id(parameter);
 const std::vector<RootLeaf> leaves{{"domain-a",qid,"shard-a"}};
 const AggregateRootQc root{c,pid,eid,isc,leaves,aggregate_merkle_root(leaves),3,
 {{"domain-a","shard-a"}},signers};
 emit("ISC",input);emit("SEED",seed);emit("NORM",norm);emit("EC",ec);
 emit("APC",plan);emit("PARAMETER",parameter);emit("ROOT",root);
 std::cout<<"BODY\tISC\t"<<vote_input_set_body_id(project_input_set_vote_body(input))<<'\n';
 std::cout<<"BODY\tEC\t"<<vote_eligibility_body_id(project_eligibility_vote_body(ec,sid))<<'\n';
 std::cout<<"BODY\tAPC\t"<<vote_aggregation_plan_body_id(project_aggregation_plan_vote_body(plan))<<'\n';
 std::cout<<"BODY\tROOT\t"<<vote_aggregate_root_body_id(project_aggregate_root_vote_body(root))<<'\n';
 auto altered=input;altered.signer_ids.back()="validator-4";
 std::cout<<"VARIANT\talternate_signer_qc\t"<<content_id(altered)<<'\n';
 std::cout<<"VARIANT\talternate_signer_body\t"
 <<vote_input_set_body_id(project_input_set_vote_body(altered))<<'\n';
 std::cout<<"VARIANT\talternate_seed_body\t"
 <<vote_eligibility_body_id(project_eligibility_vote_body(ec,id('9')))<<'\n';
 for(int n=1;n<=4;++n){std::vector<RootLeaf> more;
 for(int i=0;i<n;++i)more.push_back(
 {"domain-a",id(static_cast<char>('1'+i)),"shard-"+std::to_string(i)});
 std::cout<<"MERKLE\t"<<n<<'\t'<<aggregate_merkle_root(more)<<'\n';}
 rejects("empty-input",[&]{auto bad=input;bad.tuples.clear();static_cast<void>(content_id(bad));});
 rejects("duplicate-signer",[&]{auto bad=input;bad.signer_ids[1]=bad.signer_ids[0];
 static_cast<void>(content_id(bad));});
 rejects("invalid-root",[&]{auto bad=input;bad.input_root="invalid";
 static_cast<void>(content_id(bad));});
 rejects("wrong-merkle",[&]{auto bad=root;bad.merkle_root=id('0');
 static_cast<void>(content_id(bad));});
 rejects("duplicate-leaf",[&]{auto bad=root;bad.leaves.push_back(bad.leaves[0]);
 static_cast<void>(content_id(bad));});
}
"""


def parse_output(output):
    """Fail closed on duplicate, malformed, missing or unexpected result rows."""
    observed = {"certificates": {}, "bodies": {}, "merkle_cases": {}, "rejections": []}
    widths = {"CERT": 4, "BODY": 3, "MERKLE": 3, "VARIANT": 3, "REJECT": 2}
    seen = set()
    for line in output.splitlines():
        row = line.split("\t")
        if row[0] not in widths or len(row) != widths[row[0]]:
            raise ValueError("malformed C++ output")
        key = tuple(row[:2])
        if key in seen:
            raise ValueError("duplicate C++ output")
        seen.add(key)
        if row[0] == "CERT":
            observed["certificates"][row[1]] = {"id": row[2], "json_hex": row[3]}
        elif row[0] == "BODY":
            observed["bodies"][row[1]] = row[2]
        elif row[0] == "MERKLE":
            observed["merkle_cases"][row[1]] = row[2]
        elif row[0] == "VARIANT":
            if row[1] in observed:
                raise ValueError("C++ variant namespace collision")
            observed[row[1]] = row[2]
        else:
            observed["rejections"].append(row[1])
    if observed != expected_components():
        raise ValueError("native/Python component mismatch")
    return observed


def cross_check(vcvars):
    sources = blobs()
    build = ROOT / "formal/build/native-certificate-chain"
    build.mkdir(parents=True, exist_ok=True)
    FOLDER.mkdir(parents=True, exist_ok=True)
    for path in [
        "delta-core-cpp/include/delta/core/canonical.hpp",
        "delta-core-cpp/include/delta/certificates/contracts.hpp",
    ]:
        target = build / "include" / path.split("/include/")[1]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(sources[path])
    for path in [
        "delta-core-cpp/src/canonical.cpp",
        "delta-core-cpp/src/sha256.cpp",
        "delta-core-cpp/src/sha256.hpp",
        "delta-core-cpp/src/certificates/contracts.cpp",
    ]:
        (build / Path(path).name).write_bytes(sources[path])
    code, spans = harness(sources)
    (build / "harness.cpp").write_text(code, encoding="utf-8", newline="\n")
    cmd = (
        '@echo off\ncall "'
        + str(vcvars)
        + '" >nul\nif errorlevel 1 exit /b 1\n'
        + "cl /Bv /std:c++20 /EHsc /W4 /WX /Iinclude "
        + "harness.cpp canonical.cpp sha256.cpp contracts.cpp /Fe:chain.exe\n"
        + "exit /b %errorlevel%\n"
    )
    (build / "compile.cmd").write_text(cmd, encoding="utf-8", newline="\r\n")
    run = subprocess.run(
        ["cmd", "/d", "/c", str(build / "compile.cmd")], cwd=build, capture_output=True
    )
    log = (run.stdout + run.stderr).replace(b"\r\n", b"\n")
    (FOLDER / "compile.txt").write_bytes(log)
    if run.returncode:
        raise RuntimeError("native certificate component compile failed")
    output = subprocess.check_output([str(build / "chain.exe")], cwd=build).decode("ascii")
    observed = parse_output(output)
    compiler = re.search(rb"Optimizing Compiler Version ([0-9.]+) for x64", log)
    if not compiler:
        raise ValueError("compiler identity missing")
    (FOLDER / "harness.cpp").write_text(code, encoding="utf-8", newline="\n")
    result = {
        "status": "PASS_CERTIFICATE_COMPONENTS_NOT_FULL_RUNTIME",
        "source_commit": SOURCE,
        "source_sha256": {path: hashlib.sha256(raw).hexdigest() for path, raw in sources.items()},
        "extracted_definitions": spans,
        "unmodified_translation_units": ["canonical.cpp", "sha256.cpp", "contracts.cpp"],
        "compiler": compiler[1].decode(),
        "compiler_flags": "/Bv /std:c++20 /EHsc /W4 /WX",
        "observed": observed,
        "harness_sha256": hashlib.sha256(code.encode()).hexdigest(),
        "native_component_execution": True,
        "native_runtime_execution": False,
        "native_export_authenticated": False,
        "gate_eligible": False,
    }
    write_canonical_json(FOLDER / "cpp-cross-check.json", result)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--vcvars", type=Path)
    args = parser.parse_args()
    write_canonical_json(TARGET, document())
    if args.vcvars:
        print(cross_check(args.vcvars)["status"])
    else:
        print("GENERATED_SEPARATE_NATIVE_CERTIFICATE_CHAIN")
