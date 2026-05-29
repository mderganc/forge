"""Graphify disable / defer enforcement."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def prefs_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "graphify-out").mkdir()
    (tmp_path / "graphify-out" / "GRAPH_REPORT.md").write_text(
        "# Graph\n\nSample report body for banner excerpt.\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_forge_skip_graphify_disables_banner_and_refresh(
    prefs_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from forge_next.graphify import skip_graphify_refresh_spawn
    from forge_next.graphify_enforcement import graphify_fully_disabled
    from scripts.shared.graphify_contract import forge_graphify_banner

    monkeypatch.setenv("FORGE_SKIP_GRAPHIFY", "1")
    assert graphify_fully_disabled(prefs_repo)
    assert forge_graphify_banner("implement", 3, prefs_repo) == ""
    assert skip_graphify_refresh_spawn(prefs_repo)


def test_repo_prefs_off_disables_banner(
    prefs_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from forge_next.graphify_enforcement import set_graphify_disabled
    from scripts.shared.graphify_contract import forge_graphify_banner

    monkeypatch.delenv("FORGE_SKIP_GRAPHIFY", raising=False)
    set_graphify_disabled(prefs_repo, disabled=True)
    assert forge_graphify_banner("develop", 1, prefs_repo) == ""


def test_defer_implement_waves_suppresses_wave_steps_only(
    prefs_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from forge_next.graphify_enforcement import set_graphify_defer_implement_waves
    from scripts.shared.graphify_contract import forge_graphify_banner

    monkeypatch.delenv("FORGE_SKIP_GRAPHIFY", raising=False)
    set_graphify_defer_implement_waves(prefs_repo, defer=True)
    wave_banner = forge_graphify_banner("implement", 3, prefs_repo)
    assert "GRAPHIFY — codebase map" not in wave_banner
    assert "deferred" in wave_banner.lower()
    assert "GRAPHIFY — codebase map" in forge_graphify_banner("implement", 6, prefs_repo)


def test_forge_skip_graphify_also_blocks_refresh_spawn(
    prefs_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from forge_next.graphify import refresh_needed
    from forge_next.graphify_enforcement import graphify_refresh_disabled

    monkeypatch.setenv("FORGE_SKIP_GRAPHIFY", "1")
    assert graphify_refresh_disabled(prefs_repo)
    assert refresh_needed(prefs_repo) is False
