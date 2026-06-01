"""Parse implementation wave tables from plan markdown.

Plans following `templates/writing-plans.md` include a **Parallelization Map**
markdown table with columns such as Task, Agent, Depends On, Wave, ...
This module extracts wave assignments so the implement orchestrator can set
`total_waves` and render per-wave task lists without manual counting.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from scripts.implement.plan_waves_parse import parse_parallelization_table_with_diagnostics
from scripts.implement.plan_waves_types import (
    ParseDiagnostics,
    ParsePolicy,
    WaveRow,
    coerce_policy,
)

# Backward-compatible aliases for private helpers moved to plan_waves_types / plan_waves_parse.
_coerce_policy = coerce_policy

__all__ = [
    "ParseDiagnostics",
    "ParsePolicy",
    "WaveRow",
    "custom_to_wave_rows",
    "format_wave_tasks_from_custom",
    "format_wave_tasks_markdown",
    "load_plan_text",
    "parse_parallelization_table",
    "parse_parallelization_table_with_diagnostics",
    "sync_waves_from_plan_file",
    "wave_rows_to_custom",
]


def parse_parallelization_table(markdown: str) -> tuple[int, list[WaveRow]]:
    """Parse wave rows using default parser policy."""
    total, rows, _diag = parse_parallelization_table_with_diagnostics(markdown)
    return total, rows


def format_wave_tasks_markdown(rows: list[WaveRow], wave: int) -> str:
    """Human-readable task list for one wave (markdown bullet list)."""
    mine = [r for r in rows if r.wave == wave]
    if not mine:
        return f"_No tasks found for wave {wave} in the parallelization table._"
    lines_out: list[str] = []
    for r in mine:
        extra = []
        if r.agent:
            extra.append(f"agent: {r.agent}")
        if r.depends_on:
            extra.append(f"depends: {r.depends_on}")
        suffix = f" ({'; '.join(extra)})" if extra else ""
        lines_out.append(f"- **{r.task}**{suffix}")
    return "\n".join(lines_out)


def load_plan_text(plan_path: Path) -> str:
    try:
        return plan_path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return plan_path.read_text(encoding="cp1252")


def sync_waves_from_plan_file(plan_path: Path) -> tuple[int, list[WaveRow]]:
    if not plan_path.is_file():
        return 0, []
    text = load_plan_text(plan_path)
    return parse_parallelization_table(text)


def wave_rows_to_custom(rows: list[WaveRow]) -> list[dict[str, object]]:
    """JSON-serializable rows for SkillState.custom."""
    return [
        {
            "task": r.task,
            "agent": r.agent,
            "depends_on": r.depends_on,
            "wave": r.wave,
            "parallel_with": r.parallel_with,
            "raw": dict(r.raw),
        }
        for r in rows
    ]


def custom_to_wave_rows(rows: list[dict[str, object]]) -> list[WaveRow]:
    out: list[WaveRow] = []
    for d in rows:
        try:
            w = int(d.get("wave", 0))
        except (TypeError, ValueError):
            continue
        out.append(
            WaveRow(
                task=str(d.get("task", "")),
                agent=str(d.get("agent", "")),
                depends_on=str(d.get("depends_on", "")),
                wave=w,
                parallel_with=str(d.get("parallel_with", "")),
                raw={str(k): str(v) for k, v in dict(d.get("raw", {}) or {}).items()},
            )
        )
    return out


def format_wave_tasks_from_custom(rows: list[dict[str, object]], wave: int) -> str:
    """Like format_wave_tasks_markdown but uses serialized custom dicts."""
    return format_wave_tasks_markdown(custom_to_wave_rows(rows), wave)
