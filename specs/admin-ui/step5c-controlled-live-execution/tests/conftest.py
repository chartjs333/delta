"""Pytest path bootstrap for Step 5C security tests."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[4]

for src in (
    ROOT_DIR / "delta-controller-python" / "src",
    ROOT_DIR / "delta-worker-python" / "src",
):
    src_text = str(src)
    if src_text not in sys.path:
        sys.path.insert(0, src_text)
