"""Canonical Forge workflow pipeline order and handoff flow."""

from __future__ import annotations

# Explicit pipeline order — never iterate PIPELINE_SKILLS set for ordering.
PIPELINE_SKILL_ORDER: tuple[str, ...] = (
    "design",
    "plan",
    "implement",
    "code-review",
    "test",
    "diagnose",
)

PIPELINE_SKILL_INDEX: dict[str, int] = {
    name: idx for idx, name in enumerate(PIPELINE_SKILL_ORDER)
}

# Next skill after each pipeline skill completes (evaluate/iterate/ship are out of band).
PIPELINE_FLOW: dict[str, str | None] = {
    skill: (
        PIPELINE_SKILL_ORDER[i + 1]
        if i + 1 < len(PIPELINE_SKILL_ORDER)
        else None
    )
    for i, skill in enumerate(PIPELINE_SKILL_ORDER)
}
PIPELINE_FLOW["evaluate"] = None
PIPELINE_FLOW["iterate"] = None
PIPELINE_FLOW["ship"] = None


def next_pipeline_skill(current_skill: str) -> str | None:
    """Return the suggested next skill in the main pipeline, or None."""
    return PIPELINE_FLOW.get(current_skill)
