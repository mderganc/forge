"""Resolve which diagnose techniques are in play for adaptive gating."""

from __future__ import annotations

from pathlib import Path

from scripts.diagnose.diagnose_framing import (
    CORE_TECHNIQUES,
    FRAMING_ENTRIES,
    FRAMING_TO_CATALOG,
    HYPOTHESIS_TECHNIQUES,
)
from scripts.diagnose.diagnose_registers import resolve_sidecar_path
from scripts.diagnose.problem_spec_register import FILENAME as PROBLEM_SPEC_FILENAME
from scripts.diagnose.problem_spec_register import load_register as load_problem_spec


def _normalize_names(values: object) -> set[str]:
    if not values:
        return set()
    if isinstance(values, str):
        return {values.strip()} if values.strip() else set()
    if isinstance(values, list):
        return {str(v).strip() for v in values if v and str(v).strip()}
    return set()


def activated_from_problem_spec(data: dict | None) -> set[str]:
    """Techniques explicitly activated via problem spec."""
    if not data:
        return set(CORE_TECHNIQUES)

    activated = set(CORE_TECHNIQUES)
    entry = data.get("framing_entry")
    if entry in FRAMING_ENTRIES:
        mapped = FRAMING_TO_CATALOG.get(entry)
        if mapped:
            activated.add(mapped)

    activated |= _normalize_names(data.get("activated_techniques"))
    activated |= _normalize_names(data.get("routing_preferred"))
    return activated


def resolve_activated_techniques(
    state_path: Path,
    state_custom: dict | None = None,
) -> set[str]:
    """Union of problem-spec routing and optional state.custom overrides.

    ``state_path`` is the orchestrator state file (e.g. ``session.json``);
    the problem-spec sidecar is resolved via ``resolve_sidecar_path`` so it
    is found whether it lives beside the state file or under ``sidecars/``.
    """
    spec = load_problem_spec(resolve_sidecar_path(state_path, PROBLEM_SPEC_FILENAME))
    activated = activated_from_problem_spec(spec)
    if state_custom:
        activated |= _normalize_names(state_custom.get("activated_techniques"))
    return activated


def requires_hypothesis_register(activated: set[str]) -> bool:
    return bool(activated & HYPOTHESIS_TECHNIQUES)


def requires_first_principles(activated: set[str]) -> bool:
    return "First-principles thinking" in activated


def requires_mece_tree(activated: set[str]) -> bool:
    return "MECE issue tree" in activated
