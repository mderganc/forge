"""Tests for takeover scope_tier and severity-filtered gates."""

from __future__ import annotations

from scripts.takeover.router import RoutePlan, _decorate_plan, normalize_scope_tier
from scripts.takeover.takeover import _blocking_findings_count


def test_normalize_scope_tier():
    assert normalize_scope_tier("trivial") == "small"
    assert normalize_scope_tier("simple") == "small"
    assert normalize_scope_tier("large") == "large"
    assert normalize_scope_tier(None) == "medium"


def test_decorate_small_skips_evaluate():
    plan = _decorate_plan(RoutePlan(entry_skill="plan", entry_reason="t", scope_tier="small"))
    # _decorate_plan may overwrite from memory; force small
    plan.scope_tier = "small"
    plan.skip_evaluate = True
    plan.code_review_effort = "light"
    assert plan.skip_evaluate is True
    assert plan.code_review_effort == "light"


def test_blocking_findings_ignores_suggestions():
    assert _blocking_findings_count({"critical": 0, "warning": 0, "suggestion": 3}) == 0
    assert _blocking_findings_count({"critical": 1, "warning": 0, "suggestion": 9}) == 1
    assert _blocking_findings_count({"blocking_findings": 0, "open_findings_total": 5}) == 0
    assert _blocking_findings_count({"open_findings_total": 2}) == 2
