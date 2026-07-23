"""Recommend code-review --effort and structural fan-out from session context.

Structural probes are **always on** by default (scale fan-out, do not opt in).
Escalate effort only when ≥2 corroborating signals agree (keyword **and**
file-count / path breadth).
"""

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

_AUTH_DATA_KEYWORDS = (
    "auth",
    "oauth",
    "permission",
    "rbac",
    "secret",
    "password",
    "token",
    "crypto",
    "encrypt",
    "pii",
    "gdpr",
    "credential",
    "session",
    "cookie",
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


def mentions_auth_or_data(text: str) -> bool:
    """True when target/handoff suggests auth or sensitive-data review."""
    lowered = (text or "").lower()
    return any(kw in lowered for kw in _AUTH_DATA_KEYWORDS)


def _file_breadth_signal(files_changed: int | None, path_count: int, target_file_count: int) -> bool:
    """True when change surface is medium+ (file-count corroborator)."""
    if files_changed is not None and files_changed >= 8:
        return True
    if path_count >= 6:
        return True
    if target_file_count >= 4:
        return True
    return False


def _keyword_signal(combined: str) -> bool:
    return any(kw in combined for kw in _LARGE_HANDOFF_KEYWORDS)


def recommend_effort_structural(
    *,
    mode: str,
    target: str,
    target_tokens: list[str],
    handoff_content: str = "",
    plan_path: str = "",
    quick: bool = False,
) -> EffortRecommendation:
    """Score effort from mode/target/handoff; structural always recommended on."""
    mode = (mode or "pr").strip().lower()
    combined = f"{target} {handoff_content}".lower()
    path_count = _count_handoff_paths(handoff_content)
    files_changed = _handoff_mentions_files_changed(handoff_content)
    target_file_count = sum(
        1 for tok in target_tokens if "." in tok or "/" in tok or "\\" in tok
    )

    keyword = _keyword_signal(combined)
    breadth = _file_breadth_signal(files_changed, path_count, target_file_count)
    auth_data = mentions_auth_or_data(combined)

    reasoning: list[str] = []
    confidence = 0.72

    # Structural is always on — scale fan-out at dispatch, never require --structural.
    structural = True

    if quick:
        return EffortRecommendation(
            effort="light",
            structural=True,
            reasoning=[
                "`--quick` → light team (Architect + QA); structural probes still on "
                "(S3/S4/S8 quick subset)."
            ],
            confidence=0.95,
            signals={
                "quick": True,
                "keyword": keyword,
                "breadth": breadth,
                "auth_data": auth_data,
            },
        )

    # Explicit architecture mode is an intentional thorough review.
    if mode == "architecture":
        return EffortRecommendation(
            effort="thorough",
            structural=True,
            reasoning=[
                "Architecture mode → full team + broader structural fan-out.",
                "Structural probes always on; unrelated findings remain advisory.",
            ],
            confidence=0.9,
            signals={
                "mode": mode,
                "path_count": path_count,
                "files_changed": files_changed,
                "target_file_count": target_file_count,
                "keyword": keyword,
                "breadth": breadth,
                "auth_data": auth_data,
                "has_handoff": bool(handoff_content),
                "has_plan": bool(plan_path),
            },
        )

    effort = "standard"

    # Small surfaces prefer light (still with structural quick subset).
    small_surface = (
        (files_changed is not None and files_changed <= 3)
        or (target_file_count == 1 and mode == "pr" and not handoff_content)
        or (mode == "pr" and not handoff_content and not target_tokens)
    )
    if small_surface and not (keyword and breadth):
        effort = "light"
        if files_changed is not None and files_changed <= 3:
            reasoning.append(
                f"Small handoff scope ({files_changed} files) — light team + structural quick subset."
            )
            confidence = max(confidence, 0.78)
        elif target_file_count == 1 and mode == "pr" and not handoff_content:
            reasoning.append("Single-file target with no implement handoff — light review.")
            confidence = max(confidence, 0.76)
        else:
            reasoning.append(
                "Open-ended PR review with sparse target — start light; escalate if needed."
            )
            confidence = 0.7

    if mode == "deep" or any(kw in combined for kw in _DEEP_KEYWORDS):
        if effort == "light":
            effort = "standard"
        reasoning.append(
            "Deep/troubleshooting signals — standard trimmed team; structural probes on."
        )
        confidence = max(confidence, 0.85)

    # Escalate to thorough only with ≥2 corroborating signals (keyword AND breadth).
    if keyword and breadth:
        effort = "thorough"
        reasoning.append(
            "Escalated to thorough: keyword signal and file-breadth signal both present."
        )
        if files_changed is not None:
            reasoning.append(f"Handoff reports {files_changed} files changed.")
        if path_count:
            reasoning.append(f"Handoff lists ~{path_count} paths.")
        confidence = max(confidence, 0.88)
    elif keyword and not breadth:
        reasoning.append(
            "Keyword signal alone (refactor/security/etc.) — not escalating without file-breadth."
        )
        confidence = max(confidence, 0.8)
    elif breadth and not keyword:
        if files_changed is not None and files_changed >= 8:
            reasoning.append(
                f"Medium+ file count ({files_changed}) without large-scope keywords — stay "
                f"{effort}; structural probes cover coupling."
            )
        else:
            reasoning.append(
                f"Path breadth (~{path_count or target_file_count} paths) without keywords — "
                f"stay {effort}."
            )
        confidence = max(confidence, 0.8)

    if plan_path:
        reasoning.append("Plan file linked — structural probes compare intent vs code.")
        confidence = max(confidence, 0.8)

    if auth_data and effort == "standard":
        reasoning.append("Auth/data keywords → include Security Reviewer on the standard team.")

    if not reasoning:
        reasoning.append(
            "Default pipeline review — standard trimmed team; structural always on "
            "(quick subset unless thorough)."
        )

    reasoning.append(
        "Structural probes always on; scale fan-out (S3/S4/S8 for light/standard; "
        "full eight for thorough). Diff-scoped; unrelated findings advisory."
    )

    if effort not in _EFFORT_LEVELS:
        effort = "standard"

    return EffortRecommendation(
        effort=effort,
        structural=structural,
        reasoning=reasoning,
        confidence=confidence,
        signals={
            "mode": mode,
            "path_count": path_count,
            "files_changed": files_changed,
            "target_file_count": target_file_count,
            "keyword": keyword,
            "breadth": breadth,
            "auth_data": auth_data,
            "has_handoff": bool(handoff_content),
            "has_plan": bool(plan_path),
        },
    )


def resolve_applied_config(
    args: Any,
    recommendation: EffortRecommendation,
) -> tuple[str, bool, bool, bool]:
    """Return (effort, structural_enabled, effort_overridden, structural_overridden).

    Structural defaults **on**. Only ``--no-structural`` turns it off.
    """
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

    if structural_flag is False:
        structural_enabled = False
    else:
        # True CLI flag, recommendation, or default — always on unless opted out.
        structural_enabled = True

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
        f"| structural | {rec_struct} | {_applied_note(structural_overridden, rec_struct, app_struct)} |",
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
            "Structural is **on by default** (no `--structural` opt-in). "
            "Scale fan-out with effort; use `--no-structural` only to skip.",
            "",
            "Restart step 1 to change: "
            f"`forge code-review --step 1 --effort {recommendation.effort}"
            + (" --no-structural" if not recommendation.structural else "")
            + " ...`",
        ]
    )
    return "\n".join(lines)
