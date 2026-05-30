"""Graphify disable / ship-only orchestrator banners."""

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
    assert forge_graphify_banner("ship", 1, prefs_repo) == ""
    assert forge_graphify_banner("implement", 3, prefs_repo) == ""
    assert skip_graphify_refresh_spawn(prefs_repo)


def test_repo_prefs_off_disables_banner(
    prefs_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from forge_next.graphify_enforcement import set_graphify_disabled
    from scripts.shared.graphify_contract import forge_graphify_banner

    monkeypatch.delenv("FORGE_SKIP_GRAPHIFY", raising=False)
    set_graphify_disabled(prefs_repo, disabled=True)
    assert forge_graphify_banner("ship", 1, prefs_repo) == ""
    assert forge_graphify_banner("develop", 1, prefs_repo) == ""


def test_workflow_skills_suppress_graphify_banner(
    prefs_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.shared.graphify_contract import forge_graphify_banner

    monkeypatch.delenv("FORGE_SKIP_GRAPHIFY", raising=False)
    for skill in ("develop", "implement", "code-review", "plan", "test", "diagnose", "evaluate"):
        assert forge_graphify_banner(skill, 1, prefs_repo) == ""
        assert forge_graphify_banner(skill, 6, prefs_repo) == ""


def test_ship_shows_graphify_banner(
    prefs_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.shared.graphify_contract import forge_graphify_banner

    monkeypatch.delenv("FORGE_SKIP_GRAPHIFY", raising=False)
    banner = forge_graphify_banner("ship", 1, prefs_repo)
    assert "GRAPHIFY — refresh before you ship" in banner
    assert "GRAPHIFY — codebase map" not in banner


def test_forge_graphify_context_block_does_not_spawn_on_implement(
    prefs_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from scripts.shared import orchestrator as orch

    monkeypatch.delenv("FORGE_SKIP_GRAPHIFY", raising=False)
    monkeypatch.setattr(orch, "REPO_ROOT", prefs_repo)
    calls: list[Path] = []

    def fake_spawn(root: Path) -> bool:
        calls.append(root)
        return True

    monkeypatch.setattr("forge_next.graphify.spawn_refresh_background", fake_spawn)
    block = orch.forge_graphify_context_block("implement", 3)
    assert block == ""
    assert calls == []

    block_ship = orch.forge_graphify_context_block("ship", 1)
    assert "GRAPHIFY" in block_ship
    assert calls == []


def test_forge_skip_graphify_also_blocks_refresh_spawn(
    prefs_repo: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from forge_next.graphify import refresh_needed
    from forge_next.graphify_enforcement import graphify_refresh_disabled

    monkeypatch.setenv("FORGE_SKIP_GRAPHIFY", "1")
    assert graphify_refresh_disabled(prefs_repo)
    assert refresh_needed(prefs_repo) is False
