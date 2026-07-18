"""Recommend code-review --effort and --structural from session context."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_EFFORT_LEVELS = frozenset({"light", "standard", "thorough"})

_LARGE_HANDOFF_KEYWORDS = (
    "refactor",
    "architecture",
    "structural",
    "security",
    "migration",
    "breaking",
    "cross-cutting",
    "multi-module",
)

_DEEP_KEYWORDS = (
    "bug",
    "regression",
    "incident",
    "fail",
    "crash",
    "flaky",
    "investigate",
    "root cause",
)


@dataclass
class EffortRecommendation:
    effort: str
    structural: bool
    reasoning: list[str] = field(default_factory=list)
    confidence: float = 0.75
    signals: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "effort": self.effort,
            "structural": self.structural,
            "reasoning": list(self.reasoning),
            "confidence": round(float(self.confidence), 2),
            "signals": dict(self.signals),
        }


def _count_handoff_paths(handoff_content: str) -> int:
    if not handoff_content:
        return 0
    # Bullet paths and backtick paths common in implement handoffs
    bullets = re.findall(r"(?m)^\s*[-*]\s+`([^`]+)`", handoff_content)
    inline = re.findall(r"`([^\s`]+\.[a-zA-Z0-9]+)`", handoff_content)
    paths = {p.strip() for p in (*bullets, *inline) if "/" in p or "\\" in p}
    return len(paths)


def _handoff_mentions_files_changed(handoff_content: str) -> int | None:
    m = re.search(
        r"(\d+)\s+files?\s+changed",
        handoff_content,
        flags=re.IGNORECASE,
    )
    return int(m.group(1)) if m else None


@dataclass
class _ScoreState:
    effort: str = "standard"
    structural: bool = False
    reasoning: list[str] = field(default_factory=list)
    confidence: float = 0.72

    def bump_confidence(self, value: float) -> None:
        self.confidence = max(self.confidence, value)


def _score_from_mode(score: _ScoreState, mode: str, combined: str) -> None:
    if mode == "architecture":
        score.effort = "thorough"
        score.structural = True
        score.reasoning.append("Architecture mode benefits from full team + structural Pass B.")
        score.bump_confidence(0.9)
    elif mode == "deep":
        score.effort = "standard"
        score.structural = True
        score.reasoning.append(
            "Deep/troubleshooting mode: full team with structural probes for trace paths."
        )
        score.bump_confidence(0.85)
    elif any(kw in combined for kw in _DEEP_KEYWORDS):
        score.effort = "standard"
        score.structural = True
        score.reasoning.append("Target/handoff mentions failure or investigation keywords.")
        score.bump_confidence(0.8)


def _score_from_files_changed(score: _ScoreState, files_changed: int | None, mode: str) -> None:
    if files_changed is None:
        return
    if files_changed >= 20:
        score.effort = "thorough"
        score.structural = True
        score.reasoning.append(
            f"Implement handoff reports {files_changed} files changed (large scope)."
        )
        score.bump_confidence(0.88)
    elif files_changed >= 8:
        score.structural = True
        score.reasoning.append(
            f"Implement handoff reports {files_changed} files changed (medium scope)."
        )
        score.bump_confidence(0.82)
    elif files_changed <= 3 and mode == "pr":
        score.effort = "light"
        score.structural = False
        score.reasoning.append(
            f"Small handoff scope ({files_changed} files) — light PR pass is enough."
        )
        score.bump_confidence(0.78)


def _score_from_path_count(score: _ScoreState, path_count: int) -> None:
    if path_count >= 15:
        score.effort = "thorough"
        score.structural = True
        score.reasoning.append(f"Handoff lists ~{path_count} paths (broad touch surface).")
        score.bump_confidence(0.86)
    elif path_count >= 6 and not score.structural:
        score.structural = True
        score.reasoning.append(f"Handoff lists ~{path_count} paths — structural probes add signal.")
        score.bump_confidence(0.8)


def _score_from_target(
    score: _ScoreState,
    *,
    mode: str,
    target_tokens: list[str],
    handoff_content: str,
    target_file_count: int,
) -> None:
    if target_file_count == 1 and mode == "pr" and not handoff_content:
        score.effort = "light"
        score.structural = False
        score.reasoning.append("Single-file target with no implement handoff — light review.")
        score.bump_confidence(0.76)
    elif target_file_count >= 4 and mode == "pr":
        if score.effort == "light":
            score.effort = "standard"
        score.structural = True
        score.reasoning.append(f"Multiple explicit target paths ({target_file_count}).")
        score.bump_confidence(0.77)
    elif not handoff_content and mode == "pr" and not target_tokens:
        score.effort = "light"
        score.structural = False
        score.reasoning.append(
            "Open-ended PR review with sparse target — start light; escalate if needed."
        )
        score.confidence = 0.7


def recommend_effort_structural(
    *,
    mode: str,
    target: str,
    target_tokens: list[str],
    handoff_content: str = "",
    plan_path: str = "",
    quick: bool = False,
) -> EffortRecommendation:
    """Score effort/structural from mode, target, and implement handoff signals."""
    mode = (mode or "pr").strip().lower()
    combined = f"{target} {handoff_content}".lower()
    path_count = _count_handoff_paths(handoff_content)
    files_changed = _handoff_mentions_files_changed(handoff_content)
    target_file_count = sum(
        1 for tok in target_tokens if "." in tok or "/" in tok or "\\" in tok
    )

    effort = "standard"
    structural = False
    reasoning: list[str] = []
    confidence = 0.72

    if quick:
        return EffortRecommendation(
            effort="light",
            structural=False,
            reasoning=["`--quick` requests abbreviated Architect + QA review only."],
            confidence=0.95,
            signals={"quick": True},
        )

    score = _ScoreState()
    _score_from_mode(score, mode, combined)
    _score_from_files_changed(score, files_changed, mode)
    _score_from_path_count(score, path_count)

    if any(kw in combined for kw in _LARGE_HANDOFF_KEYWORDS):
        if score.effort == "standard":
            score.effort = "thorough"
        score.structural = True
        score.reasoning.append("Handoff/target mentions refactor, security, or structural work.")
        score.bump_confidence(0.84)

    if plan_path:
        score.structural = True
        score.reasoning.append("Plan file linked — structural probes help compare intent vs code.")
        score.bump_confidence(0.8)

    _score_from_target(
        score,
        mode=mode,
        target_tokens=target_tokens,
        handoff_content=handoff_content,
        target_file_count=target_file_count,
    )

    if not score.reasoning:
        score.reasoning.append("Default pipeline review after implement — standard team, probes optional.")

    effort = score.effort if score.effort in _EFFORT_LEVELS else "standard"
    return EffortRecommendation(
        effort=effort,
        structural=score.structural,
        reasoning=score.reasoning,
        confidence=score.confidence,
        signals={
            "mode": mode,
            "path_count": path_count,
            "files_changed": files_changed,
            "target_file_count": target_file_count,
            "has_handoff": bool(handoff_content),
            "has_plan": bool(plan_path),
        },
    )


def resolve_applied_config(
    args: Any,
    recommendation: EffortRecommendation,
) -> tuple[str, bool, bool, bool]:
    """Return (effort, structural_enabled, effort_overridden, structural_overridden)."""
    quick = bool(getattr(args, "quick", False))
    explicit_effort = getattr(args, "effort", None) is not None

    if quick:
        effort = "light"
    elif explicit_effort:
        effort = (getattr(args, "effort", None) or "standard").strip().lower()
    else:
        effort = recommendation.effort

    if effort not in _EFFORT_LEVELS:
        effort = "light" if quick else "standard"
    if quick and effort == "standard":
        effort = "light"

    structural_flag = getattr(args, "structural", None)
    explicit_structural = structural_flag is not None

    if structural_flag is True:
        structural_enabled = True
    elif structural_flag is False:
        structural_enabled = False
    elif recommendation.structural:
        structural_enabled = True
    else:
        structural_enabled = effort == "thorough"

    return effort, structural_enabled, explicit_effort, explicit_structural


def format_effort_config_section(
    recommendation: EffortRecommendation,
    *,
    applied_effort: str,
    applied_structural: bool,
    effort_overridden: bool,
    structural_overridden: bool,
) -> str:
    """Markdown block for step 1/2 prompts."""
    rec_struct = "on" if recommendation.structural else "off"
    app_struct = "on" if applied_structural else "off"

    def _applied_note(overridden: bool, rec: str, applied: str) -> str:
        if overridden:
            return f"**{applied}** (CLI override; recommended `{rec}`)"
        if rec == applied:
            return f"**{applied}** (matches recommendation)"
        return f"**{applied}** (recommended `{rec}`)"

    lines = [
        "## Recommended review config",
        "",
        "| Setting | Recommended | Applied |",
        "|---------|-------------|---------|",
        f"| `--effort` | `{recommendation.effort}` | {_applied_note(effort_overridden, recommendation.effort, applied_effort)} |",
        f"| `--structural` | {rec_struct} | {_applied_note(structural_overridden, rec_struct, app_struct)} |",
        "",
        f"**Confidence:** {recommendation.confidence:.0%}",
        "",
        "**Why:**",
    ]
    for reason in recommendation.reasoning:
        lines.append(f"- {reason}")
    lines.extend(
        [
            "",
            "Restart step 1 to change: "
            f"`forge code-review --step 1 --effort {recommendation.effort}"
            + (" --structural" if recommendation.structural else " --no-structural")
            + " ...`",
        ]
    )
    return "\n".join(lines)
