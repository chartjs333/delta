"""T010: Process and package boundary verification."""

from __future__ import annotations

import sys


def test_controller_does_not_import_browser_state() -> None:
    """Ensure controller package has zero dependencies on browser automation libraries or DOM."""
    import deltacontroller  # noqa: F401

    forbidden_packages = ["playwright", "selenium", "puppeteer", "jsdom", "webdriver"]
    for mod_name in sys.modules:
        top_pkg = mod_name.split(".")[0].lower()
        if top_pkg in forbidden_packages:
            msg = f"Forbidden browser automation module found in sys.modules: {mod_name}"
            raise AssertionError(msg)


def test_controller_does_not_import_native_consensus_apis() -> None:
    """Ensure controller package does not import C++ consensus WAL, FFM, or reactors."""
    import deltacontroller  # noqa: F401

    forbidden_consensus = [
        "delta_core_cpp",
        "delta_runtime_cpp",
        "delta_ffi",
        "deltanode",
    ]
    for mod_name in sys.modules:
        top_pkg = mod_name.split(".")[0].lower()
        if top_pkg in forbidden_consensus:
            raise AssertionError(f"Forbidden consensus module found in sys.modules: {mod_name}")


def test_controller_package_version_and_exports() -> None:
    """Verify package version and expected core symbols."""
    import deltacontroller

    assert deltacontroller.__version__ == "1.0.0"
    assert hasattr(deltacontroller, "AuthorizationGate")
    assert hasattr(deltacontroller, "IngressParser")
    assert hasattr(deltacontroller, "CatalogValidator")
    assert hasattr(deltacontroller, "IdempotencyLedger")
    assert hasattr(deltacontroller, "QuotaManager")
