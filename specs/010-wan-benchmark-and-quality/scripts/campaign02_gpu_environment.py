"""Write or verify the immutable Campaign 02 GPU environment lock and SBOM."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "delta-worker-python/src"))

from deltatorrent.benchmark.gpu_environment import (  # noqa: E402
    verify_gpu_environment_outputs,
    write_gpu_environment_lock,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    arguments = parser.parse_args()
    lock = (
        write_gpu_environment_lock(ROOT)
        if arguments.write
        else verify_gpu_environment_outputs(ROOT)
    )
    print(
        json.dumps(
            {
                "gpu_environment_lock_id": lock.content_id,
                "platform_lock_count": len(lock.document["platform_locks"]),
                "sbom_id": lock.sbom_id,
                "status": "PASS",
            },
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
