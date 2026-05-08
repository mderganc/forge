"""Shared pytest fixtures for regression tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = REPO_ROOT / "tests" / "fixtures"


@pytest.fixture
def fixture_project(tmp_path: Path) -> Path:
    """Factory: copy mock-flows-target fixture to tmp_path and return the path.

    Provides a minimal FastAPI project with:
    - pyproject.toml (pytest declared)
    - app/main.py (FastAPI HTTP endpoints)
    - app/models.py (SQLite storage)
    - app/roles.yaml (3-role policy file)
    - tests/conftest.py (test fixtures)

    Use in tests as:
        def test_something(fixture_project):
            fixture_path = fixture_project
            result = detect_test_layout(fixture_path)
    """
    src = FIXTURES_DIR / "mock-flows-target"
    if not src.exists():
        pytest.skip(f"Fixture project not found at {src}")

    dst = tmp_path / "fixture-project"
    shutil.copytree(src, dst)
    return dst
