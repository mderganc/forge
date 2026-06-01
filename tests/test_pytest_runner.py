"""Tests for forge:test pytest auto-run helpers."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from scripts.test.pytest_runner import (
    _parse_pytest_summary,
    apply_results_to_state_custom,
    default_pytest_command,
    format_execution_log,
    parse_pytest_argv,
    pytest_subprocess_env,
    should_run_pytest,
    skip_test_auto_run,
)


def test_parse_pytest_summary_passed_only() -> None:
    out = "358 passed in 12.34s\n"
    parsed = _parse_pytest_summary(out, "", 0)
    assert parsed["passed"] == 358
    assert parsed["failed"] == 0
    assert parsed["total"] == 358
    assert parsed["ok"] is True
    assert parsed["duration_s"] == 12.34


def test_parse_pytest_summary_mixed() -> None:
    out = "6 failed, 352 passed, 2 skipped in 8.08s\n"
    parsed = _parse_pytest_summary(out, "", 1)
    assert parsed["failed"] == 6
    assert parsed["passed"] == 352
    assert parsed["skipped"] == 2
    assert parsed["total"] == 360
    assert parsed["ok"] is False


def test_apply_results_to_state_custom() -> None:
    custom: dict = {"test_results": {"coverage_pct": "42"}}
    apply_results_to_state_custom(
        custom,
        {
            "command": "python -m pytest tests/",
            "exit_code": 0,
            "passed": 10,
            "failed": 0,
            "skipped": 0,
            "error": 0,
            "total": 10,
            "duration_s": 1.5,
            "stdout_tail": "10 passed in 1.5s",
        },
    )
    assert custom["test_results"]["passed"] == 10
    assert custom["test_results"]["coverage_pct"] == "42"
    assert "python -m pytest" in custom["test_execution_log"]


def test_default_pytest_command_uses_tests_dir(tmp_path: Path) -> None:
    (tmp_path / "tests").mkdir()
    cmd = default_pytest_command(tmp_path)
    assert "pytest tests/" in cmd


def test_pytest_subprocess_env_strips_forge_skips(monkeypatch) -> None:
    monkeypatch.setenv("FORGE_SKIP_AUTO_CLOSE", "1")
    monkeypatch.setenv("FORGE_SKIP_SESSION_OPTIN", "1")
    monkeypatch.setenv("PATH", "/bin")
    env = pytest_subprocess_env()
    assert "FORGE_SKIP_AUTO_CLOSE" not in env
    assert "FORGE_SKIP_SESSION_OPTIN" not in env
    assert env.get("PATH") == "/bin"
    assert env.get("PYTHONUTF8") == "1"


def test_skip_test_auto_run_env(monkeypatch) -> None:
    monkeypatch.delenv("FORGE_SKIP_TEST_AUTO_RUN", raising=False)
    assert skip_test_auto_run() is False
    monkeypatch.setenv("FORGE_SKIP_TEST_AUTO_RUN", "1")
    assert skip_test_auto_run() is True


def test_parse_pytest_argv_splits_command() -> None:
    argv = parse_pytest_argv("python -m pytest tests/ -q")
    assert argv[0] == "python"
    assert "-m" in argv
    assert "pytest" in argv


def test_should_run_pytest_skips_when_results_exist(monkeypatch) -> None:
    monkeypatch.delenv("FORGE_SKIP_TEST_AUTO_RUN", raising=False)
    monkeypatch.delenv("FORGE_TEST_FORCE_RERUN", raising=False)
    assert should_run_pytest({"test_results": {"total": 10}}) is False
    monkeypatch.setenv("FORGE_TEST_FORCE_RERUN", "1")
    assert should_run_pytest({"test_results": {"total": 10}}) is True


def test_run_pytest_invokes_subprocess(tmp_path: Path) -> None:
    from scripts.test.pytest_runner import run_pytest

    fake = MagicMock()
    fake.returncode = 0
    fake.stdout = "3 passed in 0.01s\n"
    fake.stderr = ""

    with patch("scripts.test.pytest_runner.subprocess.run", return_value=fake) as run:
        result = run_pytest(tmp_path, "python -m pytest -q")

    run.assert_called_once()
    assert run.call_args.kwargs.get("shell") is False
    assert isinstance(run.call_args.args[0], list)
    assert result["passed"] == 3
    assert result["command"] == "python -m pytest -q"


def test_format_execution_log_includes_tail() -> None:
    md = format_execution_log(
        {
            "command": "pytest",
            "exit_code": 0,
            "passed": 1,
            "failed": 0,
            "skipped": 0,
            "error": 0,
            "total": 1,
            "stdout_tail": "1 passed",
        }
    )
    assert "pytest" in md
    assert "1 passed" in md
