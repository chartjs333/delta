"""Authenticated Quick Tunnel gateway for the existing local presentation only.

No consensus logic, dynamic proxy destinations, shell execution, or key custody.
The launcher supplies a local-only control secret through a file, never argv.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import hmac
import html
import json
import os
import re
import secrets
import subprocess
import threading
import time
from http.client import HTTPConnection, HTTPException
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit

PUBLIC_URL = re.compile(r"https://[a-z0-9]+(?:-[a-z0-9]+)*\.trycloudflare\.com")
UUID = r"[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}"
COOKIE = "__Host-delta_demo"
TTL = 12 * 60 * 60
MAX_BODY = 300_000


def allowed(method: str, path: str) -> bool:
    if method == "GET":
        return path in {
            "/",
            "/admin",
            "/admin/",
            "/app.js",
            "/i18n.mjs",
            "/style.css",
            "/api/state",
            "/api/health",
            "/api/workspace",
            "/readyz",
        } or bool(
            re.fullmatch(
                r"/(?:admin/)?assets/[A-Za-z0-9_-][A-Za-z0-9_.-]*\.(?:js|css|png)"
                r"|/api/linked-execution/"
                + UUID
                + r"|/api/report/[0-9a-f]{32}|/api/v1/execution/"
                + UUID
                + r"/(?:status|receipt)",
                path,
            )
        )
    if method == "PUT":
        return path == "/api/workspace"
    return method == "POST" and (
        path in {"/api/train", "/api/simulate", "/api/v1/intent/submit"}
        or bool(re.fullmatch(r"/api/v1/execution/" + UUID + r"/cancel", path))
    )


def safe_next(value: str) -> str:
    parts = urlsplit(value)
    if (
        parts.scheme
        or parts.netloc
        or "\\" in value
        or "%" in parts.path
        or not value.startswith("/")
        or value.startswith("//")
        or any(ord(c) < 32 for c in value)
        or len(value) > 2048
        or parts.path not in {"/", "/admin", "/admin/"}
    ):
        return "/?lang=en"
    return value


class Gateway(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = False

    def __init__(self, port: int, upstream: int, instance: str, control: str, code: str):
        self.upstream = upstream
        self.instance = instance
        self.control = control
        self.code = code
        self.secret = secrets.token_bytes(32)
        self.public_url = ""
        self.connected = False
        self.stopping = threading.Event()
        self.login_lock = threading.Lock()
        self.attempts: list[float] = []
        super().__init__(("127.0.0.1", port), Handler)

    def session(self) -> str:
        payload = f"{int(time.time()) + TTL}.{secrets.token_hex(16)}"
        signature = hmac.new(self.secret, payload.encode(), hashlib.sha256).hexdigest()
        return payload + "." + signature

    def authenticated(self, header: str) -> bool:
        if len(header) > 4096:
            return False
        try:
            cookie: SimpleCookie = SimpleCookie()
            cookie.load(header)
            value = cookie[COOKIE].value
            expiry, nonce, signature = value.split(".")
            if not re.fullmatch(r"[0-9]{10}\.[0-9a-f]{32}\.[0-9a-f]{64}", value):
                return False
            expected = hmac.new(
                self.secret, f"{expiry}.{nonce}".encode(), hashlib.sha256
            ).hexdigest()
            return time.time() < int(expiry) <= time.time() + TTL and hmac.compare_digest(
                signature, expected
            )
        except (KeyError, ValueError):
            return False


class Handler(BaseHTTPRequestHandler):
    server: Gateway

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, *args):
        # Never log cookies, login bodies, or private controls.
        pass

    def reply(
        self,
        status,
        body=b"",
        media="application/json",
        headers=None,
        *,
        referrer_policy="no-referrer",
    ):
        self.send_response(status)
        self.send_header("Content-Type", media)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", referrer_policy)
        self.send_header("X-Frame-Options", "DENY")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def error(self, status, reason):
        self.reply(status, json.dumps({"error": reason}).encode())

    def read_body(self):
        size = self.headers.get("Content-Length", "0")
        if (
            self.headers.get("Transfer-Encoding")
            or len(self.headers.get_all("Content-Length", [])) > 1
            or not size.isdecimal()
            or int(size) > MAX_BODY
        ):
            raise ValueError("INVALID_BODY_LENGTH")
        body = self.rfile.read(int(size))
        if len(body) != int(size):
            raise ValueError("INCOMPLETE_BODY")
        return body

    def login_page(self, query, status=200, failed=False):
        language = "ru" if query.get("lang", [""])[0] == "ru" else "en"
        target = safe_next(query.get("next", ["/?lang=" + language])[0])
        copy = {
            "en": [
                "Presentation access",
                "Enter the access code shown by START-REMOTE.ps1 on the host computer.",
                "Access code",
                "Open application",
                "Invalid code. Try again.",
                "Local demonstration · shared profile · SIMULATED_LOCAL",
            ],
            "ru": [
                "Доступ к презентации",
                "Введите код доступа, который START-REMOTE.ps1 показывает на основном компьютере.",
                "Код доступа",
                "Открыть приложение",
                "Неверный код. Попробуйте ещё раз.",
                "Локальная демонстрация · общий профиль · SIMULATED_LOCAL",
            ],
        }[language]
        links = " · ".join(
            '<a href="/_access/login?'
            + html.escape(urlencode({"lang": lang, "next": target}))
            + f'">{label}</a>'
            for lang, label in [("en", "English"), ("ru", "Русский")]
        )
        body = f'''<!doctype html><html lang="{language}"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DeltaReduce · {copy[0]}</title>
<style>body{{background:#f2f6fc;color:#18304a;font:17px system-ui;margin:0;padding:6vh 20px}}
main{{max-width:480px;margin:auto;padding:36px;border:1px solid #dce5ef;
border-radius:22px;background:white}}h1{{font-size:30px}}
label,input,button{{display:block;width:100%;box-sizing:border-box}}
input,button{{padding:14px;border-radius:9px;font:inherit;margin:10px 0 20px}}
input{{border:1px solid #879db5}}
button{{background:#1263c5;color:white;border:0;cursor:pointer}}
a{{color:#1263c5}}small{{color:#53647a}}[role=alert]{{color:#a72121}}</style>
<main><nav>{links}</nav><h1>{copy[0]}</h1><p>{copy[1]}</p>
{('<p role="alert">' + copy[4] + "</p>") if failed else ""}
<form action="/_access/login" method="post"><input type="hidden" name="lang" value="{language}">
<input type="hidden" name="next" value="{html.escape(target, quote=True)}">
<label for="code">{copy[2]}</label><input id="code" name="code" type="password"
required maxlength="128" autocomplete="current-password" autofocus>
<button>{copy[3]}</button></form><small>{copy[5]}</small></main></html>'''
        self.reply(
            status,
            body.encode(),
            "text/html; charset=utf-8",
            {
                "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; "
                "form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
            },
            # no-referrer makes browser form POSTs send Origin: null, which our
            # strict origin gate must reject. Preserve the origin for this form
            # while continuing to suppress referrers to other sites.
            referrer_policy="same-origin",
        )

    def dispatch(self):
        try:
            body = self.read_body()
        except (ValueError, OSError):
            self.error(400, "INVALID_BODY")
            return
        parts = urlsplit(self.path)
        if (
            len(self.path) > 4096
            or parts.scheme
            or parts.netloc
            or "\\" in parts.path
            or "%" in parts.path
            or "//" in parts.path
            or ".." in parts.path
            or len(self.headers.get_all("Host", [])) != 1
        ):
            self.error(400, "INVALID_PATH_OR_HOST")
            return
        local_host = f"127.0.0.1:{self.server.server_port}"
        host = self.headers.get("Host", "")
        if parts.path.startswith("/_tunnel/"):
            if host != local_host or not hmac.compare_digest(
                self.headers.get("X-Delta-Tunnel-Control", ""), self.server.control
            ):
                self.error(404, "NOT_FOUND")
            elif self.command == "GET" and parts.path == "/_tunnel/health":
                self.reply(
                    200,
                    json.dumps(
                        {
                            "service": "delta-remote-gateway",
                            "pid": os.getpid(),
                            "instance_id": self.server.instance,
                            "url": self.server.public_url,
                            "status": "READY" if self.server.connected else "CONNECTING",
                        }
                    ).encode(),
                )
            elif self.command == "POST" and parts.path == "/_tunnel/stop":
                self.reply(202, b'{"status":"STOPPING"}')
                self.server.stopping.set()
            else:
                self.error(404, "NOT_FOUND")
            return
        if not self.server.public_url or host != urlsplit(self.server.public_url).netloc:
            self.error(403, "HOST_FORBIDDEN")
            return
        query = parse_qs(parts.query)
        if self.command != "GET" and self.headers.get("Origin") != self.server.public_url:
            self.error(403, "ORIGIN_FORBIDDEN")
            return
        if parts.path == "/_access/login":
            if self.command == "GET":
                self.login_page(query)
            elif (
                self.command == "POST"
                and len(body) <= 4096
                and self.headers.get_content_type() == "application/x-www-form-urlencoded"
            ):
                fields = parse_qs(body.decode("utf-8", errors="replace"), max_num_fields=8)
                with self.server.login_lock:
                    now = time.monotonic()
                    self.server.attempts = [t for t in self.server.attempts if t > now - 60]
                    limited = len(self.server.attempts) >= 30
                    if not limited:
                        self.server.attempts.append(now)
                if limited:
                    self.error(429, "LOGIN_RATE_LIMIT")
                elif not hmac.compare_digest(
                    fields.get("code", [""])[0].encode(), self.server.code.encode()
                ):
                    self.login_page(fields, status=401, failed=True)
                else:
                    self.reply(
                        303,
                        headers={
                            "Location": safe_next(fields.get("next", ["/?lang=en"])[0]),
                            "Set-Cookie": f"{COOKIE}={self.server.session()}; Secure; HttpOnly; "
                            f"SameSite=Strict; Path=/; Max-Age={TTL}",
                        },
                    )
            else:
                self.error(400, "INVALID_LOGIN")
            return
        if not self.server.authenticated(self.headers.get("Cookie", "")):
            if self.command == "GET" and parts.path in {"/", "/admin", "/admin/"}:
                self.reply(
                    303,
                    headers={
                        "Location": "/_access/login?"
                        + urlencode({"lang": query.get("lang", ["en"])[0], "next": self.path})
                    },
                )
            else:
                self.error(401, "AUTHENTICATION_REQUIRED")
            return
        if not allowed(self.command, parts.path):
            self.error(404, "NOT_FOUND")
            return
        origin = f"http://127.0.0.1:{self.server.upstream}"
        headers = {"Origin": origin}
        for key in ("Content-Type", "X-Delta-Presentation", "X-Delta-Request"):
            if key in self.headers:
                headers[key] = self.headers[key]
        connection = HTTPConnection("127.0.0.1", self.server.upstream, timeout=15)
        try:
            connection.request(self.command, self.path, body=body or None, headers=headers)
            response = connection.getresponse()
            data = response.read(8_000_001)
            if len(data) > 8_000_000:
                self.error(502, "UPSTREAM_RESPONSE_TOO_LARGE")
                return
            forwarded = {
                key: response.getheader(key)
                for key in ("Content-Disposition", "Content-Security-Policy")
                if response.getheader(key)
            }
            self.reply(
                response.status,
                data,
                response.getheader("Content-Type", "application/octet-stream"),
                forwarded,
            )
        except (OSError, HTTPException):
            self.error(502, "PRESENTATION_UNAVAILABLE")
        finally:
            connection.close()

    def handle_request(self):
        try:
            self.dispatch()
        except (ValueError, OSError):
            self.close_connection = True

    do_GET = handle_request
    do_POST = handle_request
    do_PUT = handle_request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8871)
    parser.add_argument("--upstream", type=int, default=8870)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--cloudflared", type=Path, required=True)
    args = parser.parse_args()
    state = json.loads((args.data_dir / "control.json").read_text(encoding="utf-8-sig"))
    code = (args.data_dir / "access-code.txt").read_text().strip()
    if not re.fullmatch(r"[A-Za-z0-9_-]{32,128}", code):
        raise ValueError("Invalid access-code file")
    gateway = Gateway(args.port, args.upstream, state["instance_id"], state["control"], code)
    child = None
    thread = threading.Thread(target=gateway.serve_forever, daemon=True)
    thread.start()
    try:
        if os.name == "nt":
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000001)
        child = subprocess.Popen(
            [
                str(args.cloudflared),
                "tunnel",
                "--no-autoupdate",
                "--url",
                f"http://127.0.0.1:{args.port}",
                "--loglevel",
                "info",
                "--protocol",
                "http2",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )

        def capture():
            with (args.data_dir / "cloudflared.log").open("w", encoding="utf-8") as log:
                for line in child.stdout:
                    log.write(line)
                    log.flush()
                    match = PUBLIC_URL.search(line)
                    if match and not gateway.public_url:
                        gateway.public_url = match.group()
                    if "Registered tunnel connection" in line:
                        gateway.connected = True

        threading.Thread(target=capture, daemon=True).start()
        while not gateway.stopping.wait(0.5):
            if child.poll() is not None:
                raise RuntimeError("cloudflared exited; inspect cloudflared.log")
    finally:
        gateway.connected = False
        gateway.shutdown()
        gateway.server_close()
        thread.join(timeout=5)
        if child is not None:
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait(timeout=5)
            child.stdout.close()
        if os.name == "nt":
            ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)


if __name__ == "__main__":
    main()
