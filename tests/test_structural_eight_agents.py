"""Tests for Civil Learning eight-agent dispatch banner."""

from __future__ import annotations

import pytest

from scripts.shared import structural_eight_agents as sea


def test_master_prompt_contains_eight_missions() -> None:
    assert "8 subagents" in sea.CIVIL_LEARNING_MASTER_PROMPT
    assert "knip" in sea.CIVIL_LEARNING_MASTER_PROMPT
    assert "madge" in sea.CIVIL_LEARNING_MASTER_PROMPT
    assert "AI slop" in sea.CIVIL_LEARNING_MASTER_PROMPT


def test_eight_agents_table_has_s1_through_s8() -> None:
    assert len(sea.EIGHT_AGENTS) == 8
    assert [a["id"] for a in sea.EIGHT_AGENTS] == [
        "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"
    ]


def test_dispatch_banner_includes_master_prompt_and_spawn_table() -> None:
    banner = sea.format_eight_agents_dispatch_banner(quick_mode=False)
    assert "STRUCTURAL QUALITY — eight parallel subagents" in banner
    assert "8 subagents" in banner
    assert "S3" in banner and "knip" in banner
    assert "structural-quality-eight-agents.md" in banner
    assert sea.SIDECAR_NAME in banner


def test_quick_mode_limits_agents() -> None:
    assert len(sea.agents_for_mode(quick_mode=True)) == 3
    banner = sea.format_eight_agents_dispatch_banner(quick_mode=True)
    assert "S3, S4, S8" in banner


def test_template_file_exists() -> None:
    text = sea.load_eight_agents_template()
    assert "Civil Learning" in text
    assert "S1" in text


def test_should_dispatch_eight_agents_matrix() -> None:
    assert sea.should_dispatch_eight_agents("code-review", 3)
    assert sea.should_dispatch_eight_agents("evaluate", 1, mode="review")
    assert not sea.should_dispatch_eight_agents("evaluate", 4, mode="post")
    assert not sea.should_dispatch_eight_agents("evaluate", 4, mode="pre")


def test_default_eight_agents_quick_mode() -> None:
    assert sea.default_eight_agents_quick_mode(user_quick=False) is True
    assert sea.default_eight_agents_quick_mode(user_quick=True) is True


def test_skip_structural_eight_agents(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("FORGE_SKIP_STRUCTURAL_EIGHT_AGENTS", "1")
    assert sea.skip_structural_eight_agents()
    assert not sea.should_dispatch_eight_agents("code-review", 3)
