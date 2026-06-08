"""Canonical skill names and legacy aliases (e.g. develop → design)."""

from __future__ import annotations

_DESIGN_ALIASES = frozenset({"design", "develop"})


def skill_name_variants(skill: str) -> frozenset[str]:
    """Return equivalent skill slugs for session/handoff lookup."""
    slug = skill.strip().lower().replace("_", "-")
    if slug in _DESIGN_ALIASES:
        return set(_DESIGN_ALIASES)
    return {slug}


def skills_match(stored: str, requested: str) -> bool:
    """True when persisted ``stored`` skill matches ``requested`` (with aliases)."""
    return stored.strip().lower().replace("_", "-") in skill_name_variants(requested)
