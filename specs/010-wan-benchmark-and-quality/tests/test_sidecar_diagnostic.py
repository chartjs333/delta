from __future__ import annotations

import copy
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "specs/010-wan-benchmark-and-quality/scripts"
DIAGNOSTICS = ROOT / "specs/010-wan-benchmark-and-quality/diagnostics"
JAVA_CAPTURE = (
    ROOT / "delta-node-java/src/test/java/io/deltareduce/node/sidecar/SidecarComparisonCapture.java"
)
HOST_COLLECTOR = DIAGNOSTICS / "Collect-SidecarDiagnosticHost.ps1"
HOST_WRAPPER = DIAGNOSTICS / "Invoke-SidecarDiagnosticCampaign.ps1"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(DIAGNOSTICS))
import assemble_sidecar_diagnostic_allocation as allocation_assembler  # noqa: E402
import run_sidecar_diagnostic as runner  # noqa: E402
import sidecar_diagnostic_common as diagnostic  # noqa: E402


def example_manifest() -> dict[str, object]:
    path = DIAGNOSTICS / "sidecar-diagnostic-manifest.example.json"
    raw = path.read_bytes()
    value = json.loads(raw)
    return value


def synthetic_process_receipt(tmp_path: Path, *arguments: str) -> dict[str, object]:
    invocation = diagnostic.invocation_record(
        [str(Path(sys.executable).resolve()), *arguments],
        environment={"LANG": "C", "LC_ALL": "C", "TZ": "UTC"},
        working_directory=tmp_path,
    )
    return {
        **invocation,
        "exit_code": 0,
        "stderr_sha256": diagnostic.sha256_id(b""),
        "stdout_sha256": diagnostic.sha256_id(b""),
    }


def synthetic_checkout_receipt(tmp_path: Path, source: dict[str, object]) -> dict[str, object]:
    return {
        "checkout_root": tmp_path.resolve().as_posix(),
        "commit": source["commit"],
        "git_invocations": [synthetic_process_receipt(tmp_path, "git-probe")],
        "status_porcelain_sha256": diagnostic.sha256_id(b""),
        "tree": source["tree"],
    }


def allocation_fixture(
    tmp_path: Path, manifest: dict[str, object], *, jfr_name: str = "jdk/bin/jfr"
) -> tuple[dict[str, object], dict[str, object]]:
    root = tmp_path / "pinned-allocation"
    relatives = {
        "BUILD_PROVENANCE_RECEIPT": "build-provenance.json",
        "CANONICAL_CORPUS": "corpus.bin",
        "JAVA_CLASSES_JAR": "sidecar-diagnostic-tests.jar",
        "JAVA_EXECUTABLE": "jdk/bin/java",
        "JFR_EXECUTABLE": jfr_name,
        "NATIVE_LIBRARY": "libdelta_ffi.so",
        "SIDECAR_EXECUTABLE": "delta_runtime_sidecar",
        "STRACE_EXECUTABLE": "bin/strace",
    }
    indexed: dict[str, dict[str, object]] = {}
    for identifier in diagnostic.ALLOCATION_ARTIFACT_IDS[1:]:
        path = root / relatives[identifier]
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = f"{identifier}\n".encode()
        path.write_bytes(payload)
        indexed[identifier] = {
            "artifact_id": identifier,
            "path": path.as_posix(),
            "sha256": diagnostic.sha256_id(payload),
            "size_bytes": len(payload),
        }
    environment = manifest["environment"]
    assert isinstance(environment, dict)
    environment["allocation_root"] = root.as_posix()
    invocation = {
        "argv": ["cmake", "--build", "--preset", "ci"],
        "environment": {"CC": "clang", "CXX": "clang++"},
        "environment_mode": "REPLACE",
        "working_directory": tmp_path.resolve().as_posix(),
    }
    build_stdout = root / "build.stdout"
    build_stderr = root / "build.stderr"
    build_stdout.write_bytes(b"synthetic build stdout\n")
    build_stderr.write_bytes(b"")

    def execution_record(path: Path) -> dict[str, object]:
        payload = path.read_bytes()
        return {
            "path": path.as_posix(),
            "sha256": diagnostic.sha256_id(payload),
            "size_bytes": len(payload),
        }

    provenance = {
        "builder_container_image_digest": environment["container_image_digest"],
        "execution": {
            "exit_code": 0,
            "stderr": execution_record(build_stderr),
            "stdout": execution_record(build_stdout),
        },
        "invocation": invocation,
        "invocation_sha256": diagnostic.sha256_id(diagnostic.canonical_bytes(invocation)),
        "outputs": [
            {
                "artifact_id": identifier,
                "sha256": indexed[identifier]["sha256"],
            }
            for identifier in diagnostic.BUILD_OUTPUT_IDS
        ],
        "schema_version": diagnostic.SCHEMA_VERSION,
        "source": manifest["source"],
        "source_checkout": synthetic_checkout_receipt(tmp_path, manifest["source"]),
        "type_name": diagnostic.BUILD_PROVENANCE_TYPE,
    }
    provenance_path = root / relatives["BUILD_PROVENANCE_RECEIPT"]
    provenance_payload = diagnostic.canonical_bytes(provenance) + b"\n"
    provenance_path.write_bytes(provenance_payload)
    indexed["BUILD_PROVENANCE_RECEIPT"] = {
        "artifact_id": "BUILD_PROVENANCE_RECEIPT",
        "path": provenance_path.as_posix(),
        "sha256": diagnostic.sha256_id(provenance_payload),
        "size_bytes": len(provenance_payload),
    }
    artifacts = [indexed[identifier] for identifier in diagnostic.ALLOCATION_ARTIFACT_IDS]
    allocation = {
        "artifacts": artifacts,
        "container": {
            "image_digest": environment["container_image_digest"],
            "runtime": environment["container_runtime"]["name"],
            "runtime_version": environment["container_runtime"]["version"],
        },
        "resources": {
            "available_processors": 2,
            "cgroup_mode": "V2",
            "cpu_max": "200000 100000",
            "cpuset_cpus_effective": "0-1",
            "memory_max": "8589934592",
        },
        "jdk_tree": {
            **diagnostic.directory_inventory(root / "jdk"),
            "root": (root / "jdk").as_posix(),
        },
        "schema_version": diagnostic.SCHEMA_VERSION,
        "source": manifest["source"],
        "type_name": diagnostic.ALLOCATION_TYPE,
    }
    allocation_path = tmp_path / "allocation.json"
    allocation_payload = diagnostic.canonical_bytes(allocation) + b"\n"
    allocation_path.write_bytes(allocation_payload)
    record = {
        "path": allocation_path.as_posix(),
        "sha256": diagnostic.sha256_id(allocation_payload),
        "size_bytes": len(allocation_payload),
    }
    environment["allocation_manifest"] = record
    return allocation, record


def allocation_plan_fixture(tmp_path: Path) -> tuple[dict[str, object], Path]:
    source_root = tmp_path / "assembler-source"
    source_root.mkdir()
    allocation_root = tmp_path / "assembled-allocation"
    relative_outputs = [
        "corpus.bin",
        "sidecar-diagnostic-tests.jar",
        "jdk/bin/java",
        "jdk/bin/jfr",
        "libdelta_ffi.so",
        "delta_runtime_sidecar",
        "bin/strace",
        "jdk/lib/jfr/profile.jfc",
    ]
    jfr_profile = (
        "<configuration>"
        + "".join(
            f'<event name="{name}"><setting name="enabled">true</setting></event>'
            for name in allocation_assembler.REQUIRED_JFR_EVENTS
        )
        + "</configuration>"
    )
    command = (
        "from pathlib import Path;"
        f"r=Path({str(allocation_root)!r});"
        f"names={relative_outputs!r};"
        "[(r/n).parent.mkdir(parents=True,exist_ok=True) for n in names];"
        "[(r/n).write_bytes((n+'\\n').encode()) for n in names];"
        f"(r/'jdk/lib/jfr/profile.jfc').write_text({jfr_profile!r});"
        "[(r/n).chmod(0o755) for n in "
        "['jdk/bin/java','jdk/bin/jfr','delta_runtime_sidecar','bin/strace']]"
    )
    plan: dict[str, object] = {
        "allocation_manifest_path": (tmp_path / "assembled-allocation.json").as_posix(),
        "allocation_root": allocation_root.as_posix(),
        "container": {
            "image_digest": "sha256:" + "b" * 64,
            "runtime": "docker",
            "runtime_version": "unit-test-runtime",
        },
        "invocation": {
            "argv": [str(Path(sys.executable).resolve()), "-c", command],
            "environment": {key: value for key, value in os.environ.items() if value},
            "environment_mode": "REPLACE",
            "working_directory": source_root.resolve().as_posix(),
        },
        "resources": {
            "available_processors": 2,
            "cgroup_mode": "V2",
            "cpu_max": "200000 100000",
            "cpuset_cpus_effective": "0-1",
            "memory_max": "8589934592",
        },
        "schema_version": diagnostic.SCHEMA_VERSION,
        "source": {
            "commit": "1" * 40,
            "repository": diagnostic.SOURCE_REPOSITORY,
            "tree": "2" * 40,
        },
        "type_name": allocation_assembler.PLAN_TYPE,
    }
    return plan, source_root


def test_cgroup_v1_allocation_is_normalized_without_claiming_v2(tmp_path: Path) -> None:
    mount = tmp_path / "cgroup"
    relative = Path("docker/frozen")
    cpu = mount / "cpu" / relative
    cpuset = mount / "cpuset" / relative
    memory = mount / "memory" / relative
    for path in (cpu, cpuset, memory):
        path.mkdir(parents=True)
    proc = tmp_path / "self.cgroup"
    proc.write_text(
        "2:cpu,cpuacct:/docker/frozen\n1:cpuset:/docker/frozen\n5:memory:/docker/frozen\n",
        encoding="ascii",
    )
    mountinfo = tmp_path / "mountinfo"
    cpu_mount = cpu.as_posix().removesuffix("/docker/frozen")
    cpuset_mount = cpuset.as_posix().removesuffix("/docker/frozen")
    memory_mount = memory.as_posix().removesuffix("/docker/frozen")
    mountinfo.write_text(
        f"1 0 0:1 / {cpu_mount} rw - cgroup cgroup rw,cpu,cpuacct\n"
        f"2 0 0:2 / {cpuset_mount} rw - cgroup cgroup rw,cpuset\n"
        f"3 0 0:3 / {memory_mount} rw - cgroup cgroup rw,memory\n",
        encoding="ascii",
    )
    (cpu / "cpu.cfs_quota_us").write_text("400000\n", encoding="ascii")
    (cpu / "cpu.cfs_period_us").write_text("100000\n", encoding="ascii")
    (cpu / "cpu.stat").write_text(
        "nr_periods 10\nnr_throttled 2\nthrottled_time 3000\n", encoding="ascii"
    )
    (cpuset / "cpuset.cpus").write_text("0-3\n", encoding="ascii")
    (memory / "memory.usage_in_bytes").write_text("4096\n", encoding="ascii")
    (memory / "memory.limit_in_bytes").write_text("8589934592\n", encoding="ascii")

    layout = runner.cgroup_layout(proc, mountinfo)
    assert layout is not None and layout.mode == "V1"
    values = runner.normalized_cgroup_values(layout)
    assert values["cpu.max"] == {"status": "AVAILABLE", "value": "400000 100000"}
    assert values["cpuset.cpus.effective"] == {"status": "AVAILABLE", "value": "0-3"}
    assert values["memory.max"] == {"status": "AVAILABLE", "value": "8589934592"}
    assert values["cpu.stat"]["value"]["throttled_time"] == 3000


def test_cgroup_v2_allocation_remains_exact(tmp_path: Path) -> None:
    mount = tmp_path / "cgroup"
    group = mount / "frozen"
    group.mkdir(parents=True)
    proc = tmp_path / "self.cgroup"
    proc.write_text("0::/frozen\n", encoding="ascii")
    mountinfo = tmp_path / "mountinfo"
    mountinfo.write_text(
        f"1 0 0:1 / {mount.as_posix()} rw - cgroup2 cgroup rw\n",
        encoding="ascii",
    )
    (group / "cpu.max").write_text("200000 100000\n", encoding="ascii")
    (group / "cpu.stat").write_text(
        "usage_usec 5\nnr_periods 1\nnr_throttled 0\nthrottled_usec 0\n",
        encoding="ascii",
    )
    (group / "cpuset.cpus.effective").write_text("4-5\n", encoding="ascii")
    (group / "memory.current").write_text("2048\n", encoding="ascii")
    (group / "memory.max").write_text("4294967296\n", encoding="ascii")

    layout = runner.cgroup_layout(proc, mountinfo)
    assert layout is not None and layout.mode == "V2"
    values = runner.normalized_cgroup_values(layout)
    assert values["cpu.max"] == {"status": "AVAILABLE", "value": "200000 100000"}
    assert values["cpuset.cpus.effective"] == {"status": "AVAILABLE", "value": "4-5"}
    assert values["cpu.stat"]["value"]["usage_usec"] == 5


def test_cgroup_v1_mount_root_equal_to_membership_resolves_mountpoint(tmp_path: Path) -> None:
    mount = tmp_path / "cgroup"
    for controller in ("cpu", "cpuset", "memory"):
        (mount / controller).mkdir(parents=True)
    proc = tmp_path / "self.cgroup"
    proc.write_text(
        "2:cpu,cpuacct:/docker/not-visible\n"
        "1:cpuset:/docker/not-visible\n"
        "5:memory:/docker/not-visible\n",
        encoding="ascii",
    )
    mountinfo = tmp_path / "mountinfo"
    cpu_mount = (mount / "cpu").as_posix()
    cpuset_mount = (mount / "cpuset").as_posix()
    memory_mount = (mount / "memory").as_posix()
    mountinfo.write_text(
        f"1 0 0:1 /docker/not-visible {cpu_mount} rw - cgroup cgroup rw,cpu,cpuacct\n"
        f"2 0 0:2 /docker/not-visible {cpuset_mount} rw - cgroup cgroup rw,cpuset\n"
        f"3 0 0:3 /docker/not-visible {memory_mount} rw - cgroup cgroup rw,memory\n",
        encoding="ascii",
    )

    layout = runner.cgroup_layout(proc, mountinfo)
    assert layout is not None
    assert layout.mode == "V1"
    assert (layout.cpu, layout.cpuset, layout.memory) == tuple(
        (mount / name).resolve() for name in ("cpu", "cpuset", "memory")
    )
    assert [item.mount_root for item in layout.memberships] == [
        "/docker/not-visible",
        "/docker/not-visible",
        "/docker/not-visible",
    ]


def test_cgroup_v1_never_falls_back_to_unrelated_controller_root(tmp_path: Path) -> None:
    mount = tmp_path / "cgroup"
    for controller in ("cpu", "cpuset", "memory"):
        (mount / controller).mkdir(parents=True)
    proc = tmp_path / "self.cgroup"
    proc.write_text(
        "2:cpu,cpuacct:/docker/process\n1:cpuset:/docker/process\n5:memory:/docker/process\n",
        encoding="ascii",
    )
    mountinfo = tmp_path / "mountinfo"
    mountinfo.write_text(
        f"1 0 0:1 /other {(mount / 'cpu').as_posix()} rw - cgroup cgroup rw,cpu,cpuacct\n"
        f"2 0 0:2 /other {(mount / 'cpuset').as_posix()} rw - cgroup cgroup rw,cpuset\n"
        f"3 0 0:3 /other {(mount / 'memory').as_posix()} rw - cgroup cgroup rw,memory\n",
        encoding="ascii",
    )
    assert runner.cgroup_layout(proc, mountinfo) is None


def valid_lane_events(
    *, profile: str = "EMBEDDED_FFM", duration: int = 1, processors: int = 2
) -> list[dict[str, object]]:
    count = duration * diagnostic.OFFER_RATE
    roots = [diagnostic.sha256_id(f"state-{index}".encode()) for index in range(count + 1)]
    events: list[dict[str, object]] = [
        {
            "available_processors": processors,
            "duration_seconds": duration,
            "event_type": "LANE_START",
            "initial_durable_sequence": 1_007,
            "initial_state_root": roots[0],
            "monotonic_anchor_ns": 900_000_000,
            "offers_per_second": diagnostic.OFFER_RATE,
            "process_id": 1234,
            "profile_id": profile,
            "source_root": "/source-s",
            "wall_anchor_ns": 1_700_000_000_000_000_000,
            "warmup_completed_operations": diagnostic.WARMUP_OPERATIONS,
        }
    ]
    for ordinal in range(count):
        scheduled = 1_000_000_000 + ordinal * 10_000_000
        events.append(
            {
                "actual_offer_ns": scheduled,
                "actual_wall_time_ns": 1_700_000_000_000_000_000 + scheduled,
                "admission_accepted": True,
                "event_type": "OFFER",
                "harness_preparation_overran_slot": False,
                "missed_slot": False,
                "offer_ordinal": ordinal,
                "preparation_latency_ns": 0,
                "process_cpu_delta_ns": {"status": "AVAILABLE", "value": 1},
                "profile_id": profile,
                "request_id": f"request-{ordinal}",
                "scheduled_offer_ns": scheduled,
                "scheduler_lateness_ns": 0,
                "scheduler_thread_cpu_delta_ns": {"status": "AVAILABLE", "value": 1},
                "schedstat_delta": {
                    "status": "AVAILABLE",
                    "value": {"running_ns": 1, "timeslices": 1, "waiting_ns": 0},
                },
                "wal_before": {
                    "modified_time_millis": 1,
                    "observed_at_ns": scheduled,
                    "present": True,
                    "size_bytes": 1_000 + ordinal,
                },
                "wakeup_lateness_ns": 0,
                "wakeup_ns": scheduled,
            }
        )
    for ordinal in range(count):
        events.append(
            {
                "completed_at_ns": 1_000_000_100 + ordinal * 10_000_000,
                "completed_wall_time_ns": 1_700_000_001_000_000_100 + ordinal * 10_000_000,
                "durable_sequence": 1_008 + ordinal,
                "event_type": "COMPLETION",
                "native_phase_latency_ns": 50,
                "next_state_root": roots[ordinal + 1],
                "offer_ordinal": ordinal,
                "operation_latency_ns": 100,
                "prior_state_root": roots[ordinal],
                "profile_id": profile,
                "request_id": f"request-{ordinal}",
                "wal_after": {
                    "modified_time_millis": 2,
                    "observed_at_ns": 1_000_000_101 + ordinal * 10_000_000,
                    "present": True,
                    "size_bytes": 2_000 + ordinal,
                },
            }
        )
    events.append(
        {
            "completed_operations": count,
            "event_type": "LANE_END",
            "final_durable_sequence": 1_007 + count,
            "final_state_root": roots[-1],
            "monotonic_ns": 3_000_000_000,
            "profile_id": profile,
            "terminal_state_validated": True,
            "wall_time_ns": 1_700_000_003_000_000_000,
        }
    )
    return events


def telemetry(*, missing: str | None = None) -> dict[str, object]:
    result: dict[str, object] = {
        item: {"status": "AVAILABLE", "value": {"artifact": item}}
        for item in diagnostic.MANDATORY_COLLECTORS
    }
    if missing is not None:
        result[missing] = {"reason": "synthetic unavailable collector", "status": "NOT_AVAILABLE"}
    return result


def missed_slot(
    *,
    missing: str | None = None,
    cgroup: bool = False,
    cpu_or_io_psi: bool = False,
    harness: bool = False,
    host_fault: bool = False,
    java_pause: bool = False,
    not_consuming_cpu: bool = False,
    run_queue: bool = False,
    sustained_cpu: bool = False,
    wal_fsync: bool = False,
) -> dict[str, object]:
    return {
        "actual_offer_ns": 20_000_001,
        "event_type": "MISSED_SLOT",
        "mandatory_telemetry": telemetry(missing=missing),
        "predicates": {
            "cgroup_throttling_overlap": cgroup,
            "cpu_or_io_psi_overlap": cpu_or_io_psi,
            "harness_or_timer_defect_observed": harness,
            "host_hardware_fault_overlap": host_fault,
            "java_pause_or_compiler_overlap": java_pause,
            "process_runnable_not_continuously_consuming_cpu": not_consuming_cpu,
            "run_queue_starvation_overlap": run_queue,
            "sustained_target_runtime_cpu_demand": sustained_cpu,
            "wal_or_fsync_stall_overlap": wal_fsync,
        },
        "scheduled_offer_ns": 10_000_000,
        "scheduler_lateness_ns": 10_000_001,
    }


def lanes(*slots: dict[str, object]) -> list[dict[str, object]]:
    return [
        {"java_involved": True, "missed_slots": list(slots), "profile_id": "EMBEDDED_FFM"},
        {"java_involved": True, "missed_slots": [], "profile_id": "ISOLATED_SIDECAR"},
    ]


def test_example_validates_but_is_never_executable() -> None:
    manifest = example_manifest()
    diagnostic.validate_manifest(manifest, executable=False)
    with pytest.raises(diagnostic.DiagnosticError, match="MANIFEST_STATE"):
        diagnostic.validate_manifest(manifest, executable=True)


def test_java_offer_timestamp_is_adjacent_to_real_adapter_call() -> None:
    source = JAVA_CAPTURE.read_text(encoding="utf-8")
    assert re.search(
        r"var actual = System\.nanoTime\(\);\s*"
        r"var submission = adapter\.tryExecute\(command, actual\);",
        source,
    )
    assert "var wakeupLateness = checkedElapsed(wakeup, scheduled" in source
    assert "lateness >= interval && wakeupLateness < interval" in source
    assert '"delta_runtime_submit_receipt_borrowed_v1"' in source
    assert "ABI_FEATURE_SUBMIT_RECEIPT_V1 = 16L" in source
    assert "NO_NATIVE_SEQUENCE" not in source
    assert "embedded native submit receipt has no durable sequence" in source
    assert 'event.put("initial_durable_sequence", cursor.durableSequence())' in source
    assert 'event.put("initial_state_root", cursor.stateRoot())' in source


def test_host_wrapper_fails_closed_on_stale_receipts_before_container_start() -> None:
    wrapper = HOST_WRAPPER.read_text(encoding="utf-8")
    collector = HOST_COLLECTOR.read_text(encoding="utf-8")
    stale_check = "Preregistered campaign artifact already exists; no stale receipt may be reset"
    assert wrapper.index(stale_check) < wrapper.index("Invoke-Docker $runArguments")
    assert wrapper.index("$recoverTerminalOnly") < wrapper.index("Invoke-Docker $runArguments")
    assert wrapper.index('"--recover-terminal"') < wrapper.index('"--preflight-only"')
    assert wrapper.index('"--recover-terminal"') < wrapper.index('"--arm-only"')
    assert wrapper.index('"--recover-terminal"') < wrapper.index("$collectorJob = Start-Job")
    assert wrapper.index("return", wrapper.index('"--recover-terminal"')) < wrapper.index(
        '"--preflight-only"'
    )
    assert wrapper.index('"--preflight-only"') < wrapper.index('"--arm-only"')
    assert wrapper.index('"--arm-only"') < wrapper.index("$collectorJob = Start-Job")
    assert "([int]$manifest.environment.host_telemetry_wait_seconds + 300)" in wrapper
    assert '"--fail-armed"' in wrapper
    assert wrapper.index("catch {") > wrapper.index('"--arm-only"')
    assert '@("attempt", "started", "terminal", "completed", "failed")' in wrapper
    assert "$attemptHost" in wrapper
    assert "$armedByThisInvocation = $true" in wrapper
    assert (
        "if ($armedByThisInvocation -and (Test-Path -LiteralPath $attemptHost -PathType Leaf))"
        in wrapper
    )
    attempt_guard = "The runner has not published its durable attempt seal"
    assert collector.index(attempt_guard) < collector.index("Write-ExclusiveJson $ReceiptPath")
    assert '"ARMED_ONE_SHOT_NO_RERUN"' in collector
    assert "[IO.FileMode]::CreateNew" in collector
    assert "Host receipt already exists; this campaign cannot be retried" in collector
    assert "Host telemetry already exists; this campaign cannot be retried" in collector
    assert "Lanes-complete handshake already exists; this campaign cannot be retried" in collector
    assert "$successfulQueries -ne $Providers.Count" in collector
    assert "Not every requested Windows event provider was queryable" in collector
    assert "Remove-Item" not in wrapper
    assert "Remove-Item" not in collector


def test_published_schemas_match_the_strict_contract(tmp_path: Path) -> None:
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads((DIAGNOSTICS / "sidecar-diagnostic-manifest.schema.json").read_bytes())
    validator = jsonschema.Draft202012Validator(schema)
    validator.check_schema(schema)
    validator.validate(example_manifest())
    invalid = example_manifest()
    invalid["environment"]["unexpected"] = True
    with pytest.raises(jsonschema.ValidationError):
        validator.validate(invalid)

    allocation_schema = json.loads(
        (DIAGNOSTICS / "sidecar-diagnostic-allocation.schema.json").read_bytes()
    )
    allocation_validator = jsonschema.Draft202012Validator(allocation_schema)
    allocation_validator.check_schema(allocation_schema)
    allocation, _ = allocation_fixture(tmp_path, example_manifest())
    allocation_validator.validate(allocation)
    provenance_schema = json.loads(
        (DIAGNOSTICS / "sidecar-diagnostic-build-provenance.schema.json").read_bytes()
    )
    provenance_validator = jsonschema.Draft202012Validator(provenance_schema)
    provenance_validator.check_schema(provenance_schema)
    provenance_path = Path(allocation["artifacts"][0]["path"])
    provenance_validator.validate(json.loads(provenance_path.read_bytes()))
    for name in (
        "sidecar-diagnostic-allocation-plan.schema.json",
        "sidecar-diagnostic-evidence.schema.json",
        "sidecar-diagnostic-host-receipt.schema.json",
        "sidecar-diagnostic-host-telemetry.schema.json",
    ):
        extra_schema = json.loads((DIAGNOSTICS / name).read_bytes())
        jsonschema.Draft202012Validator.check_schema(extra_schema)
    plan_schema = json.loads(
        (DIAGNOSTICS / "sidecar-diagnostic-allocation-plan.schema.json").read_bytes()
    )
    plan_directory = tmp_path / "plan-fixture"
    plan_directory.mkdir()
    plan, _ = allocation_plan_fixture(plan_directory)
    jsonschema.Draft202012Validator(plan_schema).validate(plan)
    allocation["artifacts"][0]["artifact_id"] = "SUBSTITUTED"
    with pytest.raises(jsonschema.ValidationError):
        allocation_validator.validate(allocation)


def test_allocation_artifacts_bind_every_lane_path_before_seal(tmp_path: Path) -> None:
    manifest = example_manifest()
    allocation, record = allocation_fixture(tmp_path, manifest)
    loaded = diagnostic.load_and_verify_allocation(record, manifest)
    assert loaded == allocation
    evidence_root = tmp_path / "fresh-evidence"
    prepared = runner.prepare_lanes(
        manifest,
        loaded,
        source_root=tmp_path,
        evidence_root=evidence_root,
    )
    assert [item.profile for item in prepared] == diagnostic.PROFILE_ORDER
    assert not evidence_root.exists()


def test_lane_and_probe_subprocesses_use_only_the_recorded_replacement_environment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("JAVA_TOOL_OPTIONS", "-javaagent:/unregistered-agent.jar")
    monkeypatch.setenv("JDK_JAVA_OPTIONS", "-XX:StartFlightRecording=filename=unregistered.jfr")
    monkeypatch.setenv("LD_PRELOAD", "/unregistered/interposer.so")
    manifest = example_manifest()
    allocation, _ = allocation_fixture(tmp_path, manifest)
    prepared = runner.prepare_lanes(
        manifest,
        allocation,
        source_root=tmp_path,
        evidence_root=tmp_path / "evidence",
    )
    forbidden = {"JAVA_TOOL_OPTIONS", "JDK_JAVA_OPTIONS", "LD_PRELOAD"}
    expected_base = {
        key: value.replace("{ALLOCATION_ROOT}", str(manifest["environment"]["allocation_root"]))
        for key, value in diagnostic.LANE_ENVIRONMENT_TEMPLATE.items()
    }
    for lane in prepared:
        assert not forbidden & set(lane.environment)
        assert lane.environment == {
            **expected_base,
            "DELTA_DIAGNOSTIC_AUTHORITY": "DIAGNOSTIC_ONLY",
            "DELTA_DIAGNOSTIC_EVENT_LOG": str(lane.lane_directory / "operations.jsonl"),
            "DELTA_DIAGNOSTIC_OFFERS_PER_SECOND": str(diagnostic.OFFER_RATE),
            "DELTA_DIAGNOSTIC_PROFILE": lane.profile,
        }
        assert lane.working_directory == tmp_path.resolve()

    probe_environment = {
        **diagnostic.git_replacement_environment(),
        "DIAGNOSTIC_ALLOWED_SENTINEL": "present",
    }
    receipt, stdout, _ = runner.invocation_probe(
        [
            str(Path(sys.executable).resolve()),
            "-c",
            (
                "import os,sys;"
                "forbidden={'JAVA_TOOL_OPTIONS','JDK_JAVA_OPTIONS','LD_PRELOAD'};"
                "sys.exit(9) if forbidden & set(os.environ) else "
                "print(os.getcwd()+'|'+os.environ['DIAGNOSTIC_ALLOWED_SENTINEL'])"
            ),
        ],
        environment=probe_environment,
        working_directory=tmp_path,
        expected_exit_codes={0},
        label="UNIT_EXACT_ENVIRONMENT",
    )
    assert stdout.decode().strip() == f"{tmp_path.resolve()}|present"
    assert receipt["environment"] == probe_environment
    assert receipt["environment_mode"] == "REPLACE"
    assert receipt["working_directory"] == str(tmp_path.resolve())
    assert not forbidden & set(receipt["environment"])


def test_git_checkout_receipt_records_exact_argv_environment_and_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    git = diagnostic.shutil.which("git")
    if git is None:
        pytest.skip("git is unavailable")
    repository = tmp_path / "clean-repository"
    repository.mkdir()
    for arguments in (
        ("init",),
        ("config", "user.name", "Diagnostic Test"),
        ("config", "user.email", "diagnostic@example.invalid"),
        ("config", "core.autocrlf", "false"),
    ):
        diagnostic.subprocess.run(
            [git, *arguments], cwd=repository, check=True, capture_output=True
        )
    (repository / "tracked.txt").write_text("tracked\n", encoding="utf-8")
    diagnostic.subprocess.run([git, "add", "tracked.txt"], cwd=repository, check=True)
    diagnostic.subprocess.run(
        [git, "commit", "-m", "fixture"], cwd=repository, check=True, capture_output=True
    )
    monkeypatch.setenv("JAVA_TOOL_OPTIONS", "-javaagent:/must-not-leak.jar")
    receipt, _ = diagnostic.git_checkout_receipt(repository)
    expected_environment = diagnostic.git_replacement_environment()
    assert receipt["git_invocations"]
    for invocation in receipt["git_invocations"]:
        assert Path(invocation["argv"][0]).is_absolute()
        assert invocation["environment"] == expected_environment
        assert invocation["environment_mode"] == "REPLACE"
        assert invocation["working_directory"] == str(repository.resolve())
        assert "JAVA_TOOL_OPTIONS" not in invocation["environment"]


@pytest.mark.parametrize(
    ("target", "code"),
    [
        ("java", "LANE_JAVA_ARTIFACT_MISMATCH"),
        ("classpath", "LANE_CLASSPATH_ARTIFACT_MISMATCH"),
        ("corpus", "LANE_CORPUS_ARTIFACT_MISMATCH"),
        ("native", "LANE_NATIVE_ARTIFACT_MISMATCH"),
        ("sidecar", "LANE_SIDECAR_ARTIFACT_MISMATCH"),
        ("strace", "LANE_STRACE_ARTIFACT_MISMATCH"),
    ],
)
def test_lane_artifact_substitution_fails_before_attempt_seal(
    tmp_path: Path, target: str, code: str
) -> None:
    manifest = example_manifest()
    _, record = allocation_fixture(tmp_path, manifest)
    loaded = diagnostic.load_and_verify_allocation(record, manifest)
    lane_index = 1 if target == "sidecar" else 0
    lane = manifest["lanes"][lane_index]
    if target == "java":
        lane["argv"][0] = "{ALLOCATION_ROOT}/substitute-java"
    elif target == "strace":
        lane["strace_fsync"]["argv_prefix"][0] = "{ALLOCATION_ROOT}/substitute-strace"
    else:
        option = {
            "classpath": "-cp",
            "corpus": "--corpus",
            "native": "--native-library",
            "sidecar": "--sidecar-executable",
        }[target]
        position = lane["argv"].index(option)
        lane["argv"][position + 1] = f"{{ALLOCATION_ROOT}}/substitute-{target}"
    evidence_root = tmp_path / "fresh-evidence"
    with pytest.raises(diagnostic.DiagnosticError, match=code):
        runner.prepare_lanes(
            manifest,
            loaded,
            source_root=tmp_path,
            evidence_root=evidence_root,
        )
    assert not evidence_root.exists()


def test_jfr_must_be_the_hashed_java_sibling(tmp_path: Path) -> None:
    manifest = example_manifest()
    _, record = allocation_fixture(tmp_path, manifest, jfr_name="tools/not-the-java-jfr")
    with pytest.raises(diagnostic.DiagnosticError, match="ALLOCATION_JFR_NOT_JAVA_SIBLING"):
        diagnostic.load_and_verify_allocation(record, manifest)


def test_jdk_inventory_detects_unlisted_tree_mutation(tmp_path: Path) -> None:
    manifest = example_manifest()
    _, record = allocation_fixture(tmp_path, manifest)
    diagnostic.load_and_verify_allocation(record, manifest)
    root = Path(manifest["environment"]["allocation_root"])
    (root / "jdk" / "lib" / "injected.bin").parent.mkdir(parents=True)
    (root / "jdk" / "lib" / "injected.bin").write_bytes(b"unfrozen")
    with pytest.raises(diagnostic.DiagnosticError, match="ALLOCATION_JDK_TREE_MISMATCH"):
        diagnostic.load_and_verify_allocation(record, manifest)


def test_build_provenance_invocation_hash_is_recomputed(tmp_path: Path) -> None:
    manifest = example_manifest()
    allocation, record = allocation_fixture(tmp_path, manifest)
    provenance_record = allocation["artifacts"][0]
    provenance_path = Path(provenance_record["path"])
    provenance = json.loads(provenance_path.read_bytes())
    provenance["invocation"]["argv"].append("--tampered")
    raw = diagnostic.canonical_bytes(provenance) + b"\n"
    provenance_path.write_bytes(raw)
    provenance_record["sha256"] = diagnostic.sha256_id(raw)
    provenance_record["size_bytes"] = len(raw)
    allocation_path = Path(record["path"])
    allocation_raw = diagnostic.canonical_bytes(allocation) + b"\n"
    allocation_path.write_bytes(allocation_raw)
    record["sha256"] = diagnostic.sha256_id(allocation_raw)
    record["size_bytes"] = len(allocation_raw)
    with pytest.raises(diagnostic.DiagnosticError, match="BUILD_PROVENANCE_INVOCATION_MISMATCH"):
        diagnostic.load_and_verify_allocation(record, manifest)


def test_allocation_assembler_builds_seals_and_round_trips_exclusively(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan, source_root = allocation_plan_fixture(tmp_path)
    receipt = {
        "checkout_root": str(source_root.resolve()),
        "commit": plan["source"]["commit"],
        "git_invocations": [synthetic_process_receipt(source_root, "git-probe")],
        "status_porcelain_sha256": diagnostic.sha256_id(b""),
        "tree": plan["source"]["tree"],
    }
    monkeypatch.setattr(
        diagnostic,
        "verify_source_checkout",
        lambda _root, _source: copy.deepcopy(receipt),
    )

    allocation = allocation_assembler.build_and_assemble(plan, source_root)
    manifest_path = Path(plan["allocation_manifest_path"])
    assert (
        allocation_assembler.verify_generated_allocation(plan, source_root, manifest_path)
        == allocation
    )
    provenance_path = Path(plan["allocation_root"]) / "build-provenance.json"
    provenance = json.loads(provenance_path.read_bytes())
    assert provenance["invocation"] == plan["invocation"]
    assert provenance["execution"]["exit_code"] == 0
    assert Path(provenance["execution"]["stdout"]["path"]).is_file()
    assert Path(provenance["execution"]["stderr"]["path"]).is_file()

    with pytest.raises(diagnostic.DiagnosticError, match="ASSEMBLER_ALLOCATION_ROOT_MUST_BE_FRESH"):
        allocation_assembler.build_and_assemble(plan, source_root)

    jar = Path(plan["allocation_root"]) / "sidecar-diagnostic-tests.jar"
    jar.write_bytes(b"tampered")
    with pytest.raises(diagnostic.DiagnosticError, match=r"ARTIFACT_(SIZE|SHA256)"):
        allocation_assembler.verify_generated_allocation(plan, source_root, manifest_path)


def test_allocation_assembler_rejects_disabled_preregistered_jfr_event(tmp_path: Path) -> None:
    java = tmp_path / "jdk" / "bin" / "java"
    java.parent.mkdir(parents=True)
    java.write_bytes(b"java")
    profile = tmp_path / "jdk" / "lib" / "jfr" / "profile.jfc"
    profile.parent.mkdir(parents=True)
    profile.write_text(
        "<configuration>"
        + "".join(
            f'<event name="{name}"><setting name="enabled">'
            f"{'false' if name == 'jdk.SafepointEnd' else 'true'}</setting></event>"
            for name in allocation_assembler.REQUIRED_JFR_EVENTS
        )
        + "</configuration>",
        encoding="utf-8",
    )
    with pytest.raises(
        diagnostic.DiagnosticError,
        match=r"ASSEMBLER_JFR_EVENTS_NOT_ENABLED:jdk\.SafepointEnd",
    ):
        allocation_assembler.verify_jfr_profile(java)


def test_allocation_assembler_rejects_disabled_jfr_event_before_sealing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    plan, source_root = allocation_plan_fixture(tmp_path)
    invocation = plan["invocation"]
    assert isinstance(invocation, dict)
    argv = invocation["argv"]
    assert isinstance(argv, list)
    enabled = '<event name="jdk.SafepointEnd"><setting name="enabled">true</setting></event>'
    disabled = enabled.replace(">true<", ">false<")
    argv[-1] = str(argv[-1]).replace(enabled, disabled)
    receipt = {
        "checkout_root": str(source_root.resolve()),
        "commit": plan["source"]["commit"],
        "git_invocations": [synthetic_process_receipt(source_root, "git-probe")],
        "status_porcelain_sha256": diagnostic.sha256_id(b""),
        "tree": plan["source"]["tree"],
    }
    monkeypatch.setattr(
        diagnostic,
        "verify_source_checkout",
        lambda _root, _source: copy.deepcopy(receipt),
    )

    with pytest.raises(
        diagnostic.DiagnosticError,
        match=r"ASSEMBLER_JFR_EVENTS_NOT_ENABLED:jdk\.SafepointEnd",
    ):
        allocation_assembler.build_and_assemble(plan, source_root)
    allocation_root = Path(str(plan["allocation_root"]))
    assert not (allocation_root / "build-provenance.json").exists()
    assert not Path(str(plan["allocation_manifest_path"])).exists()


def test_preflight_rejects_nonexecutable_exact_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = example_manifest()
    allocation, _ = allocation_fixture(tmp_path, manifest)
    original_access = runner.os.access

    def access(path: object, mode: int) -> bool:
        if mode == runner.os.X_OK and Path(str(path)).name == "java":
            return False
        return original_access(path, mode)

    monkeypatch.setattr(runner.os, "access", access)
    with pytest.raises(
        diagnostic.DiagnosticError,
        match="PREFLIGHT_ARTIFACT_NOT_EXECUTABLE:JAVA_EXECUTABLE",
    ):
        runner.preflight_allocation(
            allocation,
            allocation_root=Path(manifest["environment"]["allocation_root"]),
        )


def test_preflight_requires_native_library_readability_but_not_execute_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = example_manifest()
    allocation, _ = allocation_fixture(tmp_path, manifest)
    native = Path(str(allocation["artifacts"][5]["path"]))
    executable_checks: list[Path] = []

    def access(path: object, mode: int) -> bool:
        resolved = Path(str(path))
        if mode == runner.os.X_OK:
            executable_checks.append(resolved)
            return resolved != native
        return True

    monkeypatch.setattr(runner.os, "access", access)
    monkeypatch.setattr(runner, "mount_is_read_only", lambda _path: True)
    with pytest.raises(diagnostic.DiagnosticError, match="PREFLIGHT_LANES_REQUIRED"):
        runner.preflight_allocation(
            allocation,
            allocation_root=Path(manifest["environment"]["allocation_root"]),
        )
    assert native not in executable_checks


def test_failed_non_consuming_preflight_creates_no_receipt_or_campaign_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = example_manifest()
    manifest["manifest_state"] = diagnostic.FROZEN_STATE
    manifest["diagnostic_campaign_id"] = "unit-non-consuming-preflight"
    manifest["source"] = {
        "commit": "1" * 40,
        "repository": diagnostic.SOURCE_REPOSITORY,
        "tree": "2" * 40,
    }
    source_root = tmp_path / "source"
    manifest_root = tmp_path / "manifest"
    evidence_parent = tmp_path / "evidence-parent"
    ledger_root = tmp_path / "ledger"
    exchange_root = tmp_path / "exchange"
    for path in (source_root, manifest_root, evidence_parent, ledger_root, exchange_root):
        path.mkdir()
    manifest["evidence_directory"] = (evidence_parent / "campaign").as_posix()
    environment = manifest["environment"]
    environment["campaign_ledger_directory"] = ledger_root.as_posix()
    environment["host_receipt_path"] = (exchange_root / "receipt.json").as_posix()
    environment["host_telemetry_path"] = (exchange_root / "telemetry.json").as_posix()
    _, _ = allocation_fixture(tmp_path, manifest)
    manifest_path = manifest_root / "frozen-manifest.json"
    runner.canonical_write(manifest_path, manifest)
    source_receipt = synthetic_checkout_receipt(source_root, manifest["source"])
    manifest_receipt = {
        **synthetic_checkout_receipt(manifest_root, manifest["source"]),
        "manifest_blob": "9" * 40,
        "manifest_relative_path": manifest_path.name,
    }
    monkeypatch.setattr(
        diagnostic,
        "verify_source_checkout",
        lambda _root, _source: copy.deepcopy(source_receipt),
    )
    monkeypatch.setattr(
        diagnostic,
        "verify_manifest_checkout",
        lambda _path, _root: copy.deepcopy(manifest_receipt),
    )
    monkeypatch.setattr(runner, "mount_is_read_only", lambda _path: True)

    def fail_after_immutable_inputs(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise diagnostic.DiagnosticError("LATE_PREFLIGHT_FAILURE")

    monkeypatch.setattr(runner, "preflight_allocation", fail_after_immutable_inputs)
    preflight_receipt = tmp_path / "preflight.json"
    with pytest.raises(diagnostic.DiagnosticError, match="LATE_PREFLIGHT_FAILURE"):
        runner.preflight_campaign(
            manifest_path,
            manifest_root,
            source_root,
            preflight_receipt,
        )

    assert not preflight_receipt.exists()
    assert not Path(manifest["evidence_directory"]).exists()
    assert not any(ledger_root.iterdir())
    assert not any(exchange_root.iterdir())


def test_non_consuming_preflight_receipt_cannot_alias_the_campaign_ledger(
    tmp_path: Path,
) -> None:
    manifest = example_manifest()
    ledger = tmp_path / "ledger"
    exchange = tmp_path / "exchange"
    manifest["evidence_directory"] = (tmp_path / "evidence" / "campaign").as_posix()
    manifest["environment"]["campaign_ledger_directory"] = ledger.as_posix()
    manifest["environment"]["host_receipt_path"] = (exchange / "receipt.json").as_posix()
    with pytest.raises(
        diagnostic.DiagnosticError,
        match="PREFLIGHT_RECEIPT_PERSISTENT_LOCATION:LEDGER",
    ):
        runner.validate_preflight_receipt_location(ledger / "campaign.attempt.json", manifest)


def test_arm_seal_is_the_exclusive_consuming_transition_before_host_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    manifest = example_manifest()
    manifest["manifest_state"] = diagnostic.FROZEN_STATE
    manifest["diagnostic_campaign_id"] = "unit-exclusive-arm-before-receipt"
    manifest["source"] = {
        "commit": "1" * 40,
        "repository": diagnostic.SOURCE_REPOSITORY,
        "tree": "2" * 40,
    }
    source_root = tmp_path / "source"
    manifest_root = tmp_path / "manifest"
    evidence_parent = tmp_path / "evidence-parent"
    ledger_root = tmp_path / "ledger"
    exchange_root = tmp_path / "exchange"
    for path in (source_root, manifest_root, evidence_parent, ledger_root, exchange_root):
        path.mkdir()
    manifest["evidence_directory"] = (evidence_parent / "campaign").as_posix()
    environment = manifest["environment"]
    environment["campaign_ledger_directory"] = ledger_root.as_posix()
    receipt_path = exchange_root / "receipt.json"
    environment["host_receipt_path"] = receipt_path.as_posix()
    environment["host_telemetry_path"] = (exchange_root / "telemetry.json").as_posix()
    _, allocation_record = allocation_fixture(tmp_path, manifest)
    manifest_path = manifest_root / "frozen-manifest.json"
    runner.canonical_write(manifest_path, manifest)
    source_receipt = synthetic_checkout_receipt(source_root, manifest["source"])
    manifest_receipt = {
        **synthetic_checkout_receipt(manifest_root, manifest["source"]),
        "manifest_blob": "8" * 40,
        "manifest_relative_path": manifest_path.name,
    }
    preflight = {
        "allocation_manifest_sha256": allocation_record["sha256"],
        "allocation_preflight": {"synthetic": True},
        "consumes_campaign": False,
        "created_at_utc": "2020-01-01T00:00:00Z",
        "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
        "live_allocation": {"synthetic": True},
        "manifest_checkout": manifest_receipt,
        "manifest_sha256": diagnostic.sha256_id(diagnostic.canonical_bytes(manifest)),
        "schema_version": diagnostic.SCHEMA_VERSION,
        "source": manifest["source"],
        "source_checkout": source_receipt,
        "state": runner.PREFLIGHT_RECEIPT_STATE,
        "type_name": runner.PREFLIGHT_RECEIPT_TYPE,
    }
    preflight_path = tmp_path / "preflight.json"
    runner.canonical_write(preflight_path, preflight)
    monkeypatch.setattr(runner, "mount_is_read_only", lambda _path: True)
    monkeypatch.setattr(
        runner,
        "validate_preflight_receipt",
        lambda value, **_kwargs: value,
    )
    monkeypatch.setattr(
        diagnostic,
        "verify_source_checkout",
        lambda _root, _source: copy.deepcopy(source_receipt),
    )
    monkeypatch.setattr(
        diagnostic,
        "verify_manifest_checkout",
        lambda _path, _root: copy.deepcopy(manifest_receipt),
    )

    attempt = runner.arm_campaign(
        manifest_path,
        manifest_root,
        source_root,
        preflight_path,
    )
    attempt_path = ledger_root / f"{manifest['diagnostic_campaign_id']}.attempt.json"
    assert attempt_path.is_file()
    assert attempt["state"] == runner.ATTEMPT_SEAL_STATE
    assert attempt["preflight_receipt_sha256"] == diagnostic.sha256_id(preflight_path.read_bytes())
    assert not receipt_path.exists()
    assert preflight["consumes_campaign"] is False
    with pytest.raises(diagnostic.DiagnosticError, match="CAMPAIGN_LEDGER_ALREADY_EXISTS"):
        runner.arm_campaign(
            manifest_path,
            manifest_root,
            source_root,
            preflight_path,
        )


def test_post_arm_preexecution_failure_is_terminally_sealed(tmp_path: Path) -> None:
    manifest = example_manifest()
    manifest["manifest_state"] = diagnostic.FROZEN_STATE
    manifest["diagnostic_campaign_id"] = "unit-post-arm-terminal-failure"
    manifest["source"] = {
        "commit": "1" * 40,
        "repository": diagnostic.SOURCE_REPOSITORY,
        "tree": "2" * 40,
    }
    evidence_parent = tmp_path / "evidence"
    evidence_parent.mkdir()
    ledger_root = tmp_path / "ledger"
    ledger_root.mkdir()
    manifest["evidence_directory"] = (evidence_parent / "campaign").as_posix()
    manifest["environment"]["campaign_ledger_directory"] = ledger_root.as_posix()
    manifest_path = tmp_path / "manifest.json"
    runner.canonical_write(manifest_path, manifest)
    manifest_canonical = diagnostic.canonical_bytes(manifest)
    attempt = {
        "allocation_manifest_sha256": manifest["environment"]["allocation_manifest"]["sha256"],
        "authority": "DIAGNOSTIC_ONLY",
        "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
        "manifest_checkout": {},
        "manifest_sha256": diagnostic.sha256_id(manifest_canonical),
        "preflight_receipt_sha256": diagnostic.sha256_id(b"preflight"),
        "schema_version": diagnostic.SCHEMA_VERSION,
        "source": manifest["source"],
        "source_checkout": {},
        "started_at_utc": "2020-01-01T00:00:00Z",
        "state": runner.ATTEMPT_SEAL_STATE,
        "type_name": runner.ATTEMPT_SEAL_TYPE,
    }
    seals = runner.ledger_paths(ledger_root, manifest["diagnostic_campaign_id"])
    runner.durable_exclusive_write(seals["attempt"], attempt)

    with pytest.raises(diagnostic.DiagnosticError, match="OUTPUT_DIRECTORY_MISMATCH"):
        runner.run_campaign(
            manifest_path,
            tmp_path / "manifest-checkout",
            tmp_path / "source-checkout",
            evidence_parent / "wrong-output",
            tmp_path / "missing-preflight.json",
        )

    assert seals["started"].is_file()
    assert seals["terminal"].is_file()
    assert seals["failed"].is_file()
    assert not seals["completed"].exists()
    terminal = json.loads(seals["terminal"].read_bytes())
    failure = json.loads(seals["failed"].read_bytes())
    assert terminal["outcome"] == "FAILED"
    assert failure["state"] == "FAILED_NO_RERUN"
    assert failure["error_type"] == "DiagnosticError"
    assert failure["execution_started_record_sha256"] == diagnostic.sha256_id(
        seals["started"].read_bytes()
    )


def test_host_sampler_thread_failure_is_rethrown(tmp_path: Path) -> None:
    sampler = runner.HostSampler(tmp_path / "missing-parent" / "telemetry.jsonl", 10)
    sampler.start()
    with pytest.raises(diagnostic.DiagnosticError, match="HOST_SAMPLER_FAILED"):
        sampler.stop()


def test_strace_must_be_fully_parseable_before_becoming_available(tmp_path: Path) -> None:
    trace = tmp_path / "fsync.strace.1"
    trace.write_text(
        "1720000000.123456789 fsync(7) = 0 <0.010000001>\n"
        "1720000000.123456790 +++ exited with 0 +++\n",
        encoding="utf-8",
    )
    parsed = runner.parse_strace_files([trace])
    assert parsed["status"] == "AVAILABLE"
    assert runner.fsync_overlap(
        parsed,
        1_720_000_000_110_000_000,
        1_720_000_000_123_456_789,
        10_000_001,
    )

    trace.write_text("1720000000.123456789 fsync(7 <unfinished ...>\n", encoding="utf-8")
    incomplete = runner.parse_strace_files([trace])
    assert incomplete["status"] == "NOT_AVAILABLE"


def test_jfr_json_requires_complete_selected_event_records() -> None:
    runner.validate_jfr_document({"recording": {"events": []}}, {"jdk.Compilation"})
    with pytest.raises(ValueError, match="values"):
        runner.validate_jfr_document(
            {"recording": {"events": [{"type": "jdk.Compilation"}]}},
            {"jdk.Compilation"},
        )


def test_jfr_selected_families_are_proven_enabled_even_with_zero_events(tmp_path: Path) -> None:
    java = tmp_path / "jdk" / "bin" / "java"
    java.parent.mkdir(parents=True)
    java.write_bytes(b"java")
    profile = tmp_path / "jdk" / "lib" / "jfr" / "profile.jfc"
    profile.parent.mkdir(parents=True)
    selected = ["jdk.GarbageCollection", "jdk.Compilation"]
    profile.write_text(
        "<configuration>"
        '<event name="jdk.GarbageCollection"><setting name="enabled">true</setting></event>'
        '<event name="jdk.Compilation"><setting name="enabled">true</setting></event>'
        "</configuration>",
        encoding="utf-8",
    )
    assert runner.jfr_profile_enabled_events(java, selected) == selected
    runner.validate_jfr_document({"recording": {"events": []}}, set(selected))


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (lambda value: value["schedule"].__setitem__("offers_per_second", 99), "RATE"),
        (
            lambda value: value["schedule"].__setitem__(
                "lane_order", list(reversed(diagnostic.PROFILE_ORDER))
            ),
            "LANE_ORDER",
        ),
        (
            lambda value: value["authority"].__setitem__("selected_profile", "ISOLATED_SIDECAR"),
            "AUTHORITY",
        ),
        (lambda value: value["authority"].__setitem__("assembler_eligible", True), "AUTHORITY"),
    ],
)
def test_manifest_mutations_fail_closed(mutation: object, code: str) -> None:
    manifest = example_manifest()
    mutation(manifest)  # type: ignore[operator]
    with pytest.raises(diagnostic.DiagnosticError, match=code):
        diagnostic.validate_manifest(manifest, executable=False)


def test_zero_misses_has_explicit_non_failure_result() -> None:
    classification, slots = diagnostic.classify_campaign(lanes())
    assert classification == "NO_MISSED_SLOTS_OBSERVED"
    assert slots == []


@pytest.mark.parametrize(
    "slot",
    [
        missed_slot(cgroup=True, not_consuming_cpu=True),
        missed_slot(cpu_or_io_psi=True, not_consuming_cpu=True),
        missed_slot(run_queue=True, not_consuming_cpu=True),
        missed_slot(wal_fsync=True, not_consuming_cpu=True),
        missed_slot(host_fault=True),
    ],
)
def test_observed_overlapping_environment_stall_is_environment_invalid(
    slot: dict[str, object],
) -> None:
    classification, classified = diagnostic.classify_campaign(lanes(slot))
    assert classification == "ENVIRONMENT_INVALID"
    assert classified[0]["classification"] == "ENVIRONMENT_INVALID"


def test_harness_defect_is_independent_of_runtime_capacity() -> None:
    classification, _ = diagnostic.classify_campaign(lanes(missed_slot(harness=True)))
    assert classification == "HARNESS_OR_TIMER_DEFECT"


def test_observed_environment_invalidator_precedes_overlapping_harness_signal() -> None:
    classification, _ = diagnostic.classify_campaign(
        lanes(missed_slot(cgroup=True, harness=True, not_consuming_cpu=True))
    )
    assert classification == "ENVIRONMENT_INVALID"


def test_java_pause_or_compiler_overlap_cannot_be_called_genuine_runtime_demand() -> None:
    classification, _ = diagnostic.classify_campaign(
        lanes(missed_slot(java_pause=True, sustained_cpu=True))
    )
    assert classification == "INCONCLUSIVE"


def test_genuine_runtime_demand_requires_all_mandatory_telemetry() -> None:
    classification, _ = diagnostic.classify_campaign(lanes(missed_slot(sustained_cpu=True)))
    assert classification == "GENUINE_RUNTIME_DEMAND_INDICATOR"

    missing, _ = diagnostic.classify_campaign(
        lanes(
            missed_slot(
                sustained_cpu=True,
                missing="WAL_AND_FSYNC_LATENCY",
            )
        )
    )
    assert missing == "INCONCLUSIVE"


def test_absence_of_stall_is_not_evidence_when_required_telemetry_is_missing() -> None:
    classification, _ = diagnostic.classify_campaign(lanes(missed_slot(missing="CPU_PSI")))
    assert classification == "INCONCLUSIVE"


def test_mixed_root_causes_fail_closed_as_inconclusive() -> None:
    classification, classified = diagnostic.classify_campaign(
        lanes(
            missed_slot(harness=True),
            missed_slot(cgroup=True, not_consuming_cpu=True),
        )
    )
    assert classification == "INCONCLUSIVE"
    assert {item["classification"] for item in classified} == {
        "ENVIRONMENT_INVALID",
        "HARNESS_OR_TIMER_DEFECT",
    }


def test_lateness_arithmetic_is_exact() -> None:
    slot = copy.deepcopy(missed_slot())
    slot["scheduler_lateness_ns"] = 10_000_000
    with pytest.raises(diagnostic.DiagnosticError, match="MISSED_SLOT_ARITHMETIC"):
        diagnostic.classify_campaign(lanes(slot))


def test_late_offer_is_joined_and_cannot_silently_become_zero_misses() -> None:
    late_offer = {
        "actual_offer_ns": 20_000_001,
        "actual_wall_time_ns": 1_000_020_000_001,
        "admission_accepted": True,
        "event_type": "OFFER",
        "harness_preparation_overran_slot": False,
        "missed_slot": True,
        "offer_ordinal": 0,
        "preparation_latency_ns": 1,
        "process_cpu_delta_ns": {"status": "AVAILABLE", "value": 9_000_000},
        "profile_id": "EMBEDDED_FFM",
        "request_id": "request-0",
        "scheduled_offer_ns": 10_000_000,
        "scheduler_lateness_ns": 10_000_001,
        "scheduler_thread_cpu_delta_ns": {"status": "AVAILABLE", "value": 1_000_000},
        "schedstat_delta": {
            "status": "AVAILABLE",
            "value": {"running_ns": 1, "timeslices": 1, "waiting_ns": 0},
        },
        "wal_before": {
            "modified_time_millis": 0,
            "observed_at_ns": 20_000_000,
            "present": False,
            "size_bytes": 0,
        },
        "wakeup_lateness_ns": 10_000_000,
        "wakeup_ns": 20_000_000,
    }
    environment = {
        "cgroup_values": {
            name: {"reason": "synthetic missing", "status": "NOT_AVAILABLE"}
            for name in ("cpu.max", "cpuset.cpus.effective", "memory.current", "memory.max")
        },
        "container_identity": {"reason": "synthetic missing", "status": "NOT_AVAILABLE"},
        "cpu_affinity": {"reason": "synthetic missing", "status": "NOT_AVAILABLE"},
    }
    missed = runner.build_missed_slots(
        [late_offer],
        [],
        environment=environment,
        host_telemetry=runner.pending_host_telemetry(),
        jfr={"reason": "synthetic missing", "status": "NOT_AVAILABLE"},
        trace_files=[],
    )
    assert len(missed) == 1
    classification, _ = diagnostic.classify_campaign(
        [
            {"java_involved": True, "missed_slots": missed, "profile_id": "EMBEDDED_FFM"},
            {"java_involved": True, "missed_slots": [], "profile_id": "ISOLATED_SIDECAR"},
        ]
    )
    assert classification == "INCONCLUSIVE"


def test_harness_preparation_predicate_is_derived_from_wakeup_and_offer() -> None:
    events = valid_lane_events()
    offer = events[1]
    completion = events[1 + diagnostic.OFFER_RATE]
    scheduled = offer["scheduled_offer_ns"]
    assert isinstance(scheduled, int)
    offer["actual_offer_ns"] = scheduled + 10_000_000
    offer["preparation_latency_ns"] = 10_000_000
    offer["scheduler_lateness_ns"] = 10_000_000
    offer["missed_slot"] = True
    offer["harness_preparation_overran_slot"] = True
    completion["completed_at_ns"] = scheduled + 10_000_100
    completion["operation_latency_ns"] = 100
    completion["wal_after"]["observed_at_ns"] = scheduled + 10_000_101
    runner.validate_lane_execution(
        events,
        profile="EMBEDDED_FFM",
        duration=1,
        expected_processors=2,
        exit_code=0,
        timed_out=False,
    )
    offer["harness_preparation_overran_slot"] = False
    with pytest.raises(diagnostic.DiagnosticError, match="LANE_HARNESS_PREPARATION_PREDICATE"):
        runner.validate_lane_execution(
            events,
            profile="EMBEDDED_FFM",
            duration=1,
            expected_processors=2,
            exit_code=0,
            timed_out=False,
        )


def test_lane_requires_cpu_thread_and_schedstat_per_offer() -> None:
    events = valid_lane_events()
    events[1]["scheduler_thread_cpu_delta_ns"] = {
        "reason": "synthetic missing",
        "status": "NOT_AVAILABLE",
    }
    with pytest.raises(diagnostic.DiagnosticError, match="LANE_SCHEDULER_THREAD_CPU_REQUIRED"):
        runner.validate_lane_execution(
            events,
            profile="EMBEDDED_FFM",
            duration=1,
            expected_processors=2,
            exit_code=0,
            timed_out=False,
        )


@pytest.mark.parametrize(
    ("mutation", "error"),
    [
        (
            lambda events: events[-1].__setitem__("monotonic_ns", 899_999_999),
            "LANE_MONOTONIC_END",
        ),
        (
            lambda events: events[-1].__setitem__("wall_time_ns", 1_699_999_999_999_999_999),
            "LANE_WALL_END",
        ),
        (
            lambda events: events[0].__setitem__("monotonic_anchor_ns", 1_000_000_001),
            "LANE_MONOTONIC_INTERVAL",
        ),
        (
            lambda events: events[1].__setitem__("actual_wall_time_ns", 1_699_999_999_999_999_999),
            "LANE_ACTUAL_WALL",
        ),
    ],
)
def test_lane_rejects_clock_values_outside_active_interval(mutation: object, error: str) -> None:
    events = valid_lane_events()
    mutation(events)  # type: ignore[operator]

    with pytest.raises(diagnostic.DiagnosticError, match=error):
        runner.validate_lane_execution(
            events,
            profile="EMBEDDED_FFM",
            duration=1,
            expected_processors=2,
            exit_code=0,
            timed_out=False,
        )


def test_lane_rejects_regressing_completion_clocks() -> None:
    events = valid_lane_events()
    first_completion = events[1 + diagnostic.OFFER_RATE]
    second_completion = events[2 + diagnostic.OFFER_RATE]
    regressing_from = int(second_completion["completed_at_ns"]) + 1
    first_completion["completed_at_ns"] = regressing_from
    first_completion["operation_latency_ns"] = regressing_from - int(events[1]["actual_offer_ns"])
    first_completion["wal_after"]["observed_at_ns"] = regressing_from

    with pytest.raises(diagnostic.DiagnosticError, match="LANE_COMPLETION_MONOTONIC_ORDER"):
        runner.validate_lane_execution(
            events,
            profile="EMBEDDED_FFM",
            duration=1,
            expected_processors=2,
            exit_code=0,
            timed_out=False,
        )

    events = valid_lane_events()
    first_completion = events[1 + diagnostic.OFFER_RATE]
    second_completion = events[2 + diagnostic.OFFER_RATE]
    first_completion["completed_wall_time_ns"] = (
        int(second_completion["completed_wall_time_ns"]) + 1
    )
    with pytest.raises(diagnostic.DiagnosticError, match="LANE_COMPLETION_WALL_ORDER"):
        runner.validate_lane_execution(
            events,
            profile="EMBEDDED_FFM",
            duration=1,
            expected_processors=2,
            exit_code=0,
            timed_out=False,
        )


def test_host_bracketing_uses_only_samples_wholly_outside_lateness() -> None:
    samples = [
        {"sample_begin_monotonic_ns": 1, "sample_end_monotonic_ns": 9},
        {"sample_begin_monotonic_ns": 8, "sample_end_monotonic_ns": 21},
        {"sample_begin_monotonic_ns": 21, "sample_end_monotonic_ns": 22},
    ]
    pair = runner.bracketing_samples(samples, scheduled=10, actual=20)
    assert pair == (samples[0], samples[2])


def test_process_tree_enumerates_children_of_every_task(tmp_path: Path) -> None:
    def task(pid: int, tid: int, children: str) -> None:
        directory = tmp_path / str(pid) / "task" / str(tid)
        directory.mkdir(parents=True)
        (directory / "children").write_text(children, encoding="ascii")

    task(100, 100, "101\n")
    task(100, 777, "202\n")
    task(101, 101, "")
    task(202, 202, "303\n")
    task(303, 303, "")

    assert runner.process_tree_pids(100, tmp_path) == [100, 101, 202, 303]


def test_process_tree_rejects_missing_task_children_file(tmp_path: Path) -> None:
    task_directory = tmp_path / "100" / "task" / "100"
    task_directory.mkdir(parents=True)

    with pytest.raises(FileNotFoundError, match="children"):
        runner.process_tree_pids(100, tmp_path)


def test_process_tree_rejects_unreadable_task_children_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    children_path = tmp_path / "100" / "task" / "100" / "children"
    children_path.parent.mkdir(parents=True)
    children_path.write_text("", encoding="ascii")
    original_read_text = Path.read_text

    def unreadable_children(path: Path, *args: object, **kwargs: object) -> str:
        if path == children_path:
            raise PermissionError("synthetic unreadable task children")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", unreadable_children)
    with pytest.raises(PermissionError, match="synthetic unreadable task children"):
        runner.process_tree_pids(100, tmp_path)


def test_process_tree_sample_marks_enumeration_failure_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(runner.os, "sysconf", lambda _name: 100, raising=False)

    def fail_enumeration(_root_pid: int, _proc_root: Path) -> dict[int, dict[int, tuple[int, ...]]]:
        raise PermissionError("synthetic partial proc tree")

    monkeypatch.setattr(runner, "process_tree_topology", fail_enumeration)
    sample = runner.process_tree_sample(100, "/opt/jdk/bin/java", True)

    assert sample == {
        "reason": "process tree sample: PermissionError",
        "status": "NOT_AVAILABLE",
    }


def test_process_tree_sample_rejects_tid_topology_change_on_rescan(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    process_root = tmp_path / "100"
    initial_task = process_root / "task" / "100"
    initial_task.mkdir(parents=True)
    (initial_task / "children").write_text("", encoding="ascii")
    stat_fields = ["S", "1", *(["0"] * 9), "3", "4", *(["0"] * 6), "500"]
    stat_path = process_root / "stat"
    stat_path.write_text(f"100 (java) {' '.join(stat_fields)}\n", encoding="ascii")
    (process_root / "schedstat").write_text("1 0 1\n", encoding="ascii")
    executable = process_root / "exe"
    executable.write_bytes(b"synthetic executable")
    added_task = process_root / "task" / "777"
    original_read_text = Path.read_text

    def add_tid_during_record_read(path: Path, *args: object, **kwargs: object) -> str:
        if path == stat_path and not added_task.exists():
            added_task.mkdir()
            (added_task / "children").write_text("", encoding="ascii")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", add_tid_during_record_read)
    monkeypatch.setattr(runner.os, "sysconf", lambda _name: 100, raising=False)

    sample = runner.process_tree_sample(
        100,
        str(executable.resolve()),
        False,
        tmp_path,
    )

    assert sample == {
        "reason": "process tree sample: DiagnosticError",
        "status": "NOT_AVAILABLE",
    }


def process_sample(
    *,
    target_ticks: int,
    tracer_ticks: int,
    target_start_time: int = 500,
    begin: int = 1,
    end: int = 2,
) -> dict[str, object]:
    return {
        "sample_begin_monotonic_ns": begin,
        "sample_end_monotonic_ns": end,
        "target_process_tree": runner.available(
            {
                "clock_ticks_per_second": 100,
                "processes": [
                    {
                        "cpu_ticks": tracer_ticks,
                        "executable": "/usr/bin/strace",
                        "parent_pid": 1,
                        "pid": 100,
                        "role": "TRACER",
                        "schedstat": runner.available("1 0 1"),
                        "start_time_ticks": 400,
                        "state": "R",
                        "target_cpu": False,
                    },
                    {
                        "cpu_ticks": target_ticks,
                        "executable": "/opt/jdk/bin/java",
                        "parent_pid": 100,
                        "pid": 101,
                        "role": "TARGET_JAVA",
                        "schedstat": runner.available("1 0 1"),
                        "start_time_ticks": target_start_time,
                        "state": "S",
                        "target_cpu": True,
                    },
                ],
                "root_pid": 100,
                "target_executable": "/opt/jdk/bin/java",
                "tracer_wrapped": True,
            }
        ),
    }


def identity_host_sample(
    *,
    target_ticks: int,
    target_start_time: int = 500,
    begin: int = 1_000_000_000,
    end: int = 1_000_000_001,
) -> dict[str, object]:
    sample = process_sample(
        target_ticks=target_ticks,
        tracer_ticks=10,
        target_start_time=target_start_time,
        begin=begin,
        end=end,
    )
    unavailable = runner.unavailable("synthetic")
    wall_offset = 1_700_000_000_000_000_000 - 900_000_000
    return {
        **sample,
        "cgroup_cpu_stat": unavailable,
        "cgroup_mode": "V2",
        "cpu_pressure": unavailable,
        "io_pressure": unavailable,
        "load_average": unavailable,
        "proc_stat": unavailable,
        "sample_begin_wall_time_ns": wall_offset + begin,
        "sample_end_wall_time_ns": wall_offset + end,
    }


def test_process_tree_cpu_excludes_tracer_activity() -> None:
    before = process_sample(target_ticks=10, tracer_ticks=10)
    after = process_sample(target_ticks=10, tracer_ticks=110, begin=30, end=31)
    assert runner.process_tree_cpu(before, after) == (
        0,
        False,
        False,
        [
            {
                "executable": "/opt/jdk/bin/java",
                "pid": 101,
                "role": "TARGET_JAVA",
                "start_time_ticks": 500,
            }
        ],
    )


def test_process_tree_cpu_rejects_pid_reuse_by_start_time() -> None:
    before = process_sample(target_ticks=10, tracer_ticks=10, target_start_time=500)
    after = process_sample(
        target_ticks=20,
        tracer_ticks=10,
        target_start_time=900,
        begin=30,
        end=31,
    )
    assert runner.process_tree_cpu(before, after) is None


def test_lane_process_identity_binds_pid_executable_and_start_time() -> None:
    events = valid_lane_events()
    events[0]["process_id"] = 101
    samples = [
        identity_host_sample(target_ticks=10),
        identity_host_sample(target_ticks=20, begin=1_100_000_000, end=1_100_000_001),
    ]

    assert runner.validate_lane_process_identity(
        events,
        samples,
        target_executable="/opt/jdk/bin/java",
    ) == {
        "executable": "/opt/jdk/bin/java",
        "pid": 101,
        "start_time_ticks": 500,
    }


def test_lane_process_identity_rejects_wrong_pid_and_pid_reuse() -> None:
    events = valid_lane_events()
    events[0]["process_id"] = 102
    samples = [identity_host_sample(target_ticks=10)]
    with pytest.raises(diagnostic.DiagnosticError, match="LANE_PROCESS_IDENTITY_PID"):
        runner.validate_lane_process_identity(
            events,
            samples,
            target_executable="/opt/jdk/bin/java",
        )

    events[0]["process_id"] = 101
    samples.append(
        identity_host_sample(
            target_ticks=20,
            target_start_time=900,
            begin=1_100_000_000,
            end=1_100_000_001,
        )
    )
    with pytest.raises(diagnostic.DiagnosticError, match="LANE_PROCESS_IDENTITY_CHANGED"):
        runner.validate_lane_process_identity(
            events,
            samples,
            target_executable="/opt/jdk/bin/java",
        )


def test_lane_process_identity_ignores_stale_samples() -> None:
    events = valid_lane_events()
    events[0]["process_id"] = 101

    with pytest.raises(diagnostic.DiagnosticError, match="LANE_PROCESS_IDENTITY_MISSING"):
        runner.validate_lane_process_identity(
            events,
            [identity_host_sample(target_ticks=10, begin=1, end=2)],
            target_executable="/opt/jdk/bin/java",
        )


def test_lane_process_identity_rejects_disconnected_java_record() -> None:
    events = valid_lane_events()
    events[0]["process_id"] = 101
    sample = identity_host_sample(target_ticks=10)
    sample["target_process_tree"]["value"]["processes"][1]["parent_pid"] = 999

    with pytest.raises(diagnostic.DiagnosticError, match="VERIFY_PROCESS_TREE_REACHABILITY"):
        runner.validate_lane_process_identity(
            events,
            [sample],
            target_executable="/opt/jdk/bin/java",
        )


def test_host_sample_rejects_correctly_labelled_disconnected_record() -> None:
    sample = identity_host_sample(target_ticks=10)
    sample["target_process_tree"]["value"]["processes"].append(
        {
            "cpu_ticks": 1,
            "executable": "/usr/bin/helper",
            "parent_pid": 998,
            "pid": 999,
            "role": "EXCLUDED_NON_TARGET_DESCENDANT",
            "schedstat": runner.available("1 0 1"),
            "start_time_ticks": 700,
            "state": "S",
            "target_cpu": False,
        }
    )

    with pytest.raises(diagnostic.DiagnosticError, match="VERIFY_PROCESS_TREE_REACHABILITY"):
        runner.validate_host_sample(sample, 0)


def test_lane_process_identity_requires_one_java_descendant() -> None:
    events = valid_lane_events()
    events[0]["process_id"] = 101
    sample = identity_host_sample(target_ticks=10)
    sample["target_process_tree"]["value"]["processes"].append(
        {
            "cpu_ticks": 10,
            "executable": "/opt/jdk/bin/java",
            "parent_pid": 100,
            "pid": 102,
            "role": "TARGET_JAVA",
            "schedstat": runner.available("1 0 1"),
            "start_time_ticks": 600,
            "state": "S",
            "target_cpu": True,
        }
    )

    with pytest.raises(diagnostic.DiagnosticError, match="LANE_PROCESS_IDENTITY_MULTIPLE_TARGETS"):
        runner.validate_lane_process_identity(
            events,
            [sample],
            target_executable="/opt/jdk/bin/java",
        )


def test_host_sample_rederives_roles_instead_of_trusting_tracer_label() -> None:
    process_tree = copy.deepcopy(
        process_sample(target_ticks=10, tracer_ticks=10)["target_process_tree"]
    )
    process_tree["value"]["processes"][0]["role"] = "TARGET_RUNTIME_DESCENDANT"
    process_tree["value"]["processes"][0]["target_cpu"] = True
    unavailable = runner.unavailable("synthetic")
    host_sample = {
        "cgroup_cpu_stat": unavailable,
        "cgroup_mode": "V2",
        "cpu_pressure": unavailable,
        "io_pressure": unavailable,
        "load_average": unavailable,
        "proc_stat": unavailable,
        "sample_begin_monotonic_ns": 1,
        "sample_begin_wall_time_ns": 1,
        "sample_end_monotonic_ns": 2,
        "sample_end_wall_time_ns": 2,
        "target_process_tree": process_tree,
    }

    with pytest.raises(diagnostic.DiagnosticError, match="VERIFY_PROCESS_TREE_ROLE_DERIVATION"):
        runner.validate_host_sample(host_sample, 0)


def test_causal_cpu_bound_subtracts_activity_outside_lateness_interval() -> None:
    before = {
        "sample_begin_monotonic_ns": 0,
        "sample_end_monotonic_ns": 5,
    }
    after = {
        "sample_begin_monotonic_ns": 25,
        "sample_end_monotonic_ns": 30,
    }
    assert runner.causal_target_cpu_lower_bound(
        20,
        before,
        after,
        scheduled_ns=10,
        actual_ns=20,
        processor_count=1,
    ) == (0, 20)
    assert runner.causal_target_cpu_lower_bound(
        30,
        before,
        after,
        scheduled_ns=10,
        actual_ns=20,
        processor_count=1,
    ) == (10, 20)


def test_tracer_cpu_cannot_classify_a_miss_as_genuine_runtime_demand() -> None:
    scheduled = 10_000_000
    actual = 20_000_001
    offer = {
        "actual_offer_ns": actual,
        "actual_wall_time_ns": 1_000_020_000_001,
        "event_type": "OFFER",
        "harness_preparation_overran_slot": False,
        "missed_slot": True,
        "offer_ordinal": 0,
        "preparation_latency_ns": 1,
        "process_cpu_delta_ns": runner.available(10_000_000),
        "scheduled_offer_ns": scheduled,
        "scheduler_lateness_ns": actual - scheduled,
        "scheduler_thread_cpu_delta_ns": runner.available(1_000_000),
        "schedstat_delta": runner.available({"running_ns": 1, "timeslices": 1, "waiting_ns": 0}),
        "wakeup_lateness_ns": actual - scheduled - 1,
        "wakeup_ns": actual - 1,
        "wal_before": {
            "modified_time_millis": 0,
            "observed_at_ns": actual,
            "present": False,
            "size_bytes": 0,
        },
    }
    before = process_sample(
        target_ticks=10,
        tracer_ticks=10,
        begin=1,
        end=5_000_000,
    )
    after = process_sample(
        target_ticks=10,
        tracer_ticks=110,
        begin=25_000_001,
        end=30_000_001,
    )
    environment = {
        "allocation_preflight": {"psi": runner.unavailable("synthetic")},
        "cgroup_values": {
            name: runner.unavailable("synthetic")
            for name in ("cpu.max", "cpuset.cpus.effective", "memory.current", "memory.max")
        },
        "container_identity": runner.unavailable("synthetic"),
        "cpu_affinity": runner.available([0]),
    }

    missed = runner.build_missed_slots(
        [offer],
        [before, after],
        environment=environment,
        host_telemetry=runner.pending_host_telemetry(),
        jfr=runner.unavailable("synthetic"),
        trace_files=[],
    )

    assert missed[0]["predicates"]["sustained_target_runtime_cpu_demand"] is False
    assert (
        missed[0]["mandatory_telemetry"]["PROCESS_AND_THREAD_CPU_TIME_DELTAS"]["value"][
            "target_process_tree"
        ]["target_cpu_delta_ns"]
        == 0
    )


def test_portable_artifact_verifier_rejects_absolute_paths(tmp_path: Path) -> None:
    payload = tmp_path / "payload"
    payload.write_bytes(b"evidence")
    record = {
        "path": payload.as_posix(),
        "sha256": diagnostic.sha256_id(payload.read_bytes()),
        "size_bytes": payload.stat().st_size,
    }
    with pytest.raises(diagnostic.DiagnosticError, match="PATH_NOT_PORTABLE"):
        runner.verified_artifact_path(tmp_path, record, "TEST_ARTIFACT")


def test_external_ledger_create_is_exclusive_and_durable(tmp_path: Path) -> None:
    record = tmp_path / "ledger" / "campaign.attempt.json"
    record.parent.mkdir()
    runner.durable_exclusive_write(record, {"state": "STARTED"})
    with pytest.raises(FileExistsError):
        runner.durable_exclusive_write(record, {"state": "RETRIED"})
    assert json.loads(record.read_bytes()) == {"state": "STARTED"}


def test_external_ledger_record_is_not_visible_before_atomic_publish(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = tmp_path / "ledger" / "campaign.attempt.json"
    record.parent.mkdir()

    def fail_link(_source: object, _target: object) -> None:
        raise OSError("synthetic crash before publish")

    monkeypatch.setattr(runner.os, "link", fail_link)
    with pytest.raises(OSError, match="synthetic crash before publish"):
        runner.durable_exclusive_write(record, {"state": "STARTED"})

    assert not record.exists()
    assert list(record.parent.iterdir()) == []


def test_execution_started_seal_has_exactly_one_concurrent_winner(tmp_path: Path) -> None:
    campaign_id = "unit-concurrent-execution-claim"
    manifest = {"diagnostic_campaign_id": campaign_id}
    manifest_canonical = diagnostic.canonical_bytes(manifest)
    attempt_raw = b'{"state":"ARMED"}\n'
    seals = runner.ledger_paths(tmp_path, campaign_id)

    def claim() -> str:
        try:
            runner.claim_execution(
                seals,
                manifest=manifest,
                manifest_canonical=manifest_canonical,
                attempt_raw=attempt_raw,
            )
        except diagnostic.DiagnosticError as error:
            return str(error)
        return "CLAIMED"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _index: claim(), range(2)))

    assert outcomes.count("CLAIMED") == 1
    assert outcomes.count("CAMPAIGN_EXECUTION_ALREADY_STARTED") == 1
    assert seals["started"].is_file()
    assert not seals["terminal"].exists()


def completion_seal_fixture(
    manifest: dict[str, object],
    manifest_canonical: bytes,
    attempt_raw: bytes,
    started_raw: bytes,
) -> dict[str, object]:
    return {
        "attempt_record_sha256": diagnostic.sha256_id(attempt_raw),
        "completed_at_utc": "2020-01-01T00:00:03Z",
        "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
        "evidence_sha256": diagnostic.sha256_id(b"synthetic evidence\n"),
        "execution_started_record_sha256": diagnostic.sha256_id(started_raw),
        "manifest_sha256": diagnostic.sha256_id(manifest_canonical),
        "schema_version": diagnostic.SCHEMA_VERSION,
        "state": "COMPLETED_ONE_SHOT_NO_RERUN",
        "type_name": runner.COMPLETION_SEAL_TYPE,
    }


def failure_seal_fixture(
    manifest: dict[str, object],
    manifest_canonical: bytes,
    attempt_raw: bytes,
    started_raw: bytes,
) -> dict[str, object]:
    return {
        "attempt_record_sha256": diagnostic.sha256_id(attempt_raw),
        "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
        "error_type": "SyntheticFailure",
        "execution_started_record_sha256": diagnostic.sha256_id(started_raw),
        "failed_at_utc": "2020-01-01T00:00:03Z",
        "manifest_sha256": diagnostic.sha256_id(manifest_canonical),
        "message": "synthetic failure",
        "schema_version": diagnostic.SCHEMA_VERSION,
        "state": "FAILED_NO_RERUN",
        "type_name": runner.FAILURE_SEAL_TYPE,
    }


def test_common_terminal_seal_prevents_conflicting_outcomes(tmp_path: Path) -> None:
    campaign_id = "unit-mutually-exclusive-terminal"
    manifest = {"diagnostic_campaign_id": campaign_id}
    manifest_canonical = diagnostic.canonical_bytes(manifest)
    attempt_raw = b'{"state":"ARMED"}\n'
    seals = runner.ledger_paths(tmp_path, campaign_id)
    runner.claim_execution(
        seals,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_raw,
    )
    started_raw = seals["started"].read_bytes()
    completion = completion_seal_fixture(manifest, manifest_canonical, attempt_raw, started_raw)
    runner.durable_terminal_transition(
        seals,
        "completed",
        completion,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_raw,
        started_raw=started_raw,
    )
    with pytest.raises(diagnostic.DiagnosticError, match="CONFLICTING_TERMINAL_SEAL"):
        runner.durable_terminal_transition(
            seals,
            "failed",
            failure_seal_fixture(manifest, manifest_canonical, attempt_raw, started_raw),
            manifest=manifest,
            manifest_canonical=manifest_canonical,
            attempt_raw=attempt_raw,
            started_raw=started_raw,
        )

    assert json.loads(seals["terminal"].read_bytes())["outcome"] == "COMPLETED"
    assert seals["completed"].is_file()
    assert not seals["failed"].exists()


def test_terminal_publish_rejects_outcome_type_mismatch(tmp_path: Path) -> None:
    campaign_id = "unit-terminal-outcome-type-mismatch"
    manifest = {"diagnostic_campaign_id": campaign_id}
    manifest_canonical = diagnostic.canonical_bytes(manifest)
    attempt_raw = b'{"state":"ARMED"}\n'
    seals = runner.ledger_paths(tmp_path, campaign_id)
    runner.claim_execution(
        seals,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_raw,
    )
    started_raw = seals["started"].read_bytes()

    with pytest.raises(diagnostic.DiagnosticError, match="COMPLETION_SEAL_FIELDS"):
        runner.durable_terminal_transition(
            seals,
            "completed",
            failure_seal_fixture(manifest, manifest_canonical, attempt_raw, started_raw),
            manifest=manifest,
            manifest_canonical=manifest_canonical,
            attempt_raw=attempt_raw,
            started_raw=started_raw,
        )

    assert not seals["terminal"].exists()
    assert not seals["completed"].exists()
    assert not seals["failed"].exists()


@pytest.mark.parametrize("outcome", ["completed", "failed"])
def test_terminal_record_recovers_outcome_after_crash_cut(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    outcome: str,
) -> None:
    campaign_id = f"unit-terminal-recovery-{outcome}"
    manifest = {"diagnostic_campaign_id": campaign_id}
    manifest_canonical = diagnostic.canonical_bytes(manifest)
    attempt_raw = b'{"state":"ARMED"}\n'
    seals = runner.ledger_paths(tmp_path, campaign_id)
    runner.claim_execution(
        seals,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_raw,
    )
    started_raw = seals["started"].read_bytes()
    outcome_record = (
        completion_seal_fixture(manifest, manifest_canonical, attempt_raw, started_raw)
        if outcome == "completed"
        else failure_seal_fixture(manifest, manifest_canonical, attempt_raw, started_raw)
    )
    durable_write = runner.durable_exclusive_write

    def crash_after_terminal(path: Path, value: object) -> None:
        if path == seals[outcome]:
            raise OSError("synthetic crash after terminal publish")
        durable_write(path, value)

    monkeypatch.setattr(runner, "durable_exclusive_write", crash_after_terminal)
    with pytest.raises(OSError, match="synthetic crash after terminal publish"):
        runner.durable_terminal_transition(
            seals,
            outcome,
            outcome_record,
            manifest=manifest,
            manifest_canonical=manifest_canonical,
            attempt_raw=attempt_raw,
            started_raw=started_raw,
        )

    terminal = json.loads(seals["terminal"].read_bytes())
    assert terminal["outcome_record"] == outcome_record
    assert not seals[outcome].exists()

    monkeypatch.setattr(runner, "durable_exclusive_write", durable_write)
    recovered = runner.durable_terminal_transition(
        seals,
        outcome,
        outcome_record,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_raw,
        started_raw=started_raw,
    )

    assert recovered == terminal
    assert json.loads(seals[outcome].read_bytes()) == outcome_record


@pytest.mark.parametrize("outcome", ["completed", "failed"])
def test_public_recovery_entrypoint_repairs_terminal_crash_cut_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    outcome: str,
) -> None:
    manifest = example_manifest()
    manifest["manifest_state"] = diagnostic.FROZEN_STATE
    manifest["diagnostic_campaign_id"] = f"unit-public-terminal-recovery-{outcome}"
    manifest["source"] = {
        "commit": "1" * 40,
        "repository": diagnostic.SOURCE_REPOSITORY,
        "tree": "2" * 40,
    }
    ledger_root = tmp_path / "ledger"
    ledger_root.mkdir()
    evidence_root = tmp_path / "evidence"
    manifest["evidence_directory"] = evidence_root.as_posix()
    manifest["environment"]["campaign_ledger_directory"] = ledger_root.as_posix()
    manifest_path = tmp_path / "manifest.json"
    runner.canonical_write(manifest_path, manifest)
    manifest_canonical = diagnostic.canonical_bytes(manifest)
    attempt = {
        "allocation_manifest_sha256": manifest["environment"]["allocation_manifest"]["sha256"],
        "authority": "DIAGNOSTIC_ONLY",
        "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
        "manifest_checkout": {},
        "manifest_sha256": diagnostic.sha256_id(manifest_canonical),
        "preflight_receipt_sha256": diagnostic.sha256_id(b"preflight"),
        "schema_version": diagnostic.SCHEMA_VERSION,
        "source": manifest["source"],
        "source_checkout": {},
        "started_at_utc": "2020-01-01T00:00:00Z",
        "state": runner.ATTEMPT_SEAL_STATE,
        "type_name": runner.ATTEMPT_SEAL_TYPE,
    }
    seals = runner.ledger_paths(ledger_root, manifest["diagnostic_campaign_id"])
    runner.durable_exclusive_write(seals["attempt"], attempt)
    attempt_raw = seals["attempt"].read_bytes()
    runner.claim_execution(
        seals,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        attempt_raw=attempt_raw,
    )
    started_raw = seals["started"].read_bytes()
    outcome_record = (
        completion_seal_fixture(manifest, manifest_canonical, attempt_raw, started_raw)
        if outcome == "completed"
        else failure_seal_fixture(manifest, manifest_canonical, attempt_raw, started_raw)
    )
    durable_write = runner.durable_exclusive_write

    def crash_after_terminal(path: Path, value: object) -> None:
        if path == seals[outcome]:
            raise OSError("synthetic crash after terminal publish")
        durable_write(path, value)

    monkeypatch.setattr(runner, "durable_exclusive_write", crash_after_terminal)
    with pytest.raises(OSError, match="synthetic crash after terminal publish"):
        runner.durable_terminal_transition(
            seals,
            outcome,
            outcome_record,
            manifest=manifest,
            manifest_canonical=manifest_canonical,
            attempt_raw=attempt_raw,
            started_raw=started_raw,
        )
    monkeypatch.setattr(runner, "durable_exclusive_write", durable_write)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "run_sidecar_diagnostic.py"),
            "--manifest",
            str(manifest_path),
            "--recover-terminal",
        ],
        cwd=ROOT,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
    assert f"outcome={outcome.upper()}" in result.stdout
    assert json.loads(seals[outcome].read_bytes()) == outcome_record
    assert not evidence_root.exists()


def test_lane_nonzero_exit_cannot_seal_as_zero_misses() -> None:
    with pytest.raises(diagnostic.DiagnosticError, match="LANE_EXIT_NONZERO"):
        runner.validate_lane_execution(
            valid_lane_events(),
            profile="EMBEDDED_FFM",
            duration=1,
            expected_processors=2,
            exit_code=17,
            timed_out=False,
        )


def test_lane_start_requires_positive_process_id() -> None:
    events = valid_lane_events()
    events[0]["process_id"] = 0
    with pytest.raises(diagnostic.DiagnosticError, match="LANE_START_PROCESS_ID"):
        runner.validate_lane_execution(
            events,
            profile="EMBEDDED_FFM",
            duration=1,
            expected_processors=2,
            exit_code=0,
            timed_out=False,
        )


def test_empty_lane_cannot_seal_as_zero_misses() -> None:
    with pytest.raises(diagnostic.DiagnosticError, match="LANE_EVENT_COUNT"):
        runner.validate_lane_execution(
            [],
            profile="EMBEDDED_FFM",
            duration=1,
            expected_processors=2,
            exit_code=0,
            timed_out=False,
        )


def test_truncated_lane_cannot_seal_as_zero_misses() -> None:
    events = valid_lane_events()
    with pytest.raises(diagnostic.DiagnosticError, match="LANE_EVENT_COUNT"):
        runner.validate_lane_execution(
            events[:-1],
            profile="EMBEDDED_FFM",
            duration=1,
            expected_processors=2,
            exit_code=0,
            timed_out=False,
        )


def test_duplicate_ordinal_cannot_seal_as_zero_misses() -> None:
    events = valid_lane_events()
    events[2]["offer_ordinal"] = 0
    with pytest.raises(diagnostic.DiagnosticError, match="LANE_OFFER_ORDINAL_SEQUENCE"):
        runner.validate_lane_execution(
            events,
            profile="EMBEDDED_FFM",
            duration=1,
            expected_processors=2,
            exit_code=0,
            timed_out=False,
        )


def test_request_join_and_terminal_state_are_fail_closed() -> None:
    events = valid_lane_events()
    completion_offset = 1 + diagnostic.OFFER_RATE
    events[completion_offset]["request_id"] = "substituted-request"
    with pytest.raises(diagnostic.DiagnosticError, match="LANE_REQUEST_JOIN"):
        runner.validate_lane_execution(
            events,
            profile="EMBEDDED_FFM",
            duration=1,
            expected_processors=2,
            exit_code=0,
            timed_out=False,
        )

    events = valid_lane_events()
    events[-1]["terminal_state_validated"] = False
    with pytest.raises(diagnostic.DiagnosticError, match="LANE_TERMINAL_STATE"):
        runner.validate_lane_execution(
            events,
            profile="EMBEDDED_FFM",
            duration=1,
            expected_processors=2,
            exit_code=0,
            timed_out=False,
        )


def test_first_completion_is_anchored_to_post_warmup_native_state() -> None:
    events = valid_lane_events()
    events[0]["initial_durable_sequence"] = 1_006
    with pytest.raises(diagnostic.DiagnosticError, match="LANE_DURABLE_SEQUENCE_CONTINUITY"):
        runner.validate_lane_execution(
            events,
            profile="EMBEDDED_FFM",
            duration=1,
            expected_processors=2,
            exit_code=0,
            timed_out=False,
        )

    events = valid_lane_events()
    events[0]["initial_state_root"] = diagnostic.sha256_id(b"wrong post-warmup state")
    with pytest.raises(diagnostic.DiagnosticError, match="LANE_STATE_ROOT_CONTINUITY"):
        runner.validate_lane_execution(
            events,
            profile="EMBEDDED_FFM",
            duration=1,
            expected_processors=2,
            exit_code=0,
            timed_out=False,
        )


def test_nanosecond_parsing_never_uses_binary_float_rounding() -> None:
    assert runner.duration_ns("PT0.000000001S") == 1
    assert runner.duration_ns("PT1H2M3.123456789S") == 3_723_123_456_789
    assert runner.instant_ns("1970-01-01T00:00:00.123456789Z") == 123_456_789
    assert runner.instant_ns("1970-01-01T01:00:00.000000001+01:00") == 1
    assert runner.decimal_seconds_ns("1234567890.1234567899") == 1_234_567_890_123_456_789


@pytest.mark.parametrize(
    ("tamper", "expected_error"),
    [
        ("missed", "VERIFY_MISSED_SLOTS"),
        ("disconnected", "VERIFY_PROCESS_TREE_REACHABILITY"),
        ("stale", "LANE_PROCESS_IDENTITY_MISSING"),
    ],
)
def test_independent_verifier_rejects_offline_lane_tampering(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tamper: str,
    expected_error: str,
) -> None:
    manifest = example_manifest()
    evidence_root = tmp_path / "evidence"
    ledger_root = tmp_path / "ledger"
    source_root = tmp_path / "source-checkout"
    manifest_root = tmp_path / "manifest-checkout"
    host_exchange = tmp_path / "host-exchange"
    for path in (evidence_root, ledger_root, source_root, manifest_root, host_exchange):
        path.mkdir()

    manifest["diagnostic_campaign_id"] = f"unit-offline-lane-tamper-{tamper}"
    manifest["manifest_state"] = diagnostic.FROZEN_STATE
    manifest["source"] = {
        "commit": "1" * 40,
        "repository": diagnostic.SOURCE_REPOSITORY,
        "tree": "2" * 40,
    }
    manifest["schedule"]["duration_seconds_per_lane"] = 1
    manifest["evidence_directory"] = evidence_root.as_posix()
    environment_manifest = manifest["environment"]
    environment_manifest["campaign_ledger_directory"] = ledger_root.as_posix()
    environment_manifest["host_receipt_path"] = (host_exchange / "host-receipt.json").as_posix()
    environment_manifest["host_telemetry_path"] = (host_exchange / "host-telemetry.json").as_posix()
    allocation, allocation_record = allocation_fixture(tmp_path, manifest)
    diagnostic.validate_manifest(manifest, executable=True)

    source_receipt = {
        "checkout_root": source_root.as_posix(),
        "commit": manifest["source"]["commit"],
        "git_invocations": [synthetic_process_receipt(source_root, "source-git-probe")],
        "status_porcelain_sha256": diagnostic.sha256_id(b""),
        "tree": manifest["source"]["tree"],
    }
    manifest_receipt = {
        "checkout_root": manifest_root.as_posix(),
        "commit": "3" * 40,
        "git_invocations": [synthetic_process_receipt(manifest_root, "manifest-git-probe")],
        "manifest_blob": "4" * 40,
        "manifest_relative_path": "frozen-manifest.json",
        "status_porcelain_sha256": diagnostic.sha256_id(b""),
        "tree": "5" * 40,
    }
    monkeypatch.setattr(
        diagnostic,
        "verify_source_checkout",
        lambda _root, _source: copy.deepcopy(source_receipt),
    )
    monkeypatch.setattr(
        diagnostic,
        "verify_manifest_checkout",
        lambda _path, _root: copy.deepcopy(manifest_receipt),
    )

    runner.canonical_write(evidence_root / "inputs" / "frozen-manifest.json", manifest)
    allocation_raw = Path(allocation_record["path"]).read_bytes()
    allocation_copy = evidence_root / "inputs" / "allocation-manifest.json"
    allocation_copy.parent.mkdir(parents=True, exist_ok=True)
    allocation_copy.write_bytes(allocation_raw)

    host_receipt = {
        "collected_at_utc": "2020-01-01T00:00:01Z",
        "collector_sha256": environment_manifest["host_collector_sha256"],
        "container": {
            "container_id": "a" * 64,
            "image_digest": allocation["container"]["image_digest"],
            "runtime": allocation["container"]["runtime"],
            "runtime_version": allocation["container"]["runtime_version"],
        },
        "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
        "host": {
            "machine_id_sha256": diagnostic.sha256_id(b"unit-host"),
            "operating_system": "unit-test-host",
        },
        "receipt_nonce": environment_manifest["host_receipt_nonce"],
        "resources": {
            name: allocation["resources"][name]
            for name in ("cgroup_mode", "cpu_max", "cpuset_cpus_effective", "memory_max")
        },
        "schema_version": diagnostic.SCHEMA_VERSION,
        "type_name": diagnostic.HOST_RECEIPT_TYPE,
    }
    host_receipt_path = evidence_root / "host" / "host-receipt.json"
    runner.canonical_write(host_receipt_path, host_receipt)

    unavailable = {
        "reason": "intentionally absent in isolated verifier fixture",
        "status": "NOT_AVAILABLE",
    }
    captured_environment = {
        "allocation_preflight": {"psi": unavailable},
        "cgroup_values": {
            name: unavailable
            for name in (
                "cpu.max",
                "cpu.stat",
                "cpuset.cpus.effective",
                "memory.current",
                "memory.max",
            )
        },
        "container_identity": runner.available(host_receipt["container"]),
        "cpu_affinity": runner.available([0, 1]),
    }
    runner.canonical_write(evidence_root / "environment.json", captured_environment)
    preflight_receipt = {
        "allocation_manifest_sha256": allocation_record["sha256"],
        "allocation_preflight": captured_environment["allocation_preflight"],
        "consumes_campaign": False,
        "created_at_utc": "2020-01-01T00:00:00Z",
        "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
        "live_allocation": {
            "available_processors": 2,
            "cgroup_mode": "V2",
            "cpu_affinity": [0, 1],
            "cpu_max": "200000 100000",
            "cpuset_cpus_effective": "0-1",
            "memory_max": "8589934592",
        },
        "manifest_checkout": manifest_receipt,
        "manifest_sha256": diagnostic.sha256_id(diagnostic.canonical_bytes(manifest)),
        "schema_version": diagnostic.SCHEMA_VERSION,
        "source": manifest["source"],
        "source_checkout": source_receipt,
        "state": runner.PREFLIGHT_RECEIPT_STATE,
        "type_name": runner.PREFLIGHT_RECEIPT_TYPE,
    }
    preflight_path = evidence_root / "inputs" / "preflight-receipt.json"
    runner.canonical_write(preflight_path, preflight_receipt)
    monkeypatch.setattr(
        runner,
        "validate_environment_evidence",
        lambda value, _allocation, _receipt, _prepared: value,
    )
    monkeypatch.setattr(
        runner,
        "validate_preflight_receipt",
        lambda value, **_kwargs: value,
    )
    monkeypatch.setattr(
        runner,
        "environment_snapshot",
        lambda _manifest, _allocation, _receipt: copy.deepcopy(captured_environment),
    )
    monkeypatch.setattr(runner, "verify_live_allocation", lambda _allocation, _snapshot: None)
    monkeypatch.setattr(runner, "verify_jfr_evidence", lambda value, **_kwargs: value)
    monkeypatch.setattr(runner, "verify_strace_evidence", lambda value, **_kwargs: value)

    prepared = runner.prepare_lanes(
        manifest,
        allocation,
        source_root=source_root,
        evidence_root=evidence_root,
    )
    lane_times = [
        ("2020-01-01T00:00:03Z", "2020-01-01T00:00:04Z"),
        ("2020-01-01T00:00:05Z", "2020-01-01T00:00:06Z"),
    ]
    lane_records: list[dict[str, object]] = []
    for lane_index, prepared_lane in enumerate(prepared):
        events = valid_lane_events(profile=prepared_lane.profile)
        if lane_index == 0 and tamper == "missed":
            offer = events[1]
            completion = events[1 + diagnostic.OFFER_RATE]
            scheduled = offer["scheduled_offer_ns"]
            assert isinstance(scheduled, int)
            actual = scheduled + 10_000_000
            offer["actual_offer_ns"] = actual
            offer["actual_wall_time_ns"] += 10_000_000
            offer["harness_preparation_overran_slot"] = True
            offer["missed_slot"] = True
            offer["preparation_latency_ns"] = 10_000_000
            offer["scheduler_lateness_ns"] = 10_000_000
            completion["completed_at_ns"] = actual + 100
            completion["completed_wall_time_ns"] += 10_000_000
            completion["operation_latency_ns"] = 100
            completion["wal_after"]["observed_at_ns"] = actual + 101

        runner.validate_lane_execution(
            events,
            profile=prepared_lane.profile,
            duration=1,
            expected_processors=2,
            exit_code=0,
            timed_out=False,
        )
        lane_directory = prepared_lane.lane_directory
        lane_directory.mkdir()
        event_log = lane_directory / "operations.jsonl"
        event_log.write_bytes(b"".join(diagnostic.canonical_bytes(item) + b"\n" for item in events))
        tracer_pid = 900 + lane_index
        target_executable = str(Path(prepared_lane.argv[0]).resolve())
        stale_sample = lane_index == 0 and tamper == "stale"
        host_sample = {
            "cgroup_cpu_stat": unavailable,
            "cgroup_mode": "V2",
            "cpu_pressure": unavailable,
            "io_pressure": unavailable,
            "load_average": unavailable,
            "proc_stat": unavailable,
            "sample_begin_monotonic_ns": 100 if stale_sample else 1_000_000_000,
            "sample_begin_wall_time_ns": (1_000 if stale_sample else 1_700_000_000_100_000_000),
            "sample_end_monotonic_ns": 200 if stale_sample else 1_000_000_001,
            "sample_end_wall_time_ns": (1_100 if stale_sample else 1_700_000_000_100_000_001),
            "target_process_tree": runner.available(
                {
                    "clock_ticks_per_second": 100,
                    "processes": [
                        {
                            "cpu_ticks": 1,
                            "executable": str(Path(prepared_lane.trace_prefix[0]).resolve()),
                            "parent_pid": 1,
                            "pid": tracer_pid,
                            "role": "TRACER",
                            "schedstat": runner.available("1 0 1"),
                            "start_time_ticks": 400 + lane_index,
                            "state": "S",
                            "target_cpu": False,
                        },
                        {
                            "cpu_ticks": 1,
                            "executable": target_executable,
                            "parent_pid": (
                                999_999
                                if lane_index == 0 and tamper == "disconnected"
                                else tracer_pid
                            ),
                            "pid": 1234,
                            "role": "TARGET_JAVA",
                            "schedstat": runner.available("1 0 1"),
                            "start_time_ticks": 500 + lane_index,
                            "state": "S",
                            "target_cpu": True,
                        },
                    ],
                    "root_pid": tracer_pid,
                    "target_executable": target_executable,
                    "tracer_wrapped": True,
                }
            ),
        }
        host_samples = lane_directory / "host-telemetry.jsonl"
        host_samples.write_bytes(diagnostic.canonical_bytes(host_sample) + b"\n")
        stdout = lane_directory / "stdout.txt"
        stderr = lane_directory / "stderr.txt"
        stdout.write_bytes(b"")
        stderr.write_bytes(b"")
        jfr = runner.unavailable("mocked only after artifact/source/allocation verification")
        strace = runner.unavailable("mocked only after artifact/source/allocation verification")
        started, ended = lane_times[lane_index]
        lane_records.append(
            {
                "artifacts": {
                    "event_log": runner.artifact(event_log, evidence_root),
                    "host_telemetry": runner.artifact(host_samples, evidence_root),
                    "stderr": runner.artifact(stderr, evidence_root),
                    "stdout": runner.artifact(stdout, evidence_root),
                },
                "ended_at_utc": ended,
                "event_count": len(events),
                "executed_argv": [
                    *prepared_lane.trace_prefix,
                    "-o",
                    str(prepared_lane.lane_directory / "fsync.strace"),
                    *prepared_lane.argv,
                ],
                "executed_environment": prepared_lane.environment,
                "environment_mode": "REPLACE",
                "exit_code": 0,
                "java_involved": True,
                "jfr": jfr,
                "missed_slots": [],
                "monotonic_duration_ns": 1,
                "profile_id": prepared_lane.profile,
                "started_at_utc": started,
                "strace_fsync": strace,
                "timed_out": False,
                "working_directory": str(prepared_lane.working_directory),
            }
        )

    handshake = {
        "capture_sha256": diagnostic.sha256_id(
            diagnostic.canonical_bytes(runner.lane_capture_binding(lane_records))
        ),
        "completed_at_utc": "2020-01-01T00:00:07Z",
        "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
        "profile_order": diagnostic.PROFILE_ORDER,
        "receipt_nonce": environment_manifest["host_receipt_nonce"],
        "schema_version": diagnostic.SCHEMA_VERSION,
        "type_name": runner.LANES_COMPLETE_TYPE,
    }
    handshake_path = evidence_root / "lanes-complete.json"
    runner.canonical_write(handshake_path, handshake)
    host_telemetry = {
        "capture_ended_at_utc": "2020-01-01T00:00:08Z",
        "capture_started_at_utc": "2020-01-01T00:00:00Z",
        "collector_sha256": environment_manifest["host_collector_sha256"],
        "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
        "docker_wsl_events": unavailable,
        "lanes_complete_sha256": diagnostic.sha256_id(handshake_path.read_bytes()),
        "receipt_nonce": environment_manifest["host_receipt_nonce"],
        "schema_version": diagnostic.SCHEMA_VERSION,
        "type_name": diagnostic.HOST_TELEMETRY_TYPE,
        "windows_hardware_events": unavailable,
    }
    runner.canonical_write(evidence_root / "host" / "host-telemetry.json", host_telemetry)

    manifest_canonical = diagnostic.canonical_bytes(manifest)
    attempt = {
        "allocation_manifest_sha256": allocation_record["sha256"],
        "authority": "DIAGNOSTIC_ONLY",
        "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
        "manifest_checkout": manifest_receipt,
        "manifest_sha256": diagnostic.sha256_id(manifest_canonical),
        "preflight_receipt_sha256": diagnostic.sha256_id(preflight_path.read_bytes()),
        "schema_version": diagnostic.SCHEMA_VERSION,
        "source": manifest["source"],
        "source_checkout": source_receipt,
        "started_at_utc": "2020-01-01T00:00:00.500000000Z",
        "state": runner.ATTEMPT_SEAL_STATE,
        "type_name": runner.ATTEMPT_SEAL_TYPE,
    }
    ledger = runner.ledger_paths(ledger_root, manifest["diagnostic_campaign_id"])
    runner.durable_exclusive_write(ledger["attempt"], attempt)
    attempt_raw = ledger["attempt"].read_bytes()
    started = {
        "attempt_record_sha256": diagnostic.sha256_id(attempt_raw),
        "diagnostic_campaign_id": manifest["diagnostic_campaign_id"],
        "manifest_sha256": diagnostic.sha256_id(manifest_canonical),
        "schema_version": diagnostic.SCHEMA_VERSION,
        "started_at_utc": "2020-01-01T00:00:00.750000000Z",
        "state": runner.EXECUTION_STARTED_SEAL_STATE,
        "type_name": runner.EXECUTION_STARTED_SEAL_TYPE,
    }
    runner.durable_exclusive_write(ledger["started"], started)
    started_raw = ledger["started"].read_bytes()
    (evidence_root / "attempt-seal.json").write_bytes(attempt_raw)
    (evidence_root / "execution-started-seal.json").write_bytes(started_raw)
    runner.write_success_evidence(
        output_directory=evidence_root,
        manifest=manifest,
        manifest_canonical=manifest_canonical,
        manifest_receipt=manifest_receipt,
        source_receipt=source_receipt,
        attempt_raw=attempt_raw,
        started_raw=started_raw,
        lanes=lane_records,
        classification="NO_MISSED_SLOTS_OBSERVED",
        classified_slots=[],
        seals=ledger,
    )

    with pytest.raises(diagnostic.DiagnosticError, match=expected_error):
        runner.verify_evidence_directory(evidence_root)
