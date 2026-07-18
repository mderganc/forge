"""Shared pytest configuration for Forge tests.

Clears host-level FORGE_SKIP_* automation flags so tests exercise default
product behavior. Individual tests may still setenv to assert skip paths.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_SKIP_ENV_VARS = (
    "FORGE_SKIP_AUTO_CLOSE",
    "FORGE_SKIP_SESSION_OPTIN",
    "FORGE_SKIP_GRAPHIFY",
    "FORGE_SKIP_GRAPHIFY_SESSION_REFRESH",
    "FORGE_SKIP_STRUCTURAL_EIGHT_AGENTS",
)


@pytest.fixture(autouse=True)
def _clear_forge_skip_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _SKIP_ENV_VARS:
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def fixture_project() -> Path:
    """Canonical mock-flows-target fixture for layout/recommendation tests."""
    root = Path(__file__).resolve().parent / "fixtures" / "mock-flows-target"
    assert root.is_dir(), f"missing fixture project: {root}"
    return root
