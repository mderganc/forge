"""Per-skill handoff routing overrides (extracted from handoff_menu)."""

from __future__ import annotations

from scripts.shared.skill_state import SkillState


def resolve_diagnose_handoff(
    state: SkillState,
    default: str | None,
    alts: list[str],
) -> tuple[str | None, list[str]]:
    fc = str(state.custom.get("fix_complexity", "unknown")).lower()
    if fc == "large":
        return "design", [c for c in alts if c not in ("design", "develop")]
    if fc == "complex":
        return "plan", [c for c in alts if c != "plan"]
    return default, alts


def _apply_test_results_handoff(
    default: str | None,
    alts: list[str],
    test_results: dict,
) -> tuple[str | None, list[str]]:
    failed = int(test_results.get("failed", 0) or 0)
    if failed > 0:
        default = "diagnose"
        alts = [c for c in alts if c != "diagnose"]
        if "ship" not in alts:
            alts.insert(0, "ship")
    else:
        default = "ship"
        alts = [c for c in alts if c != "ship"]
        if "diagnose" not in alts:
            alts.append("diagnose")
    return default, alts


def _swap_test_mode_alts(alts: list[str], mode: str) -> list[str]:
    alts = [a for a in alts if a != "test --mode ux"]
    if mode == "flows" and "test --mode flows" in alts:
        idx = alts.index("test --mode flows")
        alts[idx] = "test --mode run"
    elif mode == "run" and "test --mode run" in alts:
        idx = alts.index("test --mode run")
        alts[idx] = "test --mode flows"
    return alts


def _ensure_ux_review_alt(alts: list[str]) -> list[str]:
    if "ux-review" not in alts:
        alts.append("ux-review")
    return alts


def resolve_test_handoff(
    state: SkillState,
    default: str | None,
    alts: list[str],
) -> tuple[str | None, list[str]]:
    test_results = state.custom.get("test_results", {}) or {}
    default, alts = _apply_test_results_handoff(default, alts, test_results)
    mode = state.custom.get("mode", "run")
    alts = _swap_test_mode_alts(alts, mode)
    alts = _ensure_ux_review_alt(alts)
    return default, alts


def resolve_evaluate_handoff(
    state: SkillState,
    default: str | None,
    alts: list[str],
    *,
    alternatives: list[str],
) -> tuple[str | None, list[str]]:
    mode = str(
        getattr(state, "mode", None) or state.custom.get("mode") or "pre"
    ).lower()
    if mode == "post":
        default = "code-review"
        merged = [c for c in ("ship", "test", "plan", "implement") if c != default]
        for c in alternatives:
            if c not in merged and c != default:
                merged.append(c)
        return default, merged
    default = "implement"
    alts = [c for c in alts if c != "implement"]
    return default, alts


def resolve_ux_review_handoff(
    state: SkillState,
    default: str | None,
    alts: list[str],
) -> tuple[str | None, list[str]]:
    findings = state.custom.get("findings") or []
    high = [
        f
        for f in findings
        if isinstance(f, dict)
        and str(f.get("severity", "")).lower() in ("blocker", "critical", "high")
    ]
    if high:
        alts = [a for a in alts if a != "diagnose"]
        return "diagnose", alts
    return default, alts
