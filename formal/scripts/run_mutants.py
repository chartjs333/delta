#!/usr/bin/env python3
"""Mutate production TLA+ actions and archive each intended TLC witness."""

from __future__ import annotations

import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TLA_ROOT = ROOT / "formal" / "tla"
FIXTURES = ROOT / "formal" / "fixtures" / "counterexamples"
TOOLCHAIN = ROOT / "formal" / "toolchain"
sys.path.insert(0, str(ROOT / "formal" / "scripts"))
sys.path.insert(0, str(TOOLCHAIN))

from formal_artifacts import canonical_json_bytes, sha256_file, write_canonical_json  # noqa: E402
from prepare_cache import artifacts, verify  # noqa: E402


@dataclass(frozen=True)
class Replacement:
    old: str
    new: str
    expected_count: int = 1


@dataclass(frozen=True)
class Mutation:
    mutant_id: str
    invariant: str
    property_id: str
    source: str
    operator: str
    module: str
    config: str
    replacements: tuple[Replacement, ...]
    config_replacements: tuple[Replacement, ...] = ()


MUTATIONS = (
    Mutation(
        "MUT-MISSING-DURABLE-VOTE",
        "AllQCVotesPersisted",
        "INV-ALL-QC-VOTES-PERSISTED",
        "DeltaReduceCertificates.tla",
        "VoteISC",
        "DeltaReduceVoteLifecycleHarness",
        "vote-lifecycle-isc.cfg",
        (
            Replacement(
                "        /\\ PersistVoteEnvelopeChanges(envelope)\n"
                "        /\\ iscVotes' = iscVotes \\cup {vote}",
                "        /\\ durableVotes' = durableVotes\n"
                "        /\\ volatileVotes' = volatileVotes \\cup {envelope}\n"
                "        /\\ durableSequence' = durableSequence\n"
                "        /\\ iscVotes' = iscVotes \\cup {vote}",
            ),
        ),
    ),
    Mutation(
        "MUT-DUPLICATE-COMMITMENT",
        "CommitUniqueness",
        "INV-COMMIT-UNIQUENESS",
        "DeltaReduceTickets.tla",
        "CommitTicket",
        "DeltaReduce",
        "input-freeze-seed.cfg",
        (
            Replacement(
                "        /\\ commitments' = commitments \\cup {commitment}",
                "        /\\ commitments' = commitments \\cup\n"
                "            {[ticket |-> ticket, worker |-> worker,\n"
                "              leaseEpoch |-> epoch, content |-> candidate] :\n"
                "                candidate \\in ContentIds}",
            ),
        ),
        (Replacement("ContentIds = {content1}", "ContentIds = {content1, content2}"),),
    ),
    Mutation(
        "MUT-MUTABLE-ISC",
        "ISCImmutability",
        "INV-ISC-IMMUTABILITY",
        "DeltaReduceCertificates.tla",
        "CloseInput",
        "DeltaReduce",
        "input-freeze-seed.cfg",
        (
            Replacement(
                "        /\\ closedInputBodies' = closedInputBodies \\cup {body}",
                "        /\\ closedInputBodies' = closedInputBodies \\cup\n"
                "            {body, [body EXCEPT !.entries = {},\n"
                "                                !.canonicalRoot = {}]}",
            ),
        ),
    ),
    Mutation(
        "MUT-EARLY-SEED",
        "SeedAfterInputFreeze",
        "INV-SEED-AFTER-FREEZE",
        "DeltaReduceCertificates.tla",
        "GenerateSeed",
        "DeltaReduce",
        "input-freeze-seed.cfg",
        (
            Replacement(
                "        /\\ isc \\in FinalizedISCBodies\n"
                "        /\\ ~RoundAbortRequired(isc.round)\n"
                "        /\\ SeedsForISC(isc) = {}",
                "        /\\ isc \\in closedInputBodies\n"
                "        /\\ ~RoundAbortRequired(isc.round)\n"
                "        /\\ SeedsForISC(isc) = {}",
            ),
            Replacement(
                "GenerateSeedAction ==\n"
                "    \\E isc \\in FinalizedISCBodies : GenerateSeed(isc)",
                "GenerateSeedAction ==\n"
                "    \\E isc \\in closedInputBodies : GenerateSeed(isc)",
            ),
        ),
    ),
    Mutation(
        "MUT-MISSING-APC-PARENT",
        "APCParentage",
        "INV-APC-PARENTAGE",
        "DeltaReduceCertificates.tla",
        "VoteAPC/FinalizeAPC",
        "DeltaReduce",
        "certificate-frankenstein.cfg",
        (
            Replacement(
                "        /\\ ValidAggregationPlanBody(body)\n",
                "",
                expected_count=2,
            ),
            Replacement(
                "VoteAPCAction ==\n"
                "    \\E validator \\in Validators, ec \\in FinalizedECBodies,\n"
                "       members \\in SUBSET Tickets, profile \\in CoefficientProfiles :\n"
                "        VoteAPC(validator,\n"
                "            AggregationPlanBody(\n"
                "                ec.isc, ec.seed, ec, members, profile))",
                "VoteAPCAction ==\n"
                "    \\E validator \\in Validators, ec \\in FinalizedECBodies,\n"
                "       members \\in SUBSET Tickets, profile \\in CoefficientProfiles :\n"
                "        LET wrongISC == [ec.isc EXCEPT !.canonicalRoot = {}]\n"
                "        IN VoteAPC(validator,\n"
                "            AggregationPlanBody(\n"
                "                wrongISC, ec.seed, ec, members, profile))",
            ),
        ),
        (
            Replacement(
                "SafeCoefficientProfiles = {coeffSafe}",
                "SafeCoefficientProfiles = {coeffSafe, coeffUnsafe}",
            ),
        ),
    ),
    Mutation(
        "MUT-MISSING-SHARD-PARENT",
        "ShardViewAtomicity",
        "INV-SHARD-VIEW-ATOMICITY",
        "DeltaReduceReduceApply.tla",
        "ProposeParameterResult",
        "DeltaReducePhase6Harness",
        "arithmetic-boundary.cfg",
        (
            Replacement(
                "    /\\ ValidParameterResultBody(body)\n"
                "    /\\ ~RoundAbortRequired(body.round)\n"
                "    /\\ currentCheckpoint = body.parent",
                "    /\\ IsParameterResultBody(body)\n"
                "    /\\ ~RoundAbortRequired(body.round)",
            ),
            Replacement(
                "        /\\ ValidParameterResultBody(body)\n"
                "        /\\ Cardinality(signers) >= QuorumSize",
                "        /\\ Cardinality(signers) >= QuorumSize",
            ),
            Replacement(
                "ProposeParameterResultAction ==\n"
                "    \\E apc \\in FinalizedAPCBodies, domain \\in Domains,\n"
                "       shard \\in Shards :\n"
                "        ProposeParameterResult(\n"
                "            ParameterResultBody(\n"
                "                apc, domain, shard, ConfiguredParentCheckpoint,",
                "ProposeParameterResultAction ==\n"
                "    \\E apc \\in FinalizedAPCBodies, domain \\in Domains,\n"
                "       shard \\in Shards, parent \\in ParentCheckpoints :\n"
                "        ProposeParameterResult(\n"
                "            ParameterResultBody(\n"
                "                apc, domain, shard, parent,",
            ),
        ),
        (
            Replacement("ParentCheckpoints = {parent1}", "ParentCheckpoints = {parent1, parent2}"),
            Replacement(
                "CheckpointIds = {parent1, next1}",
                "CheckpointIds = {parent1, parent2, next1}",
            ),
        ),
    ),
    Mutation(
        "MUT-INCOMPLETE-AGGREGATE",
        "AggregateCompleteness",
        "INV-AGGREGATE-COMPLETENESS",
        "DeltaReduceReduceApply.tla",
        "AssembleAggregateRoot/FinalizeAggregateRootQC",
        "DeltaReducePhase6Harness",
        "apply-recovery.cfg",
        (
            Replacement("    /\\ ValidAggregateRootBody(body)\n", "", expected_count=2),
            Replacement(
                "AssembleAggregateRootAction ==\n"
                "    \\E apc \\in FinalizedAPCBodies :\n"
                "        AssembleAggregateRoot(\n"
                "            AggregateRootBody(\n"
                "                apc, FinalizedParameterBodiesForAPC(apc)))",
                "AssembleAggregateRootAction ==\n"
                "    \\E apc \\in FinalizedAPCBodies :\n"
                "        \\E leaves \\in SUBSET FinalizedParameterBodiesForAPC(apc) :\n"
                "            AssembleAggregateRoot(AggregateRootBody(apc, leaves))",
            ),
        ),
    ),
    Mutation(
        "MUT-UNCHECKED-OVERFLOW",
        "NoOverflow",
        "INV-NO-OVERFLOW",
        "DeltaReduceReduceApply.tla",
        "ProposeParameterResult",
        "DeltaReducePhase6Harness",
        "arithmetic-boundary.cfg",
        (
            Replacement(
                "    /\\ ValidParameterResultBody(body)\n"
                "    /\\ ~RoundAbortRequired(body.round)",
                "    /\\ IsParameterResultBody(body)\n"
                "    /\\ ~RoundAbortRequired(body.round)",
            ),
            Replacement(
                "ProposeParameterResultAction ==\n"
                "    \\E apc \\in FinalizedAPCBodies, domain \\in Domains,\n"
                "       shard \\in Shards :\n"
                "        ProposeParameterResult(\n"
                "            ParameterResultBody(\n"
                "                apc, domain, shard, ConfiguredParentCheckpoint,\n"
                "                ConfiguredParameterSchema, ConfiguredArithmeticProfile,\n"
                "                ExpectedParameterValue, TRUE))",
                "ProposeParameterResultAction ==\n"
                "    \\E apc \\in FinalizedAPCBodies, domain \\in Domains,\n"
                "       shard \\in Shards, value \\in ParameterValues,\n"
                "       checked \\in BOOLEAN :\n"
                "        ProposeParameterResult(\n"
                "            ParameterResultBody(\n"
                "                apc, domain, shard, ConfiguredParentCheckpoint,\n"
                "                ConfiguredParameterSchema, ConfiguredArithmeticProfile,\n"
                "                value, checked))",
            ),
        ),
    ),
    Mutation(
        "MUT-CURRENT-WITHOUT-APPLYQC",
        "CurrentCertified",
        "INV-CURRENT-CERTIFIED",
        "DeltaReduceReduceApply.tla",
        "AdvanceCurrentCheckpoint",
        "DeltaReducePhase6Harness",
        "apply-recovery.cfg",
        (
            Replacement(
                "    /\\ body \\in FinalizedApplyBodies\n"
                "    /\\ ValidApplyBody(body)\n"
                "    /\\ phase \\in {\"ACTIVE\", \"ABORTING\"}",
                "    /\\ body \\in applyCandidates\n"
                "    /\\ ValidApplyBody(body)\n"
                "    /\\ phase \\in {\"ACTIVE\", \"ABORTING\"}",
            ),
            Replacement(
                "AdvanceCurrentCheckpointAction ==\n"
                "    \\E body \\in FinalizedApplyBodies :\n"
                "        AdvanceCurrentCheckpoint(body)",
                "AdvanceCurrentCheckpointAction ==\n"
                "    \\E body \\in applyCandidates :\n"
                "        AdvanceCurrentCheckpoint(body)",
            ),
        ),
    ),
    Mutation(
        "MUT-PARTIAL-PUBLICATION",
        "PlaneSeparation",
        "INV-PLANE-SEPARATION",
        "DeltaReduceReduceApply.tla",
        "PublishCertifiedObject",
        "DeltaReducePhase6Harness",
        "apply-recovery.cfg",
        (
            Replacement(
                "    /\\ object \\in CertifiedGlobalObjects\n"
                "    /\\ object \\notin publishedObjects",
                "    /\\ object \\in CertifiedGlobalObjects \\cup ForbiddenPublicationObjects\n"
                "    /\\ object \\notin publishedObjects",
            ),
            Replacement(
                "PublishCertifiedObjectAction ==\n"
                "    \\E object \\in CertifiedGlobalObjects : PublishCertifiedObject(object)",
                "PublishCertifiedObjectAction ==\n"
                "    \\E object \\in CertifiedGlobalObjects \\cup ForbiddenPublicationObjects :\n"
                "        PublishCertifiedObject(object)",
            ),
        ),
    ),
)


def replace_exact(text: str, replacement: Replacement, label: str) -> str:
    count = text.count(replacement.old)
    if count != replacement.expected_count:
        raise RuntimeError(
            f"{label}: expected {replacement.expected_count} exact source anchors, found {count}"
        )
    return text.replace(replacement.old, replacement.new)


def invariant_only_config(text: str, invariant: str) -> str:
    start = text.index("INVARIANTS\n")
    end = text.index("CHECK_DEADLOCK", start)
    return f"{text[:start]}INVARIANT {invariant}\n\n{text[end:]}"


def normalized_tlc_trace(output: str) -> list[str]:
    trace = [match.strip() for match in re.findall(r"State \d+: <([^>]+)>", output)]
    if not trace:
        raise RuntimeError("TLC counterexample did not contain a state/action trace")
    return trace


def write_fixture(path: Path, value: object) -> None:
    data = canonical_json_bytes(value)
    for attempt in range(5):
        try:
            path.write_bytes(data)
            return
        except OSError:
            if attempt == 4:
                raise
            time.sleep(0.1 * (attempt + 1))


def main() -> int:
    artifact = artifacts("tla")[0]
    jar = Path(os.environ.get("TLA2TOOLS_JAR", TOOLCHAIN / "cache" / artifact["artifact"]))
    valid, reason = verify(jar, artifact)
    if not valid:
        raise RuntimeError(f"unverified tla2tools: {reason}")
    native_java = TOOLCHAIN / "windows" / "tla-runtime-17.0.20.1" / "java" / "bin" / "java.exe"
    java = os.environ.get(
        "JAVA", str(native_java) if os.name == "nt" and native_java.is_file() else "java"
    )
    if shutil.which(java) is None and not Path(java).is_file():
        raise RuntimeError("java executable is missing")

    tool_hash = sha256_file(jar)
    FIXTURES.mkdir(parents=True, exist_ok=True)
    summaries: list[dict[str, object]] = []

    requested = os.environ.get("MUTANT_FILTER")
    selected = tuple(
        mutation for mutation in MUTATIONS
        if requested is None or mutation.mutant_id == requested
    )
    if requested is not None and not selected:
        raise RuntimeError(f"unknown MUTANT_FILTER: {requested}")

    for index, mutation in enumerate(selected):
        with tempfile.TemporaryDirectory(prefix="deltareduce-production-mutant-") as raw_temp:
            work = Path(raw_temp)
            for tla in TLA_ROOT.glob("*.tla"):
                shutil.copy2(tla, work / tla.name)

            source_path = TLA_ROOT / mutation.source
            original = source_path.read_text(encoding="utf-8")
            mutated = original
            for replacement in mutation.replacements:
                mutated = replace_exact(mutated, replacement, mutation.mutant_id)
            mutated_path = work / mutation.source
            mutated_path.write_text(mutated, encoding="utf-8", newline="\n")

            cfg_source = TLA_ROOT / "cfg" / mutation.config
            cfg_text = cfg_source.read_text(encoding="utf-8")
            for replacement in mutation.config_replacements:
                cfg_text = replace_exact(cfg_text, replacement, mutation.mutant_id)
            cfg_text = invariant_only_config(cfg_text, mutation.invariant)
            cfg_path = work / "production-mutant.cfg"
            cfg_path.write_text(cfg_text, encoding="utf-8", newline="\n")

            command = [
                java,
                "-XX:+UseParallelGC",
                "-Dfile.encoding=UTF-8",
                "-Duser.language=en",
                "-Duser.country=US",
                "-Duser.timezone=UTC",
                "-cp",
                str(jar),
                "tlc2.TLC",
                "-workers",
                "1",
                "-fp",
                str((index * 7 + 3) % 64),
                "-seed",
                str(2026082500 + index),
                "-config",
                cfg_path.name,
                mutation.module,
            ]
            result = subprocess.run(
                command,
                cwd=work,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=240,
            )
            output = f"{result.stdout}\n{result.stderr}"
            expected_marker = f"Invariant {mutation.invariant} is violated."
            if "Finished computing initial states: 0 distinct states generated" in output:
                raise RuntimeError(f"{mutation.mutant_id}: vacuous model has no initial states")
            if result.returncode == 0:
                raise RuntimeError(
                    f"{mutation.mutant_id}: unexpectedly passed; output={output[-2000:]!r}"
                )
            if expected_marker not in output:
                match = re.search(r"Invariant ([A-Za-z0-9_]+) is violated", output)
                actual = match.group(1) if match else "NO_INVARIANT"
                raise RuntimeError(
                    f"{mutation.mutant_id}: intended {mutation.invariant}, observed {actual}; "
                    f"output={output[-2000:]!r}"
                )

            diff = "".join(
                difflib.unified_diff(
                    original.splitlines(keepends=True),
                    mutated.splitlines(keepends=True),
                    fromfile=f"a/formal/tla/{mutation.source}",
                    tofile=f"b/formal/tla/{mutation.source}",
                )
            )
            fixture = {
                "schema_version": "2.0.0",
                "mutant_id": mutation.mutant_id,
                "expected_property_id": mutation.property_id,
                "expected_invariant": mutation.invariant,
                "outcome": "EXPECTED_COUNTEREXAMPLE",
                "mutation_scope": "PRODUCTION_ACTION_SOURCE",
                "source_mutation": {
                    "path": f"formal/tla/{mutation.source}",
                    "operator": mutation.operator,
                    "original_sha256": sha256_file(source_path),
                    "mutated_sha256": sha256_file(mutated_path),
                    "unified_diff_sha256": hashlib.sha256(diff.encode()).hexdigest(),
                },
                "model": {
                    "root_module": mutation.module,
                    "root_path": f"formal/tla/{mutation.module}.tla",
                    "root_sha256": sha256_file(TLA_ROOT / f"{mutation.module}.tla"),
                },
                "config": {
                    "path": f"formal/tla/cfg/{mutation.config}",
                    "source_sha256": sha256_file(cfg_source),
                    "mutated_sha256": sha256_file(cfg_path),
                },
                "tool_sha256": tool_hash,
                "tlc_output_sha256": hashlib.sha256(output.encode()).hexdigest(),
                "normalized_trace": normalized_tlc_trace(output),
            }
            fixture_path = FIXTURES / f"{mutation.mutant_id.lower()}.json"
            write_fixture(fixture_path, fixture)
            summaries.append(
                {
                    "id": mutation.mutant_id,
                    "property": mutation.property_id,
                    "production_operator": mutation.operator,
                    "status": "PASS",
                }
            )
            print(
                f"{mutation.mutant_id}: production {mutation.operator} mutation "
                f"triggered {mutation.invariant}"
            )

    report = {
        "schema_version": "2.0.0",
        "status": "PASS",
        "mutation_scope": "PRODUCTION_ACTION_SOURCE",
        "mutants": summaries,
    }
    write_canonical_json(ROOT / "formal" / "reports" / "mutant-evidence.json", report)
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
