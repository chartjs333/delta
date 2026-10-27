"""T047/T053 reproducible COMPONENT qualification; no R2.3/seed-producer claim."""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "formal/proposals/evidence/profile-seed-pvss"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    receipt = OUT / "receipt.json"
    receipt.unlink(missing_ok=True)
    paths = [
        ROOT / "formal/proposals/seed-pvss-component-contract.md",
        Path(__file__),
        Path(__file__).with_name("ProfileSeedPvss.lean"),
    ]
    for folder in ("seed_source", "isc_crypto", "isc_source", "isc_w1"):
        paths += sorted((ROOT / "formal/reference" / folder).glob("*.py"))
    sources = {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in paths}
    lean = Path(os.environ["FAMILY_LEAN"])
    packages = Path(os.environ["PVSS_MATHLIB_PACKAGES"])
    actual = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=packages / "mathlib", text=True
    ).strip()
    if actual != "520045ab14e26149ee970e2e617ca04b09bde5d6":
        raise RuntimeError("Wrong pinned mathlib revision")
    env = dict(os.environ)
    env["LEAN_PATH"] = os.pathsep.join(
        str(p / ".lake/build/lib/lean") for p in packages.iterdir() if p.is_dir()
    )
    checks = []

    def run(command, log, environment=env):
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf8",
            timeout=600,
            check=False,
        )
        output = result.stdout + result.stderr
        (OUT / log).write_text(output, encoding="utf8", newline="\n")
        checks.append(dict(log=log, exit_code=result.returncode, sha256=sha(output.encode())))
        if result.returncode:
            raise RuntimeError(log + " failed: " + output[-3000:])
        return output

    version = run([str(lean), "--version"], "lean-version.txt").strip()
    if "4.32.1" not in version:
        raise RuntimeError("Wrong pinned Lean toolchain")
    logs = run(
        [str(lean), "formal/proposals/b-family-transfer/ProfileSeedPvss.lean"],
        "proof-and-axioms.txt",
    )
    axioms = re.findall(r"'([^']+)' depends on axioms: \[([^]]*)\]", logs)
    if len(axioms) != 8 or any(set(a.replace(" ", "").split(",")) - {"propext"} for _, a in axioms):
        raise RuntimeError("Incomplete/unexpected axiom audit")
    run(
        [sys.executable, "-m", "unittest", "formal.reference.seed_source.test_pvss", "-v"],
        "reference-tests.txt",
    )
    run(
        [sys.executable, "formal/reference/isc_crypto/test_signatures.py", "-v"],
        "signature-regression.txt",
    )
    sys.path.insert(0, str(ROOT))
    from formal.reference.seed_source import pvss as p
    from formal.reference.seed_source.test_pvss import fixture, make_deal, make_open

    group, seeds, boot, ctx = fixture()
    raw = make_deal(group, seeds, boot, ctx)
    openings = tuple(make_open(group, seeds, boot, ctx, raw, actor) for actor in seeds)
    vector = dict(
        classification="SYNTHETIC_PUBLIC_TEST_ONLY",
        context=ctx,
        public_keys={actor: key.hex() for actor, key in boot.validators},
        generator=group.h.hex(),
        generator_counter=group.generator_counter,
        original_deal_hex=raw.hex(),
        original_openings_hex=[x.hex() for x in openings],
        reconstructed_point=p.reconstruct(group, boot, ctx, raw, openings).hex(),
    )
    (OUT / "vector.json").write_text(json.dumps(vector, sort_keys=True, indent=2) + "\n", "utf8")
    if sources != {p.relative_to(ROOT).as_posix(): sha(p.read_bytes()) for p in paths}:
        raise RuntimeError("Sources changed during qualification")
    pin = json.loads(
        (ROOT / "formal/reference/isc_crypto/library-provenance.json").read_text("utf8")
    )
    data = dict(
        status="PVSS_COMPONENT_CHECKED",
        r23="OPEN",
        formal="NO_GO",
        contract="formal/proposals/seed-pvss-component-contract.md",
        sources=sources,
        lean=version,
        lean_binary_sha256=sha(lean.read_bytes()),
        mathlib_commit=actual,
        library_sha256=pin["dll"]["sha256"],
        checks=checks,
        vector_sha256=sha((OUT / "vector.json").read_bytes()),
        axioms={name: values.split(", ") for name, values in axioms},
        remaining="whole bias-resistant producer, prior agreement/release, coins, "
        "durability/source fold and complete R2.3 relation; no seed authority claimed",
    )
    receipt.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n", "utf8")
    print(
        json.dumps(
            {
                "status": data["status"],
                "r23": data["r23"],
                "receipt_sha256": sha(receipt.read_bytes()),
            }
        )
    )


if __name__ == "__main__":
    main()
