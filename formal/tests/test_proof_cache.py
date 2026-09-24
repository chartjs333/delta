from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "formal/toolchain"))
sys.path.insert(0, str(ROOT / "formal/scripts"))

import prepare_proof_cache as cache  # noqa: E402
import run_formal_gate as gate  # noqa: E402


class ProofCacheTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="delta-proof-cache-test-")
        self.addCleanup(self.temporary.cleanup)
        self.proofs = Path(self.temporary.name)
        self.package = self.proofs / ".lake/packages/mathlib"
        self.package.mkdir(parents=True)
        cache.git(self.package, "init", "--quiet")
        cache.git(self.package, "config", "core.autocrlf", "false")
        cache.git(self.package, "config", "core.eol", "lf")
        cache.git(self.package, "config", "user.name", "Proof cache test")
        cache.git(self.package, "config", "user.email", "test@example.invalid")
        cache.git(self.package, "config", "commit.gpgsign", "false")
        self.url = "https://github.com/leanprover-community/mathlib4"
        cache.git(self.package, "remote", "add", "origin", self.url)
        for name, content in {
            "LICENSE": "test license\n",
            "lean-toolchain": "leanprover/lean4:v4.32.1\n",
            "lake-manifest.json": '{"packages":[]}\n',
            "Example.lean": "example : True := trivial\n",
            ".gitignore": ".lake/\n",
        }.items():
            (self.package / name).write_bytes(content.encode())
        cache.git(self.package, "add", ".")
        cache.git(self.package, "commit", "--quiet", "-m", "local test fixture")
        self.rev = cache.git(self.package, "rev-parse", "HEAD")
        (self.proofs / "lean-toolchain").write_bytes((self.package / "lean-toolchain").read_bytes())
        self.lock = {
            "source": {"lake_manifest_sha256": cache.sha256(self.package / "lake-manifest.json")},
            "packages": [
                {
                    "name": "mathlib",
                    "url": self.url,
                    "rev": self.rev,
                    "license_path": "LICENSE",
                    "license_sha256": cache.sha256(self.package / "LICENSE"),
                }
            ],
        }
        self.manifest = {
            "packagesDir": ".lake/packages",
            "packages": [
                {
                    "name": "mathlib",
                    "url": self.url,
                    "rev": self.rev,
                    "type": "git",
                    "subDir": None,
                    "manifestFile": "lake-manifest.json",
                    "configFile": "lakefile.toml",
                }
            ],
        }
        self.save_locks()

    def save_locks(self) -> None:
        for name, data in (
            ("dependencies.lock.json", self.lock),
            ("lake-manifest.json", self.manifest),
        ):
            (self.proofs / name).write_text(json.dumps(data), encoding="utf-8")

    def test_exact_sources_verify_without_network_or_writes(self) -> None:
        before = cache.git(self.package, "status", "--porcelain")
        with patch.object(cache, "git", wraps=cache.git) as calls:
            report = cache.verify_packages(self.proofs)
        self.assertEqual(report["status"], "PASS")
        self.assertFalse(report["compiled_cache_provenance_verified"])
        self.assertTrue(all("fetch" not in call.args for call in calls.call_args_list))
        self.assertEqual(cache.git(self.package, "status", "--porcelain"), before)

    def test_missing_source_fails_before_lake_can_fetch(self) -> None:
        absent = self.proofs / "missing"
        absent.mkdir()
        (absent / "dependencies.lock.json").write_bytes(
            (self.proofs / "dependencies.lock.json").read_bytes()
        )
        (absent / "lake-manifest.json").write_bytes(
            (self.proofs / "lake-manifest.json").read_bytes()
        )
        with patch.object(gate, "PROOFS", absent), patch.object(gate, "run") as run:
            with self.assertRaisesRegex(ValueError, "Missing materialized dependency"):
                gate.run_proofs()
        run.assert_not_called()
        self.assertFalse((absent / ".lake").exists())

    def test_modified_sources_are_not_repaired_by_download(self) -> None:
        changed = self.package / "Example.lean"
        changed.write_text("unreviewed change", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "modified/untracked"):
            cache.download_packages(self.proofs)
        self.assertEqual(changed.read_text(), "unreviewed change")

    def test_untracked_import_is_rejected(self) -> None:
        (self.package / "Injected.lean").write_text("example : True := trivial")
        with self.assertRaisesRegex(ValueError, "modified/untracked"):
            cache.verify_packages(self.proofs)

    def test_revision_mismatch_is_rejected(self) -> None:
        cache.git(self.package, "commit", "--allow-empty", "--quiet", "-m", "another revision")
        with self.assertRaisesRegex(ValueError, "revision mismatch"):
            cache.verify_packages(self.proofs)

    def test_remote_substitution_is_rejected(self) -> None:
        cache.git(self.package, "remote", "set-url", "origin", "https://github.com/example/fake")
        with self.assertRaisesRegex(ValueError, "URL mismatch"):
            cache.verify_packages(self.proofs)

    def test_license_hash_is_verified(self) -> None:
        self.lock["packages"][0]["license_sha256"] = hashlib.sha256(b"other license").hexdigest()
        self.save_locks()
        with self.assertRaisesRegex(ValueError, "license mismatch"):
            cache.verify_packages(self.proofs)

    def test_upstream_manifest_hash_is_verified(self) -> None:
        self.lock["source"]["lake_manifest_sha256"] = "0" * 64
        self.save_locks()
        with self.assertRaisesRegex(ValueError, "upstream manifest mismatch"):
            cache.verify_packages(self.proofs)

    def test_manifest_cannot_select_another_url(self) -> None:
        self.manifest["packages"][0]["url"] = "https://github.com/example/fake"
        self.save_locks()
        with self.assertRaisesRegex(ValueError, "manifest differs"):
            cache.verify_packages(self.proofs)

    def test_package_name_cannot_escape_cache(self) -> None:
        self.lock["packages"][0]["name"] = "../../outside"
        self.save_locks()
        with self.assertRaisesRegex(ValueError, "Unsafe package name"):
            cache.verify_packages(self.proofs)

    def test_manifest_cannot_redirect_package_configuration(self) -> None:
        for field, value in (
            ("type", "path"),
            ("subDir", "../../outside"),
            ("configFile", "../../other.lean"),
            ("manifestFile", "../../other.json"),
        ):
            with self.subTest(field=field):
                original = self.manifest["packages"][0][field]
                self.manifest["packages"][0][field] = value
                self.save_locks()
                with self.assertRaisesRegex(ValueError, "redirects a locked package"):
                    cache.verify_packages(self.proofs)
                self.manifest["packages"][0][field] = original

    def test_toolchain_mismatch_is_rejected(self) -> None:
        (self.proofs / "lean-toolchain").write_text("leanprover/lean4:v0.0.0")
        with self.assertRaisesRegex(ValueError, "toolchain mismatch"):
            cache.verify_packages(self.proofs)


if __name__ == "__main__":
    unittest.main()
