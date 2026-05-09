"""Parse implementation wave tables from plan markdown.

Plans following `templates/writing-plans.md` include a **Parallelization Map**
markdown table with columns such as Task, Agent, Depends On, Wave, ...
This module extracts wave assignments so the implement orchestrator can set
`total_waves` and render per-wave task lists without manual counting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class WaveRow:
    task: str
    agent: str
    depends_on: str
    wave: int
    parallel_with: str
    raw: dict[str, str]


def _split_table_row(line: str) -> list[str]:
    if "|" not in line:
        return []
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _normalize_header(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip().lower())


def _is_separator_row(line: str) -> bool:
    """True for markdown table separator rows like | --- | :--- |."""
    if "|" not in line:
        return False
    for ch in line.strip():
        if ch not in "|\r\n\t -:":
            return False
    return "-" in line


def _wave_cell_to_int(cell: str) -> int | None:
    cell = cell.strip()
    if not cell:
        return None
    m = re.search(r"(\d+)", cell)
    if not m:
        return None
    return int(m.group(1))


def parse_parallelization_table(markdown: str) -> tuple[int, list[WaveRow]]:
    """Parse the parallelization map table; return max wave number and rows.

    Returns (0, []) when no suitable table is found or no Wave column exists.
    """
    lines = markdown.splitlines()
    header_idx: int | None = None
    headers_norm: list[str] = []

    for i, line in enumerate(lines):
        if "|" not in line or line.strip().startswith("```"):
            continue
        cells = _split_table_row(line)
        if len(cells) < 2:
            continue
        norms = [_normalize_header(c) for c in cells]
        if any("wave" == n or n.startswith("wave ") for n in norms):
            header_idx = i
            headers_norm = norms
            break

    if header_idx is None:
        return 0, []

    try:
        wave_col = next(j for j, n in enumerate(headers_norm) if n == "wave" or n.startswith("wave "))
    except StopIteration:
        return 0, []

    # Optional columns (best-effort names from writing-plans template)
    def col_idx(*names: str) -> int | None:
        for want in names:
            w = _normalize_header(want)
            for j, n in enumerate(headers_norm):
                if n == w or n.replace(" ", "") == w.replace(" ", ""):
                    return j
        return None

    ti = col_idx("task")
    ai = col_idx("agent")
    di = col_idx("depends on", "depends_on", "depends")
    pi = col_idx("can parallel with", "can_parallel_with", "parallel")

    rows: list[WaveRow] = []
    data_start = header_idx + 1
    # Skip markdown separator row (|:---|:---|)
    if data_start < len(lines) and _is_separator_row(lines[data_start]):
        data_start += 1

    for line in lines[data_start:]:
        if "|" not in line:
            break
        if line.strip().startswith("```"):
            break
        cells = _split_table_row(line)
        if len(cells) <= wave_col:
            continue
        # Skip accidental header repeats
        if _normalize_header(cells[0]) == "task" and "wave" in [_normalize_header(c) for c in cells]:
            continue

        wv = _wave_cell_to_int(cells[wave_col])
        if wv is None:
            continue

        def get(col: int | None, default: str = "") -> str:
            if col is None or col >= len(cells):
                return default
            return cells[col].strip()

        rows.append(
            WaveRow(
                task=get(ti, "(task)"),
                agent=get(ai, ""),
                depends_on=get(di, ""),
                wave=wv,
                parallel_with=get(pi, ""),
                raw={headers_norm[k]: (cells[k] if k < len(cells) else "") for k in range(len(headers_norm))},
            )
        )

    if not rows:
        return 0, []

    max_wave = max(r.wave for r in rows)
    return max_wave, rows


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


def resolve_plan_path(plan_arg: str, cwd: Path) -> Path:
    p = Path(plan_arg).expanduser()
    if not p.is_absolute():
        p = (cwd / p).resolve()
    return p


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
                raw={},
            )
        )
    return out


def format_wave_tasks_from_custom(rows: list[dict[str, object]], wave: int) -> str:
    """Like format_wave_tasks_markdown but uses serialized custom dicts."""
    return format_wave_tasks_markdown(custom_to_wave_rows(rows), wave)
