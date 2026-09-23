"""Loopback presentation UI over the existing Controller and simulation runner.

This host does not implement consensus, arithmetic, signing or scientific gates.
Only fixed local operations are exposed. Results are actual child/API results.
"""

# Russian UI strings intentionally contain Cyrillic characters.
# ruff: noqa: RUF001

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import os
import re
import subprocess
import sys
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
STATIC = Path(__file__).with_name("static")
IMAGE = "sha256:cadbe5fced95ccb849fd7ce4f6fb5135cf684f99b5a1b1257fbd9174e985b08a"
JOB_ID = re.compile(r"[0-9a-f]{32}\Z")
MODEL = "tabular-10gene-phenotype-v1"
DATASET = "synthetic-10gene-cohort-v1"
TERMINAL = {"COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"}


def now() -> str:
    return datetime.now(UTC).isoformat(timespec="milliseconds")


def load_smoke() -> Any:
    spec = importlib.util.spec_from_file_location(
        "presentation_smoke", ROOT / "tools/working-version/smoke-working-version.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class BusyError(ValueError):
    pass


@contextmanager
def exclusive_data(data: Path):
    """Hold a process-owned lock; crashes release it without deleting history."""
    data.mkdir(parents=True, exist_ok=True)
    with (data / "presentation.lock").open("a+b") as handle:
        if handle.tell() == 0:
            handle.write(b"0")
            handle.flush()
        handle.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            raise RuntimeError("PRESENTATION_DATA_ALREADY_OWNED") from error
        yield


class Presentation:
    def __init__(self, data: Path, controller_port: int, formal_report: Path | None = None):
        self.data = data.resolve()
        self.data.mkdir(parents=True, exist_ok=True)
        self.jobs_dir = self.data / "jobs"
        self.jobs_dir.mkdir(exist_ok=True)
        self.controller_url = f"http://127.0.0.1:{controller_port}"
        self.smoke = load_smoke()
        self.client = self.smoke.WorkingVersionClient(
            self.controller_url, self.controller_url, timeout_seconds=5
        )
        self.formal_report = formal_report
        self.lock = threading.RLock()
        self.jobs: dict[str, dict[str, Any]] = {}
        self.active: str | None = None
        self.stopping = False
        self.instance_id = uuid.uuid4().hex
        self.gpu: dict[str, Any] = {"state": "CHECKING"}
        for path in sorted(self.jobs_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)[-30:]:
            if not JOB_ID.fullmatch(path.stem):
                continue
            value = json.loads(path.read_text(encoding="utf-8"))
            if value["state"] in {"QUEUED", "RUNNING"}:
                value["state"] = "INTERRUPTED"
                value["error"] = "Интерфейс был перезапущен; завершение не подтверждено."
                self._save(value)
            self.jobs[value["id"]] = value

    def _save(self, job: dict[str, Any]) -> None:
        target = self.jobs_dir / f"{job['id']}.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps(job, ensure_ascii=False, sort_keys=True), encoding="utf-8")
        temporary.replace(target)

    def update(self, job_id: str, **fields: Any) -> None:
        with self.lock:
            self.jobs[job_id].update(fields, updated_at=now())
            self._save(self.jobs[job_id])

    def log(self, job_id: str, message: str) -> None:
        with self.lock:
            self.jobs[job_id]["events"].append({"time": now(), "message": message})
            self._save(self.jobs[job_id])

    def inspect_gpu(self) -> None:
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,uuid,memory.total,driver_version",
                    "--format=csv,noheader",
                ],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            self.gpu = {
                "state": "VISIBLE" if result.returncode == 0 else "UNAVAILABLE",
                "observation": result.stdout.strip()[:1000],
                "exit_code": result.returncode,
                "scope": "DEVICE_VISIBILITY_ONLY",
                "measured_at": now(),
            }
        except (OSError, subprocess.SubprocessError) as error:
            self.gpu = {"state": "UNAVAILABLE", "error": str(error)[:500]}

    def snapshot(self) -> dict[str, Any]:
        try:
            ready = self.client.ready()
        except Exception as error:
            ready = {"status": "UNAVAILABLE", "error": str(error)[:500]}
        formal: dict[str, Any] = {"decision": "UNKNOWN"}
        if self.formal_report and self.formal_report.is_file():
            report = json.loads(self.formal_report.read_text(encoding="utf-8"))
            formal = {
                key: report.get(key)
                for key in ("decision", "formal_semantics_id", "decision_reasons")
            }
        with self.lock:
            return {
                "instance_id": self.instance_id,
                "mode": "SIMULATED_LOCAL",
                "benchmark_result_qc": None,
                "feature010_go_checkpoint_sha": None,
                "feature011_admitted": False,
                "controller": ready,
                "controller_url": self.controller_url,
                "gpu": copy.deepcopy(self.gpu),
                "formal_candidate": formal,
                "active_job": self.active,
                "jobs": [copy.deepcopy(job) for job in reversed(list(self.jobs.values()))][:30],
            }

    def submit(self, kind: str) -> dict[str, Any]:
        if kind not in {"training", "controllers"}:
            raise ValueError("UNKNOWN_OPERATION")
        with self.lock:
            if self.active is not None or self.stopping:
                raise BusyError("Дождитесь завершения текущего запуска.")
            job_id = uuid.uuid4().hex
            job = {
                "id": job_id,
                "kind": kind,
                "state": "QUEUED",
                "created_at": now(),
                "updated_at": now(),
                "events": [],
                "result": None,
                "mode": "SIMULATED_LOCAL",
                "gate_eligible": False,
            }
            self._save(job)
            self.jobs[job_id] = job
            self.active = job_id
            threading.Thread(target=self._run, args=(job_id,), daemon=True).start()
            return copy.deepcopy(job)

    def _run(self, job_id: str) -> None:
        started = time.monotonic()
        try:
            self.update(job_id, state="RUNNING")
            if self.jobs[job_id]["kind"] == "training":
                result = self._train(job_id)
            else:
                result = self._controllers(job_id)
            self.update(job_id, state="COMPLETED", result=result)
            self.log(job_id, "Запуск завершён. Результат сохранён на диск.")
        except Exception as error:
            self.update(job_id, state="FAILED", error=str(error)[:2000])
            self.log(job_id, "Выполнение остановлено с ошибкой; успешный результат не создан.")
        finally:
            try:
                self.update(job_id, elapsed_ms=round((time.monotonic() - started) * 1000))
            finally:
                with self.lock:
                    self.active = None

    def _train(self, job_id: str) -> dict[str, Any]:
        self.log(job_id, "Отправка TRAIN_TICKET в существующий HTTP Controller.")
        intent = self.smoke.build_train_intent()
        submission = self.client.submit(intent)
        admission = submission["admission"]
        execution_id = admission["execution_id"]
        self.update(job_id, execution_id=execution_id, intent=intent, admission=admission)
        self.log(job_id, f"Controller принял задание {execution_id}.")
        deadline, previous = time.monotonic() + 90, None
        while time.monotonic() < deadline:
            status = self.client.status(execution_id)
            if status["state"] != previous:
                previous = status["state"]
                self.log(job_id, f"Python Worker: {previous}.")
                self.update(job_id, execution_status=status)
            if status["state"] in TERMINAL:
                break
            time.sleep(0.3)
        else:
            raise RuntimeError("Истёк срок ожидания Controller; успех не подтверждён.")
        if status["state"] != "COMPLETED":
            raise RuntimeError(f"Controller завершил задание со статусом {status['state']}")
        receipt = self.client.receipt(execution_id)
        expected = {
            "intent_id": intent["intent_id"],
            "intent_digest": intent["intent_digest"],
            "admission_id": admission["admission_id"],
            "admission_digest": admission["admission_digest"],
            "execution_id": execution_id,
        }
        if any(receipt["provenance"].get(key) != value for key, value in expected.items()):
            raise RuntimeError("RECEIPT_LINEAGE_MISMATCH")
        self.log(job_id, "Проверена связь intent → admission → execution → receipt.")
        return {
            "scope": "PLUGIN_BOUNDARY",
            "model": MODEL,
            "dataset": DATASET,
            "receipt": receipt,
            "lineage_verified": True,
            "training_device": "CPU",
            "scientific_gate_b": "NOT_QUALIFIED",
            "native_consensus": "NOT_EXECUTED",
            "java_transport": "NOT_EXECUTED",
        }

    def _controllers(self, job_id: str) -> dict[str, Any]:
        folder = self.data / "simulations" / job_id
        folder.mkdir(parents=True, exist_ok=False)
        command = [
            sys.executable,
            str(ROOT / "tools/feature010/simulated_local.py"),
            "run",
            "--mode",
            "SIMULATED_LOCAL",
            "--image",
            IMAGE,
            "--output",
            str(folder),
        ]
        self.log(job_id, "Запуск четырёх Docker-контроллеров с временными Ed25519 test keys.")
        log_path = folder / "runner-output.txt"
        observed: set[str] = set()
        messages = {
            "manifest.json": "Зафиксированы source/image IDs и видимость GPU в Docker.",
            "all-online.json": "4/4 контроллера: подписи собраны.",
            "one-lost.json": "Один контроллер остановлен: 3/4, кворум сохранён.",
            "two-lost.json": "Два контроллера остановлены: 2/4, кворума нет.",
            "restarted.json": "Контроллер перезапущен; поколение и test key изменены.",
        }
        with log_path.open("w", encoding="utf-8") as output:
            process = subprocess.Popen(command, cwd=ROOT, stdout=output, stderr=subprocess.STDOUT)
            while process.poll() is None:
                for name, message in messages.items():
                    if name not in observed and any(folder.glob(f"sim-*/{name}")):
                        observed.add(name)
                        self.log(job_id, message)
                time.sleep(0.4)
        if process.returncode:
            raise RuntimeError(log_path.read_text(encoding="utf-8")[-1800:])
        reports = list(folder.glob("sim-*/report.json"))
        if len(reports) != 1:
            raise RuntimeError("SIMULATION_REPORT_MISSING")
        run_dir = reports[0].parent
        report = json.loads(reports[0].read_text(encoding="utf-8"))
        if (
            report.get("gate_eligible") is not False
            or report.get("benchmark_result_qc") is not None
            or report.get("feature010_go_checkpoint_sha") is not None
            or report.get("diagnostic_status") != "PASS"
        ):
            raise RuntimeError("SIMULATION_BOUNDARY_INVALID")
        cleanup = json.loads((run_dir / "cleanup.json").read_text(encoding="utf-8"))
        if cleanup["resources_remaining"]:
            raise RuntimeError("SIMULATION_CLEANUP_INCOMPLETE")
        phases = {
            name: json.loads((run_dir / f"{name}.json").read_text())
            for name in ("all-online", "one-lost", "two-lost", "restarted")
        }
        self.log(job_id, "Офлайн-проверка подписей пройдена; контейнеры этого запуска удалены.")
        return {"report": report, "phases": phases, "cleanup": cleanup}


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, port: int, application: Presentation):
        self.application = application
        self.origin = f"http://127.0.0.1:{port}"
        super().__init__(("127.0.0.1", port), Handler)


class Handler(BaseHTTPRequestHandler):
    server: Server

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, format: str, *args: Any) -> None:
        pass

    def send(self, status: int, data: bytes, media: str, *, download: bool = False) -> None:
        self.send_response(status)
        self.send_header("Content-Type", media)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; script-src 'self'; style-src 'self'; connect-src 'self'; "
            "object-src 'none'; frame-ancestors 'none'; base-uri 'none'",
        )
        if download:
            self.send_header("Content-Disposition", 'attachment; filename="delta-run.json"')
        self.end_headers()
        self.wfile.write(data)

    def json(self, status: int, value: Any, *, download: bool = False) -> None:
        self.send(
            status,
            json.dumps(value, ensure_ascii=False).encode(),
            "application/json; charset=utf-8",
            download=download,
        )

    def valid_host(self) -> bool:
        return (
            self.client_address[0] == "127.0.0.1"
            and self.headers.get("Host") == urlsplit(self.server.origin).netloc
        )

    def do_GET(self) -> None:
        if not self.valid_host():
            self.json(403, {"error": "HOST_FORBIDDEN"})
            return
        path = urlsplit(self.path).path
        if path == "/api/health":
            self.json(
                200,
                {
                    "service": "delta-presentation",
                    "instance_id": self.server.application.instance_id,
                    "status": "STOPPING" if self.server.application.stopping else "READY",
                    "active_job": self.server.application.active,
                    "mode": "SIMULATED_LOCAL",
                },
            )
        elif path == "/api/state":
            self.json(200, self.server.application.snapshot())
        elif path.startswith("/api/report/") and JOB_ID.fullmatch(
            path.removeprefix("/api/report/")
        ):
            with self.server.application.lock:
                job = copy.deepcopy(self.server.application.jobs.get(path.rsplit("/", 1)[1]))
            self.json(200 if job else 404, job or {"error": "NOT_FOUND"}, download=True)
        elif path in {"/", "/app.js", "/style.css"}:
            filename = {"/": "index.html", "/app.js": "app.js", "/style.css": "style.css"}[path]
            media = {"/": "text/html", "/app.js": "text/javascript", "/style.css": "text/css"}[path]
            self.send(200, (STATIC / filename).read_bytes(), media + "; charset=utf-8")
        else:
            self.json(404, {"error": "NOT_FOUND"})

    def do_POST(self) -> None:
        if (
            not self.valid_host()
            or self.headers.get("Origin") != self.server.origin
            or self.headers.get("X-Delta-Presentation") != "1"
            or self.headers.get("Content-Type") != "application/json"
        ):
            self.json(403, {"error": "REQUEST_ORIGIN_FORBIDDEN"})
            return
        if self.headers.get("Transfer-Encoding") or self.headers.get("Content-Length") != "2":
            self.json(400, {"error": "EMPTY_OBJECT_REQUIRED"})
            return
        if self.rfile.read(2) != b"{}":
            self.json(400, {"error": "EMPTY_OBJECT_REQUIRED"})
            return
        if self.path == "/api/shutdown":
            with self.server.application.lock:
                if self.server.application.active is not None:
                    self.json(409, {"error": "JOB_ACTIVE_WAIT_FOR_COMPLETION"})
                    return
                self.server.application.stopping = True
            self.json(202, {"status": "STOPPING"})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        route = {"/api/train": "training", "/api/simulate": "controllers"}
        if self.path not in route:
            self.json(404, {"error": "NOT_FOUND"})
            return
        try:
            self.json(202, self.server.application.submit(route[self.path]))
        except BusyError as error:
            self.json(409, {"error": str(error)})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8870)
    parser.add_argument("--controller-port", type=int, default=8865)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--formal-report", type=Path)
    parser.add_argument("--instance-id", default=uuid.uuid4().hex)
    args = parser.parse_args()
    if not JOB_ID.fullmatch(args.instance_id):
        parser.error("instance-id must be a lowercase UUID hex value")
    with exclusive_data(args.data_dir):
        application = Presentation(args.data_dir, args.controller_port, args.formal_report)
        application.instance_id = args.instance_id
        with Server(args.port, application) as server:
            threading.Thread(target=application.inspect_gpu, daemon=True).start()
            print(
                json.dumps({"status": "READY", "url": server.origin, "mode": "SIMULATED_LOCAL"}),
                flush=True,
            )
            server.serve_forever()


if __name__ == "__main__":
    main()
