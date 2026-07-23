"""Tests for evaluate size/effort ceremony scaling."""

from __future__ import annotations

from scripts.evaluate.evaluate_effort import (
    infer_size_from_plan,
    should_skip_phase,
)


def test_infer_size_quick_is_small():
    size, _ = infer_size_from_plan("anything", quick=True)
    assert size == "small"


def test_infer_size_trivial_plan():
    size, _ = infer_size_from_plan("scope_tier: trivial\nPlan mode: lite")
    assert size == "small"


def test_skip_pre_heavy_for_small():
    assert should_skip_phase("pre", 4, "small") is True
    assert should_skip_phase("pre", 5, "small") is True
    assert should_skip_phase("pre", 2, "small") is False


def test_skip_post_heavy_for_small():
    assert should_skip_phase("post", 5, "small") is True
    assert should_skip_phase("post", 6, "small") is True
    assert should_skip_phase("post", 3, "small") is False


def test_no_skip_for_medium():
    assert should_skip_phase("pre", 4, "medium") is False
    assert should_skip_phase("post", 5, "medium") is False
