"""Tests for code-review effort/structural recommendation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def add_repo_to_path():
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))


class _Args:
  def __init__(self, **kwargs):
    for k, v in kwargs.items():
      setattr(self, k, v)


def test_quick_always_light_no_structural():
    from scripts.code_review.effort_recommendation import recommend_effort_structural

    rec = recommend_effort_structural(
        mode="pr",
        target="",
        target_tokens=[],
        quick=True,
    )
    assert rec.effort == "light"
    assert rec.structural is False


def test_architecture_mode_recommends_thorough_structural():
    from scripts.code_review.effort_recommendation import recommend_effort_structural

    rec = recommend_effort_structural(
        mode="architecture",
        target="src/",
        target_tokens=["src/"],
    )
    assert rec.effort == "thorough"
    assert rec.structural is True


def test_small_handoff_recommends_light():
    from scripts.code_review.effort_recommendation import recommend_effort_structural

    rec = recommend_effort_structural(
        mode="pr",
        target="",
        target_tokens=[],
        handoff_content="## Summary\n\n2 files changed\n",
    )
    assert rec.effort == "light"
    assert rec.structural is False


def test_large_handoff_recommends_thorough_structural():
    from scripts.code_review.effort_recommendation import recommend_effort_structural

    rec = recommend_effort_structural(
        mode="pr",
        target="",
        target_tokens=[],
        handoff_content="## Summary\n\n24 files changed\nRefactor across modules.\n",
    )
    assert rec.effort == "thorough"
    assert rec.structural is True


def test_resolve_applied_config_uses_recommendation_by_default():
    from scripts.code_review.effort_recommendation import (
        EffortRecommendation,
        resolve_applied_config,
    )

    rec = EffortRecommendation(effort="thorough", structural=True, reasoning=["test"])
    args = _Args(quick=False, effort=None, structural=None)
    effort, structural, e_ov, s_ov = resolve_applied_config(args, rec)
    assert effort == "thorough"
    assert structural is True
    assert e_ov is False
    assert s_ov is False


def test_resolve_applied_config_cli_override():
    from scripts.code_review.effort_recommendation import (
        EffortRecommendation,
        resolve_applied_config,
    )

    rec = EffortRecommendation(effort="thorough", structural=True, reasoning=["test"])
    args = _Args(quick=False, effort="light", structural=False)
    effort, structural, e_ov, s_ov = resolve_applied_config(args, rec)
    assert effort == "light"
    assert structural is False
    assert e_ov is True
    assert s_ov is True


def test_format_effort_config_section_mentions_override():
    from scripts.code_review.effort_recommendation import (
        EffortRecommendation,
        format_effort_config_section,
    )

    rec = EffortRecommendation(
        effort="thorough",
        structural=True,
        reasoning=["Large scope"],
        confidence=0.9,
    )
    text = format_effort_config_section(
        rec,
        applied_effort="light",
        applied_structural=False,
        effort_overridden=True,
        structural_overridden=True,
    )
    assert "CLI override" in text
    assert "`--effort`" in text
    assert "Large scope" in text
