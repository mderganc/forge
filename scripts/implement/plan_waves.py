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
from typing import Any, Mapping


@dataclass(frozen=True)
class WaveRow:
    task: str
    agent: str
    depends_on: str
    wave: int
    parallel_with: str
    raw: dict[str, str]


@dataclass(frozen=True)
class ParsePolicy:
    """Policy knobs for robust, config-compatible wave parsing."""

    min_table_coverage: float = 0.5
    min_narrative_coverage: float = 0.0
    transcript_theme_limit: int = 4


@dataclass(frozen=True)
class ParseDiagnostics:
    """Debug details for parser decisions and quality gating."""

    table_coverage: float
    narrative_coverage: float
    buckets: dict[str, int]
    transcript_themes: list[str]
    source: str


def _coerce_policy(policy: ParsePolicy | Mapping[str, Any] | None) -> ParsePolicy:
    """Build a ParsePolicy from dataclass or mapping keys."""
    if isinstance(policy, ParsePolicy):
        return policy
    if not isinstance(policy, Mapping):
        return ParsePolicy()

    def _float(name: str, default: float) -> float:
        try:
            return float(policy.get(name, default))
        except (TypeError, ValueError):
            return default

    def _int(name: str, default: int) -> int:
        try:
            return int(policy.get(name, default))
        except (TypeError, ValueError):
            return default

    return ParsePolicy(
        min_table_coverage=max(0.0, min(1.0, _float("min_table_coverage", ParsePolicy.min_table_coverage))),
        min_narrative_coverage=max(0.0, min(1.0, _float("min_narrative_coverage", ParsePolicy.min_narrative_coverage))),
        transcript_theme_limit=max(1, _int("transcript_theme_limit", ParsePolicy.transcript_theme_limit)),
    )


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


def _looks_like_wave_heading(line: str) -> re.Match[str] | None:
    return re.match(
        r"^\s{0,3}(?:[-*]\s*)?(?:#{1,6}\s*)?(?:\*\*)?\s*wave\s*(\d+)\b(?:\*\*)?\s*:?\s*(.*)$",
        line.strip(),
        flags=re.IGNORECASE,
    )


def _extract_agent(text: str) -> str:
    m = re.search(r"\bagent\s*:\s*([^,;|)]+)", text, flags=re.IGNORECASE)
    return (m.group(1).strip() if m else "")


def _extract_depends_on(text: str) -> str:
    m = re.search(r"\bdepends(?:\s+on)?\s*:\s*([^;|)]+)", text, flags=re.IGNORECASE)
    return (m.group(1).strip() if m else "")


def _clean_task_text(text: str) -> str:
    cleaned = re.sub(r"^\s*(?:[-*]\s+|\d+\.\s+)", "", text).strip()
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\b(agent|depends(?:\s+on)?)\s*:\s*[^;|)]+", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*\(\s*\)", "", cleaned)
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" -;,:")
    return cleaned


def _looks_like_task_label(text: str) -> bool:
    return bool(re.search(r"\btask\s*(?:#?\d+|[A-Za-z_-]+)\b", text, flags=re.IGNORECASE))


def _parse_narrative_wave_rows(markdown: str) -> list[WaveRow]:
    """Best-effort parser for narrative wave maps (non-table formats)."""
    lines = markdown.splitlines()
    rows: list[WaveRow] = []
    current_wave: int | None = None

    for line in lines:
        wave_match = _looks_like_wave_heading(line)
        if wave_match:
            current_wave = int(wave_match.group(1))
            inline = wave_match.group(2).strip()
            if inline and _looks_like_task_label(inline):
                chunks = [c.strip() for c in re.split(r"\s*(?:,|;|\|)\s*", inline) if c.strip()]
                for chunk in chunks:
                    if not _looks_like_task_label(chunk):
                        continue
                    rows.append(
                        WaveRow(
                            task=_clean_task_text(chunk),
                            agent=_extract_agent(chunk),
                            depends_on=_extract_depends_on(chunk),
                            wave=current_wave,
                            parallel_with="",
                            raw={"source": "narrative-inline"},
                        )
                    )
            continue

        if current_wave is None:
            continue

        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("```"):
            continue

        if _looks_like_wave_heading(stripped):
            continue

        # Bullet/numbered task lines under a "Wave N" heading.
        if re.match(r"^\s*(?:[-*]|\d+\.)\s+", line):
            task = _clean_task_text(stripped)
            if not task:
                continue
            if not _looks_like_task_label(task):
                continue
            rows.append(
                WaveRow(
                    task=task,
                    agent=_extract_agent(stripped),
                    depends_on=_extract_depends_on(stripped),
                    wave=current_wave,
                    parallel_with="",
                    raw={"source": "narrative-bullet"},
                )
            )

    return rows


def _build_diagnostics(
    table_candidates: int,
    table_rows: int,
    narrative_candidates: int,
    narrative_rows: int,
    buckets: dict[str, int],
    transcript: list[str],
    source: str,
    policy: ParsePolicy,
) -> ParseDiagnostics:
    table_cov = (table_rows / table_candidates) if table_candidates > 0 else 0.0
    narrative_cov = (narrative_rows / narrative_candidates) if narrative_candidates > 0 else 0.0
    theme_counts: dict[str, int] = {}
    for item in transcript:
        theme_counts[item] = theme_counts.get(item, 0) + 1
    top = sorted(theme_counts.items(), key=lambda kv: (-kv[1], kv[0]))[: policy.transcript_theme_limit]
    themes = [name for name, _ in top]
    return ParseDiagnostics(
        table_coverage=table_cov,
        narrative_coverage=narrative_cov,
        buckets=dict(buckets),
        transcript_themes=themes,
        source=source,
    )


def parse_parallelization_table_with_diagnostics(
    markdown: str,
    policy: ParsePolicy | Mapping[str, Any] | None = None,
) -> tuple[int, list[WaveRow], ParseDiagnostics]:
    """Parse wave assignments with policy checks and diagnostics."""
    cfg = _coerce_policy(policy)
    buckets: dict[str, int] = {}
    transcript: list[str] = []

    def _bucket(name: str) -> None:
        buckets[name] = buckets.get(name, 0) + 1
        transcript.append(name)
    # Returns (0, []) when no suitable table is found or no usable wave rows exist.
    lines = markdown.splitlines()
    header_idx: int | None = None
    headers_norm: list[str] = []
    table_candidate_rows = 0

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
            _bucket("table_header_found")
            break

    if header_idx is None:
        _bucket("table_header_missing")
        narrative_rows = _parse_narrative_wave_rows(markdown)
        narrative_candidates = sum(
            1
            for line in lines
            if re.match(r"^\s*(?:[-*]|\d+\.)\s+", line) and "wave" in markdown.lower()
        )
        narrative_cov = (len(narrative_rows) / narrative_candidates) if narrative_candidates > 0 else 0.0
        if narrative_candidates > 0 and narrative_cov < cfg.min_narrative_coverage:
            _bucket("narrative_coverage_reject")
            diag = _build_diagnostics(
                table_candidate_rows,
                0,
                narrative_candidates,
                len(narrative_rows),
                buckets,
                transcript,
                source="none",
                policy=cfg,
            )
            return 0, [], diag
        if not narrative_rows:
            _bucket("narrative_rows_missing")
            diag = _build_diagnostics(
                table_candidate_rows,
                0,
                narrative_candidates,
                0,
                buckets,
                transcript,
                source="none",
                policy=cfg,
            )
            return 0, [], diag
        _bucket("narrative_rows_used")
        diag = _build_diagnostics(
            table_candidate_rows,
            0,
            narrative_candidates,
            len(narrative_rows),
            buckets,
            transcript,
            source="narrative",
            policy=cfg,
        )
        return max(r.wave for r in narrative_rows), narrative_rows, diag

    try:
        wave_col = next(j for j, n in enumerate(headers_norm) if n == "wave" or n.startswith("wave "))
    except StopIteration:
        _bucket("table_wave_column_missing")
        narrative_rows = _parse_narrative_wave_rows(markdown)
        narrative_candidates = sum(
            1
            for line in lines
            if re.match(r"^\s*(?:[-*]|\d+\.)\s+", line) and "wave" in markdown.lower()
        )
        if not narrative_rows:
            _bucket("narrative_rows_missing")
            diag = _build_diagnostics(
                table_candidate_rows,
                0,
                narrative_candidates,
                0,
                buckets,
                transcript,
                source="none",
                policy=cfg,
            )
            return 0, [], diag
        _bucket("narrative_rows_used")
        diag = _build_diagnostics(
            table_candidate_rows,
            0,
            narrative_candidates,
            len(narrative_rows),
            buckets,
            transcript,
            source="narrative",
            policy=cfg,
        )
        return max(r.wave for r in narrative_rows), narrative_rows, diag

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
        table_candidate_rows += 1

        wv = _wave_cell_to_int(cells[wave_col])
        if wv is None:
            _bucket("table_wave_value_missing")
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
        _bucket("table_rows_missing")
        narrative_rows = _parse_narrative_wave_rows(markdown)
        narrative_candidates = sum(
            1
            for line in lines
            if re.match(r"^\s*(?:[-*]|\d+\.)\s+", line) and "wave" in markdown.lower()
        )
        if not narrative_rows:
            diag = _build_diagnostics(
                table_candidate_rows,
                0,
                narrative_candidates,
                0,
                buckets,
                transcript,
                source="none",
                policy=cfg,
            )
            return 0, [], diag
        _bucket("narrative_rows_used")
        diag = _build_diagnostics(
            table_candidate_rows,
            0,
            narrative_candidates,
            len(narrative_rows),
            buckets,
            transcript,
            source="narrative",
            policy=cfg,
        )
        return max(r.wave for r in narrative_rows), narrative_rows, diag

    table_cov = (len(rows) / table_candidate_rows) if table_candidate_rows > 0 else 0.0
    if table_candidate_rows > 0 and table_cov < cfg.min_table_coverage:
        _bucket("table_coverage_reject")
        narrative_rows = _parse_narrative_wave_rows(markdown)
        narrative_candidates = sum(
            1
            for line in lines
            if re.match(r"^\s*(?:[-*]|\d+\.)\s+", line) and "wave" in markdown.lower()
        )
        if narrative_rows:
            _bucket("narrative_rows_used")
            diag = _build_diagnostics(
                table_candidate_rows,
                len(rows),
                narrative_candidates,
                len(narrative_rows),
                buckets,
                transcript,
                source="narrative",
                policy=cfg,
            )
            return max(r.wave for r in narrative_rows), narrative_rows, diag

    max_wave = max(r.wave for r in rows)
    _bucket("table_rows_used")
    diag = _build_diagnostics(
        table_candidate_rows,
        len(rows),
        0,
        0,
        buckets,
        transcript,
        source="table",
        policy=cfg,
    )
    return max_wave, rows, diag


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
