from __future__ import annotations

import copy
import hashlib
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import test_server
from workspace_store import default_profile, read_profile, save_profile


class WorkspaceTests(unittest.TestCase):
    setUp = test_server.PresentationTests.setUp
    tearDown = test_server.PresentationTests.tearDown
    request = test_server.PresentationTests.request

    def put(self, payload, *, origin=None):
        request = Request(
            self.base + "/api/workspace",
            method="PUT",
            data=json.dumps(payload).encode(),
            headers={
                "Origin": origin or self.base,
                "Content-Type": "application/json",
                "X-Delta-Presentation": "1",
            },
        )
        try:
            with urlopen(request, timeout=3) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    def test_profile_survives_reload_and_rejects_lost_updates(self):
        profile = default_profile()
        profile["profileName"] = "Morning demo"
        profile["campaigns"].append({"id": "demo2", "name": "Second campaign"})
        profile["activeCampaignId"] = "demo2"
        self.assertEqual(self.put({"revision": 0, "data": profile}), (200, {"revision": 1}))
        self.assertEqual(read_profile(self.app.profile_path)["data"], profile)
        self.assertEqual(self.put({"revision": 0, "data": default_profile()})[0], 409)
        self.assertEqual(read_profile(self.app.profile_path)["data"], profile)
        code, raw, _ = self.request("/api/workspace")
        self.assertEqual(code, 200)
        self.assertEqual(json.loads(raw)["revision"], 1)

    def test_profile_rejects_cross_origin_credentials_and_corruption_without_overwrite(self):
        self.assertEqual(
            self.put({"revision": 0, "data": default_profile()}, origin="http://example.invalid")[
                0
            ],
            403,
        )
        profile = default_profile()
        profile["controllerDocument"] = '{"private_key":"secret"}'
        self.assertEqual(self.put({"revision": 0, "data": profile})[0], 400)
        self.assertFalse(self.app.profile_path.exists())
        self.app.profile_path.write_text('{"broken":true}', encoding="utf-8")
        self.assertEqual(self.request("/api/workspace")[0], 503)
        self.assertEqual(self.put({"revision": 0, "data": default_profile()})[0], 400)
        self.assertEqual(self.app.profile_path.read_text(), '{"broken":true}')

    def test_atomic_save_failure_keeps_previous_profile(self):
        first = save_profile(self.app.profile_path, {"revision": 0, "data": default_profile()})
        replacement = copy.deepcopy(first)
        replacement["data"]["profileName"] = "Changed"
        with patch("workspace_store.os.replace", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                save_profile(self.app.profile_path, replacement)
        self.assertEqual(read_profile(self.app.profile_path), first)

    def test_proxy_has_fixed_routes_and_requires_original_write_marker(self):
        with patch.object(
            self.app.client, "_request", return_value=(200, {"status": "READY"})
        ) as call:
            self.assertEqual(self.request("/readyz")[0], 200)
            call.assert_called_once_with("GET", "/readyz", None)
            self.assertEqual(self.request("/api/v1/intent/submit", body=b"{}")[0], 403)
            self.assertEqual(self.request("/api/v1/arbitrary")[0], 404)
            self.assertEqual(call.call_count, 1)

    def test_linked_execution_checks_digest_lineage_and_controller_failure(self):
        identifier = "55555555-5555-4555-8555-555555555555"
        provenance = {
            "execution_id": identifier,
            "intent_id": identifier,
            "intent_digest": "sha256:" + "a" * 64,
            "admission_id": identifier,
            "admission_digest": "sha256:" + "b" * 64,
        }
        receipt = {"provenance": provenance, "execution": {"terminal_status": "COMPLETED"}}
        status = {
            **provenance,
            "operation": "TRAIN_TICKET",
            "state": "COMPLETED",
            "receipt_digest": "sha256:"
            + hashlib.sha256(self.app.smoke.canonical_json(receipt)).hexdigest(),
        }
        route = "/api/linked-execution/" + identifier
        with (
            patch.object(self.app.client, "status", return_value=status),
            patch.object(self.app.client, "receipt", return_value=receipt),
        ):
            code, raw, _ = self.request(route)
            self.assertEqual(code, 200)
            self.assertTrue(json.loads(raw)["receipt_verified"])
            code, downloaded, _ = self.request(route + "?download=receipt")
            self.assertEqual(code, 200)
            self.assertEqual(downloaded, self.app.smoke.canonical_json(receipt))
            status["receipt_digest"] = "sha256:" + "0" * 64
            self.assertEqual(self.request(route)[0], 502)
            status["execution_id"] = "wrong"
            self.assertEqual(self.request(route)[0], 502)
        with patch.object(self.app.client, "status", side_effect=OSError("unavailable")):
            self.assertEqual(self.request(route)[0], 502)
