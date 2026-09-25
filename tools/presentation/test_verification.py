from __future__ import annotations

import copy
import json
import shutil
import tempfile
import time
import unittest
from pathlib import Path

import server
import test_server as server_tests
import verification_runner as runner
from tunnel_gateway import allowed, safe_next


class OracleTests(unittest.TestCase):
    def test_real_reference_computation_and_all_five_rejections(self):
        value = runner.validate_result(runner.run())
        report = value["report"]
        self.assertEqual(report["computation"]["apply"]["next_model"], [19, -19])
        self.assertEqual(report["computation"]["apply"]["next_optimizer"], [2, -2])
        self.assertEqual(len(report["cases"]), 7)
        self.assertEqual(sum(case["outcome"] == "REJECTED" for case in report["cases"]), 5)
        self.assertTrue(all(case["matches_expectation"] for case in report["cases"]))
        self.assertFalse(report["native_execution"])
        self.assertIsNone(report["wal_receipt"])

    def test_repeat_runs_preserve_computation_identity_not_report_identity(self):
        first, second = runner.run("repeat"), runner.run("repeat")
        self.assertEqual(
            first["report"]["computation_sha256"], second["report"]["computation_sha256"]
        )
        for result in (first, second):
            detail = result["report"]["cases"][0]["detail"]
            self.assertEqual(detail["first_sha256"], detail["second_sha256"])

    def test_source_and_manifest_substitutions_fail_before_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            target = Path(temporary) / "oracle"
            shutil.copytree(runner.ORACLE, target)
            source = target / "native_binding.py"
            source.write_bytes(source.read_bytes() + b"\n# tampered")
            with self.assertRaisesRegex(ValueError, "ORACLE_SOURCE_MISMATCH"):
                runner.verify_bundle(target)
            (target / "manifest.json").write_bytes(b"{}")
            with self.assertRaisesRegex(ValueError, "ORACLE_MANIFEST_MISMATCH"):
                runner.verify_bundle(target)

    def test_false_acceptance_and_qualification_cannot_be_hidden_by_rehashing(self):
        original = runner.run("parameter-tamper")
        mutations = (
            lambda r: r["cases"][0].update(observed="ACCEPTED", outcome="ACCEPTED"),
            lambda r: r.update(cases=[]),
            lambda r: r.update(native_execution=True),
            lambda r: r.update(gate_eligible=True),
            lambda r: r.update(wal_receipt={"fake": True}),
            lambda r: r["computation"]["apply"].update(next_model=[1, 2]),
        )
        for mutate in mutations:
            value = copy.deepcopy(original)
            mutate(value["report"])
            raw = runner.canonical(value["report"])
            value.update(canonical_report=raw.decode(), report_sha256=runner.sha(raw))
            with self.assertRaises(ValueError):
                runner.validate_result(value)

    def test_unknown_scenario_has_no_command_interpretation(self):
        for scenario in ("../valid", "valid;whoami", "", "ALL"):
            with self.assertRaisesRegex(ValueError, "UNKNOWN_SCENARIO"):
                runner.run(scenario)


class VerificationHttpTests(unittest.TestCase):
    setUp = server_tests.PresentationTests.setUp
    tearDown = server_tests.PresentationTests.tearDown
    request = server_tests.PresentationTests.request

    def test_real_child_process_report_and_restart_persistence(self):
        status, body, _ = self.request("/api/verify/all", body=b"{}")
        self.assertEqual(status, 202)
        job_id = json.loads(body)["id"]
        deadline = time.monotonic() + 12
        while self.app.active is not None and time.monotonic() < deadline:
            time.sleep(0.02)
        status, body, headers = self.request("/api/report/" + job_id)
        self.assertEqual(status, 200)
        self.assertIn("attachment", headers["Content-Disposition"])
        job = json.loads(body)
        self.assertEqual(job["state"], "COMPLETED", job)
        runner.validate_result(job["result"])
        restored = server.Presentation(Path(self.temp.name), 8865)
        self.assertEqual(restored.jobs[job_id]["result"], job["result"])
        self.assertIsNone(restored.active)

    def test_new_route_preserves_write_and_path_boundaries(self):
        self.assertEqual(
            self.request("/api/verify/all", body=b"{}", origin="https://evil.invalid")[0], 403
        )
        self.assertEqual(self.request("/api/verify/all", body=b"{}", marker=False)[0], 403)
        self.assertEqual(self.request("/api/verify/all", body=b'{"code":"whoami"}')[0], 400)
        self.assertEqual(self.request("/api/verify/unknown", body=b"{}")[0], 404)
        self.app.active = "some-training-job"
        self.assertEqual(self.request("/api/verify/all", body=b"{}")[0], 409)
        self.assertFalse(self.app.jobs)
        self.assertEqual(self.request("/verification/../server.py")[0], 404)
        for path in (
            "/verification/",
            "/verification/app.js",
            "/verification/i18n.mjs",
            "/verification/style.css",
        ):
            status, _, headers = self.request(path)
            self.assertEqual(status, 200)
            self.assertIn("script-src 'self'", headers["Content-Security-Policy"])
            self.assertTrue(allowed("GET", path))
        self.assertTrue(allowed("POST", "/api/verify/all"))
        self.assertFalse(allowed("POST", "/api/verify/unknown"))
        self.assertFalse(allowed("GET", "/verification/../server.py"))
        self.assertEqual(safe_next("/verification/?lang=ru"), "/verification/?lang=ru")


if __name__ == "__main__":
    unittest.main()
