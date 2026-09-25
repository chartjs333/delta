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
            "native/public WAL recovery or authenticated export. Policy/WAL "
            "decoders/replay, source provenance, full public behavior and the "
            "mandatory recovery conjunct remain open; no formal/local GO follows.",
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
