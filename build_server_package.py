"""Build a sanitized CDS server package from the canonical deployment directory."""

from __future__ import annotations

import os
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DEPLOY_DIR = ROOT_DIR / "cds_server_deploy"
ZIP_PATH = ROOT_DIR / "cds_server_deploy.zip"

REQUIRED_FILES = (
    "server.py",
    "pipeline_service.py",
    "requirements.txt",
    "README.md",
    ".env.example",
    "model_10genes_phenotype_classifier.json",
    "clinical_ontology_v1.json",
    "input_schema_v1.json",
    "safety_thresholds_v2.json",
    "support_index_v2.json",
    "compatibility_manifest_v2.json",
    "static/index.html",
    "static/app.js",
    "static/style.css",
)

EXCLUDED_NAMES = {
    ".env",
    ".pipeline_cache.json",
}

EXCLUDED_DIRS = {
    ".venv",
    "__pycache__",
}


def _assert_required_files() -> None:
    missing = [rel for rel in REQUIRED_FILES if not (DEPLOY_DIR / rel).exists()]
    if missing:
        raise SystemExit(f"Missing deployment file(s): {missing}")


def _refresh_safety_manifest() -> None:
    freezer = DEPLOY_DIR / "freeze_safety_artifacts.py"
    subprocess.check_call([sys.executable, str(freezer)], cwd=str(ROOT_DIR))


def _include_file(path: Path) -> bool:
    rel_parts = path.relative_to(DEPLOY_DIR).parts
    if any(part in EXCLUDED_DIRS for part in rel_parts):
        return False
    if path.name in EXCLUDED_NAMES:
        return False
    if path.suffix.lower() in {".pyc", ".pyo"}:
        return False
    return True


def build_zip() -> None:
    _assert_required_files()
    _refresh_safety_manifest()
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as archive:
        for root, dirs, files in os.walk(DEPLOY_DIR):
            dirs[:] = [name for name in dirs if name not in EXCLUDED_DIRS]
            for filename in files:
                full_path = Path(root) / filename
                if not _include_file(full_path):
                    continue
                archive.write(full_path, full_path.relative_to(DEPLOY_DIR))
    print(f"Created {ZIP_PATH} ({ZIP_PATH.stat().st_size / (1024 * 1024):.2f} MiB)")


if __name__ == "__main__":
    build_zip()
