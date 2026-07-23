"""Size/effort heuristics for evaluate ceremony scaling."""

from __future__ import annotations

import re
from typing import Any

SIZE_SMALL = "small"
SIZE_MEDIUM = "medium"
SIZE_LARGE = "large"

# Pre steps to auto-complete / skip for small (template keys map to step numbers)
PRE_SKIP_STEPS_SMALL = {4, 5}  # codebase_alignment, risk_dependencies
POST_SKIP_STEPS_SMALL = {5, 6}  # performance, operational_readiness

PRE_SKIP_NAMES = {
    4: "codebase_alignment",
    5: "risk_dependencies",
}
POST_SKIP_NAMES = {
    5: "performance",
    6: "operational_readiness",
}

_TASK_HEADING = re.compile(
    r"^\s{0,3}#{2,3}\s+Task\s+\d+\b|"
    r"^\s{0,3}#{2,3}\s+task\b|"
    r"^\s*[-*]\s+\*\*Task\s+\d+",
    re.IGNORECASE | re.MULTILINE,
)
_SCOPE_TIER_RE = re.compile(
    r"\bscope[_\s-]?tier\s*[:=]\s*[\"']?(trivial|small|medium|large)\b|"
    r"[\"']scope_tier[\"']\s*:\s*[\"'](trivial|small|medium|large)[\"']|"
    r"\bsize\s*[:=]\s*[\"']?(trivial|small|medium|large)\b|"
    r"\bplan\s+mode:\s*lite\b",
    re.IGNORECASE,
)
_TASK_COUNT_RE = re.compile(
    r"\btask\s+count\s*[:=]\s*(\d+)\b|"
    r"\*\*Task count:\*\*\s*(\d+)",
    re.IGNORECASE,
)


def normalize_size(raw: str | None) -> str:
    text = (raw or "").strip().lower()
    if text in ("trivial", "small", "lite", "light", "quick"):
        return SIZE_SMALL
    if text in ("large", "thorough"):
        return SIZE_LARGE
    if text in ("medium", "standard", "default"):
        return SIZE_MEDIUM
    return SIZE_MEDIUM


def count_plan_tasks(plan_content: str) -> int:
    if not plan_content:
        return 0
    explicit = _TASK_COUNT_RE.search(plan_content)
    if explicit:
        for g in explicit.groups():
            if g is not None:
                return int(g)
    return len(_TASK_HEADING.findall(plan_content))


def infer_size_from_plan(
    plan_content: str = "",
    *,
    referenced_files: list[str] | None = None,
    cli_effort: str | None = None,
    quick: bool = False,
) -> tuple[str, str]:
    """Return (size, rationale). Bias lower when unsure."""
    if quick or (cli_effort and cli_effort.strip().lower() in ("small", "lite", "light", "quick")):
        return SIZE_SMALL, "CLI --quick / --effort small"
    if cli_effort and cli_effort.strip().lower() in ("large", "thorough"):
        return SIZE_LARGE, "CLI --effort large"
    if cli_effort and cli_effort.strip().lower() in ("medium", "standard"):
        return SIZE_MEDIUM, "CLI --effort medium"

    scope_match = _SCOPE_TIER_RE.search(plan_content or "")
    if scope_match:
        for g in scope_match.groups():
            if g:
                size = normalize_size(g)
                return size, f"Plan/handoff marks scope_tier/size `{g}` → {size}"
        if re.search(r"(?i)plan\s+mode:\s*lite", plan_content or ""):
            return SIZE_SMALL, "Plan mode lite → small ceremony"

    task_count = count_plan_tasks(plan_content)
    file_count = len(referenced_files or [])
    if task_count and task_count <= 3 and (not file_count or file_count <= 5):
        return SIZE_SMALL, f"{task_count} tasks / {file_count} files — small ceremony"
    if task_count >= 8 or file_count >= 15:
        return SIZE_LARGE, f"{task_count} tasks / {file_count} files — full ceremony"
    if task_count and task_count <= 3:
        return SIZE_SMALL, f"{task_count} tasks — prefer small"
    if file_count and file_count <= 5:
        return SIZE_SMALL, f"{file_count} referenced files — prefer small"
    return SIZE_MEDIUM, "Moderate plan breadth (default medium)"


def should_skip_phase(mode: str | None, step: int, size: str, quick: bool = False) -> bool:
    if mode == "review":
        return False
    lean = quick or normalize_size(size) == SIZE_SMALL
    if not lean:
        return False
    if mode == "post":
        return step in POST_SKIP_STEPS_SMALL
    return step in PRE_SKIP_STEPS_SMALL


def skip_note(mode: str | None, step: int) -> str:
    names = POST_SKIP_NAMES if mode == "post" else PRE_SKIP_NAMES
    name = names.get(step, f"step {step}")
    return (
        f"## Phase skipped (minimal-scope)\n\n"
        f"**Size-scaled skip:** `{name}` is skipped for small/trivial/quick evaluate.\n\n"
        "Record no findings for this phase; continue to the next step.\n"
    )


def skipped_phase_summary(mode: str | None, size: str, quick: bool) -> str:
    """Human-readable list of phases that will be skipped."""
    if not (quick or normalize_size(size) == SIZE_SMALL):
        return "none (full phase set)"
    names = POST_SKIP_NAMES if mode == "post" else PRE_SKIP_NAMES
    steps = POST_SKIP_STEPS_SMALL if mode == "post" else PRE_SKIP_STEPS_SMALL
    return ", ".join(f"{s} (`{names[s]}`)" for s in sorted(steps))


def apply_size_to_custom(custom: dict[str, Any], size: str, rationale: str, quick: bool) -> None:
    size = normalize_size(size)
    custom["eval_size"] = size
    custom["eval_size_rationale"] = rationale
    custom["effort"] = {"small": "light", "medium": "standard", "large": "thorough"}.get(size, "standard")
    custom["quick_mode"] = bool(quick or size == SIZE_SMALL)
    custom["skipped_phases"] = skipped_phase_summary(
        custom.get("mode") if isinstance(custom.get("mode"), str) else None,
        size,
        bool(custom["quick_mode"]),
    )
