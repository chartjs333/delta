#!/usr/bin/env python3
"""Generate the deterministic content-addressed FormalVerificationReport."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "formal" / "reports"
sys.path.insert(0, str(ROOT / "formal" / "scripts"))

from formal_artifacts import (  # noqa: E402
    REQUIREMENT_IDS,
    derive_formal_semantics_id,
    discover_semantic_artifacts,
    finalize_report,
    is_generated_report_output,
    load_json_strict,
    reproduction_matches_source,
    review_attestation_matches,
    sha256_file,
    source_commit_from_history,
    write_canonical_json,
)


def git(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    return result.stdout.rstrip()


def is_report_output(path: str) -> bool:
    return is_generated_report_output(path)


def verified_source_manifest_status(path: Path) -> tuple[str, str, bool]:
    """Read source identity previously verified by the offline runner."""

    manifest = load_json_strict(path)
    if not isinstance(manifest, dict) or set(manifest) != {
        "schema_version",
        "checkout_commit",
        "checkout_tree",
        "source_commit",
        "source_tree",
        "source_clean",
        "files",
    }:
        raise ValueError("verified source manifest shape mismatch")
    commit = manifest["source_commit"]
    source_tree = manifest["source_tree"]
    if (
        manifest["schema_version"] != "2.0.0"
        or manifest["source_clean"] is not True
        or not isinstance(commit, str)
        or re.fullmatch(r"[0-9a-f]{40}", commit) is None
        or not isinstance(source_tree, str)
        or re.fullmatch(r"[0-9a-f]{40}", source_tree) is None
        or not isinstance(manifest["checkout_commit"], str)
        or re.fullmatch(r"[0-9a-f]{40}", manifest["checkout_commit"]) is None
        or not isinstance(manifest["checkout_tree"], str)
        or re.fullmatch(r"[0-9a-f]{40}", manifest["checkout_tree"]) is None
        or not isinstance(manifest["files"], list)
        or not manifest["files"]
    ):
        raise ValueError("verified source manifest identity is invalid")
    return commit, source_tree, True


def source_tree_status() -> tuple[str, str, bool]:
    """Return the latest source commit and whether that source tree is clean.

    Generated machine evidence and independent review attestations are committed
    as an evidence overlay after the source tree they attest. Ignoring only those
    known outputs avoids a circular reviewed_commit while every other tracked or
    untracked path remains fail-closed.
    """

    verified_manifest = os.environ.get("FORMAL_VERIFIED_SOURCE_MANIFEST")
    if verified_manifest:
        return verified_source_manifest_status(Path(verified_manifest))

    status_lines = git("status", "--porcelain=v1", "--untracked-files=all").splitlines()
    source_changes = []
    for line in status_lines:
        path = line[3:].split(" -> ")[-1].replace("\\", "/")
        if not is_report_output(path):
            source_changes.append(line)
    commit = source_commit_from_history(ROOT)
    source_tree = git("rev-parse", f"{commit}^{{tree}}")
    if len(source_tree) != 40:
        raise RuntimeError("unable to identify the attested source Git tree")
    return commit, source_tree, not source_changes


def evidence_node(identifier: str, relative: str, media_type: str) -> dict[str, str]:
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(relative)
    return {
        "id": identifier,
        "path": relative,
        "sha256": sha256_file(path),
        "media_type": media_type,
    }


def check(identifier: str, status: str, evidence_id: str) -> dict[str, Any]:
    return {
        "id": identifier,
        "mandatory": True,
        "status": status,
        "verified": status == "PASS",
        "evidence_id": evidence_id,
    }


def main() -> int:
    commit, source_tree, source_clean = source_tree_status()
    registry = load_json_strict(REPORTS / "formal-id-registry.json")
    baseline = load_json_strict(REPORTS / "baseline-inputs.json")
    phase0_run = subprocess.run(
        [sys.executable, str(ROOT / "formal/scripts/verify_phase0.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    try:
        phase0_verified = (
            phase0_run.returncode == 0 and json.loads(phase0_run.stdout).get("status") == "PASS"
        )
    except (ValueError, AttributeError):
        phase0_verified = False
    toolchains = load_json_strict(REPORTS / "toolchain-evidence.json")
    tlc = load_json_strict(REPORTS / "tlc-evidence.json")
    lean = load_json_strict(REPORTS / "lean-proof-report.json")
    mutants = load_json_strict(REPORTS / "mutant-evidence.json")
    refinement = load_json_strict(REPORTS / "refinement-evidence.json")
    cross_artifact = load_json_strict(REPORTS / "cross-artifact-analysis.json")
    semantic_artifacts = discover_semantic_artifacts(ROOT)
    formal_semantics_id = derive_formal_semantics_id(
        registry["formal_semantics_version"], semantic_artifacts
    )
    if refinement["formal_semantics_id"] != formal_semantics_id:
        raise ValueError("refinement evidence is stale for the semantic artifact set")
    write_canonical_json(
        REPORTS / "formal-semantics.json",
        {
            "schema_version": "1.0.0",
            "formal_semantics_version": registry["formal_semantics_version"],
            "formal_semantics_id": formal_semantics_id,
            "status": "published",
            "semantic_artifacts": semantic_artifacts,
            "feature_ownership": registry["actions"],
            "refinement_module": "formal/tla/DeltaReduceRefinement.tla",
            "compatibility": registry["compatibility"],
        },
    )

    clean_reproduction_path = REPORTS / "clean-offline-reproduction.json"
    if clean_reproduction_path.is_file():
        reproduction = load_json_strict(clean_reproduction_path)
    else:
        reproduction = {
            "schema_version": "1.0.0",
            "status": "MISSING",
            "environment": "linux/amd64 clean container with --network none",
            "reason": "CLEAN_OFFLINE_REPRODUCTION_NOT_RECORDED",
            "required_task": "T062",
        }
        write_canonical_json(REPORTS / "reproducibility-evidence.json", reproduction)
    if clean_reproduction_path.is_file():
        write_canonical_json(REPORTS / "reproducibility-evidence.json", reproduction)

    nodes = [
        evidence_node(
            "EVIDENCE-TOOLCHAINS", "formal/reports/toolchain-evidence.json", "application/json"
        ),
        evidence_node("EVIDENCE-TLC", "formal/reports/tlc-evidence.json", "application/json"),
        evidence_node("EVIDENCE-LEAN", "formal/reports/lean-proof-report.json", "application/json"),
        evidence_node(
            "EVIDENCE-MUTANTS", "formal/reports/mutant-evidence.json", "application/json"
        ),
        evidence_node(
            "EVIDENCE-REFINEMENT", "formal/reports/refinement-evidence.json", "application/json"
        ),
        evidence_node(
            "EVIDENCE-CROSS-ARTIFACT",
            "formal/reports/cross-artifact-analysis.json",
            "application/json",
        ),
        evidence_node(
            "EVIDENCE-REPRODUCIBILITY",
            "formal/reports/reproducibility-evidence.json",
            "application/json",
        ),
        evidence_node(
            "EVIDENCE-SEMANTICS", "formal/reports/formal-semantics.json", "application/json"
        ),
    ]

    reviews: list[dict[str, Any]] = []
    review_directory = REPORTS / "reviews"
    if review_directory.is_dir():
        for path in sorted(review_directory.glob("*.json")):
            review = load_json_strict(path)
            if not review_attestation_matches(
                review,
                reviewed_commit=commit,
                formal_semantics_id=formal_semantics_id,
            ):
                continue
            evidence_id = f"EVIDENCE-REVIEW-{len(reviews) + 1}"
            nodes.append(
                evidence_node(
                    evidence_id,
                    path.relative_to(ROOT).as_posix(),
                    "application/json",
                )
            )
            reviews.append(
                {
                    "reviewer_id": review["reviewer_id"],
                    "independent": review["independent"],
                    "status": review["status"],
                    "scope": review["scope"],
                    "evidence_id": evidence_id,
                }
            )

    manifest_files = [
        {"path": item["path"], "sha256": item["sha256"]} for item in semantic_artifacts
    ]
    manifest_files.extend({"path": node["path"], "sha256": node["sha256"]} for node in nodes)
    manifest_files.append(
        {
            "path": "formal/reports/baseline-inputs.json",
            "sha256": sha256_file(REPORTS / "baseline-inputs.json"),
        }
    )
    by_path = {item["path"]: item for item in manifest_files}
    source_manifest = {
        "schema_version": "2.0.0",
        "commit": commit,
        "git_tree": source_tree,
        "files": [by_path[path] for path in sorted(by_path)],
    }
    manifest_path = REPORTS / "source-tree-manifest.json"
    write_canonical_json(manifest_path, source_manifest)

    model_checks: list[dict[str, Any]] = []
    for model in tlc["models"]:
        item = check(model["id"], model["status"], "EVIDENCE-TLC")
        item.update(
            {
                "kind": model["kind"],
                "states": model["states"],
                "distinct_states": model["distinct_states"],
                "diameter": model["diameter"],
                "terminal_states": model["terminal_outcome_class_count"],
                "properties": [
                    {"id": identifier, "status": "PASS"} for identifier in model["properties"]
                ],
            }
        )
        model_checks.append(item)

    theorem_checks: list[dict[str, Any]] = []
    for theorem in lean["theorems"]:
        item = check(theorem["id"], theorem["status"], "EVIDENCE-LEAN")
        item.update({"source": theorem["source"], "axioms": theorem["kernel_axioms"]})
        theorem_checks.append(item)

    mutant_checks: list[dict[str, Any]] = []
    for mutant in mutants["mutants"]:
        item = check(mutant["id"], mutant["status"], "EVIDENCE-MUTANTS")
        item["expected_property_id"] = mutant["property"]
        mutant_checks.append(item)

    refinement_check = check("REFINEMENT-SUITE", refinement["status"], "EVIDENCE-REFINEMENT")
    refinement_check.update(
        {
            "legal_fixture_count": refinement["legal_fixture_count"],
            "illegal_fixture_count": refinement["illegal_fixture_count"],
        }
    )

    toolchain_checks = [
        check(item["id"], item["status"], "EVIDENCE-TOOLCHAINS") for item in toolchains["checks"]
    ]
    reproduction_pass = reproduction_matches_source(
        reproduction,
        commit,
        formal_semantics_id,
        source_tree=source_tree,
        root=ROOT,
    )
    evidence_pass = {
        "EVIDENCE-TOOLCHAINS": all(item.get("status") == "PASS" for item in toolchains["checks"]),
        "EVIDENCE-TLC": (
            tlc.get("status") == "PASS"
            and {item["id"] for item in tlc["models"]}
            == {item["id"] for item in registry["configs"]}
            and all(item.get("status") == "PASS" for item in tlc["models"])
        ),
        "EVIDENCE-LEAN": (
            lean.get("status") == "PASS"
            and lean.get("conjunct_completeness", {}).get("status") == "PASS"
        ),
        "EVIDENCE-MUTANTS": (
            mutants.get("status") == "PASS"
            and mutants.get("mutation_scope") == "PRODUCTION_ACTION_SOURCE"
        ),
        "EVIDENCE-REFINEMENT": refinement.get("status") == "PASS",
        "EVIDENCE-CROSS-ARTIFACT": (
            cross_artifact.get("status") == "PASS"
            and cross_artifact.get("gate_kind") == "SYNTACTIC_TRACEABILITY"
            and cross_artifact.get("semantic_completeness_claimed") is False
        ),
        "EVIDENCE-REPRODUCIBILITY": reproduction_pass,
        "EVIDENCE-SEMANTICS": True,
    }

    def requirement_evidence(identifier: str) -> str:
        number = int(identifier.removeprefix("FR-"))
        if number == 1:
            return "EVIDENCE-TOOLCHAINS"
        if number == 3 or number in {40, 41, 45}:
            return "EVIDENCE-CROSS-ARTIFACT"
        if 2 <= number <= 27:
            return "EVIDENCE-TLC"
        if 28 <= number <= 33:
            return "EVIDENCE-LEAN"
        if 34 <= number <= 36:
            return "EVIDENCE-MUTANTS"
        if 37 <= number <= 39:
            return "EVIDENCE-REFINEMENT"
        if 42 <= number <= 44:
            return "EVIDENCE-REPRODUCIBILITY"
        if number == 46:
            return "EVIDENCE-SEMANTICS"
        raise ValueError(f"unmapped formal requirement: {identifier}")

    coverage = []
    for identifier in sorted(REQUIREMENT_IDS):
        evidence_id = requirement_evidence(identifier)
        status = "PASS" if evidence_pass[evidence_id] else "FAIL"
        coverage.append({"id": identifier, "status": status, "evidence_id": evidence_id})

    report: dict[str, Any] = {
        "report_schema_version": "1.0.0",
        "formal_semantics_version": registry["formal_semantics_version"],
        "formal_semantics_id": "sha256:" + "0" * 64,
        "source_tree": {
            "commit": commit,
            "manifest_path": "formal/reports/source-tree-manifest.json",
            "tree_sha256": sha256_file(manifest_path),
            "clean": source_clean,
            "semantic_artifacts": semantic_artifacts,
        },
        "baseline_inputs": {
            "path": "formal/reports/baseline-inputs.json",
            "sha256": sha256_file(REPORTS / "baseline-inputs.json"),
            "input_bundle_sha256": baseline["input_bundle_sha256"],
            "verified": phase0_verified,
        },
        "toolchains": toolchain_checks,
        "model_checks": model_checks,
        "theorem_checks": theorem_checks,
        "mutant_checks": mutant_checks,
        "refinement_checks": [refinement_check],
        "coverage": {"requirements": coverage, "unresolved": []},
        "assumptions": [
            "At most f of 3f+1 configured validators are Byzantine.",
            "Liveness assumes eventual synchrony, an honest responsive quorum and weak fairness.",
            "Certified bytes needed after ISC remain available or repair succeeds before abort.",
            "Native arithmetic snapshot provenance and certificate/projection mapping must be "
            "authenticated independently; digest equality alone does not establish that premise.",
        ],
        "abstractions": [
            "Hashes and signatures are collision-resistant unforgeable identifiers, "
            "not cryptographic implementations.",
            "Consensus arithmetic is modeled as bounded canonical integers with "
            "explicit accept or reject outcomes.",
            "Artifact transfer is modeled by exact content identity and availability state.",
        ],
        "limitations": [
            "Finite TLC scopes do not prove unbounded state-space safety.",
            "PO-AB1 typed graph uniqueness is proved for independently supplied complete "
            "stores under named canonical-codec, hash-collision, anchor/recovery and "
            "certificate premises. Its source-linked Lean byte vectors use a finite "
            "lookup decoder and synthetic trust; they do not verify a general native "
            "parser, SHA-256 or provenance. The recovery conjunct remains open, "
            "as does concrete decoder/exporter/WAL refinement.",
            "The PARAMETER row kernel proves coefficient derivation, ordered vector "
            "and coefficient-sum prefixes, exact coordinate refinement and quantum "
            "conversion over mathematical inputs. Checked typed-graph extraction now "
            "derives eligible committed Q rows, validates metadata/shape and constructs "
            "the full typed PARAMETER body. Conditional nativeParameterConversionSound "
            "additionally proves exact ordered certified-body comparison, per-domain "
            "checked conversion, INT64 output bounds, full schema placement and no extra "
            "cells. This is soundness of the checked mathematical program under the "
            "named codec/trust premises, not native canonical serialization, parser "
            "completeness or admission/availability refinement. Conversion success is "
            "not an extra PARAMETER admission precondition. Audited proof dependencies "
            "are limited to permitted propext, Quot.sound and Classical.choice.",
            "The checked APPLY kernel derives the least common denominator, validates "
            "ordered mixture product/sum prefixes, and proves optimizer operation order, "
            "full output shape/bounds and uniqueness for mathematical inputs. Its 32 "
            "INT64 oracle/Lean vectors include two pinned native-fixture input graphs; "
            "fixture authentication/conversion are evaluated by the proposal oracle. "
            "The separate native bridge now proves equality of certified bodies, converted "
            "cells and aligned rows across independently anchored stores, then constructs "
            "full typed and canonical APPLY bytes with fixed INT64 outputs. Conditional "
            "nativeApplyResultUnique also binds artifact/model/optimizer hash preimages "
            "under an explicit HashAdapter premise. Seventeen new kernel examples compare "
            "the pinned full result/bytes and encoding boundaries. Input codec/hash lookup "
            "tables remain finite/synthetic; general decoder completeness, native allocation "
            "limits, cryptographic implementations and native admission/WAL execution are "
            "not proved. nativeArithmeticRecoveryRefines remains missing.",
            "The checked recovery kernel proves sequential replay/history equivalence, "
            "exact record retention and retry/conflict behavior, with explicit scan "
            "presence/absence/unknown handling. Native arithmetic admission, receipt "
            "encoders and authenticated scan/QC provenance are adapter inputs, not "
            "discharged by this sublayer. Its 37 finite Lean examples pin three "
            "arithmetic diagnostic records; five other vote slots use synthetic empty "
            "receipt/effect bytes. No production parser/exporter/WAL run is claimed; "
            "the mandatory native recovery bridge, arbitrary snapshots and repair "
            "remain open.",
            "The native pre-WAL layer derives first PARAMETER/APPLY records and exact "
            "diagnostic command/effect/receipt bytes, proves independent-store identity "
            "and checks current pointers, role, deadline, recovery and canonical equality. "
            "Its 46 kernel examples compute three records from the anchored graph. "
            "Metadata provenance, the general replay adapter, initial-prefix relation "
            "and physical native WAL remain open; these preparation helpers do not "
            "discharge nativeArithmeticRecoveryRefines. Input decoding is still a "
            "twelve-string finite codec, with additional output hash samples only.",
            "NativeReplay instantiates arithmetic admission and exact partial encoders "
            "from independently resolved native inputs, derives complete arithmetic "
            "histories and checked APPLY current changes, and preserves original "
            "records through authenticated presence/absence recovery. Its 42 kernel "
            "examples are not full public traces: the empty-journal example renumbers "
            "only three arithmetic votes, while original pinned records retain 5/6/8. "
            "Other vote kinds, full public prefix/root projection and actual metadata/"
            "QC/scan provenance remain open; nativeArithmeticRecoveryRefines is still "
            "missing. Failed effect/receipt encoding now rejects in the proof kernel.",
            "PublicJournal adds all per-actor public vote slots, exact native arithmetic "
            "sequences 5/6/8, computed envelope-ID prefix roots and checked append "
            "observations. Its 41 kernel examples replay all eight original votes; "
            "non-arithmetic native receipts remain unprojected. Other-action admission "
            "is still an explicit premise, and the example hash adapter has 17 finite "
            "samples. This is not the full public event/state-root/exposure/QC/crash/"
            "scan lifecycle: nativeArithmeticRecoveryRefines remains OPEN. Admission-"
            "only erasure of unprojected fields is not persisted receipt evidence.",
            "PublicRecovery checks exact stage-list exposure, crash/restart readiness, "
            "historical retry and full-journal scan/replay. Twenty helpers derive "
            "actual recovered history and reject inferred absence or early output. "
            "Its 44 kernel examples use fourteen prevalidated public/native fixtures; "
            "scan authentication remains synthetic. UNKNOWN-presence and explicit "
            "incomplete scans are separately labeled mathematical cases. Full event/"
            "snapshot/state-root and global quorum exposure binding, other-action "
            "admission and production adapters remain open; the mandatory native "
            "recovery conjunct is not discharged by this conditional lifecycle layer.",
            "PublicReachability derives a replay/log invariant for every successful "
            "live-machine operation from empty initialization, including unknown "
            "append resolution, exact historical retry and blocked scans. Initial "
            "state is preserved; every sent arithmetic slot is stored and every "
            "stored arithmetic record has checked native preparation provenance. "
            "Its composed examples reuse the same synthetic fixture adapters. "
            "Authenticated full public snapshots/state roots, non-arithmetic phase/QC "
            "and global SendVoteEnvelope eligibility and concrete native adapters "
            "remain open; this invariant does not close nativeArithmeticRecoveryRefines.",
            "PublicSnapshot binds exact v1 snapshot encoding/hash preimages, independent "
            "registry provenance and native resolver metadata to first PARAMETER/APPLY "
            "events and reachable journal transitions. Its finite hash samples and "
            "synthetic export provenance are not production authentication or decoding. "
            "Legacy public state roots are still opaque: the existing checker verifies "
            "adjacency and selected stutters, while fixture roots derive from labels. "
            "A retained countercheck relabels an initial root and keeps checker PASS; "
            "this demonstrates an OPEN full-state-hash obligation, not semantic "
            "equivalence. The separate candidate full-public-state profile encodes all "
            "64 ProtocolVariables, binds source/configuration identities, recomputes "
            "preimages and replays a finite RoundConfig/crash/recovery path against "
            "production Init/TypeOK/Next and named actions in TLC. Seven rehashed "
            "invalid paths are rejected. A separately pinned native-fixture embedding "
            "checks a 132-state two-shard arithmetic path with original event times "
            "and per-actor sequences 5/6/8; three rehashed arithmetic/advance faults "
            "are rejected by production Next. The finite limit 127 is not native "
            "INT64 coverage. Native snapshot roots remain incompatible opaque labels; "
            "the mapping is not authenticated exporter or Lean history composition "
            "and does not upgrade legacy traces. "
            "Complete native quorum/exposure binding remains required; "
            "nativeArithmeticRecoveryRefines stays missing.",
            "The separate full-public-native v2 candidate checker derives nine "
            "first arithmetic vote correspondences from complete states and pinned "
            "native source fixtures, preserving original snapshot/command/receipt "
            "bytes and sequences 5/6/8. Whole-body native recomputation, current "
            "model/optimizer, context/time/readiness, vote-effect fields and modeled "
            "delivered parent-QC support are checked. Old snapshot roots are not "
            "upgraded. The source registry is explicitly synthetic; source pins "
            "and rehashed wrappers cannot establish native exporter authentication. "
            "It is a finite completed-trace correspondence, not general PARAMETER "
            "admission, unknown-durability recovery or Lean history composition. "
            "No new mandatory theorem or native authority is claimed.",
            "PublicState.lean now represents all 64 tagged finite public-state fields, "
            "checks complete canonical preimages and derives first arithmetic envelopes, "
            "all-vote sequences and original parent/actor/time metadata. The native "
            "identity map and SHA adapter remain explicit boundaries. This typed-input "
            "sublayer does not prove byte decoding, encoding injectivity, native "
            "authentication, all after-state effects or production Init/Next/QC behavior. "
            "Its source-linked full-state kernel examples use a synthetic zero semantic "
            "ID to avoid a semantic self-hash cycle; finite SHA samples are not crypto "
            "authority. It does not discharge nativeArithmeticRecoveryRefines.",
            "PublicVoteEffects computes all four PARAMETER/APPLY first-vote assignments "
            "and preserves the other sixty complete-state fields. General proofs "
            "reject hidden message/current effects and other-actor sequence changes; "
            "source-linked kernel examples reuse nine original votes and three loaded "
            "state pairs. The former extraction-only message counterexample now rejects "
            "under the composed checker. This effect-footprint proof does not establish "
            "all arithmetic/phase/QC/committee/admission guards, reachable TLA Next, "
            "native exporter provenance or physical WAL. Those relations remain to be "
            "joined; nativeArithmeticRecoveryRefines is still missing.",
            "NativeScalarProjection proves a lossless, injective numeric projection "
            "only for complete scalar-shard layouts loaded from the native schema. "
            "Multi-coordinate shards are unrepresentable in this scalar model; this "
            "does not change native admission. PublicScalarNumbers checks all computed "
            "numeric cells, event frame, sequence and full effect footprint against "
            "actual native preparation and composes known-cut journal reachability. "
            "Whole authority/parent/body/denominator/quantum identity, complete prior "
            "journal correspondence and phase/QC/exporter/recovery remain open. "
            "Small kernel cases include a body missing authority/parent that passes "
            "numeric checks, explicitly demonstrating their limited scope. No new "
            "full-state/native execution example or full recovery proof is claimed.",
            "NativeInputProjection loads complete source-bound scalar input blocks "
            "without later aggregate/result success and checks ticket-weight/domain-"
            "denominator representability. PublicArithmeticInputs constructs and "
            "compares all 23 canonical input fields, with exact configured namespaces, "
            "Q/quantum/profile/current values and checked mixture LCM. Finite symbols "
            "and limit 127 do not establish native authentication or full-width "
            "admission equivalence. Complete authority/parent/certificate bodies, "
            "prior journal contents, phase/QC/recovery and native adapters remain "
            "open; nativeArithmeticRecoveryRefines is not discharged.",
            "PublicAuthority constructs the ten-field arithmetic authority and exact "
            "ISC/seed/EC/APC parent records from checked native inputs and separately "
            "resolved primitive metadata. Keys retain complete original context, "
            "native references and ordered Q commitments; whole translated bodies "
            "are not supplied. Metadata authenticity is an explicit unresolved "
            "premise, with synthetic fixture trust; aliases are not cryptographic "
            "identity. This authority layer alone does not establish complete bodies, "
            "phase/quorum/delivery "
            "admission, prior journal correspondence and native recovery remain "
            "open. Authority construction does not discharge the recovery conjunct.",
            "PublicParameterBody constructs and compares all fifteen PARAMETER fields "
            "from actual checked native rows and the complete constructed authority. "
            "The narrow accumulator is recomputed, with a separate symmetric result "
            "guard for the supported equal-bound configuration. Wide success alone "
            "is insufficient; denominator fitting adds a projection restriction. "
            "PublicParameterJoin composes this body with original native preparation, "
            "full effect footprint and actual known-cut journal execution. UNKNOWN "
            "and APPLY are not accepted by this complete-body API. Full prior durable "
            "contents, unified alias/configuration authentication, phase/QC/global "
            "exposure and joined recovery remain unproved; nativeArithmeticRecoveryRefines "
            "is still missing. Component fixtures are not a new native execution.",
            "PublicApplyArithmetic rechecks every original certified conversion and "
            "all mixture/optimizer intermediates at the projected width, deriving "
            "native output identity by cross-width trace proofs. PublicApplyBody "
            "constructs every complete PARAMETER leaf, all twelve aggregate fields "
            "and ten APPLY fields. The separate configured checkpoint symbol must "
            "map to the computed native model hash under the existing runtime "
            "convention; configuration/identity authentication and the full current "
            "command/QC contract remain unproved. PublicApplyJoin supports both "
            "complete bodies and composes actual known-cut journal operations. "
            "Full prior durable contents, phase/QC/global exposure/current and "
            "public/native recovery remain open. No new combined full-state/native "
            "execution or mandatory recovery proof is claimed.",
            "PublicDurablePrefix checks exact actor-set coverage, original ordered "
            "sequences and historical arithmetic bodies/records before known-cut "
            "persistence. It has no accepting non-arithmetic branch; original mixed "
            "prefixes fail even with otherAuthorized=true. Source inventory confirms "
            "ISC/EC/APC/ROOT legacy body hashes are label preimages, not the distinct "
            "minimal graph artifacts or full native certificate encodings. CONFIG "
            "has a canonical round-contract projection only. Old envelopes/receipts "
            "remain unchanged. A versioned typed non-arithmetic witness and its "
            "provenance are required; this partial fail-closed gate is not full "
            "native recovery, native execution, or a discharged mandatory theorem.",
            "A separately versioned native ISC voted-body fixture checks exact binary "
            "hash payloads against ten extracted PR50 C++ definitions and unmodified "
            "native SHA source on 21 cases. The bounded proposal decoder and source "
            "witness verifier reject truncated/substituted evidence. This is native "
            "encoder/SHA component execution only, not reactor/admission/WAL/exporter "
            "execution. Empty/duplicate/invalid-ID encoding cases are not admitted "
            "votes. Public configuration, commitment/content, availability/root and "
            "closed-input authority projection remain unproved; legacy labels and "
            "receipts are not rewritten. No new Lean/TLC recovery proof or local "
            "acceptance is established by these synthetic source fixtures.",
            "The separate native certificate-chain proposal compiles unchanged PR50 "
            "canonical, SHA and certificate translation units plus extracted body "
            "projections. Seven certificate encodings/content IDs, four ISC/EC/APC/ROOT "
            "body IDs and Merkle cases match Python. Its exact parent/leaf checker "
            "requires an externally fixed root and separate EC-to-seed metadata. "
            "The old native formal semantics is retained, not upgraded to candidate "
            "authority. Synthetic signer lists and input roots are not authenticated; "
            "shape checks do not establish availability, phase/QC or arithmetic "
            "admission. This is component execution only, with no new runtime/WAL, "
            "public/Lean prefix bridge, recovery theorem or local acceptance.",
            "The native InputLedger component executes 36 ordered operations using "
            "unchanged consensus/canonical/SHA/certificate translation units. It "
            "retains exact active/frozen rows and late counts through rejection, "
            "retry and late input, and constructs a separate ISC from the complete "
            "frozen list. freeze accepts a partial permitted ticket set and does "
            "not check close policy, current availability, root preimages or "
            "native snapshot provenance. The proposal coverage/tuple checks are "
            "necessary relations only; they do not establish production CloseInput, "
            "full private-state equality, WAL or the missing recovery theorem.",
            "The native admission-snapshot component executes 66 cases against eight "
            "unchanged PR50 translation units. Exact DRC1 state bytes bind state_id; "
            "stale state, closed-body, context, sequence and readiness/deadline "
            "substitutions reject. PARAMETER/APPLY remain guarded in live/recovery. "
            "Rebound synthetic closed bodies at the same state_id and a rebound "
            "inner state_root expose the required independent snapshot-origin "
            "premise, not full-pipeline vulnerabilities. Native policy identity, "
            "complete public state/CloseInput provenance and actual WAL/recovery "
            "remain unproved. This is not authenticated export or local acceptance.",
            "The native policy/WAL proposal executes twelve unchanged PR50 translation "
            "units on isolated Windows files. Nine policy codecs, full-policy digest "
            "binding, record/retry/conflict, snapshot/reopen, eight policy changes, "
            "six injected exception cuts and corrupt files are checked across 62 "
            "observations. Canonical receipts retain exact bytes across retry and a "
            "state command; PARAMETER/APPLY still reject without append. The named "
            "pre-barrier hook actually throws before append; injected exceptions "
            "are not OS/power-loss or unknown transport-outcome qualification. "
            "Initial policy provenance, complete public state/action and Lean/native "
            "WAL refinement, general adapters and arithmetic execution remain open. "
            "These actual local non-arithmetic runs are not full Feature010 GO.",
            "The native receipt container layer proves general big-endian and sized "
            "section inversion, DVREC001 structural roundtrip/injectivity and exact "
            "receipt fields independent of operational replay. Nine unchanged native "
            "codec fixtures and 27 malformed/hash counterchecks retain actual binary "
            "outputs. The Lean structural decoder deliberately does not prove DRC1 "
            "frame semantics or ID-to-frame SHA binding; an unauthenticated container "
            "countercheck documents that gap. Codec examples for PARAMETER/APPLY "
            "are not admitted native votes. Policy/WAL/public recovery and native "
            "arithmetic authority remain open; this layer does not discharge PO-AB1.",
            "The native DRC1 vote layer reads all thirteen fixed fields and checks "
            "canonical decimals/content IDs/default text limits, deriving exact "
            "frame bytes and sequence/context/action/ID receipt binding. The ID "
            "adapter receives the exact native domain, NUL and complete frame; "
            "SHA-256 and signature/authentication are not proved. Nine original "
            "receipts use finite exact-preimage digest samples. Three unchanged "
            "native translation units execute 49 codec cases (12 accepted and "
            "37 rejected), including native-accepted unknown nonempty kind and "
            "uint64 endpoints. This is codec evidence, not arithmetic admission, "
            "native/public WAL recovery or authenticated export. Policy decoding, "
            "semantic WAL replay, source provenance, full public behavior and the "
            "mandatory recovery conjunct remain open; no formal/local GO follows.",
            "The native DRW1 Lean codec derives exact entry/checksum preimages and "
            "receipt/frame/sequence/startup-policy digest binding. Structural decoding, "
            "single-frame scan bounds and all-entry sequence checks are separate; "
            "state commands count alongside votes. Three retained native frames "
            "compose with the original ISC semantic receipt using finite hash samples. "
            "That entry layer alone establishes no full-file scan/replay, new native "
            "run, policy decoding/provenance, "
            "physical durability, SHA proof or arithmetic admission is established. "
            "Unknown outcomes and full native/public recovery remain open; this "
            "conditional byte relation does not discharge PO-AB1 or authorize GO.",
            "The complete observed-byte WAL scanner derives exact original frame "
            "order, consumed prefix and retained torn suffix, with adequate-fuel "
            "and corruption propagation proofs. All-entry sequence validation "
            "and indexed original receipt binding are separately composed. It "
            "reuses a retained two-entry native byte stream and partial-write "
            "sample, with no new native execution. Complete byte consumption "
            "does not authenticate a physical file or establish readiness, "
            "native admission/state-command/snapshot replay, SHA implementation "
            "or the full public recovery relation. PO-AB1 remains open.",
            "Concrete native COMMAND/ROUND_STATE readers now derive original "
            "canonical bytes, all fixed fields, native integer/text bounds, "
            "phase/count constraints and domain-separated hash preimages. Their "
            "composition with scanned DRW1 entries retains the original all-entry "
            "sequence, distinct from the state's transition counter. Three unchanged "
            "native translation units execute 55 codec cases, with 12 accepted and "
            "43 rejected. Unknown nonempty commands and substituted valid state roots "
            "can parse; admission/transition recomputation, effect/inner-WAL encoding, "
            "startup policy, logical time/caches/snapshots and full public recovery "
            "remain open. This is codec execution, not native arithmetic authority, "
            "a new Runtime crash run, SHA proof, independent authentication or GO.",
            "Lean arithmetic and quorum theorems do not prove cryptographic libraries, "
            "worker honesty, convergence or model quality.",
            "The cross-artifact analyzer is a syntactic traceability gate and does not "
            "establish semantic completeness, liveness non-vacuity or theorem strength.",
            "A clean offline Linux reproduction and two independent technical reviews "
            "are required before Formal GO.",
            "Candidate native arithmetic witnesses cover first-vote byte recomputation. "
            "Unbounded vector proofs, tensor/adapter/frozen-base decoding, native snapshot "
            "production/authentication, production WAL/receipt encoding and native recovery "
            "crash-cut refinement remain open. The candidate persistence harness explores "
            "one validator/fault with no concurrent current change, abstract receipt tuples "
            "and fail-closed corrupt recovery; it does not establish physical WAL behavior. "
            "The public witness now binds persisted-but-unexposed complete records and "
            "requires verified recovery for surviving unacknowledged writes. Unknown append "
            "outcomes retain null post-journal/sequence; verified absence permits fresh "
            "admission and corrupt/ambiguous scans stay blocked. First-admission rejection "
            "covers only arithmetic-result mismatch over a valid bound graph. Arbitrary "
            "admission failures, repair and complete native crash-cut refinement remain open. "
            "A passing incomplete diagnostic prefix is not a total concrete-state abstraction. "
            "Draft complete-journal receipt/retry projections "
            "are synthetic evidence, not physical durability or native conformance, "
            "under PO-AB1.",
        ],
        "review_attestations": reviews,
        "evidence_graph": {"nodes": nodes, "edges": []},
        "decision": "NO_GO",
        "decision_reasons": ["DRAFT"],
    }
    if not evidence_pass["EVIDENCE-CROSS-ARTIFACT"]:
        report["coverage"]["unresolved"].append("CROSS_ARTIFACT_ANALYSIS_FAILED")
    report["coverage"]["unresolved"].append(
        "NativeTransition reconstructs seven pinned native summary commands and exact "
        "state/effect/inner-WAL outputs; scanned-entry composition retains original "
        "bytes/sequence. It does not prove mixed runtime time/request/vote-policy/"
        "snapshot replay, independent initialization/export, full public refinement "
        "or nativeArithmeticRecoveryRefines. SHA and implementation equivalence "
        "remain explicit boundaries; 59 finite native core cases do not grant GO."
    )
    report["coverage"]["unresolved"].append(
        "NativeCommandReplay computes command-only history, request/receipt caches, "
        "clock and typed snapshot checks; mixed votes reject. Startup policy admission/DRS1 "
        "decoding, independent initialization/physical scan provenance and joined "
        "public recovery remain open. 22 local runtime cases do not grant GO."
    )
    report["coverage"]["unresolved"].append(
        "NativePolicyCodec/NativePolicyBytes implement the complete DVPOL001 "
        "structural grammar and canonical shape, with general codec inverse and "
        "injectivity. This is not startup state/certificate authority or vote "
        "admission. 51 unchanged native codec cases compare every decoded primitive; "
        "allocation equivalence, authenticated exporter, mixed recovery and "
        "nativeArithmeticRecoveryRefines remain open."
    )
    report["coverage"]["unresolved"].append(
        "NativeConfigAdmission computes startup/vote checks from complete decoded "
        "policy/state/vote bytes only for a singleton CONFIG candidate with an empty "
        "certificate graph. Successful binding derives exact sources, snapshot/context "
        "preimages, committee/deadline/current/parent/sequence and live/recovery guards. "
        "54 finite unchanged native comparisons are not general implementation "
        "equivalence. Nonempty graphs/other actions, general mixed replay, SHA/signature/export "
        "authentication and nativeArithmeticRecoveryRefines remain open."
    )
    report["coverage"]["unresolved"].append(
        "NativeConfigReplay composes computed singleton/empty-graph CONFIG admission "
        "with actual command replay, full policy identity, outer sequence, distinct "
        "request/vote caches and exact snapshot-position state. General history proofs "
        "derive both original record sources, cache uniqueness/counts and historical "
        "receipt retention. 32 unchanged native CONFIG/command WAL cases are finite "
        "execution, not all-policy/native/public recovery equivalence. Other vote "
        "kinds, DRS1 byte decoding in Lean, authenticated initialization/export/physical "
        "scan completeness, unknown outcomes/repair, full public composition and "
        "nativeArithmeticRecoveryRefines remain open. No readiness, exposure or GO "
        "follows from accepting an observed byte stream."
    )
    report["coverage"]["unresolved"].append(
        "NativeProposalAdmission checks every original CONFIG/ISC candidate "
        "and computed proposal body. Closed computed admission modes now share "
        "one general Lean replay/history fold and original ISC1/freeze2 recovery; "
        "finalized graph, full native/public recovery and physical provenance remain open. "
        "NativeInputSetBody/NativeIscAdmission derive complete proposed ISC bodies "
        "and source-bound startup/vote checks from actual policy/state/vote bytes. "
        "All tuple pairs, expected context, computed body IDs and closed-set membership "
        "are checked for one ISC candidate; finalized ISC and later graph vectors "
        "remain unsupported. 60 unchanged native comparisons retain primitive-root "
        "rebinding and same-ticket/different-commitment counterchecks: this is not "
        "ledger uniqueness, root provenance, availability or authenticated CloseInput. "
        "No new mixed ISC replay, full public relation or nativeArithmeticRecoveryRefines "
        "is claimed. SHA/source authentication, all-policy admission, finalized "
        "certificates, recovery/repair and full GO remain open."
    )
    report["coverage"]["unresolved"].append(
        "NativeIscCertificate now derives all 14 canonical ISC JSON fields and the "
        "separate QC/body content IDs from actual bounded policy-section bytes. "
        "NativeFinalizedIscSection checks every original ISC certificate, configured "
        "context/committee/quorum, ordered QC IDs and exact finalized-ID subset. "
        "This isolated section does not widen the CONFIG/ISC-proposal replay gate "
        "or check later graph vectors. Signer labels are not signature authentication; "
        "primitive root/config/ledger and exporter origin, general SHA/JSON equivalence, "
        "seed/EC/APC admission, full public/native recovery and "
        "nativeArithmeticRecoveryRefines remain open. No new native execution, "
        "physical failure claim, local acceptance PASS or formal GO is issued."
    )
    report["coverage"]["unresolved"].append(
        "NativeSeedTranscript derives exact original seed JSON/wire/content identity "
        "and computes its exact ISC QC edge. NativeSeedSection checks the whole seed "
        "vector after the actual finalized-ISC section and derives a checked original "
        "certificate witness for every seed parent. This is section composition only. "
        "A separate native decimal countercheck confirms that unchanged certificate "
        "contracts accept noncanonical -00 norms and -01 signed numerators. The "
        "62 MSVC component cases retain original bytes and distinct content IDs; "
        "NativeCertificateDecimal models the observed lexical rule and proves a "
        "canonicality counterexample, not general C++ language equivalence or a "
        "runtime fix. Norm/EC/APC admission must not assume strict decimal spelling. "
        "Whole graph admission and finalization/event provenance remain open. Primitive seed, "
        "share and profile IDs do not authenticate randomness or signatures; norm/EC/APC, "
        "full native/public recovery, physical provenance and nativeArithmeticRecoveryRefines "
        "remain open. No native runtime execution or original/local GO is claimed."
    )
    report["coverage"]["unresolved"].append(
        "NativeNormEvidence retains all original norm fields, complete wire and "
        "decimal spellings, including native accepted -00; it computes the actual "
        "ISC QC edge. NativeNormSection checks the entire original norm vector "
        "after the finalized-ISC section and derives checked parent witnesses. "
        "Norm values/root are not recomputed from Q and no norm membership rule "
        "is inferred from parent identity. Alternate root/ticket counterchecks "
        "make this limit explicit. Native spelling canonicality remains FAIL; "
        "general C++/JSON/SHA equivalence, EC/APC/full admission/recovery and "
        "source/finalization authenticity remain open. No native runtime repair, "
        "new execution, local acceptance PASS or formal GO is claimed."
        " NativeEligibility/Lineage/Section now check complete original EC membership, "
        "integer gamma, distinct QC/body IDs and actual ISC/norm/seed sections. "
        "Proposed-only norm/ISC equality is not invented for the finalized loop; "
        "the isolated guard countercheck is not a complete native exploit. "
        "Finite SHA and component vectors do not authenticate a producer or "
        "prove APC/full admission/replay or nativeArithmeticRecoveryRefines. "
        "Original norm spelling failure, Q/robust derivation and physical recovery "
        "remain open; no native repair or GO."
    )
    report["coverage"]["unresolved"].append(
        "NativePlan/Lineage/Section compute all original APC fields, distinct body/QC "
        "identities, complete accepted-ticket assignment/weight coverage and actual "
        "checked ISC/EC/seed sections. Native APC checks do not repeat EC/ISC "
        "cross-parent equality; the isolated predicate example is not an accepted "
        "whole native snapshot or exploit. Bucket/alpha/transcript/accumulator "
        "preimages, full PARAMETER/root/apply admission/replay, general codec/SHA "
        "equivalence and nativeArithmeticRecoveryRefines remain open. Finite SHA "
        "components are not authentication; no native repair, execution or GO."
    )
    report["coverage"]["unresolved"].append(
        "NativeParameter/Lineage/Section now preserve all original20-field PARAMETER "
        "JSON, signed-decimal spellings, policy/body bytes and actual checked "
        "ISC/EC/APC witnesses. Proposed assignment context/map/set, required "
        "matrix/domain and parent guards remain distinct from finalized guards. "
        "Assignment context is retained in policy but omitted from the native body "
        "hash; this is not a collision or complete exploit. Native verify_shard "
        "does not derive result/denominator/Q coverage. Body-hash samples are "
        "source-derived, not new C++ observations. Finite SHA is not authentication. "
        "Original decimal canonicality still FAILS; aggregate/APPLY/current, full "
        "admission/replay/public recovery/nativeArithmeticRecoveryRefines and "
        "general native equivalence remain open. No runtime repair or GO."
    )
    report["coverage"]["unresolved"].append(
        "NativeContractSize/NativeSizedParameterSection add the original inclusive "
        "4MiB canonical-certificate-JSON guard, independently of policy wire bounds. "
        "Four fresh unchanged native NormEvidence component cases confirm exact "
        "limit-1/limit/limit+1 outcomes; native already enforces this bound. Prior "
        "raw certificate helpers omit it and remain lower layers. The new entry "
        "point constructs and checks every payload in nine existing ISC/norm/seed/"
        "EC/APC/PARAMETER groups, retaining original identities and records. "
        "This is not full policy/runtime execution, error-order/resource equivalence, "
        "native authentication, complete ROOT/APPLY/current or recovery refinement. "
        "Decimal canonicality and nativeArithmeticRecoveryRefines remain open; "
        "no runtime repair, local PASS or formal GO."
    )
    report["coverage"]["unresolved"].append(
        "NativeAggregateMerkle/Root/Lineage/Section compute the original odd-carry "
        "Merkle tree and all18-field ROOT JSON/body identities; exact ordered "
        "finalized PARAMETER coverage and three parents are checked in both modes. "
        "The actual bounded prior section executes, ROOT certificates also check "
        "the4MiB JSON guard, and original lists/provenance are retained. Original "
        "ROOT and four retained native Merkle components are reused; no fresh "
        "native/runtime run, TLA run or production mutant. Finite SHA is not "
        "authentication, and strict decoding is scoped to generated lowercase IDs. "
        "APPLY/current, complete shared admission/replay, source arithmetic and "
        "general native/public recovery refinement remain open. Native decimal "
        "canonicality still fails; no runtime repair, local PASS or formal GO."
    )
    report["coverage"]["unresolved"].append(
        "NativeApplyProfile/Certificate/Lineage/Section compute complete original "
        "profile/candidate/QC canonical JSON and bounded IDs, resolve actual "
        "finalized ROOT/profile/current-parent and compose the checked ROOT section. "
        "Original rational wire bits and signed decimal spellings are retained. "
        "Both modes check certified candidate/next hashes and structural signers; "
        "the finalized example is synthetic from the native proposed-QC rule, "
        "not an observed finalized QC. Source vectors reuse original policy bytes; "
        "no fresh native run. This source snapshot relation does not recompute "
        "next values or compare parent optimizer with current optimizer; explicit "
        "counterchecks keep these arithmetic/current joins open. Full shared "
        "admission/replay, current command, public/native recovery, physical WAL, "
        "provenance and native decimal canonicality remain unresolved. No local "
        "PASS, independent review, runtime repair, guard change or formal GO."
    )
    report["coverage"]["unresolved"].append(
        "NativeFailurePayload/Section retain complete original timeout/view/abort "
        "snapshot trees, exact binary body hashes and every abort current field "
        "and all seven finalized lists, composing actual NativeApplySection. "
        "Strict tuple/computed-ID order and request reasons are checked. Original "
        "VIEW/ABORT policy components are pinned, with two finite SHA samples; "
        "no fresh native observation. This snapshot subrelation does not prove "
        "candidate timeout authority, no-overflow view increment, empty finalized "
        "APPLY for selected ABORT, live/replay phase/deadlines/readiness, QC or "
        "current transitions. Full shared admission, source arithmetic, physical "
        "WAL, provenance and native/public recovery remain open. Native decimal "
        "canonicality still fails. No runtime repair, local PASS or formal GO."
    )
    report["coverage"]["unresolved"].append(
        "NativeFailureAuthority/Vote additionally compute original selected VIEW/ABORT "
        "contexts, all15 parent slots, actual body/timeout membership, no-overflow "
        "view increment and empty finalized APPLY for ABORT. Actual candidate selection "
        "and original bounded policy/state/vote decoding compose the prior section; "
        "live/replay identities, phase, request/deadline, readiness, invalidation "
        "and sequence checks retain the original vote bytes. This is a selected "
        "subrelation, not complete shared policy admission or journal retry/recovery. "
        "The prior timeout/request Label predicate was too restrictive: actual native "
        "require_id only rejects empty IDs, and the policy wire separately bounds "
        "printable text to4096 bytes. That formal predicate is corrected to WireId; "
        "other existing header/certificate restrictions require separate review. "
        "Four finite SHA samples and original VIEW/ABORT components are reused; "
        "no fresh native execution, whole fromBytes fixture or authenticated exporter. "
        "Runtime facts and SHA remain explicit boundaries. Shared configuration/all "
        "candidate validation, current transition, actual source arithmetic, physical "
        "WAL and full public/native recovery remain open. Native decimal canonicality "
        "still fails; no runtime repair, local PASS, independent review or formal GO."
    )
    report["coverage"]["unresolved"].append(
        "NativeCandidateShape/Authority now check all15 parent slots and all9 native "
        "candidate authorities on the SAME computed shared original snapshot. Exact "
        "first body/parent lookups, finalized membership, contexts and coordinates "
        "retain original candidate count/order; PARAMETER context stays its assignment. "
        "One original CONFIG full snapshot/candidate byte-wrapper example is checked; "
        "other original row examples use an explicitly synthetic mixed component "
        "snapshot, not a new complete native policy execution. Source arithmetic, "
        "current command, retry/unknown/recovery, physical "
        "WAL, general SHA/exporter authentication, freeze and independent review "
        "remain open. Native decimal canonicality still fails. No local PASS or GO."
    )
    report["coverage"]["unresolved"].append(
        "NativeProposedIsc/SnapshotBase now derive every proposed ISC certificate "
        "from its original body and full configured committee, enforcing its separate "
        "4MiB JSON hash bound, original closed-body identity and exact config/accumulator "
        "base checks. The executable wrapper composes all existing typed snapshot "
        "sections on the original policy/state. Configured unused validators need "
        "only nonempty IDs; actual certificate signers retain Label checks, and the "
        "expected round Label remains required by the ChainVerifier constructor. "
        "This corrects a formal overrestriction, not native runtime code. Original "
        "ISC/base components and one newly derived finite SHA sample are checked; "
        "no new whole snapshot wrapper fixture or native observation. Full candidate "
        "admission, current command, native arithmetic, journal retry/unknown/recovery, "
        "physical WAL, SHA/exporter authentication, freeze and independent review "
        "remain open. Native decimal canonicality still fails. No local PASS or GO."
    )
    report["coverage"]["unresolved"].append(
        "NativeSelectedVote composes all original policy/snapshot/candidate checks "
        "with first original VOTE selection, exact identities/current/sequence, "
        "phase and deadline/request guards. Current PARAMETER/APPLY admission "
        "remains rejected in live and recovery modes; recovery bypasses only readiness. "
        "Historical retry is a different earlier native branch, not this fresh/scan "
        "predicate. One original CONFIG full byte wrapper and seven component action "
        "checks pass; no new nonempty mixed-policy wrapper or native execution. "
        "A signature substitution still passes syntactic checks and demonstrates "
        "missing authentication. Runtime facts/provenance, CurrentPointerCommand, "
        "source arithmetic, physical WAL and joined retry/unknown/recovery, full "
        "public refinement, decimal compatibility, freeze/offline/independent review "
        "remain open. No native guard change, local PASS or GO."
    )
    report["coverage"]["unresolved"].append(
        "NativeWholeReplay adds a closed computed whole-policy mode to the existing "
        "mixed WAL fold. Startup and each recovered vote use actual decoded original "
        "policy/state and every candidate; runtime tick/invalidation/global sequence "
        "come from the executed prefix. The complete original CONFIG/ISC policy with "
        "nonempty ISC body, original ISC1/freeze2 records, caches and exact historical "
        "vote/command retries now compose in Lean using eleven finite SHA samples. "
        "Duplicates, altered policy IDs, reordered positions and invalidated fresh "
        "votes reject. Current PARAMETER/APPLY guard remains; this cannot discharge "
        "arithmetic recovery by vacuity. The byte scan composition is conditional on "
        "its computed scan and does not authenticate physical completeness/durability. "
        "No fresh native/TLC/mutant run. CurrentPointerCommand, source arithmetic, "
        "full public/native refinement, unknown/repair/arbitrary snapshots, physical "
        "WAL, SHA/exporter/signatures, decimal compatibility, freeze/offline and "
        "independent reviews remain open. No local PASS, runtime change or GO."
    )
    report["coverage"]["unresolved"].append(
        "NativeCurrentPointer computes all14 original command fields, bounded IDs, "
        "actual ApplyQC relationships and replay-before-CAS. Its separate finalized "
        "bridge executes the original APPLY section, but the low-level store only "
        "checks structural signer shape. NativePointerWal models the distinct text "
        "journal, complete line checks, retained torn suffix, computed history and "
        "known cuts. Unknown is not a known empty log. Four finite SHA samples use "
        "original008 golden contracts and synthetic source-derived WAL, no native "
        "execution. Unconfigured signer shape and rehashed unauthenticated recovery "
        "counterchecks expose unresolved caller/physical provenance. Full arithmetic "
        "admission/recovery, public phase/QC/current, physical WAL/SHA/exporter, "
        "decimal compatibility, contract freeze/offline/independent reviews remain "
        "required; no runtime change, local PASS or GO."
    )
    report["coverage"]["unresolved"].append(
        "NativeApplyResult computes complete value spellings and four value hashes "
        "from actual bound NativeApply results and parent vectors, compares shared "
        "context/profile and all ordered numeric ROOT leaves, then joins the "
        "original APPLY snapshot and fresh pointer record. This is a partial "
        "relation: configuration/schema/profile-proof and ISC/EC/APC/Q-artifact "
        "identity bridges to the draft graph remain open. No new accepted full "
        "source-join fixture. Three finite SHA samples and existing kernel graph "
        "use a synthetic constructed candidate. Original008 golden output IDs "
        "hash fixture labels, not displayed coordinates; their bytes are retained "
        "and mismatch evidence is explicit. Decimal -00/-01 compatibility still "
        "fails. General native/public admission/recovery, physical WAL, SHA/exporter, "
        "freeze/offline and independent review remain required. No runtime change "
        "or local PASS/GO."
    )
    report["coverage"]["unresolved"].append(
        "Original Q-source tooling resolves exact source004 schema/profile/config/"
        "scale/plan/proof preimages and five DRQ1 leaves, derives complete ranges, "
        "quanta and36 coordinates, and preserves all original bytes. This is a "
        "bounded Python content relation, not native execution or authentication. "
        "Original008 references16 unavailable source identities, including12 "
        "label-hashed input leaves, within the retained fixture store. Replacing "
        "those IDs is not original provenance. Accumulator proof authority, "
        "draft-graph identity and full native/public admission/recovery remain open. "
        "No new Lean proof, runtime change, local PASS or GO."
    )
    report["coverage"]["unresolved"].append(
        "Original accumulator-source tooling now recomputes exact004 product, "
        "prefix, final and separate product/accumulator widths from original "
        "proof/config/profile bytes and composes with all original Q preimages. "
        "Final-minus-prefix reconstructs the unique admissible headroom; that "
        "field is absent from serialized proof bytes and actual native request "
        "provenance is not established. Historical formal/Lean IDs and theorem "
        "names are metadata matches, not current authority. The exact positive "
        "denominator is retained but its certified ticket-weight link is open. "
        "Original008 profile/proof resolution rejects the missing accumulator "
        "preimage; a separately synthetic replacement cannot authenticate it. "
        "Worker quantization and APPLY rounding are separate stages; apply "
        "quantum is absent from that original profile. No new Lean proof, native "
        "run, source-to-draft graph admission/recovery, local PASS or GO."
    )
    report["coverage"]["unresolved"].append(
        "NativeAccumulatorBytes/Binding now decode complete original004 config/proof "
        "bytes and the exact immutable worker profile, recompute product/prefix and "
        "separate product/accumulator widths, and compose their actual hash/metadata "
        "edges with the complete manifest corpus. General signed product/prefix "
        "bounds retain explicit actual coefficient/Q/count premises. F-S is the "
        "unique admissible headroom, not a serialized native-call observation. "
        "Exact denominator is not a proof of certified weight divisibility. "
        "Kernel component examples use original config/proof bytes and three "
        "SYNTHETIC exact-preimage hashes, not verified SHA or native/exporter "
        "authentication; no new combined whole-corpus execution example. Missing "
        "base/parent/008proof preimages, source-to-draft vectors/weights/current/"
        "optimizer/APPLY, general native/public recovery, certificate decimal "
        "failure, hash/codecs/WAL, contract freeze/offline and independent review "
        "remain open. This does not discharge nativeArithmeticRecoveryRefines, "
        "authorize runtime changes or issue local PASS/GO."
    )

    report["coverage"]["unresolved"].append(
        "NativeAvailableQ/NativePlanQCorpus now execute complete original APC and Q "
        "corpus loaders, check exact original tuple/schema/proof/config and native "
        "typed availability primitives against all manifest leaves, then derive "
        "product/domain-prefix bounds from actual signed16 coordinate lookups. "
        "No assumed Q bound or decoded whole-corpus input is accepted. Primitive "
        "permission/observations are UNAUTHENTICATED_COMPONENT_INPUT, not decoded "
        "native commitment/AC preimages, signatures or physical availability. "
        "The commitment/manifest identity gap, original missing008 proof and full "
        "source-to-draft byte graph/current/APPLY/recovery "
        "remain open. Component examples reuse original blocks and prior native "
        "observations; no new whole-policy/corpus execution or native run is claimed."
    )

    report["coverage"]["unresolved"].append(
        "NativeVectorLayout/Artifacts/Join now construct complete original-derived "
        "draft SCHEMA/Q_SHARD bytes with checked coordinate naming/coverage and "
        "original vector values, then load exact bytes through real LoadedRow/RowsBound "
        "and invoke actual deriveParameter. General theorems derive numerator identity "
        "from the checked computations and compose original coefficient coordinates. "
        "The source entry loads original bytes; hash/codec and draft Binding authority "
        "remain explicit unproved boundaries. This joins one selected assignment; "
        "no full-batch byte cap, full original authority/current/APPLY provenance, "
        "whole-source kernel execution, native run or recovery theorem is claimed. "
        "Source primitives, missing008 proof/current, hash/codecs/exporter/WAL, "
        "certificate decimal failure, freeze/offline and independent reviews remain "
        "open. No runtime authority or local PASS/GO."
    )

    report["coverage"]["unresolved"].append(
        "NativePlanMembers/NativePlanCoefficients now execute original policy/state "
        "decoding and complete finalized APC/ISC/EC/norm/seed membership joins, then "
        "load the actual APC-referenced config/proof and derive final alpha coefficients "
        "from its specific denominator. General divisibility/product/domain-prefix "
        "proofs retain actual Q-value bounds as explicit premises; zero weights count "
        "and EC gamma is not multiplied again. Cross-parent and global-count guards "
        "are stronger sufficient projection restrictions, not native admission "
        "equivalence. Original008's missing proof stays missing; reused original "
        "components and separate synthetic row examples are not a new whole-policy "
        "execution, native run or authenticated authority. Full Q/source-to-draft, "
        "availability, current/model/optimizer/APPLY, physical WAL/general recovery, "
        "certificate decimal compatibility, freeze/offline/reviews remain open. "
        "nativeArithmeticRecoveryRefines is not discharged; no runtime/local PASS/GO."
    )

    report["coverage"]["unresolved"].append(
        "Original APC weight tooling now resolves complete ISC/EC/seed/norm/APC "
        "bytes, retains exact eligible ticket/domain/commitment/bucket membership, "
        "and derives coefficients from final APC alpha using its actual proof's "
        "specific denominator. Divisibility, coefficient and global count bounds "
        "including zero weights, schema/base-config identity and per-domain "
        "worst absolute prefixes are checked. EC gamma is not multiplied again. "
        "The original observed APC still has an unavailable proof preimage; its "
        "complete numeric join rejects. A separate versioned synthetic example "
        "does not authenticate original history. Primitive EC-seed metadata, "
        "signers/finality, commitment/availability/Q preimages, original-to-draft "
        "identity and general admission/recovery remain open. No new Lean proof, "
        "native execution, runtime change, local PASS or GO."
    )
    report["coverage"]["unresolved"].append(
        "Original available-Q tooling derives the exact native lexicographic "
        "leaf set from every original004 manifest/DRQ1 preimage and joins all "
        "eligible APC rows by original ticket/domain/commitment/AC/proof/config "
        "identity. A separate synthetic APC uses the original004 Q bytes. "
        "Seventeen fresh unchanged native InputLedger component cases agree "
        "on first-insert/freeze checks; the component accepts a consistent but "
        "incomplete caller-selected required list, which the Q source relation "
        "rejects. Native empty lists reject. Opaque commitment/AC IDs are not "
        "derived from manifest preimages or authenticated signatures here; "
        "that counterexample remains visible. The new observation envelope "
        "explicitly permits only unauthenticated component input. This is not "
        "a native exporter, complete ledger history, WAL/runtime execution or "
        "source-to-draft/full public recovery theorem. No new Lean proof, "
        "production mutant, runtime change, local PASS or GO."
    )
    report["coverage"]["unresolved"].append(
        "Original vector-input projection now derives complete draft SCHEMA/Q "
        "artifacts and APC-weighted vector assignments from checked original "
        "preimages, with explicit flat-coordinate naming/range restrictions. "
        "It preserves vector widths, original quanta, specific denominator, all "
        "eligible tickets and separate product/prefix bounds, then compares the "
        "derived inputs with an independently supplied draft Witness graph. "
        "Rehashed valid but changed Q/schema/weight inputs reject. The retained "
        "examples use original004 Q with a synthetic APC/draft authority and a "
        "separate multi-ticket graph; neither authenticates original history. "
        "Original current vectors, full APPLY profile, vote contexts, deadline, "
        "parent-certificate projection and producer/config/exporter provenance "
        "remain independent unresolved relations. Counterchecks changing current "
        "model or learning rate pass this INPUT-ONLY layer. No new Lean proof, "
        "native execution, TLA scalar representability, runtime change or GO."
    )
    report["coverage"]["unresolved"].append(
        "Original DRQ1 framing and ordered signed INT16 payloads now have a "
        "general Lean decoder relation, length/range/position and frame "
        "roundtrip proofs. Five pinned original004 blocks retain all36 "
        "coordinates and exact header/payload bytes. In that framing-only layer "
        "the header remains opaque; "
        "JSON/canonical field interpretation, payload SHA and source authentication "
        "are NOT established. Kernel counterchecks accept non-JSON header bytes "
        "and a changed payload with an unchanged original SHA header, showing "
        "this is not native shard admission. The separate existing Python source "
        "checker rejects the hash mismatch. Connecting decoded original vectors "
        "to source metadata, NativeBinding.LoadedRow and general admission/recovery "
        "remains mandatory. No native execution, runtime change, local PASS or GO."
    )
    report["coverage"]["unresolved"].append(
        "The subsequent mandatory Lean NativeQJson/NativeQHeader decoder now "
        "parses actual original004 canonical header bytes with all16 fixed "
        "fields, unsigned decimal/token/content-ID syntax and original "
        "semantics/profile checks. General proofs retain ordered fields and "
        "exact preimages, numeric bounds, roundtrip/uniqueness and join the "
        "parsed count to actual decoded INT16 vectors. All five original "
        "blocks/36coordinates compose in the kernel; non-JSON headers reject. "
        "This is fixed-schema unescaped ASCII JSON, not a general JSON or "
        "native machine-memory proof. Payload SHA, leaf/manifest identity, "
        "independent expected-header/source/exporter authority, plan/quantum/"
        "weights and LoadedRow/RowsBound/DerivedParameter composition remain "
        "OPEN. A changed payload with its old SHA header still passes this "
        "Lean join and fails the separate Python source checker. No full "
        "native recovery theorem, native execution, runtime change, GO or "
        "independent attestation is claimed."
    )
    report["coverage"]["unresolved"].append(
        "Original scale-table nested JSON now has mandatory Lean byte decoding "
        "and exact canonical preimage/list retention. Parsed segment ranges "
        "and positive reduced uint32 quanta compose with all five original "
        "DRQ1 header/vector decodes and all36 coordinates. General lemmas "
        "retain actual source segment membership, offset+count bounds and "
        "coordinate placement. The scale identity check still takes an "
        "UNVERIFIED hash adapter; its fixture is a one-preimage synthetic map, "
        "not SHA256 or native exporter authentication. Internal scale layout "
        "does not establish referenced schema/plan/manifest/proof/APC authority. "
        "A changed payload with its old SHA header still passes this Lean "
        "quantum join and fails the Python hash checker. Source-to-draft "
        "LoadedRow/RowsBound/DerivedParameter, original current/APPLY identity "
        "and general nativeArithmeticRecoveryRefines remain OPEN. No native "
        "execution, runtime change, local PASS, GO or independent attestation."
    )
    report["coverage"]["unresolved"].append(
        "Original parameter-schema bytes now have a mandatory Lean nested "
        "decoder preserving all parameters, shapes, trainable flags and aliases. "
        "Checked dimensions/omission/order/alias-owner rules derive the exact "
        "complete scale-segment list and prefix offsets. All five original Q "
        "blocks compose with this schema/scale/header/vector relation. The "
        "schema hash preimage has no domain/NUL; scale identity retains its "
        "separate domain. Both still use an UNVERIFIED adapter whose fixture "
        "recognizes two preimages, not a proved SHA implementation or source "
        "authentication. Original shard-plan/manifest coverage, configuration/"
        "proof/APC authority, source-to-draft LoadedRow/RowsBound/DerivedParameter "
        "and full nativeArithmeticRecoveryRefines remain OPEN. Changed Q with "
        "its old SHA header still passes this Lean relation and fails Python "
        "PAYLOAD_HASH. No native execution, runtime change, local PASS or GO."
    )
    report["coverage"]["unresolved"].append(
        "Original004 shard-plan bytes now have a mandatory Lean decoder and "
        "a computed greedy partition from the decoded complete schema. General "
        "coverage/nonoverlap/order/count/payload proofs and exact ordered entry "
        "comparison bind all five original Q blocks to their precise plan slots. "
        "The three-preimage fixture hash adapter remains SYNTHETIC/UNVERIFIED. "
        "Complete manifest/corpus availability, config/proof authority, SHA, "
        "source-to-draft arithmetic composition and native recovery remain OPEN. "
        "A changed Q with its old payload hash still passes this Lean relation. "
        "No native execution, guard change, local PASS, GO or attestation."
    )
    report["coverage"]["unresolved"].append(
        "The newest original004 manifest layer supersedes the earlier per-Q "
        "coverage gap: it decodes all18 fields and ordered8-field refs, binds the "
        "entire actual Q corpus to the computed plan, derives complete headers "
        "and exact byte/coordinate totals, and checks ordered Merkle recurrence "
        "over raw32-byte digests with odd-tail duplication. All five original "
        "blocks compose. The hash function remains UNVERIFIED; finite exact "
        "preimage fixtures are synthetic witnesses, not SHA or source authority. "
        "Configuration/proof/parent/availability authentication, general native "
        "resource/codec equivalence, source-to-draft arithmetic and complete "
        "nativeArithmeticRecoveryRefines remain OPEN. No runtime change, native "
        "execution, local PASS, GO or independent attestation is claimed."
    )
    report["coverage"]["unresolved"].append(
        "Whole original008 policy/state to ISC/norm/seed/EC/APC membership now "
        "has a mandatory kernel composition over retained raw5849/674-byte "
        "inputs. Exact source lists and parent identities compose; finite SHA "
        "samples remain synthetic. The required original008 accumulator proof "
        "is still missing. General refusal propagates absent or wrong-ID proof "
        "inputs through Q corpus/context and NativeVectorJoin.run, even with "
        "a valid separate draft Binding. The concrete case rejects original004 "
        "proof substitution. This is not a successful full vector join or full "
        "phase/candidate/current/WAL admission; later PARAMETER data is retained "
        "but not checked by plan preparation. No source authentication, runtime "
        "guard change, local PASS, GO or independent attestation is claimed."
    )
    report["coverage"]["unresolved"].append(
        "A separately versioned SYNTHETIC raw policy/state now composes actual "
        "ISC/norm/seed/EC/APC sections, original004 proof/config/profile and the "
        "complete five-block Q corpus through NativeVectorContext.bind. All36 "
        "coordinates are checked from loaded source rows. Thirty finite SHA "
        "samples, inner root, availability and certificate metadata remain "
        "synthetic/unauthenticated. The grammar-required STRUCTURAL-ONLY "
        "candidate is NOT admitted; its body/parents are not supplied by this "
        "source-section proof. Original008 proof is not repaired. The full "
        "NativeVectorJoin.run source prefix reaches the remaining draft join, "
        "but no complete draft Binding/current/APPLY/recovery execution is "
        "instantiated. General codecs/hash/exporter, phase/QC/journal/WAL, "
        "arbitrary snapshots and nativeArithmeticRecoveryRefines remain OPEN. "
        "No runtime change, native execution, local PASS, GO or attestation."
    )
    report["coverage"]["unresolved"].append(
        "General constructive vector derivation now proves that resolved payloads, "
        "full checked frame/rows and the original vector reduction imply actual "
        "draft PARAMETER extraction, complete join and raw run. No expected "
        "numerators/body or successful draft derive equation is supplied. Exact "
        "ordered generated Q bytes/leaf references and contribution weights "
        "are retained; missing leaves and mismatched decoded quantum cannot "
        "bypass the actual image loader. These are GENERAL CONDITIONAL proofs, "
        "not a newly instantiated full synthetic/native raw execution. Original "
        "source-to-draft configuration/context/current/profile identity, anchor "
        "and codec/exporter authentication, APPLY and complete recovery remain "
        "OPEN. nativeArithmeticRecoveryRefines is missing; no runtime guard, "
        "local PASS, GO or independent attestation is authorized."
    )
    report["coverage"]["unresolved"].append(
        "Original vector authority checking now derives source policy/state context "
        "and full membership, executes original PARAMETER proposal lineage, checks "
        "the complete assignment matrix and whole original body coverage, and "
        "compares the selected proposal numerators/Q leaf list against actual "
        "source computations. Vote context is checked separately from body hashes; "
        "original decimal strings and contribution order are retained. No new "
        "complete raw/native run is instantiated. Draft/native artifact mapping, "
        "all original commitments, current vectors/APPLY profile, concrete "
        "authentication and full recovery remain OPEN. Native negative-zero "
        "compatibility and the explicit shard-label projection restriction remain. "
        "No runtime guard, local PASS, GO or independent attestation is authorized."
    )
    report["coverage"]["unresolved"].append(
        "Complete ISC projection now loads every original member manifest, including "
        "rejected members, and derives canonical ISC/EC payloads and all Q references. "
        "Eligible manifests must exactly match the actual arithmetic corpus; the "
        "checker resolves computed bytes in the store and joins the same checked "
        "PARAMETER frame. An existing raw one-member fixture instantiates the complete "
        "source corpus, not a new full native/draft Binding or joined execution. "
        "At this ISC-only layer, source-derived PLAN/APC, shard naming authority, "
        "current vectors/APPLY "
        "profile and authentication of original commitment/availability observations "
        "remain OPEN. Hash/codec/exporter and full-batch resource boundaries, native "
        "decimal compatibility and full nativeArithmeticRecoveryRefines remain "
        "unproved. No runtime guard, local PASS, GO or independent attestation."
    )
    report["coverage"]["unresolved"].append(
        "Complete PLAN/APC construction now retains original prepared PARAMETER "
        "contexts, finalized APC rational weights, complete domain/shard/member "
        "coverage and decoded Q quantum. Sized original section checks apply. "
        "Computed canonical PLAN/APC resolve in the actual store; the joined "
        "checker derives all five FrameOrigin records for the same checked frame. "
        "The APPLY profile reference remains an explicit shape-checked primitive, "
        "not an authenticated profile preimage. Ordinal naming and ASCII context "
        "restrictions are not general native admission equivalence. Small encoding "
        "and source-component cases do not instantiate a complete original/draft "
        "Binding or execution. Current vectors/profile, commitment authority, "
        "general codec/hash/exporter/resource bounds, native decimal compatibility "
        "and full nativeArithmeticRecoveryRefines remain OPEN. No runtime guard, "
        "local PASS, GO or independent attestation is authorized."
    )
    report["coverage"]["unresolved"].append(
        "Current-value source checking now joins every observed pointer-WAL record "
        "to original decoded policy/state, a selected finalized APPLY certificate "
        "and exact candidate decimal preimages with computed native value hashes. "
        "Ordered complete evidence, adjacent parent model/optimizer and final "
        "state are derived from executions. Unknown, empty history and missing "
        "evidence cannot invent current vectors. This is a stronger candidate "
        "checker, not existing native recovery equivalence or authenticated "
        "historical reachability. Native -00/-01 compatibility still fails. "
        "Initial/current authority, schema/quantum/profile artifact mapping, "
        "complete original/draft Binding, physical observation/WAL/repair, "
        "concrete hash/codec/exporter and full nativeArithmeticRecoveryRefines "
        "remain OPEN. Small reused synthetic components do not instantiate a "
        "complete checked history or native execution. No runtime/local PASS/GO."
    )
    report["coverage"]["unresolved"].append(
        "Complete draft PROFILE/MODEL/OPTIMIZER bytes now derive from an actual "
        "source-policy APPLY profile, checked accumulator width, recovered "
        "original current values and the existing complete SCHEMA/PLAN/ISC/EC/APC "
        "graph. All new artifact store bytes/hash/length/payloads are checked. "
        "Quantum remains a named UnitSource primitive keyed by original context, "
        "APC/profile/proof and complete current pointer; absent metadata rejects. "
        "The same original numeric profile admits two distinct quanta, so its "
        "bytes alone cannot determine the complete draft profile. Source metadata "
        "authentication, configured profile selection, initial/current authority, "
        "complete Binding/authority walks, concrete codecs/hash/exporter and full "
        "nativeArithmeticRecoveryRefines remain OPEN. Small encoding cases are "
        "not a full history/preparation execution or authenticated UnitSource. "
        "No runtime guard, local PASS, GO or independent attestation follows."
    )
    report["coverage"]["unresolved"].append(
        "The full AUTHORITY root is now computed from checked original context "
        "and all eight projected artifact references. Executable finite-depth "
        "store traversal derives recursive Complete and ordered paths; no "
        "caller-supplied graph-completeness proof is consumed. A pre-aggregate "
        "Binding and its PARAMETER arithmetic composition are constructed from "
        "source executions with a mandatory common HashAdapter, conditional on "
        "explicit native anchor/recovery and "
        "ISC/EC/APC Trust premises. Closure does not authenticate a computed root, "
        "UnitSource or configured profile. Aggregate certification, a full raw "
        "original/draft execution instance, concrete bounded codec/hash/exporter "
        "and nativeArithmeticRecoveryRefines remain OPEN. Traversal depth is "
        "not a bound on total graph work. Small synthetic traversal and canonical "
        "encoding cases are not native custody, signatures or a GO decision."
    )
    report["coverage"]["unresolved"].append(
        "The finalized PARAMETER corpus checker compares all entries in order "
        "against source-bound vector computations, exact Q leaves, context, "
        "parents and decimal spelling. Full aggregate bytes and an extended "
        "Binding are constructed with the same HashAdapter, conditional on NEW "
        "anchor/recovery/certificate and original-to-projected custody premises. "
        "APPLY reloads its original candidate and checks the exact ROOT certificate, "
        "selected profile, computed values and native hashes. The raw-source "
        "composition remains conditional: no full authenticated original/draft "
        "instance, original008 captures or UnitSource authority is fabricated. "
        "Arbitrary journal/phase/QC/send/current/crash/unknown/repair/physical WAL, "
        "concrete codec/hash/exporter bounds, native compatibility, contract freeze "
        "and independent review remain OPEN; nativeArithmeticRecoveryRefines is "
        "still missing. No runtime guard change, local PASS or GO follows."
    )
    report["coverage"]["unresolved"].append(
        "Finalized APPLY/current now composes original full ROOT/profile identity, "
        "actual NativeApply computation and original CurrentPointerCommand/QC "
        "hashes with exact five-field pointer-WAL records. Both current parents "
        "are checked at fresh advancement; historical exact replay allocates no "
        "second record. Known observed bytes must contain exactly the selected "
        "record; UNKNOWN stays incomplete and a retained torn suffix cannot pass "
        "the complete-observation gate. This is conditional source composition, "
        "not authenticated physical recovery or a complete native execution. "
        "Source trust, UnitSource, initial custody, arithmetic vote admission, "
        "mixed journal/phase/send/QC transitions, arbitrary snapshots and repair, "
        "concrete codec/hash/exporter resources, native compatibility, freeze and "
        "independent review remain OPEN. No runtime guard change or formal GO."
    )
    report["coverage"]["unresolved"].append(
        "A separate candidate arithmetic vote relation now executes original "
        "whole-policy selection, identity, parents, phase/deadline and actual "
        "source PARAMETER/APPLY computations. One next original VOTE/WAL record "
        "is checked after a completely scanned and executed guarded mixed prefix, "
        "with exact global sequence and original signature/view/semantic fields. "
        "Unknown/torn/corrupt prefixes and duplicate vote keys reject. The "
        "original native arithmetic guard remains unchanged and still rejects. "
        "This restricted prefix cannot contain earlier arithmetic votes; no "
        "physical append/exposure or authenticated complete execution follows. "
        "The distinct draft VoteMetadata/NativePrepared lossless bridge, full "
        "arithmetic mixed recovery, public durable correspondence, authority, "
        "phase/send/QC/current/crash/repair, concrete resources, compatibility, "
        "freeze/offline/independent review remain OPEN. NO_GO remains."
    )
    report["coverage"]["unresolved"].append(
        "Source-derived VoteMetadata and ExpectedNativeVote now accompany "
        "complete original PARAMETER/APPLY votes, parents and mixed-prefix WAL "
        "entries. Actual source bodies, parent digest roundtrips and anchor "
        "context are checked; native and projected hash preimages remain distinct. "
        "Recovery-scan flags cannot produce NativePrepared even with independent "
        "metadata authentication. A completed live event, complete prior durable "
        "set and distinct draft-vote versus mixed-WAL sequence relation remain "
        "OPEN, as do authenticated arithmetic history, physical persistence/export, "
        "full recovery, compatibility, freeze/offline and independent review. "
        "No runtime guard change or formal GO follows."
    )
    report["coverage"]["unresolved"].append(
        "A separate candidate mixed journal now folds arbitrarily many checked "
        "arithmetic inputs, reloading each source against the exact preceding "
        "policy/state and retaining executable pre/step/suffix vote provenance. "
        "Original commands and guarded non-arithmetic votes remain unchanged. "
        "Global positions, unique keys, invalidation, snapshot coverage and "
        "historical exact retry are retained; complete observed bytes align with "
        "an exact-length source list. Zero-snapshot state equality is an extra "
        "candidate restriction, not a native equivalence claim. Unknown, torn "
        "and corrupt inputs reject. No successful joined multi-arithmetic raw "
        "capture, authenticated source/export or physical persistence follows. "
        "Completed recovery/live NativePrepared, full prior public/draft durable "
        "correspondence and sequence mapping, full production recovery and "
        "phase/send/QC/current/repair, bounded resources, native compatibility, "
        "freeze/offline/independent review remain OPEN. NO_GO and guard remain."
    )
    report["coverage"]["unresolved"].append(
        "The complete source-bearing native vote cache is now derived from every "
        "executed candidate step, with soundness and completeness for finite runs "
        "and complete observed recovery. Original ordinary checked snapshots and "
        "arithmetic computations, bytes, parents and positions are retained. "
        "Entire ordered native cache equality and the exact all-vote ordinal plus "
        "preceding-command relation to original WAL positions are proved. "
        "Arithmetic diagnostic projection re-derives expected data and encodes "
        "new diagnostic receipts; unsupported ordinary rows reject the entire "
        "list, never disappear. This is not authenticated NativeReplay resolution, "
        "NativePrepared or completed recovery, and scan flags remain unchanged. "
        "Non-arithmetic public bodies, full public/draft durable correspondence, "
        "all-actor sequence abstraction, authority/live transitions, physical "
        "recovery, native compatibility, bounded resources, freeze/offline and "
        "independent review remain OPEN. No new successful nonempty joined "
        "arithmetic projection or physical capture is claimed. NO_GO remains."
    )
    report["coverage"]["unresolved"].append(
        "Original CONFIG/ISC public vote construction now uses the selected "
        "whole native snapshot at the actual historical prior state, without "
        "requiring a future arithmetic Binding. ISC uniquely selects and "
        "rechecks the complete original body/context/hash, retaining every "
        "ordered tuple. Complete public envelopes and five-field ISC bodies "
        "are constructed and compared with canonicality and collision checks. "
        "Primitive names and close policy require independently authenticated "
        "metadata; fixtures use synthetic trust. Public canonicalRoot is the "
        "entry set, not the native crypto root. These are projection checks, "
        "not new native admission restrictions. Historical cache composition "
        "retains actual source and position but does not yet project the full "
        "cache into all public durable sets. Ordinary diagnostic projection "
        "still rejects; recovered/ready flags remain unchanged. EC/APC/ROOT/"
        "VIEW/ABORT, shared aliases/configuration, full public durability and "
        "phase/QC/current/recovery, physical authority, bounded resources and "
        "freeze/offline/independent review remain OPEN. No GO or new native run."
    )
    report["coverage"]["unresolved"].append(
        "Complete original EC/APC public vote bodies now derive from the unique "
        "selected native snapshot lineage, retaining full ISC tuples, seed "
        "transcripts, norm evidence, ordered accepted tickets and plan weights. "
        "Whole public envelopes are compared, with canonicality and collision "
        "checks. APC additionally checks complete ISC and seed parent equality; "
        "this stronger projection restriction is not inferred from the native "
        "parent-ID guard and does not change native admission. Seed, norm, "
        "coefficient, policy and alias metadata require independent primitive "
        "authentication, synthetic in component examples. Original EC/APC "
        "component proofs are reused; no new positive whole EC/APC admission or "
        "joined public/native execution is claimed. Historical source and "
        "position composition does not yet connect the full public durable "
        "cache. ROOT/VIEW/ABORT, unified configuration/aliases, all-actor sequence "
        "mapping, completed live/recovery resolution, phase/send/QC/current/"
        "crash/repair, physical authority, bounded resources, compatibility and "
        "freeze/offline/independent review remain OPEN. NO_GO and guard remain."
    )
    report["coverage"]["unresolved"].append(
        "Original VIEW/ABORT source projection now reuses the complete selected "
        "snapshot and checked failure tail, retaining exact rows, timeout, "
        "runtime guards and all seven native finalized lists. Complete public "
        "VIEW_CHANGE bodies/envelopes preserve native integers and check model "
        "limits and both policy deadlines. ABORT construction supports only "
        "explicitly empty downstream lineage, retaining every config; nonempty "
        "ISC/EC/APC/PARAMETER/ROOT/APPLY lists reject, never disappear. This is "
        "a restricted projection, not native admission equivalence. Checkpoint "
        "and shared primitive metadata require independent authentication, "
        "synthetic in component examples. All public abort reasons are decoded "
        "exactly; missing/unknown data is not empty state. No new whole selected "
        "failure snapshot, native execution or physical absence authority is "
        "claimed. Nonempty ABORT lineage, ROOT, full public durable equality, "
        "all-actor sequences, source/configuration/current/phase/QC/recovery "
        "and physical persistence, bounded resources, compatibility and "
        "freeze/offline/independent review remain OPEN. NO_GO and guard remain."
    )
    report["coverage"]["unresolved"].append(
        "A finalized-corpus defect was found and corrected: the earlier leaf "
        "predicate required a nonempty proposed-vote context, whereas every "
        "actual finalized certificate decodes with an empty context. A general "
        "kernel theorem proves that old predicate impossible for every checked "
        "finalized edge. The corrected predicate retains original empty context "
        "and checks native context, ISC/EC/PLAN and denominator separately. "
        "Existing vector/frame/body/leaf/ordered-coverage checks remain. "
        "Pinned certificate component positives and mutations pass; no complete "
        "positive raw original/draft corpus execution is claimed. Earlier "
        "aggregate evidence is historical conditional/component evidence. "
        "ROOT/nonempty ABORT public construction, full public durable equality, "
        "source/configuration authentication and nativeArithmeticRecoveryRefines "
        "remain OPEN. No runtime/native guard change, local PASS or GO."
    )
    report["coverage"]["unresolved"].append(
        "Proposed ROOT now has conditional complete public body construction: "
        "the original selected proposal and finalized PARAMETER certificates "
        "are checked against every actual ordered native computation; shared "
        "policy/state follows from parsing the same original bytes with the "
        "Binding's HashAdapter. No future ROOT QC or APPLY is required. All "
        "twelve public ROOT fields and full scalar PARAMETER leaves are "
        "computed and compared, preserving ordered source witnesses. Original "
        "ROOT policy has empty ROOT QC/finalized/APPLY lists and finalized "
        "PARAMETER; component checks do not instantiate a complete positive "
        "raw arithmetic corpus. ROOT now additionally checks the full original "
        "ISC graph and primitive metadata agreement with the original PLAN "
        "parent construction. Complete structured ISC/seed/EC/APC identities "
        "are derived; original PLAN/ISC/EC source equality follows from actual "
        "raw parsers and lineage. Independent primitive metadata/configuration/"
        "alias authentication remains OPEN, as does the live public configuration "
        "and full public envelope/durable/QC/recovery relation, "
        "nonempty ABORT and nativeArithmeticRecoveryRefines. No local PASS, "
        "runtime guard change or GO is implied by this construction."
    )
    finalized = finalize_report(report, ROOT, registry)
    report_path = REPORTS / "formal-verification-report.json"
    write_canonical_json(report_path, finalized)
    print(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "decision": finalized["decision"],
                "decision_reasons": finalized["decision_reasons"],
                "formal_semantics_id": finalized["formal_semantics_id"],
                "report_sha256": sha256_file(report_path),
            },
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
