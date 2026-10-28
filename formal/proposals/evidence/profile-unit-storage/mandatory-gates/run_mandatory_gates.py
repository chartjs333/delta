"""Run the exact formal-check recipes sequentially; preserve first failure."""

import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path("C:/Users/madoev/.codex/worktrees/isc-s16-sequential/delta")
OUT = Path(__file__).resolve().parent / "mandatory-gates"
RECIPES = [
    ("phase0", ["formal/scripts/verify_phase0.py"]),
    ("contracts", ["-m", "unittest", "discover", "-s", "formal/tests", "-p", "test_*.py"]),
    ("toolchain", ["formal/toolchain/verify_locks.py"]),
    *[(g, ["formal/scripts/run_formal_gate.py", g]) for g in
      ("parse", "safety", "liveness", "proofs", "mutants", "refinement", "report")],
]


def main():
    OUT.mkdir(exist_ok=False)
    environment = dict(os.environ, PYTHONUTF8="1",
        JAVA="D:/formal-tools-20260920/java/bin/java.exe",
        TLA2TOOLS_JAR="D:/formal-tools-20260920/tla/tla2tools.jar",
        LAKE="D:/formal-tools-20260920/lean/bin/lake.exe",
        ISC_SODIUM_DLL="D:/delta/.cache/isc-s16-libsodium-1.0.22/x64-release-v143-libsodium.dll")
    evidence = {
        "task_ids": ["T047", "T053"],
        "formal": "NO_GO", "R23": "OPEN",
        "command_equivalence": "Exact Makefile formal-check recipes, sequentially; GNU make unavailable",
        "makefile_sha256": hashlib.sha256((ROOT / "Makefile").read_bytes().replace(b"\r\n", b"\n")).hexdigest(),
        "gates": [],
    }
    failed = False
    for index, (name, args) in enumerate(RECIPES):
        print("Starting " + name, flush=True)
        started = time.monotonic()
        path = OUT / (name + ".txt")
        command = [sys.executable, *args]
        with path.open("wb") as log:
            result = subprocess.run(command, cwd=ROOT, env=environment, stdout=log,
                                    stderr=subprocess.STDOUT, check=False)
        evidence["gates"].append({"gate": name, "command": command,
            "exit_code": result.returncode, "log": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "wall_seconds": round(time.monotonic() - started, 2)})
        print(name + " exit " + str(result.returncode), flush=True)
        evidence["not_run"] = [n for n, _ in RECIPES[index + 1:]]
        (OUT / "result.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        if result.returncode:
            failed = True
            print(path.read_text(encoding="utf-8", errors="replace")[-5000:], flush=True)
            break
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
