"""Framing entry constants for adaptive diagnose (shared, no sidecar I/O)."""

from __future__ import annotations

FRAMING_ENTRIES = frozenset({
    "kepner_tregoe",
    "cynefin",
    "first_principles",
    "evidence_snapshot",
    "mece_sketch",
})

FRAMING_TO_CATALOG: dict[str, str | None] = {
    "kepner_tregoe": "Kepner-Tregoe Problem Analysis",
    "cynefin": None,
    "first_principles": "First-principles thinking",
    "evidence_snapshot": "Gemba Observation",
    "mece_sketch": "MECE issue tree",
}

CORE_TECHNIQUES = frozenset({"5 Whys"})

HYPOTHESIS_TECHNIQUES = frozenset({
    "Hypothesis-driven problem solving",
    "Fishbone / Ishikawa",
})
