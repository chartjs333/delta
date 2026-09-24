"""Mount the user's existing MNIST runner without editing its working tree.

The isolated process imports from the explicitly configured source checkout.
Only the presentation layer, a health identity and last-view persistence are added.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import threading
from http import HTTPStatus
from pathlib import Path
from urllib.parse import urlsplit

from node_training_view import GET_ROUTES, PREFIX, RUN_ROUTE, adapt_page


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--instance", required=True)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    args.data.mkdir(parents=True, exist_ok=True)
    sys.path.insert(0, str(source / "delta-worker-python/src"))
    from deltatorrent.benchmark import mnist_demo_workspace as workspace

    original_page = workspace._localized_workspace_html
    workspace._localized_workspace_html = lambda lang: adapt_page(original_page(lang), lang)
    snapshot_path = args.data / "last-view.json"

    class SavedState(workspace.WorkspaceState):
        def __init__(self, *values, **options):
            super().__init__(*values, **options)
            self._save_gate = threading.Lock()
            if snapshot_path.is_file():
                try:
                    saved = json.loads(snapshot_path.read_text(encoding="utf-8"))
                    if saved.get("result"):
                        self._result = workspace._validate_workspace_report(saved["result"])
                        self._percent = 100
                        self._stage = "complete"
                        self._message = "Демо завершено: фактические метрики готовы"
                        self._last_output_dir = saved.get("last_output_dir")
                except (ValueError, TypeError, KeyError, OSError):
                    # Invalid saved evidence never becomes a displayed successful result.
                    self._error = "SAVED_DEMO_RESULT_INVALID"

        def start(self):
            # The original runner clears running before returning. Retain this
            # admission gate until its snapshot is saved, so a rapid retry cannot
            # clear the result while the previous run is persisting its view.
            if not self._save_gate.acquire(blocking=False):
                return False
            if not super().start():
                self._save_gate.release()
                return False
            return True

        def _execute(self):
            try:
                super()._execute()
                temporary = snapshot_path.with_suffix(".tmp")
                temporary.write_text(
                    json.dumps(self.snapshot(), ensure_ascii=False), encoding="utf-8"
                )
                temporary.replace(snapshot_path)
            finally:
                self._save_gate.release()

    class MountedHandler(workspace.WorkspaceRequestHandler):
        def valid_host(self):
            return self.headers.get("Host") == "127.0.0.1:8872"

        def do_GET(self):
            if not self.valid_host():
                self._json(HTTPStatus.FORBIDDEN, {"error": "HOST_FORBIDDEN"})
                return
            parts = urlsplit(self.path)
            if parts.path == PREFIX + "/api/health":
                self._json(
                    HTTPStatus.OK,
                    {
                        "service": "delta-node-training-example",
                        "instance_id": args.instance,
                        "pid": os.getpid(),
                        "source": str(source),
                        "running": self.state.snapshot()["running"],
                        "mode": "LOCAL_DEMO_ONLY",
                    },
                )
            elif parts.path in GET_ROUTES:
                self.path = self.path.removeprefix(PREFIX)
                super().do_GET()
            else:
                self._json(HTTPStatus.NOT_FOUND, {"error": "NOT_FOUND"})

        def do_POST(self):
            if not self.valid_host() or self.headers.get("Origin") != "http://127.0.0.1:8872":
                self._json(HTTPStatus.FORBIDDEN, {"error": "ORIGIN_FORBIDDEN"})
                return
            if self.path != RUN_ROUTE:
                self._json(HTTPStatus.NOT_FOUND, {"error": "NOT_FOUND"})
                return
            if (
                self.headers.get("Transfer-Encoding")
                or len(self.headers.get_all("Content-Length", [])) > 1
                or self.headers.get("Content-Length", "0") != "0"
            ):
                self._json(HTTPStatus.BAD_REQUEST, {"error": "REQUEST_BODY_NOT_ALLOWED"})
                return
            self.path = "/api/run"
            super().do_POST()

    workspace.WorkspaceState = SavedState
    workspace.WorkspaceRequestHandler = MountedHandler
    workspace.serve_workspace(
        source,
        source / "artifacts/local/mnist-cache",
        args.data / "runs",
        allow_download=False,
        port=8872,
        open_browser=False,
    )


if __name__ == "__main__":
    main()
