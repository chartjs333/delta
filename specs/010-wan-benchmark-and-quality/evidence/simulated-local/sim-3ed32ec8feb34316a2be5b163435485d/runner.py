#!/usr/bin/env python3
"""SIMULATED_LOCAL infrastructure smoke; never a benchmark qualification runner.

Only the Docker driver runs on the host. Controllers generate ephemeral Ed25519
keys inside their own tmpfs. All signing and network evidence has a separate
domain/type from benchmark governance and runtime certificates.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

MODE = "SIMULATED_LOCAL"
DOMAIN = b"deltareduce.feature010.simulated-controller.v1\x00"
CONTROLLERS = tuple(f"sim-controller-{number}" for number in range(1, 5))
PHASES = {"all-online": 4, "one-lost": 3, "two-lost": 2, "restarted": 3}
ROOT = Path(__file__).resolve().parent.parent.parent
MAX_BODY = 16384
SHA256 = re.compile(r"sha256:[0-9a-f]{64}\Z")


class SimulationError(ValueError):
    pass


def require(condition: bool, code: str) -> None:
    if not condition:
        raise SimulationError(code)


def canonical(value: Any) -> bytes:
    def check(item: Any) -> None:
        require(type(item) in (dict, list, str, int, bool, type(None)), "JSON_TYPE")
        if type(item) is dict:
            for key, child in item.items():
                require(type(key) is str and key.isascii(), "JSON_KEY")
                check(child)
        elif type(item) is list:
            for child in item:
                check(child)
        elif type(item) is str:
            require(item.isascii(), "JSON_ASCII")

    check(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def decode(data: bytes) -> dict[str, Any]:
    def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            require(key not in result, "DUPLICATE_KEY")
            result[key] = value
        return result

    value = json.loads(data, object_pairs_hook=unique)
    require(type(value) is dict and canonical(value) == data, "NONCANONICAL_JSON")
    return value


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def execute(
    args: list[str], timeout: int = 60, *, check: bool = True
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
    if check and result.returncode:
        raise SimulationError(
            f"COMMAND_FAILED:{args[0]}:{result.returncode}:{result.stderr[-2000:]}"
        )
    return result


def boundaries() -> dict[str, Any]:
    return {
        "authority_scope": "LOCAL_DEVELOPMENT_ONLY",
        "benchmark_result_qc": None,
        "feature010_go_checkpoint_sha": None,
        "feature011_admitted": False,
        "gate_eligible": False,
        "governance_independent": False,
        "label": "SIMULATED",
        "mode": MODE,
        "primary_eligible": False,
        "real_wan_eligible": False,
        "result_type": "SIMULATED_INFRASTRUCTURE_REPORT",
    }


def validate_body(body: dict[str, Any]) -> None:
    require(set(body) == {"mode", "run_id", "phase", "purpose", "source_id"}, "BODY_FIELDS")
    require(body["mode"] == MODE, "MODE_FORBIDDEN")
    require(body["purpose"] == "SIMULATED_INFRASTRUCTURE_ATTESTATION", "PURPOSE_FORBIDDEN")
    require(body["phase"] in PHASES, "PHASE_INVALID")
    require(re.fullmatch(r"sim-[0-9a-f]{32}", body["run_id"]) is not None, "RUN_ID_INVALID")
    require(SHA256.fullmatch(body["source_id"]) is not None, "SOURCE_ID_INVALID")


def signing_message(body: dict[str, Any], controller: str, generation: str) -> bytes:
    validate_body(body)
    require(controller in CONTROLLERS, "CONTROLLER_INVALID")
    require(re.fullmatch(r"[0-9a-f]{32}", generation) is not None, "GENERATION_INVALID")
    return DOMAIN + canonical({"body": body, "controller": controller, "generation": generation})


def verify_attestations(
    body: dict[str, Any], registry: list[dict[str, Any]], votes: list[dict[str, Any]]
) -> bool:
    """Verify simulation-only signatures; duplicate voters are invalid, not deduplicated."""
    validate_body(body)
    require(1 <= len(registry) <= 4, "REGISTRY_SIZE")
    identities: dict[str, dict[str, Any]] = {}
    public_keys: set[str] = set()
    for identity in registry:
        require(
            set(identity) == {"controller", "generation", "public_key_der", "mode"},
            "IDENTITY_FIELDS",
        )
        controller = identity["controller"]
        require(controller in CONTROLLERS and controller not in identities, "REGISTRY_DUPLICATE")
        require(identity["mode"] == MODE, "IDENTITY_MODE")
        signing_message(body, controller, identity["generation"])
        key = identity["public_key_der"]
        require(key not in public_keys, "KEY_REUSE")
        public_keys.add(key)
        identities[controller] = identity
    seen: set[str] = set()
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary)
        for vote in votes:
            require(
                set(vote) == {"controller", "generation", "body_id", "signature"}, "VOTE_FIELDS"
            )
            controller = vote["controller"]
            require(
                controller in identities and controller not in seen, "VOTER_DUPLICATE_OR_UNKNOWN"
            )
            identity = identities[controller]
            require(vote["generation"] == identity["generation"], "STALE_GENERATION")
            require(vote["body_id"] == digest(canonical(body)), "VOTE_BODY_MISMATCH")
            key = base64.b64decode(identity["public_key_der"], validate=True)
            signature = bytes.fromhex(vote["signature"])
            # RFC 8410 Ed25519 SubjectPublicKeyInfo: no algorithm substitution.
            require(
                len(key) == 44 and key[:12].hex() == "302a300506032b6570032100",
                "ED25519_KEY_INVALID",
            )
            require(len(signature) == 64, "SIGNATURE_LENGTH")
            (folder / "public.der").write_bytes(key)
            (folder / "signature").write_bytes(signature)
            (folder / "message").write_bytes(signing_message(body, controller, vote["generation"]))
            checked = execute(
                [
                    "openssl",
                    "pkeyutl",
                    "-verify",
                    "-pubin",
                    "-keyform",
                    "DER",
                    "-inkey",
                    str(folder / "public.der"),
                    "-rawin",
                    "-in",
                    str(folder / "message"),
                    "-sigfile",
                    str(folder / "signature"),
                ],
                check=False,
            )
            require(checked.returncode == 0, "SIGNATURE_INVALID")
            seen.add(controller)
    return len(seen) >= 3


def controller_service(controller: str, run_id: str) -> None:
    require(controller in CONTROLLERS, "CONTROLLER_INVALID")
    os.umask(0o077)
    with tempfile.TemporaryDirectory() as temporary:
        folder = Path(temporary)
        private = folder / "private.pem"
        execute(["openssl", "genpkey", "-algorithm", "ED25519", "-out", str(private)])
        execute(
            [
                "openssl",
                "pkey",
                "-in",
                str(private),
                "-pubout",
                "-outform",
                "DER",
                "-out",
                str(folder / "public.der"),
            ]
        )
        generation = uuid.uuid4().hex
        identity = {
            "controller": controller,
            "generation": generation,
            "mode": MODE,
            "public_key_der": base64.b64encode((folder / "public.der").read_bytes()).decode(),
        }

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, _format: str, *args: Any) -> None:
                return

            def respond(self, status: int, document: dict[str, Any]) -> None:
                data = canonical(document)
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self) -> None:
                self.respond(
                    200 if self.path == "/identity" else 404,
                    identity if self.path == "/identity" else {"error": "PATH"},
                )

            def do_POST(self) -> None:
                try:
                    self.connection.settimeout(5)
                    size = int(self.headers.get("Content-Length", "0"))
                    require(0 < size <= MAX_BODY and self.path == "/attest", "REQUEST_INVALID")
                    body = decode(self.rfile.read(size))
                    validate_body(body)
                    require(body["run_id"] == run_id, "RUN_MISMATCH")
                    (folder / "message").write_bytes(signing_message(body, controller, generation))
                    execute(
                        [
                            "openssl",
                            "pkeyutl",
                            "-sign",
                            "-inkey",
                            str(private),
                            "-rawin",
                            "-in",
                            str(folder / "message"),
                            "-out",
                            str(folder / "signature"),
                        ]
                    )
                    self.respond(
                        200,
                        {
                            "controller": controller,
                            "generation": generation,
                            "body_id": digest(canonical(body)),
                            "signature": (folder / "signature").read_bytes().hex(),
                        },
                    )
                except (ValueError, OSError, subprocess.SubprocessError):
                    self.respond(400, {"error": "SIMULATION_REQUEST_REJECTED"})

        HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()


def request(url: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    # No host proxy may send the simulated traffic outside the Docker network.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    data = None if body is None else canonical(body)
    with opener.open(
        urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"}),
        timeout=3,
    ) as response:
        return decode(response.read(MAX_BODY + 1))


def collect_phase(folder: Path, phase: str) -> None:
    manifest = decode((folder / "manifest.json").read_bytes())
    body = {
        "mode": MODE,
        "run_id": manifest["run_id"],
        "phase": phase,
        "purpose": "SIMULATED_INFRASTRUCTURE_ATTESTATION",
        "source_id": digest(canonical(manifest["source"])),
    }
    identities: list[dict[str, Any]] = []
    votes: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []
    unavailable: list[str] = []
    for controller in CONTROLLERS:
        url = f"http://{controller}:8080"
        try:
            identity = request(url + "/identity")
        except (urllib.error.URLError, TimeoutError, OSError):
            unavailable.append(controller)
            continue
        require(identity["controller"] == controller, "ENDPOINT_IDENTITY_MISMATCH")
        identities.append(identity)
        for sample in range(3):
            start = time.monotonic_ns()
            vote = request(url + "/attest", body)
            elapsed = time.monotonic_ns() - start
            require(verify_attestations(body, [identity], [vote]) is False, "SINGLE_VOTER_QUORUM")
            observations.append(
                {
                    "controller": controller,
                    "sample": sample,
                    "round_trip_ns": elapsed,
                    "request_body_bytes": len(canonical(body)),
                    "response_body_bytes": len(canonical(vote)),
                }
            )
        votes.append(vote)
    require(len(identities) == PHASES[phase], "PHASE_AVAILABILITY_MISMATCH")
    quorum = verify_attestations(body, identities, votes)
    require(quorum == (PHASES[phase] >= 3), "PHASE_QUORUM_MISMATCH")
    result = {
        **boundaries(),
        "body": body,
        "identities": identities,
        "observations": observations,
        "unavailable": unavailable,
        "votes": votes,
        "simulated_quorum_present": quorum,
        "network": "DOCKER_INTERNAL_BRIDGE",
        "tls": False,
        "timing_scope": "HTTP_AND_SIGNING_ROUND_TRIP_ONLY",
    }
    (folder / f"{phase}.json").write_bytes(canonical(result))


def wait_ready(phase: str) -> None:
    for controller in CONTROLLERS[: PHASES[phase]]:
        for attempt in range(30):
            try:
                identity = request(f"http://{controller}:8080/identity")
                require(identity["controller"] == controller, "READY_IDENTITY")
                break
            except (urllib.error.URLError, TimeoutError, OSError):
                if attempt == 29:
                    raise
                time.sleep(0.2)


def expect_rejection(operation: Any) -> None:
    try:
        operation()
    except (ValueError, KeyError, TypeError):
        return
    raise SimulationError("NEGATIVE_PROBE_ACCEPTED")


def verify_bundle(folder: Path) -> dict[str, Any]:
    manifest = decode((folder / "manifest.json").read_bytes())
    require(
        set(manifest)
        == {
            "schema_version",
            "run_id",
            "boundaries",
            "source",
            "image_id",
            "gpu_probe",
            "docker_server",
        },
        "MANIFEST_FIELDS",
    )
    require(manifest["schema_version"] == "1.0.0", "MANIFEST_VERSION")
    require(
        canonical(manifest["boundaries"]) == canonical(boundaries()),
        "MANIFEST_PROMOTION_FORBIDDEN",
    )
    require(SHA256.fullmatch(manifest["image_id"]) is not None, "MANIFEST_IMAGE")
    require(
        set(manifest["source"])
        == {"commit", "tree", "dirty", "simulation_script_id", "dockerfile_id"},
        "SOURCE_FIELDS",
    )
    for key in ("commit", "tree"):
        require(re.fullmatch(r"[0-9a-f]{40}", manifest["source"][key]) is not None, "SOURCE_GIT_ID")
    require(type(manifest["source"]["dirty"]) is bool, "SOURCE_DIRTY_TYPE")
    for name, field in (
        ("runner.py", "simulation_script_id"),
        ("Dockerfile.simulated", "dockerfile_id"),
    ):
        require(
            digest((folder / name).read_bytes()) == manifest["source"][field],
            "SOURCE_BYTES_MISMATCH",
        )
    reports: dict[str, dict[str, Any]] = {}
    artifacts: list[dict[str, Any]] = []
    for phase, count in PHASES.items():
        path = folder / f"{phase}.json"
        encoded = path.read_bytes()
        report = decode(encoded)
        require(
            set(report)
            == set(boundaries())
            | {
                "body",
                "identities",
                "observations",
                "unavailable",
                "votes",
                "simulated_quorum_present",
                "network",
                "tls",
                "timing_scope",
            },
            "REPORT_FIELDS",
        )
        for key, value in boundaries().items():
            require(
                report.get(key) == value and type(report.get(key)) is type(value),
                "REPORT_PROMOTION_FORBIDDEN",
            )
        body = report["body"]
        require(body["run_id"] == manifest["run_id"] and body["phase"] == phase, "PHASE_BINDING")
        require(body["source_id"] == digest(canonical(manifest["source"])), "SOURCE_BINDING")
        require(len(report["identities"]) == len(report["votes"]) == count, "PHASE_COUNT")
        available = {item["controller"] for item in report["identities"]}
        require(report["unavailable"] == sorted(set(CONTROLLERS) - available), "UNAVAILABLE_SET")
        require(
            report["network"] == "DOCKER_INTERNAL_BRIDGE" and report["tls"] is False,
            "NETWORK_RELABEL",
        )
        require(report["timing_scope"] == "HTTP_AND_SIGNING_ROUND_TRIP_ONLY", "TIMING_RELABEL")
        quorum = verify_attestations(body, report["identities"], report["votes"])
        require(
            report["simulated_quorum_present"] is quorum and quorum == (count >= 3),
            "QUORUM_BINDING",
        )
        require(len(report["observations"]) == 3 * count, "OBSERVATION_COUNT")
        seen: set[tuple[str, int]] = set()
        for observation in report["observations"]:
            require(
                set(observation)
                == {
                    "controller",
                    "sample",
                    "round_trip_ns",
                    "request_body_bytes",
                    "response_body_bytes",
                },
                "OBSERVATION_FIELDS",
            )
            key = (observation["controller"], observation["sample"])
            require(
                key[0] in available and type(key[1]) is int and 0 <= key[1] < 3 and key not in seen,
                "OBSERVATION_IDENTITY",
            )
            seen.add(key)
            require(
                type(observation["round_trip_ns"]) is int and observation["round_trip_ns"] > 0,
                "TIMING_INVALID",
            )
            require(observation["request_body_bytes"] == len(canonical(body)), "REQUEST_ACCOUNTING")
            vote = next(vote for vote in report["votes"] if vote["controller"] == key[0])
            require(
                observation["response_body_bytes"] == len(canonical(vote)), "RESPONSE_ACCOUNTING"
            )
        reports[phase] = report
        artifacts.append({"path": path.name, "sha256": digest(encoded)})
    original = reports["all-online"]
    expect_rejection(
        lambda: verify_attestations(
            original["body"], original["identities"], original["votes"] + original["votes"][:1]
        )
    )
    tampered = dict(original["body"], phase="one-lost")
    expect_rejection(
        lambda: verify_attestations(tampered, original["identities"], original["votes"])
    )
    corrupt = [dict(vote, signature="00" * 64) for vote in original["votes"]]
    expect_rejection(lambda: verify_attestations(original["body"], original["identities"], corrupt))
    expect_rejection(
        lambda: signing_message(
            dict(original["body"], purpose="BENCHMARK_RESULT_VOTE"),
            CONTROLLERS[0],
            original["identities"][0]["generation"],
        )
    )
    restarted = reports["restarted"]
    original_three = [
        vote
        for vote in original["votes"]
        if vote["controller"] in {identity["controller"] for identity in restarted["identities"]}
    ]
    expect_rejection(
        lambda: verify_attestations(original["body"], restarted["identities"], original_three)
    )
    before = next(
        identity for identity in original["identities"] if identity["controller"] == CONTROLLERS[2]
    )
    after = next(
        identity for identity in restarted["identities"] if identity["controller"] == CONTROLLERS[2]
    )
    require(
        before["generation"] != after["generation"]
        and before["public_key_der"] != after["public_key_der"],
        "RESTART_IDENTITY_NOT_ROTATED",
    )
    artifacts.append({"path": "manifest.json", "sha256": digest(canonical(manifest))})
    for name in ("runner.py", "Dockerfile.simulated"):
        artifacts.append({"path": name, "sha256": digest((folder / name).read_bytes())})
    return {
        **boundaries(),
        "run_id": manifest["run_id"],
        "diagnostic_status": "PASS",
        "artifacts": sorted(artifacts, key=lambda item: item["path"]),
        "checks": [
            "four_online_signatures",
            "one_loss_quorum",
            "two_loss_no_quorum",
            "duplicate_rejected",
            "tamper_rejected",
            "bad_signature_rejected",
            "production_purpose_rejected",
            "restart_generation_fenced",
        ],
        "qualification_status": "STOPPED_BEFORE_PROTOCOL_EXECUTION",
        "blockers": [
            "FEATURE000_ARITHMETIC_BINDING",
            "NATIVE_PARAMETER_APPLY_CLOSURE",
            "PROFILE_QUALIFICATION",
            "GATES_A_B_C_D",
            "PRODUCTION_GOVERNANCE_AND_RESULT_QUORUM",
        ],
        "runtime_execution": False,
        "scientific_training_execution": False,
        "limitations": [
            "single_host_single_administrator",
            "ephemeral_test_keys",
            "docker_bridge_without_wan_emulation_or_tls",
            "no_consensus_wal_or_replay_claim",
            "no_gpu_training_claim",
        ],
    }


def docker(
    args: list[str], timeout: int = 60, *, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return execute(["docker", *args], timeout, check=check)


def run_docker(output: Path, image: str | None) -> Path:
    run_id = "sim-" + uuid.uuid4().hex
    folder = output.resolve() / run_id
    folder.mkdir(parents=True, exist_ok=False)
    script = Path(__file__).resolve()
    if image is None:
        built = docker(
            [
                "build",
                "--quiet",
                "--network",
                "none",
                "-f",
                str(script.with_name("Dockerfile.simulated")),
                str(script.parent),
            ],
            600,
        )
        image = built.stdout.strip().splitlines()[-1]
    require(SHA256.fullmatch(image) is not None, "IMAGE_MUST_BE_IMMUTABLE_LOCAL_ID")
    identity = docker(["image", "inspect", image, "--format", "{{.Id}}"]).stdout.strip()
    require(identity == image, "IMAGE_ID_MISMATCH")
    script_snapshot = folder / "runner.py"
    script_snapshot.write_bytes(script.read_bytes())
    dockerfile_snapshot = folder / "Dockerfile.simulated"
    dockerfile_snapshot.write_bytes(script.with_name("Dockerfile.simulated").read_bytes())
    # A script hash records the actual bytes even in an explicitly uncommitted checkout.
    source = {
        "commit": execute(["git", "-C", str(ROOT), "rev-parse", "HEAD"]).stdout.strip(),
        "tree": execute(["git", "-C", str(ROOT), "rev-parse", "HEAD^{tree}"]).stdout.strip(),
        "dirty": bool(execute(["git", "-C", str(ROOT), "status", "--porcelain"]).stdout.strip()),
        "simulation_script_id": digest(script_snapshot.read_bytes()),
        "dockerfile_id": digest(dockerfile_snapshot.read_bytes()),
    }
    gpu = docker(
        [
            "run",
            "--rm",
            "--network",
            "none",
            "--gpus",
            "all",
            "--entrypoint",
            "nvidia-smi",
            image,
            "--query-gpu=name,uuid,memory.total,driver_version",
            "--format=csv",
        ],
        check=False,
    )
    manifest = {
        "schema_version": "1.0.0",
        "run_id": run_id,
        "boundaries": boundaries(),
        "source": source,
        "image_id": image,
        "gpu_probe": {
            "exit_code": gpu.returncode,
            "stdout": gpu.stdout.strip(),
            "stderr": gpu.stderr.strip(),
            "scope": "DEVICE_VISIBILITY_ONLY",
        },
        "docker_server": docker(["version", "--format", "{{json .Server}}"]).stdout.strip(),
    }
    (folder / "manifest.json").write_bytes(canonical(manifest))
    network = "delta-" + run_id
    containers: list[str] = []
    network_created = False
    cleanup_errors: list[str] = []
    base = [
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "64",
        "--memory",
        "192m",
        "--cpus",
        "1",
        "--user",
        "65534:65534",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=16m,mode=1777",
        "--mount",
        f"type=bind,source={script_snapshot},target=/simulated_local.py,readonly",
        "--entrypoint",
        "python3",
    ]

    def helper(arguments: list[str], *, offline: bool = False, readonly: bool = False) -> str:
        name = network + "-helper-" + uuid.uuid4().hex[:8]
        containers.append(name)
        mount = f"type=bind,source={folder},target=/evidence"
        if readonly:
            mount += ",readonly"
        user = []
        if hasattr(os, "getuid"):
            user = ["--user", f"{os.getuid()}:{os.getgid()}"]
        return docker(
            [
                "run",
                "--name",
                name,
                "--label",
                f"delta.simulation={run_id}",
                "--network",
                "none" if offline else network,
                *base,
                *user,
                "--mount",
                mount,
                image,
                "/simulated_local.py",
                *arguments,
            ],
            90,
        ).stdout

    try:
        docker(
            ["network", "create", "--internal", "--label", f"delta.simulation={run_id}", network]
        )
        network_created = True
        for controller in CONTROLLERS:
            name = network + "-" + controller
            containers.append(name)
            docker(
                [
                    "run",
                    "-d",
                    "--name",
                    name,
                    "--label",
                    f"delta.simulation={run_id}",
                    "--network",
                    network,
                    "--network-alias",
                    controller,
                    *base,
                    image,
                    "/simulated_local.py",
                    "controller",
                    "--controller",
                    controller,
                    "--run-id",
                    run_id,
                ]
            )
        for phase in PHASES:
            if phase == "one-lost":
                docker(["kill", containers[3]])
            elif phase == "two-lost":
                docker(["kill", containers[2]])
            elif phase == "restarted":
                docker(["start", containers[2]])
            # Readiness is bounded and checked inside the same isolated network.
            helper(["ready", "--phase", phase], readonly=True)
            helper(["collect", "--output", "/evidence", "--phase", phase])
        verified = helper(["verify", "--output", "/evidence"], offline=True, readonly=True)
        report = decode(verified.strip().encode())
        encoded = canonical(report)
        (folder / "report.json").write_bytes(encoded)
        (folder / (digest(encoded)[7:] + ".json")).write_bytes(encoded)
    finally:
        # Only exact names created by this run are removed; no prune or shared volumes.
        for name in reversed(containers):
            result = docker(["rm", "-f", name], check=False)
            if result.returncode and "No such container" not in result.stderr:
                cleanup_errors.append(name)
        if network_created and docker(["network", "rm", network], check=False).returncode:
            cleanup_errors.append(network)
        (folder / "cleanup.json").write_bytes(
            canonical({"resources_remaining": cleanup_errors, "run_id": run_id})
        )
    require(not cleanup_errors, "DOCKER_CLEANUP_FAILED")
    return folder


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action", choices=("plan", "run", "controller", "ready", "collect", "verify")
    )
    parser.add_argument("--mode", choices=(MODE,), default=MODE)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts" / "feature010" / MODE)
    parser.add_argument(
        "--image", help="Exact local Docker sha256 image ID; omit to build the pinned image"
    )
    parser.add_argument("--controller", choices=CONTROLLERS)
    parser.add_argument("--run-id")
    parser.add_argument("--phase", choices=tuple(PHASES))
    args = parser.parse_args()
    try:
        if args.action == "plan":
            print(
                canonical(
                    {
                        **boundaries(),
                        "phases": PHASES,
                        "qualification_status": "BLOCKED_FORMAL",
                        "scope": "controller_signing_and_docker_network_only",
                    }
                ).decode()
            )
        elif args.action == "controller":
            require(args.controller is not None and args.run_id is not None, "CONTROLLER_ARGUMENTS")
            controller_service(args.controller, args.run_id)
        elif args.action == "collect":
            require(args.phase is not None, "PHASE_REQUIRED")
            collect_phase(args.output, args.phase)
        elif args.action == "ready":
            require(args.phase is not None, "PHASE_REQUIRED")
            wait_ready(args.phase)
        elif args.action == "verify":
            encoded = canonical(verify_bundle(args.output))
            saved_report = args.output / "report.json"
            if saved_report.exists():
                require(saved_report.read_bytes() == encoded, "SAVED_REPORT_MISMATCH")
            print(encoded.decode())
        else:
            folder = run_docker(args.output, args.image)
            print(
                canonical(
                    {
                        "mode": MODE,
                        "evidence_directory": str(folder),
                        "diagnostic_status": "PASS",
                        "qualification_status": "STOPPED_BEFORE_PROTOCOL_EXECUTION",
                    }
                ).decode()
            )
        return 0
    except (ValueError, KeyError, TypeError, OSError, subprocess.SubprocessError) as error:
        print(
            json.dumps(
                {"mode": MODE, "diagnostic_status": "FAIL", "error": str(error)}, sort_keys=True
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
