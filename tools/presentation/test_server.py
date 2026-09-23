from __future__ import annotations

import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import server


class PresentationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.app = server.Presentation(Path(self.temp.name), 8865)
        self.http = server.Server(0, self.app)
        self.base = f"http://127.0.0.1:{self.http.server_port}"
        self.http.origin = self.base
        self.thread = threading.Thread(target=self.http.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.http.shutdown()
        self.http.server_close()
        self.thread.join(timeout=3)
        self.temp.cleanup()

    def request(self, path, *, body=None, origin=None, host=None, marker=True):
        headers = {"Origin": origin or self.base, "Content-Type": "application/json"}
        if marker:
            headers["X-Delta-Presentation"] = "1"
        if host:
            headers["Host"] = host
        request = Request(self.base + path, data=body, headers=headers)
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, response.read(), response.headers
        except HTTPError as error:
            return error.code, error.read(), error.headers

    def test_cross_origin_commands_and_dns_rebinding_rejected(self):
        with patch.object(self.app, "submit") as submit:
            for parameters in (
                {"origin": "http://example.invalid"},
                {"host": "example.invalid"},
                {"marker": False},
            ):
                self.assertEqual(self.request("/api/train", body=b"{}", **parameters)[0], 403)
            submit.assert_not_called()

    def test_only_fixed_commands_no_paths_or_shell_input(self):
        with patch.object(self.app, "submit") as submit:
            for body in (b'{"command":"whoami"}', b"[]", b" {}", b"null"):
                self.assertEqual(self.request("/api/train", body=body)[0], 400)
            self.assertEqual(self.request("/api/exec", body=b"{}")[0], 404)
            self.assertEqual(self.request("/../server.py")[0], 404)
            self.assertEqual(self.request("/api/report/../../server.py")[0], 404)
            submit.assert_not_called()

    def test_slide_assets_preserve_png_bytes_and_restrict_paths(self):
        self.app.admin_root = Path(self.temp.name) / "admin-build"
        assets = self.app.admin_root / "assets"
        assets.mkdir(parents=True)
        png = b"\x89PNG\r\n\x1a\n\x00\xff\x80"
        (assets / "slide-1-example.png").write_bytes(png)
        (self.app.admin_root / "private.png").write_bytes(b"private")
        for prefix in ("/assets/", "/admin/assets/"):
            status, body, headers = self.request(prefix + "slide-1-example.png")
            self.assertEqual(status, 200)
            self.assertEqual(body, png)
            self.assertEqual(headers["Content-Type"], "image/png")
            self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
        for path in (
            "/assets/missing.png",
            "/assets/../private.png",
            "/assets/%2e%2e/private.png",
            "/assets/slide-1-example.png/private.png",
        ):
            self.assertEqual(self.request(path)[0], 404)

    def test_busy_rejects_second_job(self):
        self.app.active = "already-running"
        self.assertEqual(self.request("/api/simulate", body=b"{}")[0], 409)
        self.assertFalse(self.app.jobs)

    def test_static_is_offline_and_csp_protected(self):
        status, body, headers = self.request("/")
        self.assertEqual(status, 200)
        self.assertIn(b'type="module"', body)
        self.assertIn("connect-src 'self'", headers["Content-Security-Policy"])
        self.assertNotIn("Access-Control-Allow-Origin", headers)

    def test_failed_training_never_creates_success_result(self):
        job_id = "1" * 32
        self.app.jobs[job_id] = {
            "id": job_id,
            "state": "QUEUED",
            "kind": "training",
            "events": [],
            "result": None,
        }
        with patch.object(self.app, "_train", side_effect=RuntimeError("RECEIPT_LINEAGE_MISMATCH")):
            self.app._run(job_id)
        self.assertEqual(self.app.jobs[job_id]["state"], "FAILED")
        self.assertIsNone(self.app.jobs[job_id]["result"])
        self.assertIsNone(self.app.active)

    def test_restart_marks_unfinished_as_interrupted(self):
        job = {
            "id": "2" * 32,
            "state": "RUNNING",
            "kind": "controllers",
            "events": [],
            "result": None,
        }
        self.app._save(job)
        restored = server.Presentation(Path(self.temp.name), 8865)
        self.assertEqual(restored.jobs[job["id"]]["state"], "INTERRUPTED")
        self.assertIsNone(restored.jobs[job["id"]]["result"])

    def test_download_retains_nonqualifying_boundary(self):
        job = {
            "id": "3" * 32,
            "state": "COMPLETED",
            "mode": "SIMULATED_LOCAL",
            "gate_eligible": False,
        }
        self.app.jobs[job["id"]] = job
        status, body, headers = self.request(f"/api/report/{job['id']}")
        self.assertEqual(status, 200)
        self.assertIs(json.loads(body)["gate_eligible"], False)
        self.assertIn("attachment", headers["Content-Disposition"])

    def test_shutdown_refuses_active_job(self):
        self.app.active = "owned-docker-process"
        self.assertEqual(self.request("/api/shutdown", body=b"{}")[0], 409)
        self.assertFalse(self.app.stopping)

    def test_shutdown_fences_new_jobs(self):
        self.app.stopping = True
        self.assertEqual(self.request("/api/train", body=b"{}")[0], 409)

    def test_data_directory_excludes_second_process_owner(self):
        with server.exclusive_data(Path(self.temp.name)):
            with self.assertRaisesRegex(RuntimeError, "DATA_ALREADY_OWNED"):
                with server.exclusive_data(Path(self.temp.name)):
                    self.fail("Second owner acquired the directory")
        with server.exclusive_data(Path(self.temp.name)):
            pass


if __name__ == "__main__":
    unittest.main()
