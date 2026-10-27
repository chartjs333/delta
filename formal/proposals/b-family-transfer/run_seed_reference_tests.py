"""Run seed regressions and record executed repository import closure for qualification."""

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))


def main():
    suite = unittest.defaultTestLoader.discover(
        str(ROOT / "formal/reference/seed_source"), pattern="test_*.py"
    )
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    files = sorted(
        {
            Path(module.__file__).resolve().relative_to(ROOT).as_posix()
            for module in tuple(sys.modules.values())
            if getattr(module, "__file__", None)
            and Path(module.__file__).is_file()
            and Path(module.__file__).resolve().is_relative_to(ROOT)
        }
    )
    out = ROOT / "formal/proposals/evidence/profile-seed-agreement/executed-imports.json"
    out.write_text(json.dumps(files, indent=2) + "\n", "utf8", newline="\n")
    # The evidence describes the executed regression closure, not every possible
    # dynamic import in an unexercised branch. Sources are also explicitly pinned.
    if not result.wasSuccessful() or not result.testsRun:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
