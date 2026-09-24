"""Explicit operator smoke: authenticate through the tunnel and run the MNIST example.

Access code/cookies/tokens stay in memory and are never included in evidence.
Optional resolved IP retains ordinary TLS certificate/hostname verification.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import socket
import ssl
import time
from datetime import UTC, datetime
from http.client import HTTPSConnection
from pathlib import Path
from urllib.parse import urlencode, urlsplit
from urllib.request import urlopen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--resolved-ip")
    args = parser.parse_args()
    host = urlsplit(
        (args.data / "tunnel/current-url.txt").read_text(encoding="utf-8-sig").strip()
    ).hostname
    assert host and re.fullmatch(r"[a-z0-9-]+\.trycloudflare\.com", host)
    origin = "https://" + host

    class Connection(HTTPSConnection):
        def connect(self):
            raw = socket.create_connection(
                (args.resolved_ip or self.host, 443), timeout=self.timeout
            )
            self.sock = self._context.wrap_socket(raw, server_hostname=self.host)

    def request(path, method="GET", body=None, headers=None):
        connection = Connection(host, timeout=30, context=ssl.create_default_context())
        try:
            connection.request(method, path, body, headers or {})
            response = connection.getresponse()
            return (
                response.status,
                response.read(),
                {k.lower(): v for k, v in response.getheaders()},
            )
        finally:
            connection.close()

    assert request("/node-training/?lang=en")[0] == 303
    assert request("/node-training/api/status")[0] == 401
    code = (args.data / "tunnel/access-code.txt").read_text(encoding="utf-8-sig").strip()
    status, _, headers = request(
        "/_access/login",
        "POST",
        urlencode({"code": code, "next": "/node-training/?lang=en"}),
        {"Origin": origin, "Content-Type": "application/x-www-form-urlencoded"},
    )
    assert status == 303
    auth = {"Cookie": headers["set-cookie"].split(";")[0]}
    for lang, expected in (("en", "Node training example"), ("ru", "Обучение узлов")):
        status, page, headers = request("/node-training/?lang=" + lang, headers=auth)
        assert status == 200 and expected in page.decode()
        assert "script-src 'nonce-" in headers["content-security-policy"]
        assert b"fetch('/node-training/api/status'" in page
    token = json.loads(re.search(rb"const demoToken = (.*?);", page)[1])
    command_headers = {
        **auth,
        "Origin": origin,
        "X-Demo-Token": token,
        "Content-Type": "application/json",
    }
    for path in (
        "/node-training/api/health",
        "/node-training/api/shutdown",
        "/node-training/host.log",
    ):
        assert request(path, headers=auth)[0] == 404
    assert (
        request(
            "/node-training/api/run",
            "POST",
            b"{}",
            {**command_headers, "Origin": "https://evil.invalid"},
        )[0]
        == 403
    )
    assert (
        request(
            "/node-training/api/run", "POST", b"{}", {**command_headers, "X-Demo-Token": "invalid"}
        )[0]
        == 403
    )
    assert request("/node-training/api/run", "POST", b'{"command":"x"}', command_headers)[0] == 400
    assert request("/node-training/api/run", "POST", b"{}", command_headers)[0] == 202
    assert request("/node-training/api/run", "POST", b"{}", command_headers)[0] == 409
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        status, body, _ = request("/node-training/api/status", headers=auth)
        assert status == 200
        snapshot = json.loads(body)
        if not snapshot["running"]:
            break
        time.sleep(2)
    assert not snapshot["running"] and snapshot["error"] is None and snapshot["result"]
    report = snapshot["result"]
    with urlopen("http://127.0.0.1:8872/node-training/api/status", timeout=5) as response:
        assert json.load(response)["result"] == report
    report_path = Path(snapshot["last_output_dir"]) / "mnist-demo-report.json"
    assert json.loads(report_path.read_text(encoding="utf-8")) == report
    assert report["feature_010_go_claimed"] is False
    receipt_path = "/api/linked-execution/934a9d51-e5aa-46da-bbc3-963b9f409914?download=receipt"
    status, receipt, _ = request(receipt_path, headers=auth)
    assert status == 200
    assert (
        hashlib.sha256(receipt).hexdigest()
        == "ec715072b34d3add3e3cd7c191341e491e70866c40663752a91f7a5b6bf0230d"
    )
    with urlopen("http://127.0.0.1:8865/readyz", timeout=5) as response:
        controller = json.load(response)
    assert controller["instance_id"] == "d7602a7b-f488-47eb-8ef3-220dea499291"
    evidence = {
        "status": "PASS",
        "checked_at": datetime.now(UTC).isoformat(),
        "scope": "LOCAL_DEMO_ONLY",
        "qualifying": False,
        "public_url": origin,
        "normal_tls_validation": True,
        "resolved_ip_override": bool(args.resolved_ip),
        "anonymous_api": 401,
        "anonymous_page": 303,
        "en_ru_page": 200,
        "foreign_origin": 403,
        "invalid_token": 403,
        "nonempty_command": 400,
        "concurrent_run": 409,
        "management_and_file_routes": 404,
        "real_run_via_authenticated_https": "PASS",
        "original_report_equals_public_result": True,
        "original_report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        "report_file": str(report_path),
        "controller_instance_preserved": True,
        "existing_receipt_sha256": hashlib.sha256(receipt).hexdigest(),
        "browser_claim": "Local browser tested separately; HTTPS checked by this client",
    }
    target = args.data / "node-training/public-acceptance.json"
    target.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "public_url": origin, "evidence": str(target)}))


if __name__ == "__main__":
    main()
