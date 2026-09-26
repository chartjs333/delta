"""Read-only bilingual presentation, isolated from the running compute demo."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

import tunnel_gateway


def document(root: Path, language: str) -> bytes:
    name = "index_en.html" if language == "en" else "index.html"
    html = (root / name).read_text(encoding="utf-8")
    # Keep the authored content; adapt only local paths to the existing gateway.
    html = html.replace('href="index.html"', 'href="/?lang=ru"')
    html = html.replace('href="index_en.html"', 'href="/?lang=en"')
    html = html.replace('src="screenshots/', 'src="/assets/')
    return html.replace("openLightbox('screenshots/", "openLightbox('/assets/").encode("utf-8")


def handler(root: Path, instance: str):
    class SlidesHandler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            parts = urlsplit(self.path)
            if parts.path == "/":
                language = parse_qs(parts.query).get("lang", ["ru"])[0]
                if language not in {"ru", "en"}:
                    self.send_error(400)
                    return
                raw, media = document(root, language), "text/html; charset=utf-8"
            elif re.fullmatch(r"/assets/[A-Za-z0-9_-]+\.png", parts.path):
                path = root / "screenshots" / parts.path.rsplit("/", 1)[1]
                if not path.is_file() or path.is_symlink():
                    self.send_error(404)
                    return
                raw, media = path.read_bytes(), "image/png"
            elif parts.path == "/api/health":
                raw = json.dumps(
                    {
                        "service": "delta-presentation-slides",
                        "instance_id": instance,
                        "pid": os.getpid(),
                    }
                ).encode()
                media = "application/json"
            else:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header("Content-Type", media)
            self.send_header("Content-Length", str(len(raw)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'none'; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                "font-src https://fonts.gstatic.com; img-src 'self' data:; "
                "script-src 'unsafe-inline'; base-uri 'none'; frame-ancestors 'none'",
            )
            self.end_headers()
            self.wfile.write(raw)

    return SlidesHandler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slides", type=Path, required=True)
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--cloudflared", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8874)
    parser.add_argument("--upstream", type=int, default=8873)
    args = parser.parse_args()
    root = args.slides.resolve(strict=True)
    document(root, "ru")
    document(root, "en")
    control = json.loads((args.data_dir / "control.json").read_text("utf-8-sig"))
    server = ThreadingHTTPServer(
        ("127.0.0.1", args.upstream), handler(root, control["instance_id"])
    )
    server.daemon_threads = True
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    sys.argv = [
        "tunnel_gateway.py",
        "--data-dir",
        str(args.data_dir),
        "--cloudflared",
        str(args.cloudflared),
        "--port",
        str(args.port),
        "--upstream",
        str(args.upstream),
    ]
    try:
        tunnel_gateway.main()
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)


if __name__ == "__main__":
    main()
