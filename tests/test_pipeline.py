"""Tests for scripts.shared.pipeline."""

from scripts.shared.pipeline import (
    PIPELINE_FLOW,
    PIPELINE_SKILL_ORDER,
    next_pipeline_skill,
)


def test_pipeline_flow_derived_from_order() -> None:
    assert PIPELINE_SKILL_ORDER[-1] == "diagnose"
    assert PIPELINE_FLOW["diagnose"] is None
    assert PIPELINE_FLOW["develop"] == "plan"
    assert PIPELINE_FLOW["code-review"] == "test"
    assert next_pipeline_skill("implement") == "code-review"
