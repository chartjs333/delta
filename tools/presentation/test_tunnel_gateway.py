from __future__ import annotations

import json
import threading
import unittest
from http.client import HTTPConnection
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import ClassVar
from unittest.mock import patch
from urllib.parse import urlencode

import tunnel_gateway as remote


class Upstream(BaseHTTPRequestHandler):
    calls: ClassVar[list] = []

    def log_message(self, *args):
        pass

    def do_GET(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        self.calls.append((self.command, self.path, dict(self.headers), body))
        data = json.dumps({"ok": True}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    do_POST = do_GET
    do_PUT = do_GET


class RemoteTests(unittest.TestCase):
    def setUp(self):
        self.upstream = ThreadingHTTPServer(("127.0.0.1", 0), Upstream)
        self.gateway = remote.Gateway(
            0, self.upstream.server_port, "test-instance", "control-secret", "a" * 64
        )
        self.gateway.public_url = "https://test-example.trycloudflare.com"
        self.threads = []
        for server in (self.upstream, self.gateway):
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            self.threads.append(thread)
        Upstream.calls = []

    def tearDown(self):
        for server in (self.gateway, self.upstream):
            server.shutdown()
            server.server_close()
        for thread in self.threads:
            thread.join(timeout=3)

    def request(self, path="/", method="GET", body=None, **headers):
        connection = HTTPConnection("127.0.0.1", self.gateway.server_port, timeout=3)
        headers.setdefault("Host", "test-example.trycloudflare.com")
        connection.request(method, path, body, headers)
        response = connection.getresponse()
        result = response.status, response.read(), dict(response.getheaders())
        connection.close()
        return result

    def login(self, **overrides):
        fields = {"code": "a" * 64, "next": "/admin/?lang=ru", **overrides}
        return self.request(
            "/_access/login",
            "POST",
            urlencode(fields),
            **{
                "Origin": self.gateway.public_url,
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )

    def cookie(self):
        return self.login()[2]["Set-Cookie"].split(";")[0]

    def test_anonymous_api_and_assets_blocked_bilingual_login(self):
        for path in ("/api/state", "/api/workspace", "/assets/app.js", "/readyz"):
            self.assertEqual(self.request(path)[0], 401)
        self.assertEqual(self.request("/admin/?lang=ru")[0], 303)
        for lang, expected in (("en", "Access code"), ("ru", "Код доступа")):
            status, body, headers = self.request("/_access/login?lang=" + lang)
            self.assertEqual(status, 200)
            self.assertIn(expected, body.decode())
            self.assertIn("form-action 'self'", headers["Content-Security-Policy"])
        self.assertFalse(Upstream.calls)

    def test_login_cookie_and_open_redirect_rejection(self):
        self.assertEqual(self.login(code="wrong")[0], 401)
        status, _, headers = self.login(next="https://evil.invalid/")
        self.assertEqual(status, 303)
        self.assertEqual(headers["Location"], "/?lang=en")
        for attribute in ("Secure", "HttpOnly", "SameSite=Strict", "Path=/"):
            self.assertIn(attribute, headers["Set-Cookie"])

    def test_authenticated_proxy_rewrites_origin_and_strips_credentials(self):
        status, _, _ = self.request(
            "/api/workspace",
            "PUT",
            b"{}",
            **{
                "Cookie": self.cookie(),
                "Origin": self.gateway.public_url,
                "Content-Type": "application/json",
                "X-Delta-Presentation": "1",
                "Authorization": "never-forward",
                "X-Forwarded-Host": "evil.invalid",
            },
        )
        self.assertEqual(status, 200)
        method, path, headers, body = Upstream.calls[-1]
        self.assertEqual((method, path, body), ("PUT", "/api/workspace", b"{}"))
        self.assertEqual(headers["Origin"], f"http://127.0.0.1:{self.upstream.server_port}")
        self.assertEqual(headers["X-Delta-Presentation"], "1")
        for secret in ("Cookie", "Authorization", "X-Forwarded-Host"):
            self.assertNotIn(secret, headers)

    def test_cross_origin_shutdown_and_arbitrary_paths_never_forwarded(self):
        cookie = self.cookie()
        for origin in ("https://evil.invalid", "null", ""):
            self.assertEqual(
                self.request("/api/train", "POST", b"{}", Cookie=cookie, Origin=origin)[0], 403
            )
        for path in ("/api/shutdown", "/_tunnel/stop", "/api/unknown"):
            self.assertEqual(
                self.request(path, "POST", b"{}", Cookie=cookie, Origin=self.gateway.public_url)[0],
                404,
            )
        for path in ("/../control.json", "/%2e%2e/control.json", "http://evil.invalid/"):
            self.assertEqual(self.request(path, Cookie=cookie)[0], 400)
        self.assertEqual(self.request("/", Host="evil.invalid")[0], 403)
        self.assertFalse(Upstream.calls)

    def test_local_control_requires_separate_secret(self):
        headers = {"Host": f"127.0.0.1:{self.gateway.server_port}"}
        self.assertEqual(self.request("/_tunnel/health", **headers)[0], 404)
        headers["X-Delta-Tunnel-Control"] = "control-secret"
        status, body, _ = self.request("/_tunnel/health", **headers)
        self.assertEqual(status, 200)
        self.assertNotIn("control-secret", body.decode())
        self.assertNotIn("a" * 64, body.decode())
        self.assertEqual(self.request("/_tunnel/stop", "POST", b"{}", **headers)[0], 202)
        self.assertTrue(self.gateway.stopping.is_set())

    def test_expired_tampered_and_previous_instance_sessions_rejected(self):
        cookie = self.cookie()
        self.assertTrue(self.gateway.authenticated(cookie))
        self.assertFalse(self.gateway.authenticated(cookie[:-1] + "z"))
        with patch.object(remote.time, "time", return_value=remote.time.time() + remote.TTL + 1):
            self.assertFalse(self.gateway.authenticated(cookie))
        self.gateway.secret = b"new-instance"
        self.assertEqual(self.request("/api/state", Cookie=cookie)[0], 401)

    def test_login_rate_limit_and_oversized_body(self):
        self.gateway.attempts = [remote.time.monotonic()] * 30
        self.assertEqual(self.login()[0], 429)
        self.assertEqual(
            self.request(
                "/_access/login", "POST", b"", **{"Content-Length": str(remote.MAX_BODY + 1)}
            )[0],
            400,
        )


if __name__ == "__main__":
    unittest.main()
